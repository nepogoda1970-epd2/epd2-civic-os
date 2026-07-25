"""CT-00-01 Schema Validation (canon section 27), PACK-07 additions
(canon-0.6.0, ADR-026 through ADR-031) - added alongside (never
replacing) `test_ct00_01_schema_validation.py`'s own PACK-02/03/04/05/06
coverage.

Validates every new PACK-07 entity schema under `contracts/schemas/`
(`ParticipantEligibilityPolicy`, `ProcessEligibilityPolicy`,
`StepUpAuthenticationRequirement`, `DigitalDecision`, `AssemblyDecision`,
`PartyMembershipEligibilityPolicy`, `Membership`, `MembershipApplication`,
`AffiliationDeclaration`, `ConflictAssessment`) and every new PACK-07
event payload schema under `contracts/events/` (the twelve new events -
`ParticipationRightsDerived`, `FormalConfirmationRequested`,
`FormalConfirmationRecorded`, the shared `AuthenticationContext` payload
covering both `StepUpAuthenticationCompleted` and
`authentication_context_established`, `MembershipApplicationSubmitted`,
`MembershipEligibilityEvaluated`, `MembershipDecisionRecorded`,
`MembershipActivated`, `MembershipSuspended`, `AffiliationDeclared`,
`ConflictAssessmentOpened`, `ConflictDecisionRecorded` - `EligibilityEvaluated`
itself is pre-existing PACK-02 coverage, unchanged) against real,
directly-constructed domain instances - not through a full
application-layer command flow (unlike most of
`test_ct00_01_schema_validation.py`'s own tests), since several of these
entities' realistic construction paths require a full governance
critical-policy activation flow out of scope for a schema-shape test;
each instance below still satisfies every real `__post_init__` structural
invariant the domain class enforces.

Requires nothing beyond `epd2_core.minimal_json_schema` (always
available, stdlib-only) for validation itself.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from _schema_helpers import load_event_schema, load_schema, to_jsonable

from epd2_core.event_envelope import ActorRef
from epd2_core.minimal_json_schema import validate
from epd2_eligibility_service.domain import (
    AgeThreshold,
    AssemblyDecision,
    AssemblyDecisionStatus,
    AssuranceRequirement,
    CriticalPolicyStatus,
    DecisionEffect,
    DigitalDecision,
    DigitalDecisionStatus,
    ParticipantEligibilityPolicy,
    ProcessEligibilityClaims,
    ProcessEligibilityPolicy,
    StepUpAuthenticationRequirement,
)
from epd2_eligibility_service.events import (
    assembly_decision_state_payload,
    build_formal_confirmation_recorded_event,
    build_formal_confirmation_requested_event,
    build_participation_rights_derived_event,
    digital_decision_state_payload,
)
from epd2_identity_service.domain import AuthenticationAssuranceLevel, AuthenticationContext
from epd2_identity_service.events import build_authentication_context_event
from epd2_membership_service.domain import (
    AffiliationDeclaration,
    AffiliationStatus,
    AffiliationType,
    ConflictAssessment,
    ConflictAssessmentStatus,
    ConflictType,
    IncompatibilityLevel,
    Membership,
    MembershipApplication,
    MembershipApplicationStatus,
    MembershipStatus,
    PartyMembershipEligibilityPolicy,
)
from epd2_membership_service.domain import CriticalPolicyStatus as MembershipCriticalPolicyStatus
from epd2_membership_service.events import (
    affiliation_declaration_state_payload,
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

_OCCURRED_AT = datetime(2026, 1, 1, tzinfo=UTC)


def _actor() -> ActorRef:
    return ActorRef(actor_id=uuid4(), actor_type="service")


# ---------------------------------------------------------------------------
# Entity schemas (contracts/schemas/)
# ---------------------------------------------------------------------------


def test_participant_eligibility_policy_instance_validates() -> None:
    policy = ParticipantEligibilityPolicy(
        policy_id=uuid4(),
        policy_version=1,
        status=CriticalPolicyStatus.ACTIVE,
        scope_type="civic_space",
        scope_id=uuid4(),
        effective_from=_OCCURRED_AT,
        effective_until=None,
        adopted_by_decision_id=uuid4(),
        age_thresholds=(AgeThreshold(action_code="vote", minimum_age=18, maximum_age=None),),
        signed_policy_digest_reference="digest-1",
        transparency_log_commitment_reference="commitment-1",
    )
    instance = {
        "policy_id": str(policy.policy_id),
        "policy_version": policy.policy_version,
        "status": policy.status.value,
        "scope_type": policy.scope_type,
        "scope_id": str(policy.scope_id),
        "effective_from": _OCCURRED_AT.isoformat(),
        "effective_until": None,
        "adopted_by_decision_id": str(policy.adopted_by_decision_id),
        "age_thresholds": [
            {
                "action_code": t.action_code,
                "minimum_age": t.minimum_age,
                "maximum_age": t.maximum_age,
            }
            for t in policy.age_thresholds
        ],
        "citizenship_conditions": [],
        "residence_conditions": [],
        "exemptions": [],
        "transitional_rules": [],
        "supersedes_policy_id": None,
        "signed_policy_digest_reference": policy.signed_policy_digest_reference,
        "transparency_log_commitment_reference": policy.transparency_log_commitment_reference,
    }
    validate(instance, load_schema("participant-eligibility-policy.schema.json"))


def test_process_eligibility_policy_instance_validates() -> None:
    policy = ProcessEligibilityPolicy(
        policy_id=uuid4(),
        policy_version=1,
        status=CriticalPolicyStatus.ACTIVE,
        process_type="epd_member_vote",
        jurisdiction="DE",
        scope_type=None,
        scope_id=None,
        adopted_by=uuid4(),
        eligible_citizenship_set=("DE",),
        minimum_age=18,
        party_internal_voting_rule={"required_membership_status": "active"},
        signed_policy_digest_reference="digest-2",
        transparency_log_commitment_reference="commitment-2",
        decision_effect=DecisionEffect.INTERNALLY_BINDING,
        secret_ballot_required=True,
        permitted_participation_mode=("online",),
        required_assurance_level=AssuranceRequirement(
            required_identity_assurance_level="substantial",
            required_authentication_assurance_level="substantial",
        ),
    )
    instance = {
        "policy_id": str(policy.policy_id),
        "policy_version": policy.policy_version,
        "status": policy.status.value,
        "process_type": policy.process_type,
        "jurisdiction": policy.jurisdiction,
        "scope_type": None,
        "scope_id": None,
        "adopted_by": str(policy.adopted_by),
        "eligible_citizenship_set": list(policy.eligible_citizenship_set),
        "citizenship_rule_reference": None,
        "residence_rule": None,
        "habitual_residence_rule": None,
        "minimum_age": policy.minimum_age,
        "active_electoral_eligibility_rule": None,
        "passive_electoral_eligibility_rule": None,
        "party_internal_voting_rule": {"required_membership_status": "active"},
        "party_office_candidacy_rule": None,
        "effective_from": None,
        "effective_until": None,
        "legal_basis": None,
        "supersedes_policy_id": None,
        "signed_policy_digest_reference": policy.signed_policy_digest_reference,
        "transparency_log_commitment_reference": policy.transparency_log_commitment_reference,
        "decision_effect": policy.decision_effect.value,
        "formal_confirmation_required": policy.formal_confirmation_required,
        "formal_confirmation_authority": None,
        "secret_ballot_required": policy.secret_ballot_required,
        "permitted_participation_mode": list(policy.permitted_participation_mode),
        "required_assurance_level": {
            "required_identity_assurance_level": "substantial",
            "required_authentication_assurance_level": "substantial",
            "required_attribute_freshness": None,
        },
        "accessibility_profile": None,
    }
    validate(instance, load_schema("process-eligibility-policy.schema.json"))


def test_step_up_authentication_requirement_instance_validates() -> None:
    requirement = StepUpAuthenticationRequirement(
        requirement_id=uuid4(),
        requirement_version=1,
        status=CriticalPolicyStatus.ACTIVE,
        action_code="cast_vote",
        required_authentication_context="qualified_login",
        assurance_requirement=AssuranceRequirement(
            required_identity_assurance_level="high",
            required_authentication_assurance_level="high",
        ),
        fresh_authentication_required=True,
        reauthentication_reason="high-value action",
        signed_policy_digest_reference="digest-3",
        transparency_log_commitment_reference="commitment-3",
    )
    instance = {
        "requirement_id": str(requirement.requirement_id),
        "requirement_version": requirement.requirement_version,
        "status": requirement.status.value,
        "action_code": requirement.action_code,
        "required_authentication_context": requirement.required_authentication_context,
        "assurance_requirement": {
            "required_identity_assurance_level": "high",
            "required_authentication_assurance_level": "high",
            "required_attribute_freshness": None,
        },
        "fresh_authentication_required": requirement.fresh_authentication_required,
        "reauthentication_reason": requirement.reauthentication_reason,
        "maximum_authentication_age": None,
        "effective_from": None,
        "effective_until": None,
        "supersedes_requirement_id": None,
        "signed_policy_digest_reference": requirement.signed_policy_digest_reference,
        "transparency_log_commitment_reference": (
            requirement.transparency_log_commitment_reference
        ),
    }
    validate(instance, load_schema("step-up-authentication-requirement.schema.json"))


def test_digital_decision_instance_validates() -> None:
    decision = DigitalDecision(
        digital_decision_id=uuid4(),
        process_reference={"process_id": str(uuid4())},
        digital_result="approved",
        decision_effect=DecisionEffect.LEGALLY_FINAL,
        formal_confirmation_required=False,
        status=DigitalDecisionStatus.FINAL,
        recorded_at=_OCCURRED_AT,
    )
    validate(
        to_jsonable(digital_decision_state_payload(decision)),
        load_schema("digital-decision.schema.json"),
    )


def test_assembly_decision_instance_validates() -> None:
    decision = AssemblyDecision(
        assembly_decision_id=uuid4(),
        digital_decision_id=uuid4(),
        confirming_authority="regional_assembly",
        legal_basis="§ 21 PartG",
        confirmation_deadline=datetime(2026, 2, 1, tzinfo=UTC),
        protocol_or_evidence_reference="protocol-1",
        status=AssemblyDecisionStatus.PENDING,
    )
    validate(
        to_jsonable(assembly_decision_state_payload(decision)),
        load_schema("assembly-decision.schema.json"),
    )


def test_party_membership_eligibility_policy_instance_validates() -> None:
    policy = PartyMembershipEligibilityPolicy(
        policy_id=uuid4(),
        policy_version=1,
        status=MembershipCriticalPolicyStatus.ACTIVE,
        scope_type=None,
        scope_id=None,
        effective_from=None,
        effective_until=None,
        adopted_by_decision_id=uuid4(),
        incompatibility_rules=("dual_party_membership",),
        signed_policy_digest_reference="digest-4",
        transparency_log_commitment_reference="commitment-4",
    )
    instance = {
        "policy_id": str(policy.policy_id),
        "policy_version": policy.policy_version,
        "status": policy.status.value,
        "scope_type": None,
        "scope_id": None,
        "effective_from": None,
        "effective_until": None,
        "adopted_by_decision_id": str(policy.adopted_by_decision_id),
        "age_thresholds": [],
        "citizenship_conditions": [],
        "residence_conditions": [],
        "exemptions": [],
        "transitional_rules": [],
        "incompatibility_rules": list(policy.incompatibility_rules),
        "membership_duration_rules": None,
        "supersedes_policy_id": None,
        "signed_policy_digest_reference": policy.signed_policy_digest_reference,
        "transparency_log_commitment_reference": policy.transparency_log_commitment_reference,
    }
    validate(instance, load_schema("party-membership-eligibility-policy.schema.json"))


def test_membership_instance_validates() -> None:
    membership = Membership(
        membership_id=uuid4(),
        account_reference=uuid4(),
        organization_id=uuid4(),
        membership_type="ordinary",
        membership_status=MembershipStatus.ACTIVE,
        effective_from=_OCCURRED_AT,
        effective_until=None,
        region_code="DE-BE",
    )
    validate(
        to_jsonable(membership_state_payload(membership)), load_schema("membership.schema.json")
    )


def test_membership_application_instance_validates() -> None:
    application = MembershipApplication(
        membership_application_id=uuid4(),
        subject_reference=uuid4(),
        status=MembershipApplicationStatus.APPROVED,
        decision_authority_reference=uuid4(),
        applied_policy_version=1,
        reason_code="membership_application_approved_after_stage_b_review",
        decided_at=_OCCURRED_AT,
    )
    validate(
        to_jsonable(membership_application_state_payload(application)),
        load_schema("membership-application.schema.json"),
    )


def test_affiliation_declaration_instance_validates() -> None:
    declaration = AffiliationDeclaration(
        affiliation_declaration_id=uuid4(),
        subject_reference=uuid4(),
        affiliation_type=AffiliationType.OTHER_PARTY_MEMBERSHIP,
        declared_reference="org-ref-1",
        declared_at=_OCCURRED_AT,
        status=AffiliationStatus.DRAFT,
        valid_from=_OCCURRED_AT,
    )
    validate(
        to_jsonable(affiliation_declaration_state_payload(declaration)),
        load_schema("affiliation-declaration.schema.json"),
    )


def test_conflict_assessment_instance_validates() -> None:
    assessment = ConflictAssessment(
        conflict_assessment_id=uuid4(),
        subject_reference=uuid4(),
        conflict_type=ConflictType.DUAL_PARTY_MEMBERSHIP,
        incompatibility_level=IncompatibilityLevel.NONE,
        status=ConflictAssessmentStatus.PENDING,
        reviewed_by_role_reference=uuid4(),
    )
    validate(
        to_jsonable(conflict_assessment_state_payload(assessment)),
        load_schema("conflict-assessment.schema.json"),
    )


# ---------------------------------------------------------------------------
# Event payload schemas (contracts/events/)
# ---------------------------------------------------------------------------


def test_participation_rights_derived_event_payload_validates() -> None:
    claims = ProcessEligibilityClaims(
        active_electoral_eligibility_met=True,
        active_electoral_eligibility_reason_codes=(),
        passive_electoral_eligibility_met=False,
        passive_electoral_eligibility_reason_codes=("PASSIVE_ELECTORAL_ELIGIBILITY_NOT_MET",),
        party_internal_voting_eligibility_met=True,
        party_internal_voting_eligibility_reason_codes=(),
        party_office_candidacy_eligibility_met=False,
        party_office_candidacy_eligibility_reason_codes=(
            "PARTY_OFFICE_CANDIDACY_ELIGIBILITY_NOT_MET",
        ),
    )
    event = build_participation_rights_derived_event(
        event_id=uuid4(),
        subject_reference=uuid4(),
        process_id=uuid4(),
        action_code="cast_vote",
        claims=claims,
        actor=_actor(),
        correlation_id=uuid4(),
        causation_id=None,
        occurred_at=_OCCURRED_AT,
    )
    validate(
        to_jsonable(event.payload),
        load_event_schema("participation-rights-derived-payload.v1.schema.json"),
    )


def test_formal_confirmation_requested_event_payload_validates() -> None:
    assembly_decision = AssemblyDecision(
        assembly_decision_id=uuid4(),
        digital_decision_id=uuid4(),
        confirming_authority="regional_assembly",
        legal_basis="§ 21 PartG",
        confirmation_deadline=datetime(2026, 2, 1, tzinfo=UTC),
        protocol_or_evidence_reference="protocol-1",
        status=AssemblyDecisionStatus.PENDING,
    )
    event = build_formal_confirmation_requested_event(
        event_id=uuid4(),
        assembly_decision=assembly_decision,
        actor=_actor(),
        correlation_id=uuid4(),
        causation_id=None,
        occurred_at=_OCCURRED_AT,
    )
    validate(
        to_jsonable(event.payload),
        load_event_schema("formal-confirmation-requested-payload.v1.schema.json"),
    )


def test_formal_confirmation_recorded_event_payload_validates() -> None:
    assembly_decision = AssemblyDecision(
        assembly_decision_id=uuid4(),
        digital_decision_id=uuid4(),
        confirming_authority="regional_assembly",
        legal_basis="§ 21 PartG",
        confirmation_deadline=datetime(2026, 2, 1, tzinfo=UTC),
        protocol_or_evidence_reference="protocol-1",
        status=AssemblyDecisionStatus.CONFIRMED,
        final_legal_decision="confirmed as submitted",
        divergence_explanation=None,
        decided_at=datetime(2026, 1, 15, tzinfo=UTC),
    )
    event = build_formal_confirmation_recorded_event(
        event_id=uuid4(),
        assembly_decision=assembly_decision,
        actor=_actor(),
        correlation_id=uuid4(),
        causation_id=None,
        occurred_at=_OCCURRED_AT,
    )
    validate(
        to_jsonable(event.payload),
        load_event_schema("formal-confirmation-recorded-payload.v1.schema.json"),
    )


def test_authentication_context_event_payload_validates_for_both_event_types() -> None:
    context = AuthenticationContext(
        authentication_context_id=uuid4(),
        account_id=uuid4(),
        authentication_method="eid_card",
        authentication_assurance_level=AuthenticationAssuranceLevel.HIGH,
        session_authenticated_at=_OCCURRED_AT,
        provider_reference="provider-ref-1",
    )
    schema = load_event_schema("authentication-context-event-payload.v1.schema.json")
    for event_type in (
        "identity.authentication_context_established",
        "identity.step_up_authentication_completed",
    ):
        event = build_authentication_context_event(
            event_id=uuid4(),
            event_type=event_type,
            context=context,
            actor=_actor(),
            correlation_id=uuid4(),
            causation_id=None,
            occurred_at=_OCCURRED_AT,
        )
        validate(to_jsonable(event.payload), schema)


def test_membership_application_submitted_event_payload_validates() -> None:
    application = MembershipApplication(
        membership_application_id=uuid4(),
        subject_reference=uuid4(),
        status=MembershipApplicationStatus.APPLICATION_PENDING,
    )
    event = build_membership_application_submitted_event(
        event_id=uuid4(),
        application=application,
        actor=_actor(),
        correlation_id=uuid4(),
        causation_id=None,
        occurred_at=_OCCURRED_AT,
    )
    validate(
        to_jsonable(event.payload),
        load_event_schema("membership-application-submitted-payload.v1.schema.json"),
    )


def test_membership_eligibility_evaluated_event_payload_validates() -> None:
    application = MembershipApplication(
        membership_application_id=uuid4(),
        subject_reference=uuid4(),
        status=MembershipApplicationStatus.HUMAN_DECISION_PENDING,
    )
    event = build_membership_eligibility_evaluated_event(
        event_id=uuid4(),
        application=application,
        recommended_approval=True,
        actor=_actor(),
        correlation_id=uuid4(),
        causation_id=None,
        occurred_at=_OCCURRED_AT,
    )
    validate(
        to_jsonable(event.payload),
        load_event_schema("membership-eligibility-evaluated-payload.v1.schema.json"),
    )


def test_membership_decision_recorded_event_payload_validates() -> None:
    application = MembershipApplication(
        membership_application_id=uuid4(),
        subject_reference=uuid4(),
        status=MembershipApplicationStatus.APPROVED,
        decision_authority_reference=uuid4(),
        applied_policy_version=1,
        reason_code="membership_application_approved_after_stage_b_review",
        decided_at=_OCCURRED_AT,
    )
    event = build_membership_decision_recorded_event(
        event_id=uuid4(),
        application=application,
        actor=_actor(),
        correlation_id=uuid4(),
        causation_id=None,
        occurred_at=_OCCURRED_AT,
    )
    validate(
        to_jsonable(event.payload),
        load_event_schema("membership-decision-recorded-payload.v1.schema.json"),
    )


def test_membership_activated_event_payload_validates() -> None:
    membership = Membership(
        membership_id=uuid4(),
        account_reference=uuid4(),
        organization_id=uuid4(),
        membership_type="ordinary",
        membership_status=MembershipStatus.ACTIVE,
        effective_from=_OCCURRED_AT,
        effective_until=None,
        region_code=None,
    )
    event = build_membership_activated_event(
        event_id=uuid4(),
        membership=membership,
        actor=_actor(),
        correlation_id=uuid4(),
        causation_id=None,
        occurred_at=_OCCURRED_AT,
    )
    validate(
        to_jsonable(event.payload),
        load_event_schema("membership-activated-payload.v1.schema.json"),
    )


def test_membership_suspended_event_payload_validates() -> None:
    membership = Membership(
        membership_id=uuid4(),
        account_reference=uuid4(),
        organization_id=uuid4(),
        membership_type="ordinary",
        membership_status=MembershipStatus.SUSPENDED,
        effective_from=_OCCURRED_AT,
        effective_until=None,
        region_code=None,
    )
    event = build_membership_suspended_event(
        event_id=uuid4(),
        membership=membership,
        actor=_actor(),
        correlation_id=uuid4(),
        causation_id=None,
        occurred_at=_OCCURRED_AT,
    )
    validate(
        to_jsonable(event.payload),
        load_event_schema("membership-suspended-payload.v1.schema.json"),
    )


def test_affiliation_declared_event_payload_validates() -> None:
    declaration = AffiliationDeclaration(
        affiliation_declaration_id=uuid4(),
        subject_reference=uuid4(),
        affiliation_type=AffiliationType.PUBLIC_OFFICE,
        declared_reference="org-ref-2",
        declared_at=_OCCURRED_AT,
        status=AffiliationStatus.SUBMITTED,
        valid_from=_OCCURRED_AT,
    )
    event = build_affiliation_declared_event(
        event_id=uuid4(),
        declaration=declaration,
        actor=_actor(),
        correlation_id=uuid4(),
        causation_id=None,
        occurred_at=_OCCURRED_AT,
    )
    validate(
        to_jsonable(event.payload),
        load_event_schema("affiliation-declared-payload.v1.schema.json"),
    )


def test_conflict_assessment_opened_event_payload_validates() -> None:
    assessment = ConflictAssessment(
        conflict_assessment_id=uuid4(),
        subject_reference=uuid4(),
        conflict_type=ConflictType.DUAL_PARTY_MEMBERSHIP,
        incompatibility_level=IncompatibilityLevel.NONE,
        status=ConflictAssessmentStatus.PENDING,
        reviewed_by_role_reference=uuid4(),
    )
    event = build_conflict_assessment_opened_event(
        event_id=uuid4(),
        assessment=assessment,
        actor=_actor(),
        correlation_id=uuid4(),
        causation_id=None,
        occurred_at=_OCCURRED_AT,
    )
    validate(
        to_jsonable(event.payload),
        load_event_schema("conflict-assessment-opened-payload.v1.schema.json"),
    )


def test_conflict_decision_recorded_event_payload_validates() -> None:
    assessment = ConflictAssessment(
        conflict_assessment_id=uuid4(),
        subject_reference=uuid4(),
        conflict_type=ConflictType.DUAL_PARTY_MEMBERSHIP,
        incompatibility_level=IncompatibilityLevel.INCOMPATIBLE,
        status=ConflictAssessmentStatus.RESOLVED_INCOMPATIBLE,
        reviewed_by_role_reference=uuid4(),
        decision_authority_reference=uuid4(),
        decided_at=_OCCURRED_AT,
    )
    event = build_conflict_decision_recorded_event(
        event_id=uuid4(),
        assessment=assessment,
        actor=_actor(),
        correlation_id=uuid4(),
        causation_id=None,
        occurred_at=_OCCURRED_AT,
    )
    validate(
        to_jsonable(event.payload),
        load_event_schema("conflict-decision-recorded-payload.v1.schema.json"),
    )
