"""Tests for epd2_account_service.domain."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from epd2_account_service.domain import (
    Account,
    AccountStatus,
    assert_transition_allowed,
    parse_status,
)
from epd2_account_service.exceptions import (
    ForbiddenAccountTransitionError,
    UnknownAccountStatusError,
)


def _make_account(status: AccountStatus = AccountStatus.PENDING) -> Account:
    return Account(
        account_id=uuid4(),
        email_status="unverified",
        mfa_status="disabled",
        account_status=status,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        last_login_at=None,
        locale="en",
        terms_version="1.0",
        consent_status="granted",
    )


def test_parse_status_accepts_known_values() -> None:
    assert parse_status("active") == AccountStatus.ACTIVE


def test_parse_status_rejects_unknown_value() -> None:
    """CT-00-02: unknown status is never accepted."""
    with pytest.raises(UnknownAccountStatusError):
        parse_status("deleted_forever")


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (AccountStatus.PENDING, AccountStatus.ACTIVE),
        (AccountStatus.ACTIVE, AccountStatus.SUSPENDED),
        (AccountStatus.SUSPENDED, AccountStatus.ACTIVE),
        (AccountStatus.RECOVERY_PENDING, AccountStatus.CLOSED),
    ],
)
def test_allowed_transitions_succeed(current: AccountStatus, target: AccountStatus) -> None:
    assert_transition_allowed(current, target)  # does not raise


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (AccountStatus.CLOSED, AccountStatus.ACTIVE),
        (AccountStatus.CLOSED, AccountStatus.PENDING),
        (AccountStatus.PENDING, AccountStatus.SUSPENDED),
        (AccountStatus.SUSPENDED, AccountStatus.RESTRICTED),
    ],
)
def test_forbidden_transitions_are_rejected(current: AccountStatus, target: AccountStatus) -> None:
    """CT-00-03: forbidden transition is rejected. `closed` is terminal."""
    with pytest.raises(ForbiddenAccountTransitionError):
        assert_transition_allowed(current, target)


def test_with_status_returns_new_account_with_updated_status() -> None:
    account = _make_account(AccountStatus.ACTIVE)
    updated = account.with_status(AccountStatus.SUSPENDED)
    assert updated.account_status == AccountStatus.SUSPENDED
    assert updated.account_id == account.account_id
    assert account.account_status == AccountStatus.ACTIVE  # original is unchanged (frozen)


def test_with_status_rejects_forbidden_transition() -> None:
    account = _make_account(AccountStatus.CLOSED)
    with pytest.raises(ForbiddenAccountTransitionError):
        account.with_status(AccountStatus.ACTIVE)


def test_naive_created_at_is_rejected() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        Account(
            account_id=uuid4(),
            email_status="unverified",
            mfa_status="disabled",
            account_status=AccountStatus.PENDING,
            created_at=datetime(2026, 1, 1),
            last_login_at=None,
            locale="en",
            terms_version="1.0",
            consent_status="granted",
        )
