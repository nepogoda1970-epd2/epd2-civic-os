# PACK-16C — Append-Only and Consistency Model

**Round:** PACK-16C — Casting, Receipt, Verification Client, Bulletin Board and Election Record. **Specification and ADR only. No code. No cryptographic implementation. Not implemented. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-101`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 1. The decision

```text
MERKLE-TREE TRANSPARENCY LOG
with signed checkpoints, inclusion proofs, consistency proofs,
independent mirrors that co-sign, and published checkpoint gossip.

ARCHITECTURE PATTERN SELECTED. NO PRODUCT SELECTED.
```

## 2. The options

| Pattern                            | Inclusion proof                                   | Consistency proof           | Rollback detection              | Late-insertion detection | Verifier cost                                    | Verdict                                                            |
| ---------------------------------- | ------------------------------------------------- | --------------------------- | ------------------------------- | ------------------------ | ------------------------------------------------ | ------------------------------------------------------------------ |
| Hash chain                         | O(n) — replay the chain                           | Weak: only by full replay   | Yes, with a retained checkpoint | Yes                      | O(n) per check                                   | Rejected — a voter cannot check one ballot without the whole board |
| **Merkle tree / transparency log** | **O(log n)**                                      | **O(log n)**, cryptographic | **Yes**                         | **Yes**                  | Low per check, full recomputation still possible | **SELECTED**                                                       |
| Signed sequence checkpoints alone  | None                                              | None                        | Only between checkpoints        | Weak                     | Low                                              | Rejected — no per-entry proof                                      |
| Replicated append-only database    | Depends on the product                            | Depends on the product      | Operator-dependent              | Operator-dependent       | —                                                | Rejected — the guarantee becomes a vendor's claim                  |
| Hybrid tree + chained checkpoints  | As Merkle, plus chain linkage between checkpoints | Both                        | Strongest                       | Strongest                | Slightly higher                                  | **Adopted as the concrete shape** — §3                             |

| ID      | Rule                                                                                                                                                               |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `AO-01` | **A pattern is selected; no product is.** A design whose append-only guarantee rests on a vendor's configuration rather than on published proofs is refused        |
| `AO-02` | **Every guarantee must be checkable by a verifier that does not trust the board operator.** If a property can only be asserted, it is not a property of this board |

## 3. The structure

```text
ENTRY            canonical serialization → entry_hash = H(domain_tag_entry ‖ bytes)
TREE             Merkle tree over entry hashes, in board_sequence order
CHECKPOINT       { context_id, tree_size, root_hash, previous_checkpoint_hash,
                   coarsened_timestamp, schema_version }
                 signed by the board operator, co-signed by each mirror
CHAIN            each checkpoint commits to its predecessor's hash
```

| ID      | Rule                                                                                                                                                                                                                                                                                                                                                             |
| ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `AO-03` | **Entry hashes use a domain-separated hash** distinct from every ballot-domain tag, so a board entry can never be confused with a protocol object (`DS-*` lineage)                                                                                                                                                                                               |
| `AO-04` | **Checkpoints chain**: `previous_checkpoint_hash` makes a rollback to an earlier tree state detectable even by a reader who kept only one checkpoint                                                                                                                                                                                                             |
| `AO-05` | **Tree size is monotonically non-decreasing.** A checkpoint with a smaller `tree_size` than one already published is prima facie evidence of rollback and is a `FM-16C-*` incident                                                                                                                                                                               |
| `AO-06` | **Inclusion proofs are available for every entry**, against any checkpoint at or after its publication                                                                                                                                                                                                                                                           |
| `AO-16` | **The sealed batch layer is a second, nested commitment and does not replace the board tree.** A `sealed_batch_commitment` entry is an ordinary board entry with its own inclusion proof; the `commitment_root` inside it is a **separate Merkle root over exactly `C` leaves** (`TC-30`). Board-level and batch-level proofs are distinct and both are required |
| `AO-17` | **Leaf commitments use a domain-separated hash distinct from both the ballot domain tags and the board-entry tag** (`AO-03`, `DS-*` lineage), so a leaf can never be confused with a board entry or a protocol object                                                                                                                                            |
| `AO-18` | **A missing scheduled `sealed_batch_commitment` is a gap in a public, fixed cadence and is therefore detectable by any reader**, without any count being published (`TC-23`, `TC-25`, `FM-16C-18`)                                                                                                                                                               |
| `AO-19` | **A batch root that does not recompute from its published opening is `FM-16C-22`** — investigated and published, never silently re-derived (`TC-41`, `TC-54`)                                                                                                                                                                                                    |
| `AO-07` | **Consistency proofs are available between any two checkpoints**, proving the later tree is an append-only extension of the earlier                                                                                                                                                                                                                              |
| `AO-08` | **Timestamps in checkpoints are coarsened** to the context's granularity and are evidentiary, not authoritative — the authoritative order is `board_sequence` (`BA-09`)                                                                                                                                                                                          |

## 4. Split-view resistance

| Attack                               | Defence                                                                                                                  | Residual                                   |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------ |
| Different views for different voters | Mirrors co-sign checkpoints (`AO-09`); a voter's receipt carries the checkpoint they saw (`RE-01`)                       | Only detected if someone compares          |
| Selective omission                   | Inclusion proof fails; absence is a first-class outcome with a dispute path (`BM-19`)                                    | Requires the voter to check                |
| Mirror divergence                    | Divergent co-signatures are published and attributable (`BA-19`); tally halts (`BA-20`)                                  | Requires ≥ 2 genuinely independent mirrors |
| Checkpoint equivocation              | Two checkpoints with the same `tree_size` and different roots, both signed, are **non-repudiable proof of misbehaviour** | Needs both to be observed                  |
| Rollback                             | `AO-04`, `AO-05`                                                                                                         | Needs a retained earlier checkpoint        |
| Late insertion after closure         | Closure is a checkpoint fixing the set (`BE-10`); later insertion breaks consistency against it                          | —                                          |
| Post-election deletion               | Append-only plus archive checkpoint (`BE-16`)                                                                            | —                                          |

| ID      | Rule                                                                                                                                                                                                                      |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `AO-09` | **Each mirror independently signs every checkpoint it has seen**, and its signature set is published. Divergence is then attributable to a named operator, not merely visible (`BB-30`)                                   |
| `AO-10` | **Checkpoint gossip is published**: checkpoints are exposed at a stable, cacheable public location so that third parties and archives can capture them independently                                                      |
| `AO-11` | **The Independent Auditor captures checkpoints on its own schedule**, from its own network path, and publishes what it captured. This is the witness function, performed by a party with a duty rather than by volunteers |
| `AO-12` | **Two signed checkpoints with equal `tree_size` and different roots halt the election immediately** — `FM-P16A-10`, abort, uncertifiable. There is no reconciliation procedure, because there is no honest explanation    |

### 4.1 What is deferred, and what that costs

**Full split-view resistance requires witnesses that are not EPD²'s.**
Mirrors under distinct organisational control plus Auditor capture is
strong; cross-logging into an external transparency ecosystem, or
third-party witness cosigning by parties with no relationship to EPD², is
stronger.

| ID      | Rule                                                                                                                                                                                                                                                                          |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `AO-13` | **External witness cosigning is not specified in the initial profile** and is recorded as `OD-P16C-12` with an explicit consequence: **until it exists, split-view resistance rests on mirror independence, which is organisational and unenforceable technically** (`RR-12`) |
| `AO-14` | **This is a blocker for production implementation acceptance, not for this specification round.** PACK-16D may not present mirror co-signing alone as complete split-view resistance                                                                                          |

## 5. What a verifier checks

```text
1  recompute every entry hash from the published canonical bytes
2  recompute the Merkle root for each checkpoint's tree_size
3  verify the operator signature and every mirror co-signature
4  verify previous_checkpoint_hash linkage across the whole chain
5  verify tree_size is non-decreasing
6  verify consistency proofs between successive checkpoints
7  verify an inclusion proof for every entry it cares about
8  compare checkpoints captured from different mirrors and from the Auditor
```

| ID      | Rule                                                                                                                                                                                                                                      |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `AO-15` | **Step 8 is the one that cannot be done from a single source**, and the record says so: consistency of the record with itself is provable; consistency of what different readers were shown is not, without independent capture (`IV-11`) |

## 6. What this document does not decide

```text
Hash function for the tree (within the profile's constraints) → PACK-16D
Checkpoint and batch interval                                  → OD-P16C-10
Commitment construction                                        → OD-P16C-14
Log implementation                                             → PACK-16D
External witness ecosystem                                     → OD-P16C-12, PACK-17
```

**SPECIFIED. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY. NOT LEGALLY
ACTIVATED.**
