# Architecture Decision Records (ADR)

Любое отклонение от канона (`docs/canonical/TZ-00-domain-event-canon.md`)
или от утверждённой архитектуры оформляется как ADR.

- Шаблон: `ADR-000-template.md`.
- ADR нумеруются последовательно: `ADR-001`, `ADR-002`, ...
- До статуса `accepted` предложенное изменение **не** включается в рабочий
  код.
- Действующая версия канона: **`0.2.0`**
  (`docs/canonical/canon-version.json`), с 2026-07-22 (ADR-010).

## Статусы ADR

- `proposed`
- `under_review`
- `accepted`
- `rejected`
- `superseded`
- `implemented`

## Список ADR

| ADR                                                            | Тема                                                                               | Статус                               |
| -------------------------------------------------------------- | ---------------------------------------------------------------------------------- | ------------------------------------ |
| [ADR-001](./ADR-001-repository-strategy.md)                    | Use a modular monorepo for the initial development stage                           | accepted                             |
| [ADR-002](./ADR-002-identity-participation-separation.md)      | Identity/participation separation and canonical event/name resolution              | accepted                             |
| [ADR-003](./ADR-003-append-only-audit-hash-chain.md)           | Append-only Audit Core with sequential hash chaining                               | accepted                             |
| [ADR-004](./ADR-004-reason-code-registry.md)                   | Centralized PACK-02 reason-code registry and additive codes                        | accepted                             |
| [ADR-005](./ADR-005-pack-03-service-decomposition.md)          | PACK-03 service decomposition (Participation and Decision Kernel)                  | accepted                             |
| [ADR-006](./ADR-006-pack-03-reason-code-additions.md)          | PACK-03 reason-code registry and additive codes                                    | accepted                             |
| ADR-007                                                        | reserved — not used by this governance round                                       | —                                    |
| [ADR-008](./ADR-008-pack-03-pack-02-integration-boundary.md)   | PACK-03 to PACK-02 integration boundary                                            | accepted                             |
| [ADR-009](./ADR-009-voting-delegation-quorum-defaults.md)      | Voting, delegation, quorum, tie, challenge, and finality defaults                  | accepted (amended: items 13, 14)     |
| [ADR-010](./ADR-010-ballot-challenge-window-canon-addition.md) | Canon minor-version addition: Ballot challenge window / ResultPublication finality | accepted (amended: finality wording) |

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
