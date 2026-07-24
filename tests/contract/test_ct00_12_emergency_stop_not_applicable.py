"""CT-00-12 (Emergency Stop) - and CT-00-11 (AI Human Control)'s own
historical PACK-02/03/05 exclusion, kept here unchanged.

Per pack section 12.1: "CT-00-11 and CT-00-12 remain out of scope, but
must be explicitly marked as not applicable in PACK-02, not as passed."
PACK-03's own spec (`docs/handover/PACK-03-SPEC.md` section 1, "Scope")
carries the identical exclusion forward unchanged: "AI-processing and
Emergency remain out of scope for the same reason [as PACK-02] ... no
canon entity in this pack's scope requires `AIProcessingRecord` or
`EmergencyAction` to exist. CT-00-11 and CT-00-12 are therefore expected
[to stay not-applicable]." None of the six PACK-03 services
(initiative/deliberation/moderation/voting/tally/delegation) implement
either entity, so this file's exclusion is unchanged and unextended by
PACK-03 - it is simply still correct. PACK-05's own required scope
(item 13, "keep out of scope") names "AI-processing" and "Emergency/
Crisis Override" explicitly among the same items - the one PACK-05
service (governance-service) implements neither `AIProcessingRecord` nor
`EmergencyAction` either, so the exclusion carries forward unchanged a
second time.

PACK-06 (ai-processing-service, ADR-021 through ADR-025) changes exactly
one half of this: `AIProcessingRecord` (canon 17.1/19c) is now
implemented, so CT-00-11 becomes genuinely, fully applicable starting
this pack - required scope item 17 is explicit that CT-00-11 must move
to "fully and centrally" passing, not stay not-applicable. That test now
lives in its own dedicated file, `test_ct00_11_ai_human_control.py`,
which this file no longer covers (renamed from
`test_ct00_11_12_not_applicable.py`). `EmergencyAction` (canon 19.1)
remains out of scope for PACK-06 too (required scope item 19's explicit
"Emergency/Crisis Override" exclusion) - CT-00-12 therefore carries
forward not-applicable unchanged a third time, still skipped
(SKIPPED, never PASSED) with an explicit reason so a test-report reader
sees a clearly marked exclusion rather than a misleading green check:

- CT-00-12 (Emergency Stop): pack section 3.2 (PACK-02) / section 1
  (PACK-03) / required scope item 13 (PACK-05) / required scope item 19
  (PACK-06) explicitly excludes emergency actions from scope (no
  `EmergencyAction`, canon section 19.1, is implemented anywhere in any
  of the four packs). There is no freeze mechanism in any of them for a
  "forbidden operation during freeze" test to exercise.
"""

from __future__ import annotations

import pytest


@pytest.mark.skip(
    reason=(
        "CT-00-11 NOT APPLICABLE in PACK-02, PACK-03, or PACK-05 (superseded - "
        "see test_ct00_11_ai_human_control.py for PACK-06, where CT-00-11 is "
        "fully applicable): AIProcessingRecord (canon section 17.1) was out of "
        "scope for all three earlier packs (PACK-02 pack section 3.2; PACK-03 "
        "docs/handover/PACK-03-SPEC.md section 1; PACK-05 required scope "
        "item 13) - no AI-produced result existed in any of them for a "
        "human-control gate to apply to."
    )
)
def test_ct00_11_ai_human_control_not_applicable_in_earlier_packs() -> None:
    raise AssertionError("must not run - CT-00-11 was not applicable in PACK-02/PACK-03/PACK-05")


@pytest.mark.skip(
    reason=(
        "CT-00-12 NOT APPLICABLE in PACK-02, PACK-03, PACK-05, or PACK-06: "
        "EmergencyAction (canon section 19.1) is out of scope for all four "
        "packs (PACK-02 pack section 3.2; PACK-03 "
        "docs/handover/PACK-03-SPEC.md section 1; PACK-05 required scope "
        "item 13; PACK-06 required scope item 19's explicit Emergency/Crisis "
        "Override exclusion) - no freeze mechanism exists in any of them for "
        "a forbidden-operation-during-freeze test to exercise."
    )
)
def test_ct00_12_emergency_stop_not_applicable() -> None:
    raise AssertionError(
        "must not run - CT-00-12 is not applicable in PACK-02/PACK-03/PACK-05/PACK-06"
    )
