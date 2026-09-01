# PACK-16D — Fault Injection Matrix

**Round:** PACK-16D — Cryptographic Implementation Architecture, Reference
Components, Atomic Persistence, Test Vectors and Verification Harness.
**Reference implementation. Not production code. Not certified. Not a PASS.**
**Repository version:** unchanged at `0.16.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-102`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 1. Scope

Eleven named fault points, declared as
`FaultPoint` in
`services/voting-service/src/epd2_voting_service/reference/testing/faults.py`
and exercised by
`services/voting-service/tests/reference/test_fault_injection.py`
(22 tests).

| ID      | Rule                                                                                                                                                                                                                                                                                                                             |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `FI-01` | **A fault point is a place a crash can happen, chosen because the state it could leave behind is interesting.** Arming one raises `InjectedFault` at exactly that line; the test then asserts what survived                                                                                                                      |
| `FI-02` | **The eleven points split into two kinds, and the correct property differs between them.** Six are inside a submission transaction and must leave the store byte-identical to its pre-call state. Five are outside any transaction, where rollback is not available and the correct property is **recoverability**, not rollback |
| `FI-03` | `test_all_eleven_fault_points_are_declared` asserts `len(list(FaultPoint)) == 11` and pins the exact set of eleven string values. A point added, removed or renamed fails this test before it can silently change what the matrix covers                                                                                         |
| `FI-04` | `test_a_fault_point_fires_once_and_disarms` asserts a point fires once and then does not fire again — `trip()` discards the point from `armed` before raising. That makes the recovery half of every test meaningful: the retry runs against an un-armed system                                                                  |
| `FI-05` | `test_an_unarmed_injector_is_transparent` passes a constructed but unarmed `FaultInjector` through a full cast and asserts the result is `counted is True`. A hook that is present must not change any outcome                                                                                                                   |

## 2. The six transactional points

`ReferenceStore.transaction()` snapshots eight maps — `continuations`,
`idempotency`, `accepted_ballots`, `spoiled_ballots`, `reservations`,
`slot_owner`, `obligations` and a deep copy of `outbox.rows` — and restores
every one of them on **any** `BaseException`, `InjectedFault` included.

The two transactions place the points in slightly different order, and the
matrix covers both: a cast reserves, then persists the ballot, then mutates
the entitlement; a public challenge reserves, then mutates the entitlement,
then persists the ballot.

| ID      | Fault point                   | Armed at                                                                                                            | What must be true after the fault                                                                              |
| ------- | ----------------------------- | ------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| `FI-06` | `after_capability_validation` | Immediately after the capability is found and its entitlement checked, before any proof work                        | Nothing was mutated. The capability is still unspent                                                           |
| `FI-07` | `after_proof_validation`      | After `verify_ballot_proofs()` — and, for a challenge, `verify_challenge_opening()` — before the duplicate-id check | Nothing was mutated. Proof verification is pure                                                                |
| `FI-08` | `after_slot_reservation`      | After `reserve_leaf()` has taken a slot by compare-and-set                                                          | The reservation and its `slot_owner` entry are gone. No slot is held by a submission that did not commit       |
| `FI-09` | `after_ballot_persistence`    | After the envelope's canonical bytes are written to `accepted_ballots` (cast) or `spoiled_ballots` (challenge)      | The artefact is gone. A ballot that did not commit was never stored                                            |
| `FI-10` | `after_entitlement_mutation`  | After `consume_for_cast()` (cast) or `spend_public_challenge()` (challenge) has replaced the continuation state     | The prior continuation state is restored. **A capability is never spent by a submission that does not commit** |
| `FI-11` | `before_transaction_commit`   | After the idempotency record is written and the result object is built, on the last line inside the transaction     | Everything above, including the idempotency record. A crash one line before returning leaves no trace          |

| ID      | Rule                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `FI-12` | **The assertion is a whole-store equality, not a spot check.** `_snapshot()` captures all eight maps (values by `repr` where the object is mutable) before the call, and the test asserts `_snapshot(fixture) == before` with the message `state leaked past <point>`. A mutation the author did not anticipate fails the test as surely as one they did                                                                                  |
| `FI-13` | **Every transactional point is tested against both transactions.** `test_cast_rolls_back_completely_at_every_transactional_point` and `test_public_challenge_rolls_back_completely` are each parametrised over `TRANSACTIONAL_POINTS` — 12 tests                                                                                                                                                                                          |
| `FI-14` | **Rollback alone is not enough; the retry must succeed.** Both tests re-issue the identical request with no hook after the fault. The cast retry asserts `result.counted is True`; the challenge retry asserts `result.counted is False` and then asserts `cast_entitlement_available is True` — the cast entitlement survived both the fault and the retry                                                                               |
| `FI-15` | The same six points are exercised again end to end by `test_e2e_05_crash_before_commit`, which asserts the specific post-conditions `cast_entitlement_available is True` (`"capability was consumed by a crash"`), `accepted_ballots == {}`, `slot_owner == {}` (`"a leaf slot leaked"`), `outbox.rows == []` and `idempotency == {}`, then asserts the retry lands on leaf index 0 — the same first free slot as if nothing had happened |

## 3. The five points outside a transaction

These are the honest half of the matrix. At each of them a rollback is
either impossible or meaningless, so the test asserts what the fault
actually leaves behind and that the system can go forward from there.

| ID      | Fault point                 | Armed at                                                                                                                                                              | What it actually leaves behind, and why that is correct                                                                                                                                                                                                                                                                                                                                                                           |
| ------- | --------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `FI-16` | `after_board_append`        | In `BulletinBoard.append()`, after the entry has been appended to `entries`                                                                                           | **The entry is durable and the tree grew.** Append is append-only and not transactional: un-appending would be a rollback of a public log, which is the thing a bulletin board must never do. The property asserted is internal consistency going forward — `len(board.entries) == 2`, the root changed, and the next checkpoint covers the new entry (`tree_size == 2`, `checkpoint.root == board.root()`) rather than hiding it |
| `FI-17` | `before_checkpoint_signing` | The first line of `BulletinBoard.publish_checkpoint()`, before the previous hash is read and before the **Ed25519** signature over the checkpoint payload is computed | **No checkpoint at all.** `board.checkpoints == []`, with the message `an unsigned checkpoint was published` if it is not. A partially built or unsigned checkpoint must never reach the list — which matters more now that the signature is what a third party checks. The retry publishes exactly one checkpoint, at sequence 0, chained from the genesis value of 32 zero bytes                                                |
| `FI-18` | `before_outbox_publish`     | In `dispatch_outbox()`, before the row is marked `DISPATCHED`                                                                                                         | **The obligation stays `PENDING`.** `len(outbox.pending()) == 1`, and the next sweep dispatches exactly one row. Nothing was published and nothing was lost; the publication obligation is still owed                                                                                                                                                                                                                             |
| `FI-19` | `after_commit`              | In `dispatch_outbox()`, after the row is marked `DISPATCHED` and before it is added to the returned list                                                              | **The row is `DISPATCHED` and is not re-dispatched.** `states[id] is ObligationState.DISPATCHED` and a second `dispatch_outbox(store)` returns `[]`. Delivery is at-least-once by design; duplicate suppression is the board's job — one obligation id, one entry — not the outbox's                                                                                                                                              |
| `FI-20` | `during_record_export`      | The first line of `export_record()`, before `record.canonical_bytes()` is called                                                                                      | **Nothing.** Export is a pure function of the record, so a crash here loses no state. The test asserts `export_record(closed.record) == closed.record.canonical_bytes()` on the retry: the same bytes as if nothing had happened. The fault point exists so that purity can be demonstrated rather than asserted                                                                                                                  |

| ID      | Rule                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `FI-21` | **`FI-16` is the point where rollback is refused on purpose.** A test that asserted the entry disappeared would be asserting that a public append-only log can retract an entry. What the board owes after a crash is that its next checkpoint tells the truth about what it holds                                                                                                                                                                                                                                                                                                                                                                                                  |
| `FI-22` | **`FI-18` and `FI-19` are the two halves of the outbox's crash window**, and the pair is what makes at-least-once delivery inspectable: a crash before the mark leaves the row pending and it is retried; a crash after the mark leaves it dispatched and it is not. Neither ordering loses the obligation, and neither publishes it twice. The same two points are asserted again as races `C-08` and `C-09` in the concurrency matrix, and `FI-18` again by `test_e2e_06_crash_after_commit_before_publication`                                                                                                                                                                   |
| `FI-23` | **`before_outbox_publish` has exactly one call site**, in `dispatch_outbox()`. It used to have a second inside `seal_batch()`, which no test armed and where the label was wrong anyway — sealing is not an outbox publish — so that call site was removed rather than given a test it did not deserve. `test_the_only_other_fault_point_call_site_is_covered` parses every two-argument `trip()` call in production code with `ast`, asserts the set of tripped points is exactly `FaultPoint`, and pins the per-point call-site counts: one for `before_outbox_publish`, two for `after_capability_validation` (the cast and the challenge). An unreviewed new call site fails it |

## 4. The test-only guarantee

The injector must never be reachable from a running system. Three
structural facts make that true, and one test proves the third.

| ID      | Rule                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `FI-24` | **Production code depends on a protocol, not on the injector.** `reference/hooks.py` declares `FaultHook`, a `runtime_checkable` `Protocol` with a single method `trip(point: str) -> None`, and a module function `trip(hook, point)` that is a no-op when `hook is None`. Every production call site is `trip(fault_hook, "<point>")`                                                                                                                                                              |
| `FI-25` | **The hook's point is typed `str`, not `FaultPoint`.** That is why no production module has to import the test enum. `FaultPoint` is a `StrEnum`, so `FaultInjector.trip()` normalises the plain string back to the enum at one place instead of at every call site                                                                                                                                                                                                                                  |
| `FI-26` | **A hook can only arrive by being passed explicitly into a call.** There is no global registry, no module-level singleton and no environment switch. `fault_hook` is a keyword-only parameter defaulting to `None` on `submit_cast_ballot`, `submit_public_challenge`, `dispatch_outbox`, `BulletinBoard.append`, `BulletinBoard.publish_checkpoint` and `export_record`. `seal_batch()` no longer takes one (`FI-23`). A deployed system that never passes one cannot have a fault injected into it |
| `FI-27` | **The guarantee is checked, not asserted.** `test_production_modules_do_not_import_the_injector` walks `rglob("*.py")` over the whole `reference/` package, skips any path with `testing` in its parts, parses every remaining module with `ast`, and flags any `Import` or `ImportFrom` node naming `testing.faults`, `FaultInjector`, `InjectedFault` or `FaultPoint`. The assertion is `offenders == []` and the failure message names the file and the line number                               |
| `FI-28` | **The check is over the parsed syntax tree, which is what it used to lack.** It was a substring scan over lines beginning `import` or `from`; it is now an `ast` parse, matching the verifier-boundary check, so it sees an import wherever it appears — including inside a function body. It remains a floor rather than a proof: an injector reached through a fully dynamic mechanism such as `importlib` with a computed name is still outside what it can see                                   |
| `FI-29` | `rglob` means a new module added under `reference/` is covered without anyone remembering to add it, and the `testing` skip is by path component, so a new module under `reference/testing/` is correctly exempt                                                                                                                                                                                                                                                                                     |

## 5. What this matrix does not establish

Stated in the body, not in a footnote:

- **These are eleven chosen points, not an exhaustive crash model.** A
  crash can occur anywhere; the matrix covers the eleven places where the
  surviving state was judged interesting. No claim of exhaustiveness is
  made.
- **The rollback evidence is the reference in-memory store's.**
  `transaction()` is a snapshot-and-restore scope under a re-entrant lock.
  Equivalent atomicity from a production datastore is `OD-P16D-04` and a
  PACK-17 obligation.
- **No durability claim is made.** The reference store is in memory. Every
  statement above is about state consistency after an exception, not about
  survival of a process death, a disk loss or a `fsync` boundary.
- **`FI-23` was a coverage gap and is closed.** The
  `before_outbox_publish` call site inside `seal_batch()` was removed, and
  an `ast`-based guard now fails if an unreviewed `trip()` call site
  appears.
- **`FI-28` is the bound on the test-only guarantee.** The import check is
  an `ast` parse and still cannot see a fully dynamic import.

## 6. What this document does not decide

```text
Atomicity under a production datastore                → OD-P16D-04, PACK-17
Durability, fsync and process-death survival          → PACK-17
The seal_batch fault site (FI-23)                     → removed this round
Exhaustive crash-point enumeration                    → PACK-17
Asymmetric operator signature behind FI-17            → implemented; Ed25519, see
                                                        PACK-16D-CHECKPOINT-SIGNATURE-AND-SIGNER-TRUST-MODEL.md
Key custody for the checkpoint signing seed           → OD-P16D-11, PACK-17
```

**REFERENCE IMPLEMENTATION. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY.
NOT LEGALLY ACTIVATED.**
