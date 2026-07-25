# EPD² Civic OS

## Назначение репозитория

EPD² Civic OS — открытая цифровая инфраструктура для гражданского и партийного
участия: идентификация, допуск, участие, обсуждение, голосование и проверяемая
публичная документация решений.

Настоящий репозиторий реализует **CLAUDE-PACK-01 — Repository Skeleton**,
**CLAUDE-PACK-02 — Identity Separation and Audit Kernel**,
**CLAUDE-PACK-03 — Participation and Decision Kernel**,
**CLAUDE-PACK-04 — Transparency Context**,
**CLAUDE-PACK-05 — Governance Context** и
**CLAUDE-PACK-06 — AI Processing Context**: стартовый
монорепо-каркас платформы плюс четырнадцать независимых сервисов —
account, identity, eligibility, credential, audit-core (PACK-02, участие
и идентичность структурно разделены, каждое критическое действие
записывается в append-only, hash-chained журнал аудита), initiative,
deliberation, moderation, voting, tally, delegation (PACK-03, полный
цикл гражданской инициативы, обсуждения, модерации, голосования, подсчёта
и делегирования), transparency-service (PACK-04, публичный реестр,
audit export, политика раскрытия данных, реестр лоббистских контактов),
governance-service (PACK-05, роли участников, политики и решения органов
управления, технические оспаривания и производный статус финальности
результатов голосования) и ai-processing-service (PACK-06,
`AIProcessingRecord` с двумя независимыми статусными плоскостями,
канонический встроенный `redaction_manifest`, производный
`DisclosureStatus`, `AIDisclosurePackage`, шесть закрытых классов
использования и обязательный протокол раскрытия — ИИ остаётся строго
консультативным и никогда не получает полномочий на автономную мутацию
Civic OS). Остальная бизнес-логика (emergency actions) пока не
реализована — см. `docs/review/KNOWN_LIMITATIONS.md`.

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
- Canon version: `0.6.0` (`docs/canonical/TZ-00-domain-event-canon.md`).
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
  изменение: ни `membership-service`, ни расширение `eligibility-service`
  ещё не реализованы.
- Repository version: `0.6.0` (CLAUDE-PACK-06 implementation:
  `ai-processing-service` и связанные контракты/тесты —
  `AIProcessingRecord`, `RedactionManifest`, `AIDisclosurePackage` и
  производный read model `DisclosureStatus`; см.
  `docs/handover/PACK-06-REPORT.md`). Предыдущая версия `0.5.0`
  соответствовала CLAUDE-PACK-05 implementation (`governance-service`;
  подтверждено внешним прогоном GitHub Actions, см.
  `docs/handover/PACK-05-REPORT.md`). **Не изменена** CLAUDE-PACK-07's
  канон-только раундом выше — `membership-service` не существует,
  расширение `eligibility-service` не начато; следующий repository-side
  bump произойдёт только при реализации того и другого, per этот проект
  установленную практику (см.
  `docs/handover/PACK-07-CANON-AMENDMENT-REPORT.md`).
- База данных, event bus, аутентификация, deployment,
  `membership-service` и расширение `eligibility-service` пока не
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
├── services/              # четырнадцать сервисов: account, identity,
│                          # eligibility, credential, audit-core (PACK-02),
│                          # initiative, deliberation, moderation, voting,
│                          # tally, delegation (PACK-03), transparency
│                          # (PACK-04), governance (PACK-05),
│                          # ai-processing (PACK-06)
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
ADR-025). Канонический раунд принят для Participation & Membership
(PACK-07: канон раздел 19d, ADR-026 — ADR-031, десять новых сущностей,
восемь новых полей `IdentityRecord`), но **ещё не реализован** —
`membership-service` не существует, расширение `eligibility-service` не
начато. **Ещё не реализованы**: Organization, Emergency/Crisis
Override, `membership-service`, расширение `eligibility-service` — см.
`docs/review/KNOWN_LIMITATIONS.md`.
