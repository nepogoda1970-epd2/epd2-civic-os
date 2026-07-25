# EPD² Civic OS

## Назначение репозитория

EPD² Civic OS — открытая цифровая инфраструктура для гражданского и партийного
участия: идентификация, допуск, участие, обсуждение, голосование и проверяемая
публичная документация решений.

Настоящий репозиторий реализует **CLAUDE-PACK-01 — Repository Skeleton**,
**CLAUDE-PACK-02 — Identity Separation and Audit Kernel**,
**CLAUDE-PACK-03 — Participation and Decision Kernel**,
**CLAUDE-PACK-04 — Transparency Context**,
**CLAUDE-PACK-05 — Governance Context**,
**CLAUDE-PACK-06 — AI Processing Context**,
**CLAUDE-PACK-07 — Participation & Membership Context** и
**CLAUDE-PACK-08 — Organization & Regional Scope Foundation**: стартовый
монорепо-каркас платформы плюс шестнадцать независимых сервисов —
account, identity, eligibility, credential, audit-core (PACK-02, участие
и идентичность структурно разделены, каждое критическое действие
записывается в append-only, hash-chained журнал аудита), initiative,
deliberation, moderation, voting, tally, delegation (PACK-03, полный
цикл гражданской инициативы, обсуждения, модерации, голосования, подсчёта
и делегирования), transparency-service (PACK-04, публичный реестр,
audit export, политика раскрытия данных, реестр лоббистских контактов),
governance-service (PACK-05, роли участников, политики и решения органов
управления, технические оспаривания и производный статус финальности
результатов голосования), ai-processing-service (PACK-06,
`AIProcessingRecord` с двумя независимыми статусными плоскостями,
канонический встроенный `redaction_manifest`, производный
`DisclosureStatus`, `AIDisclosurePackage`, шесть закрытых классов
использования и обязательный протокол раскрытия — ИИ остаётся строго
консультативным и никогда не получает полномочий на автономную мутацию
Civic OS) и membership-service (PACK-07, `PartyMembershipEligibilityPolicy`,
`Membership` — первая реальная реализация канон 8.3, `MembershipApplication`
с двухэтапным жизненным циклом и жёстким инвариантом человеческого
контроля, `AffiliationDeclaration`, `ConflictAssessment`, переиспользуемый
полиморфный `Appeal`), плюс расширение уже существующих `eligibility-service`
(`ParticipantEligibilityPolicy`, `ProcessEligibilityPolicy`,
`StepUpAuthenticationRequirement`, `DigitalDecision`, `AssemblyDecision`,
четыре раздельных признака избирательного права) и `identity-service`
(`AuthenticationContext`, восемь новых полей `IdentityRecord`), а также
**organization-service** (PACK-08, `Organization`/`CivicSpace` — канон
8.1/8.2, шесть дополнительных полей `Organization` — плюс четыре новые
сущности `OrganizationalUnit`, `OrganizationalRelation`,
`OrganizationalHierarchyOverlapPolicy`, `OrganizationalInheritancePolicy`
и `OrganizationalAuthority`: default-deny региональная
scope-авторизация с шестью явными режимами доступа, временный надзор с
90-дневным лимитом по умолчанию, институциональные полномочия с
базовой матрицей несовместимости ролей, шестикатегорийная
классификация `RoleAssignment.scope_id`; ADR-032–037, канон раздел
19e). Остальная бизнес-логика (emergency actions, реальная
eID-интеграция, географическая/избирательная привязка регионов сверх
организационной модели PACK-08) пока не реализована — см.
`docs/review/KNOWN_LIMITATIONS.md`.

## Статус проекта

- Этап: infrastructure skeleton (CLAUDE-PACK-01) — **PACK-01 PASS**, см.
  `docs/handover/PACK-01-REPORT.md`.
- Этап: identity separation and audit kernel (CLAUDE-PACK-02) — **PACK-02
  PASS**, подтверждено внешним прогоном GitHub Actions с реальным сетевым
  доступом: `uv.lock` регенерирован по-настоящему (43 пакета, все 5
  сервисов PACK-02, `hypothesis`/`jsonschema`/`types-PyYAML`), 363 Python-
  теста пройдены (2 пропуска — ожидаемые CT-00-11/12 not-applicable
  маркеры), TypeScript/frontend тесты и `next build` пройдены полностью.
  См. `docs/handover/PACK-02-REPORT.md` для полного описания.
- Этап: participation and decision kernel (CLAUDE-PACK-03) — **PACK-03
  PASS**, подтверждено внешним прогоном GitHub Actions с реальным сетевым
  доступом: `uv.lock`/`package-lock.json` регенерированы по-настоящему,
  1525 Python-тестов пройдены (2 пропуска — те же CT-00-11/12
  not-applicable маркеры), TypeScript (3/3) и frontend (2/2) тесты и
  `next build` пройдены полностью, Ruff/Prettier/ESLint/mypy — чисто, все
  277 обязательных путей на месте, запрещённых файлов нет. Шесть новых
  сервисов: initiative, deliberation, moderation, voting, tally,
  delegation. См. `docs/handover/PACK-03-REPORT.md` для полного описания.
- Этап: transparency context (CLAUDE-PACK-04) — **PACK-04 PASS**,
  подтверждено внешним прогоном GitHub Actions с реальным сетевым
  доступом: `uv.lock`/`package-lock.json` регенерированы по-настоящему,
  1599 Python-тестов пройдены (2 пропуска — те же CT-00-11/12
  not-applicable маркеры), TypeScript и frontend тесты и `next build`
  пройдены полностью, Ruff/Prettier/ESLint/mypy — чисто, все 305
  обязательных путей на месте, запрещённых файлов нет. Один новый
  сервис: `transparency-service` (`PublicLedgerEntry`,
  `AuditExportPackage`, `DisclosurePolicy`, `LobbyLogEntry`; ADR-011–015,
  канон раздел 19a). См. `docs/handover/PACK-04-REPORT.md` для полного
  описания, `docs/handover/PACK-04-SPEC.md`,
  `docs/adr/ADR-013-canon-0.3.0-transparency-context-additions.md`,
  `docs/review/PACK-04-OWNER-DECISIONS.md`.
- Этап: governance context (CLAUDE-PACK-05) — **PACK-05 PASS**,
  подтверждено внешним прогоном GitHub Actions с реальным сетевым
  доступом: `uv.lock`/`package-lock.json` регенерированы по-настоящему,
  1719 Python-тестов пройдены (2 пропуска — те же CT-00-11/12
  not-applicable маркеры), TypeScript (3/3) и frontend (2/2) тесты и
  `next build` пройдены полностью, Prettier/lint/typecheck — чисто, все
  336 обязательных путей на месте, запрещённых файлов нет. Один новый
  сервис: `governance-service` (`RoleAssignment`, `GovernancePolicy`,
  `GovernanceDecision`, `TechnicalChallenge`, производный read model
  `FinalityStatus`; ADR-016–020, канон раздел 19b). См.
  `docs/handover/PACK-05-REPORT.md` для полного описания,
  `docs/handover/PACK-05-SPEC.md`,
  `docs/adr/ADR-018-canon-0.4.0-governance-context-additions.md`,
  `docs/review/PACK-05-OWNER-DECISIONS.md`.
- Этап: AI processing context (CLAUDE-PACK-06) — **PACK-06 PASS**,
  подтверждено внешним прогоном GitHub Actions с реальным сетевым
  доступом: 1822 Python-теста пройдены (3 пропуска — те же
  CT-00-10/CT-00-12 not-applicable-in-earlier-packs маркеры; CT-00-11
  для PACK-06 больше не в их числе — теперь полностью применим и
  проходит), TypeScript (3/3) и frontend (2/2) тесты и `next build`
  пройдены полностью, Prettier/Ruff/ESLint/mypy — чисто, все 363
  обязательных путей на месте, запрещённых файлов нет. Один новый
  сервис: `ai-processing-service` (`AIProcessingRecord` с плоскостями
  `processing_status`/`human_review_status`, каноническим встроенным
  `redaction_manifest`, производным read model `DisclosureStatus`,
  контрактным объектом `AIDisclosurePackage`; ADR-021–025, канон раздел
  19c). Один узкий read-зависимый переход в `governance-service`
  (`verify_role_assignment_for_action`) и вызов
  `transparency-service.publish_ledger_entry` для обязательного
  протокола раскрытия — сам сервис никогда не пишет
  `PublicLedgerEntry` напрямую. См. `docs/handover/PACK-06-REPORT.md`
  для полного описания, `docs/handover/PACK-06-SPEC.md`,
  `docs/adr/ADR-023-canon-0.5.0-ai-processing-context-additions.md`,
  `docs/review/PACK-06-OWNER-DECISIONS.md`.
- Этап: participation & membership context (CLAUDE-PACK-07,
  implementation) — **PACK-07 PASS**, подтверждено внешним прогоном
  GitHub Actions с реальным сетевым доступом: 2028 Python-тестов
  пройдено, 4 пропущено, 0 неудачных; TypeScript (3/3) и frontend (2/2)
  тесты и сборка Next.js 15.5.21 пройдены полностью; Ruff (формат: 359
  файлов уже отформатированы; lint — чисто), Prettier, ESLint, mypy — все
  чисто для всех сервисов; все 402 обязательных пути на месте;
  запрещённых файлов нет; проверка согласованности версий пройдена. (В
  ходе локальной разработки в этой песочнице без сетевого доступа было
  получено 2020 Python-тестов пройдено / 5 пропущено — разница объясняется
  тем, что внешняя среда устанавливает `hypothesis` по-настоящему и
  стартует с чистого чекаута; см. `docs/handover/PACK-07-IMPLEMENTATION-REPORT.md`
  раздел 6a/6b для полного сопоставления.) Один новый сервис: `membership-service`
  (`PartyMembershipEligibilityPolicy`, `Membership`, `MembershipApplication`,
  `AffiliationDeclaration`, `ConflictAssessment`, переиспользуемый
  `Appeal`); расширение на месте `eligibility-service`
  (`ParticipantEligibilityPolicy`, `ProcessEligibilityPolicy`,
  `StepUpAuthenticationRequirement`, `DigitalDecision`,
  `AssemblyDecision`, четыре раздельных признака избирательного права,
  атомарные capability-проверки, выпуск ограниченных capability-токенов)
  и `identity-service` (`AuthenticationContext`, восемь новых полей
  `IdentityRecord`); ADR-026–031, канон раздел 19d. См.
  `docs/handover/PACK-07-IMPLEMENTATION-REPORT.md` для полного описания.
- Canon version: `0.7.0` (`docs/canonical/TZ-00-domain-event-canon.md`).
  Изменения текста канона: PACK-03 под ADR-010 (`0.1.0 → 0.2.0`,
  добавление `Ballot.challenge_window_hours` /
  `ResultPublication.challenge_deadline_at`); CLAUDE-PACK-04 под ADR-013
  (`0.2.0 → 0.3.0`, раздел 19a Transparency Context); CLAUDE-PACK-05 под
  ADR-018/ADR-020 (`0.3.0 → 0.4.0`, раздел 19b Governance Context —
  `GovernancePolicy`, `GovernanceDecision`, `TechnicalChallenge`,
  интеграция уже существующей `RoleAssignment`); CLAUDE-PACK-06
  под ADR-023/ADR-025 (`0.4.0 → 0.5.0`, раздел 19c AI Processing
  Context — расширение уже существующей `AIProcessingRecord` полями
  `processing_status`, `supersedes_ai_processing_record_id`,
  каноническим встроенным `redaction_manifest`, полями жизненного цикла
  раскрытия и производным `DisclosureStatus`; `AIDisclosurePackage` как
  договорной объект); CLAUDE-PACK-07 под ADR-026 через ADR-031 (`0.5.0 →
0.6.0`, раздел 19d Participation & Membership Context — десять новых
  сущностей (`ParticipantEligibilityPolicy`, `ProcessEligibilityPolicy`,
  `StepUpAuthenticationRequirement`, `DigitalDecision`,
  `AssemblyDecision`, `PartyMembershipEligibilityPolicy`,
  `AffiliationDeclaration`, `ConflictAssessment`, `MembershipApplication`,
  `AuthenticationContext`); восемь новых полей `IdentityRecord`; четыре
  раздельных признака избирательного права вместо обобщённого
  `electoral_eligibility_met`; двухэтапный `MembershipApplication` без
  перегрузки `Membership.membership_status`; расширенный до семи
  категорий жёсткий инвариант человеческого контроля; активация
  критической политики по четырём независимым условиям с заморозкой
  версии; исключительно два механизма внешней авторизации). Канон не
  изменялся при реализации самого сервиса `ai-processing-service` —
  эта реализация использует уже принятый канон 0.5.0 и ADR-021–025 без
  дальнейших правок текста канона (см.
  `docs/adr/ADR-023-canon-0.5.0-ai-processing-context-additions.md`,
  `docs/review/PACK-06-OWNER-DECISIONS.md`). CLAUDE-PACK-07's канонический
  раунд (ADR-026–031, `docs/review/PACK-07-OWNER-DECISIONS.md`,
  `docs/handover/PACK-07-CANON-AMENDMENT-REPORT.md`) — также канон-только
  изменение, подтверждённое внешним прогоном GitHub Actions (PASS: 1822
  Python-теста пройдено, 3 пропущено, 0 неудачных; TypeScript 3/3;
  frontend 2/2; успешная сборка Next.js; Prettier/Ruff/ESLint/mypy без
  замечаний — см. раздел 7 `docs/handover/PACK-07-CANON-AMENDMENT-REPORT.md`):
  на момент того канонического раунда ни `membership-service`, ни
  расширение `eligibility-service` ещё не были реализованы; оба теперь
  реализованы в CLAUDE-PACK-07's implementation-раунде (см. запись выше и
  `docs/handover/PACK-07-IMPLEMENTATION-REPORT.md`). CLAUDE-PACK-08 под
  ADR-032 через ADR-037 (`0.6.0 → 0.7.0`, раздел 19e Organization &
  Regional Scope Context — расширение `Organization` (8.1) шестью
  дополнительными полями; подтверждение `CivicSpace` (8.2) без
  изменений; четыре новые сущности, владеемые `organization-service`
  (`OrganizationalUnit`, `OrganizationalRelation`,
  `OrganizationalHierarchyOverlapPolicy`, `OrganizationalInheritancePolicy`),
  плюс `OrganizationalAuthority` и переиспользуемый объект-значение
  `OrganizationalScope`; множественные типизированные направленные
  графы организационных отношений вместо простого дерева; default-deny
  региональная scope-авторизация с шестью явными режимами; владение
  политикой наследования; 90-дневный лимит временного надзора по
  умолчанию; минимальная базовая матрица несовместимости
  институциональных ролей; шестикатегорийная классификация
  `RoleAssignment.scope_id` (8.4 без изменений полей/статуса/владельца)).
  ADR-032 через ADR-036 приняты (`accepted`) в раунде коррекции
  спецификации PACK-08, предшествовавшем настоящему каноническому
  раунду; их принятие само по себе не авторизовало правку канона —
  ADR-037 является тем отдельным, посвящённым каноническому раунду,
  который эту правку авторизует и выполняет (тот же приём, что уже
  применялся к ADR-010/013/018/020/023/025/028). Канон не изменялся при
  реализации самого сервиса `organization-service` — такой реализации
  ещё не существует; настоящий раунд — исключительно канонический/
  документационный, без сервисного кода, схем, событийного транспорта
  или production-интеграции (см.
  `docs/adr/ADR-037-organization-and-regional-scope-canon-amendment.md`,
  `docs/handover/PACK-08-CANON-AMENDMENT-REPORT.md`,
  `docs/packs/PACK-08-OPEN-DECISIONS.md`). Внешний прогон GitHub Actions
  для PACK-08 не выполнялся ни на одном этапе, включая настоящий
  канонический раунд — только честный локальный самоотчёт
  (`docs/handover/PACK-08-CANON-AMENDMENT-REPORT.md` раздел 6).
- Этап: organization & regional scope foundation (CLAUDE-PACK-08,
  implementation) — **локальный самоотчёт, без внешнего прогона GitHub
  Actions**: 2141 Python-тест пройден, 5 пропущено, 0 неудачных (Ruff
  lint/format, mypy — чисто для всех 16 сервисов и `tests/contract`);
  все 445 обязательных путей на месте; запрещённых файлов нет; проверка
  согласованности версий пройдена. Frontend: 11 TypeScript unit-тестов
  пройдено (глобальный `tsx`-биндинг, без `node_modules`), `tsc
  --noEmit` — без реальных ошибок в новом коде (шум от отсутствующих
  `@types/react`/`next` отфильтрован), Prettier — чисто; ESLint и
  production-сборка Next.js не выполнялись в этой песочнице (нет
  сетевого доступа к npm — тот же документированный разрыв, что и у
  каждого предыдущего пакета). Один новый сервис:
  `organization-service` (`Organization`/`CivicSpace`,
  `OrganizationalUnit`, `OrganizationalRelation`,
  `OrganizationalHierarchyOverlapPolicy`,
  `OrganizationalInheritancePolicy`, `OrganizationalAuthority`; ADR-032
  — ADR-037, канон раздел 19e); обязательная миграционная таблица
  `RoleAssignment.scope_id` по всем 12 реальным значениям `role_code`
  (`docs/packs/PACK-08-ROLE-SCOPE-MIGRATION-TABLE.md` — ноль
  заблокированных, ноль неоднозначных); минимальный read-only
  frontend vertical slice `/organizations` (немецкий — авторитетный
  текст, английский — только информационная подпись; статические
  примерные данные, без бэкенда). См.
  `docs/handover/PACK-08-IMPLEMENTATION-REPORT.md` и
  `docs/packs/PACK-08-IMPLEMENTATION.md` для полного описания.
- Repository version: `0.8.0` (CLAUDE-PACK-08 implementation:
  `organization-service` — `Organization`, `CivicSpace`,
  `OrganizationalUnit`, `OrganizationalRelation`,
  `OrganizationalHierarchyOverlapPolicy`,
  `OrganizationalInheritancePolicy`, `OrganizationalAuthority`; см.
  `docs/handover/PACK-08-IMPLEMENTATION-REPORT.md`. Предыдущая версия
  `0.7.0` соответствовала CLAUDE-PACK-07 implementation:
  `membership-service` и расширение `eligibility-service`/
  `identity-service` — `PartyMembershipEligibilityPolicy`, `Membership`,
  `MembershipApplication`, `AffiliationDeclaration`, `ConflictAssessment`,
  `ParticipantEligibilityPolicy`, `ProcessEligibilityPolicy`,
  `StepUpAuthenticationRequirement`, `DigitalDecision`,
  `AssemblyDecision`, `AuthenticationContext`; см.
  `docs/handover/PACK-07-IMPLEMENTATION-REPORT.md`. Предыдущая версия
  `0.6.0` соответствовала CLAUDE-PACK-06 implementation:
  `ai-processing-service` и связанные контракты/тесты —
  `AIProcessingRecord`, `RedactionManifest`, `AIDisclosurePackage` и
  производный read model `DisclosureStatus`; см.
  `docs/handover/PACK-06-REPORT.md`. Версия до неё, `0.5.0`,
  соответствовала CLAUDE-PACK-05 implementation (`governance-service`;
  подтверждено внешним прогоном GitHub Actions, см.
  `docs/handover/PACK-05-REPORT.md`).
- База данных, event bus, аутентификация, deployment, реальная
  eID-интеграция, географическая/избирательная привязка регионов сверх
  организационной модели `organization-service` (PACK-08) пока не
  реализованы.

## Архитектурный принцип

Репозиторий организован как **модульный монорепозиторий** (см.
`docs/adr/ADR-001-repository-strategy.md`):

- каждая каноническая сущность имеет единственного модуля-владельца
  (см. `docs/architecture/data-ownership.md`);
- модули не обращаются напрямую к чужим таблицам или внутренним данным;
- интеграция между будущими сервисами допускается только через
  версионированные API, версионированные события, утверждённые read models
  или audit export;
- shared-пакеты (`packages/`) не содержат бизнес-логики — только
  инфраструктурные типы и утилиты;
- каждый будущий сервис потенциально отделяем в независимый деплой-юнит.

Каноническая доменная модель и обязательные архитектурные инварианты
зафиксированы в `docs/canonical/TZ-00-domain-event-canon.md` и не подлежат
изменению без принятого ADR.

## Требования

- Python 3.12+
- [`uv`](https://docs.astral.sh/uv/) для управления Python workspace и зависимостями
- Node.js 22 LTS
- GNU Make

## Быстрый запуск

```bash
make setup      # установка Python и Node зависимостей
make verify     # полный цикл проверок (repo checks, format, lint, typecheck, tests, build)
```

## Команды Make

| Команда                 | Назначение                                                                       |
| ----------------------- | -------------------------------------------------------------------------------- |
| `make setup`            | установка зависимостей (Python через `uv`, Node через `npm`)                     |
| `make format`           | автоформатирование (Ruff format, Prettier)                                       |
| `make lint`             | Ruff lint + ESLint                                                               |
| `make typecheck`        | mypy + tsc                                                                       |
| `make test`             | все тесты (Python, TypeScript, frontend)                                         |
| `make test-python`      | тесты Python workspace                                                           |
| `make test-typescript`  | тесты TypeScript пакетов                                                         |
| `make test-frontend`    | тесты и smoke test frontend                                                      |
| `make check-repository` | структурные проверки репозитория (обязательные файлы, запрещённые файлы, версии) |
| `make verify`           | полный последовательный прогон всех проверок                                     |
| `make clean`            | удаление сгенерированных артефактов                                              |

## Структура каталогов

```text
epd2-civic-os/
├── docs/                 # канон, архитектура, ADR, отчёты, открытые вопросы
├── contracts/            # будущие контракты: OpenAPI, события, схемы, reason codes
├── services/              # шестнадцать сервисов: account, identity,
│                          # eligibility, credential, audit-core (PACK-02),
│                          # initiative, deliberation, moderation, voting,
│                          # tally, delegation (PACK-03), transparency
│                          # (PACK-04), governance (PACK-05),
│                          # ai-processing (PACK-06), membership (PACK-07),
│                          # organization (PACK-08)
├── packages/
│   ├── python/epd2-core        # общий Python-пакет: версии, идентификаторы
│   └── typescript/epd2-types   # общий TypeScript-пакет: версии
├── frontend/web-shell     # минимальный Next.js frontend-каркас
├── scripts/               # скрипты проверки структуры репозитория
├── tests/repository/      # тесты уровня репозитория
└── .github/               # CI workflow, шаблоны PR и issue
```

## Важное правило: запрет прямого доступа к чужим данным

Ни один модуль (текущий или будущий) не должен:

- читать таблицы другого модуля напрямую;
- изменять чужие данные напрямую;
- использовать общий ORM для всей платформы;
- выполнять межсервисные SQL-запросы.

Подробнее: `docs/architecture/service-boundaries.md`.

## Документация

- Канон: `docs/canonical/TZ-00-domain-event-canon.md`
- Архитектура: `docs/architecture/`
- ADR: `docs/adr/`
- Правила разработки: `docs/development/`
- Открытые вопросы: `docs/review/OPEN_QUESTIONS.md`
- Известные ограничения: `docs/review/KNOWN_LIMITATIONS.md`
- Отчёт по PACK-01: `docs/handover/PACK-01-REPORT.md`
- Отчёт по PACK-02: `docs/handover/PACK-02-REPORT.md`
- Threat model PACK-02: `docs/review/PACK-02-THREAT-MODEL.md`
- Спецификация PACK-03: `docs/handover/PACK-03-SPEC.md`
- Отчёт по PACK-03: `docs/handover/PACK-03-REPORT.md`
- Спецификация PACK-04: `docs/handover/PACK-04-SPEC.md`
- Отчёт по PACK-04: `docs/handover/PACK-04-REPORT.md`
- Спецификация PACK-05: `docs/handover/PACK-05-SPEC.md`
- Отчёт по PACK-05: `docs/handover/PACK-05-REPORT.md`
- Governance ADR (PACK-05): `docs/adr/ADR-016` — `docs/adr/ADR-020`,
  `docs/review/PACK-05-OWNER-DECISIONS.md`
- Спецификация PACK-06: `docs/handover/PACK-06-SPEC.md`
- Отчёт по PACK-06: `docs/handover/PACK-06-REPORT.md`
- AI Processing Context ADR (PACK-06): `docs/adr/ADR-021` —
  `docs/adr/ADR-025`, `docs/review/PACK-06-OWNER-DECISIONS.md`
- Спецификация PACK-07 (финальная, консолидированная):
  `docs/handover/PACK-07-SPEC-FINAL.md` (исходный черновик,
  `docs/handover/PACK-07-SPEC.md`, помечен superseded)
- Participation & Membership Context ADR (PACK-07): `docs/adr/ADR-026`
  — `docs/adr/ADR-031`, `docs/review/PACK-07-OWNER-DECISIONS.md`
- Отчёт о каноническом раунде PACK-07 (canon-only, без реализации
  сервисов): `docs/handover/PACK-07-CANON-AMENDMENT-REPORT.md`
- Отчёт о раунде реализации PACK-07 (`membership-service`, расширение
  `eligibility-service`/`identity-service`):
  `docs/handover/PACK-07-IMPLEMENTATION-REPORT.md`
- Спецификация PACK-08 (Organization & Regional Scope Foundation):
  `docs/packs/PACK-08-SPECIFICATION.md`,
  `docs/packs/PACK-08-MIGRATION-MATRIX.md`,
  `docs/packs/PACK-08-OPEN-DECISIONS.md`
- Organization & Regional Scope Context ADR (PACK-08): `docs/adr/ADR-032`
  — `docs/adr/ADR-037`
- Отчёт о раунде спецификации/ADR PACK-08:
  `docs/handover/PACK-08-SPEC-REPORT.md`
- Отчёт о каноническом раунде PACK-08 (canon-only, без реализации
  сервисов): `docs/handover/PACK-08-CANON-AMENDMENT-REPORT.md`
- Обязательная миграционная таблица `RoleAssignment.scope_id` (PACK-08):
  `docs/packs/PACK-08-ROLE-SCOPE-MIGRATION-TABLE.md`
- Технический справочник по реализации PACK-08 (`organization-service`,
  контракты, frontend vertical slice):
  `docs/packs/PACK-08-IMPLEMENTATION.md`
- Отчёт о раунде реализации PACK-08 (`organization-service`, локальный
  самоотчёт без внешнего прогона GitHub Actions):
  `docs/handover/PACK-08-IMPLEMENTATION-REPORT.md`
- Локальная доверификация (генерация lock-файлов, `next build`): `LOCAL_VERIFICATION.md`
- Одноразовая проверка на GitHub Actions (когда нет доступа к обычной
  среде с интернетом): `GITHUB_ACTIONS_START.md`,
  `.github/workflows/verify-and-package.yml`
- Безопасность: `SECURITY.md`
- Вклад в проект: `CONTRIBUTING.md`

## Текущее ограничение

Реализованы: Account, Identity, Eligibility, Credential, Audit Core
(PACK-02), Initiative, Discussion (Deliberation), Moderation, Voting,
Tally, Delegation (PACK-03), Transparency (PACK-04: `PublicLedgerEntry`,
`AuditExportPackage`, `DisclosurePolicy`, `LobbyLogEntry`), Governance
(PACK-05: `RoleAssignment`, `GovernancePolicy`, `GovernanceDecision`,
`TechnicalChallenge`, производный read model `FinalityStatus`; канон
раздел 19b, ADR-016 — ADR-020) и AI Processing (PACK-06:
`ai-processing-service` — `AIProcessingRecord` с плоскостями
`processing_status`/`human_review_status`, канонический встроенный
`redaction_manifest`, производный read model `DisclosureStatus`,
контрактный объект `AIDisclosurePackage`; канон раздел 19c, ADR-021 —
ADR-025) и Participation & Membership (PACK-07: канон раздел 19d,
ADR-026 — ADR-031, `membership-service` — `PartyMembershipEligibilityPolicy`,
`Membership`, `MembershipApplication`, `AffiliationDeclaration`,
`ConflictAssessment`, переиспользуемый `Appeal`; расширение
`eligibility-service` — `ParticipantEligibilityPolicy`,
`ProcessEligibilityPolicy`, `StepUpAuthenticationRequirement`,
`DigitalDecision`, `AssemblyDecision`, четыре раздельных признака
избирательного права; расширение `identity-service` —
`AuthenticationContext`, восемь новых полей `IdentityRecord`; **PACK-07
PASS**, подтверждено внешним прогоном GitHub Actions, см.
`docs/handover/PACK-07-IMPLEMENTATION-REPORT.md`) и Organization &
Regional Scope (PACK-08: канон раздел 19e, ADR-032 — ADR-037,
`organization-service` — `Organization`/`CivicSpace`,
`OrganizationalUnit`, `OrganizationalRelation`,
`OrganizationalHierarchyOverlapPolicy`, `OrganizationalInheritancePolicy`,
`OrganizationalAuthority`; default-deny региональная scope-авторизация
с шестью режимами доступа, временный надзор, институциональные
полномочия с базовой матрицей несовместимости ролей, обязательная
миграционная таблица `RoleAssignment.scope_id`, минимальный read-only
frontend vertical slice `/organizations`; **локальный самоотчёт, без
внешнего прогона GitHub Actions**, см.
`docs/handover/PACK-08-IMPLEMENTATION-REPORT.md`).
**Ещё не реализованы**: Emergency/Crisis Override, реальная
eID/eIDAS-интеграция, криптографические протоколы голосования,
географическая/избирательная привязка регионов сверх организационной
модели PACK-08 — см. `docs/review/KNOWN_LIMITATIONS.md`.
