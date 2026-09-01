# CLAUDE-PACK-06 — AI Processing Context: Handover Report

**PACK-06 PASS — confirmed by a complete external GitHub Actions run
with real network access.** This report follows the same honesty
convention `docs/handover/PACK-02-REPORT.md` through
`docs/handover/PACK-05-REPORT.md` established: every check this sandbox
can actually run is run for real (not skipped, not asserted from memory)
and its literal output is quoted below; every check this sandbox itself
cannot run (network-gated `uv lock`/`npm install`, and everything
downstream of them locally — `npm run typecheck`, ESLint, the
TypeScript/frontend test suites, `next build`) is named explicitly as
not run locally, for the same reason PACK-02 through PACK-05 already
documented (`pypi.org`/`files.pythonhosted.org`/`registry.npmjs.org` all
return `403` from this sandbox). Sections 0a through 0c below record the
three real gaps external GitHub Actions runs found and this pack fixed
en route (a six-file Prettier formatting gap, a `CHANGELOG.md` Markdown
authoring defect, and a stale TypeScript version-test literal); section
0d records the final external run's own results, matching PACK-05's own
`0a`–`0c`-then-PASS revision history pattern.

```text
PACK-06 PASS (external GitHub Actions confirmed)
```

## 0a. First external Prettier finding and fix (revision 2)

The first real external GitHub Actions run against
`epd2-civic-os-PACK-06-final-candidate.zip` reported a Prettier
format-check failure on exactly six files, all newly written this pack
and never run through Prettier locally before revision 1's export:

```text
[warn] CHANGELOG.md
[warn] contracts/events/ai-processing-record-payload.v1.schema.json
[warn] contracts/openapi/pack-06.yaml
[warn] contracts/schemas/ai-processing-record.schema.json
[warn] docs/handover/PACK-06-REPORT.md
[warn] services/ai-processing-service/README.md
[warn] Code style issues found in 6 files. Run Prettier with --write to fix.
make: *** [Makefile:22: format-check] Error 1
```

Unlike some earlier packs' own first Prettier findings, this sandbox's
own system Prettier (3.8.1) reproduced the identical six-file list
before any fix was applied — no version-disagreement diagnosis was
needed this time. Fixed with the repository's own exact command,
`npm run format` (`prettier --write .`, resolving to the same command
`make format` runs):

```text
$ npm run format
> prettier --write .
... (every other tracked file reported "(unchanged)") ...
services/ai-processing-service/README.md 30ms
CHANGELOG.md ...ms
docs/handover/PACK-06-REPORT.md ...ms
contracts/events/ai-processing-record-payload.v1.schema.json ...ms
contracts/openapi/pack-06.yaml ...ms
contracts/schemas/ai-processing-record.schema.json ...ms

$ npm run format:check
> prettier --check .
Checking formatting...
All matched files use Prettier code style!
```

Re-verified with a file-by-file diff against the revision-1 archive
that every change is pure formatting, nothing semantic: the two JSON
Schema files had their `enum` arrays re-wrapped onto multiple lines
(Prettier's `printWidth` line-break rule — same array elements, same
order, same values); `contracts/openapi/pack-06.yaml` had one flow-style
YAML mapping (`record: { $ref: ... }`) re-wrapped across two lines in
four places (same key, same `$ref` value); `services/ai-processing-service/README.md`
and `docs/handover/PACK-06-REPORT.md` had `*emphasis*`-style markdown
markers normalized to `_emphasis_` style plus one markdown table's
column widths re-padded (same cell content); `CHANGELOG.md` had several
long lines re-wrapped at Prettier's line-length boundary (same words,
same order). No reason code, schema field, enum value, test, canon
text, ADR text, or version string was touched — confirmed by re-running
the complete local verification suite after the fix: identical to
revision 1 in every respect (363/363 required paths, canon checksum
unchanged, Ruff clean, mypy clean across all sixteen groups, 1815
passed / 4 skipped / 0 failed, `prettier --check .` now also clean
across the full tree).

`make format-check`'s own first step, `uv run ruff format --check .`,
still cannot run in this sandbox (network-gated `uv sync`, section 1) —
the standalone `/root/.local/bin/ruff format --check .` and
`/opt/node22/bin/prettier --check .` (== `npm run format:check`) were
run directly instead, both clean, exactly as every prior pack's own
local-only revision already documents for this same sandbox ceiling.

## 0b. Second external Prettier finding, real root cause found (revision 3)

The next external GitHub Actions run — against the revision-2 candidate
archive — reported Prettier still failing on exactly one file,
`CHANGELOG.md`, despite this sandbox's own system Prettier (3.8.1)
reporting that file clean both before and after the revision-2 fix.
Reading the file directly (rather than assuming another Prettier
version disagreement) found a genuine Markdown authoring defect: the
`[0.6.0]` entry's PACK-06 test-coverage bullet had lost its
list-continuation indentation and inter-word spacing across roughly
twenty lines. A literal `*` was used as an ad hoc wildcard
(`unknown-processing*status`, `` `parse**` ``/`` `Unknown*Error` ``) —
asterisks are Markdown emphasis delimiters, and a bare `*`/`**` sitting
inside plain prose or straddling a code-span boundary is a genuinely
ambiguous construct different Markdown/Prettier tokenizer versions parse
differently; several inline code spans were also missing their
surrounding whitespace, collapsing distinct words into single unbroken
tokens. The wildcard shorthand was also factually imprecise — the two
functions and two exceptions it abbreviated are
`parse_processing_status`/`parse_human_review_status` and
`UnknownProcessingStatusError`/`UnknownHumanReviewStatusError`
(confirmed by reading `services/ai-processing-service/src/
epd2_ai_processing_service/domain.py` and `exceptions.py` directly).

**Fixed at the source, content unchanged in meaning:** the bullet was
rewritten in full — correct list-continuation indentation, a space
around every inline code span, and every wildcard-style abbreviation
replaced with the real names spelled out in full. Verified with the
repository's own exact command:

```text
$ /opt/node22/bin/prettier --write CHANGELOG.md
CHANGELOG.md 192ms (unchanged)

$ /opt/node22/bin/prettier --check CHANGELOG.md
Checking formatting...
All matched files use Prettier code style!
```

Only `CHANGELOG.md` was touched this round (per that round's explicit
instruction) — confirmed by diffing the full working tree against the
revision-2 archive, which showed exactly one file differing. The
complete local verification suite was re-run and matched revision 2 in
every other respect: 363/363 required paths, canon checksum unchanged,
`verify_versions.py` consistent, mypy clean across all sixteen scoped
groups, and pytest — 1815 passed, 4 skipped, 0 failed.

## 0c. Stale TypeScript version-test literal found and fixed (revision 4)

The next external GitHub Actions run — against the revision-3 candidate
archive — reported the Prettier finding resolved, but a new failure in
the TypeScript unit test suite:
`packages/typescript/epd2-types/tests/version.test.ts`'s "current
versions match the expected skeleton version" test asserted
`CANON_VERSION === "0.4.0"` and `REPOSITORY_VERSION === "0.5.0"`, stale
literals never updated when this pack's own canon and repository
version bumps happened (section 2). `scripts/verify_versions.py` — which
checks the actual source-of-truth files against each other — had already
been passing throughout, confirming this was purely a stale test literal,
never a source-of-truth inconsistency.

**Fixed — only the one test file touched:** updated the two stale
assertions to `CANON_VERSION, "0.5.0"` and `REPOSITORY_VERSION, "0.6.0"`,
and added two further narrative comments (matching this file's own
established convention of documenting every prior version transition)
describing the `0.4.0 → 0.5.0` canon bump (ADR-023/ADR-025, canon
section 19c) and the `0.5.0 → 0.6.0` repository bump (ADR-021 through
ADR-025), cross-checked directly against `CHANGELOG.md` and the ADR
filenames on disk. A repository-wide grep confirmed this is the only
TypeScript test file referencing `CANON_VERSION`/`REPOSITORY_VERSION` at
all, so no other stale literal existed to fix.

`npm test --workspace packages/typescript/epd2-types` could not be run
in this sandbox (the same pre-existing network ceiling, section 1) — as
an honest substitute, the fixed test's logic was verified manually by
running its assertions (plain, type-annotation-free JavaScript already)
against the real `version.ts` values with Node's built-in test runner
outside the repository tree: all 3 tests passed, including the
previously-failing one. The full local verification suite was re-run
and matched revision 3 in every other respect: 363/363 required paths,
canon checksum unchanged, `verify_versions.py` consistent, mypy clean
across all fifteen scoped Python groups, and pytest — 1815 passed, 4
skipped, 0 failed.

## 0d. Final external GitHub Actions run — PASS confirmed

The external GitHub Actions run against the revision-4 candidate
archive completed successfully with real network access:

```text
Status: PASS
Python: 1822 passed, 3 skipped, 0 failed
TypeScript: 3/3 passed
Frontend tests: 2/2 passed
Next.js production build: successful
Prettier: passed
Ruff: passed
ESLint: passed
mypy: passed
Required paths: all 363 present
Forbidden files: none
```

The 3 skips are the genuine CT-00-10/CT-00-12 not-applicable-in-earlier-
packs markers (section 9); CT-00-11 is no longer among them — it is now
fully applicable and passing for PACK-06 for the first time (section 0
above). This is the first PACK-06 external run with `hypothesis`
installed and the TypeScript/frontend toolchains available, so it is
also the first run to actually execute `test_property_based.py`,
`npm run typecheck`/ESLint/the TypeScript unit tests, and `next build` —
all of which this local sandbox has never been able to run itself
(section 1). No further fix was needed for this run: it confirms
revision 4 (section 0c) as the closing candidate. `REPOSITORY_VERSION`
remains `0.6.0`, `CANON_VERSION` remains `0.5.0`, and the canon checksum
is unchanged (section 2) — nothing in this closeout pass touched
implementation logic, schemas, tests, canon, ADRs, versions, or the
workflow.

## 0. What CLAUDE-PACK-06 adds

Implements the AI Processing Context (canon section 17.1, extended by
section 19c, canon 0.5.0) in a new `services/ai-processing-service`:
`AIProcessingRecord` (two independent status planes —
`processing_status`, the technical pipeline; `human_review_status`, the
unchanged six-value canon 17.1 enum), the embedded, immutable
`RedactionManifest` value object (nine fields), the derived, never-stored
`DisclosureStatus` read model, and `AIDisclosurePackage` (a
contract/value object handed to `transparency-service`, never persisted
by either pack). Covers six closed use classes
(`summarization`/`classification`/`recommendation`/`drafting`/
`anomaly_indication`/`policy_compliance_assistance`) with their own
purpose/target allow-lists, four reviewer roles, a provider abstraction
with no callback/tool/command interface capable of mutating Civic OS, a
redaction/provenance validator this pack performs itself (never trusting
a caller-supplied flag), fourteen named fail-closed conditions, and the
five-step mandatory disclosure protocol (19c.7) delegating publication to
`transparency-service.publish_ledger_entry`. Binding ADRs: ADR-021
(service decomposition), ADR-022 (cross-pack boundary — one narrow
governance read), ADR-023 (canon 0.5.0 additions), ADR-024 (reason-code
additions), ADR-025 (use classes/policy/redaction/providers/disclosure
defaults) — all five `accepted` (ADR-021/ADR-024 without amendment;
ADR-022/ADR-023/ADR-025 accepted with amendments), confirmed by direct
inspection of each ADR's own `## Status` section this pass (section 2
quotes them). Emergency/Crisis Override, frontend/UI, real external
provider credentials, cryptographic signing, and autonomous tool
execution remain explicitly out of scope, per required-scope item 19 —
nothing in any of those areas was touched, and canon 0.5.0 itself was not
edited (it was already accepted before this implementation pass began;
see `docs/review/PACK-06-OWNER-DECISIONS.md`).

## 1. Environment and network status

```text
$ python3 --version
Python 3.11.15
```

This sandbox's network egress still blocks `pypi.org` /
`files.pythonhosted.org` / `registry.npmjs.org` (`403`), consistent with
every prior pack's own report. `uv sync --all-groups` and `npm install`
were not attempted for the same reason already documented in
`docs/handover/PACK-05-REPORT.md` section 1. No `node_modules` exists in
this tree, and no `uv`-synced project venv exists.

Local verification used the pre-existing standalone tool binaries at
`/root/.local/bin/{pytest,mypy,ruff}` and the system `python3`
interpreter, which already carries a real `pydantic`, `PyYAML`, and
`jsonschema` at `/usr/local/lib/python3.11/dist-packages` (not
network-fetched this session). `PYTHONPATH` was built from all fifteen
workspace `src/` directories (the fourteen pre-existing
services/packages plus the new `services/ai-processing-service/src`)
plus that `dist-packages` directory — the same technique every prior
pack's own report established, extended here to the fifteenth `src/`
directory. `hypothesis` remains genuinely absent from this sandbox;
`tests/contract/test_property_based.py` is the one test module that
still cannot run locally for that reason, unchanged from every prior
pack.

This pack makes no TypeScript/frontend source change beyond the
`REPOSITORY_VERSION` mirror in
`packages/typescript/epd2-types/src/version.ts` and the
`version.test.ts` assertions that check it (section 2, section 0c) —
`npm run typecheck`, ESLint, the TypeScript/frontend unit test suites,
and `next build` could not be run locally in this sandbox for the
network reason above; all of them ran for real in the final external
GitHub Actions run (section 0d) and passed.

## 2. Canon integrity

`docs/canonical/TZ-00-domain-event-canon.md` was not opened for editing
this pass and was re-verified byte-identical throughout:

```text
$ sha256sum docs/canonical/TZ-00-domain-event-canon.md
374b25fddfab88846622bf078b35c4246d8ad8c5d65bf43e6ac4e82653f74f74
```

`CANON_VERSION` remains `"0.5.0"` everywhere it is declared
(`epd2_core/version.py`, `epd2-types/version.ts`,
`docs/canonical/canon-version.json`) — canon section 19c, ADR-023, and
ADR-025 were already accepted before this implementation pass began
(see `docs/review/PACK-06-OWNER-DECISIONS.md`); this pass implements
that already-accepted text and makes no canon edit of its own.

The five binding ADRs' own `## Status` sections, read directly this
pass:

```text
ADR-021: accepted
ADR-022: accepted, with an amendment replacing the reviewer-verification
         mechanism with the narrow governance read
         (verify_role_assignment_for_action)
ADR-023: accepted, with amendments making RedactionManifest a canonical
         embedded value object and clarifying the human_review_status
         superseded semantics
ADR-024: accepted
ADR-025: accepted, with an amendment replacing the informal external-
         provider allow-list with the closed, repository-side
         LOW_RISK_EXTERNAL_PROVIDER_USE_CLASSES set
```

`REPOSITORY_VERSION` was bumped `0.5.0 → 0.6.0`
(`packages/python/epd2-core/src/epd2_core/version.py`,
`packages/typescript/epd2-types/src/version.ts`, both
version-consistency unit tests, `CHANGELOG.md`'s newest `## [0.6.0]`
entry), enforced by `scripts/verify_versions.py`, which passes:

```text
$ python3 scripts/verify_versions.py
OK: all version sources are consistent.
```

`docs/canonical/canon-version.json`'s `repository_compatibility` field
(repository-side bookkeeping, not canon-immutable content) was widened
from `">=0.1.0 <0.6.0"` to `">=0.1.0 <0.7.0"` to admit the new repository
version, mirroring how every prior pack widened this same field for its
own `REPOSITORY_VERSION` bump.

## 3. Lock files — not regenerated locally (same ceiling as every prior pack)

```text
uv.lock:            Not regenerated locally — `uv lock` requires PyPI
                     access this sandbox does not have (section 1).
package-lock.json:  Not regenerated locally — same reason, npm registry.
```

This sandbox's own local ceiling is unchanged from every prior pack's
own report and is not expected to change. No PACK-06 dependency was
added to `pyproject.toml` or `package.json` beyond what already existed
— `ai-processing-service` uses the same workspace dependency set as
every other Python service (no new third-party package).

## 4. Files added or changed this pass

**New:**

- `services/ai-processing-service/` — `pyproject.toml`, `README.md`,
  `src/epd2_ai_processing_service/{__init__.py, domain.py, application.py,
events.py, exceptions.py, storage.py, provider.py, redaction.py}`,
  `tests/{test_domain.py, test_application.py, test_storage.py}`.
- `contracts/reason-codes/pack-06.yml` — 29 entries.
- `contracts/openapi/pack-06.yaml` — 8 operations, tag
  `ai-processing-service` exclusively; documents that
  `verify_role_assignment_for_action` has no HTTP-shaped contract of its
  own (a narrow, internal, cross-pack read documented under
  `governance-service`'s own tag in `pack-05.yaml` if at all).
- `contracts/schemas/{ai-processing-record, ai-disclosure-package}.schema.json`.
- `contracts/events/ai-processing-record-payload.v1.schema.json`.
- `docs/adr/ADR-021` through `ADR-025` (five files).
- `docs/review/PACK-06-OWNER-DECISIONS.md`, `docs/handover/PACK-06-SPEC.md`,
  and this report, `docs/handover/PACK-06-REPORT.md`.
- `tests/contract/test_ct00_11_ai_human_control.py` (new — CT-00-11
  fully applicable for PACK-06, per required scope item 17).

**Modified:**

- `tests/contract/*` — `test_ct00_01_schema_validation.py` through
  `test_ct00_09_vote_linkability.py`, `test_reason_codes_registry.py`,
  and `test_openapi_contract.py` extended for PACK-06 (see section 10 for
  detail). `test_ct00_11_12_not_applicable.py` renamed to
  `test_ct00_12_emergency_stop_not_applicable.py` (CT-00-11 moved to its
  own dedicated, fully-applicable file; CT-00-12 remains not-applicable,
  extended to also name PACK-06). `test_ct00_10_rule_freeze.py` extended
  with one new, explicitly-reasoned not-applicable test for PACK-06 (its
  own module docstring explains why this pack's freeze-shaped invariants
  are better covered by its own CT-00-03 tests instead).
- `tests/repository/test_service_boundaries.py` — one E501 wrap fix on
  `ALLOWED_PACK06_GOVERNANCE_FUNCTIONS`.
- Version mirrors and required-path list: `epd2_core/version.py`,
  `epd2-types/version.ts`, `canon-version.json`, both
  `test_version.py`/`version.test.ts`, `CHANGELOG.md` (new `## [0.6.0]`
  entry), `scripts/check_repository.py` (`REQUIRED_PATHS` extended by
  every new path listed above; now 363 required paths total).
- Root `README.md` — new PACK-06 status entry, updated service count
  (thirteen → fourteen), updated repository version and documentation
  links.

No PACK-02 through PACK-05 source file was changed beyond the two
sanctioned additions above (the `test_service_boundaries.py` line-length
fix and the `CHANGELOG.md`/version-mirror updates). No Emergency/Crisis
Override, frontend/UI, or cryptographic-signing work was implemented.

## 5. Gaps found and fixed during this pass's own verification

Real gaps this sandbox's own local verification found and fixed, listed
honestly rather than omitted:

1. **Two missing parse functions.** `UnknownProcessingStatusError`/
   `UnknownHumanReviewStatusError` existed in `exceptions.py` but were
   never raised anywhere in `src/` — a genuine implementation gap
   surfaced while extending CT-00-02 for PACK-06. Fixed by adding
   `parse_processing_status`/`parse_human_review_status` to `domain.py`
   (mirroring `account-service`'s own `parse_status` precedent exactly),
   plus their own unit tests in `test_domain.py`.
2. **A test-design bug in the disclosure-package gate test.**
   `test_create_disclosure_package_requires_reviewed_output` expected
   `AIConsequentialOutputNotReviewedError`, but the record's actual state
   (never reviewed, `human_reviewer_reference is None`) always hits the
   earlier `AIHumanReviewerMissingError` branch first — the final "else"
   branch in `assert_consequential_output_reviewed` is structurally
   unreachable given the domain's own transition invariants
   (`human_reviewer_reference` is only ever set together with a terminal
   outcome transition). Fixed by correcting the test's expectation and
   documenting why in both the test docstring and the function's own
   docstring, rather than papering over it with a broader exception
   match.
3. **mypy `dict[str, object]` unpack errors** (26 errors across
   `with_processing_status`/`with_human_review_status` in `domain.py`).
   Fixed by changing the dynamically-built `changes` dict's annotation
   to `dict[str, Any]` — `object` cannot type-check against the
   dataclass's own per-field types when unpacked via
   `dataclasses.replace(self, **changes)`.
4. **mypy `"object" has no attribute ..."` errors** (~20 errors in
   `tests/test_application.py`) caused by several test helper functions
   being typed too loosely (`-> object`). Fixed by giving each helper its
   concrete return type (`app.RequestAIProcessingResult`, `UUID`,
   `AIProcessingRecord`).
5. **A reason-code registration gap.**
   `test_every_reason_code_literal_used_in_services_is_registered[pack-06]`
   failed because `AI_PROCESSING_RECORD_STATUS_CHANGED` (an
   audit-classification literal) and `ROLE_ASSIGNMENT_SCOPE_MISMATCH` (a
   cross-pack, read-only reason_code comparison literal — read, never
   raised, by `review_ai_output`) were used in `src/` but not registered
   in `pack-06.yml`. Fixed by adding both entries, following the
   established `PERMISSION_DENIED`-style cross-pack duplication
   precedent already used by `pack-03.yml`/`pack-05.yml`.
6. **A leftover uploaded archive at the repository root**
   (`epd2-civic-os-CANON-0.5.0-PACK-06-READY.zip`) was failing
   `test_no_forbidden_paths_present`. Fixed by deleting it — it was
   input material, not a repository artifact.
7. **`ALLOWED_PACK06_GOVERNANCE_FUNCTIONS` E501 line-too-long** in
   `test_service_boundaries.py`. Fixed by wrapping the frozenset literal
   across multiple lines — no logic change.
8. **`scripts/check_repository.py`'s `REQUIRED_PATHS` list initially had
   zero PACK-06 entries**, despite the check reporting "OK" (the check
   only validates presence of _listed_ paths, never completeness of the
   list itself — a pre-existing property of this script, not a defect
   introduced this pass). Fixed by adding every real PACK-06 path this
   pass actually created (five ADRs, the owner-decisions/spec/report
   docs, five contract files, and the full `services/ai-processing-service/`
   file tree) — now 363 required paths, all present.

No check was weakened, no test was deleted or loosened to make it pass,
and no field was stripped from any contract to dodge a failing assertion
— every fix above is either a genuine source/test correction or a
precedented registration/formatting fix matching an existing convention.

## 6. Cross-pack boundary (ADR-022)

`ai-processing-service` reads (never writes) exactly one
`governance-service` function,
`epd2_governance_service.application.verify_role_assignment_for_action`
— never `.domain`, never any other `.application` function, and never
duplicates Governance's own role-validity logic locally. Its
`publish_ai_disclosure` command similarly calls
`epd2_transparency_service.application.publish_ledger_entry` directly —
`ai-processing-service` never writes `PublicLedgerEntry` itself;
`transparency-service` remains the sole writer. Both directions use the
established `Any`-typed passthrough convention for foreign store
parameters (never importing the other pack's `.storage`/`.domain` for a
type annotation). An AST-based import scan
(`test_ai_processing_service_never_imports_voting_tally_delegation_account_or_identity`,
added to `tests/contract/test_ct00_09_vote_linkability.py`) confirms this
pack never imports `epd2_voting_service`, `epd2_tally_service`,
`epd2_delegation_service`, `epd2_account_service`,
`epd2_identity_service`, or `epd2_credential_service` at all — the
strict data boundary (required scope item 7) is structural, not merely a
runtime check.

## 7. Two status planes, supersession, and fail-closed human review

`processing_status` and `human_review_status` never move together
(section 0 above). `supersedes_ai_processing_record_id` is the one
shared field covering both a superseded processing attempt and a
superseded review outcome — `supersede_ai_processing_record` is the only
mechanism that ever corrects either, always via a brand-new row, never a
rewrite of the superseded row's own fields
(`test_ct00_03_forbidden_transition.py`,
`test_ai_processing_service`'s own `test_supersede_ai_processing_record`).
`assert_consequential_output_reviewed` is the fail-closed gate every
downstream disclosure/finalization step calls first — silence, timeout,
a missing reviewer, or a missing role verification never implies
approval, covered directly by the five dedicated tests in the new
`tests/contract/test_ct00_11_ai_human_control.py` (silence-never-implies-
approval, rejected-never-becomes-official, approved-becomes-official,
and the full five-step disclosure protocol proof).

## 8. Redaction, provider abstraction, and the strict data boundary

`ai-processing-service` performs redaction/provenance validation itself
(`redaction.RedactionValidator.validate`) — `prepare_input` never trusts
a caller-supplied `redaction_applied`-style flag, and an unclassified
input is rejected before any validator call runs at all. Raw input and
removed values are never stored in `RedactionManifest` — only
category-level metadata. `provider.AIModelProvider` has no callback,
tool-calling, or command-issuing parameter anywhere on its `Protocol` —
structurally incapable of mutating Civic OS, not merely restricted by
convention. `assert_external_provider_use_allowed` fail-closes an
external submission unless the use class is low-risk and the region/
retention mode are both recognized values.

## 9. Reason-code registry and contract test extension

`contracts/reason-codes/pack-06.yml` — 29 entries, independently
complete (canon-reused codes redeclared, not imported). `contracts/openapi/pack-06.yaml`
— 8 operations, single exact tag (`ai-processing-service`). Both entity
schemas and the one event-payload schema were validated against real
constructed objects via `jsonschema.validate` this pass. CT-00-01 through
CT-00-09 were extended with real PACK-06 test cases in every file (see
section 5's fixes above for the genuine gaps this surfaced); CT-00-11 is
newly, fully applicable (its own dedicated file); CT-00-10/CT-00-12 are
documented not-applicable, each with an explicitly reasoned skip.

## 10. Commands executed this pass, and results

### Final external GitHub Actions run — PASS (section 0d)

```text
✅ Status: PASS
✅ Python: 1822 passed, 3 skipped, 0 failed
✅ TypeScript: 3/3 passed
✅ Frontend tests: 2/2 passed
✅ Next.js production build: successful
✅ Prettier: passed
✅ Ruff: passed
✅ ESLint: passed
✅ mypy: passed
✅ Required paths: all 363 present
✅ Forbidden files: none
```

This is the authoritative, externally-confirmed result for the
candidate this report closes out. `REPOSITORY_VERSION` (`0.6.0`),
`CANON_VERSION` (`0.5.0`), and the canon checksum (section 2) are
unchanged from every local run below.

### Revision 4 re-verification (after the section 0c TypeScript version-test fix)

```text
✅ /opt/node22/bin/prettier --check .
   → Checking formatting...
     All matched files use Prettier code style!

✅ /root/.local/bin/ruff format --check .
   → 173 files already formatted

✅ /root/.local/bin/ruff check .
   → All checks passed!

✅ python3 scripts/check_repository.py
   → OK: all 363 required paths are present.

✅ python3 scripts/check_forbidden_files.py
   → OK: no forbidden paths found.

✅ python3 scripts/verify_versions.py
   → OK: all version sources are consistent.

✅ sha256sum docs/canonical/TZ-00-domain-event-canon.md
   374b25fddfab88846622bf078b35c4246d8ad8c5d65bf43e6ac4e82653f74f74
   (unchanged, section 2)

✅ mypy — all fifteen scoped Python groups
   → Success: no issues found, zero errors, across every group

✅ PYTHONPATH=<all 15 src/ dirs>:<system python3 dist-packages> pytest -q
   → 1815 passed, 4 skipped, 0 failed — identical to revision 3

✅ Manual Node `node:test` run of version.test.ts's logic against real
   version.ts values (tsx unavailable, section 0c)
   → 3/3 passed, including the previously-failing skeleton-version test

❌ npm test --workspace packages/typescript/epd2-types
   → could not run in this sandbox (tsx not installable, section 1/0c)
```

### Revision 3 re-verification (after the section 0b CHANGELOG.md fix)

```text
✅ /opt/node22/bin/prettier --write CHANGELOG.md
   → CHANGELOG.md 192ms (unchanged)

✅ /opt/node22/bin/prettier --check CHANGELOG.md
   → Checking formatting...
     All matched files use Prettier code style!

✅ npm run format:check   (full tree)
   → Checking formatting...
     All matched files use Prettier code style!

✅ python3 scripts/check_repository.py
   → OK: all 363 required paths are present.

✅ python3 scripts/verify_versions.py
   → OK: all version sources are consistent.

✅ sha256sum docs/canonical/TZ-00-domain-event-canon.md
   374b25fddfab88846622bf078b35c4246d8ad8c5d65bf43e6ac4e82653f74f74
   (unchanged, section 2)

✅ PYTHONPATH=<all 15 src/ dirs>:<system python3 dist-packages> pytest -q
   → 1815 passed, 4 skipped, 0 failed — identical to revision 2
```

### Revision 2 re-verification (after the section 0a Prettier fix)

```text
✅ npm run format   (the fix)
   → prettier --write . — exactly the 6 flagged files reformatted,
     every other tracked file reported "(unchanged)"

✅ npm run format:check   (after the fix)
   → Checking formatting...
     All matched files use Prettier code style!

✅ /root/.local/bin/ruff format --check .
   → 173 files already formatted

✅ /root/.local/bin/ruff check .
   → All checks passed!

✅ python3 scripts/check_repository.py
   → OK: all 363 required paths are present.

✅ python3 scripts/check_forbidden_files.py
   → OK: no forbidden paths found.

✅ python3 scripts/verify_versions.py
   → OK: all version sources are consistent.

✅ sha256sum docs/canonical/TZ-00-domain-event-canon.md
   374b25fddfab88846622bf078b35c4246d8ad8c5d65bf43e6ac4e82653f74f74
   (unchanged, section 2)

✅ mypy — all sixteen scoped groups
   → Success: no issues found, zero errors, across every group

✅ PYTHONPATH=<all 15 src/ dirs>:<system python3 dist-packages> pytest -q
   → 1815 passed, 4 skipped, 0 failed — identical to revision 1
```

Every number above is identical to revision 1 (section below) except
`prettier --check .`, which is now clean where it previously flagged
six files — confirming the fix was pure reformatting with no other
effect on the repository.

### Revision 1 (original local verification)

```text
✅ sha256sum docs/canonical/TZ-00-domain-event-canon.md
   374b25fddfab88846622bf078b35c4246d8ad8c5d65bf43e6ac4e82653f74f74
   (unchanged throughout, section 2)

✅ python3 scripts/verify_versions.py
   → OK: all version sources are consistent.

✅ python3 scripts/check_forbidden_files.py
   → OK: no forbidden paths found.

✅ python3 scripts/check_repository.py
   → OK: all 363 required paths are present.

✅ ruff check .
   → All checks passed!

✅ ruff format --check .
   → 173 files already formatted

✅ mypy — all sixteen scoped groups (fifteen prior + services/ai-processing-service)
   → Success: no issues found, zero errors, across every group

✅ PYTHONPATH=<all 15 src/ dirs>:<system python3 dist-packages> pytest -q
   → 1815 passed, 4 skipped, 0 failed
     (4 skips: test_property_based.py — hypothesis genuinely unavailable,
     section 1 — plus the three genuine CT-00-10/CT-00-11/CT-00-12
     not-applicable-in-earlier-packs markers this and prior reports
     document; zero unexplained skips, zero failures)

✅ JSON Schema validation (both entity + the event payload schema,
   against real constructed objects via jsonschema.validate)
   → ALL SCHEMAS VALID

❌ uv lock / uv sync / npm install
   → blocked, section 1/3 (network egress to
     pypi.org/files.pythonhosted.org/registry.npmjs.org returns 403,
     reconfirmed this pass)

➖ Not run this pass in this sandbox (same network restriction, section
   1): npm run typecheck (both workspaces), npm run lint (frontend
   ESLint), npm run test (both workspaces), next build. All four ran for
   real in the final external GitHub Actions run (section 0d) and
   passed: TypeScript 3/3, frontend tests 2/2, Next.js production build
   successful, ESLint clean.
```

## 11. Readiness conclusion

```text
PACK-06 PASS (external GitHub Actions confirmed)
```

**PACK-06 PASS**, confirmed by a complete external GitHub Actions run
with real network access (section 0d): 1822 Python tests passed, 3
skipped (genuine CT-00-10/CT-00-12 not-applicable-in-earlier-packs
markers — CT-00-11 is no longer among them, now fully applicable and
passing for PACK-06 for the first time, section 0), TypeScript tests
passed (3/3), frontend tests passed (2/2), a successful Next.js
production build, and Prettier, Ruff, ESLint, and mypy all clean, with
all 363 required paths present and no forbidden files. Every check this
sandbox can itself run independently confirms the same picture locally:
required structure (363 of 363 paths), no forbidden paths, all version
sources consistent, Ruff format and lint clean, `prettier --check .`
clean across the full tree, mypy clean across all fifteen scoped Python
groups with zero errors and zero blanket suppressions, and 1815 passing
Python tests with 0 failures and exactly 4 genuine, individually-
documented skips locally (1 hypothesis-unavailable in this sandbox only
— it ran for real externally, contributing to the 1822/3 external
numbers above — plus the 3 CT-00-10/12 not-applicable markers).
`docs/canonical/TZ-00-domain-event-canon.md` remains byte-identical
throughout (section 2) and `CANON_VERSION` is unchanged at `0.5.0` —
this pass implements already-accepted canon text and makes no canon
edit of its own. `REPOSITORY_VERSION` moved `0.5.0 → 0.6.0`, enforced by
`scripts/verify_versions.py`.

Three real gaps were found and fixed en route to this PASS — a
six-file Prettier formatting gap (revision 2, section 0a), a Markdown
authoring defect in `CHANGELOG.md` (revision 3, section 0b), and a
stale hardcoded TypeScript version-test literal (revision 4, section
0c) — each touching exactly the one file needed and no implementation
logic, schema, canon, or ADR content. No check was weakened, no empty
file was written to satisfy a path requirement, no reason code was
hidden, no legitimate field was stripped from this service's own
contract to make a test pass, and no data-boundary or fail-closed claim
is made without the automated test that backs it (sections 6, 7, 8, 9).
Unlike this report's own revision-2 draft, `PACK-06 PASS` is no longer a
local-only claim — it is now confirmed end to end by a real external
GitHub Actions run with genuine network access, matching PACK-02
through PACK-05's own final, externally-confirmed revisions.
