# CLAUDE-PACK-10 — Canon 0.8.0: Frontend Manifest Verification Report

Status: **PACK-10 CANON 0.8.0 CANDIDATE-6.** This round was commissioned
to restore `frontend/web-shell/package.json` and `package-lock.json` from
FRONT-01 CANDIDATE-2. **No restoration was necessary: both files in
CANDIDATE-5 are already byte-identical to FRONT-01 CANDIDATE-2.** This
report is the factual evidence, produced by reading the delivered archive
rather than by assertion, together with the identification of the tree the
failing CI run actually checked.

CANDIDATE-6 is CANDIDATE-5 plus this report. Nothing else changed.

## 1. The finding, stated plainly

The delivered `EPD2_PACK-10_CANON_0.8.0_CANDIDATE-5.zip` contains the
FRONT-01 manifests. Extracted fresh from the archive:

| File                              | SHA-256 in CANDIDATE-5                                             | SHA-256 in FRONT-01 CANDIDATE-2                                    | Identical |
| --------------------------------- | ------------------------------------------------------------------ | ------------------------------------------------------------------ | --------- |
| `frontend/web-shell/package.json` | `129b7589066c8ca3f79240f61d365b158472d056fa9fd16f01aabe2a41a75c11` | `129b7589066c8ca3f79240f61d365b158472d056fa9fd16f01aabe2a41a75c11` | yes       |
| `package-lock.json`               | `f04b249c05ad5b0394f609e5e8c90af3ce6d5a9d342c8b84415c48f9a3d89927` | `f04b249c05ad5b0394f609e5e8c90af3ce6d5a9d342c8b84415c48f9a3d89927` | yes       |

`diff` on both pairs produces no output. The exact diff requested in the
task is therefore empty, and there is no difference to explain.

## 2. The tree the failing CI run checked

The symptoms in the verification artifact — no `@playwright/test`, no
`@sparticuz/chromium`, no `vitest`, no `@vitejs/plugin-react`, and a
scripts block without the FRONT-01 test commands — match
`EPD2_PACK-10_CANON_0.8.0_CANDIDATE-3.zip` exactly. That archive predates
the cumulative rebase and still carried the PACK-09-era frontend tree:

| Property                           | CANDIDATE-3 (pre-rebase)                                           | CANDIDATE-5 / CANDIDATE-6                                          |
| ---------------------------------- | ------------------------------------------------------------------ | ------------------------------------------------------------------ |
| `frontend/web-shell/package.json`  | `1a8b8358293c72359a4280460f0c61c500e88c11df96a46271dc6c8e81bde298` | `129b7589066c8ca3f79240f61d365b158472d056fa9fd16f01aabe2a41a75c11` |
| `package-lock.json`                | `1335af3003cd0547a540bdf63554299e5032ae9d8c626bc53102b2090b4e5bb4` | `f04b249c05ad5b0394f609e5e8c90af3ce6d5a9d342c8b84415c48f9a3d89927` |
| packages in lockfile               | 396                                                                | 545                                                                |
| devDependencies                    | 9 (no Playwright, Vitest, Testing Library, jsdom, axe)             | 18                                                                 |
| scripts                            | 8 (no `test:*` beyond `test`)                                      | 13                                                                 |
| `@playwright/test` in lockfile     | absent                                                             | present, 1.62.0                                                    |
| `@sparticuz/chromium` in lockfile  | absent                                                             | present, 149.0.0                                                   |
| `vitest` in lockfile               | absent                                                             | present, 4.1.10                                                    |
| `@vitejs/plugin-react` in lockfile | absent                                                             | present, 6.0.4                                                     |

**Recommended reconciliation step, on your side:** at commit `aaf5b45`,
run

```bash
git show aaf5b45:frontend/web-shell/package.json | sha256sum
git show aaf5b45:package-lock.json | sha256sum
```

If those print `1a8b8358…` and `1335af30…`, the branch that produced
`Verify and Package #57` was built from CANDIDATE-3 content and never
received the cumulative rebase. If they print `129b7589…` and
`f04b249c…`, the manifests were correct at that commit and the failure
lies elsewhere in the pipeline — in which case send the artifact and the
job log and it can be diagnosed against this archive.

The verification artifact `epd2-civic-os-verification-result.zip` was not
attached to this request, so nothing in this report is derived from
reading it; the identification above rests entirely on the two archives
this session produced and on the symptom list quoted in the task.

## 3. Mandatory factual verification — item 1: scripts block

Read from `frontend/web-shell/package.json` in the delivered archive:

```json
{
  "dev": "next dev",
  "build": "next build",
  "start": "next start",
  "lint": "eslint .",
  "typecheck": "tsc --noEmit",
  "test": "node --import tsx --test tests/**/*.test.ts && vitest run",
  "test:components": "vitest run",
  "test:browser": "playwright test",
  "test:a11y": "playwright test --grep @a11y",
  "test:visual": "playwright test --grep @visual",
  "test:browser:update": "playwright test --grep @visual --update-snapshots",
  "format:check": "prettier --check .",
  "format": "prettier --write ."
}
```

All six FRONT-01 test scripts required by the task (`test`,
`test:components`, `test:browser`, `test:a11y`, `test:visual`,
`test:browser:update`) are present, in FRONT-01's own wording.

## 4. Mandatory factual verification — item 2: devDependencies block

```json
{
  "@axe-core/playwright": "^4.12.1",
  "@eslint/eslintrc": "^3.1.0",
  "@playwright/test": "^1.62.0",
  "@sparticuz/chromium": "^149.0.0",
  "@testing-library/jest-dom": "^7.0.0",
  "@testing-library/react": "^16.3.2",
  "@testing-library/user-event": "^14.6.1",
  "@types/node": "^22.0.0",
  "@types/react": "^19.0.0",
  "@types/react-dom": "^19.0.0",
  "@vitejs/plugin-react": "^6.0.4",
  "eslint": "^9.0.0",
  "eslint-config-next": "^15.0.0",
  "jsdom": "^29.1.1",
  "prettier": "^3.3.0",
  "tsx": "^4.15.0",
  "typescript": "^5.5.0",
  "vitest": "^4.1.10"
}
```

`dependencies` are unchanged from FRONT-01: `next` `^15.0.0`, `react`
`^19.0.0`, `react-dom` `^19.0.0`.

## 5. Mandatory factual verification — item 3: lockfile entries

Parsed from the delivered `package-lock.json` (`lockfileVersion` 3, 545
packages):

| Lockfile key                               | Status  | Version |
| ------------------------------------------ | ------- | ------- |
| `node_modules/@playwright/test`            | PRESENT | 1.62.0  |
| `node_modules/@sparticuz/chromium`         | PRESENT | 149.0.0 |
| `node_modules/vitest`                      | PRESENT | 4.1.10  |
| `node_modules/@vitejs/plugin-react`        | PRESENT | 6.0.4   |
| `node_modules/@axe-core/playwright`        | PRESENT | 4.12.1  |
| `node_modules/@testing-library/react`      | PRESENT | 16.3.2  |
| `node_modules/@testing-library/jest-dom`   | PRESENT | 7.0.0   |
| `node_modules/@testing-library/user-event` | PRESENT | 14.6.1  |
| `node_modules/jsdom`                       | PRESENT | 29.1.1  |

## 6. Mandatory factual verification — items 4 and 5: hashes and diff

Item 4 — SHA-256 of the two files as shipped in CANDIDATE-6:

```text
129b7589066c8ca3f79240f61d365b158472d056fa9fd16f01aabe2a41a75c11  frontend/web-shell/package.json
f04b249c05ad5b0394f609e5e8c90af3ce6d5a9d342c8b84415c48f9a3d89927  package-lock.json
```

Item 5 — exact diff against FRONT-01 CANDIDATE-2:

```text
$ diff FRONT-01/frontend/web-shell/package.json CANDIDATE-6/frontend/web-shell/package.json
$ diff FRONT-01/package-lock.json CANDIDATE-6/package-lock.json
```

Both produce no output: the files are byte-identical, so there are no
differences to explain.

## 7. Supporting frontend test infrastructure — verified present

| Required                                  | Present in CANDIDATE-6                                                                           |
| ----------------------------------------- | ------------------------------------------------------------------------------------------------ |
| `frontend/web-shell/playwright.config.ts` | yes                                                                                              |
| `frontend/web-shell/vitest.config.ts`     | yes                                                                                              |
| `frontend/web-shell/tests/browser/**`     | yes — `front00.browser.spec.ts`, `front01.browser.spec.ts` and both `*-snapshots` directories    |
| component tests                           | yes — `tests/foundation.render.test.tsx`, `tests/front01.render.test.tsx`, with `tests/setup.ts` |
| 45 committed visual snapshots             | yes — 15 under `front00.browser.spec.ts-snapshots`, 30 under `front01.browser.spec.ts-snapshots` |
| Playwright/Chromium helpers               | yes — `tests/resolve-chromium.mjs`, `tests/start-next.mjs`                                       |

One correction to the task's file list: there is **no
`frontend/web-shell/tests/components/` directory** in FRONT-01
CANDIDATE-2, and CANDIDATE-6 does not invent one. FRONT-01 places its
component tests directly in `tests/` as `*.render.test.tsx`, which is what
`vitest.config.ts` and the `test:components` script select. Everything the
requirement is about is present; only the directory name in the request
does not exist.

## 8. Verification actually executed

Executed here and passed:

```text
$ python3 scripts/check_canon_0_8_0.py
OK: all 17 canon 0.8.0 amendment checks passed.

$ python3 scripts/check_repository.py
OK: all 585 required paths are present.

$ python3 scripts/check_forbidden_files.py
OK: no forbidden paths found.

$ python3 scripts/verify_versions.py
OK: all version sources are consistent.

$ ruff check .
All checks passed!

$ ruff format --check .
219 files already formatted
```

Static manifest/lockfile verification: sections 3–6 above, all read from
the packaged files.

**Not executed, and not claimed:** `npm ci`,
`npm run typecheck --workspace=frontend/web-shell`,
`npm run lint --workspace=frontend/web-shell`,
`npm run test --workspace=frontend/web-shell`,
`npm run build --workspace=frontend/web-shell`, the browser, a11y and
visual suites, `make verify`, `uv run pytest`, `uv run mypy`, and
`prettier --check` at the pinned 3.9.6. The preparation environment has no
npm-registry and no PyPI access (HTTP 403 / unreachable), so none of those
commands can run here. They remain required in GitHub Actions, against a
tree whose two manifests hash to the values in section 6.

## 9. Retained from CANDIDATE-5, unchanged

PACK-10 canon 0.8.0 content (section 19f, 20.17, sections 22/23/24
additions); the ADR-048 – ADR-054 renumbering with the FRONT-00/FRONT-01
ADRs untouched; the ADR registry-integrity checker (17 checks, explicit
PACK-10 manifest, frontend digest pins); the `next-env.d.ts` ESLint
ignore; all cumulative reports; `CANON_VERSION = 0.8.0`;
`REPOSITORY_VERSION = 0.9.0`;
`finance_context_implementation_status = "not_implemented"`. No frontend
route, component, snapshot or public content was altered. No finance
runtime exists: no `services/finance-service`, and no path under
`services/`, `packages/`, `frontend/` or `contracts/` whose name contains
`finance`.

**PACK-10 CANON 0.8.0 CANDIDATE-6** — not a PASS.
