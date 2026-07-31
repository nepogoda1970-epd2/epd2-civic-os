# PACK-15 — Repository hygiene correction

```text
PACK-15 IMPLEMENTATION CANDIDATE
HYGIENE CORRECTED
EXTERNAL CI NOT YET VERIFIED
NOT FINAL PASS
NOT PRODUCTION READY
NOT LEGALLY ACTIVATED
```

**Repository version:** `0.15.0` (unchanged) · **Canon version:** `0.8.0` (unchanged)
**Archive:** `EPD2_PACK-15_VOTING_TRUST_BOUNDARY_ELIGIBILITY_CREDENTIAL_SEPARATION_0.15.0_CANDIDATE_HYGIENE_CORRECTED.zip`

---

## 1. Why this round exists, and why it is not a FINAL PASS

External GitHub Actions passed against the PACK-15 candidate. FINAL PASS
packaging was therefore proposed. Comparing the returned verification
artifact against the candidate tree, byte for byte, showed that **the tree
GitHub verified was not the candidate tree.** It was the candidate tree
plus a complete stale copy of the repository at `epd2-civic-os/`, plus
test-run artifacts, build outputs and scratch files.

That is not a packaging detail. `epd2-civic-os/` holds its own
`version.py` declaring `REPOSITORY_VERSION = "0.6.0"` and
`CANON_VERSION = "0.6.0"`, its own `uv.lock`, its own
`package-lock.json` and its own `pyproject.toml` — a PACK-07-era snapshot
of the whole system sitting inside a `0.15.0` release. Shipping it inside
an archive named FINAL PASS would put two contradictory version
declarations in one artifact and would violate the hygiene rule against
duplicate repository trees.

Removing it changes the verified tree. A FINAL PASS may only be issued
against a tree GitHub has actually run, so **this round produces a
candidate and the external run has to happen again.** The previous
verification artifact is explicitly **not** evidence for the tree
described here.

---

## 2. The arithmetic that identified the problem

The external run reported **Ruff format: PASS — 609 files**. The candidate
tree contains 436 Python files, and every local run of
`ruff format --check .` reported exactly that number. The difference was
not a version discrepancy:

```
436  Python files in the candidate tree (root)
173  Python files inside epd2-civic-os/
---
609  Python files reported by external CI
```

The nested copy was inside the scope of the external Ruff run. It was not
inside the scope of the external pytest run: `pyproject.toml` declares
`testpaths` explicitly and root-relative, so no test was ever collected
from it. The external test delta (5343 passed / 4 skipped against 5335
passed / 5 skipped locally) is separately explained: `hypothesis` is
installed in CI and absent here, so `tests/contract/test_property_based.py`
runs there and skips here — one fewer skip, eight more passes.

This directory has been flagged before. PACK-08's implementation report,
PACK-10's and PACK-11's FINAL PASS reports, and PACK-14's external CI
result all recorded it and recommended deletion. This round carries that
recommendation out.

---

## 3. What was removed

Measured against the externally verified tree contained in the
verification artifact:

| Category                                   |     Files |          Bytes |
| ------------------------------------------ | --------: | -------------: |
| `__pycache__/` and `*.pyc`                 |       435 |     12,498,114 |
| `epd2-civic-os/` — stale nested repository |       435 |      4,461,344 |
| `.hypothesis/` — test-run artifacts        |       253 |        160,429 |
| `.ruff_cache/`                             |        48 |         30,096 |
| Root scratch files                         |         5 |         74,386 |
| Playwright run output                      |         2 |        593,856 |
| TypeScript build output (`*.tsbuildinfo`)  |         1 |        116,913 |
| `.pytest_cache/`, `.mypy_cache/`           |         7 |              — |
| **Total removed**                          | **1,186** | **17,935,138** |

Of `epd2-civic-os/`'s 435 files, 435 are its own content (390 source files
plus its caches); 173 of them are Python, which is the Ruff delta above.

The five root scratch files were `VERIFICATION.log`,
`VERIFICATION-RESULT.md`, `DELETE.txt`,
`PACK-12-CI-FORMAT-CORRECTION.md` and
`PACK-12-CI-FORMAT-CORRECTION-2.md`. `DELETE.txt` was itself an action
list instructing the deletion of a path that has since been deleted.

**Nothing was copied out of the nested repository into the root.** The
cleaned tree is the externally verified root tree with the categories
above removed and nothing added except this report.

---

## 4. What was kept, and two deliberate deltas

The cleaned tree is byte-identical to the PACK-15 candidate tree except
for three files, all of them root-tree content present in the externally
verified state:

| File                                                 | Status                                                                                                       |
| ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| `docs/handover/PACK-01-VERIFICATION.log`             | present in the verified tree, absent from the candidate; retained as project record                          |
| `docs/handover/PACK-14-EXTERNAL-CI-VERIFICATION.log` | the verified tree's copy, which differs from the candidate's by three stray `\r` characters on lines 644-646 |
| `docs/handover/PACK-15-HYGIENE-CORRECTION-REPORT.md` | this file                                                                                                    |

No implementation source, migration, contract, event schema, reason code,
test, CI definition, lock file or frontend file differs from the
candidate.

---

## 5. Confirmations required by the correction task

| Requirement                                               | Result                                                                                                                           |
| --------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| Only the nested stale repository removed (plus artifacts) | **Confirmed** — see section 3                                                                                                    |
| No root implementation semantics changed                  | **Confirmed** — zero source, test, contract or CI files differ from the candidate                                                |
| Root versions preserved                                   | **Confirmed** — `REPOSITORY_VERSION 0.15.0`, `CANON_VERSION 0.8.0` in both the Python and TypeScript sources                     |
| No file copied from the nested repository into the root   | **Confirmed** — the cleaned tree was assembled by exclusion, never by copying out of `epd2-civic-os/`                            |
| Root `uv.lock` / `package-lock.json` unmodified           | **Confirmed**                                                                                                                    |
| Master Register unmodified                                | **Confirmed** — no FINAL PASS record is written, because there is no FINAL PASS                                                  |
| Required-path checks did not depend on nested paths       | **Confirmed** — `scripts/check_repository.py` never referenced `epd2-civic-os/`; `check_repository.py` reports 983/983 unchanged |
| No root import, build, test or contract references it     | **Confirmed** — see section 6                                                                                                    |
| No duplicate repository tree remains                      | **Confirmed** — one `version.py`, one `uv.lock`, one `package-lock.json` in the whole archive                                    |

---

## 6. Reference scan

Every occurrence of the string `epd2-civic-os` in the cleaned tree was
examined. There are 42 files containing it, and not one is a dependency on
the removed directory:

- **the project's own name** — `package.json`, `package-lock.json`,
  `pyproject.toml`, `uv.lock` (`name = "epd2-civic-os"`);
- **the CI artifact's name** —
  `.github/workflows/verify-and-package.yml` builds
  `epd2-civic-os-verification-result.zip`;
- **the GitHub runner's checkout path** inside historical verification
  logs (`/home/runner/work/epd2-civic-os/epd2-civic-os`);
- **a directory-tree illustration** in `README.md` line 801, where
  `epd2-civic-os/` labels the repository root itself;
- **prose in earlier handover reports** that flagged this very directory
  and recommended its deletion.

No `import`, no `testpaths` entry, no mypy target, no Makefile rule, no
workflow step and no contract path resolves into `epd2-civic-os/`.

---

## 7. Local verification of the cleaned tree

Re-run in full after the removal. These are local results and are **not**
a substitute for the external run this tree still needs.

| Check                                 | Result                                                                                                                                                                                    |
| ------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `scripts/check_repository.py`         | **PASS** — all 983 required paths present                                                                                                                                                 |
| `scripts/check_forbidden_files.py`    | **PASS** — no forbidden paths found                                                                                                                                                       |
| `scripts/verify_versions.py`          | **PASS** — consistent at `0.15.0` / `0.8.0`                                                                                                                                               |
| `scripts/check_canon_0_8_0.py`        | **PASS** — all 18 amendment checks                                                                                                                                                        |
| `ruff format --check .`               | **PASS** — **436 files** (was 609 with the duplicate)                                                                                                                                     |
| `ruff check .`                        | **PASS**                                                                                                                                                                                  |
| `mypy`, all 23 groups                 | **PASS** — no issues in any group                                                                                                                                                         |
| `pytest`                              | **PASS** — 5335 passed, 5 skipped                                                                                                                                                         |
| Prettier                              | **NOT AUTHORITATIVE HERE** — only 3.8.1 is installable; the lock pins 3.9.6. It reports three files, which are the three deliberately held in 3.9.6 form after the last correction round. |
| npm typecheck / build / browser tests | **NOT EXECUTED — ENVIRONMENT BLOCKED**                                                                                                                                                    |

The expected external numbers change with this correction: **Ruff format
should report 436 files, not 609.** Any re-run still reporting 609 means
the nested directory is still present in the pushed branch.

---

## 8. Verification artifact digests

Recomputed from the supplied file rather than transcribed:

| Artifact                    | SHA-256                                                            | Status                                                                                             |
| --------------------------- | ------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------- |
| Outer verification artifact | `675efb9377c68d938d0be189b91b0f1033b6b56b7801c7604e6cbb63cc8582ca` | **matches** the supplied value                                                                     |
| Internal verification ZIP   | `d5bba0a6a7a6e7330556e80161f80d072c4124105c8a8d5b13fa1c214912e943` | **does not match** the supplied `f3b07b3c01d3cc87c00c0b140b3951d0c6e66090c8b0f3f99dfbca08fa28b2c4` |

The value recorded here is the one computed from the file inside the
verified outer artifact. The discrepancy is recorded rather than
reconciled: the outer digest matching exactly means the artifact was not
altered in transit, so the mismatch concerns which internal ZIP the
supplied digest describes, which is a question for the party that produced
it.

**Neither artifact is evidence for the tree described in this report.**
They describe the tree that still contained `epd2-civic-os/`.

---

## 9. What has to happen next

1. Push the cleaned tree.
2. Run GitHub Actions against it in full.
3. Confirm Ruff format reports **436 files**.
4. Only then package FINAL PASS, recording that run's numbers.

**Do not proceed to PACK-16.**
