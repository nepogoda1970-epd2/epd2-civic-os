# PACK-16C — Privacy and Metadata Matrix

**Round:** PACK-16C — Casting, Receipt, Verification Client, Bulletin Board and Election Record. **Specification and ADR only. No code. No cryptographic implementation. Not implemented. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-101`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 0. The premise

```text
The ciphertext is not the risk. The metadata around it is.

Every value that touches a ballot — who asked for what, when, from
where, in what order, how large, how often — is a potential
re-identification channel. This matrix enumerates them, states who
sees each, and states what is done about it.
```

| ID      | Rule                                                                                                                                                                                     |
| ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `PM-01` | **Every metadata field that exists anywhere in the casting path appears in this matrix.** A field not in this matrix is not permitted to be collected, logged, stored or published       |
| `PM-02` | **The default for every field is "not retained".** Retention requires a named purpose, a named holder, a stated period and an acceptance row                                             |
| `PM-03` | **No field in this matrix may be joined to a continuation capability, a credential, or an identity** (`CC-04`). This is not a policy on access; it is a prohibition on the join existing |

---

## 1. The matrix

**Legend for "Seen by":** V voter · C client · G gateway/edge · S casting
service · B board · P public · A auditor · N network observer.

| #   | Field                                         | Seen by         | Published?                   | Retained?                             | Risk if exposed                                  | Mitigation                                                                                                                                           |
| --- | --------------------------------------------- | --------------- | ---------------------------- | ------------------------------------- | ------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Ballot plaintext                              | V, C            | **never**                    | **never**                             | Total loss of secrecy                            | Never leaves the client (`VP-15`)                                                                                                                    |
| 2   | Encryption randomness (cast)                  | C               | **never**                    | **never**                             | Opens the ballot                                 | Zeroised after use (`BP-*`)                                                                                                                          |
| 3   | Encryption randomness (spoiled)               | C, P            | **yes, at closure**          | in record                             | none — the ballot is not counted                 | Published with the batch opening (`CH-32`, `TC-57`)                                                                                                  |
| 4   | Ciphertexts                                   | C, S, B, P      | **yes, delayed**             | in record                             | none under the hardness assumption               | —                                                                                                                                                    |
| 5   | NIZK proofs                                   | C, S, B, P      | **yes, delayed**             | in record                             | none                                             | —                                                                                                                                                    |
| 6   | `ballot_id`                                   | C, S, B, P      | **yes**                      | in record                             | none — client random, no structure (`BP-*`)      | Not derived from anything                                                                                                                            |
| 7   | `confirmation_code`                           | V, C, S, B, P   | **yes**                      | in record                             | proves participation if shown                    | Minimal receipt (`RE-15`)                                                                                                                            |
| 8   | `board_sequence`                              | S, B, P         | **yes**                      | in record                             | arrival-order correlation                        | **Not on the receipt** (`RE-03`); randomised within batch (`BB-*`)                                                                                   |
| 9   | `internal_object_id`                          | S               | **never**                    | operational only                      | join key                                         | Never published, never in the record (`BP-*`)                                                                                                        |
| 10  | Retry token                                   | C, S            | **never**                    | until batch publication               | links resubmissions                              | **Stripped before publication** (`BP-16`)                                                                                                            |
| 11  | Continuation capability                       | C, S            | **never**                    | **never after consumption**           | the person-to-ballot link                        | Consumed and destroyed inside the boundary (`CN-*`)                                                                                                  |
| 12  | Credential / identity                         | V, C, G         | **never**                    | PACK-15 lineage                       | the link                                         | **Never reaches the casting service** (`SB-*`)                                                                                                       |
| 13  | Exact submission time                         | S, G, N         | **never**                    | **never**                             | timing correlation with issuance                 | Granularity only (`ER-09`); resolution bounded by the batch interval (`T-P16C-46`)                                                                   |
| 14  | Exact consumption time                        | S               | **never**                    | **never**                             | same, sharper                                    | Not recorded at fine granularity (`CN-*`)                                                                                                            |
| 15  | Publication timestamp                         | B, P            | **granularity only**         | in record                             | correlation                                      | `timestamp_granularity`, batched                                                                                                                     |
| 16  | Arrival order                                 | S, G            | **never**                    | **never**                             | orders voters                                    | Randomised within batch before publication                                                                                                           |
| 17  | IP address                                    | G               | **never**                    | **short operational window only**     | direct re-identification                         | Not joined to any ballot field (`PM-03`)                                                                                                             |
| 18  | User agent / device fingerprint               | G, C            | **never**                    | **never**                             | re-identification                                | Not collected as a ballot field (`BP-17`)                                                                                                            |
| 19  | Client build identifier                       | C, S            | **yes**, as a build          | **aggregate only**                    | fingerprinting if per-device                     | **Build, never device or user** (`BP-17`, `OD-P16C-03`)                                                                                              |
| 20  | Envelope byte length                          | S, G, N         | implicitly in record         | in record                             | distinguishes ballot styles, possibly selections | **Fixed-length envelopes per style** (`BP-*`)                                                                                                        |
| 21  | Number of challenges by a voter               | C, S            | **never per voter**          | **never**                             | reveals behaviour, enables coercion patterns     | Not counted per voter (`CH-*`)                                                                                                                       |
| 22  | Challenge/cast ratio                          | S, P            | **aggregate, after closure** | in record                             | behavioural inference in small contexts          | Delayed to closure; suppressed below a threshold (`TC-*`)                                                                                            |
| 23  | Rejection reason per ballot                   | S, A            | **never before closure**     | operational                           | pattern is a correlation surface                 | **Aggregate and delayed** (`VP-13`)                                                                                                                  |
| 24  | Rejection counts by class                     | S, A, P         | **yes, after closure**       | in record                             | low                                              | Artefact 28 (`ER-*`)                                                                                                                                 |
| 25  | Accepted-count so far                         | S               | **never before closure**     | **never published live**              | intermediate turnout                             | `NIT-01`…`NIT-07`, `TC-*`                                                                                                                            |
| 26  | Board size / entry count                      | B, P            | **fixed and public**         | in record                             | was an intermediate turnout proxy                | **CORRECTED** — before closure the board's per-window entry count is exactly one, of constant size, whatever the turnout (`TC-25`, `TC-29`, `TC-33`) |
| 35  | Batch `commitment_root`                       | B, P            | **yes, per window**          | in record                             | none — fixed-size root over fixed capacity `C`   | Reveals nothing about occupancy (`TC-30`)                                                                                                            |
| 36  | Leaf index of a ballot                        | S, B            | **at closure only**          | in record                             | would encode arrival order                       | Randomised assignment; revealed only with the opening (`TC-31`)                                                                                      |
| 37  | Leaf class (`accepted` / `spoiled` / `cover`) | S               | **at closure only**          | in record                             | is occupancy                                     | Indistinguishable before closure (`TC-29`, `TC-57`)                                                                                                  |
| 38  | Batch occupancy count                         | S, A            | **at closure only**          | in record                             | **is turnout**                                   | Never published, never returned by any API, never in an event before closure (`TC-07`, `API-32`)                                                     |
| 39  | Cover-leaf value                              | S, B, P         | **at closure**               | in record                             | none — a uniform random value                    | Published in full so roots recompute (`ER-27`)                                                                                                       |
| 40  | Inclusion-proof lookup subject                | V, VC           | **never**                    | **never**                             | occupancy oracle                                 | No logging of lookup subjects; rate-limited; response shape and timing independent of presence (`TC-39`, `API-30`)                                   |
| 41  | Restricted count-comparison evidence          | A               | **never**                    | Auditor-held                          | would be the linkage if it were a join           | **It is two counts, not a pairing** (`TC-52`, `DM-10`)                                                                                               |
| 42  | Capability entitlement state                  | S               | **never**                    | anonymous continuation boundary only  | would be a per-voter activity record if joined   | Three booleans, no counter, no identity, no ballot reference (`CN-36`, `DM-20`, `DM-23`)                                                             |
| 43  | Leaf reservation state                        | S               | **never**                    | in-flight only, with timeout          | would bind a slot to a voter                     | Anonymous; bound to a submission in flight, never to a capability (`TC-73`, `DM-24`)                                                                 |
| 44  | Local diagnostic challenge                    | V, C            | **never**                    | **never — nothing leaves the device** | would be a per-voter behavioural record          | **No request, no event, no telemetry, no log** (`CH-42`, `EV-70`, `API-19`)                                                                          |
| 45  | Remaining-entitlement count                   | —               | **never**                    | **not held as a count at all**        | aggregate would be an activity signal            | Not a field anywhere (`CN-37`, `DM-23`, `EV-72`)                                                                                                     |
| 46  | Capacity occupancy / remaining slots          | S               | **never**                    | operational only                      | **is turnout**                                   | Never returned by any operation, never in an event, never in an incident (`TC-81`, `RN-16C-29`)                                                      |
| 27  | Lookup query (confirmation code)              | V, VC, N        | **never**                    | **never**                             | reveals who is checking what                     | No logging of lookup subjects (`VC-*`)                                                                                                               |
| 28  | Lookup result                                 | V, VC           | **never**                    | **never**                             | same                                             | Client-side evaluation where possible                                                                                                                |
| 29  | Verification-client access logs               | VC operator     | **never**                    | **not retained**                      | reveals verifiers                                | `VC-*`; offline mode has none (`IV-*`)                                                                                                               |
| 30  | Receipt contents                              | V               | not published                | voter's own copy                      | proves participation                             | Minimal by construction (`RE-01`)                                                                                                                    |
| 31  | Support-case metadata                         | Support, A      | **never**                    | DP-governed                           | may link person to a casting event               | **Never includes a ballot identifier** (`DP-*`)                                                                                                      |
| 32  | Dispute record                                | A, P            | **aggregate/anonymised**     | in record where published             | may identify a complainant                       | `DP-*`; the complainant is never named publicly                                                                                                      |
| 33  | Mirror fetch logs                             | Mirror operator | **never**                    | operator policy                       | reveals readers                                  | Mirrors are third parties; stated, not controlled (`AO-*`)                                                                                           |
| 34  | Network-layer traffic                         | N               | —                            | —                                     | timing and volume correlation                    | **Not solved.** `T-P16A-04`, `RR-06` — stated, not claimed away                                                                                      |

---

## 2. The four channels that remain open

Named here rather than distributed through the table, because these are what
a serious adversary would use.

| Channel                                      | What it gives an adversary                                                 | Status                                                                                                                                                                     |
| -------------------------------------------- | -------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Network-layer observation** (#34)          | Who connected to the casting service, when, and how much they sent         | **Open.** Batching, fixed-length envelopes and delay reduce resolution; a global passive observer is not defeated                                                          |
| **Issuance-to-submission timing** (#13, #14) | Correlating a credential-side event with a ballot-side event               | **Reduced** by granularity, batching and randomised publication order; **not eliminated**, and the residual is `RB-16C-01`                                                 |
| **Small-context statistics** (#22, #38)      | In a context with few voters, aggregates identify people **after closure** | **Bounded** by suppression thresholds and by not activating electronically below a minimum size (`TC-16`…`TC-19`). Before closure there are no aggregates at all (`TC-07`) |
| **Gateway/edge infrastructure** (#17, #18)   | The edge sees addresses; the service sees ballots                          | **Separated by principal**, never joined (`PM-03`); a single operator controlling both is a governance risk, not a technical one, and is stated as such                    |

| ID      | Rule                                                                                                                                                                                                                                                                                                            |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `PM-04` | **These four are declared, not mitigated away.** No participant-facing text may claim anonymity in a sense these channels contradict (`PB-*`)                                                                                                                                                                   |
| `PM-05` | **The gateway and the casting service are separate principals with separate operators where governance permits**, and where they are not, the combined-visibility risk is published with the context                                                                                                            |
| `PM-06` | **Fixed-length envelopes per ballot style are normative**, because a length that varies with selections is a direct leak of the selection (`BP-*`)                                                                                                                                                              |
| `PM-07` | **Leaf index within a batch is randomised**, so board position does not encode arrival order (#8, #16, #36, `TC-31`)                                                                                                                                                                                            |
| `PM-13` | **Before closure the board is a metadata-free channel.** One constant-size entry per fixed window, whatever happened. Rows 26 and 35–39 are the correction: what was a live occupancy channel is now a constant (`TC-29`)                                                                                       |
| `PM-15` | **Rows 42–46 are the capacity correction's privacy surface, and every one of them is "never published".** Entitlement state, reservation state and capacity occupancy are the three places a bounded-capacity design most easily leaks activity, and all three are closed by construction rather than by policy |
| `PM-16` | **Row 44 is the strongest privacy statement in this matrix.** A local diagnostic challenge generates no data at all — which is why the repeatable part of the challenge mechanism was moved there                                                                                                               |
| `PM-14` | **The correction moves a leak; it does not delete one.** At closure, leaf index and batch membership localise a ballot's acceptance to one interval (`T-P16C-46`). That is strictly less than a running total, and it is not nothing                                                                            |

---

## 3. Logging rules

```text
NEVER LOGGED    ballot plaintext · any nonce of a cast ballot
                continuation capability · credential · identity
                exact submission or consumption time
                ciphertexts together with request metadata
                confirmation code together with any request metadata
                lookup subjects in the Verification Client

LOGGED, BOUNDED aggregate counters · error classes without ballot detail
                infrastructure health · gateway addresses, short window,
                never joined to ballot fields
```

| ID      | Rule                                                                                                                                                                                      |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `PM-08` | **A log line that would let two of the "never joined" fields be correlated is prohibited even if each field alone is permitted.** The prohibition is on the join, not the field (`PM-03`) |
| `PM-09` | **Debug and support modes do not relax these rules.** There is no elevated logging level that exposes a ballot's content, because the service never holds it (`VP-15`)                    |
| `PM-10` | **Log retention for anything in this matrix is the shortest period that serves its named purpose**, and the period is published with the context                                          |

---

## 4. Relationship to PACK-15's privacy lineage

PACK-15 separated eligibility from credentials and specified the continuation
capability so that the identity side and the ballot side never meet.
**PACK-16C's contribution is to keep that true on the ballot side**, where
the artefacts are public and permanent.

| ID      | Rule                                                                                                                                                                                                                          |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `PM-11` | **A public, permanent record raises the cost of a metadata mistake to irreversible.** A field wrongly published cannot be unpublished (`BL-03`, `AO-*`), so every field in §1 is decided before publication exists, not after |
| `PM-12` | **Any new field introduced in PACK-16D must be added to this matrix and to the acceptance matrix before it is implemented**, and a field introduced without a row is a defect regardless of its content                       |

---

## 5. What this document does not decide

```text
Concrete retention periods                   → GOVERNANCE, published per context
Gateway operator arrangements                 → GOVERNANCE, PM-05
Suppression thresholds                        → TC-17, GOVERNANCE
Batch interval and capacity                   → OD-P16C-10, GOVERNANCE
Lookup rate-limit values                       → API-*, PACK-16D
Network-layer defences                        → PACK-17, unsolved here
```

**SPECIFIED. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY. NOT LEGALLY
ACTIVATED.**
