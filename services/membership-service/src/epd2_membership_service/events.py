"""Canonical events emitted by Membership Service (canon section 20.3,
PACK-07 implementation round)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from epd2_core.event_envelope import ActorRef, EventEnvelope, SubjectRef, build_event_envelope
from epd2_membership_service.domain import (
    AffiliationDeclaration,
    ConflictAssessment,
    Membership,
    MembershipApplication,
)

EVENT_VERSION = "1.0"
SUPPORTED_MAJOR_VERSIONS = frozenset({1})


def membership_application_state_payload(application: MembershipApplication) -> dict[str, object]:
    """Full, canonically-hashable snapshot of a `MembershipApplication`'s
    own state, used for Audit Core's `after_hash`."""
    return {
        "membership_application_id": str(application.membership_application_id),
        "subject_reference": str(application.subject_reference),
        "status": application.status.value,
        "decision_authority_reference": (
            str(application.decision_authority_reference)
            if application.decision_authority_reference
            else None
        ),
        "applied_policy_version": application.applied_policy_version,
        "reason_code": application.reason_code,
        "decided_at": application.decided_at.isoformat() if application.decided_at else None,
        "audit_event_reference": (
            str(application.audit_event_reference) if application.audit_event_reference else None
        ),
        "supersedes_membership_application_id": (
            str(application.supersedes_membership_application_id)
            if application.supersedes_membership_application_id
            else None
        ),
    }


def membership_state_payload(membership: Membership) -> dict[str, object]:
    """Full, canonically-hashable snapshot of a `Membership`'s own state,
    used for Audit Core's `after_hash`. Never broadcast on a wire event
    payload directly (ADR-030 item 5's disclosure-by-default prohibition)."""
    return {
        "membership_id": str(membership.membership_id),
        "account_reference": str(membership.account_reference),
        "organization_id": str(membership.organization_id),
        "membership_type": membership.membership_type,
        "membership_status": membership.membership_status.value,
        "effective_from": (
            membership.effective_from.isoformat() if membership.effective_from else None
        ),
        "effective_until": (
            membership.effective_until.isoformat() if membership.effective_until else None
        ),
        "region_code": membership.region_code,
    }


def affiliation_declaration_state_payload(
    declaration: AffiliationDeclaration,
) -> dict[str, object]:
    """Full, canonically-hashable snapshot of an `AffiliationDeclaration`'s
    own state, used for Audit Core's `after_hash`."""
    return {
        "affiliation_declaration_id": str(declaration.affiliation_declaration_id),
        "subject_reference": str(declaration.subject_reference),
        "affiliation_type": declaration.affiliation_type.value,
        "declared_reference": declaration.declared_reference,
        "declared_at": declaration.declared_at.isoformat(),
        "status": declaration.status.value,
        "valid_from": declaration.valid_from.isoformat(),
        "valid_until": declaration.valid_until.isoformat() if declaration.valid_until else None,
        "verification_status": declaration.verification_status.value,
        "verified_at": declaration.verified_at.isoformat() if declaration.verified_at else None,
        "verified_by": str(declaration.verified_by) if declaration.verified_by else None,
        "supersedes_declaration_id": (
            str(declaration.supersedes_declaration_id)
            if declaration.supersedes_declaration_id
            else None
        ),
    }


def conflict_assessment_state_payload(assessment: ConflictAssessment) -> dict[str, object]:
    """Full, canonically-hashable snapshot of a `ConflictAssessment`'s
    own state, used for Audit Core's `after_hash`. Covers all thirteen
    fields of the entity (previously missing `evidence_references`,
    `supersedes_conflict_assessment_id`, and `re_evaluation_due_at` -
    found and fixed via PACK-07 contract-test work: a genuinely
    incomplete "full state" snapshot would leave those three fields
    outside Audit Core's tamper-evidence hash)."""
    return {
        "conflict_assessment_id": str(assessment.conflict_assessment_id),
        "subject_reference": str(assessment.subject_reference),
        "conflict_type": assessment.conflict_type.value,
        "incompatibility_level": assessment.incompatibility_level.value,
        "status": assessment.status.value,
        "reviewed_by_role_reference": str(assessment.reviewed_by_role_reference),
        "affiliation_declaration_id": (
            str(assessment.affiliation_declaration_id)
            if assessment.affiliation_declaration_id
            else None
        ),
        "reason_codes": list(assessment.reason_codes),
        "evidence_references": list(assessment.evidence_references),
        "decision_authority_reference": (
            str(assessment.decision_authority_reference)
            if assessment.decision_authority_reference
            else None
        ),
        "decided_at": assessment.decided_at.isoformat() if assessment.decided_at else None,
        "supersedes_conflict_assessment_id": (
            str(assessment.supersedes_conflict_assessment_id)
            if assessment.supersedes_conflict_assessment_id
            else None
        ),
        "re_evaluation_due_at": (
            assessment.re_evaluation_due_at.isoformat() if assessment.re_evaluation_due_at else None
        ),
    }


def build_membership_application_submitted_event(
    *,
    event_id: UUID,
    application: MembershipApplication,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`MembershipApplicationSubmitted` (canon 19d.9). Deliberately
    minimal - never carries any `AffiliationDeclaration`/identity content
    (ADR-030 item 5's disclosure-by-default prohibition)."""
    payload = {
        "membership_application_id": str(application.membership_application_id),
        "status": application.status.value,
    }
    return build_event_envelope(
        event_id=event_id,
        event_type="membership.membership_application_submitted",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="membership-service",
        actor=actor,
        subject=SubjectRef(
            subject_type="membership_application",
            subject_id=application.membership_application_id,
        ),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=payload,
    )


def build_membership_eligibility_evaluated_event(
    *,
    event_id: UUID,
    application: MembershipApplication,
    recommended_approval: bool,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`MembershipEligibilityEvaluated` (canon 19d.9 Stage A). Carries
    only a `recommended` outcome - canon 19d.16's hard human-control
    invariant means this can never itself be read as a final decision."""
    payload = {
        "membership_application_id": str(application.membership_application_id),
        "recommended_approval": recommended_approval,
    }
    return build_event_envelope(
        event_id=event_id,
        event_type="membership.membership_eligibility_evaluated",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="membership-service",
        actor=actor,
        subject=SubjectRef(
            subject_type="membership_application",
            subject_id=application.membership_application_id,
        ),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=payload,
    )


def build_membership_decision_recorded_event(
    *,
    event_id: UUID,
    application: MembershipApplication,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`MembershipDecisionRecorded` (canon 19d.9 Stage B) - the
    authorized human decision itself."""
    payload = {
        "membership_application_id": str(application.membership_application_id),
        "status": application.status.value,
        "decision_authority_reference": str(application.decision_authority_reference),
        "reason_code": application.reason_code,
    }
    return build_event_envelope(
        event_id=event_id,
        event_type="membership.membership_decision_recorded",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="membership-service",
        actor=actor,
        subject=SubjectRef(
            subject_type="membership_application",
            subject_id=application.membership_application_id,
        ),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=payload,
    )


def build_membership_activated_event(
    *,
    event_id: UUID,
    membership: Membership,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`MembershipActivated` - the distinct, final step following an
    `approved` `MembershipApplication` (ADR-030 item 2). Never carries
    `region_code`/`organization_id` on the wire (ADR-030 item 5)."""
    payload = {
        "membership_id": str(membership.membership_id),
        "membership_status": membership.membership_status.value,
    }
    return build_event_envelope(
        event_id=event_id,
        event_type="membership.membership_activated",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="membership-service",
        actor=actor,
        subject=SubjectRef(subject_type="membership", subject_id=membership.membership_id),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=payload,
    )


def build_membership_suspended_event(
    *,
    event_id: UUID,
    membership: Membership,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`MembershipSuspended` - canon 19d.16's second consequential
    outcome requiring an authorized human decision reference."""
    payload = {
        "membership_id": str(membership.membership_id),
        "membership_status": membership.membership_status.value,
    }
    return build_event_envelope(
        event_id=event_id,
        event_type="membership.membership_suspended",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="membership-service",
        actor=actor,
        subject=SubjectRef(subject_type="membership", subject_id=membership.membership_id),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=payload,
    )


def build_affiliation_declared_event(
    *,
    event_id: UUID,
    declaration: AffiliationDeclaration,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`AffiliationDeclared` - never carries `declared_reference` itself
    on the wire (opaque reference, but still restricted-by-default
    affiliation content, ADR-030 item 5)."""
    payload = {
        "affiliation_declaration_id": str(declaration.affiliation_declaration_id),
        "affiliation_type": declaration.affiliation_type.value,
        "status": declaration.status.value,
    }
    return build_event_envelope(
        event_id=event_id,
        event_type="membership.affiliation_declared",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="membership-service",
        actor=actor,
        subject=SubjectRef(
            subject_type="affiliation_declaration",
            subject_id=declaration.affiliation_declaration_id,
        ),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=payload,
    )


def build_conflict_assessment_opened_event(
    *,
    event_id: UUID,
    assessment: ConflictAssessment,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`ConflictAssessmentOpened` - never carries `evidence_references`/
    `reason_codes` on the wire (ADR-030 item 5)."""
    payload = {
        "conflict_assessment_id": str(assessment.conflict_assessment_id),
        "conflict_type": assessment.conflict_type.value,
        "status": assessment.status.value,
    }
    return build_event_envelope(
        event_id=event_id,
        event_type="membership.conflict_assessment_opened",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="membership-service",
        actor=actor,
        subject=SubjectRef(
            subject_type="conflict_assessment", subject_id=assessment.conflict_assessment_id
        ),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=payload,
    )


def build_conflict_decision_recorded_event(
    *,
    event_id: UUID,
    assessment: ConflictAssessment,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`ConflictDecisionRecorded` - the authorized human decision
    resolving a `ConflictAssessment`."""
    payload = {
        "conflict_assessment_id": str(assessment.conflict_assessment_id),
        "status": assessment.status.value,
        "incompatibility_level": assessment.incompatibility_level.value,
        "decision_authority_reference": (
            str(assessment.decision_authority_reference)
            if assessment.decision_authority_reference
            else None
        ),
    }
    return build_event_envelope(
        event_id=event_id,
        event_type="membership.conflict_decision_recorded",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="membership-service",
        actor=actor,
        subject=SubjectRef(
            subject_type="conflict_assessment", subject_id=assessment.conflict_assessment_id
        ),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=payload,
    )
