"""Canonical events emitted by Delegation Service (canon section 20.11):
`delegation.created`, `delegation.activated`, `delegation.revoked`,
`delegation.expired`, `delegation.cycle_detected`,
`delegation.snapshot_created`. Canon lists exactly these six - no others
are invented here (per the task's instruction not to invent beyond canon
section 20.11).

`suspend`/`unsuspend`/mark-`invalid` transitions have no corresponding
canon event name, so no builder exists for them here - see
`application.py`/README.md ("persist + audit only, no event").
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from epd2_core.event_envelope import ActorRef, EventEnvelope, SubjectRef, build_event_envelope
from epd2_delegation_service.domain import Delegation, DelegationSnapshot

EVENT_VERSION = "1.0"
SUPPORTED_MAJOR_VERSIONS = frozenset({1})


def delegation_state_payload(delegation: Delegation) -> dict[str, object]:
    """Canonically-hashable snapshot of a `Delegation`'s own state, used
    both for every `delegation.*` event payload and for Audit Core's
    `before_hash`/`after_hash` (`application.py`)."""
    return {
        "delegation_id": str(delegation.delegation_id),
        "delegator_actor_id": str(delegation.delegator_actor_id),
        "delegate_actor_id": str(delegation.delegate_actor_id),
        "scope_type": delegation.scope_type,
        "scope_id": str(delegation.scope_id),
        "valid_from": delegation.valid_from.isoformat(),
        "valid_until": delegation.valid_until.isoformat() if delegation.valid_until else None,
        "revocation_status": delegation.revocation_status,
        "status": delegation.status.value,
    }


def delegation_snapshot_state_payload(snapshot: DelegationSnapshot) -> dict[str, object]:
    """Canonically-hashable snapshot of a `DelegationSnapshot`'s own
    state, used both for the `delegation.snapshot_created` event payload
    and for Audit Core's `after_hash`."""
    return {
        "delegation_snapshot_id": str(snapshot.delegation_snapshot_id),
        "ballot_id": str(snapshot.ballot_id),
        "policy_version": snapshot.policy_version,
        "created_at": snapshot.created_at.isoformat(),
        "input_hash": snapshot.input_hash,
        "resolved_weights": {str(k): v for k, v in snapshot.resolved_weights.items()},
        "cycle_records": list(snapshot.cycle_records),
        "snapshot_hash": snapshot.snapshot_hash,
    }


def _build_delegation_event(
    *,
    event_type: str,
    event_id: UUID,
    delegation: Delegation,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return build_event_envelope(
        event_id=event_id,
        event_type=event_type,
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="delegation-service",
        actor=actor,
        subject=SubjectRef(subject_type="delegation", subject_id=delegation.delegation_id),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=delegation_state_payload(delegation),
    )


def build_delegation_created_event(
    *,
    event_id: UUID,
    delegation: Delegation,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return _build_delegation_event(
        event_type="delegation.created",
        event_id=event_id,
        delegation=delegation,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_delegation_activated_event(
    *,
    event_id: UUID,
    delegation: Delegation,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return _build_delegation_event(
        event_type="delegation.activated",
        event_id=event_id,
        delegation=delegation,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_delegation_revoked_event(
    *,
    event_id: UUID,
    delegation: Delegation,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return _build_delegation_event(
        event_type="delegation.revoked",
        event_id=event_id,
        delegation=delegation,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_delegation_expired_event(
    *,
    event_id: UUID,
    delegation: Delegation,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return _build_delegation_event(
        event_type="delegation.expired",
        event_id=event_id,
        delegation=delegation,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_delegation_snapshot_created_event(
    *,
    event_id: UUID,
    snapshot: DelegationSnapshot,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return build_event_envelope(
        event_id=event_id,
        event_type="delegation.snapshot_created",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="delegation-service",
        actor=actor,
        subject=SubjectRef(
            subject_type="delegation_snapshot", subject_id=snapshot.delegation_snapshot_id
        ),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=delegation_snapshot_state_payload(snapshot),
    )
