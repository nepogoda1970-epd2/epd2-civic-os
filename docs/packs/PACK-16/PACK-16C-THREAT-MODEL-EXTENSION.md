# PACK-16C — Threat Model Extension

**Round:** PACK-16C — Casting, Receipt, Verification Client, Bulletin Board and Election Record. **Specification and ADR only. No code. No cryptographic implementation. Not implemented. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-101`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

**This extends `PACK-16A-THREAT-MODEL.md` (`T-P16A-01`…`T-P16A-42`), which
stands unchanged.** No inherited threat is removed, renumbered, downgraded
or declared solved. What follows are the threats that only exist once
casting, a receipt, a Verification Client, a public board and a permanent
record exist.

---

## 0. Adversaries, unchanged

The PACK-16A adversary set is inherited exactly: the curious insider, the
malicious operator, the compromised voting device, the coercer, the network
observer, the dishonest guardian, the outside attacker, and the future
adversary with more compute. **PACK-16C adds one:**

| Adversary            | Capability                                                                                           | Why PACK-16C introduces it                                                                                                                 |
| -------------------- | ---------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| **The board reader** | Fetches every public artefact, repeatedly, forever, and correlates them with anything else they know | Publishing the record is the design's central act. Everything published is available to an adversary who never touches EPD² systems at all |

| ID          | Rule                                                                                                                                                                                                                                           |
| ----------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `T-P16C-00` | **The board reader is assumed to be permanent, patient, well-resourced and to hold out-of-band knowledge** — a membership list, a room, a schedule. Every published artefact is designed against this adversary, not against a casual observer |

---

## 1. Correlation threats introduced by publication

| ID          | Threat                                                                                          | Mitigation                                                                                                                                                          | Residual                                                                                                                                        |
| ----------- | ----------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| `T-P16C-01` | **Publication timing correlates with a credential-side event**                                  | Batching, randomised batch boundaries, granularity-only timestamps (`TC-04`…`TC-06`)                                                                                | **Real.** A global observer of both sides retains signal — `RB-16C-01`                                                                          |
| `T-P16C-02` | **Board position encodes arrival order**                                                        | Randomised order within a batch; sequence not on the receipt (`PM-07`, `RE-03`)                                                                                     | Batch membership still bounds arrival to an interval                                                                                            |
| `T-P16C-03` | **Batch size is a live turnout feed**                                                           | **CORRECTED.** Constant-size `sealed_batch_commitment` on a fixed gapless cadence; real and cover leaves structurally indistinguishable (`TC-25`, `TC-29`, `TC-33`) | An observer learns the public constant `C` and the public cadence, and nothing about this election. The rejected padding model's leak is closed |
| `T-P16C-04` | **Envelope length varies with selections**                                                      | Fixed-length envelopes per style (`PM-06`, `BP-*`)                                                                                                                  | Style itself is visible, and in a multi-style context that partitions voters                                                                    |
| `T-P16C-05` | **Retry token links two submissions**                                                           | Stripped before publication (`BP-16`, `VP-*` §6)                                                                                                                    | The service sees it before stripping; retention is bounded                                                                                      |
| `T-P16C-06` | **Small-context statistics identify individuals**                                               | Minimum electorate size; suppression thresholds (`TC-16`…`TC-19`)                                                                                                   | **Below the threshold the electronic channel is not used at all** — the mitigation is non-activation                                            |
| `T-P16C-07` | **Cross-election correlation** — the same person's ballots across several contexts              | `ballot_id` is client-random with no structure; no value is carried between contexts (`BP-*`)                                                                       | Behavioural timing across elections is not defended against                                                                                     |
| `T-P16C-08` | **Long-horizon re-identification** — the record is permanent, and future techniques are unknown | Nothing correlating is published in the first place (`ER-*` §2)                                                                                                     | **The record cannot be unpublished** (`PM-11`). This is why §2's field list is decided before publication exists                                |

---

## 2. Threats against the receipt and the verification path

| ID          | Threat                                                                 | Mitigation                                                                                                             | Residual                                                                                                               |
| ----------- | ---------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| `T-P16C-09` | **Coerced receipt disclosure proves participation**                    | The receipt is minimal and content-free (`RE-15`)                                                                      | **Unsolved.** Participation coercion is outside what a receipt can defend (`RE-14`)                                    |
| `T-P16C-10` | **Coerced challenge transcript** — "challenge showing X, then cast"    | A challenged ballot is never counted (`CH-05`); interface text says so (`CH-29`, `CB-06`)                              | **Unsolved.** Nothing in the record distinguishes the pattern from honest use (`CB-05`)                                |
| `T-P16C-11` | **Fake Verification Client** tells a voter their ballot is fine        | Published separate origin, published build digest, reproducible build, independent verifiers (`VC-*`, `IV-*`)          | A voter who trusts a fake site can be told anything                                                                    |
| `T-P16C-12` | **Verification lookups are logged and correlated**                     | No logging of lookup subjects; offline mode; no account (`API-30`, `EV-63`)                                            | A network observer of the lookup still learns that someone looked up something                                         |
| `T-P16C-13` | **The voter's device shows a receipt for a ballot it never submitted** | Receipt is derivable only from public data and re-fetchable from the board by a second device (`RE-04`, `VC-*`)        | A voter who checks only on the compromised device learns nothing new                                                   |
| `T-P16C-14` | **Confirmation-code transcription error is read as a missing ballot**  | Unambiguous alphabet, grouping, audio rendering, and a dispute path that names all three causes (`RE-09`, `RN-16C-20`) | A voter who gives up before disputing is invisible                                                                     |
| `T-P16C-15` | **Verification take-up is too low to detect anything**                 | Verification is easy, free, account-free and encouraged                                                                | **Real and empirical** (`RR-04`). Detection is probabilistic across the electorate, and no per-voter guarantee follows |

---

## 3. Threats against the board and the record

| ID          | Threat                                                                     | Mitigation                                                                                                                       | Residual                                                                                |
| ----------- | -------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| `T-P16C-16` | **Split view** — different readers are shown different boards              | Chained signed checkpoints, mirrors, co-signing, published gossip (`AO-*`)                                                       | **Rests on mirror independence** until external witnesses exist (`OD-P16C-12`, `AO-13`) |
| `T-P16C-17` | **Late insertion** of a ballot after closure                               | Consistency proofs between checkpoints; the closure checkpoint fixes the set (`BM-20`)                                           | Detectable only if someone checks consistency; a board nobody audits proves nothing     |
| `T-P16C-18` | **Rollback** to an earlier tree head                                       | Checkpoint chaining; the receipt carries the checkpoint current at issuance (`RE-*`, `BB-25`)                                    | Same — requires a checker                                                               |
| `T-P16C-19` | **Silent non-publication of an accepted ballot**                           | Signed publication commitment, published deadline, `publication_disputed` as a public state (`PA-*`)                             | The voter must notice and report; the deadline bounds how long that takes               |
| `T-P16C-20` | **Board signing key substitution**                                         | Key publication history in the record; rotation is a published event (`EV-27`, `ER-*` artefact 26)                               | A reader who never fetches the history sees nothing                                     |
| `T-P16C-21` | **Mirror collusion with the primary**                                      | Mirror independence requirements; co-signature divergence is publishable                                                         | **Organisational, not cryptographic** (`AO-13`) — stated as such                        |
| `T-P16C-22` | **Denial of service against publication**                                  | Pause rather than accumulate unpublishable ballots (`FM-P16A-09`, `FMR-11`)                                                      | An attacker can stop an election; they cannot corrupt it silently                       |
| `T-P16C-23` | **Record poisoning** — a valid-looking artefact that is not what it claims | Every artefact is digest-bound and covered by a checkpoint; the record manifest covers all of them (`ER-*` artefact 32, `ER-16`) | A verifier that skips the manifest check is fooled                                      |
| `T-P16C-24` | **Archive substitution after the fact**                                    | Archive checkpoint over the whole record; independent copies (`ER-24`, `IV-09`)                                                  | Depends on someone holding an independent copy                                          |

---

## 3A. Threats against the sealed batch layer

Added by the turnout correction. **`T-P16C-39` is the threat the first
candidate failed to close.**

| ID          | Threat                                                                                                                                               | Mitigation                                                                                                                                                   | Residual                                                                                                                                                                                                                |
| ----------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `T-P16C-39` | **Turnout inference from entry count** — counting the board's per-ballot entries during voting                                                       | No per-ballot entry is published before closure; one constant-size entry per window (`TC-04`, `BA-24`, `BE-28`)                                              | None from the board. Network-layer observation of the casting service is unchanged and unsolved                                                                                                                         |
| `T-P16C-40` | **Turnout inference from batch absence** — a window with no entry means no ballots                                                                   | **Empty windows publish too**, and are indistinguishable from full ones (`TC-25`). A missing entry is a published failure, not a signal (`FM-16C-18`)        | An observer learns that the board failed, which is intended                                                                                                                                                             |
| `T-P16C-41` | **Turnout inference from commitment size** — a variable-length entry encodes occupancy                                                               | Every field is fixed-width or drawn from a published profile; **serialized size is constant across batches** (`TC-33`, `BA-07`, `BE-20`)                     | Transport-layer compression could reintroduce a size channel; PACK-16D must not compress the entry adaptively                                                                                                           |
| `T-P16C-42` | **Occupancy oracle through the lookup API** — probing confirmation codes to count real leaves                                                        | High-entropy unguessable codes; rate limits; response shape and timing independent of presence; no enumeration operation exists (`TC-38`, `TC-39`, `API-20`) | **A party already holding many voters' codes learns those ballots are committed** — but it already knew those people participated (`RE-14`). It learns nothing about leaves it holds no code for                        |
| `T-P16C-43` | **Adaptive batch cadence** — an operator lengthens or shortens windows in response to load                                                           | Cadence, interval and capacity are frozen before voting opens and published; adaptation is prohibited (`TC-22`, `TC-24`)                                     | **Organisational.** A dishonest operator could still deviate — which is publicly detectable, because the schedule is public                                                                                             |
| `T-P16C-44` | **Late conversion of a cover leaf into a ballot**                                                                                                    | A cover leaf is a uniformly random value; converting it after publication requires a second preimage of the leaf commitment (`TC-28`, `TC-50`)               | Rests on the hash's second-preimage resistance, which `EPD2-CRYPTO-1` already assumes                                                                                                                                   |
| `T-P16C-45` | **Cover-leaf manipulation** — cover leaves generated with low entropy or from a predictable source, letting an observer distinguish them             | Cover leaves use PACK-16B's randomness discipline and its self-tests; `bulletin_board.cover_leaf_invalid` at closure (`TC-28`, `FM-16C-26`)                  | **A weak generator would break indistinguishability silently before closure.** This is the sharpest new implementation risk and belongs to PACK-16D — `RB-16C-10`                                                       |
| `T-P16C-46` | **Batch-boundary timing correlation** — a ballot accepted just before a window appears in that window, narrowing its acceptance time to one interval | The interval bounds the resolution; no per-ballot time is ever published; leaf index is randomised (`TC-31`, `ER-09`)                                        | **Real and bounded.** A voter's acceptance is localised to one interval once the openings are public. Shorter intervals worsen it; longer intervals worsen `PA-10`. The trade-off is stated, not resolved — `RB-16C-11` |
| `T-P16C-47` | **Selective opening** — a batch opened in part, hiding leaves                                                                                        | Opening is complete or the record is incomplete (`TC-45`, `FM-16C-23`); a root does not recompute without every leaf (`TC-41`)                               | Detectable by any verifier at closure, and only at closure                                                                                                                                                              |
| `T-P16C-48` | **Incomplete closure reconciliation** — the mapping is published but does not close                                                                  | Reconciliation is a blocking verifier check (`IV-15`, check 19); failure is `abort` or `annul` (`FM-16C-27`)                                                 | Depends on someone running check 19 — a record nobody verifies proves nothing (`BM-28`)                                                                                                                                 |

| ID          | Rule                                                                                                                                                                                                                                                                |
| ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `T-P16C-49` | **`T-P16C-46` is the price of the correction and is stated as such.** The rejected model leaked the running total continuously; the corrected model leaks, at closure, the _window_ in which each ballot was accepted. That is strictly less, and it is not nothing |
| `T-P16C-50` | **None of `T-P16C-39`…`T-P16C-48` is claimed to be eliminated by cryptography alone.** Three rest on governance (`T-P16C-43`), on implementation quality (`T-P16C-45`) or on someone actually verifying (`T-P16C-48`)                                               |

---

## 3B. Threats against bounded challenge and finite capacity

Added by the capacity correction. **`T-P16C-51` is the threat the previous
candidate did not close.**

| ID          | Threat                                                                                                                                        | Mitigation                                                                                                                                                                                            | Residual                                                                                                                                                                  |
| ----------- | --------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `T-P16C-51` | **Unbounded spoiled-ballot batch exhaustion** — unlimited published challenges against a finite `C`                                           | **Closed architecturally.** `K = 1` per capability, so publication-bearing artefacts are bounded by `L_max = E × (K + A)` and the plan is computed from it before opening (`CH-37`, `TC-59`, `TC-64`) | The bound is only as good as `E`. An issuance policy that over-issues capabilities inflates `L_max` and the plan with it — a governance property, not a cryptographic one |
| `T-P16C-52` | **Single-capability public-challenge flooding**                                                                                               | One capability yields at most one public spoiled artefact (`CH-43`, `CN-35`). Idempotency binding, rate limiting and validation before durable reservation (`CN-41`, `TC-70`)                         | A holder of many capabilities scales linearly with what they hold — which is the eligibility problem (`VP-17`), not a new one                                             |
| `T-P16C-53` | **Challenge capacity consuming cast capacity**                                                                                                | Capacity is partitioned in advance; a public challenge may **never** take a cast-reserved slot (`TC-74`, `TC-75`, `FM-16C-34`)                                                                        | If the partition is mis-sized, challenges are refused while cast capacity idles. Refusing a check is better than refusing a vote, and it is stated as the chosen trade    |
| `T-P16C-54` | **Adaptive overflow batch turnout leakage** — a reserve batch that appears only under load announces a busy interval                          | **All predeclared reserves publish on schedule, empty or not** (`TC-67`, `BA-26`). Unscheduled batches are prohibited (`TC-68`)                                                                       | Cost: reserves are published even when never needed, so the record is larger than the election was. That cost is accepted deliberately                                    |
| `T-P16C-55` | **Hidden overflow queue** — accepted artefacts parked outside the schedule                                                                    | No artefact is accepted without a reserved leaf (`TC-70`, `BA-28`); no queue exists (`TC-80`)                                                                                                         | An implementation could build one. `API-34`'s checkable-absence discipline is the defence, and it is a PACK-16D obligation                                                |
| `T-P16C-56` | **Reservation race** — two submissions reserve the same slot                                                                                  | Reservation is inside the atomic boundary and is part of the all-or-nothing effect (`TC-70`, `CN-39`)                                                                                                 | Rests on the same transaction mechanism as `OD-P16C-01`; if that is unsound, this is unsound too                                                                          |
| `T-P16C-57` | **Reservation leak** — a slot held after a rejection or never released on timeout                                                             | Release on fail-closed rejection; reservation timeout (`TC-71`, `TC-72`); reconciliation at closure                                                                                                   | **Real and quiet.** Leaked reservations shrink real capacity with no public sign until closure — `FM-16C-33`, `RB-16C-13`                                                 |
| `T-P16C-58` | **Capacity incident revealing live turnout**                                                                                                  | The incident publishes no occupancy, no remaining slots, no queue depth and no turnout figure (`TC-81`, `RN-16C-32`)                                                                                  | **The incident's existence is itself a signal** that the election is busier than planned. It is published anyway, because concealing a capacity failure is worse          |
| `T-P16C-59` | **Replay of a public-challenge entitlement**                                                                                                  | Idempotent submission returns the prior outcome; a second differing submission fails closed (`CN-41`, `FM-16C-32`)                                                                                    | Depends on the same idempotency binding as `API-15`                                                                                                                       |
| `T-P16C-60` | **Public challenge followed by challenged-ballot reuse** — casting the ciphertext, nonce, ballot ID or confirmation code that was just opened | Prohibited and detectable: the opened values are public, so reuse is visible in the record (`CH-48`)                                                                                                  | A client that reuses them has revealed the voter's choice, which is a client-compromise event, not a protocol gap                                                         |
| `T-P16C-61` | **Linking a public challenge artefact to its later cast ballot**                                                                              | Independent public references; nothing published links them (`CH-49`)                                                                                                                                 | Timing within an interval still groups them loosely once the batches are opened (`T-P16C-46`)                                                                             |
| `T-P16C-62` | **A malicious client fakes a local diagnostic challenge** and shows a reassuring result                                                       | **Not preventable, and not claimed to be.** The local check is explicitly not evidence (`CH-40`, `CH-41`); the public audit challenge and independent verification are the evidentiary paths          | **Open by construction.** This is why the public evidentiary challenge exists at all, and why bounding it to one is a real cost                                           |

| ID          | Rule                                                                                                                                                                                                                                                                                                                                                                 |
| ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `T-P16C-63` | **`T-P16C-62` is the price of the two-tier split, and it is stated rather than absorbed.** Moving unlimited checking to a local, unpublished path removes the board-exhaustion threat and returns exactly one thing to the attacker: a client that can lie about local checks all day. The public audit challenge — one per capability — is what remains to catch it |
| `T-P16C-64` | **Nothing in §3B is closed by cryptography alone.** `T-P16C-51` rests on `E` being honest, `T-P16C-53` on the partition being sized well, `T-P16C-55` on an implementation not building a queue, and `T-P16C-57` on reservation hygiene                                                                                                                              |

---

## 4. Threats against the atomic boundary

| ID          | Threat                                                                            | Mitigation                                                                                                                                                                            | Residual                                                                                                                                                                                                                                             |
| ----------- | --------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `T-P16C-25` | **Double-spend of a capability** under concurrency                                | Re-check unspent _inside_ the boundary; exactly-once effect (`CN-03`, pipeline 19–20)                                                                                                 | Depends on a transaction mechanism PACK-16D must demonstrate — `OD-P16C-01`                                                                                                                                                                          |
| `T-P16C-26` | **Partial commit** — capability consumed, ballot not recorded                     | All-or-nothing boundary; rollback is a first-class outcome (`FM-16C-14`)                                                                                                              | If the mechanism cannot guarantee atomicity, this is an **`ARCHITECTURAL BLOCKER`**, not an accepted risk (`CN-19`)                                                                                                                                  |
| `T-P16C-27` | **Retry-token confusion** — same token, different envelope                        | Explicit conflict rejection (`submission.retry_token_conflict`, stage 17)                                                                                                             | A client that loses its token cannot resume; the ballot is re-preparable                                                                                                                                                                             |
| `T-P16C-28` | **Boundary observability reconstructs the link**                                  | The two halves are written to separate stores with no shared key and no trace spanning them; **the capability-side half is not an event at all** (`DM-10`, `EV-05`, `EV-06`, `EV-71`) | **An operator with database-level access to both stores and precise timing could correlate.** This is the sharpest insider threat in the round, and the defence is separation of principals and the absence of a join key — not access control alone |
| `T-P16C-29` | **Acceptance without publication capability** — accepting while the board is down | Casting pauses when ballots cannot be published (`FMR-11`)                                                                                                                            | A pause is visible and disruptive; that is preferred to a silent backlog                                                                                                                                                                             |

---

## 5. Threats against the client and the flow

| ID          | Threat                                                             | Mitigation                                                                                                                          | Residual                                                                                                        |
| ----------- | ------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `T-P16C-30` | **Compromised client encrypts a different choice**                 | Cast-or-challenge, commitment before choice (`CH-*`)                                                                                | **Detection, never prevention** (`T-P16A-33`), probabilistic and dependent on take-up                           |
| `T-P16C-31` | **Client suppresses the challenge option**                         | Challenge is offered with equal prominence; the commitment precedes the choice; the published build is checkable (`CH-*`, `API-27`) | A voter using a substituted build may never see it                                                              |
| `T-P16C-32` | **Client cheats the commitment ordering**                          | The commitment is shown before the cast/challenge choice and is bound into the code (`CH-01`)                                       | A fully compromised client can lie about what it committed — which is exactly what a challenge would reveal     |
| `T-P16C-33` | **Served build differs from the published build**                  | Published build digest, reproducible builds, `manifest.client_build_mismatch`, `FM-16C-01`                                          | A targeted substitution served only to some voters is detectable only by those voters checking                  |
| `T-P16C-34` | **Client exhausts the voter's patience** so they skip verification | Verification is short, optional, free and possible later from any device (`VC-*`)                                                   | Behavioural, not technical                                                                                      |
| `T-P16C-35` | **Probe endpoint used to enumerate capabilities**                  | `API-14` is read-only, rate-limited, and its timing does not distinguish outcomes (`API-37`)                                        | An attacker holding candidate capabilities learns validity, which is why capabilities are unguessable (PACK-15) |

---

## 6. Threats this round does **not** address

Named so that no reader mistakes silence for coverage.

```text
NOT ADDRESSED   network-layer traffic analysis          T-P16A-04, PM-* #34
NOT ADDRESSED   a coercer physically present            T-P16A-31, CB-*
NOT ADDRESSED   remote desktop during the session       T-P16A-31
NOT ADDRESSED   the eligibility side of ballot stuffing VP-17 — PACK-15 owns it
NOT ADDRESSED   guardian collusion off-protocol         PACK-16B, ADR-100
NOT ADDRESSED   the parameter family's standing         VO-08 — OPEN
NOT ADDRESSED   post-quantum adversaries                PACK-16B agility model
NOT ADDRESSED   supply chain below the published build  PACK-16D, PACK-17
```

| ID          | Rule                                                                                                                                                                                     |
| ----------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `T-P16C-36` | **Nothing in this list is claimed to be small.** Each is a real limit of the design, each is published, and several are reasons the electronic channel is not the only channel (`CB-07`) |
| `T-P16C-37` | **`VO-08` is not owned by this round and is not closed, narrowed or re-owned here** (`SB-06`). PACK-16C neither alters nor claims approval of the parameter family                       |

---

## 7. Counts

```text
PACK-16A threats inherited unchanged                     42
PACK-16C identifiers issued                              65   T-P16C-00 … T-P16C-64
   of which THREATS                                      57   §1  8 · §2  7 · §3  9
                                                              §3A 10 · §3B 12
                                                              §4  5 · §5  6
   of which RULES                                         8   T-P16C-00, 36, 37, 38,
                                                               49, 50, 63, 64
Inherited threats removed, renumbered or downgraded       0
PACK-16C threats fully solved                             0
PACK-16C threats explicitly unsolved and stated          14
   T-P16C-01, 06, 08, 09, 10, 15, 21, 28, 30, 43, 46,
   57, 58, 62
Threats CLOSED by the turnout correction                  1
   T-P16C-03 — the board-side turnout leak
Threats CLOSED by the capacity correction                 1
   T-P16C-51 — unbounded spoiled-ballot batch exhaustion
Threat classes declared out of scope                      8   §6
```

| ID          | Rule                                                                                                                                                                                                                                                                                                                  |
| ----------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `T-P16C-38` | **"Fully solved" is zero, and that is the honest figure.** Every row in §1–§5 has a residual column with something in it — including `T-P16C-03`, whose board-side leak is closed while network-layer observation is not. A threat model whose mitigations close every row is describing a system that does not exist |

---

## 8. What this document does not decide

```text
Transaction mechanism for T-P16C-25 / T-P16C-26   → OD-P16C-01, PACK-16D
External witness ecosystem for T-P16C-16           → OD-P16C-12, PACK-17
Cover-leaf randomness quality for T-P16C-45         → PACK-16D, RB-16C-10
Reservation hygiene for T-P16C-57                    → PACK-16D, RB-16C-13
Capacity partition sizing for T-P16C-53              → OD-P16C-10, GOVERNANCE
Interval choice for T-P16C-46                        → OD-P16C-10, GOVERNANCE
Network-layer defences                              → PACK-17, unsolved
Alternative channel for coercion cases              → OD-P16A-09, GOVERNANCE
Supply-chain assurance below the build              → PACK-16D, PACK-17
```

**SPECIFIED. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY. NOT LEGALLY
ACTIVATED.**
