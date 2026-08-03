# PACK-16D — Negative Test Corpus

**Round:** PACK-16D — Cryptographic Implementation Architecture, Reference
Components, Atomic Persistence, Test Vectors and Verification Harness.
**Reference implementation. Not production code. Not certified. Not a PASS.**
**Repository version:** unchanged at `0.16.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-102`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 1. Scope and the rule the whole corpus rests on

`services/voting-service/tests/reference/test_negative_corpus.py` holds
**thirty-nine** named attack cases from §40, plus two index-consistency
guards: **41 tests** in total. Three cases were added by the correction
round — `ambiguous_sequence_encoding`, `unauthorized_board_signer` and
`insufficient_guardian_quorum` — each attacking a surface that did not
exist, or did not fail closed, in the first candidate.

| ID | Rule |
| -- | ---- |
| `NC-01` | **Every case must fail closed.** The attacked call raises, or returns a failure result code. There is no third outcome |
| `NC-02` | **A case that merely warns is an implementation defect, not a lenient test.** So is a case that succeeds with a degraded result — a clamped plaintext, a padded encoding, a partially validated ballot. If a case here ever passes by warning, the fix belongs in the implementation |
| `NC-03` | **Each case declares a specific expected reason code, not merely that something was raised.** The declaration lives in `EXPECTED_REASON_CODES`; §2 records exactly how each case checks it, because "an exception was raised" is not by itself evidence that the *right* thing was refused for the *right* reason |
| `NC-04` | `EXPECTED_REASON_CODES` in the test module is the machine-readable index this document is generated from. **A mismatch between the dict and the table in §3 is a defect in this document**, and is corrected by rereading the dict, never by editing the table to taste |
| `NC-05` | `test_every_declared_case_has_a_test` asserts that every key `k` in `EXPECTED_REASON_CODES` has a corresponding function `test_neg_<k>` in the module. The index and the suite cannot drift apart silently. `test_every_case_asserts_its_declared_reason_code` is the second guard: it reads each case's source and fails if a case stops referencing `EXPECTED_REASON_CODES`, so no case can quietly fall back to asserting only an exception type |

Two facts about the codes themselves, both visible in the dict:

| ID | Rule |
| -- | ---- |
| `NC-06` | **Codes are shared across cases where the refusal is genuinely the same.** The 39 cases declare **25** distinct codes: five share `PARAMETER_SET_INVALID`, five share `BALLOT_PREPARATION_STYLE_SHAPE_MISMATCH`, **three** share `INVALID_CANONICAL_ENCODING` since `ambiguous_sequence_encoding` joined `non_canonical_integer` and `duplicate_field`, and `INVALID_SCHEMA`, `CONTINUATION_CAST_ENTITLEMENT_EXHAUSTED`, `BULLETIN_BOARD_BATCH_RECONCILIATION_FAILED` and `BOARD_INCONSISTENCY` are shared by two each. The two codes new to the index — `BOARD_SIGNER_UNKNOWN` and `GUARDIAN_INSUFFICIENT_QUORUM` — are declared by one case each. A shared code is deliberate: the attacker learns the class of refusal, not which check caught them |
| `NC-07` | **The declared code is the code the implementation actually produces, and the vocabulary is mixed.** Some entries are the `reason_code` carried on the exception class the case raises — `CONTINUATION_CAST_ENTITLEMENT_EXHAUSTED` on `CastEntitlementExhaustedError`, `TALLY_PRE_CLOSURE_PROHIBITED` on `IntermediateTallyProhibitedError`. Some are `VerificationResultCode` members the verifier returns — `BATCH_ROOT_MISMATCH`, `INCOMPLETE_RECORD`, `TALLY_MISMATCH`, `BOARD_INCONSISTENCY`, `BATCH_CONSISTENCY_FAILED`. Four entries used to name a *class* of refusal that no exception carried — `BALLOT_STRUCTURE_INVALID` and, on the encoder, `VALIDATION_SCHEMA_INVALID` — and were corrected to the codes actually raised (`BALLOT_PREPARATION_STYLE_SHAPE_MISMATCH`, `BALLOT_PREPARATION_OVERVOTE`, `INVALID_CANONICAL_ENCODING`, `BATCH_CONSISTENCY_FAILED`) |

## 2. How to read the table

- **Attacked** — the input or state the case corrupts.
- **Expected reason code** — reproduced verbatim from
  `EXPECTED_REASON_CODES`.
- **Mech.** — how the test checks it, one of two:
  `attr` (asserts the `reason_code` attribute on the raised exception
  against the index), `result` (asserts the `VerificationResultCode` on a
  returned result against the index). Most cases assert the exception type
  and a message match as well.
- **Discharged by** — the test function in `test_negative_corpus.py`.

**Thirty-two** cases are `attr` and **seven** are `result`. **Every case
checks its declared code**; a case that asserted only an exception type
would leave the declared code as a comment rather than a check, which is
what `test_every_case_asserts_its_declared_reason_code` now prevents.

## 3. The 39 cases

### 3.1 Encoding, parameters and group elements

| ID | Case | Attacked | Expected reason code | Mech. | Discharged by |
| -- | ---- | -------- | -------------------- | ----- | ------------- |
| `NC-08` | `wrong_p_q_g` | A parameter set built with `g = 3`, which is not in the subgroup of the declared `p`, `q` | `PARAMETER_SET_INVALID` | attr | `test_neg_wrong_p_q_g` |
| `NC-09` | `invalid_subgroup_element` | `g + 1` presented as a group element | `PARAMETER_SET_INVALID` | attr | `test_neg_invalid_subgroup_element` |
| `NC-10` | `zero_element` | `0` presented as a group element | `PARAMETER_SET_INVALID` | attr | `test_neg_zero_element` |
| `NC-11` | `element_ge_p` | `p` and `p + 1` presented as group elements — the two boundary values above the field | `PARAMETER_SET_INVALID` | attr | `test_neg_element_ge_p` |
| `NC-12` | `invalid_scalar` | A plaintext of 2 encrypted with `max_message=1`: a value outside the declared domain | `BALLOT_PREPARATION_CONTEST_INVALID` | attr | `test_neg_invalid_scalar` |
| `NC-13` | `non_canonical_integer` | A short-form integer (`decode_uint(b"\x01", 4)`), an over-wide value (`2**32` in 4 bytes) and a negative value | `INVALID_CANONICAL_ENCODING` | attr | `test_neg_non_canonical_integer` |
| `NC-14` | `duplicate_field` | A struct with the field name `a` twice | `INVALID_CANONICAL_ENCODING` | attr | `test_neg_duplicate_field` |
| `NC-15` | `unknown_critical_field` | A `receipt` document carrying an undeclared field `turnout_so_far` | `INVALID_SCHEMA` | attr | `test_neg_unknown_critical_field` |
| `NC-16` | `missing_critical_field` | A `receipt` document carrying only `ballot_id` | `INVALID_SCHEMA` | attr | `test_neg_missing_critical_field` |
| `NC-51` | `ambiguous_sequence_encoding` | Two different sequences and two different structs that a raw-concatenating encoder would flatten to identical bytes: `SEQ([b"ab", b"c"])` against `SEQ([b"a", b"bc"])`, and `STRUCT(f=b"ab", g=b"c")` against `STRUCT(f=b"a", g=b"bc")` | `INVALID_CANONICAL_ENCODING` | attr | `test_neg_ambiguous_sequence_encoding` |

`NC-12` is the case that proves the encryption path **rejects rather than
clamps**. `NC-15` is the case that proves an unknown field is rejected,
never ignored — and the field it smuggles in is a turnout count, which is
the leak the schema registry exists to prevent.

`NC-51` is the corpus entry for a **real defect this round found and
fixed**. `encode_seq` used to write a four-byte count and then concatenate
the items raw, and `encode_struct` appended field values raw, so two
different sequences shared an encoding and therefore a digest. Both now
length-prefix every element. The case asserts the two pairs no longer
collide, asserts the exact corrected shape of `encode_seq`, and then
raises through the duplicate-field path to check the declared reason code,
because collision-freedom is an equality assertion and has no exception of
its own to carry a code. The defect was surfaced by the independent
cross-implementation verifier, which was written from the documented
grammar rather than from the code.

### 3.2 Ballot structure and proofs

| ID | Case | Attacked | Expected reason code | Mech. | Discharged by |
| -- | ---- | -------- | -------------------- | ----- | ------------- |
| `NC-17` | `wrong_manifest_digest` | An envelope whose `manifest_digest` is replaced with 32 zero bytes | `BALLOT_PREPARATION_STYLE_SHAPE_MISMATCH` | attr | `test_neg_wrong_manifest_digest` |
| `NC-18` | `wrong_election_context` | An envelope re-labelled with another `election_context_id` | `BALLOT_PREPARATION_STYLE_SHAPE_MISMATCH` | attr | `test_neg_wrong_election_context` |
| `NC-19` | `wrong_ballot_style` | An envelope claiming a ballot style the manifest does not define | `BALLOT_PREPARATION_STYLE_SHAPE_MISMATCH` | attr | `test_neg_wrong_ballot_style` |
| `NC-20` | `invalid_ciphertext` | `Ciphertext(alpha=0, …)` and `Ciphertext(…, beta=p)`: components outside the group | `PARAMETER_SET_INVALID` | attr | `test_neg_invalid_ciphertext` |
| `NC-21` | `invalid_proof` | One field (`v0`) of one selection proof incremented modulo `p` | `BALLOT_PREPARATION_STYLE_SHAPE_MISMATCH` | attr | `test_neg_invalid_proof` |
| `NC-22` | `reused_nonce` | One selection's proof re-presented against **another** selection's ciphertext, inside the same ballot | `BALLOT_PREPARATION_STYLE_SHAPE_MISMATCH` | attr | `test_neg_reused_nonce` |
| `NC-23` | `overvote` | Two options selected in a contest whose selection limit is one | `BALLOT_PREPARATION_OVERVOTE` | attr | `test_neg_overvote` |

`NC-22` is the transferability case: it asserts the ballot-level rejection
**and** then calls `verify_selection` directly to show the proof does not
verify under the other option's context. Fiat–Shamir binding is what makes
that true, and the case checks the mechanism rather than only the symptom.
`NC-23` refuses the overvote at ballot preparation, before any transaction
opens, so an overvote never reaches a capability.

### 3.3 Capability, entitlement and transaction

| ID | Case | Attacked | Expected reason code | Mech. | Discharged by |
| -- | ---- | -------- | -------------------- | ----- | ------------- |
| `NC-24` | `challenged_ballot_submitted_as_cast` | The same ballot published as a public challenge and then submitted as a cast under a new idempotency key | `ACCEPTANCE_DUPLICATE_BALLOT_ID` | attr | `test_neg_challenged_ballot_submitted_as_cast` |
| `NC-25` | `cast_nonce_revealed` | An opening from a *different* ballot presented as the opening for this one | `CHALLENGE_REENCRYPTION_MISMATCH` | attr | `test_neg_cast_nonce_revealed` |
| `NC-26` | `duplicate_public_challenge` | A second public challenge on a capability whose challenge entitlement is spent | `CHALLENGE_PUBLIC_ENTITLEMENT_EXHAUSTED` | attr | `test_neg_duplicate_public_challenge` |
| `NC-27` | `duplicate_cast` | A second cast on a capability whose cast entitlement is spent | `CONTINUATION_CAST_ENTITLEMENT_EXHAUSTED` | attr | `test_neg_duplicate_cast` |
| `NC-28` | `idempotency_conflict` | A *different* canonical request submitted under an already-used idempotency key, by a different capability | `SUBMISSION_IDEMPOTENCY_CONFLICT` | attr | `test_neg_idempotency_conflict` |
| `NC-29` | `capability_replay` | A consumed capability re-presented with a fresh idempotency key and a fresh ballot | `CONTINUATION_CAST_ENTITLEMENT_EXHAUSTED` | attr | `test_neg_capability_replay` |
| `NC-30` | `unknown_capability` | A capability string that was never issued | `CONTINUATION_INVALID` | attr | `test_neg_unknown_capability` |
| `NC-31` | `leaf_reservation_race` | A second cast when the only cast-reserved slot is taken (fixture C) | `SUBMISSION_CAST_CAPACITY_UNAVAILABLE` | attr | `test_neg_leaf_reservation_race` |
| `NC-32` | `wrong_slot_type` | A second public challenge attempting to take the free **cast-reserved** slot once the challenge-reserved slot is occupied | `CHALLENGE_PUBLIC_RESERVATION_UNAVAILABLE` | attr | `test_neg_wrong_slot_type` |
| `NC-33` | `adaptive_overflow_attempt` | A capacity plan whose `cast + challenge + shared` is 6 against a `primary_capacity` of 8 — two unclassified slots | `ELECTION_CAPACITY_PLAN_INVALID` | attr | `test_neg_adaptive_overflow_attempt` |

Three of these carry an extra assertion beyond the reason code, and the
extra assertion is the substantive one:

| ID | Rule |
| -- | ---- |
| `NC-34` | `NC-24` asserts `envelope.ballot_id not in store.accepted_ballots` — the refusal left nothing behind. `NC-28` and `NC-29` distinguish a conflict from a replay: a *different* request under a used key raises, it is never silently answered with the earlier result |
| `NC-35` | `NC-32` is `TC-75`. It asserts `store.slot_owner == {(0, 1): "res-chal-k1"}` before the attack and `(0, 0) not in store.slot_owner` after it: a public challenge did not take the cast-reserved slot even though that slot was free and the alternative was failing the request |
| `NC-36` | `NC-33` additionally asserts the substring `adaptive-overflow` is in the exception message. The plan is refused because an unclassified slot is adaptive overflow reintroduced by arithmetic, and the message says so where an implementer will read it |

### 3.4 Batches, board and election record

| ID | Case | Attacked | Expected reason code | Mech. | Discharged by |
| -- | ---- | -------- | -------------------- | ----- | ------------- |
| `NC-37` | `batch_root_mismatch` | A sealed batch republished with a forged `commitment_root` of `0xaa` × 32 | `BATCH_ROOT_MISMATCH` | result | `test_neg_batch_root_mismatch` |
| `NC-38` | `missing_opening` | A batch commitment published with no opening at all | `INCOMPLETE_RECORD` | result | `test_neg_missing_opening` |
| `NC-39` | `duplicate_opening` | One real leaf opening appended twice, mapping one artefact to two leaves | `BULLETIN_BOARD_BATCH_RECONCILIATION_FAILED` | attr | `test_neg_duplicate_opening` |
| `NC-40` | `cover_leaf_in_tally` | A cover leaf's opening rewritten as `ACCEPTED_CAST` with the artefact reference `ghost-ballot` | `BULLETIN_BOARD_BATCH_RECONCILIATION_FAILED` | attr | `test_neg_cover_leaf_in_tally` |
| `NC-41` | `spoiled_ballot_in_tally` | A record in which the same envelope appears in both `accepted_ballots` and `spoiled_ballots` | `TALLY_MISMATCH` | result | `test_neg_spoiled_ballot_in_tally` |
| `NC-42` | `conflicting_checkpoint` | Two checkpoints at the same tree size with different roots — equivocation within one exported view | `BOARD_INCONSISTENCY` | result | `test_neg_conflicting_checkpoint` |
| `NC-43` | `rollback` | A later checkpoint whose tree size is smaller than its predecessor's | `BOARD_INCONSISTENCY` | result | `test_neg_rollback` |
| `NC-44` | `invalid_consistency_proof` | Every single-node corruption of a consistency proof from size 2 to size 5, and the truncated proof | `BATCH_CONSISTENCY_FAILED` | result | `test_neg_invalid_consistency_proof` |
| `NC-45` | `pre_closure_decryption_artifact` | A `TALLY_ARTIFACT` entry appended to the board before closure | `PUBLICATION_UNSCHEDULED_BATCH_PROHIBITED` | attr | `test_neg_pre_closure_decryption_artifact` |
| `NC-46` | `intermediate_tally_artifact` | `tally_accepted(..., board_closed=False)` on a live election | `TALLY_PRE_CLOSURE_PROHIBITED` | attr | `test_neg_intermediate_tally_artifact` |
| `NC-52` | `unauthorized_board_signer` | A published checkpoint rewritten to name `signing_key_id = "not-a-declared-key"`, then verified against the board's own signer registry and re-presented to `verify_board` inside a complete export | `BOARD_SIGNER_UNKNOWN` | result | `test_neg_unauthorized_board_signer` |

| ID | Rule |
| -- | ---- |
| `NC-47` | `NC-37` and `NC-41` assert the numeric exit code as well as the result code — 41 and 51 respectively. Exit codes are a caller-visible contract and are pinned here as well as in the vector catalogue |
| `NC-48` | `NC-44` is exhaustive rather than illustrative: it first asserts the honest proof verifies, then corrupts **each** node of the proof in turn and asserts every corruption is detected, then asserts a truncated proof is detected. A consistency check that passed on some corruptions would not be caught by a single-mutation test. It runs each corruption through `verify_board` and asserts `BATCH_CONSISTENCY_FAILED` with exit code 44 — the code the verifier actually returns for this condition, and not `BOARD_INCONSISTENCY`, which is what `NC-42` and `NC-43` assert for equivocation and rollback |
| `NC-49` | `NC-45` asserts `board.entries == []` after the refusal. The rejected entry was not appended and then removed; it was never appended |
| `NC-50` | `NC-46` attacks the hard gate directly. `open_tally(board_closed: bool)` reads no flag, no environment variable and no configuration, so there is no second way to reach a tally before closure that this case would miss |
| `NC-54` | `NC-52` asserts the refusal **twice, at two layers**: `verify_checkpoint` returns `CheckpointSignatureOutcome.SIGNER_UNKNOWN` directly, and `verify_board` on a full export returns `BOARD_SIGNER_UNKNOWN`. The signature itself is untouched and genuine — only the key identifier was rewritten — so what the case proves is that the trust anchor is the declared registry and not the artefact. There is no path that reads a key out of the checkpoint being verified, and `CheckpointPayload` has no `public_key` field for one to arrive in |

### 3.5 Guardian ceremony and threshold decryption

| ID | Case | Attacked | Expected reason code | Mech. | Discharged by |
| -- | ---- | -------- | -------------------- | ----- | ------------- |
| `NC-53` | `insufficient_guardian_quorum` | Two decryption shares presented to `combine_shares` against a ceremony that fixed a 3-of-5 quorum | `GUARDIAN_INSUFFICIENT_QUORUM` | attr | `test_neg_insufficient_guardian_quorum` |

| ID | Rule |
| -- | ---- |
| `NC-55` | **`NC-53` is the case that proves the quorum cannot be reduced at tally time.** `combine_shares` reads the policy from the ceremony transcript, never from its caller, so there is no argument a caller can pass that makes `k-1` acceptable. The two shares presented are individually valid and individually proof-carrying; the refusal is about the *set*, and the message says `the ceremony fixed a quorum of 3 of 5 and it may not be reduced` |

## 4. What the corpus does not cover

Stated plainly, in the body:

- **These are the §40 cases, not an exhaustive adversary model.**
  Thirty-nine named attacks were enumerated and each is discharged; no
  claim is made that the enumeration is complete. Three of the thirty-nine
  were added only after an audit and an independent oracle pointed at
  surfaces the first enumeration had missed, which is itself evidence that
  the enumeration is not complete.
- **The searching is deterministic.** The property tests that would explore
  around these cases are deterministic randomised loops over a seeded
  source, not `hypothesis` strategies — no shrinking and no adversarial
  search (`OD-P16D-03`). `hypothesis` could not be installed in this
  environment.
- **`NC-31` and `NC-32` are the sequential form of the capacity races.**
  Their concurrent form is in `test_concurrency.py`, whose evidence covers
  the reference in-memory store only, not a production datastore's
  isolation level (`OD-P16D-04`).
- **Cross-mirror split view is not attacked, because it is not
  implemented.** `NC-42` detects equivocation *within a single exported
  view*. Gossip across mirrors is not implemented (`OD-P16D-06`) and no
  case here should be read as covering it.
- **No timing attack is in the corpus.** Constant-time behaviour is not
  claimed anywhere in this round (`OD-P16D-05`).
- **`NC-52` does not attack the signer registry itself.** It attacks a
  checkpoint against a registry assumed authorised. Whether the Election
  Board authorised that registry is outside the verifier's reach
  (`OD-P16D-12`) and therefore outside anything this corpus can express.
- **`NC-53` does not attack the ceremony's custody.** The reference
  ceremony exchanges shares in-process with no authenticated channel, no
  HSM and no key custody (`OD-P16D-11`); the corpus attacks the quorum
  arithmetic, not the channel it does not have.

## 5. What this document does not decide

```text
Completeness of the adversary model                  → PACK-17, external review
Hypothesis-based adversarial search                  → OD-P16D-03, PACK-17
Production datastore isolation for NC-31 / NC-32     → OD-P16D-04, PACK-17
Cross-mirror split-view detection                    → OD-P16D-06, PACK-17
Authorisation of the signer registry behind NC-52    → OD-P16D-12, PACK-17, governance
Ceremony custody and channel behind NC-53            → OD-P16D-11, PACK-17
Side-channel and timing analysis                     → OD-P16D-05, external review
Parameter appropriateness behind NC-08 … NC-11       → VO-08, PACK-16B external review
```

**REFERENCE IMPLEMENTATION. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY.
NOT LEGALLY ACTIVATED.**
