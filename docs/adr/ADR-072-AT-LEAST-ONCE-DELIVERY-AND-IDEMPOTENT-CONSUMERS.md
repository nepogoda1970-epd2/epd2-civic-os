# ADR-072 — At-least-once delivery and idempotent consumers

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

Every distributed system must choose a delivery guarantee, and the choice
is usually described dishonestly. "Exactly-once delivery" is available from
no broker in the general case; what brokers offer is at-least-once delivery
plus deduplication within a window, or transactional semantics within their
own boundary that do not extend to a consumer's side effects.

The practical danger is not the technical limitation. It is that a team
told it has exactly-once delivery **stops writing idempotent consumers** —
and then the first redelivery, months later, double-posts a financial
entry.

## Decision

The transport guarantee is **at-least-once**. The consumer effect is
**effectively-once**, achieved by **mandatory consumer idempotency**.

**Exactly-once delivery is claimed nowhere** — not in documents, code
comments, API descriptions, operator surfaces or log messages
(`P13-DEL-015`). This is enforced by a forbidden-phrase scan, not by
convention.

Every consumer is idempotent. A consumer that cannot be made idempotent is
a design defect, not a tolerated exception. Deduplication is keyed on the
event ID plus the consumer's own scope, so one event consumed by two
consumers is two independent, independently-deduplicated effects.

Where an idempotency record's expiry could admit a duplicate of a
**consequential** action — a financial posting, an export artifact, a
schema publication, a migration — the operation carries a **permanent
business-fact guard** in addition. The idempotency record is an
optimisation; the guard is the control.

Ordering is scoped, never global (ADR-076's sibling decision, spec §10):
per aggregate, per stream, or per organization and aggregate. Sequence is
explicit; timestamps are metadata, not order; clock skew therefore cannot
disturb ordering semantics.

## Consequences

**Positive.** The guarantee is achievable and honestly described. Duplicate
delivery is safe by design rather than by luck. Broker choice stays open,
since no exotic transactional guarantee is required of it.

**Negative, and accepted.** Every consumer carries deduplication state,
with its own retention and storage cost. Some naturally non-idempotent
operations need redesign around a business-fact guard. Operators must
understand that duplicates are normal and expected rather than incidents.

**Rejected.** _Claim exactly-once because the broker offers it within its
boundary_ — rejected as dishonest: the broker's boundary does not include
the consumer's side effects. _At-most-once_ — rejected: silent loss is
worse than duplication for every operation in this system.
