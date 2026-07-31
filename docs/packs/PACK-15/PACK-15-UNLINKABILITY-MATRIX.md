# PACK-15 — Unlinkability Matrix

**Round:** PACK-15 — specification and ADR only. **No code. Not implemented. Not a candidate. Not a PASS.**
**Repository version:** unchanged at `0.14.0` · **Canon version:** unchanged at `0.8.0`
**Baseline:** `EPD2_PACK-14_IDENTITY_AUTHENTICATION_ACCOUNT_SECURITY_0.14.0_FINAL_PASS.zip`
**Authoritative register:** `EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER_UPDATED_V6.md`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**
**Architecture correction applied (2026-07-31).**

The requirement this document exists to demonstrate:

> **No component may possess enough information to directly reconstruct the
> full chain.**

Seven transitions after the correction — the assertion pickup is now a hop
of its own. For each: what is visible, what the identifier is, who owns it,
whether reverse resolution is possible, retention, audit visibility,
correlation risk, the preventive control, and the residual risk.

**Corrected by this revision:** the timing residual at transition 4 now has
**specified controls with default values** rather than a named intention
(`OD-P15-02`), the pseudonym is removed from every crossing artifact
(`OD-P15-03`), and the delivery boundary removes credential material from
every surface outside WS-03 (`OD-P15-07`).

---

## 1. identity → eligibility

| Property             | Value                                                                                              |
| -------------------- | -------------------------------------------------------------------------------------------------- |
| Data visible         | Scoped predicates named by the frozen rule-set version; scope; participation class; assurance flag |
| Identifier           | The eligibility case reference, scoped to one context                                              |
| Owner                | Voting-trust service, VC-02                                                                        |
| Reverse-resolvable?  | **Yes, by design and only here.** The identity side must know whose eligibility it is deciding     |
| Retention            | Eligibility case class; PACK-09 schedule                                                            |
| Audit visibility     | `AS-01` only                                                                                        |
| Correlation risk     | The case is identified; a leak here reveals who applied to vote, not how anyone voted              |
| Preventive control   | Attribute minimization; predicate-at-source; no membership record; scoped adapter                  |
| Residual risk        | Participation *intent* is knowable on the identity side. Named, accepted, bounded to this side     |

This is the only transition where identification is intended.

---

## 2. eligibility → assertion (minting)

| Property             | Value                                                                                       |
| -------------------- | ------------------------------------------------------------------------------------------- |
| Data visible         | Result (`approved`), class, scope, assurance-satisfied, context, audience, purpose, expiry  |
| Identifier           | `EligibilityAssertionId` and a one-time `Nonce`, both random and non-derived                |
| Owner                | Assertion Issuer (VC-03) — **separate module, storage, signing key and service credential** |
| Reverse-resolvable?  | **On the identity side only**, through the issuer's own record. Never from the artifact     |
| Retention            | Assertion issuance record: short, bounded by the issuance window plus a dispute margin      |
| Audit visibility     | `AS-02` only                                                                                |
| Correlation risk     | The issuer knows participation-unit → assertion. This is the last point where that is known |
| Preventive control   | Prohibited-content list incl. the pseudonym; no derived identifiers; separate key custody; no read path to account/person/membership stores |
| Residual risk        | An insider with the issuer's store knows who was issued an assertion — but not what it became |

---

## 3. assertion → queue → release → pickup

**New hop, added by the correction.**

| Property             | Value                                                                                          |
| -------------------- | ---------------------------------------------------------------------------------------------- |
| Data visible         | The assertion, held; the release schedule; the one-time pickup state                           |
| Identifier           | The pickup reference, bound to the one-time handoff artifact                                   |
| Owner                | Assertion Issuer (VC-03) and Handoff Boundary (VC-05), identity side                            |
| Reverse-resolvable?  | On the identity side only. **The pickup is never visible to the Credential Issuer**             |
| Retention            | Consumed at pickup; the pickup record is reduced to a fact after the dispute margin             |
| Audit visibility     | `AS-02`; cohort-threshold events to `AS-04`                                                     |
| Correlation risk     | The queue is where timing correlation is deliberately broken — and where a naive queue would leak through its own metadata (`T-P15-37`) |
| Preventive control   | Batching (120 s default), minimum cohort *k* = 5, uniform release delay 30–300 s, cohort-of-one never released immediately, `cohort_wait_max` 3600 s, notification on the release schedule |
| Residual risk        | Queue-depth metrics and release-batch sizes are themselves observable and are therefore subject to disclosure control and cohort-class-only reporting |

---

## 4. assertion → credential

**The critical transition.**

| Property             | Value                                                                                                       |
| -------------------- | ----------------------------------------------------------------------------------------------------------- |
| Data visible         | The assertion's twelve fields, verified; nothing else ever                                                  |
| Identifier           | The nonce, on the way in; `VotingCredentialId`, on the way out — **and the two are never stored together**   |
| Owner                | Credential Issuer (VC-04), voting side, separate service                                                     |
| Reverse-resolvable?  | **No.** The spent-nonce set is a set, not a map; the credential record holds no assertion reference          |
| Retention            | Spent-nonce set: bounded by the context; credential record: context plus dispute margin                     |
| Audit visibility     | `AS-03` only, recording *that* a nonce was spent, never *what it produced*                                   |
| Correlation risk     | **Timing** — the residual named before the correction                                                        |
| Preventive control   | Set-not-map; no shared trace identifier; **coarsened timestamps (300 s default, ≥ 3600 s for small electorates)**; timing-class logging; **queued identity-side release**; **randomized voting-side minting delay 5–30 s**; minimum cohort *k* = 5 |
| Residual risk        | Timing correlation **reduced and bounded, not eliminated** (`T-P15-13`); infrastructure metadata (`T-P15-14`, PACK-17) |

The strongest available answer to the residual — a blind or oblivious
issuance construction in which the issuer cannot correlate even in
principle — is deliberately **not chosen here**. It is PACK-16's decision
(`OD-P15-05`), and the spent-set design is deliberately the weakest
structure achieving exactly-once so that a stronger one can replace it
without redesigning the boundary.

---

## 5. credential → redemption

| Property             | Value                                                                          |
| -------------------- | ------------------------------------------------------------------------------ |
| Data visible         | The credential, its context, its status                                        |
| Identifier           | `VotingCredentialId`; `RedemptionReference`                                    |
| Owner                | Credential Issuer (VC-04)                                                       |
| Reverse-resolvable?  | To the credential, yes. To a participant, **no** — there is nothing to resolve  |
| Retention            | Redemption record: context plus audit margin, then reduced to counts            |
| Audit visibility     | `AS-03`                                                                         |
| Correlation risk     | Client-side and network metadata at redemption time                             |
| Preventive control   | Isolated origin; **credential material never leaves WS-03 and is never displayed, persisted or copied**; no shared storage or session; `no-store`; `no-referrer`; no analytics; no third-party script |
| Residual risk        | Network-layer observation of who connects to the voting origin and when (`T-P15-14`, PACK-17) |

---

## 6. redemption → ballot

| Property             | Value                                                                                   |
| -------------------- | --------------------------------------------------------------------------------------- |
| Data visible         | A minimal, single-use continuation capability                                           |
| Identifier           | The capability's own reference; **never the credential ID, never a ballot ID that echoes it** |
| Owner                | PACK-16's voting domain                                                                  |
| Reverse-resolvable?  | **No.** Canon 15.3 already forbids identity fields on `VoteEnvelope`; PACK-15 adds that the credential reference must not be retained as a mapping |
| Retention            | PACK-16 / PACK-09                                                                        |
| Audit visibility     | `AS-04`, which contains no identity in any field                                         |
| Correlation risk     | Order-of-arrival correlation between redemption and casting                             |
| Preventive control   | The capability is not the credential; timing controls; PACK-16's own protocol design    |
| Residual risk        | Owned by PACK-16 and stated as a dependency, not claimed as solved here                 |

---

## 7. ballot → tally

| Property             | Value                                                            |
| -------------------- | ---------------------------------------------------------------- |
| Data visible         | Ballots as PACK-16 defines them                                   |
| Identifier           | PACK-16's                                                         |
| Owner                | `tally-service`, Tally Authority                                  |
| Reverse-resolvable?  | **No.** The Tally Authority receives no identity, ever            |
| Retention            | PACK-16 / PACK-09                                                 |
| Audit visibility     | Tally evidence, published after closure                           |
| Correlation risk     | Small-group disclosure in the published result (`T-P15-27`)       |
| Preventive control   | PACK-12 disclosure control; `disclosure_min_cell` = 5; complementary suppression |
| Residual risk        | A result in a body of eleven people is inherently near-identifying; owned by governance |

---

## 8. The composition argument

| Link needed             | Held by                | Available to anyone else? | What breaks it                                       |
| ----------------------- | ---------------------- | ------------------------- | ---------------------------------------------------- |
| person → eligibility    | VC-02                  | no                        | Store boundary; role separation                      |
| eligibility → assertion | VC-03                  | no                        | Separate module, storage, key and service credential |
| assertion → pickup      | VC-03 / VC-05          | no                        | One-time pickup; never visible to VC-04              |
| **assertion → credential** | **nobody**          | **no**                    | **Set-not-map; no row contains both** (ADR-093)      |
| credential → redemption | VC-04                  | no                        | Store boundary; role separation                      |
| redemption → ballot     | PACK-16                | no                        | Continuation capability ≠ credential; canon 15.3     |
| ballot → tally          | Tally Authority        | n/a                       | No identity ever enters                              |

The fourth row is the cut. Everything above it lives on the identity side,
everything below it on the voting side, and **the link that would join them
is not stored by any component**, so no compromise, collusion, export,
backup, replica or legal compulsion can produce it from this system's data.

What remains — and what this round does not claim to have solved — is
correlation from **outside** the data: timing (now bounded by specified
controls, `T-P15-13`), network metadata (`T-P15-14`), operator observation
of both sides at once (`T-P15-12`) and small populations (`T-P15-27`).
Those have owners and mitigations, and they are risks rather than gaps.

---

## 9. Prohibited constructions

| Construction                                                    | Why it is forbidden                                          |
| --------------------------------------------------------------- | ------------------------------------------------------------ |
| A "correlation ID" spanning the boundary for support purposes   | It is the link, named helpfully                              |
| A distributed trace propagated from WS-02 into the WS-03 flow   | Same, with a vendor SDK attached                             |
| A credential derived deterministically from the assertion       | Reconstructs the map without storing it                      |
| An assertion nonce derived from participant data                | Same                                                         |
| A context-scoped pseudonym placed in any crossing artifact      | **Added by the correction** — the pseudonym never crosses    |
| A shared idempotency key visible to both sides                  | Same                                                         |
| An unqueued, immediate assertion release                        | **Added by the correction** — restores the timing pair       |
| A cohort-of-one release without the recorded exception          | Same                                                         |
| Credential material on any surface outside WS-03                | **Added by the correction** — a transferable, observable bearer value |
| A reconciliation job that reads both stores                     | Creates the join at runtime even if it stores nothing        |
| A backup that snapshots both stores into one archive            | Creates the join at rest                                     |
| A data warehouse ingesting both audit streams                   | Creates the join in the place nobody reviews                 |
| An evidence bundle containing a per-participation record        | **Added by the correction** — the bundle is totals only      |
| A "participation journey" dashboard                             | The join, as a product feature                               |

Every row above has been a real design in a real system. The
implementation round's acceptance criteria test for each of them by
structure, not by policy.
