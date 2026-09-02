#!/usr/bin/env python3
"""Rehearse immutable packaging and prove source-to-ZIP byte equality."""

from __future__ import annotations

import hashlib
import json
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "validation/api06/freeze_rehearsal_result.json"
EXCLUDED_PARTS = {
    ".git",
    ".venv",
    ".api03-venv",
    ".api03-crypto",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}


def governed_files():
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        if set(rel.parts) & EXCLUDED_PARTS or path.suffix in EXCLUDED_SUFFIXES:
            continue
        if rel == OUT.relative_to(ROOT) or path.suffix == ".zip":
            continue
        yield path, rel


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    before = {str(rel): digest(path) for path, rel in governed_files()}
    with tempfile.TemporaryDirectory(prefix="api06-freeze-") as tmp:
        archive = Path(tmp) / "rehearsal.zip"
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_STORED) as out:
            for path, rel in governed_files():
                out.write(path, f"API06_REHEARSAL/{rel.as_posix()}")
        after = {str(rel): digest(path) for path, rel in governed_files()}
        with zipfile.ZipFile(archive) as frozen:
            names = frozen.namelist()
            archive_hashes = {
                name.removeprefix("API06_REHEARSAL/"): hashlib.sha256(frozen.read(name)).hexdigest()
                for name in names
            }
        bad_paths = [name for name in names if name.startswith("/") or "/../" in f"/{name}/"]
        result = "PASS" if before == after == archive_hashes and not bad_paths else "FAIL"
        payload = {
            "schema": "epd2.api06.freeze-rehearsal/1",
            "result": result,
            "file_count": len(before),
            "source_unchanged": before == after,
            "archive_byte_equal": before == archive_hashes,
            "unsafe_paths": bad_paths,
            "tree_digest": hashlib.sha256(json.dumps(before, sort_keys=True).encode()).hexdigest(),
        }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(f"API06_FREEZE_REHEARSAL:{result}:{payload['file_count']}:{payload['tree_digest']}")
    return 0 if result == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
