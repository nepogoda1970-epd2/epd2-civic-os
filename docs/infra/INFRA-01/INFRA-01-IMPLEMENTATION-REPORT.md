# INFRA-01 — CI Acceptance Harness & Release-Integrity Foundation — Implementation Report

**Stage:** `INFRA-01 — CI Acceptance Harness & Release-Integrity Foundation`
**Mode:** `PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED`
**Repository version:** unchanged at `0.16.0` · **Canon version:** unchanged at `0.8.0`
**Entering baseline:** `nepogoda1970-epd2/epd2-civic-os` commit `8ff32c3e9ed654768ae86ac569a9c498f78c5aa2`, tree `13e1c439f8f5b0bd37cb6519f109d9f4c02f1ef9` (Entering Baseline Identity v1.1)
**Harness identity:** `EPD2-INFRA01-ACCEPTANCE-HARNESS 0.1.0`

```text
INFRA-01 IMPLEMENTATION CANDIDATE
LOCAL CANONICAL HARNESS: see INFRA-01-ACCEPTANCE-MATRIX.md
EXTERNAL GOVERNED ACCEPTANCE: NOT YET PERFORMED
NOT PRODUCTION READY
NOT LEGALLY ACTIVATED
```

This round builds infrastructure. It decides no business-domain acceptance by
assertion, implements no domain logic, alters no voting cryptography, selects
no hosting provider and closes no INFRA/OPS/CTRL/SEC stage.

---

## 1. What was built

### 1.1 One canonical acceptance entry point (§4)

`uv run python -m scripts.acceptance run` (also exposed as `make acceptance`)
is the single canonical acceptance command. It executes the governed stage
sequence — bootstrap, verify-governance, verify-repository,
verify-dependencies, verify-backend, verify-frontend, verify-build,
verify-browser, verify-accessibility, verify-visual, verify-secrets,
verify-frozen-artifacts, verify-boundaries, verify-evidence, freeze, package,
verify-package, emit-manifest — and emits a sealed canonical execution
manifest plus an evidence bundle. There is no competing "canonical"
acceptance command: `make verify` remains the quick sequential developer
pipeline and is documented as not being an acceptance run, and the existing
stage-specific acceptance workflows (api01-accept, pilot04-c9-accept,
front02-governed-review, consolidation-c1-accept) remain what they were —
sealed-candidate verification for _their_ stages, not the repository
acceptance path.

### 1.2 Machine-readable check registry (INFRA01-HI-03)

`scripts/acceptance/check_registry.json` declares every governed check with
stage, kind (command/internal), mandatory flag, timeout and an explicit
execution expectation. `scripts/acceptance/registry.py` validates registry
integrity (duplicate ids, empty stages, malformed expectations fail closed
with `REGISTRY_INTEGRITY_FAILURE`). The execution manifest must account for
every registry entry with `PASS`, `FAIL`, `BLOCKED` or
`NOT_APPLICABLE_GOVERNED`; a mandatory check with no recorded result is
`MANDATORY_CHECK_MISSING` in the evidence validator. Every harness file is
additionally pinned in `scripts/check_repository.py`'s required-path
registry, so no part of the acceptance system can silently disappear from a
candidate. The schema for the registry file itself is
`scripts/acceptance/schemas/check_registry.schema.json` and is asserted by
`tests/repository/test_infra01_harness_units.py`.

### 1.3 Exact candidate identity binding (INFRA01-HI-01)

`scripts/acceptance/identity.py` binds every run to: Git commit SHA, Git tree
SHA, dirty-state with the exact diverging paths, repository version
(`0.16.0`) and canon version (`0.8.0`) from the governed version sources,
dependency-lock SHA-256 digests (`uv.lock`, `package-lock.json`), platform
and Python version, GitHub workflow/run identity where present, harness
name/version, and the candidate archive SHA-256 once packaging has produced
it. Identity capture fails closed: an undeterminable value is recorded as an
explicit problem (`IDENTITY_INCOMPLETE`) and the evidence validator rejects
manifests whose identity block is incomplete — acceptance evidence without
exact candidate identity is invalid.

### 1.4 Tested bytes == packaged bytes (INFRA01-HI-02)

`scripts/acceptance/freeze.py` derives the freeze inventory from Git's
tracked-file list, hashing every file (SHA-256) and computing a recomputable
tree digest (`sha256` over `path \0 sha256 \n` in sorted order — the same
convention prior governed rounds used). Freezing fails closed on any dirty
tracked file and on any untracked file outside recognized generated
locations. `scripts/acceptance/package.py` writes exactly the frozen bytes
plus the governed additions (`SHA256SUMS.txt`,
`ACCEPTANCE/FREEZE-INVENTORY.json` — the single canonical allowlist
`packaging_allowlist.json`), verifying each staged member against the freeze
digest as it is written (a mismatch refuses packaging and deletes the partial
archive), then `verify_archive_against_inventory` independently re-proves
byte equality from the archive side: every member is either a frozen file
with identical bytes or a governed addition; every frozen file is present;
anything else is `UNDECLARED_ARCHIVE_ENTRY` / `MISSING_ARCHIVE_ENTRY` /
`ARCHIVE_BYTE_MISMATCH`.

### 1.5 No fake PASS (INFRA01-HI-04)

`scripts/acceptance/executor.py` distinguishes executed-and-passed from
did-not-execute from evidence-says-PASS: a missing tool is `BLOCKED` (never a
skip), exit 0 without the registry's required output sentinel is `FAIL`
(`EXPECTED_OUTPUT_MISSING`), zero executed tests where tests are expected is
`FAIL` (`ZERO_TESTS_EXECUTED`), and failure markers in output override a
green exit code. Test counts are parsed from captured output (pytest, vitest,
node:test, playwright) after ANSI stripping, with per-check minimums from the
registry. `scripts/acceptance/evidence.py` then re-reconciles the sealed
manifest against the actual logs: log bytes re-hashed, counts re-parsed from
the log, sentinels re-checked, registry accounted check-by-check, commit and
archive identity re-bound. Self-declared result files are never trusted.

### 1.6 Adversarially tested validator (INFRA01-HI-05, §9)

`tests/repository/test_infra01_mutation_suite.py` corrupts representative
acceptance inputs across all sixteen governed mutation classes (M01–M16:
removed evidence, foreign PASS log, frozen-artifact byte flip, forbidden
cache directory, source change after testing, source change inside the ZIP
only, faked test count, suppressed mandatory command, exit 0 with missing
output, injected secret, repository/canon version mismatch, lock-hash
mismatch, manifest edited after sealing, undeclared archive entry, duplicate
archive path, second canonical register). Every mutation asserts the exact
detector code that catches it, and a closing test proves the sixteen classes
map onto sixteen _distinct_ detector codes — no shared poison marker can
inflate coverage. `tests/repository/test_infra01_harness_units.py` covers the
building blocks (canonical sealing, registry integrity, executor fail-closed
semantics, hygiene and secret detectors, frozen pins, deployment-manifest
validation, readiness evaluation, schema conformance of the emitted
manifest).

### 1.7 Freeze/package hygiene (INFRA01-HI-06)

`scripts/acceptance/hygiene.py` rejects development debris (`node_modules`,
`.venv`, `__pycache__`, `.pytest_cache`, Ruff/mypy caches, build caches, IDE
metadata, temporary files), nested repository copies, nested candidate
archives, duplicate archive members (byte-exact and case-insensitive),
absolute/traversal/backslash member paths and machine-local path fragments.
The only exceptions come from the one canonical governed allowlist
`scripts/acceptance/packaging_allowlist.json`.

### 1.8 Frozen/reference evidence integrity (INFRA01-HI-07)

`scripts/acceptance/frozen_artifacts.json` pins the seven governed frozen
artifacts (the five PACK-16D artifacts — test vectors, conformance evidence,
target-profile fixtures, target-profile timings, `EPD2-CRYPTO-1.json` — plus
the two TESTONLY parameter files) to their exact accepted SHA-256 at the
entering baseline commit. The harness verifies them at the five governed
lifecycle boundaries: before testing, after testing, before packaging,
during packaging (staged bytes) and against the bytes inside the produced
archive. A one-byte mutation causes packaging refusal
(`FROZEN_ARTIFACT_MISMATCH`, proven by mutation M03).

This round also carries the PACK-25C6-equivalent correction forward onto this
source lineage: `test_target_conformance.py` previously used the two frozen
target-profile artifacts as writable test outputs; generated fixtures and
timings now go only to an isolated temporary output location
(`EPD2_TARGET_CONFORMANCE_OUTPUT_DIR` or a per-session temp directory), the
frozen copies are immutable inputs, and a dedicated test proves the output
destinations resolve outside the frozen vectors directory and that the frozen
bytes still match their governed pins.

### 1.9 Secret-leakage hard gate (INFRA01-HI-08, FIR-SEC-SECRET-001 foundation)

`scripts/acceptance/secrets_scan.py` implements deterministic pattern-based
scanning of (1) the current tracked tree, (2) staged/generated material, (3)
the final archive bytes and (4) persisted CI evidence before bundling
(sanitation detectors for authorization headers, cookies and embedded
credentials). The governed allowlist
(`scripts/acceptance/secret_allowlist.json`) permits exactly one detector
match per exact line (line-SHA-256-pinned) per file, each classified as
synthetic test material or intentionally public reference material with an
evidence-backed reason; there is no inline bypass and no path- or
pattern-wide exemption, and a unit test fails when an allowlist entry goes
stale. Public PACK-16D reference cryptographic material is verified not to
trip the gate (a public key or governed test vector is not a secret merely
because it is cryptographic). The scanner design deliberately takes content
as input so the same detector set can later be pointed at every publishable
Git ref for the full public-release criteria of `FIR-SEC-SECRET-001`. An
unlisted match is a hard `SECRET_DETECTED` FAIL in tree, staging and archive
scans (proven by mutation M10). Developer pre-commit scanning
(`detect-secrets` in `.pre-commit-config.yaml`) remains as defence-in-depth
and is not the authoritative control.

### 1.10 Deployment/release identity foundation (INFRA01-HI-09, FIR-REL-001)

`scripts/acceptance/schemas/deployment_manifest.schema.json` plus
`scripts/acceptance/deployment_manifest.py` establish the machine-readable
integrated deployment manifest: per-component artifact digest, source
revision, dependency-lock digest, contract versions, configuration version
and migration set, plus approval state. The enforced invariant is `running
combination == one approved deployment manifest`, explicitly not `all
services identical version`: heterogeneous source revisions are valid only
under `mixed-by-declared-matrix` mode with a compatibility-matrix entry
covering the exact running combination; absent compatibility evidence the
combination is not deployable (`COMPATIBILITY_NOT_DECLARED`, fail closed). A
validated example instance ships at
`docs/infra/INFRA-01/examples/deployment-manifest.example.json`. CLI:
`uv run python -m scripts.acceptance validate-deployment-manifest <file>`.

### 1.11 Runtime readiness contract foundation (INFRA01-HI-10, FIR-READY-001)

`scripts/acceptance/schemas/readiness_contract.schema.json` plus
`scripts/acceptance/readiness.py` establish the canonical readiness
mechanism: ten mandatory dimensions (process_alive,
deployment_manifest_identity, configuration_compatibility,
schema_compatibility, key_trust_anchor_readiness, dependency_readiness,
projection_freshness with watermark/required-position comparison,
trusted_time, migration_state, restore_reconciliation_state) with fail-closed
semantics — `process alive != runtime safe for consequential traffic`,
`UNKNOWN` fails closed, `NOT_APPLICABLE_GOVERNED` requires a governed rule
reference, a stale projection watermark is `NOT_READY`, and a declared
overall that contradicts evaluation is rejected. INFRA-01 establishes the
mechanism; wiring live services is later INFRA/OPS work. CLI:
`uv run python -m scripts.acceptance evaluate-readiness <file>`.

### 1.12 Ingress/gateway non-ownership (INFRA01-HI-11, FIR-EDGE-001/FIR-API-001)

`scripts/acceptance/boundaries.py` enforces two structural rules as a
mandatory stage: infrastructure Python code (`scripts/`, including the
harness itself) must not import any domain service implementation module
(all 21 `epd2_*_service` prefixes; running domain test suites as
subprocesses is execution, not ownership), and GitHub workflow definitions
must not embed domain-decision markers. Violations are
`DOMAIN_LOGIC_IN_INFRASTRUCTURE`. CI/ingress/gateway/BFF infrastructure
routes and enforces technical policy; it owns no domain truth, no business
decisions, no domain authorization semantics, no voting semantics, no
publication decisions and no legal-effect decisions.

### 1.13 Sovereign-infrastructure profile readiness (INFRA01-HI-12, FIR-INFRA-SOV-001)

The deployment manifest requires a complete machine-readable
`sovereignty_profile` — region, jurisdiction, tenancy/isolation class,
data-residency policy, operator-access model, key-custody model, provider
role, backup location and explicit trust assumptions. `UNDECIDED` must be
declared explicitly rather than omitted (unknown critical infrastructure
state fails closed). No commercial hosting provider is chosen; provider
choice != trust assumption is embedded in the schema semantics and the
example instance.

### 1.14 GitHub Actions (§10)

`.github/workflows/infra01-acceptance.yml` invokes the exact canonical
repository harness (`uv run --frozen python -m scripts.acceptance run`) and
uploads the governed evidence bundle and the produced candidate artifact. It
implements no second version of acceptance logic. The pre-existing `ci.yml`
remains unchanged as the fast PR gate; it was not weakened.

### 1.15 Environment reproducibility (§6)

The canonical path installs with `uv sync --all-groups --frozen` and
`npm ci` as mandatory registry checks, records both lock digests in the
identity block at bootstrap, and re-verifies them after installation
(`LOCK_HASH_MISMATCH` on divergence, mutation M12). A run using unrelated
globally installed tools cannot be represented as canonical: tool inventory
is recorded in the manifest, and the frozen installs themselves are mandatory
registry checks that fail closed.

---

## 2. Wired governed checks

Backend (§7): repository structure (983+ required paths), forbidden paths,
version consistency, canon 0.8.0 amendment checks (now wired directly into
the acceptance path as a mandatory command; previously reachable only
through a repository test), PILOT roadmap-lock self-check, Ruff format,
Ruff lint, collision-safe repository-wide mypy groups (`make typecheck`),
full pytest (all 21 service suites + contract + repository suites, including
the PACK-16D reference suites and the independent Node.js verifier oracle),
plus an explicit re-execution of the adversarial/security reference modules
(negative corpus, fault injection, verifier branches, invariants) as a
separate mandatory check with its own executed-test evidence.

Frontend (§8): frozen dependency installation (`npm ci`), Prettier
format-check (lock-pinned version), TypeScript typecheck (epd2-types and
web-shell), ESLint, epd2-types unit tests (node:test), web-shell unit/render
tests (node:test + vitest), production `next build` (sentinel-gated),
Playwright browser suite, `@a11y` accessibility gates and `@visual`
regression gates — each with zero-test detection. A frontend result cannot
become PASS through absent Node dependencies: the installs are mandatory
checks and every suite requires positive executed-test evidence.

## 3. Baseline defects found and fixed forward

The entering baseline itself was red on two verification commands (verified
by running them on the untouched checkout):

1. `uv run ruff check .` — two pre-existing `RUF100` errors in
   `scripts/check_pilot_roadmap.py` (unused `noqa` directives).
2. `make typecheck` — ten pre-existing mypy errors in
   `scripts/check_pilot_roadmap.py` (untyped `dict` returns, `fail()` not
   marked `NoReturn`) and
   `tests/repository/test_pack16d_signature_dependency.py` (an untyped TOML
   return).

3. `npm run format:check` — the locked Prettier (3.9.6, from
   `package-lock.json`) reported 145 files as unformatted, mostly Markdown
   table alignment in `docs/packs/PACK-16/`, ADRs, governance documents,
   `CHANGELOG.md` and five workflow files. This candidate carries the
   mechanical Prettier normalization for those files (content-identical
   reflow by the repository's own locked formatter). Four
   normative/evidence artifacts were deliberately **not** reformatted and
   are now listed in `.prettierignore` with rationale, because their exact
   accepted bytes are the point: the two cryptographic key-classes profile
   files (`docs/governance/EPD2_CRYPTOGRAPHIC_KEY_CLASSES_ALGORITHM_PROFILE_0.1.{md,json}`),
   the V25 Master reconciliation evidence
   (`docs/roadmap/EPD2_MASTER_V25_RECONCILIATION.json`) and the independent
   verifier oracle
   (`services/voting-service/tests/reference/crossimpl/independent_verifier.mjs`).
   No acceptance evidence under `docs/handover/` needed any change.
4. `test_property_limitation_is_recorded` asserted that `hypothesis` is
   _not_ importable — an environment fact of the round it was written in,
   false in any healthy frozen environment. Rewritten to pass in both the
   blocked and the resolved state, per the PACK-16D lockfile-round rule.

All fixes are typing/lint/formatting-only with no behavioural change, and no
check was weakened. Additionally, the
default pytest run mutated the two frozen PACK-16D target-profile artifacts
(the PACK-25C6 class of defect, absent on this source lineage) — corrected as
described in §1.8.

## 4. Execution results

The complete canonical harness was executed on the exact candidate commit
before handoff. The full stage/result matrix with executed test counts is in
`INFRA-01-ACCEPTANCE-MATRIX.md`; the machine-readable proof is the sealed
`EXECUTION-MANIFEST.json` in the delivered evidence bundle, which also
carries the freeze tree digest and final archive SHA-256. Exact candidate
and evidence identities are recorded in the delivery note and evidence
bundle rather than inside this report, because a candidate cannot contain
its own archive hash.

## 5. Scope exclusions honoured (§13)

No domain business logic, no API service redesign, no FRONT workspace
redesign, no voting-cryptography change (the HI-07 correction touches only
test output _destinations_), no production-deployment claim, no legal
activation, no infrastructure-provider choice, no OPS/CTRL/SEC closure, no
rewriting of historical acceptance evidence, no weakening of existing
checks. INFRA-01 remains `PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED`; INFRA
closure is not proposed and remains blocked on the governed predecessor
sequence (API layer completion per the Program Control Register).

---

## 6. C1 correction round — governance freshness (2026-09-01)

The independent review of the C0 candidate (`3bb42509…3210`) returned
`REJECTED / CORRECTION REQUIRED` with two findings; both are corrected in
this candidate.

**INFRA01-C1-01 — stale current execution state.** The C0 candidate's
Program Control Register (`Updated: 2026-08-30`) still interpreted
`API-02 = ACTIVE / IN DEVELOPMENT` after the target `main` had advanced
(`556821e0e5d550a4db601bbe92e4f4673a1bc3ff`, "gov(api02): close C13 and
advance primary API stage"). C1 reconciles the candidate to that target
authority as base: the register now carries `API-01 = ACCEPTED / CLOSED`,
`API-02 = ACCEPTED / CLOSED` with the exact C13 identity and authoritative
evidence (candidate SHA `9363561271…dfc6a9`, run `33497989489`, artifact
`ac5f940b…1857`, decision record `docs/api/API-02/API02_C13_ACCEPTANCE_RECORD.json`
carried into the candidate), `API-03 = ACTIVE / IN DEVELOPMENT / NOT
ACCEPTED`, and `INFRA-01 = PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED`.
Historical statements remain preserved as history. No API-02/API-03 runtime
code was imported: reconciliation is governance-only, per the correction
scope and §8 of the C1 assignment.

**INFRA01-C1-02 — the harness did not detect stale governance.** The
reviewer proved `verify_governance()` returned `finding_count = 0` on a
candidate whose current API-02 state was stale-mutated. C1 adds a
fail-closed governance-freshness mechanism distinguishing `canonical files
exist != unique != current`: a sealed machine-readable reconciliation
record (`docs/infra/INFRA-01/INFRA01_GOVERNANCE_RECONCILIATION.json`)
binding target repository/branch/commit/tree and the exact canonical-file
identities used at seal, the exact reconciled candidate-register bytes, and
region-anchored expected current-state facts. The new mandatory registry
check `governance.freshness-reconciliation` (registry 1.1.0) validates the
record's integrity, the register's byte binding, and every fact against the
register's _current-state regions only_ (primary position, program-layer
table, immediate execution decision), so preserved audit history is never
judged as current state. Dedicated detectors: `RECONCILIATION_RECORD_MISSING`,
`RECONCILIATION_INTEGRITY_FAILURE`, `GOVERNANCE_RECONCILIATION_MISMATCH`,
`STALE_GOVERNANCE_STATE`, `GOVERNANCE_TRANSITION_MISSING`,
`GOVERNANCE_REGION_MISSING`, `TARGET_AUTHORITY_MISMATCH`. A stale register
cannot be made self-valid by rehashing it into the record: hash-rebinding
attacks are caught semantically by the recorded facts (mutation M17), and
rewriting the facts/authority themselves changes exactly the fields the
authoritative path compares against the reviewer-fetched current target
(`verify-reconciliation --target-pcr`, wired as a mandatory workflow step).
The reviewer's exact reproduction now fails closed with
`GOVERNANCE_RECONCILIATION_MISMATCH` + `GOVERNANCE_TRANSITION_MISSING`
(`finding_count = 2`, previously `0`).

**New adversarial coverage.** M17 (stale current-state regression, rehashed
record) → `STALE_GOVERNANCE_STATE`; M18 (target-authority identity edited
without reseal) → `RECONCILIATION_INTEGRITY_FAILURE`, plus the
authoritative-side variant → `TARGET_AUTHORITY_MISMATCH`; M19 (candidate
lacks a newer target transition while all canonical files exist exactly
once and versions are consistent) → `GOVERNANCE_TRANSITION_MISSING`; M20
(preserved historical `API-02 = ACTIVE` text with correct current state)
passes. The 19 negative classes map onto 19 distinct detector codes; the
47-test regression floor of the two harness test files is preserved and
extended, not diluted.

**Exact change accounting.** The complete machine-readable C0→C1 path delta
is `docs/infra/INFRA-01/INFRA01_C0_TO_C1_EXACT_INVENTORY.json` (no
exclusions: workflows, harness code, tests, governance docs, evidence and
checksum metadata all accounted). The concise correction report is
`docs/infra/INFRA-01/INFRA-01-C1-CORRECTION-REPORT.md`.
