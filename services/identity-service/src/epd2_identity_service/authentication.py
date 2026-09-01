"""Authentication attempts, challenges, risk signals and the decision.

The module where account enumeration is either prevented or created. The
rule enforced here is uniformity: **a public authentication response is
the same shape whether or not the account exists.** `AuthenticationOutcome`
carries an internal reason code for the audit record and a separate
`public_reason_code` for the response, and the mapping between them
collapses every "this account does not exist" variant into the same
`CREDENTIAL_INVALID` a wrong secret produces.

Risk signals are named individually and weighted. **Impossible travel is
a weak signal only** and can never be the sole basis for a denial - the
session security matrix says so, and `RiskAssessment` refuses to reach a
denying classification from weak signals alone.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from enum import StrEnum
from uuid import UUID

from epd2_identity_service.assurance import (
    PERMITS_LOGIN,
    AuthenticationMethod,
    RiskState,
)
from epd2_identity_service.exceptions import (
    ChallengeExpiredError,
    InvalidCredentialError,
    NonceAlreadyUsedError,
    RateLimitExceededError,
    UnknownAuthenticationMethodError,
    UnknownRiskSignalCategoryError,
)
from epd2_identity_service.identifiers import (
    ScopedIdentityReference,
    require_timezone,
)
from epd2_identity_service.secret_storage import SecureRandom
from epd2_identity_service.workspaces import WorkspaceId

#: The single public refusal for every failed authentication, whatever
#: the internal cause. An attacker learns "that did not work" and nothing
#: about whether the account exists, whether it is locked, or which half
#: of a two-factor attempt failed.
UNIFORM_PUBLIC_REASON_CODE = "CREDENTIAL_INVALID"

#: Internal reason codes that must NEVER reach an unauthenticated caller,
#: because each of them answers "does this account exist?" or "what state
#: is it in?" - questions an unauthenticated caller has no standing to
#: ask.
NON_DISCLOSABLE_REASON_CODES: frozenset[str] = frozenset(
    {
        "VALIDATION_RECORD_NOT_FOUND",
        "ACCOUNT_LOCKED",
        "ACCOUNT_RESTRICTED",
        "ACCOUNT_QUARANTINED",
        "ACCOUNT_CLOSED",
        "ACCOUNT_NOT_ACTIVATED",
        "CONTACT_ALREADY_IN_USE",
        "DUPLICATE_ACCOUNT_SUSPECTED",
        "CREDENTIAL_REVOKED",
        "CREDENTIAL_EXPIRED",
        "MFA_FACTOR_NOT_ENROLLED",
        "PASSWORD_LOGIN_DISABLED",
        "AUTHENTICATION_THROTTLED",
    }
)


def public_reason_code(internal_reason_code: str) -> str:
    """Map an internal code onto what a public response may say.

    Deliberately a whitelist-by-exclusion rather than a lookup table with
    a permissive default: a new internal code is non-disclosable until
    someone adds it to the safe set, which is the direction a mistake
    should fail in.
    """
    if internal_reason_code in NON_DISCLOSABLE_REASON_CODES:
        return UNIFORM_PUBLIC_REASON_CODE
    return internal_reason_code


class RiskSignalCategory(StrEnum):
    """The named signals from the session security matrix §3."""

    NEW_DEVICE = "new_device"
    UNUSUAL_ORIGIN = "unusual_origin"
    REPEATED_FAILURES = "repeated_failures"
    SESSION_REPLAY = "session_replay"
    IMPOSSIBLE_TRAVEL = "impossible_travel"
    CREDENTIAL_CHANGE = "credential_change"
    RECOVERY_ATTEMPT = "recovery_attempt"
    PRIVILEGED_OPERATION = "privileged_operation"


def parse_risk_signal_category(value: str) -> RiskSignalCategory:
    try:
        return RiskSignalCategory(value)
    except ValueError as exc:
        raise UnknownRiskSignalCategoryError(f"unknown risk signal category: {value!r}") from exc


class SignalWeight(StrEnum):
    WEAK = "weak"
    MEDIUM = "medium"
    HIGH = "high"


#: The weights the matrix assigns. `IMPOSSIBLE_TRAVEL` is **weak** and
#: that is a decision, not an oversight: geolocation of an IP address is
#: wrong often enough that denying a member their account on it would be
#: a routine injustice.
SIGNAL_WEIGHTS: dict[RiskSignalCategory, SignalWeight] = {
    RiskSignalCategory.NEW_DEVICE: SignalWeight.MEDIUM,
    RiskSignalCategory.UNUSUAL_ORIGIN: SignalWeight.MEDIUM,
    RiskSignalCategory.REPEATED_FAILURES: SignalWeight.HIGH,
    RiskSignalCategory.SESSION_REPLAY: SignalWeight.HIGH,
    RiskSignalCategory.IMPOSSIBLE_TRAVEL: SignalWeight.WEAK,
    RiskSignalCategory.CREDENTIAL_CHANGE: SignalWeight.HIGH,
    RiskSignalCategory.RECOVERY_ATTEMPT: SignalWeight.HIGH,
    RiskSignalCategory.PRIVILEGED_OPERATION: SignalWeight.HIGH,
}


@dataclass(frozen=True, slots=True)
class RiskSignal:
    category: RiskSignalCategory
    observed_at: datetime
    explanation: str

    def __post_init__(self) -> None:
        require_timezone(self.observed_at, "observed_at")
        if not self.explanation:
            raise ValueError("every risk signal carries a human-readable explanation")

    @property
    def weight(self) -> SignalWeight:
        return SIGNAL_WEIGHTS[self.category]


@dataclass(frozen=True, slots=True)
class RiskAssessment:
    """An explainable classification, never a bare score.

    `classify` refuses to reach `SUSPICIOUS` from weak signals alone.
    That single rule is what makes "no opaque risk score is ever the sole
    basis for a consequential denial" true of the code rather than of the
    documentation.
    """

    signals: tuple[RiskSignal, ...]
    state: RiskState

    @staticmethod
    def classify(signals: tuple[RiskSignal, ...]) -> RiskAssessment:
        high = [signal for signal in signals if signal.weight is SignalWeight.HIGH]
        medium = [signal for signal in signals if signal.weight is SignalWeight.MEDIUM]
        if high:
            state = RiskState.SUSPICIOUS
        elif medium:
            state = RiskState.ELEVATED
        else:
            state = RiskState.NORMAL
        return RiskAssessment(signals=signals, state=state)

    def named_signals(self) -> tuple[str, ...]:
        return tuple(signal.category.value for signal in self.signals)


@dataclass(frozen=True, slots=True)
class AuthenticationChallenge:
    """A short-lived, single-use challenge with a unique nonce."""

    challenge_id: UUID
    account_reference: ScopedIdentityReference | None
    workspace: WorkspaceId
    method: AuthenticationMethod
    nonce: str
    issued_at: datetime
    expires_at: datetime
    consumed_at: datetime | None = None

    def __post_init__(self) -> None:
        require_timezone(self.issued_at, "issued_at")
        require_timezone(self.expires_at, "expires_at")
        if self.consumed_at is not None:
            require_timezone(self.consumed_at, "consumed_at")

    def assert_open(self, now: datetime) -> None:
        if self.consumed_at is not None:
            raise NonceAlreadyUsedError("this challenge has already been consumed")
        if require_timezone(now, "now") >= self.expires_at:
            raise ChallengeExpiredError("the challenge has expired")

    def consumed(self, *, at: datetime) -> AuthenticationChallenge:
        return replace(self, consumed_at=require_timezone(at, "at"))


class AuthenticationOutcomeKind(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    STEP_UP_REQUIRED = "step_up_required"
    MFA_REQUIRED = "mfa_required"
    RECOVERY_REQUIRED = "recovery_required"


@dataclass(frozen=True, slots=True)
class AuthenticationOutcome:
    """The two-code result.

    `internal_reason_code` is what the audit record and the operator see;
    `public_reason_code` is what the response carries. Holding both on one
    object is what makes it hard to accidentally return the wrong one.
    """

    kind: AuthenticationOutcomeKind
    internal_reason_code: str
    public_reason_code: str
    method: AuthenticationMethod | None
    occurred_at: datetime

    def __post_init__(self) -> None:
        require_timezone(self.occurred_at, "occurred_at")
        if self.public_reason_code in NON_DISCLOSABLE_REASON_CODES:
            raise ValueError(
                f"{self.public_reason_code!r} may never be returned to an unauthenticated caller"
            )


def failed_outcome(
    *, internal_reason_code: str, method: AuthenticationMethod | None, occurred_at: datetime
) -> AuthenticationOutcome:
    return AuthenticationOutcome(
        kind=AuthenticationOutcomeKind.FAILED,
        internal_reason_code=internal_reason_code,
        public_reason_code=public_reason_code(internal_reason_code),
        method=method,
        occurred_at=occurred_at,
    )


@dataclass(frozen=True, slots=True)
class AuthenticationAttempt:
    """One attempt, as recorded.

    `account_reference` is a **scoped** reference, and `origin` is the
    workspace origin rather than a client IP address: the retention
    matrix records authentication attempts with a "coarse origin", and
    storing the precise one would build the correlation surface the
    minimization commitments forbid.
    """

    attempt_id: UUID
    account_reference: ScopedIdentityReference | None
    workspace: WorkspaceId
    method: AuthenticationMethod
    outcome: AuthenticationOutcome
    risk: RiskAssessment
    attempted_at: datetime

    def __post_init__(self) -> None:
        require_timezone(self.attempted_at, "attempted_at")


@dataclass(frozen=True, slots=True)
class RateLimitBucket:
    """A fixed-window counter for one operation and one subject.

    Deliberately simple and deliberately per-operation: a global limiter
    would let noise on one endpoint throttle another, and a limiter keyed
    only by account would let an attacker deny a member their own account
    by failing against it.
    """

    key: str
    window_started_at: datetime
    count: int
    limit: int
    window: timedelta

    def __post_init__(self) -> None:
        require_timezone(self.window_started_at, "window_started_at")
        if self.limit < 1:
            raise ValueError("a rate limit admits at least one request")

    def hit(self, *, now: datetime) -> RateLimitBucket:
        moment = require_timezone(now, "now")
        if moment - self.window_started_at >= self.window:
            return replace(self, window_started_at=moment, count=1)
        if self.count >= self.limit:
            raise RateLimitExceededError(
                f"the rate limit for {self.key!r} ({self.limit} per {self.window}) was exceeded"
            )
        return replace(self, count=self.count + 1)


def assert_method_permits_login(method: AuthenticationMethod) -> None:
    """Not every method may begin a login ceremony.

    SMS OTP is absent from `PERMITS_LOGIN` because it authenticates
    nothing; a recovery code is absent because a recovery code is
    recovery entry, and entering recovery is not logging in.
    """
    if method not in PERMITS_LOGIN:
        raise UnknownAuthenticationMethodError(
            f"{method.value} may not begin an authentication ceremony"
        )


def issue_challenge(
    *,
    challenge_id: UUID,
    account_reference: ScopedIdentityReference | None,
    workspace: WorkspaceId,
    method: AuthenticationMethod,
    issued_at: datetime,
    lifetime: timedelta,
    random: SecureRandom,
) -> AuthenticationChallenge:
    """Issue a challenge - **including for an account that does not
    exist**.

    That is the enumeration control: a caller who names an unknown handle
    receives a challenge with the same shape and the same latency profile
    as one who names a real account, and learns nothing from the
    difference. `account_reference=None` is the unknown-account case and
    is a first-class input here rather than an error.
    """
    assert_method_permits_login(method)
    moment = require_timezone(issued_at, "issued_at")
    return AuthenticationChallenge(
        challenge_id=challenge_id,
        account_reference=account_reference,
        workspace=workspace,
        method=method,
        nonce=random.token(),
        issued_at=moment,
        expires_at=moment + lifetime,
    )


def assert_uniform_failure(outcome: AuthenticationOutcome) -> None:
    """Assert an outcome is safe to return publicly.

    Called on every response path. It is a belt-and-braces check on top
    of `AuthenticationOutcome.__post_init__`, placed where a future
    refactor that constructs an outcome by other means still passes
    through it.
    """
    if outcome.public_reason_code in NON_DISCLOSABLE_REASON_CODES:
        raise InvalidCredentialError(
            "a public authentication response may not disclose account state"
        )
