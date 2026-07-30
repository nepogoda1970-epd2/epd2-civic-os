# PACK-13 — Event Delivery Matrix

Specification-only. No code. Not implemented.

Companion to `PACK-13-SPECIFICATION.md` §8–§11,
`ADR-071-TRANSACTIONAL-OUTBOX.md` and
`ADR-072-AT-LEAST-ONCE-DELIVERY-AND-IDEMPOTENT-CONSUMERS.md`.

---

## 1. The guarantee, stated once and precisely

```text
Transport guarantee:  at-least-once delivery
Consumer effect:      effectively-once, through idempotency
Never claimed:        exactly-once delivery
```

`P13-DEL-015` No PACK-13 document, code comment, API description, operator
surface or log message may describe delivery as exactly-once. A team that
believes it has exactly-once delivery stops writing idempotent consumers,
and the guarantee then fails silently the first time a broker redelivers.

---

## 2. Situation matrix

| #   | Situation                         | Detection                                                   | Retry                         | Evidence                                       | Escalation                                 | Operator action                              | Residual risk                                                                                             |
| --- | --------------------------------- | ----------------------------------------------------------- | ----------------------------- | ---------------------------------------------- | ------------------------------------------ | -------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| 1   | **Duplicate delivery**            | dedup key = event ID + consumer scope                       | n/a                           | dedup record; duplicate counter                | none unless rate is anomalous              | none                                         | dedup record expiry could admit a very late duplicate — mitigated by `P13-IDEM-006`                       |
| 2   | **Delayed delivery**              | event `occurred_at` vs processing time; consumer lag metric | n/a                           | lag metric                                     | threshold alert                            | investigate the backlog                      | a consequential decision taken on stale derived state — mitigated by `P13-PROJ-008`                       |
| 3   | **Out-of-order within scope**     | sequence gap or regression against the checkpoint           | buffer or reject, per family  | out-of-order event with reason code            | threshold alert                            | review the ordering scope                    | a consumer that ignores the reason code applies an older state                                            |
| 4   | **Missing acknowledgement**       | dispatch recorded, no ack within window                     | redeliver                     | attempt record; status `dispatching` → unknown | after N attempts                           | check broker health                          | duplicate delivery (situation 1), which is safe by design                                                 |
| 5   | **Consumer retry**                | handler error                                               | bounded, backed off           | attempt count                                  | on exhaustion → dead-letter                | review the dead-letter                       | a transient failure misclassified as poison                                                               |
| 6   | **Dead-letter**                   | retry exhausted, or poison detected                         | none                          | dead-letter record with full failure context   | **always alertable**                       | mandatory review                             | dead-letter store holds personal data — classified and access-controlled (`P13-DEL-014`)                  |
| 7   | **Replay**                        | explicit, authorized request                                | n/a                           | replay reference; scope; authority             | —                                          | approve and scope the replay                 | replay amplifies a bug across history; scope and dry-run are required                                     |
| 8   | **Consumer checkpoint advance**   | normal operation                                            | n/a                           | checkpoint record                              | backwards move is a distinct authorized op | —                                            | a checkpoint advanced past an unprocessed event is silent loss — hence durability before advance          |
| 9   | **Poison event**                  | deterministic failure across N attempts on distinct workers | stop                          | poison classification with reason code         | **alert**                                  | review; fix consumer or quarantine           | a genuinely transient fault classified as poison                                                          |
| 10  | **Compatibility failure**         | schema version unsupported by consumer                      | none                          | incompatibility event; consumer registration   | **alert the schema owner**                 | migrate the consumer or roll the change back | a non-consequential consumer skipping is acceptable; a consequential one must fail closed (`P13-DEL-013`) |
| 11  | **Sequence gap**                  | expected sequence not observed                              | wait, bounded                 | gap-detected event                             | alert on persistence                       | investigate producer or transport            | a permanent gap means an event was lost before the outbox — impossible if `P13-TX-003` holds              |
| 12  | **Broker unavailable**            | dispatch failure                                            | outbox retains; backlog grows | backlog metric                                 | threshold alert                            | restore the broker                           | backlog growth to storage pressure — bounded by alerting                                                  |
| 13  | **Outbox backlog**                | pending count / oldest-pending age                          | n/a                           | backlog metrics                                | threshold alert                            | scale or investigate the dispatcher          | publication delay, never loss                                                                             |
| 14  | **Dispatcher crash mid-dispatch** | status stuck in `dispatching` past a timeout                | redeliver                     | attempt record                                 | after N                                    | none usually                                 | duplicate delivery (safe)                                                                                 |

`P13-DEL-016` Situations 4 and 14 both resolve to duplicate delivery. That
is the intended outcome: the design chooses a safe duplicate over an unsafe
uncertainty, and the safety comes entirely from consumer idempotency.

---

## 3. Ordering scopes per event family

| Family                                                    | Ordering scope                     | Sequence source         | Consumer obligation                            |
| --------------------------------------------------------- | ---------------------------------- | ----------------------- | ---------------------------------------------- |
| Aggregate lifecycle (grant, document, export, membership) | **per aggregate**                  | aggregate version       | reject or buffer out-of-order                  |
| Schema registry                                           | **per schema family**              | schema version sequence | lifecycle transitions must be applied in order |
| Migration                                                 | **per migration plan**             | plan step index         | strict; a gap halts                            |
| Outbox / delivery                                         | **per outbox record**              | attempt number          | none; attempts are independent                 |
| Projection                                                | **per projection and aggregate**   | source event sequence   | apply in order within the aggregate            |
| Organization scope changes                                | **per organization and aggregate** | aggregate version       | reject out-of-order                            |

`P13-ORD-010` No family declares "global". A family that appears to need
global order is redesigned, not granted an exception.

---

## 4. Idempotency scopes

| Operation                  | Key derived from                    | Scope             | Retention driver    | Consequence of expiry                                                                    |
| -------------------------- | ----------------------------------- | ----------------- | ------------------- | ---------------------------------------------------------------------------------------- |
| Domain command             | caller-supplied `event_id`          | domain + command  | policy              | conflict window closes; **a consequential command carries a second business-fact guard** |
| Event consumption          | event ID                            | consumer + event  | policy              | very late duplicate possible; business-fact guard required for consequential effects     |
| External provider callback | provider's own reference            | domain + provider | policy              | duplicate callback                                                                       |
| Export generation          | export request ID                   | privileged-access | artifact retention  | a second artifact for one approval — forbidden; guarded by request state                 |
| Document rendition         | version hash + audience             | document          | rendition retention | duplicate rendition, harmless                                                            |
| Finance import             | source file digest + line reference | finance           | statutory           | **duplicate posting — never acceptable**; guarded by posting uniqueness                  |
| Deadline job               | deadline ID + scheduled instant     | compliance        | policy              | duplicate notification                                                                   |
| Notification dispatch      | activation/notification ID          | privileged-access | policy              | duplicate notification, preferred over none                                              |
| Schema publication         | schema digest                       | registry          | permanent           | duplicate publication — blocked by digest uniqueness                                     |
| Migration                  | migration ID                        | migration context | permanent           | re-application — blocked by applied-state check                                          |

`P13-IDEM-010` Rows whose expiry consequence is unacceptable (finance
import, export generation, schema publication, migration) carry a
**permanent business-fact guard** in addition to the idempotency record.
The idempotency record is an optimisation; the guard is the control.
