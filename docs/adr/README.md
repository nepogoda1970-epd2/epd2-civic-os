# Architecture Decision Records (ADR)

Любое отклонение от канона (`docs/canonical/TZ-00-domain-event-canon.md`)
или от утверждённой архитектуры оформляется как ADR.

- Шаблон: `ADR-000-template.md`.
- ADR нумеруются последовательно: `ADR-001`, `ADR-002`, ...
- До статуса `accepted` предложенное изменение **не** включается в рабочий
  код.
- Действующая версия канона: **`0.7.0`**
  (`docs/canonical/canon-version.json`), с 2026-07-25 (ADR-037).

## Статусы ADR

- `proposed`
- `under_review`
- `accepted`
- `rejected`
- `superseded`
- `implemented`

## Список ADR

| ADR                                                                                      | Тема                                                                                                                                                                                                | Статус                                                                                                                                |
| ---------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| [ADR-001](./ADR-001-repository-strategy.md)                                              | Use a modular monorepo for the initial development stage                                                                                                                                            | accepted                                                                                                                              |
| [ADR-002](./ADR-002-identity-participation-separation.md)                                | Identity/participation separation and canonical event/name resolution                                                                                                                               | accepted                                                                                                                              |
| [ADR-003](./ADR-003-append-only-audit-hash-chain.md)                                     | Append-only Audit Core with sequential hash chaining                                                                                                                                                | accepted                                                                                                                              |
| [ADR-004](./ADR-004-reason-code-registry.md)                                             | Centralized PACK-02 reason-code registry and additive codes                                                                                                                                         | accepted                                                                                                                              |
| [ADR-005](./ADR-005-pack-03-service-decomposition.md)                                    | PACK-03 service decomposition (Participation and Decision Kernel)                                                                                                                                   | accepted                                                                                                                              |
| [ADR-006](./ADR-006-pack-03-reason-code-additions.md)                                    | PACK-03 reason-code registry and additive codes                                                                                                                                                     | accepted                                                                                                                              |
| ADR-007                                                                                  | reserved — not used by this governance round                                                                                                                                                        | —                                                                                                                                     |
| [ADR-008](./ADR-008-pack-03-pack-02-integration-boundary.md)                             | PACK-03 to PACK-02 integration boundary                                                                                                                                                             | accepted                                                                                                                              |
| [ADR-009](./ADR-009-voting-delegation-quorum-defaults.md)                                | Voting, delegation, quorum, tie, challenge, and finality defaults                                                                                                                                   | accepted (amended: items 13, 14)                                                                                                      |
| [ADR-010](./ADR-010-ballot-challenge-window-canon-addition.md)                           | Canon minor-version addition: Ballot challenge window / ResultPublication finality                                                                                                                  | accepted (amended: finality wording)                                                                                                  |
| [ADR-011](./ADR-011-pack-04-transparency-service-decomposition.md)                       | PACK-04 Transparency service decomposition                                                                                                                                                          | accepted                                                                                                                              |
| [ADR-012](./ADR-012-pack-04-cross-pack-read-boundary.md)                                 | PACK-04 cross-pack read boundary and dependency matrix                                                                                                                                              | accepted                                                                                                                              |
| [ADR-013](./ADR-013-canon-0.3.0-transparency-context-additions.md)                       | Canon minor-version addition: Transparency Context entities, events, ownership (`0.2.0 → 0.3.0`, implemented 2026-07-23)                                                                            | accepted (amended: proof semantics, DisclosurePolicy field model, correction semantics, role references)                              |
| [ADR-014](./ADR-014-pack-04-reason-code-additions.md)                                    | PACK-04 reason-code registry and additive codes                                                                                                                                                     | accepted                                                                                                                              |
| [ADR-015](./ADR-015-disclosure-redaction-lobby-log-defaults.md)                          | Disclosure, redaction, public audit export, and Lobby Log defaults                                                                                                                                  | accepted (amended: Lobby Log timing, reviewer identity, small-cell threshold, audit-proof semantics)                                  |
| [ADR-016](./ADR-016-pack-05-governance-service-decomposition.md)                         | PACK-05 Governance service decomposition                                                                                                                                                            | accepted                                                                                                                              |
| [ADR-017](./ADR-017-pack-05-cross-pack-boundary.md)                                      | PACK-05 cross-pack boundary — reads, and the ballot/result write question                                                                                                                           | accepted                                                                                                                              |
| [ADR-018](./ADR-018-canon-0.4.0-governance-context-additions.md)                         | Canon minor-version addition: Governance Context entities, events, ownership (`0.3.0 → 0.4.0`, implemented 2026-07-23)                                                                              | accepted (amended: TechnicalChallenge submitter authorization, finality_outcome/FinalityStatus split, GovernanceDecision status enum) |
| [ADR-019](./ADR-019-pack-05-reason-code-additions.md)                                    | PACK-05 reason-code registry and additive codes                                                                                                                                                     | accepted                                                                                                                              |
| [ADR-020](./ADR-020-pack-05-authority-roles-challenge-lifecycle.md)                      | PACK-05 authority, roles, and challenge-lifecycle defaults                                                                                                                                          | accepted (amended: challenge-submission alignment, bootstrap mechanism fully specified)                                               |
| [ADR-021](./ADR-021-pack-06-ai-processing-service-decomposition.md)                      | PACK-06 AI Processing service decomposition                                                                                                                                                         | accepted                                                                                                                              |
| [ADR-022](./ADR-022-pack-06-cross-pack-boundary.md)                                      | PACK-06 cross-pack boundary — one narrow read into `governance-service` for reviewer verification                                                                                                   | accepted (amended: `verify_role_assignment_for_action` replaces local reviewer-check logic)                                           |
| [ADR-023](./ADR-023-canon-0.5.0-ai-processing-context-additions.md)                      | Canon minor-version addition: `AIProcessingRecord` field/status/event extensions (`0.4.0 → 0.5.0`, implemented 2026-07-24)                                                                          | accepted (amended: `RedactionManifest` canonicalized, disclosure-lifecycle fields and `DisclosureStatus` added)                       |
| [ADR-024](./ADR-024-pack-06-reason-code-additions.md)                                    | PACK-06 reason-code registry and additive codes                                                                                                                                                     | accepted                                                                                                                              |
| [ADR-025](./ADR-025-pack-06-use-policy-redaction-providers-disclosure.md)                | PACK-06 use-class policy, redaction enforcement, providers, and mandatory disclosure                                                                                                                | accepted (amended: explicit five-step `AIDisclosurePackage` disclosure protocol replaces informal orchestration rule)                 |
| [ADR-026](./ADR-026-pack-07-service-decomposition-policy-separation.md)                  | PACK-07 service decomposition — `eligibility-service`/`membership-service` split and participant/party-membership policy separation                                                                 | proposed                                                                                                                              |
| [ADR-027](./ADR-027-pack-07-cross-service-boundaries.md)                                 | PACK-07 cross-service boundaries — narrow reads between `membership-service`, `eligibility-service`, `identity-service`, `governance-service`                                                       | proposed                                                                                                                              |
| [ADR-028](./ADR-028-canon-0.6.0-participation-membership-context-additions.md)           | Canon minor-version addition (proposed): Participation and Membership Policy context — electoral-eligibility claims, two-stage admission, membership privacy (`0.5.0 → 0.6.0`, not yet implemented) | proposed                                                                                                                              |
| [ADR-029](./ADR-029-pack-07-reason-code-additions.md)                                    | PACK-07 reason-code registry and additive codes                                                                                                                                                     | proposed                                                                                                                              |
| [ADR-030](./ADR-030-pack-07-policy-mechanics-human-decisions.md)                         | PACK-07 policy mechanics, `MembershipApplication` lifecycle, consequential human decisions, and appeal-model resolution                                                                             | proposed                                                                                                                              |
| [ADR-031](./ADR-031-pack-07-security-architecture-anti-correlation-protocol-agility.md)  | PACK-07 security architecture — domain pseudonyms, anti-correlation invariant, Credential Issuer boundary, cryptographic-protocol agility, audit/queue properties, future-pack boundaries           | proposed                                                                                                                              |
| [ADR-032](./ADR-032-organization-and-civic-space-ownership.md)                           | PACK-08 Organization and CivicSpace ownership — new `organization-service`, narrow-read boundary for every other service                                                                            | accepted                                                                                                                              |
| [ADR-033](./ADR-033-organizational-relationships-effective-dating-and-reorganization.md) | PACK-08 organizational relationships, effective dating, and reorganization — multiple typed relationship graphs (hierarchy/continuity/cooperation), not a strict tree                               | accepted                                                                                                                              |
| [ADR-034](./ADR-034-regional-scope-authorization-and-inheritance.md)                     | PACK-08 regional scope authorization and inheritance — default-deny, six explicit access modes, anti-confused-deputy/anti-role-name-as-proof                                                        | accepted                                                                                                                              |
| [ADR-035](./ADR-035-cross-domain-scope-classification-and-migration.md)                  | PACK-08 cross-domain scope classification and migration — field-by-field decision for `organization_id`/`region_code`/`jurisdiction`/`scope_type`/`scope_id`, no automated bulk rewrite             | accepted                                                                                                                              |
| [ADR-036](./ADR-036-institutional-authority-assignments-and-non-combinable-roles.md)     | PACK-08 institutional authority assignments and non-combinable roles — new `OrganizationalAuthority` entity, role-lifecycle invariants, no-implicit-transfer rule                                   | accepted                                                                                                                              |
| [ADR-037](./ADR-037-organization-and-regional-scope-canon-amendment.md)                  | Organization and Regional Scope Canon Amendment — canon minor-version addition: new section 19e (`0.6.0 → 0.7.0`, implemented 2026-07-25)                                                           | accepted                                                                                                                              |

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
