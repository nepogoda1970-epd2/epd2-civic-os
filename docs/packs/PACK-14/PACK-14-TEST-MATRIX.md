**Round:** PACK-14 — implementation candidate. **NOT PASS. NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**
**Repository version:** `0.14.0` · **Canon version:** unchanged at `0.8.0`

> **Superseding status note, added by the PACK-14 FINAL PASS round
> (2026-07-30).** The header above records the implementation-candidate
> round that wrote this document and is retained unchanged as the
> historical record. External GitHub Actions has since run against this
> exact tree and **passed every stage**, so PACK-14 is now **FINAL PASS**
> at `REPOSITORY_VERSION 0.14.0` / `CANON_VERSION 0.8.0`. The PASS changes
> the _round's_ status and nothing else: no limitation below is closed by
> it, and **NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.** See
> `docs/handover/PACK-14-FINAL-PASS-REPORT.md` and
> `docs/handover/PACK-14-EXTERNAL-CI-VERIFICATION-RESULT.md`.

# PACK-14 — Test Matrix

288 tests run in `services/identity-service/tests`, of which 248 are new
this round, plus 28 new repository-level tests and 4 new contract-suite
parametrizations. Full local suite: **4898 passed, 5 skipped**
(4618 at the PACK-13 FINAL PASS baseline, plus 280).

The correction round contributed 46 of the service tests and 14 of the
repository-level ones, and **removed or weakened none** of the rest.

## 1. Files

| File                                                      | Tests | Covers                                                     |
| --------------------------------------------------------- | ----- | ---------------------------------------------------------- |
| `test_pack14_unit.py`                                     | 46    | task §30.1                                                 |
| `test_pack14_invariants.py`                               | 62    | task §30.2 and the §37 acceptance blockers                 |
| `test_pack14_integration.py`                              | 23    | task §30.3                                                 |
| `test_pack14_security.py`                                 | 42    | task §30.4 and §30.5, plus the fail-closed breach boundary |
| `test_pack14_workflows.py`                                | 36    | recovery, proofing, linking, forms, events, persistence    |
| `test_pack14_persistence.py`                              | 22    | the reference persistence path (correction §1)             |
| `test_pack14_service_api.py`                              | 17    | the runnable reference boundary (correction §3)            |
| `tests/repository/test_pack14_duplicated_logic_parity.py` | 15    | the three deliberate duplications                          |
| `tests/repository/test_pack14_fir_matrix.py`              | 4     | the FIR matrix records no `implemented` treatment          |
| `tests/repository/test_pack14_default_binding.py`         | 9     | the in-memory adapters are not the default binding         |

288 tests in `services/identity-service` and 28 at the repository level.
No existing test was deleted or weakened by the correction round.

## 2. Task §30.1 — unit

| Requirement                 | Test                                                                                                          |
| --------------------------- | ------------------------------------------------------------------------------------------------------------- |
| account lifecycle           | `test_new_account_is_pending_and_activates_only_through_the_registry`                                         |
| lock/restriction separation | `test_a_lock_does_not_change_the_account_status`, `test_security_quarantine_is_a_restriction_not_a_status`    |
| contact normalization       | `test_email_normalization`, `test_phone_normalization_requires_e164`                                          |
| credential states           | `test_credential_state_refusals_are_distinct`                                                                 |
| password fallback policy    | `test_a_new_password_only_account_is_refused`, `test_password_authentication_always_requires_a_second_factor` |
| passkey classification      | `test_a_synced_passkey_never_reaches_high`, `test_a_synced_authenticator_is_classified_as_synced`             |
| assurance calculation       | `test_two_substantial_methods_do_not_add_up_to_high`                                                          |
| step-up freshness           | `test_step_up_freshness_is_the_governed_window`                                                               |
| object-version binding      | `test_a_changed_object_version_voids_the_confirmation`                                                        |
| session expiry              | `test_idle_and_absolute_deadlines_are_both_enforced`                                                          |
| session rotation            | `test_rotation_changes_the_session_identifier`                                                                |
| session revocation          | `test_a_revoked_session_cannot_refresh`                                                                       |
| recovery states             | `test_the_full_governed_recovery_workflow`                                                                    |
| dual control                | `test_high_assurance_recovery_requires_a_second_approver`                                                     |
| identity mapping scope      | `test_a_mapping_resolves_only_for_its_own_purpose_and_scope`                                                  |
| reason codes                | `tests/contract/test_reason_codes_registry.py[pack-14]` (4 tests)                                             |

## 3. Task §30.2 — property and invariant

Each acceptance blocker in task §37 that can be stated as a property has
a test. The mapping is one-to-one:

| §37 blocker                                   | Test                                                                                                                             |
| --------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| a global user ID appeared                     | `test_every_identifier_space_except_the_scoped_one_is_refused_at_a_boundary`, plus 41 parametrized key tests                     |
| account ID became a membership ID             | same, via `NEVER_CROSSES_A_BOUNDARY`                                                                                             |
| email became the account primary key          | `test_contact_uniqueness_is_scoped_and_never_merges`                                                                             |
| the Voting Client got an ordinary session     | `test_the_voting_client_is_never_issued_an_identity_session`                                                                     |
| a bootstrap token was reusable                | `test_a_bootstrap_response_is_single_use_and_audience_bound`                                                                     |
| the voting handoff disclosed identity         | `test_a_voting_handoff_artifact_carries_no_identifier_of_any_kind`                                                               |
| a password alone gave consequential authority | `test_password_alone_cannot_authorize_a_consequential_action`                                                                    |
| SMS OTP created an AAL                        | `test_sms_otp_produces_no_assurance_and_is_not_a_factor_class`                                                                   |
| a synced passkey gave AAL-3                   | `test_a_synced_passkey_cannot_produce_high_however_it_is_combined`                                                               |
| session revoke did not block refresh          | `test_a_revoked_session_cannot_refresh`                                                                                          |
| recovery allowed a unilateral takeover        | `test_a_reviewer_cannot_decide_a_case_they_initiated`, `test_a_support_agent_cannot_approve_a_recovery_or_revoke_a_credential`   |
| secrets reached an event or a log             | `test_no_event_type_can_carry_a_secret` (59 event types), `test_redaction_replaces_every_prohibited_value_including_nested_ones` |
| step-up was not object-version bound          | `test_a_changed_object_version_voids_the_confirmation`                                                                           |
| a cross-origin cookie broke isolation         | `test_no_parent_domain_cookie_can_be_constructed`                                                                                |
| the Master Register was rolled back           | see `PACK-14-IMPLEMENTATION-REPORT.md` §9                                                                                        |
| versions contradicted each other              | `scripts/verify_versions.py`, `packages/*/tests/test_version*`                                                                   |

## 4. Task §30.4 — API negative

Wrong audience, expired bootstrap, replay, stale version, insufficient
assurance, missing approval, recently changed contact, revoked
credential, restricted account, malformed WebAuthn data, invalid provider
assertion and identity-mapping scope violation each have a named test in
`test_pack14_security.py` or `test_pack14_integration.py`.

## 5. Task §30.5 — security

Account enumeration (3 tests), CSRF (2), open redirect (1 with 3
adversarial URIs), token leakage and cookie flags (3), log redaction (2),
rate limiting and throttling (3), replay (4 across bootstrap, handoff,
refresh token and provider assertion), session fixation (via rotation),
privilege escalation (5) and recovery takeover (3).

## 6. The correction round's eight requirements

Each of the eight things the correction round required a test to prove,
and the test that proves it. They are listed individually because "the
persistence is tested" is the kind of claim that is true of a test that
never opens a file.

| Requirement                                                  | Test                                                                                                                                                                                                                                                           |
| ------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| State survives recreating the application                    | `test_account_contact_and_credential_state_survive_recreating_the_application`, `test_a_session_survives_a_restart_with_both_deadlines_intact` — a **file-backed** database, closed and reopened                                                               |
| Migration apply and compatibility checks pass                | `test_applying_the_migrations_creates_the_schema_and_is_idempotent`, `test_the_schema_carries_the_declared_constraints_and_expiry_indexes`, `test_an_edited_applied_migration_is_refused_by_the_compatibility_check`, `test_an_unapplied_migration_is_refused` |
| Rollback leaves no partial account/credential/session state  | `test_a_failed_transaction_leaves_no_partial_account_or_credential_state`, `test_a_failed_dispatch_rolls_back_and_leaves_no_partial_state`                                                                                                                     |
| Optimistic concurrency rejects stale writes                  | `test_a_stale_write_is_refused_by_the_optimistic_concurrency_check`                                                                                                                                                                                            |
| Bootstrap and handoff replay protection survives a restart   | `test_bootstrap_single_use_survives_a_restart`, `test_voting_handoff_replay_protection_survives_a_restart`, `test_nonce_and_idempotency_records_survive_a_restart`, `test_an_idempotency_key_is_honoured_across_a_restart`                                     |
| An unbound breach checker refuses enrollment                 | `test_an_unbound_breach_checker_refuses_password_enrollment` (+ 5 more in `test_pack14_security.py` §"fails closed")                                                                                                                                           |
| API serialization carries no prohibited identifier or secret | `test_no_response_body_can_carry_a_prohibited_key`, `test_the_session_inventory_carries_no_token_and_no_account_id`, and `test_no_stored_document_contains_a_secret_or_a_raw_contact` for the at-rest half                                                     |
| In-memory stores are not the default runtime binding         | `tests/repository/test_pack14_default_binding.py` — 9 tests, checking both the composition root's source and a built runtime's actual fields, plus `test_the_runtime_binds_sql_stores_and_not_the_in_memory_ones`                                              |

## 7. What the tests do **not** establish

They exercise the reference implementation, not a deployment. No test
here proves that a real WebAuthn library verifies correctly, that a real
Argon2id binding is configured, or that any retention duration is lawful.

The persistence tests are honest about their own reach: they prove that
**the reference SQLite schema** enforces the unique constraints, applies
the migrations transactionally and survives a restart. They do not prove
that a production PostgreSQL deployment does, because no such deployment
exists in this repository. What they establish is that the constraints,
the indexes, the transaction boundaries and the concurrency guard are
real code that runs, rather than metadata describing code someone would
write later — which is precisely the distinction the correction round
existed to fix. Those are deployment obligations, and
`PACK-14-OPEN-ITEMS.md` records them as open rather than covered.
