"""Delegation Service application layer: the command set canon section
20.11 lists for this service (`delegation.created`, `delegation.activated`,
`delegation.revoked`, `delegation.expired`, `delegation.cycle_detected`,
`delegation.snapshot_created`), plus `suspend_delegation`/
`unsuspend_delegation`/`mark_delegation_invalid` (persist+audit only, no
canon event name - see each function's own docstring and README.md).

No PACK-02 dependency at all (ADR-008) and no PACK-03↔PACK-03 import
(ADR-008 item 3): this module imports only `epd2_core`/`epd2_audit_core`.
Where this service would conceptually need to know "did this ballot's
delegator already cast a direct vote" (ADR-009 item 10), it accepts that
as a plain `frozenset[UUID]` parameter (`direct_voters`) supplied by the
caller - never by importing `epd2_voting_service`.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from epd2_audit_core.application import AppendAuditEventRequest, append_audit_event
from epd2_audit_core.domain import AuditEvent
from epd2_audit_core.storage import AuditEventStore
from epd2_core.clock import Clock
from epd2_core.event_envelope import ActorRef, EventEnvelope, compute_payload_hash
from epd2_core.identifiers import generate_uuid
from epd2_delegation_service.domain import (
    Delegation,
    DelegationSnapshot,
    DelegationStatus,
    compute_delegation_snapshot_hash,
    compute_delegation_snapshot_input_hash,
)
from epd2_delegation_service.events import (
    build_delegation_activated_event,
    build_delegation_created_event,
    build_delegation_expired_event,
    build_delegation_revoked_event,
    build_delegation_snapshot_created_event,
    delegation_snapshot_state_payload,
    delegation_state_payload,
)
from epd2_delegation_service.exceptions import (
    DelegationCycleError,
    DelegationExpiredError,
    SelfDelegationError,
    UnknownDelegationError,
)
from epd2_delegation_service.storage import DelegationSnapshotStore, DelegationStore

#: Audit Core's own policy version for entries this service appends -
#: independent of `events.EVENT_VERSION` (the wire event schema version).
AUDIT_POLICY_VERSION = "1.0"
_SOURCE_SERVICE = "delegation-service"

#: Audit reason_code for every `Delegation` status transition (create,
#: activate, revoke, expire, suspend, unsuspend, mark-invalid) - canon
#: gives this service one lifecycle audit classification, not one per
#: event type; the specific transition is already visible via
#: `action`/`event_type` on the audit record itself (mirrors
#: `epd2_voting_service.application._BALLOT_STATUS_CHANGED`).
_DELEGATION_STATUS_CHANGED = "DELEGATION_STATUS_CHANGED"
#: Audit reason_code for a successful `resolve_delegation_snapshot` call.
_DELEGATION_SNAPSHOT_CREATED = "DELEGATION_SNAPSHOT_CREATED"


class PermissionDeniedError(PermissionError):
    reason_code = "PERMISSION_DENIED"


@dataclass(frozen=True, slots=True)
class DelegationResult:
    delegation: Delegation
    event: EventEnvelope | None
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class DelegationSnapshotResult:
    snapshot: DelegationSnapshot
    event: EventEnvelope
    audit_event: AuditEvent


def _delegation_audit_request(
    *,
    audit_event_id: UUID,
    event_type: str,
    delegation: Delegation,
    before_hash: str,
    actor: ActorRef,
    action: str,
    reason_code: str,
    correlation_id: UUID,
    occurred_at: datetime,
) -> AppendAuditEventRequest:
    return AppendAuditEventRequest(
        audit_event_id=audit_event_id,
        event_type=event_type,
        occurred_at=occurred_at,
        actor_id=actor.actor_id,
        actor_type=actor.actor_type,
        target_type="delegation",
        target_id=delegation.delegation_id,
        action=action,
        reason_code=reason_code,
        policy_version=AUDIT_POLICY_VERSION,
        correlation_id=correlation_id,
        source_service=_SOURCE_SERVICE,
        before_hash=before_hash,
        after_hash=compute_payload_hash(delegation_state_payload(delegation)),
    )


def create_delegation(
    delegation_store: DelegationStore,
    audit_store: AuditEventStore,
    *,
    delegation_id: UUID,
    delegator_actor_id: UUID,
    delegate_actor_id: UUID,
    scope_type: str,
    scope_id: UUID,
    valid_from: datetime,
    valid_until: datetime | None,
    revocation_status: str,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> DelegationResult:
    """Create a new `Delegation` in `draft` (canon 16.1) -> `delegation.created`.

    Validates all of canon section 16.1's prohibitions that apply at
    creation time, fail-closed, in this order:

    1. `actor_is_authorized`.
    2. Prohibition #1 (self-delegation): `delegator_actor_id ==
       delegate_actor_id` is rejected here explicitly, *before* a
       `Delegation` is ever constructed - belt-and-suspenders alongside
       `Delegation.__post_init__`'s own identical, independent check
       (`SelfDelegationError`, `DELEGATION_SELF_REFERENCE_FORBIDDEN`).
    3. ADR-009 item 9 (max delegation depth 1): rejects the new
       delegation if creating it would form a two-hop chain, checked in
       *both* possible creation orders (the invariant must hold
       regardless of which delegation in a would-be chain is created
       first) -

       - the proposed *delegator* (`delegator_actor_id`) already holds
         someone else's delegated authority for this same
         `(scope_type, scope_id)` (`delegation_store.find_active_delegation_where_delegate`)
         - i.e. an active `A -> delegator_actor_id` already exists, and
           this call is the `delegator_actor_id -> delegate_actor_id`
           second hop (the ordering the task's own worked example -
           "create A->B active, then attempt B->C" - exercises); or
       - the proposed *delegate* (`delegate_actor_id`) is themselves
         already forwarding their vote onward as an active delegator for
         this same scope (`delegation_store.find_active_delegation_for`)
         - i.e. an active `delegate_actor_id -> C` already exists, and
           this call is the `A -> delegate_actor_id` first hop (the
           mirror-image creation order).

       Either match is rejected with `DelegationCycleError`
       (`DELEGATION_CYCLE`). Per the task's own judgment call (see
       README.md): this rejected attempt is NOT a state-changing action
       (no `Delegation` is created, no `delegation.*` domain event is
       emitted), but it IS audited - a rejected critical action is still
       politically significant (INV-04/INV-09) - as a lightweight,
       audit-only record classified under
       `delegation.cycle_detected`/`DELEGATION_CYCLE`.
    4. Prohibition #2 (scope conflict): enforced by
       `delegation_store.create` itself (`DelegationScopeConflictError`,
       `DELEGATION_SCOPE_CONFLICT`) - not duplicated here.

    Prohibition #3 (hidden indefinite delegation) and prohibition #4
    (snapshot immutability) are enforced elsewhere - see
    `Delegation.__post_init__` and `resolve_delegation_snapshot`/
    `storage.InMemoryDelegationSnapshotStore.save` respectively.
    """
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to create a delegation")

    if delegator_actor_id == delegate_actor_id:
        raise SelfDelegationError(
            f"delegator_actor_id and delegate_actor_id must differ (both are {delegator_actor_id})"
        )

    now = clock.now()

    upstream_violation = delegation_store.find_active_delegation_where_delegate(
        delegator_actor_id, scope_type, scope_id
    )
    downstream_violation = delegation_store.find_active_delegation_for(
        delegate_actor_id, scope_type, scope_id
    )
    depth_violation = upstream_violation if upstream_violation is not None else downstream_violation
    if depth_violation is not None:
        # Judgment call (see docstring above / README.md): audit the
        # rejected attempt even though nothing state-changing happened.
        attempted_payload = {
            "delegation_id": str(delegation_id),
            "delegator_actor_id": str(delegator_actor_id),
            "delegate_actor_id": str(delegate_actor_id),
            "scope_type": scope_type,
            "scope_id": str(scope_id),
            "conflicting_delegation_id": str(depth_violation.delegation_id),
        }
        reject_audit_event_id = event_id if event_id is not None else generate_uuid()
        append_audit_event(
            audit_store,
            AppendAuditEventRequest(
                audit_event_id=reject_audit_event_id,
                event_type="delegation.cycle_detected",
                occurred_at=now,
                actor_id=actor.actor_id,
                actor_type=actor.actor_type,
                target_type="delegation",
                target_id=delegation_id,
                action="create_rejected_depth_violation",
                reason_code="DELEGATION_CYCLE",
                policy_version=AUDIT_POLICY_VERSION,
                correlation_id=correlation_id,
                source_service=_SOURCE_SERVICE,
                before_hash="",
                after_hash=compute_payload_hash(attempted_payload),
            ),
            clock=clock,
        )
        raise DelegationCycleError(
            f"delegation {delegator_actor_id} -> {delegate_actor_id} for scope "
            f"{scope_type}:{scope_id} would exceed the maximum delegation depth "
            f"of 1 (ADR-009 item 9): conflicts with existing active delegation "
            f"{depth_violation.delegation_id}"
        )

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    delegation = Delegation(
        delegation_id=delegation_id,
        delegator_actor_id=delegator_actor_id,
        delegate_actor_id=delegate_actor_id,
        scope_type=scope_type,
        scope_id=scope_id,
        valid_from=valid_from,
        valid_until=valid_until,
        revocation_status=revocation_status,
        status=DelegationStatus.DRAFT,
    )
    stored = delegation_store.create(delegation)

    event = build_delegation_created_event(
        event_id=resolved_event_id,
        delegation=stored,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    audit_event = append_audit_event(
        audit_store,
        _delegation_audit_request(
            audit_event_id=event.event_id,
            event_type=event.event_type,
            delegation=stored,
            before_hash="",
            actor=actor,
            action="create",
            reason_code=_DELEGATION_STATUS_CHANGED,
            correlation_id=correlation_id,
            occurred_at=now,
        ),
        clock=clock,
    )
    return DelegationResult(delegation=stored, event=event, audit_event=audit_event)


def activate_delegation(
    delegation_store: DelegationStore,
    audit_store: AuditEventStore,
    *,
    delegation_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> DelegationResult:
    """`draft -> active` -> `delegation.activated`.

    Guards against activating an already-time-expired draft: if
    `valid_until` is set and `clock.now() >= valid_until`, raises
    `DelegationExpiredError` (`DELEGATION_EXPIRED`) rather than silently
    activating a delegation whose validity window has already closed."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to activate a delegation")

    delegation = delegation_store.get(delegation_id)
    if delegation is None:
        raise UnknownDelegationError(f"unknown delegation_id: {delegation_id}")

    now = clock.now()
    if delegation.valid_until is not None and now >= delegation.valid_until:
        raise DelegationExpiredError(
            f"delegation {delegation_id} valid_until "
            f"{delegation.valid_until.isoformat()} has already passed; cannot activate"
        )

    before_hash = compute_payload_hash(delegation_state_payload(delegation))
    updated = delegation.with_status(DelegationStatus.ACTIVE)
    stored = delegation_store.save(updated)

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    event = build_delegation_activated_event(
        event_id=resolved_event_id,
        delegation=stored,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    audit_event = append_audit_event(
        audit_store,
        _delegation_audit_request(
            audit_event_id=event.event_id,
            event_type=event.event_type,
            delegation=stored,
            before_hash=before_hash,
            actor=actor,
            action="activate",
            reason_code=_DELEGATION_STATUS_CHANGED,
            correlation_id=correlation_id,
            occurred_at=now,
        ),
        clock=clock,
    )
    return DelegationResult(delegation=stored, event=event, audit_event=audit_event)


def _simple_delegation_transition(
    delegation_store: DelegationStore,
    audit_store: AuditEventStore,
    *,
    delegation_id: UUID,
    target_status: DelegationStatus,
    action: str,
    build_event: Callable[..., EventEnvelope] | None,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None,
) -> DelegationResult:
    if not actor_is_authorized:
        raise PermissionDeniedError(f"actor is not authorized to {action} a delegation")

    delegation = delegation_store.get(delegation_id)
    if delegation is None:
        raise UnknownDelegationError(f"unknown delegation_id: {delegation_id}")

    now = clock.now()
    before_hash = compute_payload_hash(delegation_state_payload(delegation))
    updated = delegation.with_status(target_status)
    stored = delegation_store.save(updated)

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    event = None
    # No canon domain event exists for `suspend`/`unsuspend`/`mark_invalid`
    # (see README.md) - `event_type` here is only the audit record's own
    # `event_type` field in that case, not a real `EventEnvelope`'s.
    event_type = f"delegation.{action}"
    if build_event is not None:
        event = build_event(
            event_id=resolved_event_id,
            delegation=stored,
            actor=actor,
            correlation_id=correlation_id,
            causation_id=None,
            occurred_at=now,
        )
        event_type = event.event_type

    audit_event = append_audit_event(
        audit_store,
        _delegation_audit_request(
            audit_event_id=event.event_id if event is not None else resolved_event_id,
            event_type=event_type,
            delegation=stored,
            before_hash=before_hash,
            actor=actor,
            action=action,
            reason_code=_DELEGATION_STATUS_CHANGED,
            correlation_id=correlation_id,
            occurred_at=now,
        ),
        clock=clock,
    )
    return DelegationResult(delegation=stored, event=event, audit_event=audit_event)


def revoke_delegation(
    delegation_store: DelegationStore,
    audit_store: AuditEventStore,
    *,
    delegation_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> DelegationResult:
    """`active|suspended -> revoked` -> `delegation.revoked`."""
    return _simple_delegation_transition(
        delegation_store,
        audit_store,
        delegation_id=delegation_id,
        target_status=DelegationStatus.REVOKED,
        action="revoke",
        build_event=build_delegation_revoked_event,
        actor=actor,
        actor_is_authorized=actor_is_authorized,
        correlation_id=correlation_id,
        clock=clock,
        event_id=event_id,
    )


def expire_delegation(
    delegation_store: DelegationStore,
    audit_store: AuditEventStore,
    *,
    delegation_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> DelegationResult:
    """`active -> expired` -> `delegation.expired`."""
    return _simple_delegation_transition(
        delegation_store,
        audit_store,
        delegation_id=delegation_id,
        target_status=DelegationStatus.EXPIRED,
        action="expire",
        build_event=build_delegation_expired_event,
        actor=actor,
        actor_is_authorized=actor_is_authorized,
        correlation_id=correlation_id,
        clock=clock,
        event_id=event_id,
    )


def suspend_delegation(
    delegation_store: DelegationStore,
    audit_store: AuditEventStore,
    *,
    delegation_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> DelegationResult:
    """`active -> suspended`. Canon section 20.11 names no domain event
    for this transition - persist+audit only (`event` is `None` on the
    returned `DelegationResult`), mirroring
    `epd2_voting_service.application.submit_ballot_for_configuration_review`'s
    own "no event for this step" precedent."""
    return _simple_delegation_transition(
        delegation_store,
        audit_store,
        delegation_id=delegation_id,
        target_status=DelegationStatus.SUSPENDED,
        action="suspend",
        build_event=None,
        actor=actor,
        actor_is_authorized=actor_is_authorized,
        correlation_id=correlation_id,
        clock=clock,
        event_id=event_id,
    )


def unsuspend_delegation(
    delegation_store: DelegationStore,
    audit_store: AuditEventStore,
    *,
    delegation_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> DelegationResult:
    """`suspended -> active`. No canon domain event for this transition
    either - persist+audit only, same shape as `suspend_delegation`."""
    return _simple_delegation_transition(
        delegation_store,
        audit_store,
        delegation_id=delegation_id,
        target_status=DelegationStatus.ACTIVE,
        action="unsuspend",
        build_event=None,
        actor=actor,
        actor_is_authorized=actor_is_authorized,
        correlation_id=correlation_id,
        clock=clock,
        event_id=event_id,
    )


def mark_delegation_invalid(
    delegation_store: DelegationStore,
    audit_store: AuditEventStore,
    *,
    delegation_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> DelegationResult:
    """`draft|active -> invalid`. No canon domain event for this
    transition - persist+audit only, same shape as `suspend_delegation`.
    Unlike `epd2_voting_service`'s structurally-unreachable
    `BallotStatus.INVALIDATED` (ADR-009 item 14), this transition IS a
    real, callable command here - canon simply gives it no event name."""
    return _simple_delegation_transition(
        delegation_store,
        audit_store,
        delegation_id=delegation_id,
        target_status=DelegationStatus.INVALID,
        action="mark_invalid",
        build_event=None,
        actor=actor,
        actor_is_authorized=actor_is_authorized,
        correlation_id=correlation_id,
        clock=clock,
        event_id=event_id,
    )


def resolve_active_delegate(
    delegation_store: DelegationStore,
    *,
    delegator_actor_id: UUID,
    scope_type: str,
    scope_id: UUID,
    direct_voters: frozenset[UUID],
) -> UUID | None:
    """ADR-009 item 10 ("direct vote overrides delegation"): returns
    `None` if `delegator_actor_id` is itself in `direct_voters` (the
    delegator's own direct vote takes precedence - do not use any
    delegate), else returns the resolved `delegate_actor_id` from the
    delegator's *active* `Delegation` for this `(scope_type, scope_id)` if
    one exists, else `None` (no active delegation - the delegator simply
    contributes no weight to anyone).

    A pure query: no state change, no event, no audit entry - this is the
    building block `resolve_delegation_snapshot` calls once per delegator.
    """
    if delegator_actor_id in direct_voters:
        return None
    delegation = delegation_store.find_active_delegation_for(
        delegator_actor_id, scope_type, scope_id
    )
    if delegation is None:
        return None
    return delegation.delegate_actor_id


def resolve_delegation_snapshot(
    delegation_store: DelegationStore,
    snapshot_store: DelegationSnapshotStore,
    audit_store: AuditEventStore,
    *,
    delegation_snapshot_id: UUID | None = None,
    ballot_id: UUID,
    policy_version: int,
    delegator_actor_ids: frozenset[UUID],
    scope_type: str,
    scope_id: UUID,
    direct_voters: frozenset[UUID],
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> DelegationSnapshotResult:
    """Resolve one `DelegationSnapshot` for `ballot_id` -> `delegation.snapshot_created`.

    For each delegator in `delegator_actor_ids`, calls
    `resolve_active_delegate`; delegators who voted directly or have no
    active delegation contribute no weight to anyone. Weights are
    accumulated per resolved delegate into `resolved_weights`.

    As a defensive second layer beyond `create_delegation`'s own depth-1
    guard (ADR-009 item 9: "a hard cap in addition to, not instead of,
    `delegation.cycle_detected`/`DELEGATION_CYCLE` cycle detection - the
    two are complementary, not redundant"), this function also checks,
    for every resolved delegate, whether *that delegate* is themselves
    currently an active delegator for the same scope. Under the depth-1
    invariant this should never be true (it would mean a depth-2 chain
    slipped past `create_delegation`'s own guard) - if it somehow is, the
    contribution is excluded from `resolved_weights` and a diagnostic
    string is appended to `cycle_records`, rather than silently
    double-counting or crashing. Full multi-hop cycle detection is future
    scope (see README.md) once the depth cap is ever raised past 1; for
    depth 1, these two checks together are the complete guard.

    Idempotent by `(ballot_id, input_hash)` (see
    `domain.compute_delegation_snapshot_input_hash` /
    `storage.InMemoryDelegationSnapshotStore.save`): a replay with
    identical inputs and identical resolution content returns the
    original stored snapshot; a replay with the same inputs but different
    resolution content (e.g. delegation state changed between calls)
    raises `SnapshotFrozenError` - canon prohibition #4.

    This function's parameter list is a superset of the minimal
    resolution-only signature the task description sketches
    (`delegation_store, *, ballot_id, policy_version, delegator_actor_ids,
    scope_type, scope_id, direct_voters, clock`) - it additionally takes
    `snapshot_store`/`audit_store`/`actor`/`actor_is_authorized`/
    `correlation_id`/`event_id`, because this function IS the
    `resolve_delegation_snapshot` *command* canon section 20.11 names
    (which, like every command in this service, must authorize, persist,
    emit its event, and append an audit entry - CT-00-07). See
    README.md's "one function, two descriptions" note.
    """
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to resolve a delegation snapshot")

    now = clock.now()
    input_hash = compute_delegation_snapshot_input_hash(
        ballot_id=ballot_id,
        policy_version=policy_version,
        scope_type=scope_type,
        scope_id=scope_id,
        delegator_actor_ids=delegator_actor_ids,
        direct_voters=direct_voters,
    )

    resolved_weights: dict[UUID, int] = {}
    cycle_records: list[str] = []
    for delegator_actor_id in sorted(delegator_actor_ids, key=str):
        delegate_actor_id = resolve_active_delegate(
            delegation_store,
            delegator_actor_id=delegator_actor_id,
            scope_type=scope_type,
            scope_id=scope_id,
            direct_voters=direct_voters,
        )
        if delegate_actor_id is None:
            continue

        downstream = delegation_store.find_active_delegation_for(
            delegate_actor_id, scope_type, scope_id
        )
        if downstream is not None:
            cycle_records.append(
                f"DELEGATION_CYCLE: delegate {delegate_actor_id} for delegator "
                f"{delegator_actor_id} is itself an active delegator for scope "
                f"{scope_type}:{scope_id} (depth > 1); contribution excluded"
            )
            continue

        resolved_weights[delegate_actor_id] = resolved_weights.get(delegate_actor_id, 0) + 1

    snapshot_hash = compute_delegation_snapshot_hash(
        input_hash=input_hash,
        resolved_weights=resolved_weights,
        cycle_records=tuple(cycle_records),
    )
    candidate = DelegationSnapshot(
        delegation_snapshot_id=(
            delegation_snapshot_id if delegation_snapshot_id is not None else generate_uuid()
        ),
        ballot_id=ballot_id,
        policy_version=policy_version,
        created_at=now,
        input_hash=input_hash,
        resolved_weights=resolved_weights,
        cycle_records=tuple(cycle_records),
        snapshot_hash=snapshot_hash,
    )
    stored = snapshot_store.save(candidate)

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    event = build_delegation_snapshot_created_event(
        event_id=resolved_event_id,
        snapshot=stored,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=event.event_id,
            event_type=event.event_type,
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="delegation_snapshot",
            target_id=stored.delegation_snapshot_id,
            action="resolve_snapshot",
            reason_code=_DELEGATION_SNAPSHOT_CREATED,
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash="",
            after_hash=compute_payload_hash(delegation_snapshot_state_payload(stored)),
        ),
        clock=clock,
    )
    return DelegationSnapshotResult(snapshot=stored, event=event, audit_event=audit_event)
