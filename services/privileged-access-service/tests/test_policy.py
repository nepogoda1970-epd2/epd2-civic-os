"""The versioned numeric policy (`OD-P12-03`).

The resolution of `OD-P12-03` has two halves, and both are tested here:
every number is configurable, and the *ceilings* are not. A policy file
that could raise its own maximum would be a policy file that could
disable the control it configures.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from epd2_privileged_access_service.domain import RiskClass
from epd2_privileged_access_service.exceptions import (
    DisclosureThresholdFailedError,
    StandingAccessProhibitedError,
)
from epd2_privileged_access_service.policy import (
    MAX_ALLOWED_BREAK_GLASS_DURATION,
    MAX_ALLOWED_GRANT_DURATION,
    MINIMUM_ALLOWED_COHORT_THRESHOLD,
    REFERENCE_POLICY,
    PrivilegedAccessPolicy,
)


class TestReferenceDefaults:
    def test_reference_policy_is_labelled_as_a_reference(self) -> None:
        """The defaults are reference defaults, not legally approved
        policy. The name is the disclaimer."""
        assert REFERENCE_POLICY.policy_version.startswith("pack-12")

    def test_every_number_is_a_field_not_a_literal(self) -> None:
        """`OD-P12-03`: no hard-coded numbers in the enforcement path.

        If a limit is a dataclass field it can be versioned, reviewed and
        changed by decision. If it is an integer inside a function it can
        only be changed by a code release, which is not a governance
        act."""
        numeric = {
            name
            for name, f in PrivilegedAccessPolicy.__dataclass_fields__.items()
            if f.type in {"int", "timedelta"}
        }
        assert {"cohort_threshold", "export_access_limit", "max_grant_duration"} <= numeric


class TestCeilings:
    def test_grant_duration_ceiling_cannot_be_raised_by_configuration(self) -> None:
        with pytest.raises(StandingAccessProhibitedError):
            PrivilegedAccessPolicy(
                policy_version="test/v1",
                max_grant_duration=MAX_ALLOWED_GRANT_DURATION + timedelta(days=1),
            )

    def test_break_glass_ceiling_cannot_be_raised(self) -> None:
        with pytest.raises(StandingAccessProhibitedError):
            PrivilegedAccessPolicy(
                policy_version="test/v1",
                max_break_glass_duration=MAX_ALLOWED_BREAK_GLASS_DURATION + timedelta(hours=1),
            )

    def test_cohort_threshold_cannot_be_lowered_below_the_floor(self) -> None:
        with pytest.raises(DisclosureThresholdFailedError):
            PrivilegedAccessPolicy(
                policy_version="test/v1",
                cohort_threshold=MINIMUM_ALLOWED_COHORT_THRESHOLD - 1,
            )

    def test_a_grant_longer_than_the_configured_maximum_is_refused(self) -> None:
        with pytest.raises(StandingAccessProhibitedError):
            REFERENCE_POLICY.assert_grant_duration_allowed(
                REFERENCE_POLICY.max_grant_duration + timedelta(seconds=1)
            )

    def test_break_glass_duration_is_checked_against_its_own_limit(self) -> None:
        with pytest.raises(StandingAccessProhibitedError):
            REFERENCE_POLICY.assert_break_glass_duration_allowed(
                REFERENCE_POLICY.max_break_glass_duration + timedelta(seconds=1)
            )


class TestApproverCounts:
    def test_high_and_critical_require_at_least_two(self) -> None:
        assert REFERENCE_POLICY.required_approvers(RiskClass.HIGH) >= 2
        assert REFERENCE_POLICY.required_approvers(RiskClass.CRITICAL) >= 2

    def test_dual_control_survives_a_policy_that_forgot_it(self) -> None:
        """A configuration that sets one approver for a high-risk class
        must not be constructible: `DUAL_CONTROL_RISK_CLASSES` states the
        rule independently of the numbers."""
        with pytest.raises(StandingAccessProhibitedError):
            PrivilegedAccessPolicy(policy_version="test/v1", approvers_high=1)
