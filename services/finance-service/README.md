# Finance Service

PACK-10's one wholly new service (ADR-048). Sole authoritative owner of
the party-finance bounded context canon 0.8.0 section 19f defines: the
chart of accounts and accounting periods, the authoritative accounting
register, the transaction register with its provenance, contributions and
their governed exceptional states, sponsorship and external financial
benefit, the expense and reimbursement workflow, assets and obligations,
the reporting obligation, perimeter and frozen snapshot, the twelve-state
`Rechenschaftsbericht` lifecycle, the independent finance audit, and the
purpose-scoped `FinancePartyHandle`.

No other service reads or writes this service's storage directly
(`ФИН-44`, INV-03), and no other service imports this package
(`tests/repository/test_service_boundaries.py`).

## Module order

Each module imports only from those above it. The order is the
dependency order, and it is the order to read them in.

| Module          | Owns                                                                                                             |
| --------------- | ---------------------------------------------------------------------------------------------------------------- |
| `exceptions`    | One class per registered reason code. No domain knowledge.                                                       |
| `domain`        | `Money`, `FinancePartyHandle`, `OrganizationalScopeRef`, identity minimisation, pure invariant functions.        |
| `authorization` | Finance roles, action authorities, the canon 19f.14 incompatibility matrix, separation-of-duties assertions.     |
| `ledger`        | `FinanceAccount`, `AccountingPeriod`, `JournalEntry`, `FinancialTransaction`, correction and reversal.           |
| `records`       | Contributions, sponsorship, external benefit, expense claims, payments, assets, obligations, governed transfers. |
| `reporting`     | `ReportingObligation`, perimeter, `ReportSnapshot`, `FinanceReportVersion`, `AuditEngagement`.                   |
| `events`        | The seventy-two canon 20.17 event builders and the full-state payloads Audit Core hashes.                        |
| `references`    | Typed, content-free references to PACK-09, PACK-11 and PACK-35 records, and the refusals that keep them out.     |
| `storage`       | A `Protocol` port and an in-memory adapter per aggregate, the idempotency store and the event sink.              |
| `projections`   | Derived, versioned, never-authoritative read models and statistical disclosure control.                          |
| `application`   | Forty-two commands and five queries, each routed through one guard frame.                                        |

## The guard frame

Every command in `application` routes through one private frame, in this
order, so that no command can quietly skip a check:

1. **Scope, before anything else.** An undeterminable organizational
   scope refuses before any other check, read or write (`ФИН-04`).
2. **Authority.** Resolved through `assert_authorized` against an
   effective, scope-matching record. A role name is never proof
   (`ФИН-45`).
3. **Role compatibility and self-approval.** The canon 19f.14 matrix,
   plus the per-object comparisons a role table cannot express - creator
   against approver, claimant against reviewer, authorizer against
   executor (`ФИН-30`, `ФИН-31`).
4. **Conflict declaration.** An undeclared conflict fails closed
   (`ФИН-32`).
5. **Idempotency.** The caller supplies `event_id`; a replay with the
   same request digest returns the recorded aggregate, and a replay with
   different content raises `FINANCE_IDEMPOTENCY_CONFLICT`.
6. **Optimistic concurrency.** `expected_*_version` refuses on mismatch.

Then the domain transition, then the Audit Core append, then the event
publication. Audit before event, deliberately: an event that escaped
without an audit row would be unaccountable.

## What is deliberately absent

- **No delete method.** Not on a port, not on an adapter, not on an
  aggregate. `storage.delete_finance_record` and
  `reporting.delete_report_version` exist only to raise
  `GOVERNED_RECORD_DELETION_FORBIDDEN`: the honest API for an act the
  domain forbids is a reason-coded refusal, not a missing function
  (`ФИН-05`, `ФИН-22`).
- **No identity.** There is no `UserId`, `PersonId`, `MemberId`,
  `account_id`, credential, ballot or vote reference anywhere in this
  package, and `domain.PROHIBITED_IDENTITY_KEYS` refuses one arriving at
  any event or projection boundary (`ФИН-01`, `ФИН-02`, `ФИН-36`).
  `tests/test_privacy_boundary.py` enforces this by AST scan, not by
  convention.
- **No floating point.** `Money` is integer minor units with an explicit
  currency and scale; cross-currency arithmetic raises rather than
  netting silently (`ФИН-08`, `ФИН-09`).
- **No production data plane.** Every storage adapter is in-memory.
  Durable persistence and the production event plane are PACK-13's.
- **No frontend.** This round ships no operational finance UI.

## Reading the boundary

Legal cases, holds, retention classes and notice effects belong to
PACK-09; documents and evidence content belong to PACK-11; lobbying
contact disclosure belongs to PACK-35. This service holds each as an
opaque typed reference in `references.py` and never as an import
(`ФИН-21`, `ФИН-44`). Holding a reference to evidence does not make this
service the owner of the evidence, and no function here may assert that a
document is authentic, signed or admitted - only PACK-11 can
(`FINANCE_EVIDENCE_ASSERTION_UNAVAILABLE`).

## No claim of compliance or readiness

This service implements a governed workflow with auditability and
reason-coded refusals. Whether any accounting treatment, valuation,
aggregation rule, disclosure threshold, retention schedule or report
satisfies German party law, the Parteiengesetz, statutory accounting
rules or any authority's requirements remains a human legal and
accounting judgement made outside this system (`ФИН-43`).

See `docs/architecture/finance-service.md` for the bounded context,
`finance-ledger-model.md`, `finance-reporting-lifecycle.md`,
`finance-separation-of-duties.md` and `finance-publication-projection.md`
for the four subsystems, `docs/contracts/finance-command-query-contracts.md`
for the command and query surface, and `docs/packs/PACK-10-IMPLEMENTATION.md`
for what this round shipped and what it deferred.
