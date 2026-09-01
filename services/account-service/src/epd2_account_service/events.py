"""Canonical events emitted by Account Service.

Event names come from canon section 20.1, not this pack's own suggested
names where they differ (ADR-002). Envelope shape is canon section 21,
via `epd2_core.event_envelope`.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from epd2_account_service.domain import Account
from epd2_core.event_envelope import ActorRef, EventEnvelope, SubjectRef, build_event_envelope

EVENT_VERSION = "1.0"
SUPPORTED_MAJOR_VERSIONS = frozenset({1})


def account_state_payload(account: Account) -> dict[str, object]:
    """Full, canonically-hashable snapshot of an `Account`'s own state,
    used for Audit Core's `before_hash`/`after_hash` (`application.py`).
    `Account` has no PII fields at all (canon section 7.2), so this can
    safely be the full dataclass, unlike the minimal event payload below."""
    return {
        "account_id": str(account.account_id),
        "email_status": account.email_status,
        "mfa_status": account.mfa_status,
        "account_status": account.account_status.value,
        "created_at": account.created_at.isoformat(),
        "last_login_at": account.last_login_at.isoformat() if account.last_login_at else None,
        "locale": account.locale,
        "terms_version": account.terms_version,
        "consent_status": account.consent_status,
    }


def build_account_event(
    *,
    event_id: UUID,
    event_type: str,
    account: Account,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """Build a canonical envelope for any Account Service event. `event_type`
    must be one of the names `domain.CANONICAL_EVENT_FOR_TRANSITION` maps
    to, or `"account.created"` - callers (application.py) are responsible
    for only calling this with a canonical name.
    """
    payload = {
        "account_id": str(account.account_id),
        "account_status": account.account_status.value,
    }
    return build_event_envelope(
        event_id=event_id,
        event_type=event_type,
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="account-service",
        actor=actor,
        subject=SubjectRef(subject_type="account", subject_id=account.account_id),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=payload,
    )
