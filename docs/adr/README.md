# Architecture Decision Records (ADR)

Любое отклонение от канона (`docs/canonical/TZ-00-domain-event-canon.md`)
или от утверждённой архитектуры оформляется как ADR.

- Шаблон: `ADR-000-template.md`.
- ADR нумеруются последовательно: `ADR-001`, `ADR-002`, ...
- До статуса `accepted` предложенное изменение **не** включается в рабочий
  код.
- Действующая версия канона: **`0.4.0`**
  (`docs/canonical/canon-version.json`), с 2026-07-23 (ADR-018, ADR-020).

## Статусы ADR

- `proposed`
- `under_review`
- `accepted`
- `rejected`
- `superseded`
- `implemented`

## Список ADR

| ADR                                                                 | Тема                                                                                                                     | Статус                                                                                                                                |
| ------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------- |
| [ADR-001](./ADR-001-repository-strategy.md)                         | Use a modular monorepo for the initial development stage                                                                 | accepted                                                                                                                              |
| [ADR-002](./ADR-002-identity-participation-separation.md)           | Identity/participation separation and canonical event/name resolution                                                    | accepted                                                                                                                              |
| [ADR-003](./ADR-003-append-only-audit-hash-chain.md)                | Append-only Audit Core with sequential hash chaining                                                                     | accepted                                                                                                                              |
| [ADR-004](./ADR-004-reason-code-registry.md)                        | Centralized PACK-02 reason-code registry and additive codes                                                              | accepted                                                                                                                              |
| [ADR-005](./ADR-005-pack-03-service-decomposition.md)               | PACK-03 service decomposition (Participation and Decision Kernel)                                                        | accepted                                                                                                                              |
| [ADR-006](./ADR-006-pack-03-reason-code-additions.md)               | PACK-03 reason-code registry and additive codes                                                                          | accepted                                                                                                                              |
| ADR-007                                                             | reserved — not used by this governance round                                                                             | —                                                                                                                                     |
| [ADR-008](./ADR-008-pack-03-pack-02-integration-boundary.md)        | PACK-03 to PACK-02 integration boundary                                                                                  | accepted                                                                                                                              |
| [ADR-009](./ADR-009-voting-delegation-quorum-defaults.md)           | Voting, delegation, quorum, tie, challenge, and finality defaults                                                        | accepted (amended: items 13, 14)                                                                                                      |
| [ADR-010](./ADR-010-ballot-challenge-window-canon-addition.md)      | Canon minor-version addition: Ballot challenge window / ResultPublication finality                                       | accepted (amended: finality wording)                                                                                                  |
| [ADR-011](./ADR-011-pack-04-transparency-service-decomposition.md)  | PACK-04 Transparency service decomposition                                                                               | accepted                                                                                                                              |
| [ADR-012](./ADR-012-pack-04-cross-pack-read-boundary.md)            | PACK-04 cross-pack read boundary and dependency matrix                                                                   | accepted                                                                                                                              |
| [ADR-013](./ADR-013-canon-0.3.0-transparency-context-additions.md)  | Canon minor-version addition: Transparency Context entities, events, ownership (`0.2.0 → 0.3.0`, implemented 2026-07-23) | accepted (amended: proof semantics, DisclosurePolicy field model, correction semantics, role references)                              |
| [ADR-014](./ADR-014-pack-04-reason-code-additions.md)               | PACK-04 reason-code registry and additive codes                                                                          | accepted                                                                                                                              |
| [ADR-015](./ADR-015-disclosure-redaction-lobby-log-defaults.md)     | Disclosure, redaction, public audit export, and Lobby Log defaults                                                       | accepted (amended: Lobby Log timing, reviewer identity, small-cell threshold, audit-proof semantics)                                  |
| [ADR-016](./ADR-016-pack-05-governance-service-decomposition.md)    | PACK-05 Governance service decomposition                                                                                 | accepted                                                                                                                              |
| [ADR-017](./ADR-017-pack-05-cross-pack-boundary.md)                 | PACK-05 cross-pack boundary — reads, and the ballot/result write question                                                | accepted                                                                                                                              |
| [ADR-018](./ADR-018-canon-0.4.0-governance-context-additions.md)    | Canon minor-version addition: Governance Context entities, events, ownership (`0.3.0 → 0.4.0`, implemented 2026-07-23)   | accepted (amended: TechnicalChallenge submitter authorization, finality_outcome/FinalityStatus split, GovernanceDecision status enum) |
| [ADR-019](./ADR-019-pack-05-reason-code-additions.md)               | PACK-05 reason-code registry and additive codes                                                                          | accepted                                                                                                                              |
| [ADR-020](./ADR-020-pack-05-authority-roles-challenge-lifecycle.md) | PACK-05 authority, roles, and challenge-lifecycle defaults                                                               | accepted (amended: challenge-submission alignment, bootstrap mechanism fully specified)                                               |

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
