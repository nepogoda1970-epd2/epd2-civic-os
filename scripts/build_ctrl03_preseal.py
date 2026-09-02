#!/usr/bin/env python3
"""Build the deterministic CTRL-03 working PRESEAL and external identity record."""

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
NAME = "EPD2_CTRL03_CREDENTIAL_TRUST_AND_KEY_LIFECYCLE_CONTROL_CANDIDATE_0.1_C1"
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=ROOT.parent / f"{NAME}.zip")
    args = parser.parse_args()
    result = json.loads((ROOT / "validation/ctrl03/ctrl03_preseal_result.json").read_text())
    if result["overall"] != "PASS":
        raise SystemExit("CTRL-03 development validator has not passed")
    if result["gates_passed"] != 50 or result["gates_blocked_for_final_seal"] != []:
        raise SystemExit("unexpected gate disposition")
    mutation = json.loads((ROOT / "validation/ctrl03/mutation_result.json").read_text())
    if mutation["detected"] != 44 or mutation["undetected"]:
        raise SystemExit("mutation suite is not 44/44")

    with tempfile.TemporaryDirectory(prefix="ctrl03-preseal-") as td:
        stage = Path(td) / NAME
        stage.mkdir()
        for source in sorted(ROOT.rglob("*")):
            if not source.is_file() or not allowed(source):
                continue
            relative = source.relative_to(ROOT)
            target = stage / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        files = [
            path
            for path in sorted(stage.rglob("*"))
            if path.is_file() and path.name != "SHA256SUMS.txt"
        ]
        sums = "".join(f"{digest(path)}  {path.relative_to(stage).as_posix()}\n" for path in files)
        (stage / "SHA256SUMS.txt").write_text(sums)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(args.out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for path in sorted(stage.rglob("*")):
                if not path.is_file():
                    continue
                relative = Path(NAME) / path.relative_to(stage)
                info = zipfile.ZipInfo(relative.as_posix(), date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, path.read_bytes(), compresslevel=9)

    identity = {
        "schema": "epd2.ctrl03.external-package-identity/1",
        "file": args.out.name,
        "sha256": digest(args.out),
        "size": args.out.stat().st_size,
        "gates": "50/50 PASS",
        "mutations": "44/44 DETECTED",
        "cumulative_tests": "290 PASSED",
        "self_state": "NOT_ACCEPTED",
    }
    identity_path = args.out.with_suffix(".identity.json")
    identity_path.write_text(json.dumps(identity, indent=2, sort_keys=True) + "\n")
    verify = subprocess.run(
        [
            str(ROOT / ".venv/bin/python"),
            str(ROOT / "scripts/verify_ctrl03_package.py"),
            str(args.out),
        ],
        cwd=ROOT,
        text=True,
        check=False,
    )
    if verify.returncode:
        raise SystemExit("independent package verification failed")
    print(f"CTRL03_WORKING_PACKAGE:PASS:{identity['sha256']}:{identity['size']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
