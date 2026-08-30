# PACK-16A — Reason Code Specification

**Round:** PACK-16A — Verifiable Voting Protocol and Ballot Model Selection. **Specification and ADR only. No code. Not implemented. Not an implementation candidate. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-099`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

**Specification-level namespaces only.** No registry is implemented, no
code is written, `tests/contract/test_reason_codes_registry.py` is not
touched, and the Canonical Schema Registry is not modified. These are the
codes a later round must register, with their meanings fixed now so that
they cannot drift.

---

## 0. The prohibitions that shape this catalogue

**There is no generic `VOTING_ERROR`, no `BALLOT_ERROR` and no
`TALLY_ERROR`, and none may be added.** PACK-13's `P13-RSN-002`, PACK-14's
restatement and PACK-15 §28 apply unchanged, and here the stakes are
highest: in a contested vote the difference between `BALLOT_PROOF_INVALID`
and `BALLOT_DUPLICATE_REJECTED` is the difference between a technical fault
and an allegation.

```text
Where two failures differ in what the participant must do next,
   they are two codes.
A code's meaning never changes; a new meaning is a new code.
No code reveals identity, credential ID, continuation capability,
   ballot choice, an exact correlation timestamp, or sensitive
   cryptographic material.
No code asserts a prohibited claim.
```

Every code is also a **user-facing obligation**: each maps to a governed
German text naming the reason, the responsible body and the next possible
step, in the `PACK-15-CONTENT-CATALOGUE-DE.md` lineage.

---

## 1. Ballot preparation refusal — `BALLOT_PREPARATION_*`

| Code                                         | Meaning                                                                 | Next step for the participant                  |
| -------------------------------------------- | ----------------------------------------------------------------------- | ---------------------------------------------- |
| `BALLOT_PREPARATION_MANIFEST_UNAVAILABLE`    | The election manifest could not be retrieved or validated               | Try again; contact the election office         |
| `BALLOT_PREPARATION_PARAMETERS_UNAVAILABLE`  | The cryptographic parameter set could not be retrieved or validated     | Try again later                                |
| `BALLOT_PREPARATION_PARAMETERS_REJECTED`     | The parameter set does not match the published identifier or provenance | Do not proceed; report it                      |
| `BALLOT_PREPARATION_CONTEST_INVALID`         | Selections do not satisfy the contest's selection limits                | Adjust the selection                           |
| `BALLOT_PREPARATION_RANDOMNESS_INSUFFICIENT` | The client's randomness self-test failed; encryption refused            | Use another device; use the fallback channel   |
| `BALLOT_PREPARATION_DEVICE_UNSUPPORTED`      | The device cannot perform the required operations                       | Use another device; use the fallback channel   |
| `BALLOT_PREPARATION_WINDOW_CLOSED`           | The voting window is not open                                           | Check the published window                     |
| `BALLOT_PREPARATION_PROFILE_UNSUPPORTED`     | The context declares a profile this client does not implement           | Update the client; contact the election office |

---

## 2. Handoff refusal — `HANDOFF_*`

Extends PACK-15's handoff codes; PACK-15's are unchanged.

| Code                            | Meaning                                             | Next step                               |
| ------------------------------- | --------------------------------------------------- | --------------------------------------- |
| `HANDOFF_ARTIFACT_INVALID`      | The handoff artifact failed validation              | Start again from the workspace          |
| `HANDOFF_ARTIFACT_EXPIRED`      | The artifact's validity window elapsed              | Start again                             |
| `HANDOFF_ARTIFACT_ALREADY_USED` | Single-use semantics; already redeemed              | Start again; dispute path if unexpected |
| `HANDOFF_AUDIENCE_MISMATCH`     | Presented at the wrong audience or origin           | Use the published entry point           |
| `HANDOFF_CONTEXT_MISMATCH`      | The artifact is bound to a different voting context | Select the correct vote                 |

---

## 3. Continuation consumption refusal — `CONTINUATION_*`

| Code                                    | Meaning                                                             | Next step                     |
| --------------------------------------- | ------------------------------------------------------------------- | ----------------------------- |
| `CONTINUATION_CAPABILITY_INVALID`       | Validation failed                                                   | Start again                   |
| `CONTINUATION_CAPABILITY_EXPIRED`       | Validity window elapsed                                             | Start again within the window |
| `CONTINUATION_CAPABILITY_ALREADY_SPENT` | **Already consumed.** Distinct from expiry and from replay          | Dispute path if unexpected    |
| `CONTINUATION_REPLAY_REJECTED`          | Replay detected                                                     | Dispute path                  |
| `CONTINUATION_CONTEXT_MISMATCH`         | Bound to a different context                                        | Select the correct vote       |
| `CONTINUATION_PRECONDITION_FAILED`      | Manifest, parameter or board-checkpoint validation failed (`CC-09`) | Do not proceed; report it     |

`CONTINUATION_CAPABILITY_ALREADY_SPENT` and `CONTINUATION_REPLAY_REJECTED`
are separate because they mean different things to the participant: the
first may be their own earlier successful use; the second is an attempt
they may not have made.

---

## 4. Ballot proof failure — `BALLOT_PROOF_*`

| Code                               | Meaning                                                       | Next step                                   |
| ---------------------------------- | ------------------------------------------------------------- | ------------------------------------------- |
| `BALLOT_PROOF_GENERATION_FAILED`   | The client could not generate the required proofs             | Try again; another device; fallback channel |
| `BALLOT_PROOF_KNOWLEDGE_MISSING`   | No proof of knowledge of the plaintext was supplied (`BM-14`) | Client defect; report it                    |
| `BALLOT_PROOF_RANGE_INVALID`       | A per-selection range proof failed                            | Client defect; report it                    |
| `BALLOT_PROOF_CONTEST_SUM_INVALID` | The contest-sum proof failed against the selection limit      | Client defect; report it                    |
| `BALLOT_PROOF_PARAMETER_MISMATCH`  | Proofs are under a different parameter set                    | Client defect; report it                    |
| `BALLOT_PROOF_VERIFICATION_FAILED` | Verification failed for a reason not covered above            | Report it; the ballot is not recorded       |

---

## 5. Ballot validation and acceptance — `BALLOT_*`

| Code                        | Meaning                                                               | Next step                                |
| --------------------------- | --------------------------------------------------------------------- | ---------------------------------------- |
| `BALLOT_ACCEPTED`           | Recorded and queued for publication                                   | Note the confirmation code; verify later |
| `BALLOT_PUBLISHED`          | Present on the bulletin board                                         | Verify with the confirmation code        |
| `BALLOT_SUBMISSION_REFUSED` | Submission refused for a stated preceding reason                      | See the specific code                    |
| `BALLOT_MANIFEST_MISMATCH`  | Contests do not match the frozen manifest                             | Reload; report it                        |
| `BALLOT_OUTSIDE_WINDOW`     | Submitted after the closure checkpoint                                | The window has closed                    |
| `BALLOT_DUPLICATE_REJECTED` | A duplicate identifier or an identical ciphertext                     | Dispute path if unexpected               |
| `BALLOT_REPLAY_REJECTED`    | A previously seen ciphertext was resubmitted                          | Dispute path                             |
| `BALLOT_NOT_FOUND_ON_BOARD` | **A first-class outcome** — the confirmation code is not on the board | **Dispute path immediately** (`BM-19`)   |

`BALLOT_NOT_FOUND_ON_BOARD` is the most important code in this catalogue.
It is not an error state, it is not a lookup failure, and it must never be
presented as one. It is the outcome that makes `recorded as cast`
meaningful, and it has its own dispute path.

---

## 6. Challenge, spoil and revote — `BALLOT_CHALLENGE_*`, `BALLOT_SPOIL_*`, `BALLOT_REVOTE_*`, `BALLOT_SUPERSESSION_*`

| Code                                | Meaning                                                                        | Next step                       |
| ----------------------------------- | ------------------------------------------------------------------------------ | ------------------------------- |
| `BALLOT_CHALLENGE_ACCEPTED`         | The challenge was accepted; the ballot is opened and spoiled                   | Check the opening; vote again   |
| `BALLOT_CHALLENGE_FAILED`           | The challenge could not be completed                                           | Try again; report it            |
| `BALLOT_CHALLENGE_MISMATCH`         | **The opening does not match what was displayed** — a client integrity finding | **Stop; report it immediately** |
| `BALLOT_SPOILED`                    | The ballot is spoiled and will never be tallied                                | Vote again                      |
| `BALLOT_SPOIL_PUBLISHED`            | The spoiled ballot and its opening are on the board                            | Verifiable by anyone            |
| `BALLOT_REVOTE_NOT_PERMITTED`       | Revoting is not available in this profile                                      | See the published rules         |
| `BALLOT_SUPERSESSION_NOT_PERMITTED` | Supersession is not reachable in this profile (`§3.4` of the lifecycle)        | —                               |

`BALLOT_CHALLENGE_MISMATCH` is the single code that reports a **detected
dishonest client**. Its governed text must not minimise it, must not
suggest user error, and must route to an incident path rather than to
support.

---

## 7. Bulletin board — `BOARD_*`

| Code                            | Meaning                                              | Next step                                     |
| ------------------------------- | ---------------------------------------------------- | --------------------------------------------- |
| `BOARD_PUBLICATION_FAILED`      | An accepted ballot could not be published            | Voting is paused (`FM-P16A-09`)               |
| `BOARD_UNAVAILABLE`             | The board cannot be reached                          | Try again; voting may be paused               |
| `BOARD_CHECKPOINT_INVALID`      | A checkpoint failed signature or chain verification  | Stop; report it                               |
| `BOARD_CHECKPOINT_CHAIN_BROKEN` | The checkpoint chain does not link                   | Stop; report it                               |
| `BOARD_MIRROR_DIVERGENCE`       | **Mirrors disagree** — equivocation indicator        | **Voting halts** (`FM-P16A-10`, `FM-P16A-11`) |
| `BOARD_MIRROR_UNAVAILABLE`      | A mirror cannot be reached; distinct from divergence | Recorded; monitored                           |
| `BOARD_ENTRY_NOT_FOUND`         | The queried confirmation code is not present         | See `BALLOT_NOT_FOUND_ON_BOARD`               |
| `BOARD_APPEND_REJECTED`         | An append was refused by privacy filtering (`BB-21`) | Defect; report it                             |

---

## 8. Verification, tally, trustee, quorum, election state, audit, archive

### 8.1 `VERIFICATION_*`

| Code                               | Meaning                                                             |
| ---------------------------------- | ------------------------------------------------------------------- |
| `VERIFICATION_CODE_PRESENT`        | The confirmation code is on the board                               |
| `VERIFICATION_CODE_ABSENT`         | It is not — first-class outcome, dispute path                       |
| `VERIFICATION_CHECKPOINT_MISMATCH` | The checkpoint shown does not appear in the published chain         |
| `VERIFICATION_RECORD_INCOMPLETE`   | The published record is insufficient to verify                      |
| `VERIFICATION_PROOF_MISMATCH`      | An independent verifier's check failed against the published record |

### 8.2 `TALLY_*`

| Code                                 | Meaning                                                                             |
| ------------------------------------ | ----------------------------------------------------------------------------------- |
| `TALLY_NOT_PERMITTED_BEFORE_CLOSURE` | A decryption or aggregation was attempted before `voting_closed`                    |
| `TALLY_AGGREGATION_FAILED`           | Aggregation over the checkpointed set failed                                        |
| `TALLY_SHARE_INVALID`                | A decryption share failed proof verification — **halts the tally**                  |
| `TALLY_EXCLUSION_APPLIED`            | A ballot was excluded with a published reason (`EX-03`)                             |
| `TALLY_EXCLUSION_REFUSED`            | An exclusion was requested on a ground not in the closed list (`EX-01`)             |
| `TALLY_RESULT_UNCERTIFIABLE`         | The evidence is insufficient for independent verification (§5 of the failure model) |
| `TALLY_RESULT_WITHHELD_DISCLOSURE`   | Publication withheld under small-cell disclosure control (`SD-08`)                  |

### 8.3 `TRUSTEE_*` and `QUORUM_*`

| Code                            | Meaning                                                             |
| ------------------------------- | ------------------------------------------------------------------- |
| `TRUSTEE_PARTICIPATION_FAILED`  | A trustee could not complete their contribution                     |
| `TRUSTEE_PROOF_INVALID`         | A trustee's key-generation or share proof failed                    |
| `TRUSTEE_UNAVAILABLE`           | A trustee is absent; compensated shares may apply (`KC-11`)         |
| `TRUSTEE_SUBSTITUTION_RECORDED` | A trustee was substituted before the ceremony, under dual control   |
| `QUORUM_NOT_MET`                | Fewer than k trustees are available                                 |
| `QUORUM_LOST`                   | Quorum is permanently unobtainable — **the result is unobtainable** |

### 8.4 `ELECTION_*`

| Code                                   | Meaning                                                            |
| -------------------------------------- | ------------------------------------------------------------------ |
| `ELECTION_PAUSED`                      | Casting suspended; existing ballots stand                          |
| `ELECTION_RESUMED`                     | Casting resumed                                                    |
| `ELECTION_WINDOW_EXTENDED`             | The window was lengthened, with a reason                           |
| `ELECTION_SUSPENDED`                   | Stopped pending a governance decision                              |
| `ELECTION_ABORTED`                     | Stopped before a result                                            |
| `ELECTION_ANNULLED`                    | A result declared void                                             |
| `ELECTION_RERUN_SCHEDULED`             | A new context will be held                                         |
| `VOTING_CONTEXT_CONFIGURATION_INVALID` | Configuration outside permitted ranges (PACK-15 §19.2)             |
| `VOTING_CONTEXT_LEGAL_BASIS_MISSING`   | The declared mode has no legal basis; activation refused           |
| `VOTING_PROFILE_NOT_ACTIVATED`         | The declared profile is not activated (`§2.1` of the ballot model) |

### 8.5 `AUDIT_*` and `ARCHIVE_*`

| Code                               | Meaning                                                               |
| ---------------------------------- | --------------------------------------------------------------------- |
| `AUDIT_DISCREPANCY_DETECTED`       | Evidence-bundle validation or count-consistency failed                |
| `AUDIT_EXPORT_REFUSED`             | An export naming two contexts or two streams' raw content was refused |
| `AUDIT_PRECLOSURE_SECTION_REFUSED` | An outcome-bearing section was requested before closure               |
| `ARCHIVE_VERIFICATION_FAILED`      | An archived record failed integrity verification                      |
| `ARCHIVE_DISCREPANCY_DETECTED`     | The archive differs from the published record                         |
| `ARCHIVE_EVIDENCE_LOST`            | Evidence required for verification is irrecoverably lost              |

---

## 9. Properties every code must have

| ID      | Property                                                                                                                     |
| ------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `RC-01` | **Stable** — the identifier never changes; a new meaning is a new code                                                       |
| `RC-02` | **Machine-readable** — `SCREAMING_SNAKE_CASE`, namespaced by prefix                                                          |
| `RC-03` | **Privacy-safe** — reveals no identity, no credential ID, no continuation capability, no ballot choice, no exact timestamp   |
| `RC-04` | **Non-identifying** — a code plus its context does not narrow a population below `disclosure_min_cell`                       |
| `RC-05` | **Non-secret-dependent** — carries no cryptographic material and no value whose secrecy matters                              |
| `RC-06` | **Suitable for UI mapping** — one governed text per code, per language, naming the next step                                 |
| `RC-07` | **Suitable for audit** — usable in an evidence bundle without further redaction                                              |
| `RC-08` | **Compatible with the Canonical Schema Registry** — registrable without a schema change; the registration is a later round's |
| `RC-09` | **No prohibited claim** — no code's text asserts anything in `PACK-16A-COERCION-AND-RECEIPT-BOUNDARY.md` §8                  |
| `RC-10` | **No generic fallback code** — an unmapped condition is a specification defect, not a `*_ERROR`                              |

### 9.1 Codes deliberately absent

```text
No code reports "this participant has already voted."
No code reports "this ballot belongs to you."
No code reports "your vote was counted for option X."
No code distinguishes failures in a way that reveals turnout.
No code carries a count before closure.
No generic VOTING_ERROR, BALLOT_ERROR or TALLY_ERROR.
```

The first three are absent because the questions are unanswerable by
design, and a code that appeared to answer them would be a linkage claim.

---

## 10. What PACK-16A does not do

```text
Register any code in the Canonical Schema Registry
Modify tests/contract/test_reason_codes_registry.py
Modify any schema, contract fixture or event catalogue
Produce the governed German texts
```

Registration and content are **PACK-16C's and FRONT-PACK's**. This
document fixes the namespaces and the meanings so that they cannot drift
between here and there.

**SPECIFIED. NOT IMPLEMENTED. NOT REGISTERED. REQUIRES EXTERNAL REVIEW. NOT
PRODUCTION READY. NOT LEGALLY ACTIVATED.**
