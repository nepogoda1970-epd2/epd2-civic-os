"""Canonical events emitted by Deliberation Service (canon section 20.8,
verbatim): `discussion.opened`, `contribution.created`,
`contribution.edited`, `contribution.flagged`, `contribution.hidden`,
`contribution.restored`, `discussion.closed`. No other event types are
defined here.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from epd2_core.event_envelope import ActorRef, EventEnvelope, SubjectRef, build_event_envelope
from epd2_deliberation_service.domain import Contribution, Discussion

EVENT_VERSION = "1.0"
SUPPORTED_MAJOR_VERSIONS = frozenset({1})

_PRODUCER = "deliberation-service"


def discussion_state_payload(discussion: Discussion) -> dict[str, object]:
    """Minimal, canonically-hashable event-payload snapshot of a
    discussion's state, used for `discussion.opened`/`discussion.closed`
    payloads. Deliberately excludes `moderation_policy_id` (not needed by
    a consumer reacting to an open/close transition) - see
    `discussion_full_state_payload` for Audit Core's `before_hash`/
    `after_hash`, which needs the complete state."""
    return {
        "discussion_id": str(discussion.discussion_id),
        "subject_type": discussion.subject_type,
        "subject_id": str(discussion.subject_id),
        "space_id": str(discussion.space_id),
        "status": discussion.status.value,
    }


def discussion_full_state_payload(discussion: Discussion) -> dict[str, object]:
    """Full, canonically-hashable snapshot of a discussion's own state,
    used for Audit Core's `before_hash`/`after_hash` (`application.py`)."""
    payload = discussion_state_payload(discussion)
    policy_id = discussion.moderation_policy_id
    payload["moderation_policy_id"] = str(policy_id) if policy_id is not None else None
    return payload


def contribution_state_payload(contribution: Contribution) -> dict[str, object]:
    """Minimal, canonically-hashable event-payload snapshot of a
    contribution's state, used for `contribution.*` event payloads.
    Deliberately excludes `created_at` (not needed by a consumer reacting
    to a creation/edit/moderation transition) - see
    `contribution_full_state_payload` for Audit Core's `before_hash`/
    `after_hash`, which needs the complete state."""
    return {
        "contribution_id": str(contribution.contribution_id),
        "discussion_id": str(contribution.discussion_id),
        "author_actor_id": str(contribution.author_actor_id),
        "parent_contribution_id": (
            str(contribution.parent_contribution_id)
            if contribution.parent_contribution_id is not None
            else None
        ),
        "contribution_type": contribution.contribution_type.value,
        "content": contribution.content,
        "content_hash": contribution.content_hash,
        "visibility_status": contribution.visibility_status.value,
        "edited_version": contribution.edited_version,
    }


def contribution_full_state_payload(contribution: Contribution) -> dict[str, object]:
    """Full, canonically-hashable snapshot of a contribution's own state,
    used for Audit Core's `before_hash`/`after_hash` (`application.py`)."""
    payload = contribution_state_payload(contribution)
    payload["created_at"] = contribution.created_at.isoformat()
    return payload


def build_discussion_opened_event(
    *,
    event_id: UUID,
    discussion: Discussion,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return build_event_envelope(
        event_id=event_id,
        event_type="discussion.opened",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer=_PRODUCER,
        actor=actor,
        subject=SubjectRef(subject_type="discussion", subject_id=discussion.discussion_id),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=discussion_state_payload(discussion),
    )


def build_discussion_closed_event(
    *,
    event_id: UUID,
    discussion: Discussion,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return build_event_envelope(
        event_id=event_id,
        event_type="discussion.closed",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer=_PRODUCER,
        actor=actor,
        subject=SubjectRef(subject_type="discussion", subject_id=discussion.discussion_id),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=discussion_state_payload(discussion),
    )


def build_contribution_created_event(
    *,
    event_id: UUID,
    contribution: Contribution,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return build_event_envelope(
        event_id=event_id,
        event_type="contribution.created",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer=_PRODUCER,
        actor=actor,
        subject=SubjectRef(subject_type="contribution", subject_id=contribution.contribution_id),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=contribution_state_payload(contribution),
    )


def build_contribution_edited_event(
    *,
    event_id: UUID,
    contribution: Contribution,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return build_event_envelope(
        event_id=event_id,
        event_type="contribution.edited",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer=_PRODUCER,
        actor=actor,
        subject=SubjectRef(subject_type="contribution", subject_id=contribution.contribution_id),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=contribution_state_payload(contribution),
    )


def build_contribution_flagged_event(
    *,
    event_id: UUID,
    contribution: Contribution,
    flag_reason_code: str,
    note: str | None,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`flag_reason_code`/`note` describe *why* the flag was raised (e.g.
    canon section 24's `MODERATION_POLICY_VIOLATION`) - distinct from the
    audit entry's own `reason_code` (`application.py`'s
    `CONTRIBUTION_FLAGGED`, which describes the audit *action*, not the
    flag's substantive reason)."""
    payload = dict(contribution_state_payload(contribution))
    payload["flag_reason_code"] = flag_reason_code
    payload["note"] = note
    return build_event_envelope(
        event_id=event_id,
        event_type="contribution.flagged",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer=_PRODUCER,
        actor=actor,
        subject=SubjectRef(subject_type="contribution", subject_id=contribution.contribution_id),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=payload,
    )


def build_contribution_hidden_event(
    *,
    event_id: UUID,
    contribution: Contribution,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return build_event_envelope(
        event_id=event_id,
        event_type="contribution.hidden",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer=_PRODUCER,
        actor=actor,
        subject=SubjectRef(subject_type="contribution", subject_id=contribution.contribution_id),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=contribution_state_payload(contribution),
    )


def build_contribution_restored_event(
    *,
    event_id: UUID,
    contribution: Contribution,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return build_event_envelope(
        event_id=event_id,
        event_type="contribution.restored",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer=_PRODUCER,
        actor=actor,
        subject=SubjectRef(subject_type="contribution", subject_id=contribution.contribution_id),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=contribution_state_payload(contribution),
    )
