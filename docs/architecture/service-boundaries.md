# Service Boundaries

Настоящий документ фиксирует обязательные границы между будущими модулями
и сервисами EPD² Civic OS, вытекающие из архитектурных инвариантов ТЗ-00
(`docs/canonical/TZ-00-domain-event-canon.md`, раздел 4).

## Один владелец сущности

У каждой канонической сущности есть ровно один модуль-владелец (см.
`docs/architecture/data-ownership.md` и раздел 22 канона —
«Матрица владения сущностями»). Другие модули не изменяют сущность
напрямую и не обращаются напрямую к её хранилищу.

## Запрет прямого доступа к чужой базе

Модуль не может:

- читать таблицы другого модуля;
- изменять их;
- использовать общий ORM для всей платформы;
- выполнять межсервисные SQL-запросы.

## Интеграция только через API и события

Взаимодействие между модулями допускается только через:

- версионированный API;
- версионированное событие (см. раздел 21 канона — «Стандарт события»);
- утверждённый read model;
- специальный audit export.

## Shared packages не содержат бизнес-логики

Пакеты в `packages/` (`epd2-core` для Python, `epd2-types` для TypeScript)
предоставляют только:

- инфраструктурные типы;
- константы версий;
- универсальные утилиты (например, генерацию и валидацию UUID).

Они не должны содержать доменных сущностей, доменных статусов, бизнес-правил
или бизнес-логики конкретного контура.

## Потенциальная отделяемость сервиса

Репозиторий на этом этапе организован как модульный монорепозиторий (см.
`docs/adr/ADR-001-repository-strategy.md`), но каждый будущий сервис должен
проектироваться так, чтобы его можно было выделить в независимый деплой-юнит
без нарушения перечисленных выше границ.

## Реализация в CLAUDE-PACK-02

`services/account-service`, `services/identity-service`,
`services/eligibility-service`, `services/credential-service`,
`services/audit-core` — первые пять независимых модулей, реализующих
правила этого документа буквально, а не только декларативно:

- у каждого — собственный `pyproject.toml`, `src/`, `tests/`, storage
  interface и in-memory reference adapter (пока без production-базы —
  см. `docs/review/KNOWN_LIMITATIONS.md`);
- ни один из пяти сервисов не импортирует `src/` другого — проверено
  структурно (AST-анализ импортов, не текстовый grep) в
  `tests/repository/test_service_boundaries.py`, которая проходит по
  полной матрице N×N запрещённых пар для всех пяти сервисов разом, и
  дополнительно в
  `services/eligibility-service/tests/test_domain.py::test_eligibility_service_has_no_import_dependency_on_identity_service`
  как узкая, service-локальная проверка того же правила;
- взаимодействие между сервисами идёт только через явный вызов
  прикладной команды одного сервиса, куда caller передаёт результат
  другого сервиса как input value — не через общее хранилище;
- единственная намеренная межсервисная зависимость — все четыре
  доменных сервиса (`account-`, `identity-`, `eligibility-`,
  `credential-service`) зависят от `epd2-audit-core`, чтобы записывать
  собственные `AuditEvent` (см. `docs/architecture/audit-kernel.md`);
  зависимость однонаправленная — Audit Core не знает ни о каком
  доменном сервисе;
- `packages/python/epd2-core` расширен только инфраструктурными
  примитивами (canonical event envelope, UUID/time helpers, generic
  validation utilities, version constants, reason-code infrastructure
  без доменных решений) — без единой доменной сущности, статуса или
  бизнес-правила, специфичного для одного контура (пакет 4.2).

Полное разделение личности и участия (`Account` → `IdentityRecord` →
`EligibilityRule`/`Decision`/`Snapshot` → `ParticipationCredential`)
описано отдельно в
`docs/architecture/identity-participation-separation.md`.
