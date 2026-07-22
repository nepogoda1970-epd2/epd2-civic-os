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
from epd2_identity_service.domain import VerificationStatus
from epd2_identity_service.domain import assert_transition_allowed as assert_identity_transition
from epd2_identity_service.exceptions import ForbiddenVerificationTransitionError


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
