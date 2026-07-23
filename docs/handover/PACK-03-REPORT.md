# CLAUDE-PACK-03 — Participation and Decision Kernel: Handover Report

**Revision 4 — PASS.** Revisions 1 through 3 each closed a real,
sandbox-invisible mypy bug found by successive external GitHub Actions
verification runs (a generic-exception-typed attribute access, revision
2 section 0a; a redundant sort key unsafe under real pytest stubs,
revision 3 section 0b, found in ten call sites across four services). A
subsequent external GitHub Actions run against the revision-3 candidate
archive, with genuine network access, completed the full pipeline
successfully end to end (section 0c): 1525 Python tests passed, 2
skipped (the same genuine CT-00-11/12 not-applicable markers this report
has always documented), TypeScript 3/3, frontend tests 2/2, a successful
Next.js production build, and Ruff, Prettier, ESLint, and mypy all
clean, with all 277 required paths present and no forbidden files. No
source code, test, or check was changed to reach this result — this
revision is a documentation-only update recording a genuine,
already-achieved PASS.

```text
PACK-03 PASS
```

## 0a. External verification finding and fix (revision 2)

External verification on GitHub Actions (running against the revision-1
candidate archive) reported one real mypy error, with everything before
it in the pipeline (Ruff format, Prettier, Ruff lint, frontend ESLint,
mypy for `epd2-core`/`scripts`/`tests/repository`/`conftest.py`) already
passing:

```text
tests/contract/test_ct00_02_unknown_status.py:146: error: "Exception"
has no attribute "reason_code"  [attr-defined]
```

Root cause: `test_pack03_unknown_enum_value_is_rejected` is one
parametrized test covering all 18 PACK-03 status/value enums'
`Unknown*Error` exception classes across six services — those classes
share no common concrete base beyond `ValueError`, so the test parameter
`expected_exception` is typed as the generic `type[Exception]`. Passing
that generic type into `pytest.raises(expected_exception)` makes
`excinfo.value` resolve to plain `Exception`, which has no
`reason_code` attribute — only the concrete `Unknown*Error` subclasses
do. This is genuinely invisible in this sandbox: the project's own mypy
config carries `ignore_missing_imports = true` for `pytest`/`_pytest.*`
(documented in `pyproject.toml`, originally added because this sandbox's
standalone mypy tool has no `pytest` installed to find real stubs for),
so locally `pytest.raises(...)` resolves to `Any` and the attribute
access never gets checked at all — the same category of "invisible
locally, real once genuine stubs are installed" gap
`docs/handover/PACK-02-REPORT.md` section 0d already documented for
Hypothesis.

Fixed at the source, with no blanket `# type: ignore` and no relaxed
mypy setting: added a `@runtime_checkable` `Protocol` (`_ReasonCodedError`,
declaring `reason_code: str`) to
`tests/contract/test_ct00_02_unknown_status.py`, and narrowed the caught
exception against it before accessing the attribute:

```python
error = excinfo.value
assert isinstance(error, _ReasonCodedError)
assert error.reason_code == "VALIDATION_UNKNOWN_STATUS"
```

This is option 2 of the two the pack's own instruction allowed ("narrow
the caught exception before accessing `reason_code`") — option 1 (naming
one concrete exception type per case) was not available without
introducing a new shared exception base class across eleven services'
`exceptions.py` modules, a materially larger and riskier change than this
test file needed. The `isinstance()` check is a genuine runtime
assertion, not a no-op: `@runtime_checkable` protocols check for the
declared attribute's actual presence on the instance
(`hasattr`-equivalent, confirmed directly this pass with a throwaway
script — a plain `ValueError` without `reason_code` correctly fails the
isinstance check), so if any of the 18 `Unknown*Error` classes ever
stopped declaring `reason_code`, this test would fail loudly rather than
silently pass. Mypy narrows `error`'s static type to a synthesized
intersection of `Exception` and `_ReasonCodedError` after the assert
(confirmed directly this pass via `reveal_type`), which is exactly what
makes the following `.reason_code` access type-check. The assertion this
test makes — that an unknown status value produces
`reason_code == "VALIDATION_UNKNOWN_STATUS"` — is unchanged and still
genuinely executed for all 18 cases.

`.github/workflows/verify-and-package.yml` was not touched — the fix is
entirely inside the one test file that had the bug. This sandbox still
cannot install real `pytest`/`_pytest.*` stubs to reproduce CI's exact
failure locally (same root cause as the bug itself), so this fix was
verified as far as this environment allows: `mypy tests/contract` still
reports "Success: no issues found in 18 source files" (unchanged — this
sandbox's config never saw the error in the first place), and a
standalone, throwaway repro file using a hand-written `Exception`-typed
variable (not going through `pytest.raises`, to sidestep the
`ignore_missing_imports` masking) confirmed both halves directly:
accessing `.reason_code` on a bare `Exception`-typed variable fails
`attr-defined` exactly as CI reported, and the same access after
`assert isinstance(error, _ReasonCodedError)` type-checks cleanly with
mypy narrowing to the intersection type. Full confirmation that the real
CI error is gone requires the next external GitHub Actions run.

## 0b. External verification finding and fix (revision 3)

A subsequent external GitHub Actions run — against the revision-2
candidate archive — passed everything through the section 0a fix (Ruff
format, Prettier, Ruff lint, frontend ESLint, mypy for
`epd2-core`/`scripts`/`tests/repository`/`conftest.py`, mypy for
`audit-core`), then found four real mypy errors, all in one file:

```text
services/initiative-service/tests/test_domain.py:133: error: Value of
type "object" is not indexable  [index]
services/initiative-service/tests/test_domain.py:274: error: Value of
type "object" is not indexable  [index]
services/initiative-service/tests/test_domain.py:330: error: Value of
type "object" is not indexable  [index]
services/initiative-service/tests/test_domain.py:375: error: Value of
type "object" is not indexable  [index]
```

Root cause: all four flagged lines were `@pytest.mark.parametrize`
decorators of the form
`sorted(ALLOWED_*_TRANSITIONS, key=lambda p: (p[0], p[1]))` — one per
owned entity (`Initiative`, `SupportRecord`, `Amendment`, `SourceRecord`).
Reproduced directly this pass with a hand-written stand-in for pytest's
real `parametrize` signature (`argvalues: Iterable[Sequence[object] |
object]`, closely matching the real stub, in a throwaway file, since this
sandbox's own mypy config masks real `pytest` via `ignore_missing_imports`
exactly as section 0a described): when `sorted(...)`'s result is passed
as an argument into a call whose parameter is typed with that broad
`Sequence[object] | object` element type, mypy's bidirectional inference
pushes that expected type down into the lambda, and the lambda parameter
`p` types as `object` instead of the correct
`tuple[SomeStatus, SomeStatus]` inferred from `ALLOWED_*_TRANSITIONS`
itself — so `p[0]`/`p[1]` fail `object` is not indexable. Confirmed with
a second throwaway repro that removing the `key=` argument entirely
avoids the broken inference path completely and type-checks cleanly.

The `key=lambda p: (p[0], p[1])` was always a no-op: for a 2-tuple `p`,
`(p[0], p[1])` is exactly `p` itself, so this key function does not
change the sort order at all — `sorted(x, key=lambda p: (p[0], p[1]))`
and `sorted(x)` are the same operation whenever `x`'s elements are
themselves comparable 2-tuples (true here: every `ALLOWED_*_TRANSITIONS`
is declared as `frozenset[tuple[SomeStatus, SomeStatus]]`, and every
`SomeStatus` is a `StrEnum`, which supports ordering). Fixed by deleting
the redundant `key=` argument at all four flagged lines, leaving
`sorted(ALLOWED_*_TRANSITIONS)` — not a cast, not a blanket ignore, and
not a behavior change: confirmed programmatically this pass, for each of
the four affected sets, that `sorted(x, key=lambda p: (p[0], p[1])) ==
sorted(x)` (`True` in all four cases, with the documented edge counts:
28 initiative, 2 support, 11 amendment, 13 source-verification
transitions), so the parametrized test cases and their order are
byte-for-byte unchanged — this satisfies the pack's requirement to
preserve existing assertions and test meaning exactly, while removing
the operation mypy correctly flagged as unsafe under real pytest stubs.

While fixing this, the identical `sorted(ALLOWED_*, key=lambda p: (p[0],
p[1]))` pattern was found, unprompted by the CI report, in four more
places across three other PACK-03 services —
`services/voting-service/tests/test_domain.py` (4 occurrences: `Ballot`,
`BallotOption`, `VoteEnvelope`, `VoteReceipt`),
`services/delegation-service/tests/test_domain.py` (1: `Delegation`),
and `services/tally-service/tests/test_domain.py` (1: `Tally`
verification status) — the same sub-agent-authored pattern, copied
across services when each service's own transition-table test was
written. These had not yet been reached by CI's per-service mypy
ordering, but are the exact same latent bug and would have failed the
next run regardless. Fixed identically (redundant `key=` removed) and
verified programmatically the same way: `sorted(x, key=lambda p: (p[0],
p[1])) == sorted(x)` for all six additional sets (`True` in every case).
Ten occurrences fixed in total this revision, not four — closing this
whole bug class in one pass rather than trickling in one CI round at a
time.

`.github/workflows/verify-and-package.yml` was not touched. This
sandbox's own `mypy services/initiative-service` (and the five other
affected services) reported "Success: no issues found" both before and
after this fix — the bug is invisible here for the same
`ignore_missing_imports`-on-`pytest` reason as section 0a, which is
exactly why the two throwaway repro files above (using a hand-written
stand-in for pytest's real signature, not a real pytest import) were used
to reproduce and confirm the fix locally as far as this environment
allows. The full local verification suite (section 6) was re-run clean
after this fix: 1518 passed, 3 skipped, 0 failed — unchanged from
revision 2, confirming zero test-behavior change.

## 0c. External verification: PASS (revision 4)

A subsequent external GitHub Actions run — against the revision-3
candidate archive (`epd2-civic-os-PACK-03-final-candidate-v3.zip`), with
genuine PyPI/npm network access — completed the full `make verify`
pipeline successfully:

```text
Status: PASS
Python:     1525 passed, 2 skipped, 0 failed
TypeScript: 3/3 passed
Frontend:   2/2 passed
Next.js production build: successful
Ruff, Prettier, ESLint, mypy: clean
scripts/check_repository.py: all 277 required paths present
scripts/check_forbidden_files.py: no forbidden paths found
```

These results were reported directly by the project owner after running
the real workflow, not independently inspected by this sandbox against a
raw returned log or tree this round (unlike revision 4's PACK-02
counterpart, section 3 of that report, where a returned artifact was
extracted and diffed directly) — this sandbox still has no path to a
returned CI artifact or genuine network access itself (section 1
below is unchanged). The reported numbers are, however, independently
_reconcilable_ against this sandbox's own last local run rather than
accepted blind: revision 3's local pytest run reported `1518 passed, 3
skipped` — 1 skip for `tests/contract/test_property_based.py`
(`pytest.importorskip("hypothesis")`, a single module-level skip outcome
since `hypothesis` cannot be installed here) and 2 for the genuine
CT-00-11/12 not-applicable markers. That file contains exactly 7 test
functions (confirmed by inspection: `test_no_forbidden_field_name_...`,
`test_credential_expiry_boundary_is_strict`,
`test_duplicate_audit_event_id_with_identical_content_is_always_idempotent`,
`test_duplicate_audit_event_id_with_different_action_always_conflicts`,
`test_reason_code_strings_are_stable_literals_not_derived`,
`test_canonical_dumps_is_independent_of_input_key_order`, and one more) —
so a real `hypothesis` install turning that one collection-level skip
into 7 real passes predicts exactly `1518 + 7 = 1525` passed and
`3 - 1 = 2` skipped, matching the reported CI numbers exactly. This
arithmetic match is meaningful corroboration, not proof of an
independent log inspection, and this report says so plainly rather than
implying more certainty than this sandbox actually has.

The workflow's own lock-file steps (`.github/workflows/verify-and-package.yml`
lines "Generate Python lock file: uv lock" and "Generate Node lock file
and install dependencies: npm install") always regenerate `uv.lock` and
`package-lock.json` fresh from the current `pyproject.toml`/`package.json`
on every run — they never read or depend on whatever lock file happens
to be committed in the tree. This means the sandbox's inability to run
`uv lock`/`npm install` locally (section 1, unchanged from every prior
revision) was always a _local verification ceiling_, never a _CI
blocker_ — the successful CI run above is exactly the confirmation of
that. This working tree's own committed `uv.lock`/`package-lock.json`
remain the same PACK-02-era files they were before this pack's
implementation (7 workspace members, not 12) — genuinely stale, but
inconsequential to this PASS, since CI never reads them and no PACK-03
service depends on their content. They were left untouched this revision
rather than hand-edited to look regenerated, since a hand-written lock
file would not be a real one (the same principle
`docs/handover/PACK-02-REPORT.md` section 3 states for its own,
now-closed, identical-in-kind gap).

## 0. What CLAUDE-PACK-03 adds

Six new Python services, each an independent `uv` workspace member with
its own `pyproject.toml`, `src/`, and `tests/`, implementing the 18
in-scope canonical entities for participation and decision-making:

- `services/initiative-service` (`epd2_initiative_service`) — owns
  `Initiative`, `InitiativeVersion`, `SupportRecord`, `Amendment`,
  `SourceRecord`.
- `services/deliberation-service` (`epd2_deliberation_service`) — owns
  `Discussion`, `Contribution`.
- `services/moderation-service` (`epd2_moderation_service`) — owns
  `ModerationCase`, `ModerationDecision`, `Appeal`.
- `services/voting-service` (`epd2_voting_service`) — owns `Ballot`,
  `BallotOption`, `VoteEnvelope`, `VoteReceipt`.
- `services/tally-service` (`epd2_tally_service`) — owns `Tally`,
  `ResultPublication`.
- `services/delegation-service` (`epd2_delegation_service`) — owns
  `Delegation`, `DelegationSnapshot`.

Plus: five accepted ADRs already present in this tree
(`docs/adr/ADR-005-pack-03-service-decomposition.md`,
`ADR-006-pack-03-reason-code-additions.md`,
`ADR-008-pack-03-pack-02-integration-boundary.md`,
`ADR-009-voting-delegation-quorum-defaults.md`,
`ADR-010-ballot-challenge-window-canon-addition.md`), a separate 70-entry
reason-code registry (`contracts/reason-codes/pack-03.yml`, ADR-006
Option B — never merged with `pack-02.yml`), 18 entity JSON Schemas and
18 event-payload JSON Schemas in `contracts/schemas/` /
`contracts/events/`, a 71-path OpenAPI contract
(`contracts/openapi/pack-03.yaml`), the CT-00-01 through CT-00-10
contract-test suite extended to cover all six services (CT-00-11/12
remain documented not-applicable, unchanged from PACK-02, since neither
`AIProcessingRecord` nor `EmergencyAction` is in scope for PACK-03
either), and a repository-wide structural boundary test
(`tests/repository/test_service_boundaries.py`) enforcing ADR-008's
narrow, `.application`-only PACK-03 → PACK-02 read edge with no
PACK-02 → PACK-03 dependency and no PACK-03 ↔ PACK-03 cross-service
imports.

## 1. Environment and network status

```text
$ python3 --version
Python 3.11.15
$ python3.12 --version
Python 3.12.3
```

This sandbox's network egress blocks `pypi.org` / `files.pythonhosted.org`
/ `registry.npmjs.org` (`403`), reconfirmed directly this pass:

```text
$ curl -sS -o /dev/null -w "%{http_code}\n" https://registry.npmjs.org/
403
$ curl -sS -o /dev/null -w "%{http_code}\n" https://pypi.org/
403
```

No standalone `uv`-synced project venv exists in this sandbox for the
same reason. Local verification instead used the pre-existing standalone
tool binaries at `/root/.local/share/uv/tools/{pytest,mypy}/bin/` and
`/root/.local/bin/ruff`, plus the system `python3`/`python3.12`
interpreters (each with a real, already-installed `PyYAML` and
`jsonschema` — not network-fetched this session) and a system-installed
Prettier 3.8.1 (found available outside the project's own blocked
`npm install` path, the same discovery `docs/handover/PACK-02-REPORT.md`
section 0c made). `node_modules` does not exist in this tree; PACK-03
makes no frontend/TypeScript source change (only the `REPOSITORY_VERSION`
mirror in `packages/typescript/epd2-types/src/version.ts`, section 2), so
`npm run typecheck`, ESLint, the TypeScript unit tests, and `next build`
were not run locally — consistent with every one of PACK-02's early
revisions, before GitHub Actions' real network access closed that gap.

One improvement over PACK-02's local-verification ceiling: pointing
`PYTHONPATH` at the system `python3`'s `dist-packages` directory
(`/usr/local/lib/python3.11/dist-packages`, which already carries a real
`PyYAML` and `jsonschema`) in addition to all twelve workspace `src/`
directories let the standalone `pytest` tool run every YAML/JSON-Schema-
dependent test for real this pass, instead of `pytest.importorskip`-ing
them. The only test that still cannot run locally is
`tests/contract/test_property_based.py` (needs `hypothesis`, which is
genuinely absent from this sandbox and not present in any local cache —
confirmed by `find /` turning up no installable wheel or importable
module anywhere on the filesystem).

## 2. Canon integrity

`docs/canonical/TZ-00-domain-event-canon.md` was not opened for editing
this pass and was re-verified byte-identical both before and after every
change in this pass (prettier run, reason-code generation, mypy/ruff
fixes):

```text
sha256(docs/canonical/TZ-00-domain-event-canon.md) =
  5ed52c3a6a94e821323616ac369595fd364a71115cf5c1c6763d8edb51a6044a
```

This matches the value fixed at the start of this task and must never
change. `CANON_VERSION` remains `"0.2.0"` everywhere it is declared
(`epd2_core/version.py`, `epd2-types/version.ts`,
`docs/canonical/canon-version.json`) — PACK-03 adds one narrow,
ADR-010-accepted canon addition (`Ballot.challenge_window_hours`,
`ResultPublication.challenge_deadline_at`) but does not bump
`CANON_VERSION` itself, per ADR-010's own framing of this as an additive,
backward-compatible field addition rather than a new canon version.

`REPOSITORY_VERSION` was bumped `0.2.0` → `0.3.0`
(`packages/python/epd2-core/src/epd2_core/version.py`,
`packages/typescript/epd2-types/src/version.ts`, both tests' expected
values, `CHANGELOG.md`'s newest entry), enforced by
`scripts/verify_versions.py`, which passes.
`docs/canonical/canon-version.json`'s `repository_compatibility` field
(repository-side bookkeeping, not canon-immutable content) was widened
from `">=0.1.0 <0.3.0"` to `">=0.1.0 <0.4.0"` to admit the new repository
version.

## 3. Lock files — closed (revision 4)

```text
uv.lock:            Regenerated fresh by the external GitHub Actions
                     run's own "Generate Python lock file: uv lock" step
                     (workflow line 34) — this step always runs `uv
                     lock` from the current `pyproject.toml` regardless
                     of what is committed, so it produced a genuine
                     lock covering all 12 workspace members
                     (5 PACK-02 + epd2-core + 6 PACK-03 services) and
                     resolved successfully with real PyPI access.
package-lock.json:  Regenerated fresh by the same run's "Generate Node
                     lock file and install dependencies: npm install"
                     step (workflow line 40) — PACK-03 added no npm
                     dependency, so this step reconfirmed the existing
                     dependency set resolves cleanly.
```

This sandbox never had a path to run either step itself (section 1:
network egress to pypi.org/files.pythonhosted.org/registry.npmjs.org is
still blocked here, unchanged), and revisions 1 through 3 of this report
were explicit that this was an open gap under this pack's own
instruction not to mark PASS while it remained true. It is no longer
true: the external GitHub Actions run in section 0c completed both
lock-generation steps and the full `make verify` pipeline that depends
on them successfully. This working tree's own committed
`uv.lock`/`package-lock.json` were left exactly as they were (still
reflecting only PACK-02's 5 services, section 0c) — not hand-edited to
look regenerated, since a hand-written lock file would not be a real
one, and not necessary for this PASS, since (as section 0c explains in
full) the workflow's lock-generation steps never read the committed
files in the first place; they always generate fresh from
`pyproject.toml`/`package.json`.

## 4. Files added or changed this pass

New:

- `services/initiative-service/`, `services/deliberation-service/`,
  `services/moderation-service/`, `services/voting-service/`,
  `services/tally-service/`, `services/delegation-service/` — full
  `src/`, `tests/`, `pyproject.toml`, `README.md` each.
- `contracts/reason-codes/pack-03.yml` (70 entries).
- `contracts/schemas/*.json` (18 new PACK-03 entity schemas),
  `contracts/events/*.json` (18 new PACK-03 event-payload schemas),
  `contracts/openapi/pack-03.yaml` (71 paths).
- `tests/contract/test_ct00_*.py`, `test_state_transitions.py` — extended
  in place to cover all eleven PACK-02+PACK-03 services (CT-00-01
  through CT-00-10); `test_ct00_11_12_not_applicable.py` updated with
  PACK-03-scoped justification text.
- `tests/repository/test_service_boundaries.py` — rewritten (see
  section 5) to enforce the ADR-008 edge at the dotted-module-path
  level, not just the root-package level.
- `docs/handover/PACK-03-REPORT.md` — this report.

Changed:

- `services/eligibility-service/src/epd2_eligibility_service/application.py`
  — added `get_eligibility_decision` and `get_eligibility_snapshot`, two
  plain, unaudited read functions under ADR-008's narrow
  PACK-03 → PACK-02 `.application`-only edge (with matching tests and a
  new README section).
- Root `pyproject.toml` — `[project.dependencies]`,
  `[tool.uv.workspace].members` (now 12), `[tool.uv.sources]`,
  `[tool.ruff].src`, `[tool.ruff.lint.isort].known-first-party`,
  `[tool.mypy].mypy_path`, `[tool.pytest.ini_options].testpaths` — all
  extended for the six new services.
- `Makefile` — `typecheck` target extended with one scoped
  `mypy services/<name>` line per new service (same one-invocation-per-
  non-colliding-basename-group pattern PACK-02 established, section 5 of
  that report).
- `scripts/check_repository.py` — `REQUIRED_PATHS` extended with all new
  ADR, contract, schema, and per-service paths (277 total, all present —
  section 6).
- `packages/python/epd2-core/src/epd2_core/version.py`,
  `packages/typescript/epd2-types/src/version.ts` and their tests,
  `docs/canonical/canon-version.json`, `CHANGELOG.md` — version bump,
  section 2.
- 14 files reformatted with a real Prettier binary this pass (content
  unchanged, whitespace/formatting only): `CHANGELOG.md`, 5
  `contracts/events/*.v1.schema.json` PACK-03 files,
  `contracts/openapi/pack-03.yaml`, `contracts/reason-codes/pack-03.yml`,
  and 6 PACK-03 service `README.md` files
  (`delegation-service`, `deliberation-service`, `initiative-service`,
  `moderation-service`, `tally-service`, `voting-service`).
  `docs/canonical/TZ-00-domain-event-canon.md` was not among them and its
  SHA-256 is unchanged (section 2).

Not changed: `docs/canonical/TZ-00-domain-event-canon.md` (byte-identical,
section 2); `package.json` / `package-lock.json` (no npm-side change,
section 3); `frontend/web-shell/`; any of the five PACK-02 services'
`src/` (only `eligibility-service/application.py` gained the two new
read functions above — no existing PACK-02 behavior was altered).

Changed in revision 2 (section 0a):

- `tests/contract/test_ct00_02_unknown_status.py` — added a
  `@runtime_checkable` `Protocol` (`_ReasonCodedError`) and narrowed
  `test_pack03_unknown_enum_value_is_rejected`'s caught exception against
  it via `isinstance()` before accessing `.reason_code`, fixing the one
  real mypy error external GitHub Actions verification found.
- `docs/handover/PACK-03-REPORT.md` — this revision.

Changed in revision 3 (section 0b):

- `services/initiative-service/tests/test_domain.py` (4 sites),
  `services/voting-service/tests/test_domain.py` (4 sites),
  `services/delegation-service/tests/test_domain.py` (1 site),
  `services/tally-service/tests/test_domain.py` (1 site) — removed the
  redundant, no-op `key=lambda p: (p[0], p[1])` argument from each
  `sorted(ALLOWED_*_TRANSITIONS, ...)` call feeding a
  `@pytest.mark.parametrize` decorator, fixing the four real mypy errors
  external GitHub Actions verification found (plus six identical latent
  occurrences found while fixing them, section 0b).
- `docs/handover/PACK-03-REPORT.md` — this revision.

Changed in revision 4 (this revision, sections 0c/3/11):

- `docs/handover/PACK-03-REPORT.md` — rewritten from local-PASS/pending
  to PASS: header, section 0c (external verification results), section 3
  (lock-file gap closed), section 11 (conclusion changed to PACK-03
  PASS). No source code, test, or check was changed as part of this
  revision.
- `README.md` — status section updated to include PACK-03 PASS,
  the six new services, and the current canon/repository version (it had
  fallen behind during implementation and still described only PACK-01/
  PACK-02, canon `0.1.0`, and an empty `services/` directory — fixed as
  part of this closeout, not merely for the PASS marker).
- `CHANGELOG.md` — the existing `[0.3.0]` entry's description of what
  PACK-03 adds is unchanged; a short verification-status line was added
  recording the external PASS.

## 5. Gaps found and fixed during this pass's own verification

Recorded here in full, per this pack's demand for honest verification,
rather than folded silently into the file list above:

1. **The reason-code registry test originally scanned all eleven
   services against only `pack-02.yml`.** `tests/contract/test_reason_codes_registry.py`
   pre-existed this pass scoped to PACK-02's five services; once PACK-03's
   six services landed in `services/`, a naive extension would have
   scanned them against the wrong registry. Fixed by parametrizing the
   test over `(pack_name, registry_path, service_dir_names,
minimum_size)` so PACK-02 services check against `pack-02.yml` and
   PACK-03 services check against `pack-03.yml` independently — each
   pack's registry remains a complete, standalone source of truth for
   its own services, per ADR-006 Option B.
2. **The structural boundary test needed a finer edge than "which
   package did you import."** PACK-02's own
   `tests/repository/test_service_boundaries.py` checked root package
   names only, which is too coarse for ADR-008: PACK-03 services are
   allowed to import specific `.application`-scoped functions from
   specific PACK-02 services, but never their `.storage` or `.domain`
   modules, and never each other. Fixed by adding
   `_imported_module_paths()` (full dotted-path AST inspection, not just
   root-package names) alongside the existing `_imported_roots()`, and
   five explicit test functions covering both PACK-02's own one-way
   dependency rule and every new PACK-03 edge — all five pass against
   the real codebase.
3. **Sub-agent-authored PACK-03 contract test extensions repeatedly put
   new imports mid-file instead of at the top**, producing 119 Ruff
   `E402` errors across ten files. Fixed file-by-file (manual `Edit` for
   `test_state_transitions.py`; a small one-off AST-based script,
   deleted after use, for the other eight `test_ct00_*.py` files),
   followed by `ruff check . --fix` for import ordering.
4. **mypy strict mode surfaced twelve real, previously-unchecked errors**
   once the new contract-test and deliberation-service test helpers were
   type-checked for real: missing parameter annotations
   (`test_ct00_02/05/06_*.py`), a `dict[str, object]`-typed helper
   returning `Any` where `dict[str, object]` was declared
   (`test_ct00_08_identity_leakage.py`), a `Union[...]` attribute access
   needing per-branch `# type: ignore` instead of one blanket comment
   (`test_state_transitions.py`), and — the largest of these — two
   deliberation-service test helpers (`_setup_contribution`,
   `_make_contribution` in both `test_domain.py` and `test_storage.py`)
   whose `**overrides: object` splat pattern left `content`/
   `contribution_type` typed as bare `object` when passed into
   `compute_contribution_content_hash(content: str, contribution_type:
ContributionType)`. Fixed by narrowing with explicit
   `isinstance(...)` assertions before use (mirroring the existing
   `_setup_contribution` return-type fix already applied to
   `test_application.py`) rather than adding another blanket
   `# type: ignore`; this also resolved four stale, now-`unused-ignore`
   comments the strict `warn_unused_ignores = true` setting was
   correctly flagging as errors in their own right. All twelve fixed for
   real; none suppressed with a bare ignore.
5. **Prettier had never actually been run against this pass's new
   files.** Running the system Prettier 3.8.1 binary (available outside
   the project's own network-blocked `npm install` path — same discovery
   PACK-02 made in its own revision 3) found 14 genuinely
   non-Prettier-compliant files (section 4). Fixed with `prettier
--write .`; canon checksum reconfirmed byte-identical before and
   after (section 2).

## 6. Commands executed this pass, and results

### Revision 4: external GitHub Actions verification — PASS (final, source of truth)

Run against the revision-3 candidate archive
(`epd2-civic-os-PACK-03-final-candidate-v3.zip`), with genuine PyPI/npm
network access. Results as reported to this report's author by the
project owner (see section 0c for the full reconciliation against this
sandbox's own last local run):

```text
✅ VERIFICATION-RESULT.md
   → Status: PASS

✅ uv lock / uv sync --all-groups --frozen
   → generated a genuine uv.lock covering all 12 workspace members and
     installed from it (section 0c)

✅ npm install
   → generated a genuine package-lock.json and installed from it

✅ scripts/check_repository.py
   → OK: all 277 required paths are present.

✅ scripts/check_forbidden_files.py
   → OK: no forbidden paths found.

✅ ruff format --check . / ruff check .
   → clean

✅ prettier --check .
   → clean

✅ eslint .
   → clean

✅ mypy — all thirteen scoped groups
   → clean

✅ npm run typecheck — both TypeScript workspaces
   → clean

✅ pytest -q
   → 1525 passed, 2 skipped, 0 failed
     (2 skips: the same genuine CT-00-11/CT-00-12 not-applicable markers
     this report has always documented — zero unexplained skips, zero
     failures; count is higher than this sandbox's own local
     1518 passed/3 skipped because a real `hypothesis` install lets
     `tests/contract/test_property_based.py`'s 7 test functions run for
     real instead of the whole module import-skipping, section 0c)

✅ TypeScript unit tests (epd2-types workspace)
   → 3/3 passed

✅ frontend unit tests (web-shell workspace)
   → 2/2 passed

✅ next build
   → successful production build
```

This sandbox did not independently inspect a raw `VERIFICATION.log` or
extract/diff a returned tree this round (section 0c states this
plainly) — the numbers above are the project owner's direct report of
the actual run, reconciled (not merely accepted) against this sandbox's
own last local numbers.

### Revision 3 re-verification (historical, for the record)

Full local verification suite re-run end to end after the section 0b
fix, from a clean state. Results are identical to revision 2's own
re-verification below in every respect except `ruff format --check .`
(two more files reformatted this revision, reflecting the ten `sorted()`
call-site edits) — same 277/277 required paths, same canon checksum,
same 1518 passed / 3 skipped / 0 failed:

```text
✅ sha256(docs/canonical/TZ-00-domain-event-canon.md) unchanged:
   5ed52c3a6a94e821323616ac369595fd364a71115cf5c1c6763d8edb51a6044a

✅ python3 scripts/verify_versions.py
   → OK: all version sources are consistent.

✅ python3 scripts/check_forbidden_files.py
   → OK: no forbidden paths found.

✅ python3 scripts/check_repository.py
   → OK: all 277 required paths are present.

✅ ruff check .
   → All checks passed!

✅ ruff format --check .
   → 141 files already formatted (after `ruff format .` reformatted
     `services/initiative-service/tests/test_domain.py` and
     `services/voting-service/tests/test_domain.py`, section 0b)

✅ prettier --check .   (system Prettier 3.8.1, outside npm install)
   → All matched files use Prettier code style!

✅ mypy packages/python/epd2-core scripts tests/repository conftest.py
   → Success: no issues found in 24 source files
✅ mypy tests/contract
   → Success: no issues found in 18 source files
✅ mypy services/account-service
   → Success: no issues found in 8 source files
✅ mypy services/identity-service
   → Success: no issues found in 8 source files
✅ mypy services/eligibility-service
   → Success: no issues found in 8 source files
✅ mypy services/credential-service
   → Success: no issues found in 11 source files
✅ mypy services/audit-core
   → Success: no issues found in 10 source files
✅ mypy services/initiative-service
   → Success: no issues found in 9 source files
✅ mypy services/deliberation-service
   → Success: no issues found in 9 source files
✅ mypy services/moderation-service
   → Success: no issues found in 9 source files
✅ mypy services/voting-service
   → Success: no issues found in 9 source files
✅ mypy services/tally-service
   → Success: no issues found in 9 source files
✅ mypy services/delegation-service
   → Success: no issues found in 9 source files

✅ PYTHONPATH=<all 12 src/ dirs>:<python3 dist-packages> pytest -q
   → 1518 passed, 3 skipped, 0 failed
     (3 skips: `test_property_based.py` — hypothesis genuinely
     unavailable, section 1 — and the same 2 genuine CT-00-11/CT-00-12
     not-applicable markers this project has always documented; zero
     unexplained skips, zero failures — identical count to revision 2,
     confirming the section 0b fix changed no test behavior)

✅ JSON/YAML parse validation (every *.json / *.yml / *.yaml, 67 files)
   → all files parse without error

❌ uv lock / uv sync / npm install
   → blocked, section 3 (the one genuine, unresolved gap — network
     egress to pypi.org/files.pythonhosted.org/registry.npmjs.org
     returns 403, reconfirmed this pass)

⏳ Not run this pass (same network restriction; PACK-03 makes no
   frontend/TypeScript source change, section 1): npm run typecheck
   (both workspaces), npm run lint (frontend ESLint), npm run test (both
   workspaces), next build.
```

### Revision 2 re-verification (historical, for the record)

Full local verification suite re-run end to end after the section 0a
fix, from a clean state:

```text
✅ sha256(docs/canonical/TZ-00-domain-event-canon.md) unchanged:
   5ed52c3a6a94e821323616ac369595fd364a71115cf5c1c6763d8edb51a6044a

✅ python3 scripts/verify_versions.py
   → OK: all version sources are consistent.

✅ python3 scripts/check_forbidden_files.py
   → OK: no forbidden paths found.

✅ python3 scripts/check_repository.py
   → OK: all 277 required paths are present.

✅ ruff check .
   → All checks passed!

✅ ruff format --check .
   → 141 files already formatted (after `ruff format .` reformatted one
     file this pass, section 4's mypy fix reflow)

✅ prettier --check .   (system Prettier 3.8.1, outside npm install)
   → All matched files use Prettier code style! (after `prettier
     --write .` fixed 14 genuinely non-compliant files, section 5)

✅ mypy packages/python/epd2-core scripts tests/repository conftest.py
   → Success: no issues found in 24 source files
✅ mypy tests/contract
   → Success: no issues found in 18 source files
✅ mypy services/account-service
   → Success: no issues found in 8 source files
✅ mypy services/identity-service
   → Success: no issues found in 8 source files
✅ mypy services/eligibility-service
   → Success: no issues found in 8 source files
✅ mypy services/credential-service
   → Success: no issues found in 11 source files
✅ mypy services/audit-core
   → Success: no issues found in 10 source files
✅ mypy services/initiative-service
   → Success: no issues found in 9 source files
✅ mypy services/deliberation-service
   → Success: no issues found in 9 source files
✅ mypy services/moderation-service
   → Success: no issues found in 9 source files
✅ mypy services/voting-service
   → Success: no issues found in 9 source files
✅ mypy services/tally-service
   → Success: no issues found in 9 source files
✅ mypy services/delegation-service
   → Success: no issues found in 9 source files

✅ PYTHONPATH=<all 12 src/ dirs>:<python3 dist-packages> pytest -q
   → 1518 passed, 3 skipped, 0 failed
     (3 skips: `test_property_based.py` — hypothesis genuinely
     unavailable, section 1 — and the same 2 genuine CT-00-11/CT-00-12
     not-applicable markers this project has always documented; zero
     unexplained skips, zero failures)

✅ JSON/YAML parse validation (every *.json / *.yml / *.yaml, 67 files)
   → all files parse without error

❌ uv lock / uv sync / npm install
   → blocked, section 3 (the one genuine, unresolved gap — network
     egress to pypi.org/files.pythonhosted.org/registry.npmjs.org
     returns 403, reconfirmed this pass)

⏳ Not run this pass (same network restriction; PACK-03 makes no
   frontend/TypeScript source change, section 1): npm run typecheck
   (both workspaces), npm run lint (frontend ESLint), npm run test (both
   workspaces), next build.
```

### Revision 1's original verification (historical, for the record)

Identical results to revision 2 above, except
`tests/contract/test_ct00_02_unknown_status.py` did not yet have the
section 0a fix — this sandbox's own `mypy tests/contract` run reported
"Success: no issues found in 18 source files" then too (the bug was
invisible locally both before and after the fix, section 0a), and the
full local pytest count was the same 1518 passed / 3 skipped / 0 failed,
since the fix changed only type annotations and an added runtime
`isinstance` assertion that always evaluates `True` for every real
`Unknown*Error` instance in this codebase — no test behavior changed.

### Why 3 tests are skipped, not failing

```text
SKIPPED  tests/contract/test_property_based.py                 (no hypothesis)
SKIPPED  tests/contract/test_ct00_11_12_not_applicable.py (2 tests)
```

The first is a `pytest.importorskip("hypothesis")` guard: this sandbox
cannot install `hypothesis` at all (section 1) — CI's `uv sync
--all-groups` installs it and PACK-02's own GitHub Actions run already
confirmed this module runs and passes for real once it is present; PACK-03
made no change to this file. The remaining two are genuine, scope-level
**not-applicable** markers, unchanged from PACK-02: CT-00-11
(AI-produced-result human-control gate) and CT-00-12
(forbidden-operation-during-freeze) both require canon entities
(`AIProcessingRecord`, `EmergencyAction`) that are explicitly out of
scope for both PACK-02 and PACK-03 — there is nothing in either pack for
either test to exercise, and `test_ct00_11_12_not_applicable.py`
documents why rather than silently omitting them from the suite.

## 7. Repository boundary enforcement (ADR-008)

`tests/repository/test_service_boundaries.py` enforces, against the real
codebase's AST (not a hand-maintained list asserted to be true):

- No PACK-02 service imports another PACK-02 service's package (except
  every service's existing, unchanged dependency on `epd2_audit_core`)
  — PACK-02's own pre-existing rule, reconfirmed unbroken.
- No PACK-03 service imports another PACK-03 service's package.
  `initiative-service`, `deliberation-service`, `moderation-service`,
  `voting-service`, `tally-service`, and `delegation-service` are
  mutually independent; each depends only on its own package,
  `epd2_core`, and `epd2_audit_core`.
- No PACK-02 service imports any PACK-03 service — the dependency edge
  is strictly one-directional.
- Every PACK-03 → PACK-02 import is limited to the exact
  `.application`-scoped module paths ADR-008 names
  (`ALLOWED_PACK03_TO_PACK02_APPLICATION_MODULES`) — never a `.storage`
  or `.domain` import, and never an unlisted PACK-02 service. This is
  what makes `epd2_eligibility_service.application.get_eligibility_decision`
  / `get_eligibility_snapshot` (section 4) necessary: without them,
  `voting-service` and `initiative-service` would have no ADR-008-legal
  way to read eligibility state at all.
- `epd2_audit_core` itself imports neither PACK-02 nor PACK-03 domain
  services.

All five checks pass against the real, current codebase — none is
currently vacuous (each PACK-03 service genuinely does import at least
one allowed PACK-02 `.application` function where the pack's own spec
requires it, so the "narrow edge, not zero edge" distinction is actually
exercised).

## 8. Voting, delegation, and finality rules (ADR-009 / ADR-010)

Enforced in `services/voting-service`, `services/tally-service`, and
`services/delegation-service`, each backed by dedicated domain/application
tests:

- Vote changes are allowed until a ballot closes; only the latest valid
  `VoteEnvelope` per voter counts (superseding, not accumulating).
- Abstention is an explicit `BallotOption`, never an implicit "no
  envelope" state.
- Pilot ballot methods are restricted to single-choice and yes/no
  (`BallotMethod`); no ranked or weighted method is reachable this pack.
- Quorum is optional per ballot (`quorum_rule` may be `"none"`).
- Configuring a ballot requires second-actor approval — the actor who
  created a ballot cannot also be the one who approves its
  configuration (enforced in `voting-service`'s application layer, tested
  in `tests/contract/test_ct00_06_missing_permission.py`).
- Delegation is disabled by default and capped at depth 1, enforced
  bidirectionally in `delegation-service`'s domain layer (a delegation
  cannot be created if it would make any chain, in either direction,
  exceed depth 1).
- A direct vote always overrides a delegated one.
- A tie produces `ThresholdResult.TIE_NO_DECISION` — never a
  silently-broken tie.
- `Ballot.challenge_window_hours` defaults to 72
  (`DEFAULT_CHALLENGE_WINDOW_HOURS`) and is configurable per ballot
  (ADR-010).
- `ResultPublication`'s finality state is one of exactly
  `PROVISIONAL_BEFORE_DEADLINE` or
  `PROVISIONAL_PENDING_CHALLENGE_MECHANISM` — `compute_finality_state`
  has no code path that returns anything resembling "final"; there is no
  automatic-production-finality state in this pack, per ADR-010's own
  clarification.
- No PACK-03-accessible command reaches `BallotStatus.INVALIDATED` —
  confirmed by an AST-based test walking every `voting-service`
  application function's reachable status transitions, not merely
  asserted.

## 9. Identity separation and vote-linkability (structural, not

cryptographic)

`VoteEnvelope`, `VoteReceipt`, `Tally`, `ResultPublication`,
`SupportRecord`, `Delegation`, and `DelegationSnapshot` each declare
`additionalProperties: false` in their JSON Schema and are checked
against a `FORBIDDEN_FIELD_NAMES` frozenset (no `account_id`,
`person_id`, or `identity_record_id` field, and no schema property that
would let one be added) — the same structural pattern PACK-02 established
for `ParticipationCredential` (CT-00-08), extended here to every
PACK-03 entity that touches a vote, a delegation, or a support signature.
`tests/contract/test_ct00_08_identity_leakage.py` and
`test_ct00_09_vote_linkability.py` exercise this for all eleven
PACK-02+PACK-03 services, including a positive-space regression test
(mirroring PACK-02's own, section 0a of that report) confirming that
identity-service's own OpenAPI paths still legitimately declare
`identity_record_id` — proving the forbidden-field scan is scoped
correctly rather than passing vacuously. As with PACK-02, this is an
explicitly **structural** guarantee (no field, no shared ID, no schema
property, no reverse-lookup path from a vote back to an account) — not a
cryptographic-anonymity or unlinkability-under-collusion claim.

## 10. Reason-code registry

`contracts/reason-codes/pack-03.yml`: 70 entries — 14 canon-sourced (9
PACK-03-relevant canon section-24 codes plus 5 reused generics:
`PERMISSION_DENIED`, `EVENT_VERSION_UNSUPPORTED`,
`INTEGRITY_CHECK_FAILED`, `SERVICE_STATE_READ_ONLY`,
`EMERGENCY_FREEZE_ACTIVE`), 3 validation-generic additive codes
(mirroring `pack-02.yml`'s own pattern), and 53 PACK-03-additive codes
across all six services (ADR-006). This is a separate, non-overlapping
file from `contracts/reason-codes/pack-02.yml` (ADR-006 Option B) — codes
both packs need, such as `PERMISSION_DENIED`, are independently
redeclared in each registry rather than shared by import. Every reason
code actually used in a PACK-03 service's `raise ...Error(reason_code=...)`
call is checked against this registry by the pack-parametrized
`tests/contract/test_reason_codes_registry.py` (section 5, gap 1) — this
pass confirmed, both via that test (now running for real, not
sandbox-skipped, section 1) and via a direct `yaml.safe_load` cross-check,
that all 65 actually-used PACK-03 codes are present in the registry.

## 11. Readiness conclusion

```text
PACK-03 PASS
```

Every check this repository defines has now passed, both locally (as far
as this sandbox allows, revisions 1 through 3) and, decisively, by a
complete external GitHub Actions run with real network access (section
0c, revision 4): required structure (277 of 277 paths), no forbidden
paths, all version sources consistent, Ruff format and lint clean, a
real Prettier format check clean, ESLint clean, mypy clean across all
thirteen scoped groups with zero errors and zero suppressed via blanket
ignores, 1525 passing Python tests with 0 failures and exactly 2 genuine
CT-00-11/CT-00-12 not-applicable skips (zero unexplained skips), 3/3
TypeScript unit tests, 2/2 frontend tests, and a successful Next.js
production build. This revision closes the single remaining
Definition-of-Done gap from revisions 1 through 3: `uv.lock` and
`package-lock.json` were regenerated for real by the workflow's own
lock-generation steps, which — as section 0c explains — always run
fresh from the current `pyproject.toml`/`package.json` regardless of
what is committed, so this sandbox's own inability to run `uv
lock`/`npm install` locally was never actually a blocker for CI, only
for this sandbox's own local verification ceiling.

This report incorporates two real fixes surfaced across two rounds of
external GitHub Actions verification — a generic-exception-typed
attribute access in a parametrized contract test (section 0a), and a
redundant, mypy-unsafe sort key repeated across ten call sites in four
services (section 0b) — each closed with a precise, source-level fix (a
type-safe `isinstance` narrowing; a no-op key's removal, verified
programmatically to change no test outcome) and no blanket suppression,
with `.github/workflows/verify-and-package.yml` left untouched both
times and again this revision (documentation-only). No check was
weakened, no empty file was written to satisfy a path requirement, no
reason code was hidden, no legitimate field was stripped from a
service's own contract to make a test pass, and no unlinkability claim
is made without the automated test that backs it (section 9).
`docs/canonical/TZ-00-domain-event-canon.md` remains byte-identical
throughout (section 2). Nothing further stands between this repository
and this pack's Definition of Done: **PACK-03 PASS**.
