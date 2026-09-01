"""CT-00-12 (Emergency Stop) - and CT-00-11 (AI Human Control)'s own
historical PACK-02/03/05/07 exclusion, kept here unchanged.

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

PACK-07 (eligibility-service extensions, membership-service, canon-0.6.0
ADR-026 through ADR-031) implements neither `AIProcessingRecord` nor
`EmergencyAction` either - required scope item 19 explicitly defers "new
AI processing functionality", and no `EmergencyAction`-shaped entity
(canon 19.1) appears anywhere in this pack's 22-point scope - so both
CT-00-11 and CT-00-12 carry forward not-applicable unchanged a fourth
time. This is a genuinely different concept from PACK-07's own canon
19d.16 hard human-control invariant (no automated process may finally
decide membership rejection/suspension/expulsion/incompatibility/denial
of fundamental rights/restoration denial - see
`services/membership-service/tests/test_application.py`'s
`test_stage_a_always_transitions_to_human_decision_pending_regardless_of_recommendation`
and `test_activate_membership_is_the_only_path_to_active_status`, and
`services/eligibility-service/`'s own four-gate critical-policy
activation tests) - that invariant is about a *human's* decision
authority over a *membership/policy* outcome, never about an *AI*'s
output requiring human confirmation (CT-00-11's specific canonical
meaning) or about a system-wide *emergency freeze* mechanism (CT-00-12's
specific canonical meaning). PACK-07's own human-control invariant is
exercised directly in the service-level test suites named above, not
here.

- CT-00-12 (Emergency Stop): pack section 3.2 (PACK-02) / section 1
  (PACK-03) / required scope item 13 (PACK-05) / required scope item 19
  (PACK-06) / required scope item 19 (PACK-07) explicitly excludes
  emergency actions from scope (no `EmergencyAction`, canon section 19.1,
  is implemented anywhere in any of the five packs). There is no freeze
  mechanism in any of them for a "forbidden operation during freeze" test
  to exercise.
"""

from __future__ import annotations

import pytest


@pytest.mark.skip(
    reason=(
        "CT-00-11 NOT APPLICABLE in PACK-02, PACK-03, PACK-05, or PACK-07 "
        "(superseded - see test_ct00_11_ai_human_control.py for PACK-06, "
        "where CT-00-11 is fully applicable): AIProcessingRecord (canon "
        "section 17.1) was out of scope for all four of these packs (PACK-02 "
        "pack section 3.2; PACK-03 docs/handover/PACK-03-SPEC.md section 1; "
        "PACK-05 required scope item 13; PACK-07 required scope item 19) - no "
        "AI-produced result existed in any of them for a human-control gate "
        "to apply to. PACK-07's own canon 19d.16 human-control invariant "
        "(membership/critical-policy decisions requiring an authorized human "
        "decision-maker) is a distinct concept, exercised in "
        "services/membership-service's and services/eligibility-service's "
        "own test suites, not by this CT-00-11 gate."
    )
)
def test_ct00_11_ai_human_control_not_applicable_in_earlier_packs() -> None:
    raise AssertionError(
        "must not run - CT-00-11 was not applicable in PACK-02/PACK-03/PACK-05/PACK-07"
    )


@pytest.mark.skip(
    reason=(
        "CT-00-12 NOT APPLICABLE in PACK-02, PACK-03, PACK-05, PACK-06, or "
        "PACK-07: EmergencyAction (canon section 19.1) is out of scope for "
        "all five packs (PACK-02 pack section 3.2; PACK-03 "
        "docs/handover/PACK-03-SPEC.md section 1; PACK-05 required scope "
        "item 13; PACK-06 required scope item 19's explicit Emergency/Crisis "
        "Override exclusion; PACK-07 required scope item 19's identical "
        "exclusion) - no freeze mechanism exists in any of them for a "
        "forbidden-operation-during-freeze test to exercise."
    )
)
def test_ct00_12_emergency_stop_not_applicable() -> None:
    raise AssertionError(
        "must not run - CT-00-12 is not applicable in PACK-02/PACK-03/PACK-05/PACK-06/PACK-07"
    )
