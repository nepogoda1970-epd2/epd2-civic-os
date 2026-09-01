"""PACK-15 identity-side event builders on PACK-13's canonical envelope.

Every event uses `epd2_core.event_envelope.build_event_envelope` unchanged
(canon section 21). Three payload rules are enforced **structurally**,
before an envelope can exist:

1. no forbidden identity or ballot field (`assert_no_forbidden_fields`);
2. no payload carrying both an assertion reference and a credential
   reference (`assert_no_assertion_credential_pair`, ADR-093);
3. no exact cohort size, batch size or queue depth - classes only, because
   an exact size in a small electorate is a participation statement
   (`T-P15-37`).

`correlation_id` chains terminate at the trust boundary: the identity side
never receives one minted on the voting side, and none is echoed back.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any
from uuid import UUID

from epd2_core.event_envelope import ActorRef, EventEnvelope, SubjectRef, build_event_envelope
from epd2_eligibility_service.voting_eligibility import (
    AssertionQueueEntry,
    EligibilityAssertion,
    EligibilityCase,
    EligibilityDecision,
    assert_no_assertion_credential_pair,
    assert_no_forbidden_fields,
    decision_reason_codes,
)
from epd2_eligibility_service.voting_timing import CohortSizeClass, coarsen
from epd2_eligibility_service.voting_trust_exceptions import VotingBoundaryIntegrityError

EVENT_VERSION = "1.0"
SUPPORTED_MAJOR_VERSIONS = frozenset({1})
PRODUCER = "eligibility-service"

#: Event types, aggregate-prefixed per PACK-13's `P13-EVT-002`.
ELIGIBILITY_REQUESTED = "eligibility.requested"
ELIGIBILITY_EVALUATION_STARTED = "eligibility.evaluation_started"
ELIGIBILITY_APPROVED = "eligibility.approved"
ELIGIBILITY_DENIED = "eligibility.denied"
ELIGIBILITY_REVIEW_REQUIRED = "eligibility.review_required"
ELIGIBILITY_EVIDENCE_REFERENCED = "eligibility.evidence_referenced"
ELIGIBILITY_DECISION_EXPIRED = "eligibility.decision_expired"
ELIGIBILITY_DISPUTED = "eligibility.disputed"
ELIGIBILITY_DISPUTE_RESOLVED = "eligibility.dispute_resolved"

ASSERTION_MINTED = "eligibility_assertion.minted"
ASSERTION_QUEUED = "eligibility_assertion.queued"
ASSERTION_RELEASED = "eligibility_assertion.released"
ASSERTION_REVOKED = "eligibility_assertion.revoked"
ASSERTION_EXPIRED = "eligibility_assertion.expired"
ASSERTION_REDEEMED = "eligibility_assertion.redeemed"
ASSERTION_REPLAY_REJECTED = "eligibility_assertion.replay_rejected"

PICKUP_CREATED = "assertion_pickup.created"
PICKUP_REDEEMED = "assertion_pickup.redeemed"
PICKUP_EXPIRED = "assertion_pickup.expired"
PICKUP_REPLAY_REJECTED = "assertion_pickup.replay_rejected"

HANDOFF_ACCEPTED = "voting_handoff_acceptance.accepted"
HANDOFF_REJECTED = "voting_handoff_acceptance.rejected"
HANDOFF_EXPIRED = "voting_handoff_acceptance.expired"
HANDOFF_REPLAY_REJECTED = "voting_handoff_acceptance.replay_rejected"

COHORT_THRESHOLD_NOT_MET = "voting_boundary.cohort_threshold_not_met"
TIMING_PROFILE_APPLIED = "voting_boundary.timing_profile_applied"
CORRELATION_RISK_DETECTED = "voting_boundary.correlation_risk_detected"
INTEGRITY_VIOLATION_DETECTED = "voting_boundary.integrity_violation_detected"

#: Exact sizes are never published. Any payload key ending in one of these
#: suffixes must carry a class, not a number.
SIZE_KEYS_REQUIRING_CLASS: frozenset[str] = frozenset(
    {"cohort_size", "batch_size", "queue_depth", "turnout", "eligible_population"}
)


def _guard(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    assert_no_forbidden_fields(payload)
    assert_no_assertion_credential_pair(payload)
    offending = sorted(set(payload) & SIZE_KEYS_REQUIRING_CLASS)
    if offending:
        raise VotingBoundaryIntegrityError(
            "exact sizes are never published in a voting-trust payload: " + ", ".join(offending)
        )
    return payload


def _envelope(
    *,
    event_id: UUID,
    event_type: str,
    subject: SubjectRef,
    actor: ActorRef,
    occurred_at: datetime,
    correlation_id: UUID,
    causation_id: UUID | None,
    payload: Mapping[str, Any],
) -> EventEnvelope:
    return build_event_envelope(
        event_id=event_id,
        event_type=event_type,
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer=PRODUCER,
        actor=actor,
        subject=subject,
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=_guard(payload),
    )


def build_eligibility_event(
    *,
    event_id: UUID,
    event_type: str,
    case: EligibilityCase,
    decision: EligibilityDecision | None,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """An eligibility-stream event. The subject is the case, which is the
    last artifact in the flow whose subject is identity-side."""
    payload: dict[str, Any] = {
        "case_id": str(case.case_id),
        "voting_context_reference": case.voting_context_reference,
        "participation_class": case.participation_class,
        "assisted": case.assisted_by is not None,
    }
    if decision is not None:
        payload["decision_id"] = str(decision.decision_id)
        payload["status"] = decision.status.value
        payload["rule_set_version"] = decision.rule_set.rule_set_version
        payload["reason_codes"] = list(decision_reason_codes(decision.reasons))
        payload["source_versions"] = dict(decision.source_versions)
        payload["organizational_scope"] = decision.organizational_scope
    return _envelope(
        event_id=event_id,
        event_type=event_type,
        subject=SubjectRef(subject_type="eligibility_case", subject_id=case.case_id),
        actor=actor,
        occurred_at=occurred_at,
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=payload,
    )


def build_assertion_event(
    *,
    event_id: UUID,
    event_type: str,
    assertion: EligibilityAssertion,
    granularity_seconds: int,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """An assertion-stream event. Carries **no credential reference**."""
    payload = {
        "assertion_id": str(assertion.assertion_id),
        "voting_context_reference": assertion.voting_context_reference,
        "eligibility_class": assertion.eligibility_class,
        "organizational_scope": assertion.organizational_scope,
        "status": assertion.status.value,
        "audience": assertion.audience,
        "expires_at_bucket": coarsen(assertion.expires_at, granularity_seconds).isoformat(),
    }
    return _envelope(
        event_id=event_id,
        event_type=event_type,
        subject=SubjectRef(subject_type="eligibility_assertion", subject_id=assertion.assertion_id),
        actor=actor,
        occurred_at=coarsen(occurred_at, granularity_seconds),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=payload,
    )


def build_queue_event(
    *,
    event_id: UUID,
    event_type: str,
    entry: AssertionQueueEntry,
    cohort_size_class: CohortSizeClass,
    granularity_seconds: int,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """A queue event. Reports a cohort **class**, never a size."""
    payload = {
        "assertion_id": str(entry.assertion_id),
        "voting_context_reference": entry.voting_context_reference,
        "batch_reference": entry.batch_reference,
        "cohort_size_class": cohort_size_class.value,
        "below_minimum_cohort": entry.below_minimum_cohort,
    }
    return _envelope(
        event_id=event_id,
        event_type=event_type,
        subject=SubjectRef(subject_type="eligibility_assertion", subject_id=entry.assertion_id),
        actor=actor,
        occurred_at=coarsen(occurred_at, granularity_seconds),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=payload,
    )


def build_handoff_event(
    *,
    event_id: UUID,
    event_type: str,
    acceptance_id: UUID,
    voting_context_reference: str,
    audience: str,
    origin: str,
    reason_code: str,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """A handoff-acceptance event. Carries no account and no session."""
    payload = {
        "acceptance_id": str(acceptance_id),
        "voting_context_reference": voting_context_reference,
        "audience": audience,
        "origin": origin,
        "reason_code": reason_code,
    }
    return _envelope(
        event_id=event_id,
        event_type=event_type,
        subject=SubjectRef(subject_type="voting_handoff_acceptance", subject_id=acceptance_id),
        actor=actor,
        occurred_at=occurred_at,
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=payload,
    )


def build_integrity_event(
    *,
    event_id: UUID,
    event_type: str,
    detection_id: UUID,
    voting_context_reference: str,
    risk_class: str,
    severity: str,
    reason_code: str,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """A voting-integrity event. Contains **no identity, in any field**."""
    payload = {
        "detection_id": str(detection_id),
        "voting_context_reference": voting_context_reference,
        "risk_class": risk_class,
        "severity": severity,
        "reason_code": reason_code,
    }
    return _envelope(
        event_id=event_id,
        event_type=event_type,
        subject=SubjectRef(subject_type="voting_boundary_detection", subject_id=detection_id),
        actor=actor,
        occurred_at=occurred_at,
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=payload,
    )


#: Every PACK-15 identity-side event type, for the contract tests.
ELIGIBILITY_EVENT_TYPES: tuple[str, ...] = (
    ELIGIBILITY_REQUESTED,
    ELIGIBILITY_EVALUATION_STARTED,
    ELIGIBILITY_APPROVED,
    ELIGIBILITY_DENIED,
    ELIGIBILITY_REVIEW_REQUIRED,
    ELIGIBILITY_EVIDENCE_REFERENCED,
    ELIGIBILITY_DECISION_EXPIRED,
    ELIGIBILITY_DISPUTED,
    ELIGIBILITY_DISPUTE_RESOLVED,
)
ASSERTION_EVENT_TYPES: tuple[str, ...] = (
    ASSERTION_MINTED,
    ASSERTION_QUEUED,
    ASSERTION_RELEASED,
    ASSERTION_REVOKED,
    ASSERTION_EXPIRED,
    ASSERTION_REDEEMED,
    ASSERTION_REPLAY_REJECTED,
    PICKUP_CREATED,
    PICKUP_REDEEMED,
    PICKUP_EXPIRED,
    PICKUP_REPLAY_REJECTED,
)
HANDOFF_EVENT_TYPES: tuple[str, ...] = (
    HANDOFF_ACCEPTED,
    HANDOFF_REJECTED,
    HANDOFF_EXPIRED,
    HANDOFF_REPLAY_REJECTED,
)
INTEGRITY_EVENT_TYPES: tuple[str, ...] = (
    COHORT_THRESHOLD_NOT_MET,
    TIMING_PROFILE_APPLIED,
    CORRELATION_RISK_DETECTED,
    INTEGRITY_VIOLATION_DETECTED,
)
ALL_EVENT_TYPES: tuple[str, ...] = (
    ELIGIBILITY_EVENT_TYPES + ASSERTION_EVENT_TYPES + HANDOFF_EVENT_TYPES + INTEGRITY_EVENT_TYPES
)
