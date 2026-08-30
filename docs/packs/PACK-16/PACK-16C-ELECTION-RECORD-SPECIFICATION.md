# PACK-16C — Election Record Specification

**Round:** PACK-16C — Casting, Receipt, Verification Client, Bulletin Board and Election Record. **Specification and ADR only. No code. No cryptographic implementation. Not implemented. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-101`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 0. The definition this document is written against

```text
The election record is the set of artefacts sufficient for a stranger —
with no account, no credential, no access to EPD² systems and no trust
in anyone who ran the election — to check the announced result,
using only published software they can rebuild themselves.

If a check requires something not in the record, the record is
INCOMPLETE. There is no category of "available on request".
```

| ID      | Rule                                                                                                                                                                                                                                               |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ER-01` | **Sufficiency is the acceptance test, not volume.** A record is complete when every published claim about the outcome can be recomputed from it, and no earlier                                                                                    |
| `ER-02` | **The record is self-describing.** It states which protocol profile, which parameter set, which specification digest and which schema version it is written against, so that a verifier written years later can interpret it without asking anyone |
| `ER-03` | **Nothing in the record is available only through EPD²-operated infrastructure.** It is downloadable in bulk, mirrorable, and byte-identical wherever it is obtained (`AO-*`)                                                                      |

---

## 1. Contents of the election record

Every row is **mandatory**. Optional artefacts are marked as such and are
never load-bearing for a verification check.

### 1.1 Definition of the election

| #   | Artefact                                                                                                                             | Why a verifier needs it                                                                                   |
| --- | ------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------- |
| 1   | **Election manifest**, signed, with its digest                                                                                       | Fixes contests, options, ballot styles, selection limits — everything a ballot's shape is checked against |
| 2   | **Ballot styles** and their contest bindings                                                                                         | Stage 8 of the pipeline is not re-performable without them                                                |
| 3   | **Protocol profile identifier** `EPD2-HOM-1` and its published specification digest                                                  | Fixes which algorithm the artefacts are to be read under                                                  |
| 4   | **Parameter set** `EPD2-CRYPTO-1`: `p`, `q`, `g`, `H`, encodings, the 27 domain-separation tags, and the pinned specification digest | Every recomputation depends on these bytes exactly                                                        |
| 5   | **Approval record of the parameter set**, and the open verification obligations against it                                           | So the verifier knows the parameters are declared, not merely used — including `VO-08`, unresolved        |
| 6   | **Election context descriptor**: opening and closing checkpoints, timezone, `timestamp_granularity`                                  | Fixes the window inside which submissions were admissible                                                 |

### 1.2 Keys and the ceremony

| #   | Artefact                                                                            | Why a verifier needs it                                        |
| --- | ----------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| 7   | **Joint public election key** and the base-hash chain `ver → H_P → H_B → H_E → H_I` | Every ciphertext and every proof is bound to `H_E`             |
| 8   | **Guardian public commitments** and the published DKG transcript                    | Lets the verifier check the key was formed as claimed          |
| 9   | **Guardian set, `k` and `n`**, fixed before opening                                 | Lets the verifier check the threshold actually applied         |
| 10  | **Key-ceremony checkpoints** published by PACK-16B                                  | Binds the key to a ceremony that happened before voting opened |
| 11  | **Guardian absence and substitution records**, if any, with their published grounds | An unexplained change in the guardian set is a finding         |

### 1.3 The ballots

| #   | Artefact                                                                                                                       | Why a verifier needs it                                                                    |
| --- | ------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------ |
| 12  | **Every accepted encrypted ballot**, with all ciphertexts and all NIZK proofs                                                  | Stages 9–15 are re-performed over these                                                    |
| 13  | **Every ballot's confirmation code**                                                                                           | Lets each voter find their own, and lets the verifier recompute it                         |
| 14  | **Every spoiled (challenged) ballot with its full opening**                                                                    | The challenge mechanism is worthless unless the openings are public and checkable (`CH-*`) |
| 15  | **Board sequence numbers** and the canonical ordering                                                                          | Fixes what "the set" means for the tally                                                   |
| 16  | **The closure checkpoint** fixing the eligible set                                                                             | Without it, "which ballots were counted" is an assertion                                   |
| 17  | **Every exclusion record**: identifier, ground from the closed list, reason code, Election Board decision, Auditor concurrence | `EX-01`…`EX-07`; a ballot leaving the tally silently would be undetectable otherwise       |

### 1.4 The tally

| #   | Artefact                                                                                 | Why a verifier needs it                                                          |
| --- | ---------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| 18  | **The homomorphic aggregate ciphertexts** per contest and option                         | The verifier recomputes the aggregation from artefact 12 and compares            |
| 19  | **Guardian decryption shares** and their **proofs of correct decryption**                | The step from aggregate to plaintext is otherwise unverifiable                   |
| 20  | **Which guardians contributed**, and the quorum satisfied                                | Lets the verifier check `k` was met and no compensated path was used (`ADR-100`) |
| 21  | **The decrypted totals per contest and option**                                          | The announced result                                                             |
| 22  | **The count reconciliation**: accepted, published, eligible, excluded, spoiled, included | The arithmetic that must close                                                   |

### 1.5 The board and its integrity

| #   | Artefact                                                                               | Why a verifier needs it                                                               |
| --- | -------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| 23  | **Every board entry** in the catalogued types (`BE-*`)                                 | The record _is_ the board, read as a whole                                            |
| 24  | **Every signed checkpoint**, chained, with signer identity                             | Establishes append-only behaviour over time                                           |
| 25  | **Mirror checkpoint co-signatures**, where mirrors exist                               | Split-view detection rests on these (`AO-*`)                                          |
| 26  | **Board and checkpoint signing public keys**, with their publication history           | A key rotation not visible in the record is indistinguishable from a substitution     |
| 27  | **Inclusion and consistency proof material** sufficient to recompute any proof offline | The verifier must not have to ask a server for a proof it is checking the server with |

### 1.5.1 The sealed batch layer

| #   | Artefact                                                                                                                                                                                                                                                    | Why a verifier needs it                                                                                           |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| 33  | **Every `sealed_batch_commitment`**, in cadence order, for every scheduled window including empty ones                                                                                                                                                      | Check 17 — a gap or a duplicate in the cadence is a finding (`TC-23`, `TC-44`)                                    |
| 34  | **Every `sealed_batch_opening`**, complete: each leaf's opening in index order, real leaves as salt plus committed fields, **cover leaves as their values**, the leaf-index → artefact mapping and each leaf's declared class                               | Check 18 — without the cover-leaf values the root cannot be recomputed at all (`TC-41`, `TC-45`)                  |
| 35  | **The `batch_reconciliation_record`**: occupancy by class per batch (`accepted_cast`, `public_challenged_spoiled`, `cover`), per-batch and global totals, the mapping to ballot artefacts, the recomputed roots and the verification result for every batch | Check 19 — the completeness and no-late-insertion argument (`TC-42`, `TC-43`, `TC-53`)                            |
| 36  | **The capacity plan as executed**: `E`, `K`, `A`, `L_max`, `C_primary`, `C_reserve`, `R`, the interval count, the capacity partition and the safety reserve — published with the manifest before opening and republished at closure                         | Check 20 — that the finite bound was computed, published in advance, and not exceeded (`TC-59`, `TC-64`, `BE-32`) |
| 37  | **Every capacity incident record**, if any, with its signed reservation-state evidence                                                                                                                                                                      | Check 21 — that no exhaustion was resolved silently (`TC-79`, `FM-16C-29`)                                        |

### 1.6 Governance and honesty

| #   | Artefact                                                                              | Why a verifier needs it                                                                                |
| --- | ------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| 28  | **Aggregate rejection counts by reason class**, published after closure               | Lets an observer see whether the process was under stress, without per-ballot detail (`VP-13`, `PM-*`) |
| 29  | **Published failure notices**: `publication_disputed`, missed deadlines, incidents    | An election with no incidents and an election that hid them look identical without these (`PA-*`)      |
| 30  | **Independent verifier reports**, where produced                                      | `IV-*`, governed under `OD-P16C-09`                                                                    |
| 31  | **The "what you cannot check" statement**                                             | §4 — mandatory, not a courtesy                                                                         |
| 32  | **The record's own manifest**: every file, its digest, and the digest of the manifest | Makes the record a single verifiable object                                                            |

**Thirty-seven mandatory artefacts.**

**Optional and never load-bearing:** human-readable summaries, charts,
translations, tooling convenience bundles. Each is marked derived and
carries the digest of the artefact it was derived from.

| ID      | Rule                                                                                                                                                                        |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ER-04` | **A derived artefact never substitutes for its source.** Where a summary and the record disagree, the record governs, and the summary is a defect to be corrected in public |
| `ER-05` | **Artefact 22 must close arithmetically**, and a record in which it does not is a finding of the highest severity, not a rounding note                                      |
| `ER-06` | **Artefact 31 is mandatory.** A record that lists only what can be verified misrepresents itself by omission                                                                |

---

## 2. What the record must never contain

```text
voter identity                       membership number
credential                            credential reference
continuation capability               continuation reference
authentication artefact               session identifier
IP address                            user agent
device fingerprint                    exact submission timestamp
exact consumption timestamp           arrival order
per-voter participation flag          per-ballot rejection detail
ballot plaintext of a CAST ballot     any nonce of a CAST ballot
any value from which a person-to-ballot link is derivable
```

| ID      | Rule                                                                                                                                                                                                                                                                                               |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ER-07` | **Nothing is added to the record because it "might be useful later".** Every field is present because a named check needs it, and the check is named in `PACK-16C-ELECTION-RECORD-COMPLETENESS-MATRIX.md`                                                                                          |
| `ER-08` | **A spoiled ballot's opening is published in full; a cast ballot's opening never is.** This is the single most dangerous adjacency in the design, and the two paths are separated at the data-model level, not by a conditional (`CH-*`, `DM-*`)                                                   |
| `ER-09` | **No timestamp anywhere in the record is finer than the context's `timestamp_granularity`**, and no field pair permits reconstructing a finer one by subtraction                                                                                                                                   |
| `ER-10` | **Turnout is not derivable from the record before closure**, because before closure the record contains **only constant-size sealed batch commitments on a fixed gapless cadence** and nothing per-ballot or aggregate at all (`TC-04`, `TC-29`, `TC-33`, `NIT-01`…`NIT-07`)                       |
| `ER-26` | **Artefacts 33–35 are mandatory and jointly indivisible.** A commitment without its opening, an opening without its commitment, or either without the reconciliation makes the record incomplete (`TC-44`, `EC-*`)                                                                                 |
| `ER-29` | **The record distinguishes `accepted_cast`, `public_challenged_spoiled` and `cover` leaves at closure, and proves each class's rule**: `accepted_cast` leaves enter the tally exactly once, `public_challenged_spoiled` leaves never enter it, and cover leaves are not ballots (`TC-43`, `TC-57`) |
| `ER-30` | **Local diagnostic challenges are not in the record and must not be.** They produce no artefact anywhere (`CH-42`, `TC-58`)                                                                                                                                                                        |
| `ER-31` | **Artefact 36 makes the capacity bound auditable after the fact.** A record whose executed plan differs from the plan published before opening is a finding, not a rounding note                                                                                                                   |
| `ER-27` | **Cover-leaf values are published in full at closure and are part of the record.** They are not secrets, not ballots, and not omitted for brevity — without them no batch root recomputes (`TC-28`, `TC-43`)                                                                                       |

---

## 3. Format, stability and long-term readability

| ID      | Rule                                                                                                                                                                                                         |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `ER-11` | **The record is a set of files with a published schema and a published schema version.** A verifier built against version _n_ states which versions it accepts, and the record states which version it is    |
| `ER-12` | **Canonical serialization is normative and identical to the casting-time rules** (`BP-*`). A record that re-serialises differently from what was signed cannot be checked against its own signatures         |
| `ER-13` | **The record is downloadable as a whole**, in bulk, without pagination games, rate limits that make full download impractical, or an account                                                                 |
| `ER-14` | **The record is byte-identical across mirrors**, and any divergence is itself a publishable finding (`AO-*`)                                                                                                 |
| `ER-15` | **The record does not depend on any EPD² service being alive.** A copy taken today must remain checkable when the organisation no longer exists — that is the point of publishing it                         |
| `ER-16` | **The record's own manifest digest is published outside the record**, alongside delivery, because a digest inside the object it describes proves nothing                                                     |
| `ER-17` | **Superseded artefacts are never deleted.** Where a correction is published, both the corrected artefact and the correction are in the record, with the checkpoint chain showing the order (`AO-*`, `BL-03`) |

---

## 4. What the record does **not** let anyone check

Mandatory in every published record, in participant-readable German and in
the record's own documentation. Written plainly.

```text
1. THAT EACH BALLOT CAME FROM A DISTINCT ENTITLED PERSON.
   The record shows that every published ballot is well-formed, unique
   and included. It CANNOT show that each one corresponded to a real,
   distinct entitlement. That link is deliberately absent, because its
   presence would let anyone connect a person to a ballot.
   Ballot stuffing is therefore NOT detectable from the record alone
   (VP-17). The controls against it are the eligibility and issuance
   separation specified in PACK-15 and the separation of principals —
   not a proof in this record.

2. THAT A VOTER'S DEVICE ENCRYPTED WHAT THEY INTENDED.
   The challenge mechanism DETECTS a dishonest client probabilistically,
   for voters who use it. It does not prevent one, and take-up is
   empirically low (CH-25, RR-04).

3. THAT NOBODY WAS COERCED.
   Nothing in the record speaks to this. The profile is
   coercion-MITIGATING, not coercion-resistant.

4. THAT EVERY ELIGIBLE PERSON WHO WANTED TO VOTE COULD.
   Ballots that were never submitted leave no trace. Access failures,
   exclusion and disenfranchisement are outside what a record of cast
   ballots can show.

5. THAT THE GUARDIANS' PRIVATE KEY SHARES WERE HANDLED CORRECTLY.
   The record shows the ceremony's public transcript and the decryption
   proofs. It does not show what happened to a share afterwards.

6. THAT THE PARAMETERS ARE APPROPRIATE.
   The record publishes them and publishes VO-08 as OPEN. It does not
   certify them, and no BSI-conformity claim is made (SB-06).
```

| ID      | Rule                                                                                                                                                                |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ER-18` | **This list is published with the record and not only in specification documents.** A reader of the record must encounter the limits without going looking for them |
| `ER-19` | **No published EPD² text may contradict this list**, and the prohibited-claims registry (`PB-*`) is enforced over participant-facing text mechanically (`CB-04`)    |
| `ER-20` | **Discovering a new limit is a reason to extend this list, never a reason to reword it into vagueness**                                                             |

---

## 5. When the record is published

| Moment         | What becomes public                                                                                                                                                                                     |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Before opening | Manifest, styles, parameter set, joint key, ceremony checkpoints, guardian commitments, `k`/`n`, opening checkpoint                                                                                     |
| During voting  | **One constant-size `sealed_batch_commitment` per scheduled window, and chained checkpoints. Nothing else.** No ballot, no confirmation code, no count of any kind (`TC-04`, `TC-25`)                   |
| At closure     | Closure checkpoint fixing the eligible set; **every `sealed_batch_opening`**; every encrypted ballot; every spoiled ballot with its opening; every confirmation code; the `batch_reconciliation_record` |
| After closure  | Aggregates, decryption shares and proofs, results, count reconciliation, aggregate rejection counts, exclusion records                                                                                  |
| Afterwards     | Independent verifier reports, incident notices, corrections, archive checkpoints                                                                                                                        |

| ID      | Rule                                                                                                                                                                                                               |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `ER-21` | **No decryption artefact of any kind exists before the closure checkpoint** — no partial share, no test decryption, no operational "sanity check" (`ADR-100`)                                                      |
| `ER-22` | **The pre-opening artefacts are published before opening, not reconstructed afterwards.** A manifest published after voting proves nothing about what ballots were checked against                                 |
| `ER-28` | **The batch cadence parameters are published before opening**, with the manifest, so that a reader can tell in advance exactly how many `sealed_batch_commitment` entries a complete record must contain (`TC-22`) |

---

## 6. Retention and archive

| ID      | Rule                                                                                                                                                                                                                               |
| ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ER-23` | **The record is retained for the period the governing statute and the context's published retention policy require, whichever is longer**, and the period is published with the record                                             |
| `ER-24` | **Archiving seals; it does not summarise.** An archive checkpoint covers the complete record, and an archive that dropped artefacts to save space is not an archive of this record                                                 |
| `ER-25` | **Retention of the record does not extend retention of anything outside it.** Operational logs, request metadata and support records follow their own PACK-15 lineage and are not permitted to be retained _because_ the record is |

---

## 7. What this document does not decide

```text
File layout and concrete schema             → PACK-16D, OD-P16C-04
Commitment and opening formats               → OD-P16C-14, OD-P16C-16
Bulk distribution mechanism                  → PACK-16D
Retention period per context                 → GOVERNANCE, published with the manifest
Independent verifier engagement               → OD-P16C-08
Verification-report governance                → OD-P16C-09
Long-term archival custody                    → PACK-17
```

**SPECIFIED. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY. NOT LEGALLY
ACTIVATED.**
