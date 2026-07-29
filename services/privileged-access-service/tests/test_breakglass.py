"""Break-glass: a separate workflow that only adds obligations
(`P12-BG-*`, FIR-INV-006, FIR-INV-009, ADR-063)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from epd2_privileged_access_service.breakglass import (
    BreakGlassActivation,
    BreakGlassIndependentReview,
    BreakGlassState,
    EmergencyCondition,
    NotificationOutcome,
    assert_notification_not_suppressed,
    assert_renewal_is_new_decision,
    resolve_break_glass_state,
)
from epd2_privileged_access_service.domain import (
    EffectiveWindow,
    OrganizationalScopeRef,
    Purpose,
    PurposeBinding,
    ReasonCoded,
)
from epd2_privileged_access_service.exceptions import (
    BreakGlassConditionAbsentError,
    BreakGlassDualControlMissingError,
    BreakGlassNotificationUndeliveredError,
    BreakGlassRenewalRequiresDecisionError,
    BreakGlassScopeTooBroadError,
    ForbiddenTransitionError,
    SelfApprovalProhibitedError,
    StandingAccessProhibitedError,
    UnknownStatusError,
)
from epd2_privileged_access_service.policy import REFERENCE_POLICY
from epd2_privileged_access_service.storage import ReferenceNotificationAdapter

T0 = datetime(2026, 3, 1, 9, 0, tzinfo=UTC)
SCOPE = OrganizationalScopeRef(organization_id=uuid4())


def _condition() -> EmergencyCondition:
    return EmergencyCondition(
        condition_reference="incident:INC-1",
        condition_class="service_outage",
        declared_at=T0,
        declared_by="actor:oncall",
    )


def _reason() -> ReasonCoded:
    return ReasonCoded(
        reason_code="PRIVILEGE_BREAK_GLASS_APPROVAL_RECORDED",
        authority_reference="auth:1",
    )


def _activation(**overrides: object) -> BreakGlassActivation:
    base: dict[str, object] = {
        "activation_id": uuid4(),
        "organization_scope": SCOPE,
        "activator_reference": "actor:activator",
        "approver_reference": "actor:approver",
        "condition": _condition(),
        "purpose": PurposeBinding(purpose=Purpose.INCIDENT_RESPONSE, justification_reference="j"),
        "resource_domain": "membership",
        "permitted_operations": frozenset({"read_record"}),
        "window": EffectiveWindow(valid_from=T0, valid_until=T0 + timedelta(hours=1)),
        "policy_version": REFERENCE_POLICY.policy_version,
    }
    base.update(overrides)
    return BreakGlassActivation(**base)  # type: ignore[arg-type]


class TestEmergencyCondition:
    def test_a_condition_reference_is_mandatory(self) -> None:
        """Without it there is nothing to review afterwards, which is the
        whole point of the post-hoc review."""
        with pytest.raises(BreakGlassConditionAbsentError):
            EmergencyCondition(
                condition_reference="  ",
                condition_class="service_outage",
                declared_at=T0,
                declared_by="actor:oncall",
            )


class TestDualControl:
    def test_activator_and_approver_must_differ(self) -> None:
        """`P12-BG-003`: the second control is a second person."""
        with pytest.raises((SelfApprovalProhibitedError, BreakGlassDualControlMissingError)):
            _activation(activator_reference="actor:same", approver_reference="actor:same")

    def test_scope_must_stay_narrow(self) -> None:
        """Two separate ways a scope can be too broad, and both refuse:
        a window past the emergency ceiling, and a wildcard operation
        set. A wildcard is the more dangerous of the two, because it is
        the one that looks like a convenience."""
        broad_window = _activation(
            window=EffectiveWindow(
                valid_from=T0,
                valid_until=T0 + REFERENCE_POLICY.max_break_glass_duration * 2,
            )
        )
        with pytest.raises(StandingAccessProhibitedError):
            broad_window.assert_scope_narrow(REFERENCE_POLICY)

        wildcard = _activation(permitted_operations=frozenset({"*"}))
        with pytest.raises(BreakGlassScopeTooBroadError):
            wildcard.assert_scope_narrow(REFERENCE_POLICY)

        _activation().assert_scope_narrow(REFERENCE_POLICY)


class TestNotification:
    def test_suppression_by_the_activator_is_not_a_notification(self) -> None:
        outcome = NotificationOutcome(
            delivered=True,
            dispatch_reference="dispatch:1",
            recipient_class="security_oversight",
            suppressed_by="actor:activator",
        )
        with pytest.raises(BreakGlassNotificationUndeliveredError):
            assert_notification_not_suppressed(
                outcome,
                activator_reference="actor:activator",
                directed_subjects=frozenset(),
            )

    def test_suppression_by_a_directed_subject_is_also_refused(self) -> None:
        """The load-bearing clause: an activator who administers the
        notification channel has suppressed it without ever touching a
        suppression control."""
        outcome = NotificationOutcome(
            delivered=True,
            dispatch_reference="dispatch:1",
            recipient_class="security_oversight",
            suppressed_by="actor:their-deputy",
        )
        with pytest.raises(BreakGlassNotificationUndeliveredError):
            assert_notification_not_suppressed(
                outcome,
                activator_reference="actor:activator",
                directed_subjects=frozenset({"actor:their-deputy"}),
            )

    def test_an_unsuppressed_outcome_passes(self) -> None:
        outcome = NotificationOutcome(
            delivered=True,
            dispatch_reference="dispatch:1",
            recipient_class="security_oversight",
        )
        assert_notification_not_suppressed(
            outcome, activator_reference="actor:a", directed_subjects=frozenset()
        )

    def test_a_failed_dispatch_records_its_reason(self) -> None:
        adapter = ReferenceNotificationAdapter(deliver=False)
        outcome = adapter.dispatch(
            activation_id=uuid4(),
            organization_scope=SCOPE,
            recipient_class="security_oversight",
            activator_reference="actor:a",
        )
        assert outcome.delivered is False
        assert outcome.failure_reason


class TestLifecycle:
    def test_an_undeclared_transition_is_refused(self) -> None:
        with pytest.raises(ForbiddenTransitionError):
            _activation().with_state(
                BreakGlassState.EXPIRED,
                at=T0,
                action="skip",
                reason=_reason(),
                actor_reference="actor:x",
            )

    def test_escalation_is_reachable_from_approved_and_activated(self) -> None:
        approved = _activation().with_state(
            BreakGlassState.APPROVED,
            at=T0,
            action="approve",
            reason=_reason(),
            actor_reference="actor:approver",
        )
        escalated = approved.with_state(
            BreakGlassState.ESCALATED,
            at=T0,
            action="escalate",
            reason=_reason(),
            actor_reference="actor:approver",
        )
        assert escalated.state is BreakGlassState.ESCALATED

    def test_resolve_rejects_an_unknown_state(self) -> None:
        with pytest.raises(UnknownStatusError):
            resolve_break_glass_state("permanent")


class TestRenewal:
    def test_a_renewal_must_be_a_new_activation(self) -> None:
        """`P12-BG-013`: extension in place would make the ceiling
        advisory."""
        previous = _activation()
        with pytest.raises(BreakGlassRenewalRequiresDecisionError):
            assert_renewal_is_new_decision(previous, previous.activation_id)
        assert_renewal_is_new_decision(previous, uuid4())


class TestIndependentReview:
    def _review(self, reviewer: str) -> BreakGlassIndependentReview:
        return BreakGlassIndependentReview(
            review_id=uuid4(),
            activation_id=uuid4(),
            organization_scope=SCOPE,
            reviewer_reference=reviewer,
            reviewed_at=T0,
            outcome="justified",
            reason=_reason(),
        )

    def test_the_reviewer_is_neither_activator_nor_approver(self) -> None:
        activation = _activation()
        with pytest.raises(SelfApprovalProhibitedError):
            self._review("actor:activator").assert_reviewer_independent(activation)
        with pytest.raises(SelfApprovalProhibitedError):
            self._review("actor:approver").assert_reviewer_independent(activation)
        self._review("actor:independent").assert_reviewer_independent(activation)
