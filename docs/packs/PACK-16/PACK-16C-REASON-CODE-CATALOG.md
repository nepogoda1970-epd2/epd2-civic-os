# PACK-16C — Reason Code Catalog

**Round:** PACK-16C — Casting, Receipt, Verification Client, Bulletin Board and Election Record. **Specification and ADR only. No code. No cryptographic implementation. Not implemented. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-101`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

**Specification-level namespaces only.** No registry is implemented, no code
is written, `tests/contract/test_reason_codes_registry.py` is untouched, and
the Canonical Schema Registry is not modified. These are the codes a later
round must register.

---

## 0. The invariants, inherited and restated

PACK-13 `P13-RSN-002`, PACK-14, PACK-15 §28, PACK-16A §0 and PACK-16B §1
apply unchanged.

```text
NO generic code. There is no ballot.error, no casting.failed,
   no publication.error, and none may be added.
Two failures that differ in what the participant must do next
   are two codes.
A code's meaning never changes. A new meaning is a new code.
No code reveals identity, credential, continuation capability,
   ballot choice, an exact correlation timestamp, or any secret.
No code asserts a prohibited claim (PB-*).
```

| ID       | Rule                                                                                                              |
| -------- | --------------------------------------------------------------------------------------------------------------------- |
| `RN-16C-01` | **The reason code names the check, never the value.** `ballot_proof.range_failed` says a range proof failed; it does not say for which contest or option, because that could narrow the choice (`VP-11`) |
| `RN-16C-02` | **No code carries a ballot identifier, a confirmation code, a retry token or a continuation reference as a field.** The code plus a governed German text is the entire participant-facing response (`VP-12`) |
| `RN-16C-03` | **No PACK-16C code is minted for a condition PACK-16A or PACK-16B already named.** Where the condition exists, the earlier code is reused — §5 lists every reuse |
| `RN-16C-04` | **Operational codes and participant-facing codes are different populations.** A voter sees a governed text; the audit stream and the record see the code. Enriching the participant text with operational detail is prohibited (`RN-C13` lineage) |

---

## 1. `manifest.*` — the election's definition

| Code | Meaning | Participant next step |
| ---- | ------- | --------------------- |
| `manifest.unavailable` | The manifest could not be retrieved | Try again; contact the election office |
| `manifest.signature_invalid` | The manifest's signature does not verify | **Do not proceed**; report it |
| `manifest.signer_unknown` | The signer is not in the published set | **Do not proceed**; report it |
| `manifest.digest_mismatch` | The manifest digest differs from the published one, or from the one an envelope binds | **Do not proceed**; report it |
| `manifest.context_closed` | The context is not open for voting | Check the published window |
| `manifest.ballot_style_unknown` | The style is not in this manifest | Contact the election office |
| `manifest.election_type_unsupported` | The client does not implement this election type | Update the client |
| `manifest.joint_key_mismatch` | The joint key does not match the ceremony record | **Do not proceed**; report it — `FM-16C-04` |
| `manifest.ceremony_checkpoint_missing` | The ceremony checkpoint the key should bind to is absent | **Do not proceed**; report it |
| `manifest.client_build_mismatch` | The served build does not match the published build digest | **Do not proceed**; report it — `FM-16C-01`, `D-05` |

| ID       | Rule                                                                                                          |
| -------- | ----------------------------------------------------------------------------------------------------------------- |
| `RN-16C-05` | **The four "do not proceed" codes above are not retryable and must never be presented as transient.** Each means the client is looking at something other than the published election |

---

## 2. `parameter_set.*` — inherited from PACK-16B, unchanged

`parameter_set.not_approved`, `parameter_set.digest_mismatch`,
`parameter_set.deprecated`, `parameter_set.prohibited`,
`parameter_set.membership_failed` are **defined in
`PACK-16B-REASON-CODE-SPECIFICATION.md` and reused verbatim.** PACK-16C
adds no `parameter_set.*` code and redefines none.

| ID       | Rule                                                                                                          |
| -------- | ----------------------------------------------------------------------------------------------------------------- |
| `RN-16C-06` | **`parameter_set.membership_failed` covers both the group-membership and the subgroup check** (pipeline stages 9 and 10). The two are not split, because the participant action is identical and the distinction is in the audit stream's `check` field, not in a second code |

---

## 3. `continuation.*` — the capability

| Code | Meaning | Participant next step |
| ---- | ------- | --------------------- |
| `continuation.absent` | No capability was presented | Start again from the workspace |
| `continuation.malformed` | The capability does not parse | Start again |
| `continuation.invalid` | Validation failed | Start again |
| `continuation.already_spent` | **Already consumed.** Distinct from expiry and from replay | Dispute path if unexpected — `DP-*` |
| `continuation.window_closed` | The capability's validity window elapsed | Start again within the window |

| ID       | Rule                                                                                                          |
| -------- | ----------------------------------------------------------------------------------------------------------------- |
| `RN-16C-07` | **`continuation.already_spent` is never merged with `continuation.invalid`.** A voter who is told "invalid" when the truth is "you have already voted" cannot tell an error from a possible compromise (`CN-*`) |
| `RN-16C-08` | **No `continuation.*` code carries the capability, a hash of it, or anything derived from it.** The code is the whole answer |

---

## 4. The casting-path namespaces

### 4.1 `ballot_preparation.*` — before any ciphertext exists

| Code | Meaning | Participant next step |
| ---- | ------- | --------------------- |
| `ballot_preparation.contest_invalid` | Selections violate the contest's limits | Adjust the selection |
| `ballot_preparation.overvote` | More selections than the limit | Remove a selection |
| `ballot_preparation.selection_unknown` | A selection is not an option of this contest | Reload the ballot |
| `ballot_preparation.contest_inactive` | The contest is not active in this context | Contact the election office |
| `ballot_preparation.style_shape_mismatch` | The envelope's shape does not match the declared style | **Client defect** — report it |
| `ballot_preparation.placeholder_failure` | Placeholder construction failed | Retry; report if it persists |
| `ballot_preparation.undervote_confirmed` | The voter chose fewer than the limit and confirmed | **none — this is a normal outcome** |
| `ballot_preparation.blank_contest_confirmed` | The voter left a contest blank and confirmed | **none — normal** |
| `ballot_preparation.blank_ballot_confirmed` | The voter left the whole ballot blank and confirmed | **none — normal** |

| ID       | Rule                                                                                                          |
| -------- | ----------------------------------------------------------------------------------------------------------------- |
| `RN-16C-09` | **The last three are outcomes, not failures**, and are catalogued as codes because a blank ballot must be an explicit, confirmed, recorded choice rather than an unhandled state. They are never presented as errors and never block casting |
| `RN-16C-10` | **No `ballot_preparation.*` code names a contest or an option.** `overvote` says the limit was exceeded, not where |

### 4.2 `ballot_encryption.*`

| Code | Meaning | Participant next step |
| ---- | ------- | --------------------- |
| `ballot_encryption.failed` | Encryption could not complete on this device | Retry; use another device; use the alternative channel |

**Randomness self-test failure reuses PACK-16B's
`ballot.randomness_insufficient` and is not re-minted here** (`RN-16C-03`).

### 4.3 `ballot_proof.*`

| Code | Meaning | Where it arises | Participant next step |
| ---- | ------- | --------------- | --------------------- |
| `ballot_proof.generation_failed` | The client could not produce a proof | client, step 12 | **Fail closed.** Retry; do not submit |
| `ballot_proof.invalid` | A proof did not verify, class unspecified | service | **Client defect or attack** — report it |
| `ballot_proof.knowledge_failed` | The plaintext-knowledge proof failed | pipeline 11 | as above |
| `ballot_proof.range_failed` | A selection is not an encryption of 0 or 1 | pipeline 12 | as above |
| `ballot_proof.contest_sum_failed` | A contest does not sum to its limit | pipeline 13 | as above |
| `ballot_proof.confirmation_code_mismatch` | The recomputed code differs from the submitted one | pipeline 15 | as above |

| ID       | Rule                                                                                                          |
| -------- | ----------------------------------------------------------------------------------------------------------------- |
| `RN-16C-11` | **`ballot_proof.invalid` is never used where a specific code applies.** It exists only for a proof that fails in a way the pipeline's named stages do not cover, and its use is itself a signal worth investigating |
| `RN-16C-12` | **A malformed proof and an absent proof are distinguished** — the former by `submission.schema_invalid`, the latter by `submission.schema_invalid` with a distinct `check` field, never by silently accepting either (`VP-08`) |

### 4.4 `challenge.*`

| Code | Meaning | Public? |
| ---- | ------- | ------- |
| `challenge.selected` | The voter chose to challenge | no |
| `challenge.commitment_missing` | A cast or challenge was attempted with no prior commitment | no — **the flow stops** (`FM-16C-10`) |
| `challenge.opening_incomplete` | The published opening does not cover every encryption | no |
| `challenge.reencryption_mismatch` | Re-encrypting the opening does not reproduce the ciphertexts | **yes — this is the detection event** |
| `challenge.class_mismatch` | The opening's ballot style or shape does not match | yes |
| `challenge.spoiled_published` | The challenged ballot and its opening were published | **yes, batched** |
| `challenge.abandoned` | A challenge was begun and not completed | no |

| ID       | Rule                                                                                                          |
| -------- | ----------------------------------------------------------------------------------------------------------------- |
| `RN-16C-13` | **`challenge.reencryption_mismatch` is the highest-severity participant-triggered event in the system.** It means a client encrypted something other than what was chosen. It escalates to `FM-16C-13` and `D-04` automatically and is never presented to the voter as a routine error |
| `RN-16C-14` | **No `challenge.*` code reveals the opened content**, which is published separately and on the batch schedule, not in the code |

### 4.5 `submission.*`

| Code | Meaning | Stage |
| ---- | ------- | ----- |
| `submission.sent` | The client sent an envelope | client |
| `submission.too_large` | Envelope exceeds the published maximum | 1 |
| `submission.malformed` | Envelope does not parse | 1 |
| `submission.schema_invalid` | A required field is missing or mistyped | 2 |
| `submission.unknown_field` | An unknown field is present | 2 |
| `submission.duplicate_field` | A field appears twice | 2 |
| `submission.non_canonical_encoding` | Encoding is not the canonical form | 3 |
| `submission.profile_unsupported` | The profile is not this context's | 4 |
| `submission.context_unknown` | The context does not exist | 6 |
| `submission.window_closed` | Outside the voting window | 6 |
| `submission.retry_token_conflict` | Same token, different envelope | 17 |
| `submission.timeout` | No response within the bound | client |

| ID       | Rule                                                                                                          |
| -------- | ----------------------------------------------------------------------------------------------------------------- |
| `RN-16C-15` | **`submission.unknown_field` and `submission.duplicate_field` are separate codes and neither is a warning.** Both are rejections, because both are how a malleability or confusion attack presents (`VP-06`) |
| `RN-16C-16` | **`submission.timeout` is a client-side observation, not a server verdict.** It never means the ballot was lost, and the governed text says so — the voter's next step is a status check, not a resubmission (`CN-26`) |

### 4.6 `acceptance.*` — the atomic boundary

| Code | Meaning | Public? |
| ---- | ------- | ------- |
| `acceptance.duplicate_ballot_id` | The identifier or envelope digest is already on the board | no |
| `acceptance.capability_already_spent` | The re-check inside the boundary found it spent | no |
| `acceptance.atomic_boundary_failed` | The boundary rolled back | no |
| `acceptance.commitment_signing_failed` | The publication commitment could not be signed | no |
| `acceptance.committed` | The boundary committed; the ballot is accepted | no, until publication |
| `acceptance.excluded` | A ballot was excluded from the tally with a published ground | **yes** |

| ID       | Rule                                                                                                          |
| -------- | ----------------------------------------------------------------------------------------------------------------- |
| `RN-16C-17` | **`acceptance.excluded` always carries a published ground from the closed list and never stands alone** (`EX-01`…`EX-07`, `BL-04`). A code without a ground is a silent exclusion by another name |
| `RN-16C-18` | **`acceptance.atomic_boundary_failed` means nothing was consumed.** The governed text tells the voter to retry with the same token, because a rollback that reads as a loss will cause a voter to abandon a ballot they still hold (`VP-*` §7) |

### 4.7 `publication.*`

| Code | Meaning | Public? |
| ---- | ------- | ------- |
| `publication.published` | The ballot appears on the board under a checkpoint | **yes** |
| `publication.delayed` | Publication is behind schedule but inside the deadline | **yes** |
| `publication.failed` | A publication attempt failed | **yes** |
| `publication.deadline_missed` | The published deadline passed without publication | **yes** — `publication_disputed` |
| `publication.recovered` | A disputed publication was remedied within the escalation window | **yes** |
| `publication.unrecoverable` | Not remedied; escalates to the election level | **yes** — `FM-16C-16` |

| ID       | Rule                                                                                                          |
| -------- | ----------------------------------------------------------------------------------------------------------------- |
| `RN-16C-19` | **Every `publication.*` code except `published` is a public failure notice** (`ER-*` artefact 29). None may be recorded operationally without being published, because a hidden publication failure is indistinguishable from censorship (`PA-*`) |

### 4.8 `receipt.*`, `verification.*`, `election.*`, `archive.*`

| Code | Meaning | Note |
| ---- | ------- | ---- |
| `receipt.generation_failed` | The receipt could not be produced | **The ballot stays accepted**; the receipt is re-derivable (`RE-04`) — never presented as a casting failure |
| `verification.code_not_found` | A looked-up confirmation code is not on the board | **First-class outcome with a dispute path** (`RE-08`, `D-01`), never a generic "not found" |
| `election.closed` | The closure checkpoint fixed the eligible set | Public |
| `archive.sealed` | An archive checkpoint was published over the record | Public |

| ID       | Rule                                                                                                          |
| -------- | ----------------------------------------------------------------------------------------------------------------- |
| `RN-16C-20` | **`verification.code_not_found` never implies voter error.** Its governed text states the three possibilities — mistranscription, a client that never submitted, or a publication failure — and routes to the dispute path rather than to an apology |

---

## 4A. The sealed batch layer — added by the turnout correction

### 4A.1 `bulletin_board.*` — the board's own obligations

| Code | Meaning | Public? |
| ---- | ------- | ------- |
| `bulletin_board.batch_commitment_missing` | A scheduled batch window passed with no `sealed_batch_commitment` | **yes, immediately** — `FM-16C-18` |
| `bulletin_board.batch_commitment_late` | The commitment was published after its scheduled window time | **yes**, with the delay stated — `FM-16C-19` |
| `bulletin_board.batch_root_mismatch` | A `commitment_root` does not recompute from its published opening | **yes** — `FM-16C-22` |
| `bulletin_board.batch_opening_missing` | A published commitment has no closure opening, or an incomplete one | **yes** — `FM-16C-23` |
| `bulletin_board.batch_opening_invalid` | An opening is malformed, has the wrong leaf count, or contradicts its commitment | **yes** — `FM-16C-23` |
| `bulletin_board.duplicate_leaf_opening` | Two openings claim the same leaf, or one leaf opens to two artefacts | **yes** — `FM-16C-24` |
| `bulletin_board.cover_leaf_invalid` | A leaf declared `cover` opens to a structured value, or a leaf declared real opens to a random one | **yes** — `FM-16C-26` |
| `bulletin_board.late_insertion_detected` | A ballot artefact appears with no pre-closure committed leaf | **yes** — `FM-16C-25` |
| `bulletin_board.batch_reconciliation_failed` | The reconciliation does not close in either direction | **yes** — `FM-16C-27` |

### 4A.2 `verification.*` additions

| Code | Meaning |
| ---- | ------- |
| `verification.batch_inclusion_failed` | A voter's leaf does not verify against the batch's `commitment_root` |
| `verification.batch_consistency_failed` | A batch commitment is inconsistent with the checkpoint chain that carries it |

### 4A.3 `publication.*` additions

| Code | Meaning | Public? |
| ---- | ------- | ------- |
| `publication.batch_committed` | The ballot's leaf is inside its named window's `commitment_root` | **the commitment, yes; the ballot, no** |
| `publication.batch_delayed` | A commitment obligation is behind schedule but inside the escalation window | **yes**, without a count |

### 4A.4 `privacy.*` — a new namespace

| Code | Meaning |
| ---- | ------- |
| `privacy.turnout_oracle_detected` | A query pattern consistent with occupancy probing or confirmation-code enumeration was detected |

### 4A.5 `election_record.*` — a new namespace

| Code | Meaning |
| ---- | ------- |
| `election_record.batch_artifact_missing` | A mandatory artefact 33, 34 or 35 is absent from the published record |

| ID       | Rule                                                                                                          |
| -------- | ----------------------------------------------------------------------------------------------------------------- |
| `RN-16C-25` | **Every `bulletin_board.*` code is a public failure notice.** None may be recorded operationally without being published, because a hidden batch failure is indistinguishable from occupancy manipulation (`TC-54`, `RN-16C-19`) |
| `RN-16C-26` | **No code in §4A carries a count, an occupancy figure, a leaf index or a ballot reference.** `bulletin_board.batch_commitment_missing` names the window, never how many ballots it should have held (`TC-07`, `PA-05`) |
| `RN-16C-27` | **`privacy.turnout_oracle_detected` is an internal detection code and is never returned to a caller.** Returning it would tell an attacker their probing was noticed and would itself be an oracle |
| `RN-16C-28` | **`verification.batch_inclusion_failed` is never presented to a voter as their error.** It means the board's commitment does not contain what the board said it would, and it routes to `D-01` (`RN-16C-20`, `DP-05`) |

---

## 4B. Bounded challenge and finite capacity — added by the capacity correction

| Code | Meaning | Public? |
| ---- | ------- | ------- |
| `challenge.public_entitlement_exhausted` | A second, differing public evidentiary challenge was attempted on a capability whose public-challenge entitlement is spent | no — the voter is told the audit challenge is available once, **before** they use it |
| `challenge.public_reservation_unavailable` | No allowed leaf slot could be reserved for a public evidentiary challenge | no |
| `submission.cast_capacity_unavailable` | No cast-reserved leaf slot could be reserved for a final cast ballot | no |
| `bulletin_board.batch_capacity_exhausted` | Every predeclared slot allowed to a submission in the interval is unavailable | **yes, as an election-wide capacity incident, without any count** |
| `publication.unscheduled_batch_prohibited` | An attempt to publish a batch commitment outside the predeclared schedule | **yes** |
| `privacy.adaptive_capacity_signal_prevented` | A capacity-driven change that would have altered the published shape was refused | **no** — internal detection only |
| `election.capacity_plan_invalid` | The published capacity plan does not satisfy `Σ C_interval ≥ L_max + reserve`, or was not published before opening | **yes — the context is not activated** |

| ID       | Rule                                                                                                          |
| -------- | ----------------------------------------------------------------------------------------------------------------- |
| `RN-16C-29` | **No capacity code reports occupancy, remaining slots, a queue depth or a turnout figure**, to a voter or to any caller. It names the condition, never the number (`TC-81`, `RN-16C-26`) |
| `RN-16C-30` | **`challenge.public_entitlement_exhausted` is not an error the voter should be surprised by.** The interface states the entitlement is available once before it is used; the code exists for the fail-closed path and for a defective client (`CH-51`) |
| `RN-16C-31` | **`challenge.public_reservation_unavailable` and `submission.cast_capacity_unavailable` are distinct**, because a challenge may be refused while cast capacity is intact — that is exactly what the cast-reserved partition is for (`TC-75`) |
| `RN-16C-32` | **`bulletin_board.batch_capacity_exhausted` is published as an election-wide incident with no figure at all.** A count of unserved submissions would be a turnout proxy (`TC-81`) |
| `RN-16C-33` | **`privacy.adaptive_capacity_signal_prevented` is an internal detection code and is never returned to a caller**, for the same reason as `privacy.turnout_oracle_detected` (`RN-16C-27`) |
| `RN-16C-34` | **`election.capacity_plan_invalid` blocks activation.** It is not a warning and has no override |
| `RN-16C-35` | **There is no reason code for a local diagnostic challenge.** It reaches no server, so it produces no server-side code; `challenge.local_completed` is a client-local outcome, not a reason code (`CH-42`) |

---

## 5. Reuse from earlier rounds — the complete list

**No code below is redefined. Each is used with its original meaning.**

| Code | Defined in | Used by PACK-16C for |
| ---- | ---------- | -------------------- |
| `parameter_set.not_approved` | PACK-16B | Pipeline stage 5; casting flow step 4 |
| `parameter_set.digest_mismatch` | PACK-16B | Pipeline stage 5 |
| `parameter_set.deprecated` | PACK-16B | Casting flow step 4 |
| `parameter_set.prohibited` | PACK-16B | Casting flow step 4 |
| `parameter_set.membership_failed` | PACK-16B | Pipeline stages 9 and 10 |
| `ballot.randomness_insufficient` | PACK-16B | Casting flow step 11 — **not re-minted** |
| `joint_key.published` | PACK-16B | Board entry for the ceremony's joint key |
| `BALLOT_PREPARATION_*`, `CONTINUATION_*`, `HANDOFF_*` | PACK-16A | **Participant-facing** codes, unchanged; PACK-16C's codes are operational and map to them |

| ID       | Rule                                                                                                          |
| -------- | ----------------------------------------------------------------------------------------------------------------- |
| `RN-16C-21` | **The PACK-16A participant-facing catalogue is not extended by this round.** Where a PACK-16C operational code must reach a voter, it maps to an existing PACK-16A code or to a governed text, and the mapping is many-to-one and lossy on purpose |

---

## 6. Counts and uniqueness

```text
Namespaces opened by PACK-16C                            16
Namespaces reused without redefinition                    2   parameter_set.*, ballot.*
Codes defined by PACK-16C                                88
   of which added by the turnout correction              15
   of which added by the capacity correction              7
Codes reused from PACK-16A/16B without redefinition       7
Codes redefined                                            0
Generic catch-all codes                                    0
Codes carrying a ballot identifier or secret               0
```

| Namespace | New codes |
| --------- | --------- |
| `manifest.*` | 10 |
| `continuation.*` | 5 |
| `ballot_preparation.*` | 9 |
| `ballot_encryption.*` | 1 |
| `ballot_proof.*` | 6 |
| `challenge.*` | 9 | *(7 + 2 from §4B)* |
| `submission.*` | 13 | *(12 + 1 from §4B)* |
| `acceptance.*` | 6 |
| `publication.*` | 9 | *(6 + 2 from §4A.3 + 1 from §4B)* |
| `receipt.*` | 1 |
| `verification.*` | 3 | *(1 + 2 from §4A.2)* |
| `election.*` | 2 | *(1 + 1 from §4B)* |
| `archive.*` | 1 |
| `bulletin_board.*` | 10 | *(9 from §4A.1 + 1 from §4B)* |
| `privacy.*` | 2 | *(1 from §4A.4 + 1 from §4B)* |
| `election_record.*` | 1 | *(new — §4A.5)* |
| **total** | **88** |

| ID       | Rule                                                                                                          |
| -------- | ----------------------------------------------------------------------------------------------------------------- |
| `RN-16C-22` | **The count is computed from the tables above, not asserted.** Sixteen namespaces are opened and sixteen rows appear; `parameter_set.*` and `ballot.*` are absent from that table because they are reused rather than opened, and the sum of the right-hand column is the defined-code count |
| `RN-16C-23` | **Every code in this catalogue is referenced by at least one PACK-16C document.** A code with no referencing document is removed rather than kept for completeness |
| `RN-16C-24` | **Registration happens in PACK-16D, not here.** These namespaces are reserved by specification; nothing is written to the Canonical Schema Registry in this round |

---

## 7. What this document does not decide

```text
Registry implementation and schema            → PACK-16D
Governed German texts                          → PACK-15 content-catalogue lineage
Audit-stream field definitions                  → PACK-16D
Mapping to participant-facing HTTP responses    → API-*, PACK-16D
```

**SPECIFIED. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY. NOT LEGALLY
ACTIVATED.**
