"""State transition tests (pack section 12.3): the full allowed/forbidden
transition matrix for Account, IdentityRecord, EligibilityDecision/
Snapshot (immutability), and ParticipationCredential. An unknown status is
always fail-closed (already covered per-entity in
`test_ct00_02_unknown_status.py`; this file is the transition-table
completeness check pack section 12.3 asks for)."""

from __future__ import annotations

import itertools
from enum import Enum
from typing import TypeVar

import pytest

from epd2_account_service.domain import ALLOWED_TRANSITIONS as ACCOUNT_ALLOWED
from epd2_account_service.domain import AccountStatus
from epd2_account_service.domain import assert_transition_allowed as assert_account
from epd2_account_service.exceptions import ForbiddenAccountTransitionError
from epd2_credential_service.domain import ALLOWED_TRANSITIONS as CREDENTIAL_ALLOWED
from epd2_credential_service.domain import CredentialStatus
from epd2_credential_service.domain import assert_transition_allowed as assert_credential
from epd2_credential_service.exceptions import ForbiddenCredentialTransitionError

# PACK-03 imports (see the "PACK-03: full allowed/forbidden transition-table
# coverage" section further down this file for what they're used for).
from epd2_delegation_service.domain import ALLOWED_TRANSITIONS as DELEGATION_ALLOWED
from epd2_delegation_service.domain import DelegationStatus
from epd2_delegation_service.domain import (
    assert_delegation_transition_allowed as assert_delegation,
)
from epd2_delegation_service.exceptions import ForbiddenDelegationTransitionError
from epd2_deliberation_service.domain import ALLOWED_DISCUSSION_TRANSITIONS as DISCUSSION_ALLOWED
from epd2_deliberation_service.domain import DiscussionStatus
from epd2_deliberation_service.domain import (
    assert_discussion_transition_allowed as assert_discussion,
)
from epd2_deliberation_service.exceptions import ForbiddenDiscussionTransitionError
from epd2_identity_service.domain import ALLOWED_TRANSITIONS as IDENTITY_ALLOWED
from epd2_identity_service.domain import VerificationStatus
from epd2_identity_service.domain import assert_transition_allowed as assert_identity
from epd2_identity_service.exceptions import ForbiddenVerificationTransitionError
from epd2_initiative_service.domain import ALLOWED_INITIATIVE_TRANSITIONS as INITIATIVE_ALLOWED
from epd2_initiative_service.domain import InitiativeStatus
from epd2_initiative_service.domain import (
    assert_initiative_transition_allowed as assert_initiative,
)
from epd2_initiative_service.exceptions import ForbiddenInitiativeTransitionError
from epd2_moderation_service.domain import CASE_ALLOWED_TRANSITIONS as CASE_ALLOWED
from epd2_moderation_service.domain import ModerationCaseStatus
from epd2_moderation_service.domain import assert_case_transition_allowed as assert_case
from epd2_moderation_service.exceptions import ForbiddenModerationCaseTransitionError
from epd2_tally_service.domain import ALLOWED_TRANSITIONS as TALLY_ALLOWED
from epd2_tally_service.domain import TallyVerificationStatus
from epd2_tally_service.domain import assert_transition_allowed as assert_tally
from epd2_tally_service.exceptions import ForbiddenTallyTransitionError
from epd2_voting_service.domain import ALLOWED_TRANSITIONS as BALLOT_ALLOWED
from epd2_voting_service.domain import BallotStatus
from epd2_voting_service.domain import assert_ballot_transition_allowed as assert_ballot
from epd2_voting_service.exceptions import ForbiddenBallotTransitionError

# PEP 695 generic syntax (`def f[T](...)`) is intentionally NOT used here:
# mypy can only *parse* that syntax when the interpreter running mypy itself
# is Python 3.12+ (see mypy docs, "PEP 695 generic syntax"). This repository's
# sandbox-local mypy tool binary is pinned to Python 3.11 (network-restricted;
# see docs/review/KNOWN_LIMITATIONS.md), so PEP 695 syntax would be a silent,
# unverifiable local blind spot even though CI's `uv sync`-provisioned
# Python 3.12 environment could parse it. The classic TypeVar form below is
# fully equivalent and verifiable under both Python 3.11 and 3.12.
StatusT = TypeVar("StatusT", bound=Enum)


def _all_forbidden_pairs(  # noqa: UP047 -- see comment above: PEP 695 syntax
    # is unparseable by this sandbox's Python-3.11-hosted mypy binary; the
    # classic TypeVar form is used deliberately so mypy can actually check
    # this file locally. CI (Python 3.12 via `uv sync`) supports either form.
    status_enum: type[StatusT],
    allowed: frozenset[tuple[StatusT, StatusT]],
) -> list[tuple[StatusT, StatusT]]:
    return [
        (current, target)
        for current, target in itertools.product(status_enum, status_enum)
        if (current, target) not in allowed
    ]


@pytest.mark.parametrize("current,target", _all_forbidden_pairs(AccountStatus, ACCOUNT_ALLOWED))
def test_every_non_allow_listed_account_transition_is_forbidden(
    current: AccountStatus, target: AccountStatus
) -> None:
    with pytest.raises(ForbiddenAccountTransitionError):
        assert_account(current, target)


@pytest.mark.parametrize("current,target", list(ACCOUNT_ALLOWED))
def test_every_allow_listed_account_transition_is_accepted(
    current: AccountStatus, target: AccountStatus
) -> None:
    assert_account(current, target)  # must not raise


@pytest.mark.parametrize(
    "current,target", _all_forbidden_pairs(VerificationStatus, IDENTITY_ALLOWED)
)
def test_every_non_allow_listed_identity_transition_is_forbidden(
    current: VerificationStatus, target: VerificationStatus
) -> None:
    with pytest.raises(ForbiddenVerificationTransitionError):
        assert_identity(current, target)


@pytest.mark.parametrize("current,target", list(IDENTITY_ALLOWED))
def test_every_allow_listed_identity_transition_is_accepted(
    current: VerificationStatus, target: VerificationStatus
) -> None:
    assert_identity(current, target)  # must not raise


@pytest.mark.parametrize(
    "current,target", _all_forbidden_pairs(CredentialStatus, CREDENTIAL_ALLOWED)
)
def test_every_non_allow_listed_credential_transition_is_forbidden(
    current: CredentialStatus, target: CredentialStatus
) -> None:
    with pytest.raises(ForbiddenCredentialTransitionError):
        assert_credential(current, target)


@pytest.mark.parametrize("current,target", list(CREDENTIAL_ALLOWED))
def test_every_allow_listed_credential_transition_is_accepted(
    current: CredentialStatus, target: CredentialStatus
) -> None:
    assert_credential(current, target)  # must not raise


def test_eligibility_decision_and_snapshot_are_immutable_dataclasses() -> None:
    """EligibilityDecision/EligibilitySnapshot have no `with_status`-style
    mutator at all (unlike Account/IdentityRecord/ParticipationCredential)
    - once created, the only way to get a "later" state is to create a new
    decision or a new (eligibility_rule_id, rule_version). Verified
    structurally: both are frozen dataclasses with no status-transition
    method."""
    from epd2_eligibility_service.domain import EligibilityDecision, EligibilitySnapshot

    assert EligibilityDecision.__dataclass_params__.frozen is True  # type: ignore[attr-defined]
    assert EligibilitySnapshot.__dataclass_params__.frozen is True  # type: ignore[attr-defined]
    assert not hasattr(EligibilityDecision, "with_status")
    assert not hasattr(EligibilitySnapshot, "with_status")


# =============================================================================
# PACK-03: full allowed/forbidden transition-table coverage (pack section
# 12.3's own "transition-table completeness check", extended to the six new
# services) for Ballot, Initiative, Delegation, ModerationCase, Tally, and
# Discussion, plus immutability checks for InitiativeVersion/
# ModerationDecision/ResultPublication (mirroring EligibilityDecision/
# EligibilitySnapshot's own immutability check above).
# =============================================================================


@pytest.mark.parametrize("current,target", _all_forbidden_pairs(BallotStatus, BALLOT_ALLOWED))
def test_every_non_allow_listed_ballot_transition_is_forbidden(
    current: BallotStatus, target: BallotStatus
) -> None:
    with pytest.raises(ForbiddenBallotTransitionError):
        assert_ballot(current, target)


@pytest.mark.parametrize("current,target", list(BALLOT_ALLOWED))
def test_every_allow_listed_ballot_transition_is_accepted(
    current: BallotStatus, target: BallotStatus
) -> None:
    assert_ballot(current, target)  # must not raise


@pytest.mark.parametrize(
    "current,target", _all_forbidden_pairs(InitiativeStatus, INITIATIVE_ALLOWED)
)
def test_every_non_allow_listed_initiative_transition_is_forbidden(
    current: InitiativeStatus, target: InitiativeStatus
) -> None:
    with pytest.raises(ForbiddenInitiativeTransitionError):
        assert_initiative(current, target)


@pytest.mark.parametrize("current,target", list(INITIATIVE_ALLOWED))
def test_every_allow_listed_initiative_transition_is_accepted(
    current: InitiativeStatus, target: InitiativeStatus
) -> None:
    assert_initiative(current, target)  # must not raise


@pytest.mark.parametrize(
    "current,target", _all_forbidden_pairs(DelegationStatus, DELEGATION_ALLOWED)
)
def test_every_non_allow_listed_delegation_transition_is_forbidden(
    current: DelegationStatus, target: DelegationStatus
) -> None:
    with pytest.raises(ForbiddenDelegationTransitionError):
        assert_delegation(current, target)


@pytest.mark.parametrize("current,target", list(DELEGATION_ALLOWED))
def test_every_allow_listed_delegation_transition_is_accepted(
    current: DelegationStatus, target: DelegationStatus
) -> None:
    assert_delegation(current, target)  # must not raise


@pytest.mark.parametrize("current,target", _all_forbidden_pairs(ModerationCaseStatus, CASE_ALLOWED))
def test_every_non_allow_listed_moderation_case_transition_is_forbidden(
    current: ModerationCaseStatus, target: ModerationCaseStatus
) -> None:
    with pytest.raises(ForbiddenModerationCaseTransitionError):
        assert_case(current, target)


@pytest.mark.parametrize("current,target", list(CASE_ALLOWED))
def test_every_allow_listed_moderation_case_transition_is_accepted(
    current: ModerationCaseStatus, target: ModerationCaseStatus
) -> None:
    assert_case(current, target)  # must not raise


@pytest.mark.parametrize(
    "current,target", _all_forbidden_pairs(TallyVerificationStatus, TALLY_ALLOWED)
)
def test_every_non_allow_listed_tally_transition_is_forbidden(
    current: TallyVerificationStatus, target: TallyVerificationStatus
) -> None:
    with pytest.raises(ForbiddenTallyTransitionError):
        assert_tally(current, target)


@pytest.mark.parametrize("current,target", list(TALLY_ALLOWED))
def test_every_allow_listed_tally_transition_is_accepted(
    current: TallyVerificationStatus, target: TallyVerificationStatus
) -> None:
    assert_tally(current, target)  # must not raise


@pytest.mark.parametrize(
    "current,target", _all_forbidden_pairs(DiscussionStatus, DISCUSSION_ALLOWED)
)
def test_every_non_allow_listed_discussion_transition_is_forbidden(
    current: DiscussionStatus, target: DiscussionStatus
) -> None:
    with pytest.raises(ForbiddenDiscussionTransitionError):
        assert_discussion(current, target)


@pytest.mark.parametrize("current,target", list(DISCUSSION_ALLOWED))
def test_every_allow_listed_discussion_transition_is_accepted(
    current: DiscussionStatus, target: DiscussionStatus
) -> None:
    assert_discussion(current, target)  # must not raise


def test_pack03_immutable_entities_have_no_status_transition_method() -> None:
    """`InitiativeVersion`, `ModerationDecision`, and `ResultPublication`
    are each immutable, frozen dataclasses with no `with_status`-style
    mutator - once created, there is no "later" state for any of them
    (mirroring `EligibilityDecision`/`EligibilitySnapshot`'s own
    immutability check above)."""
    from epd2_initiative_service.domain import InitiativeVersion
    from epd2_moderation_service.domain import ModerationDecision
    from epd2_tally_service.domain import ResultPublication

    assert InitiativeVersion.__dataclass_params__.frozen is True  # type: ignore[attr-defined]
    assert not hasattr(InitiativeVersion, "with_status")
    assert ModerationDecision.__dataclass_params__.frozen is True  # type: ignore[attr-defined]
    assert not hasattr(ModerationDecision, "with_status")
    assert ResultPublication.__dataclass_params__.frozen is True  # type: ignore[attr-defined]
    assert not hasattr(ResultPublication, "with_status")
