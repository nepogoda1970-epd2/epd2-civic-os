# ADR-075 — Database migration discipline

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

Migrations are where a reviewed system silently becomes a different one. A
migration runs with elevated privilege, changes structure irreversibly, and
is usually reviewed less carefully than the application code it supports.
In this system it can also do things no application code could: drop an
organizational-scope column, break a hash-linked evidence chain, delete
records under legal hold, or create the global identifier that
`FIR-INV-001` forbids.

## Decision

**A migration is immutable once applied.** A correction is a new migration.
Every migration has a stable ID, a deterministic ordering position and a
**mandatory checksum** verified before application. A checksum mismatch
**halts and escalates**; it is never auto-repaired, because auto-repair
erases the evidence of tampering.

Migrations are **classed** — expand, backfill, switch, contract,
corrective, emergency — and the class determines the controls. Destructive
(contract) migrations require **separate approval with separation of
duties**, dry-run evidence, an elapsed observation period, and consumer
readiness.

Migration execution requires a **scoped PACK-12 privileged grant**, and
**no manual undocumented production SQL** is possible: direct SQL happens
in a governed migration or emergency context that leaves session evidence.

Five checks are **automated gates**, not reviewer vigilance:

- organizational scope is not lost;
- retention and legal-hold records survive;
- document and evidence linkage survives;
- **no global user identifier is created**;
- **voting unlinkability is not weakened**.

**Expand/contract** is the normative pattern, in nine steps, with two
constraints that experience makes necessary: **dual-write is forbidden
without an approved reconciliation strategy** (two unreconciled writes are
two sources of truth), and **the observation period must elapse** before
the destructive step — divergence is found by running, not by reviewing.

**Rollback is either tested or declared forward-fix-only.** An untested
rollback script presented as a safety net is worse than an honest
declaration that there is none.

Backfills are deterministic, restartable, idempotent, checkpointed,
rate-limited, policy-aware — and **invent nothing**. Where a source lacks a
required fact, the record goes to a review queue; it is never filled with a
default or an inference, because an inferred fact becomes an authoritative
lie.

## Consequences

**Positive.** Structural change becomes reviewable, evidenced and
reversible-or-honestly-not. The invariants that a migration could silently
destroy are protected by automated gates.

**Negative, and accepted.** Migrations are slower and require more people.
Expand/contract turns one change into several deployments. The "just fix it
in production" path is closed — including during incidents, where it is
replaced by break-glass with evidence.

**Rejected.** _Auto-repair checksum mismatches_ — rejected: it removes the
signal. _Allow emergency DDL outside the pipeline_ — rejected:
`FIR-INV-006`; emergencies use break-glass, which adds obligations rather
than removing them.
