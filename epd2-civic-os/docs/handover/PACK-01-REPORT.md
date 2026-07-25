# CLAUDE-PACK-01 — Repository Skeleton: Handover Report

**Revision 4 (real verification received, integrity issue found and repaired,
genuine PACK-01 PASS recorded).** The project owner ran the four local/CI
verification commands on a machine with normal internet access (via
`.github/workflows/verify-and-package.yml` on GitHub Actions) and returned a
result archive. Before accepting it as the new canonical repository state,
it was diffed file-by-file against the prior (revision 3) tree. That diff
found the delivered archive had altered the immutable canon file and emptied
five required governance files — see section 0 for the full account. The
canon and governance files were restored from the untouched revision 3
tree, the genuine `uv.lock`/`package-lock.json` and the new CI workflow were
kept, and the complete offline verification suite was re-run on the repaired
tree. Everything passes. This revision records a genuine **PACK-01 PASS**.

## 0. Remediation and verification history

- **Revision 1**: initial delivery. Claimed `tests/repository` passed 4/4
  — inconsistent, since `uv.lock`/`package-lock.json` were already absent.
- **Revision 2**: fixed that inconsistency, and fixed the real bug behind
  it — `scripts/check_forbidden_files.py` used to walk the entire
  filesystem, so it flagged mypy/ruff/pytest's own already-`.gitignore`d
  cache directories as "forbidden" when run after them. Made git-aware
  (`git ls-files --cached --others --exclude-standard`) so it evaluates
  only what would actually be committed.
- **Revision 3**: no further attempt to reach `pypi.org` /
  `files.pythonhosted.org` / `registry.npmjs.org` was made, per the owner's
  instruction. Added `LOCAL_VERIFICATION.md`, tightened `pyproject.toml`'s
  dev dependency upper bounds, fixed a missing `@eslint/eslintrc`
  devDependency. Recorded network-gated items as
  `NOT EXECUTED — NETWORK RESTRICTED`. Concluded `PACK-01 FAIL`.
- **Revision 4 (this one)**: the owner added
  `.github/workflows/verify-and-package.yml` (a `workflow_dispatch` job
  that generates both lock files, runs `make verify`, and packages the
  result) to their copy of the revision-3 repository, ran it on GitHub
  Actions — a real environment with unrestricted PyPI/npm access — and
  attached the resulting artifact (`epd2civicosPACK01result1.zip`,
  containing `uv.lock`, `package-lock.json`, `PACK-01-RESULT.md`,
  `PACK-01-VERIFICATION.log`).

  **Before accepting that archive as the new canonical state, it was
  extracted and diffed file-by-file against the revision-3 tree.** That
  comparison found two integrity problems in the delivered archive that
  the archive's own `PACK-01-RESULT.md`/`PACK-01-VERIFICATION.log` did not
  mention:
  1. `docs/canonical/TZ-00-domain-event-canon.md` had a different checksum
     (`7ffdd1b1e0a22412686b4ec508441924` → `bf8cd9d5a9a2e424eead969dcdb4e07d`).
     A whitespace-normalized diff showed the only remaining difference was
     markdown table-separator padding (`|---|---|` →
     `| ----- | ----- |`) — a Prettier table reformat, not a content or
     meaning change. Root cause: the archive was missing
     `.prettierignore` entirely, so Prettier reformatted the one file this
     project's own rules say must never be edited without a separate task
     and an accepted ADR.
  2. Five required governance files existed at their correct path (so
     `scripts/check_repository.py` still reported all 72 required paths
     present) but had been silently truncated to **0 bytes**, content
     entirely gone: `.github/workflows/ci.yml` (was 2277 bytes),
     `.github/pull_request_template.md` (1262 bytes),
     `.github/ISSUE_TEMPLATE/bug_report.yml` (1104 bytes),
     `.github/ISSUE_TEMPLATE/feature_request.yml` (966 bytes),
     `.github/ISSUE_TEMPLATE/architecture_change.yml` (1512 bytes). Three
     further files were missing outright (not required-path-tracked, so
     nothing flagged their absence either): `.prettierignore`,
     `.python-version`, `.secrets.baseline`.

  The cause of the emptying is not established (it was not reproduced
  here); it may be an artifact of however the archive's contents were
  copied/edited between the workflow run and the upload. Everything else
  in the archive checked out: `package.json`, `frontend/web-shell/package.json`,
  `pyproject.toml`, `.gitignore`, and `Makefile` were byte-identical to
  revision 3; `uv.lock` and `package-lock.json` look like genuine,
  tool-produced output; `PACK-01-VERIFICATION.log` shows a real,
  successful end-to-end `make verify` run including a real `next build`.

  **Repair performed** (owner-selected option: repair then accept):
  - Restored `docs/canonical/TZ-00-domain-event-canon.md` from the
    untouched revision-3 copy (checksum `7ffdd1b1e0a22412686b4ec508441924`
    confirmed matching the original byte-for-byte copy placed at project
    start).
  - Restored the five emptied governance files and the three missing
    files (`.prettierignore`, `.python-version`, `.secrets.baseline`) from
    the untouched revision-3 tree, unchanged.
  - Kept the genuine `uv.lock` and `package-lock.json` from the archive.
  - Kept `.github/workflows/verify-and-package.yml` (the owner's new
    one-click verification workflow) and its instructions
    (`GITHUB_ACTIONS_START.md`), and moved the archive's
    `PACK-01-RESULT.md` / `PACK-01-VERIFICATION.log` into
    `docs/handover/` as evidence, referenced below. A redundant root-level
    duplicate of `verify-and-package.yml` present in the archive (outside
    `.github/workflows/`) was not carried over, to avoid two copies of the
    same file.
  - Re-ran the complete offline verification suite on the repaired tree
    (section 5). All checks pass, including `test_no_required_paths_are_missing`
    for the first time (both lock files now genuinely exist).
  - Confirmed the repair does not affect the TypeScript/Next.js results
    already recorded in `PACK-01-VERIFICATION.log`: none of the restored
    files (canon doc, CI/governance files, `.prettierignore`,
    `.python-version`, `.secrets.baseline`) are read by `tsc`, ESLint,
    the frontend test suite, or `next build`; the only check any of them
    affects is `npm run format:check` (Prettier), which was re-run locally
    on the repaired tree and passes (section 5).
  - Logged the detection gap this incident exposed —
    `scripts/check_repository.py` checks path existence only, not
    non-emptiness — as a recommendation for the owner to decide on, in
    `docs/review/OPEN_QUESTIONS.md` (item 8). Not implemented unilaterally
    this pass, to avoid an unrequested scope/architecture decision.

## 1. Summary

CLAUDE-PACK-01 is complete and verified. All required paths, Python
tooling (Ruff format/lint, mypy, pytest), Prettier, JSON/YAML validity, and
the repository-hygiene scripts pass in this sandbox on the repaired tree.
TypeScript/Next.js checks (typecheck, ESLint, TypeScript tests, `next
build`) were verified on GitHub Actions with real PyPI/npm access and are
unaffected by the repair (section 0). `uv.lock` and `package-lock.json` are
genuine, tool-generated, and committed.

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

This sandbox's own network egress is unchanged and still blocks
`pypi.org` / `files.pythonhosted.org` / `registry.npmjs.org` (`403
host_not_allowed`), reconfirmed read-only this pass. That is why lock-file
generation and the frontend build were done on GitHub Actions
(`.github/workflows/verify-and-package.yml`), per `GITHUB_ACTIONS_START.md`,
rather than in this session. Python 3.12 / Node 22 / Next.js remain the
approved stack throughout — recorded above from both this sandbox and from
`PACK-01-VERIFICATION.log`'s GitHub Actions run.

## 3. Lock files

```text
uv.lock:            PRESENT — genuine, uv-generated
package-lock.json:  PRESENT — genuine, npm-generated
```

SHA-256 (repaired, currently-committed tree):

```text
3ace36a8ced7987525a83798689d1c0728fa64f08c026787b8736d46bebfbcb7  uv.lock
1335af3003cd0547a540bdf63554299e5032ae9d8c626bc53102b2090b4e5bb4  package-lock.json
```

Neither file was hand-edited after extraction from the archive.

## 4. Files added or changed this pass

- `uv.lock`, `package-lock.json` (new) — genuine output of `uv lock` /
  `npm install`, taken from the owner's GitHub Actions artifact.
- `.github/workflows/verify-and-package.yml` (new) — the owner's
  `workflow_dispatch` job: generates both lock files, runs `make verify`,
  packages the repository regardless of outcome. Kept as a permanent,
  reusable way to verify this repository from any environment with normal
  internet access.
- `GITHUB_ACTIONS_START.md` (new) — one-click instructions for the workflow
  above.
- `docs/handover/PACK-01-RESULT.md`, `docs/handover/PACK-01-VERIFICATION.log`
  (new) — the raw result/log produced by that GitHub Actions run, kept as
  evidence.
- `docs/review/OPEN_QUESTIONS.md` — added item 8 (the
  existence-vs-content detection gap this incident exposed).
- `docs/review/KNOWN_LIMITATIONS.md` — updated: lock files and frontend
  build are no longer "missing" / "not executed"; added a note on the
  archive-integrity incident and its resolution.
- `LOCAL_VERIFICATION.md` — added a status note pointing to this
  revision and to `GITHUB_ACTIONS_START.md`; the install/build procedure
  itself is unchanged and still valid for future re-verification.
- `README.md` — status line now reads PACK-01 PASS; documentation list
  links `GITHUB_ACTIONS_START.md` / `verify-and-package.yml`.
- `docs/handover/PACK-01-REPORT.md` — this revision.
- **Not changed**: `docs/canonical/TZ-00-domain-event-canon.md`,
  `.github/workflows/ci.yml`, `.github/pull_request_template.md`,
  `.github/ISSUE_TEMPLATE/*.yml`, `.prettierignore`, `.python-version`,
  `.secrets.baseline` — all restored to, and byte-identical with, their
  revision-3 originals (section 0).

No business modules, Docker, PostgreSQL, event bus, authentication, or
deployment configuration was added. Scope was not expanded beyond what
section 0 describes.

## 5. Commands executed this pass, and results

```text
✅ python3.12 scripts/check_repository.py
   → OK: all 72 required paths are present.

✅ python3.12 scripts/check_forbidden_files.py
   → OK: no forbidden paths found.

✅ python3.12 scripts/verify_versions.py
   → OK: all version sources are consistent.

✅ ruff format --check .
   → 13 files already formatted

✅ ruff check .
   → All checks passed!

✅ PYTHONPATH=packages/python/epd2-core/src mypy .
   → Success: no issues found in 13 source files

✅ PYTHONPATH=packages/python/epd2-core/src pytest -v
   → 14 passed, 0 failed
     (test_no_required_paths_are_missing now passes — both lock files
     genuinely present for the first time)

✅ prettier --check .   (repository-wide, respecting the restored
   .prettierignore, which excludes the canon file)
   → All matched files use Prettier code style!

✅ JSON/YAML parse validation (every *.json / *.yml / *.yaml)
   → all files parse without error

✅ git status --short — clean tree aside from the intentional additions
   in section 4; no source file left modified by any check itself

Verified on GitHub Actions (real PyPI/npm access), unaffected by the
repair per section 0's reasoning — see docs/handover/PACK-01-VERIFICATION.log:
✅ npm run typecheck --workspace=packages/typescript/epd2-types  → no errors
✅ npm run typecheck --workspace=frontend/web-shell              → no errors
✅ npm run lint --workspace=frontend/web-shell (ESLint)          → no errors
✅ npm run test --workspace=packages/typescript/epd2-types       → 3 passed
✅ npm run test --workspace=frontend/web-shell                   → 2 passed
✅ npm run build --workspace=frontend/web-shell (next build)     → succeeded,
   4 routes generated, "Compiled successfully in 4.3s"
```

## 6. Test results

- **Python** (`pytest`): 14 passed, 0 failed. Full green for the first
  time — both lock files now genuinely exist.
- **Ruff format / lint**: clean.
- **mypy**: clean (13 source files).
- **Repository structure**: 72 of 72 required paths present.
- **Forbidden-files check**: clean.
- **Version consistency**: clean.
- **Prettier / YAML / JSON**: clean, including the canon file (excluded
  via the restored `.prettierignore`).
- **TypeScript typecheck, TypeScript tests, frontend tests, frontend
  build, frontend ESLint**: all passed on GitHub Actions
  (`docs/handover/PACK-01-VERIFICATION.log`); not re-executed in this
  sandbox (still network-restricted), but confirmed unaffected by this
  pass's repair (section 0).

## 7. Security checks

Unchanged and reconfirmed: no `.env`, private keys, `.pem`/`.key` files
outside allowed fixtures, or real database files present; no
`node_modules`/`.venv`/cache directories committed; `.secrets.baseline`
(restored, unmodified) has no findings; `CODEOWNERS` uses documented
placeholders; `LICENSE` is the required placeholder; no secrets or
credentials introduced. `.secrets.baseline` and `.python-version`, which
were missing from the delivered archive, are confirmed present and
unmodified in the repaired tree.

## 8. Open questions

See `docs/review/OPEN_QUESTIONS.md` — item 8 (new this revision) covers
the existence-vs-content detection gap this incident exposed in
`scripts/check_repository.py`. All other items unchanged.

## 9. Known limitations

See `docs/review/KNOWN_LIMITATIONS.md` (updated this revision). No
business modules, database, event bus, authentication, or deployment
configuration exist yet — unchanged from prior revisions.

## 10. Deviations (complete list — nothing hidden)

1. `.github/workflows/verify-and-package.yml` and `GITHUB_ACTIONS_START.md`
   (new, this pass) — added by the owner to solve the sandbox's network
   restriction; kept as a permanent, reusable verification path.
2. `docs/handover/PACK-01-RESULT.md` / `PACK-01-VERIFICATION.log` (new,
   this pass) — evidence from the GitHub Actions run; not part of the
   pack's literal file tree, kept for auditability.
3. The archive that produced items 1–2 also contained an unrelated
   integrity problem (reformatted canon file, five emptied governance
   files, three missing safety files) that was detected before acceptance
   and repaired from the untouched revision-3 tree — see section 0 for
   the complete account. Nothing from that corrupted state was kept.
4. `.python-version`, `.secrets.baseline`, `.prettierignore` — unchanged
   from earlier revisions; reconfirmed present and byte-identical after
   the repair.
5. `scripts/check_forbidden_files.py` is git-aware (revision 2 bug fix,
   unchanged).
6. `LOCAL_VERIFICATION.md` (revision 3) — unchanged procedure, status note
   added pointing here.
7. `pyproject.toml` dev dependency upper bounds (revision 3) — unchanged.
8. `frontend/web-shell/package.json`'s `@eslint/eslintrc` addition
   (revision 3) — unchanged; confirmed working end-to-end by the real
   `npm run lint` / `next build` in `PACK-01-VERIFICATION.log`.
9. Everything else follows CLAUDE-PACK-01 without further deviation. No
   Docker, PostgreSQL, Keycloak, event bus, API Gateway, authentication,
   business services, or deployment was added.

## 11. Files requiring owner configuration

- `CODEOWNERS` — replace placeholder team aliases once real GitHub teams exist.
- Repository URL / GitHub organization settings.
- `LICENSE` — pending an actual license decision.
- Whether to act on `docs/review/OPEN_QUESTIONS.md` item 8 (strengthening
  `scripts/check_repository.py` against silent content truncation) is an
  owner decision, not made unilaterally this pass.

## 12. Readiness conclusion

```text
PACK-01 PASS
```

All Definition-of-Done items this repository can verify are met: required
structure, formatting, linting, type checking, and tests pass in this
sandbox (section 5); TypeScript/Next.js checks and a real `next build`
pass on GitHub Actions with genuine, tool-generated lock files (section 5,
`docs/handover/PACK-01-VERIFICATION.log`); the canon file is confirmed
byte-identical to the original placed at project start
(`7ffdd1b1e0a22412686b4ec508441924`); no verification check was weakened
to reach this result — the one integrity problem found (section 0) was in
a delivered archive, not in this repository's rules, and was resolved by
restoring the affected files from the untouched, already-verified
revision-3 tree rather than by relaxing any check.
