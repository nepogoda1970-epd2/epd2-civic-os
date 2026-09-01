# ADR-077 — Concurrency and idempotency

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

Two clients act on one aggregate; a retry arrives after a timeout; an
approver approves a version that changed while they were reading it. Each
is routine, and each has a default resolution that is wrong for this
system: last write wins, act twice, approve the new state.

The consequences are not symmetric with a typical CRUD application. A
silently overwritten decision is an ungoverned decision. A duplicated
financial posting is a false accounting record. An approval applied to a
changed object is an authorization that nobody actually gave.

## Decision

**Optimistic concurrency, everywhere it matters.** Every mutable aggregate
carries a version; every state-changing command takes an expected version;
a mismatch is a reason-coded conflict, never a silent overwrite.

**Last-write-wins is forbidden for consequential records** — anything
bearing a decision, an authorization, a financial fact, a governed document
state, a privileged grant, a retention or hold state, or any legal effect.
Where it is admissible at all, the record class says so explicitly.

**An approval does not apply to a version that changed since the approver
saw it.** The submitted snapshot is immutable, the decision records the
exact version it was taken against, and a moved aggregate returns the
approval for a fresh decision with its own reason code. This is the
concurrency expression of PACK-12's activation re-check, and it exists
because "approve" means "approve _this_", not "approve whatever is there
now".

**Effective-dated authority is re-checked at execution**, not only at
construction. Authority that lapsed in between is not authority.

`ExpectedVersion` distinguishes **"any version"** from **"must not
exist"**. Collapsing them turns a create-if-absent into a silent overwrite
— a small modelling decision with a large failure mode.

**Idempotency** is required across ten operation classes. Keys are scoped
to a domain and an operation — never global, and **never derived from a
person identifier**, which would turn a key space into a correlation space
and defeat `FIR-INV-001`. Reuse with a different payload is a conflict, not
a replay. The first successful result is reproducible without re-performing
the effect. Idempotency storage holds a **request digest, not the
request**.

Where expiry of an idempotency record could admit a duplicate of a
consequential action, a **permanent business-fact guard** applies as well:
a unique posting, a single artifact per approval, a digest uniqueness in
the registry, an applied-state check for migrations.

## Consequences

**Positive.** Conflicts surface to the user who can resolve them.
Consequential effects happen once. Stale approvals are refused rather than
applied.

**Negative, and accepted.** Every client must handle conflict, which is
more work than ignoring it. Version plumbing touches every command
signature. Business-fact guards add uniqueness constraints that occasionally
refuse a legitimate-looking retry — correctly, but confusingly.

**Rejected.** _Pessimistic locking_ — rejected: it does not survive user
think-time and turns contention into outage. _Last-write-wins with an audit
trail_ — rejected: an audited wrong answer is still wrong. _A single global
idempotency key space_ — rejected: cross-domain collision, and it is a
correlation key in disguise.
