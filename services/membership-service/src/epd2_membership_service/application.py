"""Membership Service application layer (PACK-07, canon-0.6.0).

Cross-pack boundary (ADR-027): this module imports exactly three
functions across pack boundaries - `epd2_identity_service.application.
get_identity_participation_claims` (Stage A identity-layer facts),
`epd2_eligibility_service.application.get_eligibility_decision` (the one
sanctioned read of a subject's already-published participant-eligibility
verdict), and `epd2_governance_service.application.
verify_decision_authorizes_policy_activation` (reused generically for
both critical-policy activation and Stage B/`ConflictAssessment` human-
decision-authority verification) - never any `.storage`/`.domain` module
(`tests/repository/test_service_boundaries.py`). Store passthrough
parameters for those three edges are accepted as `object` (the same
convention `epd2_voting_service.application.invalidate_ballot`, ADR-017,
and `epd2_eligibility_service.application`'s own PACK-07 additions
already establish) so this module never needs to import the type of a
store it does not own.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from epd2_audit_core.application import AppendAuditEventRequest, append_audit_event
from epd2_audit_core.domain import AuditEvent
from epd2_audit_core.storage import AuditEventStore
from epd2_core.clock import Clock
from epd2_core.event_envelope import ActorRef, EventEnvelope, compute_payload_hash
from epd2_core.identifiers import generate_uuid
from epd2_eligibility_service.application import get_eligibility_decision
from epd2_governance_service.application import verify_decision_authorizes_policy_activation
from epd2_identity_service.application import get_identity_participation_claims
from epd2_membership_service.domain import (
    AffiliationDeclaration,
    AffiliationStatus,
    AffiliationType,
    Appeal,
    AppealStatus,
    ConflictAssessment,
    ConflictAssessmentStatus,
    ConflictType,
    CriticalPolicyActivationGate,
    CriticalPolicyStatus,
    IncompatibilityLevel,
    Membership,
    MembershipApplication,
    MembershipApplicationStatus,
    MembershipDerivedClaims,
    MembershipStatus,
    PartyMembershipEligibilityPolicy,
    StageAEligibilityResult,
    assert_critical_policy_activation_gate,
)
from epd2_membership_service.events import (
    build_affiliation_declared_event,
    build_conflict_assessment_opened_event,
    build_conflict_decision_recorded_event,
    build_membership_activated_event,
    build_membership_application_submitted_event,
    build_membership_decision_recorded_event,
    build_membership_eligibility_evaluated_event,
    build_membership_suspended_event,
    conflict_assessment_state_payload,
    membership_application_state_payload,
    membership_state_payload,
)
from epd2_membership_service.exceptions import (
    ConflictReviewSelfApprovalProhibitedError,
    MembershipDecisionAuthorityInvalidError,
    MembershipHumanApprovalRequiredError,
    PermissionDeniedError,
    UnknownAffiliationDeclarationError,
    UnknownAppealError,
    UnknownConflictAssessmentError,
    UnknownMembershipApplicationError,
    UnknownMembershipError,
    UnknownPartyMembershipEligibilityPolicyError,
)
from epd2_membership_service.storage import (
    AffiliationDeclarationStore,
    AppealStore,
    ConflictAssessmentStore,
    MembershipApplicationStore,
    MembershipStore,
    PartyMembershipEligibilityPolicyStore,
)

AUDIT_POLICY_VERSION = "1.0"
_SOURCE_SERVICE = "membership-service"


@dataclass(frozen=True, slots=True)
class MembershipApplicationResult:
    application: MembershipApplication
    event: EventEnvelope
    audit_event: AuditEvent


def submit_membership_application(
    store: MembershipApplicationStore,
    audit_store: AuditEventStore,
    *,
    membership_application_id: UUID,
    subject_reference: UUID,
    supersedes_membership_application_id: UUID | None,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
) -> MembershipApplicationResult:
    """Canon 19d.9: create a new `MembershipApplication`, immediately
    entering Stage A (`eligibility_review`) - the `application_pending`
    moment itself has no distinct action to perform beyond existing.
    Emits `MembershipApplicationSubmitted`."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to submit a membership application")
    pending = MembershipApplication(
        membership_application_id=membership_application_id,
        subject_reference=subject_reference,
        status=MembershipApplicationStatus.APPLICATION_PENDING,
        supersedes_membership_application_id=supersedes_membership_application_id,
    )
    under_review = pending.with_status(MembershipApplicationStatus.ELIGIBILITY_REVIEW)
    store.save(under_review)

    now = clock.now()
    event = build_membership_application_submitted_event(
        event_id=generate_uuid(),
        application=under_review,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=event.event_id,
            event_type=event.event_type,
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="membership_application",
            target_id=under_review.membership_application_id,
            action="submit",
            reason_code="MEMBERSHIP_APPLICATION_SUBMITTED",
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash="",
            after_hash=compute_payload_hash(membership_application_state_payload(under_review)),
        ),
        clock=clock,
    )
    return MembershipApplicationResult(
        application=under_review, event=event, audit_event=audit_event
    )


@dataclass(frozen=True, slots=True)
class StageAResult:
    application: MembershipApplication
    result: StageAEligibilityResult
    event: EventEnvelope
    audit_event: AuditEvent


def evaluate_membership_application_eligibility(
    application_store: MembershipApplicationStore,
    policy_store: PartyMembershipEligibilityPolicyStore,
    identity_record_store: object,
    audit_store: AuditEventStore,
    *,
    membership_application_id: UUID,
    identity_record_id: UUID,
    scope_type: str | None,
    scope_id: UUID | None,
    effective_date: datetime,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
) -> StageAResult:
    """Canon 19d.9 Stage A: a formal eligibility evaluation against the
    active `PartyMembershipEligibilityPolicy`, using
    `identity-service.application.get_identity_participation_claims`
    (ADR-027). **Never itself activates or rejects the application** -
    canon 19d.16's hard human-control invariant: this always produces a
    `recommended` outcome and always transitions to
    `human_decision_pending`, regardless of the recommendation."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to evaluate this application")
    application = application_store.get(membership_application_id)
    if application is None:
        raise UnknownMembershipApplicationError(
            f"unknown membership_application_id: {membership_application_id}"
        )
    policy = policy_store.resolve_for_evaluation(
        scope_type=scope_type, scope_id=scope_id, effective_date=effective_date
    )
    if policy is None:
        raise UnknownPartyMembershipEligibilityPolicyError(
            "no active PartyMembershipEligibilityPolicy for the given scope/date"
        )

    identity_claims = get_identity_participation_claims(
        identity_record_store,  # type: ignore[arg-type]
        identity_record_id=identity_record_id,
        required_identity_assurance_level="substantial",
        minimum_age=None,
        eligible_citizenship_set=(),
        residence_rule=None,
        territorial_scope_rule=None,
        evaluated_at=effective_date,
    )
    reason_codes: list[str] = []
    if not identity_claims.identity_verified:
        reason_codes.append("IDENTITY_NOT_VERIFIED")
    recommended_approval = identity_claims.identity_verified and not policy.incompatibility_rules
    if policy.incompatibility_rules and identity_claims.identity_verified:
        # Presence of any pre-declared incompatibility rule on the active
        # policy is, by itself, only ever a signal Stage A surfaces to
        # the human decision-maker (canon 19d.16) - never a silent
        # auto-rejection.
        reason_codes.append("MEMBERSHIP_HUMAN_APPROVAL_REQUIRED")

    result = StageAEligibilityResult(
        recommended_approval=recommended_approval, reason_codes=tuple(reason_codes)
    )
    updated = application.with_status(MembershipApplicationStatus.HUMAN_DECISION_PENDING)
    application_store.save(updated)

    now = clock.now()
    event = build_membership_eligibility_evaluated_event(
        event_id=generate_uuid(),
        application=updated,
        recommended_approval=recommended_approval,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=event.event_id,
            event_type=event.event_type,
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="membership_application",
            target_id=updated.membership_application_id,
            action="evaluate_eligibility",
            reason_code="MEMBERSHIP_ELIGIBILITY_EVALUATED",
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash="",
            after_hash=compute_payload_hash(membership_application_state_payload(updated)),
        ),
        clock=clock,
    )
    return StageAResult(application=updated, result=result, event=event, audit_event=audit_event)


def _verify_decision_authority(
    governance_decision_store: object, *, decision_authority_reference: UUID
) -> None:
    """Shared Stage B / `ConflictAssessment` decision-authority check:
    the referenced `GovernanceDecision` must be real and `approved`.
    Unlike critical-policy activation, an individual membership/conflict
    decision does not additionally require `multi_person_approval_met` -
    that stricter gate is reserved for critical-policy activation
    (canon 19d.7), never for an individual consequential decision."""
    authorization = verify_decision_authorizes_policy_activation(
        governance_decision_store,  # type: ignore[arg-type]
        governance_decision_id=decision_authority_reference,
    )
    if not authorization.authorized:
        raise MembershipDecisionAuthorityInvalidError(
            f"decision_authority_reference {decision_authority_reference} does not resolve "
            "to a real, approved GovernanceDecision"
        )


@dataclass(frozen=True, slots=True)
class MembershipDecisionResult:
    application: MembershipApplication
    membership: Membership | None
    event: EventEnvelope
    audit_event: AuditEvent


def record_membership_human_decision(
    application_store: MembershipApplicationStore,
    membership_store: MembershipStore,
    governance_decision_store: object,
    audit_store: AuditEventStore,
    *,
    membership_application_id: UUID,
    outcome: str,
    decision_authority_reference: UUID,
    applied_policy_version: int,
    reason_code: str,
    membership_id: UUID | None = None,
    account_reference: UUID | None = None,
    organization_id: UUID | None = None,
    membership_type: str | None = None,
    region_code: str | None = None,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
) -> MembershipDecisionResult:
    """Canon 19d.9 Stage B: the authorized human decision. `outcome` must
    be `"approved"` or `"rejected"` - never any other
    `MembershipApplicationStatus` value (task 5's human-control
    invariant: this is the ONLY function that may move a
    `MembershipApplication` out of `human_decision_pending`). A
    `rejected` outcome also sets `Membership.membership_status = rejected`
    in the same call; an `approved` outcome does NOT itself activate
    membership - see `activate_membership` (ADR-030 item 2's distinct
    final step)."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to record a membership decision")
    if outcome not in ("approved", "rejected"):
        raise ValueError(f"outcome must be 'approved' or 'rejected', got {outcome!r}")

    application = application_store.get(membership_application_id)
    if application is None:
        raise UnknownMembershipApplicationError(
            f"unknown membership_application_id: {membership_application_id}"
        )
    if application.status is not MembershipApplicationStatus.HUMAN_DECISION_PENDING:
        raise MembershipHumanApprovalRequiredError(
            f"membership_application {membership_application_id} is not awaiting a human "
            f"decision (status={application.status.value!r})"
        )

    _verify_decision_authority(
        governance_decision_store, decision_authority_reference=decision_authority_reference
    )

    now = clock.now()
    new_status = (
        MembershipApplicationStatus.APPROVED
        if outcome == "approved"
        else MembershipApplicationStatus.REJECTED
    )
    updated = application.with_status(
        new_status,
        decision_authority_reference=decision_authority_reference,
        applied_policy_version=applied_policy_version,
        reason_code=reason_code,
        decided_at=now,
        audit_event_reference=generate_uuid(),
    )
    application_store.save(updated)

    membership: Membership | None = None
    if outcome == "rejected":
        if membership_id is None or account_reference is None or organization_id is None:
            raise ValueError(
                "membership_id, account_reference, and organization_id are required "
                "to record a rejected Membership row"
            )
        membership = Membership(
            membership_id=membership_id,
            account_reference=account_reference,
            organization_id=organization_id,
            membership_type=membership_type or "party",
            membership_status=MembershipStatus.REJECTED,
            effective_from=None,
            effective_until=None,
            region_code=region_code,
        )
        membership_store.save(membership)

    event = build_membership_decision_recorded_event(
        event_id=generate_uuid(),
        application=updated,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=event.event_id,
            event_type=event.event_type,
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="membership_application",
            target_id=updated.membership_application_id,
            action="record_human_decision",
            reason_code=reason_code,
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash="",
            after_hash=compute_payload_hash(membership_application_state_payload(updated)),
        ),
        clock=clock,
    )
    return MembershipDecisionResult(
        application=updated, membership=membership, event=event, audit_event=audit_event
    )


@dataclass(frozen=True, slots=True)
class MembershipActivationResult:
    application: MembershipApplication
    membership: Membership
    event: EventEnvelope
    audit_event: AuditEvent


def activate_membership(
    application_store: MembershipApplicationStore,
    membership_store: MembershipStore,
    audit_store: AuditEventStore,
    *,
    membership_application_id: UUID,
    membership_id: UUID,
    account_reference: UUID,
    organization_id: UUID,
    membership_type: str,
    region_code: str | None,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
) -> MembershipActivationResult:
    """ADR-030 item 2's distinct final step: `approved -> activated` on
    the `MembershipApplication`, and only here does
    `Membership.membership_status` become `active`. No code path may set
    `active` any other way (canon 19d.9's binding rule)."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to activate this membership")
    application = application_store.get(membership_application_id)
    if application is None:
        raise UnknownMembershipApplicationError(
            f"unknown membership_application_id: {membership_application_id}"
        )
    if application.status is not MembershipApplicationStatus.APPROVED:
        raise MembershipHumanApprovalRequiredError(
            f"membership_application {membership_application_id} has not been approved "
            f"(status={application.status.value!r})"
        )
    updated_application = application.with_status(MembershipApplicationStatus.ACTIVATED)
    application_store.save(updated_application)

    now = clock.now()
    membership = Membership(
        membership_id=membership_id,
        account_reference=account_reference,
        organization_id=organization_id,
        membership_type=membership_type,
        membership_status=MembershipStatus.ACTIVE,
        effective_from=now,
        effective_until=None,
        region_code=region_code,
    )
    membership_store.save(membership)

    event = build_membership_activated_event(
        event_id=generate_uuid(),
        membership=membership,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=event.event_id,
            event_type=event.event_type,
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="membership",
            target_id=membership.membership_id,
            action="activate",
            reason_code="MEMBERSHIP_ACTIVATED",
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash="",
            after_hash=compute_payload_hash(membership_state_payload(membership)),
        ),
        clock=clock,
    )
    return MembershipActivationResult(
        application=updated_application, membership=membership, event=event, audit_event=audit_event
    )


@dataclass(frozen=True, slots=True)
class MembershipSuspensionResult:
    membership: Membership
    event: EventEnvelope
    audit_event: AuditEvent


def suspend_membership(
    membership_store: MembershipStore,
    governance_decision_store: object,
    audit_store: AuditEventStore,
    *,
    membership_id: UUID,
    decision_authority_reference: UUID,
    reason_code: str,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
) -> MembershipSuspensionResult:
    """Canon 19d.16's third consequential outcome: `active -> suspended`,
    gated on an authorized `GovernanceDecision` reference - never a bare
    status flip. Emits `MembershipSuspended`."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to suspend this membership")
    membership = membership_store.get(membership_id)
    if membership is None:
        raise UnknownMembershipError(f"unknown membership_id: {membership_id}")
    _verify_decision_authority(
        governance_decision_store, decision_authority_reference=decision_authority_reference
    )
    updated = membership.with_status(MembershipStatus.SUSPENDED)
    membership_store.save(updated)

    now = clock.now()
    event = build_membership_suspended_event(
        event_id=generate_uuid(),
        membership=updated,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=event.event_id,
            event_type=event.event_type,
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="membership",
            target_id=updated.membership_id,
            action="suspend",
            reason_code=reason_code,
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash="",
            after_hash=compute_payload_hash(membership_state_payload(updated)),
        ),
        clock=clock,
    )
    return MembershipSuspensionResult(membership=updated, event=event, audit_event=audit_event)


def get_membership_derived_claims(
    membership_store: MembershipStore,
    *,
    account_reference: UUID,
    organization_id: UUID,
    required_membership_status: str = "active",
    minimum_duration_days: int | None = None,
    evaluated_at: datetime,
) -> MembershipDerivedClaims:
    """ADR-027's narrow read: the ONLY function `eligibility-service` may
    import from this module. Returns two booleans plus a reason code -
    never the raw `Membership` row, `organization_id`, or
    `membership_status` value itself."""
    membership = membership_store.get_for_account(
        account_reference=account_reference, organization_id=organization_id
    )
    if membership is None:
        return MembershipDerivedClaims(
            required_membership_status_met=False,
            membership_duration_requirement_met=False,
            reason_code="MEMBERSHIP_HUMAN_APPROVAL_REQUIRED",
        )
    status_met = membership.membership_status.value == required_membership_status
    duration_met = True
    if minimum_duration_days is not None:
        if membership.effective_from is None:
            duration_met = False
        else:
            duration_met = (evaluated_at - membership.effective_from).days >= minimum_duration_days
    reason_code = None if (status_met and duration_met) else "MEMBERSHIP_HUMAN_APPROVAL_REQUIRED"
    return MembershipDerivedClaims(
        required_membership_status_met=status_met,
        membership_duration_requirement_met=duration_met,
        reason_code=reason_code,
    )


def read_participant_eligibility_decision(
    eligibility_decision_store: object, *, eligibility_decision_id: UUID
) -> object:
    """ADR-027's other narrow read this service may perform: a subject's
    already-published `EligibilityDecision` (canon 9.2, unchanged, reused
    - never `eligibility-service`'s `ParticipantEligibilityPolicy` row or
    `EligibilityRule` content itself). Thin passthrough to
    `eligibility-service.application.get_eligibility_decision`
    (ADR-008's own precedent function, reused here for a second,
    independently-authorized caller)."""
    return get_eligibility_decision(
        eligibility_decision_store,  # type: ignore[arg-type]
        eligibility_decision_id=eligibility_decision_id,
    )


@dataclass(frozen=True, slots=True)
class AffiliationResult:
    declaration: AffiliationDeclaration
    event: EventEnvelope
    audit_event: AuditEvent


def declare_affiliation(
    store: AffiliationDeclarationStore,
    audit_store: AuditEventStore,
    *,
    affiliation_declaration_id: UUID,
    subject_reference: UUID,
    affiliation_type: str,
    declared_reference: str,
    valid_from: datetime,
    valid_until: datetime | None = None,
    supersedes_declaration_id: UUID | None = None,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
) -> AffiliationResult:
    """Canon 19d.10: create a new `AffiliationDeclaration` in `submitted`.
    Emits `AffiliationDeclared`. Where `supersedes_declaration_id` is
    given, the superseded declaration is independently transitioned to
    `superseded` via `supersede_declaration` (never mutated in place by
    this function)."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to declare an affiliation")
    now = clock.now()
    declaration = AffiliationDeclaration(
        affiliation_declaration_id=affiliation_declaration_id,
        subject_reference=subject_reference,
        affiliation_type=AffiliationType(affiliation_type),
        declared_reference=declared_reference,
        declared_at=now,
        status=AffiliationStatus.SUBMITTED,
        valid_from=valid_from,
        valid_until=valid_until,
        supersedes_declaration_id=supersedes_declaration_id,
    )
    store.save(declaration)
    event = build_affiliation_declared_event(
        event_id=generate_uuid(),
        declaration=declaration,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=event.event_id,
            event_type=event.event_type,
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="affiliation_declaration",
            target_id=declaration.affiliation_declaration_id,
            action="declare",
            reason_code="AFFILIATION_DECLARED",
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash="",
            after_hash=compute_payload_hash(
                {"affiliation_declaration_id": str(affiliation_declaration_id)}
            ),
        ),
        clock=clock,
    )
    return AffiliationResult(declaration=declaration, event=event, audit_event=audit_event)


def supersede_declaration(
    store: AffiliationDeclarationStore, *, affiliation_declaration_id: UUID
) -> AffiliationDeclaration:
    """Transition an existing `AffiliationDeclaration` to `superseded`
    (canon 19d.10's `supersedes_declaration_id` pattern: a correction is
    always a new declaration referencing this one, never a rewrite of
    it)."""
    declaration = store.get(affiliation_declaration_id)
    if declaration is None:
        raise UnknownAffiliationDeclarationError(
            f"unknown affiliation_declaration_id: {affiliation_declaration_id}"
        )
    updated = declaration.with_status(AffiliationStatus.SUPERSEDED)
    store.save(updated)
    return updated


@dataclass(frozen=True, slots=True)
class ConflictAssessmentResult:
    assessment: ConflictAssessment
    event: EventEnvelope
    audit_event: AuditEvent


def open_conflict_assessment(
    store: ConflictAssessmentStore,
    audit_store: AuditEventStore,
    *,
    conflict_assessment_id: UUID,
    subject_reference: UUID,
    conflict_type: str,
    reviewed_by_role_reference: UUID,
    affiliation_declaration_id: UUID | None = None,
    evidence_references: Sequence[str] = (),
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
) -> ConflictAssessmentResult:
    """Canon 19d.11: open a new `ConflictAssessment` in `pending`. The
    reviewer must never be the subject under assessment (canon 19d.11's
    own reviewer-separation rule)."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to open a conflict assessment")
    if reviewed_by_role_reference == subject_reference:
        raise ConflictReviewSelfApprovalProhibitedError(
            "reviewed_by_role_reference must not equal the subject under assessment"
        )
    assessment = ConflictAssessment(
        conflict_assessment_id=conflict_assessment_id,
        subject_reference=subject_reference,
        conflict_type=ConflictType(conflict_type),
        incompatibility_level=IncompatibilityLevel.NONE,
        status=ConflictAssessmentStatus.PENDING,
        reviewed_by_role_reference=reviewed_by_role_reference,
        affiliation_declaration_id=affiliation_declaration_id,
        evidence_references=tuple(evidence_references),
    )
    store.save(assessment)
    now = clock.now()
    event = build_conflict_assessment_opened_event(
        event_id=generate_uuid(),
        assessment=assessment,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=event.event_id,
            event_type=event.event_type,
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="conflict_assessment",
            target_id=assessment.conflict_assessment_id,
            action="open",
            reason_code="CONFLICT_ASSESSMENT_OPENED",
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash="",
            after_hash=compute_payload_hash(conflict_assessment_state_payload(assessment)),
        ),
        clock=clock,
    )
    return ConflictAssessmentResult(assessment=assessment, event=event, audit_event=audit_event)


def record_conflict_decision(
    store: ConflictAssessmentStore,
    governance_decision_store: object,
    audit_store: AuditEventStore,
    *,
    conflict_assessment_id: UUID,
    new_status: str,
    incompatibility_level: str,
    reason_codes: Sequence[str],
    decision_authority_reference: UUID | None,
    re_evaluation_due_at: datetime | None = None,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
) -> ConflictAssessmentResult:
    """Canon 19d.11/19d.16: records the authorized human decision
    resolving a `ConflictAssessment`. `decision_authority_reference` is
    mandatory - and independently verified against `governance-service`
    - when `new_status='resolved_incompatible'` (canon 19d.11's own
    mandatory-field rule, `domain.ConflictAssessment.__post_init__`,
    re-checked here fail-closed before any governance call is made)."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to record a conflict decision")
    assessment = store.get(conflict_assessment_id)
    if assessment is None:
        raise UnknownConflictAssessmentError(
            f"unknown conflict_assessment_id: {conflict_assessment_id}"
        )
    resolved_status = ConflictAssessmentStatus(new_status)
    if (
        resolved_status is ConflictAssessmentStatus.RESOLVED_INCOMPATIBLE
        and decision_authority_reference is None
    ):
        raise MembershipHumanApprovalRequiredError(
            "decision_authority_reference is required for resolved_incompatible "
            "(canon 19d.11/19d.16)"
        )
    if decision_authority_reference is not None:
        _verify_decision_authority(
            governance_decision_store, decision_authority_reference=decision_authority_reference
        )
    now = clock.now()
    updated = assessment.with_decision(
        new_status=resolved_status,
        incompatibility_level=IncompatibilityLevel(incompatibility_level),
        reason_codes=tuple(reason_codes),
        decision_authority_reference=decision_authority_reference,
        decided_at=now,
        re_evaluation_due_at=re_evaluation_due_at,
    )
    store.save(updated)
    event = build_conflict_decision_recorded_event(
        event_id=generate_uuid(),
        assessment=updated,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=event.event_id,
            event_type=event.event_type,
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="conflict_assessment",
            target_id=updated.conflict_assessment_id,
            action="record_decision",
            reason_code=(reason_codes[0] if reason_codes else "CONFLICT_DECISION_RECORDED"),
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash="",
            after_hash=compute_payload_hash(conflict_assessment_state_payload(updated)),
        ),
        clock=clock,
    )
    return ConflictAssessmentResult(assessment=updated, event=event, audit_event=audit_event)


def activate_party_membership_eligibility_policy(
    store: PartyMembershipEligibilityPolicyStore,
    governance_decision_store: object,
    *,
    policy_id: UUID,
    actor_is_authorized: bool,
) -> PartyMembershipEligibilityPolicy:
    """Canon 19d.7's four-gate activation, this service's own critical
    policy (`PartyMembershipEligibilityPolicy`). No canonical event -
    mirrors `eligibility-service.application.
    activate_participant_eligibility_policy`'s own precedent for a
    policy-row activation with no dedicated PACK-07 event name."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to activate this policy")
    policy = store.get(policy_id)
    if policy is None:
        raise UnknownPartyMembershipEligibilityPolicyError(f"unknown policy_id: {policy_id}")
    authorization = verify_decision_authorizes_policy_activation(
        governance_decision_store,  # type: ignore[arg-type]
        governance_decision_id=policy.adopted_by_decision_id,
    )
    gate = CriticalPolicyActivationGate(
        decision_authorized=authorization.authorized,
        multi_person_approval_met=authorization.multi_person_approval_met,
        signed_policy_digest_reference=policy.signed_policy_digest_reference,
        transparency_log_commitment_reference=policy.transparency_log_commitment_reference,
    )
    assert_critical_policy_activation_gate(gate)
    activated = policy.with_status(CriticalPolicyStatus.ACTIVE)
    store.save(activated)
    return activated


@dataclass(frozen=True, slots=True)
class AppealResult:
    appeal: Appeal
    event: EventEnvelope | None
    audit_event: AuditEvent | None


def submit_membership_appeal(
    store: AppealStore,
    audit_store: AuditEventStore,
    *,
    appeal_id: UUID,
    decision_id: UUID,
    submitted_by: UUID,
    grounds: str,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
) -> Appeal:
    """ADR-030 item 4: reuse canon's polymorphic `Appeal` (14.3) for a
    `ConflictAssessment`/`MembershipApplication` rejection appeal -
    `decision_id` is set to whichever `conflict_assessment_id`/
    `membership_application_id` is being appealed. No dedicated
    `MembershipAppeal` entity (ADR-030 item 4's standing default)."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to submit an appeal")
    del audit_store, correlation_id, clock, actor  # unaudited, mirrors domain-level test coverage
    appeal = Appeal(
        appeal_id=appeal_id,
        decision_id=decision_id,
        submitted_by=submitted_by,
        grounds=grounds,
        status=AppealStatus.SUBMITTED,
        reviewer_actor_id=None,
        result=None,
    )
    store.save(appeal)
    return appeal


def decide_membership_appeal(
    store: AppealStore,
    *,
    appeal_id: UUID,
    reviewer_actor_id: UUID,
    original_decision_author_reference: UUID,
    outcome: str,
    result: str,
    actor_is_authorized: bool,
) -> Appeal:
    """Canon 14.3's reviewer-separation rule, restated for this service's
    reused `Appeal`: `reviewer_actor_id` must differ from whichever actor
    authored the original `ConflictAssessment`/`MembershipApplication`
    decision being appealed (`original_decision_author_reference`,
    resolved by the caller - this function's own signature mirrors
    `epd2_moderation_service.application.decide_appeal`'s identical
    check)."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to decide an appeal")
    if reviewer_actor_id == original_decision_author_reference:
        raise PermissionDeniedError(
            "an appeal must not be finally decided by the actor who made the original "
            "decision (canon section 14.3)"
        )
    appeal = store.get(appeal_id)
    if appeal is None:
        raise UnknownAppealError(f"unknown appeal_id: {appeal_id}")

    final_outcome = AppealStatus(outcome)
    stage_1 = appeal.with_reviewer_and_status(
        reviewer_actor_id=reviewer_actor_id,
        new_status=AppealStatus.ADMISSIBILITY_REVIEW,
        result=None,
    )
    stage_2 = stage_1.with_reviewer_and_status(
        reviewer_actor_id=reviewer_actor_id, new_status=AppealStatus.UNDER_REVIEW, result=None
    )
    final = stage_2.with_reviewer_and_status(
        reviewer_actor_id=reviewer_actor_id, new_status=final_outcome, result=result
    )
    store.save(final)
    return final
