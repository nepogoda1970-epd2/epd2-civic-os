"""Canonical events emitted by Identity Service (canon section 20.2, via
ADR-002 for the revocation mapping)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from epd2_core.event_envelope import ActorRef, EventEnvelope, SubjectRef, build_event_envelope
from epd2_identity_service.domain import AuthenticationContext, IdentityRecord

EVENT_VERSION = "1.0"
SUPPORTED_MAJOR_VERSIONS = frozenset({1})


def identity_record_payload(record: IdentityRecord) -> dict[str, object]:
    """Full, canonically-hashable snapshot of an `IdentityRecord`'s own
    state, used for Audit Core's `before_hash`/`after_hash`
    (`application.py`). Deliberately more complete than the minimal event
    payload below - Audit Core's before/after hashes exist to prove
    tamper-evidence over this service's own owned entity (canon section
    7.3), which is not the "identity data on a credential" case the
    identity-leakage rule (pack section 5.2) forbids.

    Includes canon 19d.2's eight additive fields (PACK-07) so a
    modification to any of them is tamper-evident too - this is still
    only ever used for Audit Core's own before/after hash, never
    broadcast on the wire event below.
    """
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
        "date_of_birth": record.date_of_birth.isoformat() if record.date_of_birth else None,
        "citizenship_status": list(record.citizenship_status),
        "residence_status": dict(record.residence_status) if record.residence_status else None,
        "identity_assurance_level": record.identity_assurance_level.value,
        "identity_scheme": record.identity_scheme,
        "attribute_verification_level": record.attribute_verification_level,
        "attribute_verified_at": (
            record.attribute_verified_at.isoformat() if record.attribute_verified_at else None
        ),
        "attribute_valid_until": (
            record.attribute_valid_until.isoformat() if record.attribute_valid_until else None
        ),
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
    """Deliberately minimal payload - never includes any of canon
    19d.2's identity/attribute fields (`date_of_birth`,
    `citizenship_status`, `residence_status`, `identity_scheme`,
    `attribute_*`), matching this project's identity-leakage-minimization
    discipline (pack section 5.2) and PACK-07's own task 11 boundary:
    consumers of identity-service events get only verification-lifecycle
    facts, never raw identity attributes."""
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


def authentication_context_payload(context: AuthenticationContext) -> dict[str, object]:
    """Full, canonically-hashable snapshot of an `AuthenticationContext`,
    used for Audit Core's before/after hash."""
    return {
        "authentication_context_id": str(context.authentication_context_id),
        "account_id": str(context.account_id),
        "authentication_method": context.authentication_method,
        "authentication_assurance_level": context.authentication_assurance_level.value,
        "session_authenticated_at": context.session_authenticated_at.isoformat(),
        "provider_reference": context.provider_reference,
        "step_up_completed_at": (
            context.step_up_completed_at.isoformat() if context.step_up_completed_at else None
        ),
    }


def build_authentication_context_event(
    *,
    event_id: UUID,
    event_type: str,
    context: AuthenticationContext,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """Minimal payload - never includes `provider_reference` (an opaque
    infrastructure reference, not a business fact any consumer needs) or
    any `IdentityRecord` field."""
    payload = {
        "authentication_context_id": str(context.authentication_context_id),
        "account_id": str(context.account_id),
        "authentication_assurance_level": context.authentication_assurance_level.value,
    }
    return build_event_envelope(
        event_id=event_id,
        event_type=event_type,
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="identity-service",
        actor=actor,
        subject=SubjectRef(
            subject_type="authentication_context",
            subject_id=context.authentication_context_id,
        ),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=payload,
    )
