# FRONT-01 + PACK-10 CANON 0.8.0 — FINAL PASS

Final status: **FRONT-01 + PACK-10 CANON 0.8.0 — FINAL PASS.**

This package is the verified cumulative state of the repository. The PASS
rests on an external GitHub Actions run whose artifact was supplied with
this packaging request and whose checked-out tree was compared, file by
file, against the package contents (section 8). The packaging round
itself changed no implementation, no canon, no frontend content, no test,
no route, no snapshot, no ADR number and no version.

## 1. Inputs

| Role                                              | File                                               | SHA-256                                                                                                                         |
| ------------------------------------------------- | -------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| Exact implementation source                       | `EPD2_PACK-10_CANON_0.8.0_CANDIDATE-7.zip`         | `4dd9922e94f8a341ddb5c3bff4368af180370bec2ab6e663ee5b678ccae4cb52`                                                              |
| External CI evidence (as uploaded, outer wrapper) | `epd2-civic-os-verification-result(11).zip`        | `b81ffe044d6f0329b3f62376470e48aab0087ffedf1ef70e94279edcc1332e7e`                                                              |
| External CI evidence (inner artifact)             | `epd2-civic-os-verification-result.zip`            | `cd16fc812ad4a698dd71ac32edf71251e80c702a02c4efb608026789fd23b841`                                                              |
| Output                                            | `EPD2_FRONT-01_PACK-10_CANON_0.8.0_FINAL_PASS.zip` | stated in the delivery message and reproducible with `sha256sum` on the delivered file — an archive cannot contain its own hash |

## 2. Versions — unchanged by this packaging round

| Item                                    | Value             |
| --------------------------------------- | ----------------- |
| `REPOSITORY_VERSION`                    | `0.9.0`           |
| `CANON_VERSION`                         | `0.8.0`           |
| `finance_context_implementation_status` | `not_implemented` |
| `repository_compatibility`              | `>=0.1.0 <0.10.0` |
| `minimum_repository_version`            | `0.9.0`           |

## 3. Cumulative scope in this package

- PACK-01 through PACK-09 — FINAL PASS baseline, unchanged.
- FRONT-00 Foundation — final PASS content (`docs/frontend/FRONT-00-*`,
  `frontend/web-shell/foundation/**`, `components/**`, FRONT-00 browser
  suite and its 15 visual baselines).
- FRONT-01 Public Website 0.2.0 — 31 WS-01 routes, the public
  information architecture, 61 legacy migration decisions, the FRONT-01
  browser/a11y/visual suite and its 30 visual baselines.
- PACK-10 Canon Amendment 0.8.0 — canon section 19f (`ФИН-01`–`ФИН-45`,
  21 finance aggregates, four institutional roles, `FinancePartyHandle`,
  the twelve-state `Rechenschaftsbericht` lifecycle), section 20.17 (72
  events), 21 section-22 ownership rows, 25 section-23 forbidden links,
  45 section-24 `FINANCE_*` reason codes, `scripts/check_canon_0_8_0.py`
  with 17 checks, and the PACK-10 document set.

## 4. ADR registry

Fifty-three ADRs plus `ADR-000-template.md`; ids `001`–`054` with the
single recorded gap at `007`; **zero duplicate ADR ids**, zero duplicate
filenames, and every filename id equal to the id declared in the
document's own title.

| Range             | Owner               | Files                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| ----------------- | ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| ADR-044 – ADR-047 | FRONT-00 / FRONT-01 | `ADR-044-shared-frontend-source-runtime-isolation.md`, `ADR-045-existing-visual-baseline-preservation.md`, `ADR-046-voting-client-origin-and-build-isolation.md`, `ADR-047-frontend-browser-storage-policy.md`                                                                                                                                                                                                                                               |
| ADR-048 – ADR-054 | PACK-10             | `ADR-048-pack-10-finance-service-decomposition.md`, `ADR-049-authoritative-finance-ledger-and-correction-model.md`, `ADR-050-purpose-scoped-financial-party-references-and-aggregation.md`, `ADR-051-rechenschaftsbericht-lifecycle-snapshot-and-authority-semantics.md`, `ADR-052-finance-authority-separation-and-independent-audit.md`, `ADR-053-pack-10-pack-09-pack-11-pack-35-boundaries.md`, `ADR-054-canon-0.8.0-party-finance-context-additions.md` |

None of the obsolete pre-renumbering PACK-10 filenames (`ADR-044-pack-10-…`
through `ADR-050-canon-0.8.0-…`) exists in this package; all seven were
verified absent before packaging.

## 5. Finance runtime — absent, by check

No `services/finance-service`. No path under `services/`, `packages/`,
`frontend/` or `contracts/` whose name contains `finance`. Check 5 of
`scripts/check_canon_0_8_0.py` asserts exactly this and passes. PACK-10
remains canon-and-documentation only; canon 19f.25 is the implementation
gate, and ADR-048 – ADR-054 remain `proposed`.

## 6. FRONT-01 scope and visual baselines

- `docs/frontend/FRONT-01-ROUTE-CATALOG.csv` holds **31** routes and the
  `workspace` column contains exactly one distinct value: `WS-01`.
- `docs/frontend/FRONT-01-ACCEPTANCE-MATRIX.md` states the WS-01-only
  requirement as mandatory, enforced by `data-workspace="WS-01"`, route
  and architecture tests.
- **45** committed PNG visual baselines: 15 under
  `tests/browser/front00.browser.spec.ts-snapshots/`, 30 under
  `tests/browser/front01.browser.spec.ts-snapshots/`. Not regenerated;
  no snapshot-update mode was used anywhere in this session.

## 7. Files added, changed or removed for final packaging

| Action  | Path                                                              | Reason                                  |
| ------- | ----------------------------------------------------------------- | --------------------------------------- |
| added   | `docs/handover/FRONT-01-PACK-10-CANON-0.8.0-FINAL-PASS-REPORT.md` | This report — the only packaging change |
| changed | none                                                              | —                                       |
| removed | none                                                              | —                                       |

Against `EPD2_PACK-10_CANON_0.8.0_CANDIDATE-7.zip`: **1 file added, 0
changed, 0 removed.** Total files in this package: **730**.

Excluded from the archive, as required and verified absent: `.git`,
`.venv`, `node_modules`, `.next`, `__pycache__`, `*.pyc`,
`.pytest_cache`, `.mypy_cache`, `.ruff_cache`, `.hypothesis`, coverage
output, `test-results`, Playwright reports, `tsconfig.tsbuildinfo`,
nested ZIP archives, and the external verification artifact itself.
Preserved: `.github` (both workflows), `.gitignore`, `.editorconfig`,
`.prettierignore`, `.pre-commit-config.yaml`, all six `.gitkeep` files,
`uv.lock`, `package-lock.json`, every manifest, every test and every
handover report.

## 8. Correspondence between this package and the CI-verified tree

The supplied artifact contains the full tree the run checked out. It was
compared file by file against this package (CI-side caches, `node_modules`,
`.next`, `test-results`, the artifact's own `VERIFICATION.log` /
`VERIFICATION-RESULT.md` and its nested `epd2-civic-os/` staging copy
excluded from the comparison):

- **728 files byte-identical.**
- **0 files present in the CI tree and missing here.**
- **3 differences, all explained, none a source change:**

| Difference                                                                                                                  | Explanation                                                                                                                                                                                                      |
| --------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `package-lock.json` — the CI copy has one extra line, `"dev": true`, inside `node_modules/playwright/node_modules/fsevents` | npm added the flag to a macOS-only optional transitive dependency while installing on the runner. No declared dependency, version or integrity hash differs. This package keeps the committed FRONT-01 lockfile. |
| `docs/frontend/FRONT-00-PAGE-INVENTORY.csv` — differs                                                                       | Line endings only: this package carries the CRLF file exactly as FRONT-01 CANDIDATE-2 shipped it; the git checkout in CI has LF. Byte-identical after newline normalisation (verified).                          |
| `docs/handover/PACK-09-EXTERNAL-CI-VERIFICATION.log` — present here, absent in the CI tree                                  | `.gitignore` line 53 is `*.log`, so this historical PACK-09 artifact cannot exist in a git checkout. It is not a required path (the repository checker passes with 585 paths in both trees).                     |

## 9. Checks actually rerun locally for this packaging round

Executed here, on the staged tree, and passed:

```text
$ python3 scripts/check_repository.py
OK: all 585 required paths are present.

$ python3 scripts/check_forbidden_files.py
OK: no forbidden paths found.

$ python3 scripts/verify_versions.py
OK: all version sources are consistent.

$ python3 scripts/check_canon_0_8_0.py
OK: all 17 canon 0.8.0 amendment checks passed.

$ ruff check .
All checks passed!

$ ruff format --check .
219 files already formatted
```

Also executed here: the 18 test functions of
`tests/repository/test_canon_0_8_0_amendment.py`, imported and called
directly (pytest is not installed in this environment) — all passed; the
ADR-registry scan reported in section 4; the snapshot, route, `.gitkeep`,
`uv.lock` and dependency inventories in sections 6 and 10; the file-by-file
comparison in section 8; and the archive round-trip in section 11.

## 10. Frontend dependency manifests — present and locked

`frontend/web-shell/package.json` devDependencies include
`@axe-core/playwright ^4.12.1`, `@playwright/test ^1.62.0`,
`@sparticuz/chromium ^149.0.0`, `@testing-library/jest-dom ^7.0.0`,
`@testing-library/react ^16.3.2`, `@testing-library/user-event ^14.6.1`,
`@vitejs/plugin-react ^6.0.4`, `jsdom ^29.1.1`, `vitest ^4.1.10`; its
scripts include `test`, `test:components`, `test:browser`, `test:a11y`,
`test:visual` and `test:browser:update`. The root `package-lock.json`
(lockfileVersion 3, 545 packages) resolves `@playwright/test` 1.62.0,
`@sparticuz/chromium` 149.0.0, `vitest` 4.1.10, `@vitejs/plugin-react`
6.0.4, `next` 15.5.21, `typescript` 5.9.3, `eslint` 9.39.5 and `prettier`
3.9.6.

## 11. Packaging integrity

- Archive root is the repository root — no extra nested directory.
- The extracted archive is byte-identical to the staged clean tree
  (recursive `diff`, 0 differences).
- 730 files; zero forbidden generated paths; zero nested ZIP archives;
  zero missing baseline files.

## 12. Results accepted from the external GitHub Actions evidence

Not rerun here — this environment has no npm-registry or PyPI access, so
every network-dependent suite below is accepted **from the supplied
artifact**, not reproduced:

| Step                               | Result in the artifact                       |
| ---------------------------------- | -------------------------------------------- |
| Overall status                     | **PASS**                                     |
| Runner                             | GitHub Actions / ubuntu-latest               |
| Python / Node.js                   | 3.12 / 22                                    |
| Repository check                   | `OK: all 585 required paths are present.`    |
| Forbidden-path check               | `OK: no forbidden paths found.`              |
| Version consistency                | `OK: all version sources are consistent.`    |
| Ruff format                        | `392 files already formatted`                |
| Ruff lint                          | `All checks passed!`                         |
| Prettier                           | `All matched files use Prettier code style!` |
| ESLint                             | PASS                                         |
| mypy (19 groups)                   | `Success: no issues found` in every group    |
| TypeScript typecheck               | PASS                                         |
| Python tests                       | `2677 passed, 4 skipped`                     |
| TypeScript package tests           | PASS                                         |
| Frontend component tests (Vitest)  | `2 files, 16 tests passed`                   |
| Next.js production build           | PASS                                         |
| Playwright browser / a11y / visual | `108 passed`                                 |
| Committed visual snapshots         | all 45 matched, no snapshot update used      |

The artifact's own `VERIFICATION-RESULT.md` notes that the workflow is
pack-agnostic and verifies whatever tree is checked out; section 8 above
is what ties that run to this package's contents.

## 13. Scope of this PASS

This is a verification result for the cumulative repository state
described above. It is **not** a claim of legal compliance, tax
correctness, audit sufficiency, authority acceptance or production
readiness for any pack, and specifically not for PACK-10: no finance
runtime exists, ADR-048 – ADR-054 remain `proposed`, and canon 19f.25
still gates implementation. Any later implementation package must earn
its own verification and must not inherit this label.

**FRONT-01 + PACK-10 CANON 0.8.0 — FINAL PASS**
