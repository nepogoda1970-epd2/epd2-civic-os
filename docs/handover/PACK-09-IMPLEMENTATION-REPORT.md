# PACK-09 Implementation Report

|                    |                                                                    |
| ------------------ | ------------------------------------------------------------------ |
| Date               | 2026-07-26                                                         |
| Status             | **PACK-09 IMPLEMENTATION 0.9.0 — EXTERNAL CI PASS** (section 3)    |
| Repository version | `0.8.0` → `0.9.0`                                                  |
| Canon version      | `0.7.0` (unchanged; no canon-owned file touched)                   |
| New service        | `services/compliance-service`                                      |
| ADRs               | ADR-038 … ADR-043, all `accepted`                                  |
| Authoritative spec | EPD² Architecture & Domain Framework **0.8.1** (Roadmap Amendment) |

This report replaces the pre-review draft of the same name. That draft
claimed `LOCAL PASS`; the review round established that several mandatory
checks had not in fact been run and that the pack was not wired into the
repository's own verification machinery at all. What follows records what
was found, what was changed, and — in section 3 — the external CI run
that verified the result.

The full pipeline has since been executed on GitHub Actions against the
locked toolchain and passed. Section 3 is the single verification record;
the sandbox-substitute results that earlier revisions carried have been
removed rather than kept alongside it.

This is an implementation and verification statement only. It is **not**
a statement that the system is production-ready, deployed, or legally
activated.

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

## 3. Verification — external CI

The whole pipeline was executed on **GitHub Actions / ubuntu-latest**,
Python 3.12, Node.js 22, against the locked toolchain (`uv sync
--all-groups --frozen`, `npm ci`). This is the only verification record
for PACK-09; earlier sandbox-substitute results have been removed rather
than kept alongside it, so no two totals in this document can disagree.

**Overall result: All checks passed.**

| Check                    | Command                                                   | Result                                                                         |
| ------------------------ | --------------------------------------------------------- | ------------------------------------------------------------------------------ |
| Repository structure     | `scripts/check_repository.py`                             | **PASS** — 556 required paths                                                  |
| Forbidden files          | `scripts/check_forbidden_files.py`                        | **PASS** — no forbidden paths                                                  |
| Version consistency      | `scripts/verify_versions.py`                              | **PASS** — all sources consistent                                              |
| Python format            | `ruff format --check .`                                   | **PASS**                                                                       |
| Prettier                 | `npm run format:check`                                    | **PASS**                                                                       |
| Python lint              | `ruff check .`                                            | **PASS**                                                                       |
| Frontend lint            | `npm run lint --workspace=frontend/web-shell`             | **PASS**                                                                       |
| Python type check        | `mypy` over every Makefile group                          | **PASS** — all services, incl. `organization-service` and `compliance-service` |
| Python tests             | `pytest`                                                  | **2659 passed, 4 skipped, 0 failed**                                           |
| TypeScript package tests | `npm run test --workspace=packages/typescript/epd2-types` | **3 passed**                                                                   |
| Frontend tests           | `npm run test --workspace=frontend/web-shell`             | **11 passed**                                                                  |
| Production build         | `npm run build --workspace=frontend/web-shell` (Next.js)  | **PASS**                                                                       |

The raw runner output is preserved verbatim in
`docs/handover/PACK-09-EXTERNAL-CI-VERIFICATION.log`, and the runner's own
summary in `docs/handover/PACK-09-EXTERNAL-CI-VERIFICATION-RESULT.md`.

### Test totals

|                   |                                               |
| ----------------- | --------------------------------------------- |
| passed            | **2659**                                      |
| failed            | **0**                                         |
| skipped           | **4**                                         |
| xfailed / xpassed | **0** (the suite declares no `xfail` markers) |

### What PACK-09 contributes to that suite

Counts of tests added by this pack, against the PACK-08 baseline
archive's own 2147. These are components of the 2659 above, not a
competing total.

| Where                                                               | Count   |
| ------------------------------------------------------------------- | ------- |
| `services/compliance-service/tests/test_domain.py`                  | 61      |
| `services/compliance-service/tests/test_application.py`             | 50      |
| `services/compliance-service/tests/test_storage.py`                 | 13      |
| `services/compliance-service/tests/test_casework.py`                | 46      |
| `services/compliance-service/tests/test_notices.py`                 | 23      |
| `services/compliance-service/tests/test_dataprotection.py`          | 24      |
| `services/compliance-service/tests/test_framework_application.py`   | 32      |
| `tests/contract/test_ct00_01_pack09_schema_validation.py`           | 24      |
| `tests/contract/test_ct00_01_pack09_framework_schema_validation.py` | 201     |
| PACK-09 sections in the shared CT-00, OpenAPI and repository suites | balance |

`-k compliance` matches **260** tests; `-k pack09` matches **245**.

No pre-existing test was deleted, weakened, converted to a mock, or had an
assertion relaxed.

### The four skips, each explained

All four are pre-existing; PACK-09 adds none. Each carries its full
justification in the skip message itself.

1. `test_ct00_10_rule_freeze.py::…pack06…` — CT-00-10 names Ballot
   configuration freeze, which `ai-processing-service` never touches.
2. `test_ct00_10_rule_freeze.py::…pack07…` — same reason for PACK-07's two
   services.
3. `test_ct00_12_…::CT-00-11` — `AIProcessingRecord` was out of scope for
   PACK-02/03/05/07.
4. `test_ct00_12_…::CT-00-12` — `EmergencyAction` was out of scope for
   PACK-02/03/05/06/07.

## 4. What changed in the review round

Counts in this section describe the review round specifically. The
Framework 0.8.1 round that followed is recorded in section 8, and the
final artefact counts are stated there.

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
- `README.md`, `CHANGELOG.md`, `LOCAL_VERIFICATION.md` — updated.
- `docs/handover/PACK-08-IMPLEMENTATION-REPORT.md` — Prettier formatting
  only (finding 7).

No PACK-01 … PACK-08 source file, contract or test was otherwise
modified.

## 5. Two questions the external run had to settle

The pack was submitted for CI with two open questions, both raised by
findings in section 2. Both are now answered by the run recorded in
section 3:

1. **Does `uv sync --all-groups --frozen` accept the hand-corrected
   `uv.lock`?** Yes. The lock file was corrected by hand when the
   submission was found to have added `epd2-compliance-service` to
   `pyproject.toml` without regenerating the lock; the frozen install
   succeeded on the runner, so the environment CI builds does contain the
   package.
2. **Does the locked Prettier version agree with the formatting applied
   offline?** Yes. `npm run format:check` passed under the locked
   toolchain.

No further verification is outstanding.

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

# 8. Architecture & Domain Framework 0.8.1 round

This section **continues** the report above rather than replacing it.
Every finding, fix and limitation recorded in sections 1–7 still stands.

The EPD² **Architecture & Domain Framework 0.8.1** (Roadmap Amendment)
became the authoritative scope and acceptance document for PACK-09
part-way through this work. It supersedes the earlier PACK-09 brief where
the two differ, and it does not contradict anything already built — it
extends it. Nothing from the earlier round was rewritten.

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

## 8.4 Verification

See **section 3**. That section is the single verification record for this
pack; this round adds no separate totals.

## 8.5 Scope discipline

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
