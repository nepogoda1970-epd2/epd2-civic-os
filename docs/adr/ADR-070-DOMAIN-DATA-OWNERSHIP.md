# ADR-070 — Domain data ownership

**Status:** accepted
**Specification round:** PACK-13 — Production Data Plane & Contract Evolution (specification and ADR only)
**Implementation round:** PACK-13 Implementation Candidate · **Repository version:** `0.13.0` · **Canon version:** unchanged at `0.8.0`

The decision below is implemented in **reference form** by
`services/data-plane-service`. Reference form means the contracts, the
governed workflows and the refusals are real and tested; the production
data plane is not deployed and is not claimed. **NOT PASS. NOT PRODUCTION
READY. NOT LEGALLY ACTIVATED.** See
`docs/handover/PACK-13-IMPLEMENTATION-CANDIDATE-REPORT.md` and
`docs/handover/PACK-13-KNOWN-LIMITATIONS.md`.

## Context

Once the data is in one engine, "who may read this table" becomes a
question the engine will answer permissively unless someone decides
otherwise. Cross-domain reads are the most common way a well-designed
architecture becomes a distributed monolith, and they are invisible in code
review because the query is correct, fast and works.

Canon §22 already assigns entity ownership at the domain level. This ADR
carries that assignment down to persistence, where it can actually be
enforced.

## Decision

**Every table has exactly one owning domain**, and ownership means the four
things in the ownership matrix: only the owner writes; direct reads by
others are not an integration pattern; others hold typed references, not
access; emergency access is not integration.

Exactly **four** integration mechanisms are admissible: an owned API;
versioned events; a governed projection; an approved read contract. The
list is closed.

**Audit ingestion is the one case that looks like an exception and is not.**
_All domains may submit typed audit records through the governed
audit-ingestion contract; only `audit-core` persists authoritative audit
records._ "Every domain appends to audit" and "only the owner writes" are
both true because they describe different acts: every domain **submits**
through a port, API or versioned command; exactly one domain **persists**.
Other domains' application credentials carry no write grant on the audit
schema; bulk loading and emergency SQL are not ordinary integration paths;
and privileged maintenance under PACK-12 does not transfer ownership.
Append-only describes ingestion semantics and authoritative storage alike.

Four consequences are stated explicitly because each is a place the rule
would otherwise erode:

- **The outbox is co-located with its domain.** A central outbox table
  written by every domain is precisely the shared mutable table this ADR
  forbids.
- **`organization-service` is the one universal input, and it is consumed
  by event and API, never by join.** Every domain stores its own
  `organization_id`.
- **Future domains get no reserved tables.** Reserving space in a schema
  for a domain that does not exist is how a shared table is born.
- **Reserved boundaries are conceptual, not services.** The identity,
  eligibility, credential, voting and tally/result-certification boundaries
  have owners _to be established_ by PACK-14 and PACK-15/16. Some have
  baseline reference implementations; that does not settle production
  ownership, and this ADR does not settle it either. It fixes only that
  whatever owner is established must comply with the PACK-13 data-plane
  contracts, and that final topology is approved by the corresponding
  PACK.

Cross-domain reference _types_ are enumerated in a closed list. Each is an
identifier plus an owning domain and confers **nothing** — a `DocumentRef`
is not a licence to open the row.

## Consequences

**Positive.** The boundary is a database grant, so violating it requires
changing a grant, which is auditable. Ownership questions have one answer.

**Negative, and accepted.** Audit submission needs a real ingestion
contract rather than a shared table, which is more work than a direct
insert. Reporting across domains needs a governed projection or several API
calls. Onboarding is slower: "just join it" is
not available. Some operational investigations that a shared database would
make trivial now require a PACK-12 privileged grant — deliberately.

**Rejected.** _A read-only cross-domain role for reporting_ — rejected: it
is a direct-read integration pattern with a friendly name, and it would
carry no organizational-scope enforcement. _Allowing joins within a
"trusted" subset of domains_ — rejected: the subset always grows.
