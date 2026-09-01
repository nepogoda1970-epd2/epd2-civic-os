"""Freeze/package hygiene (INFRA01-HI-06).

The acceptance path rejects development debris, nested repositories, nested
candidate archives, duplicate or unsafe archive paths, machine-local paths
and undeclared generated artifacts. Exceptions come only from the one
canonical governed allowlist ``packaging_allowlist.json``.
"""

from __future__ import annotations

import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from scripts.acceptance import codes
from scripts.acceptance.canonical import load_json

ALLOWLIST_FILE = Path(__file__).resolve().parent / "packaging_allowlist.json"

#: Directory names that never enter a candidate, at any depth.
FORBIDDEN_DIRECTORY_NAMES = frozenset(
    {
        ".venv",
        "venv",
        ".direnv",
        "node_modules",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".hypothesis",
        ".next",
        ".turbo",
        ".swc",
        "htmlcov",
        "coverage",
        "test-results",
        "playwright-report",
        ".idea",
        ".vscode",
        "dist",
        "build",
        ".cache",
        ".uv-cache",
        ".npm",
    }
)

#: File names that never enter a candidate.
FORBIDDEN_FILE_NAMES = frozenset(
    {
        ".DS_Store",
        "Thumbs.db",
        "desktop.ini",
        ".env",
        "tsconfig.tsbuildinfo",
        ".coverage",
    }
)

#: Suffixes that never enter a candidate.
FORBIDDEN_SUFFIXES = (".pyc", ".pyo", ".orig", ".rej", ".swp", ".tmp", ".bak")

#: Nested archives are candidate-in-candidate smuggling unless governed.
ARCHIVE_SUFFIXES = (".zip", ".tar", ".gz", ".tgz", ".7z", ".rar", ".xz", ".bz2")

#: Member names that reveal machine-local paths.
_MACHINE_LOCAL_MARKERS = ("/home/", "/Users/", "C:\\", "D:\\", "AppData", "/tmp/")


@dataclass(frozen=True)
class HygieneFinding:
    code: str
    path: str
    detail: str


def load_allowlist(allowlist_file: Path = ALLOWLIST_FILE) -> dict[str, list[str]]:
    document = load_json(allowlist_file)
    return {
        "governed_additions": [str(item) for item in document["governed_additions"]],
        "allowed_nested_archives": [str(item) for item in document["allowed_nested_archives"]],
        "allowed_empty_directories": [str(item) for item in document["allowed_empty_directories"]],
    }


def _check_relative_path(
    rel_posix: str, allowed_archives: frozenset[str], is_dir: bool
) -> list[HygieneFinding]:
    findings: list[HygieneFinding] = []
    parts = PurePosixPath(rel_posix).parts
    name = parts[-1] if parts else rel_posix

    for part in parts[:-1] if not is_dir else parts:
        if part in FORBIDDEN_DIRECTORY_NAMES:
            findings.append(
                HygieneFinding(codes.FORBIDDEN_PATH, rel_posix, f"forbidden directory {part!r}")
            )
            break
    if ".git" in parts[1:] or (len(parts) > 1 and parts[0] == ".git"):
        findings.append(
            HygieneFinding(codes.NESTED_REPOSITORY, rel_posix, "repository metadata in candidate")
        )
    if not is_dir:
        if name in FORBIDDEN_DIRECTORY_NAMES and len(parts) > 1:
            pass  # a *file* merely named like a forbidden dir is handled below by suffix/name rules
        if name in FORBIDDEN_FILE_NAMES or (
            name.startswith(".env.") and name != ".env.example" and not name.endswith(".example")
        ):
            findings.append(
                HygieneFinding(codes.FORBIDDEN_PATH, rel_posix, f"forbidden file {name!r}")
            )
        lowered = name.lower()
        if lowered.endswith(FORBIDDEN_SUFFIXES):
            findings.append(
                HygieneFinding(codes.FORBIDDEN_PATH, rel_posix, "forbidden temporary suffix")
            )
        if lowered.endswith(ARCHIVE_SUFFIXES) and rel_posix not in allowed_archives:
            findings.append(
                HygieneFinding(codes.NESTED_ARCHIVE, rel_posix, "undeclared nested archive")
            )
    return findings


def scan_tree(root: Path, allowlist: dict[str, list[str]] | None = None) -> list[HygieneFinding]:
    """Scan a working tree that is about to be frozen/packaged."""
    resolved = allowlist or load_allowlist()
    allowed_archives = frozenset(resolved["allowed_nested_archives"])
    findings: list[HygieneFinding] = []
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root).as_posix()
        if rel == ".git" or rel.startswith(".git/"):
            continue  # the candidate's own checkout metadata is excluded at packaging, not nested
        nested_git = path.name == ".git" and path.parent != root
        if nested_git:
            findings.append(
                HygieneFinding(codes.NESTED_REPOSITORY, rel, "nested repository copy in candidate")
            )
            continue
        findings.extend(_check_relative_path(rel, allowed_archives, path.is_dir()))
    return findings


def scan_archive(
    archive: Path, allowlist: dict[str, list[str]] | None = None
) -> list[HygieneFinding]:
    """Scan a produced candidate archive: hygiene, duplicates, unsafe paths."""
    resolved = allowlist or load_allowlist()
    allowed_archives = frozenset(resolved["allowed_nested_archives"])
    findings: list[HygieneFinding] = []
    with zipfile.ZipFile(archive) as bundle:
        names = bundle.namelist()
        seen: set[str] = set()
        seen_case_insensitive: dict[str, str] = {}
        roots = {name.split("/", 1)[0] for name in names if name}
        if len(roots) != 1:
            findings.append(
                HygieneFinding(
                    codes.UNSAFE_ARCHIVE_PATH,
                    archive.name,
                    f"archive must have exactly one root, found {sorted(roots)!r}",
                )
            )
        for name in names:
            if name in seen:
                findings.append(
                    HygieneFinding(codes.DUPLICATE_ARCHIVE_PATH, name, "duplicate archive member")
                )
            seen.add(name)
            lowered = name.lower()
            if lowered in seen_case_insensitive and seen_case_insensitive[lowered] != name:
                findings.append(
                    HygieneFinding(
                        codes.DUPLICATE_ARCHIVE_PATH,
                        name,
                        f"case collision with {seen_case_insensitive[lowered]!r}",
                    )
                )
            seen_case_insensitive.setdefault(lowered, name)
            if any(marker in name for marker in _MACHINE_LOCAL_MARKERS):
                findings.append(
                    HygieneFinding(codes.MACHINE_LOCAL_PATH, name, "machine-local path in member")
                )
            if name.startswith("/") or ".." in PurePosixPath(name).parts or "\\" in name:
                findings.append(
                    HygieneFinding(codes.UNSAFE_ARCHIVE_PATH, name, "absolute or traversal path")
                )
                continue
            interior = name.split("/", 1)[1] if "/" in name else name
            if interior:
                findings.extend(
                    _check_relative_path(interior, allowed_archives, name.endswith("/"))
                )
    return findings
