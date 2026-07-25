"""Repository-level test: canon and repository versions must be consistent.

Must be run from the repository root (see docs/development/local-development.md).
"""

from scripts.verify_versions import REPO_ROOT, find_mismatches


def test_versions_are_consistent() -> None:
    mismatches = find_mismatches(REPO_ROOT)
    assert mismatches == [], f"Version mismatches: {mismatches}"
