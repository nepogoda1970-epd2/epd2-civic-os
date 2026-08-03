# PACK-16D — Ballot Cryptography Implementation

**Round:** PACK-16D — Cryptographic Implementation Architecture, Reference
Components, Atomic Persistence, Test Vectors and Verification Harness.
**Reference implementation. Not production code. Not certified. Not a PASS.**
**Repository version:** unchanged at `0.16.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-102`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 1. What this document describes

The ballot half of the reference implementation as it is actually written:
`crypto/elgamal.py`, `casting/ballot.py` and `casting/confirmation.py`
under
`services/voting-service/src/epd2_voting_service/reference/`. Proof
construction and verification are described in
`PACK-16D-PROOF-IMPLEMENTATION.md`; the capability state machine in
`PACK-16D-CONTINUATION-STATE-IMPLEMENTATION.md`.

Every statement below is a statement about code in this repository. Where
the implementation is narrower than the PACK-16A/16B/16C specification, §10
says so.

## 2. The encryption scheme

| ID | Rule |
| -- | ---- |
| `BC-01` | The scheme is **exponential ElGamal over the order-`q` subgroup**: `Encrypt(m; r) = (g^r mod p, K^r · g^m mod p)`, where `K` is the election public key. `Ciphertext` is a frozen dataclass of exactly two integers, `alpha` and `beta` |
| `BC-02` | **There is no arbitrary-message encryption.** `encrypt()` encrypts an exponent and nothing else. Offering a general message API would be unused, untested attack surface, so it is not offered |
| `BC-03` | Homomorphic accumulation is componentwise multiplication modulo `p`, which adds the plaintext exponents. `accumulate()` is the only aggregation path |
| `BC-04` | **Every ciphertext component is checked for order-`q` subgroup membership before it is used.** `validate_ciphertext()` calls `require_in_subgroup()` on both `alpha` and `beta`; `is_in_subgroup(v)` is `0 < v < p` **and** `v^q ≡ 1 mod p`. `accumulate()` re-validates every input on every call, not once at the boundary |
| `BC-05` | `encrypt()` validates the public key (`validate_public_key`) and the nonce range (`0 < r < q`) on every call. A nonce outside the range raises `ParameterValidationError` |
| `BC-06` | `random_nonce()` returns `1 + random_below(q − 1)`, i.e. a uniform value in `[1, q−1]`. Zero is not a possible nonce |

Group elements are serialised at the full `|p|` byte width and scalars at
the full `|q|` byte width by `encode_group_element` / `encode_scalar`
(`EPD2-ENC-1`). There is no short form, so two implementations cannot
disagree about leading zeros.

## 3. The plaintext domain is closed, and violations are rejected

| ID | Rule |
| -- | ---- |
| `BC-07` | `encrypt(message, ..., max_message=1)` raises `PlaintextDomainError` (`BALLOT_PREPARATION_CONTEST_INVALID`) for any `message` outside `[0, max_message]`. **It never clamps, never truncates and never reduces modulo anything.** A caller that offers `2` where `1` is the bound gets an exception, not a `1` |
| `BC-08` | Clamping is prohibited because a clamp silently changes a voter's ballot into a different valid ballot. A rejection is visible to the caller and to the test suite; a clamp is invisible to both |
| `BC-09` | `accumulate([])` raises `PlaintextDomainError`. **An empty list is an error, never the identity element `(1, 1)`** |

`BC-09` is worth stating explicitly because returning the identity would be
the mathematically natural choice. It is refused because
`Ciphertext(1, 1)` is a valid-looking encryption of `0` under any key: a
contest that lost all of its selections through a bug would then
accumulate to a well-formed ciphertext of zero and could pass a sum proof
constructed against the same empty set. Making the empty case unreachable
removes that whole class of silent-zero failure. The negative corpus
exercises the domain rule directly in `test_neg_invalid_scalar`.

## 4. Bounded exponent decode

| ID | Rule |
| -- | ---- |
| `BC-10` | `decode_exponent(g^m, params, maximum=n)` recovers `m` by iterating `g^0, g^1, …, g^n` and comparing. It is a **linear bounded search, not a general discrete-logarithm routine** |
| `BC-11` | `MAX_EXPONENT_SEARCH = 1024`. A request with `maximum > MAX_EXPONENT_SEARCH` raises `DecryptionDomainError` (`TALLY_MISMATCH`) **before** the loop starts |
| `BC-12` | A value that does not decode inside `[0, maximum]` raises `DecryptionDomainError`. The function never returns a "closest" or "unknown" answer and never loops unbounded |

The bound is safe only because the plaintext domain is closed: a selection
is `0` or `1` and a contest total is bounded by its selection limit, so the
tally exponent is bounded by the number of accepted ballots. In
`election_record/builder.py` the decode is called with
`maximum=len(accepted)`. **An election with more than
`MAX_EXPONENT_SEARCH` accepted ballots in one contest option would fail
closed at decode time in this reference implementation.** That is a
reference-scale limitation, not a protocol limit; a production
implementation needs a giant-step/baby-step decode or a larger bound.

## 5. Placeholder selections and structural indistinguishability

`encrypt_ballot()` builds, for each contest in the ballot style:

1. one encryption per **real option**, of `1` if the option was chosen and
   `0` otherwise;
2. then `selection_limit` **placeholder selections**, with option ids of
   the form `<contest_id>#placeholder-<index>`, of which the first
   `selection_limit − len(chosen)` encrypt `1` and the rest encrypt `0`.

| ID | Rule |
| -- | ---- |
| `BC-13` | **Every contest accumulates to exactly its selection limit.** The placeholders absorb the undervote; the sum is `selection_limit` whether the voter selected all, some or none of the options |
| `BC-14` | A contest therefore always carries exactly `len(option_ids) + selection_limit` encrypted selections. `verify_ballot_proofs()` recomputes that number from the manifest and rejects any other count as `BallotStructureError` |
| `BC-15` | **An undervote, a blank contest and a fully-selected contest are structurally identical**: the same number of ciphertexts, the same number of proofs, the same serialised shape, and the same accumulated plaintext. Nothing in the envelope distinguishes them |
| `BC-16` | Consequently **there is no "abstain" or "blank" marker anywhere in the envelope**, and none may be added. A marker would be a plaintext field that separates blank ballots from voted ones, which is exactly the distinction placeholders exist to erase |
| `BC-17` | An **overvote** — more selections than the limit — is refused at preparation with `OvervoteError` (`BALLOT_PREPARATION_OVERVOTE`). An unknown option id is refused with `BallotStructureError`. Neither is silently dropped |

Evidence: `test_undervote_is_absorbed_by_placeholders` builds a ballot with
one contest partly filled and one contest empty, asserts the selection
count equals `len(option_ids) + selection_limit` for every contest, and
then verifies all proofs.
`test_a_blank_contest_still_produces_a_valid_ballot` builds a wholly blank
ballot, verifies its proofs and verifies its challenge opening.
`test_neg_overvote` asserts the overvote rejection.

The placeholder mechanism is the reason the contest sum proof is a proof of
a *fixed* value (`PR-05` in `PACK-16D-PROOF-IMPLEMENTATION.md`) rather than
a range proof: because the target is always `selection_limit`, the proof
reveals nothing about how many real options were chosen.

## 6. `BallotEnvelope` — exactly six fields, none of them an identity

```text
BallotEnvelope
  ballot_id            election_context_id   ballot_style_id
  parameter_set_id     manifest_digest       contests
```

| ID | Rule |
| -- | ---- |
| `BC-18` | `BallotEnvelope` is a frozen, slotted dataclass with **exactly these six fields and no others**. `contests` holds `EncryptedContest` values, each holding its `EncryptedSelection` tuple, its accumulated ciphertext and its sum proof |
| `BC-19` | **No field is an identity, a credential, a capability, a session, a device, an address or a timestamp**, and none may be added. There is no `voter_id`, no `credential_id`, no `capability_reference`, no `submitted_at` |
| `BC-20` | The absence is enforced by test, not by review. `test_ballot_envelope_carries_no_identity_field` reads `BallotEnvelope.__slots__`, asserts set equality against the six names, and asserts the intersection with `{voter_id, identity, credential_id, capability_reference}` is empty |
| `BC-21` | `canonical_bytes()` encodes the six fields **in declaration order** under `EPD2-ENC-1`; `encode_struct` never sorts. `digest()` is `h(ZERO_KEY, BALLOT_HASH, [canonical_bytes])` |
| `BC-22` | Four identity values are kept structurally distinct and are never derived from one another: `internal_object_id` (operational, never published), `ballot_id` (the public reference), `confirmation_code` (derived from the encryptions and `H_E`) and the board position (assigned at publication) |

`verify_ballot_proofs()` binds the envelope to its context before it looks
at any cryptography: the election context id must equal the manifest's, the
`manifest_digest` must equal the recomputed manifest digest, the
`parameter_set_id` must equal the active parameter set's, the contest count
and contest order must match the ballot style. Each of those four is a
named negative case (`test_neg_wrong_election_context`,
`test_neg_wrong_manifest_digest`, `test_neg_wrong_ballot_style`, and the
count check in the same function).

## 7. `ballot_id` is client-random and structureless

| ID | Rule |
| -- | ---- |
| `BC-23` | `new_ballot_id()` returns `source.random_bytes(32).hex()` — **32 bytes from the random source, rendered as 64 lowercase hex characters** (`BALLOT_ID_BYTES = 32`) |
| `BC-24` | It is **not** a hash, **not** a counter, **not** a timestamp, **not** derived from the ballot content, and **not** derived from the capability, the credential or any identity. There is nothing in it to walk back to a person, and nothing in it to order two ballots by |
| `BC-25` | It is drawn **client-side, before encryption**, and is then used as the Fiat–Shamir context prefix for every proof on the ballot (see `PR-07`) and as the `submission_reference` on the leaf reservation |
| `BC-26` | Two independently drawn ids must differ and must contain no structure. `test_ballot_id_is_client_random_and_structureless` asserts the 64-character length, inequality across two sources, and that the value is pure hex |

Because `ballot_id` is not derived from content, a ballot's public
reference tells a reader nothing about what it contains. Because it is not
sequential, it tells a reader nothing about when it arrived. Arrival order
is not the board order either — `board_sequence` is assigned at
publication and shuffled within the batch (`BE-00`).

## 8. Confirmation code

| ID | Rule |
| -- | ---- |
| `BC-27` | `derive_confirmation_code(envelope, params, base_hash)` is `h(ZERO_KEY, CONFIRMATION_CODE, [STRUCT(base_hash, envelope.canonical_bytes())])`, rendered in a 32-character alphabet. **That preimage is exported as `confirmation_input(envelope, params, base_hash)`**, so an independent implementation can be handed the input and derive the code itself rather than being handed the code and asked to agree with it. The cross-implementation oracle uses exactly that route |
| `BC-28` | **Its only inputs are the ballot's own encryptions and the election base hash `H_E`.** No capability, no credential, no identity, no nonce and no plaintext enters the derivation. Nothing secret is an input |
| `BC-29` | It is therefore **recomputable by anybody holding the published ballot**, and that is the point: it lets a voter match a code to a published artefact. **It is not, and must never be described as, evidence of how the voter voted** — the same code is derivable by any third party from public data, and the code is a function of ciphertexts, which do not reveal the plaintext |
| `BC-30` | It is **not** a receipt of intent, **not** a proof of eligibility and **not** a secret. A coercer who obtains it learns which published artefact is referred to, and nothing about its content |
| `BC-31` | Rendering: `CONFIRMATION_GROUPS = 5` groups of `CONFIRMATION_GROUP_LEN = 5` characters, joined by `-`, over `CONFIRMATION_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"` (32 symbols; `0`, `1`, `I`, `O` and `l` are excluded so that transcription errors are less likely) |
| `BC-32` | The rendering consumes the digest low-symbol-first, 25 symbols of 5 bits each: **125 bits of the 256-bit digest are exposed, and the remaining bits are discarded.** This is a display truncation of the code, not a truncation of the hash — `DIGEST_BYTES` is always 32 and `h()` never truncates |
| `BC-33` | The code is deterministic for a given envelope and differs between two ballots with identical selections, because the envelopes differ in `ballot_id` and in every nonce. `test_confirmation_code_is_deterministic_and_ballot_specific` asserts both halves |

`test_confirmation_code_shape_and_alphabet` asserts the five-group shape,
the group length, that every character is in the alphabet, and that the
alphabet shares no character with `01IOl`.

## 9. Challenge opening and the re-encryption check

A public evidentiary challenge publishes the ballot's opening — the nonce
and the plaintext of every selection — so that any reader can re-encrypt
and confirm the ciphertexts were formed as claimed. `BallotOpening` carries
`ballot_id`, `nonces` and `plaintexts` and is returned to the client by
`encrypt_ballot()`; the cast path never publishes it.

| ID | Rule |
| -- | ---- |
| `BC-34` | `verify_challenge_opening()` first checks `opening.ballot_id == envelope.ballot_id`, and raises `ChallengeOpeningError` (`CHALLENGE_REENCRYPTION_MISMATCH`) otherwise. **An opening for a different ballot does not open this one** (`test_neg_cast_nonce_revealed`) |
| `BC-35` | For **every** selection in **every** contest it recovers the nonce for that option id, re-runs `encrypt(message, nonce, public_key, params)` and compares **both** `alpha` and `beta` against the published ciphertext. Any mismatch raises `ChallengeOpeningError` |
| `BC-36` | A selection for which the opening carries **no nonce** is a failure (`"opening is incomplete"`), not a skipped check. A partial opening cannot pass |
| `BC-37` | The check is a **direct group-element comparison**, not a hash comparison and not a proof check. It is deterministic and needs no randomness |
| `BC-38` | The comparison covers placeholder selections exactly as it covers real ones, so a challenger cannot open the real options and leave the placeholders unopened |
| `BC-39` | The same function is the **local** cast-as-intended check: a client re-encrypts from its own opening without contacting the service. `test_p11_local_challenge_causes_no_server_state` runs 40 local checks and asserts that continuations, accepted ballots, spoiled ballots, slot ownership, the outbox and the board are byte-for-byte unchanged |

Two behaviours of this function must be read exactly as written rather than
generously:

- A selection whose option id is present in `nonces` but **absent from**
  `plaintexts` is re-encrypted with message `0`
  (`plaintext_by_option.get(option_id, 0)`). An opening that omits a
  plaintext is therefore treated as an opening that claims zero, and
  succeeds only if the ciphertext really encrypts zero under that nonce.
  It does not fail as a malformed opening.
- The function recomputes the per-selection Fiat–Shamir context but does
  **not** use it: it does not re-verify the selection proofs. Proof
  verification is a separate step. `submit_public_challenge()` calls
  `verify_ballot_proofs()` first and `verify_challenge_opening()` second,
  inside the same transaction, so the published path does both; a caller
  that invokes the opening check alone gets only the re-encryption check.

## 10. Limitations of this implementation, stated plainly

| ID | Limitation |
| -- | ---------- |
| `BC-40` | **Constant-time behaviour is not claimed.** Python `int` arithmetic and `pow(a, b, m)` offer no side-channel guarantee. Every operation in this document is variable-time with respect to its secret inputs. A production implementation needs a constant-time bignum path (`OD-P16D-05`) |
| `BC-41` | **Secret material is not zeroized.** Python cannot reliably overwrite an immutable `int` or `bytes` and the garbage collector may copy. Nonces and openings remain in memory until collected. This is stated as an unsolved limitation, not a solved problem |
| `BC-42` | **There is no nonce-reuse detector.** Each selection draws a fresh nonce from the random source, and a proof is bound to its context so a copied proof does not transfer — but a caller that passes the same nonce twice is not caught by any check in `elgamal.py` |
| `BC-43` | **Ballot cryptography runs on the real `EPD2-CRYPTO-1` profile** — see `BC-47`. `production_use_permitted` is nevertheless `False` on every profile the loader can return, including the target: loading the published parameters is not authorisation to run an election on them, and `VO-08` remains **OPEN** |
| `BC-44` | **A threshold decryption path exists, and the single-guardian path remains beside it.** `tally_accepted()` still computes one share with one secret and records `guardian_index = 1` for the non-threshold fixtures; `tally_accepted_threshold()` is the multi-guardian path, taking its quorum from the ceremony transcript. Nothing in *this* document is evidence about the ceremony — that is `PACK-16D-THRESHOLD-GUARDIAN-REFERENCE-IMPLEMENTATION.md` |
| `BC-45` | **Full interoperability is not established.** The parameters now come from a primary source and the encryption, encoding and accumulation paths are cross-checked by an independent Node.js oracle, but no comparison against another *complete* ElectionGuard implementation exists (`OD-P16D-02`). The 23 internal stability vectors remain stability-only |
| `BC-46` | `DomainLabel.BALLOT_NONCE` and `DomainLabel.CHALLENGE_OPENING` are registered in `EPD2-DS-1` but have **no call site** in this round: nonces are drawn from the random source rather than derived by hash, and the opening check compares group elements rather than digests. A registered-but-unused label is a specification obligation not yet consumed, not a hidden code path. Both are named in the registry's `RESERVED_WITHOUT_CALL_SITE` frozenset, which a test asserts is exactly the set of labels with no call site |

### 10.1 Measured cost on the real profile

`BC-43` has a price, and it is stated rather than left to be discovered.
These are benchmark figures on `EPD2-CRYPTO-1`, not capacity figures, and
no validation was disabled to obtain them:

```text
single selection encryption                 0.014 s
selection proof generation                  0.076 s
selection proof verification                0.205 s
ballot encryption (1 contest, 3 slots)      0.529 s
ballot proof verification                   0.889 s
peak RSS                                   18.8 MB
```

| ID | Rule |
| -- | ---- |
| `BC-47` | **The whole ballot path runs on `EPD2-CRYPTO-1`**: `test_epd2_crypto_1_encrypt_verify`, `test_epd2_crypto_1_challenge_opening` and `test_epd2_crypto_1_homomorphic_tally` encrypt, prove, verify, open a challenge, derive a confirmation code and accumulate a tally on the real parameters. The fast test profile is retained for the property and concurrency suites because a 4096-bit exponentiation is roughly forty times the cost of the 1024-bit one — not because the real profile is unavailable |

## 11. What this document does not decide

```text
Appropriateness of the group parameters     → VO-08, PACK-16B external review
Threshold ceremony and quorum decryption    → PACK-16D-THRESHOLD-GUARDIAN-REFERENCE-IMPLEMENTATION.md
Constant-time arithmetic and zeroization    → OD-P16D-05, PACK-17
A second complete independent
  implementation                            → OD-P16D-02, PACK-17
Tally decode above MAX_EXPONENT_SEARCH      → PACK-17
Ballot-style and manifest governance         → PACK-16A
Receipt wording shown to a voter             → PACK-16C receipt specification
BSI conformity / VO-08                       → OPEN, PACK-16B review + PACK-17
```

**REFERENCE IMPLEMENTATION. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY.
NOT LEGALLY ACTIVATED.**
