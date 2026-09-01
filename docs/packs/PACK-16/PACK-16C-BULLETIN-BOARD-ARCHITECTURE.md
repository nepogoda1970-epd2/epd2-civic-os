# PACK-16C — Bulletin Board Architecture

**Round:** PACK-16C — Casting, Receipt, Verification Client, Bulletin Board and Election Record. **Specification and ADR only. No code. No cryptographic implementation. Not implemented. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-101`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 1. The board is a separate bounded context and a separate trust boundary

```text
The board is not a feature of the casting service.
It is the artefact that makes the casting service checkable,
and it must be operable by someone who does not run the casting service.
```

| ID      | Rule                                                                                                                                                         |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `BA-01` | **The board is its own bounded context**, with its own operator role (`R-06`), its own origin, its own storage and its own signing key                       |
| `BA-02` | **The Bulletin-Board Operator holds no guardian share, no election-officer role and no write access to the casting service's stores** (`BB-29`, `RS-16B-09`) |
| `BA-03` | **The casting service cannot modify a published entry**, and possesses no operation that could                                                               |
| `BA-04` | **One board per voting context** (`BB-02`). No shared board across contexts, no cross-context references, no cross-context derivation (`T-P16A-09`)          |

## 2. Properties

| Property                     | Rule                                                                            | Inherited        |
| ---------------------------- | ------------------------------------------------------------------------------- | ---------------- |
| **Append-only**              | No operation modifies or removes a published entry; deletion is not implemented | `BB-01`          |
| **Election-scoped**          | One canonical namespace per context                                             | `BB-02`          |
| **Canonical ordering**       | Total order by **board sequence**, assigned at publication, published as a rule | `BB-03`, `BM-06` |
| **Globally consistent**      | Every reader verifying a checkpoint sees the same content for that checkpoint   | `BB-04`          |
| **Equivocation-resistant**   | Divergent views detectable by comparing signed checkpoints across mirrors       | `BB-05`          |
| **Signed checkpoints**       | Periodic signed commitments over content to that point                          | `BB-06`          |
| **Independently mirrorable** | ≥ 2 mirrors under distinct organisational control                               | `BB-07`          |
| **Publicly auditable**       | Whole board downloadable as one artefact with a published digest                | `BB-09`          |
| **Privacy-filtered**         | Every entry checked against the prohibited-content list before publication      | `BB-21`          |
| **Versioned**                | Entries and the board state carry a schema version                              | `BB-35`          |
| **Archivable**               | An archived board verifies with the same verifier and the same published rules  | `BB-20`          |

## 3. Prohibited board content — normative

```text
identity                     credential ID
continuation capability      continuation reference
member identifier            account identifier
IP address                   device fingerprint
private ballot nonce (cast)  plaintext of a cast ballot
exact submission timestamp   arrival order
retry token                  internal object ID
session or trace ID          any free-text field
```

| ID      | Rule                                                                                                                                                                                                                                                                                                                  |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `BA-05` | **Privacy filtering happens before publication, not after** (`BB-21`). An entry that fails the filter is not published and the failure is an incident, not a redaction                                                                                                                                                |
| `BA-06` | **Append-only means a mistaken publication cannot be withdrawn.** That is why `BA-05` is a gate and not a review step                                                                                                                                                                                                 |
| `BA-07` | **The board publishes no count of accepted ballots before closure** (`TC-07`), and no figure from which one can be derived — including entry totals, sequence maxima, page counts and **the serialized size of any published entry** (`TC-33`)                                                                        |
| `BA-24` | **Before closure the board publishes no individual ballot entry at all.** The only per-window publication is one constant-size `sealed_batch_commitment` (`BE-24`, `TC-04`, `TC-29`). Individual `ballot_accepted`, `ballot_challenged` and `ballot_spoiled` entries appear **at closure**, with their batch openings |
| `BA-25` | **The batch cadence is fixed, gapless and non-adaptive**, and an empty window publishes its commitment like any other (`TC-23`, `TC-24`, `TC-25`)                                                                                                                                                                     |
| `BA-26` | **Every predeclared reserve commitment for every interval is published on schedule, empty or not** (`TC-67`). The published shape of an interval is identical whether one artefact or `C_interval` artefacts were produced                                                                                            |
| `BA-27` | **The board creates no unscheduled batch, ever** (`TC-68`). There is no operation that does so, and its absence is checkable (`API-34`)                                                                                                                                                                               |
| `BA-28` | **The board accepts no publication-bearing artefact without an atomically reserved leaf slot** (`TC-70`). The board never holds an accepted artefact for which it has no scheduled place                                                                                                                              |
| `BA-29` | **There is no overflow queue, hidden or otherwise** (`TC-80`). An artefact is reserved into a scheduled leaf or it was never accepted                                                                                                                                                                                 |

## 4. Publication model

```text
SEALED BATCH COMMITMENTS ON A FIXED CADENCE,
OPENED IN FULL AT CLOSURE.          (BB-11 satisfied by TC-* §4)

Entries are accumulated and published in batches at intervals with a
randomized offset, so that publication time carries no information
about submission time, and board order carries no arrival order.
```

| ID      | Rule                                                                                                                                                                                                                                                                                                                   |
| ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `BA-08` | **Board sequence is assigned within a batch in an order independent of arrival.** Under the corrected model this is realised by randomised **leaf-index assignment** inside the sealed batch, revealed at closure (`TC-31`); the property — position never encodes arrival order — is unchanged (`BM-06`, `T-P16A-05`) |
| `BA-09` | **Every entry's published timestamp is the batch's, coarsened to the context's granularity.** No per-entry time is published                                                                                                                                                                                           |
| `BA-10` | **The batching interval and the delay distribution are published in the manifest before `voting_open`**, so that the schedule is a known parameter and not a lever                                                                                                                                                     |
| `BA-11` | **Spoiled ballots occupy leaves in the same sealed batches as accepted ones and are opened with them** (`CH-33`, `TC-57`), so challenging is not a timing signal and not a participation signal                                                                                                                        |

## 5. Individual verification without a live count

The board must let a voter check their own ballot while revealing no
aggregate. That tension is resolved by what a lookup returns.

| ID      | Rule                                                                                                                                                                                                                                                                                  |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `BA-12` | A lookup by confirmation code returns **presence-or-absence, the voter's own leaf opening, a Merkle inclusion path and the current signed checkpoint, and nothing else** (`BB-22`, `BB-25`, `TC-36`…`TC-40`). It never returns occupancy, a count, or another occupant's leaf opening |
| `BA-13` | **No position, no index, no neighbours, no total, no timestamp finer than the context's granularity** (`BB-23`)                                                                                                                                                                       |
| `BA-14` | **Lookups are unauthenticated and rate-limited per code, not per participant** (`BB-24`)                                                                                                                                                                                              |
| `BA-15` | **Query volume is not published, exported or displayed before closure** — it is a turnout proxy (`BB-27`)                                                                                                                                                                             |
| `BA-16` | **Full-board download is available**, and is the route that necessarily reveals the entry count — which is why it is subject to `TC-*`'s decision on pre-closure availability                                                                                                         |

## 6. Mirrors

| ID      | Rule                                                                                                                                                                                 |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `BA-17` | **At least two mirrors under organisationally distinct control** — not two servers under one operator (`BB-07`, `BB-28`)                                                             |
| `BA-18` | **No mirror operator holds a guardian share, an election-officer role, or write access to the primary board** (`BB-29`)                                                              |
| `BA-19` | **Each mirror publishes its own signature over every checkpoint it has seen**, so divergence is attributable rather than merely detectable (`BB-30`)                                 |
| `BA-20` | **Mirror divergence halts the tally pending a governance decision** (`BB-31`, `FM-P16A-11`). It is not a warning and not an eventual-consistency artefact                            |
| `BA-21` | **The mirror list is published in the manifest before `voting_open`**; adding a mirror mid-election is a recorded governance act, and removing one is a published incident (`BB-32`) |

**Stated plainly:** mirror independence is **organisational and cannot be
enforced technically** (`RR-12`). Two mirrors operated by the same people in
two data centres satisfy the letter and none of the purpose.

## 7. Availability

| ID      | Rule                                                                                                                                                                      |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `BA-22` | **Board unavailability pauses casting** (`FM-P16A-09`), because accepting ballots that cannot be published creates the state `PA-*` forbids                               |
| `BA-23` | **The board's availability is a single point of failure for casting**, and this is recorded as a residual risk rather than engineered away by weakening `BA-22` (`RR-15`) |

## 8. What this document does not decide

```text
The append-only mechanism                → PACK-16C-APPEND-ONLY-AND-CONSISTENCY-MODEL.md
Entry types and their fields              → PACK-16C-BULLETIN-BOARD-ENTRY-CATALOG.md
Acceptance-to-publication relationship     → PACK-16C-PUBLICATION-ATOMICITY-MODEL.md
Batch interval and capacity                → OD-P16C-10, GOVERNANCE
Storage product and hosting                → PACK-16D
Mirror operator selection                  → GOVERNANCE, OD-P16C-11
```

**SPECIFIED. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY. NOT LEGALLY
ACTIVATED.**
