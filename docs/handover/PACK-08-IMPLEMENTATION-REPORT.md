# CLAUDE-PACK-08 — Organization & Regional Scope Foundation: Implementation Handover Report

Status: **local self-report only. No external GitHub Actions run was
performed or is claimed for this implementation round.** This report
records exactly what was run in this sandbox, exactly what could not be
run here (and why — the same documented no-network limitation as every
prior pack), and exactly what passed, failed, or was skipped. Nothing
below is rounded up to "0 real failures" language where a real gap
exists.

This report covers the **implementation round** that follows
`docs/handover/PACK-08-CANON-AMENDMENT-REPORT.md` (the canon-only round
that accepted ADR-037 and raised `CANON_VERSION` to `0.7.0`, with
`REPOSITORY_VERSION` deliberately left at `0.7.0` at the time, since no
organization-service code existed yet). This round implements the
accepted canon 19e text and ADR-032 through ADR-037 against real service
code and raises `REPOSITORY_VERSION` to `0.8.0`. `CANON_VERSION` is
unchanged.

## 0. What this round adds

See `docs/packs/PACK-08-IMPLEMENTATION.md` for the full technical
reference. In summary:

- A new, independent, in-memory-backed service, **`organization-service`**
  (`Organization`, `OrganizationalUnit`, `CivicSpace`,
  `OrganizationalRelation`, `OrganizationalHierarchyOverlapPolicy`,
  `OrganizationalInheritancePolicy`, `OrganizationalAuthority`, plus the
  `OrganizationalScope` value shape) — the sole authoritative owner of
  every canon 19e entity.
- The default-deny regional scope authorization engine (six access
  modes), temporary supervision (90-day default maximum), institutional
  authority assignments with the eight-rule role-incompatibility
  baseline, and role/authority lifecycle rules.
- The mandatory `RoleAssignment.scope_id` migration table
  (`docs/packs/PACK-08-ROLE-SCOPE-MIGRATION-TABLE.md`), produced by
  inspecting all 12 real `role_code` values in the repository before any
  migration behavior was implemented — zero blocked, zero ambiguous.
- Thirteen canon 20.5 events, 32 reason codes, 5 entity + 6 event-payload
  JSON Schemas, a 9-operation minimal reference OpenAPI spec (explicitly
  no bulk cross-regional directory, no public member directory, no
  lifecycle-transition HTTP path).
- A minimal, read-only, accessible frontend vertical slice under
  `frontend/web-shell/app/organizations/*` — static sample data only,
  German-authoritative/English-informational, no backend connection.
- The `REPOSITORY_VERSION 0.7.0 -> 0.8.0` bump, with `CANON_VERSION`
  unchanged at `0.7.0` and the canon checksum unchanged (no canon-owned
  file was touched this round).

## 1. Environment and network status

Same sandbox, same limitation as every prior pack (see
`LOCAL_VERIFICATION.md`): no live PyPI/npm registry access. Both
`npm install` and `npm install --offline` were attempted fresh this round
and both fail (`E403 Forbidden` / `ENOTCACHED` respectively) — confirming
this is the same no-network ceiling documented for PACK-01 through
PACK-07, not a new one.

Python verification used the established workaround: standalone
`pytest`/`mypy`/`ruff` binaries at `/root/.local/bin/` (isolated
`uv`-tool installs with no project dependencies), with `PYTHONPATH`
pointed at every service's `src/` and every Python package's `src/`, plus
the system `dist-packages` directory for PyYAML. `hypothesis` remains
unavailable this way, so `test_property_based.py` still skips, unchanged
from every prior pack.

TypeScript verification used a different, narrower workaround this
round: a global `tsx` binary (`/home/claude/.npm-global/lib/node_modules/tsx`)
and a global TypeScript compiler (`typescript@6.0.3`, via
`/home/claude/.npm-global/bin/tsc`) let unit tests run
(`node --import <tsx-loader> --test tests/*.test.ts`) and let a type-check
pass run (`tsc --noEmit -p tsconfig.json`) without the project's own
`node_modules`. This surfaces real project-code type errors correctly (it
caught and led to a genuine fix — see section 3) but also reports a large
number of `Cannot find module 'next'/'react'` and `JSX.IntrinsicElements`
errors that come purely from the missing, project-pinned `@types/react`/
`next` packages, not from this round's code; these are filtered out
explicitly in section 6b's reported command and are the same class of
gap PACK-07 reported as "not run in this sandbox" for the whole
TypeScript/lint/build surface. ESLint and Prettier both have a global
binary available in this sandbox (`/opt/node22/bin/{eslint,prettier}`);
Prettier ran successfully against the new frontend files (see section
6b). ESLint could not run: `eslint.config.mjs` imports `@eslint/eslintrc`,
a project dependency not present without `node_modules`, so ESLint fails
immediately with `ERR_MODULE_NOT_FOUND`. The Next.js production build
requires the project's own `next` binary and also could not run. Neither
is claimed as passing from this local run.

## 2. Canon integrity

No canon edit was made this round. `docs/canonical/TZ-00-domain-event-canon.md`
is untouched; `CANON_VERSION` stays `0.7.0` in every source
(`packages/python/epd2-core/src/epd2_core/version.py`,
`packages/typescript/epd2-types/src/version.ts`,
`docs/canonical/canon-version.json`). Checksum
(`sha256sum docs/canonical/TZ-00-domain-event-canon.md`):
`a16341a66ce39514e6d8cd6d7a6dde8fc37b0430e3e9ddd7bfd284b116cb9072` —
identical to the value recorded at the end of the canon-amendment round.
This is purely an implementation round against already-accepted text.

## 3. Bug found and fixed during implementation

`would_create_hierarchy_cycle` in `domain.py` originally searched in the
wrong direction (see `docs/packs/PACK-08-IMPLEMENTATION.md` section 3 for
the full explanation and the inline code comment). Found via two failing
tests (`test_forbidden_hierarchical_cycle_detected`,
`test_forbidden_hierarchical_cycle_rejected_end_to_end`), fixed by
swapping the BFS start node and search target, re-verified against the
full `organization-service` test suite (all passing after the fix, see
section 6b). `would_create_supervision_cycle` needed no fix.

A second, narrower issue was a `mypy`-only gap, not a runtime bug:
31 test functions in `test_application.py` were missing parameter type
annotations, caught only by the correct per-service `mypy` invocation
(`mypy services/organization-service`, checking the whole service
directory including `tests/`) rather than a `src`-only invocation. Fixed
by adding explicit fixture/parameter types, following this repository's
own established `**overrides: object` + `# type: ignore[arg-type]`
pattern from `credential-service`'s and `ai-processing-service`'s test
suites.

## 4. Architectural / scope decisions confirmed during this round

- **Lifecycle-transition commands are deliberately absent from
  `contracts/openapi/pack-08.yaml`.** Activation, suspension, dissolution,
  merge, split, and successor declaration remain internal
  application-layer functions only — no public HTTP-shaped path — a
  narrower scope decision than a full administration API, consistent with
  the governing task's explicit "minimal reference OpenAPI" instruction
  and tested for directly
  (`test_pack08_lifecycle_transition_commands_have_no_openapi_path`).
- **No bulk cross-regional directory, no public member directory** — both
  explicitly excluded from the OpenAPI spec
  (`test_pack08_no_bulk_cross_regional_directory_endpoint`) and from the
  frontend vertical slice (organization browser is a flat, in-page table
  over sample data only, not a queryable directory service).
- **Cross-cutting aggregator test files from earlier packs were not
  extended.** `test_state_transitions.py`, `test_audit.py`, and similar
  repo-wide files were not given a new PACK-08 section; this pack's own
  transition/audit behavior is exercised by its own
  `services/organization-service/tests/{test_domain,test_application,test_storage}.py`
  instead. This mirrors earlier packs' own precedent of not universally
  extending every cross-cutting file every round (e.g. PACK-06's
  not-applicable markers in `test_ct00_10_rule_freeze.py`).
- **The pre-existing `scripts/check_repository.py` `REQUIRED_PATHS` gap
  for PACK-07's own handover/review/ADR docs was documented, not
  backfilled.** Only this round's own new paths were added to
  `REQUIRED_PATHS`. Retroactively fixing an earlier round's gap was
  judged out of scope for an implementation round governed by its own
  30-item task list.
- **`docs/architecture/system-context.md` and
  `docs/architecture/service-boundaries.md` were reviewed and left
  unchanged** — see `docs/packs/PACK-08-IMPLEMENTATION.md` section 8 for
  the reasoning (both documents were already accurate at the level they
  operate at, or were never extended by any implementation pack since
  PACK-02, so a PACK-08-only addition would have been inconsistent with
  established practice rather than a continuation of it).

## 5. Files added or changed this round

**New service** (`services/organization-service/`): `README.md`,
`pyproject.toml`, `src/epd2_organization_service/{__init__,domain,
application,events,exceptions,storage}.py`,
`tests/{test_domain,test_application,test_storage}.py`.

**Contracts**: `contracts/reason-codes/pack-08.yml` (32 entries);
`contracts/schemas/{organization,organizational-unit,civic-space,
organizational-relation,organizational-authority}.schema.json` (5 new
entity schemas); `contracts/events/{organization-status-payload,
organizational-relation-created-payload,organizational-relation-ended-payload,
organizational-authority-assigned-payload,organizational-authority-revoked-payload,
regional-scope-access-granted-payload,regional-scope-access-revoked-payload}.v1.schema.json`
(6 new event-payload schemas covering 13 event types);
`contracts/openapi/pack-08.yaml` (new, 9 operations, tag
`organization-service`).

**Cross-service tests**: `tests/repository/test_service_boundaries.py`
(extended: 3 new PACK-08 boundary tests); `tests/contract/_schema_helpers.py`,
`test_reason_codes_registry.py`, `test_openapi_contract.py` (each extended
for the new PACK-08 registry/spec files, 4 + 5 new tests respectively);
`tests/contract/test_ct00_01_pack08_schema_validation.py` (new, 12 tests).

**Documentation**: `docs/packs/{PACK-08-ROLE-SCOPE-MIGRATION-TABLE,
PACK-08-IMPLEMENTATION}.md` (new); `docs/packs/PACK-08-OPEN-DECISIONS.md`
(OD-11 closed out); `docs/architecture/data-ownership.md` (Organization/
CivicSpace marked implemented, 5 new PACK-08 rows added, pre-existing gap
for PACK-03–PACK-07 rows documented honestly); `frontend/README.md`,
`frontend/web-shell/README.md` (updated for the new vertical slice); this
report.

**Frontend vertical slice**
(`frontend/web-shell/app/organizations/`): `data.ts`, `labels.ts`,
`authorization.ts`, `Bilingual.tsx`, `AsOfSelector.tsx`, `page.tsx`,
`[id]/page.tsx`, `dev-authorization-console/page.tsx`;
`frontend/web-shell/app/globals.css` (extended with table/accessibility/
focus-visible styles); `frontend/web-shell/tests/organizations.test.ts`
(new, 9 tests).

**Repository infrastructure**: `scripts/check_repository.py`
(`REQUIRED_PATHS` extended with every file above);
`packages/python/epd2-core/src/epd2_core/version.py`,
`packages/typescript/epd2-types/src/version.ts`, both version-consistency
unit tests (`REPOSITORY_VERSION` assertion moved to `0.8.0`),
`docs/canonical/canon-version.json` (`repository_compatibility` upper
bound widened `<0.8.0 -> <0.9.0`); `CHANGELOG.md` (new `[0.8.0]` entry).

## 6. Verification performed this round

### 6a. External verification

Not performed, not claimed. This is a local sandbox self-report only, per
this round's own honest-reporting requirement.

### 6b. Local verification performed during implementation

Commands (from repository root):

```bash
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH=$(python3 -c "
import glob
paths = glob.glob('services/*/src') + glob.glob('packages/python/*/src')
print(':'.join(paths))
"):/usr/local/lib/python3.11/dist-packages

/root/.local/bin/ruff check --no-cache .
/root/.local/bin/ruff format --no-cache --check .
/root/.local/bin/mypy --cache-dir=/dev/null packages/python/epd2-core scripts tests/repository conftest.py
MYPYPATH="$PYTHONPATH" /root/.local/bin/mypy --cache-dir=/dev/null tests/contract
for svc in services/*/; do /root/.local/bin/mypy --cache-dir=/dev/null "$svc"; done   # one invocation per service, 16 total
/root/.local/bin/pytest -p no:cacheprovider packages/python/epd2-core tests/repository -q
/root/.local/bin/pytest -p no:cacheprovider tests/contract -q
/root/.local/bin/pytest -p no:cacheprovider services -q
python3 scripts/check_repository.py
python3 scripts/verify_versions.py

# TypeScript (see section 1 for the narrower workaround used this round)
cd frontend/web-shell
node --import /home/claude/.npm-global/lib/node_modules/tsx/dist/loader.mjs --test tests/*.test.ts
PATH=/home/claude/.npm-global/bin:$PATH tsc --noEmit -p tsconfig.json   # then filter out missing-dependency-only errors, see section 1
PATH=/opt/node22/bin:$PATH prettier --check 'app/**/*.{ts,tsx}' 'tests/**/*.ts'
```

Results:

- **Ruff (lint):** clean, whole repository (`All checks passed!`).
- **Ruff (format):** clean, whole repository (196 files already
  formatted).
- **mypy:** `Success: no issues found` for core/scripts/repository-tests
  (25 files), `tests/contract` (21 files, with `MYPYPATH` set to every
  service's `src/`), and all 16 services individually (mypy invoked once
  per service directory, including its own `tests/`, per this
  repository's documented `Makefile` convention).
- **Python tests:** `packages/python/epd2-core` + `tests/repository`:
  **98 passed, 0 failed** (the one `test_no_required_paths_are_missing`
  failure observed mid-session, before this report and
  `docs/packs/PACK-08-IMPLEMENTATION.md` existed, is resolved now that
  both files are present). `tests/contract`: **936 passed, 5 skipped**
  (the same `hypothesis`-unavailable skip and the same four pre-existing
  CT-00-10/11/12 not-applicable markers as every prior pack — none of
  them PACK-08-specific). `services/*`: **1107 passed**. **Total: 2141
  passed, 5 skipped, 0 failed.**
- **`scripts/check_repository.py`:** all required paths present
  (including this report and `docs/packs/PACK-08-IMPLEMENTATION.md`); no
  forbidden paths reported by the script itself.
- **`scripts/verify_versions.py`:** `OK: all version sources are
consistent.` (`CANON_VERSION 0.7.0` / `REPOSITORY_VERSION 0.8.0`
  everywhere they are declared, including the corrected `CHANGELOG.md`
  `## [0.8.0]` heading placement).
- **TypeScript unit tests (frontend):** **11 passed, 0 failed** (2
  pre-existing `smoke.test.ts` tests + 9 new `organizations.test.ts`
  tests), run via a global `tsx` loader binary (no project `node_modules`
  — see section 1).
- **TypeScript type-check (frontend):** `tsc --noEmit` reported errors
  only of the `Cannot find module 'react'/'next'` /
  `JSX.IntrinsicElements` / implicit-`any`-parameter kind, traceable
  entirely to the missing, project-pinned `@types/react`/`next` packages
  (no `node_modules` — see section 1); after filtering those out, **zero
  genuine type errors** in this round's new code. One genuine type issue
  this check _did_ surface and that was fixed for real (not filtered
  out): an `'organization' is possibly 'undefined'` narrowing gap after
  `notFound()` in `app/organizations/[id]/page.tsx`, fixed by adding an
  explicit `return null;` after the `notFound()` call so control-flow
  narrowing does not depend on `next/navigation`'s (unavailable, in this
  sandbox) `never`-typed return signature.
- **Prettier (frontend, new files only):** clean after one
  `prettier --write` pass; `prettier --check` now reports "All matched
  files use Prettier code style!" across `app/**/*.{ts,tsx}` and
  `tests/**/*.ts`.
- **ESLint, Next.js production build (frontend):** **not run** in this
  sandbox. `eslint.config.mjs` requires `@eslint/eslintrc` (a project
  dependency, absent without `node_modules`) even though a global
  `eslint` binary exists; the Next.js build requires the project's own
  `next` binary. Both `npm install` and `npm install --offline` were
  attempted fresh this round and both fail (section 1) — the same
  no-network ceiling documented for every prior pack. Not claimed as
  passing from this local run.

This is an honest local self-report, not an external GitHub Actions PASS.
Whoever runs this round's real CI should expect the TypeScript/ESLint/
Next.js-build gap above to close automatically (real `npm install`
resolves the missing packages, exactly as it did for PACK-07's own
external run — see `docs/handover/PACK-07-IMPLEMENTATION-REPORT.md`
section 6a).

## 7. ADR-032 through ADR-037: satisfied?

Yes, all six. ADR-032 (Organization/CivicSpace as canon 19e's foundation,
no new bounded context beyond organization-service) — satisfied: a single
new service owns every canon 19e entity. ADR-033 (multiple typed directed
graphs, not a tree) — satisfied: `RelationType`'s nine values across
three categories, no single-parent-tree constraint anywhere in
`domain.py`. ADR-034 (inheritance policy ownership/versioning, temporary
supervision mandatory `valid_until` + 90-day default) — satisfied:
`OrganizationalInheritancePolicy`, `TEMPORARY_SUPERVISION_DEFAULT_MAX_DAYS`.
ADR-035 (`RoleAssignment.scope_id` six-category classification scheme) —
satisfied: `docs/packs/PACK-08-ROLE-SCOPE-MIGRATION-TABLE.md`'s full
classification of all 12 real values. ADR-036 (eight-rule institutional
role incompatibility baseline) — satisfied: `PAIRWISE_INCOMPATIBLE_ROLES`,
version `"1.0"`. ADR-037 (canon 19e field-name reconciliation, e.g.
`OrganizationalAuthority`'s `role_code`/`scope`/`scope_type` naming) —
satisfied: `domain.py` uses exactly the canon-reconciled names throughout.

## 8. Was any scope deferred?

Yes, three items, all deliberate and all documented in section 4 and in
`docs/packs/PACK-08-IMPLEMENTATION.md` section 8: lifecycle-transition
commands have no public OpenAPI path; cross-cutting aggregator test files
from earlier packs were not extended with a PACK-08 section (this pack's
own equivalent coverage lives in its own service test suite instead); the
pre-existing PACK-07 `REQUIRED_PATHS` gap was documented, not backfilled.
No production claim is made anywhere in this round — this remains an
in-memory reference implementation, explicitly not backed by a
production database (see `docs/review/KNOWN_LIMITATIONS.md`'s
established pattern). No legal or security blocker was found during this
round.

## 9. Deliverables

- `docs/handover/PACK-08-IMPLEMENTATION-REPORT.md` (this file).
- `docs/packs/PACK-08-IMPLEMENTATION.md` (technical reference).
- `README.md`, `CHANGELOG.md` (updated).
- `epd2-civic-os-PACK-08-IMPLEMENTATION-0.8.0-CANDIDATE.zip` — one
  complete, clean archive (excludes `.git/`, `node_modules/`, `.venv/`,
  `__pycache__/`, `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`,
  frontend build output, verification-result ZIPs, nested ZIPs, and
  temporary logs/machine-specific artifacts). **Deliberately not labeled
  "PASS"** — this is a local self-report, not an externally-verified
  result, per this round's own required-scope instruction.
- Superseded, for CI purposes, by
  `epd2-civic-os-PACK-08-IMPLEMENTATION-0.8.0-CI-CANDIDATE.zip` — see
  section 10.

## 10. Migration table correction (post-implementation, pre-CI)

**Targeted correction round, 2026-07-25, "PACK-08 MIGRATION TABLE
CORRECTION."** Before this round's archive was sent to external CI, a
review of `docs/packs/PACK-08-ROLE-SCOPE-MIGRATION-TABLE.md` section 2.7
found that its classification of `oversight_reviewer` was represented
incorrectly: the role_code was given a single row asserting two scope
classes ("dual — 5 for X, 4 for Y") as though the role_code alone
determined scope. It does not. Scope classification for
`oversight_reviewer` depends on the governed assignment context —
specifically, which `GovernanceDecision.decision_type` the particular
`RoleAssignment` grant is being exercised for. This was corrected in
place:

- Section 2.7 is now two context-specific rows, 2.7.1
  (`decision_type` ∈ {`MANDATE`, `OVERSIGHT_DIRECTIVE`} → category 5,
  global/system) and 2.7.2 (`decision_type` = `RESULT_FINALITY_DETERMINATION`
  → category 4, process-local), each carrying its own source/context,
  current meaning, target scope class, canonical owner, migration
  action, compatibility rule, authorization impact, event impact, API
  impact, and test requirement.
- The section 3 summary table gained an explicit **Context key** column,
  filled in for every row (`n/a (single context)` for the eleven
  single-context role_codes, the explicit `decision_type` value for each
  of the two `oversight_reviewer` rows) — so "no context key needed" is
  itself a recorded finding for every row, not a silent omission for the
  eleven and a special case only for the twelfth.
- `docs/packs/PACK-08-OPEN-DECISIONS.md` (OD-11's closing paragraph) and
  `docs/packs/PACK-08-IMPLEMENTATION.md` (section 2) were updated to
  match — neither now describes `oversight_reviewer` as a single "dual
  classification" row.
- A stray internal cross-reference in the migration table's own section
  2.6 (`governance_reviewer`), which pointed at "`oversight_reviewer`
  (2.9 below)" — an incorrect section number even before this
  correction — was fixed to point at the correct section (2.7).

**Explicitly stated, per this correction's own requirement:** `role_code`
alone is insufficient to determine scope; scope classification depends
on the governed assignment context; no downstream service may infer
scope from the role_code name alone; this is **not a blocking
ambiguity** after the context-specific split — both 2.7.1 and 2.7.2 are
fully pinned down by existing source, not unknowns.

**Unchanged by this correction, verified explicitly:**
`REPOSITORY_VERSION` (`0.8.0`), `CANON_VERSION` (`0.7.0`), the canon
checksum (`a16341a66ce39514e6d8cd6d7a6dde8fc37b0430e3e9ddd7bfd284b116cb9072`),
every ADR-032–037 status (all remain `accepted`), and all implementation
code (`services/organization-service/`, `governance-service`,
`ai-processing-service` — none of these were touched; this is a
documentation-only correction to how an already-correct, already-
implemented dispatch behavior is _described_, not a change to that
behavior itself).

**Documentation and repository checks re-run honestly after this
correction** (same commands as section 6b, re-executed from a clean
cache state):

- `python3 scripts/check_repository.py` → `OK: all 445 required paths
are present.` (unchanged path count — this correction edited existing
  required files, added none).
- `python3 scripts/verify_versions.py` → `OK: all version sources are
consistent.`
- `python3 scripts/check_forbidden_files.py` → `OK: no forbidden paths
found.`
- `/root/.local/bin/pytest -p no:cacheprovider packages/python/epd2-core
tests/repository tests/contract services -q` → **2141 passed, 5
  skipped, 0 failed** — identical to section 6b's figures, as expected:
  this correction touched only Markdown documentation, no test, schema,
  or source file, so no Python test outcome could change.
- `/root/.local/bin/ruff check --no-cache .` /
  `/root/.local/bin/ruff format --no-cache --check .` → both clean,
  unchanged from section 6b (Markdown is outside Ruff's scope).
- Frontend TypeScript unit tests (`node --import <tsx-loader> --test
tests/*.test.ts`) → **11 passed, 0 failed**, unchanged from section 6b
  — no frontend file was touched by this correction.

**New archive:** `epd2-civic-os-PACK-08-IMPLEMENTATION-0.8.0-CI-CANDIDATE.zip`
— rebuilt with the same exclusions as the original CANDIDATE archive
(section 9), all caches cleaned immediately before packaging, extracted
copy independently re-verified. Contains exactly four changed files
relative to the original CANDIDATE archive:
`docs/packs/PACK-08-ROLE-SCOPE-MIGRATION-TABLE.md`,
`docs/packs/PACK-08-OPEN-DECISIONS.md`,
`docs/packs/PACK-08-IMPLEMENTATION.md`, and this report — no
implementation code, contract, schema, test, or version/checksum file
differs from the CANDIDATE archive. Still deliberately not labeled
"PASS": this remains a local self-report; the "CI-CANDIDATE" name
reflects only that this is the archive intended for submission to
external CI next, not that CI has run.
