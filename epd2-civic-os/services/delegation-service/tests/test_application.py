"""Tests for epd2_delegation_service.application.

Exercises the full command set, canon section 16.1's prohibitions #1/#2
enforced end-to-end through `create_delegation`, the ADR-009 item 9
depth-1/`DELEGATION_CYCLE` guard (with an explicit A->B then B->C
regression), ADR-009 item 10's direct-vote-override resolution via
`resolve_active_delegate`, `resolve_delegation_snapshot`'s freeze/
idempotency, event-idempotency replay, and audit creation (including the
audit-only record for a rejected cycle-detection attempt).
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from epd2_audit_core.storage import InMemoryAuditEventStore
from epd2_core.clock import FixedClock
from epd2_core.event_envelope import ActorRef
from epd2_delegation_service.application import (
    DelegationResult,
    PermissionDeniedError,
    activate_delegation,
    create_delegation,
    expire_delegation,
    mark_delegation_invalid,
    resolve_active_delegate,
    resolve_delegation_snapshot,
    revoke_delegation,
    suspend_delegation,
    unsuspend_delegation,
)
from epd2_delegation_service.domain import DelegationStatus
from epd2_delegation_service.exceptions import (
    DelegationCycleError,
    DelegationExpiredError,
    DelegationScopeConflictError,
    SelfDelegationError,
    SnapshotFrozenError,
    UnknownDelegationError,
)
from epd2_delegation_service.storage import (
    InMemoryDelegationSnapshotStore,
    InMemoryDelegationStore,
)

_NOW = datetime(2026, 1, 5, tzinfo=UTC)
_CLOCK = FixedClock(_NOW)
_VALID_FROM = datetime(2026, 1, 1, tzinfo=UTC)


def _actor() -> ActorRef:
    return ActorRef(actor_id=uuid4(), actor_type="service")


class _Fixture:
    def __init__(self) -> None:
        self.delegation_store = InMemoryDelegationStore()
        self.snapshot_store = InMemoryDelegationSnapshotStore()
        self.audit_store = InMemoryAuditEventStore()


def _create(
    fx: _Fixture,
    *,
    delegator_actor_id: UUID | None = None,
    delegate_actor_id: UUID | None = None,
    scope_type: str = "ballot",
    scope_id: UUID | None = None,
    valid_until: datetime | None = None,
    delegation_id: UUID | None = None,
    actor: ActorRef | None = None,
    actor_is_authorized: bool = True,
    event_id: UUID | None = None,
) -> DelegationResult:
    return create_delegation(
        fx.delegation_store,
        fx.audit_store,
        delegation_id=delegation_id if delegation_id is not None else uuid4(),
        delegator_actor_id=delegator_actor_id if delegator_actor_id is not None else uuid4(),
        delegate_actor_id=delegate_actor_id if delegate_actor_id is not None else uuid4(),
        scope_type=scope_type,
        scope_id=scope_id if scope_id is not None else uuid4(),
        valid_from=_VALID_FROM,
        valid_until=valid_until,
        revocation_status="none",
        actor=actor if actor is not None else _actor(),
        actor_is_authorized=actor_is_authorized,
        correlation_id=uuid4(),
        clock=_CLOCK,
        event_id=event_id,
    )


# --- create_delegation ---------------------------------------------------


def test_create_delegation_requires_authorization() -> None:
    fx = _Fixture()
    with pytest.raises(PermissionDeniedError):
        _create(fx, actor_is_authorized=False)


def test_create_delegation_rejects_self_delegation() -> None:
    fx = _Fixture()
    actor_id = uuid4()
    with pytest.raises(SelfDelegationError):
        _create(fx, delegator_actor_id=actor_id, delegate_actor_id=actor_id)


def test_create_delegation_emits_event_and_audit() -> None:
    fx = _Fixture()
    result = _create(fx)
    assert result.delegation.status == DelegationStatus.DRAFT
    assert result.event is not None
    assert result.event.event_type == "delegation.created"
    assert result.audit_event.reason_code == "DELEGATION_STATUS_CHANGED"
    assert result.audit_event.target_id == result.delegation.delegation_id


def test_create_delegation_is_idempotent_by_event_id() -> None:
    """CT-00-04: a retried call with the same `event_id` (and therefore
    the same `audit_event_id`) AND identical other content is a no-op -
    same `correlation_id` too, since `append_audit_event`'s own
    idempotency check compares every caller-controlled field, including
    `correlation_id` (see `epd2_audit_core.application._matches_existing`).
    """
    fx = _Fixture()
    event_id = uuid4()
    delegation_id = uuid4()
    delegator = uuid4()
    delegate = uuid4()
    scope_id = uuid4()
    correlation_id = uuid4()
    kwargs: dict[str, object] = dict(
        delegation_id=delegation_id,
        delegator_actor_id=delegator,
        delegate_actor_id=delegate,
        scope_type="ballot",
        scope_id=scope_id,
        valid_from=_VALID_FROM,
        valid_until=None,
        revocation_status="none",
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=correlation_id,
        clock=_CLOCK,
        event_id=event_id,
    )
    first = create_delegation(fx.delegation_store, fx.audit_store, **kwargs)  # type: ignore[arg-type]
    second = create_delegation(fx.delegation_store, fx.audit_store, **kwargs)  # type: ignore[arg-type]
    assert first.audit_event.audit_event_id == second.audit_event.audit_event_id
    assert first.audit_event == second.audit_event


def test_create_delegation_rejects_scope_conflict() -> None:
    """Canon prohibition #2."""
    fx = _Fixture()
    delegator = uuid4()
    scope_id = uuid4()
    _create(fx, delegator_actor_id=delegator, scope_id=scope_id)
    with pytest.raises(DelegationScopeConflictError):
        _create(fx, delegator_actor_id=delegator, scope_id=scope_id)


def test_create_delegation_rejects_depth_1_violation() -> None:
    """ADR-009 item 9: create A->B (active) then attempt to create B->C
    for the SAME scope, expecting rejection (DELEGATION_CYCLE)."""
    fx = _Fixture()
    a = uuid4()
    b = uuid4()
    c = uuid4()
    scope_id = uuid4()

    a_to_b = _create(fx, delegator_actor_id=a, delegate_actor_id=b, scope_id=scope_id)
    activate_delegation(
        fx.delegation_store,
        fx.audit_store,
        delegation_id=a_to_b.delegation.delegation_id,
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )

    with pytest.raises(DelegationCycleError):
        _create(fx, delegator_actor_id=b, delegate_actor_id=c, scope_id=scope_id)


def test_create_delegation_depth_violation_is_audited_despite_no_event() -> None:
    """Judgment call (README.md): a rejected cycle attempt writes no
    Delegation and emits no delegation.* event, but IS audited under
    delegation.cycle_detected / DELEGATION_CYCLE."""
    fx = _Fixture()
    a = uuid4()
    b = uuid4()
    c = uuid4()
    scope_id = uuid4()

    a_to_b = _create(fx, delegator_actor_id=a, delegate_actor_id=b, scope_id=scope_id)
    activate_delegation(
        fx.delegation_store,
        fx.audit_store,
        delegation_id=a_to_b.delegation.delegation_id,
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )

    # Two audit entries so far for the real A->B delegation: one for
    # `create`, one for `activate`.
    audit_count_before = len(
        fx.audit_store.list_by_aggregate("delegation", a_to_b.delegation.delegation_id)
    )
    assert audit_count_before == 2
    attempted_delegation_id = uuid4()
    with pytest.raises(DelegationCycleError):
        _create(
            fx,
            delegator_actor_id=b,
            delegate_actor_id=c,
            scope_id=scope_id,
            delegation_id=attempted_delegation_id,
        )
    # The rejected attempt must not add any audit entry under the real
    # A->B delegation's own aggregate - it gets its own, separate record.
    assert (
        len(fx.audit_store.list_by_aggregate("delegation", a_to_b.delegation.delegation_id))
        == audit_count_before
    )

    rejection_records = fx.audit_store.list_by_aggregate("delegation", attempted_delegation_id)
    assert len(rejection_records) == 1
    record = rejection_records[0]
    assert record.event_type == "delegation.cycle_detected"
    assert record.reason_code == "DELEGATION_CYCLE"
    assert fx.delegation_store.get(attempted_delegation_id) is None


def test_create_delegation_allows_depth_1_chain_for_different_scope() -> None:
    """The depth-1 guard is scoped: B may still delegate for a DIFFERENT
    scope even while B is an active delegator for another scope."""
    fx = _Fixture()
    a = uuid4()
    b = uuid4()
    c = uuid4()
    scope_1 = uuid4()
    scope_2 = uuid4()

    a_to_b = _create(fx, delegator_actor_id=a, delegate_actor_id=b, scope_id=scope_1)
    activate_delegation(
        fx.delegation_store,
        fx.audit_store,
        delegation_id=a_to_b.delegation.delegation_id,
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )

    b_to_c = _create(fx, delegator_actor_id=b, delegate_actor_id=c, scope_id=scope_2)
    assert b_to_c.delegation.status == DelegationStatus.DRAFT


# --- activate_delegation ---------------------------------------------------


def test_activate_delegation_transitions_draft_to_active() -> None:
    fx = _Fixture()
    created = _create(fx)
    result = activate_delegation(
        fx.delegation_store,
        fx.audit_store,
        delegation_id=created.delegation.delegation_id,
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.delegation.status == DelegationStatus.ACTIVE
    assert result.event is not None
    assert result.event.event_type == "delegation.activated"


def test_activate_delegation_rejects_unknown_delegation() -> None:
    fx = _Fixture()
    with pytest.raises(UnknownDelegationError):
        activate_delegation(
            fx.delegation_store,
            fx.audit_store,
            delegation_id=uuid4(),
            actor=_actor(),
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


def test_activate_delegation_rejects_already_time_expired_draft() -> None:
    fx = _Fixture()
    # After valid_from (2026-01-01) so construction succeeds, but before
    # _NOW (2026-01-05) so activation finds it already time-expired.
    already_passed_valid_until = datetime(2026, 1, 3, tzinfo=UTC)
    created = _create(
        fx,
        valid_until=already_passed_valid_until,
    )
    with pytest.raises(DelegationExpiredError):
        activate_delegation(
            fx.delegation_store,
            fx.audit_store,
            delegation_id=created.delegation.delegation_id,
            actor=_actor(),
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


# --- revoke / expire / suspend / unsuspend / mark_invalid ------------------


def test_revoke_delegation_emits_event() -> None:
    fx = _Fixture()
    created = _create(fx)
    activate_delegation(
        fx.delegation_store,
        fx.audit_store,
        delegation_id=created.delegation.delegation_id,
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    result = revoke_delegation(
        fx.delegation_store,
        fx.audit_store,
        delegation_id=created.delegation.delegation_id,
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.delegation.status == DelegationStatus.REVOKED
    assert result.event is not None
    assert result.event.event_type == "delegation.revoked"


def test_expire_delegation_emits_event() -> None:
    fx = _Fixture()
    created = _create(fx)
    activate_delegation(
        fx.delegation_store,
        fx.audit_store,
        delegation_id=created.delegation.delegation_id,
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    result = expire_delegation(
        fx.delegation_store,
        fx.audit_store,
        delegation_id=created.delegation.delegation_id,
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.delegation.status == DelegationStatus.EXPIRED
    assert result.event is not None
    assert result.event.event_type == "delegation.expired"


def test_suspend_and_unsuspend_persist_and_audit_but_emit_no_event() -> None:
    """suspend/unsuspend/invalid: persist+audit only, no canon event."""
    fx = _Fixture()
    created = _create(fx)
    activate_delegation(
        fx.delegation_store,
        fx.audit_store,
        delegation_id=created.delegation.delegation_id,
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    suspended = suspend_delegation(
        fx.delegation_store,
        fx.audit_store,
        delegation_id=created.delegation.delegation_id,
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert suspended.delegation.status == DelegationStatus.SUSPENDED
    assert suspended.event is None
    assert suspended.audit_event.reason_code == "DELEGATION_STATUS_CHANGED"

    unsuspended = unsuspend_delegation(
        fx.delegation_store,
        fx.audit_store,
        delegation_id=created.delegation.delegation_id,
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert unsuspended.delegation.status == DelegationStatus.ACTIVE
    assert unsuspended.event is None


def test_mark_delegation_invalid_persists_and_audits_no_event() -> None:
    fx = _Fixture()
    created = _create(fx)
    result = mark_delegation_invalid(
        fx.delegation_store,
        fx.audit_store,
        delegation_id=created.delegation.delegation_id,
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.delegation.status == DelegationStatus.INVALID
    assert result.event is None


# --- resolve_active_delegate (ADR-009 item 10) -----------------------------


def test_resolve_active_delegate_returns_none_when_delegator_voted_directly() -> None:
    fx = _Fixture()
    delegator = uuid4()
    delegate = uuid4()
    scope_id = uuid4()
    created = _create(
        fx, delegator_actor_id=delegator, delegate_actor_id=delegate, scope_id=scope_id
    )
    activate_delegation(
        fx.delegation_store,
        fx.audit_store,
        delegation_id=created.delegation.delegation_id,
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )

    resolved = resolve_active_delegate(
        fx.delegation_store,
        delegator_actor_id=delegator,
        scope_type="ballot",
        scope_id=scope_id,
        direct_voters=frozenset({delegator}),
    )
    assert resolved is None


def test_resolve_active_delegate_returns_delegate_when_active() -> None:
    fx = _Fixture()
    delegator = uuid4()
    delegate = uuid4()
    scope_id = uuid4()
    created = _create(
        fx, delegator_actor_id=delegator, delegate_actor_id=delegate, scope_id=scope_id
    )
    activate_delegation(
        fx.delegation_store,
        fx.audit_store,
        delegation_id=created.delegation.delegation_id,
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )

    resolved = resolve_active_delegate(
        fx.delegation_store,
        delegator_actor_id=delegator,
        scope_type="ballot",
        scope_id=scope_id,
        direct_voters=frozenset(),
    )
    assert resolved == delegate


def test_resolve_active_delegate_returns_none_without_active_delegation() -> None:
    fx = _Fixture()
    resolved = resolve_active_delegate(
        fx.delegation_store,
        delegator_actor_id=uuid4(),
        scope_type="ballot",
        scope_id=uuid4(),
        direct_voters=frozenset(),
    )
    assert resolved is None


def test_resolve_active_delegate_ignores_draft_delegation() -> None:
    fx = _Fixture()
    delegator = uuid4()
    delegate = uuid4()
    scope_id = uuid4()
    _create(fx, delegator_actor_id=delegator, delegate_actor_id=delegate, scope_id=scope_id)
    # Still draft - not active.
    resolved = resolve_active_delegate(
        fx.delegation_store,
        delegator_actor_id=delegator,
        scope_type="ballot",
        scope_id=scope_id,
        direct_voters=frozenset(),
    )
    assert resolved is None


# --- resolve_delegation_snapshot --------------------------------------------


def _active_delegation(fx: _Fixture, *, delegator: UUID, delegate: UUID, scope_id: UUID) -> UUID:
    created = _create(
        fx, delegator_actor_id=delegator, delegate_actor_id=delegate, scope_id=scope_id
    )
    activate_delegation(
        fx.delegation_store,
        fx.audit_store,
        delegation_id=created.delegation.delegation_id,
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    return created.delegation.delegation_id


def test_resolve_delegation_snapshot_accumulates_weights() -> None:
    fx = _Fixture()
    scope_id = uuid4()
    delegate = uuid4()
    delegators = {uuid4(), uuid4(), uuid4()}
    for d in delegators:
        _active_delegation(fx, delegator=d, delegate=delegate, scope_id=scope_id)

    ballot_id = uuid4()
    result = resolve_delegation_snapshot(
        fx.delegation_store,
        fx.snapshot_store,
        fx.audit_store,
        ballot_id=ballot_id,
        policy_version=1,
        delegator_actor_ids=frozenset(delegators),
        scope_type="ballot",
        scope_id=scope_id,
        direct_voters=frozenset(),
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.snapshot.resolved_weights == {delegate: 3}
    assert result.event.event_type == "delegation.snapshot_created"
    assert result.audit_event.reason_code == "DELEGATION_SNAPSHOT_CREATED"


def test_resolve_delegation_snapshot_excludes_direct_voters() -> None:
    fx = _Fixture()
    scope_id = uuid4()
    delegate = uuid4()
    direct_voter = uuid4()
    delegated = uuid4()
    _active_delegation(fx, delegator=direct_voter, delegate=delegate, scope_id=scope_id)
    _active_delegation(fx, delegator=delegated, delegate=delegate, scope_id=scope_id)

    result = resolve_delegation_snapshot(
        fx.delegation_store,
        fx.snapshot_store,
        fx.audit_store,
        ballot_id=uuid4(),
        policy_version=1,
        delegator_actor_ids=frozenset({direct_voter, delegated}),
        scope_type="ballot",
        scope_id=scope_id,
        direct_voters=frozenset({direct_voter}),
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.snapshot.resolved_weights == {delegate: 1}


def test_resolve_delegation_snapshot_is_idempotent_for_identical_inputs() -> None:
    fx = _Fixture()
    scope_id = uuid4()
    delegate = uuid4()
    delegator = uuid4()
    _active_delegation(fx, delegator=delegator, delegate=delegate, scope_id=scope_id)
    ballot_id = uuid4()

    kwargs = dict(
        ballot_id=ballot_id,
        policy_version=1,
        delegator_actor_ids=frozenset({delegator}),
        scope_type="ballot",
        scope_id=scope_id,
        direct_voters=frozenset(),
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    first = resolve_delegation_snapshot(
        fx.delegation_store,
        fx.snapshot_store,
        fx.audit_store,
        **kwargs,  # type: ignore[arg-type]
    )
    second = resolve_delegation_snapshot(
        fx.delegation_store,
        fx.snapshot_store,
        fx.audit_store,
        **kwargs,  # type: ignore[arg-type]
    )
    assert first.snapshot.delegation_snapshot_id == second.snapshot.delegation_snapshot_id
    assert first.snapshot.snapshot_hash == second.snapshot.snapshot_hash


def test_resolve_delegation_snapshot_raises_frozen_error_when_delegation_state_changes() -> None:
    """Canon prohibition #4: once frozen for a given `(ballot_id,
    input_hash)`, the snapshot cannot silently change even if the
    underlying delegation graph changes afterward - this asserts the
    freeze against this service's own `DelegationSnapshot` digest, the
    same pattern `EligibilityRule`/`EligibilitySnapshot` established
    (CT-00-10 Rule Freeze test case)."""
    fx = _Fixture()
    scope_id = uuid4()
    delegate_1 = uuid4()
    delegator = uuid4()
    ballot_id = uuid4()
    delegation_id = _active_delegation(
        fx, delegator=delegator, delegate=delegate_1, scope_id=scope_id
    )

    kwargs = dict(
        ballot_id=ballot_id,
        policy_version=1,
        delegator_actor_ids=frozenset({delegator}),
        scope_type="ballot",
        scope_id=scope_id,
        direct_voters=frozenset(),
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    resolve_delegation_snapshot(
        fx.delegation_store,
        fx.snapshot_store,
        fx.audit_store,
        **kwargs,  # type: ignore[arg-type]
    )

    # Revoke the delegation and create + activate a new one to a
    # different delegate, WITHOUT changing input_hash's own inputs
    # (delegator_actor_ids/direct_voters/ballot_id/policy_version/scope
    # are identical) - the resolved *content* would now differ.
    revoke_delegation(
        fx.delegation_store,
        fx.audit_store,
        delegation_id=delegation_id,
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    _active_delegation(fx, delegator=delegator, delegate=uuid4(), scope_id=scope_id)

    with pytest.raises(SnapshotFrozenError):
        resolve_delegation_snapshot(
            fx.delegation_store,
            fx.snapshot_store,
            fx.audit_store,
            **kwargs,  # type: ignore[arg-type]
        )


def test_resolve_delegation_snapshot_requires_authorization() -> None:
    fx = _Fixture()
    with pytest.raises(PermissionDeniedError):
        resolve_delegation_snapshot(
            fx.delegation_store,
            fx.snapshot_store,
            fx.audit_store,
            ballot_id=uuid4(),
            policy_version=1,
            delegator_actor_ids=frozenset(),
            scope_type="ballot",
            scope_id=uuid4(),
            direct_voters=frozenset(),
            actor=_actor(),
            actor_is_authorized=False,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )
