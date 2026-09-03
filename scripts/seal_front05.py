#!/usr/bin/env python3
"""Seal the FRONT-05 C1 candidate archive.

Archive hygiene is enforced by construction rather than by a post-hoc scan: the
walker refuses to descend into an excluded directory, so a build output or an
installed dependency tree cannot end up inside and then be noticed later. The
manifest it writes is what gate G43 reads.

Determinism matters here. Entries are added in sorted order with a fixed
timestamp and fixed permissions, so sealing the same tree twice produces the
same bytes — which is what makes "the same bytes were reviewed" a checkable
statement rather than a hope.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import zipfile
from pathlib import Path

NAME = "EPD2_FRONT05_WS04_REPRESENTATIVE_WORKSPACE_CANDIDATE_0.1_C1.zip"

EXCLUDED_DIRS = {
    "node_modules", ".next", ".git", "test-results", "playwright-report",
    "coverage", "__pycache__", ".turbo", ".swc", ".venv", ".ruff_cache",
    ".pytest_cache", ".mypy_cache",
}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".env", ".pem", ".key", ".p12", ".pfx"}
EXCLUDED_NAMES = {".DS_Store", "tsconfig.tsbuildinfo", ".env", ".env.local"}

FIXED_TIME = (2026, 1, 1, 0, 0, 0)

# Three artifacts describe the archive and therefore cannot be inside it. Putting
# any of them in would also break determinism: sealing writes them, so the second
# seal of the same tree would differ from the first, and "the same bytes were
# reviewed" would stop being checkable. They live beside the archive instead, the
# same way the detached .sha256 does.
SELF_DESCRIBING = {
    NAME,
    f"{NAME}.sha256",
    "validation/front05/archive_manifest.json",
}


def collect(root: Path) -> list[Path]:
    out: list[Path] = []

    def walk(directory: Path) -> None:
        for entry in sorted(directory.iterdir()):
            if entry.is_symlink():
                continue
            if entry.is_dir():
                if entry.name in EXCLUDED_DIRS:
                    continue
                walk(entry)
                continue
            if entry.name in EXCLUDED_NAMES or entry.suffix in EXCLUDED_SUFFIXES:
                continue
            out.append(entry)

    walk(root)
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    root = Path(args.root).resolve()
    target = Path(args.out) if args.out else root / NAME
    if target.exists():
        target.unlink()

    files = collect(root)
    entries: list[str] = []
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            relative = path.relative_to(root).as_posix()
            if relative in SELF_DESCRIBING:
                continue
            info = zipfile.ZipInfo(relative, date_time=FIXED_TIME)
            info.external_attr = 0o644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, path.read_bytes())
            entries.append(relative)

    data = target.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    (target.parent / f"{target.name}.sha256").write_text(
        f"{sha}  {target.name}\n", encoding="utf-8"
    )

    manifest = {
        "schema": "epd2.front05.archive-manifest/1",
        "stage": "FRONT-05 — WS-04 Representative Workspace",
        "candidate_state": "CANDIDATE_NOT_ACCEPTED",
        "filename": target.name,
        "sha256": sha,
        "size_bytes": len(data),
        "entry_count": len(entries),
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "excluded_directories": sorted(EXCLUDED_DIRS),
        "excluded_suffixes": sorted(EXCLUDED_SUFFIXES),
        "deterministic": "entries added in sorted order with a fixed timestamp and fixed permissions",
        "entries": entries,
    }
    out = root / "validation/front05/archive_manifest.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"{target.name}")
    print(f"  sha256 {sha}")
    print(f"  size   {len(data)}")
    print(f"  files  {len(entries)}")
    print(f"FRONT05_C1_CANDIDATE_RESULT:PASS:{sha}:{len(data)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
