#!/usr/bin/env python3
"""Check that forbidden files and directories are absent from the repository.

Usage:
    python scripts/check_forbidden_files.py

Per CLAUDE-PACK-01 section 16 ("check_forbidden_files.py"), the repository
must not contain: `.env`, private keys, files named `id_rsa` / `id_ed25519`,
`*.pem` files (except explicitly allowed test fixtures), `node_modules`,
`.venv`, `__pycache__`, `.DS_Store`, real database files, or archives with
unknown contents.

Per CLAUDE-PACK-02 section 15, this also checks for the absence of a
forbidden central identity-participation mapping table or file: a filename
that names an identity/person entity together with a credential,
participation, or account entity *and* an explicit "map"/"link"/"join"-style
word (e.g. `identity_credential_map.py`, `person_participation_link.json`).
This is a structural, filename-based heuristic only - it cannot detect a
mapping expressed purely as runtime data or as a column pairing inside an
otherwise innocuously-named file, but it catches the concrete, statically
detectable case the pack asks for. It is deliberately narrow (requires a
link-style word) so it does not flag legitimate schema/service files that
merely mention both an identity term and a credential/participation term,
such as `contracts/schemas/participation-credential.schema.json` (the
ParticipationCredential schema, not a mapping table).

This check is git-aware: it evaluates the set of paths that are tracked, or
would be trackable (untracked and not `.gitignore`-excluded), via
`git ls-files --cached --others --exclude-standard`. This matters because
running the project's own tooling (pytest, mypy, ruff) legitimately creates
local cache directories such as `.pytest_cache/`, `.mypy_cache/`, and
`__pycache__/` — all of which are already excluded via `.gitignore` and
would never actually be committed. Flagging them as "forbidden" during a
normal `make verify` run (which runs mypy/ruff/pytest before this check
could plausibly run again as part of the Python test suite) would be a
false positive having nothing to do with repository hygiene. Checking only
git-trackable paths means the result reflects what would actually end up in
version control, not incidental local build artifacts.

If the repository is not (yet) a git repository, this falls back to a full
filesystem walk and prints a warning, since "what would be committed" cannot
be determined without git.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Directory names that must not be present among git-trackable paths.
FORBIDDEN_DIR_NAMES = {
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}

# Exact file names that must not be present among git-trackable paths.
FORBIDDEN_FILE_NAMES = {
    ".env",
    "id_rsa",
    "id_ed25519",
    ".DS_Store",
}

# Suffixes that must not be present among git-trackable paths.
FORBIDDEN_SUFFIXES = {
    ".pem",
    ".key",
    ".sqlite3",
    ".db",
}

# Archive suffixes: not forbidden by extension alone, but their contents
# cannot be verified by this script, so any archive found is flagged for
# manual review (per CLAUDE-PACK-01 section 16: "archives with unknown
# contents").
ARCHIVE_SUFFIXES = {".zip", ".tar", ".gz", ".tgz", ".7z", ".rar"}

# Paths (relative to repo root) explicitly allowed to contain a `.pem`
# fixture for contract tests, per section 16 of CLAUDE-PACK-01
# ("except explicitly allowed test fixtures").
ALLOWED_PEM_FIXTURE_DIRS = ("contracts/fixtures", "tests/fixtures")


def _is_allowed_pem_fixture(rel_posix: str) -> bool:
    if not rel_posix.endswith(".pem"):
        return False
    return any(rel_posix.startswith(f"{allowed}/") for allowed in ALLOWED_PEM_FIXTURE_DIRS)


# CLAUDE-PACK-02 section 15: forbidden central identity-participation
# mapping table/file, detected by filename. A match requires an identity
# term, a participation-adjacent term, AND an explicit link/mapping word -
# all three - so ordinary schema/service filenames that merely mention two
# domain nouns (e.g. `participation-credential.schema.json`) are never
# flagged.
_IDENTITY_TERMS = ("identity", "person")
_PARTICIPATION_TERMS = ("participation", "credential", "account")
_LINK_TERMS = ("map", "mapping", "link", "linkage", "join", "bridge")


def _is_forbidden_identity_link_filename(name: str) -> bool:
    lower = name.lower()
    has_identity = any(term in lower for term in _IDENTITY_TERMS)
    has_participation = any(term in lower for term in _PARTICIPATION_TERMS)
    has_link = any(term in lower for term in _LINK_TERMS)
    return has_identity and has_participation and has_link


def _git_trackable_paths(root: Path) -> list[str] | None:
    """Return git-relative paths that are tracked or trackable (untracked
    and not gitignored), or None if `root` is not a git repository / git is
    unavailable."""
    if not (root / ".git").exists():
        return None
    try:
        result = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return [line for line in result.stdout.splitlines() if line]


def _walk_all_paths(root: Path) -> list[str]:
    """Fallback: every path under `root`, relative, as posix strings,
    skipping `.git` itself. Used only when `root` is not a git repository."""
    paths = []
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if rel.parts and rel.parts[0] == ".git":
            continue
        paths.append(rel.as_posix())
    return paths


def find_forbidden_paths(root: Path) -> list[str]:
    """Return a list of forbidden paths (relative, as strings) found among
    git-trackable paths under `root` (or, without git, among all paths)."""
    rel_paths = _git_trackable_paths(root)
    used_git = rel_paths is not None
    if rel_paths is None:
        rel_paths = _walk_all_paths(root)

    found: set[str] = set()

    for rel_posix in rel_paths:
        parts = rel_posix.split("/")
        name = parts[-1]

        for i, part in enumerate(parts[:-1] if used_git else parts):
            if part in FORBIDDEN_DIR_NAMES:
                found.add("/".join(parts[: i + 1]) + "/")

        if used_git:
            # `git ls-files` only ever lists files, never directories, so
            # forbidden directory names can only show up as intermediate
            # path components (handled above) — nothing further to do for
            # the file itself unless it also matches a file-level rule.
            pass
        else:
            # Non-git fallback also walks real directory entries; check the
            # last component too, since `_walk_all_paths` yields both files
            # and directories.
            if (root / rel_posix).is_dir() and name in FORBIDDEN_DIR_NAMES:
                found.add(f"{rel_posix}/")
                continue

        if (root / rel_posix).is_dir():
            continue

        if name in FORBIDDEN_FILE_NAMES:
            found.add(rel_posix)
            continue

        if _is_forbidden_identity_link_filename(name):
            found.add(rel_posix)
            continue

        suffix = f".{name.rsplit('.', 1)[-1]}" if "." in name else ""

        if suffix in FORBIDDEN_SUFFIXES and not _is_allowed_pem_fixture(rel_posix):
            found.add(rel_posix)
            continue

        if suffix in ARCHIVE_SUFFIXES:
            found.add(rel_posix)
            continue

    return sorted(found)


def main() -> int:
    if not (REPO_ROOT / ".git").exists():
        print(
            "WARNING: repository root is not a git repository; falling back "
            "to a full filesystem walk (local build caches may be flagged)."
        )
    forbidden = find_forbidden_paths(REPO_ROOT)
    if forbidden:
        print("Forbidden paths found:")
        for path in forbidden:
            print(f"  - {path}")
        return 1
    print("OK: no forbidden paths found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
