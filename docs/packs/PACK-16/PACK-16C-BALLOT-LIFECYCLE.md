# PACK-16C — Ballot Lifecycle

**Round:** PACK-16C — Casting, Receipt, Verification Client, Bulletin Board and Election Record. **Specification and ADR only. No code. No cryptographic implementation. Not implemented. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-101`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 1. The states

```text
prepared                        client-side only
encrypted                       client-side only
challenged                      the voter chose to open it
spoiled                         opened and published — ABSORBING, never counted
submitted                       sent, outcome not yet known
submission_uncertain            client lost the answer, not the ballot
cryptographically_validating    inside the pipeline
rejected                        failed a check — ABSORBING for this envelope
accepted_pending_publication    inside/after the atomic boundary
published                       committed in a sealed batch under a
                                checkpoint, then opened at closure — two
                                PHASES of one state, not two states (§2.1)
publication_disputed            accepted but not published as required
eligible_for_tally              in the set fixed by the closure checkpoint
excluded_with_public_reason     removed from the tally, publicly, with a ground
included_in_tally               counted
archived                        in the retained record
```

**Sixteen states.** `superseded_if_permitted` is retained from PACK-16A as
**defined and unreachable** — §6.

---

## 2. Relationship to the PACK-16A lifecycle

PACK-16A defined fourteen states. **None is renamed, removed or redefined.**
PACK-16C adds five and inherits the rest exactly.

| PACK-16A state                                                                                    | In PACK-16C                                                                                                                                                                                                                         |
| ------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `prepared`, `encrypted`, `challenged`, `spoiled`, `submitted`                                     | **unchanged**                                                                                                                                                                                                                       |
| `cryptographically_validated`                                                                     | **refined into** `cryptographically_validating` (in progress) → `accepted_pending_publication` (passed) or `rejected` (failed). The PACK-16A meaning — "checks have passed" — is the transition into `accepted_pending_publication` |
| `accepted`                                                                                        | **refined into** `accepted_pending_publication`, which makes explicit that acceptance and publication are distinct (`PA-*`)                                                                                                         |
| `published`, `eligible_for_tally`, `excluded_with_public_reason`, `included_in_tally`, `archived` | **unchanged**                                                                                                                                                                                                                       |
| `tallied`                                                                                         | **unchanged**, and reached from `included_in_tally` at result publication                                                                                                                                                           |
| `superseded_if_permitted`                                                                         | **unchanged and unreachable**                                                                                                                                                                                                       |
| —                                                                                                 | **new:** `submission_uncertain`, `rejected`, `publication_disputed`                                                                                                                                                                 |

| ID      | Rule                                                                                                                                                                                        |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `BL-01` | **The new states make existing failure modes nameable; they do not create new paths.** Every PACK-16A prohibited transition remains prohibited, and no new transition into the tally exists |

### 2.1 `published` has two phases — and is still one state

The corrected turnout model (`TC-*` §4) splits publication into a
**commitment** phase before closure and an **opening** phase at closure.

```text
published (committed)   the ballot's leaf is inside a published
                        commitment_root; the ballot artefact itself is
                        NOT public, and occupancy is not derivable

published (opened)      the ballot artefact and its leaf opening are
                        public, at closure
```

| ID      | Rule                                                                                                                                                                                                                                                                      |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `BL-12` | **These are phases of the single state `published`, not new lifecycle states.** The state count remains **sixteen**; nothing in PACK-16A's model is renamed or added to. The receipt distinguishes the phases (`RE-*`), and the lifecycle does not need to                |
| `BL-14` | **A local diagnostic challenge produces no lifecycle state.** The ballot never leaves `encrypted`, is discarded, and a fresh one is prepared. Only a **public evidentiary** challenge reaches `challenged` (`CH-39`, `CH-43`)                                             |
| `BL-15` | **`challenged` and `spoiled` are reachable at most once per capability in the initial profile**, because the public-challenge entitlement is spent by the first one (`CN-33`, `CN-35`)                                                                                    |
| `BL-13` | **Neither phase is skippable.** A ballot cannot be opened at closure without having been committed in a pre-closure window — that is exactly what `TC-53` rejects as a late insertion — and a committed ballot that is never opened makes the record incomplete (`TC-44`) |

---

## 3. Transitions

| From                               | To                                 | Actor                        | Precondition                                                                                                              | Proof / evidence                                         | Public?                                 | Reason code                      |
| ---------------------------------- | ---------------------------------- | ---------------------------- | ------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------- | --------------------------------------- | -------------------------------- |
| —                                  | `prepared`                         | Voter + client               | Manifest, parameters and key verified                                                                                     | none                                                     | no                                      | —                                |
| `prepared`                         | `encrypted`                        | Client                       | Randomness self-test passed                                                                                               | ciphertexts + proofs                                     | no                                      | —                                |
| `encrypted`                        | _(no state)_                       | **Voter**                    | **Local diagnostic challenge** — checked locally, discarded, never submitted                                              | none                                                     | no                                      | none — client-local (`CH-39`)    |
| `encrypted`                        | `challenged`                       | **Voter**                    | **Public evidentiary challenge**; confirmation code committed and shown (`CH-01`); public-challenge entitlement available | opening                                                  | later, yes                              | `challenge.selected`             |
| `challenged`                       | `spoiled`                          | Board                        | Leaf reserved, boundary committed, opening published at closure                                                           | ballot + opening                                         | **yes, at closure**                     | `challenge.spoiled_published`    |
| `encrypted`                        | `submitted`                        | **Voter**                    | Cast chosen; commitment preceded it                                                                                       | envelope                                                 | no                                      | `submission.sent`                |
| `submitted`                        | `submission_uncertain`             | Client                       | No response within the bound                                                                                              | retry token held                                         | no                                      | `submission.timeout`             |
| `submission_uncertain`             | `submitted`                        | Client                       | Voter-initiated status check or same-token resubmit                                                                       | idempotent outcome                                       | no                                      | —                                |
| `submitted`                        | `cryptographically_validating`     | Service                      | Envelope parsed                                                                                                           | —                                                        | no                                      | —                                |
| `cryptographically_validating`     | `rejected`                         | Service                      | Any stage 1–18 failure                                                                                                    | distinct reason code                                     | aggregate only                          | `ballot_proof.*`, `submission.*` |
| `cryptographically_validating`     | `accepted_pending_publication`     | Service                      | **All checks passed**, atomic boundary committed                                                                          | signed publication commitment                            | no, yet                                 | `acceptance.committed`           |
| `accepted_pending_publication`     | `published` **(phase: committed)** | Board                        | The ballot's leaf is inside the `commitment_root` of its named sealed batch window                                        | `sealed_batch_commitment` + privacy-safe inclusion proof | **the commitment, yes; the ballot, no** | `publication.batch_committed`    |
| `published` **(phase: committed)** | `published` **(phase: opened)**    | Board                        | Closure opening published in full                                                                                         | `sealed_batch_opening` + `batch_reconciliation_record`   | **yes**                                 | `publication.published`          |
| `accepted_pending_publication`     | `publication_disputed`             | Board / Auditor              | The named batch window passed without the leaf                                                                            | published failure notice                                 | **yes**, without a count                | `publication.deadline_missed`    |
| `publication_disputed`             | `published`                        | Board                        | Remedied within the escalation window                                                                                     | entry + explanation                                      | **yes**                                 | `publication.recovered`          |
| `publication_disputed`             | _(election-level)_                 | Election Board               | Not remedied                                                                                                              | `FM-16C-16`                                              | **yes**                                 | `publication.unrecoverable`      |
| `published`                        | `eligible_for_tally`               | Closure checkpoint           | Ballot inside the set fixed at closure (`BM-20`)                                                                          | closure checkpoint                                       | **yes**                                 | `election.closed`                |
| `eligible_for_tally`               | `excluded_with_public_reason`      | **Election Board + Auditor** | A ground from the closed list (`EX-01`)                                                                                   | published exclusion record                               | **yes**                                 | `acceptance.excluded`            |
| `eligible_for_tally`               | `included_in_tally`                | Tally                        | Aggregation over the fixed set                                                                                            | tally artefacts                                          | **yes**                                 | —                                |
| `included_in_tally`                | `tallied`                          | Tally                        | Result published with proofs                                                                                              | decryption shares + proofs                               | **yes**                                 | —                                |
| any                                | `archived`                         | Archive Custodian            | Retention policy                                                                                                          | archive checkpoint                                       | **yes**                                 | `archive.sealed`                 |

---

## 4. Prohibited transitions — normative

```text
spoiled            → anything countable          ABSORBING
challenged         → submitted as cast
rejected           → accepted, by any authority
published          → deleted
published          → modified
published          → replaced
accepted           → silently unpublished
eligible_for_tally → superseded
included_in_tally  → excluded, without a published ground and Auditor concurrence
any                → included_in_tally, other than from eligible_for_tally
archived           → modified
```

| ID      | Rule                                                                                                                                                                                                            |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `BL-02` | **No silent ballot replacement.** There is no operation that substitutes one published ballot for another (`T-P16A-11`)                                                                                         |
| `BL-03` | **No silent ballot deletion.** Removal from the board is not an operation that exists; append-only means the entry stays (`BB-01`, `T-P16A-12`)                                                                 |
| `BL-04` | **No silent ballot exclusion.** A ballot leaves the tally only through `excluded_with_public_reason`, with a published ground, a reason code, Election Board decision and Auditor concurrence (`EX-01`…`EX-07`) |
| `BL-05` | **`spoiled` is absorbing.** Nothing converts a spoiled ballot into a counted one — not an administrator, not a recovery procedure, not a governance decision (`CH-05`)                                          |
| `BL-06` | **`rejected` is absorbing for that envelope.** A rejected ballot is never later accepted; the voter submits a _new_ ballot, and the capability was never consumed                                               |
| `BL-07` | **No revoting.** There is no `superseded`, no `replaced`, no `cancelled_and_recast`. A voter casts once (`ADR-099`)                                                                                             |

---

## 5. Privacy rules per state

| State                                                               | May be public                                                     | Must not be public                                                         |
| ------------------------------------------------------------------- | ----------------------------------------------------------------- | -------------------------------------------------------------------------- |
| `prepared`, `encrypted`                                             | **nothing**                                                       | that a ballot exists at all                                                |
| `challenged`, `spoiled`                                             | ballot, opening, marking — **at closure, with the batch opening** | who challenged, when precisely, how many before closure (`CH-32`, `TC-57`) |
| `submitted`, `submission_uncertain`, `cryptographically_validating` | **nothing per ballot**                                            | the existence of an in-flight submission                                   |
| `rejected`                                                          | **aggregate counts only, delayed**                                | per-ballot rejection detail before closure (`VP-13`)                       |
| `accepted_pending_publication`                                      | **nothing per ballot before its batch**                           | the accepted count before closure (`TC-*`)                                 |
| `published` (committed)                                             | **nothing per ballot** — only the constant-size batch commitment  | occupancy, count, leaf index, any per-ballot value                         |
| `published` (opened)                                                | ballot, proofs, confirmation code, leaf index, batch              | arrival order, exact time, submitter metadata                              |
| `publication_disputed`                                              | **the dispute itself, always**                                    | which voter is affected                                                    |
| `eligible_for_tally`, `included_in_tally`                           | the set, after closure                                            | any per-ballot choice, ever                                                |
| `excluded_with_public_reason`                                       | identifier, ground, reason code, decision                         | who cast it — **which is not knowable** (`EX-07`)                          |
| `archived`                                                          | the record and its checkpoints                                    | anything the live record could not show                                    |

| ID      | Rule                                                                                                                                                                                                                                                                                                                                     |
| ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `BL-08` | **No state transition is published in real time.** Before closure the only publication is one constant-size sealed batch commitment per fixed window (`TC-04`, `BE-24`); individual state changes become public at closure. `BB-11`'s property — publication is never a per-ballot timing channel — is preserved by a stronger mechanism |
| `BL-09` | **No state anywhere holds a continuation reference beside a ballot identifier** (`CC-04`), including transient in-flight states                                                                                                                                                                                                          |

---

## 6. `superseded_if_permitted` — defined and unreachable

PACK-16A defined this state so that a future profile permitting revoting
would not invent one silently. **PACK-16C keeps it exactly as it found it.**

| ID      | Rule                                                                                                                                                                                                 |
| ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `BL-10` | **No transition into `superseded_if_permitted` exists in `EPD2-HOM-1`.** It has no predecessor state, no actor, no precondition and no reason code, and any implementation offering one is defective |
| `BL-11` | If a future profile permits supersession, `SU-01`…`SU-05` bind it, and it requires a new ADR. **PACK-16C does not enable it**                                                                        |

---

## 7. Retryability

| State                          | Retryable?               | By what means                                                   |
| ------------------------------ | ------------------------ | --------------------------------------------------------------- |
| `prepared`, `encrypted`        | **yes**                  | Revise or re-encrypt; nothing spent                             |
| `challenged` / `spoiled`       | **yes, as a new ballot** | Fresh ballot, fresh randomness, same capability (`CF-26`)       |
| `submitted`                    | **yes**                  | Same retry token, identical envelope (`CN-08`)                  |
| `submission_uncertain`         | **yes**                  | Status check first; resubmit only with the same token (`CN-26`) |
| `rejected`                     | **yes, as a new ballot** | Capability untouched                                            |
| `accepted_pending_publication` | **no**                   | The ballot is cast; the capability is spent                     |
| `publication_disputed`         | **no, for the voter**    | Election-level remedy only                                      |
| everything after               | **no**                   | —                                                               |

---

## 8. What this document does not decide

```text
State storage and its schema                → PACK-16D
Timeout values                               → PACK-16D
Batch interval and capacity                  → OD-P16C-10, GOVERNANCE
Exclusion grounds list per context            → GOVERNANCE, published with the manifest
```

**SPECIFIED. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY. NOT LEGALLY
ACTIVATED.**
