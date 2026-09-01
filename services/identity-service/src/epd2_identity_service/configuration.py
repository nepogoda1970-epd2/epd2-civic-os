"""Governed timeout and freshness configuration (specification §8.1).

Every duration PACK-14 enforces is **configuration with a safe default**,
owned by `FIR-CONFIG-001` - not a hard-coded constant and not canon. This
module is where that decision is made real, and the four rules that
constrain the configuration itself are enforced here rather than
documented elsewhere:

1. A deployment may make any value **stricter** freely.
2. **Relaxing** a value is a governed change carrying an authority and a
   registered reason code; without one it is refused.
3. **No configuration may remove a deadline.** There is no "unlimited"
   value and the constructor admits none, which is what makes "no
   infinite session" a structural property rather than a policy.
4. Missing or unreadable configuration **falls back to the defaults**,
   never to permissive behaviour.

The defaults themselves come from the accepted specification's §8.1 table
and are reproduced nowhere else in this package, so a future edit changes
one place.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import timedelta
from enum import StrEnum

from epd2_identity_service.domain import AuthenticationAssuranceLevel
from epd2_identity_service.exceptions import (
    ConfigurationDeadlineRemovalRefusedError,
    ConfigurationRelaxationNotGovernedError,
    UnknownStepUpActionClassError,
)


class ActionClass(StrEnum):
    """The action classes the freshness table is keyed by. Each names a
    distinct consequence, because a single "sensitive action" bucket
    would make the 60-minute submission window and the 15-minute security
    window the same window."""

    ORDINARY_READ = "ordinary_read"
    SECURITY_SETTINGS_READ = "security_settings_read"
    CONSEQUENTIAL_ACTION = "consequential_action"
    OFFICIAL_SUBMISSION = "official_submission"
    SECURITY_OR_CONTACT_CHANGE = "security_or_contact_change"


def parse_action_class(value: str) -> ActionClass:
    try:
        return ActionClass(value)
    except ValueError as exc:
        raise UnknownStepUpActionClassError(f"unknown action class: {value!r}") from exc


#: Specification §8.1: idle and absolute timeouts by achieved assurance.
#: `none` has no row because an unauthenticated session is not a session.
DEFAULT_IDLE_TIMEOUTS: dict[AuthenticationAssuranceLevel, timedelta] = {
    AuthenticationAssuranceLevel.LOW: timedelta(minutes=30),
    AuthenticationAssuranceLevel.SUBSTANTIAL: timedelta(minutes=30),
    AuthenticationAssuranceLevel.HIGH: timedelta(minutes=15),
}

DEFAULT_ABSOLUTE_TIMEOUTS: dict[AuthenticationAssuranceLevel, timedelta] = {
    AuthenticationAssuranceLevel.LOW: timedelta(days=7),
    AuthenticationAssuranceLevel.SUBSTANTIAL: timedelta(hours=24),
    AuthenticationAssuranceLevel.HIGH: timedelta(hours=8),
}

#: Specification §8.1: freshness windows by action class.
DEFAULT_FRESHNESS_WINDOWS: dict[ActionClass, timedelta] = {
    ActionClass.ORDINARY_READ: timedelta(hours=24),
    ActionClass.SECURITY_SETTINGS_READ: timedelta(minutes=60),
    ActionClass.CONSEQUENTIAL_ACTION: timedelta(minutes=15),
    ActionClass.OFFICIAL_SUBMISSION: timedelta(minutes=60),
    ActionClass.SECURITY_OR_CONTACT_CHANGE: timedelta(minutes=15),
}

#: How long after a contact change that channel may not be the sole basis
#: for recovery. Provisional pending `OD-P14-07`; the *behaviour* it
#: guards is not provisional.
DEFAULT_CONTACT_PROTECTIVE_WINDOW = timedelta(days=7)

#: Default cooling-off before a recovery may complete, and before a
#: closure request takes effect.
DEFAULT_RECOVERY_COOLING_OFF = timedelta(hours=48)
DEFAULT_CLOSURE_COOLING_OFF = timedelta(days=14)

#: Short lifetimes for the single-use artifacts. Both are checked at
#: redemption, never at issuance only.
DEFAULT_BOOTSTRAP_LIFETIME = timedelta(minutes=2)
DEFAULT_VOTING_HANDOFF_LIFETIME = timedelta(minutes=2)
DEFAULT_CHALLENGE_LIFETIME = timedelta(minutes=5)


@dataclass(frozen=True, slots=True)
class GovernanceAuthority:
    """Who authorised a relaxation, and under what registered code. A
    relaxation without one of these is refused - "someone edited an
    environment variable" is not an authority."""

    authority_reference: str
    reason_code: str

    def __post_init__(self) -> None:
        if not self.authority_reference:
            raise ValueError("authority_reference must not be empty")
        if not self.reason_code:
            raise ValueError("reason_code must not be empty")


@dataclass(frozen=True, slots=True)
class SessionTimeoutPolicy:
    """Idle and absolute deadlines per assurance level.

    Both fields are mandatory `timedelta`s. There is no `None`, no zero
    and no sentinel meaning "unlimited": rule 3 is enforced by the type
    and by `__post_init__` together, so no code path in this package can
    construct a session without both deadlines.
    """

    idle: dict[AuthenticationAssuranceLevel, timedelta]
    absolute: dict[AuthenticationAssuranceLevel, timedelta]

    def __post_init__(self) -> None:
        for level in (
            AuthenticationAssuranceLevel.LOW,
            AuthenticationAssuranceLevel.SUBSTANTIAL,
            AuthenticationAssuranceLevel.HIGH,
        ):
            for table, name in ((self.idle, "idle"), (self.absolute, "absolute")):
                if level not in table:
                    raise ConfigurationDeadlineRemovalRefusedError(
                        f"{name} deadline missing for assurance {level.value!r}"
                    )
                if table[level] <= timedelta(0):
                    raise ConfigurationDeadlineRemovalRefusedError(
                        f"{name} deadline for {level.value!r} must be a positive duration"
                    )
            if self.absolute[level] < self.idle[level]:
                raise ConfigurationDeadlineRemovalRefusedError(
                    f"absolute deadline for {level.value!r} must not be shorter than the idle one"
                )


@dataclass(frozen=True, slots=True)
class IdentityConfiguration:
    """The whole governed configuration surface for this package.

    Constructed through `default_configuration()` and changed only
    through `tighten()` or `relax()`, so every change goes through the
    rule that applies to it. Reading a field is free; widening one is
    not.
    """

    session_timeouts: SessionTimeoutPolicy
    freshness_windows: dict[ActionClass, timedelta]
    contact_protective_window: timedelta
    recovery_cooling_off: timedelta
    closure_cooling_off: timedelta
    bootstrap_lifetime: timedelta
    voting_handoff_lifetime: timedelta
    challenge_lifetime: timedelta
    password_login_enabled: bool

    def __post_init__(self) -> None:
        for action_class in ActionClass:
            window = self.freshness_windows.get(action_class)
            if window is None or window <= timedelta(0):
                raise ConfigurationDeadlineRemovalRefusedError(
                    f"freshness window missing or non-positive for {action_class.value!r}"
                )
        for name in (
            "contact_protective_window",
            "recovery_cooling_off",
            "closure_cooling_off",
            "bootstrap_lifetime",
            "voting_handoff_lifetime",
            "challenge_lifetime",
        ):
            if getattr(self, name) <= timedelta(0):
                raise ConfigurationDeadlineRemovalRefusedError(
                    f"{name} must be a positive duration; no deadline may be removed"
                )

    def idle_timeout(self, level: AuthenticationAssuranceLevel) -> timedelta:
        return self.session_timeouts.idle[level]

    def absolute_timeout(self, level: AuthenticationAssuranceLevel) -> timedelta:
        return self.session_timeouts.absolute[level]

    def freshness_window(self, action_class: ActionClass) -> timedelta:
        return self.freshness_windows[action_class]


def default_configuration() -> IdentityConfiguration:
    """The safe defaults from specification §8.1.

    This is also the fallback: `load_configuration` returns exactly this
    when configuration is missing or unreadable, because rule 4 says the
    fallback is the default and never permissive behaviour.
    """
    return IdentityConfiguration(
        session_timeouts=SessionTimeoutPolicy(
            idle=dict(DEFAULT_IDLE_TIMEOUTS),
            absolute=dict(DEFAULT_ABSOLUTE_TIMEOUTS),
        ),
        freshness_windows=dict(DEFAULT_FRESHNESS_WINDOWS),
        contact_protective_window=DEFAULT_CONTACT_PROTECTIVE_WINDOW,
        recovery_cooling_off=DEFAULT_RECOVERY_COOLING_OFF,
        closure_cooling_off=DEFAULT_CLOSURE_COOLING_OFF,
        bootstrap_lifetime=DEFAULT_BOOTSTRAP_LIFETIME,
        voting_handoff_lifetime=DEFAULT_VOTING_HANDOFF_LIFETIME,
        challenge_lifetime=DEFAULT_CHALLENGE_LIFETIME,
        password_login_enabled=True,
    )


def load_configuration(overrides: object | None) -> IdentityConfiguration:
    """Rule 4, as a function.

    `overrides` is deliberately typed `object | None`: this reference
    implementation reads no file and no environment, so anything that is
    not already an `IdentityConfiguration` is treated as unreadable and
    the defaults are returned. A deployment that grows a real loader
    replaces this body; what it may not do is return something more
    permissive than the defaults when the load fails.
    """
    if isinstance(overrides, IdentityConfiguration):
        return overrides
    return default_configuration()


def _assert_stricter(current: timedelta, proposed: timedelta, name: str) -> None:
    if proposed > current:
        raise ConfigurationRelaxationNotGovernedError(
            f"{name}: {proposed} is longer than the current {current}; "
            "relaxing a governed value requires an authority and a reason code"
        )


def tighten_freshness_window(
    configuration: IdentityConfiguration,
    *,
    action_class: ActionClass,
    proposed: timedelta,
) -> IdentityConfiguration:
    """Rule 1: stricter is free, and needs no authority."""
    _assert_stricter(
        configuration.freshness_window(action_class), proposed, f"freshness[{action_class.value}]"
    )
    windows = dict(configuration.freshness_windows)
    windows[action_class] = proposed
    return replace(configuration, freshness_windows=windows)


def relax_freshness_window(
    configuration: IdentityConfiguration,
    *,
    action_class: ActionClass,
    proposed: timedelta,
    authority: GovernanceAuthority | None,
) -> IdentityConfiguration:
    """Rule 2: relaxing requires a named authority and a reason code.

    `authority=None` is the ordinary case a careless caller produces, and
    it is refused rather than defaulted - which is the difference between
    a governed change and an environment variable.
    """
    if authority is None:
        raise ConfigurationRelaxationNotGovernedError(
            f"freshness[{action_class.value}] may not be relaxed without a governance authority"
        )
    if proposed <= configuration.freshness_window(action_class):
        return tighten_freshness_window(configuration, action_class=action_class, proposed=proposed)
    windows = dict(configuration.freshness_windows)
    windows[action_class] = proposed
    return replace(configuration, freshness_windows=windows)


def tighten_session_timeout(
    configuration: IdentityConfiguration,
    *,
    level: AuthenticationAssuranceLevel,
    idle: timedelta | None = None,
    absolute: timedelta | None = None,
) -> IdentityConfiguration:
    """Rule 1 for session deadlines. Passing `None` leaves that deadline
    untouched; passing a longer value is refused, because that is a
    relaxation whatever the caller named the function."""
    idle_table = dict(configuration.session_timeouts.idle)
    absolute_table = dict(configuration.session_timeouts.absolute)
    if idle is not None:
        _assert_stricter(idle_table[level], idle, f"idle[{level.value}]")
        idle_table[level] = idle
    if absolute is not None:
        _assert_stricter(absolute_table[level], absolute, f"absolute[{level.value}]")
        absolute_table[level] = absolute
    return replace(
        configuration,
        session_timeouts=SessionTimeoutPolicy(idle=idle_table, absolute=absolute_table),
    )


def disable_password_login(
    configuration: IdentityConfiguration, *, authority: GovernanceAuthority
) -> IdentityConfiguration:
    """Specification §5.2: password login can be disabled through
    governed configuration. Disabling is a tightening, so it needs no
    justification beyond the authority record that makes it auditable -
    and the authority is still required, because an organization needs to
    know who closed a login path for its members."""
    if not authority.authority_reference:
        raise ConfigurationRelaxationNotGovernedError("disabling password login needs an authority")
    return replace(configuration, password_login_enabled=False)


def enable_password_login(
    configuration: IdentityConfiguration, *, authority: GovernanceAuthority | None
) -> IdentityConfiguration:
    """Re-enabling password login **is** a relaxation and is governed as
    one."""
    if authority is None:
        raise ConfigurationRelaxationNotGovernedError(
            "re-enabling password login is a relaxation and requires a governance authority"
        )
    return replace(configuration, password_login_enabled=True)
