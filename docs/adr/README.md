# Architecture Decision Records (ADR)

FRONT-00 adds Proposed ADR-044 through ADR-047. They are not accepted and do not
change canon 0.7.0.

Любое отклонение от канона (`docs/canonical/TZ-00-domain-event-canon.md`)
или от утверждённой архитектуры оформляется как ADR.

- Шаблон: `ADR-000-template.md`.
- ADR нумеруются последовательно: `ADR-001`, `ADR-002`, ...
- До статуса `accepted` предложенное изменение **не** включается в рабочий
  код.
- Действующая версия канона: **`0.8.0`**
  (`docs/canonical/canon-version.json`), с 2026-07-27 (ADR-054,
  **`proposed`** — канон-кандидат PACK-10, раздел 19f). Предыдущая
  действующая версия — `0.7.0`, с 2026-07-25 (ADR-037, `accepted`).

## Статусы ADR

- `proposed`
- `under_review`
- `accepted`
- `rejected`
- `superseded`
- `implemented`

## Список ADR

| ADR                                                                                      | Тема                                                                                                                                                                                                                                                                                                                                                                                         | Статус                                                                                                                                |
| ---------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| [ADR-001](./ADR-001-repository-strategy.md)                                              | Use a modular monorepo for the initial development stage                                                                                                                                                                                                                                                                                                                                     | accepted                                                                                                                              |
| [ADR-002](./ADR-002-identity-participation-separation.md)                                | Identity/participation separation and canonical event/name resolution                                                                                                                                                                                                                                                                                                                        | accepted                                                                                                                              |
| [ADR-003](./ADR-003-append-only-audit-hash-chain.md)                                     | Append-only Audit Core with sequential hash chaining                                                                                                                                                                                                                                                                                                                                         | accepted                                                                                                                              |
| [ADR-004](./ADR-004-reason-code-registry.md)                                             | Centralized PACK-02 reason-code registry and additive codes                                                                                                                                                                                                                                                                                                                                  | accepted                                                                                                                              |
| [ADR-005](./ADR-005-pack-03-service-decomposition.md)                                    | PACK-03 service decomposition (Participation and Decision Kernel)                                                                                                                                                                                                                                                                                                                            | accepted                                                                                                                              |
| [ADR-006](./ADR-006-pack-03-reason-code-additions.md)                                    | PACK-03 reason-code registry and additive codes                                                                                                                                                                                                                                                                                                                                              | accepted                                                                                                                              |
| ADR-007                                                                                  | reserved — not used by this governance round                                                                                                                                                                                                                                                                                                                                                 | —                                                                                                                                     |
| [ADR-008](./ADR-008-pack-03-pack-02-integration-boundary.md)                             | PACK-03 to PACK-02 integration boundary                                                                                                                                                                                                                                                                                                                                                      | accepted                                                                                                                              |
| [ADR-009](./ADR-009-voting-delegation-quorum-defaults.md)                                | Voting, delegation, quorum, tie, challenge, and finality defaults                                                                                                                                                                                                                                                                                                                            | accepted (amended: items 13, 14)                                                                                                      |
| [ADR-010](./ADR-010-ballot-challenge-window-canon-addition.md)                           | Canon minor-version addition: Ballot challenge window / ResultPublication finality                                                                                                                                                                                                                                                                                                           | accepted (amended: finality wording)                                                                                                  |
| [ADR-011](./ADR-011-pack-04-transparency-service-decomposition.md)                       | PACK-04 Transparency service decomposition                                                                                                                                                                                                                                                                                                                                                   | accepted                                                                                                                              |
| [ADR-012](./ADR-012-pack-04-cross-pack-read-boundary.md)                                 | PACK-04 cross-pack read boundary and dependency matrix                                                                                                                                                                                                                                                                                                                                       | accepted                                                                                                                              |
| [ADR-013](./ADR-013-canon-0.3.0-transparency-context-additions.md)                       | Canon minor-version addition: Transparency Context entities, events, ownership (`0.2.0 → 0.3.0`, implemented 2026-07-23)                                                                                                                                                                                                                                                                     | accepted (amended: proof semantics, DisclosurePolicy field model, correction semantics, role references)                              |
| [ADR-014](./ADR-014-pack-04-reason-code-additions.md)                                    | PACK-04 reason-code registry and additive codes                                                                                                                                                                                                                                                                                                                                              | accepted                                                                                                                              |
| [ADR-015](./ADR-015-disclosure-redaction-lobby-log-defaults.md)                          | Disclosure, redaction, public audit export, and Lobby Log defaults                                                                                                                                                                                                                                                                                                                           | accepted (amended: Lobby Log timing, reviewer identity, small-cell threshold, audit-proof semantics)                                  |
| [ADR-016](./ADR-016-pack-05-governance-service-decomposition.md)                         | PACK-05 Governance service decomposition                                                                                                                                                                                                                                                                                                                                                     | accepted                                                                                                                              |
| [ADR-017](./ADR-017-pack-05-cross-pack-boundary.md)                                      | PACK-05 cross-pack boundary — reads, and the ballot/result write question                                                                                                                                                                                                                                                                                                                    | accepted                                                                                                                              |
| [ADR-018](./ADR-018-canon-0.4.0-governance-context-additions.md)                         | Canon minor-version addition: Governance Context entities, events, ownership (`0.3.0 → 0.4.0`, implemented 2026-07-23)                                                                                                                                                                                                                                                                       | accepted (amended: TechnicalChallenge submitter authorization, finality_outcome/FinalityStatus split, GovernanceDecision status enum) |
| [ADR-019](./ADR-019-pack-05-reason-code-additions.md)                                    | PACK-05 reason-code registry and additive codes                                                                                                                                                                                                                                                                                                                                              | accepted                                                                                                                              |
| [ADR-020](./ADR-020-pack-05-authority-roles-challenge-lifecycle.md)                      | PACK-05 authority, roles, and challenge-lifecycle defaults                                                                                                                                                                                                                                                                                                                                   | accepted (amended: challenge-submission alignment, bootstrap mechanism fully specified)                                               |
| [ADR-021](./ADR-021-pack-06-ai-processing-service-decomposition.md)                      | PACK-06 AI Processing service decomposition                                                                                                                                                                                                                                                                                                                                                  | accepted                                                                                                                              |
| [ADR-022](./ADR-022-pack-06-cross-pack-boundary.md)                                      | PACK-06 cross-pack boundary — one narrow read into `governance-service` for reviewer verification                                                                                                                                                                                                                                                                                            | accepted (amended: `verify_role_assignment_for_action` replaces local reviewer-check logic)                                           |
| [ADR-023](./ADR-023-canon-0.5.0-ai-processing-context-additions.md)                      | Canon minor-version addition: `AIProcessingRecord` field/status/event extensions (`0.4.0 → 0.5.0`, implemented 2026-07-24)                                                                                                                                                                                                                                                                   | accepted (amended: `RedactionManifest` canonicalized, disclosure-lifecycle fields and `DisclosureStatus` added)                       |
| [ADR-024](./ADR-024-pack-06-reason-code-additions.md)                                    | PACK-06 reason-code registry and additive codes                                                                                                                                                                                                                                                                                                                                              | accepted                                                                                                                              |
| [ADR-025](./ADR-025-pack-06-use-policy-redaction-providers-disclosure.md)                | PACK-06 use-class policy, redaction enforcement, providers, and mandatory disclosure                                                                                                                                                                                                                                                                                                         | accepted (amended: explicit five-step `AIDisclosurePackage` disclosure protocol replaces informal orchestration rule)                 |
| [ADR-026](./ADR-026-pack-07-service-decomposition-policy-separation.md)                  | PACK-07 service decomposition — `eligibility-service`/`membership-service` split and participant/party-membership policy separation                                                                                                                                                                                                                                                          | proposed                                                                                                                              |
| [ADR-027](./ADR-027-pack-07-cross-service-boundaries.md)                                 | PACK-07 cross-service boundaries — narrow reads between `membership-service`, `eligibility-service`, `identity-service`, `governance-service`                                                                                                                                                                                                                                                | proposed                                                                                                                              |
| [ADR-028](./ADR-028-canon-0.6.0-participation-membership-context-additions.md)           | Canon minor-version addition (proposed): Participation and Membership Policy context — electoral-eligibility claims, two-stage admission, membership privacy (`0.5.0 → 0.6.0`, not yet implemented)                                                                                                                                                                                          | proposed                                                                                                                              |
| [ADR-029](./ADR-029-pack-07-reason-code-additions.md)                                    | PACK-07 reason-code registry and additive codes                                                                                                                                                                                                                                                                                                                                              | proposed                                                                                                                              |
| [ADR-030](./ADR-030-pack-07-policy-mechanics-human-decisions.md)                         | PACK-07 policy mechanics, `MembershipApplication` lifecycle, consequential human decisions, and appeal-model resolution                                                                                                                                                                                                                                                                      | proposed                                                                                                                              |
| [ADR-031](./ADR-031-pack-07-security-architecture-anti-correlation-protocol-agility.md)  | PACK-07 security architecture — domain pseudonyms, anti-correlation invariant, Credential Issuer boundary, cryptographic-protocol agility, audit/queue properties, future-pack boundaries                                                                                                                                                                                                    | proposed                                                                                                                              |
| [ADR-032](./ADR-032-organization-and-civic-space-ownership.md)                           | PACK-08 Organization and CivicSpace ownership — new `organization-service`, narrow-read boundary for every other service                                                                                                                                                                                                                                                                     | accepted                                                                                                                              |
| [ADR-033](./ADR-033-organizational-relationships-effective-dating-and-reorganization.md) | PACK-08 organizational relationships, effective dating, and reorganization — multiple typed relationship graphs (hierarchy/continuity/cooperation), not a strict tree                                                                                                                                                                                                                        | accepted                                                                                                                              |
| [ADR-034](./ADR-034-regional-scope-authorization-and-inheritance.md)                     | PACK-08 regional scope authorization and inheritance — default-deny, six explicit access modes, anti-confused-deputy/anti-role-name-as-proof                                                                                                                                                                                                                                                 | accepted                                                                                                                              |
| [ADR-035](./ADR-035-cross-domain-scope-classification-and-migration.md)                  | PACK-08 cross-domain scope classification and migration — field-by-field decision for `organization_id`/`region_code`/`jurisdiction`/`scope_type`/`scope_id`, no automated bulk rewrite                                                                                                                                                                                                      | accepted                                                                                                                              |
| [ADR-036](./ADR-036-institutional-authority-assignments-and-non-combinable-roles.md)     | PACK-08 institutional authority assignments and non-combinable roles — new `OrganizationalAuthority` entity, role-lifecycle invariants, no-implicit-transfer rule                                                                                                                                                                                                                            | accepted                                                                                                                              |
| [ADR-037](./ADR-037-organization-and-regional-scope-canon-amendment.md)                  | Organization and Regional Scope Canon Amendment — canon minor-version addition: new section 19e (`0.6.0 → 0.7.0`, implemented 2026-07-25)                                                                                                                                                                                                                                                    | accepted                                                                                                                              |
| [ADR-038](./ADR-038-pack-09-compliance-service-decomposition.md)                         | PACK-09 compliance-service decomposition — one new bounded service for records governance and legal workflows, importing only `epd2_core` and `epd2_audit_core` (amended: Framework 0.8.1 additions, `references.py` outward interface)                                                                                                                                                      | accepted                                                                                                                              |
| [ADR-039](./ADR-039-record-retention-and-legal-hold.md)                                  | PACK-09 record retention and Legal Hold — separate authorization from execution, destruction evidence, hold beats schedule (amended: `RecordClass`, hold propagation to derivatives)                                                                                                                                                                                                         | accepted                                                                                                                              |
| [ADR-040](./ADR-040-processing-registry-and-data-catalog.md)                             | PACK-09 processing registry and data catalog — versioned processing activities, recorded legal basis (amended: DPIA activation gate that fails closed on absence)                                                                                                                                                                                                                            | accepted                                                                                                                              |
| [ADR-041](./ADR-041-governed-procedural-cases-and-deadlines.md)                          | PACK-09 governed procedural cases and deadlines — deadline state derived from an append-only history, never stored (amended: common legal-case substrate, immutable docket, three decision statuses)                                                                                                                                                                                         | accepted                                                                                                                              |
| [ADR-042](./ADR-042-party-arbitration-independence.md)                                   | PACK-09 party arbitration independence — the decision-maker may not be a party, a handler or conflicted (amended: due-process prerequisites, recusal hooks, no AI decision)                                                                                                                                                                                                                  | accepted                                                                                                                              |
| [ADR-043](./ADR-043-official-notice-legal-effect-trust-boundary.md)                      | Official notice, service telemetry and legal effect as three separate objects — only a governed `NoticeEffectDecision` may start a procedural deadline (Framework 0.8.1 hard invariants 39/40/57/59/60)                                                                                                                                                                                      | accepted                                                                                                                              |
| [ADR-048](./ADR-048-pack-10-finance-service-decomposition.md)                            | PACK-10 finance domain service decomposition — one bounded context `services/finance-service` with explicitly separated internal modules, importing only `epd2_core` and `epd2_audit_core`                                                                                                                                                                                                   | proposed                                                                                                                              |
| [ADR-049](./ADR-049-authoritative-finance-ledger-and-correction-model.md)                | Authoritative finance ledger, balanced posting and correction model — layered: the double-entry ledger is authoritative for monetary effect, the transaction register for the business fact and its provenance; integer minor units; posted entries immutable; period lock and controlled reopening                                                                                          | proposed                                                                                                                              |
| [ADR-050](./ADR-050-purpose-scoped-financial-party-references-and-aggregation.md)        | Purpose-scoped financial party references and lawful aggregation without a global user ID — opaque handles per (perimeter, purpose, policy version), a governed matching act, restricted resolution, and no claim that pseudonymization creates anonymity                                                                                                                                    | proposed                                                                                                                              |
| [ADR-051](./ADR-051-rechenschaftsbericht-lifecycle-snapshot-and-authority-semantics.md)  | `Rechenschaftsbericht` lifecycle, source snapshot and authority semantics — ten states, create-once snapshot, submission ≠ acceptance (only a PACK-09 `NoticeEffectDecision` reaches `accepted_by_authority`), publication ≠ approval, append-only versions                                                                                                                                  | proposed                                                                                                                              |
| [ADR-052](./ADR-052-finance-authority-separation-and-independent-audit.md)               | Finance authority separation, incompatible roles and independent finance audit — four new institutional roles, five action-level separations, the extended non-combinable-role matrix PACK-08 section 9.3 explicitly reserved, create-once `AuditConclusion`                                                                                                                                 | proposed                                                                                                                              |
| [ADR-053](./ADR-053-pack-10-pack-09-pack-11-pack-35-boundaries.md)                       | PACK-10 / PACK-09 / PACK-11 / PACK-35 ownership boundaries — the decidable financial-value versus influence-relationship test, reference-only PACK-09 integration, placeholder-only PACK-11 integration, and the `FinanceEvidenceRef` determination                                                                                                                                          | proposed                                                                                                                              |
| [ADR-054](./ADR-054-canon-0.8.0-party-finance-context-additions.md)                      | Canon minor-version addition: Party Finance & Financial Accountability Context (`0.7.0 → 0.8.0`) — new section 19f, the `ФИН-01`–`ФИН-45` invariant register, four new institutional role codes, `FinancePartyHandle`, the twelve-state `Rechenschaftsbericht` lifecycle, section 20.17 (72 events), 21 section-22 ownership rows, 25 section-23 forbidden links, 45 section-24 reason codes | proposed                                                                                                                              |
| [ADR-055](./ADR-055-pack-11-document-service-decomposition.md)                           | PACK-11 decomposition: one wholly new `document-service` in thirteen modules, and a 71-entry reason-code registry with no canon-owned codes (canon section 24 registers none for documents)                                                                                                                                                                                                  | proposed                                                                                                                              |
| [ADR-056](./ADR-056-document-authority-separation-and-access.md)                         | Eight document roles, a symmetric incompatibility matrix re-checked at the moment of the act, per-act separation of duties, access profiles as ceilings, read-time independence, and no break-glass                                                                                                                                                                                          | proposed                                                                                                                              |
| [ADR-057](./ADR-057-immutable-document-versions-and-hash-linked-history.md)              | Immutable `DocumentVersion` and the SHA-256 hash-linked chain implementing `FIR-INV-010`; three independent defences; tamper _evidence_, not tamper resistance, stated as such                                                                                                                                                                                                               | proposed                                                                                                                              |
| [ADR-058](./ADR-058-evidence-provenance-custody-and-sealed-bundles.md)                   | Evidence as a governed _use_ of an exact version; custody verified as a continuous chain; sealed, order-sensitive, citable evidence bundles                                                                                                                                                                                                                                                  | proposed                                                                                                                              |
| [ADR-059](./ADR-059-governed-determinations-not-inferred.md)                             | Signature and admissibility determinations are recorded, never computed; absence is an explicit value; staleness is structural — closing ADR-053's four PACK-11 interface requirements                                                                                                                                                                                                       | proposed                                                                                                                              |
| [ADR-060](./ADR-060-document-publication-separation-and-projection-surface.md)           | Publication separated from approval by a third authority; revoked publications become tombstones; one emission chokepoint; no projection carries content                                                                                                                                                                                                                                     | proposed                                                                                                                              |
| [ADR-061](./ADR-061-pack-12-privileged-role-separation.md)                               | Two institutional roles consumed and nine operational assignments introduced; PACK-08's pairwise baseline preserved and made stricter by fourteen pairs; a role is a ceiling, never a key                                                                                                                                                                                                    | proposed                                                                                                                              |
| [ADR-062](./ADR-062-pack-12-purpose-scoped-pam.md)                                       | Nine jointly-mandatory grant properties enforced at construction; no standing superuser expressible; separation of duties evaluated twice — at approval and again at activation                                                                                                                                                                                                              | proposed                                                                                                                              |
| [ADR-063](./ADR-063-pack-12-break-glass-dual-control.md)                                 | Emergency access as a separate workflow that only adds obligations; notification is part of the act; an undelivered notification escalates rather than passing silently; renewal is a new decision                                                                                                                                                                                           | proposed                                                                                                                              |
| [ADR-064](./ADR-064-pack-12-authorization-aware-search.md)                               | Two governed search modes and no third; investigation is a purpose, not a mode; source authorization re-resolved at result time; suppression reported as bands; cache keyed by the whole authorization context                                                                                                                                                                               | proposed                                                                                                                              |
| [ADR-065](./ADR-065-pack-12-high-confidentiality-index-exclusion.md)                     | A canonical source→tier classification mapping that fails closed; prohibited-tier material excluded from every index by two independent mechanisms; restricted tiers get no snippet                                                                                                                                                                                                          | proposed                                                                                                                              |
| [ADR-066](./ADR-066-pack-12-governed-data-export.md)                                     | Five distinct permissions, none substitutable for another; a closed recipient taxonomy with no generic `external`; permitted fields selected before generation, never stripped after; an export artifact is never authoritative                                                                                                                                                              | proposed                                                                                                                              |
| [ADR-067](./ADR-067-pack-12-dlp-and-disclosure-control.md)                               | Eighteen DLP controls with a named fail-closed subset; at least two independent disclosure rule families always active; a bounded cumulative-release model that fails closed when the release history is unavailable                                                                                                                                                                         | proposed                                                                                                                              |
| [ADR-068](./ADR-068-pack-12-privileged-session-evidence.md)                              | Sessions sealed into a hash-chained, tamper-**evident** record reusing PACK-11's evidence bundles; a distinct immutable sealed type with no mutator; no credential, token, user content, ballot material or export payload in the record                                                                                                                                                     | proposed                                                                                                                              |

ADR-061 through ADR-068 are this project's twelfth governance round —
the PACK-12 round (Privileged Administration, Authorization-Aware Search
& Governed Data Export, `FIR-ROADMAP-002`). Like the PACK-11 round and
unlike ADR-054, this round amends **no** canon: `CANON_VERSION` stays
`0.8.0` and `docs/canonical/TZ-00-domain-event-canon.md` is untouched.
Canon 19e.15 keeps `role_code` an open list extensible
"by configuration + ADR review", and canon 19e.16 fixes a _minimum_
pairwise incompatibility baseline that may be made stricter and never relaxed —
which is exactly what ADR-061 does. The nine roles PACK-12 adds are
privileged _operational assignments_, not institutional offices, so no
canon amendment follows from them; `docs/packs/PACK-12/PACK-12-CANON-ASSESSMENT.md`
records that verdict in full. The eight ADRs plus
`docs/packs/PACK-12/PACK-12-SPECIFICATION.md` are the normative record
for the model, because the context has no canon section of its own. All
eight are `proposed`.

PACK-12 reached **FINAL PASS** at repository version `0.12.0` on an
external GitHub Actions run; the ADRs' `proposed` status is unaffected by
that, exactly as ADR-055 through ADR-060 stayed `proposed` after PACK-11's
FINAL PASS. A green pipeline verifies the implementation, not the
governance status of the decision records. See
`docs/handover/PACK-12-FINAL-PASS-REPORT.md`.

ADR-055 through ADR-060 are this project's eleventh governance round —
the PACK-11 implementation round (Governed Documents & Evidence,
`FIR-ROADMAP-001`, `FIR-INV-010`). Unlike ADR-054, this round amends **no**
canon: `CANON_VERSION` stays `0.8.0` and
`docs/canonical/TZ-00-domain-event-canon.md` is untouched. Canon 19f.22
already assigns document bytes, authoritative versions, signatures,
cryptographic version chains, evidence content and chain of custody to
PACK-11; this round implements that assignment, and the six ADRs plus
`docs/packs/PACK-11-SPECIFICATION.md` are the normative record for the
model, because the context has no canon section of its own. All six are
`proposed`.

ADR-054 is this project's tenth governance round, the canon-amendment
round for CLAUDE-PACK-10. `CANON_VERSION` moves `0.7.0 → 0.8.0`: a new
canon section 19f ("Партийные финансы и финансовая отчётность / Party
Finance & Financial Accountability Context"), inserted between sections
19e and 20 by the established non-renumbering technique; a new section
20.17 with seventy-two finance events; twenty-one new section 22
ownership-matrix rows (owner `Finance Service`); twenty-five new section
23 forbidden-link entries; and forty-five new section 24 reason codes.
The section also carries a forty-five-rule finance-invariant register
(`ФИН-01` – `ФИН-45`), four new institutional `role_code` values
(`finance_administrator`, `payment_authorizer`, `payment_executor`,
`report_signatory`) extending 19e.15's open list together with the
extended 19e.16 incompatibility baseline — including the adopted owner
decision that `finance_administrator` is incompatible with
`organizational_administrator` in the same legally relevant scope — the
purpose-scoped `FinancePartyHandle`, the twelve-state
`Rechenschaftsbericht` lifecycle in which submission is neither
acknowledgement nor acceptance, governed effective-dated finance
policies, and safe public financial projections.

**Status: canon candidate, not accepted.** Unlike ADR-037, which was
`accepted` in the round that performed PACK-08's canon edit, ADR-054 is
`proposed`: the amended canon in this archive is submitted for review.
`REPOSITORY_VERSION` stays `0.9.0`, `canon-version.json` records
`finance_context_implementation_status = "not_implemented"`, and **no
`services/finance-service` directory, source file, schema, OpenAPI
operation, migration, frontend page or reason-code registry file was
created** — canon 19f.25 is the implementation gate, and implementation
requires ADR-048 – ADR-053 **and** this canon content, with neither
sufficient alone. Verification, exact commands and results:
`docs/handover/PACK-10-CANON-0.8.0-REPORT.md`; compatibility and the
registry diff: `docs/packs/PACK-10-CANON-0.8.0-COMPATIBILITY.md`;
acceptance evidence:
`docs/packs/PACK-10-CANON-0.8.0-ACCEPTANCE-MATRIX.md`.

ADR-048 through ADR-053 are this project's ninth governance round, the
specification/ADR round for CLAUDE-PACK-10 (Party Finance,
Rechenschaftsbericht & Financial External Influence,
`docs/packs/PACK-10-SPECIFICATION.md`), authored against the
`epd2-civic-os-PACK-09-IMPLEMENTATION-0.9.0-PASS` baseline. All six are
`proposed`; none is accepted, and **no PACK-10 code, service directory,
schema, OpenAPI file or reason-code registry file exists** — this round
is documentation only, and it changed neither `REPOSITORY_VERSION`
(`0.9.0`) nor `CANON_VERSION` (`0.7.0`).

Unlike PACK-09, PACK-10 **requires a canon amendment before
implementation**, and this round says so explicitly rather than leaving
it conditional: `docs/packs/PACK-10-CANON-AMENDMENT-ASSESSMENT.md`
records the determination concept by concept, and
`docs/packs/PACK-10-CANON-AMENDMENT-PROPOSAL.md` contains the proposed
addition — a new section 19f ("Партийные финансы и финансовая
отчётность / Party Finance & Financial Accountability Context") inserted
between 19e and 20 using the established non-renumbering technique, a
new section 20.17 event catalogue, new section 22 ownership rows, new
section 23 forbidden links and new section 24 reason codes, with
`CANON_VERSION` moving `0.7.0 → 0.8.0` in its own separate, dedicated
round. **That amendment has not been performed**; the canonical file is
byte-identical to the baseline's. Implementation of `finance-service`
therefore remains gated on two independent things — acceptance of these
six ADRs **and** the canon amendment landing — and is authorized by
neither alone, the same two-gate pattern ADR-032 through ADR-037
established for PACK-08.

The round's own report, including exactly what was and was not verified
locally, is `docs/handover/PACK-10-SPEC-REPORT.md`. Open owner, legal
and security questions are consolidated in
`docs/packs/PACK-10-OPEN-DECISIONS.md` (OD-1 through OD-22).

ADR-037 is this project's seventh governance round, the canon-amendment
round for CLAUDE-PACK-08 that ADR-032 through ADR-036's own acceptance
required before implementation. `CANON_VERSION` moved `0.6.0 → 0.7.0`:
new canon section 19e ("Организация и региональная авторизация —
расширение / Organization & Regional Scope Context"), inserted between
sections 19d and 20 (the established non-renumbering technique). Full
detail: `docs/handover/PACK-08-CANON-AMENDMENT-REPORT.md`,
`docs/canonical/PACK-08-GLOSSARY.md`. **No `services/organization-service`
directory, schema, OpenAPI file, or reason-code registry exists yet** —
implementation of `organization-service` itself remains a separate,
later task, gated on this canon content and on ADR-032 through ADR-036,
but not authorized by any of them alone.

**ADR-037's canon edit has been implemented in the canon itself**
(2026-07-25), in the same round as its own acceptance (unlike ADR-032
through ADR-036, whose acceptance deliberately deferred the canon edit
to this dedicated later task — the pattern ADR-010/013/018/020/023/025/028
each already established): canon section 19e extends `Organization`
(8.1) with six additive fields (`organization_profile`,
`parent_reference`, `effective_from`, `effective_until`, `dissolved_at`,
`successor_reference`); confirms `CivicSpace` (8.2) unchanged; defines
`OrganizationalUnit`, `OrganizationalRelation`,
`OrganizationalHierarchyOverlapPolicy`, `OrganizationalInheritancePolicy`,
and `OrganizationalAuthority` (all owned by `organization-service`) plus
the reusable `OrganizationalScope` value shape; canonizes multiple
typed directed graphs for organizational relationships, effective
dating, reorganization rules (with the hard no-automatic-rights-
transfer invariant), default-deny regional scope authorization (six
access modes), inheritance-policy ownership, the 90-day
temporary-supervision default, the institutional-role minimum
non-combinable-role baseline, role/authority lifecycle rules, extended
identity-minimization rules, and the six-category
`RoleAssignment.scope_id` classification requirement (8.4 itself
unchanged in fields/status/owner). Section 20.5 gains thirteen new
events with full payload/timing/audit/privacy documentation; section 22
gains five new ownership-matrix rows; section 23 gains new
forbidden-link entries; section 24 gains ten new reason codes.
`canon_version` moved `0.6.0 → 0.7.0`, mirrored across
`docs/canonical/canon-version.json`,
`packages/python/epd2-core/src/epd2_core/version.py`, and
`packages/typescript/epd2-types/src/version.ts`, with both
version-consistency unit tests updated and `scripts/verify_versions.py`
passing:

```text
sha256(docs/canonical/TZ-00-domain-event-canon.md) =
  a16341a66ce39514e6d8cd6d7a6dde8fc37b0430e3e9ddd7bfd284b116cb9072
CANON_VERSION = 0.7.0
```

This is a canon-only change: no `services/organization-service`
directory, JSON Schema, OpenAPI file, or reason-code registry was
created, and no PACK-01 through PACK-07 source code was touched.
Implementation of `organization-service` remains a separate, later
task, gated on this canon content but not authorized by it alone.

ADR-032 through ADR-036 are this project's sixth governance round, for
CLAUDE-PACK-08 (`docs/packs/PACK-08-SPECIFICATION.md`, Organization &
Regional Scope Foundation) — a specification/ADR round only, authorized
against the approved `MASTER-ARCHITECTURE-0.8.md`/`MASTER-ROADMAP-0.8.md`/
`HARD-INVARIANTS-0.8.md`/`ARCHITECTURE-GAP-REGISTER.md` planning
baseline and `PACK-08-PROPOSAL.md`. All five ADRs were drafted
`proposed` on 2026-07-25, then moved to **`accepted`** the same day in a
subsequent targeted correction round ("PACK-08 SPEC CORRECTION + OWNER
DECISIONS") once that round's owner decisions settled every core
architectural question each ADR raised — organizational graph model
(multiple typed directed graphs, not a strict tree), inheritance-policy
ownership, temporary-supervision maximum duration, a minimum
non-combinable-role baseline, `RoleAssignment.scope_id`'s six-category
classification, and `parent_reference`'s non-authoritative status.
**Every one of the five ADRs' own acceptance is explicitly qualified:
acceptance does not authorize implementation, and a canon amendment is
now confirmed as a mandatory precondition — not conditional — before
any PACK-08 implementation begins** (each ADR's own "Related canon
version" section restates this identically). No canon edit has been
performed at this stage (canon `0.6.0` is read and classified, never
amended; `CANON_VERSION` and the canon checksum are unchanged by both
the original round and the correction round). No service code, schema,
or contract file was created — see
`docs/handover/PACK-08-SPEC-REPORT.md` for the complete scope-discipline
statement and correction-round file list, and
`docs/packs/PACK-08-OPEN-DECISIONS.md` for the eighteen open decisions
(OD-1 through OD-18) this round surfaces — OD-5/OD-8/OD-10 closed,
OD-7/OD-11 partially closed, OD-18 closed definitively, the remainder
still open — for owner/legal/security review before any implementation
round is authorized.

ADR-026 through ADR-031 are this project's fifth governance round, for
CLAUDE-PACK-07 (`docs/handover/PACK-07-SPEC.md`, Participation & Membership
Policy) — see `docs/review/PACK-07-OWNER-DECISIONS.md` for the open
decision checklist. ADR-026 through ADR-030 were drafted `proposed` on
2026-07-24, with binding amendments the project owner had already
specified incorporated directly into each ADR's own Decision text (not
left as options to choose among) — the same drafting pattern
ADR-016–020 and ADR-021–025 each used. The project owner then issued
three further, mandatory amendment rounds the same day — (1) identity
verification is not citizenship, (2) process-specific electoral
eligibility via `ProcessEligibilityPolicy`, and (3) a strengthened
identity/session/anti-correlation architecture plus (4) an explicit
`decision_effect`/formal-confirmation model for digital processes — all
incorporated directly into ADR-027/028/030's own Decision text, with a
new, sixth ADR (**ADR-031**, `proposed`) recording the security-
architecture content (domain pseudonyms, anti-correlation invariant,
Credential Issuer boundary, cryptographic-protocol agility, audit/queue
properties, and three named future security packs) that falls outside
ADR-026–030's own participation/membership-policy scope. **No ADR has
been accepted yet. No canon edit has been performed. No
`services/membership-service` directory, schema, OpenAPI file, or
reason-code registry exists.** Canon remains byte-identical to the
PACK-06 PASS state:

```text
sha256(docs/canonical/TZ-00-domain-event-canon.md) =
  374b25fddfab88846622bf078b35c4246d8ad8c5d65bf43e6ac4e82653f74f74
CANON_VERSION = 0.5.0
```

ADR-021 through ADR-025 are this project's fourth governance round, for
CLAUDE-PACK-06 (`docs/handover/PACK-06-SPEC.md`, AI Processing Context)
— see `docs/review/PACK-06-OWNER-DECISIONS.md` for the resolved decision
record. **The project owner acted on all five drafted ADRs on
2026-07-24.** ADR-021 and ADR-024 were accepted exactly as proposed, no
amendments. ADR-022, ADR-023, and ADR-025 were accepted with amendments,
each fully incorporated into the ADR's own Decision text — see each
ADR's own "Owner decision" section for the exact amended text.
**ADR-023's (and, for its repository-side content, ADR-025's) canon edit
has now been implemented** (2026-07-24, as its own separate, dedicated
task, per that acceptance's own explicit deferral) — see the paragraph
below for the resulting canon 19c content and checksum. **No
`services/ai-processing-service` directory, schema, OpenAPI file, or
reason-code registry exists yet** — implementation of
`ai-processing-service` itself remains a separate, later task, gated on
these five accepted ADRs and on the canon content below, but not
authorized by either alone.

**ADR-023's canon edit has been implemented in the canon itself**
(2026-07-24), as its own separate, dedicated task following ADR-023's
(and ADR-025's) acceptance (this project's fourth canon-text edit, after
ADR-010's, ADR-013's, and ADR-018's): a new section 19c ("ИИ-обработка —
расширение / AI Processing Context") extends the already-canon-defined
`AIProcessingRecord` (17.1, twelve existing fields and six-value
`human_review_status` both unchanged) with a new, independent
`processing_status` field (six values, no stored `superseded`), a
unified `supersedes_ai_processing_record_id` field, fifteen further
model-governance/provenance/confidence/explainability/lifecycle fields,
a new canonical embedded `redaction_manifest` value object (nine
sub-fields), three disclosure-lifecycle fields plus a derived
`DisclosureStatus` read-model type, `AIDisclosurePackage` defined
explicitly as a contract/value object (never a canonical
system-of-record entity), and a mandatory five-step disclosure protocol
— including all of ADR-023's and ADR-025's own Owner-decision
amendments. Section 20.12's AI event catalog is corrected
(`ai.output.corrected` → `ai.output_corrected`) and gains six new
events; section 22's ownership matrix gains no new row
(`AIProcessingRecord`'s existing ownership is unchanged); section 23's
forbidden-links list gains new entries for the no-autonomous-decision,
no-identity-reverse-lookup, no-vote-linkage-reconstruction,
no-model-provider-mutation-authority, no-raw-private-input-in-
disclosure, and no-hidden-reasoning-claim invariants. `canon_version`
moved `0.4.0 → 0.5.0`, mirrored across
`docs/canonical/canon-version.json`,
`packages/python/epd2-core/src/epd2_core/version.py`, and
`packages/typescript/epd2-types/src/version.ts`, with both
version-consistency unit tests updated and `scripts/verify_versions.py`
passing:

```text
sha256(docs/canonical/TZ-00-domain-event-canon.md) =
  374b25fddfab88846622bf078b35c4246d8ad8c5d65bf43e6ac4e82653f74f74
CANON_VERSION = 0.5.0
```

This is a canon-only change: no `services/ai-processing-service`
directory, JSON Schema, OpenAPI file, or reason-code registry was
created, and no PACK-02/03/04/05 source code was touched. ADR-022's own
content — the `verify_role_assignment_for_action` function signature and
the repository-level reviewer-role taxonomy — remains repository-side,
not canon text, since canon does not name specific cross-pack functions;
ADR-025's own content — the provider-abstraction interface and the
`AIDisclosurePackage` JSON Schema — likewise remains repository-side;
canon 19c only records the canon-shaped parts of ADR-023's and ADR-025's
decisions (the field/status/event additions and the structural
invariants). Implementation of `ai-processing-service` remains a
separate, later task, gated on this canon content but not authorized by
it alone.

ADR-016 through ADR-020 are this project's third governance round,
drafted and accepted for CLAUDE-PACK-05 (`docs/handover/PACK-05-SPEC.md`,
Governance Context) — see `docs/review/PACK-05-OWNER-DECISIONS.md` for
the resolved decision record. ADR-016/017/019 were accepted as proposed;
ADR-018 and ADR-020 with amendments — see each ADR's own "Owner decision"
section for the exact amended text. **ADR-018's (and, for its
repository-side content, ADR-020's) canon edit has now been implemented**
(2026-07-23, as its own separate, dedicated task, per that acceptance's
own explicit deferral) — see the paragraph below for the resulting
canon 19b content and checksum. **No `services/governance-service`
directory, schema, OpenAPI file, or reason-code registry exists yet** —
implementation of `governance-service` itself remains a separate, later
task, gated on these five accepted ADRs and on the canon content below,
but not authorized by either alone.

**ADR-018's canon edit has been implemented in the canon itself**
(2026-07-23), as its own separate, dedicated task following ADR-018's
(and ADR-020's) acceptance (this project's third canon-text edit, after
ADR-010's and ADR-013's): a new section 19b ("Governance Context")
defines `GovernancePolicy`, `GovernanceDecision`, and `TechnicalChallenge`
— fields, identifiers, statuses, owner, invariants, allowed transitions,
forbidden links, and immutable correction/superseding semantics — in
full, including all three ADR-018 Owner-decision amendments, and fully
integrates the already-canon-defined `RoleAssignment` (8.4, unchanged),
including the D2 `AdministratorRole` clarification; a new section 20.15
adds the twelve-event Governance catalog; section 22's ownership matrix
gained three new rows; section 23's forbidden-links list gained the
reworded `AdministratorRole` entry plus new D4/D5 entries. Section
19b.6 records ADR-017's accepted cross-pack write boundary
(`voting-service` sole writer of `Ballot`; no `ResultPublication`
mutation; finality via `governance-service`). `canon_version` moved
`0.3.0 → 0.4.0`, mirrored across `docs/canonical/canon-version.json`,
`packages/python/epd2-core/src/epd2_core/version.py`, and
`packages/typescript/epd2-types/src/version.ts`, with both
version-consistency unit tests updated and `scripts/verify_versions.py`
passing:

```text
sha256(docs/canonical/TZ-00-domain-event-canon.md) =
  61232dc8488f1dd96ea030fa3c41bd397c1c5cf1c7c8cee484bda0568d02c202
CANON_VERSION = 0.4.0
```

This is a canon-only change: no `services/governance-service` directory,
JSON Schema, OpenAPI file, or reason-code registry was created, and no
PACK-02/03/04 source code was touched. ADR-020's own content — the
closed `role_code` pilot taxonomy and the bootstrap seed-command
mechanism (§5) — remains repository-side content, not canon text; canon
19b only records the structural, canon-shaped parts of ADR-020's
decisions (two-actor approval scope reflected in transition rules,
`role_code` naming for cross-reference, and the multiple-challenge/
no-challenge-path rules). Implementation of `governance-service`
remains a separate, later task, gated on this canon content but not
authorized by it alone.

ADR-011 through ADR-015 are this project's second governance round,
drafted and accepted for CLAUDE-PACK-04 (`docs/handover/PACK-04-SPEC.md`,
Transparency Context) — see `docs/review/PACK-04-OWNER-DECISIONS.md` for
the resolved decision record. ADR-011/012/014 were accepted as proposed;
ADR-013 and ADR-015 with amendments — see each ADR's own "Owner decision"
section for the exact amended text. **ADR-013's canon edit has now been
implemented** (2026-07-23, as its own separate, dedicated task, per that
acceptance's own explicit deferral): canon section 19a
(`PublicLedgerEntry`, `AuditExportPackage`, `DisclosurePolicy`,
`LobbyLogEntry`, with all four Owner-decision amendments), section 20.14
(ten Transparency events), and four new section 22 ownership-matrix rows
are now part of the canon document; `canon_version` moved `0.2.0 →
0.3.0`. **No PACK-04 service code exists yet** — this was a canon-only
change; `transparency-service` implementation remains a separate, later
task, not authorized by the canon edit alone.

ADR-005/006/008/009/010 were all accepted for CLAUDE-PACK-03
(`docs/handover/PACK-03-SPEC.md`) — ADR-005/006/008 as proposed;
ADR-009 and ADR-010 with amendments — see each ADR's own "Owner decision"
section for the exact amended text.

**ADR-010 has been implemented in the canon itself** (2026-07-22): this
is the first edit to `docs/canonical/TZ-00-domain-event-canon.md`'s own
text since its original acceptance. `Ballot.challenge_window_hours`
(section 15.1) and `ResultPublication.challenge_deadline_at` (section
15.6, with the finality clarification the owner required) are now part
of the canon; `canon_version` moved `0.1.0 → 0.2.0`, mirrored across
`docs/canonical/canon-version.json`,
`packages/python/epd2-core/src/epd2_core/version.py`, and
`packages/typescript/epd2-types/src/version.ts`, with both
version-consistency unit tests updated to match and
`scripts/verify_versions.py` passing. Every prior addition in this
project (including PACK-02's own 21 reason codes) went through a
pack-level registry file specifically to avoid touching the canon
document — this is the first time that was not possible, since a
challenge window and a finality cutoff are properties of the canonical
`Ballot`/`ResultPublication` entities themselves, not reason-code
metadata.

Per canon section 26, PACK-03 implementation code may now be written
consistent with all five accepted ADRs above — no PACK-03 service
directory has been created yet; that remains a separate, later task.
Owner-facing status: `docs/review/PACK-03-OWNER-DECISIONS.md`.

**ADR-013 has been implemented in the canon itself** (2026-07-23), as its
own separate, dedicated task following ADR-013's acceptance (this
project's second canon-text edit, after ADR-010's): a new section 19a
("Прозрачность / Transparency Context") defines `PublicLedgerEntry`,
`AuditExportPackage`, `DisclosurePolicy`, and `LobbyLogEntry` — fields,
identifiers, statuses, owner, invariants, forbidden links, and the
amended immutability/correction semantics — in full; a new section 20.14
adds the ten-event Transparency catalog; section 22's ownership matrix
gained four new rows; section 23's forbidden-links list was extended.
`canon_version` moved `0.2.0 → 0.3.0`, mirrored across
`docs/canonical/canon-version.json`,
`packages/python/epd2-core/src/epd2_core/version.py`, and
`packages/typescript/epd2-types/src/version.ts`, with both
version-consistency unit tests updated and `scripts/verify_versions.py`
passing:

```text
sha256(docs/canonical/TZ-00-domain-event-canon.md) =
  9fc04b928ff043d25354039165eb7a9d0683396c6712210594eef232d6daf9ad
CANON_VERSION = 0.3.0
```

This is a canon-only change: no `services/transparency-service`
directory, JSON Schema, OpenAPI file, or reason-code registry was
created, and no PACK-02/03 source code was touched. Implementation of
`transparency-service` remains a separate, later task, gated on this
canon content but not authorized by it alone.

---

## ADR-069 — ADR-078 (PACK-13, Production Data Plane & Contract Evolution)

**Status: accepted.** Proposed and accepted by the PACK-13 specification
round, which set no version and implemented nothing; implemented in
**reference form** in `services/data-plane-service`. Reference form means
the contracts, the governed workflows and the refusals are real and
tested, and the production data plane is neither deployed nor claimed.

PACK-13 reached **FINAL PASS** at repository version `0.13.0` on an
external GitHub Actions run. The ten ADRs were `accepted` before that run
and are unaffected by it, in the same way ADR-055—ADR-060 and
ADR-061—ADR-068 kept their `proposed` status through PACK-11's and
PACK-12's FINAL PASS rounds: a green pipeline verifies the implementation,
not the governance status of a decision record. **NOT PRODUCTION READY.
NOT LEGALLY ACTIVATED.**

| ADR     | Decision                                                                                                                                                           | Where the reference implementation lives |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------- |
| ADR-069 | A PostgreSQL-compatible relational data plane organised as domain-owned schemas, with organizational scope as a first-class column from the first migration        | `domain`, `storage`, `boundaries`        |
| ADR-070 | Every table has exactly one owning domain; exactly four integration mechanisms are admissible; audit ingestion is submission, not persistence                      | `boundaries`, `storage`                  |
| ADR-071 | The transactional outbox is mandatory; transport metadata stays off the canonical envelope, which is what keeps this pack canon-neutral                            | `outbox`, `storage.ReferenceUnitOfWork`  |
| ADR-072 | At-least-once delivery with effectively-once consumer effect through mandatory consumer idempotency; the stronger phrase is claimed nowhere and a scan enforces it | `delivery`, `idempotency`                |
| ADR-073 | A canonical schema registry in which content digest and schema-version identity are separate fields answering separate questions                                   | `registry`, `canonicalization`           |
| ADR-074 | Five compatibility modes with `unknown` as a first-class outcome; six structurally invisible change classes always require semantic review                         | `compatibility`, `contracts`             |
| ADR-075 | A migration is immutable once applied; five checks are automated gates rather than reviewer vigilance                                                              | `migrations`, `backfill`                 |
| ADR-076 | A read model is never authoritative, never widens source authorization, and is not a hidden cross-domain database                                                  | `projections`                            |
| ADR-077 | Optimistic concurrency everywhere it matters; idempotency keys scoped to a domain and an operation, never derived from a person identifier                         | `concurrency`, `idempotency`             |
| ADR-078 | Retention applies to infrastructure; a legal hold preserves data and authorizes nothing; evidence uses PACK-11's mechanisms rather than a second store             | `retention`                              |

Specification and matrices: `docs/packs/PACK-13/`. Round reports:
`docs/handover/PACK-13-SPEC-ADR-REPORT.md` (the specification round,
retained unchanged), `docs/handover/PACK-13-IMPLEMENTATION-CANDIDATE-REPORT.md`
(the candidate round, likewise retained unchanged),
`docs/handover/PACK-13-KNOWN-LIMITATIONS.md`,
`docs/handover/PACK-13-FINAL-PASS-REPORT.md` and
`docs/handover/PACK-13-EXTERNAL-CI-VERIFICATION-RESULT.md`.
