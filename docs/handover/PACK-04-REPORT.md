# CLAUDE-PACK-04 — Transparency Context: Handover Report

**Revision 4 — PASS.** Revisions 1 through 3 each closed a real,
externally-found gap — a 10-file Prettier formatting gap (revision 2,
section 0a) and a genuine markdown-authoring defect in this report's own
prose (revision 3, section 0b). A subsequent external GitHub Actions run
against the revision-3 candidate archive, with genuine PyPI/npm network
access, completed the full pipeline successfully end to end (section
0c): 1599 Python tests passed, 2 skipped (the same genuine CT-00-11/12
not-applicable markers this report has always documented), TypeScript
tests passed, frontend tests passed, a successful Next.js production
build, and Ruff, Prettier, ESLint, and mypy all clean, with all 305
required paths present and no forbidden files. No source code, test,
schema, workflow, or canon content was changed to reach this result —
this revision is a documentation-only update recording a genuine,
already-achieved PASS.

```text
PACK-04 PASS
```

This report follows the same honesty convention
`docs/handover/PACK-02-REPORT.md` and `docs/handover/PACK-03-REPORT.md`
established: every check this sandbox can actually run is run for real
(not skipped, not asserted from memory) and its literal output is quoted
below; every check this sandbox itself cannot run (network-gated `uv
lock`/`npm install`, and everything downstream of them locally —
`npm run typecheck`, ESLint, the TypeScript/frontend test suites, `next
build`) is named explicitly as not run locally, with the same reason
PACK-02 and PACK-03 already documented (`pypi.org`/
`files.pythonhosted.org`/`registry.npmjs.org` all return `403` from this
sandbox). That local ceiling is exactly what the external GitHub Actions
run in section 0c closes: it has genuine network access, regenerated
both lock files for real, and ran the complete pipeline end to end. This
report now claims a genuine, externally-confirmed `PACK-04 PASS`.

## 0a. External verification finding and fix (revision 2)

External verification on GitHub Actions (running against the revision-1
candidate archive, `epd2-civic-os-PACK-04-final-candidate.zip`) reported
a Prettier format-check failure — the one check this sandbox's own
revision-1 local run could not exercise, since no system Prettier
install check was repeated for the JSON/YAML/Markdown files this pass
specifically touched (this sandbox's `/opt/node22/bin/prettier` is
present and was not run against the full tree before the revision-1
export, unlike PACK-03's own early revisions, which did run it):

```text
Code style issues found in 10 files.
Run Prettier with --write to fix.
```

The 10 files: `CHANGELOG.md`; `contracts/openapi/pack-04.yaml`;
`contracts/events/transparency-audit-export-payload.v1.schema.json`,
`transparency-disclosure-policy-payload.v1.schema.json`,
`transparency-lobby-log-entry-payload.v1.schema.json`;
`contracts/schemas/audit-export-package.schema.json`,
`disclosure-policy.schema.json`, `lobby-log-entry.schema.json`;
`docs/handover/PACK-04-REPORT.md` (this file, revision 1's own text);
`services/transparency-service/README.md`. All ten are files newly
written or edited this pack — every one of them was hand- or
script-written without ever being run through Prettier locally, so this
is a real, genuine gap this sandbox's own `/opt/node22/bin/prettier
--check .` reproduced identically before any fix (`10 files`, exact
match to the list GitHub Actions reported).

Fixed at the source, with no logic, schema, test, workflow, or canon
change: `/opt/node22/bin/prettier --write .` (system-installed Prettier
3.8.1, the same binary PACK-03's own report already found and used
outside the blocked `npm install` path, section 1) reformatted exactly
those files listed above (whitespace/indentation/quote-style only — pure
formatting, per Prettier's own defaults, since this repository declares
no `.prettierrc`). Confirmed the change is formatting-only, not
content-bearing: every JSON schema and the OpenAPI YAML file were
re-parsed after the fix and compared for structural equivalence (same
keys, same `contracts/reason-codes/pack-04.yml` entry count of 18, same
10 OpenAPI paths) — nothing but layout changed. `ruff check .`, `ruff
format --check .`, `mypy` across all fourteen scoped groups, and the
full local pytest run were all re-executed after the fix and produced
results identical to revision 1 in every respect (same 305/305 required
paths, same canon checksum, same 1592 passed / 3 skipped / 0 failed,
section 11) — proving the Prettier fix changed no logic, schema, test,
or workflow behavior, exactly as this task's own instruction required.
`.github/workflows/*.yml` was not touched.

## 0b. External verification finding and fix (revision 3)

External verification on GitHub Actions (running against the revision-2
candidate archive, `epd2-civic-os-PACK-04-final-candidate-v2.zip`)
reported Prettier still failing on exactly one file:
`docs/handover/PACK-04-REPORT.md` — despite this sandbox's own
`/opt/node22/bin/prettier --check .` reporting that same file clean
after the section 0a fix.

Root cause, found on direct inspection rather than assumed: this
report's own revision-1 "Gaps found and fixed" section 5, item 3, was
genuinely malformed markdown. A code span wrapping a literal double
asterisk sat directly adjacent to other backtick-delimited terms with no
separating space, and the list continuation lines lost their leading
indentation and inter-word spacing entirely, with a literal backslash-
escaped double asterisk appearing further down — verbatim, the broken
text read (shown here as a plain code block, deliberately not inline
markdown, so this description cannot reintroduce the same ambiguity it
is describing):

```text
3. **`mypy` `**kwargs`unpacking against a`dict[str, object]`.**
`test_publish_ledger_entry_is_idempotent_by_event_id`builds a`kwargs = dict(...)`of mixed-typed values (mirroring the identical
...
idempotency tests) and unpacks it twice with `\*\*kwargs`. mypy widens
```

A code span whose content begins with a double asterisk, sitting inside
(or next to) a bold run, is a genuinely ambiguous construct for a
markdown parser — different Prettier/remark versions can tokenize it
differently, which is consistent with this sandbox's system Prettier
(3.8.1) and CI's locked Prettier (`package-lock.json` pins `3.9.6`)
disagreeing about how to normalize it, each producing output the other's
`--check` would reject. This was a genuine authoring defect in this
report's own prose, not something either Prettier version invented — no
other file in the `docs/canonical/`, `docs/handover/`, `docs/adr/`,
`docs/review/`, or `contracts/` trees, and no other list item in this
same file, contains the same backtick-adjacency pattern (checked
directly with a regex sweep for a closing backtick immediately followed
by a letter, across every Markdown/JSON/YAML file this pack touched or
otherwise scanned).

Fixed at the source: rewrote the item 5.3 heading and body in plain,
unambiguous prose — `**kwargs`, when mentioned, now appears only inside
non-bold running text ("unpacks it twice via double-star (`**kwargs`)
syntax"), never nested inside a bold span or jammed against another
code span with no separating space. No logic, schema, test, workflow,
or canon content changed — this is exclusively a correction to this
report's own descriptive text about a mypy fix that was already applied
correctly in `services/transparency-service/tests/test_application.py`
in revision 1; nothing about that fix itself changed. Re-ran
`/opt/node22/bin/prettier --write docs/handover/PACK-04-REPORT.md`
(reported "unchanged" — the hand-rewritten text already matched
Prettier's expected output), then `/opt/node22/bin/prettier --check .`
and `npm run format:check` against the full tree (both clean), then the
complete local verification suite end to end: results identical to
revision 2 in every respect (305/305 required paths, canon checksum
unchanged, Ruff clean, mypy clean across all fourteen scoped groups,
1592 passed / 3 skipped / 0 failed, section 11). `.github/workflows/*.yml`
was not touched.

## 0c. External verification: PASS (revision 4)

A subsequent external GitHub Actions run — against the revision-3
candidate archive (`epd2-civic-os-PACK-04-final-candidate-v3.zip`), with
genuine PyPI/npm network access — completed the full `make verify`
pipeline successfully:

```text
Status: PASS
Python:     1599 passed, 2 skipped, 0 failed
TypeScript: passed
Frontend:   passed
Next.js production build: successful
Ruff, Prettier, ESLint, mypy: clean
scripts/check_repository.py: all 305 required paths present
scripts/check_forbidden_files.py: no forbidden paths found
```

These results were reported directly by the project owner after running
the real workflow, not independently inspected by this sandbox against a
raw returned log or tree this round — this sandbox still has no path to
a returned CI artifact or genuine network access itself (section 1
below is unchanged). The reported numbers are, however, independently
_reconcilable_ against this sandbox's own last local run rather than
accepted blind: revision 3's local pytest run reported `1592 passed, 3
skipped` — 1 skip for `tests/contract/test_property_based.py`
(`pytest.importorskip("hypothesis")`, a single module-level skip outcome
since `hypothesis` cannot be installed here) and 2 for the genuine
CT-00-11/12 not-applicable markers. A real `hypothesis` install turning
that one collection-level skip into real passes for that module's test
functions predicts exactly the reported `1592 + 7 = 1599` passed and
`3 - 1 = 2` skipped — the identical arithmetic pattern, and the identical
`+7`/`-1` delta, that PACK-03's own revision 4 (section 0c of that
report) already established for this same sandbox/CI gap. This
arithmetic match is meaningful corroboration, not proof of an
independent log inspection, and this report says so plainly rather than
implying more certainty than this sandbox actually has.

The workflow's own lock-file steps (`.github/workflows/verify-and-package.yml`
lines "Generate Python lock file: uv lock" and "Generate Node lock file
and install dependencies: npm install") always regenerate `uv.lock` and
`package-lock.json` fresh from the current `pyproject.toml`/`package.json`
on every run — they never read or depend on whatever lock file happens
to be committed in the tree. This means the sandbox's inability to run
`uv lock`/`npm install` locally (section 1/3, unchanged) was always a
_local verification ceiling_, never a _CI blocker_ — the successful CI
run above is exactly the confirmation of that. This working tree's own
committed `uv.lock`/`package-lock.json` remain exactly as they were
before this revision — genuinely stale, but inconsequential to this
PASS, since CI never reads them and no PACK-04 service depends on their
committed content. They were left untouched rather than hand-edited to
look regenerated, since a hand-written lock file would not be a real one
(the same principle `docs/handover/PACK-02-REPORT.md` section 3 and
`docs/handover/PACK-03-REPORT.md` section 0c both state for their own,
now-closed, identical-in-kind gap).

No source code, test, schema, workflow file, or canon text was changed
to reach this PASS — revisions 2 and 3 (sections 0a/0b) were the last
substantive fixes, both formatting/documentation-only as those sections
detail; this revision only records the external result and updates this
report's own status language accordingly (sections 3, 11, 12).

## 0. What CLAUDE-PACK-04 adds

One new Python service, `services/transparency-service`
(`epd2_transparency_service`), implementing canon section 19a exactly as
accepted (canon 0.3.0, ADR-013, with ADR-013's own amendments) and
ADR-011 through ADR-015 (all `accepted`):

- The four canonical entities: `PublicLedgerEntry`, `AuditExportPackage`,
  `DisclosurePolicy`, `LobbyLogEntry` (`domain.py`) — `StrEnum` statuses,
  `*_ALLOWED_TRANSITIONS` state machines where canon defines one
  (`AuditExportPackageStatus`: `generated → published → superseded`;
  `DisclosurePolicyStatus`: `draft → active → superseded`;
  `LobbyLogEntryStatus`: `submitted → published`), and permanent
  content-immutability with no transition table at all for
  `PublicLedgerEntry` (canon 19a.1 gives it exactly one status value and
  an explicit "never rewritten" rule — mirroring `ModerationDecision`'s
  established precedent from PACK-03).
- Ten application-layer commands (`application.py`):
  `publish_ledger_entry`, `correct_ledger_entry`,
  `generate_audit_export_package`, `publish_audit_export_package`,
  `verify_audit_export_package`, `define_disclosure_policy`,
  `activate_disclosure_policy`, `submit_lobby_log_entry`,
  `publish_lobby_log_entry`, `correct_lobby_log_entry` — each with
  CT-00-04 idempotency (caller-supplied `event_id` short-circuits via
  `audit_store.get_by_event_id`), CT-00-07 audit creation via
  `epd2_audit_core.application.append_audit_event`, and construction of
  the ten canonical Transparency events (canon section 20.14,
  `events.py`).
- Storage interfaces plus in-memory reference adapters for all four
  entities (`storage.py`) — `create()` idempotent-by-content
  (`*ConflictError` on a same-id content mismatch),
  `AuditExportPackageStore`/`DisclosurePolicyStore`/
  `LobbyLogEntryStore.save()` for their real status transitions,
  `PublicLedgerEntryStore` with no `save()` at all (nothing to mutate).
- `contracts/openapi/pack-04.yaml` (10 operations, one path per real
  command, tag `transparency-service` exclusively — ADR-011's
  single-service decomposition), `contracts/reason-codes/pack-04.yml`
  (18 entries, ADR-014), four entity JSON Schemas and four event-payload
  JSON Schemas in `contracts/schemas/`/`contracts/events/`.
- `tests/repository/test_service_boundaries.py` extended with four new
  PACK-04 boundary tests (section 7).
- `tests/contract/test_ct00_08_identity_leakage.py` and
  `tests/contract/test_ct00_09_vote_linkability.py` each extended with a
  PACK-04 section (section 9).
- Additive, read-only upstream `.application`-layer functions across
  five existing services, per ADR-012 (section 6).

Governance Context (canon 5.12), AI-processing (canon section 17), and
Emergency/Crisis Override (canon section 19) remain explicitly out of
scope and unimplemented by this pass, per the task's own instruction and
canon 19a's own closing subsection.

## 1. Environment and network status

```text
$ python3 --version
Python 3.11.15
```

This sandbox's network egress still blocks `pypi.org` /
`files.pythonhosted.org` / `registry.npmjs.org` (`403`), reconfirmed
directly this pass:

```text
$ curl -sS -o /dev/null -w "%{http_code}\n" https://registry.npmjs.org/
403
$ curl -sS -o /dev/null -w "%{http_code}\n" https://pypi.org/
403
```

No `node_modules` exists in this tree, and no standalone `uv`-synced
project venv exists, for the same reason. Local verification instead
used the pre-existing standalone tool binaries at
`/root/.local/share/uv/tools/{pytest,mypy}/bin/` and
`/root/.local/bin/ruff`, plus the system `python3` interpreter (which
already carries a real `PyYAML` and `jsonschema` at
`/usr/local/lib/python3.11/dist-packages` — not network-fetched this
session). Pointing the standalone `pytest` tool's `PYTHONPATH` at that
same `dist-packages` directory, in addition to all thirteen workspace
`src/` directories, let every YAML/JSON-Schema-dependent contract test
run for real this pass instead of `pytest.importorskip`-skipping —
exactly the improvement PACK-03's own report (section 1) first found.
`hypothesis` remains genuinely absent from this sandbox (confirmed again
this pass — no installable wheel or importable module found anywhere on
the filesystem); `tests/contract/test_property_based.py` is the one test
module that still cannot run locally for that reason, unchanged from
PACK-02/03.

Because this pack makes no TypeScript/frontend source change beyond the
`REPOSITORY_VERSION` mirror in
`packages/typescript/epd2-types/src/version.ts` (already covered by
`version.test.ts`, section 2), `npm run typecheck`, ESLint, the
TypeScript/frontend unit test suites, and `next build` were not run
locally — consistent with every PACK-02/03 revision before external CI's
real network access closed that gap.

## 2. Canon integrity

`docs/canonical/TZ-00-domain-event-canon.md` was not opened for editing
this pass and was re-verified byte-identical both before and after every
change made this pass:

```text
$ sha256sum docs/canonical/TZ-00-domain-event-canon.md
9fc04b928ff043d25354039165eb7a9d0683396c6712210594eef232d6daf9ad
```

This matches the value fixed at the start of this task and has not
changed. `CANON_VERSION` remains `"0.3.0"` everywhere it is declared
(`epd2_core/version.py`, `epd2-types/version.ts`,
`docs/canonical/canon-version.json`) — this pass implements the
already-accepted canon 19a text; it makes no canon edit of its own.

`REPOSITORY_VERSION` was bumped `0.3.0 → 0.4.0`
(`packages/python/epd2-core/src/epd2_core/version.py`,
`packages/typescript/epd2-types/src/version.ts`, both version-consistency
unit tests, `CHANGELOG.md`'s newest entry), enforced by
`scripts/verify_versions.py`, which passes:

```text
$ python3 scripts/verify_versions.py
OK: all version sources are consistent.
```

`docs/canonical/canon-version.json`'s `repository_compatibility` field
(repository-side bookkeeping, not canon-immutable content) was widened
from `">=0.1.0 <0.4.0"` to `">=0.1.0 <0.5.0"` to admit the new
repository version, mirroring exactly how PACK-03 widened this same
field for its own `REPOSITORY_VERSION` bump (section 2 of that report).

## 3. Lock files — closed (revision 4)

```text
uv.lock:            Not regenerated locally — `uv lock` requires PyPI
                     access this sandbox does not have (section 1).
package-lock.json:  Not regenerated locally — same reason, npm registry.
```

This sandbox's own local ceiling above is unchanged and is not expected
to change (it never has real PyPI/npm network access). It is, however,
no longer an open gap for the pack as a whole: the external GitHub
Actions run recorded in section 0c has genuine network access, and its
own lock-generation steps (`uv lock`, `npm install`) regenerate both
lock files fresh from the current `pyproject.toml`/`package.json` on
every run, independent of whatever is committed in this tree — exactly
as PACK-03's own revision 4 (that report's section 0c) already
established for this identical sandbox/CI split. This working tree's own
committed `uv.lock`/`package-lock.json` are left exactly as they were —
not hand-edited to look regenerated — since CI never reads them and no
PACK-04 service depends on their committed content.

## 4. Files added or changed this pass

New:

- `services/transparency-service/` — full `src/`, `tests/`,
  `pyproject.toml`, `README.md`.
- `contracts/reason-codes/pack-04.yml` (18 entries).
- `contracts/schemas/public-ledger-entry.schema.json`,
  `audit-export-package.schema.json`, `disclosure-policy.schema.json`,
  `lobby-log-entry.schema.json`.
- `contracts/events/transparency-ledger-entry-payload.v1.schema.json`,
  `transparency-audit-export-payload.v1.schema.json`,
  `transparency-disclosure-policy-payload.v1.schema.json`,
  `transparency-lobby-log-entry-payload.v1.schema.json`.
- `contracts/openapi/pack-04.yaml` (10 paths, tag `transparency-service`).
- `docs/handover/PACK-04-REPORT.md` — this report.

Changed:

- `services/audit-core/src/epd2_audit_core/{application,storage}.py` —
  additive `list_by_target_types` (application) / `list_all` (storage),
  plus tests. Used directly by `generate_audit_export_package`.
- `services/initiative-service/src/epd2_initiative_service/application.py`
  — additive `get_published_initiative`, `get_initiative_version`, plus
  tests.
- `services/moderation-service/src/epd2_moderation_service/application.py`
  — additive `get_moderation_decision`, plus a test.
- `services/voting-service/src/epd2_voting_service/application.py` —
  additive `get_ballot`, plus a test.
- `services/tally-service/src/epd2_tally_service/application.py` —
  additive `get_result_publication`, plus a test.
- `tests/repository/test_service_boundaries.py` — four new PACK-04
  boundary tests (section 7).
- `tests/contract/_schema_helpers.py`,
  `test_reason_codes_registry.py`, `test_openapi_contract.py`,
  `test_ct00_08_identity_leakage.py`, `test_ct00_09_vote_linkability.py`
  — extended for PACK-04 (section 9).
- `scripts/check_repository.py` — `REQUIRED_PATHS` extended with every
  new PACK-04 path (277 → 305).
- Root `pyproject.toml` — `epd2-transparency-service` added to
  `dependencies`, `[tool.uv.workspace] members`, `[tool.uv.sources]`,
  Ruff `src`/isort `known-first-party`, mypy `mypy_path`, and pytest
  `testpaths`.
- `Makefile` — one `mypy services/transparency-service` line added to
  `typecheck`.
- `packages/python/epd2-core/src/epd2_core/version.py`,
  `packages/typescript/epd2-types/src/version.ts`,
  `packages/python/epd2-core/tests/test_version.py`,
  `packages/typescript/epd2-types/tests/version.test.ts`,
  `docs/canonical/canon-version.json` — `REPOSITORY_VERSION` `0.3.0 →
0.4.0` (section 2).
- `CHANGELOG.md` — new `[0.4.0] - transparency context (implementation)`
  entry, distinct from the earlier canon-only `[Unreleased]` entry.

## 5. Gaps found and fixed during this pass's own verification

1. **`publish_lobby_log_entry` forbidden-field false-positive.** The
   first draft of `application.publish_lobby_log_entry` called
   `assert_no_forbidden_fields` against
   `lobby_log_entry_full_state_payload(entry)` — the _audit_ payload
   builder, which legitimately includes `submitted_by_role_id` (a real,
   stored domain field). Since `submitted_by_role_id` is itself in
   `FORBIDDEN_FIELD_NAMES` (it may never appear in a _public_ payload),
   this made every call to `publish_lobby_log_entry` raise
   unconditionally. Caught by an end-to-end smoke test, not a unit test
   (none of the unit tests written up to that point happened to isolate
   this exact interaction). Fixed by switching the check to
   `lobby_log_entry_public_payload(entry)` — the public-payload builder,
   which never includes `submitted_by_role_id` in the first place — so
   the assertion now checks the thing it is actually supposed to guard.
2. **Docstring overclaimed the ADR-012 read boundary.** The first draft
   of `application.py`'s module docstring, and the README's own "Cross-
   pack read boundary" section, both stated the module "calls exactly
   four upstream read-only functions" (`get_published_initiative`,
   `get_initiative_version`, `get_moderation_decision`, `get_ballot`,
   `get_result_publication`). On review, none of those four is actually
   called from any command body — `publish_ledger_entry`,
   `correct_ledger_entry`, and `submit_lobby_log_entry` all take
   caller-supplied `raw_content` instead of fetching it internally
   (sourcing the correct upstream snapshot is the caller's
   responsibility; this service's own job is disclosure filtering plus
   immutable publication). The four functions are real, import-legal,
   and boundary-tested (section 7) — they exist for a later
   verify-before-publish enhancement — but claiming they are called
   today would have been inaccurate. Fixed by rewriting both the module
   docstring and the README section to state plainly which upstream call
   _is_ made (`list_by_target_types`, from
   `generate_audit_export_package`) and which four are sanctioned but
   not yet invoked.
3. **`mypy` disagreeing with a keyword-argument dict unpack.**
   `test_publish_ledger_entry_is_idempotent_by_event_id` builds a
   `kwargs = dict(...)` of mixed-typed values (mirroring the identical
   pattern already used in `services/delegation-service`,
   `initiative-service`, `moderation-service`, and `tally-service`'s own
   idempotency tests) and unpacks it twice via double-star (`**kwargs`)
   syntax. mypy widens the dict to `dict[str, object]`, which does not
   statically match `publish_ledger_entry`'s individually-typed keyword
   parameters. Fixed with the same `# type: ignore[arg-type]` on the two
   call sites the four sibling services already use for this exact,
   harmless pattern — not a blanket per-module or per-rule suppression.
4. **Ruff `E501`/`RUF001`/`RUF002` in the newly-authored files.** 18
   findings: several genuinely-over-100-column lines (wrapped by hand or
   via `ruff format`), two ambiguous EN DASH characters in a small-cell
   banding example (`"1–9"` → `"1-9"`, matching the ASCII hyphen the
   surrounding docstring already used), and three docstrings quoting a
   full Russian canon sentence that happened to include an isolated
   single-letter Cyrillic word (`с`, "with") — visually identical to
   Latin `c` in isolation, unlike a full Cyrillic word or phrase (which
   is what every _other_ service's existing Cyrillic canon quotes
   already use, and which ruff does not flag). Fixed by rewording the
   three docstrings to quote the same canon text without isolating a
   single-letter word, rather than adding a project-wide
   `allowed-confusables` override that would also silence this check for
   any future genuinely-ambiguous character elsewhere in the repository.

## 6. Cross-pack read boundary (ADR-012)

This is the second time this project reads from another same-generation
pack rather than an older one (PACK-03 → PACK-02 was the first, ADR-008).
`epd2_transparency_service.application` calls exactly one upstream
function directly: `epd2_audit_core.application.list_by_target_types`
(additive, read-only), from `generate_audit_export_package`. Four further
upstream read functions — `epd2_initiative_service.application.
get_published_initiative`/`get_initiative_version`,
`epd2_moderation_service.application.get_moderation_decision`,
`epd2_voting_service.application.get_ballot`,
`epd2_tally_service.application.get_result_publication` — are ADR-012-
sanctioned, implemented, unit-tested at their own service boundary, and
enforced as PACK-04's only permitted upstream `.application`-module
imports (section 7), but are not yet called from within
`epd2_transparency_service.application` itself (section 5, gap 2); they
remain available for a later verify-before-publish enhancement. No
PACK-02 identity/credential service, no `deliberation-service`, and no
`delegation-service` is ever imported by `transparency-service` (ADR-012's
explicit exclusions, section 7/9).

## 7. Repository boundary enforcement (ADR-012)

`tests/repository/test_service_boundaries.py` gained four new PACK-04
checks, run against the real codebase's AST:

- No PACK-04 service imports another PACK-04 service's package (vacuous
  today — PACK-04 has exactly one service, ADR-011 — but checked for
  the same reason PACK-02/03's own single-service edge cases are still
  checked: so the assertion is already in place before it could ever
  matter).
- No PACK-02 or PACK-03 service imports the PACK-04 service — the
  dependency edge is strictly one-directional, same shape as ADR-008's
  PACK-03 → PACK-02 edge.
- Every PACK-04 → upstream import is limited to the exact
  `.application`-scoped module paths ADR-012 names
  (`ALLOWED_PACK04_TO_UPSTREAM_APPLICATION_MODULES`) — never a
  `.storage` or `.domain` import, and never an unlisted service.
- `transparency-service` never imports `epd2_deliberation_service`,
  `epd2_delegation_service`, or either PACK-02 identity service
  (`epd2_account_service`, `epd2_identity_service`) — ADR-012's explicit
  exclusion list, checked structurally rather than merely documented.

All four checks pass against the real, current codebase; the third is
not vacuous — `generate_audit_export_package` genuinely does import
`epd2_audit_core.application.list_by_target_types`, so the "narrow edge,
not zero edge" distinction is actually exercised (identical framing to
PACK-03's own section 7).

## 8. Disclosure and Lobby Log rules (ADR-013/014/015)

- Per-field `DisclosurePolicy.field_rules`: `public` / `redacted` /
  `restricted` / `prohibited` classes (`DisclosureClass`); a field with
  no matching rule, or an ambiguous/duplicate one, defaults to
  `prohibited` (`resolve_field_rule`) — fail-closed, not fail-open.
  `FieldRule.__post_init__` rejects any rule that reclassifies a
  structurally forbidden field (`FORBIDDEN_FIELD_NAMES`) to anything
  other than `prohibited`/`suppress` — a policy can never override the
  structural prohibition, checked both at rule-construction time
  (`FieldRule`) and at policy-construction time
  (`DisclosurePolicy.__post_init__`'s `non_prohibited` check).
  `Transformation.GENERALIZE_TO_ROLE_SCOPE` only ever substitutes a
  caller-supplied `replacement_label` string — never the underlying
  value — so role-scope generalization can only ever produce a label,
  never a name, UUID, or other identifying value.
- `small_cell_threshold` defaults to `10`
  (`DEFAULT_SMALL_CELL_THRESHOLD`); `band_small_cell_value` bands `1`
  through `threshold - 1` as `"1-<threshold-1>"` and shows `0` and
  values `>= threshold` exactly.
  `SMALL_CELL_EXEMPT_SUBJECT_TYPES = {LedgerSubjectType.
RESULT_PUBLICATION}` — official result counts are never banded,
  matching this pack's own required-scope wording ("exact official
  ResultPublication counts remain exact").
- Lobby Log: `LOBBY_LOG_PUBLICATION_WINDOW` is 7 calendar days;
  `is_within_publication_deadline` checks it directly against
  `submitted_at`. `submit_lobby_log_entry` rejects a submission missing
  any of `organization_name`, `related_subject_type`,
  `related_subject_id`, `contact_date`, `topic_summary`, or
  `submitted_by_role_id` (`LobbyLogEntryIncompleteError`,
  ADR-014) — mandatory automated completeness and prohibited-field
  validation, no mandatory human pre-publication approval step by
  default. `correct_lobby_log_entry` is the only path to changing a
  published entry's content, and it always creates a new row with
  `supersedes_entry_id` set — `storage.InMemoryLobbyLogEntryStore` has
  no way to rewrite an existing row's `organization_name`/
  `topic_summary`/etc. in place.
- Public audit export (`AuditExportPackage`): `_build_chain_proof`
  constructs one `ChainProofItem` per included `AuditEvent` — each
  carries `event_hash`, `previous_event_hash`, public-safe metadata
  (`event_type`, `occurred_at`, `target_type`, `correlation_id`; never
  `actor_id`/`actor_type`/`before_hash`/`after_hash`, per
  `FORBIDDEN_AUDIT_EVENT_FIELDS`), and its own sequence position.
  `_compute_package_digest` folds every item's `event_hash` plus
  ordering into one package-level digest (`package_digest`);
  `_compute_integrity_proof` derives a separate `integrity_proof` field.
  `verify_audit_export_package` recomputes the digest over the package's
  _own_ stored `chain_proof` and compares it to the stored
  `package_digest` (`is_intact`) — `VerifyAuditExportPackageResult`'s own
  docstring states explicitly that `is_intact=False` means the exported
  segment's internal digest does not match, and never means anything
  about the original private `AuditEvent.event_hash` values, which this
  package does not and cannot recompute (no path in this service ever
  reads a private `AuditEvent`'s `before_hash`/`after_hash` back out).

## 9. Identity separation and vote-linkability

`FORBIDDEN_FIELD_NAMES` (`domain.py`) is the one structural rule shared
by all four entities: `account_id`, `person_id`, `identity_record_id`,
`participation_credential_id`, `vote_envelope_id`,
`encrypted_or_encoded_choice`, `credential_proof`, and the four internal
`*_role_id` fields. `assert_no_forbidden_fields` is checked
unconditionally — before, and independent of, whatever a
`DisclosurePolicy`'s own field rules would otherwise allow
(`apply_disclosure_policy` skips any `field_path` in
`FORBIDDEN_FIELD_NAMES` before ever consulting a rule). The four
`*_role_id` fields are legitimate _stored_ domain fields (canon section
8.4 `RoleAssignment` references); the "never published verbatim" half of
the rule is enforced one layer up, in `events.py`'s `*_public_payload`
builders — the only functions that should ever serialize one of these
four entities for external consumption.

`tests/contract/test_ct00_08_identity_leakage.py` gained a PACK-04
section: structural schema checks that none of the four entity schemas
or four event-payload schemas exposes an identity/credential/role-UUID
field, plus a real end-to-end test
(`test_transparency_ledger_entry_published_event_has_no_role_id`) that
calls `define_disclosure_policy → activate_disclosure_policy →
publish_ledger_entry` and asserts the `role_id` UUID string never
appears anywhere in the serialized emitted event payload, while
confirming it does appear on the stored domain entity (proving the scan
is scoped correctly, not vacuous).

`tests/contract/test_ct00_09_vote_linkability.py` gained a PACK-04
section: `FORBIDDEN_FIELD_NAMES` is confirmed to name
`vote_envelope_id`, `encrypted_or_encoded_choice`, and `credential_proof`
explicitly; a real end-to-end `publish_ledger_entry` call whose
caller-supplied `raw_content` includes all three of those keys proves
they are dropped from both the persisted `content_snapshot` and the
emitted public payload, even though the active `DisclosurePolicy` for
that call was never given a chance to say otherwise (they are removed
before any policy rule is consulted); and an AST-based import scan
confirms no module in `epd2_transparency_service` ever imports
`epd2_delegation_service` or `epd2_voting_service.domain` (the module
that actually carries `VoteEnvelope`) directly — PACK-04's one
sanctioned voting-service import, `get_ballot`, lives in
`epd2_voting_service.application` instead (section 6/7). As with
PACK-02/03, this is an explicitly **structural** guarantee — not a
cryptographic-anonymity claim.

## 10. Reason-code registry

`contracts/reason-codes/pack-04.yml`: 18 entries (ADR-014) — a separate,
non-overlapping file from `pack-02.yml`/`pack-03.yml` (same Option B
pattern ADR-006 established: codes both packs need, such as
`PERMISSION_DENIED`, are independently redeclared rather than shared by
import). Every reason code actually used in a
`transparency-service` `raise ...Error(reason_code=...)` call or audit
`reason_code=` classification was checked against this registry with a
manual `ReasonCodeRegistry` load plus a regex scan of `src/` for
`"[A-Z][A-Z0-9_]{2,}"`-shaped literals (the same method
`test_reason_codes_registry.py` uses, run directly this pass since the
standalone `pytest` tool now has real `PyYAML`, section 1): zero missing,
zero unused.

## 11. Commands executed this pass, and results

### Revision 4: external GitHub Actions verification — PASS (final, source of truth)

Run against the revision-3 candidate archive
(`epd2-civic-os-PACK-04-final-candidate-v3.zip`), with genuine PyPI/npm
network access. Results as reported to this report's author by the
project owner (see section 0c for the full reconciliation against this
sandbox's own last local run):

```text
✅ uv lock / uv sync
   → generated a genuine uv.lock covering all thirteen workspace
     members and installed from it (section 0c)

✅ npm install
   → generated a genuine package-lock.json and installed from it

✅ scripts/check_repository.py
   → OK: all 305 required paths are present.

✅ scripts/check_forbidden_files.py
   → OK: no forbidden paths found.

✅ ruff format --check . / ruff check .
   → clean

✅ prettier --check .
   → clean

✅ eslint .
   → clean

✅ mypy — all fourteen scoped groups
   → clean

✅ npm run typecheck — both TypeScript workspaces
   → clean

✅ pytest -q
   → 1599 passed, 2 skipped, 0 failed
     (2 skips: the same genuine CT-00-11/CT-00-12 not-applicable markers
     this report has always documented — zero unexplained skips, zero
     failures; count is higher than this sandbox's own local
     1592 passed/3 skipped because a real `hypothesis` install lets
     `tests/contract/test_property_based.py` run for real instead of the
     whole module import-skipping, section 0c)

✅ TypeScript unit tests
   → passed

✅ frontend unit tests
   → passed

✅ next build
   → successful production build
```

This sandbox did not independently inspect a raw log or extract/diff a
returned tree this round (section 0c states this plainly) — the numbers
above are the project owner's direct report of the actual run,
reconciled (not merely accepted) against this sandbox's own last local
numbers.

### Revision 2 re-verification (after the section 0a Prettier fix)

```text
✅ /opt/node22/bin/prettier --check .   (before the fix)
   → Code style issues found in 10 files. Run Prettier with --write to
     fix. (exact match to GitHub Actions' own report, section 0a)

✅ /opt/node22/bin/prettier --write .   (the fix)
   → 10 files reformatted, 140 files unchanged

✅ /opt/node22/bin/prettier --check .   (after the fix)
   → All matched files use Prettier code style!

✅ JSON/YAML structural re-check (all 6 reformatted JSON/YAML files)
   → same keys, same 18 pack-04.yml reason-code entries, same 10
     pack-04.yaml OpenAPI paths — formatting-only, confirmed
```

Every command below was re-run in full after the fix and produced
results identical to revision 1:

```text
✅ sha256sum docs/canonical/TZ-00-domain-event-canon.md
   9fc04b928ff043d25354039165eb7a9d0683396c6712210594eef232d6daf9ad
   (unchanged, section 2)

✅ python3 scripts/verify_versions.py
   → OK: all version sources are consistent.

✅ python3 scripts/check_forbidden_files.py
   → OK: no forbidden paths found.

✅ python3 scripts/check_repository.py
   → OK: all 305 required paths are present.

✅ ruff check .
   → All checks passed!

✅ ruff format --check .
   → 150 files already formatted

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
✅ mypy services/transparency-service
   → Success: no issues found in 9 source files

✅ PYTHONPATH=<all 13 src/ dirs>:<system python3 dist-packages> pytest -q
   → 1592 passed, 3 skipped, 0 failed
     (3 skips: `test_property_based.py` — hypothesis genuinely
     unavailable, section 1 — and the same 2 genuine CT-00-11/CT-00-12
     not-applicable markers PACK-02/03 already documented; zero
     unexplained skips, zero failures)

✅ JSON/YAML parse validation (every *.json / *.yml / *.yaml, 77 files)
   → all files parse without error

❌ uv lock / uv sync / npm install
   → blocked, section 3 (network egress to
     pypi.org/files.pythonhosted.org/registry.npmjs.org returns 403,
     reconfirmed this pass)

⏳ Not run this pass (same network restriction; PACK-04 makes no
   frontend/TypeScript source change beyond the REPOSITORY_VERSION
   mirror, section 1): npm run typecheck (both workspaces), npm run
   lint (frontend ESLint), npm run test (both workspaces), next build.
```

## 12. Readiness conclusion

```text
PACK-04 PASS
```

Every check this repository defines has now passed, both locally (as far
as this sandbox allows, revisions 1 through 3) and, decisively, by a
complete external GitHub Actions run with real network access (section
0c, revision 4): required structure (305 of 305 paths), no forbidden
paths, all version sources consistent, Ruff format and lint clean, a
real Prettier format check clean, ESLint clean, mypy clean across all
fourteen scoped groups with zero errors and zero blanket suppressions
(one documented, precedented `# type: ignore[arg-type]` pattern, section
5, identical to the one already used in four PACK-03 services' own
idempotency tests), 1599 passing Python tests with 0 failures and
exactly 2 genuine CT-00-11/CT-00-12 not-applicable skips (zero
unexplained skips), TypeScript tests passed, frontend tests passed, and
a successful Next.js production build. This revision closes the single
remaining Definition-of-Done gap from revisions 1 through 3: `uv.lock`
and `package-lock.json` were regenerated for real by the workflow's own
lock-generation steps, which — as section 0c explains — always run
fresh from the current `pyproject.toml`/`package.json` regardless of
what is committed, so this sandbox's own inability to run `uv
lock`/`npm install` locally was never actually a blocker for CI, only for
this sandbox's own local verification ceiling.

`docs/canonical/TZ-00-domain-event-canon.md` remains byte-identical
throughout (section 2) and `CANON_VERSION` is unchanged. No check was
weakened, no empty file was written to satisfy a path requirement, no
reason code was hidden, no legitimate field was stripped from a
service's own contract to make a test pass, no logic/schema/test/
workflow/canon content changed by either the section 0a or section 0b
fix (both formatting/documentation-only, independently re-confirmed),
and no unlinkability claim is made without the automated test that backs
it (section 9).

This report incorporates two real fixes surfaced across two rounds of
external GitHub Actions verification — a 10-file Prettier formatting gap
(section 0a) and a genuine markdown-authoring defect in this report's own
prose (section 0b) — each closed with a precise, source- or
documentation-level fix, re-verified locally after each fix, and now
confirmed by a clean external PASS (section 0c) with no further findings.
`PACK-04 PASS` is now a genuine, externally-confirmed status, not a
local-only claim.
