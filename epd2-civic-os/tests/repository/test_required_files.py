"""Repository-level test: required files and directories must exist.

Must be run from the repository root (see docs/development/local-development.md).
"""

from pathlib import Path

from scripts.check_repository import REPO_ROOT, find_missing_required_paths


def test_no_required_paths_are_missing() -> None:
    missing = find_missing_required_paths(REPO_ROOT)
    assert missing == [], f"Missing required paths: {missing}"


def test_repo_root_resolves_to_repository_root() -> None:
    # Sanity check: REPO_ROOT should contain this very test file.
    assert Path(__file__).resolve() == (REPO_ROOT / "tests/repository/test_required_files.py")
