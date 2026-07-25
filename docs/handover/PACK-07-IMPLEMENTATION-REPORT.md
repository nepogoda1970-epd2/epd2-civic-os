# CLAUDE-PACK-07 — Participation & Membership Context: Implementation Handover Report

Status: **PASS — externally verified.** This round's implementation was
verified by an external GitHub Actions run with real network access,
confirming the full stack — including the TypeScript, Prettier, ESLint,
and Next.js production-build checks that this sandbox's no-network
limitation could not perform locally. Section 6 records both the local
verification performed in this sandbox during implementation and the exact
external GitHub Actions results that closed this round out.

This report covers the **implementation round** that follows
`docs/handover/PACK-07-CANON-AMENDMENT-REPORT.md` (the canon-only round that
accepted ADR-026 through ADR-031 and raised `CANON_VERSION` to `0.6.0`, with
`REPOSITORY_VERSION` deliberately left at `0.6.0` at the time, since no
service code existed yet). This round implements the accepted canon 19d
text against real service code and raises `REPOSITORY_VERSION` to `0.7.0`.
`CANON_VERSION` is unchanged.

## 0. What this round adds

- A new, independent, in-memory-backed service, **`membership-service`**
  (`PartyMembershipEligibilityPolicy`, `Membership` — canon 8.3's first
  real implementation, `MembershipApplication`, `AffiliationDeclaration`,
  `ConflictAssessment`, a documented-duplicate `Appeal`).
- In-place extensions to two pre-existing PACK-02 services:
  - **`eligibility-service`**: `ParticipantEligibilityPolicy`,
    `ProcessEligibilityPolicy`, `StepUpAuthenticationRequirement`,
    `DigitalDecision`, `AssemblyDecision`, the four separated
    electoral-eligibility claims, atomic capability checks, and scoped
    capability-token issuance.
  - **`identity-service`**: `AuthenticationContext`, canon 19d.2's eight
    additive `IdentityRecord` fields, and the two narrow ADR-027
    cross-pack reads other services call directly.
- The full 22-point scope from the governing request: process-specific
  eligibility with four separated claims, a dedicated membership
  lifecycle with a hard human-control invariant, restricted-by-default
  membership disclosure, immutable versioned affiliation declarations,
  structured conflict assessment, appeal reuse, step-up authentication
  contracts, a narrow identity boundary, the legal-effect/formal-
  confirmation vocabulary and lifecycle, governance safety for critical
  policies, the full PACK-07 reason-code set, thirteen new/reused canon
  events, cross-language contract parity via JSON Schema + OpenAPI, an
  honest CT-00 mapping, and the version bump — all covered below.

## 1. Environment and network status

Same sandbox, same limitation as every prior pack (see
`LOCAL_VERIFICATION.md`): no live PyPI/npm registry access. Verification
used the established workaround — standalone `pytest`/`mypy`/`ruff`
binaries at `/root/.local/bin/` (isolated `uv`-tool installs with no
project dependencies), with `PYTHONPATH` pointed at every service's `src/`
and every Python package's `src/`. This round refined that workaround
further: appending the system Python's own `dist-packages` directory
(where PyYAML is already installed) to `PYTHONPATH` lets the standalone
`pytest` binary import `yaml` — unblocking `tests/contract/test_reason_codes_registry.py`
and `tests/contract/test_openapi_contract.py`, both of which used to skip
unconditionally in this sandbox. `hypothesis` remains unavailable this way
(not present in that `dist-packages` directory either), so
`test_property_based.py` still skips, unchanged from every prior pack.

`node`, `npm`, and a global `tsx` binary are present, but the TypeScript
workspace's own `node_modules` are not installed (`npm install --offline`
fails with `ENOTCACHED` — no cached registry response, confirming this is
the same no-network ceiling, not a new one). TypeScript unit tests,
Prettier, ESLint, and the Next.js frontend build could therefore not be run
in this sandbox during implementation. This gap is now closed: the
external GitHub Actions run (real network access, dependencies installed
for real) executed and passed all of them — see section 6a.

## 2. Canon integrity

No canon edit was made this round. `docs/canonical/TZ-00-domain-event-canon.md`
is untouched; `CANON_VERSION` stays `0.6.0` in every source
(`packages/python/epd2-core/src/epd2_core/version.py`,
`packages/typescript/epd2-types/src/version.ts`,
`docs/canonical/canon-version.json`). This is purely an implementation
round against the already-accepted text.

## 3. Architectural decisions confirmed or corrected during this round

- **`packages/typescript/epd2-types` gains no PACK-07 domain types.** The
  inherited task list for this round included "TypeScript canonical
  models" as a deliverable. On inspection, this package's own
  `package.json` description ("shared TypeScript infrastructure package,
  no domain types"), `docs/development/local-development.md`, and
  `docs/development/new-module-guide.md` all state, consistently across
  PACK-01 through PACK-06, that this package holds only version constants
  — never business/domain types, for any pack, including packs (PACK-03,
  PACK-05, PACK-06) that introduced many new canonical entities of their
  own. No prior pack ever added a TypeScript mirror of its domain model
  here. Cross-language contract parity for this project has always been
  carried by JSON Schema + OpenAPI (language-neutral, validated in every
  language that needs to consume it), not hand-written per-language model
  mirrors. Introducing PACK-07-only domain types into this package would
  have been a one-off architectural deviation, not a continuation of
  established practice. This round therefore does not add them; parity is
  carried entirely by the ten new entity JSON Schemas and twelve new
  event-payload JSON Schemas (section 5).
- **`CriticalPolicyVersionFrozenError` (canon 19d.7) is declared but
  deliberately left unraised.** Both `eligibility-service` and
  `membership-service` declare this exception (mirroring the
  already-accepted canon text's "an active critical-policy version
  already in use by an active process should not be superseded" rule),
  but neither service raises it anywhere. Enforcing it correctly requires
  knowing whether an active process is currently relying on a given
  policy version — which needs a persisted Process/Election
  lifecycle-tracking aggregate. No such aggregate exists anywhere in this
  repository through PACK-07 (it is not part of this round's 22-point
  scope, and the "full Regional Organization model" is explicitly
  deferred by that scope too). Raising this exception now, against no
  real "is a process using this version" signal, would create a false
  sense of enforced safety rather than real safety. This is reported
  honestly (both exception classes' own docstrings explain it, and
  `tests/contract/test_ct00_10_rule_freeze.py`'s new PACK-07 section
  documents it as part of an explicit CT-00-10 not-applicable mapping)
  rather than silently glossed over, per required scope item 18's
  no-false-applicability-claims requirement. A future pack that
  introduces real process-lifecycle tracking is the correct place to wire
  this up for real.

## 4. Files added or changed this round

**New service** (`services/membership-service/`): `README.md`,
`pyproject.toml`, `src/epd2_membership_service/{__init__,domain,
application,events,exceptions,storage}.py`, `tests/{test_domain,
test_application,test_storage}.py` (25 + 26 + 10 = 61 tests).

**Extended services**: `services/eligibility-service/src/epd2_eligibility_service/{domain,
application,events,exceptions,storage}.py` (PACK-07 additions layered
alongside PACK-02's existing code, never replacing it) and
`services/eligibility-service/tests/test_application_pack07.py` (22
tests); `services/identity-service/src/epd2_identity_service/{domain,
application,events}.py` (PACK-07 additions) and
`services/identity-service/tests/test_application_pack07.py` (7 tests).

**Contracts**: `contracts/reason-codes/pack-07.yml` (38 entries);
`contracts/schemas/{participant-eligibility-policy,process-eligibility-policy,
step-up-authentication-requirement,digital-decision,assembly-decision,
party-membership-eligibility-policy,membership,membership-application,
affiliation-declaration,conflict-assessment}.schema.json` (10 new entity
schemas); `contracts/schemas/identity-record.schema.json` (updated, canon
19d.2's eight additive fields added to `required`/`properties`);
`contracts/events/{participation-rights-derived,formal-confirmation-requested,
formal-confirmation-recorded,authentication-context-event,
membership-application-submitted,membership-eligibility-evaluated,
membership-decision-recorded,membership-activated,membership-suspended,
affiliation-declared,conflict-assessment-opened,
conflict-decision-recorded}-payload.v1.schema.json` (12 new event-payload
schemas); `contracts/openapi/pack-07.yaml` (new, ~25 operations across
both services, tags `eligibility-service`/`membership-service`).

**Cross-service tests**: `tests/repository/test_service_boundaries.py`
(extended: PACK-07 edge-matrix enforcement, 3 new tests, plus 2 existing
tests' exception sets widened for eligibility-service's new legitimate
edges); `tests/repository/test_pack07_duplicated_logic_parity.py` (new, 8
tests — proves the three deliberately-duplicated logic pieces stay
byte-for-byte equivalent across their service copies); `tests/contract/
test_ct00_01_pack07_schema_validation.py` (new, 22 tests — every new
entity and event-payload schema against a real, directly-constructed
domain instance); `tests/contract/test_ct00_0{2,3,4,5,6,7,8,9}` (each
extended with a PACK-07 section); `tests/contract/test_ct00_10_rule_freeze.py`
and `test_ct00_12_emergency_stop_not_applicable.py` (each extended with a
documented PACK-07 not-applicable section, see section 3); `tests/contract/_schema_helpers.py`
and `test_reason_codes_registry.py` and `test_openapi_contract.py`
(extended for the new PACK-07 registry/spec files).

**Repository infrastructure**: `scripts/check_repository.py`
(`REQUIRED_PATHS` extended with every file above — 402 required paths
total, up from the PACK-06 baseline); `packages/python/epd2-core/src/epd2_core/version.py`,
`packages/typescript/epd2-types/src/version.ts`, both version-consistency
unit tests, `docs/canonical/canon-version.json` (`repository_compatibility`
upper bound widened `<0.7.0 → <0.8.0`); `CHANGELOG.md` (new `[0.7.0]`
entry); this report.

## 5. Contract parity (schemas, OpenAPI, reason codes)

Ten new entity JSON Schemas and twelve new event-payload JSON Schemas
(the thirteenth named event, `EligibilityEvaluated`, reuses PACK-02's own
existing `eligibility-evaluated-payload.v1.schema.json` unchanged — no
new schema was needed for it). Every one is validated in
`test_ct00_01_pack07_schema_validation.py` against a real,
directly-constructed domain instance (not a hand-typed fixture dict) —
either via each service's own `*_state_payload`/`build_*_event` function
where one exists, or via a manually-assembled instance dict that mirrors
the dataclass's exact field set where no such helper exists (four
critical-policy entities whose realistic construction would otherwise
require a full governance approval flow out of scope for a schema-shape
test).

`contracts/reason-codes/pack-07.yml` has exactly 38 entries: canon
19d.15's eight electoral-eligibility/membership-human-control codes named
explicitly by required scope item 15
(`ACTIVE_ELECTORAL_ELIGIBILITY_NOT_MET`,
`PASSIVE_ELECTORAL_ELIGIBILITY_NOT_MET`,
`PARTY_INTERNAL_VOTING_ELIGIBILITY_NOT_MET`,
`PARTY_OFFICE_CANDIDACY_ELIGIBILITY_NOT_MET`,
`MEMBERSHIP_HUMAN_APPROVAL_REQUIRED`,
`MEMBERSHIP_DECISION_AUTHORITY_INVALID`,
`MEMBERSHIP_STATUS_DISCLOSURE_PROHIBITED`,
`MEMBERSHIP_PUBLICATION_CONSENT_MISSING`), critical-policy
activation/identity-layer/step-up/atomic-capability/formal-confirmation
codes, membership-service's own additive codes, and five PACK-02 generic
codes independently redeclared for membership-service's self-contained
registry scan (this repository's established per-pack precedent). Since
PACK-07 is the first pack to extend pre-existing PACK-02 service
directories in place (rather than introduce only new ones), the
literal-usage scan for `pack-02.yml` is unioned with `pack-07.yml` for
`eligibility-service`/`identity-service`'s own scan only — the other
three registry-validity checks still validate each file independently,
unchanged.

`contracts/openapi/pack-07.yaml` documents every real public
command/read function in `epd2_eligibility_service.application`'s PACK-07
additions and the whole of `epd2_membership_service.application`,
transport-neutral (no production HTTP server ships in this pack). Per
ADR-027, the four narrow internal cross-pack reads
(`get_identity_participation_claims`,
`check_authentication_step_up_satisfied`, `get_membership_derived_claims`,
`read_participant_eligibility_decision`) have no HTTP-shaped path at all
— mirroring `pack-06.yaml`'s own precedent for
`verify_role_assignment_for_action`.

## 6. Verification performed this round

### 6a. External GitHub Actions verification — PASS

An external GitHub Actions run, with real network access and real
dependency installation (`uv.lock`/`package-lock.json` resolved for real,
not the local standalone-binary workaround below), verified this round's
implementation end to end. Exact reported results:

- **Status: PASS**
- All 402 required paths present.
- No forbidden paths.
- Version consistency check passed.
- Ruff formatting: 359 files already formatted.
- Ruff lint: passed.
- Prettier: passed.
- ESLint: passed.
- mypy: passed for all services.
- Python: **2028 passed, 4 skipped, 0 failed**.
- TypeScript: **3/3 passed**.
- Frontend: **2/2 passed**.
- Next.js 15.5.21 production build: passed.

The external Python figures (2028 passed / 4 skipped) differ slightly from
the local sandbox run recorded in section 6b (2020 passed / 5 skipped)
because the external environment has real network access: it installs
`hypothesis` for real (so `test_property_based.py` runs instead of
skipping) and starts from a clean checkout with no leftover
`__pycache__`/tool-cache directories from an active local verification
session (so `test_no_forbidden_paths_present` passes outright rather than
via the "clean immediately before archiving" workaround this sandbox
relied on). Both figures describe the same implementation; neither
contradicts the other.

This is now a **genuine external GitHub Actions PASS** for the PACK-07
implementation round — not a local self-report.

### 6b. Local verification performed during implementation

Commands (from repository root):

```bash
export PYTHONPATH=$(python3 -c "
import glob
paths = glob.glob('services/*/src') + glob.glob('packages/python/*/src')
print(':'.join(paths))
"):/usr/local/lib/python3.11/dist-packages

/root/.local/bin/ruff check .
/root/.local/bin/ruff format --check .
/root/.local/bin/mypy packages/python/epd2-core scripts tests/repository conftest.py
/root/.local/bin/mypy tests/contract
/root/.local/bin/mypy services/<each-service>          # one invocation per service
/root/.local/bin/pytest packages/python/epd2-core tests/repository -q
/root/.local/bin/pytest tests/contract -q
/root/.local/bin/pytest services -q
python3 scripts/check_repository.py
python3 scripts/verify_versions.py
```

Results:

- **Ruff (lint):** clean, whole repository.
- **Ruff (format):** clean, whole repository (186 files).
- **mypy:** `Success: no issues found` for every group — core/scripts/
  repository-tests (25 files), `tests/contract` (20 files), and every one
  of the seventeen services individually (mypy is invoked once per
  service, never as a single repo-wide pass, because multiple services
  deliberately share identically-named test files with no `__init__.py`
  — a pre-existing, documented `Makefile` limitation, unrelated to this
  round).
- **Python tests:** `packages/python/epd2-core` + `tests/repository`: 94
  passed, 1 expected failure (`test_no_forbidden_paths_present` — caches
  present from this session's own verification runs; resolved by cleaning
  before packaging, see section 7). `tests/contract`: 915 passed, 5
  skipped (`test_property_based.py`'s `hypothesis`-unavailable skip,
  unchanged from every prior pack; two CT-00-10 not-applicable markers —
  PACK-06's pre-existing one and this round's new PACK-07 one; two
  CT-00-11/CT-00-12 not-applicable markers, both now covering PACK-07
  too). `services/*`: 1011 passed. **Total: 2020 passed, 5 skipped, 0
  failed** (the one cache-related failure above is expected and resolved
  before archiving).
- **`scripts/check_repository.py`:** all 402 required paths present, no
  forbidden files reported by the script itself (its own check is
  narrower than the pytest cache-directory check above).
- **`scripts/verify_versions.py`:** all version sources consistent
  (`CANON_VERSION 0.6.0` / `REPOSITORY_VERSION 0.7.0` everywhere they are
  declared).
- **TypeScript unit tests, Prettier, ESLint, Next.js build:** **not run**
  in this sandbox — `npm install --offline` fails with `ENOTCACHED` (no
  cached registry response), the same no-network ceiling documented for
  every prior pack. Not claimed as passing from this local run alone.

This local run was, at the time, an honest self-report rather than an
external GitHub Actions PASS. It has since been superseded by the genuine
external GitHub Actions PASS recorded in section 6a, which covers exactly
the TypeScript/Prettier/ESLint/Next.js-build ground this sandbox could not
reach.

## 7. Before archiving

Python bytecode/tool caches (`__pycache__/`, `.mypy_cache/`,
`.pytest_cache/`, `.ruff_cache/`, `.venv/`) accumulate during local
verification and are cleaned before the delivery archive is built, so
`tests/repository/test_forbidden_paths.py::test_no_forbidden_paths_present`
passes in the delivered archive exactly as it does mid-session once those
directories don't exist yet.

## 8. Deliverables

- `docs/handover/PACK-07-IMPLEMENTATION-REPORT.md` (this file, updated for
  closeout to record the genuine external PASS).
- `README.md`, `CHANGELOG.md` (updated for closeout).
- `epd2-civic-os-PACK-07-IMPLEMENTATION-0.7.0-PASS.zip` — one complete,
  clean archive (excludes `.git/`, `node_modules/`, `.venv/`,
  `__pycache__/`, `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`,
  frontend build output, verification-result ZIPs, nested ZIPs, and
  temporary logs/machine-specific artifacts) reflecting the
  externally-verified PACK-07 implementation at `REPOSITORY_VERSION
  0.7.0` / `CANON_VERSION 0.6.0`.
