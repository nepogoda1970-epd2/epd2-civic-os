"""Versioned numeric policy for PACK-12 (resolution of `OD-P12-03`).

Every numeric threshold this pack needs lives here, in one typed,
versioned, immutable object. Nothing in `access`, `breakglass`,
`search`, `export`, `dlp` or `disclosure` may hard-code a duration, a
limit or a threshold: a number written into domain logic is a number no
operator can govern and no test can vary.

Three properties are load-bearing:

- **Centralised and typed.** One dataclass, constructed once, passed
  explicitly. There is no module-level mutable default and no
  environment lookup.
- **Versioned.** `policy_version` travels on every decision and every
  event, so a past refusal stays answerable after the policy changes
  (`P12-EXP-019`).
- **Unable to disable an invariant.** `__post_init__` refuses values that
  would switch a control off - a zero-length break-glass window, an
  unbounded grant, a cohort threshold below the floor. A policy that
  could set `max_grant_duration` to a century would be
  `P12-PAM-003`'s prohibited standing superuser reintroduced as
  configuration (`P12-BG-009`, register `FIR-INV-006`).

**The defaults below are reference defaults for a reference
implementation.** They are not a legally approved operational policy, not
a recommendation, and not a claim that any particular number is
sufficient for any particular organization. Choosing real values is a
governed decision made outside this system.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from epd2_privileged_access_service.domain import RiskClass
from epd2_privileged_access_service.exceptions import (
    DisclosureThresholdFailedError,
    StandingAccessProhibitedError,
)

#: The absolute ceilings this module will not allow a policy to exceed.
#: A policy is governed configuration; these are the floor beneath the
#: configuration, and they exist so that a mis-set policy degrades to
#: "too strict" rather than "switched off".
MAX_ALLOWED_GRANT_DURATION: timedelta = timedelta(days=30)
MAX_ALLOWED_BREAK_GLASS_DURATION: timedelta = timedelta(hours=8)
MINIMUM_ALLOWED_COHORT_THRESHOLD: int = 3


@dataclass(frozen=True, slots=True)
class PrivilegedAccessPolicy:
    """The complete numeric policy for one organization at one version.

    Constructed explicitly and passed down; never read from a global."""

    policy_version: str

    # --- privileged access lifecycle -------------------------------------
    #: Longest an ordinary just-in-time grant may run before it expires
    #: and must be re-requested. Continuation is a new decision
    #: (`P12-PAM-006`).
    max_grant_duration: timedelta = timedelta(hours=8)
    #: Longest a grant may sit approved-but-unactivated before it lapses.
    max_activation_delay: timedelta = timedelta(hours=4)
    #: Unused-for-this-long marks a grant dormant and requiring review
    #: (`P12-PAM-009`). Resolution of `AC-P12-019`.
    dormancy_interval: timedelta = timedelta(days=7)
    #: How often an active grant must be reviewed (`P12-PAM-008`).
    periodic_review_interval: timedelta = timedelta(days=30)

    # --- break-glass -----------------------------------------------------
    #: Hard ceiling on emergency access (`P12-BG-004`).
    max_break_glass_duration: timedelta = timedelta(hours=2)
    #: Emergency access must be reviewed within this window of expiry
    #: (`P12-BG-014`).
    break_glass_review_deadline: timedelta = timedelta(days=3)

    # --- export ----------------------------------------------------------
    #: Default life of an export artifact (`P12-EXP-010`).
    export_artifact_expiry: timedelta = timedelta(days=14)
    #: How many times an artifact may be accessed before the limit bites.
    export_access_limit: int = 10
    #: Largest number of records one export may carry.
    export_max_records: int = 10_000
    #: How many exports one subject may request inside the frequency
    #: window before repeated-request risk is raised.
    export_frequency_limit: int = 5
    export_frequency_window: timedelta = timedelta(days=1)

    # --- disclosure control ----------------------------------------------
    #: Smallest cohort that may be released without suppression
    #: (`P12-SDC-001`). A floor this code will not go below, not a legal
    #: threshold it claims to know.
    cohort_threshold: int = 5
    #: Window over which cumulative releases are accounted
    #: (`P12-SDC-004`, resolution of `OD-P12-08`).
    cumulative_release_window: timedelta = timedelta(days=90)
    #: How many overlapping releases against one cohort dimension raise
    #: cumulative risk.
    cumulative_release_limit: int = 3
    #: How many near-identical queries raise differencing risk
    #: (`P12-SDC-003`).
    repeated_query_limit: int = 3

    # --- approvals -------------------------------------------------------
    #: Approvers required per risk class. High and critical are dual
    #: control by construction; see `DUAL_CONTROL_RISK_CLASSES`.
    approvers_low: int = 1
    approvers_moderate: int = 1
    approvers_high: int = 2
    approvers_critical: int = 2

    def __post_init__(self) -> None:
        if not self.policy_version or not self.policy_version.strip():
            raise StandingAccessProhibitedError("policy_version must be a non-empty string")
        for name, value in (
            ("max_grant_duration", self.max_grant_duration),
            ("max_activation_delay", self.max_activation_delay),
            ("dormancy_interval", self.dormancy_interval),
            ("periodic_review_interval", self.periodic_review_interval),
            ("max_break_glass_duration", self.max_break_glass_duration),
            ("break_glass_review_deadline", self.break_glass_review_deadline),
            ("export_artifact_expiry", self.export_artifact_expiry),
            ("cumulative_release_window", self.cumulative_release_window),
            ("export_frequency_window", self.export_frequency_window),
        ):
            if value <= timedelta(0):
                raise StandingAccessProhibitedError(f"{name} must be a positive duration")
        if self.max_grant_duration > MAX_ALLOWED_GRANT_DURATION:
            raise StandingAccessProhibitedError(
                "max_grant_duration exceeds the ceiling; a policy may not create standing access"
            )
        if self.max_break_glass_duration > MAX_ALLOWED_BREAK_GLASS_DURATION:
            raise StandingAccessProhibitedError(
                "max_break_glass_duration exceeds the ceiling for emergency access"
            )
        if self.cohort_threshold < MINIMUM_ALLOWED_COHORT_THRESHOLD:
            raise DisclosureThresholdFailedError(
                "cohort_threshold is below the floor; a policy may not disable disclosure control"
            )
        for name, count in (
            ("export_access_limit", self.export_access_limit),
            ("export_max_records", self.export_max_records),
            ("export_frequency_limit", self.export_frequency_limit),
            ("cumulative_release_limit", self.cumulative_release_limit),
            ("repeated_query_limit", self.repeated_query_limit),
            ("approvers_low", self.approvers_low),
            ("approvers_moderate", self.approvers_moderate),
            ("approvers_high", self.approvers_high),
            ("approvers_critical", self.approvers_critical),
        ):
            if count < 1:
                raise StandingAccessProhibitedError(f"{name} must be a positive integer")
        if self.approvers_high < 2 or self.approvers_critical < 2:
            raise StandingAccessProhibitedError(
                "high and critical risk classes require dual control; a policy may not reduce it"
            )

    def required_approvers(self, risk: RiskClass) -> int:
        """How many distinct approvers this risk class needs."""
        return {
            RiskClass.LOW: self.approvers_low,
            RiskClass.MODERATE: self.approvers_moderate,
            RiskClass.HIGH: self.approvers_high,
            RiskClass.CRITICAL: self.approvers_critical,
        }[risk]

    def assert_grant_duration_allowed(self, duration: timedelta) -> None:
        if duration > self.max_grant_duration:
            raise StandingAccessProhibitedError(
                f"requested duration {duration} exceeds the policy maximum "
                f"{self.max_grant_duration}"
            )

    def assert_break_glass_duration_allowed(self, duration: timedelta) -> None:
        if duration > self.max_break_glass_duration:
            raise StandingAccessProhibitedError(
                f"requested emergency duration {duration} exceeds the policy maximum "
                f"{self.max_break_glass_duration}"
            )

    def to_payload(self) -> dict[str, object]:
        """The reference form carried on decisions and events: the
        version, never the whole table."""
        return {"policy_version": self.policy_version}


#: The reference default policy. Reference defaults for a reference
#: implementation - not a legally approved operational policy.
REFERENCE_POLICY: PrivilegedAccessPolicy = PrivilegedAccessPolicy(
    policy_version="pack-12-reference/v1"
)
