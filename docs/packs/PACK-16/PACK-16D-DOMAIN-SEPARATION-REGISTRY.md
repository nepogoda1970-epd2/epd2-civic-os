# PACK-16D — Domain Separation Registry (`EPD2-DS-1`)

**Round:** PACK-16D — Cryptographic Implementation Architecture, Reference
Components, Atomic Persistence, Test Vectors and Verification Harness.
**Reference implementation. Not production code. Not certified. Not a PASS.**
**Repository version:** unchanged at `0.16.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-102`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 1. One registry, one way to obtain a label

`REGISTRY_VERSION = "EPD2-DS-1"`, defined in
`services/voting-service/src/epd2_voting_service/reference/crypto/domain_separation.py`.

The registry is a single `StrEnum`, `DomainLabel`, with 25 members. Its
values are the wire labels. A frozenset `_ALL` holds every registered
value, and `require_label()` is the only sanctioned way to turn a string
into a label that a hash will accept.

| ID | Rule |
| -- | ---- |
| `DS-01` | **Every hash and HMAC input in the reference implementation is prefixed with exactly one registered label.** Ad-hoc string literals in cryptographic code are prohibited |
| `DS-02` | `require_label(label)` returns the wire form of a registered label or raises `UnregisteredDomainLabelError` (`reason_code = "VALIDATION_FORBIDDEN_TRANSITION"`). **There is no permissive mode, no warning path and no pass-through.** An unregistered label is a failure, not a new label |
| `DS-03` | The registry is **append-only**. Changing an existing value changes every digest derived under it; that is a new profile version, not an edit |
| `DS-04` | `all_labels()` returns every label in **declaration order**, so the registry has a stable enumeration that a test or an external reviewer can diff |
| `DS-05` | Label values are namespaced and versioned in their own text: every value has the shape `EPD2/v1/<artefact>` |

The hash construction that consumes a label is in `crypto/hashing.py`:

```text
h(key, label, parts) = HMAC-SHA-256(key, TEXT(require_label(label)) || SEQ(parts))
```

| ID | Rule |
| -- | ---- |
| `DS-06` | `HASH_PROFILE = "HMAC-SHA-256"`. `require_label` is called **inside** `h`, so a label cannot reach a digest without passing the registry check — a caller cannot opt out by holding a plain string |
| `DS-07` | The label is `TEXT`-encoded (`EPD2-ENC-1`), so it is length-prefixed and NFC-normalised. It is **part of the preimage, not a prefix convention**: a label cannot merge with the payload that follows it |
| `DS-08` | `h_int` reads the digest as a big-endian integer; `h_q` is `h_int mod q`, the Fiat–Shamir challenge-derivation form. Both go through `h`, so both inherit the registry check |

## 2. The 27 labels

"Call site" lists where the label is used inside
`services/voting-service/src/epd2_voting_service/reference/`. A dash means
the label is registered and **has no call site in this round's code**.

| ID | Label | Wire value | What it covers | Call site this round |
| -- | ----- | ---------- | -------------- | -------------------- |
| `DS-09` | `PARAMETER_SET` | `EPD2/v1/parameter_set` | The digest of a validated `ParameterSet`'s canonical bytes | `crypto/parameters.py:186` |
| `DS-10` | `ELECTION_CONTEXT` | `EPD2/v1/election_context` | The election context / base-hash input binding an election's fixed inputs | — |
| `DS-11` | `MANIFEST` | `EPD2/v1/manifest` | The manifest digest a ballot envelope commits to | `casting/ballot.py:101` |
| `DS-12` | `GUARDIAN_COMMITMENT` | `EPD2/v1/guardian_commitment` | A guardian's key-ceremony commitment, and the share-context binding a threshold share to its ciphertext | `guardians/threshold.py:275` |
| `DS-13` | `GUARDIAN_PROOF` | `EPD2/v1/guardian_proof` | The Schnorr proof-of-possession challenge in the ceremony | `guardians/ceremony.py:291` |
| `DS-14` | `JOINT_PUBLIC_KEY` | `EPD2/v1/joint_public_key` | The joint election public key derived from guardian contributions | — |
| `DS-15` | `BALLOT_NONCE` | `EPD2/v1/ballot_nonce` | Derived per-selection nonces (this round draws nonces from the random source directly) | — |
| `DS-16` | `SELECTION_ENCRYPTION` | `EPD2/v1/selection_encryption` | A single encrypted selection | — |
| `DS-17` | `SELECTION_PROOF` | `EPD2/v1/selection_proof` | The disjunctive Chaum–Pedersen challenge for `m ∈ {0,1}` | `crypto/proofs.py:120` |
| `DS-18` | `CONTEST_PROOF` | `EPD2/v1/contest_proof` | The contest-sum Chaum–Pedersen challenge, prove and verify sides | `crypto/proofs.py:238`, `:265` |
| `DS-19` | `BALLOT_HASH` | `EPD2/v1/ballot_hash` | The digest of a `BallotEnvelope`'s canonical bytes | `casting/ballot.py:171` |
| `DS-20` | `CONFIRMATION_CODE` | `EPD2/v1/confirmation_code` | The confirmation code derived from the base hash and the envelope | `casting/confirmation.py:35` |
| `DS-21` | `CHALLENGE_OPENING` | `EPD2/v1/challenge_opening` | A public-challenge opening (nonces and plaintexts) | — |
| `DS-22` | `CAST_BALLOT` | `EPD2/v1/cast_ballot` | An accepted cast ballot artefact | — |
| `DS-23` | `SPOILED_BALLOT` | `EPD2/v1/spoiled_ballot` | A challenged-and-spoiled ballot artefact | — |
| `DS-24` | `BATCH_LEAF` | `EPD2/v1/batch_leaf` | **Merkle leaf hashing** and the real-leaf hiding commitment | `crypto/merkle.py:40`, `publication/sealed_batches.py:77` |
| `DS-25` | `BATCH_COVER_LEAF` | `EPD2/v1/batch_cover_leaf` | Reserved for cover leaves. **Deliberately unused:** a cover leaf is uniform random bytes, not a hash of anything, so there is nothing to domain-separate | — |
| `DS-26` | `BATCH_ROOT` | `EPD2/v1/batch_root` | **Merkle internal nodes** and the empty-tree root | `crypto/merkle.py:44`, `:48` |
| `DS-27` | `BOARD_ENTRY` | `EPD2/v1/board_entry` | A bulletin-board entry's content digest | `publication/bulletin_board.py:74` |
| `DS-28` | `BOARD_CHECKPOINT` | `EPD2/v1/board_checkpoint` | A checkpoint's content digest, on both the board and the verifier side | `publication/bulletin_board.py:99`, `verification/verifier.py:181` |
| `DS-29` | `ELECTION_RECORD` | `EPD2/v1/election_record` | The election record's digest over its canonical bytes | `election_record/builder.py:195` |
| `DS-30` | `DECRYPTION_SHARE` | `EPD2/v1/decryption_share` | The Chaum–Pedersen challenge for a guardian decryption share, prove and verify sides | `crypto/proofs.py:296`, `:317` |
| `DS-31` | `TALLY` | `EPD2/v1/tally` | Tally and reconciliation artefacts | `testing/vectors.py:333` (vector generation only) |
| `DS-32` | `VERIFICATION_RESULT` | `EPD2/v1/verification_result` | A verification result | — |
| `DS-52` | `AUDIT_RECORD` | `EPD2/v1/audit_record` | An audit record's digest | `audit.py:71` |
| `DS-53` | `CEREMONY_TRANSCRIPT` | `EPD2/v1/ceremony_transcript` | A guardian ceremony transcript's digest | `guardians/ceremony.py:245` |
| `DS-54` | `BOARD_SIGNATURE` | `EPD2/v1/board_signature` | The signer-registry digest — the trust anchor a verifier is handed, not the checkpoint it signs | `publication/checkpoint_signing.py:141` |

| ID | Rule |
| -- | ---- |
| `DS-33` | `test_domain_labels_are_unique_and_registered` in `tests/reference/test_crypto_units.py` asserts that the labels are pairwise unique, that there are at least 24, that `require_label` round-trips every enum member, and that an unregistered value (`EPD2/v1/not-registered`) raises |
| `DS-34` | `test_hash_is_domain_separated` asserts that the same payload under `BALLOT_HASH` and under `CONFIRMATION_CODE` yields different digests. The separation property is tested, not assumed |

## 3. No unkeyed convenience wrapper

`hashing.py` exposes `h`, `h_int` and `h_q`. All three are keyed. There is
no `hash(label, parts)` helper, and adding one is prohibited.

| ID | Rule |
| -- | ---- |
| `DS-35` | **An unkeyed digest is expressed as a keyed digest under `ZERO_KEY`** — 32 zero bytes — not as a separate function. `ZERO_KEY` appears explicitly at the call site |
| `DS-36` | The reason is call-site discipline. A convenience wrapper is the shortest path in the file, so it becomes the default; once it is the default, keyed and unkeyed uses stop being visibly different, and a hash context can be reused across artefact kinds without anyone noticing. Making the zero key explicit means the choice is written down at every call site and shows up in review and in diffs |
| `DS-37` | Passing `ZERO_KEY` does not weaken the separation. The separation comes from the label inside the preimage (`DS-07`), not from the key |

## 4. Never truncate

| ID | Rule |
| -- | ---- |
| `DS-38` | `DIGEST_BYTES = 32`. `h` returns the **full** 32-byte HMAC-SHA-256 output, always |
| `DS-39` | **Truncation is not offered.** PACK-16D requires a truncation rule per use; the reference implementation's rule is "never truncate", which is the only rule with no per-use decision to get wrong. There is no length parameter to `h` |
| `DS-40` | `h_q` is a reduction, not a truncation: the whole digest is read as an integer and reduced modulo `q`, so every bit of the digest contributes |

## 5. The Merkle tree carries RFC 6962's leaf/node distinction through labels

RFC 6962 §2.1 distinguishes leaf hashes from internal-node hashes by
prefixing the hash input with `0x00` for a leaf and `0x01` for a node.
Without that distinction an internal node can be presented as a leaf, and
an inclusion proof can be forged.

EPD² already has a registry, so `crypto/merkle.py` carries the same
distinction through labels instead of prefix bytes:

| Construction | RFC 6962 | `crypto/merkle.py` |
| ------------ | -------- | ------------------ |
| Leaf hash | `SHA-256(0x00 \|\| leaf)` | `h(ZERO_KEY, BATCH_LEAF, [encode_bytes(leaf)])` |
| Internal node | `SHA-256(0x01 \|\| left \|\| right)` | `h(ZERO_KEY, BATCH_ROOT, [encode_seq([left, right])])` |
| Empty tree | hash of the empty string | `h(ZERO_KEY, BATCH_ROOT, [encode_uint(0, 8)])` |

| ID | Rule |
| -- | ---- |
| `DS-41` | **The separation property is identical: no internal node can be reinterpreted as a leaf.** It is enforced through one registry rather than through two conventions that each implementation must remember |
| `DS-42` | The tree is **unkeyed** — every hash uses `ZERO_KEY`. These are public commitments over public artefacts. A leaf's content stays secret because of the 32-byte salt inside the leaf preimage, not because of the tree |
| `DS-43` | The tree shape is RFC 6962's split at the largest power of two strictly below `n`. The earlier draft duplicated the last node on odd levels — the CVE-2012-2459 shape, in which two different leaf sequences share a root. **That construction was replaced, not patched** |

## 6. Limitations — stated, not softened

| ID | Limitation |
| -- | ---------- |
| `DS-44` | **Nine of the 27 labels have no call site in this round** (`DS-10`, `DS-14`, `DS-15`, `DS-16`, `DS-21`, `DS-22`, `DS-23`, `DS-25`, `DS-32`). They are registered ahead of the code that will use them. A registered label with no call site has never been exercised against a real preimage. The nine are named in code by the frozenset `RESERVED_WITHOUT_CALL_SITE`, and `test_verifier_branches.test_reserved_domain_labels_are_declared_accurately` asserts that the set is exactly the set of labels with no call site, so the claim cannot drift |
| `DS-44a` | **The reserved set shrank by two in the correction round.** `GUARDIAN_COMMITMENT` and `GUARDIAN_PROOF` acquired real call sites when the threshold ceremony arrived, and a label that is in use must not stay on a list of labels that are not. The frozenset was edited in the same change as the call sites, because the test that keeps the two honest would otherwise have failed — which is the point of having it |
| `DS-45` | **`VERIFICATION_RESULT` no longer does double duty.** It previously covered the audit record's digest as well, because no audit label existed — two artefact kinds under one label, which is precisely what a domain-separation registry is meant to prevent. `AUDIT_RECORD` (`DS-52`) was added and `audit.py:71` now digests under it; because values are append-only (`DS-03`), every audit record digest changed when it landed. `VERIFICATION_RESULT` itself now has no call site (`DS-44`) |
| `DS-46` | **Three hash call sites bypass the registry entirely, and none computes a protocol digest.** `casting/idempotency.py:15` computes the request digest as a bare `hashlib.sha256(...)` with no label and no key — a local storage key, never published; `crypto/randomness.py:108` generates counter-mode blocks inside `DeterministicTestRandomSource`; and `publication/bulletin_board.py` derives a 32-byte Ed25519 seed from a short human-readable **test** key with a bare `hashlib.sha256(...)`, so that a fixture string cannot become a short key |
| `DS-46a` | **The checkpoint signature is no longer one of them.** The first candidate signed with a bare unlabelled HMAC; the signing input now goes through `h()` under `BOARD_CHECKPOINT` (`DS-28`), so a signature over some other EPD² structure can never be presented as a checkpoint signature. That is a domain-separation property, not only a signature-scheme one |
| `DS-47` | **Nothing statically prevents a new bypass.** `require_label` is a runtime gate on `h`, not a prohibition on importing `hmac` or `hashlib`. No lint rule and no AST test asserts that cryptographic modules obtain their digests only through `hashing.h` — unlike the verifier, whose import boundary *is* asserted by an AST test. Adding that check is unfinished work |
| `DS-48` | **`REGISTRY_VERSION = "EPD2-DS-1"` is not pinned by any test.** The schema registry's `EPD2-SCHEMA-1` is asserted in `tests/reference/test_invariants.py:293`; the domain-separation registry version has no equivalent assertion, so a silent edit of the version string would not fail the suite |
| `DS-49` | `h_q` reduces a 256-bit digest modulo `q`. When `\|q\|` equals the digest length the reduction is not exactly uniform over `[0, q)`. The deviation is negligible in size, but it is not zero and **no test measures it** |
| `DS-50` | The labels commit to an artefact *kind*, not to a protocol version beyond the `v1` in the value. Cryptographic agility — what happens to every digest when the hash profile changes — is PACK-16B's `EPD2-AGILITY` question and is not solved here |
| `DS-51` | No constant-time property is claimed for any hash call site (`OD-P16D-05`) |

## 7. What this document does not decide

```text
An AUDIT_RECORD label and the audit digest  → added; DS-52, DS-45
CEREMONY_TRANSCRIPT and BOARD_SIGNATURE     → added; DS-53, DS-54
Labelled checkpoint signing input           → done; DS-46a
Which labels the ceremony uses              → answered; DS-12, DS-13, DS-53
Static enforcement against raw hmac/hashlib → unfinished; PACK-17
Hash profile migration / agility            → PACK-16B, EPD2-AGILITY
External conformance of any digest          → narrowed; the Node.js oracle
                                              re-derives seven of these
                                              digests independently and
                                              agrees. OD-P16D-02 stays open
                                              for a complete implementation
```

**REFERENCE IMPLEMENTATION. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY.
NOT LEGALLY ACTIVATED.**
