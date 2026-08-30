#!/usr/bin/env python3
"""Fail-closed guard for the locked EPD² PILOT roadmap.

Usage:
  python scripts/check_pilot_roadmap.py --self-check
  python scripts/check_pilot_roadmap.py --zip path/to/PILOT-candidate.zip

Starting with PILOT-03, candidate archives must contain
`docs/roadmap/PILOT_STAGE_SCOPE.json` under the single candidate root.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path, PurePosixPath

REPO_ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = REPO_ROOT / "docs" / "roadmap" / "EPD2_PILOT_ROADMAP_LOCK.json"

FROZEN_STAGES = {
    "PILOT-01": "Internal Organization Pilot",
    "PILOT-02": "Membership & Participation Pilot",
    "PILOT-03": "Assemblies / Motions / Communications Pilot",
    "PILOT-04": "Non-binding Digital Vote Pilot",
    "PILOT-05": "Representative Desk / Transparency Pilot",
    "PILOT-06": "Pilot Findings & Corrections",
    "PILOT-07": "Production Readiness Decision",
}

PILOT03_REQUIRED_CAPABILITIES = {
    "assemblies",
    "motions",
    "communications",
    "member_frontend_integration",
}

PILOT02_C4_FILENAME = (
    "EPD2_PILOT02_PUBLIC_SITE_INTEGRATION_AND_UNIFIED_PILOT_PRODUCT_CANDIDATE_0.51.2_C4.zip"
)
PILOT02_C4_SHA256 = "261ab0996659f453d3d6d3cf43e12ad105fa6dbacd5035de40ca949029cbfc3e"
SCOPE_MANIFEST = "docs/roadmap/PILOT_STAGE_SCOPE.json"
LOCK_SCHEMA = "epd2.pilot-roadmap-lock/1"


def fail(message: str) -> None:
    raise ValueError(message)


def load_lock() -> dict:
    if not LOCK_PATH.is_file():
        fail(f"missing roadmap lock: {LOCK_PATH}")
    return json.loads(LOCK_PATH.read_text(encoding="utf-8"))


def validate_lock(lock: dict) -> None:
    if lock.get("schema_version") != LOCK_SCHEMA:
        fail("unexpected roadmap lock schema_version")
    if lock.get("status") != "LOCKED":
        fail("roadmap lock is not LOCKED")
    if lock.get("non_binding_pilot") is not True:
        fail("roadmap lock must preserve NON_BINDING_PILOT")

    stages = lock.get("stages")
    if not isinstance(stages, list):
        fail("roadmap lock stages must be an array")
    actual = {item.get("id"): item.get("title") for item in stages}
    if actual != FROZEN_STAGES:
        fail(f"roadmap stage drift detected: {actual!r}")

    p3 = next(item for item in stages if item.get("id") == "PILOT-03")
    caps = set(p3.get("required_capabilities") or [])
    if caps != PILOT03_REQUIRED_CAPABILITIES:
        fail("PILOT-03 required capability set drifted")
    pred = p3.get("accepted_predecessor") or {}
    if pred.get("filename") != PILOT02_C4_FILENAME:
        fail("PILOT-03 predecessor filename drifted")
    if pred.get("sha256") != PILOT02_C4_SHA256:
        fail("PILOT-03 predecessor SHA256 drifted")

    superseded = lock.get("superseded_guidance") or []
    if not any(
        x.get("path_inside_artifact") == "docs/pilot/PILOT-02/25_NEXT_GATE_RECOMMENDATION.md"
        and x.get("source_artifact_sha256") == PILOT02_C4_SHA256
        for x in superseded
    ):
        fail("stale PILOT-02 next-gate guidance is not explicitly superseded")


def infer_stage_from_filename(name: str) -> str | None:
    match = re.search(r"PILOT[-_]?0?([1-7])(?:\D|$)", name, re.IGNORECASE)
    if not match:
        return None
    return f"PILOT-0{match.group(1)}"


def archive_root(names: list[str]) -> str:
    roots: set[str] = set()
    for raw in names:
        if not raw or raw.startswith("__MACOSX/"):
            continue
        p = PurePosixPath(raw)
        if p.is_absolute() or ".." in p.parts:
            fail(f"unsafe archive path: {raw}")
        if p.parts:
            roots.add(p.parts[0])
    if len(roots) != 1:
        fail(f"candidate must have exactly one root, found: {sorted(roots)}")
    return next(iter(roots))


def read_manifest_from_zip(zip_path: Path) -> tuple[dict, str, list[str]]:
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        root = archive_root(names)
        manifest_name = f"{root}/{SCOPE_MANIFEST}"
        if manifest_name not in names:
            fail(
                f"missing mandatory scope manifest {SCOPE_MANIFEST}; "
                "PILOT-03+ candidates fail closed"
            )
        try:
            manifest = json.loads(zf.read(manifest_name).decode("utf-8"))
        except Exception as exc:
            fail(f"invalid scope manifest: {exc}")
        return manifest, root, names


def validate_candidate(zip_path: Path, lock: dict) -> None:
    if not zip_path.is_file():
        fail(f"candidate ZIP not found: {zip_path}")

    filename_stage = infer_stage_from_filename(zip_path.name)
    if filename_stage is None:
        fail("candidate filename does not identify a locked PILOT stage")

    manifest, root, names = read_manifest_from_zip(zip_path)
    stage_id = manifest.get("stage_id")
    stage_title = manifest.get("stage_title")

    if stage_id != filename_stage:
        fail(f"filename/manifest stage mismatch: filename={filename_stage}, manifest={stage_id}")
    if stage_id not in FROZEN_STAGES:
        fail(f"unknown or unlocked stage: {stage_id}")
    if stage_title != FROZEN_STAGES[stage_id]:
        fail(
            f"scope mismatch for {stage_id}: expected {FROZEN_STAGES[stage_id]!r}, "
            f"got {stage_title!r}"
        )
    if manifest.get("roadmap_lock_schema_version") != LOCK_SCHEMA:
        fail("candidate does not bind to the current roadmap lock schema")
    if manifest.get("non_binding_pilot") is not True:
        fail("candidate does not preserve NON_BINDING_PILOT")

    if stage_id == "PILOT-03":
        pred = manifest.get("accepted_predecessor") or {}
        if pred.get("filename") != PILOT02_C4_FILENAME:
            fail("PILOT-03 candidate names the wrong accepted predecessor")
        if pred.get("sha256") != PILOT02_C4_SHA256:
            fail("PILOT-03 candidate has the wrong accepted predecessor SHA256")
        caps = set(manifest.get("required_capabilities") or [])
        if caps != PILOT03_REQUIRED_CAPABILITIES:
            fail(
                "PILOT-03 candidate capability manifest must be exactly: "
                + ", ".join(sorted(PILOT03_REQUIRED_CAPABILITIES))
            )
        if manifest.get("operations_workstream") in {True, "PILOT-03"}:
            fail("deployment/operations workstream may not masquerade as PILOT-03")

        # Catch the exact stale-scope pattern that caused the rejected candidate.
        # Scan only active documents for the candidate's current stage. Historical
        # predecessor documents and the canonical roadmap lock intentionally quote
        # superseded wording and must not trigger this heuristic.
        stale_markers = (
            "pilot operation readiness",
            "deployment operations and real pilot readiness",
            "it did not change the product",
        )
        active_stage_prefix = f"{root}/docs/pilot/{stage_id}/"
        relevant_docs = [
            n for n in names if n.startswith(active_stage_prefix) and n.lower().endswith(".md")
        ]
        with zipfile.ZipFile(zip_path) as zf:
            for name in relevant_docs:
                try:
                    text = zf.read(name).decode("utf-8", errors="ignore").lower()
                except Exception:
                    continue
                for marker in stale_markers:
                    if marker in text:
                        fail(f"stale/wrong PILOT-03 scope marker {marker!r} found in {name}")

    print(f"PILOT roadmap scope PASS: {zip_path.name} -> {stage_id} / {stage_title}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--zip", type=Path)
    args = parser.parse_args()

    try:
        lock = load_lock()
        validate_lock(lock)
        if args.self_check:
            print("PILOT roadmap lock self-check PASS")
        if args.zip is not None:
            validate_candidate(args.zip, lock)
        if not args.self_check and args.zip is None:
            parser.error("use --self-check and/or --zip")
    except (ValueError, json.JSONDecodeError, zipfile.BadZipFile) as exc:
        print(f"PILOT roadmap guard FAIL: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
