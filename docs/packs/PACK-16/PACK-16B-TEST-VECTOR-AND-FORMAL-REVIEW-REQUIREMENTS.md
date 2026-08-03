# PACK-16B — Test Vector and Formal Review Requirements

**Round:** PACK-16B — Cryptographic Parameters, Key Ceremony and Trustee Architecture. **Specification and ADR only. No code. No cryptographic code. Not implemented. Not a PASS. No test is written by this round.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-100`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 0. The finding this document exists to answer honestly

```text
No peer-reviewed security analysis specifically covering the selected
ElectionGuard 2.1 key-ceremony composition was located in the sources
reviewed for PACK-16B.  [F-31]

This absence-of-evidence finding must not be interpreted as proof that
no such analysis exists.
```

That is the state of **the evidence located by this round's survey**, and
**it is not remedied by anything EPD² can do to its own repository.** A
bounded search establishes what was not found; it does not establish what
does not exist, and the two are not interchangeable. Writing more tests
does not produce a security proof; producing a specification document does
not produce peer review.

| ID       | Rule                                                                                                                     |
| -------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `TV-00`  | **`OD-P16A-06` is NOT closed by this document, this round, or any amount of internal testing.** It is given a named external deliverable, a named gate, and a status of `blocked pending cryptographic review` |

Anything in this document that reads like reassurance should be read against
`TV-00` first.

---

## 1. The eight obligations

| ID       | Obligation                                                                                                    | Owner            | Gate                                                        |
| -------- | ------------------------------------------------------------------------------------------------------------- | ---------------- | ----------------------------------------------------------- |
| `TV-01`  | **Parameter reproduction.** The fixed `p`, `q`, `r`, `g` are re-derived from their published derivation and compared bit for bit | PACK-16D        | **Blocking** — a parameter that cannot be reproduced is not a parameter |
| `TV-02`  | **Official upstream vectors** are obtained, run and reproduced bit for bit                                    | PACK-16D         | **Blocking**                                                |
| `TV-03`  | **EPD² profile vectors** are produced and published for every EPD²-specific construct — the `H_X` domain, the commitment round, the transcript encoding | PACK-16D         | **Blocking**                                                |
| `TV-04`  | **Negative and malformed-input vectors** are produced for every rejection path in the failure matrix          | PACK-16D         | **Blocking**                                                |
| `TV-05`  | **Serialization vectors** fix the canonical encoding, including the non-canonical forms that must be rejected  | PACK-16D         | **Blocking**                                                |
| `TV-06`  | **Domain-separation vectors** cover all 27 upstream tags and every EPD² string tag                            | PACK-16D         | **Blocking**                                                |
| `TV-07`  | **Independent implementation and differential testing** against an implementation EPD² did not write          | PACK-16D + `R-18` | **Blocking for activation**, not for PACK-16D acceptance    |
| `TV-08`  | **External cryptographic review** of the parameter profile, the ceremony orchestration and the EPD² additions  | `R-18`, external | **Blocking for activation.** This is `OD-P16A-06`'s deliverable |
| **`TV-19`** | **Independent conforming-verifier interoperability test** — an election record produced under the EPD² profile is accepted by a conforming ElectionGuard 2.1 verifier that EPD² did not write or operate | PACK-16D + independent | **Blocking for implementation acceptance.** §1.1 |

```text
TV-01…TV-06 are things EPD² can do to itself.
TV-07, TV-08 and TV-19 are things EPD² cannot do to itself, and they are
the three that matter for the finding above.
```

### 1.1 `TV-19`, and why the interoperability claim is conditional on it

**No verifier-consumed ElectionGuard 2.1 field is changed by the PACK-16B
orchestration profile.** That is a statement about the specification, made
by reading it, and it is the strongest statement this round is entitled to.

**It is not a demonstration.** Until an election record produced under this
profile has actually been accepted by a conforming verifier that EPD² did
not write, the correct wording everywhere in this pack is:

```text
EXPECTED SPECIFICATION COMPATIBILITY,
CONDITIONAL ON INDEPENDENT VERIFIER TESTING.
```

| ID       | Rule                                                                                                                |
| -------- | ----------------------------------------------------------------------------------------------------------------------- |
| `TV-20`  | **No document in this pack may claim FULL interoperability, PROVEN compatibility, or that every conforming verifier accepts an EPD² record**, until `TV-19` has been performed and published |
| `TV-21`  | `TV-19` is performed against a verifier **EPD² did not write and does not operate**, and its inputs, outputs and verdict are published in full — including a failure |
| `TV-22`  | A `TV-19` failure is a **finding about the EPD² profile first**, not about the verifier, and is investigated in that order |

**Nomenclature note.** An architectural audit referred to the independent
verifier test as "`TV-11`". In this document `TV-11` is a **review-scope**
rule (§4) and is unchanged and still binding; the verifier obligation was
carried by `TV-07` and `VC-05`, and is now stated explicitly and separately
as `TV-19` so that the two cannot be confused again.

---

## 2. The fourteen vector classes

| ID      | Class                             | Contents                                                                                          | Source                       | Obligation |
| ------- | --------------------------------- | ------------------------------------------------------------------------------------------------- | ---------------------------- | ---------- |
| `VC-01` | **Official upstream vectors**     | Whatever the specification's maintainers publish, run unmodified                                   | upstream                     | `TV-02`    |
| `VC-02` | **EPD² profile vectors**          | `H_X` derivation, commitment-round hashes, transcript checkpoint hashes, reason-code payloads       | EPD², published              | `TV-03`    |
| `VC-03` | **Positive vectors**              | Every operation with valid inputs and its expected output, per operation and per key set            | EPD² + upstream              | `TV-02`, `TV-03` |
| `VC-04` | **Negative vectors**              | Every rejection path in `PACK-16B-FAILURE-AND-ABORT-MATRIX.md`, one vector per `FM-16B-*`           | EPD²                         | `TV-04`    |
| `VC-05` | **Cross-language vectors**        | The same inputs run through at least two language implementations, outputs compared byte for byte; and a complete election record accepted by an independent conforming verifier | EPD² + independent           | `TV-07`, `TV-19` |
| `VC-06` | **Serialization vectors**         | 512/32/4-byte fixed-length forms; leading-zero, short, over-long and out-of-range rejections         | EPD²                         | `TV-05`    |
| `VC-07` | **Domain-separation vectors**     | All 27 upstream tags; every EPD² string tag; **cross-tag substitution must fail**                  | EPD²                         | `TV-06`    |
| `VC-08` | **DKG transcript vectors**        | A complete synthetic ceremony transcript for `k=3/n=5` and `k=4/n=7`, verifiable end to end          | EPD²                         | `TV-03`    |
| `VC-09` | **Complaint vectors**             | Each of the eleven complaint grounds, including both directions of `share_inconsistent`, with the adjudication each must produce | EPD²      | `TV-03`, `TV-04` |
| `VC-10` | **Compensated-decryption vectors**| **Unreachability vectors.** The mechanism does not exist (`BR-13`); the vectors assert that no input reaches a compensation path and that `compensation.*` cannot be emitted | EPD² | `TV-04` |
| `VC-11` | **Quorum-loss vectors**           | `h = k` (succeeds), `h = k − 1` (must fail cleanly, no partial result), `h = n` (succeeds), absence exactly `n − k` | EPD²             | `TV-04`    |
| `VC-12` | **Malformed-share vectors**       | Wrong index, wrong context, replayed from another ceremony, correct-looking but failing verification | EPD²                        | `TV-04`    |
| `VC-13` | **Parameter-downgrade vectors**   | Weaker set offered, digest mismatch, deprecated set past its date, prohibited set — each must be refused, none must negotiate | EPD²         | `TV-04`    |
| `VC-14` | **Historical-verification vectors**| A complete archived context re-verified years later from published material alone, with no live system | EPD², PACK-17               | `TV-03`, `TV-07` |

### 2.1 The three classes that are easy to get wrong

**`VC-10`** is the one an implementer will consider vacuous. It is not: its
purpose is to fail loudly if a future contributor reintroduces a
compensation path, which is precisely the drift `BR-13` exists to prevent.
A vector asserting that something is unreachable is a regression test on a
decision.

**`VC-11`'s `h = k − 1` case** must fail *cleanly* — no partial output, no
partial decryption published, no aggregate, no count. A test that only
asserts "an error occurs" passes against an implementation that leaks a
partial result first.

**`VC-14`** is the only class that tests the property the whole archive
exists for, and it cannot be run quickly: it needs a context, a full
archive, and a verifier built from published material by someone with no
access to EPD² systems.

---

## 3. What requires what — the assurance mapping

| Property                                                        | Paper proof | Symbolic analysis | Property-based | Differential | Independent impl. | Expert review |
| --------------------------------------------------------------- | ----------- | ----------------- | -------------- | ------------ | ----------------- | ------------- |
| Parameter derivation correctness                                 | –           | –                 | –              | ✓            | ✓                 | ✓             |
| Group and subgroup validation                                    | –           | –                 | **✓**          | ✓            | ✓                 | –             |
| Canonical encoding round-trip and rejection                      | –           | –                 | **✓**          | **✓**        | ✓                 | –             |
| Fiat–Shamir soundness in this transcript construction            | **✓**       | ✓                 | –              | –            | –                 | **✓**         |
| Domain separation completeness (no two contexts share an input)  | **✓**       | **✓**             | ✓              | –            | –                 | **✓**         |
| DKG correctness (share consistency, joint-key correctness)       | **✓**       | –                 | ✓              | ✓            | **✓**             | **✓**         |
| DKG secrecy under `< k` corruptions                              | **✓**       | –                 | –              | –            | –                 | **✓**         |
| Threshold decryption correctness                                 | **✓**       | –                 | ✓              | ✓            | **✓**             | ✓             |
| Ballot well-formedness proof soundness                           | **✓**       | ✓                 | –              | –            | –                 | **✓**         |
| Benaloh challenge indistinguishability                           | **✓**       | –                 | –              | –            | –                 | **✓**         |
| Commitment round binding (EPD² addition)                         | **✓**       | ✓                 | –              | –            | –                 | **✓**         |
| Complaint protocol resolution (EPD² addition)                    | –           | **✓**             | ✓              | –            | –                 | **✓**         |
| Transcript non-equivocation                                      | –           | ✓                 | ✓              | –            | ✓                 | ✓             |
| Randomness architecture adequacy                                 | –           | –                 | ✓              | –            | –                 | **✓**         |
| Side-channel posture                                             | –           | –                 | –              | –            | –                 | **✓**         |
| Archive re-verifiability                                         | –           | –                 | ✓              | ✓            | **✓**             | –             |

**Bold = the load-bearing method for that property.** Everything in the
"paper proof" column that is bold is a claim EPD² currently cannot make, and
§4 says what would let it.

### 3.1 The two EPD² additions carry the heaviest review burden

The complaint protocol and the pre-publication commitment round are
EPD²'s own work on top of a specification nobody has peer-reviewed. They sit
at the orchestration layer and change no hash input, no challenge and no
verifier-consumed field — which bounds the risk but does not remove it.

```text
An addition that changes no cryptographic input can still change what
an adversary can do with the timing of publication.
That is exactly what a commitment round is FOR, and exactly why it
needs someone who is not its author to look at it.
```

---

## 4. `OD-P16A-06` — the named deliverable and the gate

**The obligation is not "seek review". It is this:**

| Element                | Requirement                                                                                                              |
| ---------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| **Deliverable**        | A written cryptographic review, by an external party with no EPD² engagement other than the review, covering: (a) the parameter profile and its BSI assessment; (b) the Fiat–Shamir and domain-separation construction as EPD² uses it; (c) the DKG and threshold decryption as specified upstream; (d) **the two EPD² additions**; (e) the randomness architecture |
| **Form**               | Published in full, including findings EPD² did not act on, and including the reviewer's own statement of what they did not examine |
| **Reviewer**           | `R-18`, engaged per `RS-16B-15`; the engagement and any commissioning relationship published                              |
| **Gate**               | **Activation of any binding context is blocked until the review exists and its blocking findings are closed.** Non-binding internal use is permitted before it, with the gap published |
| **What does not count**| An internal review; a review by the implementation's own authors; a FIPS or Common Criteria certificate; a favourable press mention; a vendor assurance; this document |
| **Status**             | `blocked pending cryptographic review`                                                                                    |

| ID       | Rule                                                                                                                     |
| -------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `TV-09`  | **A missing review is published as missing**, on the same page as the system's other assurance claims, for as long as it is missing |
| `TV-10`  | **A review with findings is published with its findings open**, and each finding gets a dated disposition — closed, accepted with reason, or outstanding |
| `TV-11`  | **No review closes `OD-P16A-06` by covering only the upstream specification.** The EPD² additions are in scope or the review does not discharge the obligation |
| `TV-12`  | If the upstream specification receives a peer-reviewed analysis in the interim, that is **evidence toward** `TV-08` and does not by itself discharge it |

---

## 5. Upstream obligations EPD² cannot discharge

| Gap                                                                | EPD²'s only available response                                                             |
| ------------------------------------------------------------------ | -------------------------------------------------------------------------------------------- |
| No peer-reviewed analysis of the key ceremony **located** `[F-31]` | `TV-08`; publish the gap; the ceremony-form decision (`PACK-16B-REMOTE-CEREMONY-ASSESSMENT.md` §4) is made conservatively because of it |
| No peer-reviewed analysis of version 2.1 **located** `[F-31]`      | `TV-08`; version pinning (`CA-*`) so the analysed object is fixed                            |
| No published errata process upstream `[F-30]`                      | EPD²'s own errata record (`CA-22` lineage) and advisory intake                               |
| Two internal specification inconsistencies                          | Resolved locally and documented (`DS-16`), deferring to upstream if it resolves differently  |
| Known DKG-family bias results (GJKR)                                | Assessed in the parameter document; the commitment round addresses the analogous exposure at the orchestration layer, and this is **claimed as a mitigation, not as a fix** |

| ID       | Rule                                                                                                          |
| -------- | ----------------------------------------------------------------------------------------------------------------- |
| `TV-13`  | **EPD² does not describe an upstream gap as closed by an EPD² document.** Every row above stays open until an external artefact closes it |

---

## 6. Vector governance

| ID       | Rule                                                                                                             |
| -------- | -------------------------------------------------------------------------------------------------------------------- |
| `TV-14`  | Vectors are **published with the specification digest** they were produced against (`PS-*`)                        |
| `TV-15`  | A vector set is **versioned and never edited in place**; a corrected vector is a new vector with the correction recorded |
| `TV-16`  | **Vectors contain no production key material** and no production ballot, ever — synthetic inputs only (`CM-24`)     |
| `TV-17`  | Vector failures are **published**, including failures found after acceptance                                        |
| `TV-18`  | The vector suite is **run against every candidate implementation** during `OD-P16A-04` evaluation, and the results are part of the published assessment (`IM-03`) |

---

## 7. What this document does not decide

```text
Which verifier implementation TV-19 is run against → PACK-16D
Test framework, harness and CI integration     → PACK-16D
Who is engaged as reviewer                      → GOVERNANCE, OD-P16B-03
Review budget and timing                        → GOVERNANCE
Independent verifier implementation             → PACK-16C, PACK-17
```

**`OD-P16A-06` REMAINS OPEN AND IS RECORDED AS `blocked pending
cryptographic review`.**

**SPECIFIED. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY. NOT LEGALLY
ACTIVATED.**
