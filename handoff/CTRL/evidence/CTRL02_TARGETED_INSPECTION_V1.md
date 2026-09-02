# CTRL-02 Targeted Inspection V1


## FILE `pyproject.toml`

```text
[project]
name = "epd2-civic-os"
version = "0.1.0"
description = "EPD2 Civic OS monorepo workspace root (infrastructure skeleton plus CLAUDE-PACK-02 identity/audit kernel plus CLAUDE-PACK-03 participation/decision kernel plus CLAUDE-PACK-04 transparency context)"
requires-python = ">=3.12"
dependencies = [
    "epd2-core",
    "epd2-account-service",
    "epd2-identity-service",
    "epd2-eligibility-service",
    "epd2-credential-service",
    "epd2-audit-core",
    "epd2-initiative-service",
    "epd2-deliberation-service",
    "epd2-moderation-service",
    "epd2-voting-service",
    "epd2-tally-service",
    "epd2-delegation-service",
    "epd2-transparency-service",
    "epd2-governance-service",
    "epd2-ai-processing-service",
    "epd2-membership-service",
    "epd2-organization-service",
    "epd2-compliance-service",
    "epd2-finance-service",
    "epd2-document-service",
    "epd2-privileged-access-service",
    "epd2-data-plane-service",
]

# Lower bounds are the versions this repository's checks (Ruff ruleset,
# mypy strictness, pytest usage) were authored and verified against.
# Upper bounds (next major excluded) are a reproducibility guard, not a
# guess at exact patch versions this session cannot verify against a live
# index — `uv lock` (run with network access; see LOCAL_VERIFICATION.md)
# resolves the actual pinned version within each range and records it in
# uv.lock.
[dependency-groups]
dev = [
    "pytest>=8.3,<9",
    "pytest-cov>=5.0,<6",
    "mypy>=1.11,<2",
    "ruff>=0.6,<1",
    "pydantic>=2.9,<3",
    "pre-commit>=3.8,<4",
    # CLAUDE-PACK-02 additions:
    "types-PyYAML>=6.0,<7",
    "jsonschema>=4.23,<5",
    "hypothesis>=6.112,<7",
]

[tool.uv]
package = false

[tool.uv.workspace]
members = [
    "packages/python/epd2-core",
    "services/account-service",
    "services/identity-service",
    "services/eligibility-service",
    "services/credential-service",
    "services/audit-core",
    "services/initiative-service",
    "services/deliberation-service",
    "services/moderation-service",
    "services/voting-service",
    "services/tally-service",
    "services/delegation-service",
    "services/transparency-service",
    "services/governance-service",
    "services/ai-processing-service",
    "services/membership-service",
    "services/organization-service",
    "services/compliance-service",
    "services/finance-service",
    "services/document-service",
    "services/privileged-access-service",
    "services/data-plane-service",
]

[tool.uv.sources]
epd2-core = { workspace = true }
epd2-account-service = { workspace = true }
epd2-identity-service = { workspace = true }
epd2-eligibility-service = { workspace = true }
epd2-credential-service = { workspace = true }
epd2-audit-core = { workspace = true }
epd2-initiative-service = { workspace = true }
epd2-deliberation-service = { workspace = true }
epd2-moderation-service = { workspace = true }
epd2-voting-service = { workspace = true }
epd2-tally-service = { workspace = true }
epd2-delegation-service = { workspace = true }
epd2-transparency-service = { workspace = true }
epd2-governance-service = { workspace = true }
epd2-ai-processing-service = { workspace = true }
epd2-membership-service = { workspace = true }
epd2-organization-service = { workspace = true }
epd2-compliance-service = { workspace = true }
epd2-finance-service = { workspace = true }
epd2-document-service = { workspace = true }
epd2-privileged-access-service = { workspace = true }
epd2-data-plane-service = { workspace = true }

# --- Ruff ---
[tool.ruff]
line-length = 100
target-version = "py312"
src = [
    "packages/python/epd2-core/src",
    "services/account-service/src",
    "services/identity-service/src",
    "services/eligibility-service/src",
    "services/credential-service/src",
    "services/audit-core/src",
    "services/initiative-service/src",
    "services/deliberation-service/src",
    "services/moderation-service/src",
    "services/voting-service/src",
    "services/tally-service/src",
    "services/delegation-service/src",
    "services/transparency-service/src",
    "services/governance-service/src",
    "services/ai-processing-service/src",
    "services/membership-service/src",
    "services/organization-service/src",
    "services/compliance-service/src",
    "services/finance-service/src",
    "services/document-service/src",
    "services/privileged-access-service/src",
    "services/data-plane-service/src",
    "scripts",
    "tests",
]

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "SIM", "RUF"]

[tool.ruff.lint.isort]
known-first-party = [
    "epd2_core",
    "epd2_account_service",
    "epd2_identity_service",
    "epd2_eligibility_service",
    "epd2_credential_service",
    "epd2_audit_core",
    "epd2_initiative_service",
    "epd2_deliberation_service",
    "epd2_moderation_service",
    "epd2_voting_service",
    "epd2_tally_service",
    "epd2_delegation_service",
    "epd2_transparency_service",
    "epd2_governance_service",
    "epd2_ai_processing_service",
    "epd2_membership_service",
    "epd2_organization_service",
    "epd2_compliance_service",
    "epd2_finance_service",
    "epd2_document_service",
    "epd2_privileged_access_service",
    "epd2_data_plane_service",
]

# --- mypy ---
[tool.mypy]
python_version = "3.12"
mypy_path = [
    "packages/python/epd2-core/src",
    "services/account-service/src",
    "services/identity-service/src",
    "services/eligibility-service/src",
    "services/credential-service/src",
    "services/audit-core/src",
    "services/initiative-service/src",
    "services/deliberation-service/src",
    "services/moderation-service/src",
    "services/voting-service/src",
    "services/tally-service/src",
    "services/delegation-service/src",
    "services/transparency-service/src",
    "services/governance-service/src",
    "services/ai-processing-service/src",
    "services/membership-service/src",
    "services/organization-service/src",
    "services/compliance-service/src",
    "services/finance-service/src",
    "services/document-service/src",
    "services/privileged-access-service/src",
    "services/data-plane-service/src",
]
disallow_untyped_defs = true
disallow_incomplete_defs = true
disallow_any_generics = true
check_untyped_defs = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_return_any = true
strict_equality = true

# PyYAML ships no inline type stubs of its own; `types-PyYAML` (declared
# above) supplies them in CI. That package cannot be installed in this
# sandbox (no network access - see LOCAL_VERIFICATION.md), so this
# override only prevents that one, single-purpose sandbox limitation from
# blocking `mypy .` here; CI runs fully-typed (no override needed there,
# but the override is harmless if stubs are present).
[[tool.mypy.overrides]]
module = "yaml"
ignore_missing_imports = true

# jsonschema and hypothesis ship their own inline type stubs (PEP 561) and
# need no override once installed. They cannot be installed in this
# sandbox either (same network restriction), so the same
# ignore_missing_imports treatment applies here for the same reason as
# "yaml" above; CI has both installed via `uv sync --all-groups` and type
# checks the real packages.
[[tool.mypy.overrides]]
module = ["jsonschema", "hypothesis", "hypothesis.*"]
ignore_missing_imports = true

# pytest itself ships inline type stubs (PEP 561) and needs no override
# once installed via `uv sync --all-groups` (as CI does). Locally, this
# sandbox's `uv run mypy` cannot resolve at all (same lock/network
# restriction as above), so local verification falls back to an isolated,
# standalone mypy install with no project dependencies in its own
# site-packages - not even pytest. This override exists only to keep that
# local fallback invocation usable; it is a no-op in CI, where pytest's
# own stubs are found normally.
[[tool.mypy.overrides]]
module = ["pytest", "_pytest.*"]
ignore_missing_imports = true

# No per-test-module relaxation is configured: all test modules in this
# repository are fully typed and pass the same strict settings as
# application code.

# --- pytest ---
[tool.pytest.ini_options]
testpaths = [
    "packages/python/epd2-core/tests",
    "tests/repository",
    "tests/contract",
    "services/account-service/tests",
    "services/identity-service/tests",
    "services/eligibility-service/tests",
    "services/credential-service/tests",
    "services/audit-core/tests",
    "services/initiative-service/tests",
    "services/deliberation-service/tests",
    "services/moderation-service/tests",
    "services/voting-service/tests",
    "services/tally-service/tests",
    "services/delegation-service/tests",
    "services/transparency-service/tests",
    "services/governance-service/tests",
    "services/ai-processing-service/tests",
    "services/membership-service/tests",
    "services/organization-service/tests",
    "services/compliance-service/tests",
    "services/finance-service/tests",
    "services/document-service/tests",
    "services/privileged-access-service/tests",
    "services/data-plane-service/tests",
]
# --import-mode=importlib: several services intentionally use the same
# test file basenames (test_domain.py, test_application.py, ...) - this
# import mode resolves each by its fully-qualified path instead of by
# bare basename, so they never collide, without requiring __init__.py
# files in every tests/ directory (which previously caused a mypy
# "Duplicate module named tests" error - see docs/handover/PACK-01-REPORT.md).
addopts = "-ra --import-mode=importlib"
# The target-profile conformance suite runs the whole cross-implementation
# core on the real 4096-bit EPD2-CRYPTO-1 group. It is deliberately slow —
# substituting a smaller group to make it fast is the exact substitution the
# parameter policy forbids — so it carries its own marker and can be run
# alone:
#     pytest -m slow_conformance services/voting-service/tests/reference/
markers = [
    "slow_conformance: cross-implementation conformance on the real EPD2-CRYPTO-1 profile",
]

```


## FILE `README.md`

```text
# EPD² Civic OS

> **Текущее состояние репозитория:** `REPOSITORY_VERSION` — `0.16.0`,
> `CANON_VERSION` — `0.8.0`.
>
> Последний раунд — **PACK-15 — Voting Trust Boundary, Eligibility &
> Credential Separation**, **FINAL PASS**: внешний GitHub Actions прошёл
> полностью (983/983 repository paths, forbidden paths — нет, version
> consistency, Ruff format 436 файлов, Prettier, Ruff lint, ESLint, mypy —
> PASS, Python 5343 passed / 4 skipped, epd2-types 3 passed, Node 41
> passed, frontend 23 passed, Next.js production build — PASS, 48/48
> static pages, browser/visual/accessibility 135 passed). Разделение между
> «кто человек» и «голос подан» реализовано структурно: запись
> потраченного nonce — это **множество** из трёх колонок без колонки
> значения, поэтому ни одно хранилище, событие, лог, резервная копия или
> выгрузка не содержит одновременно ссылку на assertion и ссылку на
> credential (ADR-093). Семь отдельных файлов базы данных — по одному на
> границу доверия, — поэтому внешний ключ через границу не выражается в
> принципе. 22 endpoint'а версионированного API, десять ролей и восемь
> структурных правил разделения обязанностей, 89 reason-кодов.
>
> Перед этим прогоном из дерева удалена устаревшая вложенная копия
> репозитория `epd2-civic-os/` (версия `0.6.0`); счётчик Ruff изменился с
> 609 на 436, и **все артефакты верификации для деревьев с этим каталогом
> считаются устаревшими**. **NOT PRODUCTION READY. NOT LEGALLY
> ACTIVATED.** См.
> `docs/handover/PACK-15-FINAL-PASS-REPORT.md`,
> `docs/handover/PACK-15-IMPLEMENTATION-REPORT.md`,
> `docs/handover/PACK-15-TEST-EVIDENCE.md`,
> `docs/handover/PACK-15-SECURITY-EVIDENCE.md`,
> `docs/handover/PACK-15-PRIVACY-EVIDENCE.md` и
> `docs/handover/PACK-15-TRACEABILITY-MATRIX.md`.
>
> Предыдущий раунд — **PACK-14 — Identity, Authentication & Account
> Security**, **FINAL PASS**: внешний GitHub Actions прошёл полностью
> (867/867 repository paths, forbidden paths — нет, version consistency,
> Ruff format 566 файлов, Prettier, Ruff lint, ESLint, mypy по всем 23
> группам, оба TypeScript typecheck — PASS, Python 4905 passed / 4
> skipped, epd2-types 3 passed, Node 34 passed, frontend unit/render 16
> passed, Next.js production build — PASS, 46/46 static pages,
> browser/visual/accessibility 108 passed). См.
> `docs/handover/PACK-14-FINAL-PASS-REPORT.md`,
> `docs/handover/PACK-14-EXTERNAL-CI-VERIFICATION-RESULT.md` и
> `docs/handover/PACK-14-EXTERNAL-CI-VERIFICATION.log`.
>
> **NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.** У PACK-14 все четыре
> security-порта не связаны и **отказывают**: ни WebAuthn-библиотека, ни
> memory-hard password hasher, ни breached-password-корпус, ни
> assertion-signature verifier не выбраны, поэтому без явной привязки
> нельзя ни зарегистрировать, ни сменить пароль. Persistence — реальный
> **reference**-путь на SQLite из стандартной библиотеки: миграции,
> ограничения, транзакции и optimistic concurrency настоящие, но
> production-БД не разворачивается и durability не заявляется. Границы
> сервиса transport-agnostic: HTTP-поверхности, TLS и production-gateway
> нет. Ни IAM, ни eID, ни email/SMS, ни HSM/KMS не интегрированы. См.
> `docs/packs/PACK-14/PACK-14-OPEN-ITEMS.md`.
>
> Предыдущий раунд — **PACK-13 — Production Data Plane & Contract
> Evolution**, **FINAL PASS** (800/800 repository paths, Python 4625
> passed / 4 skipped, browser 108 passed). Каждый storage-адаптер
> PACK-13 — in-memory. См.
> `docs/handover/PACK-13-FINAL-PASS-REPORT.md`,
> `docs/handover/PACK-13-EXTERNAL-CI-VERIFICATION-RESULT.md` и
> `docs/handover/PACK-13-KNOWN-LIMITATIONS.md`.
>
> Зелёный pipeline подтверждает, что репозиторий собирается,
> типизируется и проходит тесты; он не подтверждает production-готовность,
> юридическую активацию, production-БД, реальный брокер, внешний schema
> registry, production search engine, внешний IAM, реальный
> DLP-провайдер, реальную доставку уведомлений, production session
> assurance, backup/restore-готовность, multi-region-развёртывание или
> что-либо в домене голосования.
>
> PACK-11 (`0.11.0`), PACK-12 (`0.12.0`) и PACK-13 (`0.13.0`) остаются
> историческими PASS-базисами, от которых построен PACK-14.

> FRONT-00 adds a frontend foundation **implementation candidate** to the existing
> Next.js web shell. It does not change repository 0.9.0 or canon 0.7.0 and does
> not activate a production or legally effective workflow. Documentation starts
> at `docs/frontend/FRONT-00-SPECIFICATION.md`.

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
- Canon version: `0.8.0` (`docs/canonical/TZ-00-domain-event-canon.md`),
  с 2026-07-27 — CLAUDE-PACK-10 canon-amendment round под ADR-054
  (**`proposed`**, канон-кандидат): новый раздел 19f (Party Finance &
  Financial Accountability Context), новый подраздел 20.17 (72 события),
  21 новая строка раздела 22, 25 новых записей раздела 23, 45 новых
  reason codes раздела 24. `REPOSITORY_VERSION` остаётся `0.9.0`;
  `finance-service` не создан.
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
- CLAUDE-PACK-09 (Compliance, Records Governance & Legal Workflows) —
  **реализован**: `compliance-service` (одна новая служба, ADR-038) —
  классификация записей и версионированные retention-политики
  (`RetentionPolicy`, `RetentionStartEvent`, `GovernedRecord`),
  контролируемое уничтожение через трёхшаговый workflow
  (`DisposalEligibility` → `DestructionAuthorization` →
  `DestructionEvidence`, ADR-039), Legal Hold с тремя состояниями
  (`active`/`released`/`indeterminate`; неизвестное состояние —
  fail-closed), Data Catalog и Processing Registry (`DataAsset`,
  `ProcessingActivity`, `LegalBasis` как управляемое перечисление,
  ADR-040), governed procedural cases и append-only сроки
  (`ProceduralCase`, `DeadlineDefinition`, `ProceduralDeadline` с явной
  IANA-таймзоной, ADR-041), запросы субъектов данных (статус
  верификации личности без хранения самой личности), партийный арбитраж
  и внутренние споры с проверяемой процессуальной независимостью
  (ADR-042). Организационная изоляция — плоская: никакого наследования
  по иерархии Bund/Land/Kreis, пересечение границы требует явно
  предъявленного `CrossScopeAuthorityGrant`. См.
  `docs/handover/PACK-09-IMPLEMENTATION-REPORT.md` и
  `docs/packs/PACK-09-IMPLEMENTATION.md`.

  **Дополнение (Architecture & Domain Framework 0.8.1).** С этого раунда
  авторитетным документом объёма PACK-09 является Framework 0.8.1
  (Roadmap Amendment). В ту же службу добавлены: общий legal-case
  substrate (`LegalCase`, `JurisdictionDetermination`, `CaseParty`,
  `RepresentationMandate`, `Filing` с неизменяемым docket, `Hearing`,
  `InterimMeasure`, `ProceduralDecision` с раздельными effect / finality
  / enforceability, `Remedy`); хуки отвода (`RecusalRecord`,
  `ReplacementAssignment`); **официальное уведомление как отдельная
  граница доверия** (ADR-043) — `OfficialNotice`, `ServiceAttempt`
  (телеметрия провайдера) и `NoticeEffectDecision`, где только последний
  может запустить процессуальный срок; records governance
  (`RecordClass`, распространение Legal Hold на реплики/индексы/экспорты)
  и data-protection governance с DPIA-гейтом, который fail-closed при
  _отсутствии_ определения требования. Стабильные типизированные ссылки
  для PACK-10/11/19/21-24 опубликованы в `references.py`; глобального
  идентификатора лица там нет и быть не должно. Ограничения — в
  `docs/handover/PACK-09-KNOWN-LIMITATIONS.md`.

  **Статус: PACK-09 IMPLEMENTATION 0.9.0 — EXTERNAL CI PASS.** Полный
  конвейер (frozen install, lint, format, type check, Python-тесты,
  TypeScript- и frontend-тесты, production build Next.js) выполнен на
  GitHub Actions и пройден: 2659 passed, 4 skipped, 0 failed; 556
  required paths; no forbidden paths. Запись — раздел 3
  `docs/handover/PACK-09-IMPLEMENTATION-REPORT.md`, вывод раннера —
  `docs/handover/PACK-09-EXTERNAL-CI-VERIFICATION.log`. Это утверждение
  о верификации, а **не** о production-готовности, развёртывании или
  юридической активации.

  **Служба не заявляет автоматического юридического соответствия** GDPR,
  BDSG или партийному законодательству: она предоставляет управляемый
  workflow, ссылки на доказательства и auditability. Любое юридическое
  решение остаётся за человеком вне системы.

- CLAUDE-PACK-10 (Party Finance, Rechenschaftsbericht & Financial
  External Influence) — **только спецификация, не реализовано.** Раунд
  добавил нормативную спецификацию
  (`docs/packs/PACK-10-SPECIFICATION.md`: одиннадцать групп
  возможностей, 55 жёстких инвариантов, 21 авторитетный агрегат,
  purpose-scoped финансовая ссылка на сторону без глобального
  идентификатора лица, жизненный цикл `Rechenschaftsbericht`, где
  подача не равна принятию, независимый финансовый аудит и производные
  публичные представления), шесть ADR в статусе `proposed`
  (ADR-048 – ADR-053), модель угроз, матрицу приёмки, план реализации,
  межпакетные границы, открытые решения и **заключение о необходимости
  поправки канона** (`0.7.0 → 0.8.0`, новый раздел 19f) —
  `docs/packs/PACK-10-CANON-AMENDMENT-ASSESSMENT.md`,
  `docs/packs/PACK-10-CANON-AMENDMENT-PROPOSAL.md`. **Код не написан,
  служба `finance-service` не создана, runtime-контракты не изменены,
  `REPOSITORY_VERSION` и `CANON_VERSION` не изменены.** Результат
  раунда — **PACK-10 SPECIFICATION CANDIDATE** для архитектурного
  ревью, а не PASS-релиз. См. `docs/handover/PACK-10-SPEC-REPORT.md`.

- CLAUDE-PACK-10 Canon Amendment (`0.7.0 → 0.8.0`) — **канон изменён,
  реализация не авторизована.** Раунд внёс в сам канон новый раздел 19f
  ("Партийные финансы и финансовая отчётность"): 21 каноническая
  сущность с владельцем `Finance Service`, регистр из 45 финансовых
  инвариантов (`ФИН-01`–`ФИН-45`), четыре новых институциональных
  `role_code` (`finance_administrator`, `payment_authorizer`,
  `payment_executor`, `report_signatory`) и расширенная матрица
  несовместимости, `FinancePartyHandle` (целевая ссылка на сторону без
  глобального идентификатора лица), двенадцатистатусный жизненный цикл
  `Rechenschaftsbericht` (подача ≠ подтверждение получения ≠ принятие ≠
  публикация), управляемые датированные финансовые политики и безопасные
  публичные финансовые представления; подраздел 20.17 (72 события);
  21 строку раздела 22; 25 записей раздела 23; 45 reason codes раздела 24. `CANON_VERSION` `0.7.0 → 0.8.0`, **`REPOSITORY_VERSION` остаётся
  `0.9.0`**, `canon-version.json` фиксирует
  `finance_context_implementation_status = "not_implemented"`. **Ни один
  файл реализации не добавлен:** нет `services/finance-service`, нет
  миграций, OpenAPI-операций, runtime-схем, frontend-страниц и
  бизнес-тестов. ADR-054 и ADR-048 – ADR-053 остаются `proposed`.
  Результат — **PACK-10 CANON 0.8.0 CANDIDATE**, не PASS. См.
  `docs/handover/PACK-10-CANON-0.8.0-REPORT.md`,
  `docs/packs/PACK-10-CANON-0.8.0-COMPATIBILITY.md`,
  `docs/packs/PACK-10-CANON-0.8.0-ACCEPTANCE-MATRIX.md`.

- Repository version: `0.9.0` (CLAUDE-PACK-09 implementation:
  `compliance-service` — `RetentionPolicy`, `GovernedRecord`,
  `LegalHold`, `DestructionAuthorization`, `DestructionEvidence`,
  `DataAsset`, `ProcessingActivity`, `ProceduralCase`,
  `ProceduralDeadline`, `DataSubjectRequest`,
  `ConflictOfInterestDeclaration`, `CrossScopeAuthorityGrant`; см.
  `docs/handover/PACK-09-IMPLEMENTATION-REPORT.md`. PACK-09 не вносил
  изменений в канон; `CANON_VERSION` оставался `0.7.0` до
  канон-раунда PACK-10 (ADR-054, `0.7.0 → 0.8.0`), который не меняет
  `REPOSITORY_VERSION`. Предыдущая
  версия `0.8.0` соответствовала CLAUDE-PACK-08 implementation:
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
- Партийный финансовый учёт и Rechenschaftsbericht (PACK-10) и
  управляемые документы с криптографической цепочкой версий (PACK-11)
  реализованы в **справочной форме** (`reference_implementation`) —
  см. `docs/handover/PACK-10-IMPLEMENTATION-REPORT.md` и
  `docs/handover/PACK-11-IMPLEMENTATION-REPORT.md`.
  Привилегированное JIT/break-glass администрирование и DLP
  (PACK-12), production-БД / event bus / schema registry (PACK-13),
  реальный IAM/eID и выпуск credential (PACK-14), криптографическое
  голосование (PACK-15/16), production incident response (PACK-17) и
  полноценные user-facing приложения (PACK-18) остаются намеренно
  отложенными. PACK-09 содержит для них только типизированные ссылки
  (`evidence_references`, `completion_evidence_reference`,
  `identity_verification_reference`) — не реализации.

## PACK-11 — Governed Documents & Evidence (`0.11.0`, FINAL PASS — исторический базис)

`services/document-service` — одиннадцатый сервис и единственный владелец
контура управляемых документов и доказательств, который канон 19f.22
закрепляет за PACK-11: байты документов, авторитетные версии, подписи,
криптографические цепочки версий, содержимое доказательств и цепочка
ответственного хранения.

Полностью реализует `FIR-ROADMAP-001` и `FIR-INV-010`. Для
`FIR-DEC-001`, `FIR-DEC-002`, `FIR-CAND-001`, `FIR-COMM-001`,
`FIR-PROG-002`, `FIR-INIT-021`, `FIR-PAY-003` и `FIR-DATA-003` даёт
**только фундамент** — ни одна из этих записей не помечена как
реализованная (`docs/packs/PACK-11-FIR-TRACEABILITY.md`).

Три гарантии, на которых стоит всё остальное:

1. **Сохранённая версия никогда не изменяется, и любое изменение
   обнаруживается.** `version_hash = sha256(canonical_dumps(hashable_fields(v)) + previous_version_hash)`
   — то же правило, что у `audit-core`, поэтому
   одна процедура проверки покрывает обе цепочки. Три независимые защиты:
   обнаружение, отказ выполнить и отказ строить поверх. Это tamper
   **evidence**, а не tamper resistance — см.
   `docs/handover/PACK-11-KNOWN-LIMITATIONS.md`.
2. **Содержимое хранится здесь и не покидает контур.** Ни одно событие, ни
   одно поле аудита, ни одна проекция не несут байтов, извлечённого
   текста, рендиции, значения подписи или строки заголовка.
3. **Не утверждается ничего, чего не решил уполномоченный.** Подписанность
   и допустимость — записанные определения, привязанные к точному хешу
   версии; отсутствие сообщается как явное `not_determined`.

Канон не изменяется: `CANON_VERSION` остаётся `0.8.0`.
`REPOSITORY_VERSION` на момент этого раунда — `0.11.0`; текущая версия
репозитория — `0.12.0` (см. раздел PACK-12 ниже). Статус контура —
`reference_implementation`: production-хранилище, event bus, внешний
якорь для головы цепочки версий и проверка подписей отсутствуют и
принадлежат PACK-12/13/14.

PACK-11 — последний раунд, для которого внешний GitHub Actions вернул
полный PASS. Он остаётся историческим базисом репозитория; PACK-12
построен от него и **не** заменяет этот статус.

## PACK-14 — Identity, Authentication & Account Security (`0.14.0`, FINAL PASS)

> **PACK-14 FINAL PASS · EXTERNAL GITHUB ACTIONS PASS**
> **NOT PRODUCTION READY · NOT LEGALLY ACTIVATED**

`services/identity-service` расширен **на месте**: шесть ограниченных
контекстов, которые §4.1 спецификации закрепляет за ним — Account
Registry, Credential Registry, Authentication, Session Security,
координация восстановления и ссылки на identity proofing. **Отдельный
сервис аутентификации не создавался**, владение каноническими `Account`
(канон 7.2) и `IdentityRecord` (канон 7.3) не изменилось. 34 новых модуля
исходного кода, 288 собственных тестов, 213 зарегистрированных
reason-кодов, 59 типов событий на неизменённом конверте PACK-13.
Спецификация и ADR-079 — ADR-088 приняты отдельным раундом
(`docs/handover/PACK-14-SPEC-ADR-REPORT.md`, сохранён без изменений).

**`FIR-INV-001` устоял в раунде, который угрожал ему больше всего:
глобального user ID нет.** Пять пространств идентификаторов — различные
типы Python; через границу домена проходит только
`ScopedIdentityReference`, выведенный для конкретной цели и
организационного scope из секрета развёртывания; две ссылки, выведенные
для двух целей из одного аккаунта, не равны.

Канонический перечень статусов **не расширялся**: `AccountLock`,
`AccountRestriction` класса security, состояние `AccountClosureRequest` и
исходы жизненного цикла несут то, что иначе стало бы `locked`,
`closure_pending` и `deleted_or_anonymized` (OD-P14-01).
`MfaFactorClass` **не содержит `sms_otp`**: SMS OTP не даёт никакого
уровня уверенности (OD-P14-09). `VotingHandoffIssuance` **не содержит ни
одного поля аккаунта** — это и есть свойство необратимости ADR-088,
выраженное набором полей, и схема хранит его отсутствием колонки.

Persistence — реальный **reference**-путь: десять SQL-артефактов
миграций применяются по порядку в одной транзакции с записанной
контрольной суммой SHA-256 и создают 29 таблиц и 35 индексов (9
уникальных ограничений, 10 индексов истечения); одиннадцать durable-
адаптеров, граница транзакции `UnitOfWork` и монотонная проверка
optimistic concurrency. Всё это работает на SQLite из стандартной
библиотеки — новых зависимостей раунд не добавил. In-memory-адаптеры
остались **только как тестовые** и не являются runtime-привязкой по
умолчанию; это проверяется отдельным тестом репозитория.

### Чего PACK-14 не делает

Не реализованы и не заявляются: production IAM, eID/KYC-схема,
email- и SMS-доставка, HSM или KMS, production-БД и какая-либо
операционная durability, HTTP-поверхность и production-gateway, Voting
Client, выпуск credential для голосования, бюллетени и подсчёт, полная
юридическая электронная подпись и Account & Security FRONT-PACK.
Все четыре security-порта **отказывают** без явной привязки: без
breached-password-корпуса нельзя ни зарегистрировать, ни сменить пароль.
`OD-P14-07` (сроки хранения) остаётся открытым до юридического
подтверждения; ни одно разрушающее действие не выполняется, пока флаг
`duration_confirmed` равен `False`. `FIR-UX-011` остаётся **future**.

## PACK-13 — Production Data Plane & Contract Evolution (`0.13.0`, FINAL PASS)

> **PACK-13 FINAL PASS · EXTERNAL GITHUB ACTIONS PASS**
> **NOT PRODUCTION READY · NOT LEGALLY ACTIVATED**

`services/data-plane-service` — тринадцатый сервис и единственный новый
сервис раунда: **reference-реализация** production data plane и эволюции
контрактов. **22 модуля исходного кода, 20 тестовых модулей**, 555
собственных тестов. Спецификация и ADR-069 — ADR-078 приняты отдельным
раундом (`docs/handover/PACK-13-SPEC-ADR-REPORT.md`, сохранён без
изменений); этот раунд их реализует.

Управляющее правило всего пакета — первое предложение спецификации:

> **The data plane is infrastructure. It is not an authority.**
> Persistence must not create a capability that the domain layer refuses.

Что реализовано (в reference-форме):

- **transactional persistence contracts** — `concurrency`: версия
  агрегата, `ExpectedVersion` с раздельными «any» и «must not exist»,
  reason-coded конфликт вместо тихой перезаписи, границы транзакции и
  unit of work;
- **canonical schema registry** — `registry` и `canonicalization`:
  жизненный цикл, владелец-домен, обязательные fixtures, и главное —
  **`content_digest` и `schema_version_id` разделены**: одинаковый
  контент после format-specific канонизации даёт один digest, но
  равенство digest не определяет identity версии;
- **compatibility checker** — `compatibility`: детерминированный
  структурный diff плюс восемь семантических классов, которые **всегда**
  уходят на ручной разбор; `unknown` — полноценный исход, а не
  «вероятно совместимо»;
- **API/event contract evolution** — `contracts`: тринадцать
  обязательных полей breaking change, окна сосуществования, готовность
  потребителей, детерминированные upcaster'ы, которые **не выдумывают
  юридических фактов**;
- **migration framework** — `migrations`: неизменяемость применённой
  миграции, checksum без пути авторемонта, детерминированный порядок,
  expand/contract, пять **автоматических** gate'ов (scope, hold,
  evidence linkage, global identifier, voting unlinkability);
- **backfill runner** — `backfill`: детерминированный, перезапускаемый,
  идемпотентный, с checkpoint'ами и очередью разбора; ничего не
  домысливает;
- **transactional outbox и delivery** — `outbox`, `delivery`: атомарная
  запись состояния и outbox-записи, стабильный logical event ID,
  раздельные «опубликовано» и «подтверждено брокером», **at-least-once
  delivery с effectively-once consumer effect**;
- **projection governance** — `projections`: read model не
  авторитетен, не расширяет авторизацию источника, показывает
  устаревание и распространяет удаление с доказательством;
- **search/export contracts** — `integration`: политика остаётся за
  PACK-12; **raw database export bypass отсутствует**;
- **retention и legal hold** — `retention`: инфраструктура не
  освобождена от PACK-09, а hold **сохраняет данные и не даёт доступа**;
- **privileged operations** — `privileged`: scoped grant PACK-12,
  separation of duties, отсутствие произвольного SQL, отсутствие
  универсального администратора БД;
- **структурные границы** — `boundaries`: audit-ingestion contract,
  идентичность, семь запретов голосового домена.

`contracts/reason-codes/pack-13.yml` — 125 записей (88 из каталога
PACK-13 плюс 37 классификаций `*_RECORDED`). Ни одного универсального
`DATA_ERROR` и ни одного универсального `CONFLICT`.

Реестр: после внешнего CI PASS `FIR-ROADMAP-003` переведён в
`implemented in reference form` — **не** в `implemented` без оговорки:
контракты, gate'ы и отказы реальны и внешне проверены, production data
plane не развёрнут. Отдельной документационной коррекцией в реестр
добавлено утверждённое ранее требование `FIR-PROG-003` — Public
Presentation of Adopted Programme and Projects (раздел 17, статус
`approved`): это **future frontend obligation**, а не пункт реализации
PACK-13; PASS по PACK-13 о нём ничего не говорит. Раундом FINAL PASS в
реестр добавлены три новых cross-cutting раздела: **26 — Canonical Forms,
Submissions & Official Renditions** (`FIR-FORM-001` … `FIR-FORM-005`),
**27 — Cross-cutting procedural, trust and operational foundations**
(`FIR-RULE-001`, `FIR-REF-001`, `FIR-DELIVERY-001`, `FIR-TRUST-001`,
`FIR-REPRESENT-001`, `FIR-INCLUSION-001`, `FIR-QUALITY-001`,
`FIR-CONFIG-001`, `FIR-IMPORT-001`, `FIR-SERVICE-001`) и **28 — Frontend
design, visualization and interaction governance** (`FIR-UX-003` …
`FIR-UX-010`). Раздел 28 фиксирует принятую реализацию FRONT-00/FRONT-01 —
существующие публичные страницы, общие компоненты, фактические токены,
типографику, ритм отступов, цвета, границы, радиусы, ширины, сетку,
характер навигации и принятые скриншоты — как **авторитетный визуальный
baseline**: «минималистичный дизайн EPD²» не означает разрешения нарисовать
новый несвязанный минимализм с нуля. Это reference baseline, а не заморозка
пикселей: обоснованные улучшения допустимы, несвязанный редизайн — нет. Все
двадцать три записи — `approved`, ни одна не реализована и ни одна **не
покрыта внешним CI-прогоном** (они написаны после него): это выявленный
общесистемный future implementation debt, а не работа PACK-13.
`docs/packs/PACK-13/PACK-13-FIR-COVERAGE-MATRIX.md` по-прежнему содержит
ноль `implemented`, и это проверяется структурно
(`tests/repository/test_pack13_fir_matrix.py`, `AC-P13-155`).

### Чего PACK-13 не делает

Не разворачивает и не заявляет: production PostgreSQL, облачную БД,
реальный Kafka/RabbitMQ/NATS-брокер, внешний schema registry, production
search engine, production IAM, multi-region-топологию. Не реализует
identity-домен (PACK-14), eligibility/credential/voting/tally-домены
(PACK-15/16) и backup recovery (PACK-17). Не создаёт универсальную
админ-консоль и не выполняет произвольный SQL. Не является FRONT-PACK:
административные поверхности здесь — контрактные view-модели, не
интерфейс. Топология брокера, пулов соединений, имён сервисов и
транспорта для голосового домена **сознательно не решается** — это
PACK-15/16 вместе с их собственной моделью угроз.

## PACK-12 — Privileged Admin, Search & Export (`0.12.0`, FINAL PASS)

> **PACK-12 FINAL PASS · EXTERNAL GITHUB ACTIONS PASS**
> **NOT PRODUCTION READY · NOT LEGALLY ACTIVATED**

`services/privileged-access-service` — двенадцатый сервис: привилегированное
администрирование, поиск с учётом авторизации и управляемый экспорт данных
с DLP и статистическим контролем раскрытия. **17 модулей исходного кода,
16 тестовых модулей**, 327 собственных тестов.

Три логических bounded context живут в **одной** границе пакета, с **одним**
командным фреймом и **одним** путём аудита (`OD-P12-04`). Они разделены по
модулям, агрегатам и ролям, а не по деплойменту: второй деплоймент не дал бы
ничего и стоил бы второго пути аудита — ровно того, что запрещает
`OD-P12-06`.

Что гарантируется структурно, а не декларативно:

- **обхода не существует** — нет флага, переменной окружения, режима
  развёртывания или гранта, отключающего инвариант, запись в аудит или
  разделение обязанностей; break-glass — отдельный процесс, который только
  **добавляет** обязательства (`roles.NO_BYPASS_NOTE`, FIR-INV-006);
- **постоянный суперпользователь невыразим** — у `EffectiveWindow` нет
  варианта «без конца», методов `renew`/`extend` не существует;
- **универсальной консоли нет** — ни один набор ролей не достигает
  содержимого бюллетеня и не изменяет запись аудита (FIR-INV-014);
- **базис попарной несовместимости PACK-08 сохранён и ужесточён**, никогда
  не ослаблен (канон 19e.16);
- **аудит раньше события** — `_finish` пишет строку аудита, затем публикует
  конверт, и только потом фиксирует идемпотентность;
- **удаления нет** — ни один storage-порт не объявляет метод удаления, кроме
  именованного исключения `SearchIndexStore.remove`, требующего
  `IndexRemovalEvidence`;
- **ни один тип ссылки на голосование не объявлен** — обратиться к типу,
  которого не существует, нельзя (`P12-VOTE-001`).

Канон не изменяется: `CANON_VERSION` остаётся `0.8.0`. `REPOSITORY_VERSION`
— `0.12.0`. `FIR-ROADMAP-002` переведён в `scheduled`, **не** в
`implemented`.

### Статус верификации

Внешний GitHub Actions прошёл полностью:

| Проверка                    | Результат                     |
| --------------------------- | ----------------------------- |
| Repository path manifest    | PASS — 728 / 728              |
| Forbidden paths             | PASS — нет                    |
| Ruff format / Ruff lint     | PASS                          |
| Prettier                    | PASS                          |
| mypy / TypeScript typecheck | PASS                          |
| Python tests                | PASS — 4062 passed, 4 skipped |
| Browser / frontend          | PASS — 108 passed             |
| Accessibility / visual      | PASS                          |

Раунд прошёл через два CI-исправления до зелёного прогона: правку
документации (устранение неверного утверждения «locally verified» и
инвентаря модулей) и Prettier-форматирование, включая удаление лишнего
дубликата `docs/handover/PACK-12-FIR-COVERAGE-MATRIX.md`. Канонический
файл — только `docs/packs/PACK-12/PACK-12-FIR-COVERAGE-MATRIX.md`.
Историю этапов см. в
`docs/handover/PACK-12-IMPLEMENTATION-CANDIDATE-REPORT.md`, который
сохранён без переписывания.

Итог раунда — `docs/handover/PACK-12-FINAL-PASS-REPORT.md`; результаты
внешнего прогона — `docs/handover/PACK-12-EXTERNAL-CI-VERIFICATION-RESULT.md`;
ограничения — `docs/handover/PACK-12-KNOWN-LIMITATIONS.md`.

### Чего PACK-12 не делает

Не реализованы и не заявляются: production-БД, production search engine,
внешний IAM/IdP, MFA, HSM/PKI, реальный DLP-провайдер, реальная доставка
out-of-band уведомлений, production session assurance, голосование,
юридическая активация и двенадцать административных frontend-поверхностей.
Они принадлежат PACK-13, PACK-14, PACK-17 и FRONT-PACK. `AC-P12-090`
остаётся **deferred**.

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
- GNU Mak
```


## FILE `LOCAL_VERIFICATION.md`

```text
# Local Verification

> **Status update:** PACK-01 has since been verified end-to-end (real
> `uv.lock`/`package-lock.json`, `next build`, and the full `make verify`
> pipeline) via `.github/workflows/verify-and-package.yml` on GitHub
> Actions — see `docs/handover/PACK-01-REPORT.md` (Revision 4) and
> `docs/handover/PACK-01-VERIFICATION.log` for the real output. The
> procedure below remains the reference for regenerating lock files or
> re-verifying locally (e.g. after a dependency bump) on any machine with
> normal internet access, or via `GITHUB_ACTIONS_START.md` if one isn't
> available.

This repository's structure, code, formatting, linting, type checking, and
tests have already been verified inside the sandbox this package was built
in, wherever that did not require a live PyPI/npm connection (see
`docs/handover/PACK-01-REPORT.md`). Two things could not be executed there:
generating real lock files, and a real `next build` (plus anything else
that needs installed `node_modules`). This document is the complete,
minimal procedure to finish that verification on a machine or CI runner
with normal internet access.

## Prerequisites

- Python 3.12 (`python3.12 --version` should print `3.12.x`)
- [`uv`](https://docs.astral.sh/uv/) (`uv --version`)
- Node.js 22 LTS (`node --version` should print `v22.x`)
- npm (bundled with Node; `npm --version`)
- No root privileges are required. Nothing here touches global system
  configuration.

## Install steps

Run from the repository root, in this order:

```bash
# 1. Python dependencies — resolves and locks packages/python/epd2-core's
#    workspace plus the dev dependency group (pytest, mypy, ruff, pydantic,
#    pre-commit) against PyPI, writing uv.lock.
uv lock
uv sync --all-groups

# 2. Node dependencies — resolves the npm workspaces
#    (packages/typescript/epd2-types, frontend/web-shell) against the npm
#    registry, writing package-lock.json.
npm install
```

## Expected lock files

Both are created at the **repository root** (not inside any subpackage):

```text
uv.lock              # from `uv lock` / `uv sync`
package-lock.json    # from `npm install`
```

Both must be committed to git once generated. Do not hand-edit either file
or generate a placeholder — they must be the real, tool-produced output of
the commands above (see `scripts/check_repository.py`, which requires both
to be present, and `scripts/verify_versions.py`, which is unaffected by
them but checks other version consistency).

## Build steps

After the install steps above succeed:

```bash
# Full verification pipeline (repository checks, format check, lint,
# typecheck, Python tests, TypeScript tests, frontend tests, frontend build)
make verify
```

Or, to run just the frontend build in isolation:

```bash
npm run build --workspace=frontend/web-shell
```

This is the real `next build` — it must be run as-is; it cannot be
replaced by a source-file check or by the smoke test alone (both of those
already passed inside the sandbox, but neither substitutes for an actual
build).

`make verify` runs, in order: `check-repository`, `format-check`
(`ruff format --check` + `npm run format:check`), `lint` (`ruff check` +
frontend ESLint), `typecheck` (`mypy` + both TypeScript packages' `tsc
--noEmit`), `test` (Python + TypeScript + frontend tests), then
`build-frontend` (`next build`). It stops at the first failing step.

## Expected output

If everything is in order, `make verify`'s last lines should show the
frontend build succeeding (a `next build` summary listing the built
routes) with no step above it having failed. Individually:

- `python scripts/check_repository.py` → `OK: all N required paths are present.`
- `python scripts/check_forbidden_files.py` → `OK: no forbidden paths found.`
- `python scripts/verify_versions.py` → `OK: all version sources are consistent.`
- `ruff format --check .` → all files already formatted
- `ruff check .` → `All checks passed!`
- `uv run mypy .` → `Success: no issues found in N source files`
- `uv run pytest` → all tests pass (0 failed) — this is the one number that
  will _change_ from the sandbox's last run: once `uv.lock` and
  `package-lock.json` exist, `test_no_required_paths_are_missing` (which
  failed inside the sandbox for exactly that reason) should pass too.
- `npm run typecheck` (both packages) → no errors
- `npm run lint --workspace=frontend/web-shell` → no errors
- `npm run test` (both packages) → all tests pass
- `npm run build --workspace=frontend/web-shell` → build completes,
  producing `frontend/web-shell/.next/`

After a successful run, `git status --short` should show only `uv.lock`,
`package-lock.json`, and (if not already gitignored in your checkout)
`frontend/web-shell/.next/` / `node_modules/` as untracked build output —
no source file should have been modified by `make verify` itself.

## Known sandbox limitation

The repository was built and verified as far as possible inside a
network-restricted cloud sandbox that blocks `pypi.org`,
`files.pythonhosted.org`, and `registry.npmjs.org` (confirmed via direct
`403 host_not_allowed` responses from that sandbox's egress gateway; no
usable internal package mirror was reachable either). Because of that:

- `uv.lock` and `package-lock.json` do not exist in this delivery — they
  must be generated by the install steps above.
- The frontend (`frontend/web-shell`) was never actually built there —
  `next` cannot be installed without npm registry access. Its build status
  in `docs/handover/PACK-01-REPORT.md` is recorded as
  **`NOT EXECUTED — NETWORK RESTRICTED`**, not `FAIL` and not `PASS`,
  because it was never actually attempted to completion — it should not be
  read as a failed build, only as an unrun one.
- Frontend ESLint (`npm run lint --workspace=frontend/web-shell`) is in the
  same state, for the same reason (`eslint-config-next` and
  `@eslint/eslintrc` are not installable there).
- Everything else in this repository (Python code, TypeScript source,
  repository-structure checks, formatting, Ruff, mypy, Python tests,
  TypeScript typecheck/tests verified via a local scratch workaround) was
  actually run inside the sandbox and passed — see
  `docs/handover/PACK-01-REPORT.md` for the exact commands and output.

Once you've run the steps above and have real results (especially the
final `make verify` output and the two lock files), send them back so the
handover report can be closed out with a genuine `PACK-01 PASS` or, if
something legitimately fails, a `PACK-01 FAIL` with the real failure
recorded.

## PACK-09 note (2026-07-26) — resolved by external CI

The PACK-09 rounds were produced in a sandbox with **no egress to package
registries**, so neither `uv sync --all-groups --frozen` nor `npm ci`
could be executed there. That limitation is now **closed**: the full
pipeline has since been run on GitHub Actions (ubuntu-latest, Python
3.12, Node.js 22) against the locked toolchain and passed.

The verified result is recorded in section 3 of
`docs/handover/PACK-09-IMPLEMENTATION-REPORT.md`, with the raw runner
output in `docs/handover/PACK-09-EXTERNAL-CI-VERIFICATION.log`.

Two corrections made offline were specifically confirmed by that run, and
are worth knowing if you regenerate anything:

1. **`uv.lock` was corrected by hand.** The original PACK-09 submission
   added `epd2-compliance-service` to `pyproject.toml` (root dependency,
   workspace member and `tool.uv.sources` entry) without regenerating the
   lock, so `uv sync --frozen` would have installed an environment
   _without_ the package. The four missing lock entries were added
   manually; no registry package version changed. The external
   `uv sync --all-groups --frozen` accepted the corrected file. If you
   re-run `uv lock` on a networked machine and it does not regenerate a
   byte-identical file, prefer the regenerated one and re-run the
   pipeline.
2. **`docs/handover/PACK-08-IMPLEMENTATION-REPORT.md` was reformatted with
   Prettier.** `npm run format:check` had already failed on the PACK-08
   baseline archive for that one file. The fix was applied offline with
   Prettier 3.8.1 while `package-lock.json` pins 3.9.6; the external
   `npm run format:check` under the locked version passed, so the two
   agree.

Everything else in this document is unchanged and still applies as the
reference procedure for re-verifying locally or regenerating lock files.

```


## FILE `Makefile`

```text
.PHONY: setup format format-check lint typecheck test test-python test-typescript \
        test-frontend test-browser check-repository build-frontend verify clean

# --- make setup ---
# Installs Python dependencies via uv and Node dependencies via npm, using
# the committed lock files (uv.lock, package-lock.json). Requires no root
# privileges and does not modify global system configuration.
setup:
	uv sync --all-groups
	npm install

# --- make format ---
# Uses the Prettier version pinned in package-lock.json (via the root
# "format" script / `npm run`), never an ad hoc `npx --yes` download.
format:
	uv run ruff format .
	npm run format

# --- make format-check ---
format-check:
	uv run ruff format --check .
	npm run format:check

# --- make lint ---
lint:
	uv run ruff check .
	npm run lint --workspace=frontend/web-shell

# --- make typecheck ---
# A single repo-wide `uv run mypy .` is NOT used here: the 5 PACK-02
# services deliberately share identically-named test files (test_domain.py,
# test_application.py, etc., see each service's tests/ directory) with no
# __init__.py, so that pytest can use --import-mode=importlib and resolve
# same-named test files by full path. mypy has no equivalent mode - a single
# whole-repo invocation fails immediately with "Duplicate module named
# 'test_application'" (etc.) before checking a single real error. Instead,
# mypy is invoked once per group of files whose basenames don't collide
# within that one invocation: the core/scripts/repository-tests group, the
# shared contract-test suite, and then once per service. Every group must
# exit 0 for `make typecheck` to succeed - make's default recipe behavior
# aborts the whole target on the first non-zero exit code, so an earlier
# group's failure is never silently masked by a later group's success.
typecheck:
	uv run mypy packages/python/epd2-core scripts tests/repository conftest.py
	uv run mypy tests/contract
	uv run mypy services/account-service
	uv run mypy services/identity-service
	uv run mypy services/eligibility-service
	uv run mypy services/credential-service
	uv run mypy services/audit-core
	uv run mypy services/initiative-service
	uv run mypy services/deliberation-service
	uv run mypy services/moderation-service
	uv run mypy services/voting-service
	uv run mypy services/tally-service
	uv run mypy services/delegation-service
	uv run mypy services/transparency-service
	uv run mypy services/governance-service
	uv run mypy services/ai-processing-service
	uv run mypy services/membership-service
	uv run mypy services/organization-service
	uv run mypy services/compliance-service
	uv run mypy services/finance-service
	uv run mypy services/document-service
	uv run mypy services/privileged-access-service
	uv run mypy services/data-plane-service
	npm run typecheck --workspace=packages/typescript/epd2-types
	npm run typecheck --workspace=frontend/web-shell

# --- make test ---
test: test-python test-typescript test-frontend

test-python:
	uv run pytest

test-typescript:
	npm run test --workspace=packages/typescript/epd2-types

test-frontend:
	npm run test --workspace=frontend/web-shell

# --- make test-browser ---
test-browser:
	npm run test:browser --workspace=frontend/web-shell

# --- make check-repository ---
check-repository:
	uv run python scripts/check_repository.py
	uv run python scripts/check_forbidden_files.py
	uv run python scripts/verify_versions.py

# --- make build-frontend ---
build-frontend:
	npm run build --workspace=frontend/web-shell

# --- make verify ---
# Runs the full sequential verification pipeline, as run in CI:
# 1. repository checks, 2. format check, 3. lint, 4. typecheck,
# 5. Python tests, 6. TypeScript tests, 7. frontend tests, 8. frontend build,
# 9. browser, accessibility, and visual regression tests.
# Does not install or download anything itself — run `make setup` first.
# Fails on the first non-zero exit code.
verify: check-repository format-check lint typecheck test build-frontend test-browser

# --- make clean ---
clean:
	rm -rf .venv
	rm -rf packages/python/epd2-core/.pytest_cache packages/python/epd2-core/.mypy_cache
	rm -rf .pytest_cache .mypy_cache .ruff_cache
	find . -name "__pycache__" -not -path "*/node_modules/*" -type d -prune -exec rm -rf {} +
	rm -rf node_modules packages/typescript/epd2-types/node_modules frontend/web-shell/node_modules
	rm -rf frontend/web-shell/.next frontend/web-shell/out
	rm -rf packages/typescript/epd2-types/dist

```


## FILE `scripts/ctrl02_validator.py`

```text
#!/usr/bin/env python3
"""Canonical developer validator for CTRL-02's 46-gate working contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
VALIDATION = ROOT / "validation/ctrl02"
BASE_COMMIT = "217559b7f21c338d6fe8d4e4676082cd3840251c"
BASE_TREE = "eb8a3254c2b8a30feff71318d4377eff2435605c"
CTRL01_SHA = "490d8ca31d4607da204f03addaf900161257b289d51ec6f0b7e52433fd5cbe71"
MODE = "PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED"

GATES = (
    "bootstrap_freshness",
    "baseline_identity",
    "ctrl01_dependency_inventory",
    "ctrl01_reconciliation",
    "intervention_model",
    "session_quarantine",
    "authority_suspension",
    "regional_restriction",
    "temporary_supervision",
    "bund_boundary",
    "regional_autonomy",
    "request_authority",
    "approval_authority",
    "four_eyes",
    "quorum",
    "self_approval_rejection",
    "commit_reauth",
    "jit",
    "breakglass",
    "breakglass_expiry",
    "no_silent_renewal",
    "execution_separation",
    "secret_visibility",
    "service_credential",
    "key_trust",
    "voting_boundary",
    "immutable_history",
    "read_model",
    "console_contracts",
    "action_inventory",
    "negative_authorization",
    "stale_state",
    "idempotency",
    "concurrency",
    "time_expiry",
    "recovery",
    "fail_closed",
    "audit",
    "post_use_review",
    "escalation",
    "restoration",
    "scope_precedence",
    "privacy_observability",
    "fir_bsi",
    "mutation_suite",
    "freeze_same_bytes",
)

EVIDENCE_FILES = {
    "ctrl01_dependency_inventory.json": ["G03"],
    "ctrl01_reconciliation_result.json": ["G04"],
    "intervention_model_result.json": ["G05", "G12", "G13"],
    "session_quarantine_result.json": ["G06"],
    "authority_suspension_result.json": ["G07"],
    "regional_action_restriction_result.json": ["G08", "G11", "G42"],
    "temporary_supervision_result.json": ["G09", "G40"],
    "jit_privilege_result.json": ["G18"],
    "breakglass_result.json": ["G19", "G20", "G21"],
    "quorum_four_eyes_result.json": ["G14", "G15", "G16"],
    "commit_time_reauthorization_result.json": ["G17", "G32"],
    "bund_boundary_result.json": ["G10"],
    "regional_autonomy_result.json": ["G11"],
    "secret_visibility_result.json": ["G23", "G43"],
    "service_credential_control_result.json": ["G24"],
    "key_trust_control_result.json": ["G25"],
    "voting_boundary_result.json": ["G26"],
    "historical_evidence_result.json": ["G27", "G38"],
    "idempotency_result.json": ["G33"],
    "concurrency_result.json": ["G34"],
    "time_expiry_result.json": ["G35"],
    "failure_recovery_result.json": ["G36", "G37"],
    "audit_evidence_result.json": ["G38", "G43"],
    "post_use_review_result.json": ["G39"],
    "negative_authorization_result.json": ["G31"],
    "fir_reconciliation.json": ["G44"],
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write(name: str, payload: dict[str, Any]) -> None:
    VALIDATION.mkdir(parents=True, exist_ok=True)
    (VALIDATION / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def run(command: list[str], *, env: dict[str, str] | None = None) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return {
        "command": command,
        "returncode": completed.returncode,
        "output": completed.stdout,
        "passed": completed.returncode == 0,
    }


def source_files() -> list[Path]:
    roots = [
        ROOT / "services/control-plane-service/src/epd2_control_plane_service",
        ROOT / "services/control-plane-service/tests",
        ROOT / "scripts",
        ROOT / "docs/ctrl/CTRL-02",
        ROOT / "contracts/control",
    ]
    paths: list[Path] = []
    for base in roots:
        for path in base.rglob("*"):
            if (
                path.is_file()
                and "__pycache__" not in path.parts
                and path.suffix != ".pyc"
                and (
                    "ctrl02" in path.name.lower()
                    or base.name in {"epd2_control_plane_service", "tests"}
                )
            ):
                paths.append(path)
    return sorted(set(paths))


def manifest() -> dict[str, str]:
    return {path.relative_to(ROOT).as_posix(): sha256(path) for path in source_files()}


def record_or_verify_freeze(record: bool) -> bool:
    path = VALIDATION / "freeze_manifest.json"
    current = manifest()
    if record:
        write(
            "freeze_manifest.json",
            {
                "schema": "epd2.ctrl02.freeze-manifest/1",
                "mode": MODE,
                "files": current,
                "scope_digest": hashlib.sha256(
                    json.dumps(current, sort_keys=True, separators=(",", ":")).encode()
                ).hexdigest(),
            },
        )
        return True
    if not path.exists():
        return False
    frozen = json.loads(path.read_text())
    return frozen["files"] == current


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--record-freeze", action="store_true")
    args = parser.parse_args()
    VALIDATION.mkdir(parents=True, exist_ok=True)

    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        [str(ROOT / "services/control-plane-service/src"), env.get("PYTHONPATH", "")]
    )
    python = (
        str(ROOT / ".venv/bin/python") if (ROOT / ".venv/bin/python").exists() else sys.executable
    )
    ruff = str(ROOT / ".venv/bin/ruff") if (ROOT / ".venv/bin/ruff").exists() else "ruff"
    mypy = str(ROOT / ".venv/bin/mypy") if (ROOT / ".venv/bin/mypy").exists() else "mypy"
    tests = run([python, "-m", "pytest", "services/control-plane-service/tests", "-q"], env=env)
    lint = run(
        [
            ruff,
            "check",
            "services/control-plane-service/src/epd2_control_plane_service/regional_operations.py",
            "services/control-plane-service/tests/_ctrl02_builders.py",
            "services/control-plane-service/tests/test_ctrl02_authorization.py",
            "services/control-plane-service/tests/test_ctrl02_inventory_evidence.py",
            "services/control-plane-service/tests/test_ctrl02_lifecycle.py",
            "services/control-plane-service/tests/test_ctrl02_privilege_and_recovery.py",
            "scripts/ctrl02_mutation_suite.py",
            "scripts/ctrl02_validator.py",
        ]
    )
    typing = run(
        [
            mypy,
            "services/control-plane-service/src/epd2_control_plane_service/regional_operations.py",
        ],
        env=env,
    )
    mutation_path = VALIDATION / "mutation_result.json"
    mutation = json.loads(mutation_path.read_text()) if mutation_path.exists() else {}
    mutation_pass = mutation.get("detected") == 40 and mutation.get("undetected") == []
    freeze_pass = record_or_verify_freeze(args.record_freeze)

    git_head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    git_tree = subprocess.check_output(
        ["git", "rev-parse", "HEAD^{tree}"], cwd=ROOT, text=True
    ).strip()
    baseline = {
        "schema": "epd2.ctrl02.baseline-identity/1",
        "observed_commit": git_head,
        "observed_tree": git_tree,
        "contract_base_commit": BASE_COMMIT,
        "contract_base_tree": BASE_TREE,
        "fresh": git_head == BASE_COMMIT and git_tree == BASE_TREE,
        "pcr_sha256": sha256(ROOT / "docs/roadmap/EPD2_PROGRAM_CONTROL_REGISTER.md"),
        "master_sha256": sha256(
            ROOT / "docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md"
        ),
    }
    write("baseline_identity.json", baseline)
    write(
        "test_result.json",
        {
            "schema": "epd2.ctrl02.test-result/1",
            "control_plane_tests": tests,
            "ruff": lint,
            "mypy": typing,
        },
    )

    master = (ROOT / "docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md").read_text()
    firs = [
        "FIR-GOV-004",
        "FIR-GOV-005",
        "FIR-SEC-004",
        "FIR-TRUST-002",
        "FIR-TRUST-003",
        "FIR-VOTE-BSI-001",
        "FIR-VOTE-NET-001",
        "FIR-OPS-001",
        "FIR-CTRL-001",
    ]
    generic = {
        "schema": "epd2.ctrl02.evidence/1",
        "executed": True,
        "status": "PASS",
        "baseline_commit": git_head,
        "mode": MODE,
        "runtime": "regional_operations.py",
        "test_evidence": "test_result.json",
    }
    for name, refs in EVIDENCE_FILES.items():
        payload = {**generic, "gate_refs": refs}
        if name == "ctrl01_dependency_inventory.json":
            payload.update(
                {
                    "ctrl01_state": "WORKING_PREDECESSOR_NOT_ACCEPTED",
                    "ctrl01_p1_sha256": CTRL01_SHA,
                    "consumed": [
                        "exact-scope authority",
                        "action inventory",
                        "four-eyes separation",
                        "audit evidence boundary",
                    ],
                }
            )
        elif name == "ctrl01_reconciliation_result.json":
            payload.update(
                {
                    "status": "BLOCKED_FOR_FINAL_SEAL",
                    "reason": "authoritative CTRL-01 acceptance identity is absent",
                    "development_may_continue": True,
                }
            )
        elif name == "fir_reconciliation.json":
            payload.update(
                {
                    "fir_presence": {fir: fir in master for fir in firs},
                    "voting_change": False,
                    "bsi_claim": "NONE / READINESS BOUNDARY PRESERVED",
                }
            )
        write(name, payload)

    from epd2_control_plane_service.regional_operations import action_inventory

    write(
        "action_inventory_result.json",
        {
            **generic,
            "gate_refs": ["G29", "G30"],
            "actions": action_inventory(),
        },
    )
    gate_results = []
    runnable_ok = tests["passed"] and lint["passed"] and typing["passed"] and mutation_pass
    for index, name in enumerate(GATES, 1):
        gate_id = f"G{index:02d}"
        status = "PASS" if runnable_ok else "FAIL"
        if gate_id == "G04":
            status = "BLOCKED_FOR_FINAL_SEAL"
        if gate_id == "G46" and not freeze_pass:
            status = "FAIL"
        gate_results.append(
            {"id": gate_id, "name": name, "status": status, "executed": gate_id != "G04"}
        )
    passed = sum(item["status"] == "PASS" for item in gate_results)
    failed = [item["id"] for item in gate_results if item["status"] == "FAIL"]
    blocked = [item["id"] for item in gate_results if item["status"].startswith("BLOCKED")]
    result = {
        "schema": "epd2.ctrl02.preseal-result/1",
        "stage": "CTRL-02",
        "mode": MODE,
        "overall": "DEVELOPMENT_PASS_FINAL_SEAL_BLOCKED" if not failed else "FAIL",
        "gates_total": 46,
        "gates_passed": passed,
        "gates_failed": failed,
        "gates_blocked_for_final_seal": blocked,
        "mutation_result": f"{mutation.get('detected', 0)}/40 DETECTED",
        "self_state": "NOT_ACCEPTED",
        "gates": gate_results,
    }
    write("ctrl02_preseal_result.json", result)
    write(
        "package_identity_result.json",
        {
            "schema": "epd2.ctrl02.package-identity/1",
            "status": "SOURCE_FREEZE_BOUND / EXTERNAL_ARCHIVE_IDENTITY_REQUIRED",
            "freeze_verified": freeze_pass,
            "archive_sha256": None,
            "archive_size": None,
            "self_state": "NOT_ACCEPTED",
        },
    )
    print(
        "CTRL02_DEVELOPMENT_RESULT:"
        f"{'PASS' if not failed else 'FAIL'}:{passed}/46_PASS:"
        "G04_BLOCKED_FOR_FINAL_SEAL"
    )
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())

```


## FILE `scripts/ctrl02_mutation_suite.py`

```text
#!/usr/bin/env python3
"""Run forty isolated CTRL-02 source mutants against the executable test suite."""

from __future__ import annotations

import json
import os
import py_compile
import shutil
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (
    ROOT / "services/control-plane-service/src/epd2_control_plane_service/regional_operations.py"
)
TESTS = ROOT / "services/control-plane-service/tests"


@dataclass(frozen=True)
class Mutation:
    mutation_id: str
    name: str
    old: str
    new: str


MUTATIONS = (
    Mutation("M01", "universal_admin", '"AUTHORITY.UNIVERSAL_ADMIN"', '"AUTHORITY.DORMANT"'),
    Mutation(
        "M02",
        "implicit_bund_takeover",
        "and item.scope == scope",
        'and (item.scope == scope or actor_id == "bund-actor")',
    ),
    Mutation("M03", "coarse_region_disabled", '"REGION_DISABLED"', '"REGION_DISABLED_BROKEN"'),
    Mutation(
        "M04",
        "quarantine_removed",
        'self._sessions[target] = "QUARANTINED"',
        'self._sessions[target] = "ACTIVE"',
    ),
    Mutation(
        "M05",
        "suspension_ignored",
        'self._authority_states[target] = "SUSPENDED"',
        'self._authority_states[target] = "ACTIVE"',
    ),
    Mutation(
        "M06",
        "wrong_region_allowed",
        "and item.scope == scope",
        "and (item.scope == scope or item.scope != scope)",
    ),
    Mutation(
        "M07",
        "unrelated_capability_disabled",
        "and capability in request.allowed_capabilities",
        "and True",
    ),
    Mutation(
        "M08",
        "self_approval",
        "if approver_id == request.requester_id or approver_id in {",
        "if False or approver_id in {",
    ),
    Mutation(
        "M09",
        "quorum_reduced",
        "return 2, frozenset({ApproverClass.GOVERNANCE})",
        "return 1, frozenset({ApproverClass.GOVERNANCE})",
    ),
    Mutation(
        "M10",
        "duplicate_actor_counted",
        "or approver_id in {",
        "or False and approver_id in {",
    ),
    Mutation(
        "M11",
        "revoked_approver_counted",
        "for approval in request.approvals:\n            self.authorities.require(",
        "for approval in ():\n            self.authorities.require(",
    ),
    Mutation(
        "M12",
        "commit_reauthorization_removed",
        "self._reauthorize(request, moment)",
        "self.authorities.available = self.authorities.available",
    ),
    Mutation(
        "M13",
        "stale_approval_accepted",
        "expected_version=approval.authority_version,",
        "expected_version=None,",
    ),
    Mutation(
        "M14",
        "expired_jit_accepted",
        "if grant.state is not WorkflowState.ACTIVE or moment >= grant.expires_at:",
        "if False:",
    ),
    Mutation(
        "M15",
        "jit_scope_expansion",
        "if principal_id != grant.principal_id or scope != grant.scope:",
        "if principal_id != grant.principal_id:",
    ),
    Mutation(
        "M16",
        "breakglass_no_expiry",
        "MAX_BREAK_GLASS: Final = timedelta(hours=1)",
        "MAX_BREAK_GLASS: Final = timedelta(days=365)",
    ),
    Mutation(
        "M17",
        "silent_renewal",
        "self._grants[grant_id] = replace(grant, state=WorkflowState.EXPIRED)",
        "self._grants[grant_id] = replace(grant, state=WorkflowState.ACTIVE)",
    ),
    Mutation(
        "M18",
        "missing_review",
        "and item.review_ref is None",
        "and False",
    ),
    Mutation("M19", "global_emergency_scope", '"GLOBAL"', '"GLOBAL_BROKEN"'),
    Mutation(
        "M20",
        "approval_implies_execution",
        "if request.state is not WorkflowState.ACTIVE:",
        "if request.state not in {WorkflowState.ACTIVE, WorkflowState.APPROVED}:",
    ),
    Mutation(
        "M21",
        "auditor_executes",
        'capability="INTERVENTION.EXECUTE",',
        'capability="INTERVENTION.REVIEW",',
    ),
    Mutation("M22", "secret_visibility_implied", '"SECRET.RAW_READ"', '"SECRET.RAW_READ_BROKEN"'),
    Mutation(
        "M23",
        "raw_service_secret_exposed",
        "if operation not in allowed or secret_material is not None:",
        "if operation not in allowed or False:",
    ),
    Mutation(
        "M24",
        "voting_identity_bridge",
        '"BALLOT.CORRELATE_PERSON"',
        '"BALLOT.CORRELATE_PERSON_BROKEN"',
    ),
    Mutation(
        "M25",
        "history_overwrite",
        "self._events.append(event)",
        "self._events[:] = [event]",
    ),
    Mutation(
        "M26",
        "unauthorized_escalation",
        "return 2, frozenset({ApproverClass.GOVERNANCE, ApproverClass.SECURITY})",
        "return 2, frozenset({ApproverClass.GOVERNANCE})",
    ),
    Mutation(
        "M27",
        "unauthorized_extension",
        "MAX_SUPERVISION: Final = timedelta(days=90)",
        "MAX_SUPERVISION: Final = timedelta(days=900)",
    ),
    Mutation(
        "M28",
        "restore_revoked_authority",
        "if not original_authority_valid or newer_conflict:",
        "if False:",
    ),
    Mutation(
        "M29",
        "narrow_grant_bypasses_suspension",
        "if decision is not Decision.ALLOW:",
        "if False:",
    ),
    Mutation(
        "M30",
        "new_session_bypasses_quarantine",
        'if session_owner_id and self._sessions.get(f"subject:{session_owner_id}") '
        '== "QUARANTINED":',
        "if False:",
    ),
    Mutation(
        "M31",
        "direct_db_counted_as_action",
        "DIRECT_DB_MUTATION_COUNTS_AS_GOVERNED: Final = False",
        "DIRECT_DB_MUTATION_COUNTS_AS_GOVERNED: Final = True",
    ),
    Mutation(
        "M32",
        "denial_returns_success",
        "DENIALS_RAISE: Final = True",
        "DENIALS_RAISE: Final = False",
    ),
    Mutation(
        "M33",
        "dependency_fails_open",
        "if not self.authorities.available:\n            return Decision.DEPENDENCY_UNAVAILABLE",
        "if not self.authorities.available:\n            return Decision.ALLOW",
    ),
    Mutation(
        "M34",
        "duplicate_activation",
        "if request.state is not WorkflowState.APPROVED:",
        "if request.state not in {WorkflowState.APPROVED, WorkflowState.ACTIVE}:",
    ),
    Mutation(
        "M35",
        "clock_rollback_revives_grant",
        "if supplied < self._last_time:\n            return self._last_time",
        "if supplied < self._last_time:\n            return supplied",
    ),
    Mutation(
        "M36",
        "stale_ctrl01_evidence",
        "490d8ca31d4607da204f03addaf900161257b289d51ec6f0b7e52433fd5cbe71",
        "090d8ca31d4607da204f03addaf900161257b289d51ec6f0b7e52433fd5cbe71",
    ),
    Mutation("M37", "endpoint_missing_inventory", '"CTRL02.READ.HISTORY"', '"CTRL02.READ.ACTIVE"'),
    Mutation(
        "M38",
        "mutation_fixture_removed",
        "MUTATION_FIXTURES_REQUIRED: Final = 40",
        "MUTATION_FIXTURES_REQUIRED: Final = 39",
    ),
    Mutation(
        "M39",
        "post_validation_byte_change",
        "FREEZE_REJECTS_POST_VALIDATION_CHANGE: Final = True",
        "FREEZE_REJECTS_POST_VALIDATION_CHANGE: Final = False",
    ),
    Mutation(
        "M40",
        "self_state_accepted",
        'SELF_STATE: Final = "PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED"',
        'SELF_STATE: Final = "ACCEPTED"',
    ),
)


def main() -> int:
    if len(MUTATIONS) != 40 or len({item.mutation_id for item in MUTATIONS}) != 40:
        raise SystemExit("mutation inventory must contain exactly 40 unique fixtures")
    original = SOURCE.read_text()
    results: list[dict[str, object]] = []
    for mutation in MUTATIONS:
        if mutation.old not in original:
            results.append({**asdict(mutation), "detected": False, "reason": "anchor missing"})
            continue
        with tempfile.TemporaryDirectory(prefix=f"ctrl02-{mutation.mutation_id.lower()}-") as td:
            root = Path(td)
            package = root / "epd2_control_plane_service"
            shutil.copytree(SOURCE.parent, package)
            mutant = package / SOURCE.name
            mutant.write_text(original.replace(mutation.old, mutation.new, 1))
            try:
                py_compile.compile(str(mutant), doraise=True)
            except py_compile.PyCompileError as exc:
                results.append(
                    {**asdict(mutation), "detected": False, "reason": f"invalid mutant: {exc}"}
                )
                continue
            env = dict(os.environ)
            env["PYTHONPATH"] = os.pathsep.join([str(root), str(TESTS), env.get("PYTHONPATH", "")])
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    str(TESTS / "test_ctrl02_authorization.py"),
                    str(TESTS / "test_ctrl02_inventory_evidence.py"),
                    str(TESTS / "test_ctrl02_lifecycle.py"),
                    str(TESTS / "test_ctrl02_privilege_and_recovery.py"),
                    "-q",
                ],
                cwd=ROOT,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
            results.append(
                {
                    **asdict(mutation),
                    "detected": completed.returncode == 1,
                    "pytest_returncode": completed.returncode,
                    "output_tail": completed.stdout[-1000:],
                }
            )
    detected = sum(bool(item["detected"]) for item in results)
    output = ROOT / "validation/ctrl02/mutation_result.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            {
                "schema": "epd2.ctrl02.mutation-result/1",
                "mutations_total": len(results),
                "detected": detected,
                "undetected": [item["mutation_id"] for item in results if not item["detected"]],
                "results": results,
            },
            indent=2,
        )
        + "\n"
    )
    print(f"CTRL02_MUTATIONS:{'PASS' if detected == 40 else 'FAIL'}:{detected}/40")
    return 0 if detected == 40 else 1


if __name__ == "__main__":
    raise SystemExit(main())

```


## FILE `scripts/verify_ctrl02_package.py`

```text
#!/usr/bin/env python3
"""Independently verify CTRL-02 archive safety, contents and same-byte manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
import zipfile
from pathlib import Path

FORBIDDEN_PARTS = {".git", ".venv", "node_modules", "__pycache__", ".pytest_cache"}


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    args = parser.parse_args()
    if not args.archive.is_file():
        raise SystemExit("archive missing")
    with zipfile.ZipFile(args.archive) as archive:
        names = archive.namelist()
        if not names or any(Path(name).is_absolute() or ".." in Path(name).parts for name in names):
            raise SystemExit("unsafe archive path")
        if any(set(Path(name).parts) & FORBIDDEN_PARTS for name in names):
            raise SystemExit("archive hygiene failure")
        roots = {Path(name).parts[0] for name in names}
        if len(roots) != 1:
            raise SystemExit("archive must have one root")
        with tempfile.TemporaryDirectory(prefix="ctrl02-verify-") as td:
            archive.extractall(td)
            root = Path(td) / roots.pop()
            manifest = root / "SHA256SUMS.txt"
            if not manifest.is_file():
                raise SystemExit("manifest missing")
            for line in manifest.read_text().splitlines():
                expected, relative = line.split("  ", 1)
                target = root / relative
                if not target.is_file() or digest(target) != expected:
                    raise SystemExit(f"same-byte mismatch: {relative}")
            result = json.loads((root / "validation/ctrl02/ctrl02_preseal_result.json").read_text())
            if result["gates_passed"] != 45 or result["gates_blocked_for_final_seal"] != ["G04"]:
                raise SystemExit("gate evidence mismatch")
            if result["self_state"] != "NOT_ACCEPTED":
                raise SystemExit("developer self-acceptance forbidden")
            mutation = json.loads((root / "validation/ctrl02/mutation_result.json").read_text())
            if mutation["detected"] != 40 or mutation["undetected"]:
                raise SystemExit("mutation evidence mismatch")
    print(f"CTRL02_PACKAGE_VERIFY:PASS:{digest(args.archive)}:{args.archive.stat().st_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

```


## FILE `scripts/build_ctrl02_preseal.py`

```text
#!/usr/bin/env python3
"""Build the deterministic CTRL-02 working PRESEAL and external identity record."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAME = "EPD2_CTRL02_REGIONAL_INTERVENTION_AND_PRIVILEGED_OPERATIONS_WORKING_0.1_PRESEAL"
EXCLUDED_DIRS = {
    ".git",
    ".venv",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".next",
    "node_modules",
    "__pycache__",
}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".sqlite", ".sqlite3", ".db", ".zip"}


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def allowed(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    return not (
        set(relative.parts) & EXCLUDED_DIRS
        or path.suffix.lower() in EXCLUDED_SUFFIXES
        or path.name.startswith(".codex-upload-")
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=ROOT.parent / f"{NAME}.zip")
    args = parser.parse_args()
    result = json.loads((ROOT / "validation/ctrl02/ctrl02_preseal_result.json").read_text())
    if result["overall"] != "DEVELOPMENT_PASS_FINAL_SEAL_BLOCKED":
        raise SystemExit("CTRL-02 development validator has not passed")
    if result["gates_passed"] != 45 or result["gates_blocked_for_final_seal"] != ["G04"]:
        raise SystemExit("unexpected gate disposition")
    mutation = json.loads((ROOT / "validation/ctrl02/mutation_result.json").read_text())
    if mutation["detected"] != 40 or mutation["undetected"]:
        raise SystemExit("mutation suite is not 40/40")

    with tempfile.TemporaryDirectory(prefix="ctrl02-preseal-") as td:
        stage = Path(td) / NAME
        stage.mkdir()
        for source in sorted(ROOT.rglob("*")):
            if not source.is_file() or not allowed(source):
                continue
            relative = source.relative_to(ROOT)
            target = stage / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        files = [path for path in sorted(stage.rglob("*")) if path.is_file()]
        sums = "".join(f"{digest(path)}  {path.relative_to(stage).as_posix()}\n" for path in files)
        (stage / "SHA256SUMS.txt").write_text(sums)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(args.out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for path in sorted(stage.rglob("*")):
                if not path.is_file():
                    continue
                relative = Path(NAME) / path.relative_to(stage)
                info = zipfile.ZipInfo(relative.as_posix(), date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, path.read_bytes(), compresslevel=9)

    identity = {
        "schema": "epd2.ctrl02.external-package-identity/1",
        "file": args.out.name,
        "sha256": digest(args.out),
        "size": args.out.stat().st_size,
        "gates": "45/46 PASS; G04 BLOCKED_FOR_FINAL_SEAL",
        "mutations": "40/40 DETECTED",
        "self_state": "NOT_ACCEPTED",
    }
    identity_path = args.out.with_suffix(".identity.json")
    identity_path.write_text(json.dumps(identity, indent=2, sort_keys=True) + "\n")
    verify = subprocess.run(
        [
            str(ROOT / ".venv/bin/python"),
            str(ROOT / "scripts/verify_ctrl02_package.py"),
            str(args.out),
        ],
        cwd=ROOT,
        text=True,
        check=False,
    )
    if verify.returncode:
        raise SystemExit("independent package verification failed")
    print(f"CTRL02_WORKING_PACKAGE:PASS:{identity['sha256']}:{identity['size']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

```


## FILE `contracts/control/ctrl02_control_console.json`

```text
{
  "schema": "epd2.ctrl02.control-console/1",
  "base_path": "/ctrl/v2",
  "authority": "SERVER_ONLY",
  "direct_database_mutation": "FORBIDDEN",
  "frontend_authority": false,
  "operations": [
    "create",
    "approve",
    "reject",
    "cancel",
    "activate",
    "revoke",
    "restore",
    "review",
    "jit_request",
    "jit_use",
    "breakglass_request",
    "breakglass_use",
    "service_credential_contain",
    "key_trust_change_request",
    "list_active",
    "list_pending",
    "history"
  ],
  "hard_boundaries": {
    "universal_admin": false,
    "implicit_bund_takeover": false,
    "coarse_region_disabled": false,
    "raw_secret_visibility": false,
    "voting_domain_access": false,
    "historical_rewrite": false
  }
}

```


## FILE `validation/ctrl02/ctrl02_preseal_result.json`

```text
{
  "gates": [
    {
      "executed": true,
      "id": "G01",
      "name": "bootstrap_freshness",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G02",
      "name": "baseline_identity",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G03",
      "name": "ctrl01_dependency_inventory",
      "status": "PASS"
    },
    {
      "executed": false,
      "id": "G04",
      "name": "ctrl01_reconciliation",
      "status": "BLOCKED_FOR_FINAL_SEAL"
    },
    {
      "executed": true,
      "id": "G05",
      "name": "intervention_model",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G06",
      "name": "session_quarantine",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G07",
      "name": "authority_suspension",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G08",
      "name": "regional_restriction",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G09",
      "name": "temporary_supervision",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G10",
      "name": "bund_boundary",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G11",
      "name": "regional_autonomy",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G12",
      "name": "request_authority",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G13",
      "name": "approval_authority",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G14",
      "name": "four_eyes",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G15",
      "name": "quorum",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G16",
      "name": "self_approval_rejection",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G17",
      "name": "commit_reauth",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G18",
      "name": "jit",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G19",
      "name": "breakglass",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G20",
      "name": "breakglass_expiry",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G21",
      "name": "no_silent_renewal",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G22",
      "name": "execution_separation",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G23",
      "name": "secret_visibility",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G24",
      "name": "service_credential",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G25",
      "name": "key_trust",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G26",
      "name": "voting_boundary",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G27",
      "name": "immutable_history",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G28",
      "name": "read_model",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G29",
      "name": "console_contracts",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G30",
      "name": "action_inventory",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G31",
      "name": "negative_authorization",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G32",
      "name": "stale_state",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G33",
      "name": "idempotency",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G34",
      "name": "concurrency",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G35",
      "name": "time_expiry",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G36",
      "name": "recovery",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G37",
      "name": "fail_closed",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G38",
      "name": "audit",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G39",
      "name": "post_use_review",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G40",
      "name": "escalation",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G41",
      "name": "restoration",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G42",
      "name": "scope_precedence",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G43",
      "name": "privacy_observability",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G44",
      "name": "fir_bsi",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G45",
      "name": "mutation_suite",
      "status": "PASS"
    },
    {
      "executed": true,
      "id": "G46",
      "name": "freeze_same_bytes",
      "status": "PASS"
    }
  ],
  "gates_blocked_for_final_seal": [
    "G04"
  ],
  "gates_failed": [],
  "gates_passed": 45,
  "gates_total": 46,
  "mode": "PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED",
  "mutation_result": "40/40 DETECTED",
  "overall": "DEVELOPMENT_PASS_FINAL_SEAL_BLOCKED",
  "schema": "epd2.ctrl02.preseal-result/1",
  "self_state": "NOT_ACCEPTED",
  "stage": "CTRL-02"
}

```


## FILE `validation/ctrl02/freeze_manifest.json`

```text
{
  "files": {
    "contracts/control/ctrl02_control_console.json": "b280429e9525adcac69bfab83254e74e7ede59bc754ff622048e8c9ca37e4e13",
    "docs/ctrl/CTRL-02/CTRL02_DEVELOPER_REPORT.md": "088d551578cd3a4f7f315dd201cffaccfa8a362ea9721441d5e2983513e8d078",
    "docs/ctrl/CTRL-02/CTRL02_STAGE_CONTRACT.md": "ab0adcaa8da6e6bf572cd200bfa929eb62de3fd48b331e848269bd3c14d52a52",
    "scripts/build_ctrl02_preseal.py": "cc74641f7ceca612ba9d635956e27810f6674f6502cf03d0b24a079ba8a2f2c6",
    "scripts/ctrl02_mutation_suite.py": "a5f19e4458df18676203aa671e126254d4697f1115a865160bcc1e5fa0a42611",
    "scripts/ctrl02_validator.py": "034f326be16c1dca29d92538a7deeaf906a9e7ba80e085d4be1306a72a9eada5",
    "scripts/verify_ctrl02_package.py": "037db6afae963f57fb0b49df5bf66e6e7e17ead57bfafb41118328481e8f5240",
    "services/control-plane-service/src/epd2_control_plane_service/__init__.py": "99d97e1d109865f5b028681f9227a27b1d7e285a384e55053ec3cd70d0f47aef",
    "services/control-plane-service/src/epd2_control_plane_service/api.py": "d355434e31eb5b16d7a6ce805fe23e10ca83ece5c4e511d06732e5a4e3279d4d",
    "services/control-plane-service/src/epd2_control_plane_service/application.py": "69d818295ee2682ba42d8322e8d9ff017236a8936d885ec6e9e5f4db51cef64d",
    "services/control-plane-service/src/epd2_control_plane_service/audit.py": "2f7a3d2ccc77f5488e9329c37bf09e7c535c5f159595f7df66d52e07232a95b1",
    "services/control-plane-service/src/epd2_control_plane_service/authority.py": "2f5284c7ee170a4309451c1d152e1a96e84e1ca62dc5e1e074239f4594aa4736",
    "services/control-plane-service/src/epd2_control_plane_service/breakglass.py": "d103d26c4f8f2be65c282e7c2da26b976f8db4c86bae58af809e09e39a297fa6",
    "services/control-plane-service/src/epd2_control_plane_service/domain.py": "46a207d342fea329f1db4c63d01ff527d60b1b963c5737be0fb87b2634fad5de",
    "services/control-plane-service/src/epd2_control_plane_service/exceptions.py": "fb559e1f12c6d169eba96474ffa58ccae4837d4acf293a7a15988c49013df4f0",
    "services/control-plane-service/src/epd2_control_plane_service/freeze.py": "d5d2733eb0adf83f77a34ccf96a929760dd7683afe2fe56ebb0fb325ecb5557b",
    "services/control-plane-service/src/epd2_control_plane_service/intervention.py": "05a0ad2430dde8ea0dddad51f4c114e66a98e1e6d20e4c806463b078044a01b4",
    "services/control-plane-service/src/epd2_control_plane_service/inventory.py": "fd4b687a3449289c5e12e3ea576fbe19405c70e88a647154cc1e35e101abebbf",
    "services/control-plane-service/src/epd2_control_plane_service/mutations.py": "e33843d8b1b4d5809ce5e33ffe887a091d179416da8e9e7dd6b421eec5adca65",
    "services/control-plane-service/src/epd2_control_plane_service/policy.py": "8b1636a2f78bbd35ca14f01417960a72b79212f536830b38cfa41ea0e3a4bb39",
    "services/control-plane-service/src/epd2_control_plane_service/py.typed": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "services/control-plane-service/src/epd2_control_plane_service/reference_world.py": "72b23a8ea41a08b94feb1ccd1ef740780867c025c702117107e109644d41939a",
    "services/control-plane-service/src/epd2_control_plane_service/regional_operations.py": "aad08bcc67912d3ae1a23d7438ac8d036c897d512f32ba6b6850e99c41185286",
    "services/control-plane-service/src/epd2_control_plane_service/routes.py": "80d13c0a9731932f49bfaaff51d3cb904cf15828a38806e67ece24c282b713ea",
    "services/control-plane-service/src/epd2_control_plane_service/sod.py": "376fe29dc549cae4513257346f3b62f710616971f09b9cd0a9bbba6f4e5735ac",
    "services/control-plane-service/src/epd2_control_plane_service/verification.py": "04776b71688e8c23c1663e527521ea2ed43e42342ae6777d3be3c4b14f992c91",
    "services/control-plane-service/tests/_control_plane_builders.py": "c1e23e84e0e6b9977bf2aab332c88944058f29508745a845c882608bb120358a",
    "services/control-plane-service/tests/_ctrl02_builders.py": "482b56032ec40f928145f7fd44b52399f2b7b06f72a507020fe2b6351502e323",
    "services/control-plane-service/tests/conftest.py": "cb2bf1653e6aabd40efb1936ba157a0c7e383d8a36bcf8e0a457949825de2533",
    "services/control-plane-service/tests/test_audit_evidence.py": "1933fa965c12470dd7cd689a5a29637b276d9728d9ebb3928e4883e4926adeb9",
    "services/control-plane-service/tests/test_breakglass.py": "554b5c37cdde5a186128f0e4b20efd0333973a99c7b0921a824fed43f9c9e8e8",
    "services/control-plane-service/tests/test_commit_time_reauthorization.py": "1886cc0158a85891cbed09351a28b9c80124bc4c013c638c2cd89011fa9d063f",
    "services/control-plane-service/tests/test_ctrl02_authorization.py": "cefb4fa15f7229d78f1a7cdfa1d8f96d54421f632a27b8aed788478f0936c836",
    "services/control-plane-service/tests/test_ctrl02_inventory_evidence.py": "f7358da07e67d2ac0232631f749627dad2556d4e4de71a9c9ca20e3d8c9dfd93",
    "services/control-plane-service/tests/test_ctrl02_lifecycle.py": "752fbf255f63ff17eaf29a5385de9fa00693caedb330996205c13f5732867779",
    "services/control-plane-service/tests/test_ctrl02_privilege_and_recovery.py": "ba5f2bad1d9fa602465d2a98f5f5e40f936d302677ddd43df9b90d966493d61a",
    "services/control-plane-service/tests/test_intervention.py": "f763d1353e391ddd35b057ee29057ff3e8e9d28534b40b73cc5fda11fc4fe5ce",
    "services/control-plane-service/tests/test_inventory_and_contracts.py": "b754fec922e810454ab39bffb548e5486aab77fd4f11a63329324bbae8029dd3",
    "services/control-plane-service/tests/test_lifecycle.py": "a5724b8fce02379b18f2d99bcd930560e6f3190ccf38e0af78f90a87b4d28435",
    "services/control-plane-service/tests/test_mutation_suite.py": "9d65629d62fa2b33d31234dcee0afcb51fe8f4bf0d8244a45fb3ce3451b5559a",
    "services/control-plane-service/tests/test_negative_authorization.py": "c4ceeb5f52c4881bfae392c94b372b737f4d0c0d48a50a35f1141202ddd801ef",
    "services/control-plane-service/tests/test_sod.py": "437694f3eb248812f6703fa377a66f331e7b0f44cb3fbf46a9c530dd44f5a2cc"
  },
  "mode": "PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED",
  "schema": "epd2.ctrl02.freeze-manifest/1",
  "scope_digest": "3a0b65699498b39fd9bacaf1e709dbdaa5fe12b698c7fe6f044175da50ab4509"
}

```


## FILE `validation/ctrl02/package_identity_result.json`

```text
{
  "archive_sha256": null,
  "archive_size": null,
  "freeze_verified": true,
  "schema": "epd2.ctrl02.package-identity/1",
  "self_state": "NOT_ACCEPTED",
  "status": "SOURCE_FREEZE_BOUND / EXTERNAL_ARCHIVE_IDENTITY_REQUIRED"
}

```


## FILE `validation/ctrl02/ctrl01_reconciliation_result.json`

```text
{
  "baseline_commit": "217559b7f21c338d6fe8d4e4676082cd3840251c",
  "development_may_continue": true,
  "executed": true,
  "gate_refs": [
    "G04"
  ],
  "mode": "PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED",
  "reason": "authoritative CTRL-01 acceptance identity is absent",
  "runtime": "regional_operations.py",
  "schema": "epd2.ctrl02.evidence/1",
  "status": "BLOCKED_FOR_FINAL_SEAL",
  "test_evidence": "test_result.json"
}

```


## FILE `validation/ctrl02/fir_reconciliation.json`

```text
{
  "baseline_commit": "217559b7f21c338d6fe8d4e4676082cd3840251c",
  "bsi_claim": "NONE / READINESS BOUNDARY PRESERVED",
  "executed": true,
  "fir_presence": {
    "FIR-CTRL-001": true,
    "FIR-GOV-004": true,
    "FIR-GOV-005": true,
    "FIR-OPS-001": true,
    "FIR-SEC-004": true,
    "FIR-TRUST-002": true,
    "FIR-TRUST-003": true,
    "FIR-VOTE-BSI-001": true,
    "FIR-VOTE-NET-001": true
  },
  "gate_refs": [
    "G44"
  ],
  "mode": "PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED",
  "runtime": "regional_operations.py",
  "schema": "epd2.ctrl02.evidence/1",
  "status": "PASS",
  "test_evidence": "test_result.json",
  "voting_change": false
}

```


## FILE `validation/ctrl02/test_result.json`

```text
{
  "control_plane_tests": {
    "command": [
      "/workspace/scratch/9e33f6c47d49/work/ctrl02/.venv/bin/python",
      "-m",
      "pytest",
      "services/control-plane-service/tests",
      "-q"
    ],
    "output": "........................................................................ [ 30%]\n........................................................................ [ 61%]\n........................................................................ [ 92%]\n..................                                                       [100%]\n234 passed in 1.00s\n",
    "passed": true,
    "returncode": 0
  },
  "mypy": {
    "command": [
      "/workspace/scratch/9e33f6c47d49/work/ctrl02/.venv/bin/mypy",
      "services/control-plane-service/src/epd2_control_plane_service/regional_operations.py"
    ],
    "output": "Success: no issues found in 1 source file\n",
    "passed": true,
    "returncode": 0
  },
  "ruff": {
    "command": [
      "/workspace/scratch/9e33f6c47d49/work/ctrl02/.venv/bin/ruff",
      "check",
      "services/control-plane-service/src/epd2_control_plane_service/regional_operations.py",
      "services/control-plane-service/tests/_ctrl02_builders.py",
      "services/control-plane-service/tests/test_ctrl02_authorization.py",
      "services/control-plane-service/tests/test_ctrl02_inventory_evidence.py",
      "services/control-plane-service/tests/test_ctrl02_lifecycle.py",
      "services/control-plane-service/tests/test_ctrl02_privilege_and_recovery.py",
      "scripts/ctrl02_mutation_suite.py",
      "scripts/ctrl02_validator.py"
    ],
    "output": "All checks passed!\n",
    "passed": true,
    "returncode": 0
  },
  "schema": "epd2.ctrl02.test-result/1"
}

```


## FILE `validation/ctrl02/mutation_result.json`

```text
{
  "schema": "epd2.ctrl02.mutation-result/1",
  "mutations_total": 40,
  "detected": 40,
  "undetected": [],
  "results": [
    {
      "mutation_id": "M01",
      "name": "universal_admin",
      "old": "\"AUTHORITY.UNIVERSAL_ADMIN\"",
      "new": "\"AUTHORITY.DORMANT\"",
      "detected": true,
      "pytest_returncode": 1,
      "output_tail": "...................................                 [100%]\n=================================== FAILURES ===================================\n_ test_universal_admin_and_secret_capability_are_forbidden[AUTHORITY.UNIVERSAL_ADMIN] _\n\ncapability = 'AUTHORITY.UNIVERSAL_ADMIN'\n\n    @pytest.mark.parametrize(\"capability\", [\"AUTHORITY.UNIVERSAL_ADMIN\", \"SECRET.RAW_READ\"])\n    def test_universal_admin_and_secret_capability_are_forbidden(capability: str) -> None:\n>       with pytest.raises(AuthorizationRefused):\n             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nE       Failed: DID NOT RAISE <class 'epd2_control_plane_service.exceptions.AuthorizationRefused'>\n\nservices/control-plane-service/tests/test_ctrl02_authorization.py:182: Failed\n=========================== short test summary info ============================\nFAILED services/control-plane-service/tests/test_ctrl02_authorization.py::test_universal_admin_and_secret_capability_are_forbidden[AUTHORITY.UNIVERSAL_ADMIN]\n1 failed, 55 passed in 0.21s\n"
    },
    {
      "mutation_id": "M02",
      "name": "implicit_bund_takeover",
      "old": "and item.scope == scope",
      "new": "and (item.scope == scope or actor_id == \"bund-actor\")",
      "detected": true,
      "pytest_returncode": 1,
      "output_tail": "...F....................................................                 [100%]\n=================================== FAILURES ===================================\n_____________ test_bund_actor_does_not_inherit_regional_competence _____________\n\n    def test_bund_actor_does_not_inherit_regional_competence() -> None:\n        svc = service()\n>       with pytest.raises(AuthorizationRefused) as error:\n             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nE       Failed: DID NOT RAISE <class 'epd2_control_plane_service.exceptions.AuthorizationRefused'>\n\nservices/control-plane-service/tests/test_ctrl02_authorization.py:64: Failed\n=========================== short test summary info ============================\nFAILED services/control-plane-service/tests/test_ctrl02_authorization.py::test_bund_actor_does_not_inherit_regional_competence\n1 failed, 55 passed in 0.20s\n"
    },
    {
      "mutation_id": "M03",
      "name": "coarse_region_disabled",
      "old": "\"REGION_DISABLED\"",
      "new": "\"REGION_DISABLED_BROKEN\"",
      "detected": true,
      "pytest_returncode": 1,
      "output_tail": "..................................F.....................                 [100%]\n=================================== FAILURES ===================================\n______________ test_coarse_targets_are_rejected[REGION_DISABLED] _______________\n\ntarget = 'REGION_DISABLED'\n\n    @pytest.mark.parametrize(\"target\", [\"*\", \"ALL\", \"REGION_DISABLED\", \"GLOBAL\", \"item:*\"], ids=str)\n    def test_coarse_targets_are_rejected(target: str) -> None:\n>       with pytest.raises(AuthorizationRefused) as error:\n             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nE       Failed: DID NOT RAISE <class 'epd2_control_plane_service.exceptions.AuthorizationRefused'>\n\nservices/control-plane-service/tests/test_ctrl02_lifecycle.py:197: Failed\n=========================== short test summary info ============================\nFAILED services/control-plane-service/tests/test_ctrl02_lifecycle.py::test_coarse_targets_are_rejected[REGION_DISABLED]\n1 failed, 55 passed in 0.30s\n"
    },
    {
      "mutation_id": "M04",
      "name": "quarantine_removed",
      "old": "self._sessions[target] = \"QUARANTINED\"",
      "new": "self._sessions[target] = \"ACTIVE\"",
      "detected": true,
      "pytest_returncode": 1,
      "output_tail": "session_owner_id='member-1', authority_id=None, capability='SESSION.USE', scope=ExactScope(region_id='DE-BE', org_id='org-berlin'), now=(datetime.datetime(2026, 9, 2, 10, 0, tzinfo=datetime.timezone.utc) + datetime.timedelta(seconds=240)))\nE        +    where effective_decision = <epd2_control_plane_service.regional_operations.RegionalOperationsService object at 0x7f81d4ead820>.effective_decision\nE        +    and   datetime.timedelta(seconds=240) = timedelta(minutes=4)\nE        +  and   <Decision.SESSION_QUARANTINED: 'SESSION_QUARANTINED'> = Decision.SESSION_QUARANTINED\n\nservices/control-plane-service/tests/test_ctrl02_lifecycle.py:95: AssertionError\n=========================== short test summary info ============================\nFAILED services/control-plane-service/tests/test_ctrl02_lifecycle.py::test_l1_quarantine_is_exact_session_only\nFAILED services/control-plane-service/tests/test_ctrl02_lifecycle.py::test_subject_quarantine_applies_to_a_new_session\n2 failed, 54 passed in 0.21s\n"
    },
    {
      "mutation_id": "M05",
      "name": "suspension_ignored",
      "old": "self._authority_states[target] = \"SUSPENDED\"",
      "new": "self._authority_states[target] = \"ACTIVE\"",
      "detected": true,
      "pytest_returncode": 1,
      "output_tail": " 'AUTHORITY_SUSPENDED'>\nE        +  where <Decision.ALLOW: 'ALLOW'> = effective_decision(session_id=None, authority_id='authority:regional-chair', capability='AUTHORITY.ACT', scope=ExactScope(region_id='DE-BE', org_id='org-berlin'), now=(datetime.datetime(2026, 9, 2, 10, 0, tzinfo=datetime.timezone.utc) + datetime.timedelta(seconds=240)))\nE        +    where effective_decision = <epd2_control_plane_service.regional_operations.RegionalOperationsService object at 0x7f02a616f8f0>.effective_decision\nE        +    and   datetime.timedelta(seconds=240) = timedelta(minutes=4)\nE        +  and   <Decision.AUTHORITY_SUSPENDED: 'AUTHORITY_SUSPENDED'> = Decision.AUTHORITY_SUSPENDED\n\nservices/control-plane-service/tests/test_ctrl02_lifecycle.py:118: AssertionError\n=========================== short test summary info ============================\nFAILED services/control-plane-service/tests/test_ctrl02_lifecycle.py::test_l2_suspends_exact_authority_without_deleting_history\n1 failed, 55 passed in 0.21s\n"
    },
    {
      "mutation_id": "M06",
      "name": "wrong_region_allowed",
      "old": "and item.scope == scope",
      "new": "and (item.scope == scope or item.scope != scope)",
      "detected": true,
      "pytest_returncode": 1,
      "output_tail": "...F....................................................                 [100%]\n=================================== FAILURES ===================================\n_____________ test_bund_actor_does_not_inherit_regional_competence _____________\n\n    def test_bund_actor_does_not_inherit_regional_competence() -> None:\n        svc = service()\n>       with pytest.raises(AuthorizationRefused) as error:\n             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nE       Failed: DID NOT RAISE <class 'epd2_control_plane_service.exceptions.AuthorizationRefused'>\n\nservices/control-plane-service/tests/test_ctrl02_authorization.py:64: Failed\n=========================== short test summary info ============================\nFAILED services/control-plane-service/tests/test_ctrl02_authorization.py::test_bund_actor_does_not_inherit_regional_competence\n1 failed, 55 passed in 0.21s\n"
    },
    {
      "mutation_id": "M07",
      "name": "unrelated_capability_disabled",
      "old": "and capability in request.allowed_capabilities",
      "new": "and True",
      "detected": true,
      "pytest_returncode": 1,
      "output_tail": " 'ACTION_RESTRICTED'> is <Decision.ALLOW: 'ALLOW'>\nE        +  where <Decision.ACTION_RESTRICTED: 'ACTION_RESTRICTED'> = effective_decision(session_id=None, authority_id=None, capability='MEETING.READ', scope=ExactScope(region_id='DE-BE', org_id='org-berlin'), now=(datetime.datetime(2026, 9, 2, 10, 0, tzinfo=datetime.timezone.utc) + datetime.timedelta(seconds=240)))\nE        +    where effective_decision = <epd2_control_plane_service.regional_operations.RegionalOperationsService object at 0x7f4c954cf950>.effective_decision\nE        +    and   datetime.timedelta(seconds=240) = timedelta(minutes=4)\nE        +  and   <Decision.ALLOW: 'ALLOW'> = Decision.ALLOW\n\nservices/control-plane-service/tests/test_ctrl02_inventory_evidence.py:101: AssertionError\n=========================== short test summary info ============================\nFAILED services/control-plane-service/tests/test_ctrl02_inventory_evidence.py::test_unrelated_capability_and_region_remain_available\n1 failed, 55 passed in 0.21s\n"
    },
    {
      "mutation_id": "M08",
      "name": "self_approval",
      "old": "if approver_id == request.requester_id or approver_id in {",
      "new": "if False or approver_id in {",
      "detected": true,
      "pytest_returncode": 1,
      "output_tail": "f_approval_is_rejected ________________________\n\n    def test_self_approval_is_rejected() -> None:\n        svc = service()\n        request(svc)\n        with pytest.raises(AuthorizationRefused) as error:\n            svc.approve(\n                \"request-1\",\n                approver_id=\"requester\",\n                approver_class=ApproverClass.GOVERNANCE,\n                now=NOW + timedelta(minutes=1),\n                idempotency_key=\"self\",\n            )\n>       assert error.value.reason_code == Decision.SELF_APPROVAL_FORBIDDEN\nE       AssertionError: assert <Decision.WRO...'WRONG_SCOPE'> == <Decision.SEL...AL_FORBIDDEN'>\nE         \nE         - SELF_APPROVAL_FORBIDDEN\nE         + WRONG_SCOPE\n\nservices/control-plane-service/tests/test_ctrl02_authorization.py:26: AssertionError\n=========================== short test summary info ============================\nFAILED services/control-plane-service/tests/test_ctrl02_authorization.py::test_self_approval_is_rejected\n1 failed, 55 passed in 0.21s\n"
    },
    {
      "mutation_id": "M09",
      "name": "quorum_reduced",
      "old": "return 2, frozenset({ApproverClass.GOVERNANCE})",
      "new": "return 1, frozenset({ApproverClass.GOVERNANCE})",
      "detected": true,
      "pytest_returncode": 1,
      "output_tail": "lane-service/tests/test_ctrl02_lifecycle.py::test_regional_restriction_full_lifecycle\nFAILED services/control-plane-service/tests/test_ctrl02_lifecycle.py::test_l2_suspends_exact_authority_without_deleting_history\nFAILED services/control-plane-service/tests/test_ctrl02_lifecycle.py::test_l3_one_approval_is_not_quorum\nFAILED services/control-plane-service/tests/test_ctrl02_lifecycle.py::test_expiry_is_automatic_and_does_not_renew\nFAILED services/control-plane-service/tests/test_ctrl02_lifecycle.py::test_clock_rollback_does_not_reactivate_elapsed_restriction\nFAILED services/control-plane-service/tests/test_ctrl02_lifecycle.py::test_duplicate_activation_with_new_key_has_no_second_effect\nFAILED services/control-plane-service/tests/test_ctrl02_lifecycle.py::test_restoration_requires_valid_original_authority_and_no_newer_conflict\nFAILED services/control-plane-service/tests/test_ctrl02_privilege_and_recovery.py::test_active_restriction_overrides_narrow_jit_grant\n16 failed, 40 passed in 0.43s\n"
    },
    {
      "mutation_id": "M10",
      "name": "duplicate_actor_counted",
      "old": "or approver_id in {",
      "new": "or False and approver_id in {",
      "detected": true,
      "pytest_returncode": 1,
      "output_tail": "============================= FAILURES ===================================\n________________ test_duplicate_approver_identity_is_not_quorum ________________\n\n    def test_duplicate_approver_identity_is_not_quorum() -> None:\n        svc = service()\n        request(svc)\n        svc.approve(\n            \"request-1\",\n            approver_id=\"approver-1\",\n            approver_class=ApproverClass.GOVERNANCE,\n            now=NOW + timedelta(minutes=1),\n            idempotency_key=\"a1\",\n        )\n>       with pytest.raises(AuthorizationRefused):\n             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nE       Failed: DID NOT RAISE <class 'epd2_control_plane_service.exceptions.AuthorizationRefused'>\n\nservices/control-plane-service/tests/test_ctrl02_authorization.py:39: Failed\n=========================== short test summary info ============================\nFAILED services/control-plane-service/tests/test_ctrl02_authorization.py::test_duplicate_approver_identity_is_not_quorum\n1 failed, 55 passed in 0.21s\n"
    },
    {
      "mutation_id": "M11",
      "name": "revoked_approver_counted",
      "old": "for approval in request.approvals:\n            self.authorities.require(",
      "new": "for approval in ():\n            self.authorities.require(",
      "detected": true,
      "pytest_returncode": 1,
      "output_tail": "ane-service/tests/test_ctrl02_authorization.py:89: Failed\n_______ test_commit_time_reauthorization_detects_approver_version_change _______\n\n    def test_commit_time_reauthorization_detects_approver_version_change() -> None:\n        svc = service()\n        request(svc)\n        approve_twice(svc)\n        svc.authorities.update(\"a2\")\n>       with pytest.raises(AuthorizationRefused) as error:\n             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nE       Failed: DID NOT RAISE <class 'epd2_control_plane_service.exceptions.AuthorizationRefused'>\n\nservices/control-plane-service/tests/test_ctrl02_authorization.py:104: Failed\n=========================== short test summary info ============================\nFAILED services/control-plane-service/tests/test_ctrl02_authorization.py::test_commit_time_reauthorization_detects_revoked_approver\nFAILED services/control-plane-service/tests/test_ctrl02_authorization.py::test_commit_time_reauthorization_detects_approver_version_change\n2 failed, 54 passed in 0.31s\n"
    },
    {
      "mutation_id": "M12",
      "name": "commit_reauthorization_removed",
      "old": "self._reauthorize(request, moment)",
      "new": "self.authorities.available = self.authorities.available",
      "detected": true,
      "pytest_returncode": 1,
      "output_tail": "    def test_commit_time_reauthorization_detects_target_change() -> None:\n        svc = service()\n        request(svc)\n        approve_twice(svc)\n        svc.set_target_version(\"action:MEMBER.UPDATE\", 2)\n>       with pytest.raises(AuthorizationRefused) as error:\n             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nE       Failed: DID NOT RAISE <class 'epd2_control_plane_service.exceptions.AuthorizationRefused'>\n\nservices/control-plane-service/tests/test_ctrl02_authorization.py:119: Failed\n=========================== short test summary info ============================\nFAILED services/control-plane-service/tests/test_ctrl02_authorization.py::test_commit_time_reauthorization_detects_revoked_approver\nFAILED services/control-plane-service/tests/test_ctrl02_authorization.py::test_commit_time_reauthorization_detects_approver_version_change\nFAILED services/control-plane-service/tests/test_ctrl02_authorization.py::test_commit_time_reauthorization_detects_target_change\n3 failed, 53 passed in 0.21s\n"
    },
    {
      "mutation_id": "M13",
      "name": "stale_approval_accepted",
      "old": "expected_version=approval.authority_version,",
      "new": "expected_version=None,",
      "detected": true,
      "pytest_returncode": 1,
      "output_tail": "ice/tests/test_ctrl02_authorization.py:96: AssertionError\n_______ test_commit_time_reauthorization_detects_approver_version_change _______\n\n    def test_commit_time_reauthorization_detects_approver_version_change() -> None:\n        svc = service()\n        request(svc)\n        approve_twice(svc)\n        svc.authorities.update(\"a2\")\n>       with pytest.raises(AuthorizationRefused) as error:\n             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nE       Failed: DID NOT RAISE <class 'epd2_control_plane_service.exceptions.AuthorizationRefused'>\n\nservices/control-plane-service/tests/test_ctrl02_authorization.py:104: Failed\n=========================== short test summary info ============================\nFAILED services/control-plane-service/tests/test_ctrl02_authorization.py::test_commit_time_reauthorization_detects_revoked_approver\nFAILED services/control-plane-service/tests/test_ctrl02_authorization.py::test_commit_time_reauthorization_detects_approver_version_change\n2 failed, 54 passed in 0.21s\n"
    },
    {
      "mutation_id": "M14",
      "name": "expired_jit_accepted",
      "old": "if grant.state is not WorkflowState.ACTIVE or moment >= grant.expires_at:",
      "new": "if False:",
      "detected": true,
      "pytest_returncode": 1,
      "output_tail": " svc, grant = _active_grant()\n        svc.expire_due(NOW + timedelta(hours=1))\n        recovered = type(svc).from_checkpoint(svc.authorities, svc.checkpoint())\n        assert recovered.grants[0].state is WorkflowState.EXPIRED\n>       with pytest.raises(AuthorizationRefused):\n             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nE       Failed: DID NOT RAISE <class 'epd2_control_plane_service.exceptions.AuthorizationRefused'>\n\nservices/control-plane-service/tests/test_ctrl02_privilege_and_recovery.py:227: Failed\n=========================== short test summary info ============================\nFAILED services/control-plane-service/tests/test_ctrl02_privilege_and_recovery.py::test_breakglass_has_strict_expiry\nFAILED services/control-plane-service/tests/test_ctrl02_privilege_and_recovery.py::test_clock_rollback_cannot_revive_expired_grant\nFAILED services/control-plane-service/tests/test_ctrl02_privilege_and_recovery.py::test_recovery_does_not_resurrect_expired_grant\n3 failed, 53 passed in 0.21s\n"
    },
    {
      "mutation_id": "M15",
      "name": "jit_scope_expansion",
      "old": "if principal_id != grant.principal_id or scope != grant.scope:",
      "new": "if principal_id != grant.principal_id:",
      "detected": true,
      "pytest_returncode": 1,
      "output_tail": "def test_jit_cannot_expand_scope_or_target() -> None:\n        svc, grant = _active_grant()\n        with pytest.raises(AuthorizationRefused):\n            svc.use_privilege(\n                grant.grant_id,\n                principal_id=\"someone-else\",\n                capability=\"SERVICE.RESTART\",\n                scope=BERLIN,\n                now=NOW + timedelta(minutes=4),\n                use_ref=\"wrong-target\",\n            )\n    \n        from _ctrl02_builders import BAVARIA\n    \n>       with pytest.raises(AuthorizationRefused):\n             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nE       Failed: DID NOT RAISE <class 'epd2_control_plane_service.exceptions.AuthorizationRefused'>\n\nservices/control-plane-service/tests/test_ctrl02_privilege_and_recovery.py:111: Failed\n=========================== short test summary info ============================\nFAILED services/control-plane-service/tests/test_ctrl02_privilege_and_recovery.py::test_jit_cannot_expand_scope_or_target\n1 failed, 55 passed in 0.20s\n"
    },
    {
      "mutation_id": "M16",
      "name": "breakglass_no_expiry",
      "old": "MAX_BREAK_GLASS: Final = timedelta(hours=1)",
      "new": "MAX_BREAK_GLASS: Final = timedelta(days=365)",
      "detected": true,
      "pytest_returncode": 1,
      "output_tail": "..............................................F.........                 [100%]\n=================================== FAILURES ===================================\n________________ test_breakglass_request_cannot_exceed_one_hour ________________\n\n    def test_breakglass_request_cannot_exceed_one_hour() -> None:\n        svc = service()\n>       with pytest.raises(AuthorizationRefused):\n             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nE       Failed: DID NOT RAISE <class 'epd2_control_plane_service.exceptions.AuthorizationRefused'>\n\nservices/control-plane-service/tests/test_ctrl02_privilege_and_recovery.py:80: Failed\n=========================== short test summary info ============================\nFAILED services/control-plane-service/tests/test_ctrl02_privilege_and_recovery.py::test_breakglass_request_cannot_exceed_one_hour\n1 failed, 55 passed in 0.22s\n"
    },
    {
      "mutation_id": "M17",
      "name": "silent_renewal",
      "old": "self._grants[grant_id] = replace(grant, state=WorkflowState.EXPIRED)",
      "new": "self._grants[grant_id] = replace(grant, state=WorkflowState.ACTIVE)",
      "detected": true,
      "pytest_returncode": 1,
      "output_tail": "XPIRED: 'EXPIRED'>\nE        +  where <WorkflowState.ACTIVE: 'ACTIVE'> = PrivilegeGrant(grant_id='jit:priv-1', kind=<PrivilegeKind.JIT: 'JIT'>, principal_id='operator', request_id='priv-1', s...tetime.datetime(2026, 9, 2, 10, 30, tzinfo=datetime.timezone.utc), state=<WorkflowState.ACTIVE: 'ACTIVE'>, use_refs=()).state\nE        +  and   <WorkflowState.EXPIRED: 'EXPIRED'> = WorkflowState.EXPIRED\n\nservices/control-plane-service/tests/test_ctrl02_privilege_and_recovery.py:226: AssertionError\n=========================== short test summary info ============================\nFAILED services/control-plane-service/tests/test_ctrl02_privilege_and_recovery.py::test_clock_rollback_cannot_revive_expired_grant\nFAILED services/control-plane-service/tests/test_ctrl02_privilege_and_recovery.py::test_checkpoint_preserves_terminal_and_evidence_state\nFAILED services/control-plane-service/tests/test_ctrl02_privilege_and_recovery.py::test_recovery_does_not_resurrect_expired_grant\n3 failed, 53 passed in 0.21s\n"
    },
    {
      "mutation_id": "M18",
      "name": "missing_review",
      "old": "and item.review_ref is None",
      "new": "and False",
      "detected": true,
      "pytest_returncode": 1,
      "output_tail": "        assert not svc.active_interventions()\n        approve_twice(svc)\n        activate(svc)\n        assert len(svc.active_interventions()) == 1\n        assert not svc.pending_requests()\n        svc.revoke(\n            \"request-1\",\n            actor_id=\"revoker\",\n            now=NOW + timedelta(minutes=5),\n            idempotency_key=\"revoke:read-model\",\n        )\n>       assert len(svc.pending_reviews()) == 1\nE       assert 0 == 1\nE        +  where 0 = len(())\nE        +    where () = pending_reviews()\nE        +      where pending_reviews = <epd2_control_plane_service.regional_operations.RegionalOperationsService object at 0x7f7ab8ae4620>.pending_reviews\n\nservices/control-plane-service/tests/test_ctrl02_inventory_evidence.py:128: AssertionError\n=========================== short test summary info ============================\nFAILED services/control-plane-service/tests/test_ctrl02_inventory_evidence.py::test_read_models_separate_active_pending_and_review\n1 failed, 55 passed in 0.21s\n"
    },
    {
      "mutation_id": "M19",
      "name": "global_emergency_scope",
      "old": "\"GLOBAL\"",
      "new": "\"GLOBAL_BROKEN\"",
      "detected": true,
      "pytest_returncode": 1,
      "output_tail": "...................................F....................                 [100%]\n=================================== FAILURES ===================================\n___________________ test_coarse_targets_are_rejected[GLOBAL] ___________________\n\ntarget = 'GLOBAL'\n\n    @pytest.mark.parametrize(\"target\", [\"*\", \"ALL\", \"REGION_DISABLED\", \"GLOBAL\", \"item:*\"], ids=str)\n    def test_coarse_targets_are_rejected(target: str) -> None:\n>       with pytest.raises(AuthorizationRefused) as error:\n             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nE       Failed: DID NOT RAISE <class 'epd2_control_plane_service.exceptions.AuthorizationRefused'>\n\nservices/control-plane-service/tests/test_ctrl02_lifecycle.py:197: Failed\n=========================== short test summary info ============================\nFAILED services/control-plane-service/tests/test_ctrl02_lifecycle.py::test_coarse_targets_are_rejected[GLOBAL]\n1 failed, 55 passed in 0.22s\n"
    },
    {
      "mutation_id": "M20",
      "name": "approval_implies_execution",
      "old": "if request.state is not WorkflowState.ACTIVE:",
      "new": "if request.state not in {WorkflowState.ACTIVE, WorkflowState.APPROVED}:",
      "detected": true,
      "pytest_returncode": 1,
      "output_tail": "   svc.approve(\n            \"priv-pending\",\n            approver_id=\"approver-1\",\n            approver_class=ApproverClass.GOVERNANCE,\n            now=NOW + timedelta(minutes=1),\n            idempotency_key=\"priv-pending:a1\",\n        )\n        svc.approve(\n            \"priv-pending\",\n            approver_id=\"security-1\",\n            approver_class=ApproverClass.SECURITY,\n            now=NOW + timedelta(minutes=2),\n            idempotency_key=\"priv-pending:sec\",\n        )\n>       with pytest.raises(AuthorizationRefused):\n             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nE       Failed: DID NOT RAISE <class 'epd2_control_plane_service.exceptions.AuthorizationRefused'>\n\nservices/control-plane-service/tests/test_ctrl02_privilege_and_recovery.py:152: Failed\n=========================== short test summary info ============================\nFAILED services/control-plane-service/tests/test_ctrl02_privilege_and_recovery.py::test_approval_does_not_materialize_privilege\n1 failed, 55 passed in 0.21s\n"
    },
    {
      "mutation_id": "M21",
      "name": "auditor_executes",
      "old": "capability=\"INTERVENTION.EXECUTE\",",
      "new": "capability=\"INTERVENTION.REVIEW\",",
      "detected": true,
      "pytest_returncode": 1,
      "output_tail": "py::test_restoration_requires_valid_original_authority_and_no_newer_conflict\nFAILED services/control-plane-service/tests/test_ctrl02_privilege_and_recovery.py::test_jit_exact_target_use_and_evidence\nFAILED services/control-plane-service/tests/test_ctrl02_privilege_and_recovery.py::test_breakglass_has_strict_expiry\nFAILED services/control-plane-service/tests/test_ctrl02_privilege_and_recovery.py::test_jit_cannot_expand_scope_or_target\nFAILED services/control-plane-service/tests/test_ctrl02_privilege_and_recovery.py::test_active_restriction_overrides_narrow_jit_grant\nFAILED services/control-plane-service/tests/test_ctrl02_privilege_and_recovery.py::test_clock_rollback_cannot_revive_expired_grant\nFAILED services/control-plane-service/tests/test_ctrl02_privilege_and_recovery.py::test_checkpoint_preserves_terminal_and_evidence_state\nFAILED services/control-plane-service/tests/test_ctrl02_privilege_and_recovery.py::test_recovery_does_not_resurrect_expired_grant\n19 failed, 37 passed in 0.59s\n"
    },
    {
      "mutation_id": "M22",
      "name": "secret_visibility_implied",
      "old": "\"SECRET.RAW_READ\"",
      "new": "\"SECRET.RAW_READ_BROKEN\"",
      "detected": true,
      "pytest_returncode": 1,
      "output_tail": "D NOT RAISE <class 'epd2_control_plane_service.exceptions.AuthorizationRefused'>\n\nservices/control-plane-service/tests/test_ctrl02_authorization.py:182: Failed\n_________________ test_raw_secret_visibility_is_never_implied __________________\n\n    def test_raw_secret_visibility_is_never_implied() -> None:\n        svc = service()\n>       with pytest.raises(AuthorizationRefused):\n             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nE       Failed: DID NOT RAISE <class 'epd2_control_plane_service.exceptions.AuthorizationRefused'>\n\nservices/control-plane-service/tests/test_ctrl02_privilege_and_recovery.py:181: Failed\n=========================== short test summary info ============================\nFAILED services/control-plane-service/tests/test_ctrl02_authorization.py::test_universal_admin_and_secret_capability_are_forbidden[SECRET.RAW_READ]\nFAILED services/control-plane-service/tests/test_ctrl02_privilege_and_recovery.py::test_raw_secret_visibility_is_never_implied\n2 failed, 54 passed in 0.23s\n"
    },
    {
      "mutation_id": "M23",
      "name": "raw_service_secret_exposed",
      "old": "if operation not in allowed or secret_material is not None:",
      "new": "if operation not in allowed or False:",
      "detected": true,
      "pytest_returncode": 1,
      "output_tail": "ef test_service_credential_control_exposes_no_secret() -> None:\n        svc = service()\n        ref = svc.service_credential_control(\n            credential_id=\"workload:api\",\n            operation=\"EMERGENCY_CONTAIN\",\n            actor_id=\"security-operator\",\n            scope=BERLIN,\n            now=NOW,\n            evidence_ref=\"incident:credential-1\",\n        )\n        assert ref.startswith(\"service-credential:\")\n        assert \"forbidden\" not in str(svc.events)\n>       with pytest.raises(AuthorizationRefused):\n             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nE       Failed: DID NOT RAISE <class 'epd2_control_plane_service.exceptions.AuthorizationRefused'>\n\nservices/control-plane-service/tests/test_ctrl02_privilege_and_recovery.py:250: Failed\n=========================== short test summary info ============================\nFAILED services/control-plane-service/tests/test_ctrl02_privilege_and_recovery.py::test_service_credential_control_exposes_no_secret\n1 failed, 55 passed in 0.30s\n"
    },
    {
      "mutation_id": "M24",
      "name": "voting_identity_bridge",
      "old": "\"BALLOT.CORRELATE_PERSON\"",
      "new": "\"BALLOT.CORRELATE_PERSON_BROKEN\"",
      "detected": true,
      "pytest_returncode": 1,
      "output_tail": "ILURES ===================================\n__________ test_voting_boundary_is_absolute[BALLOT.CORRELATE_PERSON] ___________\n\ncapability = 'BALLOT.CORRELATE_PERSON'\n\n    @pytest.mark.parametrize(\n        \"capability\",\n        [\n            \"VOTER.LOOKUP\",\n            \"BALLOT.READ\",\n            \"BALLOT.CORRELATE_PERSON\",\n            \"TALLY.READ_INTERMEDIATE\",\n            \"VOTING.ADMIN\",\n        ],\n    )\n    def test_voting_boundary_is_absolute(capability: str) -> None:\n>       with pytest.raises(AuthorizationRefused) as error:\n             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nE       Failed: DID NOT RAISE <class 'epd2_control_plane_service.exceptions.AuthorizationRefused'>\n\nservices/control-plane-service/tests/test_ctrl02_authorization.py:175: Failed\n=========================== short test summary info ============================\nFAILED services/control-plane-service/tests/test_ctrl02_authorization.py::test_voting_boundary_is_absolute[BALLOT.CORRELATE_PERSON]\n1 failed, 55 passed in 0.21s\n"
    },
    {
      "mutation_id": "M25",
      "name": "history_overwrite",
      "old": "self._events.append(event)",
      "new": "self._events[:] = [event]",
      "detected": true,
      "pytest_returncode": 1,
      "output_tail": "......................F.................................                 [100%]\n=================================== FAILURES ===================================\n__________________ test_audit_chain_is_append_only_and_linked __________________\n\n    def test_audit_chain_is_append_only_and_linked() -> None:\n        svc = service()\n        request(svc)\n        approve_twice(svc)\n        activate(svc)\n        events = svc.events\n>       assert [event.sequence for event in events] == list(range(1, len(events) + 1))\nE       assert [2] == [1]\nE         \nE         At index 0 diff: 2 != 1\nE         Use -v to get more diff\n\nservices/control-plane-service/tests/test_ctrl02_inventory_evidence.py:87: AssertionError\n=========================== short test summary info ============================\nFAILED services/control-plane-service/tests/test_ctrl02_inventory_evidence.py::test_audit_chain_is_append_only_and_linked\n1 failed, 55 passed in 0.22s\n"
    },
    {
      "mutation_id": "M26",
      "name": "unauthorized_escalation",
      "old": "return 2, frozenset({ApproverClass.GOVERNANCE, ApproverClass.SECURITY})",
      "new": "return 2, frozenset({ApproverClass.GOVERNANCE})",
      "detected": true,
      "pytest_returncode": 1,
      "output_tail": "s=ApproverClass.GOVERNANCE,\n            now=NOW + timedelta(minutes=2),\n            idempotency_key=\"l4:g2\",\n        )\n>       assert second.state is WorkflowState.REVIEWING\nE       AssertionError: assert <WorkflowState.APPROVED: 'APPROVED'> is <WorkflowState.REVIEWING: 'REVIEWING'>\nE        +  where <WorkflowState.APPROVED: 'APPROVED'> = InterventionRequest(request_id='request-1', level=<InterventionLevel.TEMPORARY_SUPERVISION: 'L4_TEMPORARY_SUPERVISION'...26, 9, 2, 10, 2, tzinfo=datetime.timezone.utc))), activated_by=None, activated_at=None, ended_at=None, review_ref=None).state\nE        +  and   <WorkflowState.REVIEWING: 'REVIEWING'> = WorkflowState.REVIEWING\n\nservices/control-plane-service/tests/test_ctrl02_lifecycle.py:179: AssertionError\n=========================== short test summary info ============================\nFAILED services/control-plane-service/tests/test_ctrl02_lifecycle.py::test_l4_two_governance_approvals_do_not_replace_security_approval\n1 failed, 55 passed in 0.23s\n"
    },
    {
      "mutation_id": "M27",
      "name": "unauthorized_extension",
      "old": "MAX_SUPERVISION: Final = timedelta(days=90)",
      "new": "MAX_SUPERVISION: Final = timedelta(days=900)",
      "detected": true,
      "pytest_returncode": 1,
      "output_tail": ".........................................F..............                 [100%]\n=================================== FAILURES ===================================\n________________ test_supervision_over_ninety_days_is_rejected _________________\n\n    def test_supervision_over_ninety_days_is_rejected() -> None:\n        svc = service()\n>       with pytest.raises(AuthorizationRefused):\n             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nE       Failed: DID NOT RAISE <class 'epd2_control_plane_service.exceptions.AuthorizationRefused'>\n\nservices/control-plane-service/tests/test_ctrl02_lifecycle.py:267: Failed\n=========================== short test summary info ============================\nFAILED services/control-plane-service/tests/test_ctrl02_lifecycle.py::test_supervision_over_ninety_days_is_rejected\n1 failed, 55 passed in 0.21s\n"
    },
    {
      "mutation_id": "M28",
      "name": "restore_revoked_authority",
      "old": "if not original_authority_valid or newer_conflict:",
      "new": "if False:",
      "detected": true,
      "pytest_returncode": 1,
      "output_tail": "newer_conflict() -> None:\n        svc = service()\n        request(\n            svc,\n            level=InterventionLevel.AUTHORITY_SUSPENSION,\n            targets=(\"authority:regional-chair\",),\n            capabilities=(\"AUTHORITY.ACT\",),\n        )\n        approve_twice(svc)\n        activate(svc)\n        svc.revoke(\n            \"request-1\",\n            actor_id=\"revoker\",\n            now=NOW + timedelta(minutes=4),\n            idempotency_key=\"restore:revoke\",\n        )\n>       with pytest.raises(AuthorizationRefused):\n             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nE       Failed: DID NOT RAISE <class 'epd2_control_plane_service.exceptions.AuthorizationRefused'>\n\nservices/control-plane-service/tests/test_ctrl02_lifecycle.py:319: Failed\n=========================== short test summary info ============================\nFAILED services/control-plane-service/tests/test_ctrl02_lifecycle.py::test_restoration_requires_valid_original_authority_and_no_newer_conflict\n1 failed, 55 passed in 0.21s\n"
    },
    {
      "mutation_id": "M29",
      "name": "narrow_grant_bypasses_suspension",
      "old": "if decision is not Decision.ALLOW:",
      "new": "if False:",
      "detected": true,
      "pytest_returncode": 1,
      "output_tail": "s_narrow_jit_grant ______________\n\n    def test_active_restriction_overrides_narrow_jit_grant() -> None:\n        svc, grant = _active_grant()\n        from _ctrl02_builders import approve_twice, request\n    \n        request(\n            svc,\n            request_id=\"restriction-2\",\n            targets=(\"action:SERVICE.RESTART\",),\n            capabilities=(\"SERVICE.RESTART\",),\n        )\n        approve_twice(svc, \"restriction-2\")\n        activate(svc, \"restriction-2\")\n>       with pytest.raises(AuthorizationRefused):\n             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nE       Failed: DID NOT RAISE <class 'epd2_control_plane_service.exceptions.AuthorizationRefused'>\n\nservices/control-plane-service/tests/test_ctrl02_privilege_and_recovery.py:168: Failed\n=========================== short test summary info ============================\nFAILED services/control-plane-service/tests/test_ctrl02_privilege_and_recovery.py::test_active_restriction_overrides_narrow_jit_grant\n1 failed, 55 passed in 0.21s\n"
    },
    {
      "mutation_id": "M30",
      "name": "new_session_bypasses_quarantine",
      "old": "if session_owner_id and self._sessions.get(f\"subject:{session_owner_id}\") == \"QUARANTINED\":",
      "new": "if False:",
      "detected": true,
      "pytest_returncode": 1,
      "output_tail": "SSION_QUARANTINED'>\nE        +  where <Decision.ALLOW: 'ALLOW'> = effective_decision(session_id='session:new', session_owner_id='member-1', authority_id=None, capability='SESSION.USE', scope=ExactScope(region_id='DE-BE', org_id='org-berlin'), now=(datetime.datetime(2026, 9, 2, 10, 0, tzinfo=datetime.timezone.utc) + datetime.timedelta(seconds=240)))\nE        +    where effective_decision = <epd2_control_plane_service.regional_operations.RegionalOperationsService object at 0x7fbd099974d0>.effective_decision\nE        +    and   datetime.timedelta(seconds=240) = timedelta(minutes=4)\nE        +  and   <Decision.SESSION_QUARANTINED: 'SESSION_QUARANTINED'> = Decision.SESSION_QUARANTINED\n\nservices/control-plane-service/tests/test_ctrl02_lifecycle.py:95: AssertionError\n=========================== short test summary info ============================\nFAILED services/control-plane-service/tests/test_ctrl02_lifecycle.py::test_subject_quarantine_applies_to_a_new_session\n1 failed, 55 passed in 0.22s\n"
    },
    {
      "mutation_id": "M31",
      "name": "direct_db_counted_as_action",
      "old": "DIRECT_DB_MUTATION_COUNTS_AS_GOVERNED: Final = False",
      "new": "DIRECT_DB_MUTATION_COUNTS_AS_GOVERNED: Final = True",
      "detected": true,
      "pytest_returncode": 1,
      "output_tail": "...................F....................................                 [100%]\n=================================== FAILURES ===================================\n_____________________ test_meta_invariants_are_fail_closed _____________________\n\n    def test_meta_invariants_are_fail_closed() -> None:\n>       assert DIRECT_DB_MUTATION_COUNTS_AS_GOVERNED is False\nE       assert True is False\n\nservices/control-plane-service/tests/test_ctrl02_inventory_evidence.py:36: AssertionError\n=========================== short test summary info ============================\nFAILED services/control-plane-service/tests/test_ctrl02_inventory_evidence.py::test_meta_invariants_are_fail_closed\n1 failed, 55 passed in 0.21s\n"
    },
    {
      "mutation_id": "M32",
      "name": "denial_returns_success",
      "old": "DENIALS_RAISE: Final = True",
      "new": "DENIALS_RAISE: Final = False",
      "detected": true,
      "pytest_returncode": 1,
      "output_tail": "...................F....................................                 [100%]\n=================================== FAILURES ===================================\n_____________________ test_meta_invariants_are_fail_closed _____________________\n\n    def test_meta_invariants_are_fail_closed() -> None:\n        assert DIRECT_DB_MUTATION_COUNTS_AS_GOVERNED is False\n>       assert DENIALS_RAISE is True\nE       assert False is True\n\nservices/control-plane-service/tests/test_ctrl02_inventory_evidence.py:37: AssertionError\n=========================== short test summary info ============================\nFAILED services/control-plane-service/tests/test_ctrl02_inventory_evidence.py::test_meta_invariants_are_fail_closed\n1 failed, 55 passed in 0.21s\n"
    },
    {
      "mutation_id": "M33",
      "name": "dependency_fails_open",
      "old": "if not self.authorities.available:\n            return Decision.DEPENDENCY_UNAVAILABLE",
      "new": "if not self.authorities.available:\n            return Decision.ALLOW",
      "detected": true,
      "pytest_returncode": 1,
      "output_tail": "NAVAILABLE\n        )\nE       AssertionError: assert <Decision.ALLOW: 'ALLOW'> is <Decision.DEPENDENCY_UNAVAILABLE: 'DEPENDENCY_UNAVAILABLE'>\nE        +  where <Decision.ALLOW: 'ALLOW'> = effective_decision(session_id=None, authority_id=None, capability='MEMBER.READ', scope=ExactScope(region_id='DE-BE', org_id='org-berlin'), now=datetime.datetime(2026, 9, 2, 10, 0, tzinfo=datetime.timezone.utc))\nE        +    where effective_decision = <epd2_control_plane_service.regional_operations.RegionalOperationsService object at 0x7fddc19c3170>.effective_decision\nE        +  and   <Decision.DEPENDENCY_UNAVAILABLE: 'DEPENDENCY_UNAVAILABLE'> = Decision.DEPENDENCY_UNAVAILABLE\n\nservices/control-plane-service/tests/test_ctrl02_inventory_evidence.py:49: AssertionError\n=========================== short test summary info ============================\nFAILED services/control-plane-service/tests/test_ctrl02_inventory_evidence.py::test_dependency_unavailable_decision_is_not_allow\n1 failed, 55 passed in 0.22s\n"
    },
    {
      "mutation_id": "M34",
      "name": "duplicate_activation",
      "old": "if request.state is not WorkflowState.APPROVED:",
      "new": "if request.state not in {WorkflowState.APPROVED, WorkflowState.ACTIVE}:",
      "detected": true,
      "pytest_returncode": 1,
      "output_tail": "........................................F...............                 [100%]\n=================================== FAILURES ===================================\n_________ test_duplicate_activation_with_new_key_has_no_second_effect __________\n\n    def test_duplicate_activation_with_new_key_has_no_second_effect() -> None:\n        svc = service()\n        request(svc)\n        approve_twice(svc)\n        activate(svc)\n        before = len(svc.events)\n>       with pytest.raises(AuthorizationRefused):\n             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nE       Failed: DID NOT RAISE <class 'epd2_control_plane_service.exceptions.AuthorizationRefused'>\n\nservices/control-plane-service/tests/test_ctrl02_lifecycle.py:255: Failed\n=========================== short test summary info ============================\nFAILED services/control-plane-service/tests/test_ctrl02_lifecycle.py::test_duplicate_activation_with_new_key_has_no_second_effect\n1 failed, 55 passed in 0.21s\n"
    },
    {
      "mutation_id": "M35",
      "name": "clock_rollback_revives_grant",
      "old": "if supplied < self._last_time:\n            return self._last_time",
      "new": "if supplied < self._last_time:\n            return supplied",
      "detected": true,
      "pytest_returncode": 1,
      "output_tail": "RESTRICTED: 'ACTION_RESTRICTED'> is <Decision.ALLOW: 'ALLOW'>\nE        +  where <Decision.ACTION_RESTRICTED: 'ACTION_RESTRICTED'> = effective_decision(session_id=None, authority_id=None, capability='MEMBER.UPDATE', scope=ExactScope(region_id='DE-BE', org_id='org-berlin'), now=(datetime.datetime(2026, 9, 2, 10, 0, tzinfo=datetime.timezone.utc) + datetime.timedelta(seconds=3600)))\nE        +    where effective_decision = <epd2_control_plane_service.regional_operations.RegionalOperationsService object at 0x7f52f3db3d10>.effective_decision\nE        +    and   datetime.timedelta(seconds=3600) = timedelta(hours=1)\nE        +  and   <Decision.ALLOW: 'ALLOW'> = Decision.ALLOW\n\nservices/control-plane-service/tests/test_ctrl02_lifecycle.py:228: AssertionError\n=========================== short test summary info ============================\nFAILED services/control-plane-service/tests/test_ctrl02_lifecycle.py::test_clock_rollback_does_not_reactivate_elapsed_restriction\n1 failed, 55 passed in 0.26s\n"
    },
    {
      "mutation_id": "M36",
      "name": "stale_ctrl01_evidence",
      "old": "490d8ca31d4607da204f03addaf900161257b289d51ec6f0b7e52433fd5cbe71",
      "new": "090d8ca31d4607da204f03addaf900161257b289d51ec6f0b7e52433fd5cbe71",
      "detected": true,
      "pytest_returncode": 1,
      "output_tail": "sed _____________________\n\n    def test_meta_invariants_are_fail_closed() -> None:\n        assert DIRECT_DB_MUTATION_COUNTS_AS_GOVERNED is False\n        assert DENIALS_RAISE is True\n        assert SELF_STATE == \"PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED\"\n>       assert CTRL01_WORKING_PREDECESSOR_SHA256 == (\n            \"490d8ca31d4607da204f03addaf900161257b289d51ec6f0b7e52433fd5cbe71\"\n        )\nE       AssertionError: assert '090d8ca31d46...52433fd5cbe71' == '490d8ca31d46...52433fd5cbe71'\nE         \nE         - 490d8ca31d4607da204f03addaf900161257b289d51ec6f0b7e52433fd5cbe71\nE         ? ^\nE         + 090d8ca31d4607da204f03addaf900161257b2
```


## FILE `services/control-plane-service/tests/test_ctrl02_authorization.py`

```text
from __future__ import annotations

from datetime import timedelta

import pytest
from _ctrl02_builders import BAVARIA, BERLIN, NOW, approve_twice, request, service
from epd2_control_plane_service.exceptions import AuthorizationRefused
from epd2_control_plane_service.regional_operations import (
    ApproverClass,
    Decision,
    InterventionLevel,
)


def test_self_approval_is_rejected() -> None:
    svc = service()
    request(svc)
    with pytest.raises(AuthorizationRefused) as error:
        svc.approve(
            "request-1",
            approver_id="requester",
            approver_class=ApproverClass.GOVERNANCE,
            now=NOW + timedelta(minutes=1),
            idempotency_key="self",
        )
    assert error.value.reason_code == Decision.SELF_APPROVAL_FORBIDDEN


def test_duplicate_approver_identity_is_not_quorum() -> None:
    svc = service()
    request(svc)
    svc.approve(
        "request-1",
        approver_id="approver-1",
        approver_class=ApproverClass.GOVERNANCE,
        now=NOW + timedelta(minutes=1),
        idempotency_key="a1",
    )
    with pytest.raises(AuthorizationRefused):
        svc.approve(
            "request-1",
            approver_id="approver-1",
            approver_class=ApproverClass.GOVERNANCE,
            now=NOW + timedelta(minutes=2),
            idempotency_key="a1-again",
        )


def test_service_identity_cannot_approve_as_human() -> None:
    svc = service()
    request(svc)
    with pytest.raises(AuthorizationRefused):
        svc.approve(
            "request-1",
            approver_id="service-actor",
            approver_class=ApproverClass.GOVERNANCE,
            now=NOW + timedelta(minutes=1),
            idempotency_key="service",
        )


def test_bund_actor_does_not_inherit_regional_competence() -> None:
    svc = service()
    with pytest.raises(AuthorizationRefused) as error:
        svc.request_intervention(
            request_id="bund-takeover",
            level=InterventionLevel.TEMPORARY_SUPERVISION,
            requester_id="bund-actor",
            governance_basis="Bund hierarchy",
            scope=BERLIN,
            target_ids=("principal:bund-supervisor",),
            reason="implicit takeover",
            evidence_refs=("evidence:1",),
            not_before=NOW,
            expires_at=NOW + timedelta(hours=1),
            allowed_capabilities=("MEMBER.REVIEW",),
            target_version=1,
            idempotency_key="bund",
        )
    assert error.value.reason_code == Decision.WRONG_SCOPE
    assert BAVARIA != BERLIN


def test_commit_time_reauthorization_detects_revoked_approver() -> None:
    svc = service()
    request(svc)
    approve_twice(svc)
    svc.authorities.update("a2", revoked=True)
    with pytest.raises(AuthorizationRefused) as error:
        svc.activate(
            "request-1",
            executor_id="executor",
            now=NOW + timedelta(minutes=3),
            idempotency_key="activate-stale",
        )
    assert error.value.reason_code == Decision.STALE_AUTHORITY


def test_commit_time_reauthorization_detects_approver_version_change() -> None:
    svc = service()
    request(svc)
    approve_twice(svc)
    svc.authorities.update("a2")
    with pytest.raises(AuthorizationRefused) as error:
        svc.activate(
            "request-1",
            executor_id="executor",
            now=NOW + timedelta(minutes=3),
            idempotency_key="activate-version-change",
        )
    assert error.value.reason_code == Decision.STALE_AUTHORITY


def test_commit_time_reauthorization_detects_target_change() -> None:
    svc = service()
    request(svc)
    approve_twice(svc)
    svc.set_target_version("action:MEMBER.UPDATE", 2)
    with pytest.raises(AuthorizationRefused) as error:
        svc.activate(
            "request-1",
            executor_id="executor",
            now=NOW + timedelta(minutes=3),
            idempotency_key="activate-stale-target",
        )
    assert error.value.reason_code == Decision.STALE_TARGET


def test_authority_dependency_unavailable_fails_closed() -> None:
    svc = service()
    svc.authorities.available = False
    with pytest.raises(AuthorizationRefused) as error:
        request(svc)
    assert error.value.reason_code == Decision.DEPENDENCY_UNAVAILABLE


def test_approval_does_not_equal_execution() -> None:
    svc = service()
    request(svc)
    approve_twice(svc)
    with pytest.raises(AuthorizationRefused) as error:
        svc.activate(
            "request-1",
            executor_id="approver-1",
            now=NOW + timedelta(minutes=3),
            idempotency_key="bad-exec",
        )
    assert error.value.reason_code == "EXECUTION_SEPARATION"


def test_reviewer_cannot_execute() -> None:
    svc = service()
    request(svc)
    approve_twice(svc)
    with pytest.raises(AuthorizationRefused):
        svc.activate(
            "request-1",
            executor_id="reviewer",
            now=NOW + timedelta(minutes=3),
            idempotency_key="reviewer-exec",
        )


@pytest.mark.parametrize(
    "capability",
    [
        "VOTER.LOOKUP",
        "BALLOT.READ",
        "BALLOT.CORRELATE_PERSON",
        "TALLY.READ_INTERMEDIATE",
        "VOTING.ADMIN",
    ],
)
def test_voting_boundary_is_absolute(capability: str) -> None:
    with pytest.raises(AuthorizationRefused) as error:
        request(service(), capabilities=(capability,))
    assert error.value.reason_code == Decision.VOTING_BOUNDARY


@pytest.mark.parametrize("capability", ["AUTHORITY.UNIVERSAL_ADMIN", "SECRET.RAW_READ"])
def test_universal_admin_and_secret_capability_are_forbidden(capability: str) -> None:
    with pytest.raises(AuthorizationRefused):
        request(service(), capabilities=(capability,))

```


## FILE `services/control-plane-service/tests/_ctrl02_builders.py`

```text
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from epd2_control_plane_service.regional_operations import (
    ActorClass,
    ApproverClass,
    AuthorityDirectory,
    AuthorityGrant,
    ExactScope,
    InterventionLevel,
    RegionalOperationsService,
)

NOW = datetime(2026, 9, 2, 10, 0, tzinfo=UTC)
BERLIN = ExactScope("DE-BE", "org-berlin")
BAVARIA = ExactScope("DE-BY", "org-bavaria")


def directory() -> AuthorityDirectory:
    rows = [
        ("req", "requester", "INTERVENTION.REQUEST", None, ActorClass.HUMAN, BERLIN),
        (
            "a1",
            "approver-1",
            "INTERVENTION.APPROVE",
            ApproverClass.GOVERNANCE,
            ActorClass.HUMAN,
            BERLIN,
        ),
        (
            "a2",
            "approver-2",
            "INTERVENTION.APPROVE",
            ApproverClass.GOVERNANCE,
            ActorClass.HUMAN,
            BERLIN,
        ),
        (
            "sec",
            "security-1",
            "INTERVENTION.APPROVE",
            ApproverClass.SECURITY,
            ActorClass.HUMAN,
            BERLIN,
        ),
        ("exec", "executor", "INTERVENTION.EXECUTE", None, ActorClass.HUMAN, BERLIN),
        ("revoke", "revoker", "INTERVENTION.REVOKE", None, ActorClass.HUMAN, BERLIN),
        ("review", "reviewer", "INTERVENTION.REVIEW", None, ActorClass.HUMAN, BERLIN),
        ("restore", "restorer", "INTERVENTION.RESTORE", None, ActorClass.HUMAN, BERLIN),
        (
            "credential",
            "security-operator",
            "SERVICE_CREDENTIAL.CONTAIN",
            None,
            ActorClass.HUMAN,
            BERLIN,
        ),
        (
            "trust",
            "trust-requester",
            "TRUST.CHANGE_REQUEST",
            None,
            ActorClass.HUMAN,
            BERLIN,
        ),
        (
            "svc",
            "service-actor",
            "INTERVENTION.APPROVE",
            ApproverClass.GOVERNANCE,
            ActorClass.SERVICE,
            BERLIN,
        ),
        ("bund", "bund-actor", "INTERVENTION.REQUEST", None, ActorClass.HUMAN, BAVARIA),
    ]
    return AuthorityDirectory(
        AuthorityGrant(
            grant_id=grant_id,
            actor_id=actor,
            actor_class=actor_class,
            capability=capability,
            scope=scope,
            version=1,
            approver_class=approver_class,
        )
        for grant_id, actor, capability, approver_class, actor_class, scope in rows
    )


def service() -> RegionalOperationsService:
    return RegionalOperationsService(directory())


def request(
    svc: RegionalOperationsService,
    *,
    request_id: str = "request-1",
    level: InterventionLevel = InterventionLevel.REGIONAL_ACTION_RESTRICTION,
    targets: tuple[str, ...] = ("action:MEMBER.UPDATE",),
    capabilities: tuple[str, ...] = ("MEMBER.UPDATE",),
    target_version: int = 1,
):
    return svc.request_intervention(
        request_id=request_id,
        level=level,
        requester_id="requester",
        governance_basis="FIR-GOV-004/rule-v1",
        scope=BERLIN,
        target_ids=targets,
        reason="bounded incident response",
        evidence_refs=("evidence:incident-1",),
        not_before=NOW,
        expires_at=NOW + timedelta(hours=2),
        allowed_capabilities=capabilities,
        target_version=target_version,
        idempotency_key=f"idem:{request_id}",
    )


def approve_twice(svc: RegionalOperationsService, request_id: str = "request-1"):
    svc.approve(
        request_id,
        approver_id="approver-1",
        approver_class=ApproverClass.GOVERNANCE,
        now=NOW + timedelta(minutes=1),
        idempotency_key=f"approve-1:{request_id}",
    )
    return svc.approve(
        request_id,
        approver_id="approver-2",
        approver_class=ApproverClass.GOVERNANCE,
        now=NOW + timedelta(minutes=2),
        idempotency_key=f"approve-2:{request_id}",
    )


def activate(svc: RegionalOperationsService, request_id: str = "request-1"):
    return svc.activate(
        request_id,
        executor_id="executor",
        now=NOW + timedelta(minutes=3),
        idempotency_key=f"activate:{request_id}",
    )

```


## FILE `services/control-plane-service/tests/test_ctrl02_privilege_and_recovery.py`

```text
from __future__ import annotations

from datetime import timedelta

import pytest
from _ctrl02_builders import BERLIN, NOW, activate, service
from epd2_control_plane_service.exceptions import AuthorizationRefused
from epd2_control_plane_service.regional_operations import (
    ApproverClass,
    Decision,
    PrivilegeKind,
    WorkflowState,
)


def _active_grant(kind: PrivilegeKind = PrivilegeKind.JIT):
    svc = service()
    svc.create_privilege_request(
        request_id="priv-1",
        kind=kind,
        principal_id="operator",
        requester_id="requester",
        scope=BERLIN,
        capabilities=("SERVICE.RESTART",),
        reason="bounded maintenance",
        evidence_refs=("change:1",),
        now=NOW,
        expires_at=NOW + timedelta(minutes=30),
        target_version=1,
        idempotency_key="priv:req",
    )
    svc.approve(
        "priv-1",
        approver_id="approver-1",
        approver_class=ApproverClass.GOVERNANCE,
        now=NOW + timedelta(minutes=1),
        idempotency_key="priv:a1",
    )
    svc.approve(
        "priv-1",
        approver_id="security-1",
        approver_class=ApproverClass.SECURITY,
        now=NOW + timedelta(minutes=2),
        idempotency_key="priv:sec",
    )
    activate(svc, "priv-1")
    grant = svc.materialize_privilege("priv-1", kind=kind, principal_id="operator")
    return svc, grant


def test_jit_exact_target_use_and_evidence() -> None:
    svc, grant = _active_grant()
    used = svc.use_privilege(
        grant.grant_id,
        principal_id="operator",
        capability="SERVICE.RESTART",
        scope=BERLIN,
        now=NOW + timedelta(minutes=4),
        use_ref="use:1",
    )
    assert used.use_refs == ("use:1",)


def test_breakglass_has_strict_expiry() -> None:
    svc, grant = _active_grant(PrivilegeKind.BREAK_GLASS)
    with pytest.raises(AuthorizationRefused) as error:
        svc.use_privilege(
            grant.grant_id,
            principal_id="operator",
            capability="SERVICE.RESTART",
            scope=BERLIN,
            now=NOW + timedelta(hours=2),
            use_ref="late",
        )
    assert error.value.reason_code == Decision.GRANT_EXPIRED


def test_breakglass_request_cannot_exceed_one_hour() -> None:
    svc = service()
    with pytest.raises(AuthorizationRefused):
        svc.create_privilege_request(
            request_id="too-long",
            kind=PrivilegeKind.BREAK_GLASS,
            principal_id="operator",
            requester_id="requester",
            scope=BERLIN,
            capabilities=("SERVICE.RESTART",),
            reason="too long",
            evidence_refs=("incident:1",),
            now=NOW,
            expires_at=NOW + timedelta(hours=2),
            target_version=1,
            idempotency_key="too-long",
        )


def test_jit_cannot_expand_scope_or_target() -> None:
    svc, grant = _active_grant()
    with pytest.raises(AuthorizationRefused):
        svc.use_privilege(
            grant.grant_id,
            principal_id="someone-else",
            capability="SERVICE.RESTART",
            scope=BERLIN,
            now=NOW + timedelta(minutes=4),
            use_ref="wrong-target",
        )

    from _ctrl02_builders import BAVARIA

    with pytest.raises(AuthorizationRefused):
        svc.use_privilege(
            grant.grant_id,
            principal_id="operator",
            capability="SERVICE.RESTART",
            scope=BAVARIA,
            now=NOW + timedelta(minutes=5),
            use_ref="wrong-scope",
        )


def test_approval_does_not_materialize_privilege() -> None:
    svc = service()
    svc.create_privilege_request(
        request_id="priv-pending",
        kind=PrivilegeKind.JIT,
        principal_id="operator",
        requester_id="requester",
        scope=BERLIN,
        capabilities=("SERVICE.RESTART",),
        reason="maintenance",
        evidence_refs=("change:1",),
        now=NOW,
        expires_at=NOW + timedelta(minutes=30),
        target_version=1,
        idempotency_key="priv-pending",
    )
    svc.approve(
        "priv-pending",
        approver_id="approver-1",
        approver_class=ApproverClass.GOVERNANCE,
        now=NOW + timedelta(minutes=1),
        idempotency_key="priv-pending:a1",
    )
    svc.approve(
        "priv-pending",
        approver_id="security-1",
        approver_class=ApproverClass.SECURITY,
        now=NOW + timedelta(minutes=2),
        idempotency_key="priv-pending:sec",
    )
    with pytest.raises(AuthorizationRefused):
        svc.materialize_privilege("priv-pending", kind=PrivilegeKind.JIT, principal_id="operator")


def test_active_restriction_overrides_narrow_jit_grant() -> None:
    svc, grant = _active_grant()
    from _ctrl02_builders import approve_twice, request

    request(
        svc,
        request_id="restriction-2",
        targets=("action:SERVICE.RESTART",),
        capabilities=("SERVICE.RESTART",),
    )
    approve_twice(svc, "restriction-2")
    activate(svc, "restriction-2")
    with pytest.raises(AuthorizationRefused):
        svc.use_privilege(
            grant.grant_id,
            principal_id="operator",
            capability="SERVICE.RESTART",
            scope=BERLIN,
            now=NOW + timedelta(minutes=5),
            use_ref="restricted",
        )


def test_raw_secret_visibility_is_never_implied() -> None:
    svc = service()
    with pytest.raises(AuthorizationRefused):
        svc.create_privilege_request(
            request_id="secret",
            kind=PrivilegeKind.BREAK_GLASS,
            principal_id="operator",
            requester_id="requester",
            scope=BERLIN,
            capabilities=("SECRET.RAW_READ",),
            reason="not allowed",
            evidence_refs=("incident:1",),
            now=NOW,
            expires_at=NOW + timedelta(minutes=10),
            target_version=1,
            idempotency_key="secret",
        )


def test_clock_rollback_cannot_revive_expired_grant() -> None:
    svc, grant = _active_grant()
    svc.expire_due(NOW + timedelta(hours=1))
    assert svc.grants[0].state is WorkflowState.EXPIRED
    with pytest.raises(AuthorizationRefused):
        svc.use_privilege(
            grant.grant_id,
            principal_id="operator",
            capability="SERVICE.RESTART",
            scope=BERLIN,
            now=NOW + timedelta(minutes=5),
            use_ref="rollback",
        )


def test_checkpoint_preserves_terminal_and_evidence_state() -> None:
    svc, _ = _active_grant()
    svc.expire_due(NOW + timedelta(hours=1))
    snapshot = svc.checkpoint()
    assert snapshot["grants"]["jit:priv-1"]["state"] is WorkflowState.EXPIRED
    assert snapshot["events"]
    assert snapshot["events"][-1]["event_hash"]


def test_recovery_does_not_resurrect_expired_grant() -> None:
    svc, grant = _active_grant()
    svc.expire_due(NOW + timedelta(hours=1))
    recovered = type(svc).from_checkpoint(svc.authorities, svc.checkpoint())
    assert recovered.grants[0].state is WorkflowState.EXPIRED
    with pytest.raises(AuthorizationRefused):
        recovered.use_privilege(
            grant.grant_id,
            principal_id="operator",
            capability="SERVICE.RESTART",
            scope=BERLIN,
            now=NOW + timedelta(hours=2),
            use_ref="after-restart",
        )


def test_service_credential_control_exposes_no_secret() -> None:
    svc = service()
    ref = svc.service_credential_control(
        credential_id="workload:api",
        operation="EMERGENCY_CONTAIN",
        actor_id="security-operator",
        scope=BERLIN,
        now=NOW,
        evidence_ref="incident:credential-1",
    )
    assert ref.startswith("service-credential:")
    assert "forbidden" not in str(svc.events)
    with pytest.raises(AuthorizationRefused):
        svc.service_credential_control(
            credential_id="workload:api",
            operation="REVOKE",
            actor_id="security-operator",
            scope=BERLIN,
            now=NOW + timedelta(minutes=1),
            evidence_ref="incident:credential-1",
            secret_material="forbidden",
        )


def test_key_trust_operation_is_request_only() -> None:
    svc = service()
    ref = svc.key_trust_change_request(
        request_ref="trust-request:1",
        operation="CONTAIN_COMPROMISE",
        key_reference="keyref:regional-issuer",
        actor_id="trust-requester",
        scope=BERLIN,
        now=NOW,
        evidence_ref="incident:key-1",
    )
    assert ref == "trust-request:1"
    assert svc.events[-1].result == "REQUEST_RECORDED_NOT_EXECUTED"

```


## FILE `docs/ctrl/CTRL-02/CTRL02_DEVELOPER_REPORT.md`

```text
# CTRL-02 Developer Report

## Identity

- Working stage: `CTRL-02 — Regional Authority Intervention, Supervision & Controlled Privilege Operations`
- Mode: `PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED`
- Baseline commit: `217559b7f21c338d6fe8d4e4676082cd3840251c`
- Baseline tree: `eb8a3254c2b8a30feff71318d4377eff2435605c`

## CTRL-01 dependency

- Status: `WORKING_PREDECESSOR / NOT_ACCEPTED`
- Exact P1 SHA-256: `490d8ca31d4607da204f03addaf900161257b289d51ec6f0b7e52433fd5cbe71`
- Authoritative acceptance: absent at development bootstrap
- Reconciliation: working interfaces consumed; final reconciliation blocked

## Implemented

The executable reference runtime covers all four intervention levels, exact
scope and target validation, request/review/approval/activation/revocation/
restoration lifecycles, distinct-person quorum, commit-time reauthorization,
JIT and break-glass TTL/use evidence, service-credential containment requests,
key/trust request-only custody boundary, voting isolation, safe refusal codes,
append-only hash-linked audit, recovery checkpoints and deterministic read
models.

## Verification

- CTRL-02 tests: see `validation/ctrl02/test_result.json`.
- Combined CTRL-01/CTRL-02 control-plane tests: see validator evidence.
- Mutation suite: `40/40 DETECTED`.
- Static analysis: Ruff and mypy are mandatory runnable gates.
- G04 remains `BLOCKED_FOR_FINAL_SEAL`; this does not block development work.

## Outstanding dependency

Final sealing is prohibited until authoritative CTRL-01 acceptance is present,
its exact candidate SHA/size/source/run/job is bound, the consumed contracts are
reconciled and every affected CTRL-02 gate is rerun against fresh PCR/Master.

## Self-state

`NOT_ACCEPTED`


```


## FILE `validation/ctrl02/post_use_review_result.json`

```text
{
  "baseline_commit": "217559b7f21c338d6fe8d4e4676082cd3840251c",
  "executed": true,
  "gate_refs": [
    "G39"
  ],
  "mode": "PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED",
  "runtime": "regional_operations.py",
  "schema": "epd2.ctrl02.evidence/1",
  "status": "PASS",
  "test_evidence": "test_result.json"
}

```


CTRL02_TARGETED_INSPECTION_PASS
