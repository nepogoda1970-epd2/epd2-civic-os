"""CT-00-11 (AI Human Control) and CT-00-12 (Emergency Stop).

Per pack section 12.1: "CT-00-11 and CT-00-12 remain out of scope, but
must be explicitly marked as not applicable in PACK-02, not as passed."

Both are skipped here (SKIPPED, never PASSED) with an explicit reason, so
a test-report reader sees a clearly marked exclusion rather than a
misleading green check:

- CT-00-11 (AI Human Control): pack section 3.2 explicitly excludes AI
  processing from PACK-02's scope (no `AIProcessingRecord`, canon section
  17.1, is implemented). There is no AI-produced result in this pack for
  a human-confirmation gate to apply to.
- CT-00-12 (Emergency Stop): pack section 3.2 explicitly excludes
  emergency actions from PACK-02's scope (no `EmergencyAction`, canon
  section 19.1, is implemented). There is no freeze mechanism in this
  pack for a "forbidden operation during freeze" test to exercise.
"""

from __future__ import annotations

import pytest


@pytest.mark.skip(
    reason=(
        "CT-00-11 NOT APPLICABLE in PACK-02: AIProcessingRecord (canon "
        "section 17.1) is out of scope (pack section 3.2) - no AI-produced "
        "result exists for a human-control gate to apply to."
    )
)
def test_ct00_11_ai_human_control_not_applicable() -> None:
    raise AssertionError("must not run - CT-00-11 is not applicable in PACK-02")


@pytest.mark.skip(
    reason=(
        "CT-00-12 NOT APPLICABLE in PACK-02: EmergencyAction (canon section "
        "19.1) is out of scope (pack section 3.2) - no freeze mechanism "
        "exists for a forbidden-operation-during-freeze test to exercise."
    )
)
def test_ct00_12_emergency_stop_not_applicable() -> None:
    raise AssertionError("must not run - CT-00-12 is not applicable in PACK-02")
