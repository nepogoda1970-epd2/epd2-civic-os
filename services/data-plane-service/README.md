# data-plane-service — PACK-13 reference implementation

**Status:** FINAL PASS at repository version `0.13.0`, verified by an
external GitHub Actions run. Canon version unchanged at `0.8.0` — this
round amends no canon.

**PACK-13 FINAL PASS · EXTERNAL GITHUB ACTIONS PASS**
**NOT PRODUCTION READY · NOT LEGALLY ACTIVATED**

The bounded implementation area for PACK-13 (`Production Data Plane &
Contract Evolution`, ADR-069 through ADR-078). It is deliberately **not**
a god service: it owns the five logical contexts the specification's §3
assigns to PACK-13 itself — transactional persistence contracts, the
canonical schema registry, contract evolution, migration control, and
delivery/projection governance — and owns no other domain's data.

## What this package is

A **reference implementation**. Every adapter in `storage.py` is an
in-memory, deterministic, single-process double. The package models the
_contracts_ a production data plane must satisfy and proves the refusals
are real; it deploys no database, no broker, no schema-registry product
and no search engine.

| Module             | Responsibility                                                                                   |
| ------------------ | ------------------------------------------------------------------------------------------------ |
| `exceptions`       | One class per registered reason code, no domain knowledge                                        |
| `domain`           | Value objects, organization scope, prohibited payload keys, reserved boundaries, digest helpers  |
| `concurrency`      | Aggregate version, expected version, conflict decisions, unit-of-work and transaction boundaries |
| `idempotency`      | Scoped keys, records, decisions, deduplication and the business-fact guard                       |
| `canonicalization` | Format-specific canonical forms and the content digest (`P13-REG-005`)                           |
| `registry`         | Schema families, versions, lifecycle, ownership, publication decisions, consumers                |
| `compatibility`    | The deterministic structural checker and the semantic-risk escalation                            |
| `contracts`        | API and event contract evolution, deprecation, upcasters, consumer version support               |
| `migrations`       | Migration definitions, plans, executions, checkpoints, verification, rollback decisions          |
| `backfill`         | The deterministic, restartable, checkpointed backfill runner and its review queue                |
| `outbox`           | The transactional outbox record, statuses, delivery attempts and publication evidence            |
| `delivery`         | Dispatcher/consumer simulation, ordering scopes, dead-letter, replay, consumer checkpoints       |
| `projections`      | Projection definitions, lag, staleness, rebuild, deletion propagation, tombstones                |
| `integration`      | Search-projection and governed-export persistence contracts (PACK-12 remains the policy owner)   |
| `retention`        | Retention, deletion eligibility, legal hold and PACK-11 evidence references                      |
| `privileged`       | PACK-12 gates for migration execution, direct SQL, schema activation and operator privilege      |
| `boundaries`       | Cross-domain, audit-ingestion, identity and voting structural guards                             |
| `events`           | The thirty-seven canonical event builders, on the unchanged canon §21 envelope                   |
| `storage`          | Storage ports and in-memory reference adapters; no delete method exists on any port              |
| `application`      | The governed commands that compose the above                                                     |
| `administration`   | Contract-level reference administrative surfaces (no console, no SQL, no raw data)               |

## What this package is not

It is not a production PostgreSQL deployment, a cloud database, a real
Kafka/RabbitMQ/NATS broker, an external schema-registry product, a
production IAM, an arbitrary-SQL admin console, a multi-region topology,
or a legal activation. It implements no identity domain (PACK-14), no
voting or tally domain (PACK-15/16) and no backup recovery (PACK-17).
See `docs/handover/PACK-13-KNOWN-LIMITATIONS.md`.

## Delivery guarantee

**At-least-once delivery with effectively-once consumer effect through
idempotency.** The stronger phrase is claimed nowhere in this package,
in its documents, in its comments or in any surface it exposes, and
`tests/test_boundaries.py` scans for it.
