"""CT-00-03 Forbidden Transition (canon section 27): a forbidden status
transition is rejected, for every service with a status transition table."""

from __future__ import annotations

import pytest

from epd2_account_service.domain import AccountStatus
from epd2_account_service.domain import assert_transition_allowed as assert_account_transition
from epd2_account_service.exceptions import ForbiddenAccountTransitionError
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
