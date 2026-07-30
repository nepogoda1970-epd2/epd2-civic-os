**Round:** PACK-14 — implementation candidate. **NOT PASS. NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**
**Repository version:** `0.14.0` · **Canon version:** unchanged at `0.8.0`
**External GitHub Actions has not run against this round.**

# PACK-14 — Security Verification

Every control task §28 names, where it is implemented, and how it is
tested. Where a control is a **deployment obligation** rather than
something this repository can discharge, it says so.

## 1. Controls implemented and tested

| Control                                 | Implementation                                                                                                                                 | Test                                                                                                                                                                                    |
| --------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Rate limiting                           | `authentication.RateLimitBucket`, per operation and subject                                                                                    | `test_a_rate_limit_bucket_refuses_past_its_limit_and_resets_per_window`                                                                                                                 |
| Brute-force resistance                  | `passwords.AuthenticationThrottleState`                                                                                                        | `test_repeated_failures_throttle_the_attempt_source`                                                                                                                                    |
| Account enumeration resistance          | `authentication.public_reason_code` + `NON_DISCLOSABLE_REASON_CODES`                                                                           | `test_no_public_response_discloses_account_state`                                                                                                                                       |
| Constant-shape public responses         | `issue_challenge` accepts an unknown account as a first-class input                                                                            | `test_a_challenge_is_issued_for_an_unknown_account_too`                                                                                                                                 |
| Challenge expiry                        | Every challenge type carries a mandatory `expires_at`                                                                                          | `test_step_up_freshness_is_the_governed_window` and others                                                                                                                              |
| Nonce uniqueness                        | `persistence.assert_nonce_unused`, store-wide                                                                                                  | `test_a_nonce_is_single_use_across_the_whole_store`                                                                                                                                     |
| Replay prevention                       | Bootstrap, handoff, refresh-token family, provider assertion                                                                                   | 4 named tests                                                                                                                                                                           |
| Secure random generation                | `secret_storage.SystemSecureRandom` (CSPRNG)                                                                                                   | The deterministic double is a separate class                                                                                                                                            |
| Token hashing at rest                   | `hash_token`; only digests are stored                                                                                                          | `test_a_voting_handoff_artifact_is_single_use`                                                                                                                                          |
| Token audience binding                  | Bootstrap and handoff both audience-bound                                                                                                      | `test_a_bootstrap_response_presented_to_another_workspace_is_refused`                                                                                                                   |
| Origin validation                       | `workspaces.assert_declared_origin`, `SessionScope`                                                                                            | `test_an_assertion_from_another_origin_is_refused`                                                                                                                                      |
| Redirect allowlist                      | `assert_redirect_allowlisted`, **exact match**                                                                                                 | `test_the_redirect_allowlist_is_exact_match` (3 adversarial URIs)                                                                                                                       |
| CSRF                                    | `SessionRecord.assert_csrf`                                                                                                                    | `test_a_state_changing_request_without_a_csrf_token_is_refused`                                                                                                                         |
| No secrets in logs                      | `observability.redact`, `assert_no_secret_in_log_line`                                                                                         | 2 tests                                                                                                                                                                                 |
| Audit minimization                      | Actor **classes** and scoped references, never identifiers                                                                                     | `test_a_recovery_event_names_signals_and_a_role_not_a_score_or_a_reviewer`                                                                                                              |
| Session invalidation                    | `revoke_session`, `revoke_all_sessions`                                                                                                        | `test_session_issue_list_and_revoke_all`                                                                                                                                                |
| Credential compromise workflow          | `revoke_credential` revokes sessions in the same command                                                                                       | `test_revoking_a_credential_revokes_the_sessions_it_could_have_produced`                                                                                                                |
| Dual control                            | `recovery.record_decision`, `administration`                                                                                                   | 3 tests                                                                                                                                                                                 |
| Reason-coded admin actions              | Every admin path carries a registered code                                                                                                     | `tests/contract/test_reason_codes_registry.py[pack-14]`                                                                                                                                 |
| No session identifier in a URL          | `refuse_session_identifier_in_url`                                                                                                             | `test_no_session_identifier_may_appear_in_a_url`                                                                                                                                        |
| Secure cookie attributes                | `SessionCookieAttributes`, unconstructible otherwise                                                                                           | 2 tests                                                                                                                                                                                 |
| **Breach check fails closed**           | `secret_storage.UnboundBreachedPasswordChecker` is the default and **raises**; no password may be enrolled or replaced without a bound checker | `test_an_unbound_breach_checker_refuses_password_enrollment`, `test_the_unbound_checker_never_returns_a_boolean`, `test_no_permissive_breached_password_checker_remains_in_the_package` |
| Degraded mode is bounded                | `PasswordDegradedModeDecision` permits **authentication only**; it has no field that could re-open enrollment                                  | `test_the_degraded_mode_decision_cannot_permit_enrollment`, `test_a_degraded_mode_decision_requires_an_authority_and_a_reason_code`                                                     |
| Durable replay prevention               | Nonce, idempotency and assertion-id records are written to the reference store, not held in a process                                          | `test_bootstrap_single_use_survives_a_restart`, `test_voting_handoff_replay_protection_survives_a_restart`                                                                              |
| Optimistic concurrency                  | `sql_storage` writes through `WHERE version < ?`; a stale write is refused                                                                     | `test_a_stale_write_is_refused_by_the_optimistic_concurrency_check`                                                                                                                     |
| Atomic multi-record operations          | `UnitOfWork` transaction boundary; a failed operation leaves no partial account, credential or session state                                   | `test_a_failed_transaction_leaves_no_partial_account_or_credential_state`, `test_a_failed_dispatch_rolls_back_and_leaves_no_partial_state`                                              |
| No secret or raw identifier at rest     | `codecs.encode_value` refuses `bytes`; only digests are persisted                                                                              | `test_no_stored_document_contains_a_secret_or_a_raw_contact` (sweeps every row of every table)                                                                                          |
| No secret or raw identifier on the wire | `assert_response_safe` runs in `ApiResponse.__post_init__`, so an unsafe response cannot be constructed                                        | `test_no_response_body_can_carry_a_prohibited_key`, `test_the_session_inventory_carries_no_token_and_no_account_id`                                                                     |
| Secure defaults at composition          | All four security ports default to adapters that refuse; no in-memory store is a runtime binding                                               | `tests/repository/test_pack14_default_binding.py` (9 tests)                                                                                                                             |

## 2. XSS-safe output

**A deployment obligation, and not discharged here.** This round builds
no rendering layer, so there is no output-encoding code to verify. The
FRONT-00/FRONT-01 baseline's own escaping remains in force and is
untouched. Recorded as an obligation rather than claimed as a control.

## 3. "Do not rely on the frontend for security enforcement"

Every control above is server-side. The only frontend-adjacent artefacts
this round produces are the governed content strings in `forms.py`, which
are text rather than enforcement — and `assert_governed_text` exists so a
UI cannot silently invent a consequential label instead.

## 4. The structural refusals

Beyond the control table, six functions exist purely so that an attempt
is a reason-coded, auditable refusal rather than a silent success:

| Function                                   | Refuses                                                |
| ------------------------------------------ | ------------------------------------------------------ |
| `voting_handoff.refuse_reverse_resolution` | Resolving a redemption back to an account              |
| `mappings.refuse_unrestricted_lookup`      | Enumerating mappings without a purpose and a scope     |
| `contacts.refuse_auto_merge`               | Merging two accounts by a shared contact value         |
| `passwords.refuse_security_question`       | Storing or evaluating a knowledge-based answer         |
| `proofing.refuse_membership_inference`     | Deriving a membership approval from a proofing verdict |
| `providers.refuse_subject_as_account_key`  | Using a provider subject as an account or join key     |

Each always raises. None has a parameter that makes it succeed.

## 5. Threats from the specification's §13 list

Phishing (origin binding, phishing-resistant method classes), credential
stuffing and spraying (rate limiting, throttling, and a breach boundary
that **refuses when unbound** rather than passing silently),
stolen session (rotation, deadlines, revocation), refresh-token replay
(family revocation), SIM swap (SMS OTP carries no assurance at all),
email compromise (email is `low`; recovery requires an independent
method), device theft (device-bound credential revocation revokes its
sessions), malicious recovery (cooling-off, dual control, out-of-band
notification), insider reset and support impersonation (separation of
duties, `SUPPORT_PROHIBITED`), cookie theft (host-scoped, `HttpOnly`,
`Secure`), CSRF (token check), session fixation (identifier rotation),
passkey removal abuse (`CREDENTIAL_LAST_REMAINING`, `high` + step-up),
MFA downgrade (assurance recomputation on removal), cross-origin leakage
(no parent-domain cookie, no reusable token) and correlation through
telemetry (metric label allowlist, disclosure floor).

**Not covered by this round:** shared-device risk and malicious browser
extensions, both of which are client-side and belong to the FRONT-PACK
round together with the rendering layer.

## 6. The one control that was wrong in the first candidate

The first candidate archive bound `NoBreachedPasswordChecker` by default:
a checker that reported nothing as breached. It was documented as an
unmet obligation, which is not the same as being safe — the failure would
have surfaced after a credential-stuffing incident rather than at
enrollment, and a control that fails open is worse than a control that is
absent, because it looks present.

It is removed. The default now raises `BREACH_CHECK_UNAVAILABLE`, both
booleans are refused (each would be a different lie), the deterministic
checker names itself a test double in its own docstring, and a test
asserts that the removed class has not returned to the package. The
governed degraded-mode decision permits authentication against an
**already stored** hash and has no field that could permit anything else.

**No new or changed password can bypass breach checking.**
