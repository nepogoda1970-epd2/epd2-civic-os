# PACK-16B — Fiat–Shamir Transcript and Domain Separation

**Round:** PACK-16B — Cryptographic Parameters, Key Ceremony and Trustee Architecture. **Specification and ADR only. No code. No cryptographic code. Not implemented. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-100`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 0. Why this document exists

`F-INF-2`: weak Fiat–Shamir was found in Helios in 2012, found again in
Swiss Post/Scytl in 2019, and is **still present in Helios master in 2026**
despite a version-4 specification that corrects it (`[E-19]`, `[E-22]`,
`[E-33]`). It is the field's most durable production defect, and it is
invisible: the proofs verify.

This document fixes the transcript model normatively so that
`AC-P16A-039` — *the chosen implementation must be shown by test to use
strong Fiat–Shamir* — has something exact to test against.

---

## 1. The good news, verified

**The selected specification uses strong Fiat–Shamir in all three proof
families.** The challenge includes the statement and the context, not only
the commitment `[F-08]`:

| Proof family                     | Challenge input                                                                              | Statement included?             |
| -------------------------------- | ---------------------------------------------------------------------------------------------- | --------------------------------- |
| Key-ceremony Schnorr PoK         | `H_q(H_P; 0x10, "pk_vote", i, K_{i,0}…K_{i,k−1}, κ_i, h_{i,0}…h_{i,k})`                       | **Yes** — all commitments, the communication key, the guardian index, and the parameter context via the `H_P` key slot |
| Ballot correctness proofs        | `H_q(H_I; 0x24, ind_c, ind_o, α, β, a_0, b_0, …, a_R, b_R)`                                   | **Yes** — the ciphertext, all commitments, contest and option indices, and via `H_I → H_E` the joint keys and the manifest |
| Decryption Chaum–Pedersen        | `H_q(H_E; 0x31, ind_c, ind_o, A, B, a, b, M)`                                                 | **Yes** — the ciphertext, both commitments, the claimed plaintext and the indices |

The specification states the reason itself: *"if the prover knows a
challenge value prior to making its commitment, it can create a false
proof"* `[F-08]`.

**One indirection worth recording.** The joint public key `K` is not a
direct hash input to the ballot proofs; it enters through `H_E` inside
`H_I` `[F-08]`. The binding is real but transitive, so **a verifier that
recomputes `H_I` incorrectly loses the key binding silently**. `TV-06`
makes that a required negative test.

---

## 2. The hash function

```text
H(B₀, B₁) = HMAC-SHA-256(B₀, B₁)
```

| Property                | Requirement                                                                                          |
| ----------------------- | ------------------------------------------------------------------------------------------------------ |
| Construction            | HMAC instantiated with SHA-256 `[F-06]`                                                              |
| First argument `B₀`     | **The HMAC key slot. Exactly 32 bytes, always.** `[F-06]`                                            |
| Second argument `B₁`    | Domain-separation tag followed by data, arbitrary length                                             |
| Purpose                 | HMAC is used **as a random oracle**, not as a MAC and not with a secret key `[F-06]`                  |
| Justification           | Indifferentiability of HMAC with fixed-length keys shorter than the block length, cited in the specification `[F-06]` |
| Reduction               | `H_q(B₀,B₁) = H(B₀,B₁) mod q`, whose near-uniformity depends on `q` being within `189/2²⁵⁶` of `2²⁵⁶` `[F-07]` |

| ID       | Rule                                                                                                          |
| -------- | ---------------------------------------------------------------------------------------------------------------- |
| `FS-01`  | `H` is HMAC-SHA-256 and nothing else. A bare SHA-256 is **not** `H` and must fail a known-answer test          |
| `FS-02`  | The key slot is **always exactly 32 bytes**. A shorter or longer key slot is a defect, not a variant           |
| `FS-03`  | `H_q` is plain reduction. **It is valid only for this `q`** and may not be reused if `q` ever changes `[F-07]` |
| `FS-04`  | The context binding travels in the key slot: `ver`, `H_P`, `H_B`, `H_E` or `H_I` `[F-06]`. **The key slot is never a constant chosen by an implementation** |

---

## 3. Canonical encoding

The specification's unambiguity argument is *"As all byte arrays that
represent input elements have a fixed length, there is no need for a
separator byte or character"* `[F-09]`. **Unambiguity therefore rests
entirely on every field being fixed-length or explicitly length-prefixed**,
and it fails silently if any implementation deviates.

| Type                        | Encoding                                            | Length under `EPD2-CRYPTO-1` |
| --------------------------- | ----------------------------------------------------- | ------------------------------ |
| Integer mod `p`             | big-endian, left zero-padded                        | **512 bytes**                 |
| Integer mod `q`             | big-endian, left zero-padded                        | **32 bytes**                  |
| Small integer (index, n, k, R, L) | big-endian, MSB zero                           | **4 bytes**                   |
| Hash output                 | fed straight back                                   | 32 bytes                      |
| Fixed-length string label   | UTF-8, no terminator                                | its own length                |
| Variable-length string      | `b(len,4)` prefix, then the bytes                    | 4 + len                       |
| File (manifest)             | `b(len,4)` prefix, then the bytes; ≤ 2³¹−1 bytes     | 4 + len                       |

| ID       | Rule                                                                                                                                 |
| -------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `FS-05`  | **Encoding version `EPD2-ENC-1`** is exactly the above. It is a registry field of the parameter set, not an implementation choice        |
| `FS-06`  | **Length-prefixing or fixed length is mandatory for every field.** A field that is neither is a specification defect and must be raised, never guessed |
| `FS-07`  | Integers are **left zero-padded to full length**. A minimally-encoded integer is a different byte string and is **rejected**            |
| `FS-08`  | **Duplicate fields are rejected.** A structure presenting a field twice is refused, never last-wins or first-wins                        |
| `FS-09`  | **Unknown fields are rejected** in any structure that enters a hash. Ignoring an unknown field changes what was hashed                   |
| `FS-10`  | **Field order is canonical and fixed** by the specification. Reordering is a rejection, not a normalisation                              |
| `FS-11`  | A version mismatch between the record's declared specification version and the verifier's is a **refusal to verify**, never a best-effort verification (`CA-05`) |

### 3.1 The rule this document exists to state

```text
NON-CANONICAL OR AMBIGUOUSLY ENCODED CRYPTOGRAPHIC MATERIAL IS REJECTED.
IT IS NEVER SILENTLY NORMALIZED DURING VERIFICATION.
```

| ID       | Consequence                                                                                                            |
| -------- | -------------------------------------------------------------------------------------------------------------------------- |
| `FS-12`  | A verifier **must not** strip padding, re-pad, re-order, canonicalise, trim, coerce types or repair encodings before hashing |
| `FS-13`  | A verifier that normalises **is non-conforming**, even if it then reports the correct result — because it will also accept a forged encoding |
| `FS-14`  | Rejection carries a distinct reason code (`transcript.encoding_non_canonical`) and is **never** reported as a generic parse error |
| `FS-15`  | Non-canonical encoding is a **required negative test** (`TV-05`)                                                        |

`FS-13` is the subtle one. A normalising verifier gives right answers on
honest input and is therefore hard to catch in testing, while accepting two
distinct byte strings for the same statement — which is precisely the
ambiguity fixed-length encoding was adopted to prevent.

---

## 4. Domain separation — the registry

`EPD2-DS-1` is the specification's §5.5 table, adopted **verbatim and in
full**, with the two errata of §7 resolved. The complete tag space `[F-13]`:

### 4.1 Parameters and base hashes

| Tag    | Use                                        | Key slot |
| ------ | ------------------------------------------ | -------- |
| `0x00` | Parameter base hash `H_P`                  | `ver`    |
| `0x01` | Election base hash `H_B` (over the manifest) | `H_P`  |

### 4.2 Key generation

| Tag                   | Use                                                          | Key slot |
| --------------------- | ------------------------------------------------------------ | -------- |
| `0x10` + `"pk_vote"`  | Schnorr PoK challenge, vote-encryption coefficients + `κ_i`   | `H_P`    |
| `0x10` + `"pk_data"`  | Schnorr PoK challenge, ballot-data coefficients + `κ_i`       | `H_P`    |
| `0x11`                | Share-encryption symmetric key `k_{i,ℓ}`                     | `H_P`    |
| `0x12`                | Challenge for the share-encryption nonce Schnorr proof        | `H_P`    |
| `0x13`                | Guardian-record comparison hash `H_G`                        | `H_B`    |
| `0x14`                | Extended base hash `H_E`                                     | `H_B`    |

### 4.3 Ballot encryption and confirmation codes

| Tag    | Use                                                                                  | Key slot        |
| ------ | ------------------------------------------------------------------------------------ | --------------- |
| `0x20` | Selection-encryption identifier hash `H_I`                                           | `H_E`           |
| `0x21` | Per-selection encryption-nonce derivation                                            | `H_I`           |
| `0x22` | KDF seed for ballot-nonce encryption                                                 | `H_I`           |
| `0x23` | Challenge for the ballot-nonce encryption Schnorr proof                              | `H_I`           |
| `0x24` | **All ballot-correctness challenges** — 0/1 disjunctive, general range, and contest selection-limit proofs | `H_I` |
| `0x25` | Contest-data encryption-nonce derivation                                             | `H_I`           |
| `0x26` | KDF seed for contest-data encryption                                                 | `H_I`           |
| `0x27` | Challenge for the contest-data encryption Schnorr proof                              | `H_I`           |
| `0x28` | Contest hash `χ_l`                                                                   | `H_I`           |
| `0x29` | Confirmation code `H_C`; chain initialisation; chain closing                         | `H_I` / `H_E`   |
| `0x2A` | Voting-device information hash `H_DI`                                                | `H_E`           |
| `0x2B` | Chain-closing inner hash                                                             | `H_E`           |

### 4.4 Verifiable decryption

| Tag    | Use                                                                        | Key slot |
| ------ | -------------------------------------------------------------------------- | -------- |
| `0x30` | Guardian commitment hash `d_i` for tally decryption — **the anti-rushing pre-commit** | `H_E` |
| `0x31` | Challenge for the tally-decryption Chaum–Pedersen proof                    | `H_E`    |
| `0x32` | Guardian commitment hash for contest-data decryption                       | `H_I` — see §7 |
| `0x33` | Challenge for the contest-data decryption proof                            | `H_I`    |

### 4.5 Pre-encrypted ballots (optional; not used by `EPD2-HOM-1` v1)

`0x40`–`0x45`. **Not used**, and `DS-07` below governs that.

### 4.6 KDF label and context strings

These use HMAC directly rather than `H`, with UTF-8 string labels `[F-10]`:

| Purpose                    | Label              | Context                                       | Output   |
| -------------------------- | ------------------ | --------------------------------------------- | -------- |
| Guardian share encryption  | `"share_enc_keys"` | `"share_encrypt"` ‖ `b(i,4)` ‖ `b(ℓ,4)`       | 512 bits |
| Ballot-nonce encryption    | `"ballot_nonce"`   | `"ballot_nonce_encrypt"`                      | 256 bits |
| Contest-data encryption    | `"data_enc_keys"`  | `"contest_data"` ‖ `b(ind_c,4)`               | variable |

### 4.7 Rules

| ID       | Rule                                                                                                                        |
| -------- | ------------------------------------------------------------------------------------------------------------------------------- |
| `DS-01`  | **Every label string is underscored.** They are `pk_vote`, `pk_data`, `share_enc_keys`, `share_encrypt`, `ballot_nonce`, `ballot_nonce_encrypt`, `data_enc_keys`, `contest_data` |
| `DS-02`  | Label strings and tag bytes are **byte-exact**. They are never localised, case-folded, trimmed or re-encoded                  |
| `DS-03`  | The tag table is a **registry version** (`EPD2-DS-1`), pinned in the parameter set. A change is a new version, never an edit  |
| `DS-04`  | `0x24` is **overloaded** across three statement types; separation is carried by the *inputs*, not the tag. An implementation must therefore never treat the tag alone as sufficient separation |
| `DS-05`  | Tag values not listed are **unused, not free.** EPD² may not assign meaning to `0x02`–`0x0F`, `0x15`–`0x1F`, `0x2C`–`0x2F`, `0x34`–`0x3F` or `0x46`+, because a future upstream version may |
| `DS-06`  | **EPD²-specific hashes use a separate domain** — §5 — and never occupy an upstream tag                                        |
| `DS-07`  | Unused blocks (pre-encrypted ballots, `0x40`–`0x45`) are **not implemented**; encountering them in a record is a refusal, not a silent skip |
| `DS-08`  | Domain-separation tags are **derived from §5.5 of the pinned specification, never from its changelog** — the changelog itself disclaims completeness for exactly these values `[F-13]` |

`DS-01` is not pedantry. The label strings appear in the specification's
PDF text layer with the underscores rendered as spaces, and the byte
lengths stated alongside them prove the underscores are present `[F-13]`.
**An implementation that copies the labels out of the text layer produces
wrong challenge hashes and fails every interoperability test for a reason
that looks like a cryptographic bug.** `TV-04` makes the label bytes a
required known-answer vector.

`DS-05` is the discipline that keeps `EPD2-DS-1` forward-compatible: the
unused values are reserved by omission, and squatting on them would create
a collision with a future upstream version that EPD² could not detect.

---

## 5. EPD²-specific hashes

PACK-16B introduces artefacts the upstream specification does not have —
the ceremony transcript, its checkpoints, and the complaint records. They
need hashing, and they must not collide with anything upstream.

| ID       | Rule                                                                                                                          |
| -------- | --------------------------------------------------------------------------------------------------------------------------------- |
| `DS-09`  | EPD²-specific hashes use `H` with a **key slot derived for EPD²**, not `H_P`, `H_B`, `H_E`, `H_I` or `ver`                     |
| `DS-10`  | That key slot is `H_X = H(H_B; "epd2_ceremony_v1")` — bound to the election through `H_B`, and unreachable from any upstream computation because no upstream tag byte precedes an EPD² label |
| `DS-11`  | EPD² tags are **strings, not bytes**, so that the EPD² and upstream tag spaces cannot collide by construction: `"transcript"`, `"checkpoint"`, `"complaint"`, `"commitment_round"` |
| `DS-12`  | The EPD² domain is a registry version of its own, pinned in the parameter set alongside `EPD2-DS-1`                            |
| `DS-13`  | **No EPD² hash enters an upstream verification step**, and no upstream verifier is required to know they exist                 |

`DS-13` is what keeps the profile interoperable: a conforming verifier
reads the election record and ignores the ceremony transcript entirely,
because everything it must check is in the record the specification defines.

---

## 6. What a verifier must do — normative

| ID       | Requirement                                                                                                      |
| -------- | ------------------------------------------------------------------------------------------------------------------ |
| `VF-01`  | Recompute `H_P`, `H_B`, `H_E` and `H_I` from published inputs; do not accept published hash values                |
| `VF-02`  | Check group membership before use: `0 ≤ x < p` and `x^q mod p = 1` for every value claimed to be in `Z_p^r` `[F-05]` |
| `VF-03`  | Check `0 ≤ x < q` for every value claimed to be in `Z_q`                                                          |
| `VF-04`  | Recompute every Fiat–Shamir challenge from the statement and context; never trust a published challenge           |
| `VF-05`  | Reject non-canonical encoding (`FS-12`)                                                                          |
| `VF-06`  | Reject an unknown or mismatched specification version (`FS-11`)                                                   |
| `VF-07`  | Report **which** check failed, by reason code, never a generic verification failure                               |
| `VF-08`  | Report what it did **not** check, so that absence of a check is never read as a passed check (`BB-37`)            |

`VF-02` deserves a note. The specification's verification steps check
membership for guardian commitments (2.A) and for every selection
ciphertext (6.A), and the downstream checks rely on those transitively —
Verification 10 does not re-assert membership for the aggregate, and
Verification 3 does not re-assert it for the joint keys `[F-05]`. **A
verifier that skips 2.A or 6.A therefore loses subgroup soundness
everywhere downstream, silently.** `TV-07` makes that a required negative
test.

---

## 7. Two specification inconsistencies, resolved here

Two internal contradictions were found in the pinned specification's hash
section by a single reading pass `[F-19]`. Neither has a published erratum,
because the specification has no errata process `[F-30]`.

| # | Inconsistency                                                                                                                                    | **EPD² resolution**                                        | Basis                                                                     |
| - | -------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------ | --------------------------------------------------------------------------- |
| 1 | The contest-data decryption commitment hash `d_i` (tag `0x32`) is defined with key slot `H_I` in the protocol section and `H_E` in the §5.5 table  | **`H_I`** — the protocol section governs                     | The protocol section defines the computation; the table restates it. Two implementations following different halves cannot complete a contest-data decryption together |
| 2 | The pre-encrypted chain-closing hash (tag `0x44`) is given in the §5.5 table with an extra 4-byte constant `0x4C4F434B` (`"LOCK"`), but the stated total input length is only consistent **without** it | **Without the constant** — and moot in practice              | The regular-ballot analogue has no such constant and totals the same length; the value is a residue of an earlier draft. Block `0x4_` is unused by `EPD2-HOM-1` in any case (`DS-07`) |

| ID       | Rule                                                                                                                                |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| `DS-14`  | Both resolutions are recorded in **EPD²'s own errata record** (`CA-27`) and published with the profile                               |
| `DS-15`  | Both are **reported upstream**, through whatever channel exists, and the report and any response are recorded                        |
| `DS-16`  | If upstream resolves either differently, **EPD² follows upstream** and treats its own resolution as superseded — interoperability wins over being first |
| `DS-17`  | An interoperability test against any independent implementation must include both cases (`TV-08`)                                    |

`DS-16` is the right default. EPD²'s interest is a record any conforming
verifier can check, and being unilaterally correct about a hash input is
worth less than agreeing with everyone else.

---

## 8. What this document does not decide

```text
The ballot-side application of this model      → PACK-16C
The record serialization format                → PACK-16C
The verifier's user interface and reporting    → PACK-16C
The test vectors themselves                    → PACK-16D
Any implementation                             → PACK-16D
```

**SPECIFIED. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY. NOT LEGALLY
ACTIVATED.**
