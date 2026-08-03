# PACK-16D — Atomic Challenge Transaction

**Round:** PACK-16D — Cryptographic Implementation Architecture, Reference
Components, Atomic Persistence, Test Vectors and Verification Harness.
**Reference implementation. Not production code. Not certified. Not a PASS.**
**Repository version:** unchanged at `0.16.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-102`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 1. Scope

This document specifies `submit_public_challenge()` as implemented in
`services/voting-service/src/epd2_voting_service/reference/casting/transactions.py`.
It is the public evidentiary challenge boundary: the point at which a
ballot is spoiled, opened publicly, given a leaf slot and made a
publication obligation — or at which nothing at all happens.

| ID | Rule |
| -- | ---- |
| `AC-01` | **The whole operation is one `store.transaction()` scope.** There is no partial outcome. Either every mutation in §3 is present after the call, or none of them is |
| `AC-02` | **A challenge that does not commit does not spend the challenge entitlement.** The entitlement is a state field inside the same transaction as the artefact, so a failure cannot spend it |
| `AC-03` | **A public challenge never consumes the capability.** It clears `public_challenge_entitlement_available` only; `cast_entitlement_available` and `capability_consumed` are untouched |

## 2. Computed before the transaction opens

Two values are derived before the lock is taken. Neither reads or writes
the store, so computing them early is not a race.

```text
scope  = (runtime.manifest.election_context_id, "public_challenge", idempotency_key)
digest = request_digest(envelope.canonical_bytes(runtime.params))
```

| ID | Rule |
| -- | ---- |
| `AC-04` | The idempotency scope is a three-tuple of election context, operation literal `"public_challenge"` and caller key. The operation literal is part of the scope, so the same key used for a cast is a different record (see `PACK-16D-IDEMPOTENCY-AND-REPLAY-MODEL.md`) |
| `AC-05` | The request digest binds to the canonical encoding of the envelope under the election's parameter set, never to a summary, a field subset or a client-supplied hash |

## 3. The ordered step list

Steps run in exactly this order inside one transaction. "Mutates" marks a
step that writes to the store; every write before it is undone if any
later step raises.

| # | Step | Mutates | Fault point |
| -- | ---- | ------- | ----------- |
| 1 | Open `store.transaction()` — acquire the store lock, snapshot every map | no | — |
| 2 | `_replay(tx, scope, digest)` — idempotency lookup **inside** the transaction | no | — |
| 3 | Load `tx.continuations[capability_reference]`; absent is an error | no | — |
| 4 | Check `public_challenge_entitlement_available` | no | `after_capability_validation` |
| 5 | `verify_ballot_proofs()` — structure, subgroup membership, selection proofs, accumulation, contest-sum proof | no | — |
| 6 | `verify_challenge_opening()` — re-encrypt every selection from the submitted nonces and plaintexts and compare | no | `after_proof_validation` |
| 7 | Reject if `envelope.ballot_id` is already in `spoiled_ballots` or `accepted_ballots` | no | — |
| 8 | `tx.reserve_leaf()` — compare-and-set over `(batch_sequence, leaf_index)`, candidate list per §6 | **yes** | `after_slot_reservation` |
| 9 | `tx.continuations[cap] = state.spend_public_challenge()` | **yes** | `after_entitlement_mutation` |
| 10 | `tx.spoiled_ballots[ballot_id] = envelope.canonical_bytes(params)` | **yes** | `after_ballot_persistence` |
| 11 | `tx.commit_reservation(reservation_id)` — flips the reservation to `committed=True` | **yes** | — |
| 12 | Build `PublicationObligation`, store it in `tx.obligations`, `tx.outbox.enqueue()` it | **yes** | — |
| 13 | Build the `SubmissionResult`, deriving the confirmation code from the public ciphertexts and `base_hash` | no | — |
| 14 | `_record_idempotency(tx, scope, digest, result)` | **yes** | `before_transaction_commit` |
| 15 | Return; the context manager exits without an exception and nothing is restored | no | — |

| ID | Rule |
| -- | ---- |
| `AC-06` | **Steps 2 to 7 are read-only.** The first byte written to the store is the leaf reservation in step 8. Every rejection reachable from a well-formed request is therefore a rejection that has changed nothing |
| `AC-07` | **The reservation precedes the artefact.** There is no path that persists a spoiled ballot and then looks for a slot to put it in |
| `AC-08` | Successful outcome: `Outcome.ACCEPTED`, reason code `challenge.spoiled_published`, `counted = False`. The artefact is published as evidence and is never tallied |
| `AC-09` | The publication obligation is `obl-chal-<ballot_id>` with `artifact_type = "public_challenged_spoiled"`, `batch_window_id` from the runtime and `coarse_creation_bucket` equal to that window id. No finer time value exists on the row |

## 4. What is validated before anything is mutated

| ID | Validated at step | Content |
| -- | ----------------- | ------- |
| `AC-10` | 2 | Replay: an existing record with the same digest returns the recorded outcome; an existing record with a different digest is a hard conflict |
| `AC-11` | 3 | The continuation capability exists in this store |
| `AC-12` | 4 | The public-challenge entitlement is still available |
| `AC-13` | 5 | Election context, manifest digest and parameter-set id match the runtime; contest count, contest order and per-contest selection count match the ballot style; every ciphertext component is a member of the order-`q` subgroup; every disjunctive selection proof verifies; the accumulated ciphertext recomputes; the contest-sum proof verifies |
| `AC-14` | 6 | The opening belongs to this ballot id, is complete for every selection, and re-encrypting each selection under its submitted nonce and plaintext reproduces the published ciphertext exactly |
| `AC-15` | 7 | The ballot id is unused in both the accepted and the spoiled map |

| ID | Rule |
| -- | ---- |
| `AC-16` | **Proof verification is not optional and not sampled.** `verify_ballot_proofs()` raises on the first failure; it has no permissive branch and no "accept and flag" outcome |
| `AC-17` | **Subgroup membership is checked before any equation is evaluated**, on every ciphertext component |
| `AC-18` | A challenge whose opening does not re-encrypt is rejected. The reference implementation does not publish an unverified opening, because an opening that does not reproduce the ciphertext is not evidence of anything |

## 5. Why the entitlement is spent inside the same transaction

The challenge entitlement is a finite resource: `K = 1` public challenge
per continuation capability (`K_PUBLIC_CHALLENGES_PER_CONTINUATION`). It
bounds `L_max = E × (K + A)` and therefore bounds the published capacity
plan. Spending it and persisting the artefact are the same fact.

| ID | Rule |
| -- | ---- |
| `AC-19` | **Spending the entitlement outside the transaction that persists the artefact would create two failure modes, both unacceptable.** Spend-then-persist can burn a voter's only challenge and publish nothing. Persist-then-spend can publish a spoiled artefact against an entitlement that is never debited, so one capability yields two challenges and the capacity plan no longer bounds the board |
| `AC-20` | Both mutations are steps 9 and 10 of one transaction. A crash between them restores both |
| `AC-21` | `ContinuationState.spend_public_challenge()` is itself defensive: it re-checks the entitlement and refuses if the capability has already been consumed by a cast. The transaction check at step 4 and the state-machine check are independent |
| `AC-22` | The entitlement lives in `store.continuations`, keyed by capability reference; the artefact lives in `store.spoiled_ballots`, keyed by ballot id. They are mutated in one transaction and **share no key** (`DM-10`). Atomicity here does not create a join |

## 6. Slot eligibility — `TC-75`

`_candidate_slots()` builds the candidate list from the declared capacity
partition, in order:

```text
challenge-reserved:  [cast_n              .. cast_n + chal_n)
shared reserve:      [cast_n + chal_n     .. cast_n + chal_n + shared_n)
```

| ID | Rule |
| -- | ---- |
| `AC-23` | **A public challenge may take a challenge-reserved slot, then a shared-reserve slot, and NEVER a cast-reserved slot** (`TC-75`). Cast-reserved indices `[0, cast_n)` are not in the candidate list at all — the prohibition is structural, not a check that could be skipped |
| `AC-24` | Order is fixed: the challenge-reserved range is exhausted before the shared reserve is touched. A challenge does not reach for the shared reserve while its own class still has room |
| `AC-25` | The shared reserve is exactly `plan.shared_reserve_per_batch` slots. It is never inferred from the batch capacity — see Defect 2 in `PACK-16D-PERSISTENCE-AND-TRANSACTION-MODEL.md` |
| `AC-26` | `requested_class` selects the reason code on exhaustion. It never widens the candidate list; the caller has already decided which slots this submission may take |
| `AC-27` | Exhaustion fails closed with `PublicChallengeReservationUnavailableError`. There is no queue, no deferral and no overflow batch. The capability is untouched, so a lost slot is not a lost challenge |

**Evidence.** `test_c03_cast_and_public_challenge_concurrently`
(`test_concurrency.py`, 12 repeats) races a cast and a public challenge on
one capability. The outcome is order-dependent, and the test asserts it
that way: the cast is always accepted, and **when the challenge wins the
race** it too is accepted, its leaf index differs from the cast's, and
`challenge_leaf >= plan.cast_reserved_per_batch` — that is `TC-75` checked
under a real thread race rather than in sequence. When the cast wins, the
capability is already consumed, so the challenge is refused with
`PublicChallengeEntitlementExhaustedError` and takes no slot at all.
`test_e2e_01_valid_cast` asserts the complementary bound for a cast:
`committed[0].leaf_index < plan.cast_reserved_per_batch`.

## 7. Reason codes

Each failure raises a typed exception carrying a `reason_code` class
attribute. No failure returns a partial success.

| ID | Step | Exception | `reason_code` |
| -- | ---- | --------- | ------------- |
| `AC-28` | 2 | `IdempotencyConflictError` — same key, different canonical request | `SUBMISSION_IDEMPOTENCY_CONFLICT` |
| `AC-29` | 3 | `CapabilityUnknownError` | `CONTINUATION_INVALID` |
| `AC-30` | 4 | `PublicChallengeEntitlementExhaustedError` | `CHALLENGE_PUBLIC_ENTITLEMENT_EXHAUSTED` |
| `AC-31` | 5 | `BallotStructureError` — context, manifest digest, parameter set, style shape, contest order, selection count, selection proof, accumulation, contest-sum proof | `BALLOT_PREPARATION_STYLE_SHAPE_MISMATCH` |
| `AC-32` | 5 | `ParameterValidationError` — a ciphertext component is not in the order-`q` subgroup | `PARAMETER_SET_INVALID` |
| `AC-33` | 6 | `ChallengeOpeningError` — wrong ballot id, incomplete opening, or re-encryption mismatch | `CHALLENGE_REENCRYPTION_MISMATCH` |
| `AC-34` | 7 | `DuplicateArtifactError` — ballot id already present | `ACCEPTANCE_DUPLICATE_BALLOT_ID` |
| `AC-35` | 8 | `PublicChallengeReservationUnavailableError` | `CHALLENGE_PUBLIC_RESERVATION_UNAVAILABLE` |
| `AC-36` | any | `InjectedFault` — test-only, raised only by an explicitly passed hook | `INTERNAL_FAIL_CLOSED` |

| ID | Rule |
| -- | ---- |
| `AC-37` | A replayed request returns `Outcome.REPLAYED` carrying the **recorded** outcome code from the original acceptance, not a fresh one |
| `AC-38` | `ReservationUnavailableError` is a base class and is never raised directly. A cast and a challenge exhaust different capacity and get different codes, because collapsing them would hide which class ran out |

## 8. Rollback evidence

`test_public_challenge_rolls_back_completely` in
`services/voting-service/tests/reference/test_fault_injection.py` is
parametrised over the six transactional fault points listed in §3
(`after_capability_validation`, `after_proof_validation`,
`after_slot_reservation`, `after_ballot_persistence`,
`after_entitlement_mutation`, `before_transaction_commit`). For each
point it:

1. snapshots eight structures — `continuations`, `accepted_ballots`,
   `spoiled_ballots`, `reservations`, `slot_owner`, `obligations`,
   `outbox.rows` and `idempotency`;
2. arms the point and asserts `InjectedFault` propagates;
3. asserts the snapshot after the fault equals the snapshot before it;
4. re-runs the identical request without a hook and asserts it succeeds
   with `counted is False`;
5. asserts `cast_entitlement_available is True` after both the fault and
   the retry.

| ID | Rule |
| -- | ---- |
| `AC-39` | **A crash at any transactional fault point leaves the store byte-identical to its pre-call state.** This is asserted over all eight structures, not over a chosen subset |
| `AC-40` | **The retry then succeeds.** A fault is not a state a caller has to clean up |
| `AC-41` | The fault hook reaches the transaction only by being passed explicitly into the call. `hooks.trip()` is a no-op when no hook is supplied, there is no global registry and no environment switch, and `test_production_modules_do_not_import_the_injector` parses every non-`testing` module under `reference/` and asserts none imports the injector |
| `AC-42` | `test_an_unarmed_injector_is_transparent` asserts that a present-but-unarmed hook changes no outcome, so the hook itself is not the thing being tested around |

`test_c02_two_simultaneous_public_challenges` (12 repeats) races two
challenges on one capability: exactly one is accepted, every failure is a
`PublicChallengeEntitlementExhaustedError`, exactly one row exists in
`spoiled_ballots`, and afterwards
`public_challenge_entitlement_available is False` while
`cast_entitlement_available is True`. `test_e2e_03_second_public_challenge_rejected`
asserts the sequential form, including that the rejected ballot id is
absent from `spoiled_ballots`.

The concurrency evidence is bounded by §17.2 of the round's fact base:
these races run against the reference in-memory store, whose transaction
boundary is a re-entrant lock. They say nothing about a production
datastore's isolation level (`OD-P16D-04`).

## 9. What this document does not decide

```text
Production datastore isolation level        → OD-P16D-04, PACK-17
Production authentication of the caller     → OD-P16D-08
Batch interval, capacity plan values         → GOVERNANCE, PACK-16C
Reservation expiry policy in production      → PACK-17
Cross-mirror split-view detection            → OD-P16D-06
External review of the cryptography          → VO-08, open
```

**REFERENCE IMPLEMENTATION. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY.
NOT LEGALLY ACTIVATED.**
