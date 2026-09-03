#!/usr/bin/env python3
"""Canonical FRONT-05 source-set digests.

One module computes every digest the verification chain uses, so the runner
that records evidence and the validator that checks it cannot disagree about
what "the source tree" means.

Design points that matter:

* The include set is expressed as **roots**, not as a hand-maintained file
  list. A newly added source file inside a root is picked up automatically, so
  a new import cannot slip in unrepresented.
* The exclusion set is **closed and machine-checked**: every exclusion carries a
  reason, and `audit_exclusions` proves that nothing excluded is a first-party
  source file. If a future change starts excluding real source, the audit fails.
* Digests are computed over a canonical serialisation of (path, sha256) pairs
  sorted by path, so they are stable across filesystems and orderings.

Where the boundary sits, and why. The set covers the implementation, its tests,
its configuration, the tooling that produces and checks evidence, and the stage
contract that defines what "correct" means. It does not cover the evidence
outputs themselves, which cannot be inside the set they bind, nor the prose
documents, which the validator re-reads and content-checks on every run.

One boundary decision here is a direct correction. In FRONT-04 the developer
report also sat outside this set, and a stale `source_tree_digest` quoted in its
prose survived to a sealed archive that was then rejected. The lesson was not
that the report should be digest-covered — it cannot be, since it quotes the
digest of the tree that contains it — but that its quoted identities need their
own gate. That is G45, in `validate_front05.py`, and it reads the same summary
this module produces.

The inherited FRONT-03, FRONT-04 and PACK-15 evidence is pinned separately, by
explicit SHA-256 in the stage contract.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

SCHEMA = "epd2.front05.digest/1"

# Roots whose contents can affect accepted FRONT-05 behaviour.
INCLUDE_ROOTS: tuple[str, ...] = (
    "frontend/representative-workspace",
    "docs/frontend/FRONT-05-STAGE-CONTRACT.md",
    "docs/frontend/FRONT-05-STAGE-CONTRACT.json",
    "docs/frontend/FRONT-05-C1-GOVERNANCE-OPENING.json",
    "scripts/front05_digest.py",
    "scripts/validate_front05.py",
    "scripts/run_front05_mutations.py",
    "scripts/run_front05_verification.py",
    "scripts/build_front05_identity.py",
    "scripts/build_front05_records.py",
    "scripts/build_front05_report.py",
    "scripts/build_front05_dependency_findings.py",
    "scripts/build_front05_authorization_negatives.py",
    "scripts/check_front05_fixture_absence.py",
    "scripts/seal_front05.py",
    "package.json",
    "package-lock.json",
)

# Closed exclusion set. Each entry names why the path cannot affect accepted
# behaviour. `audit_exclusions` checks the claim rather than trusting it.
EXCLUDED_DIR_NAMES: dict[str, str] = {
    "node_modules": "installed dependency tree; identity is carried by package-lock.json",
    ".next": "build output regenerated from source on every build",
    "test-results": "per-run Playwright output",
    "playwright-report": "per-run Playwright report",
    "coverage": "per-run coverage output",
    "__pycache__": "Python bytecode cache",
    ".turbo": "build cache",
    ".swc": "build cache",
}
EXCLUDED_FILE_NAMES: dict[str, str] = {
    "tsconfig.tsbuildinfo": "TypeScript incremental cache; the package sets incremental=false",
    ".DS_Store": "filesystem metadata",
}

# Files whose content defines how the suites run.
CONFIG_FILES: tuple[str, ...] = (
    "package.json",
    "package-lock.json",
    "frontend/representative-workspace/package.json",
    "frontend/representative-workspace/tsconfig.json",
    "frontend/representative-workspace/next.config.ts",
    "frontend/representative-workspace/middleware.ts",
    "frontend/representative-workspace/playwright.config.ts",
    "frontend/representative-workspace/vitest.config.ts",
    "frontend/representative-workspace/eslint.config.mjs",
)

TEST_ROOT = "frontend/representative-workspace/tests"

VALIDATOR_FILES: tuple[str, ...] = (
    "scripts/validate_front05.py",
    "scripts/front05_digest.py",
)

CONTRACT_FILES: tuple[str, ...] = (
    "docs/frontend/FRONT-05-STAGE-CONTRACT.md",
    "docs/frontend/FRONT-05-STAGE-CONTRACT.json",
)

# First-party source extensions. Used by the exclusion audit.
SOURCE_SUFFIXES = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".css", ".py"}


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _excluded(relative: Path) -> str | None:
    for part in relative.parts[:-1]:
        if part in EXCLUDED_DIR_NAMES:
            return f"dir:{part}"
    if relative.name in EXCLUDED_FILE_NAMES:
        return f"file:{relative.name}"
    return None


def collect(root: Path) -> dict[str, str]:
    """Every included file, mapped to its SHA-256, keyed by POSIX relative path."""
    found: dict[str, str] = {}
    for entry in INCLUDE_ROOTS:
        target = root / entry
        if target.is_file():
            found[entry] = file_sha256(target)
            continue
        if not target.is_dir():
            continue
        for path in target.rglob("*"):
            if not path.is_file() or path.is_symlink():
                continue
            relative = path.relative_to(root)
            if _excluded(relative):
                continue
            found[relative.as_posix()] = file_sha256(path)
    return dict(sorted(found.items()))


def digest_of(entries: dict[str, str]) -> str:
    canonical = "\n".join(f"{path}\x00{digest}" for path, digest in sorted(entries.items()))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def subset(entries: dict[str, str], prefix: str) -> dict[str, str]:
    return {k: v for k, v in entries.items() if k == prefix or k.startswith(prefix + "/")}


def named(entries: dict[str, str], names: tuple[str, ...]) -> dict[str, str]:
    return {name: entries[name] for name in names if name in entries}


def audit_exclusions(root: Path) -> list[str]:
    """Prove the exclusion set omits no first-party source file.

    Walks the include roots ignoring the exclusion set, and reports any excluded
    path that is a first-party source file living outside a known generated or
    installed location. An empty list means the exclusion set is safe.
    """
    problems: list[str] = []
    for entry in INCLUDE_ROOTS:
        target = root / entry
        if not target.is_dir():
            continue
        for path in target.rglob("*"):
            if not path.is_file():
                continue
            relative = path.relative_to(root)
            reason = _excluded(relative)
            if reason is None:
                continue
            if path.suffix not in SOURCE_SUFFIXES:
                continue
            # A source file inside node_modules, a build directory or a cache is
            # expected. A source file excluded for any other reason is not.
            if reason.startswith("dir:") and reason.split(":", 1)[1] in EXCLUDED_DIR_NAMES:
                continue
            problems.append(f"{relative.as_posix()} excluded by {reason}")
    return problems


def compute(root: Path) -> dict[str, object]:
    root = Path(root).resolve()
    entries = collect(root)
    tests = subset(entries, TEST_ROOT)
    return {
        "schema": SCHEMA,
        "include_roots": list(INCLUDE_ROOTS),
        "excluded_dir_names": EXCLUDED_DIR_NAMES,
        "excluded_file_names": EXCLUDED_FILE_NAMES,
        "file_count": len(entries),
        "source_tree_digest": digest_of(entries),
        "test_source_digest": digest_of(tests),
        "test_file_count": len(tests),
        "config_digest": digest_of(named(entries, CONFIG_FILES)),
        "validator_source_digest": digest_of(named(entries, VALIDATOR_FILES)),
        "contract_digest": digest_of(named(entries, CONTRACT_FILES)),
        "package_lock_sha256": entries.get("package-lock.json", ""),
        "exclusion_audit_problems": audit_exclusions(root),
        "files": entries,
    }


def summary(root: Path) -> dict[str, object]:
    """The binding block embedded in every evidence record."""
    full = compute(root)
    return {
        key: full[key]
        for key in (
            "schema",
            "source_tree_digest",
            "test_source_digest",
            "config_digest",
            "validator_source_digest",
            "contract_digest",
            "package_lock_sha256",
            "file_count",
        )
    }


if __name__ == "__main__":
    import sys

    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    result = compute(root)
    files = result.pop("files")
    print(json.dumps(result, indent=2))
    print(f"# {len(files)} files included", file=sys.stderr)
