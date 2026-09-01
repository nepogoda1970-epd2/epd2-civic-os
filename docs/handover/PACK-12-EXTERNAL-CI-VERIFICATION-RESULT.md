# PACK-12 — External CI Verification Result

Status: **PASS**

Runner: GitHub Actions / ubuntu-latest
Repository version: `0.12.0`
Canon version: `0.8.0`
Evidence archive (retained outside this repository):
`epd2-civic-os-verification-result(14).zip`

This workflow is pack-agnostic: it verifies whatever pack(s) are
implemented in the checked-out tree at run time. This document records
the run that applies to PACK-12; the pack-specific report is
`docs/handover/PACK-12-FINAL-PASS-REPORT.md`.

---

## 1. Results

| Check                    | Result                            |
| ------------------------ | --------------------------------- |
| Repository path manifest | **PASS** — 728 / 728              |
| Forbidden paths          | **PASS** — none present           |
| Ruff format              | **PASS**                          |
| Prettier                 | **PASS**                          |
| Ruff lint                | **PASS**                          |
| mypy                     | **PASS**                          |
| TypeScript typecheck     | **PASS**                          |
| Python test suite        | **PASS** — 4062 passed, 4 skipped |
| Browser / frontend suite | **PASS** — 108 passed             |
| Accessibility checks     | **PASS**                          |
| Visual checks            | **PASS**                          |

---

## 2. Provenance of these figures — stated plainly

**The evidence archive was not available inside the build environment
that assembled the FINAL PASS archive.** The figures in section 1 are
recorded **as reported by the operator** from the external GitHub Actions
run, not re-derived here and not re-executed here.

This is a narrower evidentiary basis than PACK-11's, where the raw CI
transcript was present in the packaging environment and was committed as
`docs/handover/PACK-11-EXTERNAL-CI-VERIFICATION.log`. No equivalent
`PACK-12-EXTERNAL-CI-VERIFICATION.log` exists in this repository, because
inventing a transcript that nobody produced would be worse than not
having one. The authoritative artifact remains
`epd2-civic-os-verification-result(14).zip`, held outside the repository:
per this round's own instruction, no nested ZIP is placed inside the
FINAL PASS archive.

## 3. What _was_ independently corroborated

Two figures were checked against the packaged tree rather than accepted
on trust, and both agree exactly:

| Figure                   | CI reported      | Recomputed from the packaged tree                                                 |
| ------------------------ | ---------------- | --------------------------------------------------------------------------------- |
| Repository path manifest | 728 / 728        | `len(scripts.check_repository.REQUIRED_PATHS)` = **728**, all unique, all present |
| Python tests             | 4062 / 4 skipped | **4054 passed / 5 skipped** locally, reconciled exactly — see below               |

The eight-test difference is fully explained and is an artefact of this
environment, not of the tree. `tests/contract/test_property_based.py`
calls `pytest.importorskip("hypothesis")`; `hypothesis` cannot be
installed here (the package registries are unreachable), so the whole
module is skipped locally and its tests do not run. Adding that module
back accounts for both numbers: 4054 + the property-based module = 4062,
and 5 local skips − 1 (that module, which runs in CI) = 4.

Everything else in section 1 — Prettier, TypeScript, the browser suite,
accessibility and visual checks — depends on `npm ci` and is accepted
from the external run without local corroboration. Sections 8 and 9 of
`docs/handover/PACK-12-FINAL-PASS-REPORT.md` state which local checks
were re-run after the documentation edits in this packaging round.

---

## 4. What this PASS does not establish

A green pipeline is evidence that the repository builds, type-checks,
lints, formats and tests cleanly. It is not evidence of any of the
following, none of which PACK-12 implements or claims:

- production readiness or operational deployment;
- legal validity, legal activation or admissibility;
- a production database, event bus or search engine;
- an external IAM or identity provider, MFA, or HSM/PKI;
- a production DLP provider or real content inspection;
- real out-of-band notification delivery;
- production session assurance;
- anything in the voting domain.
