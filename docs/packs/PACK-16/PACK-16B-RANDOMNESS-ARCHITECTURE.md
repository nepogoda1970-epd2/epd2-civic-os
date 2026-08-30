# PACK-16B — Randomness Architecture

**Round:** PACK-16B — Cryptographic Parameters, Key Ceremony and Trustee Architecture. **Specification and ADR only. No code. No cryptographic code. Not implemented. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-100`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

Profile identifier: **`EPD2-RND-1`**, a registry field of the parameter set.

---

## 0. Why randomness gets its own architecture

The selected specification specifies what must be uniform and says almost
nothing about where uniformity comes from. That gap is where the worst
failures in this field live, because bad randomness produces output that is
correctly formatted, correctly proved and correctly verified — and
decryptable.

Two properties make it worse here. Ballot nonces are generated **in a
browser**, on a device EPD² does not control. And a nonce failure is
**silent**: nothing in the election record reveals it, and no verifier can
detect it.

---

## 1. Sources — the permitted classes

Reference: **BSI AIS 20/31, "A proposal for: Functionality classes for
random number generators", Version 3.0, 17 September 2024** `[F-26]`, with
NIST SP 800-90A Rev 1 `[F-27]`, SP 800-90B `[F-28]` and SP 800-90C (final,
24 September 2025) `[F-29]` as the complementary constructions.

| Class   | Type          | Meaning                                                                            |
| ------- | ------------- | ---------------------------------------------------------------------------------- |
| `PTG.2` | physical      | Physical noise source with digitisation                                            |
| `PTG.3` | physical      | **Strongest** — physical source with DRG.3-compliant cryptographic post-processing |
| `DRG.3` | deterministic | Backward, forward and enhanced backward secrecy                                    |
| `DRG.4` | deterministic | DRG.3 plus enhanced forward secrecy (hybrid)                                       |
| `DRT.1` | deterministic | **New in v3.0** — requirements for DRNG _trees_                                    |
| `NTG.1` | non-physical  | Hybrid non-physical true RNG with DRG.3-compliant post-processing                  |

**The rule that governs the whole architecture** `[F-26]`:

> _"It is thus recommended **not to use a PTG.2-compliant PTRNG 'directly'
> to generate sensitive data like keys, signature parameters, nonces,
> etc.**"_

A PTG.2 source **seeds** a DRNG; it does not produce key material directly.

| ID      | Rule                                                                                                                                |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `RN-01` | Long-term key material is generated from **`PTG.3`**, or from **`DRG.3` or `DRG.4`** seeded by a `PTG.2`, `PTG.3` or `NTG.1` source |
| `RN-02` | A `PTG.2` source is **never** used directly for keys, shares, coefficients or nonces                                                |
| `RN-03` | Where a DRBG is used it is one of the SP 800-90A Rev 1 mechanisms — **Hash_DRBG, HMAC_DRBG or CTR_DRBG** — and no other `[F-27]`    |
| `RN-04` | The entropy source satisfies SP 800-90B, including its health tests and min-entropy estimation `[F-28]`                             |
| `RN-05` | The construction follows SP 800-90C `[F-29]`, and the construction class used is **recorded in the ceremony transcript**            |
| `RN-06` | Which AIS 20/31 class current German guidance actually requires is **`VO-02`** and is **not assumed** here                          |

---

## 2. Per-consumer requirements

Each row states: source class · minimum entropy · reseeding · health tests ·
fork safety · failure behaviour · audit evidence.

### 2.1 Guardian key generation and DKG coefficients

| Property        | Requirement                                                                                                                                        |
| --------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| Consumers       | `a_{i,j}`, `â_{i,j}` (polynomial coefficients), `ζ_i` (communication secret), `u_{i,j}` (Schnorr commitments), `ξ_{i,ℓ}` (share-encryption nonces) |
| Source class    | **`PTG.3`**, or `DRG.4` seeded from a hardware source on the guardian's dedicated device                                                           |
| Minimum entropy | ≥ **256 bits** of min-entropy into the internal state before any output; a full reseed before each ceremony                                        |
| Reseeding       | Before every ceremony session. **Never** across ceremonies without reseeding                                                                       |
| Health tests    | Start-up test, total-failure test and continuous online test, all **before** any coefficient is produced `[F-26]`                                  |
| Fork safety     | Not applicable — a dedicated device, single process, no fork, no VM snapshot (§4)                                                                  |
| **Failure**     | **FAIL CLOSED. The ceremony does not start. No key material is produced.**                                                                         |
| Audit evidence  | Health-test outcome and source class recorded in the ceremony transcript; **no sample, no seed, no output ever recorded**                          |

### 2.2 Ballot encryption nonces and proof nonces

| Property        | Requirement                                                                                                                     |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| Consumers       | The ballot nonce `ξ_B` and every derived `ξ_{i,j}`; every Schnorr and Chaum–Pedersen commitment nonce; challenge/spoil material |
| Source class    | The platform CSPRNG, which must be **DRG.3-equivalent or better and continuously seeded by the operating system**               |
| Minimum entropy | ≥ 256 bits in the underlying state                                                                                              |
| Reseeding       | Delegated to the operating system                                                                                               |
| Health tests    | A **startup self-test in the client before the first encryption of a session**                                                  |
| Fork safety     | **Required.** A duplicated execution context must not reproduce a nonce (§4)                                                    |
| **Failure**     | **FAIL CLOSED. Refuse to encrypt. No ballot is produced.** `FM-16B-06`                                                          |
| Audit evidence  | A reason code only. **Never the nonce, never the seed, never the state**                                                        |

**Derivation rather than draw.** Per-selection nonces are _derived_ from a
single ballot nonce by the specification's KDF `[F-13]`, so the client
draws **one** high-quality value per ballot rather than dozens. That is a
significant reduction in exposure and it is a property of the selected
construction, not an EPD² addition.

### 2.3 Checkpoint signing, ceremony session identifiers, transcript nonces

| Property        | Requirement                                                                       |
| --------------- | --------------------------------------------------------------------------------- |
| Source class    | `DRG.3` or better, server-side, OS-seeded                                         |
| Minimum entropy | ≥ 256 bits                                                                        |
| Health tests    | Startup plus periodic                                                             |
| **Failure**     | **FAIL CLOSED.** No checkpoint is signed; the board pauses (`FM-P16A-09` lineage) |
| Audit evidence  | Reason code and health-test outcome                                               |

### 2.4 Test-vector and rehearsal randomness

| Property       | Requirement                                                                                                     |
| -------------- | --------------------------------------------------------------------------------------------------------------- |
| Source         | **Deterministic seeds are permitted and required for reproducibility** — in the test and rehearsal domains only |
| Separation     | A deterministic-seed mode must be **structurally unreachable in production**, not merely disabled (§5)          |
| **Failure**    | If a production build can reach deterministic mode at all, that is `FM-16B-24` — **block activation**           |
| Audit evidence | The test domain's own records; never mixed with production evidence                                             |

---

## 3. Prohibited

```text
NO timestamp-derived randomness.
NO UUID used as cryptographic randomness — of any version.
NO application-level PRNG (language `random`, `Math.random`, seeded PRNGs).
NO shared nonce source between two consumers.
NO reuse of a nonce, ever, for any purpose.
NO silent fallback to a weaker source on error, timeout or unavailability.
NO deterministic test seed in production.
NO derivation of a nonce from data the adversary can influence or observe.
NO "top up" of insufficient entropy with a hash of something predictable.
NO reuse of a guardian's randomness across election contexts.
```

| ID      | Rule                                                                                                                                             |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| `RN-07` | Each consumer class has **its own generator instance**. No instance serves two of §2.1, §2.2, §2.3                                               |
| `RN-08` | **Nonce reuse is detected where detectable and fatal where detected**, and it is a `confirmed_compromise` of the ballot or key material involved |
| `RN-09` | There is **no fallback path.** A weaker source is not a degraded mode; it is a refusal                                                           |
| `RN-10` | No random value is ever logged, traced, exported, included in telemetry, written to an error report or held after use                            |
| `RN-11` | Memory holding random material is zeroized where the platform makes that meaningful, and the limitation is recorded where it does not            |

---

## 4. Duplication hazards

Three ways a correct generator produces a repeated value.

| Hazard                          | Where it bites                                                                                   | Control                                                                                                                                                                                            |
| ------------------------------- | ------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Process fork**                | Server-side, after `fork()` without reseeding                                                    | Reseed on fork; or single-threaded, no-fork ceremony and signing processes                                                                                                                         |
| **VM or container snapshot**    | Snapshot-and-resume replays generator state — the classic silent nonce repeat                    | **Ceremony devices are never virtualised and never snapshotted** (`KC-16B-05`). Server-side components reseed on resume and record it                                                              |
| **Browser context duplication** | Tab duplication, session restore, back/forward cache, or a restored page reusing in-memory state | The client draws its ballot nonce **once per ballot, at preparation, from the platform CSPRNG**, and never carries a nonce across a page lifecycle. A restored page starts a new ballot or refuses |

| ID      | Rule                                                                                                                |
| ------- | ------------------------------------------------------------------------------------------------------------------- |
| `RN-12` | Ceremony key material is generated **on a dedicated, non-virtualised device**                                       |
| `RN-13` | Any server-side component that may be snapshotted, migrated or restored **reseeds on resume** and records the event |
| `RN-14` | The Voting Client **never persists** random material across a page lifecycle, and never restores one (`CC-07`)      |
| `RN-15` | A restored or duplicated client context **starts a fresh ballot or refuses**; it never continues one                |

---

## 5. Domain separation of randomness

Extending `PACK-16A-ACCESSIBILITY-REQUIREMENTS.md`'s and PACK-15's test-key
discipline (`KC-20`) to randomness:

```text
development · test · staging · ceremony rehearsal · production · verification
```

| ID      | Rule                                                                                                                             |
| ------- | -------------------------------------------------------------------------------------------------------------------------------- |
| `RN-16` | Deterministic-seed mode is **structurally unreachable** in a production build — absent from the artifact, not disabled by a flag |
| `RN-17` | Rehearsal uses its own generator instances, its own keys and its own context identifiers, and its material is destroyed after    |
| `RN-18` | **Production guardian material never enters any other domain**, in any direction                                                 |
| `RN-19` | A rehearsal transcript **cannot activate a real election** — it carries a domain marker that configuration validation refuses    |
| `RN-20` | Test vectors published for interoperability use **test keys only**, and this is demonstrable rather than asserted (`KC-20`)      |

---

## 6. Failure behaviour, stated once

```text
FAIL CLOSED
NO BALLOT
NO KEY CEREMONY
NO FALLBACK RANDOMNESS
```

| Condition                                          | Behaviour                                                       | Reason code                         | Reference   |
| -------------------------------------------------- | --------------------------------------------------------------- | ----------------------------------- | ----------- |
| Client startup randomness self-test fails          | Refuse to encrypt; offer another device or the fallback channel | `ballot.randomness_insufficient`    | `FM-16B-06` |
| Ceremony device health test fails                  | Ceremony does not start                                         | `ceremony.randomness_health_failed` | `FM-16B-05` |
| Health test fails mid-ceremony                     | Ceremony **aborts**; material destroyed; restart from scratch   | `ceremony.randomness_degraded`      | `FM-16B-05` |
| Reseed fails after fork, resume or snapshot        | The component refuses to serve                                  | `crypto.reseed_failed`              | `FM-16B-05` |
| Nonce repetition detected                          | Treated as `confirmed_compromise` of the affected material      | `crypto.nonce_reuse_detected`       | `FM-16B-23` |
| Deterministic seed reachable in a production build | **Activation blocked**                                          | `crypto.test_mode_reachable`        | `FM-16B-24` |

**A voter who is refused because their device cannot generate sound
randomness has been protected, not obstructed**, and the interface must say
so in those terms (`AX-08`). The alternative — encrypting with weak
randomness — produces a ballot that looks perfect and is readable.

---

## 7. What cannot be verified, stated honestly

| Cannot be verified                                          | Consequence                                                                      |
| ----------------------------------------------------------- | -------------------------------------------------------------------------------- |
| That a voter's browser produced sound randomness            | **No verifier can detect a weak ballot nonce.** Nothing in the record reveals it |
| That a guardian's device produced sound randomness          | Only the device's own health tests attest, and they attest to themselves         |
| That a generator was not backdoored                         | Outside every control available here                                             |
| Retrospectively, that any specific value was well-generated | By construction — the values are secret or destroyed                             |

**This is the sharpest residual in this round.** Every other property in
`PACK-16B` is checkable from published evidence by someone who does not
trust EPD². Randomness quality is not, in either direction, and no
architecture makes it so. It is recorded as `RB-08` and it is named in the
claims discipline: **EPD² may state that it requires and tests for sound
randomness; it may not state that ballots were soundly randomised.**

---

## 8. What this document does not decide

```text
The client's randomness self-test design      → PACK-16C
The specific DRBG instantiation and library    → PACK-16D
Ceremony device procurement                    → PACK-16D, GOVERNANCE
Which AIS 20/31 class guidance requires        → VO-02
Server-side deployment and snapshot policy     → PACK-17
```

**SPECIFIED. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY. NOT LEGALLY
ACTIVATED.**
