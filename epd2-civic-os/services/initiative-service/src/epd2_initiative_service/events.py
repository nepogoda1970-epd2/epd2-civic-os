"""Canonical events emitted by Initiative Service (canon sections 20.6,
20.7), plus the minimal/full state-payload split
(`epd2_credential_service.events`'s precedent): a minimal, canonically-
hashable snapshot for the wire event payload, and a complete snapshot for
Audit Core's `before_hash`/`after_hash` (`application.py`), which needs
the full state to be a meaningful tamper-evidence check even for fields
the event payload itself omits.

`SourceRecord` has no listed canon event (creation and verification-
status updates are audited via Audit Core directly, never a canonical
event - see `application.add_source_record` and
`application.update_source_verification_status`), so this module has no
`build_source_*_event` function; `source_record_full_state_payload`
below exists purely for those two commands' audit hashing.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from epd2_core.event_envelope import ActorRef, EventEnvelope, SubjectRef, build_event_envelope
from epd2_initiative_service.domain import (
    Amendment,
    Initiative,
    InitiativeVersion,
    SourceRecord,
    SupportRecord,
)

EVENT_VERSION = "1.0"
SUPPORTED_MAJOR_VERSIONS = frozenset({1})


# ---------------------------------------------------------------------------
# State payloads
# ---------------------------------------------------------------------------


def initiative_state_payload(initiative: Initiative) -> dict[str, object]:
    """Minimal, canonically-hashable snapshot of an `Initiative`'s state,
    used for every `initiative.*` status-change event payload."""
    return {
        "initiative_id": str(initiative.initiative_id),
        "space_id": str(initiative.space_id),
        "current_version_id": (
            str(initiative.current_version_id) if initiative.current_version_id else None
        ),
        "status": initiative.status.value,
        "support_count": initiative.support_count,
    }


def initiative_full_state_payload(initiative: Initiative) -> dict[str, object]:
    """Full, canonically-hashable snapshot of an `Initiative`'s own
    state, used for Audit Core's `before_hash`/`after_hash`."""
    payload = initiative_state_payload(initiative)
    payload.update(
        {
            "author_actor_id": str(initiative.author_actor_id),
            "initiative_type": initiative.initiative_type,
            "workflow_id": str(initiative.workflow_id),
            "created_at": initiative.created_at.isoformat(),
        }
    )
    return payload


def initiative_version_state_payload(version: InitiativeVersion) -> dict[str, object]:
    """Minimal, canonically-hashable snapshot of an `InitiativeVersion`,
    used for the `initiative.version_created` event payload."""
    return {
        "initiative_version_id": str(version.initiative_version_id),
        "initiative_id": str(version.initiative_id),
        "version_number": version.version_number,
        "content_hash": version.content_hash,
    }


def initiative_version_full_state_payload(version: InitiativeVersion) -> dict[str, object]:
    """Full, canonically-hashable snapshot of an `InitiativeVersion`'s
    own state, used for Audit Core's `after_hash`."""
    payload = initiative_version_state_payload(version)
    payload.update(
        {
            "title": version.title,
            "problem_statement": version.problem_statement,
            "proposed_solution": version.proposed_solution,
            "affected_groups": list(version.affected_groups),
            "expected_effects": version.expected_effects,
            "risks": version.risks,
            "estimated_resources": version.estimated_resources,
            "legal_questions": version.legal_questions,
            "source_references": [str(s) for s in version.source_references],
            "created_by_actor_id": str(version.created_by_actor_id),
        }
    )
    return payload


def support_record_state_payload(support: SupportRecord) -> dict[str, object]:
    """Minimal, canonically-hashable snapshot of a `SupportRecord`, used
    for `initiative.support_added`/`initiative.support_withdrawn` event
    payloads. Deliberately excludes `support_actor_reference`/
    `credential_reference` from the wire event - see
    `support_record_full_state_payload` for the complete snapshot used by
    Audit Core, which needs every field to be a meaningful tamper-
    evidence check even though neither field is itself identity data
    (canon 11.3; `epd2_initiative_service.domain.FORBIDDEN_FIELD_NAMES`)."""
    return {
        "support_record_id": str(support.support_record_id),
        "initiative_id": str(support.initiative_id),
        "status": support.status.value,
    }


def support_record_full_state_payload(support: SupportRecord) -> dict[str, object]:
    """Full, canonically-hashable snapshot of a `SupportRecord`'s own
    state, used for Audit Core's `before_hash`/`after_hash`."""
    payload = support_record_state_payload(support)
    payload.update(
        {
            "support_actor_reference": str(support.support_actor_reference),
            "credential_reference": str(support.credential_reference),
            "created_at": support.created_at.isoformat(),
        }
    )
    return payload


def amendment_state_payload(amendment: Amendment) -> dict[str, object]:
    """Minimal, canonically-hashable snapshot of an `Amendment`, used for
    every `amendment.*` event payload."""
    return {
        "amendment_id": str(amendment.amendment_id),
        "initiative_id": str(amendment.initiative_id),
        "target_version_id": str(amendment.target_version_id),
        "status": amendment.status.value,
    }


def amendment_full_state_payload(amendment: Amendment) -> dict[str, object]:
    """Full, canonically-hashable snapshot of an `Amendment`'s own state,
    used for Audit Core's `before_hash`/`after_hash`."""
    payload = amendment_state_payload(amendment)
    payload.update(
        {
            "proposer_actor_id": str(amendment.proposer_actor_id),
            "proposed_change": amendment.proposed_change,
            "justification": amendment.justification,
            "decision_reference": (
                str(amendment.decision_reference) if amendment.decision_reference else None
            ),
        }
    )
    return payload


def source_record_state_payload(source: SourceRecord) -> dict[str, object]:
    """Minimal, canonically-hashable snapshot of a `SourceRecord`. No
    canon event names a `SourceRecord` payload directly (see module
    docstring) - this is used only as the base of
    `source_record_full_state_payload` below."""
    return {
        "source_id": str(source.source_id),
        "source_type": source.source_type,
        "verification_status": source.verification_status.value,
        "content_hash": source.content_hash,
    }


def source_record_full_state_payload(source: SourceRecord) -> dict[str, object]:
    """Full, canonically-hashable snapshot of a `SourceRecord`'s own
    state, used for Audit Core's `before_hash`/`after_hash` in
    `application.add_source_record`/`application.
    update_source_verification_status`."""
    payload = source_record_state_payload(source)
    payload.update(
        {
            "title": source.title,
            "publisher": source.publisher,
            "publication_date": (
                source.publication_date.isoformat() if source.publication_date else None
            ),
            "url": source.url,
            "archive_reference": source.archive_reference,
            "added_by_actor_id": str(source.added_by_actor_id),
            "accessed_at": source.accessed_at.isoformat(),
            "valid_until": source.valid_until.isoformat() if source.valid_until else None,
        }
    )
    return payload


# ---------------------------------------------------------------------------
# Event builders - canon section 20.6 (Initiative)
# ---------------------------------------------------------------------------


def _build_initiative_event(
    *,
    event_type: str,
    event_id: UUID,
    initiative: Initiative,
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
        producer="initiative-service",
        actor=actor,
        subject=SubjectRef(subject_type="initiative", subject_id=initiative.initiative_id),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=initiative_state_payload(initiative),
    )


def build_draft_created_event(
    *,
    event_id: UUID,
    initiative: Initiative,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return _build_initiative_event(
        event_type="initiative.draft_created",
        event_id=event_id,
        initiative=initiative,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_submitted_event(
    *,
    event_id: UUID,
    initiative: Initiative,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return _build_initiative_event(
        event_type="initiative.submitted",
        event_id=event_id,
        initiative=initiative,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_revision_requested_event(
    *,
    event_id: UUID,
    initiative: Initiative,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return _build_initiative_event(
        event_type="initiative.revision_requested",
        event_id=event_id,
        initiative=initiative,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_published_event(
    *,
    event_id: UUID,
    initiative: Initiative,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return _build_initiative_event(
        event_type="initiative.published",
        event_id=event_id,
        initiative=initiative,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_qualified_event(
    *,
    event_id: UUID,
    initiative: Initiative,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return _build_initiative_event(
        event_type="initiative.qualified",
        event_id=event_id,
        initiative=initiative,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_deliberation_started_event(
    *,
    event_id: UUID,
    initiative: Initiative,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return _build_initiative_event(
        event_type="initiative.deliberation_started",
        event_id=event_id,
        initiative=initiative,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_legal_review_requested_event(
    *,
    event_id: UUID,
    initiative: Initiative,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return _build_initiative_event(
        event_type="initiative.legal_review_requested",
        event_id=event_id,
        initiative=initiative,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_ready_for_ballot_event(
    *,
    event_id: UUID,
    initiative: Initiative,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return _build_initiative_event(
        event_type="initiative.ready_for_ballot",
        event_id=event_id,
        initiative=initiative,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_initiative_withdrawn_event(
    *,
    event_id: UUID,
    initiative: Initiative,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return _build_initiative_event(
        event_type="initiative.withdrawn",
        event_id=event_id,
        initiative=initiative,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_archived_event(
    *,
    event_id: UUID,
    initiative: Initiative,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return _build_initiative_event(
        event_type="initiative.archived",
        event_id=event_id,
        initiative=initiative,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_version_created_event(
    *,
    event_id: UUID,
    version: InitiativeVersion,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return build_event_envelope(
        event_id=event_id,
        event_type="initiative.version_created",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="initiative-service",
        actor=actor,
        subject=SubjectRef(
            subject_type="initiative_version", subject_id=version.initiative_version_id
        ),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=initiative_version_state_payload(version),
    )


def build_support_added_event(
    *,
    event_id: UUID,
    support: SupportRecord,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return build_event_envelope(
        event_id=event_id,
        event_type="initiative.support_added",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="initiative-service",
        actor=actor,
        subject=SubjectRef(subject_type="support_record", subject_id=support.support_record_id),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=support_record_state_payload(support),
    )


def build_support_withdrawn_event(
    *,
    event_id: UUID,
    support: SupportRecord,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return build_event_envelope(
        event_id=event_id,
        event_type="initiative.support_withdrawn",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="initiative-service",
        actor=actor,
        subject=SubjectRef(subject_type="support_record", subject_id=support.support_record_id),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=support_record_state_payload(support),
    )


# ---------------------------------------------------------------------------
# Event builders - canon section 20.7 (Amendment)
# ---------------------------------------------------------------------------


def _build_amendment_event(
    *,
    event_type: str,
    event_id: UUID,
    amendment: Amendment,
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
        producer="initiative-service",
        actor=actor,
        subject=SubjectRef(subject_type="amendment", subject_id=amendment.amendment_id),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=amendment_state_payload(amendment),
    )


def build_amendment_submitted_event(
    *,
    event_id: UUID,
    amendment: Amendment,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return _build_amendment_event(
        event_type="amendment.submitted",
        event_id=event_id,
        amendment=amendment,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_amendment_published_event(
    *,
    event_id: UUID,
    amendment: Amendment,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return _build_amendment_event(
        event_type="amendment.published",
        event_id=event_id,
        amendment=amendment,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_amendment_accepted_event(
    *,
    event_id: UUID,
    amendment: Amendment,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return _build_amendment_event(
        event_type="amendment.accepted",
        event_id=event_id,
        amendment=amendment,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_amendment_rejected_event(
    *,
    event_id: UUID,
    amendment: Amendment,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return _build_amendment_event(
        event_type="amendment.rejected",
        event_id=event_id,
        amendment=amendment,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )
