# EPD² CIVIC OS
## ТЗ-00. Каноническая модель домена и событий

**Версия:** 0.7.0  
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

# 19c. ИИ-обработка — расширение (AI Processing Context)

Добавлено версией канона 0.5.0 (ADR-023, ADR-025, приняты 2026-07-24) и
расширяет уже существующий раздел 17 ("ИИ-обработка"), определяющий
`AIProcessingRecord` (17.1) с двенадцатью полями и шестизначным
статусом `human_review_status`. Раздел вставлен под номером 19c, между
разделами 19b (Governance Context) и 20 (Канонический каталог событий),
чтобы не переносить нумерацию уже существующих разделов 20–30 — тот же
приём, использованный при добавлении разделов 19a (ADR-013, версия
0.3.0) и 19b (ADR-018/ADR-020, версия 0.4.0).

`AIProcessingRecord` (17.1) остаётся единственной сущностью настоящего
раздела; её владелец не меняется (AI Accountability Service, раздел
22). Ни одно поле, статус, событие или запрет ни одного другого
контура — Governance Context (19b), Transparency Context (19a),
Moderation (раздел 14), Identity/Credential-слои (разделы 6–10),
Emergency/Crisis Override (раздел 19) — не изменяется настоящим
разделом.

## 19c.1. AIProcessingRecord — сохранённые поля и `human_review_status`

Двенадцать существующих полей `AIProcessingRecord` (17.1) остаются без
изменений: `ai_processing_record_id`, `purpose_code`, `target_type`,
`target_id`, `input_version`, `model_provider`, `model_name`,
`model_version`, `prompt_template_version`, `output_reference`,
`created_at`, `human_review_status`, `correction_reference`.
`target_type` и `target_id` остаются непрозрачными,
предоставленными вызывающей стороной ссылками и никогда не
разыменовываются через `initiative-service`, `deliberation-service`,
`moderation-service`, `voting-service`, `tally-service`,
`delegation-service` или `transparency-service`.

Шестизначный статус `human_review_status` (`not_required`, `pending`,
`approved`, `approved_with_changes`, `rejected`, `superseded`) не
изменяется: ни одно значение не добавлено, не удалено и не
переименовано. Его семантика уточняется, не изменяется:

- `superseded` достигается на существующей записи `AIProcessingRecord`
  **исключительно** при создании новой записи с заполненным
  `supersedes_ai_processing_record_id` (19c.2), указывающим на
  заменяемую запись — никогда как самостоятельный переход без
  соответствующей новой записи.
- После того как `human_review_status` записи достигает `approved`,
  `approved_with_changes`, `rejected` или `superseded`, ни одно поле
  этой записи, включая `output_reference`, никогда более не
  переписывается никакой командой — тот же принцип неизменяемости
  после решения, что и у `GovernanceDecision` (19b.3) и
  content-неизменяемости `PublicLedgerEntry` (19a.1). Исправление —
  всегда новая запись `AIProcessingRecord` со ссылкой
  `supersedes_ai_processing_record_id`, никогда переписывание исходной
  записи.
- `not_required` допустим только для **non-consequential** результата
  (точное определение — 19c.8). Для любого **consequential**
  использования `human_review_status` обязан начинаться со значения
  `pending` и достигать терминального значения только через явное
  человеческое действие (`approved`/`approved_with_changes`/
  `rejected`); молчание, истечение времени ожидания или отсутствие
  рецензента никогда не читается как одобрение.

### `processing_status` (новое поле, новый статус)

Новое поле, ограниченное исключительно технической
конвейерно-обрабатывающей плоскостью и структурно отделённое от
`human_review_status`:

- `requested` — запрос зафиксирован; вызов модели ещё не производился.
- `input_prepared` — шаг валидации редактирования/происхождения (19c.4)
  завершён успешно, `redaction_manifest` заполнен с `result = "pass"`;
  вызов модели ещё не производился.
- `processing` — вызов модели выполняется (переходное состояние без
  отдельного события, тем же приёмом, что и у других переходных
  состояний этого проекта).
- `completed` — вызов модели вернул пригодный к использованию
  результат.
- `failed` — вызов модели не смог вернуть пригодный к использованию
  результат.
- `rejected_by_policy` — обработка отклонена, до или после вызова
  модели, проверкой политики.

**`processing_status` не имеет хранимого значения `superseded`.**
Заменена ли данная попытка обработки более поздней — производный,
вычисляемый на момент чтения факт: проверяется, существует ли другая
запись `AIProcessingRecord` с `supersedes_ai_processing_record_id`,
равным идентификатору данной записи (19c.2).

**Допустимые переходы:** `requested → input_prepared → processing →
{completed | failed | rejected_by_policy}`. `rejected_by_policy` также
напрямую достижим из `requested`. Ни один переход не возвращается к
более раннему значению; `completed`, `failed` и `rejected_by_policy`
терминальны.

## 19c.2. `supersedes_ai_processing_record_id` — неизменяемая замена

Новое поле: nullable UUID, ссылка на `ai_processing_record_id` другой
записи `AIProcessingRecord`. Заполняется на **новой** записи именно
тогда, когда эта новая запись заменяет существующую — **никогда
задним числом на старой записи**: поля старой записи никогда не
переписываются, только новая запись несёт обратную ссылку. Заменена ли
данная запись — всегда производный, вычисляемый на момент чтения факт,
тем же способом, что и `GovernanceDecision.supersedes_decision_id`
(19b.3) и `PublicLedgerEntry.supersedes_entry_id` (19a.1). Один и тот
же механизм покрывает как замену технической попытки обработки
(`processing_status`), так и замену итога человеческой проверки
(`human_review_status`) — оба случая используют одно и то же поле, а не
два раздельных механизма замены.

## 19c.3. Дополнительные поля: модель, провенанс, уверенность, объяснимость, жизненный цикл

`AIProcessingRecord` получает следующие дополнительные поля,
сгруппированные по назначению:

- **Управление моделью и развёртыванием:** `deployment_version`,
  `system_policy_version`, `generation_settings`, `processing_region`,
  `data_retention_mode`, `external_provider_flag`.
- **Происхождение и целостность:** `input_hash`, `output_hash`.
- **Уверенность и неопределённость:** `confidence_score`,
  `uncertainty_indicator`.
- **Объяснимость:** `explanation_reference`, `reason_codes`.
- **Происхождение решения рецензента:** `human_reviewer_reference` —
  непрозрачная ссылка (тот же приём, что и
  `TechnicalChallenge.submitter_authorization_reference`, 19b.4);
  проверяется, для consequential-проверки, через существующую
  `RoleAssignment` (8.4) на стороне Governance Context (репозиторный
  механизм проверки — вне настоящего раздела, см. 19c.9), никогда не
  принимается как непроверенное утверждение.
- **Временные метки жизненного цикла:** `completed_at`, `reviewed_at`.

Существующие двенадцать полей и шестизначный статус `human_review_status`
(19c.1) остаются без изменений.

## 19c.4. `redaction_manifest` — RedactionManifest как встроенный неизменяемый объект-значение

**`RedactionManifest` — канонически определённый, неизменяемый,
встроенный объект-значение внутри `AIProcessingRecord`**, а не отдельная
сущность и не выбираемое на этапе реализации представление.
`AIProcessingRecord` получает одно новое поле, `redaction_manifest`
(nullable, пока `processing_status = requested`; обязательно и
неизменяемо начиная с `input_prepared`), содержащее ровно:

- `redaction_policy_reference` — какая политика редактирования
  выполнила данную проверку.
- `redaction_policy_version` — версия этой политики.
- `input_classification` — заявленная вызывающей стороной либо локально
  выведенная классификация входного содержимого.
- `checked_field_categories` — какие категории запрещённого содержимого
  (identity, credential, vote-linkage, unrestricted audit) были
  проверены.
- `removed_field_categories` — какие из проверенных категорий были
  обнаружены и исключены — **никогда сами удалённые значения.**
- `prepared_input_hash` — тот же дайджест, что и `input_hash` (19c.3),
  продублированный здесь для самодостаточности манифеста.
- `validator_version` — версия самой логики валидации редактирования.
- `validated_at` — временная метка выполнения проверки.
- `result` — `pass` | `fail`.

**`redaction_manifest` никогда не содержит:** исходный ввод; удалённые
значения; данные личности; данные credential; содержимое голоса;
содержимое приватного аудита — только метаданные уровня категории о
том, что было проверено и что было обнаружено и исключено, тот же
принцип «категория, не содержимое», что и у публично-безопасных
метаданных `AuditExportPackage.chain_proof` (19a.2).

**После записи `redaction_manifest` никогда не изменяется** — он
устанавливается ровно один раз, самим `ai-processing-service` (никогда
не принимается как предоставленный вызывающей стороной), в момент
завершения шага валидации редактирования/происхождения, независимо от
того, `pass` или `fail` результат. Значение `fail` — само по себе
зафиксированный, постоянный факт об этой попытке обработки, а не то,
что исправляется на месте более поздним шагом; исправленная попытка —
всегда новая запись `AIProcessingRecord` (19c.2).

## 19c.5. Жизненный цикл раскрытия (disclosure) и `DisclosureStatus`

`AIProcessingRecord` получает три дополнительных поля:

- `disclosure_required` — boolean. Устанавливается один раз, при
  создании записи или не позднее перехода `processing_status →
completed`, на основании того, подпадает ли использование данной
  записи под обязательное правило раскрытия (19c.7) — официальный или
  публичный ИИ-содействующий результат. Никогда не изменяется задним
  числом.
- `disclosure_package_reference` — nullable, непрозрачная ссылка на
  `AIDisclosurePackage` (19c.6), которую конструирует
  `ai-processing-service` для данной записи, после того как пакет
  сконструирован. Никогда не содержит и не указывает ни на что,
  содержащее исходный ввод, исходный приватный результат, скрытый
  prompt, личность рецензента, UUID `RoleAssignment`, данные личности,
  данные credential или скрытые рассуждения.
- `disclosure_receipt_reference` — nullable, непрозрачная ссылка на
  подтверждение, которое возвращает
  `transparency-service.publish_ledger_entry` после публикации
  соответствующей `PublicLedgerEntry`. Устанавливается ровно один раз,
  никогда не переписывается.

**`DisclosureStatus`** — не поле канонической сущности, а тип модели
чтения (query/read-model), вычисляемый из трёх полей выше:

- `not_required` — `disclosure_required = false`.
- `pending_package` — `disclosure_required = true` и
  `disclosure_package_reference` ещё не установлена.
- `pending_publication` — `disclosure_required = true`,
  `disclosure_package_reference` установлена,
  `disclosure_receipt_reference` ещё не установлена.
- `published` — `disclosure_required = true` и
  `disclosure_receipt_reference` установлена.

**`DisclosureStatus` — производный и не изменяется независимо** — ни
одна команда никогда не записывает значение `DisclosureStatus`
напрямую; оно всегда вычисляется заново, на момент запроса, из трёх
полей выше — тот же принцип «производное, не хранимое отдельно», что и
у `FinalityStatus` (19b.3).

## 19c.6. `AIDisclosurePackage` — договорной объект, не каноническая сущность

**`AIDisclosurePackage` — договорной объект/объект-значение
(contract/value object), а не новая каноническая сущность системы
записи.** Это временный payload, который `ai-processing-service`
конструирует и передаёт `transparency-service.publish_ledger_entry` как
предоставленное вызывающей стороной содержимое (`raw_content`) — он
никогда не сохраняется как строка, которой владеет
`ai-processing-service` или `transparency-service`; его единственный
устойчивый след — (а) результирующая запись `PublicLedgerEntry`,
которой уже владеет и которую уже сохраняет `transparency-service` под
своим существующим владением (19a.1, без изменений настоящим
разделом, при `subject_type = ai_processing_record`, уже принятом и до
сих пор не задействованном, ADR-013 D3.5), и (б) непрозрачные значения
`disclosure_package_reference`/`disclosure_receipt_reference`,
записанные на исходной `AIProcessingRecord` (19c.5). Точная схема
`AIDisclosurePackage` фиксируется на этапе реализации как
`contracts/schemas/` JSON Schema — не каноническое добавление и не
второй источник истины для факта, который уже фиксирует
`PublicLedgerEntry`.

**Обязательное содержимое:** факт использования ИИ-содействия;
`purpose_code`; утверждённая публичная категория и версия модели/
провайдера; дата обработки; статус человеческой проверки; принял ли
человек черновик без изменений, с изменениями или отклонил; ссылки на
версию prompt-шаблона и версию системной политики; публичная ссылка на
`AIProcessingRecord`.

**Запрещённое содержимое:** исходный ввод; исходный приватный результат
(если он отдельно не утверждён для публикации); скрытые prompt;
приватная личность рецензента; любой UUID `RoleAssignment`; данные
identity/account/credential; данные голоса; скрытые рассуждения
(chain-of-thought).

## 19c.7. Обязательный протокол раскрытия для официального/публичного ИИ-содействующего результата

Для **consequential** официального или публичного ИИ-содействующего
результата (точное определение — 19c.8) обязателен следующий,
пятишаговый протокол — заменяющий любую неформальную договорённость об
оркестрации конкретной, проверяемой структурой:

1. Consequential официальный/публичный результат ИИ получает
   подтверждённое человеческое одобрение (`human_review_status →
approved` либо `approved_with_changes`).
2. `ai-processing-service` создаёт неизменяемый, отредактированный
   `AIDisclosurePackage` (19c.6) и записывает ссылку на него в
   `disclosure_package_reference` (19c.5) — `DisclosureStatus`
   становится `pending_publication`.
3. `transparency-service` публикует пакет через уже существующую
   команду `publish_ledger_entry` (`PublicLedgerEntry.subject_type =
ai_processing_record`, ADR-013 D3.5), передавая содержимое
   `AIDisclosurePackage` как предоставленное вызывающей стороной
   `raw_content` — новая связь чтения или записи между сервисами не
   вводится, используется уже существующий приём — и возвращает
   `disclosure_receipt_reference`.
4. Ссылка на подтверждение записывается в `AIProcessingRecord`
   (`disclosure_receipt_reference`, 19c.5) — `DisclosureStatus`
   становится `published`.
5. Владеющий сервис вправе завершить официальный/публичный артефакт
   **только когда**: `disclosure_required = true`; `DisclosureStatus =
published`; `disclosure_receipt_reference` присутствует. Любая попытка
   завершения до выполнения всех трёх условий отклоняется — в команде
   владеющего сервиса, а не как проверка, которую
   `ai-processing-service` выполняет от имени другой сущности, поскольку
   `ai-processing-service` никогда не помечает какую-либо другую
   сущность «завершённой».

**Правила:**

- `ai-processing-service` никогда не записывает хранилище Transparency
  Context — он только конструирует пакет и передаёт его как
  предоставленное вызывающей стороной содержимое.
  **`transparency-service` остаётся единственным модулем записи
  `PublicLedgerEntry`.**
- Отсутствие подтверждения — fail-closed: `DisclosureStatus` остаётся
  на значении `pending_publication` (либо `pending_package`, если не
  удался сам шаг 2), пока не записано настоящее подтверждение; иного,
  ослабленного пути к `published` не существует.
- Официальный/публичный артефакт не вправе полагаться исключительно на
  договорённость на уровне оркестрации или на утверждение вызывающей
  стороны — проверка шага 5 выполняется против реальных, сохранённых
  полей `AIProcessingRecord` и производного `DisclosureStatus`, а не
  против утверждения, предоставленного любым вызывающим.

## 19c.8. Consequential-use семантика и человеческий контроль

**Consequential результат** — любой результат ИИ, который: становится
официальным или публичным содержимым; на который ссылается человеческое
решение модерации или governance; влияет на участник-ориентированную
классификацию; инициирует или рекомендует формальный процесс проверки;
включается в каноническую сущность; либо может существенно повлиять на
доступ, участие, репутацию, голосование, публичную информацию или
governance.

**Consequential результат всегда требует подтверждённой человеческой
проверки** — полный путь `human_review_status` (19c.1) **и**, для
любого использования, требующего разделения ролей (модерация,
governance, ballot-adjacent, официальная публикация), проверку
полномочий рецензента через существующую `RoleAssignment` (8.4) на
стороне Governance Context — никогда не только заявленный
`actor_is_authorized`. Рецензент обязан отличаться от актора, подавшего
запрос ИИ. Итоговое человеческое действие всегда остаётся командой
владеющего сервиса, никогда командой сервиса ИИ-обработки.

**Non-consequential внутреннее содействие** вправе использовать
`human_review_status = not_required` (19c.1), но никогда не вправе
вызывать изменение состояния или официальную публикацию.

Молчание, истечение времени ожидания или отсутствие рецензента никогда
не читается как одобрение (повторяет 19c.1 применительно к настоящему
подразделу).

## 19c.9. Структурное разделение с другими контурами и инварианты

`AIProcessingRecord` (17.1, 19c.1–19c.8) не требует существования
`GovernancePolicy`, `GovernanceDecision`, `TechnicalChallenge` (19b),
`PublicLedgerEntry`, `AuditExportPackage`, `DisclosurePolicy` или
`LobbyLogEntry` (19a), либо `EmergencyAction` (19.1). Настоящий раздел
не реализует Governance Context, Transparency Context или
Emergency/Crisis Override и не расширяет их. Единственная точка, где
настоящий раздел опирается на решение, похожее на governance (проверка
полномочий рецензента), разрешена через уже существующую,
узкоспециализированную роль `RoleAssignment` (8.4), а не через
определение новой сущности настоящего раздела; конкретный механизм
этой проверки (специализированная функция чтения на стороне
Governance Context) — репозиторный, не канонический, и не описывается
настоящим разделом.

Настоящий раздел, вместе с уже существующим инвариантом INV-07 (раздел
9) и раздела 23, закрепляет следующие структурные инварианты для
ИИ-обработки:

- Ни `AIProcessingRecord`, ни какой-либо процесс настоящего раздела не
  вправе самостоятельно принимать политическое, governance-,
  модерационное, голосующее, eligibility-, ролевое, emergency- или
  публикационное решение — каждое из них остаётся исключительно
  командой сервиса, которому принадлежит соответствующая сущность
  (`Initiative`, `GovernanceDecision`, `ModerationDecision`, `Ballot`,
  `EligibilityDecision`, `RoleAssignment`, `EmergencyAction`,
  `PublicLedgerEntry` соответственно).
- Ни `AIProcessingRecord`, ни `redaction_manifest` (19c.4), ни
  `AIDisclosurePackage` (19c.6) не вправе обеспечивать обратный поиск
  скрытой личности (`IdentityRecord`), не требуемой для заявленной
  операции.
- Ни `AIProcessingRecord`, ни какой-либо процесс настоящего раздела не
  вправе восстанавливать связь между `VoteEnvelope` и личностью либо
  агрегировать содержимое голоса за пределами уже существующих
  структурных гарантий CT-00-08/09.
- Ни один внешний провайдер модели не получает полномочий на мутацию
  Civic OS — ни через callback, ни через tool-calling интерфейс (19c.6,
  протокол абстракции провайдера — репозиторное содержимое).
- `AIDisclosurePackage` (19c.6) никогда не содержит исходный приватный
  ввод или исходный приватный результат, кроме отдельно утверждённого
  для публикации содержимого.
- Ни `AIProcessingRecord`, ни `AIDisclosurePackage`, ни какое-либо
  публичное представление настоящего раздела не заявляют и не содержат
  скрытые рассуждения модели (chain-of-thought) как факт или
  доказательство.

---

# 19d. Участие и членство (Participation & Membership Context)

Добавлено версией канона 0.6.0 (ADR-026 через ADR-031, приняты
2026-07-25) и реализует расширение контура 5.2 (Eligibility Context)
процесс-специфичной избирательной правоспособностью, а также новый
слой политики членства в партии, ранее не имевший канонической опоры,
кроме уже существующих `Membership` (8.3) и `RoleAssignment` (8.4).
Раздел вставлен под номером 19d, между разделами 19c (AI Processing
Context) и 20 (Канонический каталог событий), чтобы не переносить
нумерацию уже существующих разделов 20–30 — тот же приём, использованный
при добавлении разделов 19a, 19b и 19c.

Десять новых канонических сущностей настоящего раздела физически
реализуются двумя сервисами: `eligibility-service` (уже существующий с
PACK-02, впервые расширяемый настоящим разделом) владеет
`ParticipantEligibilityPolicy`, `ProcessEligibilityPolicy`,
`StepUpAuthenticationRequirement`, `DigitalDecision`, `AssemblyDecision`;
новый `membership-service` владеет `PartyMembershipEligibilityPolicy`,
`AffiliationDeclaration`, `ConflictAssessment`, `MembershipApplication`;
`identity-service` (существующий с PACK-02) получает новую сущность
`AuthenticationContext`. `Membership` (8.3) и `RoleAssignment` (8.4)
остаются без изменений полей, статусов или владельца. Ни одно поле,
статус, событие или запрет ни одного другого контура — Governance
Context (19b), Transparency Context (19a), AI Processing Context (19c),
Moderation (раздел 14), Emergency/Crisis Override (раздел 19) — не
изменяется настоящим разделом. Настоящий раздел не авторизует код
`membership-service`, расширение `eligibility-service`, схемы,
OpenAPI-файлы или исполняемый реестр reason codes — только
каноническую модель (раздел 26; `docs/review/PACK-07-OWNER-DECISIONS.md`).

## 19d.1. Обзор: разделение сервисов и `ParticipantEligibilityPolicy` vs `PartyMembershipEligibilityPolicy`

`ParticipantEligibilityPolicy` (19d.4, `eligibility-service`) и
`PartyMembershipEligibilityPolicy` (19d.6, `membership-service`) —
структурно раздельные сущности с раздельным версионированием и
активацией; ни одна не является частным случаем другой.
`eligibility-service` никогда не создаёт и не изменяет `Membership`;
`membership-service` никогда не становится владельцем общей
правоспособности участия Civic OS. Платформенный участник не обязан
иметь запись `Membership`. `ParticipationRightsProfile` (19d.13) —
единственная точка, где результаты обоих сервисов и `RoleAssignment`
сводятся вместе, и делает это исключительно как производное, не
хранимое представление.

## 19d.2. `IdentityRecord` — дополнительные поля

`IdentityRecord` (7.3) сохраняет все десять существующих полей без
изменений (`identity_record_id`, `account_id`, `verification_provider`,
`verification_level`, `verification_status`, `verified_at`,
`expires_at`, `country`, `duplicate_check_status`,
`provider_reference`) и владельца (Identity Verification Service).
Настоящий раздел добавляет восемь новых полей:

- `date_of_birth`.
- `citizenship_status` — список гражданств; допускает безгражданство и
  множественное гражданство, никогда не единственное булево значение.
- `residence_status` — встроенный объект с как минимум `residence_type`
  (включая значение, соответствующее habitual residence) и
  `territorial_connection`.
- `identity_assurance_level` — enum `none`/`low`/`substantial`/`high` —
  уровень доверия к самому подтверждению личности. Не совпадает и не
  подменяет `authentication_assurance_level` (19d.8).
- `identity_scheme` — открытая, расширяемая строка (не менее:
  `de_personalausweis_online`, `eu_eea_eid_card`, `eidas_foreign_eid`,
  `other_approved_method`); никогда не является признаком гражданства.
- `attribute_verification_level`, `attribute_verified_at`,
  `attribute_valid_until` — актуальность подтверждения **конкретного**
  атрибута, отдельно от общей верификации личности.

**Обязательное разделение, без исключений:** подтверждение личности
через любой из перечисленных `identity_scheme` не эквивалентно и не
подразумевает немецкое (или любое иное конкретное) гражданство.
`verification_status`/`identity_assurance_level` вычисляются
исключительно из факта и качества верификации личности и никогда не
используются как замена, источник или подтверждение
`citizenship_status`. Ни одно правило настоящего раздела не
ограничивает верифицированное участие, подачу заявления о партийном
членстве или партийное членство гражданами одной страны — гражданин
любого государства ЕС/ЕЭП, верифицированный через любой поддерживаемый
маршрут, может стать верифицированным участником, заявителем или
членом при соблюдении применимой политики.

## 19d.3. Четыре отдельных признака избирательного права

Настоящий раздел не вводит и никогда не вводит единого обобщённого
признака `electoral_eligibility_met` — такого поля, статуса или
производного значения не существует ни в каноне, ни в одной реализации,
основанной на нём. Вместо этого — четыре независимо вычисляемых
булевых признака:

- `active_electoral_eligibility_met` — право голосовать в
  соответствующем публичном избирательном процессе.
- `passive_electoral_eligibility_met` — право быть кандидатом в том же
  публичном избирательном процессе.
- `party_internal_voting_eligibility_met` — право голосовать во
  внутрипартийных решениях.
- `party_office_candidacy_eligibility_met` — право выдвигаться на
  партийную должность.

Ни одно поле или флаг не представляет «избирательное право» обобщённо
— каждый потребитель обязан указывать, какой из четырёх вопросов он
задаёт. Первые два вычисляются исключительно из фактов
идентификационного слоя (возраст, гражданство, резидентство,
территориальная связь); последние два дополнительно используют узкое
чтение `eligibility-service → membership-service`
(`required_membership_status_met`/`membership_duration_requirement_met`,
19d.1) — `membership-service` никогда не вычисляет избирательный
признак самостоятельно. Один и тот же человек может получить разные
результаты для разных процессов одновременно — это ожидаемое, а не
ошибочное поведение.

## 19d.4. ParticipantEligibilityPolicy

Версионируемая, активируемая политика общей правоспособности участия
платформы, того же класса, что `GovernancePolicy` (19b.2) и
`DisclosurePolicy` (19a.3).

### Поля

- `policy_id`, `policy_version`.
- `status` — `draft` / `active` / `superseded`.
- `scope_type`, `scope_id` — nullable, непрозрачная ссылка.
- `effective_from`, `effective_until` — nullable.
- `adopted_by_decision_id` — **не nullable**: ссылка на утверждённую
  `GovernanceDecision` (19d.7).
- `age_thresholds` — список `{action_code, minimum_age, maximum_age}`.
- `citizenship_conditions`, `residence_conditions` — списки
  структурированных условий.
- `exemptions` — список структурированных исключений.
- `transitional_rules` — структурированные переходные правила, никогда
  не применяются неявно.
- `supersedes_policy_id` — nullable; исправление — всегда новая версия.
- `signed_policy_digest_reference`, `transparency_log_commitment_reference`
  — оба **не nullable** при `status = active` (19d.7).

### Статусы и переходы

`draft → active` (только при выполненных условиях 19d.7); `active →
superseded` (не более одной активной версии на `(scope_type, scope_id)`
одновременно). Возврат к `draft` невозможен.

### Владелец

`eligibility-service` (раздел 22).

## 19d.5. ProcessEligibilityPolicy

Версионируемая политика, параметризующая избирательную/процессную
правоспособность для конкретного процесса — никогда не одно постоянное
свойство человека.

### Поля

- `policy_id`, `policy_version`, `status` — как 19d.4.
- `process_type` — открытая строка; не менее девяти категорий:
  `bundestag_election`, `european_parliament_election_de`,
  `land_election`, `municipal_district_election`,
  `epd_public_consultation`, `epd_participant_poll`, `epd_member_vote`,
  `epd_party_office_election`, `epd_public_candidate_nomination`.
- `jurisdiction`, `scope_type`, `scope_id` — открытые/непрозрачные.
- `eligible_citizenship_set` — список кодов ISO 3166-1 либо ссылка на
  правило гражданства.
- `residence_rule`, `habitual_residence_rule`, `minimum_age`.
- `active_electoral_eligibility_rule`, `passive_electoral_eligibility_rule`.
- `party_internal_voting_rule`, `party_office_candidacy_rule` —
  nullable для непартийных `process_type`.
- `effective_from`, `effective_until`, `legal_basis` (иллюстративная
  ссылка, никогда не фиксированное значение), `adopted_by`,
  `supersedes_policy_id`.
- `signed_policy_digest_reference`, `transparency_log_commitment_reference`
  — как 19d.4.

### Дополнительные поля — правовой эффект и формальное подтверждение (19d.12)

- `decision_effect` — enum, не менее: `advisory`, `politically_binding`,
  `internally_binding`, `legally_final`, `requires_formal_confirmation`.
- `formal_confirmation_required` — boolean.
- `formal_confirmation_authority` — открытая ссылка, непрозрачная.
- `secret_ballot_required` — boolean.
- `permitted_participation_mode` — открытая строка/множество; никогда
  не универсальное правило физического присутствия.
- `required_assurance_level` — nullable ссылка на `AssuranceRequirement`
  (19d.8).
- `accessibility_profile` — открытая ссылка; детализация отложена
  (19d.18).

**Инвариант:** ровно одна `active` версия на `(process_type,
jurisdiction, scope_type, scope_id)` на данную `effective_date`,
разрешается заново при каждой оценке, никогда не кешируется как
постоянный факт. Ни одна дата вступления в силу текущего результата
голосования по умолчанию не считается юридически окончательной.

### Владелец

`eligibility-service` (раздел 22).

## 19d.6. PartyMembershipEligibilityPolicy

Разделяет поля и жизненный цикл с `ParticipantEligibilityPolicy`
(19d.4: `policy_id`, `policy_version`, `status`, `scope_type`,
`scope_id`, `effective_from`, `effective_until`,
`adopted_by_decision_id`, `age_thresholds`, `citizenship_conditions`,
`residence_conditions`, `exemptions`, `transitional_rules`,
`supersedes_policy_id`, `signed_policy_digest_reference`,
`transparency_log_commitment_reference`), и дополнительно:

- `incompatibility_rules` — список значений `conflict_type` (19d.11).
- `membership_duration_rules` — nullable.

### Владелец

`membership-service` (раздел 22).

## 19d.7. Критическая политика — активация, многостороннее утверждение, заморозка версии

`ParticipantEligibilityPolicy` (19d.4), `ProcessEligibilityPolicy`
(19d.5), `PartyMembershipEligibilityPolicy` (19d.6) и
`StepUpAuthenticationRequirement` (19d.8) — каждая классифицируется как
**критическая политика**. Переход любой из них в `active` требует
одновременно и независимо всех четырёх условий; отсутствие любого
одного — fail-closed отказ активации:

1. Утверждённая, `approved` `GovernanceDecision`
   (`adopted_by_decision_id`/`adopted_by`).
2. `multi_person_approval_met = true` — новое булево значение,
   возвращаемое расширенным `governance-service`-чтением
   `verify_decision_authorizes_policy_activation` (сконфигурированный
   минимум различных утверждающих акторов; сам список утверждающих
   вызывающей стороне не передаётся).
3. `signed_policy_digest_reference` заполнена — ссылка на
   криптографическую подпись содержимого версии политики.
4. `transparency_log_commitment_reference` заполнена — ссылка на
   публичную фиксацию через уже существующий механизм Transparency
   Context (`PublicLedgerEntry`/`AuditExportPackage`, 19a) — новая
   инфраструктура публикации не вводится.

**Заморозка версии (расширяет CT-00-10):** активная версия критической
политики, уже использованная активным процессом, не может быть
заменена, пока этот процесс не достигнет терминального состояния —
тот же принцип, что заморозка `EligibilityRule` при открытии
голосования (9.1). Факт "используется активным процессом" — производный,
вычисляемый на момент проверки; отдельное хранимое поле "заморожено"
не вводится.

## 19d.8. StepUpAuthenticationRequirement и AuthenticationContext

Пять раздельных, никогда не взаимозаменяемых понятий: идентификационная
уверенность (`identity_assurance_level`, `IdentityRecord`, 19d.2);
аутентификационная уверенность (`authentication_assurance_level`,
`AuthenticationContext`, ниже); актуальность атрибута
(`attribute_verification_level`/`attribute_verified_at`/
`attribute_valid_until`, `IdentityRecord`, 19d.2, для конкретного
атрибута); время и метод аутентификации сессии
(`session_authenticated_at`/`authentication_method`,
`AuthenticationContext`); ссылка на провайдера
(`AuthenticationContext.provider_reference`, отдельно от
`IdentityRecord.provider_reference`).

### AuthenticationContext (новая сущность)

- `authentication_context_id`, `account_id`.
- `authentication_method` — открытая строка.
- `authentication_assurance_level` — `none`/`low`/`substantial`/`high`.
- `session_authenticated_at`, `provider_reference`.
- `step_up_completed_at` — nullable.

Владелец: `identity-service`.

### StepUpAuthenticationRequirement (новая сущность, критическая политика)

- `requirement_id`, `requirement_version`, `status` (`draft`/`active`/
  `superseded`).
- `action_code` — открытая строка.
- `required_authentication_context`.
- `assurance_requirement` — встроенный `AssuranceRequirement`:
  `required_identity_assurance_level`,
  `required_authentication_assurance_level`,
  `required_attribute_freshness` (nullable).
- `fresh_authentication_required` — boolean.
- `maximum_authentication_age` — nullable.
- `reauthentication_reason` — reason code.
- `effective_from`, `effective_until`, `supersedes_requirement_id`.
- `signed_policy_digest_reference`, `transparency_log_commitment_reference`
  (19d.7 — тот же четырёхшаговый gate).

**Оценка, fail-closed:** требование удовлетворено только если
аутентификационная уверенность, идентификационная уверенность,
свежесть сессии (где применимо) и свежесть атрибута (где применимо)
выполняются **все одновременно**; ни одно "или"-условие не допускается.
Отсутствующий, истёкший или неразрешимый `AuthenticationContext` —
fail-closed отказ, никогда не разрешение по умолчанию.

Владелец: `eligibility-service`.

## 19d.9. MembershipApplication; `Membership` (8.3) без изменений

**Двухэтапный процесс, обязателен без исключений:**
`Membership.membership_status` (8.3) никогда не переходит напрямую из
состояния заявки в `active` как автоматический результат оценки
политики.

- **Этап A — формальная оценка правоспособности.** `membership-service`
  оценивает заявителя по текущей активной
  `PartyMembershipEligibilityPolicy`. Положительный результат этапа A
  сам по себе никогда не создаёт и не активирует запись `Membership`.
- **Этап B — авторизованное человеческое решение.** Запись `Membership`
  достигает `active` только после явного, утверждённого решения,
  несущего: ссылку на решающий орган/актора, версию политики, по
  которой был пройден этап A, `reason_code`, `decided_at` и ссылку на
  `AuditEvent`.

### MembershipApplication (новая сущность)

- `membership_application_id`, `subject_reference`.
- `status` — шесть значений: `application_pending`, `eligibility_review`,
  `human_decision_pending`, `approved`, `rejected`, `activated`.
- Поля, необходимые для отражения этапов A/B: ссылка на решающий
  орган/актора, применённую `policy_version`, `reason_code`,
  `decided_at`, ссылку на `AuditEvent`.
- `supersedes_membership_application_id` — nullable; исправление —
  всегда новая запись, никогда не переписывание существующей.

**Обязательное правило:** ни один код не вправе установить
`Membership.membership_status = active`, кроме как шагом `activated`,
следующим за зафиксированным `approved` `MembershipApplication`. Тот же
двухэтапный принцип симметрично применяется к приостановке,
прекращению/исключению и восстановлению — ни одна автоматизированная
система не вправе окончательно принять, отклонить, приостановить или
исключить человека без человеческого решения (19d.16).

**`Membership` (8.3) не изменяется настоящим разделом:** все восемь
существующих полей, семь существующих значений `membership_status`
(`application_pending`, `verification_pending`, `active`, `suspended`,
`terminated`, `rejected`, `expired`) и владелец остаются без изменений
— ничего не удалено и не переопределено, в соответствии с
принципом «только аддитивные изменения» minor-версии канона (раздел
25). `MembershipApplication` — самостоятельная, независимо
версионируемая сущность, владеющая переходным (pre-admission)
жизненным циклом; она не переопределяет и не заменяет ни одно
хранимое значение `Membership.membership_status`. Практически, при
реализации настоящего раздела в будущем пакете, переход
`Membership.membership_status` в `active`/`suspended`/`terminated`/
`expired` управляется исключительно через `MembershipApplication` и
симметричные ей решения этапа B; значения `application_pending`,
`verification_pending` и `rejected` остаются частью хранимого enum
`Membership.membership_status` для обратной совместимости, но не
получают новой семантики и не обязательны к производству новой
реализацией.

### Владелец

`membership-service`.

## 19d.10. AffiliationDeclaration

### Поля

- `affiliation_declaration_id`, `subject_reference`.
- `affiliation_type` — `other_party_membership`,
  `political_association_membership`, `public_office`,
  `elected_office`, `lobbying_or_interest_representation`,
  `organizational_leadership_or_employment`,
  `declared_incompatible_organization`.
- `declared_reference` — непрозрачная ссылка, никогда свободный текст
  названия организации на уровне схемы.
- `declared_at`.
- `status` — `draft` / `submitted` / `under_review` / `acknowledged` /
  `superseded` / `withdrawn`.
- `supersedes_declaration_id` — nullable.
- `valid_from` — собственное фактическое начало действия аффилиации,
  отдельно от `declared_at`.
- `valid_until` — nullable; собственное фактическое окончание, если
  известно.
- `verification_status` — `declared` / `verified` / `disputed` /
  `unverifiable`.
- `verified_at` — nullable.
- `verified_by` — nullable, непрозрачная ссылка на `RoleAssignment`;
  никогда не сам заявитель.

Декларации целевые — служат исключительно для `ConflictAssessment`,
никогда не становятся общей системой политического профилирования.

### Владелец

`membership-service`.

## 19d.11. ConflictAssessment

### Поля

- `conflict_assessment_id`, `subject_reference`.
- `affiliation_declaration_id` — nullable.
- `conflict_type` — `dual_party_membership`,
  `political_association_conflict`, `public_office_incompatibility`,
  `lobbying_role_incompatibility`, `organizational_affiliation_conflict`,
  `declared_incompatible_organization`.
- `incompatibility_level` — `none` / `disclosed_no_conflict` /
  `conditional_restriction` / `incompatible`.
- `status` — `pending` / `under_review` / `resolved_no_conflict` /
  `resolved_conditional` / `resolved_incompatible` / `appealed` /
  `overturned` / `expired_reevaluation_due`.
- `reason_codes`, `evidence_references` (непрозрачные).
- `reviewed_by_role_reference` — непрозрачная ссылка на `RoleAssignment`.
- `decision_authority_reference` — nullable ссылка на
  `GovernanceDecision`, обязательна для `resolved_incompatible`.
- `decided_at`, `supersedes_conflict_assessment_id`,
  `re_evaluation_due_at` — все nullable, где применимо.

Рецензент, проверяющий `decision_authority_reference`, никогда не
совпадает с актором, подавшим соответствующую `AffiliationDeclaration`.

### Владелец

`membership-service`.

## 19d.12. DigitalDecision / AssemblyDecision — правовой эффект и формальное подтверждение

Ни один результат цифрового участия или голосования не считается
юридически окончательным по умолчанию. Где `ProcessEligibilityPolicy.
formal_confirmation_required = true`, применяется отдельный,
явный жизненный цикл, никогда не сворачиваемый в сам цифровой
результат:

### DigitalDecision (новая сущность)

- `digital_decision_id`, `process_reference` (непрозрачная).
- `digital_result`.
- `decision_effect` — копируется неизменно из применимой
  `ProcessEligibilityPolicy`.
- `formal_confirmation_required` — boolean, копируется аналогично.
- `status` — `final` / `formal_confirmation_required`.
- `recorded_at`.

### AssemblyDecision (новая сущность; создаётся только когда `DigitalDecision.status = formal_confirmation_required`)

- `assembly_decision_id`, `digital_decision_id`.
- `confirming_authority` — копируется из `formal_confirmation_authority`.
- `legal_basis`, `confirmation_deadline`.
- `protocol_or_evidence_reference` — непрозрачная.
- `final_legal_decision`.
- `divergence_explanation` — nullable; **обязательна**, если
  `final_legal_decision` расходится с `digital_result`.
- `status` — `pending` / `confirmed` / `rejected` /
  `returned_for_revision`.
- `decided_at`.

**Жизненный цикл:** `DigitalDecision` (`formal_confirmation_required`)
→ `AssemblyDecision` (`pending`) → `AssemblyDecision` (`confirmed` /
`rejected` / `returned_for_revision`). `DigitalDecision`, чей
`decision_effect` не требует формального подтверждения, достигает
`status = final` напрямую, без создания `AssemblyDecision`. Истёкший
`confirmation_deadline` никогда не завершает или не переводит
результат автоматически — молчание никогда не считается одобрением
(INV-10). Расхождение между `final_legal_decision` и `digital_result`
без заполненного `divergence_explanation` отклоняется валидацией.

### Владелец

`eligibility-service`.

## 19d.13. ParticipationRightsProfile — внутренняя, невладеемая производная модель

**Внутренняя, неавторитетная, никогда не хранимая производная модель
чтения** (тот же приём стоимость-vs-хранимого разделения, что и
`FinalityStatus`/`DisclosureStatus`). Служит исключительно для
человеко-ориентированного отображения ("что я сейчас могу"); **никогда
не является механизмом, разрешающим или запрещающим действие.**

### Состав (вычисляется по запросу, никогда не хранится)

- `subject_reference`, `evaluated_at`.
- `can_read_public`, `can_discuss`, `can_create_initiative`,
  `can_support_initiative`, `can_join_civic_consultation` —
  вычисляются `eligibility-service`.
- `can_apply_for_party_membership`, `can_vote_as_party_member`,
  `can_stand_for_party_office` — вычисляются `membership-service` из
  `Membership.membership_status`/`PartyMembershipEligibilityPolicy`,
  предоставляются `eligibility-service` только как
  `required_membership_status_met`/`membership_duration_requirement_met`.
- `can_hold_special_role` — читается без изменений из
  `RoleAssignment` (`governance-service`).

**Единственно допустимые механизмы авторизации действия (19d.14) —
никогда чтение и ветвление по настоящей модели.** Ни один сервис,
frontend или иной потребитель не вправе читать
`ParticipationRightsProfile` и принимать решение о разрешении действия
на основе его полей.

### Владелец

Не имеет отдельного владельца — составная производная модель, не
самостоятельная хранимая сущность (раздел 22).

## 19d.14. Внешняя авторизация — atomic capability check или scoped capability token, исключительно

Любая проверка полномочия на действие в границах настоящего раздела и
за ними, где участвует хотя бы одна из его сущностей, использует ровно
один из двух механизмов:

1. **Atomic capability check** — узкое, синхронное,
   специально-назначенное чтение, возвращающее одно булево значение
   (либо малый закрытый набор булевых значений и reason codes) ровно
   на один вопрос авторизации для ровно одного действия — тот же
   приём, что уже установлен узкими чтениями раздела 5 (в
   реализационном соглашении) и `verify_role_assignment_for_action`
   (19b.1)/`verify_decision_authorizes_policy_activation` (19d.7).
2. **Single-purpose scoped capability token** — существующая
   `ParticipationCredential` (10.1), ограниченная ровно одним
   действием или процессом, предъявляемая и проверяемая в момент
   использования.

Третий механизм не допускается. В частности, чтение
`ParticipationRightsProfile` (19d.13) и ветвление по его полям **не
является допустимым механизмом авторизации** ни при каких
обстоятельствах.

## 19d.15. Appeal — полиморфная целевая ссылка (документальное уточнение)

`Appeal` (14.3) не получает новых полей, статусов или изменений
владельца настоящим разделом. `Appeal.decision_id` — полиморфная
целевая ссылка: помимо уже подразумеваемой ссылки на
`ModerationDecision`, она может указывать на
`ConflictAssessment.conflict_assessment_id` или
`MembershipApplication.membership_application_id`, а также на любой
дальнейший обжалуемый тип решения, который настоящий или будущий
раздел вводит — это **резервный принцип по умолчанию**, а не
исключение только для двух названных сущностей. Отдельная,
специализированная сущность апелляции для нового типа решения
вводится только там, где отдельный ADR, тем же стандартом прямой
проверки полей, что применён здесь, доказывает недостаточность формы
`Appeal`. `Appeal`'s собственные статусы и правило «апелляцию не
должен окончательно рассматривать автор исходного решения» переносятся
без изменения смысла на `ConflictAssessment`/`MembershipApplication`:
рецензент апелляции по `ConflictAssessment` структурно не совпадает с
`ConflictAssessment.reviewed_by_role_reference`.

## 19d.16. Жёсткий инвариант человеческого контроля

**Семь категорий, ни одна не достижима исключительно автоматизированной
оценкой политики:** приём в члены (`MembershipApplication → approved`/
`activated`); отказ (`rejected`); приостановка
(`Membership.membership_status → suspended`); прекращение/исключение
(`→ terminated`); установление несовместимости
(`ConflictAssessment.status → resolved_incompatible`); восстановление
прав членства; и, как седьмая, открытая категория, **лишение любого
фундаментального права члена, независимо от способа, которым оно
произведено.** Ни один программный путь не достигает ни одного из этих
семи исходов исключительно из булева значения оценки политики,
истечения времени ожидания или отсутствующего рецензента,
интерпретируемого как решение — молчание никогда не считается
одобрением. Настоящий инвариант связывает по **эффекту, а не по
названию**: новый, ещё не поименованный настоящим разделом тип исхода,
который по своему эффекту лишает члена фундаментального права,
покрывается этим инвариантом так же, как если бы он был явно перечислен
выше. Оценка политики может только рекомендовать, отметить или
вычислить входное значение; авторизованное человеческое решение,
ссылающееся на реальную `GovernanceDecision`/
`decision_authority_reference` там, где это требуется, всегда остаётся
единственной и непосредственной причиной любого из этих семи исходов.

## 19d.17. Отложенные будущие концепции — доменные псевдонимы, анти-корреляция, криптографический протокол, будущее требование к ИИ-резюме

Настоящий подраздел **называет**, но не определяет как полностью
оснащённые канонические сущности, три концепции, чья конкретная
реализация закреплена за будущими пакетами:

- `DomainPseudonymReference` — требование раздельных, доменно-
  ограниченных псевдонимных идентификаторов как минимум для пяти
  доменов (участник, членство, правоспособность, выдача credential,
  голосование); ни один универсальный, постоянный, единый
  идентификатор личности не вычисляется и не переиспользуется через
  всю платформу. Алгоритм вывода, ключ и реализация не выбираются
  настоящим разделом.
- `AntiCorrelationInvariant` — уточняет уже существующие
  INV-01/CT-00-08/CT-00-09 явным, поимённым, fail-closed перечнем
  запрещённых векторов корреляции между слоем
  идентификации/выдачи credential и анонимным участием или подачей
  голоса: общие идентификаторы пользователя/запроса/трассировки/
  аналитики; точное сопоставление по времени; сохранённые IP-адреса в
  домене бюллетеня; браузерный fingerprinting; общие сессионные cookie
  между идентифицирующим контекстом и анонимной точкой; корреляция по
  порядку сообщений; журналы reverse-proxy, содержащие
  идентифицирующие метаданные. Это структурный, fail-closed инвариант,
  не рекомендация.
- `CryptographicProtocolProfile` — абстрактная, версионируемая
  концепция выбора криптографического протокола; ни Blind Signatures,
  ни ElGamal, ни гомоморфное шифрование, ни mixnet, ни zero-knowledge
  proofs не фиксируются настоящим разделом. Любое будущее конкретное
  принятие протокола потребует как минимум: формальной модели угроз;
  аудированного протокола; внешней криптографической экспертизы;
  дизайна управления ключами; защиты от replay; **временнóй
  неразличимости** (протокол не должен структурно допускать
  корреляцию по времени); **транспортной неразличимости** (сетевой
  транспорт не должен допускать связывание через переиспользование
  соединения, возобновление TLS-сессии или корреляцию по IP);
  сохраняющего приватность механизма отзыва (событие отзыва не должно
  само по себе раскрывать, какой credential или какое лицо отозвано);
  документированной процедуры проверки.

Ни `eligibility-service`, ни `membership-service` не вводят
собственного анонимного участия, выдачи анонимного credential или
криптографического протокола — все три концепции выше остаются
идентифицированными, но не реализованными настоящим разделом,
закреплены за будущим **Identity & Authentication Security pack** и
будущим **Verifiable Voting Cryptography pack** соответственно (раздел
26; не авторизуются ни настоящим разделом, ни ADR-031 к реализации).

**Будущее требование к ИИ-содействующим резюме (не изменяет раздел 17
или 19c).** Настоящий раздел не вводит и не расширяет
`AIProcessingRecord` (17.1, 19c) — ни одно его поле не изменяется.
Тем не менее, зафиксировано как одобренное будущее архитектурное
требование: любое существенное (consequential) ИИ-сгенерированное
резюме, где бы на платформе оно ни было впоследствии введено, обязано
поддерживать: (1) детерминированное сопоставление источников — от
каждого значимого сегмента резюме к его исходным ссылкам на
`Contribution`; (2) метаданные покрытия (какая доля/какие части
исходного материала действительно отражены резюме); (3) явный статус
человеческой проверки; (4) неизменяемую связь с `AIProcessingRecord`.
Реализация, включая любое соответствующее добавление поля к
`AIProcessingRecord`, остаётся отложенной до будущего пакета поправок
к ИИ-обработке (расширение PACK-06) и не авторизуется, не
разрабатывается и не выполняется настоящим разделом.

## 19d.18. Структурное разделение с другими контурами

`ParticipantEligibilityPolicy`, `ProcessEligibilityPolicy`,
`StepUpAuthenticationRequirement`, `DigitalDecision`, `AssemblyDecision`,
`PartyMembershipEligibilityPolicy`, `AffiliationDeclaration`,
`ConflictAssessment`, `MembershipApplication` и `AuthenticationContext`
не имеют ни одного read- или write-ребра к `voting-service`,
`tally-service` или `VoteEnvelope` — ни прямо, ни через
`ParticipationRightsProfile`. Ни `eligibility-service`, ни
`membership-service` не читают и не изменяют `PublicLedgerEntry`,
`AuditExportPackage`, `DisclosurePolicy`, `LobbyLogEntry` (19a),
`GovernancePolicy`, `TechnicalChallenge` (19b, помимо уже названного
узкого чтения `GovernanceDecision`) или `AIProcessingRecord` (17, 19c)
напрямую — единственная связь с Governance Context — через уже
названные узкие чтения (`verify_decision_authorizes_policy_activation`
и эквивалент для `decision_authority_reference`). Emergency/Crisis
Override (раздел 19) не входит в настоящий раздел и не расширяется им.

---

# 19e. Организация и региональная авторизация — расширение (Organization & Regional Scope Context)

Добавлено версией канона 0.7.0 (ADR-032 через ADR-037, приняты
2026-07-25) и реализует полное каноническое определение контура 5.4
(Organization Context) — ранее обозначенного канoном 0.1.0 лишь как
раздел ответственности без сущностей — а также расширяет уже
существующие `Organization` (8.1) и подтверждает `CivicSpace` (8.2) без
изменений. Раздел вставлен под номером 19e, между разделами 19d
(Participation & Membership Context) и 20 (Канонический каталог
событий), чтобы не переносить нумерацию уже существующих разделов
20–30 — тот же приём, использованный при добавлении разделов 19a, 19b,
19c и 19d. Настоящий раздел закрывает канонический пробел, явно
зафиксированный `docs/handover/PACK-07-SPEC-FINAL.md` разделом 11
("Ни один сервис не вправе предполагать существование живой сущности
`Organization` или `CivicSpace` до определения PACK-08") и
`docs/packs/PACK-08-SPECIFICATION.md`/ADR-032 через ADR-036
(специфицированы и приняты 2026-07-25, до настоящего канонического
раунда).

Новые и расширенные канонические сущности настоящего раздела
физически закреплены за новым `organization-service` (владелец:
Organization Service, ADR-032) — сервис, код которого настоящим
разделом **не создаётся**: это канонический, а не реализационный
раунд (19e.23). `RoleAssignment` (8.4, Governance Context, владелец
Permission / Role Service / `governance-service`) не изменяется ни в
одном поле, статусе или владельце — настоящий раздел лишь фиксирует
обязательную классификацию его поля `scope_id` (19e.19). `Membership`
(8.3, владелец Membership Service / `membership-service`) не
изменяется ни в одном поле, статусе или владельце. Ни одно поле,
статус, событие или запрет ни одного другого контура — Governance
Context (19b), Transparency Context (19a), AI Processing Context
(19c), Participation & Membership Context (19d), Emergency/Crisis
Override (раздел 19) — не изменяется настоящим разделом (19e.22).

## 19e.1. Обзор и перечень сущностей

- **`Organization`** (8.1, расширена настоящим разделом — 19e.3, 19e.4).
- **`OrganizationalUnit`** (новая, 19e.5).
- **`CivicSpace`** (8.2, без изменений — 19e.6).
- **`OrganizationalRelation`** (новая, 19e.7).
- **`OrganizationalHierarchyOverlapPolicy`** (новая, 19e.8).
- **`OrganizationalInheritancePolicy`** (новая, 19e.13).
- **`OrganizationalAuthority`** (новая, 19e.15).
- **`OrganizationalScope`** (новый переиспользуемый объект-значение, не
  отдельно владеемая сущность — 19e.11, тот же принцип, что уже
  применён к `RedactionManifest`, 19c.4, и `AIDisclosurePackage`,
  19c.6).

Все восемь — за исключением `RoleAssignment`, который остаётся
исключительно владением Governance Context — физически реализуются
`organization-service` (ADR-032). Настоящий раздел определяет только
каноническую модель; ни один из перечисленных пунктов не авторизует
код, схему, событие транспорта или API этого сервиса (19e.23).

## 19e.2. Разделение понятий — Organization, Jurisdiction, CivicSpace, локальный для процесса Scope

Настоящий раздел канонически фиксирует четыре взаимно
невзаимозаменяемые понятия (ADR-035; `docs/packs/PACK-08-SPECIFICATION.md`
раздел 2/4):

- **Organization** — управляемый узел организационного домена платформы
  (Bund-уровневая партия, Landesverband, Kreisverband, нетерриториальный
  рабочий орган, специальный или межрегиональный узел). Единственный
  владелец — `organization-service` (ADR-032). Идентифицируется
  `organization_id` (8.1, имя поля не изменяется).
- **Jurisdiction** — географический или юридический факт (например,
  «DE», «Berlin», наднациональный орган), внешний по отношению к
  собственной организационной структуре платформы, уже моделируемый
  как открытая строка на `ProcessEligibilityPolicy.jurisdiction` (19d.5,
  ADR-028). Jurisdiction никогда не является узлом `Organization`, и ни
  один узел `Organization` не считается «являющимся» юрисдикцией лишь
  потому, что его название на неё похоже.
- **CivicSpace** — локальная для процесса область участия, вложенная в
  `Organization` (8.2, без изменений — 19e.6).
- **Scope, локальный для процесса** — непрозрачная пара
  `scope_type`/`scope_id`, уже используемая разнородно
  `credential-service`, `delegation-service`, `voting-service`,
  `initiative-service`, `eligibility-service` и `membership-service` для
  обозначения «конкретного экземпляра объекта, к которому применяется
  данная проверка возможности или политика» — сегодня, в большинстве
  этих сервисов, **не** являющейся организационной ссылкой.

**Обязательное правило.** Organization, Jurisdiction, CivicSpace и
локальный для процесса Scope могут ссылаться друг на друга (значение
`OrganizationalScope`, 19e.11, может указывать на `Organization`;
`ProcessEligibilityPolicy` может нести одновременно `jurisdiction` и,
аддитивно, ссылку `OrganizationalScope`), но ни один потребитель не
вправе трактовать одно из четырёх понятий как замену другого, и ни
одно из следующих полей не подлежит молчаливой переинтерпретации между
доменами: `organization_id`, `jurisdiction`, `region_code`, `scope_id`,
`civic_space_id`. Классификация конкретных полей — предмет ADR-035 и
`docs/packs/PACK-08-MIGRATION-MATRIX.md`, не настоящего раздела; canon
фиксирует только запрет молчаливой переинтерпретации как таковой.

## 19e.3. `Organization` — дополнительные поля

`Organization` (8.1) сохраняет все шесть существующих полей без
изменений (`organization_id`, `name`, `legal_operator`,
`organization_type`, `status`, `default_policy_version`) и владельца
(Organization Service). Настоящий раздел добавляет шесть новых полей:

- `organization_profile` — открытая, расширяемая таксономия (не
  закрытый enum), не менее: `bund`, `landesverband`, `kreisverband`,
  `bezirksverband`, `ortsverband`, `ortsgruppe`, `non_territorial_unit`,
  `special_unit`, `cross_regional_unit`, `working_group` — расширяется
  на уровне репозитория, никогда правкой канона (тот же приём, что уже
  применён к `identity_scheme`, 19d.2). Ни один профиль не занимает
  фиксированный уровень дерева фиксированной глубины.
- `parent_reference` — nullable; **не авторитетен** (19e.4).
- `effective_from`.
- `effective_until` — nullable.
- `dissolved_at` — nullable.
- `successor_reference` — nullable, непрозрачная ссылка; сама по себе
  никогда не подразумевает передачи прав (19e.10).

## 19e.4. `parent_reference` — неавторитетная проекция

Канонизируется (владелец: `docs/packs/PACK-08-OPEN-DECISIONS.md`
владелец-решение, зафиксированное в ADR-033):

- `parent_reference` **не авторитетен**.
- `OrganizationalRelation` (19e.7) — единственный авторитетный источник
  родительских/иерархических связей.
- `parent_reference` существует не иначе как производная read-модель
  или совместимостная проекция; он никогда не создаётся и не
  изменяется отдельной командой записи.
- Тесты согласованности обязаны доказывать корректность проекции
  относительно текущего активного набора иерархических
  `OrganizationalRelation` (будущая реализационная обязанность,
  раздел 27).
- `parent_reference` может отсутствовать вовсе там, где его сохранение
  рискует стать вторым источником истины (например, когда узел имеет
  более одной конкурентной родительской связи, разрешённой 19e.7).

## 19e.5. `OrganizationalUnit`

Новая сущность — более лёгкий узел для подчинённых структур, не
являющихся полноценной `Organization` в юридически-уставном смысле
(тематическая рабочая группа, временный региональный рабочий орган), но
нуждающихся в тех же scope-, дате-эффективности- и
relationship-механизмах. Владелец — `organization-service`, тот же, что
`Organization`; смоделирована как специализация `Organization` через
`organization_profile` (19e.3), не как параллельная иерархия — то же
физическое семейство таблиц, та же relationship- (19e.7) и scope-
(19e.11/19e.12) машинерия.

## 19e.6. `CivicSpace` — без изменений

`CivicSpace` (8.2) сохраняет все семь полей (`space_id`,
`organization_id`, `name`, `space_type`, `visibility`,
`participation_policy_id`, `status`), пять статусов и владельца
(Organization Service) без изменений. Первичный ключ остаётся
`space_id`; настоящий раздел не переименовывает его в `civic_space_id`
— последнее остаётся лишь рекомендацией по именованию для будущих
внешних ссылочных полей (`docs/packs/PACK-08-MIGRATION-MATRIX.md`
раздел 2.11), не канонической правкой.

## 19e.7. `OrganizationalRelation` — множественные типизированные направленные графы

Новая каноническая сущность — типизированное, версионированное,
эффективно-датированное ребро, связывающее два узла
`Organization`/`OrganizationalUnit`.

### Поля

```text
OrganizationalRelation:
  relation_id
  relation_version
  relation_type            — parent_of | subordinate_to | affiliated_with
                              | successor_of | merged_into | split_from
                              | temporary_supervision_by | operates_within
                              | participates_in (открытый список внутри
                              категории; новая категория требует ADR)
  relation_category        — hierarchy | continuity | cooperation
                              (производится из relation_type, никогда не
                              задаётся отдельно)
  source_organization_id
  target_organization_id
  status                   — draft | active | superseded | ended
  valid_from
  valid_until               — nullable
  recorded_at
  supersedes_relation_id    — nullable
  authorizing_decision_reference
```

### Принятое решение (владелец-решение, раунд коррекции PACK-08,
подтверждено настоящим каноническим раундом)

- Организационные отношения образуют **множественные типизированные
  направленные графы**; простое дерево не авторитетно.
- Семантика отношения — **специфична для типа отношения**.
- Циклы **запрещены** для отношений категории containment/subordination
  (`parent_of`, `subordinate_to`), без исключений.
- Нехиерархические типы отношений (категория cooperation) могут
  допускать циклы **только там, где это явно определено** для данного
  типа отношения.
- Перекрывающиеся родительско-подобные отношения требуют либо разных
  типов отношения, либо явного разрешения политикой
  (`OrganizationalHierarchyOverlapPolicy`, 19e.8).
- Все отношения версионированы и эффективно-датированы (19e.9).

Три категории (`relation_category`, производная от `relation_type`):
**hierarchy** (`parent_of`, `subordinate_to` — ожидаемо древовидна для
большинства территориальных узлов, но не принудительно; узел может
иметь ноль родителей; более одного конкурентного родителя допустимо
только по `OrganizationalHierarchyOverlapPolicy`); **continuity**
(`successor_of`, `merged_into`, `split_from` — направленная,
только-добавляемая, историческая запись организационной
непрерывности; никогда не изменяется на месте; никогда не
интерпретируется как иерархическое ребро; сама по себе никогда не
подразумевает передачи прав или ролей, 19e.10); **cooperation**
(`affiliated_with`, `temporary_supervision_by`, `operates_within`,
`participates_in` — общий направленный граф; взаимные `affiliated_with`
рёбра допустимы; цикло-свобода не является сквозным правилом для этой
категории, за исключением `temporary_supervision_by`, для которого узел
не может надзирать сам за собой, прямо или транзитивно).

## 19e.8. `OrganizationalHierarchyOverlapPolicy`

Новая каноническая, версионированная политика, владелец
`organization-service`. Определяет, когда более одного конкурентного
ребра одной hierarchy-категории (`parent_of`/`subordinate_to`) может
одновременно существовать для одного узла — заменяет собой любую
неформальную «рассмотренную исключительную ситуацию» явной,
именованной, версионированной сущностью политики. Минимальные поля:
`policy_id`, `policy_version`, применимый(е) `relation_type`,
разрешение перекрытия (булево или структурированное условие),
`authorizing_decision_reference`, `valid_from`/`valid_until` (nullable),
`status` (`draft`/`active`/`superseded`). Точная схема валидации и
алгоритм проверки остаются реализационным решением (раздел 27); канон
фиксирует существование, владельца и обязательность этой сущности как
единственного источника разрешения перекрытия.

## 19e.9. Эффективное датирование

Канонизируется для `Organization`, `OrganizationalUnit`,
`OrganizationalRelation` и `OrganizationalAuthority` единообразно:

- `valid_from` — обязательно.
- `valid_until` — nullable; отсутствие означает «всё ещё действует».
- `recorded_at` — момент фактической записи, отличный от `valid_from`
  (см. будущие даты ниже).
- `supersedes_*_id` — механизм исправления/версионирования; исправление
  — всегда новая версия, никогда не правка на месте.
- **Историческая опрашиваемость** — «каково было состояние на дату X»
  всегда отвечаемо фильтрацией каждой релевантной записи по окну
  `[valid_from, valid_until)`, покрывающему X, никогда не изменением
  или удалением прошлой записи.
- **Будущие даты** — `valid_from` может быть установлен в будущем;
  запись при этом уже существует и опрашиваема как запланированное
  будущее состояние, но не действует для целей scope-авторизации
  (19e.12) до наступления `valid_from`.
- **Валидация перекрытия** — для типов отношений, где более одного
  одновременно активного ребра было бы противоречивым, путь записи
  обязан отклонять перекрывающееся окно `[valid_from, valid_until)`
  против существующей активной записи того же конфликтующего вида;
  проверка **специфична для типа отношения** (19e.7), не единое сквозное
  правило.
- **Жёсткое правило**: текущее состояние никогда не должно
  перезаписывать историческую организационную истину.

## 19e.10. Реорганизация

Канонические правила для следующих рабочих процессов — каждый
отдельное, аудируемое, явно управляемое (governed) решение/событие,
никогда не выводимое автоматически из изменения статуса в другом
месте:

- **Создание** — новый узел `Organization`/`OrganizationalUnit`, статус
  `draft` изначально, требует `authorizing_decision_reference`.
- **Активация** — `draft → active`; требует того же управляемого
  человеческого решения, что и любой другой существенный переход
  (никогда не автоматически при создании).
- **Приостановка** — `active → restricted`; обратима, требует ссылку на
  решение и reason code.
- **Роспуск (dissolution)** — `active`/`restricted → archived`;
  `dissolved_at` фиксируется; необратим через этот рабочий процесс —
  распущенная организация никогда молчаливо не реактивируется, только
  новый узел, опционально связанный через `successor_of`, может
  продолжить её работу.
- **Слияние (merger)** — исходные узлы получают отношение
  `merged_into` категории continuity, нацеленное на один результирующий
  узел; каждый исходный узел распускается тем же управляемым решением.
- **Разделение (split)** — исходный узел получает одну или более
  `split_from` continuity-связей от результирующих узлов; собственный
  статус продолжения исходного узла — явное поле решения.
- **Организация-правопреемник (successor)** — отношение `successor_of`
  записывается как собственное явное управляемое решение с
  `authorizing_decision_reference`; `successor_reference` (19e.3)
  предшественника заполняется одновременно как удобство
  read-оптимизации, никогда как единственная запись факта.
- **Переименование** — аддитивное, версионированное изменение `name`;
  прежнее имя остаётся исторически опрашиваемым; переименование само по
  себе никогда не изменяет `organization_id`, отношения иерархии или
  назначения полномочий.
- **Территориальное переназначение** — изменение того, в какой
  родительский узел отчитывается `Organization`/`OrganizationalUnit`;
  записывается как новая версия hierarchy-категории
  `OrganizationalRelation` (старое отношение получает `valid_until`,
  новое — собственный `valid_from`), никогда не правка существующей
  записи на месте.

**Жёсткое правило (дословно из владелец-решения):** ни одно
полномочие, роль, право доступа или институциональное назначение не
переходит автоматически к слитой, разделённой или организации-
правопреемнику. Передача требует явного управляемого решения,
даты вступления в силу и записи аудита.

## 19e.11. `OrganizationalScope` — переиспользуемый объект-значение

Узкий, непрозрачный контракт scope-ссылки, получаемый другими сервисами,
когда им нужно спросить «находится ли это действие/запись внутри этой
организационной scope», не получая при этом граф `Organization`.
`OrganizationalScope`-значение всегда именует, к какому из четырёх
понятий раздела 19e.2 оно относится (`organization_scope` |
`jurisdiction_scope` | `civic_space_scope` | `process_scope`) — потребитель,
держащий `OrganizationalScope`, всегда может ответить «это ссылка на
organization scope, и если да, то на какую организацию» без
необходимости угадывать по одному лишь имени поля. Не является
отдельно владеемой сущностью — переиспользуемый объект-значение (тот же
принцип, что уже применён к `RedactionManifest`, 19c.4).

## 19e.12. Региональная авторизация scope — default-deny

**Каждое решение об авторизации региональной scope по умолчанию
отклоняется (default-deny).** Доступ предоставляется только одним из
следующих явных режимов, оцениваемых узким, атомарным, серверным
чтением (`check_regional_scope_access`, тот же приём, что уже применён
атомарной capability-проверкой ADR-027/19d.14):

1. **Точный scope (exact-scope)** — собственная `OrganizationalScope`-
   ссылка актора совпадает со scope целевой записи в точности.
2. **Scope предка (ancestor-scope)** — scope актора является
   hierarchy-предком scope цели, **и** каноническая, версионированная
   `OrganizationalInheritancePolicy` (19e.13) для соответствующей
   роли/действия это разрешает (никогда не предполагается лишь из
   иерархической позиции).
3. **Scope потомка (descendant-scope)** — симметрично пункту 2, для
   более редкого случая, когда scope-актору потомка нужен узкий доступ
   в запись предка; также никогда не предполагается по умолчанию.
4. **Явно делегированный межscope-доступ** — ограниченная по времени,
   с фиксацией цели запись делегирования, предоставляющая названному
   актору или роли конкретное межscope-полномочие.
5. **Временный надзор (temporary supervision)** — отношение
   `temporary_supervision_by` (19e.7), само эффективно-датированное и
   отзываемое, предоставляющее авторизованным акторам надзирающего узла
   узкое, целенаправленное окно доступа в scope надзираемого узла
   (19e.14).
6. **Институциональный надзор без подразумеваемого доступа к данным** —
   назначение `OrganizationalAuthority` (19e.15), чья
   `grants_procedural_authority` истинна, но `grants_data_access` ложна,
   не даёт доступа к чтению самим по себе титулом; любой доступ к
   данным, нужный надзорной роли, должен быть предоставлен явно через
   режимы 1–4, никогда не выводиться из титула надзора.

**Жёсткие правила:**

- Название роли **не является** доказательством полномочия.
- Позиция в иерархии **не является** доказательством полномочия.
- Frontend **никогда** не является источником авторизации.
- Потребляющие домены **могут** применять более строгие правила scope.
- Потребляющие домены **не могут** расширять полномочие, унаследованное
  от домена Organization & Regional Scope.
- Ни один универсальный администратор не может возникнуть через
  наследование scope.
- Межscope-доступ требует явной политики и записи аудита.

## 19e.13. `OrganizationalInheritancePolicy` — владение политикой наследования

Новая каноническая, версионированная, аудируемая сущность, владелец
`organization-service`, управляющая режимами наследования предка/потомка
(19e.12, режимы 2–3). Минимальные поля: `policy_id`, `policy_version`,
`role_code` или `action_code`, к которому применяется, `inheritance_mode`
(`ancestor` | `descendant` | `both`), `authorizing_decision_reference`,
`valid_from`/`valid_until` (nullable), `status`.

Канонизируется:

- Политика наследования принадлежит домену Organization & Regional
  Scope.
- Потребляющие домены могут применять более строгие правила.
- Потребляющие домены **не могут** расширять унаследованное полномочие.
- Правила наследования версионированы.
- Решения о наследовании аудируемы.
- Нижестоящие сервисы не могут самостоятельно выводить более широкое
  наследование.
- Frontend не может выводить или расширять наследование.
- Scope-заявление (scoped claim) обязано нести достаточный контекст для
  оценки версии политики и момента её действия.

## 19e.14. Временный надзор (temporary supervision)

Канонизируется, применительно к отношению `temporary_supervision_by`
(19e.7) и режиму 5 раздела 19e.12:

- `valid_from` и `valid_until` **обязательны**; бессрочный временный
  надзор **запрещён**.
- Максимальная длительность по умолчанию — **90 дней**.
- Продление требует нового управляемого решения и создаёт собственную
  новую запись аудита — никогда не молчаливое продление существующей
  записи.
- Более узкие юридические ограничения могут быть добавлены для
  конкретных организационных форм или юрисдикций (никогда не более
  широкие).

## 19e.15. `OrganizationalAuthority` — назначения институционального полномочия

Новая каноническая сущность, владелец `organization-service`, отдельная
от канонической `RoleAssignment` (8.4, Governance Context, без
изменений). `RoleAssignment` продолжает означать «системную/
governance-политическую роль»; `OrganizationalAuthority` означает
«институциональное, организационно-scope-ограниченное назначение».
Связь между ними — только через непрозрачную ссылку, никогда через
слияние сущностей или сервисов.

### Поля

```text
OrganizationalAuthority:
  authority_id
  authority_version
  role_code                     — dpo | election_board_member |
                                   election_officer | independent_auditor
                                   | finance_auditor | party_arbitrator |
                                   organizational_administrator (открытый
                                   список — 19e.16)
  scope                         — OrganizationalScope-ссылка (19e.11),
                                   именующая ровно один из
                                   organization_scope / jurisdiction_scope
                                   / civic_space_scope / process_scope,
                                   в зависимости от того, к чему
                                   применяется данное назначение
  appointing_authority_reference — непрозрачная ссылка на
                                   уполномоченный орган/решение;
                                   никогда не совпадает с назначаемым
                                   субъектом (19e.17)
  assigned_subject_reference     — непрозрачная ссылка на субъект,
                                   которому назначено полномочие
  valid_from
  valid_until                   — nullable
  status
  revocation_reason_reference    — обязательно, если статус отозван
  policy_version
  decision_reference
  audit_reference
```

*Примечание об именовании.* Запрос настоящего канонического раунда
описывает эти свойства также как `authority_type`,
`organization_scope`/`jurisdiction_scope`/`CivicSpace scope`/
`process scope` как отдельные поля. Настоящий раздел фиксирует
каноническое имя поля как `role_code` (а не `authority_type`) и единое
поле `scope` типа `OrganizationalScope` (а не четыре раздельных поля) —
в точном соответствии с уже принятой спецификацией
(`docs/packs/PACK-08-SPECIFICATION.md` раздел 9.1) — во избежание двух
разных канонических имён для одного и того же поля. `OrganizationalScope`
(19e.11) сама по себе именует, какое из четырёх понятий применяется, что
достигает того же эффекта, что и четыре раздельных поля, без их
дублирования.

Назначение может предоставлять: процедурное полномочие
(`grants_procedural_authority`); доступ к данным
(`grants_data_access`); оба; либо ни одного, до выдачи отдельной
возможности (capability) — независимые булевы поля, никогда не
выводимые исключительно из титула полномочия (19e.12, режим 6).

## 19e.16. Институциональные роли и минимальная базовая матрица несовместимости

Канонизируются как минимум семь именованных ролей:

- **Data Protection Officer (DPO)** — процедурное полномочие над
  реестром обработки и вопросами приватности в рамках scope.
- **Election board member / election officer** — процедурное
  полномочие над избирательными операциями в рамках scope; разные роли
  (совет действует коллективно, officer — индивидуально).
- **Independent auditor** — полномочие проверки/чтения, никогда
  полномочие записи над проверяемыми записями.
- **Finance auditor** — независимое ревизионное полномочие над
  финансовыми записями в рамках scope, структурно отделённое от
  полномочия подготовки/утверждения финансов.
- **Party arbitrator** — процедурное полномочие в рамках (отложенного)
  арбитражного процесса; настоящий раздел определяет только форму
  назначения полномочия, не саму процедуру.
- **Organizational administrator** — scope-ограниченное
  административное полномочие над одним узлом
  `Organization`/`OrganizationalUnit`; **никогда** платформенный
  администратор (см. запрет универсального администратора, 19e.12).

**Минимальная базовая матрица несовместимости** (дословно из
владелец-решения; минимальный базовый уровень, подлежащий юридическому
уточнению — уточнение может сделать её строже, никогда мягче):

1. `election officer` не может одновременно выступать `election auditor`
   для одного и того же процесса и scope.
2. `election board member` не может самостоятельно утвердить
   собственное назначение или отстранение.
3. `finance auditor` не может одновременно быть `finance administrator`
   для одной и той же организации и scope.
4. `independent auditor` не может проверять действия, которые он сам
   выполнил или утвердил.
5. `party arbitrator` не может участвовать в деле, где он занимает
   операционную роль в затронутой организации.
6. `organizational administrator` не может самостоятельно назначить
   себе институциональное полномочие.
7. Процедурная независимость `DPO` должна быть сохранена.
8. Ни одно лицо не может удовлетворять обеим сторонам действия с
   двойным контролем (dual-control).

## 19e.17. Жизненный цикл роли/полномочия

Канонизируется для `OrganizationalAuthority` (и, тем же правилом, для
`RoleAssignment`, scope-ограниченного `Organization`):

1. Полномочие не может начаться раньше существования организации.
2. Полномочие не может оставаться действительным после роспуска, если
   оно явно не мигрировано.
3. Слияние, разделение и правопреемство не передают полномочие
   автоматически.
4. Самостоятельное назначение запрещено.
5. Действие с двойным контролем не может быть завершено одним лицом.
6. Предложение и активация должны быть разделены там, где политика
   требует двойного контроля.
7. Истёкшее, отозванное или приостановленное полномочие не может быть
   использовано.
8. Глобальный или системный scope не подразумевает универсального
   администрирования.

## 19e.18. Минимизация идентичности — расширение

Сохраняет и расширяет уже существующее разделение идентичности
(INV-01; `DomainPseudonymReference`/`AntiCorrelationInvariant`, 19d.17).
Жёсткие правила:

1. Отсутствие глобального идентификатора пользователя.
2. Отсутствие нового междоменного графа идентичности.
3. Доменно-специфичные псевдонимные ссылки.
4. Отсутствие публичного каталога участников по умолчанию.
5. Отсутствие межрегионального каталога участников по умолчанию.
6. События не должны содержать излишних данных идентичности.
7. Ссылки на институциональное полномочие обязаны использовать
   минимально необходимую информацию идентичности.
8. Scope-авторизация не должна раскрывать несвязанную информацию о
   членстве или идентичности.

## 19e.19. `RoleAssignment.scope_id` — классификация для миграции scope

Настоящий раздел требует, чтобы каждый существующий `role_code` на
`RoleAssignment.scope_id` (8.4, без изменений полей/статусов/владельца)
был классифицирован в ровно одну из шести категорий:

1. Organization scope.
2. Jurisdiction scope.
3. CivicSpace scope.
4. Локальный для процесса (process-local) scope.
5. Global/system scope.
6. Недействительный/legacy неоднозначный (invalid/legacy ambiguous).

Правила:

- Молчаливая переинтерпретация запрещена.
- Неоднозначные роли (категория 6) остаются заблокированными для
  миграции (migration-blocked) — ни одна реализация не вправе связать
  их с `check_regional_scope_access` (19e.12) или иной scope-
  осведомлённой логикой до реклассификации.
- Реализация обязана включать явную таблицу миграции `role_code` до
  начала миграции данных.
- Роли global/system scope не создают универсального
  административного полномочия (19e.12, 19e.17.8).
- Текущий смысл данных должен оставаться исторически восстановимым —
  ни одна реклассификация не переписывает прошлые записи на месте.

Конкретное перечисление каждого существующего `role_code` — предмет
`docs/packs/PACK-08-MIGRATION-MATRIX.md` раздела 2.3 и будущего
реализационного раунда, не настоящего канонического текста (ADR-035).

## 19e.20. Канонические события — перекрёстная ссылка

Полный каталог событий настоящего раздела зафиксирован разделом 20.5
(расширен) — канонический владелец, минимальный/запрещённый payload,
время вступления в силу, время записи, ссылки на версию политики,
привязка к аудиту, ожидания идемпотентности и ограничения приватности
документированы там вместе с остальным каталогом событий Organization,
не дублируются здесь.

## 19e.21. Reason codes — перекрёстная ссылка

Десять reason code настоящего раздела зафиксированы разделом 24
(расширен): `ORGANIZATION_NOT_ACTIVE`, `ORGANIZATION_SCOPE_MISMATCH`,
`CROSS_SCOPE_ACCESS_DENIED`, `AUTHORITY_ASSIGNMENT_INVALID`,
`AUTHORITY_ROLE_INCOMPATIBLE`, `AUTHORITY_SCOPE_INVALID`,
`SUCCESSOR_TRANSFER_REQUIRES_DECISION`, `ORGANIZATIONAL_RELATION_OVERLAP`,
`ORGANIZATIONAL_CYCLE_FORBIDDEN`, `HISTORICAL_SCOPE_NOT_EFFECTIVE`. Ни
один существующий reason code не переименован и не изменён по смыслу
настоящим разделом; конфликтов имён с уже зарегистрированными кодами не
обнаружено (проверено настоящим раундом).

## 19e.22. Структурное разделение с другими контурами

`Organization`, `OrganizationalUnit`, `OrganizationalRelation`,
`OrganizationalHierarchyOverlapPolicy`, `OrganizationalInheritancePolicy`,
`OrganizationalAuthority` и `OrganizationalScope` не имеют ни одного
read- или write-ребра к `voting-service`, `tally-service` или
`VoteEnvelope` — ни прямо, ни через региональную scope-авторизацию
(19e.12). Региональная scope-авторизация никогда не предоставляет
доступ к бюллетеню или голосу. `RoleAssignment` и Governance Context
(19b) не изменяются настоящим разделом, помимо уже названной
классификации `scope_id` (19e.19). `Membership` (8.3) и Participation &
Membership Context (19d) не изменяются, за исключением того, что
`Membership.organization_id` (8.3) со временем получает реальный
референт (поведенческое, не полевое изменение будущего реализационного
раунда, `docs/packs/PACK-08-MIGRATION-MATRIX.md` раздел 2.1) — само
поле `organization_id` не меняется настоящим разделом. AI Processing
(раздел 17, 19c), Transparency (19a) и Emergency/Crisis Override
(раздел 19) не затрагиваются и не расширяются настоящим разделом.

## 19e.23. Ворота реализации (implementation gate)

Настоящий раздел определяет исключительно каноническую модель. Ни код
`organization-service`, ни база данных, ни миграция, ни event bus, ни
frontend, ни production-интеграция не авторизуются одним лишь этим
разделом (раздел 26; ADR-037; `docs/handover/PACK-08-CANON-AMENDMENT-REPORT.md`).
Реализация требует собственного отдельного, более позднего, управляемого
раунда, гейтуемого настоящим разделом и ADR-037, но не авторизуемого
ими в одиночку.

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
- `membership.terminated` (добавлено 0.6.0, 19d — завершает покрытие
  переходов `Membership.membership_status`, 8.3)
- `membership.rejected` (добавлено 0.6.0, 19d)
- `membership.expired` (добавлено 0.6.0, 19d)
- `role.assigned`
- `role.revoked`
- `organization.activated` (добавлено 0.7.0, 19e.10 — `draft → active`)
- `organization.suspended` (добавлено 0.7.0, 19e.10 — `active → restricted`)
- `organization.dissolved` (добавлено 0.7.0, 19e.10 — `→ archived`,
  `dissolved_at` зафиксирован)
- `organization.merged` (добавлено 0.7.0, 19e.10 — исходные узлы получили
  `merged_into`-отношение и распущены той же управляемой decision)
- `organization.split` (добавлено 0.7.0, 19e.10 — исходный узел получил
  `split_from`-отношения от результирующих узлов)
- `organization.successor_declared` (добавлено 0.7.0, 19e.10 —
  `successor_of`-отношение записано собственным управляемым решением)
- `organizational_relation.created` (добавлено 0.7.0, 19e.7)
- `organizational_relation.ended` (добавлено 0.7.0, 19e.7 — `valid_until`
  зафиксирован на существующей записи; новая версия при территориальном
  переназначении создаёт собственное `organizational_relation.created`)
- `organizational_authority.assigned` (добавлено 0.7.0, 19e.15)
- `organizational_authority.revoked` (добавлено 0.7.0, 19e.15 —
  `revocation_reason_reference` обязателен)
- `regional_scope_access.granted` (добавлено 0.7.0, 19e.12 — создаётся
  только для режимов 2–5 [ancestor/descendant/delegated/temporary
  supervision]; режим 1, exact-scope, будучи умолчанием, не создаёт
  собственного grant-события; режим 6, институциональный надзор без
  доступа к данным, по определению не предоставляет доступа и потому
  также не создаёт данного события)
- `regional_scope_access.revoked` (добавлено 0.7.0, 19e.12)

### Минимальный/запрещённый payload, время, версии, идемпотентность,
приватность (19e.20)

Для всех тринадцати событий, добавленных версией 0.7.0:

- **Канонический владелец** — `organization-service` (ADR-032), кроме
  `regional_scope_access.granted`/`.revoked`, которые может создавать
  любой сервис, вызывающий `check_regional_scope_access` (19e.12) от
  имени домена Organization & Regional Scope, но не как собственное,
  самостоятельно владеемое событие другого домена.
- **Минимальный payload** — идентификатор изменённой записи
  (`organization_id`/`relation_id`/`authority_id`), её новый статус,
  `effective_time` (см. ниже), `recorded_at`, `decision_reference`
  (где применимо, 19e.10) и, для reason-code-несущих событий, ровно
  один reason code раздела 24.
- **Запрещённый payload** — сырое имя/идентичность любого связанного с
  полномочием или отношением физического лица (только непрозрачные
  ссылки, 19e.18); полный список акторов, стоящих за многосторонним
  утверждением, где применимо (тот же принцип, что уже применён 19d.7);
  любое поле, специфичное для `voting-service`/`tally-service`/
  `VoteEnvelope` (19e.22).
- **Время вступления в силу (`effective_time`)** — соответствующий
  `valid_from` записи (может быть в будущем, 19e.9), отдельно от
  `recorded_at`.
- **Время записи (`recorded_at`)** — момент фактического создания
  события, всегда «сейчас» на момент публикации, независимо от
  `effective_time`.
- **Ссылки на версию политики** — `policy_version`
  (`OrganizationalHierarchyOverlapPolicy`/`OrganizationalInheritancePolicy`,
  где применимо к событию) включается, чтобы потребитель мог оценить,
  под какой версией политики принято решение (19e.13).
- **Привязка к аудиту** — каждое из тринадцати событий сопровождается
  записью `AuditEvent` (18.1) через `epd2_audit_core`, тот же
  сквозной проект-wide инвариант, что и для любого другого
  канонического события.
- **Ожидания идемпотентности** — повторная публикация того же события с
  тем же идентификатором записи и тем же новым статусом — не создаёт
  второй записи аудита и не изменяет состояние повторно (CT-00-04, тот
  же сквозной проект-wide инвариант).
- **Ограничения приватности** — ни одно из тринадцати событий не
  раскрывает информацию о членстве или идентичности, не связанную с
  самим организационным изменением (19e.18, правило 8); отсутствие
  публичного/межрегионального каталога участников (19e.18, правила 4–5)
  не нарушается ни одним из этих событий.
- **Не авторизует транспорт события** — настоящий раздел фиксирует
  только имя, владельца и семантику payload; ни JSON Schema, ни
  транспорт события, ни очередь не создаются настоящим каноническим
  раундом (19e.23).

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

Расширено версией канона 0.5.0 (ADR-023, раздел 19c). Существующие пять
событий сохранены (одно — с исправленным именем); добавлены шесть новых
событий, покрывающих `processing_status`, замену записи и жизненный
цикл раскрытия.

- `ai.processing_requested` — (без изменений) создана `AIProcessingRecord`.
- `ai.input_prepared` — (новое) `processing_status → input_prepared`
  (`redaction_manifest.result = "pass"`, 19c.4).
- `ai.output_created` — (без изменений) `processing_status → completed`.
- `ai.processing_failed` — (новое) `processing_status → failed`.
- `ai.processing_rejected_by_policy` — (новое) `processing_status →
rejected_by_policy` (включая исход `redaction_manifest.result =
"fail"`).
- `ai.processing_record_superseded` — (новое) новая запись, чей
  `supersedes_ai_processing_record_id` ссылается на данную запись, для
  замены технической попытки обработки (19c.2).
- `ai.output_reviewed` — (без изменений) `human_review_status → pending`.
- `ai.output_accepted` — (новое) `human_review_status → approved`.
- `ai.output_corrected` — (имя исправлено; ранее `ai.output.corrected`)
  `human_review_status → approved_with_changes`.
- `ai.output_rejected` — (без изменений) `human_review_status →
rejected`.
- `ai.review_outcome_superseded` — (новое) новая запись, чей
  `supersedes_ai_processing_record_id` ссылается на данную запись, для
  замены итога человеческой проверки (19c.2).

`ai.processing_record_superseded` и `ai.review_outcome_superseded`
создаются при создании новой, замещающей записи (19c.2) — не при
изменении статуса замещаемой записи, поскольку ни `processing_status`,
ни `human_review_status` не хранят значения `superseded` в этом смысле
и ни одно поле замещаемой записи не переписывается (19c.1, 19c.2).

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

## 20.16. Участие и членство

Добавлено версией канона 0.6.0 (ADR-026 через ADR-031, раздел 19d).
События создаются исключительно `eligibility-service` и
`membership-service` при активации/замене политик, обработке заявления
о членстве, декларации аффилиации, оценке конфликта, а также записи
цифрового/ассамблейного решения.

- `participant_eligibility_policy.activated`
- `participant_eligibility_policy.superseded`
- `process_eligibility_policy.activated`
- `process_eligibility_policy.superseded`
- `party_membership_eligibility_policy.activated`
- `party_membership_eligibility_policy.superseded`
- `step_up_authentication_requirement.activated`
- `step_up_authentication_requirement.superseded`
- `authentication_context.step_up_completed`
- `membership_application.created`
- `membership_application.eligibility_reviewed`
- `membership_application.human_decision_recorded`
- `membership_application.approved`
- `membership_application.rejected`
- `membership_application.activated`
- `affiliation_declaration.submitted`
- `affiliation_declaration.updated`
- `affiliation_declaration.withdrawn`
- `conflict_assessment.opened`
- `conflict_assessment.decided`
- `conflict_assessment.appealed`
- `conflict_assessment.overturned`
- `conflict_assessment.reevaluation_due`
- `digital_decision.recorded`
- `digital_decision.finalized`
- `assembly_decision.opened`
- `assembly_decision.confirmed`
- `assembly_decision.rejected`
- `assembly_decision.returned_for_revision`

`ParticipationRightsProfile` (19d.13) — производная модель, никогда не
хранится и не создаёт собственных событий. `*_policy.superseded`
создаётся при активации новой, замещающей версии соответствующей
критической политики (19d.7) — не при изменении статуса замещаемой
записи.

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
| ParticipantEligibilityPolicy | Eligibility Engine |
| ProcessEligibilityPolicy | Eligibility Engine |
| StepUpAuthenticationRequirement | Eligibility Engine |
| DigitalDecision | Eligibility Engine |
| AssemblyDecision | Eligibility Engine |
| PartyMembershipEligibilityPolicy | Membership Service |
| AffiliationDeclaration | Membership Service |
| ConflictAssessment | Membership Service |
| MembershipApplication | Membership Service |
| AuthenticationContext | Identity Verification Service |
| OrganizationalUnit | Organization Service |
| OrganizationalRelation | Organization Service |
| OrganizationalHierarchyOverlapPolicy | Organization Service |
| OrganizationalInheritancePolicy | Organization Service |
| OrganizationalAuthority | Organization Service |

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

Версия канона 0.5.0 (ADR-023, ADR-025, раздел 19c) не добавляет ни
одной новой строки в настоящую матрицу: `AIProcessingRecord` уже
присутствует в ней ("AI Accountability Service") и остаётся её
единственным владельцем без изменений. `RedactionManifest` — встроенный
объект-значение внутри `AIProcessingRecord` (19c.4), не отдельная
владеемая сущность. `AIDisclosurePackage` — договорной объект/объект-
значение (19c.6), никогда не сохраняемый ни `ai-processing-service`, ни
`transparency-service`, и потому также не получает собственной строки.

Десять строк (`ParticipantEligibilityPolicy`, `ProcessEligibilityPolicy`,
`StepUpAuthenticationRequirement`, `DigitalDecision`, `AssemblyDecision`,
`PartyMembershipEligibilityPolicy`, `AffiliationDeclaration`,
`ConflictAssessment`, `MembershipApplication`, `AuthenticationContext`)
добавлены версией канона 0.6.0 (ADR-026 через ADR-031, раздел 19d).
Физически первые пять реализуются существующим `eligibility-service`
(расширение, первое с PACK-02); следующие четыре — новым
`membership-service`; последняя — существующим `identity-service`
(расширение). Строка `Membership` ("Membership Service") уже
присутствовала в настоящей матрице до версии 0.6.0 и не изменяется —
`membership-service` теперь физически реализует и её, и четыре новые
строки выше, тем же принципом "один физический сервис — несколько
канонически названных модулей". Строка `RoleAssignment` ("Permission /
Role Service") не изменяется настоящей версией.

Пять строк (`OrganizationalUnit`, `OrganizationalRelation`,
`OrganizationalHierarchyOverlapPolicy`, `OrganizationalInheritancePolicy`,
`OrganizationalAuthority`) добавлены версией канона 0.7.0 (ADR-032 через
ADR-037, раздел 19e). Физически все пять реализуются новым
`organization-service` (ADR-032, ещё не созданным — настоящий раунд
канонический, не реализационный, 19e.23), вместе с уже существующими
строками `Organization` и `CivicSpace` ("Organization Service", без
изменений настоящей версией) — тот же принцип "один физический сервис
— несколько канонически названных модулей". `OrganizationalScope`
(19e.11) не получает собственной строки — переиспользуемый объект-
значение, тот же статус, что уже применён к `RedactionManifest` (19c.4)
и `AIDisclosurePackage` (19c.6). Строки `RoleAssignment` ("Permission /
Role Service") и `Membership` ("Membership Service") не изменяются
настоящей версией — см. 19e.19/19e.22 для единственного затрагиваемого
аспекта (`RoleAssignment.scope_id`'s классификация, не поле/статус/
владелец).

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
- `AIProcessingRecord` / `redaction_manifest` / `AIDisclosurePackage` → самостоятельное политическое, governance-, модерационное, голосующее, eligibility-, ролевое, emergency- или публикационное решение (добавлено 0.5.0, 19c.9) — каждое такое решение остаётся исключительно командой сервиса, владеющего соответствующей сущностью
- `AIProcessingRecord` / `redaction_manifest` / `AIDisclosurePackage` → обратный поиск скрытой `IdentityRecord`, не требуемой для заявленной операции (добавлено 0.5.0, 19c.9; уточняет уже существующий запрет `AIProcessingRecord → скрытый IdentityRecord`, выше)
- `AIProcessingRecord` / `redaction_manifest` / `AIDisclosurePackage` → восстановление связи `VoteEnvelope` с личностью либо агрегирование содержимого голоса (добавлено 0.5.0, 19c.9)
- Внешний провайдер модели ИИ → полномочие на мутацию Civic OS через callback или tool-calling интерфейс (добавлено 0.5.0, 19c.6, 19c.9)
- `redaction_manifest` → исходный ввод / удалённые значения / данные личности / данные credential / содержимое голоса / содержимое приватного аудита (добавлено 0.5.0, 19c.4) — допустимы только метаданные уровня категории
- `AIDisclosurePackage` → исходный приватный ввод / исходный приватный результат (кроме отдельно утверждённого для публикации) / скрытый prompt / приватная личность рецензента / UUID `RoleAssignment` / данные identity, account или credential / данные голоса (добавлено 0.5.0, 19c.6)
- `AIProcessingRecord` / `AIDisclosurePackage` → заявление или представление скрытых рассуждений модели (chain-of-thought) как факта или доказательства (добавлено 0.5.0, 19c.9)
- Официальный/публичный артефакт, зависящий от ИИ-содействующего результата → завершение при `DisclosureStatus`, отличном от `published` (добавлено 0.5.0, 19c.7)
- `ParticipantEligibilityPolicy` / `ProcessEligibilityPolicy` / `StepUpAuthenticationRequirement` / `DigitalDecision` / `AssemblyDecision` / `PartyMembershipEligibilityPolicy` / `AffiliationDeclaration` / `ConflictAssessment` / `MembershipApplication` / `AuthenticationContext` → `VoteEnvelope` / `Tally` / `Ballot` (прямо либо через `ParticipationRightsProfile`) (добавлено 0.6.0, 19d.18)
- Любой сервис или frontend → чтение `ParticipationRightsProfile` и принятие решения о разрешении/запрете действия на его основе (добавлено 0.6.0, 19d.13, 19d.14) — единственно допустимые механизмы авторизации фиксированы 19d.14
- `IdentityRecord.identity_assurance_level` / `identity_scheme` → подмена, замена или использование как признак `citizenship_status` (добавлено 0.6.0, 19d.2)
- Любая `RoleAssignment`, участвующая в утверждении критической политики (19d.7) → раскрытие вызывающей стороне полного списка утверждающих акторов, стоящего за `multi_person_approval_met` (добавлено 0.6.0, 19d.7) — передаётся только булево значение
- `membership-service` → самостоятельное вычисление любого из четырёх признаков избирательного права (19d.3) (добавлено 0.6.0, 19d.3) — вычисление остаётся исключительно за `eligibility-service`
- `AffiliationDeclaration` / `ConflictAssessment` → публикация вне ограниченного, целевого доступа `ConflictAssessment`-рецензента (добавлено 0.6.0, 19d.10, 19d.11) — данные о членстве и аффилиации ограничены по умолчанию
- Автоматизированная оценка политики (любая критическая политика, 19d.7, либо `ParticipantEligibilityPolicy`/`ProcessEligibilityPolicy`/`PartyMembershipEligibilityPolicy`) → единоличное, окончательное производство любого из семи исходов раздела 19d.16 (добавлено 0.6.0, 19d.16)
- `Organization` / `OrganizationalUnit` / `OrganizationalRelation` / `OrganizationalHierarchyOverlapPolicy` / `OrganizationalInheritancePolicy` / `OrganizationalAuthority` / `OrganizationalScope` → `VoteEnvelope` / `Tally` / `Ballot` (прямо либо через региональную scope-авторизацию) (добавлено 0.7.0, 19e.22)
- Название `role_code` (например, `"kreisvorsitzender"`) само по себе → доказательство полномочия (добавлено 0.7.0, 19e.12) — обязательна текущая активная запись `RoleAssignment`/`OrganizationalAuthority` с совпадающим scope и окном действия
- Позиция в организационной иерархии сама по себе → институциональное полномочие или расширенный доступ к данным на любом более низком/высоком уровне иерархии без явной `OrganizationalInheritancePolicy` (добавлено 0.7.0, 19e.12, 19e.13)
- Frontend или любой клиентский код → источник региональной scope-авторизации или самостоятельный вывод наследования (добавлено 0.7.0, 19e.12, 19e.13)
- `organization_id` / `jurisdiction` / `region_code` / `scope_id` / `civic_space_id` → молчаливая переинтерпретация значения поля между доменами без явной классификации ADR-035/`docs/packs/PACK-08-MIGRATION-MATRIX.md` (добавлено 0.7.0, 19e.2)
- `Organization.parent_reference` → независимая мутация в обход `OrganizationalRelation` (добавлено 0.7.0, 19e.4) — единственный авторитетный источник иерархических связей — `OrganizationalRelation`
- `OrganizationalRelation` категории containment/subordination (`parent_of`/`subordinate_to`) → цикл любой длины (добавлено 0.7.0, 19e.7) — без исключений
- `merged_into` / `split_from` / `successor_of` отношение само по себе → передача полномочия, роли, права доступа или институционального назначения предшествующего узла (добавлено 0.7.0, 19e.10) — требуется явное управляемое решение, дата вступления в силу и запись аудита
- `RoleAssignment.scope_id`, классифицированный как категория 6 (недействительный/legacy неоднозначный, 19e.19) → использование в `check_regional_scope_access` или иной scope-осведомлённой логике до реклассификации (добавлено 0.7.0, 19e.19)
- Роль с global/system scope (категория 5, 19e.19) → универсальное административное полномочие (добавлено 0.7.0, 19e.12, 19e.16, 19e.17) — HI-11-эквивалентный запрет применяется к global/system scope так же, как к любой другой роли
- `temporary_supervision_by`-отношение без установленного `valid_until` → создание или сохранение в статусе `active` (добавлено 0.7.0, 19e.14) — бессрочный временный надзор запрещён структурно

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
- `ORGANIZATION_NOT_ACTIVE` (добавлено 0.7.0, 19e.21) — scope- или
  authority-проверка выполнена против узла `Organization`/
  `OrganizationalUnit`, не находящегося в статусе `active`.
- `ORGANIZATION_SCOPE_MISMATCH` (добавлено 0.7.0, 19e.21) — заявленный
  `OrganizationalScope` не соответствует scope целевой записи.
- `CROSS_SCOPE_ACCESS_DENIED` (добавлено 0.7.0, 19e.21) — ни один из
  шести режимов раздела 19e.12 не предоставил доступ; default-deny
  сработал.
- `AUTHORITY_ASSIGNMENT_INVALID` (добавлено 0.7.0, 19e.21) —
  назначение `OrganizationalAuthority` не удовлетворяет правилу
  жизненного цикла (19e.17).
- `AUTHORITY_ROLE_INCOMPATIBLE` (добавлено 0.7.0, 19e.21) — назначение
  нарушает минимальную базовую матрицу несовместимости (19e.16).
- `AUTHORITY_SCOPE_INVALID` (добавлено 0.7.0, 19e.21) — `scope`
  назначения `OrganizationalAuthority` структурно некорректен или не
  разрешается ни к одному из четырёх понятий раздела 19e.2.
- `SUCCESSOR_TRANSFER_REQUIRES_DECISION` (добавлено 0.7.0, 19e.21) —
  попытка использовать `successor_of`/`merged_into`/`split_from`
  отношение как основание для передачи полномочия без отдельного
  явного управляемого решения (19e.10).
- `ORGANIZATIONAL_RELATION_OVERLAP` (добавлено 0.7.0, 19e.21) —
  перекрывающееся hierarchy-категории отношение без разрешающей
  `OrganizationalHierarchyOverlapPolicy` (19e.7, 19e.8).
- `ORGANIZATIONAL_CYCLE_FORBIDDEN` (добавлено 0.7.0, 19e.21) — попытка
  создать цикл в отношении категории containment/subordination (19e.7).
- `HISTORICAL_SCOPE_NOT_EFFECTIVE` (добавлено 0.7.0, 19e.21) — запрос к
  историческому состоянию scope/полномочия за пределами его
  `[valid_from, valid_until)` окна (19e.9).

Реестр PACK-08, 19e.21 — единственный источник конфликта имён,
проверенный настоящим раундом: ни один из десяти кодов выше не
переопределяет и не переименовывает существующий код настоящего
раздела; конфликтов не обнаружено (`docs/handover/PACK-08-CANON-AMENDMENT-REPORT.md`
раздел 3).

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
