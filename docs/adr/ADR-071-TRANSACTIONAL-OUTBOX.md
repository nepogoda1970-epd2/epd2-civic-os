# ADR-071 — Transactional outbox

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

A domain command changes state and publishes an event. If those two are not
atomic, the system has exactly two failure modes, and both are bad: an
event describing state that does not exist (unrecoverable downstream), or a
state change nobody was told about (silently divergent). Publishing to a
broker inside a database transaction fixes neither and adds a third: an
open transaction awaiting a network call.

## Decision

The **transactional outbox is mandatory**. No domain publishes to a broker
from command execution. The state change and the outbox record are written
in the **same transaction**; a separate dispatcher reads the outbox and
publishes.

Four properties are load-bearing:

1. **Atomicity** (`P13-TX-003`) — the event exists if and only if the state
   change does.
2. **Immutability after commit**, except delivery metadata. Identity, type,
   version and payload never change.
3. **Stable event ID across republication.** A consumer that has seen the
   ID has seen the event.
4. **Published state and delivery evidence are distinct fields.** "We
   dispatched" and "the broker acknowledged" are different facts, and
   conflating them makes a lost acknowledgement look like success.

**Transport metadata stays out of the envelope.** Attempt counts, broker
references and dispatch timestamps live on the outbox record, not on the
canonical event. This is the specific decision that keeps PACK-13
canon-neutral (see the canon assessment): had delivery state been added to
the envelope, canon §21 would have required amendment.

The dispatcher **changes no domain semantics**: it reads, publishes,
records. A dispatcher that filters or enriches is a hidden business rule in
infrastructure.

## Consequences

**Positive.** The strongest guarantee available without distributed
transactions. Broker outages delay publication and never lose it. Every
delivery attempt is auditable.

**Negative, and accepted.** Publication is asynchronous, so consumers see
events after commit rather than at commit — every consumer must tolerate
delay. The outbox is write amplification on every command. Outbox growth
becomes an operational signal requiring alerting and retention.

**Rejected.** _Publish inside the transaction_ — rejected: an external call
inside a transaction. _Publish after commit, best effort_ — rejected: the
crash between commit and publish loses the event silently. _Change data
capture from the transaction log_ — a legitimate alternative, not chosen:
it couples the event contract to the physical schema, so a column rename
becomes an event change.
