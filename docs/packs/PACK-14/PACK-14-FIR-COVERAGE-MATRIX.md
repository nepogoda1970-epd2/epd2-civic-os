# PACK-14 — FIR Coverage Matrix

> **Status, as of the PACK-14 FINAL PASS round (2026-07-30):**
> **PACK-14 EXTERNAL CI PASS · FINAL PASS ARCHIVE PREPARED ·
> `REPOSITORY_VERSION` `0.14.0` · `CANON_VERSION` `0.8.0` ·
> NOT PRODUCTION READY · NOT LEGALLY ACTIVATED.** See
> `docs/handover/PACK-14-FINAL-PASS-REPORT.md`.
>
> The header below records the **specification** round that wrote this
> matrix and is retained unchanged. The implementation round has since
> happened and the external pipeline has now run and passed. That changes
> the _round's_ status; it does not retroactively meet a criterion whose
> evidence is a bound WebAuthn library, a bound password hasher, a bound
> breached-password corpus, a deployed database, a selected identity
> provider or a rendered frontend, because a pipeline binds no provider
> and deploys nothing. The per-entry treatments are unchanged by the PASS, and
> `FIR-UX-011` and every other future obligation stay **future**.

**Round:** PACK-14 — specification and ADR only. **No code. Not implemented. Not a candidate. Not a PASS.**
**Repository version:** unchanged at `0.13.0` · **Canon version:** unchanged at `0.8.0`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**
**Architecture correction applied (2026-07-30).**

**No FIR entry is marked `implemented` by this round, and none may be.**
A specification round produces requirements rather than implementations.
Treatment values: **addressed** (fully specified), **partially addressed**
(specified in part, remainder named), **deferred** (recorded as a
dependency owned by a later pack), **unchanged** (untouched by PACK-14).

---

## 1. Roadmap

| FIR               | Status before | Treatment | References              | Implementation-stage obligation                                                                                                       |
| ----------------- | ------------- | --------- | ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| `FIR-ROADMAP-004` | `approved`    | addressed | whole pack; ADR-079…088 | Build the identity, authentication and session architecture; satisfy every PASS-blocking criterion; only then propose a status change |

`FIR-ROADMAP-004` MUST NOT move past `scheduled` or `under_review` on the
strength of this round.

## 2. Hard invariants

| FIR                                               | Status before                   | Treatment           | References                                          | Implementation-stage obligation                                                                                |
| ------------------------------------------------- | ------------------------------- | ------------------- | --------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| `FIR-INV-001` No global user ID                   | `approved`                      | addressed           | ADR-079; identity separation matrix; AC-P14-001…005 | Enforce structurally: scoped actor references, prohibited-key scans, governed mapping boundaries               |
| `FIR-INV-002` Identity/ballot unlinkability       | `approved`                      | partially addressed | ADR-088; AC-P14-046…050                             | PACK-14 supplies the identity-free handoff boundary; the credential protocol is PACK-15/16's                   |
| `FIR-INV-003` Voting Client isolation             | `approved`                      | partially addressed | cross-workspace matrix; ADR-088                     | PACK-14 issues no session for WS-03 and shares nothing with it; the client itself is PACK-15/16 and FRONT-PACK |
| `FIR-INV-004` Eligibility/credential separation   | `approved`                      | unchanged           | —                                                   | PACK-14 declares no eligibility and no credential in the voting sense                                          |
| `FIR-INV-005` No intermediate tally               | `approved`                      | unchanged           | —                                                   | Nothing here touches tally                                                                                     |
| `FIR-INV-006` Safe feature flags                  | `approved`                      | partially addressed | ADR-087; AC-P14-071…076                             | No flag may disable an assurance requirement, a step-up, an audit obligation or a separation of duties         |
| `FIR-INV-007` DLP and controlled export           | `approved`                      | unchanged           | —                                                   | PACK-12 owns it; PACK-14 adds no export surface                                                                |
| `FIR-INV-008` Security/System Admin separation    | `approved`                      | addressed           | ADR-087                                             | Enforce at the act, reusing PACK-12's mechanism                                                                |
| `FIR-INV-009` JIT and break-glass governance      | `approved`                      | addressed           | ADR-087; AC-P14-075                                 | Reuse PACK-12; add no second mechanism                                                                         |
| `FIR-INV-010` Document version integrity          | `implemented in reference form` | unchanged           | —                                                   | Proofing and recovery evidence use PACK-11 as-is                                                               |
| `FIR-INV-011` Statistical disclosure control      | `approved`                      | unchanged           | —                                                   | PACK-12 owns it                                                                                                |
| `FIR-INV-012` Accessibility as definition of done | `approved`                      | partially addressed | AC-P14-091…095                                      | Every identity surface must satisfy it; FRONT-PACK builds them                                                 |
| `FIR-INV-013` Bund/Land/Kreis isolation           | `approved`                      | partially addressed | mapping boundary; AC-P14-005                        | Organizational scope is mandatory on every mapping and every scoped reference                                  |
| `FIR-INV-014` No universal administration         | `approved`                      | addressed           | ADR-087; AC-P14-071                                 | No identity console may be built                                                                               |
| `FIR-INV-015` No false production claims          | `approved`                      | addressed           | every status banner; AC-P14-103                     | Keep the banners honest through implementation                                                                 |

## 3. Identity, account and communication

| FIR                                                | Treatment           | Note                                                                                                        |
| -------------------------------------------------- | ------------------- | ----------------------------------------------------------------------------------------------------------- |
| `FIR-ID-001`                                       | partially addressed | The account and session model is specified here; the member cabinet surface is not                          |
| `FIR-ID-002`                                       | partially addressed | Identity and session model specified; the identity-minimization profile for communication remains PACK-18's |
| `FIR-COMM-003` Communication identity-minimization | unchanged           | The persona is excluded from authentication here, which is a precondition, not an implementation            |
| `FIR-COMM-004`                                     | unchanged           | —                                                                                                           |

## 4. Cross-cutting layers introduced by the PACK-13 register addenda

| FIR                                                                    | Treatment                     | What PACK-14 does                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| ---------------------------------------------------------------------- | ----------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `FIR-FORM-001` Canonical forms framework                               | partially addressed           | Fifteen forms specified with versioning, declarations, submission binding and receipts; the framework itself is a future foundation PACK                                                                                                                                                                                                                                                                                                                                                |
| `FIR-FORM-002` Domain forms inventory                                  | addressed **for this domain** | All seven required documents produced, plus the mandatory coverage section in the acceptance matrix                                                                                                                                                                                                                                                                                                                                                                                     |
| `FIR-FORM-003` Initial catalogue                                       | partially addressed           | PACK-14's own forms are specified; the cross-domain catalogue remains future                                                                                                                                                                                                                                                                                                                                                                                                            |
| `FIR-FORM-004` Governed content and language                           | partially addressed           | Real German texts produced with owner, version and effective-date fields; the governed content store is future                                                                                                                                                                                                                                                                                                                                                                          |
| `FIR-FORM-005` Multi-channel renditions                                | partially addressed           | Web, mobile, accessible, print, PDF and receipt specified; none implemented                                                                                                                                                                                                                                                                                                                                                                                                             |
| `FIR-RULE-001` Governed rules registry                                 | deferred                      | Assurance and step-up policy is exactly the kind of rule that belongs there; PACK-14 records the dependency                                                                                                                                                                                                                                                                                                                                                                             |
| `FIR-REF-001` Reference data and taxonomy                              | deferred                      | Method classes, factor classes, proofing levels and reason codes are taxonomy candidates                                                                                                                                                                                                                                                                                                                                                                                                |
| `FIR-DELIVERY-001` Official delivery evidence                          | partially addressed           | Notification classes and channel rules specified; delivery evidence is that entry's own round                                                                                                                                                                                                                                                                                                                                                                                           |
| `FIR-TRUST-001` Signature and trusted timestamp                        | partially addressed           | The boundary is drawn — authentication is **not** a signature — and nothing more is claimed                                                                                                                                                                                                                                                                                                                                                                                             |
| `FIR-REPRESENT-001` Representation and mandate                         | partially addressed           | actor/principal/beneficiary/authority distinction preserved; no mandate model built                                                                                                                                                                                                                                                                                                                                                                                                     |
| `FIR-INCLUSION-001` Assisted and alternative channels                  | partially addressed           | Assisted registration, assisted recovery, offline proofing and in-person fallback specified with helper attribution and no impersonation                                                                                                                                                                                                                                                                                                                                                |
| `FIR-QUALITY-001` Data quality and reconciliation                      | deferred                      | Duplicate-account review is a reconciliation case; the framework is future                                                                                                                                                                                                                                                                                                                                                                                                              |
| `FIR-CONFIG-001` Governed operational configuration                    | deferred                      | Timeouts, windows and thresholds are governed configuration, not constants                                                                                                                                                                                                                                                                                                                                                                                                              |
| `FIR-IMPORT-001` Legacy import                                         | deferred                      | Importing existing member records without creating a global ID is a named future problem                                                                                                                                                                                                                                                                                                                                                                                                |
| `FIR-SERVICE-001` Service catalogue                                    | deferred                      | —                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| `FIR-UX-003` … `FIR-UX-010` Frontend design and interaction governance | partially addressed           | The existing FRONT-00/FRONT-01 baseline is inventoried and treated as authoritative; surfaces are specified, none built                                                                                                                                                                                                                                                                                                                                                                 |
| `FIR-UX-011` Page specification and screen content governance          | partially addressed           | PACK-14 supplies the **domain side** of the responsibility split — process, authoritative data, permissions and assurance per action, forms, decisions, mandatory governed content and state semantics. It produces **none** of the ten `FIR-UX-011` artefacts and defines no page order, navigation model or screen structure. The complete first-page-to-final-page structure is defined during the relevant `FRONT-PACK Specification + UX/IA` stage, before frontend implementation |
| `FIR-PROG-003` Programme presentation                                  | unchanged                     | Untouched; remains an approved future frontend obligation                                                                                                                                                                                                                                                                                                                                                                                                                               |

## 5. Everything else

**Unchanged.** No other entry is touched by this round. In particular every
`FIR-FIN-*`, `FIR-ASM-*`, `FIR-DEC-*`, `FIR-INIT-*`, `FIR-PAY-*`,
`FIR-GOV-*`, `FIR-REP-*`, `FIR-SEARCH-*`, `FIR-SUPPORT-*` and
`FIR-METRIC-*` entry is untouched, and no status anywhere is downgraded.

**New FIR identifiers created by this round: none.**

---

## Summary

| Treatment           | Count |
| ------------------- | ----- |
| addressed           | 9     |
| partially addressed | 19    |
| deferred            | 6     |
| unchanged           | 8     |
| **implemented**     | **0** |
