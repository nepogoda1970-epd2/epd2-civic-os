# CLAUDE-PACK-10 — Canon 0.8.0 compatibility and registry diff

This document records exactly what canon `0.8.0` changes relative to
`0.7.0`, what stays compatible, and what a consumer currently at
`REPOSITORY_VERSION = 0.9.0` must and must not assume as a result.
It is a compatibility and registry-diff reference, not a new
specification: the normative text is
`docs/canonical/TZ-00-domain-event-canon.md` section `19f` and the
governing determination is
`docs/packs/PACK-10-CANON-AMENDMENT-ASSESSMENT.md`. Every count below
was verified directly against the repository files named in each
section, not copied from prose elsewhere.

## 1. Version state

| Item                                                                      | Before (`0.7.0`)        | After (`0.8.0`)         | Changed                 |
| ------------------------------------------------------------------------- | ----------------------- | ----------------------- | ----------------------- |
| `CANON_VERSION`                                                           | `0.7.0`                 | `0.8.0`                 | Yes                     |
| `REPOSITORY_VERSION`                                                      | `0.9.0`                 | `0.9.0`                 | No                      |
| `canon-version.json` `canon_version`                                      | `0.7.0`                 | `0.8.0`                 | Yes                     |
| `canon-version.json` `status`                                             | `working-canon`         | `working-canon`         | No                      |
| `canon-version.json` `repository_compatibility`                           | `>=0.1.0 <0.10.0`       | `>=0.1.0 <0.10.0`       | No                      |
| `canon-version.json` `minimum_repository_version`                         | absent                  | `0.9.0`                 | Yes (new key)           |
| `canon-version.json` `amended_at_repository_version`                      | absent                  | `0.9.0`                 | Yes (new key)           |
| `canon-version.json` `finance_context_implementation_status`              | absent                  | `not_implemented`       | Yes (new key)           |
| `epd2_core.version.CANON_VERSION` (Python)                                | `0.7.0`                 | `0.8.0`                 | Yes                     |
| `epd2_core.version.REPOSITORY_VERSION` (Python)                           | `0.9.0`                 | `0.9.0`                 | No                      |
| `epd2-types` `version.ts` `CANON_VERSION` (TypeScript)                    | `0.7.0`                 | `0.8.0`                 | Yes                     |
| `epd2-types` `version.ts` `REPOSITORY_VERSION` (TypeScript)               | `0.9.0`                 | `0.9.0`                 | No                      |
| `packages/python/epd2-core/tests/test_version.py` skeleton assertion      | asserts `0.7.0`/`0.9.0` | asserts `0.8.0`/`0.9.0` | Yes (test text updated) |
| `packages/typescript/epd2-types/tests/version.test.ts` skeleton assertion | asserts `0.7.0`/`0.9.0` | asserts `0.8.0`/`0.9.0` | Yes (test text updated) |
| `CHANGELOG.md` latest released heading                                    | `## [0.9.0]`            | `## [0.9.0]`            | No                      |

`CHANGELOG.md` gains exactly one new entry, `## [Unreleased] - canon
minor version 0.8.0 (Party Finance & Financial Accountability
Context)`, placed above the pre-existing
`## [Unreleased] - PACK-10 specification candidate (documentation
only)` entry, which is itself left untouched. No **released** heading
is added or changed: `## [0.9.0]` remains the newest released entry
because this round released nothing — it is documentation and canon
text only.

`repository_compatibility` stays `>=0.1.0 <0.10.0` on purpose. A
repository at `0.9.0` is inside that range and can consume canon
`0.8.0` without any repository-side change. Widening the range now to
admit a future `0.10.0` would pre-authorize a PACK-10
**implementation** round — moving `REPOSITORY_VERSION` to `0.10.0` —
that has not happened and is not authorized by this canon-only round
alone (`19f.25`). The range is therefore deliberately left untouched,
and the ordering/widening question stays open as `OD-20` (section 9).

## 2. Backward compatibility

The amendment is purely additive. Item by item:

- No existing canonical entity, field, status, or owner assignment in
  sections `5` through `19e` was changed, renamed, removed or
  repurposed. `diff -rq` between the `0.7.0` and `0.8.0` trees shows
  twelve changed files — `docs/canonical/TZ-00-domain-event-canon.md`,
  `docs/canonical/canon-version.json`, the two version-constant files,
  their two version tests, `docs/canonical/README.md`,
  `docs/adr/README.md`, `docs/architecture/data-ownership.md`,
  `docs/architecture/service-boundaries.md`, `README.md` and
  `CHANGELOG.md` — and six new files: one ADR
  (`docs/adr/ADR-050-canon-0.8.0-party-finance-context-additions.md`),
  this document,
  `docs/packs/PACK-10-CANON-0.8.0-ACCEPTANCE-MATRIX.md`,
  `docs/handover/PACK-10-CANON-0.8.0-REPORT.md`, one new script
  (`scripts/check_canon_0_8_0.py`) and one new test
  (`tests/repository/test_canon_0_8_0_amendment.py`). Nothing under
  `services/`, `contracts/` or `frontend/` is touched at all, and
  nothing under `packages/` beyond the two version constants and
  their two tests.
- No existing event name in section `20.1` through `20.16` was
  renamed, removed, or reassigned a different owner or version. New
  section `20.17` adds seventy-two events, all owned by
  `finance-service`, with no aggregate name reused from an earlier
  section.
- No existing reason code in section `24` was renamed, redefined or
  reassigned. Thirty-two existing codes are reused verbatim by the
  finance context (section 3.2); forty-five new `FINANCE_`-prefixed
  codes are added (section 3.1); zero collisions were found (section
  24's own text: "конфликтов не обнаружено").
- No existing forbidden link in section `23` was weakened, narrowed or
  removed. Twenty-five entries are added (section 7), all pointing
  **into** finance boundaries, none pointing **out of** an existing
  boundary into finance in a way that changes an existing rule's
  meaning.
- Existing services — `identity-service`, `eligibility-service`,
  `credential-service`, `organization-service`, `initiative-service`,
  `discussion-service`, `moderation-service`, `voting-service`,
  `tally-service`, `delegation-service`, `ai-processing-service`,
  `transparency-service`, `governance-service`, `membership-service`,
  `compliance-service` (PACK-02 through PACK-09) — are unaffected,
  because none of them reads a canonical entity, field, event, or
  reason code that this round changed. They are named as **consumers**
  of the new event stream (`19f.24`), never as owners of anything it
  defines.
- Contract tests, JSON Schemas and OpenAPI files are untouched. The
  `diff -rq` result above confirms this directly: no file under
  `contracts/`, `schemas/`, or any service's OpenAPI definition
  appears in the changed-file list.

A consumer still running against canon `0.7.0` experiences no
breakage: nothing it reads changed shape, name or meaning. Section
`19f`, the seventy-two new events, the new reason codes and the new
forbidden links are simply unknown to it — inert, not contradicted.

A consumer must **not** infer, from the presence of this canon text,
that: finance is implemented; a `Finance Service` exists as running
code (`services/finance-service` does not exist — `19f.25`); any
legal threshold, disclosure amount, or currency list is fixed (no
`FinancePolicy` instance exists; only the policy **shape** is
canonical); or that `REPOSITORY_VERSION` has moved. It has not.

## 3. Reason-code registry diff

### 3.1 Newly added codes

Forty-five `FINANCE_*` codes are now defined in canon section `24`.
Forty-four come from specification section `15.2` verbatim; the
forty-fifth, `FINANCE_EXTERNAL_ACCEPTANCE_MISSING`, is **added by the
amendment itself** — it is not in the specification's proposed list
and exists to enforce the canon's own `externally_accepted` rule
(`19f.17`).

| Code                                                    | Canon subsection | Meaning                                                                            |
| ------------------------------------------------------- | ---------------- | ---------------------------------------------------------------------------------- |
| `FINANCE_AUTHORITY_MISSING`                             | `19f.18`         | No active, scope-matching finance authority for the action                         |
| `FINANCE_AUDITOR_INDEPENDENCE_VIOLATION`                | `19f.18`         | Candidate auditor fails the independence check for this scope/period               |
| `FINANCE_ACCOUNTING_PERIOD_CLOSED`                      | `19f.5`          | Target accounting period is closed; ordinary write refused                         |
| `FINANCE_ACCOUNTING_PERIOD_UNDETERMINED`                | `19f.5`          | No period, or no timezone-explicit period, could be determined                     |
| `FINANCE_PERIOD_REOPENING_NOT_AUTHORIZED`               | `19f.5`          | Reopening lacks authority, reason, or dual control                                 |
| `FINANCE_JOURNAL_ENTRY_UNBALANCED`                      | `19f.4`          | Debit and credit sums differ for a currency                                        |
| `FINANCE_IMMUTABLE_RECORD_MODIFICATION_ATTEMPTED`       | `19f.4`          | Attempt to modify a posted entry, frozen snapshot, or submitted version            |
| `FINANCE_CURRENCY_UNSUPPORTED`                          | `19f.3`          | Currency not in active policy, or cross-currency arithmetic attempted              |
| `FINANCE_MONETARY_AMOUNT_INVALID`                       | `19f.3`          | Amount is not integer minor units with a recorded scale and rounding rule          |
| `FINANCE_DUPLICATE_TRANSACTION`                         | `19f.6`          | A transaction with the same fingerprint already exists                             |
| `FINANCE_DUPLICATE_IMPORT`                              | `19f.6`          | Batch fingerprint matches an already-applied import                                |
| `FINANCE_IMPORT_PROVENANCE_MISSING`                     | `19f.6`          | Imported transaction lacks a batch or provenance reference                         |
| `FINANCE_TRANSFER_PAIR_UNRESOLVED`                      | `19f.6`          | An inter-unit transfer has no matching counterpart                                 |
| `FINANCE_RECLASSIFICATION_BYPASS_DENIED`                | `19f.6`          | Reclassification would drop a disclosure, review, aggregation or reporting duty    |
| `FINANCE_CONTRIBUTION_SOURCE_UNDETERMINED`              | `19f.7`          | Contributor source is anonymous or cannot be established                           |
| `FINANCE_CONTRIBUTION_VERIFICATION_INCOMPLETE`          | `19f.7`          | Required verification or declaration is missing                                    |
| `FINANCE_CONTRIBUTION_CLASSIFICATION_UNDETERMINED`      | `19f.7`          | No policy-bound classification could be determined                                 |
| `FINANCE_CONTRIBUTION_PROHIBITED`                       | `19f.7`          | Policy classifies the contribution as prohibited or restricted                     |
| `FINANCE_CONTRIBUTION_AGGREGATION_UNRESOLVED`           | `19f.8`          | The aggregate over the relevant period/perimeter could not be resolved             |
| `FINANCE_CONTRIBUTION_RETURN_REQUIRED`                  | `19f.7`          | A return obligation exists and blocks the requested action                         |
| `FINANCE_IN_KIND_VALUATION_MISSING`                     | `19f.9`          | A non-monetary contribution or benefit lacks a valuation basis                     |
| `FINANCE_VALUATION_METHOD_MISSING`                      | `19f.9`          | A valuation or revaluation lacks a method reference                                |
| `FINANCE_COUNTER_PERFORMANCE_MISSING`                   | `19f.9`          | Sponsorship approved without counter-performance or explicit policy classification |
| `FINANCE_SPONSORSHIP_DISCLOSURE_INCOMPLETE`             | `19f.9`          | Required disclosure classification or declaration is missing                       |
| `FINANCE_PAYMENT_AUTHORIZATION_MISSING`                 | `19f.10`         | Settlement attempted without a valid authorization                                 |
| `FINANCE_WRITE_OFF_NOT_AUTHORIZED`                      | `19f.11`         | Write-off lacks the authority or dual control the policy requires                  |
| `FINANCE_BUDGET_ACTUAL_WRITE_FORBIDDEN`                 | `19f.12`         | An attempt to store an actual amount on a budget line                              |
| `FINANCE_CROSS_SCOPE_CONSOLIDATION_DENIED`              | `19f.17`         | Consolidation lacks explicit authority, or would write into a lower scope          |
| `FINANCE_REPORTING_PERIMETER_UNDETERMINED`              | `19f.16`         | No effective reporting-perimeter definition exists for the period                  |
| `FINANCE_REPORT_SNAPSHOT_MISSING`                       | `19f.16`         | Preparation, validation or submission attempted without a frozen snapshot          |
| `FINANCE_REPORT_VALIDATION_INCOMPLETE`                  | `19f.17`         | Required validations have not completed or have open blocking findings             |
| `FINANCE_REPORT_APPROVAL_MISSING`                       | `19f.17`         | The action requires an approval that has not been recorded                         |
| `FINANCE_REPORT_SIGN_OFF_MISSING`                       | `19f.17`         | The action requires the legally responsible sign-off                               |
| `FINANCE_REPORT_STATUS_UNKNOWN`                         | `19f.17`         | Report status cannot be determined — fails closed                                  |
| `FINANCE_AUDIT_INCOMPLETE`                              | `19f.18`         | Auditor review requires a concluded engagement for this scope and period           |
| `FINANCE_EXTERNAL_ACKNOWLEDGEMENT_NOT_AUTHORITATIVE`    | `19f.17`         | An acknowledgement, receipt, delivery record or read status offered as acceptance  |
| `FINANCE_EXTERNAL_ACCEPTANCE_MISSING` (amendment-added) | `19f.17`         | External acceptance required, but no authoritative competent-authority reference   |
| `FINANCE_STATISTICAL_DISCLOSURE_RISK`                   | `19f.21`         | Requested view would breach the small-cell or combination disclosure rules         |
| `FINANCE_EVIDENCE_REFERENCE_MISSING`                    | `19f.23`         | A required evidence or document reference is absent                                |
| `FINANCE_EVIDENCE_ASSERTION_UNAVAILABLE`                | `19f.23`         | An authenticity/signedness/admissibility assertion is required but PACK-11-only    |
| `FINANCE_PARTY_HANDLE_PURPOSE_MISMATCH`                 | `19f.15`         | A handle was presented for a purpose or perimeter it was not minted for            |
| `FINANCE_PARTY_HANDLE_RESOLUTION_DENIED`                | `19f.15`         | Handle resolution attempted without the separate resolution authority              |
| `FINANCE_RETENTION_BINDING_MISSING`                     | `19f.23`         | A governed finance record has no PACK-09 record-class binding                      |
| `FINANCE_POLICY_MISSING`                                | `19f.20`         | No applicable policy of the required kind exists for this scope and date           |
| `FINANCE_POLICY_VERSION_UNKNOWN`                        | `19f.20`         | The referenced policy version does not exist or is not readable                    |

### 3.2 Reused existing codes

Thirty-two existing codes are reused verbatim by the finance context —
not duplicated, not redeclared under a `FINANCE_` name, not
reinterpreted:

| Code                                            | Introduced by             | Finance use                                                             |
| ----------------------------------------------- | ------------------------- | ----------------------------------------------------------------------- |
| `PERMISSION_DENIED`                             | `pack-02`                 | Caller lacks any authority for the operation                            |
| `VALIDATION_RECORD_NOT_FOUND`                   | `pack-02`                 | Unknown record, or the non-disclosing answer for a foreign-scope record |
| `VALIDATION_FORBIDDEN_TRANSITION`               | `pack-02`                 | Any lifecycle transition not in the allowed set                         |
| `VALIDATION_UNKNOWN_STATUS`                     | `pack-02`                 | Unknown status value on input                                           |
| `OPTIMISTIC_CONCURRENCY_CONFLICT`               | `pack-02`                 | Stale `expected_*_version`                                              |
| `AUDIT_CHAIN_BROKEN`                            | `pack-02`                 | Audit append integrity failure                                          |
| `EVENT_VERSION_UNSUPPORTED`                     | `pack-02`                 | Unsupported event version                                               |
| `INTEGRITY_CHECK_FAILED`                        | `pack-02`                 | Snapshot digest or import fingerprint mismatch                          |
| `SERVICE_STATE_READ_ONLY`                       | `pack-02`                 | Service in read-only state                                              |
| `EMERGENCY_FREEZE_ACTIVE`                       | `pack-02`                 | Emergency freeze blocks the write                                       |
| `ORGANIZATION_SCOPE_MISMATCH`                   | canon `0.7.0` / `pack-08` | Asserted scope does not match the target record's scope                 |
| `ORGANIZATION_SCOPE_UNDETERMINED`               | `pack-08`/`pack-09`       | Scope cannot be determined — default deny                               |
| `CROSS_SCOPE_ACCESS_DENIED`                     | canon `0.7.0`             | None of the six access modes granted access                             |
| `CROSS_SCOPE_AUTHORITY_INVALID`                 | `pack-09`                 | Presented cross-scope authority is invalid                              |
| `AUTHORITY_ROLE_INCOMPATIBLE`                   | canon `0.7.0`             | Auditor/administrator and other incompatible role pairs                 |
| `AUTHORITY_ASSIGNMENT_INVALID`                  | canon `0.7.0`             | Authority record fails PACK-08's lifecycle rule                         |
| `AUTHORITY_SCOPE_INVALID`                       | canon `0.7.0`             | Authority scope is structurally invalid                                 |
| `ORGANIZATIONAL_AUTHORITY_NOT_USABLE`           | `pack-08`                 | Authority exists but is not currently usable                            |
| `ORGANIZATION_DUAL_CONTROL_VIOLATION`           | `pack-08`                 | One actor on both sides of a dual-control action                        |
| `CONFLICT_OF_INTEREST_UNDECLARED`               | `pack-07`/`pack-09`       | Conflict state undeclared — fails closed                                |
| `CONFLICT_OF_INTEREST_BLOCKING`                 | `pack-07`/`pack-09`       | Declared conflict blocks the action                                     |
| `CONFLICT_REVIEW_SELF_APPROVAL_PROHIBITED`      | `pack-07`                 | Self-approval of one's own or self-benefiting act                       |
| `RECORD_UNDER_LEGAL_HOLD`                       | `pack-09`                 | Legal hold blocks the disposal-relevant action                          |
| `LEGAL_HOLD_STATE_UNKNOWN`                      | `pack-09`                 | Hold state indeterminate — fails closed                                 |
| `RETENTION_POLICY_REBIND_REQUIRES_REEVALUATION` | `pack-09`                 | Retention rebinding cannot shorten an obligation                        |
| `GOVERNED_RECORD_DELETION_FORBIDDEN`            | `pack-09`                 | Any deletion attempt on a governed finance record                       |
| `HISTORICAL_SCOPE_NOT_EFFECTIVE`                | canon `0.7.0`             | Scope/authority queried outside its effective window                    |
| `SUCCESSOR_TRANSFER_REQUIRES_DECISION`          | canon `0.7.0`             | A reorganization relation used as if it transferred finance authority   |
| `PUBLICATION_NOT_ALLOWED`                       | `pack-04`                 | Publication attempted without a separate publication authorization      |
| `DISCLOSURE_POLICY_VIOLATION`                   | `pack-04`                 | Emission would violate the disclosure policy                            |
| `CRITICAL_POLICY_ACTIVATION_NOT_AUTHORIZED`     | `pack-07`                 | Critical policy version activated without the required approval         |
| `CRITICAL_POLICY_VERSION_FROZEN`                | `pack-07`                 | Attempt to edit a frozen policy version                                 |

### 3.3 Renamed or rejected proposed codes

Four families of proposed names were rejected because they would have
silently collided with an existing code's meaning; each was resolved
by adopting a `FINANCE_`-prefixed name instead:

| Proposed name (rejected)                                                                                                                             | Would collide with                                                          | Adopted instead                                                                                              |
| ---------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| `CONTRIBUTION_CREATED` / `CONTRIBUTION_EDITED` / `CONTRIBUTION_FLAGGED` / `CONTRIBUTION_STATUS_CHANGED` / `CONTRIBUTION_DUPLICATE_CREATION_CONFLICT` | `Contribution` (canon `13.2`), a **deliberation** utterance in a discussion | `FINANCE_CONTRIBUTION_*` and `finance_contribution.*` events                                                 |
| `LEDGER_ENTRY_ALREADY_PUBLISHED` / `LEDGER_ENTRY_DUPLICATE_CONFLICT` / `TRANSPARENCY_LEDGER_ENTRY_PUBLISHED`                                         | `PublicLedgerEntry` (canon `19a.1`), the **public transparency ledger**     | `FINANCE_JOURNAL_ENTRY_*` and `journal_entry.*` events                                                       |
| `ACCOUNT_CREATED` / `ACCOUNT_STATUS_CHANGED`                                                                                                         | `Account` (canon `7.2`), a **platform user account**                        | `finance_account.*` events (no reason-code collision needed)                                                 |
| `AUDIT_EXPORT_*` / `AUDIT_EVENT_CONFLICT`                                                                                                            | audit-log integrity (`pack-02`/`pack-04`)                                   | `FINANCE_AUDIT_*` and `finance_audit.*` events (finance-audit engagement, distinct from audit-log integrity) |

One further near-collision was resolved the other way, by reuse
rather than renaming: PACK-09's `RETENTION_*`, `LEGAL_HOLD_*` and
`RECORD_UNDER_LEGAL_HOLD` codes mean exactly what the finance context
needs, because retention and legal holds remain PACK-09's domain.
They are deliberately reused verbatim (section 3.2) rather than
shadowed by `FINANCE_`-prefixed duplicates.

### 3.4 Registry file impact

No `contracts/reason-codes/pack-10.yml` was created in this round,
and none should be, until an implementation round exists.

This is a canon-only round: canon section `24` is now the canonical
registry of record for all forty-five new codes and the thirty-two
reused ones. A pack registry file such as `pack-09.yml` is an
**implementation-round** artefact — every existing registry
(`pack-02.yml` through `pack-09.yml`) exists to be loaded at runtime by
`epd2_core.reason_codes.ReasonCodeRegistry` and to be checked against
literal `reason_code` usage inside that pack's own running service
code.

`tests/contract/test_reason_codes_registry.py` makes this concrete: it
is parametrized over a fixed tuple of eight packs, `pack-02` through
`pack-09`, each entry naming that pack's registry path and its own
`services/<name>/src` directory list. For each pack it (1) asserts
every registry entry has the seven mandatory fields; (2) asserts no
duplicate codes; (3) scans that pack's own `services/*/src` trees with
a broad all-caps-literal regex and asserts every such literal is
registered in that pack's own file; and (4) asserts the registry loads
via `epd2_core.reason_codes.ReasonCodeRegistry` and meets a minimum
entry count. There is no ninth tuple entry for `pack-10`, and there is
no `services/finance-service/src` directory for it to scan — `19f.25`
states plainly that no such service exists yet.

Shipping a `pack-10.yml` now would therefore either fail check (3)
outright (a registry with no matching service directory has nothing
to scan, so the check would either be skipped in a way that proves
nothing, or the tuple would need a `services/finance-service` entry
that points at code that does not exist), or it would require
weakening the test's scanning/parametrization contract to tolerate an
empty or absent service directory. Weakening an existing, passing
test is explicitly forbidden by this project's own working rules, so
the registry file is deferred rather than shipped in a form the test
cannot honestly exercise.

The future file's shape is already fixed by convention and by
specification section `15`: the seven mandatory fields
(`code`, `meaning`, `severity`, `description`, `retryable`, `owner`,
`introduced_in_version`) that every existing registry uses, plus the
`source` marker (`pack-10-service` for the forty-five new codes,
`pack-0X-reused` for each of the thirty-two reused codes) that
distinguishes introduced from redeclared entries — the same
convention `pack-09.yml`'s header documents. Every new entry's
`introduced_in_version` will read `0.10.0` (the **repository**
version an implementation round would introduce it at, a different
axis from `CANON_VERSION`), and every new entry's `owner` will read
`finance-service`.

## 4. Event-canon diff

Canon section `20.17` now lists seventy-two events (verified by
counting the section's own bullet list), against the sixty-nine
proposed in specification section `14` (also verified by counting the
specification's table rows). Three events were added by the amendment
that the specification did not propose:

- `import_batch.duplicate_detected` — required by the duplicate-import
  rule the amendment added at `19f.6`: a batch fingerprint matching an
  already-applied import must be observable as its own fact, not
  folded silently into `import_batch.rejected`.
- `finance_report.amended` and `finance_report.superseded` — required
  by the canon's twelve-state report lifecycle at `19f.17`, which
  splits the specification's single `amended_or_restated` state into
  three distinct, separately triggered facts: `restated` (already
  proposed), `amended` (added), and the new terminal `superseded`
  (added, marking a version displaced by a later one).

No event in sections `20.1` through `20.16` was renamed, removed, or
given a new owner by this round. Section `20.17` is additive-only, and
its own text confirms the envelope from section `21` applies
unchanged, so no existing event's version was bumped either.

## 5. Report-state naming diff

The specification's ten `Rechenschaftsbericht` states (section `4.9`)
map onto the canon's twelve (`19f.17`) as follows:

| Specification state (`0.9.0`, section `4.9`) | Canon state(s) (`0.8.0`, `19f.17`)  | Note                                               |
| -------------------------------------------- | ----------------------------------- | -------------------------------------------------- |
| `draft`                                      | `draft`                             | unchanged                                          |
| `internally_reviewed`                        | `internally_reviewed`               | unchanged                                          |
| `auditor_reviewed`                           | `auditor_reviewed`                  | unchanged                                          |
| `approved`                                   | `approved`                          | unchanged                                          |
| `signed`                                     | `signed`                            | unchanged                                          |
| `submitted`                                  | `submitted`                         | unchanged                                          |
| `externally_acknowledged`                    | `externally_acknowledged`           | unchanged                                          |
| `accepted_by_authority`                      | `externally_accepted`               | renamed                                            |
| `published`                                  | `published`                         | unchanged                                          |
| `amended_or_restated`                        | `amended`, `restated`, `superseded` | split into three; `superseded` is new and terminal |

The canon names are now authoritative. `PACK-10-SPECIFICATION.md`
section `4.9` and `docs/adr/ADR-047-rechenschaftsbericht-lifecycle-snapshot-and-authority-semantics.md`
still use the earlier, ten-state names, because they are
architecturally accepted (the ADRs themselves remain `proposed`)
specification and ADR text and are not rewritten after the fact. An
implementation round must follow the canon's twelve-state names, not
the specification's ten; this divergence is recorded here rather than
silently reconciled by editing the architecturally accepted
specification.

## 6. Ownership diff

Section `22` gains twenty-one new rows (verified by counting rows
whose owner column reads `Finance Service`), one per new aggregate,
all in `finance-service`:

`FinanceAccount`, `AccountingPeriod`, `JournalEntry`,
`FinancialTransaction`, `ImportBatch`, `ReconciliationRecord`,
`FinanceContribution`, `SponsorshipAgreement`,
`ExternalFinancialBenefit`, `ExpenseClaim`, `PaymentAuthorization`,
`Budget`, `FinancialAsset`, `FinancialObligation`,
`ReportingObligation`, `ReportingPerimeterDefinition`, `FinanceReport`,
`ReportSnapshot`, `AuditEngagement`, `FinancePolicy`,
`FinancePartyHandle`.

Nothing else moved. In particular, ownership of the following stayed
exactly where it already was:

- **Identity** — `IdentityRecord` stays with Identity Verification
  Service.
- **Membership** — `Membership` stays with Membership Service.
- **Organizational authority** — `OrganizationalAuthority` and
  `RoleAssignment` stay with Organization Service / Permission-Role
  Service.
- **Legal cases, deadlines, notices, Legal Hold, retention
  governance** — all stay with `compliance-service` (PACK-09); the
  finance context only holds safe references to them
  (`FinanceEvidenceRef`-style boundary, section 2).
- **Document bytes, evidence content** — stay with the Evidence
  Service (PACK-11); finance records only carry safe references.
- **Lobbying meetings** — stay with the Lobby Log Service /
  Transparency Context (canon `19a.4`) and PACK-35's future scope.
- **Voting, ballots, eligibility credentials, tally** — stay with
  Vote Casting Service, Ballot Definition Service, Credential Issuer,
  and Tally Service respectively; section `23` (section 7) forbids
  any finance record from correlating with them.
- **Production payment execution** — the actual movement of money
  outside the platform is not owned by `Finance Service` and is not
  claimed by this round at all; `PaymentAuthorization` records that an
  authorization and a settlement fact occurred, never the external
  payment rail itself.

## 7. Forbidden-link diff

Section `23` gains twenty-five new entries (counted as complete bullet
items, several of which wrap across more than one source line — a
naive per-line count of the `(добавлено 0.8.0, ...)` marker undercounts
this for that reason). Grouped by what they prohibit:

- **Voting correlation** — no finance record, event, or derived
  representation may reach `Ballot`, `VoteEnvelope`, `Tally`, or any
  voting credential; `FinancePartyHandle` specifically may never touch
  `ParticipationCredential` or any eligibility signal.
- **Identity exposure** — no finance event or public financial
  representation may carry `IdentityRecord`, `Account` data, bank
  details, IBANs, or payment identifiers; `FinancePartyHandle` may
  never be reused across purposes or perimeters, or projected
  publicly in any form.
- **Storage boundaries** — `finance-service` may not itself store
  PACK-09 records (legal case, deadline, notice, legal hold) or
  PACK-11 records (document, evidence, authenticity assertions), nor
  compute or store voting/tally/delegation data; a document reference
  may never carry an authenticity or admissibility assertion itself
  (only PACK-11 makes that assertion); `FinanceContribution`,
  `SponsorshipAgreement` and `ExternalFinancialBenefit` may not reach
  PACK-35's meeting/contact/lobbying/influence entities directly.
- **Authority overreach** — a system or technical administrator gets
  no finance authority, posting, approval, signature or publication
  right; `finance_administrator` and `finance_auditor` remain
  incompatible in the same scope/period; a consolidating scope gets no
  posting/correction/approval/closing right in a subordinate scope; an
  audit authority may not post into the aggregate it audits or treat
  its own reconciliation as authoritative.
- **Telemetry / legal effect** — delivery, receipt or read telemetry
  may never itself constitute legal effect or drive a report-version
  transition; publication of a report version is never automatic legal
  acceptance by a competent authority.
- **Budget / ledger integrity** — `Budget`/`BudgetVersion` may never
  overwrite ledger facts or store an actual value; a posted
  `JournalEntry`, a frozen `ReportSnapshot`, or a submitted report
  version may never be edited in place or deleted; reclassifying a
  record may never be used to shed a disclosure, verification,
  aggregation or reporting obligation; `FinancePolicy.effective_from`
  may never be backdated into an already-closed or already-submitted
  period.
- **Publication / acceptance** — a derived public representation may
  never perform an authoritative mutation of the source record or
  assign itself authoritative status.

## 8. Consumer guidance

An implementation round for PACK-10 must, before writing any service
code: bind explicitly to canon `0.8.0` (not `0.7.0`); create
`contracts/reason-codes/pack-10.yml` following the shape in section
3.4, once `services/finance-service` exists for the registry test to
scan; and follow the canon's twelve-state report names (section 5),
not the specification's ten-state names, wherever the two diverge.

Owners of PACK-09 (`compliance-service`), PACK-11 (Evidence Service)
and PACK-35 need to know only that they are named as **consumers** of
the section `20.17` event stream and as holders of records finance
references safely — none of their own owned entities, statuses, or
reason codes changed, and none of them is expected to emit or mutate
anything in section `20.17`.

Nothing in canon `0.8.0` licenses: standing up
`services/finance-service`; declaring any legal, tax, or disclosure
threshold as fixed; treating any `FinanceReport` state as reachable
without its named precondition (a snapshot, a concluded audit
engagement, an authoritative acceptance reference); or bumping
`REPOSITORY_VERSION` or widening `repository_compatibility`. All of
those require their own separate, later, governed round (`19f.25`).

## 9. Open compatibility questions

- **`OD-20` — `repository_compatibility` range and round ordering.**
  Already recorded in `docs/packs/PACK-10-OPEN-DECISIONS.md`: whether
  the declared `>=0.1.0 <0.10.0` range is widened to admit a future
  `0.10.0`, or the canon amendment lands first and the range moves
  with it, and whether the canon-first ordering the specification
  assumes (sections 17, 19) is confirmed as an owner decision rather
  than treated as already settled. Recommended handling: keep the
  range unchanged until an implementation round is actually authorized
  (section 1), and resolve `OD-20` as part of authorizing that round,
  not before.
- **Report-state naming divergence (section 5).** The specification
  and ADR-047 use the ten-state names; the canon uses twelve. Recommended
  handling: treat the canon names as authoritative for all future
  work and leave the specification and ADR-047 text as historical
  record of the state at proposal time, rather than editing the
  architecturally accepted
  documents to match later canon text.
- **Registry-file timing (section 3.4).** `contracts/reason-codes/pack-10.yml`
  should not be created before `services/finance-service` exists,
  because `test_reason_codes_registry.py` would have nothing real to
  scan against it. Recommended handling: create the file as the first
  deliverable of the implementation round's phase 0, immediately
  alongside the new service directory, so the registry and the
  contract test become meaningful together rather than the file
  existing unchecked in the meantime.
