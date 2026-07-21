#!/usr/bin/env python3
"""Verify that canon and repository version numbers are consistent.

Usage:
    python scripts/verify_versions.py

Checks consistency across:
    - packages/python/epd2-core/src/epd2_core/version.py (CANON_VERSION, REPOSITORY_VERSION)
    - packages/typescript/epd2-types/src/version.ts (CANON_VERSION, REPOSITORY_VERSION)
    - docs/canonical/canon-version.json (canon_version)
    - CHANGELOG.md (latest entry version)

Exits with a non-zero status and prints every mismatch found.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _extract_py_constant(text: str, name: str, source: Path) -> str:
    match = re.search(rf'^{name}\s*=\s*"([^"]+)"', text, flags=re.MULTILINE)
    if not match:
        raise ValueError(f"Could not find {name} in {source}")
    return match.group(1)


def _extract_ts_constant(text: str, name: str, source: Path) -> str:
    match = re.search(rf'export const {name}\s*=\s*"([^"]+)"', text)
    if not match:
        raise ValueError(f"Could not find {name} in {source}")
    return match.group(1)


def _extract_changelog_version(text: str, source: Path) -> str:
    match = re.search(r"^## \[(\d+\.\d+\.\d+)\]", text, flags=re.MULTILINE)
    if not match:
        raise ValueError(f"Could not find a version heading in {source}")
    return match.group(1)


def collect_versions(root: Path) -> dict[str, str]:
    """Collect every version value that must stay consistent."""
    py_version_file = root / "packages/python/epd2-core/src/epd2_core/version.py"
    ts_version_file = root / "packages/typescript/epd2-types/src/version.ts"
    canon_json_file = root / "docs/canonical/canon-version.json"
    changelog_file = root / "CHANGELOG.md"

    py_text = py_version_file.read_text()
    ts_text = ts_version_file.read_text()
    canon_json = json.loads(canon_json_file.read_text())
    changelog_text = changelog_file.read_text()

    return {
        "python.CANON_VERSION": _extract_py_constant(py_text, "CANON_VERSION", py_version_file),
        "python.REPOSITORY_VERSION": _extract_py_constant(
            py_text, "REPOSITORY_VERSION", py_version_file
        ),
        "typescript.CANON_VERSION": _extract_ts_constant(ts_text, "CANON_VERSION", ts_version_file),
        "typescript.REPOSITORY_VERSION": _extract_ts_constant(
            ts_text, "REPOSITORY_VERSION", ts_version_file
        ),
        "canon_version.json": str(canon_json["canon_version"]),
        "CHANGELOG.md": _extract_changelog_version(changelog_text, changelog_file),
    }


def find_mismatches(root: Path) -> list[str]:
    """Return a list of human-readable mismatch descriptions, empty if
    everything is consistent."""
    versions = collect_versions(root)

    canon_sources = {
        "python.CANON_VERSION": versions["python.CANON_VERSION"],
        "typescript.CANON_VERSION": versions["typescript.CANON_VERSION"],
        "canon_version.json": versions["canon_version.json"],
    }
    repository_sources = {
        "python.REPOSITORY_VERSION": versions["python.REPOSITORY_VERSION"],
        "typescript.REPOSITORY_VERSION": versions["typescript.REPOSITORY_VERSION"],
        "CHANGELOG.md": versions["CHANGELOG.md"],
    }

    mismatches: list[str] = []

    canon_values = set(canon_sources.values())
    if len(canon_values) > 1:
        mismatches.append(f"Canon version mismatch across sources: {canon_sources}")

    repository_values = set(repository_sources.values())
    if len(repository_values) > 1:
        mismatches.append(f"Repository version mismatch across sources: {repository_sources}")

    return mismatches


def main() -> int:
    try:
        mismatches = find_mismatches(REPO_ROOT)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"ERROR while verifying versions: {exc}")
        return 1

    if mismatches:
        print("Version mismatches found:")
        for mismatch in mismatches:
            print(f"  - {mismatch}")
        return 1

    print("OK: all version sources are consistent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
