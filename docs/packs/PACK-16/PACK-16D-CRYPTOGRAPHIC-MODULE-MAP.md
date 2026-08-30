# PACK-16D — Cryptographic Module Map

**Round:** PACK-16D — Network-Enabled Finalization: Lockfile Regeneration,
Immutable ElectionGuard Provenance and Final Acceptance Alignment.
**Reference implementation. Not production code. Not certified. Not a PASS.**
**Repository version:** unchanged at `0.16.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-102`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 1. What is under `crypto/`

```text
services/voting-service/src/epd2_voting_service/reference/crypto/
  __init__.py
  domain_separation.py    encoding.py     hashing.py      randomness.py
  parameters.py           elgamal.py      proofs.py       merkle.py
  signature_provider.py
  profiles/EPD2-CRYPTO-1.json
  profiles/EPD2-TESTONLY-NOTCONFORMANT-P4096-Q256.params
  profiles/EPD2-TESTONLY-NOTCONFORMANT-P1024-Q160.params
```

Nine substantive modules and three parameter artefacts. `crypto/ed25519.py`
— the hand-written Ed25519 of the previous candidate — **is deleted**. It
was not moved and not deprecated; the file is gone, and
`crypto/signature_provider.py` (§2.9) takes its place as a port over a
vetted library rather than an implementation. Four further modules carry
cryptography outside this package — `guardians/ceremony.py`,
`guardians/threshold.py`, `publication/checkpoint_signing.py` and
`testing/conformance.py` — and are mapped in §2.10, because they are
protocol layers built on `crypto/` rather than primitives. This document
maps each one's exported surface and its permitted dependencies, and states
the two rules that make the whole set reviewable: one hash function, one
label registry.

The reference package is **45 Python modules** in total, counted across
`reference/` and its six subpackages.

| ID      | Rule                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `CM-01` | **Nothing under `crypto/` imports anything outside `crypto/`** within this repository. The cryptographic core knows nothing about ballots, batches, boards, stores, records or capabilities. It can be reviewed, and its vectors regenerated, in isolation                                                                                                                                                                                                                                                                                                               |
| `CM-02` | **The dependency graph within `crypto/` is acyclic and every import is fully qualified.** There are no relative imports and no dynamic imports anywhere in the reference package, so the graph is readable statically                                                                                                                                                                                                                                                                                                                                                    |
| `CM-44` | **The reference package has exactly one third-party import, in exactly one module.** `crypto/signature_provider.py` imports `cryptography`; the other 44 modules import only the Python standard library and other `reference/` modules. This is not a convention: `test_handwritten_ed25519_not_imported` in `tests/reference/test_checkpoint_signatures.py` parses every `*.py` under `reference/` with `ast` and fails if any module other than `signature_provider.py` names `cryptography`, or if any module imports or defines curve arithmetic under any filename |

---

## 2. The module map

### 2.1 `crypto/domain_separation.py` — the label registry

|                       |                                                                                                                                                                          |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Exports**           | `DomainLabel` (`StrEnum`, 27 members), `REGISTRY_VERSION = "EPD2-DS-1"`, `RESERVED_WITHOUT_CALL_SITE`, `UnregisteredDomainLabelError`, `require_label()`, `all_labels()` |
| **May depend on**     | nothing inside `reference/` — `enum` only                                                                                                                                |
| **May not depend on** | every other module, including `encoding` and `hashing`. It is the root of the graph and must stay there                                                                  |

The 27 labels, in declaration order: `PARAMETER_SET`, `ELECTION_CONTEXT`,
`MANIFEST`, `GUARDIAN_COMMITMENT`, `GUARDIAN_PROOF`, `JOINT_PUBLIC_KEY`,
`BALLOT_NONCE`, `SELECTION_ENCRYPTION`, `SELECTION_PROOF`,
`CONTEST_PROOF`, `BALLOT_HASH`, `CONFIRMATION_CODE`, `CHALLENGE_OPENING`,
`CAST_BALLOT`, `SPOILED_BALLOT`, `BATCH_LEAF`, `BATCH_COVER_LEAF`,
`BATCH_ROOT`, `BOARD_ENTRY`, `BOARD_CHECKPOINT`, `ELECTION_RECORD`,
`DECRYPTION_SHARE`, `TALLY`, `VERIFICATION_RESULT`, `AUDIT_RECORD`,
`CEREMONY_TRANSCRIPT`, `BOARD_SIGNATURE`. Each wire value has the form
`EPD2/v1/<name>`.

`CEREMONY_TRANSCRIPT` and `BOARD_SIGNATURE` were appended for the guardian
ceremony and the signer registry (`CM-04` — appending is permitted, editing
is not). **`GUARDIAN_COMMITMENT` and `GUARDIAN_PROOF` now have call
sites** — `quorum_digest()` in `guardians/threshold.py` and the Schnorr
proof-of-possession challenge in `guardians/ceremony.py` — and are no
longer members of `RESERVED_WITHOUT_CALL_SITE`.

| ID      | Rule                                                                                                                                                                                                                                                                                                                                          |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CM-03` | **`require_label()` is the only way to obtain a label**, and it raises `UnregisteredDomainLabelError` (`reason_code = "VALIDATION_FORBIDDEN_TRANSITION"`) for anything not in the registry. An ad-hoc string literal in cryptographic code is prohibited and fails closed rather than silently producing a digest under an unreviewed context |
| `CM-04` | **Label values are append-only.** Changing one changes every digest derived under it. That is a new profile version, not an edit                                                                                                                                                                                                              |

### 2.2 `crypto/encoding.py` — `EPD2-ENC-1`

|                       |                                                                                                                                                                                                                                                                                                       |
| --------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Exports**           | `ENCODING_VERSION = "EPD2-ENC-1"`, `MAX_BYTES_LEN`, `MAX_SEQ_LEN`, `MAX_TEXT_LEN`, `CanonicalEncodingError`, `encode_uint()`, `decode_uint()`, `encode_bytes()`, `normalize_text()`, `encode_text()`, `encode_seq()`, `encode_struct()`, `encode_group_element()`, `encode_scalar()`, `encode_bool()` |
| **May depend on**     | nothing inside `reference/` — `unicodedata` and `collections.abc` only                                                                                                                                                                                                                                |
| **May not depend on** | every other module. A canonical encoding that depended on a parameter set or a label would have two versions of itself                                                                                                                                                                                |

The grammar, from the module's own docstring:

```text
UINT(n, width)  ->  width bytes, big-endian, fixed width, no leading-zero
                    stripping and no short forms
BYTES(b)        ->  UINT(len(b), 4) || b
TEXT(s)         ->  BYTES(NFC(s).encode("utf-8"))
SEQ(items)      ->  UINT(len(items), 4) || concat(encode(item))
FIELD(name, v)  ->  TEXT(name) || encode(v)
STRUCT(fields)  ->  UINT(len(fields), 4) || concat(FIELD(...)) in
                    declaration order, never sorted, never a map
```

| ID      | Rule                                                                                                                                                                                                                                                                                                                                 |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `CM-05` | **This is a binary tuple encoding, deliberately not "JSON that happens to look stable".** Ordinary JSON leaves key order, integer/float ambiguity, Unicode escaping and whitespace under-specified, so two conforming encoders can produce different bytes for one value. Hashes are computed over these bytes and over nothing else |
| `CM-06` | **Field order is normative and `encode_struct` never sorts.** Maps are prohibited as an input type, because a map has no order and therefore no canonical form                                                                                                                                                                       |
| `CM-07` | **Duplicate field names are rejected** with `CanonicalEncodingError`                                                                                                                                                                                                                                                                 |
| `CM-08` | **Text is NFC-normalised before encoding**, so two Unicode spellings of one string encode identically                                                                                                                                                                                                                                |
| `CM-09` | **Group elements are always the full `\|p\|` bytes and scalars always the full `\|q\|` bytes.** There is no short form for two implementations to disagree about, and `decode_uint` rejects an input of the wrong width rather than padding it                                                                                       |

### 2.3 `crypto/hashing.py` — the hash profile

|                       |                                                                                             |
| --------------------- | ------------------------------------------------------------------------------------------- |
| **Exports**           | `HASH_PROFILE = "HMAC-SHA-256"`, `DIGEST_BYTES = 32`, `ZERO_KEY`, `h()`, `h_int()`, `h_q()` |
| **May depend on**     | `domain_separation`, `encoding`                                                             |
| **May not depend on** | `parameters`, `elgamal`, `proofs`, `merkle`, `randomness`, and anything outside `crypto/`   |

```text
h(key, label, parts)      = HMAC-SHA-256(key, TEXT(require_label(label)) || SEQ(parts))
h_int(key, label, parts)  = h(...) read as a big-endian integer
h_q(key, label, parts, q) = h_int(...) mod q          the challenge-derivation form
```

| ID      | Rule                                                                                                                                                                                                             |
| ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CM-10` | **There is deliberately no unkeyed convenience wrapper.** An unkeyed digest is expressed as a keyed one under `ZERO_KEY`, so no call site can reuse a hash context across artefact kinds by omitting an argument |
| `CM-11` | **The truncation rule is "never truncate".** `DIGEST_BYTES` is always 32 and `h()` offers no length parameter                                                                                                    |

### 2.4 `crypto/randomness.py`

|                       |                                                                                                                                                                                                                                       |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Exports**           | `TEST_PROFILE_ENV = "EPD2_VOTING_REFERENCE_TEST_PROFILE"`, `RandomnessUnavailableError`, `DeterministicSourceForbiddenError`, `RandomSource` (Protocol), `ProductionRandomSource`, `DeterministicTestRandomSource`, `select_source()` |
| **May depend on**     | nothing inside `reference/` — `secrets`, `hashlib`, `os`, `typing` only                                                                                                                                                               |
| **May not depend on** | every other module. Randomness must not be derivable from a parameter set, a label or an encoding                                                                                                                                     |

| ID      | Rule                                                                                                                                                                                                                                                                                                                                                                                           |
| ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CM-12` | **`ProductionRandomSource` has no seed parameter, no reseed hook and no fallback.** On any CSPRNG failure it raises `RandomnessUnavailableError` (`CRYPTO_RANDOMNESS_UNAVAILABLE`) rather than degrading. `random_below` uses rejection sampling over whole bytes drawn through `random_bytes`, so a CSPRNG failure surfaces through the same fail-closed path rather than as a bare `OSError` |
| `CM-13` | **`DeterministicTestRandomSource` requires two independent guards**: `allow_in_test=True` **and** the environment marker `EPD2_VOTING_REFERENCE_TEST_PROFILE=1`. Either alone raises `DeterministicSourceForbiddenError` (`CRYPTO_TEST_MODE_REACHABLE`), so neither a stray keyword nor a stray environment variable is sufficient                                                             |
| `CM-14` | **`select_source()` accepts only the literal string `"production"`.** Every other value — including `"test"`, `"deterministic"`, `""` and `"PRODUCTION"` — raises. There is no code path by which it can return a deterministic source, and this is asserted by test rather than by convention                                                                                                 |
| `CM-15` | **`RandomSource` is the only randomness interface cryptographic code may depend on.** No module under `crypto/` may call `secrets` or `os.urandom` directly; `secrets` is imported in this module and nowhere else in the package                                                                                                                                                              |

### 2.5 `crypto/parameters.py`

|                       |                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| --------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Exports**           | `Q_ELECTIONGUARD_2_1`, `ParameterValidationError`, `ParameterProfileUnavailableError`, `ProfileSubstitutionError`, `is_probable_prime()`, `ParameterSet`, `validate_parameter_set()`, `is_in_subgroup()`, `require_in_subgroup()`, `PROFILE_DIR`, `PROFILE_BIT_LENGTHS`, `PROFILE_REGISTRY`, `EPD2_CRYPTO_1_PARAMETER_DIGEST`, `TARGET_PROFILE_ID`, `TEST_ONLY_MARKER`, `is_target_profile()`, `require_target_profile()`, `load_profile()`, `load_target_profile()` |
| **May depend on**     | `domain_separation`, `encoding`, `hashing`                                                                                                                                                                                                                                                                                                                                                                                                                           |
| **May not depend on** | `elgamal`, `proofs`, `merkle`, `randomness`, and anything outside `crypto/`                                                                                                                                                                                                                                                                                                                                                                                          |

`ParameterSet` is frozen and slotted, carrying `parameter_set_id`,
`profile_version`, `provenance`, `production_use_permitted`, `p`, `q`,
`g`, with `canonical_bytes()` and a `digest()` taken under
`DomainLabel.PARAMETER_SET`.

| ID      | Rule                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `CM-16` | **A parameter set is never trusted by identifier.** Every load runs `validate_parameter_set()`, which checks in order and fails closed on the first violation: `\|p\|` matches expectation, `\|q\|` matches expectation, `p` and `q` both exceed 2, `q \| p−1`, `1 < g < p`, `g^q ≡ 1 mod p`, then optionally probable-primality of `q` and of `p`                                                                                                                                                                                                     |
| `CM-17` | **`is_probable_prime()` is a small-prime sieve plus Miller–Rabin, and its docstring says explicitly that it is not a proof of primality.** No document may upgrade that statement                                                                                                                                                                                                                                                                                                                                                                      |
| `CM-18` | **`EPD2-CRYPTO-1` is the target profile and it loads**, from the artefact `profiles/EPD2-CRYPTO-1.json`, whose primary source, parameter digest and arithmetic verification are recorded in `PACK-16D-PARAMETER-PROFILE-IMPLEMENTATION.md` §1. Validation is fail-closed, the expected bit lengths come from `PROFILE_BIT_LENGTHS` **in code**, and **there is no fallback**: `load_profile` has no `except` branch, no default and no reference to a test profile, and `require_target_profile()` raises `ProfileSubstitutionError` for anything else |
| `CM-19` | What is asserted first-hand and tested about the small prime: `Q_ELECTIONGUARD_2_1 == 2**256 - 189`, 256 bits, probable-prime — arithmetic, so it cannot carry a transcription error                                                                                                                                                                                                                                                                                                                                                                   |
| `CM-20` | **`production_use_permitted` is `False` on every profile `load_profile()` can return, including the target**, and both test `.params` files carry the four-line banner `TEST ONLY / NOT EPD2-CRYPTO-1 / NOT ELECTIONGUARD 2.1 CONFORMANCE / NOT PRODUCTION`                                                                                                                                                                                                                                                                                            |

The three shipped profiles:

| Profile                                  | \|p\| | \|q\|                  | Verified properties                                                                                                                                                                      |
| ---------------------------------------- | ----- | ---------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `EPD2-CRYPTO-1`                          | 4096  | 256 (`q = 2²⁵⁶ − 189`) | the full set: `q \| p−1`, `p = q·r + 1`, `g^q ≡ 1 mod p`, `1 < g < p`, probable-primality of `p`, `q` and `r/2`, the leading and trailing 256 one-bits of `p`, and the `ln(2)` agreement |
| `EPD2-TESTONLY-NOTCONFORMANT-P4096-Q256` | 4096  | 256 (`q = 2²⁵⁶ − 189`) | `q \| p−1`, `g^q ≡ 1 mod p`, `1 < g < p`                                                                                                                                                 |
| `EPD2-TESTONLY-NOTCONFORMANT-P1024-Q160` | 1024  | 160                    | the same, plus primality of both `p` and `q`                                                                                                                                             |

`EPD2-TESTONLY-NOTCONFORMANT-P4096-Q256` shares only the _dimensions_ of
`EPD2-CRYPTO-1`: it is **not** those constants and lacks that family's
r/2-prime property, which is why shape alone was never accepted as a
substitute. `EPD2-TESTONLY-NOTCONFORMANT-P1024-Q160` is cryptographically
inadequate by construction and exists only to make property and concurrency
tests fast. `TEST_ONLY_MARKER = "TESTONLY-NOTCONFORMANT"` is asserted by
test to appear in every non-target profile id.

### 2.6 `crypto/elgamal.py` — `EPD2-HOM-1`

|                       |                                                                                                                                                                                                                   |
| --------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Exports**           | `MAX_EXPONENT_SEARCH = 1024`, `PlaintextDomainError`, `DecryptionDomainError`, `Ciphertext`, `validate_ciphertext()`, `validate_public_key()`, `random_nonce()`, `encrypt()`, `accumulate()`, `decode_exponent()` |
| **May depend on**     | `encoding`, `parameters`, `randomness`                                                                                                                                                                            |
| **May not depend on** | `proofs`, `merkle`, and anything outside `crypto/`                                                                                                                                                                |

```text
Encrypt(m; r) = (g^r mod p,  K^r · g^m mod p)
```

| ID      | Rule                                                                                                                                                                                                                     |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `CM-21` | **Homomorphic accumulation is componentwise multiplication, and `accumulate([])` is an error — never the identity element.** An empty accumulation is a caller defect, and returning an encryption of zero would hide it |
| `CM-22` | **`encrypt()` rejects any plaintext outside `[0, max_message]` with `PlaintextDomainError`. It never clamps**                                                                                                            |
| `CM-23` | **`decode_exponent()` is a bounded search with `MAX_EXPONENT_SEARCH = 1024`** and raises `DecryptionDomainError` outside the bound rather than looping                                                                   |
| `CM-24` | **There is no arbitrary-message encryption.** The protocol only ever encrypts exponents, so offering more would be unused, untested attack surface                                                                       |

### 2.7 `crypto/proofs.py`

|                       |                                                                                                                                                                                                                     |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Exports**           | `ProofGenerationError`, `DisjunctiveProof`, `ChaumPedersenProof`, `prove_selection()`, `verify_selection()`, `prove_contest_sum()`, `verify_contest_sum()`, `prove_decryption_share()`, `verify_decryption_share()` |
| **May depend on**     | `domain_separation`, `encoding`, `hashing`, `parameters`, `elgamal`, `randomness`                                                                                                                                   |
| **May not depend on** | `merkle`, and anything outside `crypto/`                                                                                                                                                                            |

Three proof kinds: disjunctive Chaum–Pedersen that a selection encrypts
`m ∈ {0,1}`; Chaum–Pedersen that a contest's accumulated ciphertext
encrypts exactly its selection limit; Chaum–Pedersen that a decryption
share was computed under the secret its public commitment names.

| ID      | Rule                                                                                                                                                                                                                                                                                                         |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `CM-25` | **No new proof system is invented.** These are the standard constructions of the adopted ElectionGuard lineage, re-expressed over this repository's canonical encoding and domain-separation registry                                                                                                        |
| `CM-26` | **Fiat–Shamir challenges are taken over domain-separated hashes bound to a context that includes the base hash, the ballot id, the contest id and the option id**, so a proof does not transfer to another selection or another ballot                                                                       |
| `CM-27` | **Every verify function checks subgroup membership of every proof element and the range of every scalar before evaluating any equation**                                                                                                                                                                     |
| `CM-28` | **Constant-time behaviour is not claimed, and `crypto/proofs.py` says so in its own source.** Python big-integer arithmetic and `pow(a, b, m)` give no side-channel guarantee (`OD-P16D-05`)                                                                                                                 |
| `CM-29` | **The decryption-share proof on its own establishes one share, not a quorum.** The quorum is established by `guardians/threshold.py` (§2.10), which takes `k` from the ceremony transcript and refuses a smaller set. The single-guardian path (`guardian_index = 1`) remains for the non-threshold fixtures |

### 2.8 `crypto/merkle.py`

|                       |                                                                                                                                                                 |
| --------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Exports**           | `MerkleError`, `leaf_hash()`, `node_hash()`, `empty_root()`, `root()`, `inclusion_proof()`, `verify_inclusion()`, `consistency_proof()`, `verify_consistency()` |
| **May depend on**     | `domain_separation`, `encoding`, `hashing`                                                                                                                      |
| **May not depend on** | `parameters`, `elgamal`, `proofs`, `randomness`, and anything outside `crypto/`                                                                                 |

See §4, which this module exists to explain.

### 2.9 `crypto/signature_provider.py` — a port, not an implementation

This module replaced `crypto/ed25519.py`, which is deleted. The previous
candidate carried Edwards-curve point arithmetic, point compression, scalar
multiplication, private-key expansion, signing and verification, all
written here. It followed RFC 8032 and it agreed with OpenSSL on every
vector it was given, and an independent audit still failed it — correctly.
Agreement on the vectors an author thought to write is not the property
that matters for a low-level primitive; the property that matters is the
vulnerability class the author did not think of, and that is found by years
of adversarial attention paid to one widely deployed implementation.

So the arithmetic is gone. What remains is a **port**: a declaration of
what the publication layer needs from a signature scheme, and an adapter
from a vetted library to it.

|                       |                                                                                                                                                                                                                                                                                                                  |
| --------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Exports**           | `PUBLIC_KEY_BYTES = 32`, `SIGNATURE_BYTES = 64`, `PRIVATE_KEY_BYTES = 32`, `SIGNATURE_PROFILE = "Ed25519 (RFC 8032, PureEdDSA, SHA-512)"`, `SignatureProviderUnavailableError`, `SignatureFormatError`, `CheckpointSignatureProvider` (Protocol), `CryptographyEd25519Provider`, `PROVIDER`, `active_provider()` |
| **May depend on**     | nothing inside `reference/` — `typing` and the third-party `cryptography` package only                                                                                                                                                                                                                           |
| **May not depend on** | every other module. It is a primitive layer, and a primitive that reached for a parameter set or a label would not be one                                                                                                                                                                                        |

**The port.** `CheckpointSignatureProvider` is a `@runtime_checkable`
`Protocol` carrying a `profile` string and exactly six operations:

```text
generate_test_keypair(seed)                    -> (private_key_bytes, public_key_bytes)
load_public_key(raw)                           -> a public key object
sign_checkpoint(private_key_bytes, message)    -> signature bytes
verify_checkpoint(public_key_bytes, msg, sig)  -> bool
public_key_bytes(public_key)                   -> raw 32 bytes
signature_bytes(signature)                     -> raw 64 bytes
```

**The single active provider** is `CryptographyEd25519Provider`, with
`profile = "Ed25519 (RFC 8032, PureEdDSA, SHA-512)"` and
`backend = "cryptography (OpenSSL Ed25519)"`. It is instantiated once as
the module-level singleton `PROVIDER`, reachable through `active_provider()`
for callers that prefer a function to a global.

| ID      | Rule                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CM-39` | **The signature primitive is supplied by a vetted library and is not implemented in this repository.** Every method of `CryptographyEd25519Provider` is argument validation and canonical encoding around a library call. Curve arithmetic reappearing in this module is the defect the module exists to prevent, and `test_handwritten_ed25519_not_imported` (`CM-44`) fails if it does                                                                                                                                                                                                                                                                                              |
| `CM-40` | **There is exactly one provider and no selection mechanism.** `PROVIDER` is a module-level `Final` singleton. There is no configuration key, environment variable or plugin lookup that can choose a different one, because a provider an operator can choose is a provider an operator can get wrong                                                                                                                                                                                                                                                                                                                                                                                 |
| `CM-41` | **Constant-time behaviour is still not claimed.** The signing surface moved to OpenSSL, which pursues side-channel resistance; EPD² has measured nothing, and the group arithmetic everywhere else in `crypto/` remains pure Python. `OD-P16D-05` is **narrowed, not closed**                                                                                                                                                                                                                                                                                                                                                                                                         |
| `CM-45` | **There is no fallback, deliberately.** `cryptography` is imported at module scope. If it is absent the import raises `SignatureProviderUnavailableError` (reason code `SIGNATURE_PROVIDER_UNAVAILABLE`) and the process does not start. A `try: import cryptography / except: use our own curve code` would silently reinstate the removed implementation on whichever machine happened to lack the dependency — the one machine you would least want running hand-rolled cryptography. `test_missing_provider_fails_closed` runs the import in a subprocess with the module blocked, together with a control run, and asserts the import fails rather than succeeding by a fallback |
| `CM-46` | **Only strict raw canonical encodings are accepted. No PEM, no DER, no base64.** A public key is exactly 32 raw bytes, a signature exactly 64, a private key exactly 32; a length that is not exactly right is a malformed input rather than an alternative encoding, and is refused with `SignatureFormatError` (reason code `BOARD_SIGNATURE_INVALID`). Accepting several encodings would let two byte strings name one key, and a registry keyed on bytes would then hold two entries for one signer                                                                                                                                                                               |
| `CM-47` | **`verify_checkpoint` returns `False` on every defect and never raises on bad input.** A malformed key, a malformed signature and a genuine mismatch are indistinguishable at this layer on purpose: the distinction a reader needs — unknown signer, unauthorised signer, altered bytes — is drawn by `publication/checkpoint_signing.py`, which holds the registry to draw it with. A primitive that reported on trust would be two mechanisms wearing one name                                                                                                                                                                                                                     |
| `CM-48` | **The provider has no opinion on whose key it is holding.** It answers "is this signature valid for this key over these bytes" and nothing else. Signer authorisation lives in `SignerRegistry` and the election context (`CM-43`)                                                                                                                                                                                                                                                                                                                                                                                                                                                    |

### 2.10 Cryptographic modules outside `crypto/`

These are protocol layers, not primitives. They are listed here because a
reader auditing the cryptography needs to know they exist and where their
boundaries are; their behaviour is owned by the documents named beside them.

| Module                              | Exported surface (principal)                                                                                                                                                                                                                                                                 | May depend on                                                                                                          | Owned by                                                  |
| ----------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------- |
| `guardians/ceremony.py`             | `QuorumPolicy`, `SchnorrProof`, `GuardianRecord`, `GuardianSecret`, `CeremonyTranscript`, `prove_possession()`, `verify_possession()`, `verify_share()`, `run_ceremony()`, `derive_joint_public_key()`, `guardian_public_share_key()`, `verify_ceremony()`, `compensated_decryption_share()` | `crypto/` only                                                                                                         | `PACK-16D-THRESHOLD-GUARDIAN-REFERENCE-IMPLEMENTATION.md` |
| `guardians/threshold.py`            | `ThresholdShare`, `share_context()`, `compute_share()`, `verify_share()`, `lagrange_coefficient()`, `combine_shares()`, `quorum_digest()`                                                                                                                                                    | `crypto/`, `guardians/ceremony`                                                                                        | the same document                                         |
| `publication/checkpoint_signing.py` | `CHECKPOINT_SCHEMA_VERSION = "EPD2-CHECKPOINT-2"`, `SIGNATURE_PROFILE`, `CheckpointSignatureOutcome`, `SignerRecord`, `SignerRegistry`, `CheckpointPayload`, `sign_checkpoint()`, `verify_checkpoint()`                                                                                      | `crypto/` only                                                                                                         | `PACK-16D-CHECKPOINT-SIGNATURE-AND-SIGNER-TRUST-MODEL.md` |
| `testing/conformance.py`            | `EvidenceClass`, `ConformanceVector`, `PRIMARY_SOURCE_UNAVAILABLE`, `serialize()`                                                                                                                                                                                                            | everything — it is under `testing/`, which nothing else imports (`IA-08` in `PACK-16D-IMPLEMENTATION-ARCHITECTURE.md`) | `PACK-16D-EXTERNAL-CONFORMANCE-REPORT.md`                 |

| ID      | Rule                                                                                                                                                                                                                        |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CM-42` | **The guardian package depends on `crypto/` and nothing else in `reference/`**, so the ceremony and the threshold path can be reviewed against the primitives without the casting, publication or record layers             |
| `CM-43` | **`publication/checkpoint_signing.py` never reads a key out of the artefact it verifies.** The trust anchor is the `SignerRegistry` supplied alongside the export, and `CheckpointPayload` has no `public_key` field at all |

---

## 3. The two rules that hold the set together

| ID      | Rule                                                                                                                                                                                                                                                                                                                                                                                          |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CM-30` | **Every domain-separated protocol digest in the system is computed by `crypto/hashing.h()`.** Parameter sets, manifests, ballots, confirmation codes, challenge openings, batch leaves, batch roots, board entries, board checkpoints, election records, decryption shares, tallies and audit records all derive their digests through that one function, under a label from the one registry |
| `CM-31` | **Every domain label comes from `crypto/domain_separation.py` through `require_label()`.** There is no second registry, no per-module constant and no string literal. `require_label()` is called inside `h()`, so the check cannot be bypassed by a call site that forgets it                                                                                                                |

A cover leaf is the one published value that is deliberately **not** a
digest: `cover_leaf()` returns `DIGEST_BYTES` of uniform randomness drawn
from the `RandomSource`, with no opening, no salt and no artefact
reference. It is not a hash of anything, so `CM-30` does not apply to it.
One consequence is worth recording for an auditor reading the registry
against the code: the registered label `BATCH_COVER_LEAF` has no call
site in the reference implementation or its tests.

### 3.1 The direct uses of `hashlib`/`hmac` outside `crypto/hashing.py`

`CM-30` is a strong claim, so its exceptions are named rather than left
for an auditor to find. **Four** modules use `hashlib` directly. None of
them computes a protocol digest.

The list is one shorter than it was. `crypto/ed25519.py` used
`hashlib.sha512(...)` for the SHA-512 that is part of the Ed25519 algorithm
itself; that module is deleted, and the hashing inside the signature scheme
now happens inside the vetted library, where this repository does not call
`hashlib` at all.

| Where                           | What it does                                                                               | Why it is not a `CM-30` violation                                                                                                                                                                                                                                                                                                     |
| ------------------------------- | ------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `crypto/parameters.py`          | `hashlib.sha256(p_hex \|\| q_hex \|\| g_hex \|\| r_hex)` in `_artifact_parameter_digest()` | An artefact-integrity digest over a file's own textual constants, compared against the value pinned in code. It is not a protocol digest and never enters a transcript; the parameter set's protocol digest is taken through `h()` under `PARAMETER_SET`                                                                              |
| `publication/bulletin_board.py` | `hashlib.sha256(signing_key)` in `_seed()`                                                 | Derives a 32-byte **TEST-ONLY** Ed25519 private key from a fixture's short signing-key string, so that a short string cannot become a short key; a value already of the right length is used as-is. It hashes a key, not an artefact. A production board holds a real key in a key store this reference implementation does not model |
| `casting/idempotency.py`        | `hashlib.sha256(canonical_request).hexdigest()` in `request_digest()`                      | A local storage key scoping `(election_context_id, operation, idempotency_key)`. It is never published, never verified by anyone, and never enters a transcript                                                                                                                                                                       |
| `crypto/randomness.py`          | `hashlib.sha256(seed \|\| counter)` inside `DeterministicTestRandomSource`                 | Counter-mode block generation for the test source. It produces randomness, not a digest of an artefact, and is unreachable without both guards of `CM-13`                                                                                                                                                                             |

| ID      | Rule                                                                                                                                                                             |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CM-32` | **Any new direct use of `hashlib` or `hmac` outside `crypto/hashing.py` requires the same explicit justification as the four above, recorded here.** The default answer is `h()` |

---

## 4. The Merkle construction was replaced, not patched

| ID      | Rule                                                                                                                                  |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| `CM-33` | **The first draft of `crypto/merkle.py` duplicated the last node on odd levels. That construction was replaced in full, not amended** |

**Why the previous shape was unsafe.** Duplicating the last node on an
odd level means that two _different_ leaf sequences can produce the same
root — the second-preimage shape recorded as CVE-2012-2459. Concretely,
a tree over `n` leaves whose last node is duplicated is indistinguishable
at the root from a tree over `n + 1` leaves whose last two leaves are
equal. For this system that is not an abstract defect: a batch commitment
is exactly a Merkle root over a fixed-capacity leaf sequence, and a
publisher who can present two different leaf sequences under one
published root can claim after the fact that a batch contained a
different set of artefacts than it did. Everything the sealed-batch layer
is for — that the commitment binds the occupancy before the opening is
published — would rest on a root that does not bind.

That is not a bug to patch at the edges. A construction whose root is
ambiguous has to be exchanged for one whose root is not.

**What replaced it.** RFC 6962 §2.1: the empty tree hashes the empty
sequence, a one-leaf tree is its leaf hash, and an `n`-leaf tree splits at
the largest power of two **strictly below** `n`. The split point is a
function of `n` alone, so a given leaf sequence has exactly one tree.

**Domain separation.** RFC 6962 prefixes `0x00` for leaves and `0x01` for
internal nodes. EPD² already has a label registry, so the distinction is
carried by the label instead: leaves hash under `BATCH_LEAF`, internal
nodes under `BATCH_ROOT`. The separation property is the same — no
internal node can be reinterpreted as a leaf — and it is enforced through
one registry rather than two conventions.

| ID      | Rule                                                                                                                                                                                                                                                                            |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CM-34` | **The tree is unkeyed: every hash uses `ZERO_KEY`.** These are public commitments over public artefacts. Secrecy of a leaf's _content_ comes from the salt inside the leaf preimage, not from the tree                                                                          |
| `CM-35` | **Consistency proofs (RFC 6962 §2.1.2) were added with the replacement**, so an old tree can be proved a prefix of a new one                                                                                                                                                    |
| `CM-36` | **`verify_consistency()` is the standard iterative algorithm and deliberately not a mirror of the prover's recursion.** A verifier that re-ran the prover's own recursion would agree with the prover by construction and would prove nothing                                   |
| `CM-37` | The replacement was **verified exhaustively for every tree size 1…32 and every `(old, new)` pair**, not on sampled sizes                                                                                                                                                        |
| `CM-38` | **What the Merkle layer does not give is cross-mirror split-view detection.** `verify_board()` detects rollback, equivocation and a broken checkpoint chain **within a single exported view**. Gossip between mirrors is not implemented and must not be claimed (`OD-P16D-06`) |

---

## 5. What this document does not decide

```text
What is in and out of scope this round      → PACK-16D-SCOPE-AND-IMPLEMENTATION-BOUNDARY.md
Layering, placement and dependency direction → PACK-16D-IMPLEMENTATION-ARCHITECTURE.md
Language and dependency policy                → PACK-16D-LANGUAGE-AND-DEPENDENCY-ASSESSMENT.md
How the locked `cryptography` dependency
  was resolved and verified                    → PACK-16D-LANGUAGE-AND-DEPENDENCY-ASSESSMENT.md §4.1
Appropriateness of the EPD2-CRYPTO-1
  parameters                                  → VO-08, PACK-16B external review
A second complete independent
  implementation                              → OD-P16D-02, PACK-17
Constant-time bignum path                     → OD-P16D-05, PACK-17
Cross-mirror gossip                           → OD-P16D-06, PACK-17
Ceremony custody, HSM and authenticated
  channels                                    → OD-P16D-11, PACK-16B, PACK-17
Non-crypto modules (casting, publication,
  election record, verification, testing)     → the documents that own them
```

**REFERENCE IMPLEMENTATION. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY.
NOT LEGALLY ACTIVATED.**
