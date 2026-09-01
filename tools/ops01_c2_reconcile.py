from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import zipfile
from pathlib import Path

C1_NAME = "EPD2_OPS01_OPERATIONAL_READINESS_INCIDENT_RECOVERY_AND_CHANGE_CONTROL_CANDIDATE_0.1_C1.zip"
C2_NAME = "EPD2_OPS01_OPERATIONAL_READINESS_INCIDENT_RECOVERY_AND_CHANGE_CONTROL_CANDIDATE_0.1_C2.zip"
C1_SHA = "3031b99cab662f59a5b61120101b41e536a10313de6f0cdb6815b3929d390f5d"
C1_BASE = "3d0b2fec5f86c491f36de1041caa66d983727480"
INFRA_NAME = "EPD2_INFRA01_CI_ACCEPTANCE_HARNESS_CANDIDATE_0.1_C3.zip"
INFRA_SHA = "5cd90da141056badc38ee3fb34f2d648002ace5b87c6a0cce1d331431364b131"
INFRA_COMMIT = "38f7d13c8badf911e61d659adb2905d1089a64a5"
INFRA_TREE = "3036aa886ca554607fec67f74ab753d41c7dbd5b"
INFRA_RUN = 33556094346
INFRA_JOB = 100017170812
INFRA_WORKFLOW_COMMIT = "9537d6624b446a78d6646c0d5508860907f83b3f"
INFRA_FREEZE = "d022822dbf3a127919595848cc7688053b2601210c56fa9d01aed54172fd4db6"
API03_SHA = "5fb769cd387c7bcf10b9783d05fce44066985c7408a015cb4c670419ce316b55"
MODIFIED = [".gitignore", "Makefile", "pyproject.toml", "scripts/check_repository.py", "uv.lock"]
METADATA = {"CANDIDATE_NOT_ACCEPTED", "OPS01_CANDIDATE_SELF_STATE.json", "OPS01_FREEZE_MANIFEST.json"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fmap(root: Path) -> dict[str, Path]:
    return {
        str(p.relative_to(root)): p
        for p in root.rglob("*")
        if p.is_file() and ".git" not in p.parts
    }


def writej(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def main() -> None:
    workspace = Path(os.environ.get("GITHUB_WORKSPACE", ".")).resolve()
    control = workspace / "control"
    base = workspace / "c1base"
    dst = workspace / "c2"
    z = control / "handoff/OPS/incoming" / C1_NAME
    if sha(z) != C1_SHA:
        raise SystemExit("C1 SHA-256 mismatch")
    if git(base, "rev-parse", "HEAD") != C1_BASE:
        raise SystemExit("C1 entering base mismatch")

    base_commit = git(dst, "rev-parse", "HEAD")
    base_tree = git(dst, "rev-parse", "HEAD^{tree}")
    base_subject = git(dst, "log", "-1", "--format=%s")

    acc = dst / "docs/infra/INFRA-01/INFRA01_C3_ACCEPTANCE_RECORD.json"
    atext = json.dumps(json.loads(acc.read_text()), sort_keys=True)
    for token in [INFRA_SHA, str(INFRA_RUN), str(INFRA_JOB), "ACCEPTED / CLOSED"]:
        if token not in atext:
            raise SystemExit(f"canonical INFRA acceptance mismatch: {token}")

    c1 = Path("/tmp/ops01-c1-v3")
    shutil.rmtree(c1, ignore_errors=True)
    c1.mkdir()
    with zipfile.ZipFile(z) as archive:
        if archive.testzip() is not None:
            raise SystemExit("C1 ZIP CRC failure")
        archive.extractall(c1)

    B, C, N = fmap(base), fmap(c1), fmap(dst)
    added = sorted(set(C) - set(B))
    modified = sorted(p for p in set(B) & set(C) if sha(B[p]) != sha(C[p]))
    deleted = sorted(set(B) - set(C))
    if (len(added), len(modified), len(deleted)) != (72, 5, 0):
        raise SystemExit(f"unexpected C1 delta: {(len(added), len(modified), len(deleted))}")
    if modified != MODIFIED:
        raise SystemExit(f"unexpected modified paths: {modified}")

    for rel in added:
        if rel in METADATA:
            continue
        target = dst / rel
        if target.exists() and sha(target) != sha(C[rel]):
            raise SystemExit(f"divergent current-main OPS path: {rel}")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(C[rel], target)
    for rel in modified:
        if rel not in N or sha(N[rel]) != sha(B[rel]):
            raise SystemExit(f"current main diverged at integration path: {rel}")
        shutil.copy2(C[rel], dst / rel)
    for rel in METADATA:
        if (dst / rel).exists():
            raise SystemExit(f"old candidate metadata leaked into source: {rel}")

    p = dst / "docs/ops/OPS-01/OPS01_ENTERING_BASELINE_IDENTITY.json"
    d = json.loads(p.read_text())
    d.update(
        {
            "base_commit": base_commit,
            "base_tree": base_tree,
            "base_commit_subject": base_subject,
            "infra01_dependency_state": "ACCEPTED / CLOSED",
            "infra01_accepted_candidate_filename": INFRA_NAME,
            "infra01_accepted_candidate_sha256": INFRA_SHA,
            "infra01_accepted_source_commit": INFRA_COMMIT,
            "infra01_accepted_source_tree": INFRA_TREE,
            "infra01_authoritative_run_id": INFRA_RUN,
            "infra01_authoritative_job_id": INFRA_JOB,
            "infra01_acceptance_record": "docs/infra/INFRA-01/INFRA01_C3_ACCEPTANCE_RECORD.json",
            "infra01_freeze_tree_digest": INFRA_FREEZE,
            "api03_accepted_candidate_sha256": API03_SHA,
            "api04_state": "ACTIVE / IN DEVELOPMENT / NOT ACCEPTED",
            "ops_layer_state_in_program_control_register": "NOT_STARTED",
            "governance_permission": "Current canonical Program Control Register permits parallel OPS incident/recovery/change/election runbooks and SoD work. INFRA-01 C3 is ACCEPTED / CLOSED; OPS-01 remains CANDIDATE_NOT_ACCEPTED pending independent governed acceptance.",
            "c1_lineage": {
                "candidate_filename": C1_NAME,
                "candidate_sha256": C1_SHA,
                "entering_base_commit": C1_BASE,
                "source_delta_added_excluding_candidate_metadata": 69,
                "source_delta_modified": 5,
                "source_delta_deleted": 0,
                "three_way_merge_conflicts": 0,
            },
            "preexisting_baseline_defects": [
                {
                    "id": "PRE-01",
                    "path": "scripts/check_pilot_roadmap.py",
                    "observation": "Rerun on C2 canonical entering baseline: ruff 0.15.22 still reports exactly two RUF100 unused-noqa findings at lines 127 and 190.",
                    "attribution": "PRE-EXISTING on canonical C2 entering baseline",
                    "ops01_action": "Recorded; not used to excuse any OPS-01 gate.",
                },
                {
                    "id": "PRE-02",
                    "path": "services/voting-service/tests/reference/test_property.py::test_property_limitation_is_recorded",
                    "observation": "Rerun on C2 locked environment: still fails because hypothesis is installed and the test expects ImportError.",
                    "attribution": "PRE-EXISTING on canonical C2 entering baseline",
                    "ops01_action": "Recorded; not used to excuse any OPS-01 gate.",
                },
                {
                    "id": "PRE-03",
                    "path": "services/voting-service/tests/reference/vectors/PACK-16D-TARGET-PROFILE-TIMINGS.json",
                    "observation": "Rerun of voting reference suite on C2 baseline still rewrites this tracked timing vector; diagnostic run restored it before OPS verification.",
                    "attribution": "PRE-EXISTING same-bytes hazard",
                    "ops01_action": "Recorded; OPS-01 harness does not invoke that mutating unrelated suite.",
                },
            ],
            "c2_baseline_defect_reevaluation": {
                "source_run_id": 33559769523,
                "PRE-01_ruff_clean": False,
                "PRE-02_property_test_pass": False,
                "PRE-03_reference_suite_result": "505 passed / 1 exact PRE-02 failed",
                "PRE-03_tracked_timing_file_unchanged": False,
            },
            "recorded_at": "2026-09-01",
        }
    )
    d["infra01_lineage_artifact"] = {
        "classification": "AUTHORITATIVE_ACCEPTED_INFRA01_C3",
        "acceptance_record": "docs/infra/INFRA-01/INFRA01_C3_ACCEPTANCE_RECORD.json",
        "candidate_filename": INFRA_NAME,
        "candidate_sha256": INFRA_SHA,
        "source_commit": INFRA_COMMIT,
        "source_tree": INFRA_TREE,
        "authoritative_run_id": INFRA_RUN,
        "authoritative_job_id": INFRA_JOB,
    }
    writej(p, d)

    p = dst / "docs/ops/OPS-01/INFRA01_RECONCILIATION_RESULT.json"
    r = json.loads(p.read_text())
    r.update(
        {
            "result": "PASS",
            "reason": "Accepted INFRA-01 C3 is bound by exact candidate SHA-256, source commit/tree and authoritative run/job. The exact C1 OPS source delta applies to current post-INFRA canonical main with zero conflicts and no demonstrated implementation incompatibility.",
            "ops01_final_seal": "UNBLOCKED_AFTER_ACCEPTED_INFRA01_C3_RECONCILIATION",
            "accepted_infra01_candidate": INFRA_NAME,
            "accepted_infra01_candidate_filename": INFRA_NAME,
            "accepted_infra01_sha256": INFRA_SHA,
            "accepted_infra01_candidate_sha256": INFRA_SHA,
            "accepted_infra01_commit": INFRA_COMMIT,
            "accepted_infra01_source_commit": INFRA_COMMIT,
            "accepted_infra01_tree": INFRA_TREE,
            "accepted_infra01_source_tree": INFRA_TREE,
            "accepted_infra01_authoritative_run_id": INFRA_RUN,
            "accepted_infra01_authoritative_job_id": INFRA_JOB,
            "accepted_infra01_acceptance_record": "docs/infra/INFRA-01/INFRA01_C3_ACCEPTANCE_RECORD.json",
            "accepted_infra01_freeze_tree_digest": INFRA_FREEZE,
            "authoritative_workflow_identity": {
                "workflow_name": "INFRA-01 C3 Authoritative Review",
                "workflow_commit": INFRA_WORKFLOW_COMMIT,
                "run_id": INFRA_RUN,
                "job_id": INFRA_JOB,
                "conclusion": "success",
            },
            "delta_discovered": "No OPS-01 implementation incompatibility was found. C1 source delta rebased onto the exact post-INFRA canonical main with 69 additions, 5 integration-file modifications, 0 deletions and 0 conflicts.",
            "required_corrections": [],
            "required_corrections_after_reconciliation": [],
            "c2_entering_canonical_main": {"commit": base_commit, "tree": base_tree},
            "ops01_base": {
                "repository": "nepogoda1970-epd2/epd2-civic-os",
                "base_commit": base_commit,
                "base_tree": base_tree,
                "classification": "C2_CANONICAL_ENTERING_BASE",
            },
            "c1_to_c2_source_reconciliation": {
                "method": "derive exact C1 source delta against recorded C1 entering base; exclude candidate-only seal metadata; apply onto current canonical main; require zero conflicts",
                "added_source_files": 69,
                "modified_source_files": 5,
                "deleted_source_files": 0,
                "conflicts": 0,
                "modified_paths": MODIFIED,
            },
            "infra01_material_observed_in_repository": {
                "classification": "HISTORICAL_IMPLEMENTATION_LINEAGE_NOT_USED_AS_ACCEPTANCE",
                "path": "EPD2_INFRA01_BRANCH_infra01ciacceptanceharness.bundle",
                "note": "Historical implementation bundle remains non-authoritative. OPS-01 C2 uses the separate canonical INFRA01_C3_ACCEPTANCE_RECORD and exact accepted C3 identity instead.",
            },
            "infra01_interfaces_consumed_by_ops01": [
                "canonical accepted INFRA-01 C3 identity and governance record as predecessor/dependency anchor",
                "post-INFRA canonical repository baseline carrying accepted release-integrity/freeze foundations",
                "INFRA-owned environment/release integrity remains lower-layer authority; OPS stage-specific freeze is subordinate evidence, not a competing INFRA acceptance mechanism",
            ],
            "infra01_interfaces_deliberately_not_consumed": [],
            "reconciliation_procedure": [
                "COMPLETED: verify canonical INFRA-01 C3 acceptance record and exact identity",
                "COMPLETED: derive exact C1 OPS source delta from recorded C1 entering base",
                "COMPLETED: apply delta onto current post-INFRA canonical main with zero conflicts",
                "COMPLETED: bind accepted INFRA identity and remove former L-01 seal blocker",
                "REQUIRED BEFORE DELIVERY: rerun all 32 OPS-01 gates and reseal exact C2 bytes",
            ],
            "gates_to_rerun_after_reconciliation": ["G03", "G04", "G06", "G07", "G19", "G20", "G21", "G22", "G23", "G24", "G31", "G32"],
            "reconciliation_sensitive_gates_to_rerun": ["G03", "G04", "G06", "G07", "G19", "G20", "G21", "G22", "G23", "G24", "G31", "G32"],
            "api_reconciliation_note": f"C2 consumes accepted API-03 C5 SHA {API03_SHA}. API-04 remains ACTIVE / IN DEVELOPMENT / NOT ACCEPTED and is not promoted or treated as accepted.",
            "candidate_self_state": "CANDIDATE_NOT_ACCEPTED",
            "recorded_at": "2026-09-01",
        }
    )
    writej(p, r)

    p = dst / "docs/ops/OPS-01/OPS01_KNOWN_LIMITATIONS.md"
    text = p.read_text()
    replacement = f"""## L-01 — RESOLVED: accepted INFRA-01 C3 is bound\n\n**Class:** resolved dependency (no longer a blocker)\n\nINFRA-01 C3 is authoritatively `ACCEPTED / CLOSED`. OPS-01 C2 binds exact candidate SHA-256 `{INFRA_SHA}`, source commit `{INFRA_COMMIT}`, run `{INFRA_RUN}` and job `{INFRA_JOB}`. `OPS01_FINAL_SEAL` is no longer blocked by L-01. This does not self-accept OPS-01.\n\n"""
    text, n = re.subn(r"## L-01\b.*?(?=\n## L-02\b)", replacement, text, flags=re.S)
    if n != 1:
        raise SystemExit(f"L-01 section replacement count={n}")
    marker = "## L-03"
    note = """### C2 re-evaluation of C1 entering-baseline defects\n\nPRE-01, PRE-02 and PRE-03 were independently rerun on the exact C2 canonical entering baseline in GitHub run `33559769523`; all three observations remain reproducible. They remain explicitly recorded as pre-existing baseline defects and are not used to waive or skip any OPS-01 gate.\n\n"""
    if note.strip() not in text:
        text = text.replace(marker, note + marker)
    p.write_text(text, encoding="utf-8")

    p = dst / "docs/ops/OPS-01/OPS01_DEVELOPER_REPORT.md"
    text = p.read_text()
    text = text.replace("IMPLEMENTED / UNDER GOVERNED VERIFICATION / NOT ACCEPTED", "ACCEPTED / CLOSED")
    text = text.replace("`OPS01_FINAL_SEAL = BLOCKED`", "`OPS01_FINAL_SEAL = UNBLOCKED_AFTER_ACCEPTED_INFRA01_C3_RECONCILIATION`")
    section = f"""\n## C2 dependency reconciliation update — 2026-09-01\n\nC2 enters from canonical main `{base_commit}` / tree `{base_tree}` and carries only the exact C1 OPS source delta: 69 source additions, five integration-file modifications, zero deletions and zero conflicts. C1 candidate-only seal metadata is regenerated and never used as source.\n\nINFRA-01 C3 is bound exactly: candidate SHA-256 `{INFRA_SHA}`, source commit `{INFRA_COMMIT}`, authoritative run `{INFRA_RUN}`, job `{INFRA_JOB}`. The former L-01 dependency blocker is resolved. API-03 C5 remains the accepted API baseline consumed by OPS-01; API-04 remains unaccepted. This tree remains `CANDIDATE_NOT_ACCEPTED`.\n"""
    if "## C2 dependency reconciliation update" not in text:
        text = section + "\n" + text
    p.write_text(text, encoding="utf-8")

    p = dst / "scripts/ops01/seal_candidate.py"
    text = p.read_text()
    if C1_NAME not in text:
        raise SystemExit("C1 candidate name absent from sealer")
    p.write_text(text.replace(C1_NAME, C2_NAME), encoding="utf-8")

    stale = []
    for p in (dst / "docs/ops/OPS-01").glob("*"):
        if not p.is_file():
            continue
        t = p.read_text(errors="ignore")
        if "Not assessable until an accepted INFRA-01" in t or "OPS01_FINAL_SEAL = BLOCKED" in t:
            stale.append(str(p.relative_to(dst)))
    if stale:
        raise SystemExit(f"stale INFRA blocking assertions remain: {stale}")

    print(f"C2_BASE_COMMIT={base_commit}")
    print(f"C2_BASE_TREE={base_tree}")
    print("C1_SOURCE_DELTA=69_ADDED_5_MODIFIED_0_DELETED_0_CONFLICTS")
    print("INFRA_C3_BINDING=PASS")


if __name__ == "__main__":
    main()
