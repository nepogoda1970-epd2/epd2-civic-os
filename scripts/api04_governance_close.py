from __future__ import annotations

import json
from pathlib import Path

REC = Path("docs/api/API-04/API04_C1_ACCEPTANCE_RECORD.json")
REG = Path("docs/roadmap/EPD2_PROGRAM_CONTROL_REGISTER.md")

rec = json.loads(REC.read_text())
assert rec["decision"] == "ACCEPTED_CLOSED"
assert rec["candidate"]["sha256"] == "8356ba6f1b0e254f9aa215b4873a1e38f44a47fdac2ac859ff62bd95db999337"
assert rec["authoritative"]["run_id"] == 33569092401
assert rec["authoritative"]["job_id"] == 100058880258
assert rec["authoritative"]["conclusion"] == "SUCCESS"
assert rec["authoritative"]["terminal_marker"] == "API04_RESULT:PASS:validation/api04/authoritative_acceptance_result.json"
assert rec["open_blockers"] == []
assert rec["next_permitted_primary_stage"] == "API-05"

s = REG.read_text()
original = s

old = "**Updated:** 2026-09-01  "
assert old in s
s = s.replace(old, "**Updated:** 2026-09-02  ", 1)

anchor = "**FRONT-03 authoritative acceptance and bounded stage closure (2026-09-01):**"
assert anchor in s
assert "API-04 authoritative acceptance and closure (2026-09-02)" not in s
closure = """**API-04 authoritative acceptance and closure (2026-09-02):** exact sealed candidate `EPD2_API04_EVENTS_AND_MESSAGING_RUNTIME_CANDIDATE_0.1_C1.zip`, SHA-256 `8356ba6f1b0e254f9aa215b4873a1e38f44a47fdac2ac859ff62bd95db999337`, size `43,880,523` bytes, passed the independent sealed GitHub Actions workflow `.github/workflows/api04-accept.yml`, authoritative run `33569092401`, job `100058880258`, provenance commit `299d4f4bce52daf14961e5d4cdb23c81ada05734`, conclusion `success`. The run emitted `API04_RESULT:PASS:validation/api04/authoritative_acceptance_result.json`; all `28/28` governed gates passed with no failed or environment-blocked gate. Exact live evidence includes `623/623` API-04 tests with `0` failed and `0` skipped, PostgreSQL `16.15`, RabbitMQ `3.12.1`, eight mTLS service principals, exact API-03 C5 predecessor binding, transactional outbox, durable inbox/deduplication, acknowledgement/crash/redelivery, schema compatibility, retry/DLQ/quarantine, replay/re-drive governance, asynchronous FIR-AUTH-001, voting isolation, API-chain non-regression, DATA no-new-regression, cross-service failure fixtures, mutation self-test and no API-05+ scope leakage all PASS. The independent runner also proved the exact C1 SHA/size, complete `SHA256SUMS` seal and byte-for-byte sealed acceptance workflow SHA-256 `3decc2dd0592800d7278ba83b3c6a88ed51177b78aa40b0966b62cac101e2bec`. Authoritative evidence artifact `api04-c1-authoritative-acceptance-33569092401`, artifact ID `9824542224`, GitHub artifact digest `sha256:0289b930353f74a7e263af3c55df24b0ebf8578e45238b6b56a2bfd90193109f`. The governance decision is recorded in `docs/api/API-04/API04_C1_ACCEPTANCE_RECORD.json`. **API-04 is therefore `ACCEPTED / CLOSED`.** The candidate's `CANDIDATE_NOT_ACCEPTED` self-state remains the intentional no-self-acceptance safeguard and is superseded only by the independent post-run governance decision. No open API-04 blocker remains. `API-05 = ACTIVE / IN DEVELOPMENT / NOT ACCEPTED` is now the next primary API stage. The API layer remains open until API-06; no production-readiness, legal-activation, final-security, BSI/CC or EAL4 certification claim follows from this transition.


"""
s = s.replace(anchor, closure + anchor, 1)

old = """DATA = CLOSED
API-01 = ACCEPTED / CLOSED
API-02 = ACCEPTED / CLOSED
API-03 = ACCEPTED / CLOSED
API-04 = ACTIVE / IN DEVELOPMENT / NOT ACCEPTED"""
new = """DATA = CLOSED
API-01 = ACCEPTED / CLOSED
API-02 = ACCEPTED / CLOSED
API-03 = ACCEPTED / CLOSED
API-04 = ACCEPTED / CLOSED
API-05 = ACTIVE / IN DEVELOPMENT / NOT ACCEPTED"""
assert old in s
s = s.replace(old, new, 1)

old = "While API-04 is the active primary API stage, the following may proceed without changing `API-04 = ACTIVE / IN DEVELOPMENT / NOT ACCEPTED`. API-03 is accepted/closed at exact C5 and is the governed predecessor for API-04:"
new = "While API-05 is the active primary API stage, the following may proceed without changing `API-05 = ACTIVE / IN DEVELOPMENT / NOT ACCEPTED`. API-04 is accepted/closed at exact C1 and is the governed predecessor for API-05:"
assert old in s
s = s.replace(old, new, 1)

old = "**Primary implementation:** `API-04 = ACTIVE / IN DEVELOPMENT / NOT ACCEPTED` (`API-01 = ACCEPTED / CLOSED`; `API-02 = ACCEPTED / CLOSED`; `API-03 = ACCEPTED / CLOSED`). API-04 must treat exact accepted API-03 C5 SHA-256 `5fb769cd387c7bcf10b9783d05fce44066985c7408a015cb4c670419ce316b55` as its governed predecessor baseline and requires its own seal and independent authoritative acceptance."
new = "**Primary implementation:** `API-05 = ACTIVE / IN DEVELOPMENT / NOT ACCEPTED` (`API-01 = ACCEPTED / CLOSED`; `API-02 = ACCEPTED / CLOSED`; `API-03 = ACCEPTED / CLOSED`; `API-04 = ACCEPTED / CLOSED`). API-05 must treat exact accepted API-04 C1 SHA-256 `8356ba6f1b0e254f9aa215b4873a1e38f44a47fdac2ac859ff62bd95db999337` as its governed predecessor baseline and requires its own seal and independent authoritative acceptance."
assert old in s
s = s.replace(old, new, 1)

old = "**Governed forward path:** complete API-04 against the exact accepted API-03 C5 predecessor, seal and independently verify API-04 before any API-04 acceptance/closure claim; then continue API-05 → API-06 with independent authoritative acceptance at each stage; close API only after API-06."
new = "**Governed forward path:** complete API-05 against the exact accepted API-04 C1 predecessor, seal and independently verify API-05 before any API-05 acceptance/closure claim; then continue API-06 with independent authoritative acceptance; close API only after API-06."
assert old in s
s = s.replace(old, new, 1)

s = s.replace(
    "does not alter `API-04 = ACTIVE / IN DEVELOPMENT / NOT ACCEPTED`.",
    "does not alter `API-05 = ACTIVE / IN DEVELOPMENT / NOT ACCEPTED`.",
    2,
)
s = s.replace(
    "API-04 is now the primary API stage; this FRONT work does not constitute FRONT acceptance or final closure.",
    "API-05 is now the primary API stage; this FRONT work does not constitute FRONT acceptance or final closure.",
    1,
)
s = s.replace(
    "Neither accepted PILOT stage changes the current API-04 primary position, claims production readiness/legal activation, or forces immediate INTEGRATION-01 advancement.",
    "Neither accepted PILOT stage changes the current API-05 primary position, claims production readiness/legal activation, or forces immediate INTEGRATION-01 advancement.",
    1,
)
s = s.replace(
    "The current primary implementation position is `API-04 = ACTIVE / IN DEVELOPMENT / NOT ACCEPTED`; API-03 is `ACCEPTED / CLOSED`;",
    "The current primary implementation position is `API-05 = ACTIVE / IN DEVELOPMENT / NOT ACCEPTED`; API-04 is `ACCEPTED / CLOSED`;",
    1,
)

assert s != original
sec3 = s.split("## 3. Parallel work currently permitted", 1)[1].split("## 4.", 1)[0]
sec9 = s.split("## 9. Immediate execution decision", 1)[1]
assert "API-04 = ACTIVE / IN DEVELOPMENT / NOT ACCEPTED" not in sec3
assert "**Primary implementation:** `API-04" not in sec9
REG.write_text(s)
print("API04_GOVERNANCE_PATCH:PASS")
