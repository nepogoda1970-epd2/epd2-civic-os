# PACK-13 — Reason Code Catalog

Specification-only. **No `contracts/reason-codes/pack-13.yml` is created by
this round.** The registry file is an implementation-round artifact; this
document specifies the codes it must contain.

---

## 1. Rules

`P13-RSN-001` Every refusal carries a **registered code**. Free text is not
a reason.

`P13-RSN-002` **No generic `DATA_ERROR` and no generic `CONFLICT`.** A
single code for many causes is a code that tells an operator nothing and an
auditor less.

`P13-RSN-003` Codes are **upper case**, prefixed by family.

`P13-RSN-004` A code's **meaning never changes** (`P13-API-007`). A new
meaning is a new code.

`P13-RSN-005` Codes reused from earlier packs keep their original owner and
meaning; PACK-13 does not shadow them with prefixed duplicates.

---

## 2. Schema and contract — `SCHEMA_*`

| Code                                              | Refuses                                                                                                         |
| ------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `SCHEMA_INCOMPATIBLE`                             | The proposed version is incompatible under the declared mode                                                    |
| `SCHEMA_COMPATIBILITY_UNKNOWN`                    | The checker could not classify; manual review required                                                          |
| `SCHEMA_OWNER_MISSING`                            | No registered owner; publication refused                                                                        |
| `SCHEMA_NOT_APPROVED`                             | Activation attempted before approval                                                                            |
| `SCHEMA_DIGEST_MISMATCH`                          | The content does not match the recorded `content_digest`                                                        |
| `SCHEMA_DUPLICATE_CONTENT`                        | Content identical to a registered version after canonicalization; accidental republication blocked              |
| `SCHEMA_DUPLICATE_CONTENT_REVIEW_REQUIRED`        | Identical content submitted as a new version without a `governance_justification`; reason-coded review required |
| `SCHEMA_IDENTICAL_CONTENT_REPUBLICATION_APPROVED` | Identical content deliberately bound to a new governed version, with justification recorded                     |
| `SCHEMA_VERSION_IDENTITY_IMMUTABLE`               | An attempt to re-point, merge or rewrite a historical `schema_version_id` because of digest equality            |
| `SCHEMA_GOVERNANCE_JUSTIFICATION_MISSING`         | A governed re-issue lacks its justification                                                                     |
| `SCHEMA_EXAMPLES_INVALID`                         | The schema's own fixtures do not validate against it                                                            |
| `SCHEMA_LIFECYCLE_TRANSITION_FORBIDDEN`           | The requested lifecycle transition is not declared                                                              |
| `SCHEMA_RETIRED`                                  | A retired version was used for new traffic                                                                      |
| `SCHEMA_REGISTRY_UNAVAILABLE`                     | The registry could not be reached; publication blocked                                                          |
| `CONSUMER_NOT_READY`                              | A registered consumer has not migrated                                                                          |
| `CONSUMER_NOT_REGISTERED`                         | The consumer receives no compatibility protection                                                               |
| `BREAKING_CHANGE_NOT_APPROVED`                    | A breaking change lacks its required approval                                                                   |
| `DEPRECATION_WINDOW_INCOMPLETE`                   | Retirement attempted before the window elapsed                                                                  |
| `SEMANTIC_REVIEW_REQUIRED`                        | An invisible-class change requires human assessment                                                             |
| `LEGAL_REVIEW_REQUIRED`                           | The change touches legal effect or retention semantics                                                          |
| `SECURITY_REVIEW_REQUIRED`                        | The change touches authorization implication or identity linkage                                                |

## 3. Migration — `MIGRATION_*`

| Code                                      | Refuses                                             |
| ----------------------------------------- | --------------------------------------------------- |
| `MIGRATION_CHECKSUM_MISMATCH`             | An applied migration's content changed              |
| `MIGRATION_ORDER_INVALID`                 | Ordering position conflicts with applied state      |
| `MIGRATION_ALREADY_APPLIED`               | Re-application attempted                            |
| `MIGRATION_NOT_APPROVED`                  | A class requiring approval lacks it                 |
| `MIGRATION_SEPARATION_OF_DUTIES_MISSING`  | Proposer and approver are the same subject          |
| `MIGRATION_PARTIAL_FAILURE`               | Execution halted mid-way; state preserved           |
| `MIGRATION_DRY_RUN_MISSING`               | No dry-run evidence                                 |
| `MIGRATION_DESTRUCTIVE_NOT_AUTHORIZED`    | Destructive step without its separate approval      |
| `MIGRATION_OBSERVATION_PERIOD_INCOMPLETE` | Contract step attempted too early                   |
| `MIGRATION_SCOPE_LOSS_DETECTED`           | Organizational scope would be lost                  |
| `MIGRATION_HOLD_STATE_UNKNOWN`            | Legal-hold state could not be resolved; fail closed |
| `MIGRATION_EVIDENCE_LINKAGE_BROKEN`       | Document/evidence linkage would break               |
| `MIGRATION_GLOBAL_IDENTIFIER_PROHIBITED`  | The migration would create a global user identifier |
| `MIGRATION_VOTING_UNLINKABILITY_AT_RISK`  | The migration would weaken ballot unlinkability     |
| `ROLLBACK_UNAVAILABLE`                    | No tested rollback; forward-fix only                |
| `MANUAL_SQL_PROHIBITED`                   | Direct SQL outside a governed context               |

## 4. Backfill — `BACKFILL_*`

| Code                             | Refuses                                                       |
| -------------------------------- | ------------------------------------------------------------- |
| `BACKFILL_CONFLICT`              | Target already populated with a different value               |
| `BACKFILL_SOURCE_INCOMPLETE`     | The source lacks a fact the target requires; routed to review |
| `BACKFILL_INVARIANT_VIOLATION`   | The written record would violate a domain invariant           |
| `BACKFILL_CHECKPOINT_LOST`       | Resume position unavailable                                   |
| `BACKFILL_RECONCILIATION_FAILED` | Counts do not reconcile                                       |

## 5. Concurrency and idempotency — `CONCURRENCY_*`, `IDEMPOTENCY_*`

| Code                                            | Refuses                                                              |
| ----------------------------------------------- | -------------------------------------------------------------------- |
| `CONCURRENCY_STALE_AGGREGATE_VERSION`           | Expected version does not match actual                               |
| `CONCURRENCY_APPROVAL_ON_CHANGED_VERSION`       | The aggregate moved since the approver saw it                        |
| `CONCURRENCY_LAST_WRITE_WINS_PROHIBITED`        | The record class forbids overwrite resolution                        |
| `CONCURRENCY_AUTHORITY_LAPSED`                  | Effective-dated authority expired between construction and execution |
| `IDEMPOTENCY_KEY_REUSED_WITH_DIFFERENT_PAYLOAD` | Same key, different content                                          |
| `IDEMPOTENCY_KEY_SCOPE_INVALID`                 | Key is not scoped to a domain and operation                          |
| `IDEMPOTENCY_RECORD_EXPIRED`                    | The window closed; the business-fact guard governs                   |
| `IDEMPOTENCY_GLOBAL_IDENTIFIER_PROHIBITED`      | The key derives from a global user identifier                        |

## 6. Delivery — `DELIVERY_*`, `EVENT_*`

| Code                                | Refuses / classifies                               |
| ----------------------------------- | -------------------------------------------------- |
| `EVENT_DUPLICATE_SUPPRESSED`        | A duplicate was absorbed                           |
| `EVENT_ORDERING_GAP_DETECTED`       | A sequence gap in the ordering scope               |
| `EVENT_OUT_OF_ORDER`                | An event arrived behind the checkpoint             |
| `EVENT_VERSION_UNSUPPORTED`         | The consumer supports no such version; fail closed |
| `EVENT_POISON_MESSAGE`              | Deterministic failure across attempts              |
| `EVENT_DEAD_LETTER_REQUIRED`        | Retry exhausted                                    |
| `EVENT_REPLAY_NOT_AUTHORIZED`       | Replay without authority or scope                  |
| `OUTBOX_PUBLICATION_PENDING`        | Committed but not yet published                    |
| `OUTBOX_BACKLOG_THRESHOLD_EXCEEDED` | Backlog past its alert threshold                   |
| `BROKER_UNAVAILABLE`                | The broker could not be reached                    |
| `DELIVERY_ACKNOWLEDGEMENT_MISSING`  | Dispatched, acknowledgement unknown                |

## 7. Projection — `PROJECTION_*`

| Code                                           | Refuses                                                     |
| ---------------------------------------------- | ----------------------------------------------------------- |
| `PROJECTION_STALE`                             | Lag exceeds the freshness a consequential decision requires |
| `PROJECTION_REBUILD_REQUIRED`                  | The projection cannot serve until rebuilt                   |
| `PROJECTION_REBUILD_FAILED`                    | Rebuild did not complete                                    |
| `PROJECTION_DELETION_NOT_PROPAGATED`           | A source deletion has not reached the projection            |
| `PROJECTION_AUTHORIZATION_WIDENING_PROHIBITED` | The projection would expose more than its sources           |
| `PROJECTION_NOT_AUTHORITATIVE`                 | A legal-effect decision attempted against a read model      |

## 8. Data plane and boundary — `DATAPLANE_*`

| Code                                            | Refuses                                                                                                                        |
| ----------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| `DATAPLANE_CROSS_DOMAIN_DIRECT_ACCESS_DENIED`   | A direct read or write across a domain boundary                                                                                |
| `DATAPLANE_AUDIT_DIRECT_WRITE_DENIED`           | A non-owner domain attempted to write audit persistence directly instead of submitting through the governed ingestion contract |
| `DATAPLANE_AUDIT_INGESTION_CONTRACT_REQUIRED`   | An audit record arrived by a path other than the ingestion port, API or versioned command                                      |
| `DATAPLANE_RESERVED_BOUNDARY_SCHEMA_PROHIBITED` | A schema was proposed for a reserved future boundary whose owner is not yet established                                        |
| `DATAPLANE_ORGANIZATION_SCOPE_MISSING`          | A scoped record without scope                                                                                                  |
| `DATAPLANE_GLOBAL_USER_IDENTIFIER_PROHIBITED`   | A structure that would correlate a person across domains                                                                       |
| `DATAPLANE_VOTING_MATERIAL_PROHIBITED`          | Ballot, credential or tally material in the general plane                                                                      |
| `DATAPLANE_RAW_EXPORT_PROHIBITED`               | An export route bypassing PACK-12                                                                                              |
| `DATAPLANE_OPERATOR_PRIVILEGE_INSUFFICIENT`     | Cluster privilege presented as domain-content authority                                                                        |
| `DATAPLANE_DATABASE_UNAVAILABLE`                | The database could not be reached                                                                                              |
| `DATAPLANE_REPLICA_STALE`                       | A consequential read against a stale replica                                                                                   |

## 9. Reused from earlier packs

| Code                                 | Owner   | Reused for                           |
| ------------------------------------ | ------- | ------------------------------------ |
| `RECORD_UNDER_LEGAL_HOLD`            | PACK-09 | Deletion blocked by hold             |
| `LEGAL_HOLD_STATE_UNKNOWN`           | PACK-09 | Hold state unresolvable; fail closed |
| `ORGANIZATION_SCOPE_UNDETERMINED`    | PACK-09 | Scope not resolvable                 |
| `ORGANIZATION_SCOPE_MISMATCH`        | PACK-08 | Cross-scope act refused              |
| `PERMISSION_DENIED`                  | PACK-02 | Generic authorization refusal        |
| `VALIDATION_RECORD_NOT_FOUND`        | PACK-02 | Record absent or out of scope        |
| `OPTIMISTIC_CONCURRENCY_CONFLICT`    | PACK-09 | Generic version conflict             |
| `AUDIT_CHAIN_BROKEN`                 | PACK-02 | Chain verification failure           |
| `PRIVILEGE_AUTHORITY_MISSING`        | PACK-12 | Migration or SQL without a grant     |
| `GOVERNED_RECORD_DELETION_FORBIDDEN` | PACK-09 | Deletion of a governed record        |

## 10. Codes for successfully-audited acts

`P13-RSN-006` Canon §24 is refusal-only. Acts that **succeed** still need a
registered classification for their audit rows — the same gap ADR-004
recorded for PACK-02. The implementation round registers a `*_RECORDED`
code for each governed act in §2–§8 of the event catalog.

## 11. Count

| Family                                | Codes  |
| ------------------------------------- | ------ |
| `SCHEMA_*` / contract                 | 21     |
| `MIGRATION_*`                         | 16     |
| `BACKFILL_*`                          | 5      |
| `CONCURRENCY_*` / `IDEMPOTENCY_*`     | 8      |
| `DELIVERY_*` / `EVENT_*` / `OUTBOX_*` | 11     |
| `PROJECTION_*`                        | 6      |
| `DATAPLANE_*`                         | 11     |
| Reused                                | 10     |
| **Total specified**                   | **88** |

plus the `*_RECORDED` classifications the implementation round derives from
the 37 events.
