# Finance command and query contracts

The command and query surface of `services/finance-service`, as it
exists. Every entry below was read off
`epd2_finance_service.application`; nothing here is aspirational.

There is deliberately **no HTTP surface** this round: no
`contracts/openapi/pack-10.yaml`, no per-entity JSON Schema set, no
route. `PACK-10-IMPLEMENTATION-PLAN.md` phase 0 named all three; this
round shipped the domain, the command layer and the tests instead, and
publishing an OpenAPI document describing endpoints that do not exist
would make the contract suite assert against nothing runnable. The
contract that does exist is the Python signature plus the reason code
each refusal carries, and that is what this document records.

## How to read a command

Every command takes its stores as leading positional parameters and
everything else keyword-only, including `context: RequestContext`,
`port: AuthorizationPort` and `clock: Clock`. Every command returns a
frozen `*Result` carrying the new aggregate, the `EventEnvelope` that
was published and the `AuditEvent` that was appended. No command reads
system time: the injected `Clock` is the only time source, and
`tests/test_application.py` asserts it.

Every command routes through one guard frame, in a fixed order: scope
(`ФИН-04`, refused before any other check, read or write), authority
(`ФИН-45`, resolved against an effective scope-matching record, never
from a role name), role compatibility and per-object self-approval
(`ФИН-30`, `ФИН-31`), conflict declaration (`ФИН-32`, undeclared fails
closed), idempotency on the caller-supplied `event_id`, and
`expected_*_version` optimistic concurrency. Only then the domain
transition, then the audit append, then the event publication.

The **authority** column names the `ACTION_REQUIREMENTS` key the
command maps to through `_ACTION_FOR_COMMAND`; the **roles** column is
the role set that key permits. Where one key serves two commands, the
commands are distinguished by a per-object check the table cannot
express - `authorize_payment` and `settle_payment` hold different keys,
but `record_external_acknowledgement` and `record_external_acceptance`
share one and are separated by the authoritativeness of the reference
presented.

## Chart of accounts and accounting periods (canon 19f.4, 19f.5)

| Command                         | Authority                  | Permitted roles                                         |
| ------------------------------- | -------------------------- | ------------------------------------------------------- |
| `create_finance_account`        | `manage_chart_of_accounts` | `finance_administrator`                                 |
| `change_finance_account_status` | `manage_chart_of_accounts` | `finance_administrator`                                 |
| `open_accounting_period`        | `open_period`              | `finance_administrator`                                 |
| `close_accounting_period`       | `close_period`             | `finance_administrator`                                 |
| `request_period_reopening`      | `request_period_reopening` | `finance_administrator`                                 |
| `reopen_accounting_period`      | `approve_period_reopening` | `finance_administrator`, `organizational_administrator` |

## The authoritative register (canon 19f.4)

| Command                 | Authority             | Permitted roles         |
| ----------------------- | --------------------- | ----------------------- |
| `draft_journal_entry`   | `post_transaction`    | `finance_administrator` |
| `post_journal_entry`    | `post_transaction`    | `finance_administrator` |
| `reverse_journal_entry` | `reverse_transaction` | `finance_administrator` |
| `correct_journal_entry` | `correct_transaction` | `finance_administrator` |

## Transactions, provenance and import (canon 19f.6)

| Command                            | Authority                | Permitted roles         |
| ---------------------------------- | ------------------------ | ----------------------- |
| `record_financial_transaction`     | `post_transaction`       | `finance_administrator` |
| `reclassify_financial_transaction` | `reclassify_transaction` | `finance_administrator` |
| `register_import_batch`            | `register_import_batch`  | `finance_administrator` |

## Contributions, sponsorship and external benefit (canon 19f.7-19f.9)

| Command                             | Authority                 | Permitted roles         |
| ----------------------------------- | ------------------------- | ----------------------- |
| `record_contribution`               | `record_contribution`     | `finance_administrator` |
| `assess_contribution`               | `assess_contribution`     | `finance_administrator` |
| `decide_contribution`               | `accept_contribution`     | `finance_administrator` |
| `return_contribution`               | `return_contribution`     | `payment_executor`      |
| `register_sponsorship`              | `record_sponsorship`      | `finance_administrator` |
| `approve_sponsorship`               | `approve_sponsorship`     | `finance_administrator` |
| `record_external_financial_benefit` | `record_external_benefit` | `finance_administrator` |

## Expenses, payments and positions (canon 19f.10, 19f.11)

| Command                          | Authority            | Permitted roles                                         |
| -------------------------------- | -------------------- | ------------------------------------------------------- |
| `submit_expense_claim`           | `record_expense`     | `finance_administrator`                                 |
| `approve_expense_claim`          | `approve_expense`    | `finance_administrator`                                 |
| `authorize_payment`              | `authorize_payment`  | `payment_authorizer`                                    |
| `settle_payment`                 | `execute_payment`    | `payment_executor`                                      |
| `record_financial_obligation`    | `record_obligation`  | `finance_administrator`                                 |
| `write_off_financial_obligation` | `write_off_position` | `finance_administrator`, `organizational_administrator` |

## Reporting and the Rechenschaftsbericht lifecycle (canon 19f.16, 19f.17)

| Command                           | Authority                       | Permitted roles                                    |
| --------------------------------- | ------------------------------- | -------------------------------------------------- |
| `freeze_report_snapshot`          | `create_snapshot`               | `finance_administrator`                            |
| `prepare_report_version`          | `prepare_report`                | `finance_administrator`                            |
| `complete_internal_report_review` | `record_review`                 | `finance_administrator`, `report_signatory`        |
| `record_auditor_review`           | `record_auditor_review`         | `finance_administrator`, `report_signatory`        |
| `approve_report_version`          | `approve_report`                | `organizational_administrator`, `report_signatory` |
| `sign_report_version`             | `sign_report`                   | `report_signatory`                                 |
| `submit_report_version`           | `record_external_submission`    | `report_signatory`                                 |
| `record_external_acknowledgement` | `record_external_acceptance`    | `finance_administrator`, `report_signatory`        |
| `record_external_acceptance`      | `record_external_acceptance`    | `finance_administrator`, `report_signatory`        |
| `publish_report_version`          | `create_publication_projection` | `organizational_administrator`, `report_signatory` |
| `create_corrected_report_version` | `create_report_version`         | `finance_administrator`                            |

## Independent finance audit (canon 19f.18)

| Command                     | Authority              | Permitted roles                                         |
| --------------------------- | ---------------------- | ------------------------------------------------------- |
| `open_audit_engagement`     | `request_audit`        | `finance_administrator`, `organizational_administrator` |
| `record_audit_finding`      | `record_audit_opinion` | `finance_auditor`                                       |
| `conclude_audit_engagement` | `record_audit_opinion` | `finance_auditor`                                       |

## The purpose-scoped party reference (canon 19f.15)

| Command                | Authority           | Permitted roles         |
| ---------------------- | ------------------- | ----------------------- |
| `mint_party_handle`    | `mint_party_handle` | `finance_administrator` |
| `resolve_party_handle` | _not in the table_  | _see below_             |

### Why `resolve_party_handle` is not in `ACTION_REQUIREMENTS`

Canon 19f.15 requires a separate, explicitly granted authority to
resolve a `FinancePartyHandle` back to a party. Modelling it as one
more `FinanceRole` would make it grantable alongside the others, so it
is a bare role code, `authorization.PARTY_HANDLE_RESOLUTION_ROLE_CODE`,
which `resolve_finance_role` deliberately returns `None` for. The command
resolves it through the port directly and refuses everything else with
`FINANCE_PARTY_HANDLE_RESOLUTION_DENIED`. The resolution act is audited
even when it succeeds, and the resolved value never enters the event
payload, the audit row or the return value.

## Queries

The five queries are scope-filtered reads that return `projections.*`
objects, never aggregates. They take no action authority: a read is
gated by scope alone, and a foreign-scope read answers
`VALIDATION_RECORD_NOT_FOUND` - the same class and message shape as a
nonexistent record, so a foreign identifier discloses nothing.

This is weaker than the command surface and is stated rather than
hidden: canon 19f.21 governs what a public projection may contain,
which the projection builders enforce, but it does not by itself
require an action authority for an in-scope internal read. A round that
adds an external read API will need one.

| Query                             | Returns                  |
| --------------------------------- | ------------------------ |
| `get_account_balance_projection`  | `projections` read model |
| `get_period_summary`              | `projections` read model |
| `list_contribution_disclosures`   | `projections` read model |
| `get_published_report_projection` | `projections` read model |
| `get_audit_conclusion_projection` | `projections` read model |

## Refusal contract

Every refusal in this surface carries a reason code registered in
`contracts/reason-codes/pack-10.yml`, and one exception class exists
per code in `epd2_finance_service.exceptions`. There is no free-text
refusal anywhere in the service (`ФИН-40`).

`tests/test_application.py` proves this twice: a table of
`(callable, expected_code)` pairs asserting the exact code each named
refusal raises, and a walk over the whole `FinanceError` subclass tree
asserting that every class's `reason_code` is registered - including
codes no command currently raises, so a future command cannot
introduce an unregistered one by reusing an existing class.
