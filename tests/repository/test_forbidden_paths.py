"""Repository-level test: forbidden files and directories must be absent.

Must be run from the repository root (see docs/development/local-development.md).
"""

from scripts.check_forbidden_files import REPO_ROOT, find_forbidden_paths


def test_no_forbidden_paths_present() -> None:
    forbidden = find_forbidden_paths(REPO_ROOT)
    assert forbidden == [], f"Forbidden paths found: {forbidden}"
