# PACK-16C — Ballot Validation Pipeline

**Round:** PACK-16C — Casting, Receipt, Verification Client, Bulletin Board and Election Record. **Specification and ADR only. No code. No cryptographic implementation. Not implemented. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-101`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 0. The rule the whole pipeline exists to enforce

```text
FAIL CLOSED.

A ballot is accepted only if every check passed.
Nothing is accepted provisionally. Nothing is normalised.
Nothing is repaired. Nothing is published before it is verified.
```

| ID      | Rule                                                                                                                                                                          |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `VP-00` | **There is no "accept now, verify later" path**, no asynchronous validation queue whose output could arrive after acceptance, and no configuration that reorders these stages |

---

## 1. The ordered pipeline

Stages run **in this order**. A failure at any stage stops the pipeline and
returns a **distinct reason code**; later stages do not run.

| #   | Stage                                             | Checks                                                                                                                                                             | On failure                                                                                                          |
| --- | ------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------- |
| 1   | **Size and parse guard**                          | Envelope within the published maximum for the style; parses at all                                                                                                 | `submission.too_large`, `submission.malformed`                                                                      |
| 2   | **Schema validation**                             | Every required field present; **no unknown fields**; **no duplicate fields**; types correct                                                                        | `submission.schema_invalid`, `submission.unknown_field`, `submission.duplicate_field`                               |
| 3   | **Canonical encoding validation**                 | Fixed-length big-endian; no leading zeros, short forms, over-long forms or alternate representations; deterministic re-serialisation reproduces the received bytes | `submission.non_canonical_encoding`                                                                                 |
| 4   | **Protocol-profile validation**                   | `protocol_profile_id` = the context's profile                                                                                                                      | `submission.profile_unsupported`                                                                                    |
| 5   | **Parameter-set validation**                      | `parameter_set_id` and `specification_digest` match the context's, **bit for bit**                                                                                 | `parameter_set.digest_mismatch`, `parameter_set.not_approved`                                                       |
| 6   | **Election-context validation**                   | Context exists, is `voting_open`, and the submission is inside the window fixed by signed checkpoints                                                              | `submission.window_closed`, `submission.context_unknown`                                                            |
| 7   | **Manifest binding**                              | `manifest_digest` equals the context's published manifest digest                                                                                                   | `manifest.digest_mismatch`                                                                                          |
| 8   | **Ballot-style binding**                          | Style exists in that manifest; the envelope's contests and selections match the style exactly — same contests, same options, same order, same counts               | `manifest.ballot_style_unknown`, `ballot_preparation.style_shape_mismatch`                                          |
| 9   | **Group membership**                              | Every ciphertext component satisfies `0 ≤ x < p`                                                                                                                   | `parameter_set.membership_failed`                                                                                   |
| 10  | **Subgroup checks**                               | Every ciphertext component satisfies `x^q mod p = 1` — **on every element, every time**                                                                            | `parameter_set.membership_failed`                                                                                   |
| 11  | **Plaintext-knowledge proof**                     | `BM-14` — the submitter knows the plaintext and randomness                                                                                                         | `ballot_proof.knowledge_failed`                                                                                     |
| 12  | **Range proofs**                                  | Each selection encrypts 0 or 1                                                                                                                                     | `ballot_proof.range_failed`                                                                                         |
| 13  | **Contest-sum proofs**                            | Each contest sums to its selection limit                                                                                                                           | `ballot_proof.contest_sum_failed`                                                                                   |
| 14  | **Contest constraint verification**               | Selection limits, option limits and placeholder counts are those the style declares                                                                                | `ballot_preparation.contest_invalid`                                                                                |
| 15  | **Confirmation-code verification**                | Recomputed from the received encryptions and `H_E`; equals the submitted value                                                                                     | `ballot_proof.confirmation_code_mismatch`                                                                           |
| 16  | **Duplicate-ballot detection**                    | `ballot_id` not already on the board; envelope digest not already accepted                                                                                         | `acceptance.duplicate_ballot_id`                                                                                    |
| 17  | **Retry-token resolution**                        | Same token + identical envelope → return the prior outcome; same token + different envelope → reject                                                               | `submission.retry_token_conflict`                                                                                   |
| 18  | **Capability validity**                           | Capability well-formed, in-window, **unspent**                                                                                                                     | `continuation.invalid`, `continuation.already_spent`                                                                |
| —   | **— ATOMIC BOUNDARY OPENS —**                     |                                                                                                                                                                    |                                                                                                                     |
| 19  | **Re-check unspent**                              | Inside the boundary (`CN-03`)                                                                                                                                      | rollback, `acceptance.capability_already_spent`                                                                     |
| 20  | **Consume capability**                            | Exactly-once effect                                                                                                                                                | rollback                                                                                                            |
| 21  | **Durable acceptance**                            | Ballot recorded as accepted                                                                                                                                        | rollback                                                                                                            |
| 22  | **Sign publication commitment**                   | Returned to the client                                                                                                                                             | rollback                                                                                                            |
| —   | **— ATOMIC BOUNDARY CLOSES —**                    |                                                                                                                                                                    |                                                                                                                     |
| 23  | **Sealed batch commitment, then closure opening** | Committed in the named window, opened at closure, append-only (`PA-*` §4)                                                                                          | `bulletin_board.batch_commitment_missing`, `publication.deadline_missed` → `publication_disputed`, **never silent** |

---

## 2. Which side of the boundary each check sits on

```text
BEFORE (1–18)    repeatable · nothing consumed · nothing durable · no side effect
                 a failure here costs the voter nothing but a retry

INSIDE (19–22)   atomic · all or nothing · the only irreversible step

AFTER  (23)      durable and published · failure is public, never silent
```

| ID      | Rule                                                                                                                                                  |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `VP-01` | **Every cryptographic check is before the boundary.** Stages 9–15 may never be moved inside or after it                                               |
| `VP-02` | **Capability consumption is the last thing that happens before durable acceptance, and nothing cryptographic follows it**                             |
| `VP-03` | **Nothing is published before stage 15 has passed** (`BM-16`). Publication of an unverified ballot is prohibited, including "provisional" publication |
| `VP-04` | **A rejected ballot does not consume the capability** — for any rejection at stages 1–18                                                              |

---

## 3. The five prohibitions

```text
NO accept-now-verify-later
NO publish-before-proof-validation
NO silent proof normalization
NO silent field coercion
NO best-effort subgroup checks
```

| ID      | Rule                                                                                                                                                                                                               |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `VP-05` | **No proof is normalised, re-encoded, padded or "fixed" before verification.** A proof that verifies only after normalisation did not verify                                                                       |
| `VP-06` | **No field is coerced.** A string where an integer belongs is a rejection, not a conversion. A missing optional is not defaulted into a cryptographic input                                                        |
| `VP-07` | **Subgroup checks are exhaustive, not sampled.** Every element, every ballot, every time — no fast path, no cache keyed on ballot shape, no "trusted client" exemption                                             |
| `VP-08` | **A malformed proof is rejected as malformed, and is distinguished from an absent proof** in the reason code, because the two mean different things about what went wrong                                          |
| `VP-09` | **Verification failures are not retried internally.** A proof either verifies or it does not; a second attempt at the same computation is either identical or evidence of nondeterminism, which is itself a defect |

---

## 4. Reason-code discipline

| ID      | Rule                                                                                                                                                                                                                              |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `VP-10` | **Each failure class has its own reason code.** A single `BALLOT_INVALID` is prohibited: the difference between a range-proof failure and a canonical-encoding failure is the difference between a defective client and an attack |
| `VP-11` | **No reason code reveals ballot content**, a nonce, a capability, or which contest or option was involved where that could narrow the choice. The code names the check, not the value (`RN-16C-*`)                                |
| `VP-12` | **The response to the voter is the reason code plus a governed German text**, and never a raw error, stack trace, exception message or field dump                                                                                 |
| `VP-13` | **Failure counts are aggregate and delayed.** Per-ballot rejection detail is not published before closure, because the pattern of rejections is a correlation surface (`BE-*`, `PM-*`)                                            |

---

## 5. What the server does not do

```text
does not decrypt anything
does not learn the choice
does not generate proofs on the voter's behalf
does not repair, complete or resubmit a ballot
does not decide cast versus challenge
does not see the continuation capability after stage 20
does not store the envelope together with any capability reference
does not log the envelope's ciphertexts alongside any request metadata
   that could identify the submitter
```

| ID      | Rule                                                                                                                                                                                                                                          |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `VP-14` | **The casting service is a validator and a recorder, not a participant.** It holds no key that decrypts anything, and its compromise cannot reveal a choice — only stop or corrupt the _process_, which the board and the record make visible |
| `VP-15` | **The service never sees the plaintext**, so no configuration, flag, debug mode or support tool can be built that exposes it. There is nothing to expose                                                                                      |

---

## 6. Independent re-verification

Every check in stages 2–16 is **re-performable by anyone** against the
published record — that is what makes the record self-sufficient.

| Stage                                             | Re-verifiable from the record?                                       | By whom                            |
| ------------------------------------------------- | -------------------------------------------------------------------- | ---------------------------------- |
| 2–3 schema and canonical encoding                 | **yes**                                                              | any verifier                       |
| 4–8 profile, parameters, context, manifest, style | **yes**                                                              | any verifier                       |
| 9–10 group and subgroup                           | **yes**                                                              | any verifier                       |
| 11–13 proofs                                      | **yes**                                                              | any verifier                       |
| 14 contest constraints                            | **yes**                                                              | any verifier                       |
| 15 confirmation code                              | **yes**                                                              | any verifier, and the voter        |
| 16 duplicates                                     | **yes**                                                              | any verifier, over the whole board |
| 17 retry token                                    | **no** — stripped before publication, by design (`BP-16`)            | nobody                             |
| 18–20 capability                                  | **no** — and must not be, because it would create the link (`CC-04`) | nobody                             |

| ID      | Rule                                                                                                                                                                                                                                                                                                                                          |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `VP-16` | **The two rows that are not re-verifiable are exactly the two that would create a person-to-ballot link.** Their unverifiability is a property of the design, is stated in the record's "what you cannot check" section (`BB-37`, `IV-*`), and is not presented as an oversight                                                               |
| `VP-17` | **Ballot-stuffing is therefore not verifiable from the record alone.** What a verifier can check is that every published ballot is well-formed, unique and included; what it cannot check is that each corresponded to a real, distinct entitlement. That is the price of unlinkability, and it is stated wherever verifiability is described |

**`VP-17` is the honest limit of this architecture and is not softened.** The
mitigations are the eligibility and issuance controls PACK-15 specified, the
separation of principals, and the published count reconciliation after
closure (`ER-*`) — not a proof in the record.

---

## 7. Failure handling summary

| Stage range | Capability  | Ballot state                                            | Voter action                                                                      |
| ----------- | ----------- | ------------------------------------------------------- | --------------------------------------------------------------------------------- |
| 1–8         | untouched   | `rejected`                                              | Fix and resubmit; usually a client defect                                         |
| 9–15        | untouched   | `rejected`                                              | **Cannot be fixed by the voter** — the client is defective or dishonest; escalate |
| 16–17       | untouched   | `rejected`                                              | Duplicate or conflicting retry; status check                                      |
| 18          | untouched   | `rejected`                                              | Capability problem; support path (`DP-*`)                                         |
| 19–22       | rolled back | `submitted`                                             | Retry with the same token                                                         |
| 23          | **spent**   | `accepted_pending_publication` → `publication_disputed` | Nothing the voter can do; election-level remedy                                   |

| ID      | Rule                                                                                                                                                                                                             |
| ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `VP-18` | **A stage 9–15 failure is a signal, not a nuisance.** Repeated proof failures across many submissions are evidence of a broken or hostile client build, are counted in aggregate, and escalate under `FM-16C-13` |

---

## 8. What this document does not decide

```text
Verification library and its selection      → OD-P16A-04, PACK-16D
Timeouts, rate limits, concurrency          → PACK-16D
Storage schema                               → PACK-16D
Aggregate-count publication delay            → PM-*, OD-P16C-*
```

**SPECIFIED. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY. NOT LEGALLY
ACTIVATED.**
