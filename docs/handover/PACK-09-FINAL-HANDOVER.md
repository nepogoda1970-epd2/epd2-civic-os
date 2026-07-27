# PACK-09 — final handover note

**PACK-09 IMPLEMENTATION 0.9.0 — EXTERNAL CI PASS**

Date: 2026-07-26
Archive: `epd2-civic-os-PACK-09-IMPLEMENTATION-0.9.0-PASS.zip`

---

## 1. External CI passed

The complete verification pipeline was executed outside this repository's
authoring environment, on **GitHub Actions / ubuntu-latest**, Python
3.12, Node.js 22, against the locked toolchain (`uv sync --all-groups
--frozen`, `npm ci`).

| Check                    | Result                                                                                  |
| ------------------------ | --------------------------------------------------------------------------------------- |
| Required paths           | **556**                                                                                 |
| Forbidden paths          | **none**                                                                                |
| Prettier                 | **PASS**                                                                                |
| Ruff format              | **PASS**                                                                                |
| Ruff lint                | **PASS**                                                                                |
| mypy                     | **PASS** — all included services, incl. `organization-service` and `compliance-service` |
| Python tests             | **2659 passed, 4 skipped, 0 failed**                                                    |
| TypeScript package tests | **3 passed**                                                                            |
| Frontend tests           | **11 passed**                                                                           |
| Next.js production build | **PASS**                                                                                |
| Overall                  | **All checks passed**                                                                   |

Evidence, verbatim, in this archive:

- `docs/handover/PACK-09-EXTERNAL-CI-VERIFICATION.log` — the runner's full
  output.
- `docs/handover/PACK-09-EXTERNAL-CI-VERIFICATION-RESULT.md` — the
  runner's own summary.

This closes the limitation every earlier PACK-09 round carried: the
authoring sandbox had no egress to `pypi.org` or `registry.npmjs.org`, so
the frozen install and the whole npm half of the pipeline could not be
run there. Both have now been executed under the pinned versions.

## 2. No source changes after the verified commit

The archive contains the **exact tree that CI verified**, with only
documentation and status cleanup applied on top. Specifically:

**Unchanged, byte-for-byte, from the verified tree:**

- every file under `services/`, `packages/`, `frontend/`, `tests/`,
  `scripts/` and `contracts/`
- `pyproject.toml`, `package.json`, `uv.lock`, `package-lock.json`,
  `Makefile`, `conftest.py`
- `docs/canonical/TZ-00-domain-event-canon.md` and
  `docs/canonical/canon-version.json` — SHA-256
  `a16341a66ce39514e6d8cd6d7a6dde8fc37b0430e3e9ddd7bfd284b116cb9072` and
  `22c2eac62ce10b276328ee3fb63b4bf1ef2adeaac46607040ffd38299960f3f5`
  respectively, identical to the verified tree

**Changed — documentation and status only:**

- `docs/handover/PACK-09-IMPLEMENTATION-REPORT.md` — section 3 replaced
  with the external CI results and made the single verification record;
  the sandbox-substitute verification sections and the two superseded
  test totals removed, so no two figures in the document disagree.
- `docs/handover/PACK-09-KNOWN-LIMITATIONS.md` — the "verification
  limitations" section replaced with what a passing CI run does and does
  not establish. Limitations 1–8 are unchanged and still stand.
- `LOCAL_VERIFICATION.md` — the PACK-09 egress note marked resolved,
  keeping the two offline corrections CI confirmed (the hand-corrected
  `uv.lock`, and the Prettier version agreement).
- `README.md`, `CHANGELOG.md`, `docs/packs/PACK-09-IMPLEMENTATION.md` —
  status wording updated from candidate to verified.
- Added: the two CI evidence files above, and this note.

No architecture, domain scope, contract, schema, API, event, reason code,
test or implementation logic was touched.

**Artifacts removed** from the delivered tree: a stale nested
`epd2-civic-os/` copy of an older snapshot, the nested verification ZIP,
`.mypy_cache`, `.ruff_cache`, `.pytest_cache`, `.hypothesis`,
`__pycache__`, and `.pyc` files. No `.git`, `.venv`, `node_modules`,
`.next`, coverage output or IDE files were present.

The three documentation files added here are deliberately **not**
registered in `scripts/check_repository.py`, so the required-path count
stays at the verified **556** rather than drifting from the number CI
checked.

## 3. Self-consistency re-checked in this environment

Re-run against the assembled archive before packaging:

| Check                              | Result                                                  |
| ---------------------------------- | ------------------------------------------------------- |
| `scripts/check_repository.py`      | **PASS** — 556 required paths                           |
| `scripts/check_forbidden_files.py` | **PASS** — no forbidden paths                           |
| `scripts/verify_versions.py`       | **PASS** — canon `0.7.0`, repository `0.9.0` everywhere |
| `ruff check .`                     | **PASS**                                                |
| `ruff format --check .`            | **PASS**                                                |
| `mypy` (every Makefile group)      | **PASS**                                                |
| `pytest`                           | **PASS** — 2652 passed, 5 skipped                       |

The local figure differs from CI's 2659/4 for one reason, and only one:
`hypothesis` is not installable in this environment, so
`tests/contract/test_property_based.py` is skipped here instead of
contributing its 7 tests. `2652 − 1 skip + 7 = 2659`, and `5 − 1 = 4`.
The two runs are the same suite. **The CI figures are the authoritative
ones**, because they were produced under the pinned toolchain.

Markdown edited in this round was normalised to Prettier's table and
blank-line rules using a checker first validated against the verified
tree (it reports zero changes across every file CI's `prettier --check`
already accepted).

## 4. Preserved

- `REPOSITORY_VERSION` = **0.9.0**
- `CANON_VERSION` = **0.7.0**
- canon document and `canon-version.json` checksums, unchanged
- ADR-038 … ADR-043, all `accepted`

## 5. Status

PACK-09 is **ready for final acceptance review**.

This is a statement about implementation and verification. It is **not** a
statement that the system is production-ready, deployed, or legally
activated, and nothing in this archive asserts that any retention
schedule, deemed-service rule, notice method, deadline computation,
processing basis or arbitration decision satisfies the GDPR, the BDSG,
the Parteiengesetz or any other law. Those remain human determinations
made outside this system. The scope boundaries and partial guarantees
that survive a passing pipeline are enumerated in
`docs/handover/PACK-09-KNOWN-LIMITATIONS.md`.
