# Reason Codes

Список ниже — точная копия раздела 24
(«Стандарт reason codes») `docs/canonical/TZ-00-domain-event-canon.md`,
canon version `0.1.0`. Список пока документальный.

- `IDENTITY_NOT_VERIFIED`
- `IDENTITY_VERIFICATION_EXPIRED`
- `ELIGIBILITY_NOT_MET`
- `ELIGIBILITY_PENDING`
- `CREDENTIAL_EXPIRED`
- `CREDENTIAL_ALREADY_USED`
- `CREDENTIAL_SCOPE_MISMATCH`
- `PERMISSION_DENIED`
- `ROLE_CONFLICT`
- `BALLOT_NOT_OPEN`
- `BALLOT_ALREADY_CLOSED`
- `BALLOT_CONFIGURATION_LOCKED`
- `DUPLICATE_SUPPORT`
- `DUPLICATE_VOTE`
- `DELEGATION_CYCLE`
- `DELEGATION_EXPIRED`
- `MODERATION_POLICY_VIOLATION`
- `APPEAL_DEADLINE_EXPIRED`
- `EVENT_VERSION_UNSUPPORTED`
- `INTEGRITY_CHECK_FAILED`
- `SERVICE_STATE_READ_ONLY`
- `EMERGENCY_FREEZE_ACTIVE`

## Статус

- Список пока документальный.
- Executable enum будет создан в отдельном пакете, когда появится модуль,
  который реально их использует.
- Новые reason codes нельзя добавлять без изменения канона (ADR + новая
  версия `docs/canonical/TZ-00-domain-event-canon.md`).
