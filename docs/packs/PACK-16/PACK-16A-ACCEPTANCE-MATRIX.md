# PACK-16A — Acceptance Matrix

**Round:** PACK-16A — Verifiable Voting Protocol and Ballot Model Selection. **Specification and ADR only. No code. Not implemented. Not an implementation candidate. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-099`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 0. How to read this matrix, and the status that does not exist

**There is no `PASS` column and no `PASS` status, because a specification
round cannot pass anything.** A document existing is not a criterion being
met, and the statuses below are chosen so that "we wrote it down" and "it
is true of a system" cannot be confused.

| Status                         | Meaning                                                                                                         |
| ------------------------------ | --------------------------------------------------------------------------------------------------------------- |
| **SATISFIED BY SPECIFICATION** | The requirement is fully expressed as a normative rule with an owner; nothing further is owed **at this stage** |
| **SELECTED FOR REVIEW**        | A choice was made from assessed alternatives and is submitted for architectural review                          |
| **PARTIALLY SATISFIED**        | Expressed in part; the remainder is named with an owner                                                         |
| **DEFERRED**                   | Recorded as a dependency owned by a named later stage                                                           |
| **OPEN**                       | A decision this round could not take; carried in `PACK-16A-OPEN-DECISIONS.md`                                   |
| **BLOCKED**                    | Cannot proceed until an external condition — usually legal — is met                                             |
| **NOT APPLICABLE**             | Does not arise in the selected profile                                                                          |

Columns: **Requirement ID · Requirement · Baseline source · External source
· Decision document · Section · Decision · Evidence · Status · Residual
risk · Owning next stage.**

Abbreviations in the _Decision document_ column: `SCOPE`, `CMP`
(comparison), `EVD` (evidence matrix), `TM` (threat model), `BM` (ballot
model), `EPM` (election profile matrix), `RBL` (revoting and lifecycle),
`CRB` (coercion and receipt boundary), `BB` (bulletin board), `TCR`
(trustee and ceremony), `RSM` (role separation), `GLB` (German legal
boundary), `PDF` (privacy data flows), `FAM` (failure and abort), `AXR`
(accessibility), `RCS` (reason codes), `FIR` (FIR coverage), `CAN` (canon
assessment), `ODM` (open decisions).

**Total criteria: 96. Criteria met by a running system: 0.**

---

## 1. Inherited invariants

| ID            | Requirement                                       | Baseline source      | External source           | Doc       | §        | Decision                                                    | Evidence                              | Status                         | Residual                                    | Owner      |
| ------------- | ------------------------------------------------- | -------------------- | ------------------------- | --------- | -------- | ----------------------------------------------------------- | ------------------------------------- | ------------------------------ | ------------------------------------------- | ---------- |
| `AC-P16A-001` | No identity in a ballot                           | ADR-093; PACK-15 §3  | `[E-06]`                  | BM        | 3.2      | Prohibited-content list is normative and derivability-based | Prohibited-key scan design            | **SATISFIED BY SPECIFICATION** | Opaque re-derivation is not name-detectable | PACK-16D   |
| `AC-P16A-002` | Credential ID never becomes a ballot ID           | PACK-15 §11          | —                         | BM        | 3.3      | `BM-01`, `BM-02`                                            | Structural test design                | **SATISFIED BY SPECIFICATION** | —                                           | PACK-16D   |
| `AC-P16A-003` | Continuation reference never becomes a ballot ID  | PACK-15 §12          | —                         | BM        | 3.3      | `BM-01`; `CC-03`                                            | Same                                  | **SATISFIED BY SPECIFICATION** | A future idempotency need will re-ask       | PACK-16D   |
| `AC-P16A-004` | No person-to-ballot link exists in any store      | PACK-15 §3           | —                         | BM, PDF   | 3.3, all | `BM-04`; every flow's prohibited-evidence row               | Store inventory design                | **PARTIALLY SATISFIED**        | Timing correlation remains                  | PACK-16C   |
| `AC-P16A-005` | No identity recovery by correlation               | ADR-093              | `[E-27]`                  | TM        | 2        | Ten correlation threats with controls                       | Threat entries                        | **PARTIALLY SATISFIED**        | Network metadata unsolved                   | PACK-17    |
| `AC-P16A-006` | No reusable voting session                        | ADR-096; PACK-15 §12 | —                         | SCOPE     | 3.2      | `CC-07`                                                     | —                                     | **SATISFIED BY SPECIFICATION** | —                                           | PACK-16C   |
| `AC-P16A-007` | No intermediate tally, without exception          | ADR-094              | `[E-56]` Std 24           | BM        | 6.1      | `NIT-01`…`NIT-07`; `BM-21`                                  | No pre-closure decryption path exists | **SATISFIED BY SPECIFICATION** | —                                           | PACK-16C   |
| `AC-P16A-008` | No partial outcome disclosure                     | ADR-094              | —                         | BM, BB    | 6, 3.1   | Ballot entries withheld pre-closure                         | Publication model                     | **SATISFIED BY SPECIFICATION** | Reduces pre-closure scrutiny (`RR-11`)      | accepted   |
| `AC-P16A-009` | No turnout disclosure before closure              | `IT-11`              | —                         | BB, PDF   | 4, 3     | `BB-27`; `CC-10`; `DF-03` metrics rule                      | —                                     | **SATISFIED BY SPECIFICATION** | —                                           | PACK-16C   |
| `AC-P16A-010` | No single-admin decryption                        | PACK-15 §18          | `[E-04]`                  | TCR       | 2, 4     | `KC-01`, `KC-02`; `BM-22`                                   | Threshold construction                | **SATISFIED BY SPECIFICATION** | Quorum collusion undetectable               | PACK-16B   |
| `AC-P16A-011` | No silent ballot replacement                      | canon 15.3           | `[E-15]`                  | RBL       | 3.3      | Prohibited-transition list; `BM-05`                         | Board append-only                     | **SATISFIED BY SPECIFICATION** | —                                           | PACK-16C   |
| `AC-P16A-012` | No silent ballot deletion                         | —                    | `[E-15]`                  | RBL, BB   | 3.3, 2   | `BB-01`; mirrors                                            | Checkpoint chain                      | **SATISFIED BY SPECIFICATION** | Detection needs a checker                   | PACK-16C   |
| `AC-P16A-013` | No unexplained ballot exclusion                   | —                    | —                         | RBL       | 4        | `EX-01`…`EX-07`; closed ground list                         | Published exclusion                   | **SATISFIED BY SPECIFICATION** | —                                           | PACK-16C   |
| `AC-P16A-014` | No receipt reveals choice                         | canon 15.4           | `[E-05]`, `[E-56]` Std 23 | BM, CRB   | 3.3, 3   | `BM-03`                                                     | Code derivation                       | **SATISFIED BY SPECIFICATION** | Proves participation                        | PACK-16C   |
| `AC-P16A-015` | No third-party analytics, no fingerprinting       | ADR-096              | —                         | SCOPE     | 4        | Inherited unchanged; extended to the verification origin    | CSP design                            | **SATISFIED BY SPECIFICATION** | Extensions outside control                  | FRONT-PACK |
| `AC-P16A-016` | No ballot content in dispute records              | ADR-098              | —                         | SCOPE, BM | 7, 9.1   | No operation exists; consent creates none                   | Dispute-link check                    | **SATISFIED BY SPECIFICATION** | The request will be made                    | GOVERNANCE |
| `AC-P16A-017` | No individual correction through identity linkage | ADR-098              | —                         | BM, RSM   | 9.1, 4   | Prohibited as an act, with no decider                       | —                                     | **SATISFIED BY SPECIFICATION** | —                                           | GOVERNANCE |
| `AC-P16A-018` | Append-only verifiable election evidence          | —                    | `[E-15]`, `[E-45]`        | BB        | 2        | `BB-01`…`BB-07`                                             | Checkpoint chain                      | **SATISFIED BY SPECIFICATION** | Board is unbuilt (`RR-10`)                  | PACK-16C   |

## 2. Continuation-capability boundary

| ID            | Requirement                                                     | Baseline source    | External source | Doc        | §      | Decision              | Evidence            | Status                         | Residual                    | Owner                |
| ------------- | --------------------------------------------------------------- | ------------------ | --------------- | ---------- | ------ | --------------------- | ------------------- | ------------------------------ | --------------------------- | -------------------- |
| `AC-P16A-019` | Consumption is exactly-once and atomic                          | PACK-15 §12, §13.1 | —               | SCOPE      | 3.2    | `CC-01`               | Replay store        | **SATISFIED BY SPECIFICATION** | —                           | PACK-16D             |
| `AC-P16A-020` | Consumption produces no record beside a ballot                  | PACK-15 §3         | —               | SCOPE      | 3.2    | `CC-04`, `CC-05`      | Store inventory     | **SATISFIED BY SPECIFICATION** | —                           | PACK-16D             |
| `AC-P16A-021` | No board artifact derives from the continuation reference       | PACK-15 §12        | —               | SCOPE      | 3.2    | `CC-03`               | Derivability test   | **SATISFIED BY SPECIFICATION** | —                           | PACK-16D             |
| `AC-P16A-022` | Consumption timestamps are coarsened                            | PACK-15 §19.2      | —               | SCOPE, PDF | 3.2, 3 | `CC-06`               | Log field inventory | **SATISFIED BY SPECIFICATION** | —                           | PACK-16C             |
| `AC-P16A-023` | A failed cast after consumption does not restore the capability | PACK-15 §13.2      | —               | SCOPE, FAM | 3.2, 3 | `CC-08`; `FM-P16A-07` | Governed remedy     | **SATISFIED BY SPECIFICATION** | **Real participation loss** | accepted; GOVERNANCE |
| `AC-P16A-024` | Consumption is refused on manifest/parameter/checkpoint failure | —                  | `[E-33]`        | SCOPE      | 3.2    | `CC-09`               | Validation record   | **SATISFIED BY SPECIFICATION** | —                           | PACK-16C             |

## 3. Identity / credential / ballot separation

| ID            | Requirement                                                 | Baseline source       | External source    | Doc      | §        | Decision                                                  | Evidence                  | Status                         | Residual                        | Owner      |
| ------------- | ----------------------------------------------------------- | --------------------- | ------------------ | -------- | -------- | --------------------------------------------------------- | ------------------------- | ------------------------------ | ------------------------------- | ---------- |
| `AC-P16A-025` | The selected family requires no identity on the voting side | —                     | `[E-06]`           | CMP, BM  | 3.1, 9   | ElectionGuard's declared scope limit is the interface     | Compatibility check table | **SELECTED FOR REVIEW**        | —                               | review     |
| `AC-P16A-026` | No party holds both-side references                         | PACK-15 §3            | `[E-06]`, `[E-13]` | CMP      | 2.4      | Filter `F3`; Belenios and IVXV fail it                    | Filter table              | **SATISFIED BY SPECIFICATION** | —                               | PACK-16D   |
| `AC-P16A-027` | No per-participant persistent voting-side identifier        | PACK-15 §3            | `[E-13]`, `[E-24]` | CMP, RBL | 2.4, 2.2 | Filter `F1`; and the no-revoting decision follows from it | Revoting analysis         | **SATISFIED BY SPECIFICATION** | —                               | PACK-16D   |
| `AC-P16A-028` | `FIR-INV-002` is not closed by this round                   | PACK-15 §26; register | —                  | FIR      | 2.1      | Explicitly not closed                                     | FIR matrix                | **PARTIALLY SATISFIED**        | Second half specified, unproven | PACK-16C/D |

## 4. Protocol candidates

| ID            | Requirement                                                                    | Baseline source | External source              | Doc      | §       | Decision                                                                                       | Evidence           | Status                         | Residual                                             | Owner        |
| ------------- | ------------------------------------------------------------------------------ | --------------- | ---------------------------- | -------- | ------- | ---------------------------------------------------------------------------------------------- | ------------------ | ------------------------------ | ---------------------------------------------------- | ------------ |
| `AC-P16A-029` | ElectionGuard assessed against primary sources                                 | —               | `[E-01]`…`[E-10a]`           | CMP      | 3.1     | **SUITABLE WITH A FORMAL EPD² PROFILE**                                                        | Evidence matrix §1 | **SELECTED FOR REVIEW**        | No production-grade 2.1 implementation               | review       |
| `AC-P16A-030` | Belenios assessed                                                              | —               | `[E-10]`…`[E-16a]`           | CMP      | 3.2     | **SUITABLE ONLY AS REFERENCE**                                                                 | Evidence matrix §2 | **SATISFIED BY SPECIFICATION** | —                                                    | —            |
| `AC-P16A-031` | Helios assessed                                                                | —               | `[E-17]`…`[E-22]`            | CMP      | 3.3     | **NOT SUITABLE**                                                                               | Evidence matrix §3 | **SATISFIED BY SPECIFICATION** | —                                                    | —            |
| `AC-P16A-032` | Estonian IVXV assessed                                                         | —               | `[E-23]`…`[E-29]`, `[E-40]`  | CMP      | 3.4     | **NOT SUITABLE**                                                                               | Evidence matrix §4 | **SATISFIED BY SPECIFICATION** | —                                                    | —            |
| `AC-P16A-033` | A mature verifiable mixnet assessed                                            | —               | `[E-30]`…`[E-33]`            | CMP      | 3.5     | **SUITABLE ONLY AS REFERENCE**; component candidate for a deferred profile                     | Evidence matrix §5 | **DEFERRED**                   | —                                                    | future round |
| `AC-P16A-034` | A coercion-resistant / revoting protocol assessed                              | —               | `[E-34]`…`[E-44]`            | CMP      | 3.6–3.9 | JCJ/Civitas and VoteAgain **NOT SUITABLE**; Selene and BeleniosRF **REQUIRE FURTHER RESEARCH** | Evidence matrix §6 | **SATISFIED BY SPECIFICATION** | —                                                    | `OD-P16A-10` |
| `AC-P16A-035` | Security assumptions and known limitations recorded per candidate              | —               | all                          | CMP, EVD | 3, all  | Per-candidate narrative plus the evidence matrix                                               | Both documents     | **SATISFIED BY SPECIFICATION** | —                                                    | —            |
| `AC-P16A-036` | No new cryptographic voting protocol is invented                               | —               | —                            | CMP      | 0       | Prohibited; a published specification is adopted as base                                       | `ADR-099`          | **SATISFIED BY SPECIFICATION** | —                                                    | —            |
| `AC-P16A-037` | No incompatible protocol parts are combined without composition analysis       | —               | `[E-33]`                     | CMP      | 0       | Prohibited; the profile adds surrounding requirements, not cryptographic parts                 | `ADR-099`          | **SATISFIED BY SPECIFICATION** | Composition of profile + board is unproven (`RR-09`) | `OD-P16A-06` |
| `AC-P16A-038` | Selection is not made on convenience, popularity, openness or governmental use | —               | —                            | CMP      | 0       | Four prohibited bases named                                                                    | —                  | **SATISFIED BY SPECIFICATION** | —                                                    | —            |
| `AC-P16A-039` | The chosen implementation must be shown to use **strong Fiat–Shamir**          | —               | `[E-19]`, `[E-33]`           | BM, TCR  | 8.2, 6  | `KC-23`; verified by test, not assumed                                                         | Test design        | **DEFERRED**                   | The field's most repeated production bug             | **PACK-16D** |
| `AC-P16A-040` | Every ballot carries a proof of knowledge of its plaintext                     | —               | `[E-19]`, `[E-27]`, `[E-32]` | BM       | 5       | `BM-14`                                                                                        | Ballot format      | **SATISFIED BY SPECIFICATION** | —                                                    | PACK-16C     |

## 5. Ballot types

| ID            | Requirement                                                   | Baseline source | External source    | Doc | §        | Decision                                                                 | Evidence                              | Status                         | Residual                             | Owner        |
| ------------- | ------------------------------------------------------------- | --------------- | ------------------ | --- | -------- | ------------------------------------------------------------------------ | ------------------------------------- | ------------------------------ | ------------------------------------ | ------------ |
| `AC-P16A-041` | Yes/no, single-choice, n-of-m, approval, multi-seat supported | canon 15.1      | `[E-08]`           | EPM | 2, 3     | Supported initially in `EPD2-HOM-1`                                      | Per-type analysis                     | **SATISFIED BY SPECIFICATION** | —                                    | PACK-16C     |
| `AC-P16A-042` | Ranked, STV, Condorcet, Majority Judgment unsupported         | —               | `[E-08]`, `[E-12]` | EPM | 2, 3     | Not supported; require the deferred profile                              | Per-type analysis                     | **SATISFIED BY SPECIFICATION** | Bodies using them must change method | GOVERNANCE   |
| `AC-P16A-043` | Write-ins prohibited pending research                         | —               | `[E-08]`           | EPM | 2        | Prohibited                                                               | —                                     | **BLOCKED**                    | —                                    | future round |
| `AC-P16A-044` | No individual ballot plaintext in the selected profile        | —               | `[E-08]`           | EPM | 3        | Homomorphic only                                                         | Column "plaintext individual ballots" | **SATISFIED BY SPECIFICATION** | —                                    | —            |
| `AC-P16A-045` | Multi-seat counting rule published in advance                 | —               | —                  | EPM | 4        | `MS-01`…`MS-05`                                                          | Manifest                              | **SATISFIED BY SPECIFICATION** | —                                    | PACK-16C     |
| `AC-P16A-046` | No hidden universal hybrid profile                            | —               | —                  | BM  | 2.1      | One profile per context; no inference; refusal not defaulting            | Configuration rule                    | **SATISFIED BY SPECIFICATION** | —                                    | PACK-16D     |
| `AC-P16A-047` | The mixnet profile is defined but not activated               | —               | `[E-12]`, `[E-33]` | BM  | 2.2, 2.3 | `EPD2-MIX-1` prohibited pending research, with `MX-01`…`MX-06` fixed now | —                                     | **BLOCKED**                    | —                                    | `OD-P16A-02` |

## 6. Verifiability properties

| ID            | Requirement               | Baseline source | External source           | Doc     | §    | Decision                                                            | Evidence                         | Status                         | Residual                                                | Owner                |
| ------------- | ------------------------- | --------------- | ------------------------- | ------- | ---- | ------------------------------------------------------------------- | -------------------------------- | ------------------------------ | ------------------------------------------------------- | -------------------- |
| `AC-P16A-048` | Cast as intended          | —               | `[E-05]`, `[E-56]` Std 15 | BM      | 4    | Challenge/spoil, required and non-disablable                        | `BM-07`…`BM-13`                  | **PARTIALLY SATISFIED**        | Probabilistic; depends on take-up                       | PACK-16C             |
| `AC-P16A-049` | Recorded as cast          | —               | `[E-56]` Std 15           | BM, BB  | 5, 4 | Confirmation code + board presence check                            | `BM-17`…`BM-19`; `BB-22`…`BB-26` | **PARTIALLY SATISFIED**        | Take-up 9.9 % at best                                   | PACK-16C             |
| `AC-P16A-050` | Tallied as recorded       | —               | `[E-56]` Std 17           | BM      | 6    | Aggregate, shares and proofs published                              | `BM-20`…`BM-25`                  | **SATISFIED BY SPECIFICATION** | Needs a verifier                                        | PACK-16C             |
| `AC-P16A-051` | Individual verifiability  | —               | `[E-29]`, `[E-40]`        | BB      | 4    | Presence query with a checkpoint                                    | `BB-22`…`BB-27`                  | **PARTIALLY SATISFIED**        | Empirically low take-up                                 | PACK-16C             |
| `AC-P16A-052` | Universal verifiability   | —               | `[E-45]` Art. 5           | BB      | 6    | Independent verifier from the published record                      | `BB-33`…`BB-37`                  | **PARTIALLY SATISFIED**        | No verifier exists yet                                  | PACK-16C             |
| `AC-P16A-053` | Software independence     | —               | —                         | BM      | 7    | Objective specified, not demonstrated                               | `BM-26`…`BM-29`                  | **PARTIALLY SATISFIED**        | Not demonstrated                                        | PACK-16C/D           |
| `AC-P16A-054` | Eligibility verifiability | —               | `[E-06]`, `[E-56]` Std 18 | GLB     | 6    | Only the aggregate count check; **weaker than Std 18, and said so** | —                                | **PARTIALLY SATISFIED**        | Structural — ballot-level would need the forbidden link | accepted             |
| `AC-P16A-055` | Cryptographic agility     | —               | `[E-52]`                  | BM, TCR | 8, 6 | `BM-30`…`BM-35`; `KC-21`…`KC-27`                                    | Parameter identifier             | **SATISFIED BY SPECIFICATION** | Parameters unchosen                                     | PACK-16B             |
| `AC-P16A-056` | Fail-closed behaviour     | PACK-15 §27     | —                         | FAM     | 2    | 25 conditions with outcomes and deciders                            | `FM-P16A-01`…`25`                | **SATISFIED BY SPECIFICATION** | —                                                       | PACK-16C             |
| `AC-P16A-057` | Independent verification  | —               | `[E-45]` Art. 10          | BM, BB  | 7, 6 | `BM-28` as a governance gate item                                   | Gate item 9                      | **DEFERRED**                   | —                                                       | GOVERNANCE, PACK-16C |

## 7. Receipt, coercion and revoting

| ID            | Requirement                                                         | Baseline source | External source               | Doc | §        | Decision                                                                    | Evidence                  | Status                         | Residual                                            | Owner        |
| ------------- | ------------------------------------------------------------------- | --------------- | ----------------------------- | --- | -------- | --------------------------------------------------------------------------- | ------------------------- | ------------------------------ | --------------------------------------------------- | ------------ |
| `AC-P16A-058` | Receipt-freeness stated as a bounded claim only                     | —               | `[E-05]`, `[E-14]`, `[E-42]`  | CRB | 3, 7     | Bounded; the in-person qualifier does not transfer                          | Permitted-claims registry | **SATISFIED BY SPECIFICATION** | Participation is provable                           | accepted     |
| `AC-P16A-059` | Coercion-resistance limits described honestly                       | —               | `[E-46]`, `[E-34]`, `[E-37]`  | CRB | 1, 2, 5  | Six layers; two threats recorded **unmitigated**                            | `T-P16A-26`, `T-P16A-30`  | **SATISFIED BY SPECIFICATION** | Unmitigated by design                               | GOVERNANCE   |
| `AC-P16A-060` | The revoting decision is explicit                                   | —               | `[E-15]`, `[E-28a]`, `[E-44]` | RBL | 1, 2     | **No revoting**, with the required proof attempted and its failure recorded | §2.2, §2.3                | **SELECTED FOR REVIEW**        | Coercion mitigation forgone                         | review       |
| `AC-P16A-061` | If supersession were selected, five obligations would be discharged | —               | —                             | RBL | 2.2, 3.4 | Not selected; `SU-01`…`SU-05` bind any future profile                       | —                         | **NOT APPLICABLE**             | —                                                   | `OD-P16A-01` |
| `AC-P16A-062` | Challenge/spoil cannot be disabled                                  | `FIR-INV-006`   | `[E-05]`                      | BM  | 4        | Required in every `EPD2-HOM-1` context                                      | `BM-11`, `BM-12`          | **SATISFIED BY SPECIFICATION** | —                                                   | PACK-16C     |
| `AC-P16A-063` | Verification cannot become a coercion instrument                    | —               | `[E-56]` Std 23               | CRB | 6        | Presence only; separate origin; no post-cast choice disclosure              | `BB-14`                   | **PARTIALLY SATISFIED**        | A coercer present at casting already has the choice | accepted     |

## 8. Ballot lifecycle and bulletin board

| ID            | Requirement                                                                                  | Baseline source | External source              | Doc | §        | Decision                                                                               | Evidence            | Status                         | Residual                              | Owner      |
| ------------- | -------------------------------------------------------------------------------------------- | --------------- | ---------------------------- | --- | -------- | -------------------------------------------------------------------------------------- | ------------------- | ------------------------------ | ------------------------------------- | ---------- |
| `AC-P16A-064` | Ballot lifecycle formalised with all required states                                         | canon 15.3      | —                            | RBL | 3.1, 3.2 | 14 states; per-transition actor, proof, evidence, failure code, reversibility, privacy | Transition table    | **SATISFIED BY SPECIFICATION** | —                                     | PACK-16C   |
| `AC-P16A-065` | Silent replacement, deletion and exclusion prohibited                                        | —               | `[E-15]`                     | RBL | 3.3      | Prohibited-transition list                                                             | —                   | **SATISFIED BY SPECIFICATION** | —                                     | PACK-16C   |
| `AC-P16A-066` | Exclusion carries a formalised ground and privacy-safe reason                                | —               | —                            | RBL | 4        | `EX-01`…`EX-07`; closed ground list                                                    | Published exclusion | **SATISFIED BY SPECIFICATION** | —                                     | PACK-16C   |
| `AC-P16A-067` | Bulletin-board requirements defined as a trust boundary                                      | —               | `[E-07]`, `[E-15]`, `[E-32]` | BB  | 1, 2     | 37 requirements                                                                        | `BB-01`…`BB-37`     | **SATISFIED BY SPECIFICATION** | Entirely unbuilt (`RR-10`)            | PACK-16C   |
| `AC-P16A-068` | Equivocation, split view, rollback, late insertion, deletion, mirror inconsistency addressed | —               | `[E-15]`                     | BB  | 5        | Signed chained checkpoints + independent mirrors                                       | `BB-28`…`BB-32`     | **SATISFIED BY SPECIFICATION** | Mirror independence is organisational | GOVERNANCE |
| `AC-P16A-069` | Any restriction on publicity is justified                                                    | —               | `[E-41]`                     | BB  | 3.1      | Pre-closure ballot entries withheld — required by `ADR-094`, not chosen                | —                   | **SATISFIED BY SPECIFICATION** | `RR-11`                               | accepted   |

## 9. Threshold trust

| ID            | Requirement                                             | Baseline source | External source | Doc      | §      | Decision                           | Evidence               | Status                         | Residual                                  | Owner      |
| ------------- | ------------------------------------------------------- | --------------- | --------------- | -------- | ------ | ---------------------------------- | ---------------------- | ------------------------------ | ----------------------------------------- | ---------- |
| `AC-P16A-070` | Threshold trust is mandatory                            | PACK-15 §18     | `[E-04]`        | TCR      | 2, 3   | `KC-01`; `TP-01`…`TP-07`           | —                      | **SATISFIED BY SPECIFICATION** | —                                         | PACK-16B   |
| `AC-P16A-071` | No single organisation may supply a quorum              | —               | `[E-45]` Art. 8 | TCR      | 3.1    | `TP-02`                            | Published trustee list | **SATISFIED BY SPECIFICATION** | Undetectable if violated in fact          | GOVERNANCE |
| `AC-P16A-072` | No escrow, no master key, no recovery outside a quorum  | —               | —               | TCR, FAM | 4.2, 4 | `KC-15`; six prohibited recoveries | —                      | **SATISFIED BY SPECIFICATION** | **Quorum loss loses the election**        | accepted   |
| `AC-P16A-073` | Trustee acts possible only after closure are enumerated | ADR-094         | —               | TCR      | 5.1    | Four acts named                    | —                      | **SATISFIED BY SPECIFICATION** | —                                         | PACK-16B   |
| `AC-P16A-074` | Parameter provenance published and reproducible         | —               | `[E-33]`        | BM, TCR  | 8, 2   | `BM-33`; `KC-19`                   | Provenance document    | **SATISFIED BY SPECIFICATION** | Provenance nobody reproduces is unchecked | PACK-16B   |

## 10. Correlation, disclosure and disputes

| ID            | Requirement                                                                | Baseline source              | External source | Doc     | §      | Decision                                                        | Evidence             | Status                         | Residual                                | Owner       |
| ------------- | -------------------------------------------------------------------------- | ---------------------------- | --------------- | ------- | ------ | --------------------------------------------------------------- | -------------------- | ------------------------------ | --------------------------------------- | ----------- |
| `AC-P16A-075` | Timing correlation treated separately and not declared solved              | PACK-15 §19.5                | —               | PDF, TM | 13, 2  | Coarsening, minting delay, batching, delayed publication        | `T-P16A-04`          | **PARTIALLY SATISFIED**        | **Reduced and bounded, not eliminated** | PACK-16C    |
| `AC-P16A-076` | Order-of-arrival correlation addressed                                     | —                            | —               | BM, BB  | 3.3, 2 | `BM-06`; `BB-11`                                                | —                    | **PARTIALLY SATISFIED**        | A single-ballot batch reveals order     | PACK-16C    |
| `AC-P16A-077` | Network and infrastructure correlation named, not claimed solved           | PACK-15 `T-P15-14`           | —               | PDF, TM | 13, 9  | Owned by PACK-17                                                | —                    | **DEFERRED**                   | Unsolved at the application layer       | **PACK-17** |
| `AC-P16A-078` | Verification-timing correlation addressed                                  | —                            | —               | BB, PDF | 4, 7   | Unauthenticated unlogged reads; full-board download             | `BB-09`, `BB-24`     | **PARTIALLY SATISFIED**        | A mirror can observe fetches            | PACK-16C    |
| `AC-P16A-079` | Small-group disclosure extended to results without changing PACK-15 values | PACK-15 §19.4; `FIR-INV-011` | —               | EPM     | 6      | `SD-01`…`SD-09`; `disclosure_min_cell` unchanged                | Suppression metadata | **SATISFIED BY SPECIFICATION** | Small bodies remain self-revealing      | GOVERNANCE  |
| `AC-P16A-080` | Bodies below three cannot vote secretly and are refused                    | —                            | `[E-51]`        | EPM     | 6.2    | Configuration refusal                                           | —                    | **SATISFIED BY SPECIFICATION** | —                                       | PACK-16D    |
| `AC-P16A-081` | The dispute model creates no person-to-ballot link                         | ADR-098                      | —               | BM, TM  | 9.1, 7 | Six link routes checked; the trustee route prohibited as an act | Dispute-link check   | **SATISFIED BY SPECIFICATION** | The request will be made                | GOVERNANCE  |

## 11. Roles, failure, reason codes, accessibility

| ID            | Requirement                                                      | Baseline source | External source                    | Doc | §      | Decision                                                      | Evidence              | Status                         | Residual                                              | Owner        |
| ------------- | ---------------------------------------------------------------- | --------------- | ---------------------------------- | --- | ------ | ------------------------------------------------------------- | --------------------- | ------------------------------ | ----------------------------------------------------- | ------------ |
| `AC-P16A-082` | Sixteen roles with a separation matrix                           | `FIR-ROLE-005`  | —                                  | RSM | 1, 2   | Matrix with `✓`/`✗`/`△`                                       | —                     | **SATISFIED BY SPECIFICATION** | —                                                     | PACK-16D     |
| `AC-P16A-083` | Eleven minimum prohibitions, each with an enforcement mechanism  | —               | —                                  | RSM | 3, 3.1 | Structural or cryptographic for nine of eleven                | —                     | **SATISFIED BY SPECIFICATION** | Two are organisational                                | GOVERNANCE   |
| `AC-P16A-084` | Dangerous collusion combinations described                       | —               | `[E-45]` Art. 8                    | RSM | 5      | Ten combinations                                              | —                     | **SATISFIED BY SPECIFICATION** | Combination 1 is undetectable                         | PACK-16B     |
| `AC-P16A-085` | Fail-closed and abort model covers all named conditions          | PACK-15 §27     | —                                  | FAM | 2      | 25 entries with decider, concurrence, evidence, communication | —                     | **SATISFIED BY SPECIFICATION** | —                                                     | PACK-16C     |
| `AC-P16A-086` | Uncertifiable results are defined and cannot be re-asserted away | canon 15.6      | —                                  | FAM | 5      | Declaration, publication, non-withdrawal                      | —                     | **SATISFIED BY SPECIFICATION** | —                                                     | GOVERNANCE   |
| `AC-P16A-087` | Reason-code namespaces specified and privacy-safe                | PACK-15 §28     | —                                  | RCS | 1–9    | 11 namespaces; `RC-01`…`RC-10`; no generic error code         | —                     | **SATISFIED BY SPECIFICATION** | Not registered                                        | PACK-16C     |
| `AC-P16A-088` | Accessibility is a protocol-level requirement                    | `FIR-INV-012`   | `[E-41]`, `[E-55]`, `[E-56]` Std 1 | AXR | 1–8    | 43 requirements; conflicts named, never silently downgraded   | —                     | **SATISFIED BY SPECIFICATION** | Interface work remains                                | FRONT-PACK   |
| `AC-P16A-089` | Plain-language verification required by architecture             | —               | `[E-41]`, `[E-55]`                 | AXR | 4      | `AX-21`…`AX-27`                                               | Comprehension testing | **PARTIALLY SATISFIED**        | Whether any crypto scheme meets Rn. 109 is unresolved | `OD-P16A-10` |

## 12. Legal, canon, FIR and claims

| ID            | Requirement                                                           | Baseline source | External source             | Doc      | §      | Decision                                                                             | Evidence                             | Status                         | Residual                                    | Owner      |
| ------------- | --------------------------------------------------------------------- | --------------- | --------------------------- | -------- | ------ | ------------------------------------------------------------------------------------ | ------------------------------------ | ------------------------------ | ------------------------------------------- | ---------- |
| `AC-P16A-090` | German legal boundary separated from technical capability             | —               | `[E-41]`, `[E-49]`…`[E-56]` | GLB      | 1, 5   | Nine modes with default states                                                       | Mode table                           | **SATISFIED BY SPECIFICATION** | —                                           | LEGAL      |
| `AC-P16A-091` | Public-election activation prohibited by default                      | —               | `[E-41]`                    | GLB      | 5      | Modes F–I prohibited; configuration refusal                                          | `VOTING_CONTEXT_LEGAL_BASIS_MISSING` | **SATISFIED BY SPECIFICATION** | —                                           | GOVERNANCE |
| `AC-P16A-092` | Statutory candidate nomination prohibited                             | —               | `[E-50]`, `[E-51]`          | GLB, EPM | 4.3, 5 | Mode C prohibited for statutory use                                                  | Guidance citation                    | **BLOCKED**                    | Requires legal change to move               | LEGAL      |
| `AC-P16A-093` | A ten-item governance gate exists and cannot be delegated             | —               | `[E-45]` Art. 10            | GLB      | 8      | Ten items; four permitted outcomes; six prohibited uses                              | —                                    | **SATISFIED BY SPECIFICATION** | —                                           | GOVERNANCE |
| `AC-P16A-094` | Canon assessment performed without changing the canon                 | PACK-15 §31     | —                           | CAN      | all    | **CANON CLARIFICATION REQUIRED**; three amendment candidates recorded, none proposed | `CQ-01`…`CQ-06`; `CA-01`…`CA-03`     | **SATISFIED BY SPECIFICATION** | Amendment likely at 16B/16C                 | PACK-16B/C |
| `AC-P16A-095` | FIR coverage without false closure                                    | register        | —                           | FIR      | all    | 0 marked implemented; 0 created; 0 removed; `FIR-INV-002` explicitly not closed      | FIR matrix                           | **SATISFIED BY SPECIFICATION** | —                                           | —          |
| `AC-P16A-096` | Permitted- and prohibited-claims registries exist and are enforceable | `FIR-INV-015`   | —                           | CRB      | 7, 8   | 11 permitted with qualifications; 17 prohibited; scannable                           | Prohibited-phrase scan design        | **SATISFIED BY SPECIFICATION** | Enforcement is an implementation obligation | PACK-16D   |

---

## 13. Summary

**This summary is derived from the rows in §1–§12, not the other way
round.** It was recomputed by extracting the status cell of every
`AC-P16A-nnn` row; the arithmetic check below is the guard against the two
of them ever diverging again.

| Status                               | Count  |
| ------------------------------------ | ------ |
| SATISFIED BY SPECIFICATION           | 71     |
| PARTIALLY SATISFIED                  | 14     |
| SELECTED FOR REVIEW                  | 3      |
| DEFERRED                             | 4      |
| BLOCKED                              | 3      |
| OPEN                                 | 0      |
| NOT APPLICABLE                       | 1      |
| **Sum of status counts**             | **96** |
| **Total requirement rows**           | **96** |
| **Criteria met by a running system** | **0**  |

### 13.1 Arithmetic check

```text
sum(all status counts) == total requirement rows
71 + 14 + 3 + 4 + 3 + 0 + 1 = 96 == 96   ✓

requirement rows ................... 96
duplicate Requirement IDs ..........  0
missing Requirement IDs (1…96) .....  0
status values outside the vocabulary  0
```

**A summary that does not satisfy this check is wrong, and the rows are
what must be believed.** The counts were previously published as
62/16/4/5/4/0/1, which summed to 92 against 96 rows; that summary was an
estimate rather than a count, and **no row status was changed to reconcile
it**. The row-level statuses were independently recounted and found
correct; only the summary was replaced. `PACK-16A-HANDOVER.md` §5.1 records
the correction.

`OPEN` is zero not because nothing is unresolved but because the
unresolved items are carried as numbered entries in
`PACK-16A-OPEN-DECISIONS.md` rather than as matrix rows — twelve of them,
each with an owner and a closing round.

**SPECIFIED. ASSESSED. SELECTED FOR ARCHITECTURAL REVIEW. REQUIRES EXTERNAL
REVIEW. REQUIRES LEGAL ASSESSMENT. NOT PRODUCTION READY. NOT LEGALLY
ACTIVATED.**
