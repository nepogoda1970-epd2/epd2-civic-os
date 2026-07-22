"""`Account`, per `docs/canonical/TZ-00-domain-event-canon.md`, section 7.2.

No personal data: only technical account state. Identity attributes
(name, date of birth, email address, ...) belong to `IdentityRecord`
(Identity Service), never here (INV-01).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from epd2_account_service.exceptions import (
    ForbiddenAccountTransitionError,
    UnknownAccountStatusError,
)


class AccountStatus(StrEnum):
    """Canon section 7.2's exact status list."""

    PENDING = "pending"
    ACTIVE = "active"
    RESTRICTED = "restricted"
    SUSPENDED = "suspended"
    RECOVERY_PENDING = "recovery_pending"
    CLOSED = "closed"


# Which transitions are permitted. `closed` is terminal (no outgoing
# transitions) per the conservative reading documented in README.md /
# docs/review/OPEN_QUESTIONS.md.
ALLOWED_TRANSITIONS: frozenset[tuple[AccountStatus, AccountStatus]] = frozenset(
    {
        (AccountStatus.PENDING, AccountStatus.ACTIVE),
        (AccountStatus.PENDING, AccountStatus.CLOSED),
        (AccountStatus.ACTIVE, AccountStatus.RESTRICTED),
        (AccountStatus.ACTIVE, AccountStatus.SUSPENDED),
        (AccountStatus.ACTIVE, AccountStatus.RECOVERY_PENDING),
        (AccountStatus.ACTIVE, AccountStatus.CLOSED),
        (AccountStatus.RESTRICTED, AccountStatus.ACTIVE),
        (AccountStatus.RESTRICTED, AccountStatus.SUSPENDED),
        (AccountStatus.RESTRICTED, AccountStatus.CLOSED),
        (AccountStatus.SUSPENDED, AccountStatus.ACTIVE),
        (AccountStatus.SUSPENDED, AccountStatus.CLOSED),
        (AccountStatus.RECOVERY_PENDING, AccountStatus.ACTIVE),
        (AccountStatus.RECOVERY_PENDING, AccountStatus.CLOSED),
    }
)

# The canonical event name (canon section 20.1) for a transition, if any.
# A transition present in ALLOWED_TRANSITIONS but absent here emits no
# event - it is not one of the canonically-named account events (ADR-002).
CANONICAL_EVENT_FOR_TRANSITION: dict[tuple[AccountStatus, AccountStatus], str] = {
    (AccountStatus.ACTIVE, AccountStatus.RESTRICTED): "account.restricted",
    (AccountStatus.ACTIVE, AccountStatus.SUSPENDED): "account.suspended",
    (AccountStatus.RESTRICTED, AccountStatus.SUSPENDED): "account.suspended",
    (AccountStatus.PENDING, AccountStatus.CLOSED): "account.closed",
    (AccountStatus.ACTIVE, AccountStatus.CLOSED): "account.closed",
    (AccountStatus.RESTRICTED, AccountStatus.CLOSED): "account.closed",
    (AccountStatus.SUSPENDED, AccountStatus.CLOSED): "account.closed",
    (AccountStatus.RECOVERY_PENDING, AccountStatus.CLOSED): "account.closed",
}


def parse_status(value: str) -> AccountStatus:
    """Parse `value` into an `AccountStatus`, raising
    `UnknownAccountStatusError` (fail-closed, INV-10) if it is not one of
    the canonical status values - never guesses or defaults.
    """
    try:
        return AccountStatus(value)
    except ValueError as exc:
        raise UnknownAccountStatusError(f"unknown account status: {value!r}") from exc


def assert_transition_allowed(current: AccountStatus, target: AccountStatus) -> None:
    if (current, target) not in ALLOWED_TRANSITIONS:
        raise ForbiddenAccountTransitionError(
            f"transition {current.value!r} -> {target.value!r} is not allowed"
        )


@dataclass(frozen=True, slots=True)
class Account:
    """Canon section 7.2 fields exactly - no additional fields, so this
    entity structurally cannot carry identity data.
    """

    account_id: UUID
    email_status: str
    mfa_status: str
    account_status: AccountStatus
    created_at: datetime
    last_login_at: datetime | None
    locale: str
    terms_version: str
    consent_status: str

    def __post_init__(self) -> None:
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")
        if self.last_login_at is not None and self.last_login_at.tzinfo is None:
            raise ValueError("last_login_at must be timezone-aware")

    def with_status(self, new_status: AccountStatus) -> Account:
        assert_transition_allowed(self.account_status, new_status)
        return Account(
            account_id=self.account_id,
            email_status=self.email_status,
            mfa_status=self.mfa_status,
            account_status=new_status,
            created_at=self.created_at,
            last_login_at=self.last_login_at,
            locale=self.locale,
            terms_version=self.terms_version,
            consent_status=self.consent_status,
        )
