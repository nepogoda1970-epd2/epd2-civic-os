# PACK-15 — API Catalog

**Round:** PACK-15 — specification and ADR only. **No code. Not implemented. Not a candidate. Not a PASS.**
**Repository version:** unchanged at `0.14.0` · **Canon version:** unchanged at `0.8.0`
**Baseline:** `EPD2_PACK-14_IDENTITY_AUTHENTICATION_ACCOUNT_SECURITY_0.14.0_FINAL_PASS.zip`
**Authoritative register:** `EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER_UPDATED_V6.md`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**
**Architecture correction applied (2026-07-31).**

**Thirty-four future versioned operations. None is implemented, none is
routed, and no transport is bound.** Like PACK-10 through PACK-14, this
round exposes no HTTP surface, so there is deliberately **no
`contracts/openapi/pack-15.yaml`**: an OpenAPI document describing an
unbound transport would make the contract suite assert against a fiction.

---

## 1. Obligations every consequential operation must declare

Following PACK-14's `EndpointSpec` discipline, a PACK-15 operation may not
be specified without stating all six:

| Obligation                 | Meaning                                                                  |
| -------------------------- | ------------------------------------------------------------------------ |
| `idempotency_key_required` | Whether a retry must be safe, and on what key                            |
| `version_check_required`   | Whether the operation is bound to an object version                      |
| `audit_evidence_required`  | Which of the six streams receives evidence — **exactly one**             |
| `required_assurance`       | The PACK-14 assurance the caller must have, where the caller is a person |
| `separation_of_duties`     | Which roles may call it and which combinations are refused               |
| `boundary_side`            | `identity` or `voting` — and no operation may declare both               |

The last one is PACK-15's addition and is the load-bearing one: an
operation that would need both sides does not exist, and the specification
must refuse it rather than route it.

---

## 2. Voting context — VC-01, identity-neutral

| Operation                 | Consequential | Idempotent | Stream  | Roles                                            |
| ------------------------- | ------------- | ---------- | ------- | ------------------------------------------------ |
| `voting_context.create`   | yes           | yes        | `AS-06` | Voting Operations Officer                        |
| `voting_context.activate` | yes           | yes        | `AS-06` | Voting Operations Officer + Governance (dual)    |
| `voting_context.suspend`  | yes           | yes        | `AS-06` | Voting Operations Officer                        |
| `voting_context.close`    | yes           | yes        | `AS-06` | Voting Operations Officer                        |
| `voting_context.get`      | no            | n/a        | —       | Any authenticated participant, for public fields |

## 3. Eligibility — VC-02, identity side

| Operation                               | Consequential | Idempotent | Stream  | Roles                                |
| --------------------------------------- | ------------- | ---------- | ------- | ------------------------------------ |
| `eligibility.request_evaluation`        | yes           | yes        | `AS-01` | Participant; assisted helper         |
| `eligibility.get_state`                 | no            | n/a        | —       | The participant; Eligibility Officer |
| `eligibility.submit_evidence_reference` | yes           | yes        | `AS-01` | Participant; assisted helper         |
| `eligibility.request_manual_review`     | yes           | yes        | `AS-01` | Participant; Eligibility Officer     |
| `eligibility.record_decision`           | yes           | yes        | `AS-01` | Eligibility Reviewer                 |
| `eligibility.open_dispute`              | yes           | yes        | `AS-01` | Participant                          |
| `eligibility.resolve_dispute`           | yes           | yes        | `AS-01` | Dispute Reviewer                     |

## 4. Assertion — VC-03, identity side

| Operation            | Consequential | Idempotent            | Stream                                                           | Roles                                 |
| -------------------- | ------------- | --------------------- | ---------------------------------------------------------------- | ------------------------------------- |
| `assertion.issue`    | yes           | yes                   | `AS-02`                                                          | Assertion Issuer (system role)        |
| `assertion.revoke`   | yes           | yes                   | `AS-02`                                                          | Assertion Issuer; Eligibility Officer |
| `assertion.validate` | no            | n/a                   | —                                                                | Credential Issuer only                |
| `assertion.redeem`   | yes           | **yes, on the nonce** | `AS-02` + `AS-03` **as two separate records with no shared key** | Credential Issuer                     |

`assertion.redeem` is the only operation that writes evidence on both sides
of the boundary, and it does so as **two independent records that share no
key, no correlation identifier and no timestamp precision**. The
implementation round must demonstrate that the two records cannot be
paired, which is a stronger obligation than demonstrating that no code
pairs them.

## 5. Credential — VC-04, voting side

| Operation                            | Consequential | Idempotent | Stream  | Roles                                       |
| ------------------------------------ | ------------- | ---------- | ------- | ------------------------------------------- |
| `credential.request`                 | yes           | yes        | `AS-03` | Participant's client                        |
| `credential.issue`                   | yes           | yes        | `AS-03` | Credential Issuer                           |
| `credential.revoke_unredeemed`       | yes           | yes        | `AS-03` | Credential Issuer (+ dual control late)     |
| `credential.redeem`                  | yes           | yes        | `AS-03` | The isolated client                         |
| `credential.reject_replay`           | n/a           | n/a        | `AS-03` | Credential Issuer                           |
| `credential.get_privacy_safe_status` | no            | n/a        | —       | The holder, against a reference they supply |

`credential.get_privacy_safe_status` **has no search**. It answers only
about a credential reference the caller already holds, returns only a
status class and a next step, and returns the same shape for an unknown
reference as for a revoked one, so that it cannot be used as an oracle.

## 6. Handoff — VC-05

| Operation                          | Consequential | Idempotent | Stream  | Roles  |
| ---------------------------------- | ------------- | ---------- | ------- | ------ |
| `handoff.accept`                   | yes           | yes        | `AS-06` | System |
| `handoff.validate_origin_audience` | no            | n/a        | —       | System |
| `handoff.create_eligibility_flow`  | yes           | yes        | `AS-06` | System |
| `handoff.consume_one_time`         | yes           | yes        | `AS-06` | System |

## 7. Audit — VC-06

| Operation                          | Consequential | Idempotent | Stream  | Roles                                  |
| ---------------------------------- | ------------- | ---------- | ------- | -------------------------------------- |
| `audit.export_separated_bundle`    | yes           | yes        | `AS-05` | Independent Auditor                    |
| `audit.verify_integrity`           | no            | n/a        | —       | Independent Auditor; Security Auditor  |
| `audit.request_independent_review` | yes           | yes        | `AS-05` | Governance; participant via `F-P15-09` |

`audit.export_separated_bundle` exports **one** stream's bundle per call
and refuses a request naming two. There is no "export everything"
operation, and its absence is a specified property rather than an
omission.

---

## 8. Operations deliberately absent

| Operation that will be proposed     | Why it does not exist                                |
| ----------------------------------- | ---------------------------------------------------- |
| `credential.find_by_participant`    | The issuer does not know participants                |
| `eligibility.get_credential_status` | Crosses the boundary in one call                     |
| `participation.get_journey`         | The journey is the chain                             |
| `voting_context.get_turnout`        | An intermediate tally                                |
| `credential.list` (unscoped)        | Enumerating credentials is enumerating participation |
| `assertion.get_issued_credential`   | The pairing, as an endpoint                          |
| `audit.export_all`                  | The join, as an endpoint                             |
| `credential.revoke_by_participant`  | Selective disenfranchisement, as an endpoint         |

---

## 9. Contract evolution

PACK-13's ADR-074 governs, unchanged. Two PACK-15-specific rules:

1. **No operation may gain a parameter or a response field that would make
   it span both sides of the boundary.** Compatibility is not the test;
   `boundary_side` is.
2. **A response field that narrows a cohort is a breaking change to
   privacy even when it is compatible in shape.** Scope labels, precise
   timestamps and device classes on voting-side responses fall under this
   rule.

---

## 10. Operations added and constrained by the architecture correction (2026-07-31)

**Total after the correction: forty operations.** None is implemented, none
is routed, and no transport is bound.

### 10.1 Assertion queue and pickup — VC-03 / VC-05

| Operation                     | Consequential | Idempotent        | Stream  | `boundary_side` | Roles                                 |
| ----------------------------- | ------------- | ----------------- | ------- | --------------- | ------------------------------------- |
| `assertion.mint`              | yes           | yes               | `AS-02` | identity        | Assertion Issuer (system)             |
| `assertion.get_release_state` | no            | n/a               | —       | identity        | The participant (own state only)      |
| `pickup.create`               | yes           | yes               | `AS-02` | identity        | Assertion Issuer (system)             |
| `pickup.redeem`               | yes           | **yes, one-time** | `AS-02` | identity        | **The isolated client only**          |
| `pickup.expire`               | yes           | yes               | `AS-02` | identity        | System                                |
| `evidence_bundle.generate`    | yes           | yes               | `AS-05` | audit           | VC-06 (system)                        |
| `evidence_bundle.validate`    | no            | n/a               | —       | audit           | Independent Auditor; Security Auditor |

`pickup.redeem` is the only identity-side operation callable from inside
WS-03. It accepts the one-time handoff artifact, returns **the assertion
and nothing else**, and is bound to the voting origin by audience and
origin checks. It returns no account, no session, no case reference and no
context-scoped pseudonym.

### 10.2 Constrained by the correction

| Operation                             | Constraint added                                                                                                  |
| ------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `assertion.issue`                     | Superseded by `assertion.mint` + queued release; **immediate issuance is not an available mode**                  |
| `credential.request`                  | Must originate from the voting origin; refuses otherwise with `CREDENTIAL_ORIGIN_REFUSED`                         |
| `credential.issue`                    | Applies the randomized minting delay; returns credential material **only to the isolated client**                 |
| `credential.redeem`                   | Unchanged, and now normally called in the same visit as `credential.issue`                                        |
| `audit.export_separated_bundle`       | Becomes `evidence_bundle.export` (§10.3); the old name is retained as its compatible predecessor                  |
| `voting_context.create` / `.activate` | Must carry a valid `IssuanceTimingProfile`; an out-of-bounds value is refused with `TIMING_PROFILE_OUT_OF_BOUNDS` |

### 10.3 `evidence_bundle.export`

| Property      | Rule                                                                                             |
| ------------- | ------------------------------------------------------------------------------------------------ |
| Authorization | Independent Auditor **plus** a time-boxed PACK-12 grant                                          |
| Scope         | **One context per call.** Two contexts, or raw stream content, is refused                        |
| Pre-closure   | Sections 1, 2, 6, 7, 8 only, under **dual control**                                              |
| Post-closure  | All eight sections                                                                               |
| Evidence      | The export is audited to `AS-05` and `AS-06`                                                     |
| Refusals      | `EVIDENCE_BUNDLE_SCOPE_REFUSED`, `EVIDENCE_BUNDLE_PRECLOSURE_REFUSED`, `EVIDENCE_BUNDLE_INVALID` |

### 10.4 Operations that remain deliberately absent

Everything in §8, plus five the correction adds:

| Operation that will be proposed           | Why it does not exist                                   |
| ----------------------------------------- | ------------------------------------------------------- |
| `credential.deliver_by_email`             | A prohibited delivery channel                           |
| `credential.export` / `credential.render` | Credential material never leaves WS-03                  |
| `assertion.release_now`                   | Bypasses the queue, restoring the timing pair           |
| `pseudonym.resolve`                       | The pseudonym is not reverse-resolvable through any API |
| `evidence_bundle.export_all_contexts`     | Differencing across contexts, as an endpoint            |
