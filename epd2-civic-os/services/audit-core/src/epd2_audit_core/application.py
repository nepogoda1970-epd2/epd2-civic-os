"""Audit Core's application layer: the single `append` command plus the
read operations. This is the only way any other service's critical action
becomes durable, tamper-evident history (INV-04, CT-00-07).
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from uuid import UUID

from epd2_audit_core.domain import AuditEvent
from epd2_audit_core.exceptions import AuditEventConflictError
from epd2_audit_core.hash_chain import compute_event_hash
from epd2_audit_core.storage import AuditEventStore, ChainVerificationResult
from epd2_core.clock import Clock


@dataclass(frozen=True, slots=True)
class AppendAuditEventRequest:
    """Input to `append_audit_event`. `audit_event_id` should be a stable,
    caller-generated UUID (typically derived from the domain event's own
    `event_id`) so retried calls are idempotent (CT-00-04).
    """

    audit_event_id: UUID
    event_type: str
    occurred_at: datetime
    actor_id: UUID
    actor_type: str
    target_type: str
    target_id: UUID
    action: str
    reason_code: str
    policy_version: str
    correlation_id: UUID
    source_service: str
    before_hash: str = ""
    after_hash: str = ""


def _matches_existing(request: AppendAuditEventRequest, existing: AuditEvent) -> bool:
    """Compare only the caller-controlled fields of `request` against
    `existing` - NOT `recorded_at`/`previous_event_hash`/`event_hash`,
    which depend on when and where in the chain the event was appended,
    not on its logical content. Chain position must never affect whether
    a repeated request is considered identical (see the idempotency bug
    this fixes: naively recomputing `previous_event_hash` from the
    store's *current* head on every call makes a true replay look like a
    conflict once the head has moved on).
    """
    return (
        request.event_type == existing.event_type
        and request.occurred_at == existing.occurred_at
        and request.actor_id == existing.actor_id
        and request.actor_type == existing.actor_type
        and request.target_type == existing.target_type
        and request.target_id == existing.target_id
        and request.action == existing.action
        and request.reason_code == existing.reason_code
        and request.policy_version == existing.policy_version
        and request.correlation_id == existing.correlation_id
        and request.source_service == existing.source_service
        and request.before_hash == existing.before_hash
        and request.after_hash == existing.after_hash
    )


def append_audit_event(
    store: AuditEventStore,
    request: AppendAuditEventRequest,
    *,
    clock: Clock,
) -> AuditEvent:
    """Append a new `AuditEvent` built from `request`.

    Idempotent: an identical repeat of the same `audit_event_id` returns
    the existing record without touching the chain again; a repeat with
    the same id but different content raises `AuditEventConflictError`.
    The identity check happens before any new hash is computed, so it is
    independent of how far the chain has moved since the original append.
    """
    existing = store.get_by_event_id(request.audit_event_id)
    if existing is not None:
        if _matches_existing(request, existing):
            return existing
        raise AuditEventConflictError(
            f"audit_event_id {request.audit_event_id} already recorded with different content"
        )

    previous_hash = store.head_hash()
    # Two-step construction: build with a placeholder event_hash, compute
    # the real hash over every other field plus previous_event_hash, then
    # rebuild with the final hash - AuditEvent is immutable (frozen), so
    # the hash cannot be patched in after construction.
    provisional = AuditEvent(
        audit_event_id=request.audit_event_id,
        event_type=request.event_type,
        occurred_at=request.occurred_at,
        recorded_at=clock.now(),
        actor_id=request.actor_id,
        actor_type=request.actor_type,
        target_type=request.target_type,
        target_id=request.target_id,
        action=request.action,
        reason_code=request.reason_code,
        policy_version=request.policy_version,
        before_hash=request.before_hash,
        after_hash=request.after_hash,
        correlation_id=request.correlation_id,
        source_service=request.source_service,
        previous_event_hash=previous_hash,
        event_hash="pending",
    )
    final_hash = compute_event_hash(provisional)
    final_event = replace(provisional, event_hash=final_hash)
    return store.append(final_event)


def get_by_event_id(store: AuditEventStore, audit_event_id: UUID) -> AuditEvent | None:
    return store.get_by_event_id(audit_event_id)


def list_by_aggregate(
    store: AuditEventStore, target_type: str, target_id: UUID
) -> tuple[AuditEvent, ...]:
    return store.list_by_aggregate(target_type, target_id)


def verify_chain(store: AuditEventStore) -> ChainVerificationResult:
    return store.verify_chain()


def list_by_target_types(
    store: AuditEventStore, target_types: frozenset[str]
) -> tuple[AuditEvent, ...]:
    """Return every recorded event whose `target_type` is in
    `target_types`, in append (chain) order.

    Additive, read-only (PACK-04, ADR-012 item 4): the one new Audit Core
    interface this pack's own ADR anticipated needing.
    `epd2_transparency_service.application.generate_audit_export_package`
    is this function's only caller — used to build an
    `AuditExportPackage.chain_proof` (canon section 19a.2). Does not
    change any existing function's signature or behavior.
    """
    return tuple(event for event in store.list_all() if event.target_type in target_types)
