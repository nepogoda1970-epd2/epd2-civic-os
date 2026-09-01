# INFRA-01 — Acceptance Matrix

**Stage:** `INFRA-01 — CI Acceptance Harness & Release-Integrity Foundation`
**Mode:** `PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED`

Result vocabulary (assignment §16): `EXECUTED AND PASS`, `EXECUTED AND
FAIL`, `NOT EXECUTED / BLOCKED`, `NOT APPLICABLE BY GOVERNED RULE`. Nothing
below is inferred from source inspection; every `EXECUTED AND PASS` row is
backed by a captured execution log whose SHA-256 is recorded in the sealed
execution manifest of the delivered evidence bundle. Exact run identity
(run ID, timestamps, freeze tree digest, final archive SHA-256) lives in
that bundle — a candidate cannot contain its own archive hash.

## 1. Hard invariants

| Invariant                                                | Status            | Evidence                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| -------------------------------------------------------- | ----------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| INFRA01-HI-01 exact candidate identity                   | EXECUTED AND PASS | `bootstrap.identity` check; identity block of the sealed manifest binds commit, tree, versions, lock digests, workflow, harness version; `IDENTITY_INCOMPLETE`/`DIRTY_TREE` fail closed; evidence validator rejects incomplete identity                                                                                                                                                                                                                                       |
| INFRA01-HI-02 tested bytes == packaged bytes             | EXECUTED AND PASS | `freeze.*`, `package.build`, `verify-package.byte-identity` checks; freeze inventory + tree digest; archive-side byte re-proof; mutations M05/M06/M14                                                                                                                                                                                                                                                                                                                         |
| INFRA01-HI-03 mandatory checks cannot disappear          | EXECUTED AND PASS | machine-readable registry, 43 governed checks (registry 1.1.0, incl. the C1 governance-freshness gate), manifest accountability for each; `MANDATORY_CHECK_MISSING` (mutation M08); stale-governance detection `STALE_GOVERNANCE_STATE`/`GOVERNANCE_TRANSITION_MISSING` (mutations M17-M20); exact-delta accounting `CORRECTION_INVENTORY_MISMATCH` and temporal provenance `RECONCILIATION_TIME_INVALID` (mutations M21-M22); harness files pinned in required-path registry |
| INFRA01-HI-04 no fake PASS                               | EXECUTED AND PASS | executor sentinel/count/zero-test semantics; evidence re-reconciliation from logs; mutations M02/M07/M09                                                                                                                                                                                                                                                                                                                                                                      |
| INFRA01-HI-05 adversarially tested validator             | EXECUTED AND PASS | 21/21 negative mutation classes detected by 21 distinct detector codes (M01-M16, C1 freshness M17-M19, C2 exact-delta/temporal M21-M22; M20 is the mandatory positive history fixture) (`test_infra01_mutation_suite.py`, executed inside `backend.pytest`)                                                                                                                                                                                                                   |
| INFRA01-HI-06 freeze/package hygiene                     | EXECUTED AND PASS | `verify-package.hygiene`; forbidden dirs/files/suffixes, nested repos/archives, duplicate and machine-local paths; single governed allowlist; mutations M04/M15                                                                                                                                                                                                                                                                                                               |
| INFRA01-HI-07 frozen artifact integrity                  | EXECUTED AND PASS | 7 pinned artifacts verified at 5 lifecycle points (`bootstrap.frozen-pre-test`, `frozen.post-test`, `freeze.frozen-pre-package`, staged-byte check in `package.build`, `verify-package.frozen-in-archive`); PACK-25C6-equivalent test-output isolation; mutation M03                                                                                                                                                                                                          |
| INFRA01-HI-08 secret leakage hard gate                   | EXECUTED AND PASS | `secrets.tree-scan`, `verify-package.secret-scan`, `verify-package.evidence-sanitation`; line-pinned governed allowlist (3 entries, all synthetic); mutation M10                                                                                                                                                                                                                                                                                                              |
| INFRA01-HI-09 deployment/release identity foundation     | EXECUTED AND PASS | schema + validator + example; mixed-version-without-matrix fails closed (unit-proven); `validate-deployment-manifest` CLI                                                                                                                                                                                                                                                                                                                                                     |
| INFRA01-HI-10 runtime readiness contract foundation      | EXECUTED AND PASS | schema + fail-closed evaluator + example; UNKNOWN fails closed, stale watermark NOT_READY (unit-proven); `evaluate-readiness` CLI                                                                                                                                                                                                                                                                                                                                             |
| INFRA01-HI-11 ingress/gateway non-ownership              | EXECUTED AND PASS | `boundaries.non-ownership` mandatory stage; domain-import and workflow-marker scans clean on this candidate                                                                                                                                                                                                                                                                                                                                                                   |
| INFRA01-HI-12 sovereign-infrastructure profile readiness | EXECUTED AND PASS | mandatory machine-readable sovereignty profile in every deployment manifest; no provider chosen; UNDECIDED explicit                                                                                                                                                                                                                                                                                                                                                           |

## 2. Canonical stage/check matrix

The authoritative machine-readable matrix is the `results` array of
`EXECUTION-MANIFEST.json` in the evidence bundle. The complete registry
executed on the delivered candidate:

<!-- STAGE-MATRIX:BEGIN -->

| Stage                   | Check                                 | Result            | Executed-test evidence                 |
| ----------------------- | ------------------------------------- | ----------------- | -------------------------------------- |
| bootstrap               | `bootstrap.identity`                  | EXECUTED AND PASS | —                                      |
| bootstrap               | `bootstrap.tools`                     | EXECUTED AND PASS | —                                      |
| bootstrap               | `bootstrap.registry-integrity`        | EXECUTED AND PASS | —                                      |
| bootstrap               | `bootstrap.frozen-pre-test`           | EXECUTED AND PASS | —                                      |
| verify-governance       | `governance.canonical-registers`      | EXECUTED AND PASS | —                                      |
| verify-governance       | `governance.freshness-reconciliation` | EXECUTED AND PASS | —                                      |
| verify-governance       | `governance.pilot-roadmap-lock`       | EXECUTED AND PASS | —                                      |
| verify-repository       | `repository.required-paths`           | EXECUTED AND PASS | —                                      |
| verify-repository       | `repository.forbidden-paths`          | EXECUTED AND PASS | —                                      |
| verify-repository       | `repository.version-consistency`      | EXECUTED AND PASS | —                                      |
| verify-repository       | `repository.canon-0-8-0`              | EXECUTED AND PASS | —                                      |
| verify-dependencies     | `dependencies.uv-sync-frozen`         | EXECUTED AND PASS | —                                      |
| verify-dependencies     | `dependencies.npm-ci`                 | EXECUTED AND PASS | —                                      |
| verify-dependencies     | `dependencies.locks-unchanged`        | EXECUTED AND PASS | —                                      |
| verify-backend          | `backend.ruff-format`                 | EXECUTED AND PASS | —                                      |
| verify-backend          | `backend.ruff-lint`                   | EXECUTED AND PASS | —                                      |
| verify-backend          | `backend.mypy`                        | EXECUTED AND PASS | —                                      |
| verify-backend          | `backend.pytest`                      | EXECUTED AND PASS | pytest: 5922 passed                    |
| verify-backend          | `backend.security-suites`             | EXECUTED AND PASS | pytest: 157 passed                     |
| verify-frontend         | `frontend.prettier`                   | EXECUTED AND PASS | —                                      |
| verify-frontend         | `frontend.typecheck-types`            | EXECUTED AND PASS | —                                      |
| verify-frontend         | `frontend.typecheck-web-shell`        | EXECUTED AND PASS | —                                      |
| verify-frontend         | `frontend.eslint`                     | EXECUTED AND PASS | —                                      |
| verify-frontend         | `frontend.test-types`                 | EXECUTED AND PASS | nodetest: 3 passed                     |
| verify-frontend         | `frontend.test-web-shell`             | EXECUTED AND PASS | nodetest: 41 passed, vitest: 23 passed |
| verify-build            | `build.next-build`                    | EXECUTED AND PASS | —                                      |
| verify-browser          | `browser.playwright`                  | EXECUTED AND PASS | playwright: 135 passed                 |
| verify-accessibility    | `accessibility.playwright-a11y`       | EXECUTED AND PASS | playwright: 63 passed                  |
| verify-visual           | `visual.playwright-visual`            | EXECUTED AND PASS | playwright: 15 passed                  |
| verify-secrets          | `secrets.tree-scan`                   | EXECUTED AND PASS | —                                      |
| verify-frozen-artifacts | `frozen.post-test`                    | EXECUTED AND PASS | —                                      |
| verify-boundaries       | `boundaries.non-ownership`            | EXECUTED AND PASS | —                                      |
| verify-evidence         | `evidence.reconciliation`             | EXECUTED AND PASS | —                                      |
| freeze                  | `freeze.preconditions`                | EXECUTED AND PASS | —                                      |
| freeze                  | `freeze.inventory`                    | EXECUTED AND PASS | —                                      |
| freeze                  | `freeze.frozen-pre-package`           | EXECUTED AND PASS | —                                      |
| package                 | `package.build`                       | EXECUTED AND PASS | —                                      |
| verify-package          | `verify-package.byte-identity`        | EXECUTED AND PASS | —                                      |
| verify-package          | `verify-package.hygiene`              | EXECUTED AND PASS | —                                      |
| verify-package          | `verify-package.frozen-in-archive`    | EXECUTED AND PASS | —                                      |
| verify-package          | `verify-package.secret-scan`          | EXECUTED AND PASS | —                                      |
| verify-package          | `verify-package.evidence-sanitation`  | EXECUTED AND PASS | —                                      |
| emit-manifest           | `manifest.emit`                       | EXECUTED AND PASS | —                                      |

<!-- STAGE-MATRIX:END -->

### Executed-test evidence summary (canonical run on this candidate)

43/43 governed checks `EXECUTED AND PASS` (registry 1.1.0, including the
governance-freshness gate with C2 temporal-provenance enforcement); 0
`FAIL`, 0 `BLOCKED`, 0 `NOT APPLICABLE BY GOVERNED RULE`. Positive
executed-test evidence: pytest 5922 passed (full suite) plus 157 passed
(explicit adversarial/security re-execution); node:test 3 (epd2-types) +
41 (web-shell); vitest 23 render tests; Playwright 135 browser, 63
accessibility, 15 visual. Counts are parsed from the captured logs and
re-verified by the evidence validator; run identity, per-check log SHA-256,
freeze tree digest and the final archive SHA-256 are in the delivered
evidence bundle.

## 3. Delivery status

```text
INFRA-01 IMPLEMENTATION CANDIDATE
LOCAL CANONICAL HARNESS: PASS
EXTERNAL GOVERNED ACCEPTANCE: NOT YET PERFORMED
NOT PRODUCTION READY
NOT LEGALLY ACTIVATED
```

INFRA-01 does not close the INFRA stage. Closure remains blocked on the
governed predecessor sequence recorded in the Program Control Register and
on independent governed review of the exact frozen candidate.
