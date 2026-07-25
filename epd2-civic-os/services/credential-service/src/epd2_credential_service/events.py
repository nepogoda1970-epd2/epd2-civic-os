"""Canonical events emitted by Credential Service (canon section 20.4,
via ADR-002 for the "validated" name resolution).

No payload here ever includes `issuance_reference` or any identity field
- see `tests/contract/test_identity_leakage.py`.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from epd2_core.event_envelope import ActorRef, EventEnvelope, SubjectRef, build_event_envelope
from epd2_credential_service.domain import ParticipationCredential

EVENT_VERSION = "1.0"
SUPPORTED_MAJOR_VERSIONS = frozenset({1})


def credential_state_payload(credential: ParticipationCredential) -> dict[str, object]:
    """Minimal, canonically-hashable event-payload snapshot of a
    credential's state, used for `credential.issued`/`credential.revoked`
    payloads (this module). Deliberately excludes fields not needed by an
    event consumer (`issued_at`, `valid_from`, `usage_limit`,
    `usage_counter`, `revocation_status`, `issuer_signature`) - see
    `credential_full_state_payload` for Audit Core's `before_hash`/
    `after_hash`, which needs the complete state to be a meaningful
    tamper-evidence check."""
    return {
        "credential_id": str(credential.credential_id),
        "credential_type": credential.credential_type.value,
        "scope_type": credential.scope_type,
        "scope_id": str(credential.scope_id),
        "status": credential.status.value,
        "credential_version": credential.credential_version,
        "rule_version": credential.rule_version,
        "eligibility_snapshot_digest": credential.eligibility_snapshot_digest,
        "expires_at": credential.expires_at.isoformat(),
    }


def credential_full_state_payload(credential: ParticipationCredential) -> dict[str, object]:
    """Full, canonically-hashable snapshot of a credential's own state,
    used for Audit Core's `before_hash`/`after_hash` (`application.py`).
    Distinct from `credential_state_payload` (the minimal event payload
    above) so a change to a field the event payload omits - e.g.
    `usage_counter` incrementing on use - still changes the audit hash."""
    payload = credential_state_payload(credential)
    payload.update(
        {
            "issued_at": credential.issued_at.isoformat(),
            "valid_from": credential.valid_from.isoformat(),
            "usage_limit": credential.usage_limit,
            "usage_counter": credential.usage_counter,
            "revocation_status": credential.revocation_status,
            "issuer_signature": credential.issuer_signature,
        }
    )
    return payload


def build_credential_issued_event(
    *,
    event_id: UUID,
    credential: ParticipationCredential,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return build_event_envelope(
        event_id=event_id,
        event_type="credential.issued",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="credential-service",
        actor=actor,
        subject=SubjectRef(
            subject_type="participation_credential", subject_id=credential.credential_id
        ),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=credential_state_payload(credential),
    )


def build_credential_revoked_event(
    *,
    event_id: UUID,
    credential: ParticipationCredential,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return build_event_envelope(
        event_id=event_id,
        event_type="credential.revoked",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="credential-service",
        actor=actor,
        subject=SubjectRef(
            subject_type="participation_credential", subject_id=credential.credential_id
        ),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=credential_state_payload(credential),
    )


def build_validation_failed_event(
    *,
    event_id: UUID,
    credential_id: UUID,
    reason_codes: tuple[str, ...],
    actor: ActorRef,
    correlation_id: UUID,
    occurred_at: datetime,
) -> EventEnvelope:
    payload = {
        "credential_id": str(credential_id),
        "reason_codes": list(reason_codes),
    }
    return build_event_envelope(
        event_id=event_id,
        event_type="credential.validation_failed",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="credential-service",
        actor=actor,
        subject=SubjectRef(subject_type="participation_credential", subject_id=credential_id),
        correlation_id=correlation_id,
        causation_id=None,
        payload=payload,
    )
