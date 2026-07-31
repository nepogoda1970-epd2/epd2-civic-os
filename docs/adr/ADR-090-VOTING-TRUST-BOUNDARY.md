# ADR-090 — There is one voting trust boundary, one artifact crosses it, and no component exists on both sides

**Status:** proposed
**Round:** PACK-15 — Voting Trust Boundary, Eligibility & Credential Separation (specification and ADR only)
**Repository version:** unchanged at `0.14.0` · **Canon version:** unchanged at `0.8.0`

**NO CODE. NOT IMPLEMENTED. NOT A CANDIDATE. NOT A PASS. NOT PRODUCTION
READY. NOT LEGALLY ACTIVATED.**

> **Architecture correction (2026-07-31).** The decision below is unchanged
> and is not reversed. The open questions it left are now closed; the
> closures are recorded in `docs/packs/PACK-15/PACK-15-SPECIFICATION.md`
> §32 and summarised for this ADR in the note that follows. The
> authoritative register is now
> `EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER_UPDATED_V6.md`, carried at
> the canonical path, which preserves every prior entry and adds
> `FIR-OSS-001` … `FIR-OSS-006`.
>
> **The crossing is re-drawn without moving the boundary (`OD-P15-07`).**
> The ordinary workspace now transmits **only** PACK-14's one-time handoff
> artifact. The assertion is collected inside the isolated origin through a
> **one-time pickup** (`H-06`), and the credential is minted and redeemed
> there. `pickup.redeem` is the only identity-side operation callable from
> inside WS-03; it returns the assertion and nothing else — no account, no
> session, no case reference, no context-scoped pseudonym. Every operation
> still declares exactly one `boundary_side`, and the trace break moves to
> `H-05`/`H-06`.

## Context

PACK-14 defined the `VotingHandoffArtifact` and stopped at the edge,
recording explicitly that how an eligibility statement reaches the voting
domain without an identity attached is PACK-15's problem, taken with
PACK-15's own threat model (ADR-088). That was the right refusal: settling
a security architecture from outside the round that owns it is itself a
vulnerability, and PACK-13 established that discipline before PACK-14
inherited it.

The problem PACK-15 inherits is not "how do we pass a message across". It
is "how do we make sure that the two sides remain two sides" — under
operational pressure, under an incident, under a support escalation, and
under an engineer who needs a correlation ID to debug a production issue
during a live vote.

A boundary that exists only as a diagram is not a boundary. It has to be
expressible as a property that can be checked.

## Decision

**There is exactly one trust boundary in the voting flow. Exactly one
artifact crosses it. No component, store, key, audit stream, role,
principal, trace or identifier exists on both sides of it.**

1. **The boundary sits between the Assertion Issuer and the Credential
   Issuer.** Everything before it is the identity side; everything after it
   is the voting side.

2. **The only artifact that crosses is the minimized eligibility
   assertion** (ADR-091). Its complete permitted content is twelve fields,
   and the list is closed.

3. **Every operation declares a `boundary_side`** — `identity` or `voting`
   — and no operation may declare both. An operation that would need both
   does not exist; the specification refuses it rather than routing it.
   This is what makes the boundary checkable rather than aspirational.

4. **`assertion.redeem` is the single apparent exception, and is not one.**
   It writes evidence on both sides, as two independent records that share
   no key, no correlation identifier and no timestamp precision. The
   implementation must demonstrate that the two records cannot be paired —
   a stronger obligation than demonstrating that no code pairs them.

5. **Distributed tracing, correlation IDs, request IDs and idempotency keys
   terminate at the boundary.** An identity-side chain ends at assertion
   issuance; the voting side begins a new one. Modern instrumentation
   propagates context by default, so the break must be explicit and
   tested, not assumed.

6. **The handoff boundary (VC-05) is on the identity side.** It consumes
   PACK-14's artifact, learns that a valid single-use artifact was redeemed
   for a stated context, and never learns which account obtained it. It
   holds no session and issues none.

7. **The boundary binds infrastructure as well as code**: no shared
   database, no shared backup domain, no shared restore target, no shared
   log index, no shared metrics label space, no principal with read access
   to both sides.

## Consequences

**Debugging a cross-boundary problem is genuinely harder.** An engineer
cannot follow a single request from the member's click to the credential.
They can see the identity side fail, or the voting side fail, and they can
correlate by reason code and timing class. That is a real operational cost
and it is accepted, because the alternative is a trace that reconstructs
the chain on demand.

**Incident response is constrained.** No tool may be granted read access to
both sides, including during an incident, including under break-glass. An
incident that genuinely requires it is a context-level event — suspension,
annulment, re-run — decided by governance, not resolved by a temporary
grant.

**The boundary is testable.** Because `boundary_side` is a declared
property and the prohibited constructions are enumerated
(`PACK-15-UNLINKABILITY-MATRIX.md` §8), the implementation round can assert
the boundary structurally rather than reviewing it by eye.

**PACK-16 inherits a boundary rather than a tangle.** Whatever casting and
tally protocol it selects, it begins from a point where nothing on its side
knows who anyone is, and it does not have to undo an existing linkage to
get there.

## Alternatives rejected

**A trusted broker that sees both sides and is "carefully controlled".**
Rejected: the broker is the link, and its trustworthiness is exactly the
assumption the architecture is built to avoid making.

**Boundary by network segmentation alone.** Rejected: segmentation
constrains reachability, not data content. Two segments can still hold the
same identifier.

**Boundary by policy with monitoring.** Rejected: monitoring detects a
crossing after it happened, and a correlation that existed for an hour
existed.
