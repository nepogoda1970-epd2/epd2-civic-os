"""Canonical events emitted by Tally Service (canon events section 20.10's
tally/result subset, verbatim): `tally.started`, `tally.completed`,
`tally.verified`, `result.published`.

Per ADR-009 item 15's minimum-public-disclosure rule, no payload built
here ever includes individual vote contents - only aggregate counts and
administrative fields, which is all this service ever has access to in
the first place (it never imports `epd2_voting_service`, see
`domain.py`'s module docstring and `README.md`).
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from epd2_core.event_envelope import ActorRef, EventEnvelope, SubjectRef, build_event_envelope
from epd2_tally_service.domain import ResultPublication, Tally

EVENT_VERSION = "1.0"
SUPPORTED_MAJOR_VERSIONS = frozenset({1})


def tally_state_payload(tally: Tally) -> dict[str, object]:
    """Minimal, canonically-hashable event-payload snapshot of a `Tally`'s
    own state, used for `tally.started`/`tally.completed`/`tally.verified`
    payloads. Deliberately excludes `result_data`/`invalid_vote_count`/
    `tally_signature` - see `tally_full_state_payload` for Audit Core's
    `before_hash`/`after_hash`, which needs the complete state to be a
    meaningful tamper-evidence check."""
    return {
        "tally_id": str(tally.tally_id),
        "ballot_id": str(tally.ballot_id),
        "input_set_hash": tally.input_set_hash,
        "algorithm_version": tally.algorithm_version,
        "verification_status": tally.verification_status.value,
        "started_at": tally.started_at.isoformat(),
        "completed_at": tally.completed_at.isoformat() if tally.completed_at is not None else None,
    }


def tally_full_state_payload(tally: Tally) -> dict[str, object]:
    """Full, canonically-hashable snapshot of a `Tally`'s own state, used
    for Audit Core's `before_hash`/`after_hash` (`application.py`)."""
    payload = tally_state_payload(tally)
    payload.update(
        {
            "result_data": dict(tally.result_data),
            "invalid_vote_count": tally.invalid_vote_count,
            "tally_signature": tally.tally_signature,
        }
    )
    return payload


def result_publication_state_payload(result: ResultPublication) -> dict[str, object]:
    """Full, canonically-hashable snapshot of a `ResultPublication`'s own
    state, used for both `result.published`'s event payload and Audit
    Core's `after_hash`. Per ADR-009 item 15, every field here is already
    part of the minimum-disclosure set (aggregate counts plus
    administrative fields) - there is no narrower "public" subset to
    additionally redact, unlike `credential_state_payload` vs
    `credential_full_state_payload` in credential-service."""
    return {
        "result_publication_id": str(result.result_publication_id),
        "ballot_id": str(result.ballot_id),
        "tally_id": str(result.tally_id),
        "eligible_count": result.eligible_count,
        "credential_count": result.credential_count,
        "accepted_vote_count": result.accepted_vote_count,
        "rejected_vote_count": result.rejected_vote_count,
        "quorum_result": result.quorum_result.value,
        "threshold_result": result.threshold_result.value,
        "published_at": result.published_at.isoformat(),
        "audit_package_reference": result.audit_package_reference,
        "challenge_deadline_at": result.challenge_deadline_at.isoformat(),
    }


def build_tally_started_event(
    *,
    event_id: UUID,
    tally: Tally,
    actor: ActorRef,
    correlation_id: UUID,
    occurred_at: datetime,
) -> EventEnvelope:
    return build_event_envelope(
        event_id=event_id,
        event_type="tally.started",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="tally-service",
        actor=actor,
        subject=SubjectRef(subject_type="tally", subject_id=tally.tally_id),
        correlation_id=correlation_id,
        causation_id=None,
        payload=tally_state_payload(tally),
    )


def build_tally_completed_event(
    *,
    event_id: UUID,
    tally: Tally,
    actor: ActorRef,
    correlation_id: UUID,
    occurred_at: datetime,
) -> EventEnvelope:
    return build_event_envelope(
        event_id=event_id,
        event_type="tally.completed",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="tally-service",
        actor=actor,
        subject=SubjectRef(subject_type="tally", subject_id=tally.tally_id),
        correlation_id=correlation_id,
        causation_id=None,
        payload=tally_state_payload(tally),
    )


def build_tally_verified_event(
    *,
    event_id: UUID,
    tally: Tally,
    actor: ActorRef,
    correlation_id: UUID,
    occurred_at: datetime,
) -> EventEnvelope:
    """Only ever built on a successful `completed -> verified` transition.
    Canon events section 20.10 gives no distinct event name for a failed
    verification (`completed -> verification_failed`) - that transition is
    persisted and audited (`INTEGRITY_CHECK_FAILED`) but emits no domain
    event here, see `application.py::verify_tally`."""
    return build_event_envelope(
        event_id=event_id,
        event_type="tally.verified",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="tally-service",
        actor=actor,
        subject=SubjectRef(subject_type="tally", subject_id=tally.tally_id),
        correlation_id=correlation_id,
        causation_id=None,
        payload=tally_state_payload(tally),
    )


def build_result_published_event(
    *,
    event_id: UUID,
    result: ResultPublication,
    actor: ActorRef,
    correlation_id: UUID,
    occurred_at: datetime,
) -> EventEnvelope:
    return build_event_envelope(
        event_id=event_id,
        event_type="result.published",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="tally-service",
        actor=actor,
        subject=SubjectRef(
            subject_type="result_publication", subject_id=result.result_publication_id
        ),
        correlation_id=correlation_id,
        causation_id=None,
        payload=result_publication_state_payload(result),
    )
