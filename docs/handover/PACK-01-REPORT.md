# CLAUDE-PACK-01 — Repository Skeleton: Handover Report

**Revision 3 (second remediation pass — local-verification handoff).** The
project owner accepted revision 2's fix to the report inconsistency and
asked that no further attempts be made to bypass this sandbox's network
restriction. This revision instead prepares the repository so the owner
can complete verification on a machine or CI with normal internet access,
and it records network-gated results as `NOT EXECUTED — NETWORK
RESTRICTED` rather than `PASS` or `FAIL`, since they were never actually
attempted to completion here.

## 0. Remediation history

- **Revision 1**: initial delivery. Claimed `tests/repository` passed 4/4
  — inconsistent, since `uv.lock`/`package-lock.json` were already absent.
- **Revision 2**: fixed that inconsistency, and fixed the real bug behind
  it — `scripts/check_forbidden_files.py` used to walk the entire
  filesystem, so it flagged mypy/ruff/pytest's own already-`.gitignore`d
  cache directories as "forbidden" when run after them. Made git-aware
  (`git ls-files --cached --others --exclude-standard`) so it evaluates
  only what would actually be committed. Verified with a regression check
  (`git add -f` a forbidden file → still caught).
- **Revision 3 (this one)**: no further attempt to reach `pypi.org` /
  `files.pythonhosted.org` / `registry.npmjs.org` was made, per the owner's
  instruction. Instead:
  - Added `LOCAL_VERIFICATION.md` (prerequisites, install steps, build
    steps, expected output, known sandbox limitation) so the owner can run
    the remaining verification themselves.
  - Tightened `pyproject.toml`'s dev dependency group with explicit upper
    bounds (next major excluded) instead of open-ended lower bounds only —
    the most "pinned" this session can responsibly do without a live index
    to resolve exact patch versions against.
  - Found and fixed a real, separate manifest bug while auditing
    completeness: `frontend/web-shell/eslint.config.mjs` imports
    `@eslint/eslintrc` (for `FlatCompat`), but it was never declared in
    `package.json`'s `devDependencies`. A real `npm install` followed by
    `npm run lint` would have failed with "cannot find module
    `@eslint/eslintrc`" even once network access was available. Fixed by
    adding it. Cross-checked every other non-relative, non-`node:` import
    in both TypeScript packages against their `package.json` — no other
    gaps found.
  - Re-ran every check this session can run without network on the
    resulting clean tree (section 6) — all still pass for the same,
    already-documented reason (missing lock files) and no new regressions.

## 1. Summary

Repository prepared for local closure of CLAUDE-PACK-01. Everything this
sandboxed session can verify without live PyPI/npm access has been
verified and passes. Everything that needs that access — generating
`uv.lock`/`package-lock.json`, `next build`, frontend ESLint — is staged
and documented in `LOCAL_VERIFICATION.md`, and is recorded below as
`NOT EXECUTED — NETWORK RESTRICTED`, not `PASS` and not `FAIL`.

## 2. Environment and network status

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

Network status (unchanged from revision 2; not re-attempted this pass, per
the owner's instruction — no further bypass attempts were made):

```text
pypi.org               → 403 host_not_allowed
files.pythonhosted.org → 403 host_not_allowed
registry.npmjs.org     → 403 host_not_allowed
```

This is a constraint of the current execution session, not a decision
about the project's approved stack — Python 3.12 / Node 22 / Next.js
remain declared and targeted throughout.

## 3. Lock files

```text
uv.lock:            MISSING
package-lock.json:  MISSING
```

Not hand-created; no placeholder substituted. See `LOCAL_VERIFICATION.md`
for the exact commands to generate both (`uv lock`, `uv sync --all-groups`,
`npm install`) and where they land (repository root). SHA-256 checksums
cannot be provided because the files do not exist yet.

## 4. Files added or changed this pass

- `LOCAL_VERIFICATION.md` (new) — prerequisites, install steps, build
  steps, expected output, and the known sandbox limitation, so the owner
  can finish verification independently.
- `pyproject.toml` — dev dependency group given explicit upper bounds
  (`pytest>=8.3,<9`, `pytest-cov>=5.0,<6`, `mypy>=1.11,<2`, `ruff>=0.6,<1`,
  `pydantic>=2.9,<3`, `pre-commit>=3.8,<4`) with a comment explaining why
  exact patch versions are not guessed.
- `frontend/web-shell/package.json` — added missing `@eslint/eslintrc`
  devDependency (real bug fix, section 0).
- `scripts/check_repository.py` — `LOCAL_VERIFICATION.md` added to
  `REQUIRED_PATHS` (72 required paths total now).
- `README.md` — links `LOCAL_VERIFICATION.md` from the documentation list.
- `docs/handover/PACK-01-REPORT.md` — this revision.

No other source files changed. Scope was not expanded: still no Docker,
PostgreSQL, Keycloak, event bus, API Gateway, authentication, business
services, or deployment configuration anywhere in this repository.

## 5. Commands executed this pass, and results

```text
✅ python3.12 scripts/check_repository.py
   → FAIL: missing uv.lock, package-lock.json (only these two, of 72
     required paths)

✅ python3.12 scripts/check_forbidden_files.py
   → OK: no forbidden paths found.

✅ python3.12 scripts/verify_versions.py
   → OK: all version sources are consistent.

✅ ruff format --check .
   → 13 files already formatted

✅ ruff check .
   → All checks passed!

✅ PYTHONPATH=packages/python/epd2-core/src mypy .
   (sandbox's pre-installed mypy 1.20.2, Python 3.11.15 host, checking
    this repository's Python-3.12-targeted source)
   → Success: no issues found in 13 source files

✅ PYTHONPATH=packages/python/epd2-core/src pytest -v
   → 13 passed, 1 failed
     FAILED test_no_required_paths_are_missing (uv.lock,
       package-lock.json missing — section 3; unchanged, expected)

✅ python3 -c "import json; json.load(open('frontend/web-shell/package.json'))"
   → OK (validates the package.json edit in section 4)

✅ prettier --check .  (repository-wide, respecting .prettierignore)
   → All matched files use Prettier code style!

✅ python3 -c "import yaml, json; ... validate every *.yml/*.yaml/*.json"
   → all files parse without error

⛔ uv lock / uv sync --all-groups     → NOT EXECUTED — NETWORK RESTRICTED
⛔ npm install / npm ci               → NOT EXECUTED — NETWORK RESTRICTED
⛔ npm run build --workspace=frontend/web-shell (next build)
                                      → NOT EXECUTED — NETWORK RESTRICTED
⛔ npm run lint --workspace=frontend/web-shell (ESLint)
                                      → NOT EXECUTED — NETWORK RESTRICTED
⛔ npm run typecheck (both TS packages, via a real npm install)
                                      → NOT EXECUTED — NETWORK RESTRICTED
   (revision 2 additionally ran a non-shipped, scratch local-symlink
    workaround for epd2-types only, as a diagnostic — 0 errors, 3/3 tests
    — but that is not a substitute for the real, network-installed
    toolchain and is not re-claimed as a pass here)
⛔ make verify (end-to-end)           → NOT EXECUTED — NETWORK RESTRICTED
   (its first step, `make setup`, requires the network access above)
```

## 6. Test results

- **Python** (`pytest`): 13 passed, 1 failed — same single, documented,
  expected failure as revision 2 (missing lock files). No regressions from
  this pass's edits.
- **Ruff format / lint**: clean.
- **mypy**: clean (13 source files).
- **Repository structure**: 70 of 72 required paths present (only the two
  lock files missing).
- **Forbidden-files check**: clean (git-aware; see revision 2's fix).
- **Version consistency**: clean.
- **Prettier / YAML / JSON**: clean.
- **TypeScript typecheck, TypeScript tests, frontend build, frontend
  ESLint**: `NOT EXECUTED — NETWORK RESTRICTED` (section 5). Not claimed as
  passing; not claimed as failing.

## 7. Security checks

Unchanged and reconfirmed: no `.env`, private keys, `.pem`/`.key` files
outside allowed fixtures, or real database files present; no
`node_modules`/`.venv`/cache directories committed; `.secrets.baseline` has
no findings; `CODEOWNERS` uses documented placeholders; `LICENSE` is the
required placeholder; no secrets or credentials introduced.

## 8. Open questions

Unchanged — see `docs/review/OPEN_QUESTIONS.md`.

## 9. Known limitations

Unchanged — see `docs/review/KNOWN_LIMITATIONS.md`; still accurate for
this revision.

## 10. Deviations (complete list — nothing hidden)

1. `uv.lock` and `package-lock.json` are absent — environment limitation
   (section 2), staged for local generation via `LOCAL_VERIFICATION.md`.
2. `.python-version` (`3.12`) — pins `uv` to the required interpreter.
3. `.secrets.baseline` — supports the `detect-secrets` pre-commit hook.
4. `.prettierignore` — excludes the frozen canon file from Prettier, plus
   standard build/dependency directories.
5. `scripts/check_forbidden_files.py` is git-aware (revision 2 bug fix).
6. `LOCAL_VERIFICATION.md` (new, this pass) — not part of the pack's
   literal file tree; added at the owner's explicit request this pass, and
   now tracked in `scripts/check_repository.py`'s required paths.
7. `pyproject.toml` dev dependency upper bounds (this pass) — tightening,
   not a scope or stack change.
8. `frontend/web-shell/package.json`'s `@eslint/eslintrc` addition (this
   pass) — a genuine missing-dependency bug fix, not a scope change.
9. Everything else follows CLAUDE-PACK-01 without further deviation. No
   Docker, PostgreSQL, Keycloak, event bus, API Gateway, authentication,
   business services, or deployment was added.

## 11. Files requiring owner configuration

- `CODEOWNERS` — replace placeholder team aliases once real GitHub teams exist.
- Repository URL / GitHub organization settings.
- `LICENSE` — pending an actual license decision.
- `uv.lock` / `package-lock.json` — generate via `LOCAL_VERIFICATION.md`.

## 12. Readiness conclusion

```text
PACK-01 FAIL
```

Not all Definition-of-Done items are met yet. This is not a code or
architecture defect: everything checkable without a live PyPI/npm
connection was verified and passes (section 6). The remaining items are
staged, precisely scoped, and documented in `LOCAL_VERIFICATION.md` for
the owner to run locally:

```text
uv.lock:              MISSING (generate via LOCAL_VERIFICATION.md)
package-lock.json:    MISSING (generate via LOCAL_VERIFICATION.md)
uv sync / npm install: NOT EXECUTED — NETWORK RESTRICTED
next build:            NOT EXECUTED — NETWORK RESTRICTED
frontend ESLint:       NOT EXECUTED — NETWORK RESTRICTED
make verify:           NOT EXECUTED — NETWORK RESTRICTED
```

Once the owner runs the steps in `LOCAL_VERIFICATION.md` and returns the
real `uv.lock`, `package-lock.json`, and `make verify` output, this report
will be updated with the genuine results — `PACK-01 PASS` if everything
holds, or a specific `PACK-01 FAIL` with the real failure if something
legitimately breaks once actually run against a live index.
