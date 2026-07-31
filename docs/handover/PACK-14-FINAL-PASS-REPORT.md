# PACK-14 Identity, Authentication & Account Security 0.14.0 — Final PASS Report

Status: **PACK-14 IDENTITY, AUTHENTICATION & ACCOUNT SECURITY 0.14.0 — FINAL PASS.**

```text
PACK-14 FINAL PASS
REPOSITORY_VERSION 0.14.0
CANON_VERSION 0.8.0
EXTERNAL CI PASS
NOT PRODUCTION READY
NOT LEGALLY ACTIVATED
```

This is a **packaging round**. No implementation was rebuilt. No
`identity-service` module was changed, no migration artefact, test, reason
code, ADR, contract, frontend file, route, visual snapshot or CI
definition was touched, and neither the repository nor the canon version
moved. The archive is the externally verified tree plus the status,
register and handover documents that close the round.

The PASS rests on an **external GitHub Actions run**. Section 10 records
its figures, read out of the committed transcript rather than transcribed
from a message; section 11 states exactly which checks were re-run locally
after the documentation edits and which are accepted from that run.
Nothing network-dependent is claimed as locally verified, and — this
matters for a pack named after identity and authentication — no provider,
no cryptographic library and no deployment is claimed at all.

---

## 1. Input baseline — PACK-13

|                             |                                                                               |
| --------------------------- | ----------------------------------------------------------------------------- |
| Baseline archive            | `EPD2_PACK-13_PRODUCTION_DATA_PLANE_CONTRACT_EVOLUTION_0.13.0_FINAL_PASS.zip` |
| Baseline SHA-256            | `713739c21199d73cffb80f51581683ef9fa2f379752ad0f4f866827f8c0a15f2`            |
| Baseline repository version | `0.13.0`                                                                      |
| Canon version               | `0.8.0` — unchanged by this round                                             |
| Baseline status             | FINAL PASS, external GitHub Actions verified                                  |

PACK-13 is now the previous PASS baseline. Nothing in PACK-01—PACK-13 was
rewritten to reach this one.

## 2. Candidate archive lineage

PACK-14 reached this PASS through three candidate archives. Each is named
here because a lineage that only records its endpoint hides the review
that produced it.

| Step | Archive                                                    | SHA-256                                                            | Outcome                                                                     |
| ---- | ---------------------------------------------------------- | ------------------------------------------------------------------ | --------------------------------------------------------------------------- |
| 1    | `EPD2_PACK-14_..._0.14.0_CANDIDATE.zip`                    | `8035adf645f68c497f5eea14bea83e8cace411ba599f6ae9db061f50bfb70953` | Reviewed before external CI; three findings returned.                       |
| 2    | `EPD2_PACK-14_..._0.14.0_CANDIDATE_CORRECTED.zip`          | `33dedae729dccdc57d522493194a9d87114fc0e7f6a63762e62bfe323628b0fa` | Findings fixed. First external run failed at `make format-check`.           |
| 3    | `EPD2_PACK-14_..._0.14.0_CANDIDATE_CORRECTED_PRETTIER.zip` | `c655798888d52481133093cd5b02657545b53dc29dd282090f5ca527baf3c209` | **The archive the passing run verified.** This FINAL PASS is built from it. |

**Step 1 → 2, the correction round.** Three findings, all fixed before any
external run: persistence that was metadata rather than persistence (ten
real SQL migration artefacts, a transactional checksum-guarded migration
runner, eleven durable adapters, a `UnitOfWork` and a monotonic
optimistic-concurrency guard replaced it); a breached-password default
that reported nothing as breached (removed — the unbound default now
raises, so no password can be enrolled or replaced without a bound
checker); and an `api.py` that was an endpoint catalogue rather than a
boundary (a transport-agnostic runnable adapter was added for 12 of the 42
catalogued operations). `docs/packs/PACK-14/PACK-14-IMPLEMENTATION-REPORT.md`
§12 records all three in full.

**Step 2 → 3, the Prettier fix.** The first external run failed on exactly
one file: `contracts/reason-codes/pack-14.yml` was not Prettier-formatted.
`prettier --write` removed 215 blank lines between entries and changed
nothing else — the registry still parses to the same 213 entries in the
same order, with identical codes, meanings, severities and owners, and a
JSON round-trip comparison before and after is identical.

At no step was functional scope expanded, a frontend built, a dependency
added, a CI gate weakened, an existing test removed, or either version
moved.

## 3. Verification artifact

|                        |                                                                        |
| ---------------------- | ---------------------------------------------------------------------- |
| Artifact               | `epd2-civic-os-verification-result(16).zip`                            |
| SHA-256                | `c80b2f1a05f97423c782f7b0e42f78502a802bd47432a43caee207321dff515d`     |
| Inner verification ZIP | `epd2-civic-os-verification-result.zip`                                |
| SHA-256                | `df6981227d80f4a01d406bcf882f7dea3cfd31400d3c262eb93009c1eb1b6054`     |
| Retained               | **Outside** this repository; the raw transcript is committed inside it |

Both digests were recomputed in the environment that assembled this
archive and both match the values supplied with the task. The artifact is
a snapshot of the runner's workspace after the run; the transcript it
contains is committed here as
`docs/handover/PACK-14-EXTERNAL-CI-VERIFICATION.log` (797 lines).

## 4. Scope of PACK-14

Identity, Authentication & Account Security. `services/identity-service`
was extended **in place** with the six bounded contexts specification §4.1
assigns to it — Account Registry, Credential Registry, Authentication,
Session Security, Recovery coordination and Identity-Proofing references —
as internally separated modules with separate storage boundaries. **No
parallel authentication service was created**, and ownership of canon
7.2's `Account` and canon 7.3's `IdentityRecord` is unchanged.

## 5. The decisions the PASS carries

**`FIR-INV-001` survives the round that most threatened it: there is no
global user ID.** Five identifier spaces are distinct Python types even
though all are UUIDs underneath; what crosses a domain boundary is a
`ScopedIdentityReference` derived per purpose, per organizational scope
and per domain owner from a per-deployment secret salt; and
`reject_prohibited_payload_keys` runs before any event, audit record or
API response exists. Two references derived for two purposes from one
account do not compare equal.

**Canon 7.2's status enum is not extended.** `AccountLock`, a
security-class `AccountRestriction`, `AccountClosureRequest` state and
lifecycle outcomes carry what would otherwise have been `locked`,
`closure_pending` and `deleted_or_anonymized`. This closed OD-P14-01
without a canon amendment, which is why `CANON_VERSION` is still `0.8.0`.

**All four security ports refuse by default.** `UnboundWebAuthnVerifier`,
`UnavailablePasswordHasher`, `UnboundBreachedPasswordChecker` and
`UnboundAssertionSignatureVerifier` all raise. **No password may be
enrolled or replaced while no breach checker is bound**; the one governed
exception, `PasswordDegradedModeDecision`, permits authentication against
an already stored hash and has no field that could permit anything else.

**`MfaFactorClass` has no `sms_otp` member.** SMS OTP carries no assurance
level at all, and the system operates with no SMS provider (OD-P14-09).

**`VotingHandoffIssuance` has no account field of any kind**, and
`0008_bootstrap_and_handoff.sql` records in a comment that a migration
adding one would reverse ADR-088. The non-reversibility property is
expressed as an absent column, not as a policy.

## 6. The reference persistence path

Ten SQL artefacts in `services/identity-service/migrations/`, applied in
declared order inside a single `BEGIN IMMEDIATE` transaction by
`migration_runner`, each recorded with a SHA-256 checksum, with a
compatibility check that refuses a database whose history disagrees with
the files on disk. Applying them produces **29 tables and 35 indexes** — 9
unique constraints, two of them partial, and 10 expiry indexes. Eleven
durable adapters in `sql_storage`, a nesting-aware `UnitOfWork`, and a
monotonic optimistic-concurrency guard that refuses stale writes.

It runs on **SQLite through the Python standard library**, which is why
the round added no dependency: `uv.lock` and `package-lock.json` are
unchanged, and CI's frozen install is unaffected. **No production database
is deployed and no operational durability is claimed.** The in-memory
adapters remain in `account_security_storage` as explicit **test**
adapters and are not the default runtime binding —
`tests/repository/test_pack14_default_binding.py` asserts that the
composition root names none of them.

## 7. The runnable reference boundary

`service_api.IdentityServiceApi` parses and validates requests, checks
origin against the ten declared workspace origins, asserts audience,
carries session context, honours idempotency keys durably across a
restart, carries version fields, and answers with a registered reason code
on **every** response including the successful ones.
`assert_response_safe` runs in `ApiResponse.__post_init__`, so a response
carrying a prohibited identifier or a secret cannot be constructed.

`ROUTED_OPERATIONS` has 12 entries and `CONTRACT_ONLY_OPERATIONS` has 30,
both named constants asserted against the catalogue, so no document can
imply that all 42 catalogued operations run. It is transport-agnostic:
**no HTTP server, no TLS termination, no gateway, no public deployment.**

## 8. Numbers

| Thing                                | Count                                                |
| ------------------------------------ | ---------------------------------------------------- |
| Source modules in `identity-service` | 40 (34 new)                                          |
| Test modules in `identity-service`   | 12                                                   |
| Tests in `identity-service`          | 288                                                  |
| New repository-level tests           | 28                                                   |
| Registered reason codes              | 213 (131 additive · 22 redeclared · 60 `*_RECORDED`) |
| Event types                          | 59, in 9 families                                    |
| API operations                       | 42 catalogued · 12 routed                            |
| Migration artefacts                  | 10, expand-only                                      |
| Schema they create                   | 29 tables · 35 indexes (9 unique · 10 expiry)        |
| ADRs                                 | ADR-079 — ADR-088, status `proposed`                 |

## 9. FIR treatment

`FIR-ROADMAP-004` moves from `candidate` to **`implemented in reference
form`** — not to `implemented`, because no provider is bound and nothing
is deployed. It is the **only** status change this round makes.

141 FIR entries before this round and 141 after; no entry was added,
removed or rolled back. `FIR-UX-011` stays **future** — no FRONT-PACK was
built and no page catalogue or screen-state matrix exists. `FIR-TRUST-001`,
`FIR-REPRESENT-001` and `FIR-INCLUSION-001` stay future. `FIR-CONFIG-001`
gained a consumer in the candidate round and is still not implemented by
it.

`OD-P14-07` (retention durations) remains **open** pending legal
confirmation. The PASS does not close it: every `duration_confirmed` flag
is still `False`, every destructive disposition still refuses while it is,
deletion under a legal hold still refuses, and an unknown hold state still
fails closed.

**One factual correction was made to the register.** The candidate round's
`FIR-BASE-001` entry described ADR-079 — ADR-088 as "accepted in the
specification round". `docs/handover/PACK-14-SPEC-ADR-REPORT.md` §2 records
them as `proposed`, and the ADR files say `proposed`. The register now says
`proposed` too. **No ADR file was edited.** Their governance status belongs
to the body that owns them and a green pipeline does not move it — the
same treatment ADR-061 — ADR-068 received through PACK-11's and PACK-12's
FINAL PASS rounds, and the reason is stated in `docs/adr/README.md`.

## 10. External GitHub Actions results

Runner: GitHub Actions / ubuntu-latest · Python 3.12.13 · Node.js 22.
Every figure below was read out of
`docs/handover/PACK-14-EXTERNAL-CI-VERIFICATION.log`.

| Stage                            | Command                                          | Result                             |
| -------------------------------- | ------------------------------------------------ | ---------------------------------- |
| Repository path manifest         | `scripts/check_repository.py`                    | **PASS** — 867 / 867               |
| Forbidden paths                  | `scripts/check_forbidden_files.py`               | **PASS** — none present            |
| Version consistency              | `scripts/verify_versions.py`                     | **PASS**                           |
| Ruff format                      | `ruff format --check .`                          | **PASS** — 566 files               |
| Prettier                         | `npm run format:check`                           | **PASS**                           |
| Ruff lint                        | `ruff check .`                                   | **PASS**                           |
| ESLint                           | `npm run lint --workspace=frontend/web-shell`    | **PASS**                           |
| mypy                             | 23 separate targets                              | **PASS** — no issues in any group  |
| TypeScript typecheck             | `tsc --noEmit` in `epd2-types` and `web-shell`   | **PASS**                           |
| Python test suite                | `pytest`                                         | **PASS** — 4905 passed, 4 skipped  |
| TypeScript package tests         | `node --import tsx --test` in `epd2-types`       | **PASS** — 3 passed, 0 failed      |
| Node tests (`web-shell`)         | `node --import tsx --test`                       | **PASS** — 34 passed, 0 failed     |
| Frontend unit / render tests     | `vitest` in `frontend/web-shell`                 | **PASS** — 16 passed, 2 test files |
| Next.js production build         | `next build`                                     | **PASS** — 46 / 46 static pages    |
| Browser / accessibility / visual | Playwright, projects `desktop`, `mobile`, `wide` | **PASS** — 108 passed              |

`identity-service`'s own mypy target reports **no issues found in 52
source files**, and the transcript collects
`tests/repository/test_pack14_default_binding.py .........` — direct
evidence that the run exercised PACK-14's code rather than an older tree.

Two arithmetic reconciliations are recorded in
`docs/handover/PACK-14-EXTERNAL-CI-VERIFICATION-RESULT.md` §2 rather than
glossed: the seven-test difference between CI's 4905 and the packaging
sandbox's 4898 is `hypothesis` being uninstallable here, and the 566-file
Ruff count against the sandbox's 393 is the 173 Python files of a stale
nested directory in the GitHub checkout that this archive excludes (§16).

## 11. What was re-run locally after the documentation edits

The documentation edits below were made after the external run, so the
checks that could detect a documentation regression were re-run here.

| Check                                             | Result                                    |
| ------------------------------------------------- | ----------------------------------------- |
| `scripts/check_repository.py`                     | **OK — 870 / 870 required paths**         |
| `scripts/check_forbidden_files.py`                | **OK — no forbidden paths**               |
| `scripts/verify_versions.py`                      | **OK — all version sources consistent**   |
| `scripts/check_canon_0_8_0.py`                    | **OK — all 18 canon 0.8.0 checks passed** |
| `ruff format --check .`                           | **PASS**                                  |
| `ruff check .`                                    | **All checks passed**                     |
| `mypy`, all 23 targets                            | **Success in every group**                |
| `pytest`                                          | **4898 passed, 5 skipped**                |
| `prettier --check` on every changed Markdown file | **PASS**                                  |

The required-path count moves from **867 to 870** because this round adds
three required paths: this report,
`PACK-14-EXTERNAL-CI-VERIFICATION-RESULT.md` and
`PACK-14-EXTERNAL-CI-VERIFICATION.log`. That is the only intended
difference between what CI counted and what this archive counts, and it is
stated here rather than left to be discovered.

**Accepted from the external run, not re-run here:** Prettier over the
whole tree, ESLint, both TypeScript typechecks, the `epd2-types` tests,
the Node tests, the frontend unit and render tests, the Next.js production
build and the 108 Playwright browser, accessibility and visual tests. This
sandbox has no network access to npm, so none of them can run here and
none is claimed as locally verified. No frontend file, route, snapshot or
TypeScript source changed in this round, so the external results still
describe this tree.

## 12. What the PASS does not establish

A green pipeline is evidence that the repository builds, type-checks,
lints, formats and tests cleanly. It is **not** evidence of any of the
following, none of which PACK-14 implements or claims:

- production readiness, operational deployment, or legal activation;
- a production IAM, identity provider, eID scheme or KYC integration;
- correct WebAuthn verification or correct password hashing — both are
  ports whose default binding refuses, and neither algorithm is
  implemented in this repository;
- a bound breached-password corpus;
- a production database, replication, backup, failover or restore;
- an HTTP surface, TLS termination, production gateway or public
  deployment;
- a durable audit store — `runtime.build_identity_service` binds
  `InMemoryAuditEventStore` and records why: `audit-core` owns durable
  audit persistence;
- email or SMS delivery, an HSM or a KMS;
- a Voting Client, eligibility assertion, voting credential issuance,
  ballots or tally (PACK-15 / PACK-16);
- a full legal electronic signature (`FIR-TRUST-001`);
- the Account & Security FRONT-PACK (`FIR-UX-011`);
- lawful retention durations (`OD-P14-07`).

`docs/packs/PACK-14/PACK-14-OPEN-ITEMS.md` records these as open rather
than covered.

## 13. Dependencies on later packs

Eligibility assertion without an attached identity, voting credential
issuance, ballots, verification and tally are **PACK-15 / PACK-16**;
PACK-14 defines only the WS-03 handoff boundary and implements no Voting
Client. Backup and restore capability is **PACK-17**. The Account &
Security page sequence and screen-state matrix belong to the
`FRONT-PACK Specification + UX/IA` stage under `FIR-UX-011`. Electronic
signature is `FIR-TRUST-001`; mandate and representation are
`FIR-REPRESENT-001`. Confirmed retention durations are PACK-09's plus
legal review.

## 14. Known limitations

Unchanged by the PASS and recorded in
`docs/packs/PACK-14/PACK-14-OPEN-ITEMS.md`, which now carries a
superseding status note saying exactly that. The five that matter most:
the persistence path is a SQLite reference path and not a production data
plane; no provider of any kind is integrated and all four security ports
refuse; the service boundary is a transport-agnostic adapter for 12 of 42
operations with no gateway in front of it; the audit store is the one port
the composition root still binds in memory; and no frontend was built.

## 15. Production and legal disclaimers

**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.** Nothing in this archive
deploys a system, processes a real person's identity data, authenticates a
real member, issues a real credential or produces a legally effective
record. The pipeline verifies a repository. Activation is a decision for
the party's governing bodies under the applicable statutory framework, and
this document neither anticipates nor substitutes for it.

## 16. Archive hygiene

The archive was built from an explicit file walk with a fixed exclusion
set, then verified by extracting the result and scanning it. It contains
**no** `.git`, `.venv`, `node_modules`, `.next`, `dist`, `build`,
`__pycache__`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`,
`.hypothesis`, coverage artifact, temporary file, editor cache, OS
metadata file, secret, credential-bearing environment file, or nested
archive of any kind. **The verification artifact is not inside it and
neither is any candidate ZIP.** There is no duplicate path, no duplicate
Master Register, no duplicate PACK-14 matrix and no duplicate ADR
filename.

Four hygiene decisions are recorded rather than left to be noticed.

1. **A stale nested repository was excluded.** The GitHub checkout
   contains `epd2-civic-os/` — a **complete copy of the repository at
   `REPOSITORY_VERSION 0.6.0`**, 435 files, 173 of them Python, whose
   `identity-service` has six modules and none of PACK-14's. It was
   format-checked and linted by the run (which is why Ruff reported 566
   files rather than 393) but never imported, collected or type-checked,
   because `pyproject.toml`'s `testpaths` is an explicit list, the mypy
   invocations name 23 explicit targets and `check_repository.py` reads a
   manifest. It has never been part of any FINAL PASS archive. Carrying it
   would put a second, eight-versions-old repository inside the
   authoritative baseline. **Recommendation: delete `epd2-civic-os/` from
   the GitHub repository.**
2. **PACK-12's temporary correction notes are absent.** `DELETE.txt`,
   `PACK-12-CI-FORMAT-CORRECTION.md` and
   `PACK-12-CI-FORMAT-CORRECTION-2.md` exist in the verified checkout,
   are superseded by `docs/handover/PACK-12-FINAL-PASS-REPORT.md` §7, and
   were excluded by PACK-13's FINAL PASS round for the same reason.
3. **`docs/handover/PACK-01-VERIFICATION.log` is absent.** It exists in
   the GitHub working repository but in **no** archive of the cumulative
   lineage, including the PACK-13 FINAL PASS baseline this round was built
   from. Absorbing it silently would be a scope change to the cumulative
   archive, so it is reported here instead. It can be added deliberately
   in a later round if it is wanted.
4. **The run's own outputs are absent, except the transcript.**
   `VERIFICATION.log` and `VERIFICATION-RESULT.md` sat at the root of the
   verified workspace; the log is committed here under its PACK-14 name
   instead. `frontend/web-shell/playwright-report/`,
   `frontend/web-shell/test-results/` and `tsconfig.tsbuildinfo` are build
   and report artifacts and are excluded.

## 17. Documentation changed by this packaging round

- `docs/handover/PACK-14-FINAL-PASS-REPORT.md` — **new**, this document.
- `docs/handover/PACK-14-EXTERNAL-CI-VERIFICATION-RESULT.md` — **new**.
- `docs/handover/PACK-14-EXTERNAL-CI-VERIFICATION.log` — **new**, the raw
  797-line transcript, adopted verbatim from the verification artifact.
- `docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md` — §1.16
  round record, `FIR-BASE-001`'s baseline pointer, `FIR-ROADMAP-004`'s
  status, §21's implementation summary, and the one factual correction in
  §9 above.
- `CHANGELOG.md` — the `0.14.0` heading becomes `(FINAL PASS)`, the round
  entry records the external results, and a packaging-round entry records
  what this round touched.
- `README.md` — the repository-state header block and a new PACK-14
  section.
- `docs/adr/README.md` — the ADR-079 — ADR-088 index section, which was
  missing entirely.
- `services/README.md` — the PACK-14 row and the note that PACK-14 added
  no fourteenth service.
- `services/identity-service/README.md` — unchanged this round; the
  candidate round already documented the runtime, the reference
  persistence path and the refusing ports.
- `docs/packs/PACK-14/PACK-14-ACCEPTANCE-MATRIX.md` and
  `PACK-14-FIR-COVERAGE-MATRIX.md` — status blocks only; no criterion,
  treatment or row changed.
- `docs/packs/PACK-14/PACK-14-SPECIFICATION.md` — one superseding status
  note; the original header is preserved.
- The ten implementation-round documents under `docs/packs/PACK-14/` and
  `docs/handover/PACK-14-IMPLEMENTATION-CANDIDATE-REPORT.md` — each had
  the line **"External GitHub Actions has not run against this round."**
  replaced by a superseding status note, because after the run that
  sentence was false. Nothing else in any of the eleven changed.
- `scripts/check_repository.py` — three required paths added.
- `docs/handover/PACK-09-EXTERNAL-CI-VERIFICATION.log`,
  `PACK-11-…` and `PACK-13-…` — adopted from the externally verified tree,
  as recorded in §18.

**`docs/handover/PACK-14-IMPLEMENTATION-CANDIDATE-REPORT.md` and
`docs/handover/PACK-14-SPEC-ADR-REPORT.md` keep their bodies unmodified.**
Each round genuinely was what it said it was at the time, and rewriting
either to read as though it had always been a FINAL PASS would destroy the
record this handover chain exists to keep.

## 18. Files adopted from the externally verified tree

Three files differed between the packaging sandbox and the tree that
passed. The tree that passed is the source of truth, so its bytes were
adopted — the same decision PACK-13's round made for its two.

| File                                                 | Difference                                                                     |
| ---------------------------------------------------- | ------------------------------------------------------------------------------ |
| `docs/handover/PACK-09-EXTERNAL-CI-VERIFICATION.log` | Identical content; three `Generating static pages` lines carried a stray `CR`. |
| `docs/handover/PACK-11-EXTERNAL-CI-VERIFICATION.log` | Same, three lines.                                                             |
| `docs/handover/PACK-13-EXTERNAL-CI-VERIFICATION.log` | Same, three lines.                                                             |

No other byte of any of the three differs, and no other file in the
packaging tree differed from the verified checkout in any way.

## 19. Files added since the PACK-13 FINAL PASS baseline (103)

| File                                                                                  | SHA-256                                                                                          |
| ------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| `contracts/reason-codes/pack-14.yml`                                                  | `8b67a912f9de0bdb612a33a1645cf318b3ba3af6b249214c7effd03b6fff2e33`                               |
| `docs/adr/ADR-079-NO-GLOBAL-USER-IDENTITY.md`                                         | `2d89a86c813de5c5c29ae95d8be3a6393fd2c09675df0634e20dd55d706a69fe`                               |
| `docs/adr/ADR-080-ACCOUNT-PERSON-MEMBERSHIP-SEPARATION.md`                            | `ea29b5fb6876642cb693f57a3bce932024afbbc546747d23ae03a99e2da665fb`                               |
| `docs/adr/ADR-081-PASSKEY-FIRST-AUTHENTICATION.md`                                    | `7dd81f97603838e432a74e4710e1ccaeed52abaf08b2b5b9092bd0e36fbd11bd`                               |
| `docs/adr/ADR-082-AUTHENTICATION-ASSURANCE-AND-STEP-UP.md`                            | `01b668dcea7cd2b5db5bc0b1edf6bd899be305564f2866513af47d8e87b60e29`                               |
| `docs/adr/ADR-083-SESSION-SECURITY-AND-CROSS-WORKSPACE-ISOLATION.md`                  | `d247a67e3d54057928930f50573bc96f218be0e54d8e58c529856eb9ce552dd9`                               |
| `docs/adr/ADR-084-ACCOUNT-LIFECYCLE-AND-CREDENTIAL-GOVERNANCE.md`                     | `cad2ede26ab337a3b44f764a1d195702f8097e04bbdc52236f71f70d2930c001`                               |
| `docs/adr/ADR-085-ACCOUNT-RECOVERY-AND-TAKEOVER-PROTECTION.md`                        | `07499968294063e1a49337b6d0ab748cfcdbf19acbad405fc759d1562b42fa05`                               |
| `docs/adr/ADR-086-IDENTITY-PROOFING-BOUNDARY.md`                                      | `de7e37c893c7d78417d45563375fb4652d5501a3fea84ddd55987bb6cfb4a039`                               |
| `docs/adr/ADR-087-PRIVILEGED-IDENTITY-ADMINISTRATION.md`                              | `07a0c78c1c9e83f6c2483bf774bc56ed1937feb4ae5bc1e2215c69b459db6821`                               |
| `docs/adr/ADR-088-VOTING-HANDOFF-IDENTITY-SEPARATION.md`                              | `7c00ff30dff09015c6902cd4f3e30a67dfaa5040113bc80238355ebb1984946b`                               |
| `docs/handover/PACK-14-EXTERNAL-CI-VERIFICATION-RESULT.md`                            | `687357837f2c65d0e92af14142c00e390f87686f8d28ccbe1808478c506d5235`                               |
| `docs/handover/PACK-14-EXTERNAL-CI-VERIFICATION.log`                                  | `a26d8aa607f752c9db8fe9f720817bddb5ba9864ce1add01d5eca96f33ea6bf6`                               |
| `docs/handover/PACK-14-FINAL-PASS-REPORT.md`                                          | _self-referential — a file cannot contain its own digest; compute it from the delivered archive_ |
| `docs/handover/PACK-14-IMPLEMENTATION-CANDIDATE-REPORT.md`                            | `afe28187911e170f3539f932961d9c8815d5758f66ff04e66f62a8ac4a32e3bb`                               |
| `docs/handover/PACK-14-SPEC-ADR-REPORT.md`                                            | `9b2fc11228ae00550ad1f4e7c5ba464a8fb2b78c052aeb06781b182a124a9bbd`                               |
| `docs/packs/PACK-14/PACK-14-ACCEPTANCE-MATRIX.md`                                     | `f2cddea0305e8b5fba7eca9c229a4e69c1de3ea93be772840b59d90e09c19cdd`                               |
| `docs/packs/PACK-14/PACK-14-API-CATALOG.md`                                           | `356e5abe4323bff90da725b88656087f1349c226f0e471b78ec11bf220e797c5`                               |
| `docs/packs/PACK-14/PACK-14-ASSURANCE-LEVEL-MATRIX.md`                                | `8cc987cea33e991a5f454e7d3f4bb94cc47359330bc8f0d1c34a90facb24bb73`                               |
| `docs/packs/PACK-14/PACK-14-ATTACHMENT-MATRIX.md`                                     | `29f4fb77af34b673ac7d20c033c6bf74910687740d50310149a6b090a1b494ab`                               |
| `docs/packs/PACK-14/PACK-14-AUTHENTICATION-METHOD-MATRIX.md`                          | `317a6a57ab15e71f7d3e335414f71e8cf106b6f3665a100b5607bc827f06b7dd`                               |
| `docs/packs/PACK-14/PACK-14-CANON-ASSESSMENT.md`                                      | `c2623507d162797396f88dc2785192dfc9d3980d6b1418c5777ad5b3c94cbc7f`                               |
| `docs/packs/PACK-14/PACK-14-CONTENT-CATALOGUE-DE.md`                                  | `5d7e8a69b238b43c7890b1fa5fd1100839c0d389e7d2b588443f5123506c860c`                               |
| `docs/packs/PACK-14/PACK-14-CROSS-WORKSPACE-SESSION-MATRIX.md`                        | `c7731e015fb606e284ae87adf7a7b0f9ac5dfc5cd164430c7204be275ab173f7`                               |
| `docs/packs/PACK-14/PACK-14-DATA-MODEL.md`                                            | `69dd2db5a5fcb7ddc0aa1b025b4e9acd173fdbc8ad828bddbe50dadc35a4dbef`                               |
| `docs/packs/PACK-14/PACK-14-DEPENDENCY-REPORT.md`                                     | `7b2c539989cb74d19e4df5b8d8df90e1ebf1a61d3faaf75c52043634f69e8030`                               |
| `docs/packs/PACK-14/PACK-14-EVENT-CATALOG.md`                                         | `51a7fff12e40ea7c053a4dde3533a9ca87dcb298465b6318a1f89f75e508d7b2`                               |
| `docs/packs/PACK-14/PACK-14-FIELD-CATALOGUE.md`                                       | `5de067100fd65aedbbf530a2bae651644f812348fcf431bd15d395a6ab5f9a03`                               |
| `docs/packs/PACK-14/PACK-14-FIR-COVERAGE-MATRIX.md`                                   | `13871ef13d0751ba5e847f9731624f3f347eea48b5c4e031aeeb2cc1959b0a8e`                               |
| `docs/packs/PACK-14/PACK-14-FORM-INVENTORY.md`                                        | `ccd75c7c8dbda9197039e6c0abd8d9d94dec663e0c18b2478337a75c2568ee83`                               |
| `docs/packs/PACK-14/PACK-14-IDENTITY-PROOFING-MATRIX.md`                              | `6d2bd6ef547ef19ca99f7cd262332fa6ffd6405bb50f4595ee75783a377bb11e`                               |
| `docs/packs/PACK-14/PACK-14-IDENTITY-SEPARATION-MATRIX.md`                            | `3c540a3324b0370e15ef6d2992b4a3a4b992e6974238661aa47b4861bb379eb2`                               |
| `docs/packs/PACK-14/PACK-14-IMPLEMENTATION-MATRIX.md`                                 | `1eaf5a017f4788a2a55bc9c74f05d83905c67944305fb36f2ad6fc003a818131`                               |
| `docs/packs/PACK-14/PACK-14-IMPLEMENTATION-REPORT.md`                                 | `c718465b6cee665120f35df710833592b2418b4ad5abcdbd6b23ecc4060e4948`                               |
| `docs/packs/PACK-14/PACK-14-MIGRATION-REPORT.md`                                      | `d6f8bccdc772bf2fa2726c0d8d2e8b135ec6ffb6c747626d68c780fb4cc639cb`                               |
| `docs/packs/PACK-14/PACK-14-OPEN-ITEMS.md`                                            | `8790b41913ef97da09ca7d3ee44d908bdf416aa41b52b69b578c2579b8efff2e`                               |
| `docs/packs/PACK-14/PACK-14-PRIVACY-RETENTION-MATRIX.md`                              | `1eda9782e27dc4f7742624770d8806a397067f2a9c46fcd184b3452a9ef71588`                               |
| `docs/packs/PACK-14/PACK-14-PRIVACY-VERIFICATION.md`                                  | `227172267f5d1f310a951315458a7be330f795899500ac023b39180c8db6b770`                               |
| `docs/packs/PACK-14/PACK-14-REASON-CODE-CATALOG.md`                                   | `05d3863783addbcb942bb374d911f028fc8dd9ec043f4b301d3b37eb66e980f4`                               |
| `docs/packs/PACK-14/PACK-14-RECOVERY-CONTROL-MATRIX.md`                               | `6ba597ac0cbd9f7fecf3cd0fa6bbbfccc4366c8dd531ed61ed87eca861110562`                               |
| `docs/packs/PACK-14/PACK-14-RENDITION-SPECIFICATION.md`                               | `6942fe21be9ec246835305be8659fae5e2dae7a9ed2483fb7a9b8873cf82c3e4`                               |
| `docs/packs/PACK-14/PACK-14-SECURITY-VERIFICATION.md`                                 | `4abcc5534321db3e22146ad00558172e3be8815dec48300ae6038e764a15b1f4`                               |
| `docs/packs/PACK-14/PACK-14-SESSION-SECURITY-MATRIX.md`                               | `377fcdf42979596c1750fd99de55ef2f1b5f56046e2e50118d2cc6d906f2ad04`                               |
| `docs/packs/PACK-14/PACK-14-SPECIFICATION.md`                                         | `ba3b5f4df34d1cc6887a4580ad855f3dac833c81d1632a693b3504bc4c03f9d1`                               |
| `docs/packs/PACK-14/PACK-14-TEST-MATRIX.md`                                           | `814853fc5aa6ed30fc12b474aeb47231ea81646b5e657c62625e1b0e69304b7f`                               |
| `docs/packs/PACK-14/PACK-14-THREAT-MODEL.md`                                          | `2ac296339c9a9bc0f94a55082e8a607a4f5e0b834b0ca69ff07b3380a6591f79`                               |
| `docs/packs/PACK-14/PACK-14-WORKFLOW-MATRIX.md`                                       | `55fdaa41c34e6718608b442b64517702a354618420a3da29a371c23fb1fa9e0e`                               |
| `services/identity-service/migrations/0001_account_registry.sql`                      | `2c4257e8bcd316cd4329e1426b367391c1de5018c8e46851e3641e369b6e9580`                               |
| `services/identity-service/migrations/0002_account_contacts.sql`                      | `b9a03965c73fd490b069f0a004fa4a6de090ec823d0612fad4ec02f51f3f17f6`                               |
| `services/identity-service/migrations/0003_credential_registry.sql`                   | `80c798fd9641a9944cc0351bc3ae553da610441efc8e86da909e72652561c006`                               |
| `services/identity-service/migrations/0004_sessions.sql`                              | `eb0a5b6e01a2fc68b6cbbdc5a1bfdce2da600c269d730abe5f57d1d122a10c88`                               |
| `services/identity-service/migrations/0005_step_up.sql`                               | `de1134206834579143a421765ba3c18ea1f61d39434e4ee40a6af360ce7697fd`                               |
| `services/identity-service/migrations/0006_recovery.sql`                              | `c6e74f50e173b55d9060e1de80385e69c6db690501aeebd1d2ae56511a614195`                               |
| `services/identity-service/migrations/0007_proofing.sql`                              | `4c7215060fee4feb9fd32f24cfdd7ea7ac42f1da55091122fa52a0f0c194f70c`                               |
| `services/identity-service/migrations/0008_bootstrap_and_handoff.sql`                 | `a6806016e686b50da1413dbf0ccd0cc671f0ea58e34e075ddce192527f077012`                               |
| `services/identity-service/migrations/0009_identity_mappings.sql`                     | `6937806b6909b3cd96dfc7a731678a5c77be653d589f6c0a015350b8d33a5630`                               |
| `services/identity-service/migrations/0010_replay_prevention.sql`                     | `f7478f02cd6f001aa3ac6fae237859af570caca282ab8385bc6a3d1f3fba3f57`                               |
| `services/identity-service/src/epd2_identity_service/account_security_application.py` | `3f1ae834b2292212f82235ef674dcd6aa639017a2d9c6258f14dbebb88500bb1`                               |
| `services/identity-service/src/epd2_identity_service/account_security_events.py`      | `6fd0c23ef57836c336d9ae9231494362b30948215ae36ebbe3303e2158a543d6`                               |
| `services/identity-service/src/epd2_identity_service/account_security_storage.py`     | `d133e27eac8d254c0a323955f1a9f29299547e80dbdede521c7d2cadab22bccc`                               |
| `services/identity-service/src/epd2_identity_service/accounts.py`                     | `2dbd33f57287ced33723d35fe315e80c74450c748a8966e9e9f21e484d6958d4`                               |
| `services/identity-service/src/epd2_identity_service/administration.py`               | `1896cfdc61f632e179a8ec9d63ef04bd7d9c78b2e907e330bd835d24980abbf8`                               |
| `services/identity-service/src/epd2_identity_service/api.py`                          | `6d9871fa7d77c7cc609f60a6d35a22c28084847169315fbe24b472a01f12a5f0`                               |
| `services/identity-service/src/epd2_identity_service/assurance.py`                    | `55dbf7f1a313100a29c519401def4731521025830a1beab400066540fcbedece`                               |
| `services/identity-service/src/epd2_identity_service/authentication.py`               | `f197e128ed662f27a4911313d4a487c35be653e7c6f4da7921e15b8c8d8aba57`                               |
| `services/identity-service/src/epd2_identity_service/bootstrap.py`                    | `eee253a0f0926cb8ce7e11f154cced1ac3f5a32211de8c0079bc96a25a15bb4b`                               |
| `services/identity-service/src/epd2_identity_service/codecs.py`                       | `3fe9edd8047882ef8b723e083389bdad0e939b0beacafca5bf67a1c03d55512c`                               |
| `services/identity-service/src/epd2_identity_service/configuration.py`                | `d241e5a99705d35e7c24f7680fdb01039e50f66c8b6285026795377db7a9215c`                               |
| `services/identity-service/src/epd2_identity_service/contacts.py`                     | `26566b4285ab34b68a9c37d1044c8020b80cf79ab9ad5a24cf5014ac0c9dfafb`                               |
| `services/identity-service/src/epd2_identity_service/credentials.py`                  | `93446a87831b2e386c74c73a7e4582efe8d31f22309cb86fe21ddb1241b9bde0`                               |
| `services/identity-service/src/epd2_identity_service/forms.py`                        | `d1e25e1e1efab80aca9c071c418c7ffe3a57a683d408715a99acf9b73f1aa4d2`                               |
| `services/identity-service/src/epd2_identity_service/identifiers.py`                  | `31119e7996cbe3e992c6e46ac36d088c42e46aee5ca1053dacc5aea11e738ce0`                               |
| `services/identity-service/src/epd2_identity_service/linking.py`                      | `d8b28bebf3ef700eccb7bd80c899be2a2d466d32547c838fe6977149633d35ba`                               |
| `services/identity-service/src/epd2_identity_service/mappings.py`                     | `d7c1a4106074ba841250175d047f460df9159f60dc536b4d459b9af93de500d1`                               |
| `services/identity-service/src/epd2_identity_service/mfa.py`                          | `e6f9804054c2efe613de064452cb4d62f6d08ede5df483e39edfc482914b88c9`                               |
| `services/identity-service/src/epd2_identity_service/migration_runner.py`             | `7e2546918237993deb4b65941a19d68038f741535eca083f00d9b638c6cbab52`                               |
| `services/identity-service/src/epd2_identity_service/observability.py`                | `de3be4baa57e7e6d0b855cf54be23e40acf2f92ed8ce45a0b49a3a446dc5078f`                               |
| `services/identity-service/src/epd2_identity_service/passkeys.py`                     | `22a384854306ade958556d83a91135eb2fe0a9bb76cdac5c923e827d3a1042a7`                               |
| `services/identity-service/src/epd2_identity_service/passwords.py`                    | `481901674f82b463f2f2b5a29b59a3351b10918dc58fb5eb95d36e657402acb3`                               |
| `services/identity-service/src/epd2_identity_service/persistence.py`                  | `4648524e6b2ca25d7243aeba6a6508c8edcd86987cf3931afdb207bc17a5e382`                               |
| `services/identity-service/src/epd2_identity_service/proofing.py`                     | `a68757fb303f9d46d4d2b8b9ce5d6171f3059b16331ef34d8d27b6f811a3dd69`                               |
| `services/identity-service/src/epd2_identity_service/providers.py`                    | `b5e5dad3578f8150dd53a00f705214c7567c3af4427e33499dfd02a9f38ba363`                               |
| `services/identity-service/src/epd2_identity_service/recovery.py`                     | `1c16ad061a1be6e0d56b292e6624447e13cb8f17ff5b12909831b6dc719dded6`                               |
| `services/identity-service/src/epd2_identity_service/runtime.py`                      | `2f50e1b4600f5bfd402d25c4f23111f8f9fc6953410f5a124c643998b73ff1fb`                               |
| `services/identity-service/src/epd2_identity_service/secret_storage.py`               | `74a4359f84bb0ccf3d6068197a5c9de3d7e3b232b46085a5b852ac0a60d83d29`                               |
| `services/identity-service/src/epd2_identity_service/service_api.py`                  | `2938b13a506a21823aef7576987fd8ab23b3cf7241d00c79f440f8060beec0ef`                               |
| `services/identity-service/src/epd2_identity_service/sessions.py`                     | `a605ddac620cf0be04ce6b85dbbe7d8c9257b93999542234ad37478088090050`                               |
| `services/identity-service/src/epd2_identity_service/sql_storage.py`                  | `5644e0ac37283e43cc3bd5883090694325b53608f91c60b549a8cb5af008f878`                               |
| `services/identity-service/src/epd2_identity_service/stepup.py`                       | `bf5d0b5f0dedb51cd942201dd0b51805cac72477806588b2558a756f3a839e92`                               |
| `services/identity-service/src/epd2_identity_service/voting_handoff.py`               | `b15731e6db189bc82ae8fb6fb5121920a150515344beecf23dd2d4467c2f91e3`                               |
| `services/identity-service/src/epd2_identity_service/workspaces.py`                   | `efb161d7d5632451e5da9badaa200a002a629658ba7560f398c02fb8d8a9c985`                               |
| `services/identity-service/tests/_pack14_builders.py`                                 | `25ec8ce5e45414d0b840967ed8d8167085dca172fa168e1ec6c649fec87041d7`                               |
| `services/identity-service/tests/conftest.py`                                         | `08eb110f644cc5fb1ac24742eb1fd8cb0bbad511512e416de673a8173ab113df`                               |
| `services/identity-service/tests/test_pack14_integration.py`                          | `efcf9d4e8de528884413566c1a7582727c2741d2a9d656b9319e424aa5a8a941`                               |
| `services/identity-service/tests/test_pack14_invariants.py`                           | `8651c837652ccdb1560fdc76a6d2b8aec0ac11ed79eb97ea967d5b9664b6f195`                               |
| `services/identity-service/tests/test_pack14_persistence.py`                          | `a06c743479a779982fc57c68b6cbd849c86d98129d5a64cbc5861b9361916334`                               |
| `services/identity-service/tests/test_pack14_security.py`                             | `cc77ad2b0d4fd038b73800155afc5ccd78920eac549a2095c0505cfd8ccad4e4`                               |
| `services/identity-service/tests/test_pack14_service_api.py`                          | `d1c4fda8fe885c3d7d304c55aa5a7849d66834f3f1ca3ce217b720003f8e6240`                               |
| `services/identity-service/tests/test_pack14_unit.py`                                 | `12b465ce4ddd8d41549dfb9efeeabae61adc089a2a9fe15d9b57066386a12d89`                               |
| `services/identity-service/tests/test_pack14_workflows.py`                            | `3a681f716099f478931d7cc1d53ce9bbd8c9b57e5fce91131da8ab4c2fc52e02`                               |
| `tests/repository/test_pack14_default_binding.py`                                     | `56e51898d6b414b5b59ec16805cd7e8e3b558869492f584d88c2d5d580c0488a`                               |
| `tests/repository/test_pack14_duplicated_logic_parity.py`                             | `a4f2368de1f3d66828e9008e46929e85e766abd3a4d9024f096900e882f6dd33`                               |
| `tests/repository/test_pack14_fir_matrix.py`                                          | `54411655b4fa7cd3d11d8a8fb7c0f5fd4049688d6291fed0f64bcd04bd5c471f`                               |

## 20. Files changed since the PACK-13 FINAL PASS baseline (20)

| File                                                                | SHA-256                                                            |
| ------------------------------------------------------------------- | ------------------------------------------------------------------ |
| `CHANGELOG.md`                                                      | `6acd13f74990fc1d453e5d6aa41f5bfbfec3f1f1df8cc8c5e9cde555ced083e9` |
| `README.md`                                                         | `582197cb64c1b537d36addee5586c8716deec64055d25456f58bab5176a50e45` |
| `docs/adr/README.md`                                                | `32964654783ea17d6cebef18808cfdf5a71a2b78a280a3ca6a34b5decd20b364` |
| `docs/canonical/canon-version.json`                                 | `abf0b682c9447beeb23551227e8a46ec7727e4a6c81d33e73775e32614f09502` |
| `docs/handover/PACK-09-EXTERNAL-CI-VERIFICATION.log`                | `8543abe417e58c070677423e47deca03bfe1e7ae3957dfd6fa717d959b351589` |
| `docs/handover/PACK-11-EXTERNAL-CI-VERIFICATION.log`                | `18df2300ea25e168d7d49f4bb6a3bc1c00d1e51805af211fa251d3e879577492` |
| `docs/handover/PACK-13-EXTERNAL-CI-VERIFICATION.log`                | `90b12079bf658c3784a98b85e39a8be35704abac29a6b236412de492705a12b8` |
| `docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md`        | `3de0d7187ee0f42aed980def83845a471408ff4c3e8487d4a8f517917e902cb5` |
| `packages/python/epd2-core/src/epd2_core/version.py`                | `7877c46f03f0cd55f0e694fdbc98ccb8a14a3623cf4d8d057fd77ee6c9107b0a` |
| `packages/python/epd2-core/tests/test_version.py`                   | `0fea721084a848a7ab57569fbd990c41bb7d92c1511bf6cfeded8cc059d96018` |
| `packages/typescript/epd2-types/src/version.ts`                     | `d52e574a313a7f58e9f63fb7d05c70ca08a51a2a3599069d95079076bcf5118d` |
| `packages/typescript/epd2-types/tests/version.test.ts`              | `dd198ee187ab6a4094336f8eb855a4984b48adbe618a5f303c4f95f15a0826b0` |
| `scripts/check_canon_0_8_0.py`                                      | `756180e317301ea2841c4cb1e6e51de4be0351f18a33e5c33f084c68f8c65017` |
| `scripts/check_repository.py`                                       | `4746f8b6f0239c7f10b7d119a1cd38a96d7654846f9b29fa1e21de08b9eee5a3` |
| `services/README.md`                                                | `c6905f75b0e65677603a4332bbc3c4a12d2ac6447a9147cc599fde329dc1223b` |
| `services/identity-service/README.md`                               | `4d61fc192a81f43ea9f2db361bc110c3c698974cba2795095c2180b3793415f7` |
| `services/identity-service/src/epd2_identity_service/__init__.py`   | `066d7373f3df7ba10819f376551cd97331362f2696c943dd11dfd14aa5d9dd47` |
| `services/identity-service/src/epd2_identity_service/exceptions.py` | `8ed8bbb53f73467227cb6dae4e5d284076f0d13288f2484661e73d97caae9562` |
| `tests/contract/_schema_helpers.py`                                 | `b9af2ab64efe17310b3f7d883e6cb8d8fb357119617a14bf5b0c4e043e46fac6` |
| `tests/contract/test_reason_codes_registry.py`                      | `e882702a827464c5b9283b9c18ea8ec3363e910d182f246268287ec73a2e98ef` |

## 21. Files removed

**None.** The cumulative archive only grows; no path present in the
PACK-13 FINAL PASS baseline is missing from this one.

## 22. Archive contents and digest

|                      |           |
| -------------------- | --------- |
| Files in the archive | **1056**  |
| Repository version   | `0.14.0`  |
| Canon version        | `0.8.0`   |
| Required paths       | 870 / 870 |

The SHA-256 of the delivered archive is reported in the delivery message
accompanying it, and is deliberately not printed here: a file cannot
contain the digest of the archive that contains it.

```bash
sha256sum EPD2_PACK-14_IDENTITY_AUTHENTICATION_ACCOUNT_SECURITY_0.14.0_FINAL_PASS.zip
```
