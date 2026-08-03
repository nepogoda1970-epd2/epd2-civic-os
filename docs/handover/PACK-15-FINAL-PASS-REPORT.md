# PACK-15 — Voting Trust Boundary, Eligibility & Credential Separation — FINAL PASS

```text
PACK-15 FINAL PASS
REPOSITORY_VERSION 0.15.0
CANON_VERSION 0.8.0
EXTERNAL CI PASS
HYGIENE CORRECTION VERIFIED
NOT PRODUCTION READY
NOT LEGALLY ACTIVATED
```

**Archive:** `EPD2_PACK-15_VOTING_TRUST_BOUNDARY_ELIGIBILITY_CREDENTIAL_SEPARATION_0.15.0_FINAL_PASS.zip`
**Authoritative register:** `docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md`
**ADRs:** ADR-089 through ADR-098

**This is a packaging round.** No implementation was rebuilt. No service
module, migration, API catalogue, event schema, reason code, test, CI
definition, lock file or frontend file changed. The archive is the
externally verified tree plus the status, register and handover documents
that close the round.

---

## 1. Lineage

| Stage                         | Archive                                                                       | Outcome                                                                |
| ----------------------------- | ----------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| Baseline                      | `EPD2_PACK-14_IDENTITY_AUTHENTICATION_ACCOUNT_SECURITY_0.14.0_FINAL_PASS.zip` | authoritative cumulative PASS baseline entering this pack              |
| Specification + ADR           | `..._0.15.0_SPEC_ADR.zip`                                                     | specification only; no code                                            |
| Corrected specification + ADR | `..._0.15.0_SPEC_ADR_ARCHITECTURE_CORRECTED.zip`                              | closed `OD-P15-01`…`OD-P15-04`, `OD-P15-07`; adopted register V6       |
| Foundation slice              | `..._FOUNDATION_SLICE_NOT_A_CANDIDATE.zip`                                    | partial; explicitly not a candidate                                    |
| Implementation in progress    | `..._IMPLEMENTATION_IN_PROGRESS_NOT_A_CANDIDATE.zip`                          | five groups still open; explicitly not a candidate                     |
| Implementation candidate      | `..._0.15.0_CANDIDATE.zip`                                                    | all five groups closed; version moved to `0.15.0`                      |
| Prettier correction           | `..._0.15.0_CANDIDATE_PRETTIER.zip`                                           | repository-wide Prettier pass                                          |
| Prettier 3.9.6 correction     | `..._0.15.0_CANDIDATE_PRETTIER_396.zip`                                       | three TypeScript files returned to the pinned formatter's form         |
| mypy correction               | `..._0.15.0_CANDIDATE_PRETTIER_396_MYPY.zip`                                  | one test-file type correction; CI error reproduced locally, then fixed |
| Hygiene correction            | `..._0.15.0_CANDIDATE_HYGIENE_CORRECTED.zip`                                  | stale nested `epd2-civic-os/` repository removed                       |
| **FINAL PASS**                | **this archive**                                                              | **externally verified clean tree**                                     |

The intermediate archives are named here as history. **None of them is
contained in this archive**, and no verification artifact is either.

---

## 2. External verification — the authoritative result

GitHub Actions, `ubuntu-latest`, Python 3.12, Node.js 22.

| Stage                            | Result                        |
| -------------------------------- | ----------------------------- |
| Required paths                   | PASS — 983 / 983              |
| Forbidden paths                  | PASS                          |
| Version consistency              | PASS                          |
| Ruff format                      | PASS — **436 files**          |
| Prettier                         | PASS                          |
| Ruff lint                        | PASS                          |
| ESLint                           | PASS                          |
| mypy                             | PASS                          |
| Python tests                     | PASS — 5343 passed, 4 skipped |
| TypeScript package tests         | PASS — 3 passed               |
| Node tests                       | PASS — 41 passed              |
| Frontend tests                   | PASS — 23 passed              |
| Next.js production build         | PASS                          |
| Static pages                     | 48 / 48                       |
| Browser / visual / accessibility | PASS — 135 passed             |

Read back from the committed run log: `436 files already formatted`;
`5343 passed, 4 skipped`; `Test Files 3 passed`, `Tests 23 passed`;
`Generating static pages (48/48)`; `135 passed (1.4m)`.

### 2.1 Verification hashes

| Artifact                    | SHA-256                                                            | Recomputed |
| --------------------------- | ------------------------------------------------------------------ | ---------- |
| Outer verification artifact | `e8fd5b2a14e61be95be49afd461467a9ddbaab8f5dc70db68a9ab5f0bb9cd1b4` | **match**  |
| Internal verification ZIP   | `7ea70c5b9ba3c7350e1d0831148c2be560512e17f78392031c1b0e5e7ea3df8c` | **match**  |

Both were recomputed from the supplied files rather than transcribed.

### 2.2 Supersession of earlier artifacts

**Every verification artifact produced for a tree containing
`epd2-civic-os/` is superseded and may not be cited as FINAL PASS
evidence.** In particular the run reporting `Ruff format: 609 files`
verified a tree that also held a complete stale copy of the repository at
`REPOSITORY_VERSION 0.6.0` / `CANON_VERSION 0.6.0`. Its outer digest was
`675efb93…`; its internal ZIP computed to `d5bba0a6…`, which did not
match the digest supplied with it at the time. That discrepancy is
recorded in `PACK-15-HYGIENE-CORRECTION-REPORT.md` and is now moot: the
run it belonged to is superseded.

The arithmetic that exposed the problem, and now confirms its removal:

```
436  Python files in the clean tree      -> this run reports 436
173  Python files inside epd2-civic-os/
---
609  reported by the superseded run
```

### 2.3 The archive is the verified tree

The tree inside the verification artifact was compared file by file
against this archive: **1171 source files, zero differences — no file
only on one side, no content difference.** The artifact additionally
holds 753 files the run itself produced (`__pycache__`, `.hypothesis`,
tool caches, Playwright output, a `tsbuildinfo`, five root scratch
files); none of them is in this archive.

---

## 3. Three stages, kept distinct

This project's rule has been that a claim names the run that supports it.

1. **Local partial verification.** Performed in a sandbox where PyPI and
   the npm registry return HTTP 403. `pytest`, `mypy` and `ruff` were
   available and executed (5335 passed / 5 skipped locally, mypy clean,
   Ruff clean, 436 files). The entire npm surface — TypeScript typecheck,
   frontend tests, Playwright, axe, `next build`, Prettier at the pinned
   version — could not run at all. The local difference of eight tests
   and one skip against CI is `hypothesis`, which CI has and the sandbox
   does not.
2. **External GitHub Actions PASS.** Section 2. This is the authoritative
   verification and the only evidence for the frontend half.
3. **FINAL PASS assembly.** This round: no implementation change, the
   documents that close the pack, and the archive.

---

## 4. What PACK-15 implements

The separation between knowing **who someone is** and knowing **that a
vote was cast**, made structural rather than procedural.

### 4.1 Components

| Component                  | Location                                                                                                                                                              |
| -------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Voting context registry    | `governance-service/voting_contexts.py`, `voting_context_sql_storage.py`                                                                                              |
| Eligibility and assertions | `eligibility-service/voting_eligibility.py`, `voting_attributes.py`, `voting_timing.py`                                                                               |
| Assertion Issuer           | `eligibility-service/voting_assertion_issuer.py`                                                                                                                      |
| PACK-14 handoff acceptance | `eligibility-service/voting_handoff.py`                                                                                                                               |
| Voting credentials         | `credential-service/voting_credentials.py`, `voting_credential_application.py`                                                                                        |
| Audit streams and bundles  | `audit-core/voting_evidence_bundle.py`, `voting_audit_sql_storage.py`                                                                                                 |
| Authorization matrix       | `governance-service/voting_authorization.py`                                                                                                                          |
| Shared migration runner    | `epd2-core/sqlite_migrations.py`                                                                                                                                      |
| Shared API contracts       | `epd2-core/api_contracts.py`                                                                                                                                          |
| Composition roots          | `voting_trust_runtime.py`, `voting_credential_runtime.py`                                                                                                             |
| Frontend WS-02 / WS-03     | `web-shell/foundation/voting-trust-policy.ts`, `public/voting-content.ts`, `components/voting-trust.tsx`, `app/mitwirkung/abstimmungen/page.tsx`, `app/vote/page.tsx` |

### 4.2 Migrations — ten files across seven sets, one database per boundary

| Database                | Migration set                                      |
| ----------------------- | -------------------------------------------------- |
| Eligibility             | `eligibility-service/migrations/eligibility/`      |
| Assertion issuer        | `eligibility-service/migrations/assertion-issuer/` |
| Voting credentials      | `credential-service/migrations/`                   |
| Voting context registry | `governance-service/migrations/`                   |
| Identity-side audit     | `audit-core/migrations/identity-side/`             |
| Voting-side audit       | `audit-core/migrations/voting-side/`               |
| Neutral audit           | `audit-core/migrations/neutral/`                   |

Separate files mean a cross-boundary foreign key is not _expressible_,
which is stronger than not written.

### 4.3 APIs — 22 endpoints

Nine identity-side, four voting-side, five governance, four audit, over
`epd2_core.api_contracts`. Every endpoint declares its obligations, its
authorized roles and its reason codes; a consequential endpoint may waive
none of them; an operation name may not exist on both sides of the trust
boundary; every response body is scanned at every nesting depth before it
leaves.

### 4.4 Events and reason codes

Eight event payload schemas (`contracts/events/pack15-*.v1.schema.json`)
over PACK-13's canonical envelope. **89 reason codes** in
`contracts/reason-codes/pack-15.yml`, no duplicates, every entry carrying
all seven required fields.

`ALREADY_VOTED` and `PARTICIPATION_CONFIRMED` are **absent by design and
may never be added**: emitting either would require knowing that a
particular participant's credential was redeemed, which is the linkage
this pack removes.

---

## 5. Evidence for the load-bearing guarantees

Each is asserted by executed, passing tests — 434 PACK-15 tests inside
the 5343 the external run reports.

### 5.1 WS-03 isolation

The ordinary workspace transmits only PACK-14's opaque, single-use,
audience- and context-bound handoff artifact; ten prohibited identity
fields are refused on arrival rather than trusted absent. Origin and
audience are checked **before** anything else is read, audience
comparison is constant-time, and the artifact's value is never stored —
only its SHA-256 digest, which is the one-time key. Credential issuance
and redemption are refused from any origin other than the isolated voting
workspace, and refused rather than redirected. The frontend policy module
permits no browser storage of any kind for WS-03; the browser spec
asserts zero cookies and empty storage.

### 5.2 Unlinkability

The spent-nonce record is a **set** — three columns, no value column —
so there is nowhere to record a credential beside a nonce. The
participation-unit ledger records _that_ an assertion was minted, never
_which_. The four boundaries are separate database files. Tests assert
against a real migrated schema that `spent_nonce` has exactly three
columns, that no voting-side table carries an identity-side column, and
that no foreign key leaves its own database. The bounded idempotency
window is the only place the two references coexist; it is capped at 900
seconds and `assert_not_durable` refuses to make it permanent.

### 5.3 No intermediate tally

Outcome-bearing keys are refused before context closure; a pre-closure
bundle carries no totals; `assert_no_intermediate_tally` is applied to
every bundle payload. Pre-closure export requires a dual-control
reference as a **CHECK constraint**, not an application-layer assertion.

### 5.4 Revocation cutoff

`redeemed` is absorbing — the transition table leads nowhere out of it.
Revocation after the cutoff fails a database CHECK. The revocation
interface has **no participant parameter**, so "revoke this person's
vote" is not a request that can be expressed. The API boundary requires a
second signature, so `DUAL_CONTROL_REQUIRED` names a path that exists.

### 5.5 Participation-status minimization

No endpoint accepts a participant reference. `credential.status` answers
only against a reference the caller already holds, and an unknown
reference returns the same shape as a withdrawn one, so it is not an
existence oracle. There is no search endpoint on the voting side — not a
restricted one, none. Identity-side surfaces return no credential or
ballot fact, because that side holds none.

### 5.6 Audit separation

Six streams in three separate database files: identity-side (AS-01,
AS-02), voting-side (AS-03, AS-04), neutral (AS-05, AS-06 and the export
log). Each stream has its own key space and **no table carries two of
them**. Selecting a voting-side table through the identity-side
connection is not a permission failure — the table does not exist there,
and a test catches exactly that error.

### 5.7 Authorization separation

Ten roles and a capability matrix validated **at import time**, so a role
added without capabilities fails when the module loads. Eight structural
rules: no role holds eligibility and issuance and tally; the Credential
Issuer holds no identity-record access; the Eligibility Officer holds no
credential-secret access; no auditor — and no other role — spans the
audit stream groups; security and system administrator are distinct with
neither capability set containing the other; no self-review; privileged
export and break-glass need two distinct approvers holding different
roles.

### 5.8 Frontend and accessibility

Verified only by the external run, and now verified: ESLint PASS,
frontend tests 23 passed, Node tests 41 passed, TypeScript package tests
3 passed, Next.js production build PASS with **48/48** static pages, and
**135** browser, visual and accessibility tests passed.

---

## 6. Defects found and closed during the pack

Recorded because a FINAL PASS listing only successes is not evidence.

1. **A failed mint left a participation-unit claim behind**, which the
   next successful write committed — permanently refusing a participant
   with `CREDENTIAL_ALREADY_ISSUED` for an assertion they never received.
   Fixed with a rollback guard; two tests pin it.
2. **The voting side's identity-field scan was shallow**, checking only
   top-level request keys while the outbound scan walked every depth —
   and the inbound bodies are nested. Both directions now walk every
   depth.
3. **An out-of-range client-supplied minting delay crashed the boundary**
   through a bare `ValueError`. Now refused with `API_REQUEST_MALFORMED`.
4. **The assurance flag crossed the boundary and was never read** — a
   fail-open in a control the specification marks fail-closed. Found
   while building the traceability matrix. Now refused with
   `ELIGIBILITY_ASSURANCE_INSUFFICIENT`.
5. **A stale nested repository at `epd2-civic-os/`** — flagged by PACK-08,
   PACK-10, PACK-11 and PACK-14 and finally removed here.

Two contract corrections: `credential.revoke` now genuinely requires dual
control, and two governance failures were split into
`VOTING_CONTEXT_VERSION_CONFLICT` (retryable) and
`VOTING_CONTEXT_VERSION_FROZEN` (not).

---

## 7. Master Register update summary

Four changes, and nothing else in that file:

1. Round record **1.19 — PACK-15 FINAL PASS**.
2. `FIR-BASE-001`: PACK-15 becomes the authoritative cumulative PASS
   baseline; PACK-14 becomes the previous one; the candidate pointer is
   replaced.
3. `FIR-ROADMAP-005`: `candidate` → **`implemented in reference form`** —
   not `implemented`, because no provider is bound and nothing is
   deployed.
4. Section 21's implementation summary moves PACK-15 out of the
   "candidate, not yet externally verified" subsection.

**Preserved unchanged:** every other entry and status, `FIR-OSS-001`
through `FIR-OSS-006`, `FIR-UX-011` (still **future** — no FRONT-PACK was
built and no page catalogue exists), `FIR-ROADMAP-006` (PACK-16),
`FIR-ROADMAP-007`, `FIR-ROADMAP-008` and every later obligation.
`FIR-INV-002` remains **partially addressed and future**: PACK-15 closes
the identity-to-credential half, the credential-to-ballot half is
PACK-16's, and neither alone closes the invariant. **No future obligation
was removed and no entry was rolled back.**

---

## 8. Archive

**File count: 1172** — the 1171 externally verified files plus this
report.

`scripts/check_repository.py` was deliberately **not** modified: the
external run verified 983/983 required paths, and adding this report to
`REQUIRED_PATHS` would change a number the run has already certified.

### 8.1 Hygiene confirmation

| Excluded                                                                     | Present in archive |
| ---------------------------------------------------------------------------- | ------------------ |
| `.git`, `.venv`, `node_modules`, `.next`                                     | none               |
| `__pycache__`, `*.pyc`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`        | none               |
| `.hypothesis`, editor caches                                                 | none               |
| Temporary databases, generated secrets, `.env` files                         | none               |
| Verification artifacts, embedded verification ZIP                            | none               |
| Candidate ZIPs, nested ZIPs of any kind                                      | none               |
| Build outputs (`.tsbuildinfo`, Playwright output)                            | none               |
| Temporary logs, root scratch files                                           | none               |
| `FOUNDATION_SLICE`, `IMPLEMENTATION_IN_PROGRESS`, `NOT_A_CANDIDATE` archives | none               |
| Nested `epd2-civic-os/` repository tree                                      | none               |

| Confirmed              | Result                           |
| ---------------------- | -------------------------------- |
| Duplicate paths        | none — 1172 entries, 1172 unique |
| Repository roots       | exactly one                      |
| `uv.lock`              | exactly one                      |
| `package-lock.json`    | exactly one                      |
| `epd2_core/version.py` | exactly one                      |
| Stale version `0.6.0`  | none                             |

### 8.2 Changed documents

| Document                                        | Change                                                   |
| ----------------------------------------------- | -------------------------------------------------------- |
| `PACK-15-FINAL-PASS-REPORT.md`                  | new — this file                                          |
| `PACK-15-IMPLEMENTATION-REPORT.md`              | status block; external CI section                        |
| `PACK-15-TEST-EVIDENCE.md`                      | status block; external CI section                        |
| `PACK-15-SECURITY-EVIDENCE.md`                  | status block; external CI section                        |
| `PACK-15-PRIVACY-EVIDENCE.md`                   | status block; external CI section                        |
| `PACK-15-TRACEABILITY-MATRIX.md`                | status block; external CI section                        |
| `PACK-15-IMPLEMENTATION-STATUS.md`              | status block                                             |
| `PACK-15-HYGIENE-CORRECTION-REPORT.md`          | status block — the correction is now externally verified |
| `EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md` | round record 1.19; `FIR-BASE-001`; `FIR-ROADMAP-005`     |
| `CHANGELOG.md`                                  | `0.15.0` entry records the external PASS                 |
| `README.md`                                     | status line records the external PASS                    |

No source, migration, contract, event schema, reason code, test, CI
definition, lock file or frontend file was touched.

---

## 9. What FINAL PASS does not mean

The pipeline verifies the repository. It binds no provider and deploys
nothing.

- **No production key custody.** `FutureKeyServiceCustody` refuses every
  call; everything signed in tests is signed with a reference HMAC key.
- **No transport layer.** The API is transport-agnostic values; TLS, rate
  limiting, request-size limits and DoS resistance are deployment
  concerns this repository does not implement.
- **No production database.** SQLite is the reference persistence. The
  constraints carrying the guarantees port directly; the concurrency
  behaviour under production load does not.
- **The credential-to-ballot half of unlinkability is PACK-16's.**
- **Six acceptance criteria rest on absence rather than on a control** —
  no import path exists today, and nothing fails when someone adds one.
  They are marked in the traceability matrix rather than counted as
  satisfied.

**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**

---

## 10. Handover

**Do not proceed to PACK-16.** PACK-15 hands it a boundary and nothing
else.
