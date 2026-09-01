"""Tests for epd2_membership_service.application."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from epd2_audit_core.storage import InMemoryAuditEventStore
from epd2_core.clock import FixedClock
from epd2_core.event_envelope import ActorRef
from epd2_governance_service.domain import (
    GovernanceDecision,
    GovernanceDecisionStatus,
    GovernanceDecisionType,
)
from epd2_governance_service.storage import InMemoryGovernanceDecisionStore
from epd2_identity_service.domain import IdentityAssuranceLevel, IdentityRecord, VerificationStatus
from epd2_identity_service.storage import InMemoryIdentityRecordStore
from epd2_membership_service.application import (
    MembershipDecisionAuthorityInvalidError,
    PermissionDeniedError,
    activate_membership,
    activate_party_membership_eligibility_policy,
    decide_membership_appeal,
    declare_affiliation,
    evaluate_membership_application_eligibility,
    get_membership_derived_claims,
    open_conflict_assessment,
    record_conflict_decision,
    record_membership_human_decision,
    submit_membership_appeal,
    submit_membership_application,
    supersede_declaration,
    suspend_membership,
)
from epd2_membership_service.domain import (
    AffiliationStatus,
    ConflictAssessmentStatus,
    CriticalPolicyStatus,
    Membership,
    MembershipApplicationStatus,
    MembershipStatus,
    PartyMembershipEligibilityPolicy,
)
from epd2_membership_service.exceptions import (
    ConflictReviewSelfApprovalProhibitedError,
    MembershipHumanApprovalRequiredError,
    UnknownAppealError,
)
from epd2_membership_service.storage import (
    InMemoryAffiliationDeclarationStore,
    InMemoryAppealStore,
    InMemoryConflictAssessmentStore,
    InMemoryMembershipApplicationStore,
    InMemoryMembershipStore,
    InMemoryPartyMembershipEligibilityPolicyStore,
)

_CLOCK = FixedClock(datetime(2026, 1, 1, tzinfo=UTC))
_ACTOR = ActorRef(actor_id=uuid4(), actor_type="service")


def _make_identity_record(store: InMemoryIdentityRecordStore, *, verified: bool = True) -> UUID:
    identity_record_id = uuid4()
    record = IdentityRecord(
        identity_record_id=identity_record_id,
        account_id=uuid4(),
        verification_provider="provider",
        verification_level="substantial",
        verification_status=(
            VerificationStatus.VERIFIED if verified else VerificationStatus.PENDING
        ),
        verified_at=_CLOCK.now() if verified else None,
        expires_at=None,
        country="DE",
        duplicate_check_status="unique",
        provider_reference="ref",
        identity_assurance_level=(
            IdentityAssuranceLevel.SUBSTANTIAL if verified else IdentityAssuranceLevel.NONE
        ),
    )
    store.save(record)
    return identity_record_id


def _make_active_policy(
    store: InMemoryPartyMembershipEligibilityPolicyStore,
    *,
    incompatibility_rules: tuple[str, ...] = (),
) -> PartyMembershipEligibilityPolicy:
    policy = PartyMembershipEligibilityPolicy(
        policy_id=uuid4(),
        policy_version=1,
        status=CriticalPolicyStatus.ACTIVE,
        scope_type=None,
        scope_id=None,
        effective_from=datetime(2025, 1, 1, tzinfo=UTC),
        effective_until=None,
        adopted_by_decision_id=uuid4(),
        incompatibility_rules=incompatibility_rules,
        signed_policy_digest_reference="digest",
        transparency_log_commitment_reference="commitment",
    )
    store.save(policy)
    return policy


def _make_approved_governance_decision(
    store: InMemoryGovernanceDecisionStore,
) -> GovernanceDecision:
    proposed_by = uuid4()
    approved_by = uuid4()
    decision = GovernanceDecision(
        governance_decision_id=uuid4(),
        decision_type=GovernanceDecisionType.MANDATE,
        subject_reference={"kind": "membership_decision"},
        proposed_by_role_id=proposed_by,
        approved_by_role_id=None,
        rejected_by_role_id=None,
        reason_code="MANDATE_ISSUED",
        evidence_references=(),
        finality_outcome=None,
        created_at=_CLOCK.now(),
        decided_at=None,
        supersedes_decision_id=None,
        status=GovernanceDecisionStatus.PROPOSED,
    )
    store.create(decision)
    approved = decision.with_approved(
        approved_by_role_id=approved_by, decided_at=_CLOCK.now(), finality_outcome=None
    )
    store.save(approved)
    return approved


def _submit_and_evaluate(
    *,
    application_store: InMemoryMembershipApplicationStore,
    policy_store: InMemoryPartyMembershipEligibilityPolicyStore,
    identity_store: InMemoryIdentityRecordStore,
    audit_store: InMemoryAuditEventStore,
    incompatibility_rules: tuple[str, ...] = (),
    identity_verified: bool = True,
) -> UUID:
    membership_application_id = uuid4()
    submit_membership_application(
        application_store,
        audit_store,
        membership_application_id=membership_application_id,
        subject_reference=uuid4(),
        supersedes_membership_application_id=None,
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    _make_active_policy(policy_store, incompatibility_rules=incompatibility_rules)
    identity_record_id = _make_identity_record(identity_store, verified=identity_verified)
    evaluate_membership_application_eligibility(
        application_store,
        policy_store,
        identity_store,
        audit_store,
        membership_application_id=membership_application_id,
        identity_record_id=identity_record_id,
        scope_type=None,
        scope_id=None,
        effective_date=_CLOCK.now(),
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    return membership_application_id


# =============================================================================
# submit_membership_application
# =============================================================================


def test_submit_membership_application_enters_eligibility_review() -> None:
    application_store = InMemoryMembershipApplicationStore()
    audit_store = InMemoryAuditEventStore()
    result = submit_membership_application(
        application_store,
        audit_store,
        membership_application_id=uuid4(),
        subject_reference=uuid4(),
        supersedes_membership_application_id=None,
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.application.status is MembershipApplicationStatus.ELIGIBILITY_REVIEW
    assert result.event.event_type == "membership.membership_application_submitted"


def test_submit_membership_application_without_permission_is_denied() -> None:
    application_store = InMemoryMembershipApplicationStore()
    audit_store = InMemoryAuditEventStore()
    with pytest.raises(PermissionDeniedError):
        submit_membership_application(
            application_store,
            audit_store,
            membership_application_id=uuid4(),
            subject_reference=uuid4(),
            supersedes_membership_application_id=None,
            actor=_ACTOR,
            actor_is_authorized=False,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


# =============================================================================
# evaluate_membership_application_eligibility (Stage A)
# =============================================================================


def test_stage_a_always_transitions_to_human_decision_pending_regardless_of_recommendation() -> (
    None
):
    """Canon 19d.16's hard human-control invariant: Stage A never
    auto-approves or auto-rejects, even when recommended_approval=False."""
    application_store = InMemoryMembershipApplicationStore()
    policy_store = InMemoryPartyMembershipEligibilityPolicyStore()
    identity_store = InMemoryIdentityRecordStore()
    audit_store = InMemoryAuditEventStore()
    membership_application_id = _submit_and_evaluate(
        application_store=application_store,
        policy_store=policy_store,
        identity_store=identity_store,
        audit_store=audit_store,
        identity_verified=False,
    )
    application = application_store.get(membership_application_id)
    assert application is not None
    assert application.status is MembershipApplicationStatus.HUMAN_DECISION_PENDING


def test_stage_a_recommends_approval_when_identity_verified_and_no_incompatibility() -> None:
    application_store = InMemoryMembershipApplicationStore()
    policy_store = InMemoryPartyMembershipEligibilityPolicyStore()
    identity_store = InMemoryIdentityRecordStore()
    audit_store = InMemoryAuditEventStore()
    membership_application_id = uuid4()
    submit_membership_application(
        application_store,
        audit_store,
        membership_application_id=membership_application_id,
        subject_reference=uuid4(),
        supersedes_membership_application_id=None,
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    _make_active_policy(policy_store)
    identity_record_id = _make_identity_record(identity_store, verified=True)
    result = evaluate_membership_application_eligibility(
        application_store,
        policy_store,
        identity_store,
        audit_store,
        membership_application_id=membership_application_id,
        identity_record_id=identity_record_id,
        scope_type=None,
        scope_id=None,
        effective_date=_CLOCK.now(),
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.result.recommended_approval is True
    assert result.event.event_type == "membership.membership_eligibility_evaluated"


def test_stage_a_flags_but_never_auto_rejects_when_incompatibility_rules_present() -> None:
    application_store = InMemoryMembershipApplicationStore()
    policy_store = InMemoryPartyMembershipEligibilityPolicyStore()
    identity_store = InMemoryIdentityRecordStore()
    audit_store = InMemoryAuditEventStore()
    membership_application_id = _submit_and_evaluate(
        application_store=application_store,
        policy_store=policy_store,
        identity_store=identity_store,
        audit_store=audit_store,
        incompatibility_rules=("some_incompatibility",),
        identity_verified=True,
    )
    application = application_store.get(membership_application_id)
    assert application is not None
    assert application.status is MembershipApplicationStatus.HUMAN_DECISION_PENDING


# =============================================================================
# record_membership_human_decision (Stage B) / activate_membership
# =============================================================================


def test_record_human_decision_approved_does_not_itself_activate_membership() -> None:
    """ADR-030 item 2: an approved outcome does NOT itself create an
    active Membership row - only activate_membership does."""
    application_store = InMemoryMembershipApplicationStore()
    policy_store = InMemoryPartyMembershipEligibilityPolicyStore()
    identity_store = InMemoryIdentityRecordStore()
    membership_store = InMemoryMembershipStore()
    governance_store = InMemoryGovernanceDecisionStore()
    audit_store = InMemoryAuditEventStore()
    membership_application_id = _submit_and_evaluate(
        application_store=application_store,
        policy_store=policy_store,
        identity_store=identity_store,
        audit_store=audit_store,
    )
    decision = _make_approved_governance_decision(governance_store)
    result = record_membership_human_decision(
        application_store,
        membership_store,
        governance_store,
        audit_store,
        membership_application_id=membership_application_id,
        outcome="approved",
        decision_authority_reference=decision.governance_decision_id,
        applied_policy_version=1,
        reason_code="OK",
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.application.status is MembershipApplicationStatus.APPROVED
    assert result.membership is None


def test_record_human_decision_rejected_creates_rejected_membership_row() -> None:
    application_store = InMemoryMembershipApplicationStore()
    policy_store = InMemoryPartyMembershipEligibilityPolicyStore()
    identity_store = InMemoryIdentityRecordStore()
    membership_store = InMemoryMembershipStore()
    governance_store = InMemoryGovernanceDecisionStore()
    audit_store = InMemoryAuditEventStore()
    membership_application_id = _submit_and_evaluate(
        application_store=application_store,
        policy_store=policy_store,
        identity_store=identity_store,
        audit_store=audit_store,
    )
    decision = _make_approved_governance_decision(governance_store)
    result = record_membership_human_decision(
        application_store,
        membership_store,
        governance_store,
        audit_store,
        membership_application_id=membership_application_id,
        outcome="rejected",
        decision_authority_reference=decision.governance_decision_id,
        applied_policy_version=1,
        reason_code="PARTY_MEMBERSHIP_ELIGIBILITY_NOT_MET",
        membership_id=uuid4(),
        account_reference=uuid4(),
        organization_id=uuid4(),
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.application.status is MembershipApplicationStatus.REJECTED
    assert result.membership is not None
    assert result.membership.membership_status is MembershipStatus.REJECTED


def test_record_human_decision_rejects_invalid_outcome() -> None:
    application_store = InMemoryMembershipApplicationStore()
    policy_store = InMemoryPartyMembershipEligibilityPolicyStore()
    identity_store = InMemoryIdentityRecordStore()
    membership_store = InMemoryMembershipStore()
    governance_store = InMemoryGovernanceDecisionStore()
    audit_store = InMemoryAuditEventStore()
    membership_application_id = _submit_and_evaluate(
        application_store=application_store,
        policy_store=policy_store,
        identity_store=identity_store,
        audit_store=audit_store,
    )
    with pytest.raises(ValueError, match="outcome"):
        record_membership_human_decision(
            application_store,
            membership_store,
            governance_store,
            audit_store,
            membership_application_id=membership_application_id,
            outcome="maybe",
            decision_authority_reference=uuid4(),
            applied_policy_version=1,
            reason_code="OK",
            actor=_ACTOR,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


def test_record_human_decision_requires_valid_decision_authority() -> None:
    """The governance_decision_id must resolve to a real, approved
    GovernanceDecision - an unknown id fails closed."""
    application_store = InMemoryMembershipApplicationStore()
    policy_store = InMemoryPartyMembershipEligibilityPolicyStore()
    identity_store = InMemoryIdentityRecordStore()
    membership_store = InMemoryMembershipStore()
    governance_store = InMemoryGovernanceDecisionStore()
    audit_store = InMemoryAuditEventStore()
    membership_application_id = _submit_and_evaluate(
        application_store=application_store,
        policy_store=policy_store,
        identity_store=identity_store,
        audit_store=audit_store,
    )
    with pytest.raises(MembershipDecisionAuthorityInvalidError):
        record_membership_human_decision(
            application_store,
            membership_store,
            governance_store,
            audit_store,
            membership_application_id=membership_application_id,
            outcome="approved",
            decision_authority_reference=uuid4(),
            applied_policy_version=1,
            reason_code="OK",
            actor=_ACTOR,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


def test_record_human_decision_requires_application_awaiting_human_decision() -> None:
    application_store = InMemoryMembershipApplicationStore()
    membership_store = InMemoryMembershipStore()
    governance_store = InMemoryGovernanceDecisionStore()
    audit_store = InMemoryAuditEventStore()
    membership_application_id = uuid4()
    submit_membership_application(
        application_store,
        audit_store,
        membership_application_id=membership_application_id,
        subject_reference=uuid4(),
        supersedes_membership_application_id=None,
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    decision = _make_approved_governance_decision(governance_store)
    with pytest.raises(MembershipHumanApprovalRequiredError):
        record_membership_human_decision(
            application_store,
            membership_store,
            governance_store,
            audit_store,
            membership_application_id=membership_application_id,
            outcome="approved",
            decision_authority_reference=decision.governance_decision_id,
            applied_policy_version=1,
            reason_code="OK",
            actor=_ACTOR,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


def test_activate_membership_is_the_only_path_to_active_status() -> None:
    application_store = InMemoryMembershipApplicationStore()
    policy_store = InMemoryPartyMembershipEligibilityPolicyStore()
    identity_store = InMemoryIdentityRecordStore()
    membership_store = InMemoryMembershipStore()
    governance_store = InMemoryGovernanceDecisionStore()
    audit_store = InMemoryAuditEventStore()
    membership_application_id = _submit_and_evaluate(
        application_store=application_store,
        policy_store=policy_store,
        identity_store=identity_store,
        audit_store=audit_store,
    )
    decision = _make_approved_governance_decision(governance_store)
    record_membership_human_decision(
        application_store,
        membership_store,
        governance_store,
        audit_store,
        membership_application_id=membership_application_id,
        outcome="approved",
        decision_authority_reference=decision.governance_decision_id,
        applied_policy_version=1,
        reason_code="OK",
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    result = activate_membership(
        application_store,
        membership_store,
        audit_store,
        membership_application_id=membership_application_id,
        membership_id=uuid4(),
        account_reference=uuid4(),
        organization_id=uuid4(),
        membership_type="party",
        region_code=None,
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.application.status is MembershipApplicationStatus.ACTIVATED
    assert result.membership.membership_status is MembershipStatus.ACTIVE
    assert result.event.event_type == "membership.membership_activated"


def test_activate_membership_requires_approved_application() -> None:
    application_store = InMemoryMembershipApplicationStore()
    membership_store = InMemoryMembershipStore()
    audit_store = InMemoryAuditEventStore()
    membership_application_id = uuid4()
    submit_membership_application(
        application_store,
        audit_store,
        membership_application_id=membership_application_id,
        subject_reference=uuid4(),
        supersedes_membership_application_id=None,
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    with pytest.raises(MembershipHumanApprovalRequiredError):
        activate_membership(
            application_store,
            membership_store,
            audit_store,
            membership_application_id=membership_application_id,
            membership_id=uuid4(),
            account_reference=uuid4(),
            organization_id=uuid4(),
            membership_type="party",
            region_code=None,
            actor=_ACTOR,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


def test_suspend_membership_requires_valid_decision_authority() -> None:
    membership_store = InMemoryMembershipStore()
    governance_store = InMemoryGovernanceDecisionStore()
    audit_store = InMemoryAuditEventStore()
    membership = Membership(
        membership_id=uuid4(),
        account_reference=uuid4(),
        organization_id=uuid4(),
        membership_type="party",
        membership_status=MembershipStatus.ACTIVE,
        effective_from=_CLOCK.now(),
        effective_until=None,
        region_code=None,
    )
    membership_store.save(membership)
    with pytest.raises(MembershipDecisionAuthorityInvalidError):
        suspend_membership(
            membership_store,
            governance_store,
            audit_store,
            membership_id=membership.membership_id,
            decision_authority_reference=uuid4(),
            reason_code="CONFLICT_DETECTED",
            actor=_ACTOR,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


def test_suspend_membership_succeeds_with_valid_decision_authority() -> None:
    membership_store = InMemoryMembershipStore()
    governance_store = InMemoryGovernanceDecisionStore()
    audit_store = InMemoryAuditEventStore()
    membership = Membership(
        membership_id=uuid4(),
        account_reference=uuid4(),
        organization_id=uuid4(),
        membership_type="party",
        membership_status=MembershipStatus.ACTIVE,
        effective_from=_CLOCK.now(),
        effective_until=None,
        region_code=None,
    )
    membership_store.save(membership)
    decision = _make_approved_governance_decision(governance_store)
    result = suspend_membership(
        membership_store,
        governance_store,
        audit_store,
        membership_id=membership.membership_id,
        decision_authority_reference=decision.governance_decision_id,
        reason_code="CONFLICT_DETECTED",
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.membership.membership_status is MembershipStatus.SUSPENDED
    assert result.event.event_type == "membership.membership_suspended"


# =============================================================================
# get_membership_derived_claims (ADR-027 narrow read)
# =============================================================================


def test_get_membership_derived_claims_false_when_no_membership_exists() -> None:
    membership_store = InMemoryMembershipStore()
    claims = get_membership_derived_claims(
        membership_store,
        account_reference=uuid4(),
        organization_id=uuid4(),
        evaluated_at=_CLOCK.now(),
    )
    assert claims.required_membership_status_met is False
    assert claims.reason_code == "MEMBERSHIP_HUMAN_APPROVAL_REQUIRED"


def test_get_membership_derived_claims_true_when_active_and_duration_met() -> None:
    membership_store = InMemoryMembershipStore()
    account_reference = uuid4()
    organization_id = uuid4()
    membership = Membership(
        membership_id=uuid4(),
        account_reference=account_reference,
        organization_id=organization_id,
        membership_type="party",
        membership_status=MembershipStatus.ACTIVE,
        effective_from=datetime(2020, 1, 1, tzinfo=UTC),
        effective_until=None,
        region_code=None,
    )
    membership_store.save(membership)
    claims = get_membership_derived_claims(
        membership_store,
        account_reference=account_reference,
        organization_id=organization_id,
        minimum_duration_days=30,
        evaluated_at=_CLOCK.now(),
    )
    assert claims.required_membership_status_met is True
    assert claims.membership_duration_requirement_met is True
    assert claims.reason_code is None


# =============================================================================
# AffiliationDeclaration
# =============================================================================


def test_declare_affiliation_and_supersede_declaration() -> None:
    store = InMemoryAffiliationDeclarationStore()
    audit_store = InMemoryAuditEventStore()
    result = declare_affiliation(
        store,
        audit_store,
        affiliation_declaration_id=uuid4(),
        subject_reference=uuid4(),
        affiliation_type="other_party_membership",
        declared_reference="ref-1",
        valid_from=_CLOCK.now(),
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.event.event_type == "membership.affiliation_declared"
    # supersede_declaration relies on the domain's own transition table
    # (canon 19d.10: only an acknowledged declaration may be superseded) -
    # walk it there first, exactly as a real review workflow would.
    under_review = result.declaration.with_status(AffiliationStatus.UNDER_REVIEW)
    acknowledged = under_review.with_status(AffiliationStatus.ACKNOWLEDGED)
    store.save(acknowledged)
    superseded = supersede_declaration(
        store, affiliation_declaration_id=result.declaration.affiliation_declaration_id
    )
    assert superseded.status is AffiliationStatus.SUPERSEDED


def test_declare_affiliation_without_permission_is_denied() -> None:
    store = InMemoryAffiliationDeclarationStore()
    audit_store = InMemoryAuditEventStore()
    with pytest.raises(PermissionDeniedError):
        declare_affiliation(
            store,
            audit_store,
            affiliation_declaration_id=uuid4(),
            subject_reference=uuid4(),
            affiliation_type="other_party_membership",
            declared_reference="ref-1",
            valid_from=_CLOCK.now(),
            actor=_ACTOR,
            actor_is_authorized=False,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


# =============================================================================
# ConflictAssessment
# =============================================================================


def test_open_conflict_assessment_prohibits_reviewer_self_approval() -> None:
    store = InMemoryConflictAssessmentStore()
    audit_store = InMemoryAuditEventStore()
    subject_reference = uuid4()
    with pytest.raises(ConflictReviewSelfApprovalProhibitedError):
        open_conflict_assessment(
            store,
            audit_store,
            conflict_assessment_id=uuid4(),
            subject_reference=subject_reference,
            conflict_type="dual_party_membership",
            reviewed_by_role_reference=subject_reference,
            actor=_ACTOR,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


def test_record_conflict_decision_requires_decision_authority_when_incompatible() -> None:
    store = InMemoryConflictAssessmentStore()
    governance_store = InMemoryGovernanceDecisionStore()
    audit_store = InMemoryAuditEventStore()
    opened = open_conflict_assessment(
        store,
        audit_store,
        conflict_assessment_id=uuid4(),
        subject_reference=uuid4(),
        conflict_type="dual_party_membership",
        reviewed_by_role_reference=uuid4(),
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    ).assessment
    under_review = opened.with_decision(
        new_status=ConflictAssessmentStatus.UNDER_REVIEW,
        incompatibility_level=opened.incompatibility_level,
        reason_codes=(),
        decision_authority_reference=None,
        decided_at=_CLOCK.now(),
    )
    store.save(under_review)
    with pytest.raises(MembershipHumanApprovalRequiredError):
        record_conflict_decision(
            store,
            governance_store,
            audit_store,
            conflict_assessment_id=under_review.conflict_assessment_id,
            new_status="resolved_incompatible",
            incompatibility_level="incompatible",
            reason_codes=("REASON",),
            decision_authority_reference=None,
            actor=_ACTOR,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


def test_record_conflict_decision_succeeds_with_valid_decision_authority() -> None:
    store = InMemoryConflictAssessmentStore()
    governance_store = InMemoryGovernanceDecisionStore()
    audit_store = InMemoryAuditEventStore()
    opened = open_conflict_assessment(
        store,
        audit_store,
        conflict_assessment_id=uuid4(),
        subject_reference=uuid4(),
        conflict_type="dual_party_membership",
        reviewed_by_role_reference=uuid4(),
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    ).assessment
    under_review = opened.with_decision(
        new_status=ConflictAssessmentStatus.UNDER_REVIEW,
        incompatibility_level=opened.incompatibility_level,
        reason_codes=(),
        decision_authority_reference=None,
        decided_at=_CLOCK.now(),
    )
    store.save(under_review)
    decision = _make_approved_governance_decision(governance_store)
    result = record_conflict_decision(
        store,
        governance_store,
        audit_store,
        conflict_assessment_id=under_review.conflict_assessment_id,
        new_status="resolved_incompatible",
        incompatibility_level="incompatible",
        reason_codes=("REASON",),
        decision_authority_reference=decision.governance_decision_id,
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.event.event_type == "membership.conflict_decision_recorded"


# =============================================================================
# activate_party_membership_eligibility_policy (critical-policy 4-gate)
# =============================================================================


def test_activate_party_membership_eligibility_policy_requires_all_four_gates() -> None:
    policy_store = InMemoryPartyMembershipEligibilityPolicyStore()
    governance_store = InMemoryGovernanceDecisionStore()
    policy = PartyMembershipEligibilityPolicy(
        policy_id=uuid4(),
        policy_version=1,
        status=CriticalPolicyStatus.DRAFT,
        scope_type=None,
        scope_id=None,
        effective_from=_CLOCK.now(),
        effective_until=None,
        adopted_by_decision_id=uuid4(),
    )
    policy_store.save(policy)
    with pytest.raises(Exception):  # noqa: B017 - unauthorized/unresolvable decision
        activate_party_membership_eligibility_policy(
            policy_store,
            governance_store,
            policy_id=policy.policy_id,
            actor_is_authorized=True,
        )


def test_activate_party_membership_eligibility_policy_succeeds_when_all_gates_met() -> None:
    policy_store = InMemoryPartyMembershipEligibilityPolicyStore()
    governance_store = InMemoryGovernanceDecisionStore()
    decision = _make_approved_governance_decision(governance_store)
    policy = PartyMembershipEligibilityPolicy(
        policy_id=uuid4(),
        policy_version=1,
        status=CriticalPolicyStatus.DRAFT,
        scope_type=None,
        scope_id=None,
        effective_from=_CLOCK.now(),
        effective_until=None,
        adopted_by_decision_id=decision.governance_decision_id,
        signed_policy_digest_reference="digest",
        transparency_log_commitment_reference="commitment",
    )
    policy_store.save(policy)
    activated = activate_party_membership_eligibility_policy(
        policy_store,
        governance_store,
        policy_id=policy.policy_id,
        actor_is_authorized=True,
    )
    assert activated.status is CriticalPolicyStatus.ACTIVE


# =============================================================================
# Appeal (submit / decide) - ADR-030 item 4
# =============================================================================


def test_submit_and_decide_membership_appeal_enforces_reviewer_separation() -> None:
    store = InMemoryAppealStore()
    audit_store = InMemoryAuditEventStore()
    original_decision_author = uuid4()
    appeal = submit_membership_appeal(
        store,
        audit_store,
        appeal_id=uuid4(),
        decision_id=uuid4(),
        submitted_by=uuid4(),
        grounds="grounds",
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    with pytest.raises(PermissionDeniedError):
        decide_membership_appeal(
            store,
            appeal_id=appeal.appeal_id,
            reviewer_actor_id=original_decision_author,
            original_decision_author_reference=original_decision_author,
            outcome="upheld",
            result="upheld: incompatibility not established",
            actor_is_authorized=True,
        )


def test_decide_membership_appeal_succeeds_with_independent_reviewer() -> None:
    store = InMemoryAppealStore()
    audit_store = InMemoryAuditEventStore()
    original_decision_author = uuid4()
    appeal = submit_membership_appeal(
        store,
        audit_store,
        appeal_id=uuid4(),
        decision_id=uuid4(),
        submitted_by=uuid4(),
        grounds="grounds",
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    decided = decide_membership_appeal(
        store,
        appeal_id=appeal.appeal_id,
        reviewer_actor_id=uuid4(),
        original_decision_author_reference=original_decision_author,
        outcome="upheld",
        result="upheld: incompatibility not established",
        actor_is_authorized=True,
    )
    assert decided.status.value == "upheld"
    assert store.get(appeal.appeal_id) == decided


def test_decide_membership_appeal_unknown_appeal_raises() -> None:
    store = InMemoryAppealStore()
    with pytest.raises(UnknownAppealError):
        decide_membership_appeal(
            store,
            appeal_id=uuid4(),
            reviewer_actor_id=uuid4(),
            original_decision_author_reference=uuid4(),
            outcome="upheld",
            result="upheld",
            actor_is_authorized=True,
        )
