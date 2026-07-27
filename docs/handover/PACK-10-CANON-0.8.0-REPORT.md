# CLAUDE-PACK-10 — Canon 0.8.0 (Party Finance & Financial Accountability Context): Canon-Amendment Round Report

Status: **PACK-10 CANON 0.8.0 CANDIDATE.** The canon amendment is applied
in this archive and submitted for review. It is **not** a PASS release,
and ADR-054 — the ADR that governs it — is `proposed`, not `accepted`.
This round is canon-only: no runtime implementation was added, and
`REPOSITORY_VERSION` is unchanged.

## 1. Baseline

| Item                        | Value                                                                                                                            |
| --------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| Baseline archive            | `EPD2_PACK-10_SPECIFICATION_0.10.0_CANDIDATE.zip`                                                                                |
| Baseline state              | PACK-01 – PACK-09 FINAL PASS; PACK-10 specification architecturally accepted by the owner, ADR-048 – ADR-053 formally `proposed` |
| `CANON_VERSION` before      | `0.7.0`                                                                                                                          |
| `CANON_VERSION` after       | `0.8.0`                                                                                                                          |
| `REPOSITORY_VERSION` before | `0.9.0`                                                                                                                          |
| `REPOSITORY_VERSION` after  | `0.9.0` — **unchanged**                                                                                                          |
| Latest ADR before           | ADR-053                                                                                                                          |
| ADR added                   | ADR-054 (`proposed`)                                                                                                             |

Normative inputs used: `docs/packs/PACK-10-SPECIFICATION.md`,
`docs/packs/PACK-10-CANON-AMENDMENT-ASSESSMENT.md`,
`docs/packs/PACK-10-CANON-AMENDMENT-PROPOSAL.md`, ADR-048 – ADR-053, the
existing canonical document, the existing reason-code registries, the
existing domain-event canon, and the existing ownership and
forbidden-link conventions.

## 2. Files added — six

| Path                                                              | Lines | Purpose                                                                          |
| ----------------------------------------------------------------- | ----- | -------------------------------------------------------------------------------- |
| `scripts/check_canon_0_8_0.py`                                    | 1014  | Sixteen standalone canon-level checks                                            |
| `docs/packs/PACK-10-CANON-0.8.0-COMPATIBILITY.md`                 | 478   | Compatibility statement, reason-code registry diff, event and report-state diffs |
| `docs/adr/ADR-054-canon-0.8.0-party-finance-context-additions.md` | 379   | The canon-amendment ADR (`proposed`)                                             |
| `docs/packs/PACK-10-CANON-0.8.0-ACCEPTANCE-MATRIX.md`             | 334   | Acceptance evidence and the `ФИН` ↔ `HI` coverage map                            |
| `tests/repository/test_canon_0_8_0_amendment.py`                  | 121   | Pytest wrapper over the sixteen checks                                           |
| `docs/handover/PACK-10-CANON-0.8.0-REPORT.md`                     | 443   | This report                                                                      |

## 3. Files changed — twelve

| Path                                                   | Change                                                                                                                                                                            |
| ------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `docs/canonical/TZ-00-domain-event-canon.md`           | Header version `0.7.0 → 0.8.0`; new section 19f; new subsection 20.17; twenty-one section-22 rows; twenty-five section-23 entries; forty-five section-24 codes. 4514 → 5957 lines |
| `docs/canonical/canon-version.json`                    | `canon_version` `0.7.0 → 0.8.0`; three explicit compatibility keys added                                                                                                          |
| `packages/python/epd2-core/src/epd2_core/version.py`   | `CANON_VERSION = "0.8.0"`; `REPOSITORY_VERSION` untouched                                                                                                                         |
| `packages/typescript/epd2-types/src/version.ts`        | `CANON_VERSION = "0.8.0"`; `REPOSITORY_VERSION` untouched                                                                                                                         |
| `packages/python/epd2-core/tests/test_version.py`      | Expected canon version updated with the round's narrative comment                                                                                                                 |
| `packages/typescript/epd2-types/tests/version.test.ts` | Same, on the TypeScript side                                                                                                                                                      |
| `docs/canonical/README.md`                             | Current canon version, latest-amendment narrative, candidate status                                                                                                               |
| `docs/adr/README.md`                                   | Canon-version line, ADR-054 index row, round narrative                                                                                                                            |
| `docs/architecture/data-ownership.md`                  | Twenty-one finance ownership rows, all marked not implemented                                                                                                                     |
| `docs/architecture/service-boundaries.md`              | New finance trust-boundary section                                                                                                                                                |
| `README.md`                                            | Canon `0.8.0`; the canon-round status entry                                                                                                                                       |
| `CHANGELOG.md`                                         | New `## [Unreleased] - canon minor version 0.8.0` entry                                                                                                                           |

No file was deleted or moved. Nothing under `services/`, `contracts/`,
`frontend/`, or any existing test other than the two version tests was
touched.

## 4. Canonical finance bounded-context ownership

Twenty-one authoritative entities, owner `Finance Service`, registered in
canon section 22 and mirrored in `docs/architecture/data-ownership.md`:
`FinanceAccount`, `AccountingPeriod`, `JournalEntry`,
`FinancialTransaction`, `ImportBatch`, `ReconciliationRecord`,
`FinanceContribution`, `SponsorshipAgreement`,
`ExternalFinancialBenefit`, `ExpenseClaim`, `PaymentAuthorization`,
`Budget`, `FinancialAsset`, `FinancialObligation`,
`ReportingObligation`, `ReportingPerimeterDefinition`, `FinanceReport`,
`ReportSnapshot`, `AuditEngagement`, `FinancePolicy`,
`FinancePartyHandle`.

Finance owns **none** of: identity, membership, organizational authority
assignments, legal cases, legal deadlines, notices, Legal Hold, general
retention governance, document bytes, evidence content, lobbying
meetings, voting, ballots, eligibility credentials, tally, or production
payment execution. Every one of those stays with its existing owner, and
canon 19f.22 states it explicitly.

Value objects (`Money`, `PostingLine`, `InKindValuation`,
`AggregationSnapshot`, `PerimeterSnapshot`, `FinancePolicyBinding`,
`ContributionPartyRef`, `RetentionBinding`, `FinanceEvidenceReference`)
and derived read models receive no ownership row — the same treatment
canon already gives `RedactionManifest` (19c.4) and `OrganizationalScope`
(19e.11).

## 5. Hard invariants added

Forty-five, as the canonical register `ФИН-01` – `ФИН-45` in canon
19f.13. `ФИН-01` – `ФИН-43` are the forty-three the governing request
required, in its order. Two further rules were added because the
specification supports them directly and the repository already enforces
their equivalents everywhere else:

- `ФИН-44` — no direct access to another service's storage; every
  cross-service fact arrives through a published interface (restates
  INV-03 for the finance context).
- `ФИН-45` — a role name alone is never proof of finance authority;
  authority resolves to an active, scope-matching
  `OrganizationalAuthority`/`RoleAssignment` record (restates 19e.12).

The `ФИН` ↔ specification `HI-1` – `HI-55` mapping, including the
specification invariants that stay repository-level conventions rather
than canon rules, is in
`docs/packs/PACK-10-CANON-0.8.0-ACCEPTANCE-MATRIX.md` section 3.

## 6. Roles added or clarified

Four new institutional `role_code` values extend canon 19e.15's
explicitly open list: `finance_administrator`, `payment_authorizer`,
`payment_executor`, `report_signatory`. The existing `finance_auditor`
is clarified, not redefined.

Four **action-level** authorities are codified as authorities recorded on
the action rather than institutional roles: transaction creator,
transaction reviewer, report preparer, report approver. This is
deliberate: nine institutional roles would expand the platform's standing
privilege surface where four suffice.

All of them remain scoped to a single `OrganizationalScope`,
effective-dated, revocable only with a reason reference, with assignment
history preserved. **No generic superuser is introduced**, and technical
or system administration never implies financial authority.

This round also closes a pre-existing canon defect: 19e.16 rule 3 already
forbade combining `finance auditor` with `finance administrator` although
`finance_administrator` was not among 19e.15's enumerated values. Canon
19f.14 enumerates it.

## 7. Incompatibilities added

Extending 19e.16's minimum baseline, in the same scope and at the same
time:

- `finance_auditor` × `finance_administrator` (preserved from 19e.16
  rule 3, now with both roles enumerated);
- `finance_auditor` × `payment_authorizer`, × `payment_executor`, ×
  `report_signatory`, × report preparer, × report approver;
- `payment_authorizer` × `payment_executor` for the same payment;
- transaction creator × approver of the same object;
- claimant × reviewer / approver / authorizer / executor of their own
  claim;
- **`finance_administrator` × `organizational_administrator` in the same
  legally relevant scope** — the recommended invariant, **adopted**.

On the last one: repository analysis found no conflict with accepted
organization governance. Canon 19e.16 already makes `finance_auditor`
incompatible with `organizational_administrator` for the same
independence reason, and 19e.15's `organizational_administrator` is a
scoped administrative role over one node's own records, never a
platform-wide administrator (HI-11). Adopting the incompatibility
therefore extends an existing pattern rather than contradicting one. The
operational consequence — a small local chapter where one person would
naturally hold both — is a **policy** question, not an architectural one:
any exception must be a governed, documented decision, never a silent
combination. That operational question is recorded as an open decision
(section 12, OD-23) rather than resolved here.

## 8. Events added

Seventy-two, in the new canon subsection 20.17, each with owner
(`finance-service` without exception), aggregate, event version (all
start at `1` under section 21's unchanged envelope), required safe
metadata, prohibited payload, cross-pack consumers and an explicit
public-projection rule per group.

Sixty-nine are the specification's section 14 catalogue verbatim. Three
were added because the governing request required them and the
specification lacked a distinct name:

- `import_batch.duplicate_detected` — replay/duplicate import detection
  as its own recorded fact;
- `finance_report.amended` — an amendment version, distinct from a
  restatement;
- `finance_report.superseded` — a version replaced by a later one.

Prohibited in every finance event payload: names, addresses,
bank-account data, identity documents, free-form evidence content,
document bytes, voting information, credentials, secrets, and any
unnecessary personal data — and, for `finance_party_handle.resolved`, the
resolved value itself.

No existing event in sections 20.1 – 20.16 was renamed, removed or
reassigned.

## 9. Reason codes added and reused

- **Added:** forty-five `FINANCE_*` codes in canon section 24. Forty-four
  come from specification section 15.2; the forty-fifth,
  `FINANCE_EXTERNAL_ACCEPTANCE_MISSING`, is added by this amendment for
  the refusal to enter `externally_accepted` without an authoritative
  reference.
- **Reused verbatim:** thirty-two existing codes, unchanged in meaning
  and not shadowed by finance duplicates — including PACK-09's
  `RECORD_UNDER_LEGAL_HOLD`, `LEGAL_HOLD_STATE_UNKNOWN` and the
  `RETENTION_*` family, PACK-08's scope and authority codes, and PACK-02's
  generic codes.
- **Rejected collisions:** `CONTRIBUTION_*` (canon 13.2 deliberation
  contributions), `LEDGER_ENTRY_*` / `TRANSPARENCY_LEDGER_ENTRY_PUBLISHED`
  (canon 19a.1 public ledger), `ACCOUNT_*` (canon 7.2 platform accounts)
  and the audit-log integrity codes — each would have been a silent
  semantic collision, and each is avoided by the `FINANCE_` prefix.

No existing code was renamed, redefined or repurposed; canon section 24's
own closing note records the collision check, as the PACK-08 round's did.
The full diff, including the four rejected families and the exact future
shape of `contracts/reason-codes/pack-10.yml`, is
`docs/packs/PACK-10-CANON-0.8.0-COMPATIBILITY.md` section 3.

**No `contracts/reason-codes/pack-10.yml` was created.** Canon section 24
is the registry of record for a canon round; the pack registry file is an
implementation-round artefact whose codes must be reachable from real
service code, and `tests/contract/test_reason_codes_registry.py` checks
exactly that. Shipping the file with no `finance-service` behind it would
either fail that test or require weakening it, which this round is
forbidden to do.

## 10. Forbidden links added

Twenty-five new entries in canon section 23, each carrying a
`(добавлено 0.8.0, 19f.x)` marker, grouped as:

- **voting correlation** — finance record → `Ballot`, → `VoteEnvelope`,
  → voting credential; `FinancePartyHandle` → eligibility credential;
  `finance-service` → voting/tally/delegation storage;
- **identity exposure** — public finance projection → `IdentityRecord` /
  private identity data; finance event → bank-account details;
  `FinancePartyHandle` → public projection, export or inclusion in a
  published report; `FinancePartyHandle` → cross-purpose or
  cross-perimeter reuse;
- **storage and ownership boundaries** — `finance-service` → direct
  PACK-09 storage; → direct PACK-11 storage; finance event → evidence
  content or document bytes; document reference → an authenticity,
  signature or admissibility assertion; finance record → PACK-35
  meeting/lobbying entity;
- **authority overreach** — system or technical administrator → finance
  authority; `finance_administrator` → `finance_auditor` authority in the
  same scope; consolidation → lower-scope write authority; audit
  authority → writing into an audited aggregate;
- **effect and truth boundaries** — report publication → automatic legal
  acceptance; delivery/read telemetry → legal effect; derived public
  projection → authoritative mutation or authoritative status;
  `Budget`/`BudgetVersion` → ledger overwrite or stored actuals;
  immutable-record edit or deletion; reclassification bypass; policy
  backdating into a closed or submitted period.

## 11. Cross-pack boundaries

Codified in canon 19f.22: **PACK-09** owns legal cases, deadlines,
notices, legal effect, Legal Hold, retention governance and procedural
appeal infrastructure — finance consumes typed references only.
**PACK-11** owns document bytes, authoritative document versions,
signatures, cryptographic version chains, evidence content and chain of
custody — and a document reference implies neither authenticity,
signature, legal validity, admissibility nor publishability.
**PACK-12** owns privileged administration, JIT/break-glass, DLP and
protected exports. **PACK-13** owns the production data plane, event bus
and schema-registry implementation. **PACK-14** owns real identity,
authentication and external identity gateways. **PACK-35** owns lobbying
contacts, meeting disclosure, access records and non-financial external
influence; finance owns only financially measurable influence and its
disclosure.

## 12. Compatibility changes

- `canon_version` `0.7.0 → 0.8.0`, mirrored across
  `canon-version.json`, `epd2_core/version.py` and
  `epd2-types/src/version.ts`, with both version tests updated.
- `canon-version.json` gains three explicit keys:
  `minimum_repository_version: "0.9.0"`,
  `amended_at_repository_version: "0.9.0"`, and
  `finance_context_implementation_status: "not_implemented"` — the last
  one exists precisely so that consuming canon `0.8.0` can never be read
  as "PACK-10 is implemented".
- `repository_compatibility` deliberately stays `>=0.1.0 <0.10.0`. A
  repository at `0.9.0` is inside that range and can consume canon
  `0.8.0`, which is what this round requires. Widening the range to admit
  a future `0.10.0` would pre-authorize an implementation round that has
  not happened, so the question stays open (OD-20).
- The amendment is purely additive: no existing canonical entity, field,
  status, owner, event, reason code or forbidden link was changed,
  renamed, removed or repurposed. Services PACK-02 – PACK-09 read nothing
  that changed.
- Two documented divergences from the architecturally accepted
  specification, recorded
  rather than silently reconciled: the canon's twelve report states
  (`externally_accepted` in place of `accepted_by_authority`;
  `amended`/`restated`/`superseded` in place of `amended_or_restated`),
  and the three added events plus one added reason code. The canon names
  are authoritative for an implementation round;
  `PACK-10-CANON-0.8.0-COMPATIBILITY.md` sections 4 and 5 carry the
  mapping.

## 13. Unresolved legal-policy decisions

Every open decision from the specification round remains open —
`docs/packs/PACK-10-OPEN-DECISIONS.md`, OD-1 through OD-22. The canon
deliberately encodes **no** German statutory threshold, category or
period as a constant; all of them are governed, effective-dated
`FinancePolicy` inputs (canon 19f.20). Still unresolved and still
required before any implementation seeds real policy content: the
`Rechenschaftsbericht` taxonomy (OD-1), the aggregation perimeter
(OD-3), contributor categories (OD-4), thresholds (OD-5), public
disclosure granularity (OD-7), the sign-off model (OD-9), retention
periods (OD-14), currency scope (OD-17), the chart of accounts (OD-18),
and the PACK-10/PACK-35 division (OD-19). OD-20 (the
`repository_compatibility` range and the `0.10.0` question) is now a
canon-round question rather than a hypothetical one.

This round adds one open decision:

- **OD-23 — operational exception mechanism for
  `finance_administrator` × `organizational_administrator`.** The
  incompatibility is adopted in canon 19f.14. Small local chapters may
  have no second qualified person. Whether the party's statutes permit a
  governed, time-boxed, audited exception — and who may grant it — is a
  legal and organizational question, not an architectural one. Until it
  is answered, the incompatibility holds without exception.

## 14. Verification — exact commands and results

Executed in the preparation environment, on the delivered tree:

```text
$ python3 scripts/verify_versions.py
OK: all version sources are consistent.

$ python3 scripts/check_canon_0_8_0.py
OK: all 16 canon 0.8.0 amendment checks passed.

$ python3 scripts/check_repository.py
OK: all 556 required paths are present.

$ python3 scripts/check_forbidden_files.py
WARNING: repository root is not a git repository; falling back to a full
filesystem walk (local build caches may be flagged).
OK: no forbidden paths found.

$ ruff check .
All checks passed!

$ ruff format --check .
218 files already formatted

$ python3 -c "import ast; ast.parse(open('tests/repository/test_canon_0_8_0_amendment.py').read())"
(no output — parses cleanly)
```

Not executed, and therefore not claimed:

- **`pytest`** — not installed in the preparation environment. The new
  `tests/repository/test_canon_0_8_0_amendment.py` was verified to parse
  and its underlying check functions were all executed directly through
  `scripts/check_canon_0_8_0.py`, which is the same code path. The two
  updated version tests
  (`packages/python/epd2-core/tests/test_version.py`,
  `packages/typescript/epd2-types/tests/version.test.ts`) were **not**
  run; their assertions were updated to `0.8.0` and their consistency is
  independently confirmed by `scripts/verify_versions.py`.
- **`mypy`** — not installed. The new checker is fully type-annotated,
  standard-library-only, `from __future__ import annotations`, and passes
  `ruff` under the repository's own rule set.
- **`npm test` / `tsc` / `next build`** — the npm registry is not
  reachable from the preparation environment, so TypeScript and frontend
  suites could not be built or run. Nothing in this round changes
  TypeScript source except the `CANON_VERSION` constant and its test's
  expected value.
- **`prettier --check`** — same reason (registry unreachable). New and
  edited markdown follows Prettier 3 defaults and its tables were padded
  by a routine reproducing Prettier's column padding.
  `docs/canonical/TZ-00-domain-event-canon.md` is listed in
  `.prettierignore` and is not subject to Prettier at all.
- **GitHub Actions** — no CI run was performed for this round, and none
  is claimed. PACK-09's external result belongs to PACK-09.

Integrity manifest — SHA-256 (first 16 hex characters) of every file this
round added or changed:

| File                                                              | SHA-256 (short)    |
| ----------------------------------------------------------------- | ------------------ |
| `docs/canonical/TZ-00-domain-event-canon.md`                      | `7c9f05ce7e686fa3` |
| `docs/canonical/canon-version.json`                               | `6ffdd7089d269679` |
| `docs/adr/ADR-054-canon-0.8.0-party-finance-context-additions.md` | `ece021d75ae23556` |
| `docs/packs/PACK-10-CANON-0.8.0-ACCEPTANCE-MATRIX.md`             | `a21dccf5f8e39d6b` |
| `docs/packs/PACK-10-CANON-0.8.0-COMPATIBILITY.md`                 | `a2eb18937b27c04d` |
| `scripts/check_canon_0_8_0.py`                                    | `31aae85752969ca9` |
| `tests/repository/test_canon_0_8_0_amendment.py`                  | `93debc1c2e7327dd` |
| `packages/python/epd2-core/src/epd2_core/version.py`              | `9c28c59f2ba9f13b` |
| `packages/typescript/epd2-types/src/version.ts`                   | `b3961ccb7aff5e54` |
| `packages/python/epd2-core/tests/test_version.py`                 | `5fe6dbd039919291` |
| `packages/typescript/epd2-types/tests/version.test.ts`            | `f5bf9ff78ce54bf8` |
| `docs/canonical/README.md`                                        | `f88d43741e03f599` |
| `docs/adr/README.md`                                              | `0ba678d6d16ae2bc` |
| `docs/architecture/data-ownership.md`                             | `5fb2e02f996f9f88` |
| `docs/architecture/service-boundaries.md`                         | `6ef3ea57c7967b22` |
| `README.md`                                                       | `7b2f1f65bf79b5bb` |
| `CHANGELOG.md`                                                    | `2f24a1dc9e97455b` |

(This report's own hash is necessarily absent from that table, and the
**SHA-256 of the delivered archive `EPD2_PACK-10_CANON_0.8.0_CANDIDATE.zip`
is stated in the delivery message accompanying it** — an archive cannot
contain a hash of itself. The manifest above is what allows the archive's
contents to be verified independently of its packaging.)

## 15. Confirmations

- **No runtime implementation was added.** No `services/finance-service`
  directory, no source file, no `__init__.py`, no package. No file
  anywhere under `services/`, `packages/`, `frontend/` or `contracts/`
  has a name containing `finance` — check 5 of
  `scripts/check_canon_0_8_0.py` enforces exactly this and passes.
- **No migration, no OpenAPI operation, no runtime JSON Schema, no
  frontend page, no business test.** `contracts/**` is byte-identical to
  the baseline. The only test files touched are the two version tests,
  whose expected canon version changed; no test was weakened or removed.
- **`REPOSITORY_VERSION` remains `0.9.0`** in both mirrored locations,
  and the latest released CHANGELOG heading remains `## [0.9.0]`. The
  repository was **not** raised to `0.10.0`.
- **PACK-01 – PACK-09 implementation and existing backend behaviour are
  untouched.** No service source file, contract or existing test was
  modified.
- **No accepted ADR was rewritten.** ADR-001 – ADR-043 are unchanged;
  ADR-048 – ADR-053 remain `proposed`; ADR-054 is `proposed`. Check 16
  enforces this and passes.
- **Existing domain ownership is unchanged** except for the twenty-one
  additive finance rows the amendment explicitly introduces.
- **Business scope did not expand** beyond the architecturally accepted
  PACK-10 specification; the four deliberate deltas (three events, one reason
  code, the report-state renaming, the adopted role incompatibility) are
  named in section 12 and in the compatibility document.
- **No claim of production readiness or legal compliance is made.** Canon
  19f asserts no compliance with the Parteiengesetz, the
  Abgabenordnung, the Handelsgesetzbuch, the GDPR, the BDSG or any other
  law; it encodes no statutory threshold; `AuditConclusion` is not a
  statutory audit opinion; pseudonymization is not anonymity; and canon
  19f.25 states that implementation is authorized by neither this canon
  content nor the ADRs alone.
- **This is a canon candidate.** ADR-054 is `proposed`. Until it is
  accepted, the amended canon in this archive is a proposal that has been
  written into the document for review, not an accepted canon edit —
  `docs/canonical/README.md` and `docs/adr/README.md` say so in the same
  words.
