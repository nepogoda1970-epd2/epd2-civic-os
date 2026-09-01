# PACK-16C — Event Catalog

**Round:** PACK-16C — Casting, Receipt, Verification Client, Bulletin Board and Election Record. **Specification and ADR only. No code. No cryptographic implementation. Not implemented. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-101`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

**No event is implemented in this round.** No event class, no handler, no
schema and no test is added. The event stream this round describes is the
one PACK-16D must build, with its privacy boundaries fixed now.

---

## 0. The rule that shapes every event

```text
An event stream is a correlation surface with a nice name.

Every event below is written so that possessing the ENTIRE stream
tells an observer nothing about who voted for what. Where an event
would carry a correlating field, the field is absent — not redacted,
not hashed, not tokenised. Absent.
```

| ID      | Rule                                                                                                                                                         |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `EV-01` | **No event carries an identity, a credential, a capability, a ballot plaintext, a nonce, or an exact timestamp** (`PM-*`)                                    |
| `EV-02` | **No event carries two fields that, joined, would link a person to a ballot** — the prohibition is on the pair, not on either field (`PM-08`)                |
| `EV-03` | **Hashing is not anonymisation.** A hashed capability reference in an event is a capability reference. No event carries a derived form of a prohibited field |
| `EV-04` | **An event that exists only because it might be useful for debugging is not specified.** Every event below has a named consumer                              |

---

## 1. Casting-side events — internal, never published per ballot

| ID       | Event                           | Emitted when                           | Fields                                                             | Consumer                       |
| -------- | ------------------------------- | -------------------------------------- | ------------------------------------------------------------------ | ------------------------------ |
| `EV-10`  | `ballot.submission_received`    | An envelope arrives                    | context reference, envelope digest, granular time                  | operations                     |
| `EV-11`  | `ballot.validation_failed`      | Any stage 1–18 fails                   | context reference, reason code, stage, granular time               | operations, aggregate counters |
| `EV-12`  | `ballot.validated`              | Stages 1–18 all pass                   | context reference, envelope digest, granular time                  | pipeline                       |
| `EV-13`  | `ballot.acceptance_committed`   | The atomic boundary commits            | context reference, ballot reference, granular time                 | board scheduler                |
| `EV-14`  | `ballot.acceptance_rolled_back` | The boundary rolls back                | context reference, reason code, granular time                      | operations, `FM-16C-14`        |
| `EV-16`  | `receipt.issued`                | A receipt is produced                  | context reference, granular time                                   | operations                     |
| `EV-17`  | `receipt.generation_failed`     | It is not                              | context reference, reason code                                     | operations, `FM-16C-17`        |
| `EV-18`  | `challenge.public_submitted`    | A public evidentiary challenge arrives | context reference, artefact digest, granular time                  | pipeline                       |
| `EV-19`  | `challenge.public_accepted`     | Its atomic boundary commits            | context reference, artefact reference, batch window, granular time | board scheduler                |
| `EV-19a` | `challenge.public_rejected`     | Any stage or the boundary rejects it   | context reference, reason code, granular time                      | operations, `FM-16C-32`        |

| ID      | Rule                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `EV-70` | **`challenge.local_completed` is a CLIENT-LOCAL outcome and is never emitted as an event, a telemetry signal, a metric or a log line.** It never leaves the device, in production or in any diagnostic mode (`CH-42`, `API-19`). An implementation that transmits it has defeated the local tier's whole purpose                                                                                                                                                                                                                                                               |
| `EV-71` | **The capability-side half of each atomic boundary is NOT AN EVENT.** Capability consumption on the cast path and public-challenge entitlement consumption on the challenge path are **internal transactional state changes**, atomic with acceptance, recorded only as privacy-restricted audit evidence inside the bounded context. Neither is emitted as a domain event, an integration event, a metric or a log line (`EV-74`)                                                                                                                                             |
| `EV-72` | **No event carries a remaining-entitlement count, an occupancy figure, a reserved-slot count or a queue depth** (`CN-37`, `TC-81`)                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| `EV-73` | **`EV-30c` carries no figure at all.** It names the incident class and the affected scope; how many submissions were unserved is not in it (`FMR-16` lineage, `RN-16C-32`)                                                                                                                                                                                                                                                                                                                                                                                                     |
| `EV-05` | **Only the artefact-side half of each atomic boundary is an event.** `EV-13` on the cast path and `EV-19` on the challenge path are emitted; the capability-side half is not emitted at all (`EV-71`). Neither emitted event carries a capability reference, and there is no counterpart event to correlate one with (`DM-10`)                                                                                                                                                                                                                                                 |
| `EV-74` | **The entitlement and consumption transitions are internal parts of their atomic transactions.** Their audit evidence may carry **only** `election_context_id`, the transaction outcome, a `reason_code`, a coarse time bucket, `schema_version`, and a bounded-context-local transaction reference. It may **not** carry a continuation capability, a capability reference, a credential, an identity, a challenge artefact's public reference, a final cast ballot reference, a shared trace identifier, a cross-context correlation identifier, or an exact voter timestamp |
| `EV-75` | **Any technical object that internal transaction evidence requires is non-exportable, bounded-context-local, never placed on an event bus, never in the election record, never available to identity or credential services, and deleted or retained under a short governed retention policy**                                                                                                                                                                                                                                                                                 |
| `EV-76` | **A renamed replacement is not a fix.** An event such as `challenge.public_entitlement_transition_completed` that still crosses a bus is the same defect under another name and is prohibited (`EV-71`)                                                                                                                                                                                                                                                                                                                                                                        |
| `EV-78` | **`EV-15` and `EV-19b` are retired identifiers, not missing events.** They previously named `capability.consumed` and `challenge.public_entitlement_consumed`, each carrying a capability reference in its payload. Both were **deleted** by the event-privacy correction. The identifiers are **not reused and not renumbered**, and the gap must not be read as an omission                                                                                                                                                                                                  |
| `EV-77` | **The rules in §0 bind every event in this catalogue without exception**, including `challenge.public_submitted`, `challenge.public_accepted`, `challenge.public_rejected` and `challenge.public_published`: no continuation capability, no capability reference, no credential ID, no identity, no shared session identifier and no cross-domain trace identifier appears in any payload (`EV-01`, `EV-03`)                                                                                                                                                                   |
| `EV-06` | **No trace, span or correlation identifier spans the atomic boundary.** Distributed tracing that joins the submission to the consumption reconstructs exactly the link the design removes, and is prohibited                                                                                                                                                                                                                                                                                                                                                                   |
| `EV-07` | **`EV-11` is counted in aggregate and published only after closure** (`VP-13`, `API-29`)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |

---

## 2. Board and publication events — published

| ID       | Event                                  | Emitted when                                                           | Public?                               |
| -------- | -------------------------------------- | ---------------------------------------------------------------------- | ------------------------------------- |
| `EV-20`  | `board.batch_commitment_published`     | A `sealed_batch_commitment` is published at its scheduled window       | **yes**                               |
| `EV-21`  | `board.checkpoint_published`           | A checkpoint is signed and published                                   | **yes**                               |
| `EV-22`  | `board.mirror_cosigned`                | A mirror co-signs a checkpoint                                         | **yes**                               |
| `EV-23`  | `board.publication_delayed`            | A batch is behind schedule, inside the deadline                        | **yes**                               |
| `EV-24`  | `board.publication_deadline_missed`    | The deadline passes                                                    | **yes** — `publication_disputed`      |
| `EV-25`  | `board.publication_recovered`          | A disputed publication is remedied                                     | **yes**                               |
| `EV-26`  | `board.inconsistency_detected`         | A mirror, verifier or witness reports divergence                       | **yes, immediately**                  |
| `EV-27`  | `board.signing_key_rotated`            | A signing key changes                                                  | **yes, in advance where possible**    |
| `EV-28`  | `board.batch_commitment_missed`        | A scheduled window passed with no commitment                           | **yes, immediately, without a count** |
| `EV-29`  | `board.batch_opening_published`        | A `sealed_batch_opening` is published at closure                       | **yes**                               |
| `EV-30a` | `board.batch_reconciliation_published` | The `batch_reconciliation_record` is published                         | **yes**                               |
| `EV-30b` | `challenge.public_published`           | A public evidentiary challenge's opening is published at closure       | **yes**                               |
| `EV-30c` | `election.capacity_incident_declared`  | Capacity is constrained and publication-bearing submissions are paused | **yes, immediately, with no figure**  |

| ID      | Rule                                                                                                                                                                                                                                                                                              |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `EV-08` | **`EV-23` through `EV-26` are published as they occur and are never held pending review.** A publication failure that is investigated privately first is indistinguishable from one that is concealed (`RN-16C-19`)                                                                               |
| `EV-09` | **`EV-26` is the highest-severity board event** and blocks certification until resolved (`D-02`, `FM-P16A-10`)                                                                                                                                                                                    |
| `EV-60` | **`EV-20` carries no size, no occupancy and no count.** It names the window and the commitment root, both of which are constant-shaped whatever the turnout (`TC-29`, `TC-33`). **This corrects the first candidate, in which `EV-20` carried the batch's size and was itself a turnout channel** |
| `EV-68` | **`EV-28` never states how many ballots the missed window should have held** (`FMR-16`). It names the window and nothing else                                                                                                                                                                     |
| `EV-69` | **`EV-29` and `EV-30a` exist only at closure.** An occurrence before the closure checkpoint is an incident, not an early publication (`BE-28`)                                                                                                                                                    |

---

## 3. Election-lifecycle events — published

| ID      | Event                           | Emitted when                                    |
| ------- | ------------------------------- | ----------------------------------------------- |
| `EV-30` | `election.manifest_published`   | Before opening                                  |
| `EV-31` | `election.parameters_published` | Before opening                                  |
| `EV-32` | `election.ceremony_completed`   | Before opening, from PACK-16B                   |
| `EV-33` | `election.joint_key_published`  | Before opening                                  |
| `EV-34` | `election.voting_opened`        | At the opening checkpoint                       |
| `EV-35` | `election.voting_closed`        | At the closure checkpoint                       |
| `EV-36` | `election.eligible_set_fixed`   | With the closure checkpoint                     |
| `EV-37` | `election.tally_published`      | After decryption                                |
| `EV-38` | `election.result_published`     | With the proofs                                 |
| `EV-39` | `election.ballot_excluded`      | With a published ground and Auditor concurrence |
| `EV-40` | `election.record_archived`      | At the archive checkpoint                       |

| ID      | Rule                                                                                                                                                                 |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `EV-61` | **No event between `EV-34` and `EV-35` carries a count of any kind** (`TC-07`). The voting period emits batch and checkpoint events and nothing that aggregates them |
| `EV-62` | **`EV-39` never occurs without a published ground, a reason code and Auditor concurrence** (`BL-04`, `RN-16C-17`)                                                    |

---

## 4. Verification-side events

| ID      | Event                                 | Emitted when                               | Fields                                                                |
| ------- | ------------------------------------- | ------------------------------------------ | --------------------------------------------------------------------- |
| `EV-50` | `verification.report_published`       | An independent verifier publishes a result | verifier identity, version, result, check list, what it did not check |
| `EV-51` | `verification.client_build_published` | A Verification Client build is released    | build digest, source reference, attestation                           |

| ID      | Rule                                                                                                                        |
| ------- | --------------------------------------------------------------------------------------------------------------------------- |
| `EV-63` | **There is no lookup event.** A voter checking their confirmation code emits nothing, anywhere, ever (`PM-*` #27, `API-30`) |
| `EV-64` | **`EV-50` always carries the "what it did not check" list** (`IV-11`)                                                       |

---

## 5. Events that must not exist

```text
MUST NOT EXIST   voter.voted
MUST NOT EXIST   participation.recorded
MUST NOT EXIST   ballot.linked_to_capability
MUST NOT EXIST   turnout.updated   (or any live counter event)
MUST NOT EXIST   board.batch_occupancy  (or any event carrying a leaf
                 count, an occupancy figure or a leaf class before closure)
MUST NOT EXIST   challenge.local_completed as a transmitted event
MUST NOT EXIST   capability.entitlement_remaining (or any event carrying
                 a residual entitlement count)
MUST NOT EXIST   reservation.slots_remaining (or any capacity gauge
                 reachable from outside the operating principal)
MUST NOT EXIST   ballot.decrypted before the closure checkpoint
MUST NOT EXIST   verification.code_looked_up
MUST NOT EXIST   any event carrying a ballot plaintext or a nonce of a
                 cast ballot
MUST NOT EXIST   any event spanning the atomic boundary with a shared
                 correlation identifier
MUST NOT EXIST   capability.consumed  (or any event announcing that a
                 continuation capability was spent)
MUST NOT EXIST   challenge.public_entitlement_consumed  (or any renamed
                 equivalent that still crosses an event bus)
MUST NOT EXIST   any event payload containing a continuation capability,
                 a capability reference, or a derived form of either
```

| ID      | Rule                                                                                                                                                                                                |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `EV-65` | **These eight are checkable absences**, and PACK-16D must be able to demonstrate that no event class, no audit-log writer and no telemetry exporter produces any of them                            |
| `EV-66` | **Adding an event in PACK-16D requires a row in `PACK-16C-PRIVACY-AND-METADATA-MATRIX.md` and an acceptance row.** An event introduced without both is a defect regardless of its content (`PM-12`) |

---

## 6. Retention

| Stream                                                     | Retention                                                                                                            | Why                                                |
| ---------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------- |
| Casting-side internal (`EV-10`…`EV-19a`)                   | shortest operational period, published per context                                                                   | correlation risk decays only when the data is gone |
| Capability consumption and entitlement transition          | **not an event stream at all** — internal transactional audit evidence only, under a short governed retention policy | `EV-71`, `EV-74`, `EV-75`                          |
| Board and publication (`EV-20`…`EV-29`, `EV-30a`…`EV-30c`) | **permanent, in the record**                                                                                         | they are the append-only evidence                  |
| Election lifecycle (`EV-30`…`EV-40`)                       | **permanent, in the record**                                                                                         | same                                               |
| Verification (`EV-50`, `EV-51`)                            | **permanent, in the record**                                                                                         | `IV-10`                                            |

| ID      | Rule                                                                                                                                                                                                                                 |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `EV-67` | **Permanent retention applies only to streams that carry no correlating field.** Nothing in §1 is retained permanently, and nothing in §2–§4 needs to be redacted later, because neither ever held a correlating field to begin with |

---

## 7. What this document does not decide

```text
Event schema, transport and storage         → PACK-16D
Concrete retention periods                   → GOVERNANCE, per context
Observability tooling                         → PACK-16D, within EV-06
Audit-stream field definitions                → PACK-16D
```

**SPECIFIED. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY. NOT LEGALLY
ACTIVATED.**
