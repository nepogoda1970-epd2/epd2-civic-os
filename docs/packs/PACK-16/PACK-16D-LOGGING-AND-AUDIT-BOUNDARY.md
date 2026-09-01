# PACK-16D — Logging and Audit Boundary

**Round:** PACK-16D — Cryptographic Implementation Architecture, Reference
Components, Atomic Persistence, Test Vectors and Verification Harness.
**Reference implementation. Not production code. Not certified. Not a PASS.**
**Repository version:** unchanged at `0.16.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-102`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 1. Scope

This document describes
`services/voting-service/src/epd2_voting_service/reference/logging_boundary.py`
and `.../reference/audit.py`: what may be logged, what may never be
logged, what happens to a record that breaks the rule, and what the audit
chain does and does not prove.

| ID      | Symbol                                          | Role                                                                                                          |
| ------- | ----------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| `LA-01` | `FORBIDDEN_LOG_FIELDS`                          | 23 field names that are never logged, under any level, in any environment                                     |
| `LA-02` | `ALLOWED_FIELDS`                                | The complete set of 7 loggable field names. Nothing else may be emitted                                       |
| `LA-03` | `ReferenceLogger.emit()`                        | The only sink. Validates the reason code, then every field name, then writes                                  |
| `LA-04` | `ForbiddenLogFieldError`                        | Reason code `LOG_FIELD_REJECTED`. Raised for a forbidden name, an undeclared name, or a free-text reason code |
| `LA-05` | `scan_mapping()`                                | Returns any forbidden names present in a mapping. Used by the event and outbox tests as well as by logging    |
| `LA-06` | `AuditRecordType`, `AuditLog`, `verify_chain()` | 10 record types, hash-chained append-only evidence                                                            |
| `LA-07` | `AuditFieldRejected`                            | Reason code `AUDIT_FIELD_REJECTED`. Raised for **any** additional field, forbidden or not                     |

## 2. The two lists

### 2.1 The 23 forbidden field names

```text
continuation_capability   capability            capability_reference
credential                credential_id         identity
identity_id               voter_id              member_id
ballot_plaintext          plaintext             ballot_nonce
nonce                     exact_timestamp       timestamp
ip                        ip_address            client_ip
challenge_to_cast_correlation                   trace_id
correlation_id            session_id            user_agent
```

| ID      | Rule                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `LA-08` | The list covers four distinct hazards, not one: **capability and credential material** (`continuation_capability` … `member_id`), **ballot content** (`ballot_plaintext`, `plaintext`, `ballot_nonce`, `nonce`), **correlation handles** (`challenge_to_cast_correlation`, `trace_id`, `correlation_id`, `session_id`), and **network or device identity plus precise time** (`ip`, `ip_address`, `client_ip`, `user_agent`, `exact_timestamp`, `timestamp`) |
| `LA-09` | `timestamp` and `exact_timestamp` are both forbidden because a precise time is a correlation handle. The only permitted temporal field is `coarse_time_bucket`                                                                                                                                                                                                                                                                                               |
| `LA-10` | `trace_id` and `correlation_id` are forbidden even though every other service in this repository would treat them as routine operational fields. A trace identifier that spans a public challenge and a later cast rejoins exactly the two events the protocol separates                                                                                                                                                                                     |
| `LA-11` | **Every one of the 23 names is tested individually.** `test_forbidden_log_field_fails_the_test_sink` is parametrised over `sorted(FORBIDDEN_LOG_FIELDS)`, asserts the raise, and then asserts `logger.records == []` — so a name that were to slip through the check but still be written would fail on the second assertion                                                                                                                                 |
| `LA-12` | Name matching is on `name.strip().lower()`, so `"Capability "` and `"CAPABILITY"` are refused exactly as `"capability"` is                                                                                                                                                                                                                                                                                                                                   |

### 2.2 The 7 allowed field names

| ID      | Field                     | Why it is safe to log                                                                                                                                                                                         |
| ------- | ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `LA-13` | `component`               | Names the emitting module. Carries no per-submission information. Set on the logger, not per record                                                                                                           |
| `LA-14` | `reason_code`             | A catalogue code, shape-constrained — see §4                                                                                                                                                                  |
| `LA-15` | `coarse_time_bucket`      | The batch window, not the moment. The whole point of the batch window is that it is the finest time granularity the system is willing to disclose                                                             |
| `LA-16` | `election_context_id`     | Public. It is on the bulletin board                                                                                                                                                                           |
| `LA-17` | `outcome`                 | The result class of the operation, not the artefact it acted on                                                                                                                                               |
| `LA-18` | `count`                   | An aggregate. Note that a count is only safe where the emitting component is not counting accepted ballots before closure; the field name boundary does not enforce that, the pre-closure entry-type rules do |
| `LA-19` | `internal_transaction_id` | See §5                                                                                                                                                                                                        |

| ID      | Rule                                                                                                                                                                                                                                                                                                                                                     |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `LA-20` | **`ALLOWED_FIELDS` and `FORBIDDEN_LOG_FIELDS` are asserted disjoint** by `test_allowed_and_forbidden_log_fields_are_disjoint`, so the two lists cannot drift into disagreeing about one name                                                                                                                                                             |
| `LA-21` | **An undeclared field is refused even when it looks harmless.** `logger.emit("acceptance.committed", ballot_count=3)` raises, because `ballot_count` is in neither list. `test_an_undeclared_field_is_refused_even_if_it_looks_harmless` pins this. The error message names the remedy — add the field to the boundary with a decision, or do not log it |
| `LA-22` | There is no level-dependent behaviour. The boundary applies identically at every level and in every environment; there is no debug mode in which more may be logged                                                                                                                                                                                      |

## 3. There is no redaction step

| ID      | Rule                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `LA-23` | **A forbidden field is a defect in the caller, not a value to be masked.** `_check()` raises `ForbiddenLogFieldError`; `emit()` therefore never reaches the append, and **nothing is written** — not the offending field, not the record it was part of, not a redacted version of either                                                                                                                                                                          |
| `LA-24` | **This is the whole design decision.** A redaction step turns a caller defect into a silent, absorbed condition: the field is masked, the log line is written, the reviewer sees `capability=***` and concludes the boundary works. What the boundary would actually have proved is that a code path exists which hands capability material to the logging layer. Refusing the record makes that path fail loudly, in a test, at the point where it can be removed |
| `LA-25` | **The consequence is accepted deliberately: a defective caller loses its log line.** That is preferable to keeping the line and normalising the defect. Losing observability at a broken call site is a smaller harm than a redaction pipeline nobody reads the output of                                                                                                                                                                                          |
| `LA-26` | The same discipline is applied to the audit log, where the rule is stricter still — see `LA-38`                                                                                                                                                                                                                                                                                                                                                                    |

## 4. The reason-code shape constraint

`reason_code` is validated before any field is examined, against

```text
^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$    |    ^[A-Z][A-Z0-9_]*$
```

| ID      | Rule                                                                                                                                                                                                                                                                                                                                              |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `LA-27` | Two shapes are accepted: a **dotted lowercase catalogue code** with at least one dot (`acceptance.committed`, `challenge.public_entitlement_exhausted`), and an **all-uppercase code** (`SUBMISSION_IDEMPOTENCY_CONFLICT`). The second shape is the form the reference implementation's typed errors carry in their `reason_code` class attribute |
| `LA-28` | The single-dot requirement is what excludes an ordinary English word. A bare `accepted` does not match the dotted alternative, because that alternative requires a dot                                                                                                                                                                            |
| `LA-29` | **A free-text reason code is refused.** `logger.emit("voter cap-1 cast ballot abc")` raises `ForbiddenLogFieldError` with the message _"is not a catalogue reason code"_. `test_free_text_reason_codes_are_refused` pins it. Spaces and hyphens match neither alternative                                                                         |
| `LA-30` | The constraint is a shape constraint, not a membership check. The sink does not hold the PACK-16C catalogue and does not verify that a well-shaped code is a _registered_ code. A code of the right shape that names nothing is accepted by the sink and would have to be caught by review                                                        |

## 5. Why no free-text field is allowed at all

| ID      | Rule                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `LA-31` | **`ALLOWED_FIELDS` contains no message field, no detail field and no free-text field of any kind.** `ReferenceLogger` never formats a string; `emit()` takes a reason code and named fields, and `LogRecord` holds `component`, `reason_code` and a tuple of `(name, value)` pairs                                                                                                                                                                                                  |
| `LA-32` | **The reason is structural, and it is the honest limit of this whole mechanism.** This is a _field-name_ boundary. It can decide whether a field called `capability_reference` is present. It cannot look at the value of a permitted field and decide whether a capability is hiding in it. A single free-text field — `message="rejected submission for cap-8f21e0 in contest c1"` — would defeat every one of the 23 prohibitions at once, and the boundary would report success |
| `LA-33` | `logging_boundary.py` states this in its own module docstring, so a reader of the code meets the limitation before meeting the mechanism: _"This is a field-name boundary. It cannot detect a capability reference smuggled inside an allowed free-text field, which is why `ALLOWED_FIELDS` contains no free-text field and `reason_code` is constrained to the PACK-16C catalogue shape."_                                                                                        |
| `LA-34` | **The residual exposure that remains.** Values of the six permitted non-`component` fields are stringified and written unchecked. A caller that passes `outcome=<capability string>` is not caught by anything in this module. Removing free text narrows the opening; it does not close it. Only review of the call sites closes it, and this round has no automated check over call-site values                                                                                   |

## 6. `internal_transaction_id`

| ID      | Rule                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `LA-35` | `internal_transaction_id` is on the allow-list because §46 permits a non-sensitive internal transaction identifier for operational correlation **within one service**, in place of the `trace_id` and `correlation_id` the same boundary forbids                                                                                                                                                                                                                                                                                                                                                                                          |
| `LA-36` | Three rules govern it, and all three are properties of how a caller mints and handles the value, not properties this class can check: it is **not exported** to any public artefact or bulletin-board entry; it is **not shared across an identity domain**, so it may never appear in both an identity-side and a voting-side record; and it is **never election-record material** — no field of `ElectionRecord`, `SealedBatch`, `BatchOpening` or any board entry carries one                                                                                                                                                          |
| `LA-37` | **What the code actually enforces is only the field name.** `ReferenceLogger` accepts the field and stringifies whatever it is given. In this round no reference component mints an `internal_transaction_id` at all: the identifier appears in the source only in `ALLOWED_FIELDS`, in the class docstring, and in `test_allowed_log_fields_are_accepted`, which passes the literal `"tx-1"` and asserts it is accepted. There is therefore **no test that a minted identifier stays inside its service**, because nothing mints one. The three rules above are obligations on a production implementation, and they are unverified here |

## 7. The audit model

### 7.1 Ten record types

```text
parameter_validation   proof_validation        atomic_acceptance
atomic_challenge       reservation             publication_obligation
board_append           checkpoint              closure
verification
```

| ID      | Rule                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `LA-38` | **An audit record carries exactly seven fields and accepts no others:** `sequence`, `record_type`, `reason_code`, `election_context_id`, `coarse_time_bucket`, `outcome`, `previous_hash`. `AuditLog.append()` collects any additional keyword into `**rejected` and raises `AuditFieldRejected` if that mapping is non-empty. The rule is stricter than the logging allow-list — **any** extra field is refused, not merely a forbidden one — and the error message names both the offending fields and, separately, which of them are in `FORBIDDEN_LOG_FIELDS`. `test_audit_records_reject_extra_fields` passes `capability_reference="cap-1"`, asserts the raise, and asserts `log.records == []` |
| `LA-39` | **The record type list is closed.** Adding a class means adding a decision, not adding a string at a call site                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `LA-40` | **An audit record is not a capability-to-ballot map, by shape.** `test_audit_log_is_not_a_capability_to_ballot_map` reads `record.__slots__` and asserts it intersects none of `capability_reference`, `ballot_id`, `voter_id`, `identity`. The record has no field that could hold either half of that join                                                                                                                                                                                                                                                                                                                                                                                          |

### 7.2 The hash chain

| ID      | Rule                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `LA-41` | Each record's `previous_hash` is the digest of its predecessor; the first record's is 32 zero bytes. A digest is `h(ZERO_KEY, DomainLabel.AUDIT_RECORD, [canonical_bytes()])` — HMAC-SHA-256 under the registry's own `AUDIT_RECORD` domain label, over the canonical encoding of all seven fields                                                                                                                                                                                                                                                      |
| `LA-42` | The `AUDIT_RECORD` label exists because of a correction made during this round. Audit records had been digested under the `VERIFICATION_RESULT` label, reusing another aggregate's domain. The label was added; the registry holds 27 labels after the correction round added `CEREMONY_TRANSCRIPT` and `BOARD_SIGNATURE` as well                                                                                                                                                                                                                       |
| `LA-43` | `verify_chain()` walks the list once and returns `False` if any record's `sequence` is not its index or if any `previous_hash` does not match the recomputed digest of its predecessor. `test_audit_log_is_tamper_evident` appends one record of each of the 10 types, asserts `verify_chain() is True`, replaces record 3 with a copy whose `reason_code` differs, and asserts `verify_chain() is False`                                                                                                                                               |
| `LA-44` | **What the chain proves and what it does not.** It makes silent modification and silent deletion _detectable_. It does not make them _impossible_ — an actor who can rewrite the list can rebuild the chain over it, because the digest key is `ZERO_KEY` and the chain is not anchored anywhere outside the process. `audit.py` says this in its module docstring, and adds the second half: **the audit log is not a substitute for the bulletin board.** The board is the published, externally checkable record; the audit log is internal evidence |

### 7.3 Role restriction and retention are named, not implemented

| ID      | Rule                                                                                                                                                                                                                                                                                                                                                                                                                              |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `LA-45` | **Access to audit evidence is not restricted by this class.** `AuditLog` is a dataclass with a public `records` list. Anything holding the object can read, append to and mutate that list. Role restriction — Auditor-only access to the per-capability entitlement evidence, and the separation of that role from operations — is a governance property enforced outside the class. `AuditLog`'s own docstring names it as such |
| `LA-46` | **Retention is not implemented.** There is no expiry, no maximum length, no deletion path and no retention policy in the code. Records accumulate for the lifetime of the object                                                                                                                                                                                                                                                  |
| `LA-47` | **Neither may be described as implemented anywhere.** They are named here so that a reader is not left to infer from a hash-chained append-only structure that access control and a retention schedule came with it. They did not                                                                                                                                                                                                 |

## 8. What this document does not decide

```text
Audit access control and Auditor role separation      → GOVERNANCE, not implemented
Audit retention schedule and deletion                 → GOVERNANCE, not implemented
Call-site review of permitted field *values*          → open, no automated check
Externally anchored audit evidence                    → PACK-17
Production logging transport and storage              → PACK-17
Registered-code membership checking in the sink       → PACK-17
```

**REFERENCE IMPLEMENTATION. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY.
NOT LEGALLY ACTIVATED.**
