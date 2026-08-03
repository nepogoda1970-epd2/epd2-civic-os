# PACK-16D — Sealed Batch Implementation

**Round:** PACK-16D — Cryptographic Implementation Architecture, Reference
Components, Atomic Persistence, Test Vectors and Verification Harness.
**Reference implementation. Not production code. Not certified. Not a PASS.**
**Repository version:** unchanged at `0.16.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-102`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 1. Scope and the modules this document describes

PACK-16C specified fixed-capacity sealed batches (`TC-27`…`TC-45`,
`TC-59`…`TC-77`) but deliberately left the commitment construction, the
opening format and the capacity arithmetic to PACK-16D. This document
states what the reference implementation actually does.

| ID | Module (under `services/voting-service/src/epd2_voting_service/reference/`) | Role |
| -- | ---- | ---- |
| `SE-01` | `publication/sealed_batches.py` | `LeafClass`, `LeafOpening`, `real_leaf()`, `cover_leaf()`, `new_salt()`, `SealedBatch`, `BatchOpening` |
| `SE-02` | `publication/sealing.py` | `seal_batch()` — turns committed reservations into a full batch |
| `SE-03` | `publication/capacity.py` | `CapacityPlan`, `SlotClass`, `K`, `A`, `l_max`, `validate()` |
| `SE-04` | `casting/store.py` | `reserve_leaf()` compare-and-set, the two exhaustion errors |
| `SE-05` | `casting/transactions.py` | `_candidate_slots()` — which slots a cast or a challenge may take |
| `SE-06` | `crypto/merkle.py` | The RFC 6962 tree the commitment root is computed over |

This is reference code. It is not production code and has not been
externally reviewed.

## 2. The three leaf classes

`LeafClass` is a `StrEnum` with exactly three members. There is no fourth
class, and no class that exists only under load.

| ID | Leaf class | Value | Committed to | Opened at closure |
| -- | ---------- | ----- | ------------ | ----------------- |
| `SE-07` | `ACCEPTED_CAST` | `"accepted_cast"` | An accepted encrypted ballot's canonical digest | Yes — salt, reference and digest |
| `SE-08` | `PUBLIC_CHALLENGED_SPOILED` | `"public_challenged_spoiled"` | A publicly challenged, spoiled ballot's canonical digest | Yes — salt, reference and digest |
| `SE-09` | `COVER` | `"cover"` | Nothing | Yes, as its value — there is nothing else to reveal |

| ID | Rule |
| -- | ---- |
| `SE-10` | **A cast leaf and a challenge leaf are constructed by the same function with the same shape.** `real_leaf()` takes the leaf class inside the opening struct, so the two differ only in a field that is not public until closure. Nothing in the published commitment distinguishes them (`TC-57`) |
| `SE-11` | **Leaf class is decided by which artefact map holds the reservation's `submission_reference`**, not by any caller-supplied label: `seal_batch()` reads `store.accepted_ballots` first and falls through to `store.spoiled_ballots` |

## 3. The real leaf is a hiding commitment under a 32-byte salt

`real_leaf(election_context_id, batch_sequence, opening)` returns

```text
h(ZERO_KEY, BATCH_LEAF, [ STRUCT(
    election_context_id : TEXT
    batch_sequence      : UINT(8)
    opening             : LeafOpening.canonical_bytes()
) ])
```

where `h` is `HMAC-SHA-256` under the domain-separation registry
(`EPD2-DS-1`) and the opening is

```text
LeafOpening.canonical_bytes() = STRUCT(
    leaf_index         : UINT(4)
    leaf_class         : TEXT
    salt               : BYTES
    artifact_reference : TEXT
    artifact_digest    : BYTES
)
```

| ID | Rule |
| -- | ---- |
| `SE-12` | **The salt is `SALT_BYTES = 32` bytes drawn from the injected `RandomSource`** (`new_salt()`). It is the hiding term: without it, a leaf would be a deterministic function of a ballot digest and an observer holding a candidate digest could test membership before closure |
| `SE-13` | **The leaf digest is `DIGEST_BYTES = 32` bytes and is never truncated.** `crypto/hashing.py` has no truncation path |
| `SE-14` | **The commitment is bound to its position and its election.** `election_context_id`, `batch_sequence` and `leaf_index` are inside the preimage, so a leaf lifted from one batch, one index or one election does not recompute in another |
| `SE-15` | **The salt is published only in the closure opening.** Before closure the salt exists only in the sealing step's output, which is not a pre-closure board entry |

Hiding is claimed at the level of construction: a 32-byte uniform salt
inside an HMAC-SHA-256 preimage. **No formal indistinguishability proof
was produced this round**, and none is claimed.

## 4. The cover leaf is uniform random bytes, and has no opening

```python
def cover_leaf(source: RandomSource) -> bytes:
    """A uniform random value of the leaf's exact size. Not a hash of anything."""
    return source.random_bytes(DIGEST_BYTES)
```

| ID | Rule |
| -- | ---- |
| `SE-16` | **A cover leaf is 32 uniform random bytes. It is not a hash of anything** — not of a null artefact, not of a padding constant, not of its index. There is therefore no preimage anyone can be compelled to produce, and no oracle that distinguishes "cover" from "real" by testing a guess |
| `SE-17` | **A cover leaf has no opening.** `seal_batch()` records it as `LeafOpening(leaf_class=COVER, salt=b"", artifact_reference="", artifact_digest=b"")` — an empty salt, an empty reference and an empty digest. The struct exists so that the opening covers every index in order; it commits to nothing |
| `SE-18` | **The verifier skips cover leaves when recomputing leaves and re-proving inclusion.** `verify_batches()` `continue`s on `LeafClass.COVER` in both loops. A cover leaf is checked only by the root recomputation over the full leaf vector |
| `SE-19` | **A cover leaf never enters the tally.** `reconcile()` counts it and then `continue`s before the artefact-mapping checks; `cover_leaf_in_tally` is a named negative-corpus case |

Because a cover leaf is drawn from the same `RandomSource` as the salts,
a randomness failure during sealing surfaces through the same fail-closed
path as everywhere else (`RandomnessUnavailableError`); it never degrades
to a weaker source.

## 5. Fill to capacity

`seal_batch()` iterates `range(capacity)` — not over the reservations —
and asks, for each index, whether a *committed* reservation claims it:

| ID | Rule |
| -- | ---- |
| `SE-20` | **Every unused slot becomes a cover leaf.** A batch is always exactly `capacity` leaves, whatever the occupancy |
| `SE-21` | **Only committed reservations produce a real leaf.** The filter is `r.batch_sequence == batch_sequence and r.committed`; a reservation taken by a transaction that did not commit contributes nothing and its slot is covered |
| `SE-22` | **Leaves are emitted in leaf-index order**, so the opening and the commitment agree on order by construction rather than by a sort |
| `SE-23` | **The commitment root is `merkle_root(leaves)` over exactly `capacity` leaves**, and an empty leaf list is refused (`BatchIntegrityError`, "a batch must have at least one leaf") |
| `SE-46` | **An over-full batch is refused before it is sealed.** Before building any leaf, `seal_batch()` compares the committed reservations for this batch against `capacity` and raises `CapacityExhaustedError` (`BULLETIN_BOARD_BATCH_CAPACITY_EXHAUSTED`) if there are more of them than there are leaves, or if any claims a leaf index at or above `capacity`. Reaching this is a defect upstream, not a condition to absorb: sealing is the last point at which the alternative — quietly dropping a committed reservation, and with it an accepted ballot — could still happen. `test_verifier_branches::test_capacity_exhaustion_is_caught_at_sealing_time` pins it |

`SealedBatch` — the published commitment — carries six fields:
`election_context_id`, `batch_sequence`, `batch_window_id`,
`fixed_capacity_profile_id`, `capacity` and `commitment_root`. There is no
occupancy field, no count, no bitmap and no list.

## 6. Constant size (`TC-33`), and the test that measures it

`TC-33` requires that a published batch not distinguish an empty batch
from a full one. In this implementation the property follows from three
facts: every leaf is exactly 32 bytes; the leaf count is always
`capacity`; and `SealedBatch.canonical_bytes()` uses fixed-width,
length-prefixed encoding over a fixed field list.

`test_sealed_batch_size_is_independent_of_occupancy` in
`services/voting-service/tests/reference/test_casting_units.py` measures
it rather than asserting it. The test:

1. builds fixture A and seals a batch with **no** submissions;
2. builds a second fixture A, submits **four** cast ballots through
   `submit_cast_ballot`, and seals a batch with the same capacity;
3. asserts `len(empty_batch.canonical_bytes()) == len(busy_batch.canonical_bytes())`;
4. asserts `len(empty_opening.leaves) == len(busy_opening.leaves)`;
5. asserts every leaf of both batches has the same length —
   `len({len(leaf) for leaf in (*empty_opening.leaves, *busy_opening.leaves)}) == 1`;
6. asserts the two roots **differ**, so equal size is not equal content.

| ID | Rule |
| -- | ---- |
| `SE-24` | **The size test compares an empty batch against a four-ballot batch, not two empty ones.** A size-invariance test that never varies occupancy proves nothing |
| `SE-25` | `test_cover_leaves_fill_every_unused_slot` separately asserts that one cast ballot yields exactly one `ACCEPTED_CAST` leaf and `capacity - 1` `COVER` leaves, and that the opening recomputes the published root |

What this does **not** show: it does not measure the size of a serialised
board entry as transported, and it does not measure timing. Size
invariance of the canonical bytes is what was measured.

## 7. Capacity: the partition and `L_max`

```text
K_PUBLIC_CHALLENGES_PER_CONTINUATION = 1
A_ACCEPTED_CASTS_PER_CONTINUATION    = 1
L_max = E * (K + A)          # E = max_valid_continuations
```

| ID | Rule |
| -- | ---- |
| `SE-26` | **`L_max` is derived from the maximum number of valid continuation capabilities, never from turnout.** `CapacityPlan.l_max` is `max_valid_continuations * (k + a)`. There is no expected-turnout input to the plan, and no code path that reads one |
| `SE-27` | **The plan is capability-shaped, so it is fixed before the election opens.** A capacity that responded to observed demand would be an adaptive channel: batch sizes would then carry turnout |
| `SE-28` | `SlotClass` has three members — `CAST_RESERVED`, `CHALLENGE_RESERVED`, `SHARED_RESERVE` — and every slot in a primary batch belongs to exactly one of them |
| `SE-29` | **`validate()` requires `cast + challenge + shared == primary_capacity` exactly.** A partition that does not cover the batch raises `CapacityPlanInvalidError` with the message *"an unclassified slot is an adaptive-overflow hole"* |
| `SE-30` | **`validate()` also requires `total_capacity >= L_max + safety_reserve`**, where `total_capacity = (primary_capacity + reserve_commitments * reserve_capacity) * interval_count`. A plan that cannot cover `L_max` is not activated |
| `SE-31` | `validate()` fails closed on the first violation and returns the plan otherwise; `E`, the interval count and the primary capacity must each be positive |
| `SE-32` | **`slot_capacity()` returns the declared shared reserve and explicitly discards the batch capacity argument** (`del batch_capacity  # the shared reserve is declared, never inferred`) |
| `SE-33` | Every `CapacityPlan` carries `profile_label`, defaulting to `"TEST PROFILE ONLY - NOT A PRODUCTION DEFAULT"`. `test_capacity_profile_is_marked_test_only` asserts the fixture's plan carries it. **No production capacity profile is shipped this round** |

### 7.1 A real defect the tests found here

The first implementation of `_candidate_slots()` computed the shared
reserve as "every slot from `cast_n + chal_n` up to the batch capacity",
ignoring `plan.shared_reserve_per_batch`. Any batch made larger than the
declared partition silently gained unclassified slots — adaptive overflow
reintroduced by arithmetic. `test_e2e_07_capacity_exhaustion` found it.
The implementation now uses exactly the declared count:

```python
shared = list(range(cast_n + chal_n, cast_n + chal_n + shared_n))
```

and `CapacityPlan.validate()` refuses a plan whose partition does not
cover the batch exactly. This is reported because it is evidence the
harness works, not because it is decoration.

## 8. Which slots a submission may take

`_candidate_slots(runtime, slot_class)` returns an ordered list of
`(leaf_index, slot_class)` pairs. `reserve_leaf()` walks it and takes the
first index not already in `slot_owner` (compare-and-set inside the
transaction lock).

| ID | Requesting | Candidate order | May never take |
| -- | ---------- | --------------- | -------------- |
| `SE-34` | Cast | `[0, cast_n)` then the declared shared reserve | — |
| `SE-35` | Public challenge | `[cast_n, cast_n + chal_n)` then the declared shared reserve | **Any cast-reserved slot** (`TC-75`) |

| ID | Rule |
| -- | ---- |
| `SE-36` | **`requested_class` selects the exhaustion reason code and is not used to widen the candidate list.** The caller has already decided which slots the submission may take; `reserve_leaf()` cannot grant more |
| `SE-37` | `TC-75` is verified sequentially by `test_candidate_slots_never_offer_a_cast_slot_to_a_challenge` and under a real thread race by `test_c03_cast_and_public_challenge_concurrently`, which asserts the challenge's leaf index is `>= plan.cast_reserved_per_batch` whenever the challenge wins the race — and that it reserved nothing at all when the cast won and consumed the capability first |
| `SE-38` | **Reservation precedes durable acceptance.** There is no path that accepts an artefact and then looks for a slot; a transaction that fails restores a full snapshot including `slot_owner` and `reservations` |

## 9. Exhaustion fails closed, with two distinct reason codes

When no candidate slot is free, `reserve_leaf()` raises. The two cases are
distinct exception types on a common base that is never raised directly,
because a cast and a public challenge exhaust different capacity and a
caller must be able to tell them apart.

| ID | Condition | Exception | Reason code |
| -- | --------- | --------- | ----------- |
| `SE-39` | No cast-eligible slot | `CastCapacityUnavailableError` | `SUBMISSION_CAST_CAPACITY_UNAVAILABLE` |
| `SE-40` | No challenge-eligible slot | `PublicChallengeReservationUnavailableError` | `CHALLENGE_PUBLIC_RESERVATION_UNAVAILABLE` |
| `SE-41` | (base, never raised directly) | `ReservationUnavailableError` | `RESERVATION_UNAVAILABLE` |

`test_e2e_07_capacity_exhaustion` runs this on fixture C, whose plan has
one cast-reserved slot and no shared reserve, and asserts:

| ID | Asserted on exhaustion |
| -- | ---------------------- |
| `SE-42` | The second ballot is **not** in `store.accepted_ballots` — no acceptance without a reservation |
| `SE-43` | The outbox holds exactly one row — **no hidden queue and no retry buffer** |
| `SE-44` | The rejected submitter's continuation still has `cast_entitlement_available is True` and `capability_consumed is False` — **a capability is never spent by a submission that does not commit** |
| `SE-45` | The incident is publishable before closure as an `INCIDENT_NOTICE` whose payload is the constant `b"election.capacity_exhausted"` — it names no capability, no ballot and no count |

## 10. What is not implemented

- **No production capacity profile.** Both the parameter profiles and the
  capacity plan shipped here are TEST-labelled. Choosing `E`, the
  interval count, the batch capacity and the safety reserve for a real
  election is a governance act and is not implemented.
- **No formal hiding proof.** The salt construction is stated, not proven.
- **No constant-time claim.** Sealing uses Python big-integer and bytes
  operations; timing behaviour is not claimed anywhere in this round
  (`OD-P16D-05`).
- **No production datastore.** The compare-and-set is a dictionary under a
  re-entrant lock in the reference store. That the same invariants hold
  under a production isolation level is a PACK-17 obligation
  (`OD-P16D-04`).

## 11. What this document does not decide

```text
Batch interval, capacity and safety reserve values   → OD-P16C-10, GOVERNANCE
Retention of batch commitments and openings          → OD-P16A-07, PACK-09/PACK-17
Production datastore isolation for reservations      → OD-P16D-04, PACK-17
Constant-time / side-channel behaviour               → OD-P16D-05, PACK-17
Formal analysis of the leaf commitment               → external cryptographic review
```

**REFERENCE IMPLEMENTATION. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY.
NOT LEGALLY ACTIVATED.**
