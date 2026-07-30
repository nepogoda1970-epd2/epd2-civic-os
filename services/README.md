# Services

Заготовка каталога для будущих автономных бизнес-сервисов EPD² Civic OS
(Account, Identity, Eligibility, Credential, Organization, Initiative,
Discussion, Moderation, Voting, Tally, Delegation, Transparency,
Governance, Audit Core — см. `docs/canonical/TZ-00-domain-event-canon.md`,
раздел 22).

На этапе CLAUDE-PACK-01 этот каталог **намеренно пуст**: настоящий пакет
запрещает создание бизнес-модулей. См. `docs/development/new-module-guide.md`
для правил добавления сервиса в последующих пакетах.

---

## Текущий состав каталога

Каталог давно не пуст: PACK-02 — PACK-13 добавили тринадцать сервисов.
Ниже — только те, чей владелец и статус зафиксированы; полный список
доменов и их владельцев — `docs/architecture/data-ownership.md` и
`docs/canonical/TZ-00-domain-event-canon.md`, раздел 22.

| Сервис                                                                                                                      | Пакет   | Статус                                                              |
| --------------------------------------------------------------------------------------------------------------------------- | ------- | ------------------------------------------------------------------- |
| `account-service`, `identity-service`, `eligibility-service`, `credential-service`, `audit-core`                            | PACK-02 | reference implementation                                            |
| `initiative-service`, `deliberation-service`, `moderation-service`, `voting-service`, `tally-service`, `delegation-service` | PACK-03 | reference implementation                                            |
| `transparency-service`                                                                                                      | PACK-04 | reference implementation                                            |
| `governance-service`                                                                                                        | PACK-05 | reference implementation                                            |
| `ai-processing-service`                                                                                                     | PACK-06 | reference implementation                                            |
| `membership-service`                                                                                                        | PACK-07 | reference implementation                                            |
| `organization-service`                                                                                                      | PACK-08 | reference implementation                                            |
| `compliance-service`                                                                                                        | PACK-09 | reference implementation                                            |
| `finance-service`                                                                                                           | PACK-10 | reference implementation                                            |
| `document-service`                                                                                                          | PACK-11 | reference implementation                                            |
| `privileged-access-service`                                                                                                 | PACK-12 | reference implementation                                            |
| `data-plane-service`                                                                                                        | PACK-13 | reference implementation — **implementation candidate, not a PASS** |

`reference implementation` — это честное, а не скромное описание: у
каждого сервиса governed-процессы, модель разделения и поверхность
отказов реальны и покрыты тестами, а production data plane отсутствует.
`services/data-plane-service` специфицирует именно этот отсутствующий
слой и реализует его контракты — но не разворачивает его: каждый адаптер
в нём in-memory (`docs/handover/PACK-13-KNOWN-LIMITATIONS.md`).

Правила добавления сервиса в последующих пакетах не изменились —
`docs/development/new-module-guide.md`.
