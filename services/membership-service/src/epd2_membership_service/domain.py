"""`PartyMembershipEligibilityPolicy` (canon 19d.6), `Membership` (canon
8.3 - first real implementation), `MembershipApplication` (canon 19d.9),
`AffiliationDeclaration` (canon 19d.10), `ConflictAssessment` (canon
19d.11), and a duplicated `Appeal` (canon 14.3) - PACK-07 implementation
round (ADR-026 through ADR-030).

This module has zero import dependency on `epd2_eligibility_service` or
`epd2_identity_service` - the same zero-cross-service-domain-dependency
boundary those two services' own `domain.py` modules already establish.
`CriticalPolicyStatus`/`CriticalPolicyActivationGate`/
`assert_critical_policy_activation_gate` below are a deliberate,
documented duplicate of `epd2_eligibility_service.domain`'s own copies -
never an import, per `epd2_core`'s business-logic-free charter - kept
honest by `tests/repository/test_pack07_duplicated_logic_parity.py`.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from dataclasses import replace as dataclasses_replace
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from epd2_membership_service.exceptions import (
    ConflictDecisionAuthorityRequiredError,
    CriticalPolicyActivationNotAuthorizedError,
    ForbiddenAffiliationTransitionError,
    ForbiddenAppealTransitionError,
    ForbiddenConflictAssessmentTransitionError,
    ForbiddenCriticalPolicyTransitionError,
    ForbiddenMembershipApplicationTransitionError,
    ForbiddenMembershipTransitionError,
    UnknownAffiliationStatusError,
    UnknownAffiliationTypeError,
    UnknownAffiliationVerificationStatusError,
    UnknownAppealStatusError,
    UnknownConflictAssessmentStatusError,
    UnknownConflictTypeError,
    UnknownCriticalPolicyStatusError,
    UnknownIncompatibilityLevelError,
    UnknownMembershipApplicationStatusError,
    UnknownMembershipStatusError,
)

# =============================================================================
# Duplicated critical-policy machinery (canon 19d.7) - see module docstring.
# =============================================================================


class CriticalPolicyStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    SUPERSEDED = "superseded"


CRITICAL_POLICY_ALLOWED_TRANSITIONS: frozenset[
    tuple[CriticalPolicyStatus, CriticalPolicyStatus]
] = frozenset(
    {
        (CriticalPolicyStatus.DRAFT, CriticalPolicyStatus.ACTIVE),
        (CriticalPolicyStatus.ACTIVE, CriticalPolicyStatus.SUPERSEDED),
    }
)


def parse_critical_policy_status(value: str) -> CriticalPolicyStatus:
    try:
        return CriticalPolicyStatus(value)
    except ValueError as exc:
        raise UnknownCriticalPolicyStatusError(
            f"unknown critical policy status: {value!r}"
        ) from exc


def assert_critical_policy_transition_allowed(
    current: CriticalPolicyStatus, target: CriticalPolicyStatus
) -> None:
    if (current, target) not in CRITICAL_POLICY_ALLOWED_TRANSITIONS:
        raise ForbiddenCriticalPolicyTransitionError(
            f"critical policy transition {current.value!r} -> {target.value!r} is not allowed"
        )


@dataclass(frozen=True, slots=True)
class CriticalPolicyActivationGate:
    """Canon 19d.7's four independent gates - this service's own copy,
    used for `PartyMembershipEligibilityPolicy` activation. See module
    docstring for why this is a documented duplicate of
    `epd2_eligibility_service.domain.CriticalPolicyActivationGate`, not
    an import."""

    decision_authorized: bool
    multi_person_approval_met: bool
    signed_policy_digest_reference: str | None
    transparency_log_commitment_reference: str | None


def assert_critical_policy_activation_gate(gate: CriticalPolicyActivationGate) -> None:
    """Fail-closed: every one of the four gates must independently hold
    (canon 19d.7). Kept in lockstep with `epd2_eligibility_service.domain.
    assert_critical_policy_activation_gate` by
    `tests/repository/test_pack07_duplicated_logic_parity.py`."""
    if not gate.decision_authorized:
        raise CriticalPolicyActivationNotAuthorizedError(
            "critical policy activation requires an authorized GovernanceDecision"
        )
    if not gate.multi_person_approval_met:
        raise CriticalPolicyActivationNotAuthorizedError(
            "critical policy activation requires multi_person_approval_met"
        )
    if not gate.signed_policy_digest_reference:
        raise CriticalPolicyActivationNotAuthorizedError(
            "critical policy activation requires signed_policy_digest_reference"
        )
    if not gate.transparency_log_commitment_reference:
        raise CriticalPolicyActivationNotAuthorizedError(
            "critical policy activation requires transparency_log_commitment_reference"
        )


# =============================================================================
# PartyMembershipEligibilityPolicy (canon 19d.6)
# =============================================================================


@dataclass(frozen=True, slots=True)
class PartyMembershipEligibilityPolicy:
    """Canon 19d.6: shares `ParticipantEligibilityPolicy`'s (19d.4) field
    set and lifecycle, plus `incompatibility_rules`/
    `membership_duration_rules`. Structurally separate from
    `ParticipantEligibilityPolicy` - neither is a special case of the
    other (canon 19d.4's own framing)."""

    policy_id: UUID
    policy_version: int
    status: CriticalPolicyStatus
    scope_type: str | None
    scope_id: UUID | None
    effective_from: datetime | None
    effective_until: datetime | None
    adopted_by_decision_id: UUID
    age_thresholds: tuple[Mapping[str, object], ...] = ()
    citizenship_conditions: tuple[Mapping[str, object], ...] = ()
    residence_conditions: tuple[Mapping[str, object], ...] = ()
    exemptions: tuple[Mapping[str, object], ...] = ()
    transitional_rules: tuple[Mapping[str, object], ...] = ()
    incompatibility_rules: tuple[str, ...] = ()
    membership_duration_rules: Mapping[str, object] | None = None
    supersedes_policy_id: UUID | None = None
    signed_policy_digest_reference: str | None = None
    transparency_log_commitment_reference: str | None = None

    def __post_init__(self) -> None:
        if self.policy_version < 1:
            raise ValueError("policy_version must be >= 1")
        if self.status is CriticalPolicyStatus.ACTIVE:
            if not self.signed_policy_digest_reference:
                raise ValueError("signed_policy_digest_reference is required when status=active")
            if not self.transparency_log_commitment_reference:
                raise ValueError(
                    "transparency_log_commitment_reference is required when status=active"
                )
        if self.effective_from is not None and self.effective_from.tzinfo is None:
            raise ValueError("effective_from must be timezone-aware")
        if self.effective_until is not None and self.effective_until.tzinfo is None:
            raise ValueError("effective_until must be timezone-aware")

    def with_status(self, new_status: CriticalPolicyStatus) -> PartyMembershipEligibilityPolicy:
        assert_critical_policy_transition_allowed(self.status, new_status)
        return dataclasses_replace(self, status=new_status)


# =============================================================================
# Membership (canon 8.3 - first real implementation)
# =============================================================================


class MembershipStatus(StrEnum):
    """Canon 8.3's exact, unchanged seven-value status list."""

    APPLICATION_PENDING = "application_pending"
    VERIFICATION_PENDING = "verification_pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"
    REJECTED = "rejected"
    EXPIRED = "expired"


#: Canon 19d.9: `Membership.membership_status` transitions to
#: `active`/`suspended`/`terminated`/`expired` are, in this
#: implementation, reached exclusively through `MembershipApplication`
#: (`active`) or an explicit Stage-B-equivalent human decision
#: (`suspended`/`terminated`/restoration/`expired`) - never a bare
#: domain-level transition with no accompanying human-decision record.
#: This table only expresses which raw transitions are ever structurally
#: valid; `application.py`'s own commands are what actually enforce the
#: human-decision requirement (canon 19d.16).
MEMBERSHIP_ALLOWED_TRANSITIONS: frozenset[tuple[MembershipStatus, MembershipStatus]] = frozenset(
    {
        (MembershipStatus.APPLICATION_PENDING, MembershipStatus.VERIFICATION_PENDING),
        (MembershipStatus.APPLICATION_PENDING, MembershipStatus.ACTIVE),
        (MembershipStatus.APPLICATION_PENDING, MembershipStatus.REJECTED),
        (MembershipStatus.VERIFICATION_PENDING, MembershipStatus.ACTIVE),
        (MembershipStatus.VERIFICATION_PENDING, MembershipStatus.REJECTED),
        (MembershipStatus.ACTIVE, MembershipStatus.SUSPENDED),
        (MembershipStatus.ACTIVE, MembershipStatus.TERMINATED),
        (MembershipStatus.ACTIVE, MembershipStatus.EXPIRED),
        (MembershipStatus.SUSPENDED, MembershipStatus.ACTIVE),
        (MembershipStatus.SUSPENDED, MembershipStatus.TERMINATED),
        (MembershipStatus.SUSPENDED, MembershipStatus.EXPIRED),
    }
)


def parse_membership_status(value: str) -> MembershipStatus:
    try:
        return MembershipStatus(value)
    except ValueError as exc:
        raise UnknownMembershipStatusError(f"unknown membership status: {value!r}") from exc


def assert_membership_transition_allowed(
    current: MembershipStatus, target: MembershipStatus
) -> None:
    if (current, target) not in MEMBERSHIP_ALLOWED_TRANSITIONS:
        raise ForbiddenMembershipTransitionError(
            f"membership transition {current.value!r} -> {target.value!r} is not allowed"
        )


@dataclass(frozen=True, slots=True)
class Membership:
    """Canon 8.3's exact, unchanged eight-field set."""

    membership_id: UUID
    account_reference: UUID
    organization_id: UUID
    membership_type: str
    membership_status: MembershipStatus
    effective_from: datetime | None
    effective_until: datetime | None
    region_code: str | None

    def __post_init__(self) -> None:
        if not self.membership_type:
            raise ValueError("membership_type must not be empty")
        if self.effective_from is not None and self.effective_from.tzinfo is None:
            raise ValueError("effective_from must be timezone-aware")
        if self.effective_until is not None and self.effective_until.tzinfo is None:
            raise ValueError("effective_until must be timezone-aware")

    def with_status(
        self, new_status: MembershipStatus, *, effective_from: datetime | None = None
    ) -> Membership:
        assert_membership_transition_allowed(self.membership_status, new_status)
        return dataclasses_replace(
            self,
            membership_status=new_status,
            effective_from=effective_from if effective_from is not None else self.effective_from,
        )


# =============================================================================
# MembershipApplication (canon 19d.9)
# =============================================================================


class MembershipApplicationStatus(StrEnum):
    """Canon 19d.9's exact six-value lifecycle."""

    APPLICATION_PENDING = "application_pending"
    ELIGIBILITY_REVIEW = "eligibility_review"
    HUMAN_DECISION_PENDING = "human_decision_pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ACTIVATED = "activated"


MEMBERSHIP_APPLICATION_ALLOWED_TRANSITIONS: frozenset[
    tuple[MembershipApplicationStatus, MembershipApplicationStatus]
] = frozenset(
    {
        (
            MembershipApplicationStatus.APPLICATION_PENDING,
            MembershipApplicationStatus.ELIGIBILITY_REVIEW,
        ),
        (
            MembershipApplicationStatus.ELIGIBILITY_REVIEW,
            MembershipApplicationStatus.HUMAN_DECISION_PENDING,
        ),
        (
            MembershipApplicationStatus.HUMAN_DECISION_PENDING,
            MembershipApplicationStatus.APPROVED,
        ),
        (
            MembershipApplicationStatus.HUMAN_DECISION_PENDING,
            MembershipApplicationStatus.REJECTED,
        ),
        (MembershipApplicationStatus.APPROVED, MembershipApplicationStatus.ACTIVATED),
    }
)


def parse_membership_application_status(value: str) -> MembershipApplicationStatus:
    try:
        return MembershipApplicationStatus(value)
    except ValueError as exc:
        raise UnknownMembershipApplicationStatusError(
            f"unknown membership application status: {value!r}"
        ) from exc


def assert_membership_application_transition_allowed(
    current: MembershipApplicationStatus, target: MembershipApplicationStatus
) -> None:
    if (current, target) not in MEMBERSHIP_APPLICATION_ALLOWED_TRANSITIONS:
        raise ForbiddenMembershipApplicationTransitionError(
            f"membership application transition {current.value!r} -> {target.value!r} "
            "is not allowed"
        )


@dataclass(frozen=True, slots=True)
class MembershipApplication:
    """Canon 19d.9's new, dedicated entity. `decision_authority_reference`/
    `applied_policy_version`/`reason_code`/`decided_at`/`audit_event_reference`
    are Stage B's own decision record fields - all `None` until Stage B
    actually runs (`application.record_membership_human_decision`)."""

    membership_application_id: UUID
    subject_reference: UUID
    status: MembershipApplicationStatus
    decision_authority_reference: UUID | None = None
    applied_policy_version: int | None = None
    reason_code: str | None = None
    decided_at: datetime | None = None
    audit_event_reference: UUID | None = None
    supersedes_membership_application_id: UUID | None = None

    def __post_init__(self) -> None:
        if self.decided_at is not None and self.decided_at.tzinfo is None:
            raise ValueError("decided_at must be timezone-aware")
        if self.status in (
            MembershipApplicationStatus.APPROVED,
            MembershipApplicationStatus.REJECTED,
        ):
            if self.decision_authority_reference is None:
                raise ValueError(
                    "decision_authority_reference is required once status is "
                    "approved or rejected (canon 19d.9 Stage B)"
                )
            if self.reason_code is None or self.decided_at is None:
                raise ValueError(
                    "reason_code and decided_at are required once status is "
                    "approved or rejected (canon 19d.9 Stage B)"
                )

    def with_status(
        self,
        new_status: MembershipApplicationStatus,
        *,
        decision_authority_reference: UUID | None = None,
        applied_policy_version: int | None = None,
        reason_code: str | None = None,
        decided_at: datetime | None = None,
        audit_event_reference: UUID | None = None,
    ) -> MembershipApplication:
        assert_membership_application_transition_allowed(self.status, new_status)
        return MembershipApplication(
            membership_application_id=self.membership_application_id,
            subject_reference=self.subject_reference,
            status=new_status,
            decision_authority_reference=(
                decision_authority_reference
                if decision_authority_reference is not None
                else self.decision_authority_reference
            ),
            applied_policy_version=(
                applied_policy_version
                if applied_policy_version is not None
                else self.applied_policy_version
            ),
            reason_code=reason_code if reason_code is not None else self.reason_code,
            decided_at=decided_at if decided_at is not None else self.decided_at,
            audit_event_reference=(
                audit_event_reference
                if audit_event_reference is not None
                else self.audit_event_reference
            ),
            supersedes_membership_application_id=self.supersedes_membership_application_id,
        )


# =============================================================================
# AffiliationDeclaration (canon 19d.10)
# =============================================================================


class AffiliationType(StrEnum):
    OTHER_PARTY_MEMBERSHIP = "other_party_membership"
    POLITICAL_ASSOCIATION_MEMBERSHIP = "political_association_membership"
    PUBLIC_OFFICE = "public_office"
    ELECTED_OFFICE = "elected_office"
    LOBBYING_OR_INTEREST_REPRESENTATION = "lobbying_or_interest_representation"
    ORGANIZATIONAL_LEADERSHIP_OR_EMPLOYMENT = "organizational_leadership_or_employment"
    DECLARED_INCOMPATIBLE_ORGANIZATION = "declared_incompatible_organization"


def parse_affiliation_type(value: str) -> AffiliationType:
    try:
        return AffiliationType(value)
    except ValueError as exc:
        raise UnknownAffiliationTypeError(f"unknown affiliation type: {value!r}") from exc


class AffiliationStatus(StrEnum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    ACKNOWLEDGED = "acknowledged"
    SUPERSEDED = "superseded"
    WITHDRAWN = "withdrawn"


AFFILIATION_ALLOWED_TRANSITIONS: frozenset[tuple[AffiliationStatus, AffiliationStatus]] = frozenset(
    {
        (AffiliationStatus.DRAFT, AffiliationStatus.SUBMITTED),
        (AffiliationStatus.SUBMITTED, AffiliationStatus.UNDER_REVIEW),
        (AffiliationStatus.UNDER_REVIEW, AffiliationStatus.ACKNOWLEDGED),
        (AffiliationStatus.DRAFT, AffiliationStatus.WITHDRAWN),
        (AffiliationStatus.SUBMITTED, AffiliationStatus.WITHDRAWN),
        (AffiliationStatus.UNDER_REVIEW, AffiliationStatus.WITHDRAWN),
        (AffiliationStatus.ACKNOWLEDGED, AffiliationStatus.SUPERSEDED),
    }
)


def parse_affiliation_status(value: str) -> AffiliationStatus:
    try:
        return AffiliationStatus(value)
    except ValueError as exc:
        raise UnknownAffiliationStatusError(f"unknown affiliation status: {value!r}") from exc


def assert_affiliation_transition_allowed(
    current: AffiliationStatus, target: AffiliationStatus
) -> None:
    if (current, target) not in AFFILIATION_ALLOWED_TRANSITIONS:
        raise ForbiddenAffiliationTransitionError(
            f"affiliation transition {current.value!r} -> {target.value!r} is not allowed"
        )


class AffiliationVerificationStatus(StrEnum):
    DECLARED = "declared"
    VERIFIED = "verified"
    DISPUTED = "disputed"
    UNVERIFIABLE = "unverifiable"


def parse_affiliation_verification_status(value: str) -> AffiliationVerificationStatus:
    try:
        return AffiliationVerificationStatus(value)
    except ValueError as exc:
        raise UnknownAffiliationVerificationStatusError(
            f"unknown affiliation verification status: {value!r}"
        ) from exc


@dataclass(frozen=True, slots=True)
class AffiliationDeclaration:
    """Canon 19d.10's exact field set. `declared_reference` is an opaque
    reference, never a free-text organization name at the schema level
    (canon: "никогда свободный текст названия организации на уровне
    схемы"). Targeted - exists only to feed `ConflictAssessment`, never a
    general political-profiling system (canon 19d.10's own framing)."""

    affiliation_declaration_id: UUID
    subject_reference: UUID
    affiliation_type: AffiliationType
    declared_reference: str
    declared_at: datetime
    status: AffiliationStatus
    valid_from: datetime
    verification_status: AffiliationVerificationStatus = AffiliationVerificationStatus.DECLARED
    supersedes_declaration_id: UUID | None = None
    valid_until: datetime | None = None
    verified_at: datetime | None = None
    verified_by: UUID | None = None

    def __post_init__(self) -> None:
        if not self.declared_reference:
            raise ValueError("declared_reference must not be empty")
        if self.declared_at.tzinfo is None:
            raise ValueError("declared_at must be timezone-aware")
        if self.valid_from.tzinfo is None:
            raise ValueError("valid_from must be timezone-aware")
        if self.valid_until is not None and self.valid_until.tzinfo is None:
            raise ValueError("valid_until must be timezone-aware")
        if self.verified_at is not None and self.verified_at.tzinfo is None:
            raise ValueError("verified_at must be timezone-aware")

    def with_status(self, new_status: AffiliationStatus) -> AffiliationDeclaration:
        assert_affiliation_transition_allowed(self.status, new_status)
        return dataclasses_replace(self, status=new_status)

    def with_verification(
        self,
        *,
        verification_status: AffiliationVerificationStatus,
        verified_at: datetime,
        verified_by: UUID,
    ) -> AffiliationDeclaration:
        """`verified_by` must never be `subject_reference` itself (a
        declarant cannot verify their own declaration) - enforced by the
        caller (`application.py`), which alone knows `verified_by`'s
        actor identity relationship to `subject_reference`."""
        return dataclasses_replace(
            self,
            verification_status=verification_status,
            verified_at=verified_at,
            verified_by=verified_by,
        )


# =============================================================================
# ConflictAssessment (canon 19d.11)
# =============================================================================


class ConflictType(StrEnum):
    DUAL_PARTY_MEMBERSHIP = "dual_party_membership"
    POLITICAL_ASSOCIATION_CONFLICT = "political_association_conflict"
    PUBLIC_OFFICE_INCOMPATIBILITY = "public_office_incompatibility"
    LOBBYING_ROLE_INCOMPATIBILITY = "lobbying_role_incompatibility"
    ORGANIZATIONAL_AFFILIATION_CONFLICT = "organizational_affiliation_conflict"
    DECLARED_INCOMPATIBLE_ORGANIZATION = "declared_incompatible_organization"


def parse_conflict_type(value: str) -> ConflictType:
    try:
        return ConflictType(value)
    except ValueError as exc:
        raise UnknownConflictTypeError(f"unknown conflict type: {value!r}") from exc


class IncompatibilityLevel(StrEnum):
    NONE = "none"
    DISCLOSED_NO_CONFLICT = "disclosed_no_conflict"
    CONDITIONAL_RESTRICTION = "conditional_restriction"
    INCOMPATIBLE = "incompatible"


def parse_incompatibility_level(value: str) -> IncompatibilityLevel:
    try:
        return IncompatibilityLevel(value)
    except ValueError as exc:
        raise UnknownIncompatibilityLevelError(f"unknown incompatibility level: {value!r}") from exc


class ConflictAssessmentStatus(StrEnum):
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    RESOLVED_NO_CONFLICT = "resolved_no_conflict"
    RESOLVED_CONDITIONAL = "resolved_conditional"
    RESOLVED_INCOMPATIBLE = "resolved_incompatible"
    APPEALED = "appealed"
    OVERTURNED = "overturned"
    EXPIRED_REEVALUATION_DUE = "expired_reevaluation_due"


CONFLICT_ASSESSMENT_ALLOWED_TRANSITIONS: frozenset[
    tuple[ConflictAssessmentStatus, ConflictAssessmentStatus]
] = frozenset(
    {
        (ConflictAssessmentStatus.PENDING, ConflictAssessmentStatus.UNDER_REVIEW),
        (ConflictAssessmentStatus.UNDER_REVIEW, ConflictAssessmentStatus.RESOLVED_NO_CONFLICT),
        (ConflictAssessmentStatus.UNDER_REVIEW, ConflictAssessmentStatus.RESOLVED_CONDITIONAL),
        (ConflictAssessmentStatus.UNDER_REVIEW, ConflictAssessmentStatus.RESOLVED_INCOMPATIBLE),
        (ConflictAssessmentStatus.RESOLVED_INCOMPATIBLE, ConflictAssessmentStatus.APPEALED),
        (ConflictAssessmentStatus.RESOLVED_CONDITIONAL, ConflictAssessmentStatus.APPEALED),
        (ConflictAssessmentStatus.APPEALED, ConflictAssessmentStatus.OVERTURNED),
        (
            ConflictAssessmentStatus.RESOLVED_CONDITIONAL,
            ConflictAssessmentStatus.EXPIRED_REEVALUATION_DUE,
        ),
        (
            ConflictAssessmentStatus.RESOLVED_INCOMPATIBLE,
            ConflictAssessmentStatus.EXPIRED_REEVALUATION_DUE,
        ),
    }
)


def parse_conflict_assessment_status(value: str) -> ConflictAssessmentStatus:
    try:
        return ConflictAssessmentStatus(value)
    except ValueError as exc:
        raise UnknownConflictAssessmentStatusError(
            f"unknown conflict assessment status: {value!r}"
        ) from exc


def assert_conflict_assessment_transition_allowed(
    current: ConflictAssessmentStatus, target: ConflictAssessmentStatus
) -> None:
    if (current, target) not in CONFLICT_ASSESSMENT_ALLOWED_TRANSITIONS:
        raise ForbiddenConflictAssessmentTransitionError(
            f"conflict assessment transition {current.value!r} -> {target.value!r} is not allowed"
        )


@dataclass(frozen=True, slots=True)
class ConflictAssessment:
    """Canon 19d.11's exact field set. `decision_authority_reference` is
    mandatory once `status=resolved_incompatible` (enforced below,
    fail-closed) - the same Stage-B-style human-decision requirement
    `MembershipApplication` enforces for admission."""

    conflict_assessment_id: UUID
    subject_reference: UUID
    conflict_type: ConflictType
    incompatibility_level: IncompatibilityLevel
    status: ConflictAssessmentStatus
    reviewed_by_role_reference: UUID
    affiliation_declaration_id: UUID | None = None
    reason_codes: tuple[str, ...] = ()
    evidence_references: tuple[str, ...] = ()
    decision_authority_reference: UUID | None = None
    decided_at: datetime | None = None
    supersedes_conflict_assessment_id: UUID | None = None
    re_evaluation_due_at: datetime | None = None

    def __post_init__(self) -> None:
        if (
            self.status is ConflictAssessmentStatus.RESOLVED_INCOMPATIBLE
            and self.decision_authority_reference is None
        ):
            raise ConflictDecisionAuthorityRequiredError(
                "decision_authority_reference is required when "
                "status=resolved_incompatible (canon 19d.11)"
            )
        if self.decided_at is not None and self.decided_at.tzinfo is None:
            raise ValueError("decided_at must be timezone-aware")
        if self.re_evaluation_due_at is not None and self.re_evaluation_due_at.tzinfo is None:
            raise ValueError("re_evaluation_due_at must be timezone-aware")

    def with_decision(
        self,
        *,
        new_status: ConflictAssessmentStatus,
        incompatibility_level: IncompatibilityLevel,
        reason_codes: tuple[str, ...],
        decision_authority_reference: UUID | None,
        decided_at: datetime,
        re_evaluation_due_at: datetime | None = None,
    ) -> ConflictAssessment:
        assert_conflict_assessment_transition_allowed(self.status, new_status)
        return ConflictAssessment(
            conflict_assessment_id=self.conflict_assessment_id,
            subject_reference=self.subject_reference,
            conflict_type=self.conflict_type,
            incompatibility_level=incompatibility_level,
            status=new_status,
            reviewed_by_role_reference=self.reviewed_by_role_reference,
            affiliation_declaration_id=self.affiliation_declaration_id,
            reason_codes=reason_codes,
            evidence_references=self.evidence_references,
            decision_authority_reference=decision_authority_reference,
            decided_at=decided_at,
            supersedes_conflict_assessment_id=self.supersedes_conflict_assessment_id,
            re_evaluation_due_at=re_evaluation_due_at,
        )


# =============================================================================
# Appeal (canon 14.3) - duplicated, not imported (see module docstring).
# =============================================================================


class AppealStatus(StrEnum):
    SUBMITTED = "submitted"
    ADMISSIBILITY_REVIEW = "admissibility_review"
    UNDER_REVIEW = "under_review"
    UPHELD = "upheld"
    PARTIALLY_UPHELD = "partially_upheld"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


#: The final review outcomes `application.decide_membership_appeal` may
#: produce - mirrors `epd2_moderation_service.domain.FINAL_APPEAL_OUTCOMES`.
FINAL_APPEAL_OUTCOMES: frozenset[AppealStatus] = frozenset(
    {AppealStatus.UPHELD, AppealStatus.PARTIALLY_UPHELD, AppealStatus.REJECTED}
)

APPEAL_ALLOWED_TRANSITIONS: frozenset[tuple[AppealStatus, AppealStatus]] = frozenset(
    {
        (AppealStatus.SUBMITTED, AppealStatus.ADMISSIBILITY_REVIEW),
        (AppealStatus.ADMISSIBILITY_REVIEW, AppealStatus.UNDER_REVIEW),
        (AppealStatus.ADMISSIBILITY_REVIEW, AppealStatus.REJECTED),
        (AppealStatus.UNDER_REVIEW, AppealStatus.UPHELD),
        (AppealStatus.UNDER_REVIEW, AppealStatus.PARTIALLY_UPHELD),
        (AppealStatus.UNDER_REVIEW, AppealStatus.REJECTED),
        (AppealStatus.SUBMITTED, AppealStatus.WITHDRAWN),
        (AppealStatus.ADMISSIBILITY_REVIEW, AppealStatus.WITHDRAWN),
        (AppealStatus.UNDER_REVIEW, AppealStatus.WITHDRAWN),
    }
)


def parse_appeal_status(value: str) -> AppealStatus:
    try:
        return AppealStatus(value)
    except ValueError as exc:
        raise UnknownAppealStatusError(f"unknown appeal status: {value!r}") from exc


def assert_appeal_transition_allowed(current: AppealStatus, target: AppealStatus) -> None:
    if (current, target) not in APPEAL_ALLOWED_TRANSITIONS:
        raise ForbiddenAppealTransitionError(
            f"appeal transition {current.value!r} -> {target.value!r} is not allowed"
        )


@dataclass(frozen=True, slots=True)
class Appeal:
    """Canon 14.3's exact field set - this service's own copy, reused
    (per ADR-030 item 4's standing default) for `ConflictAssessment` and
    `MembershipApplication` rejection appeals via the already-generic
    `decision_id` field. See module docstring for why this is a
    documented duplicate of `epd2_moderation_service.domain.Appeal`, not
    an import - `epd2_core`'s charter forbids a shared business-logic
    home, and this pack's own service-boundary rules forbid a
    `membership-service -> moderation-service` import that no ADR
    authorizes."""

    appeal_id: UUID
    decision_id: UUID
    submitted_by: UUID
    grounds: str
    status: AppealStatus
    reviewer_actor_id: UUID | None
    result: str | None

    def __post_init__(self) -> None:
        if not self.grounds:
            raise ValueError("grounds must not be empty")

    def with_status(self, new_status: AppealStatus) -> Appeal:
        assert_appeal_transition_allowed(self.status, new_status)
        return dataclasses_replace(self, status=new_status)

    def with_reviewer_and_status(
        self, *, reviewer_actor_id: UUID, new_status: AppealStatus, result: str | None
    ) -> Appeal:
        assert_appeal_transition_allowed(self.status, new_status)
        return dataclasses_replace(
            self, status=new_status, reviewer_actor_id=reviewer_actor_id, result=result
        )


# =============================================================================
# Narrow cross-pack read result shapes (ADR-027)
# =============================================================================


@dataclass(frozen=True, slots=True)
class MembershipDerivedClaims:
    """The exact two-boolean shape ADR-027 fixes for
    `application.get_membership_derived_claims` - `eligibility-service`'s
    one sanctioned read into this service. Never the raw `Membership`
    row."""

    required_membership_status_met: bool
    membership_duration_requirement_met: bool
    reason_code: str | None


@dataclass(frozen=True, slots=True)
class StageAEligibilityResult:
    """The result of `application.evaluate_membership_application_eligibility`
    (Stage A, canon 19d.9) - a `recommended` outcome only, never final
    (canon 19d.16's hard human-control invariant - see README.md)."""

    recommended_approval: bool
    reason_codes: tuple[str, ...]
