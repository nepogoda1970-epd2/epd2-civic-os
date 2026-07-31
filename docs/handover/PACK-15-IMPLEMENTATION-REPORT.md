# PACK-15 — Implementation report

```text
PACK-15 IMPLEMENTATION CANDIDATE
PARTIAL LOCAL VERIFICATION ONLY
DEPENDENCY INSTALLATION BLOCKED BY SANDBOX NETWORK POLICY
EXTERNAL CI NOT YET VERIFIED
NOT FINAL PASS
NOT PRODUCTION READY
NOT LEGALLY ACTIVATED
```

**Repository version:** `0.15.0` · **Canon version:** `0.8.0` (unchanged)
**Baseline:** `EPD2_PACK-14_IDENTITY_AUTHENTICATION_ACCOUNT_SECURITY_0.14.0_FINAL_PASS.zip`
**Authoritative register:** `docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md`
**ADRs:** ADR-089 through ADR-098

---

## 1. What this round built

PACK-15 implements the voting trust boundary: the separation between
knowing **who someone is** and knowing **that a vote was cast**. The
specification and ADR round defined it; the architecture-correction round
closed five open decisions; this round is the code.

The whole design turns on one structural cut, ADR-093's "set, not map":

> The spent-nonce record is a **set**. It has three columns and no value
> column. No store, log, event, trace, backup or export contains both an
> assertion reference and a credential reference for the same
> participation.

Everything else follows from making that cut real in a schema rather than
in a rule. A rule survives until the next person who needs a number in a
hurry; a missing column survives an operator with a SQL prompt, a backup
tape and a court order.

---

## 2. Scope of this round in particular

The preceding round left five implementation groups open and refused to
call the archive a candidate while they were. This round closed all five:

| Group | What was built |
| ----- | -------------- |
| 1. Durable persistence and migrations | Ten migration files across seven migration **sets**, SQL adapters for every store port in four services, two composition roots, and transactional and concurrency tests |
| 2. Versioned API | A shared contract layer in `epd2-core` plus four per-service endpoint catalogues and reference adapters - 22 endpoints |
| 3. Event JSON schemas | Eight payload schemas and their contract tests (closed in the previous round; unchanged here) |
| 4. Authorization and separation matrix | Ten roles, a capability matrix validated at import time, and eight structural separation rules |
| 5. Implementation evidence | This report plus the test, security, privacy and traceability documents |

Only after all five were present and wired was `REPOSITORY_VERSION` moved
to `0.15.0`, the register updated and the archive named a candidate. That
ordering was the previous round's own rule and it was kept.

---

## 3. Architecture decisions worth explaining

### 3.1 Seven databases, not one

The separation this pack exists to create is expressed as **separate
SQLite database files**, one per trust boundary:

| Database | Migration set | Holds |
| -------- | ------------- | ----- |
| Eligibility | `eligibility-service/migrations/eligibility/` | cases, decisions, the participation-unit ledger |
| Assertion issuer | `eligibility-service/migrations/assertion-issuer/` | assertions, the release queue, one-time pickups, handoff acceptances |
| Voting credentials | `credential-service/migrations/` | credentials, the spent-nonce set, redemptions, replays, revocations |
| Voting context registry | `governance-service/migrations/` | administrative configuration only |
| Identity-side audit | `audit-core/migrations/identity-side/` | AS-01, AS-02 |
| Voting-side audit | `audit-core/migrations/voting-side/` | AS-03, AS-04 |
| Neutral audit | `audit-core/migrations/neutral/` | AS-05, AS-06, the export log |

A foreign key from a credential to an assertion is therefore not
*expressible*, which is a stronger guarantee than not written. A test
asserts the practical form of this: selecting the voting-side audit table
through the identity-side connection is not a permission failure - the
table does not exist there.

`build_voting_trust_runtime` takes both identity-side database paths as
**required arguments with no defaults**, and
`assert_storage_boundaries_are_separate` refuses a deployment that points
them at one file. A default would have to be either one shared database,
which collapses the boundary, or a pair of names the operator never
chose.

### 3.2 No new workspace member

PACK-15 extends four existing workspace members in place -
`eligibility-service`, `credential-service`, `governance-service`,
`audit-core` - rather than adding one. This is deliberate: a new member
would require regenerating `uv.lock`, and CI runs `uv sync --frozen`
followed by `git diff --exit-code -- uv.lock package-lock.json`. In an
environment where the package registries return HTTP 403, a regenerated
lock file could not have been produced honestly at all.

Neither lock file was modified in this round.

### 3.3 The generic halves live in `epd2-core`

Two pieces of machinery were needed by four services at once, and
`tests/repository/test_service_boundaries.py` forbids one service
importing another:

* `epd2_core.sqlite_migrations` - the migration runner: definition
  records, checksums, bookkeeping, statement splitting, apply and verify.
* `epd2_core.api_contracts` - the endpoint spec and its obligations, the
  request and response values, the response-safety scan and the
  dispatcher.

What stays per service in both cases is the **list**: the migration list
and the endpoint list are each that service's own contract, and pulling
them into a shared package would have made four services share one.

### 3.4 The split exactly-once rule

Exactly-once is enforced on **both sides, differently**, because a single
enforcement point would have to see both sides and that is the thing
being prevented:

* identity side: one assertion per participation unit per context, by the
  `participation_unit_ledger` composite primary key;
* voting side: one credential per assertion nonce, by the `spent_nonce`
  primary key.

Both are decided by the INSERT itself, so a concurrent second attempt
loses on a constraint rather than on a check-then-act read that raced.
The persistence tests exercise this under real thread contention - eight
threads, eight connections, one winner.

### 3.5 The API has no HTTP

`ApiRequest` and `ApiResponse` are plain values and `dispatch` is a
function. There is no framework, for two reasons: adding one would change
`uv.lock`, and the security-relevant work is not in the socket. A
deployment binds ASGI, WSGI or a queue consumer around `dispatch` without
any of the six checks moving.

The honest cost is stated in the test evidence: "the endpoint works"
here means "the handler, the store and the schema agree", not "a request
over a socket succeeded".

---

## 4. Inventory

| Category | Count | Note |
| -------- | ----: | ---- |
| Reason codes in `contracts/reason-codes/pack-15.yml` | 89 | includes 5 API-boundary codes, 2 registry-version codes, and `PERMISSION_DENIED` restated |
| Event payload schemas | 8 | `contracts/events/pack15-*.v1.schema.json` |
| Migration files | 10 | across 7 migration sets |
| Python modules added or extended by PACK-15 | 26 | four services plus two `epd2-core` modules |
| API endpoints | 22 | 9 identity-side, 4 voting-side, 5 governance, 4 audit |
| Roles in the separation matrix | 10 | |
| PACK-15 test modules | 15 | |
| PACK-15 tests | 434 | all passing |
| Full repository suite | 5335 passing, 5 skipped | see the test evidence for the skips |
| Required paths registered | 983 | `scripts/check_repository.py` |

---

## 5. Defects found and fixed during this round

Four, all found by adversarial review after the code was written, and all
recorded because a report listing only what worked first time is not
evidence.

1. **A failed mint left a participation-unit claim behind.** The claim is
   taken before minting so that exactly-once survives a retry; a mint
   that then failed left an uncommitted INSERT which the next successful
   write committed. The participant would then be refused forever with
   `CREDENTIAL_ALREADY_ISSUED` for an assertion they never received.
   Fixed with a rollback guard; two tests pin it.
2. **The voting side's identity-field scan was shallow.** It checked only
   top-level request keys while the outbound scan walked every depth -
   and the inbound bodies are nested, so the realistic attack shape was
   the one that passed. Now both directions walk every depth.
3. **A client-controlled minting delay crashed the boundary.** An
   out-of-range value raised a bare `ValueError`, which has no reason
   code, so the dispatcher re-raised it. Now bounded where it arrives and
   refused with `API_REQUEST_MALFORMED`.
4. **The assurance flag was carried across the boundary and never
   read.** `required_assurance_satisfied` was persisted and ignored - a
   fail-open in a control the specification marks fail-closed. Found
   while building the traceability matrix, which is the argument for
   building one. Now refused with
   `ELIGIBILITY_ASSURANCE_INSUFFICIENT`.

Two smaller contract corrections were made in the same pass:
`credential.revoke` declared `DUAL_CONTROL_REQUIRED` while no path could
return it (the boundary now requires a second signature, rather than the
declaration being deleted), and two governance failures shared
`VOTING_CONTEXT_CONFIGURATION_INVALID` where they differ in what the
caller must do next (now `VOTING_CONTEXT_VERSION_CONFLICT`, retryable,
and `VOTING_CONTEXT_VERSION_FROZEN`, not).

---

## 6. Verification

Corrected from the two preceding rounds, which recorded that no Python
tooling could run: **`pytest`, `mypy` and `ruff` are available in this
environment and were really executed.** The npm side remains entirely
blocked.

| Check | Result |
| ----- | ------ |
| `pytest` (full repository) | **PASS** — 5335 passed, 5 skipped |
| `mypy` (every Python group of the `typecheck` target) | **PASS** — no issues |
| `ruff check` | **PASS** |
| `ruff format --check` | **PASS** |
| `scripts/check_repository.py` | **PASS** — 983 paths |
| `scripts/check_forbidden_files.py` | **PASS** |
| `scripts/verify_versions.py` | **PASS** |
| `scripts/check_canon_0_8_0.py` | **PASS** — 18 checks |
| `uv sync --frozen` | **NOT EXECUTED — ENVIRONMENT BLOCKED** |
| npm typecheck, tests, lint, `next build`, Playwright, axe, Prettier | **NOT EXECUTED — ENVIRONMENT BLOCKED** |
| Property-based tests | **NOT EXECUTED — ENVIRONMENT BLOCKED** (`hypothesis` unavailable) |
| Visual regression | **NOT APPLICABLE** |

The Python tools ran from outside the project environment, so the
versions they resolve to are not the versions `uv.lock` pins. **External
CI remains the authoritative run.** No CI check was weakened, no lock
file was modified, and no test result was fabricated.

Full detail: `PACK-15-TEST-EVIDENCE.md`.

---

## 7. What is not done

1. **The entire frontend is unverified.** Five source files and three
   test files exist, are registered in `check_repository.py`, and have
   never been executed, type-checked or rendered here.
2. **No production key custody.** `FutureKeyServiceCustody` refuses every
   call; everything signed in tests is signed with a reference HMAC key.
3. **The credential-to-ballot half of unlinkability is PACK-16's.** This
   pack closes the identity-to-credential half. Both are needed for
   `FIR-INV-002`, and neither alone should be described as closing it.
4. **Six criteria rest on absence rather than on a control** - no import
   path exists today, and nothing fails when someone adds one. They are
   marked in the traceability matrix rather than counted as satisfied.
5. **SQLite is the reference persistence.** The constraints carrying the
   guarantees port directly; the concurrency behaviour under production
   load does not, and re-verifying it against the production engine is
   required work that has not happened.

---

## 8. Handover

The next round is external CI verification against this candidate. It is
not PACK-16, and it is not a final pass. What CI has to establish is
exactly the right-hand column of section 6: the locked dependency
versions, the whole TypeScript and frontend surface, and the property-based
tests.

**Do not proceed to PACK-16.**
