# PACK-12 — Specification & ADR Handover Report

**Round:** CLAUDE-PACK-12 — Privileged Administration, Search & Data Export Security
**Round type:** specification and ADR only
**Artifact:** `EPD2_PACK-12_PRIVILEGED_ADMIN_SEARCH_EXPORT_0.12.0_SPEC_ADR_CORRECTED.zip`
**Supersedes:** `EPD2_PACK-12_PRIVILEGED_ADMIN_SEARCH_EXPORT_0.12.0_SPEC_ADR.zip`

> **Status note added by the PACK-12 implementation candidate round
> (2026-07-29).** The "specification-only / not implemented" statement
> above describes the _specification round_ that produced this document
> and is preserved as the historical record. It is no longer the state of
> the repository: `services/privileged-access-service` now implements this
> specification as an **implementation candidate** at repository version
> `0.12.0`.
>
> **LOCAL VERIFICATION INCOMPLETE / EXTERNAL CI PENDING / NOT FINAL PASS.**
> Nothing here is claimed as verified, passed, or production-ready. See
> `docs/handover/PACK-12-IMPLEMENTATION-CANDIDATE-REPORT.md` section 5.

**Status:**

- `NO CODE CHANGED`
- `NOT IMPLEMENTED`
- `NOT PASS`

**Baseline:** `EPD2_PACK-11_GOVERNED_DOCUMENTS_EVIDENCE_0.11.0_FINAL_PASS.zip`
(PACK-01 through PACK-11: FINAL PASS)

**Versions:** `REPOSITORY_VERSION` remains `0.11.0`. `CANON_VERSION`
remains `0.8.0`. `0.12.0` appears in this package only as PACK-12's
_target_, never as a setting.

---

## 1. What was created

Eighteen documentation files. Nothing else.

**Specification package** — `docs/packs/PACK-12/`

| File                                   | Content                                                                                                                |
| -------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| `PACK-12-SPECIFICATION.md`             | 19 sections; 116 normative statements `P12-<AREA>-NNN` across 15 areas                                                 |
| `PACK-12-ROLE-SEPARATION-MATRIX.md`    | 2 institutional roles consumed + 9 operational assignments; 17-row capability matrix; 14 added pairs + 1 preserved     |
| `PACK-12-DATA-SEARCH-EXPORT-MATRIX.md` | Canonical classification → enforcement tier mapping; 20 data classes; voting split; 9 enforcement points               |
| `PACK-12-EVENT-CATALOG.md`             | 44 event types in 6 families; safe metadata; forbidden payload contents                                                |
| `PACK-12-REASON-CODE-CATALOG.md`       | 97 codes in 4 prefixes plus 13 reused; registry obligations                                                            |
| `PACK-12-THREAT-MODEL.md`              | 22 threats, each with asset, attacker, boundary, preventive, detective, evidence, residual, dependency                 |
| `PACK-12-ACCEPTANCE-MATRIX.md`         | 101 criteria in 13 groups, each with ID, requirement, rationale, component, evidence, testability, blocker, dependency |
| `PACK-12-CANON-ASSESSMENT.md`          | Verdict and its reasoning, reconciled against framework 0.8.2 CORRECTED                                                |
| `PACK-12-FIR-COVERAGE-MATRIX.md`       | 26 FIR entries with status-before, treatment, references, implementation obligation; zero marked implemented           |

**Decisions** — `docs/adr/`

| ADR                                                    | Decision                                                                                                                                                   |
| ------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ADR-061-pack-12-privileged-role-separation`           | Two institutional roles consumed unchanged; nine operational assignments via 19e.15's open list; 14 added pairs + 1 preserved                              |
| `ADR-062-pack-12-purpose-scoped-pam`                   | Nine jointly-mandatory grant properties; SoD at approval and re-evaluated at activation; automatic expiry, no in-place extension                           |
| `ADR-063-pack-12-break-glass-dual-control`             | Separate workflow; dual control; unsuppressible out-of-band notification; undelivered ⇒ escalate; renewal is a new decision                                |
| `ADR-064-pack-12-authorization-aware-search`           | Search never expands source authorization; four enforcement points; query-time re-resolution; count/facet/snippet/cache rules                              |
| `ADR-065-pack-12-high-confidentiality-index-exclusion` | 11 categories excluded by default; 4 absolutely; list is a floor a stricter domain overrides                                                               |
| `ADR-066-pack-12-governed-data-export`                 | Export as a governed object; authority never inherited from read, search or admin privilege; fields excluded before generation; revocation is not deletion |
| `ADR-067-pack-12-dlp-and-disclosure-control`           | 18 DLP controls; assessment before decision; fail-closed detection; threshold never the only protection; cumulative release assessed                       |
| `ADR-068-pack-12-privileged-session-evidence`          | 18 evidence fields; references not copies; sealed via PACK-11 bundles; tamper evidence, not tamper resistance                                              |

**Handover** — `docs/handover/PACK-12-SPEC-ADR-REPORT.md` (this file).

---

## 2. Architecture gaps addressed

| Gap      | Closed by                                                                                                                                                     |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `AGR-23` | Privileged administration: sections 3–6 of the specification; ADR-061, ADR-062, ADR-063, ADR-068                                                              |
| `AGR-24` | Search, export and DLP by purpose and record class: sections 7–10; ADR-064, ADR-065, ADR-066, ADR-067                                                         |
| `AGR-20` | Statistical disclosure control **foundation only**: section 11; ADR-067. The production analytics engine and the data plane it needs remain PACK-13-dependent |

Register invariants given concrete form: `FIR-INV-006`, `FIR-INV-007`,
`FIR-INV-008`, `FIR-INV-009`, `FIR-INV-011`, `FIR-INV-013`,
`FIR-INV-014`, `FIR-INV-015`, under roadmap entry `FIR-ROADMAP-002`.

**Given form is not implemented.** No `FIR-*` entry may be marked
implemented on the strength of this round.

---

## 3. What remains out of scope

Not implemented and not fully specified, per specification section 16:
production database platform; schema registry and contract-evolution
runtime; final external identity provider; complete authentication and
MFA; PKI, HSM and key management; voting unlinkability protocol; voting
implementation; full incident-response platform; backup and recovery;
complete communications gateway; complete frontend workspaces; public
transparency publication; external recipient portal; production DLP
vendor integration; full legal activation; party operational policy as
legally approved policy; unrelated product domains.

These are referenced as dependencies. None is absorbed.

---

## 4. Dependencies

| Pack       | PACK-12 needs                                                                                  | Hardness of the dependency                                |
| ---------- | ---------------------------------------------------------------------------------------------- | --------------------------------------------------------- |
| PACK-13    | Production data plane, real index, durable event bus, schema registry, release-history storage | Hard for threats 08, 09, 12, 14, 15, 16, 22               |
| PACK-14    | Authentication, session assurance, gateway, identity provider                                  | Hard for threats 05, 06, 11; AC-P12-090 is deferred to it |
| PACK-15/16 | Voting trust boundary and implementation                                                       | PACK-12 only forbids reaching voting material             |
| PACK-17    | Incident response, out-of-band notification transport                                          | Hard for threat 20; `P12-BG-008` fixes the obligation now |
| FRONT-PACK | Workspace UX, design system, navigation                                                        | PACK-12 defines 12 administrative surfaces only           |

---

## 5. Canon assessment

# CANON AMENDMENT NOT REQUIRED

Reasoning in `PACK-12-CANON-ASSESSMENT.md`, now reconciled against
`EPD2 Architecture Domain Framework 0.8.2 CORRECTED` and
`EPD2 Target Frontend Architecture 0.8.2 CORRECTED`.

In short: every system-wide rule PACK-12 enforces already exists as an
approved `FIR-INV-*` register entry; the two institutional roles it works
with are the framework's own and are consumed unchanged, so PACK-12
introduces nine operational assignments rather than eleven roles; those
nine use canon 19e.15's open-list extension point and 19e.16's explicitly
permitted "make stricter, never relax" rule; the reason codes follow
PACK-11's precedent, whose registry likewise contains no
`source: canon-0.8.0` entry; the events use canon section 21's envelope
and section 20's naming convention unchanged; and nothing in PACK-12
binds a domain outside PACK-12 except by restating that domain's own
existing rule.

The reconciliation strengthened the verdict rather than weakening it. All
three corrections — institutional roles consumed rather than introduced,
canonical classification authoritative rather than replaced, certified
results left to the domain that owns them — reduce what PACK-12 asserts
about framework-owned concepts.

Section 7 of that document records the five findings that would reverse
the verdict. `OD-P12-01` is closed.

The canon is not modified. `docs/canonical/` is untouched.

## 6. Open implementation decisions

| ID              | Decision                                                                                  |
| --------------- | ----------------------------------------------------------------------------------------- |
| ~~`OD-P12-01`~~ | **CLOSED** — reconciled against framework 0.8.2 CORRECTED; spec §0.1, canon assessment §0 |
| `OD-P12-02`     | Whether privileged investigative search is defined at all                                 |
| `OD-P12-03`     | Numeric values: break-glass maximum duration, dormancy interval, cohort thresholds        |
| `OD-P12-04`     | Whether PACK-12 is one service or three bounded contexts                                  |
| ~~`OD-P12-05`~~ | **CLOSED** — ADRs renumbered `ADR-061`..`ADR-068`; all internal references updated        |
| `OD-P12-06`     | Whether `QueryAudit` belongs to `audit-core` or the PACK-12 context                       |
| `OD-P12-07`     | Recipient-category taxonomy and which categories may ever receive special-category data   |
| `OD-P12-08`     | How cumulative-release accounting is bounded in time and storage                          |

`OD-P12-01` and `OD-P12-05` are closed by this correction round. Six
remain open (`OD-P12-02`, `03`, `04`, `06`, `07`, `08`); none of them is
an unresolved disagreement — each is a design choice the implementation
round must make, recorded so it is made deliberately.

The eight ADRs are now numbered `ADR-061` through `ADR-068`, continuing
the repository's sequential registry from `ADR-060`, and use the
repository's `ADR-NNN-lowercase-slug.md` filename convention. All internal
cross-references in every package file were updated. `docs/adr/README.md`
is **not** touched by this round: it lives in the repository baseline, and
the implementation candidate must add the eight entries to it at merge
time.

## 7. Future tests

The 101 criteria in `PACK-12-ACCEPTANCE-MATRIX.md` each carry a
testability approach. The families the implementation round will need:

- **Structural tests** — absence of a universal-admin path; absence of
  any voting reference type; absence of a mutating operation on the audit
  port; exact event-name set; every reason-code literal registered;
  forbidden-phrase scans for production, legal and tamper-resistance
  claims.
- **Property tests** — for random subject/record pairs, findable ⊆
  openable; a grant missing any of the nine properties cannot be
  constructed; suppressed values not recoverable from totals or
  neighbours.
- **Time-controlled tests** — grant expiry, break-glass hard expiry,
  artifact expiry, dormancy, using the repository's injected `Clock`
  rather than real elapsed time.
- **Separation tests** — each of the 15 incompatibility pairs; each
  per-object self-approval rule; requester ≠ approver ≠ reviewer.
- **Leakage tests** — count identical whether or not restricted matches
  exist; no facet, autocomplete or snippet discloses restricted values;
  two subjects with the same query share no cache entry.
- **Boundary tests** — cross-organization grant, query and export;
  legal hold widens nothing; denied field absent from artifact bytes, not
  merely hidden.
- **Regression tests** — every PACK-08 incompatibility pair still holds;
  no PACK-09 or PACK-11 entity or reason code duplicated.

None of these tests exists. They are specified, not written.

---

## 7a. Corrections applied in this round

| #   | Correction                                                                                                                                                                                                             | Files changed                                                                                                                               |
| --- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Reconciliation against framework 0.8.2 CORRECTED; every "framework unavailable" caveat removed; `OD-P12-01` closed                                                                                                     | Specification §0.1; canon assessment §0 and §7; this report                                                                                 |
| 2   | Institutional roles (System Administrator, Security Administrator) separated from nine operational assignments; `P12-ROLE-014`..`021` added                                                                            | Role separation matrix; specification §3; ADR-061; canon assessment §3; threat model; acceptance matrix                                     |
| 3   | Canonical classification made authoritative; derived enforcement tier introduced; normative mapping table added; `P12-CLS-001`..`005`                                                                                  | Data/search/export matrix §2; specification §8.0; ADR-064; ADR-065; ADR-066; acceptance matrix                                              |
| 4   | Voting rule split: absolute prohibition on ballot-level and intermediate/partial/non-certified tally material vs. permitted publication of a final certified result by the authoritative domain; `P12-VOTE-001`..`006` | Data matrix §4; specification §8.1; ADR-064; ADR-065; ADR-066; event catalog; reason-code catalog; threat model T-P12-21; acceptance matrix |
| 5   | `PACK-12-FIR-COVERAGE-MATRIX.md` added — 26 FIR entries, zero marked implemented                                                                                                                                       | New file; acceptance matrix `AC-P12-101`                                                                                                    |
| 6   | Master register obligation recorded for the implementation candidate (section 7b)                                                                                                                                      | This report                                                                                                                                 |
| 7   | ADRs renumbered `ADR-061`..`ADR-068`; all references updated; `OD-P12-05` closed                                                                                                                                       | All eight ADR files renamed; twelve files' references updated                                                                               |

## 7b. Master register obligation for the implementation candidate

This correction round creates **no** second register, modifies **no**
repository baseline file, and touches
`docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md` not at all.
That file lives in the PACK-11 FINAL PASS baseline and stays there
unchanged.

The implementation candidate MUST, when it opens:

- update the **existing** register file at
  `docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md` — never
  create a second or parallel future register;
- set the baseline to PACK-11 / `0.11.0`;
- set `FIR-ROADMAP-001` to `implemented`;
- set `FIR-ROADMAP-002` to `scheduled` or `under_review` — **never**
  `implemented` on the strength of a specification round;
- record PACK-01 through PACK-11 as `implemented`;
- remove governed documents from the "specified but not implemented"
  list, since PACK-11 shipped them;
- preserve the history of every entry; no entry is silently deleted or
  repurposed (register section 1.2);
- keep the single-file policy of register section 23.

## 8. Consistency checks performed

| Check                                                   | Result                                                                   |
| ------------------------------------------------------- | ------------------------------------------------------------------------ |
| Does not duplicate PACK-09 records governance           | Pass — retention, disposal and hold state are consumed by reference only |
| Does not duplicate PACK-11 governed documents/evidence  | Pass — evidence bundles reused by reference; no document bytes held      |
| Does not absorb PACK-13 production data plane           | Pass — index, bus and registry named as dependencies                     |
| Does not absorb PACK-14 authentication/gateway          | Pass — actor reference assumed, never minted; AC-P12-090 deferred        |
| Does not absorb PACK-15/16 voting                       | Pass — only prohibitions; no voting entity defined                       |
| Does not absorb PACK-17 incident/resilience             | Pass — notification obligation fixed, transport deferred                 |
| Role names consistent with the institutional role model | Pass — 11 codes via 19e.15's open list; 19e.16's seven untouched         |
| Data classes consistent with the classification model   | Pass — PACK-09's four levels reused; no fifth level added                |
| Search/export rules consistent with hard invariants     | Pass — mapped in canon assessment section 2                              |
| Roadmap dependencies preserved                          | Pass — `FIR-ROADMAP-002` scope list matches                              |
| Frontend scope minimal                                  | Pass — 12 administrative surfaces; `P12-FE-002` forbids expansion        |
| MUST / MUST NOT / SHOULD used consistently              | Pass — normative statements carry IDs; prose is unmarked                 |
| No production-readiness promise                         | Pass — scanned                                                           |
| No legal compliance or activation claim                 | Pass — scanned                                                           |
| No repository or canon version change                   | Pass — no version file exists in this package                            |

---

## 9. Confirmations

- **`NO CODE CHANGED`** — this package contains eighteen `.md` files and
  nothing else. No `services/`, no `packages/`, no `contracts/`, no
  `tests/`, no `scripts/`, no CI file, no version file, no canon file.
  The package is additive documentation; it modifies no file of the
  PACK-11 FINAL PASS baseline.
- **`NOT IMPLEMENTED`** — no service, module, schema, registry file,
  event implementation, test or frontend exists for PACK-12. Every
  control described is a requirement on a future round.
- **`NOT PASS`** — this round has no CI verification, no acceptance
  criterion satisfied, and no PASS status. PACK-12 is neither a candidate
  nor complete.
- **No production readiness** is claimed, asserted or implied.
- **No legal activation, legal validity or regulatory compliance** is
  claimed, asserted or implied.

---

## 10. Package file digests

SHA-256 of every other file in the corrected package. The digest of
this report itself and of the ZIP are reported in the delivery
message, since neither can be contained in the file it describes.

| File                                                               | SHA-256                                                            |
| ------------------------------------------------------------------ | ------------------------------------------------------------------ |
| `docs/adr/ADR-061-pack-12-privileged-role-separation.md`           | `f6e80fa7356a3d5b40b0f9492c45df34eaaa5f400d1a9c3753a89dcbec69e178` |
| `docs/adr/ADR-062-pack-12-purpose-scoped-pam.md`                   | `6a7eda052d9aaa63d78a8d6024763decd68670d727654998a752aa4a629d861b` |
| `docs/adr/ADR-063-pack-12-break-glass-dual-control.md`             | `1b3763eb1eed5f2306341cdaf1354555113fa3385bc32596360c0828e86edf02` |
| `docs/adr/ADR-064-pack-12-authorization-aware-search.md`           | `749eb0cc3c82d8df218e7d71d87d2722aad2f5f641da27e6c7d8717adf5f3c75` |
| `docs/adr/ADR-065-pack-12-high-confidentiality-index-exclusion.md` | `7f61b45386de76a39bb4bae7fbc6da0c04903ac543edb0dfc0f799c6a3b4d30c` |
| `docs/adr/ADR-066-pack-12-governed-data-export.md`                 | `1d83682581b5c208baf1af01c21ec8d94f0b131d48d1f247cca1e41af027f0df` |
| `docs/adr/ADR-067-pack-12-dlp-and-disclosure-control.md`           | `8ee5f2831d98661e2fd75b87412f9d43f9840f39d938fe153c3d8e8ccca17065` |
| `docs/adr/ADR-068-pack-12-privileged-session-evidence.md`          | `7d63267013980701ed1aa1bf892f4239ab5767133c1b0fbb277f275414af3d58` |
| `docs/packs/PACK-12/PACK-12-ACCEPTANCE-MATRIX.md`                  | `0aecb52acc747bd83715f9c453a72a33cf177c2451911ebe98ae18c4e012f2ac` |
| `docs/packs/PACK-12/PACK-12-CANON-ASSESSMENT.md`                   | `14b57db2d4f4b67ca1cd1c6b4a1352f41e28ed9e9aae92b320aec9f22ce6a82f` |
| `docs/packs/PACK-12/PACK-12-DATA-SEARCH-EXPORT-MATRIX.md`          | `7ecf80d86f0aedb8f2ca420d536b16e978702cdf0076ffd6ec2d4c1639491964` |
| `docs/packs/PACK-12/PACK-12-EVENT-CATALOG.md`                      | `2bbf3b10edff3c985cb9362bb338f19325b8dad9bd45bce8bff2f010c2decbf6` |
| `docs/packs/PACK-12/PACK-12-FIR-COVERAGE-MATRIX.md`                | `6999604da5e61d9c657f68b4f6bba6fd2b79c2c5b1a047eb899dcbb5a99eb26f` |
| `docs/packs/PACK-12/PACK-12-REASON-CODE-CATALOG.md`                | `f6ef6ab4f1fb46d54326d0dfd750dc974fe564c6a2cbced050ae59c6d3cf3179` |
| `docs/packs/PACK-12/PACK-12-ROLE-SEPARATION-MATRIX.md`             | `143bf7fa32eef2a0beadb49cbb760078369588e08bac7306251d6ea78e36da0c` |
| `docs/packs/PACK-12/PACK-12-SPECIFICATION.md`                      | `95d03667fc499fb73545b049d119e5a1f8cb60c91bc9f2f112d273f0095ac423` |
| `docs/packs/PACK-12/PACK-12-THREAT-MODEL.md`                       | `631ffa1d15447db27f18877532ed15290ab9e1e4f521c088ca06b039c66c25b8` |
