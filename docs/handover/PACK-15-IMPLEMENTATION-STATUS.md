# PACK-15 — Implementation status and verification matrix

```text
PACK-15 IMPLEMENTATION CANDIDATE
PARTIAL LOCAL VERIFICATION ONLY
DEPENDENCY INSTALLATION BLOCKED BY SANDBOX NETWORK POLICY
EXTERNAL CI NOT YET VERIFIED
NOT FINAL PASS
NOT PRODUCTION READY
NOT LEGALLY ACTIVATED
```

**`REPOSITORY_VERSION` is `0.15.0`. `CANON_VERSION` remains `0.8.0`.**

The version moved, the register was updated and the archive is named a
candidate because all five remaining implementation groups are now
present and wired. That ordering was the previous round's own rule and it
was kept: the earlier revision of this file recorded five open groups and
refused all three of those steps while they were open.

---

## 1. The five groups that were open, and what closed them

| Group                                  | Closed by                                                                                                                                                                                                                                                         |
| -------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1. Durable persistence and migrations  | Ten migration files across seven migration sets; SQL adapters for every store port in four services; two composition roots binding them by default; transactional and concurrency tests including an eight-thread contention test on the participation-unit claim |
| 2. Versioned API                       | `epd2_core.api_contracts` plus four per-service endpoint catalogues and reference adapters — 22 endpoints, each declaring its obligations, its authorized roles and its reason codes                                                                              |
| 3. Event JSON schemas                  | Eight payload schemas with contract tests (closed in the previous round; unchanged here)                                                                                                                                                                          |
| 4. Authorization and separation matrix | `voting_authorization` — ten roles, a capability matrix validated at import time, eight structural separation rules                                                                                                                                               |
| 5. Implementation evidence             | `PACK-15-IMPLEMENTATION-REPORT.md`, `PACK-15-TEST-EVIDENCE.md`, `PACK-15-SECURITY-EVIDENCE.md`, `PACK-15-PRIVACY-EVIDENCE.md`, `PACK-15-TRACEABILITY-MATRIX.md`                                                                                                   |

---

## 2. Environment limitation, stated precisely

The two earlier revisions of this file recorded that **no** Python
tooling could run. That is no longer accurate, and it is corrected here
rather than repeated:

| Fact                   | Observed in this round                                                                     |
| ---------------------- | ------------------------------------------------------------------------------------------ |
| PyPI access            | **HTTP 403 Forbidden** — `uv sync` cannot download `pydantic==2.13.4`                      |
| npm registry access    | **HTTP 403 Forbidden** — `npm ping` returns 403                                            |
| `node_modules`         | **absent and uninstallable**                                                               |
| `uv sync --all-groups` | **cannot complete**                                                                        |
| `pytest`               | **available** (9.0.3, installed outside the project environment) and **executed**          |
| `mypy`                 | **available** and **executed**                                                             |
| `ruff`                 | **available** (0.15.11) and **executed**                                                   |
| `pydantic`, `PyYAML`   | **available to the system interpreter**                                                    |
| `hypothesis`           | **unavailable** — the property-based module skips itself rather than passing vacuously     |
| Consequence            | The Python surface was really verified. The whole TypeScript and frontend surface was not. |

Because the tools run from outside the project environment, they resolve
to versions `uv.lock` does not pin. **External CI remains the
authoritative run**: a check that passes here has passed against _a_
supported version, not against the locked one.

**No CI check was weakened, disabled or removed. No lock file was
modified. No test result was fabricated.**

---

## 3. Verification matrix

| #   | Required check                                       | Result                                                                                             |
| --- | ---------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| 1   | `scripts/check_repository.py` — repository structure | **PASS** — all 983 required paths present                                                          |
| 2   | `scripts/check_forbidden_files.py` — forbidden paths | **PASS** — no forbidden paths found                                                                |
| 3   | `scripts/verify_versions.py` — version consistency   | **PASS** — consistent at `0.15.0` / `0.8.0`                                                        |
| 4   | Canon checks (`check_canon_0_8_0.py`)                | **PASS** — all 18 amendment checks                                                                 |
| 5   | `ruff format --check`                                | **PASS** — 436 files                                                                               |
| 6   | `ruff check` (lint)                                  | **PASS**                                                                                           |
| 7   | `mypy` (per group)                                   | **PASS** — no issues in any Python group                                                           |
| 8   | `pytest`                                             | **PASS** — 5335 passed, 5 skipped                                                                  |
| 9   | TypeScript tests (`epd2-types`)                      | **NOT EXECUTED — ENVIRONMENT BLOCKED**                                                             |
| 10  | Frontend tests (`web-shell`)                         | **NOT EXECUTED — ENVIRONMENT BLOCKED**                                                             |
| 11  | Frontend lint / typecheck                            | **NOT EXECUTED — ENVIRONMENT BLOCKED**                                                             |
| 12  | `next build`                                         | **NOT EXECUTED — ENVIRONMENT BLOCKED**                                                             |
| 13  | Playwright browser tests                             | **NOT EXECUTED — ENVIRONMENT BLOCKED**                                                             |
| 14  | Accessibility tests (axe)                            | **NOT EXECUTED — ENVIRONMENT BLOCKED**                                                             |
| 15  | Visual regression                                    | **NOT APPLICABLE** — no PACK-15 screenshot baselines were added, and none can be generated offline |
| 16  | Prettier `format:check`                              | **NOT EXECUTED — ENVIRONMENT BLOCKED**                                                             |
| 17  | `uv sync --frozen`                                   | **NOT EXECUTED — ENVIRONMENT BLOCKED**                                                             |
| 18  | Property-based tests (`hypothesis`)                  | **NOT EXECUTED — ENVIRONMENT BLOCKED**                                                             |

CI's lock-file guard — `git diff --exit-code -- uv.lock package-lock.json`
after `uv sync --frozen` — will pass, because neither file was touched.
That is asserted here by inspection, not by execution.

Twenty-nine lint findings and twenty formatting differences were present
when `ruff` was first run against this round's work. All were fixed. No
rule was disabled, no `noqa` was added, and no check was narrowed. Two of
them were fixed by changing a **test** rather than a rule, because the
tools had found the tests were weak: a `pytest.raises(Exception)` that
would have passed on any failure now names
`IssuanceWindowGuaranteeError`, and a test asserting that two distinct
enum members are distinct now asserts the property that actually
differs — `review_required` retains a path to `approved`, `denied` does
not, and the only route out of a denial is a dispute.

---

## 4. What remains unverified

The five PACK-15 frontend artefacts and their three test files exist, are
registered in `scripts/check_repository.py`, and **have never been
executed, type-checked or rendered**:

```
frontend/web-shell/foundation/voting-trust-policy.ts
frontend/web-shell/public/voting-content.ts
frontend/web-shell/components/voting-trust.tsx
frontend/web-shell/app/mitwirkung/abstimmungen/page.tsx
frontend/web-shell/app/vote/page.tsx
frontend/web-shell/tests/pack15.test.ts
frontend/web-shell/tests/pack15.render.test.tsx
frontend/web-shell/tests/browser/pack15.browser.spec.ts
```

The participant-facing half of this pack depends on that code. None of
the structural guarantees does — those live in the schema and the Python
layer, and they were executed — but the isolated voting origin _as an
experience someone uses_ is unverified until external CI runs.

Also unverified, and not defects: production key custody (unbound and
refusing by design), any transport layer (the API is transport-agnostic
values), and the concurrency behaviour of anything other than SQLite.

---

## 5. Invariant coverage actually demonstrated

Each row is asserted by an executed, passing test — not by a document.
The full mapping is in `PACK-15-TRACEABILITY-MATRIX.md`; these are the
load-bearing ones.

| Invariant                                     | Demonstrated by                                                                                                                                                                                         |
| --------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `NO PERSON-TO-BALLOT LINK`                    | `spent_nonce` has exactly three columns and no value column, asserted against a real migrated schema; no voting-side table carries an identity-side column; no foreign key leaves its own database file |
| `ELIGIBILITY != VOTING CREDENTIAL`            | Separate services, separate database files, a five-field minimized issuer input                                                                                                                         |
| `NO GLOBAL USER ID`                           | Every prohibited attribute refused at the adapter; the twelve-field closed assertion; response and request scans at every nesting depth                                                                 |
| `NO INTERMEDIATE TALLY`                       | Outcome keys refused before closure; pre-closure bundles carry no totals and require dual control as a CHECK constraint                                                                                 |
| `NO IDENTITY-SIDE REDEMPTION STATUS`          | No endpoint accepts a participant reference; `credential.status` answers only against a reference the caller holds, and an unknown one returns the same shape as a withdrawn one                        |
| `NO PERSON-LEVEL REVOCATION AFTER REDEMPTION` | `redeemed` is absorbing; the revocation signature has no participant parameter; a post-cutoff revocation fails a CHECK                                                                                  |
| Exactly-once, both halves                     | Eight threads racing one participation-unit claim produce exactly one winner; a second redemption of one credential raises `IntegrityError`                                                             |
| No failure disenfranchises                    | A refused mint leaves no claim behind, even after a later successful write commits on the same connection                                                                                               |
| Separation of duties                          | No role holds eligibility, issuance and tally; no auditor spans the audit stream groups; privileged export needs two distinct approvers in different roles                                              |
| Timing controls                               | A cohort of one is never released early, and is released anyway at the deadline; every hard floor refuses rather than clamping                                                                          |
| Delivery boundary                             | All ten prohibited channels refused; only `isolated_ws03_origin` permitted                                                                                                                              |

---

## 6. Next round

External CI verification against
`EPD2_PACK-15_VOTING_TRUST_BOUNDARY_ELIGIBILITY_CREDENTIAL_SEPARATION_0.15.0_CANDIDATE.zip`.

It is not PACK-16 and it is not a final pass. **Do not proceed to
PACK-16.**

---

**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. NOT A FINAL PASS.**
