# EPD² Civic OS — NEW BRANCH BOOTSTRAP

Работаем с проектом:

`nepogoda1970-epd2/epd2-civic-os`

## 0. СНАЧАЛА — ОБЯЗАТЕЛЬНАЯ ПРОВЕРКА ВОЗМОЖНОСТЕЙ ЭТОГО ЧАТА

**До анализа проекта, чтения старых отчётов и любых предложений сначала проверь реально доступные в ЭТОЙ сессии GitHub-инструменты. Не предполагай возможности по памяти или по предыдущим чатам.**

В первом ответе дай мне короткий статус строго по этим пунктам:

```text
GITHUB CAPABILITY CHECK

1. Read repository/files/branches/commits: YES / NO
2. Read workflow runs/jobs/logs/artifacts: YES / NO
3. Create branch: YES / NO
4. Create/update/delete repository files: YES / NO
5. Move/update branch refs: YES / NO
6. Trigger or rerun GitHub Actions/workflow jobs: YES / NO
7. Download workflow artifacts: YES / NO

RESULT:
FULL EPD2 EXECUTION AVAILABLE
или
LIMITED / READ-ONLY — missing: <точный список>
```

### Что считать полноценным режимом

Для полноценной EPD² development/closure работы должны быть доступны как минимум:

- чтение live GitHub;
- создание/обновление файлов;
- работа с отдельными ветками;
- commit/ref updates;
- чтение workflow logs/artifacts;
- запуск или rerun GitHub Actions.

Если чего-то из этого нет:

**скажи об этом сразу в первом ответе и не трать время на длинный анализ, который предполагает недоступное исполнение.**

Не говори «я могу довести до PASS», если write/Actions реально недоступны.

Если полный доступ есть:

**не спрашивай дополнительного разрешения — сразу продолжай работу по правилам ниже.**

---

# 1. LIVE AUTHORITY — ВСЕГДА СНАЧАЛА

Перед любой EPD² development, verification, planning, status assessment, correction, packaging, release или repository task:

прочитай из **текущего live repository** строго в этом порядке:

1. `docs/roadmap/EPD2_PROJECT_ENTRYPOINT.md`
2. `docs/roadmap/EPD2_PROGRAM_CONTROL_REGISTER.md`
3. `docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md`
4. exact current stage contract / handover, указанный PCR.

Не определяй текущий статус проекта по:

- памяти чата;
- старым сообщениям;
- названию ZIP;
- старым PACK/DATA/API/INFRA/OPS/CTRL/FRONT/SEC отчётам;
- старому continuation memo.

Если live canonical repository доступен — **он имеет приоритет**.

---

# 2. CONTINUATION MEMO — ЭТО HANDOFF, НЕ AUTHORITY

Приложенная/переданная записка:

`EPD2_CONTINUATION_MEMO_20260904_V2.md`

является:

`handoff snapshot`

а не live authority.

Используй её для:

- понимания последовательности;
- predecessor relationships;
- известных кандидатов;
- известных blocker-ов;
- hard invariants;
- shortest safe path.

Но перед любым утверждением:

```text
CURRENT
PASS
AUTHORITATIVE PASS
ACCEPTED
CLOSED
PRQ PROVEN
SYSTEM TRIAL PREVIEW OPEN
```

обязательно перепроверь live GitHub и canonical registers.

---

# 3. ОСНОВНЫЕ СЕМАНТИЧЕСКИЕ ПРАВИЛА

Никогда не смешивай:

```text
WORKING
PRESEAL
PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED
CANDIDATE_NOT_ACCEPTED
PASS_LOCAL
AUTHORITATIVE PASS / AWAITING GOVERNANCE ACCEPTANCE
ACCEPTED / CLOSED
```

Особенно:

```text
PASS_LOCAL
≠ AUTHORITATIVE PASS
≠ GOVERNANCE ACCEPTANCE
```

Candidate не может self-accept.

CI PASS — evidence, а не governance acceptance.

Acceptance должен связывать exact bytes.

Отдельное governance action переводит stage в:

`ACCEPTED / CLOSED`

---

# 4. КОНФЛИКТЫ — FAIL CLOSED

Если:

- PCR;
- FIR;
- stage contract;
- candidate;
- evidence;
- acceptance record

материально расходятся:

не угадывай.

Не выбирай молча более старый документ.

Не заявляй:

- PASS;
- CLOSED;
- READY;
- IMPLEMENTED.

Сначала reconcile.

Если reconciliation можно выполнить через доступный GitHub — сделай это сам.

Пользователя привлекай только если требуется реальное governance/legal/business решение, которое невозможно вывести из уже принятых правил.

---

# 5. AUTONOMOUS EXECUTION

Для каждого задания выполняй максимум работы самостоятельно.

Принцип:

```text
maximum autonomous completion
→ verification
→ concrete result
```

а не:

```text
partial analysis
→ manual task for user
→ continuation
```

Не проси пользователя:

- вручную править файлы;
- запускать команды;
- считать SHA;
- смотреть обычные logs;
- создавать routine commits;
- переносить механические изменения;

если это можешь сделать сам доступными инструментами.

Если task понятен и безопасен — продолжай через зависимые шаги без лишних остановок.

---

# 6. CURRENT STRATEGIC ORDER

Live state нужно перепроверить, но governing sequence к первому реальному пробнику остаётся:

```text
API CLOSED
→ INFRA/OPS PREVIEW-READINESS MINIMUM
→ SYSTEM TRIAL PREVIEW
→ INFRA CLOSED
→ OPS CLOSED
→ CTRL CLOSED
→ FRONT CLOSED
→ FINAL INTEGRATION
→ SEC
→ FINAL READINESS
```

System Trial Preview:

- не является отдельным layer;
- не означает production readiness;
- не закрывает автоматически INFRA/OPS/CTRL/FRONT;
- не является BSI/CC certification.

---

# 7. CURRENT PRIORITY ORDER

После live verification действуй по фактическому состоянию repository.

Рабочая приоритетная последовательность:

## Priority 1 — INFRA-04

Закрыть INFRA-04 cleanly.

Не начинать с нуля, если live GitHub уже содержит более свежую диагностику.

Найди:

- текущую `candidate/infra04-c2-canonical`;
- последний authoritative run;
- точные failing gates;
- текущие diagnostics/repair branches.

Исправляй только реальные оставшиеся blocker-ы.

Целевой технический endpoint:

```text
INFRA-04 =
AUTHORITATIVE PASS / AWAITING GOVERNANCE ACCEPTANCE
```

Только отдельная governance action может затем установить:

```text
INFRA-04 = ACCEPTED / CLOSED
```

Не закрывай автоматически INFRA layer.

Не открывай автоматически System Trial Preview.

---

## Priority 2 — FIND-ST01-04

Параллельно, если INFRA-04 не требует всех доступных ресурсов:

довести governed acceptance path FIND-ST01-04.

Не переделывать уже работающую runtime correction без доказанной необходимости.

Закрывать именно:

- governed artifact/dependency acquisition;
- evidence revision consistency;
- non-authoritative wording;
- legacy verification ambiguity;
- authoritative run;
- independent exact-byte review;
- governance acceptance.

---

## Priority 3 — INFRA-05 / PRQ-17

После accepted INFRA-04:

- fresh reconciliation;
- bind exact accepted INFRA-04;
- real observability redeployment;
- rerun qualification;
- seal;
- authoritative review;
- governance acceptance;
- `PRQ-17 PROVEN`.

---

## Priority 4 — INFRA-06 / PRQ-19

После accepted INFRA-04:

- bind exact accepted platform;
- real NTS/time deployment;
- external trusted time;
- destination-restricted egress;
- refusal evidence;
- seal;
- authoritative review;
- governance acceptance;
- `PRQ-19 PROVEN`.

---

## Priority 5 — SEC-PREVIEW-01 / PRQ-18

Только после:

```text
FIND-ST01-04 = ACCEPTED / CLOSED
INFRA-04 = ACCEPTED / CLOSED
```

и exact accepted API-02 foundation.

Затем:

```text
real Keycloak principal
→ accepted API auth/session
→ accepted FIND Member Runtime
→ protected member route
→ same Identity Authentication authority
→ authorization/refusal
```

Закрыть G27:

`MEMBER_RUNTIME_IDENTITY_AUTHENTICATION_BINDING`

После authoritative review + governance:

`PRQ-18 PROVEN`.

---

# 8. PREVIEW PREREQUISITES — НЕ СЕРИАЛИЗОВАТЬ ОШИБОЧНО

Правильная структура:

```text
                         ┌─ INFRA-05 → PRQ-17
accepted INFRA-04 ───────┼─ SEC-PREVIEW-01 → PRQ-18
                         └─ INFRA-06 → PRQ-19

accepted FIND-ST01-04 ─────→ SEC-PREVIEW-01 G27
accepted API-02 C13 ───────→ SEC-PREVIEW-01

PRQ-17 + PRQ-18 + PRQ-19
            ↓
     PRQ-20 governance
            ↓
SYSTEM TRIAL PREVIEW = OPEN
```

INFRA-05 и INFRA-06 — sibling prerequisites, а не predecessor SEC-PREVIEW-01.

---

# 9. HARD INVARIANTS

Не потерять:

- `FIR-GOV-004`
- `FIR-GOV-005`
- `FIR-SEC-004`
- `FIR-TRUST-002`
- `FIR-TRUST-003`
- `FIR-OSS-007`
- `FIR-VOTE-BSI-001`

Особенно voting identity boundary:

до явного governed изменения authentication заканчивается на identity/eligibility boundary.

В voting domain не передавать:

- civil identity;
- account/member identity;
- persistent person/member identifier;
- reusable Keycloak `sub`;
- Keycloak `sid`;
- normal Member Core session identifier.

---

# 10. FIRST SYSTEM TRIAL PREVIEW

Когда PRQ-17/18/19 доказаны и PRQ-20 governance пройден:

не делать новый giant source merge.

Собирать первый preview из **exact accepted artifacts**.

Нужны:

- exact component identities;
- deployment/config digests;
- Member Runtime identity;
- Keycloak realm/config identity;
- DB/schema identity;
- trusted-time identity;
- observability identity;
- exact CTRL/FRONT artifacts.

Цель первого bounded пробника:

```text
create real preview member
→ login
→ accepted auth/session
→ corrected Member Runtime
→ allowed action
→ denied action
→ audit evidence
→ observability evidence
→ trusted timestamp
→ logout/revoke
→ stale-session refusal
→ reset/recovery
```

---

# 11. COMPLETION STANDARD

Не выдавай промежуточный результат за завершение.

Если задача не может быть полностью закончена:

1. выполни всё возможное;
2. укажи точный blocker;
3. дай strongest verified intermediate result;
4. не перекладывай устранимую работу на пользователя.

В финале указывай, где применимо:

- что изменено;
- branch;
- commit SHA;
- artifact;
- SHA-256;
- workflow run/job/artifact IDs;
- verification result;
- exact remaining blocker.

---

# 12. ПЕРВЫЙ ОТВЕТ В НОВОЙ ВЕТКЕ

Твой первый ответ после получения этой записки должен быть коротким.

Сначала только:

```text
GITHUB CAPABILITY CHECK
...
RESULT: ...
```

Если:

`FULL EPD2 EXECUTION AVAILABLE`

то сразу после этого:

```text
Начинаю live bootstrap:
Entrypoint → PCR → FIR → current stage contract → live GitHub state.
```

и начинай работу.

Если:

`LIMITED / READ-ONLY`

то перечисли недостающие capabilities и **остановись до тяжёлого анализа**, чтобы пользователь мог сразу перейти в другую ветку.

Не трать время пользователя на двадцать сообщений до выяснения, что реальное исполнение недоступно.
