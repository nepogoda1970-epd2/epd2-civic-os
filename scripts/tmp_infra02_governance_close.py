from pathlib import Path
import json

p = Path("docs/roadmap/EPD2_PROGRAM_CONTROL_REGISTER.md")
s = p.read_text()

assert "INFRA02_AUTHORITATIVE_RESULT:PASS" not in s
assert "`INFRA-02 ACCEPTED / CLOSED`" not in s

marker = "**OPS-01 authoritative acceptance and bounded stage closure (2026-09-01):**"
assert marker in s
para = (
    "**INFRA-02 authoritative acceptance and bounded stage closure (2026-09-02):** exact sealed candidate "
    "`EPD2_INFRA02_CI_CD_AND_SOFTWARE_SUPPLY_CHAIN_CANDIDATE_0.1.zip`, SHA-256 "
    "`d91fa6db81126765c0e26bf285fff2f974464544b7fa6299b6d069a25d1ff72c`, size `15,980,332` bytes, "
    "passed independent exact-byte GitHub Actions authoritative review, run `33574647511`, job `100075828121`, conclusion `success`. "
    "Independent review proved exact transport identity, clean seal/freeze hygiene, exact accepted INFRA-01 C3 predecessor "
    "SHA-256 `5cd90da141056badc38ee3fb34f2d648002ace5b87c6a0cce1d331431364b131`, predecessor delta "
    "`35 added / 11 modified / 0 removed / 1450 unchanged`, governance freshness, `146/146` targeted tests, and full canonical harness "
    "`51/51 PASS`. Current-run evidence returned `INFRA01_EVIDENCE_RESULT:PASS`; submitted candidate and harness-produced package "
    "were independently bound by `INFRA02_PACKAGE_CONTENT_IDENTITY:PASS:1496`; terminal marker "
    "`INFRA02_AUTHORITATIVE_RESULT:PASS:d91fa6db81126765c0e26bf285fff2f974464544b7fa6299b6d069a25d1ff72c:15980332`. "
    "Post-run reconciliation against `main@4b95cc952897bd78fe912a2737f53e66264d6ff1` classified the concurrent API-05 PCR closure "
    "and formatting-only API-05 helper change as `NO_INFRA02_CONTROLLING_CONFLICT`; newer `API-05 ACCEPTED / CLOSED; API-06 NEXT` state is preserved. "
    "The governance decision is recorded in `docs/infra/INFRA-02/INFRA02_ACCEPTANCE_RECORD.json`. "
    "**INFRA-02 is therefore `ACCEPTED / CLOSED` as the bounded CI/CD & Software Supply-Chain Integrity stage.** "
    "The overall INFRA layer remains open; INFRA-03…INFRA-07 are not promoted. No production-readiness, hosting-provider, legal-activation, "
    "BSI/CC/EAL4 or final-security claim follows.\n\n"
)
s = s.replace(marker, para + marker, 1)

old_row = "| INFRA | `INFRA-01 ACCEPTED / CLOSED; INFRA LAYER OPEN` | Exact bounded INFRA-01 CI Acceptance Harness & Release-Integrity Foundation is accepted/closed at C3. The overall INFRA layer remains open; final INFRA closure still follows API dependencies. |"
new_row = "| INFRA | `INFRA-01 ACCEPTED / CLOSED; INFRA-02 ACCEPTED / CLOSED; INFRA LAYER OPEN` | Exact bounded INFRA-01 C3 and INFRA-02 software supply-chain foundation are accepted/closed. The overall INFRA layer remains open; INFRA-03…INFRA-07 and final INFRA closure remain governed separately and still follow API dependencies. |"
assert old_row in s
s = s.replace(old_row, new_row, 1)

section7 = "\n---\n\n## 7. Branch / reconciliation discipline"
assert section7 in s
transition = """
### INFRA-02 authoritative transition — 2026-09-02

- **Previous state:** `PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED` in the independently reviewed candidate line; no canonical INFRA-02 acceptance/closure had yet been recorded on `main`.
- **New state:** `INFRA-02 ACCEPTED / CLOSED`.
- **Governing candidate:** `EPD2_INFRA02_CI_CD_AND_SOFTWARE_SUPPLY_CHAIN_CANDIDATE_0.1.zip`.
- **Candidate SHA-256:** `d91fa6db81126765c0e26bf285fff2f974464544b7fa6299b6d069a25d1ff72c`.
- **Candidate size:** `15,980,332` bytes.
- **Accepted predecessor:** INFRA-01 C3 SHA-256 `5cd90da141056badc38ee3fb34f2d648002ace5b87c6a0cce1d331431364b131`.
- **Authoritative run:** `33574647511`, job `100075828121`, conclusion `success`.
- **Independent proof:** exact transport PASS; seal/freeze PASS; exact predecessor delta `35/11/0/1450`; targeted tests `146/146 PASS`; canonical harness `51/51 PASS`; current-run evidence `INFRA01_EVIDENCE_RESULT:PASS`; package member-content identity `1496/1496`; terminal `INFRA02_AUTHORITATIVE_RESULT:PASS`.
- **Authoritative evidence artifact:** `infra02-authoritative-evidence-33574647511`, ID `9826333069`, wrapper SHA-256 `4fada409e8fe58f861a0615e2606d5e26615e815b2da6126f430a583b045e5b1`.
- **Exact reviewed candidate artifact:** `infra02-authoritative-candidate-33574647511`, ID `9826333641`, wrapper SHA-256 `69bdcf1210f7ef371513f41d22d32bed42bf25ab81dd2aa5a244aca95ec17ab6`.
- **Post-run reconciliation:** freshness gate observed `main@b359c575b224727a9b69cabc1ea3f3bf63a2f64c`; before closure, `main` advanced to `4b95cc952897bd78fe912a2737f53e66264d6ff1`. Concurrent changes were the authoritative API-05 PCR closure and formatting-only API-05 governance helper. Classification `NO_INFRA02_CONTROLLING_CONFLICT`; API-05 closed/API-06 next state is preserved.
- **Acceptance decision:** `docs/infra/INFRA-02/INFRA02_ACCEPTANCE_RECORD.json`.
- **Open blockers for INFRA-02:** none.
- **Scope consequence:** bounded INFRA-02 closes at the exact candidate above; overall INFRA remains open and INFRA-03…INFRA-07 are not promoted. No production-readiness, legal-activation, BSI/CC/EAL4 or final-security claim follows.
- **Next permitted primary program stage:** unchanged — `API-06 = NEXT`.
"""
s = s.replace(section7, "\n" + transition + section7, 1)

front_marker = "**Parallel FRONT action:**"
assert front_marker in s
infra_action = (
    "**Parallel INFRA action:** bounded `INFRA-02 — CI/CD & Software Supply-Chain Integrity` is `ACCEPTED / CLOSED` at exact "
    "SHA-256 `d91fa6db81126765c0e26bf285fff2f974464544b7fa6299b6d069a25d1ff72c`, authoritative run `33574647511`. "
    "Its accepted build-once, SBOM/provenance, vulnerability/history-secret, promotion-by-digest, drift-detection and release-integrity foundation "
    "may be reused by later INFRA work. This does not close the overall INFRA layer, open or accept INFRA-03…INFRA-07, select a hosting provider, "
    "or change `API-06 = NEXT`.\n\n"
)
s = s.replace(front_marker, infra_action + front_marker, 1)

stale_primary = "**Primary implementation:** `API-06 = NEXT` (`API-01 = ACCEPTED / CLOSED`; `API-02 = ACCEPTED / CLOSED`; `API-03 = ACCEPTED / CLOSED`; `API-04 = ACCEPTED / CLOSED`). API-05 must treat exact accepted API-04 C1 SHA-256 `8356ba6f1b0e254f9aa215b4873a1e38f44a47fdac2ac859ff62bd95db999337` as its governed predecessor baseline and requires its own seal and independent authoritative acceptance."
current_primary = "**Primary implementation:** `API-06 = NEXT` (`API-01 = ACCEPTED / CLOSED`; `API-02 = ACCEPTED / CLOSED`; `API-03 = ACCEPTED / CLOSED`; `API-04 = ACCEPTED / CLOSED`; `API-05 = ACCEPTED / CLOSED`). API-06 is the next permitted primary API stage; it is not active or accepted until its governed stage work is opened and independently accepted."
assert stale_primary in s
s = s.replace(stale_primary, current_primary, 1)

stale_forward = "**Governed forward path:** complete API-05 against the exact accepted API-04 C1 predecessor, seal and independently verify API-05 before any API-05 acceptance/closure claim; then continue API-06 with independent authoritative acceptance; close API only after API-06."
current_forward = "**Governed forward path:** open and complete API-06 from the exact accepted API-05 C1 predecessor, seal and independently verify API-06, and close API only after API-06 authoritative acceptance."
assert stale_forward in s
s = s.replace(stale_forward, current_forward, 1)

stale_pilot = "Neither accepted PILOT stage changes the current API-05 primary position, claims production readiness/legal activation, or forces immediate INTEGRATION-01 advancement."
current_pilot = "Neither accepted PILOT stage changes `API-06 = NEXT`, claims production readiness/legal activation, or forces immediate INTEGRATION-01 advancement."
assert stale_pilot in s
s = s.replace(stale_pilot, current_pilot, 1)

p.write_text(s)

record = {
  "schema": "epd2.infra02.acceptance-record/1",
  "stage": "INFRA-02 — CI/CD & Software Supply-Chain Integrity",
  "decision": "ACCEPTED / CLOSED",
  "decision_date": "2026-09-02",
  "decision_authority": "Project Owner",
  "decision_basis": "Independent exact-byte authoritative GitHub acceptance plus post-run governance reconciliation.",
  "scope": {"bounded_stage": "INFRA-02", "overall_infra_layer": "OPEN", "primary_program_stage_unchanged": "API-06 NEXT"},
  "entering_canonical_main": {"repository": "nepogoda1970-epd2/epd2-civic-os", "branch": "main", "commit": "4b95cc952897bd78fe912a2737f53e66264d6ff1"},
  "candidate": {
    "filename": "EPD2_INFRA02_CI_CD_AND_SOFTWARE_SUPPLY_CHAIN_CANDIDATE_0.1.zip",
    "sha256": "d91fa6db81126765c0e26bf285fff2f974464544b7fa6299b6d069a25d1ff72c",
    "size_bytes": 15980332,
    "git_blob_sha1": "bc08c9d3b27cc580d7598b5b63b4c1bd37ded54d",
    "source_commit": "3e27fa7b427d252a4fcbe4d093139bd1bd14219f",
    "source_tree": "63a675e7cf9593ed623bf1aa926bd4876c453e8f",
    "freeze_tree_digest": "c169a2930ab50612076ab3f90468ff03f5ec19e2005c520765a4905e15c51f7d",
    "archive_member_count": 1496,
    "source_file_count": 1494,
    "candidate_self_acceptance": False
  },
  "predecessor": {
    "stage": "INFRA-01 C3",
    "filename": "EPD2_INFRA01_CI_ACCEPTANCE_HARNESS_CANDIDATE_0.1_C3.zip",
    "sha256": "5cd90da141056badc38ee3fb34f2d648002ace5b87c6a0cce1d331431364b131",
    "size_bytes": 15854311,
    "authoritative_candidate_artifact_id": 9819612258
  },
  "authoritative_review": {
    "workflow": "INFRA-02 Independent Authoritative Review",
    "run_id": 33574647511,
    "job_id": 100075828121,
    "conclusion": "success",
    "freshness_target_commit": "b359c575b224727a9b69cabc1ea3f3bf63a2f64c",
    "freshness_target_tree": "04891ced573661614a6e288a816dd71ce645d7ad",
    "exact_transport": "PASS",
    "seal_hygiene": "PASS",
    "predecessor_delta": {"added": 35, "modified": 11, "removed": 0, "unchanged": 1450},
    "targeted_tests": "146/146 PASS",
    "canonical_harness": "51/51 PASS; 0 FAIL; 0 BLOCKED",
    "evidence_verification": "INFRA01_EVIDENCE_RESULT:PASS",
    "package_content_identity": "INFRA02_PACKAGE_CONTENT_IDENTITY:PASS:1496",
    "terminal_marker": "INFRA02_AUTHORITATIVE_RESULT:PASS:d91fa6db81126765c0e26bf285fff2f974464544b7fa6299b6d069a25d1ff72c:15980332",
    "evidence_artifact": {"name": "infra02-authoritative-evidence-33574647511", "id": 9826333069, "wrapper_sha256": "4fada409e8fe58f861a0615e2606d5e26615e815b2da6126f430a583b045e5b1"},
    "candidate_artifact": {"name": "infra02-authoritative-candidate-33574647511", "id": 9826333641, "wrapper_sha256": "69bdcf1210f7ef371513f41d22d32bed42bf25ab81dd2aa5a244aca95ec17ab6"}
  },
  "post_run_reconciliation": {
    "authoritative_gate_main": "b359c575b224727a9b69cabc1ea3f3bf63a2f64c",
    "governance_decision_main": "4b95cc952897bd78fe912a2737f53e66264d6ff1",
    "concurrent_commits": ["2b840017e8cdabcb9af78e3ae25f79e7e75c73f8", "4b95cc952897bd78fe912a2737f53e66264d6ff1"],
    "changed_paths": ["docs/roadmap/EPD2_PROGRAM_CONTROL_REGISTER.md", "scripts/api05_governance_close.py"],
    "classification": "NO_INFRA02_CONTROLLING_CONFLICT",
    "disposition": "Preserve newer API-05 ACCEPTED/CLOSED and API-06 NEXT state; record INFRA-02 acceptance on top without resealing the accepted candidate."
  },
  "open_blockers": [],
  "exclusions": [
    "This decision closes only bounded INFRA-02; it does not close the overall INFRA layer.",
    "It does not accept or close INFRA-03 through INFRA-07.",
    "It does not close the API layer or change API-06 from NEXT.",
    "It does not select a hosting provider or establish production secrets/key custody.",
    "It is not a production-readiness or legal-activation decision.",
    "It is not BSI/Common-Criteria/EAL4 or final security certification."
  ]
}
out = Path("docs/infra/INFRA-02/INFRA02_ACCEPTANCE_RECORD.json")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n")
