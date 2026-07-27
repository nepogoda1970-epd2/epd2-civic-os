# CLAUDE-PACK-10 — Canon 0.8.0: Cumulative Frontend Baseline Rebase Report

Status: **PACK-10 CANON 0.8.0 CANDIDATE-4.** A cumulative rebase of the
PACK-10 canon amendment onto the FRONT-01 public-website baseline. Not a
PASS: the frontend pipeline that this rebase exists to unblock cannot be
executed in the preparation environment (section 7), and ADR-048 through
ADR-054 remain `proposed`.

## 1. Source baselines

| Role                              | Archive                                               | SHA-256                                                                                                                                                         |
| --------------------------------- | ----------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Authoritative cumulative baseline | `EPD2_FRONT-01_PUBLIC_WEBSITE_0.2.0_CANDIDATE-2.zip`  | `d7a11d9d0f818238421b31620c314a7e4f6c99c8c5ffcf594e13c2e5b5c18e96`                                                                                              |
| Canon amendment being rebased     | `EPD2_PACK-10_CANON_0.8.0_CANDIDATE-3.zip`            | `e7a77f240f80fc4cd836e6ab1584967c6961f4f34eb1fa0f9b50d3e448f09ddf`                                                                                              |
| Common ancestor of both           | `epd2-civic-os-PACK-09-IMPLEMENTATION-0.9.0-PASS.zip` | (the PACK-09 FINAL PASS baseline both rounds were cut from)                                                                                                     |
| Result                            | `EPD2_PACK-10_CANON_0.8.0_CANDIDATE-4.zip`            | stated in the delivery message — an archive cannot contain its own hash; the per-file manifest in section 5 is what makes its contents independently verifiable |

File counts: FRONT-01 CANDIDATE-2 706 files → CANDIDATE-4 **728 files**
(+21 PACK-10 files, +1 this report, 0 removed).

## 2. Root cause of the overwritten manifests

Both rounds were cut from the same PACK-09 `0.9.0` FINAL PASS baseline
and never met:

- **FRONT-01** advanced `frontend/**`, `docs/frontend/**`,
  `frontend/web-shell/package.json`, the root `package-lock.json`,
  `scripts/check_repository.py`, the CI workflow and four frontend ADRs.
- **PACK-10** advanced the canon, the canon version, the version
  constants and the PACK-10 document set. It changed **no npm manifest at
  all**.

CANDIDATE-3 was therefore not a repository that overwrote FRONT-01's
dependency state with a _different_ one: it was a repository that still
carried the **pre-FRONT-01** frontend tree, because FRONT-01 did not
exist in its baseline. Delivering it as the newest archive silently
reverted FRONT-01, and the TypeScript step failed on the FRONT-01 config
files it had (`playwright.config.ts`, `vitest.config.ts` — absent) and
the dependencies it did not (`@playwright/test`, `@sparticuz/chromium`,
`vitest/config`, `@vitejs/plugin-react`).

The correct repair is a rebase, not a patch: start from FRONT-01, apply
the PACK-10 delta. Patching the five TypeScript errors individually
would have left the rest of FRONT-01 — 31 routes, 45 snapshots, the
component and browser test infrastructure — still missing.

## 3. Dependency differences (old PACK-10 frontend vs FRONT-01)

`frontend/web-shell/package.json` in CANDIDATE-3 (i.e. the PACK-09-era
manifest) versus FRONT-01's, which CANDIDATE-4 keeps byte-identical:

| Item                                                                                         | Old PACK-10 (PACK-09-era)                     | FRONT-01 / CANDIDATE-4                                      |
| -------------------------------------------------------------------------------------------- | --------------------------------------------- | ----------------------------------------------------------- |
| `@axe-core/playwright`                                                                       | absent                                        | `^4.12.1`                                                   |
| `@playwright/test`                                                                           | absent                                        | `^1.62.0`                                                   |
| `@sparticuz/chromium`                                                                        | absent                                        | `^149.0.0`                                                  |
| `@testing-library/jest-dom`                                                                  | absent                                        | `^7.0.0`                                                    |
| `@testing-library/react`                                                                     | absent                                        | `^16.3.2`                                                   |
| `@testing-library/user-event`                                                                | absent                                        | `^14.6.1`                                                   |
| `@vitejs/plugin-react`                                                                       | absent                                        | `^6.0.4`                                                    |
| `jsdom`                                                                                      | absent                                        | `^29.1.1`                                                   |
| `vitest`                                                                                     | absent                                        | `^4.1.10`                                                   |
| script `test`                                                                                | `node --import tsx --test tests/**/*.test.ts` | `node --import tsx --test tests/**/*.test.ts && vitest run` |
| scripts `test:components`, `test:browser`, `test:a11y`, `test:visual`, `test:browser:update` | absent                                        | present                                                     |

Nothing was removed in the other direction: every dependency and script
the old manifest had is still present in FRONT-01's. `dependencies`
(`next`, `react`, `react-dom`) are identical in both.

## 4. Lockfile — deliberately not regenerated

`package-lock.json` is FRONT-01's, byte-identical.

The instruction to regenerate assumed the cumulative manifests would be a
merge of two dependency states. They are not: **PACK-10 changed no
manifest**, so the cumulative manifests _are_ FRONT-01's manifests, and
FRONT-01's lockfile already resolves them. Verified from the delivered
lockfile — every package the correction requires is present and pinned:

| Package                       | Locked version |
| ----------------------------- | -------------- |
| `@playwright/test`            | 1.62.0         |
| `@sparticuz/chromium`         | 149.0.0        |
| `@axe-core/playwright`        | 4.12.1         |
| `vitest`                      | 4.1.10         |
| `@vitejs/plugin-react`        | 6.0.4          |
| `jsdom`                       | 29.1.1         |
| `@testing-library/react`      | 16.3.2         |
| `@testing-library/jest-dom`   | 7.0.0          |
| `@testing-library/user-event` | 14.6.1         |
| `next`                        | 15.5.21        |
| `typescript`                  | 5.9.3          |
| `eslint`                      | 9.39.5         |
| `prettier`                    | 3.9.6          |

Running `npm install --package-lock-only` would in the best case have
been a no-op and in the worst case have re-resolved unrelated transitive
versions. It was also not executable here: the preparation environment
has no npm-registry access (section 7). The lockfile was **not** edited
by hand, in any way.

## 5. Cumulative changed-file manifest

Relative to FRONT-01 CANDIDATE-2: **0 files removed, 0 FRONT-01 files
modified, 12 files modified, 22 files added.**

### 5.1 Modified — twelve, all from the reviewed PACK-10 delta

| Path                                                   | Applied how     | Origin state in FRONT-01            |
| ------------------------------------------------------ | --------------- | ----------------------------------- |
| `docs/canonical/TZ-00-domain-event-canon.md`           | verbatim        | identical to PACK-09 baseline       |
| `docs/canonical/canon-version.json`                    | verbatim        | identical to PACK-09 baseline       |
| `docs/canonical/README.md`                             | verbatim        | identical to PACK-09 baseline       |
| `docs/architecture/data-ownership.md`                  | verbatim        | identical to PACK-09 baseline       |
| `docs/architecture/service-boundaries.md`              | verbatim        | identical to PACK-09 baseline       |
| `packages/python/epd2-core/src/epd2_core/version.py`   | verbatim        | identical to PACK-09 baseline       |
| `packages/python/epd2-core/tests/test_version.py`      | verbatim        | identical to PACK-09 baseline       |
| `packages/typescript/epd2-types/src/version.ts`        | verbatim        | identical to PACK-09 baseline       |
| `packages/typescript/epd2-types/tests/version.test.ts` | verbatim        | identical to PACK-09 baseline       |
| `CHANGELOG.md`                                         | three-way merge | FRONT-01 had added its own entries  |
| `README.md`                                            | three-way merge | FRONT-01 had added its own sections |
| `docs/adr/README.md`                                   | three-way merge | FRONT-01 had added a two-line note  |

Each of the nine "verbatim" files was applied only after confirming that
FRONT-01's copy was byte-identical to the PACK-09 baseline both rounds
started from — that is, nothing of FRONT-01's was overwritten. The three
merges were produced by `git merge-file` with the PACK-09 baseline as the
common ancestor; **all three merged without a single conflict hunk**, and
each result was inspected: the CHANGELOG keeps FRONT-00/FRONT-01 entries
above the two PACK-10 `[Unreleased]` sections, the README keeps both the
frontend sections and the canon-`0.8.0` status entry, and the ADR index
keeps FRONT-01's note together with PACK-10's seven index rows and round
narrative.

### 5.2 Added — twenty-two

The twenty-one PACK-10 files (7 ADRs, 2 handover reports, 10 pack
documents, `scripts/check_canon_0_8_0.py`,
`tests/repository/test_canon_0_8_0_amendment.py`), plus this report. No
added path collided with an existing FRONT-01 path.

### 5.3 The planned FRONT-01 modification turned out to be unnecessary

The rebase was authorized to modify exactly one FRONT-01 file —
`frontend/web-shell/eslint.config.mjs`, to carry over CANDIDATE-3's
`next-env.d.ts` ignore entry. **It was not modified.** FRONT-01's own
copy already contains the identical entry:

```js
ignores: ["node_modules/**", ".next/**", "dist/**", "next-env.d.ts"],
```

FRONT-01 had independently made the same correction. Adding CANDIDATE-3's
explanatory comment would have been a gratuitous edit, so the file is
FRONT-01's, byte for byte. **The number of intentionally modified
FRONT-01 files is therefore zero**, and `frontend/` in its entirety is
byte-identical to FRONT-01 CANDIDATE-2.

### 5.4 One reproduced failure in CANDIDATE-4, and the file changed to fix it

After the mechanical rebase, `python3 scripts/check_canon_0_8_0.py`
failed — reproduced in the rebased repository, not anticipated
speculatively:

```text
Canon 0.8.0 amendment problems found:
  - docs/adr/ADR-047-frontend-browser-storage-policy.md: Status is '',
    expected 'proposed' - the 0.8.0 round accepts no ADR.
```

Cause: check 16 resolved this round's ADRs with the glob
`ADR-{number:03d}-*.md`, and in the rebased repository ADR-044 through
ADR-047 each matched **two** files — a frontend one and a finance one
(section 6). For ADR-047 the frontend file sorted first; its status is
declared as a `- Status: Proposed` bullet rather than the template's
`## Status` section, so the checker read an empty status and refused it.

CANDIDATE-4 fixed that by pinning this round's ADRs to exact filenames in
`scripts/check_canon_0_8_0.py`. CANDIDATE-5 removed the underlying cause
(section 6) and replaced the pin with an explicit id/filename manifest
plus a new registry-integrity check.

## 6. The ADR numbering collision — resolved in CANDIDATE-5

The cumulative repository briefly carried duplicate ADR ids: both rounds
had legitimately allocated numbers from the same free range while unaware
of each other. **CANDIDATE-5 resolves it by renumbering the PACK-10 set
to the next free consecutive range above the complete existing registry.**
The FRONT-00/FRONT-01 ADRs keep their numbers and are byte-identical to
FRONT-01 CANDIDATE-2.

Registry inspected before choosing the range: `docs/adr/` holds
ADR-000 (template) and ADR-001 – ADR-047, with a recorded gap at ADR-007
("reserved — not used by this governance round"). The highest number not
belonging to PACK-10 is ADR-047 (frontend), so the next free consecutive
block of seven is **ADR-048 – ADR-054**.

| Kept (FRONT-00/FRONT-01)                              | PACK-10 before | PACK-10 after                                                                |
| ----------------------------------------------------- | -------------- | ---------------------------------------------------------------------------- |
| `ADR-044-shared-frontend-source-runtime-isolation.md` | ADR-044        | `ADR-048-pack-10-finance-service-decomposition.md`                           |
| `ADR-045-existing-visual-baseline-preservation.md`    | ADR-045        | `ADR-049-authoritative-finance-ledger-and-correction-model.md`               |
| `ADR-046-voting-client-origin-and-build-isolation.md` | ADR-046        | `ADR-050-purpose-scoped-financial-party-references-and-aggregation.md`       |
| `ADR-047-frontend-browser-storage-policy.md`          | ADR-047        | `ADR-051-rechenschaftsbericht-lifecycle-snapshot-and-authority-semantics.md` |
| —                                                     | ADR-048        | `ADR-052-finance-authority-separation-and-independent-audit.md`              |
| —                                                     | ADR-049        | `ADR-053-pack-10-pack-09-pack-11-pack-35-boundaries.md`                      |
| —                                                     | ADR-050        | `ADR-054-canon-0.8.0-party-finance-context-additions.md`                     |

Every slug is unchanged; only the numeric prefix moved. 239 references
across 30 files were updated in one pass — canon section 19f, the PACK-10
specification, open decisions, implementation plan, threat model,
acceptance matrices, compatibility document, cross-pack boundaries, both
canon-amendment documents, all three PACK-10 reports, the ADR index,
`README.md`, `CHANGELOG.md`, `docs/canonical/README.md`, the two
architecture documents, the two version tests, and
`scripts/check_canon_0_8_0.py`. Two reference sites were deliberately
**not** renumbered because they speak about the frontend ADRs:
`docs/adr/README.md`'s FRONT-00 note and the corresponding `CHANGELOG.md`
line, both of which still read "Proposed ADR-044 through ADR-047".

`scripts/check_repository.py` needed no change: its four ADR entries name
the frontend files, which did not move.

The checker no longer infers PACK-10 ownership from a numeric range. It
carries an explicit `PACK10_ADRS` manifest of (id, filename) pairs, and a
new **check 17 — ADR registry integrity** asserts, over the real contents
of `docs/adr/`: every ADR id is globally unique; every filename id equals
the id the document declares in its own `# ADR-NNN` title; every ADR of
this round exists at its manifest filename and id; and each of the four
frontend ADRs matches a pinned SHA-256 taken from FRONT-01 CANDIDATE-2.
Three negative controls confirm it is not vacuous: tampering with a
frontend ADR, introducing a second file with an existing id, and making a
title disagree with its filename each produce a distinct, correct
failure.

## 7. Verification

### 7.1 Executed in the preparation environment — all passed

```text
$ python3 scripts/check_repository.py
OK: all 585 required paths are present.

$ python3 scripts/check_forbidden_files.py
OK: no forbidden paths found.

$ python3 scripts/verify_versions.py
OK: all version sources are consistent.

$ python3 scripts/check_canon_0_8_0.py
OK: all 16 canon 0.8.0 amendment checks passed.

$ ruff check .
All checks passed!

$ ruff format --check .
219 files already formatted
```

Additionally executed, without pytest, by importing the module and
calling its test functions directly:

```text
tests/repository/test_canon_0_8_0_amendment.py
  17 test functions imported and executed — all passed
```

And structurally, against the FRONT-01 baseline:

- `diff -rq` FRONT-01 → CANDIDATE-4: 0 removed, 12 modified, 22 added.
- `frontend/`, `docs/frontend/`, `contracts/`, `services/` and `.github/`
  are byte-identical to FRONT-01.
- 31 rows in `FRONT-01-ROUTE-CATALOG.csv`; 61 rows in
  `FRONT-01-LEGACY-MIGRATION-MAP.csv`; 45 PNG snapshots (15 FRONT-00 + 30
  FRONT-01); 6 `.gitkeep` files; both workflows; `.github`, `.gitignore`,
  `.prettierignore`, `Makefile`, `conftest.py` all FRONT-01's.
- The ESLint ignore mechanism was verified against a real ESLint (10.1.0)
  on a scratch copy of the same `ignores` array: `next-env.d.ts` is
  reported ignored, a handwritten `.tsx` is still inspected, and
  `eslint .` — the exact form the workspace script uses — exits 0 with no
  output.

### 7.2 Not executable here — no npm-registry and no PyPI access

`npm` returns HTTP 403 for the public registry and the internal mirror
requires credentials; PyPI is unreachable. The following therefore **were
not run, and nothing in this report claims their result**:

| Command                                                           | Why not executable                                                                                   |
| ----------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| `npm ci`                                                          | registry unreachable                                                                                 |
| `npm run typecheck --workspace=frontend/web-shell`                | needs `typescript`, `next`, `@playwright/test`, `vitest`, `@vitejs/plugin-react` from `node_modules` |
| `npm run lint --workspace=frontend/web-shell`                     | needs `eslint-config-next`                                                                           |
| `npm run test --workspace=frontend/web-shell`                     | needs `vitest`, `tsx`, `@testing-library/*`                                                          |
| `npm run test:browser` / `:a11y` / `:visual`                      | needs Playwright and `@sparticuz/chromium` browser binaries                                          |
| `npm run build --workspace=frontend/web-shell`                    | needs the full Next.js toolchain                                                                     |
| `npm run test --workspace=packages/typescript/epd2-types`         | needs the TypeScript toolchain                                                                       |
| `uv run pytest` / `uv run mypy` (`make verify`, `make typecheck`) | PyPI unreachable                                                                                     |
| `npm run format:check` at the pinned Prettier 3.9.6               | registry unreachable — see below                                                                     |

Prettier: the preparation environment has a system Prettier **3.8.1**,
while `package-lock.json` pins **3.9.6**. Run at 3.8.1, `prettier --check .`
flags three files —
`docs/adr/ADR-051-rechenschaftsbericht-lifecycle-snapshot-and-authority-semantics.md`
(a PACK-10 file; asterisk-escaping rule, changed between 3.8 and 3.9) and
`frontend/web-shell/foundation/storage-policy.ts` and
`frontend/web-shell/foundation/types.ts` (FRONT-01 files; union-type line
breaking, same version gap). **None of the three was touched.** All three
are formatted for the pinned 3.9.6, which is what CI runs; reformatting
them at 3.8.1 would break the pinned check and, for the two FRONT-01
files, would also violate this rebase's preservation rule.

### 7.3 Still required in GitHub Actions

The rebase is structurally verified only. These are the commands that
must pass in CI before this archive can be called anything stronger than
a candidate, in this order:

```bash
npm ci
npm run typecheck --workspace=frontend/web-shell
npm run lint --workspace=frontend/web-shell
npm run test --workspace=frontend/web-shell
npm run test:browser --workspace=frontend/web-shell
npm run test:a11y --workspace=frontend/web-shell
npm run test:visual --workspace=frontend/web-shell
npm run build --workspace=frontend/web-shell
npm run format:check
npm run test --workspace=packages/typescript/epd2-types
uv sync --all-groups
make check-repository
make format-check
make lint
make typecheck
make test
make build-frontend
make verify
python scripts/check_canon_0_8_0.py
```

Expected there, and specifically **not** claimed here: TypeScript
resolves `@playwright/test`, `@sparticuz/chromium`, `vitest/config` and
`@vitejs/plugin-react`; no implicit-`any` remains in
`playwright.config.ts`; the component, browser and axe suites pass; all
45 visual snapshots match **without** `--update-snapshots`; the Next.js
build succeeds; and the Python suite passes.

No speculative fix was added for any of those: the only failure this
round repaired is the one it actually reproduced (section 5.4).

## 8. Confirmations

- **No FRONT-01 file was lost.** 0 deletions; `frontend/`,
  `docs/frontend/`, `contracts/`, `services/` and `.github/` byte-identical
  to FRONT-01 CANDIDATE-2. Preserved and counted: the FRONT-00 final PASS
  report, the FRONT-00 candidate report, the FRONT-01 implementation
  report, the four frontend ADRs, the Mobile Application Profile
  (`docs/frontend/FRONT-00-MOBILE-APPLICATION-PROFILE.md`), 31 WS-01
  routes, 61 legacy migration decisions, 45 visual snapshots, the
  component/browser/a11y test infrastructure (`playwright.config.ts`,
  `vitest.config.ts`, `tests/browser/**`, `tests/setup.ts`,
  `tests/resolve-chromium.mjs`, `tests/start-next.mjs`), both workflows,
  `.gitignore` and all six `.gitkeep` files.
- **No FRONT-01 file was modified.** The single authorized modification
  proved unnecessary (section 5.3).
- **No frontend dependency was downgraded, removed or re-pinned**, and
  `package-lock.json` was neither regenerated nor hand-edited.
- **The PACK-10 canon amendment is complete and unchanged**:
  `CANON_VERSION = 0.8.0`, `REPOSITORY_VERSION = 0.9.0`,
  `finance_context_implementation_status = "not_implemented"`, canon
  section 19f with its `ФИН-01`–`ФИН-45` register, 21 ownership rows, 72
  events in 20.17, 25 forbidden links, 45 `FINANCE_*` reason codes, the
  four institutional roles and their incompatibilities, the twelve-state
  report lifecycle, `FinancePartyHandle`, the cross-pack boundary
  documentation and the canon checker. The canon document is byte-identical
  to CANDIDATE-3's.
- **No finance runtime was added.** No `services/finance-service`; no path
  under `services/`, `packages/`, `frontend/` or `contracts/` whose name
  contains `finance`; no migration, OpenAPI operation, runtime schema,
  frontend page or business test. Enforced by check 5 of
  `scripts/check_canon_0_8_0.py`, which passes.
- **ADR-048 – ADR-054 remain `proposed`.** No accepted ADR was rewritten.
- **This is a candidate, not a PASS**, and no claim of legal compliance,
  authority acceptance or production readiness is made anywhere in it.
