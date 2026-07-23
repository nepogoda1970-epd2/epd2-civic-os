"""Canonical events emitted by Voting Service (canon section 20.10):
`ballot.created`, `ballot.configuration_locked`, `ballot.scheduled`,
`ballot.opened`, `ballot.paused`, `ballot.resumed`, `vote.received`,
`vote.validated`, `vote.rejected`, `vote.superseded`, `ballot.closed`,
`ballot.cancelled`.

`tally.*`/`result.published` belong to `tally-service`, not this
service - never built here. No `ballot.invalidated` builder exists in
this module at all (ADR-009 item 14, amended) - see README.md.

No payload here ever includes `credential_proof`'s referenced
credential's own identity-adjacent data, or
`encrypted_or_encoded_choice` in a form a governance audit trail
shouldn't retain unbounded - see `vote_envelope_state_payload` below for
the one deliberate exception (the encoded choice itself, needed for
Audit Core's own tamper-evidence hash) and its documented rationale.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from epd2_core.event_envelope import ActorRef, EventEnvelope, SubjectRef, build_event_envelope
from epd2_voting_service.domain import Ballot, VoteEnvelope

EVENT_VERSION = "1.0"
SUPPORTED_MAJOR_VERSIONS = frozenset({1})


def ballot_state_payload(ballot: Ballot) -> dict[str, object]:
    """Minimal, canonically-hashable event-payload snapshot of a
    `Ballot`'s state, used for every `ballot.*` event payload below."""
    return {
        "ballot_id": str(ballot.ballot_id),
        "space_id": str(ballot.space_id),
        "subject_type": ballot.subject_type,
        "subject_id": str(ballot.subject_id),
        "ballot_method": ballot.ballot_method.value,
        "status": ballot.status.value,
        "opens_at": ballot.opens_at.isoformat(),
        "closes_at": ballot.closes_at.isoformat(),
        "configuration_hash": ballot.configuration_hash,
    }


def ballot_full_state_payload(ballot: Ballot) -> dict[str, object]:
    """Full, canonically-hashable snapshot of a `Ballot`'s own state, used
    for Audit Core's `before_hash`/`after_hash` - distinct from
    `ballot_state_payload` so a change to a field the event payload omits
    still changes the audit hash."""
    payload = ballot_state_payload(ballot)
    payload.update(
        {
            "question": ballot.question,
            "secrecy_mode": ballot.secrecy_mode,
            "eligibility_rule_version": ballot.eligibility_rule_version,
            "delegation_policy_version": ballot.delegation_policy_version,
            "quorum_rule": ballot.quorum_rule,
            "threshold_rule": ballot.threshold_rule,
            "challenge_window_hours": ballot.challenge_window_hours,
        }
    )
    return payload


def vote_envelope_state_payload(envelope: VoteEnvelope) -> dict[str, object]:
    """Minimal, canonically-hashable event-payload snapshot of a
    `VoteEnvelope`'s state, used for every `vote.*` event payload below.

    Deliberately excludes `encrypted_or_encoded_choice` from the *event*
    payload (a domain event is broadcast more widely than an audit
    record) - only `integrity_hash` (already a one-way digest) travels on
    the wire. See `vote_envelope_full_state_payload` for Audit Core's
    `after_hash`, which does include the raw choice, since Audit Core's
    trail is this service's own tamper-evidence record, not a public
    broadcast."""
    return {
        "vote_envelope_id": str(envelope.vote_envelope_id),
        "ballot_id": str(envelope.ballot_id),
        "credential_proof": str(envelope.credential_proof),
        "integrity_hash": envelope.integrity_hash,
        "validation_status": envelope.validation_status.value,
        "included_in_tally": envelope.included_in_tally,
    }


def vote_envelope_full_state_payload(envelope: VoteEnvelope) -> dict[str, object]:
    """Full snapshot for Audit Core's `before_hash`/`after_hash` only -
    never for a domain event payload (see `vote_envelope_state_payload`).
    """
    payload = vote_envelope_state_payload(envelope)
    payload.update(
        {
            "encrypted_or_encoded_choice": envelope.encrypted_or_encoded_choice,
            "submitted_at": envelope.submitted_at.isoformat(),
        }
    )
    return payload


def _build_ballot_event(
    *,
    event_type: str,
    event_id: UUID,
    ballot: Ballot,
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
        producer="voting-service",
        actor=actor,
        subject=SubjectRef(subject_type="ballot", subject_id=ballot.ballot_id),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=ballot_state_payload(ballot),
    )


def build_ballot_created_event(
    *,
    event_id: UUID,
    ballot: Ballot,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return _build_ballot_event(
        event_type="ballot.created",
        event_id=event_id,
        ballot=ballot,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_ballot_configuration_locked_event(
    *,
    event_id: UUID,
    ballot: Ballot,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return _build_ballot_event(
        event_type="ballot.configuration_locked",
        event_id=event_id,
        ballot=ballot,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_ballot_scheduled_event(
    *,
    event_id: UUID,
    ballot: Ballot,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return _build_ballot_event(
        event_type="ballot.scheduled",
        event_id=event_id,
        ballot=ballot,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_ballot_opened_event(
    *,
    event_id: UUID,
    ballot: Ballot,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return _build_ballot_event(
        event_type="ballot.opened",
        event_id=event_id,
        ballot=ballot,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_ballot_paused_event(
    *,
    event_id: UUID,
    ballot: Ballot,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return _build_ballot_event(
        event_type="ballot.paused",
        event_id=event_id,
        ballot=ballot,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_ballot_resumed_event(
    *,
    event_id: UUID,
    ballot: Ballot,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return _build_ballot_event(
        event_type="ballot.resumed",
        event_id=event_id,
        ballot=ballot,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_ballot_closed_event(
    *,
    event_id: UUID,
    ballot: Ballot,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return _build_ballot_event(
        event_type="ballot.closed",
        event_id=event_id,
        ballot=ballot,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_ballot_cancelled_event(
    *,
    event_id: UUID,
    ballot: Ballot,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return _build_ballot_event(
        event_type="ballot.cancelled",
        event_id=event_id,
        ballot=ballot,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def _build_vote_event(
    *,
    event_type: str,
    event_id: UUID,
    envelope: VoteEnvelope,
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
        producer="voting-service",
        actor=actor,
        subject=SubjectRef(subject_type="vote_envelope", subject_id=envelope.vote_envelope_id),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=vote_envelope_state_payload(envelope),
    )


def build_vote_received_event(
    *,
    event_id: UUID,
    envelope: VoteEnvelope,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return _build_vote_event(
        event_type="vote.received",
        event_id=event_id,
        envelope=envelope,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_vote_validated_event(
    *,
    event_id: UUID,
    envelope: VoteEnvelope,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return _build_vote_event(
        event_type="vote.validated",
        event_id=event_id,
        envelope=envelope,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_vote_rejected_event(
    *,
    event_id: UUID,
    envelope: VoteEnvelope,
    reason_codes: tuple[str, ...],
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    payload = vote_envelope_state_payload(envelope)
    payload["reason_codes"] = list(reason_codes)
    return build_event_envelope(
        event_id=event_id,
        event_type="vote.rejected",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="voting-service",
        actor=actor,
        subject=SubjectRef(subject_type="vote_envelope", subject_id=envelope.vote_envelope_id),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=payload,
    )


def build_vote_superseded_event(
    *,
    event_id: UUID,
    envelope: VoteEnvelope,
    superseded_by: UUID,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    payload = vote_envelope_state_payload(envelope)
    payload["superseded_by"] = str(superseded_by)
    return build_event_envelope(
        event_id=event_id,
        event_type="vote.superseded",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="voting-service",
        actor=actor,
        subject=SubjectRef(subject_type="vote_envelope", subject_id=envelope.vote_envelope_id),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=payload,
    )
