"""Exact candidate identity binding (INFRA01-HI-01).

Every acceptance execution binds itself to the exact Git commit, source-tree
identity, repository and canon versions, dependency-lock digests, harness
version and — where a candidate archive is supplied — the archive's SHA-256.
Acceptance evidence without exact candidate identity is invalid, so identity
capture fails closed: a value that cannot be determined is recorded as an
explicit problem, never silently omitted or guessed.
"""

from __future__ import annotations

import platform
import subprocess
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.acceptance import HARNESS_NAME, HARNESS_VERSION
from scripts.acceptance.canonical import sha256_file
from scripts.verify_versions import collect_versions, find_mismatches

LOCK_FILES = ("uv.lock", "package-lock.json")


@dataclass
class CandidateIdentity:
    """The complete identity block of one acceptance execution."""

    run_id: str
    started_at: str
    git_commit: str
    git_tree: str
    git_dirty: bool
    dirty_paths: list[str]
    repository_version: str
    canon_version: str
    versions: dict[str, str]
    lock_hashes: dict[str, str]
    platform: str
    python_version: str
    harness_name: str = HARNESS_NAME
    harness_version: str = HARNESS_VERSION
    workflow: dict[str, str] = field(default_factory=dict)
    candidate_archive_sha256: str | None = None
    problems: list[str] = field(default_factory=list)

    def as_document(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "started_at": self.started_at,
            "git_commit": self.git_commit,
            "git_tree": self.git_tree,
            "git_dirty": self.git_dirty,
            "dirty_paths": sorted(self.dirty_paths),
            "repository_version": self.repository_version,
            "canon_version": self.canon_version,
            "versions": dict(sorted(self.versions.items())),
            "lock_hashes": dict(sorted(self.lock_hashes.items())),
            "platform": self.platform,
            "python_version": self.python_version,
            "harness_name": self.harness_name,
            "harness_version": self.harness_version,
            "workflow": dict(sorted(self.workflow.items())),
            "candidate_archive_sha256": self.candidate_archive_sha256,
            "problems": sorted(self.problems),
        }


def _git(root: Path, *args: str) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout.strip()


def utc_now() -> str:
    return datetime.now(tz=UTC).isoformat(timespec="seconds")


def collect_identity(
    root: Path,
    environ: dict[str, str],
    candidate_archive: Path | None = None,
) -> CandidateIdentity:
    """Collect the identity of the tree at ``root``; never guess a value."""
    problems: list[str] = []

    commit = _git(root, "rev-parse", "HEAD")
    tree = _git(root, "rev-parse", "HEAD^{tree}")
    status = _git(root, "status", "--porcelain")
    if commit is None or tree is None or status is None:
        problems.append("git identity unavailable: not a Git checkout or git failed")
        commit = commit or "UNKNOWN"
        tree = tree or "UNKNOWN"
    dirty_paths = [line[3:] for line in (status or "").splitlines() if line.strip()]

    try:
        versions = collect_versions(root)
        for mismatch in find_mismatches(root):
            problems.append(f"version mismatch: {mismatch}")
    except (OSError, KeyError, ValueError) as error:
        versions = {}
        problems.append(f"version sources unreadable: {error}")

    lock_hashes: dict[str, str] = {}
    for name in LOCK_FILES:
        lock = root / name
        if lock.is_file():
            lock_hashes[name] = sha256_file(lock)
        else:
            problems.append(f"dependency lock file missing: {name}")

    workflow = {
        key.lower(): environ[key]
        for key in (
            "GITHUB_RUN_ID",
            "GITHUB_RUN_ATTEMPT",
            "GITHUB_WORKFLOW",
            "GITHUB_WORKFLOW_REF",
            "GITHUB_SHA",
            "GITHUB_REPOSITORY",
        )
        if environ.get(key)
    }

    archive_sha = None
    if candidate_archive is not None:
        if candidate_archive.is_file():
            archive_sha = sha256_file(candidate_archive)
        else:
            problems.append(f"candidate archive not found: {candidate_archive}")

    return CandidateIdentity(
        run_id=uuid.uuid4().hex,
        started_at=utc_now(),
        git_commit=commit,
        git_tree=tree,
        git_dirty=bool(dirty_paths),
        dirty_paths=dirty_paths,
        repository_version=versions.get("python.REPOSITORY_VERSION", "UNKNOWN"),
        canon_version=versions.get("python.CANON_VERSION", "UNKNOWN"),
        versions=versions,
        lock_hashes=lock_hashes,
        platform=platform.platform(),
        python_version=platform.python_version(),
        workflow=workflow,
        candidate_archive_sha256=archive_sha,
        problems=problems,
    )


def lock_mismatches(root: Path, recorded: dict[str, str]) -> list[str]:
    """Compare current dependency-lock digests to the recorded ones.

    A successful run whose lock files changed underneath it was not a
    frozen-dependency run; the mismatch is a fail-closed defect
    (:data:`scripts.acceptance.codes.LOCK_HASH_MISMATCH`).
    """
    from scripts.acceptance import codes

    findings: list[str] = []
    for name, expected in sorted(recorded.items()):
        target = root / name
        if not target.is_file():
            findings.append(f"{codes.LOCK_HASH_MISMATCH}: {name}: lock file disappeared")
            continue
        actual = sha256_file(target)
        if actual != expected:
            findings.append(
                f"{codes.LOCK_HASH_MISMATCH}: {name}: recorded {expected}, current {actual}"
            )
    return findings


def tool_inventory(root: Path) -> dict[str, str]:
    """Versions of the tools the canonical run depends on.

    A tool that cannot report its version is recorded as ``UNAVAILABLE`` —
    the executor turns that into BLOCKED for every check that needs it.
    """
    inventory: dict[str, str] = {}
    for name, command in (
        ("git", ["git", "--version"]),
        ("uv", ["uv", "--version"]),
        ("python", ["python3", "--version"]),
        ("node", ["node", "--version"]),
        ("npm", ["npm", "--version"]),
        ("make", ["make", "--version"]),
    ):
        try:
            completed = subprocess.run(
                command, capture_output=True, text=True, timeout=60, check=False, cwd=root
            )
            first_line = (completed.stdout or completed.stderr).splitlines()
            inventory[name] = first_line[0].strip() if first_line else "UNAVAILABLE"
            if completed.returncode != 0:
                inventory[name] = "UNAVAILABLE"
        except (OSError, subprocess.TimeoutExpired):
            inventory[name] = "UNAVAILABLE"
    return inventory
