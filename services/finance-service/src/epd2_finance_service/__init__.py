"""Finance Service — PACK-10's one wholly new service (ADR-048).

Sole authoritative owner of the party-finance bounded context defined by
canon 0.8.0 section 19f: the chart of accounts and accounting periods
(`FinanceAccount`, `AccountingPeriod`), the authoritative accounting
register (`JournalEntry`, `PostingLine`), the transaction register with
its provenance and import batches (`FinancialTransaction`,
`GovernedTransfer`), contributions and their exceptional states
(`FinanceContribution`), sponsorship and external financial benefit
(`SponsorshipAgreement`, `ExternalFinancialBenefit`), the expense and
reimbursement workflow with separated authorisation and execution
(`ExpenseClaim`, `PaymentAuthorization`, `Reimbursement`), assets and
obligations (`FinancialAsset`, `FinancialObligation`), the reporting
obligation, perimeter and frozen snapshot (`ReportingObligation`,
`ReportingPerimeterDefinition`, `ReportSnapshot`), the twelve-state
`Rechenschaftsbericht` lifecycle (`FinanceReportVersion`), the
independent finance audit (`AuditEngagement`, `AuditConclusion`), and the
purpose-scoped party reference (`FinancePartyHandle`).

Module map, in dependency order — each module imports only from those
above it:

- `exceptions` — one class per reason code, no domain knowledge.
- `domain` — value objects, identity minimisation, `Money`, pure
  invariant functions. No I/O, no clock, no storage.
- `authorization` — finance roles, action authorities, the
  incompatibility matrix, separation-of-duties assertions.
- `ledger` — accounts, periods, balanced postings, correction and
  reversal.
- `records` — contributions, sponsorship, external benefit, expense
  claims, payments, assets, obligations, transfers.
- `reporting` — reporting obligation, perimeter, snapshot, the report
  lifecycle, the audit engagement.
- `events` — the seventy-two canonical section-20.17 event builders and
  the audit-state payloads.
- `references` — the outward-facing typed references other packs may
  hold, and the refusals that keep foreign concepts out.
- `storage` — storage ports and in-memory reference adapters. No delete
  method exists on any port.
- `projections` — derived, versioned, non-authoritative read models,
  including the publication-safe projections.
- `application` — the commands and queries: authority checks,
  idempotency, optimistic concurrency, reason-coded refusals, canonical
  events and audit appends.

**What this service is not.** It carries no production data plane: every
adapter in `storage` is in-memory, and PACK-13 owns the durable one. It
integrates with no bank, no payment provider and no external authority
system; a submission is a *reference* to an act performed elsewhere. It
owns no document bytes or evidence content (PACK-11), no lobbying-contact
disclosure (PACK-35), no retention or legal-hold decision (PACK-09), and
no identity (`ФИН-01`: there is no user, person or member identifier
anywhere in this package).

**No claim of legal compliance or operational readiness.** This service
implements a governed workflow with auditability and reason-coded
refusals. Whether any accounting treatment, valuation, aggregation rule,
disclosure threshold, retention schedule or report satisfies German party
law, the Parteiengesetz, statutory accounting rules or any authority's
requirements remains a human legal and accounting judgement made outside
this system (`ФИН-43`).
"""

from __future__ import annotations
