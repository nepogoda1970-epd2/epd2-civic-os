"""Controlled password fallback (specification §5.2, OD-P14-03).

Excluding passwords entirely would have been the cleaner security story
and the worse inclusion outcome: it makes participation depend on owning
a passkey-capable device, which is not a condition a party may place on
its members. So the fallback exists, and it is fenced by rules this
module enforces rather than documents:

1. **Passkeys remain preferred** and are offered first everywhere.
2. **No new password-only account may be created.**
3. **Password login always requires MFA** - single-factor password
   authentication does not exist in this system.
4. **A password never authorizes a consequential action alone.** Its
   ceiling is `substantial`, so it cannot satisfy a `high` action.
5. **Password login can be disabled by governed configuration**, globally,
   per organizational scope or per account.
6. **No security questions**, ever - for candidates and office-holders the
   answers are campaign material.
7. Storage is a modern memory-hard hash through the `PasswordHasher`
   port. **No hashing algorithm is implemented here.**

Rule 4 is the one worth stating twice, because it is the one an
implementer is most tempted to soften: two `substantial` paths do not add
up to a `high` one.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from uuid import UUID

from epd2_identity_service.domain import AuthenticationAssuranceLevel
from epd2_identity_service.exceptions import (
    AuthenticationThrottledError,
    BreachedPasswordRefusedError,
    InvalidCredentialError,
    MfaRequiredError,
    PasswordLoginDisabledError,
    PasswordOnlyAccountRefusedError,
    PasswordPolicyNotMetError,
    SecurityQuestionRefusedError,
)
from epd2_identity_service.identifiers import AccountId, require_timezone
from epd2_identity_service.secret_storage import (
    BreachedPasswordChecker,
    PasswordHasher,
)

#: The ceiling password authentication can ever reach, whatever it is
#: combined with (specification §5.2, authentication method matrix §3.5).
PASSWORD_ASSURANCE_CEILING = AuthenticationAssuranceLevel.SUBSTANTIAL

#: Minimum length. Deliberately the only length rule: composition rules
#: ("one digit, one symbol") measurably produce weaker passwords, and the
#: breached-password boundary does the work a composition rule pretends
#: to.
MINIMUM_PASSWORD_LENGTH = 12
MAXIMUM_PASSWORD_LENGTH = 256


class PasswordLoginScope(StrEnum):
    """The three levels at which password login may be disabled."""

    GLOBAL = "global"
    ORGANIZATIONAL_SCOPE = "organizational_scope"
    ACCOUNT = "account"


@dataclass(frozen=True, slots=True)
class PasswordCredentialReference:
    """The stored reference to a password credential.

    There is no `password` field and no `plaintext` field. `stored_hash`
    is the opaque string the bound `PasswordHasher` produced and only it
    can interpret; `algorithm_label` is recorded so a rehash-on-login
    policy has something to act on and an operator can tell which
    algorithm a given record predates.
    """

    credential_id: UUID
    account_id: AccountId
    stored_hash: str
    algorithm_label: str
    created_at: datetime
    last_verified_at: datetime | None = None

    def __post_init__(self) -> None:
        require_timezone(self.created_at, "created_at")
        if self.last_verified_at is not None:
            require_timezone(self.last_verified_at, "last_verified_at")
        if not self.stored_hash or not self.algorithm_label:
            raise ValueError("a password credential reference carries a hash and its algorithm")


@dataclass(frozen=True, slots=True)
class PasswordLoginPolicy:
    """Whether password login is available here, and for whom.

    `disabled_scopes` and `disabled_accounts` are separate from the
    global switch so an organization can require passkeys of its own
    members without the platform deciding for everyone.
    """

    globally_enabled: bool
    disabled_organizational_units: frozenset[UUID] = frozenset()
    disabled_accounts: frozenset[AccountId] = frozenset()

    def assert_available(self, *, account_id: AccountId, organizational_unit_id: UUID) -> None:
        if not self.globally_enabled:
            raise PasswordLoginDisabledError("password login is disabled by governed configuration")
        if organizational_unit_id in self.disabled_organizational_units:
            raise PasswordLoginDisabledError(
                "password login is disabled for this organizational scope"
            )
        if account_id in self.disabled_accounts:
            raise PasswordLoginDisabledError("password login is disabled for this account")


@dataclass(frozen=True, slots=True)
class AuthenticationThrottleState:
    """Per-subject failure counting.

    Counted per (account, attempt source) rather than per account alone,
    so an attacker cannot lock a member out of their own account by
    failing against it from elsewhere - denial of service disguised as a
    security control.
    """

    failures: int
    first_failure_at: datetime | None
    throttled_until: datetime | None

    def assert_not_throttled(self, now: datetime) -> None:
        if self.throttled_until is None:
            return
        if require_timezone(now, "now") < self.throttled_until:
            raise AuthenticationThrottledError(
                "authentication is throttled after repeated failures"
            )

    def after_failure(
        self, *, now: datetime, threshold: int, penalty: timedelta
    ) -> AuthenticationThrottleState:
        moment = require_timezone(now, "now")
        failures = self.failures + 1
        return AuthenticationThrottleState(
            failures=failures,
            first_failure_at=self.first_failure_at or moment,
            throttled_until=(moment + penalty) if failures >= threshold else self.throttled_until,
        )

    def cleared(self) -> AuthenticationThrottleState:
        return AuthenticationThrottleState(failures=0, first_failure_at=None, throttled_until=None)


def initial_throttle_state() -> AuthenticationThrottleState:
    return AuthenticationThrottleState(failures=0, first_failure_at=None, throttled_until=None)


def refuse_security_question(prompt: str) -> None:
    """Rule 6, as a call site.

    Any code path that finds itself about to store or evaluate a
    knowledge-based answer calls this. It always raises. The function
    exists so that "no security questions" is something the code does
    rather than something a document says.
    """
    raise SecurityQuestionRefusedError(
        f"security questions are prohibited; refused prompt {prompt[:32]!r}"
    )


def assert_password_policy(password: str) -> None:
    if not MINIMUM_PASSWORD_LENGTH <= len(password) <= MAXIMUM_PASSWORD_LENGTH:
        raise PasswordPolicyNotMetError(
            "the proposed password does not satisfy the governed length policy"
        )
    if password.strip() != password:
        raise PasswordPolicyNotMetError("the proposed password has leading or trailing whitespace")


def enroll_password(
    *,
    credential_id: UUID,
    account_id: AccountId,
    password: str,
    created_at: datetime,
    hasher: PasswordHasher,
    breach_checker: BreachedPasswordChecker,
    account_has_other_credential: bool,
) -> PasswordCredentialReference:
    """Rule 2 lives here.

    `account_has_other_credential=False` means this password would be the
    account's only way in - a new password-only account - and that is
    refused. A password is a fallback for someone who already has a way
    in, not a default path for a new account.
    """
    if not account_has_other_credential:
        raise PasswordOnlyAccountRefusedError(
            "a new password-only account may not be created; enroll a passkey first"
        )
    assert_password_policy(password)
    if breach_checker.is_breached(password):
        raise BreachedPasswordRefusedError("the proposed password is known-compromised")
    return PasswordCredentialReference(
        credential_id=credential_id,
        account_id=account_id,
        stored_hash=hasher.hash(password),
        algorithm_label=hasher.algorithm_label,
        created_at=require_timezone(created_at, "created_at"),
    )


def verify_password(
    reference: PasswordCredentialReference,
    *,
    password: str,
    hasher: PasswordHasher,
    mfa_satisfied: bool,
) -> None:
    """Rule 3 lives here, and it is checked **after** the password.

    Checking MFA first would make a wrong password and a missing factor
    distinguishable by which error came back, which is an oracle. Both
    orderings refuse; this one refuses without telling the caller which
    half was wrong when the password itself was wrong.
    """
    if not hasher.verify(password, reference.stored_hash):
        raise InvalidCredentialError("the presented credential did not verify")
    if not mfa_satisfied:
        raise MfaRequiredError(
            "password authentication always requires a second factor in this system"
        )


def password_assurance_ceiling() -> AuthenticationAssuranceLevel:
    """Rule 4, as a value other modules read rather than restate."""
    return PASSWORD_ASSURANCE_CEILING


def assert_password_cannot_authorize(required: AuthenticationAssuranceLevel) -> None:
    """Refuse where a password-derived session is asked to carry a `high`
    action. Called by the assurance evaluator, so the ceiling is applied
    at the decision point rather than trusted at the login point."""
    if required is AuthenticationAssuranceLevel.HIGH:
        raise InvalidCredentialError(
            "password authentication never reaches 'high'; a consequential action "
            "requires a phishing-resistant credential"
        )
