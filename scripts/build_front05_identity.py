#!/usr/bin/env python3
"""FRONT-05 identity, lineage and delta records.

Three questions a reviewer asks first, answered mechanically rather than in
prose: what exactly is this package, what accepted bytes did it come from, and
what changed since those bytes.

The delta is computed against the accepted FRONT-04 C2 source tree by comparing
per-file digests, so "added, changed, removed" is a measurement rather than a
recollection. That matters more than it sounds: the FRONT-04 C1 review found a
claimed inventory that was simply absent, and prose inventories are exactly the
artifact that drifts.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import front04_digest as front04
import front05_digest as digest

STAGE = "FRONT-05 — WS-04 Representative Workspace"
CANDIDATE_STATE = "CANDIDATE_NOT_ACCEPTED"

FRONT04_C2 = {
    "filename": "EPD2_FRONT04_WS03_VOTING_CLIENT_CANDIDATE_0.1_C2.zip",
    "sha256": "1ac87914a30e589b4059e3b7c74e0a0fd940a78cecbe7f06de299421c8da55f8",
    "size_bytes": 21448756,
    "source_tree_digest": "eee6bf1e80f9e5b5ce18618611513b871b195a163e98948d55d99f61276f2f2e",
    "authoritative_run": 33569268417,
    "authoritative_job": 100059427183,
    "reviewed_commit": "66a65f2303d2a0d18fb8396887a35d6c14df1d92",
    "decision": "ACCEPTED",
}


def now() -> str:
    return dt.datetime.now(dt.UTC).isoformat()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--baseline", help="path to a baseline source_manifest.json")
    parser.add_argument(
        "--entering-main",
        default="8db1b85056aad3099fa27e12b29ab9f0a00c4a5b",
    )
    args = parser.parse_args()
    root = Path(args.root).resolve()
    out = root / "validation" / "front05"
    out.mkdir(parents=True, exist_ok=True)

    current = digest.compute(root)
    files = current["files"]

    identity = {
        "schema": "epd2.front05.preseal-identity/1",
        "stage": STAGE,
        "candidate_state": CANDIDATE_STATE,
        "self_acceptance": False,
        "highest_self_assertion": "PASS_FOR_INDEPENDENT_ACCEPTANCE",
        "canonically_opened_stage": True,
        "generated_at": now(),
        "source_tree_digest": current["source_tree_digest"],
        "test_source_digest": current["test_source_digest"],
        "configuration_digest": current["config_digest"],
        "validator_source_digest": current["validator_source_digest"],
        "contract_digest": current["contract_digest"],
        "package_lock_sha256": current["package_lock_sha256"],
        "source_file_count": current["file_count"],
        "include_roots": current["include_roots"],
        "exclusion_audit_problems": current["exclusion_audit_problems"],
    }
    (out / "preseal_identity.json").write_text(
        json.dumps(identity, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    lineage = {
        "schema": "epd2.front05.lineage/1",
        "stage": STAGE,
        "candidate_state": CANDIDATE_STATE,
        "generated_at": now(),
        "entering_canonical_main": args.entering_main,
        "accepted_predecessors": {
            "FRONT-04 C2": FRONT04_C2,
            "FRONT-03 C1": {
                "sha256": "fec7b19d77c27cbc3ef8a34e433f5aef94ef7853f76d3212bed6acd682497c26",
                "authoritative_run": 33528038712,
                "authoritative_job": 99923795567,
                "decision": "ACCEPTED",
            },
            "FRONT-02 C2.1": {
                "sha256": "aaf980a2cd3b3b06d48218adaa68d109c8770e6abfcbef230197b51a87006179",
                "decision": "ACCEPTED_IMPLEMENTATION_BASELINE",
            },
        },
        "predecessor_programme_state": {
            "ARCH": "CLOSED",
            "DATA": "CLOSED",
            "API": "API-01..06 ACCEPTED / CLOSED; API LAYER CLOSED",
            "INFRA": "INFRA-01/02 ACCEPTED / CLOSED; LAYER OPEN",
            "OPS": "OPS-01/02 ACCEPTED / CLOSED; LAYER OPEN",
            "CTRL": "CTRL-01 ACCEPTED / CLOSED; LAYER OPEN",
        },
        "note": (
            "This package inherits the accepted FRONT-04 C2 bytes unchanged and adds "
            "the WS-04 workspace beside them. The bounded C1 acceptance attempt is "
            "opened by project-owner directive but remains NOT_ACCEPTED until independent review."
        ),
    }
    (out / "lineage.json").write_text(
        json.dumps(lineage, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    baseline_files: dict[str, str] = {}
    baseline_source = args.baseline
    if baseline_source and Path(baseline_source).is_file():
        baseline_files = json.loads(Path(baseline_source).read_text())["files"]

    added = sorted(p for p in files if p not in baseline_files)
    removed = sorted(p for p in baseline_files if p not in files)
    changed = sorted(
        p for p in files if p in baseline_files and files[p] != baseline_files[p]
    )

    # The FRONT-05 digest boundary covers the new workspace and its tooling, so
    # every file in it is new by construction. That would make an "added: 113"
    # delta look impressive and say nothing. The measurement that carries
    # information is the other one: did adding this workspace disturb the
    # accepted FRONT-04 C2 bytes it sits beside?
    #
    # Two files legitimately change and exactly two: the root `package.json`
    # gains the new workspace entry and `package-lock.json` records its
    # dependency resolution. Registering a workspace *is* editing those files;
    # there is no way to add one without them. So they are called out by name
    # with that reason, and the assertion is made over the FRONT-04
    # implementation itself, which must be identical to the byte.
    SHARED_ROOT_FILES = ("package.json", "package-lock.json")
    inherited = front04.compute(root)
    baseline_manifest = root / "validation/front04/source_manifest.json"
    accepted_files: dict[str, str] = {}
    if baseline_manifest.is_file():
        accepted_files = json.loads(baseline_manifest.read_text())["files"]

    def implementation_only(entries: dict[str, str]) -> dict[str, str]:
        return {k: v for k, v in entries.items() if k not in SHARED_ROOT_FILES}

    measured_impl = front04.digest_of(implementation_only(inherited["files"]))
    accepted_impl = (
        front04.digest_of(implementation_only(accepted_files)) if accepted_files else ""
    )
    disturbed = sorted(
        path
        for path in set(inherited["files"]) | set(accepted_files)
        if inherited["files"].get(path) != accepted_files.get(path)
        and path not in SHARED_ROOT_FILES
    )
    inherited_unchanged = bool(accepted_impl) and measured_impl == accepted_impl

    delta = {
        "schema": "epd2.front05.source-delta/1",
        "inherited_front04_c2": {
            "accepted_candidate_sha256": FRONT04_C2["sha256"],
            "accepted_source_tree_digest": FRONT04_C2["source_tree_digest"],
            "measured_source_tree_digest": inherited["source_tree_digest"],
            "measured_with": "scripts/front04_digest.py, over the FRONT-04 include roots",
            "file_count": inherited["file_count"],
            "implementation_digest_accepted": accepted_impl,
            "implementation_digest_measured": measured_impl,
            "implementation_unchanged": inherited_unchanged,
            "files_disturbed_outside_the_shared_root": disturbed,
            "shared_root_files_changed": list(SHARED_ROOT_FILES),
            "shared_root_change_reason": (
                "the root package.json gains the representative-workspace entry and "
                "package-lock.json records its dependency resolution. Registering a "
                "workspace is editing those two files; the FRONT-04 implementation "
                "itself is byte-identical."
            ),
        },
        "stage": STAGE,
        "candidate_state": CANDIDATE_STATE,
        "generated_at": now(),
        "baseline": "supplied manifest"
        if baseline_files
        else "none supplied — every file in the FRONT-05 digest boundary is new, "
        "because that boundary covers only the new workspace and its tooling",
        "baseline_manifest": baseline_source or None,
        "counts": {
            "added": len(added),
            "changed": len(changed),
            "removed": len(removed),
            "current_total": len(files),
        },
        "added": added,
        "changed": changed,
        "removed": removed,
    }
    (out / "source_delta.json").write_text(
        json.dumps(delta, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    print(f"source_tree_digest = {current['source_tree_digest']}")
    print(f"files = {current['file_count']}")
    print(f"delta: +{len(added)} ~{len(changed)} -{len(removed)}")
    print(f"inherited FRONT-04 implementation unchanged: {inherited_unchanged}")
    if disturbed:
        print("  disturbed:", disturbed)
    if not inherited_unchanged:
        print(f"  accepted implementation digest {accepted_impl}")
        print(f"  measured implementation digest {measured_impl}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
