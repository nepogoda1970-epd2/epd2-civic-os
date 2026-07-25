"""Storage protocols and in-memory reference adapters for Membership
Service's five owned entities (PACK-07, canon-0.6.0)."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from epd2_membership_service.domain import (
    AffiliationDeclaration,
    AffiliationStatus,
    Appeal,
    ConflictAssessment,
    CriticalPolicyStatus,
    Membership,
    MembershipApplication,
    PartyMembershipEligibilityPolicy,
)


class PartyMembershipEligibilityPolicyStore(Protocol):
    def save(self, policy: PartyMembershipEligibilityPolicy) -> None: ...

    def get(self, policy_id: UUID) -> PartyMembershipEligibilityPolicy | None: ...

    def resolve_for_evaluation(
        self, *, scope_type: str | None, scope_id: UUID | None, effective_date: datetime
    ) -> PartyMembershipEligibilityPolicy | None: ...


class InMemoryPartyMembershipEligibilityPolicyStore:
    def __init__(self) -> None:
        self._policies: dict[UUID, PartyMembershipEligibilityPolicy] = {}

    def save(self, policy: PartyMembershipEligibilityPolicy) -> None:
        self._policies[policy.policy_id] = policy

    def get(self, policy_id: UUID) -> PartyMembershipEligibilityPolicy | None:
        return self._policies.get(policy_id)

    def resolve_for_evaluation(
        self, *, scope_type: str | None, scope_id: UUID | None, effective_date: datetime
    ) -> PartyMembershipEligibilityPolicy | None:
        candidates = [
            policy
            for policy in self._policies.values()
            if (
                policy.status is CriticalPolicyStatus.ACTIVE
                and policy.scope_type == scope_type
                and policy.scope_id == scope_id
                and (policy.effective_from is None or policy.effective_from <= effective_date)
                and (policy.effective_until is None or effective_date < policy.effective_until)
            )
        ]
        if not candidates:
            return None
        return max(candidates, key=lambda p: p.policy_version)


class MembershipStore(Protocol):
    def save(self, membership: Membership) -> None: ...

    def get(self, membership_id: UUID) -> Membership | None: ...

    def get_for_account(
        self, *, account_reference: UUID, organization_id: UUID
    ) -> Membership | None: ...


class InMemoryMembershipStore:
    def __init__(self) -> None:
        self._memberships: dict[UUID, Membership] = {}

    def save(self, membership: Membership) -> None:
        self._memberships[membership.membership_id] = membership

    def get(self, membership_id: UUID) -> Membership | None:
        return self._memberships.get(membership_id)

    def get_for_account(
        self, *, account_reference: UUID, organization_id: UUID
    ) -> Membership | None:
        for membership in self._memberships.values():
            if (
                membership.account_reference == account_reference
                and membership.organization_id == organization_id
            ):
                return membership
        return None


class MembershipApplicationStore(Protocol):
    def save(self, application: MembershipApplication) -> None: ...

    def get(self, membership_application_id: UUID) -> MembershipApplication | None: ...

    def get_latest_for_subject(self, subject_reference: UUID) -> MembershipApplication | None: ...


class InMemoryMembershipApplicationStore:
    """`get_latest_for_subject` returns the most recently saved
    application - a durable backend would order explicitly; this
    reference adapter uses insertion order (mirrors
    `epd2_identity_service.storage.InMemoryAuthenticationContextStore`'s
    own documented precedent)."""

    def __init__(self) -> None:
        self._applications: dict[UUID, MembershipApplication] = {}
        self._by_subject_order: list[UUID] = []

    def save(self, application: MembershipApplication) -> None:
        if application.membership_application_id not in self._applications:
            self._by_subject_order.append(application.membership_application_id)
        self._applications[application.membership_application_id] = application

    def get(self, membership_application_id: UUID) -> MembershipApplication | None:
        return self._applications.get(membership_application_id)

    def get_latest_for_subject(self, subject_reference: UUID) -> MembershipApplication | None:
        for application_id in reversed(self._by_subject_order):
            application = self._applications[application_id]
            if application.subject_reference == subject_reference:
                return application
        return None


class AffiliationDeclarationStore(Protocol):
    def save(self, declaration: AffiliationDeclaration) -> None: ...

    def get(self, affiliation_declaration_id: UUID) -> AffiliationDeclaration | None: ...

    def get_active_for_subject(
        self, subject_reference: UUID
    ) -> tuple[AffiliationDeclaration, ...]: ...


class InMemoryAffiliationDeclarationStore:
    def __init__(self) -> None:
        self._declarations: dict[UUID, AffiliationDeclaration] = {}

    def save(self, declaration: AffiliationDeclaration) -> None:
        self._declarations[declaration.affiliation_declaration_id] = declaration

    def get(self, affiliation_declaration_id: UUID) -> AffiliationDeclaration | None:
        return self._declarations.get(affiliation_declaration_id)

    def get_active_for_subject(self, subject_reference: UUID) -> tuple[AffiliationDeclaration, ...]:
        return tuple(
            declaration
            for declaration in self._declarations.values()
            if (
                declaration.subject_reference == subject_reference
                and declaration.status
                in (AffiliationStatus.SUBMITTED, AffiliationStatus.ACKNOWLEDGED)
            )
        )


class ConflictAssessmentStore(Protocol):
    def save(self, assessment: ConflictAssessment) -> None: ...

    def get(self, conflict_assessment_id: UUID) -> ConflictAssessment | None: ...

    def get_latest_for_subject(self, subject_reference: UUID) -> ConflictAssessment | None: ...


class InMemoryConflictAssessmentStore:
    def __init__(self) -> None:
        self._assessments: dict[UUID, ConflictAssessment] = {}
        self._by_subject_order: list[UUID] = []

    def save(self, assessment: ConflictAssessment) -> None:
        if assessment.conflict_assessment_id not in self._assessments:
            self._by_subject_order.append(assessment.conflict_assessment_id)
        self._assessments[assessment.conflict_assessment_id] = assessment

    def get(self, conflict_assessment_id: UUID) -> ConflictAssessment | None:
        return self._assessments.get(conflict_assessment_id)

    def get_latest_for_subject(self, subject_reference: UUID) -> ConflictAssessment | None:
        for assessment_id in reversed(self._by_subject_order):
            assessment = self._assessments[assessment_id]
            if assessment.subject_reference == subject_reference:
                return assessment
        return None


class AppealStore(Protocol):
    def save(self, appeal: Appeal) -> None: ...

    def get(self, appeal_id: UUID) -> Appeal | None: ...


class InMemoryAppealStore:
    def __init__(self) -> None:
        self._appeals: dict[UUID, Appeal] = {}

    def save(self, appeal: Appeal) -> None:
        self._appeals[appeal.appeal_id] = appeal

    def get(self, appeal_id: UUID) -> Appeal | None:
        return self._appeals.get(appeal_id)
