"""Multi-factor authentication: factors, their lifecycle, and the one
factor class that is deliberately absent.

`MfaFactorClass` has no `sms_otp` member and none may be added. SMS OTP
is **not a login method and not a step-up factor**, and it carries no
assurance level at all (OD-P14-09): an attacker who takes over a phone
number gains a verified channel and no authentication. It appears in this
package only as `phone_channel_verification` in `contacts.py` and as a
low-weight signal in `recovery.py`, and `refuse_sms_otp_as_factor()`
below exists so that a caller who reaches for it gets a refusal with its
own reason code rather than a `KeyError`.

Email OTP **is** a class, because verifying an email channel is a real
operation - but it is `low` assurance and never a high-assurance factor.

Recovery codes are a factor class of their own: single-use, issued as a
set, shown once, revoked and reissued as a whole set. Consuming one is
recorded so the same code can never be presented twice.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from epd2_identity_service.exceptions import (
    ForbiddenMfaFactorTransitionError,
    MfaFactorAlreadyEnrolledError,
    MfaFactorNotConfirmedError,
    MfaFactorNotEnrolledError,
    MfaFactorRevokedError,
    MfaFailedError,
    RecoveryCodeAlreadyUsedError,
    RecoveryCodeInvalidError,
    RecoveryCodeSetExhaustedError,
    SmsOtpNotAnAuthenticationFactorError,
    UnknownMfaFactorClassError,
    UnknownMfaFactorStatusError,
)
from epd2_identity_service.identifiers import AccountId, require_timezone
from epd2_identity_service.secret_storage import (
    HashedSecret,
    SecureRandom,
    TotpVerifier,
    hash_token,
)

#: How many codes a recovery set contains. A policy value, small enough
#: that a person can plausibly store them and large enough that ordinary
#: use does not exhaust the set between reissues.
RECOVERY_CODE_SET_SIZE = 10


class MfaFactorClass(StrEnum):
    """The factor classes this system recognises.

    **`SMS_OTP` is deliberately absent.** See the module docstring; the
    absence is the decision, not an omission.
    """

    TOTP = "totp"
    SECURITY_KEY = "security_key"
    RECOVERY_CODE = "recovery_code"
    EMAIL_OTP = "email_otp"
    PROVIDER_MFA = "provider_mfa"


def parse_factor_class(value: str) -> MfaFactorClass:
    """Fail-closed parse. `"sms_otp"` reaches the SMS-specific refusal
    rather than a generic unknown-value error, because a caller who sent
    it needs to be told *why* it does not exist, not that it was
    misspelled."""
    if value == "sms_otp":
        refuse_sms_otp_as_factor("enrollment")
    try:
        return MfaFactorClass(value)
    except ValueError as exc:
        raise UnknownMfaFactorClassError(f"unknown MFA factor class: {value!r}") from exc


def refuse_sms_otp_as_factor(context: str) -> None:
    """OD-P14-09, as a call site. Always raises."""
    raise SmsOtpNotAnAuthenticationFactorError(
        f"SMS OTP is not an authentication or step-up factor ({context}); it verifies a "
        "phone channel and contributes a low-weight recovery signal, and it carries no "
        "assurance level at all"
    )


class MfaFactorStatus(StrEnum):
    ENROLLED_UNCONFIRMED = "enrolled_unconfirmed"
    ACTIVE = "active"
    REVOKED = "revoked"


def parse_factor_status(value: str) -> MfaFactorStatus:
    try:
        return MfaFactorStatus(value)
    except ValueError as exc:
        raise UnknownMfaFactorStatusError(f"unknown MFA factor status: {value!r}") from exc


_ALLOWED_FACTOR_TRANSITIONS: frozenset[tuple[MfaFactorStatus, MfaFactorStatus]] = frozenset(
    {
        (MfaFactorStatus.ENROLLED_UNCONFIRMED, MfaFactorStatus.ACTIVE),
        (MfaFactorStatus.ENROLLED_UNCONFIRMED, MfaFactorStatus.REVOKED),
        (MfaFactorStatus.ACTIVE, MfaFactorStatus.REVOKED),
    }
)


@dataclass(frozen=True, slots=True)
class MfaFactor:
    """One enrolled factor.

    `secret_reference` is an opaque handle into the deployment's secret
    store - never the TOTP seed itself. A serialization of this dataclass
    carries nothing an attacker can use.
    """

    factor_id: UUID
    account_id: AccountId
    factor_class: MfaFactorClass
    status: MfaFactorStatus
    secret_reference: str | None
    enrolled_at: datetime
    confirmed_at: datetime | None
    last_used_at: datetime | None
    revoked_at: datetime | None
    revocation_reason_code: str | None

    def __post_init__(self) -> None:
        require_timezone(self.enrolled_at, "enrolled_at")
        for name in ("confirmed_at", "last_used_at", "revoked_at"):
            moment = getattr(self, name)
            if moment is not None:
                require_timezone(moment, name)

    def assert_usable(self) -> None:
        if self.status is MfaFactorStatus.REVOKED:
            raise MfaFactorRevokedError("the factor has been revoked")
        if self.status is MfaFactorStatus.ENROLLED_UNCONFIRMED:
            raise MfaFactorNotConfirmedError(
                "the factor was enrolled but never confirmed; an unconfirmed factor is a claim"
            )

    def transitioned(self, target: MfaFactorStatus, *, at: datetime) -> MfaFactor:
        if (self.status, target) not in _ALLOWED_FACTOR_TRANSITIONS:
            raise ForbiddenMfaFactorTransitionError(
                f"MFA factor transition {self.status.value!r} -> {target.value!r} is not allowed"
            )
        moment = require_timezone(at, "at")
        return replace(
            self,
            status=target,
            confirmed_at=moment if target is MfaFactorStatus.ACTIVE else self.confirmed_at,
            revoked_at=moment if target is MfaFactorStatus.REVOKED else self.revoked_at,
        )


def enroll_factor(
    *,
    factor_id: UUID,
    account_id: AccountId,
    factor_class: MfaFactorClass,
    secret_reference: str | None,
    enrolled_at: datetime,
    existing: tuple[MfaFactor, ...],
) -> MfaFactor:
    for other in existing:
        if other.factor_class is factor_class and other.status is not MfaFactorStatus.REVOKED:
            raise MfaFactorAlreadyEnrolledError(
                f"a {factor_class.value} factor is already enrolled on this account"
            )
    return MfaFactor(
        factor_id=factor_id,
        account_id=account_id,
        factor_class=factor_class,
        status=MfaFactorStatus.ENROLLED_UNCONFIRMED,
        secret_reference=secret_reference,
        enrolled_at=require_timezone(enrolled_at, "enrolled_at"),
        confirmed_at=None,
        last_used_at=None,
        revoked_at=None,
        revocation_reason_code=None,
    )


def confirm_totp_factor(
    factor: MfaFactor,
    *,
    secret: str,
    presented_code: str,
    unix_time: int,
    verifier: TotpVerifier,
    confirmed_at: datetime,
) -> MfaFactor:
    """Confirmation proves the enrolling device actually holds the seed.

    Without it an "enrolled" factor is a claim, and an account can end up
    relying for its second factor on an authenticator nobody ever
    successfully used.
    """
    if factor.factor_class is not MfaFactorClass.TOTP:
        raise MfaFactorNotEnrolledError("this factor is not a TOTP factor")
    if not verifier.verify(secret, presented_code, unix_time=unix_time):
        raise MfaFailedError("the presented code did not verify")
    return factor.transitioned(MfaFactorStatus.ACTIVE, at=confirmed_at)


def verify_totp_factor(
    factor: MfaFactor,
    *,
    secret: str,
    presented_code: str,
    unix_time: int,
    verifier: TotpVerifier,
    used_at: datetime,
) -> MfaFactor:
    factor.assert_usable()
    if not verifier.verify(secret, presented_code, unix_time=unix_time):
        raise MfaFailedError("the presented code did not verify")
    return replace(factor, last_used_at=require_timezone(used_at, "used_at"))


def revoke_factor(factor: MfaFactor, *, reason_code: str, revoked_at: datetime) -> MfaFactor:
    revoked = factor.transitioned(MfaFactorStatus.REVOKED, at=revoked_at)
    return replace(revoked, revocation_reason_code=reason_code)


def active_factors(factors: tuple[MfaFactor, ...]) -> tuple[MfaFactor, ...]:
    return tuple(factor for factor in factors if factor.status is MfaFactorStatus.ACTIVE)


def assert_factor_enrolled(
    factors: tuple[MfaFactor, ...], required_class: MfaFactorClass
) -> MfaFactor:
    for factor in active_factors(factors):
        if factor.factor_class is required_class:
            return factor
    raise MfaFactorNotEnrolledError(
        f"no active {required_class.value} factor is enrolled on this account"
    )


@dataclass(frozen=True, slots=True)
class RecoveryCodeSet:
    """A set of single-use recovery codes.

    Only digests are stored. The plaintext codes exist once, in the
    response that displays them, and are never recoverable afterwards -
    which is why the form requires an explicit "I have stored these"
    declaration before the set is considered issued.
    """

    set_id: UUID
    account_id: AccountId
    code_digests: tuple[HashedSecret, ...]
    consumed_digests: frozenset[str]
    issued_at: datetime
    revoked_at: datetime | None = None
    revocation_reason_code: str | None = None

    def __post_init__(self) -> None:
        require_timezone(self.issued_at, "issued_at")
        if self.revoked_at is not None:
            require_timezone(self.revoked_at, "revoked_at")
        if not self.code_digests:
            raise ValueError("a recovery code set contains at least one code")

    def remaining(self) -> int:
        return len(self.code_digests) - len(self.consumed_digests)

    def is_active(self) -> bool:
        return self.revoked_at is None and self.remaining() > 0

    def consume(self, presented_code: str) -> RecoveryCodeSet:
        """Three distinct refusals: not ours, already spent, none left.

        Collapsing "already used" into "invalid" would hide a replay - the
        one thing a single-use credential exists to make visible.
        """
        if self.revoked_at is not None:
            raise RecoveryCodeInvalidError("this recovery code set has been revoked")
        digest = hash_token(presented_code)
        known = {stored.digest for stored in self.code_digests}
        if digest.digest not in known:
            raise RecoveryCodeInvalidError("the presented code is not part of this account's set")
        if digest.digest in self.consumed_digests:
            raise RecoveryCodeAlreadyUsedError("this recovery code has already been used")
        if self.remaining() <= 0:
            raise RecoveryCodeSetExhaustedError("every code in this set has been consumed")
        return replace(self, consumed_digests=self.consumed_digests | {digest.digest})

    def revoked(self, *, reason_code: str, revoked_at: datetime) -> RecoveryCodeSet:
        return replace(
            self,
            revoked_at=require_timezone(revoked_at, "revoked_at"),
            revocation_reason_code=reason_code,
        )


def issue_recovery_code_set(
    *,
    set_id: UUID,
    account_id: AccountId,
    issued_at: datetime,
    random: SecureRandom,
    count: int = RECOVERY_CODE_SET_SIZE,
) -> tuple[RecoveryCodeSet, tuple[str, ...]]:
    """Issue a set; return the record **and** the plaintext codes.

    The plaintext tuple is the caller's single opportunity to display
    them. It is deliberately a separate return value rather than a field
    on the record, so no persistence path can accidentally store it.
    """
    codes = tuple(random.token(16) for _ in range(count))
    record = RecoveryCodeSet(
        set_id=set_id,
        account_id=account_id,
        code_digests=tuple(hash_token(code) for code in codes),
        consumed_digests=frozenset(),
        issued_at=require_timezone(issued_at, "issued_at"),
    )
    return record, codes
