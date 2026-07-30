# PACK-14 — Reason Code Catalog

**Part A round:** PACK-14 — specification and ADR only. Retained unchanged; Part B below records the implementation candidate.
**Round:** PACK-14 — specification and ADR only. **No code. Not implemented. Not a candidate. Not a PASS.**
**Repository version:** unchanged at `0.13.0` · **Canon version:** unchanged at `0.8.0`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**
**Architecture correction applied (2026-07-30).**

## 0. The prohibition that shapes this catalog

**There is no generic `AUTH_ERROR`, and none may be added.** The reasoning
is PACK-13's `P13-RSN-002`, applied to a domain where it matters even
more: where two failures differ in what the person must do next, they are
two codes. "Authentication failed" tells a user nothing and an auditor
less, and in an account-takeover investigation the difference between
"wrong credential" and "credential revoked" is the whole investigation.

A code's meaning never changes. A new meaning is a new code.

## 1. Credential

| Code                          | Meaning                                                                |
| ----------------------------- | ---------------------------------------------------------------------- |
| `CREDENTIAL_INVALID`          | The presented credential did not verify                                |
| `CREDENTIAL_REVOKED`          | The credential exists and has been revoked                             |
| `CREDENTIAL_EXPIRED`          | The credential exists and is past its validity                         |
| `PASSKEY_VERIFICATION_FAILED` | WebAuthn assertion verification failed                                 |
| `PASSKEY_ORIGIN_MISMATCH`     | The assertion was produced for a different origin                      |
| `CREDENTIAL_LAST_REMAINING`   | Removal refused: it is the only credential and no recovery path exists |

## 2. Multi-factor

| Code                      | Meaning                                                    |
| ------------------------- | ---------------------------------------------------------- |
| `MFA_REQUIRED`            | The action requires a second factor that was not presented |
| `MFA_FAILED`              | The second factor was presented and did not verify         |
| `MFA_FACTOR_NOT_ENROLLED` | No factor of the required class is enrolled                |
| `MFA_FACTOR_REVOKED`      | The factor exists and has been revoked                     |

## 3. Assurance and step-up

| Code                     | Meaning                                                      |
| ------------------------ | ------------------------------------------------------------ |
| `ASSURANCE_INSUFFICIENT` | The session's assurance is below what the action requires    |
| `ASSURANCE_STALE`        | Assurance was sufficient but is outside the freshness window |
| `STEP_UP_REQUIRED`       | A step-up is required and has not been performed             |
| `STEP_UP_EXPIRED`        | The step-up was performed and its window has elapsed         |
| `STEP_UP_OBJECT_CHANGED` | The object changed after confirmation; the approval is void  |
| `STEP_UP_CANCELLED`      | The user cancelled the step-up                               |

## 4. Session

| Code                      | Meaning                                              |
| ------------------------- | ---------------------------------------------------- |
| `SESSION_EXPIRED`         | Idle or absolute deadline reached                    |
| `SESSION_REVOKED`         | The session was revoked and cannot refresh           |
| `SESSION_REPLAY_DETECTED` | A rotated token was presented again                  |
| `SESSION_SCOPE_MISMATCH`  | The session is not scoped to this workspace          |
| `SESSION_ORIGIN_MISMATCH` | Presented from an origin the session is not bound to |
| `CSRF_TOKEN_INVALID`      | A state-changing request lacked a valid CSRF token   |

## 5. Account state

| Code                    | Meaning                                          |
| ----------------------- | ------------------------------------------------ |
| `ACCOUNT_LOCKED`        | Technical lock in force                          |
| `ACCOUNT_RESTRICTED`    | A restriction with a named authority is in force |
| `ACCOUNT_QUARANTINED`   | Security quarantine in force                     |
| `ACCOUNT_CLOSED`        | The account is closed                            |
| `ACCOUNT_NOT_ACTIVATED` | Still `pending`                                  |

## 6. Recovery

| Code                                | Meaning                                                 |
| ----------------------------------- | ------------------------------------------------------- |
| `RECOVERY_REQUIRED`                 | Authentication cannot proceed; recovery is the path     |
| `RECOVERY_RISK_TOO_HIGH`            | Risk assessment refused the recovery                    |
| `RECOVERY_COOLING_OFF_ACTIVE`       | The cooling-off window has not elapsed                  |
| `ALTERNATE_VERIFICATION_FAILED`     | The independent verification method failed              |
| `RECOVERY_CONTACT_RECENTLY_CHANGED` | The channel offered was changed too recently to rely on |
| `RECOVERY_SELF_APPROVAL_REFUSED`    | The reviewer is the initiator or the subject            |

## 7. Contact

| Code                       | Meaning                                     |
| -------------------------- | ------------------------------------------- |
| `CONTACT_NOT_VERIFIED`     | The channel has not completed verification  |
| `CONTACT_RECENTLY_CHANGED` | Within the protective window after a change |
| `CONTACT_ALREADY_IN_USE`   | Uniqueness scope violated                   |
| `CONTACT_REUSE_BLOCKED`    | Governed reuse policy refuses this channel  |

## 8. Linking, duplicates and proofing

| Code                             | Meaning                                               |
| -------------------------------- | ----------------------------------------------------- |
| `DUPLICATE_ACCOUNT_SUSPECTED`    | Routed to review; never an automatic merge            |
| `ACCOUNT_LINKING_DENIED`         | Linking refused                                       |
| `ACCOUNT_LINKING_PROOF_MISSING`  | Control of both sides was not proven                  |
| `IDENTITY_PROOFING_INSUFFICIENT` | Proofing assurance below what the action requires     |
| `IDENTITY_ASSERTION_EXPIRED`     | The assertion is outside its freshness window         |
| `IDENTITY_PROOFING_INCONCLUSIVE` | Neither verified nor rejected; manual review required |

## 9. External providers

| Code                            | Meaning                                            |
| ------------------------------- | -------------------------------------------------- |
| `EXTERNAL_PROVIDER_UNAVAILABLE` | The adapter could not reach the provider           |
| `EXTERNAL_ASSERTION_INVALID`    | Issuer, audience, signature or replay check failed |

## 10. Scope, workspace and voting handoff

| Code                              | Meaning                                                   |
| --------------------------------- | --------------------------------------------------------- |
| `ORGANIZATION_SCOPE_MISMATCH`     | Reused from earlier packs; scope does not permit this act |
| `CROSS_WORKSPACE_HANDOFF_INVALID` | Expired, wrong audience or wrong purpose                  |
| `VOTING_HANDOFF_ALREADY_USED`     | Single-use artifact presented a second time               |

## 11. Privileged and review

| Code                            | Meaning                                                   |
| ------------------------------- | --------------------------------------------------------- |
| `PRIVILEGED_APPROVAL_MISSING`   | The required PACK-12 grant or approval is absent          |
| `MANUAL_REVIEW_REQUIRED`        | The decision is routed to a human                         |
| `SEPARATION_OF_DUTIES_VIOLATED` | The actor may not perform this act given their other role |

## 12. Registration rule

The implementation round registers these in
`contracts/reason-codes/pack-14.yml` following the established pattern:
one file, standalone, with independently redeclared reused codes, and a
contract test that no service source contains an unregistered all-caps code
literal. **This round creates no such file, because this round creates no
code.**

---

# Part A ends here.

# Part B — implementation record (PACK-14 candidate, repository `0.14.0`)

Part A above is the accepted specification round's own text, retained
**unchanged**, including its round header. It is the record of that
round and is deliberately not rewritten to read as though it had always
been an implementation - the discipline PACK-13's FINAL PASS round
applied to its own candidate report.

Everything below records what the implementation candidate actually
built.

## B.0 What was registered

## 0. The prohibition, restated

**There is no generic `AUTH_ERROR` and none may be added.** Where two
failures differ in what the person or the operator must do next, they are
two codes. A code's meaning never changes; a new meaning is a new code.

## 1. The registry

`contracts/reason-codes/pack-14.yml`, 213 entries:

| Group                                              | Count |
| -------------------------------------------------- | ----- |
| Additive PACK-14 codes                             | 131   |
| Redeclared from PACK-02, PACK-07, PACK-08, PACK-09 | 22    |
| `*_RECORDED` audit classifications                 | 60    |

The 22 redeclarations exist because PACK-14 extends an **existing**
service in place. Each keeps its original owning pack's meaning and names
that owner, so the file is a complete standalone source of truth for the
literal scan over `services/identity-service/src` without any code
acquiring a second meaning.

## 2. Task §23 → registered name

The task's §23 list uses an `AUTH_`-prefixed style; the accepted
specification's catalog groups codes by subject. The catalog is the
authoritative architecture for this round, so the registry follows it.
**Nothing in the task's minimum set is missing.**

| Task §23 name                            | Registered code                  | Note                                                        |
| ---------------------------------------- | -------------------------------- | ----------------------------------------------------------- |
| `AUTH_INVALID_CREDENTIAL`                | `CREDENTIAL_INVALID`             |                                                             |
| `AUTH_CREDENTIAL_REVOKED`                | `CREDENTIAL_REVOKED`             |                                                             |
| `AUTH_CREDENTIAL_EXPIRED`                | `CREDENTIAL_EXPIRED`             |                                                             |
| `AUTH_PASSKEY_VERIFICATION_FAILED`       | `PASSKEY_VERIFICATION_FAILED`    |                                                             |
| `AUTH_MFA_REQUIRED`                      | `MFA_REQUIRED`                   |                                                             |
| `AUTH_MFA_FAILED`                        | `MFA_FAILED`                     |                                                             |
| `AUTH_ASSURANCE_INSUFFICIENT`            | `ASSURANCE_INSUFFICIENT`         |                                                             |
| `AUTH_STEP_UP_EXPIRED`                   | `STEP_UP_EXPIRED`                |                                                             |
| `AUTH_STEP_UP_BINDING_MISMATCH`          | `STEP_UP_BINDING_MISMATCH`       | **and** `STEP_UP_OBJECT_CHANGED` — two responses, two codes |
| `SESSION_EXPIRED`                        | `SESSION_EXPIRED`                | unchanged                                                   |
| `SESSION_REVOKED`                        | `SESSION_REVOKED`                | unchanged                                                   |
| `SESSION_REPLAY_DETECTED`                | `SESSION_REPLAY_DETECTED`        | unchanged                                                   |
| `ACCOUNT_LOCKED`                         | `ACCOUNT_LOCKED`                 | unchanged                                                   |
| `ACCOUNT_RESTRICTED`                     | `ACCOUNT_RESTRICTED`             | unchanged                                                   |
| `RECOVERY_REQUIRED`                      | `RECOVERY_REQUIRED`              | unchanged                                                   |
| `RECOVERY_RISK_TOO_HIGH`                 | `RECOVERY_RISK_TOO_HIGH`         | unchanged                                                   |
| `RECOVERY_COOLING_OFF_ACTIVE`            | `RECOVERY_COOLING_OFF_ACTIVE`    | unchanged                                                   |
| `RECOVERY_ALTERNATE_VERIFICATION_FAILED` | `ALTERNATE_VERIFICATION_FAILED`  |                                                             |
| `CONTACT_NOT_VERIFIED`                   | `CONTACT_NOT_VERIFIED`           | unchanged                                                   |
| `CONTACT_RECENTLY_CHANGED`               | `CONTACT_RECENTLY_CHANGED`       | unchanged                                                   |
| `ACCOUNT_DUPLICATE_SUSPECTED`            | `DUPLICATE_ACCOUNT_SUSPECTED`    |                                                             |
| `ACCOUNT_LINKING_DENIED`                 | `ACCOUNT_LINKING_DENIED`         | unchanged                                                   |
| `PROOFING_INSUFFICIENT`                  | `IDENTITY_PROOFING_INSUFFICIENT` |                                                             |
| `PROOFING_ASSERTION_EXPIRED`             | `IDENTITY_ASSERTION_EXPIRED`     |                                                             |
| `EXTERNAL_PROVIDER_UNAVAILABLE`          | `EXTERNAL_PROVIDER_UNAVAILABLE`  | unchanged                                                   |
| `EXTERNAL_ASSERTION_INVALID`             | `EXTERNAL_ASSERTION_INVALID`     | unchanged                                                   |
| `ORGANIZATIONAL_SCOPE_MISMATCH`          | `ORGANIZATION_SCOPE_MISMATCH`    | PACK-08's own code, redeclared unchanged                    |
| `BOOTSTRAP_INVALID`                      | `BOOTSTRAP_INVALID`              | unchanged                                                   |
| `BOOTSTRAP_AUDIENCE_MISMATCH`            | `BOOTSTRAP_AUDIENCE_MISMATCH`    | unchanged                                                   |
| `BOOTSTRAP_ALREADY_USED`                 | `BOOTSTRAP_ALREADY_USED`         | unchanged                                                   |
| `VOTING_HANDOFF_INVALID`                 | `VOTING_HANDOFF_INVALID`         | unchanged                                                   |
| `VOTING_HANDOFF_ALREADY_USED`            | `VOTING_HANDOFF_ALREADY_USED`    | unchanged                                                   |
| `PRIVILEGED_APPROVAL_MISSING`            | `PRIVILEGED_APPROVAL_MISSING`    | unchanged                                                   |
| `MANUAL_REVIEW_REQUIRED`                 | `MANUAL_REVIEW_REQUIRED`         | unchanged                                                   |

## 3. Codes the implementation added beyond both lists

The specification catalog named the families; implementing them surfaced
distinctions that needed their own codes, because each calls for a
different response. Among them: `PASSKEY_CHALLENGE_EXPIRED`,
`PASSKEY_SIGN_COUNTER_REGRESSION` (the cloned-authenticator signal),
`PASSKEY_MALFORMED_RESPONSE`, `PASSWORD_ONLY_ACCOUNT_REFUSED`,
`SECURITY_QUESTION_REFUSED`, `SMS_OTP_NOT_AN_AUTHENTICATION_FACTOR`,
`RECOVERY_CREDENTIALS_NOT_REVOKED`, `RECOVERY_RISK_ACCEPTANCE_REQUIRED`,
`CONTACT_AUTO_MERGE_REFUSED`, `GLOBAL_IDENTIFIER_REFUSED`,
`UNRESTRICTED_MAPPING_LOOKUP_REFUSED`,
`VOTING_HANDOFF_REVERSE_RESOLUTION_REFUSED`,
`SYSTEM_ADMIN_IDENTITY_ACCESS_REFUSED`, `SECRET_IN_PAYLOAD_REFUSED`,
`SESSION_IDENTIFIER_IN_URL` and `RETENTION_SCHEDULE_UNCONFIRMED`.

Several of these exist so that an **attempt** is auditable rather than
merely impossible: `VOTING_HANDOFF_REVERSE_RESOLUTION_REFUSED` and
`UNRESTRICTED_MAPPING_LOOKUP_REFUSED` name questions the system will not
answer, and knowing that somebody asked is the point.

## 4. Enforcement

`tests/contract/test_reason_codes_registry.py` runs four checks over
`pack-14.yml`: required fields, no duplicates, loadable through
`epd2_core.reason_codes`, and — the one that matters — every all-caps
literal in `services/identity-service/src` is registered. Ten literals
are enumerated as provable non-codes (five `__init__` constant names,
three `ConfidentialityClass` values, two workspace sensitivity strings)
rather than excluded by a rule that would also hide a genuine code.
