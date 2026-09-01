"""Step-up authentication, bound to an action **and** to an object
version.

The rule this module exists for: **if the object changes, the
confirmation is void.** A step-up obtained against version *n* does not
authorise version *n+1*. It is the rule that prevents an approval being
harvested for one thing and spent on another - a member confirms a
harmless-looking change, the underlying record is edited, and the
confirmation is redeemed against the edited version.

Two related properties follow and are enforced here rather than trusted:

- A confirmation authorises **one act**. `STEP_UP_ALREADY_CONSUMED` is a
  distinct refusal from `STEP_UP_EXPIRED`, because a spent confirmation
  and a stale one mean different things in an incident review.
- A confirmation is bound to the **actor and session** that obtained it.
  Presenting someone else's confirmation is `STEP_UP_BINDING_MISMATCH`,
  never a quiet success.

Evaluation is fail-closed exactly as canon 19d.8 requires: every
applicable condition holds simultaneously, and no "or" is permitted.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from enum import StrEnum
from uuid import UUID

from epd2_identity_service.assurance import (
    AssuranceRequirement,
    AuthenticationMethod,
    assert_method_step_up_eligible,
    assurance_rank,
)
from epd2_identity_service.configuration import ActionClass, IdentityConfiguration
from epd2_identity_service.domain import AuthenticationAssuranceLevel
from epd2_identity_service.exceptions import (
    AssuranceInsufficientError,
    StepUpAlreadyConsumedError,
    StepUpBindingMismatchError,
    StepUpCancelledError,
    StepUpExpiredError,
    StepUpObjectChangedError,
    StepUpRequiredError,
    UnknownStepUpStatusError,
)
from epd2_identity_service.identifiers import (
    ScopedIdentityReference,
    SessionId,
    require_timezone,
)
from epd2_identity_service.secret_storage import SecureRandom, constant_time_equals


class StepUpStatus(StrEnum):
    ISSUED = "issued"
    SATISFIED = "satisfied"
    CONSUMED = "consumed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


def parse_step_up_status(value: str) -> StepUpStatus:
    try:
        return StepUpStatus(value)
    except ValueError as exc:
        raise UnknownStepUpStatusError(f"unknown step-up status: {value!r}") from exc


@dataclass(frozen=True, slots=True)
class StepUpBinding:
    """Everything a confirmation is bound to.

    All six fields are mandatory. An optional `resource_version` would be
    an omitted `resource_version`, and an omitted one is the harvesting
    attack this module exists to prevent - so where an action genuinely
    has no versioned object, callers pass the action's own reference and
    version `0`, which still binds the confirmation to that action.
    """

    actor_reference: ScopedIdentityReference
    session_id: SessionId
    action_code: str
    resource_type: str
    resource_id: UUID
    resource_version: int

    def __post_init__(self) -> None:
        if not self.action_code:
            raise ValueError("a step-up binding names its action")
        if not self.resource_type:
            raise ValueError("a step-up binding names its resource type")
        if self.resource_version < 0:
            raise ValueError("resource_version must not be negative")

    def matches(self, other: StepUpBinding) -> bool:
        """Actor, session, action and resource identity must all match.

        The **version** is deliberately excluded here and compared
        separately, so a version difference produces
        `STEP_UP_OBJECT_CHANGED` rather than a generic binding mismatch -
        two different situations with two different remedies.
        """
        return (
            self.actor_reference == other.actor_reference
            and self.session_id == other.session_id
            and self.action_code == other.action_code
            and self.resource_type == other.resource_type
            and self.resource_id == other.resource_id
        )


@dataclass(frozen=True, slots=True)
class StepUpChallenge:
    """A step-up in flight."""

    challenge_id: UUID
    binding: StepUpBinding
    required_assurance: AuthenticationAssuranceLevel
    action_class: ActionClass
    nonce: str
    issued_at: datetime
    expires_at: datetime
    status: StepUpStatus = StepUpStatus.ISSUED

    def __post_init__(self) -> None:
        require_timezone(self.issued_at, "issued_at")
        require_timezone(self.expires_at, "expires_at")
        if self.expires_at <= self.issued_at:
            raise ValueError("a step-up challenge must expire after it was issued")
        if not self.nonce:
            raise ValueError("a step-up challenge carries a nonce")


@dataclass(frozen=True, slots=True)
class StepUpResult:
    """A completed step-up. The thing an action redeems, once."""

    challenge_id: UUID
    binding: StepUpBinding
    achieved_assurance: AuthenticationAssuranceLevel
    method: AuthenticationMethod
    completed_at: datetime
    expires_at: datetime
    status: StepUpStatus

    def __post_init__(self) -> None:
        require_timezone(self.completed_at, "completed_at")
        require_timezone(self.expires_at, "expires_at")

    def consumed(self) -> StepUpResult:
        return replace(self, status=StepUpStatus.CONSUMED)


@dataclass(frozen=True, slots=True)
class StepUpFreshness:
    """How long a completed step-up remains spendable, per action class.

    Read from the governed configuration rather than held as a constant,
    so `FIR-CONFIG-001` genuinely owns the numbers (specification §8.1).
    """

    action_class: ActionClass
    window: timedelta

    @staticmethod
    def for_action(
        action_class: ActionClass, configuration: IdentityConfiguration
    ) -> StepUpFreshness:
        return StepUpFreshness(
            action_class=action_class, window=configuration.freshness_window(action_class)
        )


def issue_step_up_challenge(
    *,
    challenge_id: UUID,
    binding: StepUpBinding,
    requirement: AssuranceRequirement,
    issued_at: datetime,
    configuration: IdentityConfiguration,
    random: SecureRandom,
) -> StepUpChallenge:
    moment = require_timezone(issued_at, "issued_at")
    return StepUpChallenge(
        challenge_id=challenge_id,
        binding=binding,
        required_assurance=requirement.required_authentication_assurance,
        action_class=requirement.action_class,
        nonce=random.token(),
        issued_at=moment,
        expires_at=moment + configuration.freshness_window(requirement.action_class),
    )


def complete_step_up(
    challenge: StepUpChallenge,
    *,
    presented_nonce: str,
    method: AuthenticationMethod,
    achieved_assurance: AuthenticationAssuranceLevel,
    completed_at: datetime,
) -> StepUpResult:
    """Complete a challenge into a spendable result.

    The method's step-up eligibility is checked first: a method the
    matrix marks ineligible can never satisfy a step-up, whatever
    assurance the session already holds (matrix rule 4), and finding that
    out after computing an assurance would invite treating the assurance
    as the answer.
    """
    moment = require_timezone(completed_at, "completed_at")
    if challenge.status is StepUpStatus.CANCELLED:
        raise StepUpCancelledError("the step-up was cancelled")
    if challenge.status is not StepUpStatus.ISSUED:
        raise StepUpAlreadyConsumedError("this step-up challenge is no longer open")
    if moment >= challenge.expires_at:
        raise StepUpExpiredError("the step-up window has elapsed")
    if not constant_time_equals(presented_nonce, challenge.nonce):
        raise StepUpBindingMismatchError("the presented nonce does not match this challenge")
    assert_method_step_up_eligible(method)
    if assurance_rank(achieved_assurance) < assurance_rank(challenge.required_assurance):
        raise AssuranceInsufficientError(
            f"this step-up requires {challenge.required_assurance.value} and "
            f"{achieved_assurance.value} was achieved"
        )
    return StepUpResult(
        challenge_id=challenge.challenge_id,
        binding=challenge.binding,
        achieved_assurance=achieved_assurance,
        method=method,
        completed_at=moment,
        expires_at=challenge.expires_at,
        status=StepUpStatus.SATISFIED,
    )


def redeem_step_up(
    result: StepUpResult | None,
    *,
    binding: StepUpBinding,
    now: datetime,
) -> StepUpResult:
    """Spend a confirmation against exactly one act.

    Five refusals in a deliberate order - missing, cancelled, consumed,
    expired, mis-bound, object changed - because each tells the caller a
    different thing about what to do next, and the last of them is the
    one this module exists for.
    """
    if result is None:
        raise StepUpRequiredError("this action requires a step-up and none was presented")
    if result.status is StepUpStatus.CANCELLED:
        raise StepUpCancelledError("the step-up was cancelled")
    if result.status is StepUpStatus.CONSUMED:
        raise StepUpAlreadyConsumedError(
            "this confirmation was already spent; a confirmation authorises one act"
        )
    if result.status is not StepUpStatus.SATISFIED:
        raise StepUpRequiredError("no satisfied step-up is available for this action")
    if require_timezone(now, "now") >= result.expires_at:
        raise StepUpExpiredError("the step-up window has elapsed")
    if not result.binding.matches(binding):
        raise StepUpBindingMismatchError(
            "the confirmation is bound to a different actor, session, action or resource"
        )
    if result.binding.resource_version != binding.resource_version:
        raise StepUpObjectChangedError(
            f"the object changed after confirmation "
            f"(confirmed version {result.binding.resource_version}, "
            f"presented version {binding.resource_version}); the approval is void"
        )
    return result.consumed()


def cancel_step_up(challenge: StepUpChallenge) -> StepUpChallenge:
    """Cancellation is recorded distinctly from failure.

    A person who changed their mind and a person whose factor did not
    verify are not the same event, and a security review that cannot tell
    them apart will read one as the other.
    """
    return replace(challenge, status=StepUpStatus.CANCELLED)


def expire_step_up(challenge: StepUpChallenge, *, now: datetime) -> StepUpChallenge:
    if require_timezone(now, "now") >= challenge.expires_at:
        return replace(challenge, status=StepUpStatus.EXPIRED)
    return challenge
