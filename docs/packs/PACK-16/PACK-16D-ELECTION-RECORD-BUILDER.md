# PACK-16D — Election Record Builder

**Round:** PACK-16D — Cryptographic Implementation Architecture, Reference
Components, Atomic Persistence, Test Vectors and Verification Harness.
**Reference implementation. Not production code. Not certified. Not a PASS.**
**Repository version:** unchanged at `0.16.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-102`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 1. Scope

This document describes
`services/voting-service/src/epd2_voting_service/reference/election_record/builder.py`:
the no-intermediate-tally gate, homomorphic accumulation and bounded
decode, batch reconciliation, the canonical record and its digest, and
export. PACK-16C specified the election record; this round builds one.

| ID | Symbol | Role |
| -- | ------ | ---- |
| `RB-01` | `open_tally(board_closed)` | The hard gate |
| `RB-02` | `tally_accepted(...)` | Single-guardian accumulation, decryption share, bounded decode |
| `RB-48` | `tally_accepted_threshold(...)` | The multi-guardian path: accumulation, one share per participating guardian, Lagrange combination, bounded decode |
| `RB-03` | `reconcile(...)` | Artefact ↔ leaf reconciliation, fail closed |
| `RB-04` | `ElectionRecord` | The record, its canonical bytes and its digest |
| `RB-05` | `export_record(record)` | Pure serialisation for archival |
| `RB-06` | `GuardianShare`, `ContestTally`, `ReconciliationRecord`, `CeremonyTranscript`, `ThresholdShare` | Record components |

## 2. The tally gate

```python
def open_tally(board_closed: bool) -> None:
    """The hard gate. Called before any tally construction."""
    if not board_closed:
        raise IntermediateTallyProhibitedError(
            "no tally artefact may be constructed before the closure checkpoint"
        )
```

| ID | Rule |
| -- | ---- |
| `RB-07` | **`tally_accepted()` calls `open_tally()` as its first statement.** There is no tally construction path that does not pass the gate |
| `RB-08` | The exception is `IntermediateTallyProhibitedError`, reason code `TALLY_PRE_CLOSURE_PROHIBITED`. Its docstring says "Hard invariant. No feature flag can disable this." |
| `RB-09` | **`no_intermediate_tally` is one of the ten `IMMUTABLE_INVARIANTS`.** A feature flag whose normalised name merely *contains* an invariant name is refused at startup, so `disable_no_intermediate_tally` fails the same way `no_intermediate_tally` does |
| `RB-10` | The board enforces the other half: `TALLY_ARTIFACT` is not in `PRE_CLOSURE_ENTRY_TYPES`, so a result artefact cannot be published before closure even if one existed |

### 2.1 Why the signature takes a bool

`open_tally` takes exactly one positional parameter, `board_closed: bool`.
It reads no configuration object, no feature flag, no environment
variable and no global. This is a deliberate choice about *where the
decision can be made*:

| ID | Rule |
| -- | ---- |
| `RB-11` | **A gate that reads a flag can be opened by whoever can write the flag.** Deployment configuration, an environment variable or a settings service is a second, weaker authority over an invariant that is supposed to be absolute |
| `RB-12` | **A gate that takes a bool can only be opened by a caller that has the closure fact in hand.** In every call site the argument is `board.closed`, which becomes `True` only inside `BulletinBoard.close()` — the same call that appends the `ELECTION_CLOSED` entry |
| `RB-13` | **The invariant therefore lives in code and in the board's state, not in configuration**, which is what makes it reviewable by reading two functions |

The test asserts the shape of the function itself rather than only its
behaviour, so a future edit that reintroduces a flag lookup fails even if
the behaviour still happens to be right:

```python
def test_no_feature_flag_can_reach_the_tally_gate() -> None:
    """`open_tally` takes a bool, not a flag lookup. Assert its shape."""
    signature = inspect.signature(open_tally)
    assert list(signature.parameters) == ["board_closed"]
    source = inspect.getsource(open_tally)
    assert "flag" not in source.lower()
    assert "getenv" not in source and "environ" not in source
```

| ID | Rule |
| -- | ---- |
| `RB-14` | The test inspects **the signature** (exactly one parameter, named `board_closed`) **and the source** (no `flag`, no `getenv`, no `environ`). Adding a second parameter, a default that means "assume closed", or an environment read fails it |
| `RB-15` | `test_tally_construction_is_unavailable_before_closure` covers behaviour in both directions: `open_tally(board_closed=False)` raises, `open_tally(board_closed=True)` returns |
| `RB-16` | `test_e2e_10_pre_closure_tally_attempt` runs the full path — a cast ballot, an open board, a `tally_accepted` call — asserts `reason_code == "TALLY_PRE_CLOSURE_PROHIBITED"`, then asserts no `TALLY_ARTIFACT` entry exists and that the board refuses one |

## 3. Accumulation, decryption share and bounded decode

For each contest of the manifest's ballot style and each option in it,
`tally_accepted()`:

1. gathers the matching ciphertext from every accepted envelope;
2. skips the option entirely if nothing was gathered
   (`accumulate([])` is an error, never an identity element);
3. computes `aggregate = accumulate(gathered, params)` — componentwise
   modular multiplication, with every component subgroup-validated;
4. computes the decryption share `share = aggregate.alpha ** secret mod p`;
5. proves the share correct with a Chaum–Pedersen proof under the context
   built by `decryption_share_context(election_context_id, contest_id,
   option_id)` — a canonical struct, so the share is bound to the contest
   and option it decrypts and does not verify under another option's
   context. The function is exported so the verifier derives the context
   independently instead of being handed one;
6. recovers `g^m` as `aggregate.beta * share^(p-2) mod p` (Fermat
   inversion) and decodes it with `decode_exponent(..., maximum=len(accepted))`.

| ID | Rule |
| -- | ---- |
| `RB-17` | **Accumulation is homomorphic and never decrypts an individual ballot.** Only the aggregate is ever exponentiated with the secret |
| `RB-18` | **`accumulate([])` raises `PlaintextDomainError`.** An empty aggregate that silently returned the identity would tally an empty contest as a valid zero |
| `RB-19` | **The decode is bounded.** `decode_exponent` refuses a `maximum` above `MAX_EXPONENT_SEARCH = 1024` and raises `DecryptionDomainError` if `g^m` does not decode inside the bound. It is a linear search, so it is bounded by construction, not by a timeout |
| `RB-20` | **The bound passed is `len(accepted)`** — a tally cannot decode to more votes than there were accepted ballots. A result outside the bound is an error, never a clamped value |
| `RB-21` | Because `MAX_EXPONENT_SEARCH` is 1024, **the reference tally cannot decode an election with more than 1024 accepted ballots per option.** This is a reference limit, not a protocol limit; a production implementation needs a different decode strategy. It is not a defect in the fixtures, which are far smaller |
| `RB-22` | Every option with no gathered ciphertext produces **no tally row**, rather than a zero row. The verifier's recomputation loop skips the same way |

**Reference simplification, stated plainly:** `tally_accepted()` iterates
`manifest.ballot_styles[0]`. Tallying an election whose contests span more
than one ballot style is **not implemented** this round.

## 4. Two tally paths: threshold, and the single-guardian fixture path

| ID | Statement |
| -- | --------- |
| `RB-23` | **`tally_accepted_threshold()` is the multi-guardian path.** It accumulates as before, then asks each participating guardian for a `ThresholdShare` through `compute_share()`, and combines them with `combine_shares()` — Lagrange interpolation in the exponent — before the bounded decode |
| `RB-24` | **The quorum comes from the ceremony transcript, never from the caller.** `quorum_selection` chooses *which* guardians take part, not *how many* are required; a selection smaller than the transcript's `k` is refused inside `combine_shares()`, which also rejects duplicate guardians, shares for another contest or option, and any share whose proof does not verify. None of those is recoverable by dropping the offending share and continuing |
| `RB-25` | **`tally_accepted()` remains for the non-threshold fixtures.** It takes one `secret` and one `guardian_public` and emits `GuardianShare` values with `guardian_index = 1` as a literal. A record built through it has a single point of decryption trust, and must not be cited as evidence about a ceremony |
| `RB-26` | The ceremony itself — Feldman VSS DKG, the proofs of possession, the quorum policy and the prohibition on compensated decryption — is owned by `PACK-16D-THRESHOLD-GUARDIAN-REFERENCE-IMPLEMENTATION.md`, not by this document |

Both paths rest on the same share-proof shape: a Chaum–Pedersen proof of
correct exponentiation per share, verified independently by the reference
verifier (`verify_decryption_share`, result code
`INVALID_DECRYPTION_SHARE`, exit code 50). The threshold path additionally
checks each share against the public share key **derived from the ceremony
commitments**, so a verifier confirms a guardian's share without ever
seeing that guardian's secret.

## 5. Reconciliation

`reconcile(openings, accepted, spoiled, max_valid_continuations)` walks
every leaf opening of every batch and fails closed.

| ID | Rule | Failure |
| -- | ---- | ------- |
| `RB-27` | **One artefact ↔ one leaf.** An `artifact_reference` seen in two leaves is refused | `ReconciliationError("artefact ... maps to two leaves")` |
| `RB-28` | **No cover leaf enters the tally.** A `COVER` leaf is counted and then skipped before any artefact mapping; it has no reference to map | negative-corpus case `cover_leaf_in_tally` |
| `RB-29` | **Accepted-cast leaves must equal the accepted ballots** exactly | `"accepted-cast leaves do not match accepted ballots"` |
| `RB-30` | **Spoiled leaves must equal the spoiled ballots** exactly | `"spoiled leaves do not match spoiled ballots"` |
| `RB-31` | **Every accepted and spoiled artefact must have a committed leaf** — the artefact id set must be a subset of the referenced set | `"an artefact has no committed leaf"` |
| `RB-32` | **`accepted ≤ E`**, where `E` is `max_valid_continuations` | `"accepted casts exceed E"` |
| `RB-33` | **`spoiled ≤ E × K`.** With `K = 1` this is implemented as a comparison against `max_valid_continuations` | `"public challenges exceed E * K"` |

The result is a `ReconciliationRecord` carrying the three class counts,
`E`, `K` and `A`. `K` and `A` are written as `1` and `1`, matching
`K_PUBLIC_CHALLENGES_PER_CONTINUATION` and
`A_ACCEPTED_CASTS_PER_CONTINUATION`.

`test_reconciliation_reports_every_class` casts one ballot, publicly
challenges another, closes and asserts
`accepted_cast == 1`, `public_challenged_spoiled == 1`,
`cover == batch_capacity - 2`, `E` equal to the plan's value, and
`(k, a) == (1, 1)`.

| ID | Rule |
| -- | ---- |
| `RB-34` | **Reconciliation runs before a record can be built**, so `BATCH_RECONCILIATION_FAILED` is not a code the verifier returns — the builder raises first. This is one of the seven codes declared unreachable through `verify_record` this round |
| `RB-35` | Reconciliation compares **public artefacts against public leaves only**. It never joins a ballot to a capability, a credential or an identity; the restricted count-comparison evidence of PACK-16C `TC-52` is not in this code path |

## 6. Canonical bytes and digest

`ElectionRecord.canonical_bytes()` encodes, in this order and never
sorted:

```text
manifest · parameter_set · joint_public_key · base_hash ·
sealed_batches · accepted_ballots · spoiled_ballots ·
batch_openings · reconciliation · tallies ·
ceremony · threshold_shares · shares
```

`digest()` is `h(ZERO_KEY, ELECTION_RECORD, [canonical_bytes()])`.

| ID | Rule |
| -- | ---- |
| `RB-36` | **Determinism comes from `EPD2-ENC-1`, not from convention**: fixed-width big-endian integers, length-prefixed bytes, NFC-normalised text, ordered structs, duplicate field names rejected, and no map type anywhere |
| `RB-37` | `joint_public_key` is encoded at the full `|p|` width and every group element inside the nested structures likewise, so there is no short form for two implementations to disagree about |
| `RB-38` | `build`-time inputs alone determine the bytes: the record is a frozen dataclass and `canonical_bytes()` reads nothing else |
| `RB-39` | `test_election_record_digest_is_deterministic` asserts `digest() == digest()` and that `export_record(record) == record.canonical_bytes()` |
| `RB-49` | **The record gained `ceremony` and `threshold_shares`, and both are inside `canonical_bytes()`.** `ceremony` is the `CeremonyTranscript` this election's joint key came from, encoded through its own canonical bytes, or an empty `TEXT` when there is none; `threshold_shares` is a sequence of `ThresholdShare` canonical bytes. A record whose ceremony or threshold shares were altered has a different digest, which is what the verifier's ceremony checks then rest on |
| `RB-50` | **The joint public key is a derived quantity and the record says where it came from.** A record carrying a ceremony is verified by re-deriving the joint key from the roster's commitments; a joint key accepted standalone is never treated as evidence of anything |
| `RB-40` | **The digest covers `batch_openings` and `shares`.** Both used to be fields of `ElectionRecord` that `canonical_bytes()` never encoded, so the digest committed to the sealed batches and their roots but not to the opening structures or the decryption shares. Both are now inside the canonical struct — each opening as `batch_sequence`, `leaves`, `openings`, and each share as `contest_id`, `option_id`, `guardian_index`, `guardian_public`, `share`, `proof`. `test_verifier_branches::test_record_digest_covers_the_openings_and_the_shares` drops one leaf opening and one share in turn and asserts the digest changes. Verifying the openings and shares themselves is still `verify_record`'s job; the digest now commits to what it verifies |

## 7. Export is pure

```python
def export_record(record, *, fault_hook=None) -> bytes:
    trip(fault_hook, "during_record_export")
    return record.canonical_bytes()
```

| ID | Rule |
| -- | ---- |
| `RB-41` | **Export mutates nothing.** It has no store handle, writes no file and marks no state; a crash during export loses nothing and the caller simply exports again |
| `RB-42` | The fault point exists so that the property is **demonstrated rather than asserted**: `test_during_record_export_loses_nothing` arms `DURING_RECORD_EXPORT`, catches the injected fault, then re-exports and asserts the bytes equal `record.canonical_bytes()` |
| `RB-43` | Archival packaging — container format, manifest of files, archive digest — is **not implemented**. `ARCHIVE_CORRUPTION` exists as a result code but no reference archive reader exists this round |

## 8. Order of operations at closure

`testing/scenarios.close_and_build()` performs the ordinary happy path,
and its order is load-bearing:

| ID | Step |
| -- | ---- |
| `RB-44` | Seal the batch and publish `SEALED_BATCH_COMMITMENT` **before** closure |
| `RB-45` | Publish a checkpoint, then `close()` — the `ELECTION_CLOSED` entry fixes the tallied set |
| `RB-46` | Only then publish `SEALED_BATCH_OPENING`, checkpoint again, and construct the tally with `board_closed=board.closed` |
| `RB-47` | Reconcile, then build the `ElectionRecord` |

Reversing any of this is exactly what the no-intermediate-tally tests
attack.

## 9. What is not implemented

- **Production key custody for the ceremony** — shares are exchanged
  in-process, with no authenticated channel, no HSM and no air gap
  (`OD-P16D-11`).
- **Multi-ballot-style tallying** — the first ballot style only.
- **Archive packaging and archive integrity checking** (`RB-43`).
- **Any judgement that the parameters are appropriate** — `EPD2-CRYPTO-1`
  loads and records can be built on it, but `production_use_permitted` is
  `False` on every profile and `VO-08` remains **OPEN**.
- **Constant-time arithmetic** — Python `int` and `pow()` offer no
  side-channel guarantee (`OD-P16D-05`).
- **Full interoperability** — the internal stability vectors are
  self-generated, and agreement with another complete implementation is
  unestablished (`OD-P16D-02`).

## 10. What this document does not decide

```text
Threshold ceremony mechanics and quorum policy       → PACK-16D-THRESHOLD-GUARDIAN-REFERENCE-IMPLEMENTATION.md
Key ceremony execution and custody                   → PACK-16B, OD-P16D-11, GOVERNANCE
Archive container format and retention               → OD-P16A-07, PACK-09/PACK-17
Production decode strategy above the bounded search  → PACK-17
Certification of a record                            → PACK-16C governance, GOVERNANCE
```

**REFERENCE IMPLEMENTATION. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY.
NOT LEGALLY ACTIVATED.**
