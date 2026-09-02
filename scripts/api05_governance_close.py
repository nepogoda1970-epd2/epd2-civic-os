from __future__ import annotations

import json
from pathlib import Path

REC = Path("docs/api/API-05/API05_C1_ACCEPTANCE_RECORD.json")
REG = Path("docs/roadmap/EPD2_PROGRAM_CONTROL_REGISTER.md")

rec = json.loads(REC.read_text())
assert rec["decision"] == "ACCEPTED_CLOSED"
assert (
    rec["candidate"]["sha256"] == "38bab7663b54f9f81538666315ee16195b0aa086e5b5c50c2b87acc3f4f03a70"
)
assert rec["candidate"]["size_bytes"] == 43953160
assert rec["authoritative"]["run_id"] == 33574342011
assert rec["authoritative"]["job_id"] == 100074902089
assert rec["authoritative"]["conclusion"] == "SUCCESS"
assert rec["authoritative"]["governed_gates_total"] == 8
assert rec["authoritative"]["failed_gates"] == 0
assert rec["authoritative"]["environment_blocked_gates"] == 0
assert (
    rec["authoritative"]["terminal_marker"]
    == "API05_RESULT:PASS:validation/api05/authoritative_acceptance_result.json"
)
assert rec["open_blockers"] == []
assert rec["next_permitted_primary_stage"] == "API-06"
assert rec["next_stage_state"] == "NEXT"

s = REG.read_text()
original = s

# Add one authoritative, post-run closure record without rewriting historical round records.
anchor = "**FRONT-03 authoritative acceptance and bounded stage closure (2026-09-01):**"
assert anchor in s
assert "**API-05 authoritative acceptance and closure (2026-09-02):**" not in s
closure = """**API-05 authoritative acceptance and closure (2026-09-02):** exact sealed candidate `EPD2_API05_EXTERNAL_INTEGRATION_BOUNDARY_CANDIDATE_0.1_C1.zip`, SHA-256 `38bab7663b54f9f81538666315ee16195b0aa086e5b5c50c2b87acc3f4f03a70`, size `43,953,160` bytes, passed the independent sealed GitHub Actions workflow `.github/workflows/api05-accept.yml`, authoritative run `33574342011`, job `100074902089`, provenance commit `23fb2c034959cc74a006df89d377c5669e2e0398`, conclusion `success`. The run emitted `API05_RESULT:PASS:validation/api05/authoritative_acceptance_result.json`; all `8/8` governed gates passed with no failed or environment-blocked gate. Exact live evidence includes `66/66` API-05 behavioral tests with `0` failed, PostgreSQL `16.15` (`server_version_num=160015`) with the PostgreSQL gate passing, locked dependency provisioning, Ruff check/format, clean archive hygiene, exact accepted API-04 C1 predecessor binding with `4,237` predecessor files verified unchanged, complete `SHA256SUMS` seal and byte-for-byte equality of the installed acceptance workflow with sealed workflow SHA-256 `6b2fba5dba895594ac246547ace3b62074b9a80f3c76b3fc3e4a88da8173e106`. The accepted C1 contains the independently hardened external-integration boundary for pinned DNS-to-connection dispatch, query-bound endpoint allowlisting, recursive identifier isolation, semantic validation before replay reservation, idempotent callback publication recovery, retry-time reauthorization and predecessor dependency-version preservation. Authoritative evidence artifact `api05-c1-authoritative-acceptance-33574342011`, artifact ID `9826088503`, GitHub artifact digest `sha256:251f429765b86687a3064fa6a7b45bac7b8cca8dfbb11c5aca79c0fec868ec78`. The governance decision is recorded in `docs/api/API-05/API05_C1_ACCEPTANCE_RECORD.json`. **API-05 is therefore `ACCEPTED / CLOSED`.** The candidate's `CANDIDATE_NOT_ACCEPTED` self-state remains the intentional no-self-acceptance safeguard and is superseded only by the independent post-run governance decision. No open API-05 blocker remains. `API-06 = NEXT`; it is not marked active because no canonical API-06 stage/handoff is present on `main` at this transition. The API layer remains open until API-06 receives its own authoritative acceptance; no production-readiness, legal-activation, final-security, BSI/CC or EAL4 certification claim follows from this transition.


"""
s = s.replace(anchor, closure + anchor, 1)

# Canonical current-state block.
old = """DATA = CLOSED
API-01 = ACCEPTED / CLOSED
API-02 = ACCEPTED / CLOSED
API-03 = ACCEPTED / CLOSED
API-04 = ACCEPTED / CLOSED
API-05 = ACTIVE / IN DEVELOPMENT / NOT ACCEPTED"""
new = """DATA = CLOSED
API-01 = ACCEPTED / CLOSED
API-02 = ACCEPTED / CLOSED
API-03 = ACCEPTED / CLOSED
API-04 = ACCEPTED / CLOSED
API-05 = ACCEPTED / CLOSED
API-06 = NEXT"""
assert old in s
s = s.replace(old, new, 1)

# Current parallel-work rule only; historical statements are preserved.
old = "While API-05 is the active primary API stage, the following may proceed without changing `API-05 = ACTIVE / IN DEVELOPMENT / NOT ACCEPTED`. API-04 is accepted/closed at exact C1 and is the governed predecessor for API-05:"
new = "While `API-06 = NEXT`, the following parallel work may proceed without treating API-06 as active or accepted. API-05 is accepted/closed at exact C1 and is the governed predecessor for API-06:"
assert old in s
s = s.replace(old, new, 1)

# Refresh the current program-layer summary if it still carries the pre-closure API row.
old = "| API | `API-01 ACCEPTED / CLOSED; API-02 ACCEPTED / CLOSED; API-03 ACCEPTED / CLOSED; API-04 ACTIVE / IN DEVELOPMENT / NOT ACCEPTED` | API-04 is the active primary API stage. API-03 is closed at exact accepted C5. API remains open through API-06. |"
new = "| API | `API-01 ACCEPTED / CLOSED; API-02 ACCEPTED / CLOSED; API-03 ACCEPTED / CLOSED; API-04 ACCEPTED / CLOSED; API-05 ACCEPTED / CLOSED; API-06 NEXT` | API-05 is closed at exact accepted C1. API-06 is the next permitted primary stage but is not active until its governed stage work is opened. API remains open through API-06. |"
if old in s:
    s = s.replace(old, new, 1)

# Refresh the checkpoint sequence when present, without touching dated historical prose.
old = """  → API-03 CLOSED
  → API-04 ACTIVE
  → API-05
  → API-06
  → API CLOSED"""
new = """  → API-03 CLOSED
  → API-04 CLOSED
  → API-05 CLOSED
  → API-06 NEXT
  → API CLOSED"""
if old in s:
    s = s.replace(old, new, 1)

# Current immediate-execution section: no unearned ACTIVE state for API-06.
if "## 9. Immediate execution decision" in s:
    head, sec9 = s.split("## 9. Immediate execution decision", 1)
    sec9 = sec9.replace(
        "`API-05 = ACTIVE / IN DEVELOPMENT / NOT ACCEPTED`",
        "`API-06 = NEXT`",
    )
    sec9 = sec9.replace(
        "API-05 is now the primary API stage",
        "API-06 is now the next permitted primary API stage",
    )
    sec9 = sec9.replace(
        "API-05 is the active primary API stage",
        "API-06 is the next permitted primary API stage",
    )
    s = head + "## 9. Immediate execution decision" + sec9

assert s != original
assert "**API-05 authoritative acceptance and closure (2026-09-02):**" in s
# The authoritative current-state block must be unambiguous.
state_block = s.split("DATA = CLOSED", 1)[1].split("```", 1)[0]
assert "API-05 = ACCEPTED / CLOSED" in state_block
assert "API-06 = NEXT" in state_block
assert "API-05 = ACTIVE / IN DEVELOPMENT / NOT ACCEPTED" not in state_block
REG.write_text(s)
print("API05_GOVERNANCE_PATCH:PASS")
