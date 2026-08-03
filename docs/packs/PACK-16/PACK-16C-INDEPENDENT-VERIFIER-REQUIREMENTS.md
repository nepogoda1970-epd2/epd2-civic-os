# PACK-16C — Independent Verifier Requirements

**Round:** PACK-16C — Casting, Receipt, Verification Client, Bulletin Board and Election Record. **Specification and ADR only. No code. No cryptographic implementation. Not implemented. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-101`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 1. What a verifier must be able to check

| # | Check | Inputs from the record |
| - | ----- | ---------------------- |
| 1 | **Manifest consistency** | Manifest, its signature, its digest as bound in every ballot |
| 2 | **Parameter-set consistency** | Parameter definitions, pinned specification digest, bit-equality |
| 3 | **Ceremony transcript validation** | Transcript, commitments, Schnorr proofs, checkpoint chain |
| 4 | **Joint-key derivation** | Guardian contributions → recompute the joint public key |
| 5 | **Base-hash chain** | `ver → H_P → H_B → H_E → H_I` recomputed from published inputs |
| 6 | **Ballot well-formedness** | Every published ballot: group membership, subgroup, range proofs, contest-sum proofs, plaintext-knowledge proof |
| 7 | **Confirmation codes** | Recomputed from each ballot's encryptions and `H_E` |
| 8 | **Challenge validation** | Spoiled ballots: re-encrypt from published opening, compare to published ciphertexts |
| 9 | **Board inclusion** | Inclusion proof for every entry against its checkpoint |
| 10 | **Board consistency** | Consistency proofs between successive checkpoints; no rollback, no late insertion |
| 11 | **Uniqueness** | No duplicate `ballot_id`, no duplicate confirmation code |
| 12 | **Closure validation** | The closure checkpoint fixes exactly the tallied set (`BM-20`) |
| 13 | **Decryption-share validation** | Every share's proof; quorum satisfied; no share dropped (`KC-10`) |
| 14 | **Tally recomputation** | Homomorphic aggregation over the published accepted set, independently |
| 15 | **Aggregate-result verification** | Combined decryption matches the published plaintext result |
| 16 | **Archive integrity** | Archive checkpoint over the whole record; digests match |
| 17 | **Batch cadence completeness** | Every scheduled batch window has exactly one `sealed_batch_commitment`, in sequence, with no gap and no duplicate (`TC-23`, `TC-44`) |
| 18 | **Batch root recomputation** | Every `commitment_root` recomputes from its published `sealed_batch_opening` over exactly `C` leaves (`TC-30`, `TC-41`) |
| 19 | **Batch reconciliation** | Every ballot artefact maps to exactly one occupied leaf and back; no cover leaf is tally-eligible; no tally input lacks a committed leaf (`TC-42`, `TC-43`, `TC-53`) |
| 20 | **Capacity-bound conformance** | `accepted_cast` leaves ≤ `E`; `public_challenged_spoiled` leaves ≤ `E × K`, which is `E` in the initial profile; the executed plan matches the plan published before opening (`TC-59`, `ER-31`) |
| 21 | **Capacity-incident completeness** | Every capacity incident has a signed record, and no interval shows an unscheduled batch or an unaccounted artefact (`TC-68`, `TC-79`) |

| ID | Rule |
| -- | ---- |
| `IV-01` | **Every one of the twenty-one checks is performable from the published record alone.** If a check needs anything else, the record is incomplete (`EC-*`) |
| `IV-02` | **The checks are specified in prose sufficient to write an independent verifier** (`BM-27`, `BB-34`) — this document plus the record schema is the specification |

## 2. What a verifier must never need

```text
voter identity            credential database
private keys              trust in the production server
trust in EPD²'s frontend  an account, a login, or accepted terms
network access, in offline mode
```

| ID | Rule |
| -- | ---- |
| `IV-03` | **A verifier that requires any of the above is not an independent verifier**, and its output may not be cited as independent verification |
| `IV-04` | **Verification requires no credential, no account and no agreement to terms** (`BB-36`) |

## 3. Verifier classes

| Class | Written by | Purpose | Required? |
| ----- | ---------- | ------- | --------- |
| **Official verifier** | EPD² | Reference behaviour, test vectors, day-to-day checks | Yes — and **not sufficient** |
| **Independent reference verifier** | A party EPD² did not commission | The universal-verifiability guarantee | **Required before binding use** (`BM-28`) |
| **Third-party verifier** | Anyone | Adversarial checking | Encouraged, not commissioned |
| **Auditor verifier** | Independent Auditor's choice | The Auditor's own verdict | Required for certification |
| **Offline verifier** | Any of the above | Verification with no network | Required capability (`VC-09`) |

| ID | Rule |
| -- | ---- |
| `IV-05` | **The official verifier is never sufficient for universal verifiability.** A system verifying itself has proved nothing to anyone who does not already trust it |
| `IV-06` | **At least one verifier not written or commissioned by EPD² must verify a real context before any binding use** (`BM-28`). This is an activation gate, not an aspiration |

## 4. Distribution requirements

```text
open source                      reproducible build
signed release                   published artefact digests
cross-language test vectors      archived source and binaries
deterministic output             no network dependence in offline mode
no analytics                     no identity, no account
```

| ID | Rule |
| -- | ---- |
| `IV-07` | **Deterministic output**: the same record yields the same result, on any machine, at any time, in any supported implementation |
| `IV-08` | **Cross-language test vectors are published** so that two implementations can be shown to agree (`TV-07`, `VC-05` lineage) |
| `IV-09` | **Source and released binaries are archived with the election record**, so a record can still be verified after the project that built the verifier is gone |
| `IV-10` | **A verifier release is pinned per election record**: the record states which verifier versions were used and what they returned |

## 5. What the verifier cannot check — published alongside what it can

```text
CANNOT CHECK  that a device encrypted the choice its voter intended
              — only the challenge can test that, per ballot, and only
              if a voter chose to challenge          (BB-37, T-P16A-33)

CANNOT CHECK  that every published ballot corresponds to a distinct real
              entitlement — the unlinkability that protects the voter
              also removes this proof                (VP-17)

CANNOT CHECK  that no eligible person was prevented from voting
CANNOT CHECK  that the guardians did not collude off-protocol
CANNOT CHECK  that the board showed the same view to everyone, unless
              independent mirrors and witnesses were actually consulted (AO-*)
CANNOT CHECK  how many ballots existed at any moment BEFORE closure
              — by design; the pre-closure record is a sequence of
              constant-size commitments                        (TC-29)
CANNOT CHECK  the accepted-ballot vs consumed-capability count
              comparison — that is Auditor-restricted evidence  (TC-52, IV-17)
```

| ID | Rule |
| -- | ---- |
| `IV-11` | **The verifier's output states these limits every time**, not only in documentation. A `VERIFIED` result that does not say what it did not check is misleading, and is prohibited |

## 6. Result model

| Result | Severity | Public message | Auditor detail | Certification effect | Election effect |
| ------ | -------- | -------------- | -------------- | -------------------- | ---------------- |
| `VERIFIED` | — | "The published record is internally consistent and the result matches the published ballots." | Full check list with per-check counts | Permits certification | none |
| `VERIFIED_WITH_WARNINGS` | low | Same, plus the named warnings | Warning list with locations | Permits certification **with the warnings published** | none |
| `INCOMPLETE_RECORD` | **high** | "The published record is incomplete." | Missing artefact list | **Blocks certification** | Investigate; publish; remedy or annul |
| `UNSUPPORTED_PROFILE` | medium | "This verifier does not support this record's profile." | Profile and schema versions | Neutral — a verifier limitation | Obtain a supporting verifier |
| `INVALID_MANIFEST` | **high** | "The manifest does not verify." | Signature and digest detail | **Blocks certification** | Abort or annul |
| `INVALID_CEREMONY` | **critical** | "The key ceremony record does not verify." | Transcript detail | **Blocks certification** | **Annul** — the key's provenance is unsound |
| `INVALID_BALLOT_PROOF` | **critical** | "One or more published ballots do not verify." | Ballot identifiers and failing checks | **Blocks certification** | `FM-P16A-12`: exclude with public reason; escalate if outcome-changing |
| `BOARD_INCONSISTENCY` | **critical** | "The public record is not consistent." | Checkpoints, mirrors, divergence point | **Blocks certification** | **Abort — uncertifiable** (`FM-P16A-10`) |
| `INVALID_DECRYPTION_SHARE` | **critical** | "A decryption share does not verify." | Guardian index, equation | **Blocks certification** | **Halt the tally** (`KC-10`) — never drop the share |
| `TALLY_MISMATCH` | **critical** | "The published result does not match the published ballots." | Recomputed versus published | **Blocks certification** | **Annul** |
| `ARCHIVE_CORRUPTION` | **high** | "The archived record does not match its checkpoints." | Digest comparison | Blocks archival attestation | Investigate; the result may become uncertifiable (`FM-P16A-24`) |

| ID | Rule |
| -- | ---- |
| `IV-12` | **Every result is machine-readable, with a stable identifier, a severity, and a privacy-safe evidence reference** — never free text alone |
| `IV-13` | **No result reveals ballot content, identity, or which voter is affected.** Evidence references point at published artefacts, which are already public |
| `IV-14` | **A `VERIFIED` result is not a certification.** Certification is the Election Board's act with Auditor concurrence, and requires `VO-08`, `TV-08` and the remaining activation gates |
| `IV-15` | **Checks 17–19 are blocking.** A missing batch window, a root that does not recompute, or a reconciliation that does not close yields `INCOMPLETE_RECORD` at minimum and `TALLY_MISMATCH` where a tally input has no committed leaf (`TC-53`) |
| `IV-16` | **A verifier must not be able to perform checks 17–21 before closure**, because doing so would require the openings, and the openings are what make occupancy public. Pre-closure the verifier checks only cadence and checkpoint consistency (`TC-38`) |
| `IV-18` | **Check 20 is a public check on totals, not on pairings.** A public verifier counts leaves by class and compares with `E` and `E × K` from artefact 36. It cannot and must not check *which* capability produced *which* artefact |
| `IV-19` | **The per-capability bound — at most one accepted cast artefact and at most one public challenge artefact per anonymous continuation — is verified through privacy-preserving restricted reconciliation evidence held by the Independent Auditor**, never by publishing a capability-to-artefact mapping (`TC-83`) |
| `IV-20` | **The exact privacy-preserving construction of that evidence is not specified by this round.** It belongs to PACK-16D's implementation specification and PACK-17's independent cryptographic review, and it is carried as an open decision with a named consequence (`OD-P16C-19`) rather than asserted as solved |
| `IV-17` | **The restricted count comparison of `TC-52` is the Independent Auditor's check, not a public verifier's.** A public verifier cannot perform it, must not claim to have performed it, and its absence from a public `VERIFIED` result is stated under `IV-11` |

## 7. What this document does not decide

```text
Verifier implementation and language     → PACK-16D
Who is engaged as the independent party  → GOVERNANCE, OD-P16C-08
Verification-report governance            → OD-P16C-09
Test-vector production                    → PACK-16D, TV-* lineage
```

**SPECIFIED. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY. NOT LEGALLY
ACTIVATED.**
