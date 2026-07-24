"""CT-00-02 Unknown Status (canon section 27): an unrecognized status
value is never accepted, for every service that owns a status enum."""

from __future__ import annotations

from collections.abc import Callable
from enum import Enum
from typing import Protocol, runtime_checkable

import pytest

from epd2_account_service.domain import parse_status as parse_account_status
from epd2_account_service.exceptions import UnknownAccountStatusError
from epd2_credential_service.domain import parse_status as parse_credential_status
from epd2_credential_service.exceptions import UnknownCredentialStatusError
from epd2_delegation_service.domain import parse_delegation_status
from epd2_delegation_service.exceptions import UnknownDelegationStatusError
from epd2_deliberation_service.domain import (
    parse_contribution_type,
    parse_discussion_status,
    parse_visibility_status,
)
from epd2_deliberation_service.exceptions import (
    UnknownContributionTypeError,
    UnknownContributionVisibilityStatusError,
    UnknownDiscussionStatusError,
)
from epd2_eligibility_service.domain import parse_decision_value
from epd2_eligibility_service.exceptions import UnknownEligibilityDecisionValueError
from epd2_governance_service.domain import (
    parse_governance_decision_status,
    parse_governance_policy_status,
    parse_role_assignment_status,
    parse_technical_challenge_status,
)
from epd2_governance_service.exceptions import (
    UnknownGovernanceDecisionStatusError,
    UnknownGovernancePolicyStatusError,
    UnknownRoleAssignmentStatusError,
    UnknownTechnicalChallengeStatusError,
)
from epd2_identity_service.domain import parse_status as parse_identity_status
from epd2_identity_service.exceptions import UnknownVerificationStatusError
from epd2_initiative_service.domain import (
    parse_amendment_status,
    parse_initiative_status,
    parse_source_verification_status,
    parse_support_status,
)
from epd2_initiative_service.exceptions import (
    UnknownAmendmentStatusError,
    UnknownInitiativeStatusError,
    UnknownSourceVerificationStatusError,
    UnknownSupportStatusError,
)
from epd2_moderation_service.domain import (
    parse_appeal_status,
    parse_case_status,
    parse_decision_type,
)
from epd2_moderation_service.exceptions import (
    UnknownAppealStatusError,
    UnknownModerationCaseStatusError,
    UnknownModerationDecisionTypeError,
)
from epd2_tally_service.domain import (
    parse_quorum_result,
    parse_threshold_result,
    parse_verification_status,
)
from epd2_tally_service.exceptions import (
    UnknownQuorumResultError,
    UnknownTallyVerificationStatusError,
    UnknownThresholdResultError,
)
from epd2_voting_service.domain import (
    parse_ballot_option_status,
    parse_ballot_status,
    parse_vote_envelope_status,
    parse_vote_receipt_verification_status,
)
from epd2_voting_service.exceptions import (
    UnknownBallotOptionStatusError,
    UnknownBallotStatusError,
    UnknownVoteEnvelopeStatusError,
    UnknownVoteReceiptStatusError,
)


def test_account_unknown_status_is_rejected() -> None:
    with pytest.raises(UnknownAccountStatusError) as excinfo:
        parse_account_status("not_a_real_status")
    assert excinfo.value.reason_code == "VALIDATION_UNKNOWN_STATUS"


def test_identity_unknown_status_is_rejected() -> None:
    with pytest.raises(UnknownVerificationStatusError) as excinfo:
        parse_identity_status("not_a_real_status")
    assert excinfo.value.reason_code == "VALIDATION_UNKNOWN_STATUS"


def test_eligibility_unknown_decision_value_is_rejected() -> None:
    with pytest.raises(UnknownEligibilityDecisionValueError) as excinfo:
        parse_decision_value("not_a_real_decision")
    assert excinfo.value.reason_code == "VALIDATION_UNKNOWN_STATUS"


def test_credential_unknown_status_is_rejected() -> None:
    with pytest.raises(UnknownCredentialStatusError) as excinfo:
        parse_credential_status("not_a_real_status")
    assert excinfo.value.reason_code == "VALIDATION_UNKNOWN_STATUS"


# =============================================================================
# PACK-03: one parametrized test covering all 18 PACK-03 status/value enums'
# own `parse_*` functions (one parametrized test is preferred here over 18
# near-duplicate test functions - this file did not previously use
# `pytest.mark.parametrize` for PACK-02's four enums, which are left as
# individual functions above, unchanged).
# =============================================================================


@runtime_checkable
class _ReasonCodedError(Protocol):
    """Structural protocol used to narrow a caught, generically-typed
    exception before accessing its `reason_code` attribute.

    `expected_exception` below is intentionally typed as the generic
    `type[Exception]` - the 18 `Unknown*Error` classes in
    `_PACK03_PARSE_CASES` span six different services' `exceptions`
    modules and share no common concrete base beyond `ValueError`, so a
    single parametrized test cannot name one concrete exception type.
    Each of those classes does declare a class-level `reason_code: str`
    attribute (every service's `exceptions.py` module docstring says so),
    but a plain `Exception` does not, so `excinfo.value.reason_code`
    fails mypy's `attr-defined` check once real pytest type stubs are
    installed (this is invisible in a sandbox where `pytest` falls back
    to `ignore_missing_imports`, per this project's mypy config, and
    surfaced only on external GitHub Actions verification with pytest
    genuinely installed). `isinstance(error, _ReasonCodedError)` performs
    a real runtime check for the attribute's presence
    (`@runtime_checkable` protocols check `hasattr` for every declared
    member, not just methods) and narrows `error`'s static type for the
    following line - not a blanket `# type: ignore`, and no weakening of
    the assertion this test makes."""

    reason_code: str


#: (parse_fn, expected_exception_type) for all 18 PACK-03 enums across the
#: six new services: initiative-service (4), deliberation-service (3),
#: moderation-service (3), voting-service (4), tally-service (3),
#: delegation-service (1).
_PACK03_PARSE_CASES = (
    (parse_initiative_status, UnknownInitiativeStatusError),
    (parse_support_status, UnknownSupportStatusError),
    (parse_amendment_status, UnknownAmendmentStatusError),
    (parse_source_verification_status, UnknownSourceVerificationStatusError),
    (parse_discussion_status, UnknownDiscussionStatusError),
    (parse_contribution_type, UnknownContributionTypeError),
    (parse_visibility_status, UnknownContributionVisibilityStatusError),
    (parse_case_status, UnknownModerationCaseStatusError),
    (parse_decision_type, UnknownModerationDecisionTypeError),
    (parse_appeal_status, UnknownAppealStatusError),
    (parse_ballot_status, UnknownBallotStatusError),
    (parse_ballot_option_status, UnknownBallotOptionStatusError),
    (parse_vote_envelope_status, UnknownVoteEnvelopeStatusError),
    (parse_vote_receipt_verification_status, UnknownVoteReceiptStatusError),
    (parse_verification_status, UnknownTallyVerificationStatusError),
    (parse_quorum_result, UnknownQuorumResultError),
    (parse_threshold_result, UnknownThresholdResultError),
    (parse_delegation_status, UnknownDelegationStatusError),
)


@pytest.mark.parametrize(
    "parse_fn,expected_exception",
    _PACK03_PARSE_CASES,
    ids=[fn.__name__ for fn, _ in _PACK03_PARSE_CASES],
)
def test_pack03_unknown_enum_value_is_rejected(
    parse_fn: Callable[[str], Enum], expected_exception: type[Exception]
) -> None:
    with pytest.raises(expected_exception) as excinfo:
        parse_fn("not_a_real_value")
    error = excinfo.value
    assert isinstance(error, _ReasonCodedError)
    assert error.reason_code == "VALIDATION_UNKNOWN_STATUS"


# =============================================================================
# PACK-05: the one PACK-05 service's (governance-service) four status enums'
# own `parse_*` functions, mirroring the PACK-03 parametrized block above.
# =============================================================================

#: (parse_fn, expected_exception_type) for all 4 PACK-05 status enums:
#: RoleAssignment, GovernancePolicy, GovernanceDecision, TechnicalChallenge.
_PACK05_PARSE_CASES = (
    (parse_role_assignment_status, UnknownRoleAssignmentStatusError),
    (parse_governance_policy_status, UnknownGovernancePolicyStatusError),
    (parse_governance_decision_status, UnknownGovernanceDecisionStatusError),
    (parse_technical_challenge_status, UnknownTechnicalChallengeStatusError),
)


@pytest.mark.parametrize(
    "parse_fn,expected_exception",
    _PACK05_PARSE_CASES,
    ids=[fn.__name__ for fn, _ in _PACK05_PARSE_CASES],
)
def test_pack05_unknown_enum_value_is_rejected(
    parse_fn: Callable[[str], Enum], expected_exception: type[Exception]
) -> None:
    with pytest.raises(expected_exception) as excinfo:
        parse_fn("not_a_real_value")
    error = excinfo.value
    assert isinstance(error, _ReasonCodedError)
    assert error.reason_code == "VALIDATION_UNKNOWN_STATUS"
