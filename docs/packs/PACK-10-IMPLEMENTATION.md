# PACK-10 — implementation notes

Companion to `PACK-10-SPECIFICATION.md`. What was built, how it follows
the conventions PACK-02 through PACK-09 established, where it departs
from `PACK-10-IMPLEMENTATION-PLAN.md`, and what is deliberately absent.

The round shipped one wholly new service, `services/finance-service`,
the sole authoritative owner of the party-finance bounded context canon
`0.8.0` section 19f defines. No existing service was extended in place.

## 1. Service layout

Twelve modules, in dependency order — each imports only from those above
it, and the order is enforced by the import graph rather than by
convention.

| Module             | Owns                                                                                                                                                                                            |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `__init__.py`      | The package docstring and the module map; no code                                                                                                                                               |
| `exceptions.py`    | 62 exception classes, one per registered reason code, plus `FinanceTechnicalError` for failures that are deliberately not reason codes                                                          |
| `domain.py`        | `Money`, `FinancePartyHandle`, `PROHIBITED_IDENTITY_KEYS`, `OrganizationalScopeRef`, `Provenance`, `EvidenceReference`, `PolicyBinding`, `RetentionBinding`, `RequestContext`                   |
| `authorization.py` | `FinanceRole`, `FinanceActionAuthority`, `INCOMPATIBLE_ROLE_PAIRS`, `ACTION_REQUIREMENTS`, `AuthorizationPort`, the self-approval and auditor-independence assertions                           |
| `ledger.py`        | `FinanceAccount`, `AccountingPeriod`, `PeriodReopeningRecord`, `PostingLine`, `JournalEntry`, `FinancialTransaction`, `correction_chain`                                                        |
| `records.py`       | `FinanceContribution`, `SponsorshipAgreement`, `ExternalFinancialBenefit`, `ExpenseClaim`, `PaymentAuthorization`, `Reimbursement`, `FinancialAsset`, `FinancialObligation`, `GovernedTransfer` |
| `reporting.py`     | `ReportingObligation`, `ReportingPerimeterDefinition`, `PerimeterSnapshot`, `ReportSnapshot`, `ReportState`, `FinanceReportVersion`, `AuditEngagement`, `AuditConclusion`                       |
| `events.py`        | The 72 canonical section-20.17 builders, the `*_state_payload` audit snapshots, `FINANCE_EVENT_TYPES` and `PUBLIC_PROJECTION_ALLOWED`                                                           |
| `references.py`    | The typed inward references to PACK-08/09/11/35 records, the outward `Finance*Reference` types, and the boundary refusals                                                                       |
| `storage.py`       | One `Protocol` per aggregate plus an in-memory reference adapter, `ImportBatchRecord`, `IdempotencyRecord`, `transaction_fingerprint`, `delete_finance_record`                                  |
| `projections.py`   | The derived, versioned, non-authoritative read models and the statistical-disclosure floor                                                                                                      |
| `application.py`   | 42 commands and 5 queries, all routed through one `_guard` frame and one `_finish` tail                                                                                                         |

`authorization.py` is a module the plan did not name; see section 5.

## 2. Conventions carried over from earlier packs

- Dependency-injected `Clock` — no command reads system time. Proved by
  `test_a_fixed_clock_is_the_only_time_source_any_command_reads` and
  `test_a_command_records_the_clocks_instant_and_never_the_wall_clock`.
- Caller-supplied `event_id` idempotency (CT-00-04) — the caller puts
  the id on `RequestContext`; `storage.CommandIdempotencyStore` answers
  first with what the command produced, and Audit Core's own
  `get_by_event_id` stays in place as the second line of defence for the
  window where a command appended its audit row and died before
  persisting its idempotency row. Neither subsumes the other. A replay
  of the same id with a different `request_digest` raises
  `FINANCE_IDEMPOTENCY_CONFLICT`.
- Audit Core append on every command (CT-00-07/INV-04) — with
  canonical-JSON `before_hash`/`after_hash` computed by `_state_hash`
  over the full-state payloads in `events.py`. `_finish` appends the
  audit row before publishing the envelope and records the idempotency
  row last, so no event can escape without an audit row.
- One exception class per registered reason code — every literal in
  `exceptions.py` is registered in `contracts/reason-codes/pack-10.yml`
  (96 entries: 45 canon `0.8.0` codes, 19 additive PACK-10 codes, 32
  reused verbatim from earlier packs and never shadowed by a `FINANCE_`
  duplicate).
- Optimistic concurrency — every mutating command takes an optional
  `expected_*_version`. The version is derived, not stored: for the nine
  aggregates carrying an append-only `history` tuple it is that tuple's
  length (`_history_version`), for `FinancialTransaction` it is the
  explicit `version` field, and for `JournalEntry` and
  `PaymentAuthorization` it is the ordinal of a lifecycle position each
  aggregate reaches at most once.
- In-memory reference stores only — production persistence is PACK-13
  (ADR-038). The adapters are not concurrency-safe and say so.
- Imports limited to `epd2_core` and `epd2_audit_core` — declared in
  `pyproject.toml` and checked by
  `test_the_finance_package_imports_no_other_service_package`. PACK-09's
  reference shapes are re-declared as finance-side mirrors rather than
  imported.
- Two-tier scope errors — `_load_scoped` answers a foreign-scope record
  with the same `VALIDATION_RECORD_NOT_FOUND` as a nonexistent one. The
  specific `ORGANIZATION_SCOPE_MISMATCH` refusal is reachable only on a
  write by a caller that already presented an authority scoped to the
  record's own organization. Reads never reach it.
- No delete method anywhere — not on a port, not on an adapter.
  `storage.delete_finance_record` and `reporting.delete_report_version`
  exist to refuse with `GOVERNED_RECORD_DELETION_FORBIDDEN`, and
  `test_no_port_or_adapter_exposes_any_delete_shaped_method` checks the
  shape structurally.

## 3. The command and query surface

Every command resolves its authority through `ACTION_REQUIREMENTS`,
which holds 40 governed actions. A command whose action is absent from
that table denies rather than defaulting open. Four actions —
`submit_for_review`, `settle_obligation`, `record_transfer` and
`supersede_report` — carry a role set but no command this round.

| Command                             | Action requirement              | Roles permitted                                         |
| ----------------------------------- | ------------------------------- | ------------------------------------------------------- |
| `create_finance_account`            | `manage_chart_of_accounts`      | `finance_administrator`                                 |
| `change_finance_account_status`     | `manage_chart_of_accounts`      | `finance_administrator`                                 |
| `open_accounting_period`            | `open_period`                   | `finance_administrator`                                 |
| `close_accounting_period`           | `close_period`                  | `finance_administrator`                                 |
| `request_period_reopening`          | `request_period_reopening`      | `finance_administrator`                                 |
| `reopen_accounting_period`          | `approve_period_reopening`      | `finance_administrator`, `organizational_administrator` |
| `draft_journal_entry`               | `post_transaction`              | `finance_administrator`                                 |
| `post_journal_entry`                | `post_transaction`              | `finance_administrator`                                 |
| `reverse_journal_entry`             | `reverse_transaction`           | `finance_administrator`                                 |
| `correct_journal_entry`             | `correct_transaction`           | `finance_administrator`                                 |
| `record_financial_transaction`      | `post_transaction`              | `finance_administrator`                                 |
| `reclassify_financial_transaction`  | `reclassify_transaction`        | `finance_administrator`                                 |
| `register_import_batch`             | `register_import_batch`         | `finance_administrator`                                 |
| `record_contribution`               | `record_contribution`           | `finance_administrator`                                 |
| `assess_contribution`               | `assess_contribution`           | `finance_administrator`                                 |
| `decide_contribution`               | `accept_contribution`           | `finance_administrator`                                 |
| `return_contribution`               | `return_contribution`           | `payment_executor`                                      |
| `register_sponsorship`              | `record_sponsorship`            | `finance_administrator`                                 |
| `approve_sponsorship`               | `approve_sponsorship`           | `finance_administrator`                                 |
| `record_external_financial_benefit` | `record_external_benefit`       | `finance_administrator`                                 |
| `submit_expense_claim`              | `record_expense`                | `finance_administrator`                                 |
| `approve_expense_claim`             | `approve_expense`               | `finance_administrator`                                 |
| `authorize_payment`                 | `authorize_payment`             | `payment_authorizer`                                    |
| `settle_payment`                    | `execute_payment`               | `payment_executor`                                      |
| `record_financial_obligation`       | `record_obligation`             | `finance_administrator`                                 |
| `write_off_financial_obligation`    | `write_off_position`            | `finance_administrator`, `organizational_administrator` |
| `freeze_report_snapshot`            | `create_snapshot`               | `finance_administrator`                                 |
| `prepare_report_version`            | `prepare_report`                | `finance_administrator`                                 |
| `complete_internal_report_review`   | `record_review`                 | `finance_administrator`, `report_signatory`             |
| `record_auditor_review`             | `record_auditor_review`         | `finance_administrator`, `report_signatory`             |
| `approve_report_version`            | `approve_report`                | `report_signatory`, `organizational_administrator`      |
| `sign_report_version`               | `sign_report`                   | `report_signatory`                                      |
| `submit_report_version`             | `record_external_submission`    | `report_signatory`                                      |
| `record_external_acknowledgement`   | `record_external_acceptance`    | `finance_administrator`, `report_signatory`             |
| `record_external_acceptance`        | `record_external_acceptance`    | `finance_administrator`, `report_signatory`             |
| `publish_report_version`            | `create_publication_projection` | `report_signatory`, `organizational_administrator`      |
| `create_corrected_report_version`   | `create_report_version`         | `finance_administrator`                                 |
| `open_audit_engagement`             | `request_audit`                 | `finance_administrator`, `organizational_administrator` |
| `record_audit_finding`              | `record_audit_opinion`          | `finance_auditor`                                       |
| `conclude_audit_engagement`         | `record_audit_opinion`          | `finance_auditor`                                       |
| `mint_party_handle`                 | `mint_party_handle`             | `finance_administrator`                                 |
| `resolve_party_handle`              | none — see below                | `finance_party_handle_resolver` role code only          |

`resolve_party_handle` is the single command that does not consult
`ACTION_REQUIREMENTS`. Its authority is resolved by
`_resolve_party_handle_authority` against the exact role code
`PARTY_HANDLE_RESOLUTION_ROLE_CODE`, in this exact scope, with an active
assignment behind the presented object. The bar is narrower than
`assert_authorized`'s, not wider: listing resolution in the action table
would make the party join reachable from an ordinary finance grant.
`_guard` refuses a pre-resolved authority from any other command, so the
parameter cannot become a way past the table.

The five queries take no action requirement at all. Each requires only a
determinable scope (`RequestContext.require_scope`) and applies the
two-tier scope rule on the record it loads. That is weaker than the
command surface and is stated here rather than implied: a caller who can
reach a query needs no finance role to read a projection of its own
scope.

| Query                             | Returns                             | Authority required |
| --------------------------------- | ----------------------------------- | ------------------ |
| `get_account_balance_projection`  | `AccountBalanceProjection`          | scope only         |
| `get_period_summary`              | `PeriodSummaryProjection`           | scope only         |
| `list_contribution_disclosures`   | `ContributionDisclosureProjection`s | scope only         |
| `get_published_report_projection` | `PublishedReportProjection`         | scope only         |
| `get_audit_conclusion_projection` | `AuditConclusionProjection`         | scope only         |

## 4. Design choices worth reading the code for

### The period lock lives inside the posting command

`ledger.post` takes the `AccountingPeriod` as a required keyword
argument and calls `assert_open_for_posting` on it. There is no overload
that posts without one, because canon 19f.5 requires the closed-period
refusal to happen inside the posting command; an overload would be the
bypass `ФИН-10` forbids. `closing` denies as firmly as `closed` —
`_POSTABLE_PERIOD_STATUSES` is an enumerated set rather than "not
closed", so a future status denies by default.

### A reopening record is the evidence, not a side effect

`AccountingPeriod.request_reopening` builds a create-once
`PeriodReopeningRecord` and performs the dual-control check while
building it; `reopen` then refuses a record whose `closed_state_digest`
does not match the period's current `state_digest()`, so a stale
approval cannot be replayed against a period that has since moved on.
`assert_reopening_dual_control` compares both `authority_id` and
`actor_reference`, because a dual-control rule one person can satisfy
alone is not one.

### Correction chains refuse cycles, branches and double origins

`ledger.correction_chain` reads only each record's identity and its
single backward link. It refuses a cycle, a duplicate identity, more
than one origin, and a branch — canon 19f.4 describes a chain, not a
tree, and silently picking one branch would hide the other. A
predecessor id absent from the input means "outside this chain", which
is what makes the function safe on a scope-filtered slice.

### Contributions fail closed into a state, not into a refusal

`FinanceContribution.assess` routes an unresolved assessment to
`quarantined` rather than to `assessed`. The transition table holds no
`received -> accepted` edge at all, so acceptance always follows a
resolved, policy-bound assessment. `assert_receipt_unchanged` runs on
every transition, so "rejection, return and escalation leave the receipt
unchanged" is a checked property rather than a convention.

### Publication is a guard, not a table edge

`signed -> published` is deliberately absent from
`ALLOWED_REPORT_TRANSITIONS`. `FinanceReportVersion.publish` permits it
only after checking three independent facts — a recorded approval, a
presented and scope-matched `PublicationAuthorization`, and a
`PublicationReference` naming that authorisation. A free table edge
would make publication look like an ordinary next step and would drop
the authorisation requirement for anyone reading the table alone.

### Auditor independence is re-verified three times

Canon 19f.18 requires the check at opening, at every finding and at
conclusion. `authorization.assert_auditor_independent` is therefore a
free function taking everything it needs, and `AuditEngagement.open`,
`record_finding` and `conclude` each call it. Called without an
`AuthorizationPort` it runs three of its four checks and clears nothing;
`FinanceReportVersion.record_auditor_review` calls it again against the
actor set read off that version's own history.

### `is_authoritative` is a property, not a field

`projections.FinanceProjection.is_authoritative` returns `False` and has
no setter. A field could be constructed `True` by a `replace`, a
deserialiser or a careless builder; a read-only property on a frozen,
slotted dataclass has no such path.

### Emission is one chokepoint

Every projection builder runs `_assert_emittable`, which walks its own
`to_payload()` output through `domain.reject_identity_payload_keys`
before the projection is returned — so a projection that would leak an
identity key never comes into existence. The same rejection runs over
every assembled event payload in `events.py`.

## 5. Deviations from `PACK-10-IMPLEMENTATION-PLAN.md`

The plan is not authoritative over the implementation; it is a record of
what an authorized round intended. Where the round departed from it, the
departure is listed here rather than left to be discovered by comparing
two file trees.

### 5.1 A different, smaller module split

The plan (and specification section 7, quoting ADR-048) named seventeen
source files. Eight of them do not exist:

| Planned module        | What shipped instead                                                                                                                    |
| --------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| `imports.py`          | `storage.ImportBatchRecord`, `ImportBatchStore` and `transaction_fingerprint` — ingestion is an infrastructure record, not an aggregate |
| `policy.py`           | Nothing. `domain.PolicyBinding` and `references.PolicyVersionReference` carry policy identity; no `FinancePolicy` aggregate exists      |
| `partyregistry.py`    | `domain.FinancePartyHandle`, `storage.FinancePartyHandleStore`, and the two commands `mint_party_handle` and `resolve_party_handle`     |
| `contributions.py`    | `records.py`                                                                                                                            |
| `expenses.py`         | `records.py`                                                                                                                            |
| `positions.py`        | `records.py`                                                                                                                            |
| `budgets.py`          | Nothing. No `Budget`, `BudgetVersion` or `BudgetLine` aggregate exists                                                                  |
| `audit_engagement.py` | `reporting.py`, which holds `AuditEngagement`, `AuditFinding` and `AuditConclusion` alongside the report lifecycle they attach to       |

One module was added that the plan did not name: `authorization.py`,
holding the roles, the incompatibility matrix, the action-requirements
table and the independence assertions. In the plan those lived
implicitly across `domain.py` and the per-aggregate modules.

The cost of the smaller split is specific and worth naming. Four of the
plan's architecture tests were expressed as import-boundary rules
between modules that no longer exist:

- `test_budget_module_has_no_ledger_write_import` cannot exist because
  `budgets.py` does not. The rule it protected (`ФИН-12`, a budget never
  becomes a second source of truth about actuals) is instead enforced by
  the absence of any budget aggregate at all, plus
  `BudgetActualWriteForbiddenError` standing ready and
  `projections.BudgetSummaryProjection` being built from typed arguments
  rather than from a `Budget` object.
- "`partyregistry.py` is the only module resolving a handle" is now
  "`application._resolve_party_handle_authority` is the only function
  that resolves the resolution authority, and
  `PARTY_HANDLE_RESOLUTION_ROLE_CODE` is deliberately not a
  `FinanceRole`". That is a call-site rule rather than an import rule,
  and it is weaker in exactly one sense: a future function in
  `application.py` could call the store directly. Nothing structural
  prevents it.
- "`audit_engagement.py` may not write to any aggregate it audits" is
  now the fact that `AuditEngagement` methods return only new
  `AuditEngagement` instances, and that `record_auditor_review` is a
  report-side action whose role set excludes `finance_auditor`.
- "`projections.py` performs no authoritative write" survives as an
  import rule, since `projections.py` still exists.

The plan's phase ordering constraint — Phase 3 (policy, party registry)
had to land before Phase 4 (contributions), because a contribution needs
a handle and a policy version to bind to — dissolved rather than being
met: both are value objects in `domain.py`, so `records.py` depends on
`domain.py` and on nothing else.

### 5.2 No OpenAPI surface and no JSON Schema set

Phase 0 of the plan named `contracts/openapi/pack-10.yaml`, one JSON
Schema per entity in specification section 8
(`contracts/schemas/*.schema.json`), and one payload schema per event
(`contracts/events/*-payload.v1.schema.json`). None of the three was
created. `contracts/openapi/` holds `pack-02.yaml` through
`pack-09.yaml` and no `pack-10.yaml`; there is no PACK-10 entity schema
and no PACK-10 event payload schema.

The one Phase 0 deliverable that did land is
`contracts/reason-codes/pack-10.yml`, and it is larger than planned: 96
entries against the plan's 76. The extra twenty are canon `0.8.0`
section 24 codes (45 rather than the plan's assumed count) and the
fifteen additive `AuditEvent.reason_code` classifications for
successfully-audited acts, which canon's refusal-only list has no code
for.

`scripts/check_repository.py` reflects the shipped set: it requires
every finance module, every finance test file, the reason-code registry
and the six PACK-10 documents, and it names no OpenAPI or schema path
for this pack.

### 5.3 Different test files

The plan named `test_imports.py`, `test_policy.py`,
`test_partyregistry.py`, `test_contributions.py`, `test_expenses.py`,
`test_positions.py`, `test_budgets.py` and `test_audit_engagement.py`.
Eleven test files shipped instead, one per shipped module plus
`test_privacy_boundary.py`: `test_domain.py`, `test_authorization.py`,
`test_ledger.py`, `test_records.py`, `test_reporting.py`,
`test_events.py`, `test_references.py`, `test_storage.py`,
`test_projections.py`, `test_application.py`,
`test_privacy_boundary.py`.

### 5.4 Three stale claims found in review and corrected

A review pass over the delegated modules found three statements in the
code that were false about the code around them. All three were corrected
before packaging; they are recorded here because a defect found and fixed
is more useful to the next reader than a clean surface.

- `application._guard`, `_resolve_party_handle_authority` and
  `resolve_party_handle` each described `ACTION_REQUIREMENTS` as holding
  "thirty-one governed finance actions". It holds forty. The rule each
  comment stated was right; only the count was wrong. Corrected to
  "forty".
- `__init__.py`, `application.py`, `tests/contract/_schema_helpers.py`
  and the header of `contracts/reason-codes/pack-10.yml` cited an
  "ADR-055". `docs/adr/` contains ADR-048 through ADR-054 and no
  ADR-055. The decomposition decision this service implements is
  ADR-048, and every citation now names it.
- `write_off_financial_obligation`'s docstring said its unconditional
  dual control "is the compensation for `ACTION_REQUIREMENTS` having no
  write-off role of its own". The table does have one -
  `write_off_position`, permitting `finance_administrator` and
  `organizational_administrator` - added in the same review pass. The
  docstring now states what the two checks each answer: who may write off
  at all, and whether one actor may do it alone.

## 6. Deferred, stated as facts

Each item below is something canon 19f or the specification names and
this round did not build. What exists in its place is given for each.

- `Budget`, `BudgetVersion` and `BudgetLine` have no aggregate. What
  exists: two event builders (`build_budget_approved_event`,
  `build_budget_amended_event`), `BudgetActualWriteForbiddenError`, and
  `projections.BudgetSummaryProjection`, which is built from typed
  arguments because there is no aggregate to derive from.
- `ReconciliationRecord` has no aggregate. What exists:
  `build_reconciliation_recorded_event`. Canon 19f.18 rule 3 already
  says an auditor's reconciliation is a finding and not an authoritative
  `ReconciliationRecord`; the authoritative side of that distinction was
  not built.
- `ImportBatch` has no aggregate. What exists:
  `storage.ImportBatchRecord`, an infrastructure record of an ingestion
  act — canon 19f.1 lists `ImportBatch` among the twenty-one
  authoritative aggregates, and this round classified it as
  infrastructure instead, on the grounds that it carries no monetary
  effect, appears in no report and is included in no reporting
  perimeter. That is a judgement against the canon's own list and is
  recorded as such.
- `FinancePolicy` has no aggregate. What exists: `domain.PolicyBinding`
  (the exact policy kind, id, version and effective date a decision
  used), `references.PolicyVersionReference`, `PolicyMissingError`,
  `PolicyVersionUnknownError`, and the two policy event builders. Every
  protected decision stores the binding it used; nothing resolves a
  policy at read time. No policy content is seeded and no policy is
  evaluated by this service.
- Twenty-six of the 72 canonical event builders have no command that
  emits them: `budget.approved`, `budget.amended`,
  `expense_claim.reviewed`, `expense_claim.rejected`,
  `expense_claim.corrected`, `finance_contribution.escalated`,
  `finance_in_kind_valuation.recorded`, `finance_party_handle.merged`,
  `finance_policy.version_published`, `finance_policy.superseded`,
  `finance_report.consolidated`, `finance_report.correction_requested`,
  `finance_report.superseded`, `financial_asset.recorded`,
  `financial_asset.revalued`, `financial_asset.written_off`,
  `financial_obligation.revalued`, `financial_obligation.settled`,
  `import_batch.completed`, `import_batch.rejected`,
  `import_batch.duplicate_detected`, `reconciliation.recorded`,
  `reporting_obligation.created`, `reporting_perimeter.defined`,
  `sponsorship.disclosure_classified` and `sponsorship.rejected`. Each
  builder is complete, tested and refuses an identity key; none is
  reachable from `application.py`.
- `PublicationAuthorization` has no creating command. What exists: the
  aggregate in `reporting.py`, `storage.PublicationAuthorizationStore`
  (create-once), and `publish_report_version`, which requires the
  authorisation to be presented and refuses without it. The
  authorisation has to be constructed by the caller.
- `ReportingPerimeterDefinition` has no creating command. What exists:
  the aggregate with its `draft -> active -> superseded` lifecycle,
  `freeze_perimeter`, `storage.ReportingPerimeterDefinitionStore` with
  `resolve_active`, and `freeze_report_snapshot`, which reads an active
  definition and freezes it alongside the snapshot. The definition has
  to be created and activated by the caller.
- `ReportingObligation`, `FinancialAsset` and `GovernedTransfer` have
  aggregates and stores but no command and no store reference in
  `application.py` at all. They are reachable only by direct use of the
  domain modules.
- No OpenAPI surface, no JSON Schema set. See section 5.2.
- No production persistence, no HTTP server, no event bus. Every adapter
  in `storage.py` is in-memory and none is concurrency-safe;
  `InMemoryEventSink` collects envelopes in a list. PACK-13 owns the
  durable data plane and the production event plane (ADR-038).
- No bank, payment-provider or authority-system integration. A
  submission is a reference to an act performed elsewhere; a settlement
  is a recorded fact, not a payment instruction. No IBAN, account
  number, card datum or payment identifier is stored anywhere — those
  key names are in `PROHIBITED_IDENTITY_KEYS` and are refused at every
  event and projection boundary.
- No finance frontend. No page, route, component or client under
  `frontend/` addresses this service.

## 7. No claim of legal compliance or operational readiness

Repeated here because it belongs next to the code, and because canon
`ФИН-43` says no such claim follows from section 19f: this service
implements a governed workflow with auditability, reason-coded refusals
and separated authorities. Whether any accounting treatment, valuation,
aggregation rule, disclosure threshold, minimum cell size, retention
schedule, report or publication satisfies the Parteiengesetz, German
statutory accounting rules or any authority's requirements is a human
legal and accounting judgement made outside this system.
