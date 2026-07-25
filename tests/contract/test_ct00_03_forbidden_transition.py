"""CT-00-03 Forbidden Transition (canon section 27): a forbidden status
transition is rejected, for every service with a status transition table."""

from __future__ import annotations

import pytest

from epd2_account_service.domain import AccountStatus
from epd2_account_service.domain import assert_transition_allowed as assert_account_transition
from epd2_account_service.exceptions import ForbiddenAccountTransitionError
from epd2_ai_processing_service.domain import (
    ForbiddenHumanReviewStatusTransitionError,
    ForbiddenProcessingStatusTransitionError,
    HumanReviewStatus,
    ProcessingStatus,
    assert_human_review_status_transition_allowed,
    assert_processing_status_transition_allowed,
)
from epd2_credential_service.domain import CredentialStatus
from epd2_credential_service.domain import assert_transition_allowed as assert_credential_transition
from epd2_credential_service.exceptions import ForbiddenCredentialTransitionError
from epd2_delegation_service.domain import (
    DelegationStatus,
    assert_delegation_transition_allowed,
)
from epd2_delegation_service.exceptions import ForbiddenDelegationTransitionError
from epd2_deliberation_service.domain import (
    ContributionVisibilityStatus,
    DiscussionStatus,
    assert_contribution_visibility_transition_allowed,
    assert_discussion_transition_allowed,
)
from epd2_deliberation_service.exceptions import (
    ForbiddenContributionVisibilityTransitionError,
    ForbiddenDiscussionTransitionError,
)
from epd2_eligibility_service.domain import (
    AssemblyDecisionStatus,
    assert_assembly_decision_transition_allowed,
)
from epd2_eligibility_service.domain import CriticalPolicyStatus as EligibilityCriticalPolicyStatus
from epd2_eligibility_service.domain import (
    assert_critical_policy_transition_allowed as assert_eligibility_policy_transition_allowed,
)
from epd2_eligibility_service.exceptions import ForbiddenAssemblyDecisionTransitionError
from epd2_eligibility_service.exceptions import (
    ForbiddenCriticalPolicyTransitionError as ForbiddenEligibilityCriticalPolicyTransitionError,
)
from epd2_governance_service.domain import (
    GovernanceDecisionStatus,
    GovernancePolicyStatus,
    RoleAssignmentStatus,
    TechnicalChallengeStatus,
    assert_governance_decision_transition_allowed,
    assert_governance_policy_transition_allowed,
    assert_role_assignment_transition_allowed,
    assert_technical_challenge_transition_allowed,
)
from epd2_governance_service.exceptions import (
    ForbiddenGovernanceDecisionTransitionError,
    ForbiddenGovernancePolicyTransitionError,
    ForbiddenRoleAssignmentTransitionError,
    ForbiddenTechnicalChallengeTransitionError,
)
from epd2_identity_service.domain import VerificationStatus
from epd2_identity_service.domain import assert_transition_allowed as assert_identity_transition
from epd2_identity_service.exceptions import ForbiddenVerificationTransitionError
from epd2_initiative_service.domain import (
    AmendmentStatus,
    InitiativeStatus,
    SourceVerificationStatus,
    SupportStatus,
    assert_amendment_transition_allowed,
    assert_initiative_transition_allowed,
    assert_source_verification_transition_allowed,
    assert_support_transition_allowed,
)
from epd2_initiative_service.exceptions import (
    ForbiddenAmendmentTransitionError,
    ForbiddenInitiativeTransitionError,
    ForbiddenSourceVerificationTransitionError,
    ForbiddenSupportTransitionError,
)
from epd2_membership_service.domain import (
    AffiliationStatus,
    ConflictAssessmentStatus,
    MembershipApplicationStatus,
    MembershipStatus,
    assert_affiliation_transition_allowed,
    assert_conflict_assessment_transition_allowed,
    assert_membership_application_transition_allowed,
    assert_membership_transition_allowed,
)
from epd2_membership_service.domain import AppealStatus as MembershipAppealStatus
from epd2_membership_service.domain import (
    CriticalPolicyStatus as MembershipCriticalPolicyStatus,
)
from epd2_membership_service.domain import (
    assert_appeal_transition_allowed as assert_membership_appeal_transition_allowed,
)
from epd2_membership_service.domain import (
    assert_critical_policy_transition_allowed as assert_membership_policy_transition_allowed,
)
from epd2_membership_service.exceptions import (
    ForbiddenAffiliationTransitionError,
    ForbiddenConflictAssessmentTransitionError,
    ForbiddenMembershipApplicationTransitionError,
    ForbiddenMembershipTransitionError,
)
from epd2_membership_service.exceptions import (
    ForbiddenAppealTransitionError as ForbiddenMembershipAppealTransitionError,
)
from epd2_membership_service.exceptions import (
    ForbiddenCriticalPolicyTransitionError as ForbiddenMembershipCriticalPolicyTransitionError,
)
from epd2_moderation_service.domain import (
    AppealStatus,
    ModerationCaseStatus,
    assert_appeal_transition_allowed,
    assert_case_transition_allowed,
)
from epd2_moderation_service.exceptions import (
    ForbiddenAppealTransitionError,
    ForbiddenModerationCaseTransitionError,
)
from epd2_tally_service.domain import (
    TallyVerificationStatus,
)
from epd2_tally_service.domain import (
    assert_transition_allowed as assert_tally_transition,
)
from epd2_tally_service.exceptions import ForbiddenTallyTransitionError
from epd2_voting_service.domain import (
    BallotOptionStatus,
    BallotStatus,
    VoteEnvelopeStatus,
    VoteReceiptVerificationStatus,
    assert_ballot_option_transition_allowed,
    assert_ballot_transition_allowed,
    assert_receipt_transition_allowed,
    assert_vote_envelope_transition_allowed,
)
from epd2_voting_service.exceptions import (
    ForbiddenBallotOptionTransitionError,
    ForbiddenBallotTransitionError,
    ForbiddenVoteEnvelopeTransitionError,
    ForbiddenVoteReceiptTransitionError,
)


def test_account_closed_is_terminal() -> None:
    """`closed` has no outgoing transitions (README.md / OPEN_QUESTIONS.md
    conservative reading)."""
    with pytest.raises(ForbiddenAccountTransitionError) as excinfo:
        assert_account_transition(AccountStatus.CLOSED, AccountStatus.ACTIVE)
    assert excinfo.value.reason_code == "VALIDATION_FORBIDDEN_TRANSITION"


def test_account_pending_to_suspended_is_forbidden() -> None:
    """A pending account must be activated before it can be suspended."""
    with pytest.raises(ForbiddenAccountTransitionError):
        assert_account_transition(AccountStatus.PENDING, AccountStatus.SUSPENDED)


def test_identity_failed_cannot_go_directly_to_verified() -> None:
    with pytest.raises(ForbiddenVerificationTransitionError) as excinfo:
        assert_identity_transition(VerificationStatus.FAILED, VerificationStatus.VERIFIED)
    assert excinfo.value.reason_code == "VALIDATION_FORBIDDEN_TRANSITION"


def test_identity_expired_cannot_go_directly_to_verified() -> None:
    with pytest.raises(ForbiddenVerificationTransitionError):
        assert_identity_transition(VerificationStatus.EXPIRED, VerificationStatus.VERIFIED)


def test_credential_revoked_is_terminal() -> None:
    with pytest.raises(ForbiddenCredentialTransitionError) as excinfo:
        assert_credential_transition(CredentialStatus.REVOKED, CredentialStatus.ACTIVE)
    assert excinfo.value.reason_code == "VALIDATION_FORBIDDEN_TRANSITION"


# =============================================================================
# PACK-03: at least one real forbidden pair from each entity with a real
# state machine, plus the two critical named-in-spec cases as their own
# explicit, clearly-named tests.
# =============================================================================


def test_initiative_draft_cannot_go_directly_to_qualified() -> None:
    with pytest.raises(ForbiddenInitiativeTransitionError) as excinfo:
        assert_initiative_transition_allowed(InitiativeStatus.DRAFT, InitiativeStatus.QUALIFIED)
    assert excinfo.value.reason_code == "VALIDATION_FORBIDDEN_TRANSITION"


def test_support_record_withdrawn_is_terminal() -> None:
    with pytest.raises(ForbiddenSupportTransitionError):
        assert_support_transition_allowed(SupportStatus.WITHDRAWN, SupportStatus.ACTIVE)


def test_amendment_rejected_is_terminal() -> None:
    with pytest.raises(ForbiddenAmendmentTransitionError):
        assert_amendment_transition_allowed(AmendmentStatus.REJECTED, AmendmentStatus.PUBLISHED)


def test_source_record_outdated_cannot_go_back_to_unverified() -> None:
    with pytest.raises(ForbiddenSourceVerificationTransitionError):
        assert_source_verification_transition_allowed(
            SourceVerificationStatus.OUTDATED, SourceVerificationStatus.UNVERIFIED
        )


def test_discussion_archived_is_terminal() -> None:
    with pytest.raises(ForbiddenDiscussionTransitionError):
        assert_discussion_transition_allowed(DiscussionStatus.ARCHIVED, DiscussionStatus.OPEN)


def test_contribution_visible_cannot_go_directly_to_restored() -> None:
    with pytest.raises(ForbiddenContributionVisibilityTransitionError):
        assert_contribution_visibility_transition_allowed(
            ContributionVisibilityStatus.VISIBLE, ContributionVisibilityStatus.RESTORED
        )


def test_moderation_case_open_cannot_go_directly_to_decided() -> None:
    with pytest.raises(ForbiddenModerationCaseTransitionError):
        assert_case_transition_allowed(ModerationCaseStatus.OPEN, ModerationCaseStatus.DECIDED)


def test_appeal_upheld_is_terminal() -> None:
    with pytest.raises(ForbiddenAppealTransitionError):
        assert_appeal_transition_allowed(AppealStatus.UPHELD, AppealStatus.UNDER_REVIEW)


def test_ballot_option_locked_cannot_return_to_active() -> None:
    with pytest.raises(ForbiddenBallotOptionTransitionError):
        assert_ballot_option_transition_allowed(
            BallotOptionStatus.LOCKED, BallotOptionStatus.ACTIVE
        )


def test_vote_envelope_rejected_is_terminal() -> None:
    with pytest.raises(ForbiddenVoteEnvelopeTransitionError):
        assert_vote_envelope_transition_allowed(
            VoteEnvelopeStatus.REJECTED, VoteEnvelopeStatus.VALIDATED
        )


def test_vote_receipt_invalid_is_terminal() -> None:
    with pytest.raises(ForbiddenVoteReceiptTransitionError):
        assert_receipt_transition_allowed(
            VoteReceiptVerificationStatus.INVALID, VoteReceiptVerificationStatus.VERIFIED
        )


def test_tally_pending_cannot_go_directly_to_completed() -> None:
    with pytest.raises(ForbiddenTallyTransitionError):
        assert_tally_transition(TallyVerificationStatus.PENDING, TallyVerificationStatus.COMPLETED)


def test_delegation_revoked_is_terminal() -> None:
    with pytest.raises(ForbiddenDelegationTransitionError) as excinfo:
        assert_delegation_transition_allowed(DelegationStatus.REVOKED, DelegationStatus.ACTIVE)
    assert excinfo.value.reason_code == "VALIDATION_FORBIDDEN_TRANSITION"


# --- The two critical, spec-named cases, each its own explicit test -------


def test_ballot_closed_never_returns_to_open() -> None:
    """PACK-03 spec's own explicitly-named case: `Ballot.closed` never
    returns to `open`."""
    with pytest.raises(ForbiddenBallotTransitionError) as excinfo:
        assert_ballot_transition_allowed(BallotStatus.CLOSED, BallotStatus.OPEN)
    assert excinfo.value.reason_code == "VALIDATION_FORBIDDEN_TRANSITION"


def test_ballot_tallying_and_tallied_never_precede_closed() -> None:
    """PACK-03 spec's own explicitly-named case: `tallying`/`tallied`
    never precede `closed` - neither status is reachable from any status
    other than `closed`/`tallying` themselves."""
    for source in BallotStatus:
        if source in (BallotStatus.CLOSED,):
            continue
        with pytest.raises(ForbiddenBallotTransitionError):
            assert_ballot_transition_allowed(source, BallotStatus.TALLYING)
    for source in BallotStatus:
        if source in (BallotStatus.TALLYING,):
            continue
        with pytest.raises(ForbiddenBallotTransitionError):
            assert_ballot_transition_allowed(source, BallotStatus.TALLIED)


# =============================================================================
# PACK-05: at least one real forbidden pair from each of governance-service's
# four entities with a real state machine, mirroring the PACK-03 section
# above.
# =============================================================================


def test_role_assignment_revoked_is_terminal() -> None:
    with pytest.raises(ForbiddenRoleAssignmentTransitionError) as excinfo:
        assert_role_assignment_transition_allowed(
            RoleAssignmentStatus.REVOKED, RoleAssignmentStatus.ACTIVE
        )
    assert excinfo.value.reason_code == "VALIDATION_FORBIDDEN_TRANSITION"


def test_role_assignment_expired_cannot_go_directly_to_active() -> None:
    with pytest.raises(ForbiddenRoleAssignmentTransitionError):
        assert_role_assignment_transition_allowed(
            RoleAssignmentStatus.EXPIRED, RoleAssignmentStatus.ACTIVE
        )


def test_governance_policy_superseded_is_terminal() -> None:
    """PACK-05 spec's own explicitly-named case: a `GovernancePolicy`
    never returns to `draft`, and `superseded` has no outgoing
    transitions (canon 19b.2: at most one active version per policy_type,
    superseding is one-directional)."""
    with pytest.raises(ForbiddenGovernancePolicyTransitionError) as excinfo:
        assert_governance_policy_transition_allowed(
            GovernancePolicyStatus.SUPERSEDED, GovernancePolicyStatus.ACTIVE
        )
    assert excinfo.value.reason_code == "VALIDATION_FORBIDDEN_TRANSITION"


def test_governance_policy_draft_cannot_go_directly_to_superseded() -> None:
    with pytest.raises(ForbiddenGovernancePolicyTransitionError):
        assert_governance_policy_transition_allowed(
            GovernancePolicyStatus.DRAFT, GovernancePolicyStatus.SUPERSEDED
        )


def test_governance_decision_approved_is_terminal() -> None:
    """PACK-05 spec's own explicitly-named case: a `GovernanceDecision` is
    immutable once `approved` or `rejected` (canon 19b.3) - there is no
    stored `superseded` status at all; corrections are always a new row."""
    with pytest.raises(ForbiddenGovernanceDecisionTransitionError) as excinfo:
        assert_governance_decision_transition_allowed(
            GovernanceDecisionStatus.APPROVED, GovernanceDecisionStatus.REJECTED
        )
    assert excinfo.value.reason_code == "VALIDATION_FORBIDDEN_TRANSITION"


def test_governance_decision_rejected_is_terminal() -> None:
    with pytest.raises(ForbiddenGovernanceDecisionTransitionError):
        assert_governance_decision_transition_allowed(
            GovernanceDecisionStatus.REJECTED, GovernanceDecisionStatus.APPROVED
        )


def test_technical_challenge_upheld_is_terminal() -> None:
    with pytest.raises(ForbiddenTechnicalChallengeTransitionError) as excinfo:
        assert_technical_challenge_transition_allowed(
            TechnicalChallengeStatus.UPHELD, TechnicalChallengeStatus.UNDER_REVIEW
        )
    assert excinfo.value.reason_code == "VALIDATION_FORBIDDEN_TRANSITION"


def test_technical_challenge_submitted_cannot_go_directly_to_upheld() -> None:
    """PACK-05 spec's own explicitly-named case: adjudication (`upheld`/
    `rejected`) is only reachable through `under_review`, never directly
    from `submitted` (canon 19b.4: adjudication is always a side effect
    of deciding the linked `GovernanceDecision`)."""
    with pytest.raises(ForbiddenTechnicalChallengeTransitionError):
        assert_technical_challenge_transition_allowed(
            TechnicalChallengeStatus.SUBMITTED, TechnicalChallengeStatus.UPHELD
        )


# =============================================================================
# PACK-06: at least one real forbidden pair from each of ai-processing-
# service's two status planes (`processing_status`, `human_review_status`),
# mirroring the PACK-05 section above.
# =============================================================================


def test_processing_status_completed_is_terminal() -> None:
    """canon 19c.1: `completed`, `failed`, and `rejected_by_policy` are
    all terminal - no further processing_status transition is ever
    allowed once one is reached."""
    with pytest.raises(ForbiddenProcessingStatusTransitionError) as excinfo:
        assert_processing_status_transition_allowed(
            ProcessingStatus.COMPLETED, ProcessingStatus.PROCESSING
        )
    assert excinfo.value.reason_code == "VALIDATION_FORBIDDEN_TRANSITION"


def test_processing_status_requested_cannot_go_directly_to_processing() -> None:
    """`processing` is only reachable through `input_prepared` -
    redaction validation is never skippable (required scope item 6)."""
    with pytest.raises(ForbiddenProcessingStatusTransitionError):
        assert_processing_status_transition_allowed(
            ProcessingStatus.REQUESTED, ProcessingStatus.PROCESSING
        )


def test_human_review_status_approved_is_terminal() -> None:
    """A `human_review_status` outcome, once reached, is never further
    transitioned - a correction is always a brand-new
    `AIProcessingRecord` with `supersedes_ai_processing_record_id` set
    (canon 19c.2), never a further status change of this same row."""
    with pytest.raises(ForbiddenHumanReviewStatusTransitionError) as excinfo:
        assert_human_review_status_transition_allowed(
            HumanReviewStatus.APPROVED, HumanReviewStatus.REJECTED
        )
    assert excinfo.value.reason_code == "VALIDATION_FORBIDDEN_TRANSITION"


def test_human_review_status_not_required_cannot_go_to_approved() -> None:
    """required scope item 4: `not_required` is decided once, at
    creation, for non-consequential output only - it is never itself the
    starting point of a real review outcome transition."""
    with pytest.raises(ForbiddenHumanReviewStatusTransitionError):
        assert_human_review_status_transition_allowed(
            HumanReviewStatus.NOT_REQUIRED, HumanReviewStatus.APPROVED
        )


# =============================================================================
# PACK-07: at least one real forbidden pair from each of eligibility-service's
# and membership-service's state-machine entities (canon 19d.4-19d.11),
# mirroring the PACK-06 section above. `DigitalDecisionStatus` has no
# transition function at all - canon 19d.12: its `status` is set once, at
# construction, from the applicable `ProcessEligibilityPolicy` fields, and
# never transitions afterward (see `DigitalDecision`'s own docstring in
# `epd2_eligibility_service.domain`) - so there is no forbidden-transition
# test for it here.
# =============================================================================


def test_eligibility_critical_policy_superseded_is_terminal() -> None:
    """canon 19d.7's shared critical-policy status list (`Participant
    EligibilityPolicy`/`ProcessEligibilityPolicy`/
    `StepUpAuthenticationRequirement` all share this one status/transition
    table) - `superseded` is terminal, the same three-value shape
    `GovernancePolicyStatus` already established for governance-service."""
    with pytest.raises(ForbiddenEligibilityCriticalPolicyTransitionError) as excinfo:
        assert_eligibility_policy_transition_allowed(
            EligibilityCriticalPolicyStatus.SUPERSEDED, EligibilityCriticalPolicyStatus.ACTIVE
        )
    assert excinfo.value.reason_code == "VALIDATION_FORBIDDEN_TRANSITION"


def test_eligibility_critical_policy_draft_cannot_go_directly_to_superseded() -> None:
    with pytest.raises(ForbiddenEligibilityCriticalPolicyTransitionError):
        assert_eligibility_policy_transition_allowed(
            EligibilityCriticalPolicyStatus.DRAFT, EligibilityCriticalPolicyStatus.SUPERSEDED
        )


def test_assembly_decision_confirmed_cannot_return_to_pending() -> None:
    """canon 19d.12: an `AssemblyDecision.status` moves out of `pending`
    exactly once - none of `confirmed`/`rejected`/`returned_for_revision`
    is ever a source status again (canon 19d.12/INV-10: silence is never
    treated as approval, and neither is a completed decision ever
    reopened)."""
    with pytest.raises(ForbiddenAssemblyDecisionTransitionError) as excinfo:
        assert_assembly_decision_transition_allowed(
            AssemblyDecisionStatus.CONFIRMED, AssemblyDecisionStatus.PENDING
        )
    assert excinfo.value.reason_code == "VALIDATION_FORBIDDEN_TRANSITION"


def test_assembly_decision_returned_for_revision_cannot_go_directly_to_confirmed() -> None:
    with pytest.raises(ForbiddenAssemblyDecisionTransitionError):
        assert_assembly_decision_transition_allowed(
            AssemblyDecisionStatus.RETURNED_FOR_REVISION, AssemblyDecisionStatus.CONFIRMED
        )


def test_membership_critical_policy_superseded_is_terminal() -> None:
    """membership-service's own documented duplicate of
    `epd2_eligibility_service.domain.CriticalPolicyStatus`/
    `assert_critical_policy_transition_allowed` (module docstring: kept
    honest by `tests/repository/test_pack07_duplicated_logic_parity.py`) -
    same three-value shape, same forbidden pair."""
    with pytest.raises(ForbiddenMembershipCriticalPolicyTransitionError) as excinfo:
        assert_membership_policy_transition_allowed(
            MembershipCriticalPolicyStatus.SUPERSEDED, MembershipCriticalPolicyStatus.ACTIVE
        )
    assert excinfo.value.reason_code == "VALIDATION_FORBIDDEN_TRANSITION"


def test_membership_critical_policy_draft_cannot_go_directly_to_superseded() -> None:
    with pytest.raises(ForbiddenMembershipCriticalPolicyTransitionError):
        assert_membership_policy_transition_allowed(
            MembershipCriticalPolicyStatus.DRAFT, MembershipCriticalPolicyStatus.SUPERSEDED
        )


def test_membership_terminated_is_terminal() -> None:
    """canon 8.3: `terminated` is a dead end - no `membership_status`
    transition is ever allowed out of it."""
    with pytest.raises(ForbiddenMembershipTransitionError) as excinfo:
        assert_membership_transition_allowed(MembershipStatus.TERMINATED, MembershipStatus.ACTIVE)
    assert excinfo.value.reason_code == "VALIDATION_FORBIDDEN_TRANSITION"


def test_membership_application_pending_cannot_go_directly_to_activated() -> None:
    """canon 19d.9: a `MembershipApplication` must pass through
    `eligibility_review` -> `human_decision_pending` -> `approved` before
    it is ever `activated` - none of those stages is ever skippable."""
    with pytest.raises(ForbiddenMembershipApplicationTransitionError) as excinfo:
        assert_membership_application_transition_allowed(
            MembershipApplicationStatus.APPLICATION_PENDING,
            MembershipApplicationStatus.ACTIVATED,
        )
    assert excinfo.value.reason_code == "VALIDATION_FORBIDDEN_TRANSITION"


def test_affiliation_draft_cannot_go_directly_to_acknowledged() -> None:
    """canon 19d.10: an `AffiliationDeclaration` must pass through
    `submitted` -> `under_review` before it is ever `acknowledged`."""
    with pytest.raises(ForbiddenAffiliationTransitionError) as excinfo:
        assert_affiliation_transition_allowed(
            AffiliationStatus.DRAFT, AffiliationStatus.ACKNOWLEDGED
        )
    assert excinfo.value.reason_code == "VALIDATION_FORBIDDEN_TRANSITION"


def test_conflict_assessment_pending_cannot_go_directly_to_resolved_no_conflict() -> None:
    """canon 19d.11: a `ConflictAssessment` must pass through
    `under_review` before any `resolved_*` outcome is reached - `pending`
    itself never resolves a conflict directly."""
    with pytest.raises(ForbiddenConflictAssessmentTransitionError) as excinfo:
        assert_conflict_assessment_transition_allowed(
            ConflictAssessmentStatus.PENDING, ConflictAssessmentStatus.RESOLVED_NO_CONFLICT
        )
    assert excinfo.value.reason_code == "VALIDATION_FORBIDDEN_TRANSITION"


def test_membership_appeal_submitted_cannot_go_directly_to_upheld() -> None:
    """canon 14.3 (membership-service's own documented duplicate of
    moderation-service's `Appeal`, module docstring): an appeal must pass
    through `admissibility_review` -> `under_review` before any final
    outcome, the same shape moderation-service's own `Appeal` already
    establishes in the PACK-03 section above."""
    with pytest.raises(ForbiddenMembershipAppealTransitionError) as excinfo:
        assert_membership_appeal_transition_allowed(
            MembershipAppealStatus.SUBMITTED, MembershipAppealStatus.UPHELD
        )
    assert excinfo.value.reason_code == "VALIDATION_FORBIDDEN_TRANSITION"
