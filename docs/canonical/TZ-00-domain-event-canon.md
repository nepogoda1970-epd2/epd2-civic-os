# EPD² CIVIC OS
## ТЗ-00. Каноническая модель домена и событий

**Версия:** 0.4.0  
**Статус:** working canon  
**Владелец документа:** EPD Plattform e.V.  
**Назначение:** единая обязательная спецификация для всех разработчиков и модулей EPD²  
**Следующий документ:** CLAUDE-PACK-01 — Repository Skeleton

---

# 1. Назначение документа

Настоящий документ определяет:

- архитектурные границы EPD²;
- обязательные системные принципы;
- основные контуры платформы;
- владельцев данных;
- канонические сущности;
- статусы сущностей;
- допустимые переходы;
- системные события;
- запретные связи;
- правила аудита;
- правила изменения канона;
- минимальные критерии совместимости модулей.

Ни один разработчик или ИИ-исполнитель не вправе самостоятельно изменять описанные здесь сущности, статусы, события или архитектурные границы.

Изменения вносятся только через отдельное архитектурное решение — `Architecture Decision Record` (`ADR`).

---

# 2. Целевая функция EPD²

EPD² — цифровая гражданская и партийная платформа, позволяющая участникам:

- проходить регистрацию и подтверждение права участия;
- создавать инициативы;
- обсуждать предложения;
- вносить поправки;
- поддерживать инициативы;
- участвовать в голосованиях;
- делегировать участие в допустимых пределах;
- проверять проведение процедур;
- видеть публичную историю решений;
- контролировать применение модерации и ИИ.

EPD² не является только информационным сайтом или системой публикации партийных материалов.

Платформа должна поддерживать полный цикл:

**идентификация → допуск → участие → решение → проверяемое доказательство**

---

# 3. Юридический оператор

Оператором платформы является:

**EPD Plattform e.V.**

- форма: eingetragener Verein;
- регистрационный суд: Amtsgericht Charlottenburg;
- регистрационный номер: VR 42522 B;
- место нахождения: Berlin.

Юридический оператор не получает технического права бесследно изменять решения, бюллетени, журналы или публичную историю.

---

# 4. Архитектурные инварианты

Инвариант — правило, которое должно оставаться истинным при любой реализации системы.

## INV-01. Разделение личности и участия

Реальная личность участника не хранится рядом с:

- содержимым тайного голоса;
- записью делегированного голоса;
- анонимным политическим действием;
- закрытой оценкой;
- голосовательным бюллетенем.

Identity-контур подтверждает право участия и выдаёт ограниченный credential.

Participation-контур проверяет credential, но не должен получать полный `IdentityRecord`.

## INV-02. Один владелец каждой сущности

У каждой канонической сущности существует только один модуль-владелец.

Другие модули:

- не изменяют её напрямую;
- не обращаются напрямую к её таблице;
- получают данные через API или события;
- хранят только разрешённые производные данные.

## INV-03. Отсутствие прямого доступа к чужой базе

Модуль не может:

- читать таблицы другого модуля;
- изменять их;
- использовать общий ORM для всей платформы;
- выполнять межсервисные SQL-запросы.

Интеграция допускается только через:

- версионированный API;
- версионированное событие;
- утверждённый read model;
- специальный audit export.

## INV-04. Политически значимые действия оставляют след

Обязательному аудиту подлежат:

- создание инициативы;
- изменение опубликованной инициативы;
- публикация;
- снятие с публикации;
- открытие и закрытие голосования;
- изменение правил процедуры;
- выдача и отзыв допуска;
- назначение роли;
- модерация;
- апелляция;
- применение crisis override;
- подсчёт результата;
- повторный подсчёт;
- публикация результата;
- применение ИИ к официальному объекту.

## INV-05. Нельзя бесследно изменять историю

Политически значимый объект не перезаписывается без сохранения предыдущей версии.

Это относится к:

- инициативам;
- поправкам;
- правилам голосования;
- бюллетеням;
- результатам;
- модерационным решениям;
- AI-generated summaries;
- policy documents.

## INV-06. Правила голосования замораживаются

После перехода голосования в статус `open` запрещено менять:

- вопрос;
- варианты ответа;
- круг допущенных лиц;
- кворум;
- порог;
- метод подсчёта;
- режим тайны;
- правила делегирования;
- дату начала задним числом.

Для изменения создаётся новое голосование либо процедура отменяется с публичным reason code.

## INV-07. ИИ не принимает окончательное политическое решение

ИИ может:

- структурировать;
- классифицировать;
- искать сходство;
- формировать проект резюме;
- выделять аргументы;
- указывать возможные правовые вопросы;
- предлагать модератору обратить внимание на контент.

ИИ не может самостоятельно:

- отклонить инициативу;
- лишить пользователя права участия;
- определить итог голосования;
- вынести окончательное модерационное решение;
- принять апелляционное решение;
- изменить программу;
- выдать окончательное юридическое заключение.

## INV-08. Критические действия требуют разделения полномочий

Один человек или один сервис не должен единолично:

- менять правила доступа и подтверждать собственное изменение;
- запускать crisis override и удалять след его применения;
- определять параметры голосования и единолично публиковать итог;
- разрабатывать Vote Casting и быть единственным аудитором;
- изменять tally и подтверждать собственный tally.

## INV-09. Отказ должен быть объяснимым

Любое значимое отклонение действия возвращает:

- машинный код причины;
- человекочитаемое объяснение;
- ссылку на применённое правило;
- допустимый следующий шаг;
- возможность апелляции, если она предусмотрена.

## INV-10. Fail-closed

Если система не может надёжно подтвердить:

- право пользователя;
- действительность credential;
- целостность бюллетеня;
- совместимость версии события;
- полномочия вызывающего субъекта;
- непротиворечивость критического перехода,

операция не выполняется.

Неопределённость не трактуется как разрешение.

---

# 5. Контуры платформы

## 5.1. Identity Context

Ответственность:

- аккаунт;
- вход;
- подтверждение личности;
- подтверждение уникальности;
- eID;
- MFA;
- восстановление;
- согласия;
- статус identity verification.

Identity Context знает, кто является пользователем.

Он не хранит политические действия пользователя.

## 5.2. Eligibility Context

Ответственность:

- членство;
- регион;
- возрастные и временные условия;
- статус права участия;
- eligibility snapshot;
- reason codes допуска и недопуска.

Eligibility Context отвечает на вопрос:

**имеет ли подтверждённый участник право участвовать в конкретном процессе?**

## 5.3. Credential Context

Ответственность:

- выдача Participation Credential;
- scope;
- срок действия;
- одноразовость;
- отзыв;
- защита от повторного использования;
- минимизация связуемости.

Credential Context является техническим мостом между Identity и Participation.

## 5.4. Organization Context

Ответственность:

- организация;
- подразделения;
- Civic Spaces;
- рабочие группы;
- роли;
- членство;
- организационная структура.

## 5.5. Initiative Context

Ответственность:

- инициатива;
- версии;
- публикация;
- поддержка;
- поправки;
- источники;
- прохождение этапов Programmwerkstatt.

## 5.6. Deliberation Context

Ответственность:

- обсуждения;
- аргументы;
- комментарии;
- ответы;
- реакции;
- тематические ветки;
- структурированные позиции.

## 5.7. Moderation Context

Ответственность:

- жалобы;
- флаги;
- решения;
- временное скрытие;
- ограничения;
- апелляции;
- восстановление;
- публичная статистика.

## 5.8. Voting Context

Ответственность:

- параметры голосования;
- бюллетени;
- приём голосов;
- защита от повторного участия;
- receipts;
- закрытие процесса.

Voting Context не должен получать реальное имя участника.

## 5.9. Tally Context

Ответственность:

- проверка набора бюллетеней;
- подсчёт;
- повторяемость;
- обработка недействительных записей;
- формирование подписанного результата.

## 5.10. Delegation Context

Ответственность:

- создание делегирования;
- scope;
- срок;
- отзыв;
- цепочки;
- циклы;
- snapshot;
- расчёт итогового веса.

## 5.11. Transparency Context

Ответственность:

- публичный реестр инициатив;
- реестр решений;
- история версий;
- результаты;
- журналы модерации;
- журналы ИИ;
- финансовая прозрачность;
- lobbying log;
- audit exports.

## 5.12. Governance Context

Ответственность:

- системные роли;
- политика полномочий;
- версии правил;
- emergency procedures;
- crisis override;
- audit access;
- review procedures.

---

# 6. Канонические идентификаторы

Каждый объект получает глобальный идентификатор формата UUID.

## Обязательные поля всех канонических объектов

- `id`
- `schema_version`
- `created_at`
- `created_by_actor_id`
- `updated_at`
- `status`
- `version`
- `correlation_id`
- `source_system`
- `integrity_hash`, если объект политически значим

## Требования

- идентификатор не должен содержать смысловой информации;
- ID пользователя не должен совпадать с ID identity record;
- публичный actor ID не должен позволять восстановить identity ID;
- ID бюллетеня не должен генерироваться на основе account ID;
- correlation ID не используется как постоянный идентификатор пользователя.

---

# 7. Субъекты системы

## 7.1. Person

Физическое лицо вне технической системы.

Не является непосредственно программной сущностью Participation Context.

## 7.2. Account

Техническая учётная запись пользователя.

### Владелец

Account Service.

### Основные поля

- `account_id`
- `email_status`
- `mfa_status`
- `account_status`
- `created_at`
- `last_login_at`
- `locale`
- `terms_version`
- `consent_status`

### Статусы

- `pending`
- `active`
- `restricted`
- `suspended`
- `recovery_pending`
- `closed`

## 7.3. IdentityRecord

Результат подтверждения личности.

### Владелец

Identity Verification Service.

### Основные поля

- `identity_record_id`
- `account_id`
- `verification_provider`
- `verification_level`
- `verification_status`
- `verified_at`
- `expires_at`
- `country`
- `duplicate_check_status`
- `provider_reference`

### Запрет

`IdentityRecord` не содержит:

- список голосований;
- выбранные варианты;
- список инициатив;
- политические предпочтения;
- делегирования.

## 7.4. Actor

Субъект действия внутри конкретного доменного контура.

Actor может представлять:

- пользователя;
- системный сервис;
- модератора;
- аудитора;
- организационный орган;
- автоматический процесс.

### Поля

- `actor_id`
- `actor_type`
- `scope`
- `status`

Actor ID не обязан быть одинаковым в разных контурах.

---

# 8. Организационные сущности

## 8.1. Organization

### Владелец

Organization Service.

### Поля

- `organization_id`
- `name`
- `legal_operator`
- `organization_type`
- `status`
- `default_policy_version`

### Статусы

- `draft`
- `active`
- `restricted`
- `archived`

## 8.2. CivicSpace

Область участия.

Примеры:

- федеральная программа;
- Landesverband;
- местная группа;
- тематическая мастерская;
- закрытый пробник.

### Поля

- `space_id`
- `organization_id`
- `name`
- `space_type`
- `visibility`
- `participation_policy_id`
- `status`

### Статусы

- `draft`
- `active`
- `read_only`
- `suspended`
- `archived`

## 8.3. Membership

### Поля

- `membership_id`
- `account_reference`
- `organization_id`
- `membership_type`
- `membership_status`
- `effective_from`
- `effective_until`
- `region_code`

### Статусы

- `application_pending`
- `verification_pending`
- `active`
- `suspended`
- `terminated`
- `rejected`
- `expired`

## 8.4. RoleAssignment

### Поля

- `role_assignment_id`
- `actor_id`
- `role_code`
- `scope_id`
- `valid_from`
- `valid_until`
- `assigned_by`
- `approval_reference`

### Статусы

- `pending`
- `active`
- `suspended`
- `expired`
- `revoked`

---

# 9. Eligibility

## 9.1. EligibilityRule

Определяет условия участия.

### Поля

- `eligibility_rule_id`
- `rule_version`
- `scope_type`
- `scope_id`
- `required_membership_status`
- `required_verification_level`
- `region_constraint`
- `minimum_membership_age`
- `exclusion_conditions`
- `valid_from`
- `valid_until`

После открытия голосования используемая версия правила замораживается.

## 9.2. EligibilityDecision

Результат проверки конкретного права.

### Поля

- `eligibility_decision_id`
- `subject_reference`
- `process_id`
- `rule_version`
- `decision`
- `reason_codes`
- `evaluated_at`
- `expires_at`

### Значения decision

- `eligible`
- `not_eligible`
- `pending`
- `expired`
- `manual_review_required`

## 9.3. EligibilitySnapshot

Зафиксированный набор условий и допусков на момент процедуры.

### Требования

- неизменяем после открытия процедуры;
- имеет hash;
- содержит версию правил;
- не содержит содержимого будущих голосов;
- допускает независимую проверку количества допущенных лиц.

---

# 10. Participation Credential

## 10.1. ParticipationCredential

Ограниченное подтверждение права на действие.

### Поля

- `credential_id`
- `credential_type`
- `scope_type`
- `scope_id`
- `issued_at`
- `expires_at`
- `usage_limit`
- `usage_counter`
- `revocation_status`
- `issuer_signature`
- `credential_version`

### Типы

- `space_access`
- `initiative_support`
- `ballot_access`
- `delegation_access`
- `audit_access`

### Статусы

- `issued`
- `active`
- `used`
- `expired`
- `revoked`
- `invalid`

### Запрет

Credential не содержит ФИО, email или адрес пользователя.

---

# 11. Инициативы

## 11.1. Initiative

### Поля

- `initiative_id`
- `space_id`
- `current_version_id`
- `author_actor_id`
- `initiative_type`
- `workflow_id`
- `status`
- `support_count`
- `created_at`

### Статусы

- `draft`
- `submitted`
- `completeness_review`
- `revision_required`
- `published`
- `support_collection`
- `qualified`
- `deliberation`
- `legal_review`
- `ready_for_ballot`
- `voting`
- `adopted`
- `rejected`
- `withdrawn`
- `archived`

## 11.2. InitiativeVersion

### Поля

- `initiative_version_id`
- `initiative_id`
- `version_number`
- `title`
- `problem_statement`
- `proposed_solution`
- `affected_groups`
- `expected_effects`
- `risks`
- `estimated_resources`
- `legal_questions`
- `source_references`
- `created_by_actor_id`
- `content_hash`

Опубликованная версия не изменяется. Любая редакция создаёт новую версию.

## 11.3. SupportRecord

### Поля

- `support_record_id`
- `initiative_id`
- `support_actor_reference`
- `credential_reference`
- `created_at`
- `status`

### Статусы

- `active`
- `withdrawn`
- `invalidated`

Один участник не может иметь более одной активной поддержки одной инициативы.

## 11.4. Amendment

### Поля

- `amendment_id`
- `initiative_id`
- `target_version_id`
- `proposer_actor_id`
- `proposed_change`
- `justification`
- `status`
- `decision_reference`

### Статусы

- `draft`
- `submitted`
- `published`
- `under_discussion`
- `accepted`
- `rejected`
- `withdrawn`
- `superseded`

---

# 12. Источники и доказательства

## 12.1. SourceRecord

### Поля

- `source_id`
- `source_type`
- `title`
- `publisher`
- `publication_date`
- `url`
- `archive_reference`
- `verification_status`
- `added_by_actor_id`
- `accessed_at`
- `content_hash`
- `valid_until`

### Статусы проверки

- `unverified`
- `automatically_checked`
- `human_checked`
- `disputed`
- `unavailable`
- `outdated`

ИИ не может незаметно повысить статус источника до `human_checked`.

---

# 13. Обсуждение

## 13.1. Discussion

### Поля

- `discussion_id`
- `subject_type`
- `subject_id`
- `space_id`
- `status`
- `moderation_policy_id`

### Статусы

- `open`
- `limited`
- `read_only`
- `closed`
- `archived`

## 13.2. Contribution

### Типы

- `comment`
- `argument_for`
- `argument_against`
- `question`
- `answer`
- `proposal`
- `source_note`
- `moderator_notice`

### Поля

- `contribution_id`
- `discussion_id`
- `author_actor_id`
- `parent_contribution_id`
- `contribution_type`
- `content`
- `content_hash`
- `visibility_status`
- `created_at`
- `edited_version`

### Статусы видимости

- `visible`
- `temporarily_hidden`
- `restricted`
- `removed_from_public_view`
- `restored`

Физическое удаление политически значимого Contribution допускается только по отдельной retention policy, при сохранении audit proof.

---

# 14. Модерация и апелляции

## 14.1. ModerationCase

### Поля

- `moderation_case_id`
- `target_type`
- `target_id`
- `opened_by`
- `trigger_type`
- `policy_version`
- `status`
- `assigned_moderator`

### Статусы

- `open`
- `under_review`
- `action_proposed`
- `decided`
- `appealed`
- `closed`

## 14.2. ModerationDecision

### Поля

- `moderation_decision_id`
- `case_id`
- `decision_type`
- `reason_code`
- `policy_reference`
- `decided_by`
- `effective_from`
- `effective_until`
- `public_explanation`
- `audit_reference`

### Типы решений

- `no_action`
- `warning`
- `temporary_hide`
- `restore`
- `participation_limit`
- `account_restriction_request`
- `escalate`
- `remove_from_public_view`

## 14.3. Appeal

### Поля

- `appeal_id`
- `decision_id`
- `submitted_by`
- `grounds`
- `status`
- `reviewer_actor_id`
- `result`

### Статусы

- `submitted`
- `admissibility_review`
- `under_review`
- `upheld`
- `partially_upheld`
- `rejected`
- `withdrawn`

Апелляцию не должен окончательно рассматривать автор исходного решения.

---

# 15. Голосование

## 15.1. Ballot

### Поля

- `ballot_id`
- `space_id`
- `subject_type`
- `subject_id`
- `question`
- `ballot_method`
- `secrecy_mode`
- `eligibility_rule_version`
- `delegation_policy_version`
- `quorum_rule`
- `threshold_rule`
- `opens_at`
- `closes_at`
- `status`
- `configuration_hash`
- `challenge_window_hours`

### Статусы

- `draft`
- `configuration_review`
- `scheduled`
- `open`
- `paused`
- `closed`
- `tallying`
- `tallied`
- `published`
- `cancelled`
- `invalidated`

`challenge_window_hours` необязательно; при отсутствии значения
применяется репозиторный default (72 часа); значение может быть
переопределено индивидуально для конкретного Ballot.

## 15.2. BallotOption

### Поля

- `ballot_option_id`
- `ballot_id`
- `option_code`
- `label`
- `description`
- `display_order`
- `status`

После открытия Ballot варианты блокируются.

## 15.3. VoteEnvelope

Защищённая запись поданного бюллетеня.

### Поля

- `vote_envelope_id`
- `ballot_id`
- `credential_proof`
- `encrypted_or_encoded_choice`
- `submitted_at`
- `integrity_hash`
- `validation_status`
- `included_in_tally`

### Статусы

- `received`
- `validated`
- `rejected`
- `superseded`
- `included`
- `quarantined`

### Запрет

VoteEnvelope не содержит:

- account ID;
- ФИО;
- email;
- membership ID;
- identity provider reference.

## 15.4. VoteReceipt

### Поля

- `receipt_id`
- `ballot_id`
- `vote_envelope_reference`
- `receipt_hash`
- `issued_at`
- `verification_status`

Receipt должен позволять проверить включение бюллетеня без публичного раскрытия выбранного варианта.

## 15.5. Tally

### Поля

- `tally_id`
- `ballot_id`
- `input_set_hash`
- `algorithm_version`
- `started_at`
- `completed_at`
- `result_data`
- `invalid_vote_count`
- `tally_signature`
- `verification_status`

### Статусы

- `pending`
- `running`
- `completed`
- `verification_failed`
- `verified`
- `superseded`

## 15.6. ResultPublication

### Поля

- `result_publication_id`
- `ballot_id`
- `tally_id`
- `eligible_count`
- `credential_count`
- `accepted_vote_count`
- `rejected_vote_count`
- `quorum_result`
- `threshold_result`
- `published_at`
- `audit_package_reference`
- `challenge_deadline_at`

`challenge_deadline_at` вычисляется как `published_at` плюс применимый
`challenge_window_hours` связанного Ballot (либо default, если поле не
задано). Наступление `challenge_deadline_at` — необходимое, но не
достаточное условие окончательности результата: до появления
канонического либо отдельно утверждённого механизма регистрации и
рассмотрения технических возражений (technical challenge) ResultPublication
остаётся в состоянии ожидания окончательности на уровне прикладной
логики. Ни один модуль не вправе автоматически считать результат
окончательным исключительно по факту истечения `challenge_deadline_at`.

---

# 16. Делегирование

## 16.1. Delegation

### Поля

- `delegation_id`
- `delegator_actor_id`
- `delegate_actor_id`
- `scope_type`
- `scope_id`
- `valid_from`
- `valid_until`
- `revocation_status`
- `status`

### Статусы

- `draft`
- `active`
- `revoked`
- `expired`
- `suspended`
- `invalid`

### Запреты

- самоделегирование;
- две конкурирующие активные делегации одного scope;
- скрытое бессрочное делегирование;
- изменение snapshot после открытия голосования.

## 16.2. DelegationSnapshot

### Поля

- `delegation_snapshot_id`
- `ballot_id`
- `policy_version`
- `created_at`
- `input_hash`
- `resolved_weights`
- `cycle_records`
- `snapshot_hash`

---

# 17. ИИ-обработка

## 17.1. AIProcessingRecord

### Поля

- `ai_processing_record_id`
- `purpose_code`
- `target_type`
- `target_id`
- `input_version`
- `model_provider`
- `model_name`
- `model_version`
- `prompt_template_version`
- `output_reference`
- `created_at`
- `human_review_status`
- `correction_reference`

### Статусы human review

- `not_required`
- `pending`
- `approved`
- `approved_with_changes`
- `rejected`
- `superseded`

Для официального резюме инициативы обязательна человеческая проверка.

---

# 18. Аудит

## 18.1. AuditEvent

### Обязательные поля

- `audit_event_id`
- `event_type`
- `occurred_at`
- `recorded_at`
- `actor_id`
- `actor_type`
- `target_type`
- `target_id`
- `action`
- `reason_code`
- `policy_version`
- `before_hash`
- `after_hash`
- `correlation_id`
- `source_service`
- `previous_event_hash`
- `event_hash`

### Требования

- append-only;
- последовательная hash chain;
- невозможность изменения через обычный API;
- независимый экспорт;
- отдельные права чтения;
- отсутствие полного содержимого тайного голоса.

---

# 19. Crisis Override

## 19.1. EmergencyAction

### Поля

- `emergency_action_id`
- `emergency_type`
- `target_scope`
- `reason_code`
- `evidence_references`
- `initiated_by`
- `approved_by`
- `started_at`
- `expires_at`
- `status`
- `recovery_plan_reference`
- `public_report_status`

### Типы

- `platform_read_only`
- `credential_issuance_pause`
- `ballot_pause`
- `ballot_cancel`
- `force_logout`
- `credential_revocation`
- `service_isolation`
- `evidence_preservation`

### Статусы

- `proposed`
- `approved`
- `active`
- `extended`
- `resolved`
- `cancelled`
- `under_review`

Для критических действий необходимы два независимых подтверждения, кроме автоматической кратковременной технической блокировки.

---

# 19a. Прозрачность (Transparency Context)

Добавлено версией канона 0.3.0 (ADR-013, принят 2026-07-23) и реализует
сущности контекста 5.11 (Transparency Context). Раздел вставлен под
номером 19a, между разделами 19 (Crisis Override) и 20 (Канонический
каталог событий), чтобы не переносить нумерацию уже существующих
разделов 20–27, на которые ссылаются ранее принятые ADR и отчёты.
Governance Context (5.12), ИИ-обработка (раздел 17) и Emergency/Crisis
Override (раздел 19) не входят в настоящий раздел и не расширяются им —
ни одна из четырёх сущностей ниже не требует существования сущности
Governance-контекста, `AIProcessingRecord` или `EmergencyAction`
(подробности разделения — 19a.6).

## 19a.1. PublicLedgerEntry

Единая, обобщённая запись публикуемого факта ("публичный реестр
инициатив, реестр решений, история версий, результаты, журналы
модерации", 5.11) с дискриминатором `subject_type` — вместо нескольких
почти одинаковых сущностей.

### Поля

- `public_ledger_entry_id`
- `subject_type`
- `subject_id`
- `subject_event_id`
- `published_at`
- `published_by_role_id`
- `content_snapshot`
- `content_hash`
- `previous_entry_hash`
- `disclosure_policy_id`
- `redaction_notice`
- `supersedes_entry_id`
- `status`

### Значения subject_type

- `initiative`
- `initiative_version`
- `moderation_decision`
- `result_publication`
- `ai_processing_record`

Значение `ai_processing_record` используется исключительно для
публикации уже существующей `AIProcessingRecord` (см. 19a.6) — настоящий
раздел не создаёт и не требует `AIProcessingRecord`.

### Статусы

- `published`

`PublicLedgerEntry` не имеет иного статуса, кроме `published`; поле
`status` не изменяется после создания записи.

### Неизменяемость и исправления

Опубликованная запись неизменяема: поля `status`, `content_snapshot`,
`content_hash`, `previous_entry_hash` и любые иные поля записи не
переписываются после создания — ни при каких условиях. Исправление
оформляется исключительно как новая запись `PublicLedgerEntry` с
заполненным `supersedes_entry_id`, указывающим на исправляемую запись.
Факт «данная запись заменена» является производным (вычисляется на
момент чтения по наличию другой записи со ссылкой `supersedes_entry_id`)
и не хранится и не записывается обратно в исходную запись.

### Запрещённые связи

- `PublicLedgerEntry → Account` — запрещено.
- `PublicLedgerEntry → IdentityRecord` — запрещено.
- `PublicLedgerEntry → ParticipationCredential` — запрещено.
- `PublicLedgerEntry → VoteEnvelope` — запрещено.
- `PublicLedgerEntry → Delegation` / `DelegationSnapshot` — запрещено.
- `published_by_role_id` не публикуется в исходном виде — допустима
  только утверждённая генерализованная метка роли (`replacement_label`,
  19a.3).

### Владелец

Public Ledger Service (раздел 22).

## 19a.2. AuditExportPackage

Реализует «audit exports» (5.11) и механизм INV-03 «специальный audit
export» — пакетный, доказуемый по цепочке хешей экспорт записей
`AuditEvent` (18.1), редактированный для публичного потребления.

### Поля

- `audit_export_package_id`
- `scope_description`
- `requested_by_role_id`
- `included_target_types`
- `event_count`
- `chain_proof`
- `package_digest`
- `integrity_proof`
- `generated_at`
- `redaction_notice`
- `supersedes_package_id`
- `status`

### Значения included_target_types

- `initiative`
- `initiative_version`
- `ballot`
- `moderation_case`
- `moderation_decision`
- `result_publication`

Значения `vote_envelope` и `delegation` в этот перечень не входят ни при
каких условиях.

### chain_proof

`chain_proof` — упорядоченный список элементов доказательства, по
одному на каждое включённое `AuditEvent`. Каждый элемент содержит:
`event_hash` (собственный `event_hash` исходного `AuditEvent`);
`previous_event_hash` (`event_hash` предыдущего элемента в этом
экспортированном сегменте); публично-безопасные метаданные —
`event_type`, `occurred_at`, `target_type`, `target_id`, `action`,
`reason_code`, `correlation_id`, `source_service` (без `actor_id`,
`actor_type`, `before_hash`, `after_hash`, `recorded_at`,
`policy_version`); и `sequence_position` — порядковый номер элемента в
сегменте, непрерывный, без пропусков, количеством равным `event_count`.

### Семантика проверки

Внешний проверяющий может независимо подтвердить: (1) непрерывность
цепочки — `previous_event_hash` каждого следующего элемента равен
`event_hash` предыдущего; (2) порядок и полноту — значения
`sequence_position` непрерывны, их количество равно `event_count`;
(3) отсутствие изменений после экспорта — пересчитанный дайджест по
полученному упорядоченному `chain_proof` совпадает с `package_digest`.
Внешний проверяющий **не может** по одному этому пакету пересчитать
исходные приватные значения `AuditEvent.event_hash` "с нуля", поскольку
`event_hash` (18.1) вычисляется по полному каноническому набору полей
`AuditEvent`, включающему поля, намеренно не раскрываемые данным пакетом
(`actor_id`, `actor_type`, `before_hash`, `after_hash`). Пакет
доказывает целостность и неизменность опубликованного сегмента — не
пересчёт приватного хеша; полный аудит исходной приватной цепочки
остаётся доступен только через отдельные права чтения `epd2_audit_core`
(18.1), а не через данный пакет.

### Статусы

- `generated`
- `published`
- `superseded`

Переходы: `generated → published`; `published → superseded` (только
через новый пакет с `supersedes_package_id`). Возврат к `generated`
невозможен; исходный пакет не редактируется.

### Запрещённые связи

- `AuditExportPackage → AuditEvent.actor_id` / `actor_type` /
  `before_hash` / `after_hash` — запрещено для любого включённого
  события.
- `requested_by_role_id` не публикуется в исходном виде.
- `AuditExportPackage → непубличные персональные данные` — запрещено.

### Владелец

Audit Export Service (раздел 22).

## 19a.3. DisclosurePolicy

Управляет тем, что именно и на каком основании раскрывается публично
для всех сущностей настоящего раздела.

### Поля

- `disclosure_policy_id`
- `applies_to_subject_type`
- `field_rules`
- `small_cell_threshold`
- `effective_from`
- `approved_by_role_id`
- `version`
- `status`

### field_rules

`field_rules` — список структурированных правил; каждое правило
содержит: `field_path` (путь к полю в схеме публикуемого содержимого);
`disclosure_class` — одно из `public`, `redacted`, `restricted`,
`prohibited`; `transformation` (способ преобразования значения, например
`none`, `generalize_to_role_scope`, `band_small_cell`, `suppress`,
`hash`); и необязательный `replacement_label` (замещающая публичная
метка, используется при `transformation = generalize_to_role_scope` и
аналогичных).

Каждое потенциально публикуемое поле должно иметь ровно одно применимое
правило; отсутствие правила или неоднозначность (более одного
применимого правила) переводит поле в класс `prohibited` (fail-closed,
INV-10). Правило не может перевести структурно запрещённое поле (19a.6)
в какой-либо иной класс, кроме `prohibited`.

### small_cell_threshold

Значение по умолчанию — `10`: агрегированные значения от 1 до 9 в
открытых аналитических представлениях, не являющихся формально
обязательными, отображаются как `"1–9"`; значение `0` отображается
точно. Для формально обязательного официального `ResultPublication`
(через `PublicLedgerEntry`, `subject_type = result_publication`)
подавление/группировка малых значений не применяется — точные значения
раскрываются всегда, независимо от размера выборки; данное исключение
фиксируется отдельным правилом `field_rules` с `transformation = none`
для этого `subject_type` — не подразумевается неявно.

### Статусы

- `draft`
- `active`
- `superseded`

`draft → active` требует заполненного `approved_by_role_id` (разделение
полномочий, INV-08); `active → superseded` — только при активации новой
версии для того же `applies_to_subject_type` (не более одной активной
версии одновременно); возврат к `draft` невозможен. Изменение уже
действующих правил производится только новой версией — не
редактированием существующей.

### Владелец

Disclosure Policy Service (раздел 22).

## 19a.4. LobbyLogEntry

Реализует «lobbying log» (5.11). Минимальная схема; полноценная
регистрация внешних лоббирующих субъектов остаётся будущим расширением
Organization Context (5.4).

### Поля

- `lobby_log_entry_id`
- `submitted_by_role_id`
- `organization_name`
- `related_subject_type`
- `related_subject_id`
- `contact_date`
- `contact_method`
- `topic_summary`
- `submitted_at`
- `published_at`
- `supersedes_entry_id`
- `status`

### Значения related_subject_type

- `initiative`
- `ballot`
- `amendment`

### Значения contact_method

- `meeting`
- `written_submission`
- `call`
- `other`

### Обязательные поля

`organization_name`, `related_subject_type` и `related_subject_id`,
`contact_date`, `topic_summary`, `submitted_by_role_id` обязательны;
запись с отсутствующим обязательным полем отклоняется при подаче и не
публикуется в неполном виде.

### Публикация

Запись публикуется не позднее 7 календарных дней после `submitted_at`.
Обязательного предварительного рассмотрения человеком по умолчанию нет;
обязательна автоматическая проверка перед публикацией: полнота
обязательных полей, отсутствие структурно запрещённых полей (19a.6),
соответствие действующей `DisclosurePolicy`.

### Статусы

- `submitted`
- `published`

`submitted → published` — однократный переход. После перехода в
`published` запись не изменяется ни при каких условиях. Исправление —
исключительно новая запись `LobbyLogEntry` с заполненным
`supersedes_entry_id`; факт замены исходной записи является производным
(вычисляется на момент чтения), исходная запись не переписывается.

### Запрещённые связи

- `LobbyLogEntry → IdentityRecord` / `Account` подающего лица —
  запрещено.
- `submitted_by_role_id` не публикуется в исходном виде.

### Владелец

Lobby Log Service (раздел 22).

## 19a.5. Связь PublicLedgerEntry с Initiative, InitiativeVersion, ModerationDecision, ResultPublication и AuditEvent

- **Initiative** (11.1): запись с `subject_type = initiative` создаётся
  при достижении `Initiative.status = published`, по событию
  `initiative.published` (20.6). `content_snapshot` — редактированная
  копия публичных полей на момент публикации, не живая ссылка на
  текущее состояние источника.
- **InitiativeVersion** (11.2): запись с `subject_type =
initiative_version` создаётся на каждую новую опубликованную версию,
  по событию `initiative.version_created` (20.7) — реализует «историю
  версий» (5.11).
- **ModerationDecision** (14.2): запись с `subject_type =
moderation_decision` создаётся при вынесении или исполнении решения
  (`moderation.decision_issued` / `moderation.decision_enforced`, 20.9).
  `content_snapshot` никогда не содержит `actor_id`, UUID
  `RoleAssignment` либо иной учётной/личной ссылки на рецензента —
  раскрывается только генерализованная метка роли (например,
  `"moderator"`); полная информация о рецензенте доступна только по
  restricted-доступу авторизованным ролям аудита и надзора, но не через
  публичное содержимое `PublicLedgerEntry`.
- **ResultPublication** (15.6): запись с `subject_type =
result_publication` создаётся по событию `result.published` (20.10).
  `content_snapshot` ограничен точно агрегатными полями
  `ResultPublication` (`eligible_count`, `credential_count`,
  `accepted_vote_count`, `rejected_vote_count`, `quorum_result`,
  `threshold_result`, `challenge_deadline_at`) — никогда содержимым
  `VoteEnvelope` или внутренним представлением `Tally.result_data`, если
  оно отличается. Этот `subject_type` исключён из подавления малых
  значений (19a.3, small_cell_threshold) — официальный результат
  публикуется точно всегда, независимо от размера выборки.
- **AuditEvent** (18.1): публикация или исправление `PublicLedgerEntry`
  сама по себе относится к обязательным для аудита действиям INV-04
  («публикация», «снятие с публикации») и создаёт обычную (непубличную)
  `AuditEvent` в `epd2_audit_core` — как и любое другое значимое
  действие. `AuditExportPackage` (19a.2) — отдельный, более крупный
  механизм: он упаковывает диапазон уже существующих `AuditEvent` в
  публично проверяемое доказательство целостности и неизменности
  экспортированного сегмента, а не доказательство содержимого.
  `PublicLedgerEntry` публикует содержимое; `AuditExportPackage`
  публикует доказательство того, что процесс публикации был соблюдён
  корректно. Одно не заменяет другое.

## 19a.6. Структурный запрет и разделение с другими контурами

Ни одна из четырёх сущностей настоящего раздела не может содержать поле
`account_id`, `person_id`, `identity_record_id`,
`participation_credential_id`, `vote_envelope_id`,
`encrypted_or_encoded_choice` или `credential_proof`. Поля
`published_by_role_id`, `requested_by_role_id`, `approved_by_role_id`,
`submitted_by_role_id` — внутренние служебные ссылки (`RoleAssignment`,
8.4) и ни при каких условиях не публикуются в исходном виде; в открытом
представлении допустима только утверждённая генерализованная метка роли
(`replacement_label`, 19a.3). `AuditExportPackage` дополнительно никогда
не раскрывает `AuditEvent.actor_id`, `actor_type`, `before_hash` или
`after_hash` для любого включённого события (19a.2).

`PublicLedgerEntry.subject_type = ai_processing_record` (19a.1)
используется исключительно для публикации уже существующей
`AIProcessingRecord` (17.1, владелец — AI Accountability Service);
настоящий раздел не создаёт, не изменяет и не требует существования
`AIProcessingRecord`, и не реализует ИИ-обработку. Governance Context
(5.12) — системные роли, политика полномочий, версии правил, emergency
procedures, crisis override, audit access, review procedures — не
входит в настоящий раздел; единственная точка, где требуется решение,
похожее на governance (кто уполномочен утвердить `DisclosurePolicy` или
опубликовать `LobbyLogEntry`), разрешена через уже существующую,
узкоспециализированную роль `RoleAssignment` (8.4), а не через
определение или реализацию новой сущности Governance-контекста.
Emergency/Crisis Override (раздел 19) также не входит в настоящий
раздел: ни одна из четырёх сущностей не требует существования
`EmergencyAction`.

---

# 19b. Governance (Governance Context)

Добавлено версией канона 0.4.0 (ADR-018, ADR-020, приняты 2026-07-23) и
реализует сущности контекста 5.12 (Governance Context). Раздел вставлен
под номером 19b, между разделами 19a (Transparency Context) и 20
(Канонический каталог событий), чтобы не переносить нумерацию уже
существующих разделов 20–30, на которые ссылаются ранее принятые ADR и
отчёты — тот же приём, использованный при добавлении раздела 19a
(ADR-013, версия 0.3.0).

`RoleAssignment` (8.4) уже полностью определена канонически; настоящий
раздел не изменяет её поля, идентификатор, статусы или владельца, а
только интегрирует её как центральную сущность полномочий, на которой
строятся три новые сущности ниже. `GovernancePolicy`, `GovernanceDecision`
и `TechnicalChallenge` физически реализуются вместе с `RoleAssignment`
одним сервисом, `governance-service` (ADR-016). Transparency Context
(19a), ИИ-обработка (раздел 17) и Emergency/Crisis Override (раздел 19)
не входят в настоящий раздел и не расширяются им — подробности
разделения приведены в 19b.7.

## 19b.1. RoleAssignment — интеграция и уточнение AdministratorRole

`RoleAssignment` (8.4) не получает новых полей настоящим разделом; поля
(`role_assignment_id`, `actor_id`, `role_code`, `scope_id`, `valid_from`,
`valid_until`, `assigned_by`, `approval_reference`), статусы (`pending`,
`active`, `suspended`, `expired`, `revoked`) и владелец ("Permission /
Role Service", раздел 22) остаются без изменений. Каждая ссылка вида
`proposed_by_role_id`, `approved_by_role_id`, `rejected_by_role_id` во
всех трёх новых сущностях ниже — ссылка на
`RoleAssignment.role_assignment_id`.

Закрытый перечень допустимых значений `RoleAssignment.role_code` для
пилотной версии Governance Context (ADR-020, §5):
`governance_policy_proposer`, `governance_policy_approver`,
`governance_reviewer`, `technical_challenge_reviewer`,
`ballot_invalidation_proposer`, `ballot_invalidation_approver`,
`oversight_reviewer`, `observer`. Этот перечень — содержимое первой
версии `GovernancePolicy` (`policy_type = "role_taxonomy"`, 19b.2), а не
самостоятельное канонически зафиксированное значение — `role_code`
остаётся открытой строкой на уровне канона (8.4), как и прежде.

**Уточнение `AdministratorRole` (раздел 23):** `AdministratorRole`, ранее
упоминавшаяся только в разделе 23 без собственного определения, **не
является отдельной канонической сущностью**. Она обозначает концепцию
`RoleAssignment.role_code` (предлагаемое буквальное значение, если оно
будет введено репозиторной таксономией: `"administrator"`) — обычную
`RoleAssignment`, ограниченную по scope как любая другая, а не
структурно отдельную сущность со своими полями или строкой владения.
Соответствующая запись раздела 23 переформулирована и обобщена за
пределы одного буквального имени роли: **ни одна `RoleAssignment`,
независимо от значения `role_code`, не вправе расшифровывать, получать
или связывать тайный голос** (см. раздел 23). Это не ограничение новой
возможности — уже сегодня ни один код в репозитории не расшифровывает и
не связывает `VoteEnvelope` с личностью (структурные гарантии
CT-00-08/09 это уже обеспечивают); правило лишь делает запрет явным и
именованным для любой Governance-роли, которую вводит настоящий раздел,
закрывая возможность прочитать будущую "administrator"- или
"governance"-подобную роль как неявное исключение из CT-00-09.

## 19b.2. GovernancePolicy

Реализует часть 5.12 "политика полномочий; версии правил" —
версионируемая, активируемая политика полномочий, аналог
`DisclosurePolicy` (19a.3) для Governance Context.

### Поля

- `governance_policy_id` — UUID.
- `policy_type` — enum: `role_taxonomy`, `approval_rule`,
  `challenge_rule`, `oversight_rule` — категория политики полномочий,
  которую версионирует данная запись.
- `rule_definition` — JSON-объект, версионируемое содержимое политики
  (например, для `policy_type = "role_taxonomy"` — закрытый набор
  допустимых значений `role_code` и правило, какая роль вправе выдавать
  какую другую роль, согласно ADR-020, §5).
- `effective_from` — timestamp.
- `proposed_by_role_id` — UUID, ссылка на `RoleAssignment` — актор,
  предложивший данную версию.
- `approved_by_role_id` — UUID, **не nullable**: любая версия
  `GovernancePolicy` требует явного, утверждённого двумя акторами
  перехода в `active` (INV-08; тот же приём, что и
  `DisclosurePolicy.approved_by_role_id`, 19a.3). `approved_by_role_id`
  должен отличаться от `proposed_by_role_id` — проверяется в момент
  активации, а не только документируется.
- `version` — целое число, монотонно возрастающее в пределах одного
  `policy_type`.
- `status` — enum: `draft`, `active`, `superseded`.

### Статусы и переходы

`draft → active` (требует заполненного `approved_by_role_id`, отличного
от `proposed_by_role_id`); `active → superseded` (только когда для того
же `policy_type` активируется новая версия — не более одной активной
версии на `policy_type` одновременно, тот же принцип, что и у
`DisclosurePolicy`). Возврат к `draft` невозможен.

### Запрещённые связи

- `GovernancePolicy → RoleAssignment.actor_id` в любом публично
  доступном представлении — запрещено (внутренние данные полномочий, та
  же категория ограничения, что и у `DisclosurePolicy.approved_by_role_id`,
  19a.3).

### Владелец

Governance Policy Service (раздел 22).

## 19b.3. GovernanceDecision

Реализует часть 5.12 "review procedures", а также "governance decisions
and mandates", "ballot invalidation authorization" и "oversight and
review workflows". Одна сущность с дискриминатором `decision_type` —
тот же приём консолидации, что и у `PublicLedgerEntry.subject_type`
(19a.1).

### Поля

- `governance_decision_id` — UUID.
- `decision_type` — enum, **обязан включать не менее**:
  `ballot_invalidation`, `technical_challenge_adjudication`,
  `result_finality_determination`, `mandate`, `oversight_directive`.
- `subject_reference` — JSON-объект, идентифицирующий предмет решения,
  форма которого зависит от `decision_type`:
  - `ballot_invalidation` → `{"ballot_id": <UUID>}`;
  - `technical_challenge_adjudication` → `{"technical_challenge_id":
<UUID>}`;
  - `result_finality_determination` → `{"result_publication_id":
<UUID>}`;
  - `mandate` / `oversight_directive` → произвольная форма, ограниченная
    предметом мандата/директивы (например, `RoleAssignment.scope_id`,
    `ModerationCase.moderation_case_id`) — конкретный допустимый набор
    форм для этих двух типов фиксируется отдельной реализационной
    задачей, а не настоящим разделом, поскольку ни один из них не
    порождает межпакетную запись (19b.6).
- `proposed_by_role_id` — UUID, ссылка на `RoleAssignment`.
- `approved_by_role_id` — nullable UUID, обязателен и должен отличаться
  от `proposed_by_role_id` до перехода `status` в `approved` (INV-08).
- `rejected_by_role_id` — nullable UUID, заполняется только при переходе
  `status` в `rejected`; также должен отличаться от
  `proposed_by_role_id`.
- `reason_code` — строка, из `contracts/reason-codes/pack-05.yml` либо
  переиспользуемого общего набора (раздел 24).
- `evidence_references` — список строк, произвольные ссылки на
  подтверждающие материалы (аналогично
  `EmergencyAction.evidence_references`, 19.1).
- `finality_outcome` — **nullable** enum, **имеет смысл только при
  `decision_type = "result_finality_determination"`** и **содержит
  только сохранённые, утверждённые значения: `final`, `invalidated`**.
  Именно это поле — а не какое-либо поле `ResultPublication` (15.6) —
  является местом, где хранится состояние окончательности результата; оно
  заполняется ровно один раз, когда решение с `decision_type =
"result_finality_determination"` переходит в `approved` (никогда
  раньше, никогда для `rejected` или ещё `proposed` записи). См.
  подраздел "FinalityStatus (производная модель чтения)" ниже для
  отдельного, производного четырёхзначного представления, в которое
  агрегируются эти два сохранённых значения.
- `created_at` — timestamp.
- `decided_at` — nullable timestamp, заполняется при переходе `status` в
  `approved` или `rejected`.
- `supersedes_decision_id` — nullable UUID. Любая `GovernanceDecision`
  неизменяема после перехода в `approved` или `rejected`. Исправление
  или отмена — никогда не редактирование существующей записи, а всегда
  **новая** запись `GovernanceDecision` с заполненным
  `supersedes_decision_id`, указывающим на заменяемое решение. Факт «это
  решение заменено» — производный, вычисляемый на момент чтения, тем же
  способом, что и `PublicLedgerEntry.supersedes_entry_id` (19a.1);
  никогда не записывается обратно в исходную запись и никогда не
  представляется отдельным хранимым значением статуса (см. `status`
  ниже).
- `status` — enum: `proposed`, `approved`, `rejected`. **`superseded` не
  является хранимым значением.**

### Статусы и переходы

`proposed → approved` (требует `approved_by_role_id`, отличного от
`proposed_by_role_id`); `proposed → rejected` (требует
`rejected_by_role_id`, отличного от `proposed_by_role_id`). **Перехода в
какое-либо значение `superseded` не существует, поскольку такого
хранимого значения не существует.** После перехода записи в `approved`
или `rejected` поле `status` никогда более не изменяется никакой
командой — факт «решение заменено» устанавливается исключительно
производной проверкой на момент чтения (существует ли другая
`GovernanceDecision` с `supersedes_decision_id`, равным идентификатору
данной записи) — тот же принцип «производный факт, не хранимое
значение», что и у `PublicLedgerEntry` (19a.1). Возврат к `proposed`
невозможен.

**Неизменяемость:** после перехода `GovernanceDecision` в `approved` или
`rejected` ни одно поле этой записи — включая `finality_outcome`,
`evidence_references` или `reason_code` — не может быть переписано
никакой последующей командой. Изменение позиции, новое обстоятельство
или исправление ошибочного решения представляется **исключительно**
новой `GovernanceDecision` с заполненным `supersedes_decision_id`, а не
обновлением исходной записи.

### FinalityStatus (производная модель чтения)

Не поле канонической сущности — тип модели чтения (query/read-model),
возвращаемый функцией `get_finality_status(result_publication_id)`
governance-сервиса (19b.6). Четыре значения:

- `provisional` — **только производное.** Для данной `ResultPublication`
  ещё не существует ни одной `result_finality_determination`
  `GovernanceDecision` (утверждённой или иной), и ни одна
  `TechnicalChallenge` против неё в данный момент не остаётся
  нерассмотренной.
- `finality_blocked` — **только производное.** Одна или более
  `TechnicalChallenge` против данной `ResultPublication` остаются в
  статусе `submitted` или `under_review` (19b.5) — определение
  окончательности структурно запрещено, пока это условие сохраняется.
- `final` — **отражает хранимое значение.** Последняя, не заменённая,
  `approved`-запись `result_finality_determination` `GovernanceDecision`
  для данной `ResultPublication` имеет `finality_outcome = "final"`.
- `invalidated` — **отражает хранимое значение.** Симметрично `final`,
  для `finality_outcome = "invalidated"`.

`provisional` и `finality_blocked` **никогда не записываются** как
значение `GovernanceDecision.finality_outcome` — они существуют
исключительно как результат запроса `get_finality_status`, вычисляемый
заново при каждом обращении из статусов `TechnicalChallenge` и
наличия/отсутствия утверждённого, не заменённого решения
`result_finality_determination`. `final`/`invalidated` — **единственные**
два значения, которые может принимать само поле `finality_outcome`;
`FinalityStatus` лишь передаёт их без изменения, когда хранимое решение
существует. Это разделение — одно хранимое двузначное поле плюс
отдельный производный четырёхзначный тип модели чтения — обязательно к
реализации как два различных определения типа в схемах и коде, никогда
как один общий четырёхзначный enum, используемый непоследовательно в
обоих местах.

### Запрещённые связи

- `GovernanceDecision → RoleAssignment.actor_id` в любом публично
  доступном представлении — запрещено.
- `GovernanceDecision.subject_reference → VoteEnvelope` — запрещено; ни
  один `decision_type` не вправе ссылаться на отдельный `VoteEnvelope`,
  только на агрегатные идентификаторы `ResultPublication`/`Ballot`.
- `GovernanceDecision → расшифровка, получение или связывание тайного
голоса` — повторяет обобщённый запрет 19b.1 применительно к данной
  сущности: ни одна `GovernanceDecision`, независимо от `decision_type`
  или того, какая `RoleAssignment` её предложила/утвердила, не вправе
  санкционировать расшифровку, получение или связывание тайного голоса.

### Владелец

Governance Decision Service (раздел 22).

## 19b.4. TechnicalChallenge

Реализует механизм регистрации и рассмотрения технического возражения
против `ResultPublication` (15.6) до наступления её
`challenge_deadline_at`, упомянутый в 15.6 как требующий отдельного
канонического либо утверждённого механизма. Адъюдикация технического
возражения структурно отделена от `GovernanceDecision`, которая по нему
выносится (19b.3, `decision_type = "technical_challenge_adjudication"`)
— тот же приём разделения, что и у `ModerationCase`/`ModerationDecision`
(раздел 14).

### Поля

- `technical_challenge_id` — UUID.
- `result_publication_id` — UUID, оспариваемая `ResultPublication`
  (15.6).
- `submitter_authorization_type` — enum: `participation_credential`,
  `role_assignment`.
- `submitter_authorization_reference` — непрозрачная, ограниченная в
  доступе ссылка на применимое доказательство полномочия подачи; никогда
  не разбирается, не разрешается и не разыменовывается никаким
  публично-ориентированным кодом. Форма зависит от
  `submitter_authorization_type`:
  - `participation_credential` — допущенный участник подаёт возражение
    через действительный, привязанный к конкретному Ballot
    `ParticipationCredential` (10.1); ссылка — непрозрачное значение
    вида credential-commitment, никогда не само секретное содержимое
    credential и не разрешаемый указатель на `Account`/`IdentityRecord`
    участника.
  - `role_assignment` — уполномоченный наблюдатель/рецензент подаёт
    возражение через активную, входящую в scope `RoleAssignment`; ссылка
    — идентификатор этой `RoleAssignment`.

  Ни `Account`, ни `IdentityRecord`, ни персональный идентификатор, ни
  секретное содержимое credential, ни `actor_id`, ни UUID
  `RoleAssignment` не могут появляться в публичном выводе; необработанная
  ссылка на полномочие остаётся ограниченной в доступе; рецензенты
  возражения не получают обратного пути от `ParticipationCredential` к
  личности участника.

  **Граница проверки:** `governance-service` проверяет ссылку типа
  `role_assignment` локально (`RoleAssignment` — его собственная
  сущность, проверка активности/scope — локальный запрос, межпакетное
  чтение не требуется). Ссылка типа `participation_credential` не
  проверяется повторно у `credential-service`/`eligibility-service` —
  настоящий раздел не вводит нового межпакетного чтения; ссылка
  принимается как предоставленное вызывающей стороной, структурно
  непрозрачное доказательство (тот же принцип, что и у
  caller-supplied `raw_content` в `publish_ledger_entry`, 19a).
- `challenge_reason_code` — строка, из `contracts/reason-codes/pack-05.yml`.
- `evidence_references` — список строк.
- `submitted_at` — timestamp. Должен строго предшествовать
  `ResultPublication.challenge_deadline_at` (15.6) оспариваемой записи —
  проверяется в момент подачи.
- `governance_decision_id` — nullable UUID, заполняется при вынесении
  решения: `GovernanceDecision` (19b.3, `decision_type =
"technical_challenge_adjudication"`), которая рассматривает именно это
  возражение.
- `status` — enum: `submitted`, `under_review`, `upheld`, `rejected`.

### Статусы и переходы

`submitted → under_review` (начинается рассмотрение); `under_review →
upheld` либо `under_review → rejected` (через связанную
`GovernanceDecision`, 19b.3). **Перехода из `upheld` или `rejected`
не существует** — `TechnicalChallenge` никогда не подаётся и не
рассматривается повторно после достижения любого из этих терминальных
статусов; новое сомнение в целостности той же `ResultPublication`
требует полностью новой записи `TechnicalChallenge`, сохраняя полную
историю, а не переписывая один итог другим.

### Запрещённые связи

- `TechnicalChallenge.submitter_authorization_reference → публичное
содержимое` — запрещено в исходном виде в любом публично доступном
  представлении; допустима только утверждённая генерализованная
  ролевая метка для пути `role_assignment`, если вообще какое-либо
  представление показывается; путь `participation_credential` не имеет
  публичного представления вовсе.
- `TechnicalChallenge → Account` / `IdentityRecord` / персональный
  идентификатор / секретное содержимое credential / `actor_id` / UUID
  `RoleAssignment`, в любом публичном выводе — запрещено.
- `TechnicalChallenge → VoteEnvelope` — запрещено; возражение касается
  агрегатной целостности `ResultPublication`, никогда отдельного голоса.

### Владелец

Technical Challenge Service (раздел 22).

## 19b.5. Правило агрегатного определения окончательности результата

Определяет, как `GovernanceDecision` (19b.3) и `TechnicalChallenge`
(19b.4) структурно взаимодействуют между собой:

- Каждая `TechnicalChallenge` против данной `ResultPublication` получает
  **собственную** `GovernanceDecision` с `decision_type =
"technical_challenge_adjudication"` — адъюдикация всегда один-к-одному
  с возражением, по которому выносится решение, никогда не
  объединяется по нескольким возражениям сразу.
- **Ровно одна** агрегатная `GovernanceDecision` с `decision_type =
"result_finality_determination"` создаётся для данной
  `ResultPublication`, и только после того, как **каждая**
  `TechnicalChallenge`, поданная против неё, достигла `upheld` или
  `rejected`. Определение окончательности для данной
  `ResultPublication` структурно запрещено, пока хотя бы одна
  `TechnicalChallenge` остаётся в статусе `submitted` или
  `under_review`.
- **Противоречащие друг другу решения об окончательности запрещены**:
  как только для `ResultPublication` существует утверждённая, не
  заменённая `result_finality_determination`, второе, независимое
  решение того же типа для той же `ResultPublication` создано быть не
  может — только новое решение с `supersedes_decision_id`, указывающим
  на предыдущее, вправе его заменить, никогда второе самостоятельное
  решение рядом с первым.
- Если `challenge_deadline_at` наступает при **нуле** поданных записей
  `TechnicalChallenge`, `GovernanceDecision` с `decision_type =
"result_finality_determination"` всё равно **обязательна** и требует
  явного утверждения двумя акторами — истечение срока является
  предпосылкой для её создания, но никогда не заменяет её (наступление
  `challenge_deadline_at` остаётся необходимым, но не достаточным
  условием окончательности, как и указано в 15.6).

## 19b.6. Межпакетная граница записи (Ballot, ResultPublication)

Governance Context нуждается в чтении состояния, которым владеют другие
контуры (`Ballot`, 15.1, и `ResultPublication`, 15.6), и в возможности,
чтобы утверждённое решение реально изменяло состояние сущности, которой
Governance Context не владеет. Настоящий подраздел фиксирует принятую
асимметричную модель:

- **Инвалидация Ballot:** `voting-service` остаётся **единственным**
  модулем записи `Ballot`. Он получает собственную, узко специализированную
  команду, которая перед переходом `Ballot.status → invalidated`
  подтверждает, что ссылающееся решение — `GovernanceDecision` (19b.3) с
  `decision_type = "ballot_invalidation"` — уже `approved` и относится
  именно к данному `Ballot`, посредством чтения из Governance Context.
  Governance Context никогда не записывает `Ballot` напрямую и не
  получает какой-либо функции записи, направленной в `voting-service`.
- **Окончательность результата:** ни `ResultPublication` (15.6), ни
  владеющий ею модуль не получают новой команды записи или нового поля.
  Состояние окончательности результата целиком представлено и
  запрашивается через `GovernanceDecision.finality_outcome` (19b.3) и
  производную модель `FinalityStatus` (19b.3) — через функцию чтения
  `get_finality_status(result_publication_id)`, реализуемую Governance
  Context. Модуль, владеющий `ResultPublication`, отвечает только на
  чтение (существование записи, `challenge_deadline_at`) и никогда не
  запрашивается и не отвечает на вопрос об окончательности напрямую.

Правило INV-02 (один владелец каждой сущности) сохраняется в полном
объёме: `voting-service` остаётся единственным модулем, когда-либо
записывающим `Ballot.status`; `ResultPublication` не получает второго
модуля записи, поскольку не получает записи вовсе со стороны Governance
Context.

## 19b.7. Структурное разделение с другими контурами

Ни одна из четырёх сущностей настоящего раздела (`RoleAssignment` в её
интеграции здесь, `GovernancePolicy`, `GovernanceDecision`,
`TechnicalChallenge`) не требует существования `PublicLedgerEntry`,
`AuditExportPackage`, `DisclosurePolicy` или `LobbyLogEntry` (19a),
`AIProcessingRecord` (17.1) или `EmergencyAction` (19.1). Настоящий
раздел не реализует Transparency Context, ИИ-обработку или
Emergency/Crisis Override и не расширяет их. Governance-решение,
становящееся публично видимым (например, через будущую публикацию в
`PublicLedgerEntry`), остаётся будущим вопросом Transparency Context, а
не записью или чтением настоящего раздела.

---

# 20. Канонические системные события

## 20.1. Account

- `account.created`
- `account.email_verified`
- `account.mfa_enabled`
- `account.restricted`
- `account.suspended`
- `account.closed`
- `account.session_revoked`

## 20.2. Identity

- `identity.verification_started`
- `identity.verified`
- `identity.verification_failed`
- `identity.verification_expired`
- `identity.duplicate_suspected`
- `identity.manual_review_required`

## 20.3. Eligibility

- `eligibility.evaluated`
- `eligibility.granted`
- `eligibility.denied`
- `eligibility.pending`
- `eligibility.snapshot_created`

## 20.4. Credential

- `credential.issued`
- `credential.activated`
- `credential.used`
- `credential.expired`
- `credential.revoked`
- `credential.validation_failed`

## 20.5. Organization

- `organization.created`
- `space.created`
- `space.activated`
- `space.suspended`
- `membership.applied`
- `membership.activated`
- `membership.suspended`
- `role.assigned`
- `role.revoked`

## 20.6. Initiative

- `initiative.draft_created`
- `initiative.submitted`
- `initiative.revision_requested`
- `initiative.published`
- `initiative.support_added`
- `initiative.support_withdrawn`
- `initiative.qualified`
- `initiative.deliberation_started`
- `initiative.legal_review_requested`
- `initiative.ready_for_ballot`
- `initiative.withdrawn`
- `initiative.archived`

## 20.7. Amendment

- `amendment.submitted`
- `amendment.published`
- `amendment.accepted`
- `amendment.rejected`
- `initiative.version_created`

## 20.8. Discussion

- `discussion.opened`
- `contribution.created`
- `contribution.edited`
- `contribution.flagged`
- `contribution.hidden`
- `contribution.restored`
- `discussion.closed`

## 20.9. Moderation

- `moderation.case_opened`
- `moderation.case_assigned`
- `moderation.decision_issued`
- `moderation.decision_enforced`
- `moderation.appeal_submitted`
- `moderation.appeal_decided`

## 20.10. Voting

- `ballot.created`
- `ballot.configuration_locked`
- `ballot.scheduled`
- `ballot.opened`
- `ballot.paused`
- `ballot.resumed`
- `vote.received`
- `vote.validated`
- `vote.rejected`
- `vote.superseded`
- `ballot.closed`
- `tally.started`
- `tally.completed`
- `tally.verified`
- `result.published`
- `ballot.cancelled`
- `ballot.invalidated`

## 20.11. Delegation

- `delegation.created`
- `delegation.activated`
- `delegation.revoked`
- `delegation.expired`
- `delegation.cycle_detected`
- `delegation.snapshot_created`

## 20.12. AI

- `ai.processing_requested`
- `ai.output_created`
- `ai.output_reviewed`
- `ai.output.corrected`
- `ai.output_rejected`

## 20.13. Emergency

- `emergency.proposed`
- `emergency.approved`
- `emergency.activated`
- `emergency.extended`
- `emergency.resolved`
- `emergency.report_published`

## 20.14. Прозрачность

Добавлено версией канона 0.3.0 (ADR-013). События создаются исключительно
`transparency-service` (19a) при публикации, экспорте или исправлении
записей настоящего раздела.

- `transparency.ledger_entry_published`
- `transparency.ledger_entry_corrected`
- `transparency.audit_export_generated`
- `transparency.audit_export_published`
- `transparency.disclosure_policy_defined`
- `transparency.disclosure_policy_activated`
- `transparency.disclosure_policy_superseded`
- `transparency.lobby_log_entry_submitted`
- `transparency.lobby_log_entry_published`
- `transparency.lobby_log_entry_corrected`

`transparency.ledger_entry_corrected` и
`transparency.lobby_log_entry_corrected` создаются при создании новой,
замещающей записи (19a.1, 19a.4) — не при изменении существующей
строки, поскольку такое изменение не допускается.

## 20.15. Governance

Добавлено версией канона 0.4.0 (ADR-018). События создаются
исключительно `governance-service` (19b) при предложении, утверждении,
отклонении, замене или подаче/адъюдикации записей настоящего раздела.

- `governance.role_assignment_requested`
- `governance.role_assignment_activated`
- `governance.role_assignment_revoked`
- `governance.policy_proposed`
- `governance.policy_activated`
- `governance.policy_superseded`
- `governance.decision_proposed`
- `governance.decision_approved`
- `governance.decision_rejected`
- `governance.decision_superseded`
- `governance.technical_challenge_submitted`
- `governance.technical_challenge_adjudicated`

`governance.decision_superseded` создаётся при утверждении новой,
замещающей `GovernanceDecision` с заполненным `supersedes_decision_id`
(19b.3) — не при изменении статуса замещаемой записи, поскольку
`GovernanceDecision.status` не хранит значения `superseded` и не
переписывается после `approved`/`rejected` (19b.3).

---

# 21. Стандарт события

Каждое событие передаётся в едином envelope.

```json
{
  "event_id": "uuid",
  "event_type": "initiative.submitted",
  "event_version": "1.0",
  "occurred_at": "ISO-8601",
  "producer": "initiative-service",
  "actor": {
    "actor_id": "uuid",
    "actor_type": "user"
  },
  "subject": {
    "subject_type": "initiative",
    "subject_id": "uuid"
  },
  "correlation_id": "uuid",
  "causation_id": "uuid",
  "payload": {},
  "integrity": {
    "payload_hash": "hash",
    "signature": "optional-signature"
  }
}
```

## Обязательные правила

- событие неизменяемо;
- повторная доставка не создаёт повторное действие;
- потребитель обязан проверять `event_id`;
- неизвестная major-версия события не обрабатывается;
- отсутствующее обязательное поле вызывает fail-closed;
- персональные данные не добавляются «на всякий случай».

---

# 22. Матрица владения сущностями

| Сущность | Модуль-владелец |
|---|---|
| Account | Account Service |
| IdentityRecord | Identity Verification Service |
| EligibilityRule | Eligibility Engine |
| EligibilityDecision | Eligibility Engine |
| ParticipationCredential | Credential Issuer |
| Organization | Organization Service |
| CivicSpace | Organization Service |
| Membership | Membership Service |
| RoleAssignment | Permission / Role Service |
| Initiative | Initiative Service |
| InitiativeVersion | Initiative Service |
| Amendment | Amendment Service |
| SourceRecord | Evidence Service |
| Discussion | Discussion Service |
| Contribution | Discussion Service |
| ModerationCase | Moderation Service |
| ModerationDecision | Moderation Service |
| Appeal | Appeal Service |
| Ballot | Ballot Definition Service |
| VoteEnvelope | Vote Casting Service |
| VoteReceipt | Receipt Service |
| Tally | Tally Service |
| ResultPublication | Result Publication Service |
| Delegation | Delegation Service |
| DelegationSnapshot | Delegation Resolution Engine |
| AIProcessingRecord | AI Accountability Service |
| AuditEvent | Audit Core |
| EmergencyAction | Governance / Crisis Service |
| PublicLedgerEntry | Public Ledger Service |
| AuditExportPackage | Audit Export Service |
| DisclosurePolicy | Disclosure Policy Service |
| LobbyLogEntry | Lobby Log Service |
| GovernancePolicy | Governance Policy Service |
| GovernanceDecision | Governance Decision Service |
| TechnicalChallenge | Technical Challenge Service |

Четыре строки (`PublicLedgerEntry`, `AuditExportPackage`,
`DisclosurePolicy`, `LobbyLogEntry`) добавлены версией канона 0.3.0
(ADR-013, раздел 19a). Физически все четыре реализуются одним сервисом,
`transparency-service` (ADR-011) — как и для ряда более ранних записей
этой матрицы, один физический сервис может владеть несколькими
канонически названными модулями.

Три строки (`GovernancePolicy`, `GovernanceDecision`,
`TechnicalChallenge`) добавлены версией канона 0.4.0 (ADR-018, раздел
19b). Физически все три реализуются одним сервисом, `governance-service`
(ADR-016), вместе с уже существующей строкой `RoleAssignment`
("Permission / Role Service", без изменений настоящей версией) — тот же
принцип "один физический сервис — несколько канонически названных
модулей".

---

# 23. Запрещённые связи

Следующие технические связи запрещены.

- `VoteEnvelope → Account`
- `VoteEnvelope → IdentityRecord`
- `VoteReceipt → email`
- `Tally → IdentityRecord`
- `AIProcessingRecord → скрытый IdentityRecord`, если личность не требуется для заявленной операции
- `PublicLedgerEntry → непубличные персональные данные`
- `ModerationDecision → возможность физического удаления AuditEvent`
- `RoleAssignment (любой role_code, включая "administrator") →
расшифровка, получение или связывание тайного голоса` (изменено 0.4.0,
  19b.1 — ранее сформулировано как `AdministratorRole → право
расшифровать тайные голоса`; `AdministratorRole` не является отдельной
  сущностью, см. 19b.1)
- `Identity provider reference → Participation database`
- `Credential → полная копия личных данных`
- `PublicLedgerEntry → Account` / `IdentityRecord` / `ParticipationCredential` / `VoteEnvelope` / `Delegation` / `DelegationSnapshot` (добавлено 0.3.0, 19a.1)
- `AuditExportPackage → AuditEvent.actor_id` / `actor_type` / `before_hash` / `after_hash` (добавлено 0.3.0, 19a.2)
- `published_by_role_id` / `requested_by_role_id` / `approved_by_role_id` / `submitted_by_role_id` → публикация в исходном виде (добавлено 0.3.0, 19a.6) — допустима только генерализованная метка роли
- `DisclosurePolicy.field_rules` → переклассификация структурно запрещённого поля в класс, отличный от `prohibited` (добавлено 0.3.0, 19a.3)
- `GovernancePolicy → RoleAssignment.actor_id` в публично доступном представлении (добавлено 0.4.0, 19b.2)
- `GovernanceDecision → RoleAssignment.actor_id` в публично доступном представлении (добавлено 0.4.0, 19b.3)
- `GovernanceDecision.subject_reference → VoteEnvelope` (добавлено 0.4.0, 19b.3)
- `TechnicalChallenge.submitter_authorization_reference` → публикация в исходном виде (добавлено 0.4.0, 19b.4)
- `TechnicalChallenge → Account` / `IdentityRecord` / персональный идентификатор / секретное содержимое credential / `actor_id` / UUID `RoleAssignment`, в публичном выводе (добавлено 0.4.0, 19b.4)
- `TechnicalChallenge → VoteEnvelope` (добавлено 0.4.0, 19b.4)

---

# 24. Стандарт reason codes

Все значимые отказы и ограничения используют стабильные коды.

- `IDENTITY_NOT_VERIFIED`
- `IDENTITY_VERIFICATION_EXPIRED`
- `ELIGIBILITY_NOT_MET`
- `ELIGIBILITY_PENDING`
- `CREDENTIAL_EXPIRED`
- `CREDENTIAL_ALREADY_USED`
- `CREDENTIAL_SCOPE_MISMATCH`
- `PERMISSION_DENIED`
- `ROLE_CONFLICT`
- `BALLOT_NOT_OPEN`
- `BALLOT_ALREADY_CLOSED`
- `BALLOT_CONFIGURATION_LOCKED`
- `DUPLICATE_SUPPORT`
- `DUPLICATE_VOTE`
- `DELEGATION_CYCLE`
- `DELEGATION_EXPIRED`
- `MODERATION_POLICY_VIOLATION`
- `APPEAL_DEADLINE_EXPIRED`
- `EVENT_VERSION_UNSUPPORTED`
- `INTEGRITY_CHECK_FAILED`
- `SERVICE_STATE_READ_ONLY`
- `EMERGENCY_FREEZE_ACTIVE`

Reason code не заменяется свободным текстом.

---

# 25. Версионирование канона

Используется semantic versioning.

## Patch

Исправление описания без изменения поведения.

Пример:

`0.1.0 → 0.1.1`

## Minor

Добавление обратно совместимой сущности, поля, события или статуса.

Пример:

`0.1.0 → 0.2.0`

## Major

Изменение:

- обязательного поля;
- смысла события;
- владельца сущности;
- архитектурного инварианта;
- правил анонимности;
- жизненного цикла критического объекта.

Пример:

`0.x → 1.0`

---

# 26. Architecture Decision Record

Любое отклонение оформляется в ADR.

## Обязательные поля ADR

- `ADR-ID`
- название;
- инициатор;
- дата;
- проблема;
- контекст;
- варианты;
- принятое решение;
- затронутые сущности;
- затронутые события;
- риски;
- миграция;
- обратимость;
- статус одобрения.

### Статусы ADR

- `proposed`
- `under_review`
- `accepted`
- `rejected`
- `superseded`
- `implemented`

До статуса `accepted` изменение не включается в рабочий код.

---

# 27. Минимальные contract tests

Каждый модуль должен проходить общий набор тестов.

## CT-00-01. Schema Validation

Невалидная структура отклоняется.

## CT-00-02. Unknown Status

Неизвестный статус не принимается.

## CT-00-03. Forbidden Transition

Запрещённый переход отклоняется.

## CT-00-04. Event Idempotency

Повтор одного `event_id` не создаёт второе действие.

## CT-00-05. Unsupported Event Version

Неизвестная major-версия не обрабатывается.

## CT-00-06. Missing Permission

Действие без полномочий отклоняется.

## CT-00-07. Audit Creation

Критическое действие создаёт `AuditEvent`.

## CT-00-08. Identity Leakage

Participation response не содержит identity-полей.

## CT-00-09. Vote Linkability

Обычный администратор не может получить account ID по `VoteEnvelope`.

## CT-00-10. Rule Freeze

После открытия `Ballot` конфигурация не изменяется.

## CT-00-11. AI Human Control

ИИ-результат не становится официальным без требуемого подтверждения.

## CT-00-12. Emergency Stop

При активном freeze запрещённые операции не выполняются.

---

# 28. Gate ТЗ-00

ТЗ-00 считается принятым, когда:

1. определены все основные доменные контуры;
2. у каждой сущности установлен один владелец;
3. зафиксированы архитектурные инварианты;
4. зафиксировано разделение Identity и Participation;
5. определены базовые статусы инициативы;
6. определены базовые статусы голосования;
7. определены сущности делегирования;
8. определена структура AuditEvent;
9. определены канонические события;
10. определены запрещённые связи;
11. определён порядок изменения канона;
12. определён минимальный набор contract tests;
13. все последующие пакеты обязаны ссылаться на версию настоящего документа.

---

# 29. Открытые решения до разработки голосования

Следующие вопросы не блокируют инфраструктурный этап, но должны быть решены до пакета Voting:

1. Может ли участник изменить голос до закрытия голосования?
2. Какой вариант считается действительным при изменении голоса?
3. Допускается ли воздержание как отдельный вариант?
4. Какие типы голосования входят в пробник?
5. Требуется ли кворум для всех процедур?
6. Кто может создавать голосование?
7. Кто утверждает его окончательные параметры?
8. Разрешается ли делегирование в первом пробнике?
9. Какова максимальная глубина делегирования?
10. Может ли делегатор проголосовать самостоятельно, отменив делегацию для конкретного Ballot?
11. Как обрабатываются ничьи?
12. Когда результат считается окончательным?
13. Какой срок предусмотрен для технического оспаривания результата?
14. Кто вправе признать голосование недействительным?
15. Какие данные audit package публикуются открыто?

---

# 30. Следующая стадия

После принятия ТЗ-00 разработка переходит к:

**CLAUDE-PACK-01 — Repository Skeleton**

Claude Code должен использовать настоящий документ как неизменяемую зависимость, поместив его по пути:

```text
docs/canonical/TZ-00-domain-event-canon.md
```

Claude Code не должен редактировать настоящий документ в рамках CLAUDE-PACK-01.
