# PACK-10 — Party Finance Backend Implementation 0.10.0

Status: **PACK-10 PARTY FINANCE 0.10.0 CANDIDATE.** Not a PASS. Not a
claim of production, legal, banking or external-authority readiness
(`ФИН-43`).

This round implements the first executable slice of the party-finance
bounded context defined by canon 0.8.0 section 19f, as
`services/finance-service`. It amends no canon: `CANON_VERSION` stays
`0.8.0` and `docs/canonical/TZ-00-domain-event-canon.md` is byte-identical
to the 0.8.0 text. `REPOSITORY_VERSION` moves `0.9.0 → 0.10.0`, which a
new bounded context requires under canon section 25.

The cumulative baseline is `EPD2_FRONT-01_PACK-10_CANON_0.8.0_FINAL_PASS`
(730 files); this candidate has 764. Nothing in FRONT-00 or FRONT-01
was touched.

## 1. What shipped

`services/finance-service` — twelve modules, 20,355 lines, plus eleven
test files, 9,699 lines and 388 test functions (677 collected cases).

| Module          | Lines | Owns                                                                                                             |
| --------------- | ----: | ---------------------------------------------------------------------------------------------------------------- |
| `__init__`      |    64 | The package charter: what the context owns, what it is not, and the no-compliance-claim statement.               |
| `exceptions`    |   512 | One class per registered reason code. No domain knowledge.                                                       |
| `domain`        |   569 | `Money`, `FinancePartyHandle`, `OrganizationalScopeRef`, identity minimisation, pure invariant functions.        |
| `authorization` |   695 | Six finance roles, four action authorities, the canon 19f.14 incompatibility matrix, forty governed actions.     |
| `references`    |   705 | Typed, content-free references to PACK-09, PACK-11 and PACK-35 records, and the refusals that keep them out.     |
| `projections`   |  1032 | Derived, versioned, never-authoritative read models and statistical disclosure control.                          |
| `ledger`        |  1251 | Accounts, accounting periods, balanced double-entry postings, correction and reversal, the correction chain.     |
| `records`       |  1512 | Contributions, sponsorship, external benefit, expense claims, payments, assets, obligations, governed transfers. |
| `reporting`     |  1695 | Reporting obligation, perimeter, frozen snapshot, the twelve-state report lifecycle, the audit engagement.       |
| `storage`       |  1719 | Twenty-four storage ports with in-memory adapters, the idempotency store, the event sink. No delete method.      |
| `events`        |  4438 | All seventy-two canon 20.17 event builders and the full-state payloads Audit Core hashes.                        |
| `application`   |  6163 | Forty-two commands and five queries, each routed through one guard frame.                                        |

Also shipped: `contracts/reason-codes/pack-10.yml` (96 entries), six
architecture and pack documents, `docs/contracts/finance-command-query-contracts.md`,
and this report.

## 2. Changed-file manifest, relative to the cumulative baseline

Fifty paths differ: 34 added, 16 modified, 0 removed. Every one is
listed. Counted by recursive comparison against the extracted baseline
archive, not by recollection.

**Added — 34 files:**

- `services/finance-service/` — 26 files: README, `pyproject.toml`,
  twelve source modules, eleven test files.
- `contracts/reason-codes/pack-10.yml`.
- `docs/architecture/finance-service.md`,
  `finance-ledger-model.md`, `finance-reporting-lifecycle.md`,
  `finance-separation-of-duties.md`,
  `finance-publication-projection.md`.
- `docs/packs/PACK-10-IMPLEMENTATION.md`.
- `docs/contracts/finance-command-query-contracts.md` (new directory).
- `docs/handover/PACK-10-IMPLEMENTATION-REPORT.md` (this file).

**Modified — 16 files:**

| File                                                   | Change                                                                                       |
| ------------------------------------------------------ | -------------------------------------------------------------------------------------------- |
| `packages/python/epd2-core/src/epd2_core/version.py`   | `REPOSITORY_VERSION` `0.9.0 → 0.10.0`.                                                       |
| `packages/typescript/epd2-types/src/version.ts`        | Same.                                                                                        |
| `packages/python/epd2-core/tests/test_version.py`      | Expected repository version and the comment recording why it moved.                          |
| `packages/typescript/epd2-types/tests/version.test.ts` | Same.                                                                                        |
| `docs/canonical/canon-version.json`                    | Status `not_implemented → reference_implementation`; compatibility `<0.10.0 → <0.11.0`.      |
| `CHANGELOG.md`                                         | New `## [0.10.0]` entry.                                                                     |
| `pyproject.toml`                                       | Workspace member, dependency, uv source, ruff `src`, isort first-party, mypy path, testpath. |
| `uv.lock`                                              | The new workspace member. No dependency version changed.                                     |
| `Makefile`                                             | One `uv run mypy services/finance-service` line.                                             |
| `scripts/check_repository.py`                          | 33 new required paths.                                                                       |
| `scripts/check_canon_0_8_0.py`                         | Checks 2, 3, 4 follow the new version and status; check 5 inverted (section 5 below).        |
| `tests/repository/test_canon_0_8_0_amendment.py`       | Follows those four checks.                                                                   |
| `tests/repository/test_service_boundaries.py`          | Three new PACK-10 boundary tests.                                                            |
| `tests/contract/_schema_helpers.py`                    | `PACK10_REASON_CODES_PATH`, `PACK10_SERVICE_DIRS`.                                           |
| `tests/contract/test_reason_codes_registry.py`         | pack-10 added to the parametrized packs; one documented non-reason-code literal.             |
| `docs/architecture/data-ownership.md`                  | 21 finance rows: 17 to implemented, 4 to deferred.                                           |

**Not modified, verified byte-identical by recursive diff against the
baseline:** the whole of `frontend/` including all 45 committed visual
snapshots, `package-lock.json`, `frontend/web-shell/package.json`,
`docs/canonical/TZ-00-domain-event-canon.md`, and the whole of
`docs/adr/` — ADR-044 through ADR-054, all IDs still globally unique.

## 3. Verification actually executed in this environment

Every command below was run from the repository root and its real result
is reported.

```text
$ ruff check .
All checks passed!

$ ruff format --check .
242 files already formatted

$ mypy services/finance-service          # mypy 1.20.2, repo pyproject config
Success: no issues found in 23 source files

$ mypy packages/python/epd2-core scripts tests/repository conftest.py
Success: no issues found in 28 source files

$ python3 scripts/check_repository.py
OK: all 619 required paths are present.

$ python3 scripts/check_forbidden_files.py
OK: no forbidden paths found.

$ python3 scripts/verify_versions.py
OK: all version sources are consistent.

$ python3 scripts/check_canon_0_8_0.py
OK: all 17 canon 0.8.0 amendment checks passed.

$ uv lock --check
Resolved 56 packages

$ pytest -q                              # pytest 9.0.3
3354 passed, 5 skipped

$ prettier --check "**/*.md"             # prettier 3.8.1, see section 4
All matched files use Prettier code style!
  ... except docs/adr/ADR-051-...md - see below
```

The full `pytest` run includes the 677 collected finance cases, the
repository suite, and the PACK-02 through PACK-09 contract suite —
nothing was scoped down to make it pass.

## 4. Verification NOT executed, and not claimed

This sandbox has no npm-registry and no PyPI access (HTTP 403 /
unreachable). The following are **required in GitHub Actions** and were
not run here. None of them is claimed as passing:

- `npm ci`, and every command that depends on `node_modules`:
  `npm run typecheck`, `npm run lint`, `npm run test`, `npm run build`
  for `frontend/web-shell` and `packages/typescript/epd2-types`, the
  Playwright browser, accessibility and visual-snapshot suites.
- `make verify` end to end, `uv sync`, `uv run pytest`, `uv run mypy`.
- `prettier --check` **at the pinned 3.9.6**. Only 3.8.1 is installed
  here. The two known divergence surfaces between those versions are
  ambiguous `*`/`_` emphasis and TypeScript union wrapping; no document
  written this round uses inline emphasis, and no TypeScript file was
  reformatted, so the exposure is small — but it is not zero and is not
  claimed as verified.

  One file makes the divergence concrete, and it was deliberately left
  alone. `prettier` 3.8.1 reports
  `docs/adr/ADR-051-rechenschaftsbericht-lifecycle-snapshot-and-authority-semantics.md`
  as unformatted, wanting `no\*` where the file has `no*` in a table
  cell. That file is byte-identical to the cumulative baseline, which
  passed `prettier --check` at the pinned 3.9.6 in GitHub Actions run
  "Verify and Package #57". Rewriting it to satisfy the older local
  binary would break the pinned one. It is therefore reported here as a
  known local-only warning rather than fixed, and every other markdown
  file in the repository — 3.8.1 and the pinned version agreeing — passes
  clean.

- `hypothesis`-backed property tests (`tests/contract/test_property_based.py`)
  skip here for the same reason they have skipped since PACK-02: the
  package cannot be installed.

The Python interpreter that runs `pytest` in this sandbox needed
`PYTHONPATH` extended with the system `dist-packages` directory to see
PyYAML. That is a sandbox artefact, not a repository change; CI installs
PyYAML through `uv`.

## 5. The canon checker was inverted, deliberately

`scripts/check_canon_0_8_0.py` check 5 previously asserted that
`services/finance-service` did **not** exist, that being canon 19f.25's
implementation gate in its closed position. This round is the round the
gate was waiting for. Leaving the assertion in place would have made the
checker enforce the previous round's state permanently, and it would have
done so silently — a checker that passes tells you nothing about whether
it is still asking the right question.

`check_no_finance_runtime_implementation` was therefore replaced by
`check_finance_runtime_within_boundary`, which asserts the part of 19f.25
that did not change:

- `services/finance-service` exists and carries all twelve named
  modules — enumerated, so deleting one fails rather than shrinking the
  service unnoticed;
- no finance-named path exists under `packages/` or `frontend/` (canon
  19f.23's structural separation; no shared finance package, no
  operational finance frontend);
- no second finance-named service exists (canon 19f.1: one owner);
- no `def delete_`/`remove_`/`purge_`/`destroy_` appears anywhere in the
  package, except the two functions that exist only to raise
  (`ФИН-05`, `ФИН-22`).

Checks 2, 3 and 4 follow the new state: `REPOSITORY_VERSION` 0.10.0;
`repository_compatibility` widened to `<0.11.0`;
`minimum_repository_version` deliberately left at `0.9.0`, because it
records the version the amendment was made at and must not drift forward
with each round that implements it; and
`finance_context_implementation_status` set to
`reference_implementation`. That value was chosen over both adjacent
alternatives: `not_implemented` stopped being true the moment the service
shipped, and `implemented` would assert a production data plane this
round does not have.

## 6. Defects found in review, and fixed

The four domain modules and the events, storage, references, projections,
application and test layers were produced across several passes and were
reviewed against canon 19f and the accepted specification rather than
accepted as delivered. What that review found:

1. **`ReportState` did not use the canonical names.** The lifecycle
   carried the governing brief's section-10 vocabulary (`prepared`,
   `under_internal_review`, `internally_approved`, `audit_requested`,
   `audit_opinion_recorded`, `ready_for_external_submission`,
   `externally_submitted_reference_recorded`,
   `accepted_reference_recorded`, `correction_required`). Canon 19f.17
   defines all twelve states by name, and both the brief's own section 4
   ("where canon 0.8.0 is more specific, canon controls") and its
   section 10 ("use the exact canonical state names where already
   defined") point the same way. The enum now carries the canon names,
   and `reporting.OPERATIONAL_STATE_SYNONYMS` records the brief's
   vocabulary as a documented translation — including the two entries
   that map to no state at all, because `audit_requested` opens a
   separate aggregate and a correction request is a record on the
   version rather than a status of it. The transition graph, the
   immutable-state set, the guarded publication path and eight methods
   were rewritten with it.
2. **`require_timezone` refused a naive datetime with a monetary reason
   code.** A time defect was being reported as `FINANCE_MONETARY_AMOUNT_INVALID`.
   It now raises `FINANCE_ACCOUNTING_PERIOD_UNDETERMINED`, which canon
   section 24 defines as "no period, or no timezone-explicit period,
   could be determined".
3. **`ACTION_REQUIREMENTS` was too small for the command surface**, so
   nine commands borrowed a neighbouring action's key. Two of those
   borrowings were weaker than canon requires: import-batch registration
   inherited posting authority (canon 19f.6 separates ingestion), and
   write-off inherited the authority to record an obligation (canon
   19f.11 names a distinct write-off authority). Seven entries were
   added — `manage_chart_of_accounts`, `register_import_batch`,
   `reclassify_transaction`, `return_contribution`,
   `record_external_benefit`, `write_off_position`, `sign_report`,
   `record_auditor_review`, `mint_party_handle` — and the command map
   was repointed at them. `sign_report` permits the `report_signatory`
   alone: nobody signs a statutory report on the strength of an
   administrative role. `record_auditor_review` deliberately excludes
   `finance_auditor`, because canon 19f.18 forbids the audit contour
   writing into an aggregate it audits.
4. **The party-handle resolution role code was declared twice**, in
   `authorization` and again in `application`. Two sources of truth for
   one privilege is exactly how they drift apart; the second is now a
   re-export.
5. **Three stale claims inside the code.** Three comments described
   `ACTION_REQUIREMENTS` as holding "thirty-one" actions when it held
   forty; four files cited an "ADR-055" that does not exist (the
   decomposition decision is ADR-048); and `write_off_financial_obligation`'s
   docstring justified its dual control as compensating for a missing
   table entry that now exists. All corrected, and recorded in
   `docs/packs/PACK-10-IMPLEMENTATION.md` section 5.4 rather than
   quietly cleaned up.
6. **Three lint defects in `domain.py`** (two over-length lines, one
   ambiguous-Unicode comment) that had been reported clean in an earlier
   pass. They were not clean; `ruff check` is now green over the whole
   repository.

## 7. Deliberate deviations from the implementation plan

`docs/packs/PACK-10-IMPLEMENTATION-PLAN.md` proposed a larger module
split (`imports.py`, `policy.py`, `partyregistry.py`, `contributions.py`,
`expenses.py`, `positions.py`, `budgets.py`, `audit_engagement.py`). This
round shipped twelve modules instead, matching the brief's own module
list. Three of the plan's proposed architecture tests were import-boundary
rules between modules that now do not exist; what replaced each is stated
in `PACK-10-IMPLEMENTATION.md` section 5.1, including the one place the
replacement is genuinely weaker — nothing structural now prevents a
future function in `application.py` from reaching `FinancePartyHandleStore`
directly, where a separate `partyregistry.py` would have made it an
import violation.

The plan also named `contracts/openapi/pack-10.yaml` and a per-entity
JSON Schema set. Neither was created. This round exposes no HTTP surface,
and an OpenAPI document describing endpoints that do not exist would make
the contract suite assert against nothing runnable.

## 8. Deferred, and stated as such

Canon 19f.1 names twenty-one authoritative aggregates. Sixteen exist as
aggregates in this round. The five that do not:

- **`Budget`** — the two `budget.*` event builders and
  `BudgetSummaryProjection` exist and take typed arguments; there is no
  aggregate and no command. `ФИН-12` (a budget never overwrites register
  facts) is enforced structurally instead: the projection has no field
  for an actual amount.
- **`ReconciliationRecord`** — the `reconciliation.recorded` builder
  exists; the aggregate does not.
- **`FinancePolicy`** — policy versions are held as `PolicyBinding`
  references on the records that were decided under them, which keeps
  `ФИН-23` (historical versions stay bound to historical decisions)
  true; there is no policy aggregate, and `GOVERNED_CURRENCIES` is
  consequently the fixed set `{"EUR"}` rather than a policy-resolved one.
- **`ImportBatch`** — shipped as `storage.ImportBatchRecord`, an
  infrastructure record of an ingestion act rather than a canonical
  aggregate. This is a judgement made against the canon's own list and
  is flagged as such.
- **`FinanceReport`** — the series identity. Only `FinanceReportVersion`
  exists, carrying a `report_id`.

Also deferred: twenty-six of the seventy-two event builders have no
command yet (enumerated by name in `PACK-10-IMPLEMENTATION.md`);
`PublicationAuthorization` and `ReportingPerimeterDefinition` have no
creating command; consolidation has no command, though `GovernedTransfer`
pairing exists so elimination is possible later; and the five queries
take no action authority, being gated by scope alone.

And, categorically: no production persistence, no event bus, no bank or
payment-provider integration, no external-authority submission channel,
no operational finance frontend. Every storage adapter is in-memory and
PACK-13 owns the production data plane.

## 9. Invariant coverage

`services/finance-service/tests/test_domain.py` carries
`FIN_INVARIANT_COVERAGE`, a map from each of `ФИН-01` through `ФИН-45` to
the test function that proves it, and three tests police the map itself:
that all forty-five are present, that every named test actually exists in
the suite, and that every uncovered entry states a reason instead of
being omitted.

Forty-four of forty-five are covered by an executable test. The
exception is **`ФИН-43`** — "no claim of legal compliance, authority
acceptance or operational readiness follows from this section" — which is
a rule about what humans may assert about the system, and which no code
path can prove or disprove. It is recorded in the package docstring, in
the service README, and in this report.

Four of the forty-four are proved structurally rather than behaviourally,
and the map says so: `ФИН-12` by the absence of an actual-amount field on
the budget projection; `ФИН-37` by an authority scoped elsewhere being
refused, there being no consolidation command to test; `ФИН-42` by an AST
scan proving no function in the package accepts a bypass-flag parameter;
`ФИН-44` by an AST import scan proving the package's first-party import
set is exactly `{epd2_core, epd2_audit_core, epd2_finance_service}`.

## 10. What a reviewer should check first

1. That check 5 of the canon checker was inverted for the right reason
   (section 5 above) and not to make a failing assertion pass.
2. `reporting.ReportState` and `OPERATIONAL_STATE_SYNONYMS` against canon
   19f.17 — this is the largest single judgement call in the round.
3. The nine `ACTION_REQUIREMENTS` entries added in review, against canon
   19f.14, and the twelve command-to-action mappings that did not change.
4. `contracts/reason-codes/pack-10.yml`'s forty-five canon entries
   against canon section 24, and the nineteen additive entries against
   the argument in each `meaning` for why the nearest canon code would
   have been wrong.
5. The deferral list in section 8 against canon 19f.1 — specifically
   whether `ImportBatch` as an infrastructure record is acceptable.

## 11. Archive identity

| Archive                                                 | SHA-256                                                            |
| ------------------------------------------------------- | ------------------------------------------------------------------ |
| `EPD2_FRONT-01_PACK-10_CANON_0.8.0_FINAL_PASS.zip` (in) | `5ad93c2e292f623c9d68a2c4d7df91bc6e32c5cab679d0378383deed9319e731` |
| `EPD2_PACK-10_SPECIFICATION_0.10.0_CANDIDATE.zip` (in)  | `6df589bea37d9384df12ffc50edddd94ce713d4cb692893c86e2589e1ae9a01b` |
| `EPD2_PACK-10_PARTY_FINANCE_0.10.0_CANDIDATE.zip` (out) | reported in the delivery message                                   |

The output archive's own SHA-256 cannot appear inside it: writing the
hash into a file that the hash covers changes the hash. It is therefore
reported in the delivery message accompanying this archive, computed
after packaging, and it is the value to check the download against.

The archive was verified by extracting it to a clean directory and
running a recursive byte comparison against the staged tree — 764 files,
zero differences — and then re-running `check_repository.py`,
`check_forbidden_files.py`, `verify_versions.py` and
`check_canon_0_8_0.py` against the extracted copy rather than the
staged one, so the checks answer for what was actually shipped. The
extracted tree carries all 45 committed visual snapshots and all 54 ADR
files.

## 12. Status

**PACK-10 PARTY FINANCE 0.10.0 CANDIDATE.** Not a PASS. The network-
dependent half of the verification matrix (section 4) has not been run
anywhere yet, and until GitHub Actions has run `make verify` against this
tree, no PASS claim would be supportable.
