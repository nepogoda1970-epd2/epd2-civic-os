# PACK-16A — Specification Report

**Round:** PACK-16A — Verifiable Voting Protocol and Ballot Model Selection. **Specification and ADR only. No code. Not implemented. Not an implementation candidate. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**Baseline:** `EPD2_PACK-15_VOTING_TRUST_BOUNDARY_ELIGIBILITY_CREDENTIAL_SEPARATION_0.15.0_FINAL_PASS.zip`
SHA-256 `38697c0a0bca9d211bf9f44ec5c2f7b475d86bd38eb1ccc10bc9521c3f2f087a`
**ADR:** `ADR-099`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 1. What was done

The actual PACK-15 baseline was extracted and read — the specification, the
matrices, the threat model, the catalogues, `ADR-088` … `ADR-098`, the
canonical domain and event model, and the Master Register — rather than
quoted from a handover. Version constants were read from the tree
(`REPOSITORY_VERSION = 0.15.0`, `CANON_VERSION = 0.8.0`), not from a claim.

Nine verifiable-voting protocol families were then assessed against primary
sources: official specifications, peer-reviewed papers, official caveat and
limitation documents, official repositories, a binding regulatory
ordinance, a constitutional judgment, current national technical guidance
and party law. **Fifty-nine substantive evidence entries** were recorded —
with source title, issuing institution, version and date, source type, URL,
relevant section, property supported, scope of support, limitations and the
documents citing each — plus **one reserved identifier**, giving **sixty
allocated Evidence IDs** in a **single canonical registry**,
`PACK-16A-PROTOCOL-EVIDENCE-MATRIX.md`. Each entry is classified as
protocol property, implementation property, legal or inference. Items that
could not be verified were marked **UNVERIFIED** and support no conclusion.

From that, one protocol family was selected, bounded into one profile,
extended with a threat model, a lifecycle, a board specification, ceremony
obligations, role separation, privacy flows, a failure model, accessibility
constraints and reason-code namespaces, and recorded as a **proposed** ADR.

**No code was written. No version was changed. No canon was amended. No FIR
obligation was closed.**

---

## 2. The decision

```text
SELECTED PROTOCOL FAMILY
  Homomorphic exponential-ElGamal ballots with threshold distributed key
  generation and decryption, non-interactive zero-knowledge well-formedness
  proofs, and Benaloh cast-or-challenge, in the lineage of the
  ElectionGuard Design Specification 2.1.0.

SELECTED PROFILE
  EPD2-HOM-1 — cardinal ballots, homomorphic tally.

DEFINED, NOT SELECTED, PROHIBITED PENDING RESEARCH
  EPD2-MIX-1 — ordinal ballots, mixnet tally.

REVOTING
  None. Explicitly decided, not deferred.
```

### 2.1 The argument, in one paragraph

The selected family's most-cited limitation is that it does no eligibility
and no authentication, requiring both to be established outside it and
asking only that ballots cast not exceed voters entitled `[E-06]`. For
every other integrator that is a gap. For EPD² it is a specification of the
interface PACK-15 already built: eligibility settled on the far side of a
trust boundary, one artifact crossing, no shared per-participation
reference, and an aggregate count as the only figure the two sides may
share. The boundary and the protocol were designed independently, and they
meet without either being bent. Everything else — homomorphic-only tally,
threshold guardians, cast-or-challenge, a published verifier
specification, an MIT licence — reinforces a fit that already existed.

---

## 3. What the research found that changed the design

Three findings emerged from the sources rather than from any one of them,
and each became a requirement rather than a remark.

**Ballot independence is the recurring systemic failure of deployed
verifiable voting systems.** Cortier–Smyth on Helios, Müller on Estonian
IVXV, and Verificatum's own Pfitzmann warning are three instances of one
gap: a submitted ciphertext with no proof of knowledge of its plaintext is
malleable, and malleability is a privacy attack. Two widely deployed
systems learned this from outside researchers years after deployment.
→ **`BM-14`: every submitted ballot carries a proof of knowledge of its
plaintext.**

**Weak Fiat–Shamir recurs in production code and survives its own published
fix.** Found in Helios in 2012, found again in Swiss Post/Scytl in 2019,
and still present in Helios master in 2026 despite a version-4
specification that corrects it. → **`AC-P16A-039`: the chosen
implementation must be _shown by test_ to use strong Fiat–Shamir. Not
assumed.**

**Mixnet risk in practice is parameter-generation and integration risk, not
proof-system risk.** In the Swiss case the proof system was sound; the
commitment parameters were generated "without a proof of how they arose",
and the routine that produced them produced exactly the trapdoor needed to
break binding — yielding transcripts that pass verification while altering
votes. → **`BM-33`, `KC-19`: published, independently reproducible
parameter provenance — and no mixnet profile is activated in this round.**

---

## 4. What was refused

| Refused                                      | Because                                                                                            |
| -------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| Inventing a voting protocol                  | No cryptographic research capacity; the one risk process cannot mitigate                           |
| Belenios as base                             | Its credential list pairs voter identity with a voting-side reference — the row PACK-15 §3 forbids |
| Helios as base                               | Weak Fiat–Shamir in shipping code; no ballot weeding; n-of-n trustees; names beside ciphertexts    |
| Estonian IVXV as base                        | The identity↔ciphertext binding is stored and severed by a trusted offline procedure               |
| A mixnet profile now                         | Individual-ballot decryption is a preference-pattern channel small-cell control cannot close       |
| Revoting                                     | It requires a persistent voting-side per-participant handle, and it costs verifiability            |
| A recovery path for a lost trustee quorum    | A recoverable secret is worse than an unrecoverable election                                       |
| A dispute mechanism that decrypts one ballot | Consent does not make a linkage capability safe; a capability that exists can be compelled         |
| Claiming coercion resistance                 | It is not achievable for remote voting, and no assessed system claims it                           |
| Claiming BSI or BVerfG compliance            | Nothing is certified; the Court has never ruled on cryptographic verifiability                     |

---

## 5. Documents produced

| Document                                        | What it settles                                                                                                                        |
| ----------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| `PACK-16A-SCOPE-AND-BOUNDARY.md`                | The inherited boundary as obligations; `CC-01`…`CC-10`; `NIT-01`…`NIT-07`                                                              |
| `PACK-16A-PROTOCOL-COMPARISON.md`               | Nine families assessed; five structural filters; verdicts                                                                              |
| `PACK-16A-PROTOCOL-EVIDENCE-MATRIX.md`          | **The single canonical Evidence Registry** — 59 substantive entries, 1 reserved ID, 60 allocated; three findings; contradictions shown |
| `PACK-16A-THREAT-MODEL.md`                      | Forty-two threats continuing PACK-15's thirty-nine                                                                                     |
| `PACK-16A-BALLOT-MODEL-SPECIFICATION.md`        | The profile; `BM-01`…`BM-35`; ten residual risks; six invalidating conditions                                                          |
| `PACK-16A-ELECTION-PROFILE-MATRIX.md`           | Fourteen election types; `MS-01`…`MS-05`; `SD-01`…`SD-09`                                                                              |
| `PACK-16A-REVOTING-AND-BALLOT-LIFECYCLE.md`     | The revoting decision and its proof attempt; fourteen states; `EX-01`…`EX-07`                                                          |
| `PACK-16A-COERCION-AND-RECEIPT-BOUNDARY.md`     | Six layers; permitted and prohibited claims registries                                                                                 |
| `PACK-16A-BULLETIN-BOARD-REQUIREMENTS.md`       | `BB-01`…`BB-37`; the layered publication model and its justification                                                                   |
| `PACK-16A-TRUSTEE-AND-CEREMONY-REQUIREMENTS.md` | `KC-01`…`KC-27`; `TP-01`…`TP-07`; the no-escrow trade                                                                                  |
| `PACK-16A-ROLE-SEPARATION-MATRIX.md`            | Sixteen roles; eleven prohibitions; ten dangerous collusion combinations                                                               |
| `PACK-16A-GERMAN-LEGAL-BOUNDARY.md`             | Nine modes; the ten-item governance gate; the legal source list                                                                        |
| `PACK-16A-PRIVACY-DATA-FLOW-MATRIX.md`          | Twelve flows; seven correlation channels; eight mechanisms assessed                                                                    |
| `PACK-16A-FAILURE-AND-ABORT-MODEL.md`           | `FM-P16A-01`…`25`; uncertifiable results                                                                                               |
| `PACK-16A-ACCESSIBILITY-REQUIREMENTS.md`        | `AX-01`…`AX-43`; seven named security conflicts                                                                                        |
| `PACK-16A-REASON-CODE-SPECIFICATION.md`         | Eleven namespaces; `RC-01`…`RC-10`; codes deliberately absent                                                                          |
| `PACK-16A-FIR-COVERAGE-MATRIX.md`               | Register assessment; zero closures; zero creations                                                                                     |
| `PACK-16A-CANON-ASSESSMENT.md`                  | `CQ-01`…`CQ-06`; `CA-01`…`CA-03`; no canon change                                                                                      |
| `PACK-16A-ACCEPTANCE-MATRIX.md`                 | Ninety-six criteria; zero met by a running system                                                                                      |
| `PACK-16A-OPEN-DECISIONS.md`                    | Twelve open decisions with owners and closing rounds                                                                                   |
| `PACK-16A-SPECIFICATION-REPORT.md`              | This document                                                                                                                          |
| `PACK-16A-HANDOVER.md`                          | The handover and archive facts                                                                                                         |
| `docs/adr/ADR-099-…`                            | The decision record, status `proposed`                                                                                                 |

---

## 6. What this round does not establish

```text
That the architecture is correct — it has not been reviewed.
That it is implementable — no implementation of the selected specification
   version is production-grade.
That it is legal — no legal assessment has been performed.
That it protects a coerced voter — it does not, and no remote system does.
That FIR-INV-002 is closed — it is not, and this round cannot close it.
That any election may be held with it — none may.
```

---

## 7. The five things a reviewer should attack first

Offered because a review that starts in the right place is worth more than
a thorough one that starts in the wrong place.

1. **`OD-P16A-04` and `RR-01`.** The selected specification has no
   production-grade implementation. Is selecting a specification rather
   than a library the right call, or does it defer an unsolvable problem?
2. **The revoting refusal.** `PACK-16A-REVOTING-AND-BALLOT-LIFECYCLE.md`
   §2.2 argues that supersession requires a persistent voting-side handle.
   Is there a construction that discharges `SU-05`? If so, the decision is
   wrong.
3. **The board withholding ballot entries before closure** (`BB` §3.1,
   `RR-11`). It is required by `ADR-094` and it is a real reduction in
   transparency. Is `BB-22`…`BB-26` an adequate substitute?
4. **`RR-09` and `OD-P16A-06`.** There is no symbolic or cryptographic
   proof of the profile as composed, and composition is where this field's
   failures concentrate.
5. **The German legal reading** in `GLB` §4, particularly the assertion
   that § 15 Abs. 2a PartG permits binding internal electronic votes and
   that statutory nomination is closed. It is the load-bearing legal claim
   and it is an architecture assessment, not legal advice.

---

## 8. Verification performed

`PACK-16A-HANDOVER.md` §5 records the local verification result in full,
including what could not be checked in this environment.

**SPECIFIED. ASSESSED. SELECTED FOR ARCHITECTURAL REVIEW. REQUIRES EXTERNAL
REVIEW. REQUIRES LEGAL ASSESSMENT. NOT PRODUCTION READY. NOT LEGALLY
ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**
