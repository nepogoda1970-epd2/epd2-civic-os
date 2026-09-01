from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request

AUTHORITATIVE_TARGET_MAIN = "e89778667ee65e38001874b01681eff64c11354f"
AUTHORITATIVE_TARGET_TREE = "5c2c1fddcdafdf73c38ad68d5494590d33a5b97d"
CANDIDATE_SHA = "39a6b02af03269a8ebf61216503fa03df2abf4e5194aa3c45c6f4bb176f2ad27"
RUN_ID = 33564968274
JOB_ID = 100045926256
WORKFLOW_COMMIT = "0cb18e707d18d034d8dec8d76662f3aac8042eca"
EVIDENCE_ARTIFACT_ID = 9822755955
EVIDENCE_ARTIFACT_DIGEST = "sha256:4bc58f043f0a89753086a5d6b560bf7af800e80cc310ec5951c60035ad6567f7"
CANDIDATE_ARTIFACT_ID = 9822756668
CANDIDATE_ARTIFACT_DIGEST = "sha256:8e07a54a1a5b60285485e595630cca060a7c6c05f12c88d89b3dc97b45c22a46"

CONTROLLING_AUTHORITY_PATHS = [
    "docs/roadmap/EPD2_PROJECT_ENTRYPOINT.md",
    "docs/roadmap/EPD2_PROGRAM_CONTROL_REGISTER.md",
    "docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md",
    "docs/roadmap/EPD2_BSI_VOTING_BOOTSTRAP_RULE.md",
    "docs/security/bsi/EPD2_BSI_CC_PP_0121_CERTIFICATION_READINESS_GAP_MATRIX_0.1.md",
    "docs/infra/INFRA-01/INFRA01_C3_ACCEPTANCE_RECORD.json",
    "docs/handover/PACK-15-PRIVACY-EVIDENCE.md",
    "docs/handover/PACK-15-SECURITY-EVIDENCE.md",
    "docs/packs/PACK-16/PACK-16B-BACKUP-RECOVERY-AND-COMPENSATION.md",
    "docs/packs/PACK-16/PACK-16B-INCIDENT-AND-NOTIFICATION-MODEL.md",
    "docs/packs/PACK-16/PACK-16D-LOGGING-AND-AUDIT-BOUNDARY.md",
    "docs/packs/PACK-16/PACK-16D-SCOPE-AND-IMPLEMENTATION-BOUNDARY.md",
]


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def git_check(repo: Path, *args: str) -> None:
    subprocess.check_call(["git", "-C", str(repo), *args])


def api_get(url: str) -> dict:
    token = os.environ["GH_TOKEN"]
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(req) as response:
        return json.load(response)


def reconcile_current_main(repo: Path) -> dict:
    current = git(repo, "rev-parse", "HEAD")
    current_tree = git(repo, "rev-parse", "HEAD^{tree}")
    git_check(repo, "merge-base", "--is-ancestor", AUTHORITATIVE_TARGET_MAIN, current)

    authority_diff = git(
        repo,
        "diff",
        "--name-only",
        f"{AUTHORITATIVE_TARGET_MAIN}..{current}",
        "--",
        *CONTROLLING_AUTHORITY_PATHS,
    )
    assert authority_diff == "", f"controlling authority changed after authoritative review: {authority_diff}"

    pcr = (repo / "docs/roadmap/EPD2_PROGRAM_CONTROL_REGISTER.md").read_text()
    assert "| OPS | `NOT_STARTED` | Procedures/runbooks may be prepared; runtime closure follows INFRA. |" in pcr
    assert "API-04 = ACTIVE / IN DEVELOPMENT / NOT ACCEPTED" in pcr
    assert "INFRA-01 is therefore `ACCEPTED / CLOSED`" in pcr
    assert "OPS-01 authoritative acceptance and bounded stage closure (2026-09-01)" not in pcr

    raw = git(repo, "diff", "--name-status", f"{AUTHORITATIVE_TARGET_MAIN}..{current}")
    changes = []
    for line in raw.splitlines():
        if not line:
            continue
        parts = line.split("\t")
        changes.append({"status": parts[0], "paths": parts[1:]})

    return {
        "authoritative_target_main": AUTHORITATIVE_TARGET_MAIN,
        "authoritative_target_tree": AUTHORITATIVE_TARGET_TREE,
        "governance_decision_entering_main": current,
        "governance_decision_entering_tree": current_tree,
        "controlling_authority_diff": [],
        "concurrent_changes_since_authoritative_target": changes,
        "classification": "NO_CONTROLLING_AUTHORITY_CONFLICT",
    }


def verify_authoritative_evidence(evidence: Path) -> tuple[dict, dict]:
    run = api_get(f"https://api.github.com/repos/nepogoda1970-epd2/epd2-civic-os/actions/runs/{RUN_ID}")
    assert run["status"] == "completed"
    assert run["conclusion"] == "success"
    assert run["head_sha"] == WORKFLOW_COMMIT
    assert run["name"] == "OPS-01 C2 Authoritative Review"

    ev_meta = api_get(
        f"https://api.github.com/repos/nepogoda1970-epd2/epd2-civic-os/actions/artifacts/{EVIDENCE_ARTIFACT_ID}"
    )
    cand_meta = api_get(
        f"https://api.github.com/repos/nepogoda1970-epd2/epd2-civic-os/actions/artifacts/{CANDIDATE_ARTIFACT_ID}"
    )
    assert ev_meta["name"] == f"ops01-c2-authoritative-evidence-{RUN_ID}"
    assert ev_meta["digest"] == EVIDENCE_ARTIFACT_DIGEST
    assert cand_meta["name"] == f"ops01-c2-authoritative-candidate-{RUN_ID}"
    assert cand_meta["digest"] == CANDIDATE_ARTIFACT_DIGEST

    authoritative = json.loads((evidence / "OPS01_C2_AUTHORITATIVE_ACCEPTANCE_RESULT.json").read_text())
    bsi = json.loads((evidence / "OPS01_C2_BSI_READINESS_DISPOSITION.json").read_text())

    assert authoritative["schema"] == "epd2.ops01.authoritative-acceptance/1"
    assert authoritative["stage"] == "OPS-01"
    assert authoritative["verdict"] == "PASS"
    assert authoritative["candidate"]["sha256"] == CANDIDATE_SHA
    assert authoritative["candidate"]["size_bytes"] == 16457357
    assert authoritative["candidate"]["member_count"] == 1489
    assert authoritative["source"]["seal_commit"] == "a12d990d76fc4ebf7d0d08634b4cad0fbc5862cc"
    assert authoritative["source"]["seal_tree"] == "a91a290ae87a83bede5d3cfc0e53dc682379b8a3"
    assert authoritative["source"]["freeze_file_count"] == 1486
    assert authoritative["source"]["freeze_tree_digest"] == "e08ef203c096e17779592407d7b48c843c84f4f27d99e6e7514ddb7491a11613"
    assert authoritative["canonical_target"]["main_commit"] == AUTHORITATIVE_TARGET_MAIN
    assert authoritative["canonical_target"]["main_tree"] == AUTHORITATIVE_TARGET_TREE
    h = authoritative["ops_harness"]
    assert (h["gates_total"], h["gates_executed"], h["gates_passed"]) == (32, 32, 32)
    assert h["gates_failed"] == [] and h["skipped"] == [] and h["environment_blocked"] == [] and h["not_run"] == []

    assert bsi["schema"] == "epd2.ops01.bsi-readiness-disposition/1"
    assert bsi["candidate_sha256"] == CANDIDATE_SHA
    assert bsi["result"] == "PASS_WITH_EXPLICIT_EXISTING_DEFERRED_GAPS"
    assert bsi["certification_claim"] == "NONE"
    assert bsi["new_certification_blockers"] == []
    assert len(bsi["deferred_existing_gap_bindings"]) == 9
    inv = bsi["stronger_epd2_invariants_preserved"]
    assert inv["no_persistent_person_member_identifier_in_voting_domain"] is True
    assert inv["identity_ballot_unlinkability"] is True
    return authoritative, bsi


def build_acceptance_record(authoritative: dict, bsi: dict, reconciliation: dict) -> dict:
    return {
        "schema": "epd2.ops01.acceptance-record/1",
        "stage": "OPS-01 — Operational Readiness, Incident, Recovery & Change Control Foundation",
        "decision": "ACCEPTED / CLOSED",
        "decision_date": "2026-09-01",
        "decision_authority": "Project Owner",
        "decision_basis": "Independent post-run governance decision after successful exact-sealed-byte authoritative GitHub acceptance, followed by fail-closed reconciliation against the then-current canonical main.",
        "scope": {
            "bounded_stage": "OPS-01",
            "overall_ops_layer": "OPEN",
            "primary_program_stage_unchanged": "API-04 ACTIVE / IN DEVELOPMENT / NOT ACCEPTED",
        },
        "authoritative_review_target": {
            "repository": "nepogoda1970-epd2/epd2-civic-os",
            "branch": "main",
            "commit": AUTHORITATIVE_TARGET_MAIN,
            "tree": AUTHORITATIVE_TARGET_TREE,
        },
        "post_run_canonical_reconciliation": reconciliation,
        "candidate": {
            "filename": authoritative["candidate"]["filename"],
            "sha256": authoritative["candidate"]["sha256"],
            "size_bytes": authoritative["candidate"]["size_bytes"],
            "member_count": authoritative["candidate"]["member_count"],
            "source_commit": authoritative["source"]["seal_commit"],
            "source_tree": authoritative["source"]["seal_tree"],
            "freeze_file_count": authoritative["source"]["freeze_file_count"],
            "freeze_tree_digest": authoritative["source"]["freeze_tree_digest"],
            "candidate_self_acceptance": False,
        },
        "accepted_predecessor": {
            "stage": "INFRA-01",
            "candidate_sha256": authoritative["accepted_infra01"]["candidate_sha256"],
            "source_commit": authoritative["accepted_infra01"]["source_commit"],
            "source_tree": authoritative["accepted_infra01"]["source_tree"],
            "authoritative_run_id": authoritative["accepted_infra01"]["run_id"],
            "authoritative_job_id": authoritative["accepted_infra01"]["job_id"],
        },
        "authoritative_review": {
            "workflow": "OPS-01 C2 Authoritative Review",
            "run_id": RUN_ID,
            "job_id": JOB_ID,
            "workflow_commit": WORKFLOW_COMMIT,
            "conclusion": "success",
            "terminal_marker": f"OPS01_C2_AUTHORITATIVE_RESULT:PASS:{CANDIDATE_SHA}",
            "canonical_harness": "32/32 governed OPS-01 gates EXECUTED AND PASS; 0 failed; 0 skipped; 0 environment-blocked; 0 not-run",
            "ops_tests": "88/88 PASS",
            "postgresql_server": "16.15",
            "quality": "ruff format PASS; ruff check PASS; mypy PASS",
            "sealed_transport_identity": "PASS",
            "freeze_manifest_verification": "1486/1486 governed files PASS",
            "same_governed_source_bytes_after_execution": True,
            "evidence_artifact": {
                "name": f"ops01-c2-authoritative-evidence-{RUN_ID}",
                "id": EVIDENCE_ARTIFACT_ID,
                "digest": EVIDENCE_ARTIFACT_DIGEST,
            },
            "candidate_artifact": {
                "name": f"ops01-c2-authoritative-candidate-{RUN_ID}",
                "id": CANDIDATE_ARTIFACT_ID,
                "digest": CANDIDATE_ARTIFACT_DIGEST,
            },
        },
        "bsi_certification_readiness": {
            "result": bsi["result"],
            "certification_claim": bsi["certification_claim"],
            "new_certification_blockers": bsi["new_certification_blockers"],
            "touched_rows": bsi["touched_rows"],
            "stronger_epd2_invariants_preserved": bsi["stronger_epd2_invariants_preserved"],
            "deferred_existing_gap_bindings": bsi["deferred_existing_gap_bindings"],
            "persisted_disposition": "docs/ops/OPS-01/OPS01_C2_BSI_READINESS_DISPOSITION.json",
        },
        "authoritative_result_file": "docs/ops/OPS-01/OPS01_C2_AUTHORITATIVE_ACCEPTANCE_RESULT.json",
        "master_register": {"unchanged_by_this_decision": True, "fir_status_changes": []},
        "exclusions": [
            "This decision closes only bounded OPS-01; it does not close the overall OPS layer.",
            "It does not change API-04 status or close the API layer.",
            "It does not close INFRA, CTRL, final FRONT or SEC.",
            "It is not a production-readiness or legal-activation decision.",
            "It is not BSI/Common-Criteria/EAL4 or final security certification.",
        ],
    }


def patch_pcr(repo: Path, reconciliation: dict) -> None:
    p = repo / "docs/roadmap/EPD2_PROGRAM_CONTROL_REGISTER.md"
    s = p.read_text()
    assert "OPS-01 authoritative acceptance and bounded stage closure (2026-09-01)" not in s
    old = "| OPS | `NOT_STARTED` | Procedures/runbooks may be prepared; runtime closure follows INFRA. |"
    new = "| OPS | `OPS-01 ACCEPTED / CLOSED; OPS LAYER OPEN` | Exact bounded OPS-01 Operational Readiness, Incident, Recovery & Change Control Foundation is accepted/closed at C2. The overall OPS layer remains open; final OPS closure still follows API/INFRA dependencies and the governed system-trial path. |"
    assert s.count(old) == 1
    s = s.replace(old, new, 1)

    anchor = "**INFRA-01 authoritative acceptance and bounded stage closure (2026-09-01):**"
    start = s.index(anchor)
    end = s.index("\n\nOn 2026-08-26", start)
    current = reconciliation["governance_decision_entering_main"]
    concurrent_count = len(reconciliation["concurrent_changes_since_authoritative_target"])
    para = f'''\n\n**OPS-01 authoritative acceptance and bounded stage closure (2026-09-01):** exact sealed C2 candidate `EPD2_OPS01_OPERATIONAL_READINESS_INCIDENT_RECOVERY_AND_CHANGE_CONTROL_CANDIDATE_0.1_C2.zip`, SHA-256 `{CANDIDATE_SHA}`, size `16,457,357` bytes, passed the independent sealed-byte GitHub Actions workflow `OPS-01 C2 Authoritative Review`, authoritative run `{RUN_ID}`, job `{JOB_ID}`, workflow commit `{WORKFLOW_COMMIT}`, conclusion `success`. The runner independently proved ZIP structure and exact transport identity, bound the candidate byte-for-byte to canonical authority `main@{AUTHORITATIVE_TARGET_MAIN}`, verified all `1,486` governed freeze-manifest files and freeze tree digest `e08ef203c096e17779592407d7b48c843c84f4f27d99e6e7514ddb7491a11613`, executed the locked environment on PostgreSQL `16.15`, passed Ruff format/check and mypy, passed `88/88` OPS tests, and completed all `32/32` OPS-01 gates with `0` failed, `0` skipped, `0` environment-blocked and `0` not-run. The exact terminal marker is `OPS01_C2_AUTHORITATIVE_RESULT:PASS:{CANDIDATE_SHA}`; same-governed-source-byte verification also passed after execution. Authoritative evidence artifact `ops01-c2-authoritative-evidence-{RUN_ID}`, artifact ID `{EVIDENCE_ARTIFACT_ID}`, GitHub artifact digest `{EVIDENCE_ARTIFACT_DIGEST}`; exact reviewed-candidate artifact `ops01-c2-authoritative-candidate-{RUN_ID}`, artifact ID `{CANDIDATE_ARTIFACT_ID}`, GitHub artifact-wrapper digest `{CANDIDATE_ARTIFACT_DIGEST}`. Before recording the post-run decision, governance fail-closed reconciled the newer canonical `main@{current}` against the authoritative target: all controlling PCR/Master/BSI/INFRA/PACK-15/PACK-16 authority files remained unchanged; `{concurrent_count}` concurrent non-authority file change(s) were recorded in the acceptance record with classification `NO_CONTROLLING_AUTHORITY_CONFLICT`. The independent BSI certification-readiness disposition is `PASS_WITH_EXPLICIT_EXISTING_DEFERRED_GAPS`: touched rows `M-02`, `M-03`, `M-11`, `M-16`, `M-17`, `M-19`, `M-20`, `M-25`, `M-27`, `M-30`; `new_certification_blockers = []`; stronger EPD² voting unlinkability/no-persistent-identifier invariants are preserved, and nine existing certification gaps remain explicitly deferred with owner, closure stage and required evidence in `docs/ops/OPS-01/OPS01_C2_BSI_READINESS_DISPOSITION.json`. The governance decision is recorded in `docs/ops/OPS-01/OPS01_C2_ACCEPTANCE_RECORD.json`. **OPS-01 is therefore `ACCEPTED / CLOSED` as a bounded operational-foundation stage.** The overall OPS layer remains open and its final closure still follows the canonical API/INFRA dependencies. `API-04 = ACTIVE / IN DEVELOPMENT / NOT ACCEPTED` remains unchanged. No production-readiness, legal-activation, BSI/CC/EAL4 or final-security claim follows from this transition.'''
    s = s[:end] + para + s[end:]

    marker = "**Parallel FRONT action:** FRONT-02 specification is established."
    assert s.count(marker) == 1
    action = f"**Parallel OPS action:** bounded `OPS-01 — Operational Readiness, Incident, Recovery & Change Control Foundation` is `ACCEPTED / CLOSED` at exact C2 SHA-256 `{CANDIDATE_SHA}`. This accepted foundation may be reused by later preview/final OPS work, but it does not close the overall OPS layer, does not authorize production operation, and does not alter `API-04 = ACTIVE / IN DEVELOPMENT / NOT ACCEPTED`.\n\n"
    s = s.replace(marker, action + marker, 1)
    p.write_text(s)


def main() -> None:
    repo = Path(sys.argv[1]).resolve()
    evidence = Path(sys.argv[2]).resolve()
    reconciliation = reconcile_current_main(repo)
    authoritative, bsi = verify_authoritative_evidence(evidence)

    target = repo / "docs/ops/OPS-01"
    target.mkdir(parents=True, exist_ok=True)
    (target / "OPS01_C2_AUTHORITATIVE_ACCEPTANCE_RESULT.json").write_text(
        json.dumps(authoritative, indent=2, sort_keys=True) + "\n"
    )
    (target / "OPS01_C2_BSI_READINESS_DISPOSITION.json").write_text(
        json.dumps(bsi, indent=2, sort_keys=True) + "\n"
    )
    (target / "OPS01_C2_ACCEPTANCE_RECORD.json").write_text(
        json.dumps(build_acceptance_record(authoritative, bsi, reconciliation), indent=2, ensure_ascii=False) + "\n"
    )
    patch_pcr(repo, reconciliation)

    assert git(repo, "diff", "--name-only", "--", "docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md") == ""
    tracked = set(filter(None, git(repo, "diff", "--name-only").splitlines()))
    untracked = set(filter(None, git(repo, "ls-files", "--others", "--exclude-standard").splitlines()))
    changed = tracked | untracked
    expected = {
        "docs/ops/OPS-01/OPS01_C2_ACCEPTANCE_RECORD.json",
        "docs/ops/OPS-01/OPS01_C2_AUTHORITATIVE_ACCEPTANCE_RESULT.json",
        "docs/ops/OPS-01/OPS01_C2_BSI_READINESS_DISPOSITION.json",
        "docs/roadmap/EPD2_PROGRAM_CONTROL_REGISTER.md",
    }
    assert changed == expected, (changed, expected)
    pcr = (repo / "docs/roadmap/EPD2_PROGRAM_CONTROL_REGISTER.md").read_text()
    assert "| OPS | `OPS-01 ACCEPTED / CLOSED; OPS LAYER OPEN`" in pcr
    assert "API-04 = ACTIVE / IN DEVELOPMENT / NOT ACCEPTED" in pcr
    assert "OPS-01 is therefore `ACCEPTED / CLOSED` as a bounded operational-foundation stage." in pcr
    git_check(repo, "diff", "--check")
    print("OPS01_C2_POSTRUN_GOVERNANCE_WRITER_V2=PASS")
    print("GOVERNANCE_ENTERING_MAIN=" + reconciliation["governance_decision_entering_main"])
    print("GOVERNANCE_ENTERING_TREE=" + reconciliation["governance_decision_entering_tree"])
    print("CONCURRENT_CHANGE_COUNT=" + str(len(reconciliation["concurrent_changes_since_authoritative_target"])))
    for path in sorted(changed):
        print(f"GOVERNANCE_DELTA={path}")


if __name__ == "__main__":
    main()
