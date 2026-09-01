# PACK-16D — Proof Implementation

**Round:** PACK-16D — Cryptographic Implementation Architecture, Reference
Components, Atomic Persistence, Test Vectors and Verification Harness.
**Reference implementation. Not production code. Not certified. Not a PASS.**
**Repository version:** unchanged at `0.16.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-102`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 1. Scope

`crypto/proofs.py` and the proof call sites in `casting/ballot.py`,
`election_record/builder.py` and `guardians/`. Ballot construction and the
envelope are described in
`PACK-16D-BALLOT-CRYPTOGRAPHY-IMPLEMENTATION.md`; the ceremony that the
last two proof kinds belong to is described in
`PACK-16D-THRESHOLD-GUARDIAN-REFERENCE-IMPLEMENTATION.md`.

**No new proof system is invented.** The constructions are the standard
ones of the adopted ElectionGuard lineage, re-expressed over this
repository's canonical encoding (`EPD2-ENC-1`) and domain-separation
registry (`EPD2-DS-1`). This document describes what the code does, and
§7 says what it does not do.

## 2. The proof family

| ID      | Kind                                                                                          | Statement proved                                                                                                       | Type                                                  | Domain label       |
| ------- | --------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------- | ------------------ |
| `PR-01` | **Selection** — `prove_selection` / `verify_selection`                                        | the ciphertext encrypts `m ∈ {0, 1}`                                                                                   | `DisjunctiveProof` (`a0, b0, a1, b1, c0, c1, v0, v1`) | `SELECTION_PROOF`  |
| `PR-02` | **Contest sum** — `prove_contest_sum` / `verify_contest_sum`                                  | the contest's accumulated ciphertext encrypts **exactly** its `selection_limit`                                        | `ChaumPedersenProof` (`a, b, challenge, response`)    | `CONTEST_PROOF`    |
| `PR-03` | **Decryption share** — `prove_decryption_share` / `verify_decryption_share`                   | `log_g(guardian_public) = log_alpha(share)`, i.e. the share was computed with the secret its public commitment names   | `ChaumPedersenProof`                                  | `DECRYPTION_SHARE` |
| `PR-32` | **Proof of possession** — `prove_possession` / `verify_possession` in `guardians/ceremony.py` | the guardian knows the constant term `a_{i,0}` of the polynomial whose commitment `K_{i,0} = g^{a_{i,0}}` it published | `SchnorrProof` (`commitment, challenge, response`)    | `GUARDIAN_PROOF`   |
| `PR-33` | **Threshold decryption share** — `compute_share` / `verify_share` in `guardians/threshold.py` | `M_l = alpha^{s_l}` for the same `s_l` whose public image `g^{s_l}` the verifier derived from the ceremony commitments | `ChaumPedersenProof`, wrapped in a `ThresholdShare`   | `DECRYPTION_SHARE` |

`PR-32` is a Schnorr proof: the guardian commits to a fresh nonce,
challenges itself over a canonical struct naming the guardian, the
election, the parameter set, its public key and its commitment, and
responds `nonce + challenge·secret mod q`. Without it, a guardian could
publish a commitment to a value it does not hold, and the failure would
only surface at decryption time when it is too late.

`PR-33` reuses the `PR-03` primitive but the _statement_ differs: the
public value it is checked against is `guardian_public_share_key()`,
derived from the published commitments alone, so a verifier checks a
guardian's share without ever seeing `s_l`. Its context binds the
election, the parameter set, the contest, the option **and the guardian
sequence**, so a share proved for one guardian does not verify for
another.

`PR-01` is a **disjunctive** Chaum–Pedersen: the prover runs the real
protocol for the branch that is true and simulates the other branch by
choosing its challenge and response first and solving for the commitments.
`prove_selection` refuses any `message` other than `0` or `1` with
`ProofGenerationError` (`BALLOT_PROOF_GENERATION_FAILED`) — the proof
system is not defined outside the bit domain and does not pretend to be.

`PR-02` is a plain Chaum–Pedersen against the shifted target
`target_b = beta · g^(q − (selection_limit mod q)) mod p`, i.e. the
accumulated `beta` with `g^selection_limit` divided out. It proves equality
of two discrete logarithms and therefore that the accumulated ciphertext's
exponent is exactly `selection_limit`. It is a proof of a **fixed** value,
not a range proof, and that is only sound because placeholder selections
force every contest to that fixed value (`BC-13`). It follows that the
proof leaks nothing about how many real options were chosen.

`PR-03` proves the share is consistent with the guardian public value —
one share, never a quorum. The threshold path derives each guardian's
public share value `g^{s_l}` from the ceremony's published commitments and
proves against that; the non-threshold fixture path still uses one guardian
with `guardian_index = 1`. Which path a record was built through is
therefore a question a reader must ask before citing `PR-03` for anything
(see `PR-24`).

## 3. Fiat–Shamir: what the transcript contains

Every challenge is `h_q(ZERO_KEY, <label>, [payload], q)`, which is
`HMAC-SHA-256(ZERO_KEY, TEXT(label) || SEQ(payload)) mod q`. The payload is
a canonical `STRUCT` — ordered, never sorted, fixed-width, length-prefixed.

| ID      | Kind             | Payload fields, in order                                                                                      |
| ------- | ---------------- | ------------------------------------------------------------------------------------------------------------- |
| `PR-04` | Selection        | `context`, `public_key`, `alpha`, `beta`, `a0`, `b0`, `a1`, `b1`                                              |
| `PR-05` | Contest sum      | `context`, `base_b = public_key`, `target_a = accumulated.alpha`, `target_b`, `commitment_a`, `commitment_b`  |
| `PR-06` | Decryption share | `context`, `base_b = alpha`, `target_a = guardian_public`, `target_b = share`, `commitment_a`, `commitment_b` |

The transcript therefore always covers **the statement and the
commitments**, so a prover cannot choose commitments after seeing the
challenge, and a verifier that recomputes the challenge from the published
values gets a different challenge for any altered statement.

## 4. What the context binds, and why a proof does not transfer

For every proof on a ballot, `casting/ballot.py` builds the context as a
canonical struct:

```text
prefix  = STRUCT( base_hash = H_E , ballot_id )
context = STRUCT( prefix , contest_id , option_id )
```

| ID      | Rule                                                                                                                                                                                                                                                                                     |
| ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `PR-07` | **The context binds four values: the election base hash `H_E`, the `ballot_id`, the `contest_id` and the `option_id`.** All four are inside the hashed transcript, so all four are covered by the challenge                                                                              |
| `PR-08` | Because the **option id** is bound, a proof valid for one selection **does not verify** for another selection of the same contest, even if both ciphertexts encrypt the same value under the same key                                                                                    |
| `PR-09` | Because the **ballot id** is bound, a proof does not transfer between two ballots, even between two ballots with identical selections                                                                                                                                                    |
| `PR-10` | Because the **base hash** is bound, a proof does not transfer between two elections, even under the same parameter set and key                                                                                                                                                           |
| `PR-11` | The contest sum proof uses the same prefix with the reserved option id `"#sum"`, so a sum proof is bound to its contest and cannot be presented as a selection proof or as another contest's sum proof                                                                                   |
| `PR-12` | Placeholder selections use option ids of the form `<contest_id>#placeholder-<index>` and are bound exactly like real options. A placeholder proof does not transfer to a real option and vice versa                                                                                      |
| `PR-13` | The context is an **input to the hash**, not a field of the proof. It is not carried in the envelope and cannot be tampered with independently: the verifier reconstructs it from the manifest, the base hash and the envelope, and a mismatch shows up as a failed challenge comparison |

## 5. Validation before evaluation

| ID      | Rule                                                                                                                                                                                                                                                                    |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `PR-14` | **Every verify function checks subgroup membership of every group element and the range of every scalar BEFORE it evaluates any verification equation.** The membership test is `is_in_subgroup(v)`: `0 < v < p` **and** `v^q ≡ 1 mod p`. The range test is `0 ≤ s < q` |
| `PR-15` | The order is normative, not stylistic. Evaluating an equation on an element of unknown order can succeed for a small-subgroup element and would turn a group-membership failure into a passed proof                                                                     |
| `PR-16` | A failed structural check returns `False`. It does not raise, does not warn and does not continue to the equations                                                                                                                                                      |

Exactly what each function checks, before any equation:

| Function                  | Subgroup-checked                                                            | Range-checked           |
| ------------------------- | --------------------------------------------------------------------------- | ----------------------- |
| `verify_selection`        | `public_key`, `a0`, `b0`, `a1`, `b1`, `ciphertext.alpha`, `ciphertext.beta` | `c0`, `c1`, `v0`, `v1`  |
| `verify_contest_sum`      | `public_key`, `a`, `b`, `accumulated.alpha`, `accumulated.beta`             | `challenge`, `response` |
| `verify_decryption_share` | `a`, `b`, `alpha`, `share`, `guardian_public`                               | `challenge`, `response` |

The equations then evaluated are:

```text
selection      c0 + c1 ≡ challenge (mod q)
               g^v0 = a0 · alpha^c0            K^v0 = b0 · beta^c0
               g^v1 = a1 · alpha^c1            K^v1 = b1 · (beta·g^-1)^c1
contest sum    challenge = recomputed
               g^response = a · alpha^challenge
               K^response = b · target_b^challenge
share          challenge = recomputed
               g^response = a · guardian_public^challenge
               alpha^response = b · share^challenge
```

**A gap that was closed:** `verify_selection` and `verify_contest_sum`
used **not** to re-check the subgroup membership of the `public_key` they
were handed, treating it as already validated by the caller — so a caller
passing an unvalidated key straight into the primitive got no key check
from the proof layer, and every equation below it would have been
meaningless. Both now check it first, before any other element, and return
`False` on failure; `verify_decryption_share` already checked
`guardian_public`, and `encrypt()` validates the public key on every call.
`test_verifier_branches::test_ballot_proof_verifiers_reject_a_public_key_outside_the_subgroup`
pins it.

## 6. Malleability evidence

| ID      | Evidence                                                                                                                                                                                                                                                                                                                                |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `PR-17` | **Tampering any single proof field fails.** `test_p03_modified_proof_fails` runs 40 cases; each case reads the proof's `__slots__`, selects one field by rotating index, replaces it with `(value + 1) mod p` and asserts `verify_selection` returns `False`. Over the run this covers every one of the eight `DisjunctiveProof` fields |
| `PR-18` | **A proof under a different context fails.** The same test additionally verifies the untampered proof against the context `b"other"` and asserts `False`. This is the direct evidence for `PR-07`…`PR-10`                                                                                                                               |
| `PR-19` | **A tampered proof inside a real ballot is rejected by the ballot pipeline, not just by the primitive.** `test_neg_invalid_proof` increments `v0` on the first selection of a real envelope and asserts `verify_ballot_proofs` raises `BallotStructureError` matching `"selection proof failed"`                                        |
| `PR-20` | **A proof copied to another selection of the same contest fails.** `test_neg_reused_nonce` moves the first selection's proof onto the second selection's ciphertext, asserts the ballot pipeline raises, and separately asserts `verify_selection` returns `False` for that pairing under a different context                           |
| `PR-21` | **A valid proof always verifies.** `test_p02_valid_selection_proof_always_verifies` runs 40 cases alternating `m = 0` and `m = 1` with fresh nonces and asserts every one verifies. Without this, `PR-17`…`PR-20` would be satisfiable by a verifier that always returns `False`                                                        |
| `PR-22` | The accumulated ciphertext is **recomputed** from the published selections by `verify_ballot_proofs` and compared componentwise before the sum proof is checked, so a prover cannot publish selections that do not accumulate to the ciphertext its sum proof is about                                                                  |

The negative corpus index `EXPECTED_REASON_CODES` in
`test_negative_corpus.py` pins each of these cases to a specific expected
reason code, and `test_every_declared_case_has_a_test` asserts the index
and the suite cannot drift apart.

## 7. Limitations, stated plainly

| ID      | Limitation                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `PR-23` | **Constant-time behaviour is NOT claimed, and no side-channel resistance is claimed.** The package `__init__.py` states this in its own docstring. Python `int` arithmetic and `pow(a, b, m)` provide no timing guarantee; the simulated and real branches of `prove_selection` execute different operation sequences; `is_in_subgroup` and the equation comparisons short-circuit. An attacker able to measure the prover's or verifier's timing is outside what this implementation defends against. A constant-time bignum path is a production blocker (`OD-P16D-05`)                                                                                                                                                                                                                                                                                                          |
| `PR-24` | **`PR-03` on its own is evidence about one share, never about a quorum.** `tally_accepted()` still computes one share from one secret and records `guardian_index = 1` for the non-threshold fixtures. The quorum is established by `PR-33` together with `combine_shares()`, which takes `k` from the ceremony transcript and refuses a smaller set — not by the share proof, which cannot know how many other shares exist                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| `PR-25` | **The decryption-share context binds the election context, the contest and the option.** It used to be the bare literal `b"tally"`, which contributed no per-contest separation at all. It is now the canonical struct built by `decryption_share_context(election_context_id, contest_id, option_id)` in `election_record/builder.py`, which the verifier derives independently rather than being handed a context by the party whose proof it is checking. `test_verifier_branches::test_decryption_share_proof_is_bound_to_its_contest_and_option` asserts a share does not verify under another option's context                                                                                                                                                                                                                                                               |
| `PR-26` | **The challenge is a 256-bit digest reduced modulo `q`.** `HMAC-SHA-256` produces 32 bytes and `h_q` reduces them mod `q`. Every registered profile has `\|q\| ≤ 256` — `EPD2-CRYPTO-1`: 256 bits; `EPD2-TESTONLY-NOTCONFORMANT-P4096-Q256`: 256 bits; `EPD2-TESTONLY-NOTCONFORMANT-P1024-Q160`: 160 bits — so the challenge spans the scalar range. A profile with a subgroup order larger than 256 bits would need a wider challenge derivation, and no such profile is registered                                                                                                                                                                                                                                                                                                                                                                                               |
| `PR-27` | **Verification returns a boolean, not a reason.** `verify_selection`, `verify_contest_sum` and `verify_decryption_share` return `False` for every distinct failure — bad subgroup element, out-of-range scalar, wrong challenge, failed equation. The reason code is attached by the caller (`verify_ballot_proofs`, the verifier's result codes). This keeps the primitive from leaking which check failed, and it means a debugging auditor must instrument, not read a message                                                                                                                                                                                                                                                                                                                                                                                                  |
| `PR-28` | **No nonce-reuse detector exists.** A fresh nonce is drawn per selection and per proof commitment, and context binding prevents a copied proof from transferring, but a caller that supplies the same nonce twice is not caught                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| `PR-29` | **Full interoperability is still not established, but the selection proof is now cross-checked by an independent implementation.** `tests/reference/crossimpl/independent_verifier.mjs` — a Node.js program written from the specification, importing only `node:` builtins and implementing its own square-and-multiply modular exponentiation — **recomputes the Fiat–Shamir challenge itself** from the canonical struct of `PR-04`, then checks the challenge split `c0 + c1 ≡ challenge (mod q)` and all four verification equations of `PR-01`. It is not handed the challenge, and it does not call any Python function. A companion test feeds it a wrong expected answer to prove it can fail. The internal stability vectors remain self-generated and `stability-only`, and no comparison against another _complete_ ElectionGuard implementation exists (`OD-P16D-02`) |
| `PR-30` | **The property tests are deterministic randomised loops, not `hypothesis` strategies.** `hypothesis` is a declared dev dependency but could not be installed in the environment this round was built in. `CASES = 40` per property, seeded, with **no shrinking and no adversarial search**. `test_property_limitation_is_recorded` asserts that `import hypothesis` still fails, so the limitation cannot be quietly dropped (`OD-P16D-03`)                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| `PR-31` | **No formal verification, no external cryptographic review and no BSI conformity is claimed.** `VO-08` is **OPEN**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |

## 8. What this document does not decide

```text
Ceremony custody, HSM and authenticated
  channels                                  → OD-P16D-11, PACK-16B, PACK-17
Constant-time / side-channel hardening      → OD-P16D-05, PACK-17
A second complete independent
  implementation                            → OD-P16D-02, PACK-17
Hypothesis-based property search            → OD-P16D-03, PACK-17
Per-contest binding of the share context    → done this round, see PR-25
Appropriateness of the group parameters     → VO-08, PACK-16B external review
Formal security proof of the composition    → PACK-16B external cryptographic review
BSI conformity / VO-08                      → OPEN, PACK-16B review + PACK-17
```

**REFERENCE IMPLEMENTATION. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY.
NOT LEGALLY ACTIVATED.**
