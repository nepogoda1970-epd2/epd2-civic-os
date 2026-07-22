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
`docs/architecture/audit-kernel.md`. Остальные сущности в таблице
по-прежнему не реализованы.

| Domain                  | Future owner                  | Current implementation                                 |
| ----------------------- | ----------------------------- | ------------------------------------------------------ |
| Account                 | Account Service               | Implemented (PACK-02) — `services/account-service`     |
| IdentityRecord          | Identity Verification Service | Implemented (PACK-02) — `services/identity-service`    |
| EligibilityRule         | Eligibility Engine            | Implemented (PACK-02) — `services/eligibility-service` |
| EligibilityDecision     | Eligibility Engine            | Implemented (PACK-02) — `services/eligibility-service` |
| EligibilitySnapshot     | Eligibility Engine            | Implemented (PACK-02) — `services/eligibility-service` |
| ParticipationCredential | Credential Issuer             | Implemented (PACK-02) — `services/credential-service`  |
| Organization            | Organization Service          | Not implemented                                        |
| CivicSpace              | Organization Service          | Not implemented                                        |
| Membership              | Membership Service            | Not implemented                                        |
| RoleAssignment          | Permission / Role Service     | Not implemented                                        |
| Initiative              | Initiative Service            | Not implemented                                        |
| InitiativeVersion       | Initiative Service            | Not implemented                                        |
| Amendment               | Amendment Service             | Not implemented                                        |
| SourceRecord            | Evidence Service              | Not implemented                                        |
| Discussion              | Discussion Service            | Not implemented                                        |
| Contribution            | Discussion Service            | Not implemented                                        |
| ModerationCase          | Moderation Service            | Not implemented                                        |
| ModerationDecision      | Moderation Service            | Not implemented                                        |
| Appeal                  | Appeal Service                | Not implemented                                        |
| Ballot                  | Ballot Definition Service     | Not implemented                                        |
| BallotOption            | Ballot Definition Service     | Not implemented                                        |
| VoteEnvelope            | Vote Casting Service          | Not implemented                                        |
| VoteReceipt             | Receipt Service               | Not implemented                                        |
| Tally                   | Tally Service                 | Not implemented                                        |
| ResultPublication       | Result Publication Service    | Not implemented                                        |
| Delegation              | Delegation Service            | Not implemented                                        |
| DelegationSnapshot      | Delegation Resolution Engine  | Not implemented                                        |
| AIProcessingRecord      | AI Accountability Service     | Not implemented                                        |
| AuditEvent              | Audit Core                    | Implemented (PACK-02) — `services/audit-core`          |
| EmergencyAction         | Governance / Crisis Service   | Not implemented                                        |
