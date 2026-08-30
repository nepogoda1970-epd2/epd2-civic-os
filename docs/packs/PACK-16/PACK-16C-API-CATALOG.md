# PACK-16C — API Catalog

**Round:** PACK-16C — Casting, Receipt, Verification Client, Bulletin Board and Election Record. **Specification and ADR only. No code. No cryptographic implementation. Not implemented. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-101`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

**No endpoint is implemented in this round.** No route is added, no OpenAPI
document is modified, no contract test is written or changed. This is the
operation surface a later round must build, with its boundaries fixed now.

**CORRECTED.** The first PACK-16C candidate listed operations without
schemas, authorization, idempotency, rate-limit policy, timeout, retry or
failure semantics. **Every operation below now carries all sixteen required
fields.** Paths and schemas are **specification-level and concrete**; they
are not an implementation.

---

## 0. Reading rules

```text
PUBLIC        no authentication, no account, no terms, no cookies
CAPABILITY    requires a continuation capability, and nothing else
NONE OF THEM  requires an identity  <- this column is empty by design
```

| ID       | Rule                                                                                                                                                                                     |
| -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `API-01` | **No operation in this catalogue takes an identity, a credential, a session or a membership as input.** The casting side never learns who is voting (`SB-*`, `CC-04`)                    |
| `API-02` | **Every read operation on the board and the record is PUBLIC**, subject to the closure phase gate. Verification behind a login is not verification (`BB-36`, `IV-04`)                    |
| `API-03` | **No operation returns a count, a rate, an occupancy figure or a progress figure before the closure checkpoint** (`TC-07`). This is a property of the surface, not of a permission check |
| `API-04` | **There is no administrative operation that reads, alters, re-casts, excludes or deletes an individual ballot.** No such operation may be added in PACK-16D (`DP-03`)                    |

---

## 1. Privacy classification vocabulary — defined once

| Class                         | Meaning                                                                                                                                                                                                                 | Consequence                                                                                                                   |
| ----------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| **PUBLIC**                    | Served to anyone, at any time, with no authentication and no phase gate                                                                                                                                                 | Must work without JavaScript, without an account and without accepting terms (`API-33`, `XA-27`)                              |
| **PUBLIC_AFTER_CLOSURE**      | Served to anyone, but **only after the closure checkpoint**. Before it, the operation returns `not_yet_public` and **does not exist in any other sense** — it is not permission-gated and never returns an empty result | `API-32`; the phase gate is what makes turnout confidentiality a property of the surface (`EC-14`)                            |
| **ANONYMOUS-SENSITIVE**       | Served without identity, but the **request itself** is a correlation surface: a confirmation code, a capability or a retry token                                                                                        | Never logged by subject; strict rate limits; response shape and timing independent of the answer (`TC-39`, `API-30`)          |
| **RESTRICTED-ELECTION-ADMIN** | Served only to a named election-administration principal, and **never able to reach an individual ballot** (`API-04`)                                                                                                   | No operation in this catalogue carries this class; it is defined so that PACK-16D cannot introduce one without naming it      |
| **AUDITOR-RESTRICTED**        | Held by the Independent Auditor and **not served by any operation here**                                                                                                                                                | The restricted count comparison of `TC-52` is the only instance, and it is a comparison of two counts, never a join (`DM-10`) |

| ID       | Rule                                                                                                                                                                                      |
| -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `API-41` | **Every operation carries exactly one class.** A class is a property of the operation, not of the caller                                                                                  |
| `API-42` | **`PUBLIC_AFTER_CLOSURE` is not "PUBLIC with a permission check".** Before closure the underlying artefact does not exist (`API-52`, `API-53`), and the honest answer is `not_yet_public` |
| `API-43` | **No operation may be reclassified downward in PACK-16D.** Moving an operation from `PUBLIC_AFTER_CLOSURE` to `PUBLIC` would reopen the turnout channel this correction closed            |

---

## 2. Rate-limit policy — normative, without numbers

Concrete limits require a governance basis and a traffic model, neither of
which belongs in a specification round. **What the policy must achieve is
normative; the numbers are configuration bounds.**

| ID      | Policy                                                                                                                                                                                                                                                                        |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `RL-01` | **Confirmation-code enumeration must be infeasible.** The per-source and per-code limits on `API-18` and `API-20` must make bulk probing of the code space impractical at any realistic attacker budget                                                                       |
| `RL-02` | **Occupancy probing must be infeasible.** `API-18` and `API-20` share the confirmation-code surface and are limited **jointly**, not independently, so that an attacker cannot double their budget by alternating                                                             |
| `RL-03` | **Public download of the record must never be obstructed.** `API-24`, `API-26`, `API-50`, `API-52` and `API-53` are limited only against denial of service, and a complete independent download after closure must remain practical for an ordinary reader (`ER-13`, `IV-04`) |
| `RL-04` | **Board scraping must not become a timing oracle.** Limits on `API-21`…`API-25` must not vary with what is being fetched, because a limit that bites differently on different entry types is itself a signal                                                                  |
| `RL-05` | **Rate limiting must not distinguish outcomes.** A limited request and an absent-subject request are indistinguishable in shape and timing (`API-37`, `TC-39`)                                                                                                                |
| `RL-06` | **Limits are published configuration with normative bounds**, not undocumented operational values, and a change during an election is an incident (`FIR-CONFIG-001`)                                                                                                          |
| `RL-07` | **A detected probing pattern raises `privacy.turnout_oracle_detected` internally and is never returned to the caller** (`RN-16C-27`)                                                                                                                                          |
| `RL-08` | **The public-challenge entitlement is the primary anti-DoS bound, not the rate limit.** One capability yields at most one published challenge artefact (`CH-43`), so rate limiting handles burst and cost, not total volume                                                   |
| `RL-09` | **Rate limiting creates no identity linkage.** Limits are applied per source and per anonymous capability, and no limiter state may be joined to an identity, a credential or a ballot (`CN-36`, `PM-03`)                                                                     |
| `RL-10` | **No limiter response reveals capacity.** `rate_limited` and `challenge.public_reservation_unavailable` are distinct conditions, and neither carries a figure (`RN-16C-29`)                                                                                                   |

---

## 3. Failure semantics — the shared vocabulary

Every operation's **Failure semantics** field draws from this set. Defined
once so that no operation invents a synonym.

| Failure                              | Meaning                                                                                                                       |
| ------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------- |
| `invalid_request`                    | The request does not satisfy the operation's schema                                                                           |
| `unsupported_schema`                 | The caller's `schema_version` is not accepted by this deployment (`API-40`)                                                   |
| `unauthorized`                       | A capability or retry token was required and was absent, malformed or invalid                                                 |
| `not_yet_public`                     | The artefact exists in the election's future, not in the caller's permissions (`API-42`)                                      |
| `not_found_without_existence_oracle` | The subject was not found, answered so that presence and absence are indistinguishable to a caller probing at scale (`RL-05`) |
| `rate_limited`                       | The limit bit; shape and timing identical to `not_found_without_existence_oracle`                                             |
| `temporarily_unavailable`            | Infrastructure failure; the caller retries                                                                                    |
| `checkpoint_mismatch`                | The requested checkpoint does not cover the requested subject                                                                 |
| `proof_unavailable`                  | A proof cannot be produced for a subject that should have one — **an incident, not a normal answer**                          |
| `record_incomplete`                  | A mandatory artefact is absent; stated rather than silently omitted (`EC-*`)                                                  |
| `internal_fail_closed`               | Anything unexpected. **Nothing is consumed, nothing is published, nothing is repaired** (`VP-00`)                             |

| ID       | Rule                                                                                                                                                                                                                                                                                                                                                                                                  |
| -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `API-36` | **Every failure response is a reason code plus a governed German text.** No raw error, no stack trace, no exception message, no field dump (`VP-12`, `RN-16C-02`)                                                                                                                                                                                                                                     |
| `API-44` | **A privacy-sensitive lookup must not distinguish its answers in a way that permits bulk guessing of valid confirmation codes.** `not_found_without_existence_oracle` and `rate_limited` are indistinguishable to a caller measuring shape or time; a voter checking their own code once still receives the first-class `verification.code_not_found` outcome and its dispute path (`RE-08`, `DP-05`) |
| `API-45` | **`internal_fail_closed` never leaves partial state.** In particular it never consumes a capability, never publishes an entry and never emits a commitment                                                                                                                                                                                                                                            |

---

## 4. Operation profiles

Every operation carries all sixteen fields. **Paths are specification-level.**

---

### 4.1 Casting operations

#### `API-10` — Fetch election manifest

| Field                      | Value                                                                                                                                                              |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Operation ID**           | `API-10`                                                                                                                                                           |
| **Method and path**        | `GET /elections/{election_context_id}/manifest`                                                                                                                    |
| **Purpose**                | Return the signed election manifest a client must validate before preparing a ballot (`CF-*` step 2).                                                              |
| **Caller**                 | Voting client · Verification Client · any public reader                                                                                                            |
| **Authorization**          | **None.** No account, no session, no terms (`API-02`, `API-33`)                                                                                                    |
| **Request schema**         | `election_context_id`                                                                                                                                              |
| **Response schema**        | `manifest`, `manifest_digest`, `signer_id`, `signature`, `batch_cadence_profile`, `fixed_capacity_profile_id`, `schema_version`                                    |
| **Privacy classification** | PUBLIC                                                                                                                                                             |
| **Idempotency**            | **Yes** — pure read, no state                                                                                                                                      |
| **Rate-limit policy**      | Generous per-source ceiling; never so tight that a full public download is impractical (`RL-03`)                                                                   |
| **Reason codes**           | `manifest.unavailable`, `manifest.signature_invalid`, `manifest.signer_unknown`, `manifest.digest_mismatch`, `manifest.context_closed`                             |
| **Timeout semantics**      | Bounded; a timeout is a client-side observation, not a verdict                                                                                                     |
| **Retry semantics**        | Safe — idempotent read                                                                                                                                             |
| **Failure semantics**      | `not_yet_public` before the manifest is published; `temporarily_unavailable` on infrastructure failure; **fail closed** — a partial manifest is never returned     |
| **Audit evidence**         | Aggregate request counts only; no per-request record                                                                                                               |
| **Forbidden data**         | identity · credential ID · continuation capability · IP-derived identifier · exact acceptance timestamp · ballot choice · **batch occupancy count before closure** |

#### `API-11` — Fetch parameter set

| Field                      | Value                                                                                                                                                                  |
| -------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Operation ID**           | `API-11`                                                                                                                                                               |
| **Method and path**        | `GET /elections/{election_context_id}/parameters`                                                                                                                      |
| **Purpose**                | Return `EPD2-CRYPTO-1` and its provenance so a client and a verifier bind to identical bytes (`VP-*` stage 5).                                                         |
| **Caller**                 | Voting client · Verification Client · any verifier                                                                                                                     |
| **Authorization**          | **None**                                                                                                                                                               |
| **Request schema**         | `election_context_id`                                                                                                                                                  |
| **Response schema**        | `parameter_set_id`, `p`, `q`, `g`, `hash_spec`, encodings, domain-separation tags, `specification_digest`, approval record, **`VO-08` status: OPEN**, `schema_version` |
| **Privacy classification** | PUBLIC                                                                                                                                                                 |
| **Idempotency**            | **Yes**                                                                                                                                                                |
| **Rate-limit policy**      | As `API-10`                                                                                                                                                            |
| **Reason codes**           | `parameter_set.not_approved`, `parameter_set.digest_mismatch`, `parameter_set.deprecated`, `parameter_set.prohibited`                                                  |
| **Timeout semantics**      | Bounded                                                                                                                                                                |
| **Retry semantics**        | Safe                                                                                                                                                                   |
| **Failure semantics**      | **Fail closed.** A parameter set is returned whole and byte-identical or not at all                                                                                    |
| **Audit evidence**         | Aggregate counts only                                                                                                                                                  |
| **Forbidden data**         | identity · credential ID · continuation capability · IP-derived identifier · exact acceptance timestamp · ballot choice · **batch occupancy count before closure**     |

#### `API-12` — Fetch joint key and ceremony checkpoints

| Field                      | Value                                                                                                                                                                                                   |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Operation ID**           | `API-12`                                                                                                                                                                                                |
| **Method and path**        | `GET /elections/{election_context_id}/joint-key`                                                                                                                                                        |
| **Purpose**                | Return the joint public election key, the base-hash chain inputs and the ceremony checkpoints that bind them (`CF-*` step 5).                                                                           |
| **Caller**                 | Voting client · Verification Client · any verifier                                                                                                                                                      |
| **Authorization**          | **None**                                                                                                                                                                                                |
| **Request schema**         | `election_context_id`                                                                                                                                                                                   |
| **Response schema**        | `joint_public_key`, guardian public commitments, `k`, `n`, base-hash chain `ver → H_P → H_B → H_E → H_I`, ceremony checkpoint references, `schema_version`                                              |
| **Privacy classification** | PUBLIC                                                                                                                                                                                                  |
| **Idempotency**            | **Yes**                                                                                                                                                                                                 |
| **Rate-limit policy**      | As `API-10`                                                                                                                                                                                             |
| **Reason codes**           | `manifest.joint_key_mismatch`, `manifest.ceremony_checkpoint_missing`                                                                                                                                   |
| **Timeout semantics**      | Bounded                                                                                                                                                                                                 |
| **Retry semantics**        | Safe                                                                                                                                                                                                    |
| **Failure semantics**      | **Fail closed.** Never returns a key without its ceremony checkpoint                                                                                                                                    |
| **Audit evidence**         | Aggregate counts only                                                                                                                                                                                   |
| **Forbidden data**         | **Any guardian private share**, plus identity · credential ID · continuation capability · IP-derived identifier · exact acceptance timestamp · ballot choice · **batch occupancy count before closure** |

#### `API-13` — Fetch ballot style

| Field                      | Value                                                                                                                                                              |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Operation ID**           | `API-13`                                                                                                                                                           |
| **Method and path**        | `GET /elections/{election_context_id}/ballot-styles/{ballot_style_id}`                                                                                             |
| **Purpose**                | Return the contests, options, selection limits and placeholder rules a ballot is checked against (`VP-*` stage 8).                                                 |
| **Caller**                 | Voting client · Verification Client                                                                                                                                |
| **Authorization**          | **None**                                                                                                                                                           |
| **Request schema**         | `election_context_id`, `ballot_style_id`                                                                                                                           |
| **Response schema**        | `contests[]`, `options[]`, `selection_limit`, `option_limit`, `placeholder_rule`, `manifest_digest`, `schema_version`                                              |
| **Privacy classification** | PUBLIC                                                                                                                                                             |
| **Idempotency**            | **Yes**                                                                                                                                                            |
| **Rate-limit policy**      | As `API-10`                                                                                                                                                        |
| **Reason codes**           | `manifest.ballot_style_unknown`, `manifest.digest_mismatch`                                                                                                        |
| **Timeout semantics**      | Bounded                                                                                                                                                            |
| **Retry semantics**        | Safe                                                                                                                                                               |
| **Failure semantics**      | `not_found_without_existence_oracle` is **not** used here — ballot styles are public and enumerable by design                                                      |
| **Audit evidence**         | Aggregate counts only                                                                                                                                              |
| **Forbidden data**         | identity · credential ID · continuation capability · IP-derived identifier · exact acceptance timestamp · ballot choice · **batch occupancy count before closure** |

#### `API-14` — Probe continuation-capability validity

| Field                      | Value                                                                                                                                                                                                              |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Operation ID**           | `API-14`                                                                                                                                                                                                           |
| **Method and path**        | `POST /elections/{election_context_id}/capability/probe`                                                                                                                                                           |
| **Purpose**                | Tell a voter **before** they prepare a ballot whether their capability is usable. **Consumes nothing** (`CF-*` step 7, `API-05`).                                                                                  |
| **Caller**                 | Voting client                                                                                                                                                                                                      |
| **Authorization**          | **Continuation capability**, in the request body over an authenticated channel — never in a URL or query string (`API-09`)                                                                                         |
| **Request schema**         | `election_context_id`, `continuation_capability`                                                                                                                                                                   |
| **Response schema**        | `status` ∈ {`valid`, `invalid`, `already_spent`, `window_closed`}, `schema_version`                                                                                                                                |
| **Privacy classification** | ANONYMOUS-SENSITIVE                                                                                                                                                                                                |
| **Idempotency**            | **Yes — read-only.** Repeated probes are indistinguishable in effect from one probe                                                                                                                                |
| **Rate-limit policy**      | **Strict per-capability and per-source.** The probe is the natural capability-enumeration surface; **response timing must not distinguish outcomes** (`API-37`)                                                    |
| **Reason codes**           | `continuation.absent`, `continuation.malformed`, `continuation.invalid`, `continuation.already_spent`, `continuation.window_closed`                                                                                |
| **Timeout semantics**      | Short and bounded; a timeout leaves the capability untouched                                                                                                                                                       |
| **Retry semantics**        | Safe — nothing is consumed, so retry is free                                                                                                                                                                       |
| **Failure semantics**      | `rate_limited` on abuse; `internal_fail_closed` never consumes                                                                                                                                                     |
| **Audit evidence**         | Aggregate probe counts by outcome class, **after closure only** (`TC-07`)                                                                                                                                          |
| **Forbidden data**         | The capability itself in any log, URL or event; identity · credential ID · continuation capability · IP-derived identifier · exact acceptance timestamp · ballot choice · **batch occupancy count before closure** |

#### `API-15` — Submit ballot

| Field                      | Value                                                                                                                                                                                                                                                     |
| -------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Operation ID**           | `API-15`                                                                                                                                                                                                                                                  |
| **Method and path**        | `POST /elections/{election_context_id}/ballots`                                                                                                                                                                                                           |
| **Purpose**                | Carry an envelope through the 23-stage pipeline and, if every check passes, through the atomic acceptance boundary (`VP-*`).                                                                                                                              |
| **Caller**                 | Voting client                                                                                                                                                                                                                                             |
| **Authorization**          | **Continuation capability** in the request body; **no identity, no session, no account** (`API-01`)                                                                                                                                                       |
| **Request schema**         | `election_context_id`, `ballot_envelope` (`DM-01`), `continuation_capability`, `retry_token`, `protocol_profile_id`, `parameter_set_id`, `manifest_digest`, `schema_version`                                                                              |
| **Response schema**        | `status`, `confirmation_code`, `signed_publication_commitment` (naming `batch_window_id`), `board_checkpoint_reference`, `publication_status = ACCEPTED_PENDING_BATCH_COMMITMENT`, `schema_version`                                                       |
| **Privacy classification** | ANONYMOUS-SENSITIVE                                                                                                                                                                                                                                       |
| **Idempotency**            | **Yes, by `retry_token` and by nothing else.** Same token + identical envelope → the prior outcome; same token + different envelope → `submission.retry_token_conflict` (`API-06`)                                                                        |
| **Rate-limit policy**      | Per-capability and per-source; must not be so tight that a slow device cannot complete a legitimate submission (`XA-20`)                                                                                                                                  |
| **Reason codes**           | `submission.*`, `parameter_set.*`, `ballot_proof.*`, `ballot_preparation.style_shape_mismatch`, `continuation.*`, `acceptance.*`                                                                                                                          |
| **Timeout semantics**      | Bounded and published. **A timeout is a client-side observation, never a server verdict** (`RN-16C-16`) — the client's next step is `API-16`, not resubmission                                                                                            |
| **Retry semantics**        | **Only with the same `retry_token` and an identical envelope.** A retry with a different envelope is a rejection, never a second acceptance                                                                                                               |
| **Failure semantics**      | `internal_fail_closed` — a rollback inside the boundary consumes nothing (`FM-16C-14`); every rejection returns a distinct reason code plus governed German text and never a raw error (`API-36`)                                                         |
| **Audit evidence**         | Acceptance is an event (`EV-13`); **consumption is not** — it is an internal transactional state change recorded as privacy-restricted audit evidence carrying no capability reference (`EV-71`, `EV-74`, `EV-75`). No trace spans the boundary (`EV-06`) |
| **Forbidden data**         | Ballot content, board position, exact time, leaf index, batch occupancy; identity · credential ID · continuation capability · IP-derived identifier · exact acceptance timestamp · ballot choice · **batch occupancy count before closure**               |

#### `API-16` — Check submission status

| Field                      | Value                                                                                                                                                                                                 |
| -------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Operation ID**           | `API-16`                                                                                                                                                                                              |
| **Method and path**        | `GET /elections/{election_context_id}/submissions/{retry_token}`                                                                                                                                      |
| **Purpose**                | Let a client that lost the answer learn the committed outcome without resubmitting (`CN-26`).                                                                                                         |
| **Caller**                 | Voting client                                                                                                                                                                                         |
| **Authorization**          | **Retry token**, which is a bearer for this operation only and is stripped before publication (`BP-16`)                                                                                               |
| **Request schema**         | `election_context_id`, `retry_token`                                                                                                                                                                  |
| **Response schema**        | The prior outcome for that token, byte-identical on every call: `status`, `confirmation_code` if accepted, `signed_publication_commitment`, `publication_status`                                      |
| **Privacy classification** | ANONYMOUS-SENSITIVE                                                                                                                                                                                   |
| **Idempotency**            | **Yes, and non-mutating.** A status check is not a resubmission and spends nothing (`API-07`)                                                                                                         |
| **Rate-limit policy**      | Per-token and per-source                                                                                                                                                                              |
| **Reason codes**           | `submission.timeout`, `submission.retry_token_conflict`, `acceptance.committed`                                                                                                                       |
| **Timeout semantics**      | Bounded                                                                                                                                                                                               |
| **Retry semantics**        | Safe — pure read                                                                                                                                                                                      |
| **Failure semantics**      | `not_found_without_existence_oracle` for an unknown token: shape and timing identical to a known-but-pending token                                                                                    |
| **Audit evidence**         | Aggregate counts only                                                                                                                                                                                 |
| **Forbidden data**         | Anything about another submission; identity · credential ID · continuation capability · IP-derived identifier · exact acceptance timestamp · ballot choice · **batch occupancy count before closure** |

#### `API-17` — Submit a public evidentiary challenge

| Field                      | Value                                                                                                                                                                                                                                                                                                                     |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Operation ID**           | `API-17`                                                                                                                                                                                                                                                                                                                  |
| **Method and path**        | `POST /elections/{election_context_id}/public-challenges`                                                                                                                                                                                                                                                                 |
| **Purpose**                | Submit a challenged ballot with its opening as **public audit evidence**. Bounded to one per anonymous continuation capability in the initial profile (`CH-43`). **Never counted, never tally-eligible**                                                                                                                  |
| **Caller**                 | Voting client                                                                                                                                                                                                                                                                                                             |
| **Authorization**          | **Continuation capability** with `public_challenge_entitlement_available = true` — validated, and the **cast entitlement is never touched** (`CH-44`, `CN-33`)                                                                                                                                                            |
| **Request schema**         | `election_context_id`, `ballot_id`, `ciphertexts`, `proofs`, `confirmation_code`, `full_opening`, `continuation_capability`, `retry_token`, `schema_version`                                                                                                                                                              |
| **Response schema**        | `status`, `public_challenge_confirmation_reference`, `sealed_batch_reference`, `signed_publication_commitment`, `publication_status = ACCEPTED_PENDING_BATCH_COMMITMENT`, **`counted = false`**, `verification_instructions`, `schema_version`                                                                            |
| **Privacy classification** | ANONYMOUS-SENSITIVE                                                                                                                                                                                                                                                                                                       |
| **Idempotency**            | **Yes, by `retry_token`.** The same submission returns the same outcome; a **second, differing** public challenge fails closed with `challenge.public_entitlement_exhausted` (`CN-41`)                                                                                                                                    |
| **Rate-limit policy**      | Per-capability and per-source. The entitlement itself is the primary bound (`RL-08`); rate limiting is anti-DoS only and creates no identity linkage                                                                                                                                                                      |
| **Reason codes**           | `challenge.opening_incomplete`, `challenge.class_mismatch`, `challenge.reencryption_mismatch`, `challenge.public_entitlement_exhausted`, `challenge.public_reservation_unavailable`, `bulletin_board.batch_capacity_exhausted`                                                                                            |
| **Timeout semantics**      | Bounded. A timeout is a client-side observation; the client's next step is `API-54`, not resubmission                                                                                                                                                                                                                     |
| **Retry semantics**        | **Only with the same `retry_token` and an identical artefact.** A retry with a different artefact is `challenge.public_entitlement_exhausted`, never a second published challenge                                                                                                                                         |
| **Failure semantics**      | `unauthorized` if the entitlement is spent · `rate_limited` · `internal_fail_closed`. **A leaf slot is atomically reserved before durable acceptance** (`TC-70`, `CN-42`); if none is available the submission is rejected and **the entitlement is not spent** (`TC-82`). **A challenge never becomes a cast** (`BL-05`) |
| **Audit evidence**         | The spoiled artefact is an event (`EV-19`); **the entitlement transition is not** — it is an internal part of the atomic transaction, recorded as privacy-restricted audit evidence carrying no capability reference (`EV-71`, `EV-74`, `CN-36`)                                                                          |
| **Forbidden data**         | Any indication of how many public challenges have occurred · occupancy · remaining slots · the cast entitlement's state · identity · credential ID · continuation capability · IP-derived identifier · exact acceptance timestamp · **batch occupancy count before closure**                                              |

#### `API-18` — Fetch receipt

| Field                      | Value                                                                                                                                                                                                                                                                                                       |
| -------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Operation ID**           | `API-18`                                                                                                                                                                                                                                                                                                    |
| **Method and path**        | `GET /elections/{election_context_id}/receipts/{confirmation_code}`                                                                                                                                                                                                                                         |
| **Purpose**                | Re-derive a receipt from public data so that losing it costs nothing (`RE-04`).                                                                                                                                                                                                                             |
| **Caller**                 | Voter · Verification Client                                                                                                                                                                                                                                                                                 |
| **Authorization**          | **None beyond possession of the confirmation code** (`API-08`)                                                                                                                                                                                                                                              |
| **Request schema**         | `election_context_id`, `confirmation_code`                                                                                                                                                                                                                                                                  |
| **Response schema**        | `election_context_reference`, `confirmation_code`, `sealed_batch_reference`, `board_checkpoint_reference`, `publication_status`, `verification_instructions`, `receipt_schema_version`                                                                                                                      |
| **Privacy classification** | ANONYMOUS-SENSITIVE                                                                                                                                                                                                                                                                                         |
| **Idempotency**            | **Yes**                                                                                                                                                                                                                                                                                                     |
| **Rate-limit policy**      | **Strict per-source**, because this operation and `API-20` share the confirmation-code surface (`RL-02`)                                                                                                                                                                                                    |
| **Reason codes**           | `verification.code_not_found`, `receipt.generation_failed`                                                                                                                                                                                                                                                  |
| **Timeout semantics**      | Bounded                                                                                                                                                                                                                                                                                                     |
| **Retry semantics**        | Safe                                                                                                                                                                                                                                                                                                        |
| **Failure semantics**      | `not_found_without_existence_oracle`: an absent code and a rate-limited request are indistinguishable in shape and timing to a caller probing at scale, while a voter who checks their own code once receives the first-class `verification.code_not_found` outcome and its dispute path (`RE-08`, `DP-05`) |
| **Audit evidence**         | **Nothing.** Receipt fetches are not logged by subject (`PM-*` #27)                                                                                                                                                                                                                                         |
| **Forbidden data**         | Leaf index, batch occupancy, board sequence, position among real ballots; identity · credential ID · continuation capability · IP-derived identifier · exact acceptance timestamp · ballot choice · **batch occupancy count before closure**                                                                |

---

### 4.2 Verification and board operations

#### `API-20` — Look up a confirmation code and obtain its commitment inclusion proof

| Field                      | Value                                                                                                                                                                                                                                                              |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Operation ID**           | `API-20`                                                                                                                                                                                                                                                           |
| **Method and path**        | `GET /elections/{election_context_id}/confirmations/{confirmation_code}`                                                                                                                                                                                           |
| **Purpose**                | **Corrected.** The voter's `recorded-as-cast` check. Before closure it returns a **privacy-safe commitment inclusion proof** (`TC-36`…`TC-40`); after closure it also resolves to the opened ballot artefact.                                                      |
| **Caller**                 | Voter · Verification Client · any holder of the code                                                                                                                                                                                                               |
| **Authorization**          | **None beyond possession of the confirmation code.** No identity, no credential, no capability, no account, no terms (`TC-36`)                                                                                                                                     |
| **Request schema**         | `election_context_id`, `confirmation_code`, optional `requested_checkpoint`, optional `verifier_nonce`                                                                                                                                                             |
| **Response schema**        | `status`, `batch_sequence`, `commitment_root`, `leaf_opening` (**the caller's own leaf only**), `inclusion_proof` (sibling hashes), `signed_checkpoint`, `publication_phase` ∈ {`COMMITTED`, `PUBLISHED_AFTER_CLOSURE`}, `schema_version`                          |
| **Privacy classification** | ANONYMOUS-SENSITIVE                                                                                                                                                                                                                                                |
| **Idempotency**            | **Yes.** Repeated lookups of the same code return the same proof against the same checkpoint                                                                                                                                                                       |
| **Rate-limit policy**      | **The strictest policy in the catalogue.** Per-source and per-code. Must defeat confirmation-code enumeration and occupancy probing (`RL-01`, `T-P16C-42`)                                                                                                         |
| **Reason codes**           | `verification.code_not_found`, `verification.batch_inclusion_failed`, `verification.batch_consistency_failed`                                                                                                                                                      |
| **Timeout semantics**      | Bounded                                                                                                                                                                                                                                                            |
| **Retry semantics**        | Safe — pure read                                                                                                                                                                                                                                                   |
| **Failure semantics**      | `not_found_without_existence_oracle`, `rate_limited`, `checkpoint_mismatch`, `proof_unavailable`. **Response shape and timing are independent of presence** (`TC-39`)                                                                                              |
| **Audit evidence**         | **None by subject.** No confirmation code, no result, no correlation with a request address is recorded (`API-30`, `EV-63`). A detected probing pattern raises `privacy.turnout_oracle_detected` internally and is **never returned to the caller** (`RN-16C-27`)  |
| **Forbidden data**         | Any other occupant's leaf opening · the leaf index · batch occupancy · a count of real leaves · identity · credential ID · continuation capability · IP-derived identifier · exact acceptance timestamp · ballot choice · **batch occupancy count before closure** |

#### `API-21` — Fetch board inclusion proof

| Field                      | Value                                                                                                                                                              |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Operation ID**           | `API-21`                                                                                                                                                           |
| **Method and path**        | `GET /elections/{election_context_id}/board/entries/{board_sequence}/inclusion`                                                                                    |
| **Purpose**                | Prove that a **board entry** is included in a named checkpoint's tree (`AO-06`).                                                                                   |
| **Caller**                 | Any verifier                                                                                                                                                       |
| **Authorization**          | **None**                                                                                                                                                           |
| **Request schema**         | `election_context_id`, `board_sequence`, `checkpoint_reference`                                                                                                    |
| **Response schema**        | `inclusion_proof`, `checkpoint_reference`, `tree_size`, `schema_version`                                                                                           |
| **Privacy classification** | PUBLIC                                                                                                                                                             |
| **Idempotency**            | **Yes**                                                                                                                                                            |
| **Rate-limit policy**      | Generous; must not obstruct full-record download (`RL-03`)                                                                                                         |
| **Reason codes**           | `verification.batch_consistency_failed`                                                                                                                            |
| **Timeout semantics**      | Bounded                                                                                                                                                            |
| **Retry semantics**        | Safe                                                                                                                                                               |
| **Failure semantics**      | `proof_unavailable`, `checkpoint_mismatch`. **The proof material is recomputable from `API-24`** so the caller need not trust this response (`API-31`)             |
| **Audit evidence**         | Aggregate counts only                                                                                                                                              |
| **Forbidden data**         | identity · credential ID · continuation capability · IP-derived identifier · exact acceptance timestamp · ballot choice · **batch occupancy count before closure** |

#### `API-22` — Fetch board consistency proof

| Field                      | Value                                                                                                                                                              |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Operation ID**           | `API-22`                                                                                                                                                           |
| **Method and path**        | `GET /elections/{election_context_id}/board/consistency`                                                                                                           |
| **Purpose**                | Prove that a later checkpoint's tree is an append-only extension of an earlier one (`AO-07`).                                                                      |
| **Caller**                 | Any verifier                                                                                                                                                       |
| **Authorization**          | **None**                                                                                                                                                           |
| **Request schema**         | `election_context_id`, `from_checkpoint`, `to_checkpoint`                                                                                                          |
| **Response schema**        | `consistency_proof`, both checkpoint references, both tree sizes, `schema_version`                                                                                 |
| **Privacy classification** | PUBLIC                                                                                                                                                             |
| **Idempotency**            | **Yes**                                                                                                                                                            |
| **Rate-limit policy**      | As `API-21`                                                                                                                                                        |
| **Reason codes**           | `verification.batch_consistency_failed`                                                                                                                            |
| **Timeout semantics**      | Bounded                                                                                                                                                            |
| **Retry semantics**        | Safe                                                                                                                                                               |
| **Failure semantics**      | `proof_unavailable`, `checkpoint_mismatch`                                                                                                                         |
| **Audit evidence**         | Aggregate counts only                                                                                                                                              |
| **Forbidden data**         | identity · credential ID · continuation capability · IP-derived identifier · exact acceptance timestamp · ballot choice · **batch occupancy count before closure** |

#### `API-23` — Fetch latest checkpoint

| Field                      | Value                                                                                                                                                              |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Operation ID**           | `API-23`                                                                                                                                                           |
| **Method and path**        | `GET /elections/{election_context_id}/board/checkpoints/latest`                                                                                                    |
| **Purpose**                | Return the current signed, chained checkpoint with its mirror co-signatures (`AO-04`, `AO-09`).                                                                    |
| **Caller**                 | Any reader · every mirror · the Independent Auditor                                                                                                                |
| **Authorization**          | **None**                                                                                                                                                           |
| **Request schema**         | `election_context_id`                                                                                                                                              |
| **Response schema**        | `checkpoint`: `tree_size`, `root`, `previous_checkpoint_hash`, `sequence`, `signer_id`, `signature`, `cosignatures[]`, coarsened timestamp, `schema_version`       |
| **Privacy classification** | PUBLIC                                                                                                                                                             |
| **Idempotency**            | **Yes**                                                                                                                                                            |
| **Rate-limit policy**      | Generous — checkpoint gossip depends on frequent public fetching (`AO-10`)                                                                                         |
| **Reason codes**           | `bulletin_board.batch_root_mismatch`                                                                                                                               |
| **Timeout semantics**      | Bounded                                                                                                                                                            |
| **Retry semantics**        | Safe                                                                                                                                                               |
| **Failure semantics**      | `temporarily_unavailable`. **A checkpoint is never returned unsigned or unchained**                                                                                |
| **Audit evidence**         | Published gossip capture is itself public (`AO-11`)                                                                                                                |
| **Forbidden data**         | identity · credential ID · continuation capability · IP-derived identifier · exact acceptance timestamp · ballot choice · **batch occupancy count before closure** |

#### `API-24` — Fetch board entries in bulk

| Field                      | Value                                                                                                                                                                                            |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Operation ID**           | `API-24`                                                                                                                                                                                         |
| **Method and path**        | `GET /elections/{election_context_id}/board/entries?from=&to=`                                                                                                                                   |
| **Purpose**                | Let anyone download the board and recompute every proof offline (`ER-13`, `API-31`).                                                                                                             |
| **Caller**                 | Any reader · mirrors · archives                                                                                                                                                                  |
| **Authorization**          | **None**                                                                                                                                                                                         |
| **Request schema**         | `election_context_id`, `from`, `to`                                                                                                                                                              |
| **Response schema**        | `entries[]` with `entry_type`, `board_sequence`, `content_digest`, payload, `previous_checkpoint_reference`; `schema_version`                                                                    |
| **Privacy classification** | **PUBLIC** for `BE-01`…`BE-04`, `BE-09`, `BE-17`, `BE-24`; **PUBLIC_AFTER_CLOSURE** for every other entry type (`BE-28`)                                                                         |
| **Idempotency**            | **Yes**                                                                                                                                                                                          |
| **Rate-limit policy**      | Generous and explicitly sized for full download; **pagination must not make a complete fetch impractical** (`ER-13`, `RL-03`)                                                                    |
| **Reason codes**           | `election_record.batch_artifact_missing`                                                                                                                                                         |
| **Timeout semantics**      | Bounded; large ranges may stream                                                                                                                                                                 |
| **Retry semantics**        | Safe                                                                                                                                                                                             |
| **Failure semantics**      | `not_yet_public` for a post-closure entry type requested before closure — **a distinct, honest answer, never an empty list**, because an empty list would be an occupancy signal                 |
| **Audit evidence**         | Aggregate counts only                                                                                                                                                                            |
| **Forbidden data**         | Any pre-closure ballot entry; identity · credential ID · continuation capability · IP-derived identifier · exact acceptance timestamp · ballot choice · **batch occupancy count before closure** |

#### `API-25` — Fetch checkpoint history

| Field                      | Value                                                                                                                                                              |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Operation ID**           | `API-25`                                                                                                                                                           |
| **Method and path**        | `GET /elections/{election_context_id}/board/checkpoints`                                                                                                           |
| **Purpose**                | Return the full chain with signer identities and their publication history, so a key rotation cannot pass as a substitution (`ER-*` artefact 26).                  |
| **Caller**                 | Any verifier                                                                                                                                                       |
| **Authorization**          | **None**                                                                                                                                                           |
| **Request schema**         | `election_context_id`, optional range                                                                                                                              |
| **Response schema**        | `checkpoints[]`, `signing_keys[]` with validity windows and publication events, `schema_version`                                                                   |
| **Privacy classification** | PUBLIC                                                                                                                                                             |
| **Idempotency**            | **Yes**                                                                                                                                                            |
| **Rate-limit policy**      | As `API-24`                                                                                                                                                        |
| **Reason codes**           | `bulletin_board.batch_root_mismatch`                                                                                                                               |
| **Timeout semantics**      | Bounded                                                                                                                                                            |
| **Retry semantics**        | Safe                                                                                                                                                               |
| **Failure semantics**      | `temporarily_unavailable`; **never a truncated chain without saying so**                                                                                           |
| **Audit evidence**         | Aggregate counts only                                                                                                                                              |
| **Forbidden data**         | identity · credential ID · continuation capability · IP-derived identifier · exact acceptance timestamp · ballot choice · **batch occupancy count before closure** |

#### `API-26` — Fetch the election record

| Field                      | Value                                                                                                                                                              |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Operation ID**           | `API-26`                                                                                                                                                           |
| **Method and path**        | `GET /elections/{election_context_id}/record`                                                                                                                      |
| **Purpose**                | Return the complete record — all 37 mandatory artefacts — as files, with its manifest and digest (`ER-*`).                                                         |
| **Caller**                 | Anyone, including after EPD² ceases to exist                                                                                                                       |
| **Authorization**          | **None**                                                                                                                                                           |
| **Request schema**         | `election_context_id`                                                                                                                                              |
| **Response schema**        | The record bundle, `record_manifest`, `record_manifest_digest`, `schema_version`                                                                                   |
| **Privacy classification** | **PUBLIC** for pre-closure artefacts; **PUBLIC_AFTER_CLOSURE** for the record as a whole                                                                           |
| **Idempotency**            | **Yes** — and byte-identical across mirrors (`ER-14`)                                                                                                              |
| **Rate-limit policy**      | **Deliberately permissive.** Rate limiting must never obstruct independent public download after closure (`RL-03`)                                                 |
| **Reason codes**           | `election_record.batch_artifact_missing`                                                                                                                           |
| **Timeout semantics**      | Generous; streaming permitted                                                                                                                                      |
| **Retry semantics**        | Safe                                                                                                                                                               |
| **Failure semantics**      | `not_yet_public` before closure; `record_incomplete` where a mandatory artefact is absent — **stated, never silently omitted**                                     |
| **Audit evidence**         | Aggregate counts only                                                                                                                                              |
| **Forbidden data**         | identity · credential ID · continuation capability · IP-derived identifier · exact acceptance timestamp · ballot choice · **batch occupancy count before closure** |

#### `API-27` — Fetch client build metadata

| Field                      | Value                                                                                                                                                              |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Operation ID**           | `API-27`                                                                                                                                                           |
| **Method and path**        | `GET /clients/{client_id}/build`                                                                                                                                   |
| **Purpose**                | Publish the build digest, source reference and reproducible-build attestation for the voting and verification clients (`IV-07`…`IV-10`).                           |
| **Caller**                 | Any reader · the voting client itself                                                                                                                              |
| **Authorization**          | **None**                                                                                                                                                           |
| **Request schema**         | `client_id`, optional `version`                                                                                                                                    |
| **Response schema**        | `build_digest`, `source_reference`, `attestation`, `release_signature`, `published_at` (coarsened), `schema_version`                                               |
| **Privacy classification** | PUBLIC                                                                                                                                                             |
| **Idempotency**            | **Yes**                                                                                                                                                            |
| **Rate-limit policy**      | Generous                                                                                                                                                           |
| **Reason codes**           | `manifest.client_build_mismatch`                                                                                                                                   |
| **Timeout semantics**      | Bounded                                                                                                                                                            |
| **Retry semantics**        | Safe                                                                                                                                                               |
| **Failure semantics**      | `temporarily_unavailable`. A mismatch against the served build is `FM-16C-01`, **not** a silent update                                                             |
| **Audit evidence**         | Aggregate counts only                                                                                                                                              |
| **Forbidden data**         | identity · credential ID · continuation capability · IP-derived identifier · exact acceptance timestamp · ballot choice · **batch occupancy count before closure** |

#### `API-28` — Fetch published failure notices

| Field                      | Value                                                                                                                                                                                                                                    |
| -------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Operation ID**           | `API-28`                                                                                                                                                                                                                                 |
| **Method and path**        | `GET /elections/{election_context_id}/incidents`                                                                                                                                                                                         |
| **Purpose**                | Return every published incident, publication dispute and correction (`ER-*` artefact 29).                                                                                                                                                |
| **Caller**                 | Any reader                                                                                                                                                                                                                               |
| **Authorization**          | **None**                                                                                                                                                                                                                                 |
| **Request schema**         | `election_context_id`, optional range                                                                                                                                                                                                    |
| **Response schema**        | `notices[]` with class, reason code, affected scope, coarsened time, remedy state, `schema_version`                                                                                                                                      |
| **Privacy classification** | PUBLIC                                                                                                                                                                                                                                   |
| **Idempotency**            | **Yes**                                                                                                                                                                                                                                  |
| **Rate-limit policy**      | Generous                                                                                                                                                                                                                                 |
| **Reason codes**           | `publication.*`, `bulletin_board.*`                                                                                                                                                                                                      |
| **Timeout semantics**      | Bounded                                                                                                                                                                                                                                  |
| **Retry semantics**        | Safe                                                                                                                                                                                                                                     |
| **Failure semantics**      | `temporarily_unavailable`. **A notice is published as it occurs and is never held pending review** (`EV-08`)                                                                                                                             |
| **Audit evidence**         | The notices are themselves the audit evidence                                                                                                                                                                                            |
| **Forbidden data**         | **Any count of affected ballots before closure** (`PA-05`, `FMR-16`); identity · credential ID · continuation capability · IP-derived identifier · exact acceptance timestamp · ballot choice · **batch occupancy count before closure** |

#### `API-29` — Fetch post-closure aggregates

| Field                      | Value                                                                                                                                                                                                                                                  |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Operation ID**           | `API-29`                                                                                                                                                                                                                                               |
| **Method and path**        | `GET /elections/{election_context_id}/aggregates`                                                                                                                                                                                                      |
| **Purpose**                | Return turnout, rejection counts by class, challenge ratio and the count reconciliation — **after the closure checkpoint and not before** (`TC-14`).                                                                                                   |
| **Caller**                 | Any reader                                                                                                                                                                                                                                             |
| **Authorization**          | **None**                                                                                                                                                                                                                                               |
| **Request schema**         | `election_context_id`                                                                                                                                                                                                                                  |
| **Response schema**        | `turnout`, `rejection_counts_by_class[]`, `challenge_ratio`, `count_reconciliation`, `suppression_notices[]`, `schema_version`                                                                                                                         |
| **Privacy classification** | **PUBLIC_AFTER_CLOSURE**                                                                                                                                                                                                                               |
| **Idempotency**            | **Yes**                                                                                                                                                                                                                                                |
| **Rate-limit policy**      | Generous, after closure                                                                                                                                                                                                                                |
| **Reason codes**           | `election.closed`                                                                                                                                                                                                                                      |
| **Timeout semantics**      | Bounded                                                                                                                                                                                                                                                |
| **Retry semantics**        | Safe                                                                                                                                                                                                                                                   |
| **Failure semantics**      | `not_yet_public` before closure — **the operation does not exist rather than returning an empty or permission-denied answer** (`API-32`). A figure suppressed under `TC-17` is returned **as suppressed, with the threshold**, never omitted (`TC-19`) |
| **Audit evidence**         | Aggregate counts only                                                                                                                                                                                                                                  |
| **Forbidden data**         | Any pre-closure figure; identity · credential ID · continuation capability · IP-derived identifier · exact acceptance timestamp · ballot choice · **batch occupancy count before closure**                                                             |

---

### 4.2a Client-local operations — no network API

#### `API-19` — Local diagnostic challenge

| Field                      | Value                                                                                                                                                                               |
| -------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Operation ID**           | `API-19`                                                                                                                                                                            |
| **Method and path**        | **NO NETWORK API — CLIENT-LOCAL OPERATION.** There is no route, no request and no response. It is catalogued so that its absence from the network surface is explicit and checkable |
| **Purpose**                | Let a voter verify, **locally and without limit**, that this device encrypted what they chose (`CH-39`…`CH-42`)                                                                     |
| **Caller**                 | The voter, inside the Voting Client                                                                                                                                                 |
| **Authorization**          | **None — nothing leaves the device.** No capability is presented and none is spent                                                                                                  |
| **Request schema**         | — none. The client reveals its own locally held nonces and re-encrypts                                                                                                              |
| **Response schema**        | — none over the network. On screen: what was checked, the result, and that this local ballot must now be discarded                                                                  |
| **Privacy classification** | **Not applicable — no data leaves the client.** It is neither PUBLIC nor ANONYMOUS-SENSITIVE, because there is no request                                                           |
| **Idempotency**            | **Not applicable** — no server state exists to be idempotent about (`CN-34`)                                                                                                        |
| **Rate-limit policy**      | **None, and none may be added.** Rate-limiting a local check would be a limit on how hard a voter may examine their own device (`CH-18`)                                            |
| **Reason codes**           | **None.** `challenge.local_completed` is a client-local outcome, not a reason code (`RN-16C-35`)                                                                                    |
| **Timeout semantics**      | Local computation only                                                                                                                                                              |
| **Retry semantics**        | **Unlimited**, with a fresh ballot and fresh randomness each time (`CH-47`)                                                                                                         |
| **Failure semantics**      | Displayed locally. A mismatch is the strongest local signal a voter can obtain and routes them to the **public audit challenge** and to independent verification (`CH-41`)          |
| **Audit evidence**         | **None, anywhere.** No board entry, no record artefact, no event, no telemetry (`CH-42`, `TC-58`, `ER-30`)                                                                          |
| **Forbidden data**         | **Everything** — nothing may be transmitted. Emitting a local-challenge signal as telemetry is prohibited (`EV-70`)                                                                 |

---

### 4.3 Sealed batch operations — added by the turnout correction

#### `API-50` — Fetch a public batch commitment

| Field                      | Value                                                                                                                                                                                                                                                                                                            |
| -------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Operation ID**           | `API-50`                                                                                                                                                                                                                                                                                                         |
| **Method and path**        | `GET /elections/{election_context_id}/batches/{batch_sequence}/commitment`                                                                                                                                                                                                                                       |
| **Purpose**                | Return one `sealed_batch_commitment` entry — the only per-window publication before closure (`BE-24`, `TC-33`).                                                                                                                                                                                                  |
| **Caller**                 | Any reader · mirrors · verifiers                                                                                                                                                                                                                                                                                 |
| **Authorization**          | **None**                                                                                                                                                                                                                                                                                                         |
| **Request schema**         | `election_context_id`, `batch_sequence`                                                                                                                                                                                                                                                                          |
| **Response schema**        | `election_context_id`, `batch_sequence`, `batch_window_id`, `fixed_capacity_profile_id`, `commitment_root`, `previous_checkpoint_reference`, `signature`, `schema_version`                                                                                                                                       |
| **Privacy classification** | PUBLIC                                                                                                                                                                                                                                                                                                           |
| **Idempotency**            | **Yes**                                                                                                                                                                                                                                                                                                          |
| **Rate-limit policy**      | Generous — every reader is expected to fetch every window (`RL-03`)                                                                                                                                                                                                                                              |
| **Reason codes**           | `bulletin_board.batch_commitment_missing`, `bulletin_board.batch_commitment_late`                                                                                                                                                                                                                                |
| **Timeout semantics**      | Bounded                                                                                                                                                                                                                                                                                                          |
| **Retry semantics**        | Safe                                                                                                                                                                                                                                                                                                             |
| **Failure semantics**      | `not_found_without_existence_oracle` is **not** used: a window either has a commitment or its absence is a published failure (`FM-16C-18`). `not_yet_public` for a window whose scheduled time has not arrived                                                                                                   |
| **Audit evidence**         | Aggregate counts only                                                                                                                                                                                                                                                                                            |
| **Forbidden data**         | **Real ballot count · leaf occupancy bitmap · any individual ballot hash · confirmation code · acceptance timestamp · capability reference**; identity · credential ID · continuation capability · IP-derived identifier · exact acceptance timestamp · ballot choice · **batch occupancy count before closure** |

#### `API-51` — Fetch a sealed batch checkpoint

| Field                      | Value                                                                                                                                                                            |
| -------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Operation ID**           | `API-51`                                                                                                                                                                         |
| **Method and path**        | `GET /elections/{election_context_id}/batches/{batch_sequence}/checkpoint`                                                                                                       |
| **Purpose**                | Return the signed board checkpoint that covers a given batch commitment, with mirror co-signatures, so a voter's inclusion proof anchors to something signed (`TC-35`, `AO-16`). |
| **Caller**                 | Voter · Verification Client · any verifier                                                                                                                                       |
| **Authorization**          | **None**                                                                                                                                                                         |
| **Request schema**         | `election_context_id`, `batch_sequence`                                                                                                                                          |
| **Response schema**        | `checkpoint`, `covers_batch_sequence`, `cosignatures[]`, `schema_version`                                                                                                        |
| **Privacy classification** | PUBLIC                                                                                                                                                                           |
| **Idempotency**            | **Yes**                                                                                                                                                                          |
| **Rate-limit policy**      | Generous                                                                                                                                                                         |
| **Reason codes**           | `verification.batch_consistency_failed`, `bulletin_board.batch_root_mismatch`                                                                                                    |
| **Timeout semantics**      | Bounded                                                                                                                                                                          |
| **Retry semantics**        | Safe                                                                                                                                                                             |
| **Failure semantics**      | `checkpoint_mismatch` where the requested batch is not yet covered; **never a checkpoint without its chain link**                                                                |
| **Audit evidence**         | Public gossip capture (`AO-11`)                                                                                                                                                  |
| **Forbidden data**         | identity · credential ID · continuation capability · IP-derived identifier · exact acceptance timestamp · ballot choice · **batch occupancy count before closure**               |

#### `API-52` — Fetch a batch opening

| Field                      | Value                                                                                                                                                                                                                                                                                |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Operation ID**           | `API-52`                                                                                                                                                                                                                                                                             |
| **Method and path**        | `GET /elections/{election_context_id}/batches/{batch_sequence}/opening`                                                                                                                                                                                                              |
| **Purpose**                | **After closure only.** Return the complete `sealed_batch_opening`: every leaf's opening in index order, real and cover, with the leaf-index → artefact mapping and each leaf's declared class (`BE-25`, `TC-41`, `TC-45`).                                                          |
| **Caller**                 | Any verifier                                                                                                                                                                                                                                                                         |
| **Authorization**          | **None**                                                                                                                                                                                                                                                                             |
| **Request schema**         | `election_context_id`, `batch_sequence`                                                                                                                                                                                                                                              |
| **Response schema**        | `batch_sequence`, `leaves[]` each with `leaf_index`, `class` ∈ {`accepted`, `spoiled`, `cover`}, `opening`, and for real leaves the `salt` and committed fields; `recomputed_root`; `schema_version`                                                                                 |
| **Privacy classification** | **PUBLIC_AFTER_CLOSURE**                                                                                                                                                                                                                                                             |
| **Idempotency**            | **Yes**                                                                                                                                                                                                                                                                              |
| **Rate-limit policy**      | Generous — full download is the point                                                                                                                                                                                                                                                |
| **Reason codes**           | `bulletin_board.batch_opening_missing`, `bulletin_board.batch_opening_invalid`, `bulletin_board.duplicate_leaf_opening`, `bulletin_board.cover_leaf_invalid`                                                                                                                         |
| **Timeout semantics**      | Generous; streaming permitted                                                                                                                                                                                                                                                        |
| **Retry semantics**        | Safe                                                                                                                                                                                                                                                                                 |
| **Failure semantics**      | `not_yet_public` before closure — **this is the operation that makes occupancy public, and it does not exist before the closure checkpoint** (`EC-14`). **Partial openings are prohibited**: the response is complete or the record is incomplete (`TC-45`)                          |
| **Audit evidence**         | The opening is itself public evidence                                                                                                                                                                                                                                                |
| **Forbidden data**         | **Any nonce or plaintext of an accepted ballot** (a spoiled ballot's opening is published by design); capability; identity · credential ID · continuation capability · IP-derived identifier · exact acceptance timestamp · ballot choice · **batch occupancy count before closure** |

#### `API-53` — Fetch the batch reconciliation record

| Field                      | Value                                                                                                                                                                                                                                                                                           |
| -------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Operation ID**           | `API-53`                                                                                                                                                                                                                                                                                        |
| **Method and path**        | `GET /elections/{election_context_id}/batches/reconciliation`                                                                                                                                                                                                                                   |
| **Purpose**                | **After closure only.** Return occupancy by class per batch, per-batch and global totals, the mapping to accepted-ballot artefacts, the recomputed roots and the per-batch verification result (`BE-26`, `TC-42`, `TC-43`).                                                                     |
| **Caller**                 | Any verifier · the Independent Auditor                                                                                                                                                                                                                                                          |
| **Authorization**          | **None** for the public record; the restricted count comparison of `TC-52` is **AUDITOR-RESTRICTED and is not served by this operation**                                                                                                                                                        |
| **Request schema**         | `election_context_id`                                                                                                                                                                                                                                                                           |
| **Response schema**        | `batches[]` with `batch_sequence`, `accepted_count`, `spoiled_count`, `cover_count`, `recomputed_root`, `verification_result`; `global_totals`; `artifact_mapping`; `schema_version`                                                                                                            |
| **Privacy classification** | **PUBLIC_AFTER_CLOSURE**                                                                                                                                                                                                                                                                        |
| **Idempotency**            | **Yes**                                                                                                                                                                                                                                                                                         |
| **Rate-limit policy**      | Generous                                                                                                                                                                                                                                                                                        |
| **Reason codes**           | `bulletin_board.batch_reconciliation_failed`, `bulletin_board.late_insertion_detected`, `election_record.batch_artifact_missing`                                                                                                                                                                |
| **Timeout semantics**      | Bounded                                                                                                                                                                                                                                                                                         |
| **Retry semantics**        | Safe                                                                                                                                                                                                                                                                                            |
| **Failure semantics**      | `not_yet_public` before closure; `record_incomplete` where any batch is unaccounted for (`TC-44`)                                                                                                                                                                                               |
| **Audit evidence**         | The record is itself public evidence; the Auditor's count comparison is held separately and never published (`TC-52`)                                                                                                                                                                           |
| **Forbidden data**         | **Any pairing of a ballot with a capability** — the reconciliation maps public artefacts to public artefacts only (`DM-10`); identity · credential ID · continuation capability · IP-derived identifier · exact acceptance timestamp · ballot choice · **batch occupancy count before closure** |

#### `API-54` — Fetch public-challenge publication status

| Field                      | Value                                                                                                                                                                                                                                                  |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Operation ID**           | `API-54`                                                                                                                                                                                                                                               |
| **Method and path**        | `GET /elections/{election_context_id}/public-challenges/{public_challenge_confirmation_reference}`                                                                                                                                                     |
| **Purpose**                | Let the submitter of a public evidentiary challenge check that its leaf is committed in the named window, and after closure that its opening is published (`PA-15`)                                                                                    |
| **Caller**                 | The submitter · Verification Client                                                                                                                                                                                                                    |
| **Authorization**          | **None beyond possession of the public-challenge confirmation reference**                                                                                                                                                                              |
| **Request schema**         | `election_context_id`, `public_challenge_confirmation_reference`, optional `requested_checkpoint`                                                                                                                                                      |
| **Response schema**        | `status`, `batch_sequence`, `commitment_root`, own `leaf_opening`, `inclusion_proof`, `signed_checkpoint`, `publication_phase`, **`counted = false`**, `schema_version`                                                                                |
| **Privacy classification** | ANONYMOUS-SENSITIVE                                                                                                                                                                                                                                    |
| **Idempotency**            | **Yes**                                                                                                                                                                                                                                                |
| **Rate-limit policy**      | As `API-20`, and **jointly with it** — both share the confirmation-reference surface (`RL-02`)                                                                                                                                                         |
| **Reason codes**           | `verification.code_not_found`, `verification.batch_inclusion_failed`, `verification.batch_consistency_failed`                                                                                                                                          |
| **Timeout semantics**      | Bounded                                                                                                                                                                                                                                                |
| **Retry semantics**        | Safe — pure read                                                                                                                                                                                                                                       |
| **Failure semantics**      | `not_found_without_existence_oracle`, `rate_limited`, `checkpoint_mismatch`. **Response shape and timing independent of presence** (`TC-39`)                                                                                                           |
| **Audit evidence**         | **None by subject** (`API-30`)                                                                                                                                                                                                                         |
| **Forbidden data**         | Whether the submitter later cast a ballot · the cast entitlement's state · occupancy · leaf index · identity · credential ID · continuation capability · IP-derived identifier · exact acceptance timestamp · **batch occupancy count before closure** |

#### `API-55` — Fetch election capacity incident status

| Field                      | Value                                                                                                                                                                              |
| -------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Operation ID**           | `API-55`                                                                                                                                                                           |
| **Method and path**        | `GET /elections/{election_context_id}/capacity-incidents`                                                                                                                          |
| **Purpose**                | Publish that capacity is constrained, what is paused and what happens next — **with no figure of any kind** (`TC-81`, `FM-16C-29`)                                                 |
| **Caller**                 | Any reader                                                                                                                                                                         |
| **Authorization**          | **None**                                                                                                                                                                           |
| **Request schema**         | `election_context_id`                                                                                                                                                              |
| **Response schema**        | `incidents[]` with `incident_class`, `reason_code`, `affected_scope`, coarsened time, `remedy_state`, `governed_decision_reference`; `schema_version`                              |
| **Privacy classification** | PUBLIC                                                                                                                                                                             |
| **Idempotency**            | **Yes**                                                                                                                                                                            |
| **Rate-limit policy**      | Generous — an incident notice must be readable by everyone at once (`RL-03`)                                                                                                       |
| **Reason codes**           | `bulletin_board.batch_capacity_exhausted`, `election.capacity_plan_invalid`, `publication.unscheduled_batch_prohibited`                                                            |
| **Timeout semantics**      | Bounded                                                                                                                                                                            |
| **Retry semantics**        | Safe                                                                                                                                                                               |
| **Failure semantics**      | `temporarily_unavailable`. **An incident is published as it occurs and is never held pending review** (`EV-08`)                                                                    |
| **Audit evidence**         | The incident records are themselves the evidence (artefact 37)                                                                                                                     |
| **Forbidden data**         | **Occupancy · remaining slots · queue depth · number of unserved submissions · turnout** — the incident says capacity is constrained, never how constrained (`TC-81`, `RN-16C-29`) |

---

## 5. Operations that are prohibited

Listed as operations so that their absence is checkable rather than assumed.

```text
PROHIBITED   read a ballot's plaintext                    - nothing holds it
PROHIBITED   look up a ballot by voter, credential or capability
PROHIBITED   look up whether a person has voted
PROHIBITED   delete, modify or replace a published entry
PROHIBITED   re-cast, restore or transfer a ballot
PROHIBITED   decrypt anything before the closure checkpoint
PROHIBITED   any live count, turnout or progress read
PROHIBITED   an administrative override of the atomic boundary
PROHIBITED   an operation that returns per-ballot rejection detail
             before closure
PROHIBITED   an export that joins gateway metadata to ballot fields

ADDED BY THE TURNOUT CORRECTION

PROHIBITED   enumerate the occupied leaves of a batch
PROHIBITED   return a batch's occupancy, real-leaf count or leaf classes
             before closure
PROHIBITED   return another caller's leaf opening
PROHIBITED   open a batch partially, or open one batch and not another
PROHIBITED   re-issue, back-date or re-derive a batch commitment
PROHIBITED   change the batch cadence, interval or capacity during an
             election

ADDED BY THE CAPACITY CORRECTION

PROHIBITED   report occupancy, remaining slots or queue depth to any
             caller, at any time
PROHIBITED   accept a publication-bearing submission without an
             atomically reserved leaf slot
PROHIBITED   publish a batch commitment outside the predeclared schedule
PROHIBITED   let a public evidentiary challenge consume a cast-reserved
             slot
PROHIBITED   hold an accepted artefact in any queue outside the schedule
PROHIBITED   transmit a local diagnostic challenge as telemetry or as an
             event
PROHIBITED   expose a per-capability remaining-entitlement counter
```

| ID       | Rule                                                                                                                                                                                 |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `API-34` | **Each prohibition is a checkable absence.** PACK-16D must be able to show that no route, no internal service call and no administrative tool implements any of them                 |
| `API-35` | **A prohibition is not satisfied by requiring elevated permission.** These operations must not exist at any permission level, because the risk is that they exist at all (`DP-01`)   |
| `API-46` | **The six added prohibitions are what make the sealed batch layer a guarantee rather than a convention.** An occupancy endpoint behind an admin role would defeat `TC-29` completely |

---

## 6. Cross-cutting behaviour

| ID       | Rule                                                                                                                                                                                                                                                         |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `API-05` | **`API-14` is a probe and consumes nothing.** It exists so that a voter learns early that a capability is unusable, and it is explicitly excluded from the atomic boundary (`CN-*`)                                                                          |
| `API-06` | **`API-15` is idempotent by retry token and by nothing else.** Same token and identical envelope returns the prior outcome; same token and a different envelope is `submission.retry_token_conflict`, never a second acceptance (`CN-08`, pipeline stage 17) |
| `API-07` | **`API-16` never mutates.** A status check is not a resubmission, and a voter who checks status has not spent anything                                                                                                                                       |
| `API-08` | **`API-18` takes a confirmation code, not an identity.** Anyone holding the code can fetch the receipt, which is exactly what makes the receipt worthless as proof of content (`RE-01`)                                                                      |
| `API-09` | **No casting operation accepts or returns a continuation capability in a URL, a query string or a redirect.** The capability travels in a request body over an authenticated channel and appears in no log (`PM-*`)                                          |
| `API-30` | **`API-18` and `API-20` log nothing about the subject of the query.** No confirmation code, no result, no correlation with a request address (`PM-*` #27, #40)                                                                                               |
| `API-31` | **`API-21`, `API-22` and `API-51` return material a verifier can recompute from `API-24` and `API-50`.** A verifier must never have to trust the server for the proof it is checking the server with                                                         |
| `API-32` | **`API-29`, `API-52` and `API-53` do not exist before closure.** They are not permission-gated, rate-limited or empty — the closure checkpoint is what brings them into being (`API-03`, `API-42`)                                                           |
| `API-33` | **Every public read is available over a plain HTTPS fetch without JavaScript, without an account and without accepting terms** (`XA-27`, `IV-04`)                                                                                                            |
| `API-37` | **Rate limiting never distinguishes a valid capability from an invalid one by its response timing**, because a timing oracle on `API-14` would let an attacker test capabilities                                                                             |
| `API-38` | **No operation returns a different shape depending on ballot content or batch occupancy.** Response size and structure are fixed per operation and per phase (`PM-06`, `TC-33`)                                                                              |
| `API-39` | **Errors are returned to the client and recorded in aggregate**, never published per ballot before closure (`VP-13`)                                                                                                                                         |
| `API-40` | **Versioning is explicit**: every response names the schema version it is written against, and a verifier states which versions it accepts (`ER-11`)                                                                                                         |
| `API-47` | **`API-50` is fetched on a fixed public cadence and its response is constant-size.** A caller polling it learns the schedule, which is already published, and nothing else (`TC-33`)                                                                         |

---

## 7. Data models — `DM-*`

Named here because several documents refer to them and because the
separations below are the ones a schema can silently destroy.

| ID      | Model                             | Holds                                                                                                                                   | **Must never hold**                                                                                                          |
| ------- | --------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `DM-01` | **Ballot envelope**               | `ballot_id`, ciphertexts, proofs, style reference, manifest digest, parameter set reference, profile, confirmation code, retry token    | identity, credential, capability, plaintext, nonce, timestamp finer than granularity                                         |
| `DM-02` | **Published board entry**         | entry type, sequence, payload digest, payload, checkpoint reference                                                                     | retry token (stripped, `BP-16`), capability, internal object ID, arrival order                                               |
| `DM-03` | **Acceptance record**             | ballot reference, acceptance state, publication commitment, **named batch window**, leaf reference                                      | **any capability reference** — this is the join that must not exist (`CN-*`, `PM-03`)                                        |
| `DM-04` | **Capability consumption record** | capability reference, consumed flag                                                                                                     | **any ballot reference** — the other half of the same prohibition                                                            |
| `DM-05` | **Receipt**                       | context reference, confirmation code, **sealed batch reference**, checkpoint reference, publication status, schema version              | everything in `RE-*` §2's prohibited list, including leaf index and occupancy                                                |
| `DM-06` | **Checkpoint**                    | tree head, previous checkpoint, sequence, signature, signer, co-signatures                                                              | —                                                                                                                            |
| `DM-07` | **Spoiled-ballot record**         | ciphertexts, **full opening**, style, marking as not counted                                                                            | any link to a cast ballot, any voter reference                                                                               |
| `DM-08` | **Exclusion record**              | ballot identifier, ground, reason code, decision, Auditor concurrence                                                                   | who cast it — **not knowable** (`EX-07`)                                                                                     |
| `DM-09` | **Aggregate/tally artefact**      | aggregate ciphertexts, shares, proofs, contributing guardians, totals                                                                   | any per-ballot plaintext                                                                                                     |
| `DM-14` | **Sealed batch commitment**       | `batch_sequence`, `batch_window_id`, `fixed_capacity_profile_id`, `commitment_root`, checkpoint linkage, signature                      | **occupancy, leaf classes, any leaf's contents, any count** — and its serialized size must not vary with occupancy (`TC-33`) |
| `DM-15` | **Commitment leaf**               | for a real leaf: salt plus the committed digests of `TC-27`; for a cover leaf: a uniform random value of identical size                 | for a cover leaf: **any structure at all** — it must be indistinguishable from a hash output (`TC-28`)                       |
| `DM-16` | **Batch opening**                 | every leaf in index order with its class and opening, and the leaf-index → artefact mapping                                             | any nonce or plaintext of an **accepted** ballot; any capability reference                                                   |
| `DM-17` | **Batch reconciliation record**   | per-batch counts by class, global totals, artefact mapping, recomputed roots, per-batch verification result, the executed capacity plan | **any pairing of a ballot with a capability** (`DM-10`)                                                                      |
| `DM-20` | **Capability entitlement state**  | `cast_entitlement_available`, `public_challenge_entitlement_available`, `capability_consumed` — three booleans, nothing more            | **identity · credential · ballot reference · public challenge artefact ID · any counter** (`CN-36`, `CN-37`, `CN-38`)        |
| `DM-21` | **Leaf reservation**              | slot reference, interval, partition class, in-flight submission reference, timeout                                                      | **any capability reference, identity or ballot content** (`TC-73`)                                                           |
| `DM-22` | **Capacity plan**                 | `E`, `K`, `A`, `L_max`, `C_primary`, `C_reserve`, `R`, interval count, partition, safety reserve                                        | nothing voter-specific; it is published with the manifest (`BE-32`)                                                          |

| ID      | Rule                                                                                                                                                                                                                                                                              |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `DM-10` | **`DM-03` and `DM-04` are separate stores with no foreign key, no shared surrogate key and no common correlation column.** The atomic boundary writes to both; nothing ever reads them together. This is the single most important schema statement in the pack (`CC-04`, `CN-*`) |
| `DM-11` | **`DM-07` is a separate model from `DM-01`, not a flag on it.** A spoiled ballot's opening and a cast ballot's absence of one are separated at the data-model level, so that no conditional decides whether an opening is published (`ER-08`)                                     |
| `DM-12` | **No model carries an exact timestamp.** Where a time is needed, it is at the context's `timestamp_granularity` (`ER-09`)                                                                                                                                                         |
| `DM-13` | **A field added to any model in PACK-16D must be added to `PACK-16C-PRIVACY-AND-METADATA-MATRIX.md` first** (`PM-12`)                                                                                                                                                             |
| `DM-18` | **`DM-15`'s two variants must be byte-indistinguishable before closure.** A cover leaf that is shorter, longer, structured, or drawn from a distinguishable distribution breaks `TC-29` silently — this is `T-P16C-45` and `RB-16C-10`                                            |
| `DM-23` | **`DM-20` holds three booleans and no counter**, so no deployment can widen the bound by writing a larger number, and no aggregate of residual entitlements can become an activity signal (`CN-37`, `CN-38`)                                                                      |
| `DM-24` | **`DM-21` is anonymous and short-lived.** A reservation binds a slot to a submission in flight; it never binds a slot to a capability, and it is released on rejection or timeout (`TC-71`, `TC-72`)                                                                              |
| `DM-19` | **`DM-17` maps public artefacts to public artefacts only.** It is the completeness argument, not an audit join; the count comparison of `TC-52` lives outside it, with the Auditor                                                                                                |

---

## 8. Completeness of this catalogue

```text
Operations specified                                   26
   casting                                              9   API-10 ... API-18
   client-local, NO NETWORK API                         1   API-19
   verification and board                              10   API-20 ... API-29
   sealed batch and capacity                            6   API-50 ... API-55
Operations with all sixteen required fields            26
Operations missing any required field                   0
Duplicate Operation IDs                                 0
Operations taking an identity as input                  0
Operations returning occupancy at any time              0
Operations returning a remaining-entitlement count      0
Prohibited operations enumerated                       23
Data models specified                                  16   DM-01 … DM-09, DM-14 … DM-17,
                                                             DM-20 … DM-22
Data-model rules                                        6   DM-10 … DM-13, DM-18, DM-19
```

| ID       | Rule                                                                                                                                                                                                                               |
| -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `API-48` | **The count is computed from §4, not asserted.** Each profile is a `#### \`API-nn\`` heading followed by exactly sixteen field rows, and both are mechanically checkable                                                           |
| `API-49` | **An operation added in PACK-16D must arrive with all sixteen fields, a privacy class, a rate-limit policy and an acceptance row.** An operation introduced without them is a defect regardless of what it does (`PM-12`, `EV-66`) |

---

## 9. What this document does not decide

```text
Transport, verbs, status codes and route framework   -> PACK-16D
OpenAPI documents and contract tests                  -> PACK-16D
Wire serialization                                     -> OD-P16C-04
Inclusion-proof wire format                            -> OD-P16C-15
Opening and reconciliation format                      -> OD-P16C-16
Concrete rate-limit values                             -> GOVERNANCE, RL-06
Storage engine and physical schema                      -> PACK-16D
```

**SPECIFIED. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY. NOT LEGALLY
ACTIVATED.**
