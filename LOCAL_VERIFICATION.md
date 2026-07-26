# Local Verification

> **Status update:** PACK-01 has since been verified end-to-end (real
> `uv.lock`/`package-lock.json`, `next build`, and the full `make verify`
> pipeline) via `.github/workflows/verify-and-package.yml` on GitHub
> Actions — see `docs/handover/PACK-01-REPORT.md` (Revision 4) and
> `docs/handover/PACK-01-VERIFICATION.log` for the real output. The
> procedure below remains the reference for regenerating lock files or
> re-verifying locally (e.g. after a dependency bump) on any machine with
> normal internet access, or via `GITHUB_ACTIONS_START.md` if one isn't
> available.

This repository's structure, code, formatting, linting, type checking, and
tests have already been verified inside the sandbox this package was built
in, wherever that did not require a live PyPI/npm connection (see
`docs/handover/PACK-01-REPORT.md`). Two things could not be executed there:
generating real lock files, and a real `next build` (plus anything else
that needs installed `node_modules`). This document is the complete,
minimal procedure to finish that verification on a machine or CI runner
with normal internet access.

## Prerequisites

- Python 3.12 (`python3.12 --version` should print `3.12.x`)
- [`uv`](https://docs.astral.sh/uv/) (`uv --version`)
- Node.js 22 LTS (`node --version` should print `v22.x`)
- npm (bundled with Node; `npm --version`)
- No root privileges are required. Nothing here touches global system
  configuration.

## Install steps

Run from the repository root, in this order:

```bash
# 1. Python dependencies — resolves and locks packages/python/epd2-core's
#    workspace plus the dev dependency group (pytest, mypy, ruff, pydantic,
#    pre-commit) against PyPI, writing uv.lock.
uv lock
uv sync --all-groups

# 2. Node dependencies — resolves the npm workspaces
#    (packages/typescript/epd2-types, frontend/web-shell) against the npm
#    registry, writing package-lock.json.
npm install
```

## Expected lock files

Both are created at the **repository root** (not inside any subpackage):

```text
uv.lock              # from `uv lock` / `uv sync`
package-lock.json    # from `npm install`
```

Both must be committed to git once generated. Do not hand-edit either file
or generate a placeholder — they must be the real, tool-produced output of
the commands above (see `scripts/check_repository.py`, which requires both
to be present, and `scripts/verify_versions.py`, which is unaffected by
them but checks other version consistency).

## Build steps

After the install steps above succeed:

```bash
# Full verification pipeline (repository checks, format check, lint,
# typecheck, Python tests, TypeScript tests, frontend tests, frontend build)
make verify
```

Or, to run just the frontend build in isolation:

```bash
npm run build --workspace=frontend/web-shell
```

This is the real `next build` — it must be run as-is; it cannot be
replaced by a source-file check or by the smoke test alone (both of those
already passed inside the sandbox, but neither substitutes for an actual
build).

`make verify` runs, in order: `check-repository`, `format-check`
(`ruff format --check` + `npm run format:check`), `lint` (`ruff check` +
frontend ESLint), `typecheck` (`mypy` + both TypeScript packages' `tsc
--noEmit`), `test` (Python + TypeScript + frontend tests), then
`build-frontend` (`next build`). It stops at the first failing step.

## Expected output

If everything is in order, `make verify`'s last lines should show the
frontend build succeeding (a `next build` summary listing the built
routes) with no step above it having failed. Individually:

- `python scripts/check_repository.py` → `OK: all N required paths are present.`
- `python scripts/check_forbidden_files.py` → `OK: no forbidden paths found.`
- `python scripts/verify_versions.py` → `OK: all version sources are consistent.`
- `ruff format --check .` → all files already formatted
- `ruff check .` → `All checks passed!`
- `uv run mypy .` → `Success: no issues found in N source files`
- `uv run pytest` → all tests pass (0 failed) — this is the one number that
  will _change_ from the sandbox's last run: once `uv.lock` and
  `package-lock.json` exist, `test_no_required_paths_are_missing` (which
  failed inside the sandbox for exactly that reason) should pass too.
- `npm run typecheck` (both packages) → no errors
- `npm run lint --workspace=frontend/web-shell` → no errors
- `npm run test` (both packages) → all tests pass
- `npm run build --workspace=frontend/web-shell` → build completes,
  producing `frontend/web-shell/.next/`

After a successful run, `git status --short` should show only `uv.lock`,
`package-lock.json`, and (if not already gitignored in your checkout)
`frontend/web-shell/.next/` / `node_modules/` as untracked build output —
no source file should have been modified by `make verify` itself.

## Known sandbox limitation

The repository was built and verified as far as possible inside a
network-restricted cloud sandbox that blocks `pypi.org`,
`files.pythonhosted.org`, and `registry.npmjs.org` (confirmed via direct
`403 host_not_allowed` responses from that sandbox's egress gateway; no
usable internal package mirror was reachable either). Because of that:

- `uv.lock` and `package-lock.json` do not exist in this delivery — they
  must be generated by the install steps above.
- The frontend (`frontend/web-shell`) was never actually built there —
  `next` cannot be installed without npm registry access. Its build status
  in `docs/handover/PACK-01-REPORT.md` is recorded as
  **`NOT EXECUTED — NETWORK RESTRICTED`**, not `FAIL` and not `PASS`,
  because it was never actually attempted to completion — it should not be
  read as a failed build, only as an unrun one.
- Frontend ESLint (`npm run lint --workspace=frontend/web-shell`) is in the
  same state, for the same reason (`eslint-config-next` and
  `@eslint/eslintrc` are not installable there).
- Everything else in this repository (Python code, TypeScript source,
  repository-structure checks, formatting, Ruff, mypy, Python tests,
  TypeScript typecheck/tests verified via a local scratch workaround) was
  actually run inside the sandbox and passed — see
  `docs/handover/PACK-01-REPORT.md` for the exact commands and output.

Once you've run the steps above and have real results (especially the
final `make verify` output and the two lock files), send them back so the
handover report can be closed out with a genuine `PACK-01 PASS` or, if
something legitimately fails, a `PACK-01 FAIL` with the real failure
recorded.

## PACK-09 note (2026-07-26)

The PACK-09 review round was carried out in a sandbox with **no egress to
package registries** — `pypi.org`, `files.pythonhosted.org` and
`registry.npmjs.org` all return `403 Host not in allowlist`. Neither
`uv sync --all-groups --frozen` nor `npm ci` could therefore be executed
there, and the artifact is labelled **CANDIDATE**, not PASS.

What _was_ executed offline, and what it substitutes for, is listed in
`docs/handover/PACK-09-IMPLEMENTATION-REPORT.md` section 3. Two results
from that round matter for anyone re-running this procedure:

1. **`uv.lock` was corrected by hand.** The PACK-09 submission added
   `epd2-compliance-service` to `pyproject.toml` (root dependency,
   workspace member and `tool.uv.sources` entry) without regenerating the
   lock, so `uv sync --frozen` would have installed an environment
   _without_ the package. The four missing lock entries were added
   manually; no registry package version changed. `uv lock --check` and
   `uv lock --locked` both pass, and `uv export --frozen` now emits
   `-e ./services/compliance-service`. A networked run should confirm that
   `uv lock` regenerates a byte-identical file — if it does not, prefer
   the regenerated one and re-run the pipeline.

2. **`docs/handover/PACK-08-IMPLEMENTATION-REPORT.md` was reformatted with
   Prettier.** `npm run format:check` already failed on the PACK-08
   baseline archive for that one file. The fix was applied with Prettier
   3.8.1 (the version available offline) while `package-lock.json` pins
   3.9.6; a networked run should confirm the locked version agrees.

Everything else in this document is unchanged and still applies.

## PACK-09 CANDIDATE-2 note (Architecture & Domain Framework 0.8.1)

The CANDIDATE-2 round — which continues the CANDIDATE above rather than
replacing it — ran in the same sandbox, under the same egress
restriction. Nothing in the note above is withdrawn, and the same two
corrections still stand.

**Commands that could NOT be run, and are therefore not claimed:**

| Command                          | Why                                              |
| -------------------------------- | ------------------------------------------------ |
| `uv sync --all-groups --frozen`  | needs `pypi.org` / `files.pythonhosted.org`      |
| `uv run <anything>`              | needs the synced environment                     |
| `npm ci`                         | needs `registry.npmjs.org`                       |
| `npm run lint`                   | needs `node_modules`                             |
| `npm run build`                  | needs `node_modules`                             |
| `npm run format:check`           | needs `node_modules`                             |
| `npm run typecheck`              | needs `node_modules`                             |

**No TypeScript, frontend or npm-workspace file was modified in the
CANDIDATE-2 round**, so the npm half of the pipeline has the same status
it had after CANDIDATE: unverified in this sandbox, verified content
unchanged.

**Commands that WERE run, and with what:**

| Command                | Substitute used                                              |
| ---------------------- | ------------------------------------------------------------ |
| `ruff check .`         | standalone `ruff` (uv tool install), not the locked version   |
| `ruff format --check .`| same                                                          |
| `mypy <all packages>`  | standalone `mypy`, Python 3.11 host interpreter               |
| `pytest`               | standalone `pytest`, Python 3.11 host interpreter             |
| `scripts/check_repository.py` | system `python3`                                       |
| `scripts/verify_versions.py`  | system `python3`                                       |

Two deltas against `uv.lock` matter and are stated rather than glossed:

1. **Python 3.11, not 3.12.** `pyproject.toml` targets 3.12; the sandbox
   interpreter is 3.11. No PEP 695 generic syntax or other 3.12-only
   construct is used anywhere in this repository (round 1 removed the one
   occurrence), so the suite runs identically — but "runs on 3.11" is not
   the same claim as "runs on the pinned 3.12", and only CI can make the
   second.
2. **Tool versions are whatever was installable offline**, not the
   versions `uv.lock` pins. A locked `ruff` could in principle report a
   rule this one does not.

`uv.lock` was **not modified** in the CANDIDATE-2 round: no dependency
was added, removed or bumped. The four new source modules
(`casework.py`, `notices.py`, `dataprotection.py`, `references.py`) live
inside the already-locked `epd2-compliance-service` package and import
only the standard library and `epd2_core`/`epd2_audit_core`.
