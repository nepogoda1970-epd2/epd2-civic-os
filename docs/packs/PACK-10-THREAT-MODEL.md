# CLAUDE-PACK-10 — Threat model

This is a specification-phase threat model for a domain that is not
implemented. `services/finance-service` does not exist; no production code,
schema, API operation or test named here has been written. Every
"mitigation" below names a planned enforcement point from
`PACK-10-SPECIFICATION.md` section 6 (hard invariants, `HI-nn`) and section
15 (reason codes) — a design commitment, not a shipped control. Nothing was
tested or run, and no residual-risk rating is measured.

Scope mirrors section 4 and section 5: ledger, income, expenditure,
donations and contributions, sponsorship and external financial influence,
expense and reimbursement, assets and obligations, budgets, the
Rechenschaftsbericht lifecycle, finance audit, and public transparency
views. Document custody (PACK-11), privileged administration and DLP
(PACK-12), the production data plane (PACK-13), real IAM (PACK-14) and
lobbying disclosure (PACK-35) are named only as future-pack dependencies.

## T-01 — Transaction deletion

- **Protected asset**: completeness of `FinancialTransaction`/
  `JournalEntry` — a recorded fact cannot disappear.
- **Attacker or failure mode**: an operator with storage access deletes a
  record; honest failure: an adapter change leaks a "cleanup" delete method
  into production.
- **Trust boundary**: `storage.py` protocol, between domain code and its
  persistence adapter.
- **Planned mitigation**: `HI-5` — no delete method on any store `Protocol`;
  disposal only via PACK-09's disposition workflow. Module `storage.py`.
  Reason code `GOVERNED_RECORD_DELETION_FORBIDDEN` (reused).
- **Detection**:
  `test_service_boundaries.py::test_finance_service_storage_exposes_no_delete_operation`.
- **Audit evidence**: gap-free Audit Core sequence (`HI-52`); no deletion
  event type exists in the taxonomy (section 14).
- **Residual risk**: application-layer only; a direct storage-engine write
  bypassing `finance-service` code is unaddressed.
- **Future-pack dependency**: PACK-13 (database-level constraints).

## T-02 — Retroactive mutation of a posted entry

- **Protected asset**: the content of a `posted` `JournalEntry`.
- **Attacker or failure mode**: an insider edits a posted entry; honest
  failure: a `draft`-only edit path stays reachable for `posted` via an
  incomplete state check.
- **Trust boundary**: `application.py`, `draft`/`posted` state check.
- **Planned mitigation**: `HI-6` — `posted` is terminal; correction is only
  a new reversing entry. Module `domain.py` (`JournalEntry`). Reason code
  `FINANCE_IMMUTABLE_RECORD_MODIFICATION_ATTEMPTED`.
- **Detection**:
  `test_a_posted_journal_entry_cannot_be_edited_only_reversed`.
- **Audit evidence**: `journal_entry.posted` followed only by `.reversed`;
  no edit event exists in the taxonomy (section 14).
- **Residual risk**: same limit as T-01 — no protection against a direct
  store write bypassing `application.py`.
- **Future-pack dependency**: PACK-13.

## T-03 — Ledger imbalance

- **Protected asset**: the double-entry invariant that debit and credit
  lines sum equal per currency, per `JournalEntry`.
- **Attacker or failure mode**: a crafted unbalanced entry; honest failure:
  a rounding error in a multi-line split.
- **Trust boundary**: `domain.py` constructor, posting re-check.
- **Planned mitigation**: `HI-7` — `assert_balanced` runs at construction
  and posting. Module `domain.py`. Reason code
  `FINANCE_JOURNAL_ENTRY_UNBALANCED`.
- **Detection**: `test_an_unbalanced_entry_cannot_be_constructed_or_posted`.
- **Audit evidence**: `journal_entry.posted` carries the balanced-sum check
  result and amounts by currency (section 14).
- **Residual risk**: guarantees per-entry balance only; no cross-entry check
  covers a valid-but-wrong-account entry.
- **Future-pack dependency**: none.

## T-04 — Duplicate posting

- **Protected asset**: the one-to-one link between a business fact and its
  posted record.
- **Attacker or failure mode**: a retried request after a timeout; malicious
  variant: deliberate resubmission to double-book spend.
- **Trust boundary**: `application.py` idempotency keyed on `event_id`.
- **Planned mitigation**: `HI-50` (`event_id` idempotency) and `HI-41`
  (fingerprint dedup). Module `application.py`, `imports.py`. Reason codes
  `FINANCE_DUPLICATE_TRANSACTION`, `FINANCE_DUPLICATE_IMPORT`.
- **Detection**:
  `test_the_same_batch_imported_twice_is_detected_not_duplicated`.
- **Audit evidence**: a retried `event_id` produces exactly one
  `financial_transaction.recorded` event (`HI-50`).
- **Residual risk**: a manually re-keyed duplicate — worded differently,
  sharing no fingerprint or `event_id` — is undetectable.
- **Future-pack dependency**: none.

## T-05 — Replayed import

- **Protected asset**: `ImportBatch` integrity — a source file cannot be
  re-applied to double-count rows.
- **Attacker or failure mode**: accidental resubmission; malicious variant:
  deliberate replay to inflate income or expenditure.
- **Trust boundary**: `imports.py` intake boundary.
- **Planned mitigation**: `HI-41` — content fingerprint over the batch;
  re-applying an `applied` batch is forbidden (section 8.2.5). Module
  `imports.py`. Reason code `FINANCE_DUPLICATE_IMPORT`.
- **Detection**:
  `test_the_same_batch_imported_twice_is_detected_not_duplicated`.
- **Audit evidence**: `import_batch.registered` carries the fingerprint; a
  replay yields `.rejected`, not a second `.completed`.
- **Residual risk**: an "explicit, reason-coded override decision" can force
  re-apply a matching fingerprint (section 8.2.5) — a deliberate escape
  hatch if the authorizer is compromised.
- **Future-pack dependency**: PACK-13 (real ingestion).

## T-06 — Amount manipulation

- **Protected asset**: correctness of every `Money` value posted.
- **Attacker or failure mode**: a manipulated amount; honest failure:
  upstream floating-point drift before the value arrives.
- **Trust boundary**: `domain.py` `Money` value-object boundary.
- **Planned mitigation**: `HI-9` (integer minor units) and `HI-55` (explicit
  scale/rounding). Module `domain.py`. Reason code
  `FINANCE_MONETARY_AMOUNT_INVALID`.
- **Detection**: Hypothesis round-trip property in `test_property_based.py`.
- **Audit evidence**: posted payloads carry amounts by currency and scale,
  bound to a `FinancePolicyBinding` (`HI-44`).
- **Residual risk**: rules out an unrepresentable amount, not a
  valid-but-wrong one; no reconciliation is mandatory before posting.
- **Future-pack dependency**: none.

## T-07 — Currency confusion

- **Protected asset**: correctness of cross-currency accounting.
- **Attacker or failure mode**: honest bug mixes currencies in one entry;
  malicious variant: a missing conversion check hides a cross-border
  transfer's value.
- **Trust boundary**: `domain.py` `Money` arithmetic boundary.
- **Planned mitigation**: `HI-8` — explicit `currency_code`, no implicit
  currency, no cross-currency arithmetic without a recorded conversion.
  Module `domain.py`. Reason code `FINANCE_CURRENCY_UNSUPPORTED`.
- **Detection**: `test_money_refuses_mixed_currency_arithmetic`.
- **Audit evidence**: `journal_entry.posted` records amounts by currency,
  never a combined total (section 14).
- **Residual risk**: fixes unconverted arithmetic; supported currencies and
  conversion-rate sourcing remain open `FinancePolicy` inputs (section 13).
- **Future-pack dependency**: none.

## T-08 — Threshold splitting

- **Protected asset**: donation-threshold aggregation — a large gift cannot
  evade disclosure as many small ones.
- **Attacker or failure mode**: a donor splits one contribution to stay
  under a threshold.
- **Trust boundary**: `contributions.py` aggregation boundary.
- **Planned mitigation**: `HI-14` — aggregation key is (party handle, policy
  period, perimeter, policy version); evaluated on the aggregate, never one
  contribution. Module `contributions.py`. Reason code
  `FINANCE_CONTRIBUTION_AGGREGATION_UNRESOLVED`.
- **Detection**:
  `test_four_split_contributions_aggregate_to_one_threshold_evaluation`.
- **Audit evidence**: each `finance_contribution.assessed` carries an
  aggregation-snapshot digest.
- **Residual risk**: depends on the same handle being matched across splits
  by the governed act in `partyregistry.py` (section 9.4) — shared cause
  with T-09, T-11.
- **Future-pack dependency**: none.

## T-09 — Donor fragmentation across units or periods

- **Protected asset**: aggregation correctness across organizational units
  and periods, not only within one.
- **Attacker or failure mode**: a donor gives to several Kreisverband units,
  or times gifts across a period boundary, to dodge one threshold.
- **Trust boundary**: `contributions.py` aggregation, extended across
  perimeter and period.
- **Planned mitigation**: `HI-14`/`HI-15` — declared related or intermediary
  contributions extend the aggregation key even when separate. Module
  `contributions.py`. Reason code
  `FINANCE_CONTRIBUTION_AGGREGATION_UNRESOLVED`.
- **Detection**:
  `test_a_declared_intermediary_chain_aggregates_with_its_principal`.
- **Audit evidence**: the frozen `AggregationSnapshot` on each append-only
  assessment entry (section 8.2.7).
- **Residual risk**: named unclosable (section 16, point 3): the key only
  extends to declared relationships; an undeclared one under-aggregates.
- **Future-pack dependency**: none; not closable per the specification's own
  framing.

## T-10 — Undisclosed intermediary

- **Protected asset**: the true originating party behind a contribution or
  sponsorship an intermediary obscures.
- **Attacker or failure mode**: a contributor routes money through a third
  party so the recorded handle points at the intermediary.
- **Trust boundary**: `contributions.py` declaration boundary, acting only
  on what is declared.
- **Planned mitigation**: `HI-15` (declared chains aggregate with their
  principal) and `HI-16`/`HI-17` (fail closed on unverifiable or prohibited
  source). Module `contributions.py`. Reason codes
  `FINANCE_CONTRIBUTION_AGGREGATION_UNRESOLVED`,
  `FINANCE_CONTRIBUTION_SOURCE_UNDETERMINED`.
- **Detection**:
  `test_a_declared_intermediary_chain_aggregates_with_its_principal`.
- **Audit evidence**: `finance_contribution.received`/`.assessed` carry the
  policy binding used; an absent `intermediary_declaration` is visible.
- **Residual risk**: named unclosed (section 16, point 3): a system
  receiving only declarations cannot discover a concealed intermediary.
- **Future-pack dependency**: none — a future PACK-35 record could
  corroborate this non-financially but is not claimed to close it.

## T-11 — Beneficial-origin concealment

- **Protected asset**: the true ultimate beneficial owner behind a
  legal-person contributor or sponsor.
- **Attacker or failure mode**: a legal-person contributor conceals its
  owner behind an undeclared entity chain.
- **Trust boundary**: `contributions.py`/`partyregistry.py` declaration
  boundary.
- **Planned mitigation**: `HI-16` (fail closed, source undetermined) and
  `HI-17` (fail closed, unverifiable/prohibited). Module `contributions.py`.
  Reason codes `FINANCE_CONTRIBUTION_SOURCE_UNDETERMINED`,
  `FINANCE_CONTRIBUTION_VERIFICATION_INCOMPLETE`.
- **Detection**:
  `test_an_unverifiable_contribution_lands_in_quarantine_not_accepted`.
- **Audit evidence**: `finance_contribution.quarantined` records the
  exceptional state, rather than passing silently into `accepted`.
- **Residual risk**: named unclosed (section 16, point 3): fails closed on
  the unknown but cannot discover a concealed or falsely declared owner.
- **Future-pack dependency**: none — stated unclosable.

## T-12 — In-kind undervaluation

- **Protected asset**: correctness of a non-monetary contribution's or
  benefit's recorded value.
- **Attacker or failure mode**: a donor or accepting authority understates a
  valuation; honest failure: no independent review is required.
- **Trust boundary**: `domain.py` `InKindValuation` boundary.
- **Planned mitigation**: `HI-19` — valuation method, date and evidence
  reference are mandatory for non-monetary items. Module `domain.py`. Reason
  codes `FINANCE_IN_KIND_VALUATION_MISSING`,
  `FINANCE_EVIDENCE_REFERENCE_MISSING`.
- **Detection**:
  `test_an_in_kind_contribution_without_a_valuation_basis_is_refused`.
- **Audit evidence**: `finance_in_kind_valuation.recorded` carries the
  method reference, date and evidence reference permanently.
- **Residual risk**: enforces that a basis exists, not that it is correct —
  content is PACK-11's domain (`HI-22`).
- **Future-pack dependency**: PACK-11 (valuation report authenticity).

## T-13 — Sponsorship disguised as ordinary income

- **Protected asset**: the legal distinction between sponsorship (with
  counter-performance) and ordinary income.
- **Attacker or failure mode**: an actor records a sponsorship as generic
  income to avoid disclosure rules.
- **Trust boundary**: `contributions.py` classification boundary for
  `SponsorshipAgreement`.
- **Planned mitigation**: `HI-20` — counter-performance mandatory unless
  explicitly classified as none; never inferred from amount alone (section
  4.2). Module `contributions.py`. Reason code
  `FINANCE_COUNTER_PERFORMANCE_MISSING`.
- **Detection**:
  `test_sponsorship_without_counter_performance_needs_an_explicit_policy_classification`.
- **Audit evidence**: `sponsorship.registered`/`.disclosure_classified`
  carry the disclosure class and policy binding used.
- **Residual risk**: prevents an unclassified escape, not a deliberate
  misclassification by an authorized classifier — see T-16.
- **Future-pack dependency**: none.

## T-14 — Expenditure disguised as reimbursement

- **Protected asset**: correctness of expenditure classification — a
  personal benefit is not recorded as ordinary reimbursement.
- **Attacker or failure mode**: a claimant submits a personal expense
  through `ExpenseClaim` framed as legitimate.
- **Trust boundary**: `expenses.py` review/approval boundary.
- **Planned mitigation**: `HI-32` (self-approval prohibited) and `HI-33`
  (undeclared conflict fails closed). Module `expenses.py`, `domain.py`
  (`assert_not_self_approval`). Reason codes
  `CONFLICT_REVIEW_SELF_APPROVAL_PROHIBITED`,
  `CONFLICT_OF_INTEREST_UNDECLARED`.
- **Detection**:
  `test_the_claimant_cannot_approve_or_execute_their_own_reimbursement`.
- **Audit evidence**: `expense_claim.reviewed`/`.approved` carry an
  authority distinct from the claimant's on `.submitted`.
- **Residual risk**: addresses who may approve, not the substantive purpose
  classification an independent reviewer accepts.
- **Future-pack dependency**: PACK-11 (receipts to verify a claim).

## T-15 — Self-approval

- **Protected asset**: segregation of duties wherever one actor could cause
  and approve/execute a payment-affecting outcome.
- **Attacker or failure mode**: an actor approves, authorizes or executes
  their own claim, payment or reversal.
- **Trust boundary**: `application.py`, creating/benefiting act vs.
  approving act.
- **Planned mitigation**: `HI-32` — `assert_not_self_approval` compares
  actor authority references. Module `domain.py`. Reason code
  `CONFLICT_REVIEW_SELF_APPROVAL_PROHIBITED`.
- **Detection**:
  `test_the_claimant_cannot_approve_or_execute_their_own_reimbursement` plus
  two `test_application.py` cases.
- **Audit evidence**: `payment.authorized`/`.settled` record separate
  authorizing and executing authority fields (section 14).
- **Residual risk**: compares authority references only; one person holding
  two distinct assignments in one scope depends on PACK-08's authority
  model, not resolved here.
- **Future-pack dependency**: PACK-08 (authority-identity resolution).

## T-16 — Collusive approval

- **Protected asset**: every segregation-of-duties rule, against two or more
  cooperating actors rather than one.
- **Attacker or failure mode**: two or more authorized actors coordinate,
  each within their own authority, to push fraud through.
- **Trust boundary**: `application.py` authority separation, across actors.
- **Planned mitigation**: role separation of section 4.10 and ADR-052
  (`HI-30`, `HI-31`, `HI-32`, `HI-53`). Module `application.py`,
  `audit_engagement.py`. Reason codes `AUTHORITY_ROLE_INCOMPATIBLE`,
  `FINANCE_AUTHORITY_MISSING`.
- **Detection**: none structural — no planned test claims to detect this;
  only auditor review or a legal case surfaces it afterward.
- **Audit evidence**: append-only authority references, reason codes and
  timestamps (`HI-52`) make a pattern reconstructible after the fact.
- **Residual risk**: named explicitly (section 16, point 1) and restated
  below: collusion is made evidenced, not impossible.
- **Future-pack dependency**: none named as closing this.

## T-17 — Auditor conflict

- **Protected asset**: independence of a `finance_auditor`'s
  `AuditEngagement`.
- **Attacker or failure mode**: an engaged auditor is also
  `finance_administrator` in scope, or has an undeclared relationship with
  the audited entity.
- **Trust boundary**: `audit_engagement.py`/`application.py` authority
  resolution at engagement creation.
- **Planned mitigation**: `HI-30` (`assert_auditor_independent`) and `HI-31`
  (incompatibility, PACK-08 9.3 rule 3, canon 19e.16). Module `domain.py`.
  Reason codes `FINANCE_AUDITOR_INDEPENDENCE_VIOLATION`,
  `AUTHORITY_ROLE_INCOMPATIBLE`.
- **Detection**: five `test_domain.py` cases plus two in
  `test_application.py`.
- **Audit evidence**: `finance_audit.opened` carries an independence check
  result in its payload (section 14).
- **Residual risk**: operates over PACK-08's known authority records; an
  undeclared relationship never represented there is invisible.
- **Future-pack dependency**: none; depends on PACK-08 data completeness.

## T-18 — Unauthorized period reopening

- **Protected asset**: the integrity of a closed `AccountingPeriod`.
- **Attacker or failure mode**: an actor reopens a closed period to slip in
  a late favorable adjustment without authority.
- **Trust boundary**: `application.py` `reopen_accounting_period`.
- **Planned mitigation**: `HI-11` — distinct command, distinct approving
  authority, mandatory reason, create-once `PeriodReopeningRecord`
  snapshotting the closed state. Module `application.py`. Reason code
  `FINANCE_PERIOD_REOPENING_NOT_AUTHORIZED`.
- **Detection**:
  `test_reopening_preserves_the_closed_state_and_requires_authority`.
- **Audit evidence**: `.reopening_requested`/`.reopened` carry the
  requesting and authorizing authority plus a preserved-state digest.
- **Residual risk**: dual control requires two authorities; it does not stop
  them legitimately colluding — see T-16.
- **Future-pack dependency**: none.

## T-19 — Report snapshot replacement

- **Protected asset**: the frozen `ReportSnapshot` a version was prepared
  from.
- **Attacker or failure mode**: an actor substitutes a snapshot after
  preparation; honest failure: a re-snapshot overwrites, not versions.
- **Trust boundary**: `reporting.py` `ReportSnapshot` create-once boundary.
- **Planned mitigation**: `HI-25` — create-once; no preparation, validation
  or submission proceeds without one. Module `reporting.py`. Reason codes
  `FINANCE_REPORT_SNAPSHOT_MISSING` (absence),
  `FINANCE_IMMUTABLE_RECORD_MODIFICATION_ATTEMPTED` (mutation).
- **Detection**:
  `test_a_report_snapshot_is_write_once_and_survives_every_later_version`.
- **Audit evidence**: `finance_report.snapshot_frozen` carries a content
  digest, period id set and policy binding set.
- **Residual risk**: create-once is application-layer only, same limit as
  T-01, T-02, T-05.
- **Future-pack dependency**: PACK-13 (durable immutability).

## T-20 — Publication of an unapproved draft

- **Protected asset**: only approved, signed report content is ever made
  publicly readable.
- **Attacker or failure mode**: an actor publishes a `draft` or
  `internally_reviewed` version early; honest failure: a publish command
  targets the wrong version id.
- **Trust boundary**: `reporting.py`/`projections.py` publication boundary.
- **Planned mitigation**: `HI-29` — publication requires an existing
  approval and a separate publication authorization; publishing never sets
  approval. Module `reporting.py`, `projections.py`. Reason code
  `PUBLICATION_NOT_ALLOWED`.
- **Detection**: `test_publication_does_not_imply_approval_and_vice_versa`.
- **Audit evidence**: `finance_report.published` carries the publication
  authority, cross-referenceable against `.approved` and `.signed`.
- **Residual risk**: the approval precondition is structural; no
  content-diff check against the published rendition is named.
- **Future-pack dependency**: PACK-11 (publication rendition, section 12).

## T-21 — False external acceptance

- **Protected asset**: the `accepted_by_authority` state — never inferred
  from less than an authoritative reference.
- **Attacker or failure mode**: delivery/read telemetry recorded as
  acceptance; honest failure: a "delivered" webhook wired into the
  transition.
- **Trust boundary**: `reporting.py`, `submitted` vs.
  `accepted_by_authority`.
- **Planned mitigation**: `HI-27`/`HI-28` — reachable only from a PACK-09
  `NoticeEffectRef` (ADR-043); no telemetry drives a transition. Module
  `reporting.py`. Reason code
  `FINANCE_EXTERNAL_ACKNOWLEDGEMENT_NOT_AUTHORITATIVE`.
- **Detection**:
  `test_submission_alone_never_reaches_accepted_by_authority`.
- **Audit evidence**: `.external_acknowledgement_recorded` (never an
  acceptance flag) is distinct from `.acceptance_recorded` (carries the
  notice effect reference and deciding authority).
- **Residual risk**: named unclosed (section 16, point 2): a human still
  records the `NoticeEffectRef`, with no external gateway to verify it.
- **Future-pack dependency**: PACK-09 (`NoticeEffectDecision` quality); no
  pack owns a submission gateway (section 5).

## T-22 — Cross-scope data access

- **Protected asset**: scope isolation between Bund, Landesverband,
  Kreisverband and other governed scopes.
- **Attacker or failure mode**: an actor infers another scope's data; honest
  failure: a query omits a scope filter.
- **Trust boundary**: `application.py` scope guard, `storage.py` scoped
  lookups.
- **Planned mitigation**: `HI-3` (isolation, foreign records not-found) and
  `HI-4` (default deny, checked first). Module `application.py`,
  `storage.py`. Reason codes `ORGANIZATION_SCOPE_MISMATCH`,
  `ORGANIZATION_SCOPE_UNDETERMINED`, `CROSS_SCOPE_ACCESS_DENIED` (reused).
- **Detection**: `test_application.py` scope-isolation suite.
- **Audit evidence**: every event carries organizational scope; a
  foreign-scope read answers `VALIDATION_RECORD_NOT_FOUND`,
  non-disclosingly.
- **Residual risk**: application-query-layer only; no real database access
  control backs the claim yet.
- **Future-pack dependency**: PACK-13 (data plane); PACK-14 (IAM).

## T-23 — Consolidation double counting

- **Protected asset**: correctness of consolidated totals across
  organizational units.
- **Attacker or failure mode**: honest bug: a transfer counted as income in
  both units; malicious variant: the `internal_transfer_reference` is
  omitted to inflate income.
- **Trust boundary**: `reporting.py` consolidation boundary.
- **Planned mitigation**: `HI-39` (consolidation reads lower-scope records,
  writes only its own `ConsolidationRecord`) plus transfer pairing (section
  4.3). Module `reporting.py`. Reason codes
  `FINANCE_TRANSFER_PAIR_UNRESOLVED`,
  `FINANCE_CROSS_SCOPE_CONSOLIDATION_DENIED`.
- **Detection**: `test_consolidation_cannot_write_into_a_lower_scope`.
- **Audit evidence**: `finance_report.consolidated` carries the
  consolidation record id and eliminated-transfer count.
- **Residual risk**: elimination depends on both sides sharing one reference
  at recording; an omission is not caught by any independent cross-unit
  balance check named in the specification.
- **Future-pack dependency**: none.

## T-24 — Historical perimeter rewrite after reorganization

- **Protected asset**: the historical `PerimeterSnapshot` of a closed or
  submitted period.
- **Attacker or failure mode**: a reorganization retroactively changes a
  submitted period's coverage; honest failure: report code re-resolves
  current state instead of the frozen snapshot.
- **Trust boundary**: `reporting.py` perimeter-snapshot boundary.
- **Planned mitigation**: `HI-54` (perimeter frozen into the report version)
  plus PACK-08's rule that succession alone transfers nothing (canon
  19e.10). Module `reporting.py`. Reason code
  `FINANCE_REPORTING_PERIMETER_UNDETERMINED`.
- **Detection**:
  `test_a_reorganization_leaves_a_submitted_periods_perimeter_untouched`.
- **Audit evidence**: `reporting_perimeter.defined` is distinct from the
  `PerimeterSnapshot` embedded via `finance_report.snapshot_frozen`.
- **Residual risk**: flagged (section 10) as the most likely place for a
  plausible-looking implementation to go wrong. Not implemented yet.
- **Future-pack dependency**: PACK-08 (ADR-033 effective dating
  correctness).

## T-25 — Identity leakage through a finance record, event or view

- **Protected asset**: absence of identity data (names, addresses, national
  identifiers — section 9.3) in any PACK-10 record, event or view.
- **Attacker or failure mode**: a convenience field carrying identity data
  is added later; malicious variant: identity data hides in a free-text
  field's value.
- **Trust boundary**: `domain.py`/`events.py`/`projections.py` field-shape
  boundary.
- **Planned mitigation**: `HI-1` (no global user ID) and `HI-2` (no identity
  payload; key-name rejector refuses prohibited field names). Module
  `domain.py`, `events.py`, `projections.py`. Reason code: none — refusal is
  structural.
- **Detection**: PACK-10 section of `test_ct00_08_identity_leakage.py`.
- **Audit evidence**: the schema shape itself, once implemented, plus the
  rejector's own logged refusal.
- **Residual risk**: name-based checks, as PACK-02's threat model concedes
  for a sibling domain (its `T-10`), cannot catch identity data encoded as
  an innocuous field's value.
- **Future-pack dependency**: PACK-12 (DLP).

## T-26 — Bank-detail leakage

- **Protected asset**: absence of bank-account details (IBAN, account
  number, card data), named explicitly in section 9.3 as the place storage
  "feels natural."
- **Attacker or failure mode**: a future payment integration stores bank
  details on `ExpenseClaim`/`PaymentAuthorization` for convenience; the
  payment rail is out of scope (section 5).
- **Trust boundary**: `domain.py`/`expenses.py` field-shape boundary.
- **Planned mitigation**: `HI-2` (no identity/bank-detail payload) and
  section 9.3's prohibition. Module `domain.py`, `expenses.py`, `events.py`.
  Reason code: none dedicated — the field does not exist, matching T-25.
- **Detection**:
  `test_no_finance_event_payload_carries_identity_or_bank_detail`.
- **Audit evidence**: `payment.authorized`/`.settled` payloads
  (authorization id, payable reference, authority, amount) carry no bank
  fields.
- **Residual risk**: real payment/bank integration is unowned (section 5);
  the risk resurfaces if it is added without re-verifying this rule.
- **Future-pack dependency**: none — unowned integration risk.

## T-27 — Document-reference overclaim

- **Protected asset**: the boundary between holding a
  `FinanceEvidenceReference` and holding a verified fact about the document
  (authentic, signed, admitted, valid, publishable).
- **Attacker or failure mode**: a developer reads "has a reference" as
  "verified"; malicious variant: a forged reference forces a decision.
- **Trust boundary**: `references.py` `FinanceEvidenceReference` boundary.
- **Planned mitigation**: `HI-22` — placeholder-shaped only (`owner`,
  `kind`, `external_reference`, scope); no `is_authentic`/`is_signed`/
  `is_admitted`/`is_valid`/`is_publishable` field exists. Module
  `references.py`. Reason codes `FINANCE_EVIDENCE_REFERENCE_MISSING`,
  `FINANCE_EVIDENCE_ASSERTION_UNAVAILABLE`.
- **Detection**: `test_ct00_01` PACK-10 schema check — absence of
  document-content fields.
- **Audit evidence**: the reference's own recorded shape is the negative
  evidence; an unavailable assertion fails closed with a logged reason code.
- **Residual risk**: real and unclosed — until PACK-11 exists there is no
  way to verify authenticity, signature or admissibility at all.
- **Future-pack dependency**: PACK-11 (documents and evidence, section 12).

## T-28 — Legal-hold bypass

- **Protected asset**: a PACK-09 `LegalHold` blocking disposal of covered
  finance records.
- **Attacker or failure mode**: a disposal proceeds because a hold placed
  after the check began (a race) is unseen or was cached.
- **Trust boundary**: `application.py` disposal-relevant command boundary.
- **Planned mitigation**: `HI-23` — hold state re-read immediately before
  any disposal-relevant action, never cached. Module `application.py`.
  Reason codes `RECORD_UNDER_LEGAL_HOLD` (reused),
  `LEGAL_HOLD_STATE_UNKNOWN` (indeterminate, also fails closed).
- **Detection**:
  `test_a_hold_placed_after_authorization_still_blocks_a_finance_disposal`.
- **Audit evidence**: the refusal cites the `HoldRef`; PACK-09's own
  hold-placement trail cross-references the finance record.
- **Residual risk**: depends on PACK-09's hold-state read returning current
  data; a hold PACK-09 has not yet recorded cannot be honoured.
- **Future-pack dependency**: PACK-09 (hold-state authority, ADR-039).

## T-29 — Retention-policy rewrite

- **Protected asset**: retention cannot be shortened by rebinding a record
  to a different retention policy.
- **Attacker or failure mode**: an actor rebinds a record to a
  shorter-retention `RecordClass`; honest failure: a reclassification tool
  skips re-evaluation.
- **Trust boundary**: the binding to PACK-09 — PACK-10 binds to a
  `RecordClassRef` but does not own retention logic.
- **Planned mitigation**: `HI-24` — retention semantics, including
  supersession, stay PACK-09's. Module: none local, a cross-pack binding.
  Reason code `RETENTION_POLICY_REBIND_REQUIRES_REEVALUATION` (reused).
- **Detection**:
  `test_superseding_a_finance_retention_binding_does_not_shorten_an_active_obligation`.
- **Audit evidence**: the rebinding act is reason-coded and cross-referenced
  against the record's `RecordClassRef` history.
- **Residual risk**: PACK-10 only trusts PACK-09's supersession rule; a
  defect in that engine is outside PACK-10's reach.
- **Future-pack dependency**: PACK-09 (retention rules, ADR-039).

## T-30 — Export abuse

- **Protected asset**: finance data leaves only through one governed,
  policy-bound export surface.
- **Attacker or failure mode**: a second export builder bypasses
  classification; malicious variant: a bulk read via a debug path.
- **Trust boundary**: `projections.py` single-chokepoint export boundary
  (section 9.7).
- **Planned mitigation**: `HI-35` (read-only projections, no write-back) and
  `HI-47` (no direct access to another service's storage). Module
  `projections.py`. Reason code `DISCLOSURE_POLICY_VIOLATION` (reused).
- **Detection**:
  `test_service_boundaries.py::test_projections_module_performs_no_authoritative_write`.
  Section 9.7 states the design in prose but names no dedicated test proving
  no second export path exists — worth flagging as a gap.
- **Audit evidence**: every export carries a purpose, disclosure binding and
  per-field classification, logged at the chokepoint.
- **Residual risk**: the chokepoint is a precondition for PACK-12's DLP, not
  DLP itself; nothing yet inspects what leaves beyond classification.
- **Future-pack dependency**: PACK-12 (DLP, privileged administration).

## T-31 — Feature-flag bypass of an invariant

- **Protected asset**: no hard invariant can be disabled by configuration.
- **Attacker or failure mode**: not malicious in the plausible case — a flag
  gating an optional surface is later wired into an invariant check.
- **Trust boundary**: the configuration surface, read at command entry.
- **Planned mitigation**: `HI-45` — flags may gate optional read surfaces
  only; no flag is read inside an invariant check. Module: cross-cutting
  configuration, no single owner. Reason code: none.
- **Detection**: `test_no_invariant_check_reads_a_feature_flag`.
- **Audit evidence**: none produced directly — a structural, test-enforced
  guarantee, not an emitted event.
- **Residual risk**: defeatable by an indirect flag read the test's
  heuristic misses.
- **Future-pack dependency**: none.

## T-32 — Finance-to-voting correlation

- **Protected asset**: non-correlatability between a `FinancePartyHandle`
  and any voting/participation identity.
- **Attacker or failure mode**: an analyst joins finance timestamps or
  minting patterns with voting records; honest failure: a shared identifier
  appears later.
- **Trust boundary**: `domain.py` handle derivation and the service's import
  graph.
- **Planned mitigation**: `HI-37` (no vote/ballot/delegation/credential/
  tally linkage or import) and `HI-38` (handle non-derivable from any
  participation identifier). Module `domain.py`, `events.py`. Reason code:
  none — enforced by import-graph absence.
- **Detection**: PACK-10 section of `test_ct00_09_vote_linkability.py`.
- **Audit evidence**: `finance_party_handle.minted` carries "never any
  identifying attribute"; the import graph itself is inspectable evidence.
- **Residual risk**: mirrors PACK-02's own finding (its threat 4,
  "Correlation through timestamps"): no issuance-time batching or jitter
  exists, and real timestamps are required for `HI-52`.
- **Future-pack dependency**: PACK-07 (anti-correlation model, ADR-031,
  applied); timing correlation has no named owner.

## T-33 — Small-sample re-identification in a public view

- **Protected asset**: a public view does not let a reader infer an
  individual from a small cell or unusual combination.
- **Attacker or failure mode**: a small Kreisverband unit's donation view
  lets a reader infer the one plausible donor from amount and date.
- **Trust boundary**: `projections.py` disclosure-control boundary.
- **Planned mitigation**: `HI-36` — policy-driven minimum cell size and
  suppression applied before emission. Module `projections.py`. Reason code
  `FINANCE_STATISTICAL_DISCLOSURE_RISK`.
- **Detection**:
  `test_a_small_cell_view_is_suppressed_or_aggregated_before_emission`.
- **Audit evidence**: every public view carries its source version and
  generation time (`HI-35`); suppression decisions are logged at the
  chokepoint.
- **Residual risk**: disclosure thresholds are policy inputs whose defaults
  are "legally and statistically unverified" (section 4.11); effectiveness
  at any threshold is unproven.
- **Future-pack dependency**: none; depends on owner and legal confirmation
  of the threshold.

## T-34 — Handle resolution abuse by an authorized resolver

- **Protected asset**: how, and how often, an authorized resolver may
  connect a `FinancePartyHandle` to identifying evidence.
- **Attacker or failure mode**: an actor holding resolution authority
  resolves handles beyond the stated purpose that justified it.
- **Trust boundary**: `partyregistry.py` — the only module permitted to
  resolve a handle at all.
- **Planned mitigation**: `HI-1`/`HI-48` (purpose-scoped handles) plus
  section 9.5's separate resolution authority and the
  `finance_party_handle.resolved` event. Module `partyregistry.py`. Reason
  code `FINANCE_PARTY_HANDLE_RESOLUTION_DENIED`.
- **Detection**:
  `test_the_same_legal_person_gets_unequal_handles_for_unequal_purposes`
  covers purpose-scoping; no test targets resolution-frequency abuse.
- **Audit evidence**: `.resolved` records who resolved what, under which
  authority, for which purpose — carrying no resolved value itself.
- **Residual risk**: named explicitly (section 16, point 4): the handle
  limits correlation, not lawful resolution; no check evaluates necessity.
- **Future-pack dependency**: PACK-12 (the DLP layer named to constrain
  access, section 16 point 4).

## T-35 — Policy backdating to legitimise a past decision

- **Protected asset**: `FinancePolicy` effective dating and its binding to
  decisions already made.
- **Attacker or failure mode**: a new policy version's `effective_from`
  reaches back before a disputed decision, hoping it appears compliant
  retroactively.
- **Trust boundary**: `policy.py` effective-dating boundary.
- **Planned mitigation**: the section 13 rule against backdating
  `effective_from` into a closed/submitted period, plus `HI-44` (unknown
  policy fails closed) and a decision binding to a stored
  `FinancePolicyBinding`, not a read-time lookup. Module `policy.py`. Reason
  codes `FINANCE_POLICY_VERSION_UNKNOWN`, `FINANCE_POLICY_MISSING`.
- **Detection**: the six "unknown fails closed" `HI-44` tests cover an
  unresolvable reference; none targets backdating specifically.
- **Audit evidence**: `finance_policy.version_published` carries effective
  dates and approving authority; a stored `FinancePolicyBinding` means a
  later version cannot retroactively appear in a past decision.
- **Residual risk**: the backdating prohibition is a stated rule in prose,
  not tied to a numbered invariant or a named test in section 6.
- **Future-pack dependency**: none.

## Residual risks that PACK-10 does not close

Four residual risks are named in `PACK-10-SPECIFICATION.md` section 16 as
severe enough to state in the specification itself, because no PACK-10
mechanism closes them. They are restated here, tied back to the threats
above that instantiate each:

1. **Collusion of two or more authorized authorities** defeats every
   separation-of-duties rule here. PACK-10 makes it evidenced — history,
   distinct authority references, the audit chain (`HI-52`) — not
   impossible. See T-13, T-16, T-18, T-20.

2. **False external acceptance** is prevented in the data model (`HI-27`),
   but the recorded reference still depends on a human recording it
   correctly, with no gateway to verify it (section 5, OD-16). See T-21.

3. **Undisclosed intermediary and beneficial-origin concealment** cannot be
   detected by a system receiving only what a contributor declares. PACK-10
   fails closed but cannot discover a concealed principal. See T-08, T-09,
   T-10, T-11.

4. **Identity re-identification by an authorized resolver** is inherent in
   section 9.8: the handle limits correlation, not lawful resolution.
   PACK-12's future DLP layer constrains access. See T-25, T-30, T-34.

A fifth risk emerges from reading the thirty-five threats together and is
this document's own addition — not named in `PACK-10-SPECIFICATION.md`
section 16:

5. **Application-layer immutability has no storage-layer backstop.** `HI-5`,
   `HI-6`, `HI-25` and `HI-26` enforce their guarantees only inside
   `finance-service`'s own command and store-protocol code (T-01, T-02,
   T-19, T-22) — no database constraint, write-once medium or external
   anchoring backs any of them. Every guarantee holds only because no other
   write path exists yet, not because one has been ruled out. This is the
   same shape of gap PACK-02's own threat model names for its audit hash
   chain (its threat 9: detects an edit left in place, not a fully
   self-consistent rewrite); PACK-10 inherits it across a wider set of
   records, closed only when PACK-13's production data plane adds real
   storage-level enforcement.
