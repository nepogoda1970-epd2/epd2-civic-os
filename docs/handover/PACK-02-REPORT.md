# CLAUDE-PACK-02 — Identity Separation and Audit Kernel: Handover Report

**Revision 5 — PASS.** Revisions 1 through 4 each fixed one real bug found
by successive external GitHub Actions verification runs — a test-scope
bug (revision 2, section 0a), a Hypothesis parameter rename (revision 3,
section 0b), and a Hypothesis `categories=` argument-typing gap (revision
4, section 0d) — and cleaned up delivery so no manual GitHub edit was ever
required (revision 3, section 0c). A subsequent external GitHub Actions
run against the revision-4 tree, with genuine PyPI/npm network access,
completed the full pipeline successfully: `uv lock` regenerated a real
`uv.lock` (43 packages, including all 5 PACK-02 workspace members and
`hypothesis` 6.160.0, `jsonschema`, `types-PyYAML`, with real
files.pythonhosted.org hashes/URLs — not asserted, verified directly
against the returned lock file, section 3), and the complete `make verify`
pipeline passed end to end: 363 Python tests passed, 2 skipped (the same 2
genuine CT-00-11/12 not-applicable markers this report has always
documented — zero unexplained skips, zero failures), TypeScript typecheck
clean for both workspaces, ESLint clean, 3/3 TypeScript unit tests passed,
2/2 frontend tests passed, and `next build` completed successfully with 4
static routes generated. Full evidence (`VERIFICATION-RESULT.md`,
`VERIFICATION.log`) is in `epd2civicosverificationresult.zip`, and — per
this project's own established practice, restated after the PACK-01
incident — the returned tree was diffed file-by-file against the tree
that was sent for verification before being accepted (section 3): the only
differences were the regenerated `uv.lock`, the workflow's own
`VERIFICATION-RESULT.md`/`VERIFICATION.log` output, two harmless
build-time artifacts (`next-env.d.ts`, `tsconfig.tsbuildinfo`, both
`.gitignore`d or build-regenerated), and one non-required historical
evidence file (`docs/handover/PACK-01-VERIFICATION.log`) that did not
survive the round trip (see section 3's note — almost certainly because
it matches this repository's own `*.log` `.gitignore` pattern, not because
of any content corruption; it is not a required path and does not affect
this pack's verification). `docs/canonical/TZ-00-domain-event-canon.md`'s
SHA-256 is byte-identical to what was sent. No source code, test, or
check was changed to reach this result — this revision is a
documentation-only update recording a genuine, already-achieved PASS.

```text
PACK-02 PASS
```

## 0a. External verification finding and fix (revision 2)

External verification on GitHub Actions (running against the revision-1
candidate archive) reported a real bug in
`tests/contract/test_ct00_08_identity_leakage.py::test_openapi_credential_responses_do_not_reference_identity_fields`:
the test serialized the **entire** OpenAPI document
(`contracts/openapi/pack-02.yaml`, which covers all five PACK-02 services,
not just credential-service) and did a full-text substring scan for every
forbidden field name. It failed on `identity_record_id`, which
identity-service's own `/identity/verifications` path legitimately
declares as its request-body primary key (canon section 22's ownership
matrix — `IdentityRecord` owns `identity_record_id`; only
_credential/participation_-facing artifacts are required to omit it). This
was a genuine test-scope bug, not a canon or contract violation: no
identity field ever leaked into a credential response; the test was simply
checking the wrong (too broad) slice of the document.

Fixed by rewriting the test to:

1. Scope the scan to only the OpenAPI `paths` tagged `credential-service`
   (`_credential_service_paths`), plus the local `contracts/schemas/*.json`
   files those paths `$ref` (`_referenced_local_schema_names`) — never
   identity-service's or eligibility-service's own paths.
2. Check **declared `properties` keys**, not a full-text substring scan
   (`_declared_property_names`), because a second, related false-positive
   was found while fixing the first: `participation-credential.schema.json`'s
   own `description` field legitimately _names_ all eight forbidden fields
   in prose, to document what its `additionalProperties: false` guarantee
   excludes — a naive substring scan over the serialized schema flags its
   own documentation as a violation. Checking structural `properties` keys
   (the same approach `test_credential_schema_forbids_identity_fields` and
   `test_credential_event_payload_schemas_forbid_identity_fields` already
   used above it in the same file) catches only an actual declared field,
   which is what CT-00-08 is actually about.
3. Add a new, explicit positive-space test,
   `test_identity_service_paths_may_reference_identity_record_id`, that
   asserts identity-service's OpenAPI path still legitimately declares
   `identity_record_id` — proving the new scoping genuinely excludes
   identity-service rather than happening to pass vacuously, and guarding
   against a future, opposite mistake (stripping a legitimate field from
   identity-service's own contract because someone assumed the forbidden
   list applied everywhere).

No identity field was removed from `docs/canonical/TZ-00-domain-event-canon.md`
or from `contracts/openapi/pack-02.yaml`'s identity-service path;
`identity_record_id` is exactly as present there as before this fix.
CT-00-08 was not weakened — if anything it is now stricter (checking
actual declared properties in referenced schemas too, not just the inline
path text) and has an explicit regression test for the correct scope
boundary. Verified this pass: both the fixed and the new test were
executed directly (via a small harness using `python3.12`, which has a
real `PyYAML` install, since this sandbox's isolated `pytest` tool venv
still lacks `yaml` — see section 6) against the real
`contracts/openapi/pack-02.yaml` and confirmed to genuinely pass; the
now-fixed whole-spec substring scan was also re-run standalone to confirm
it really did previously flag `identity_record_id`, `person_id`, and
`account_id` (reproducing the reported failure), and that the new,
scoped, property-key check flags nothing.

## 0b. External verification finding and fix (revision 3, part 1): Hypothesis API rename

The same external GitHub Actions run also reported a real failure in
`tests/contract/test_property_based.py` once the suite ran there with a
genuinely installed `hypothesis` package (this test module import-skips
entirely in this sandbox, since `hypothesis` cannot be installed here at
all — section 6 — so this class of bug is invisible locally by
construction, exactly like section 0a's). Two calls used
`st.characters(whitelist_categories=(...))`. `whitelist_categories` /
`blacklist_categories` are old Hypothesis parameter names that were
renamed to `categories` / `exclude_categories` and later removed outright
— well before the `hypothesis>=6.112,<7` range this repository already
pins in `pyproject.toml` — so the call raises a hard `TypeError` (unexpected
keyword argument) at real import/collection time, not a deprecation
warning. This is a genuine source-level bug, fixed at the source: both
call sites (`test_duplicate_audit_event_id_with_identical_content_is_always_idempotent`'s
strategy and `test_canonical_dumps_is_independent_of_input_key_order`'s
strategy) now use `categories=(...)`, matching the current, real
Hypothesis API. No `# type: ignore` or version-pin change was used to
mask this — `categories` has been the stable, correct name for the entire
pinned `>=6.112,<7` range. The module docstring now records why, for
future readers who — like this sandbox — cannot see the failure locally.

This sandbox still cannot install `hypothesis` to execute the fixed file
end-to-end (same network restriction as section 3), so this fix was
verified as far as this environment allows: `python3 -m py_compile` on the
corrected file, a full `grep` confirming zero remaining references to the
old parameter names anywhere in the repository, and a manual check that
`categories` is the parameter Hypothesis's `characters()` strategy has
accepted since long before the pinned lower bound. Full behavioral
confirmation (the test actually running green) requires CI's real,
installed `hypothesis` — the same GitHub Actions run that found this bug
is expected to now pass it.

## 0c. Delivery-mechanics cleanup (revision 3, part 2): no manual GitHub edits required

Two further problems were fixed this revision, neither a bug in PACK-02's
own logic but both real gaps in how cleanly this repository could be
verified on GitHub Actions without a human editing anything there first:

1. **The repository was not actually Prettier-formatted**, despite
   `make verify` requiring `npm run format:check` (Prettier) to pass. This
   sandbox has no working `npm install` (network-restricted), so every
   earlier revision's Prettier compliance was _asserted_, never checked
   against a real Prettier binary — until this pass, when a
   system-installed Prettier (3.8.1, satisfying the `^3.3.0` range
   `package.json` already pins) was found available in this sandbox
   outside the project's own blocked `npm install` path. Running
   `prettier --check .` for the first time found 18 files
   genuinely non-compliant (mostly PACK-02's own new ADRs, architecture
   docs, JSON Schemas, and the OpenAPI contract — files this sandbox could
   author but never actually format-check). Running `prettier --write .`
   (respecting `.prettierignore`, which excludes the canon file) fixed all
   18; `docs/canonical/TZ-00-domain-event-canon.md`'s SHA-256 was
   confirmed unchanged before and after
   (`c731a24477d91010b5c6bc41a00253c8e30279b7f03394e53481ef0d8975e18b`),
   and a subsequent `prettier --check .` now reports "All matched files
   use Prettier code style!" This means `make verify`'s format-check will
   now pass in GitHub Actions on the first attempt, with no auto-fix step
   needed inside CI at all.
2. **`.github/workflows/verify-and-package.yml` carried two patch steps**
   that existed only to work around problems earlier revisions have now
   fixed at the source: "Restore required repository structure" (`mkdir`/
   `touch` for files that are now genuinely present with real content —
   confirmed via `scripts/check_repository.py`, all 166 required paths
   present) and "Fix canonical document formatting" (an in-CI
   `prettier --write` against the canon file, guarded by a checksum check
   added in revision 1 — necessary only because the repository wasn't
   pre-formatted, per point 1 above). Both were removed. The workflow now
   contains exactly: checkout, Python/uv/Node dependency setup, `uv lock`,
   `uv sync` + `npm install` (install), `make verify`, verification-status
   write, archive packaging, and artifact upload — nothing else. Since the
   tree is now genuinely Prettier-clean (point 1) and every required path
   is genuinely present with real content, neither removed step has
   anything left to do, and their removal closes the exact class of risk
   that caused the PACK-01 incident (an in-CI auto-format step touching a
   file it shouldn't have) rather than merely hardening it.

`uv.lock` itself remains un-regenerated in this repository (section 3):
this sandbox has no path to real PyPI access, so per this revision's own
instructions, GitHub Actions running the cleaned-up workflow above is the
stated, sole remaining step — not a placeholder for further manual
repository edits.

## 0d. External verification finding and fix (revision 4): mypy `arg-type` on `characters(categories=...)`

A subsequent external GitHub Actions run — against revision 3, with a
genuinely installed `hypothesis` and its real, PEP 561 type stubs — found
one real mypy error:

```text
tests/contract/test_property_based.py:202: error: Argument "categories"
to "characters" has incompatible type "tuple[str]"  [arg-type]
```

Line 202 is `st.characters(categories=("Ll",))`, nested inside
`st.text(alphabet=...)` inside `st.dictionaries(...)`. Hypothesis's real
stub types `characters(categories: Collection[CategoryName] | None = ...)`,
where `CategoryName` (imported internally from
`hypothesis.internal.charmap`) is a restrictive type covering only the
valid one/two-letter Unicode category codes — confirmed against
Hypothesis's own public API reference documentation this pass (fetched
directly rather than assumed), which describes `categories`/
`exclude_categories` as accepting exactly this kind of restricted category
specifier and gives `('Nd', 'Lu')` as a worked example — not plain `str`.
A bare string-literal tuple such as `("Ll",)`, written directly as a call
argument, is in this single-element case inferred by mypy as plain
`tuple[str]` rather than a `Literal["Ll"]`-typed tuple, which
`Collection[CategoryName]` correctly rejects (`str` is broader than the
`CategoryName` restriction) — this is a known category of mypy inference
gap around single-element tuple/list displays not always receiving the
same expected-type-driven literal narrowing that multi-element ones do
(the sibling call, `categories=("Lu", "Nd")`, was not flagged).

Fixed at the source, with no `# type: ignore` (a type-safe alternative
existed — say what the value actually is): both `categories=` tuples in
`tests/contract/test_property_based.py` are now named module-level
constants with an explicit `tuple[Literal["Ll"]]` /
`tuple[Literal["Lu"], Literal["Nd"]]` annotation
(`_LOWERCASE_LETTER_CATEGORY`, `_UPPERCASE_LETTER_OR_DIGIT_CATEGORIES`),
so mypy is told the precise, narrow type directly rather than left to
infer (and potentially widen) it from a bare literal. The module docstring
now records why. Both call sites were changed for consistency, not just
the one mypy flagged, since they share the same underlying construction
and the same latent risk.

This sandbox still cannot install `hypothesis` (section 3), so this fix
was verified as far as this environment allows: `python3 -m py_compile` on
the corrected file, `ruff check`/`ruff format --check` clean, and the
scoped `mypy tests/contract` group still reporting "Success" (this
sandbox's mypy run does not exercise Hypothesis's real stub at all, via
the pre-existing `ignore_missing_imports` override for a package this
sandbox cannot install — the same reason this class of bug is invisible
here in the first place and only surfaces on a real, external run with
`hypothesis` genuinely installed). Full confirmation that this specific
mypy error is gone requires that next external GitHub Actions run.

## 0. What CLAUDE-PACK-02 adds

Five new Python services, each an independent `uv` workspace member with
its own `pyproject.toml`, `src/`, and `tests/`:

- `services/account-service` (`epd2_account_service`) — owns `Account`.
- `services/identity-service` (`epd2_identity_service`) — owns
  `IdentityRecord`.
- `services/eligibility-service` (`epd2_eligibility_service`) — owns
  `EligibilityRule`, `EligibilityDecision`, `EligibilitySnapshot`.
- `services/credential-service` (`epd2_credential_service`) — owns
  `ParticipationCredential`.
- `services/audit-core` (`epd2_audit_core`) — owns `AuditEvent`, the
  append-only, hash-chained audit ledger every other service writes to.

Plus: three new ADRs (identity/participation separation, the audit hash
chain, the reason-code registry), a repository-wide JSON Schema + OpenAPI
contract for all seven entities above, a 43-entry reason-code registry (22
canon-inherited + 21 PACK-02-additive, see `contracts/reason-codes/pack-02.yml`
and ADR-004), the full CT-00-01..12 contract test suite, an identity-leakage
test suite, a full state-transition matrix test, a threat model
(`docs/review/PACK-02-THREAT-MODEL.md`), and updated architecture docs.

## 1. Environment and network status

```text
$ python3.12 --version
Python 3.12.3
$ uv --version
uv 0.8.17
$ node --version
v22.22.2
$ npm --version
10.9.7
```

This sandbox's network egress is unchanged from PACK-01 and still blocks
`pypi.org` / `files.pythonhosted.org` / `registry.npmjs.org`
(`403 host_not_allowed`), reconfirmed this pass via a direct `uv lock`
attempt (section 3). Because of this, all local verification in this
report was run using the pre-existing standalone tool binaries at
`/root/.local/share/uv/tools/{pytest,mypy,ruff}/bin/` (each in its own
isolated venv, none matching the project's own dependency set exactly —
see section 6's notes on `pytest`/`yaml`/`hypothesis` availability) rather
than through `uv run`, which requires a synced project venv this sandbox
cannot produce.

## 2. Canon integrity

`docs/canonical/TZ-00-domain-event-canon.md` was not opened for editing
this pass. `CANON_VERSION` remains `"0.1.0"` everywhere it is declared
(`epd2_core/version.py`, `epd2-types/version.ts`,
`docs/canonical/canon-version.json`). No ADR was required to touch it,
since PACK-02 adds new services and contracts, not new canon content.

```text
sha256(docs/canonical/TZ-00-domain-event-canon.md) =
  c731a24477d91010b5c6bc41a00253c8e30279b7f03394e53481ef0d8975e18b
```

`REPOSITORY_VERSION` was bumped `0.1.0` → `0.2.0` to reflect PACK-02's
addition (tracked consistently across `epd2_core/version.py`,
`epd2-types/version.ts`, `CHANGELOG.md`'s newest entry, and enforced by
`scripts/verify_versions.py`, which passes). `canon-version.json`'s
`repository_compatibility` field (repository-side bookkeeping, not
canon-immutable content — see `docs/canonical/README.md`) was widened from
`">=0.1.0 <0.2.0"` to `">=0.1.0 <0.3.0"` to admit the new repository
version.

## 3. Lock files — closed (revision 5)

```text
uv.lock:            REGENERATED — genuine, tool-generated lock file
                     produced by `uv lock` running under real GitHub
                     Actions network access; 43 packages total, including
                     all 5 PACK-02 workspace members
                     (epd2-account-service, epd2-identity-service,
                     epd2-eligibility-service, epd2-credential-service,
                     epd2-audit-core) and every new dev dependency
                     (hypothesis 6.160.0, jsonschema, types-PyYAML), each
                     with real files.pythonhosted.org URLs and hashes
package-lock.json:  UP TO DATE — confirmed byte-identical between the
                     tree sent for verification and the tree returned by
                     GitHub Actions (`diff` produced zero output);
                     PACK-02 added no new npm dependency, consistent with
                     every earlier revision's finding
```

This gap is now closed. Revisions 1 through 4 could not regenerate
`uv.lock` in this sandbox at all, because this sandbox's network egress
blocks `pypi.org` / `files.pythonhosted.org` (confirmed directly, both
online and `--offline`, in every earlier revision of this section — see
git history of this file for the exact failure transcripts) and
`hypothesis` — a genuinely new dependency this pack introduces — is not
present in the local `uv` cache either, so even an offline resolution
failed on the first new package it needed. There was no partial or manual
workaround that would have produced a genuine, tool-generated `uv.lock`
in that environment, and none was attempted; a hand-written lock file
would not be a real one.

Per the remediation path this report always described (identical in kind
to `docs/handover/PACK-01-REPORT.md`'s own revision-3-to-4 transition),
`.github/workflows/verify-and-package.yml` was run via **Actions → Verify
and Package → Run workflow** on a fork/clone with real GitHub Actions
network access. That run's `uv lock` step produced the real, complete lock
file above; its `uv sync --all-groups --frozen` step then installed from
it and the rest of `make verify` ran end to end (section 6). The lock file
was not accepted on the strength of the workflow's own PASS status alone:
per this project's established practice (restated after the PACK-01
incident), the full returned tree was extracted and diffed file-by-file
against the exact tree that was sent for verification before anything was
accepted. That diff showed only the expected differences — the
regenerated `uv.lock` itself, the workflow's own `VERIFICATION-RESULT.md`
and `VERIFICATION.log` output, two harmless build-time artifacts
(`next-env.d.ts`, `tsconfig.tsbuildinfo`, both either `.gitignore`d or
build-regenerated), and one non-required historical evidence file
(`docs/handover/PACK-01-VERIFICATION.log`) that did not survive the round
trip. That last file was investigated, not waved away: it is absent from
`scripts/check_repository.py`'s `REQUIRED_PATHS`, so its absence does not
fail any check, and it matches this repository's own `*.log`
`.gitignore` pattern, which is almost certainly why a fresh
`actions/checkout` + zip round trip did not carry it — nothing in the diff
suggests content corruption or a partial/failed run. `package-lock.json`
was separately confirmed byte-identical (zero-output `diff`), matching
this report's finding in every prior revision that PACK-02 added no npm
dependency.

The returned `uv.lock` was then copied into this working tree, replacing
the stale one. `docs/canonical/TZ-00-domain-event-canon.md`'s SHA-256 was
reconfirmed unchanged (section 2) both before and after accepting the
returned tree. No source code, test, or check was changed as part of
closing this gap — this section records a verified, external, successful
lock-file regeneration and its independent acceptance, nothing more.

## 4. Files added or changed this pass

New:

- `services/account-service/`, `services/identity-service/`,
  `services/eligibility-service/`, `services/credential-service/`,
  `services/audit-core/` — full `src/`, `tests/`, `pyproject.toml`,
  `README.md` each.
- `docs/adr/ADR-002-identity-participation-separation.md`,
  `docs/adr/ADR-003-append-only-audit-hash-chain.md`,
  `docs/adr/ADR-004-reason-code-registry.md`.
- `contracts/reason-codes/pack-02.yml`, `contracts/schemas/*.json` (8
  files), `contracts/events/*.json` (6 files), `contracts/openapi/pack-02.yaml`.
- `tests/contract/` — `conftest.py`, `_schema_helpers.py`, all
  `test_ct00_01..12*.py`, `test_state_transitions.py`, `test_audit.py`,
  `test_reason_codes_registry.py`, `test_openapi_contract.py`,
  `test_property_based.py`.
- `tests/repository/test_service_boundaries.py` (new this pass, see
  section 5) — the repository-wide, N×N structural boundary check.
- `docs/architecture/identity-participation-separation.md`,
  `docs/architecture/audit-kernel.md`, `docs/review/PACK-02-THREAT-MODEL.md`.
- `docs/handover/PACK-02-REPORT.md` — this report.

Changed:

- `pyproject.toml` — workspace members, dev dependencies
  (`types-PyYAML`, `jsonschema`, `hypothesis`), mypy overrides for
  `yaml`/`jsonschema`/`hypothesis`/`pytest`/`_pytest.*`
  (`ignore_missing_imports`, all sandbox-network-restriction workarounds
  that are no-ops once CI's `uv sync --all-groups` installs the real
  packages and their stubs).
- `scripts/check_repository.py` — `REQUIRED_PATHS` extended for every
  PACK-02 path above.
- `scripts/check_forbidden_files.py` — new central
  identity-participation-mapping-filename heuristic (pack section 15;
  `_is_forbidden_identity_link_filename`), tested in
  `tests/repository/test_forbidden_paths.py`.
- `Makefile` — `typecheck` target rewritten from a single `uv run mypy .`
  into scoped per-group invocations (section 5 explains why).
- `.github/workflows/verify-and-package.yml`, `GITHUB_ACTIONS_START.md` —
  generalized and hardened, see section 3.
- `docs/architecture/data-ownership.md`, `docs/architecture/service-boundaries.md`
  — updated to describe the five implemented services and the
  now-comprehensive structural boundary test.
- `docs/review/OPEN_QUESTIONS.md` — fixed a stale reason-code count (16 →
  21 additive codes, verified against the actual registry), added item 12
  (the mapping-filename heuristic's known detection limits).
- `docs/review/KNOWN_LIMITATIONS.md` — restructured into a PACK-02-current
  section and a PACK-01-inherited section.
- `packages/python/epd2-core/src/epd2_core/version.py`,
  `packages/typescript/epd2-types/src/version.ts`, `CHANGELOG.md`,
  `docs/canonical/canon-version.json` — version bump, section 2.
- `README.md` — status line and doc links updated for PACK-02 (section 8).

Not changed: `docs/canonical/TZ-00-domain-event-canon.md` (byte-identical,
section 2); `package.json` / `package-lock.json` (no npm-side change, see
section 3); `frontend/web-shell/`, `CODEOWNERS`, `LICENSE` (still
PACK-01-era placeholders, unchanged, see `docs/review/KNOWN_LIMITATIONS.md`).

Changed in revision 2 (section 0a):

- `tests/contract/test_ct00_08_identity_leakage.py` — rewrote
  `test_openapi_credential_responses_do_not_reference_identity_fields` to
  scope its scan to credential-service-tagged OpenAPI paths and their
  `$ref`'d schemas only, and to check declared `properties` keys instead
  of a full-text substring scan; added the new
  `test_identity_service_paths_may_reference_identity_record_id` regression
  test; added `_credential_service_paths`, `_referenced_local_schema_names`,
  and `_declared_property_names` helpers.

Changed in revision 3 (this revision, sections 0b/0c):

- `tests/contract/test_property_based.py` — both `st.characters(...)`
  calls changed from the removed `whitelist_categories=` parameter name to
  the real, current `categories=` name; added a docstring note explaining
  why (section 0b).
- `.github/workflows/verify-and-package.yml` — removed the "Restore
  required repository structure" and "Fix canonical document formatting"
  steps entirely (section 0c); now exactly checkout → dependency setup →
  `uv lock` → install → `make verify` → result write → package → artifact
  upload.
- 18 files reformatted with a real Prettier binary (section 0c) —
  `contracts/events/*.v1.schema.json` (4 files), `contracts/openapi/pack-02.yaml`,
  `contracts/schemas/account.schema.json`, `contracts/schemas/audit-event.schema.json`,
  `contracts/schemas/eligibility-decision.schema.json`,
  `docs/adr/ADR-002-identity-participation-separation.md`,
  `docs/adr/ADR-003-append-only-audit-hash-chain.md`,
  `docs/adr/ADR-004-reason-code-registry.md`, `docs/adr/README.md`,
  `docs/architecture/audit-kernel.md`, `docs/architecture/data-ownership.md`,
  `docs/architecture/identity-participation-separation.md`,
  `docs/handover/PACK-02-REPORT.md` (this file, from its own revision-1/2
  content), `docs/review/PACK-02-THREAT-MODEL.md`,
  `services/credential-service/README.md` — content unchanged, only
  whitespace/formatting; `docs/canonical/TZ-00-domain-event-canon.md` was
  not among them and its SHA-256 is unchanged (section 2).
- `docs/handover/PACK-02-REPORT.md` — revision 3 content.

Changed in revision 4 (this revision, section 0d):

- `tests/contract/test_property_based.py` — added `_LOWERCASE_LETTER_CATEGORY:
tuple[Literal["Ll"]]` and `_UPPERCASE_LETTER_OR_DIGIT_CATEGORIES:
tuple[Literal["Lu"], Literal["Nd"]]` module-level constants (with
  `from typing import Literal` added to the imports); both
  `st.characters(categories=...)` call sites now reference these typed
  constants instead of bare tuple literals; extended the module docstring
  explaining the mypy inference gap this works around (section 0d).
- `docs/handover/PACK-02-REPORT.md` — this revision.

Changed in revision 5 (this revision, section 3):

- `uv.lock` — replaced with the genuine, tool-generated lock file returned
  by the external GitHub Actions run (43 packages, including all 5
  PACK-02 workspace members and `hypothesis` 6.160.0, `jsonschema`,
  `types-PyYAML` with real `files.pythonhosted.org` hashes/URLs), after
  being diffed file-by-file against the sent tree and accepted (section 3).
- `docs/handover/PACK-02-REPORT.md` — rewritten from FAIL to PASS: header,
  section 3 (lock-file gap closed), section 6 (revision 5 verification
  results added), section 9 (conclusion changed to PACK-02 PASS). No
  source code, test, or check was changed as part of this revision.
- `README.md` — status line updated from PACK-02 FAIL to PACK-02 PASS.

## 5. A gap found and fixed during this pass's own verification

Two real problems were found while producing this report, not before it —
recorded here in full rather than quietly folded into the file list above,
per the pack's demand for honest verification:

1. **A single, repository-wide `uv run mypy .` cannot run at all.** The
   five services deliberately share identically-named test files (e.g.
   every service has its own `tests/test_domain.py`) with no `__init__.py`,
   so pytest can resolve them via `--import-mode=importlib`. mypy has no
   equivalent mode: one whole-repo invocation fails immediately with
   `Duplicate module named 'test_domain'` before checking a single real
   type. This was **not caught by earlier verification passes in this
   session** because the collision aborts before producing any per-file
   errors, which read superficially like "nothing to check" rather than
   "checking never happened." Fixed by invoking mypy once per group of
   files whose basenames cannot collide within that invocation
   (`packages/python/epd2-core scripts tests/repository conftest.py`;
   `tests/contract`; one call per service) — reflected in the `Makefile`'s
   `typecheck` target (section 4) and in section 6's commands below. Once
   the collision was worked around, mypy surfaced roughly 140 real,
   previously-unchecked errors across `tests/contract/*.py` (missing
   function annotations, `**dict`-splat argument-type mismatches once
   annotations were added, and two genuine `AuditEvent | None` `union-attr`
   bugs in `test_ct00_07_audit_creation.py` that needed an actual
   `assert result.audit_event is not None` fix, not a type-ignore) — all
   fixed for real; none suppressed.
2. **The structural service-boundary check only covered one direction.**
   Before this pass, the only AST-based cross-service import check lived
   in `services/eligibility-service/tests/test_domain.py`
   (`test_eligibility_service_has_no_import_dependency_on_identity_service`),
   checking just that one service against two others — not the full 5×5
   matrix `docs/architecture/service-boundaries.md` describes. Fixed by
   adding `tests/repository/test_service_boundaries.py`, which walks every
   service's actual `src/` AST and asserts the complete forbidden-pair
   matrix (every service may only import its own package,
   `epd2_core`, and `epd2_audit_core`; `epd2_audit_core` itself may import
   neither `epd2_core` peers nor any domain service). Currently zero
   violations exist in the real codebase — this test would have caught
   none retroactively, but it is now a real regression guard where before
   there was only a partial, one-directional one.
3. **A PEP 695 generic (`def f[T](...)`) syntax choice, made to satisfy
   Ruff's `UP047`, was silently unverifiable by this sandbox's own mypy
   tool.** mypy can only parse that syntax when the Python interpreter
   running mypy itself is 3.12+; this sandbox's standalone mypy binary
   runs under Python 3.11.15 (confirmed: `mypy --python-version 3.12` on a
   two-line PEP-695 file still fails with a hard parser `SyntaxError`,
   independent of the `--python-version` target flag). Reverted
   `tests/contract/test_state_transitions.py`'s `_all_forbidden_pairs` to
   a classic module-level `TypeVar`, which type-checks identically under
   Python 3.11 and 3.12, with a documented, narrow `# noqa: UP047` (Ruff's
   established local convention for this kind of tool-version conflict;
   see also the pre-existing `# noqa: E402` precedent in
   `packages/python/epd2-core/tests/test_reason_codes.py`).

## 6. Commands executed this pass, and results

### Revision 5: external GitHub Actions verification — PASS (final, source of truth)

Run against the revision-4 tree, on GitHub Actions (`ubuntu-latest`,
Python 3.12, Node.js 22), with genuine PyPI/npm network access. Evidence:
`VERIFICATION-RESULT.md` and the full `VERIFICATION.log` transcript,
delivered in `epd2-civic-os-verification-result.zip`
(`epd2civicosverificationresult.zip` as uploaded). Independently inspected
directly, not taken on the strength of a summary:

```text
✅ VERIFICATION-RESULT.md
   → Status: PASS
     Runner: GitHub Actions / ubuntu-latest
     Python: 3.12
     Node.js: 22

✅ uv lock
   → generated a genuine uv.lock: 43 packages, including all 5 PACK-02
     workspace members and hypothesis 6.160.0, jsonschema, types-PyYAML,
     with real files.pythonhosted.org hashes/URLs (section 3)

✅ uv sync --all-groups --frozen
   → installed from the freshly generated lock file

✅ npm install
   → installed; package-lock.json confirmed byte-identical to the sent
     tree (zero-output diff)

✅ scripts/check_repository.py
   → OK: all 166 required paths are present.

✅ scripts/check_forbidden_files.py
   → OK: no forbidden paths found.

✅ scripts/verify_versions.py
   → OK: all version sources are consistent.

✅ ruff format --check .
   → 87 files already formatted

✅ prettier --check .
   → All matched files use Prettier code style!

✅ ruff check .
   → All checks passed!

✅ eslint .
   → clean

✅ mypy — all 7 scoped groups (epd2-core/scripts/tests-repository/conftest,
   tests/contract, and one per service)
   → Success: no issues found, in every group

✅ npm run typecheck — both TypeScript workspaces
   → clean

✅ pytest -q
   → 363 passed, 2 skipped, 0 failed
     (2 skips: the same genuine CT-00-11/CT-00-12 not-applicable markers
     this report has always documented — zero unexplained skips, zero
     failures; count is higher than revisions 1-4's sandbox-observed
     339 passed/8 skipped because a real hypothesis + PyYAML install lets
     every previously sandbox-skipped test, including the full property-
     based suite, actually run for real instead of import-skipping)

✅ TypeScript unit tests (epd2-types workspace)
   → 3/3 passed

✅ frontend unit tests (web-shell workspace)
   → 2/2 passed

✅ next build
   → Compiled successfully; 4 static routes generated (/, /_not-found,
     and the remaining two PACK-01-era routes)

✅ sha256(docs/canonical/TZ-00-domain-event-canon.md) unchanged:
   c731a24477d91010b5c6bc41a00253c8e30279b7f03394e53481ef0d8975e18b
```

No `FAIL`, `Error`, or `error:` string appears anywhere in the 200-line
`VERIFICATION.log` (confirmed via `grep`). File-by-file diff of the
returned tree against the sent tree, per this project's established
practice: clean except for the expected regenerated `uv.lock`, the
workflow's own result files, two harmless build artifacts, and one
non-required historical log file, all accounted for in section 3.

### Revision 4 re-verification (historical, for the record)

```text
✅ python3 -m py_compile tests/contract/test_property_based.py
   → compiles cleanly after the Literal-annotated categories= constants (section 0d)

✅ python3 scripts/check_repository.py
   → OK: all 166 required paths are present.

✅ python3 scripts/check_forbidden_files.py
   → OK: no forbidden paths found.

✅ python3 scripts/verify_versions.py
   → OK: all version sources are consistent.

✅ ruff check .
   → All checks passed!

✅ ruff format --check .
   → 87 files already formatted

✅ prettier --check .   (real Prettier 3.8.1 binary)
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

✅ PYTHONPATH=<all 6 src/ dirs> pytest -q
   → 339 passed, 8 skipped, 0 failed (unchanged from revision 3 — this
     fix is type-annotation-only, no test logic or count changed)

✅ JSON/YAML parse validation (every *.json / *.yml / *.yaml)
   → all files parse without error

✅ sha256(docs/canonical/TZ-00-domain-event-canon.md) unchanged:
   c731a24477d91010b5c6bc41a00253c8e30279b7f03394e53481ef0d8975e18b

✅ .github/workflows/verify-and-package.yml step list reconfirmed unchanged
   (12 steps: checkout, Python/uv/Node setup ×3, uv lock, uv sync, npm
   install, make verify, write status, create archive, upload artifact,
   mark-failed — no patch step added, per this revision's own instruction)

❌ uv lock / uv lock --offline
   → still fails, see section 3 (the one genuine, unresolved gap, entirely
     unrelated to and unaffected by this revision's mypy annotation fix)
```

### Revision 3 re-verification (historical, for the record)

```text
✅ python3 scripts/check_repository.py
   → OK: all 166 required paths are present.

✅ python3 scripts/check_forbidden_files.py
   → OK: no forbidden paths found.

✅ python3 scripts/verify_versions.py
   → OK: all version sources are consistent.

✅ ruff check .
   → All checks passed!

✅ ruff format --check .
   → 87 files already formatted

✅ prettier --check .   (real Prettier 3.8.1 binary, found available in
   this sandbox outside the project's own network-blocked npm install —
   first genuine Prettier check any revision of this report has run)
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

✅ PYTHONPATH=<all 6 src/ dirs> pytest -q
   → 339 passed, 8 skipped, 0 failed

✅ JSON/YAML parse validation (every *.json / *.yml / *.yaml)
   → all files parse without error

✅ sha256(docs/canonical/TZ-00-domain-event-canon.md) unchanged:
   c731a24477d91010b5c6bc41a00253c8e30279b7f03394e53481ef0d8975e18b

✅ python3 -m py_compile tests/contract/test_property_based.py
   → compiles cleanly after the categories= fix (section 0b)

✅ grep -rn "whitelist_categories\|blacklist_categories\|whitelist_characters\|blacklist_characters"
   → zero matches anywhere in the repository (only the explanatory
     docstring in test_property_based.py names the old parameter, as
     prose, not as code)

❌ uv lock / uv lock --offline
   → still fails, see section 3 — the one genuine, unresolved gap; per
     this revision's own instructions, GitHub Actions running the
     now-minimal `.github/workflows/verify-and-package.yml` is the stated
     remaining step, not a placeholder for a manual repository edit
     (section 0c)

⏳ Not run this pass (same network restriction as PACK-01, and PACK-02
   makes no frontend/TypeScript change that would affect their result):
   npm run typecheck (both workspaces), npm run lint (frontend ESLint),
   npm run test (both workspaces), npm run build (frontend).
```

### Revision 2 re-verification (historical, for the record)

```text
✅ python3 scripts/check_repository.py
   → OK: all 166 required paths are present.

✅ python3 scripts/check_forbidden_files.py
   → OK: no forbidden paths found.

✅ python3 scripts/verify_versions.py
   → OK: all version sources are consistent.

✅ ruff format --check .
   → 87 files already formatted

✅ ruff check .
   → All checks passed!

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

✅ PYTHONPATH=<all 6 src/ dirs> pytest -q
   → 339 passed, 8 skipped, 0 failed
     (one more skip than revision 1's baseline: the section 0a fix added
     a second yaml-dependent test to test_ct00_08_identity_leakage.py,
     which sandbox-skips for the same reason as the other four yaml-gated
     tests below — both new/fixed tests were independently confirmed to
     genuinely pass against the real spec via a python3.12 + real-PyYAML
     harness, see section 0a and section 6's "Why 8 tests are skipped")

✅ JSON/YAML parse validation (every *.json / *.yml / *.yaml)
   → all files parse without error (checked programmatically this pass)

✅ sha256(docs/canonical/TZ-00-domain-event-canon.md) unchanged:
   c731a24477d91010b5c6bc41a00253c8e30279b7f03394e53481ef0d8975e18b

❌ uv lock / uv lock --offline
   → fails, see section 3 (the one genuine, unresolved gap, unchanged by
     this revision's fix — it is unrelated to the OpenAPI test scoping)

⏳ Not run this pass (same network restriction as PACK-01, and PACK-02
   makes no frontend/TypeScript change that would affect their result):
   npm run typecheck (both workspaces), npm run lint (frontend ESLint),
   npm run test (both workspaces), npm run build (frontend). PACK-01's own
   verification of these (`docs/handover/PACK-01-VERIFICATION.log`) is
   unaffected by PACK-02, which added no TypeScript/npm dependency or
   frontend code change.
```

### Why 8 tests are skipped, not failing

```text
SKIPPED  packages/python/epd2-core/tests/test_reason_codes.py       (no yaml)
SKIPPED  tests/contract/test_openapi_contract.py                    (no yaml)
SKIPPED  tests/contract/test_reason_codes_registry.py                (no yaml)
SKIPPED  tests/contract/test_ct00_08_identity_leakage.py (2 tests)    (no yaml)
SKIPPED  tests/contract/test_property_based.py                 (no hypothesis)
SKIPPED  tests/contract/test_ct00_11_12_not_applicable.py (2 tests)
```

The first five lines (6 tests) are `pytest.importorskip(...)` guards: this
sandbox's standalone `pytest` tool venv has neither `PyYAML` nor
`hypothesis` installed (same root network restriction as section 3), so
these tests are honestly reported as skipped rather than silently deleted
or their assertions weakened — CI's `uv sync --all-groups` installs both,
and they are expected to run and pass there. All of them, including both
of `test_ct00_08_identity_leakage.py`'s yaml-gated tests after the section
0a fix, were independently executed outside pytest this pass using
`python3.12` (which has a real `PyYAML` install already present in this
sandbox) against the real `contracts/openapi/pack-02.yaml`, and confirmed
to genuinely pass — this is stronger evidence than a re-read, since it is
an actual execution against real data, not just logic review. The last two
are genuine, pack-scoped **not-applicable** markers, not skips due to a
missing dependency: CT-00-11 (AI-produced-result human-control gate) and
CT-00-12 (forbidden-operation-during-freeze) both require canon entities
(`AIProcessingRecord`, `EmergencyAction`) that are explicitly out of
PACK-02's scope per the pack's own section 3.2 — there is nothing in this
pack for either test to exercise, and `test_ct00_11_12_not_applicable.py`
documents why rather than silently omitting CT-00-11/12 from the suite.

### Revision 1's original verification log (historical, for the record)

```text
✅ python3 scripts/check_repository.py (after PACK-02-REPORT.md was written)
   → OK: all 166 required paths are present.
✅ PYTHONPATH=<all 6 src/ dirs> pytest -q
   → 339 passed, 7 skipped, 0 failed
(before that, with the report not yet written: 338 passed, 7 skipped, 1
failed — test_no_required_paths_are_missing, for the report's own
absence, the only non-environmental failure revision 1 ever had)
```

## 7. Reason-code registry

`contracts/reason-codes/pack-02.yml`: 43 entries total — 22 inherited
verbatim from the canon's own reason-code standard (canon section 24) and
21 new, PACK-02-additive codes introduced under ADR-004 (verified
programmatically this pass: `Counter(source for source in registry) ==
{"canon": 22, "pack-02-adr-004": 21}`). Every code used in a service's
`raise ...Error(reason_code=...)` call is checked against the registry by
`tests/contract/test_reason_codes_registry.py::test_every_reason_code_literal_used_in_services_is_registered`
(currently sandbox-skipped only because that test needs `yaml`, section 6;
not because the check itself is disabled).

## 8. Identity/participation separation (INV-01) and the audit kernel (INV-04/05)

See `docs/architecture/identity-participation-separation.md` and
`docs/architecture/audit-kernel.md` for the full account. In summary:
`ParticipationCredential` (credential-service), `EligibilityDecision`/
`EligibilitySnapshot` (eligibility-service), and every canonical event
payload schema structurally forbid identity-linking fields
(`FORBIDDEN_FIELD_NAMES`, enforced via `additionalProperties: false` in
every relevant JSON Schema and exercised end-to-end in
`tests/contract/test_ct00_08_identity_leakage.py` and
`test_ct00_09_vote_linkability.py`). This is a **structural**, tested
guarantee (no field, no shared ID, no schema property) — it is explicitly
**not** a cryptographic-anonymity or unlinkability-under-collusion claim;
`docs/architecture/identity-participation-separation.md`'s final section
says so directly, and `docs/review/PACK-02-THREAT-MODEL.md` records the
residual risk of a privileged insider correlating records through
side channels (timestamps, request metadata) that this pack's scope does
not close.

`epd2_audit_core`'s `AuditEventStore` interface
(`services/audit-core/src/epd2_audit_core/storage.py`) has exactly four
methods — `append`, `get_by_event_id`, `list_by_aggregate`,
`verify_chain` — and **no update or delete method exists at all**
(confirmed by reading the interface, not merely asserted); every append is
SHA-256 hash-chained to the previous entry
(`services/audit-core/src/epd2_audit_core/hash_chain.py`), and tamper /
broken-link detection is exercised in
`services/audit-core/tests/test_storage.py`.

## 9. Readiness conclusion

```text
PACK-02 PASS
```

Every check this repository can genuinely execute passes, now confirmed
both locally (as far as this sandbox allows) and, decisively, by a
complete external GitHub Actions run with real network access (section 6,
revision 5): required structure (166 of 166 paths), forbidden-paths,
version consistency, Ruff format, Ruff lint, a real Prettier format check,
ESLint, mypy across all 7 scoped groups (87 source files, zero errors,
zero suppressed via blanket ignores), TypeScript typecheck for both
workspaces, 363 passing Python tests with 0 failures and exactly 2 genuine
CT-00-11/CT-00-12 not-applicable skips (zero unexplained skips), 3/3
TypeScript unit tests, 2/2 frontend tests, a successful `next build`
(4 static routes), and JSON/YAML validity across every contract file. This
revision closes the single remaining Definition-of-Done gap from
revisions 1 through 4: `uv.lock` has been regenerated for real (43
packages, all 5 PACK-02 workspace members, `hypothesis` 6.160.0,
`jsonschema`, `types-PyYAML`, real `files.pythonhosted.org` hashes/URLs —
section 3), verified as a genuine tool-generated artifact and not
fabricated, and accepted only after the established file-by-file diff
against the sent tree came back clean (section 3).

This report incorporates four real fixes surfaced across four separate
rounds of external GitHub Actions verification — a test-scoping bug
(section 0a), a Hypothesis parameter rename (section 0b), a Hypothesis
`categories=` argument-typing gap (section 0d), and the lock-file
regeneration itself (section 3) — none a canon or contract violation,
each closed with a precise, source-level, type-safe change and no blanket
suppression. Delivery mechanics were cleaned up so no manual GitHub edit
was ever required: the tree is genuinely Prettier-formatted and
`.github/workflows/verify-and-package.yml` performs only checkout,
dependency setup, `uv lock`, install, `make verify`, result generation,
packaging, and artifact upload (section 0c) — unchanged since revision 3
and reconfirmed present in the exact tree that produced this PASS. No
check was weakened, no empty file was written to satisfy a path
requirement, no reason code was hidden, no legitimate field was stripped
from a service's own contract to make a test pass, and no unlinkability
claim is made without the automated test that backs it (section 8).
`docs/canonical/TZ-00-domain-event-canon.md` remains byte-identical
throughout (section 2). `package-lock.json` required no change (section
3). Nothing further stands between this repository and this pack's
Definition of Done: **PACK-02 PASS**.
