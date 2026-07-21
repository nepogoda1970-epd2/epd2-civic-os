# Known Limitations

Состояние репозитория после CLAUDE-PACK-01 — Repository Skeleton.

- Отсутствуют бизнес-сервисы: Account, Identity, Eligibility, Credential,
  Organization, Initiative, Discussion/Deliberation, Moderation, Voting,
  Tally, Delegation, Transparency, Governance, Audit Core. `services/`
  содержит только заготовку каталога.
- Отсутствует база данных (PostgreSQL или любая другая). Ни одна
  каноническая сущность не персистится.
- Отсутствует event bus (NATS, Kafka, RabbitMQ или иной). Стандарт события
  (раздел 21 канона) задокументирован, но не реализован программно.
- Отсутствует authentication, authorization, MFA, eID-интеграция.
- Отсутствует deployment: нет Docker, Docker Compose, Kubernetes, Terraform,
  production-инфраструктуры.
- Отсутствует production security review — `SECURITY.md` фиксирует только
  базовые правила текущего инфраструктурного этапа.
- Frontend (`frontend/web-shell`) — это только минимальный Next.js
  skeleton: без API, без login, без форм, без политического контента, без
  сторонних UI-библиотек, без аналитики, без cookies, без внешних шрифтов.
- Reason codes (раздел 24 канона) пока представлены только как
  документация (`contracts/reason-codes/README.md`) — исполняемый enum
  будет создан в отдельном пакете, когда появится модуль, который реально
  их использует.
- ТЗ-00 подключено к репозиторию как документационная зависимость
  (`docs/canonical/TZ-00-domain-event-canon.md`), а не как машинно-
  проверяемая полная схема (JSON Schema / Pydantic-модели для всех
  канонических сущностей); `contracts/schemas/` и `contracts/events/`
  пока пусты (только `.gitkeep`) и будут заполняться по мере реализации
  соответствующих модулей.
- `CODEOWNERS` содержит placeholder-псевдонимы, не привязанные к реальным
  GitHub-пользователям или командам (см.
  `docs/review/OPEN_QUESTIONS.md`, пункт 3).
- Лицензия проекта не выбрана — `LICENSE` содержит временную заглушку (см.
  `docs/review/OPEN_QUESTIONS.md`, пункт 1).
- `uv.lock` и `package-lock.json` **отсутствуют**. Исполнительная песочница,
  в которой собирался этот пакет, блокирует сетевой доступ к
  `pypi.org` / `files.pythonhosted.org` / `registry.npmjs.org` (egress
  policy возвращает `403 host_not_allowed`), поэтому `uv lock` и
  `npm install` не могут быть выполнены и зафиксированы в этой среде.
  Оба lock-файла должны быть сгенерированы разработчиком или CI-машиной с
  обычным доступом к сети (`uv lock`, затем `npm install`) при первом
  реальном использовании репозитория. См.
  `docs/handover/PACK-01-REPORT.md` (раздел "Deviations") для полной
  информации и точных сообщений об ошибке.
- По той же причине пакет `packages/typescript/epd2-types` и
  `frontend/web-shell` не были собраны/протестированы через штатный
  `npm install` + `next build` в этой песочнице; `next` нигде не доступен
  офлайн. Frontend-код написан и проверен доступными локальными средствами
  (глобально установленные `tsc`/`tsx`/`prettier`), но полноценная сборка
  Next.js не подтверждена в этой среде — только в реальном CI/дев-окружении
  с доступом к npm registry (см. `.github/workflows/ci.yml`, который
  выполняется на инфраструктуре GitHub с полным доступом в интернет).
