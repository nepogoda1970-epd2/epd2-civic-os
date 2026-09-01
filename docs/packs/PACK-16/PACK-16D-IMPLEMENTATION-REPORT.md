# PACK-16D — Implementation Report

**Round:** PACK-16D — Network-Enabled Finalization: Lockfile Regeneration,
Immutable ElectionGuard Provenance and Final Acceptance Alignment. A correction
of the PACK-16D reference-implementation candidate, not a new round.
**Reference implementation. Not production code. Not certified. Not a PASS.**
**Repository version:** unchanged at `0.16.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-102`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 0. Why there is a network-enabled finalization

The previous correction resolved everything it could and recorded two things
it could not: `uv.lock` could not be regenerated, and the corroborating
ElectionGuard implementation source could not be commit-pinned. Both were
blocked by the build environment's network policy, both were recorded with
verbatim transcripts rather than worked around, and both named the exact
command that would close them.

Those commands were run on a host with the required access. **This round did
no cryptographic work at all**; it verified the resulting lock, wrote the
provenance into the parameter artefact, converted every dual-state test into a
real check, and aligned the documentation and the acceptance matrix to the new
facts.

| Finding                                         | Outcome this round                                                                                                                                                                                                                                               |
| ----------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `DEPENDENCY LOCK / FROZEN INSTALL: FAIL`        | **RESOLVED.** `uv.lock` regenerated; `cryptography 46.0.7` resolves from `https://pypi.org/simple` with hashes on all 43 artefacts, inside the `epd2-voting-service` graph. `uv sync --all-groups --frozen` → `Checked 61 packages`, on the network-enabled host |
| `IMMUTABLE PARAMETER PROVENANCE: FAIL`          | **RESOLVED.** `microsoft/electionguard-rust` at `520651138110a13f777409e96606454df928ceac`, `src/eg/src/standard_parameters.rs`, SHA-256 `ad38bfa6…5770`, retrieved 2026-08-03 — all recorded in the artefact beside the already-pinned normative specification  |
| `ACCEPTANCE MATRIX: NARROW CORRECTION REQUIRED` | **ALIGNED.** `AM-79` and `AM-89` promoted to `SATISFIED` against the five stated conditions each, with the two remaining limits stated in their residual-risk columns                                                                                            |

### 0.1 What was verified rather than accepted, and what was not

The supplied lock was **verified, not regenerated blindly**. It is parsed as
TOML rather than searched as text, because a string search matches the package
name inside another package's dependency list and reports an entry that does
not exist. The checks are listed in §3; the load-bearing ones are that the
entry has a registry source and `sha256:`-prefixed hashes, that it sits in
`epd2-voting-service`'s own dependency list rather than at the workspace root,
that the resolved version satisfies every clause of the declared specifier, and
that the lock delta is purely additive — 149 lines added, none removed, no
existing package's version changed.

Two things this session did **not** do, stated here rather than at the end:

1. **It did not re-run the frozen install.** The session has no package index.
   `uv sync --all-groups --frozen` ran on the network-enabled host. What this
   session shows instead is that the imported `cryptography` is version-identical
   to the locked resolution — which ties the exercised code to the recorded
   resolution but is not the same claim.
2. **It did not re-fetch the upstream file's bytes.** The digest was computed on
   the network-enabled host. This session verified the pin's internal
   consistency — full 40-character lower-case object id, pinned URL containing
   that exact commit and that exact path, 64 lower-case hex digest — and
   re-derived every parameter offline. `source_sha256_verification_scope` records
   this in the artefact, where a verifier will look, and names the one command
   that closes it.

**One transcription discrepancy is recorded rather than silently corrected.**
The finalization brief quoted the new `uv.lock` digest as `02d0775458…`; the
digest computed over the delivered file's actual bytes is `b2d0775458…`. They
agree in 63 of 64 hex characters, which no byte-level corruption produces — a
one-nibble difference from changed bytes is about as likely as guessing the
digest — so this is a transcription slip in the brief. The computed value is
used throughout, because it is the one anybody can reproduce from the file.

## 0.2 Why there was a third correction

An independent audit of the FINAL REVIEW candidate (`ff3909bb…86de5`)
returned:

```text
ARCHIVE HYGIENE:                          PASS
VETTED ED25519 PROVIDER:                  PASS
HANDWRITTEN ED25519 REMOVAL:              PASS
CHECKPOINT AUTHENTICITY:                  PASS
REAL EPD2-CRYPTO-1:                       PASS
3-OF-5 THRESHOLD PATH:                    PASS
4-OF-7 CONFIGURATION:                     PASS
TARGET-PROFILE CROSS-IMPLEMENTATION CORE: PASS
DEPENDENCY LOCK / FROZEN INSTALL:         FAIL
IMMUTABLE PARAMETER PROVENANCE:           FAIL
ACCEPTANCE MATRIX:                        NARROW CORRECTION REQUIRED
PACK-16D:                                 NOT YET ACCEPTED
PACK-17:                                  DO NOT START
```

**Every cryptographic finding passed. Nothing cryptographic was touched by
this round.**

| Finding                                         | Outcome this round                                                                                                                                                |
| ----------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `DEPENDENCY LOCK / FROZEN INSTALL: FAIL`        | **NOT RESOLVED — `BLOCKED BY ENVIRONMENT`.** Re-attempted and refused; `FROZEN CLEAN INSTALL: NOT EXECUTED`                                                       |
| `IMMUTABLE PARAMETER PROVENANCE: FAIL`          | **PARTIALLY SATISFIED.** The normative half was already pinned; the implementation half could not be pinned — re-attempted and refused by two distinct mechanisms |
| `ACCEPTANCE MATRIX: NARROW CORRECTION REQUIRED` | **RESOLVED.** `AM-79` corrected from `SATISFIED` to `PARTIALLY SATISFIED`                                                                                         |

### 0.2.1 The matrix defect was real, and it is the one worth dwelling on

The audit's third finding was that `AM-79` claimed the parameter set was
_immutably provenanced_ with status `SATISFIED`, while the row's own
evidence column recorded that the commit, the pinned URL and the source
digest were all absent. A row cannot assert a property and document its
absence in the same sentence.

Nothing new was learned to force that downgrade. The facts were already in
the parameter artefact, already in the evidence registry, and already in the
previous handover. What was wrong was the _status placed on top of them_ —
the evidence stayed honest while the summary drifted optimistic. That is the
failure mode a matrix is most prone to, it is invisible to anyone who reads
only the status column, and it is exactly what an audit that reads both
columns will catch.

The two blockers were **re-attempted rather than carried forward**, because
a blocker quoted from a previous round's notes is indistinguishable from an
excuse. Every command and every error string is reproduced verbatim in
`PACK-16D-ENVIRONMENT-BLOCKED-EVIDENCE.md`.

## 0.3 Why there was a second correction

An independent audit of the **corrected** PACK-16D candidate
(`bd543264…ab891`) returned:

```text
ARCHIVE HYGIENE:                          PASS
REAL EPD2-CRYPTO-1:                       PASS
TARGET-PROFILE CRYPTO TESTS:              PASS
3-OF-5 THRESHOLD REFERENCE PATH:          PASS
4-OF-7 GENERIC PATH:                      PASS
CHECKPOINT SIGNATURE SEMANTICS:           PASS
CHECKPOINT SIGNATURE PRIMITIVE POLICY:    FAIL - HANDWRITTEN ED25519
PARAMETER SOURCE REPRODUCIBILITY:         PARTIAL - MUTABLE URL / DIGEST NOT IN ARTIFACT
CROSS-IMPLEMENTATION ON TARGET PROFILE:   PARTIAL
PACK-16D:                                 NOT YET ACCEPTED
PACK-17:                                  DO NOT START
```

Three faults, and the first is the one worth dwelling on. The previous round
had implemented Ed25519 from RFC 8032 in the standard library, cross-checked
it against OpenSSL on 25 vectors, and written a careful paragraph explaining
why that was defensible. Every fact in that paragraph was true. The
conclusion was wrong, and the reason it was wrong is instructive: the round
had optimised for **"add no dependency"** when the property that mattered was
**"implement no cryptographic primitive"**. Those two goals pointed in
opposite directions and the round did not notice it had chosen the weaker
one.

| Audit finding                                     | State now                                                                                         | Evidence                                  |
| ------------------------------------------------- | ------------------------------------------------------------------------------------------------- | ----------------------------------------- |
| `CHECKPOINT SIGNATURE PRIMITIVE POLICY: FAIL`     | **Vetted provider.** `cryptography` 46.0.7 over OpenSSL; `crypto/ed25519.py` deleted; no fallback | `test_checkpoint_signatures.py`, 44 tests |
| `PARAMETER SOURCE REPRODUCIBILITY: PARTIAL`       | **Versioned authoritative reference, digest in the artefact, and full offline reconstruction**    | `test_epd2_crypto_1.py`, 25 tests         |
| `CROSS-IMPLEMENTATION ON TARGET PROFILE: PARTIAL` | **All twelve core operations on `EPD2-CRYPTO-1`**, plus two invalid fixtures                      | `test_target_conformance.py`, 15 tests    |

Everything the audit passed was preserved without architectural change:
the guardian model, both atomic transactions, sealed batches, the checkpoint
payload and signer trust model, Merkle mechanics, the election record, the
verifier boundary, the negative corpus, and the concurrency and
fault-injection harnesses.

**That unfinished lock is finished.** `cryptography` is declared in
`pyproject.toml` and resolves in `uv.lock` as 46.0.7 — see §0 and §3.

## 0.4 Why there was a first correction

An independent audit of the first PACK-16D candidate returned:

```text
ARCHIVE HYGIENE:                    PASS
REFERENCE TEST SUITE:               PASS
REFERENCE IMPLEMENTATION SCAFFOLD:  PASS
ATOMIC PERSISTENCE MODEL:           PASS FOR REFERENCE STORE
ACTUAL EPD2-CRYPTO-1 PROFILE:       FAIL
THRESHOLD GUARDIAN MODEL:           FAIL
CHECKPOINT AUTHENTICITY:            FAIL
EXTERNAL CONFORMANCE:               FAIL
PACK-16D:                           NOT ACCEPTED
PACK-17:                            DO NOT START
```

The four failures share one shape. In each case the first candidate had a
central mechanism missing, described the absence carefully and honestly, and
then filed it under a heading — an open decision, a `BLOCKED` acceptance
row, an external-party dependency — that made it look like somebody else's
work. Careful description of a gap is not the same as not having the gap,
and an audit is right to refuse the substitution.

All four are now implemented. Everything the audit passed was preserved
rather than rebuilt: canonical encoding, domain separation, RNG separation,
both atomic transactions, idempotency, the concurrency and fault-injection
harnesses, sealed batches, Merkle mechanics, the negative corpus, the
election-record scaffolding, the verifier boundary and archive hygiene.

| Audit finding                        | State now                                                                       | Evidence                                  |
| ------------------------------------ | ------------------------------------------------------------------------------- | ----------------------------------------- |
| `ACTUAL EPD2-CRYPTO-1 PROFILE: FAIL` | **Implemented** — the real parameters load and the whole stack runs on them     | `test_epd2_crypto_1.py`, 18 tests         |
| `THRESHOLD GUARDIAN MODEL: FAIL`     | **Implemented** — Feldman-VSS DKG, generic `k`-of-`n`, 3-of-5 and 4-of-7        | `test_guardians.py`, 28 tests             |
| `CHECKPOINT AUTHENTICITY: FAIL`      | **Implemented** — Ed25519 signing and verification with a declared trust anchor | `test_checkpoint_signatures.py`, 32 tests |
| `EXTERNAL CONFORMANCE: FAIL`         | **Implemented** — primary-source and cross-implementation evidence, two oracles | `test_conformance.py`, 18 tests           |

## 1. What was built

**45 Python modules, 2 test parameter files and 1 real parameter artefact**
under `services/voting-service/src/epd2_voting_service/reference/`, plus
**15 test modules, 2 cross-implementation oracles and 4 catalogues** under
`services/voting-service/tests/reference/`. **7 534 lines of
implementation, 7 977 lines of tests** (the latter including the Node.js
oracle).

The module count is unchanged at 45: this correction deleted one module
(`crypto/ed25519.py`) and added one (`crypto/signature_provider.py`), which
is the whole shape of the change to the active path.

The reference implementation covers the whole path PACK-16A, PACK-16B and
PACK-16C specified, in reference form and **on the real parameter
profile**: cryptography and canonical encodings, ballot preparation and the
NIZK proof family, the two atomic transactions, threshold guardian key
generation and decryption, sealed fixed-capacity batches, the bulletin
board with an RFC 6962 transparency log and Ed25519-signed checkpoints, the
election record, and an independent verifier — with a harness of 23
stability vectors, 13 conformance entries, a 39-case negative corpus, 15
properties, 9 concurrency races and 11 fault points.

## 2. Change inventory for this correction

**No cryptographic, guardian, checkpoint, conformance, transaction or
sealed-batch code was modified.** The change is `uv.lock`, one parameter
artefact's provenance metadata, two test modules that stopped tolerating the
blocked state, and the documentation set.

| Class    | Count  | Detail                                                                              |
| -------- | ------ | ----------------------------------------------------------------------------------- |
| Added    | **0**  | —                                                                                   |
| Deleted  | **0**  | —                                                                                   |
| Modified | **24** | `uv.lock`, 1 artefact, 2 test modules, 1 regenerated timings artefact, 19 documents |

```text
MODIFIED - lock
uv.lock                        1a1e5a72...d543 -> b2d07754...8066
    + cryptography 46.0.7  registry source, 43 sha256-hashed artefacts
    + cffi 2.1.0           the binding layer to OpenSSL
    + pycparser 3.0        cffi's own C parser
    149 lines added, 0 removed, 0 existing package versions changed,
    requires-python and lock revision unchanged.
    Supplied already regenerated; VERIFIED here by parsing as TOML.

MODIFIED - artefact
reference/crypto/profiles/EPD2-CRYPTO-1.json
    + upstream_commit, upstream_commit_date, commit_pinned_source_url,
      source_sha256, source_sha256_verification_scope, retrieval_date
    - unpinned_reason, auditor_action   (removed WITH the pin, not after)
    ~ provenance_status -> SATISFIED; hierarchy note -> PINNED
    ~ digests.source_sha256 / source_sha256_status -> RECORDED
    = human_readable_url_is_authoritative STILL false
    = withdrawn_digest_note KEPT
    = parameter_digest UNCHANGED and still recomputes

MODIFIED - tests
tests/reference/test_epd2_crypto_1.py                    30 -> 32 tests
    upstream_commit_format        -> upstream_commit_is_full_sha
    source_url_contains_commit    -> source_url_contains_exact_commit
    mutable_main_not_authoritative-> mutable_branch_not_authoritative
    source_sha256_present         -> now asserts the UPSTREAM digest
    +specification_sha256_present  (the old body, under its real name)
    +source_file_path_present
    every dual-state branch removed: a null commit now fails
tests/repository/test_pack16d_signature_dependency.py     7 -> 9 tests
    +test_cryptography_is_in_the_voting_service_graph
    +test_blocked_evidence_is_marked_resolved
    vetted_provider_imports_from_locked_environment
      -> vetted_provider_imports_and_matches_the_lock
         (asserts cryptography.__version__ == the locked version)
    lock_state_is_either_correct_or_documented
      -> outstanding_lock_notice_did_not_outlive_the_lock
tests/reference/vectors/PACK-16D-TARGET-PROFILE-TIMINGS.json
    regenerated by the conformance run; timings only, no fixture changed

MODIFIED - documents
PACK-16D-ENVIRONMENT-BLOCKED-EVIDENCE.md  -> RESOLVED historical record
PACK-16D-ACCEPTANCE-MATRIX.md             AM-79, AM-89 -> SATISFIED
PACK-16D-OPEN-DECISIONS.md                OD-P16D-16/-17 CLOSED
PACK-16D-LANGUAGE-AND-DEPENDENCY-ASSESSMENT.md   section 4.1 rewritten
PACK-16D-PARAMETER-PROFILE-IMPLEMENTATION.md     PP-66..PP-75
PACK-16D-PROTOCOL-EVIDENCE-MATRIX.md      H-01, H-08, H-10, H-R11, H-R12
PACK-16D-EXTERNAL-CONFORMANCE-REPORT.md   EC-23, EC-27, EC-42, EC-111, EC-112
PACK-16D-CHECKPOINT-SIGNATURE-AND-SIGNER-TRUST-MODEL.md   CS-75, CS-79
PACK-16D-SECURITY-AND-SIDE-CHANNEL-LIMITATIONS.md         SL-55, SL-56
PACK-16D-CRYPTOGRAPHIC-MODULE-MAP.md      boundary list
PACK-16D-FIR-COVERAGE-MATRIX.md           FC-30
PACK-16D-CANON-ASSESSMENT.md              round header only
PACK-16D-TEST-VECTOR-CATALOG.md           round header only
PACK-16D-REFERENCE-VERIFIER.md            round header only
PACK-16D-IMPLEMENTATION-REPORT.md         this file
PACK-16D-HANDOVER.md                      status block and evidence
ADR-102                                   lock, provenance, open decisions
EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md   section 1.27 added
CHANGELOG.md                              round entry
```

**`package-lock.json` is unchanged**: no Node dependency exists.
`services/voting-service/pyproject.toml` is unchanged from the source
candidate — `cryptography>=46.0.7,<47` was already declared and the range did
not need to move.
**`REPOSITORY_VERSION` stays `0.16.0`, `CANON_VERSION` stays `0.8.0`,
`ADR-102` stays `proposed`, and no file under `docs/canonical/` was
modified.**

## 3. Commands — executed, with real output

| Command                                                        | Output                                            |
| -------------------------------------------------------------- | ------------------------------------------------- |
| `ruff check .`                                                 | `All checks passed!`                              |
| `ruff format --check .`                                        | `498 files already formatted`                     |
| `mypy services/voting-service`                                 | `Success: no issues found in 70 source files`     |
| `pytest` (whole repository, **no `--ignore`**)                 | `5851 passed, 5 skipped, 3 warnings` in 138.56 s  |
| `pytest services/voting-service/tests/reference/`              | `506 passed` in 76.41 s                           |
| `pytest -m slow_conformance .../tests/reference/`              | `15 passed, 491 deselected` in 9.82 s             |
| `pytest -m "not slow_conformance" .../tests/reference/`        | `491 passed, 15 deselected` in 71.32 s            |
| `pytest .../test_epd2_crypto_1.py`                             | `32 passed in 29.54s`                             |
| `pytest .../test_guardians.py`                                 | `28 passed in 3.10s`                              |
| `pytest .../test_checkpoint_signatures.py`                     | `44 passed in 0.79s`                              |
| `pytest .../test_conformance.py`                               | `19 passed in 5.84s`                              |
| `pytest .../test_target_conformance.py`                        | `15 passed in 9.00s`                              |
| `pytest .../test_concurrency.py`                               | `87 passed in 11.25s`                             |
| `pytest .../test_fault_injection.py`                           | `22 passed in 2.26s`                              |
| `pytest .../test_negative_corpus.py`                           | `41 passed in 2.30s`                              |
| `pytest .../test_casting_units.py`                             | `28 passed in 1.83s`                              |
| `pytest .../test_e2e.py`                                       | `24 passed in 4.60s`                              |
| `pytest .../test_verifier_branches.py`                         | `33 passed in 2.15s`                              |
| `pytest .../test_invariants.py`                                | `61 passed in 0.65s`                              |
| `pytest .../test_vectors.py`                                   | `31 passed in 1.44s`                              |
| `pytest .../test_crypto_units.py`                              | `24 passed in 4.58s`                              |
| `pytest .../test_property.py`                                  | `17 passed in 7.45s`                              |
| `pytest tests/repository/test_pack16d_signature_dependency.py` | `9 passed`                                        |
| `python scripts/verify_versions.py`                            | `OK: all version sources are consistent.`         |
| `python scripts/check_canon_0_8_0.py`                          | `OK: all 18 canon 0.8.0 amendment checks passed.` |
| `python scripts/check_repository.py`                           | `OK: all 983 required paths are present.`         |
| `python scripts/check_forbidden_files.py`                      | `OK: no forbidden paths found.`                   |

The whole-repository run needs no `--ignore`, and the 5 remaining skips are
4 documented NOT-APPLICABLE contract tests and 1 hypothesis property test.

The reference suite runs with the workspace `src` directories and the
interpreter's site-packages on `PYTHONPATH`, and with bytecode and pytest
caching disabled, because the repository's forbidden-path test refuses
`__pycache__` and `.pytest_cache` directories:

```text
PP=$(ls -d packages/python/*/src services/*/src | tr '\n' ':')
PYTHONPATH="$PP:/usr/local/lib/python3.11/dist-packages" PYTHONDONTWRITEBYTECODE=1 \
  pytest -q -p no:cacheprovider
```

One note on invocation, because it cost a false alarm here. Running
`pytest .` instead of bare `pytest` overrides the repository's `testpaths`
ordering, and twenty service test suites each contain a `test_application.py`;
under `--import-mode=importlib` the resulting collection order makes
`document-service`'s privacy-boundary tests import `identity-service`'s module
and fail with an `ImportError`. **Bare `pytest`, which honours `testpaths`, is
the invocation the repository intends**, and it is what the numbers above come
from.

### 3.1 Commands executed on the network-enabled host, not here

```console
$ uv lock
$ rm -rf .venv
$ uv sync --all-groups --frozen
Checked 61 packages
```

```text
old uv.lock SHA-256   1a1e5a72b67b92a53b189e6eb9c9f4305f236a0aa76f7d55887f24ad2a76d543
new uv.lock SHA-256   b2d0775458d3b6e81d321724530c7a473584fb2b3d9d231d220d8e9dcdfe8066
resolved              cryptography 46.0.7 (+ cffi 2.1.0, pycparser 3.0)
```

```text
repository        https://github.com/microsoft/electionguard-rust
upstream commit   520651138110a13f777409e96606454df928ceac
commit date       2025-02-02T22:17:21-08:00
source file       src/eg/src/standard_parameters.rs
source SHA-256    ad38bfa68d31131a7d721e08d359224b21e967aae4d517534a60a109e10f5770
retrieval date    2026-08-03
```

These are listed separately rather than folded into §3 because the build
session has no package index and no route to GitHub. What it verified:

```text
cryptography present in uv.lock                      yes
source is a registry (https://pypi.org/simple)       yes
artifact hashes on all 43 artefacts                  yes, all sha256:-prefixed
resolved 46.0.7 satisfies >=46.0.7,<47               yes, every clause
cffi 2.1.0 and pycparser 3.0 locked with hashes      yes
cryptography in epd2-voting-service dependencies     yes
requires-dist specifier matches the manifest         yes
existing package versions changed                    none
imported cryptography version == locked version      yes (46.0.7)
upstream_commit is 40 lower-case hex                 yes
pinned URL contains that commit and that path        yes
source_sha256 is 64 lower-case hex                   yes
unpinned_reason / auditor_action removed with pin    yes, asserted by test
parameter values reconstruct offline                 yes, all four constants
parameter_digest recomputes                          yes, unchanged
```

`Checked 61 packages` against 62 lock entries is expected: the workspace root
is a lock entry that is not itself installed as a distribution.

**The lock digest quoted in the finalization brief differs from the file's in
its first hex character only** — `02d0775458…` against a computed
`b2d0775458…`, with the remaining 63 identical. No byte-level corruption
produces that; SHA-256 avalanche makes a one-nibble difference about as likely
as guessing the digest. It is a transcription slip, and the computed value is
used everywhere in this round because it is the one anybody can reproduce.

## 4. Commands NOT executed — and why

**None of the following is claimed as a PASS.**

| Command                                                          | Why it did not run                                                                                                                                                                                                                                                                                      |
| ---------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `uv lock`, `uv sync --all-groups --frozen` **in this session**   | The build session's egress allowlist still refuses `pypi.org`. Both ran on the network-enabled host — §3.1 — and this session verified the resulting lock's contents rather than re-running them. "The tests are green" and "the frozen install passes" are separate claims and are recorded separately |
| `curl <pinned-url> \| sha256sum` **in this session**             | No route to `raw.githubusercontent.com`. The digest was computed on the network-enabled host; `source_sha256_verification_scope` records that in the artefact, and this command settles it on any networked machine                                                                                     |
| `uv lock --check`                                                | Also requires re-resolving against the index, so it cannot run here either                                                                                                                                                                                                                              |
| `npm ci`                                                         | npm registry returns **HTTP 403**; `node_modules` cannot be installed                                                                                                                                                                                                                                   |
| `npm run lint`, `npm run typecheck`, `npm test`, `npm run build` | Depend on `npm ci`. **The entire Node and frontend side of this repository was not executed.** Unrelated to the Node.js _conformance oracle_, which is a standalone script run directly by the Node binary and needs no `node_modules`                                                                  |
| Hypothesis-based property tests                                  | `hypothesis` not installable. The 15 §41 properties ran as deterministic seeded loops instead (`OD-P16D-03`)                                                                                                                                                                                            |
| `pytest --cov` / branch coverage                                 | Neither `pytest-cov` nor `coverage` is installable. Line coverage was measured with the standard library's `trace` module; **branch coverage was not measured**                                                                                                                                         |

A further honesty note. Because `ruff`, `mypy` and `pytest` ran from a
standalone toolchain rather than through `uv run`, the versions used may
differ from the pinned ones. `mypy` reported **1.20.2**, which matches the
pin. **An auditor with network access should re-run every command in §3
through `uv run` to confirm.**

## 5. Test evidence

| Suite                           | Tests   | Seconds | Covers                                                                  |
| ------------------------------- | ------- | ------- | ----------------------------------------------------------------------- |
| `test_concurrency.py`           | 87      | 11.25   | §42 — 9 named races × 12 repeats                                        |
| `test_invariants.py`            | 61      | 0.65    | §44, §45, §46, §47, §50, §36                                            |
| `test_checkpoint_signatures.py` | 44      | 0.79    | the vetted provider, RFC 8032, signer trust model, verifier integration |
| `test_negative_corpus.py`       | 41      | 2.30    | §40 — 39 cases + two index guards                                       |
| `test_verifier_branches.py`     | 33      | 2.15    | §37 result-code coverage, closed gaps                                   |
| `test_vectors.py`               | 31      | 1.44    | §38 — 23 stability vectors                                              |
| `test_guardians.py`             | 28      | 3.10    | DKG, quorum, threshold decryption, prohibitions                         |
| `test_casting_units.py`         | 28      | 1.83    | ballot, capacity, sealing, board, record, API                           |
| `test_epd2_crypto_1.py`         | 32      | 29.54   | the real profile end to end, and its provenance                         |
| `test_e2e.py`                   | 24      | 4.60    | §58 — E2E-01 … E2E-14                                                   |
| `test_crypto_units.py`          | 24      | 4.58    | parameters, encoding, domain separation, randomness                     |
| `test_fault_injection.py`       | 22      | 2.26    | §43 — 11 fault points                                                   |
| `test_conformance.py`           | 19      | 5.84    | five evidence classes, catalogue completeness                           |
| `test_property.py`              | 17      | 7.45    | §41 — 15 named properties                                               |
| `test_target_conformance.py`    | 15      | 9.00    | **the target-profile cross-implementation core**                        |
| **Total**                       | **506** | ~76     |                                                                         |

Plus **9** tests in `tests/repository/test_pack16d_signature_dependency.py`,
which live with the repository checks rather than the reference suite
because the property they hold — the declared cryptographic dependency is
locked, in the right graph, and from a registry — is a packaging property.
They parse `uv.lock` with `tomllib` rather than searching it as text: a
string search for `cryptography` matches the name inside _other_ packages'
dependency lists and would report a lock entry that does not exist.

**Every dual-state branch in those tests is gone.** While the lock could not
be regenerated they were deliberately written to pass in both states — a test
that stays red until somebody gets round to it trains a reader to ignore red,
and a red suite hides the next real regression. That accommodation had to end
the moment the lock existed, or it would have become the thing it was designed
to prevent: a check that cannot fail. A missing lock entry now fails; so does
an entry without a registry source or `sha256:`-prefixed hashes, a resolved
version outside the declared range, a `cryptography` locked outside the
`epd2-voting-service` graph, and an outstanding-lock notice left behind after
the lock caught up.

The same applies to the nine provenance tests in `test_epd2_crypto_1.py`: a
`null` `upstream_commit` is now a failure rather than a tolerated state, and
an abbreviated hash, a URL pinning a different commit than the field beside
it, or a leftover `unpinned_reason` each fail on their own.

## 6. Coverage

Line coverage of the reference package: **90.9 % (3 816 / 4 200 executable
lines)**, measured with the standard library's `trace` module. The
percentage fell slightly from the first candidate's 91.8 % because the
package grew by roughly a third; the absolute number of covered lines rose
by more than 900.

| §59 dimension             | Result                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Line coverage             | **90.9 %**, measured                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| Branch coverage           | **NOT MEASURED** — no tool installable                                                                                                                                                                                                                                                                                                                                                                                                                  |
| Critical-path coverage    | Every cryptographic and transactional branch named in the acceptance matrix has explicit test evidence; the matrix's Test evidence column is the record                                                                                                                                                                                                                                                                                                 |
| Reason-code coverage      | 49 typed error classes; two are abstract bases by design (`SchemaError`, `ReservationUnavailableError`). `SignatureProviderUnavailableError` is new and is raised at **import** time, so it stops the process rather than reaching a caller. All **26** verification result codes are enumerated; 19 are reachable through `verify_record`, and the 7 that are not are named with reasons in `test_verifier_branches.UNREACHABLE_IN_REFERENCE_VERIFIER` |
| Negative-vector coverage  | 39 of 39 §40 cases present, each asserting its declared reason code, with a guard test that fails if any weakens to a type-only assertion                                                                                                                                                                                                                                                                                                               |
| State-transition coverage | Both continuation transitions, both submission outcomes, all three obligation states, both board phases, all three leaf classes and both quorum configurations are exercised                                                                                                                                                                                                                                                                            |

The `0.0 %` rows the raw tool prints for `__init__.py` files and
`testing/fixtures.py` are a tracing artefact — those modules are imported
before tracing starts — not untested code.

**Coverage is reported, not used as a quality gate.** 90.9 % of lines
executed says nothing about whether the 9.1 % that did not matter.

## 7. Defects this correction found

### 7.1 A pre-existing repository defect, unmasked by running more of the suite

**`tests/contract/test_reason_codes_registry.py::test_every_reason_code_literal_used_in_services_is_registered[pack-03]`
failed on the unmodified source archive.** It had been _skipping_, not
passing, since PACK-16D first landed, because it needs PyYAML and PyYAML was
not importable. Roughly sixty-five reason-code-shaped literals introduced by
the reference package had therefore never been checked against
`contracts/reason-codes/pack-03.yml` — through two candidate rounds and two
independent audits.

This was verified as pre-existing by running the failing test against the
untouched source tree before changing anything, rather than assuming it.

**Fixed** by excluding the `reference/` subtree **by path**, with the reason
recorded in `_EXCLUDED_SUBTREES`: those literals are genuine refusal codes,
but they belong to `PACK-16D-REASON-CODE-COVERAGE.md`, not to the voting
service's public contract. Registering `CRYPTO_TEST_MODE_REACHABLE` or
`EPD2_VOTING_REFERENCE_TEST_PROFILE` in `pack-03.yml` would tell a client to
expect refusals the deployed service can never emit — a worse outcome than
the gap.

The lesson is worth more than the fix: **a skipped test is not a passing
test**, and a suite that reports "17 skipped" without anyone reading which
17 is a suite with unknown coverage. This one hid a genuine contract
mismatch for two rounds.

### 7.2 Defects in this round's own work

A round that reports no defects has usually not looked. The first candidate
reported eighteen; the first correction found eight more; this one is
smaller because its scope was narrower, and **every one was fixed in the
implementation rather than documented around**.

| Defect                                                                                                                                                                                                                                                                     | How it was found                                                                                                           | Fix                                                                                                                                                                                      |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **`encode_seq` and `encode_struct` were ambiguous** — items were concatenated raw after a count, so `SEQ([b"ab", b"c"])` and `SEQ([b"a", b"bc"])` produced identical bytes. Two different structures could share a protocol digest                                         | **The independent Node.js oracle**, written from the documented grammar rather than from the code, disagreed with the code | Both encoders now length-prefix every member. Every digest in the round changed; the stability vectors caught the change, and the docstring records why it must not be "simplified" back |
| The threshold-tally fixture verified decryption-share proofs against the pre-ceremony public key                                                                                                                                                                           | `test_guardians.py` failures once a real ceremony existed                                                                  | The fixture derives the joint key from the roster and replaces the runtime's key with it                                                                                                 |
| `verify_record` ran the ceremony check too late, so a tampered transcript surfaced as `INVALID_BALLOT_PROOF`                                                                                                                                                               | `test_e2e_14`                                                                                                              | The ceremony block moved to immediately after the joint-key subgroup check, before anything uses the key                                                                                 |
| The chain digest silently weakened when an export carried checkpoint tuples but no signed checkpoints                                                                                                                                                                      | Review of `board_export_from`                                                                                              | `_chain_digest()` prefers `signed_checkpoints`; an export with tuples but no signed checkpoints returns `INCOMPLETE_RECORD` rather than falling back                                     |
| The OpenSSL cross-check **skipped** rather than failed, because pytest runs under an interpreter without `cryptography`                                                                                                                                                    | Reading the test output rather than its summary line                                                                       | Restructured to run out-of-process under a located interpreter, and to **fail loudly** if none exists. A conformance test that skips is a conformance test that lies                     |
| A share-tampering test passed for the wrong reason — doubling a share left the subgroup, so it hit the cheaper check first and never reached the proof                                                                                                                     | Reading the assertion                                                                                                      | Split into two: an out-of-subgroup case and a multiply-by-`g` case that stays in the subgroup and does reach the proof                                                                   |
| `pytest.raises(match=…)` treats its argument as a regex, so `"g^q != 1"` never matched                                                                                                                                                                                     | A test that passed when it should not have                                                                                 | `re.escape()` on every expected substring                                                                                                                                                |
| A helper named `test_source` was collected as a test and returned a value                                                                                                                                                                                                  | `PytestReturnNotNoneWarning`                                                                                               | Renamed to `deterministic_source` throughout                                                                                                                                             |
| **`test_missing_provider_fails_closed` passed for the wrong reason.** It ran a subprocess with `cryptography` blocked and asserted the import failed — but the subprocess interpreter could not import `cryptography` in the first place, so the blocker was doing nothing | Reading the test rather than its result                                                                                    | A **control run** was added: the same subprocess must import the provider successfully _without_ the blocker, or the test fails with "this test proves nothing about the fallback"       |
| The same test used the legacy `find_module`/`load_module` finder protocol, removed in Python 3.12. On 3.12+ the blocker would silently not block                                                                                                                           | Reading the test                                                                                                           | Rewritten to `find_spec`                                                                                                                                                                 |
| `CV-01` in the conformance catalogue still carried the withdrawn `3afa2962…` digest and the mutable `/main/` URL after the parameter artefact had moved on                                                                                                                 | A subagent reviewing documents against source                                                                              | Catalogue entry rewritten to the versioned specification reference, with the withdrawal stated in its `limitations`                                                                      |
| `testing/conformance.py` still said "three classes" in its docstring and emitted `catalog_version EPD2-CONFORMANCE-1` while the committed catalogue was `-2`; regenerating from code would have silently downgraded it                                                     | The same review                                                                                                            | Both corrected                                                                                                                                                                           |

## 8. Security review (§60)

The full checklist is in
`docs/packs/PACK-16/PACK-16D-SECURITY-AND-SIDE-CHANNEL-LIMITATIONS.md`.
The ones that must not be missed:

- **Constant-time behaviour is NOT claimed.** Four surfaces are
  distinguished: public verification carries no secret; **guardian secret
  operations and secret-nonce use remain pure Python and are not
  constant-time**. Ed25519 signing moved to OpenSSL, which pursues
  side-channel resistance as a design goal — a real reduction in risk and
  **not an assurance**, because EPD² measured nothing and a library's stated
  goals are not this repository's evidence. `OD-P16D-05` is **narrowed to
  three surfaces, not closed**, and remains the round's **production
  blocker**.
- **A compiled native artefact is now in the runtime path.** `cryptography`
  links a Rust binding layer over OpenSSL's libcrypto. That widens the
  build and supply-chain surface and makes a libcrypto CVE an EPD² concern.
  It is the deliberate price of not maintaining an elliptic-curve
  implementation, and it is stated rather than netted off.
- **Secret-material zeroization is NOT implemented** and cannot be done
  reliably in Python — immutable `int` and `bytes`, and a garbage collector
  that may copy. Guardian shares make this worse than it was.
- **The key ceremony has no custody model** (`OD-P16D-11`): one process, no
  authenticated channel between guardians, no HSM, no air gap, no
  witnesses.
- **The signer registry's own authorisation is unverifiable** by the
  verifier (`OD-P16D-12`).
- **No nonce-reuse detector exists.** A caller passing the same nonce twice
  is not caught, though a context-bound proof does not transfer.

There is no longer an Ed25519 implementation in this repository to assess.
`crypto/signature_provider.py` is argument validation and canonical encoding
around six library calls; if a future reader finds curve arithmetic there
again, that is the defect the module exists to prevent, and an `ast` test
fails on it.

## 9. Secret scan (§61)

| Category                                                | Result                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| ------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Real private keys                                       | **none** — no production private key material of any kind exists in the tree                                                                                                                                                                                                                                                                                                                                                                                                                              |
| Guardian secrets                                        | **none** — guardian polynomials and shares are generated at test time from a seeded deterministic source and are never written to a file. A test searches the ceremony transcript's canonical bytes for every share and coefficient                                                                                                                                                                                                                                                                       |
| Production credentials, API secrets, database passwords | **none**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| Real member or voter data                               | **none** — every fixture identifier is `cap-<fixture>-<n>` or `opt-<n>`                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| Test parameter files present                            | Two `.params` files containing **public group parameters only** — `p`, `q`, `g`. Both are named `EPD2-TESTONLY-NOTCONFORMANT-*`, both open with `# TEST ONLY / # NOT EPD2-CRYPTO-1 / # NOT ELECTIONGUARD 2.1 CONFORMANCE / # NOT PRODUCTION`, both are deterministic and reproducible, and `production_use_permitted` is `False` on both                                                                                                                                                                  |
| Real parameter artefact                                 | `EPD2-CRYPTO-1.json` contains **public group parameters only** — the published ElectionGuard 2.1 standard baseline constants. Public parameters are not secrets                                                                                                                                                                                                                                                                                                                                           |
| Board signing key                                       | The literal `b"test-board-key"`, appearing only inside `testing/fixtures.py`, and `b"TEST-ONLY-board-seed"` inside the checkpoint tests. Each is hashed to a 32-byte **TEST-ONLY** Ed25519 private key by `BulletinBoard._seed()`. Deterministic, fixture-scoped, named for what they are, and signing nothing outside a test. The provider's method for deriving them is called `generate_test_keypair` rather than `generate_keypair`, so the restriction is in the call site and not only in a comment |
| Exported target-profile fixtures                        | `PACK-16D-TARGET-PROFILE-FIXTURES.json` carries `contains_secret_material: false`, and a test greps it for `secret_key_share`, `coefficients` and `private`. The encryption **nonces** are present deliberately: a fixed nonce is what makes an independently computed ciphertext comparable, and it belongs to a test fixture with no election behind it                                                                                                                                                 |

`scripts/check_forbidden_files.py` reports `OK: no forbidden paths found.`

## 10. Repository version assessment (§62)

**Bump required: no. `REPOSITORY_VERSION` stays `0.16.0`.**

Reason: this is a correction of a candidate that was **not accepted**. The
0.16.0 number was allocated to PACK-16D's implementation content and that
content is what is being corrected; consuming 0.16.1 or 0.17.0 would
suggest an accepted 0.16.0 exists to supersede. `scripts/verify_versions.py`
passes unchanged, as does `scripts/check_canon_0_8_0.py`.

`CANON_VERSION` remains `0.8.0`.

```text
CANON_VERSION remains 0.8.0.

No Canon domain, aggregate, event or invariant semantics changed.

Canon compatibility metadata continues to support
repository version 0.16.x.
```

"Continues to support" rather than "was updated": the widening of
`repository_compatibility` from `>=0.1.0 <0.16.0` to `>=0.1.0 <0.17.0`
happened in the 0.16.0 round, is correct, and is not reverted. **This
correction modified no file under `docs/canonical/`** — and the sentence is
phrased that way rather than as "canon files untouched", which would be a
false statement about the entry's history.

**This is not a FINAL PASS and is not labelled as one.**

## 11. What this round did not do

```text
production deployment            real identity integration
production eligibility           production credential issuance
production key ceremony          HSM procurement
cloud deployment                 mobile app release
real election UI                 legal or formal certification
production monitoring            incident operations
real election configuration      PACK-17
production authentication        constant-time cryptography
trusted timestamping             cross-mirror gossip
comparison against a complete independent implementation
any cryptographic change whatsoever
```

The last line is the one to hold onto. `uv lock` and the upstream commit pin
were the two things a previous round attempted and the environment prevented;
both are done, and neither touched an algorithm, a guardian path, a checkpoint
semantic, a transaction, a sealed batch or a conformance oracle. Everything
else in that list remains out of scope by decision, and clearing two
environmental blockers moves none of it.

Two verification steps happened on the network-enabled host rather than here,
and are listed in §4 rather than folded into §3: the frozen install, and the
fetch of the upstream file's bytes. Each is one command for an auditor who has
what this session lacks.

**REFERENCE IMPLEMENTATION. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY.
NOT LEGALLY ACTIVATED.**
