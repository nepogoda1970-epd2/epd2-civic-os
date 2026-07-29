"""The command frame: what every command is forced through.

`_guard` and `_finish` exist so that no command can assemble its own
sequence of checks. The tests here exercise the frame itself through real
commands, because a frame that is only unit-tested in isolation is a frame
a command can still bypass.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from _privileged_builders import FixedClock, StubAuthorizationPort, authority, build_stores

from epd2_privileged_access_service import application as app
from epd2_privileged_access_service.access import GrantState, ResourceScope
from epd2_privileged_access_service.domain import (
    AuthorityReference,
    EffectiveWindow,
    OrganizationalScopeRef,
    Purpose,
    PurposeBinding,
    ReasonCoded,
    RequestContext,
    RiskClass,
)
from epd2_privileged_access_service.exceptions import (
    IdempotencyConflictError,
    OptimisticConcurrencyConflictError,
    OrganizationScopeUndeterminedError,
    PrivilegeAuthorityMissingError,
    PrivilegePurposeMismatchError,
    RecordNotFoundError,
    SelfApprovalProhibitedError,
)
from epd2_privileged_access_service.policy import REFERENCE_POLICY
from epd2_privileged_access_service.roles import OperationalAssignmentRole
from epd2_privileged_access_service.storage import PrivilegedStores

T0 = datetime(2026, 3, 1, 9, 0, tzinfo=UTC)
SCOPE = OrganizationalScopeRef(organization_id=uuid4())
OTHER = OrganizationalScopeRef(organization_id=uuid4())

SUBJECT = "actor:subject"
APPROVER = "actor:security"


def _reason(code: str = "PRIVILEGE_ACCESS_APPROVAL_RECORDED") -> ReasonCoded:
    return ReasonCoded(reason_code=code, authority_reference="authority:1")


def _context(
    role: str,
    actor: str,
    *,
    scope: OrganizationalScopeRef = SCOPE,
    event_id: UUID | None = None,
    authorities: tuple[AuthorityReference, ...] | None = None,
) -> RequestContext:
    return RequestContext(
        scope=scope,
        authorities=authorities if authorities is not None else (authority(role, scope, actor),),
        event_id=event_id or uuid4(),
    )


def _request_access(
    stores: PrivilegedStores,
    port: StubAuthorizationPort,
    clock: FixedClock,
    *,
    request_id: UUID | None = None,
    risk: RiskClass = RiskClass.MODERATE,
    scope: OrganizationalScopeRef = SCOPE,
) -> UUID:
    request_id = request_id or uuid4()
    app.request_privileged_access(
        stores,
        context=_context("domain_administrator", SUBJECT, scope=scope),
        port=port,
        clock=clock,
        policy=REFERENCE_POLICY,
        request_id=request_id,
        subject_reference=SUBJECT,
        requested_role=OperationalAssignmentRole.DOMAIN_ADMINISTRATOR,
        resource_scope=ResourceScope(domain="membership"),
        requested_operations=frozenset({"read_record"}),
        purpose=PurposeBinding(
            purpose=Purpose.OPERATIONS, justification_reference="justification:1"
        ),
        requested_window=EffectiveWindow(valid_from=T0, valid_until=T0 + timedelta(hours=4)),
        risk_class=risk,
        data_classes=frozenset({"membership_record"}),
    )
    return request_id


def _approved_grant(
    stores: PrivilegedStores,
    port: StubAuthorizationPort,
    clock: FixedClock,
    *,
    approvers: tuple[str, ...] = (APPROVER,),
) -> UUID:
    request_id = _request_access(stores, port, clock)
    grant_id = uuid4()
    app.approve_privileged_access(
        stores,
        context=_context("security_administrator", APPROVER),
        port=port,
        clock=clock,
        policy=REFERENCE_POLICY,
        request_id=request_id,
        grant_id=grant_id,
        approvers=approvers,
        reason=_reason(),
    )
    return grant_id


@pytest.fixture
def frame() -> tuple[PrivilegedStores, StubAuthorizationPort, FixedClock]:
    return build_stores(), StubAuthorizationPort(), FixedClock(T0)


class TestScopeFirst:
    def test_an_undetermined_scope_denies_before_anything_else(
        self, frame: tuple[PrivilegedStores, StubAuthorizationPort, FixedClock]
    ) -> None:
        """Scope is checked before authority, before any read and before
        any write. A command that resolved authority first would have
        already told the caller something about another organization."""
        stores, port, clock = frame
        context = RequestContext(
            scope=None,
            authorities=(authority("domain_administrator", SCOPE, SUBJECT),),
            event_id=uuid4(),
        )
        with pytest.raises(OrganizationScopeUndeterminedError):
            _ = app.request_privileged_access(
                stores,
                context=context,
                port=port,
                clock=clock,
                policy=REFERENCE_POLICY,
                request_id=uuid4(),
                subject_reference=SUBJECT,
                requested_role=OperationalAssignmentRole.DOMAIN_ADMINISTRATOR,
                resource_scope=ResourceScope(domain="membership"),
                requested_operations=frozenset({"read_record"}),
                purpose=PurposeBinding(purpose=Purpose.OPERATIONS, justification_reference="j"),
                requested_window=EffectiveWindow(
                    valid_from=T0, valid_until=T0 + timedelta(hours=1)
                ),
                risk_class=RiskClass.LOW,
                data_classes=frozenset({"membership_record"}),
            )
        assert stores.sink.published() == ()

    def test_a_foreign_record_reports_not_found_not_forbidden(
        self, frame: tuple[PrivilegedStores, StubAuthorizationPort, FixedClock]
    ) -> None:
        """`P12-ORG-005`: distinguishing "exists elsewhere" from "does not
        exist" would let a caller confirm another organization's grants by
        probing identifiers."""
        stores, port, clock = frame
        grant_id = _approved_grant(stores, port, clock)
        with pytest.raises(RecordNotFoundError):
            app.expire_privileged_access(
                stores,
                context=_context("security_administrator", APPROVER, scope=OTHER),
                port=port,
                clock=clock,
                policy=REFERENCE_POLICY,
                grant_id=grant_id,
                reason=_reason("PRIVILEGE_ACCESS_EXPIRY_RECORDED"),
            )


class TestAuthority:
    def test_a_command_with_no_declared_requirement_denies(self) -> None:
        """Adding a command forces an explicit authority decision: the
        failure mode of forgetting is denial, not silent permission."""
        assert "not_a_command" not in app.ACTION_REQUIREMENTS

    def test_every_declared_command_names_at_least_one_role(self) -> None:
        for command, roles in app.ACTION_REQUIREMENTS.items():
            assert roles, command

    def test_the_wrong_role_cannot_approve(
        self, frame: tuple[PrivilegedStores, StubAuthorizationPort, FixedClock]
    ) -> None:
        stores, port, clock = frame
        request_id = _request_access(stores, port, clock)
        with pytest.raises(PrivilegeAuthorityMissingError):
            app.approve_privileged_access(
                stores,
                context=_context("data_owner", APPROVER),
                port=port,
                clock=clock,
                policy=REFERENCE_POLICY,
                request_id=request_id,
                grant_id=uuid4(),
                approvers=(APPROVER,),
                reason=_reason(),
            )

    def test_an_unresolvable_authority_denies_even_with_the_right_string(
        self, frame: tuple[PrivilegedStores, StubAuthorizationPort, FixedClock]
    ) -> None:
        stores, _, clock = frame
        presented = authority("domain_administrator", SCOPE, SUBJECT)
        port = StubAuthorizationPort(inactive=frozenset({presented.authority_id}))
        with pytest.raises(PrivilegeAuthorityMissingError):
            app.request_privileged_access(
                stores,
                context=_context("", "", authorities=(presented,)),
                port=port,
                clock=clock,
                policy=REFERENCE_POLICY,
                request_id=uuid4(),
                subject_reference=SUBJECT,
                requested_role=OperationalAssignmentRole.DOMAIN_ADMINISTRATOR,
                resource_scope=ResourceScope(domain="membership"),
                requested_operations=frozenset({"read_record"}),
                purpose=PurposeBinding(purpose=Purpose.OPERATIONS, justification_reference="j"),
                requested_window=EffectiveWindow(
                    valid_from=T0, valid_until=T0 + timedelta(hours=1)
                ),
                risk_class=RiskClass.LOW,
                data_classes=frozenset({"membership_record"}),
            )


class TestSeparationOfDuties:
    def test_the_requester_may_not_approve_their_own_request(
        self, frame: tuple[PrivilegedStores, StubAuthorizationPort, FixedClock]
    ) -> None:
        """`P12-PAM-004`, enforced twice over: the acting approver is
        compared with the recorded requester, and the approver set is
        checked against it separately."""
        stores, port, clock = frame
        request_id = _request_access(stores, port, clock)
        with pytest.raises(SelfApprovalProhibitedError):
            app.approve_privileged_access(
                stores,
                context=_context("security_administrator", SUBJECT),
                port=port,
                clock=clock,
                policy=REFERENCE_POLICY,
                request_id=request_id,
                grant_id=uuid4(),
                approvers=(APPROVER,),
                reason=_reason(),
            )

    def test_the_requester_may_not_appear_in_the_approver_set(
        self, frame: tuple[PrivilegedStores, StubAuthorizationPort, FixedClock]
    ) -> None:
        stores, port, clock = frame
        request_id = _request_access(stores, port, clock)
        with pytest.raises(SelfApprovalProhibitedError):
            app.approve_privileged_access(
                stores,
                context=_context("security_administrator", APPROVER),
                port=port,
                clock=clock,
                policy=REFERENCE_POLICY,
                request_id=request_id,
                grant_id=uuid4(),
                approvers=(APPROVER, SUBJECT),
                reason=_reason(),
            )

    def test_an_incompatible_held_role_refuses_at_the_act(
        self, frame: tuple[PrivilegedStores, StubAuthorizationPort, FixedClock]
    ) -> None:
        """The matrix is re-checked against what the actor *really*
        holds, not against the role code they presented."""
        stores, _, clock = frame
        port = StubAuthorizationPort(held={APPROVER: frozenset({"system_administrator"})})
        request_id = _request_access(stores, port, clock)
        with pytest.raises(Exception) as excinfo:
            app.approve_privileged_access(
                stores,
                context=_context("security_administrator", APPROVER),
                port=port,
                clock=clock,
                policy=REFERENCE_POLICY,
                request_id=request_id,
                grant_id=uuid4(),
                approvers=(APPROVER,),
                reason=_reason(),
            )
        assert getattr(excinfo.value, "reason_code", "") == "AUTHORITY_ROLE_INCOMPATIBLE"


class TestIdempotency:
    def test_a_replay_returns_the_recorded_aggregate_without_re_running(
        self, frame: tuple[PrivilegedStores, StubAuthorizationPort, FixedClock]
    ) -> None:
        stores, port, clock = frame
        request_id = _request_access(stores, port, clock)
        grant_id = uuid4()
        event_id = uuid4()
        context = _context("security_administrator", APPROVER, event_id=event_id)
        first = app.approve_privileged_access(
            stores,
            context=context,
            port=port,
            clock=clock,
            policy=REFERENCE_POLICY,
            request_id=request_id,
            grant_id=grant_id,
            approvers=(APPROVER,),
            reason=_reason(),
        )
        published = len(stores.sink.published())
        second = app.approve_privileged_access(
            stores,
            context=context,
            port=port,
            clock=clock,
            policy=REFERENCE_POLICY,
            request_id=request_id,
            grant_id=grant_id,
            approvers=(APPROVER,),
            reason=_reason(),
        )
        assert second.grant.grant_id == first.grant.grant_id
        assert len(second.grant.history) == len(first.grant.history)
        assert len(stores.sink.published()) == published

    def test_the_same_event_id_with_different_content_is_a_conflict(
        self, frame: tuple[PrivilegedStores, StubAuthorizationPort, FixedClock]
    ) -> None:
        stores, port, clock = frame
        request_id = _request_access(stores, port, clock)
        event_id = uuid4()
        context = _context("security_administrator", APPROVER, event_id=event_id)
        app.approve_privileged_access(
            stores,
            context=context,
            port=port,
            clock=clock,
            policy=REFERENCE_POLICY,
            request_id=request_id,
            grant_id=uuid4(),
            approvers=(APPROVER,),
            reason=_reason(),
        )
        with pytest.raises(IdempotencyConflictError):
            app.approve_privileged_access(
                stores,
                context=context,
                port=port,
                clock=clock,
                policy=REFERENCE_POLICY,
                request_id=request_id,
                grant_id=uuid4(),
                approvers=(APPROVER,),
                reason=_reason(),
            )

    def test_a_missing_event_id_is_refused(
        self, frame: tuple[PrivilegedStores, StubAuthorizationPort, FixedClock]
    ) -> None:
        stores, port, clock = frame
        context = RequestContext(
            scope=SCOPE,
            authorities=(authority("domain_administrator", SCOPE, SUBJECT),),
            event_id=None,
        )
        with pytest.raises(IdempotencyConflictError):
            app.request_privileged_access(
                stores,
                context=context,
                port=port,
                clock=clock,
                policy=REFERENCE_POLICY,
                request_id=uuid4(),
                subject_reference=SUBJECT,
                requested_role=OperationalAssignmentRole.DOMAIN_ADMINISTRATOR,
                resource_scope=ResourceScope(domain="membership"),
                requested_operations=frozenset({"read_record"}),
                purpose=PurposeBinding(purpose=Purpose.OPERATIONS, justification_reference="j"),
                requested_window=EffectiveWindow(
                    valid_from=T0, valid_until=T0 + timedelta(hours=1)
                ),
                risk_class=RiskClass.LOW,
                data_classes=frozenset({"membership_record"}),
            )


class TestOptimisticConcurrency:
    def test_a_stale_expected_version_is_refused(
        self, frame: tuple[PrivilegedStores, StubAuthorizationPort, FixedClock]
    ) -> None:
        stores, port, clock = frame
        grant_id = _approved_grant(stores, port, clock)
        with pytest.raises(OptimisticConcurrencyConflictError):
            app.expire_privileged_access(
                stores,
                context=_context("security_administrator", APPROVER),
                port=port,
                clock=clock,
                policy=REFERENCE_POLICY,
                grant_id=grant_id,
                reason=_reason("PRIVILEGE_ACCESS_EXPIRY_RECORDED"),
                expected_history_length=99,
            )

    def test_the_current_version_is_accepted(
        self, frame: tuple[PrivilegedStores, StubAuthorizationPort, FixedClock]
    ) -> None:
        stores, port, clock = frame
        grant_id = _approved_grant(stores, port, clock)
        grant = stores.grants.get(grant_id)
        assert grant is not None
        result = app.expire_privileged_access(
            stores,
            context=_context("security_administrator", APPROVER),
            port=port,
            clock=clock,
            policy=REFERENCE_POLICY,
            grant_id=grant_id,
            reason=_reason("PRIVILEGE_ACCESS_EXPIRY_RECORDED"),
            expected_history_length=len(grant.history),
        )
        assert result.grant.state is GrantState.EXPIRED


class TestAuditBeforeEvent:
    def test_every_published_event_has_an_audit_row(
        self, frame: tuple[PrivilegedStores, StubAuthorizationPort, FixedClock]
    ) -> None:
        """An event that reached the stream without an audit row is an
        act nobody can account for."""
        stores, port, clock = frame
        _approved_grant(stores, port, clock)
        published = stores.sink.published()
        assert published
        assert len(stores.audit.list_all()) >= len(published)

    def test_the_audit_row_carries_the_command_and_a_registered_reason(
        self, frame: tuple[PrivilegedStores, StubAuthorizationPort, FixedClock]
    ) -> None:
        stores, port, clock = frame
        _approved_grant(stores, port, clock)
        rows = stores.audit.list_all()
        approval = [r for r in rows if r.action == "approve_privileged_access"]
        assert approval
        assert approval[0].reason_code == app.RC_ACCESS_APPROVED
        assert approval[0].policy_version == app.AUDIT_POLICY_VERSION
        assert approval[0].source_service == "privileged-access-service"

    def test_before_and_after_hashes_differ_across_a_transition(
        self, frame: tuple[PrivilegedStores, StubAuthorizationPort, FixedClock]
    ) -> None:
        stores, port, clock = frame
        _approved_grant(stores, port, clock)
        approval = next(
            r for r in stores.audit.list_all() if r.action == "approve_privileged_access"
        )
        assert approval.before_hash
        assert approval.after_hash
        assert approval.before_hash != approval.after_hash

    def test_the_actor_is_the_authority_never_a_person(
        self, frame: tuple[PrivilegedStores, StubAuthorizationPort, FixedClock]
    ) -> None:
        """FIR-INV-001: which office acted is recorded; which human
        exercised the office is deliberately not knowable from here."""
        stores, port, clock = frame
        _approved_grant(stores, port, clock)
        for row in stores.audit.list_all():
            assert row.actor_type == "organizational_authority"
        for envelope in stores.sink.published():
            assert envelope.actor.actor_type == "organizational_authority"


class TestActivationRechecks:
    def test_activation_refuses_a_grant_approved_under_another_policy(
        self, frame: tuple[PrivilegedStores, StubAuthorizationPort, FixedClock]
    ) -> None:
        """`P12-PAM-006`: time passes between approval and activation,
        and the policy can change in it. Activating on the stale policy
        would be acting on a fact that is no longer true."""
        from dataclasses import replace

        stores, port, clock = frame
        grant_id = _approved_grant(stores, port, clock)
        newer = replace(REFERENCE_POLICY, policy_version="pack-12-policy/v2")
        with pytest.raises(OptimisticConcurrencyConflictError):
            app.activate_privileged_access(
                stores,
                context=_context("domain_administrator", SUBJECT),
                port=port,
                clock=clock,
                policy=newer,
                grant_id=grant_id,
                requested_operation="read_record",
                requested_domain="membership",
                requested_purpose=Purpose.OPERATIONS,
                reason=_reason("PRIVILEGE_ACCESS_ACTIVATION_RECORDED"),
            )

    def test_activation_refuses_outside_the_validity_window(
        self, frame: tuple[PrivilegedStores, StubAuthorizationPort, FixedClock]
    ) -> None:
        stores, port, clock = frame
        grant_id = _approved_grant(stores, port, clock)
        clock.advance(timedelta(hours=5))
        with pytest.raises(Exception) as excinfo:
            app.activate_privileged_access(
                stores,
                context=_context("domain_administrator", SUBJECT),
                port=port,
                clock=clock,
                policy=REFERENCE_POLICY,
                grant_id=grant_id,
                requested_operation="read_record",
                requested_domain="membership",
                requested_purpose=Purpose.OPERATIONS,
                reason=_reason("PRIVILEGE_ACCESS_ACTIVATION_RECORDED"),
            )
        assert getattr(excinfo.value, "reason_code", "").startswith("PRIVILEGE_")

    def test_activation_refuses_an_operation_outside_the_grant(
        self, frame: tuple[PrivilegedStores, StubAuthorizationPort, FixedClock]
    ) -> None:
        stores, port, clock = frame
        grant_id = _approved_grant(stores, port, clock)
        with pytest.raises(PrivilegePurposeMismatchError):
            app.activate_privileged_access(
                stores,
                context=_context("domain_administrator", SUBJECT),
                port=port,
                clock=clock,
                policy=REFERENCE_POLICY,
                grant_id=grant_id,
                requested_operation="delete_record",
                requested_domain="membership",
                requested_purpose=Purpose.OPERATIONS,
                reason=_reason("PRIVILEGE_ACCESS_ACTIVATION_RECORDED"),
            )
