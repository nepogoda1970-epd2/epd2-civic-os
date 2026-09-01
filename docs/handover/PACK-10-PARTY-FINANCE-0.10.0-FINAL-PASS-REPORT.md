# PACK-10 Party Finance 0.10.0 — Final PASS Report

Status: **PACK-10 PARTY FINANCE 0.10.0 — FINAL PASS.**

This is a packaging round. No implementation was rebuilt, no
finance-service code was changed, no test was changed, no frontend file,
route, visual snapshot or ADR was touched, and neither the repository nor
the canon version moved. The archive is the accepted candidate plus this
one report.

The PASS status rests on an external GitHub Actions run, not on anything
this environment could execute. Section 8 states exactly which checks
were re-run locally and which are accepted from that run; the two lists
do not overlap in the places that matter, and nothing network-dependent
is claimed as locally verified.

## 1. Inputs

| Artifact                                            | SHA-256                                                            |
| --------------------------------------------------- | ------------------------------------------------------------------ |
| `EPD2_PACK-10_PARTY_FINANCE_0.10.0_CANDIDATE.zip`   | `3cd5733717fc252a94883defc2c9b41198ab0b5181e0926e587ca52829692e15` |
| `epd2-civic-os-verification-result(12).zip` (outer) | `94ca14d5ba3b9ebfe0b0667c86690c72059c96f84227cf2a5432294aa90c63c1` |
| `epd2-civic-os-verification-result.zip` (inner)     | `868b6d61b6f26cc991264b5968088d9e3d1b7cec37c78eb4792032a0be97832f` |

The candidate archive was extracted to a clean directory and is the
staged tree for this package, unmodified apart from the addition of this
report. A recursive byte comparison confirmed the extracted tree is
identical to the tree that produced the candidate hash above.

## 2. Versions and status

| Value                                   | Setting                    | Declared in                                                                                           |
| --------------------------------------- | -------------------------- | ----------------------------------------------------------------------------------------------------- |
| `REPOSITORY_VERSION`                    | `0.10.0`                   | `packages/python/epd2-core/src/epd2_core/version.py`, `packages/typescript/epd2-types/src/version.ts` |
| `CANON_VERSION`                         | `0.8.0`                    | the same two files and `docs/canonical/canon-version.json`                                            |
| `finance_context_implementation_status` | `reference_implementation` | `docs/canonical/canon-version.json`                                                                   |
| `repository_compatibility`              | `>=0.1.0 <0.11.0`          | `docs/canonical/canon-version.json`                                                                   |
| `minimum_repository_version`            | `0.9.0`                    | `docs/canonical/canon-version.json`                                                                   |

`reference_implementation` is the truthful value and was chosen over both
neighbours. `not_implemented` stopped being true when
`services/finance-service` shipped; `implemented` would assert a
production data plane — durable storage, an event bus, a bank
integration — that this round does not have. `minimum_repository_version`
stays at `0.9.0` because it records the repository version the canon
0.8.0 amendment was made at, and that does not move forward with each
round that implements it.

## 3. Implementation scope

`services/finance-service` is the sole authoritative owner of the
party-finance bounded context defined by canon 0.8.0 section 19f: the
chart of accounts and accounting periods, the authoritative
double-entry register, the transaction register with its provenance,
contributions and their governed exceptional states, sponsorship and
external financial benefit, the expense and reimbursement workflow with
authorisation separated from execution, assets and obligations, the
reporting obligation, perimeter and frozen snapshot, the twelve-state
`Rechenschaftsbericht` lifecycle, the independent finance audit, and the
purpose-scoped `FinancePartyHandle`.

### 3.1 Domain modules

Twelve modules, 20,355 lines. Each imports only from those above it.

| Module          | Lines | Owns                                                                                                             |
| --------------- | ----: | ---------------------------------------------------------------------------------------------------------------- |
| `__init__`      |    64 | The package charter, the boundary statement and the no-compliance-claim statement.                               |
| `exceptions`    |   512 | 64 classes: one per registered reason code, plus one deliberately non-reason-coded technical error.              |
| `domain`        |   569 | `Money`, `FinancePartyHandle`, `OrganizationalScopeRef`, identity minimisation, pure invariant functions.        |
| `authorization` |   695 | Six roles, four action-level authorities, the 19f.14 incompatibility matrix, forty governed actions.             |
| `references`    |   705 | Typed, content-free references to PACK-08/09/11/35 records, and the refusals that keep foreign concepts out.     |
| `projections`   |  1032 | Derived, versioned, never-authoritative read models and statistical disclosure control.                          |
| `ledger`        |  1251 | Accounts, accounting periods, balanced postings, correction and reversal, the acyclic correction chain.          |
| `records`       |  1512 | Contributions, sponsorship, external benefit, expense claims, payments, assets, obligations, governed transfers. |
| `reporting`     |  1695 | Reporting obligation, perimeter, frozen snapshot, the twelve-state report lifecycle, the audit engagement.       |
| `storage`       |  1719 | 24 ports, 24 in-memory adapters, the idempotency store and the event sink. No delete method.                     |
| `events`        |  4438 | All 72 canon 20.17 event builders and the full-state payloads Audit Core hashes.                                 |
| `application`   |  6163 | 42 commands and 5 queries, 19 result dataclasses, one shared guard frame.                                        |

Tests: eleven files, 9,699 lines, 388 test functions, 677 collected
cases.

### 3.2 Commands and queries

Forty-two commands, each returning a frozen result carrying the new
aggregate, the published `EventEnvelope` and the appended `AuditEvent`:

- **Accounts and periods (6)** — `create_finance_account`,
  `change_finance_account_status`, `open_accounting_period`,
  `close_accounting_period`, `request_period_reopening`,
  `reopen_accounting_period`.
- **The register (4)** — `draft_journal_entry`, `post_journal_entry`,
  `reverse_journal_entry`, `correct_journal_entry`.
- **Transactions and provenance (3)** — `record_financial_transaction`,
  `reclassify_financial_transaction`, `register_import_batch`.
- **Contributions, sponsorship, external benefit (7)** —
  `record_contribution`, `assess_contribution`, `decide_contribution`,
  `return_contribution`, `register_sponsorship`, `approve_sponsorship`,
  `record_external_financial_benefit`.
- **Expenses, payments, positions (6)** — `submit_expense_claim`,
  `approve_expense_claim`, `authorize_payment`, `settle_payment`,
  `record_financial_obligation`, `write_off_financial_obligation`.
- **Reporting (11)** — `freeze_report_snapshot`,
  `prepare_report_version`, `complete_internal_report_review`,
  `record_auditor_review`, `approve_report_version`,
  `sign_report_version`, `submit_report_version`,
  `record_external_acknowledgement`, `record_external_acceptance`,
  `publish_report_version`, `create_corrected_report_version`.
- **Audit (3)** — `open_audit_engagement`, `record_audit_finding`,
  `conclude_audit_engagement`.
- **Party reference (2)** — `mint_party_handle`, `resolve_party_handle`.

Five queries, all scope-filtered and all returning projections rather
than aggregates: `get_account_balance_projection`, `get_period_summary`,
`list_contribution_disclosures`, `get_published_report_projection`,
`get_audit_conclusion_projection`. They take no action authority — a
read is gated by scope alone, and a foreign-scope read answers
`VALIDATION_RECORD_NOT_FOUND`, the same class and message shape as a
nonexistent record, so a foreign identifier discloses nothing.

Every command routes through one guard frame, in a fixed order: scope
first and before any other check, read or write (`ФИН-04`); authority
resolved against an effective, scope-matching record, never from a role
name (`ФИН-45`); role compatibility and per-object self-approval
(`ФИН-30`, `ФИН-31`); conflict declaration, undeclared failing closed
(`ФИН-32`); idempotency on the caller-supplied `event_id`; and
`expected_*_version` optimistic concurrency. Then the domain transition,
then the audit append, then the event publication — audit before event,
so nothing escapes unaccounted for. No command reads system time; the
injected `Clock` is the only source, and the suite asserts it.

### 3.3 Events

All **72** canon section 20.17 event types are implemented, each with a
named builder routing through one chokepoint that rejects an unknown
type, requires a timezone-explicit instant, attaches the mandatory safe
metadata (aggregate identifier, organizational scope, scope kind) and
runs the prohibited-identity-key rejection over the final payload before
the envelope is built. Every event enters at major version 1 under the
canon section 21 envelope.

Payloads are minimal by construction: no name, address, bank detail,
payment identifier, identity document, evidence content, document bytes,
voting information, credential value or secret. Contributors appear only
as the opaque `fph:` handle reference, and
`finance_party_handle.resolved` carries no resolved value — the canon
states that exclusion explicitly and the builder enforces it.

`PUBLIC_PROJECTION_ALLOWED` records which of the 72 may appear in a
public projection at all, following canon 20.17's six-group breakdown.
Individual ledger, account, period, provenance, `expense_claim.*` and
`payment.*` events are excluded, as are `finance_report.snapshot_frozen`,
`finance_report.validation_finding_recorded` and
`finance_report.correction_requested`.

Twenty-six of the 72 builders have no command in this round; they are
enumerated by name in `docs/packs/PACK-10-IMPLEMENTATION.md`.

### 3.4 Ports and adapters

**24 storage ports** (`typing.Protocol`) with **24 in-memory reference
adapters**, plus `IdempotencyRecord`/`CommandIdempotencyStore`, the
event sink, and `ImportBatchRecord` as an infrastructure record of an
ingestion act.

No port, adapter or aggregate exposes a delete-shaped method. The two
functions carrying a delete-shaped name —
`storage.delete_finance_record` and `reporting.delete_report_version` —
exist only to raise `GOVERNED_RECORD_DELETION_FORBIDDEN`, because the
honest API for an act the domain forbids is a reason-coded refusal, not
a missing function (`ФИН-05`, `ФИН-22`). This is enforced three ways: by
the service's own `tests/test_storage.py`, by
`tests/repository/test_service_boundaries.py`'s AST scan of
`storage.py`, and by `scripts/check_canon_0_8_0.py` check 5, which scans
every module in the package for a delete-shaped definition and permits
exactly those two names.

Every adapter is in-memory. There is no durable persistence in this
round; the production data plane is PACK-13's.

### 3.5 Reason-code coverage

`contracts/reason-codes/pack-10.yml` — **96 entries**, each carrying all
seven mandatory fields:

| Source            | Count | What it is                                                                        |
| ----------------- | ----: | --------------------------------------------------------------------------------- |
| `canon-0.8.0`     |    45 | The `FINANCE_*` codes canon section 24 introduced with the 0.8.0 amendment.       |
| `pack-10-service` |    19 | Additive: 4 refusals canon has no code for, 15 audit classifications for success. |
| `pack-02-reused`  |    10 | Generic validation, concurrency, audit and service-state codes.                   |
| `pack-08-reused`  |    10 | Organizational scope and authority codes.                                         |
| `pack-09-reused`  |     5 | Retention, legal hold, governed deletion, cross-scope authority.                  |
| `pack-07-reused`  |     5 | Conflict of interest, self-approval, critical-policy codes.                       |
| `pack-04-reused`  |     2 | Publication and disclosure-policy codes.                                          |

Codes are reused verbatim rather than shadowed: retention and legal hold
remain PACK-09's domain, scope and authority remain PACK-08's, and a
`FINANCE_`-prefixed duplicate of either would create two codes for one
fact. Four existing families that look applicable are deliberately not
reused — pack-03's `CONTRIBUTION_*` (a deliberation utterance), pack-04's
`LEDGER_ENTRY_*` (a public transparency ledger entry), pack-02's
`ACCOUNT_*` (a platform user account) and pack-02/04's `AUDIT_*`
(audit-log integrity).

`exceptions.py` holds **64 classes**: one per registered code, plus one
deliberately non-reason-coded `FinanceTechnicalError`. No free-text
refusal exists anywhere in the service (`ФИН-40`).
`tests/contract/test_reason_codes_registry.py` proves every reason-code
literal in the service is registered; the service's own
`test_application.py` proves it twice more — a table of
`(callable, expected_code)` pairs, and a walk over the whole
`FinanceError` subclass tree so codes no command currently raises are
still checked against the YAML.

### 3.6 Authorization and separation of duties

Six institutional roles: `finance_administrator`, `payment_authorizer`,
`payment_executor`, `report_signatory`, `finance_auditor`, and the
pre-existing `organizational_administrator` that the matrix makes
incompatible with the first.

Four action-level authorities recorded on the act itself and
deliberately never granted as roles: `transaction_creator`,
`transaction_reviewer`, `report_preparer`, `report_approver`. That
distinction is what keeps the privileged surface at four new
institutional roles rather than nine.

**Forty governed actions** in `ACTION_REQUIREMENTS`, a closed mapping:
an action absent from it has no permitted role and therefore denies, so
adding a command without deciding who may run it fails closed. Nine
entries were added during the implementation round's own review, so that
no command borrows a neighbouring action's authority — notably
`register_import_batch` (canon 19f.6 separates ingestion from posting),
`write_off_position` (recording a debt and erasing it are not one
privilege), `sign_report` (`report_signatory` alone; nobody signs a
statutory report on the strength of an administrative role) and
`record_auditor_review` (which excludes `finance_auditor`, because canon
19f.18 forbids the audit contour writing into an aggregate it audits).

**Six hard incompatibility pairs** implement canon 19f.14's matrix:
`finance_auditor` against each of `finance_administrator`,
`payment_authorizer`, `payment_executor` and `report_signatory`;
`payment_authorizer` against `payment_executor`; and
`finance_administrator` against `organizational_administrator` in one
legally relevant scope — the adopted owner decision of 19f.14.

The rows a role table cannot express are checked per object instead:
creator against approver of the same object; a claimant against anyone
reviewing, approving, authorising or executing their own claim; the
payment authorizer against the executor of the same payment; the
approver against the signatory of the same report version; and the
auditor against every actor read off that version's own append-only
history. Conflict declaration is required for every command, not only
for canon's "protected actions" — stricter, never softer — and an
undeclared state fails closed.

Party-handle resolution requires a separate authority that is
deliberately **not** a `FinanceRole` and deliberately absent from
`ACTION_REQUIREMENTS`, so that no finance grant can reach it. The
resolution act is audited even when it succeeds, and the resolved value
never enters the payload, the audit row or the return value.

### 3.7 Reporting and the Rechenschaftsbericht lifecycle

The **twelve canonical states** of canon 19f.17, in the canon's own
names and in its order: `draft`, `internally_reviewed`,
`auditor_reviewed`, `approved`, `signed`, `submitted`,
`externally_acknowledged`, `externally_accepted`, `published`,
`amended`, `restated`, `superseded`.

The implementation round's brief used a longer operational vocabulary
while also instructing that the exact canonical names be used where the
canon already defines them. The canon defines all twelve, so the canon's
names are authoritative and the brief's vocabulary is preserved as a
documented translation in `reporting.OPERATIONAL_STATE_SYNONYMS` —
including the two entries that map to no state at all, because
`audit_requested` opens a separate aggregate with its own lifecycle and
a correction request is a record on the version rather than a status of
it.

The transition graph is derived from the canon's order rather than typed
out, so it cannot drift from it, with three documented additions: every
state may reach `superseded`; `submitted` may reach
`externally_accepted` directly, because acknowledgement is not implied
by submission and an acceptance decision arriving without one must not
be unreachable; and `amended`/`restated` are correction entry states
whose only forward edge is `internally_reviewed`, so a corrected version
walks the lifecycle again rather than resuming with decisions given for
different figures.

The rules the lifecycle refuses on:

- A version binds exactly one frozen snapshot for its whole life; a
  different snapshot raises, and no method rebinds it (`ФИН-24`).
- Submission is not acknowledgement and acknowledgement is not
  acceptance (`ФИН-26`). An acknowledgement, receipt, delivery record or
  read status offered as acceptance raises
  `FINANCE_EXTERNAL_ACKNOWLEDGEMENT_NOT_AUTHORITATIVE`; all four are
  legitimate, storable facts and none is a legal act (`ФИН-27`).
- Acceptance is never inferred. No reference raises
  `FINANCE_EXTERNAL_ACCEPTANCE_MISSING`, and
  `assert_no_inferred_acceptance` answers the question the system will
  eventually be asked — "the authority has not replied in six weeks, may
  we treat it as accepted?" — with no, whatever the clock says.
- Publication is authorised separately: approval is not publication and
  publication is not approval (`ФИН-28`). Three independent facts are
  required, each refusing on its own.
- A correction never overwrites. It produces an `amended` or `restated`
  successor carrying a typed backward reference, and the predecessor
  becomes `superseded` and stays readable forever (`ФИН-05`, `ФИН-25`).
- Submitted, acknowledged, accepted, published and superseded versions
  are field-immutable; the single edit path refuses in those states by
  construction rather than by a per-field check.
- Auditor review requires a concluded engagement for the same scope and
  period, and independence is re-verified at the moment of the act
  against the actor set read off that version's own history, not
  assumed from a role grant (`ФИН-29`, `ФИН-30`).

## 4. Files added, changed and removed by this packaging round

Relative to `EPD2_PACK-10_PARTY_FINANCE_0.10.0_CANDIDATE.zip`:

| Change  | Count | Paths                                                             |
| ------- | ----: | ----------------------------------------------------------------- |
| Added   |     1 | `docs/handover/PACK-10-PARTY-FINANCE-0.10.0-FINAL-PASS-REPORT.md` |
| Changed |     0 | —                                                                 |
| Removed |     0 | —                                                                 |

Verified by recursive byte comparison of the extracted candidate archive
against the staged tree before packaging: 764 files identical, this
report the only addition, giving 765.

Relative to the previous cumulative baseline
`EPD2_FRONT-01_PACK-10_CANON_0.8.0_FINAL_PASS.zip` (730 files), the
implementation round's own manifest — 34 added, 16 modified, 0 removed —
is in `docs/handover/PACK-10-IMPLEMENTATION-REPORT.md` section 2 and is
not restated here.

## 5. FRONT-00 and FRONT-01 remain intact

Confirmed by recursive byte comparison of the staged tree against the
extracted FRONT-01 + PACK-10 Canon 0.8.0 FINAL PASS baseline:

- The whole of `frontend/` is byte-identical. No route, page, component,
  style, test, config or fixture changed.
- **All 45 committed visual snapshots are present and byte-identical** —
  15 under `front00.browser.spec.ts-snapshots`, 30 under
  `front01.browser.spec.ts-snapshots`.
- `package-lock.json` and `frontend/web-shell/package.json` are
  byte-identical. No dependency was added, removed, upgraded or
  downgraded.
- `docs/frontend/` is unchanged.
- `docs/adr/` is unchanged: 54 ADR files, ADR-044 through ADR-054
  included, with **zero duplicate ADR ids** (verified by extracting and
  sorting every filename id).
- `docs/canonical/TZ-00-domain-event-canon.md` is byte-identical to the
  0.8.0 text. This round amends no canon.

The external CI run confirms the same from the other direction: 108
Playwright browser, accessibility and visual tests passed, which
includes every one of the 45 snapshot comparisons.

## 6. What was not added

No production database or durable persistence — every storage adapter is
in-memory and the production data plane is PACK-13's. No event bus or
message broker; the event sink is an in-process port. No banking,
payment-provider or payment-rail integration of any kind. No
external-authority submission channel; a submission is a reference to
an act performed elsewhere. No operational finance user interface, and
no finance-named path anywhere under `frontend/` — enforced by
`scripts/check_canon_0_8_0.py` check 5, not merely intended. No shared
finance package under `packages/`. No second finance-named service.

No claim of legal compliance, authority acceptance or operational
readiness follows from any of this (`ФИН-43`). Whether any accounting
treatment, valuation, aggregation rule, disclosure threshold, retention
schedule or report satisfies German party law, the Parteiengesetz,
statutory accounting rules or any authority's requirements remains a
human legal and accounting judgement made outside this system.

## 7. Correspondence between the CI run and this archive

The CI artifact's root-level tree is the workspace GitHub Actions
verified. It was compared file-by-file against the staged tree by
SHA-256, excluding build caches:

- **762 of 764 files are byte-identical.**
- Two differ, both from CI-side normalisation, neither from any change
  in this round:
  - `docs/frontend/FRONT-00-PAGE-INVENTORY.csv` — the staged copy has
    CRLF line endings, the CI checkout has LF. The two are identical
    after newline normalisation, and the staged copy is byte-identical
    to the FRONT-01 FINAL PASS baseline that CI has accepted before.
  - `package-lock.json` — the CI copy has one extra line, `"dev": true,`
    on a transitive `fsevents` entry, added by npm during install. The
    staged copy is byte-identical to the FRONT-01 FINAL PASS baseline.
- One file is in the archive but not in the CI checkout:
  `docs/handover/PACK-09-EXTERNAL-CI-VERIFICATION.log`. It matches
  `*.log` in `.gitignore`, so git never tracked it and CI never checked
  it out. It is a PACK-09 baseline artefact carried forward; no checker
  requires it.

**One observation the archive does not contain, reported because it
affects the integrating checkout rather than this package.** The CI
workspace contains an untracked directory `epd2-civic-os/` holding 399
stale files at `REPOSITORY_VERSION`/`CANON_VERSION` `0.6.0`, with no
`finance-service` and only 32 ADRs. It is not in git, not in this
archive, and did not affect the verification — every command in
`VERIFICATION.log` ran at the repository root against the real tree, and
`check_forbidden_files.py` passed because the directory is untracked.
It is worth deleting from the working copy: a stale 0.6.0 tree sitting
inside a 0.10.0 checkout is exactly the kind of thing that produces a
confusing diff in a later round.

## 8. Checks re-run locally in this environment

Every command below was executed against the staged tree and its real
result is reported.

```text
$ python3 scripts/check_repository.py
OK: all 619 required paths are present.

$ python3 scripts/check_forbidden_files.py
OK: no forbidden paths found.

$ python3 scripts/verify_versions.py
OK: all version sources are consistent.

$ python3 scripts/check_canon_0_8_0.py
OK: all 17 canon 0.8.0 amendment checks passed.

$ ruff check .
All checks passed!

$ ruff format --check .
242 files already formatted

$ mypy services/finance-service          # mypy 1.20.2
Success: no issues found in 23 source files

$ pytest -q                              # pytest 9.0.3
3354 passed, 5 skipped
```

Structural checks, also executed here: `finance-service` imports cleanly
module by module; 72 event types; 40 governed actions; 6 incompatibility
pairs; 6 roles and 4 action authorities; 12 report states with the canon
names; 24 ports and 24 in-memory adapters; 47 public application
functions; 96 registry entries with no duplicate code and all seven
mandatory fields; 45 PNG snapshots; 54 ADR files with zero duplicate ids;
0 nested ZIP files; `.github`, `.gitignore`, `.editorconfig`,
`.prettierignore`, `.pre-commit-config.yaml` and 6 `.gitkeep` files all
present; `uv.lock` and `package-lock.json` present.

The local `pytest` count (3354 passed, 5 skipped) differs from CI's
(3361 passed, 4 skipped) for one reason: `hypothesis` cannot be installed
in this sandbox, so `tests/contract/test_property_based.py` skips here
and runs in CI. 3354 + 7 = 3361 and 5 − 1 = 4. The two runs are the same
suite.

## 9. Checks accepted from external CI

Accepted from the supplied GitHub Actions artifact, **not** re-run here:

| Check                                                  | Result                        |
| ------------------------------------------------------ | ----------------------------- |
| `check_repository.py`                                  | 619 required paths present    |
| `check_forbidden_files.py`                             | PASS                          |
| `verify_versions.py`                                   | PASS                          |
| `ruff format --check` / `ruff check`                   | PASS                          |
| Prettier (`npm run format:check`, pinned 3.9.6)        | PASS                          |
| ESLint (`npm run lint --workspace=frontend/web-shell`) | PASS                          |
| `mypy`, all 18 service groups including finance        | PASS, finance 23 source files |
| TypeScript typecheck, both workspaces                  | PASS                          |
| `uv run pytest`                                        | 3361 passed, 4 skipped        |
| Frontend component tests (Vitest)                      | 16 passed, 2 files            |
| Next.js production build                               | PASS, compiled in 5.6s        |
| Playwright browser, accessibility and visual suites    | 108 passed                    |
| Committed visual snapshots                             | all 45 passed                 |

The npm-dependent half of that table — Prettier at the pinned 3.9.6,
ESLint, TypeScript, the Vitest component tests, the Next.js build and
the entire Playwright suite — **cannot** run in this environment, which
has no npm-registry and no PyPI access. None of it is claimed as
independently re-run. It is accepted on the evidence of the artifact,
and the correspondence between that artifact's tree and this archive is
established in section 7.

The one local check that is weaker than CI's is Prettier: only 3.8.1 is
installed here against the pinned 3.9.6. The pinned version is what
passed in CI, so its verdict is the one that counts; the local binary
disagrees on exactly one pre-existing file
(`docs/adr/ADR-051-...md`, over `no*` versus `no\*` in a table cell),
which is byte-identical to the baseline CI has accepted twice and was
deliberately left alone rather than rewritten to satisfy the older
binary.

## 10. Packaging integrity

Archive root is the repository root. Excluded: `.git`, `.venv`,
`node_modules`, `.next`, `__pycache__`, `*.pyc`, `.pytest_cache`,
`.mypy_cache`, `.ruff_cache`, `.hypothesis`, coverage output,
`test-results`, Playwright reports, `tsconfig.tsbuildinfo`, all nested
ZIP files, and the external verification artifact itself.

Preserved: `.github` (workflows, issue templates, pull-request
template), `.gitignore`, `.editorconfig`, `.prettierignore`,
`.pre-commit-config.yaml`, all six required `.gitkeep` files, every
source and test file, every handover report, all 54 ADRs, all 45
committed PNG snapshots, both package manifests, `package-lock.json` and
`uv.lock`.

The archive was verified by extracting it to a clean directory and
running a recursive byte comparison against the staged tree — zero
differences — and then re-running `check_repository.py`,
`check_forbidden_files.py`, `verify_versions.py` and
`check_canon_0_8_0.py` against the extracted copy, so the checks answer
for what was actually shipped rather than for what was staged.

## 11. Archive identity

The output archive's own SHA-256 cannot appear inside it: writing the
hash into a file the hash covers changes the hash. It is reported in the
delivery message accompanying this archive, computed after packaging,
and it is the value to check the download against. The two input hashes
are in section 1.

## 12. Status

**PACK-10 PARTY FINANCE 0.10.0 — FINAL PASS.**

This status applies to this package and to nothing after it. Any later
package is a candidate until an external CI run says otherwise.
