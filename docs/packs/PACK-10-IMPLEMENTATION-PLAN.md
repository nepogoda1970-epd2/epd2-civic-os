# CLAUDE-PACK-10 — Implementation plan

PACK-10 is a specification candidate
(`docs/packs/PACK-10-SPECIFICATION.md`). Nothing described in this
document has been built, and this document does not authorize
building it. It describes, in order, what an authorized PACK-10
implementation round would do if and when it is authorized: which
phases it would work through, which files it would create, which
conventions it would carry over from PACK-02 through PACK-09, and
where the sequencing risk is highest. Every "would" in this document
is deliberate.

Two gates are hard, and neither one alone is sufficient — this
mirrors canon 19e.23's implementation-gate wording for
`organization-service`, applied here to `finance-service`:

1. **ADR-044 through ADR-049 accepted.** All six are currently
   `proposed` (specification section 0, section 21). An implementation
   round may not begin against a proposed ADR.
2. **The canon amendment lands as its own dedicated round.** Section 17
   of the specification requires a canon amendment
   (`CANON_VERSION` `0.7.0` to `0.8.0`) and is explicit that this is a
   separate, dedicated round, not a step inside the implementation
   round. `CANON_VERSION` must already read `0.8.0` before this plan's
   Phase 0 starts.

Accepting the ADRs without landing the canon amendment, or landing
the canon amendment without accepted ADRs, does not open either gate.
Both must be true before Phase 0 begins.

## 1. Prerequisites and gates

Beyond the two hard gates above, a defensible fraction of the open
decisions in `PACK-10-OPEN-DECISIONS.md` must be resolved before real
policy content — as opposed to placeholder or test-fixture policy
content — may be seeded. The open decisions split into two groups.

**Block seeding real policy content.** These bear directly on what a
`FinancePolicy` version would assert as legally meaningful, so an
implementation round may build the mechanism but must not seed the
content until each is resolved:

- `OD-1` — the legal `Rechenschaftsbericht` taxonomy that
  `FinancePolicy(report_structure)` would encode.
- `OD-3` — the contribution aggregation perimeter
  (`FinancePolicy(report_perimeter)` content feeding hard invariant
  14).
- `OD-4` — legally relevant contributor categories for
  `FinancePolicy(contribution_classification)` and
  `FinancePolicy(contribution_restriction)`.
- `OD-5` — the actual disclosure and reporting threshold values; no
  default is offered anywhere for this one.
- `OD-7` — public disclosure granularity, including whether a donor
  is ever named.
- `OD-9` — the external sign-off model: whether a preparer may also
  be a signatory.
- `OD-14` — the record-class-to-retention-period mapping that binds
  finance records to PACK-09's `RecordClass` taxonomy.
- `OD-17` — currency scope (EUR-only versus multi-currency) and, if
  multi-currency, who owns the conversion policy `Money` needs.
- `OD-18` — the chart of accounts content and its governance process.

**Do not block the round.** These affect architecture or future
extension points, not the legal content of a seeded policy, and can
be resolved during the round or left as recorded open questions
without stopping Phase 0 through Phase 7:

- `OD-15` — whether `FinanceEvidenceRef` should later carry a typed
  `FinanceRecordRef`; recommended default is not now.
- `OD-16` — ownership of the external-authority/bank/tax integration
  surface, which this round does not implement regardless.
- `OD-19` — the exact PACK-10/PACK-35 boundary in contested cases;
  the boundary rule itself is already specified.
- `OD-22` — whether the party handle registry stays in
  `finance-service` long term; recommended default is yes, for now.

The remaining open decisions (`OD-2`, `OD-6`, `OD-8`, `OD-10` through
`OD-13`, `OD-20`, `OD-21`) sit between these two groups and should be
triaged by the round's own owner/legal/security reviewers against the
same test: does resolving it change what gets seeded as if it were
law? If yes, treat it as blocking.

Across every phase below, one statement holds without exception: **no
legally unverified default may be seeded as law.** Where
`PACK-10-OPEN-DECISIONS.md` offers a recommended default, that default
may inform a test fixture or a placeholder policy version explicitly
marked as unverified; it may never be the value an implementation
ships as the party's actual chart of accounts, threshold, taxonomy or
retention period without the owner/legal confirmation the open
decisions document itself demands.

## 2. Phase plan

Eight phases. Each phase names what is built, the specification
section governing it, which hard invariants (`HI-*`, specification
section 6) become testable once the phase lands, and the exit
criterion that gates moving to the next phase. Phases are ordered by
dependency, not by document section number — Phase 3 (policy and
party registry) precedes Phase 4 (contributions) because a
contribution cannot be recorded without a policy to bind to or a
handle to reference.

### Phase 0 — Contracts and registry

**Builds:** `contracts/reason-codes/pack-10.yml` with all 76 entries
(32 reused, 44 new — specification section 15); the JSON Schemas for
every entity named in specification section 8; the OpenAPI operations
for `finance-service`; the event payload schemas for the events listed
in specification section 14. **Governed by:** specification sections
14 and 15.

**Invariants testable after this phase:** none directly — this phase
is the contract surface every later phase's tests validate against.
It does make `HI-43` (every denial reason-coded) checkable in
principle once `exceptions.py` exists in Phase 1.

**Exit criterion:** the registry file loads via `epd2_core`, contains
no duplicate code, and every JSON Schema and OpenAPI operation
validates against the contract-test tooling PACK-02 established.

### Phase 1 — `domain.py` value objects and pure invariants

**Builds:** `Money`, `PostingLine`, `InKindValuation`,
`AggregationSnapshot`, `PerimeterSnapshot`, `FinancePolicyBinding`,
`ContributionPartyRef`, `RetentionBinding`, `FinanceEvidenceReference`;
the pure functions `assert_balanced`, `assert_not_self_approval`,
`assert_auditor_independent`, `require_timezone`. **Governed by:**
specification sections 8.5 and 8.2 (the `Money`, `JournalEntry`,
`AuditEngagement`, `ExpenseClaim` and `PaymentAuthorization` entries).

**Invariants testable after this phase:** `HI-6` through `HI-9`
(balancing, currency, monetary representation), `HI-30` and `HI-32`
(auditor independence and self-approval as pure functions, without a
store), `HI-42` (timezone explicitness), `HI-55` (rounding and
valuation method recorded).

**Exit criterion:** every value object and pure function has no I/O
and no import beyond `epd2_core`; `test_domain.py` proves each
invariant function in isolation, matching PACK-09's
`assert_decision_maker_eligible` pattern (`PACK-09-IMPLEMENTATION.md`
section 3, "Independence is one pure function").

### Phase 2 — Ledger and periods

**Builds:** `ledger.py` (`FinanceAccount`, `AccountingPeriod`,
`JournalEntry`, `FinancialTransaction`, `ReconciliationRecord`);
`imports.py` (`ImportBatch`, provenance and duplicate detection).
**Governed by:** specification section 4.1, section 8.2.1 through
8.2.6.

**Invariants testable after this phase:** `HI-3` through `HI-5`
(scope isolation, default deny, no delete), `HI-6` and `HI-7`
(immutability and balancing at the store level), `HI-10` and `HI-11`
(period closure and reopening), `HI-40` and `HI-41` (import
provenance and duplicate detection).

**Exit criterion:** `test_a_closed_period_refuses_every_ordinary_
posting_path` and `test_an_unbalanced_entry_cannot_be_constructed_or_
posted` (specification section 6, rows 7 and 10) pass; no store in
`ledger.py` or `imports.py` exposes a delete-shaped method.

### Phase 3 — Policy and party registry

**Builds:** `policy.py` (`FinancePolicy`, all seventeen policy kinds,
effective dating); `partyregistry.py` (`FinancePartyHandle` minting
and the restricted resolution surface). **Governed by:** specification
section 8.2.20, section 8.2.21, and section 13.

**This phase must land before Phase 4.** `Contribution.received`
requires a `ContributionPartyRef` wrapping a `FinancePartyHandle`
(specification section 8.2.7); a contribution cannot be recorded
without a handle to reference, and a contribution's assessment cannot
be recorded without a policy version to bind to (`HI-44`). Building
Phase 4 first would mean either faking the handle and policy binding
or building them ad hoc inside `contributions.py`, which is exactly
the kind of dependency-shaped shortcut this plan exists to prevent.

**Invariants testable after this phase:** `HI-1` and `HI-48`
(purpose-scoped handle, non-reusable across purpose or perimeter),
`HI-44` (unknown policy version fails closed).

**Exit criterion:** `test_the_same_legal_person_gets_unequal_handles_
for_unequal_purposes` and the policy-version-binding tests pass;
`partyregistry.py` is the only module resolving a handle, verified by
an import-boundary test mirroring `test_ct00_09_vote_linkability.py`'s
approach.

### Phase 4 — Contributions, sponsorship and external benefits

**Builds:** `contributions.py` (`Contribution`, aggregation and
threshold evaluation, `SponsorshipAgreement`,
`ExternalFinancialBenefit`).

**Governed by:** specification sections 4.4, 4.5, 8.2.7 through 8.2.9.

**Invariants testable after this phase:** `HI-1`, `HI-13` through
`HI-21` (reclassification bypass, aggregation, fail-closed
exceptional states, receipt preservation, in-kind valuation,
counter-performance, no lobbying entity), `HI-33` (undeclared
conflict fails closed), `HI-38` and `HI-48` (handle
non-correlatability, reused from Phase 3's foundation).

**Exit criterion:** `test_an_unverifiable_contribution_lands_in_
quarantine_not_accepted` and `test_four_split_contributions_
aggregate_to_one_threshold_evaluation` (specification section 6, rows
16 and 14) pass; `test_service_boundaries.py::test_no_pack35_
lobbying_entity_exists_in_finance_service` passes against the real
module.

### Phase 5 — Expenses, payments, positions, budgets

**Builds:** `expenses.py` (`ExpenseClaim`, `PaymentAuthorization`);
`positions.py` (`FinancialAsset`, `FinancialObligation`); `budgets.py`
(`Budget`, `BudgetVersion`, `BudgetLine`). **Governed by:**
specification sections 4.6 through 4.8, section 8.2.10 through 8.2.14.

**Invariants testable after this phase:** `HI-12` (budget cannot
rewrite ledger actuals), `HI-23` (legal hold blocks disposal), `HI-32`
(self-approval and authorizer/executor separation), `HI-53` (a role
name alone never authorizes).

**Exit criterion:** `test_service_boundaries.py::test_budget_module_
has_no_ledger_write_import` and `test_the_claimant_cannot_approve_or_
execute_their_own_reimbursement` pass; no `actual_amount` field exists
anywhere in `budgets.py`.

### Phase 6 — Reporting, consolidation, submission, publication and audit engagement

**Builds:** `reporting.py` (`ReportingObligation`,
`ReportingPerimeterDefinition`, `FinanceReport`, `ReportSnapshot`,
consolidation, submission, publication); `audit_engagement.py`
(`AuditEngagement`, `AuditFinding`, `AuditConclusion`).

**Governed by:** specification sections 4.9, 4.10, 8.2.15 through
8.2.19.

**Invariants testable after this phase:** `HI-25` through `HI-31`
(snapshot-first, version immutability, submission-is-not-acceptance,
telemetry-is-not-effect, publication-is-not-approval, four
distinguishable report actions, auditor independence), `HI-39`
(consolidation cannot write into a lower scope), `HI-54` (perimeter
snapshot survives reorganization).

**Exit criterion:** `test_a_report_snapshot_is_write_once_and_
survives_every_later_version` and `test_submission_alone_never_
reaches_accepted_by_authority` pass; `AuditConclusion` is create-once
and no aggregate this service audits is ever written to by
`audit_engagement.py`.

### Phase 7 — Projections, public views and statistical disclosure control

**Builds:** `projections.py` (`TrialBalanceView`,
`ContributionAggregationView`, `BudgetVersusActualView`,
`PositionSummaryView`, `ReportPreparationView`, `PublicFinanceView`,
`PublicContributionView`, `AuditTrailView`, and the disclosure-control
gate).

**Governed by:** specification sections 4.11, 8.4.

**Invariants testable after this phase:** `HI-2` (no identity
payload), `HI-35` and `HI-36` (derived, versioned, non-authoritative
views; statistical disclosure control before emission).

**Exit criterion:** `test_a_small_cell_view_is_suppressed_or_
aggregated_before_emission` and
`test_service_boundaries.py::test_projections_module_performs_no_
authoritative_write` pass; no view carries a `FinancePartyHandle`, a
name, or any value from which handle sameness could be inferred.

## 3. Module and file inventory

Every file the round would create, and nothing more — this plan
creates none of them. Test file names are indicative of what the
phase plan above requires; the acceptance matrix is the authoritative
list.

| Path                                                                    | Purpose                                                                                                                                    |
| ----------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `services/finance-service/README.md`                                    | Service purpose, owned entities, produced/consumed events, per the new-module guide                                                        |
| `services/finance-service/pyproject.toml`                               | Package definition, dependencies limited to `epd2_core` and `epd2_audit_core`                                                              |
| `services/finance-service/src/epd2_finance_service/__init__.py`         | Package marker                                                                                                                             |
| `services/finance-service/src/epd2_finance_service/domain.py`           | `Money`, `PostingLine`, `InKindValuation`, pure invariant functions (Phase 1)                                                              |
| `services/finance-service/src/epd2_finance_service/ledger.py`           | `FinanceAccount`, `AccountingPeriod`, `JournalEntry`, `FinancialTransaction`, `ReconciliationRecord` (Phase 2)                             |
| `services/finance-service/src/epd2_finance_service/imports.py`          | `ImportBatch`, provenance and duplicate detection (Phase 2)                                                                                |
| `services/finance-service/src/epd2_finance_service/policy.py`           | `FinancePolicy`, all policy kinds, effective dating (Phase 3)                                                                              |
| `services/finance-service/src/epd2_finance_service/partyregistry.py`    | `FinancePartyHandle` minting and restricted resolution (Phase 3)                                                                           |
| `services/finance-service/src/epd2_finance_service/contributions.py`    | `Contribution`, aggregation, `SponsorshipAgreement`, `ExternalFinancialBenefit` (Phase 4)                                                  |
| `services/finance-service/src/epd2_finance_service/expenses.py`         | `ExpenseClaim`, `PaymentAuthorization` (Phase 5)                                                                                           |
| `services/finance-service/src/epd2_finance_service/positions.py`        | `FinancialAsset`, `FinancialObligation` (Phase 5)                                                                                          |
| `services/finance-service/src/epd2_finance_service/budgets.py`          | `Budget`, `BudgetVersion`, `BudgetLine` (Phase 5)                                                                                          |
| `services/finance-service/src/epd2_finance_service/reporting.py`        | `ReportingObligation`, `ReportingPerimeterDefinition`, `FinanceReport`, `ReportSnapshot`, consolidation, submission, publication (Phase 6) |
| `services/finance-service/src/epd2_finance_service/audit_engagement.py` | `AuditEngagement`, `AuditFinding`, `AuditConclusion` (Phase 6)                                                                             |
| `services/finance-service/src/epd2_finance_service/projections.py`      | Derived read models, public views, statistical disclosure control (Phase 7)                                                                |
| `services/finance-service/src/epd2_finance_service/events.py`           | Canonical event builders and full-state payload snapshots                                                                                  |
| `services/finance-service/src/epd2_finance_service/storage.py`          | One `Protocol` per aggregate plus an in-memory reference adapter; no delete method                                                         |
| `services/finance-service/src/epd2_finance_service/application.py`      | Commands, scope guards, Audit Core append, reason-coded refusals                                                                           |
| `services/finance-service/src/epd2_finance_service/references.py`       | Typed references PACK-10 exports to later packs                                                                                            |
| `services/finance-service/src/epd2_finance_service/exceptions.py`       | One class per registered reason code                                                                                                       |
| `services/finance-service/tests/test_domain.py`                         | Phase 1 value-object and pure-invariant tests                                                                                              |
| `services/finance-service/tests/test_ledger.py`                         | Phase 2 account, period, entry, transaction, reconciliation tests                                                                          |
| `services/finance-service/tests/test_imports.py`                        | Phase 2 import provenance and duplicate-detection tests                                                                                    |
| `services/finance-service/tests/test_policy.py`                         | Phase 3 policy versioning and effective-dating tests                                                                                       |
| `services/finance-service/tests/test_partyregistry.py`                  | Phase 3 handle minting, purpose isolation, resolution-audit tests                                                                          |
| `services/finance-service/tests/test_contributions.py`                  | Phase 4 contribution, aggregation, sponsorship, benefit tests                                                                              |
| `services/finance-service/tests/test_expenses.py`                       | Phase 5 claim, review, authorization, settlement tests                                                                                     |
| `services/finance-service/tests/test_positions.py`                      | Phase 5 asset and obligation tests                                                                                                         |
| `services/finance-service/tests/test_budgets.py`                        | Phase 5 budget version, line, consolidation-read tests                                                                                     |
| `services/finance-service/tests/test_reporting.py`                      | Phase 6 report lifecycle, snapshot, submission, publication tests                                                                          |
| `services/finance-service/tests/test_audit_engagement.py`               | Phase 6 engagement, finding, conclusion, independence tests                                                                                |
| `services/finance-service/tests/test_projections.py`                    | Phase 7 read-model and disclosure-control tests                                                                                            |
| `services/finance-service/tests/test_application.py`                    | Cross-module command, scope, authority and idempotency tests                                                                               |
| `services/finance-service/tests/test_storage.py`                        | Scoped-lookup, append-only, create-once, no-delete tests                                                                                   |
| `contracts/reason-codes/pack-10.yml`                                    | The 76-entry reason-code registry (Phase 0)                                                                                                |
| `contracts/openapi/pack-10.yaml`                                        | OpenAPI operations for `finance-service` (Phase 0)                                                                                         |
| `contracts/schemas/*.schema.json`                                       | One JSON Schema per entity in specification section 8 (Phase 0)                                                                            |
| `contracts/events/*-payload.v1.schema.json`                             | One payload schema per event in specification section 14 (Phase 0)                                                                         |
| `docs/packs/PACK-10-IMPLEMENTATION.md`                                  | Implementation notes, mirroring `PACK-09-IMPLEMENTATION.md`'s shape                                                                        |
| `docs/handover/PACK-10-IMPLEMENTATION-REPORT.md`                        | The round's own handover report                                                                                                            |

## 4. Conventions the round must carry over

PACK-02 through PACK-09 established a set of conventions that every
later round has kept without exception. `PACK-09-IMPLEMENTATION.md`
section 2 states the PACK-09 instance of each; PACK-10 would follow
the same pattern with no deviation:

- **Injected `Clock`.** No command in `application.py` reads system
  time; every command receives `epd2_core.clock.Clock` and a test
  named in the shape of `test_a_fixed_clock_is_all_a_command_ever_
reads` proves it (`HI-49`).
- **Caller-supplied `event_id` idempotency.** Replay detection goes
  through Audit Core's own `get_by_event_id`, exactly as
  `compliance-service` and every earlier service do. A retried
  command returns the recorded result rather than re-attempting the
  transition (`HI-50`).
- **Audit Core append with canonical-JSON hashing.** Every critical
  action appends through `epd2_audit_core` with canonical-JSON
  `before_hash`/`after_hash` (`HI-52`), and the hash chain stays
  verifiable across a full workflow, mirroring PACK-09's
  `test_the_audit_chain_stays_verifiable_across_a_full_workflow`.
- **Reason-coded refusal, one exception class per code.** Every
  denial carries a code registered in `contracts/reason-codes/
pack-10.yml`; `exceptions.py` holds exactly one class per code, no
  free-text refusal anywhere (`HI-43`).
- **Optimistic concurrency via `expected_*_version`.** Every mutable
  aggregate carries a monotonically increasing version, and every
  command that mutates it accepts an optional `expected_*_version`
  that refuses on mismatch (`HI-51`).
- **In-memory reference stores only.** `storage.py` provides a
  `Protocol` per aggregate plus an in-memory adapter; production
  persistence is PACK-13's, not this round's (specification section
  5).
- **Imports limited to `epd2_core` and `epd2_audit_core`.** No direct
  import of another service's internals; every cross-service fact
  arrives through a published interface call (`HI-47`), the same
  boundary `test_finance_service_imports_only_shared_packages` would
  check.
- **Two-tier scope errors.** A read, or a write by a caller presenting
  no authority, against a foreign-scope record reports
  `VALIDATION_RECORD_NOT_FOUND` — the same exception class and
  message shape as a nonexistent record. The specific cross-scope
  codes (`CROSS_SCOPE_ACCESS_DENIED`, `CROSS_SCOPE_AUTHORITY_INVALID`)
  are reachable only by a caller who already asserted it holds
  authority there — PACK-09's pattern
  (`PACK-09-IMPLEMENTATION.md` section 3), carried over unchanged so
  `HI-3` and the non-disclosure requirement are satisfied together.
- **No delete method anywhere.** No store protocol or adapter exposes
  a delete-shaped method, at any phase. Disposal, where it applies,
  goes through PACK-09's governed disposition workflow by reference,
  never through a local delete (`HI-5`).

## 5. Sequencing risks

Ordered by severity. Each risk names the mitigation the phase plan in
section 2 already encodes, so that a future implementer sees why the
ordering is not arbitrary.

1. **Building contributions before the party registry.** Building
   `contributions.py` ahead of `partyregistry.py` forces a fake or
   improvised `FinancePartyHandle` shape that then has to be
   reconciled with the real one Phase 3 defines — a rework risk on
   the aggregate the specification calls the most privacy-sensitive
   in the pack. Mitigation: Phase 3 lands before Phase 4.

2. **Building any protected decision before policy versioning
   exists.** A contribution assessment, a sponsorship approval or a
   reclassification that runs before `policy.py` exists has nothing
   to bind to, so it either hard-codes a value or defers the binding
   — both violate `HI-44`. Mitigation: `policy.py` is part of Phase
   3, before any of Phase 4 through Phase 6's protected decisions.

3. **Preparing a report before a snapshot mechanism exists.**
   `FinanceReport` preparation without `ReportSnapshot` in place
   risks a report version that was never actually snapshot-bound.
   Mitigation: `ReportSnapshot` and `FinanceReport` are built together
   in Phase 6, and `HI-25`'s test
   (`test_a_report_snapshot_is_write_once_and_survives_every_later_
version`) is part of that phase's exit criterion, not a follow-up.

4. **Storing an `actual_amount` on a budget line.** The single most
   tempting shortcut in Phase 5: it would make `BudgetVersusActualView`
   trivial to compute and trivial to get wrong the moment a ledger
   correction lands after the budget line was last touched.
   Mitigation: `HI-12` forbids it structurally;
   `test_service_boundaries.py::test_budget_module_has_no_ledger_
write_import` checks the import graph, not just the field list.

5. **Adding a `membership_id` "just for dues."** Section 9.4 already
   closes this door by requiring a purpose-scoped dues reference
   rather than a direct membership identifier, but the temptation
   resurfaces whenever a dues-accounting test needs a real membership
   to point at. Mitigation: no phase in section 2 introduces a
   `membership_id` field anywhere in `finance-service`;
   `test_ct00_08_identity_leakage.py`'s PACK-10 section checks this
   exhaustively over every dataclass, the technique PACK-09 used
   (`HI-1`).

6. **Inferring acceptance from an acknowledgement.** Phase 6 is where
   this risk concentrates: an `ExternalAcknowledgement` record exists
   right next to the `accepted_by_authority` state, and treating "we
   got something back" as "it was accepted" is the shortest path to
   violating `HI-27` and `HI-28`. Mitigation: `accepted_by_authority`
   is reachable only from an explicit `NoticeEffectRef` or equivalent
   governed decision; `test_submission_alone_never_reaches_accepted_
by_authority` is part of Phase 6's exit criterion.

7. **Hard-coding a threshold "temporarily."** Every threshold is
   legally unverified until `OD-5` and related decisions are resolved
   (section 1), which makes a "temporary" constant in
   `contributions.py` or `reporting.py` attractive during Phase 4 and
   Phase 6 test-writing. Mitigation: `HI-44` requires every protected
   decision to bind to a `FinancePolicyBinding` pointing at a real,
   versioned `FinancePolicy`; a fixture may use an
   explicitly-marked-unverified policy version, but no code path may
   read a Python constant instead of a policy lookup.

8. **A reorganization arriving mid-period.** PACK-08's organizational
   hierarchy can change while a period or report version is open, and
   a naive implementation would recompute the reporting perimeter
   from the current hierarchy at report time — silently rewriting
   which units a submitted period covered. Mitigation:
   `ReportingPerimeterDefinition` is effective-dated and
   `PerimeterSnapshot` freezes into the report version (`HI-54`);
   Phase 6's exit criterion includes
   `test_a_reorganization_leaves_a_submitted_periods_perimeter_
untouched`.

## 6. Repository-integration decisions

**`scripts/check_repository.py`'s required-path list is deliberately
not extended by this round.** The specification (section 2) ties this
to precedent: ADR-026 through ADR-037 were never added to that list
either, a pre-existing gap the script's own comment records rather
than silently widening. Whether a `finance-service` implementation
round follows that precedent or closes the gap is a decision for the
implementation round to make explicitly, not something this plan
pre-decides.

**`tests/repository/test_required_files.py`** needs no change if the
round follows the precedent above; it already asserts against
whatever `find_missing_required_paths` reports, so it tracks the
script automatically either way.

**`tests/contract/test_reason_codes_registry.py`** would need a
`pack-10` row alongside the existing nine: required-field validation
for every entry, no duplicate codes across the full registry set, and
that `contracts/reason-codes/pack-10.yml` loads through `epd2_core`
exactly as `pack-09.yml` does, mirroring
`PACK-09-IMPLEMENTATION.md` section 4's own row for this test.

**Version bump plan.** `REPOSITORY_VERSION` moves `0.9.0` to `0.10.0`
in every mirrored location: the Python package version, the TypeScript
package version, `docs/canonical/canon-version.json`'s repository
field, and `CHANGELOG.md`. `scripts/verify_versions.py` and
`tests/repository/test_version_consistency.py` need no logic change
— they already check consistency across those locations — but would
fail until all of them are updated together in the same commit. This
bump depends on the canon amendment gate having already moved
`CANON_VERSION` to `0.8.0` first (specification section 17, 19).

**`CHANGELOG.md` and `README.md` updates.** `CHANGELOG.md` gains a
`0.10.0` entry describing `finance-service` and pointing at the ADR
range and the canon amendment it depended on. `README.md` gains
`finance-service` to its service inventory, in the style PACK-07
through PACK-09 used for their own new services.

**The `repository_compatibility` range question (`OD-20`).**
`docs/canonical/canon-version.json` currently declares
`"repository_compatibility": ">=0.1.0 <0.10.0"`, which excludes
`0.10.0` itself. Two paths close this: widen the declared range, or
let the canon amendment round move it at the same time it moves
`CANON_VERSION`. Specification section 17 and `OD-20` both record the
specification's own position that the canon amendment should land
first and carry this change with it — but `OD-20` is explicit this is
an owner decision to confirm, and this plan does not settle it.

## 7. Definition of done

`PACK-10-ACCEPTANCE-MATRIX.md` section 8 is the authoritative
definition of done for an implementation round: it restates every
hard invariant from specification section 6 with its full planned
test path, and a round is complete only when every test named there
exists and passes.

Passing that matrix asserts nothing beyond what it tests. A green
acceptance matrix run is a statement about this repository's own
tests, and it asserts nothing about legal compliance, tax
correctness, audit sufficiency or production readiness — the same
limits specification section 22 places on PACK-10 itself apply
without exception to a completed implementation round. Reaching
`signed` in the `FinanceReport` lifecycle means a recorded signatory
authority performed a recorded act, not that the report is legally
correct or complete; a concluded `AuditEngagement` is an internal
governed workflow, not a statutory audit opinion; and a fully green
test suite for `finance-service` says the code does what this
specification and this plan describe, and says nothing about whether
what it describes satisfies the Parteiengesetz, the Abgabenordnung,
the GDPR, the BDSG, or any other law.
