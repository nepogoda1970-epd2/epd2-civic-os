# PACK-15 — Test evidence

```text
PACK-15 IMPLEMENTATION CANDIDATE
PARTIAL LOCAL VERIFICATION ONLY
DEPENDENCY INSTALLATION BLOCKED BY SANDBOX NETWORK POLICY
EXTERNAL CI NOT YET VERIFIED
NOT FINAL PASS
NOT PRODUCTION READY
NOT LEGALLY ACTIVATED
```

This file records **what was executed and what was not**. Every number
below was produced by running the command shown; nothing here is
estimated, and no result is reported for a check that did not run.

---

## 1. What the environment allows, as observed in this round

The two earlier PACK-15 rounds recorded that no Python tooling could run
at all. That is **no longer accurate for the Python side**, and this file
corrects it rather than repeating it:

| Tool                 | Status in this round                                                                  | Evidence                                             |
| -------------------- | ------------------------------------------------------------------------------------- | ---------------------------------------------------- |
| `pytest`             | **available** — 9.0.3, installed as a standalone tool outside the project environment | `pytest --version`                                   |
| `mypy`               | **available**                                                                         | `mypy --version`                                     |
| `ruff`               | **available** — 0.15.11                                                               | `ruff --version`                                     |
| `pydantic`, `PyYAML` | **available** to the system interpreter (`/usr/local/lib/python3.11/dist-packages`)   | `python3 -c "import pydantic, yaml"`                 |
| `hypothesis`         | **not available**                                                                     | `tests/contract/test_property_based.py` skips itself |
| PyPI                 | **HTTP 403 Forbidden**                                                                | `uv sync` cannot download `pydantic==2.13.4`         |
| npm registry         | **HTTP 403 Forbidden**                                                                | `npm ping` returns 403                               |
| `node_modules`       | **absent and uninstallable**                                                          | no `node_modules` directory exists                   |

The consequence is precise and worth stating plainly: **the Python suite
was really executed, and the whole TypeScript and frontend surface was
not.** The Python tools are present because they exist in the image, not
because `uv sync` succeeded - it did not, and `uv.lock` was not touched.

Because the tools run from outside the project environment, the commands
below set `PYTHONPATH` explicitly. The version pins those tools resolve to
are not the pins `uv.lock` names, so **external CI remains the
authoritative run**: a check that passes here has passed against _a_
supported version, not against the locked one.

---

## 2. Commands executed

```
# Full Python suite
PYTHONPATH=/usr/local/lib/python3.11/dist-packages:$(ls -d services/*/src packages/python/*/src | tr '\n' ':') \
  pytest -q

# Type checking, one group per Makefile `typecheck` target
mypy packages/python/epd2-core scripts tests/repository conftest.py
mypy tests/contract
mypy services/<name>          # once per service

# Lint and format
ruff check .
ruff format --check .

# Repository scripts
python3 scripts/check_repository.py
python3 scripts/check_forbidden_files.py
python3 scripts/verify_versions.py
python3 scripts/check_canon_0_8_0.py
```

---

## 3. Results

### 3.1 Full Python suite

```
5335 passed, 5 skipped
```

The five skips are pre-existing and each carries its own recorded reason:
one for the absent `hypothesis` package, and four CT-00 applicability
skips inherited from PACK-06 and PACK-07 whose justifications are written
into the skip messages themselves.

### 3.2 PACK-15 modules, individually

| Test module                                                              |   Tests | Result   |
| ------------------------------------------------------------------------ | ------: | -------- |
| `services/eligibility-service/tests/test_pack15_voting_trust.py`         |      52 | PASS     |
| `services/eligibility-service/tests/test_pack15_persistence.py`          |      22 | PASS     |
| `services/eligibility-service/tests/test_pack15_voting_trust_api.py`     |      37 | PASS     |
| `services/credential-service/tests/test_pack15_voting_credentials.py`    |      39 | PASS     |
| `services/credential-service/tests/test_pack15_persistence.py`           |      18 | PASS     |
| `services/credential-service/tests/test_pack15_voting_credential_api.py` |      45 | PASS     |
| `services/governance-service/tests/test_pack15_voting_contexts.py`       |      14 | PASS     |
| `services/governance-service/tests/test_pack15_persistence.py`           |      12 | PASS     |
| `services/governance-service/tests/test_pack15_voting_authorization.py`  |      37 | PASS     |
| `services/governance-service/tests/test_pack15_voting_context_api.py`    |      47 | PASS     |
| `services/audit-core/tests/test_pack15_evidence_bundle.py`               |      17 | PASS     |
| `services/audit-core/tests/test_pack15_persistence.py`                   |      18 | PASS     |
| `services/audit-core/tests/test_pack15_voting_evidence_api.py`           |      53 | PASS     |
| `tests/contract/test_pack15_event_schemas.py`                            |      11 | PASS     |
| `tests/repository/test_pack15_default_binding.py`                        |      12 | PASS     |
| **Total**                                                                | **434** | **PASS** |

### 3.3 Type checking

Every group in the `Makefile` `typecheck` target's Python half was run.
All report `Success: no issues found`. The two npm typecheck lines of that
target were not run (see section 4).

### 3.4 Lint and format

```
ruff check .          -> All checks passed!
ruff format --check . -> 436 files already formatted
```

Twenty-nine lint findings and twenty formatting differences were present
when the tools were first run against this round's work and were fixed
rather than suppressed. Two findings were fixed by changing a **test**
rather than a rule:

- `B017` (`pytest.raises(Exception)`) in
  `test_pack15_voting_trust.py` now names `IssuanceWindowGuaranteeError`,
  so the test can no longer pass because of an unrelated failure.
- A `comparison-overlap` error from mypy showed that
  `test_review_required_is_not_a_denial` was asserting a tautology - two
  distinct enum members are trivially distinct. It now asserts the
  property that actually matters: `review_required` retains a path to
  `approved` through review, `denied` does not, and the only route out of
  a denial is a dispute.

No rule was disabled, no `noqa` was added, and no check was narrowed.

### 3.5 Repository scripts

| Script                             | Result                                                                            |
| ---------------------------------- | --------------------------------------------------------------------------------- |
| `scripts/check_repository.py`      | **PASS** — all 983 required paths present                                         |
| `scripts/check_forbidden_files.py` | **PASS** — after removing `__pycache__` directories produced by running the suite |
| `scripts/verify_versions.py`       | **PASS** — all version sources consistent                                         |
| `scripts/check_canon_0_8_0.py`     | **PASS** — all 18 canon 0.8.0 amendment checks passed                             |

---

## 4. What was not executed

| Check                                           | Status                                 | Why                                                                             |
| ----------------------------------------------- | -------------------------------------- | ------------------------------------------------------------------------------- |
| `uv sync --frozen`                              | **NOT EXECUTED — ENVIRONMENT BLOCKED** | PyPI returns HTTP 403                                                           |
| `npm ci` / `npm install`                        | **NOT EXECUTED — ENVIRONMENT BLOCKED** | npm registry returns HTTP 403                                                   |
| `npm run typecheck` (`epd2-types`, `web-shell`) | **NOT EXECUTED — ENVIRONMENT BLOCKED** | no `node_modules`                                                               |
| TypeScript unit tests (`epd2-types`)            | **NOT EXECUTED — ENVIRONMENT BLOCKED** | no `node_modules`                                                               |
| Frontend tests (`web-shell`, vitest)            | **NOT EXECUTED — ENVIRONMENT BLOCKED** | no `node_modules`                                                               |
| Frontend lint (`eslint`)                        | **NOT EXECUTED — ENVIRONMENT BLOCKED** | no `node_modules`                                                               |
| `next build`                                    | **NOT EXECUTED — ENVIRONMENT BLOCKED** | no `node_modules`                                                               |
| Playwright browser tests                        | **NOT EXECUTED — ENVIRONMENT BLOCKED** | no `node_modules`, no browser install                                           |
| Accessibility tests (axe)                       | **NOT EXECUTED — ENVIRONMENT BLOCKED** | no `node_modules`                                                               |
| Prettier `format:check`                         | **NOT EXECUTED — ENVIRONMENT BLOCKED** | no `node_modules`                                                               |
| Property-based tests                            | **NOT EXECUTED — ENVIRONMENT BLOCKED** | `hypothesis` unavailable; the module skips itself rather than passing vacuously |
| Visual regression                               | **NOT APPLICABLE**                     | no PACK-15 screenshot baselines were added, and none can be generated offline   |

The five PACK-15 frontend artefacts
(`foundation/voting-trust-policy.ts`, `public/voting-content.ts`,
`components/voting-trust.tsx`, `app/mitwirkung/abstimmungen/page.tsx`,
`app/vote/page.tsx`) and their three test files are present and are wired
into `scripts/check_repository.py`, but **not one line of them has been
executed, type-checked or rendered.** They are unverified until external
CI runs.

---

## 5. What the tests actually defend

A count of passing tests says little on its own. The properties below are
the ones worth naming, each with the module that would fail first if it
stopped holding:

| Property                                                                                    | Where it is enforced                             | Where it is tested                                              |
| ------------------------------------------------------------------------------------------- | ------------------------------------------------ | --------------------------------------------------------------- |
| The spent-nonce record is a set with no value column                                        | `0002_spent_nonce_set.sql`                       | `credential-service/tests/test_pack15_persistence.py`           |
| A second redemption of one credential is a constraint violation, not a race                 | `uq_credential_redemption_credential`            | same                                                            |
| A participation unit can be claimed exactly once, under real thread contention              | `participation_unit_ledger` primary key          | `eligibility-service/tests/test_pack15_persistence.py`          |
| No foreign key crosses a trust boundary, because the boundaries are separate database files | four separate migration sets                     | both persistence modules                                        |
| A failed mint leaves no claim behind, so a failure cannot disenfranchise                    | `voting_trust_api.mint_assertion`                | `eligibility-service/tests/test_pack15_voting_trust_api.py`     |
| No API response carries an identity field, at any nesting depth                             | `epd2_core.api_contracts.assert_response_safe`   | all four API test modules                                       |
| No API request into the voting side carries an identity field, at any nesting depth         | `voting_credential_api.assert_no_identity_field` | `credential-service/tests/test_pack15_voting_credential_api.py` |
| No role holds eligibility, issuance and tally                                               | `voting_authorization`                           | `governance-service/tests/test_pack15_voting_authorization.py`  |
| No auditor role spans the identity-side and voting-side audit streams                       | same                                             | same                                                            |
| An activated context version cannot be edited in place                                      | `SqlVotingContextStore.save`                     | `governance-service/tests/test_pack15_persistence.py`           |
| The in-memory adapters are not the default runtime binding                                  | two composition roots                            | `tests/repository/test_pack15_default_binding.py`               |

---

## 6. Honest limitations

1. **The locked dependency versions were never installed.** Everything
   Python ran against tool versions that happen to be in this image. CI
   runs `uv sync --frozen`; a version-sensitive failure would appear
   there and not here.
2. **The entire frontend is unverified.** See section 4.
3. **No performance, load or soak testing was done**, and none is
   claimed.
4. **No end-to-end run across a real deployment exists.** The API layer
   is transport-agnostic by design and has no HTTP binding in this
   repository, so "the endpoint works" means "the handler, the store and
   the schema agree", not "a request over a socket succeeded".
5. **The signing custody is a reference HMAC implementation.** Real key
   custody is `FutureKeyServiceCustody`, whose every method raises. No
   test asserts anything about an HSM, because none is bound.
