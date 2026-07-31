"""PACK-15 voting-side event builders on PACK-13's canonical envelope.

Every payload here is checked against `FORBIDDEN_FIELD_NAMES` before an
envelope can exist, so a credential event structurally cannot carry an
assertion reference, a nonce, a pseudonym or any identity field.

`correlation_id` chains **begin** on this side. One minted on the identity
side is never accepted here and never echoed back: a chain that spans the
boundary is the link (ADR-090).
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any
from uuid import UUID, uuid5

from epd2_core.event_envelope import ActorRef, EventEnvelope, SubjectRef, build_event_envelope
from epd2_credential_service.voting_credentials import (
    CredentialRedemption,
    CredentialReplayRecord,
    VotingCredential,
    assert_no_forbidden_credential_fields,
)

EVENT_VERSION = "1.0"
SUPPORTED_MAJOR_VERSIONS = frozenset({1})
PRODUCER = "credential-service"

CREDENTIAL_REQUESTED = "voting_credential.requested"
CREDENTIAL_QUEUED = "voting_credential.queued"
CREDENTIAL_ISSUED = "voting_credential.issued"
CREDENTIAL_REVOKED = "voting_credential.revoked"
CREDENTIAL_EXPIRED = "voting_credential.expired"
CREDENTIAL_REDEEMED = "voting_credential.redeemed"
CREDENTIAL_REPLAY_REJECTED = "voting_credential.replay_rejected"
DUPLICATE_ISSUANCE_REJECTED = "voting_credential.duplicate_issuance_rejected"
CREDENTIAL_MINTING_DELAYED = "voting_credential.minting_delayed"
DELIVERY_CHANNEL_REFUSED = "voting_credential.delivery_channel_refused"

VOTING_CREDENTIAL_EVENT_TYPES: tuple[str, ...] = (
    CREDENTIAL_REQUESTED,
    CREDENTIAL_QUEUED,
    CREDENTIAL_ISSUED,
    CREDENTIAL_REVOKED,
    CREDENTIAL_EXPIRED,
    CREDENTIAL_REDEEMED,
    CREDENTIAL_REPLAY_REJECTED,
    DUPLICATE_ISSUANCE_REJECTED,
    CREDENTIAL_MINTING_DELAYED,
    DELIVERY_CHANNEL_REFUSED,
)

#: A fixed, non-identifying actor for the issuer's own acts. The voting
#: side has no participant to attribute an act to, and inventing one would
#: be the leak.
_ISSUER_ACTOR_NAMESPACE = UUID("6f1f1f7e-0a5a-4f6d-9a2f-8f4a1c3b7d21")


def issuer_actor() -> ActorRef:
    return ActorRef(
        actor_id=uuid5(_ISSUER_ACTOR_NAMESPACE, "voting-credential-issuer"),
        actor_type="service",
    )


def _coarsen(moment: datetime, granularity_seconds: int) -> datetime:
    epoch = int(moment.timestamp())
    return datetime.fromtimestamp(epoch - (epoch % granularity_seconds), tz=moment.tzinfo)


def _guard(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    assert_no_forbidden_credential_fields(payload)
    return payload


def build_credential_event(
    *,
    event_id: UUID,
    event_type: str,
    credential: VotingCredential,
    reason_code: str,
    granularity_seconds: int,
    correlation_id: UUID,
    occurred_at: datetime,
    causation_id: UUID | None = None,
) -> EventEnvelope:
    payload: dict[str, Any] = {
        "voting_credential_id": str(credential.voting_credential_id),
        "voting_context_reference": credential.voting_context_reference,
        "credential_type": credential.credential_type,
        "status": credential.status.value,
        "reason_code": reason_code,
        "expires_at_bucket": _coarsen(credential.expires_at, granularity_seconds).isoformat(),
    }
    if credential.revocation_reason is not None:
        payload["revocation_reason"] = credential.revocation_reason
    return build_event_envelope(
        event_id=event_id,
        event_type=event_type,
        event_version=EVENT_VERSION,
        occurred_at=_coarsen(occurred_at, granularity_seconds),
        producer=PRODUCER,
        actor=issuer_actor(),
        subject=SubjectRef(
            subject_type="voting_credential", subject_id=credential.voting_credential_id
        ),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=_guard(payload),
    )


def build_redemption_event(
    *,
    event_id: UUID,
    redemption: CredentialRedemption,
    correlation_id: UUID,
    causation_id: UUID | None = None,
) -> EventEnvelope:
    """A redemption event.

    It carries the redemption reference and the credential it consumed -
    both voting-side - and **never** the continuation capability, which is
    a secret handed to the client and not an audit fact.
    """
    payload: dict[str, Any] = {
        "redemption_reference": redemption.redemption_reference,
        "voting_credential_id": str(redemption.voting_credential_id),
        "voting_context_reference": redemption.voting_context_reference,
        "redeemed_at_bucket": redemption.redeemed_at_bucket.isoformat(),
    }
    return build_event_envelope(
        event_id=event_id,
        event_type=CREDENTIAL_REDEEMED,
        event_version=EVENT_VERSION,
        occurred_at=redemption.redeemed_at_bucket,
        producer=PRODUCER,
        actor=issuer_actor(),
        subject=SubjectRef(
            subject_type="voting_credential", subject_id=redemption.voting_credential_id
        ),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=_guard(payload),
    )


def build_replay_event(
    *,
    event_id: UUID,
    event_type: str,
    replay: CredentialReplayRecord,
    correlation_id: UUID,
    occurred_at: datetime,
    causation_id: UUID | None = None,
) -> EventEnvelope:
    """A replay event. Carries no holder, because none is knowable here."""
    payload: dict[str, Any] = {
        "replay_id": str(replay.replay_id),
        "voting_context_reference": replay.voting_context_reference,
        "reason_code": replay.reason_code,
        "timing_class": replay.timing_class,
    }
    return build_event_envelope(
        event_id=event_id,
        event_type=event_type,
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer=PRODUCER,
        actor=issuer_actor(),
        subject=SubjectRef(subject_type="voting_credential_replay", subject_id=replay.replay_id),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=_guard(payload),
    )
