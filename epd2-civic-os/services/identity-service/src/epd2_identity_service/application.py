"""Identity Service application layer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from epd2_audit_core.application import AppendAuditEventRequest, append_audit_event
from epd2_audit_core.domain import AuditEvent
from epd2_audit_core.storage import AuditEventStore
from epd2_core.clock import Clock
from epd2_core.event_envelope import ActorRef, EventEnvelope, compute_payload_hash
from epd2_core.identifiers import generate_uuid
from epd2_identity_service.domain import (
    CANONICAL_EVENT_FOR_TRANSITION,
    IdentityRecord,
    VerificationStatus,
    assert_transition_allowed,
)
from epd2_identity_service.events import build_identity_event, identity_record_payload
from epd2_identity_service.exceptions import UnknownIdentityRecordError
from epd2_identity_service.storage import IdentityRecordStore

#: Audit Core's own policy version for entries this service appends -
#: independent of the wire event schema version.
AUDIT_POLICY_VERSION = "1.0"
_SOURCE_SERVICE = "identity-service"
_TARGET_TYPE = "identity_record"

#: Audit reason_code by verification outcome, for `record_verification_result`.
#: See ADR-004 - VERIFIED/FAILED/EXPIRED reuse existing registry codes;
#: DUPLICATE_SUSPECTED/MANUAL_REVIEW_REQUIRED are new audit-only
#: classifications with no existing refusal code to reuse.
_AUDIT_REASON_FOR_OUTCOME: dict[VerificationStatus, str] = {
    VerificationStatus.VERIFIED: "IDENTITY_VERIFIED",
    VerificationStatus.FAILED: "IDENTITY_NOT_VERIFIED",
    VerificationStatus.EXPIRED: "IDENTITY_VERIFICATION_EXPIRED",
    VerificationStatus.DUPLICATE_SUSPECTED: "IDENTITY_DUPLICATE_SUSPECTED",
    VerificationStatus.MANUAL_REVIEW_REQUIRED: "IDENTITY_MANUAL_REVIEW_REQUIRED",
}


class PermissionDeniedError(PermissionError):
    reason_code = "PERMISSION_DENIED"


@dataclass(frozen=True, slots=True)
class CommandResult:
    record: IdentityRecord
    event: EventEnvelope | None
    audit_event: AuditEvent | None = None


def start_identity_verification(
    store: IdentityRecordStore,
    audit_store: AuditEventStore,
    *,
    account_id: UUID,
    verification_provider: str,
    verification_level: str,
    country: str,
    provider_reference: str,
    actor: ActorRef,
    correlation_id: UUID,
    clock: Clock,
) -> CommandResult:
    """Create a new `IdentityRecord` in `pending` status and emit
    `identity.verification_started`."""
    now = clock.now()
    record = IdentityRecord(
        identity_record_id=generate_uuid(),
        account_id=account_id,
        verification_provider=verification_provider,
        verification_level=verification_level,
        verification_status=VerificationStatus.PENDING,
        verified_at=None,
        expires_at=None,
        country=country,
        duplicate_check_status="not_checked",
        provider_reference=provider_reference,
    )
    store.save(record)
    event = build_identity_event(
        event_id=generate_uuid(),
        event_type="identity.verification_started",
        record=record,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    # CT-00-07 / INV-04: starting an identity verification process is a
    # critical action for this service's own owned entity.
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=event.event_id,
            event_type=event.event_type,
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type=_TARGET_TYPE,
            target_id=record.identity_record_id,
            action="start_verification",
            reason_code="IDENTITY_VERIFICATION_STARTED",
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash="",
            after_hash=compute_payload_hash(identity_record_payload(record)),
        ),
        clock=clock,
    )
    return CommandResult(record=record, event=event, audit_event=audit_event)


def record_verification_result(
    store: IdentityRecordStore,
    audit_store: AuditEventStore,
    *,
    identity_record_id: UUID,
    outcome: VerificationStatus,
    expires_at: datetime | None,
    duplicate_check_status: str | None,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    causation_id: UUID | None,
    clock: Clock,
) -> CommandResult:
    """Record the outcome of a verification attempt (CT-00-06: rejected if
    the actor is not authorized)."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to record a verification result")

    record = store.get(identity_record_id)
    if record is None:
        raise UnknownIdentityRecordError(f"unknown identity_record_id: {identity_record_id}")

    before_hash = compute_payload_hash(identity_record_payload(record))
    now = clock.now()
    previous_status = record.verification_status
    assert_transition_allowed(previous_status, outcome)
    updated = record.with_status(
        outcome,
        verified_at=now if outcome == VerificationStatus.VERIFIED else None,
        expires_at=expires_at,
        duplicate_check_status=duplicate_check_status,
    )
    store.save(updated)

    event_type = CANONICAL_EVENT_FOR_TRANSITION[(previous_status, outcome)]
    event = build_identity_event(
        event_id=generate_uuid(),
        event_type=event_type,
        record=updated,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=now,
    )
    # CT-00-07 / INV-04: recording a verification outcome is a critical
    # action. `reason_code` is classified by outcome (ADR-004).
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=event.event_id,
            event_type=event.event_type,
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type=_TARGET_TYPE,
            target_id=updated.identity_record_id,
            action="record_verification_result",
            reason_code=_AUDIT_REASON_FOR_OUTCOME[outcome],
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash=before_hash,
            after_hash=compute_payload_hash(identity_record_payload(updated)),
        ),
        clock=clock,
    )
    return CommandResult(record=updated, event=event, audit_event=audit_event)


def revoke_verification(
    store: IdentityRecordStore,
    audit_store: AuditEventStore,
    *,
    identity_record_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    causation_id: UUID | None,
    clock: Clock,
) -> CommandResult:
    """Explicitly revoke a `verified` record. Per ADR-002, this emits the
    canonical `identity.verification_expired` event (canon has no separate
    revocation event) - the audit trail's `reason_code` still records this
    distinctly as a revocation, not a natural expiry
    (`IDENTITY_VERIFICATION_REVOKED`, see ADR-004).
    """
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to revoke a verification")

    record = store.get(identity_record_id)
    if record is None:
        raise UnknownIdentityRecordError(f"unknown identity_record_id: {identity_record_id}")

    before_hash = compute_payload_hash(identity_record_payload(record))
    assert_transition_allowed(record.verification_status, VerificationStatus.EXPIRED)
    updated = record.with_status(VerificationStatus.EXPIRED)
    store.save(updated)

    now = clock.now()
    event = build_identity_event(
        event_id=generate_uuid(),
        event_type=CANONICAL_EVENT_FOR_TRANSITION[
            (record.verification_status, VerificationStatus.EXPIRED)
        ],
        record=updated,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
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
            target_type=_TARGET_TYPE,
            target_id=updated.identity_record_id,
            action="revoke_verification",
            reason_code="IDENTITY_VERIFICATION_REVOKED",
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash=before_hash,
            after_hash=compute_payload_hash(identity_record_payload(updated)),
        ),
        clock=clock,
    )
    return CommandResult(record=updated, event=event, audit_event=audit_event)
