#!/usr/bin/env python3
"""Seal the deterministic CTRL-05 C1 candidate and emit its external identity.

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
NAME = "EPD2_CTRL05_AUDIT_AND_OVERSIGHT_CONSOLE_CANDIDATE_0.1_C1"
VALIDATION = ROOT / "validation/ctrl05"
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
    result = json.loads((VALIDATION / "preseal_result.json").read_text())
    require(result["overall"] == "PASS", "developer validator has not passed")
    require(result["gates_passed"] == 56 and not result["gates_failed"], "gate disposition")
    require(result["self_state"] == "CANDIDATE_NOT_ACCEPTED", "self-state")
    require(result["self_acceptance"] is False, "self-acceptance")
    mutation = json.loads((VALIDATION / "mutation_result.json").read_text())
    require(
        mutation["detected"] == 52 and not mutation["undetected"], "mutation suite is not 52/52"
    )
    e2e = json.loads((VALIDATION / "e2e_journeys_result.json").read_text())
    require(e2e["journeys_passed"] == 22, "E2E journeys are not 22/22")
    browser = json.loads((VALIDATION / "browser_journeys_result.json").read_text())
    require(browser.get("status") == "PASS", "browser journeys did not pass")
    freeze = json.loads((VALIDATION / "source_freeze.json").read_text())
    for rel, expected in freeze["files"].items():
        require(digest(ROOT / rel) == expected, f"freeze drift: {rel}")
    import sys

    sys.path.insert(0, str(ROOT / "scripts"))
    from ctrl05_common import runtime_source_digest  # type: ignore[import-not-found]

    digest_now = runtime_source_digest()
    for name, payload in (
        ("mutation", mutation),
        ("e2e", e2e),
        ("browser", browser),
    ):
        require(
            payload.get("runtime_source_digest") == digest_now,
            f"{name} evidence was produced from different runtime bytes",
        )
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    tree = subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], cwd=ROOT, text=True).strip()
    manifest_path = ROOT / "docs/ctrl/CTRL-05/CTRL05_C1_CANDIDATE_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text())
    require(manifest["candidate_state"] == "CANDIDATE_NOT_ACCEPTED", "manifest state")
    require(manifest["self_acceptance"] is False, "manifest self-acceptance")
    require(
        manifest["repository_commit"] == head and manifest["repository_tree"] == tree,
        "manifest identity",
    )
    require(
        manifest["gates"]["passed"] == 56 and manifest["mutations"]["detected"] == 52,
        "manifest counts",
    )

    with tempfile.TemporaryDirectory(prefix="ctrl05-seal-") as td:
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
        "schema": "epd2.ctrl05.external-package-identity/1",
        "stage": "CTRL-05",
        "file": args.out.name,
        "sha256": sha,
        "size": size,
        "repository_commit": head,
        "repository_tree": tree,
        "gates": "56/56 PASS",
        "mutations": "52/52 DETECTED",
        "e2e_journeys": "22/22 PASS",
        "browser_journeys": (
            f"{browser.get('journeys_passed')}/{browser.get('journeys_total')} PASS"
        ),
        "tests": result["tests"],
        "runtime_source_digest": digest_now,
        "candidate_state": "CANDIDATE_NOT_ACCEPTED",
        "self_acceptance": False,
        "terminal_marker": f"CTRL05_PRESEAL_RESULT:PASS:{sha}:{size}",
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
            str(ROOT / "scripts/verify_ctrl05_package.py"),
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
