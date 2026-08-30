# PACK-16D — Concurrency Test Matrix

**Round:** PACK-16D — Cryptographic Implementation Architecture, Reference
Components, Atomic Persistence, Test Vectors and Verification Harness.
**Reference implementation. Not production code. Not certified. Not a PASS.**
**Repository version:** unchanged at `0.16.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-102`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 1. The limitation, before the evidence

`services/voting-service/tests/reference/test_concurrency.py` is 87 tests:
nine named races from §42, seven of them parametrised over `REPEATS = 12`,
two crash-ordering tests run once, and one leakage test.

The limitation is stated here rather than at the end, because a reader who
takes a green run as deployment evidence has drawn the wrong conclusion.

| ID      | Rule                                                                                                                                                                                                                                                                                |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CR-01` | **This evidence covers the reference in-memory store only.** `ReferenceStore.transaction()` is a `threading.RLock` around a snapshot-and-restore scope. The races run real OS threads against it and prove the _logic_ is race-free under the serialisation that lock provides      |
| `CR-02` | **It says nothing about a production datastore.** There, the same invariants must come from row-level locking or a serialisable isolation level, and neither is exercised by anything in this suite. A green run here is evidence about this implementation, not about a deployment |
| `CR-03` | This is open decision **`OD-P16D-04`** and a **PACK-17 obligation**. Demonstrating the invariants under a real datastore's isolation level is not done, is not partially done, and must not be read into these results                                                              |
| `CR-04` | The same limitation is written into the module docstring of `test_concurrency.py`, in the same position — first — so it is met by a reader of the code before the results                                                                                                           |

## 2. The barrier technique

The races contend because they are made to. Without a barrier, threads
started in a loop routinely run to completion one after another, and a
suite of "races" that never overlap will pass against an implementation
with no locking at all.

```python
def _race(calls):
    barrier = threading.Barrier(len(calls))
    ...
    def runner(index):
        barrier.wait()
        try:
            results[index] = (calls[index](), None)
        except BaseException as exc:
            results[index] = (None, exc)
```

| ID      | Rule                                                                                                                                                                                                                                                                                                          |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CR-05` | **`threading.Barrier(len(calls))` releases every thread at the same instant.** Each thread is constructed and started first, then blocks in `barrier.wait()`; the last thread to arrive releases all of them. The contended window is the whole call, not the tail of it                                      |
| `CR-06` | **The race outcome is captured, never hidden.** `runner` catches `BaseException` and stores it as the thread's result. An exception raised in a racing thread is the evidence, so it is returned to the test rather than being swallowed by the thread's default handler and reported as a pass               |
| `CR-07` | **A deadlock fails the test rather than hanging the suite.** Each `thread.join(timeout=30)` is followed by `assert not thread.is_alive(), "a racing thread deadlocked"`                                                                                                                                       |
| `CR-08` | **Repeats are pytest parameters, not an inner loop.** `@pytest.mark.parametrize("repeat", range(REPEATS))` with `REPEATS = 12` gives each repetition its own fresh fixture, its own test id and its own failure report. An intermittent failure names the repeat index instead of appearing as one flaky test |
| `CR-09` | Repetition mitigates scheduling luck; it does not eliminate it. Twelve repeats of a two-thread race is a sampling of interleavings, not a proof of their exhaustion. §5 records what that cost this round                                                                                                     |

## 3. The nine races

Seven races are parametrised over 12 repeats (84 tests); `C-08` and `C-09`
are deterministic crash-ordering tests using an armed fault point and run
once each; `test_no_capability_to_ballot_leakage_in_any_persisted_row`
discharges §42's fifth expectation over every persisted row. 87 in total.

| ID      | Race                                                      | Threads                                                                                        | Repeats | Test                                                   |
| ------- | --------------------------------------------------------- | ---------------------------------------------------------------------------------------------- | ------- | ------------------------------------------------------ |
| `CR-10` | **C-01** two simultaneous cast requests on one capability | 2 casts, one capability, distinct keys                                                         | 12      | `test_c01_two_simultaneous_casts_on_one_capability`    |
| `CR-11` | **C-02** two simultaneous public challenges               | 2 challenges, one capability, distinct keys                                                    | 12      | `test_c02_two_simultaneous_public_challenges`          |
| `CR-12` | **C-03** cast and public challenge concurrently           | 1 cast + 1 challenge, one capability                                                           | 12      | `test_c03_cast_and_public_challenge_concurrently`      |
| `CR-13` | **C-04** same idempotency key concurrently                | 3 casts sharing the key `same`: two identical, one different request under a second capability | 12      | `test_c04_same_idempotency_key_concurrently`           |
| `CR-14` | **C-05** two reservations for the same slot               | 2 casts, distinct capabilities, fixture C (one cast-reserved slot, no shared reserve)          | 12      | `test_c05_two_reservations_for_the_same_slot`          |
| `CR-15` | **C-06** batch sealing during reservation                 | 1 cast racing `seal_batch()`                                                                   | 12      | `test_c06_batch_sealing_during_reservation`            |
| `CR-16` | **C-07** publication worker retry                         | 4 concurrent `dispatch_outbox()` sweeps                                                        | 12      | `test_c07_publication_worker_retry`                    |
| `CR-17` | **C-08** crash after persistence, before outbox dispatch  | 1 thread; `BEFORE_OUTBOX_PUBLISH` armed                                                        | 1       | `test_c08_crash_after_persistence_before_dispatch`     |
| `CR-18` | **C-09** crash after dispatch, before acknowledgement     | 1 thread; `AFTER_COMMIT` armed                                                                 | 1       | `test_c09_crash_after_dispatch_before_acknowledgement` |

| ID      | Rule                                                                                                                                                                                                                                                                                                               |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `CR-19` | **C-05 uses fixture C deliberately.** Fixture C declares exactly one cast-reserved slot and no shared reserve, so the two threads are guaranteed to contend for the same slot rather than merely for the lock. A race for a resource that is not scarce is not a race                                              |
| `CR-20` | **C-04's third request is the one that matters.** Two identical requests may legitimately resolve as one `ACCEPTED` and one `REPLAYED`; the third is a _different_ canonical request under the same key and must fail. This is the case that found defect 1 (§4)                                                   |
| `CR-21` | **C-08 and C-09 are not thread races and are not parametrised.** They are ordering tests: a fault is armed at a named point, the crash is provoked, and the test asserts what survived. They belong to §42 because the property under test is the same one — an obligation is never lost and never published twice |

## 4. The five §42 expectations, mapped to assertions

| ID      | Expectation                               | Where it is asserted                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| ------- | ----------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CR-22` | **No double acceptance**                  | `C-01`: `len(accepted) == 1, "double acceptance"` and `len(store.accepted_ballots) == 1`. `C-02`: `len(accepted) == 1` and `len(store.spoiled_ballots) == 1`. `C-03`: `store.accepted_ballots.keys() == {cast.ballot_id}`. `C-04`: `outcomes.count(Outcome.ACCEPTED) == 1` and `len(store.accepted_ballots) == 1`. `C-05`: `len(accepted) == 1`. `C-06`: at most one artefact reference in the sealed batch, and no duplicate                                                                                                                                                                        |
| `CR-23` | **No double entitlement consumption**     | `C-01`: every loser raises `CastEntitlementExhaustedError`, and `continuations[capability].capability_consumed is True`. `C-02`: every loser raises `PublicChallengeEntitlementExhaustedError`, and the surviving state has `public_challenge_entitlement_available is False` with `cast_entitlement_available is True` — a challenge does not spend the cast. `C-03`: `capability_consumed is True` and `public_challenge_entitlement_available is False` in both orderings. `C-05`: exactly one of the two capabilities still has `cast_entitlement_available` — _a lost race is not a spent vote_ |
| `CR-24` | **No lost publication obligation**        | `C-07`: `ids.count(result.publication_obligation_id) == 1, "obligation dispatched twice"` across four concurrent sweeps, and `store.outbox.pending() == []` afterwards. `C-08`: the pending list still holds exactly the obligation id, the ballot is still in `accepted_ballots`, and a retried `dispatch_outbox` recovers exactly one row. `C-09`: the row is `ObligationState.DISPATCHED`, a second sweep returns `[]`, and `len(store.outbox.rows) == 1` — at-least-once delivery without a duplicate board entry                                                                                |
| `CR-25` | **No orphan committed slot**              | `C-01`: exactly one reservation has `committed`, and `len(store.slot_owner) == 1, "an orphan slot survived"`. `C-03` (cast-wins branch): `challenge.ballot_id not in by_reference` and `len(store.slot_owner) == 1`. `C-05`: `len(store.slot_owner) == 1`. `C-06`: `len(opening.leaves) == batch.capacity` and `opening.recompute_root() == batch.commitment_root` whichever way the race resolved                                                                                                                                                                                                   |
| `CR-26` | **No capability-to-ballot event leakage** | `test_no_capability_to_ballot_leakage_in_any_persisted_row`: after one challenge and one cast on the same capability, the capability string appears in no `LeafReservation`, no `PublicationObligation`, no outbox row, and neither in an idempotency key nor an idempotency value; and no `ContinuationState` contains either ballot id. The assertion is `capability not in str(row)` over **every** row, which also catches the string appearing inside a nested field                                                                                                                            |

| ID      | Rule                                                                                                                                                                                                                                                                                                                                                     |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CR-27` | **`C-03` additionally asserts slot-class separation under a race (`TC-75`).** The cast's leaf index is asserted below `plan.cast_reserved_per_batch`; if the challenge won, its leaf index is asserted to differ from the cast's and to be at or above that boundary. A public challenge does not take a cast-reserved slot even when the two are racing |
| `CR-28` | **`CR-26` is a substring assertion and is deliberately blunt.** It fails on a capability that appears in a debug field, a repr or a nested structure. The point is that a persisted row should have no vocabulary for the capability at all                                                                                                              |

## 5. Two things reported honestly

### 5.1 The §17.2 limitation, restated where it applies

`CR-01` to `CR-04` above are not a preamble. The whole of §4's evidence is
conditional on the reference store's re-entrant lock. If the same code ran
against a datastore at read-committed isolation, `CR-22` and `CR-25` would
have to be re-established from that datastore's guarantees, and nothing in
this suite would carry over. That work is `OD-P16D-04` and belongs to
PACK-17. No claim is made here about any deployment.

### 5.2 `test_c03` was wrong, and the implementation was right

`test_c03_cast_and_public_challenge_concurrently` originally asserted that
a concurrent cast and public challenge **both always succeed**. It passed
most runs and failed roughly one run in thirty.

| ID      | Finding                                                                                                                                                                                                                                                                                                                                                                                                                    |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CR-29` | **The assertion was wrong, not the code.** A final cast consumes the capability outright: `consume_for_cast()` clears the public-challenge entitlement as well. A public challenge published _after_ the ballot it was meant to test is not evidence of anything, so refusing it is correct behaviour                                                                                                                      |
| `CR-30` | Therefore the outcome is **order-dependent**. If the challenge wins the race, both submissions succeed. If the cast wins, the challenge is correctly refused with `PublicChallengeEntitlementExhaustedError`. The old assertion was true only for the interleaving that happened to occur most of the time                                                                                                                 |
| `CR-31` | The test now asserts the order-dependent outcome: the cast succeeds in **either** ordering (a challenge does not consume the cast entitlement, and nothing can take that away), and the branch on `challenge_error` asserts the full state for each ordering — including, in the cast-wins branch, that `store.spoiled_ballots == {}`, that the challenge's ballot id reserved nothing, and that exactly one slot is owned |
| `CR-32` | **This is recorded because an intermittent failure is the most dangerous kind of test result.** A one-in-thirty failure invites re-running until green. The correct response was to determine which of the test and the implementation was wrong, and it was the test                                                                                                                                                      |

This is item 9 of the corrections listed in the PACK-16D fact sheet §27.
Two further defects found by this suite and its siblings are recorded in
the implementation report: the idempotency check that ran outside the
transaction (found by `C-04`) and the shared reserve that was inferred
rather than declared.

## 6. What this document does not decide

```text
Production datastore isolation level                 → OD-P16D-04, PACK-17
Row-level locking under a real database              → OD-P16D-04, PACK-17
Exhaustive interleaving exploration / model checking → PACK-17
Adversarial search around these races                → OD-P16D-03, PACK-17
Cross-mirror split-view detection                    → OD-P16D-06, PACK-17
```

**REFERENCE IMPLEMENTATION. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY.
NOT LEGALLY ACTIVATED.**
