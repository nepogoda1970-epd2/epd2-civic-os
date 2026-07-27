# CLAUDE-PACK-10 — Party Finance, Rechenschaftsbericht & Financial External Influence: Specification/ADR Round Handover Report

Status: **PACK-10 SPECIFICATION CANDIDATE.** Specification and ADR round
complete, documentation only. No service code, database, migration,
infrastructure, runtime contract or production integration is authorized
or delivered by this round. **No GitHub Actions run has ever been
performed for PACK-10, and none is claimed by this report.** Section 6
states exactly what was and was not verified locally, distinguishing this
round's own results from PACK-09's separately confirmed external result.

## 1. Baseline

| Item                         | Value                                                 |
| ---------------------------- | ----------------------------------------------------- |
| Baseline archive             | `epd2-civic-os-PACK-09-IMPLEMENTATION-0.9.0-PASS.zip` |
| `REPOSITORY_VERSION` before  | `0.9.0`                                               |
| `REPOSITORY_VERSION` after   | `0.9.0` — unchanged                                   |
| `CANON_VERSION` before       | `0.7.0`                                               |
| `CANON_VERSION` after        | `0.7.0` — unchanged                                   |
| Latest accepted ADR at start | ADR-043                                               |
| First ADR number used here   | ADR-048                                               |
| Baseline state               | PACK-01 through PACK-09 FINAL PASS; PACK-09 closed    |

The baseline's own external verification result (556 required paths;
Python 2659 passed / 4 skipped; TypeScript 3 passed; frontend 11 passed;
Prettier, Ruff, mypy and the Next.js build all PASS) belongs to PACK-09.
It is neither re-run nor re-claimed here.

## 2. Files added — fifteen

Documentation only. Line counts are as delivered.

| Path                                                                                  | Lines | Purpose                                                  |
| ------------------------------------------------------------------------------------- | ----- | -------------------------------------------------------- |
| `docs/packs/PACK-10-SPECIFICATION.md`                                                 | 2176  | The normative specification                              |
| `docs/packs/PACK-10-THREAT-MODEL.md`                                                  | 753   | Thirty-five threats, eight fields each                   |
| `docs/packs/PACK-10-CANON-AMENDMENT-PROPOSAL.md`                                      | 700   | Proposed canon addition `0.7.0 → 0.8.0` (not applied)    |
| `docs/packs/PACK-10-IMPLEMENTATION-PLAN.md`                                           | 518   | Gates, eight phases, file inventory, sequencing risks    |
| `docs/packs/PACK-10-ACCEPTANCE-MATRIX.md`                                             | 473   | 137 planned tests and the invariant coverage map         |
| `docs/packs/PACK-10-CROSS-PACK-BOUNDARIES.md`                                         | 390   | Ownership matrix, reads, references, forbidden edges     |
| `docs/packs/PACK-10-OPEN-DECISIONS.md`                                                | 335   | OD-1 through OD-22                                       |
| `docs/packs/PACK-10-CANON-AMENDMENT-ASSESSMENT.md`                                    | 297   | The explicit determination that an amendment is required |
| `docs/adr/ADR-052-finance-authority-separation-and-independent-audit.md`              | 418   | ADR-E equivalent                                         |
| `docs/adr/ADR-053-pack-10-pack-09-pack-11-pack-35-boundaries.md`                      | 380   | ADR-F equivalent                                         |
| `docs/adr/ADR-049-authoritative-finance-ledger-and-correction-model.md`               | 353   | ADR-B equivalent                                         |
| `docs/adr/ADR-051-rechenschaftsbericht-lifecycle-snapshot-and-authority-semantics.md` | 355   | ADR-D equivalent                                         |
| `docs/adr/ADR-048-pack-10-finance-service-decomposition.md`                           | 340   | ADR-A equivalent                                         |
| `docs/adr/ADR-050-purpose-scoped-financial-party-references-and-aggregation.md`       | 329   | ADR-C equivalent                                         |
| `docs/handover/PACK-10-SPEC-REPORT.md`                                                | 308   | This report                                              |

## 3. Files changed — three

| Path                 | Change                                                                                                                            |
| -------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| `docs/adr/README.md` | Six new index rows (ADR-048 – ADR-053, all `proposed`) and a narrative entry for this round. The canon-version line is untouched. |
| `README.md`          | One PACK-10 status entry identifying the pack as specification-only and not implemented.                                          |
| `CHANGELOG.md`       | One new `## [Unreleased] - PACK-10 specification candidate (documentation only)` section, above the existing canon-0.7.0 entry.   |

Nothing else in the archive differs from the baseline. Verified by a full
recursive comparison against the unpacked baseline: three files differ,
fifteen are new, none is deleted or moved.

## 4. What this round decided

### 4.1 ADRs proposed — six, all `proposed`, none accepted

| ADR     | Decision                                                                                                                                                                      |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ADR-048 | One bounded context `services/finance-service` with explicitly separated internal modules (option 3 of four analysed)                                                         |
| ADR-049 | Layered ledger: the double-entry general ledger is authoritative for monetary effect, the transaction register for the business fact and provenance; posted entries immutable |
| ADR-050 | Purpose-scoped opaque `FinancePartyHandle` with a governed matching act; lawful aggregation without a platform-wide identifier; restricted, audited resolution                |
| ADR-051 | Ten-state `Rechenschaftsbericht` lifecycle; create-once source snapshot; submission ≠ acceptance ≠ publication; append-only version chain; frozen historical perimeter        |
| ADR-052 | Four new institutional roles plus five action-level separations; the extended non-combinable-role matrix PACK-08 section 9.3 reserved; create-once `AuditConclusion`          |
| ADR-053 | Ownership boundaries across PACK-08/09/10/11/12/13/14/35; reference-only PACK-09 integration; placeholder-only PACK-11 integration; `FinanceEvidenceRef` remains sufficient   |

No separate reason-code ADR was created. ADR-004 already fixes the
registry model and additive-code convention, the proposed catalogue lives
in specification section 15, and nothing is registered this round —
adding a seventh ADR for it would have been artificial fragmentation,
which the governing request explicitly forbids.

### 4.2 Domain ownership decision

`services/finance-service` — one new bounded context, not created this
round. Seventeen internal modules with load-bearing boundaries: `budgets`
may not import a ledger store, `projections` may perform no authoritative
write, `audit_engagement` may not write into anything it audits, and
`partyregistry` is the only module that may resolve a party handle. The
service would import `epd2_core` and `epd2_audit_core` only, the rule
ADR-038 fixed for `compliance-service`.

Twenty-one authoritative aggregates are specified. Four candidate
concepts were deliberately merged or renamed rather than added
(`Liability` → `FinancialObligation`; `AccountClassification` →
`FinancePolicy(chart_of_accounts)`; `Restatement` → a report version with
a typed backward reference; `AuditOpinion` → `AuditConclusion`), and four
concepts the candidate list did not name were added because the analysis
required them (`FinancePolicy`, `FinancePolicyBinding`,
`FinancePartyHandle`, `PeriodReopeningRecord`).

### 4.3 Canon amendment conclusion

**Option 2 — a canon amendment is required.** Not conditional, not
deferred to the implementation round's discretion.

PACK-10 introduces or materially clarifies system-wide concepts no
accepted canon section covers, needs new section 22 ownership rows, new
section 23 forbidden links and new section 24 reason codes, and none of
that can be added by a pack-level registry file. The determination is
argued concept by concept in
`docs/packs/PACK-10-CANON-AMENDMENT-ASSESSMENT.md`; the proposed text is
`docs/packs/PACK-10-CANON-AMENDMENT-PROPOSAL.md` (new section 19f between
19e and 20 using the established non-renumbering technique, new section
20.17 event catalogue, ownership rows, forbidden links, reason codes,
`CANON_VERSION 0.7.0 → 0.8.0`).

**The canon was not edited.** `docs/canonical/TZ-00-domain-event-canon.md`
is byte-identical to the baseline's (4514 lines), and
`docs/canonical/canon-version.json` still reads `"canon_version":
"0.7.0"`. The amendment is a separate, dedicated later round, exactly as
ADR-032 through ADR-036 deferred to ADR-037 for PACK-08.

### 4.4 Counts

| Item                                                    | Count                              |
| ------------------------------------------------------- | ---------------------------------- |
| Hard invariants                                         | 55 (46 required + 9 from analysis) |
| Authoritative aggregates                                | 21                                 |
| Proposed domain events                                  | 69                                 |
| Proposed new reason codes                               | 44                                 |
| Existing reason codes reused verbatim                   | 32                                 |
| Proposed `pack-10.yml` entries in total                 | 76                                 |
| Threats analysed                                        | 35                                 |
| Planned tests in the acceptance matrix                  | 137 (`AT-001` – `AT-137`)          |
| Open decisions                                          | 22 (`OD-1` – `OD-22`)              |
| Existing reason codes enumerated for collision analysis | 303                                |

## 5. Cross-pack dependencies

- **PACK-08** — organizations, organizational units, `OrganizationalScope`,
  `OrganizationalAuthority`, inheritance policy. Read through
  `organization-service`'s published interface; four new `role_code`
  values proposed as additive configuration on its extensible field.
- **PACK-09** — `LegalCaseRef`, `DeadlineRef`, `DeadlineTriggerRef`,
  `NoticeRef`, `NoticeEffectRef`, `HoldRef`, `RecordClassRef`,
  `JurisdictionRef`, `CasePartyRef` (never resolved by PACK-10).
  Reference-only. `accepted_by_authority` is reachable **only** through a
  governed `NoticeEffectDecision` (ADR-043).
- **PACK-11** — one placeholder shape for eleven document kinds; four
  future interface requirements named; no bytes, signatures, chains or
  custody in PACK-10.
- **PACK-12** — future DLP attaches at the single `projections.py` export
  chokepoint.
- **PACK-13** — production data plane, event bus, schema registry;
  in-memory reference stores only until then.
- **PACK-14** — real IAM/eID and qualified signatures.
- **PACK-35** — general lobbying and meeting disclosure; PACK-10
  implements none of it and exposes typed integration points only.
- **PACK-04** — the public-disclosure and small-cell precedents PACK-10
  reuses rather than reinventing.
- **No pack yet owns** payment providers, bank/PSD2, automated transfers,
  tax filing or a real external-authority submission gateway (OD-16).

## 6. Verification performed — and not performed

**Performed.** Full read of the baseline documentation set: the canon
(sections 4, 8, 19a–19e, 20–24), `PACK-08-GLOSSARY.md`, the PACK-08
specification and open decisions, the PACK-09 specification and
implementation notes, PACK-09's final handover and known limitations,
ADR-032 through ADR-043, the ADR index, all eight pack reason-code
registry files (303 distinct existing codes enumerated), PACK-09's
`references.py` in full, `scripts/check_repository.py`'s required-path
list, the repository and contract test inventories, and the
Prettier configuration.

**Performed.** Documentation-level consistency checks: every path the new
documents reference _as existing_ exists in this archive, and every path
they name as a future deliverable (`services/finance-service/**`,
`contracts/reason-codes/pack-10.yml`, `contracts/openapi/pack-10.yaml`,
`docs/packs/PACK-10-IMPLEMENTATION.md`,
`docs/handover/PACK-10-IMPLEMENTATION-REPORT.md`) is explicitly labelled
as planned and does not exist; ADR numbering
continues after ADR-043 with no gap and no reuse; all six new ADRs are
`proposed`; no accepted ADR text was altered; the canon and
`canon-version.json` are byte-identical to the baseline; a full recursive
diff against the unpacked baseline shows exactly the fifteen additions
and three modifications listed in sections 2 and 3.

**Not performed, and not claimed.** No `pytest`, no `ruff`, no `mypy`, no
`prettier --check`, no `npm test`, no Next.js build, no GitHub Actions
run. This round adds no code and no contract, so those suites are
unchanged from PACK-09's verified result — but "unchanged" is a statement
about the diff, not a re-verification, and this report does not present it
as one.

**A specific local limitation, recorded rather than glossed over.**
Prettier could not be executed in the environment this round was prepared
in: the npm registry was unreachable, so `prettier@3` could not be
installed. The new markdown was therefore written to Prettier 3's default
markdown style (printWidth 80, `proseWrap: preserve`, ATX headings,
`_italic_`, no trailing whitespace, single trailing newline) and its
tables were generated by a padding routine that reproduces Prettier's
column padding. **`prettier --check .` on the added documentation remains
unconfirmed** and should be treated as the first thing any CI run or
implementation round verifies. If it reports a diff, it will be
whitespace inside tables, not content.

## 7. Unresolved owner decisions

Twenty-two, consolidated in `docs/packs/PACK-10-OPEN-DECISIONS.md`. The
nine that block seeding real policy content are OD-1 (report taxonomy),
OD-3 (aggregation perimeter), OD-4 (contributor categories), OD-5
(thresholds), OD-7 (public disclosure granularity), OD-9 (sign-off
model), OD-14 (retention periods), OD-17 (currency scope) and OD-18
(chart of accounts). Two are architectural rather than legal: OD-15 (a
possible later typed `FinanceRecordRef` on PACK-09's side) and OD-22
(whether the party-handle registry should later be extracted from
`finance-service`). One is a repository-level matter that will bite the
implementation round if ignored: OD-20 —
`docs/canonical/canon-version.json` declares
`"repository_compatibility": ">=0.1.0 <0.10.0"`, which a PACK-10
implementation at `REPOSITORY_VERSION = 0.10.0` would fall outside.

Every recommended default in that document is marked where it is legally
unverified, and none of them may be seeded as law.

## 8. Implementation blockers

1. **The canon amendment has not been performed.** Implementation is
   gated on ADR-048 – ADR-053 being accepted **and** the amendment
   landing. Neither authorizes implementation alone.
2. **Nine legal open decisions** must be resolved before any policy
   content is seeded (section 7).
3. **No external submission or banking interface exists or is owned**
   (OD-16), so `SubmissionRecord`, `PaymentAuthorization` and
   `ImportBatch` would ship as governed records with no integration
   behind them.
4. **PACK-11 does not exist**, so no assertion about a document's
   authenticity, signature or admissibility can be obtained; affected
   actions fail closed by design
   (`FINANCE_EVIDENCE_ASSERTION_UNAVAILABLE`).
5. **A canon defect must be closed in the amendment round:** canon
   19e.16 rule 3 forbids combining `finance auditor` with `finance
administrator`, but `finance_administrator` is not among the
   `role_code` values canon 19e.15 enumerates. The proposal closes it;
   until then the incompatibility references a role the canon never
   defines.
6. **An entity-naming decision needs owner confirmation:** the finance
   aggregate's canonical name is `FinanceContribution`, because canon
   section 22 cannot hold two rows named `Contribution` (canon 13.2's
   belongs to Discussion Service).

## 9. Legal assumptions requiring external review

None of the following is asserted as law by this round:

- what the `Rechenschaftsbericht` must contain, and in what structure;
- which contributor categories exist, and which contributions are
  prohibited or restricted;
- every monetary threshold, reporting period and aggregation perimeter;
- what constitutes a related party or an intermediary chain;
- what must be published, at what granularity, and whether a donor must
  be named;
- the counter-performance test that separates sponsorship from donation;
- who may sign the report, and whether the preparer may be the signatory;
- which retention periods apply to finance records;
- acceptable in-kind valuation methodologies;
- whether dues accounting may run through a purpose-scoped reference
  rather than a membership identifier;
- statistical disclosure control thresholds;
- the final division between financial external influence (PACK-10) and
  general lobbying disclosure (PACK-35).

The specification is built so that each of these is a versioned,
effective-dated policy input rather than a constant in code, precisely so
that legal review can change them without a redesign.

## 10. Confirmations

- **No production code was written.** No file under `services/`,
  `packages/`, `frontend/`, `contracts/`, `tests/` or `scripts/` was
  added, modified or deleted. No `services/finance-service` directory
  exists, and none was created to reserve the name. No empty runtime
  package was added.
- **No runtime contract was modified.** `contracts/**` is untouched: no
  JSON Schema, no OpenAPI operation, no event payload schema, no
  reason-code registry file. `contracts/reason-codes/pack-10.yml` is
  proposed in documentation and does not exist.
- **No version was changed.** `REPOSITORY_VERSION` remains `0.9.0` in
  every mirrored location; `CANON_VERSION` remains `0.7.0`;
  `canon-version.json`, `epd2_core/version.py` and
  `epd2-types/src/version.ts` are byte-identical to the baseline.
- **Repository-checker behaviour is unchanged.**
  `scripts/check_repository.py` was not modified, and the new
  documentation paths were deliberately not added to its required-path
  list — the same precedent ADR-026 through ADR-037 set, recorded in that
  file's own comment.
- **PACK-09 remains intact.** No PACK-09 document, ADR, contract, code
  file or test was altered. No previously accepted ADR was rewritten.
- **No scope leakage.** Nothing here implements PACK-11, PACK-12,
  PACK-13, PACK-14, PACK-15/16, PACK-17, PACK-18 or PACK-35.
- **No global user ID was introduced**, and no entity, event, schema or
  reference in the proposed model carries one.
- **No claim of legal compliance or production readiness is made**, in
  this report or anywhere in the delivered documentation.
- **PACK-10 remains a specification candidate.** The result of this round
  is **PACK-10 SPECIFICATION CANDIDATE**, for architectural review. It is
  not a PASS.
