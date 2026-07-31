# PACK-15 — FIR Coverage Matrix

**Round:** PACK-15 — specification and ADR only. **No code. Not implemented. Not a candidate. Not a PASS.**
**Repository version:** unchanged at `0.14.0` · **Canon version:** unchanged at `0.8.0`
**Baseline:** `EPD2_PACK-14_IDENTITY_AUTHENTICATION_ACCOUNT_SECURITY_0.14.0_FINAL_PASS.zip`
**Authoritative register:** `EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER_UPDATED_V6.md`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**
**Architecture correction applied (2026-07-31).**

Assessed against the **cumulative Master Future Implementation Register
carried in the PACK-14 FINAL PASS archive**, which is the only
authoritative register. No standalone register version is used.

**No FIR entry is marked `implemented` by this round, and none may be.**
Treatment values: **addressed** (fully specified), **partially addressed**
(specified in part, remainder named), **deferred** (recorded as a
dependency owned by a later pack), **unchanged** (untouched by PACK-15).

**New FIR identifiers created by this round: none.**

---

## 1. Roadmap

| FIR               | Status before | Treatment | References              | Implementation-stage obligation                                                                              |
| ----------------- | ------------- | --------- | ----------------------- | ------------------------------------------------------------------------------------------------------------ |
| `FIR-ROADMAP-005` | `approved`    | addressed | whole pack; ADR-089…098 | Build the trust boundary, eligibility and credential separation; satisfy all 126 criteria; only then propose a status change |
| `FIR-ROADMAP-006` | `approved`    | unchanged | —                       | PACK-16 remains future; PACK-15 hands it a boundary and nothing else                                         |

`FIR-ROADMAP-005` MUST NOT move past `scheduled` or `under_review` on the
strength of this round.

---

## 2. Hard invariants

| FIR                                               | Status before                   | Treatment           | References                                             | Implementation-stage obligation                                                                                       |
| ------------------------------------------------- | ------------------------------- | ------------------- | ------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------- |
| `FIR-INV-001` No global user ID                   | `approved`                      | addressed           | ADR-091; assertion prohibited-content list; AC-P15-001…005 | Enforce structurally: prohibited-key and derivability scans over every artifact                                    |
| `FIR-INV-002` Identity/ballot unlinkability       | `approved`                      | addressed **for this boundary** | ADR-093; unlinkability matrix; AC-P15-061…067 | PACK-15 closes the identity→credential half; the credential→ballot half is PACK-16's, and both are needed          |
| `FIR-INV-003` Voting Client isolation             | `approved`                      | addressed **for the boundary**, client deferred | ADR-096; cross-boundary matrix; AC-P15-075…086 | The isolation contract is complete; the client is FRONT-PACK and PACK-16                        |
| `FIR-INV-004` Eligibility/credential separation   | `approved`                      | **addressed**       | ADR-089; ADR-092; separation-of-duties matrix          | This is the entry PACK-15 exists for: separate owners, separate stores, separate keys, separate audit streams        |
| `FIR-INV-005` No intermediate tally               | `approved`                      | addressed **for the pre-tally domain** | ADR-094; prohibition matrix; AC-P15-068…074 | PACK-15 forbids disclosure before closure; the tally itself is PACK-16's                              |
| `FIR-INV-006` Safe feature flags                  | `approved`                      | partially addressed | `SD-12`; AC-P15-092                                     | No flag may disable the spent-set check, an audit obligation, an assurance requirement or a separation of duties     |
| `FIR-INV-007` DLP and controlled export           | `approved`                      | partially addressed | audit separation matrix; AC-P15-094                     | PACK-12 owns the mechanism; PACK-15 adds the no-two-streams export rule                                              |
| `FIR-INV-008` Security/System Admin separation    | `approved`                      | unchanged           | —                                                       | Reused from PACK-12 unchanged                                                                                        |
| `FIR-INV-009` JIT and break-glass governance      | `approved`                      | partially addressed | `SD-09`; AC-P15-089…090                                 | Reuse PACK-12; add the rule that no grant spans the boundary                                                        |
| `FIR-INV-010` Document version integrity          | `implemented in reference form` | unchanged           | —                                                       | Eligibility evidence uses PACK-11 as-is                                                                              |
| `FIR-INV-011` Statistical disclosure control      | `approved`                      | partially addressed | prohibition matrix §3; AC-P15-072…073                   | PACK-12 owns the mechanism; PACK-15 adds joint (set-level) disclosure control                                        |
| `FIR-INV-012` Accessibility as definition of done | `approved`                      | partially addressed | AC-P15-108…112                                          | Every PACK-15 surface must satisfy it; FRONT-PACK builds them                                                        |
| `FIR-INV-013` Bund/Land/Kreis isolation           | `approved`                      | partially addressed | `EC-03`, `EC-04`; AC-P15-008                            | Scope is mandatory on every context, decision, assertion and credential                                              |
| `FIR-INV-014` No universal administration         | `approved`                      | addressed           | separation-of-duties matrix                              | No election console spanning eligibility, issuance and tally may be built                                            |
| `FIR-INV-015` No false production claims          | `approved`                      | addressed           | every status banner; AC-P15-126                          | Keep the banners honest through implementation                                                                       |

---

## 3. Roles

| FIR            | Treatment           | Note                                                                                                                    |
| -------------- | ------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| `FIR-ROLE-002` Election board / election officer | partially addressed | Voting Operations Officer and Eligibility Officer are specified as roles with authorities and prohibitions; the wider election-board model is governance's |
| `FIR-ROLE-003` Independent auditor              | partially addressed | The auditor's access model is specified as bundle-based; the bundle format is `OD-P15-04`                        |
| `FIR-ROLE-005` Election Administration Separation Matrix | **addressed for this boundary** | `PACK-15-SEPARATION-OF-DUTIES-MATRIX.md` is that matrix for eligibility and credential administration; the assembly and candidacy sides remain future |
| `FIR-ROLE-001` DPO                              | unchanged           | —                                                                                                                        |
| `FIR-ROLE-004` Finance auditor                  | unchanged           | —                                                                                                                        |
| `FIR-ROLE-006` Finance separation of duties     | unchanged           | —                                                                                                                        |

---

## 4. Cross-cutting layers

| FIR                                                                    | Treatment           | What PACK-15 does                                                                                                                                                                                                                                                                                             |
| ---------------------------------------------------------------------- | ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `FIR-FORM-001` Canonical forms framework                               | partially addressed | Nine forms specified with versioning, declarations, submission binding and receipts; the framework itself remains a future foundation PACK                                                                                                                                                                    |
| `FIR-FORM-002` Domain forms inventory                                  | addressed **for this domain** | All seven required documents produced, plus the coverage statement                                                                                                                                                                                                                                  |
| `FIR-FORM-003` Initial catalogue                                       | partially addressed | PACK-15's own forms are specified; the cross-domain catalogue remains future                                                                                                                                                                                                                                 |
| `FIR-FORM-004` Governed content and language                           | partially addressed | Real German texts with owner, version and effective date; the governed content store is future                                                                                                                                                                                                                |
| `FIR-FORM-005` Multi-channel renditions                                | partially addressed | Web, mobile, accessible, print, PDF and receipt specified; none implemented                                                                                                                                                                                                                                   |
| `FIR-RULE-001` Governed rules registry                                 | deferred            | Eligibility rule-sets are exactly what belongs there; PACK-15 records the dependency and specifies freeze semantics in the meantime                                                                                                                                                                            |
| `FIR-REF-001` Reference data and taxonomy                              | deferred            | Context types, participation classes, credential types and reason codes are taxonomy candidates                                                                                                                                                                                                              |
| `FIR-DELIVERY-001` Official delivery evidence                          | partially addressed | Nine notification classes and the channel prohibitions specified; delivery evidence is that entry's own round                                                                                                                                                                                                 |
| `FIR-TRUST-001` Signature and trusted timestamp                        | partially addressed | The cryptographic boundary is divided by function with separate keys and trust roots; no scheme is selected and no signature claim is made                                                                                                                                                                    |
| `FIR-REPRESENT-001` Representation and mandate                         | partially addressed | Assisted channels preserve actor/principal separation with helper attribution and no impersonation; no mandate model is built, and **representation may not extend to casting a ballot**                                                                                                                      |
| `FIR-INCLUSION-001` Assisted and alternative channels                  | partially addressed | Assisted eligibility review, in-person confirmation, assisted delivery, accessibility support and an offline fallback are specified, with the hard limit that assistance never reveals or controls a choice                                                                                                     |
| `FIR-QUALITY-001` Data quality and reconciliation                      | deferred            | Source-staleness handling is specified; the reconciliation framework is future — and PACK-15 adds that no reconciliation may span the boundary                                                                                                                                                                |
| `FIR-CONFIG-001` Governed operational configuration                    | deferred            | Windows, cutoffs, thresholds, cohort sizes and expiries are governed configuration, not constants                                                                                                                                                                                                              |
| `FIR-IMPORT-001` Legacy import                                         | unchanged           | —                                                                                                                                                                                                                                                                                                             |
| `FIR-SERVICE-001` Service catalogue                                    | deferred            | Six bounded contexts are named with owners; the catalogue entry remains future                                                                                                                                                                                                                                |
| `FIR-SEARCH-001` … `FIR-SEARCH-003`                                    | partially addressed | By exclusion: **no search surface over eligibility cases, credentials or participation is created**, and none may be                                                                                                                                                                                          |
| `FIR-COMM-002` Neutral sensitive notifications                         | partially addressed | Voting notifications are specified neutrally; no message states a person-level voting status                                                                                                                                                                                                                  |
| `FIR-COMM-003` Communication identity-minimization                     | unchanged           | The persona is excluded from every PACK-15 artifact, which is a precondition, not an implementation                                                                                                                                                                                                           |
| `FIR-METRIC-001`, `FIR-METRIC-002`                                     | partially addressed | Operational metrics are constrained by the intermediate-tally prohibition and joint disclosure control                                                                                                                                                                                                        |
| `FIR-UX-003` … `FIR-UX-010`                                            | partially addressed | The FRONT-00/FRONT-01 baseline is inventoried and treated as authoritative; patterns are classified reuse/extend/new; nothing is built                                                                                                                                                                        |
| `FIR-UX-011` Page specification and screen content governance          | partially addressed | PACK-15 supplies the **domain side** only — process, authoritative data, permissions and assurance per action, forms, decisions, mandatory governed content and state semantics. It produces **none** of the ten artefacts and defines no page order, navigation model or screen structure. The complete first-page-to-final-page structure is defined during the relevant `FRONT-PACK Specification + UX/IA` stage, before frontend implementation |
| `FIR-ASM-006` Advance voting                                           | unchanged           | Named as a future consumer of this boundary; nothing here implements it                                                                                                                                                                                                                                       |
| `FIR-ASM-007` Closed confidential poll                                 | unchanged           | Same                                                                                                                                                                                                                                                                                                          |
| `FIR-CAND-001` Candidacy and nomination                                | unchanged           | `candidate_nomination` exists as a context type; the candidacy domain is untouched                                                                                                                                                                                                                            |
| `FIR-DEC-001` … `FIR-DEC-003`                                          | unchanged           | Decision recording consumes results; PACK-15 produces none                                                                                                                                                                                                                                                    |
| `FIR-PROG-003` Programme presentation                                  | unchanged           | —                                                                                                                                                                                                                                                                                                             |

---

## 5. Everything else

**Unchanged.** No other entry is touched by this round. In particular every
`FIR-FIN-*`, `FIR-PAY-*`, `FIR-INIT-*`, `FIR-GOV-*`, `FIR-REP-*`,
`FIR-SUPPORT-*`, `FIR-AI-*`, `FIR-DATA-*`, `FIR-DEL-*` and `FIR-MEM-*`
entry is untouched, and **no status anywhere is downgraded.**

---

## Summary

| Treatment           | Count |
| ------------------- | ----- |
| addressed           | 8     |
| partially addressed | 24    |
| deferred            | 6     |
| unchanged           | 15    |
| **implemented**     | **0** |

---

## 6. Register change and additions assessed by the architecture correction (2026-07-31)

### 6.1 The authoritative register changed

This matrix is now assessed against
**`EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER_UPDATED_V6.md`**, carried in
this archive at the canonical path
`docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md`. It supersedes
the register version carried in the pre-correction PACK-15 archive.

Verified before adoption: V6 is **purely additive** with respect to the
superseded copy — every prior entry is preserved byte-for-byte, no entry
was removed, reordered, reverted or restatused, and the only additions are
register §1.15 (the documentation-only round record for open-source
licensing) and register §29 with `FIR-OSS-001` … `FIR-OSS-006`. Entry count
141 → 147.

**There is one canonical register copy in this archive and no standalone
second copy.**

### 6.2 `FIR-OSS-001` … `FIR-OSS-006`

All six are `approved` in the register and **none is touched by this
round**. PACK-15 is a documentation-only specification round for a voting
trust boundary; it selects no licence, publishes no source, generates no
SBOM, accepts no contribution and makes no release.

| FIR            | Subject                                                          | Treatment     | Why                                                                                                       |
| -------------- | ---------------------------------------------------------------- | ------------- | --------------------------------------------------------------------------------------------------------- |
| `FIR-OSS-001`  | `EUPL-1.2` project licensing baseline                            | **unchanged** | No licence text, SPDX header, notice or package metadata is produced or changed by this round             |
| `FIR-OSS-002`  | Source availability for network-provided modified versions       | **unchanged** | This round deploys nothing and communicates nothing to the public                                          |
| `FIR-OSS-003`  | Third-party licence and dependency compliance                    | **unchanged** | No dependency is added, removed or vendored; no SBOM obligation is engaged                                 |
| `FIR-OSS-004`  | Contribution, copyright and provenance governance                | **unchanged** | No contribution workflow, CLA or DCO decision is made here                                                  |
| `FIR-OSS-005`  | Trademark, name and official-instance separation                 | **unchanged** | No naming, branding or official-instance claim is made                                                      |
| `FIR-OSS-006`  | Open verification, reproducible builds and public security process | **unchanged** | No release, signature, advisory or verification artefact is produced                                        |

**Nothing in this round may be read as licensing compliance, as a public
release, or as a claim that any `FIR-OSS-*` obligation is met.** The
register's own §29 boundaries apply and are not narrowed here: the entries
select an intended licence, do not complete legal licensing, do not change
`REPOSITORY_VERSION` and do not change `CANON_VERSION`.

### 6.3 One forward-looking note, recorded rather than acted on

`FIR-OSS-006` requires that public protocol and schema documentation, public
test suites and public verification tools accompany a future public
release, and that security through obscurity is not a primary control.
**This round is compatible with that requirement and depends on it**: the
separation architecture's guarantees are structural and are meant to be
checkable by an outside reader, which is why every prohibition here is
stated as a testable property rather than as an operational practice. No
obligation is discharged by saying so.

### 6.4 Treatments changed by the architecture correction

| FIR                | Before        | After                          | Why                                                                                          |
| ------------------ | ------------- | ------------------------------ | -------------------------------------------------------------------------------------------- |
| `FIR-CONFIG-001`   | deferred      | **partially addressed**        | The `IssuanceTimingProfile` is specified as governed configuration with ranges and hard lower bounds, rather than as constants |
| `FIR-INV-002`      | addressed for this boundary | unchanged in status, **strengthened** | Timing controls, pseudonym exclusion and the delivery boundary close named residual paths |
| `FIR-INV-011`      | partially addressed | unchanged in status, **strengthened** | Complementary suppression across cells and across bundles is now specified          |
| `FIR-ROLE-003`     | partially addressed | unchanged in status, **strengthened** | The auditor's bundle is now defined rather than deferred                             |
| `FIR-INCLUSION-001`| partially addressed | unchanged in status, **strengthened** | Assisted delivery now has a structural non-retention property rather than a declaration |

**No entry is upgraded to `implemented`, and none may be.**

### 6.5 Revised summary

| Treatment           | Count |
| ------------------- | ----- |
| addressed           | 8     |
| partially addressed | 25    |
| deferred            | 5     |
| unchanged           | 21    |
| **implemented**     | **0** |

The counts move by two: `FIR-CONFIG-001` from deferred to partially
addressed, and six `FIR-OSS-*` entries enter as unchanged.
