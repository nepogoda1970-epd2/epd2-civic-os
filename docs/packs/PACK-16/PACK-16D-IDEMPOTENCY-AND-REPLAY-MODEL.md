# PACK-16D — Idempotency and Replay Model

**Round:** PACK-16D — Cryptographic Implementation Architecture, Reference
Components, Atomic Persistence, Test Vectors and Verification Harness.
**Reference implementation. Not production code. Not certified. Not a PASS.**
**Repository version:** unchanged at `0.16.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-102`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 1. Scope

This document specifies the replay model implemented in
`services/voting-service/src/epd2_voting_service/reference/casting/idempotency.py`
and applied by `_replay()` and `_record_idempotency()` in
`casting/transactions.py`.

The problem it solves is narrow and unavoidable: a voter's client may not
know whether a submission it lost the answer to was accepted. It must be
able to ask again without risking either a second accepted ballot or a
silent misreading of a _different_ request as the earlier one.

## 2. Scope key

```text
scope = (election_context_id, operation, idempotency_key)
```

| ID      | Rule                                                                                                                                                                                                                             |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ID-01` | **The idempotency scope is the three-tuple above.** All three components are part of the key. `IdempotencyRecord.scope` returns exactly this tuple, so the record and the lookup cannot drift apart                              |
| `ID-02` | `election_context_id` comes from the runtime manifest, never from the request. A caller cannot address another election's record by claiming to be in it                                                                         |
| `ID-03` | `operation` is the literal `"public_challenge"` in `submit_public_challenge()` and `"cast"` in `submit_cast_ballot()`. It is set by the transaction, not supplied by the caller                                                  |
| `ID-04` | `idempotency_key` is caller-supplied and opaque to the service                                                                                                                                                                   |
| `ID-05` | **The key is never a capability reference, a credential or a public ballot reference.** `test_no_capability_to_ballot_leakage_in_any_persisted_row` asserts that no capability reference appears in any idempotency key or value |
| `ID-06` | The record stores `outcome_code` and an ordered tuple of `(name, value)` string pairs — `ballot_id`, `confirmation_code`, `batch_window_id`, `publication_obligation_id`, `counted` — and nothing else                           |

### 2.1 Why the same key in a different operation is a different scope

A cast and a public challenge are different acts with different
consequences: one consumes the capability and is counted, the other
spends the challenge entitlement and is published as evidence and never
counted. Their result payloads differ in `counted` and in
`artifact_type`.

| ID      | Rule                                                                                                                                                                                                                                                                                                          |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ID-07` | **A key reused across operations addresses two independent records.** `("ctx", "cast", "k")` and `("ctx", "public_challenge", "k")` are distinct scopes                                                                                                                                                       |
| `ID-08` | This is the correct behaviour, not a leniency. If the operation were dropped from the scope, a client that reused one key for both submissions would receive the cast's recorded outcome in answer to a challenge — a reply describing an artefact that was counted, for a request that must never be counted |
| `ID-09` | It is not a loophole in the entitlement limits either. The scope key governs _replay_; the number of accepted casts and challenges is governed by `ContinuationState`, which is checked separately in every transaction. Reusing a key across operations buys no extra entitlement                            |
| `ID-10` | A key reused across elections is likewise a different scope, because `election_context_id` is part of the tuple                                                                                                                                                                                               |

## 3. Request digest

```python
def request_digest(canonical_request: bytes) -> str:
    return hashlib.sha256(canonical_request).hexdigest()
```

The argument is always `envelope.canonical_bytes(runtime.params)`.

| ID      | Rule                                                                                                                                                                                                                                               |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ID-11` | **The digest binds to the canonical request bytes, never to a loose summary.** Not a field subset, not a client-supplied hash, not a JSON rendering                                                                                                |
| `ID-12` | The canonical encoding is `EPD2-ENC-1`: fixed-width, length-prefixed, ordered and never sorted, NFC-normalised, duplicate-field-rejecting. Two encodings that differ in any field, in field order or in Unicode spelling produce different digests |
| `ID-13` | The digest is computed before the transaction opens. It reads nothing from the store, so computing it early is not a race                                                                                                                          |

## 4. Stable replay versus hard conflict

`_replay()` has exactly three outcomes.

| ID      | Record state                            | Outcome                                                                                                                                                |
| ------- | --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `ID-14` | No record for this scope                | Return `None`; the transaction proceeds to capability validation                                                                                       |
| `ID-15` | Record exists, `request_digest` matches | Return a `SubmissionResult` with `outcome = Outcome.REPLAYED`, rebuilt from the stored payload, carrying the **recorded** `outcome_code`               |
| `ID-16` | Record exists, `request_digest` differs | Raise `IdempotencyConflictError` (`SUBMISSION_IDEMPOTENCY_CONFLICT`), message "the same idempotency key was reused with a different canonical request" |

| ID      | Rule                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ID-17` | **A replay is stable.** It returns the ballot id, confirmation code, batch window id, publication obligation id and `counted` flag of the original acceptance. It performs no new proof verification, reserves no slot, mutates no entitlement and enqueues no second obligation                                                                                                                                                                                                                               |
| `ID-18` | **A replay is distinguishable from an acceptance.** `Outcome.REPLAYED` is a different value from `Outcome.ACCEPTED`; a caller that cannot tell the two apart has not been told the truth about what happened                                                                                                                                                                                                                                                                                                   |
| `ID-19` | **A conflict is a hard failure, never a silent replay.** A different canonical request under the same key raises. Returning the earlier result would answer a question the caller did not ask, about a ballot it did not send                                                                                                                                                                                                                                                                                  |
| `ID-20` | The idempotency record is written inside the transaction, at the last step before commit, from the result that was actually produced. A transaction that rolls back leaves no record — `test_e2e_05_crash_before_commit` asserts `store.idempotency == {}` after a crash, so a crashed attempt cannot make its own retry look like a replay                                                                                                                                                                    |
| `ID-21` | A duplicate **ballot id** is a separate check with a **different** reason code: a ballot id already present in `accepted_ballots` or `spoiled_ballots` raises `DuplicateArtifactError` (`ACCEPTANCE_DUPLICATE_BALLOT_ID`), message "ballot ... is already published". This catches a resubmitted artefact under a fresh key, which the scope check cannot see. The two codes differ because a client may retry an idempotency conflict with a corrected request and must not retry a duplicate artefact at all |

## 5. Defect 1 — the check ran outside the transaction

Reported plainly, because it is evidence that the harness works and
because an auditor who finds an undisclosed defect is entitled to
distrust everything else in this round.

**The defect.** The first implementation called `_replay()` _before_
opening `store.transaction()`.

**Why it was wrong.** The check and the write were then in different
critical sections. Two concurrent requests sharing one idempotency key
could both perform the lookup, both observe "no record yet", and both
proceed into the transaction. The second request was therefore evaluated
as a fresh submission instead of being compared against the first. A
conflicting request — the same key with a different canonical request —
could be accepted rather than rejected, which is precisely the outcome
`ID-19` exists to prevent.

**How it was found.** `test_c04_same_idempotency_key_concurrently` in
`services/voting-service/tests/reference/test_concurrency.py`,
parametrised over 12 repeats. It races three `submit_cast_ballot` calls
released together by a `threading.Barrier`: two identical requests on one
capability under the key `"same"`, and a third, conflicting request on a
different capability under the same key. It asserts that exactly one
result is `Outcome.ACCEPTED`, that at least one failure is an
`IdempotencyConflictError` or a `CastEntitlementExhaustedError` with the
comment "the conflicting third request must fail, never silently replay",
and that `len(store.accepted_ballots) == 1`.

**How it was fixed.** The implementation was changed, not the test. The
`_replay()` call now runs **inside** `store.transaction()` in both
`submit_public_challenge()` and `submit_cast_ballot()`, so the lookup and
the record write are in the same critical section. The code carries a
comment at the call site stating that checking first and then opening a
transaction is a race, that a concurrency test found exactly that, and
that it must not be moved back out.

| ID      | Rule                                                                                                                                                      |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ID-22` | **The idempotency check runs inside the transaction that writes the idempotency record.** Any implementation that separates them reintroduces this defect |
| `ID-23` | The lesson generalises: a read-then-write pair that decides whether a submission is new is not a validation step, it is a critical section                |

## 6. Limitation

| ID      | Rule                                                                                                                                                                                                                                                                                                                                                                                      |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ID-24` | **The evidence for `ID-22` covers this in-memory store's re-entrant lock only.** The race tests use real OS threads against `ReferenceStore`. In a production datastore the same guarantee must come from row-level locking, a unique constraint on the scope tuple or a serialisable isolation level. Nothing in this round demonstrates that; it is a PACK-17 obligation (`OD-P16D-04`) |
| `ID-25` | There is no expiry, eviction or retention policy for idempotency records in the reference store. A production deployment needs one, and it is not specified here                                                                                                                                                                                                                          |

## 7. What this document does not decide

```text
Idempotency record retention and expiry       → PACK-17
Production datastore isolation level          → OD-P16D-04, PACK-17
Client key-generation policy                   → PACK-17
Production authentication of the caller        → OD-P16D-08
Transport-level retry behaviour                → PACK-16C API catalog
```

**REFERENCE IMPLEMENTATION. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY.
NOT LEGALLY ACTIVATED.**
