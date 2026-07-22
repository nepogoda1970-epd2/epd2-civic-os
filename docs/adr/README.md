# Architecture Decision Records (ADR)

Любое отклонение от канона (`docs/canonical/TZ-00-domain-event-canon.md`)
или от утверждённой архитектуры оформляется как ADR.

- Шаблон: `ADR-000-template.md`.
- ADR нумеруются последовательно: `ADR-001`, `ADR-002`, ...
- До статуса `accepted` предложенное изменение **не** включается в рабочий
  код.

## Статусы ADR

- `proposed`
- `under_review`
- `accepted`
- `rejected`
- `superseded`
- `implemented`

## Список ADR

| ADR                                                       | Тема                                                                  | Статус   |
| --------------------------------------------------------- | --------------------------------------------------------------------- | -------- |
| [ADR-001](./ADR-001-repository-strategy.md)               | Use a modular monorepo for the initial development stage              | accepted |
| [ADR-002](./ADR-002-identity-participation-separation.md) | Identity/participation separation and canonical event/name resolution | accepted |
| [ADR-003](./ADR-003-append-only-audit-hash-chain.md)      | Append-only Audit Core with sequential hash chaining                  | accepted |
| [ADR-004](./ADR-004-reason-code-registry.md)              | Centralized PACK-02 reason-code registry and additive codes           | accepted |
