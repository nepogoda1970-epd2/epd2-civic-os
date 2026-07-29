# ADR-064: Authorization-aware search with query-time re-resolution

## Status

`proposed`

## Date

2026-07-29

## Context

`AGR-24` requires search to be governed by purpose and record class.
`FIR-INV-007` requires scoped access, reason codes, purpose, DLP checks,
rate limits, approval where required and audit evidence for search and
export alike. `FIR-INV-013` requires organizational isolation from the
beginning of the data model.

Every prior pack has kept its read model non-authoritative and derived:
PACK-10's `projections` module states it in a property that cannot be
constructed `True`, and PACK-04's transparency ledger is a publication
surface, not a source. A search index is the same kind of object, with
one additional hazard: it aggregates across domains, so a single mistake
in it leaks from everywhere at once.

## Problem

1. An index built with an authorization snapshot answers from that
   snapshot. When authorization narrows, the index keeps answering from
   the wider view until it converges — and "until it converges" is an
   access-control gap measured in whatever the reindex latency happens to
   be.
2. Search leaks through channels that are not the result list: counts,
   facets, autocomplete, snippets, and caches shared across subjects.
   Each is a legitimate feature and each is an oracle.
3. If search returns anything the requester could not open directly, the
   index has become a second, weaker authorization path — and the weaker
   path is the one an attacker uses.

## Considered options

- **Option A — index-time filtering only.** Cheapest at query time and
  wrong: it is exactly the stale-ACL failure (T-P12-09). Rejected.
- **Option B — query-time filtering only.** Correct on authorization and
  wrong on containment: restricted content sits in a shared index where
  an index-level compromise reaches everything. Rejected.
- **Option C — enforcement at four points: index admission, field
  projection, query admission, and result retrieval with re-resolution of
  source authorization against current state — plus explicit rules for
  counts, facets, snippets and caches.** **Chosen.**

## Decision

Enforcement operates on a **derived enforcement tier** mapped from the
authoritative source classification, never on a classification PACK-12
invents. `P12-CLS-001` keeps the source classification authoritative;
`P12-CLS-002` makes the tier a derived policy abstraction with no
authority of its own; `P12-CLS-005` fails closed on an unmapped value.
The mapping table is `PACK-12-DATA-SEARCH-EXPORT-MATRIX.md` section 2.

`P12-SRCH-003` is the governing sentence: **search never expands source
authorization**. A participant may find only what they may open.

Enforcement is at four points, not one (`P12-SRCH-004`), and result
retrieval re-resolves authorization against the source's current state
(`P12-SRCH-005`). The index is not authoritative and a result creates no
legal effect (`P12-SRCH-014`).

The leakage channels are addressed individually because they fail
individually: counts computed over the authorized set only
(`P12-SRCH-007`); facets, autocomplete, aggregations and suggestions
disclosing nothing restricted (`P12-SRCH-008`); snippets bound by the
source's restriction (`P12-SRCH-006`); cache keys including the effective
authorization context (`P12-SRCH-009`).

`SEARCH_RESULT_SUPPRESSED` exists for the audit trail, not for the
response body: from the requester's side, suppressed and absent are
deliberately indistinguishable.

At least two modes are defined — general authorized search and
scoped/domain search. A third, privileged investigative search, MAY be
defined and if defined is a purpose-scoped governed operation with its
own grant, approval and session evidence; never an ambient capability.
Whether it is defined at all is `OD-P12-02`, deliberately left open.

## Consequences

Easier: one rule to check any search feature against; leakage channels
enumerated rather than discovered; deletion and revocation actually
remove findability.

Harder: query-time re-resolution costs latency on every result, and there
will be pressure to cache the authorization decision itself. That
pressure is the threat. The implementation may cache, but the cache key
must carry the authorization context, and the entry must not outlive the
authorization it encodes.

## Security impact

Addresses T-P12-09 (stale ACL), T-P12-10 (count/facet/snippet leakage)
and T-P12-11 (cache cross-contamination). Timing and latency side
channels are **not** addressed and are stated as residual.

## Data impact

Introduces `IndexPolicy`, `IndexFieldPolicy`, `SearchScope`,
`SearchPurpose`, `QueryRequest`, `QueryDecision`, `QueryAudit`,
`SearchResultReference`, `IndexProjectionReference`, `ReindexRequest`,
`IndexRemovalEvidence`. `SearchResultReference` carries a reference and a
policy-bounded snippet, never the record.

Whether `QueryAudit` lives in `audit-core` or in the PACK-12 context is
`OD-P12-06`, open.

## Migration impact

None in this round. The real index is PACK-13's; this ADR fixes the
contract it must satisfy.

## Reversibility

Reversible with cost at the mode level; the four enforcement points are
not sensibly reversible without reintroducing the threats they exist for.

## Related canon version

Authored against canon `0.8.0`. Proposes no canon version bump.
