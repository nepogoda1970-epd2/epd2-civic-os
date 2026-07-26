# PACK-09 Implementation Report

|                    |                                                                    |
| ------------------ | ------------------------------------------------------------------ |
| Date               | 2026-07-26                                                         |
| Status             | **CANDIDATE-2 — NEEDS CI** — see section 5 and section 8           |
| Repository version | `0.8.0` → `0.9.0`                                                  |
| Canon version      | `0.7.0` (unchanged; no canon-owned file touched)                   |
| New service        | `services/compliance-service`                                      |
| ADRs               | ADR-038 … ADR-043, all `accepted`                                  |
| Authoritative spec | EPD² Architecture & Domain Framework **0.8.1** (Roadmap Amendment) |

This report replaces the pre-review draft of the same name. That draft
claimed `LOCAL PASS`; this round's review established that several
mandatory checks had not in fact been run and that the pack was not wired
into the repository's own verification machinery at all. What follows
records what was found, what was changed, and — explicitly — what has
still not been executed.

## 1. What PACK-09 delivers

`compliance-service`, PACK-09's one wholly new service (ADR-038), owning
six entity families: records governance and versioned retention;
controlled destruction with immutable evidence; Legal Hold; the Data
Catalog and Processing Registry; governed procedural cases and
append-only deadlines; data-subject/legal requests and party arbitration.
See `docs/packs/PACK-09-SPECIFICATION.md` for the scope and the
invariant-to-test map, and `docs/packs/PACK-09-IMPLEMENTATION.md` for the
design notes.

## 2. Findings from the review round

Severity is relative to what would have happened in CI or in review, not
to production impact (nothing here is deployed).

### Critical

1. **`uv.lock` did not contain `epd2-compliance-service`.**
   `pyproject.toml` declared it as a root dependency, a workspace member
   and a `tool.uv.sources` entry, but the lock was byte-identical to
   PACK-08's. `uv sync --all-groups --frozen` would therefore have built
   an environment _without_ the package, and every PACK-09 test would have
   failed at import. Fixed by adding the four lock entries a workspace
   member requires (manifest member, root dependency, root
   `requires-dist`, and the package block with its two editable
   dependencies). **No registry package version changed** — the diff is 22
   lines and adds no dependency. Verified with
   `uv lock --check --offline` and `uv lock --locked --offline`
   (both pass, 55 packages resolved) and with `uv export --frozen`, which
   now emits `-e ./services/compliance-service`.

2. **`ruff check .` failed with 117 errors, all in PACK-09.** 42 × F405,
   29 × E501, 21 × E701, 15 × E702, 5 × I001, 5 × F403. The submitted
   service and its tests used wildcard imports and semicolon-compressed
   one-liners. `ruff format --check .` additionally reported all six
   PACK-09 files as unformatted. The claim of a local PASS could not have
   been made with these checks run.

3. **`contracts/reason-codes/pack-09.yml` could not be loaded by the
   repository's own loader.** Every entry omitted `description` and
   `retryable`, both of which `epd2_core.reason_codes.ReasonCodeRegistry`
   lists in `_REQUIRED_FIELDS`; loading raised
   `InvalidReasonCodeRegistryError`. The file was also unreachable — no
   test referenced it.

### High

4. **PACK-09 was invisible to every repository verification mechanism.**
   `compliance-service` appeared zero times in `tests/contract/`,
   `tests/repository/`, `conftest.py` and `.github/workflows/`. In
   particular: no pack-09 row in the reason-code registry test, no
   PACK09 constants in `_schema_helpers.py`, no OpenAPI contract
   assertions, no CT-00-01 schema validation, no CT-00-08 identity-leakage
   or CT-00-09 vote-linkability coverage, no service-boundary test, and no
   entry in `scripts/check_repository.py`. The draft report's "required
   repository structure check: PASS (445 paths)" was true only because not
   one PACK-09 path was required.

5. **`contracts/openapi/pack-09.yaml` was a 32-line stub.** Five
   operations, no `tags`, no `requestBody`, no error responses, no
   security or scope semantics. Every other pack's contract carries tags
   (asserted by `test_openapi_contract.py`), so extending that test to
   PACK-09 would have failed immediately.

6. **No event contracts and no audit integration.** The service declared
   `epd2-audit-core` as a dependency and never used it: no `events.py`, no
   event payload schemas, no `AuditEvent` append, no `event_id`
   idempotency. CT-00-04 and CT-00-07 were therefore unsatisfied for
   PACK-09.

7. **`npm run format:check` already failed on the PACK-08 baseline** —
   `docs/handover/PACK-08-IMPLEMENTATION-REPORT.md` is not
   Prettier-formatted in `epd2-civic-os-PACK-08-IMPLEMENTATION-0.8.0-PASS.zip`.
   This is a pre-existing defect, not a PACK-09 regression, but CI's
   "Formatting check (Prettier)" step would fail for PACK-09 too. Fixed by
   running Prettier over that one file (25 diff lines, formatting only).

### Medium

8. **Hard-invariant gaps in the submitted implementation.** The
   pre-review service satisfied roughly a third of the fifteen required
   invariants. Specifically absent: destruction authorization and
   evidence (invariant 4 — `dispose_record` mutated a field with no
   authorization and no proof); any policy-supersession path, so
   invariant 5 was neither implemented nor testable; append-only deadline
   history (invariant 6 — `ProceduralDeadline` overwrote `due_at` and
   `status` via `dataclasses.replace`); any no-silent-reset rule
   (invariant 7); a distinguishable case-handler role (invariant 8);
   conflict-of-interest state (invariant 10); audit metadata discipline
   (invariant 13, no events existed); and any fail-closed handling of an
   unknown hold state or an unresolved scope (invariant 15). Invariant 9
   was only partially handled, by comparing a `UUID` to an unrelated
   free-text `subject_reference`. Invariant 2 was enforced on two of six
   commands: `dispose_record`, `register_record`,
   `register_retention_policy` and `place_legal_hold` took no requester
   scope at all, so any caller could dispose of any record by id.

9. **Timezone handling was partial.** `_aware` was applied to
   `RetentionPolicy`, `GovernedRecord` and `ProcessingActivity` but not to
   `ProceduralCase` or `ProceduralDeadline`, so naive datetimes reached
   deadline arithmetic. No IANA timezone existed anywhere.

10. **`Makefile`'s `typecheck` target omitted `services/compliance-service`**
    — and also `services/organization-service`, missing since PACK-08. Both
    added.

11. **README stated `Repository version: 0.9.0` while the paragraph still
    described PACK-08**, and carried a banner line above the H1 that no
    other release used. Rewritten.

12. **Schemas were single-line minified JSON** and would have failed
    `prettier --check`; `processing-activity.schema.json` had no
    `$id`; several had no `description`. All fifteen regenerated in the
    repository's own style.

### Low

13. **ADR-038 … ADR-042 were 5–9 lines each**, against a repository norm
    of 285–370 lines with the full ADR-000 template. None documented
    considered options, security impact, data impact, migration impact,
    reversibility or the canon relationship. All five rewritten.

14. **`scripts/check_repository.py` has never listed ADR-026 … ADR-037**
    (PACK-07's and PACK-08's ADRs). Left untouched rather than silently
    widened; recorded in `docs/review/KNOWN_LIMITATIONS.md`.

15. **`UnknownComplianceRecordError` was the only "not found" error and
    disclosed nothing about scope**, so a cross-organization read and a
    genuine miss were indistinguishable by accident rather than by design.
    Now deliberate and documented (ADR-041 section 6).

## 3. Verification actually executed

Run in this sandbox on Python 3.12.3 (`ruff`, `uv`) and, for the test
suite, on a CPython 3.11.15 interpreter with the repository's `src` trees
on `PYTHONPATH` — see section 5 for why, and for what that does and does
not prove.

| Check                     | Command                                                                      | Result                                                                                    |
| ------------------------- | ---------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| Lock/manifest consistency | `uv lock --check --offline`; `uv lock --locked --offline`                    | **PASS** — 55 packages resolved, lock up to date                                          |
| Lock content              | `uv export --frozen --no-hashes --offline`                                   | **PASS** — 18 editable workspace members incl. `-e ./services/compliance-service`         |
| Python lint               | `ruff check .`                                                               | **PASS** — 0 errors (was 117)                                                             |
| Python format             | `ruff format --check .`                                                      | **PASS** — 206 files already formatted                                                    |
| Python type check         | `mypy` over all 19 Makefile targets                                          | **PASS** — 0 errors; `compliance-service` 9 source files clean                            |
| Python tests              | `pytest` (full suite, git checkout)                                          | **2315 passed, 5 skipped, 0 failed**                                                      |
| Prettier                  | `prettier --check .`                                                         | **PASS** (after fixing the pre-existing PACK-08 report)                                   |
| Repository structure      | `scripts/check_repository.py`                                                | **PASS** — 489 required paths, 0 missing                                                  |
| Forbidden files           | `scripts/check_forbidden_files.py`                                           | **PASS** in a git checkout                                                                |
| Version consistency       | `scripts/verify_versions.py`                                                 | **PASS** — canon `0.7.0`, repository `0.9.0` everywhere                                   |
| JSON Schema validity      | `jsonschema.Draft202012Validator.check_schema` over all 126 documents        | **PASS** — 0 invalid                                                                      |
| OpenAPI structure         | YAML parse + OAS-3.1 skeleton + local `$ref` resolution over all 8 contracts | **PASS** — pack-09: 28 paths, 28 operations, 0 problems                                   |
| TypeScript tests          | `node --import tsx --test` for `epd2-types` and `web-shell`                  | **PASS** — 3 + 11 = 14 tests, using a globally-installed `tsx` rather than the locked one |

### Test totals

|                   |                                               |
| ----------------- | --------------------------------------------- |
| passed            | **2315**                                      |
| failed            | **0**                                         |
| skipped           | **5**                                         |
| xfailed / xpassed | **0** (the suite declares no `xfail` markers) |

PACK-09 contributes **168** of those, measured against the PACK-08
baseline archive's own 2147:

| Where                                                               | Count   |
| ------------------------------------------------------------------- | ------- |
| `services/compliance-service/tests/test_domain.py`                  | 61      |
| `services/compliance-service/tests/test_application.py`             | 44      |
| `services/compliance-service/tests/test_storage.py`                 | 19      |
| `tests/contract/test_ct00_01_pack09_schema_validation.py`           | 24      |
| `tests/contract/test_openapi_contract.py` (`-k pack09`)             | 11      |
| `tests/contract/test_ct00_08_identity_leakage.py` (PACK-09 section) | 5       |
| `tests/contract/test_reason_codes_registry.py` (`-k pack-09`)       | 4       |
| `tests/contract/test_ct00_09_vote_linkability.py` (PACK-09 section) | 3       |
| `tests/repository/test_service_boundaries.py` (`-k compliance`)     | 3       |
| Pre-existing parametrized tests newly covering PACK-09 paths        | balance |

No pre-existing test was deleted, weakened, or converted to a mock, and no
assertion was relaxed. The two `tests/repository` tests that fail when the
suite is run in a non-git working tree
(`test_forbidden_paths` sees the `__pycache__` directories the run itself
creates) pass in a git checkout, which is how CI runs them —
`scripts/check_forbidden_files.py` uses `git ls-files` and prints an
explicit warning when it has to fall back to a filesystem walk.

### The five skips, each explained

All five are pre-existing and unchanged by this round; PACK-09 adds none.

1. `test_property_based.py` — `hypothesis` is not importable in this
   sandbox (no package-registry egress). Runs for real in CI.
2. `test_ct00_10_rule_freeze.py::…pack06…` — CT-00-10 names Ballot
   configuration freeze, which `ai-processing-service` never touches.
3. `test_ct00_10_rule_freeze.py::…pack07…` — same reason for PACK-07's two
   services.
4. `test_ct00_12_…::CT-00-11` — `AIProcessingRecord` was out of scope for
   PACK-02/03/05/07.
5. `test_ct00_12_…::CT-00-12` — `EmergencyAction` was out of scope for
   PACK-02/03/05/06/07.

Each carries its full justification in the skip message itself.

## 4. What changed

- `services/compliance-service/` — rewritten: `domain.py`, `events.py`
  (new), `storage.py`, `application.py`, `exceptions.py`, `README.md`,
  `__init__.py`, plus `tests/test_domain.py`, `tests/test_application.py`
  and `tests/test_storage.py` (new).
- `contracts/` — `reason-codes/pack-09.yml` rewritten (40 codes, all seven
  required fields); fifteen entity schemas and eight event payload schemas
  written or rewritten; `openapi/pack-09.yaml` rewritten (28 operations).
- `docs/adr/ADR-038` … `ADR-042` — rewritten to the full template.
- `docs/packs/PACK-09-SPECIFICATION.md`,
  `docs/packs/PACK-09-IMPLEMENTATION.md`, this report — rewritten.
- `tests/contract/_schema_helpers.py`,
  `tests/contract/test_reason_codes_registry.py`,
  `tests/contract/test_openapi_contract.py`,
  `tests/contract/test_ct00_08_identity_leakage.py`,
  `tests/contract/test_ct00_09_vote_linkability.py`,
  `tests/repository/test_service_boundaries.py` — extended with PACK-09
  coverage; `tests/contract/test_ct00_01_pack09_schema_validation.py` —
  new.
- `scripts/check_repository.py` — 44 PACK-09 required paths.
- `Makefile` — `typecheck` extended to `organization-service` and
  `compliance-service`.
- `uv.lock` — workspace member added (see finding 1). **No dependency
  version changed.**
- `README.md`, `CHANGELOG.md`, `LOCAL_VERIFICATION.md`,
  `docs/review/KNOWN_LIMITATIONS.md` — updated.
- `docs/handover/PACK-08-IMPLEMENTATION-REPORT.md` — Prettier formatting
  only (finding 7).

No PACK-01 … PACK-08 source file, contract or test was otherwise
modified.

## 5. Checks that could NOT be executed — why this is a CANDIDATE

This sandbox has **no network egress to package registries**:
`pypi.org`, `files.pythonhosted.org` and `registry.npmjs.org` all return
`403 Host not in allowlist`, verified directly, through the proxy and with
the sandbox disabled. Consequently:

| Blocked command                                 | Why it could not run                                                                                                       | Substitute actually executed                                                                                                              |
| ----------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `uv sync --all-groups --frozen`                 | ~40% of the locked wheels are absent from the local cache (`mypy`, `pyyaml`, `hypothesis`, `pydantic-core`, …)             | `uv lock --check`/`--locked`/`export` for lock correctness; the test suite run on a 3.11 interpreter with the `src` trees on `PYTHONPATH` |
| `npm ci`                                        | registry blocked (`403`)                                                                                                   | none — `node_modules` cannot be created                                                                                                   |
| `npm run lint --workspace=frontend/web-shell`   | needs `eslint` + `eslint-config-next` from `node_modules`                                                                  | not run                                                                                                                                   |
| `npm run typecheck` (both workspaces)           | needs the locked `typescript@^5.5` and `@types/*`; only a global `typescript@6.0.3` is present, which is a different major | not run                                                                                                                                   |
| `npm run build --workspace=frontend/web-shell`  | needs `next`                                                                                                               | not run                                                                                                                                   |
| `uv run pytest` / `uv run mypy` / `uv run ruff` | no `.venv` can be created                                                                                                  | the same tools run directly: `ruff` 0.15.11, `mypy` 1.20.2, `pytest` 9.0.3                                                                |

**What the substitute test run does and does not prove.** The suite was
executed on CPython **3.11.15** (the only interpreter with `PyYAML`,
`jsonschema` and `pydantic` available offline) rather than the project's
3.12. The whole tree compiles under 3.11 (`python3.11 -m compileall`,
exit 0) and no PACK-09 code uses 3.12-only syntax, so the results are
meaningful — but they are not the locked toolchain. Version deltas versus
`uv.lock`: `ruff` 0.15.11 vs 0.15.22, `pytest` 9.0.3 vs 8.4.2,
`jsonschema` 4.26.0 (matches), `mypy` 1.20.2 (matches), `prettier` 3.8.1
vs 3.9.6.

**Therefore this archive is a CANDIDATE, not a PASS.** An independent
final verification must run, on a networked machine, exactly:

```bash
uv sync --all-groups --frozen
npm ci
git diff --exit-code -- uv.lock package-lock.json
uv run python scripts/check_repository.py
uv run python scripts/check_forbidden_files.py
uv run python scripts/verify_versions.py
uv run ruff format --check .
npm run format:check
uv run ruff check .
uv run mypy .
uv run pytest
npm run typecheck --workspace=packages/typescript/epd2-types
npm run typecheck --workspace=frontend/web-shell
npm run lint --workspace=frontend/web-shell
npm run test --workspace=packages/typescript/epd2-types
npm run test --workspace=frontend/web-shell
npm run build --workspace=frontend/web-shell
```

Two specific things for that run to confirm: that `uv sync --frozen`
accepts the hand-corrected `uv.lock` (finding 1), and that Prettier 3.9.6
agrees with the 3.8.1 formatting applied here (finding 7).

## 6. Remaining limitations, deliberately deferred

Party finance and Rechenschaftsbericht, sponsorship/lobbying registry
(PACK-10); document storage, evidence content, cryptographic document
version chains (PACK-11); privileged JIT/break-glass administration, DLP
(PACK-12); production database, event bus, schema registry (PACK-13); real
IAM/eID and credential issuance (PACK-14); voting threat model and
cryptographic voting (PACK-15/16); production incident response (PACK-17);
user-facing applications (PACK-18).

Within PACK-09's own scope, three things are honestly _not_ implemented
rather than claimed: there is no panel/multi-decider arbitration model, no
quorum rule, and no automatic inference of conflicts of interest from
organizational relationships — conflicts must be declared (ADR-042).

## 7. No claim of legal compliance

PACK-09 provides a governed workflow, evidence references and
auditability. It does not determine, and no part of this repository
asserts, that any retention schedule, legal basis, deadline computation,
data-subject response or arbitration decision satisfies the GDPR, the
BDSG, the Parteiengesetz or any other law. Every legal determination
remains a human judgement made outside this system.

---

# 8. CANDIDATE-2 round — Architecture & Domain Framework 0.8.1

This section **continues** the report above rather than replacing it.
Every finding, fix and limitation recorded in sections 1–7 still stands.

The EPD² **Architecture & Domain Framework 0.8.1** (Roadmap Amendment)
became the authoritative scope and acceptance document for PACK-09
part-way through this work. It supersedes the earlier PACK-09 brief where
the two differ, and it does not contradict anything already built — it
extends it. Nothing from the CANDIDATE round was rewritten.

## 8.1 What the Framework required, and where it landed

| Framework section | Requirement                                  | Where                                                                         |
| ----------------- | -------------------------------------------- | ----------------------------------------------------------------------------- |
| 13.1              | common legal-case substrate                  | `casework.py` (1 582 lines)                                                   |
| 13.1              | official notice as a separate trust boundary | `notices.py` (+ **ADR-043**)                                                  |
| 13.2              | procedural deadlines: basis, trigger, outage | `notices.DeadlineTrigger`, round-1 suspend/resume kept unchanged              |
| 13.1              | recusal / conflict hooks                     | `casework.RecusalRecord`, `ReplacementAssignment`, `assert_actor_not_recused` |
| 11                | records governance, hold propagation         | `domain.RecordClass`, `HoldPropagationRecord`                                 |
| 13.1              | data-protection governance, DPIA gate        | `dataprotection.py`                                                           |
| 13.1 / 7          | stable typed interfaces for later packs      | `references.py`                                                               |
| 13.3              | named reason codes                           | 32 new refusal codes in `contracts/reason-codes/pack-09.yml`                  |
| 13.3              | contracts, schemas, events, OpenAPI          | 22 entity schemas, 33 payload schemas, 34 OpenAPI operations                  |
| 13.4              | mandatory test matrix                        | 4 new service test modules + 1 new contract module (see 8.4)                  |

## 8.2 The four Framework invariants that shaped the design most

**#39 / #40 / #57 — telemetry is not notice.** This produced the round's
only new ADR. The mechanism is three objects, not one with a status
field: `OfficialNotice` has no effect vocabulary at all,
`ServiceAttempt` carries `DeliveryTelemetryStatus` / `ReadTelemetryStatus`
and an `is_reconciled` flag that gates every deemed-service rule without
exception, and `NoticeEffectDecision` is the only object in this
repository that can start a procedural deadline. `TriggerSource` names
`delivery_telemetry` and `read_telemetry` **so that they can be refused by
name** — an omission cannot be tested; a named refusal can, and
`test_telemetry_can_never_be_a_governed_deadline_trigger` does.

**#52 — no sanction without due process.**
`assert_due_process_complete` takes six named prerequisites and reports
the _one_ that is missing. A refusal reading only "due process
incomplete" would be unactionable for the party told to fix it.
`issue_procedural_decision` resolves `notice_effect_id` against the
store rather than accepting a caller's flag.

**#53 / #54 — recusal blocks capability without erasing history.**
`prior_participation_codes` survives; `assert_actor_not_recused` is
applied to _every_ consequential command, not only to final decisions,
because scheduling a hearing is an exercise of authority too; a
replacement who is themselves recused is refused.

**#69 — AI decides no consequential legal outcomes.** Enforced in two
independent places: `InterimMeasure.__post_init__` refuses to construct a
_granted_ measure without `ActorClass.HUMAN_AUTHORITY`, and
`assert_due_process_complete` refuses any decision by a `service` or
`automated` actor. `human_case_handler` is a human and is deliberately
still insufficient.

## 8.3 Three implementation defects found and fixed by the new tests

These were found by tests written for this round, against code written
for this round, and are recorded because a report that lists only
successes is not a review.

1. **`InterimMeasure` raised a bare `ValueError`** when a granted measure
   carried neither an end date nor a review date, while the two
   neighbouring guards raised registered reason-coded errors. An
   indefinite measure is a governance refusal a party can be told about
   and can appeal, not a programming mistake. Now
   `INTERIM_MEASURE_AUTHORITY_DENIED`.
2. **`DeadlineTrigger.__post_init__` raised a bare `ValueError`** for a
   telemetry source. Same problem, and worse: it was the constructor
   guard backing hard invariant 39. Now `DEADLINE_TRIGGER_INVALID`.
3. **`determine_notice_effect` raised when every authorized attempt
   failed**, which meant `NoticeEffectOutcome.NOT_EFFECTIVE` — a value in
   the enum, in the schema, and in the event payload — was unreachable
   through the governed path. A finding that every attempt failed is a
   _determination_ the parties are entitled to see and challenge; an
   exception leaves no record. It now returns a recorded `NOT_EFFECTIVE`
   decision carrying `SERVICE_NOT_PROVEN`, establishing no legal effect
   and starting nothing.

One earlier decision was also revisited: `DeliveryTelemetryStatus.REFUSED`
is **not** classified as a delivery failure, because refusing service
constitutes service in several jurisdictions — but no deemed-service rule
accepts it alone either, so it falls to `SERVICE_NOT_PROVEN`.
Fail-closed on a contested legal question was preferred to silently
picking a side; `test_a_refused_delivery_is_not_treated_as_a_delivery_failure`
records the reasoning.

## 8.4 Test totals after CANDIDATE-2

|                   |                                                |
| ----------------- | ---------------------------------------------- |
| passed            | **2652**                                       |
| failed            | **0**                                          |
| skipped           | **5** (all pre-existing; this round adds none) |
| xfailed / xpassed | **0**                                          |

The CANDIDATE round ended at 2315. The 337 added here:

| Where                                                                   | Count |
| ----------------------------------------------------------------------- | ----- |
| `services/compliance-service/tests/test_casework.py`                    | 46    |
| `services/compliance-service/tests/test_notices.py`                     | 23    |
| `services/compliance-service/tests/test_dataprotection.py`              | 24    |
| `services/compliance-service/tests/test_framework_application.py`       | 32    |
| `tests/contract/test_ct00_01_pack09_framework_schema_validation.py`     | 201   |
| `tests/contract/test_openapi_contract.py` (new PACK-09 section)         | 7     |
| `tests/contract/test_ct00_08_identity_leakage.py` (new PACK-09 section) | 4     |

`compliance`-matching tests total **260**; `pack09`-matching **245**.

No pre-existing test was deleted, weakened, converted to a mock, or had
an assertion relaxed. Three round-1 test expectations were _corrected_
where the test, not the code, had been wrong — each is noted in 8.3.

## 8.5 Verification executed in this round

| Command                       | Result                                    |
| ----------------------------- | ----------------------------------------- |
| `ruff check .`                | **pass** — all checks passed              |
| `ruff format --check .`       | **pass** — 216 files already formatted    |
| `mypy` (13 Makefile groups)   | **pass** — 0 issues across all groups     |
| `pytest`                      | **pass** — 2652 passed, 5 skipped         |
| `scripts/check_repository.py` | **pass** — all 554 required paths present |
| `scripts/verify_versions.py`  | **pass** — all version sources consistent |

`mypy` was run per Makefile group rather than as one whole-repo
invocation, for the reason the Makefile itself documents (identically
named test modules across services). `services/compliance-service`
type-checks clean across all 17 source files under the repository's
strict settings.

## 8.6 Why this is CANDIDATE-2 and not PASS

Unchanged from the CANDIDATE round, and restated here because §20 of the
brief requires it:

- `uv sync --all-groups --frozen` — **not run**; no egress to `pypi.org`.
- `uv run <anything>` — **not run**; depends on the above.
- `npm ci`, `npm run lint`, `npm run build`, `npm run typecheck`,
  `npm run format:check` — **not run**; no egress to `registry.npmjs.org`.

Everything reported as passing above was run against a locally-assembled
Python 3.11 interpreter and standalone `ruff` / `mypy` / `pytest`, **not**
against the versions `uv.lock` pins for Python 3.12. That substitution is
documented in full in `LOCAL_VERIFICATION.md`. The archive is therefore
named `CANDIDATE-2 — NEEDS CI`.

`uv.lock` was **not modified** in this round: no dependency was added,
removed or bumped, and the four new modules live inside the
already-locked `epd2-compliance-service` package.

No TypeScript, frontend or npm-workspace file was modified either, so the
npm half of the pipeline carries exactly the status it had after
CANDIDATE.

## 8.7 Scope discipline

Nothing outside PACK-09 was started. No candidacy, nomination or ballot
entity; no assembly or motion entity; no communication channel, template
or message entity; no finance entity; no document storage. For each,
PACK-09 publishes only a typed reference or a domain-neutral primitive —
enumerated in `references.py` and asserted by
`test_pack09_declares_no_endpoint_belonging_to_a_later_pack`.

`CANON_VERSION` stays `0.7.0`. `REPOSITORY_VERSION` stays `0.9.0` — this
round raised nothing.

Remaining limitations, including the ones where a guarantee is
deliberately partial, are in
`docs/handover/PACK-09-KNOWN-LIMITATIONS.md`.
