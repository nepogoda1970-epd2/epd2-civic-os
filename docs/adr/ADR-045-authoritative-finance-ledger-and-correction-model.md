# ADR-045: Authoritative finance ledger, balanced posting and correction model

## Status

`proposed`

## Date

2026-07-27

## Context

A party's internal accounting has two things that both look like "the
truth" and are not the same thing. One is the double-entry general
ledger: balanced debits and credits that determine the party's
financial position. The other is the record of what actually
happened — a donation received, an invoice paid, a transfer between
organizational units — with who or what caused it, which policy
version classified it, which evidence supports it, and which import
batch it arrived through. Collapsing these into one aggregate, or
declaring one a cache of the other, is the standard failure mode
finance systems fall into, and it produces the two failures PACK-10
cannot tolerate: a balanced ledger that cannot explain itself, or a
well-documented business record whose monetary effect was never
checked for balance.

PACK-10 additionally inherits three repository-wide conventions this
decision must respect without restating their reasoning: governed
records are never deleted, only disposed of through PACK-09's
three-step workflow (ADR-039); money must never be represented as a
floating-point value anywhere, including on the wire; and a service
may hold only an in-memory reference store this round, per ADR-038's
precedent for `compliance-service` (HI-47, section 5).

## Problem

Which aggregate, if any, is authoritative for a party's financial
position, such that:

- every posted monetary effect is provably balanced, per currency,
  and cannot be posted otherwise;
- the business fact behind a posting — what happened, its purpose,
  its classification, its evidence, its import provenance — is never
  lost, invented, or inferred from the posting alone;
- neither aggregate can silently overrule the other, and no third
  aggregate (trial balance, budget-versus-actual, a public view) can
  be mistaken for a source of truth;
- a business fact with monetary effect but no valid posting is never
  treated as complete; and
- correction happens without ever rewriting a posted record?

## Considered options

- **Option A — general ledger first.** The `JournalEntry` /
  `PostingLine` pair is the only authoritative aggregate. Business
  context (purpose, provenance, classification) is carried as
  optional metadata fields on the entry or its lines.
- **Option B — transaction register first.** `FinancialTransaction`
  is the only authoritative aggregate, carrying both the business
  fact and its own debit/credit amounts. A `JournalEntry` is
  generated from it as a downstream, non-authoritative projection.
- **Option C — layered combination, single authoritative money
  layer.** Two authoritative aggregates with a precise split: the
  ledger (`JournalEntry` + `PostingLine`) is authoritative for
  monetary effect only; the register (`FinancialTransaction`) is
  authoritative for the business fact and its provenance only.
  Neither is a cache of the other. Nothing else is authoritative.

Comparison against the forces in section 4.1 and hard invariants 5-12:

| Concern                              | A — ledger only                                | B — register only                                 | C — layered            |
| ------------------------------------ | ---------------------------------------------- | ------------------------------------------------- | ---------------------- |
| Balancing enforced structurally      | yes, natively                                  | no — amounts on the register are not debit/credit | yes, in `JournalEntry` |
| Provenance/import batch has a home   | bolted onto posting lines, no natural identity | yes, natively                                     | yes, in the register   |
| Reclassification without reposting   | forces editing a posted line, breaks HI-6      | trivial, but then balancing is unverified         | yes — register history |
| Reporting can trust monetary totals  | yes                                            | no — register amounts are declared, not proven    | yes — from the ledger  |
| Single accepted "authoritative" idea | one aggregate, simpler mental model            | one aggregate, simpler mental model               | two, precisely bounded |

Option A fails HI-40/HI-41: an imported transaction's provenance and
duplicate-detection fingerprint have no natural home on a balanced
posting line without turning the ledger into a business-fact store it
was never designed to validate, and every later classification change
becomes an edit to a `posted` entry, which HI-6 forbids outright.

Option B fails HI-7 more fundamentally: nothing forces a register
amount to be balanced, because "balanced" is a property of a set of
debit/credit lines, not of a single business fact. A
`FinancialTransaction` that is its own source of monetary truth can
record an income of 500 EUR with no corresponding equity or asset
movement, and there is no structural check inside that aggregate to
catch it. Making the register enforce balancing would require it to
grow `PostingLine`-shaped internals anyway, at which point it has
become option C with an extra layer of indirection.

## Decision

**Option C.** The general ledger and the transaction register are
both authoritative, over disjoint concerns, and neither is a cache or
a projection of the other:

- The **general ledger** — `JournalEntry` containing an ordered tuple
  of `PostingLine` value objects — is the sole authoritative record
  of **monetary effect**: which accounts moved, by how much, in which
  currency, as of which posting date.
- The **transaction register** — `FinancialTransaction` — is the sole
  authoritative record of the **business fact and its provenance**:
  what happened, the purpose-scoped party reference involved, the
  classification and the `FinancePolicyBinding` it was classified
  under, the evidence references, and the `ImportBatch` it came
  from, if any.

Nothing else is authoritative. Trial balances, period totals,
budget-versus-actual comparisons and every public transparency view
are derived read models, computed on demand or cached for
performance, and are never a point of record (canon 2.2: a read model
is not a source of truth). `budgets.py` accordingly has no import
path to a ledger store (HI-12), and `projections.py` performs no
authoritative write (HI-35).

### Lifecycle coupling

`FinancialTransaction` moves `recorded → classified → posted →
(corrected) → (reversed)`. Reaching `posted` on the transaction
requires a balanced, posted `JournalEntry` to exist for it; a
transaction cannot self-report as posted. A `FinancialTransaction`
that has monetary effect and no balanced, posted `JournalEntry`
attached is an **incomplete state**. It is not a silently accepted
record and it is not treated as zero for reporting purposes — every
report-affecting read (trial balance, period total, `ReportSnapshot`
freeze) fails closed on it rather than omitting it silently, because
omitting it silently is indistinguishable from the business fact
never having been recorded at all.

### Balanced posting

`JournalEntry`'s constructor computes, per currency present in its
`PostingLine`s, the sum of debit minor units and the sum of credit
minor units, and refuses construction if they differ
(`FINANCE_JOURNAL_ENTRY_UNBALANCED`). The same check runs again at
the moment of posting, not only at construction, so that a `draft`
entry cannot be mutated into an unbalanced shape between the two and
slip through on the strength of an earlier check (HI-7).

### Money representation

`Money` is `(minor_units: int, currency_code, scale, rounding_rule)`.
There is no floating-point representation anywhere in the domain
layer, and none on the wire: every JSON Schema for a monetary field
forbids `number` structurally, so a client cannot even construct a
compliant payload that uses one (HI-9). Currency is always explicit;
arithmetic across two `Money` values with different currency codes is
refused (`FINANCE_CURRENCY_UNSUPPORTED`) unless a recorded conversion
— itself a policy-governed, evidenced act, not an inline exchange
rate — produced the second value. A `Money` value that cannot be
expressed as integer minor units at its recorded scale is
`FINANCE_MONETARY_AMOUNT_INVALID` (HI-8, HI-55).

### Immutability and correction

A `posted` `JournalEntry` is terminal for content. There is no update
path to it, structurally — not a soft "posted entries are edited only
by an administrator" convention, but the absence of a mutating method
in `ledger.py`. Correction is always a **new**, governed entry: a
reversing entry that references the original entry by id and carries
a reason code, or a correcting `FinancialTransaction` that produces
its own new balanced entry. Reversal chains are append-only and
cycle-free — a reversal can never itself be the original of an
earlier entry it reverses. Any attempted edit of a posted entry, a
frozen `ReportSnapshot`, or a submitted `FinanceReportVersion` raises
`FINANCE_IMMUTABLE_RECORD_MODIFICATION_ATTEMPTED` (HI-6, HI-25,
HI-26). Deletion is not a distinct, weaker operation available as a
fallback: any deletion attempt on a governed finance record reuses
PACK-09's `GOVERNED_RECORD_DELETION_FORBIDDEN` (HI-5), and, as with
every other pack since ADR-039, there is no delete method on any
store protocol or adapter for a caller to reach for.

### Period close, lock and reopening

`AccountingPeriod` moves `open → closing → closed → (reopened →
closing → closed)*`. The period lock is not a gate checked once when
a transaction enters the system; it is re-checked **inside every
posting command**, so that a `closed` period cannot be written into
by any path that skips the original intake check
(`FINANCE_ACCOUNTING_PERIOD_CLOSED`, HI-10).

Reopening a `closed` period is a distinct command requiring distinct
authority from ordinary open/close — a dual-control action in which
the approving authority may not be the actor who requested the
reopening (`ORGANIZATION_DUAL_CONTROL_VIOLATION`, reused from
PACK-08). It requires a mandatory reason reference and produces a
create-once `PeriodReopeningRecord` that snapshots the closed state
before any further posting is allowed
(`FINANCE_PERIOD_REOPENING_NOT_AUTHORIZED` on any attempt that skips
this). Reopening a period whose report version has already reached
`submitted` is not covered by this workflow alone: it additionally
requires an explicit correction-or-restatement decision under the
`FinanceReport` lifecycle, because a submitted report has already
made a factual claim to a third party that a silent reopening would
undermine (ADR-047).

### Dates and timezones

`transaction_date`, `posting_date` and `value_date` are three
separate, explicit fields on `FinancialTransaction` and `JournalEntry`
respectively — never one field reused for three purposes. Every
period boundary and every deadline-relevant computation carries a
named IANA timezone; a naive datetime is refused wherever a period
boundary is computed (`FINANCE_ACCOUNTING_PERIOD_UNDETERMINED`,
HI-42).

### Provenance and replay

Every imported transaction requires an `ImportBatch` with a
`source_system_reference` and a content fingerprint over the batch
payload. Provenance fields — `transaction_date`, the classification
history's originating entry, and `import_batch_reference` — are
immutable once a transaction reaches `recorded`
(`FINANCE_IMPORT_PROVENANCE_MISSING` when absent, HI-40). Duplicate
detection runs at two levels: a per-row import fingerprint catches a
duplicate row inside or across batches
(`FINANCE_DUPLICATE_TRANSACTION`), and a batch-level fingerprint
catches a batch applied twice (`FINANCE_DUPLICATE_IMPORT`), both
reinforced by caller-supplied `event_id` idempotency through Audit
Core, the same mechanism CT-00-04 already establishes across the
repository (HI-41, HI-50).

### Reconciliation

`ReconciliationRecord` is create-once per reconciliation act: it is
never edited after creation, and a later reconciliation of the same
account and period produces a new record rather than revising the
old one. This preserves the history of what was believed reconciled
at each point in time, which a mutable "reconciliation status" field
on the account would destroy.

### Explicitly out of scope

This ADR does not specify, and PACK-10 does not implement: bank or
PSD2 integration, payment-provider integration, automated bank
transfers, or tax-filing integration. `ImportBatch`,
`PaymentAuthorization` and `SubmissionRecord` are the governed facts
such an integration would eventually feed; no pack owns the
integration itself yet (section 5, OD-16). Production persistence —
a real database, event bus and schema registry — is PACK-13's
responsibility; this round's `storage.py` is an in-memory reference
adapter only, with no delete method, following the same precedent
ADR-038 established for `compliance-service` (HI-47).

## Consequences

Easier: a balanced monetary position and a well-documented business
history can each be verified independently, against their own
narrow invariant, rather than against one aggregate trying to satisfy
both at once. An auditor can walk the ledger for correctness of
balance without wading through classification history, and can walk
the register for provenance without re-deriving it from posting
lines. Reclassifying a transaction's business meaning never requires
touching a posted entry, which keeps HI-6 intact by construction
rather than by discipline.

Harder: every write that has monetary effect now has two aggregates
to keep coherent instead of one, and the "incomplete state" case —
a transaction with monetary effect and no posted entry — is a state
the system must actively detect and fail closed on, rather than a
state that simply cannot occur. Reporting code must explicitly join
across both aggregates rather than reading one table; that join is
exactly what `ReportSnapshot` freezes (HI-25), so the cost is paid
once per report preparation rather than on every read.

## Security impact

This ADR is where PACK-10's central fail-closed guarantee for money
lives: an incomplete transaction-to-entry linkage is never reported
as a zero, an omission, or an implicit "not yet relevant" — it blocks
the report-affecting read that would have used it. Combined with
HI-6's structural absence of an edit path on posted entries and
HI-5's absence of a delete path anywhere, the two aggregates together
remove both privileged shortcuts a compromised or careless caller
would otherwise reach for: silently editing history, and silently
dropping an inconvenient fact. Balanced-posting enforcement at both
construction and posting time closes the gap where a draft could be
built balanced and mutated unbalanced before commit.

## Data impact

New aggregates introduced by this decision: `JournalEntry` (with
`PostingLine` as an inline value object), `FinancialTransaction`,
`ImportBatch`, `ReconciliationRecord`, `AccountingPeriod`, and
`PeriodReopeningRecord` as a create-once child of `AccountingPeriod`.
`FinanceAccount` is the scope each posting line references but is
specified in full detail elsewhere in section 8.2. `Money` and
`PostingLine` are value objects with no independent lifecycle. No
existing PACK-01 through PACK-09 entity is changed; PACK-10 consumes
PACK-08's `OrganizationalScope` and PACK-09's `RecordClassRef` and
`HoldRef` by typed reference only, never by reading those services'
stores directly (HI-47).

New events proposed for canon section 20.17:
`journal_entry.drafted`, `journal_entry.posted`,
`journal_entry.reversed`, `financial_transaction.recorded`,
`financial_transaction.classification_changed`,
`accounting_period.opened`, `accounting_period.closed`,
`accounting_period.reopening_requested`,
`accounting_period.reopened`, `import_batch.registered`,
`import_batch.completed`, `import_batch.rejected`,
`reconciliation.recorded`. No event payload carries an identity
value, a bank-account detail, or document content — only ids, enums,
timestamps, reason codes and policy version references, per HI-2.

## Migration impact

None. No pre-existing ledger, transaction register or accounting
period data exists in the baseline; this is new domain territory for
the repository. A future pack or implementation round that imports
historical ledger data must construct it through the same
`ImportBatch` provenance path this ADR specifies — there is no
separate bulk-load path that bypasses balancing or provenance
checks, because creating one would reopen exactly the gap this ADR
closes.

## Reversibility

The layered split is reversible toward a **simpler** shape at a
bounded cost: collapsing back to "ledger only" would mean dropping
the register's authority over provenance and re-hosting business-fact
metadata onto posting lines, which loses the cleanly separated
history this ADR is written to produce, but does not corrupt
existing data — every posted `JournalEntry` would still balance.

The reverse direction is not symmetric. Once a `FinanceReport`
version has been prepared, validated or submitted with figures
derived by joining the register to the ledger, moving to a
**"register only"** model — where the register itself carries
authoritative amounts and the ledger becomes a projection — is
**effectively irreversible**. Reports already cite posted entries by
id in their snapshots and consolidation records; retroactively
declaring those entries non-authoritative would invalidate every
citation a submitted or published report has already made, which
HI-26 forbids touching. This asymmetry is stated here plainly rather
than left implicit: choose option C expecting to live with it, not
expecting to trade down to option B later.

## Related canon version

Canon `0.7.0`. The canon amendment required for PACK-10 overall
(`docs/packs/PACK-10-CANON-AMENDMENT-PROPOSAL.md`, `0.7.0 → 0.8.0`)
covers the new event names this ADR's aggregates emit, under new
canon subsection 20.17, and the `finance_`/`FINANCE_` naming
convention that keeps this ADR's `Contribution` distinct from canon
13.2's deliberation `Contribution` (section 3, rule 3). This ADR
itself does not edit canon; it is authored against `0.7.0` as it
stands, and the amendment is tracked as a separate deliverable of
this round, not folded into this document.
