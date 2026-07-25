"""Canonical events emitted by Eligibility Service (canon section 20.3)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from epd2_core.event_envelope import ActorRef, EventEnvelope, SubjectRef, build_event_envelope
from epd2_eligibility_service.domain import EligibilityDecision, EligibilitySnapshot

EVENT_VERSION = "1.0"
SUPPORTED_MAJOR_VERSIONS = frozenset({1})


def decision_state_payload(decision: EligibilityDecision) -> dict[str, object]:
    """Full, canonically-hashable snapshot of an `EligibilityDecision`'s
    own state, used for Audit Core's `after_hash` (`application.py`) -
    deliberately more complete than the minimal event payload below."""
    return {
        "eligibility_decision_id": str(decision.eligibility_decision_id),
        "subject_reference": str(decision.subject_reference),
        "process_id": str(decision.process_id),
        "eligibility_rule_id": str(decision.eligibility_rule_id),
        "rule_version": decision.rule_version,
        "decision": decision.decision.value,
        "reason_codes": list(decision.reason_codes),
        "evaluated_at": decision.evaluated_at.isoformat(),
        "expires_at": decision.expires_at.isoformat() if decision.expires_at else None,
        "correlation_id": str(decision.correlation_id),
        "evaluator_version": decision.evaluator_version,
        "evaluated_claims": dict(decision.evaluated_claims),
    }


def snapshot_state_payload(snapshot: EligibilitySnapshot) -> dict[str, object]:
    """Full, canonically-hashable snapshot of an `EligibilitySnapshot`'s
    own state, used for Audit Core's `after_hash` (`application.py`)."""
    return {
        "eligibility_snapshot_id": str(snapshot.eligibility_snapshot_id),
        "eligibility_rule_id": str(snapshot.eligibility_rule_id),
        "rule_version": snapshot.rule_version,
        "created_at": snapshot.created_at.isoformat(),
        "eligible_decision_ids": [str(i) for i in snapshot.eligible_decision_ids],
        "eligible_count": snapshot.eligible_count,
        "digest": snapshot.digest,
    }


def build_evaluated_event(
    *,
    event_id: UUID,
    decision: EligibilityDecision,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    payload = {
        "eligibility_decision_id": str(decision.eligibility_decision_id),
        "eligibility_rule_id": str(decision.eligibility_rule_id),
        "rule_version": decision.rule_version,
        "decision": decision.decision.value,
        "reason_codes": list(decision.reason_codes),
    }
    return build_event_envelope(
        event_id=event_id,
        event_type="eligibility.evaluated",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="eligibility-service",
        actor=actor,
        subject=SubjectRef(
            subject_type="eligibility_decision", subject_id=decision.eligibility_decision_id
        ),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=payload,
    )


def build_snapshot_created_event(
    *,
    event_id: UUID,
    snapshot: EligibilitySnapshot,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    payload = {
        "eligibility_snapshot_id": str(snapshot.eligibility_snapshot_id),
        "eligibility_rule_id": str(snapshot.eligibility_rule_id),
        "rule_version": snapshot.rule_version,
        "eligible_count": snapshot.eligible_count,
        "digest": snapshot.digest,
    }
    return build_event_envelope(
        event_id=event_id,
        event_type="eligibility.snapshot_created",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="eligibility-service",
        actor=actor,
        subject=SubjectRef(
            subject_type="eligibility_snapshot", subject_id=snapshot.eligibility_snapshot_id
        ),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=payload,
    )
