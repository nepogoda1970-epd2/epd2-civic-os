**Round:** PACK-14 — implementation candidate. **NOT PASS. NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**
**Repository version:** `0.13.0` → `0.14.0` · **Canon version:** unchanged at `0.8.0`

> **Superseding status note, added by the PACK-14 FINAL PASS round
> (2026-07-30).** The header above records the implementation-candidate
> round that wrote this document and is retained unchanged as the
> historical record. External GitHub Actions has since run against this
> exact tree and **passed every stage**, so PACK-14 is now **FINAL PASS**
> at `REPOSITORY_VERSION 0.14.0` / `CANON_VERSION 0.8.0`. The PASS changes
> the _round's_ status and nothing else: no limitation below is closed by
> it, and **NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.** See
> `docs/handover/PACK-14-FINAL-PASS-REPORT.md` and
> `docs/handover/PACK-14-EXTERNAL-CI-VERIFICATION-RESULT.md`.

# PACK-14 — Implementation Report

## 1. What this round is

The reference implementation of Identity, Authentication & Account
Security, built against
`EPD2_PACK-13_..._0.13.0_FINAL_PASS.zip` as the repository baseline and
`EPD2_PACK-14_..._SPEC_ADR_ARCHITECTURE_CORRECTED_V2.zip` as the
architecture.

It is a **candidate**. No external pipeline has verified it, and §7 below
records exactly which local checks ran and which could not.

## 2. Where the code went

`services/identity-service`, extended **in place**. Specification §4.1
(closing OD-P14-02) assigns all six contexts to it, because it is already
canon 19d.8's owner of `AuthenticationContext` and splitting
authentication away from the service that owns the authentication context
would put the two halves of one decision in two places. **No parallel
authentication service was created.**

34 new source modules. Twenty-nine came from the first candidate, in
dependency order: `identifiers`,
`secret_storage`, `configuration`, `workspaces`, `accounts`, `contacts`,
`credentials`, `passkeys`, `passwords`, `mfa`, `assurance`, `sessions`,
`stepup`, `bootstrap`, `voting_handoff`, `authentication`, `recovery`,
`proofing`, `providers`, `linking`, `administration`, `observability`,
`forms`, `persistence`, `mappings`, `account_security_events`,
`account_security_storage`, `account_security_application`, `api`. Plus
1136 lines appended to the existing `exceptions.py` — one class per
registered reason code.

Five came from the **correction round** (§12), and they are the ones that
turn described persistence into applied persistence and a catalogue into
an adapter: `codecs` (type-hint-driven serialization that refuses raw
bytes and naive datetimes), `migration_runner` (ordered, transactional,
checksum-guarded application of the ten SQL artefacts in
`services/identity-service/migrations/`), `sql_storage` (eleven durable
adapters, a `UnitOfWork` and the optimistic-concurrency guard),
`service_api` (the runnable request/response boundary) and `runtime` (the
composition root — one function, and the only place a default binding is
chosen).

Ownership of canon 7.2's `Account` and canon 7.3's `IdentityRecord` is
**unchanged**.

## 3. The five decisions worth reading the code for

**`FIR-INV-001` survives.** This is the round that most threatened it.
The five identifier spaces are distinct Python types even though they are
all UUIDs underneath, so mypy refuses at the call site; what crosses a
domain boundary is a `ScopedIdentityReference` derived per purpose, per
organizational scope and per domain owner from a per-deployment secret
salt; and `reject_prohibited_payload_keys` runs before any event, audit
record or API response exists. Two references derived for two purposes
from one account do not compare equal.

**The canonical status enum is not extended.** `AccountLock`,
`AccountRestriction` of the security class, `AccountClosureRequest` state
and lifecycle outcomes carry what would otherwise have been `locked`,
`closure_pending` and `deleted_or_anonymized`. An account can be `active`
with a lock in force and a closure request pending, and each fact is
separately queryable and separately reversible. This closed OD-P14-01
without a canon amendment.

**All four security ports refuse by default.**
`UnboundWebAuthnVerifier`, `UnavailablePasswordHasher`,
`UnboundBreachedPasswordChecker` and `UnboundAssertionSignatureVerifier`
are the default bindings, and all four raise. The task forbids inventing
production cryptography and the forbidding is correct: a hand-written
verifier that passes its own tests is the most dangerous kind of working
code. The deterministic test providers are separate classes with
self-declaring names, so no production path acquires a "test mode"
branch.

The breached-password checker is the one that changed in the correction
round, and it changed because the first candidate got it wrong: it
shipped a `NoBreachedPasswordChecker` that reported nothing as breached.
That is the one direction a security default must never fail — the
deployment would have learned about it after a credential-stuffing
incident rather than at enrollment. The replacement raises rather than
returning either boolean, because `False` claims a check that did not
happen and `True` refuses every password for the wrong reason. The one
governed exception, `PasswordDegradedModeDecision`, permits
**authentication against an already stored hash** and nothing else; it
has four fields and no field that could re-open enrollment, and a test
asserts the field set.

**`MfaFactorClass` has no `sms_otp` member.** OD-P14-09 as a type rather
than as a rule: `parse_factor_class("sms_otp")` reaches
`refuse_sms_otp_as_factor`, which always raises. SMS OTP carries no
assurance level at all, and the system operates with no SMS provider.

**`VotingHandoffIssuance` has no account field.** Not a scoped reference,
not a session identifier — nothing. The issuing decision (assurance
`high`, a bound step-up, a usable account) is made _before_ the record
exists and audited on the account's own side; what survives is that an
artifact for a voting context was issued. That is the whole of ADR-088's
non-reversibility property, expressed as a field set.

## 4. Numbers

| Thing                               | Count                                                  |
| ----------------------------------- | ------------------------------------------------------ |
| Source modules in the service       | 40 (34 new: 29 candidate · 5 correction)               |
| Source lines                        | 16 387                                                 |
| Test modules in the service         | 12 (2 added by the correction round)                   |
| Tests in `identity-service`         | 288 (46 added by the correction round)                 |
| New repository-level tests          | 28 (15 parity · 4 FIR matrix · 9 default binding)      |
| New contract-suite parametrizations | 4 (`pack-14`)                                          |
| Registered reason codes             | 213 (131 additive · 22 redeclared · 60 `*_RECORDED`)   |
| Event types                         | 59, in 9 families                                      |
| API operations                      | 42 catalogued · **12 routed** by the reference adapter |
| Migration definitions               | 10, expand-only — with 10 SQL artefacts on disk        |
| Schema the artefacts create         | 29 tables · 35 indexes (9 unique · 10 expiry)          |
| Full local suite                    | **4898 passed, 5 skipped**                             |

## 5. Version changes

`REPOSITORY_VERSION` `0.13.0` → `0.14.0` in
`packages/python/epd2-core/src/epd2_core/version.py` and
`packages/typescript/epd2-types/src/version.ts`, with the matching
`CHANGELOG.md` entry and both version tests updated.
`scripts/check_canon_0_8_0.py`'s `EXPECTED_REPOSITORY_VERSION` follows.
`docs/canonical/canon-version.json` widens
`repository_compatibility` to `<0.15.0` and gains
`identity_context_implementation_status: "reference_implementation"`.

**`CANON_VERSION` remains `0.8.0`.** The round amends no canon: it reuses
canon 19d.2's and 19d.8's existing four-value assurance scale rather than
inventing an AAL-0…AAL-3 vocabulary, keeps `AccountStatus` at six values,
and holds `SessionRecord` at service level on PACK-12's
`PrivilegedSession` precedent.

## 6. CI

**No CI gate was weakened and no file was excluded from any check.**
`.github/workflows/ci.yml` is unchanged, and it needed no change:
`identity-service` is already in `make typecheck`'s per-service list, in
`pytest`'s `testpaths` and in Ruff's `src` list, because PACK-02 put it
there. That is the practical benefit of extending an existing service
rather than adding a new one.

`scripts/check_repository.py` gains 46 required paths (803 → 849): the
ten ADRs, the twenty-two specification documents, the twelve
implementation documents, the handover report, the reason-code registry
and the two new repository tests.

## 7. Local verification — exactly what ran

Run in this sandbox, from the repository root:

| Command                                   | Result                                                                                 |
| ----------------------------------------- | -------------------------------------------------------------------------------------- |
| `python scripts/check_repository.py`      | **OK: all 867 required paths are present**                                             |
| `python scripts/check_forbidden_files.py` | **OK**                                                                                 |
| `python scripts/verify_versions.py`       | **OK: all version sources are consistent**                                             |
| `python scripts/check_canon_0_8_0.py`     | **OK: all 18 canon 0.8.0 amendment checks passed**                                     |
| `ruff format --check .`                   | **passed** (3 pre-existing baseline files noted below)                                 |
| `ruff check .`                            | **All checks passed!**                                                                 |
| `mypy` (all 23 groups)                    | **Success** in every group; `identity-service`: **no issues found in 52 source files** |
| `pytest`                                  | **4898 passed, 5 skipped**                                                             |

### 7.1 What could **not** run locally, and is therefore not claimed

This sandbox has no network access to npm or PyPI, so every
Node-dependent stage is unrun. **None of the following is claimed to
pass:** Prettier format check, ESLint, both TypeScript typechecks, the
`epd2-types` tests, the frontend tests, the Next.js production build, and
the browser, accessibility and visual-regression suites. This round
changes no frontend file and no TypeScript file other than
`version.ts` and `version.test.ts`, so the expectation is that they pass
— but an expectation is not a result, and it is recorded here as one.

The 5 skips are pre-existing and unrelated to this round: one is
`hypothesis` being uninstallable here, four are the documented
CT-00-10/11/12 not-applicable declarations.

### 7.2 Three files at baseline bytes

`docs/adr/ADR-051-*.md`, `frontend/web-shell/foundation/storage-policy.ts`
and `frontend/web-shell/foundation/types.ts` are left exactly as the
PACK-13 FINAL PASS tree had them. The Prettier available in this sandbox
is 3.8.1 rather than the pinned version, and reformatting them here would
have produced a diff CI would then reverse. This is carried forward from
the PACK-13 round's own note.

## 8. Master Register

The cumulative register from the accepted PACK-14 SPEC+ADR archive was
used. **It was not replaced by standalone V5 and no PACK-13 record was
rolled back.** 141 FIR entries before, 141 after.

Four changes, and no others:

1. **§1.15** — the PACK-14 implementation candidate round record.
2. **`FIR-BASE-001`** — a "current candidate (NOT a PASS baseline)" block
   above the unchanged PACK-13 FINAL PASS baseline. The PASS baseline is
   deliberately not moved: no external pipeline has verified this round.
3. **`FIR-ROADMAP-004`** — `approved` → `candidate`. Not `implemented`,
   and not `implemented in reference form`.
4. **§21** — a new "Candidate, not yet externally verified" subsection,
   listed separately from the implemented list, plus a qualification on
   the existing `identity/auth` line under "Specified but not
   implemented".

`FIR-UX-011` stays **future**. `FIR-TRUST-001`, `FIR-REPRESENT-001` and
`FIR-INCLUSION-001` stay future. No future obligation was removed.

## 9. The specification documents were not rewritten

The twenty-two PACK-14 specification documents and the ten ADRs keep
their own round headers, which still say "specification and ADR only" and
"repository version unchanged at `0.13.0`". That is deliberate: they are
the record of that round, and rewriting them to read as though they had
always been an implementation is exactly what PACK-13's FINAL PASS round
was told not to do with its own candidate report.

Two documents are the exception, because task §34 lists them as documents
this round must "create or update": `PACK-14-EVENT-CATALOG.md` and
`PACK-14-REASON-CODE-CATALOG.md`. Each now has a **Part A** — the
specification round's text, unchanged — and a **Part B** recording what
the implementation actually emits and registers, with the boundary marked
in the document.

## 10. Known limitations

Restated from `PACK-14-OPEN-ITEMS.md` because a report that hides them in
another file is a report nobody reads twice:

1. **Persistence is a reference path, not a production data plane.** It
   is real — ten applied SQL artefacts, 29 tables, 35 indexes, eleven
   durable adapters, a transaction boundary and an optimistic-concurrency
   guard — and it runs on **SQLite through the standard library**. No
   PostgreSQL is deployed; no replication, backup, failover or
   operational durability is provided or claimed. The `InMemory*`
   adapters remain as explicit **test** adapters and are not the default
   runtime binding.
2. **No provider of any kind is integrated** — no IAM, no eID, no email,
   no SMS, no HSM or KMS.
3. **The service boundary is a runnable reference adapter, not a
   gateway.** It parses, validates, authorizes by origin and audience,
   carries session context, honours idempotency and version fields and
   answers with reason codes — for **12 of the 42** catalogued
   operations. It is transport-agnostic: no HTTP server, no TLS, no
   public deployment, no production gateway.
4. **No frontend was built.** `FIR-UX-011` stays future.
5. **Four security ports are unbound**, and all four **refuse**. An
   unconfigured deployment fails at the first attempt rather than after
   an incident.
6. **The audit store is bound in memory by the composition root.**
   `audit-core` owns durable audit persistence; binding a durable audit
   adapter is that service's round to do, and a deployment passes its own
   in the meantime. Recorded here rather than glossed.
7. **XSS-safe output is a deployment obligation**, not a control this
   round can verify — there is no rendering layer here.
8. **External CI has not run.**

## 11. `OD-P14-07`

**Open, pending legal confirmation. It does not block this
implementation.** Provisional safe schedules exist for all ten record
classes; every `duration_confirmed` flag is `False` and a test asserts
it; deletion under a legal hold refuses; an unknown hold state fails
closed; an open dispute preserves the record; and a destructive
disposition against an unconfirmed schedule is refused with
`RETENTION_SCHEDULE_UNCONFIRMED`. **Nothing in this round destroys
evidence**, because nothing in this round can.

## 12. The correction round

The first candidate archive was reviewed before external CI and three
findings were returned. They are recorded here rather than folded
silently into the text above, because a report that quietly absorbs its
own corrections teaches nobody anything.

**Finding 1 — the persistence was metadata, not persistence.** The
candidate shipped in-memory adapters plus Python objects _describing_
migrations, constraints and indexes. Descriptions of DDL are not DDL.
Corrected by adding ten real SQL artefacts, a transactional
checksum-guarded `migration_runner` that applies them, eleven durable
adapters in `sql_storage`, a `UnitOfWork` transaction boundary, a
monotonic optimistic-concurrency guard, and a `codecs` module that
serializes typed identifiers safely and refuses raw bytes and naive
datetimes outright. The guard is monotonic (`WHERE version < ?`) rather
than exact (`WHERE version = ? - 1`) because some operations apply two
domain transitions before one save — `verify_contact` moves a record from
version 1 to version 3 — and an exact guard would have made a correct
sequence look like a conflict.

**Finding 2 — the breached-password default was permissive.** Corrected
as described in §3. No new or changed password can now bypass breach
checking; authentication against an already stored hash is the only
thing the governed degraded-mode decision can permit.

**Finding 3 — `api.py` was an endpoint catalogue, not a boundary.**
Corrected by adding `service_api`, a transport-agnostic runnable adapter:
`ApiRequest` in, `ApiResponse` out, envelope validation in a fixed order
(origin → session → idempotency → version), audience assertion, a
reason code on **every** response including the successful ones, and
`assert_response_safe` running in `ApiResponse.__post_init__` so a
response carrying a prohibited identifier or a secret cannot be
constructed at all. `ROUTED_OPERATIONS` (12) and
`CONTRACT_ONLY_OPERATIONS` (30) are both named constants, so no document
can imply that all 42 catalogued operations run.

**What the correction did not do.** No functional scope was expanded, no
frontend was built, no dependency was added (`sqlite3` is standard
library; `uv.lock` and `package-lock.json` are byte-identical), no CI
gate was weakened, no existing test was deleted, and
`REPOSITORY_VERSION 0.14.0` / `CANON_VERSION 0.8.0` are unchanged. The
status block below is unchanged too: this is still a candidate.

## 13. Status

```text
PACK-14 IMPLEMENTATION CANDIDATE COMPLETE
REPOSITORY_VERSION 0.14.0
CANON_VERSION 0.8.0
LOCAL VERIFICATION COMPLETE
EXTERNAL CI NOT YET VERIFIED
NOT FINAL PASS
NOT PRODUCTION READY
NOT LEGALLY ACTIVATED
```
