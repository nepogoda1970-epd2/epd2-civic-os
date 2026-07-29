"""Statistical disclosure control foundation (ADR-067, second half).

Contract-level, not a production analytics engine. Seven entities, eight
rules, and one principle that shapes all of them: **a threshold is never
the only protection** (`P12-SDC-005`).

A threshold alone is defeated by differencing two queries, by reading a
total, by combining neighbouring cohorts, or by issuing the same query as
two people. So this module carries four independent rule families, and
`assert_release_permitted` requires more than one of them to be active:

1. cohort threshold (`P12-SDC-001`);
2. complement protection - totals and neighbours (`P12-SDC-007`);
3. differencing detection across successive queries (`P12-SDC-003`);
4. cumulative accounting across releases (`P12-SDC-004`).

`OD-P12-08` is resolved by `ReleaseHistory`: organization-scoped,
cohort-dimension-scoped and window-scoped, holding release *references*
and disclosure-relevant dimensions - never the exported payload. When the
required history cannot be read, evaluation fails closed
(`ReleaseHistoryUnavailableError`) rather than assuming no prior release.

The bound on the window is a real limitation, stated rather than hidden:
cumulative risk outside the window is not seen. Production persistence
for a longer history is PACK-13's.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from epd2_privileged_access_service.domain import (
    OrganizationalScopeRef,
    Purpose,
    ReasonCoded,
    require_text,
    require_timezone,
)
from epd2_privileged_access_service.exceptions import (
    DisclosureAssessmentMissingError,
    DisclosureComplementRecoverableError,
    DisclosureCumulativeReleaseRiskError,
    DisclosureExceptionExpiredError,
    DisclosureExceptionNotApprovedError,
    DisclosurePublicationAuthorityMissingError,
    DisclosureRepeatedQueryRiskError,
    DisclosureSuppressionRequiredError,
    DisclosureThresholdFailedError,
    ReleaseHistoryUnavailableError,
    SelfApprovalProhibitedError,
    UnknownStatusError,
)
from epd2_privileged_access_service.policy import (
    MINIMUM_ALLOWED_COHORT_THRESHOLD,
    PrivilegedAccessPolicy,
)


class DisclosureRuleFamily(StrEnum):
    COHORT_THRESHOLD = "cohort_threshold"
    COMPLEMENT_PROTECTION = "complement_protection"
    DIFFERENCING_DETECTION = "differencing_detection"
    CUMULATIVE_ACCOUNTING = "cumulative_accounting"


@dataclass(frozen=True, slots=True)
class CohortPolicy:
    """The cohort rules for one release class."""

    policy_id: UUID
    release_class: str
    minimum_cohort_size: int
    active_rule_families: frozenset[DisclosureRuleFamily]
    policy_version: str = "pack-12-disclosure/v1"

    def __post_init__(self) -> None:
        require_text(self.release_class, "release_class")
        require_text(self.policy_version, "policy_version")
        if self.minimum_cohort_size < MINIMUM_ALLOWED_COHORT_THRESHOLD:
            raise DisclosureThresholdFailedError(
                f"minimum_cohort_size {self.minimum_cohort_size} is below the hard floor "
                f"{MINIMUM_ALLOWED_COHORT_THRESHOLD}; a per-release-class policy may make the "
                "threshold stricter and never weaker than the repository-wide floor"
            )
        if len(self.active_rule_families) < 2:
            raise DisclosureThresholdFailedError(
                "a threshold is never the only protection: at least two independent rule "
                "families must be active"
            )

    def to_payload(self) -> dict[str, object]:
        return {
            "policy_id": str(self.policy_id),
            "release_class": self.release_class,
            "minimum_cohort_size": self.minimum_cohort_size,
            "active_rule_families": sorted(f.value for f in self.active_rule_families),
            "policy_version": self.policy_version,
        }


@dataclass(frozen=True, slots=True)
class DisclosureRule:
    """One evaluated rule and its outcome."""

    family: DisclosureRuleFamily
    passed: bool
    detail_reference: str

    def __post_init__(self) -> None:
        require_text(self.detail_reference, "detail_reference")

    def to_payload(self) -> dict[str, object]:
        return {
            "family": str(self.family),
            "passed": self.passed,
            "detail_reference": self.detail_reference,
        }


@dataclass(frozen=True, slots=True)
class CohortObservation:
    """One cohort in a candidate release.

    `dimensions` is the disclosure-relevant shape of the cohort - the
    fields it was cut by - not its members. Storing members would make
    the release history the very disclosure it exists to prevent."""

    cohort_key: str
    size: int
    dimensions: frozenset[str]

    def __post_init__(self) -> None:
        require_text(self.cohort_key, "cohort_key")
        if self.size < 0:
            raise DisclosureThresholdFailedError("cohort size must not be negative")


@dataclass(frozen=True, slots=True)
class ReleaseHistoryEntry:
    """One prior release, as the history records it.

    References and dimensions only: no payload, no values, no members
    (`OD-P12-08`)."""

    release_id: UUID
    organization_scope: OrganizationalScopeRef
    release_class: str
    cohort_dimensions: frozenset[str]
    cohort_keys: frozenset[str]
    released_at: datetime
    release_reference: str

    def __post_init__(self) -> None:
        require_timezone(self.released_at, context="ReleaseHistoryEntry.released_at")
        require_text(self.release_reference, "release_reference")


@dataclass(frozen=True, slots=True)
class ReleaseHistory:
    """A bounded, scoped view of prior releases.

    `available` is explicit rather than implied by an empty list: "no
    prior releases" and "could not read the history" are different facts,
    and treating the second as the first is how cumulative accounting
    silently stops working."""

    organization_scope: OrganizationalScopeRef
    window_start: datetime
    window_end: datetime
    entries: tuple[ReleaseHistoryEntry, ...]
    available: bool = True

    def __post_init__(self) -> None:
        require_timezone(self.window_start, context="ReleaseHistory.window_start")
        require_timezone(self.window_end, context="ReleaseHistory.window_end")

    def assert_available(self) -> None:
        if not self.available:
            raise ReleaseHistoryUnavailableError(
                "the release history required for cumulative accounting could not be read; "
                "the release is refused rather than evaluated against an assumed empty history"
            )

    def overlapping(
        self, cohort_keys: frozenset[str], release_class: str
    ) -> tuple[ReleaseHistoryEntry, ...]:
        return tuple(
            entry
            for entry in self.entries
            if entry.release_class == release_class and entry.cohort_keys & cohort_keys
        )


@dataclass(frozen=True, slots=True)
class SuppressionDecision:
    """Which cohorts were suppressed and why."""

    decision_id: UUID
    suppressed_cohorts: frozenset[str]
    rule_reference: str
    decided_at: datetime

    def __post_init__(self) -> None:
        require_timezone(self.decided_at, context="SuppressionDecision.decided_at")
        require_text(self.rule_reference, "rule_reference")

    def to_payload(self) -> dict[str, object]:
        return {
            "decision_id": str(self.decision_id),
            "suppressed_cohort_count": len(self.suppressed_cohorts),
            "rule_reference": self.rule_reference,
            "decided_at": self.decided_at.isoformat(),
        }


@dataclass(frozen=True, slots=True)
class DisclosureExceptionRequest:
    exception_id: UUID
    release_class: str
    requester_reference: str
    justification_reference: str
    requested_at: datetime

    def __post_init__(self) -> None:
        require_timezone(self.requested_at, context="DisclosureExceptionRequest.requested_at")
        require_text(self.requester_reference, "requester_reference")
        require_text(self.justification_reference, "justification_reference")


@dataclass(frozen=True, slots=True)
class DisclosureExceptionDecision:
    """An approved override, bounded in time and conditions
    (`P12-SDC-006`)."""

    decision_id: UUID
    exception_id: UUID
    reviewer_reference: str
    approved: bool
    decided_at: datetime
    valid_until: datetime
    reason: ReasonCoded
    bounded_conditions: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        require_timezone(self.decided_at, context="DisclosureExceptionDecision.decided_at")
        require_timezone(self.valid_until, context="DisclosureExceptionDecision.valid_until")
        require_text(self.reviewer_reference, "reviewer_reference")
        if self.valid_until <= self.decided_at:
            raise DisclosureExceptionExpiredError(
                "an exception must be bounded: valid_until must be after the decision"
            )

    def assert_usable(self, at: datetime, request: DisclosureExceptionRequest) -> None:
        if self.reviewer_reference == request.requester_reference:
            raise SelfApprovalProhibitedError(
                "the requester of a release may not be its disclosure-control reviewer"
            )
        if not self.approved:
            raise DisclosureExceptionNotApprovedError("the exception was refused")
        if at >= self.valid_until:
            raise DisclosureExceptionExpiredError(
                "the approved exception's conditions no longer hold"
            )


@dataclass(frozen=True, slots=True)
class DisclosureRiskAssessment:
    """The evaluated risk picture for one candidate release."""

    assessment_id: UUID
    organization_scope: OrganizationalScopeRef
    release_class: str
    assessed_at: datetime
    reviewer_reference: str
    rules: tuple[DisclosureRule, ...]
    suppression: SuppressionDecision | None
    release_history_reference: str
    policy_version: str

    def __post_init__(self) -> None:
        require_timezone(self.assessed_at, context="DisclosureRiskAssessment.assessed_at")
        require_text(self.reviewer_reference, "reviewer_reference")
        require_text(self.release_history_reference, "release_history_reference")
        if not self.rules:
            raise DisclosureAssessmentMissingError(
                "a disclosure assessment must evaluate at least one rule"
            )

    @property
    def passed(self) -> bool:
        return all(rule.passed for rule in self.rules)

    def to_state_payload(self) -> dict[str, object]:
        return {
            "assessment_id": str(self.assessment_id),
            "organization_scope": self.organization_scope.to_payload(),
            "release_class": self.release_class,
            "assessed_at": self.assessed_at.isoformat(),
            "reviewer_reference": self.reviewer_reference,
            "rules": [rule.to_payload() for rule in self.rules],
            "suppression": self.suppression.to_payload() if self.suppression else None,
            "release_history_reference": self.release_history_reference,
            "policy_version": self.policy_version,
        }


# ---------------------------------------------------------------------------
# The four rule families
# ---------------------------------------------------------------------------


def evaluate_cohort_threshold(
    cohorts: Sequence[CohortObservation], cohort_policy: CohortPolicy
) -> DisclosureRule:
    small = [c.cohort_key for c in cohorts if 0 < c.size < cohort_policy.minimum_cohort_size]
    return DisclosureRule(
        family=DisclosureRuleFamily.COHORT_THRESHOLD,
        passed=not small,
        detail_reference=f"small_cohorts={len(small)}",
    )


def evaluate_complement_protection(
    cohorts: Sequence[CohortObservation],
    *,
    total: int,
    cohort_policy: CohortPolicy,
    suppressed: frozenset[str],
) -> DisclosureRule:
    """Whether a suppressed cohort is recoverable from the total.

    The classic failure: suppress the one cell below threshold, publish
    the total, and the reader subtracts. If exactly one cohort is
    suppressed and the remainder plus the total determine it, the release
    fails even though every published cell passed the threshold."""
    if not suppressed:
        return DisclosureRule(
            family=DisclosureRuleFamily.COMPLEMENT_PROTECTION,
            passed=True,
            detail_reference="no_suppression",
        )
    published = [c for c in cohorts if c.cohort_key not in suppressed]
    residual = total - sum(c.size for c in published)
    recoverable = len(suppressed) == 1 and residual >= 0
    return DisclosureRule(
        family=DisclosureRuleFamily.COMPLEMENT_PROTECTION,
        passed=not recoverable,
        detail_reference=f"suppressed={len(suppressed)};residual_determined={recoverable}",
    )


def evaluate_differencing(
    *, similar_query_digests: Sequence[str], policy: PrivilegedAccessPolicy
) -> DisclosureRule:
    count = len(similar_query_digests)
    return DisclosureRule(
        family=DisclosureRuleFamily.DIFFERENCING_DETECTION,
        passed=count < policy.repeated_query_limit,
        detail_reference=f"similar_queries={count}",
    )


def evaluate_cumulative(
    *,
    cohorts: Sequence[CohortObservation],
    release_class: str,
    history: ReleaseHistory,
    policy: PrivilegedAccessPolicy,
) -> DisclosureRule:
    history.assert_available()
    keys = frozenset(c.cohort_key for c in cohorts)
    overlapping = history.overlapping(keys, release_class)
    return DisclosureRule(
        family=DisclosureRuleFamily.CUMULATIVE_ACCOUNTING,
        passed=len(overlapping) < policy.cumulative_release_limit,
        detail_reference=f"overlapping_releases={len(overlapping)}",
    )


def assert_release_permitted(
    assessment: DisclosureRiskAssessment,
    *,
    cohort_policy: CohortPolicy,
    exception: DisclosureExceptionDecision | None = None,
    exception_request: DisclosureExceptionRequest | None = None,
    at: datetime | None = None,
) -> None:
    """Raise unless every evaluated rule passed, or an approved,
    unexpired, non-self-approved exception covers the failure.

    Each rule family raises its own reason code, because "the cohort was
    too small", "the total gives it away" and "you have asked this three
    times" call for three different corrections."""
    failed = [rule for rule in assessment.rules if not rule.passed]
    if not failed:
        return
    if exception is not None and exception_request is not None and at is not None:
        exception.assert_usable(at, exception_request)
        return
    first = failed[0]
    if first.family is DisclosureRuleFamily.COHORT_THRESHOLD:
        raise DisclosureThresholdFailedError(
            f"a cohort is below the threshold of {cohort_policy.minimum_cohort_size}"
        )
    if first.family is DisclosureRuleFamily.COMPLEMENT_PROTECTION:
        raise DisclosureComplementRecoverableError(
            "a suppressed value is recoverable from the published total or neighbouring cohorts"
        )
    if first.family is DisclosureRuleFamily.DIFFERENCING_DETECTION:
        raise DisclosureRepeatedQueryRiskError(
            "successive near-identical queries permit differencing"
        )
    raise DisclosureCumulativeReleaseRiskError(
        "individually permissible releases are jointly re-identifying over the policy window"
    )


def assert_suppression_applied(
    cohorts: Sequence[CohortObservation],
    *,
    cohort_policy: CohortPolicy,
    suppression: SuppressionDecision | None,
) -> None:
    """Raise if a small cohort was released without suppression."""
    small = {c.cohort_key for c in cohorts if 0 < c.size < cohort_policy.minimum_cohort_size}
    applied = suppression.suppressed_cohorts if suppression else frozenset()
    missing = small - applied
    if missing:
        raise DisclosureSuppressionRequiredError(
            f"cohorts {sorted(missing)} are below the threshold and were not suppressed"
        )


def assert_publication_authority(
    *, has_raw_access: bool, has_publication_authority: bool, purpose: Purpose
) -> None:
    """`P12-SDC-002`: privilege to access raw data is not authority to
    publish it."""
    if purpose not in {Purpose.STATISTICAL_RELEASE, Purpose.TRANSPARENCY_PUBLICATION}:
        return
    if has_raw_access and not has_publication_authority:
        raise DisclosurePublicationAuthorityMissingError(
            "raw-data access was presented as authority to publish; publication requires its "
            "own governed authority"
        )


def resolve_rule_family(value: str) -> DisclosureRuleFamily:
    try:
        return DisclosureRuleFamily(value)
    except ValueError as exc:
        raise UnknownStatusError(f"unknown disclosure rule family {value!r}") from exc
