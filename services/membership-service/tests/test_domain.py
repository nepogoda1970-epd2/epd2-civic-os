"""Tests for epd2_membership_service.domain."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from epd2_membership_service.domain import (
    AffiliationDeclaration,
    AffiliationStatus,
    AffiliationType,
    AffiliationVerificationStatus,
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
    MembershipStatus,
    PartyMembershipEligibilityPolicy,
    assert_appeal_transition_allowed,
    assert_critical_policy_activation_gate,
    assert_membership_transition_allowed,
    parse_affiliation_status,
    parse_affiliation_type,
    parse_conflict_assessment_status,
    parse_conflict_type,
    parse_critical_policy_status,
    parse_incompatibility_level,
    parse_membership_application_status,
    parse_membership_status,
)
from epd2_membership_service.exceptions import (
    ConflictDecisionAuthorityRequiredError,
    CriticalPolicyActivationNotAuthorizedError,
    ForbiddenAppealTransitionError,
    ForbiddenMembershipApplicationTransitionError,
    ForbiddenMembershipTransitionError,
    UnknownAffiliationStatusError,
    UnknownAffiliationTypeError,
    UnknownConflictAssessmentStatusError,
    UnknownConflictTypeError,
    UnknownCriticalPolicyStatusError,
    UnknownIncompatibilityLevelError,
    UnknownMembershipApplicationStatusError,
    UnknownMembershipStatusError,
)

_NOW = datetime(2026, 1, 1, tzinfo=UTC)


# =============================================================================
# CriticalPolicyActivationGate (canon 19d.7, duplicated copy)
# =============================================================================


def test_critical_policy_activation_gate_requires_all_four_conditions() -> None:
    valid = CriticalPolicyActivationGate(
        decision_authorized=True,
        multi_person_approval_met=True,
        signed_policy_digest_reference="digest",
        transparency_log_commitment_reference="commitment",
    )
    assert_critical_policy_activation_gate(valid)  # does not raise


@pytest.mark.parametrize(
    "overrides",
    [
        {"decision_authorized": False},
        {"multi_person_approval_met": False},
        {"signed_policy_digest_reference": None},
        {"transparency_log_commitment_reference": None},
    ],
)
def test_critical_policy_activation_gate_fails_closed(overrides: dict[str, object]) -> None:
    base = {
        "decision_authorized": True,
        "multi_person_approval_met": True,
        "signed_policy_digest_reference": "digest",
        "transparency_log_commitment_reference": "commitment",
    }
    base.update(overrides)
    gate = CriticalPolicyActivationGate(**base)  # type: ignore[arg-type]
    with pytest.raises(CriticalPolicyActivationNotAuthorizedError):
        assert_critical_policy_activation_gate(gate)


def test_parse_critical_policy_status_rejects_unknown() -> None:
    with pytest.raises(UnknownCriticalPolicyStatusError):
        parse_critical_policy_status("bogus")


# =============================================================================
# PartyMembershipEligibilityPolicy (canon 19d.6)
# =============================================================================


def test_party_membership_eligibility_policy_active_requires_digest_and_commitment() -> None:
    with pytest.raises(ValueError, match="signed_policy_digest_reference"):
        PartyMembershipEligibilityPolicy(
            policy_id=uuid4(),
            policy_version=1,
            status=CriticalPolicyStatus.ACTIVE,
            scope_type=None,
            scope_id=None,
            effective_from=_NOW,
            effective_until=None,
            adopted_by_decision_id=uuid4(),
        )


def test_party_membership_eligibility_policy_with_status_reenforces_active_invariant() -> None:
    """DRAFT -> ACTIVE is allowed by the transition table, but
    `dataclasses.replace` re-runs `__post_init__` - so activating a
    policy still missing its digest/commitment fields must fail closed,
    not silently succeed."""
    policy = PartyMembershipEligibilityPolicy(
        policy_id=uuid4(),
        policy_version=1,
        status=CriticalPolicyStatus.DRAFT,
        scope_type=None,
        scope_id=None,
        effective_from=_NOW,
        effective_until=None,
        adopted_by_decision_id=uuid4(),
    )
    with pytest.raises(ValueError, match="signed_policy_digest_reference"):
        policy.with_status(CriticalPolicyStatus.ACTIVE)


def test_party_membership_eligibility_policy_forbidden_transition() -> None:
    policy = PartyMembershipEligibilityPolicy(
        policy_id=uuid4(),
        policy_version=1,
        status=CriticalPolicyStatus.SUPERSEDED,
        scope_type=None,
        scope_id=None,
        effective_from=_NOW,
        effective_until=None,
        adopted_by_decision_id=uuid4(),
    )
    with pytest.raises(Exception):  # noqa: B017 - ForbiddenCriticalPolicyTransitionError
        policy.with_status(CriticalPolicyStatus.ACTIVE)


# =============================================================================
# Membership (canon 8.3)
# =============================================================================


def test_membership_status_active_exclusivity_transition_table() -> None:
    assert_membership_transition_allowed(
        MembershipStatus.APPLICATION_PENDING, MembershipStatus.ACTIVE
    )
    with pytest.raises(ForbiddenMembershipTransitionError):
        assert_membership_transition_allowed(MembershipStatus.REJECTED, MembershipStatus.ACTIVE)


def test_membership_rejects_naive_datetimes() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        Membership(
            membership_id=uuid4(),
            account_reference=uuid4(),
            organization_id=uuid4(),
            membership_type="party",
            membership_status=MembershipStatus.ACTIVE,
            effective_from=datetime(2026, 1, 1),  # deliberately naive (no tzinfo)
            effective_until=None,
            region_code=None,
        )


def test_parse_membership_status_rejects_unknown() -> None:
    with pytest.raises(UnknownMembershipStatusError):
        parse_membership_status("bogus")


# =============================================================================
# MembershipApplication (canon 19d.9)
# =============================================================================


def test_membership_application_requires_decision_fields_once_approved_or_rejected() -> None:
    with pytest.raises(ValueError, match="decision_authority_reference"):
        MembershipApplication(
            membership_application_id=uuid4(),
            subject_reference=uuid4(),
            status=MembershipApplicationStatus.APPROVED,
        )


def test_membership_application_lifecycle_never_skips_human_decision_pending() -> None:
    """Canon 19d.16: passing eligibility never auto-activates membership -
    structurally, there is no direct eligibility_review -> approved edge."""
    application = MembershipApplication(
        membership_application_id=uuid4(),
        subject_reference=uuid4(),
        status=MembershipApplicationStatus.ELIGIBILITY_REVIEW,
    )
    with pytest.raises(ForbiddenMembershipApplicationTransitionError):
        application.with_status(
            MembershipApplicationStatus.APPROVED,
            decision_authority_reference=uuid4(),
            applied_policy_version=1,
            reason_code="MEMBERSHIP_HUMAN_APPROVAL_REQUIRED",
            decided_at=_NOW,
        )


def test_membership_application_full_lifecycle_via_with_status() -> None:
    application = MembershipApplication(
        membership_application_id=uuid4(),
        subject_reference=uuid4(),
        status=MembershipApplicationStatus.APPLICATION_PENDING,
    )
    review = application.with_status(MembershipApplicationStatus.ELIGIBILITY_REVIEW)
    pending = review.with_status(MembershipApplicationStatus.HUMAN_DECISION_PENDING)
    approved = pending.with_status(
        MembershipApplicationStatus.APPROVED,
        decision_authority_reference=uuid4(),
        applied_policy_version=1,
        reason_code="OK",
        decided_at=_NOW,
    )
    activated = approved.with_status(MembershipApplicationStatus.ACTIVATED)
    assert activated.status is MembershipApplicationStatus.ACTIVATED


def test_parse_membership_application_status_rejects_unknown() -> None:
    with pytest.raises(UnknownMembershipApplicationStatusError):
        parse_membership_application_status("bogus")


# =============================================================================
# AffiliationDeclaration (canon 19d.10)
# =============================================================================


def test_affiliation_declaration_rejects_empty_declared_reference() -> None:
    with pytest.raises(ValueError, match="declared_reference"):
        AffiliationDeclaration(
            affiliation_declaration_id=uuid4(),
            subject_reference=uuid4(),
            affiliation_type=AffiliationType.OTHER_PARTY_MEMBERSHIP,
            declared_reference="",
            declared_at=_NOW,
            status=AffiliationStatus.SUBMITTED,
            valid_from=_NOW,
        )


def test_affiliation_declaration_with_status_and_with_verification() -> None:
    declaration = AffiliationDeclaration(
        affiliation_declaration_id=uuid4(),
        subject_reference=uuid4(),
        affiliation_type=AffiliationType.PUBLIC_OFFICE,
        declared_reference="ref-1",
        declared_at=_NOW,
        status=AffiliationStatus.SUBMITTED,
        valid_from=_NOW,
    )
    under_review = declaration.with_status(AffiliationStatus.UNDER_REVIEW)
    verified = under_review.with_verification(
        verification_status=AffiliationVerificationStatus.VERIFIED,
        verified_at=_NOW,
        verified_by=uuid4(),
    )
    assert verified.verification_status is AffiliationVerificationStatus.VERIFIED


def test_parse_affiliation_type_and_status_reject_unknown() -> None:
    with pytest.raises(UnknownAffiliationTypeError):
        parse_affiliation_type("bogus")
    with pytest.raises(UnknownAffiliationStatusError):
        parse_affiliation_status("bogus")


# =============================================================================
# ConflictAssessment (canon 19d.11)
# =============================================================================


def test_conflict_assessment_requires_decision_authority_when_resolved_incompatible() -> None:
    with pytest.raises(ConflictDecisionAuthorityRequiredError):
        ConflictAssessment(
            conflict_assessment_id=uuid4(),
            subject_reference=uuid4(),
            conflict_type=ConflictType.DUAL_PARTY_MEMBERSHIP,
            incompatibility_level=IncompatibilityLevel.INCOMPATIBLE,
            status=ConflictAssessmentStatus.RESOLVED_INCOMPATIBLE,
            reviewed_by_role_reference=uuid4(),
            decision_authority_reference=None,
        )


def test_conflict_assessment_with_decision_transitions_and_sets_fields() -> None:
    assessment = ConflictAssessment(
        conflict_assessment_id=uuid4(),
        subject_reference=uuid4(),
        conflict_type=ConflictType.DUAL_PARTY_MEMBERSHIP,
        incompatibility_level=IncompatibilityLevel.NONE,
        status=ConflictAssessmentStatus.PENDING,
        reviewed_by_role_reference=uuid4(),
    )
    under_review = assessment.with_decision(
        new_status=ConflictAssessmentStatus.UNDER_REVIEW,
        incompatibility_level=IncompatibilityLevel.NONE,
        reason_codes=(),
        decision_authority_reference=None,
        decided_at=_NOW,
    )
    resolved = under_review.with_decision(
        new_status=ConflictAssessmentStatus.RESOLVED_INCOMPATIBLE,
        incompatibility_level=IncompatibilityLevel.INCOMPATIBLE,
        reason_codes=("REASON",),
        decision_authority_reference=uuid4(),
        decided_at=_NOW,
    )
    assert resolved.status is ConflictAssessmentStatus.RESOLVED_INCOMPATIBLE


def test_parse_conflict_type_and_status_and_incompatibility_level_reject_unknown() -> None:
    with pytest.raises(UnknownConflictTypeError):
        parse_conflict_type("bogus")
    with pytest.raises(UnknownConflictAssessmentStatusError):
        parse_conflict_assessment_status("bogus")
    with pytest.raises(UnknownIncompatibilityLevelError):
        parse_incompatibility_level("bogus")


# =============================================================================
# Appeal (canon 14.3, duplicated copy)
# =============================================================================


def test_appeal_rejects_empty_grounds() -> None:
    with pytest.raises(ValueError, match="grounds"):
        Appeal(
            appeal_id=uuid4(),
            decision_id=uuid4(),
            submitted_by=uuid4(),
            grounds="",
            status=AppealStatus.SUBMITTED,
            reviewer_actor_id=None,
            result=None,
        )


def test_appeal_reviewer_separation_is_enforced_by_caller_not_domain() -> None:
    """The domain object itself has no notion of who authored the
    original decision - `application.decide_membership_appeal` enforces
    reviewer separation. Here we only check the transition table."""
    appeal = Appeal(
        appeal_id=uuid4(),
        decision_id=uuid4(),
        submitted_by=uuid4(),
        grounds="grounds",
        status=AppealStatus.SUBMITTED,
        reviewer_actor_id=None,
        result=None,
    )
    with pytest.raises(ForbiddenAppealTransitionError):
        assert_appeal_transition_allowed(AppealStatus.SUBMITTED, AppealStatus.UPHELD)
    reviewed = appeal.with_reviewer_and_status(
        reviewer_actor_id=uuid4(), new_status=AppealStatus.ADMISSIBILITY_REVIEW, result=None
    )
    assert reviewed.reviewer_actor_id is not None


# =============================================================================
# Structural boundary check (mirrors eligibility-service's own test)
# =============================================================================


def test_membership_service_domain_has_no_import_dependency_on_other_services() -> None:
    """Structural boundary check: `domain.py` must not *import*
    epd2_eligibility_service/epd2_identity_service/epd2_governance_service/
    epd2_moderation_service (README.md's boundary note, ADR-027). Checks
    actual import statements, not arbitrary text - the docstrings in this
    module legitimately mention those names in prose."""
    import ast

    import epd2_membership_service.domain as domain_module

    forbidden = {
        "epd2_eligibility_service",
        "epd2_identity_service",
        "epd2_governance_service",
        "epd2_moderation_service",
    }
    source_file = domain_module.__file__
    assert source_file is not None
    with open(source_file, encoding="utf-8") as f:
        tree = ast.parse(f.read())
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
    assert not (imported_roots & forbidden), f"{source_file} imports {imported_roots & forbidden}"
