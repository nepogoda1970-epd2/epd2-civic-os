# ADR-076 — Projection and read-model governance

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

Read models make hard queries easy, and that is exactly the risk. A
projection can quietly become three things it must not be: an authoritative
source, a cross-domain database, and an authorization bypass. All three
happen without anyone deciding — a projection joining two domains for a
useful report is indistinguishable, in code, from a boundary violation.

## Decision

Every projection has a **named owner, declared source events, a schema
version and a rebuild strategy**. Undeclared projections do not exist.

Four prohibitions:

1. **A read model is never authoritative and creates no legal effect.** A
   decision with legal effect reads the authoritative record.
2. **A projection never widens source authorization.** If the reader could
   not read the source, the projection does not let them read the
   derivative.
3. **A projection is not a hidden cross-domain database.** A multi-domain
   projection is admissible only where **every** source domain has approved
   that specific projection under ADR, and the result carries the
   **narrowest** authorization of its inputs.
4. **No projection uses a global identity bridge.** A projection is exactly
   where the separation that schemas enforce could be reconstituted.

Two positive obligations:

- **Staleness is visible.** Where a consequential decision depends on
  freshness, the projection exposes its lag and the decision path reads it.
  A stale projection that looks fresh is worse than one plainly
  unavailable — the first produces confident wrong answers.
- **Deletion propagates, with evidence.** When a source record is deleted
  or tombstoned under PACK-09, every derived store is updated. A projection
  that outlives its source is an undeletable copy, and it defeats the
  deletion right entirely.

Legal hold propagates to projections as a **preservation** obligation and,
consistently with PACK-09, still authorizes no access.

## Consequences

**Positive.** Read models stay derived. Authorization has one answer, not
one per copy. Deletion actually deletes.

**Negative, and accepted.** Useful cross-domain reports need ADR approval
from several owners, which is slow and will be experienced as
bureaucratic. Staleness plumbing is real work. Deletion propagation makes
every projection a participant in the retention system.

**Rejected.** _A general-purpose read-model platform any domain may write
to_ — rejected: it is the shared mutable schema again, one layer up.
_Projections as a caching detail below governance_ — rejected: a cache that
answers authorization questions is an authorization component.
