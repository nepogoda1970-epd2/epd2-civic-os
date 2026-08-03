# PACK-16C — Election Record Completeness Matrix

**Round:** PACK-16C — Casting, Receipt, Verification Client, Bulletin Board and Election Record. **Specification and ADR only. No code. No cryptographic implementation. Not implemented. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-101`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 0. What this matrix is for

`PACK-16C-ELECTION-RECORD-SPECIFICATION.md` lists 37 mandatory artefacts.
`PACK-16C-INDEPENDENT-VERIFIER-REQUIREMENTS.md` lists 21 checks. **This
document is the join**, in both directions, so that neither list can drift
from the other unnoticed.

```text
FORWARD   every check → the artefacts it consumes        §1
REVERSE   every artefact → the checks that need it       §2
GAP       artefacts no check needs   → justify or drop   §3
GAP       checks no artefact serves  → the record is incomplete   §3
```

### 0.1 Conditions that make the record INCOMPLETE

```text
a scheduled batch commitment is missing            TC-44, FM-16C-18
a commitment root cannot be recomputed             TC-41, FM-16C-22
an accepted ballot has no committed leaf           TC-42, FM-16C-25
an occupied real leaf has no ballot artefact       TC-42, FM-16C-25
a cover leaf enters the tally                      TC-43, FM-16C-26
a batch opening is missing or conflicting          TC-45, FM-16C-23
a batch reconciliation does not close              TC-42, FM-16C-27
```

**Each of these makes the completeness status `invalid` outright.** None is
a warning, none is recoverable by re-derivation, and none may be resolved by
an operator (`TC-54`).

| ID       | Rule                                                                                                              |
| -------- | --------------------------------------------------------------------------------------------------------------------- |
| `EC-01`  | **The record is complete if and only if both gap sections are discharged and no condition in §0.1 holds.** Completeness is a computed property of this matrix, not a judgement |
| `EC-02`  | **An artefact that no check consumes is either removed or given a stated non-verification purpose.** "Might be useful" is not a purpose (`ER-07`) |
| `EC-03`  | **A check with a missing artefact is a specification defect in this round**, not an implementation gap for PACK-16D to notice |

Artefact numbers below are the numbers used in
`PACK-16C-ELECTION-RECORD-SPECIFICATION.md` §1.

---

## 1. Forward: check → artefacts

| Check | Name | Artefacts consumed | Complete? |
| ----- | ---- | ------------------ | --------- |
| 1 | Manifest consistency | 1, 2, 6, 12, 32 | **yes** |
| 2 | Parameter-set consistency | 3, 4, 5, 12, 32 | **yes** |
| 3 | Ceremony transcript validation | 8, 9, 10, 24, 26 | **yes** |
| 4 | Joint-key derivation | 7, 8, 9, 10 | **yes** |
| 5 | Base-hash chain | 1, 3, 4, 7 | **yes** |
| 6 | Ballot well-formedness | 1, 2, 4, 7, 12 | **yes** |
| 7 | Confirmation codes | 7, 12, 13 | **yes** |
| 8 | Challenge validation | 4, 7, 14 | **yes** |
| 9 | Board inclusion | 23, 24, 26, 27 | **yes** |
| 10 | Board consistency | 24, 25, 26, 27 | **yes** |
| 11 | Uniqueness | 12, 13, 15, 23 | **yes** |
| 12 | Closure validation | 15, 16, 17, 22, 23 | **yes** |
| 13 | Decryption-share validation | 8, 9, 19, 20 | **yes** |
| 14 | Tally recomputation | 12, 16, 17, 18 | **yes** |
| 15 | Aggregate-result verification | 18, 19, 20, 21 | **yes** |
| 16 | Archive integrity | 23, 24, 32, and the archive checkpoint | **yes** |
| 17 | Batch cadence completeness | 6, 24, 33 | **yes** |
| 18 | Batch root recomputation | 33, 34 | **yes** |
| 19 | Batch reconciliation | 12, 14, 17, 33, 34, 35 | **yes** |
| 20 | Capacity-bound conformance | 1, 34, 35, 36 | **yes** |
| 21 | Capacity-incident completeness | 29, 33, 36, 37 | **yes** |

| ID       | Rule                                                                                                          |
| -------- | ----------------------------------------------------------------------------------------------------------------- |
| `EC-04`  | **No check consumes an artefact outside the mandatory 32.** No check depends on an optional or derived artefact, and none depends on a live EPD² service (`ER-03`, `ER-15`) |
| `EC-05`  | **Check 12 is the one that makes "the set" meaningful.** Without artefacts 16 and 17 together, a verifier can recompute a tally but cannot show it was the tally of the right ballots |
| `EC-13`  | **Check 19 is the one that makes "no late insertion" meaningful.** Without artefacts 33–35 together, a verifier can recompute a tally over a published set but cannot show that set existed before closure (`TC-53`) |
| `EC-14`  | **Checks 17–19 are performable only after closure**, because artefacts 34 and 35 exist only at closure. Before closure a verifier can check cadence and checkpoint consistency and nothing more — **that is the turnout guarantee, expressed as a limit on verification** (`IV-16`) |

---

## 2. Reverse: artefact → checks

| # | Artefact | Checks served | Also load-bearing for |
| - | -------- | ------------- | --------------------- |
| 1 | Election manifest | 1, 5, 6 | Voter-side manifest verification (`CF-*`) |
| 2 | Ballot styles | 1, 6 | Pipeline stage 8 |
| 3 | Protocol profile + digest | 2, 5 | Record interpretability (`ER-02`) |
| 4 | Parameter set | 2, 5, 6, 8 | Every recomputation |
| 5 | Parameter approval record + open obligations | 2 | Honest publication of `VO-08` |
| 6 | Election context descriptor | 1 | Window admissibility, `timestamp_granularity` |
| 7 | Joint key + base-hash chain | 4, 5, 6, 7, 8 | — |
| 8 | Guardian commitments + DKG transcript | 3, 4, 13 | — |
| 9 | Guardian set, `k`, `n` | 3, 4, 13 | Quorum honesty |
| 10 | Key-ceremony checkpoints | 3, 4 | Ceremony-before-opening ordering (`ER-22`) |
| 11 | Guardian absence/substitution records | 3 | Governance transparency |
| 12 | Accepted encrypted ballots | 1, 2, 6, 7, 11, 14 | The record's bulk |
| 13 | Confirmation codes | 7, 11 | Voter lookup (`VC-*`) |
| 14 | Spoiled ballots with openings | 8 | The challenge guarantee |
| 15 | Board sequence + canonical ordering | 11, 12 | Determinism of aggregation |
| 16 | Closure checkpoint | 12, 14 | Fixing the eligible set |
| 17 | Exclusion records | 12, 14 | `EX-01`…`EX-07` |
| 18 | Aggregate ciphertexts | 14, 15 | — |
| 19 | Decryption shares + proofs | 13, 15 | — |
| 20 | Contributing guardians + quorum | 13, 15 | No compensated path (`ADR-100`) |
| 21 | Decrypted totals | 15 | The announced result |
| 22 | Count reconciliation | 12 | `ER-05` |
| 23 | Board entries | 9, 11, 12, 16 | The board read whole |
| 24 | Signed checkpoint chain | 3, 9, 10, 16 | Append-only evidence |
| 25 | Mirror co-signatures | 10 | Split-view detection |
| 26 | Board and checkpoint signing keys | 3, 9, 10 | Key-rotation visibility |
| 27 | Inclusion/consistency proof material | 9, 10 | Offline proof recomputation |
| 28 | Aggregate rejection counts | **none** | §3.1 — process transparency |
| 29 | Published failure notices | **none** | §3.1 — incident honesty |
| 30 | Independent verifier reports | **none** | §3.1 — `IV-10`, `BM-28` |
| 31 | "What you cannot check" statement | **none** | §3.1 — `ER-06`, `ER-18` |
| 32 | Record manifest + its digest | 1, 2, 16 | Record-as-single-object |
| 33 | Sealed batch commitments | 17, 18, 19 | The only pre-closure per-window publication |
| 34 | Sealed batch openings | 18, 19 | Includes the cover-leaf values without which no root recomputes |
| 35 | Batch reconciliation record | 19, 20, 21 | Occupancy by class, totals, mappings, per-batch results |
| 36 | Capacity plan as executed | 20, 21 | The finite bound, published in advance and checkable afterwards |
| 37 | Capacity incident records | 21 | Proof that no exhaustion was resolved silently |

---

## 3. Gap analysis

### 3.1 Artefacts consumed by no check — justified, not dropped

Four artefacts serve no cryptographic check. Each is retained with a stated
purpose, and none is load-bearing for a verification result.

| # | Artefact | Why it stays | If it were dropped |
| - | -------- | ------------ | ------------------ |
| 28 | Aggregate rejection counts | Lets an observer see whether the process was under stress; the difference between a quiet election and a suppressed one is invisible without it | Process failures become undetectable from outside |
| 29 | Published failure notices | An election with no incidents and an election that hid its incidents produce identical records without these (`PA-08`, `BL-*`) | Silent publication failure becomes indistinguishable from success |
| 30 | Independent verifier reports | `BM-28` makes independent verification an activation gate; the record must show whether it happened | The gate becomes unauditable |
| 31 | "What you cannot check" statement | `ER-06`, `ER-18`, `IV-11` — the record would otherwise misrepresent itself by omission | The record's honesty depends on a document a reader may never see |

| ID       | Rule                                                                                                          |
| -------- | ----------------------------------------------------------------------------------------------------------------- |
| `EC-06`  | **These four are mandatory despite serving no check.** They are the artefacts that make the record honest rather than merely verifiable, and a record missing any of them is incomplete under `ER-01` |
| `EC-07`  | **No verification result may depend on them.** A verifier reads them, may report on their presence, and never derives `VERIFIED` or `TALLY_MISMATCH` from their content |

### 3.2 Checks with a missing artefact

```text
NONE.

All twenty-one checks in PACK-16C-INDEPENDENT-VERIFIER-REQUIREMENTS.md §1
are served entirely by the mandatory 37 artefacts.
```

| ID       | Rule                                                                                                          |
| -------- | ----------------------------------------------------------------------------------------------------------------- |
| `EC-08`  | **This is a specification-stage claim about the specification, not a demonstration.** It states that the two documents are consistent as written. Whether a real verifier can execute all sixteen against a real record is demonstrated in PACK-16D and confirmed by an independent verifier under `BM-28` — not here |

### 3.3 Checks that no artefact can ever serve

Recorded so that no future round mistakes them for a gap to be filled.

| Question | Why no artefact serves it | Where it is stated |
| -------- | ------------------------- | ------------------ |
| Did each ballot come from a distinct entitled person? | The link is deliberately absent; publishing it would defeat unlinkability | `VP-17`, `ER-*` §4.1, `IV-*` §5 |
| How many ballots existed at time *t* before closure? | The pre-closure record is a sequence of constant-size commitments; the answer is not in it, deliberately | `TC-29`, `EC-14` |
| Which capability produced which artefact? | Publishing it would be the person-to-ballot link; the per-capability bound is checked in Auditor-restricted evidence whose construction is `OD-P16C-19` | `TC-83`, `IV-19`, `IV-20` |
| Did the voter's device encrypt their intent? | Only the challenge tests this, per ballot, probabilistically | `CH-25`, `T-P16A-33` |
| Was anyone coerced? | Outside what a record of ciphertexts can show | `CB-*`, `RE-14` |
| Was anyone prevented from voting? | Un-submitted ballots leave no trace | `ER-*` §4.4 |
| Were key shares handled correctly after the ceremony? | The record shows the public transcript, not custody | `ER-*` §4.5 |
| Are the parameters appropriate? | The record publishes them; it does not certify them | `VO-08`, `SB-06` |

| ID       | Rule                                                                                                          |
| -------- | ----------------------------------------------------------------------------------------------------------------- |
| `EC-09`  | **Adding an artefact to close row 1 of this table is prohibited.** Any artefact that would make ballot stuffing checkable from the record alone would, by construction, create a person-to-ballot link. The limit is the design, not an omission (`CC-04`, `ER-07`) |
| `EC-10`  | **Rows 2–6 may be narrowed by future work but not by publishing more of this record.** They belong to the challenge take-up problem, governance, custody attestation and external cryptographic review respectively |
| `EC-15`  | **Row 7 must never be closed.** Publishing enough to answer "how many ballots existed at time *t*" before closure would reintroduce the exact defect this correction removed (`TC-21`) |

---

## 4. Counts

```text
Mandatory artefacts                                     37
Artefacts consumed by at least one check                33
Artefacts retained for honesty, serving no check         4
Verifier checks                                         21
Checks fully served by mandatory artefacts              21
Checks with a missing artefact                           0
Checks performable only after closure                    5   17 … 21
Questions no artefact can ever serve                     8
```

| ID       | Rule                                                                                                          |
| -------- | ----------------------------------------------------------------------------------------------------------------- |
| `EC-11`  | **These counts are recomputed whenever either source document changes**, and a divergence between this matrix and either source is a defect in this matrix |
| `EC-12`  | **37 = 33 + 4 and 21 = 21 + 0 are the two arithmetic identities this document asserts.** They are checkable by reading §1 and §2, and are not asserted anywhere else in the pack |

---

## 5. What this document does not decide

```text
Concrete file layout of each artefact       → PACK-16D, OD-P16C-04
Whether a real verifier executes all 21     → PACK-16D, and BM-28
Privacy-preserving per-capability proof      → OD-P16C-19, PACK-16D, PACK-17
Commitment and opening formats               → OD-P16C-14, OD-P16C-16
Retention of the archived record             → ER-23, GOVERNANCE
Verification-report governance                → OD-P16C-09
```

**SPECIFIED. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY. NOT LEGALLY
ACTIVATED.**
