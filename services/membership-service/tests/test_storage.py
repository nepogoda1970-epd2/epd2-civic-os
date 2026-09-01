"""Tests for epd2_membership_service.storage's in-memory reference
adapters, focused on the resolution/lookup logic beyond plain save/get
(ADR-030 item 6's "exactly one applicable policy version" procedure and
the various `get_latest_for_subject`/`get_active_for_subject` helpers)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from epd2_membership_service.domain import (
    AffiliationDeclaration,
    AffiliationStatus,
    AffiliationType,
    Appeal,
    AppealStatus,
    ConflictAssessment,
    ConflictAssessmentStatus,
    ConflictType,
    CriticalPolicyStatus,
    IncompatibilityLevel,
    Membership,
    MembershipApplication,
    MembershipApplicationStatus,
    MembershipStatus,
    PartyMembershipEligibilityPolicy,
)
from epd2_membership_service.storage import (
    InMemoryAffiliationDeclarationStore,
    InMemoryAppealStore,
    InMemoryConflictAssessmentStore,
    InMemoryMembershipApplicationStore,
    InMemoryMembershipStore,
    InMemoryPartyMembershipEligibilityPolicyStore,
)

_NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _active_policy(
    *, policy_version: int, effective_from: datetime, effective_until: datetime | None = None
) -> PartyMembershipEligibilityPolicy:
    return PartyMembershipEligibilityPolicy(
        policy_id=uuid4(),
        policy_version=policy_version,
        status=CriticalPolicyStatus.ACTIVE,
        scope_type="national",
        scope_id=None,
        effective_from=effective_from,
        effective_until=effective_until,
        adopted_by_decision_id=uuid4(),
        signed_policy_digest_reference="digest",
        transparency_log_commitment_reference="commitment",
    )


def test_resolve_for_evaluation_picks_highest_version_among_overlapping_candidates() -> None:
    store = InMemoryPartyMembershipEligibilityPolicyStore()
    v1 = _active_policy(policy_version=1, effective_from=_NOW - timedelta(days=10))
    v2 = _active_policy(policy_version=2, effective_from=_NOW - timedelta(days=5))
    store.save(v1)
    store.save(v2)
    resolved = store.resolve_for_evaluation(
        scope_type="national", scope_id=None, effective_date=_NOW
    )
    assert resolved is not None
    assert resolved.policy_version == 2


def test_resolve_for_evaluation_excludes_out_of_window_policy() -> None:
    store = InMemoryPartyMembershipEligibilityPolicyStore()
    expired = _active_policy(
        policy_version=1,
        effective_from=_NOW - timedelta(days=30),
        effective_until=_NOW - timedelta(days=1),
    )
    store.save(expired)
    resolved = store.resolve_for_evaluation(
        scope_type="national", scope_id=None, effective_date=_NOW
    )
    assert resolved is None


def test_resolve_for_evaluation_excludes_non_active_status() -> None:
    store = InMemoryPartyMembershipEligibilityPolicyStore()
    draft = PartyMembershipEligibilityPolicy(
        policy_id=uuid4(),
        policy_version=1,
        status=CriticalPolicyStatus.DRAFT,
        scope_type="national",
        scope_id=None,
        effective_from=_NOW - timedelta(days=1),
        effective_until=None,
        adopted_by_decision_id=uuid4(),
    )
    store.save(draft)
    resolved = store.resolve_for_evaluation(
        scope_type="national", scope_id=None, effective_date=_NOW
    )
    assert resolved is None


def test_resolve_for_evaluation_excludes_mismatched_scope() -> None:
    store = InMemoryPartyMembershipEligibilityPolicyStore()
    store.save(_active_policy(policy_version=1, effective_from=_NOW - timedelta(days=1)))
    resolved = store.resolve_for_evaluation(
        scope_type="regional", scope_id=uuid4(), effective_date=_NOW
    )
    assert resolved is None


def test_membership_store_get_for_account_matches_account_and_organization() -> None:
    store = InMemoryMembershipStore()
    account_reference = uuid4()
    organization_id = uuid4()
    membership = Membership(
        membership_id=uuid4(),
        account_reference=account_reference,
        organization_id=organization_id,
        membership_type="party",
        membership_status=MembershipStatus.ACTIVE,
        effective_from=_NOW,
        effective_until=None,
        region_code=None,
    )
    store.save(membership)
    assert (
        store.get_for_account(account_reference=account_reference, organization_id=organization_id)
        == membership
    )
    assert store.get_for_account(account_reference=uuid4(), organization_id=organization_id) is None


def test_membership_application_store_get_latest_for_subject_returns_most_recent() -> None:
    store = InMemoryMembershipApplicationStore()
    subject_reference = uuid4()
    first = MembershipApplication(
        membership_application_id=uuid4(),
        subject_reference=subject_reference,
        status=MembershipApplicationStatus.APPLICATION_PENDING,
    )
    second = MembershipApplication(
        membership_application_id=uuid4(),
        subject_reference=subject_reference,
        status=MembershipApplicationStatus.APPLICATION_PENDING,
    )
    store.save(first)
    store.save(second)
    assert store.get_latest_for_subject(subject_reference) == second


def test_membership_application_store_get_latest_for_subject_none_when_absent() -> None:
    store = InMemoryMembershipApplicationStore()
    assert store.get_latest_for_subject(uuid4()) is None


def test_affiliation_declaration_store_get_active_for_subject_filters_by_status() -> None:
    store = InMemoryAffiliationDeclarationStore()
    subject_reference = uuid4()
    submitted = AffiliationDeclaration(
        affiliation_declaration_id=uuid4(),
        subject_reference=subject_reference,
        affiliation_type=AffiliationType.OTHER_PARTY_MEMBERSHIP,
        declared_reference="ref-1",
        declared_at=_NOW,
        status=AffiliationStatus.SUBMITTED,
        valid_from=_NOW,
    )
    withdrawn = AffiliationDeclaration(
        affiliation_declaration_id=uuid4(),
        subject_reference=subject_reference,
        affiliation_type=AffiliationType.OTHER_PARTY_MEMBERSHIP,
        declared_reference="ref-2",
        declared_at=_NOW,
        status=AffiliationStatus.WITHDRAWN,
        valid_from=_NOW,
    )
    store.save(submitted)
    store.save(withdrawn)
    active = store.get_active_for_subject(subject_reference)
    assert active == (submitted,)


def test_conflict_assessment_store_get_latest_for_subject_returns_most_recent() -> None:
    store = InMemoryConflictAssessmentStore()
    subject_reference = uuid4()
    first = ConflictAssessment(
        conflict_assessment_id=uuid4(),
        subject_reference=subject_reference,
        conflict_type=ConflictType.DUAL_PARTY_MEMBERSHIP,
        incompatibility_level=IncompatibilityLevel.NONE,
        status=ConflictAssessmentStatus.PENDING,
        reviewed_by_role_reference=uuid4(),
    )
    second = ConflictAssessment(
        conflict_assessment_id=uuid4(),
        subject_reference=subject_reference,
        conflict_type=ConflictType.DUAL_PARTY_MEMBERSHIP,
        incompatibility_level=IncompatibilityLevel.NONE,
        status=ConflictAssessmentStatus.PENDING,
        reviewed_by_role_reference=uuid4(),
    )
    store.save(first)
    store.save(second)
    assert store.get_latest_for_subject(subject_reference) == second


def test_appeal_store_save_and_get_round_trips() -> None:
    store = InMemoryAppealStore()
    appeal = Appeal(
        appeal_id=uuid4(),
        decision_id=uuid4(),
        submitted_by=uuid4(),
        grounds="grounds",
        status=AppealStatus.SUBMITTED,
        reviewer_actor_id=None,
        result=None,
    )
    store.save(appeal)
    assert store.get(appeal.appeal_id) == appeal
    assert store.get(uuid4()) is None
