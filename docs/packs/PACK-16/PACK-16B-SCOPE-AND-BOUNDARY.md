# PACK-16B — Scope and Boundary

**Round:** PACK-16B — Cryptographic Parameters, Key Ceremony and Trustee Architecture. **Specification and ADR only. No code. No cryptographic code. Not implemented. Not an implementation candidate. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**Baseline:** `EPD2_PACK-16A_VERIFIABLE_VOTING_PROTOCOL_AND_BALLOT_MODEL_SPEC_ADR_CORRECTED_CANDIDATE.zip`
SHA-256 `14b65dae696eeb80e237fbb33a14f7bad55e8ca043672ba0fa2e86a90b011f9e`
**ADR:** `ADR-100`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

Evidence references `[F-nn]` resolve in
`PACK-16B-PROTOCOL-EVIDENCE-MATRIX.md`, the single canonical PACK-16B
evidence registry. PACK-16A evidence is cited as `[E-nn]` and resolves in
`PACK-16A-PROTOCOL-EVIDENCE-MATRIX.md`; the two registries do not overlap
and neither redefines the other's identifiers.

---

## 0. The question this round answers

PACK-16A selected a protocol family and left every number unchosen. This
round exists to answer one question:

> **Which cryptographic parameters and organizational conditions are
> necessary for `EPD2-HOM-1` to be implementable without a hidden master
> key, without single-admin decryption, without silent downgrade, without
> unverifiable parameter generation and without an undemonstrable key
> ceremony?**

Three of those five turned out to have good answers available. Two required
EPD² to specify what the selected specification does not (§4).

---

## 1. Inherited and not re-openable

`ADR-099` is accepted for continuation. This round does not revisit:

```text
EPD2-HOM-1
ElectionGuard 2.1 protocol lineage
homomorphic tally model
exponential-ElGamal construction family
Benaloh cast-or-challenge
NIZK well-formedness proofs
plaintext-knowledge proof requirement BM-14
no-revoting decision
EPD2-MIX-1 deferred / prohibited status
PACK-15 identity boundary
Voting Client isolation
no-intermediate-tally invariant
bulletin-board requirement
no person-to-ballot linkage
```

Nor the inherited invariants of `PACK-16A-SCOPE-AND-BOUNDARY.md` §5, nor
`CC-01` … `CC-10`, nor `BM-01` … `BM-35`, nor `TP-01` … `TP-07`, nor
`KC-01` … `KC-27`, except where a **factual correction** is recorded in
§5 below — which corrects a description of the selected specification, not
a decision.

**No architectural blocker was raised by this round.** §7 records the
conditions under which one would have been, and why none of them was met.

---

## 2. Scope

PACK-16B produces, **as documents only**:

1. this boundary;
2. a parameter assessment against primary cryptographic guidance
   (`PACK-16B-CRYPTOGRAPHIC-PARAMETER-ASSESSMENT.md`);
3. a selected parameter profile and its registry
   (`PACK-16B-PARAMETER-SET-SPECIFICATION.md`);
4. an agility model that creates no downgrade surface
   (`PACK-16B-CRYPTOGRAPHIC-AGILITY-MODEL.md`);
5. a normative transcript and domain-separation model
   (`PACK-16B-FIAT-SHAMIR-AND-DOMAIN-SEPARATION.md`);
6. a randomness architecture (`PACK-16B-RANDOMNESS-ARCHITECTURE.md`);
7. guardian count, quorum and independence
   (`PACK-16B-GUARDIAN-AND-QUORUM-MODEL.md`,
   `PACK-16B-GUARDIAN-INDEPENDENCE-MATRIX.md`);
8. the guardian lifecycle (`PACK-16B-GUARDIAN-LIFECYCLE.md`);
9. the key ceremony and its transcript
   (`PACK-16B-KEY-CEREMONY-SPECIFICATION.md`,
   `PACK-16B-CEREMONY-TRANSCRIPT-SPECIFICATION.md`);
10. a complaint and disqualification protocol
    (`PACK-16B-COMPLAINT-AND-DISQUALIFICATION-MODEL.md`);
11. custody, backup, recovery and compensation
    (`PACK-16B-KEY-CUSTODY-REQUIREMENTS.md`,
    `PACK-16B-BACKUP-RECOVERY-AND-COMPENSATION.md`);
12. compromise and quorum loss
    (`PACK-16B-COMPROMISE-AND-QUORUM-LOSS-MODEL.md`);
13. the remote-ceremony decision
    (`PACK-16B-REMOTE-CEREMONY-ASSESSMENT.md`);
14. roles, incidents, reason codes and failure handling
    (`PACK-16B-ROLE-SEPARATION-MATRIX.md`,
    `PACK-16B-INCIDENT-AND-NOTIFICATION-MODEL.md`,
    `PACK-16B-REASON-CODE-SPECIFICATION.md`,
    `PACK-16B-FAILURE-AND-ABORT-MATRIX.md`);
15. obligations handed forward
    (`PACK-16B-IMPLEMENTATION-EVALUATION-CRITERIA.md`,
    `PACK-16B-TEST-VECTOR-AND-FORMAL-REVIEW-REQUIREMENTS.md`);
16. evidence, open decisions, FIR, canon, acceptance, report, handover;
17. `docs/adr/ADR-100-CRYPTOGRAPHIC-PARAMETERS-KEY-CEREMONY-AND-TRUSTEE-ARCHITECTURE.md`,
    status `proposed`.

### 2.1 Out of scope, explicitly

```text
NO PRODUCTION CODE          NO CRYPTOGRAPHIC CODE
NO MIGRATIONS               NO API IMPLEMENTATION
NO EVENT IMPLEMENTATION     NO FRONTEND IMPLEMENTATION
NO TEST IMPLEMENTATION      NO CI CHANGES
NO DEPENDENCY CHANGES       NO VERSION BUMP
```

And, deferred by name:

| Deferred to | What                                                                                                                                                       |
| ----------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| PACK-16C    | Casting and verification protocol messages; the bulletin board; the receipt surface; the ballot-side use of the transcript model; reason-code registration |
| PACK-16D    | Any code; the library selection itself; the ceremony application; test-vector production                                                                   |
| PACK-17     | Ceremony network and infrastructure security; venue security; resilience; archival operations                                                              |
| GOVERNANCE  | Guardian appointment; guardian organizations; activation of any context                                                                                    |

**No product, vendor, library, HSM model or key-management service is
selected by this round.** Permitted _classes_ are selected
(`PACK-16B-KEY-CUSTODY-REQUIREMENTS.md`), and mandatory _evaluation
criteria_ are fixed (`PACK-16B-IMPLEMENTATION-EVALUATION-CRITERIA.md`).

---

## 3. What this round decided

```text
PARAMETER PROFILE   EPD2-CRYPTO-1
                    = the ElectionGuard 2.1.0 fixed standard baseline
                      parameters, unmodified, bound into an EPD² profile
                      that adds obligations and changes no value

GROUP DECISION      Option A — preserve the finite-field profile.
                    Options B, C and D assessed and rejected, with reasons.

QUORUM              k = 3 of n = 5 (default profile)
                    k = 4 of n = 7 (high-assurance profile)
                    No reduction for small electorates.

CEREMONY            Controlled hybrid or fully in-person.
                    Fully remote ceremony PROHIBITED in the initial profile.

BACKUP              Per-guardian, guardian-custodied backup of that
                    guardian's own share only. Everything else prohibited.

COMPENSATION        Does not exist in the selected specification version,
                    is not reintroduced, and absence tolerance is exactly
                    n − k.

BREAK-GLASS         No break-glass decryption, in any form, ever.
```

---

## 4. The two things EPD² had to specify itself

The research behind this round produced one finding that reshaped it: **the
selected specification is strong exactly where it is verifiable and thin
exactly where it is procedural.**

**First — bad shares.** The specification's entire treatment of a failed
share verification is that the receiving guardian _"complains to the
election administrator and all other guardians. This triggers an
out-of-band investigation"_, that such an investigation _"does not
necessarily allow identification of a misbehaving guardian"_, and that key
generation is then _"started from scratch"_ `[F-12]`. There is no
disqualification predicate, no complaint format, no deadline, no
adjudication authority, no liveness bound, and the encrypted shares are not
part of the published election record — so share distribution is not
publicly verifiable at all `[F-12]`.

That is a reasonable place for a cryptographic toolkit to stop. It is not a
place an election architecture can stop, because a single malicious
guardian can otherwise force unbounded restarts and no evidence
distinguishes the accuser from the accused.
`PACK-16B-COMPLAINT-AND-DISQUALIFICATION-MODEL.md` is EPD²'s own
specification of that layer, and it is additive: it publishes more, decides
faster and attributes better, and it changes no cryptographic computation.

**Second — the ordering of publication during key generation.** The
specification removed Pedersen's commit-then-open round `[F-14]`, and the
published literature shows that a distributed key generation without it
permits a party acting last to bias the joint key `[F-15]`. The
specification deploys precisely the right countermeasure — a hash
pre-commitment round — **in the decryption protocol** and not in key
generation `[F-13]`, `[F-16]`. `PACK-16B-KEY-CEREMONY-SPECIFICATION.md`
§4 adds an EPD² pre-publication commitment round **at the orchestration
layer**, outside the specification's hash computations, so that it changes
no challenge, no proof, no transcript field consumed by a conforming
verifier, and no interoperability property.

Both additions are recorded in `ADR-100` as EPD² profile obligations, not
as changes to the protocol.

---

## 5. One factual correction to PACK-16A, recorded openly

`PACK-16A-TRUSTEE-AND-CEREMONY-REQUIREMENTS.md` `KC-11` reads:

> _"Lost-trustee handling. **Compensated shares** cover an absent guardian
> within the quorum; absence is published, not concealed."_

**Compensated decryption does not exist in ElectionGuard 2.1.0.** The word
"compensated" appears nowhere in the specification; the mechanism belonged
to the 1.x lineage. In 2.1 decryption is direct Lagrange interpolation over
the set `U` of available guardians with `|U| ≥ k`, and the specification
explicitly refuses to reconstruct a missing guardian's secret — _"it is
preferable to not release any missing secret … instead only release the
partial decryptions that the secret would have produced"_ `[F-11]`.

| Aspect                                                    | `KC-11` as written | Corrected                              |
| --------------------------------------------------------- | ------------------ | -------------------------------------- |
| **Requirement — absence within the quorum is survivable** | unchanged          | unchanged                              |
| **Requirement — absence is published, not concealed**     | unchanged          | unchanged                              |
| **Mechanism**                                             | compensated shares | direct Lagrange over the available set |
| **Absence tolerance**                                     | unstated           | exactly `n − k`                        |

**No requirement changes. No invariant changes. No decision changes.** The
mechanism description was inherited from the `[E-04]` reading of the
specification, which conflated the 2.1 construction with its predecessor.
The correction is favourable: a construction with no compensation material
has nothing to store, nothing to leak and nothing that could quietly alter
the effective threshold — which is exactly what `KC-14` and `KC-15` were
written to prevent.

`PACK-16B-BACKUP-RECOVERY-AND-COMPENSATION.md` §5 is the full treatment.

---

## 6. Obligations discharged from PACK-16A

| Inherited        | Discharged where                                                                |
| ---------------- | ------------------------------------------------------------------------------- |
| `KC-01`…`KC-05`  | Guardian and quorum model §2–§4                                                 |
| `KC-06`          | Key ceremony §5 (guardian authentication and device attestation)                |
| `KC-07`…`KC-09`  | Ceremony transcript specification                                               |
| `KC-10`          | Key ceremony §14; failure matrix `FM-16B-19`                                    |
| `KC-11`…`KC-13`  | Compromise and quorum-loss model; corrected per §5 above                        |
| `KC-14`, `KC-15` | Backup, recovery and compensation §2–§4                                         |
| `KC-16`          | Role separation matrix §2                                                       |
| `KC-17`, `KC-18` | Incident and notification model                                                 |
| `KC-19`          | Parameter assessment §6 — **discharged with an unusually strong result**        |
| `KC-20`          | Test and rehearsal separation — `PACK-16B-KEY-CEREMONY-SPECIFICATION.md` §9     |
| `KC-21`, `KC-22` | Parameter assessment §3–§5                                                      |
| `KC-23`…`KC-26`  | Implementation evaluation criteria                                              |
| `KC-27`          | Cryptographic agility model §6                                                  |
| `TP-01`…`TP-07`  | Guardian and quorum model §3 — every principle satisfied by the selected values |

### 6.1 `KC-19` — the finding worth stating in the boundary

`KC-19` required _"published, independently reproducible parameter
provenance"_, and it exists because of `F-INF-3`: in the Swiss Post/Scytl
case the proof system was sound and the commitment parameters were
_"just randomly generated without a proof of how they arose"_, which
permitted transcripts that pass verification while altering votes
(`[E-33]`).

The selected parameters are not randomly generated. `p` is derived by a
published rule from the binary expansion of ln(2), with the search offset
`δ` printed in the specification; `q = 2^256 − 189`; `r = (p−1)/q`; and
`g = 2^r mod p` `[F-02]`. **The research supporting this round regenerated
all four values from the published derivation rule and confirmed
byte-for-byte agreement with the specification's printed hex, including
`g^q mod p = 1` and the primality of `p`, `q` and `r/2`** `[F-03]`.

`KC-19` is therefore discharged not by a promise but by a reproduction, and
`PACK-16B-TEST-VECTOR-AND-FORMAL-REVIEW-REQUIREMENTS.md` `TV-01` makes
that reproduction a standing acceptance test rather than a one-off.

---

## 7. Architectural-blocker conditions — assessed, none met

`ADR-099` would have had to be re-opened, rather than quietly worked
around, under any of the following. Each was assessed:

| Condition                                                            | Met?   | Basis                                                                                                            |
| -------------------------------------------------------------------- | ------ | ---------------------------------------------------------------------------------------------------------------- |
| The selected parameters fall below applicable cryptographic guidance | **No** | 4096-bit modulus against a recommended 3000; 256-bit subgroup order against a recommended 250 `[F-21]`, `[F-22]` |
| The construction cannot be used in any permitted profile             | **No** | Modes A, B, D and E of the legal boundary are unaffected                                                         |
| Strong Fiat–Shamir is not actually present in the specification      | **No** | Present in all three proof families, with statement and context in every challenge `[F-08]`                      |
| Parameter provenance is unverifiable                                 | **No** | Independently reproduced `[F-03]`                                                                                |
| No parameter set can be operated without a downgrade surface         | **No** | The parameters are fixed by the specification, which removes negotiation entirely `[F-04]`                       |
| A quorum model satisfying `TP-01`…`TP-07` does not exist             | **No** | 3-of-5 and 4-of-7 both satisfy every principle                                                                   |

**One condition is deferred rather than answered, and it is dated.** Current
German guidance recommends classical key agreement **only until the end of
2031**, and **the end of 2030** for very high protection requirements
`[F-25]`. That is not a blocker today; it is a **deprecation date**, and
§4 of `PACK-16B-CRYPTOGRAPHIC-AGILITY-MODEL.md` makes it a property of the
parameter set rather than a note in a risk register.

---

## 8. What this round does not establish

```text
That the parameters are appropriate — no cryptographic reviewer has
   assessed this profile, and OD-P16A-06 remains open.
That the key ceremony is secure — no peer-reviewed analysis of the
   selected specification's key ceremony was LOCATED by this round,
   which is not proof that none exists.
That an implementation exists — none does, and OD-P16A-04 is answered
   with criteria, not with a selection.
That any election may be held — none may.
That FIR-INV-002 is closed — it is not, and this round cannot close it.
```

**SPECIFIED. ASSESSED. REQUIRES EXTERNAL CRYPTOGRAPHIC REVIEW. NOT
PRODUCTION READY. NOT LEGALLY ACTIVATED. PACK-16C MUST NOT START BEFORE
ACCEPTANCE.**
