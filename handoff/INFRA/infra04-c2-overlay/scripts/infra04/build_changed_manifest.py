"""Regenerate INFRA-04 changed-file lineage from exact current bytes.

This runs after runtime evidence generation and before freeze/package. It compares the
candidate worktree to origin/main, excludes governed packaging additions and this
self-describing manifest, and fails if a listed path is absent. No stale C1 inventory
is trusted.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/infra/INFRA-04/INFRA04_CHANGED_FILE_MANIFEST.json"
PACKAGING = {"SHA256SUMS.txt", "ACCEPTANCE/FREEZE-INVENTORY.json"}
SELF = OUT.relative_to(ROOT).as_posix()
PRETTIER_RECONCILED = "frontend/web-shell/tests/browser/front03.visual.capture.spec.ts"


def git(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args], capture_output=True, text=True, check=True, timeout=300
    ).stdout.strip()


def exists_at(ref: str, path: str) -> bool:
    return (
        subprocess.run(
            ["git", "-C", str(ROOT), "cat-file", "-e", f"{ref}:{path}"], capture_output=True
        ).returncode
        == 0
    )


def classify(path: str, old: dict[str, str]) -> str:
    if path == ".github/workflows/infra04-c2-authoritative.yml":
        return "INFRA-04 governed acceptance runner"
    if path == "docs/infra/INFRA-01/INFRA01_GOVERNANCE_RECONCILIATION.json":
        return "INFRA-04 governance freshness binding"
    if path == "scripts/acceptance/__main__.py":
        return "INFRA-04 acceptance-harness package identity binding"
    if path.startswith("tests/repository/test_infra04_"):
        return "INFRA-04 targeted tests"
    if path == "infra/runtime/resilience_policy.json":
        return "INFRA-04 governed policy"
    if path.startswith(("docs/infra/INFRA-04/", "scripts/infra04/", "validation/infra04/")):
        return "INFRA-04 stage implementation"
    return old.get(path, "inherited baseline: explicitly reviewed delta")


def main() -> int:
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/infra04/reconcile_inherited_acceptance_baseline.py"),
            "--root",
            str(ROOT),
        ],
        check=True,
        timeout=300,
    )

    prettier = ROOT / "node_modules/.bin/prettier"
    prettier_target = ROOT / PRETTIER_RECONCILED
    if not prettier.is_file():
        raise SystemExit(f"locked prettier executable is missing: {prettier}")
    if not prettier_target.is_file():
        raise SystemExit(f"reconciled prettier target is missing: {PRETTIER_RECONCILED}")
    subprocess.run(
        [str(prettier), "--write", PRETTIER_RECONCILED],
        cwd=ROOT,
        check=True,
        timeout=300,
    )
    subprocess.run(
        [str(prettier), "--check", PRETTIER_RECONCILED],
        cwd=ROOT,
        check=True,
        timeout=300,
    )
    print("INFRA04_C2_POST_RECONCILIATION_PRETTIER:PASS:1")

    subprocess.run(
        ["git", "-C", str(ROOT), "fetch", "--no-tags", "origin", "main"], check=True, timeout=300
    )
    base = "origin/main"
    commit = git("rev-parse", base)
    tree = git("rev-parse", base + "^{tree}")
    olddoc = json.loads(OUT.read_text()) if OUT.is_file() else {"files": []}
    old = {
        e["path"]: e.get("class", "")
        for e in olddoc.get("files", [])
        if isinstance(e, dict) and e.get("path")
    }
    tracked = set(git("ls-files").splitlines())
    untracked = set(filter(None, git("ls-files", "--others", "--exclude-standard").splitlines()))
    candidates = sorted((tracked | untracked) - PACKAGING - {SELF})
    entries = []
    for path in candidates:
        p = ROOT / path
        base_has = exists_at(base, path)
        if not p.is_file():
            if base_has:
                entries.append(
                    {
                        "path": path,
                        "change": "deleted",
                        "class": old.get(path, "inherited baseline: explicitly reviewed delta"),
                        "sha256": None,
                    }
                )
            continue
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        if base_has:
            base_digest = hashlib.sha256(
                subprocess.run(
                    ["git", "-C", str(ROOT), "show", f"{base}:{path}"],
                    capture_output=True,
                    check=True,
                    timeout=120,
                ).stdout
            ).hexdigest()
            if base_digest == digest:
                continue
            change = "modified"
        else:
            change = "added"
        entries.append(
            {"path": path, "change": change, "class": classify(path, old), "sha256": digest}
        )
    counts = Counter(e["class"] for e in entries)
    doc = {
        "schema": "epd2.infra04.changed-file-manifest/2",
        "stage": "INFRA-04",
        "self_state": "PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED",
        "candidate_state": "CANDIDATE_NOT_ACCEPTED",
        "self_acceptance": False,
        "canonical_base": {
            "repository": "nepogoda1970-epd2/epd2-civic-os",
            "branch": "main",
            "commit": commit,
            "tree": tree,
        },
        "note": (
            "Exact current-byte install delta against canonical main after runtime evidence "
            "generation. This self-describing manifest and governed package additions "
            "SHA256SUMS.txt / ACCEPTANCE/FREEZE-INVENTORY.json are intentionally excluded "
            "from the recursive file list."
        ),
        "counts_by_class": dict(sorted(counts.items())),
        "files": entries,
        "total_files": len(entries),
    }
    OUT.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    subprocess.run(
        [str(prettier), "--write", SELF],
        cwd=ROOT,
        check=True,
        timeout=300,
    )
    subprocess.run(
        [str(prettier), "--check", SELF],
        cwd=ROOT,
        check=True,
        timeout=300,
    )
    print("INFRA04_C2_CHANGED_MANIFEST_PRETTIER:PASS:1")

    # Mechanical self-check: every non-deleted entry exists and matches.
    for e in entries:
        if e["change"] == "deleted":
            continue
        p = ROOT / e["path"]
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != e["sha256"]:
            raise SystemExit(f"manifest byte mismatch: {e['path']}")
    print(f"INFRA04_CHANGED_MANIFEST:PASS:{len(entries)}:{commit}:{tree}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
