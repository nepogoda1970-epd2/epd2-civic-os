# CLAUDE-PACK-10 — Canon amendment proposal (`0.7.0 → 0.8.0`)

**Status: proposal only.** This document contains the canon text PACK-10
would require, as text to be reviewed — not as an applied edit.
`docs/canonical/TZ-00-domain-event-canon.md`,
`docs/canonical/canon-version.json`,
`packages/python/epd2-core/src/epd2_core/version.py` and
`packages/typescript/epd2-types/src/version.ts` are **not modified by this
task**, and `CANON_VERSION` remains `0.7.0`. The determination that an
amendment is required is `docs/packs/PACK-10-CANON-AMENDMENT-ASSESSMENT.md`;
the authoritative source for every fact below is
`docs/packs/PACK-10-SPECIFICATION.md`, which nothing here contradicts.
Proposed canon text is in the canon's own Russian, with a one-line English
gloss under each subsection heading; where the specification fixes a hard
rule, the canon text states it as a rule.

## 1. Version decision

**Explicit decision: `CANON_VERSION` should later move `0.7.0 → 0.8.0`, in a
separate, dedicated canon round.** The change satisfies canon section 25's
`Minor` criteria exactly: additive only; no existing required field, event
name or meaning, entity owner, status enum value, architectural invariant,
anonymity rule or critical-object lifecycle is altered, renamed or removed.
**This task does not change `CANON_VERSION`** — moving it requires its own
governing ADR, per ADR-037's precedent.

## 2. Exact canon sections affected

| Canon section                          | Change              | Detail                                                                                |
| -------------------------------------- | ------------------- | ------------------------------------------------------------------------------------- |
| New section `19f` (between 19e and 20) | added               | Twenty subsections `19f.1`–`19f.20`; no existing section renumbered                   |
| Section `20.17`                        | added               | Finance event catalogue, sixty-nine names, six groups                                 |
| Section `22`                           | extended            | Twenty-one new rows, all `Finance Service`                                            |
| Section `23`                           | extended            | Fourteen new forbidden-link entries                                                   |
| Section `24`                           | extended            | Forty-four new `FINANCE_*` codes plus a collision statement                           |
| Section `25`                           | version banner      | `canon_version 0.7.0 → 0.8.0`, `Minor` category                                       |
| Sections `19e.15`, `19e.16`            | extended additively | Four `role_code` values on an open list; incompatibility baseline extended (`19f.15`) |
| All other sections                     | unchanged           | No field, status, owner, event name or invariant touched                              |

## 3. Proposed normative text — new section 19f

### 19f. Партийные финансы и финансовая отчётность (Party Finance & Financial Accountability Context)

Предлагается версией канона 0.8.0 (ADR-048 через ADR-053, `proposed`,
2026-07-27) и определяет каноническую модель управляемого домена партийных
финансов: учёт, доходы и расходы, взносы, спонсорство и финансово измеримое
внешнее влияние, возмещения, активы и обязательства, бюджеты и учётные
периоды, жизненный цикл `Rechenschaftsbericht`, независимую ревизию и
безопасные публичные финансовые представления. Раздел вставлен под номером
19f, между разделами 19e и 20, чтобы не переносить нумерацию существующих
разделов 20–30 — тот же приём, что при добавлении 19a–19e. Все новые
сущности закреплены за новым `finance-service` (владелец: Finance Service,
ADR-048), код которого настоящим разделом **не создаётся** (19f.20); модель
19e используется без изменений, и ни одно поле, статус или владелец разделов
7–19e не изменяется.

#### 19f.1. Обзор и перечень сущностей

_English: the twenty-one authoritative finance aggregates._

Авторитетные агрегаты, все — владелец `finance-service` (раздел 22):
`FinanceAccount`, `AccountingPeriod`, `JournalEntry`,
`FinancialTransaction`, `ImportBatch`, `ReconciliationRecord`,
`FinanceContribution`, `SponsorshipAgreement`, `ExternalFinancialBenefit`,
`ExpenseClaim`, `PaymentAuthorization`, `Budget`, `FinancialAsset`,
`FinancialObligation`, `ReportingObligation`,
`ReportingPerimeterDefinition`, `FinanceReport`, `ReportSnapshot`,
`AuditEngagement`, `FinancePolicy`, `FinancePartyHandle`. Объекты-значения
(`Money`, `PostingLine`, `InKindValuation`, `AggregationSnapshot`,
`PerimeterSnapshot`, `FinancePolicyBinding`, `ContributionPartyRef`,
`RetentionBinding`, `FinanceEvidenceReference`) и производные read-модели
строк раздела 22 не получают (19c.4, 19e.11).

#### 19f.2. Разделение понятий — взнос, счёт учёта, регистр учёта

_English: three terminology separations against canon 13.2, 7.2 and 19a._

Понятия ниже не взаимозаменяемы и не носят одного канонического имени;
молчаливая переинтерпретация запрещена:

- `FinanceContribution` (19f.7) — не `Contribution` раздела 13.2
  (высказывание в обсуждении, Discussion Service); префиксы —
  `finance_contribution.*`, `FINANCE_CONTRIBUTION_*`.
- `FinanceAccount` (19f.4) — узел плана счетов, не `Account` раздела 7.2; ни
  одна финансовая запись не ссылается на `Account`.
- Регистр учёта (`JournalEntry`, 19f.4) — не публичный реестр
  `PublicLedgerEntry` (19a.1) и не `AuditEvent` (18.1); `AuditEngagement`
  (19f.15) — финансовая ревизия, не аудит-журнал.

#### 19f.3. `Money` и детерминизм денежных величин

_English: integer minor units, no floating point, no implicit currency._

`Money` — объект-значение: целые минорные единицы, код валюты, явный
масштаб, зафиксированное правило округления. Представление денежной величины
числом с плавающей точкой **запрещено** на всех уровнях, включая схемы
контрактов. Валюта не подразумевается; межвалютная арифметика запрещена без
записанной конверсии с курсом и датой.

#### 19f.4. Авторитетный регистр и сбалансированная проводка

_English: the authoritative double-entry ledger and the balancing rule._

Авторитетная запись денежного эффекта — `JournalEntry` с набором
`PostingLine` (счёт, сторона дебет/кредит, `Money`): `draft` → `posted` →
(`reversed`). **Жёсткое правило:** сумма дебетовых минорных единиц равна
сумме кредитовых по каждой валюте — в конструкторе и повторно при проводке.
Проведённая запись неизменяема: исправление — только новая сторнирующая или
корректирующая запись со ссылкой на исходную и reason code (INV-05).
`FinanceAccount`: `draft` → `active` → (`restricted` ↔ `active`) → `closed`;
код и класс счёта не изменяются после первой проводки, а реклассификация
отклоняется, если снимает обязательство раскрытия.

#### 19f.5. Учётный период и контролируемое переоткрытие

_English: the posting lock and dual-control reopening._

`AccountingPeriod` владеет блокировкой, которую проверяет каждая проводка, и
всегда несёт именованную зону IANA: `open` → `closing` → `closed` →
(`reopened` → `closing` → `closed`). Проводка в закрытый период отклоняется
внутри самой команды проводки, а не только на приёме. Переоткрытие — команда
двойного контроля: собственное полномочие, ссылка на причину, создаваемая
один раз `PeriodReopeningRecord` со снимком закрытого состояния;
утверждающий ≠ запросивший.

#### 19f.6. Реестр транзакций и провенанс

_English: the transaction register, provenance and duplicate detection._

`FinancialTransaction` — авторитетная запись хозяйственного факта и его
провенанса: `recorded` → `classified` → `posted` → (`corrected`) →
(`reversed`); после `recorded` дата, провенанс и импорт неизменяемы.
`ImportBatch` обязателен для каждой импортированной транзакции (`registered`
→ `validated` → `applied` | `rejected`); повторное применение применённого
batch запрещено. **Жёсткое правило:** транзакция с денежным эффектом без
сбалансированной `JournalEntry` отклоняется при отчётности.

#### 19f.7. Жизненный цикл взноса и исключительные состояния

_English: the contribution lifecycle and its governed exceptional states._

`FinanceContribution` — корень с создаваемой один раз квитанцией и
только-добавляемой историей оценок, решений и возвратов: `received` →
`quarantined` → `assessed` → (`accepted` | `rejected` | `return_required` →
`returned` | `escalated`); прямой переход `received` → `accepted`
**запрещён**. Анонимный или непроверяемый взнос попадает в `quarantined`.
Принятие требует разрешённой оценки, привязанной к версии политики;
квитанция не редактируется; неденежный взнос требует `InKindValuation`;
конфликт `undeclared` — fail-closed.

#### 19f.8. Агрегация и запрет дробления

_English: threshold evaluation runs on the aggregate, never on one gift._

Оценка порога выполняется исключительно на агрегате за релевантный политикой
период и периметр; ключ агрегации — (`FinancePartyHandle`, период политики,
периметр, версия политики). **Жёсткое правило:** дробление одной суммы на
несколько транзакций не обходит агрегацию, а объявленные связанные стороны и
посредники расширяют набор ключей. Решающий агрегат замораживается как
`AggregationSnapshot`: новая политика не переписывает прошлое решение.

#### 19f.9. Спонсорство, внешняя финансовая выгода и граница с PACK-35

_English: sponsorship, measurable external benefit, the PACK-35 boundary._

`SponsorshipAgreement` — платёж или выгода с согласованным встречным
исполнением; дарение — без него, и различие **никогда** не выводится из
суммы или плательщика: `registered` → `under_review` → (`approved` |
`rejected`) → (`disclosure_classified`) → (`terminated`). Утверждение без
записанного встречного исполнения запрещено, если политика явно не
классифицировала его отсутствие; `ExternalFinancialBenefit` покрывает
измеримую выгоду без соглашения. **Граница:** запись принадлежит настоящему
разделу, когда её предмет — измеримая финансовая величина или оценённая
выгода партийной организации, и домену общего раскрытия лоббистских
контактов (PACK-35), когда её предмет — контакт, встреча, доступ или влияние
без финансовой величины.

#### 19f.10. Расходы и разделение авторизации и исполнения платежа

_English: expense claims and the mandatory authorize/execute split._

`ExpenseClaim`: `submitted` → `under_review` → (`approved` | `rejected`) →
`payment_authorized` → `settled` → (`corrected`). `PaymentAuthorization` —
создаваемая один раз запись, отдельная от требования потому, что авторизация
и исполнение обязаны быть разделимы: `authorized` → (`executed` |
`revoked_before_execution`). **Жёсткие правила:** авторизующий ≠ исполняющий
платёж; заявитель не может рассматривать, утверждать или исполнять
собственное требование; расчёт без авторизации запрещён (INV-08).

#### 19f.11. Активы и обязательства

_English: assets, and one obligation aggregate for every liability type._

`FinancialAsset` и `FinancialObligation` — раздельные агрегаты; отдельная
сущность `Liability` не создаётся, так как `obligation_type` покрывает
дебиторскую и кредиторскую задолженность, заём, кредит, поручительство,
условное и долгосрочное. Статусы: `recorded` → `valued` → (`revalued`)\* →
(`disposed` | `settled` | `written_off` | `expired`). Переоценка без метода
запрещена; списание требует полномочия и, выше порога, двойного контроля;
выбытие под удержанием запрещено.

#### 19f.12. Бюджеты и фактические данные

_English: a budget is an intention, never a source of truth for actuals._

`Budget` — корень только-добавляемой цепочки версий: `draft` →
`submitted_for_approval` → (`approved` | `rejected`) →
(`superseded_by_amendment`). **Жёсткое правило:** бюджет никогда не
перезаписывает регистр учёта и не становится альтернативным источником
истины о фактических транзакциях; фактическая величина на бюджетной строке
не хранится, а вычисляется как производная read-модель. Зарезервированные
суммы — факты бюджетного домена, не остатки.

#### 19f.13. Обязанность отчётности, периметр и снимок отчёта

_English: obligation, effective-dated perimeter, create-once snapshot._

`ReportingObligation`: `created` → `active` → (`fulfilled` | `waived` |
`superseded`); исполнение возможно только через запись подачи, вывод из
публикации запрещён. `ReportingPerimeterDefinition` —
эффективно-датированная версия периметра; вывод периметра неявно из текущей
иерархии запрещён, а `PerimeterSnapshot` замораживается в версию отчёта, так
что **последующая реорганизация никогда не изменяет периметр закрытого или
поданного периода** (19e.9, 19e.10). `ReportSnapshot` — создаваемый один раз
агрегат, `frozen` терминален: без снимка нет ни подготовки, ни подачи.

#### 19f.14. Жизненный цикл `Rechenschaftsbericht` — подача ≠ принятие ≠ публикация

_English: the report lifecycle; legal effect never comes from telemetry._

Статусы версии `FinanceReport`: `draft` → `internally_reviewed` →
`auditor_reviewed` → `approved` → `signed` → `submitted` →
(`externally_acknowledged`) → (`accepted_by_authority`) → (`published`) →
(`amended_or_restated`). **Жёсткие правила:** подача — не принятие; внешнее
подтверждение получения — не принятие; публикация — не утверждение, и
утверждение — не публикация. `accepted_by_authority` достижим исключительно
из явной авторитетной ссылки — управляемого решения о правовом действии
уведомления; ни одно поле телеметрии доставки, получения или прочтения не
может быть входом перехода. Более новая версия не перезаписывает поданную
или опубликованную; пересмотр — версия с обратной ссылкой.

#### 19f.15. Независимая финансовая ревизия и `AuditConclusion`

_English: the audit engagement and four new institutional role codes._

`AuditEngagement` — независимый жизненный цикл `opened` → `in_progress` →
`concluded` → (`superseded_by_new_engagement`), с только-добавляемыми
находками и одним создаваемым один раз заключением. Каноническое имя —
**`AuditConclusion`**, никогда «opinion»: ни один сохранённый объект не
должен читаться как заключение обязательного аудита. Полномочие —
`finance_auditor` (19e.15), действующее назначение `OrganizationalAuthority`
в проверяемом scope, несовместимое с `finance_administrator` там же (19e.16,
правило 3); независимость перепроверяется при открытии, при каждой находке и
при заключении, а ревизор не вправе писать в проверяемый им агрегат.

Настоящий раздел добавляет к открытому списку `role_code` (19e.15) четыре
роли — `finance_administrator`, `payment_authorizer`, `payment_executor`,
`report_signatory` — и расширяет матрицу несовместимости (19e.16) четырьмя
парами: авторизующий ≠ исполняющий платёж; заявитель ≠ рассматривающий,
утверждающий, авторизующий или исполняющий; запросивший переоткрытие ≠
утвердивший; подписант ≠ подготовивший. Каждая роль ограничена одной
`OrganizationalScope` и отзываема.

#### 19f.16. Целевая финансовая ссылка на сторону и минимизация идентичности

_English: the purpose-scoped party handle, and what finance never stores._

`FinancePartyHandle` — непрозрачный, минтуемый сервисом идентификатор,
действительный ровно в одном периметре отчётности и для ровно одной
объявленной цели; он не производится ни из имени, ни из учётной записи, ни
из членства, ни из credential, ни из участнического идентификатора, ни из
другого handle. Тождество одного юридического лица внутри периметра и цели
устанавливается управляемым, reason-coded, аудируемым актом сопоставления:
`minted` → `active` → (`merged_into` | `retired`). **Жёсткие правила:**
переиспользование между целями или периметрами запрещено; разрешение требует
отдельного полномочия, доступно только модулю реестра и создаёт событие
аудита доступа без значения.

Настоящий раздел **никогда** не хранит имя, адрес, дату рождения,
национальный или налоговый идентификатор, банковские реквизиты, документ
удостоверения, почту, телефон, значение credential, идентификатор членства
или участия и значение, связанное с голосованием. Правила 1–8 раздела 19e.18
сохраняются, и handle **является персональными данными**: псевдонимизация не
создаёт анонимности.

#### 19f.17. Финансовая политика — датирование и привязка версии

_English: every threshold is a versioned, effective-dated policy._

`FinancePolicy` — единственный носитель порогов, категорий, планов счетов,
классов раскрытия и правил утверждения; `policy_kind` — открытый перечень не
менее семнадцати видов, расширяемый на уровне репозитория, никогда правкой
канона (приём `organization_profile`, 19e.3). Политика всегда несёт
`OrganizationalScope` и ссылку на юрисдикцию и **никогда не является неявно
глобальной**: `draft` → `active` → `superseded`. Каждое защищённое решение
хранит `FinancePolicyBinding` на самом решении; неизвестная политика —
fail-closed. **Обратное датирование** `effective_from` в закрытый или
поданный период запрещено (исправление прошлого есть пересмотр, 19f.14);
критические виды требуют двойного утверждения (19d.7).

#### 19f.18. Публичные финансовые представления и контроль раскрытия

_English: derived views, provenance, suppression before emission._

Публичные финансовые представления производны, версионированы и **никогда не
авторитетны**; публикуема только версия отчёта в статусе `published`. Каждое
представление несёт свой источник: версию отчёта, ссылку на
`ReportSnapshot`, периметр, статус и момент генерации. Структурно
запрещённое поле никогда не переклассифицируется в публикуемый класс — то же
правило, что `DisclosurePolicy.field_rules` (19a.3). Статистический контроль
применяется **до** выпуска представления, и ни одно представление не
раскрывает `FinancePartyHandle`.

#### 19f.19. Канонические события и reason codes — перекрёстная ссылка

_English: cross-reference to sections 20.17 and 24._

Каталог событий зафиксирован разделом 20.17 (новый): шестьдесят девять имён,
владелец `finance-service`, минимальный и запрещённый payload, время
вступления в силу и записи, версия политики, привязка к аудиту; envelope
раздела 21 без изменений. Сорок четыре reason code зафиксированы разделом 24
(расширен), все с префиксом `FINANCE_`; тридцать два существующих кода
переиспользуются дословно и по смыслу не изменяются.

#### 19f.20. Структурное разделение с другими контурами и ворота реализации

_English: isolation from voting and every other context, plus the gate._

Ни одна сущность настоящего раздела не имеет read- или write-ребра к
`VoteEnvelope`, `Tally`, `Ballot`, `Delegation`, `DelegationSnapshot` или
`ParticipationCredential` — ни прямо, ни через scope-авторизацию (19e.22,
INV-01), и ни один финансовый идентификатор, handle или payload не образует
корреляционного мостика в голосование. Раздел 19e не изменяется:
межscope-чтение выполняется исключительно шестью режимами 19e.12, а
консолидация есть чтение режима потомка с явным полномочием. Governance
(19b), Transparency (19a), AI Processing (17, 19c), Participation &
Membership (19d) и Emergency/Crisis Override (19) не изменяются. Документные
ссылки — только placeholder-форма без байтов и хешей, никогда не
утверждающая подлинность или публикуемость.

**Ворота реализации.** Настоящий раздел определяет исключительно
каноническую модель. Ни код `finance-service`, ни база данных, ни миграция,
ни event bus, ни OpenAPI, ни JSON Schema, ни реестр reason codes, ни
frontend, ни production-интеграция не авторизуются одним лишь этим разделом
(раздел 26; ADR-048 через ADR-053).

## 4. Proposed normative text — new section 20.17

### 20.17. Партийные финансы

Добавлено версией канона 0.8.0 (ADR-048 через ADR-053, раздел 19f). События
создаются исключительно `finance-service`; имена взяты дословно из
спецификации PACK-10, раздел 14.

**Счета, периоды, регистр, провенанс (19f.4–19f.6):**

- `finance_account.created`
- `finance_account.status_changed` — активация, ограничение, закрытие
- `accounting_period.opened`
- `accounting_period.closed`
- `accounting_period.reopening_requested`
- `accounting_period.reopened` — с `PeriodReopeningRecord`
- `journal_entry.drafted`
- `journal_entry.posted` — результат проверки баланса включён
- `journal_entry.reversed` — reason code обязателен
- `financial_transaction.recorded`
- `financial_transaction.classification_changed`
- `reconciliation.recorded`
- `import_batch.registered`
- `import_batch.completed`
- `import_batch.rejected`

**Взносы, спонсорство, внешняя выгода (19f.7–19f.9):**

- `finance_contribution.received`
- `finance_contribution.quarantined`
- `finance_contribution.assessed` — отпечаток `AggregationSnapshot`
- `finance_contribution.accepted`
- `finance_contribution.rejected`
- `finance_contribution.return_required`
- `finance_contribution.returned`
- `finance_contribution.escalated`
- `finance_in_kind_valuation.recorded`
- `sponsorship.registered`
- `sponsorship.approved`
- `sponsorship.rejected`
- `sponsorship.disclosure_classified`
- `external_financial_benefit.recorded`

**Расходы, платежи, бюджеты, позиции (19f.10–19f.12):**

- `expense_claim.submitted`
- `expense_claim.reviewed`
- `expense_claim.approved`
- `expense_claim.rejected`
- `expense_claim.corrected`
- `payment.authorized`
- `payment.settled` — исполняющий ≠ авторизующий
- `budget.approved`
- `budget.amended`
- `financial_asset.recorded`
- `financial_asset.revalued`
- `financial_asset.written_off`
- `financial_obligation.recorded`
- `financial_obligation.revalued`
- `financial_obligation.settled`
- `financial_obligation.written_off`

**Отчётность и жизненный цикл отчёта (19f.13, 19f.14):**

- `reporting_obligation.created`
- `reporting_perimeter.defined`
- `finance_report.snapshot_frozen`
- `finance_report.prepared`
- `finance_report.validation_finding_recorded`
- `finance_report.consolidated`
- `finance_report.internally_reviewed`
- `finance_report.auditor_reviewed`
- `finance_report.correction_requested`
- `finance_report.approved`
- `finance_report.signed`
- `finance_report.submitted`
- `finance_report.external_acknowledgement_recorded` — не признак принятия
- `finance_report.acceptance_recorded` — только с авторитетной ссылкой
- `finance_report.published`
- `finance_report.restated`

**Ревизия и политика (19f.15, 19f.17):**

- `finance_audit.opened` — результат проверки независимости
- `finance_audit.finding_recorded`
- `finance_audit.concluded` — класс `AuditConclusion`
- `finance_policy.version_published`
- `finance_policy.superseded`

**Целевая ссылка на сторону (19f.16):**

- `finance_party_handle.minted` — без идентифицирующих атрибутов
- `finance_party_handle.merged`
- `finance_party_handle.resolved` — аудит доступа, без значения

Для всех шестидесяти девяти событий: **минимальный payload** — идентификатор
записи, её новый статус, `effective_time`, `recorded_at`, ссылка на версию
политики и, где применимо, ровно один reason code раздела 24; **запрещённый
payload** — имя, адрес, банковские реквизиты, документ удостоверения,
значение credential, содержимое доказательства, байты документа, любая
информация о голосовании; **привязка к аудиту** — запись `AuditEvent` (18.1)
через `epd2_audit_core`; **идемпотентность** — повторная публикация того же
события не создаёт второй записи аудита (CT-00-04); **транспорт события не
авторизуется** (19f.20).

## 5. Proposed section 22 additions — ownership matrix

Twenty-one new rows — every PACK-10 authoritative aggregate — all owned by
`Finance Service`:

| Сущность                     | Модуль-владелец |
| ---------------------------- | --------------- |
| FinanceAccount               | Finance Service |
| AccountingPeriod             | Finance Service |
| JournalEntry                 | Finance Service |
| FinancialTransaction         | Finance Service |
| ImportBatch                  | Finance Service |
| ReconciliationRecord         | Finance Service |
| FinanceContribution          | Finance Service |
| SponsorshipAgreement         | Finance Service |
| ExternalFinancialBenefit     | Finance Service |
| ExpenseClaim                 | Finance Service |
| PaymentAuthorization         | Finance Service |
| Budget                       | Finance Service |
| FinancialAsset               | Finance Service |
| FinancialObligation          | Finance Service |
| ReportingObligation          | Finance Service |
| ReportingPerimeterDefinition | Finance Service |
| FinanceReport                | Finance Service |
| ReportSnapshot               | Finance Service |
| AuditEngagement              | Finance Service |
| FinancePolicy                | Finance Service |
| FinancePartyHandle           | Finance Service |

Accompanying note, in the style section 22 uses for the `0.3.0`–`0.7.0`
additions: all twenty-one rows are physically realized by one new service,
`finance-service` (ADR-048, not yet created — this is a canon round,
19f.20), the same "one physical service, several canonically named modules"
principle already applied to `transparency-service`, `governance-service`
and `organization-service`. No existing row changes. Children and
create-once records inside an aggregate (`PeriodReopeningRecord`,
`FinanceReportVersion`, `ConsolidationRecord`, `SubmissionRecord`,
`ExternalAcknowledgement`, `PublicationRecord`, `ValidationFinding`,
`AuditFinding`, `AuditConclusion`, `BudgetVersion`) get no rows, and neither
do the value objects or the derived read models — the treatment
`RedactionManifest` (19c.4) and `OrganizationalScope` (19e.11) receive.

**One naming decision the amendment round must confirm.** Specification
section 8 names the aggregate `Contribution`, while its events and codes
already carry the `finance_`/`FINANCE_` prefix. Canon section 22 cannot hold
two rows named `Contribution`, so this proposal uses `FinanceContribution`
and records the divergence rather than renaming that class.

## 6. Proposed section 23 additions — forbidden links

Fourteen new entries, in the canon's own style, each carrying the
`(добавлено 0.8.0, 19f.x)` marker:

- Любая финансовая запись, событие раздела 20.17 или публичное представление
  → payload идентичности либо банковские реквизиты (добавлено 0.8.0, 19f.16)
- Любая сущность раздела 19f → `VoteEnvelope` / `Tally` / `Ballot` /
  `Delegation` / `DelegationSnapshot` / `ParticipationCredential` (добавлено
  0.8.0, 19f.20)
- `FinancePartyHandle` → переиспользование между целями или периметрами,
  публикация, разрешение вне модуля реестра (добавлено 0.8.0, 19f.16)
- Бюджетная строка → хранение фактической величины либо запись в регистр
  учёта (добавлено 0.8.0, 19f.12)
- Производное публичное представление → авторитетный статус либо публикация
  версии, отличной от `published` (добавлено 0.8.0, 19f.18)
- Ссылка на документ → утверждение подлинности, подписанности, допустимости
  или публикуемости (добавлено 0.8.0, 19f.20)
- Телеметрия доставки, получения или прочтения → правовое принятие либо
  переход версии отчёта (добавлено 0.8.0, 19f.14)
- Название `role_code` само по себе → финансовое полномочие (добавлено
  0.8.0, 19f.15)
- `FinancePolicy.effective_from` → обратное датирование в закрытый или
  поданный период (добавлено 0.8.0, 19f.17)
- Любая сущность раздела 19f → сущность встречи, контакта, календаря,
  доступа или влияния (добавлено 0.8.0, 19f.9)
- Проведённая `JournalEntry`, замороженный `ReportSnapshot`, поданная версия
  отчёта → правка на месте либо удаление (добавлено 0.8.0, 19f.4, 19f.13)
- Реклассификация записи → снятие обязательства раскрытия, проверки,
  агрегации или отчётности (добавлено 0.8.0, 19f.4)
- Консолидирующий scope → проводка, исправление, утверждение или закрытие в
  нижестоящем scope (добавлено 0.8.0, 19f.14)
- Ревизионное полномочие → запись в проверяемый агрегат либо авторитетная
  `ReconciliationRecord` (добавлено 0.8.0, 19f.15)

## 7. Proposed section 24 additions — reason codes

Forty-four new codes, all prefixed `FINANCE_`, verbatim from specification
section 15.2. Each carries the marker `(добавлено 0.8.0, 19f.19)`, stated
once rather than forty-four times; annotation style is section 24's own:

- `FINANCE_AUTHORITY_MISSING` — нет действующего полномочия в scope.
- `FINANCE_AUDITOR_INDEPENDENCE_VIOLATION` — ревизор не независим.
- `FINANCE_ACCOUNTING_PERIOD_CLOSED` — период закрыт.
- `FINANCE_ACCOUNTING_PERIOD_UNDETERMINED` — период не определён.
- `FINANCE_PERIOD_REOPENING_NOT_AUTHORIZED` — переоткрытие без права.
- `FINANCE_JOURNAL_ENTRY_UNBALANCED` — дебет и кредит не равны.
- `FINANCE_CURRENCY_UNSUPPORTED` — валюта или межвалютность.
- `FINANCE_MONETARY_AMOUNT_INVALID` — величина без масштаба.
- `FINANCE_IMMUTABLE_RECORD_MODIFICATION_ATTEMPTED` — правка неизменяемого.
- `FINANCE_DUPLICATE_TRANSACTION` — отпечаток уже существует.
- `FINANCE_DUPLICATE_IMPORT` — batch уже применён.
- `FINANCE_IMPORT_PROVENANCE_MISSING` — нет batch или провенанса.
- `FINANCE_TRANSFER_PAIR_UNRESOLVED` — нет парной стороны.
- `FINANCE_RECLASSIFICATION_BYPASS_DENIED` — обход обязательства.
- `FINANCE_CONTRIBUTION_SOURCE_UNDETERMINED` — источник не установлен.
- `FINANCE_CONTRIBUTION_VERIFICATION_INCOMPLETE` — нет декларации.
- `FINANCE_CONTRIBUTION_CLASSIFICATION_UNDETERMINED` — нет класса.
- `FINANCE_CONTRIBUTION_PROHIBITED` — взнос запрещён политикой.
- `FINANCE_CONTRIBUTION_AGGREGATION_UNRESOLVED` — агрегат не разрешён.
- `FINANCE_CONTRIBUTION_RETURN_REQUIRED` — обязанность возврата.
- `FINANCE_IN_KIND_VALUATION_MISSING` — нет основания оценки.
- `FINANCE_VALUATION_METHOD_MISSING` — нет ссылки на метод.
- `FINANCE_COUNTER_PERFORMANCE_MISSING` — нет встречного исполнения.
- `FINANCE_SPONSORSHIP_DISCLOSURE_INCOMPLETE` — нет классификации.
- `FINANCE_PAYMENT_AUTHORIZATION_MISSING` — расчёт без авторизации.
- `FINANCE_WRITE_OFF_NOT_AUTHORIZED` — списание без права.
- `FINANCE_BUDGET_ACTUAL_WRITE_FORBIDDEN` — запись факта в бюджет.
- `FINANCE_CROSS_SCOPE_CONSOLIDATION_DENIED` — нет права консолидации.
- `FINANCE_REPORTING_PERIMETER_UNDETERMINED` — нет периметра периода.
- `FINANCE_REPORT_SNAPSHOT_MISSING` — нет замороженного снимка.
- `FINANCE_REPORT_VALIDATION_INCOMPLETE` — валидации не завершены.
- `FINANCE_REPORT_APPROVAL_MISSING` — нет утверждения.
- `FINANCE_REPORT_SIGN_OFF_MISSING` — нет подписи.
- `FINANCE_REPORT_STATUS_UNKNOWN` — статус не определяется.
- `FINANCE_AUDIT_INCOMPLETE` — ревизия не завершена.
- `FINANCE_EXTERNAL_ACKNOWLEDGEMENT_NOT_AUTHORITATIVE` — получение ≠
  принятие.
- `FINANCE_STATISTICAL_DISCLOSURE_RISK` — риск малой ячейки.
- `FINANCE_EVIDENCE_REFERENCE_MISSING` — нет ссылки на документ.
- `FINANCE_EVIDENCE_ASSERTION_UNAVAILABLE` — утверждение вне домена.
- `FINANCE_PARTY_HANDLE_PURPOSE_MISMATCH` — цель или периметр не те.
- `FINANCE_PARTY_HANDLE_RESOLUTION_DENIED` — нет права разрешения.
- `FINANCE_RETENTION_BINDING_MISSING` — нет класса хранения.
- `FINANCE_POLICY_MISSING` — нет применимой политики.
- `FINANCE_POLICY_VERSION_UNKNOWN` — версия политики не найдена.

### 7.1 Collision check

Mirroring `docs/handover/PACK-08-CANON-AMENDMENT-REPORT.md` section 3:

**No naming conflict found.** A comparison of the forty-four proposed codes
against canon section 24's existing registry (the twenty-two original codes
plus the ten added by `0.7.0`, 19e.21) and against every existing
`contracts/reason-codes/pack-0N.yml` file found no collision; the prefix
guarantees it structurally, since no registered code begins with `FINANCE_`.

**No existing code is renamed, redefined or repurposed.** Twelve
canon-registered codes are **reused verbatim**, meaning intact, rather
than shadowed by a `FINANCE_` duplicate: `PERMISSION_DENIED`,
`EVENT_VERSION_UNSUPPORTED`, `INTEGRITY_CHECK_FAILED`,
`SERVICE_STATE_READ_ONLY`, `EMERGENCY_FREEZE_ACTIVE` (section 24 since
`0.1.0`), and `ORGANIZATION_SCOPE_MISMATCH`, `CROSS_SCOPE_ACCESS_DENIED`,
`AUTHORITY_ASSIGNMENT_INVALID`, `AUTHORITY_ROLE_INCOMPATIBLE`,
`AUTHORITY_SCOPE_INVALID`, `SUCCESSOR_TRANSFER_REQUIRES_DECISION`,
`HISTORICAL_SCOPE_NOT_EFFECTIVE` (added `0.7.0`, 19e.21). Twenty further
pack-level codes are reused verbatim at registry level; specification
section 15.1 lists all thirty-two. Four near-collisions were resolved
deliberately (section 15.3), which is what makes the prefix load-bearing:
`CONTRIBUTION_*` (pack-03) is a deliberation utterance; `LEDGER_ENTRY_*`
and `TRANSPARENCY_LEDGER_*` (pack-04) are the public transparency ledger;
`ACCOUNT_*` (pack-02) is a platform user account; `AUDIT_EXPORT_*` is
audit-log integrity. None changes meaning.

## 8. Rationale

The determination is in `docs/packs/PACK-10-CANON-AMENDMENT-ASSESSMENT.md`;
the rationale for the _shape_ of this amendment is narrower. Finance is a
context in canon 5's sense, and 19a–19e each established that a new context
gets its own lettered section cross-referencing the catalogue sections
rather than duplicating them. Insertion between 19e and 20 without
renumbering follows five precedents and one reason: renumbering 20–30 would
invalidate every existing cross-reference in the repository. The `role_code`
additions extend 19e.15's open list and 19e.16's baseline — already
refinable "stricter, never softer" — instead of creating a second authority
model, and 19f.18 reuses 19a.3's mechanism. Twenty-one ownership rows rather
than one "finance" row follow INV-02, as 19a–19e each did.

## 9. Compatibility impact

**Additive only.** No existing canonical entity, field, status enum value,
event name, event meaning, entity owner or reason code is altered, renamed,
removed or reassigned: `Contribution` (13.2), `Account` (7.2),
`PublicLedgerEntry` (19a.1), `AuditEvent` (18.1), `Organization` (8.1),
`RoleAssignment` (8.4), `OrganizationalAuthority` (19e.15) and `Membership`
(8.3) are untouched. No architectural invariant is weakened; 19f strengthens
INV-01, INV-02, INV-04, INV-05, INV-08 and INV-10. Existing services are
unaffected — none reads a 19f entity, no existing contract test changes
meaning — and canon section 21's envelope is reused unchanged, so section
20.17 affects no existing event consumer. This satisfies section 25's
`Minor` criteria.

**One open compatibility question (OD-20), not resolved here.**
`docs/canonical/canon-version.json` declares `"repository_compatibility":
">=0.1.0 <0.10.0"`; a PACK-10 implementation round at `REPOSITORY_VERSION =
0.10.0` falls outside it. Either the range is widened, or the canon
amendment round moves it as part of its own edit — an owner decision,
recorded here because the amendment round is the natural place to make it.

## 10. Migration impact

**No data migration in the canon round.** Canon defines the model; there is
no finance data, no `services/finance-service`, no database and no schema to
migrate. The four new institutional `role_code` values are **additive
configuration on an already extensible field**: 19e.15 declares the list
open, so no existing `OrganizationalAuthority` or `RoleAssignment` record
changes and none needs revalidation, while the extended 19e.16 baseline
constrains only future assignments involving the new roles. The
`RoleAssignment.scope_id` classification (19e.19) is untouched. **PACK-09
reference types are unchanged** — `FinanceEvidenceRef`, `LegalCaseRef`,
`DeadlineRef`, `NoticeRef`, `NoticeEffectRef`, `HoldRef`, `RecordClassRef`,
`JurisdictionRef` and `CasePartyRef` keep their shapes and owner, and 19f
consumes them as they are; the clarification of `FinanceEvidenceRef`'s
subject and the optional typed-alias step stay outside this amendment
(section 11.1, OD-15).

## 11. Reason-code and event-canon impact

Forty-four canon-level `FINANCE_*` codes are added to section 24 (section
7), with the collision check in 7.1; thirty-two existing codes are reused
verbatim and none is renamed. The executable registry
`contracts/reason-codes/pack-10.yml` — proposed at seventy-six entries with
`source` markers — is an **implementation-round deliverable**, per every
prior canon-only round's precedent. Sixty-nine event names are added as
section 20.17 (section 4), grouped in six families, verbatim from
specification section 14; no existing event name or meaning changes,
sections 20.1–20.16 are untouched, and canon section 21's envelope applies
unchanged, so no `event_version` bump is implied. Payload schemas, the event
bus and the transport are **not** authorized (19f.20) — canon fixes names,
owner and payload semantics only.

## 12. What this document does not do

- **It does not edit the canon.**
  `docs/canonical/TZ-00-domain-event-canon.md` is unmodified, at 4514 lines;
  this is the proposal, not the amendment.
- **It does not change any version.** `canon_version` stays `0.7.0` in
  `docs/canonical/canon-version.json`; `CANON_VERSION` stays `0.7.0` in
  `epd2_core.version` and `epd2_types.version`; `REPOSITORY_VERSION` stays
  `0.9.0`. Section 1's decision is a recommendation for a later round.
- **It writes no code, schema or contract**, accepts no ADR (ADR-048–ADR-053
  remain `proposed`, even accepted they authorize no canon edit — ADR-037
  requires a governing ADR for the round itself), authorizes no
  implementation, and claims no legal compliance, authority acceptance or
  readiness.

One presentational note: this proposal groups the event and reason-code
cross-references into `19f.19`, and the structural separation and
implementation gate into `19f.20`, to keep the section at twenty
subsections. Splitting them into `19f.19`–`19f.22` changes no content and is
equally acceptable.
