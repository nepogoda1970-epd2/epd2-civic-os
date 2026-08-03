# PACK-16D — Persistence and Transaction Model

**Round:** PACK-16D — Cryptographic Implementation Architecture, Reference
Components, Atomic Persistence, Test Vectors and Verification Harness.
**Reference implementation. Not production code. Not certified. Not a PASS.**
**Repository version:** unchanged at `0.16.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-102`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 1. Scope

This document specifies the reference persistence engine:
`ReferenceStore` in
`services/voting-service/src/epd2_voting_service/reference/casting/store.py`,
the transactional outbox in `publication/outbox.py`, and the capacity
partition in `publication/capacity.py`.

It exists to demonstrate atomicity, uniqueness, idempotency,
compare-and-set reservation and crash-safe publication **without adding a
database dependency the repository does not already have**. It is an
in-memory store guarded by one re-entrant lock. It is not a production
datastore and §7 states exactly what it therefore does not prove.

## 2. Store shape

```text
ReferenceStore
  continuations     dict[capability_reference          -> ContinuationState]
  idempotency       dict[(context, operation, key)     -> IdempotencyRecord]
  accepted_ballots  dict[ballot_id                     -> canonical bytes]
  spoiled_ballots   dict[ballot_id                     -> canonical bytes]
  reservations      dict[reservation_id                -> LeafReservation]
  slot_owner        dict[(batch_sequence, leaf_index)  -> reservation_id]
  obligations       dict[publication_obligation_id     -> PublicationObligation]
  outbox            Outbox(rows: list[PublicationObligation])
  _lock             threading.RLock
```

| ID | Rule |
| -- | ---- |
| `PT-01` | **The two halves of the acceptance boundary live in separate maps with no shared key** (`DM-10`). `continuations` is keyed by capability reference and holds no ballot reference. `accepted_ballots` and `spoiled_ballots` are keyed by ballot id and hold no capability reference. The join is absent from the data model, not merely forbidden by policy |
| `PT-02` | `ContinuationState` is three booleans — `cast_entitlement_available`, `public_challenge_entitlement_available`, `capability_consumed` — plus an opaque anonymous reference and the election context (`DM-20`). No counter, no identity field, no artefact field. `FORBIDDEN_CAPABILITY_FIELDS` names eleven field names that must never appear on it |
| `PT-03` | `LeafReservation` carries `submission_reference` — a ballot id — and never a capability reference (`DM-21`) |
| `PT-04` | An accepted ballot is stored as the **canonical bytes** of its envelope under the election's parameter set, not as a mutable object graph |
| `PT-05` | `ContinuationState` and `LeafReservation` are frozen dataclasses. State transitions replace the record rather than mutating it, so a rolled-back snapshot restores the exact prior value |
| `PT-06` | `test_no_capability_to_ballot_leakage_in_any_persisted_row` asserts over every reservation, obligation, outbox row, continuation state and idempotency key and value that no capability reference sits beside a ballot id and no ballot id sits inside a continuation state |

## 3. Transaction boundary — snapshot and restore

```python
with store.transaction() as tx:
    ...  # every mutation
```

`transaction()` acquires `_lock`, copies all eight structures, yields the
store, and on **any** `BaseException` restores every copy and re-raises.

| ID | Rule |
| -- | ---- |
| `PT-07` | **The rollback catches `BaseException`, not `Exception`.** A `KeyboardInterrupt` or a `SystemExit` mid-transaction restores the store like any other failure |
| `PT-08` | **All eight structures are snapshotted and all eight are restored.** There is no partially transactional map. The outbox rows are deep-copied rather than shallow-copied, so restoring the list restores the rows themselves |
| `PT-09` | The exception is always re-raised after restore. A rollback never converts a failure into a success or a silent no-op |
| `PT-10` | The lock is re-entrant, so a nested `transaction()` inside an outer one does not deadlock. It is not a savepoint: an exception restores the inner snapshot, re-raises, and the enclosing scope then restores its own older one |
| `PT-11` | **Everything a submission does is inside the boundary**, including the idempotency check (see `PACK-16D-IDEMPOTENCY-AND-REPLAY-MODEL.md` and §6 below) |

Evidence: `test_fault_injection.py` arms each of the six transactional
fault points in turn for both submission paths and asserts the eight-way
snapshot is unchanged after the fault; `test_e2e_05_crash_before_commit`
asserts the same for a cast field by field.

## 4. Compare-and-set leaf reservation

`reserve_leaf()` walks a caller-supplied candidate list of
`(leaf_index, slot_class)` pairs and takes the first index whose
`(batch_sequence, leaf_index)` key is absent from `slot_owner`. Claiming
the key and writing the `LeafReservation` happen under the store lock.

| ID | Rule |
| -- | ---- |
| `PT-12` | **`slot_owner` is the compare-and-set map.** A slot is claimed by inserting `(batch_sequence, leaf_index) -> reservation_id`; a key that is already present is skipped. Two submissions cannot hold one leaf |
| `PT-13` | **Reservation precedes durable acceptance.** There is no path that accepts an artefact and then looks for a slot |
| `PT-14` | `requested_class` selects the reason code on exhaustion — `CastCapacityUnavailableError` or `PublicChallengeReservationUnavailableError` — and never widens the candidate list. The caller has already decided which slots the submission may take |
| `PT-15` | A reservation is created with `committed=False` and replaced by an identical record with `committed=True` at `commit_reservation()`. `release_reservation()` deletes the reservation and frees its `slot_owner` key only if that key still names the same reservation |
| `PT-16` | A failed transaction needs no explicit release: the snapshot restore removes both the reservation and its `slot_owner` key. `test_e2e_05_crash_before_commit` asserts `slot_owner == {}` after a crash, with the message "a leaf slot leaked" |

Evidence: `test_c05_two_reservations_for_the_same_slot` (12 repeats) races
two casts against fixture C's single cast-reserved slot and asserts one
acceptance, `CastCapacityUnavailableError` for the loser,
`len(slot_owner) == 1`, and one capability left unspent.

## 5. Transactional outbox

A publication obligation is written to `store.obligations` and enqueued
in `store.outbox` **inside** the submission transaction. Dispatch happens
later, in `dispatch_outbox()`, outside it.

```text
ObligationState:  PENDING -> DISPATCHED -> ACKNOWLEDGED
```

| ID | Rule |
| -- | ---- |
| `PT-17` | **The obligation is created in the same transaction as the artefact.** An accepted ballot without a pending obligation, or an obligation without an artefact, cannot exist |
| `PT-18` | **Dispatch is at-least-once.** A row is marked `DISPATCHED` only after the publish step returns. A crash between the two leaves the row `PENDING` and the next sweep retries it |
| `PT-19` | **Duplicate suppression is the board's job, not the outbox's** — one obligation id, one entry. The outbox does not attempt exactly-once |
| `PT-20` | The outbox row carries no capability reference. `FORBIDDEN_OUTBOX_FIELDS` names eight prohibited field names, including `capability_reference`, `credential_id`, `voter_id`, `trace_id`, `correlation_id` and `exact_timestamp`. The row's only time value is `coarse_creation_bucket`, set to the batch window id |
| `PT-21` | `Outbox.mark()` raises `KeyError` for an unknown obligation id rather than silently doing nothing |

Evidence:

- `test_before_outbox_publish_leaves_the_obligation_pending` — after a
  crash at `before_outbox_publish` exactly one row is still pending and
  the retry dispatches exactly one.
- `test_after_commit_leaves_the_obligation_dispatched_and_not_repeated` —
  after a crash at `after_commit` the row is `DISPATCHED` and a second
  sweep returns an empty list.
- `test_c07_publication_worker_retry` (12 repeats) — four concurrent
  sweeps dispatch the obligation exactly once, with the failure message
  "obligation dispatched twice", and leave nothing pending.
- `test_c08_crash_after_persistence_before_dispatch` and
  `test_c09_crash_after_dispatch_before_acknowledgement` — the accepted
  ballot survives both, and in the second case the row stays `DISPATCHED`
  and is not re-dispatched, so the board never sees a duplicate entry.
- `test_e2e_06_crash_after_commit_before_publication` — after recovery, a
  further sweep appends nothing to the board.

## 6. Capacity partition

`CapacityPlan.validate()` fails closed. The partition rule is exact.

```text
cast_reserved_per_batch + challenge_reserved_per_batch
                        + shared_reserve_per_batch  ==  primary_capacity
```

| ID | Rule |
| -- | ---- |
| `PT-22` | **The three slot classes partition the primary batch capacity exactly.** A partition that does not sum to `primary_capacity` raises `CapacityPlanInvalidError` (`ELECTION_CAPACITY_PLAN_INVALID`) with the message "an unclassified slot is an adaptive-overflow hole" |
| `PT-23` | `validate()` also requires positive `E`, positive interval count, positive primary capacity, and `total_capacity >= L_max + safety_reserve`. A plan that does not cover `L_max` is not activated |
| `PT-24` | `L_max = E × (K + A)` with `K = 1` and `A = 1`, computed from the maximum number of valid continuation capabilities and **never** from turnout, expected turnout or observed load |
| `PT-25` | `slot_capacity()` returns the declared shared reserve and explicitly discards the `batch_capacity` argument — "the shared reserve is declared, never inferred" |
| `PT-26` | Every unused slot in a sealed batch becomes a cover leaf, so a batch is always exactly `capacity` leaves and its serialised size is independent of occupancy (`TC-33`) |

### 6.1 Defect 2 — the shared reserve was inferred, not declared

This is reported because it is evidence that the harness works, and
because an undisclosed defect makes every other claim in this round
unverifiable.

**The defect.** The first implementation of `_candidate_slots()` computed
the shared reserve as "every slot from `cast_n + chal_n` up to the batch
capacity", ignoring `plan.shared_reserve_per_batch` entirely.

**Why it was wrong.** Any batch larger than the declared partition
silently gained unclassified slots. Those slots behaved as overflow
capacity that no published plan accounted for — adaptive overflow
reintroduced by arithmetic, in the one place the specification most
carefully forbids it. Nothing announced it; a plan and a batch size that
disagreed simply produced extra room.

**How it was found.** `test_e2e_07_capacity_exhaustion`, which uses
fixture C (`primary_capacity = 2`, one cast-reserved slot, one
challenge-reserved slot, `shared_reserve_per_batch = 0`) and requires the
second cast to be rejected with `CastCapacityUnavailableError`.

**How it was fixed.** The implementation was changed, not the test. The
shared reserve is now exactly `plan.shared_reserve_per_batch` slots;
`CapacityPlan.validate()` now requires the exact partition of `PT-22`;
and `_candidate_slots()` carries a comment stating that inferring the
reserve from the capacity would silently reintroduce adaptive overflow
whenever a batch was made larger.

| ID | Rule |
| -- | ---- |
| `PT-27` | **A capacity value that can be inferred will eventually be inferred wrongly.** Every slot in a batch belongs to exactly one declared class, and the plan is rejected at validation if that is not true |

## 7. Limitation — what the concurrency evidence does not cover

Stated in full, because it bounds every atomicity claim in this round.

| ID | Rule |
| -- | ---- |
| `PT-28` | **The concurrency evidence covers this in-memory store's re-entrant lock only.** The race tests run real OS threads against `ReferenceStore`, whose transaction boundary is a `threading.RLock`. That proves the *logic* is race-free under the serialisation this store provides |
| `PT-29` | **It says nothing about a production datastore's isolation level.** There, the same invariants — one acceptance per capability, one owner per leaf, one idempotency record per scope — must come from row-level locking or a serialisable isolation level. Nothing in this round demonstrates that |
| `PT-30` | **Demonstrating it is a PACK-17 obligation** (`OD-P16D-04`). A green run of the reference concurrency suite is evidence about this implementation, not about a deployment. `test_concurrency.py` states this limitation in its module docstring so it cannot be quietly dropped |

## 8. What this document does not decide

```text
Production datastore and isolation level     → OD-P16D-04, PACK-17
Row-level locking strategy                    → PACK-17
Reservation expiry and lease policy           → PACK-17
Durable write-ahead / fsync semantics         → PACK-17
Batch interval and capacity plan values       → GOVERNANCE, PACK-16C
Board-side duplicate suppression detail       → PACK-16C
Cross-mirror split-view detection             → OD-P16D-06, not implemented
```

**REFERENCE IMPLEMENTATION. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY.
NOT LEGALLY ACTIVATED.**
