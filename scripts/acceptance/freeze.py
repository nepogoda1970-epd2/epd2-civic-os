"""Freeze: the exact byte inventory of the tested tree (INFRA01-HI-02).

The freeze inventory is the bridge between "what was tested" and "what is
packaged": it lists every governed source file with its SHA-256 at the moment
testing finished. Packaging may only write those exact bytes plus the
governed additions from the canonical allowlist; ``verify-package`` then
proves the equality again from the archive side.

The inventory is derived from Git's tracked-file list, and freezing fails
closed when the working tree diverges from it: a modified tracked file means
the tested bytes are not the committed bytes, and an untracked file outside
the recognized generated locations means the tested tree contains source that
would silently not be packaged.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from scripts.acceptance import codes
from scripts.acceptance.canonical import sha256_bytes, sha256_file
from scripts.acceptance.hygiene import FORBIDDEN_DIRECTORY_NAMES, HygieneFinding

#: Locations generated material may legitimately occupy in a working tree
#: while tests run. Anything untracked outside these fails the freeze.
GENERATED_LOCATION_NAMES = FORBIDDEN_DIRECTORY_NAMES | {".git", ".acceptance-run"}


@dataclass(frozen=True)
class FreezeInventory:
    """Sorted map of relative POSIX path to SHA-256, plus its own digest."""

    files: dict[str, str]
    tree_digest: str

    def as_document(self) -> dict[str, object]:
        return {
            "schema": "epd2.infra01.freeze-inventory/1",
            "file_count": len(self.files),
            "files": dict(sorted(self.files.items())),
            "tree_digest": self.tree_digest,
        }


def compute_tree_digest(files: dict[str, str]) -> str:
    """``sha256`` over ``path \\0 sha256(path) \\n`` in sorted path order.

    The same recomputable convention used by prior governed rounds: anyone
    with the file set can derive the digest without trusting the harness.
    """
    payload = b"".join(
        path.encode("utf-8") + b"\0" + digest.encode("ascii") + b"\n"
        for path, digest in sorted(files.items())
    )
    return sha256_bytes(payload)


def _git_lines(root: Path, *args: str) -> list[str]:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        timeout=300,
        check=True,
    )
    return (
        [line for line in completed.stdout.split("\0") if line]
        if "-z" in args
        else [line for line in completed.stdout.splitlines() if line.strip()]
    )


def tracked_files(root: Path) -> list[str]:
    return sorted(_git_lines(root, "ls-files", "-z"))


def freeze_problems(root: Path) -> list[HygieneFinding]:
    """Fail-closed preconditions for taking a freeze inventory."""
    findings: list[HygieneFinding] = []
    status = _git_lines(root, "status", "--porcelain", "-z")
    for entry in status:
        state, _, rel = entry.partition(" ")
        rel = rel.strip().lstrip(" ")
        if not rel:
            continue
        first_part = PurePosixPath(rel).parts[0] if PurePosixPath(rel).parts else rel
        if state.strip() == "??":
            if first_part in GENERATED_LOCATION_NAMES:
                continue
            if any(part in GENERATED_LOCATION_NAMES for part in PurePosixPath(rel).parts):
                continue
            findings.append(
                HygieneFinding(
                    codes.TREE_MUTATION_AFTER_FREEZE,
                    rel,
                    "untracked file outside generated locations; tested tree != committed tree",
                )
            )
        else:
            findings.append(
                HygieneFinding(
                    codes.TREE_MUTATION_AFTER_FREEZE,
                    rel,
                    f"tracked path diverges from commit (git status {state.strip()!r})",
                )
            )
    for rel in tracked_files(root):
        parts = PurePosixPath(rel).parts
        if any(part in FORBIDDEN_DIRECTORY_NAMES for part in parts[:-1]):
            findings.append(
                HygieneFinding(codes.FORBIDDEN_PATH, rel, "tracked file inside forbidden directory")
            )
    return findings


def take_inventory(root: Path) -> FreezeInventory:
    """Hash every tracked file. Caller must have handled freeze_problems()."""
    files: dict[str, str] = {}
    for rel in tracked_files(root):
        files[rel] = sha256_file(root / rel)
    return FreezeInventory(files=files, tree_digest=compute_tree_digest(files))


def diff_inventories(before: FreezeInventory, after: FreezeInventory) -> list[HygieneFinding]:
    """Detect any silent change between two inventories of the same tree."""
    findings: list[HygieneFinding] = []
    for path in sorted(set(before.files) | set(after.files)):
        old = before.files.get(path)
        new = after.files.get(path)
        if old is None:
            findings.append(
                HygieneFinding(codes.TREE_MUTATION_AFTER_FREEZE, path, "file appeared after freeze")
            )
        elif new is None:
            findings.append(
                HygieneFinding(
                    codes.TREE_MUTATION_AFTER_FREEZE, path, "file disappeared after freeze"
                )
            )
        elif old != new:
            findings.append(
                HygieneFinding(
                    codes.TREE_MUTATION_AFTER_FREEZE,
                    path,
                    f"content changed after freeze: {old} -> {new}",
                )
            )
    return findings
