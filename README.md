# EPD² Civic OS

## Назначение репозитория

EPD² Civic OS — открытая цифровая инфраструктура для гражданского и партийного
участия: идентификация, допуск, участие, обсуждение, голосование и проверяемая
публичная документация решений.

Настоящий репозиторий реализует **CLAUDE-PACK-01 — Repository Skeleton**,
**CLAUDE-PACK-02 — Identity Separation and Audit Kernel** и
**CLAUDE-PACK-03 — Participation and Decision Kernel**: стартовый
монорепо-каркас платформы плюс одиннадцать независимых сервисов —
account, identity, eligibility, credential, audit-core (PACK-02, участие
и идентичность структурно разделены, каждое критическое действие
записывается в append-only, hash-chained журнал аудита) и initiative,
deliberation, moderation, voting, tally, delegation (PACK-03, полный
цикл гражданской инициативы, обсуждения, модерации, голосования, подсчёта
и делегирования). Остальная бизнес-логика (публичная прозрачность,
governance, AI-обработка, emergency actions) пока не реализована — см.
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
- Этап: governance для CLAUDE-PACK-04 (Transparency Context) —
  ADR-011–015 приняты (ADR-013/015 — с поправками), канон дополнен под
  ADR-013: новый раздел 19a (`PublicLedgerEntry`, `AuditExportPackage`,
  `DisclosurePolicy`, `LobbyLogEntry`), раздел 20.14 (события
  прозрачности), четыре новые строки матрицы владения (раздел 22).
  Реализация `transparency-service` ещё не начата — это исключительно
  каноническое дополнение. См.
  `docs/handover/PACK-04-SPEC.md`,
  `docs/adr/ADR-013-canon-0.3.0-transparency-context-additions.md`,
  `docs/review/PACK-04-OWNER-DECISIONS.md`.
- Canon version: `0.3.0` (`docs/canonical/TZ-00-domain-event-canon.md`).
  Изменения текста канона: PACK-03 под ADR-010 (`0.1.0 → 0.2.0`,
  добавление `Ballot.challenge_window_hours` /
  `ResultPublication.challenge_deadline_at`); CLAUDE-PACK-04 governance
  под ADR-013 (`0.2.0 → 0.3.0`, раздел 19a Transparency Context).
- Repository version: `0.3.0` (не изменена этим канон-обновлением —
  сервисного кода PACK-04 ещё нет).
- База данных, event bus, аутентификация, deployment,
  `transparency-service` (реализация), governance и AI-обработка пока не
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
├── services/              # одиннадцать сервисов: account, identity,
│                          # eligibility, credential, audit-core (PACK-02),
│                          # initiative, deliberation, moderation, voting,
│                          # tally, delegation (PACK-03)
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
- Локальная доверификация (генерация lock-файлов, `next build`): `LOCAL_VERIFICATION.md`
- Одноразовая проверка на GitHub Actions (когда нет доступа к обычной
  среде с интернетом): `GITHUB_ACTIONS_START.md`,
  `.github/workflows/verify-and-package.yml`
- Безопасность: `SECURITY.md`
- Вклад в проект: `CONTRIBUTING.md`

## Текущее ограничение

Реализованы: Account, Identity, Eligibility, Credential, Audit Core
(PACK-02) и Initiative, Discussion (Deliberation), Moderation, Voting,
Tally, Delegation (PACK-03). **Ещё не реализованы**: Organization,
Transparency, Governance, AI-обработка, Emergency/Crisis Override — см.
`docs/review/KNOWN_LIMITATIONS.md`.
