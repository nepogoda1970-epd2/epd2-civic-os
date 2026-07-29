"""Authorization-aware search (`P12-SRCH-*`, `P12-HCD-*`, ADR-064)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from _privileged_builders import StubSourceAuthorizationPort

from epd2_privileged_access_service.classification import (
    EnforcementTier,
    SourceClassification,
    resolve_classification,
)
from epd2_privileged_access_service.domain import OrganizationalScopeRef, Purpose
from epd2_privileged_access_service.exceptions import (
    HighlyConfidentialDomainExcludedError,
    IndexPolicyViolationError,
    SearchBallotContentProhibitedError,
    SearchCacheContextMismatchError,
    SearchIndexAuthorizationStaleError,
    SearchModeNotPermittedError,
    SearchOrganizationMismatchError,
    SearchPurposeMismatchError,
    SearchScopeUndeterminedError,
    SearchSourceAuthorizationDeniedError,
    SearchUncertifiedResultProhibitedError,
)
from epd2_privileged_access_service.search import (
    ABSOLUTELY_EXCLUDED_DOMAINS,
    GRANT_REQUIRED_PURPOSES,
    UNCERTIFIED_RESULT_DOMAINS,
    IndexedRecord,
    IndexFieldPolicy,
    IndexPolicy,
    QueryRequest,
    SearchCacheKey,
    SearchMode,
    SearchScope,
    assert_cache_context_matches,
    assert_index_authorization_fresh,
    assert_indexable,
    assert_query_admissible,
    assert_source_authorized,
    execute_query,
    suppression_band,
)

T0 = datetime(2026, 3, 1, 9, 0, tzinfo=UTC)
SCOPE = OrganizationalScopeRef(organization_id=uuid4())

FIELD_POLICY = IndexFieldPolicy(
    record_class="membership_record",
    indexable_fields=frozenset({"title", "reference"}),
    snippet_fields=frozenset({"title"}),
    facet_fields=frozenset({"reference"}),
)
POLICY = IndexPolicy(
    index_name="main",
    policy_version="pack-12-index/v1",
    mode=SearchMode.SCOPED_DOMAIN,
    field_policies=(FIELD_POLICY,),
    admitted_tiers=frozenset({EnforcementTier.T0_OPEN, EnforcementTier.T1_INTERNAL}),
)


def _record(
    reference: str = "rec:1",
    *,
    source: SourceClassification = SourceClassification.INTERNAL,
    scope: OrganizationalScopeRef = SCOPE,
    domain: str = "membership",
) -> IndexedRecord:
    return IndexedRecord(
        record_reference=reference,
        domain=domain,
        record_class="membership_record",
        organization_scope=scope,
        classification=resolve_classification(source),
        fields={"title": "Board minutes", "reference": "M-1"},
        indexed_at=T0,
    )


def _request(
    *,
    mode: SearchMode = SearchMode.SCOPED_DOMAIN,
    purpose: Purpose = Purpose.OPERATIONS,
    domains: frozenset[str] = frozenset({"membership"}),
    scope: OrganizationalScopeRef = SCOPE,
    grant_reference: object = None,
) -> QueryRequest:
    return QueryRequest(
        query_id=uuid4(),
        requester_reference="actor:subject",
        mode=mode,
        scope=SearchScope(organization_scope=scope, domains=domains),
        purpose=purpose,
        query_digest="d" * 64,
        submitted_at=T0,
        grant_reference=grant_reference,  # type: ignore[arg-type]
    )


class TestModes:
    def test_there_are_exactly_two_modes(self) -> None:
        """`P12-SRCH-001`: there is no third, and in particular no
        unrestricted investigative mode."""
        assert {m.value for m in SearchMode} == {"general_authorized", "scoped_domain"}

    def test_investigation_is_a_purpose_requiring_a_grant(self) -> None:
        """`OD-P12-02`'s resolution: investigation narrows the ordinary
        scoped search and expands nothing, and it needs an explicit
        grant."""
        assert Purpose.INVESTIGATION in GRANT_REQUIRED_PURPOSES
        with pytest.raises(SearchModeNotPermittedError):
            assert_query_admissible(_request(purpose=Purpose.INVESTIGATION), caller_scope=SCOPE)
        assert_query_admissible(
            _request(purpose=Purpose.INVESTIGATION, grant_reference=uuid4()),
            caller_scope=SCOPE,
        )

    def test_a_purpose_the_mode_does_not_admit_is_refused(self) -> None:
        with pytest.raises(SearchPurposeMismatchError):
            assert_query_admissible(
                _request(mode=SearchMode.GENERAL_AUTHORIZED, purpose=Purpose.LEGAL_PROCEEDING),
                caller_scope=SCOPE,
            )


class TestAdmission:
    def test_an_undetermined_scope_denies(self) -> None:
        with pytest.raises(SearchScopeUndeterminedError):
            assert_query_admissible(_request(), caller_scope=None)

    def test_a_query_reaching_outside_the_caller_scope_is_refused(self) -> None:
        other = OrganizationalScopeRef(organization_id=uuid4())
        with pytest.raises(SearchOrganizationMismatchError):
            assert_query_admissible(_request(scope=other), caller_scope=SCOPE)

    @pytest.mark.parametrize("domain", sorted(ABSOLUTELY_EXCLUDED_DOMAINS))
    def test_an_absolutely_excluded_domain_is_never_searchable(self, domain: str) -> None:
        with pytest.raises(
            (SearchBallotContentProhibitedError, SearchUncertifiedResultProhibitedError)
        ):
            assert_query_admissible(_request(domains=frozenset({domain})), caller_scope=SCOPE)

    def test_uncertified_result_domains_name_what_happened(self) -> None:
        """`P12-VOTE-006`: the refusal says "uncertified result", not
        "ballot content" - they are different facts."""
        for domain in sorted(UNCERTIFIED_RESULT_DOMAINS):
            with pytest.raises(SearchUncertifiedResultProhibitedError):
                assert_query_admissible(_request(domains=frozenset({domain})), caller_scope=SCOPE)


class TestIndexAdmission:
    def test_a_prohibited_tier_is_never_indexable(self) -> None:
        decision = resolve_classification(SourceClassification.ABSOLUTELY_EXCLUDED)
        with pytest.raises((SearchBallotContentProhibitedError, IndexPolicyViolationError)):
            assert_indexable(domain="membership", classification=decision, index_policy=POLICY)

    def test_a_tier_the_policy_does_not_admit_is_refused(self) -> None:
        decision = resolve_classification(SourceClassification.HIGHLY_CONFIDENTIAL)
        with pytest.raises(HighlyConfidentialDomainExcludedError):
            assert_indexable(domain="membership", classification=decision, index_policy=POLICY)

    def test_an_admitted_tier_passes(self) -> None:
        assert_indexable(
            domain="membership",
            classification=resolve_classification(SourceClassification.INTERNAL),
            index_policy=POLICY,
        )

    def test_a_field_outside_the_policy_is_refused(self) -> None:
        with pytest.raises(IndexPolicyViolationError):
            FIELD_POLICY.assert_field_indexable("home_address")


class TestExecution:
    def test_an_authorized_record_is_returned_with_a_snippet(self) -> None:
        decision = execute_query(
            _request(),
            [_record()],
            caller_scope=SCOPE,
            index_policy=POLICY,
            port=StubSourceAuthorizationPort(),
            at=T0,
        )
        assert decision.authorized_count == 1
        assert decision.results[0].snippet == "Board minutes"

    def test_a_record_the_requester_cannot_open_is_suppressed(self) -> None:
        """`P12-SRCH-005`: nothing is trusted from the index but the
        pointer. The index may be stale; the source is asked again."""
        decision = execute_query(
            _request(),
            [_record()],
            caller_scope=SCOPE,
            index_policy=POLICY,
            port=StubSourceAuthorizationPort(openable=frozenset()),
            at=T0,
        )
        assert decision.authorized_count == 0
        assert decision.suppressed_band == "1-5"

    def test_an_unretrievable_record_is_suppressed_before_may_open(self) -> None:
        decision = execute_query(
            _request(),
            [_record()],
            caller_scope=SCOPE,
            index_policy=POLICY,
            port=StubSourceAuthorizationPort(retrievable=frozenset()),
            at=T0,
        )
        assert decision.authorized_count == 0

    def test_a_foreign_scope_record_never_leaks(self) -> None:
        other = OrganizationalScopeRef(organization_id=uuid4())
        decision = execute_query(
            _request(),
            [_record(scope=other)],
            caller_scope=SCOPE,
            index_policy=POLICY,
            port=StubSourceAuthorizationPort(),
            at=T0,
        )
        assert decision.results == ()

    def test_prohibited_tier_material_on_the_query_path_is_an_incident(self) -> None:
        record = _record(source=SourceClassification.ABSOLUTELY_EXCLUDED)
        with pytest.raises(SearchBallotContentProhibitedError):
            execute_query(
                _request(),
                [record],
                caller_scope=SCOPE,
                index_policy=POLICY,
                port=StubSourceAuthorizationPort(),
                at=T0,
            )

    def test_restricted_tiers_get_no_snippet(self) -> None:
        """`P12-SRCH-006`: a snippet is content. A tier that keeps content
        out of the index keeps it out of the excerpt too."""
        permissive = IndexPolicy(
            index_name="main",
            policy_version="v1",
            mode=SearchMode.SCOPED_DOMAIN,
            field_policies=(FIELD_POLICY,),
            admitted_tiers=frozenset({EnforcementTier.T2_CONFIDENTIAL}),
        )
        decision = execute_query(
            _request(),
            [_record(source=SourceClassification.CONFIDENTIAL_REGULATED)],
            caller_scope=SCOPE,
            index_policy=permissive,
            port=StubSourceAuthorizationPort(),
            at=T0,
        )
        assert decision.results[0].snippet is None


class TestSuppressionBands:
    @pytest.mark.parametrize(
        ("count", "band"), [(0, "none"), (1, "1-5"), (5, "1-5"), (6, "6-25"), (99, "26+")]
    )
    def test_bands_never_report_an_exact_count(self, count: int, band: str) -> None:
        """An exact suppression count is itself a disclosure of how many
        restricted records matched."""
        assert suppression_band(count) == band


class TestCachePartitioning:
    def _key(self, **overrides: object) -> SearchCacheKey:
        base: dict[str, object] = {
            "requester_reference": "actor:a",
            "organization_id": str(SCOPE.organization_id),
            "mode": "scoped_domain",
            "purpose": "operations",
            "query_digest": "d" * 64,
            "policy_version": "v1",
            "authorization_version": 1,
        }
        base.update(overrides)
        return SearchCacheKey(**base)  # type: ignore[arg-type]

    @pytest.mark.parametrize(
        "field",
        [
            "requester_reference",
            "organization_id",
            "mode",
            "purpose",
            "policy_version",
            "authorization_version",
        ],
    )
    def test_every_context_field_partitions_the_cache(self, field: str) -> None:
        """`P12-SRCH-009`: a cache keyed by the query alone serves one
        requester's results to another. All seven fields are in the
        fingerprint, and each one alone changes it."""
        base = self._key()
        changed = self._key(**{field: 2 if field == "authorization_version" else "different"})
        assert base.fingerprint() != changed.fingerprint()

    def test_a_mismatched_context_is_refused_rather_than_served(self) -> None:
        with pytest.raises(SearchCacheContextMismatchError):
            assert_cache_context_matches(self._key(), self._key(purpose="audit"))


class TestFreshness:
    def test_a_stale_index_authorization_view_refuses(self) -> None:
        with pytest.raises(SearchIndexAuthorizationStaleError):
            assert_index_authorization_fresh(index_version=1, source_version=2)

    def test_source_denial_is_reported_as_source_denial(self) -> None:
        with pytest.raises(SearchSourceAuthorizationDeniedError):
            assert_source_authorized(
                requester_reference="actor:a", record_reference="rec:1", allowed=False
            )
