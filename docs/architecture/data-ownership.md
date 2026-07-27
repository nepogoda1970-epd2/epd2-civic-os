# Data Ownership

Таблица владения каноническими сущностями. Полный список см. в
`docs/canonical/TZ-00-domain-event-canon.md`, раздел 22 («Матрица владения
сущностями»).

Настоящий документ не создаёт таблиц базы данных и не описывает схему
хранения — только владение (текущее или будущее).

**CLAUDE-PACK-02** реализовал семь сущностей ниже как независимые сервисы
с in-memory reference adapter (без production-базы данных): `Account`,
`IdentityRecord`, `EligibilityRule`, `EligibilityDecision`,
`EligibilitySnapshot`, `ParticipationCredential`, `AuditEvent`. Подробности —
в `docs/architecture/identity-participation-separation.md` и
`docs/architecture/audit-kernel.md`.

**CLAUDE-PACK-08 (implementation round)** реализовал `Organization` и
`CivicSpace` (canon 8.1/8.2, расширенные ADR-032–ADR-037) и четыре новые
канонические сущности из canon 19e (Organization & Regional Scope Context) —
`OrganizationalUnit`, `OrganizationalRelation`,
`OrganizationalHierarchyOverlapPolicy`, `OrganizationalInheritancePolicy` — а
также `OrganizationalAuthority`, все как единственный владелец в новом
`services/organization-service` (in-memory reference adapter, без
production-базы данных). Подробности — в
`docs/packs/PACK-08-IMPLEMENTATION.md` и
`docs/handover/PACK-08-IMPLEMENTATION-REPORT.md`.

Известный пробел (не устранён в рамках PACK-08, зафиксирован честно): строки
ниже для сущностей, реализованных в PACK-03–PACK-07 (например `Membership`,
`RoleAssignment`, `Initiative*`, `Ballot*`, `AIProcessingRecord` и т. д.),
по-прежнему помечены как «Not implemented», хотя соответствующие сервисы уже
существуют в репозитории. Эта таблица не обновлялась систематически в тех
раундах; исправление всей истории таблицы выходит за рамки задачи PACK-08 и
не было предпринято здесь, чтобы не путать факты реализации PACK-08 с
ретроактивной правкой более старых записей.

| Domain                               | Future owner                  | Current implementation                                  |
| ------------------------------------ | ----------------------------- | ------------------------------------------------------- |
| Account                              | Account Service               | Implemented (PACK-02) — `services/account-service`      |
| IdentityRecord                       | Identity Verification Service | Implemented (PACK-02) — `services/identity-service`     |
| EligibilityRule                      | Eligibility Engine            | Implemented (PACK-02) — `services/eligibility-service`  |
| EligibilityDecision                  | Eligibility Engine            | Implemented (PACK-02) — `services/eligibility-service`  |
| EligibilitySnapshot                  | Eligibility Engine            | Implemented (PACK-02) — `services/eligibility-service`  |
| ParticipationCredential              | Credential Issuer             | Implemented (PACK-02) — `services/credential-service`   |
| Organization                         | Organization Service          | Implemented (PACK-08) — `services/organization-service` |
| CivicSpace                           | Organization Service          | Implemented (PACK-08) — `services/organization-service` |
| OrganizationalUnit                   | Organization Service          | Implemented (PACK-08) — `services/organization-service` |
| OrganizationalRelation               | Organization Service          | Implemented (PACK-08) — `services/organization-service` |
| OrganizationalHierarchyOverlapPolicy | Organization Service          | Implemented (PACK-08) — `services/organization-service` |
| OrganizationalInheritancePolicy      | Organization Service          | Implemented (PACK-08) — `services/organization-service` |
| OrganizationalAuthority              | Organization Service          | Implemented (PACK-08) — `services/organization-service` |
| Membership                           | Membership Service            | Not implemented                                         |
| RoleAssignment                       | Permission / Role Service     | Not implemented                                         |
| Initiative                           | Initiative Service            | Not implemented                                         |
| InitiativeVersion                    | Initiative Service            | Not implemented                                         |
| Amendment                            | Amendment Service             | Not implemented                                         |
| SourceRecord                         | Evidence Service              | Not implemented                                         |
| Discussion                           | Discussion Service            | Not implemented                                         |
| Contribution                         | Discussion Service            | Not implemented                                         |
| ModerationCase                       | Moderation Service            | Not implemented                                         |
| ModerationDecision                   | Moderation Service            | Not implemented                                         |
| Appeal                               | Appeal Service                | Not implemented                                         |
| Ballot                               | Ballot Definition Service     | Not implemented                                         |
| BallotOption                         | Ballot Definition Service     | Not implemented                                         |
| VoteEnvelope                         | Vote Casting Service          | Not implemented                                         |
| VoteReceipt                          | Receipt Service               | Not implemented                                         |
| Tally                                | Tally Service                 | Not implemented                                         |
| ResultPublication                    | Result Publication Service    | Not implemented                                         |
| Delegation                           | Delegation Service            | Not implemented                                         |
| DelegationSnapshot                   | Delegation Resolution Engine  | Not implemented                                         |
| AIProcessingRecord                   | AI Accountability Service     | Not implemented                                         |
| AuditEvent                           | Audit Core                    | Implemented (PACK-02) — `services/audit-core`           |
| EmergencyAction                      | Governance / Crisis Service   | Not implemented                                         |
