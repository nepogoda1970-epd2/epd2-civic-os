# PACK-14 — External CI Verification Result

Status: **PASS**

Runner: GitHub Actions / ubuntu-latest
Python: 3.12.13 · Node.js: 22
Repository version: `0.14.0`
Canon version: `0.8.0`
Verified candidate archive:
`EPD2_PACK-14_IDENTITY_AUTHENTICATION_ACCOUNT_SECURITY_0.14.0_CANDIDATE_CORRECTED_PRETTIER.zip`
Evidence archive (retained **outside** this repository):
`epd2-civic-os-verification-result(16).zip`
SHA-256 of that archive:
`c80b2f1a05f97423c782f7b0e42f78502a802bd47432a43caee207321dff515d`
SHA-256 of the verification ZIP it contains:
`df6981227d80f4a01d406bcf882f7dea3cfd31400d3c262eb93009c1eb1b6054`

The workflow is pack-agnostic: it verifies whatever pack(s) are
implemented in the checked-out tree at run time. This document records the
run that applies to PACK-14; the pack-specific report is
`docs/handover/PACK-14-FINAL-PASS-REPORT.md`.

---

## 1. Results

| Stage                            | Command                                          | Result                             |
| -------------------------------- | ------------------------------------------------ | ---------------------------------- |
| Repository path manifest         | `scripts/check_repository.py`                    | **PASS** — 867 / 867               |
| Forbidden paths                  | `scripts/check_forbidden_files.py`               | **PASS** — none present            |
| Version consistency              | `scripts/verify_versions.py`                     | **PASS**                           |
| Ruff format                      | `ruff format --check .`                          | **PASS** — 566 files               |
| Prettier                         | `npm run format:check`                           | **PASS**                           |
| Ruff lint                        | `ruff check .`                                   | **PASS**                           |
| ESLint                           | `npm run lint --workspace=frontend/web-shell`    | **PASS**                           |
| mypy                             | 23 separate targets                              | **PASS** — no issues in any group  |
| TypeScript typecheck             | `tsc --noEmit` in `epd2-types` and `web-shell`   | **PASS**                           |
| Python test suite                | `pytest`                                         | **PASS** — 4905 passed, 4 skipped  |
| TypeScript package tests         | `node --import tsx --test` in `epd2-types`       | **PASS** — 3 passed, 0 failed      |
| Node tests (`web-shell`)         | `node --import tsx --test`                       | **PASS** — 34 passed, 0 failed     |
| Frontend unit / render tests     | `vitest` in `frontend/web-shell`                 | **PASS** — 16 passed, 2 test files |
| Next.js production build         | `next build`                                     | **PASS** — 46 / 46 static pages    |
| Browser / accessibility / visual | Playwright, projects `desktop`, `mobile`, `wide` | **PASS** — 108 passed              |

`identity-service`'s own mypy target reports **no issues found in 52
source files** — the group PACK-14 grew from 38 files to 52, and it is
clean.

The 108 Playwright tests are 36 per viewport project across
`tests/browser/front00.browser.spec.ts` and
`tests/browser/front01.browser.spec.ts`; the accessibility and
visual-regression assertions are inside that count, not a separate suite.

The raw transcript is committed at
`docs/handover/PACK-14-EXTERNAL-CI-VERIFICATION.log` (797 lines), and
`VERIFICATION-RESULT.md` in the evidence archive records the run's own
one-word verdict, `PASS`.

---

## 2. Provenance of these figures

Like PACK-13's, these figures were **not** accepted on report. The
evidence archive was available in the environment that assembled the FINAL
PASS archive, both of its SHA-256 digests were recomputed and match the
values stated above, and every figure in section 1 was read out of the
committed transcript rather than transcribed from a message.

Three further things were checked against the archive rather than assumed.

| Check                                           | Finding                                                                                                                                                    |
| ----------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Does the verified tree match the packaged tree? | Yes, file by file. All 1053 files of the packaged tree were compared by SHA-256 against the archive's checkout; the only differences are enumerated in §3. |
| Did the run actually exercise the PACK-14 code? | Yes. The transcript collects `tests/repository/test_pack14_default_binding.py .........` (9 tests) and every PACK-14 service suite by name.                |
| Does the local test count reconcile?            | Yes, exactly — see below.                                                                                                                                  |

The Python suite reports **4905 passed / 4 skipped** in CI and **4898
passed / 5 skipped** in the packaging sandbox. The seven-test difference is
an artefact of the sandbox, not of the tree:
`tests/contract/test_property_based.py` calls
`pytest.importorskip("hypothesis")`, and `hypothesis` cannot be installed
here because the package registries are unreachable, so the module's seven
tests are not collected and the module itself counts as one skip.
4898 + 7 = 4905; 5 − 1 = 4. This is the same reconciliation PACK-12's and
PACK-13's rounds recorded, with a different module size.

The four remaining skips are the documented CT-00-10 / CT-00-11 / CT-00-12
not-applicable declarations, unchanged from PACK-13.

**Ruff's file count reconciles too, and it is worth stating why it is not 393.** `ruff format --check .` reports **566** files in CI and **393** in
the packaging sandbox. The difference is exactly the 173 Python files
inside `epd2-civic-os/`, a stale nested copy of the repository present in
the GitHub checkout and described in §3. 393 + 173 = 566. The nested copy
is formatted, which is why the stage passed; it is not part of this
archive, which is why the number differs.

---

## 3. What the CI checkout contained that this archive does not

The evidence archive is a snapshot of the runner's workspace after the run,
so it contains outputs and strays the FINAL PASS archive must not.

**The run's own outputs**

- `VERIFICATION.log` and `VERIFICATION-RESULT.md` — the log is committed
  here under its PACK-14 name instead;
- `frontend/web-shell/playwright-report/index.html`,
  `frontend/web-shell/test-results/.last-run.json`,
  `frontend/web-shell/tsconfig.tsbuildinfo` — build and report artifacts.

**Caches**

- `.ruff_cache/`, `.mypy_cache/`, `.pytest_cache/`, `.hypothesis/`,
  `__pycache__/`.

**Strays in the GitHub working repository, deliberately not carried into a
cumulative archive**

- `epd2-civic-os/` — a **stale nested copy of the repository at
  `REPOSITORY_VERSION 0.6.0`** (PACK-06 era; 435 files, 173 of them
  Python). Its `identity-service` has six modules and none of PACK-14's.
  It has never been part of any FINAL PASS archive. It was linted and
  format-checked by the run (see §2) but never imported, collected or
  type-checked: `pyproject.toml`'s `testpaths` is an explicit list, the
  mypy invocations name 23 explicit targets, and
  `scripts/check_repository.py` reads a manifest. Carrying it would put a
  second, eight-versions-old repository inside the authoritative baseline
  and violate this archive's no-duplicate-paths rule. **Recommendation:
  delete `epd2-civic-os/` from the GitHub repository.**
- `DELETE.txt`, `PACK-12-CI-FORMAT-CORRECTION.md`,
  `PACK-12-CI-FORMAT-CORRECTION-2.md` — PACK-12's temporary correction
  notes, superseded by `docs/handover/PACK-12-FINAL-PASS-REPORT.md` §7.
  PACK-13's FINAL PASS round excluded the same three files for the same
  reason.
- `docs/handover/PACK-01-VERIFICATION.log` — a PACK-01-era transcript
  present in the GitHub working repository but in **no** archive of the
  cumulative lineage, including the PACK-13 FINAL PASS baseline this round
  was built from. Adding it here would be a silent scope change to the
  cumulative archive, so it is reported rather than absorbed.

Three files were adopted **from** the CI tree into this archive, because
the tree that passed is the source of truth and the packaging sandbox's
copies were stale in the same way PACK-13's two were:

| File                                                 | Difference                                                               |
| ---------------------------------------------------- | ------------------------------------------------------------------------ |
| `docs/handover/PACK-09-EXTERNAL-CI-VERIFICATION.log` | Identical content; three lines carried a stray `CR` in the sandbox copy. |
| `docs/handover/PACK-11-EXTERNAL-CI-VERIFICATION.log` | Same, three lines.                                                       |
| `docs/handover/PACK-13-EXTERNAL-CI-VERIFICATION.log` | Same, three lines.                                                       |

All three are Next.js `Generating static pages (n/m)` progress lines,
which the runner rewrites in place; no other byte of any of the three
files differs.

---

## 4. What this PASS does not establish

A green pipeline is evidence that the repository builds, type-checks,
lints, formats and tests cleanly. For a pack named after identity and
authentication it is worth stating plainly what it is **not** evidence of,
none of which PACK-14 implements or claims:

- production readiness, operational deployment, or legal activation;
- a production IAM, identity provider, eID scheme, or KYC integration —
  no provider of any kind is selected or integrated;
- correct WebAuthn verification or correct password hashing. Both are
  ports whose default binding **refuses**, and this repository implements
  neither algorithm. A pipeline cannot verify a library that is not bound;
- a bound breached-password corpus. The default refuses, so **no password
  can be enrolled or replaced** in an unconfigured deployment;
- a production database or any operational durability. PACK-14's
  persistence path is real, migrated, transactional and tested — and it
  runs on SQLite through the standard library. No PostgreSQL is deployed;
  no replication, backup, failover or restore capability exists;
- an HTTP surface, TLS termination, a production gateway or a public
  deployment. The service boundary is a transport-agnostic reference
  adapter routing 12 of the 42 catalogued operations;
- a durable audit store. `runtime.build_identity_service` binds
  `InMemoryAuditEventStore`, because `audit-core` owns durable audit
  persistence;
- email or SMS delivery, an HSM or a KMS;
- a Voting Client, eligibility assertion, voting credential issuance,
  ballots or tally (PACK-15 / PACK-16);
- a full legal electronic signature (`FIR-TRUST-001`);
- the Account & Security FRONT-PACK. No frontend file changed this round
  and `FIR-UX-011` stays **future**;
- lawful retention durations. `OD-P14-07` remains open pending legal
  confirmation; every `duration_confirmed` flag is `False` and every
  destructive disposition refuses while it is.

`docs/packs/PACK-14/PACK-14-OPEN-ITEMS.md` records these as open rather
than covered, and the PASS does not close any of them.
