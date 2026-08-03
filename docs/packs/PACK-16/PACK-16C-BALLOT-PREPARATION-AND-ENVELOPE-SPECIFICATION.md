# PACK-16C — Ballot Preparation and Envelope Specification

**Round:** PACK-16C — Casting, Receipt, Verification Client, Bulletin Board and Election Record. **Specification and ADR only. No code. No cryptographic implementation. Not implemented. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-101`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 1. The plaintext ballot, before anything is encrypted

```text
PlaintextBallot                       (client memory only, never transmitted,
  election_context_id                  never persisted, never logged)
  ballot_style_id
  manifest_digest
  parameter_set_id
  Contest[]
  ballot_nonce                        the master nonce; destroyed on cast

Contest
  contest_id
  selection_limit
  option_selection_limit
  Selection[]                         one per option in the manifest, in
  contest_sequence_order              canonical manifest order
  placeholder_count

Selection
  selection_id
  sequence_order
  vote                                0 or 1
  is_placeholder
```

| ID       | Rule                                                                                                              |
| -------- | --------------------------------------------------------------------------------------------------------------------- |
| `BP-01`  | **The plaintext ballot never leaves the client and is never persisted** — not in a draft, an autosave, a crash report, an error payload or a support attachment (`CF-14`) |
| `BP-02`  | **Every option in the manifest gets a selection**, voted or not. A ballot's shape is fixed by the ballot style, so the shape leaks nothing about the choice |
| `BP-03`  | **Placeholder selections bring each contest to its selection limit**, so that undervotes are indistinguishable from full votes in the ciphertext structure |
| `BP-04`  | Canonical order is the **manifest's declared sequence order**, never the order the voter clicked |

---

## 2. Prohibited in the plaintext ballot — normative

```text
identity                       member ID
credential ID                  continuation reference or capability
device fingerprint             IP address
account identifier             organisation membership record
human-readable voter name      email address
session ID                     trace or correlation ID
geolocation                    user agent
timestamp of selection         any free-text field
```

| ID       | Rule                                                                                                              |
| -------- | --------------------------------------------------------------------------------------------------------------------- |
| `BP-05`  | **The prohibited list is closed and is enforced by schema**, not by review. A field not in the permitted schema is rejected, not ignored (`BP-19`) |
| `BP-06`  | **`extended_data` is prohibited in the initial profile.** The construction supports an encrypted data field; EPD² does not use it, because a free field beside a ballot is where identity eventually appears. Reintroducing it requires an ADR |
| `BP-07`  | **Write-ins are not supported in the initial profile.** A write-in is free text inside a ballot, it defeats the homomorphic tally, and it is a first-class re-identification channel in small electorates. Recorded as `OD-P16C-02` |

---

## 3. Ballot identity — four values that are not one value

The round task is right to insist these be separated. They are:

| Value                    | Who computes it | Who sees it | Purpose                                            |
| ------------------------ | --------------- | ----------- | ---------------------------------------------------- |
| **`ballot_id`**          | **The client**, from client-side randomness | Client, service, board | The ballot's own identifier |
| **`confirmation_code`**  | **The client**, from the ballot's encryptions and `H_E` | Voter, board, anyone | What the voter looks up |
| **`board_sequence`**     | **The board**, at publication | Everyone | Canonical order |
| **`internal_object_id`** | The service | The service only | Storage key — **never published** |

| ID       | Rule                                                                                                              |
| -------- | --------------------------------------------------------------------------------------------------------------------- |
| `BP-08`  | `ballot_id` is **generated inside the Voting Client from client-side randomness**, independently of any value on the identity side (`BM-01`) |
| `BP-09`  | **No component may compute `ballot_id` from, or verify it against, a continuation reference or a credential ID** (`BM-02`) |
| `BP-10`  | `confirmation_code` is derived **only** from the ballot's own encryptions and the election's extended base hash (`BM-03`). It is not random, so the voter can recompute it; and it is not derived from anything identifying |
| `BP-11`  | **`board_sequence` is assigned by the board at publication and is not the arrival order** (`BM-06`, `BB-11`). It is canonical for ordering and carries no timing information |
| `BP-12`  | **`internal_object_id` is never published, never in the receipt, never in the record, and never appears in any API response.** It exists so that storage does not have to key on a public value |
| `BP-13`  | **None of the four is stable across elections.** Per-context derivation only; no cross-context reuse (`T-P16A-09`) |
| `BP-14`  | `ballot_id` uniqueness is enforced on the board; a duplicate is **rejected, never silently overwritten** (`BM-05`) |

### 3.1 The options considered for `ballot_id`

| Option | Assessment | Verdict |
| ------ | ---------- | ------- |
| **Client random identifier** | No derivation from anything; collision handled by rejection; requires no server involvement before submission | **SELECTED** |
| Hash of the encrypted ballot | Deterministic and elegant, but makes `ballot_id` and `confirmation_code` the same object with two names, and a resubmission of the identical envelope becomes indistinguishable from a duplicate attack | Rejected |
| Confirmation-code-based reference | Same collapse; also puts the voter's lookup value into every internal system | Rejected |
| Board-assigned index | Sequential, so it leaks arrival order — precisely `T-P16A-05` | Rejected |
| Hybrid public reference | Adds a fifth value with no property the other four lack | Rejected |

**Why a client random identifier and not a hash:** keeping `ballot_id`
independent of the ciphertext means a client can retry a *different*
encryption of the same choice without colliding, and means a duplicate
`ballot_id` is unambiguously an error rather than a legitimate retry. The
cost is that `ballot_id` is not self-verifying — which is fine, because the
value the voter and the verifier rely on is the **confirmation code**, and
that one *is* derived and recomputable.

---

## 4. The canonical envelope

```text
EncryptedBallotEnvelope
  schema_version                    encoding_version
  protocol_profile_id               EPD2-HOM-1
  parameter_set_id                  EPD2-CRYPTO-1
  specification_digest              pinned upstream digest
  election_context_id               manifest_digest
  ballot_style_id                   ballot_id
  submission_class                  cast | challenge
  Contest[]
  confirmation_code
  client_build_reference            per BP-17
  retry_token                       per CN-07; stripped before publication

Contest
  contest_id                        contest_sequence_order
  selection_limit                   option_selection_limit
  EncryptedSelection[]
  contest_sum_proof

EncryptedSelection
  selection_id                      sequence_order
  ciphertext (alpha, beta)          range_proof
  plaintext_knowledge_proof         per BM-14
```

**Prohibited in the envelope** — the §2 list, in full, plus:

```text
the continuation capability        any credential reference
any identity                       any shared session/trace ID
IP address                         browser fingerprint
analytics identifier               the ballot nonce (for a cast ballot)
the plaintext selections           internal_object_id
```

| ID       | Rule                                                                                                              |
| -------- | --------------------------------------------------------------------------------------------------------------------- |
| `BP-15`  | **The capability is transmitted alongside the envelope, not inside it**, and is stripped before any storage, logging or publication of the envelope (`CF-11`) |
| `BP-16`  | **`retry_token` is inside the envelope for idempotency and is removed before publication** (`CN-12`). The published envelope is the envelope minus the retry token, and the confirmation code does not cover it |
| `BP-17`  | **`client_build_reference` is a reference to a published, reproducible build**, not a device or user identifier. Where attestation is available it is a build attestation; where it is not, the limitation is published (`OD-P16C-03`) |

---

## 5. Canonical serialization

| ID       | Rule                                                                                                              |
| -------- | --------------------------------------------------------------------------------------------------------------------- |
| `BP-18`  | **Fixed-length big-endian encoding** for all group elements and scalars — 512 bytes mod `p`, 32 bytes mod `q`, 4 bytes for small integers, **no separators** (`DS-01`…`DS-06` lineage) |
| `BP-19`  | **Field order is fixed by the schema**, and serialization is deterministic: the same logical ballot serialises to the same bytes on every implementation |
| `BP-20`  | **Unknown fields are rejected, not ignored.** A lenient decoder is how a covert channel gets into a ballot |
| `BP-21`  | **Duplicate fields are rejected**, not last-wins, not first-wins |
| `BP-22`  | **Non-canonical encodings are rejected** — leading zeros, short forms, over-long forms, out-of-range values, alternate representations of the same value |
| `BP-23`  | **The schema version and encoding version are bound into the confirmation code's derivation context**, so a record cannot be reinterpreted under a different schema later (`BM-34`) |
| `BP-24`  | **A maximum envelope size is published per ballot style**, derived from the style's shape. An envelope exceeding it is rejected before parsing — `submission.too_large` |
| `BP-25`  | Malformed input is rejected with a **distinct reason code per class**, and the parser never partially applies a malformed envelope |

**Why `BP-20` and `BP-22` are stated as hard rejections:** both are the
failure modes that pass silently. A tolerated unknown field is a covert
channel into the published record; a tolerated non-canonical encoding
breaks the domain separation that the whole proof system rests on.

---

## 6. Client-side validation, before encryption

| Check                        | Failure                                          | Reason code                                  |
| ---------------------------- | ------------------------------------------------- | -------------------------------------------- |
| Selection count ≤ limit      | Overvote                                          | `ballot_preparation.overvote`                |
| Selection count < limit      | Undervote — **permitted**, filled with placeholders | `ballot_preparation.undervote_confirmed`   |
| Zero selections in a contest | Blank contest — **permitted**, and confirmed to the voter | `ballot_preparation.blank_contest_confirmed` |
| Zero selections in the ballot| Blank ballot — **permitted**, and confirmed twice  | `ballot_preparation.blank_ballot_confirmed`  |
| Option not in the style      | Invalid candidate                                 | `ballot_preparation.selection_unknown`       |
| Contest not in the style     | Inactive contest                                  | `ballot_preparation.contest_inactive`        |
| Style not in the manifest    | Ballot-style mismatch                             | `manifest.ballot_style_unknown`              |
| Manifest digest differs      | Manifest mismatch                                 | `manifest.digest_mismatch`                   |
| Unsupported election type    | Ranked, STV, cumulative                           | `manifest.election_type_unsupported`         |

| ID       | Rule                                                                                                              |
| -------- | --------------------------------------------------------------------------------------------------------------------- |
| `BP-26`  | **A blank ballot is a valid ballot.** It is encrypted, proved, cast, published and tallied as zero for every option. Refusing it would make abstention visible by its absence |
| `BP-27`  | **Undervotes and blanks are confirmed to the voter, not blocked** — one confirmation for a blank contest, two for a wholly blank ballot, in plain language (`XA-*`) |
| `BP-28`  | **Ranked, STV and cumulative ballots are unsupported** and are refused at manifest validation, not at selection time (`RR-02`). A body using them must change method or stay on the existing process |
| `BP-29`  | Client-side validation is a **usability control, not a security control.** Every check is repeated server-side (`VP-*`), and the server trusts nothing the client asserts |

---

## 7. What binds this ballot to this election and nothing else

```text
election_context_id     in the envelope and in the proof context
manifest_digest         in the envelope and in the extended base hash
parameter_set_id        in the envelope, checked bit-for-bit
specification_digest    in the envelope, pinned
ballot_style_id         in the envelope, checked against the manifest
extended base hash H_E  in every Fiat-Shamir challenge
```

| ID       | Rule                                                                                                          |
| -------- | ----------------------------------------------------------------------------------------------------------------- |
| `BP-30`  | **A ballot valid for one context is invalid for every other**, because the context binding is inside the challenge of every proof, not merely a field beside it |
| `BP-31`  | **A ballot cannot be replayed from a spoiled publication**: `BM-14`'s plaintext-knowledge proof means an attacker copying a published ballot cannot produce a valid submission for it (`T-P16A-17`) |

---

## 8. What this document does not decide

```text
The wire format (JSON, CBOR, other)     → PACK-16D, OD-P16C-04
Maximum sizes in bytes                   → PACK-16D
Attestation technology for BP-17         → OD-P16C-03, PACK-16D
Write-in support                         → OD-P16C-02, a future ADR
extended_data reintroduction             → a future ADR, BP-06
```

**SPECIFIED. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY. NOT LEGALLY
ACTIVATED.**
