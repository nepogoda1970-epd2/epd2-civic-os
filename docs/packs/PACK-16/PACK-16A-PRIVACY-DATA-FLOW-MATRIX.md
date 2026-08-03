# PACK-16A — Privacy and Metadata Data-Flow Matrix

**Round:** PACK-16A — Verifiable Voting Protocol and Ballot Model Selection. **Specification and ADR only. No code. Not implemented. Not an implementation candidate. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-099`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

Twelve flows. For each: **data · identifier · timestamp precision · network
metadata · logs · metrics · trace context · retention · access roles ·
correlation risk · permitted evidence · prohibited evidence · redaction.**
Because thirteen columns do not fit, each flow is a block.

`granularity` means the context's `timestamp_granularity` — default 300 s,
hard lower bound 60 s, ≥ 3600 s for small electorates (PACK-15 §19.2,
§19.4). **No value in this document changes any PACK-15 value.**

---

## 0. The governing rule

> **The boundary break is at `H-06`. Every identifier, trace, correlation
> ID, request ID and idempotency key terminates there. The voting side
> begins a new chain, and nothing in this document reconnects them.**

PACK-15 ADR-090 §5 established it for the identity side. This document
extends it forward: the chain that begins at the voting boundary must also
**not** propagate from casting into the board, from the board into
verification, or from any of them into the archive in a form that survives
as a per-participation identifier.

---

## 1. `DF-01` — Voting Client (WS-03), ballot preparation

| Field                    | Value                                                                                                     |
| ------------------------ | ----------------------------------------------------------------------------------------------------------- |
| **Data**                 | Voter selections, in volatile page memory only                                                            |
| **Identifier**           | None. `BallotId` is generated here from client randomness (`BM-01`) and exists only in the client until submission |
| **Timestamp precision**  | None recorded                                                                                             |
| **Network metadata**     | TLS to the voting service only; no third-party origin, no CDN for scripts                                 |
| **Logs**                 | **None.** Errors are reason codes, never payloads                                                         |
| **Metrics**              | **None** from the client                                                                                  |
| **Trace context**        | **None.** No distributed trace exists in WS-03                                                            |
| **Retention**            | Page lifetime; nothing persists (ADR-096, PACK-15 §13.3)                                                  |
| **Access roles**         | The voter only                                                                                            |
| **Correlation risk**     | Fingerprinting, extensions, screen observation — `T-P16A-07`, `T-P16A-26`                                 |
| **Permitted evidence**   | Aggregate client-error reason-code counts, published after closure only                                   |
| **Prohibited evidence**  | Any selection, any plaintext, any randomness, any device identifier, any user-agent string, any session replay |
| **Redaction**            | Not applicable — the data is never emitted                                                                |

---

## 2. `DF-02` — Handoff boundary (inherited)

Unchanged from PACK-15 §13.3 and `PACK-15-CROSS-BOUNDARY-DATA-FLOW-MATRIX.md`.
Restated only for the property PACK-16 depends on: **the ordinary workspace
transmits only a one-time handoff artifact**, the assertion is picked up
inside WS-03, and `pickup.redeem` returns the assertion and nothing else.
`no-referrer` on entry and exit; `no-store`; no shared service worker.

**PACK-16A adds nothing to this flow and relaxes nothing in it.**

---

## 3. `DF-03` — Continuation-capability consumption

| Field                    | Value                                                                                                       |
| ------------------------ | ------------------------------------------------------------------------------------------------------------- |
| **Data**                 | The continuation capability; the casting authorisation returned                                             |
| **Identifier**           | A consumption record on the credential side. **No ballot identifier is present, ever** (`CC-04`)             |
| **Timestamp precision**  | Coarsened to `granularity` (`CC-06`)                                                                        |
| **Network metadata**     | Voting-side only; source addresses not retained beyond the transport layer                                  |
| **Logs**                 | Reason code and coarsened timing class only; **the capability is never logged**                             |
| **Metrics**              | Aggregate consumption counts, **not published before closure** (`CC-10`)                                    |
| **Trace context**        | New voting-side chain; no identity-side context accepted or echoed                                          |
| **Retention**            | Credential-stream retention (`OD-P15-06`); the capability value itself is not retained after consumption    |
| **Access roles**         | Credential Authority (`R-04`); Independent Auditor via bundle only                                          |
| **Correlation risk**     | **Highest single risk in this document** — `T-P16A-04` redemption-to-casting timing                         |
| **Permitted evidence**   | Consumption occurred; refusal reason code; timing class; aggregate counts after closure                     |
| **Prohibited evidence**  | The capability value; any ballot identifier; any exact timestamp; any ordinal position                      |
| **Redaction**            | Refusal to record, not post-hoc redaction                                                                   |

**Controls against `T-P16A-04`:** coarsened timestamps; the PACK-15 §19.3
minting delay before this point; and **submission batching plus randomized
board publication** after it (`BB-11`). Together these mean that an
observer sees a consumption in one coarse bucket and a board entry in a
different, batched bucket, with no ordinal relationship between them.

**Residual, stated:** in a context with few participants and a quiet
interval, correlation remains plausible. Reduced and bounded, **not
eliminated** — the same honest position PACK-15 §19.5 took, extended one
step forward.

---

## 4. `DF-04` — Ballot encryption

| Field                   | Value                                                                                  |
| ----------------------- | ---------------------------------------------------------------------------------------- |
| **Data**                | Ciphertexts, proofs, confirmation code                                                 |
| **Identifier**          | `BallotId`, client-generated, unrelated to anything received (`BM-01`)                 |
| **Timestamp precision** | None embedded in the ballot                                                            |
| **Network metadata**    | None embedded                                                                          |
| **Logs / metrics / trace** | None from the client                                                                |
| **Retention**           | Until submission                                                                       |
| **Access roles**        | The voter                                                                              |
| **Correlation risk**    | Weak randomness (`T-P16A-35`); a compromised client (`T-P16A-33`)                      |
| **Permitted evidence**  | The published ballot and its proofs, after submission                                  |
| **Prohibited evidence** | Encryption randomness; any plaintext; the device's identity                            |
| **Redaction**           | n/a                                                                                    |

---

## 5. `DF-05` — Ballot submission

| Field                   | Value                                                                                                           |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------- |
| **Data**                | The encrypted ballot with proofs; the casting authorisation                                                     |
| **Identifier**          | `BallotId`. **The authorisation is consumed and is not stored with the ballot**                                  |
| **Timestamp precision** | Arrival time exists transiently for batching and is **never persisted or published** at finer than `granularity` |
| **Network metadata**    | Source address terminates at the edge and is not retained in application storage                                |
| **Logs**                | Acceptance or refusal reason code; timing class; **never the ciphertext's relation to an authorisation**        |
| **Metrics**             | Aggregate acceptance and refusal counts; **not published before closure**                                       |
| **Trace context**       | Voting-side chain; **does not cross into the board's chain** (§10)                                              |
| **Retention**           | Board retention (`BB-19`)                                                                                       |
| **Access roles**        | Voting-System Operator (`R-05`)                                                                                 |
| **Correlation risk**    | Order of arrival (`T-P16A-05`); network source (`T-P16A-06`)                                                    |
| **Permitted evidence**  | That a ballot was accepted; the reason a ballot was refused                                                     |
| **Prohibited evidence** | Arrival order; exact arrival time; source address; any authorisation reference                                  |
| **Redaction**           | Refusal to record                                                                                               |

---

## 6. `DF-06` — Bulletin board

| Field                   | Value                                                                                                          |
| ----------------------- | ---------------------------------------------------------------------------------------------------------------- |
| **Data**                | Accepted ballots, proofs, confirmation codes, spoiled ballots with openings, checkpoints, manifest, parameters, trustee evidence, tally artifacts |
| **Identifier**          | `BallotId`; board sequence number                                                                              |
| **Timestamp precision** | Checkpoint times at `granularity`; **no per-entry publication time finer than that** (`BB-11`)                  |
| **Network metadata**    | Reads are unauthenticated and not logged at per-entry granularity (`BB-09`, `T-P16A-08`)                        |
| **Logs**                | Board-integrity events, checkpoint operations, mirror synchronisation                                          |
| **Metrics**             | Availability and integrity metrics only. **Entry counts are not exposed before closure**                       |
| **Trace context**       | Board-local; no upstream context accepted                                                                      |
| **Retention**           | Governed; archived (`BB-19`, `BB-20`)                                                                          |
| **Access roles**        | Public (post-closure content); Bulletin-Board Operator (`R-06`); Independent Auditor (`R-11`) for the audit view |
| **Correlation risk**    | Verification timing (`T-P16A-08`); cross-election linkage (`T-P16A-09`)                                        |
| **Permitted evidence**  | Everything in `BB-10`, `BB-12`, `BB-15`–`BB-18`                                                                |
| **Prohibited evidence** | The entire `BB-21` list — every identity-bearing field, credential ID, assertion ID, continuation reference, pseudonym, network address, fingerprint, uncoarsened timestamp, **voter roll** |
| **Redaction**           | **Publication is refused, never redacted afterwards** (`BB-21`)                                                |

---

## 7. `DF-07` — Verification Client

| Field                   | Value                                                                                                      |
| ----------------------- | ------------------------------------------------------------------------------------------------------------ |
| **Data**                | A confirmation code supplied by the voter; the board content or a presence answer                          |
| **Identifier**          | The code only. **No account, no session, no registration** (`BB-36`)                                       |
| **Timestamp precision** | Not recorded per query                                                                                     |
| **Network metadata**    | Terminates at the edge; not retained                                                                       |
| **Logs**                | **No per-query log.** Aggregate availability only                                                          |
| **Metrics**             | Availability; **query volume is not published before closure** (`BB-27`)                                   |
| **Trace context**       | None                                                                                                       |
| **Retention**           | None per query                                                                                             |
| **Access roles**        | Public                                                                                                     |
| **Correlation risk**    | `T-P16A-08` verification timing; `T-P16A-28` fake interface                                                |
| **Permitted evidence**  | Aggregate verification-service availability                                                                |
| **Prohibited evidence** | Which code was queried; when; from where; how often; by whom                                               |
| **Redaction**           | Refusal to record                                                                                          |

**A third origin, mandatory** (`BB-14`). A verification surface inside the
casting origin is a surface an attacker who owns the casting origin also
owns, and a verification service that logs queries is building the
participation list the rest of this architecture refuses to hold.

---

## 8. `DF-08` — Tally service

| Field                   | Value                                                                            |
| ----------------------- | ---------------------------------------------------------------------------------- |
| **Data**                | The checkpointed ballot set; the homomorphic aggregate                           |
| **Identifier**          | Context reference; closure checkpoint reference                                  |
| **Timestamp precision** | Coarsened                                                                        |
| **Network metadata**    | Internal only                                                                    |
| **Logs**                | Aggregation steps and their reproducibility evidence                             |
| **Metrics**             | Process metrics only; **no outcome-bearing metric exists**                       |
| **Trace context**       | Tally-local                                                                      |
| **Retention**           | With the record                                                                  |
| **Access roles**        | Election Board (`R-01`) after closure; Independent Auditor (`R-11`)              |
| **Correlation risk**    | Low — the input is already anonymous                                             |
| **Permitted evidence**  | The aggregate; the reproducibility evidence                                      |
| **Prohibited evidence** | Any individual ballot decryption; any pre-closure aggregate                      |
| **Redaction**           | n/a                                                                              |

---

## 9. `DF-09` — Trustee service and ceremony

| Field                   | Value                                                                                                |
| ----------------------- | ------------------------------------------------------------------------------------------------------ |
| **Data**                | Guardian contributions, commitments, decryption shares and their proofs                              |
| **Identifier**          | Guardian identity and organisation — **published**, per `TP-07`                                       |
| **Timestamp precision** | Ceremony steps at `granularity`                                                                      |
| **Network metadata**    | Out-of-band where the ceremony is offline                                                            |
| **Logs**                | Ceremony record, published                                                                           |
| **Metrics**             | None outcome-bearing                                                                                 |
| **Trace context**       | Ceremony-local                                                                                       |
| **Retention**           | With the record; permanent for the public key evidence                                               |
| **Access roles**        | Trustees (`R-07`), Ceremony Coordinator (`R-08`), Independent Auditor (`R-11`), public for published parts |
| **Correlation risk**    | None to participants; the risk is collusion (`T-P16A-19`)                                            |
| **Permitted evidence**  | Everything in `PACK-16A-TRUSTEE-AND-CEREMONY-REQUIREMENTS.md` §5                                     |
| **Prohibited evidence** | Any share value; any reconstruction; any pre-closure decryption                                      |
| **Redaction**           | n/a — nothing participant-identifying enters this flow                                               |

**Guardian identity is the one deliberate identity in this architecture,
and it is published.** A secret guardian is not a check on anyone.

---

## 10. `DF-10` — Audit and export

| Field                   | Value                                                                                                 |
| ----------------------- | ------------------------------------------------------------------------------------------------------- |
| **Data**                | Evidence bundles, extended from PACK-15 §20.2 with ballot-domain sections                             |
| **Identifier**          | Context reference; bundle version                                                                     |
| **Timestamp precision** | Coarsened; generation time coarsened                                                                  |
| **Network metadata**    | Internal                                                                                              |
| **Logs**                | Export authorisation, audited to `AS-05` and `AS-06`                                                  |
| **Metrics**             | Export counts                                                                                         |
| **Trace context**       | Audit-local                                                                                           |
| **Retention**           | Governed                                                                                              |
| **Access roles**        | Independent Auditor (`R-11`) under a time-boxed PACK-12 grant, **one context per bundle**             |
| **Correlation risk**    | **Bundle differencing** — `T-P15-39`, extended to results by `T-P16A-41`                              |
| **Permitted evidence**  | PACK-15's eight sections, plus: ballot totals; challenge and spoil totals; exclusion counts by reason; board checkpoint chain; trustee participation record |
| **Prohibited evidence** | PACK-15's prohibited list unchanged, plus: any individual ballot plaintext; any un-suppressed cell below `disclosure_min_cell`; any per-participation record |
| **Redaction**           | Suppression with **complementary suppression applied jointly** (`SD-02`, `SD-05`)                     |

**Pre-closure export remains restricted** to the non-outcome-bearing
sections under dual control, exactly as PACK-15 §20.2 requires, because a
pre-closure count is an intermediate tally.

---

## 11. `DF-11` — Archive

| Field                   | Value                                                                                          |
| ----------------------- | ------------------------------------------------------------------------------------------------ |
| **Data**                | The complete published record and its integrity commitments                                    |
| **Identifier**          | Context reference; archive manifest reference                                                  |
| **Timestamp precision** | Coarsened                                                                                      |
| **Network metadata**    | None                                                                                           |
| **Logs**                | Archive operations; verification results                                                       |
| **Metrics**             | Integrity metrics                                                                              |
| **Trace context**       | Archive-local                                                                                  |
| **Retention**           | Governed; **the unresolved tension is `OD-P16A-07`** — verifiability wants permanence, secrecy wants destruction |
| **Access roles**        | Archive Custodian (`R-16`), Independent Auditor (`R-11`), public for public content            |
| **Correlation risk**    | Long-term: a future cryptanalytic break against retained ciphertexts (`T-P16A-40`)             |
| **Permitted evidence**  | The record as published                                                                        |
| **Prohibited evidence** | Anything not published at closure; any restored working data from the voting or credential side |
| **Redaction**           | None — the archive is append-only and its content was already filtered at publication          |

---

## 12. `DF-12` — Backup and restore

| Field                   | Value                                                                                                  |
| ----------------------- | -------------------------------------------------------------------------------------------------------- |
| **Data**                | Per-side backups                                                                                       |
| **Identifier**          | Backup domain identifiers, **never shared across the boundary**                                        |
| **Timestamp precision** | Backup metadata only                                                                                   |
| **Network metadata**    | Infrastructure                                                                                         |
| **Logs**                | Backup and restore operations                                                                          |
| **Metrics**             | Backup health                                                                                          |
| **Trace context**       | None                                                                                                   |
| **Retention**           | Governed                                                                                               |
| **Access roles**        | Backup administration, separated from Board Operator (`R-06`) — combination 9 of the collusion list     |
| **Correlation risk**    | **`T-P16A-10` — a restore into a shared environment recreates the join**                               |
| **Permitted evidence**  | Backup integrity records                                                                               |
| **Prohibited evidence** | Any cross-side restore target; any restore that co-locates identity-side and voting-side data          |
| **Redaction**           | n/a                                                                                                    |

**Owned by PACK-17.** Named here because backups are where boundaries go to
die, and because ADR-090 §7 already binds infrastructure.

---

## 13. Correlation channels assessed individually

| Channel                                   | Assessment                                                                                                                   | Controls                                                        | Residual                                             |
| ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------- | ------------------------------------------------------ |
| **Redemption-to-casting timing**          | **The primary risk.** Not solved by separate origins                                                                        | Coarsening; minting delay; submission batching; publication delay | **Real in low-volume contexts. Reduced, not eliminated** |
| **Submission ordering**                   | Board order is board sequence after batching, not arrival (`BM-06`, `BB-11`)                                                | Batching with a minimum batch size                                | A single-ballot batch reveals order                   |
| **Network source correlation**            | Outside the application layer                                                                                               | Separate origins; guidance                                        | **Unsolved here — PACK-17**                           |
| **Browser fingerprint correlation**       | No fingerprinting surface, no third-party origin, no analytics                                                              | ADR-096; CSP                                                      | Extensions are outside every control                  |
| **Verification timing correlation**       | Unauthenticated, unlogged reads; full-board download available                                                              | `BB-09`, `BB-24`, `BB-27`                                         | A mirror operator can observe fetches                 |
| **Cross-election correlation**            | Per-context keys, codes and parameters; no value stable across contexts                                                     | `T-P16A-09` controls                                              | A leaked derivation secret links one context          |
| **Backup snapshot correlation**           | Separate backup domains and restore targets                                                                                 | ADR-090 §7                                                        | **Restore under incident pressure — PACK-17**         |

### 13.1 Mechanisms assessed for adoption

| Mechanism                     | Adopted?                            | Reasoning                                                                                                       |
| ----------------------------- | ----------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| **Timing buckets**            | **Yes** — inherited and extended    | PACK-15 §19.2 coarsening applied to every voting-side record                                                    |
| **Delayed submission**        | **Yes**, as delayed *publication*   | `BB-11`; delaying the voter's own submission would harm usability without adding protection                     |
| **Batching**                  | **Yes**                             | `BB-11`, with a minimum batch size mirroring PACK-15's minimum-cohort principle                                  |
| **Mix networks for transport**| **No**                              | Adds a dependency and an operator without addressing the primary risk; and transport anonymity is PACK-17's     |
| **Proxy layers**              | **No** at this stage                | Same; recorded for PACK-17                                                                                      |
| **Metadata minimization**     | **Yes**                             | Throughout this document                                                                                        |
| **Independent verification channel** | **Yes** — mandatory          | `BB-14`, third origin                                                                                           |
| **Separate verification device** | **Recommended, not required**    | Estonia requires it and a device attack still defeated it `[E-28a]`; requiring a second device is an accessibility barrier |

**Timing correlation is not declared solved by the existence of separate
origins.** PACK-15 §19.5 refused that claim and this round refuses it
again: the controls reduce and bound the channel; they do not close it.

---

## 14. What PACK-16A does not decide

```text
The batch interval, minimum batch size and publication-delay distribution
   for BB-11                                        → PACK-16C
Retention periods                                   → OD-P16A-07, PACK-09
Network, transport and infrastructure controls      → PACK-17
Backup topology and restore procedure               → PACK-17
The evidence-bundle schema version increment        → PACK-16C
```

**SPECIFIED. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY. NOT LEGALLY
ACTIVATED.**
