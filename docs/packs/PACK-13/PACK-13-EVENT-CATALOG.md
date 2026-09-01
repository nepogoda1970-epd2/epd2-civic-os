# PACK-13 — Event Catalog

Specification-only. No code, no schema file, no implementation.

Companion to `PACK-13-SPECIFICATION.md` §8–§10, §12, §18, §21.

---

## 1. Envelope and naming

`P13-EVT-001` Events use the **existing canon §21 envelope, unchanged**.
PACK-13 adds no envelope field, removes none, and reinterprets none.

`P13-EVT-002` Names carry the **aggregate prefix** (canon §20), never a
service or pack prefix: `schema_version.approved`, never
`pack13.schema_approved`.

`P13-EVT-003` Every payload is minimal — identifiers, enum values,
timestamps, one reason code, version and policy references, opaque
references. Every payload passes the prohibited-key guard before an
envelope exists.

`P13-EVT-004` **Public projection allowance is empty.** Every event below
describes internal data-plane machinery — schema governance, migration,
delivery, projection health. None is public information.

---

## 2. Schema registry — 9 events

| Event                                      | Aggregate         | Payload carries                                                           |
| ------------------------------------------ | ----------------- | ------------------------------------------------------------------------- |
| `schema_version.proposed`                  | `schema_version`  | schema ID, family, version, owner, format, canonical digest               |
| `schema_version.compatibility_assessed`    | `schema_version`  | assessment ID, automated verdict, human verdict, mode, reviewer reference |
| `schema_version.approved`                  | `schema_version`  | approval reference, approver reference, compatibility mode                |
| `schema_version.activated`                 | `schema_version`  | effective date, superseded version reference                              |
| `schema_version.deprecated`                | `schema_version`  | deprecation date, replacement reference, coexistence end                  |
| `schema_version.retired`                   | `schema_version`  | retirement date, reason code                                              |
| `schema_version.superseded`                | `schema_version`  | superseding version reference                                             |
| `schema_consumer.registered`               | `schema_consumer` | consumer reference, supported versions, domain                            |
| `schema_consumer.incompatibility_detected` | `schema_consumer` | consumer reference, schema version, reason code                           |

## 3. Migration — 11 events

| Event                              | Aggregate             | Payload carries                                                                 |
| ---------------------------------- | --------------------- | ------------------------------------------------------------------------------- |
| `migration.planned`                | `migration_plan`      | plan ID, migration IDs, class, target schemas, owner                            |
| `migration.approved`               | `migration_plan`      | approver reference, separation-of-duties evaluation reference                   |
| `migration.started`                | `migration_execution` | execution ID, plan ID, privileged grant reference                               |
| `migration.checkpointed`           | `migration_execution` | checkpoint ID, position, records processed                                      |
| `migration.completed`              | `migration_execution` | duration, records affected, verification reference                              |
| `migration.failed`                 | `migration_execution` | failure position, reason code, state preserved flag                             |
| `migration.rollback_initiated`     | `migration_execution` | rollback decision reference, reason code                                        |
| `migration.rollback_completed`     | `migration_execution` | outcome, residual state reference                                               |
| `data_backfill.started`            | `data_backfill`       | backfill ID, scope, rate limit, batch size                                      |
| `data_backfill.completed`          | `data_backfill`       | processed, succeeded, routed to review, failed; reconciliation report reference |
| `migration.verification_completed` | `migration_execution` | verification ID, outcome, evidence reference                                    |

## 4. Outbox and delivery — 10 events

| Event                                    | Aggregate             | Payload carries                                                          |
| ---------------------------------------- | --------------------- | ------------------------------------------------------------------------ |
| `outbox_record.created`                  | `outbox_record`       | outbox record ID, event ID, event type, event version                    |
| `outbox_record.dispatch_attempted`       | `outbox_record`       | attempt number, destination reference                                    |
| `outbox_record.published`                | `outbox_record`       | published-at, destination reference                                      |
| `outbox_record.acknowledgement_received` | `outbox_record`       | broker acknowledgement reference                                         |
| `outbox_record.retry_scheduled`          | `outbox_record`       | attempt number, next attempt at, reason code                             |
| `outbox_record.dead_lettered`            | `outbox_record`       | reason code, attempt count, failure reference                            |
| `event_replay.requested`                 | `event_replay`        | replay ID, scope, authority reference, reason code                       |
| `event_replay.completed`                 | `event_replay`        | replay ID, events replayed, outcome                                      |
| `consumer_checkpoint.advanced`           | `consumer_checkpoint` | consumer reference, position, previous position                          |
| `event_delivery.gap_detected`            | `consumer_checkpoint` | consumer reference, ordering scope, expected sequence, observed sequence |

## 5. Projection — 7 events

| Event                            | Aggregate    | Payload carries                                |
| -------------------------------- | ------------ | ---------------------------------------------- |
| `projection.update_requested`    | `projection` | projection ID, source event reference          |
| `projection.updated`             | `projection` | projection ID, position, schema version        |
| `projection.lag_detected`        | `projection` | projection ID, lag band, threshold reference   |
| `projection.rebuild_started`     | `projection` | rebuild ID, source range, authority reference  |
| `projection.rebuild_completed`   | `projection` | rebuild ID, outcome, records rebuilt           |
| `projection.deletion_propagated` | `projection` | source record reference, propagation outcome   |
| `projection.tombstone_applied`   | `projection` | tombstone reference, source decision reference |

---

## 6. Totals

| Family              | Count  |
| ------------------- | ------ |
| Schema registry     | 9      |
| Migration           | 11     |
| Outbox and delivery | 10     |
| Projection          | 7      |
| **Total**           | **37** |

---

## 7. What these events deliberately do not carry

`P13-EVT-005` **No schema body.** A schema event carries the digest and the
reference, never the schema document itself — payloads are minimal, and a
schema can be large.

`P13-EVT-006` **No migrated data.** A migration event carries counts and
references, never rows.

`P13-EVT-007` **No failed payload.** A dead-letter event carries a
reference to the dead-lettered record, not its contents; the contents live
in a classified, access-controlled store (`P13-DEL-014`).

`P13-EVT-008` **No query text, no personal data, no secrets** anywhere in
this catalog.

`P13-EVT-009` **`projection.lag_detected` reports a band, not an exact
lag**, for the same reason PACK-12 reports suppression bands: an exact
figure across organizations is itself information.
