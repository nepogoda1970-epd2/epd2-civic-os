# ADR-069 — Production relational data plane

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

Twenty-one services persist through storage _ports_ whose only adapters are
in memory. That was honest for twelve rounds and is not a data plane. The
system now needs durable, transactional, queryable persistence — and the
moment it gets one, every boundary the previous packs established becomes
enforceable or unenforceable at the database layer rather than only in
application code.

The temptation at this point is well known and nearly universal: one
database, one schema, foreign keys everywhere, a `persons` table that
everything joins to. It is efficient. It is also the single change that
would destroy `FIR-INV-001` (no global user ID), `FIR-INV-002`
(identity/ballot unlinkability) and `FIR-INV-013` (organizational
isolation) in one commit, and no amount of application-layer discipline
would restore them.

## Decision

A **PostgreSQL-compatible relational database** is the reference
direction, organised as **domain-owned schemas** with explicit transaction
boundaries.

1. Relational, not document-oriented, because the invariants this system
   cares about — uniqueness, referential integrity within a domain,
   constrained enumerations, effective-dated windows — are the invariants
   relational engines enforce. A JSON store would move every one of them
   into application code, where a migration script can bypass them.
2. **Domain-owned schemas**, not one shared schema. Isolation is a grant
   boundary, not a naming convention.
3. **Organizational scope is a first-class column from the first
   migration**, never retrofitted.
4. **No global person table, and no cross-domain identity key.**
5. **No generic JSON dump is authoritative.** An opaque payload column is
   permitted; a domain's invariant-bearing fields living inside one is not,
   because a database cannot enforce what it cannot see.
6. Immutable-history tables — audit, document versions, sealed sessions —
   have **no `UPDATE` or `DELETE` in the persistence contract**, enforced
   by database privilege as well as by code.
7. **Voting material never enters this plane** (ADR-070, spec §28.1) —
   ballot content, voting secrets and credentials are absent from every
   schema this ADR governs. The voting domain's own topology, broker
   arrangement, connection and credential layout are **PACK-15/16's**, not
   settled here (spec §28.2).
8. **Reserved future boundaries get no schema.** The identity, eligibility,
   credential, voting and tally/result-certification boundaries are
   conceptual; their owners are established by PACK-14 and PACK-15/16, and
   this ADR creates no table, column or namespace for any of them
   (`P13-OWN-009`..`013`).

"PostgreSQL-compatible" is an architectural direction. It is **not** a
procurement decision, not a managed-provider commitment, and not a lock-in
claim: any engine meeting these requirements is admissible, and the
implementation round records its actual choice under its own ADR.

## Consequences

**Positive.** Invariants become enforceable where they are hardest to
bypass. Isolation is a grant, not a convention. The reference-to-production
path is adapter-by-adapter behind unchanged ports, so no domain logic
changes.

**Negative, and accepted.** Cross-domain queries become genuinely
inconvenient — which is the point, and which will be experienced as
friction by anyone who wants a quick report. Per-domain schemas multiply
migration and connection management. Some read patterns require a governed
projection where a join would have been three lines.

**Rejected alternatives.** _One shared schema_ — rejected: it makes
`FIR-INV-001` unenforceable. _Database-per-service_ — not rejected, but not
required: it is a stronger form of the same isolation and the
implementation round may choose it. _Document store as the authoritative
model_ — rejected: it moves every invariant into application code.
