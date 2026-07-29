"""Statistical disclosure control (`P12-SDC-*`, FIR-INV-011, ADR-067).

`OD-P12-08`'s resolution is the subject of most of this module: the
cumulative model is **bounded** - a window, a limit, and a history that
must be available - and it fails closed when the history cannot be read.
An unbounded "all releases ever" model would be unimplementable and would
therefore quietly become no model at all.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from epd2_privileged_access_service.disclosure import (
    CohortObservation,
    CohortPolicy,
    DisclosureExceptionDecision,
    DisclosureExceptionRequest,
    DisclosureRiskAssessment,
    DisclosureRule,
    DisclosureRuleFamily,
    ReleaseHistory,
    ReleaseHistoryEntry,
    SuppressionDecision,
    assert_publication_authority,
    assert_release_permitted,
    assert_suppression_applied,
    evaluate_cohort_threshold,
    evaluate_complement_protection,
    evaluate_cumulative,
    evaluate_differencing,
    resolve_rule_family,
)
from epd2_privileged_access_service.domain import (
    OrganizationalScopeRef,
    Purpose,
    ReasonCoded,
)
from epd2_privileged_access_service.exceptions import (
    DisclosureComplementRecoverableError,
    DisclosureCumulativeReleaseRiskError,
    DisclosureExceptionExpiredError,
    DisclosureExceptionNotApprovedError,
    DisclosurePolicyViolationError,
    DisclosurePublicationAuthorityMissingError,
    DisclosureSuppressionRequiredError,
    DisclosureThresholdFailedError,
    ReleaseHistoryUnavailableError,
    UnknownStatusError,
)
from epd2_privileged_access_service.policy import REFERENCE_POLICY

T0 = datetime(2026, 3, 1, 9, 0, tzinfo=UTC)
SCOPE = OrganizationalScopeRef(organization_id=uuid4())


def _cohort_policy(**overrides: object) -> CohortPolicy:
    base: dict[str, object] = {
        "policy_id": uuid4(),
        "release_class": "membership_statistics",
        "minimum_cohort_size": REFERENCE_POLICY.cohort_threshold,
        "active_rule_families": frozenset(DisclosureRuleFamily),
    }
    base.update(overrides)
    return CohortPolicy(**base)  # type: ignore[arg-type]


def _history(
    entries: tuple[ReleaseHistoryEntry, ...] = (), available: bool = True
) -> ReleaseHistory:
    return ReleaseHistory(
        organization_scope=SCOPE,
        window_start=T0 - REFERENCE_POLICY.cumulative_release_window,
        window_end=T0,
        entries=entries,
        available=available,
    )


def _entry(release_class: str = "membership_statistics") -> ReleaseHistoryEntry:
    return ReleaseHistoryEntry(
        release_id=uuid4(),
        organization_scope=SCOPE,
        release_class=release_class,
        cohort_dimensions=frozenset({"region"}),
        cohort_keys=frozenset({"region:north"}),
        released_at=T0 - timedelta(days=1),
        release_reference="release:1",
    )


class TestCohortPolicy:
    def test_at_least_two_rule_families_are_required(self) -> None:
        """A single small-cell check is the rule everyone implements and
        the one that alone protects least."""
        with pytest.raises(DisclosureThresholdFailedError):
            _cohort_policy(active_rule_families=frozenset({DisclosureRuleFamily.COHORT_THRESHOLD}))

    def test_the_minimum_cohort_size_cannot_go_below_the_floor(self) -> None:
        """The floor is independent of the policy, so a policy file that
        set a threshold of one could not make small-cell release
        legal."""
        with pytest.raises((DisclosureThresholdFailedError, DisclosurePolicyViolationError)):
            _cohort_policy(minimum_cohort_size=1)


class TestRuleFamilies:
    def test_a_cohort_below_the_threshold_fails(self) -> None:
        rule = evaluate_cohort_threshold(
            [
                CohortObservation(
                    cohort_key="region:north", size=2, dimensions=frozenset({"region"})
                )
            ],
            _cohort_policy(),
        )
        assert not rule.passed

    def test_cohorts_at_or_above_the_threshold_pass(self) -> None:
        rule = evaluate_cohort_threshold(
            [
                CohortObservation(
                    cohort_key="region:north",
                    size=REFERENCE_POLICY.cohort_threshold,
                    dimensions=frozenset({"region"}),
                )
            ],
            _cohort_policy(),
        )
        assert rule.passed

    def test_the_complement_of_a_suppressed_cell_is_recoverable(self) -> None:
        """Suppressing one small cell out of a known total leaves its
        value derivable by subtraction. This is the rule a
        threshold-only implementation misses."""
        cohorts = [
            CohortObservation(cohort_key="a", size=97, dimensions=frozenset({"d"})),
            CohortObservation(cohort_key="b", size=3, dimensions=frozenset({"d"})),
        ]
        rule = evaluate_complement_protection(
            cohorts,
            total=100,
            cohort_policy=_cohort_policy(),
            suppressed=frozenset({"b"}),
        )
        assert not rule.passed

    def test_repeated_similar_queries_indicate_differencing(self) -> None:
        rule = evaluate_differencing(
            similar_query_digests=["d" * 64] * (REFERENCE_POLICY.repeated_query_limit + 1),
            policy=REFERENCE_POLICY,
        )
        assert not rule.passed

    def test_a_single_query_is_not_differencing(self) -> None:
        rule = evaluate_differencing(similar_query_digests=["d" * 64], policy=REFERENCE_POLICY)
        assert rule.passed


class TestCumulativeModel:
    def test_the_model_is_bounded_by_a_window_and_a_limit(self) -> None:
        """`OD-P12-08`: bounded, not open-ended. Both bounds come from
        the versioned policy."""
        assert REFERENCE_POLICY.cumulative_release_window > timedelta(0)
        assert REFERENCE_POLICY.cumulative_release_limit >= 1

    def test_releases_past_the_limit_fail_the_rule(self) -> None:
        entries = tuple(_entry() for _ in range(REFERENCE_POLICY.cumulative_release_limit + 1))
        rule = evaluate_cumulative(
            cohorts=[
                CohortObservation(
                    cohort_key="region:north", size=10, dimensions=frozenset({"region"})
                )
            ],
            release_class="membership_statistics",
            history=_history(entries),
            policy=REFERENCE_POLICY,
        )
        assert not rule.passed

    def test_an_unavailable_history_fails_closed(self) -> None:
        """The important half of `OD-P12-08`. A history nobody could read
        is not an empty history."""
        with pytest.raises(ReleaseHistoryUnavailableError):
            _history(available=False).assert_available()

    def test_only_overlapping_releases_count(self) -> None:
        history = _history((_entry("other_statistics"),))
        assert history.overlapping(frozenset({"region:north"}), "membership_statistics") == ()


class TestSuppression:
    def test_a_small_cohort_without_suppression_is_refused(self) -> None:
        cohorts = [CohortObservation(cohort_key="a", size=1, dimensions=frozenset({"d"}))]
        with pytest.raises(DisclosureSuppressionRequiredError):
            assert_suppression_applied(cohorts, cohort_policy=_cohort_policy(), suppression=None)

    def test_a_small_cohort_with_suppression_passes(self) -> None:
        cohorts = [CohortObservation(cohort_key="a", size=1, dimensions=frozenset({"d"}))]
        assert_suppression_applied(
            cohorts,
            cohort_policy=_cohort_policy(),
            suppression=SuppressionDecision(
                decision_id=uuid4(),
                suppressed_cohorts=frozenset({"a"}),
                rule_reference="rule:threshold",
                decided_at=T0,
            ),
        )


class TestRelease:
    def _assessment(self, *, passing: bool) -> DisclosureRiskAssessment:
        rules = tuple(
            DisclosureRule(family=family, passed=passing, detail_reference="detail:1")
            for family in DisclosureRuleFamily
        )
        return DisclosureRiskAssessment(
            assessment_id=uuid4(),
            organization_scope=SCOPE,
            release_class="membership_statistics",
            assessed_at=T0,
            reviewer_reference="actor:reviewer",
            rules=rules,
            suppression=None,
            release_history_reference="history:1",
            policy_version="pack-12-disclosure/v1",
        )

    def test_a_passing_assessment_permits_release(self) -> None:
        assert_release_permitted(self._assessment(passing=True), cohort_policy=_cohort_policy())

    def test_a_failing_assessment_refuses_without_an_exception(self) -> None:
        with pytest.raises(
            (
                DisclosureThresholdFailedError,
                DisclosureComplementRecoverableError,
                DisclosureCumulativeReleaseRiskError,
                DisclosureExceptionNotApprovedError,
            )
        ):
            assert_release_permitted(
                self._assessment(passing=False), cohort_policy=_cohort_policy()
            )

    def test_an_unapproved_exception_does_not_permit(self) -> None:
        request = DisclosureExceptionRequest(
            exception_id=uuid4(),
            release_class="membership_statistics",
            requester_reference="actor:requester",
            justification_reference="j",
            requested_at=T0,
        )
        decision = DisclosureExceptionDecision(
            decision_id=uuid4(),
            exception_id=request.exception_id,
            reviewer_reference="actor:reviewer",
            approved=False,
            decided_at=T0,
            valid_until=T0 + timedelta(days=7),
            reason=ReasonCoded(
                reason_code="DISCLOSURE_EXCEPTION_NOT_APPROVED",
                authority_reference="auth:1",
            ),
        )
        with pytest.raises(DisclosureExceptionNotApprovedError):
            decision.assert_usable(T0, request)

    def test_an_expired_exception_does_not_permit(self) -> None:
        """An exception without an expiry would be a permanent hole in
        the control it excepts."""
        request = DisclosureExceptionRequest(
            exception_id=uuid4(),
            release_class="membership_statistics",
            requester_reference="actor:requester",
            justification_reference="j",
            requested_at=T0,
        )
        decision = DisclosureExceptionDecision(
            decision_id=uuid4(),
            exception_id=request.exception_id,
            reviewer_reference="actor:reviewer",
            approved=True,
            decided_at=T0,
            valid_until=T0 + timedelta(days=1),
            reason=ReasonCoded(
                reason_code="DISCLOSURE_EXCEPTION_EXPIRED", authority_reference="auth:1"
            ),
        )
        decision.assert_usable(T0, request)
        with pytest.raises(DisclosureExceptionExpiredError):
            decision.assert_usable(T0 + timedelta(days=2), request)


class TestPublicationAuthority:
    def test_raw_access_is_not_publication_authority(self) -> None:
        """`P12-SDC-010`: being able to read the underlying data is not
        being allowed to publish a statistic derived from it."""
        with pytest.raises(DisclosurePublicationAuthorityMissingError):
            assert_publication_authority(
                has_raw_access=True,
                has_publication_authority=False,
                purpose=Purpose.STATISTICAL_RELEASE,
            )
        assert_publication_authority(
            has_raw_access=True,
            has_publication_authority=True,
            purpose=Purpose.STATISTICAL_RELEASE,
        )


class TestRuleFamilyResolution:
    def test_an_unknown_family_is_refused(self) -> None:
        with pytest.raises(UnknownStatusError):
            resolve_rule_family("vibes")

    def test_every_declared_family_resolves(self) -> None:
        for family in DisclosureRuleFamily:
            assert resolve_rule_family(family.value) is family
