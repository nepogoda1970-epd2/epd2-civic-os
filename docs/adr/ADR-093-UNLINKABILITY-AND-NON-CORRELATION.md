# ADR-093 — The assertion-to-credential record is a set, not a map: no store anywhere contains both references

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
> **The timing residual now has controls and numbers (`OD-P15-02`).** This
> ADR's central decision — set-not-map, no store contains both references —
> is unchanged. What changes is the honesty of the companion paragraph: the
> timing channel this ADR named as residual is now bounded by **queued
> issuance, batching at 120 s, a minimum cohort of five, uniform release
> delay 30–300 s, `cohort_wait_max` 3600 s, coarsened timestamps at 300 s
> (≥ 3600 s for small electorates), a randomized 5–30 s minting delay, and
> an explicit small-electorate policy**, each a governed value with a hard
> lower bound that configuration cannot go below.
>
> It is **reduced and bounded, not eliminated** (`T-P15-13`), and the queue
> itself becomes an observable worth protecting (`T-P15-37`): cohort and
> batch sizes are reported as **classes**, never as numbers, and a
> small-electorate context publishes no per-scope operational metric at all.
> The cryptographic answer remains PACK-16's (`OD-P15-05`).

> **This is the load-bearing decision of PACK-15.** ADR-089 says the two
> authorities are separate; ADR-090 says the boundary is one boundary; this
> ADR says what makes them true in the presence of an operator with
> database access.

## Context

For `person → ballot` to be reconstructed, an attacker needs every link in
the chain:

```text
person → eligibility → assertion → credential → redemption → ballot → tally
```

Five of those six links are held by exactly one component each, and none of
those components can reach the next one. The third link — **assertion →
credential** — is the only one that would naturally be written down, and
the only one whose absence makes the whole chain unreconstructible.

It would be written down for good reasons. Idempotency wants to know what a
retry produced. Reconciliation wants to match issuance to minting. Support
wants to answer "what happened to my access". Auditors want to verify that
every credential came from a valid assertion. Every one of those is a real
need with a plausible design that stores the pair.

If that pair exists anywhere — in a table, a cache, a log, an event, a
trace, a backup, a warehouse or a dashboard — then a compromise of the
identity side plus a compromise of the voting side, or a single operator
with read access to both, or a subpoena served on the organization,
reconstructs the chain. The link does not have to be exploited to be
dangerous; it only has to exist.

## Decision

**No store, cache, log, event, trace, backup, archive, index, export or
dashboard, anywhere in the system, at any time, contains both an
eligibility-side reference and a voting-side reference for the same
participation.**

Concretely:

1. **The Credential Issuer records the assertion nonce as *spent*: set
   membership, not a mapping.** There is no value column, no
   `credential_id` beside the nonce, and no schema in which one could be
   added without changing this ADR.

2. **The credential record holds no assertion reference.** The credential's
   own status answers every operational question the issuer has.

3. **Idempotency is keyed on the nonce with a bounded cache window.** The
   cached outcome is discarded at the end of the window, which is explicit,
   short and tested. A cache that outlives its window is the map.

4. **`EligibilityAssertionRedeemed` (`AS-02`) and `VotingCredentialIssued`
   (`AS-03`) are two independent records** with no shared key, no shared
   correlation ID and no shared timestamp precision.

5. **The enumerated prohibited constructions**
   (`PACK-15-UNLINKABILITY-MATRIX.md` §8) are structural acceptance
   criteria, not policies: shared correlation IDs, propagated traces,
   derived credentials, derived nonces, shared idempotency keys,
   cross-store reconciliation jobs, combined backups, combined warehouses
   and participation-journey dashboards.

6. **Each of the operational needs above is met without the pair.**
   Idempotency: the nonce. Reconciliation: counts per stream. Support:
   holder-supplied references. Audit: per-stream integrity plus count
   consistency (ADR-097).

## Consequences

**What the system gains** is a property that survives compromise: an
attacker who takes the identity side learns who applied and who was
approved, and learns nothing about credentials or ballots. An attacker who
takes the voting side learns how many credentials existed and which were
redeemed, and learns nothing about people. An attacker who takes both, or
an operator with both, still cannot pair them, because the pairing was
never written.

**What is honestly not gained** is protection against correlation from
outside the data. Two residual channels survive and are named rather than
hidden:

- **Timing.** An assertion issued and a credential minted in the same quiet
  minute in a low-turnout context are plausibly the same participation.
  Mitigated by coarsened timestamps, timing-class logging, batching, jitter
  and a minimum-cohort issuance policy (`OD-P15-02`). **Reduced, not
  eliminated** (`T-P15-13`).
- **Infrastructure metadata.** Network-level observation of who connects to
  which origin when is outside any application-layer boundary and is
  PACK-17's (`T-P15-14`).

The strongest available answer to the timing residual is a cryptographic
issuance construction in which the issuer cannot correlate even in
principle — blind signatures, anonymous credentials, oblivious issuance.
**PACK-15 deliberately does not choose one** (`OD-P15-05`). Choosing a
ballot-adjacent cryptographic scheme from outside the round that owns the
ballot threat model is the mistake PACK-13 refused and PACK-14 inherited.
The spent-set design is chosen as the *weakest* structure that achieves
exactly-once, precisely so that a stronger construction can replace it
without redesigning the boundary.

## Alternatives rejected

**Store the pair, encrypt it, split the key.** Rejected: it produces a
system that *can* answer the question given cooperation, and "given
cooperation" is exactly the threat model — insider collusion, compulsion,
compromise of two components.

**Store the pair with a short retention.** Rejected: a link that exists for
an hour existed, and backups do not respect application retention.

**Store a one-way hash of the pair "for verification".** Rejected: with a
small candidate set, a one-way function over known inputs is a lookup
table.

**Rely on access control and monitoring.** Rejected: monitoring reports a
crossing after it happened. The invariant must hold against the operator,
not only against the application.
