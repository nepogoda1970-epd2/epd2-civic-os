# Known Limitations

Состояние репозитория после CLAUDE-PACK-01 (Repository Skeleton) и
CLAUDE-PACK-02 (Identity Separation and Audit Kernel).

## Состояние после CLAUDE-PACK-02

- Реализованы пять сервисов из области PACK-02: `account-service`,
  `identity-service`, `eligibility-service`, `credential-service`,
  `audit-core` (`services/`). Каждый — независимый Python-пакет с
  in-memory reference adapter, без production-базы данных (см. пункт
  ниже). Полностью **отсутствуют**: Organization, Initiative,
  Discussion/Deliberation, Moderation, Voting, Tally, Delegation,
  Transparency, Governance.
- Reason codes (раздел 24 канона) для области PACK-02 теперь
  представлены исполняемым, машинно-читаемым реестром
  (`contracts/reason-codes/pack-02.yml`, загружается через
  `epd2_core.reason_codes.ReasonCodeRegistry`), а не только
  документацией — 22 канонических кода плюс 21 дополнительный
  (`docs/adr/ADR-004-reason-code-registry.md`).
- `contracts/schemas/` и `contracts/events/` заполнены для области
  PACK-02 (8 JSON Schema сущностей, 6 event payload схем) плюс
  `contracts/openapi/pack-02.yaml`. Для будущих контуров (Voting,
  Delegation, Moderation, Organization, Initiative, Discussion,
  Governance) схемы пока не существуют.
- Audit Core (`services/audit-core`) реализует append-only,
  hash-chained `AuditEvent` (INV-04/INV-05), но **не** является
  production-grade blockchain или qualified electronic evidence (пакет,
  раздел 9.2) — однопроцессный, in-memory, без криптографической подписи
  и без внешнего anchoring. См. `docs/review/PACK-02-THREAT-MODEL.md`
  (угроза 9 — "event tampering") для полного разбора остаточного риска.
- Идентичность и участие разделены структурно (INV-01) — см.
  `docs/architecture/identity-participation-separation.md` — но это
  opaque credential reference implementation (пакет, раздел 6): нет
  blind signatures, zero-knowledge proofs или иной криптографической
  анонимности; unlinkability проверяется только на уровне отсутствия
  общих идентификаторов полей, а не криптографически. Корреляция через
  таймстемпы между сервисами не смягчается (см. угрозу 4 в
  `docs/review/PACK-02-THREAT-MODEL.md`).
- Структурированное логирование (пакет, раздел 13.2) не подключено ни
  в одном из пяти сервисов — ни один сервис не эмитит логи вообще на
  этом этапе, поэтому запрет на логирование PII (раздел 13.1) сейчас
  обеспечивается отсутствием логирования, а не проверенным механизмом
  (см. угрозу 3 в `docs/review/PACK-02-THREAT-MODEL.md`).
- Идемпотентность на уровне команды (caller-supplied `event_id`)
  реализована только в
  `epd2_credential_service.application.issue_participation_credential`;
  остальные аналогичные команды пока не принимают этот параметр (см.
  `docs/review/OPEN_QUESTIONS.md`, пункт 11).
- CT-00-11 (AIProcessingRecord human-control gate) и CT-00-12
  (EmergencyAction forbidden-during-freeze) явно отмечены как not
  applicable in PACK-02 (`tests/contract/test_ct00_11_12_not_applicable.py`),
  не как passed — обе сущности вне scope пакета (раздел 3.2).

## Состояние, унаследованное от CLAUDE-PACK-01 (без изменений в PACK-02)

- Отсутствует база данных (PostgreSQL или любая другая) для любого
  сервиса. Ни одна каноническая сущность не персистится за пределами
  процесса — все пять PACK-02 сервисов используют in-memory reference
  adapters (пакет, раздел 4.1 это прямо допускает: "Production database
  в PACK-02 не требуется").
- Отсутствует event bus (NATS, Kafka, RabbitMQ или иной). Стандарт события
  (раздел 21 канона) реализован программно как canonical event envelope
  (`epd2_core.event_envelope`), но без реальной шины/транспорта.
- Отсутствует authentication, authorization (в проверяемом
  production-смысле — `actor_is_authorized` в PACK-02 — булев input
  параметр команды, а не настоящая auth-система), MFA, eID-интеграция.
- Отсутствует deployment: нет Docker, Docker Compose, Kubernetes, Terraform,
  production-инфраструктуры.
- Отсутствует production security review — `SECURITY.md` и
  `docs/review/PACK-02-THREAT-MODEL.md` фиксируют текущий, не
  production, уровень анализа.
- Frontend (`frontend/web-shell`) — это только минимальный Next.js
  skeleton: без API, без login, без форм, без политического контента, без
  сторонних UI-библиотек, без аналитики, без cookies, без внешних шрифтов;
  не подключён ни к одному из пяти PACK-02 сервисов.
- ТЗ-00 подключено к репозиторию как документационная зависимость
  (`docs/canonical/TZ-00-domain-event-canon.md`); для области PACK-02
  она дополнена машинно-проверяемыми JSON Schema
  (`contracts/schemas/`, `contracts/events/`) — см. выше.
- `CODEOWNERS` содержит placeholder-псевдонимы, не привязанные к реальным
  GitHub-пользователям или командам (см.
  `docs/review/OPEN_QUESTIONS.md`, пункт 3).
- Лицензия проекта не выбрана — `LICENSE` содержит временную заглушку (см.
  `docs/review/OPEN_QUESTIONS.md`, пункт 1).
- `uv.lock` и `package-lock.json` **присутствуют** и являются подлинными,
  сгенерированными инструментами файлами (не написаны вручную). Они были
  созданы через `.github/workflows/verify-and-package.yml` — одноразовый
  workflow (`workflow_dispatch`) на GitHub Actions с обычным доступом в
  интернет, — потому что исполнительная песочница, в которой изначально
  собирался этот пакет, блокирует сетевой доступ к `pypi.org` /
  `files.pythonhosted.org` / `registry.npmjs.org` (egress policy возвращает
  `403 host_not_allowed`) и не может выполнить `uv lock` / `npm install`
  напрямую. См. `docs/handover/PACK-01-REPORT.md` (Revision 4) для полной
  истории, контрольных сумм и результатов повторной проверки.
- Артефакт, полученный из этого workflow, при первой передаче содержал
  повреждения (переформатированный `docs/canonical/TZ-00-domain-event-canon.md`
  и пять обнулённых файлов governance/CI) из-за отсутствующего в нём
  `.prettierignore`. Повреждения были обнаружены построчным сравнением,
  канонический файл и governance-файлы восстановлены из исходного
  состояния репозитория, после чего полный набор офлайн-проверок повторно
  пройден на восстановленном дереве. Подробности и рекомендация по
  усилению `scripts/check_repository.py` (см. `docs/review/OPEN_QUESTIONS.md`,
  пункт 8) — в `docs/handover/PACK-01-REPORT.md`.
- `packages/typescript/epd2-types` и `frontend/web-shell` собраны и
  протестированы штатным `npm install` + `next build` на GitHub Actions
  (см. `docs/handover/PACK-01-VERIFICATION.log`) — вне этой песочницы,
  которая не имеет сетевого доступа для повторного запуска той же сборки
  локально. Восстановление governance-файлов и канона не затрагивает ни
  TypeScript-код, ни конфигурацию сборки, поэтому результаты сборки
  остаются в силе после исправления (см. Revision 4 отчёта).
