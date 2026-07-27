# FRONT-01 Audit Correction Matrix

## Conditions C1–C8

| Condition | Implementation evidence                                                                           |
| --------- | ------------------------------------------------------------------------------------------------- |
| C1        | `/status` states PACK-09 FINAL PASS; tests prohibit stale CANDIDATE-2 wording.                    |
| C2        | Public copy and route-specific guards implement WC-01–23 and FEC-001–020 as mapped below.         |
| C3        | Every page has a controlled maturity banner; prototype/specification is not described as runtime. |
| C4        | `/compliance` says PACK-09 backend PASS while WS-07 UI is missing; no case or notice UI exists.   |
| C5        | `/abstimmungen` is explanation-only; WS-03 has its own origin and no shared session/storage.      |
| C6        | `/finanzen` states PACK-10 is specification/canon only and exposes no financial form.             |
| C7        | `/status` identifies PACK-19–35 and Domains 51–58 as planned/proposed unless separately proven.   |
| C8        | No production, legal-validity or cryptographic-readiness claim is made.                           |

## WC-01–WC-23

| IDs                 | Evidence                                                                                                      |
| ------------------- | ------------------------------------------------------------------------------------------------------------- |
| WC-01, WC-18, WC-19 | Shared status banner, one navigation family, future concepts below active information.                        |
| WC-02               | Crisis workflow removed from active navigation; no automatic legal effect.                                    |
| WC-03, WC-16        | `/technologie`, `/sicherheit`, `/abstimmungen`: conditional language; eID/crypto are not legal proof.         |
| WC-04, WC-05, WC-21 | `/abgeordnetentisch`: protected WS-04, sanitized projections and free-mandate safeguard.                      |
| WC-06               | Individual reputation display removed; legacy page is `REMOVE`.                                               |
| WC-07, WC-08, WC-22 | `/beratung`, `/initiativen`, `/programm`: snapshot AI; vote, adoption and immutable publication are separate. |
| WC-09               | `/buergerbuero`: planned PACK-33 routing semantics without live case/SLA.                                     |
| WC-10               | `/kontakt`: message receipt/read is not legal effect; operational communication moved to future workspace.    |
| WC-11               | `/versammlungen`: attendance, quorum and voting eligibility separated; legally blocked.                       |
| WC-12               | `/kandidatur`: all candidacy stages are distinct.                                                             |
| WC-13, WC-23        | Lobbying legacy maps to governed transparency explanation; source and rendition separated.                    |
| WC-14               | `/rechtsgovernance`: proposed institution, scope and binding effect require formal basis.                     |
| WC-15               | `/transparenz`: review, redaction, approval, projection, correction/supersession.                             |
| WC-17               | `/datenschutz`: purpose-specific notices required before future forms.                                        |
| WC-20               | Internal dashboards are not migrated; no person-like sample record appears in WS-01.                          |

## FEC-001–FEC-020

| IDs              | Evidence                                                                                        |
| ---------------- | ----------------------------------------------------------------------------------------------- |
| FEC-001          | `/abstimmungen` lists separate origin, scoped handoff, and no shared cookies/storage/analytics. |
| FEC-002, FEC-003 | Security and crisis overclaims removed or converted to conditional concepts.                    |
| FEC-004, FEC-005 | No imperative mandate or public individual reputation score.                                    |
| FEC-006          | `/mitgliedschaft` says login is a handoff; no global session.                                   |
| FEC-007          | `/buergerbuero` belongs to PACK-33 and future WS-05.                                            |
| FEC-008          | `/beratung` defines snapshot-bound advisory AI with citations/version/staleness/contestability. |
| FEC-009, FEC-019 | `/transparenz` consumes only approved projections; no operational DB access.                    |
| FEC-010, FEC-016 | Protected pages are not shipped as WS-01 tools; universal admin remains forbidden.              |
| FEC-011          | Organisation/candidacy are informational and require approved renditions.                       |
| FEC-012          | Public contact is not an official-notice workflow.                                              |
| FEC-013          | `/versammlungen` separates participation, quorum and authority.                                 |
| FEC-014, FEC-015 | Lobby/representative records are protected; only approved summaries may be public.              |
| FEC-017, FEC-018 | FRONT-00 accessible components retained; controlled unavailable/blocked statuses are visible.   |
| FEC-020          | `/status` contains corrected PACK maturity language, including PACK-09 FINAL PASS.              |
