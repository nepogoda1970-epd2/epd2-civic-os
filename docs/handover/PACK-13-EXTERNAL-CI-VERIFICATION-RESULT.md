# PACK-13 — External CI Verification Result

Status: **PASS**

Runner: GitHub Actions / ubuntu-latest
Python: 3.12 · Node.js: 22
Repository version: `0.13.0`
Canon version: `0.8.0`
Evidence archive (retained **outside** this repository):
`epd2-civic-os-verification-result(15).zip`
SHA-256 of that archive:
`e3aa070f594e7366bd40f25f8d46dab8fda7d820428fc600020b2d8adcc9667b`

The workflow is pack-agnostic: it verifies whatever pack(s) are
implemented in the checked-out tree at run time. This document records the
run that applies to PACK-13; the pack-specific report is
`docs/handover/PACK-13-FINAL-PASS-REPORT.md`.

---

## 1. Results

| Stage                            | Command                                          | Result                             |
| -------------------------------- | ------------------------------------------------ | ---------------------------------- |
| Repository path manifest         | `scripts/check_repository.py`                    | **PASS** — 800 / 800               |
| Forbidden paths                  | `scripts/check_forbidden_files.py`               | **PASS** — none present            |
| Version consistency              | `scripts/verify_versions.py`                     | **PASS**                           |
| Ruff format                      | `ruff format --check .`                          | **PASS** — 520 files               |
| Prettier                         | `npm run format:check`                           | **PASS**                           |
| Ruff lint                        | `ruff check .`                                   | **PASS**                           |
| ESLint                           | `npm run lint --workspace=frontend/web-shell`    | **PASS**                           |
| mypy                             | 23 separate targets                              | **PASS** — no issues in any group  |
| TypeScript typecheck             | `tsc --noEmit` in `epd2-types` and `web-shell`   | **PASS**                           |
| Python test suite                | `pytest`                                         | **PASS** — 4625 passed, 4 skipped  |
| Node tests (`epd2-types`)        | `node --import tsx --test`                       | **PASS** — 34 passed, 0 failed     |
| Frontend unit / render tests     | `vitest` in `frontend/web-shell`                 | **PASS** — 16 passed, 2 test files |
| Next.js production build         | `next build`                                     | **PASS** — 46 static pages         |
| Browser / accessibility / visual | Playwright, projects `desktop`, `mobile`, `wide` | **PASS** — 108 passed              |

The 108 Playwright tests are 36 per viewport project across
`tests/browser/front00.browser.spec.ts` and
`tests/browser/front01.browser.spec.ts`; the accessibility and
visual-regression assertions are inside that count, not a separate suite.

The raw transcript is committed at
`docs/handover/PACK-13-EXTERNAL-CI-VERIFICATION.log` (780 lines), and
`VERIFICATION-RESULT.md` in the evidence archive records the run's own
one-word verdict, `PASS`.

---

## 2. Provenance of these figures

Unlike PACK-12's, these figures were **not** accepted on report. The
evidence archive was available in the environment that assembled the FINAL
PASS archive, its SHA-256 was recomputed and matches the value stated
above, and every figure in section 1 was read out of the committed
transcript rather than transcribed from a message.

Two further things were checked against the archive rather than assumed:

| Check                                           | Finding                                                                                                                                                                                               |
| ----------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Does the verified tree match the packaged tree? | Yes, file by file. All 948 tracked files were compared by SHA-256 against the archive's checkout; the only differences were CI-generated artifacts (see §3) and two files adopted _from_ the CI tree. |
| Does the local test count reconcile?            | Yes, exactly — see below.                                                                                                                                                                             |

The Python suite reports **4625 passed / 4 skipped** in CI and **4618
passed / 5 skipped** in the packaging sandbox. The seven-test difference is
an artefact of the sandbox, not of the tree:
`tests/contract/test_property_based.py` calls
`pytest.importorskip("hypothesis")`, and `hypothesis` cannot be installed
here because the package registries are unreachable, so the module's seven
tests are not collected and the module itself counts as one skip.
4618 + 7 = 4625; 5 − 1 = 4. This is the same reconciliation PACK-12's round
recorded, with a different module size.

## 3. What the CI checkout contained that this archive does not

The evidence archive is a snapshot of the runner's workspace after the run,
so it contains outputs the FINAL PASS archive must not:

- `VERIFICATION.log` and `VERIFICATION-RESULT.md` — the run's own outputs;
  the log is committed here under its PACK-13 name instead;
- `frontend/web-shell/playwright-report/`,
  `frontend/web-shell/test-results/`, `tsconfig.tsbuildinfo` — build and
  report artifacts;
- `DELETE.txt`, `PACK-12-CI-FORMAT-CORRECTION.md`,
  `PACK-12-CI-FORMAT-CORRECTION-2.md` — PACK-12's temporary correction
  notes, superseded by `docs/handover/PACK-12-FINAL-PASS-REPORT.md` §7 and
  deliberately not carried into a cumulative archive;
- `.ruff_cache/`, `.mypy_cache/`, `.pytest_cache/`, `.hypothesis/`,
  `__pycache__/`, `node_modules/` — caches.

Two files were adopted **from** the CI tree into this archive, because the
tree that passed is the source of truth and the packaging sandbox's copies
were stale:

| File                                        | Difference                                                                                                        |
| ------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `uv.lock`                                   | The CI tree's lock registers `epd2-data-plane-service` and `epd2-privileged-access-service` as workspace members. |
| `docs/frontend/FRONT-00-PAGE-INVENTORY.csv` | Identical content; the CI tree has LF line endings where the sandbox copy had CRLF.                               |

---

## 4. What this PASS does not establish

A green pipeline is evidence that the repository builds, type-checks,
lints, formats and tests cleanly. For a pack named after the production
data plane it is worth stating plainly what it is **not** evidence of, none
of which PACK-13 implements or claims:

- production readiness or operational deployment;
- legal validity, legal activation or admissibility;
- a production PostgreSQL deployment, a cloud database, or any database at
  all — every storage adapter in `services/data-plane-service` is an
  in-memory dictionary;
- a real Kafka, RabbitMQ or NATS broker, or any transport, topic naming or
  partitioning decision;
- an external schema-registry product;
- a production search engine or search index;
- a production IAM, identity provider, MFA or HSM/PKI;
- identity (PACK-14), voting or tally (PACK-15/16) implementation;
- backup or restore readiness (PACK-17) — `P13-BAK-011` forbids claiming it
  without a restore test, and no backup exists here to restore;
- multi-region deployment;
- any frontend surface for the data plane.

The criteria whose stated evidence is a database grant inventory, a live
catalog snapshot, a role inventory or an egress-control review remain
`deferred to production infrastructure` in
`docs/packs/PACK-13/PACK-13-ACCEPTANCE-MATRIX.md`. A pipeline cannot close
them, because the environment they describe does not exist yet.
