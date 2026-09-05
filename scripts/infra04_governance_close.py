from __future__ import annotations

import json
from pathlib import Path

REG = Path("docs/roadmap/EPD2_PROGRAM_CONTROL_REGISTER.md")
REC = Path("docs/infra/INFRA-04/INFRA04_C2_ACCEPTANCE_RECORD.json")

record = {
    "schema": "epd2.infra04.acceptance-record/1",
    "stage": "INFRA-04 — Resilience, Recovery & INFRA Closure Readiness",
    "decision": "ACCEPTED / CLOSED",
    "decision_date": "2026-09-05",
    "decision_authority": "Project Owner",
    "decision_basis": "Independent exact-byte authoritative GitHub acceptance plus this separate post-run governance decision.",
    "scope": {
        "bounded_stage": "INFRA-04",
        "overall_infra_layer": "OPEN / NOT CLOSED",
        "system_trial_preview": "NOT_OPENED_BY_THIS_DECISION",
        "production_readiness": "NOT_CLAIMED",
    },
    "entering_canonical_main": {
        "repository": "nepogoda1970-epd2/epd2-civic-os",
        "branch": "main",
        "commit": "7544f5dc3bf40304ae81b4d8ef476cc8ecb60ec5",
        "tree": "64447ec51a0f8e2cb4bbf8819ecafafd760c37fd",
    },
    "candidate_source": {
        "branch": "candidate/infra04-c2-canonical",
        "head_sha": "215e4a900217e33b1d73060a209ecdb2733384a8",
        "head_message": "fix(infra04): bind frontend prettier gate to npm workspaces",
    },
    "candidate": {
        "filename": "EPD2_INFRA04_RESILIENCE_RECOVERY_AND_INFRA_CLOSURE_READINESS_CANDIDATE_0.1_C2.zip",
        "sha256": "dd0fc5c68debe77fc9383a91e0bca23ce58600432511cf88a960fa30e397448b",
        "size_bytes": 31687576,
        "self_acceptance": False,
        "self_state": "CANDIDATE_NOT_ACCEPTED",
        "archive_seal": "INFRA04_C2_ARCHIVE_SEAL:PASS:2182",
    },
    "accepted_predecessor": {
        "stage": "INFRA-02",
        "filename": "EPD2_INFRA02_CI_CD_AND_SOFTWARE_SUPPLY_CHAIN_CANDIDATE_0.1.zip",
        "sha256": "d91fa6db81126765c0e26bf285fff2f974464544b7fa6299b6d069a25d1ff72c",
        "size_bytes": 15980332,
    },
    "authoritative": {
        "workflow": "INFRA-04 C2 Canonical Acceptance",
        "workflow_file": ".github/workflows/infra04-c2-authoritative.yml",
        "run_id": 33964098703,
        "run_attempt": 1,
        "head_branch": "candidate/infra04-c2-canonical",
        "head_sha": "215e4a900217e33b1d73060a209ecdb2733384a8",
        "conclusion": "success",
        "build_job_id": 101300988160,
        "authoritative_review_job_id": 101302429894,
        "runtime_gates_passed": 53,
        "runtime_gates_total": 53,
        "runtime_gates_failed": 0,
        "runtime_gates_blocked": 0,
        "drills_passed": 18,
        "drills_total": 18,
        "mutation_classes_detected": 48,
        "mutation_classes_total": 48,
        "targeted_tests_passed": 117,
        "inherited_infra_regression_tests_passed": 219,
        "full_pytest": "6194 passed, 4 skipped, 0 failed",
        "frontend_browser_replay": "267 passed",
        "front03_production_browser_replay": "18 passed",
        "postgresql": "16.15",
        "terminal_marker": "INFRA04_C2_AUTHORITATIVE_RESULT:PASS:dd0fc5c68debe77fc9383a91e0bca23ce58600432511cf88a960fa30e397448b:31687576",
    },
    "artifacts": {
        "exact_candidate": {
            "name": "infra04-c2-exact-candidate-33964098703",
            "id": 9969015727,
            "digest": "sha256:6885565313a27bb824804755a00236706c1aea7c08ec1fafc9e37eca1fc0ceaa",
        },
        "build_evidence": {
            "name": "infra04-c2-build-evidence-33964098703",
            "id": 9969015887,
            "digest": "sha256:9f566d34a9fa3588467d5680100d7c44dfa770f88f50d660810d8df15f430469",
        },
        "authoritative_evidence": {
            "name": "infra04-c2-authoritative-evidence-33964098703",
            "id": 9969099450,
            "digest": "sha256:990f5cedff58bef21a7e8308ca1d32c122cdd26200443f4ceea54b03514ff994",
        },
    },
    "open_blockers": [],
    "next_required_work": [
        "FIND-ST01-04 governed acceptance path for SEC-PREVIEW-01/G27 dependency where applicable",
        "INFRA-05 / PRQ-17 observability proof",
        "INFRA-06 / PRQ-19 trusted-time proof",
        "SEC-PREVIEW-01 / PRQ-18 identity/auth/member-runtime preview proof",
        "PRQ-20 separate System Trial Preview checkpoint-opening governance",
    ],
    "nonclaims": [
        "overall INFRA layer closure",
        "System Trial Preview opening",
        "production readiness",
        "legal activation",
        "final security acceptance",
        "BSI/Common Criteria/EAL4 certification",
        "hosting-provider selection",
    ],
}


def replace_once(text: str, old: str, new: str) -> str:
    assert old in text, f"missing expected PCR text: {old[:120]!r}"
    return text.replace(old, new, 1)


REC.parent.mkdir(parents=True, exist_ok=True)
REC.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n")

s = REG.read_text()
original = s
assert "INFRA-04 C2 authoritative acceptance and bounded stage closure" not in s
assert "docs/infra/INFRA-04/INFRA04_C2_ACCEPTANCE_RECORD.json" not in s

s = replace_once(s, "**Updated:** 2026-09-04", "**Updated:** 2026-09-05")

closure = """**INFRA-04 C2 authoritative acceptance and bounded stage closure (2026-09-05):** exact sealed candidate `EPD2_INFRA04_RESILIENCE_RECOVERY_AND_INFRA_CLOSURE_READINESS_CANDIDATE_0.1_C2.zip`, SHA-256 `dd0fc5c68debe77fc9383a91e0bca23ce58600432511cf88a960fa30e397448b`, size `31,687,576` bytes, passed independent exact-byte GitHub Actions review in `.github/workflows/infra04-c2-authoritative.yml`, authoritative run `33964098703`, build job `101300988160`, independent authoritative-review job `101302429894`, reviewed head `215e4a900217e33b1d73060a209ecdb2733384a8`, conclusion `success`. The build and independent review verified exact candidate identity, safe archive extraction, complete internal SHA-256 seal, current canonical-main freshness against `main@7544f5dc3bf40304ae81b4d8ef476cc8ecb60ec5`, exact accepted INFRA-02 predecessor binding, locked dependencies, PostgreSQL `16.15`, runtime recovery semantics, dependency outage/recovery, backup/restore refusal and valid restore, bounded rollback, drift detection, trust/JWKS refusal, audit/evidence continuity, voting isolation and no persistent member/person identifier in the voting domain. Independent evidence includes `53/53` runtime-phase gates PASS, `18/18` drills PASS, `48/48` mutation classes detected, `117` targeted INFRA-04 tests PASS, `219` inherited INFRA regression tests PASS, full repository replay `6194 passed, 4 skipped, 0 failed`, browser replay `267 passed`, and production-like FRONT-03 replay `18 passed`. Terminal marker: `INFRA04_C2_AUTHORITATIVE_RESULT:PASS:dd0fc5c68debe77fc9383a91e0bca23ce58600432511cf88a960fa30e397448b:31687576`. Exact candidate artifact `infra04-c2-exact-candidate-33964098703`, artifact ID `9969015727`, digest `sha256:6885565313a27bb824804755a00236706c1aea7c08ec1fafc9e37eca1fc0ceaa`; build evidence artifact ID `9969015887`, digest `sha256:9f566d34a9fa3588467d5680100d7c44dfa770f88f50d660810d8df15f430469`; authoritative evidence artifact ID `9969099450`, digest `sha256:990f5cedff58bef21a7e8308ca1d32c122cdd26200443f4ceea54b03514ff994`. The sealed candidate correctly retained `CANDIDATE_NOT_ACCEPTED`; that no-self-acceptance state is superseded only for this bounded module by `docs/infra/INFRA-04/INFRA04_C2_ACCEPTANCE_RECORD.json`. **INFRA-04 C2 is therefore `ACCEPTED / CLOSED` as the bounded Resilience, Recovery & INFRA Closure Readiness stage.** The overall INFRA layer remains **OPEN / NOT CLOSED**; INFRA-05, INFRA-06, INFRA-07, remaining preview prerequisites and final INFRA closure remain separately governed. This acceptance does not open System Trial Preview, does not prove PRQ-17/PRQ-18/PRQ-19/PRQ-20, and makes no production-readiness, legal-activation, final-security, hosting-provider-selection or BSI/Common Criteria/EAL4 certification claim.

"""
s = replace_once(s, "## 2. Program phase state", closure + "## 2. Program phase state")

old_infra_row = "| INFRA | `INFRA-01 ACCEPTED / CLOSED; INFRA-02 ACCEPTED / CLOSED; INFRA-03 ACCEPTED / CLOSED; INFRA LAYER OPEN` | Exact bounded INFRA-01 C3, INFRA-02 and INFRA-03 C1 are accepted/closed. INFRA-03 exact C1 is independently accepted by run `33742902782`, SHA-256 `6b49e02dbf38f9672c02c2540af051e3684cb4278b4330e91909e454f379d3c1`. The overall INFRA layer remains open; INFRA-04…INFRA-07 and final INFRA closure remain governed separately. |"
new_infra_row = "| INFRA | `INFRA-01 ACCEPTED / CLOSED; INFRA-02 ACCEPTED / CLOSED; INFRA-03 ACCEPTED / CLOSED; INFRA-04 ACCEPTED / CLOSED; INFRA LAYER OPEN` | Exact bounded INFRA-01 C3, INFRA-02, INFRA-03 C1 and INFRA-04 C2 are accepted/closed. INFRA-04 exact C2 is independently accepted by run `33964098703`, SHA-256 `dd0fc5c68debe77fc9383a91e0bca23ce58600432511cf88a960fa30e397448b`. The overall INFRA layer remains open; INFRA-05…INFRA-07, remaining preview prerequisites and final INFRA closure remain governed separately. |"
s = replace_once(s, old_infra_row, new_infra_row)

old_ops_row = "| OPS | `OPS-01 ACCEPTED / CLOSED; OPS-02 ACCEPTED / CLOSED; OPS-03 ACCEPTED / CLOSED; OPS LAYER OPEN` | Exact bounded OPS-01 C2, OPS-02 C3 and OPS-03 C3 are accepted/closed. OPS-03 independently passed 50/50 governed gates and evidences 15/15 OPS-owned preview-minimum prerequisites. The overall OPS layer remains open; later OPS stages/final OPS closure remain governed separately. System Trial Preview is NOT OPENED and still requires the current INFRA-side minimum plus a separate explicit governed checkpoint-opening decision. |"
new_ops_row = "| OPS | `OPS-01 ACCEPTED / CLOSED; OPS-02 ACCEPTED / CLOSED; OPS-03 ACCEPTED / CLOSED; OPS LAYER OPEN` | Exact bounded OPS-01 C2, OPS-02 C3 and OPS-03 C3 are accepted/closed. OPS-03 independently passed 50/50 governed gates and evidences 15/15 OPS-owned preview-minimum prerequisites. The overall OPS layer remains open; later OPS stages/final OPS closure remain governed separately. System Trial Preview is NOT OPENED and still requires remaining PRQ-17/PRQ-18/PRQ-19 evidence plus a separate PRQ-20 governed checkpoint-opening decision. |"
s = replace_once(s, old_ops_row, new_ops_row)

old_position = """INFRA-01 = ACCEPTED / CLOSED
INFRA-02 = ACCEPTED / CLOSED
INFRA-03 = ACCEPTED / CLOSED
INFRA = OPEN / NOT CLOSED"""
new_position = """INFRA-01 = ACCEPTED / CLOSED
INFRA-02 = ACCEPTED / CLOSED
INFRA-03 = ACCEPTED / CLOSED
INFRA-04 = ACCEPTED / CLOSED
INFRA = OPEN / NOT CLOSED"""
s = replace_once(s, old_position, new_position)

old_next = "NEXT CHECKPOINT = INFRA/OPS PREVIEW-READINESS MINIMUM"
new_next = "NEXT CHECKPOINT = PRQ-17 / PRQ-18 / PRQ-19 / PRQ-20 SYSTEM TRIAL PREVIEW PREREQUISITES"
s = replace_once(s, old_next, new_next)

old_path = """  → INFRA/OPS PREVIEW-READINESS MINIMUM
  → SYSTEM TRIAL PREVIEW — FIRST END-TO-END PROBNIK"""
new_path = """  → INFRA/OPS PREVIEW-READINESS MINIMUM (INFRA-04 C2 + OPS-03 C3 accepted)
  → PRQ-17 / PRQ-18 / PRQ-19 PREVIEW PREREQUISITES
  → PRQ-20 GOVERNANCE CHECKPOINT
  → SYSTEM TRIAL PREVIEW — FIRST END-TO-END PROBNIK"""
s = replace_once(s, old_path, new_path)

old_parallel = "With `API = CLOSED`, parallel work may continue while the explicit INFRA/OPS preview-readiness minimum is qualified. API-06 is accepted/closed at exact C1; no parallel line may treat API closure as automatic INFRA/OPS/CTRL/FRONT closure or as System Trial Preview opening:"
new_parallel = "With `API = CLOSED` and the bounded INFRA-04/OPS-03 preview-readiness minimum accepted, parallel work may continue while the remaining System Trial Preview prerequisites are qualified. No parallel line may treat API closure, INFRA-04 acceptance or OPS-03 acceptance as automatic INFRA/OPS/CTRL/FRONT closure or as System Trial Preview opening:"
s = replace_once(s, old_parallel, new_parallel)

old_primary = "**Primary implementation:** `API = CLOSED` through exact independently accepted `API-06 C1`. The current governed checkpoint is `INFRA/OPS PREVIEW-READINESS MINIMUM`; OPS-03 qualification may now bind the exact accepted API-06 runtime."
new_primary = "**Primary implementation:** `API = CLOSED` through exact independently accepted `API-06 C1`; bounded `INFRA-04 C2` and `OPS-03 C3` are now `ACCEPTED / CLOSED` as the preview-readiness minimum. The current governed checkpoint is the remaining System Trial Preview prerequisite chain: `FIND-ST01-04`, `PRQ-17`, `PRQ-18`, `PRQ-19`, then separate `PRQ-20` checkpoint-opening governance."
s = replace_once(s, old_primary, new_primary)

old_forward = "**Governed forward path:** qualify the explicit INFRA/OPS preview-readiness minimum against the exact accepted API runtime and then, only by a separate checkpoint-opening decision, open `SYSTEM TRIAL PREVIEW — FIRST END-TO-END PROBNIK`. The preview is an early usable-system checkpoint only and cannot close INFRA or OPS. After preview findings are handled through owning-layer lineage, complete INFRA → OPS → CTRL → FRONT, establish `FINAL INTEGRATION`, and run final SEC against that exact integrated baseline before the final readiness decision."
new_forward = "**Governed forward path:** after accepted INFRA-04/OPS-03 preview-readiness minimum, complete the remaining governed prerequisites: FIND-ST01-04 where required for SEC-PREVIEW-01/G27, INFRA-05/PRQ-17 observability, INFRA-06/PRQ-19 trusted time, SEC-PREVIEW-01/PRQ-18 identity/auth/member-runtime preview proof, and then, only by separate PRQ-20 checkpoint-opening governance, open `SYSTEM TRIAL PREVIEW — FIRST END-TO-END PROBNIK`. The preview is an early usable-system checkpoint only and cannot close INFRA or OPS. After preview findings are handled through owning-layer lineage, complete INFRA → OPS → CTRL → FRONT, establish `FINAL INTEGRATION`, and run final SEC against that exact integrated baseline before the final readiness decision."
s = replace_once(s, old_forward, new_forward)

old_infra_action = "**Parallel INFRA action:** bounded `INFRA-01`, `INFRA-02` and `INFRA-03` are `ACCEPTED / CLOSED`. INFRA-02 remains accepted at SHA-256 `d91fa6db81126765c0e26bf285fff2f974464544b7fa6299b6d069a25d1ff72c`, run `33574647511`; INFRA-03 C1 is accepted at SHA-256 `6b49e02dbf38f9672c02c2540af051e3684cb4278b4330e91909e454f379d3c1`, run `33742902782`. Their accepted supply-chain and deployment/runtime foundations may be reused by later INFRA work. This does not close the overall INFRA layer, open or accept INFRA-04…INFRA-07, or select a hosting provider. API is closed; INFRA remains separately governed."
new_infra_action = "**Parallel INFRA action:** bounded `INFRA-01`, `INFRA-02`, `INFRA-03` and `INFRA-04` are `ACCEPTED / CLOSED`. INFRA-02 remains accepted at SHA-256 `d91fa6db81126765c0e26bf285fff2f974464544b7fa6299b6d069a25d1ff72c`, run `33574647511`; INFRA-03 C1 is accepted at SHA-256 `6b49e02dbf38f9672c02c2540af051e3684cb4278b4330e91909e454f379d3c1`, run `33742902782`; INFRA-04 C2 is accepted at SHA-256 `dd0fc5c68debe77fc9383a91e0bca23ce58600432511cf88a960fa30e397448b`, run `33964098703`. Their accepted supply-chain, deployment/runtime and resilience/recovery foundations may be reused by later INFRA work. This does not close the overall INFRA layer, open or accept INFRA-05…INFRA-07, prove PRQ-17/PRQ-18/PRQ-19/PRQ-20, open System Trial Preview, or select a hosting provider. API is closed; INFRA remains separately governed."
s = replace_once(s, old_infra_action, new_infra_action)

old_mobile_tail = "The current primary implementation position is `API-06 = NEXT`; API-04 is `ACCEPTED / CLOSED`; FRONT-MOBILE-02 is not started, FRONT is not closed, and no mobile/production/security readiness is claimed."
new_mobile_tail = "The current primary implementation position is the remaining System Trial Preview prerequisite chain after API closure and accepted INFRA-04/OPS-03 preview-readiness minimum; FRONT-MOBILE-02 is not started, FRONT is not closed, and no mobile/production/security readiness is claimed."
s = replace_once(s, old_mobile_tail, new_mobile_tail)

assert s != original
assert "INFRA-04 C2 is therefore `ACCEPTED / CLOSED`" in s
assert "INFRA-04 = ACCEPTED / CLOSED" in s
assert "System Trial Preview is NOT OPENED" in s
assert "PRQ-20" in s
REG.write_text(s)
print("INFRA04_GOVERNANCE_PATCH:PASS")
