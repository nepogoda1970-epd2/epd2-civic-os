# PACK-16C — Bulletin Board Entry Catalog

**Round:** PACK-16C — Casting, Receipt, Verification Client, Bulletin Board and Election Record. **Specification and ADR only. No code. No cryptographic implementation. Not implemented. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-101`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 1. Every entry has the same envelope

```text
BulletinBoardEntry
  entry_type            board_sequence          context_id
  schema_version        content_digest          previous_checkpoint_reference
  batch_reference       publication_timestamp   (coarsened, batch-level)
  operator_signature    payload
```

| ID | Rule |
| -- | ---- |
| `BE-00` | **`board_sequence` is assigned at publication, shuffled within the batch, and is the canonical order** (`BA-08`). It is not arrival order and must not be read as one |

## 2. The catalogue

| ID | Entry type | Public fields | Restricted / absent | Ordering | Publication deadline | Privacy constraint |
| -- | ---------- | ------------- | ------------------- | -------- | -------------------- | ------------------ |
| `BE-01` | `election_manifest` | Full manifest, contests, options, limits, counting rule, mirror list, batching parameters, **capacity plan — `E`, `K`, `A`, `L_max`, `C_primary`, `C_reserve`, `R`, interval count, capacity partition and safety reserve** (`TC-64`, `TC-66`, `TC-74`), verification origin, exclusion-ground list | none | First entry | **Before `issuance_open`** | none — wholly public |
| `BE-02` | `parameter_set` | `parameter_set_id`, definitions or canonical reference, pinned specification digest, provenance | none | Before any ballot | Before `issuance_open` | none |
| `BE-03` | `ceremony_transcript_checkpoint` | Transcript digest, phase, guardian indices, commitments, Schnorr proofs, Auditor verdict | Guardian personal data beyond name and organisation | Before the joint key | Before `voting_open` | `CT-13`…`CT-17` prohibitions apply |
| `BE-04` | `joint_public_key` | The key, guardian public contributions, base-hash chain inputs | none | After `BE-03` | **Before `voting_open`; no ballot may be encrypted before it** (`CF-09`) | none |
| `BE-05` | `ballot_accepted` | `ballot_id`, ciphertexts, all proofs, `confirmation_code`, `ballot_style_id` | Nonce, plaintext, capability, retry token, submitter metadata, arrival time | Leaf-index order within its batch, revealed at closure | **After closure only** — pre-closure the ballot is covered by `BE-24` (`TC-04`, `TC-29`) | `BA-05` filter |
| `BE-06` | `ballot_challenged` | `ballot_id`, ciphertexts, proofs, `confirmation_code` | same as `BE-05` | With `BE-05`, leaf-index order | **After closure only** — a spoiled ballot occupies a leaf like any other artefact (`TC-57`) | Same |
| `BE-07` | `ballot_spoiled` | The complete opening — nonces and plaintext — enabling re-encryption | The voter's identity, which is not known | With `BE-06` | **After closure only** | **Publishes a real choice** — the voter was warned (`CH-11`). The voter's own cast-as-intended check is local re-encryption and does not wait for this entry (`CH-*`) |
| `BE-08` | `ballot_rejected_summary` | **Aggregate counts by reason-code class only**, published **after closure** | Per-ballot rejection detail, at any time | Post-closure | After closure | `VP-13` — a rejection pattern is a correlation surface |
| `BE-09` | `board_checkpoint` | Sequence range, content root, previous checkpoint reference, operator signature, mirror signatures | none | Periodic and at every phase boundary | Per the published interval | none |
| `BE-10` | `election_closed` | The closure checkpoint fixing the tallied set (`BM-20`) | none | Exactly once | At window close | **The boundary before which no decryption exists** |
| `BE-11` | `tally_started` | That the decryption ceremony has begun, its form, its guardians | Guardian secret material, always | After `BE-10` | On start | Never before `BE-10` |
| `BE-12` | `guardian_decryption_share` | Partial decryption and its proof, guardian index | The guardian's secret; any missing guardian's secret (`BR-13`) | After `BE-11` | Per the ceremony | Public values only |
| `BE-13` | `tally_artifact` | Encrypted aggregate, decryption combination, plaintext result, proofs | none | After `BE-12` | Per the ceremony | none |
| `BE-14` | `verification_report` | Verifier identity, version, result code, check list, what it did not check | Anything identifying a voter | Any time after the record exists | Governed (`OD-P16C-09`) | `IV-13` |
| `BE-15` | `certification_decision` | The Election Board's decision, the Auditor's concurrence, the grounds | Deliberation content beyond the published grounds | After verification | Governed | none |
| `BE-16` | `archive_checkpoint` | Digest over the whole record, retention dates, verifier versions used | none | Final | At archival | none |
| `BE-17` | `incident_notice` | That an incident occurred, its class, what is suspended, the reason code | Evidence whose publication would harm an investigation — **named as withheld** | Any time | Per `IN-*` lineage | Never identifies a voter |
| `BE-18` | `exclusion_record` | `ballot_id`, the ground from the closed list, the reason code, the deciding body, the Auditor's concurrence | Who cast it — **not knowable** (`EX-07`) | After closure | With the decision | `EX-02` |
| `BE-24` | `sealed_batch_commitment` | `election_context_id`, `batch_sequence`, `batch_window_id`, `fixed_capacity_profile_id`, `commitment_root`, previous-checkpoint reference, `schema_version`, signature, checkpoint linkage | **Real ballot count, leaf occupancy bitmap, any individual ballot hash, confirmation code, acceptance timestamp, capability reference, identity data, and any field whose size or presence varies with occupancy** | Strictly by `batch_sequence`, one per scheduled window, **no gaps** | **At its scheduled window time; an empty window publishes too** (`TC-23`, `TC-25`) | **Constant serialized size across all batches** (`TC-33`) — the entry must not distinguish an empty batch from a full one |
| `BE-25` | `sealed_batch_opening` | `batch_sequence`, every leaf in index order with its opening — real leaves as salt plus committed fields, cover leaves as their value — the leaf-index → ballot-artefact mapping, and each leaf's declared class (`accepted_cast`, `public_challenged_spoiled`, `cover`) | Nonce or plaintext of an **accepted** ballot; capability; identity; exact acceptance timestamp | Leaf index within `batch_sequence` | **At closure, for every scheduled window, in full** — partial opening is prohibited (`TC-45`) | Opening is complete or the record is incomplete; occupancy becomes public **only here** |
| `BE-26` | `batch_reconciliation_record` | Per-batch occupancy declaration by class (`accepted_cast`, `public_challenged_spoiled`, `cover`), per-batch and global totals, the mapping to ballot artefacts, the recomputed roots, the capacity-plan parameters `E`, `K`, `A`, `L_max`, `C_primary`, `C_reserve`, `R`, and the verification result for every batch | The restricted count-comparison evidence of `TC-52`, which is Auditor-held and never published; any pairing of a ballot with a capability | Once, after all `BE-25` entries | At closure, with the closure checkpoint | Publishes **counts and mappings between public artefacts only** — never a join across the acceptance boundary (`DM-10`) |

| ID | Rule |
| -- | ---- |
| `BE-19` | **`BE-08` is published only after closure and only in aggregate.** Per-ballot rejection detail before closure would let an observer watch a specific voter fail and retry |
| `BE-20` | **No entry type carries a count of accepted ballots before closure, or any value from which one is derivable — including its own serialized size** — and none may be added that does (`TC-29`, `TC-33`, `BA-07`) |
| `BE-21` | **Every entry passes the prohibited-content filter before publication** (`BA-05`); a filter failure is an incident under `FM-16C-*`, not a redaction |
| `BE-22` | **New entry types require an ADR.** The catalogue is closed for the initial profile, because an unlisted entry type is an unreviewed publication channel. **`BE-24`, `BE-25` and `BE-26` were added by `ADR-101` and are part of the initial profile** — they are catalogued here, not asserted in prose elsewhere |
| `BE-27` | **No prose in any PACK-16C document may assert an entry type that is not in §2.** The first candidate's *padding entry* was asserted in `TC-10` and never catalogued; that model is retired (`TC-21`) and no padding entry type exists |
| `BE-28` | **Before closure the only entry types that may appear are `BE-01`…`BE-04`, `BE-09`, `BE-17` and `BE-24`.** `BE-05`, `BE-06`, `BE-07`, `BE-08`, `BE-10`…`BE-16`, `BE-18`, `BE-25` and `BE-26` are post-closure or phase-bound, and a pre-closure occurrence of any of them is an incident, not a scheduling variance |
| `BE-29` | **`BE-24` is the only entry type published on a fixed cadence**, and its cadence may never be changed in response to turnout, load or any observed property of the election (`TC-24`) |
| `BE-30` | **Every predeclared reserve batch commitment is a `BE-24` entry and is published on schedule whether used or not** (`TC-67`). A `BE-24` that appears only under load is prohibited, and an unscheduled one is `publication.unscheduled_batch_prohibited` (`TC-68`) |
| `BE-31` | **A real leaf's type binding — `accepted_cast` or `public_challenged_spoiled` — is private until closure.** `BE-24` carries no field, no length difference and no structural difference that distinguishes a cast leaf from a challenge leaf. Introducing separate pre-closure commitment types for cast and challenge is **prohibited**, because their counts would then be public (`TC-57`) |
| `BE-32` | **The capacity plan is published with the manifest (`BE-01`) before the election opens and republished in `BE-26` at closure**, so that a reader can check the plan they were promised against the plan that was executed (`TC-64`, `TC-66`) |

## 3. Retention

| Class | Retained | Rule |
| ----- | -------- | ---- |
| `BE-01`…`BE-04`, `BE-09`…`BE-16` | For the governed record retention period (`BB-19`) | Needed for historical verification |
| `BE-05`…`BE-07` | Same, and **this is a long-term secrecy liability** (`RR-14`, `T-P16A-40`) | Encrypted ballots retained indefinitely are a future-cryptanalysis exposure — `OD-P16A-07` owns the period |
| `BE-08`, `BE-17`, `BE-18` | Same | Aggregate or already privacy-filtered |
| `BE-24`, `BE-25`, `BE-26` | Same | **Mandatory in the election record** (`ER-*`). A commitment without its opening, or an opening without its commitment, makes the record incomplete (`TC-44`, `EC-*`) |

| ID | Rule |
| -- | ---- |
| `BE-23` | **The retention period is published in advance** and its expiry is itself a published event, so destruction is not a silent act |

## 4. What this document does not decide

```text
Retention period in years              → OD-P16A-07, PACK-09/PACK-17
Serialization of entries                → OD-P16C-04, PACK-16D
Batch interval and capacity              → OD-P16C-10, GOVERNANCE
Commitment construction                   → OD-P16C-14, PACK-16D
Opening and reconciliation format         → OD-P16C-16, PACK-16D
Checkpoint interval                       → OD-P16C-10
Verification-report governance            → OD-P16C-09
```

**SPECIFIED. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY. NOT LEGALLY
ACTIVATED.**
