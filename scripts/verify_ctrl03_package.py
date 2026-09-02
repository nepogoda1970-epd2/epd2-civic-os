#!/usr/bin/env python3
"""Independently verify CTRL-03 archive safety, contents and same-byte manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
import zipfile
from pathlib import Path

FORBIDDEN_PARTS = {
    ".git",
    ".venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    args = parser.parse_args()
    if not args.archive.is_file():
        raise SystemExit("archive missing")
    with zipfile.ZipFile(args.archive) as archive:
        names = archive.namelist()
        if not names or any(Path(name).is_absolute() or ".." in Path(name).parts for name in names):
            raise SystemExit("unsafe archive path")
        if any(set(Path(name).parts) & FORBIDDEN_PARTS for name in names):
            raise SystemExit("archive hygiene failure")
        if any(
            Path(name).suffix.lower() in {".pyc", ".pyo", ".db", ".sqlite", ".zip"}
            for name in names
        ):
            raise SystemExit("forbidden runtime or nested archive")
        roots = {Path(name).parts[0] for name in names}
        if len(roots) != 1:
            raise SystemExit("archive must have one root")
        with tempfile.TemporaryDirectory(prefix="ctrl03-verify-") as td:
            archive.extractall(td)
            root = Path(td) / roots.pop()
            manifest = root / "SHA256SUMS.txt"
            if not manifest.is_file():
                raise SystemExit("manifest missing")
            expected_files: set[str] = set()
            for line in manifest.read_text().splitlines():
                expected, relative = line.split("  ", 1)
                expected_files.add(relative)
                target = root / relative
                if not target.is_file() or digest(target) != expected:
                    raise SystemExit(f"same-byte mismatch: {relative}")
            actual_files = {
                path.relative_to(root).as_posix()
                for path in root.rglob("*")
                if path.is_file() and path.name != "SHA256SUMS.txt"
            }
            if actual_files != expected_files:
                raise SystemExit("manifest coverage mismatch")
            result = json.loads((root / "validation/ctrl03/ctrl03_preseal_result.json").read_text())
            if (
                result["overall"] != "PASS"
                or result["gates_passed"] != 50
                or result["gates_failed"]
                or result["gates_blocked_for_final_seal"]
            ):
                raise SystemExit("gate evidence mismatch")
            if result["self_state"] != "NOT_ACCEPTED":
                raise SystemExit("developer self-acceptance forbidden")
            predecessor = json.loads(
                (root / "validation/ctrl03/ctrl02_authoritative_acceptance.json").read_text()
            )
            if (
                predecessor.get("stage") != "CTRL-02"
                or predecessor.get("conclusion") != "PASS"
                or predecessor.get("run_id") != 33690561259
                or predecessor.get("workflow_head_sha")
                != "a70e2bfef7a668ee5158475712827bbc50f6d5fd"
                or predecessor.get("candidate_sha256")
                != "f58bafe758f19c0b40d3a525d85d0315052c01bc9ed14eae9973079a4dfb993e"
                or predecessor.get("candidate_size") != 16720456
                or predecessor.get("self_acceptance") is not False
            ):
                raise SystemExit("CTRL02_RECONCILIATION_INVALID")
            mutation = json.loads((root / "validation/ctrl03/mutation_result.json").read_text())
            if mutation["detected"] != 44 or mutation["undetected"]:
                raise SystemExit("mutation evidence mismatch")
    print(f"CTRL03_PACKAGE_VERIFY:PASS:{digest(args.archive)}:{args.archive.stat().st_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
