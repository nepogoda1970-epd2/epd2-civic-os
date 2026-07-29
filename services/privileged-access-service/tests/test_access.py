"""The privileged access grant (`P12-PAM-*`, ADR-062)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from epd2_privileged_access_service.access import (
    USABLE_STATES,
    GrantState,
    PrivilegedAccessGrant,
    PrivilegedAccessRequest,
    ResourceScope,
    assert_approver_set_sufficient,
    resolve_grant_state,
)
from epd2_privileged_access_service.domain import (
    EffectiveWindow,
    OrganizationalScopeRef,
    Purpose,
    PurposeBinding,
    ReasonCoded,
    RiskClass,
)
from epd2_privileged_access_service.exceptions import (
    ApproverCountInsufficientError,
    ForbiddenTransitionError,
    GrantDormantError,
    GrantExpiredError,
    GrantNotActivatedError,
    GrantRevokedError,
    JustificationMissingError,
    OperationNotGrantedError,
    PrivilegeOrganizationMismatchError,
    PrivilegePurposeMismatchError,
    PrivilegeScopeMismatchError,
    RiskClassificationUndeterminedError,
    SelfApprovalProhibitedError,
    UnknownStatusError,
)
from epd2_privileged_access_service.policy import REFERENCE_POLICY

T0 = datetime(2026, 3, 1, 9, 0, tzinfo=UTC)
SCOPE = OrganizationalScopeRef(organization_id=uuid4())
WINDOW = EffectiveWindow(valid_from=T0, valid_until=T0 + timedelta(hours=4))


def _purpose(p: Purpose = Purpose.OPERATIONS) -> PurposeBinding:
    return PurposeBinding(purpose=p, justification_reference="justification:1")


def _reason() -> ReasonCoded:
    return ReasonCoded(
        reason_code="PRIVILEGE_ACCESS_APPROVAL_RECORDED", authority_reference="auth:1"
    )


def _grant(**overrides: object) -> PrivilegedAccessGrant:
    base: dict[str, object] = {
        "grant_id": uuid4(),
        "request_id": uuid4(),
        "subject_reference": "actor:subject",
        "role": __import__(
            "epd2_privileged_access_service.roles", fromlist=["x"]
        ).OperationalAssignmentRole.DOMAIN_ADMINISTRATOR,
        "organization_scope": SCOPE,
        "resource_scope": ResourceScope(domain="membership"),
        "permitted_operations": frozenset({"read_record"}),
        "purpose": _purpose(),
        "window": WINDOW,
        "risk_class": RiskClass.MODERATE,
        "policy_version": REFERENCE_POLICY.policy_version,
        "approvers": ("actor:approver",),
    }
    base.update(overrides)
    return PrivilegedAccessGrant(**base)  # type: ignore[arg-type]


def _activated() -> PrivilegedAccessGrant:
    grant = _grant()
    return (
        grant.with_state(
            GrantState.UNDER_EVALUATION,
            at=T0,
            action="evaluate",
            reason=_reason(),
            actor_reference="actor:approver",
        )
        .with_state(
            GrantState.APPROVED,
            at=T0,
            action="approve",
            reason=_reason(),
            actor_reference="actor:approver",
        )
        .with_state(
            GrantState.ACTIVATED,
            at=T0,
            action="activate",
            reason=_reason(),
            actor_reference="actor:subject",
        )
    )


class TestRequestInvariants:
    def _request(self, **overrides: object) -> PrivilegedAccessRequest:
        from epd2_privileged_access_service.roles import OperationalAssignmentRole

        base: dict[str, object] = {
            "request_id": uuid4(),
            "subject_reference": "actor:subject",
            "requested_role": OperationalAssignmentRole.DATA_OWNER,
            "organization_scope": SCOPE,
            "resource_scope": ResourceScope(domain="membership"),
            "requested_operations": frozenset({"read_record"}),
            "purpose": _purpose(),
            "requested_window": WINDOW,
            "risk_class": RiskClass.LOW,
            "data_classes": frozenset({"membership_record"}),
            "requested_at": T0,
        }
        base.update(overrides)
        return PrivilegedAccessRequest(**base)  # type: ignore[arg-type]

    def test_requires_at_least_one_operation(self) -> None:
        with pytest.raises(OperationNotGrantedError):
            self._request(requested_operations=frozenset())

    def test_requires_at_least_one_data_class(self) -> None:
        """Without a data class, risk cannot be assessed, so the request
        is refused rather than assessed as low."""
        with pytest.raises(RiskClassificationUndeterminedError):
            self._request(data_classes=frozenset())

    def test_requires_a_written_justification(self) -> None:
        """The justification is enforced at the purpose binding, so a
        request cannot be assembled around an empty one in the first
        place."""
        with pytest.raises(JustificationMissingError):
            PurposeBinding(purpose=Purpose.OPERATIONS, justification_reference="")

    def test_a_complete_request_is_constructible(self) -> None:
        request = self._request()
        assert request.risk_class is RiskClass.LOW
        assert "requested_at" in request.to_state_payload()


class TestGrantInvariants:
    def test_the_subject_may_not_approve_itself(self) -> None:
        with pytest.raises(SelfApprovalProhibitedError):
            _grant(subject_reference="actor:a", approvers=("actor:a",))

    def test_approvers_must_be_distinct(self) -> None:
        with pytest.raises(ApproverCountInsufficientError):
            _grant(approvers=("actor:x", "actor:x"))

    def test_requires_at_least_one_operation(self) -> None:
        with pytest.raises(OperationNotGrantedError):
            _grant(permitted_operations=frozenset())

    def test_there_is_no_renew_method(self) -> None:
        """`P12-PAM-007`: continued access costs a new decision.

        Renewal in place would make "time-bound" advisory."""
        assert not hasattr(PrivilegedAccessGrant, "renew")
        assert not hasattr(PrivilegedAccessGrant, "extend")


class TestStateMachine:
    def test_an_undeclared_transition_is_refused(self) -> None:
        with pytest.raises(ForbiddenTransitionError):
            _grant().with_state(
                GrantState.ACTIVE,
                at=T0,
                action="skip",
                reason=_reason(),
                actor_reference="actor:x",
            )

    def test_history_is_append_only_and_sequenced(self) -> None:
        grant = _activated()
        assert [e.sequence for e in grant.history] == [1, 2, 3]
        assert grant.history[-1].state_after is GrantState.ACTIVATED

    def test_usable_states_are_exactly_two(self) -> None:
        """An approved-but-never-activated grant authorises nothing."""
        assert frozenset({GrantState.ACTIVATED, GrantState.ACTIVE}) == USABLE_STATES

    def test_resolve_rejects_an_unknown_state(self) -> None:
        with pytest.raises(UnknownStatusError):
            resolve_grant_state("superuser")


class TestAssertUsable:
    def _usable_kwargs(self, **overrides: object) -> dict[str, object]:
        base: dict[str, object] = {
            "at": T0 + timedelta(minutes=5),
            "policy": REFERENCE_POLICY,
            "operation": "read_record",
            "domain": "membership",
            "resource_reference": None,
            "scope": SCOPE,
            "purpose": Purpose.OPERATIONS,
        }
        base.update(overrides)
        return base

    def test_an_activated_grant_in_window_is_usable(self) -> None:
        _activated().assert_usable(**self._usable_kwargs())  # type: ignore[arg-type]

    def test_revocation_is_reported_before_expiry(self) -> None:
        """A revoked grant must say revoked. The two mean different
        things to an operator, and reporting expiry would hide a
        deliberate withdrawal behind the passage of time."""
        revoked = _activated().with_state(
            GrantState.REVOKED,
            at=T0,
            action="revoke",
            reason=_reason(),
            actor_reference="actor:sec",
        )
        with pytest.raises(GrantRevokedError):
            revoked.assert_usable(
                **self._usable_kwargs(at=T0 + timedelta(days=400))  # type: ignore[arg-type]
            )

    def test_an_unactivated_grant_authorises_nothing(self) -> None:
        with pytest.raises(GrantNotActivatedError):
            _grant().assert_usable(**self._usable_kwargs())  # type: ignore[arg-type]

    def test_outside_the_window_is_expiry(self) -> None:
        with pytest.raises(GrantExpiredError):
            _activated().assert_usable(
                **self._usable_kwargs(at=T0 + timedelta(hours=5))  # type: ignore[arg-type]
            )

    def test_dormancy_requires_review(self) -> None:
        grant = _activated().with_use(T0)
        long_window = EffectiveWindow(valid_from=T0, valid_until=T0 + timedelta(days=20))
        grant = _grant(window=long_window)
        grant = (
            grant.with_state(
                GrantState.UNDER_EVALUATION,
                at=T0,
                action="e",
                reason=_reason(),
                actor_reference="a",
            )
            .with_state(
                GrantState.APPROVED,
                at=T0,
                action="a",
                reason=_reason(),
                actor_reference="a",
            )
            .with_state(
                GrantState.ACTIVATED,
                at=T0,
                action="act",
                reason=_reason(),
                actor_reference="a",
            )
            .with_use(T0)
        )
        with pytest.raises(GrantDormantError):
            grant.assert_usable(
                **self._usable_kwargs(  # type: ignore[arg-type]
                    at=T0 + REFERENCE_POLICY.dormancy_interval + timedelta(hours=1)
                )
            )

    def test_a_foreign_organization_is_refused(self) -> None:
        other = OrganizationalScopeRef(organization_id=uuid4())
        with pytest.raises(PrivilegeOrganizationMismatchError):
            _activated().assert_usable(**self._usable_kwargs(scope=other))  # type: ignore[arg-type]

    def test_a_resource_outside_the_scope_is_refused(self) -> None:
        with pytest.raises(PrivilegeScopeMismatchError):
            _activated().assert_usable(**self._usable_kwargs(domain="finance"))  # type: ignore[arg-type]

    def test_an_ungranted_operation_is_refused(self) -> None:
        with pytest.raises(OperationNotGrantedError):
            _activated().assert_usable(**self._usable_kwargs(operation="delete_record"))  # type: ignore[arg-type]

    def test_a_different_purpose_is_refused(self) -> None:
        with pytest.raises(PrivilegePurposeMismatchError):
            _activated().assert_usable(**self._usable_kwargs(purpose=Purpose.AUDIT))  # type: ignore[arg-type]


class TestApproverSets:
    def test_the_requester_may_not_appear_among_approvers(self) -> None:
        with pytest.raises(SelfApprovalProhibitedError):
            assert_approver_set_sufficient(
                ("actor:a", "actor:b"),
                requester_reference="actor:a",
                risk_class=RiskClass.LOW,
                policy=REFERENCE_POLICY,
            )

    def test_high_risk_requires_the_policy_count(self) -> None:
        with pytest.raises(ApproverCountInsufficientError):
            assert_approver_set_sufficient(
                ("actor:b",),
                requester_reference="actor:a",
                risk_class=RiskClass.HIGH,
                policy=REFERENCE_POLICY,
            )
        assert_approver_set_sufficient(
            ("actor:b", "actor:c"),
            requester_reference="actor:a",
            risk_class=RiskClass.HIGH,
            policy=REFERENCE_POLICY,
        )


class TestResourceScope:
    def test_an_empty_reference_set_means_the_whole_domain(self) -> None:
        scope = ResourceScope(domain="membership")
        assert scope.admits("membership", "anything")

    def test_named_references_narrow(self) -> None:
        scope = ResourceScope(domain="membership", resource_references=frozenset({"rec:1"}))
        assert scope.admits("membership", "rec:1")
        assert not scope.admits("membership", "rec:2")
        assert not scope.admits("membership", None)
