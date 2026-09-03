#!/usr/bin/env python3
"""Seal the deterministic CTRL-04 C1 candidate and emit its external identity.

Refuses to seal unless the developer validator, mutation harness, E2E and
browser journeys all report their required results. The archive carries a
complete `SHA256SUMS.txt`; the candidate manifest inside the archive records
`CANDIDATE_NOT_ACCEPTED` and `self_acceptance = false`. The archive's own
SHA-256 and size are written to a sidecar because a file cannot contain its
own digest. Post-seal verification is run on the sealed bytes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAME = "EPD2_CTRL04_OPERATIONS_CONSOLE_CANDIDATE_0.1_C1"
VALIDATION = ROOT / "validation/ctrl04"
EXCLUDED_DIRS = {
    ".git",
    ".venv",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".next",
    "node_modules",
    "__pycache__",
}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".sqlite", ".sqlite3", ".db", ".zip"}


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def allowed(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    return not (
        set(relative.parts) & EXCLUDED_DIRS
        or path.suffix.lower() in EXCLUDED_SUFFIXES
        or path.name.startswith(".codex-upload-")
        or path.name.endswith(".identity.json")
    )


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"SEAL_REFUSED: {message}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=ROOT.parent / f"{NAME}.zip")
    args = parser.parse_args()
    result = json.loads((VALIDATION / "ctrl04_preseal_result.json").read_text())
    require(result["overall"] == "PASS", "developer validator has not passed")
    require(result["gates_passed"] == 52 and not result["gates_failed"], "gate disposition")
    require(result["self_state"] == "CANDIDATE_NOT_ACCEPTED", "self-state")
    require(result["self_acceptance"] is False, "self-acceptance")
    mutation = json.loads((VALIDATION / "mutation_result.json").read_text())
    require(
        mutation["detected"] == 48 and not mutation["undetected"], "mutation suite is not 48/48"
    )
    e2e = json.loads((VALIDATION / "e2e_journeys_result.json").read_text())
    require(e2e["journeys_passed"] == 20, "E2E journeys are not 20/20")
    browser = json.loads((VALIDATION / "browser_journeys_result.json").read_text())
    require(browser.get("status") == "PASS", "browser journeys did not pass")
    freeze = json.loads((VALIDATION / "freeze_manifest.json").read_text())
    for rel, expected in freeze["files"].items():
        require(digest(ROOT / rel) == expected, f"freeze drift: {rel}")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    tree = subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], cwd=ROOT, text=True).strip()
    manifest_path = ROOT / "docs/ctrl/CTRL-04/CTRL04_C1_CANDIDATE_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text())
    require(manifest["candidate_state"] == "CANDIDATE_NOT_ACCEPTED", "manifest state")
    require(manifest["self_acceptance"] is False, "manifest self-acceptance")
    require(
        manifest["repository_commit"] == head and manifest["repository_tree"] == tree,
        "manifest identity",
    )
    require(
        manifest["gates"]["passed"] == 52 and manifest["mutations"]["detected"] == 48,
        "manifest counts",
    )

    with tempfile.TemporaryDirectory(prefix="ctrl04-seal-") as td:
        stage = Path(td) / NAME
        stage.mkdir()
        for source in sorted(ROOT.rglob("*")):
            if not source.is_file() or not allowed(source):
                continue
            target = stage / source.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        files = [p for p in sorted(stage.rglob("*")) if p.is_file() and p.name != "SHA256SUMS.txt"]
        sums = "".join(f"{digest(p)}  {p.relative_to(stage).as_posix()}\n" for p in files)
        (stage / "SHA256SUMS.txt").write_text(sums)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(args.out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for path in sorted(stage.rglob("*")):
                if not path.is_file():
                    continue
                info = zipfile.ZipInfo(
                    (Path(NAME) / path.relative_to(stage)).as_posix(),
                    date_time=(1980, 1, 1, 0, 0, 0),
                )
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, path.read_bytes(), compresslevel=9)

    sha = digest(args.out)
    size = args.out.stat().st_size
    identity = {
        "schema": "epd2.ctrl04.external-package-identity/1",
        "stage": "CTRL-04",
        "file": args.out.name,
        "sha256": sha,
        "size": size,
        "repository_commit": head,
        "repository_tree": tree,
        "gates": "52/52 PASS",
        "mutations": "48/48 DETECTED",
        "e2e_journeys": "20/20 PASS",
        "browser_journeys": f"{browser.get('journeys_passed')}/4 PASS",
        "tests": result["tests"],
        "candidate_state": "CANDIDATE_NOT_ACCEPTED",
        "self_acceptance": False,
        "terminal_marker": f"CTRL04_PRESEAL_RESULT:PASS:{sha}:{size}",
    }
    args.out.with_suffix(".identity.json").write_text(
        json.dumps(identity, indent=2, sort_keys=True) + "\n"
    )
    sealed_manifest = {
        **manifest,
        "candidate_zip": args.out.name,
        "candidate_sha256": sha,
        "candidate_size": size,
    }
    args.out.with_name(f"{NAME}.manifest.json").write_text(
        json.dumps(sealed_manifest, indent=2, sort_keys=True) + "\n"
    )
    verify = subprocess.run(
        [
            str(ROOT / ".venv/bin/python"),
            str(ROOT / "scripts/verify_ctrl04_package.py"),
            str(args.out),
        ],
        cwd=ROOT,
        text=True,
        check=False,
    )
    require(verify.returncode == 0, "post-seal package verification failed")
    print(identity["terminal_marker"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
