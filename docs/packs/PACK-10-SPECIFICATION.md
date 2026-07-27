# CLAUDE-PACK-10 — Party Finance, Rechenschaftsbericht & Financial External Influence: Specification

## 0. Status and baseline

**Status: PACK-10 SPECIFICATION CANDIDATE.** This document is a
specification and ADR-phase artefact submitted for architectural review.
It is not a PASS release, it authorizes no implementation, and nothing in
it has been built.

|                            |                                                                                                                        |
| -------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| Baseline archive           | `epd2-civic-os-PACK-09-IMPLEMENTATION-0.9.0-PASS.zip`                                                                  |
| Repository version         | `0.9.0` — **unchanged by this round**                                                                                  |
| Canon version              | `0.7.0` — **unchanged by this round**                                                                                  |
| Confirmed baseline         | PACK-01 through PACK-09 FINAL PASS; PACK-09 closed                                                                     |
| New services               | none created this round; one proposed (`services/finance-service`, ADR-044)                                            |
| ADRs                       | ADR-044 through ADR-049, all `proposed`                                                                                |
| Canon amendment            | **required** — see `PACK-10-CANON-AMENDMENT-ASSESSMENT.md` and `PACK-10-CANON-AMENDMENT-PROPOSAL.md` (`0.7.0 → 0.8.0`) |
| Builds on                  | PACK-08 organizational substrate; PACK-09 records, cases, deadlines, notices, holds — by typed reference only          |
| Production code this round | none                                                                                                                   |

The baseline's own external verification result (556 required paths;
Python 2659 passed / 4 skipped; TypeScript 3 passed; frontend 11 passed;
Prettier, Ruff, mypy, Next.js build all PASS) belongs to PACK-09 and is
neither re-run nor re-claimed here. What this round did and did not verify
locally is stated exactly in section 20 and in
`docs/handover/PACK-10-SPEC-REPORT.md`.

Accepted PACK-01 through PACK-09 architecture is not regressed, replaced,
redesigned or reinterpreted anywhere in this document. Where PACK-10 needs
something an earlier pack owns, it consumes that pack's published typed
interface and says so.

## 1. Mission

PACK-10 specifies the governed party-finance domain: internal party
accounting, legally governed income and expenditure, donation and
contribution governance, sponsorship and other financially relevant
external influence, reimbursement and expense workflows, assets and
financial obligations, organizationally scoped budgets and accounting
periods, the preparation → review → approval → correction → publication
lifecycle of the German party financial accountability report
(`Rechenschaftsbericht`), independent finance audit, traceable links to
PACK-09 legal cases, deadlines, holds, notices and evidence references,
and public financial transparency read models that do not expose
protected personal data.

PACK-10 establishes a **domain model and trust boundaries**. It is a
specification of what must hold, where it is enforced and how it will be
proven.

PACK-10 does **not** claim, and must not be read to claim, that the
resulting system is legally activated, legally sufficient, tax-compliant,
production-ready, certified, or accepted by any German authority. Section
22 states this in full, and every reason code, invariant and lifecycle in
this document is written so that no such claim can be inferred from a
successful operation.

## 2. What this round is, and what it is not

This round produces exactly five things:

1. PACK-10 architecture analysis of the baseline repository.
2. This normative specification.
3. Six proposed ADRs (ADR-044 through ADR-049).
4. An explicit canon-amendment determination, with a proposal document.
5. An implementation plan and acceptance matrix.

It is **not** an implementation task. No production code, no service
directory, no runtime schema, no OpenAPI operation, no frontend screen, no
migration and no executable test was written. Test and acceptance planning
exists in this round only as documentation
(`PACK-10-ACCEPTANCE-MATRIX.md`, `PACK-10-IMPLEMENTATION-PLAN.md`).

Unchanged by this round, deliberately: `REPOSITORY_VERSION`,
`CANON_VERSION`, package versions, source code, runtime contracts
(`contracts/**`), CI configuration, and repository-checker behaviour
(`scripts/check_repository.py` — its required-path list is not extended;
this follows the same precedent as ADR-026 through ADR-037, which were
never added to that list either, recorded in the file's own comment).

## 3. Terminology — concepts this specification refuses to conflate

Party finance is a domain where a single sloppy synonym destroys either
the audit trail or the privacy model. Nine pairs are kept apart
throughout:

1. **Financial transaction** (the governed business fact: money moved,
   or an obligation arose, with provenance) versus **journal entry** (the
   balanced double-entry accounting record that represents it). One
   transaction produces one or more journal entries; a journal entry
   never exists without an authoritative reason for it.
2. **Correction** (a new, governed record that changes the outcome)
   versus **mutation** (overwriting a record). PACK-10 has the former and
   structurally lacks the latter for posted entries.
3. **Contribution** in the party-finance sense (money, in-kind value or
   benefit given to the party) versus **`Contribution`** in canon 13.2 (a
   deliberation utterance). These are different entities in different
   contexts. Two consequences are normative. First, the aggregate's
   canonical and class name is **`FinanceContribution`** — canon section
   22's ownership matrix cannot hold two rows named `Contribution`, and
   the finance one is the newcomer. Second, every PACK-10 event and
   reason code for the concept carries the `finance_`/`FINANCE_` prefix
   (section 14, section 15). Section 8 writes the short form
   `Contribution` only inside the finance module discussion, where the
   context is unambiguous; the canonical name is the prefixed one.
4. **Donation** (a contribution given without counter-performance)
   versus **sponsorship** (a payment or benefit with agreed
   counter-performance). The distinction is legally consequential and is
   never inferred from the amount or the payer.
5. **Submission** (the party sent the report) versus **acceptance** (a
   competent authority has determined the report is accepted). PACK-10
   can record the first from its own state; it can record the second only
   from an explicit authoritative reference or governed decision.
6. **Publication** (the report was made publicly readable) versus
   **approval** (an authorized body approved it). Neither implies the
   other.
7. **Budget** (an intention, versioned and approved) versus **ledger
   actuals** (what happened). A budget never becomes a source of truth
   for actuals.
8. **Reporting perimeter** (which organizational units and accounts a
   report covers, as of the period) versus **current organizational
   hierarchy** (which may have changed since). A closed period keeps its
   historical perimeter.
9. **Finance evidence reference** (a scoped pointer to material PACK-11
   will own) versus **evidence** (the document bytes, custody, signature
   and admissibility decision). PACK-10 holds only the former and asserts
   nothing about authenticity from holding it.

Three PACK-08 concepts are used exactly as PACK-08 defines them and never
redefined here: `Organization`/`OrganizationalUnit`,
`OrganizationalScope`, and `OrganizationalAuthority` (institutional role
assignment). Two PACK-09 concepts likewise: the governed record with its
`RecordClass`/retention binding, and the `LegalCase`/`ProceduralDeadline`/
`OfficialNotice`/`NoticeEffectDecision`/`LegalHold` complex.

## 4. Scope — capability groups

PACK-10 must specify eleven capability groups. Each subsection below is
normative for the implementation round; the aggregate-level detail is
section 8.

### 4.1 A — Finance ledger and accounting periods

Specified: organizationally scoped `FinanceAccount`; governed account
classification (a `FinancePolicy` of kind `chart_of_accounts`, not a free
string on the account); `AccountingPeriod`; `JournalEntry` with balanced
`PostingLine`s; debit and credit lines; transaction date, posting date and
value date where needed; explicit currency and amount rules; correction
and reversal; period opening and closing; period lock; controlled
reopening; provenance of imported and manually entered transactions
(`ImportBatch`); reconciliation status and evidence references
(`ReconciliationRecord`).

**Authoritative-model decision (ADR-045): layered, with a single
authoritative money layer.** The double-entry general ledger
(`JournalEntry` + `PostingLine`) is the authoritative record of monetary
effect. The transaction register (`FinancialTransaction`) is the
authoritative record of the _business fact and its provenance_ — what
happened, who it involved as a purpose-scoped reference, which policy
version classified it, which evidence is cited, which import batch it
came from. Neither is a cache of the other, and no third layer is
authoritative for anything: trial balances, period totals,
budget-versus-actual views and public views are all derived read models.
A `FinancialTransaction` that has monetary effect and no balanced,
posted `JournalEntry` is an incomplete state that fails closed on
reporting, not a silently accepted record. Full option analysis:
ADR-045.

### 4.2 B — Income

Governed treatment is specified for: membership contributions;
elected-office-holder contributions and similar party levies;
donations; sponsorship income; event and publication income; public
funding; grants and reimbursements received; asset income; other income.

The income taxonomy is a versioned `FinancePolicy` of kind
`income_classification`, extensible by governed policy version — and
constrained so that extension cannot become evasion: reclassifying an
existing record requires an authorized, reason-coded, append-only
reclassification with the prior classification preserved, and any
reclassification that would move a record out of a disclosure,
aggregation, review or legal-limit obligation is refused
(`FINANCE_RECLASSIFICATION_BYPASS_DENIED`, HI-13). Classification is
never inferred from the amount alone.

### 4.3 C — Expenditure

Governed treatment is specified for: operating, personnel, campaign,
event expenditure; procurement; travel and reimbursement; communication
and advertising; professional services; transfers between organizational
units; refunds; other expenditure. Same policy mechanism as income
(`expenditure_classification`), same anti-reclassification rule, same
requirement that a payment has an authorization distinct from its
execution (section 4.10, HI-32, HI-48).

Transfers between organizational units are modelled as two scoped
transactions bound by one `internal_transfer_reference`, precisely so
consolidation can eliminate them exactly once (HI-39, section 10).

### 4.4 D — Donations and contributions

Specified: a donor/contributor reference that is purpose-scoped and
introduces no global user ID (section 9); natural-person, legal-person
and other legally relevant contributor categories as policy-governed
values; the exceptional contribution states (anonymous, unverifiable,
prohibited, restricted, foreign-linked, intermediary-suspected, other
governed exception); acceptance; provisional quarantine; rejection;
return; remittance or escalation where legally required; aggregation
across a legally relevant reporting period; threshold evaluation; source
and beneficial-origin declarations; contribution method; in-kind
valuation; related-party and intermediary indicators; conflict-of-interest
review; required evidence and document references; append-only decision
history; reason-coded denials.

Three hard rules govern this group:

- **Fail closed on the unknown.** An anonymous or unverifiable
  contribution does not become an ordinary accepted contribution: it
  enters a governed exceptional state
  (`FINANCE_CONTRIBUTION_SOURCE_UNDETERMINED`,
  `FINANCE_CONTRIBUTION_VERIFICATION_INCOMPLETE`, HI-16, HI-17).
- **Aggregation is not defeatable by splitting.** Threshold evaluation
  runs on the aggregate over the policy's relevant period and perimeter,
  on the purpose-scoped party handle, and known related or intermediary
  contributions are aggregated even when they arrived separately (HI-14,
  HI-15).
- **Thresholds are governed policy inputs, not constants.** No German
  legal threshold is compiled into application code as an immutable
  constant. Every threshold, category and restriction lives in an
  effective-dated, versioned `FinancePolicy` with jurisdiction and scope,
  and every protected decision binds to the policy version it used
  (section 13, HI-44). This specification proposes no legal threshold
  value as fact; where a default is suggested at all it is marked as
  legally unverified in `PACK-10-OPEN-DECISIONS.md`.

### 4.5 E — Sponsorship and financial external influence

PACK-10 owns the financial record and financial disclosure of:
sponsorship agreements, the sponsoring party (as a purpose-scoped
reference), the recipient organization, amount or valuation, benefit
provided, counter-performance, purpose, campaign/event/publication/
initiative association, intermediary and beneficial-origin declarations,
approval, conflict review, disclosure classification, and evidence and
document references.

PACK-10 may additionally define financially relevant external-benefit
records: paid third-party support, in-kind campaign support, subsidized
services, guarantees, forgiven debt, and other financially measurable
external benefits (`ExternalFinancialBenefit`, section 8).

PACK-10 does **not** implement the general lobbying and meeting
disclosure domain. The register of lobbying contacts, meetings, access,
calendars and non-financial influence disclosures belongs to PACK-35.
PACK-10 exposes typed integration points for that future pack
(`PACK-10-CROSS-PACK-BOUNDARIES.md` section 5) and implements none of its
entities (HI-21).

The boundary rule, stated so it can be tested: a record belongs to
PACK-10 when its subject is a **measurable financial value or a
financially valued benefit** attributable to a party organization; it
belongs to PACK-35 when its subject is a **contact, meeting, access or
influence relationship** without a financial value being recorded. A
meeting that produced a sponsorship agreement yields a PACK-10
`SponsorshipAgreement` and, later, a PACK-35 meeting record — two
records, one typed reference, neither owning the other. Where the
division is legally uncertain it is recorded as an open decision
(OD-19), not silently resolved.

### 4.6 F — Expense and reimbursement workflow

Specified: `ExpenseClaim` with claimant reference (purpose-scoped),
organizational scope, purpose, amount, evidence references; submission;
review; approval or rejection; payment authorization; settlement;
correction; conflict checks; and segregation of requester, approver and
payment executor where required (HI-32, HI-48; ADR-048).

### 4.7 G — Assets, liabilities and obligations

Specified: `FinancialAsset` (including a typed reference to a tangible or
intangible asset where financially relevant); and `FinancialObligation`
covering receivable, payable, loan, credit, guarantee, contingent
liability and long-term obligation as governed obligation types — with
write-off, valuation date, valuation method reference, evidence, and
review/approval history.

`Liability` is deliberately **not** a separate aggregate: it is
`FinancialObligation` with an obligation type, because splitting them
would duplicate an identical lifecycle and valuation model (section 8.3).

PACK-10 creates no general asset-management system beyond what governed
party-finance accounting and reporting require: no maintenance
scheduling, no inventory operations, no depreciation engine beyond a
recorded valuation method and valuation date.

### 4.8 H — Budgets

Specified: organizational `Budget`; budget period; `BudgetLine`;
allocation; reserved, committed and actual amounts; amendment; approval;
version history; scope inheritance rules; and whether and how higher
organizational levels may consolidate lower-level budgets.

Normative: a budget never overwrites the ledger and never becomes an
alternative source of truth for actual transactions (HI-12). "Actual" on
a budget line is a derived read model computed from posted ledger
entries, not a stored, separately writable number. Reserved and
committed amounts are budget-domain facts and are never presented as
accounting balances.

### 4.9 I — Rechenschaftsbericht lifecycle

Specified as a governed lifecycle: reporting obligation; reporting
period; reporting perimeter; organizational consolidation; report
preparation; source-data freeze/snapshot; validation; reconciliation;
finance-auditor review; correction request; management or board approval;
legally responsible sign-off; submission; receipt or acknowledgement;
publication; amendment; restatement; preservation of prior versions.

The lifecycle distinguishes, as separate and separately authorized
states: `draft`, `internally_reviewed`, `auditor_reviewed`, `approved`,
`signed`, `submitted`, `externally_acknowledged`, `accepted_by_authority`,
`published`, `amended_or_restated`.

Three rules are structural, not procedural:

- The system never infers legal acceptance from upload, delivery
  telemetry, read status, publication or submission (HI-27, HI-28,
  HI-29). `accepted_by_authority` is reachable only from an explicit
  authoritative reference — in this architecture, a PACK-09
  `NoticeEffectRef` produced by a governed `NoticeEffectDecision`
  (ADR-043) or an equivalent recorded governed decision.
- A newer report version never destroys or overwrites an earlier
  submitted or published version (HI-26); versions are append-only and
  each keeps its own snapshot.
- A report is only preparable from a frozen `ReportSnapshot` that binds
  the period locks, the policy versions and the ledger state it was
  computed from (HI-25). No snapshot, no validation, no submission
  (`FINANCE_REPORT_SNAPSHOT_MISSING`).

### 4.10 J — Finance audit

Specified: the authority and workflow of the existing PACK-08
institutional role `finance_auditor` — an `AuditEngagement` with
`AuditFinding`s and one create-once `AuditConclusion`.

The accepted incompatibility is preserved verbatim: a finance auditor
must not simultaneously be finance administrator in the same legally
relevant scope (PACK-08 section 9.3 rule 3, canon 19e.16; HI-31).

Separation is analysed and specified among: transaction creator;
transaction reviewer; finance administrator; payment authorizer; payment
executor; report preparer; report approver; legally responsible
signatory; finance auditor (ADR-048). Of these, four are proposed as new
**institutional** roles extending PACK-08's `OrganizationalAuthority`
`role_code` set (`finance_administrator`, `payment_authorizer`,
`payment_executor`, `report_signatory`); the remaining five are
**action-level** separations recorded on the action, not new privileged
roles — because inventing nine institutional roles where four suffice
would silently expand the platform's privilege surface.

No globally privileged role is introduced. Every proposed institutional
role is justified, scoped to a single `OrganizationalScope`,
effective-dated, revocable with a reason reference, and carries an
explicit incompatibility set aligned with PACK-08 section 9.3 (HI-53,
ADR-048).

One pre-existing canon gap surfaced during this analysis and is recorded
rather than quietly patched: canon 19e.16 rule 3 forbids combining
`finance auditor` with `finance administrator`, but `finance_administrator`
is **not** among the `role_code` values canon 19e.15 enumerates. The canon
therefore forbids a combination involving a role it never defines — which
is coherent only because PACK-08 explicitly reserved the finance
preparation/approval roles for PACK-10 (PACK-08 specification section 9.3,
"PACK-10 will need to extend this set once such roles exist"). The
amendment proposal closes the gap by enumerating the four new role codes
in the same round that extends the incompatibility baseline
(`PACK-10-CANON-AMENDMENT-PROPOSAL.md`).

### 4.11 K — Public transparency

Specified: safe derived public views for legally publishable financial
information. Public views must be derived from governed authoritative
records; preserve the publication version; expose provenance and update
status; distinguish draft from officially published information; avoid
protected identity information; support legally required aggregation;
apply statistical disclosure control where small samples or combinations
could expose individuals; and never become the authoritative accounting
source (HI-35, HI-36).

The disclosure mechanism reuses PACK-04's accepted model rather than
inventing a second one: a `FinancePolicy` of kind `public_disclosure`
carries per-field disclosure classes, and a structurally prohibited field
can never be reclassified into a publishable class (canon 19a.3's rule,
restated for finance fields; HI-36). Statistical disclosure thresholds
are policy inputs with recommended defaults marked legally and
statistically unverified (OD-13).

## 5. Explicitly out of scope

PACK-10 defers, and this specification implements nothing for:

- document bytes and document storage; cryptographically linked
  document-version history; signed-original verification; general
  evidence custody; evidence content — **PACK-11**;
- privileged JIT/break-glass administration; DLP implementation —
  **PACK-12**;
- production database; event bus; canonical schema registry
  implementation; production API/event evolution infrastructure —
  **PACK-13**;
- real IAM/eID; credential issuance; qualified electronic signatures —
  **PACK-14** (qualified signatures additionally depend on PACK-11's
  signed-original model);
- payment-provider integration; bank API or PSD2 integration; automated
  bank transfers; tax filing integration; real external-authority
  submission gateway — **no pack owns these yet**; PACK-10 models the
  governed facts (`PaymentAuthorization`, `SubmissionRecord`,
  `ImportBatch`) that such an integration would later feed, and nothing
  else (OD-16);
- voting; tally; delegation; voting-client integration — **PACK-15/16**
  and the existing accepted voting architecture, from which PACK-10 is
  structurally isolated (HI-37, HI-38);
- general lobbying-contact and meeting register; parliamentary
  mandate-holder disclosure — **PACK-35**;
- public procurement as a general domain; campaign-management
  functionality beyond financially governed references;
- production incident response — **PACK-17**;
- user-facing production applications — **PACK-18**;
- legal activation of any kind.

Ownership that remains where it is: PACK-11 owns governed documents and
evidence content. PACK-12 owns privileged administration and DLP. PACK-13
owns the production data plane and canonical schema registry
implementation. PACK-14 owns real identity/auth gateways. PACK-35 owns
general lobbying and meeting disclosure. PACK-09 keeps ownership of legal
cases, procedural deadlines, official notices, notice-effect decisions,
legal holds and record classes; PACK-08 keeps ownership of organizations,
organizational units, organizational scope and institutional authority
assignments.

## 6. Hard invariants

These are requirements, not goals. The first 46 rows are the minimum set
the governing request fixed; rows 47–55 were added by the baseline
repository analysis, because every one of them is a convention PACK-02
through PACK-09 already enforce and a finance service that omitted it
would be the first regression in the repository.

Each row names the planned architectural enforcement point, the planned
mechanism, the planned test that proves it, the reason code or fail-closed
behaviour, and the cross-pack dependency. Nothing in this table is
implemented; `PACK-10-ACCEPTANCE-MATRIX.md` restates every test with its
full planned path and is the document the implementation round is measured
against.

| #   | Invariant                                                                                                                        | Planned enforcement point                                 | Planned mechanism                                                                                                                                        | Planned test                                                                                                            | Reason code / fail-closed behaviour                                                                                                                                                                              | Cross-pack dependency                                |
| --- | -------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------- |
| 1   | No global user ID                                                                                                                | `finance-service/domain.py`, `references.py`              | Purpose-scoped `FinancePartyHandle` minted per (perimeter, purpose, policy version); no `user_id`/`person_id`/`member_id` field on any dataclass         | `test_ct00_08_identity_leakage.py` PACK-10 section, exhaustive over every dataclass                                     | structural — the field does not exist                                                                                                                                                                            | PACK-08 scope; PACK-09 `CasePartyRef` precedent      |
| 2   | No identity payload in financial events, audit records, public views or cross-service references                                 | `events.py`, `projections.py`, `references.py`            | Payload builders accept ids, enums, timestamps, reason codes, policy versions only; a key-name rejector mirrors PACK-09's `reject_identity_payload_keys` | `test_no_finance_event_payload_carries_identity_or_bank_detail`                                                         | structural + refusal on prohibited key                                                                                                                                                                           | PACK-09 audit conventions                            |
| 3   | Organization-scope isolation for Bund/Land/Kreis and any other governed organizational scope                                     | `application.py` scope guard; `storage.py` scoped lookups | `RequestContext` carrying an `OrganizationalScope`; `_require_scope` on every command; scoped queries only                                               | `test_application.py` scope-isolation suite; `test_storage.py` scoped-lookup suite                                      | `ORGANIZATION_SCOPE_MISMATCH`; foreign records report as not found                                                                                                                                               | PACK-08 (`OrganizationalScope`, ADR-034)             |
| 4   | Default deny when organizational scope cannot be determined                                                                      | `application.py` guard order                              | Scope resolution precedes every other check and raises before any read or write                                                                          | `test_an_undetermined_scope_denies_before_any_other_check`                                                              | `ORGANIZATION_SCOPE_UNDETERMINED`                                                                                                                                                                                | PACK-08 default-deny model                           |
| 5   | Financial records cannot be silently deleted                                                                                     | `storage.py`                                              | No delete method on any store protocol or adapter; disposal only through PACK-09's governed disposition workflow                                         | `test_service_boundaries.py::test_finance_service_storage_exposes_no_delete_operation`                                  | structural                                                                                                                                                                                                       | PACK-09 (retention, disposal)                        |
| 6   | Posted entries are immutable; corrections occur through governed reversal or correcting entries                                  | `domain.py` `JournalEntry`                                | `posted` is terminal for content; create-once posting record; reversal creates a new entry referencing the original                                      | `test_a_posted_journal_entry_cannot_be_edited_only_reversed`                                                            | `FINANCE_IMMUTABLE_RECORD_MODIFICATION_ATTEMPTED`                                                                                                                                                                | —                                                    |
| 7   | Every ledger transaction must remain balanced                                                                                    | `domain.py` `assert_balanced`                             | Sum of debit minor units equals sum of credit minor units per currency, checked in the constructor and again at posting                                  | `test_an_unbalanced_entry_cannot_be_constructed_or_posted`                                                              | `FINANCE_JOURNAL_ENTRY_UNBALANCED`                                                                                                                                                                               | —                                                    |
| 8   | Currency and amount semantics must be explicit and deterministic                                                                 | `domain.py` `Money`                                       | `Money(minor_units, currency_code, scale)`; no implicit currency; no cross-currency arithmetic without a recorded conversion                             | `test_money_refuses_mixed_currency_arithmetic`                                                                          | `FINANCE_CURRENCY_UNSUPPORTED`                                                                                                                                                                                   | —                                                    |
| 9   | No floating-point money representation                                                                                           | `domain.py` `Money`; contract schemas                     | Integer minor units and an explicit scale; JSON Schema forbids `number` for monetary fields                                                              | `test_property_based.py` money round-trip; `test_openapi_contract.py` money-serialization check                         | `FINANCE_MONETARY_AMOUNT_INVALID`                                                                                                                                                                                | PACK-13 later owns wire evolution                    |
| 10  | Accounting-period closure cannot be bypassed by ordinary write operations                                                        | `application.py` posting commands                         | Period lock re-checked inside each posting command, not only at intake                                                                                   | `test_a_closed_period_refuses_every_ordinary_posting_path`                                                              | `FINANCE_ACCOUNTING_PERIOD_CLOSED`                                                                                                                                                                               | —                                                    |
| 11  | Reopening a closed period requires explicit authority, reason, audit trail and preserved prior state                             | `application.py` `reopen_accounting_period`               | Distinct command, distinct authority, mandatory reason reference, create-once `PeriodReopeningRecord` snapshotting the closed state                      | `test_reopening_preserves_the_closed_state_and_requires_authority`                                                      | `FINANCE_PERIOD_REOPENING_NOT_AUTHORIZED`                                                                                                                                                                        | PACK-08 authority resolution                         |
| 12  | A budget cannot rewrite actual ledger transactions                                                                               | module boundary `budgets.py` → `ledger.py`                | No write path from budget code to ledger stores; `actual_amount` is a derived read model                                                                 | `test_service_boundaries.py::test_budget_module_has_no_ledger_write_import`                                             | structural                                                                                                                                                                                                       | —                                                    |
| 13  | Reclassification cannot be used to bypass disclosure, review, aggregation or reporting rules                                     | `application.py` `reclassify_*`                           | Reclassification is an authorized, append-only act; the target class is evaluated against the obligations already attached to the record                 | `test_reclassification_that_would_drop_a_disclosure_obligation_is_refused`                                              | `FINANCE_RECLASSIFICATION_BYPASS_DENIED`                                                                                                                                                                         | —                                                    |
| 14  | Donation aggregation cannot be bypassed by splitting transactions within the relevant policy period and scope                    | `contributions.py` aggregation                            | Aggregation key is (party handle, policy period, perimeter, policy version); evaluation runs on the aggregate, never on the single contribution          | `test_four_split_contributions_aggregate_to_one_threshold_evaluation`                                                   | `FINANCE_CONTRIBUTION_AGGREGATION_UNRESOLVED`                                                                                                                                                                    | —                                                    |
| 15  | Known related or intermediary contributions cannot be treated as unrelated solely because they arrived as separate transactions  | `contributions.py` aggregation                            | Declared `related_party_group_reference` and `intermediary_declaration` extend the aggregation key set                                                   | `test_a_declared_intermediary_chain_aggregates_with_its_principal`                                                      | `FINANCE_CONTRIBUTION_AGGREGATION_UNRESOLVED`                                                                                                                                                                    | —                                                    |
| 16  | Anonymous or unverifiable contributions fail closed into a governed exceptional state                                            | `contributions.py` `assess_contribution`                  | Exceptional state enum; `quarantined` is the default landing state, never `accepted`                                                                     | `test_an_unverifiable_contribution_lands_in_quarantine_not_accepted`                                                    | `FINANCE_CONTRIBUTION_SOURCE_UNDETERMINED`, `FINANCE_CONTRIBUTION_VERIFICATION_INCOMPLETE`                                                                                                                       | —                                                    |
| 17  | Prohibited or uncertain contributions are not silently accepted                                                                  | `contributions.py` decision guard                         | Acceptance requires a resolved, policy-bound assessment; unresolved assessment blocks acceptance                                                         | `test_acceptance_requires_a_resolved_policy_bound_assessment`                                                           | `FINANCE_CONTRIBUTION_PROHIBITED`                                                                                                                                                                                | —                                                    |
| 18  | Return, rejection or escalation of a contribution preserves the original receipt record                                          | `domain.py` `Contribution`                                | Create-once receipt; decisions are append-only history entries, never edits to the receipt                                                               | `test_the_original_receipt_survives_return_rejection_and_escalation`                                                    | structural                                                                                                                                                                                                       | PACK-09 (escalation to a legal case)                 |
| 19  | In-kind contributions require an explicit valuation basis and evidence reference                                                 | `domain.py` `InKindValuation`                             | Valuation method, valuation date and evidence reference are mandatory for non-monetary contributions                                                     | `test_an_in_kind_contribution_without_a_valuation_basis_is_refused`                                                     | `FINANCE_IN_KIND_VALUATION_MISSING`, `FINANCE_EVIDENCE_REFERENCE_MISSING`                                                                                                                                        | PACK-11 (evidence content)                           |
| 20  | Sponsorship must record both financial value and counter-performance where applicable                                            | `domain.py` `SponsorshipAgreement`                        | Counter-performance description is mandatory unless the agreement is classified as without counter-performance by policy                                 | `test_sponsorship_without_counter_performance_needs_an_explicit_policy_classification`                                  | `FINANCE_COUNTER_PERFORMANCE_MISSING`                                                                                                                                                                            | PACK-35 (non-financial influence)                    |
| 21  | General lobbying meetings are not implemented in PACK-10                                                                         | absence of a module                                       | No meeting, contact, calendar or access entity anywhere in the service                                                                                   | `test_service_boundaries.py::test_no_pack35_lobbying_entity_exists_in_finance_service`                                  | structural                                                                                                                                                                                                       | PACK-35                                              |
| 22  | Finance evidence references do not make PACK-10 owner of document or evidence content                                            | `references.py`                                           | Placeholder-shaped references only (`owner`, `kind`, `external_reference`, scope); no bytes, no hash chain, no signature field                           | `test_ct00_01` PACK-10 schema check: absence of document-content fields                                                 | structural                                                                                                                                                                                                       | PACK-11                                              |
| 23  | Legal Hold overrides destruction or ordinary retention expiry                                                                    | `application.py` disposal-relevant commands               | PACK-09 hold state is re-read immediately before any disposal-relevant action, never cached                                                              | `test_a_hold_placed_after_authorization_still_blocks_a_finance_disposal`                                                | `RECORD_UNDER_LEGAL_HOLD`                                                                                                                                                                                        | PACK-09 (`HoldRef`, ADR-039)                         |
| 24  | Record retention cannot be bypassed by policy replacement                                                                        | binding to PACK-09                                        | Finance records bind to a PACK-09 `RecordClassRef`; retention semantics stay PACK-09's, including its supersession rule                                  | `test_superseding_a_finance_retention_binding_does_not_shorten_an_active_obligation`                                    | `RETENTION_POLICY_REBIND_REQUIRES_REEVALUATION`                                                                                                                                                                  | PACK-09 (ADR-039)                                    |
| 25  | Report source snapshots and versions are preserved                                                                               | `reporting.py`                                            | Create-once `ReportSnapshot`; append-only `FinanceReportVersion` chain                                                                                   | `test_a_report_snapshot_is_write_once_and_survives_every_later_version`                                                 | `FINANCE_REPORT_SNAPSHOT_MISSING`                                                                                                                                                                                | —                                                    |
| 26  | A newer Rechenschaftsbericht version never destroys or overwrites an earlier submitted or published version                      | `reporting.py`, `storage.py`                              | Versions are separate records; no update path to a version that has a `SubmissionRecord` or `PublicationRecord`                                          | `test_an_amendment_creates_a_new_version_and_leaves_the_submitted_one_intact`                                           | `FINANCE_IMMUTABLE_RECORD_MODIFICATION_ATTEMPTED`                                                                                                                                                                | —                                                    |
| 27  | Submission is not acceptance                                                                                                     | `reporting.py` state machine                              | `submitted` and `accepted_by_authority` are separate states; the transition requires an authoritative reference                                          | `test_submission_alone_never_reaches_accepted_by_authority`                                                             | `FINANCE_EXTERNAL_ACKNOWLEDGEMENT_NOT_AUTHORITATIVE`                                                                                                                                                             | PACK-09 (`NoticeEffectRef`, ADR-043)                 |
| 28  | Delivery/read telemetry is not legal effect                                                                                      | `reporting.py`                                            | No telemetry field is an input to any state transition; telemetry is recorded on a separate create-once record                                           | `test_no_delivery_telemetry_field_can_drive_a_report_transition`                                                        | structural                                                                                                                                                                                                       | PACK-09 (ADR-043's three-object model)               |
| 29  | Publication is not authoritative approval unless separately decided                                                              | `reporting.py`, `projections.py`                          | Publication requires an existing approval **and** a separate publication authorization; publishing does not set approval                                 | `test_publication_does_not_imply_approval_and_vice_versa`                                                               | `PUBLICATION_NOT_ALLOWED`                                                                                                                                                                                        | PACK-04 disclosure precedent                         |
| 30  | Finance auditor independence is enforced                                                                                         | `domain.py` `assert_auditor_independent`                  | One pure function: engagement, candidate authority, prepared-by authority, conflict declarations → raise                                                 | five dedicated `test_domain.py` cases plus two in `test_application.py`                                                 | `FINANCE_AUDITOR_INDEPENDENCE_VIOLATION`                                                                                                                                                                         | PACK-08 (`OrganizationalAuthority`)                  |
| 31  | Finance auditor and finance administrator cannot be the same authority in the same relevant scope                                | `application.py` authority resolution                     | PACK-08 incompatibility set is resolved through `organization-service`, never through a local role-name string                                           | `test_an_auditor_who_administers_the_same_scope_is_refused`                                                             | `AUTHORITY_ROLE_INCOMPATIBLE`                                                                                                                                                                                    | PACK-08 section 9.3 rule 3; canon 19e.16             |
| 32  | Self-approval of personally created or personally benefiting transactions is prohibited where applicable                         | `domain.py` `assert_not_self_approval`                    | Actor authority reference of the creating/benefiting act is compared with the approving act                                                              | `test_the_claimant_cannot_approve_or_execute_their_own_reimbursement`                                                   | `CONFLICT_REVIEW_SELF_APPROVAL_PROHIBITED`                                                                                                                                                                       | —                                                    |
| 33  | Conflict-of-interest state must be declared; unknown conflict state fails closed for protected actions                           | `application.py` conflict guard                           | Conflict state enum with a blocking set; `undeclared` raises rather than defaulting to none                                                              | `test_an_undeclared_conflict_fails_closed_on_every_protected_action`                                                    | `CONFLICT_OF_INTEREST_UNDECLARED`, `CONFLICT_OF_INTEREST_BLOCKING`                                                                                                                                               | canon 19d.11 `ConflictAssessment`; PACK-09 precedent |
| 34  | Report preparation, approval, sign-off and independent audit are distinguishable actions                                         | `reporting.py` commands                                   | Four separate commands, four separately recorded authority references, four separate events                                                              | `test_the_four_report_actions_are_four_records_with_four_authorities`                                                   | `FINANCE_REPORT_APPROVAL_MISSING`, `FINANCE_REPORT_SIGN_OFF_MISSING`                                                                                                                                             | PACK-08 authority model                              |
| 35  | Public financial views are derived, versioned and non-authoritative                                                              | `projections.py`                                          | Read-only projection builders; every view carries source version and generation time; no store writes back                                               | `test_service_boundaries.py::test_projections_module_performs_no_authoritative_write`                                   | structural                                                                                                                                                                                                       | PACK-04 (`PublicLedgerEntry` precedent)              |
| 36  | Small-sample or combinatorial identity disclosure must be controlled                                                             | `projections.py` disclosure control                       | Policy-driven minimum cell size and suppression rules applied before any view is emitted                                                                 | `test_a_small_cell_view_is_suppressed_or_aggregated_before_emission`                                                    | `FINANCE_STATISTICAL_DISCLOSURE_RISK`                                                                                                                                                                            | PACK-04 (ADR-015 small-cell precedent)               |
| 37  | No vote, ballot, delegation, eligibility credential or tally linkage                                                             | import graph                                              | No import of voting, tally, delegation, credential or eligibility modules; no vote-shaped field or schema property                                       | `test_ct00_09_vote_linkability.py` PACK-10 section                                                                      | structural                                                                                                                                                                                                       | PACK-15/16 isolation                                 |
| 38  | Financial records and audit metadata must not provide a correlation bridge into voting                                           | `domain.py` handle derivation; `events.py`                | Handle is purpose-scoped and non-derivable from any participation identifier; event payloads carry no participation reference                            | `test_a_finance_handle_cannot_be_correlated_to_any_participation_reference`                                             | structural                                                                                                                                                                                                       | PACK-07 anti-correlation model (ADR-031)             |
| 39  | Cross-scope consolidation must not grant write authority into lower scopes                                                       | `reporting.py` consolidation                              | Consolidation reads lower-scope records and writes only its own `ConsolidationRecord` in the consolidating scope                                         | `test_consolidation_cannot_write_into_a_lower_scope`                                                                    | `FINANCE_CROSS_SCOPE_CONSOLIDATION_DENIED`                                                                                                                                                                       | PACK-08 (ADR-034 modes)                              |
| 40  | Imported financial data must preserve source provenance and import-batch identity                                                | `imports.py`                                              | `ImportBatch` is mandatory for every imported transaction; provenance fields are immutable after intake                                                  | `test_an_imported_transaction_without_a_batch_and_provenance_is_refused`                                                | `FINANCE_IMPORT_PROVENANCE_MISSING`                                                                                                                                                                              | PACK-13 later owns real ingestion                    |
| 41  | Duplicate imports and replay must be detectable                                                                                  | `imports.py`, `application.py`                            | Per-row import fingerprint plus caller-supplied `event_id` idempotency through Audit Core                                                                | `test_the_same_batch_imported_twice_is_detected_not_duplicated`                                                         | `FINANCE_DUPLICATE_IMPORT`, `FINANCE_DUPLICATE_TRANSACTION`                                                                                                                                                      | Audit Core (CT-00-04)                                |
| 42  | Time, timezone and accounting-period boundaries must be explicit                                                                 | `domain.py` `require_timezone`                            | Named IANA zone on every period and deadline-relevant computation; no naive datetime accepted                                                            | `test_a_naive_datetime_is_refused_everywhere_a_period_boundary_is_computed`                                             | `FINANCE_ACCOUNTING_PERIOD_UNDETERMINED`                                                                                                                                                                         | PACK-09 timezone convention                          |
| 43  | Every denial and protected transition is reason-coded                                                                            | `exceptions.py`                                           | One exception class per registered code; no free-text refusal anywhere                                                                                   | `test_reason_codes_registry.py` pack-10 row; `test_pack10_every_operation_documents_at_least_one_reason_coded_denial`   | canon section 24                                                                                                                                                                                                 | ADR-004 registry model                               |
| 44  | Unknown policy version, reporting perimeter, authority, scope, conflict state or reporting status fails closed                   | `application.py` guard order                              | Each unknown raises its own code before the operation proceeds; no default-permissive branch exists                                                      | one dedicated test per unknown (six tests)                                                                              | `FINANCE_POLICY_VERSION_UNKNOWN`, `FINANCE_REPORTING_PERIMETER_UNDETERMINED`, `FINANCE_AUTHORITY_MISSING`, `ORGANIZATION_SCOPE_UNDETERMINED`, `CONFLICT_OF_INTEREST_UNDECLARED`, `FINANCE_REPORT_STATUS_UNKNOWN` | INV-10 fail-closed                                   |
| 45  | Feature flags must not disable hard invariants                                                                                   | configuration surface                                     | Flags may gate optional read surfaces and import adapters only; no flag is read inside an invariant check                                                | `test_no_invariant_check_reads_a_feature_flag`                                                                          | structural                                                                                                                                                                                                       | —                                                    |
| 46  | No production-ready, legally compliant or authority-accepted claim without separate gates                                        | documents and data model                                  | No `is_compliant`, `is_production_ready` or equivalent field; acceptance requires an authoritative external reference                                    | `test_no_finance_entity_exposes_a_compliance_or_readiness_claim_field`                                                  | structural                                                                                                                                                                                                       | PACK-09 section 6 precedent                          |
| 47  | No direct access to another service's storage                                                                                    | import graph and store protocols                          | Finance service imports only `epd2_core` and `epd2_audit_core`; every cross-service fact arrives through a published interface call                      | `test_service_boundaries.py::test_finance_service_imports_only_shared_packages`                                         | canon INV-03                                                                                                                                                                                                     | PACK-08, PACK-09 published interfaces                |
| 48  | The purpose-scoped party handle is non-reusable and non-correlatable outside the finance purpose                                 | `domain.py` handle derivation                             | Handle derived per (reporting perimeter, declared purpose, handle-policy version); no cross-purpose lookup exists                                        | `test_the_same_legal_person_gets_unequal_handles_for_unequal_purposes`                                                  | `FINANCE_PARTY_HANDLE_PURPOSE_MISMATCH`                                                                                                                                                                          | PACK-07 domain-pseudonym model (ADR-031)             |
| 49  | No command reads system time                                                                                                     | `application.py`                                          | Injected `epd2_core.clock.Clock` on every command                                                                                                        | `test_a_fixed_clock_is_all_a_command_ever_reads`                                                                        | structural                                                                                                                                                                                                       | repository-wide convention                           |
| 50  | Command idempotency through caller-supplied `event_id`                                                                           | `application.py`                                          | Replay detected via Audit Core `get_by_event_id`; retried command returns the recorded result                                                            | `test_ct00_04_event_idempotency.py` PACK-10 section                                                                     | structural                                                                                                                                                                                                       | Audit Core                                           |
| 51  | Optimistic concurrency on every mutable aggregate                                                                                | `application.py`, `storage.py`                            | `expected_*_version` parameters refusing on mismatch                                                                                                     | `test_a_stale_expected_version_is_refused_on_every_mutable_aggregate`                                                   | `OPTIMISTIC_CONCURRENCY_CONFLICT` (reused, pack-02)                                                                                                                                                              | repository-wide convention                           |
| 52  | Every critical action appends an audit event with canonical before/after hashes                                                  | `application.py`                                          | `epd2_audit_core` append with canonical-JSON `before_hash`/`after_hash`                                                                                  | `test_ct00_07_audit_creation.py` PACK-10 section; `test_the_audit_chain_stays_verifiable_across_a_full_report_workflow` | `AUDIT_CHAIN_BROKEN` (reused)                                                                                                                                                                                    | Audit Core (INV-04, ADR-003)                         |
| 53  | A role name alone is never proof of finance authority                                                                            | `application.py` authority resolution                     | Authority resolved to a currently active, scope-matching `OrganizationalAuthority`/`RoleAssignment` record; never a `role_code` string comparison        | `test_a_matching_role_code_string_alone_never_authorizes_a_finance_action`                                              | `FINANCE_AUTHORITY_MISSING`                                                                                                                                                                                      | PACK-08 (canon 19e.12)                               |
| 54  | A later reorganization never rewrites the historical organizational perimeter of an already closed or submitted reporting period | `reporting.py` perimeter snapshot                         | Perimeter is snapshotted into the report version; current hierarchy is read only for new periods                                                         | `test_a_reorganization_leaves_a_submitted_periods_perimeter_untouched`                                                  | `FINANCE_REPORTING_PERIMETER_UNDETERMINED`                                                                                                                                                                       | PACK-08 (ADR-033 effective dating)                   |
| 55  | Rounding and valuation method are recorded with the record, never implicit                                                       | `domain.py` `Money`, `InKindValuation`                    | Explicit scale and rounding rule on every computed amount; valuation method reference on every valuation                                                 | `test_every_computed_amount_carries_its_scale_and_rounding_rule`                                                        | `FINANCE_MONETARY_AMOUNT_INVALID`                                                                                                                                                                                | —                                                    |

## 7. Domain ownership and service decomposition

Four options were analysed against aggregate consistency, ledger
balancing, organizational scope, report consolidation, audit
independence, transaction boundaries, cross-service coupling, later
production data-plane migration, repository conventions, testability, the
risk of a finance monolith and the risk of premature microservice
fragmentation. The analysis is ADR-044; the decision is summarized here
because everything else in this document depends on it.

**Decision (ADR-044): option 3 — one bounded context,
`services/finance-service`, with explicitly separated internal
modules.**

| Module                | Owns                                                                                                                             |
| --------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| `domain.py`           | Value objects (`Money`, `PostingLine`, `InKindValuation`), pure invariant functions, no I/O                                      |
| `ledger.py`           | `FinanceAccount`, `AccountingPeriod`, `JournalEntry`, `FinancialTransaction`, `ReconciliationRecord`                             |
| `imports.py`          | `ImportBatch`, provenance and duplicate detection                                                                                |
| `contributions.py`    | `Contribution`, aggregation and threshold evaluation, `SponsorshipAgreement`, `ExternalFinancialBenefit`                         |
| `expenses.py`         | `ExpenseClaim`, `PaymentAuthorization`                                                                                           |
| `positions.py`        | `FinancialAsset`, `FinancialObligation`                                                                                          |
| `budgets.py`          | `Budget`, `BudgetVersion`, `BudgetLine`                                                                                          |
| `reporting.py`        | `ReportingObligation`, `ReportingPerimeterDefinition`, `FinanceReport`, `ReportSnapshot`, consolidation, submission, publication |
| `audit_engagement.py` | `AuditEngagement`, `AuditFinding`, `AuditConclusion`                                                                             |
| `policy.py`           | `FinancePolicy` (all policy kinds), version binding, effective dating                                                            |
| `partyregistry.py`    | `FinancePartyHandle` minting and the restricted resolution surface                                                               |
| `projections.py`      | Derived read models, public views, statistical disclosure control                                                                |
| `events.py`           | Canonical event builders and full-state payload snapshots                                                                        |
| `storage.py`          | One `Protocol` per aggregate plus an in-memory reference adapter; no delete method                                               |
| `application.py`      | Commands, guards, Audit Core append, reason-coded refusals                                                                       |
| `references.py`       | The typed references PACK-10 exports to later packs                                                                              |
| `exceptions.py`       | One class per registered reason code                                                                                             |

Why not the alternatives, in one line each (full reasoning in ADR-044):
one undifferentiated `finance-service` (option 1) loses the audit and
public-projection separation that HI-30/HI-35 need at module level;
three services (option 2) puts a balanced double-entry write and its
contribution decision in different transaction boundaries with no event
bus in the baseline (PACK-13 owns that) and forces distributed
consistency PACK-10 has no mechanism for; and no fourth decomposition
scored better once ledger balancing and report consolidation were
required to be transactional within one scope.

Module separation is load-bearing, not cosmetic: `budgets.py` may not
import a ledger store (HI-12), `projections.py` may not perform an
authoritative write (HI-35), `audit_engagement.py` may not write to any
aggregate it audits (HI-30), and `partyregistry.py` is the only module
that may resolve a handle (section 9). These are the architecture tests
in `PACK-10-ACCEPTANCE-MATRIX.md` section 6.

`finance-service` imports `epd2_core` and `epd2_audit_core` only — the
same rule ADR-038 fixed for `compliance-service` (HI-47). Facts owned by
PACK-08 (organization state, authority assignments, inheritance policy)
and PACK-09 (record class, retention state, hold state, case, deadline,
notice effect) are obtained through those services' published interfaces,
never by reading their stores.

## 8. Aggregates, entities and read models

### 8.1 Classification of every candidate concept

The governing request named 39 candidate concepts and stated that they
are candidates, not mandatory final names, that redundant entities must
be avoided, and that authoritative aggregates must be distinguished from
derived read models and value objects. This is that decision, in full.

Legend: **AA** = authoritative aggregate (own root, own store, own
version); **CH** = entity inside another aggregate's consistency
boundary; **CO** = create-once record inside an aggregate; **VO** = value
object; **RM** = derived read model, non-authoritative; **MERGED** =
folded into another concept; **RENAMED** = kept with a different name.

| Candidate concept                  | Decision | Host / new name                                                              | Why                                                                                                                                                                           |
| ---------------------------------- | -------- | ---------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `FinanceAccount`                   | AA       | `FinanceAccount`                                                             | Own lifecycle, own scope, referenced by every posting                                                                                                                         |
| `AccountClassification`            | MERGED   | `FinancePolicy(chart_of_accounts)` + `FinanceAccount.classification_code`    | A classification is governed policy content plus a code on the account, not a separately versioned entity                                                                     |
| `AccountingPeriod`                 | AA       | `AccountingPeriod`                                                           | Owns the lock that every posting checks                                                                                                                                       |
| `JournalEntry`                     | AA       | `JournalEntry`                                                               | The authoritative money record; balancing is its constructor invariant                                                                                                        |
| `PostingLine`                      | VO       | inside `JournalEntry`                                                        | Has no identity or lifecycle apart from its entry                                                                                                                             |
| `FinancialTransaction`             | AA       | `FinancialTransaction`                                                       | The authoritative business fact and provenance record (ADR-045)                                                                                                               |
| `ReconciliationRecord`             | AA (CO)  | `ReconciliationRecord`                                                       | Create-once statement of a reconciliation act, with its own evidence references                                                                                               |
| `ImportBatch`                      | AA       | `ImportBatch`                                                                | Provenance and replay detection anchor (HI-40, HI-41)                                                                                                                         |
| `Contribution`                     | AA       | `Contribution`                                                               | Root of the receipt → assessment → decision → return history                                                                                                                  |
| `ContributionPartyRef`             | VO       | wraps `FinancePartyHandle`                                                   | A reference, never a person (section 9)                                                                                                                                       |
| `ContributionAggregation`          | RM       | `ContributionAggregationView` + `AggregationSnapshot` (VO)                   | Recomputable from contributions and a policy version; the _decisive_ aggregate is frozen into the assessment so a later policy change cannot silently rewrite a past decision |
| `ContributionAssessment`           | CH       | append-only history entry in `Contribution`                                  | Has no meaning outside its contribution; keeping it separate would allow an assessment without a receipt                                                                      |
| `ContributionDecision`             | CH       | append-only history entry in `Contribution`                                  | Same boundary as the assessment it follows                                                                                                                                    |
| `ContributionReturn`               | CH       | append-only history entry in `Contribution`                                  | Return must not be able to exist without the preserved receipt (HI-18)                                                                                                        |
| `InKindValuation`                  | VO       | used by four aggregates                                                      | Valuation basis, method reference, date, evidence reference — no independent lifecycle                                                                                        |
| `SponsorshipAgreement`             | AA       | `SponsorshipAgreement`                                                       | Own approval, disclosure and counter-performance lifecycle                                                                                                                    |
| `ExternalFinancialBenefit`         | AA       | `ExternalFinancialBenefit`                                                   | Financially measurable external benefit without a sponsorship agreement                                                                                                       |
| `ExpenseClaim`                     | AA       | `ExpenseClaim`                                                               | Root of submission → review → approval → settlement                                                                                                                           |
| `ExpenseReview`                    | CH       | append-only history entry in `ExpenseClaim`                                  | Reviews are the claim's history, not free-standing records                                                                                                                    |
| `PaymentAuthorization`             | AA (CO)  | `PaymentAuthorization`                                                       | Kept separate from the claim precisely because authorization and execution must be separable and reusable for non-expense payables (HI-32)                                    |
| `Budget`                           | AA       | `Budget`                                                                     | Root of the version chain                                                                                                                                                     |
| `BudgetVersion`                    | CH       | append-only child of `Budget`                                                | Amendment creates a version; versions never rewrite                                                                                                                           |
| `BudgetLine`                       | VO       | inside `BudgetVersion`                                                       | Allocation/reserved/committed amounts; `actual` is never stored here (HI-12)                                                                                                  |
| `FinancialAsset`                   | AA       | `FinancialAsset`                                                             | Own valuation and review history                                                                                                                                              |
| `Liability`                        | MERGED   | `FinancialObligation(obligation_type)`                                       | Identical lifecycle and valuation model; two aggregates would duplicate every rule                                                                                            |
| `FinancialObligation`              | AA       | `FinancialObligation`                                                        | Covers receivable, payable, loan, credit, guarantee, contingent, long-term                                                                                                    |
| `ReportingObligation`              | AA       | `ReportingObligation`                                                        | The governed statement that a report is owed for a period and perimeter                                                                                                       |
| `ReportingPerimeter`               | RENAMED  | `ReportingPerimeterDefinition` (AA) + `PerimeterSnapshot` (VO)               | The definition is effective-dated and authoritative; the snapshot is what a closed period keeps (HI-54)                                                                       |
| `FinanceReport`                    | AA       | `FinanceReport`                                                              | Root of the version chain and the lifecycle                                                                                                                                   |
| `FinanceReportVersion`             | CH       | append-only child of `FinanceReport`                                         | A version is meaningless without its report; submitted/published versions are immutable (HI-26)                                                                               |
| `ReportSnapshot`                   | AA (CO)  | `ReportSnapshot`                                                             | Deliberately its own create-once aggregate: it must survive independently of every later version (HI-25)                                                                      |
| `ConsolidationRecord`              | CO       | child of `FinanceReportVersion`                                              | Records which lower-scope perimeters were consolidated and which internal transfers were eliminated                                                                           |
| `ValidationFinding`                | CH       | append-only child of `FinanceReportVersion`                                  | Findings belong to the version they were raised against                                                                                                                       |
| `AuditEngagement`                  | AA       | `AuditEngagement`                                                            | Independent lifecycle, independent authority (HI-30)                                                                                                                          |
| `AuditFinding`                     | CH       | append-only child of `AuditEngagement`                                       | —                                                                                                                                                                             |
| `AuditOpinion` / `AuditConclusion` | CO       | `AuditConclusion`, child of `AuditEngagement`                                | One per engagement, create-once. Named "conclusion", not "opinion", so nothing in the data model can be read as a statutory audit opinion                                     |
| `SubmissionRecord`                 | CO       | child of `FinanceReportVersion`                                              | Create-once; submission is a fact, not a status flag (HI-27)                                                                                                                  |
| `ExternalAcknowledgement`          | CO       | child of `SubmissionRecord`                                                  | Records that something came back — never that it was accepted (HI-27, HI-28)                                                                                                  |
| `PublicationRecord`                | CO       | child of `FinanceReportVersion`                                              | Create-once; publication is not approval (HI-29)                                                                                                                              |
| `Restatement`                      | MERGED   | `FinanceReportVersion.restatement_of_version_reference` + restatement reason | A restatement is a version with a typed backward reference; a separate entity would create two competing chains                                                               |

Four concepts the baseline analysis added, which the candidate list did
not name:

| New concept             | Decision | Why it is required                                                                                                                                                                                                                                                                 |
| ----------------------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `FinancePolicy`         | AA       | Thresholds, categories, chart of accounts, disclosure classes and approval rules must be versioned, effective-dated, jurisdiction-scoped inputs rather than code constants (section 13, HI-44). One aggregate with a `policy_kind` enum, not eleven near-identical policy entities |
| `FinancePolicyBinding`  | VO       | Every protected decision must record the exact policy id/version it used, or a later policy change silently rewrites history                                                                                                                                                       |
| `FinancePartyHandle`    | AA       | The purpose-scoped contributor/claimant/counterparty reference model has to be an owned, audited, restricted-access object; leaving it implicit is how a global user ID appears by accident (section 9, HI-1, HI-48)                                                               |
| `PeriodReopeningRecord` | CO       | Child of `AccountingPeriod`. Reopening needs authority, reason and a preserved prior state as a record, not as a mutated field (HI-11)                                                                                                                                             |

### 8.2 Authoritative aggregates in detail

Every aggregate below is specified with the fourteen properties the
governing request requires: owner, aggregate root, organizational scope,
identifier policy, lifecycle states, allowed transitions, forbidden
transitions, authority requirements, conflict checks, append-only history
requirements, PACK-09 references, references reserved for PACK-11,
emitted domain events, and public-projection implications.

Two conventions apply to all of them and are not repeated in each entry:

- **Identifier policy.** A service-minted opaque UUID (`*_id`) plus a
  monotonically increasing `*_version` for optimistic concurrency
  (HI-51). Identifiers are never derived from any human-readable or
  personal value, never reused, and never meaningful across
  organizational scopes.
- **Scope.** Every aggregate carries exactly one `OrganizationalScope`
  (PACK-08), resolved before any other check; an undeterminable scope
  denies (HI-3, HI-4).

#### 8.2.1 `FinanceAccount`

- **Owner / root:** `finance-service`, `ledger.py`; root is the account.
- **Scope:** the owning organizational unit's scope. An account is never
  shared across scopes; a consolidating scope reads, never posts.
- **Identifier policy:** UUID plus a scope-unique `account_code` drawn
  from the active `FinancePolicy(chart_of_accounts)`.
- **Lifecycle:** `draft` → `active` → (`restricted` ↔ `active`) →
  `closed`.
- **Allowed transitions:** activation by finance administrator;
  restriction and re-activation with reason; closure only when no open
  balance and no unposted transaction references it.
- **Forbidden transitions:** `closed` → anything; deletion; changing
  `account_code` or `classification_code` after the first posting
  (reclassification is its own authorized, append-only act, HI-13).
- **Authority:** `finance_administrator` in scope for create/activate/
  restrict/close; read for `finance_auditor` and consolidating scopes.
- **Conflict checks:** none at account level beyond authority
  incompatibility (HI-31).
- **Append-only history:** classification changes and status changes are
  append-only history entries carrying the policy version used.
- **PACK-09 references:** `RecordClassRef` (retention binding).
- **PACK-11 reserved:** none.
- **Events:** `finance_account.created`,
  `finance_account.status_changed`.
- **Public projection:** account code and classification may appear in
  published structures; internal notes and authority references never do.

#### 8.2.2 `AccountingPeriod`

- **Owner / root:** `ledger.py`; root is the period.
- **Scope:** organizational scope; periods are per scope, aligned to the
  active `FinancePolicy(accounting_period)`.
- **Identifier policy:** UUID plus (scope, period label) uniqueness; a
  named IANA timezone is mandatory (HI-42).
- **Lifecycle:** `open` → `closing` → `closed` → (`reopened` → `closing`
  → `closed`)\*.
- **Allowed transitions:** open by finance administrator; `closing`
  freezes new postings while corrections in flight settle; `closed` locks;
  `reopened` only through `PeriodReopeningRecord` with authority, reason
  reference and a preserved snapshot of the closed state (HI-11).
- **Forbidden transitions:** any posting path that writes into a `closed`
  period without going through reopening (HI-10); silent reopening;
  reopening a period whose report version is `submitted` without an
  explicit correction/restatement decision.
- **Authority:** `finance_administrator` to open/close;
  `finance_administrator` **plus** a distinct approving authority to
  reopen — reopening is a dual-control action (HI-32, ADR-048).
- **Conflict checks:** the reopening approver may not be the actor who
  requested it.
- **Append-only history:** every open/close/reopen is a history entry;
  `PeriodReopeningRecord` is create-once.
- **PACK-09 references:** `LegalCaseRef`, `HoldRef` — a reopening
  triggered by a legal case or blocked by a hold cites it.
- **PACK-11 reserved:** none.
- **Events:** `accounting_period.opened`, `accounting_period.closed`,
  `accounting_period.reopening_requested`, `accounting_period.reopened`.
- **Public projection:** period boundaries and closure status may be
  public; reopening reasons are disclosed only per disclosure policy.

#### 8.2.3 `JournalEntry`

- **Owner / root:** `ledger.py`; root is the entry, containing an ordered
  tuple of `PostingLine` value objects.
- **Scope:** the posting scope; all lines share it.
- **Identifier policy:** UUID; `entry_sequence` assigned at posting per
  (scope, period) and never reused.
- **Lifecycle:** `draft` → `posted` → (`reversed`).
- **Allowed transitions:** draft edit; posting into an `open` period;
  reversal by a new entry that references the original and carries a
  reason code.
- **Forbidden transitions:** editing a `posted` entry (HI-6); posting an
  unbalanced entry (HI-7); posting into a `closed` period (HI-10);
  deleting a draft that has already been referenced by a submitted
  report snapshot.
- **Authority:** creation by an actor with finance posting authority;
  posting subject to the segregation rules of ADR-048 where the entry
  settles a payment the same actor authorized (HI-32).
- **Conflict checks:** self-approval prohibition where the entry
  implements a payment to the posting actor.
- **Append-only history:** the entry itself is the history; reversal
  chains are append-only and cycle-free.
- **PACK-09 references:** `HoldRef` (a held record's disposal is blocked,
  not its posting), `LegalCaseRef` on correction entries arising from a
  case.
- **PACK-11 reserved:** `FinanceEvidenceReference` for the supporting
  document.
- **Events:** `journal_entry.drafted`, `journal_entry.posted`,
  `journal_entry.reversed`.
- **Public projection:** aggregated only. A published financial statement
  is derived from posted entries; individual entries with counterparty
  references are not published (HI-2, HI-36).

#### 8.2.4 `FinancialTransaction`

- **Owner / root:** `ledger.py`; root is the transaction.
- **Scope:** organizational scope of the transacting unit.
- **Identifier policy:** UUID; optional `import_fingerprint` for
  duplicate detection (HI-41); `internal_transfer_reference` binding the
  two sides of an inter-unit transfer (section 4.3).
- **Lifecycle:** `recorded` → `classified` → `posted` →
  (`corrected`) → (`reversed`).
- **Allowed transitions:** classification against a bound policy
  version; posting, which creates the balanced `JournalEntry`;
  correction, which creates a correcting transaction and entry.
- **Forbidden transitions:** reaching `posted` without a balanced entry;
  changing `transaction_date`, provenance or `import_batch_reference`
  after `recorded` (HI-40); reclassification that drops an obligation
  (HI-13).
- **Authority:** finance posting authority; imports additionally require
  the import authority of `imports.py`.
- **Conflict checks:** self-approval prohibition on the
  authorize/execute pair when the transaction is a payment.
- **Append-only history:** classification and correction history is
  append-only, each entry carrying its `FinancePolicyBinding`.
- **PACK-09 references:** `RecordClassRef`, `HoldRef`, `LegalCaseRef`,
  `DeadlineRef` (a correction owed by a procedural deadline).
- **PACK-11 reserved:** `FinanceEvidenceReference` (invoice, receipt,
  bank statement, contract).
- **Events:** `financial_transaction.recorded`,
  `financial_transaction.classification_changed`.
- **Public projection:** category-level aggregates only; counterparty
  handles never appear in a public view.

#### 8.2.5 `ImportBatch`

- **Owner / root:** `imports.py`; root is the batch.
- **Scope:** the importing organizational scope.
- **Identifier policy:** UUID plus `source_system_reference` and a
  content fingerprint over the batch payload.
- **Lifecycle:** `registered` → `validated` → `applied` |
  `rejected`.
- **Allowed transitions:** validation; application, producing
  transactions that each carry the batch reference; rejection with reason
  codes and per-row findings.
- **Forbidden transitions:** re-applying an `applied` batch (HI-41);
  mutating a row result; applying a batch whose fingerprint matches an
  already-applied batch without an explicit, reason-coded override
  decision.
- **Authority:** a distinct import authority; import is not implied by
  posting authority.
- **Conflict checks:** none beyond authority.
- **Append-only history:** per-row results are append-only and preserved
  after application.
- **PACK-09 references:** `RecordClassRef` (the batch is itself a
  governed record).
- **PACK-11 reserved:** `FinanceEvidenceReference` for the source file or
  statement.
- **Events:** `import_batch.registered`, `import_batch.completed`,
  `import_batch.rejected`.
- **Public projection:** none. Import provenance is internal and audit
  visible only.

#### 8.2.6 `ReconciliationRecord`

- **Owner / root:** `ledger.py`; create-once record.
- **Scope:** organizational scope of the reconciled account and period.
- **Identifier policy:** UUID; (account, period, sequence) uniqueness.
- **Lifecycle:** `recorded` (terminal). A later reconciliation is a new
  record.
- **Allowed transitions:** none — create-once by design.
- **Forbidden transitions:** editing an existing reconciliation;
  deleting a reconciliation that a report snapshot references.
- **Authority:** finance administrator; reconciliation performed by the
  auditor is recorded as an audit finding instead, never as an
  authoritative reconciliation (HI-30).
- **Conflict checks:** the reconciling actor may not be the sole
  authorizer of the transactions being reconciled where policy requires
  dual control.
- **Append-only history:** the record set is the history.
- **PACK-09 references:** `HoldRef`.
- **PACK-11 reserved:** `FinanceEvidenceReference` (bank statement).
- **Events:** `reconciliation.recorded`.
- **Public projection:** reconciliation status may be published as a
  boolean/date; discrepancy detail is not public by default.

#### 8.2.7 `Contribution`

- **Owner / root:** `contributions.py`; root is the contribution, holding
  a create-once receipt and an append-only decision history
  (`assessment`, `decision`, `return`).
- **Scope:** the receiving organizational unit's scope; aggregation
  additionally uses the legally relevant perimeter (section 10, OD-3).
- **Identifier policy:** UUID; `ContributionPartyRef` wrapping a
  `FinancePartyHandle`; never a person identifier (HI-1).
- **Lifecycle:** `received` → `quarantined` → `assessed` → (`accepted` |
  `rejected` | `return_required` → `returned` | `escalated`).
- **Allowed transitions:** assessment against a bound policy version;
  acceptance only from a resolved assessment; rejection, return and
  escalation with reason codes; escalation opens or references a PACK-09
  legal case.
- **Forbidden transitions:** `received` → `accepted` directly (HI-16,
  HI-17); editing the receipt (HI-18); recomputing a past assessment
  against a newer policy version; treating a returned contribution as
  never received.
- **Authority:** finance administrator to assess and decide; return
  requires the payment authorization/execution split (HI-32); escalation
  requires the authority that may open a case in scope.
- **Conflict checks:** mandatory conflict declaration on the deciding
  authority; `undeclared` fails closed (HI-33); related-party and
  intermediary declarations feed both the conflict check and the
  aggregation key (HI-15).
- **Append-only history:** every assessment, decision, return and
  reclassification is an appended entry with actor authority reference,
  reason code, policy binding and frozen `AggregationSnapshot`.
- **PACK-09 references:** `LegalCaseRef`, `DeadlineRef` (statutory return
  or notification period), `NoticeEffectRef` (a notice whose legal effect
  started that period), `HoldRef`, `RecordClassRef`.
- **PACK-11 reserved:** `FinanceEvidenceReference` (donation declaration,
  bank record, beneficial-origin declaration).
- **Events:** `finance_contribution.received`,
  `finance_contribution.quarantined`, `finance_contribution.assessed`,
  `finance_contribution.accepted`, `finance_contribution.rejected`,
  `finance_contribution.return_required`,
  `finance_contribution.returned`, `finance_contribution.escalated`,
  `finance_in_kind_valuation.recorded`.
- **Public projection:** only what the disclosure policy classifies as
  publishable, only at the legally required aggregation level, and only
  through statistical disclosure control (HI-36). A contributor handle is
  never published.

#### 8.2.8 `SponsorshipAgreement`

- **Owner / root:** `contributions.py`; root is the agreement.
- **Scope:** the recipient organization's scope.
- **Identifier policy:** UUID; sponsoring party as a
  `FinancePartyHandle`-based reference; campaign/event/publication/
  initiative association by typed reference only.
- **Lifecycle:** `registered` → `under_review` → (`approved` |
  `rejected`) → (`disclosure_classified`) → (`terminated`).
- **Allowed transitions:** review; approval or rejection with reason;
  disclosure classification against the disclosure policy version;
  termination with reason.
- **Forbidden transitions:** approving without a recorded
  counter-performance or an explicit policy classification stating none
  exists (HI-20); reclassifying disclosure downward to escape publication
  (HI-13); recording a meeting, contact or access event (HI-21).
- **Authority:** finance administrator plus, where the policy requires
  it, a second approving authority; disclosure classification requires
  the disclosure authority.
- **Conflict checks:** mandatory conflict declaration; a blocking
  conflict refuses approval.
- **Append-only history:** review, approval, classification and
  termination history is append-only.
- **PACK-09 references:** `LegalCaseRef`, `HoldRef`, `RecordClassRef`.
- **PACK-11 reserved:** `FinanceEvidenceReference` (the agreement
  document, valuation report).
- **Events:** `sponsorship.registered`, `sponsorship.approved`,
  `sponsorship.rejected`, `sponsorship.disclosure_classified`.
- **Public projection:** publishable per policy, typically at agreement
  level with sponsor category and value band rather than a resolvable
  identity, subject to disclosure control.

#### 8.2.9 `ExternalFinancialBenefit`

- **Owner / root:** `contributions.py`; root is the benefit record.
- **Scope:** the benefiting organization's scope.
- **Identifier policy:** UUID; `benefit_type` from policy (paid
  third-party support, in-kind campaign support, subsidized service,
  guarantee, forgiven debt, other financially measurable benefit).
- **Lifecycle:** `recorded` → `valued` → `assessed` → (`disclosed` |
  `not_publishable`).
- **Allowed transitions:** valuation with method and evidence;
  assessment against contribution/sponsorship policy to determine whether
  the benefit is legally a contribution; disclosure classification.
- **Forbidden transitions:** recording a benefit without a valuation
  basis where one is required (HI-19); using this entity to model a
  meeting or a lobbying contact (HI-21).
- **Authority:** finance administrator; disclosure authority for
  classification.
- **Conflict checks:** conflict declaration required for approval-like
  assessments.
- **Append-only history:** valuation and assessment history append-only.
- **PACK-09 references:** `LegalCaseRef`, `HoldRef`, `RecordClassRef`.
- **PACK-11 reserved:** `FinanceEvidenceReference`.
- **Events:** `external_financial_benefit.recorded`.
- **Public projection:** same rule as sponsorship.

#### 8.2.10 `ExpenseClaim`

- **Owner / root:** `expenses.py`; root is the claim with an append-only
  review history.
- **Scope:** the claiming organizational unit's scope.
- **Identifier policy:** UUID; claimant as a purpose-scoped
  `FinancePartyHandle` reference (HI-1).
- **Lifecycle:** `submitted` → `under_review` → (`approved` |
  `rejected`) → `payment_authorized` → `settled` → (`corrected`).
- **Allowed transitions:** review; approval or rejection with reason;
  payment authorization by a distinct authority; settlement by a distinct
  executor; correction creating a new correcting record.
- **Forbidden transitions:** the claimant reviewing, approving,
  authorizing or executing their own claim (HI-32); settlement without an
  authorization; editing a settled claim.
- **Authority:** reviewer (action-level), `finance_administrator` for
  approval, `payment_authorizer` for authorization, `payment_executor`
  for settlement — four distinct authority references (ADR-048).
- **Conflict checks:** mandatory declaration for reviewer, approver and
  authorizer; unknown fails closed (HI-33).
- **Append-only history:** every review, decision and correction is
  appended; evidence references are preserved.
- **PACK-09 references:** `HoldRef`, `RecordClassRef`, `LegalCaseRef`
  (disputed reimbursement), `DeadlineRef`.
- **PACK-11 reserved:** `FinanceEvidenceReference` (receipts, travel
  documents).
- **Events:** `expense_claim.submitted`, `expense_claim.reviewed`,
  `expense_claim.approved`, `expense_claim.rejected`,
  `expense_claim.corrected`.
- **Public projection:** aggregate expenditure categories only. Claimant
  handles, purposes with personal detail, and individual claim amounts
  are not public by default.

#### 8.2.11 `PaymentAuthorization`

- **Owner / root:** `expenses.py`; create-once record referencing exactly
  one payable object (claim, obligation, contribution return, or other
  governed payable).
- **Scope:** the paying organizational unit's scope.
- **Identifier policy:** UUID; `payable_reference` is typed, never a free
  string.
- **Lifecycle:** `authorized` → (`executed` | `revoked_before_execution`).
- **Allowed transitions:** execution recorded by a distinct executor
  authority, producing the settling transaction; revocation before
  execution with reason.
- **Forbidden transitions:** authorizer and executor being the same
  authority (HI-32, HI-48 of ADR-048's role matrix); executing a revoked
  authorization; editing an executed authorization.
- **Authority:** `payment_authorizer` to authorize, `payment_executor` to
  execute — both resolved as active PACK-08 authorities in scope (HI-53).
- **Conflict checks:** self-benefit check against the payee handle;
  blocking conflict refuses.
- **Append-only history:** create-once plus one execution record.
- **PACK-09 references:** `HoldRef`, `LegalCaseRef`.
- **PACK-11 reserved:** `FinanceEvidenceReference` (payment instruction,
  bank confirmation — the real bank integration is out of scope,
  section 5).
- **Events:** `payment.authorized`, `payment.settled`.
- **Public projection:** none at record level.

#### 8.2.12 `Budget`

- **Owner / root:** `budgets.py`; root is the budget, containing an
  append-only chain of `BudgetVersion` children, each holding
  `BudgetLine` value objects.
- **Scope:** the budgeting organizational unit's scope; consolidation of
  lower-level budgets is a read, never a write (HI-39).
- **Identifier policy:** UUID; (scope, budget period) uniqueness;
  versions numbered monotonically.
- **Lifecycle (per version):** `draft` → `submitted_for_approval` →
  (`approved` | `rejected`) → (`superseded_by_amendment`).
- **Allowed transitions:** amendment creating a new version; approval by
  the authority the policy names; supersession by a later approved
  version.
- **Forbidden transitions:** editing an approved version; writing an
  actual amount onto a budget line (HI-12); a higher scope amending a
  lower scope's budget without an explicit consolidation authority and
  the lower scope's own approval.
- **Authority:** `finance_administrator` to draft, the policy-named
  approving body to approve; consolidation authority to build a
  consolidated view.
- **Conflict checks:** approver may not be the sole drafter where policy
  requires dual control.
- **Append-only history:** versions and approval decisions are
  append-only.
- **PACK-09 references:** `RecordClassRef`.
- **PACK-11 reserved:** `FinanceEvidenceReference` (board resolution).
- **Events:** `budget.approved`, `budget.amended`.
- **Public projection:** approved budget totals may be publishable per
  policy; reserved and committed amounts are labelled as budget-domain
  values, never as accounting balances (section 4.8).

#### 8.2.13 `FinancialAsset`

- **Owner / root:** `positions.py`; root is the asset record.
- **Scope:** the holding organizational unit's scope.
- **Identifier policy:** UUID; optional typed
  `tangible_or_intangible_asset_reference` where financially relevant —
  a reference, not an inventory record (section 4.7).
- **Lifecycle:** `recorded` → `valued` → (`revalued`)\* →
  (`disposed` | `written_off`).
- **Allowed transitions:** valuation and revaluation with method,
  valuation date and evidence; disposal or write-off with authority and
  reason.
- **Forbidden transitions:** revaluation without a method reference
  (HI-55); write-off without the authority the policy names; disposal of
  an asset under a PACK-09 legal hold (HI-23).
- **Authority:** `finance_administrator`; write-off requires dual control
  where the policy sets a threshold.
- **Conflict checks:** self-benefit check on disposal to a related party.
- **Append-only history:** valuation and review history append-only.
- **PACK-09 references:** `HoldRef`, `LegalCaseRef`, `RecordClassRef`.
- **PACK-11 reserved:** `FinanceEvidenceReference` (valuation report,
  contract).
- **Events:** `financial_asset.recorded`, `financial_asset.revalued`,
  `financial_asset.written_off`.
- **Public projection:** aggregate asset classes only.

#### 8.2.14 `FinancialObligation`

- **Owner / root:** `positions.py`; root is the obligation.
- **Scope:** the obligated organizational unit's scope.
- **Identifier policy:** UUID; `obligation_type` ∈ {receivable, payable,
  loan, credit, guarantee, contingent_liability, long_term_obligation,
  other} from policy. This is the merge of the candidate `Liability`
  concept (section 8.1).
- **Lifecycle:** `recorded` → `valued` → (`revalued`)\* → (`settled` |
  `written_off` | `expired`).
- **Allowed transitions:** valuation, revaluation, settlement through a
  `PaymentAuthorization`, write-off with authority, expiry.
- **Forbidden transitions:** settling without an authorization; writing
  off a contingent liability that a PACK-09 case still concerns without
  citing the case; editing a settled obligation.
- **Authority:** `finance_administrator`; write-off dual control per
  policy.
- **Conflict checks:** self-benefit check where the counterparty handle
  resolves to a related party of the deciding authority.
- **Append-only history:** valuation and decision history append-only.
- **PACK-09 references:** `LegalCaseRef` (disputed or litigated
  obligation), `DeadlineRef`, `HoldRef`, `RecordClassRef`.
- **PACK-11 reserved:** `FinanceEvidenceReference` (loan agreement,
  guarantee letter).
- **Events:** `financial_obligation.recorded`,
  `financial_obligation.revalued`, `financial_obligation.settled`,
  `financial_obligation.written_off`.
- **Public projection:** aggregate obligation classes only; guarantees
  and contingent liabilities are disclosed per policy.

#### 8.2.15 `ReportingObligation`

- **Owner / root:** `reporting.py`; root is the obligation.
- **Scope:** the organizational scope legally required to report, which
  may be higher than the scopes whose data it consolidates.
- **Identifier policy:** UUID; (scope, reporting period, obligation kind)
  uniqueness.
- **Lifecycle:** `created` → `active` → (`fulfilled` | `waived` |
  `superseded`).
- **Allowed transitions:** activation; fulfilment by a submitted report
  version; waiver only with an authority reference and reason;
  supersession when the legal basis or perimeter changes.
- **Forbidden transitions:** fulfilment without a `SubmissionRecord`;
  silent waiver; deriving fulfilment from publication (HI-29).
- **Authority:** `finance_administrator` to create; waiver requires the
  authority the policy names.
- **Conflict checks:** none beyond authority.
- **Append-only history:** status history append-only, each entry citing
  the policy version and, where applicable, the PACK-09 deadline.
- **PACK-09 references:** `DeadlineRef` (the statutory submission
  deadline), `NoticeEffectRef` (a notice that started or changed it),
  `LegalCaseRef`.
- **PACK-11 reserved:** none.
- **Events:** `reporting_obligation.created`.
- **Public projection:** the existence of an obligation and its period
  may be public; waiver reasons follow disclosure policy.

#### 8.2.16 `ReportingPerimeterDefinition`

- **Owner / root:** `reporting.py`; root is the definition.
- **Scope:** the reporting scope.
- **Identifier policy:** UUID plus `definition_version`; effective-dated
  (`effective_from`, `effective_until`).
- **Lifecycle:** `draft` → `active` → `superseded`.
- **Allowed transitions:** activation; supersession by a new version.
- **Forbidden transitions:** editing an active definition; retroactively
  changing a definition a `ReportSnapshot` already used (HI-54); deriving
  the perimeter implicitly from the current organizational hierarchy at
  report time.
- **Authority:** `finance_administrator` plus the approving authority the
  policy names.
- **Conflict checks:** none beyond authority.
- **Append-only history:** version chain append-only.
- **PACK-09 references:** none.
- **PACK-11 reserved:** none.
- **Events:** `reporting_perimeter.defined`.
- **Public projection:** the perimeter of a published report is itself
  publishable and is part of what makes the report interpretable.

#### 8.2.17 `FinanceReport`

- **Owner / root:** `reporting.py`; root is the report, containing an
  append-only chain of `FinanceReportVersion` children. Each version
  holds create-once `ConsolidationRecord`, `SubmissionRecord` (with its
  own create-once `ExternalAcknowledgement`) and `PublicationRecord`
  children, plus append-only `ValidationFinding`s.
- **Scope:** the reporting scope.
- **Identifier policy:** UUID; (scope, reporting obligation) uniqueness;
  versions numbered monotonically; a restatement is a version carrying
  `restatement_of_version_reference`.
- **Lifecycle (per version):** `draft` → `internally_reviewed` →
  `auditor_reviewed` → `approved` → `signed` → `submitted` →
  (`externally_acknowledged`) → (`accepted_by_authority`) →
  (`published`) → (`amended_or_restated`).
- **Allowed transitions:** preparation from a frozen `ReportSnapshot`;
  internal review; auditor review, which requires a concluded
  `AuditEngagement` in the same scope and period; approval by the
  management/board authority; sign-off by the legally responsible
  signatory; submission producing a `SubmissionRecord`; acknowledgement
  recording; acceptance **only** with an authoritative reference;
  publication with a separate publication authorization; amendment or
  restatement creating a new version.
- **Forbidden transitions:** preparation without a snapshot (HI-25);
  `submitted` → `accepted_by_authority` on telemetry, acknowledgement or
  read status alone (HI-27, HI-28); publication implying approval, or
  approval implying publication (HI-29); editing a submitted or published
  version (HI-26); consolidating a lower scope by writing into it
  (HI-39); recomputing a submitted version's perimeter after a
  reorganization (HI-54).
- **Authority:** four distinct authorities for prepare / approve /
  sign-off / audit-review (HI-34), plus a publication authority. The
  signatory is the legally responsible role; the preparer is not
  automatically the signatory (OD-9).
- **Conflict checks:** the auditor-review step re-verifies auditor
  independence at the moment of review, not only at engagement opening
  (HI-30, HI-31).
- **Append-only history:** every version, finding, submission,
  acknowledgement, publication and restatement is append-only; nothing
  in the chain is ever rewritten.
- **PACK-09 references:** `DeadlineRef` (submission and correction
  deadlines), `NoticeEffectRef` (the governed decision that makes an
  authority response legally effective — the only path to
  `accepted_by_authority`), `LegalCaseRef` (proceedings about the
  report), `HoldRef`, `RecordClassRef`.
- **PACK-11 reserved:** `FinanceEvidenceReference` for the signed report
  rendition, submission receipt, publication rendition and audit working
  papers — none of which PACK-10 stores (HI-22).
- **Events:** `finance_report.snapshot_frozen`,
  `finance_report.prepared`,
  `finance_report.validation_finding_recorded`,
  `finance_report.consolidated`, `finance_report.internally_reviewed`,
  `finance_report.auditor_reviewed`,
  `finance_report.correction_requested`, `finance_report.approved`,
  `finance_report.signed`, `finance_report.submitted`,
  `finance_report.external_acknowledgement_recorded`,
  `finance_report.acceptance_recorded`, `finance_report.published`,
  `finance_report.restated`.
- **Public projection:** the published version is the _only_ publishable
  one, always labelled with its version, its snapshot reference, its
  perimeter and its status; a draft is never publishable (HI-35).

#### 8.2.18 `ReportSnapshot`

- **Owner / root:** `reporting.py`; create-once aggregate.
- **Scope:** the reporting scope.
- **Identifier policy:** UUID plus a content digest over the frozen
  source set.
- **Lifecycle:** `frozen` (terminal).
- **Allowed transitions:** none.
- **Forbidden transitions:** any write; replacement of a snapshot a
  version references (HI-25); recomputation that would change the digest.
- **Authority:** `finance_administrator` to freeze.
- **Conflict checks:** none.
- **Append-only history:** the snapshot set is the history; each report
  version names exactly one snapshot.
- **PACK-09 references:** `HoldRef` (a snapshot under hold cannot be
  disposed of).
- **PACK-11 reserved:** none — a snapshot holds scoped references and
  computed figures, never document bytes.
- **Events:** `finance_report.snapshot_frozen`.
- **Public projection:** the snapshot reference and digest are
  publishable as provenance; the snapshot contents are published only
  through the report's own disclosure policy.

#### 8.2.19 `AuditEngagement`

- **Owner / root:** `audit_engagement.py`; root is the engagement, with
  append-only `AuditFinding` children and one create-once
  `AuditConclusion`.
- **Scope:** the audited organizational scope and period.
- **Identifier policy:** UUID; (scope, period, engagement sequence)
  uniqueness.
- **Lifecycle:** `opened` → `in_progress` → `concluded` →
  (`superseded_by_new_engagement`).
- **Allowed transitions:** finding recording; conclusion, create-once;
  supersession by a later engagement for the same period.
- **Forbidden transitions:** conclusion by an authority that fails the
  independence check (HI-30, HI-31); editing a recorded finding or a
  conclusion; the engagement writing into any aggregate it audits;
  concluding without at least the findings required by policy.
- **Authority:** `finance_auditor`, resolved as an active PACK-08
  `OrganizationalAuthority` in the audited scope, and incompatible with
  `finance_administrator` there (canon 19e.16 rule 3).
- **Conflict checks:** independence re-checked at opening, at each
  finding and at conclusion; conflicts declared and blocking states
  refuse.
- **Append-only history:** findings and conclusion are append-only and
  survive every later engagement.
- **PACK-09 references:** `LegalCaseRef`, `HoldRef`, `RecordClassRef`.
- **PACK-11 reserved:** `FinanceEvidenceReference` (audit working
  papers).
- **Events:** `finance_audit.opened`, `finance_audit.finding_recorded`,
  `finance_audit.concluded`.
- **Public projection:** whether an audit occurred and concluded may be
  public per policy; findings are disclosed only per disclosure policy,
  and never in a form that identifies individuals (HI-2, HI-36).

#### 8.2.20 `FinancePolicy`

- **Owner / root:** `policy.py`; root is the policy, versioned.
- **Scope:** an `OrganizationalScope` plus an explicit `jurisdiction`
  reference; a policy is never implicitly global.
- **Identifier policy:** UUID plus `policy_version`; `policy_kind` ∈
  {chart_of_accounts, income_classification,
  expenditure_classification, contribution_classification,
  contribution_restriction, aggregation, disclosure_threshold,
  sponsorship_classification, approval_threshold, expense_approval,
  accounting_period, retention_binding, report_perimeter,
  report_structure, public_disclosure, statistical_disclosure,
  party_handle}.
- **Lifecycle:** `draft` → `active` → `superseded`; effective-dated with
  `effective_from` and optional `effective_until`.
- **Allowed transitions:** activation, requiring the approving authority
  the policy kind demands; supersession by a new version with a version
  increment.
- **Forbidden transitions:** editing an `active` version; retroactive
  effective dating over a period that is already closed or submitted;
  supersession that skips a version increment; a policy version being
  used by a decision without being recorded on it (HI-44).
- **Authority:** `finance_administrator` to draft; the policy kind's
  named approving authority to activate; critical kinds (contribution
  restriction, disclosure, statistical disclosure, party handle) require
  dual approval, following canon 19d.7's critical-policy pattern.
- **Conflict checks:** approver distinct from drafter for critical kinds.
- **Append-only history:** version chain append-only; every superseded
  version remains readable so historical decisions stay interpretable.
- **PACK-09 references:** `RecordClassRef` for the retention_binding
  kind.
- **PACK-11 reserved:** `FinanceEvidenceReference` (the board resolution
  adopting the policy).
- **Events:** `finance_policy.version_published`,
  `finance_policy.superseded`.
- **Public projection:** policy versions that govern published figures
  are themselves publishable, and should be, because a published number
  is uninterpretable without the classification rules behind it.

#### 8.2.21 `FinancePartyHandle`

- **Owner / root:** `partyregistry.py`; root is the handle. This is the
  most privacy-sensitive aggregate in PACK-10 and the only one with a
  restricted resolution surface.
- **Scope:** the reporting perimeter the handle is valid in, plus the
  declared purpose.
- **Identifier policy:** an opaque UUID minted by the service. It is
  derived from nothing: not from a name, not from an account, not from a
  membership, not from any participation identifier, and not from another
  handle (HI-1, HI-38, HI-48). Sameness across contributions of one legal
  person within a perimeter and purpose is established by the registry's
  own governed matching act, recorded and audited — never by a
  platform-wide identifier.
- **Lifecycle:** `minted` → `active` → (`merged_into` | `retired`).
- **Allowed transitions:** a governed, authorized, reason-coded merge
  when two handles are determined to be the same legal person within the
  same perimeter and purpose; retirement when the perimeter or purpose
  ends.
- **Forbidden transitions:** reuse across purposes or perimeters (HI-48);
  resolution by any module other than `partyregistry.py`; export of the
  resolution mapping into an event, a public view, a report snapshot or
  an audit payload (HI-2); merging handles across purposes; deriving a
  handle from a membership, account, credential or vote-related value
  (HI-37, HI-38).
- **Authority:** minting is available to the finance intake commands;
  **resolution** requires a separate, explicitly granted resolution
  authority and every resolution is audited as its own event (section 9).
- **Conflict checks:** none — but every merge records the deciding
  authority and reason.
- **Append-only history:** minting, merges, retirements and every
  resolution access are append-only.
- **PACK-09 references:** `RecordClassRef` (the handle registry is a
  governed record with its own retention), `HoldRef`, `LegalCaseRef`.
- **PACK-11 reserved:** `FinanceEvidenceReference` for the legal-identity
  evidence PACK-11 will hold — PACK-10 stores the *reference and the
  verification status*, never identity documents (section 9).
- **Events:** `finance_party_handle.minted`,
  `finance_party_handle.resolved` (access audit),
  `finance_party_handle.merged`.
- **Public projection:** **none, ever.** No handle, no handle count per
  person, no derived value from which handle sameness could be inferred
  appears in any public view.

### 8.3 Merged and rejected concepts

Four candidate concepts were deliberately not made separate entities.
Recording why is part of the specification, because a later round that
adds them back would be reintroducing a redundancy this one removed:

- **`Liability`** → `FinancialObligation` with an `obligation_type`.
  Identical lifecycle, identical valuation model, identical authority
  rules; two aggregates would mean two places to keep the same invariants
  correct.
- **`AccountClassification`** → `FinancePolicy(chart_of_accounts)` plus
  `FinanceAccount.classification_code`. A classification scheme is
  governed, versioned policy content; making it an entity would create a
  second, competing versioning mechanism next to `FinancePolicy`.
- **`Restatement`** → a `FinanceReportVersion` with
  `restatement_of_version_reference`. A separate entity would produce two
  chains (versions and restatements) that could disagree about which
  document is current.
- **`AuditOpinion`** → `AuditConclusion`. The rename is deliberate:
  "opinion" is a term of art in statutory audit, and PACK-10 must not
  imply that a recorded internal conclusion is a statutory audit opinion
  (section 22).

`ContributionAssessment`, `ContributionDecision`, `ContributionReturn`
and `ExpenseReview` are kept as concepts but not as aggregates: they are
append-only history entries inside `Contribution` and `ExpenseClaim`.
Making them free-standing would allow a decision without a receipt, or a
review without a claim — exactly the states HI-18 exists to prevent.

### 8.4 Derived read models — non-authoritative

Each of these is recomputable, carries the source version and generation
timestamp, and is never written back into an authoritative aggregate
(HI-35). None is a cache of truth: canon 2.2's rule that a read model is
not a source of truth applies unchanged.

| Read model                    | Derived from                                         | Notes                                                                                 |
| ----------------------------- | ---------------------------------------------------- | ------------------------------------------------------------------------------------- |
| `TrialBalanceView`            | posted `JournalEntry`s in a period                   | The balancing check is on the entries, not on this view                               |
| `ContributionAggregationView` | `Contribution`s + aggregation policy version         | The decisive aggregate is frozen into the assessment as `AggregationSnapshot` (HI-14) |
| `BudgetVersusActualView`      | approved `BudgetVersion` + posted entries            | The only place an "actual" number meets a budget line (HI-12)                         |
| `PositionSummaryView`         | `FinancialAsset` + `FinancialObligation`             | Aggregate classes only                                                                |
| `ReportPreparationView`       | `ReportSnapshot`                                     | Never recomputed from live data once a snapshot exists (HI-25)                        |
| `PublicFinanceView`           | published `FinanceReportVersion` + disclosure policy | Statistical disclosure control applied before emission (HI-36)                        |
| `PublicContributionView`      | accepted `Contribution`s + disclosure policy         | Legally required aggregation only; no handle, ever                                    |
| `AuditTrailView`              | Audit Core events                                    | Read-only; no identity payload (HI-2)                                                 |

### 8.5 Value objects

`Money` (integer minor units, currency code, scale, rounding rule),
`PostingLine` (account reference, debit/credit side, `Money`, optional
dimension references), `InKindValuation` (basis, method reference,
valuation date, evidence reference), `AggregationSnapshot` (frozen
aggregate, period, perimeter, policy binding), `PerimeterSnapshot`
(frozen organizational perimeter of a period), `FinancePolicyBinding`
(policy id, version, effective date used), `ContributionPartyRef` (wraps
a `FinancePartyHandle` id plus purpose), `RetentionBinding` (PACK-09
`RecordClassRef` plus binding date), and `FinanceEvidenceReference` (the
PACK-11 placeholder shape: owner, kind, opaque external reference,
scope).

None of them has an independent lifecycle, and none of them may carry a
personal name, address, bank detail, identity document reference or
credential value (HI-2).

## 9. Identity-minimization model

PACK-10 introduces none of the following, anywhere, in any form: `UserId`,
`GlobalUserId`, a generic `PersonId`, a reusable member identifier across
unrelated contexts, a voter identifier, a credential identifier, or a
ballot identifier (HI-1, HI-37).

Party finance nevertheless has a legally unavoidable identification
requirement: a contributor above a threshold, a claimant being
reimbursed, a counterparty to an obligation and the signatory of a report
all have to be identifiable to the party's finance function and to an
auditor. The model below satisfies that without creating a
platform-wide identifier.

### 9.1 Which service owns the authoritative identity

There are three different answers, and conflating them is the mistake
this section exists to prevent:

1. **Platform participants.** `identity-service` owns `IdentityRecord`
   (canon 7.3); `membership-service` owns `Membership` (canon 8.3, canon
   19d). PACK-10 owns neither and reads neither into its own records.
2. **External contributors, sponsors and counterparties.** Very often
   nobody on the platform owns their identity: a donor may have no
   account, no membership and no credential. For these, the
   authoritative identity evidence is a **document** — a donation
   declaration, a beneficial-origin declaration, a contract, a
   commercial-register extract — which **PACK-11** will own. PACK-10
   holds a reference to it and a verification _status_, never its
   content.
3. **Actors performing finance actions.** Their authority is a PACK-08
   `OrganizationalAuthority`/`RoleAssignment` reference. PACK-10 records
   the authority reference, not the person behind it.

### 9.2 What PACK-10 stores

- A `FinancePartyHandle`: an opaque, service-minted UUID, scoped to a
  declared **purpose** (contribution, sponsorship, expense claimant,
  obligation counterparty, signatory) and a **reporting perimeter**.
- The legally required **category** of the party (natural person, legal
  person, other governed category) as a policy-governed value — a
  category, not a name.
- An `identity_verification_status` (verified / unverified /
  unverifiable / not_required) plus the _authority_ that recorded it.
- A `FinanceEvidenceReference` to the PACK-11 material that evidences the
  identity, valuation or declaration.
- Where an intermediary or related-party group is declared, a
  `related_party_group_reference` — itself a purpose-scoped handle, not a
  person.

### 9.3 What PACK-10 must never store

Names, addresses, dates of birth, national identifiers, tax identifiers,
bank-account details (IBAN, account number, card data), identity-document
numbers or images, email addresses, telephone numbers, credential values,
membership identifiers, participation identifiers, vote-related values,
or any free-text field into which the above could be written and then
published. Bank details in particular are named explicitly because a
finance service is the one place where storing them feels natural: the
payment rail is out of scope (section 5), so nothing in PACK-10 needs
them, and the threat model treats bank-detail leakage as its own threat
(`PACK-10-THREAT-MODEL.md` T-26).

### 9.4 How repeated contributions aggregate lawfully

Legally required aggregation needs one thing: knowing that two
contributions came from the same contributor within the relevant period
and perimeter. It does **not** need a platform-wide identifier, and the
difference is the whole design:

1. A handle is minted per (perimeter, purpose, handle-policy version).
2. Sameness is established by a **governed matching act** inside
   `partyregistry.py`: an authorized actor, with the declaration and
   evidence references in front of them, records that this contribution
   belongs to an existing handle, or mints a new one. The act is
   reason-coded and audited.
3. Aggregation then runs on the handle (HI-14), and known related or
   intermediary relationships extend the aggregation key (HI-15).
4. The handle is meaningless outside its perimeter and purpose (HI-48). A
   handle from the contribution purpose cannot be used to look anything
   up in the sponsorship purpose, in membership, in voting, or in another
   perimeter — there is no cross-purpose lookup in the design, and
   `test_the_same_legal_person_gets_unequal_handles_for_unequal_purposes`
   is the test that keeps it that way.

For **membership contributions** the same mechanism is used with one
deliberate additional constraint: PACK-10 does not accept a
`membership_id`. It accepts a purpose-scoped dues reference issued by
`membership-service` — the domain-pseudonym pattern PACK-07's ADR-031
already anticipated — and only `membership-service` can resolve it. This
keeps dues accounting possible without giving the finance domain a
membership register. Whether German party-finance law and the party's own
statutes permit dues accounting at that level of indirection is an
**open legal question** (OD-2), and it is recorded as one rather than
assumed.

### 9.5 How identity access is audited

Minting a handle is an ordinary audited event. **Resolving** a handle —
the only operation that connects a handle to the evidence that identifies
a party — requires a separate resolution authority, is available only
inside `partyregistry.py`, and emits its own
`finance_party_handle.resolved` audit event recording who resolved what,
under which authority, for which stated purpose. Resolution is therefore
countable and reviewable: "how many times was donor identity accessed
last quarter, by whom, and why" is answerable from the audit trail
without reading any identity data.

### 9.6 How public reporting redacts and aggregates

Public views are built only from published report versions and accepted
contributions, only at the aggregation level the disclosure policy
requires, and only after statistical disclosure control (HI-35, HI-36).
Where a legal obligation requires naming a large donor, the name is not
produced by PACK-10 from stored data — PACK-10 holds no name. It is
produced, if at all, by an explicit, separately authorized disclosure act
whose content comes from the PACK-11 declaration document and which is
recorded as its own governed decision. This is a boundary the
implementation round must honour: **the absence of names in PACK-10 is
not a gap to be filled later, it is the design** (OD-7 records the legal
question of what must be published, and it is a legal question, not an
architectural one).

### 9.7 How a future DLP layer can control exports

Every export or projection leaves through one surface in
`projections.py`, carrying an export purpose, a disclosure policy
binding, and a disclosure classification per field. There is no second
export path, no ad-hoc CSV builder in another module, and no direct store
read from outside the service (HI-47). PACK-12 can therefore attach data
loss prevention at exactly one chokepoint rather than auditing every
call site.

### 9.8 What this model does not claim

Pseudonymization alone does not create anonymity. A `FinancePartyHandle`
is personal data: it is re-identifiable by design, by an authorized
actor, through the registry. The handle limits _correlation_ and
_accidental exposure_; it does not make the underlying processing
non-personal, does not remove any legal basis requirement, and does not
by itself satisfy any data-protection obligation. PACK-09's processing
registry, DPIA and legal-basis machinery apply to PACK-10's processing
exactly as they do to any other, and PACK-10 claims no exemption from
them.

## 10. Organizational model and consolidation

PACK-10 uses PACK-08's organizational model unchanged. It defines no new
organizational entity, no second hierarchy and no finance-local notion of
"parent organization".

- **Local scope ownership.** Accounts, periods, entries, transactions,
  contributions, claims, budgets, assets and obligations belong to the
  organizational unit whose scope they were created in. Bund,
  Landesverband and Kreisverband records are isolated by default (HI-3).
- **Account and report ownership.** An account is owned by exactly one
  scope. A report is owned by the scope that carries the
  `ReportingObligation`, which may legitimately be higher than the scopes
  whose data it consolidates.
- **Authorized cross-scope read access.** Cross-scope reads use PACK-08's
  six access modes (canon 19e.12, ADR-034) and nothing else: exact scope,
  ancestor, descendant, delegated, temporary supervision, and
  institutional oversight without data access. Consolidation is a
  descendant-mode read with an explicit consolidation authority; it is
  never a side effect of hierarchy position (HI-53).
- **Consolidation boundaries.** A consolidating scope reads lower-scope
  records and writes exactly one thing: its own `ConsolidationRecord` in
  its own scope (HI-39). It cannot post, correct, reclassify, approve or
  close anything in a lower scope.
- **Effective-dated relationships.** Consolidation resolves the
  organizational graph **as of the reporting period**, using PACK-08's
  effective dating (ADR-033), not as of report time.
- **Reorganization behaviour.** A merger, split or successor declaration
  does not transfer finance authority, does not re-open a closed period
  and does not rewrite a prior perimeter. PACK-08's hard rule that a
  successor relationship alone transfers nothing (canon 19e.10) is
  restated for finance: the successor scope must be granted finance
  authority by its own governed decision.
- **Historical perimeter preservation.** The perimeter of a closed or
  submitted period is a `PerimeterSnapshot` frozen into the report
  version. A later reorganization can never change it (HI-54). This is
  the single most likely place for a plausible-looking implementation to
  go wrong, which is why it has its own invariant, its own test and its
  own threat-model entry (T-24).
- **Transfers between organizational units.** Modelled as two scoped
  transactions bound by one `internal_transfer_reference`. Consolidation
  eliminates the pair exactly once; the elimination is recorded in the
  `ConsolidationRecord` so it is auditable rather than implicit.
- **Prevention of double counting.** Three mechanisms together: the
  transfer pairing above; aggregation keyed on (handle, period,
  perimeter) rather than on scope alone; and the rule that a contribution
  received by one unit is counted in exactly one unit's income, with
  onward transfer recorded as a transfer, never as new income.
- **Prevention of unauthorized lower-scope mutation.** Structural:
  consolidation code has read access only, and the write guard resolves
  the target record's own scope (HI-3, HI-39).
- **Explicit authority for consolidation.** A named, effective-dated
  consolidation authority in the consolidating scope, resolved through
  PACK-08. Absence denies (`FINANCE_CROSS_SCOPE_CONSOLIDATION_DENIED`).

## 11. PACK-09 integration

PACK-10 consumes PACK-09 through typed references and explicit interfaces
only (HI-47). The reference types are PACK-09's own
`services/compliance-service/src/epd2_compliance_service/references.py`
exports.

| PACK-10 use case                                                    | PACK-09 reference consumed                       |
| ------------------------------------------------------------------- | ------------------------------------------------ |
| A legal case about a finance violation, dispute or correction       | `LegalCaseRef`                                   |
| A procedural deadline for reporting, correction, return or response | `DeadlineRef`, `DeadlineTriggerRef`              |
| A legally effective notice from or to an authority                  | `NoticeRef`, `NoticeEffectRef`                   |
| A legal hold freezing finance records                               | `HoldRef`                                        |
| Retention class binding for a finance record                        | `RecordClassRef`                                 |
| Finance material a PACK-09 case cites                               | `FinanceEvidenceRef` (PACK-09 → PACK-10 pointer) |
| The competent-authority determination for a case kind in a scope    | `JurisdictionRef`                                |
| A party to a finance-related case                                   | `CasePartyRef` (never resolved by PACK-10)       |

Stated clearly, because each of these is a boundary an implementation
could accidentally cross:

- **PACK-10 does not decide PACK-09 case procedure.** It opens or cites a
  case; the case's own lifecycle, admissibility, hearings, decisions and
  remedies stay PACK-09's.
- **PACK-10 does not derive legal effect from ordinary delivery or read
  telemetry** (HI-28). Only a PACK-09 `NoticeEffectDecision`, surfaced as
  a `NoticeEffectRef`, starts a deadline or makes an authority response
  legally effective — exactly as ADR-043 fixed it.
- **PACK-10 cannot destroy held records** (HI-23). It re-reads hold state
  immediately before any disposal-relevant action and never caches it.
- **PACK-10 must preserve the references needed for future PACK-11
  documents and evidence** (section 12).
- **No cross-service direct storage access is allowed** (HI-47).

### 11.1 Is `FinanceEvidenceRef` still sufficient?

PACK-09 exports `FinanceEvidenceRef` as a `PlaceholderRef` subclass:
`owner = PlaceholderOwner.PACK_10_FINANCE`, an open `kind` string, an
opaque `external_reference`, and an `organization_id`. It exists so a
PACK-09 case, filing, hearing or notice can point at finance material
without PACK-09 owning it.

Assessment: **it remains sufficient and needs no replacement now**, with
one semantic correction and one addition, both specified here and
implemented in neither round:

1. **Semantic correction (documentation-level).** The name says
   "evidence", but the object it points at is a PACK-10 _finance record_
   (a transaction, contribution, sponsorship agreement, report version or
   snapshot) — not evidence content, which is PACK-11's (HI-22). The
   implementation round should document this in PACK-10's own
   `references.py` and in the PACK-11 integration ADR, so no reader
   concludes that holding a `FinanceEvidenceRef` means holding evidence.
2. **Addition, not migration.** PACK-10 exports its own typed references
   for later packs and for PACK-09's benefit: `FinanceRecordRef`,
   `FinanceReportRef`, `FinanceReportVersionRef`, `ContributionRef`,
   `SponsorshipRef`, `FinanceAuditEngagementRef` and
   `FinancePartyHandleRef` (the last one carrying a handle id and purpose
   and being resolvable by nobody outside `partyregistry.py`). Each is a
   `ScopedRef` in PACK-09's established shape: id plus scope, no content.
3. **Optional future step, explicitly not required.** PACK-09 could later
   accept a typed `FinanceRecordRef` in place of the string
   `external_reference`. That would be a change to PACK-09's own module
   and therefore a PACK-09-side ADR, in a separate round, with its own
   review. This specification records it as an option
   (`PACK-10-CROSS-PACK-BOUNDARIES.md` section 3.2, OD-15), specifies
   what it would entail, and does not implement it.

No migration is required for this specification to be implementable. If
the owner chooses option 3 later, the migration is: PACK-10 begins
minting `external_reference` strings in a documented, parseable, scoped
form from day one (specified now, so the option stays open), and PACK-09
adds a typed alias later without breaking existing references.

## 12. PACK-11 integration boundary

PACK-10 defines typed placeholders — and only placeholders — for the
material PACK-11 will own: invoices, receipts, contracts, bank
statements, valuation reports, donation declarations, sponsorship
agreements (the document, as distinct from the PACK-10 agreement
record), audit working papers, signed reports, submission receipts and
publication renditions.

All of them use one shape, `FinanceEvidenceReference`, mirroring PACK-09's
`PlaceholderRef`: `owner = PACK_11_DOCUMENTS`, an open `kind` string
(PACK-11 defines the taxonomy, not PACK-10), an opaque
`external_reference`, and the organizational scope.

PACK-10 may store the metadata and scoped references governed finance
requires: which kind of document is expected, whether one is present,
which record it belongs to, and when the reference was recorded. PACK-10
must not store document bytes, document content, signatures,
cryptographic chains or evidence custody (HI-22).

The specification prevents a document reference from being treated
automatically as **authentic**, **signed**, **admitted evidence**,
**authoritative**, **legally valid** or **publishable**. The mechanism is
structural rather than a naming convention: the reference type has no
`is_authentic`, `is_signed`, `is_admitted`, `is_valid` or
`is_publishable` field to read, and every place a finance decision would
want such a fact requires either a PACK-09 governed determination or a
future PACK-11 interface call. Where a finance action needs an assertion
PACK-10 cannot make, it fails closed with
`FINANCE_EVIDENCE_REFERENCE_MISSING` or
`FINANCE_EVIDENCE_ASSERTION_UNAVAILABLE` rather than assuming.

Required future PACK-11 interface, stated as requirements PACK-10 will
consume and not as a design PACK-10 imposes: resolve a reference to a
document's existence and kind within a scope; report a signature or
signed-original status as a governed determination; report an
admissibility determination; and produce a publication rendition
identifier that a public view can cite. Until those exist, PACK-10
records the reference and the absence of the assertion.

## 13. Policies and effective dating

Every threshold, category, classification scheme, approval rule,
disclosure rule and perimeter rule is a `FinancePolicy` version, not a
constant (section 8.2.20). The kinds are: `chart_of_accounts`,
`income_classification`, `expenditure_classification`,
`contribution_classification`, `contribution_restriction`, `aggregation`,
`disclosure_threshold`, `sponsorship_classification`,
`approval_threshold`, `expense_approval`, `accounting_period`,
`retention_binding`, `report_perimeter`, `report_structure`,
`public_disclosure`, `statistical_disclosure`, and `party_handle`.

Four rules govern all of them:

1. **A policy update must not rewrite historical decisions.** Policies
   are effective-dated and append-only; a superseded version stays
   readable forever, because a past decision is only interpretable
   against the rules that produced it.
2. **Every protected decision binds to the policy version it used.** The
   binding is a stored `FinancePolicyBinding` on the decision, not a
   lookup at read time (HI-44).
3. **Unknown or missing applicable policy fails closed.** No default
   policy, no "latest version" fallback, no implicit global scope:
   `FINANCE_POLICY_MISSING` or `FINANCE_POLICY_VERSION_UNKNOWN`.
4. **No German legal threshold is asserted as fact by this
   specification.** Where a recommended default is offered at all, it
   appears in `PACK-10-OPEN-DECISIONS.md`, is marked legally unverified,
   and requires owner and legal confirmation before an implementation
   round may seed it.

Retroactive effective dating deserves its own statement, because it is
the plausible-looking bypass: a policy version may not be given an
`effective_from` that reaches back into a closed accounting period or a
submitted reporting period. Correcting a past period is a correction and
restatement workflow with its own authority (section 4.9), never a
backdated policy.

## 14. Domain events

The proposed taxonomy follows canon section 20's naming
(`<aggregate>.<past_tense_fact>`) and canon section 21's envelope
unchanged. The `finance_` prefix on contribution, policy, audit and party
events is deliberate: canon 13.2 already owns `Contribution` as a
deliberation utterance, and an event named `contribution.received` would
be ambiguous forever (section 3, rule 3).

Every event below is a proposal for canon section 20 (new subsection 20.17
in the amendment proposal), not an implemented builder.

| Event                                              | Emitted when                                 | Payload beyond the canon envelope                                                                                                |
| -------------------------------------------------- | -------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| `finance_account.created`                          | An account is created in a scope             | account id, code, classification code, policy binding                                                                            |
| `finance_account.status_changed`                   | Activation, restriction, closure             | account id, from/to status, reason code                                                                                          |
| `accounting_period.opened`                         | A period is opened                           | period id, boundaries, timezone, policy binding                                                                                  |
| `accounting_period.closed`                         | A period is locked                           | period id, closing balances digest                                                                                               |
| `accounting_period.reopening_requested`            | Reopening is requested                       | period id, requesting authority, reason code                                                                                     |
| `accounting_period.reopened`                       | Reopening is authorized and applied          | period id, authorizing authority, reopening record id, preserved-state digest                                                    |
| `journal_entry.drafted`                            | A draft entry is created                     | entry id, transaction reference, line count                                                                                      |
| `journal_entry.posted`                             | An entry is posted                           | entry id, period id, entry sequence, balanced-sum check result, amounts by currency                                              |
| `journal_entry.reversed`                           | A reversing entry is posted                  | original entry id, reversing entry id, reason code                                                                               |
| `financial_transaction.recorded`                   | A business fact is recorded                  | transaction id, transaction/posting/value dates, provenance kind, import batch reference, party handle reference, policy binding |
| `financial_transaction.classification_changed`     | Classification or reclassification           | transaction id, from/to class, authority, reason code, policy binding                                                            |
| `reconciliation.recorded`                          | A reconciliation act is recorded             | reconciliation id, account id, period id, outcome, evidence reference                                                            |
| `import_batch.registered`                          | A batch is registered                        | batch id, source system reference, fingerprint, row count                                                                        |
| `import_batch.completed`                           | A batch is applied                           | batch id, applied/rejected row counts                                                                                            |
| `import_batch.rejected`                            | A batch is rejected                          | batch id, reason codes, row-level finding count                                                                                  |
| `finance_contribution.received`                    | A contribution receipt is created            | contribution id, party handle reference, method, amount or in-kind marker, policy binding                                        |
| `finance_contribution.quarantined`                 | Provisional quarantine                       | contribution id, exceptional state, reason code                                                                                  |
| `finance_contribution.assessed`                    | An assessment is appended                    | contribution id, assessment outcome, aggregation snapshot digest, policy binding                                                 |
| `finance_contribution.accepted`                    | Acceptance is decided                        | contribution id, deciding authority, policy binding                                                                              |
| `finance_contribution.rejected`                    | Rejection is decided                         | contribution id, deciding authority, reason code                                                                                 |
| `finance_contribution.return_required`             | A return obligation is determined            | contribution id, reason code, deadline reference                                                                                 |
| `finance_contribution.returned`                    | The return is settled                        | contribution id, payment authorization reference                                                                                 |
| `finance_contribution.escalated`                   | Escalation to a legal case                   | contribution id, legal case reference, reason code                                                                               |
| `finance_in_kind_valuation.recorded`               | An in-kind valuation is recorded             | subject reference, valuation method reference, valuation date, evidence reference                                                |
| `sponsorship.registered`                           | An agreement is registered                   | agreement id, sponsor handle reference, value, counter-performance presence                                                      |
| `sponsorship.approved`                             | Approval                                     | agreement id, approving authority, policy binding                                                                                |
| `sponsorship.rejected`                             | Rejection                                    | agreement id, authority, reason code                                                                                             |
| `sponsorship.disclosure_classified`                | Disclosure classification                    | agreement id, disclosure class, policy binding                                                                                   |
| `external_financial_benefit.recorded`              | A benefit is recorded                        | benefit id, benefit type, valuation, assessment outcome                                                                          |
| `expense_claim.submitted`                          | A claim is submitted                         | claim id, claimant handle reference, amount, purpose class                                                                       |
| `expense_claim.reviewed`                           | A review is appended                         | claim id, reviewing authority, outcome                                                                                           |
| `expense_claim.approved`                           | Approval                                     | claim id, approving authority, policy binding                                                                                    |
| `expense_claim.rejected`                           | Rejection                                    | claim id, authority, reason code                                                                                                 |
| `expense_claim.corrected`                          | A correction is recorded                     | claim id, correcting record id, reason code                                                                                      |
| `payment.authorized`                               | A payment is authorized                      | authorization id, payable reference, authorizing authority, amount                                                               |
| `payment.settled`                                  | A payment is executed                        | authorization id, executing authority, settling transaction id                                                                   |
| `budget.approved`                                  | A budget version is approved                 | budget id, version, approving authority, line count                                                                              |
| `budget.amended`                                   | A new version supersedes                     | budget id, from/to version, reason code                                                                                          |
| `financial_asset.recorded`                         | An asset is recorded                         | asset id, asset class, valuation                                                                                                 |
| `financial_asset.revalued`                         | Revaluation                                  | asset id, method reference, valuation date, new valuation                                                                        |
| `financial_asset.written_off`                      | Write-off                                    | asset id, authority, reason code                                                                                                 |
| `financial_obligation.recorded`                    | An obligation is recorded                    | obligation id, obligation type, valuation                                                                                        |
| `financial_obligation.revalued`                    | Revaluation                                  | obligation id, method reference, valuation date                                                                                  |
| `financial_obligation.settled`                     | Settlement                                   | obligation id, payment authorization reference                                                                                   |
| `financial_obligation.written_off`                 | Write-off                                    | obligation id, authority, reason code                                                                                            |
| `reporting_obligation.created`                     | An obligation to report is recorded          | obligation id, period, perimeter definition reference, deadline reference                                                        |
| `reporting_perimeter.defined`                      | A perimeter version is activated             | definition id, version, effective dates, included scope count                                                                    |
| `finance_report.snapshot_frozen`                   | A source snapshot is frozen                  | snapshot id, content digest, period id set, policy binding set                                                                   |
| `finance_report.prepared`                          | A version is prepared from a snapshot        | report id, version, snapshot id, preparing authority                                                                             |
| `finance_report.validation_finding_recorded`       | A validation finding is appended             | report id, version, finding class, reason code                                                                                   |
| `finance_report.consolidated`                      | Consolidation is recorded                    | report id, version, consolidation record id, eliminated transfer count                                                           |
| `finance_report.internally_reviewed`               | Internal review                              | report id, version, reviewing authority                                                                                          |
| `finance_report.auditor_reviewed`                  | Auditor review                               | report id, version, engagement id, auditor authority                                                                             |
| `finance_report.correction_requested`              | A correction request is recorded             | report id, version, requesting authority, reason code, deadline reference                                                        |
| `finance_report.approved`                          | Approval by the responsible body             | report id, version, approving authority                                                                                          |
| `finance_report.signed`                            | Legally responsible sign-off                 | report id, version, signatory authority, evidence reference                                                                      |
| `finance_report.submitted`                         | Submission is recorded                       | report id, version, submission record id, recipient authority reference                                                          |
| `finance_report.external_acknowledgement_recorded` | Something came back                          | submission record id, acknowledgement kind — never an acceptance flag                                                            |
| `finance_report.acceptance_recorded`               | Acceptance by an authority is recorded       | report id, version, notice effect reference, deciding authority                                                                  |
| `finance_report.published`                         | Publication                                  | report id, version, publication record id, publication authority, disclosure policy binding                                      |
| `finance_report.restated`                          | A restatement version is created             | report id, new version, restated version, reason code                                                                            |
| `finance_audit.opened`                             | An engagement is opened                      | engagement id, scope, period, auditor authority, independence check result                                                       |
| `finance_audit.finding_recorded`                   | A finding is appended                        | engagement id, finding id, severity class                                                                                        |
| `finance_audit.concluded`                          | The conclusion is recorded                   | engagement id, conclusion class, evidence reference                                                                              |
| `finance_policy.version_published`                 | A policy version becomes active              | policy id, kind, version, effective dates, jurisdiction, approving authority                                                     |
| `finance_policy.superseded`                        | A version is superseded                      | policy id, from/to version, reason code                                                                                          |
| `finance_party_handle.minted`                      | A handle is minted                           | handle id, purpose, perimeter, policy binding — never any identifying attribute                                                  |
| `finance_party_handle.merged`                      | Two handles are determined to be one party   | surviving handle id, merged handle id, deciding authority, reason code                                                           |
| `finance_party_handle.resolved`                    | A handle is resolved to identifying evidence | handle id, resolving authority, stated purpose — an access-audit event, carrying no resolved value                               |

Every event carries, per canon 21 and the conventions PACK-08/PACK-09
established: stable aggregate identifiers; organizational scope; event
type and version; `occurred_at`; the actor's **authority** reference where
permitted (never an actor identity); the reason code where applicable; the
policy version reference where applicable; and safe references only.

No event carries: names; addresses; bank-account details; identity
documents; free-form evidence content; document bytes; vote information;
credentials; secrets; or any personal data not required for the recorded
fact (HI-2). `finance_party_handle.resolved` is the sharpest case — it
records _that_ a resolution happened, never _what_ was resolved.

## 15. Reason codes

The proposed registry is `contracts/reason-codes/pack-10.yml`, following
ADR-004's model and PACK-09's file conventions exactly: a standalone,
complete file; the seven mandatory fields per entry (`code`, `meaning`,
`severity`, `description`, `retryable`, `owner`,
`introduced_in_version`); a `source` marker distinguishing codes this pack
would introduce from codes it redeclares verbatim from an earlier pack's
registry.

Nothing is registered by this round. The file itself is an
implementation-round deliverable (`PACK-10-IMPLEMENTATION-PLAN.md`
phase 0).

### 15.1 Codes reused, not duplicated

The governing request requires avoiding duplicate codes where an existing
code has the same semantics. Thirty-two existing codes cover PACK-10
situations exactly and are reused verbatim (redeclared in pack-10.yml with
`source: pack-0X-reused`, the pattern PACK-09's registry header
describes):

| Existing code                                   | Introduced by         | PACK-10 use                                                              |
| ----------------------------------------------- | --------------------- | ------------------------------------------------------------------------ |
| `PERMISSION_DENIED`                             | pack-02               | Caller lacks any authority for the operation                             |
| `VALIDATION_RECORD_NOT_FOUND`                   | pack-02               | Unknown record, and the non-disclosing answer for a foreign-scope record |
| `VALIDATION_FORBIDDEN_TRANSITION`               | pack-02               | Any lifecycle transition not in the allowed set                          |
| `VALIDATION_UNKNOWN_STATUS`                     | pack-02               | Unknown status value on input                                            |
| `OPTIMISTIC_CONCURRENCY_CONFLICT`               | pack-02               | Stale `expected_*_version` (HI-51)                                       |
| `AUDIT_CHAIN_BROKEN`                            | pack-02               | Audit append integrity failure (HI-52)                                   |
| `EVENT_VERSION_UNSUPPORTED`                     | pack-02               | Unsupported event version                                                |
| `INTEGRITY_CHECK_FAILED`                        | pack-02               | Snapshot digest or import fingerprint mismatch                           |
| `SERVICE_STATE_READ_ONLY`                       | pack-02               | Service in read-only state                                               |
| `EMERGENCY_FREEZE_ACTIVE`                       | pack-02               | Emergency freeze blocks the write                                        |
| `ORGANIZATION_SCOPE_MISMATCH`                   | canon 0.7.0 / pack-08 | Asserted scope does not match the target record's scope (HI-3)           |
| `ORGANIZATION_SCOPE_UNDETERMINED`               | pack-08/09            | Scope cannot be determined — default deny (HI-4)                         |
| `CROSS_SCOPE_ACCESS_DENIED`                     | canon 0.7.0           | None of the six access modes granted access                              |
| `CROSS_SCOPE_AUTHORITY_INVALID`                 | pack-09               | Presented cross-scope authority is invalid                               |
| `AUTHORITY_ROLE_INCOMPATIBLE`                   | canon 0.7.0           | Auditor/administrator and other incompatible pairs (HI-31)               |
| `AUTHORITY_ASSIGNMENT_INVALID`                  | canon 0.7.0           | Authority record fails PACK-08's lifecycle rule                          |
| `AUTHORITY_SCOPE_INVALID`                       | canon 0.7.0           | Authority scope is structurally invalid                                  |
| `ORGANIZATIONAL_AUTHORITY_NOT_USABLE`           | pack-08               | Authority exists but is not currently usable (HI-53)                     |
| `ORGANIZATION_DUAL_CONTROL_VIOLATION`           | pack-08               | One actor on both sides of a dual-control action (HI-32)                 |
| `CONFLICT_OF_INTEREST_UNDECLARED`               | pack-07/09            | Conflict state undeclared — fails closed (HI-33)                         |
| `CONFLICT_OF_INTEREST_BLOCKING`                 | pack-07/09            | Declared conflict blocks the action                                      |
| `CONFLICT_REVIEW_SELF_APPROVAL_PROHIBITED`      | pack-07               | Self-approval of own or self-benefiting act (HI-32)                      |
| `RECORD_UNDER_LEGAL_HOLD`                       | pack-09               | Legal hold blocks the disposal-relevant action (HI-23)                   |
| `LEGAL_HOLD_STATE_UNKNOWN`                      | pack-09               | Hold state indeterminate — fails closed                                  |
| `RETENTION_POLICY_REBIND_REQUIRES_REEVALUATION` | pack-09               | Retention rebinding cannot shorten an obligation (HI-24)                 |
| `GOVERNED_RECORD_DELETION_FORBIDDEN`            | pack-09               | Any deletion attempt on a governed finance record (HI-5)                 |
| `HISTORICAL_SCOPE_NOT_EFFECTIVE`                | canon 0.7.0           | Scope/authority queried outside its effective window (HI-54)             |
| `SUCCESSOR_TRANSFER_REQUIRES_DECISION`          | canon 0.7.0           | Reorganization relation used as if it transferred finance authority      |
| `PUBLICATION_NOT_ALLOWED`                       | pack-04               | Publication without a separate publication authorization (HI-29)         |
| `DISCLOSURE_POLICY_VIOLATION`                   | pack-04               | Emission would violate the disclosure policy                             |
| `CRITICAL_POLICY_ACTIVATION_NOT_AUTHORIZED`     | pack-07               | Critical policy version activated without the required approval          |
| `CRITICAL_POLICY_VERSION_FROZEN`                | pack-07               | Attempt to edit a frozen policy version                                  |

### 15.2 Codes PACK-10 would introduce

Forty-four new codes, all owned by `finance-service`,
`introduced_in_version: 0.10.0` — that field carries the **repository**
version the code would be introduced in, which is a different axis from
`CANON_VERSION` (section 19). With the thirty-two reused entries the
proposed registry file holds seventy-six entries:

| Proposed code                                        | Meaning                                                                                              | Severity | Proves / enforces      |
| ---------------------------------------------------- | ---------------------------------------------------------------------------------------------------- | -------- | ---------------------- |
| `FINANCE_AUTHORITY_MISSING`                          | No active, scope-matching finance authority for this action                                          | error    | HI-53, HI-44           |
| `FINANCE_AUDITOR_INDEPENDENCE_VIOLATION`             | The candidate auditor fails the independence check for this scope/period                             | error    | HI-30, HI-31           |
| `FINANCE_ACCOUNTING_PERIOD_CLOSED`                   | The target period is closed; ordinary writes are refused                                             | error    | HI-10                  |
| `FINANCE_ACCOUNTING_PERIOD_UNDETERMINED`             | No period, or no timezone-explicit period, could be determined                                       | error    | HI-42, HI-44           |
| `FINANCE_PERIOD_REOPENING_NOT_AUTHORIZED`            | Reopening lacks authority, reason or dual control                                                    | error    | HI-11                  |
| `FINANCE_JOURNAL_ENTRY_UNBALANCED`                   | Debit and credit sums differ for a currency                                                          | error    | HI-7                   |
| `FINANCE_CURRENCY_UNSUPPORTED`                       | Currency is not in the active policy, or mixed-currency arithmetic was attempted                     | error    | HI-8                   |
| `FINANCE_MONETARY_AMOUNT_INVALID`                    | Amount is not expressible as integer minor units with a recorded scale and rounding rule             | error    | HI-9, HI-55            |
| `FINANCE_IMMUTABLE_RECORD_MODIFICATION_ATTEMPTED`    | An attempt to modify a posted entry, frozen snapshot, submitted version or create-once record        | error    | HI-6, HI-25, HI-26     |
| `FINANCE_DUPLICATE_TRANSACTION`                      | A transaction with the same fingerprint already exists                                               | error    | HI-41                  |
| `FINANCE_DUPLICATE_IMPORT`                           | The batch fingerprint matches an already-applied batch                                               | error    | HI-41                  |
| `FINANCE_IMPORT_PROVENANCE_MISSING`                  | An imported transaction lacks a batch or provenance                                                  | error    | HI-40                  |
| `FINANCE_TRANSFER_PAIR_UNRESOLVED`                   | An inter-unit transfer has no matching counterpart                                                   | error    | HI-39, double counting |
| `FINANCE_RECLASSIFICATION_BYPASS_DENIED`             | The requested reclassification would drop a disclosure, review, aggregation or reporting obligation  | error    | HI-13                  |
| `FINANCE_CONTRIBUTION_SOURCE_UNDETERMINED`           | Contributor source is anonymous or cannot be established                                             | error    | HI-16                  |
| `FINANCE_CONTRIBUTION_VERIFICATION_INCOMPLETE`       | Required verification or declaration is missing                                                      | error    | HI-16                  |
| `FINANCE_CONTRIBUTION_CLASSIFICATION_UNDETERMINED`   | No policy-bound classification could be determined                                                   | error    | HI-44                  |
| `FINANCE_CONTRIBUTION_PROHIBITED`                    | Policy classifies this contribution as prohibited or restricted                                      | error    | HI-17                  |
| `FINANCE_CONTRIBUTION_AGGREGATION_UNRESOLVED`        | The aggregate over the relevant period/perimeter could not be resolved                               | error    | HI-14, HI-15           |
| `FINANCE_CONTRIBUTION_RETURN_REQUIRED`               | A return obligation exists and blocks the requested action                                           | error    | HI-17, HI-18           |
| `FINANCE_IN_KIND_VALUATION_MISSING`                  | A non-monetary contribution or benefit lacks a valuation basis                                       | error    | HI-19                  |
| `FINANCE_VALUATION_METHOD_MISSING`                   | A valuation or revaluation lacks a method reference                                                  | error    | HI-55                  |
| `FINANCE_COUNTER_PERFORMANCE_MISSING`                | Sponsorship approval without counter-performance or an explicit policy classification                | error    | HI-20                  |
| `FINANCE_SPONSORSHIP_DISCLOSURE_INCOMPLETE`          | Required disclosure classification or declaration is missing                                         | error    | HI-20, HI-36           |
| `FINANCE_PAYMENT_AUTHORIZATION_MISSING`              | Settlement attempted without a valid authorization                                                   | error    | HI-32                  |
| `FINANCE_WRITE_OFF_NOT_AUTHORIZED`                   | Write-off lacks the authority or dual control the policy requires                                    | error    | HI-32                  |
| `FINANCE_BUDGET_ACTUAL_WRITE_FORBIDDEN`              | An attempt to store an actual amount on a budget line                                                | error    | HI-12                  |
| `FINANCE_CROSS_SCOPE_CONSOLIDATION_DENIED`           | Consolidation lacks explicit authority, or would write into a lower scope                            | error    | HI-39                  |
| `FINANCE_REPORTING_PERIMETER_UNDETERMINED`           | No effective perimeter definition for the period                                                     | error    | HI-54, HI-44           |
| `FINANCE_REPORT_SNAPSHOT_MISSING`                    | Preparation, validation or submission attempted without a frozen snapshot                            | error    | HI-25                  |
| `FINANCE_REPORT_VALIDATION_INCOMPLETE`               | Required validations have not completed or have open blocking findings                               | error    | HI-34                  |
| `FINANCE_REPORT_APPROVAL_MISSING`                    | The action requires an approval that has not been recorded                                           | error    | HI-34                  |
| `FINANCE_REPORT_SIGN_OFF_MISSING`                    | The action requires the legally responsible sign-off                                                 | error    | HI-34                  |
| `FINANCE_REPORT_STATUS_UNKNOWN`                      | Report status cannot be determined — fails closed                                                    | error    | HI-44                  |
| `FINANCE_AUDIT_INCOMPLETE`                           | Auditor review requires a concluded engagement for this scope and period                             | error    | HI-30, HI-34           |
| `FINANCE_EXTERNAL_ACKNOWLEDGEMENT_NOT_AUTHORITATIVE` | An acknowledgement, receipt, delivery record or read status was offered as acceptance                | error    | HI-27, HI-28           |
| `FINANCE_STATISTICAL_DISCLOSURE_RISK`                | The requested view would breach the small-cell or combination rules                                  | error    | HI-36                  |
| `FINANCE_EVIDENCE_REFERENCE_MISSING`                 | A required evidence or document reference is absent                                                  | error    | HI-19, HI-22           |
| `FINANCE_EVIDENCE_ASSERTION_UNAVAILABLE`             | An assertion about a document (authentic, signed, admitted) is required but only PACK-11 can make it | error    | HI-22                  |
| `FINANCE_PARTY_HANDLE_PURPOSE_MISMATCH`              | A handle was presented for a purpose or perimeter it was not minted for                              | error    | HI-48                  |
| `FINANCE_PARTY_HANDLE_RESOLUTION_DENIED`             | Handle resolution attempted without the separate resolution authority                                | error    | HI-1, section 9.5      |
| `FINANCE_RETENTION_BINDING_MISSING`                  | A governed finance record has no PACK-09 record-class binding                                        | error    | HI-24                  |
| `FINANCE_POLICY_MISSING`                             | No applicable policy of the required kind exists for this scope and date                             | error    | HI-44                  |
| `FINANCE_POLICY_VERSION_UNKNOWN`                     | The referenced policy version does not exist or is not readable                                      | error    | HI-44                  |

### 15.3 Old/new comparison — collisions this analysis found and resolved

Four existing code families look like they cover PACK-10 situations and do
not. Each would have been a real, silent semantic collision:

| Existing code(s)                                                                                                                                 | Existing meaning                                                                     | Why PACK-10 does not reuse it                                                                                                                                     |
| ------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CONTRIBUTION_CREATED`, `CONTRIBUTION_EDITED`, `CONTRIBUTION_FLAGGED`, `CONTRIBUTION_STATUS_CHANGED`, `CONTRIBUTION_DUPLICATE_CREATION_CONFLICT` | pack-03: a **deliberation contribution** (canon 13.2) — an utterance in a discussion | Different entity, different context, different owner. PACK-10's donation concept uses `FINANCE_CONTRIBUTION_*` so no code, event or log line is ambiguous         |
| `LEDGER_ENTRY_ALREADY_PUBLISHED`, `LEDGER_ENTRY_DUPLICATE_CONFLICT`, `TRANSPARENCY_LEDGER_ENTRY_PUBLISHED`                                       | pack-04: `PublicLedgerEntry` — the **public transparency ledger** (canon 19a.1)      | A transparency ledger entry is a published civic record, not an accounting posting. PACK-10 uses `FINANCE_JOURNAL_ENTRY_*`                                        |
| `ACCOUNT_CREATED`, `ACCOUNT_STATUS_CHANGED`                                                                                                      | pack-02: `Account` — a **platform user account** (canon 7.2)                         | PACK-10's account is a chart-of-accounts node. The `finance_account.*` event names keep the two apart                                                             |
| `AUDIT_EXPORT_INTEGRITY_FAILED`, `AUDIT_EVENT_CONFLICT`                                                                                          | pack-02/04: **audit-log** integrity                                                  | PACK-10's audit concept is a **finance audit engagement** by a `finance_auditor`. `FINANCE_AUDIT_*` codes and events are used; audit-log codes keep their meaning |

One further near-collision was resolved the other way: PACK-09's
`RETENTION_*`, `LEGAL_HOLD_*` and `RECORD_UNDER_LEGAL_HOLD` codes mean
exactly what PACK-10 needs, because retention and holds remain PACK-09's
domain. They are reused verbatim rather than shadowed by `FINANCE_`
duplicates.

## 16. Security and threat analysis

The full threat model is `docs/packs/PACK-10-THREAT-MODEL.md`: thirty-five
threats, each with protected asset, attacker or failure mode, trust
boundary, mitigation, detection, audit evidence, residual risk and
future-pack dependency.

Four residual risks are severe enough to belong in the specification
itself, because no PACK-10 mechanism closes them and an implementation
round must not pretend otherwise:

1. **Collusion of two or more authorized authorities** defeats every
   separation-of-duties rule in this pack. PACK-10 makes collusion
   _evidenced_ (append-only history, distinct authority references,
   audit chain), not impossible.
2. **False external acceptance** is prevented in the data model (HI-27)
   but the correctness of the recorded authoritative reference depends on
   a human recording the right thing; there is no external gateway to
   verify against until one exists (section 5, OD-16).
3. **Undisclosed intermediary and beneficial-origin concealment** cannot
   be detected by a system that receives only what the contributor
   declares. PACK-10 records declarations, aggregates known
   relationships, and fails closed on the unknown; it cannot discover a
   concealed principal.
4. **Identity re-identification by an authorized resolver** is inherent
   in section 9.8: the handle model limits correlation, not lawful
   resolution. PACK-12's DLP layer, when it exists, is what constrains
   export.

## 17. Canon amendment determination

**Conclusion: option 2 — a canon amendment is required.**

PACK-10 introduces or materially clarifies system-wide concepts that no
accepted canon section covers: an authoritative financial record; an
immutable balanced ledger; independent finance audit as a workflow rather
than only a role name; a purpose-scoped financial party reference; a
report snapshot; submission versus legal acceptance for a financial
report; finance-specific separation of duties; the financial
external-influence boundary against PACK-35; and public financial
disclosure safeguards. It also needs new rows in canon section 22
(ownership matrix), new entries in section 23 (forbidden links) and new
codes in section 24 — none of which can be added by a pack-level registry
file.

The canonical file is **not edited by this round**. The determination and
its full reasoning are in
`docs/packs/PACK-10-CANON-AMENDMENT-ASSESSMENT.md`; the exact proposed
text, affected sections, compatibility impact, migration impact,
reason-code impact, event-canon impact and the version decision
(`CANON_VERSION` should later move `0.7.0 → 0.8.0`, as a separate,
dedicated round) are in
`docs/packs/PACK-10-CANON-AMENDMENT-PROPOSAL.md`.

`CANON_VERSION` is unchanged by this task.

One consequence the assessment surfaces and this specification records
because it affects the repository, not only the canon:
`docs/canonical/canon-version.json` currently declares
`"repository_compatibility": ">=0.1.0 <0.10.0"`. A PACK-10 implementation
round that moves `REPOSITORY_VERSION` to `0.10.0` would fall outside that
declared range. Whether the range is widened, or the canon amendment
lands first and moves it, is an owner decision (OD-20) — not something
this round changes.

## 18. Specification-level test plan

`docs/packs/PACK-10-ACCEPTANCE-MATRIX.md` is the implementation acceptance
plan: domain tests (money and currency, balancing, journal immutability,
reversal, period close/reopen, contribution lifecycle, aggregation,
sponsorship, reimbursement, budgets, report lifecycle, audit
independence, restatement), application tests (authority checks, conflict
checks, scope isolation, fail-closed cases, legal-hold checks, policy
binding, deadline and notice references, cross-scope consolidation,
derived public projections), storage tests (append-only history,
create-once events, no delete methods, optimistic concurrency,
scope-aware lookup, import idempotency), contract tests (JSON Schema,
OpenAPI, enum stability, event-envelope compatibility, money
serialization, absence of prohibited identity fields, absence of document
content, absence of vote-linkable fields), architecture tests (forbidden
imports, direct storage access prohibition, identity-service isolation,
voting-service isolation, PACK-09 reference-only integration, PACK-11
placeholder-only integration, PACK-35 non-implementation, no prohibited
payload in finance events) and repository tests (expected paths,
reason-code registry, ADR index, version consistency, README/CHANGELOG
consistency, no generated or cache artifacts).

Every planned test in that document names the hard invariant it proves,
and every one of the fifty-five invariants in section 6 is covered by at
least one named test.

## 19. Versions

| Item                 | Before       | After        | Changed by this round                     |
| -------------------- | ------------ | ------------ | ----------------------------------------- |
| `REPOSITORY_VERSION` | 0.9.0        | 0.9.0        | no                                        |
| `CANON_VERSION`      | 0.7.0        | 0.7.0        | no                                        |
| Package versions     | 0.9.0        | 0.9.0        | no                                        |
| Reason-code registry | 8 pack files | 8 pack files | no — `pack-10.yml` is proposed, not added |
| OpenAPI contracts    | unchanged    | unchanged    | no                                        |
| JSON Schemas         | unchanged    | unchanged    | no                                        |

The proposed target for the implementation round is
`REPOSITORY_VERSION = 0.10.0` with `CANON_VERSION = 0.8.0` already in
place from the amendment round, in that order (section 17, OD-20).

## 20. Verification performed this round

Honestly and exactly, so no reader over-reads it:

- **Performed.** Full read of the baseline archive's documentation set:
  canon `TZ-00-domain-event-canon.md` (sections 4, 8, 19a–19e, 20–24),
  `PACK-08-GLOSSARY.md`, PACK-08 specification and open decisions, PACK-09
  specification and implementation notes, PACK-09 final handover and known
  limitations, ADR-032 through ADR-043, the ADR index, the eight
  pack reason-code registry files (303 distinct existing codes enumerated for
  the collision analysis in section 15.3),
  `compliance-service/references.py` in full, the repository checker's
  required-path list, the repository and contract test inventories, and
  the Prettier/`.prettierignore` configuration.
- **Performed.** Documentation-level consistency checks: every path this
  document references exists in the delivered archive; ADR numbering
  continues the sequence after the latest accepted ADR (ADR-043) without
  gaps; every new ADR is marked `proposed`; no accepted ADR text was
  altered.
- **Not performed, and not claimed.** No test run, no `pytest`, no
  `ruff`, no `mypy`, no `prettier --check`, no Next.js build, no GitHub
  Actions run. This round adds no code and no contract, so those suites
  are unchanged from PACK-09's own verified result — but "unchanged" is a
  statement about the diff, not a re-verification, and this document does
  not present it as one.
- **Not performed for a specific reason worth recording.** Prettier could
  not be executed locally in this session (the npm registry was not
  reachable from the working environment). The new markdown was therefore
  written to Prettier 3's default markdown style, and its tables were
  generated by a padding routine that reproduces Prettier's column
  padding. The implementation round — or any CI run — should treat
  `prettier --check .` on `docs/**` as the authoritative confirmation.
  `PACK-10-SPEC-REPORT.md` section 6 repeats this limitation.

## 21. Deliverables of this round

1. `docs/packs/PACK-10-SPECIFICATION.md` — this document.
2. `docs/adr/ADR-044-pack-10-finance-service-decomposition.md`
3. `docs/adr/ADR-045-authoritative-finance-ledger-and-correction-model.md`
4. `docs/adr/ADR-046-purpose-scoped-financial-party-references-and-aggregation.md`
5. `docs/adr/ADR-047-rechenschaftsbericht-lifecycle-snapshot-and-authority-semantics.md`
6. `docs/adr/ADR-048-finance-authority-separation-and-independent-audit.md`
7. `docs/adr/ADR-049-pack-10-pack-09-pack-11-pack-35-boundaries.md`
8. `docs/adr/README.md` — six new index rows and a round narrative.
9. `docs/packs/PACK-10-OPEN-DECISIONS.md`
10. `docs/packs/PACK-10-IMPLEMENTATION-PLAN.md`
11. `docs/packs/PACK-10-ACCEPTANCE-MATRIX.md`
12. `docs/packs/PACK-10-THREAT-MODEL.md`
13. `docs/packs/PACK-10-CROSS-PACK-BOUNDARIES.md`
14. `docs/packs/PACK-10-CANON-AMENDMENT-ASSESSMENT.md`
15. `docs/packs/PACK-10-CANON-AMENDMENT-PROPOSAL.md`
16. `docs/handover/PACK-10-SPEC-REPORT.md`
17. Minimal `README.md` and `CHANGELOG.md` updates identifying PACK-10 as
    specification-only and not implemented.

No implementation source directory was created to reserve a name, and no
empty runtime package was added.

## 22. No claim of legal compliance, and no claim of readiness

PACK-10 does not, and must not be read to, establish compliance with the
Parteiengesetz, the Abgabenordnung, the Handelsgesetzbuch, the GDPR, the
BDSG, any Land-level party or transparency statute, or any other law. It
does not make the resulting system tax-compliant, audited,
production-ready, certified, or accepted by the Bundestagsverwaltung or
any other authority.

Concretely:

- **Classifications are managed fields.** Choosing an income class, a
  contribution category or a disclosure class records what the
  organization has documented. It asserts nothing about whether the
  choice is legally correct.
- **Thresholds are inputs.** Every threshold, period and category comes
  from a human-supplied, versioned policy. This document proposes no
  legal threshold as fact.
- **The `Rechenschaftsbericht` lifecycle is a workflow, not an
  attestation.** Reaching `signed` means a recorded signatory authority
  performed a recorded act; it does not mean the report is correct,
  complete or sufficient. Reaching `accepted_by_authority` means an
  authoritative reference was recorded; the legal effect of that
  acceptance is determined outside this system.
- **The finance audit is an internal governed workflow.** An
  `AuditConclusion` is not a statutory audit opinion (section 8.3), and
  the entity is named so that it cannot be mistaken for one.
- **Pseudonymization is not anonymity** (section 9.8), and no data
  protection obligation is satisfied by architecture alone.
- **Every legal determination remains a human judgement made outside this
  system**, recorded here with its authority, its reason and its
  evidence references — which is the whole of what PACK-10 offers.

`PACK-10-OPEN-DECISIONS.md` lists every question this round refused to
answer by guessing, with a recommended default where one is defensible
and an explicit statement that a legally unverified default is not law.
