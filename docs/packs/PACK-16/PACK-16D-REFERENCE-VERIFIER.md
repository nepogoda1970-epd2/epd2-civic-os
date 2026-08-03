# PACK-16D — Reference Verifier

**Round:** PACK-16D — Network-Enabled Finalization: Lockfile Regeneration,
Immutable ElectionGuard Provenance and Final Acceptance Alignment.
**Reference implementation. Not production code. Not certified. Not a PASS.**
**Repository version:** unchanged at `0.16.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-102`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 1. Scope

This document describes
`services/voting-service/src/epd2_voting_service/reference/verification/verifier.py`
and `.../verification/results.py`: the boundary that makes the verifier
independent, what it checks, what it returns, and what it does not check.

| ID | Symbol | Role |
| -- | ------ | ---- |
| `RV-01` | `BoardExport` | Bytes-only view of the board: entries, checkpoint tuples, the full `signed_checkpoints`, the declared `signer_registry`, optional consistency proofs |
| `RV-02` | `verify_board(export)` | Checkpoint chain, monotonicity, equivocation, root recomputation, **checkpoint signatures**, consistency |
| `RV-03` | `verify_batches(batches, openings, ctx)` | Cadence, root recomputation, leaf openings |
| `RV-04` | `verify_record(record, board, spoiled_openings=None)` | The whole chain, parameters through the ceremony to the tally |
| `RV-05` | `verify_leaf_inclusion(leaf, path, batch)` | One leaf against one published root |
| `RV-06` | `VerificationResultCode`, `EXIT_CODES`, `NOT_CHECKED` | 26 codes, 26 exit codes, 9 statements of non-coverage |
| `RV-78` | `board_export_from(board)` | The one place a complete export is built, so no caller can assemble a partial one by hand |

This is a *reference* verifier. An independent verifier written by another
party from the specification is a separate obligation and remains **open**.

### 1.1 What this correction changed here: only the signature primitive

**The verifier's behaviour is unchanged.** No result code was added,
removed or renumbered; no `NOT_CHECKED` entry was added or removed; no
check was added to or removed from `checks_run`; the unreachable-code
declaration is the same seven entries; the export shape, the boundary tests
and the equivocation detection are as they were.

What moved is one layer below. The Ed25519 operation that
`publication/checkpoint_signing.py` performs on the verifier's behalf is
now supplied by a vetted library through `crypto/signature_provider.py`
instead of by a hand-written module in this repository, which is deleted.

| ID | Rule |
| -- | ---- |
| `RV-96` | **The signature primitive moved; the verifier did not.** A checkpoint that verified before this correction verifies now, a checkpoint that failed fails with the same code, and the five signature outcomes still map one-to-one onto `RV-82`…`RV-86`. The correction was made because a hand-written primitive is the wrong thing to depend on, not because the verifier was returning wrong answers — the audit passed `CHECKPOINT SIGNATURE SEMANTICS`. Nothing in this document should be read as claiming the verifier got stronger |
| `RV-97` | The primitive's own properties — the port, the six operations, the absence of a fallback, the strict raw encodings, and what is and is not pinned by test about it — belong to `PACK-16D-CHECKPOINT-SIGNATURE-AND-SIGNER-TRUST-MODEL.md` §2 and are not restated here |

## 2. The independent-implementation boundary

A verifier that can reach into the service's private state proves nothing
about what a member of the public could check. The boundary here is that
the verifier consumes **exported bytes and public artefacts only**.

| ID | Rule |
| -- | ---- |
| `RV-07` | **`BoardExport` is a bytes-only view.** `entries` is a tuple of `(sequence, entry_type_value, payload)` and `checkpoints` a tuple of `(sequence, tree_size, root, previous_hash, signature)`. It additionally carries `signed_checkpoints` — the full `Checkpoint` values a signature is taken over — and `signer_registry`, the declared authorised signer set. There is no board object, no store handle and no live query |
| `RV-79` | **The signer registry is a trust anchor supplied alongside the export, never read out of it.** `verify_checkpoint` resolves a checkpoint's `signing_key_id` inside the registry it was given; `CheckpointPayload` has no `public_key` field at all, so there is no path by which a checkpoint can nominate the key that validates it |
| `RV-08` | **The verifier imports no store, continuation, transaction, idempotency or API module.** It has no way to observe a capability, a credential, an identity or an entitlement, because it has no reference to anything that holds one |
| `RV-09` | **The boundary is asserted mechanically, not by convention.** Two tests enforce it; both are in `services/voting-service/tests/reference/test_invariants.py` under the heading "§36 independent implementation boundary" |

### 2.1 The `ast` import check

`test_verifier_imports_no_identity_credential_or_capability_module` parses
**every** `*.py` file under `reference/verification/` with `ast`, walks the
tree, and collects any `Import` or `ImportFrom` node naming one of:

```text
epd2_voting_service.reference.casting.store
epd2_voting_service.reference.casting.continuation
epd2_voting_service.reference.casting.transactions
epd2_voting_service.reference.casting.idempotency
epd2_voting_service.reference.api
```

| ID | Rule |
| -- | ---- |
| `RV-10` | The assertion is `offenders == []`, and the failure message names the file, the line and the module — so a reviewer sees exactly which import broke the boundary |
| `RV-11` | **The check is over the parsed syntax tree, not a text search**, so it catches an import wherever it appears, including inside a function body. The verifier does use function-local imports (`_checkpoint_digest` imports the encoding helpers locally); those are parsed and checked like any other |
| `RV-12` | The check walks `rglob("*.py")`, so a new module added under `verification/` is covered without anyone remembering to add it |

### 2.2 The symbol check

`test_verifier_names_no_capability_or_identity_symbol` reads the text of
every `*.py` under `reference/verification/` and asserts that none of
these four strings appears anywhere in it — not in code, not in a type
annotation, not in a comment, not in a docstring:

```text
capability_reference    credential_id    voter_id    continuation_capability
```

| ID | Rule |
| -- | ---- |
| `RV-13` | **A substring assertion is deliberately blunt.** It fails on a variable name, a dictionary key, a docstring mention or a commented-out line. The point is that the verifier should have no vocabulary for identity at all |
| `RV-14` | The two tests are complementary: the `ast` check catches *reaching* private state through an import, the symbol check catches *naming* an identity concept even without importing anything |
| `RV-15` | `test_verifier_needs_no_store_or_capability` closes the loop behaviourally: it casts a ballot, closes the election, builds a `BoardExport` and calls `verify_record` with the record and the export only — and asserts `VERIFIED` |

## 3. Result codes and exit codes

26 codes, 26 distinct exit codes. `test_every_exit_code_is_distinct_and_stable`
asserts the exit codes are distinct, that `EXIT_CODES` covers exactly
`VerificationResultCode`, and that `VERIFIED` is 0.

| ID | Code | Exit | Meaning as implemented |
| -- | ---- | ---- | ---------------------- |
| `RV-16` | `VERIFIED` | 0 | Every check that ran, passed |
| `RV-17` | `VERIFIED_WITH_WARNINGS` | 1 | Reserved; no reference check emits a warning yet |
| `RV-18` | `INCOMPLETE_RECORD` | 10 | Commitments without openings, a batch cadence gap or duplicate, a spoiled ballot with no published opening, or a decryption share with no tally |
| `RV-19` | `UNSUPPORTED_PROFILE` | 11 | The record names a parameter set the verifier has no declared bit lengths for. Returned by `verify_record` before any other check, because a verifier that does not know a profile cannot say whether a record under it is valid |
| `RV-20` | `INVALID_SCHEMA` | 12 | Unknown or missing critical field |
| `RV-21` | `INVALID_CANONICAL_ENCODING` | 13 | Bytes that do not re-encode canonically |
| `RV-22` | `INVALID_MANIFEST` | 20 | Manifest digest disagreement |
| `RV-23` | `INVALID_PARAMETER_SET` | 21 | `validate_parameter_set()` rejected the record's parameters |
| `RV-24` | `INVALID_CEREMONY` | 22 | The joint public key is not in the subgroup |
| `RV-80` | `INVALID_CEREMONY_TRANSCRIPT` | 23 | The ceremony transcript fails `verify_ceremony`, names another election, or does not derive the record's joint public key |
| `RV-81` | `GUARDIAN_QUORUM_MISMATCH` | 24 | Two shares from one guardian for one tally, or fewer shares than the ceremony's quorum |
| `RV-25` | `INVALID_BALLOT_PROOF` | 30 | A selection or contest-sum proof failed |
| `RV-26` | `INVALID_CHALLENGE_OPENING` | 31 | A spoiled ballot's opening does not re-encrypt to its ciphertext |
| `RV-27` | `BOARD_INCONSISTENCY` | 40 | Rollback, equivocation or a broken checkpoint chain |
| `RV-28` | `BATCH_ROOT_MISMATCH` | 41 | A leaf does not recompute, an opening is short, or a root does not recompute |
| `RV-29` | `BATCH_RECONCILIATION_FAILED` | 42 | Artefact ↔ leaf reconciliation failed |
| `RV-30` | `BATCH_INCLUSION_FAILED` | 43 | A leaf does not prove inclusion against the published commitment root |
| `RV-31` | `BATCH_CONSISTENCY_FAILED` | 44 | A supplied consistency proof failed, or named a tree size with no checkpoint |
| `RV-82` | `BOARD_SIGNATURE_MISSING` | 45 | A checkpoint carries no signature |
| `RV-83` | `BOARD_SIGNER_UNKNOWN` | 46 | The checkpoint's `signing_key_id` does not resolve in the declared signer registry |
| `RV-84` | `BOARD_SIGNER_UNAUTHORIZED` | 47 | The resolved signer is not authorised for this election and board, or is outside its declared activation window |
| `RV-85` | `BOARD_SIGNATURE_INVALID` | 48 | The provider's Ed25519 verification returned `False` over the canonical payload — altered bytes, a replayed signature, or a malformed key or signature |
| `RV-86` | `BOARD_SIGNATURE_CONTEXT_MISMATCH` | 49 | The checkpoint's schema version, election or board does not match the registry it is checked against |
| `RV-32` | `INVALID_DECRYPTION_SHARE` | 50 | A guardian share proof failed, including a threshold share that does not verify against the ceremony commitments |
| `RV-33` | `TALLY_MISMATCH` | 51 | An aggregate does not recompute, or a ballot appears as both spoiled and accepted |
| `RV-34` | `ARCHIVE_CORRUPTION` | 60 | Archive integrity failure |

| ID | Rule |
| -- | ---- |
| `RV-35` | **Exit codes are stable and are never renumbered.** They are grouped by class — 0/1 success, 1x record and profile, 2x election setup and ceremony, 3x ballot, 4x board and batch, 5x tally, 6x archive — so a caller can branch on the decade without parsing text. The seven codes added this round were **appended within their existing decades** (23, 24, 45–49); no previously published code changed value |
| `RV-87` | **The five signature outcomes map one-to-one onto result codes.** `_SIGNATURE_OUTCOME_CODES` in `verification/verifier.py` is that mapping, so a reader of an exit code can tell "nobody signed this" from "the wrong person signed it" from "the bytes were altered" without parsing a detail string |
| `RV-36` | Every failure returns a `VerificationResult` carrying a `detail` string naming what failed and where. The verifier returns rather than raising, so a caller always gets a code |

## 4. `NOT_CHECKED` is printed with every result, including `VERIFIED`

`NOT_CHECKED` is a module-level tuple of nine statements, and
`VerificationResult.not_checked` returns it unconditionally — it is a
property of the result type, not something a caller opts into.

| ID | A `VERIFIED` result did **not** check |
| -- | ------------------------------------ |
| `RV-37` | that a device encrypted the choice its voter intended |
| `RV-38` | that every published ballot came from a distinct real entitlement |
| `RV-39` | that nobody was coerced |
| `RV-40` | that no eligible person was prevented from voting |
| `RV-41` | that guardian key shares were handled correctly after the ceremony |
| `RV-42` | that the parameters are appropriate — **`VO-08` is OPEN** |
| `RV-43` | the per-capability entitlement bound, which is Auditor-restricted evidence |
| `RV-88` | that the authorised signer set itself is the right one — the verifier checks a checkpoint against the signer registry it was given, and cannot tell you that registry was authorised by the Election Board (`OD-P16D-12`) |
| `RV-89` | that the board showed the same checkpoints to everyone — a valid signature proves who issued a checkpoint, never that no other view exists; cross-mirror comparison remains unimplemented (`OD-P16D-06`) |

The entry that used to stand here — "the board operator actually signed
each checkpoint" — was **removed because it is no longer true**: signatures
are verified (`RV-62`). It was replaced by the two narrower statements
above, which are what a verified signature still does not tell you.

| ID | Rule |
| -- | ---- |
| `RV-44` | **The list is attached to the result object, so it cannot be dropped by a caller that only prints the code.** `test_not_checked_is_never_empty_and_names_vo_08` constructs a bare `VERIFIED` result and asserts the list has nine entries, that one of them names `VO-08` and that one of them says the board is not shown to have presented the same checkpoints to everyone |
| `RV-45` | **`VERIFIED` therefore means "these checks passed", never "the election was correct".** The two lists — `checks_run` and `NOT_CHECKED` — are the whole claim; nothing outside them is asserted |
| `RV-46` | The same discipline governs `checks_run`: a check that did not run is not listed. In particular `board.consistency_proofs` is appended only when proofs were supplied and verified, so an unchecked claim never reads as a passed one |

## 5. `checks_run` of a full `VERIFIED` run

A complete `verify_record` run on fixture A reports, in order:

```text
parameter_set
joint_key
ceremony.transcript
ceremony.joint_key_derivation
ceremony.guardian_proofs
ceremony.threshold_shares
manifest
board.checkpoint_chain
board.monotonic_tree_size
board.root_recomputation
board.checkpoint_signatures
batch.cadence
batch.root_recomputation
batch.leaf_openings
batch.inclusion_proofs
ballot_proofs
spoiled_never_counted
decryption_shares
tally_recomputation
```

plus `challenge_openings` when spoiled openings are supplied, and
`board.consistency_proofs` when consistency proofs are supplied. The four
`ceremony.*` entries appear when the record carries a ceremony transcript,
and `ceremony.threshold_shares` only when it also carries threshold shares.

| ID | Check | What it actually does |
| -- | ----- | --------------------- |
| `RV-47` | `parameter_set` | `validate_parameter_set()` on the record's own parameters, with `check_primality=False` and the expected bit widths looked up in `PROFILE_BIT_LENGTHS` by parameter-set id — **not** derived from the parameters themselves. A profile with no declared pair is `UNSUPPORTED_PROFILE` (`RV-19`) |
| `RV-48` | `joint_key` | Subgroup membership of the joint public key |
| `RV-90` | `ceremony.transcript` | `verify_ceremony()` over the record's transcript: parameter set, quorum policy, roster size, guardian sequences `1…n` without gap or duplicate, distinct guardian ids, one commitment per quorum slot, and the election the transcript names |
| `RV-91` | `ceremony.joint_key_derivation` | The joint public key is **re-derived** from the roster's commitments and compared with the record's. It is never accepted standalone |
| `RV-92` | `ceremony.guardian_proofs` | Every guardian's Schnorr proof of possession verifies against its own published commitment |
| `RV-93` | `ceremony.threshold_shares` | For each tallied option: no duplicate guardian, at least the ceremony's quorum of shares, a tally to attach them to, and every share's Chaum–Pedersen proof verified against the public share key derived from the commitments |
| `RV-49` | `manifest` | The manifest is present and self-consistent — see `RV-60`, this is a weak check this round |
| `RV-50` | `board.checkpoint_chain`, `board.monotonic_tree_size`, `board.root_recomputation`, `board.checkpoint_signatures` | Delegated to `verify_board` |
| `RV-51` | `batch.cadence` | Commitments and openings are the same count, and the sequence set is exactly `0…n-1` — no gap, no duplicate |
| `RV-52` | `batch.root_recomputation` | Every opening has exactly `capacity` leaves and recomputes the published `commitment_root` |
| `RV-53` | `batch.leaf_openings` | Every non-cover leaf is recomputed with `real_leaf()` from its opening and compared against the published leaf |
| `RV-54` | `batch.inclusion_proofs` | Every non-cover leaf is re-proved against the root — see `RV-72` |
| `RV-55` | `ballot_proofs` | `verify_ballot_proofs()` over every accepted **and** spoiled envelope |
| `RV-56` | `challenge_openings` | Each spoiled ballot's opening re-encrypts to its published ciphertext; a spoiled ballot with no opening is `INCOMPLETE_RECORD` |
| `RV-57` | `spoiled_never_counted` | The accepted and spoiled ballot-id sets are disjoint |
| `RV-58` | `decryption_shares` | Every share names an existing tally and its Chaum–Pedersen proof verifies |
| `RV-59` | `tally_recomputation` | Every published aggregate is re-accumulated from the accepted ballots and compared componentwise |

| ID | Rule |
| -- | ---- |
| `RV-60` | **The `manifest` check is weak this round and is named as such.** The reference record carries one manifest *object*, so the verifier's digest comparison is a comparison with itself; the branch is marked `# pragma: no cover`. A wire-format verifier that re-parses a manifest from bytes and re-derives its digest is a PACK-17 item. `parse_manifest_from_bytes()` and `parse_envelope_from_bytes()` exist and are tested, but `verify_record` does not route through them |
| `RV-61` | **The verifier recomputes every checkpoint root from the exported entries.** `verify_board` re-derives each entry's leaf digest through its own `_entry_digest` path — a deliberate duplicate of `BoardEntry.digest()` rather than a call to it — rebuilds the root over `entries[:tree_size]`, and returns `BOARD_INCONSISTENCY` if it disagrees or if a checkpoint claims more entries than were exported. Without this, a board could publish a perfectly chained sequence of roots over entries nobody ever saw. The check is reported as `board.root_recomputation` and pinned by `test_checkpoint_roots_are_re_derived_from_the_exported_entries` |
| `RV-62` | **The verifier checks checkpoint signatures.** Checkpoints are Ed25519-signed over the canonical `CheckpointPayload`; `verify_board` resolves each checkpoint's `signing_key_id` in the supplied `SignerRegistry`, refuses a key outside its declared activation window, and verifies the signature, reporting the outcome as one of the five distinct codes of `RV-82`…`RV-86`. A clean pass appends `board.checkpoint_signatures` to `checks_run`, and `test_verifier_checks_signatures_and_says_so` asserts exactly that. The symmetric-HMAC construction of the first candidate, which a third party could not verify at all, was replaced rather than patched; the Ed25519 operation itself is now performed by the vetted provider (`RV-96`) |
| `RV-94` | **The ceremony is verified before anything uses the joint key.** In `verify_record` the ceremony block runs immediately after the joint-key subgroup check and before the manifest, the board, the ballots and the tally — because a key that has not been shown to come from a verified roster must not be relied on by any check downstream of it |
| `RV-95` | **An export without signed checkpoints is `INCOMPLETE_RECORD`, not a weaker check.** The chain digest is taken over the whole signed payload, so an export carrying only the legacy five-tuple view cannot be chain-checked; falling back to a digest covering less than the board actually signed would be a downgrade the verifier could not see. `test_an_export_without_signed_checkpoints_is_incomplete` pins it |

## 6. `verify_leaf_inclusion` — the check a voter's own client runs

```python
def verify_leaf_inclusion(leaf, path, batch) -> VerificationResult:
    """One leaf against one published commitment root."""
```

| ID | Rule |
| -- | ---- |
| `RV-63` | **It needs the leaf, its sibling path and the published batch — not the opening, not the record, and nothing about anyone else's ballot.** That is what makes it runnable by a voter's own client rather than only by a full auditor |
| `RV-64` | Success returns `VERIFIED` with `checks_run == ("batch.leaf_inclusion",)`; failure returns `BATCH_INCLUSION_FAILED`, exit code 43 |
| `RV-65` | `test_batch_inclusion_failed_branch` exercises it in both directions: the real leaf under its own path verifies; a leaf that is not in the batch does not; and a real leaf presented under **another** leaf's path does not |
| `RV-66` | The full-record path also runs a per-leaf inclusion check inside `verify_batches`, but for a *complete* opening that check is mathematically redundant with root recomputation — see `RV-72` |

## 7. Codes not reachable through `verify_record` this round

Seven of the twenty-six codes cannot be returned by `verify_record` in this
round — the same seven as before, none of them added or removed by this
correction. `UNSUPPORTED_PROFILE` was an eighth until the verifier stopped
deriving expected bit lengths from the record it was checking; it now
returns that code for a parameter set it has no declared lengths for. They are declared in
`services/voting-service/tests/reference/test_verifier_branches.py` as
`UNREACHABLE_IN_REFERENCE_VERIFIER`, a dict from code name to reason, and
`test_unreachable_codes_are_declared_and_still_exist` asserts every key is
a real member of `VerificationResultCode` and that every reason is
non-empty. The reasons below are the dict's own text.

| ID | Code | Declared reason |
| -- | ---- | --------------- |
| `RV-67` | `VERIFIED_WITH_WARNINGS` | no reference check emits a warning yet; the code exists so a future check can degrade without renumbering |
| `RV-69` | `INVALID_SCHEMA` | reached by the schema registry; see the negative corpus cases `unknown_critical_field` and `missing_critical_field` |
| `RV-70` | `INVALID_CANONICAL_ENCODING` | reached by the canonical encoder; see the negative corpus cases `non_canonical_integer` and `duplicate_field` |
| `RV-71` | `INVALID_MANIFEST` | the reference record carries one manifest object, so the digest cannot disagree with itself; a wire-format verifier reaching this code is a PACK-17 item |
| `RV-72` | `BATCH_INCLUSION_FAILED` | unreachable through `verify_batches`, because for a complete opening the per-leaf check is redundant with root recomputation; reachable and tested through `verify_leaf_inclusion`, which is the check a voter's own client runs |
| `RV-73` | `BATCH_RECONCILIATION_FAILED` | raised by `reconcile()` as `ReconciliationError` before a record can be built; see the negative corpus cases `duplicate_opening` and `cover_leaf_in_tally` |
| `RV-74` | `ARCHIVE_CORRUPTION` | archive integrity is checked by the packaging step, not by `verify_record`; no reference archive reader exists this round |

| ID | Rule |
| -- | ---- |
| `RV-75` | **Unreachable is not the same as unused.** Four of the seven are reached by another component — the schema registry, the canonical encoder, `reconcile()` and `verify_leaf_inclusion` — and the declaration names which |
| `RV-76` | **The declaration is a test, so it rots loudly.** A code renamed or deleted fails `test_unreachable_codes_are_declared_and_still_exist`; a code that becomes reachable must be removed from the dict by hand, which is a reviewable diff |

The remaining **nineteen** codes are returned by `verify_record`:
`VERIFIED`, `UNSUPPORTED_PROFILE`, `INCOMPLETE_RECORD`,
`INVALID_PARAMETER_SET`, `INVALID_CEREMONY`, `INVALID_CEREMONY_TRANSCRIPT`,
`GUARDIAN_QUORUM_MISMATCH`, `INVALID_BALLOT_PROOF`,
`INVALID_CHALLENGE_OPENING`, `BOARD_INCONSISTENCY`, `BATCH_ROOT_MISMATCH`,
`BATCH_CONSISTENCY_FAILED`, `BOARD_SIGNATURE_MISSING`,
`BOARD_SIGNER_UNKNOWN`, `BOARD_SIGNER_UNAUTHORIZED`,
`BOARD_SIGNATURE_INVALID`, `BOARD_SIGNATURE_CONTEXT_MISMATCH`,
`INVALID_DECRYPTION_SHARE` and `TALLY_MISMATCH`, each covered by a named
branch test in `test_verifier_branches.py`, `test_checkpoint_signatures.py`
or `test_e2e.py`. The five board-signature codes reach `verify_record`
because it returns `verify_board`'s result unchanged.

## 8. What the verifier is not

- **It is not an independent implementation.** It shares the repository's
  crypto, encoding and Merkle modules with the code that produced the
  artefacts. It is independent of *private state*, which is what the two
  boundary tests enforce, and that is a weaker property than an
  independently written verifier. A second implementation by another party
  remains **open**.
- **It establishes no full interoperability.** The 23 internal stability
  vectors remain self-generated and say so in their own `source` field.
  Cross-implementation evidence now exists — an independent Node.js
  verifier, run this round on `EPD2-CRYPTO-1` itself, and an out-of-process
  OpenSSL **command-line** oracle for the signature primitive — but
  agreement with another *complete* ElectionGuard implementation is still
  unestablished (`OD-P16D-02`). The CLI oracle shares an upstream with the
  library the provider links, which is stated wherever it is cited.
- **It cannot tell you the signer registry it was given was authorised.**
  It checks a checkpoint against that registry, not the provenance of the
  registry itself (`OD-P16D-12`, `RV-88`).
- **It does not detect a split view across mirrors.** Equivocation is
  detected only within a single exported view; cross-mirror gossip is not
  implemented (`OD-P16D-06`).
- **It does not verify parameters as appropriate.** `VO-08` is **OPEN**,
  and the verifier says so in `NOT_CHECKED` on every run including
  `VERIFIED`. No BSI conformity is claimed.
- **It claims nothing about timing.** Python big-integer arithmetic is not
  constant-time, and the move of the signature primitive to OpenSSL changes
  nothing the verifier can claim: EPD² has measured no timing behaviour at
  all (`OD-P16D-05`, narrowed and still open).

## 9. What this document does not decide

```text
Independent second implementation                    → PACK-17, external party
Full interoperability with ElectionGuard             → OD-P16D-02, PACK-17
Authorisation of the signer registry itself          → OD-P16D-12, PACK-17
Wire-format re-parsing in the verifier               → PACK-17
Archive reader and archive integrity                 → PACK-17
Cross-mirror split-view detection                    → OD-P16D-06, PACK-17
Parameter appropriateness                            → VO-08, PACK-16B external review
Verification-report publication and governance       → OD-P16C-09, GOVERNANCE
```

**REFERENCE IMPLEMENTATION. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY.
NOT LEGALLY ACTIVATED.**
