#!/usr/bin/env python3
"""Check that required repository files and directories exist.

Usage:
    python scripts/check_repository.py

Exits with a non-zero status and prints every missing path if anything
required is absent. Run from anywhere; the repository root is resolved
relative to this script's location.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Required top-level files and directories, per CLAUDE-PACK-01 section 5
# ("Final repository structure"). Paths are relative to the repository
# root. This intentionally does not enumerate every possible file - it
# enumerates the files and directories the package definition requires to
# exist.
REQUIRED_PATHS: tuple[str, ...] = (
    # Root
    "README.md",
    "LICENSE",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "CODEOWNERS",
    "CHANGELOG.md",
    "LOCAL_VERIFICATION.md",
    "Makefile",
    ".editorconfig",
    ".gitignore",
    ".pre-commit-config.yaml",
    "pyproject.toml",
    "uv.lock",
    "package.json",
    "package-lock.json",
    # GitHub
    ".github/workflows/ci.yml",
    ".github/pull_request_template.md",
    ".github/ISSUE_TEMPLATE/bug_report.yml",
    ".github/ISSUE_TEMPLATE/feature_request.yml",
    ".github/ISSUE_TEMPLATE/architecture_change.yml",
    # Docs: canonical
    "docs/canonical/README.md",
    "docs/canonical/TZ-00-domain-event-canon.md",
    "docs/canonical/canon-version.json",
    # Docs: architecture
    "docs/architecture/system-context.md",
    "docs/architecture/service-boundaries.md",
    "docs/architecture/data-ownership.md",
    # Docs: adr
    "docs/adr/README.md",
    "docs/adr/ADR-000-template.md",
    "docs/adr/ADR-001-repository-strategy.md",
    # Docs: development
    "docs/development/local-development.md",
    "docs/development/repository-rules.md",
    "docs/development/new-module-guide.md",
    # Docs: review
    "docs/review/OPEN_QUESTIONS.md",
    "docs/review/KNOWN_LIMITATIONS.md",
    # Docs: handover
    "docs/handover/PACK-01-REPORT.md",
    # Contracts
    "contracts/README.md",
    "contracts/openapi",
    "contracts/events",
    "contracts/schemas",
    "contracts/reason-codes/README.md",
    "contracts/fixtures",
    # Services (placeholder)
    "services/README.md",
    # Python packages
    "packages/python/README.md",
    "packages/python/epd2-core/README.md",
    "packages/python/epd2-core/pyproject.toml",
    "packages/python/epd2-core/src/epd2_core/__init__.py",
    "packages/python/epd2-core/src/epd2_core/version.py",
    "packages/python/epd2-core/src/epd2_core/identifiers.py",
    "packages/python/epd2-core/tests/test_version.py",
    "packages/python/epd2-core/tests/test_identifiers.py",
    # TypeScript packages
    "packages/typescript/README.md",
    "packages/typescript/epd2-types/README.md",
    "packages/typescript/epd2-types/package.json",
    "packages/typescript/epd2-types/tsconfig.json",
    "packages/typescript/epd2-types/src/index.ts",
    "packages/typescript/epd2-types/src/version.ts",
    "packages/typescript/epd2-types/tests/version.test.ts",
    # Frontend
    "frontend/README.md",
    "frontend/web-shell/README.md",
    "frontend/web-shell/package.json",
    "frontend/web-shell/next.config.ts",
    "frontend/web-shell/tsconfig.json",
    "frontend/web-shell/eslint.config.mjs",
    "frontend/web-shell/app/layout.tsx",
    "frontend/web-shell/app/page.tsx",
    "frontend/web-shell/tests/smoke.test.ts",
    # Scripts
    "scripts/check_repository.py",
    "scripts/check_forbidden_files.py",
    "scripts/verify_versions.py",
    # Tests
    "tests/repository/test_required_files.py",
    "tests/repository/test_forbidden_paths.py",
    "tests/repository/test_version_consistency.py",
)


def find_missing_required_paths(root: Path) -> list[str]:
    """Return the list of required paths (relative, as strings) that are
    missing under `root`."""
    missing: list[str] = []
    for rel_path in REQUIRED_PATHS:
        if not (root / rel_path).exists():
            missing.append(rel_path)
    return missing


def main() -> int:
    missing = find_missing_required_paths(REPO_ROOT)
    if missing:
        print("Missing required paths:")
        for path in missing:
            print(f"  - {path}")
        return 1
    print(f"OK: all {len(REQUIRED_PATHS)} required paths are present.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
