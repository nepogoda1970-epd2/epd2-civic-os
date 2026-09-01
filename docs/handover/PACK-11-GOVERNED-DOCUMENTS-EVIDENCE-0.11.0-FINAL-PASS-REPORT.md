# PACK-11 Governed Documents & Evidence 0.11.0 — Final PASS Report

Status: **PACK-11 GOVERNED DOCUMENTS & EVIDENCE 0.11.0 — FINAL PASS.**

This is a packaging round. No implementation was rebuilt, no
`document-service` module was changed, no test was changed, no contract,
JSON schema, reason code, ADR, frontend file, route or visual snapshot
was touched, and neither the repository nor the canon version moved. The
archive is the verified candidate tree plus this report, the external CI
log, the lock files that CI itself regenerated, and a small set of
status/history edits that close the round.

The PASS status rests on an external GitHub Actions run, not on anything
this environment could execute. Section 8 states exactly which checks
were re-run locally and which are accepted from that run; nothing
network-dependent is claimed as locally verified.

## 1. Inputs

| Artifact                                                          | SHA-256                                                            |
| ----------------------------------------------------------------- | ------------------------------------------------------------------ |
| `EPD2_PACK-11_GOVERNED_DOCUMENTS_EVIDENCE_0.11.0_CANDIDATE-8.zip` | `fcc53b0d5b693787efcf45a56a04b5d5f12f7314b0c15de59c9b70602215d97e` |
| `epd2civicosverificationresult.zip` (outer)                       | `2504e8710045243bf40da83c934adb654c3437fadddc51dae3c54474c4396c48` |
| `epd2-civic-os-verification-result.zip` (inner)                   | `ef9423fdffbbeea3efcfb13bf4429865901664412d1878034d47b8e7d2bc60d0` |

The candidate archive was extracted to a clean directory and is the
staged tree for this package. A recursive comparison against the
verification tree confirmed they agree everywhere that matters — see
section 7.

## 2. Versions and status

| Value                                    | Setting                    | Declared in                                                                                           |
| ---------------------------------------- | -------------------------- | ----------------------------------------------------------------------------------------------------- |
| `REPOSITORY_VERSION`                     | `0.11.0`                   | `packages/python/epd2-core/src/epd2_core/version.py`, `packages/typescript/epd2-types/src/version.ts` |
| `CANON_VERSION`                          | `0.8.0`                    | the same two files and `docs/canonical/canon-version.json`                                            |
| `document_context_implementation_status` | `reference_implementation` | `docs/canonical/canon-version.json`                                                                   |
| `finance_context_implementation_status`  | `reference_implementation` | `docs/canonical/canon-version.json` (unchanged by this round)                                         |
| `repository_compatibility`               | `>=0.1.0 <0.12.0`          | `docs/canonical/canon-version.json`                                                                   |
| `minimum_repository_version`             | `0.9.0`                    | `docs/canonical/canon-version.json`                                                                   |

`reference_implementation` is the truthful value for the document and
evidence context, and it was chosen over both neighbours.
`not_implemented` stopped being true when `services/document-service`
shipped; `implemented` would assert a production data plane — durable
storage, a real content store, an event bus — that this round does not
have. `minimum_repository_version` stays at `0.9.0` because it records
the repository version the canon 0.8.0 amendment was made at, and that
does not move forward with each round that implements it.

`docs/canonical/TZ-00-domain-event-canon.md` is byte-for-byte identical
to its 0.8.0 text. PACK-11 amends no canon; it implements a context that
canon 19f.22 had already assigned to PACK-11.

## 3. What the round delivered

`services/document-service` is the sole authoritative owner of the
governed-document and evidence bounded context: organization-scoped
document ownership, immutable document versions, a cryptographically
linked version history, typed document and evidence references,
controlled review and approval, the publication lifecycle, restricted and
public projections, correction, supersession and revocation, legal hold,
retention metadata, evidence bundles, provenance, complete audit history,
and scoped authorization with separation of duties.

- 13 modules under `services/document-service/src/epd2_document_service/`
- 12 test modules under `services/document-service/tests/`
- `contracts/reason-codes/pack-11.yml` — 71 entries
- 6 JSON schemas under `contracts/schemas/`
- ADR-055 through ADR-060
- `docs/packs/PACK-11-*.md` — specification, implementation, FIR
  traceability, acceptance matrix, cross-pack boundaries, threat model,
  open decisions
- `docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md` at its
  canonical repository path

`FIR-ROADMAP-001` and `FIR-INV-010` are implemented in reference form.
`FIR-DEC-001`, `FIR-DEC-002`, `FIR-CAND-001`, `FIR-COMM-001`,
`FIR-PROG-002`, `FIR-INIT-021`, `FIR-PAY-003` and `FIR-DATA-003` receive
**foundation only** and are not marked implemented. The per-entry
evidence is in `docs/packs/PACK-11-FIR-TRACEABILITY.md`; a green CI
pipeline does not upgrade any of those eight.

## 4. The technical arbiter

The arbiter for this round is an **external GitHub Actions run** on
`ubuntu-latest` with Python 3.12 and Node.js 22 — not this environment,
and not any local claim. The run's own summary is
`VERIFICATION-RESULT.md` from the verification archive:

```text
Status: PASS
Runner: GitHub Actions / ubuntu-latest
Python: 3.12
Node.js: 22
```

The complete 710-line transcript is preserved verbatim in this archive
as `docs/handover/PACK-11-EXTERNAL-CI-VERIFICATION.log`, following the
precedent set by `docs/handover/PACK-09-EXTERNAL-CI-VERIFICATION.log`.
Every figure in section 5 is quoted from it and can be re-read there in
context.

## 5. CI results, as reported by the run

| Gate                              | Command                             | Result                               |
| --------------------------------- | ----------------------------------- | ------------------------------------ |
| Repository structure              | `scripts/check_repository.py`       | 672 required paths present           |
| Forbidden files                   | `scripts/check_forbidden_files.py`  | no forbidden paths found             |
| Version consistency               | `scripts/verify_versions.py`        | all version sources consistent       |
| Python format                     | `ruff format --check .`             | 442 files already formatted          |
| Prettier format                   | `npm run format:check`              | all matched files use Prettier style |
| Python lint                       | `ruff check .`                      | all checks passed                    |
| Frontend lint                     | `eslint .`                          | clean, no findings                   |
| Type check (Python)               | `mypy`, 21 groups                   | no issues, every group               |
| Type check (TypeScript)           | `tsc --noEmit`, both workspaces     | clean                                |
| Python tests                      | `pytest`                            | **3727 passed, 4 skipped, 0 failed** |
| TypeScript `epd2-types` tests     | `node --test`                       | **3 passed, 0 failed**               |
| Additional TypeScript tests       | `node --test`                       | **34 passed, 0 failed**              |
| Frontend unit tests               | `vitest`                            | **16 passed, 0 failed**              |
| Next.js build                     | `next build`                        | PASS                                 |
| Browser, visual and accessibility | Playwright, mobile + desktop + wide | **108 passed, 0 failed**             |

The four skipped Python tests are the repository's own deliberate
CT-00-10, CT-00-11 and CT-00-12 not-applicable markers, each carrying a
written justification in its skip reason. They are not omitted coverage,
and the run reports zero failures.

`mypy` reports `Success: no issues found in 27 source files` for
`services/document-service` specifically, alongside the twenty other
groups.

## 6. Files this packaging round added and changed

Added (2):

| Path                                                                            | Why                                          |
| ------------------------------------------------------------------------------- | -------------------------------------------- |
| `docs/handover/PACK-11-GOVERNED-DOCUMENTS-EVIDENCE-0.11.0-FINAL-PASS-REPORT.md` | this report                                  |
| `docs/handover/PACK-11-EXTERNAL-CI-VERIFICATION.log`                            | the verbatim CI transcript the PASS rests on |

Changed (6):

| Path                                                         | Change                                                                                   |
| ------------------------------------------------------------ | ---------------------------------------------------------------------------------------- |
| `README.md`                                                  | PACK-11 section heading `CANDIDATE` → `FINAL PASS`                                       |
| `CHANGELOG.md`                                               | `[0.11.0]` entry restated as FINAL PASS, non-claims kept and sharpened                   |
| `docs/handover/PACK-11-IMPLEMENTATION-REPORT.md`             | status header marked superseded by this report; body left unedited as the round's record |
| `docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md` | `FIR-BASE-001` baseline moved to this archive; `FIR-ROADMAP-001` and section 21 updated  |
| `uv.lock`                                                    | replaced with the file the verified CI run itself resolved (see below)                   |
| `package-lock.json`                                          | replaced with the file the verified CI run itself resolved (see below)                   |

**The two lock files are a deliberate correction, not an incidental
edit.** The candidate's `uv.lock` contained no `epd2-document-service`
entry at all: this environment has no package-registry access, so `uv
lock` could never be run here and the committed lock stayed behind the
workspace it was supposed to describe. CI regenerated both files during
the verified run. Shipping the candidate's stale lock would mean the
archive's lock is not the lock that passed, so the CI-produced files are
carried over instead. The `uv.lock` change is +22 lines, all of them the
`epd2-document-service` workspace member and its two dependency edges;
the `package-lock.json` change is a single `"dev": true` flag.

**No implementation file was touched.** No file under
`services/*/src/`, `services/*/tests/`, `packages/`, `contracts/`,
`frontend/`, `scripts/`, `tests/`, `docs/adr/`, `docs/packs/`,
`docs/architecture/` or `docs/canonical/` differs from CANDIDATE-8.

## 7. Correspondence between the CI tree and this archive

A recursive comparison of the candidate tree against the verification
tree found no difference in any source, test, contract, schema,
documentation or configuration file. The only differences were:

- build and run artifacts present only in the CI tree
  (`__pycache__/`, `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`,
  `.hypothesis/`, `node_modules/`, `.next/`, `tsconfig.tsbuildinfo`,
  Playwright `test-results/`), all excluded from this archive;
- a nested `epd2-civic-os/` copy of the repository that the CI packaging
  step produced, excluded from this archive;
- `VERIFICATION-RESULT.md` and `VERIFICATION.log`, of which the log is
  carried into `docs/handover/` and the one-page result is quoted in
  section 4;
- `uv.lock` and `package-lock.json`, carried over as described in
  section 6;
- `docs/frontend/FRONT-00-PAGE-INVENTORY.csv`, whose content is
  character-identical and differs only in line endings; the committed
  CRLF form is kept, so this archive introduces no change there.

## 8. Checks re-run locally, and checks accepted from CI

Re-run locally in this environment, on the tree extracted from the
delivered archive:

- `scripts/check_repository.py` — 672 required paths present
- `scripts/check_forbidden_files.py` — no forbidden paths
- `scripts/verify_versions.py` — all version sources consistent
- `scripts/check_canon_0_8_0.py` — 18 of 18 canon checks
- `ruff check .` and `ruff format --check .`
- `mypy`, all 21 Makefile groups
- `pytest`, the full suite
- the `epd2-types` TypeScript test file

Accepted from the external CI run and **not** independently reproducible
here, because this environment has no package-registry access:

- `npm run format:check` under the locked Prettier 3.9.6 — locally only
  3.8.1 is available, and it disagrees with 3.9.6 on three pre-existing
  PACK-10/FRONT-00 files that CI accepts
- `eslint`, `tsc --noEmit`, the frontend unit tests, `next build`, and
  the Playwright browser, visual and accessibility suites — all require
  `node_modules`
- the additional 34 TypeScript tests, for the same reason
- lock-file regeneration

## 9. What this PASS does not claim

A green pipeline is evidence that the code builds, type-checks, lints and
behaves as its tests specify. It is not evidence of any of the
following, and none of these is claimed anywhere in this archive:

- **No production readiness.** Every storage adapter in
  `services/document-service/storage.py` is in-memory. There is no
  durable database, no real content store, no event bus and no
  operational deployment. The production data plane is PACK-13's.
- **No legal activation.** Nothing here makes a document legally
  effective, a publication legally valid, or a retention schedule legally
  sufficient. Those are human legal judgements made outside this system,
  behind their own gates.
- **No evidential admissibility.** The service records governed
  determinations about signature status and admissibility; it does not
  make them true. No output of this service establishes that any document
  is admissible before any court, tribunal or party organ.
- **No signature verification.** No cryptographic signature is validated
  anywhere in this round. A signature determination is a recorded
  governed decision with an attributed author, not a verification result.
- **No full tamper resistance.** The version chain gives tamper
  _evidence_, not tamper _resistance_: it detects modification, refuses
  to act on a broken history and refuses to build on top of one. An actor
  with write access to the store can still rewrite history and recompute
  the chain. There is no external anchor for the chain head. This is
  stated in full in `docs/handover/PACK-11-KNOWN-LIMITATIONS.md` and is
  not softened by CI passing.
- **No completion of the eight foundation-only FIR entries.** See
  section 3.
- **No document or evidence UI.** No frontend surface for this context
  exists in this round.

Each of the above requires its own separate, governed activation gate.
CI is not one of them.

## 10. Status

**PACK-11 GOVERNED DOCUMENTS & EVIDENCE 0.11.0 — FINAL PASS.**

This archive is the current authoritative cumulative baseline, replacing
`EPD2_PACK-10_PARTY_FINANCE_0.10.0_FINAL_PASS.zip`.

`REPOSITORY_VERSION = 0.11.0`. `CANON_VERSION = 0.8.0`.
