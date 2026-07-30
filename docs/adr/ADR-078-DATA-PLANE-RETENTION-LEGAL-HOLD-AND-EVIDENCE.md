# ADR-078 — Data-plane retention, legal hold and evidence

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

PACK-09 owns retention, legal hold and destruction evidence. PACK-11 owns
governed documents and evidence bundles. Neither owns the places a
production data plane copies data to: projections, caches, search indexes,
outbox records, dead-letter stores, replicas, backups and migration
artifacts.

Every one of those is a copy that can outlive its source. A deletion that
does not reach them is not a deletion — and the person exercising a
deletion right has been told something untrue.

## Decision

**Retention applies to infrastructure.** Projections, caches, events,
outbox records, schema registry entries, dead-letter stores and migration
evidence each carry a retention binding. None is exempt by virtue of being
infrastructure.

**Deletion propagates to every derived store, with evidence.** Search gets
a tombstone and index-removal evidence referencing the source decision;
projections are updated and the propagation is recorded.

**Backup retention is stated explicitly, with its consequence.** A record
deleted from the live database but present in backups **is not deleted**.
The policy states the backup horizon and what that means, rather than
letting "we deleted it" quietly mean "we deleted one copy". Closing this
gap is **PACK-17's**, not this round's.

**A legal hold preserves data. It does not authorize access, search, export
or publication.** This is restated at the data-plane layer because this is
exactly where the confusion would be operationalised: the practical meaning
of a hold is "the deletion job skips this record", never "the investigator
may now read it". Where hold state cannot be resolved, deletion **fails
closed**.

**Evidence uses PACK-11's mechanisms, not new ones.** Migration plans,
verification reports and schema publication decisions carry evidence
references into PACK-11's bundles. Historical schemas are immutable;
replacement is supersession with digest and version history preserved. A
schema definition may itself be a governed document where the domain
requires it.

**No generated artifact replaces an authoritative governed record.**

## Consequences

**Positive.** Deletion means deletion across derived stores. Hold cannot be
repurposed as an access grant. Data-plane operations produce evidence in
the system's existing evidence framework rather than in a parallel one.

**Negative, and accepted.** Every projection joins the retention system,
which is real complexity. Deletion becomes a distributed operation that can
partially fail — hence the propagation evidence and the failure reason
code. The backup gap remains open and is visible in the threat model's
residual risks rather than hidden.

**Rejected.** _A separate data-plane evidence store_ — rejected: it is the
second evidence system `OD-P12-06` forbade for PACK-12, and the argument
has not changed. _Treating infrastructure copies as exempt_ — rejected:
that is the assumption that makes deletion rights unenforceable.
