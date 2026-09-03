"""INFRA-03 packaging phase: G39/G40 and the detached preseal record
(assignment §62..§66).

Runs after the canonical acceptance harness has produced the working
archive. Independently re-proves, against the final bytes:

- G39 archive hygiene (structure, duplicates, unsafe paths, nested
  archives, forbidden content, secrets) using the same canonical scanners;
- G40 same-bytes identity: every archive member equals the frozen
  inventory byte-for-byte, and the tree that was tested is byte-identical
  to the tree that was packaged (:func:`evaluators.check_post_test_bytes`);

then emits the only permitted marker::

    INFRA03_PRESEAL_RESULT:PASS:<candidate_sha256>:<size>

never an ``AUTHORITATIVE_RESULT``, plus the detached final preseal record
and ``.sha256`` sidecar. Any failure yields a non-zero exit and no marker.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path

from scripts.acceptance.canonical import load_json, seal_document, sha256_file
from scripts.acceptance.freeze import FreezeInventory, take_inventory
from scripts.acceptance.hygiene import scan_archive as hygiene_scan_archive
from scripts.acceptance.package import verify_archive_against_inventory
from scripts.acceptance.secrets_scan import scan_archive as secrets_scan_archive
from scripts.infra03 import evaluators

CANDIDATE_NAME = "EPD2_INFRA03_DEPLOYMENT_RUNTIME_AND_PREVIEW_READINESS_CANDIDATE_0.1_C1"


def run_package_phase(root: Path, run_dir: Path, out_dir: Path) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    archive = run_dir / f"{CANDIDATE_NAME}.zip"
    if not archive.is_file():
        print(f"PRESEAL_FAIL: candidate archive absent: {archive}", file=sys.stderr)
        return 1
    sha256 = sha256_file(archive)
    size = archive.stat().st_size

    manifest = load_json(run_dir / "EXECUTION-MANIFEST.json")
    findings: list[str] = []
    if manifest.get("verdict") != "PASS":
        findings.append(f"harness verdict is {manifest.get('verdict')!r}, not PASS")
    if manifest.get("final_archive_sha256") != sha256:
        findings.append("archive bytes differ from the harness-attested digest")

    inventory_doc = load_json(run_dir / "FREEZE-INVENTORY.json")
    inventory = FreezeInventory(
        files=dict(inventory_doc["files"]), tree_digest=str(inventory_doc["tree_digest"])
    )

    # G39 — independent archive hygiene + secret re-scan
    hygiene_findings = [f"{f.code}: {f.path}: {f.detail}" for f in hygiene_scan_archive(archive)]
    secret_findings = [hit.describe() for hit in secrets_scan_archive(archive)]
    g39_findings = hygiene_findings + secret_findings

    # G40 — same-bytes identity: archive members == frozen inventory, and the
    # tree that was tested is byte-identical to the tree packaged.
    byte_findings = [
        f"{f.code}: {f.path}: {f.detail}"
        for f in verify_archive_against_inventory(archive, CANDIDATE_NAME, inventory)
    ]
    current = take_inventory(root)
    byte_findings.extend(
        evaluators.check_post_test_bytes(inventory.tree_digest, current.tree_digest)
    )

    now = datetime.now(tz=UTC).isoformat(timespec="seconds")
    runtime_summary = load_json(root / "validation/infra03/infra03_preseal_result.json")
    record = seal_document(
        {
            "schema": "epd2.infra03.preseal-final/1",
            "generated_at": now,
            "candidate": {
                "filename": archive.name,
                "sha256": sha256,
                "size_bytes": size,
                "freeze_tree_digest": inventory.tree_digest,
                "member_count": len(inventory.files) + 2,
            },
            "gates_runtime_phase": runtime_summary.get("gates"),
            "gates_package_phase": [
                {
                    "gate": "G39",
                    "title": "archive hygiene",
                    "state": "PASS" if not g39_findings else "FAIL",
                    "findings": g39_findings,
                },
                {
                    "gate": "G40",
                    "title": "same-bytes identity",
                    "state": "PASS" if not byte_findings else "FAIL",
                    "findings": byte_findings,
                },
            ],
            "harness": {
                "verdict": manifest.get("verdict"),
                "registry_version": manifest.get("registry", {}).get("registry_version"),
                "git_commit": manifest.get("identity", {}).get("git_commit"),
                "git_tree": manifest.get("identity", {}).get("git_tree"),
            },
            "self_state": [
                "IMPLEMENTATION_COMPLETE",
                "LOCAL_VERIFICATION_PASS",
                "PRESEAL_READY"
                if not (findings + g39_findings + byte_findings)
                else "PRESEAL_FAIL",
                "NOT_ACCEPTED",
            ],
            "final_seal_blockers": runtime_summary.get("final_seal_blockers"),
            "consistency_findings": findings,
        }
    )
    (out_dir / "INFRA03_PRESEAL_FINAL.json").write_text(
        json.dumps(record, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )

    total = findings + g39_findings + byte_findings
    if total:
        for finding in total:
            print(f"PRESEAL_FINDING: {finding}", file=sys.stderr)
        print("INFRA03_PRESEAL_RESULT:FAIL", file=sys.stderr)
        return 1

    shutil.copyfile(archive, out_dir / archive.name)
    (out_dir / f"{archive.name}.sha256").write_text(f"{sha256}  {archive.name}\n", encoding="utf-8")
    print(f"G39 archive hygiene: PASS ({len(inventory.files) + 2} members)")
    print(f"G40 same-bytes identity: PASS (tree {inventory.tree_digest[:16]}...)")
    print(f"INFRA03_PRESEAL_RESULT:PASS:{sha256}:{size}")
    print("NOT_ACCEPTED. PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED. Never an AUTHORITATIVE_RESULT.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="scripts.infra03.preseal")
    parser.add_argument("--root", default=".")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    return run_package_phase(
        Path(args.root).resolve(), Path(args.run_dir).resolve(), Path(args.out).resolve()
    )


if __name__ == "__main__":
    sys.exit(main())
