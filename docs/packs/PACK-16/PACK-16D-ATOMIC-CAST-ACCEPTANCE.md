# PACK-16D — Atomic Cast Acceptance

**Round:** PACK-16D — Cryptographic Implementation Architecture, Reference
Components, Atomic Persistence, Test Vectors and Verification Harness.
**Reference implementation. Not production code. Not certified. Not a PASS.**
**Repository version:** unchanged at `0.16.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-102`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 1. Scope

This document specifies `submit_cast_ballot()` as implemented in
`services/voting-service/src/epd2_voting_service/reference/casting/transactions.py`.
It is the acceptance boundary: the point at which a ballot becomes a
counted artefact, the continuation capability is consumed, a leaf slot is
committed and a publication obligation exists — or at which nothing
happens.

| ID      | Rule                                                                                                                                                                                                                                          |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `AK-01` | **The whole operation is one `store.transaction()` scope.** Either every mutation in §3 is present after the call, or none of them is                                                                                                         |
| `AK-02` | **A cast that does not commit does not consume the capability.** A voter whose submission fails still holds an unspent vote                                                                                                                   |
| `AK-03` | **One capability yields at most one accepted cast** (`A_ACCEPTED_CASTS_PER_CONTINUATION = 1`). `consume_for_cast()` clears the cast entitlement, clears the challenge entitlement and sets `capability_consumed` in one immutable replacement |

## 2. Computed before the transaction opens

```text
scope  = (runtime.manifest.election_context_id, "cast", idempotency_key)
digest = request_digest(envelope.canonical_bytes(runtime.params))
```

Neither value touches the store. The operation literal is `"cast"`, so a
key reused across the two operations addresses two different records.

## 3. The ordered step list

| #   | Step                                                                                                         | Mutates | Fault point                   |
| --- | ------------------------------------------------------------------------------------------------------------ | ------- | ----------------------------- |
| 1   | Open `store.transaction()` — acquire the store lock, snapshot every map                                      | no      | —                             |
| 2   | `_replay(tx, scope, digest)` — idempotency lookup **inside** the transaction                                 | no      | —                             |
| 3   | Load `tx.continuations[capability_reference]`; absent is an error                                            | no      | —                             |
| 4   | Check `cast_entitlement_available` **and** `not capability_consumed`                                         | no      | `after_capability_validation` |
| 5   | `verify_ballot_proofs()` — structure, subgroup membership, selection proofs, accumulation, contest-sum proof | no      | `after_proof_validation`      |
| 6   | Reject if `envelope.ballot_id` is already in `accepted_ballots` or `spoiled_ballots`                         | no      | —                             |
| 7   | `tx.reserve_leaf()` — compare-and-set, cast-reserved slots then shared reserve                               | **yes** | `after_slot_reservation`      |
| 8   | `tx.accepted_ballots[ballot_id] = envelope.canonical_bytes(params)`                                          | **yes** | `after_ballot_persistence`    |
| 9   | `tx.continuations[cap] = state.consume_for_cast()`                                                           | **yes** | `after_entitlement_mutation`  |
| 10  | `tx.commit_reservation(reservation_id)`                                                                      | **yes** | —                             |
| 11  | Build `PublicationObligation`, store it in `tx.obligations`, `tx.outbox.enqueue()` it                        | **yes** | —                             |
| 12  | Build the `SubmissionResult`, deriving the confirmation code from the public ciphertexts and `base_hash`     | no      | —                             |
| 13  | `_record_idempotency(tx, scope, digest, result)`                                                             | **yes** | `before_transaction_commit`   |
| 14  | Return; the context manager exits without an exception and nothing is restored                               | no      | —                             |

| ID      | Rule                                                                                                                                                                                                                                                                                                                                                                    |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `AK-04` | **Steps 2 to 6 are read-only.** The first write is the leaf reservation in step 7                                                                                                                                                                                                                                                                                       |
| `AK-05` | **`consume_for_cast()` runs only after the artefact is durable.** Persistence is step 8; consumption is step 9. There is no ordering in which the capability is spent while the ballot is still absent from the store                                                                                                                                                   |
| `AK-06` | This ordering is the mirror image of the challenge transaction, where the entitlement is spent before the artefact is written. Stated as a design position rather than as something the source comments assert: a consumed capability is terminal, so it is the last state change before commit, whereas a spent challenge entitlement still leaves a usable capability |
| `AK-07` | Both orderings are inside one transaction, so neither is load-bearing for correctness under rollback. The ordering is load-bearing for what a fault-point crash _means_ to a reviewer reading the trace                                                                                                                                                                 |
| `AK-08` | Successful outcome: `Outcome.ACCEPTED`, reason code `acceptance.committed`, `counted = True`                                                                                                                                                                                                                                                                            |
| `AK-09` | The publication obligation is `obl-cast-<ballot_id>` with `artifact_type = "accepted_cast"` and `coarse_creation_bucket` equal to the batch window id. The row carries no capability reference and no finer timestamp (`FORBIDDEN_OUTBOX_FIELDS`)                                                                                                                       |

## 4. What is validated before anything is mutated

| ID      | Step | Content                                                                                                                                                                                                                                                                                                                       |
| ------- | ---- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `AK-10` | 2    | Replay: same digest returns the recorded outcome; different digest is a hard conflict                                                                                                                                                                                                                                         |
| `AK-11` | 3    | The continuation capability exists in this store                                                                                                                                                                                                                                                                              |
| `AK-12` | 4    | The cast entitlement is available and the capability has not already been consumed. Both conditions, not either                                                                                                                                                                                                               |
| `AK-13` | 5    | Election context, manifest digest and parameter-set id match the runtime; contest count, contest order and per-contest selection count match the ballot style; every ciphertext component is in the order-`q` subgroup; every selection proof verifies; the accumulated ciphertext recomputes; the contest-sum proof verifies |
| `AK-14` | 6    | The ballot id is unused in both the accepted and the spoiled map                                                                                                                                                                                                                                                              |

| ID      | Rule                                                                                                                                                                                                                                                                     |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `AK-15` | **No opening is verified for a cast, and none is submitted.** A cast ballot's plaintext and nonces never reach the service. The cast path takes an envelope only; the opening parameter exists on the challenge path alone                                               |
| `AK-16` | `test_e2e_09_invalid_proof` tampers one selection ciphertext, asserts the submission raises, and then asserts `cast_entitlement_available is True`, `accepted_ballots == {}` and `slot_owner == {}` — an invalid proof costs the voter nothing and leaves no slot behind |

## 5. Slot eligibility

`_candidate_slots()` for a cast yields the cast-reserved range
`[0, cast_n)` followed by the shared reserve
`[cast_n + chal_n, cast_n + chal_n + shared_n)`.

| ID      | Rule                                                                                                                                                                                                                                                                                                                                |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `AK-17` | A cast may take a cast-reserved slot, then a shared-reserve slot. Challenge-reserved indices are not in its candidate list                                                                                                                                                                                                          |
| `AK-18` | Exhaustion raises `CastCapacityUnavailableError` (`SUBMISSION_CAST_CAPACITY_UNAVAILABLE`). There is no hidden queue and no overflow batch; the rejected caller's capability is untouched                                                                                                                                            |
| `AK-19` | `test_e2e_07_capacity_exhaustion` runs fixture C (one cast-reserved slot, one challenge-reserved slot, no shared reserve) and asserts: only the first ballot id is in `accepted_ballots`, the outbox holds exactly one row, and the loser's state still has `cast_entitlement_available is True` and `capability_consumed is False` |

## 6. Reason codes

| ID      | Step | Exception                                                           | `reason_code`                             |
| ------- | ---- | ------------------------------------------------------------------- | ----------------------------------------- |
| `AK-20` | 2    | `IdempotencyConflictError` — same key, different canonical request  | `SUBMISSION_IDEMPOTENCY_CONFLICT`         |
| `AK-21` | 3    | `CapabilityUnknownError`                                            | `CONTINUATION_INVALID`                    |
| `AK-22` | 4    | `CastEntitlementExhaustedError`                                     | `CONTINUATION_CAST_ENTITLEMENT_EXHAUSTED` |
| `AK-23` | 5    | `BallotStructureError`                                              | `BALLOT_PREPARATION_STYLE_SHAPE_MISMATCH` |
| `AK-24` | 5    | `ParameterValidationError` — element outside the order-`q` subgroup | `PARAMETER_SET_INVALID`                   |
| `AK-25` | 6    | `DuplicateArtifactError` — ballot id already present                | `ACCEPTANCE_DUPLICATE_BALLOT_ID`          |
| `AK-26` | 7    | `CastCapacityUnavailableError`                                      | `SUBMISSION_CAST_CAPACITY_UNAVAILABLE`    |
| `AK-27` | any  | `InjectedFault` — test-only                                         | `INTERNAL_FAIL_CLOSED`                    |

## 7. Crash behaviour at the six transactional fault points

`test_cast_rolls_back_completely_at_every_transactional_point` in
`services/voting-service/tests/reference/test_fault_injection.py` is
parametrised over the six points named in §3. For each point it snapshots
`continuations`, `accepted_ballots`, `spoiled_ballots`, `reservations`,
`slot_owner`, `obligations`, `outbox.rows` and `idempotency`, arms the
point, asserts `InjectedFault` propagates, and asserts the snapshot is
unchanged. It then re-runs the same request without a hook and asserts
`result.counted is True`.

| ID      | Rule                                                                                                                                                                                                                                                                                                                                                                           |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `AK-28` | **A crash at any of the six transactional fault points leaves the store byte-identical and the capability unspent.** Both halves are asserted: the snapshot equality covers the store, and `test_e2e_05_crash_before_commit` asserts `cast_entitlement_available is True` and `capability_consumed is False` explicitly, with the message "capability was consumed by a crash" |
| `AK-29` | **A retry after a crash succeeds**, and lands where it would have landed if nothing had happened. `test_e2e_05_crash_before_commit` asserts the retried submission is `Outcome.ACCEPTED` and that the resulting reservation list is exactly leaf index `[0]` — the rolled-back attempt left no orphan slot to skip over                                                        |
| `AK-30` | `test_e2e_05_crash_before_commit` additionally asserts `accepted_ballots == {}`, `slot_owner == {}` ("a leaf slot leaked"), `outbox.rows == []` and `idempotency == {}` after the fault. The idempotency record is rolled back with everything else, so a crashed attempt cannot make its own retry look like a replay                                                         |
| `AK-31` | The two post-transaction fault points behave differently by design, and this is not a rollback claim. `before_outbox_publish` leaves the obligation `PENDING` and the next sweep retries it; `after_commit` leaves it `DISPATCHED` and a second sweep dispatches nothing. See `PACK-16D-PERSISTENCE-AND-TRANSACTION-MODEL.md` §5                                               |

## 8. Concurrency evidence

`test_c01_two_simultaneous_casts_on_one_capability` in
`services/voting-service/tests/reference/test_concurrency.py` runs two
`submit_cast_ballot` calls on **one** capability, with different ballots
and different idempotency keys, on two OS threads released together by a
`threading.Barrier`. It is parametrised over 12 repeats. It asserts:

| ID      | Assertion                                                                                                                                       |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| `AK-32` | Exactly one call returns — `len(accepted) == 1`, with the failure message "double acceptance"                                                   |
| `AK-33` | Every losing call raises `CastEntitlementExhaustedError`, not a generic error and not a silent replay                                           |
| `AK-34` | `len(store.accepted_ballots) == 1` — exactly one artefact is persisted                                                                          |
| `AK-35` | `store.continuations[capability].capability_consumed is True`                                                                                   |
| `AK-36` | Exactly one committed leaf: `len([r for r in reservations.values() if r.committed]) == 1`                                                       |
| `AK-37` | `len(store.slot_owner) == 1`, with the failure message "an orphan slot survived" — the loser's compare-and-set left no reserved-but-unused slot |

Related races in the same suite, each 12 repeats:

- `test_c03_cast_and_public_challenge_concurrently` — the outcome is
  **order-dependent** and the test asserts it as such. The cast is
  accepted in either order, because a challenge does not consume the cast
  entitlement. If the challenge wins the race both succeed, the leaf
  indices differ and the challenge index is at or above
  `cast_reserved_per_batch` (`TC-75`); if the cast wins, the capability is
  already consumed, so the challenge is refused with
  `PublicChallengeEntitlementExhaustedError` and leaves nothing behind. An
  earlier version of this test asserted that both always succeed and
  failed about one run in thirty — the assertion was wrong, not the code.
- `test_c04_same_idempotency_key_concurrently` — three racing requests,
  two identical and one conflicting, all sharing one key; exactly one
  `Outcome.ACCEPTED` and exactly one accepted ballot.
- `test_c05_two_reservations_for_the_same_slot` — fixture C, one
  cast-reserved slot, two capabilities; exactly one acceptance, every
  failure a `CastCapacityUnavailableError`, `len(slot_owner) == 1`, and
  exactly one capability still holding an unspent cast entitlement ("a
  lost race is not a spent vote").
- `test_c07_publication_worker_retry` — four concurrent outbox sweeps
  dispatch the obligation exactly once.

`test_e2e_04_double_cast_race` asserts the sequential form: the second
cast raises `CastEntitlementExhaustedError`, one ballot is accepted, and
the committed leaf indices are a single distinct value.

`test_no_capability_to_ballot_leakage_in_any_persisted_row` submits both
a challenge and a cast on one capability and then asserts, over every
reservation, obligation, outbox row, continuation state and idempotency
key and value, that no capability reference appears beside a ballot id
and no ballot id appears inside a continuation state.

| ID      | Rule                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `AK-38` | **The concurrency evidence is bounded.** These races exercise real OS threads against the reference in-memory store, whose transaction boundary is a re-entrant lock. That proves the logic is race-free under the serialisation this store provides. It proves nothing about a production datastore, where the same invariants must come from row-level locking or a serialisable isolation level. That demonstration is a PACK-17 obligation (`OD-P16D-04`) |

## 9. What this document does not decide

```text
Production datastore isolation level        → OD-P16D-04, PACK-17
Production authentication of the caller     → OD-P16D-08
Constant-time / side-channel behaviour       → OD-P16D-05, not claimed
Key custody for the guardian ceremony        → OD-P16D-11, PACK-17
Capacity plan values for a real election     → GOVERNANCE, PACK-16C
External review of the cryptography          → VO-08, open
```

**REFERENCE IMPLEMENTATION. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY.
NOT LEGALLY ACTIVATED.**
