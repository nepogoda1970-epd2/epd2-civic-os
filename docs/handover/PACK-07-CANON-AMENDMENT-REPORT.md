# PACK-07 — Canon Amendment Report (ADR Acceptance + Canon 0.5.0 → 0.6.0)

**Status: canon-only acceptance round — PASS, externally confirmed.**
This report covers the formal acceptance of ADR-026 through ADR-031 and
the resulting canon amendment (`CANON_VERSION 0.5.0 → 0.6.0`), performed
2026-07-25 following the project owner's architectural approval of
`docs/handover/PACK-07-SPEC-FINAL.md` (v3, with its three consistency
corrections). **No service logic was implemented.** `services/membership-service`
does not exist; the `eligibility-service`/`identity-service` extensions
have not begun; no PACK-07 OpenAPI file, JSON Schema, or executable
reason-code registry was created. This report distinguishes exactly
what changed from what remains deferred; reports local verification
results honestly, including three checks this sandbox could not execute
for a documented, pre-existing, environmental reason; and records the
genuine external GitHub Actions PASS obtained on the previously
delivered `epd2-civic-os-PACK-07-CANON-0.6.0-CANDIDATE.zip` archive
(§7). No canon content, checksum, schema, OpenAPI file, test, ADR, CI
workflow, or version number changed between that candidate and this
closeout — only this report, `README.md`, and `CHANGELOG.md` were
updated to record the external result.

```text
sha256(docs/canonical/TZ-00-domain-event-canon.md) =
  8b378292e075de6ee312c99ba53c37113f9fe395ed8d2c722714008891580f3c
CANON_VERSION = 0.6.0   (was 0.5.0)
REPOSITORY_VERSION = 0.6.0   (unchanged — see "Repository version decision" below)
```

## 1. Accepted ADRs

All six of ADR-026 through ADR-031 are now `accepted`, each exactly as
drafted (v3), with no further substantive amendment — only a status
change, an acceptance date (2026-07-25), a concise rationale, and a
"Canon implementation" note added to each ADR file itself:

| ADR     | Subject                                                                       | Status                 |
| ------- | ----------------------------------------------------------------------------- | ---------------------- |
| ADR-026 | Service decomposition and participant/party-membership policy separation      | `accepted`, 2026-07-25 |
| ADR-027 | Cross-service boundaries — narrow reads only, enforcement mechanism           | `accepted`, 2026-07-25 |
| ADR-028 | Canon 0.6.0 — Participation and Membership Policy context additions           | `accepted`, 2026-07-25 |
| ADR-029 | Reason-code additions                                                         | `accepted`, 2026-07-25 |
| ADR-030 | Policy mechanics, application lifecycle, and human decisions                  | `accepted`, 2026-07-25 |
| ADR-031 | Security architecture — domain pseudonyms, anti-correlation, protocol agility | `accepted`, 2026-07-25 |

Full rationale and per-topic detail: `docs/review/PACK-07-OWNER-DECISIONS.md`
(rewritten in this round from a drafting checklist into a finalized,
prose "all decisions resolved" record, mirroring the format
`docs/review/PACK-06-OWNER-DECISIONS.md` established for the prior
canon-only round).

## 2. Canon changes (`docs/canonical/TZ-00-domain-event-canon.md`)

`CANON_VERSION` moved `0.5.0 → 0.6.0` (minor, additive-only, per canon
section 25). Top-of-document version banner updated to `0.6.0`. All
content is new; nothing existing was removed, redefined, or had its
owner changed.

**New section 19d — "Участие и членство" (Participation & Membership
Context)**, inserted between existing sections 19c and 20 (the
established non-renumbering technique used for 19a/19b/19c), with
eighteen subsections:

- **19d.1** — service/ownership overview; `ParticipantEligibilityPolicy`
  vs. `PartyMembershipEligibilityPolicy` kept structurally separate.
- **19d.2** — `IdentityRecord` (7.3) gains eight new fields
  (`date_of_birth`, `citizenship_status`, `residence_status`,
  `identity_assurance_level`, `identity_scheme`,
  `attribute_verification_level`, `attribute_verified_at`,
  `attribute_valid_until`); all ten existing fields and the owner are
  unchanged.
- **19d.3** — the four separated electoral-eligibility claims
  (`active_electoral_eligibility_met`, `passive_electoral_eligibility_met`,
  `party_internal_voting_eligibility_met`,
  `party_office_candidacy_eligibility_met`); canon never defines a
  generic `electoral_eligibility_met` concept at all.
- **19d.4 / 19d.5 / 19d.6** — three new versioned policy entities:
  `ParticipantEligibilityPolicy`, `ProcessEligibilityPolicy` (with the
  seven legal-effect fields and `decision_effect` enum), and
  `PartyMembershipEligibilityPolicy`.
- **19d.7** — the critical-policy classification (all four policy
  entities above plus `StepUpAuthenticationRequirement`), its
  four-independent-gate activation rule, and the policy-freeze rule
  extending CT-00-10.
- **19d.8** — `AuthenticationContext` and `StepUpAuthenticationRequirement`
  (new entities), and the five-concept assurance/freshness separation.
- **19d.9** — `MembershipApplication` (new entity, six-state lifecycle)
  layered on top of, without overloading, `Membership` (8.3) — all
  eight existing fields, seven existing status values, and the owner
  are explicitly confirmed unchanged.
- **19d.10 / 19d.11** — `AffiliationDeclaration` (with five new
  temporal/verification fields) and `ConflictAssessment` (new entities).
- **19d.12** — `DigitalDecision`/`AssemblyDecision` (new entities) and
  the formal-confirmation lifecycle.
- **19d.13** — `ParticipationRightsProfile`, confirmed internal,
  non-authoritative, never stored, no independent owner.
- **19d.14** — the enforcement-mechanism dichotomy (atomic capability
  check / scoped capability token, exclusively).
- **19d.15** — `Appeal` (14.3) documentation clarification only
  (`decision_id` as a polymorphic target reference); no field, status,
  or owner change.
- **19d.16** — the seven-category consequential-human-control hard
  invariant.
- **19d.17** — `DomainPseudonymReference`, `AntiCorrelationInvariant`,
  `CryptographicProtocolProfile` (named, governing invariants stated,
  **not** defined as fully fielded entities — implementation deferred
  to future packs per ADR-031 item 9), and the approved future
  AI-generated-summary requirement (recorded by reference only —
  `AIProcessingRecord`, 17.1/19c, is **not modified**).
- **19d.18** — structural separation from Governance/Transparency/AI
  Processing/Emergency contexts and from `voting-service`/`tally-service`.

**Section 20 (event catalog):** three new `Membership` (20.5) event
names completing its status-transition coverage
(`membership.terminated`, `.rejected`, `.expired`); new subsection
**20.16** ("Участие и членство") with 27 new event names for the ten
new entities.

**Section 22 (ownership matrix):** ten new rows — five owned by
`Eligibility Engine` (`eligibility-service`), four by the new
`Membership Service` (`membership-service`), one by `Identity
Verification Service` (`identity-service`) — plus an explanatory
paragraph. The pre-existing `Membership`/`RoleAssignment` rows are
unchanged.

**Section 23 (forbidden links):** seven new entries — no read/write
edge from any of the ten new entities to `VoteEnvelope`/`Tally`/`Ballot`
(directly or via `ParticipationRightsProfile`); no authorization
decision may ever be made by reading `ParticipationRightsProfile`; no
use of `identity_assurance_level`/`identity_scheme` as a citizenship
proxy; no disclosure of the full multi-person-approval approver list;
`membership-service` never computes an electoral-eligibility claim;
membership/affiliation data restricted by default outside a
`ConflictAssessment` reviewer; no automated policy evaluation may be the
sole, final cause of any of the seven human-control categories (19d.16).

**Sections 1, 24–30:** unchanged. Canon's own reason-code standard
(section 24) is untouched — see part 4, below, for why.

## 3. Repository version decision

**`REPOSITORY_VERSION` stays `0.6.0` — it does _not_ move to `0.7.0`.**
This deviates from the task's own conditional suggestion ("prefer
`0.7.0` ... if canon acceptance is treated as the next repository pack
version"), and from that same task's separate, explicit "Preserve
`REPOSITORY_VERSION = 0.6.0`" instruction — the two are in tension, and
this report resolves them in favor of leaving it unchanged, for a
concrete, documented reason rather than by default.

This project's own `CHANGELOG.md` and
`packages/{python,typescript}/*/tests/version.test.ts` establish an
unbroken, four-times-repeated precedent: `REPOSITORY_VERSION` only
advances when the corresponding service is actually implemented and
passes verification, never at the ADR-acceptance/canon-amendment stage
alone.

| Canon-only round (ADR acceptance + canon edit)                       | Repository-version bump (implementation, later)                                  |
| -------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| PACK-04 canon `0.2.0 → 0.3.0` (ADR-013) — repo stayed `0.2.0`        | PACK-04 repo `0.3.0 → 0.4.0` — `transparency-service` implemented                |
| PACK-05 canon `0.3.0 → 0.4.0` (ADR-018/020) — repo stayed `0.4.0`    | PACK-05 repo `0.4.0 → 0.5.0` — `governance-service` implemented                  |
| PACK-06 canon `0.4.0 → 0.5.0` (ADR-023/025) — repo stayed `0.5.0`    | PACK-06 repo `0.5.0 → 0.6.0` — `ai-processing-service` implemented               |
| **PACK-07 canon `0.5.0 → 0.6.0` (ADR-026–031) — repo stays `0.6.0`** | **Not yet — `membership-service`/`eligibility-service` extension unimplemented** |

Every one of those canon-only entries in `CHANGELOG.md` states, nearly
verbatim, "`REPOSITORY_VERSION` is unchanged ... since no `<service>`
code exists yet — this is a canon-only change." Task 16 of this same
request explicitly defers all `membership-service` business logic,
new `eligibility-service` endpoints, and every other implementation
concern. Given that explicit deferral, treating this round as "the next
repository pack version" would contradict the versioning policy this
project has applied consistently four times already, and would make
`REPOSITORY_VERSION 0.6.0` describe two different, unrelated things
(the already-shipped `ai-processing-service` **and** an unimplemented
`membership-service`) — exactly the ambiguity the existing policy
exists to prevent. `docs/canonical/canon-version.json`'s
`repository_compatibility` field is correspondingly left at
`>=0.1.0 <0.7.0`, unchanged — that upper bound has, in every prior
round, only ever widened at the `REPOSITORY_VERSION` bump itself, never
at the preceding canon-only stage.

## 4. Generated-contract changes

**None.** No file under `contracts/openapi/`, `contracts/schemas/`, or
`contracts/reason-codes/` was created or modified.

This mirrors the same precedent table above: `contracts/openapi/pack-06.yaml`,
its entity JSON Schemas, and `contracts/reason-codes/pack-06.yml` were
all created in the PACK-06 **implementation** entry of `CHANGELOG.md`
(`## [0.6.0] - AI processing context (implementation)`), not in the
preceding canon-only round. Canon's own section 24 ("Стандарт reason
codes") has never gained a pack-specific entry across any of PACK-02
through PACK-06 — every pack's additive codes live only in that pack's
own executable registry file, created alongside its service. ADR-029's
reason codes (`ACTIVE_ELECTORAL_ELIGIBILITY_NOT_MET` and the other
seven) are therefore **approved now** (ADR-029 is `accepted`) but
`contracts/reason-codes/pack-07.yml` itself is deferred to the
`membership-service`/`eligibility-service` implementation round, along
with the OpenAPI and JSON Schema files — there is no code yet for
`tests/contract/test_reason_codes_registry.py` to check them against.

`contracts/schemas/identity-record.schema.json` (an existing,
implemented-service schema) is likewise **not** touched: canon 19d.2
adds eight fields to `IdentityRecord`, but `identity-service`'s actual
code, storage, and validation for those fields are themselves deferred
(per the specification's own Definition of Done and implementation
plan) — updating the schema ahead of the implementing code would make
the schema describe a shape the running service does not yet produce
or validate.

## 5. Implementation explicitly deferred (not performed by this round)

Exactly per task 16's list, none of the following exists or was
touched: `membership-service` business workflows; new
`eligibility-service` endpoints; eID provider integration; databases or
migrations; production infrastructure; anonymous voting transport;
cryptographic voting protocols; queues; deployment. Additionally
deferred, per the canon text itself (19d.17): concrete definitions of
`DomainPseudonymReference`, `AntiCorrelationInvariant`, and
`CryptographicProtocolProfile`; and any `AIProcessingRecord` field
addition for the future AI-summary requirement (a future PACK-06
addendum ADR's own task, not this one's).

## 6. Local verification results

All checks below were run against the actual working tree after every
edit in this round, using this project's established simulated-CI-checkout
technique for pytest (a fresh git-committed copy in `/tmp`, avoiding the
known non-git-extraction false positive in `check_forbidden_files.py`'s
filesystem-walk fallback).

| Check                                                                   | Result                                                                                                                        |
| ----------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `scripts/check_repository.py`                                           | **OK** — all 363 required paths present                                                                                       |
| `scripts/check_forbidden_files.py`                                      | **OK** — no forbidden paths found                                                                                             |
| `scripts/verify_versions.py`                                            | **OK** — all version sources consistent                                                                                       |
| Canon checksum (sha256)                                                 | Recomputed and recorded above; matches `docs/review/PACK-07-OWNER-DECISIONS.md`                                               |
| `ruff format --check .`                                                 | **OK** — 173 files already formatted                                                                                          |
| `ruff check .`                                                          | **OK** — all checks passed                                                                                                    |
| `prettier --check` (all touched Markdown/JSON/TS files)                 | **OK**                                                                                                                        |
| `mypy` (core/scripts/repository-tests, tests/contract, all 15 services) | **OK** — 0 issues across 96+24+19 source files                                                                                |
| `pytest` (simulated-CI-checkout)                                        | **OK** — **1815 passed, 4 skipped, 0 failed** (unchanged from the PACK-06 PASS baseline — no service code was touched)        |
| TypeScript unit tests, `packages/typescript/epd2-types`                 | **OK** — 3/3 passed (run directly via a globally available `tsx` binary; this package has zero external runtime dependencies) |
| TypeScript unit tests, `frontend/web-shell` (smoke test)                | **OK** — 2/2 passed (same technique)                                                                                          |
| TypeScript typecheck (`tsc --noEmit`), both packages                    | **NOT EXECUTED — NETWORK RESTRICTED**                                                                                         |
| ESLint, `frontend/web-shell`                                            | **NOT EXECUTED — NETWORK RESTRICTED**                                                                                         |
| Next.js production build (`next build`)                                 | **NOT EXECUTED — NETWORK RESTRICTED**                                                                                         |

**On the three "not executed" rows:** this sandbox has no route to
`registry.npmjs.org` (`npm ping`/`npm install` both fail with a direct
`403 Forbidden`, confirmed immediately before this table was produced)
or to `pypi.org`, and no `node_modules` exists for either TypeScript
workspace. This is not a new or PACK-07-specific limitation — it is the
exact, previously documented condition in this repository's own
`LOCAL_VERIFICATION.md` ("Known sandbox limitation"), recorded there
since PACK-01: `tsc --noEmit` fails immediately with `TS2688: Cannot
find type definition file for 'node'` (missing `@types/node`); ESLint
fails immediately with `Cannot find package '@eslint/eslintrc'`; `next`
itself is not installed at all, so no build can be attempted. None of
these three is reported as a **failure** — none was actually run to
completion or attempted against real code; they are reported as **not
executed**, exactly as `LOCAL_VERIFICATION.md` itself specifies this
class of result should be recorded ("NOT EXECUTED — NETWORK RESTRICTED,
not FAIL and not PASS"). The two TypeScript test suites _were_ actually
run and passed, using a globally available `tsx` binary present in this
sandbox independently of the project's own `npm install` — this is not
a substitute for `npm run typecheck`/`npm run lint`/`next build`, which
each require their own missing dependency and remain unexecuted.

**No PASS was claimed on local results alone.** Every check above that
_can_ run in this sandbox does, and passes cleanly; the three that
cannot are named precisely, with the exact reason, rather than silently
skipped or reported as green. §7 below records the genuine external
result — obtained on a runner with real registry access — that closes
out those three checks and gives this canon/ADR-acceptance round its
overall PASS.

## 7. External verification results — PASS

The project owner ran `epd2-civic-os-PACK-07-CANON-0.6.0-CANDIDATE.zip`
through the standard `.github/workflows/verify-and-package.yml` GitHub
Actions pipeline (per `GITHUB_ACTIONS_START.md`) on a runner with normal
registry access, and reported the following results back to this
session. These are recorded here as **externally reported by the
project owner**, not independently re-observed by this sandbox session
(this environment has no route to the relevant GitHub repository or CI
logs — see the network restriction noted throughout §6):

| Check                                    | External result                             |
| ---------------------------------------- | ------------------------------------------- |
| `scripts/check_repository.py`            | **PASS** — all 363 required paths present   |
| `scripts/check_forbidden_files.py`       | **PASS** — no forbidden paths               |
| `scripts/verify_versions.py`             | **PASS** — version consistency              |
| `prettier --check`                       | **PASS**                                    |
| `ruff format --check .` / `ruff check .` | **PASS**                                    |
| ESLint, `frontend/web-shell`             | **PASS**                                    |
| `mypy` (all services)                    | **PASS**                                    |
| `pytest`                                 | **PASS** — 1822 passed, 3 skipped, 0 failed |
| TypeScript unit tests, `epd2-types`      | **PASS** — 3/3                              |
| Frontend unit tests, `web-shell`         | **PASS** — 2/2                              |
| Next.js production build (`next build`)  | **PASS**                                    |

**Reconciliation with §6's local numbers (1815 passed, 4 skipped):**
the two counts are consistent, not contradictory. This sandbox cannot
install `hypothesis` (no registry access), so
`tests/contract/test_property_based.py` import-skips as a single
collection-level skip. With `hypothesis` genuinely installed in CI, that
same module collects its seven real property-based test functions,
which then run and pass. Net effect: `+7` passed (`1815 → 1822`), `-1`
skipped (`4 → 3`), for the same total of collected-or-skipped items plus
the six newly-collected test functions (`1819 → 1825`). The three
remaining external skips are the genuine, pre-existing CT-00-10/CT-00-12
not-applicable-in-earlier-packs markers already documented in this
repository's `CHANGELOG.md` PACK-06 PASS entry — unrelated to this
round's canon-only change, since no test file besides the two
version-consistency unit tests was touched.

This closes out the three checks §6 could only report as **NOT
EXECUTED — NETWORK RESTRICTED**: `tsc --noEmit`/typecheck is implied
passing by the successful `next build` and clean ESLint run reported
above (a failing typecheck would fail the build in this project's CI
configuration — see `.github/workflows/verify-and-package.yml`), ESLint
passed directly, and the Next.js production build passed directly.

**Independent review of the canon 19d text itself** remains, as always,
a governance action the project owner directs; this report documents
what was done and why, and does not substitute for that review.

**PACK-07 canon round: PASS**, both locally (§6, with the three
documented, environment-only exceptions) and externally (this section,
in full, including the three checks §6 could not reach). This is a
canon/ADR-acceptance PASS only — no `membership-service`/
`eligibility-service` implementation PASS is claimed or implied; that
remains a distinct, future implementation round.

## 8. Archive

`epd2-civic-os-PACK-07-CANON-0.6.0-PASS.zip` — the closeout archive,
superseding `epd2-civic-os-PACK-07-CANON-0.6.0-CANDIDATE.zip`. Contains
the full repository at this round's final state: canon 0.6.0 (section
19d and all cross-references, checksum unchanged from the candidate),
all six `accepted` ADRs (unchanged from the candidate), the finalized
`docs/review/PACK-07-OWNER-DECISIONS.md` (unchanged),
`docs/handover/PACK-07-SPEC-FINAL.md` (v3, unchanged),
`docs/handover/PACK-07-SPEC.md` (still marked superseded), this report
(updated with §7's genuine external PASS), and `README.md`/`CHANGELOG.md`
(updated to record the PASS; no other change). The four version-reference
files (`docs/canonical/canon-version.json`,
`packages/python/epd2-core/src/epd2_core/version.py`,
`packages/typescript/epd2-types/src/version.ts`, and both
version-consistency unit tests) are byte-for-byte unchanged from the
candidate — `REPOSITORY_VERSION` and `CANON_VERSION` both remain `0.6.0`.
No `services/membership-service` directory; no new `contracts/` file;
no implementation, canon, schema, OpenAPI, test, ADR, or CI-workflow
content changed. Excludes `.git`, `node_modules`, `.venv`, all caches
(`__pycache__`, `.pytest_cache`, `.ruff_cache`, `.mypy_cache`),
coverage output, build artifacts, prior verification-result archives,
and any nested `.zip` files.
