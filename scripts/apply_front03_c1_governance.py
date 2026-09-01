from __future__ import annotations

import json
from pathlib import Path

PCR = Path("docs/roadmap/EPD2_PROGRAM_CONTROL_REGISTER.md")
RECORD = Path("docs/frontend/FRONT-03-C1-ACCEPTANCE-RECORD.json")

candidate_name = "EPD2_FRONT03_WS02_APPLICANT_AND_MEMBER_CORE_CANDIDATE_0.1_C1.zip"
candidate_sha = "fec7b19d77c27cbc3ef8a34e433f5aef94ef7853f76d3212bed6acd682497c26"
candidate_size = 17646011
accept_run = 33528038712
accept_job = 99923795567
accept_commit = "8fb650b5b82611926664474b93f6155d4c70d2de"
accept_artifact_id = 9808685208
accept_artifact_digest = "sha256:27dad0fb37c18bdeeda2d7d2b3670f5d0972a320b2956c8038dfe888f993e152"
finalize_run = 33527376449
finalize_job = 99921554491
runtime_run = 33526403812
runtime_job = 99918246676
preseal_sha = "da356d58192fa3afd5cedf0c7d8423df1faac3dd915d5ba26884dcb79e366294"
api02_sha = "9363561271f0f92d2afc42ccbb0d792cb5461c97c19a5f46a6fa51408bdfc6a9"
api02_run = 33497989489
front02_sha = "aaf980a2cd3b3b06d48218adaa68d109c8770e6abfcbef230197b51a87006179"
main_entering = "3d0b2fec5f86c491f36de1041caa66d983727480"
master_sha = "7f5c6a9a88f8e653b43dc542a595ac37bf7a0692"

if RECORD.exists():
    raise SystemExit(f"refusing to overwrite existing {RECORD}")

record = {
    "schema": "epd2.front03.acceptance-record/1",
    "stage": "FRONT-03 — WS-02 Applicant & Member Core",
    "decision": "ACCEPTED / CLOSED",
    "decision_date": "2026-09-01",
    "decision_authority": "Project Owner",
    "decision_basis": "Project Owner requested governed completion; independent sealed-byte GitHub acceptance completed successfully before this governance record.",
    "entering_canonical_main": main_entering,
    "candidate": {
        "filename": candidate_name,
        "sha256": candidate_sha,
        "size_bytes": candidate_size,
        "candidate_state_inside_sealed_bytes": "C1_CANDIDATE_NOT_ACCEPTED",
        "self_acceptance": False,
    },
    "technical_lineage": {
        "accepted_front02_c2_1_sha256": front02_sha,
        "front03_preseal_sha256": preseal_sha,
        "accepted_api02_c13_sha256": api02_sha,
        "accepted_api02_run_id": api02_run,
        "api03_dependency_discovered_for_c1": False,
    },
    "execution_and_seal": {
        "runtime_proof_run_id": runtime_run,
        "runtime_proof_job_id": runtime_job,
        "finalize_run_id": finalize_run,
        "finalize_job_id": finalize_job,
    },
    "independent_review": {
        "workflow": "FRONT-03 C1 governed finalize / independent-accept wrapper",
        "run_id": accept_run,
        "job_id": accept_job,
        "workflow_commit": accept_commit,
        "conclusion": "success",
        "evidence_artifact": "front03-c1-acceptance-evidence-33528038712",
        "evidence_artifact_id": accept_artifact_id,
        "evidence_artifact_digest": accept_artifact_digest,
        "result_marker": f"FRONT03_C1_ACCEPTANCE_RESULT:PASS:{candidate_sha}:{candidate_size}",
        "fresh_gates": {
            "exact_candidate_sha_size_crc": "PASS",
            "locked_dependencies_format_typecheck_lint_unit_build": "PASS",
            "tap_tests": "58/58 PASS",
            "vitest_tests": "30/30 PASS",
            "inherited_nonvisual_browser": "195/195 PASS",
            "c1_exact_api02_production_browser": "12/12 PASS",
            "production_fail_closed_browser": "6/6 PASS",
            "immutable_front03_visual_baseline": "27/27 PASS",
            "c1_validator": "14/14 PASS",
            "c1_mutations": "9/9 DETECTED",
        },
    },
    "accepted_scope": [
        "bounded FRONT-03 WS-02 Applicant & Member Core implementation stage",
        "exact API-02 C13 production adapter binding used by FRONT-03 C1",
        "Applicant-to-Member server-governed promotion boundary",
        "organization scope reauthorization and stale-scope refusal",
        "session/security projection non-disclosure",
        "WS-02 to WS-03 voting-handoff isolation without persistent identity",
        "inherited FRONT-00/01/02 and PACK-15 browser/a11y/keyboard/reflow regression scope exercised by independent acceptance",
        "27-shot immutable FRONT-03 visual baseline",
    ],
    "bsi_certification_readiness": {
        "status": "PREPARATORY ONLY / NOT CERTIFIED / NOT A CONFORMANCE CLAIM",
        "candidate_evidence": [
            "docs/frontend/FRONT-03-BSI-VOTING-READINESS-DELTA.md",
            "validation/front03/bsi-voting-readiness-delta.json",
        ],
        "hard_freeze_preserved": "no persistent member/person identifier inside voting domain",
        "new_unrecorded_blocker_introduced": False,
        "deferred_items_remain_governed": True,
    },
    "canonical_master": {
        "maintenance": "V26",
        "blob_sha": master_sha,
        "changed_by_this_decision": False,
        "reason": "bounded FRONT-03 acceptance changes current execution state but does not create, supersede, or close a Master future requirement",
    },
    "exclusions": [
        "This decision does not close the entire FRONT layer.",
        "Final integrated FRONT closure remains dependent on the canonical sequence API → INFRA → OPS → CTRL → FRONT.",
        "This decision does not close API-04 or the API layer.",
        "This decision does not declare production readiness or legal activation.",
        "This decision does not claim BSI certification, CC conformance, EAL4 certification, or security certification.",
    ],
    "next_permitted_status": "FRONT-03 C1 is the accepted bounded WS-02 baseline for later governed integration; current primary program work remains controlled by the live PCR.",
}
RECORD.parent.mkdir(parents=True, exist_ok=True)
RECORD.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")

text = PCR.read_text(encoding="utf-8")
if "**FRONT-03 authoritative acceptance and bounded stage closure (2026-09-01):**" in text:
    raise SystemExit("FRONT-03 closure already recorded")

insert_anchor = "\nOn 2026-08-26 API-01 completed independent authoritative acceptance."
if text.count(insert_anchor) != 1:
    raise SystemExit("PCR insertion anchor not unique")

closure = f'''\n\n**FRONT-03 authoritative acceptance and bounded stage closure (2026-09-01):** exact sealed candidate `{candidate_name}`, SHA-256 `{candidate_sha}`, size `{candidate_size:,}` bytes, passed independent sealed-byte GitHub verification in workflow `FRONT-03 C1 governed finalize`, authoritative acceptance run `{accept_run}`, job `{accept_job}`, workflow commit `{accept_commit}`, conclusion `success`. The independent runner downloaded the already sealed C1 artifact, verified exact SHA/size/CRC and no-self-acceptance state, performed a fresh locked dependency install, formatting/type/lint/unit/build verification, and reproduced the governed browser/visual/security boundary evidence: TAP `58/58 PASS`, Vitest `30/30 PASS`, inherited nonvisual browser regression `195/195 PASS`, exact API-02 production browser `12/12 PASS`, production fail-closed browser `6/6 PASS`, immutable FRONT-03 visual baseline `27/27 PASS`, C1 validator `14/14 PASS`, and C1 mutation resistance `9/9 DETECTED`. The run emitted `FRONT03_C1_ACCEPTANCE_RESULT:PASS:{candidate_sha}:{candidate_size}`. Authoritative evidence artifact `front03-c1-acceptance-evidence-{accept_run}`, artifact ID `{accept_artifact_id}`, GitHub artifact digest `{accept_artifact_digest}`. Exact lineage is accepted FRONT-02 C2.1 SHA-256 `{front02_sha}` + FRONT-03 PRESEAL SHA-256 `{preseal_sha}` + exact accepted API-02 C13 SHA-256 `{api02_sha}`; no real API-03 S2S dependency was discovered for the C1 browser-to-API-02 binding, so none was invented. Voting/BSI readiness evidence preserves the hard freeze against persistent member/person identity in the voting domain and introduces no unrecorded certification blocker; all BSI/CC claims remain expressly excluded. Governance decision is recorded in `docs/frontend/FRONT-03-C1-ACCEPTANCE-RECORD.json`. **FRONT-03 C1 is therefore `ACCEPTED / CLOSED` as a bounded WS-02 implementation stage.** This does not close the entire FRONT layer, does not alter the canonical primary program stage, and does not declare production readiness, legal activation, BSI/CC/EAL4 certification, or final security acceptance.\n'''
text = text.replace(insert_anchor, closure + insert_anchor, 1)

old_row = "| FRONT | `FRONT-02 C2.1 ACCEPTED_IMPLEMENTATION_BASELINE / NOT_STARTED_FINAL` | The exact C2.1 implementation candidate is accepted as a governed frontend baseline. Final integrated journeys and FRONT-layer closure remain dependent on API → INFRA → OPS → CTRL. |"
new_row = "| FRONT | `FRONT-02 C2.1 ACCEPTED_IMPLEMENTATION_BASELINE; FRONT-03 C1 ACCEPTED / CLOSED; NOT_STARTED_FINAL` | Exact FRONT-02 C2.1 and bounded FRONT-03 C1 are accepted governed frontend baselines. The overall FRONT layer remains open; final integrated journeys and FRONT-layer closure remain dependent on API → INFRA → OPS → CTRL. |"
if text.count(old_row) != 1:
    raise SystemExit("PCR FRONT row anchor not unique")
text = text.replace(old_row, new_row, 1)

PCR.write_text(text, encoding="utf-8")

# Fail closed on the core state facts we must preserve and the facts we add.
check = PCR.read_text(encoding="utf-8")
assert "API-03 is therefore `ACCEPTED / CLOSED`" in check
assert "API-04 = ACTIVE / IN DEVELOPMENT / NOT ACCEPTED" in check
assert "FRONT-03 C1 is therefore `ACCEPTED / CLOSED` as a bounded WS-02 implementation stage" in check
assert "The overall FRONT layer remains open" in check
assert candidate_sha in check
print("FRONT03_GOVERNANCE_APPLY:READY")
