# PACK-16D — Implementation Architecture

**Round:** PACK-16D — Cryptographic Implementation Architecture, Reference
Components, Atomic Persistence, Test Vectors and Verification Harness.
**Reference implementation. Not production code. Not certified. Not a PASS.**
**Repository version:** unchanged at `0.16.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-102`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 1. Where the code lives, and why there

All reference code is one package:

```text
services/voting-service/src/epd2_voting_service/reference/
```

45 Python modules (38 substantive plus 7 sub-package `__init__.py` files)
and 3 parameter artefacts — one JSON artefact for `EPD2-CRYPTO-1` and two
test `.params` files. The seventh sub-package is `guardians/`, added with
the threshold ceremony.

### 1.1 The placement decision

| ID      | Rule                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `IA-01` | **The reference implementation is placed inside the existing `epd2-voting-service` package, not in a new workspace member.** Adding a workspace member requires editing the root `pyproject.toml` and regenerating `uv.lock`. `uv.lock` cannot be regenerated in this environment — PyPI returns HTTP 403 — and hand-editing a lock file is prohibited. Placing the package inside an existing service needs no manifest change at all, so `uv.lock` and `package-lock.json` are byte-identical to `0.15.0` |
| `IA-02` | **The suggested `src/epd2/voting/...` layout was adapted to the repository's actual convention rather than followed literally.** Creating that path would have created a second repository root, which is explicitly forbidden. The adaptation preserves the intent — one package, one import prefix, no ambiguity about what is reference code — without the prohibited structural change                                                                                                                  |
| `IA-03` | **Placement is not endorsement.** Living inside a service package does not make this code part of that service's runtime. No existing module in `epd2_voting_service` imports `epd2_voting_service.reference`; the package is entered only through its own `api.py` or directly by tests                                                                                                                                                                                                                    |

The cost of `IA-01` is stated plainly: the reference implementation is not
independently versioned or independently installable, and a consumer who
wants only the verifier gets the whole voting service's package. That is
the price of leaving both lock files untouched, and it is reversible in
PACK-17 once a network-capable environment can regenerate `uv.lock`.

---

## 2. Layering

### 2.1 The layers

| Layer | Contents                                                                                                                                                                                                                                                                                            | May import                                                         |
| ----- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| 0     | `hooks.py`, `invariants.py`, `logging_boundary.py`, `crypto/domain_separation.py`, `crypto/encoding.py`, `crypto/randomness.py`, `crypto/signature_provider.py`, `publication/capacity.py`, `publication/outbox.py`, `casting/continuation.py`, `casting/idempotency.py`, `verification/results.py` | **nothing inside `reference/`**                                    |
| 1     | the rest of `crypto/` — `hashing.py`, `parameters.py`, `elgamal.py`, `proofs.py`, `merkle.py`                                                                                                                                                                                                       | layer 0 and `crypto/` only                                         |
| 1a    | `guardians/` — `ceremony.py`, `threshold.py`                                                                                                                                                                                                                                                        | layers 0–1 and `crypto/` only; `threshold` also imports `ceremony` |
| 2     | `casting/` and `publication/` — ballot, confirmation, store, transactions, sealed batches, sealing, bulletin board, checkpoint signing                                                                                                                                                              | layers 0–1, and each other under `IA-06`                           |
| 3     | `election_record/builder.py`                                                                                                                                                                                                                                                                        | layers 0–2, and `guardians/`                                       |
| 4     | `verification/verifier.py`                                                                                                                                                                                                                                                                          | layers 0–3, and `guardians/`, under the restriction in §4          |
| 5     | `api.py`, `audit.py`, `schemas.py`                                                                                                                                                                                                                                                                  | layers 0–4                                                         |
| —     | `testing/`                                                                                                                                                                                                                                                                                          | everything above, and nothing imports it (`IA-08`)                 |

| ID      | Rule                                                                                                                                                                                                                                                                                                                                                |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `IA-27` | **`guardians/` is a layer of its own between `crypto/` and `casting/`/`publication/`.** `ceremony.py` and `threshold.py` import `crypto/` and nothing else in `reference/`, so the ceremony and the threshold path can be reviewed against the primitives alone. `election_record/builder.py` and `verification/verifier.py` are the only consumers |
| `IA-28` | **`publication/checkpoint_signing.py` sits in layer 2 but imports only `crypto/`** — `ed25519`, `domain_separation`, `encoding`, `hashing`. It has no board, no store and no record, which is what lets the verifier import it without importing the publisher                                                                                      |

| ID      | Rule                                                                                                                                                                                                                                                                                                                |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `IA-04` | **The dependency graph over modules is acyclic, and that is a property to be checked rather than assumed.** Every internal import in the package is of the fully qualified form `from epd2_voting_service.reference....`; there are no relative imports and no dynamic imports, so the graph can be read statically |
| `IA-05` | **Nothing in `crypto/` imports anything outside `crypto/`.** The cryptographic core has no knowledge of ballots, batches, boards, stores or records. It can therefore be reviewed, and its test vectors regenerated, without any of them                                                                            |

### 2.2 The two cross-edges between `casting/` and `publication/`

The intended reading order is
`crypto` → `casting` → `publication` → `election_record` → `verification`.
At package granularity that is **not a strict total order**, and pretending
otherwise would misdescribe the code. Two edges cross it:

```text
casting/store.py        -> publication/capacity.py   (SlotClass)
casting/store.py        -> publication/outbox.py     (Outbox, PublicationObligation)
publication/sealing.py  -> casting/store.py          (ReferenceStore)
```

| ID      | Rule                                                                                                                                                                                                                                                                                                                                                                        |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `IA-06` | **These edges are permitted and the graph stays acyclic, because `publication/capacity.py` and `publication/outbox.py` are layer-0 modules that import nothing inside `reference/`.** They are declarative types — a slot classification and an obligation row — not behaviour. `publication/sealing.py` may therefore depend on `casting/store.py` without closing a cycle |
| `IA-07` | **Any new module in `publication/` that both imports `casting/` and is imported by `casting/` is prohibited**, because it would close the cycle that `IA-06` currently avoids by accident of leaf-ness rather than by design. If `capacity.py` or `outbox.py` ever needs a `casting/` import, the shared type moves to layer 0 instead                                      |

### 2.3 `testing/` is one-way

| ID      | Rule                                                                                                                                                                                                                                                                                |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `IA-08` | **`reference/testing/` depends on every other layer, and no module outside it depends on `reference/testing/`.** The only occurrence of the string `reference.testing` outside that package is a prose reference in `hooks.py`'s module docstring — not an import                   |
| `IA-09` | **`testing/` holds fixtures, the fault injector, scenario builders and the test-vector generator, and nothing else.** It is where deterministic randomness, small parameter profiles and armed fault points live, so that none of them has a reason to exist in the production path |
| `IA-10` | Deleting `reference/testing/` must leave the rest of the package importable. This is what `IA-08` means operationally, and it is why the fault-hook boundary in §3 exists at all                                                                                                    |

---

## 3. The fault-hook boundary

The round requires rollback and recovery to be testable at eleven named
points. The obvious implementations are both unacceptable: importing test
code into the production path, or gating behaviour on an environment
variable. `reference/hooks.py` is the compromise, and it is 32 lines.

```text
hooks.py
  FaultHook   Protocol with a single method, trip(point: str) -> None
  trip(hook, point)   calls hook.trip(point) if hook is not None
```

| ID      | Rule                                                                                                                                                                                                                                                                   |
| ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `IA-11` | **Production modules depend only on the `FaultHook` protocol and call it through `trip()`.** The parameter is typed `FaultHook \| None`; a missing hook is not an error and `trip()` is a no-op                                                                        |
| `IA-12` | **`trip()` takes the point as a plain `str`**, so that no production module has to import `FaultPoint`. `FaultPoint` is a `StrEnum` under `testing/faults.py` and normalises the value at the injector, not at every call site                                         |
| `IA-13` | **There is no global registry and no environment switch.** A hook can only be installed by passing it explicitly into a call. A deployed system that never passes one cannot have a fault injected into it — this is a structural property, not a configuration choice |
| `IA-14` | **The only implementation of the protocol that raises is `testing.faults.FaultInjector`**, which lives under `testing/` and is never constructed by production code. `InjectedFault` carries `reason_code = "INTERNAL_FAIL_CLOSED"`                                    |
| `IA-15` | **A fault point is armed once and disarms itself when it fires.** The injector discards the point before raising, so a retry after an injected fault exercises the recovery path rather than the same failure again                                                    |

The eleven points, from `testing/faults.py`:
`after_capability_validation`, `after_proof_validation`,
`after_slot_reservation`, `after_ballot_persistence`,
`after_entitlement_mutation`, `before_transaction_commit`, `after_commit`,
`before_outbox_publish`, `after_board_append`,
`before_checkpoint_signing`, `during_record_export`.

The modules that call `trip()` are `casting/transactions.py`,
`publication/bulletin_board.py` and `election_record/builder.py` — that
is, exactly the modules that mutate durable state or publish.
`publication/sealing.py` used to call it too, under the wrong point name;
that call site was removed and an `ast`-based test now pins every
remaining one.

---

## 4. Dependency direction: the verifier depends on no private state

This is the single most load-bearing architectural rule of the round. An
independent verifier that could reach the store would be verifying its own
inputs.

| ID      | Rule                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `IA-16` | **The verifier takes exported bytes and public artefacts only.** `BoardExport` is a bytes-only view: entry triples, checkpoint tuples, the full signed checkpoints, the declared `SignerRegistry`, and an optional tuple of consistency proofs. There is no handle to a live board. The signer registry is a trust anchor supplied _alongside_ the export, never read out of the checkpoints being verified                                                                                                                                                                                                                                                                                                                                                       |
| `IA-29` | **`board_export_from(board)` is the single place a complete board export is built.** Callers that assembled a `BoardExport` by hand were the reason the signed view and the legacy tuple view could drift apart; one constructor means a caller cannot forget the signed checkpoints or the registry                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| `IA-17` | **`verification/` must not import `casting.store`, `casting.continuation`, `casting.transactions`, `casting.idempotency` or `api`.** This is asserted by a test that parses `verification/*.py` with `ast` — not by convention and not by review                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| `IA-18` | **The words `capability_reference`, `credential_id`, `voter_id` and `continuation_capability` must not appear anywhere in the verifier**, in any form, including comments. A second test asserts this                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| `IA-19` | What the verifier _may_ import is the set of pure artefact and mathematics modules: `crypto/` (elgamal, merkle, parameters, proofs, encoding, hashing, domain separation), `casting/ballot.py` and `casting/confirmation.py` for the artefact shapes and the opening check, `publication/sealed_batches.py` for leaf classes and openings, `publication/bulletin_board.py` for the `Checkpoint` shape, **`publication/checkpoint_signing.py`** for the signature profile and the signer registry, **`guardians/ceremony.py` and `guardians/threshold.py`** for ceremony verification and share verification, `election_record/builder.py` for `ElectionRecord`, and `verification/results.py`. All of these are structure and equations; none of them holds state |
| `IA-20` | **Consistency verification does not mirror the prover.** `verify_consistency` in `crypto/merkle.py` is the standard iterative RFC 6962 §2.1.2 algorithm, deliberately not a re-run of the prover's recursion — a verifier that re-ran the prover's own recursion would agree with the prover by construction and prove nothing                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| `IA-21` | **An absent input produces an absent check, never a passed one — and an input that is required is not made optional.** `BoardExport.consistency_proofs` is optional; when it is empty the verifier does not add `board.consistency_proofs` to `checks_run`. An export that carries checkpoint tuples but no signed checkpoints is different: it returns `INCOMPLETE_RECORD` rather than falling back to a weaker digest, because a fallback covering less than the board actually signed is a downgrade a verifier could not see. The nine-entry `NOT_CHECKED` list is printed with every result, including `VERIFIED`, and one entry names `VO-08` as open                                                                                                       |
| `IA-22` | **Cross-mirror split-view detection is not implemented** (`OD-P16D-06`). `verify_board()` detects rollback, equivocation and a broken checkpoint chain **within a single exported view**. Gossip between mirrors is a different problem with an unsettled standards landscape, and must not be claimed                                                                                                                                                                                                                                                                                                                                                                                                                                                            |

---

## 5. Atomicity, and the two defects the harness found

The two atomic transactions — `submit_public_challenge` and
`submit_cast_ballot` — run the same eight steps inside one
`store.transaction()`: idempotency check, capability and entitlement
validation, proof verification (and, for a challenge, the opening), leaf
reservation by compare-and-set, entitlement mutation, artefact
persistence, reservation commit, then obligation creation and outbox
enqueue. The transaction snapshots every map on entry and restores the
snapshot on any exception, so a capability is never spent by a submission
that does not commit.

Two real defects were found by the tests. They are reported here because
they are the evidence that the harness does something.

| ID      | Defect and correction                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `IA-23` | **The idempotency check was outside the transaction.** The first implementation called `_replay()` before opening the transaction, so two concurrent requests sharing an idempotency key could both observe "no record yet" and both proceed — a conflicting request was accepted instead of rejected. Found by `test_c04_same_idempotency_key_concurrently`. **Fixed in the implementation**: the check now runs inside `store.transaction()`, and the code carries a comment saying not to move it back out                                                                                                                                                                                    |
| `IA-24` | **The shared reserve was inferred rather than declared.** `_candidate_slots()` computed the shared reserve as "every slot from `cast_n + chal_n` to the batch capacity", ignoring `plan.shared_reserve_per_batch`, so any batch larger than the declared partition silently gained unclassified slots — adaptive overflow reintroduced by arithmetic. Found by `test_e2e_07_capacity_exhaustion`. **Fixed in the implementation**: the shared reserve is now exactly the declared count, and `CapacityPlan.validate()` requires `cast + challenge + shared == primary_capacity` exactly, raising `CapacityPlanInvalidError` with the message "an unclassified slot is an adaptive-overflow hole" |

| ID      | Rule                                                                                                                                                                                                                                                                                                                                                                                                         |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `IA-25` | **Reservation precedes durable acceptance.** There is no path that accepts an artefact and then looks for a slot                                                                                                                                                                                                                                                                                             |
| `IA-26` | **The reference store's transaction boundary is a `threading.RLock` and a full snapshot restore.** This proves the transaction _logic_ is race-free under the serialisation this store provides. It proves **nothing** about a production datastore, where the same invariants must come from row-level locking or a serialisable isolation level. Demonstrating that is a PACK-17 obligation (`OD-P16D-04`) |

---

## 6. What this document does not decide

```text
What is in and out of scope this round      → PACK-16D-SCOPE-AND-IMPLEMENTATION-BOUNDARY.md
Language and dependency policy               → PACK-16D-LANGUAGE-AND-DEPENDENCY-ASSESSMENT.md
Cryptographic module surfaces and rules      → PACK-16D-CRYPTOGRAPHIC-MODULE-MAP.md
Production datastore isolation               → OD-P16D-04, PACK-17
Cross-mirror gossip                          → OD-P16D-06, PACK-17
Ceremony custody, HSM and authenticated
  channels                                   → OD-P16D-11, PACK-16B, PACK-17
Authorisation of the signer registry itself  → OD-P16D-12, PACK-17
Production authentication surface            → OD-P16D-08, PACK-14, PACK-15, PACK-17
Independent versioning of the reference package → PACK-17, once uv.lock can be regenerated
```

**REFERENCE IMPLEMENTATION. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY.
NOT LEGALLY ACTIVATED.**
