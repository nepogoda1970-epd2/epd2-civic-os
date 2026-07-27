# CLAUDE-PACK-10 — Canon 0.8.0 acceptance matrix

This document is the acceptance evidence for the canon-amendment round
that introduces the party-finance bounded context: canon version
`0.8.0`, section `19f`, event subsection `20.17`, and the new entries
in sections `22`, `23` and `24`. It covers canon content, version
state and the repository checks that prove them. It is not an
implementation acceptance plan — that remains
`docs/packs/PACK-10-ACCEPTANCE-MATRIX.md`, which is measured against a
`services/finance-service` that does not exist yet. No finance runtime
code exists to test: this round ships documentation only, and every
row below is honest about what was, and was not, executed.

## 1. Automated canon checks

Every check below was read from
`scripts/check_canon_0_8_0.py` and numbered exactly as the script's
own inline comments number it (`# Check 1` through `# Check 16`). The
sixteen checks run as a single process and produce a single `OK:`
line; the per-row `Result` cells below all point to that one
execution rather than sixteen separate invocations.

This section covers only whether the amendment's own automated
checks pass. It says nothing about whether those checks are complete
enough to stand in for a full canon review — that is what sections 2
through 4 exist for, walking requirement to requirement and
invariant to invariant to show exactly how much of the round each
check actually exercises, and where the evidence is documentary
instead.

| Check                                                | Implemented by                                                     | Asserts                                                                                                                                                                                      | Result                                                                                                                                                                                                                          |
| ---------------------------------------------------- | ------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Check 1 — canon version declared                     | `scripts/check_canon_0_8_0.py::check_canon_version_declared`       | `canon_version` is `0.8.0` in `canon-version.json`, `CANON_VERSION` in `version.py`, and `CANON_VERSION` in `version.ts`                                                                     | Passed — `python3 scripts/check_canon_0_8_0.py`: `OK: all 16 canon 0.8.0 amendment checks passed.`                                                                                                                              |
| Check 2 — repository version unchanged               | `check_repository_version_unchanged`                               | `REPOSITORY_VERSION` is still `0.9.0` in `version.py` and `version.ts` (19f.25)                                                                                                              | Passed — same run as above                                                                                                                                                                                                      |
| Check 3 — repository compatibility                   | `check_repository_compatibility`                                   | `repository_compatibility` range and `minimum_repository_version` in `canon-version.json` still accept a `0.9.0` repository                                                                  | Passed — same run as above                                                                                                                                                                                                      |
| Check 4 — finance implementation status              | `check_finance_implementation_status`                              | `finance_context_implementation_status` in `canon-version.json` equals `not_implemented`                                                                                                     | Passed — same run as above                                                                                                                                                                                                      |
| Check 5 — no finance runtime implementation          | `check_no_finance_runtime_implementation`                          | `services/finance-service` does not exist; no path under `services/`, `packages/`, `frontend/` or `contracts/` is named for finance                                                          | Passed — same run as above                                                                                                                                                                                                      |
| Check 6 — finance context present                    | `check_finance_context_present`                                    | Headings `# 19f.` and `## 20.17.` exist; section 22 carries at least 21 `Finance Service` ownership rows                                                                                     | Passed — same run as above                                                                                                                                                                                                      |
| Check 7 — finance entity ownership                   | `check_finance_entity_ownership`                                   | Each of the 21 named finance aggregates owns exactly one section-22 row (INV-02)                                                                                                             | Passed — same run as above                                                                                                                                                                                                      |
| Check 8 — `FinancePartyHandle` not a global identity | `check_finance_party_handle_not_global_identity`                   | `PersonId`, `UserId` and `GlobalUserId` appear in section 19f only inside an explicit prohibition (ФИН-01)                                                                                   | Passed — same run as above                                                                                                                                                                                                      |
| Check 9 — finance carries no edge into voting        | `check_finance_voting_links_forbidden`                             | Section 23 forbids a finance concept linking to `Ballot`, `VoteEnvelope` and a participation/voting credential                                                                               | Passed — same run as above                                                                                                                                                                                                      |
| Check 10 — ledger immutability and balancing         | `check_ledger_immutability_and_balancing`                          | Section 19f states the balanced-posting rule, posted-entry immutability, and the correction-by-reversal rule (19f.4)                                                                         | Passed — same run as above                                                                                                                                                                                                      |
| Check 11 — finance-auditor incompatibility           | `check_finance_auditor_incompatibility`                            | Section 19f registers `finance_auditor × finance_administrator` in its incompatibility matrix (19f.14)                                                                                       | Passed — same run as above                                                                                                                                                                                                      |
| Check 12 — submission distinct from acceptance       | `check_report_submission_distinct_from_acceptance`                 | Section 19f names both `submitted` and `externally_accepted` and states that submission alone is neither acknowledgement nor acceptance (19f.17)                                             | Passed — same run as above                                                                                                                                                                                                      |
| Check 13 — PACK-11 / PACK-35 keep their domains      | `check_cross_pack_ownership_unchanged`                             | Section 19f still assigns document/evidence bytes to PACK-11 and lobbying contacts/meeting disclosure to PACK-35 (19f.22)                                                                    | Passed — same run as above                                                                                                                                                                                                      |
| Check 14 — 20.17 event catalogue governed            | `check_finance_event_catalogue`                                    | Section 20.17 carries a `finance-service` owner statement, a no-other-owner statement, a prohibited-payload statement (with its two mandated tokens), and at least 72 backticked event names | Passed — same run as above                                                                                                                                                                                                      |
| Check 15 — reason codes unique and complete          | `check_reason_code_registry`                                       | Every code defined in section 24 is unique and at least 45 carry the `FINANCE_` prefix                                                                                                       | Passed — same run as above                                                                                                                                                                                                      |
| Check 16 — no accepted ADR rewritten                 | `check_adr_set_unchanged`                                          | `ADR-001`–`ADR-043` (excluding the recorded `ADR-007` gap) carry no `0.8.0` mention in `## Status`/`## Date`; `ADR-044`–`ADR-050` are all `proposed`                                         | Passed — same run as above                                                                                                                                                                                                      |
| `scripts/verify_versions.py`                         | repository script                                                  | Every version-declaration site in the repository (canon, package, contract) is mutually consistent                                                                                           | Executed and passed: `OK: all version sources are consistent.`                                                                                                                                                                  |
| `scripts/check_repository.py`                        | repository script                                                  | Every required repository path from the structural manifest is present                                                                                                                       | Executed and passed: `OK: all 556 required paths are present.`                                                                                                                                                                  |
| `scripts/check_forbidden_files.py`                   | repository script                                                  | No forbidden path (build artefact, secret, disallowed pattern) exists in the tree                                                                                                            | Executed and passed: `OK: no forbidden paths found.` (the script printed a `WARNING` that this container is not a git repository and fell back to a full filesystem walk; the pass verdict is unaffected)                       |
| `tests/repository/test_canon_0_8_0_amendment.py`     | pytest wrapper around all 16 functions above, plus `find_problems` | Restates each check above, plus one aggregate test, as a pytest test function                                                                                                                | **NOT executed.** `pytest` is not installed in this preparation environment (`python3 -c "import pytest"` raises `ModuleNotFoundError`). This row is not a pass; it is an honest statement that the wrapper was never run here. |

The three repository scripts were each invoked directly from the
repository root: `python3 scripts/verify_versions.py`,
`python3 scripts/check_repository.py`, and
`python3 scripts/check_forbidden_files.py`. All three exited `0` and
printed exactly the `OK:` line quoted in their row above.
`check_forbidden_files.py` additionally printed a `WARNING` that this
container is not a git repository and that it therefore fell back to
a full filesystem walk; that warning changes how the script looks for
files, not what it concluded, and its conclusion was still `OK:`.

The pytest gap deserves one further honest qualification rather than
a bare disclaimer. `tests/repository/test_canon_0_8_0_amendment.py`
imports the same sixteen functions from `scripts/check_canon_0_8_0.py`
and asserts each returns an empty problem list — it adds no
assertion of its own. Because those sixteen functions were called
directly, in this same repository checkout, and every one returned no
problems, the substance of every assertion the pytest wrapper would
make has already been exercised. What has not happened is the literal
invocation of the file through a `pytest` process, which matters for
wiring the wrapper into CI and for collecting it alongside the rest of
the repository's test suite — not for whether the sixteen underlying
claims are true in this checkout. A reviewer relying on this document
should still require an actual `pytest tests/repository/test_canon_0_8_0_amendment.py`
run in an environment where `pytest` is installed before treating the
wrapper itself as proven; this document does not substitute for that
run, it only explains why it is currently absent.

## 2. Canon content acceptance

Each row maps a requirement of the governing request to the canon
location it now lives in, and to the evidence that it is there —
either a check from section 1, or "documentary" where no automated
check reads that specific rule.

| Requirement                                                             | Canon location                                   | Evidence                                                                                                                                                                                                                               |
| ----------------------------------------------------------------------- | ------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Canon version `0.8.0`                                                   | `canon-version.json`, `version.py`, `version.ts` | Check 1                                                                                                                                                                                                                                |
| Finance bounded context, twenty-five subsections                        | `19f.1`–`19f.25`                                 | Check 6 (heading and ownership-row-count presence); the other checks below cover specific rules within it                                                                                                                              |
| Twenty-one finance aggregates, each with an ownership row               | `19f.1`, `22`                                    | Check 7                                                                                                                                                                                                                                |
| Forty-five-rule finance invariant register (`ФИН-01`–`ФИН-45`)          | `19f.13`                                         | Five of the forty-five are directly checked (Checks 8, 9, 10, 11, 12 — ФИН-01, ФИН-05/06/07, ФИН-26, ФИН-30, and part of ФИН-20/ФИН-36); the remaining rules are documentary — no automated check enumerates the register rule by rule |
| Four new institutional roles plus the extended incompatibility baseline | `19f.14`                                         | Check 11 covers the `finance_auditor × finance_administrator` pair; the rest of the matrix (`payment_authorizer`, `payment_executor`, `report_signatory`, and the remaining pairs) is documentary                                      |
| `FinancePartyHandle`                                                    | `19f.15`                                         | Check 7 (ownership row), Check 8 (not a global identity), Check 9 (no voting edge); the purpose/perimeter-scoping rules themselves are documentary                                                                                     |
| Twelve-state `Rechenschaftsbericht` lifecycle                           | `19f.17`                                         | Check 12 covers the submission/acceptance distinction; the remaining eleven-way sequencing is documentary                                                                                                                              |
| Seventy-two-event catalogue                                             | `20.17`                                          | Check 14                                                                                                                                                                                                                               |
| Forty-five new reason codes                                             | `24`                                             | Check 15                                                                                                                                                                                                                               |
| Twenty-five new forbidden links                                         | `23`                                             | Check 9 covers the three voting-isolation entries; the remaining twenty-two entries are documentary                                                                                                                                    |
| Public-disclosure rules                                                 | `19f.21`                                         | Documentary — no automated check reads section 19f.21                                                                                                                                                                                  |
| Policy versioning                                                       | `19f.20`                                         | Documentary — no automated check reads section 19f.20                                                                                                                                                                                  |
| Cross-pack boundaries                                                   | `19f.22`, `19f.23`                               | Check 13 (PACK-11/PACK-35 ownership) and Check 9 (voting isolation); the PACK-09/PACK-12/PACK-13/PACK-14 boundary prose is documentary                                                                                                 |
| Implementation gate                                                     | `19f.25`                                         | Checks 2, 3, 4, 5 and 16 jointly — repository version unchanged, compatibility metadata unchanged, `not_implemented` declared, no runtime code, and no ADR of the round accepted                                                       |

Fourteen requirements are listed above. Six are fully covered by a
single dedicated check (canon version, twenty-one ownership rows,
seventy-two-event catalogue, forty-five reason codes, and the two
halves of the implementation gate already listed as one row). Seven
are covered only in part, because the corresponding canon subsection
states more rules than any one check reads (the bounded context as a
whole, the invariant register, the institutional-role matrix,
`FinancePartyHandle`, the report lifecycle, the forbidden-link list,
and the cross-pack boundaries). Two — public-disclosure
rules and policy versioning — have no automated check at all and are
documentary only; nothing in `scripts/check_canon_0_8_0.py` reads
`19f.20` or `19f.21`. This distribution is expected for a
canon-amendment round: the script's own docstring states it verifies
version state, absence of an implementation, and a handful of the
sharpest structural rules, not every sentence of the amendment.

## 3. Invariant coverage map

One row per `ФИН-01`–`ФИН-45`, mapping each canon invariant to the
specification hard invariant(s) `HI-n` (`docs/packs/PACK-10-SPECIFICATION.md`
section 6) it corresponds to. Both registers were read start to
finish for this mapping: the forty-five rules of `19f.13`, and all
fifty-five rows of the specification's section 6 table, including its
own note that rows 1–46 are the governing request's minimum set and
rows 47–55 were added afterward by a baseline repository analysis.
The mapping is deliberately one-directional and conservative: a `ФИН`
row is mapped to every `HI` row whose planned enforcement point and
mechanism restate the same rule, and to more than one `HI` row where
the canon states in one sentence what the specification split across
several planned tests. No `HI` number is invented, and no `ФИН` row is
forced onto an `HI` row that does not actually restate it — the one
case where no honest match exists, `ФИН-23`, is left unmapped in the
table and explained below it instead of being attached to a
loosely-related `HI` row for the sake of filling the cell.

| ФИН    | Restatement                                                                                                                                       | HI mapping                             |
| ------ | ------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------- |
| ФИН-01 | No global user ID; no `UserId`, `GlobalUserId`, reusable `PersonId`                                                                               | HI-1                                   |
| ФИН-02 | Events, audit, public views and cross-service refs carry no identity data beyond ids/enums/time/codes/versions                                    | HI-2                                   |
| ФИН-03 | Every finance record is organizational-scope bound; scopes isolate by default                                                                     | HI-3                                   |
| ФИН-04 | An undeterminable scope denies the operation before any other check                                                                               | HI-4                                   |
| ФИН-05 | Posted ledger records are immutable; edit-in-place and deletion are forbidden                                                                     | HI-5, HI-6                             |
| ФИН-06 | Correction happens only through governed reversal or a correcting entry, referencing the original, with a reason code                             | HI-6                                   |
| ФИН-07 | Every posted entry balances: debit minor units equal credit minor units per currency                                                              | HI-7                                   |
| ФИН-08 | Money is integer minor units with explicit deterministic decimal semantics; floating point is forbidden                                           | HI-8, HI-9                             |
| ФИН-09 | Currency is always explicit; cross-currency arithmetic without a recorded conversion is forbidden                                                 | HI-8                                   |
| ФИН-10 | Accounting-period closure blocks ordinary posting, re-checked inside every posting command                                                        | HI-10                                  |
| ФИН-11 | Reopening a closed period requires explicit authority, reason, policy version, preserved prior state and audit                                    | HI-11                                  |
| ФИН-12 | A budget never overwrites ledger facts or becomes a second source of truth for actuals                                                            | HI-12                                  |
| ФИН-13 | Reclassification cannot bypass verification, disclosure, aggregation or reporting obligations                                                     | HI-13                                  |
| ФИН-14 | Splitting a sum across transactions within the relevant policy period/scope does not bypass aggregation                                           | HI-14                                  |
| ФИН-15 | Declared related-party or intermediary contributions are not unrelated merely because they arrived separately                                     | HI-15                                  |
| ФИН-16 | Anonymous, unverifiable or prohibited contributions fail closed into a governed exceptional state                                                 | HI-16, HI-17                           |
| ФИН-17 | Rejection, return or escalation of a contribution leaves the original receipt unchanged                                                           | HI-18                                  |
| ФИН-18 | A non-monetary contribution requires an explicit valuation basis and evidence reference                                                           | HI-19                                  |
| ФИН-19 | Sponsorship records both financial value and counter-performance; absence needs an explicit policy classification                                 | HI-20                                  |
| ФИН-20 | The finance domain does not own general lobbying-contact/meeting disclosure and implements none of its entities                                   | HI-21                                  |
| ФИН-21 | An evidence/document reference does not make the finance domain the owner of that document's or evidence's content                                | HI-22                                  |
| ФИН-22 | Legal Hold overrides destruction and ordinary retention expiry                                                                                    | HI-23, HI-24                           |
| ФИН-23 | Historical policy versions stay bound to the historical decisions they governed and remain readable forever                                       | none dedicated — see closing paragraph |
| ФИН-24 | A report source snapshot is immutable, created once, and outlives every later report version                                                      | HI-25                                  |
| ФИН-25 | A newer report version never overwrites an earlier submitted, acknowledged or published version                                                   | HI-26                                  |
| ФИН-26 | Submission is not external acceptance                                                                                                             | HI-27                                  |
| ФИН-27 | Delivery, receipt or read telemetry is not a legal act and cannot be a state-transition input                                                     | HI-28                                  |
| ФИН-28 | Publication is not approval unless separately issued; approval is not publication                                                                 | HI-29                                  |
| ФИН-29 | Financial-auditor independence is mandatory and re-checked, never presumed                                                                        | HI-30                                  |
| ФИН-30 | `finance_auditor` and `finance_administrator` are incompatible in the same legally relevant scope                                                 | HI-31                                  |
| ФИН-31 | Self-approval of a personally created or personally beneficial transaction is prohibited where policy protects it                                 | HI-32                                  |
| ФИН-32 | Conflict-of-interest state is mandatory to declare for protected actions; unknown state fails closed                                              | HI-33                                  |
| ФИН-33 | Preparation, approval, signing, audit, submission and publication are distinguishable actions with distinct authorities                           | HI-34                                  |
| ФИН-34 | Public financial representations are derived, versioned and never authoritative                                                                   | HI-35                                  |
| ФИН-35 | Statistical disclosure control applies wherever publication could reveal protected persons                                                        | HI-36                                  |
| ФИН-36 | Financial records, identifiers and audit metadata form no correlation bridge into voting                                                          | HI-37, HI-38                           |
| ФИН-37 | Cross-scope consolidation grants no write authority into a lower scope                                                                            | HI-39                                  |
| ФИН-38 | Imported data preserves source provenance and batch identity, and supports duplicate/replay detection                                             | HI-40, HI-41                           |
| ФИН-39 | Time, timezone and period boundaries are explicit; a naive datetime is never accepted                                                             | HI-42                                  |
| ФИН-40 | Every protected refusal and protected transition carries a reason code; free-text refusal is forbidden                                            | HI-43                                  |
| ФИН-41 | An unknown authority, policy version, scope, conflict state, reporting perimeter or report status fails closed                                    | HI-44                                  |
| ФИН-42 | Feature flags do not disable hard finance invariants and are not read inside an invariant check                                                   | HI-45                                  |
| ФИН-43 | No legal-compliance, authority-acceptance or operational-readiness claim follows from this section                                                | HI-46                                  |
| ФИН-44 | Direct access to another service's storage is forbidden; every cross-service fact arrives through a published interface                           | HI-47                                  |
| ФИН-45 | A role name alone is never proof of finance authority; it resolves to an active, scope-matching `OrganizationalAuthority`/`RoleAssignment` record | HI-53                                  |

Seven specification rows have no corresponding numbered `ФИН` register
entry. Four of them are implementation-level conventions the
repository already applies uniformly from PACK-02 onward, not
canon-level financial rules, and properly stay at the repository
level rather than being re-declared as finance canon: `HI-49` (no
command reads system time — injected clock), `HI-50` (command
idempotency through a caller-supplied `event_id`), `HI-51`
(optimistic concurrency on every mutable aggregate), and `HI-52`
(every critical action appends an audit event with canonical
before/after hashes). The remaining three are substantive finance
rules that the canon does state, but only in prose rather than as a
numbered `ФИН` entry: `HI-48` (the purpose-scoped handle is
non-reusable and non-correlatable outside its declared purpose,
stated in `19f.15`'s hard rules), `HI-54` (a later reorganization
never rewrites the historical perimeter of a closed or submitted
period, stated across `19f.16` and `19f.19`), and `HI-55` (rounding
and valuation method are recorded with the record, never implicit,
stated across `19f.3`, `19f.9` and `19f.11`). `ФИН-23` is the mirror
case: a canon rule (historical policy versions stay bound and remain
readable) with no dedicated specification `HI` row at all — the
closest specification treatment is `HI-44`'s fail-closed handling of
an unknown policy version, which is a related but distinct concern.

## 4. Negative acceptance — what must remain absent

Only one of the items below is checked by a repeatable, CI-grade
script: the finance-name scan performed by
`check_no_finance_runtime_implementation` (Check 5), which walks
every file and directory under `services/`, `packages/`, `frontend/`
and `contracts/` looking for `finance` in a path name. Every other row
was verified once, for this document, with a manual search run from
the repository root; those searches are point-in-time and are not
re-run automatically by any script in `scripts/` today. A future round
that wants these guarantees enforced continuously, rather than
attested once here, would need to add dedicated checks for them —
this document records that they hold now, not that they are
mechanically guaranteed to keep holding.

| Must remain absent                                                                        | Verified by                                                                                                                                                                                                 |
| ----------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `services/finance-service` directory                                                      | Check 5                                                                                                                                                                                                     |
| Any path containing `finance` under `services/`, `packages/`, `frontend/` or `contracts/` | Check 5                                                                                                                                                                                                     |
| Any migration                                                                             | Check 5's finance-name scan of those four roots, plus a manual `find` for `*migration*` paths naming finance, which returned no matches                                                                     |
| Any OpenAPI operation                                                                     | Manual search for finance-named OpenAPI/contract files; none found                                                                                                                                          |
| Any runtime JSON Schema                                                                   | Manual search under `contracts/` and `packages/`; none found                                                                                                                                                |
| Any frontend page                                                                         | Manual `find ./frontend -iname "*finance*"`; none found                                                                                                                                                     |
| Any business test                                                                         | Manual `find ./services ./tests -iname "*finance*"`; none found (`tests/repository/test_canon_0_8_0_amendment.py` is a canon-amendment test, not a finance business test)                                   |
| `REPOSITORY_VERSION` still `0.9.0`                                                        | Check 2, plus `verify_versions.py`                                                                                                                                                                          |
| No accepted ADR rewritten                                                                 | Check 16 (`ADR-001`–`ADR-043` carry no `0.8.0` mention in `## Status`/`## Date`)                                                                                                                            |
| `ADR-044`–`ADR-050` all `proposed`                                                        | Check 16, cross-checked by direct inspection of each ADR's `## Status` block                                                                                                                                |
| No existing reason code renamed or redefined                                              | Section 24's own closing paragraph names the 32 pre-existing codes reused verbatim by the finance round and states no collision was found; Check 15 additionally proves the 45 `FINANCE_*` codes are unique |
| No existing ownership row changed                                                         | Check 7 asserts only that the 21 new finance rows exist and are singular; the pre-existing rows (`Account`, `Organization`, and so on) were read and are byte-identical to the 0.7.0 matrix in section 22   |

The manual searches behind the rows above were, specifically: a
recursive `find` for any path whose name contains `migration` and
also names finance; a recursive `grep` for `finance` inside any file
named like an OpenAPI document; a recursive `find` under `contracts/`
and `packages/` for finance-named schema files; a `find` under
`frontend/` for finance-named files of any kind; and a `find` under
`services/` and `tests/` for finance-named files of any kind. Every
one of the five returned no results.

## 5. Manual review checklist

The following require a human reviewer because no automated check can
evaluate them:

- **Russian canon text correctness and idiom.** Sections 19f, 20.17,
  22, 23 and 24 are normative Russian prose; a native or expert
  reviewer must confirm the wording is correct, unambiguous and
  consistent with the rest of the canon's register, not merely that
  the expected substrings are present.
- **The twelve report states match the owner's intent.** `draft`,
  `internally_reviewed`, `auditor_reviewed`, `approved`, `signed`,
  `submitted`, `externally_acknowledged`, `externally_accepted`,
  `published`, `amended`, `restated`, `superseded` — a reviewer must
  confirm this is the lifecycle the owner actually wants, since the
  state names diverge from the specification's own state-name
  vocabulary (for example, `externally_accepted` rather than
  `accepted_by_authority`).
- **The `finance_administrator` × `organizational_administrator`
  incompatibility.** Section 19f.14 records this pair as "accepted as
  an owner decision" and a "recommended invariant," not as a
  structural necessity the repository forced. A reviewer must confirm
  this reading of the owner's decision is correct.
- **The legal open decisions remain open.** Nothing in this round may
  have quietly closed a PACK-09 legal question (for example, what
  counts as an authoritative notice-effect reference); a reviewer
  should confirm no such closure occurred under cover of a finance
  cross-reference.
- **The three divergences from the specification.** The
  report-state names, the three events added beyond the
  specification's original catalogue
  (`import_batch.duplicate_detected`, `finance_report.amended`,
  `finance_report.superseded`), and the one added reason code
  (`FINANCE_EXTERNAL_ACCEPTANCE_MISSING`, alongside the
  specification's own `FINANCE_EXTERNAL_ACKNOWLEDGEMENT_NOT_AUTHORITATIVE`)
  are all documented in `19f.24` as intentional. A reviewer must
  confirm the owner accepts each of the three, rather than reading
  them as unreviewed drift.
- **No hard-coded German legislative threshold.** `19f.20` states
  that German statutory thresholds are never encoded as canon or code
  constants and are instead inputs to a versioned `FinancePolicy`; a
  reviewer with the relevant legal knowledge must confirm that this
  section names no such threshold as fact anywhere, since no
  automated check can tell a correctly-versioned policy input from an
  accidentally hard-coded legal number.

## 6. Gate conditions

Before the 0.8.0 canon amendment can be called **accepted** rather
than a candidate, all of the following must hold:

- Every check in section 1 passes, including a completed run of the
  pytest wrapper once `pytest` is available in the environment that
  performs the acceptance — this document's Check-1-through-16 pass
  was obtained by calling the underlying functions directly via
  `python3 scripts/check_canon_0_8_0.py`, not through pytest.
- A human reviewer has worked through every item in section 5 and
  recorded agreement, in particular the three named divergences from
  the specification and the `finance_administrator` ×
  `organizational_administrator` incompatibility as an owner decision.
- `ADR-044` through `ADR-050` have moved from `proposed` to `accepted`
  by the repository's own ADR-acceptance process — this round
  explicitly does not perform that step (19f.25).
- No later round has silently widened what 19f.25 authorizes: any
  future round that adds `services/finance-service` or any other
  finance runtime artefact needs its own separate, gated,
  implementation round, measured against
  `docs/packs/PACK-10-ACCEPTANCE-MATRIX.md`, not against this
  document.
- The manual searches in section 4 have been re-run against the
  reviewed checkout, not merely trusted from this document's earlier
  run, since they are not yet wired into any repeatable script.

None of the above is a legal, tax, audit or regulatory determination.
"Accepted" here means only that the canon amendment is the model the
repository will build against next — it is a statement about
documentation, versioning and structural consistency, checked exactly
as far as sections 1 through 4 show and no further.

Passing every check in this document asserts nothing about legal
compliance, tax correctness, audit sufficiency or production
readiness. It asserts that a documented, internally consistent,
version-gated canon amendment exists and that no finance runtime
artefact was created alongside it — nothing more, and section 19f.25
and `ФИН-43`/`HI-46` say so explicitly.
