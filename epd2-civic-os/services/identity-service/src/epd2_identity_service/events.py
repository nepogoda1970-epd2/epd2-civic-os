"""Canonical events emitted by Identity Service (canon section 20.2, via
ADR-002 for the revocation mapping)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from epd2_core.event_envelope import ActorRef, EventEnvelope, SubjectRef, build_event_envelope
from epd2_identity_service.domain import IdentityRecord

EVENT_VERSION = "1.0"
SUPPORTED_MAJOR_VERSIONS = frozenset({1})


def identity_record_payload(record: IdentityRecord) -> dict[str, object]:
    """Full, canonically-hashable snapshot of an `IdentityRecord`'s own
    state, used for Audit Core's `before_hash`/`after_hash`
    (`application.py`). Deliberately more complete than the minimal event
    payload below - Audit Core's before/after hashes exist to prove
    tamper-evidence over this service's own owned entity (canon section
    7.3), which is not the "identity data on a credential" case the
    identity-leakage rule (pack section 5.2) forbids."""
    return {
        "identity_record_id": str(record.identity_record_id),
        "account_id": str(record.account_id),
        "verification_provider": record.verification_provider,
        "verification_level": record.verification_level,
        "verification_status": record.verification_status.value,
        "verified_at": record.verified_at.isoformat() if record.verified_at else None,
        "expires_at": record.expires_at.isoformat() if record.expires_at else None,
        "country": record.country,
        "duplicate_check_status": record.duplicate_check_status,
        "provider_reference": record.provider_reference,
    }


def build_identity_event(
    *,
    event_id: UUID,
    event_type: str,
    record: IdentityRecord,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    payload = {
        "identity_record_id": str(record.identity_record_id),
        "account_id": str(record.account_id),
        "verification_status": record.verification_status.value,
        "verification_level": record.verification_level,
    }
    return build_event_envelope(
        event_id=event_id,
        event_type=event_type,
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="identity-service",
        actor=actor,
        subject=SubjectRef(subject_type="identity_record", subject_id=record.identity_record_id),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=payload,
    )
