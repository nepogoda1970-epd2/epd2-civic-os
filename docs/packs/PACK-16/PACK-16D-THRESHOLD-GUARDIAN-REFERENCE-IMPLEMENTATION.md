# PACK-16D — Threshold Guardian Reference Implementation

**Round:** PACK-16D — Cryptographic Implementation Architecture, Reference
Components, Atomic Persistence, Test Vectors and Verification Harness.
**Reference implementation. Not production code. Not certified. Not a PASS.**
**Repository version:** unchanged at `0.16.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-102`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 1. Scope

This document describes
`services/voting-service/src/epd2_voting_service/reference/guardians/ceremony.py`
and `.../guardians/threshold.py`: the Feldman-VSS distributed key
generation, the `k`-of-`n` quorum policy, threshold decryption, and the
parts of the model this reference deliberately does not implement.

The audit finding `THRESHOLD GUARDIAN MODEL: FAIL` was raised because the
first PACK-16D candidate implemented one guardian and one decryption
share. PACK-16B fixes 3-of-5 by default and 4-of-7 for high assurance;
one guardian is not that model. The engine below is generic `k`-of-`n`
and both baseline configurations run on it.

| ID      | Symbol                                    | Role                                                                                    |
| ------- | ----------------------------------------- | --------------------------------------------------------------------------------------- |
| `TG-01` | `QuorumPolicy(quorum, guardian_count)`    | `k`-of-`n`, validated once, then immutable and carried in the transcript                |
| `TG-02` | `run_ceremony(...)`                       | The full DKG: polynomials, commitments, proofs of possession, share exchange, joint key |
| `TG-03` | `CeremonyTranscript`                      | The public, verifiable outcome. Carries no secret                                       |
| `TG-04` | `verify_ceremony(transcript, params)`     | Public verification of a transcript; returns `(ok, detail)`                             |
| `TG-05` | `compute_share(...)`, `ThresholdShare`    | One guardian's partial decryption of one ciphertext, with its Chaum–Pedersen proof      |
| `TG-06` | `combine_shares(...)`                     | Quorum check, share verification, Lagrange combination, bounded decode                  |
| `TG-07` | `compensated_decryption_share(...)`       | Exists only to raise `CompensatedDecryptionProhibited`                                  |
| `TG-08` | `DEFAULT_QUORUM`, `HIGH_ASSURANCE_QUORUM` | `(3, 5)` and `(4, 7)`, the two configurations PACK-16B names                            |

## 2. Guardian identity

| ID      | Rule                                                                                                                                                                                                                                                                                                                                                                                         |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `TG-09` | A `GuardianRecord` carries `guardian_id`, `guardian_sequence`, `election_context_id`, `coefficient_commitments` and `proof_of_possession`. That is the whole public record of a guardian, and none of those fields is a secret                                                                                                                                                               |
| `TG-10` | **`guardian_id` is election-scoped. It is not an account identity, not a member identity and not a voter identity.** It names a role in one ceremony and nothing else. `GuardianRecord` binds `election_context_id` alongside it, so the same string in another election is a different guardian                                                                                             |
| `TG-11` | `guardian_sequence` is the Shamir evaluation point `l`. `verify_ceremony` requires the roster's sequences to be exactly `1..n` with no gap and no duplicate, and requires the `guardian_id` set to be the same size as the sequence set — a duplicate id is refused                                                                                                                          |
| `TG-12` | Secret material lives in `GuardianSecret` (`coefficients`, `secret_key_share`), which is a separate type that is never published and never appears in a record. `test_no_guardian_secret_leaves_the_transcript` searches the transcript's canonical bytes for every share and every coefficient and asserts none is present, and asserts no slot name on the public record contains `secret` |

Nothing in this package resolves a guardian to a person. Who may hold a
guardian role, how they are appointed and how they are removed are
PACK-16B governance questions and are not modelled here.

## 3. Quorum policy, and why `2k <= n` is refused

`QuorumPolicy.validate()` rejects, in this order:

| ID      | Rejected                       | Reason as implemented                                                                                                       |
| ------- | ------------------------------ | --------------------------------------------------------------------------------------------------------------------------- |
| `TG-13` | `guardian_count < 1`           | a roster must exist                                                                                                         |
| `TG-14` | `quorum < 1`                   | a quorum of zero decrypts with nobody                                                                                       |
| `TG-15` | `quorum > guardian_count`      | a quorum that can never be met is a permanently undecryptable election, not a safe one                                      |
| `TG-16` | `2 * quorum <= guardian_count` | two **disjoint** sets of `k` guardians would each be able to decrypt on their own, which defeats the point of the threshold |

| ID      | Rule                                                                                                                                                                                                                                                                                        |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `TG-17` | **`TG-16` is a governance rule, not a cryptographic one, and the code says so in a comment rather than passing it off as mathematics.** Shamir interpolation works perfectly well at `2k <= n`; the objection is that a majority quorum is what makes "the guardians agreed" mean something |
| `TG-18` | `(3, 5)` and `(4, 7)` both satisfy it. `(2, 5)`, `(3, 7)` and `(1, 3)` do not, and `test_invalid_configurations_fail_closed` pins all of `(0,5)`, `(6,5)`, `(3,0)`, `(2,5)`, `(3,7)`, `(1,3)` as `GuardianConfigurationError`                                                               |
| `TG-19` | The policy is bound into the ceremony transcript and therefore into the election record's canonical bytes, so it is not a runtime argument a later caller can restate                                                                                                                       |

## 4. The distributed key generation

Feldman verifiable secret sharing, in the shape ElectionGuard uses. There
is no dealer and no party that ever holds the joint secret.

| ID      | Step                        | As implemented                                                                                                                                                                                                                                                                                                                                                                      |
| ------- | --------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `TG-20` | **Polynomial**              | Guardian `i` draws `k` coefficients `a_{i,0}..a_{i,k-1}`, each `1 + random_below(q - 1)`, from the injected `RandomSource`. `k` coefficients is a polynomial of degree `k-1`, which is what makes `k` shares sufficient and `k-1` useless                                                                                                                                           |
| `TG-21` | **Coefficient commitments** | `K_{i,j} = g^{a_{i,j}} mod p`, published for every `j`. These are the only image of the polynomial anyone else sees                                                                                                                                                                                                                                                                 |
| `TG-22` | **Proof of possession**     | A Schnorr proof of knowledge of the constant term `a_{i,0}`: commitment `g^nonce`, challenge `h_q` over the struct `(guardian_id, election_context_id, parameter_set_id, public_key, commitment)` under `DomainLabel.GUARDIAN_PROOF`, response `nonce + challenge * a_{i,0} mod q`. Without it a guardian could publish someone else's commitment as its own and contribute nothing |
| `TG-23` | **Share verification**      | Guardian `l` receives `P_i(l) mod q` and checks `g^{P_i(l)} == prod_j K_{i,j}^{l^j} mod p`. This is the property the commitments exist for: **a wrong share is detectable by its receiver at ceremony time**, not discovered at tally time when it is too late                                                                                                                      |
| `TG-24` | **Secret key share**        | `s_l = sum_i P_i(l) mod q`, accumulated as shares arrive. Because `s_l = P(l)` for the summed polynomial `P`, the `s_l` are Shamir shares of `s = P(0)` at threshold `k`                                                                                                                                                                                                            |
| `TG-25` | **Joint public key**        | `K = prod_i K_{i,0} mod p`. The joint secret it corresponds to is `s = sum_i P_i(0)`, and **no party ever holds it** — it is never computed anywhere in this package                                                                                                                                                                                                                |

| ID      | Rule                                                                                                                                                                                                                                                                                                                                                                 |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `TG-26` | `verify_possession` rejects before it verifies: an empty commitment list, a public key or proof commitment outside the subgroup, a challenge or response outside `[0, q)`, and a challenge that does not equal the recomputed one. Only then does it check `g^response == commitment * public_key^challenge`                                                         |
| `TG-27` | `verify_share` rejects a share outside `[0, q)` and any commitment outside the subgroup before doing the exponentiation, so a malformed input never reaches the arithmetic                                                                                                                                                                                           |
| `TG-28` | **The ceremony aborts; it does not degrade.** A share that fails `TG-23` raises `InvalidShareProofError` out of `run_ceremony`, and no transcript is produced. `run_ceremony(corrupt_share_from=...)` exists so that path is exercised rather than assumed: `test_a_corrupt_share_aborts_the_ceremony` runs a 3-of-5 with guardian 2 corrupted and asserts the abort |
| `TG-29` | Every guardian's proof of possession is verified inside `run_ceremony` as well, after the share exchange, so a roster is never assembled from unproved commitments                                                                                                                                                                                                   |
| `TG-30` | `guardian_public_share_key(transcript, l, params)` derives `g^{s_l}` from the published commitments alone — `prod_i prod_j K_{i,j}^{l^j}`. **This is how a verifier checks guardian `l`'s decryption share without ever seeing `s_l`,** and it is why a share proof needs no secret input on the verifying side                                                      |

## 5. The ceremony transcript and what the verifier checks

`CeremonyTranscript` binds `election_context_id`, `parameter_set_id`,
`policy`, the guardian roster, `joint_public_key` and `complete`, in that
declaration order, through `encode_struct`. `digest()` is domain-separated
under `DomainLabel.CEREMONY_TRANSCRIPT`.

`verify_ceremony` returns `(False, detail)` on the first of these to fail:

| ID      | Check                                                                                                                                |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| `TG-31` | the transcript's `parameter_set_id` is the parameter set the verifier holds                                                          |
| `TG-32` | the policy still validates (§3)                                                                                                      |
| `TG-33` | the roster size equals the declared `guardian_count`                                                                                 |
| `TG-34` | the sequences are exactly `1..n`, no gap, no duplicate                                                                               |
| `TG-35` | the guardian ids are distinct                                                                                                        |
| `TG-36` | every guardian published exactly `quorum` commitments                                                                                |
| `TG-37` | every guardian names the transcript's own election                                                                                   |
| `TG-38` | every guardian's proof of possession verifies                                                                                        |
| `TG-39` | **the joint public key derives from the published commitments** — `derive_joint_public_key` recomputes `prod_i K_{i,0}` and compares |
| `TG-40` | the transcript is marked `complete`                                                                                                  |

| ID      | Rule                                                                                                                                                                                                                                                                            |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `TG-41` | **The joint public key is a derived quantity and is never accepted standalone.** `derive_joint_public_key` raises `InvalidShareProofError` for a guardian with no commitments rather than skipping it, so an empty roster entry cannot silently contribute the identity element |
| `TG-42` | `quorum_digest(transcript, params)` binds `election_context_id`, `parameter_set_id`, the policy and the joint key under `DomainLabel.GUARDIAN_COMMITMENT`, so a record can be compared against the quorum the ceremony actually ran rather than the quorum it claims            |
| `TG-43` | `test_ceremony_rejects_a_tampered_transcript` pins three tampers: a replaced joint key, `complete=False`, and a dropped guardian. All three fail                                                                                                                                |

## 6. Threshold decryption

| ID      | Step                      | As implemented                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| ------- | ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `TG-44` | **Partial share**         | `M_l = alpha^{s_l} mod p`, computed by guardian `l` from the ciphertext's `alpha`                                                                                                                                                                                                                                                                                                                                                                                         |
| `TG-45` | **Proof**                 | A Chaum–Pedersen proof that `M_l` uses the same `s_l` whose public image `g^{s_l}` the verifier derives from the commitments. The Fiat–Shamir context is `share_context(...)`: the label `threshold-decryption-share`, the election, the parameter set, the contest, the option and the guardian sequence. A proof made for one of those does not verify for another, so cross-election, cross-contest and cross-option replay **fail** rather than being merely unlikely |
| `TG-46` | **Lagrange coefficients** | `w_l = prod_{j != l} j / (j - l) mod q`, evaluated at zero. `q` is prime, so the inverse is `x^(q-2) mod q`                                                                                                                                                                                                                                                                                                                                                               |
| `TG-47` | **Combination**           | `M = prod_l M_l^{w_l} mod p`, then `g^m = beta * M^(p-2) mod p`                                                                                                                                                                                                                                                                                                                                                                                                           |
| `TG-48` | **Bounded decode**        | `decode_exponent(g^m, params, maximum=...)` searches `0..maximum` only, refuses a `maximum` above `MAX_EXPONENT_SEARCH`, and raises `DecryptionDomainError` if `g^m` does not decode inside the bound. There is no unbounded discrete-log path                                                                                                                                                                                                                            |

| ID      | Rule                                                                                                                                                                                                                                                                                                                                      |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `TG-49` | `verify_share` (threshold) is public-values-only: it takes the share, the ciphertext, the transcript and the parameters. It never sees `s_l`                                                                                                                                                                                              |
| `TG-50` | The share subgroup check runs before the proof check, so a value that has left the subgroup is caught by the cheaper test. `test_invalid_guardian_share_proof_rejected` pins that ordering by tampering in two ways: doubling the share (leaves the subgroup, caught first) and multiplying by `g` (stays inside, reaches the proof)      |
| `TG-51` | `lagrange_coefficient` raises `UnknownGuardianError` for a sequence outside the selection and `DuplicateGuardianShareError` if the denominator collapses to zero. `test_lagrange_coefficients_reconstruct_at_zero` checks the interpolation identity directly — the basis polynomials at zero sum to 1 — rather than only through a tally |

## 7. The rejection matrix

`combine_shares` is fail-closed on every defect below. **None of them is a
warning, and none is recoverable by dropping the offending share and
continuing:** a bad share means the set presented is not the set the
quorum authorised.

| ID      | Condition                                                             | Raised                                                                                                           | Reason code                    |
| ------- | --------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- | ------------------------------ |
| `TG-52` | no shares at all                                                      | `InsufficientQuorumError`                                                                                        | `GUARDIAN_INSUFFICIENT_QUORUM` |
| `TG-53` | fewer shares than the transcript's `quorum`                           | `InsufficientQuorumError`                                                                                        | `GUARDIAN_INSUFFICIENT_QUORUM` |
| `TG-54` | the same `guardian_sequence` twice                                    | `DuplicateGuardianShareError`                                                                                    | `GUARDIAN_DUPLICATE_SHARE`     |
| `TG-55` | shares for different contests or options in one call                  | `ThresholdMismatchError`                                                                                         | `GUARDIAN_THRESHOLD_MISMATCH`  |
| `TG-56` | a share whose proof does not verify                                   | `InvalidShareProofError`                                                                                         | `GUARDIAN_INVALID_SHARE_PROOF` |
| `TG-57` | a share from a sequence outside the roster                            | rejected by `verify_share` → `InvalidShareProofError`; `guardian_public_share_key` raises `UnknownGuardianError` | `GUARDIAN_UNKNOWN_GUARDIAN`    |
| `TG-58` | a share naming another election                                       | rejected by `verify_share` → `InvalidShareProofError`                                                            | `GUARDIAN_INVALID_SHARE_PROOF` |
| `TG-59` | a share whose `guardian_id` does not match the sequence in the roster | rejected by `verify_share`                                                                                       | `GUARDIAN_INVALID_SHARE_PROOF` |
| `TG-60` | a share presented against a different ciphertext                      | the Chaum–Pedersen proof does not verify                                                                         | `GUARDIAN_INVALID_SHARE_PROOF` |

| ID      | Rule                                                                                                                                                                                                                                                                                                                                     |
| ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `TG-61` | The five machine-readable codes are `GuardianErrorCode`: `guardian.threshold_mismatch`, `guardian.insufficient_quorum`, `guardian.duplicate_share`, `guardian.invalid_share_proof`, `guardian.unknown_guardian`. `test_error_codes_are_the_declared_ones` asserts the enum is exactly that set, so a sixth code cannot be added silently |
| `TG-62` | The order of checks inside `combine_shares` is: duplicates and contest/option mixing first, then the quorum count, then per-share proof verification. Cheap structural refusals come before expensive arithmetic, and a duplicate is refused before it can reach the Lagrange denominator                                                |

## 8. Threshold reduction is structurally impossible

| ID      | Rule                                                                                                                                                                                                                                                                                                                                                                                                          |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `TG-63` | **The quorum comes from the ceremony transcript, never from the caller.** `combine_shares` reads `transcript.policy`; it has no parameter by which a caller can state a threshold                                                                                                                                                                                                                             |
| `TG-64` | Presenting a transcript with a rewritten quorum does not help. The policy is inside the transcript's canonical bytes and the joint key is re-derived from the roster, so `verify_ceremony` on a transcript whose quorum was changed fails before any share is combined. `test_threshold_reduction_rejected` constructs exactly that — a 3-of-5 transcript restated as 2-of-5 — and asserts it does not verify |
| `TG-65` | Verified refusals: 2-of-5 against a 3-of-5 ceremony, and 3-of-7 against a 4-of-7 ceremony. Both raise `InsufficientQuorumError`, the first with the message `the ceremony fixed a quorum of 3 of 5 and it may not be reduced`                                                                                                                                                                                 |
| `TG-66` | More than the quorum is accepted: 4 and 5 shares against a 3-of-5 ceremony both decrypt to the same value. A quorum is a floor, not an exact count                                                                                                                                                                                                                                                            |

## 9. Compensated decryption is absent, and the absence is discoverable

ElectionGuard permits the available guardians to reconstruct a missing
guardian's decryption share. This implementation does not.

| ID      | Rule                                                                                                                                                                                                                                                                                                                                |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `TG-67` | **A compensation path is a path by which `k` guardians recover another guardian's secret material.** The PACK-16B baseline prohibits it, so a missing guardian is covered by having enough others, never by reconstructing the missing one                                                                                          |
| `TG-68` | `compensated_decryption_share()` exists in `ceremony.py` and does exactly one thing: raise `CompensatedDecryptionProhibited` (reason code `GUARDIAN_COMPENSATION_PROHIBITED`) with the reason in its message. **A reader looking for the feature finds the prohibition, rather than finding nothing and assuming it was forgotten** |
| `TG-69` | `test_compensated_decryption_unavailable` calls it and asserts the raise, then reads `threshold.py` and asserts that none of `compensate`, `reconstruct_secret`, `escrow` or `break_glass` appears in it. A substring assertion is deliberately blunt: the module should have no vocabulary for reconstructing a guardian           |
| `TG-70` | The consequence is stated rather than hidden: an election that loses more than `n - k` guardians **cannot be decrypted at all**. That is the intended failure. Recovery, backup custody and the governance around losing a quorum are PACK-16B and PACK-17 obligations, not a code path here                                        |

## 10. Election record and verifier integration

`ElectionRecord` carries `ceremony: CeremonyTranscript | None` and
`threshold_shares: tuple[ThresholdShare, ...]`, both inside
`canonical_bytes()` as declared fields, so neither can be swapped without
changing the record's digest.

| ID      | Rule                                                                                                                                                                                                                                                          |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `TG-71` | `verify_record` runs the ceremony check **immediately after the joint-key subgroup check and before anything that uses the key.** A record whose ceremony does not verify never reaches the ballot proofs, the tally or the board                             |
| `TG-72` | Three refusals return `INVALID_CEREMONY_TRANSCRIPT` (exit code 23): `verify_ceremony` failed; the transcript names a different election than the manifest; or the record's joint public key is not the one `derive_joint_public_key` produces from the roster |
| `TG-73` | `GUARDIAN_QUORUM_MISMATCH` (exit code 24) is returned for a duplicate guardian share for one contest/option, or for fewer shares than the policy's quorum. Threshold shares naming a contest/option with no tally are `INCOMPLETE_RECORD`                     |
| `TG-74` | A share whose proof fails is `INVALID_DECRYPTION_SHARE` (exit code 50)                                                                                                                                                                                        |
| `TG-75` | On success the run adds `ceremony.transcript`, `ceremony.joint_key_derivation`, `ceremony.guardian_proofs` and — when threshold shares are present — `ceremony.threshold_shares` to `checks_run`. A check that did not run is not listed                      |
| `TG-76` | `NOT_CHECKED` still states, on every result including `VERIFIED`, that the verifier did not check _that guardian key shares were handled correctly after the ceremony_. Verifying a transcript says nothing about custody afterwards                          |

## 11. Verified configurations and measured behaviour

Measured, on the fast test profile unless stated otherwise. 28 tests in
`services/voting-service/tests/reference/test_guardians.py`, all passing.

| ID      | Configuration                                                        | Result                                                     |
| ------- | -------------------------------------------------------------------- | ---------------------------------------------------------- |
| `TG-77` | 3-of-5, quorum selections `(1,2,3)`, `(1,3,5)`, `(3,4,5)`, `(2,4,5)` | all decrypt to the same plaintext                          |
| `TG-78` | 3-of-5 with 4 and with 5 shares                                      | decrypt                                                    |
| `TG-79` | 2-of-5 against a 3-of-5 ceremony                                     | rejected, `InsufficientQuorumError`                        |
| `TG-80` | 4-of-7, quorum selections `(1,2,3,4)`, `(2,4,6,7)`, `(1,3,5,7)`      | all decrypt                                                |
| `TG-81` | 3-of-7 against a 4-of-7 ceremony                                     | rejected                                                   |
| `TG-82` | 3-of-5 ceremony on **`EPD2-CRYPTO-1`**                               | runs and verifies (`test_epd2_crypto_1_guardian_ceremony`) |

Timings on `EPD2-CRYPTO-1`, measured. **These are benchmark figures, not a
capacity statement**, and no validation was disabled to obtain them:

```text
3-of-5 ceremony (DKG)                       1.847 s
ceremony verification                       0.254 s
3 threshold shares + proofs                 0.189 s
3-of-5 tally verification + combination     0.641 s
```

The threshold path is also exercised end to end: E2E-11 (3-of-5 threshold
tally), E2E-12 (insufficient quorum), E2E-14 (record verification with
threshold artefacts), and the negative-corpus case
`insufficient_guardian_quorum`, which asserts the reason code
`GUARDIAN_INSUFFICIENT_QUORUM`.

## 12. What this reference ceremony does not model

This section is the point of the document. The mathematics above is a real
DKG; **the ceremony around it is not a real ceremony.**

| ID      | Not modelled                                                                                                                                                                                                                           | Consequence                                                                                                                                         |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| `TG-83` | **In-process share exchange.** `run_ceremony` computes every share inside one Python process and hands it to the receiver as an integer                                                                                                | There is no network, no message format and no ordering to attack, so nothing here is evidence that a distributed ceremony would behave the same way |
| `TG-84` | **No authenticated channel.** Nothing authenticates sender to receiver. The Feldman check proves a share matches _published commitments_; it does not prove who sent it                                                                | A production ceremony needs an authenticated, confidential channel per guardian pair. None is specified here                                        |
| `TG-85` | **No HSM and no key custody.** `run_ceremony` _returns_ the guardian secrets, because a reference ceremony has to hand them to the test that will decrypt with them. In production a guardian secret never leaves its holder's custody | This is the single largest gap between this module and a usable ceremony, and it is visible in the function signature                               |
| `TG-86` | **No air gap.** Ceremony and election run in the same process on the same machine                                                                                                                                                      | Compromise of that machine is compromise of every guardian at once, which is precisely what a threshold scheme is supposed to prevent               |
| `TG-87` | **No human ceremony script.** No witnesses, no attestations, no roles, no recorded procedure, no signed minutes                                                                                                                        | PACK-16B's ceremony requirements are unimplemented here                                                                                             |
| `TG-88` | **No complaint or disqualification workflow.** A corrupt share aborts the run; it does not raise a complaint, attribute blame durably or start a replacement procedure                                                                 | PACK-16B's complaint and disqualification model is a specification, not code                                                                        |

| ID      | Rule                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `TG-89` | All of `TG-83` to `TG-88` are recorded as **`OD-P16D-11`**, new this round: _the reference ceremony exchanges shares in-process with no authenticated channel, no HSM, no air gap and no key custody._ It is open, and it is a production blocker for the ceremony surface                                                                                                                                                                                              |
| `TG-90` | **Guardian secret operations are not constant-time** (`OD-P16D-05`, production blocker). Polynomial evaluation, share computation and the exponentiations that use `s_l` are Python big-integer arithmetic; timing on those operations touches secret material. Public verification — proofs, the joint-key derivation, `verify_ceremony` — touches no secret, so its timing carries none. The four-way split is in `PACK-16D-SECURITY-AND-SIDE-CHANNEL-LIMITATIONS.md` |
| `TG-91` | The secret nonces used for the polynomial coefficients and the Schnorr and Chaum–Pedersen proofs come from the injected `RandomSource`. Its _source_ is the OS CSPRNG; its _use_ is not constant-time                                                                                                                                                                                                                                                                   |
| `TG-92` | No external cryptographic review of this module has taken place. `VO-08` is **OPEN**, no BSI conformity is claimed, and agreement with a complete independent ElectionGuard implementation is **not** established (`OD-P16D-02`)                                                                                                                                                                                                                                        |

## 13. What this document does not decide

```text
Production key ceremony, custody, HSM, air gap        → OD-P16D-11, PACK-16B, GOVERNANCE
Authenticated guardian-to-guardian channel            → OD-P16D-11, PACK-17
Guardian appointment, removal, replacement            → PACK-16B, GOVERNANCE
Complaint and disqualification execution              → PACK-16B, PACK-17
Backup, recovery and quorum-loss handling             → PACK-16B, GOVERNANCE
Constant-time guardian operations                     → OD-P16D-05, PACK-17, FIR
Parameter appropriateness                             → VO-08, PACK-16B external review
Independent implementation of this ceremony           → OD-P16D-02, PACK-17, external party
```

**REFERENCE IMPLEMENTATION. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY.
NOT LEGALLY ACTIVATED.**
