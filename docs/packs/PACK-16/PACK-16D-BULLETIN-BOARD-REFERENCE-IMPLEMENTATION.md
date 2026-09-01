# PACK-16D — Bulletin Board Reference Implementation

**Round:** PACK-16D — Cryptographic Implementation Architecture, Reference
Components, Atomic Persistence, Test Vectors and Verification Harness.
**Reference implementation. Not production code. Not certified. Not a PASS.**
**Repository version:** unchanged at `0.16.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-102`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 1. Scope

This document describes the append-only bulletin board implemented in
`services/voting-service/src/epd2_voting_service/reference/publication/bulletin_board.py`
and the board checks in
`services/voting-service/src/epd2_voting_service/reference/verification/verifier.py`.
PACK-16A and PACK-16C specified the board's requirements and entry
catalogue; this round implements a subset of them and says which parts it
does not implement.

| ID      | Rule                                                                                                                                                                                                                                                                                                                  |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `BB-01` | **A Python list is not the append-only guarantee.** The guarantee is that every published checkpoint is chained, carries a Merkle root over the entries at a declared tree size, and can be re-derived by a party holding only the export. The module's own docstring says this, and the verifier is what enforces it |

## 2. Entry-type catalogue as implemented

`EntryType` is a `StrEnum` with twelve members. The reference board
implements a subset of PACK-16C's `BE-*` catalogue; a `BE-*` entry with no
row below is **not implemented this round**.

| ID      | `EntryType` member            | Wire value                    | Allowed before closure              |
| ------- | ----------------------------- | ----------------------------- | ----------------------------------- |
| `BB-02` | `ELECTION_MANIFEST`           | `election_manifest`           | yes                                 |
| `BB-03` | `PARAMETER_SET`               | `parameter_set`               | yes                                 |
| `BB-04` | `JOINT_PUBLIC_KEY`            | `joint_public_key`            | yes                                 |
| `BB-05` | `SEALED_BATCH_COMMITMENT`     | `sealed_batch_commitment`     | yes                                 |
| `BB-06` | `INCIDENT_NOTICE`             | `incident_notice`             | yes                                 |
| `BB-07` | `BOARD_CHECKPOINT`            | `board_checkpoint`            | yes                                 |
| `BB-08` | `SEALED_BATCH_OPENING`        | `sealed_batch_opening`        | **no**                              |
| `BB-09` | `BATCH_RECONCILIATION_RECORD` | `batch_reconciliation_record` | **no**                              |
| `BB-10` | `BALLOT_ACCEPTED`             | `ballot_accepted`             | **no**                              |
| `BB-11` | `BALLOT_SPOILED`              | `ballot_spoiled`              | **no**                              |
| `BB-12` | `TALLY_ARTIFACT`              | `tally_artifact`              | **no**                              |
| `BB-13` | `ELECTION_CLOSED`             | `election_closed`             | **no** — appended only by `close()` |

`PRE_CLOSURE_ENTRY_TYPES` is a `frozenset` of the six types marked "yes":
`ELECTION_MANIFEST`, `PARAMETER_SET`, `JOINT_PUBLIC_KEY`,
`SEALED_BATCH_COMMITMENT`, `INCIDENT_NOTICE`, `BOARD_CHECKPOINT`.

A `BoardEntry` carries three fields — `sequence`, `entry_type`, `payload`
— and its digest is `h(ZERO_KEY, BOARD_ENTRY, [canonical_bytes()])`. There
is no timestamp field, no author field and no size-varying metadata.

## 3. The pre-closure allow-list, and how it is tested

```python
if not self.closed and entry_type not in PRE_CLOSURE_ENTRY_TYPES:
    raise PreClosurePublicationError(
        f"{entry_type.value} may not be published before closure"
    )
```

| ID      | Rule                                                                                                                                                                                                                                         |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `BB-14` | **The check is an allow-list, not a deny-list.** A new `EntryType` member is refused before closure until someone adds it to `PRE_CLOSURE_ENTRY_TYPES` — so the failure mode of forgetting to classify an entry type is refusal, not leakage |
| `BB-15` | The exception is `PreClosurePublicationError`, reason code `PUBLICATION_UNSCHEDULED_BATCH_PROHIBITED`                                                                                                                                        |
| `BB-16` | **`ELECTION_CLOSED` is not appended through `append()`.** `close()` constructs the entry directly and sets `closed = True`, so closure is the one transition the allow-list cannot be asked to permit                                        |
| `BB-17` | **After closure the allow-list no longer applies** — `not self.closed` is the guard. Post-closure publication order is enforced by the caller, not by the board                                                                              |

The test is exhaustive over entry types, not a sample:

```python
@pytest.mark.parametrize(
    "entry_type",
    sorted(set(EntryType) - PRE_CLOSURE_ENTRY_TYPES - {EntryType.ELECTION_CLOSED}),
)
def test_every_post_closure_entry_type_is_refused_before_closure(entry_type): ...
```

| ID      | Rule                                                                                                                                                                                                                                                                                            |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `BB-18` | **The parametrisation is computed as a set difference over `EntryType`, so adding a post-closure entry type automatically adds a test case.** It covers every post-closure type except `ELECTION_CLOSED`, which `append()` is never asked to publish (`BB-16`)                                  |
| `BB-19` | `test_pre_closure_entry_types_exclude_every_result_artifact` separately names `TALLY_ARTIFACT`, `SEALED_BATCH_OPENING`, `BATCH_RECONCILIATION_RECORD`, `BALLOT_ACCEPTED` and `BALLOT_SPOILED` as post-closure-only, so a future edit that quietly moves one into the allow-list fails two tests |
| `BB-20` | `test_turnout_and_accepted_enumeration_are_not_exported_pre_closure` submits three ballots, publishes a manifest entry and a checkpoint, and asserts the export contains no `ballot_accepted` entry and that **no accepted ballot id appears as a substring of any exported payload**           |
| `BB-21` | `test_e2e_10_pre_closure_tally_attempt` asserts both halves of the invariant: the tally gate raises, and the board still refuses `TALLY_ARTIFACT` if asked directly                                                                                                                             |

## 4. Checkpoints: chained and Ed25519-signed

```text
Checkpoint = ( checkpoint_sequence, tree_size, root,
               previous_checkpoint_hash, signature,
               signing_key_id, board_id, election_context_id,
               protocol_profile_id, publication_phase, schema_version )

canonical_bytes = STRUCT( schema_version           : TEXT
                          protocol_profile_id      : TEXT
                          election_context_id      : TEXT
                          board_id                 : TEXT
                          checkpoint_sequence      : UINT(8)
                          tree_size                : UINT(8)
                          root                     : BYTES
                          previous_checkpoint_hash : BYTES
                          publication_phase        : TEXT
                          signing_key_id           : TEXT )

digest        = h(ZERO_KEY, BOARD_CHECKPOINT, [canonical_bytes])
signing_input = the same digest
signature     = Ed25519(signing_seed, signing_input)
```

| ID      | Rule                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `BB-22` | **The chain starts at 32 zero bytes.** The first checkpoint's `previous_checkpoint_hash` is `b"\x00" * 32`; every later one carries its predecessor's `digest()`, which is now taken over the whole signed payload                                                                                                                                                                                                                                                                                        |
| `BB-23` | **The signature is over the unsigned canonical bytes and is not part of them**, so the digest a successor chains to does not depend on the signature                                                                                                                                                                                                                                                                                                                                                      |
| `BB-24` | `root` is `merkle_root([e.digest() for e in entries])` at the moment of publication, and `tree_size` is the entry count at that moment                                                                                                                                                                                                                                                                                                                                                                    |
| `BB-25` | `root_at(tree_size)` recomputes the root the board _would_ have published at any earlier size, which is what makes an independent consistency check possible                                                                                                                                                                                                                                                                                                                                              |
| `BB-51` | **The signature binds ten named fields**, listed above. Every value a replay could vary is inside the payload: the schema, the protocol profile, the election, the board, the sequence, the size, the root, the chain link, the publication phase and the key identifier. `CHECKPOINT_SCHEMA_VERSION = "EPD2-CHECKPOINT-2"`, and `test_the_payload_binds_every_field_the_specification_lists` asserts that every one of those ten names appears in the canonical bytes, and that those bytes are not JSON |
| `BB-52` | **The payload is canonical binary tuples, never JSON**, and `signing_input()` is domain-separated under `BOARD_CHECKPOINT`, so a signature over some other EPD² structure can never be presented as a checkpoint signature                                                                                                                                                                                                                                                                                |
| `BB-53` | **The board carries `board_id`, `signing_key_id` and `protocol_profile_id`** as fields of `BulletinBoard`, and `signer_record()` / `signer_registry()` publish this board's own entry in a `SignerRegistry`. `export_signed_checkpoints()` returns the full checkpoints, which is what signature verification needs; `export_checkpoints()` remains as the legacy five-tuple view                                                                                                                         |
| `BB-54` | **The public key is never carried by the artefact it signs.** `CheckpointPayload` has no `public_key` field; a verifier resolves `signing_key_id` in a registry it was given separately, and `test_a_signer_registry_is_never_read_from_the_checkpoint` asserts there is no such path                                                                                                                                                                                                                     |

**Signing is Ed25519** — RFC 8032 PureEdDSA over edwards25519 with
SHA-512, supplied by a **vetted library** through
`crypto/signature_provider.py`. It is not implemented in this repository:
the round before this one wrote the curve arithmetic here, an audit failed
it, and `crypto/ed25519.py` was deleted rather than improved. The board
therefore calls `PROVIDER.generate_test_keypair()` for its own public key
and `sign_checkpoint()` for each checkpoint, and holds a **TEST-ONLY**
32-byte key derived from its `signing_key` fixture string.

Two earlier constructions were each replaced rather than patched, and for
different reasons worth keeping apart. The symmetric HMAC came first: only
a holder of the board's own key could check it, and a signature nobody
outside the board can verify is not authenticity. The hand-written Ed25519
came second: it was verifiable by anyone and still wrong to ship, because a
from-scratch elliptic-curve implementation carries the vulnerability classes
its author did not think of.

What remains a production obligation is key custody — the reference board
holds a test key, not an HSM (`OD-P16D-11`) — and, per PACK-16A/16C, mirror
signatures, which are **not implemented this round**.

## 5. Inclusion and consistency proofs (RFC 6962)

`crypto/merkle.py` follows RFC 6962 §2.1: the empty tree is a defined
value, a one-leaf tree is its leaf hash, and an n-leaf tree splits at the
largest power of two strictly below n.

| ID      | Rule                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `BB-26` | **The earlier draft duplicated the last node on odd levels and was replaced, not patched.** Last-node duplication lets two different leaf sequences share a root (the CVE-2012-2459 shape). `test_merkle_shape_is_not_last_node_duplication` asserts `root([a,b,c]) != root([a,b,c,c])`                                                                                                                                                                              |
| `BB-27` | **RFC 6962's 0x00/0x01 prefix is carried by the domain-separation label instead**: leaves hash under `BATCH_LEAF`, internal nodes under `BATCH_ROOT`. The separation property is the same — no internal node can be reinterpreted as a leaf — and it is enforced through one registry rather than two conventions. **The digests are therefore EPD²'s, not byte-compatible with an RFC 6962 log**; interoperability with any other log implementation is not claimed |
| `BB-28` | The tree is unkeyed (`ZERO_KEY`). Secrecy of a leaf's content comes from the salt inside the leaf preimage, not from the tree                                                                                                                                                                                                                                                                                                                                        |
| `BB-29` | `inclusion_proof()` returns `(side_of_sibling, digest)` pairs from the leaf upwards; `verify_inclusion()` walks them and rejects an unknown side                                                                                                                                                                                                                                                                                                                     |
| `BB-30` | `consistency_proof(leaves, old_size)` implements RFC 6962 §2.1.2 and rejects `old_size` outside `(0, n]`                                                                                                                                                                                                                                                                                                                                                             |
| `BB-31` | **`verify_consistency()` is the standard iterative algorithm, deliberately not a mirror of the prover's recursion.** A verifier that re-ran the prover's own recursion would agree with the prover by construction and would prove nothing. It also re-inserts the omitted old root when `old_size` is a power of two                                                                                                                                                |
| `BB-32` | The construction is verified exhaustively for every tree size 1…32 and every `(old, new)` pair                                                                                                                                                                                                                                                                                                                                                                       |

`BulletinBoard.consistency_proof(old_tree_size)` and
`ReferenceApi.check_consistency(old_tree_size)` expose this;
`test_e2e_08c_consistency_proof_holds_across_appends` proves an old root
is a prefix of the current one after three further appends and asserts a
tampered old root does **not** verify.

## 6. What `verify_board` detects

`verify_board(export)` takes a `BoardExport` — a bytes-only view of
entries, checkpoints and optional consistency proofs — and walks the
checkpoint list once.

| ID      | Detected                                                                        | How                                                                                                                                               | Result code                                                                                                                                       | Exit  |
| ------- | ------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- | ----- |
| `BB-33` | **Rollback**                                                                    | a checkpoint whose `tree_size` is below the highest seen                                                                                          | `BOARD_INCONSISTENCY`                                                                                                                             | 40    |
| `BB-34` | **Equivocation**                                                                | two different roots published at the same `tree_size`                                                                                             | `BOARD_INCONSISTENCY`                                                                                                                             | 40    |
| `BB-35` | **Broken chain**                                                                | `previous_checkpoint_hash` does not equal the recomputed digest of the preceding checkpoint                                                       | `BOARD_INCONSISTENCY`                                                                                                                             | 40    |
| `BB-36` | **Failed consistency**                                                          | a supplied proof does not verify, or names a tree size with no published checkpoint                                                               | `BATCH_CONSISTENCY_FAILED`                                                                                                                        | 44    |
| `BB-50` | **A root over entries nobody saw**                                              | the root re-derived from `export.entries[:tree_size]` does not equal the published root, or the checkpoint claims more entries than were exported | `BOARD_INCONSISTENCY`                                                                                                                             | 40    |
| `BB-55` | **An unsigned, unknown, unauthorised, forged or context-mismatched checkpoint** | `verify_checkpoint()` against the supplied `SignerRegistry`                                                                                       | `BOARD_SIGNATURE_MISSING` / `BOARD_SIGNER_UNKNOWN` / `BOARD_SIGNER_UNAUTHORIZED` / `BOARD_SIGNATURE_INVALID` / `BOARD_SIGNATURE_CONTEXT_MISMATCH` | 45–49 |
| `BB-56` | **Equivocation by an _authorised_ signer**                                      | two **validly signed** checkpoints at one sequence carrying different roots                                                                       | `BOARD_INCONSISTENCY`                                                                                                                             | 40    |
| `BB-57` | **An export with checkpoint tuples but no signed checkpoints**                  | the chain is computed over the signed payload and cannot be checked without it; there is no fallback to a weaker digest                           | `INCOMPLETE_RECORD`                                                                                                                               | 10    |

A clean run appends `board.checkpoint_chain`,
`board.monotonic_tree_size`, `board.root_recomputation` and — when a
signer registry and signed checkpoints were supplied —
`board.checkpoint_signatures` to `checks_run`.

**Authenticity and consistency remain separate properties.** A valid
signature proves that the named authorised signer issued a checkpoint. It
proves nothing about whether the board showed the same checkpoint to
everyone. `test_conflicting_signed_checkpoints_detected` constructs exactly
the hard case — two checkpoints at one sequence with different roots, both
signatures **genuine**, both from the authorised signer — and asserts
`BOARD_INCONSISTENCY` rather than a signature success, because equivocation
by an authorised signer is worse than a forgery, not better.
`test_a_valid_signature_is_not_evidence_of_a_single_view` states the same
property from the other direction.

`test_e2e_08_board_equivocation` builds an export containing an honest
checkpoint and a forged one with the same sequence and tree size but a
different root, and asserts `BOARD_INCONSISTENCY` with exit code 40.
`test_e2e_08b_rollback_is_detected` appends a later checkpoint followed by
one at a smaller tree size and asserts the same code.

### 6.1 What `verify_board` does not check — stated plainly, not in a note

| ID      | Not checked                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `BB-37` | **That the signer registry it was given is the right one.** Checkpoint signatures _are_ verified (`BB-55`), against the `SignerRegistry` supplied alongside the export. The verifier cannot tell you that the Election Board authorised that registry; establishing the registry's own provenance is outside its reach and is carried as `OD-P16D-12`. This is one of the nine `NOT_CHECKED` entries printed with every result including `VERIFIED`. The other is that a valid signature is never evidence of a single view (`BB-44`)                                                                                      |
| `BB-38` | **Checkpoint roots are recomputed from the exported entries** — this was previously not done, leaving `BoardExport.entries` unread and letting a board publish a perfectly chained sequence of roots over entries nobody saw. `verify_board` now re-derives each entry's leaf digest through its own `_entry_digest` path, rebuilds the root over `entries[:tree_size]`, compares it with the published root, and rejects a checkpoint claiming more entries than were exported (`BB-50`). What remains unchecked here is _which_ entries the board chose to export, and whether they were published on schedule (`BB-39`) |
| `BB-39` | **Nothing checks that a checkpoint was published on schedule**, or that the cadence was not adapted to load. The cadence rules of PACK-16C `BE-29` are not implemented                                                                                                                                                                                                                                                                                                                                                                                                                                                     |

## 7. Absence of a consistency proof never reads as a passed check

`BoardExport.consistency_proofs` defaults to the empty tuple.

```python
if export.consistency_proofs:
    ...
    checks.append("board.consistency_proofs")
```

| ID      | Rule                                                                                                                                                                                                                                                                                                                                |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `BB-40` | **`board.consistency_proofs` is appended to `checks_run` only when at least one proof was supplied and every supplied proof verified.** An export with no proofs still returns `VERIFIED`, but its `checks_run` does not contain the string — so a reader of the result cannot mistake "nothing was claimed" for "the claim passed" |
| `BB-41` | This is enforced by `test_a_board_export_without_proofs_claims_no_consistency_check`, whose whole purpose is the negative assertion `"board.consistency_proofs" not in verdict.checks_run`                                                                                                                                          |
| `BB-42` | `test_board_consistency_proofs_are_checked_when_supplied` covers the positive direction and two failures: a corrupted proof, and a proof naming a tree size at which no checkpoint was published. Both yield `BATCH_CONSISTENCY_FAILED`, exit code 44                                                                               |
| `BB-43` | The same discipline is why the verifier prints `NOT_CHECKED` with every result, including `VERIFIED` — see the reference-verifier document                                                                                                                                                                                          |

## 8. Cross-mirror split-view detection is not implemented

A single exported view can be internally consistent and still be a lie:
an operator can show one view to one population and a different view to
another. Detecting that requires gossip between verifiers, mirrors or
witnesses.

| ID      | Statement                                                                                                                                                                                                                        |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `BB-44` | **PACK-16D detects equivocation only _within a single exported view_** — two different roots at one tree size in one export. It does **not** detect a split view across mirrors, and no PACK-16D document may claim that it does |
| `BB-45` | **Cross-mirror gossip is not implemented.** There is no witness protocol, no mirror cross-signing, no verifier-to-verifier exchange and no client-side checkpoint pinning in this round                                          |

The reason is that the standards landscape is unsettled, which PACK-16C
recorded as evidence `G-01`…`G-05`:

| Evidence      | Finding                                                                                                                                                                                              |
| ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `G-01`…`G-05` | RFC 9162 §11.3 places gossip out of scope; RFC 6962 §5 defers it; `draft-ietf-trans-gossip-05` expired in 2020; the C2SP `tlog-witness` work is the current direction and is not a ratified standard |

Implementing a bespoke gossip protocol against an unsettled standard would
produce a mechanism nobody else can verify against and that would have to
be replaced. The honest position is to implement within-view equivocation
detection, state the residual exposure, and carry it as an open decision:
this is `OD-P16D-06`. The corresponding threat — an operator serving
divergent views — remains **open** in the PACK-16A/16C threat model and is
not mitigated by this round.

## 9. Board privacy properties that are implemented

| ID      | Property                                                                                                                                                                                                                                                                                                           | Evidence                                                                                          |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------- |
| `BB-46` | No pre-closure entry type carries a count of accepted ballots                                                                                                                                                                                                                                                      | `BB-20`; the pre-closure allow-list contains no ballot or result type                             |
| `BB-47` | A sealed batch commitment's serialised size does not vary with occupancy                                                                                                                                                                                                                                           | `TC-33`, measured in the sealed-batch document                                                    |
| `BB-48` | An incident notice publishable before closure names no capability, no ballot and no count                                                                                                                                                                                                                          | `test_e2e_07_capacity_exhaustion` publishes the constant payload `b"election.capacity_exhausted"` |
| `BB-49` | The export is public artefacts only — `export_entries()` returns `(sequence, entry_type_value, payload)`, `export_checkpoints()` returns five-tuples of ints and bytes, and `export_signed_checkpoints()` returns frozen `Checkpoint` values carrying no key material. The verifier never touches the board object | `test_board_export_is_bytes_only`                                                                 |

## 10. What this document does not decide

```text
Mirror signatures and operator key custody           → PACK-16A/16C requirements, PACK-17
Authorisation of the signer registry itself          → OD-P16D-12, PACK-17
Cross-mirror gossip / split-view detection           → OD-P16D-06, PACK-17
Checkpoint interval and publication cadence          → OD-P16C-10, GOVERNANCE
Root re-derivation from exported entries in the verifier → done this round, see BB-38
Mirror topology, hosting and availability            → PACK-16C architecture, GOVERNANCE
Retention of board entries                           → OD-P16A-07, PACK-09/PACK-17
```

**REFERENCE IMPLEMENTATION. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY.
NOT LEGALLY ACTIVATED.**
