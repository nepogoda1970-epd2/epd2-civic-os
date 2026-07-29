"""Bounded context 2 of 3 - authorization-aware search (ADR-064,
ADR-065).

One sentence governs the module: **search never expands source
authorization** (`P12-SRCH-003`). A participant may find only what they
could open directly.

Enforcement is at four points, not one (`P12-SRCH-004`), because each
fails differently:

1. **index admission** - is this class allowed in this index at all;
2. **field projection** - is this field allowed in the index;
3. **query admission** - scope present, purpose valid, mode permitted;
4. **result retrieval** - source authorization re-resolved against
   *current* state (`P12-SRCH-005`).

Index-time filtering alone is the stale-ACL failure. Query-time filtering
alone means restricted content sat in a shared index. Both, plus the
leakage rules below, is the design.

The leakage channels are handled individually because they leak
individually: counts over the authorized set only (`P12-SRCH-007`),
facets and suggestions disclosing nothing restricted (`P12-SRCH-008`),
snippets bound by the source's restriction (`P12-SRCH-006`), cache keys
carrying the authorization context (`P12-SRCH-009`).

`OD-P12-02` is resolved here: there is no separate investigative search
mode. Two modes exist - `GENERAL_AUTHORIZED` and `SCOPED_DOMAIN` - and
investigation is a `Purpose` inside the scoped mode. It narrows like
every other purpose and expands nothing.

**No voting reference type exists in this module** (`P12-VOTE-002`).
A final certified result can appear only as an approved publication
rendition reference carried on an ordinary indexable record, never as a
tally or ballot type of its own.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol
from uuid import UUID

from epd2_privileged_access_service.classification import (
    ClassificationDecision,
    EnforcementTier,
    SourceClassification,
    resolve_classification,
)
from epd2_privileged_access_service.domain import (
    OrganizationalScopeRef,
    Purpose,
    deterministic_digest,
    require_text,
    require_timezone,
)
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


class SearchMode(StrEnum):
    """The two governed modes. There is no third (`P12-SRCH-001`)."""

    GENERAL_AUTHORIZED = "general_authorized"
    SCOPED_DOMAIN = "scoped_domain"


#: Domains whose material is never admitted to any PACK-12 index,
#: whatever its classification says. Belt and braces alongside the
#: `T4-prohibited` tier: a domain marked here is refused even if a
#: classification were mis-mapped (`P12-HCD-003`, `P12-VOTE-001`).
ABSOLUTELY_EXCLUDED_DOMAINS: frozenset[str] = frozenset(
    {
        "ballot",
        "ballot_content",
        "vote",
        "vote_envelope",
        "tally",
        "intermediate_tally",
        "partial_tally",
        "uncertified_tally",
        "voting_credential",
        "whistleblower",
        "key_material",
        "privileged_session_secret",
    }
)

#: Domains whose material is uncertified voting result material
#: specifically. Separated from the set above so the refusal names what
#: actually happened (`P12-VOTE-006`).
UNCERTIFIED_RESULT_DOMAINS: frozenset[str] = frozenset(
    {"intermediate_tally", "partial_tally", "uncertified_tally"}
)


@dataclass(frozen=True, slots=True)
class IndexFieldPolicy:
    """Which fields of a record class may enter an index."""

    record_class: str
    indexable_fields: frozenset[str]
    snippet_fields: frozenset[str] = frozenset()
    facet_fields: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        require_text(self.record_class, "record_class")
        if not self.snippet_fields <= self.indexable_fields:
            raise IndexPolicyViolationError("snippet fields must be a subset of indexable fields")
        if not self.facet_fields <= self.indexable_fields:
            raise IndexPolicyViolationError("facet fields must be a subset of indexable fields")

    def assert_field_indexable(self, field_name: str) -> None:
        if field_name not in self.indexable_fields:
            raise IndexPolicyViolationError(
                f"field {field_name!r} is not indexable for record class {self.record_class!r}"
            )


@dataclass(frozen=True, slots=True)
class IndexPolicy:
    """Which classes and tiers an index admits, at a recorded version."""

    index_name: str
    policy_version: str
    mode: SearchMode
    field_policies: tuple[IndexFieldPolicy, ...]
    admitted_tiers: frozenset[EnforcementTier]

    def __post_init__(self) -> None:
        require_text(self.index_name, "index_name")
        require_text(self.policy_version, "policy_version")
        if EnforcementTier.T4_PROHIBITED in self.admitted_tiers:
            raise IndexPolicyViolationError(
                "no index policy may admit the prohibited tier; there is no configuration "
                "that moves a record out of it"
            )
        if self.mode is SearchMode.GENERAL_AUTHORIZED and not self.admitted_tiers <= frozenset(
            {EnforcementTier.T0_OPEN, EnforcementTier.T0_OPEN_AUTHORITATIVE}
        ):
            raise IndexPolicyViolationError(
                "the general index admits only open tiers; scoped material needs a scoped index"
            )

    def field_policy_for(self, record_class: str) -> IndexFieldPolicy:
        for policy in self.field_policies:
            if policy.record_class == record_class:
                return policy
        raise IndexPolicyViolationError(
            f"record class {record_class!r} has no field policy in index {self.index_name!r}"
        )


def assert_indexable(
    *,
    domain: str,
    classification: ClassificationDecision,
    index_policy: IndexPolicy,
) -> None:
    """Enforcement point 1: index admission.

    The domain check runs before the tier check so that voting material
    reports the voting refusal rather than a generic tier refusal - the
    two mean very different things to whoever reads the audit trail."""
    require_text(domain, "domain")
    if domain in UNCERTIFIED_RESULT_DOMAINS:
        raise SearchUncertifiedResultProhibitedError(
            f"domain {domain!r} is intermediate or non-certified tally material and is never "
            "indexed; a final certified result is published by the authoritative voting and "
            "result-certification domain, not indexed here"
        )
    if domain in ABSOLUTELY_EXCLUDED_DOMAINS:
        raise SearchBallotContentProhibitedError(
            f"domain {domain!r} is absolutely excluded from every PACK-12 index"
        )
    if classification.tier is EnforcementTier.T4_PROHIBITED:
        raise SearchBallotContentProhibitedError("material at the prohibited tier is never indexed")
    if classification.tier not in index_policy.admitted_tiers:
        raise HighlyConfidentialDomainExcludedError(
            f"tier {classification.tier!s} is not admitted to index {index_policy.index_name!r}"
        )


@dataclass(frozen=True, slots=True)
class SearchScope:
    """The organizational and domain bounds of a query."""

    organization_scope: OrganizationalScopeRef
    domains: frozenset[str]

    def __post_init__(self) -> None:
        if not self.domains:
            raise SearchScopeUndeterminedError("a search scope must name at least one domain")


@dataclass(frozen=True, slots=True)
class QueryRequest:
    """One query.

    `query_digest` rather than the query string: a query can itself
    contain personal data, and an audit trail of raw queries would be a
    second copy of exactly what the search rules exist to protect."""

    query_id: UUID
    requester_reference: str
    mode: SearchMode
    scope: SearchScope
    purpose: Purpose
    query_digest: str
    submitted_at: datetime
    grant_reference: UUID | None = None

    def __post_init__(self) -> None:
        require_text(self.requester_reference, "requester_reference")
        require_text(self.query_digest, "query_digest")
        require_timezone(self.submitted_at, context="QueryRequest.submitted_at")


#: Which purposes each mode admits. `INVESTIGATION` is scoped-only: that
#: is the whole of `OD-P12-02`'s resolution - investigation is a purpose,
#: not a wider mode.
_MODE_PURPOSES: dict[SearchMode, frozenset[Purpose]] = {
    SearchMode.GENERAL_AUTHORIZED: frozenset(
        {Purpose.OPERATIONS, Purpose.TRANSPARENCY_PUBLICATION}
    ),
    SearchMode.SCOPED_DOMAIN: frozenset(
        {
            Purpose.OPERATIONS,
            Purpose.INVESTIGATION,
            Purpose.INCIDENT_RESPONSE,
            Purpose.COMPLIANCE_REVIEW,
            Purpose.AUDIT,
            Purpose.DATA_SUBJECT_REQUEST,
            Purpose.LEGAL_PROCEEDING,
        }
    ),
}

#: Purposes that may only be exercised under an explicit privileged
#: grant, with their own reason code and audit trail (`P12-SRCH-002`).
GRANT_REQUIRED_PURPOSES: frozenset[Purpose] = frozenset(
    {Purpose.INVESTIGATION, Purpose.LEGAL_PROCEEDING}
)


def assert_query_admissible(
    request: QueryRequest, *, caller_scope: OrganizationalScopeRef | None
) -> None:
    """Enforcement point 3: query admission (`P12-SRCH-010`)."""
    if caller_scope is None:
        raise SearchScopeUndeterminedError(
            "no organizational scope was resolvable for the query - default deny"
        )
    if caller_scope.organization_id != request.scope.organization_scope.organization_id:
        raise SearchOrganizationMismatchError(
            "the query reaches outside the requester's organizational scope"
        )
    admitted = _MODE_PURPOSES.get(request.mode, frozenset())
    if request.purpose not in admitted:
        raise SearchPurposeMismatchError(
            f"purpose {request.purpose!s} is not admitted by mode {request.mode!s}"
        )
    if request.purpose in GRANT_REQUIRED_PURPOSES and request.grant_reference is None:
        raise SearchModeNotPermittedError(
            f"purpose {request.purpose!s} requires an explicit privileged grant"
        )
    for domain in request.scope.domains:
        if domain in UNCERTIFIED_RESULT_DOMAINS:
            raise SearchUncertifiedResultProhibitedError(f"domain {domain!r} may never be searched")
        if domain in ABSOLUTELY_EXCLUDED_DOMAINS:
            raise SearchBallotContentProhibitedError(f"domain {domain!r} may never be searched")


class SourceAuthorizationPort(Protocol):
    """Re-resolution of source authorization at result time.

    This is the port that closes the stale-ACL gap (`P12-SRCH-005`). It
    is deliberately a *port*: the index cannot answer it, because the
    index is what might be stale."""

    def may_open(
        self,
        *,
        requester_reference: str,
        record_reference: str,
        domain: str,
        scope: OrganizationalScopeRef,
        at: datetime,
    ) -> bool: ...

    def is_retrievable(self, *, record_reference: str, at: datetime) -> bool:
        """Whether the record still exists and has not been deleted,
        expired or had access revoked (`P12-SRCH-012`)."""
        ...


@dataclass(frozen=True, slots=True)
class IndexedRecord:
    """One record as it sits in the reference index."""

    record_reference: str
    domain: str
    record_class: str
    organization_scope: OrganizationalScopeRef
    classification: ClassificationDecision
    fields: dict[str, str]
    indexed_at: datetime
    authorization_version: int = 1

    def __post_init__(self) -> None:
        require_text(self.record_reference, "record_reference")
        require_text(self.domain, "domain")
        require_timezone(self.indexed_at, context="IndexedRecord.indexed_at")


@dataclass(frozen=True, slots=True)
class SearchResultReference:
    """A result: a reference plus a policy-bounded snippet.

    Never the record (`P12-SRCH-016`). `snippet` is `None` whenever the
    source restriction forbids one, and the caller cannot tell the
    difference between "no snippet allowed" and "no snippet matched" -
    which is intentional."""

    record_reference: str
    domain: str
    organization_scope: OrganizationalScopeRef
    snippet: str | None = None

    def to_payload(self) -> dict[str, object]:
        return {
            "record_reference": self.record_reference,
            "domain": self.domain,
            "organization_id": str(self.organization_scope.organization_id),
            "snippet_present": self.snippet is not None,
        }


@dataclass(frozen=True, slots=True)
class QueryDecision:
    """The outcome of one query.

    `authorized_count` counts only what the requester may see
    (`P12-SRCH-007`); `suppressed_band` reports withheld results as a
    band rather than an exact number, because an exact suppression count
    is itself a disclosure of how many restricted records matched."""

    query_id: UUID
    authorized: bool
    results: tuple[SearchResultReference, ...]
    authorized_count: int
    suppressed_band: str
    facets: dict[str, tuple[str, ...]]
    policy_version: str
    reason_code: str | None = None

    def to_payload(self) -> dict[str, object]:
        return {
            "query_id": str(self.query_id),
            "authorized": self.authorized,
            "authorized_count": self.authorized_count,
            "suppressed_band": self.suppressed_band,
            "facet_names": sorted(self.facets),
            "policy_version": self.policy_version,
            "reason_code": self.reason_code,
        }


def suppression_band(count: int) -> str:
    """Bucket a suppression count. Bands, never exact numbers."""
    if count == 0:
        return "none"
    if count <= 5:
        return "1-5"
    if count <= 25:
        return "6-25"
    return "26+"


@dataclass(frozen=True, slots=True)
class SearchCacheKey:
    """A cache key that carries the whole authorization context.

    `P12-SRCH-009`: two subjects with the same query must not share an
    entry, and an entry must not outlive the policy version it was
    computed under."""

    requester_reference: str
    organization_id: str
    mode: str
    purpose: str
    query_digest: str
    policy_version: str
    authorization_version: int

    def fingerprint(self) -> str:
        return deterministic_digest(
            self.requester_reference,
            self.organization_id,
            self.mode,
            self.purpose,
            self.query_digest,
            self.policy_version,
            str(self.authorization_version),
        )


def assert_cache_context_matches(stored: SearchCacheKey, presented: SearchCacheKey) -> None:
    if stored.fingerprint() != presented.fingerprint():
        raise SearchCacheContextMismatchError(
            "the cache entry was computed under a different authorization context"
        )


def execute_query(
    request: QueryRequest,
    candidates: Sequence[IndexedRecord],
    *,
    caller_scope: OrganizationalScopeRef | None,
    index_policy: IndexPolicy,
    port: SourceAuthorizationPort,
    at: datetime,
) -> QueryDecision:
    """Run one query through enforcement points 3 and 4.

    Every candidate is re-resolved against the source's current
    authorization; nothing is trusted from the index but the pointer.
    A candidate whose retrievability cannot be established is refused
    rather than returned, which is why `is_retrievable` is consulted
    before `may_open`."""
    assert_query_admissible(request, caller_scope=caller_scope)
    authorized: list[SearchResultReference] = []
    suppressed = 0
    facet_values: dict[str, set[str]] = {}

    for record in candidates:
        if record.domain not in request.scope.domains:
            continue
        if record.organization_scope.organization_id != (
            request.scope.organization_scope.organization_id
        ):
            suppressed += 1
            continue
        if record.classification.tier is EnforcementTier.T4_PROHIBITED:
            raise SearchBallotContentProhibitedError(
                "prohibited-tier material reached the query path; this is an incident"
            )
        if record.classification.tier not in index_policy.admitted_tiers:
            suppressed += 1
            continue
        if not port.is_retrievable(record_reference=record.record_reference, at=at):
            suppressed += 1
            continue
        may_open = port.may_open(
            requester_reference=request.requester_reference,
            record_reference=record.record_reference,
            domain=record.domain,
            scope=request.scope.organization_scope,
            at=at,
        )
        if not may_open:
            suppressed += 1
            continue

        field_policy = index_policy.field_policy_for(record.record_class)
        snippet = _snippet_for(record, field_policy)
        authorized.append(
            SearchResultReference(
                record_reference=record.record_reference,
                domain=record.domain,
                organization_scope=record.organization_scope,
                snippet=snippet,
            )
        )
        for facet_field in field_policy.facet_fields:
            value = record.fields.get(facet_field)
            if value is not None:
                facet_values.setdefault(facet_field, set()).add(value)

    return QueryDecision(
        query_id=request.query_id,
        authorized=True,
        results=tuple(authorized),
        authorized_count=len(authorized),
        suppressed_band=suppression_band(suppressed),
        facets={name: tuple(sorted(values)) for name, values in facet_values.items()},
        policy_version=index_policy.policy_version,
    )


def _snippet_for(record: IndexedRecord, field_policy: IndexFieldPolicy) -> str | None:
    """A snippet, or `None` where the source restriction forbids one.

    Restricted tiers get no snippet at all (`P12-SRCH-006`): a snippet is
    content, and a tier that keeps content out of the index keeps it out
    of the excerpt too."""
    if record.classification.tier in {
        EnforcementTier.T2_CONFIDENTIAL,
        EnforcementTier.T2_CASE_METADATA,
        EnforcementTier.T3_RESTRICTED,
        EnforcementTier.T4_PROHIBITED,
    }:
        return None
    for name in sorted(field_policy.snippet_fields):
        value = record.fields.get(name)
        if value:
            return value[:120]
    return None


def assert_source_authorized(
    *, requester_reference: str, record_reference: str, allowed: bool
) -> None:
    """Enforcement point 4, as an explicit assertion for callers that
    resolve authorization themselves."""
    if not allowed:
        raise SearchSourceAuthorizationDeniedError(
            f"{requester_reference} could not open {record_reference} directly, so search "
            "must not surface it"
        )


def assert_index_authorization_fresh(*, index_version: int, source_version: int) -> None:
    """Raise if the index's authorization view cannot be reconciled with
    the source's current one (`P12-SRCH-005`)."""
    if index_version != source_version:
        raise SearchIndexAuthorizationStaleError(
            "the index authorization view is stale and could not be reconciled; the result "
            "is refused rather than served from the stale view"
        )


@dataclass(frozen=True, slots=True)
class IndexRemovalEvidence:
    """Proof that a record left the index (`P12-SRCH-015`)."""

    removal_id: UUID
    record_reference: str
    organization_scope: OrganizationalScopeRef
    removed_at: datetime
    source_decision_reference: str
    reason_code: str

    def __post_init__(self) -> None:
        require_timezone(self.removed_at, context="IndexRemovalEvidence.removed_at")
        require_text(self.source_decision_reference, "source_decision_reference")

    def to_payload(self) -> dict[str, object]:
        return {
            "removal_id": str(self.removal_id),
            "record_reference": self.record_reference,
            "organization_id": str(self.organization_scope.organization_id),
            "removed_at": self.removed_at.isoformat(),
            "source_decision_reference": self.source_decision_reference,
            "reason_code": self.reason_code,
        }


def classification_for_domain(domain: str, source: SourceClassification) -> ClassificationDecision:
    """Resolve a record's classification, refusing prohibited domains
    before the mapping is even consulted."""
    if domain in ABSOLUTELY_EXCLUDED_DOMAINS or domain in UNCERTIFIED_RESULT_DOMAINS:
        return resolve_classification(SourceClassification.ABSOLUTELY_EXCLUDED)
    return resolve_classification(source)
