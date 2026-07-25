"""Canonical events emitted by Eligibility Service (canon section 20.3)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from epd2_core.event_envelope import ActorRef, EventEnvelope, SubjectRef, build_event_envelope
from epd2_eligibility_service.domain import (
    AssemblyDecision,
    DigitalDecision,
    EligibilityDecision,
    EligibilitySnapshot,
    ProcessEligibilityClaims,
)

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


# ---------------------------------------------------------------------------
# PACK-07 additions (canon 19d.3/19d.12/19d.14, canon-0.6.0)
# ---------------------------------------------------------------------------


def build_participation_rights_derived_event(
    *,
    event_id: UUID,
    subject_reference: UUID,
    process_id: UUID,
    action_code: str,
    claims: ProcessEligibilityClaims,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`ParticipationRightsDerived` (canon 19d.14): marks that a
    participant-side capability derivation happened for exactly one
    `(subject_reference, process_id, action_code)` tuple - never the full,
    non-persisted `ParticipationRightsProfile` (canon 19d.1/19d.14). Only
    the four already-public claim booleans are carried, never any
    identity or membership fact that produced them."""
    payload = {
        "subject_reference": str(subject_reference),
        "process_id": str(process_id),
        "action_code": action_code,
        "active_electoral_eligibility_met": claims.active_electoral_eligibility_met,
        "passive_electoral_eligibility_met": claims.passive_electoral_eligibility_met,
        "party_internal_voting_eligibility_met": claims.party_internal_voting_eligibility_met,
        "party_office_candidacy_eligibility_met": claims.party_office_candidacy_eligibility_met,
    }
    return build_event_envelope(
        event_id=event_id,
        event_type="eligibility.participation_rights_derived",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="eligibility-service",
        actor=actor,
        subject=SubjectRef(subject_type="process_eligibility_claims", subject_id=process_id),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=payload,
    )


def digital_decision_state_payload(decision: DigitalDecision) -> dict[str, object]:
    """Full, canonically-hashable snapshot of a `DigitalDecision`'s own
    state, used for Audit Core's `after_hash`."""
    return {
        "digital_decision_id": str(decision.digital_decision_id),
        "process_reference": dict(decision.process_reference),
        "digital_result": decision.digital_result,
        "decision_effect": decision.decision_effect.value,
        "formal_confirmation_required": decision.formal_confirmation_required,
        "status": decision.status.value,
        "recorded_at": decision.recorded_at.isoformat(),
    }


def assembly_decision_state_payload(decision: AssemblyDecision) -> dict[str, object]:
    """Full, canonically-hashable snapshot of an `AssemblyDecision`'s own
    state, used for Audit Core's `after_hash`."""
    return {
        "assembly_decision_id": str(decision.assembly_decision_id),
        "digital_decision_id": str(decision.digital_decision_id),
        "confirming_authority": decision.confirming_authority,
        "legal_basis": decision.legal_basis,
        "confirmation_deadline": decision.confirmation_deadline.isoformat(),
        "protocol_or_evidence_reference": decision.protocol_or_evidence_reference,
        "status": decision.status.value,
        "final_legal_decision": decision.final_legal_decision,
        "divergence_explanation": decision.divergence_explanation,
        "decided_at": decision.decided_at.isoformat() if decision.decided_at else None,
    }


def build_formal_confirmation_requested_event(
    *,
    event_id: UUID,
    assembly_decision: AssemblyDecision,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`FormalConfirmationRequested` (canon 19d.12): emitted when a
    `DigitalDecision.status=formal_confirmation_required` produces its
    one `AssemblyDecision` row (ADR-030 item 8's "confirmation-required
    path"). Never carries `digital_result` itself - only the reference
    and deadline a confirming authority needs to act."""
    payload = {
        "assembly_decision_id": str(assembly_decision.assembly_decision_id),
        "digital_decision_id": str(assembly_decision.digital_decision_id),
        "confirming_authority": assembly_decision.confirming_authority,
        "confirmation_deadline": assembly_decision.confirmation_deadline.isoformat(),
    }
    return build_event_envelope(
        event_id=event_id,
        event_type="eligibility.formal_confirmation_requested",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="eligibility-service",
        actor=actor,
        subject=SubjectRef(
            subject_type="assembly_decision", subject_id=assembly_decision.assembly_decision_id
        ),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=payload,
    )


def build_formal_confirmation_recorded_event(
    *,
    event_id: UUID,
    assembly_decision: AssemblyDecision,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`FormalConfirmationRecorded` (canon 19d.12): emitted once an
    `AssemblyDecision` reaches a terminal status (`confirmed`/`rejected`/
    `returned_for_revision`, ADR-030 item 8). Carries `final_legal_decision`
    and, where applicable, `divergence_explanation` - the confirming
    authority's own recorded outcome, never a re-statement of the
    originating `DigitalDecision.digital_result`."""
    payload = {
        "assembly_decision_id": str(assembly_decision.assembly_decision_id),
        "digital_decision_id": str(assembly_decision.digital_decision_id),
        "status": assembly_decision.status.value,
        "final_legal_decision": assembly_decision.final_legal_decision,
        "divergence_explanation": assembly_decision.divergence_explanation,
    }
    return build_event_envelope(
        event_id=event_id,
        event_type="eligibility.formal_confirmation_recorded",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="eligibility-service",
        actor=actor,
        subject=SubjectRef(
            subject_type="assembly_decision", subject_id=assembly_decision.assembly_decision_id
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
