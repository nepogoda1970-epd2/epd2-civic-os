# Data Ownership

Таблица-заготовка владения каноническими сущностями. Полный список см. в
`docs/canonical/TZ-00-domain-event-canon.md`, раздел 22 («Матрица владения
сущностями»). Ни одна из перечисленных сущностей не реализована на этапе
CLAUDE-PACK-01 — колонка «Current implementation» отражает это явно.

Настоящий документ не создаёт таблиц базы данных и не описывает схему
хранения — только будущее владение.

| Domain                  | Future owner                  | Current implementation |
| ----------------------- | ----------------------------- | ---------------------- |
| Account                 | Account Service               | Not implemented        |
| IdentityRecord          | Identity Verification Service | Not implemented        |
| EligibilityRule         | Eligibility Engine            | Not implemented        |
| EligibilityDecision     | Eligibility Engine            | Not implemented        |
| EligibilitySnapshot     | Eligibility Engine            | Not implemented        |
| ParticipationCredential | Credential Issuer             | Not implemented        |
| Organization            | Organization Service          | Not implemented        |
| CivicSpace              | Organization Service          | Not implemented        |
| Membership              | Membership Service            | Not implemented        |
| RoleAssignment          | Permission / Role Service     | Not implemented        |
| Initiative              | Initiative Service            | Not implemented        |
| InitiativeVersion       | Initiative Service            | Not implemented        |
| Amendment               | Amendment Service             | Not implemented        |
| SourceRecord            | Evidence Service              | Not implemented        |
| Discussion              | Discussion Service            | Not implemented        |
| Contribution            | Discussion Service            | Not implemented        |
| ModerationCase          | Moderation Service            | Not implemented        |
| ModerationDecision      | Moderation Service            | Not implemented        |
| Appeal                  | Appeal Service                | Not implemented        |
| Ballot                  | Ballot Definition Service     | Not implemented        |
| BallotOption            | Ballot Definition Service     | Not implemented        |
| VoteEnvelope            | Vote Casting Service          | Not implemented        |
| VoteReceipt             | Receipt Service               | Not implemented        |
| Tally                   | Tally Service                 | Not implemented        |
| ResultPublication       | Result Publication Service    | Not implemented        |
| Delegation              | Delegation Service            | Not implemented        |
| DelegationSnapshot      | Delegation Resolution Engine  | Not implemented        |
| AIProcessingRecord      | AI Accountability Service     | Not implemented        |
| AuditEvent              | Audit Core                    | Not implemented        |
| EmergencyAction         | Governance / Crisis Service   | Not implemented        |
