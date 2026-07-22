"""CT-00-10 Rule Freeze (canon section 27): once a `Ballot` opens, its
configuration cannot change.

`Ballot` itself is out of PACK-02's scope (pack section 3.2 - voting is a
future pack). What PACK-02 owns and must freeze the same way is
`EligibilityRule` (canon section 9.1): once a `(eligibility_rule_id,
rule_version)` pair is created, its content is immutable - the same
"freeze after commitment" invariant CT-00-10 tests for `Ballot`, applied
to the one canon entity in this pack's scope that has a freeze
requirement.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from epd2_eligibility_service.application import create_eligibility_rule
from epd2_eligibility_service.exceptions import RuleVersionFrozenError
from epd2_eligibility_service.storage import InMemoryEligibilityRuleStore


def test_identical_resubmission_of_a_rule_version_is_idempotent(
    eligibility_rule_store: InMemoryEligibilityRuleStore,
) -> None:
    rule_id = uuid4()
    scope_id = uuid4()
    kwargs = dict(
        eligibility_rule_id=rule_id,
        rule_version=1,
        scope_type="civic_space",
        scope_id=scope_id,
        required_membership_status="active",
        required_verification_level="basic",
        region_constraint=None,
        minimum_membership_age=None,
        exclusion_conditions=(),
        valid_from=datetime(2026, 1, 1, tzinfo=UTC),
        valid_until=None,
    )
    first = create_eligibility_rule(
        eligibility_rule_store,
        **kwargs,  # type: ignore[arg-type]
    )
    second = create_eligibility_rule(
        eligibility_rule_store,
        **kwargs,  # type: ignore[arg-type]
    )
    assert first == second


def test_conflicting_resubmission_of_a_rule_version_is_rejected(
    eligibility_rule_store: InMemoryEligibilityRuleStore,
) -> None:
    """Once (eligibility_rule_id, rule_version) exists, its content is
    frozen - a later attempt to change it (even a single field) must
    fail-closed, never silently overwrite."""
    rule_id = uuid4()
    create_eligibility_rule(
        eligibility_rule_store,
        eligibility_rule_id=rule_id,
        rule_version=1,
        scope_type="civic_space",
        scope_id=uuid4(),
        required_membership_status="active",
        required_verification_level="basic",
        region_constraint=None,
        minimum_membership_age=None,
        exclusion_conditions=(),
        valid_from=datetime(2026, 1, 1, tzinfo=UTC),
        valid_until=None,
    )
    with pytest.raises(RuleVersionFrozenError) as excinfo:
        create_eligibility_rule(
            eligibility_rule_store,
            eligibility_rule_id=rule_id,
            rule_version=1,
            scope_type="civic_space",
            scope_id=uuid4(),  # different content -> frozen conflict
            required_membership_status="active",
            required_verification_level="basic",
            region_constraint=None,
            minimum_membership_age=None,
            exclusion_conditions=(),
            valid_from=datetime(2026, 1, 1, tzinfo=UTC),
            valid_until=None,
        )
    assert excinfo.value.reason_code == "ELIGIBILITY_RULE_VERSION_FROZEN"


def test_a_new_rule_version_is_a_separate_unfrozen_entity(
    eligibility_rule_store: InMemoryEligibilityRuleStore,
) -> None:
    """Freezing applies per-version, not per-rule-id - creating rule_version
    2 for the same eligibility_rule_id is a distinct, independently
    freezable entity (this is how a rule change reaches the system at all:
    a new version, never mutating an old one)."""
    rule_id = uuid4()
    v1 = create_eligibility_rule(
        eligibility_rule_store,
        eligibility_rule_id=rule_id,
        rule_version=1,
        scope_type="civic_space",
        scope_id=uuid4(),
        required_membership_status="active",
        required_verification_level="basic",
        region_constraint=None,
        minimum_membership_age=None,
        exclusion_conditions=(),
        valid_from=datetime(2026, 1, 1, tzinfo=UTC),
        valid_until=None,
    )
    v2 = create_eligibility_rule(
        eligibility_rule_store,
        eligibility_rule_id=rule_id,
        rule_version=2,
        scope_type="civic_space",
        scope_id=uuid4(),
        required_membership_status="suspended",
        required_verification_level="enhanced",
        region_constraint=None,
        minimum_membership_age=None,
        exclusion_conditions=(),
        valid_from=datetime(2026, 6, 1, tzinfo=UTC),
        valid_until=None,
    )
    assert v1.rule_version == 1
    assert v2.rule_version == 2
    assert v1 != v2
