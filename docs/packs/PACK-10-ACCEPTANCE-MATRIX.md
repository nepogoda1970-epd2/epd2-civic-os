# CLAUDE-PACK-10 — Implementation acceptance matrix

This document is the plan an implementation round is measured against.
It names, for every one of the fifty-five hard invariants in
`docs/packs/PACK-10-SPECIFICATION.md` section 6, at least one concrete
test that would prove it, together with the full planned path of the
file that test would live in, once `services/finance-service` exists.

Nothing here has been written. Every test named below is planned, not
implemented; no test file, no fixture and no `conftest.py` entry exists
yet for `finance-service`. No test was executed this round — this round
adds documentation only, exactly as
`docs/packs/PACK-10-SPECIFICATION.md` section 20 records. Reading a row
of this document as a claim that the referenced test currently passes,
or currently exists, would be a misreading.

Sections 1 through 6 below list the tests themselves, one row per
planned test, numbered continuously `AT-001` upward regardless of
which section they fall in: domain, application, storage, contract,
architecture and repository, in that order, matching specification
section 18 exactly. Section 7, the invariant coverage map, is the
section a reviewer of the eventual implementation round should check
most closely: it maps every hard-invariant number `HI-1` through
`HI-55` to the test id or ids that would prove it, and every row has
at least one entry, cross-checked against sections 1 through 6 so a
reviewer can follow either direction — from a test id to the
invariant it proves, or from an invariant to every test that proves
it — without the two views disagreeing. Section 8 states the gate
conditions an implementation round must meet before it may be called
complete, and is explicit that meeting them proves nothing about legal
compliance or production readiness — that determination belongs to
`docs/packs/PACK-10-SPECIFICATION.md` section 22, not to this
document.

Test paths follow the repository's existing conventions, the same ones
`services/compliance-service` and every earlier service already use:
`services/<name>/tests/test_domain.py`, `test_application.py`,
`test_storage.py` and `test_events.py` for service-level unit tests;
`tests/contract/test_ct00_*.py` for the shared CT-00 contract suite,
extended with a PACK-10 section inside each shared file where the
suite already iterates every service; and `tests/repository/` for
whole-repository structural checks such as `test_service_boundaries.py`
and `test_required_files.py`. Where a test id's planned path names a
function inside an existing shared file rather than a new one — every
`test_ct00_*` row and every `tests/repository/` row below — the
planned change is an added test function and, where the file already
loops over a list of services, an added entry in that list; it is not
a new file the implementation round must create from nothing.

## 1. Domain tests

These tests exercise the pure, I/O-free rules in `domain.py` and the
aggregate-local invariants of `ledger.py`, `contributions.py`,
`expenses.py`, `budgets.py`, `positions.py`, `reporting.py` and
`audit_engagement.py`, following specification section 18's list:
money and currency, balancing, journal immutability, reversal, period
close/reopen, contribution lifecycle, aggregation, sponsorship,
reimbursement, budgets, report lifecycle, audit independence and
restatement. Every test in this section is a constructor- or
state-machine-level test with no `application.py` guard involved; the
same rule re-checked at the command layer is proven again in section 2.

| Test id  | Planned test                                                                                                                          | What it asserts                                                                             | Invariant proven |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- | ---------------- |
| `AT-001` | `services/finance-service/tests/test_domain.py::test_money_refuses_mixed_currency_arithmetic`                                         | `Money` raises on cross-currency addition without a recorded conversion                     | `HI-8`           |
| `AT-002` | `services/finance-service/tests/test_domain.py::test_money_round_trips_through_integer_minor_units_without_precision_loss`            | Constructing, serializing and reconstructing `Money` never loses a minor unit               | `HI-9`           |
| `AT-003` | `services/finance-service/tests/test_domain.py::test_every_computed_amount_carries_its_scale_and_rounding_rule`                       | Every computed `Money` value records its scale and rounding rule explicitly                 | `HI-55`          |
| `AT-004` | `services/finance-service/tests/test_domain.py::test_an_unbalanced_entry_cannot_be_constructed_or_posted`                             | `assert_balanced` raises when debit and credit minor units differ for a currency            | `HI-7`           |
| `AT-005` | `services/finance-service/tests/test_domain.py::test_a_balanced_entry_spanning_three_currencies_posts_one_line_set_per_currency`      | Balancing is evaluated per currency, not across currencies                                  | `HI-7`           |
| `AT-006` | `services/finance-service/tests/test_domain.py::test_a_posted_journal_entry_cannot_be_edited_only_reversed`                           | `JournalEntry.posted` refuses every content mutation                                        | `HI-6`           |
| `AT-007` | `services/finance-service/tests/test_domain.py::test_a_reversal_entry_references_the_original_and_carries_a_reason_code`              | Reversal creates a new entry with an original-entry reference and a reason code             | `HI-6`           |
| `AT-008` | `services/finance-service/tests/test_domain.py::test_a_reversal_chain_is_append_only_and_cycle_free`                                  | Reversal chains cannot loop back to an earlier entry in the same chain                      | `HI-6`           |
| `AT-009` | `services/finance-service/tests/test_domain.py::test_an_accounting_period_moves_from_open_to_closing_to_closed_in_order`              | `AccountingPeriod` rejects any transition skipping `closing`                                | `HI-10`          |
| `AT-010` | `services/finance-service/tests/test_domain.py::test_reopening_preserves_the_closed_state_and_requires_authority`                     | Reopening produces a `PeriodReopeningRecord` and requires a distinct authority              | `HI-11`          |
| `AT-011` | `services/finance-service/tests/test_domain.py::test_a_period_reopening_record_snapshots_the_prior_closed_state`                      | The reopening record freezes the exact closed-state values, not a live reference            | `HI-11`          |
| `AT-012` | `services/finance-service/tests/test_domain.py::test_a_naive_datetime_is_refused_everywhere_a_period_boundary_is_computed`            | `require_timezone` rejects a naive `datetime` on every period boundary computation          | `HI-42`          |
| `AT-013` | `services/finance-service/tests/test_domain.py::test_an_unverifiable_contribution_lands_in_quarantine_not_accepted`                   | An unverifiable contribution's default landing state is `quarantined`, never `accepted`     | `HI-16`          |
| `AT-014` | `services/finance-service/tests/test_domain.py::test_acceptance_requires_a_resolved_policy_bound_assessment`                          | `Contribution` cannot reach `accepted` without a resolved, policy-bound assessment          | `HI-17`          |
| `AT-015` | `services/finance-service/tests/test_domain.py::test_the_original_receipt_survives_return_rejection_and_escalation`                   | The create-once receipt is unchanged after every later decision on the same contribution    | `HI-18`          |
| `AT-016` | `services/finance-service/tests/test_domain.py::test_an_in_kind_contribution_without_a_valuation_basis_is_refused`                    | `InKindValuation` is mandatory for every non-monetary contribution                          | `HI-19`          |
| `AT-017` | `services/finance-service/tests/test_domain.py::test_four_split_contributions_aggregate_to_one_threshold_evaluation`                  | Four contributions under the threshold aggregate to one evaluation that crosses it          | `HI-14`          |
| `AT-018` | `services/finance-service/tests/test_domain.py::test_a_declared_intermediary_chain_aggregates_with_its_principal`                     | A declared `intermediary_declaration` extends the aggregation key to the principal          | `HI-15`          |
| `AT-019` | `services/finance-service/tests/test_domain.py::test_a_past_assessment_is_not_recomputed_against_a_later_policy_version`              | A frozen `AggregationSnapshot` is not silently re-evaluated when policy changes             | `HI-14`          |
| `AT-020` | `services/finance-service/tests/test_domain.py::test_sponsorship_without_counter_performance_needs_an_explicit_policy_classification` | Approval without counter-performance requires an explicit policy classification             | `HI-20`          |
| `AT-021` | `services/finance-service/tests/test_domain.py::test_a_sponsorship_disclosure_class_cannot_be_lowered_to_escape_publication`          | Disclosure reclassification downward is refused when it would drop an obligation            | `HI-13`          |
| `AT-022` | `services/finance-service/tests/test_domain.py::test_an_external_financial_benefit_without_a_valuation_basis_is_refused`              | `ExternalFinancialBenefit` refuses recording without a valuation basis                      | `HI-19`          |
| `AT-023` | `services/finance-service/tests/test_domain.py::test_the_claimant_cannot_approve_or_execute_their_own_reimbursement`                  | `assert_not_self_approval` raises when the claimant is the approver or executor             | `HI-32`          |
| `AT-024` | `services/finance-service/tests/test_domain.py::test_a_payment_authorization_cannot_share_its_authorizer_and_executor`                | `PaymentAuthorization` refuses construction when authorizer equals executor                 | `HI-32`          |
| `AT-025` | `services/finance-service/tests/test_domain.py::test_a_settled_expense_claim_cannot_be_edited_only_corrected`                         | `ExpenseClaim.settled` refuses edits; a correction creates a new correcting record          | `HI-6`           |
| `AT-026` | `services/finance-service/tests/test_domain.py::test_a_budget_line_never_stores_an_actual_amount`                                     | `BudgetLine` has no field an actual ledger amount could be written into                     | `HI-12`          |
| `AT-027` | `services/finance-service/tests/test_domain.py::test_an_approved_budget_version_cannot_be_edited_only_amended_by_a_new_version`       | An `approved` `BudgetVersion` refuses edits; amendment creates a new version                | `HI-6`           |
| `AT-028` | `services/finance-service/tests/test_domain.py::test_a_report_snapshot_is_write_once_and_survives_every_later_version`                | `ReportSnapshot` is create-once and unaffected by later `FinanceReportVersion` records      | `HI-25`          |
| `AT-029` | `services/finance-service/tests/test_domain.py::test_an_amendment_creates_a_new_version_and_leaves_the_submitted_one_intact`          | Amending a submitted report creates a new version without touching the submitted one        | `HI-26`          |
| `AT-030` | `services/finance-service/tests/test_domain.py::test_submission_alone_never_reaches_accepted_by_authority`                            | `submitted` and `accepted_by_authority` remain distinct states without a further act        | `HI-27`          |
| `AT-031` | `services/finance-service/tests/test_domain.py::test_no_delivery_telemetry_field_can_drive_a_report_transition`                       | No telemetry field is read as input by any `FinanceReport` state transition                 | `HI-28`          |
| `AT-032` | `services/finance-service/tests/test_domain.py::test_publication_does_not_imply_approval_and_vice_versa`                              | Publication and approval are independent facts on `FinanceReportVersion`                    | `HI-29`          |
| `AT-033` | `services/finance-service/tests/test_domain.py::test_a_reorganization_leaves_a_submitted_periods_perimeter_untouched`                 | A snapshotted `PerimeterSnapshot` on a submitted version ignores later hierarchy changes    | `HI-54`          |
| `AT-034` | `services/finance-service/tests/test_domain.py::test_the_engagement_authority_and_the_candidate_authority_must_differ`                | `assert_auditor_independent` raises when engagement and candidate authority are the same    | `HI-30`          |
| `AT-035` | `services/finance-service/tests/test_domain.py::test_the_prepared_by_authority_cannot_also_conclude_the_engagement`                   | `assert_auditor_independent` raises when the report preparer is also the concluding auditor | `HI-30`          |
| `AT-036` | `services/finance-service/tests/test_domain.py::test_a_declared_conflict_of_interest_blocks_engagement_conclusion`                    | A declared, blocking conflict on the auditor refuses conclusion                             | `HI-30`          |
| `AT-037` | `services/finance-service/tests/test_domain.py::test_independence_is_rechecked_at_every_recorded_finding`                             | Each `AuditFinding` re-runs `assert_auditor_independent`, not only engagement opening       | `HI-30`          |
| `AT-038` | `services/finance-service/tests/test_domain.py::test_the_same_legal_person_gets_unequal_handles_for_unequal_purposes`                 | Two purposes for the same legal person mint two unequal, non-linkable handles               | `HI-48`          |
| `AT-039` | `services/finance-service/tests/test_domain.py::test_a_finance_handle_cannot_be_correlated_to_any_participation_reference`            | A `FinancePartyHandle` carries nothing derivable from any participation identifier          | `HI-38`          |

This section lists 39 planned tests, `AT-001` through `AT-039`, all
under `services/finance-service/tests/test_domain.py`. Together they
cover every aggregate `domain.py`, `ledger.py`, `contributions.py`,
`expenses.py`, `budgets.py`, `reporting.py` and `audit_engagement.py`
own, at the level where no command, no store and no scope guard is
involved — the pure rule itself, proven once, before section 2 proves
the command layer cannot route around it.

## 2. Application tests

These tests exercise `application.py`: the command layer that resolves
authority, re-checks scope, re-checks conflict state, re-checks legal
hold, binds a policy version, and appends to Audit Core, following
specification section 18's list — authority checks, conflict checks,
scope isolation, fail-closed cases, legal-hold checks, policy binding,
deadline and notice references, cross-scope consolidation, and derived
public projections. Where section 1 proves a rule holds inside one
aggregate's constructor, this section proves the same rule cannot be
bypassed by any of the several command paths that reach it.

| Test id  | Planned test                                                                                                                                                | What it asserts                                                                                              | Invariant proven |
| -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ | ---------------- |
| `AT-040` | `services/finance-service/tests/test_application.py::test_an_undetermined_scope_denies_before_any_other_check`                                              | Scope resolution runs before every other guard and denies when it cannot resolve                             | `HI-4`           |
| `AT-041` | `services/finance-service/tests/test_application.py::test_a_finance_command_targeting_a_foreign_scope_reports_not_found`                                    | A command against another scope's record reports it as not found, not as forbidden                           | `HI-3`           |
| `AT-042` | `services/finance-service/tests/test_application.py::test_a_closed_period_refuses_every_ordinary_posting_path`                                              | Every ordinary posting command re-checks the period lock, not only intake                                    | `HI-10`          |
| `AT-043` | `services/finance-service/tests/test_application.py::test_reclassification_that_would_drop_a_disclosure_obligation_is_refused`                              | `reclassify_*` refuses a target class that would drop an attached obligation                                 | `HI-13`          |
| `AT-044` | `services/finance-service/tests/test_application.py::test_an_auditor_who_administers_the_same_scope_is_refused`                                             | Authority resolution refuses a candidate holding both `finance_auditor` and `finance_administrator` in scope | `HI-31`          |
| `AT-045` | `services/finance-service/tests/test_application.py::test_a_matching_role_code_string_alone_never_authorizes_a_finance_action`                              | A `role_code` string match without a resolved `OrganizationalAuthority` record is refused                    | `HI-53`          |
| `AT-046` | `services/finance-service/tests/test_application.py::test_an_undeclared_conflict_fails_closed_on_every_protected_action`                                    | An `undeclared` conflict state raises rather than defaulting to `none`                                       | `HI-33`          |
| `AT-047` | `services/finance-service/tests/test_application.py::test_a_hold_placed_after_authorization_still_blocks_a_finance_disposal`                                | The PACK-09 hold state is re-read immediately before disposal, never cached                                  | `HI-23`          |
| `AT-048` | `services/finance-service/tests/test_application.py::test_superseding_a_finance_retention_binding_does_not_shorten_an_active_obligation`                    | Rebinding to a new retention policy version cannot shorten a standing obligation                             | `HI-24`          |
| `AT-049` | `services/finance-service/tests/test_application.py::test_the_four_report_actions_are_four_records_with_four_authorities`                                   | Preparation, approval, sign-off and audit review each record a distinct authority reference                  | `HI-34`          |
| `AT-050` | `services/finance-service/tests/test_application.py::test_an_auditor_engagement_opened_by_the_finance_administrator_is_refused`                             | Opening an `AuditEngagement` as `finance_administrator` in the same scope is refused                         | `HI-30`, `HI-31` |
| `AT-051` | `services/finance-service/tests/test_application.py::test_independence_is_rechecked_at_the_moment_of_auditor_review_not_only_at_engagement_opening`         | The auditor-review command re-verifies independence at review time                                           | `HI-30`          |
| `AT-052` | `services/finance-service/tests/test_application.py::test_consolidation_cannot_write_into_a_lower_scope`                                                    | Consolidation reads lower-scope records and writes only its own `ConsolidationRecord`                        | `HI-39`          |
| `AT-053` | `services/finance-service/tests/test_application.py::test_a_small_cell_view_is_suppressed_or_aggregated_before_emission`                                    | A view breaching the minimum cell-size rule is suppressed or re-aggregated before emission                   | `HI-36`          |
| `AT-054` | `services/finance-service/tests/test_application.py::test_a_reopening_approver_may_not_be_the_actor_who_requested_it`                                       | The `reopen_accounting_period` approver is compared against the requesting actor                             | `HI-32`          |
| `AT-055` | `services/finance-service/tests/test_application.py::test_a_fixed_clock_is_all_a_command_ever_reads`                                                        | Every command reads time only through an injected `epd2_core.clock.Clock`                                    | `HI-49`          |
| `AT-056` | `services/finance-service/tests/test_application.py::test_an_unknown_policy_version_fails_closed_before_the_operation_proceeds`                             | `FINANCE_POLICY_VERSION_UNKNOWN` raises before any read or write proceeds                                    | `HI-44`          |
| `AT-057` | `services/finance-service/tests/test_application.py::test_an_undetermined_reporting_perimeter_fails_closed`                                                 | `FINANCE_REPORTING_PERIMETER_UNDETERMINED` raises when no effective definition exists                        | `HI-44`          |
| `AT-058` | `services/finance-service/tests/test_application.py::test_a_missing_finance_authority_fails_closed`                                                         | `FINANCE_AUTHORITY_MISSING` raises when no active scope-matching authority resolves                          | `HI-44`          |
| `AT-059` | `services/finance-service/tests/test_application.py::test_a_report_status_that_cannot_be_determined_fails_closed`                                           | `FINANCE_REPORT_STATUS_UNKNOWN` raises rather than defaulting to a permissive status                         | `HI-44`          |
| `AT-060` | `services/finance-service/tests/test_application.py::test_no_invariant_check_reads_a_feature_flag`                                                          | No invariant-check function accepts or reads a feature-flag value                                            | `HI-45`          |
| `AT-061` | `services/finance-service/tests/test_application.py::test_a_self_benefit_disposal_of_a_financial_asset_to_a_related_party_is_refused`                       | Disposal to a related party of the deciding authority is refused                                             | `HI-32`          |
| `AT-062` | `services/finance-service/tests/test_application.py::test_a_declared_related_party_settlement_requires_dual_control`                                        | Settlement to a declared related party requires the second authority the policy names                        | `HI-32`          |
| `AT-063` | `services/finance-service/tests/test_application.py::test_the_audit_chain_stays_verifiable_across_a_full_report_workflow`                                   | The Audit Core chain verifies end to end across a complete report preparation-to-publication flow            | `HI-52`          |
| `AT-064` | `services/finance-service/tests/test_application.py::test_every_protected_action_records_the_finance_policy_binding_it_used`                                | Every protected decision records the exact policy id and version used                                        | `HI-44`          |
| `AT-065` | `services/finance-service/tests/test_application.py::test_a_deadline_reference_is_attached_to_every_contribution_return_obligation`                         | `finance_contribution.return_required` carries a `DeadlineRef` for the statutory return period               | `HI-42`          |
| `AT-066` | `services/finance-service/tests/test_application.py::test_a_notice_effect_reference_is_the_only_path_to_accepted_by_authority`                              | Only a recorded `NoticeEffectRef` moves a report version to `accepted_by_authority`                          | `HI-27`          |
| `AT-067` | `services/finance-service/tests/test_application.py::test_a_correction_owed_by_a_procedural_deadline_cites_the_deadline_reference`                          | A correction command triggered by a deadline cites the `DeadlineRef` on the record                           | `HI-42`          |
| `AT-068` | `services/finance-service/tests/test_application.py::test_the_reviewer_approver_and_authorizer_of_an_expense_claim_must_be_three_distinct_authorities`      | An `ExpenseClaim` command refuses when two of the three roles share an actor                                 | `HI-32`          |
| `AT-069` | `services/finance-service/tests/test_application.py::test_a_write_off_below_the_policy_threshold_does_not_require_the_second_authority`                     | Dual control is required only where the bound policy sets a threshold that applies                           | `HI-32`          |
| `AT-070` | `services/finance-service/tests/test_application.py::test_a_scope_isolation_check_precedes_every_conflict_check_in_guard_order`                             | Scope resolution is ordered before conflict-of-interest evaluation in every command                          | `HI-4`           |
| `AT-071` | `services/finance-service/tests/test_application.py::test_a_cross_scope_consolidation_authority_is_resolved_through_organization_service_not_a_role_string` | Consolidation authority is a resolved `OrganizationalAuthority`, never a string                              | `HI-39`, `HI-53` |

This section lists 32 planned tests, `AT-040` through `AT-071`, all
under `services/finance-service/tests/test_application.py`. Every row
proves that the guard order in `application.py` — scope, then
authority, then conflict, then legal hold, then policy binding —
holds on every command path that reaches a protected action, not only
on the one path each domain-level test in section 1 exercised.

## 3. Storage tests

These tests exercise `storage.py`: one `Protocol` per aggregate plus
the in-memory reference adapter, following specification section 18's
list — append-only history, create-once records, no delete methods,
optimistic concurrency, scope-aware lookup and import idempotency. A
storage-layer test proves the store itself refuses the forbidden
operation regardless of what `application.py` would otherwise permit.

| Test id  | Planned test                                                                                                                             | What it asserts                                                                                 | Invariant proven |
| -------- | ---------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- | ---------------- |
| `AT-072` | `tests/repository/test_service_boundaries.py::test_finance_service_storage_exposes_no_delete_operation`                                  | No adapter method in `finance-service/storage.py` deletes a record                              | `HI-5`           |
| `AT-073` | `services/finance-service/tests/test_storage.py::test_the_finance_store_protocols_expose_no_delete_method_on_any_protocol`               | No `Protocol` for any aggregate declares a delete method signature                              | `HI-5`           |
| `AT-074` | `services/finance-service/tests/test_storage.py::test_a_stale_expected_version_is_refused_on_every_mutable_aggregate`                    | Every mutable aggregate's write refuses a stale `expected_*_version`                            | `HI-51`          |
| `AT-075` | `services/finance-service/tests/test_storage.py::test_scoped_queries_never_return_a_foreign_scope_record`                                | A scoped lookup returns nothing for a record outside the asserted scope                         | `HI-3`           |
| `AT-076` | `services/finance-service/tests/test_storage.py::test_an_imported_transaction_without_a_batch_and_provenance_is_refused`                 | The store refuses to persist a `FinancialTransaction` lacking an `ImportBatch` reference        | `HI-40`          |
| `AT-077` | `services/finance-service/tests/test_storage.py::test_provenance_fields_are_immutable_after_intake`                                      | Provenance fields on a stored transaction have no update path after `recorded`                  | `HI-40`          |
| `AT-078` | `tests/contract/test_ct00_04_event_idempotency.py::test_the_same_batch_imported_twice_is_detected_not_duplicated`                        | Reapplying a batch with a matching fingerprint is detected, not silently duplicated             | `HI-41`          |
| `AT-079` | `services/finance-service/tests/test_storage.py::test_a_reconciliation_record_cannot_be_edited_once_recorded`                            | `ReconciliationRecord` has no update method; a new reconciliation is a new record               | `HI-6`           |
| `AT-080` | `services/finance-service/tests/test_storage.py::test_a_period_reopening_record_is_create_once_per_reopening`                            | `PeriodReopeningRecord` is written exactly once per reopening event, never revised              | `HI-11`          |
| `AT-081` | `services/finance-service/tests/test_storage.py::test_a_payment_authorization_is_create_once_with_exactly_one_execution_record`          | `PaymentAuthorization` accepts exactly one execution write, never a second                      | `HI-32`          |
| `AT-082` | `services/finance-service/tests/test_storage.py::test_append_only_history_entries_cannot_be_removed_from_a_contribution`                 | The `Contribution` store refuses any operation that shortens the decision history               | `HI-18`          |
| `AT-083` | `services/finance-service/tests/test_storage.py::test_a_submitted_or_published_report_version_has_no_update_path`                        | A `FinanceReportVersion` carrying a `SubmissionRecord` or `PublicationRecord` cannot be updated | `HI-26`          |
| `AT-084` | `services/finance-service/tests/test_storage.py::test_an_audit_finding_and_conclusion_cannot_be_edited_after_recording`                  | `AuditFinding` and `AuditConclusion` writes are append-only, never in-place edits               | `HI-30`          |
| `AT-085` | `services/finance-service/tests/test_storage.py::test_a_report_snapshot_has_no_update_method_on_its_store_protocol`                      | The `ReportSnapshot` `Protocol` declares no method that could mutate a frozen snapshot          | `HI-25`          |
| `AT-086` | `services/finance-service/tests/test_storage.py::test_a_finance_party_handle_record_has_no_update_method_beyond_merge_and_retire`        | `FinancePartyHandle` storage exposes only mint, merge and retire, nothing else                  | `HI-48`          |
| `AT-087` | `services/finance-service/tests/test_storage.py::test_an_applied_import_batch_cannot_be_reapplied_without_an_explicit_override_decision` | An `applied` batch's fingerprint reuse is refused without an explicit override                  | `HI-41`          |

This section lists 16 planned tests, `AT-072` through `AT-087`, split
between `services/finance-service/tests/test_storage.py` and one
shared `tests/repository/` and one shared `tests/contract/` row for
the two checks — no delete method, and duplicate-import detection —
that the repository already proves the same way for every other
service, rather than reinventing a finance-specific mechanism for
either.

## 4. Contract tests

These tests exercise `contracts/schemas/`, `contracts/openapi/`,
`contracts/events/` and the shared CT-00 suite in `tests/contract/`,
following specification section 18's list — JSON Schema, OpenAPI, enum
stability, event-envelope compatibility, money serialization, absence
of prohibited identity fields, absence of document content, and
absence of vote-linkable fields. Several of these extend an existing
shared CT-00 file with a PACK-10 section, the same pattern PACK-08 and
PACK-09 already use for their own sections of those files.

| Test id  | Planned test                                                                                                                            | What it asserts                                                                                        | Invariant proven |
| -------- | --------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ | ---------------- |
| `AT-088` | `tests/contract/test_ct00_01_pack10_schema_validation.py::test_every_finance_entity_schema_matches_its_dataclass`                       | Every finance entity JSON Schema is structurally consistent with its `domain.py`/`ledger.py` dataclass | `HI-55`          |
| `AT-089` | `tests/contract/test_ct00_01_pack10_schema_validation.py::test_no_finance_schema_exposes_a_document_content_field`                      | No schema declares a byte, hash-chain or signature field for evidence content                          | `HI-22`          |
| `AT-090` | `tests/contract/test_ct00_01_pack10_schema_validation.py::test_no_finance_schema_exposes_a_compliance_or_readiness_claim_field`         | No schema declares `is_compliant`, `is_production_ready` or an equivalent field                        | `HI-46`          |
| `AT-091` | `tests/contract/test_ct00_08_identity_leakage.py::test_pack10_section_no_dataclass_carries_a_person_or_member_identifier`               | Exhaustive scan over every finance dataclass finds no identity-shaped field                            | `HI-1`           |
| `AT-092` | `tests/contract/test_ct00_09_vote_linkability.py::test_pack10_section_no_finance_schema_property_is_vote_shaped`                        | No schema property resembles a ballot, tally, delegation or eligibility credential field               | `HI-37`          |
| `AT-093` | `tests/contract/test_property_based.py::test_money_amounts_round_trip_as_integer_minor_units_under_random_inputs`                       | Property-based generation of `Money` values round-trips through JSON without precision loss            | `HI-9`           |
| `AT-094` | `tests/contract/test_openapi_contract.py::test_money_fields_reject_the_json_number_type`                                                | Every monetary field's schema type excludes JSON `number`, requiring an integer envelope               | `HI-9`           |
| `AT-095` | `tests/contract/test_openapi_contract.py::test_pack10_no_delete_method_exists_for_any_governed_resource`                                | No operation tagged `finance-service` in `contracts/openapi/pack-10.yaml` is a DELETE method           | `HI-5`           |
| `AT-096` | `tests/contract/test_ct00_02_unknown_status.py::test_pack10_section_an_unknown_status_value_is_rejected_by_every_enum`                  | Every finance status enum rejects a value outside its declared set                                     | `HI-44`          |
| `AT-097` | `tests/contract/test_ct00_03_forbidden_transition.py::test_pack10_section_every_forbidden_transition_in_section_8_is_rejected`          | Every forbidden transition table in specification section 8 is exercised and rejected                  | `HI-6`           |
| `AT-098` | `tests/contract/test_ct00_05_unsupported_event_version.py::test_pack10_section_an_unsupported_finance_event_version_is_rejected`        | A finance event carrying an unsupported `event_version` is rejected, not coerced                       | `HI-52`          |
| `AT-099` | `tests/contract/test_ct00_06_missing_permission.py::test_pack10_section_a_command_without_the_required_permission_is_refused`           | A finance command lacking the required permission is refused before any side effect                    | `HI-53`          |
| `AT-100` | `tests/contract/test_ct00_07_audit_creation.py::test_pack10_section_every_critical_finance_action_appends_a_before_after_hash_pair`     | Every critical finance action produces an Audit Core entry with canonical hashes                       | `HI-52`          |
| `AT-101` | `tests/contract/test_ct00_04_event_idempotency.py::test_a_replayed_finance_command_with_the_same_event_id_returns_the_recorded_result`  | A retried command with the same caller-supplied `event_id` returns the prior result                    | `HI-50`          |
| `AT-102` | `tests/contract/test_ct00_10_rule_freeze.py::test_pack10_section_a_frozen_finance_policy_version_cannot_change_its_evaluation_result`   | An `active` `FinancePolicy` version's evaluation result cannot drift after freezing                    | `HI-44`          |
| `AT-103` | `tests/contract/test_ct00_11_ai_human_control.py::test_pack10_section_no_finance_decision_is_made_by_an_unsupervised_automated_process` | Every protected finance decision cites a resolved human authority reference                            | `HI-53`          |
| `AT-104` | `tests/contract/test_state_transitions.py::test_pack10_section_every_documented_lifecycle_transition_matches_the_specification_table`   | The implemented state machines match specification section 8's transition tables                       | `HI-34`          |
| `AT-105` | `tests/contract/test_openapi_contract.py::test_every_pack10_operation_is_tagged_finance_service`                                        | Every operation `contracts/openapi/pack-10.yaml` defines carries the `finance-service` tag             | `HI-47`          |

This section lists 18 planned tests, `AT-088` through `AT-105`, all
inside the shared `tests/contract/` suite. Ten of the eighteen extend
an existing CT-00 file that already iterates every service with a
new PACK-10 section, the same pattern PACK-08's and PACK-09's own
sections in those files already establish; the remaining eight extend
`test_property_based.py`, `test_openapi_contract.py` and
`test_state_transitions.py` in the same way.

## 5. Architecture tests

These tests exercise the repository's structural rules: the import
graph, the module-boundary rules ADR-044 fixes, and the absence of
modules PACK-10 must not contain, following specification section 18's
list — forbidden imports, direct storage access prohibition,
identity-service isolation, voting-service isolation, PACK-09
reference-only integration, PACK-11 placeholder-only integration,
PACK-35 non-implementation, and no prohibited payload in finance
events. This section also carries the four module-boundary rules
specification section 7 calls load-bearing: `budgets.py` may not
import a ledger store, `projections.py` may perform no authoritative
write, `audit_engagement.py` may not write to any aggregate it audits,
and `partyregistry.py` is the only module that may resolve a handle.

| Test id  | Planned test                                                                                                                                         | What it asserts                                                                                      | Invariant proven |
| -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- | ---------------- |
| `AT-106` | `tests/repository/test_service_boundaries.py::test_finance_service_imports_only_shared_packages`                                                     | `finance-service` imports only `epd2_core` and `epd2_audit_core` from `src/`                         | `HI-47`          |
| `AT-107` | `tests/repository/test_service_boundaries.py::test_no_finance_service_import_edge_into_identity_service_or_credential_service`                       | No AST import node in `finance-service` names `epd2_identity_service` or `epd2_credential_service`   | `HI-1`           |
| `AT-108` | `tests/repository/test_service_boundaries.py::test_no_finance_service_import_edge_into_voting_service_or_tally_service`                              | No AST import node in `finance-service` names `epd2_voting_service` or `epd2_tally_service`          | `HI-37`          |
| `AT-109` | `tests/repository/test_service_boundaries.py::test_finance_service_reads_pack09_facts_only_through_typed_references_never_by_import`                 | No import edge into `epd2_compliance_service`; only typed references cross the boundary              | `HI-24`          |
| `AT-110` | `tests/repository/test_service_boundaries.py::test_pack11_evidence_references_are_placeholder_shaped_with_no_document_content_import`                | `FinanceEvidenceReference` carries owner, kind, external reference and scope only                    | `HI-22`          |
| `AT-111` | `tests/repository/test_service_boundaries.py::test_no_pack35_lobbying_entity_exists_in_finance_service`                                              | No meeting, contact, calendar or access entity exists anywhere in `finance-service`                  | `HI-21`          |
| `AT-112` | `services/finance-service/tests/test_events.py::test_no_finance_event_payload_carries_identity_or_bank_detail`                                       | No event payload builder accepts a name, address or bank-account field                               | `HI-2`           |
| `AT-113` | `tests/repository/test_service_boundaries.py::test_budget_module_has_no_ledger_write_import`                                                         | `budgets.py` has no import edge into any `ledger.py` store protocol                                  | `HI-12`          |
| `AT-114` | `tests/repository/test_service_boundaries.py::test_projections_module_performs_no_authoritative_write`                                               | `projections.py` calls no store's write method anywhere in its module                                | `HI-35`          |
| `AT-115` | `tests/repository/test_service_boundaries.py::test_audit_engagement_module_has_no_write_import_into_any_aggregate_it_audits`                         | `audit_engagement.py` has no write-path import into `ledger.py`, `contributions.py` or `expenses.py` | `HI-30`          |
| `AT-116` | `tests/repository/test_service_boundaries.py::test_only_partyregistry_module_may_resolve_a_finance_party_handle`                                     | No module other than `partyregistry.py` calls the handle-resolution function                         | `HI-1`           |
| `AT-117` | `tests/repository/test_service_boundaries.py::test_no_finance_service_import_edge_into_deliberation_service`                                         | No AST import node in `finance-service` names `epd2_deliberation_service`                            | `HI-38`          |
| `AT-118` | `tests/repository/test_service_boundaries.py::test_no_finance_event_type_collides_with_an_existing_pack02_pack03_pack04_event_type`                  | No `finance_*` or `finance-prefixed` event type string matches an existing event type                | `HI-2`           |
| `AT-119` | `tests/repository/test_service_boundaries.py::test_no_finance_reason_code_collides_with_an_existing_code_of_different_semantics`                     | No `FINANCE_*` code in `pack-10.yml` collides with an existing code's meaning                        | `HI-43`          |
| `AT-120` | `tests/repository/test_service_boundaries.py::test_finance_service_has_no_import_dependency_on_any_service_other_than_epd2_core_and_epd2_audit_core` | The full N x N import matrix confirms `finance-service` has exactly two outbound edges               | `HI-47`          |
| `AT-121` | `tests/repository/test_service_boundaries.py::test_no_finance_module_imports_a_document_byte_storage_or_hash_chain_module`                           | No `finance-service` module imports a byte-content or hash-chain module                              | `HI-22`          |
| `AT-122` | `tests/repository/test_service_boundaries.py::test_partyregistry_module_is_the_only_import_path_to_the_handle_resolution_function`                   | The handle-resolution function's only importer across the whole service is `partyregistry.py`        | `HI-1`           |
| `AT-123` | `tests/repository/test_service_boundaries.py::test_no_finance_module_grants_write_authority_into_a_lower_organizational_scope`                       | No consolidation or reporting write path targets a scope lower than the caller's own                 | `HI-39`          |

This section lists 18 planned tests, `AT-106` through `AT-123`, all
inside `tests/repository/test_service_boundaries.py` except one,
`AT-112`, which lives with the event builders it exercises in
`services/finance-service/tests/test_events.py`. Every row here
walks the actual `import`/`from ... import` AST nodes finance-service
would contain, the same way the existing PACK-02 through PACK-09
sections of that file already do for their own services — never a
text or docstring match, so a comment mentioning another service's
name is never a false positive and never a false negative either.

## 6. Repository tests

These tests exercise the whole-repository conventions in
`tests/repository/`: expected paths, the reason-code registry, the ADR
index, version consistency, `README.md`/`CHANGELOG.md` consistency,
and the absence of generated or cache artifacts. Most of these already
exist as parametrized suites that iterate every service and every
registry file; PACK-10's row is an added case inside an existing test,
not a new file, in every instance below except the reason-code-specific
ones the new `pack-10.yml` registry requires.

| Test id  | Planned test                                                                                                                    | What it asserts                                                                                             | Invariant proven |
| -------- | ------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- | ---------------- |
| `AT-124` | `tests/repository/test_required_files.py::test_no_required_paths_are_missing`                                                   | `finance-service`'s required paths are present in `scripts/check_repository.py`'s manifest                  | `HI-47`          |
| `AT-125` | `tests/repository/test_required_files.py::test_finance_service_required_paths_are_all_present`                                  | Every module listed in specification section 7's ownership table exists as a file                           | `HI-47`          |
| `AT-126` | `tests/contract/test_reason_codes_registry.py::test_pack10_reason_codes_registry_loads_and_validates`                           | `contracts/reason-codes/pack-10.yml` parses and validates against the registry schema                       | `HI-43`          |
| `AT-127` | `tests/contract/test_reason_codes_registry.py::test_every_pack10_reason_code_has_all_seven_mandatory_fields`                    | Every entry has `code`, `meaning`, `severity`, `description`, `retryable`, `owner`, `introduced_in_version` | `HI-43`          |
| `AT-128` | `tests/contract/test_reason_codes_registry.py::test_no_pack10_reason_code_duplicates_an_existing_code_with_different_semantics` | No new `FINANCE_*` code duplicates the meaning of an existing code from another pack                        | `HI-43`          |
| `AT-129` | `tests/repository/test_version_consistency.py::test_the_adr_index_lists_every_accepted_and_proposed_adr_without_gaps`           | `docs/adr/README.md` lists ADR-044 through ADR-049 with no numbering gap                                    | `HI-43`          |
| `AT-130` | `tests/repository/test_version_consistency.py::test_repository_version_and_canon_version_agree_across_every_declared_file`      | `REPOSITORY_VERSION` and `CANON_VERSION` agree across every file that declares them                         | `HI-44`          |
| `AT-131` | `tests/repository/test_version_consistency.py::test_readme_and_changelog_agree_on_the_current_repository_version`               | `README.md` and `CHANGELOG.md` state the same `REPOSITORY_VERSION`                                          | `HI-43`          |
| `AT-132` | `tests/repository/test_forbidden_paths.py::test_no_generated_or_cache_artifact_exists_under_services_finance_service`           | No `__pycache__`, `.pyc` or build artifact exists under `services/finance-service`                          | `HI-47`          |
| `AT-133` | `tests/contract/test_reason_codes_registry.py::test_pack10_every_operation_documents_at_least_one_reason_coded_denial`          | Every `finance-service` operation has at least one documented reason-coded refusal path                     | `HI-43`          |
| `AT-134` | `tests/repository/test_service_boundaries.py::test_finance_service_directory_structure_matches_the_module_ownership_table`      | The file layout under `services/finance-service/src/` matches specification section 7                       | `HI-47`          |
| `AT-135` | `tests/repository/test_required_files.py::test_the_acceptance_matrix_and_the_specification_name_the_same_test_paths`            | Every planned test path in this document matches the path convention section 18 declares                    | `HI-43`          |
| `AT-136` | `tests/contract/test_reason_codes_registry.py::test_pack10_yml_declares_seventy_six_entries_matching_section_15_counts`         | `pack-10.yml` declares 32 reused plus 44 new entries, 76 total, matching section 15                         | `HI-43`          |
| `AT-137` | `tests/repository/test_version_consistency.py::test_no_accepted_adr_text_was_altered_by_the_pack10_round`                       | ADR-001 through ADR-043's accepted text is byte-identical to before this round                              | `HI-6`           |

This section lists 14 planned tests, `AT-124` through `AT-137`, all
inside `tests/repository/`. Most extend an existing parametrized
suite — `test_required_files.py`, `test_reason_codes_registry.py`,
`test_version_consistency.py`, `test_forbidden_paths.py` and
`test_service_boundaries.py` already iterate every service and every
registry file the repository declares — with an added `finance-service`
case; only the reason-code-specific rows depend on the new
`pack-10.yml` registry file existing at all.

With sections 1 through 6 complete, this document has named 137
planned tests in total, `AT-001` through `AT-137`. Section 7 turns
that list around: instead of one row per test, it is one row per
hard invariant, and instead of asking "what does this test prove",
it asks the question a reviewer actually has — "is every invariant
proven by something."

## 7. Invariant coverage map

Every row below restates one hard invariant from specification section
6 in one line and names every test id from sections 1 through 6 above
that proves it. Every row has at least one test id; several rows have
several, because more than one layer — domain, application, storage,
contract, architecture or repository — proves the same rule from a
different angle, which is itself part of what "planned" means here:
no single test carries the whole weight of an invariant that spans a
constructor, a command guard and a structural import check.

| Invariant | Restatement                                                                  | Test ids                                                                                 |
| --------- | ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| `HI-1`    | No global user ID exists on any finance dataclass                            | `AT-091`, `AT-107`, `AT-116`, `AT-122`                                                   |
| `HI-2`    | No identity payload appears in events, audit records or public views         | `AT-112`, `AT-118`                                                                       |
| `HI-3`    | Organizational scope isolates every finance record                           | `AT-041`, `AT-075`                                                                       |
| `HI-4`    | An undetermined scope denies before any other check                          | `AT-040`, `AT-070`                                                                       |
| `HI-5`    | Financial records cannot be silently deleted                                 | `AT-072`, `AT-073`, `AT-095`                                                             |
| `HI-6`    | Posted entries are immutable; correction is by reversal or new record        | `AT-006`, `AT-007`, `AT-008`, `AT-025`, `AT-027`, `AT-079`, `AT-097`, `AT-137`           |
| `HI-7`    | Every ledger transaction remains balanced                                    | `AT-004`, `AT-005`                                                                       |
| `HI-8`    | Currency and amount semantics are explicit and deterministic                 | `AT-001`                                                                                 |
| `HI-9`    | No floating-point money representation exists anywhere                       | `AT-002`, `AT-093`, `AT-094`                                                             |
| `HI-10`   | Accounting-period closure cannot be bypassed by ordinary writes              | `AT-009`, `AT-042`                                                                       |
| `HI-11`   | Reopening requires authority, reason, audit trail and preserved state        | `AT-010`, `AT-011`, `AT-080`                                                             |
| `HI-12`   | A budget cannot rewrite actual ledger transactions                           | `AT-026`, `AT-113`                                                                       |
| `HI-13`   | Reclassification cannot bypass disclosure, review or reporting rules         | `AT-021`, `AT-043`                                                                       |
| `HI-14`   | Donation aggregation cannot be bypassed by splitting transactions            | `AT-017`, `AT-019`                                                                       |
| `HI-15`   | Related or intermediary contributions cannot be treated as unrelated         | `AT-018`                                                                                 |
| `HI-16`   | Anonymous or unverifiable contributions fail closed into quarantine          | `AT-013`                                                                                 |
| `HI-17`   | Prohibited or uncertain contributions are not silently accepted              | `AT-014`                                                                                 |
| `HI-18`   | Return, rejection or escalation preserves the original receipt record        | `AT-015`, `AT-082`                                                                       |
| `HI-19`   | In-kind contributions require a valuation basis and evidence reference       | `AT-016`, `AT-022`                                                                       |
| `HI-20`   | Sponsorship records financial value and counter-performance where required   | `AT-020`                                                                                 |
| `HI-21`   | General lobbying meetings are not implemented in PACK-10                     | `AT-111`                                                                                 |
| `HI-22`   | Finance evidence references do not make PACK-10 owner of document content    | `AT-089`, `AT-110`, `AT-121`                                                             |
| `HI-23`   | Legal Hold overrides destruction or ordinary retention expiry                | `AT-047`                                                                                 |
| `HI-24`   | Record retention cannot be bypassed by policy replacement                    | `AT-048`, `AT-109`                                                                       |
| `HI-25`   | Report source snapshots and versions are preserved                           | `AT-028`, `AT-085`                                                                       |
| `HI-26`   | A newer report version never destroys an earlier submitted version           | `AT-029`, `AT-083`                                                                       |
| `HI-27`   | Submission is not acceptance                                                 | `AT-030`, `AT-066`                                                                       |
| `HI-28`   | Delivery or read telemetry is not legal effect                               | `AT-031`                                                                                 |
| `HI-29`   | Publication is not authoritative approval unless separately decided          | `AT-032`                                                                                 |
| `HI-30`   | Finance auditor independence is enforced                                     | `AT-034`, `AT-035`, `AT-036`, `AT-037`, `AT-050`, `AT-051`, `AT-084`, `AT-115`           |
| `HI-31`   | Finance auditor and administrator cannot be the same authority in scope      | `AT-044`, `AT-050`                                                                       |
| `HI-32`   | Self-approval of personally created or benefiting transactions is prohibited | `AT-023`, `AT-024`, `AT-054`, `AT-061`, `AT-062`, `AT-068`, `AT-069`, `AT-081`           |
| `HI-33`   | Conflict-of-interest state must be declared; unknown fails closed            | `AT-046`                                                                                 |
| `HI-34`   | Preparation, approval, sign-off and audit are distinguishable actions        | `AT-049`, `AT-104`                                                                       |
| `HI-35`   | Public financial views are derived, versioned and non-authoritative          | `AT-114`                                                                                 |
| `HI-36`   | Small-sample or combinatorial identity disclosure is controlled              | `AT-053`                                                                                 |
| `HI-37`   | No vote, ballot, delegation, eligibility or tally linkage exists             | `AT-092`, `AT-108`                                                                       |
| `HI-38`   | Financial records provide no correlation bridge into voting                  | `AT-039`, `AT-117`                                                                       |
| `HI-39`   | Cross-scope consolidation grants no write authority into lower scopes        | `AT-052`, `AT-071`, `AT-123`                                                             |
| `HI-40`   | Imported financial data preserves source provenance and batch identity       | `AT-076`, `AT-077`                                                                       |
| `HI-41`   | Duplicate imports and replay are detectable                                  | `AT-078`, `AT-087`                                                                       |
| `HI-42`   | Time, timezone and accounting-period boundaries are explicit                 | `AT-012`, `AT-065`, `AT-067`                                                             |
| `HI-43`   | Every denial and protected transition is reason-coded                        | `AT-119`, `AT-126`, `AT-127`, `AT-128`, `AT-129`, `AT-131`, `AT-133`, `AT-135`, `AT-136` |
| `HI-44`   | Unknown policy, perimeter, authority, scope or status fails closed           | `AT-056`, `AT-057`, `AT-058`, `AT-059`, `AT-064`, `AT-096`, `AT-102`, `AT-130`           |
| `HI-45`   | Feature flags must not disable hard invariants                               | `AT-060`                                                                                 |
| `HI-46`   | No production-ready or legally compliant claim exists without external gates | `AT-090`                                                                                 |
| `HI-47`   | No direct access to another service's storage exists                         | `AT-106`, `AT-120`, `AT-124`, `AT-125`, `AT-132`, `AT-134`                               |
| `HI-48`   | The purpose-scoped party handle is non-reusable and non-correlatable         | `AT-038`, `AT-086`                                                                       |
| `HI-49`   | No command reads system time directly                                        | `AT-055`                                                                                 |
| `HI-50`   | Command idempotency holds through the caller-supplied `event_id`             | `AT-101`                                                                                 |
| `HI-51`   | Optimistic concurrency applies to every mutable aggregate                    | `AT-074`                                                                                 |
| `HI-52`   | Every critical action appends an audit event with before/after hashes        | `AT-063`, `AT-098`, `AT-100`                                                             |
| `HI-53`   | A role name alone is never proof of finance authority                        | `AT-045`, `AT-071`, `AT-099`, `AT-103`                                                   |
| `HI-54`   | A later reorganization never rewrites a closed period's perimeter            | `AT-033`                                                                                 |
| `HI-55`   | Rounding and valuation method are recorded with the record, never implicit   | `AT-003`, `AT-088`                                                                       |

## 8. Gate conditions for the implementation round

An implementation round may be called complete only when every
condition below holds. These gates are conjunctive: partial credit on
one does not offset a failure on another, and none of them, singly or
together, is a claim this document is entitled to make about anything
outside its own scope.

1. **Every planned test exists and passes.** Every test id `AT-001`
   through `AT-137` in sections 1 through 6 above is a collected
   `pytest` test in the path named for it, and the full suite passes
   with no test skipped, marked `xfail`, or deleted to make the count
   agree.

2. **The reason-code registry is loaded and complete.**
   `contracts/reason-codes/pack-10.yml` exists, parses against the
   registry schema, declares the 32 reused codes of specification
   section 15.1 with `source: pack-0X-reused` and the 44 new codes of
   section 15.2 with `source: pack-10`, and every entry carries all
   seven mandatory fields.

3. **No delete method exists anywhere in the service.** Neither a
   `Protocol` definition nor an adapter implementation under
   `services/finance-service/src/` exposes a method that deletes a
   record; disposal remains PACK-09's governed workflow only.

4. **No identity field exists on any finance dataclass.** No
   dataclass in `services/finance-service` declares `user_id`,
   `person_id`, `member_id` or a field an exhaustive scan would treat
   as equivalent; every party reference is a `FinancePartyHandle`.

5. **No floating-point money representation exists.** Every monetary
   amount in every dataclass, schema and event payload is integer
   minor units with an explicit scale and rounding rule; no JSON
   Schema for a monetary field permits the `number` type.

6. **Version declarations agree with each other.**
   `REPOSITORY_VERSION`, `CANON_VERSION`, every package version, the
   ADR index, `README.md` and `CHANGELOG.md` state the same values,
   consistent with the targets specification section 19 records
   (`REPOSITORY_VERSION = 0.10.0`, `CANON_VERSION = 0.8.0` already in
   place from the amendment round, in that order per OD-20).

7. **Formatting and static analysis are clean.** `prettier --check`
   on `docs/**` and every generated file, `ruff` and `mypy` across
   `services/finance-service` and every file this round touches all
   report zero findings, with no configuration change suppressing a
   check to reach that result.

8. **Every hard invariant maps to a passing test.** Section 7's
   coverage map holds for the implemented suite exactly as it holds
   for this planned one: all 55 rows, `HI-1` through `HI-55`, each
   with at least one test id whose test actually passes.

9. **No module-boundary rule is violated.** `budgets.py` has no
   import edge into a ledger store, `projections.py` performs no
   authoritative write, `audit_engagement.py` writes to nothing it
   audits, and `partyregistry.py` is the only module that resolves a
   `FinancePartyHandle` — the four rules `AT-113`, `AT-114`,
   `AT-115` and `AT-116`/`AT-122` prove structurally, not by
   convention.

10. **None of the above is a compliance or readiness claim.** Passing
    every gate in this section establishes that the planned tests
    exist and pass, that the registry loads, and that the structural
    rules hold. It establishes nothing about compliance with the
    Parteiengesetz, the Abgabenordnung, the Handelsgesetzbuch, the
    GDPR, the BDSG, any Land-level statute, or about production
    readiness, statutory audit opinion status, or acceptance by the
    Bundestagsverwaltung or any other authority. Specification
    section 22 governs that determination in full, and this document
    adds no claim of its own beyond what its own tests can prove.
