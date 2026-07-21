# EPD² Civic OS

## Назначение репозитория

EPD² Civic OS — открытая цифровая инфраструктура для гражданского и партийного
участия: идентификация, допуск, участие, обсуждение, голосование и проверяемая
публичная документация решений.

Настоящий репозиторий реализует **CLAUDE-PACK-01 — Repository Skeleton**:
стартовый монорепо-каркас платформы. Бизнес-логика отдельных доменных сервисов
на этом этапе не реализована — см. `docs/review/KNOWN_LIMITATIONS.md`.

## Статус проекта

- Этап: infrastructure skeleton (CLAUDE-PACK-01).
- Canon version: `0.1.0` (`docs/canonical/TZ-00-domain-event-canon.md`).
- Repository version: `0.1.0`.
- Бизнес-сервисы, база данных, event bus, аутентификация и deployment пока не
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
├── services/             # заготовка для будущих бизнес-сервисов (пока пусто)
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
- Локальная доверификация (генерация lock-файлов, `next build`): `LOCAL_VERIFICATION.md`
- Безопасность: `SECURITY.md`
- Вклад в проект: `CONTRIBUTING.md`

## Текущее ограничение

Бизнес-модули (Identity, Eligibility, Credential, Organization, Initiative,
Discussion, Moderation, Voting, Tally, Delegation, Transparency, Governance,
Audit Core) **ещё не реализованы**. Этот пакет создаёт только
инфраструктурный каркас репозитория.
