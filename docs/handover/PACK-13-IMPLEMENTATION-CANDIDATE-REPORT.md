# PACK-13 — Implementation Candidate Report

**Round:** PACK-13 — Production Data Plane & Contract Evolution,
implementation round.
**Baseline:** `EPD2_PACK-12_PRIVILEGED_ADMIN_SEARCH_EXPORT_0.12.0_FINAL_PASS.zip`
(PACK-01 through PACK-12: FINAL PASS).
**Accepted specification:** `EPD2_PACK-13_PRODUCTION_DATA_PLANE_CONTRACT_EVOLUTION_0.13.0_SPEC_ADR_CORRECTED.zip`
— `PACK-13-SPECIFICATION.md`, ten matrices and ADR-069 through ADR-078.

```text
PACK-13 IMPLEMENTATION CANDIDATE
REPOSITORY_VERSION 0.13.0
CANON_VERSION 0.8.0
NOT PASS
NOT PRODUCTION READY
NOT LEGALLY ACTIVATED
```

The specification round's own report,
`docs/handover/PACK-13-SPEC-ADR-REPORT.md`, is retained **unchanged** and
is deliberately not rewritten as an implementation report. It records what
that round decided; this document records what this round built.

---

## 1. What this round is

An implementation candidate. Not a PASS: the external GitHub Actions
pipeline has not run against it, and the local run in this environment was
incomplete for reasons stated exactly in section 9.

The governing sentence of the specification is the governing sentence of
the implementation:

> **The data plane is infrastructure. It is not an authority.** Persistence
> must not create a capability that the domain layer refuses.

Everything built this round is an elaboration of that. The package's value
is not that it stores anything — it stores nothing durable — but that it
makes the shortcuts a real data plane invites either impossible to express
or reason-coded refusals: a cross-domain write, a person key in an
idempotency key, a projection that widens authorization, a migration that
drops organizational scope, a schema republication that silently merges
into an earlier version, an export route that is not the governed one.

## 2. Scope

The thirteen areas §1 of the specification names, implemented in
**reference form** inside one bounded implementation area,
`services/data-plane-service`. Reference form means: the models, the
governed workflows, the gates and the refusals are real and tested; the
production data plane is not deployed and is not claimed.

**Deliberately out of scope, and absent:** production PostgreSQL
deployment, any real cloud database, a real Kafka/RabbitMQ/NATS broker, an
external schema-registry product, production IAM, PACK-14 identity,
PACK-15/16 voting, PACK-17 backup recovery, an arbitrary-SQL admin
console, real destructive production migrations, multi-region
infrastructure and legal activation. `tests/test_boundaries.py` asserts
structurally that no broker client is imported anywhere in the package.

## 3. Implemented modules

Twenty-two source modules, in dependency order. Each imports only from
those above it.

| Module             | What it owns                                                                                                                                                                                                                                                       |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `exceptions`       | One class per registered reason code. No generic `DATA_ERROR`, no generic `CONFLICT` (`P13-RSN-002`)                                                                                                                                                               |
| `domain`           | Scope, ownership, typed references, the four prohibited-key families, reserved boundaries, digest helpers, the delivery-guarantee constant                                                                                                                         |
| `concurrency`      | `AggregateVersion`, `ExpectedVersion` with three distinct kinds, `ConcurrencyDecision`, `ConcurrencyConflict`, `TransactionBoundary`, `UnitOfWorkReference`, `CommandExecutionReference`                                                                           |
| `idempotency`      | `IdempotencyKey`, `IdempotencyScope`, `IdempotencyRecord`, `IdempotencyDecision`, `DeduplicationRecord`, `BusinessFactGuard`                                                                                                                                       |
| `canonicalization` | Format-specific canonical forms, the content digest, the enumerated removed differences and the enumerated non-normalizations                                                                                                                                      |
| `registry`         | `SchemaFamily`, `SchemaDefinition`, `SchemaVersion`, `SchemaOwner`, lifecycle, `CompatibilityMode`, `SchemaPublicationDecision`, `SchemaDeprecation`, `SchemaSupersession`, `ConsumerRegistration`, `MigrationReference`, the three duplicate-content dispositions |
| `compatibility`    | The deterministic structural differ, eight semantic-risk classes, separate automated and human verdicts, the mode check                                                                                                                                            |
| `contracts`        | `ApiContract`, `ApiVersion`, `ApiDeprecation`, `ConsumerCompatibilityStatus`, `ApiMigrationPlan`, `BreakingChangeRecord`, `EventContractVersion`, `EventCompatibilityAssessment`, `EventUpcasterReference`, `EventConsumerVersionSupport`                          |
| `migrations`       | `MigrationDefinition`, `MigrationPlan`, `MigrationExecution`, `MigrationCheckpoint`, `MigrationVerification`, `MigrationRollbackDecision`, `DataBackfillReference`, the five automated gates, expand/contract                                                      |
| `backfill`         | The deterministic, restartable, checkpointed, rate-limited runner, its review queue and its reconciliation report                                                                                                                                                  |
| `outbox`           | `OutboxRecord`, `OutboxStatus`, `DeliveryAttempt`, `PublicationEvidence`, `BrokerAcknowledgementReference`, the writer that only works inside a unit of work                                                                                                       |
| `delivery`         | Ordering scopes and gap detection, `ConsumerCheckpoint`, `DispatchDecision`, `DeadLetterRecord`, `ReplayReference`, `RetryPolicy`, the reference dispatcher, broker double and idempotent consumer                                                                 |
| `projections`      | `ProjectionDefinition`, `ProjectionSource`, `ProjectionCheckpoint`, `ProjectionLag`, `ProjectionStaleness`, `ProjectionRebuild`, `DeletionTombstone`, `ProjectionEvidence`, `ProjectedRow`                                                                         |
| `integration`      | Search-projection versions, tombstones, index-removal evidence, reindex; export request, manifest, artifact, delivery, access, revocation, destruction attestation, release history; the closed export-route list                                                  |
| `retention`        | Infrastructure persistent classes, retention bindings, the three-valued legal-hold state, deletion eligibility, deletion evidence, the backup-horizon statement, PACK-11 evidence references                                                                       |
| `privileged`       | Data-plane roles and their incompatible pairs, scoped-grant checks, separation of duties, the SQL-context gate, break-glass, privileged action records                                                                                                             |
| `boundaries`       | Table ownership and the four admissible integration mechanisms, the audit-ingestion contract, scoped subject references, the seven voting prohibitions                                                                                                             |
| `events`           | The thirty-seven canonical event builders and the `*_RECORDED` derivation                                                                                                                                                                                          |
| `storage`          | Storage ports and in-memory adapters. **No delete method exists on any port**                                                                                                                                                                                      |
| `application`      | The governed commands that compose the above                                                                                                                                                                                                                       |
| `administration`   | The seven contract-level administrative surfaces and the observability contracts                                                                                                                                                                                   |
| `__init__`         | The package contract, the module map and the status constants                                                                                                                                                                                                      |

### 3.1 Models

Every model group §7 of the implementation task enumerates is present.
Transaction and concurrency (8), outbox and delivery (9), idempotency (5),
schema registry (12), API and event evolution (9), migrations (7) and
projections (8) — with the seven registry fields §7.4 requires to stay
separate genuinely separate: `content_digest`, `schema_version_id`,
`publication_decision_id`, `effective_at`, `deprecated_at`,
`supersession_reference` and `governance_justification`.

### 3.2 Adapters

In-memory, deterministic, single-process. `ReferenceUnitOfWork` simulates
`P13-TX-003`'s atomicity well enough to make the outbox contract testable
and no further — it has no isolation, no durability and no recovery, and
says so. `InMemoryAggregateVersionStore` states in its own docstring that
it is not concurrency-safe rather than implying otherwise.

Storage rules enforced _by the store_: owner-controlled writes,
scope-filtered reads, append-only applied migrations, append-only schema
version identity, outbox records mutable only in their delivery metadata,
and no delete method anywhere.

### 3.3 Services

`DataPlaneCommandService` (concurrency, idempotency, atomic commit,
event), `SchemaRegistryService` (the nine-check publication path,
activation, consumer readiness), `MigrationService` (gates, applied state,
checksums), `BackfillService`, `DeliveryService`, `ProjectionService`, and
`submit_audit_record` — the one integration path other domains use to
reach audit.

## 4. Tests

**555 tests in twenty test modules**, all deterministic: the package holds
no clock and mints no UUID, so every timestamp and identifier is supplied
by the caller and every run is byte-identical.

| Group                    | File                             | Covers                                                                                                                                                      |
| ------------------------ | -------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Ownership and boundaries | `test_boundaries.py`             | Owner-only writes, the closed integration list, the audit-ingestion contract, identity separation, the seven voting prohibitions, the forbidden-phrase scan |
| Concurrency              | `test_concurrency.py`            | Expected-version success and conflict, no last-write-wins, approval bound to a version, transaction boundaries                                              |
| Outbox                   | `test_outbox.py`                 | Atomic commit, rollback leaving no event, retry preserving the event ID, duplicate-append safety, delivery evidence                                         |
| Idempotency              | `test_idempotency.py`            | Same key/same payload, same key/different payload, scoped keys, consequential expiry                                                                        |
| Schema registry          | `test_registry.py`               | Lifecycle, ownership, digest canonicalization, digest/version separation, duplicate-content review, justified republication, deprecation and supersession   |
| Canonicalization         | `test_canonicalization.py`       | Per-format canonical forms, cross-format digest non-comparison, fixture validation                                                                          |
| Compatibility            | `test_compatibility.py`          | Additive, required, removed, type change, enum extension, semantic-risk review, reason-code semantics                                                       |
| Contract evolution       | `test_contracts.py`              | API identity, field reuse, privilege widening, deprecation windows, upcaster determinism, unknown enums                                                     |
| Migrations               | `test_migrations.py`             | Immutability, checksum mismatch, ordering, expand/contract, the destructive gate, the five automated gates                                                  |
| Backfill                 | `test_backfill.py`               | Determinism, restart, checkpoint, review routing, reconciliation                                                                                            |
| Delivery                 | `test_delivery.py`               | Duplicate, out-of-order, gap, unsupported version, poison, dead-letter, replay, checkpoints, lag bands                                                      |
| Projections              | `test_projections.py`            | Rebuild, lag, stale state, deletion propagation, legal hold, authorization preservation                                                                     |
| Search and export        | `test_integration.py`            | The three search versions, tombstones, and the closed export-route list                                                                                     |
| Retention                | `test_retention.py`              | Infrastructure bindings, the three-valued hold, fail-closed deletion, the backup statement, evidence                                                        |
| Privileged               | `test_privileged.py`             | Scoped grants, separation of duties, no universal DBA, no ad-hoc SQL, break-glass obligations                                                               |
| Events                   | `test_events.py`                 | Thirty-seven types, the unchanged envelope, payload minimisation, `*_RECORDED` derivation                                                                   |
| Storage                  | `test_storage.py`                | No delete method, append-only stores, scope filters, tombstones                                                                                             |
| Application              | `test_data_plane_application.py` | The composed command, publication, migration, backfill, delivery and projection paths                                                                       |
| Administration           | `test_administration.py`         | Seven surfaces, no SQL, no production claim, telemetry guards                                                                                               |
| Domain                   | `test_domain.py`                 | The four prohibited-key families, scope, reserved boundaries, references                                                                                    |

Plus `tests/repository/test_pack13_fir_matrix.py`, which asserts
structurally that the FIR coverage matrix contains no `implemented`
treatment value (`AC-P13-155`).

**The named test §9 of the implementation task requires** — _No non-owner
domain credential can write directly to audit-core persistence_ — is
`test_no_non_owner_domain_credential_can_write_audit_persistence_directly`
in `test_boundaries.py`, and the guard is on `ApplicationCredential`'s
constructor: such a credential cannot be built.

## 5. ADR-069 — ADR-078 mapping

| ADR                                            | Reference implementation                                                                                                                          |
| ---------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| ADR-069 Production relational data plane       | `domain` (scope, classification, record-class references), `storage` (domain-owned stores), `boundaries` (no shared schema, no global person key) |
| ADR-070 Domain data ownership                  | `boundaries.TableOwnership`, `INTEGRATION_MECHANISMS`, `AuditIngestionPort`, `ApplicationCredential`; the outbox co-located per domain            |
| ADR-071 Transactional outbox                   | `outbox`, `storage.ReferenceUnitOfWork`; transport metadata on the record, never on the envelope                                                  |
| ADR-072 At-least-once and idempotent consumers | `delivery`, `idempotency`; the forbidden-phrase scan                                                                                              |
| ADR-073 Canonical schema registry              | `registry`, `canonicalization`; digest and identity separate; the three duplicate-content dispositions                                            |
| ADR-074 API and event contract evolution       | `compatibility`, `contracts`; two verdicts, eight invisible classes, upcasters that invent nothing                                                |
| ADR-075 Database migration discipline          | `migrations`, `backfill`; five automated gates, no repair path                                                                                    |
| ADR-076 Projection and read-model governance   | `projections`; not authoritative, no widening, no hidden cross-domain database, no identity bridge                                                |
| ADR-077 Concurrency and idempotency            | `concurrency`, `idempotency`; three expected-version kinds, the permanent business-fact guard                                                     |
| ADR-078 Retention, legal hold and evidence     | `retention`; infrastructure is not exempt, a hold authorizes nothing, evidence is PACK-11's                                                       |

## 6. FIR treatment

`FIR-ROADMAP-003` moves from `approved` to **`scheduled`** and no
further. It is **not** `implemented`, for two independent reasons either
of which alone would be sufficient: this is a candidate that no external
pipeline has passed, and every storage adapter in it is in memory.

`docs/packs/PACK-13/PACK-13-FIR-COVERAGE-MATRIX.md` still records
**zero** `implemented` values. Its implementation-coverage appendix says,
per entry, what the candidate built and what remains open.
`FIR-INV-001`, `FIR-INV-006`, `FIR-INV-013`, `FIR-INV-014`,
`FIR-INV-015`, `FIR-DATA-001`, `FIR-DATA-003`, `FIR-INV-007` and
`FIR-INV-011` receive a reference-form foundation and none is closed.
`FIR-INV-002`, `FIR-INV-003`, `FIR-INV-004` and `FIR-INV-005` are
untouched: their remainder is PACK-15/16's.

Production-infrastructure, identity, voting and backup items in the
register remain future, unchanged.

### 6.1 The programme-presentation requirement (documentation correction)

A review of the first candidate archive found that one approved
requirement was absent from
`docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md`: the public
presentation of the adopted programme and its projects. It had been
approved before this round began but had never been written into the
register, so the instruction not to delete it was given against a baseline
that did not contain it — there was nothing to preserve, and its absence
was not detectable from inside the round.

It is now recorded as **`FIR-PROG-003` — Public Presentation of Adopted
Programme and Projects**, section 17, status `approved`, domain _public
website / program formation / governed publication_, target _future Public
Website and Program Formation frontend packages_.

Its substance: the adopted programme is the primary content of the public
`Programm` page, with its exact text in force, version, adoption date,
competent body, manner of adoption, entry into force, decision reference,
change history and archived previous versions directly available; public
projects are not rendered as a full list beside it; a single compact
`Projekte in Beratung` card per thematic section carries the count, the
explicit `Noch nicht beschlossen` marking and a link to a separate
projects page; a separate all-projects page exists; and the adopted/not-
adopted distinction is carried simultaneously by textual status, page
structure, card shape, an accessible visual marker and different
actions — never by colour alone.

**It is preserved in the register and remains outside PACK-13's scope.**
It is a **future frontend obligation**, not a PACK-13 FIR, not implemented
by this round, and not a basis for treating Program Formation or the
Public Website as complete. Nothing in `services/data-plane-service`
presents, orders or renders programme content: no model, event, reason
code or contract in it touches what `FIR-PROG-003` governs.

This correction is documentation-only. No code, test, CI configuration,
ADR, PACK-13 architecture decision, repository version or canon version
changed.

## 7. Acceptance coverage

`docs/packs/PACK-13/PACK-13-ACCEPTANCE-MATRIX.md` gains an
implementation-status appendix covering all **176** criteria, each with
its implemented component, test file, evidence, status and deferred
dependency.

| Status                                | Criteria |
| ------------------------------------- | -------- |
| implemented and tested                | 120      |
| reference implementation              | 50       |
| deferred to production infrastructure | 4        |
| blocked by PACK-15/16                 | 1        |
| blocked by PACK-14 and PACK-15/16     | 1        |

**Met by this round: 0.** A candidate satisfies no acceptance criterion by
its own assertion.

## 8. Deferred production infrastructure and pack dependencies

**Deferred to production infrastructure:** the production
PostgreSQL-compatible deployment and its per-domain grants; the production
event broker; the production schema-registry deployment; the production
search index; database-level enforcement of immutable-history tables; a
live catalog conformance report; a role inventory; infrastructure-level
egress control; saga/process-manager machinery; and downcasting, which no
current contract needs.

**PACK-14:** the identity boundary's owner, and the residual that a
superuser can read what the engine decrypts.
**PACK-15/16:** the eligibility, credential, voting and tally boundaries'
owners; the voting architecture's own threat model, isolation and
unlinkability demonstration; and every topology question `P13-VOTE-008`
reserves — broker topics, broker deployment arrangement, connection-pool
topology, service names, credential topology and transport provider.
**PACK-17:** backup and restore, and with them the deletion gap that a
record present in backups is not deleted.
**PACK-09, PACK-11, PACK-12:** retention decisions, evidence bundles, and
search/export/privileged policy respectively. PACK-13 binds and observes;
it decides none of them.
**FRONT-PACK:** every rendered surface and the accessibility obligation.

## 9. Verification results

Run in this environment, which has **no network access to PyPI or npm**.
`make setup` (`uv sync --all-groups`, `npm install`) therefore could not
run, and neither could `make verify` as a whole. The stages were run
individually with the tooling that is available. **No stage is reported
below as passing that did not run.**

| Stage                                                   | Result                          | Notes                                                                                                             |
| ------------------------------------------------------- | ------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `scripts/check_repository.py`                           | **PASS**                        | Every required path present, including the 72 added for PACK-13                                                   |
| `scripts/check_forbidden_files.py`                      | **PASS**                        | No forbidden path among git-trackable files                                                                       |
| `scripts/verify_versions.py`                            | **PASS**                        | `0.13.0` and `0.8.0` consistent across all five declaration sites                                                 |
| `scripts/check_canon_0_8_0.py`                          | **PASS**                        | All 18 canon-amendment checks. Not part of `make verify`; run because it verifies that this round amends no canon |
| `ruff format --check .`                                 | **PASS**                        | 347 files already formatted                                                                                       |
| `ruff check .`                                          | **PASS**                        | All checks passed                                                                                                 |
| `mypy` (all 23 groups)                                  | **PASS**                        | Including `services/data-plane-service`: 44 source files, no issues                                               |
| `pytest` (whole repository)                             | **PASS**                        | 4616 passed, 5 skipped, 0 failed                                                                                  |
| `npm run format:check` (Prettier)                       | **PASS, with a version caveat** | See below                                                                                                         |
| `npm run lint` (ESLint)                                 | **DID NOT RUN**                 | Requires `node_modules`; `npm install` is blocked                                                                 |
| `npm run typecheck` (TypeScript)                        | **DID NOT RUN**                 | Same                                                                                                              |
| `npm run test` (TypeScript package)                     | **DID NOT RUN**                 | Same                                                                                                              |
| `npm run test` (frontend)                               | **DID NOT RUN**                 | Same                                                                                                              |
| `npm run build` (frontend)                              | **DID NOT RUN**                 | Same                                                                                                              |
| `npm run test:browser` (browser, accessibility, visual) | **DID NOT RUN**                 | Same                                                                                                              |

**The Prettier caveat, stated precisely.** `package.json` pins
`prettier@^3.3.0` and `package-lock.json` records the resolution CI uses.
No `node_modules` could be installed here, so `npm run format:check` ran
against a Prettier **3.8.1** binary available on this machine — a
different resolution from the pinned one. Under 3.8.1 every file in the
repository formats clean **except three pre-existing baseline files**
(`docs/adr/ADR-051-…md`,
`frontend/web-shell/foundation/storage-policy.ts`,
`frontend/web-shell/foundation/types.ts`), which 3.8.1 would reformat and
which passed CI unchanged under the pinned version. Those three files were
**reverted to their baseline bytes** rather than reformatted: this round
does not rewrite PACK-01–PACK-12 files to satisfy a Prettier version CI
does not use. The consequence is honest and must be stated: **Prettier
formatting of this round's own new files is verified only against 3.8.1
and must be re-verified in CI against the pinned version.**

Two failures were found during verification and fixed rather than
reported around: `packages/python/epd2-core/tests/test_version.py` and
`packages/typescript/epd2-types/tests/version.test.ts` both pinned
`REPOSITORY_VERSION` to `0.12.0`, and both now assert `0.13.0` with the
reason recorded in the same comment style the earlier rounds used.

**This candidate is handed to the external GitHub Actions pipeline for
the stages that could not run here.** It is not a PASS and is not
described as one.

## 10. Frontend boundary

PACK-13 is not FRONT-PACK. `administration.py` provides **contract-level
view models only** for the seven administrative concerns §32 names:
schema review, compatibility result, migration status, consumer readiness,
dead-letter review, projection health and outbox backlog. There is no
route, no component, no rendered surface and no accessibility work.

No surface holds a query, a statement or a filter expression; none
returns a payload; the dead-letter surface returns identifiers and
**refuses** to open a record, pointing at the PACK-12 governed path; and
`OperationalStatus` cannot be constructed with a production-readiness or
legal-activation claim, nor with the stronger delivery phrase.

## 11. Known limitations

Fourteen, in `docs/handover/PACK-13-KNOWN-LIMITATIONS.md`. The four a
reader should not miss: every storage adapter is in memory and this is
therefore not a data plane; `ReferenceUnitOfWork` is not a transaction;
the identity guards are name-based and an opaque hash defeats them; and
the compatibility checker cannot detect an undeclared semantic change,
because no automated checker can.

## 12. File inventory

### 12.1 Added (72 files)

- `contracts/reason-codes/pack-13.yml`
- `docs/adr/ADR-069-PRODUCTION-RELATIONAL-DATA-PLANE.md`
- `docs/adr/ADR-070-DOMAIN-DATA-OWNERSHIP.md`
- `docs/adr/ADR-071-TRANSACTIONAL-OUTBOX.md`
- `docs/adr/ADR-072-AT-LEAST-ONCE-DELIVERY-AND-IDEMPOTENT-CONSUMERS.md`
- `docs/adr/ADR-073-CANONICAL-SCHEMA-REGISTRY.md`
- `docs/adr/ADR-074-API-AND-EVENT-CONTRACT-EVOLUTION.md`
- `docs/adr/ADR-075-DATABASE-MIGRATION-DISCIPLINE.md`
- `docs/adr/ADR-076-PROJECTION-AND-READ-MODEL-GOVERNANCE.md`
- `docs/adr/ADR-077-CONCURRENCY-AND-IDEMPOTENCY.md`
- `docs/adr/ADR-078-DATA-PLANE-RETENTION-LEGAL-HOLD-AND-EVIDENCE.md`
- `docs/handover/PACK-13-IMPLEMENTATION-CANDIDATE-REPORT.md`
- `docs/handover/PACK-13-KNOWN-LIMITATIONS.md`
- `docs/handover/PACK-13-SPEC-ADR-REPORT.md`
- `docs/packs/PACK-13/PACK-13-ACCEPTANCE-MATRIX.md`
- `docs/packs/PACK-13/PACK-13-CANON-ASSESSMENT.md`
- `docs/packs/PACK-13/PACK-13-DATA-OWNERSHIP-MATRIX.md`
- `docs/packs/PACK-13/PACK-13-EVENT-CATALOG.md`
- `docs/packs/PACK-13/PACK-13-EVENT-DELIVERY-MATRIX.md`
- `docs/packs/PACK-13/PACK-13-FIR-COVERAGE-MATRIX.md`
- `docs/packs/PACK-13/PACK-13-MIGRATION-CONTROL-MATRIX.md`
- `docs/packs/PACK-13/PACK-13-REASON-CODE-CATALOG.md`
- `docs/packs/PACK-13/PACK-13-SCHEMA-COMPATIBILITY-MATRIX.md`
- `docs/packs/PACK-13/PACK-13-SPECIFICATION.md`
- `docs/packs/PACK-13/PACK-13-THREAT-MODEL.md`
- `services/data-plane-service/README.md`
- `services/data-plane-service/pyproject.toml`
- `services/data-plane-service/src/epd2_data_plane_service/__init__.py`
- `services/data-plane-service/src/epd2_data_plane_service/administration.py`
- `services/data-plane-service/src/epd2_data_plane_service/application.py`
- `services/data-plane-service/src/epd2_data_plane_service/backfill.py`
- `services/data-plane-service/src/epd2_data_plane_service/boundaries.py`
- `services/data-plane-service/src/epd2_data_plane_service/canonicalization.py`
- `services/data-plane-service/src/epd2_data_plane_service/compatibility.py`
- `services/data-plane-service/src/epd2_data_plane_service/concurrency.py`
- `services/data-plane-service/src/epd2_data_plane_service/contracts.py`
- `services/data-plane-service/src/epd2_data_plane_service/delivery.py`
- `services/data-plane-service/src/epd2_data_plane_service/domain.py`
- `services/data-plane-service/src/epd2_data_plane_service/events.py`
- `services/data-plane-service/src/epd2_data_plane_service/exceptions.py`
- `services/data-plane-service/src/epd2_data_plane_service/idempotency.py`
- `services/data-plane-service/src/epd2_data_plane_service/integration.py`
- `services/data-plane-service/src/epd2_data_plane_service/migrations.py`
- `services/data-plane-service/src/epd2_data_plane_service/outbox.py`
- `services/data-plane-service/src/epd2_data_plane_service/privileged.py`
- `services/data-plane-service/src/epd2_data_plane_service/projections.py`
- `services/data-plane-service/src/epd2_data_plane_service/registry.py`
- `services/data-plane-service/src/epd2_data_plane_service/retention.py`
- `services/data-plane-service/src/epd2_data_plane_service/storage.py`
- `services/data-plane-service/tests/_data_plane_builders.py`
- `services/data-plane-service/tests/conftest.py`
- `services/data-plane-service/tests/test_administration.py`
- `services/data-plane-service/tests/test_backfill.py`
- `services/data-plane-service/tests/test_boundaries.py`
- `services/data-plane-service/tests/test_canonicalization.py`
- `services/data-plane-service/tests/test_compatibility.py`
- `services/data-plane-service/tests/test_concurrency.py`
- `services/data-plane-service/tests/test_contracts.py`
- `services/data-plane-service/tests/test_data_plane_application.py`
- `services/data-plane-service/tests/test_delivery.py`
- `services/data-plane-service/tests/test_domain.py`
- `services/data-plane-service/tests/test_events.py`
- `services/data-plane-service/tests/test_idempotency.py`
- `services/data-plane-service/tests/test_integration.py`
- `services/data-plane-service/tests/test_migrations.py`
- `services/data-plane-service/tests/test_outbox.py`
- `services/data-plane-service/tests/test_privileged.py`
- `services/data-plane-service/tests/test_projections.py`
- `services/data-plane-service/tests/test_registry.py`
- `services/data-plane-service/tests/test_retention.py`
- `services/data-plane-service/tests/test_storage.py`
- `tests/repository/test_pack13_fir_matrix.py`

### 12.2 Modified (16 files)

- `CHANGELOG.md`
- `Makefile`
- `README.md`
- `docs/adr/README.md`
- `docs/canonical/canon-version.json`
- `docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md`
- `packages/python/epd2-core/src/epd2_core/version.py`
- `packages/python/epd2-core/tests/test_version.py`
- `packages/typescript/epd2-types/src/version.ts`
- `packages/typescript/epd2-types/tests/version.test.ts`
- `pyproject.toml`
- `scripts/check_canon_0_8_0.py`
- `scripts/check_repository.py`
- `services/README.md`
- `tests/contract/_schema_helpers.py`
- `tests/contract/test_reason_codes_registry.py`

No file was deleted. One test module carries a forced name:
`services/data-plane-service/tests/test_data_plane_application.py` rather
than `test_application.py`, because
`services/document-service/tests/test_privacy_boundary.py` imports a
helper with `from test_application import Flow` — a bare module-name
import that a second `test_application` collected earlier in directory
order would shadow. Renaming here touches no earlier pack.

## 13. SHA-256 — every file added by this round

71 of the 72 added files are listed below. The one
omission is **this file**: a document cannot record its own digest, since
writing the digest into it changes the bytes the digest was taken over.
Its digest, and the archive's, are reported in the handover response
accompanying the archive.

| Path                                                                          | SHA-256                                                            |
| ----------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| `contracts/reason-codes/pack-13.yml`                                          | `0008f5ddafff420305cc291ac2a2e0085f574f056145c00c7c651376093b6417` |
| `docs/adr/ADR-069-PRODUCTION-RELATIONAL-DATA-PLANE.md`                        | `b55c6bf7f281ccf58cac54e361a24e16849c73e3d5674a429691a1aa65f6c017` |
| `docs/adr/ADR-070-DOMAIN-DATA-OWNERSHIP.md`                                   | `01ced126402f54ef238a0ffa95bde43c5adb4c475db3ac3a175598066696ad92` |
| `docs/adr/ADR-071-TRANSACTIONAL-OUTBOX.md`                                    | `27ecec8ef96a9e65f89abf00ec1cb4e050d8e9f8ad11f15b61656ffc98972a27` |
| `docs/adr/ADR-072-AT-LEAST-ONCE-DELIVERY-AND-IDEMPOTENT-CONSUMERS.md`         | `68dc00f1a257fc0ae7d1fbb7413b4e942f1c62a200d8e11e730527a9147d8254` |
| `docs/adr/ADR-073-CANONICAL-SCHEMA-REGISTRY.md`                               | `bb688fdb6eaa3ab4c93457926a1309524e98cf20c21244b5f9a2763e73d92d13` |
| `docs/adr/ADR-074-API-AND-EVENT-CONTRACT-EVOLUTION.md`                        | `a8b629fbf6afee85cbcf7bc35260860d6e517936f15af7ab496bcd1d4b8ea6a1` |
| `docs/adr/ADR-075-DATABASE-MIGRATION-DISCIPLINE.md`                           | `c1ede51f2b6e44e3e428fd0e51b50f9be79ccb1962bcb4c92d924d981447e9e5` |
| `docs/adr/ADR-076-PROJECTION-AND-READ-MODEL-GOVERNANCE.md`                    | `8e4522a5664052e468aed4bdd278fd07d0e4964d8f64a5720c2294485b4bb68b` |
| `docs/adr/ADR-077-CONCURRENCY-AND-IDEMPOTENCY.md`                             | `b9803bd5df636ccc8616fed0bbd8defaa669bc65a2a588a1417f638b6a138ae4` |
| `docs/adr/ADR-078-DATA-PLANE-RETENTION-LEGAL-HOLD-AND-EVIDENCE.md`            | `ec1205bcf0578a010bab689f16ccdcf36a63ed48c3f9fdb6259d5f486fa8499b` |
| `docs/handover/PACK-13-KNOWN-LIMITATIONS.md`                                  | `8c6d74146a3fd520eaa179c21ff0a9a5212431a28ba4a828e5300474bfeb3329` |
| `docs/handover/PACK-13-SPEC-ADR-REPORT.md`                                    | `a9f29182a6c8ce1dbe6c2a2db732f1b2010d6892f052647a115bdad8921904bf` |
| `docs/packs/PACK-13/PACK-13-ACCEPTANCE-MATRIX.md`                             | `56ca03d04f2efed5fe7c645d2ae86050138c1a08b240cdefc72fdcbfc10d3a51` |
| `docs/packs/PACK-13/PACK-13-CANON-ASSESSMENT.md`                              | `3e72cfa1966d6ab807bc6aae225f16ad9710c8e0379f47da7570395006a553a3` |
| `docs/packs/PACK-13/PACK-13-DATA-OWNERSHIP-MATRIX.md`                         | `decd441b2189c1896ed3ceb8f12b8ad15bf6c9bfc34b21ef50ee36c0fd35485f` |
| `docs/packs/PACK-13/PACK-13-EVENT-CATALOG.md`                                 | `7e7038b402c9ce8db1a774ce8a29117e0afe51c174d494e8f77d51369ba7bfc3` |
| `docs/packs/PACK-13/PACK-13-EVENT-DELIVERY-MATRIX.md`                         | `44e3e1b429a4a3bff21f2e5afde3f1120514f8aecd25f11e8cd450753ae59bcd` |
| `docs/packs/PACK-13/PACK-13-FIR-COVERAGE-MATRIX.md`                           | `42254af47f4ff8960b186471b3e6e13f48160fa2c041d6f0a7372d38f98db458` |
| `docs/packs/PACK-13/PACK-13-MIGRATION-CONTROL-MATRIX.md`                      | `09d3a716171dbfde49531c1274348291d1e4a9755668da8613ff3b18a1383fa3` |
| `docs/packs/PACK-13/PACK-13-REASON-CODE-CATALOG.md`                           | `e6e85712de7ab7999ac655dd9bdc8ebb35c32ff332f3128b5e1edd56bba47242` |
| `docs/packs/PACK-13/PACK-13-SCHEMA-COMPATIBILITY-MATRIX.md`                   | `29bcfb215b35228bc30b0130779799dae4a2190b9e1092dfa2081247b5162cb1` |
| `docs/packs/PACK-13/PACK-13-SPECIFICATION.md`                                 | `804f707c01b74a153d9331e3ff94ef3fce0643a1fba5c68a83971851152e2777` |
| `docs/packs/PACK-13/PACK-13-THREAT-MODEL.md`                                  | `a6e1651a0b941fe1a4fe3b8ebd8bb21984035ecc02b59479193222ae029d8166` |
| `services/data-plane-service/README.md`                                       | `5e09862bf132df3de1c601d1135eec2ad8c4fbd742457582db5abbfa64fa724c` |
| `services/data-plane-service/pyproject.toml`                                  | `b7da5ad1a3f9f3f1e2ccc4e8282d262fca2e52e53744c5640875af440a3ffb46` |
| `services/data-plane-service/src/epd2_data_plane_service/__init__.py`         | `3e9ecf5621f6f15fe70abbadb5da78823e40903aea7776234235769ec9defbe3` |
| `services/data-plane-service/src/epd2_data_plane_service/administration.py`   | `1c414eeeab15530ed427541cc97164186f624d66605e19535296a1c42a3fc14b` |
| `services/data-plane-service/src/epd2_data_plane_service/application.py`      | `ee3dbf88735a0c498caed77d4fbed03f955e9751e35f0dcf9bc45b9a8646ea7a` |
| `services/data-plane-service/src/epd2_data_plane_service/backfill.py`         | `bcbc32bfa1dbcbc2b3af7046ec52ad9a2bf8d71a7d209b16dfb96dd7e3e0ba80` |
| `services/data-plane-service/src/epd2_data_plane_service/boundaries.py`       | `1f91e26bf65b6b10bf61c32e7cf58e66120f11038e2eb2e2ca69f7a05b057ab2` |
| `services/data-plane-service/src/epd2_data_plane_service/canonicalization.py` | `55b66746c6d38b5e07f0fac4d657f1502c68a60647b96a0dd3413c8ba80a9f5a` |
| `services/data-plane-service/src/epd2_data_plane_service/compatibility.py`    | `06e0f5ac987b60e0fd79405ef0ee85a2b1cf54c53678ec6f96f41c9e28e8483c` |
| `services/data-plane-service/src/epd2_data_plane_service/concurrency.py`      | `19e11fed42fe0a607f861d507478de45bf2bcb4ece58701f9a105327c09c16cf` |
| `services/data-plane-service/src/epd2_data_plane_service/contracts.py`        | `bd63b39711c62c12ee6d7e7dbcfbb9f4b090552c2dc96a88523ee806127177bd` |
| `services/data-plane-service/src/epd2_data_plane_service/delivery.py`         | `a85c6aa4a24cc8c840d204513b02df630f6c005207ad0e90d2219a2936debec9` |
| `services/data-plane-service/src/epd2_data_plane_service/domain.py`           | `435ce8074ac6b811b6b4a084084d21d757ca60025a7b3bed527a453bca6a7a86` |
| `services/data-plane-service/src/epd2_data_plane_service/events.py`           | `a967def5a8c35ac6847d0b8cfe50d4c9b52751fc25942d92601b939f2a96d7d2` |
| `services/data-plane-service/src/epd2_data_plane_service/exceptions.py`       | `fcf66f34481bb1540684d3cd364ec53db8eac2956656d54a3d5b36dce4224c66` |
| `services/data-plane-service/src/epd2_data_plane_service/idempotency.py`      | `4e451b539893d5b2b5b16d7dd27af6f7c353730790ac275142182555e2118472` |
| `services/data-plane-service/src/epd2_data_plane_service/integration.py`      | `b96e86fbe6309c8e2b84f3511ebe7e7dc51e8c8d655bfb8d098afeeeabcbe6ec` |
| `services/data-plane-service/src/epd2_data_plane_service/migrations.py`       | `a542be10366e030b609338a5653c0ab587721607002afd10ef00f6f64161bf08` |
| `services/data-plane-service/src/epd2_data_plane_service/outbox.py`           | `04ae768586975ef6b252c1cf6684e85a3d7484614a7e9bcb02a4adcd6ce56886` |
| `services/data-plane-service/src/epd2_data_plane_service/privileged.py`       | `bfcaa224d4c58f2c77990e37530c89d9e2cb7efa5dec91a93185de5628ffae70` |
| `services/data-plane-service/src/epd2_data_plane_service/projections.py`      | `3ca66a63d67bd394c65d81775c502d3ba11ba4df4c6bba4fd2fd797381ea4f03` |
| `services/data-plane-service/src/epd2_data_plane_service/registry.py`         | `0a44598faed5d8ba2ccd0871a57dda1ebfb62fe880fd1b793c2db612fbcc83f0` |
| `services/data-plane-service/src/epd2_data_plane_service/retention.py`        | `dcecd4d629ceed3806a3142ae927cb370010346adac23b04be263b6f18dac2a4` |
| `services/data-plane-service/src/epd2_data_plane_service/storage.py`          | `21071126e7fb3cef518eadea311041eeb2defe395a8b959ff14bb01100482bc4` |
| `services/data-plane-service/tests/_data_plane_builders.py`                   | `3076c7d3b61100a1e686bdb92c8d0b20329a7d3f1cafc53bc26c1d44093ed1f8` |
| `services/data-plane-service/tests/conftest.py`                               | `777744cfcd6962efd718e5779c49af5bec908d1d0617d14f183fa2f7fb989869` |
| `services/data-plane-service/tests/test_administration.py`                    | `57910225e52227f3e08e855b05b748ccbb9da812446b06097bb31910c6f2e1f6` |
| `services/data-plane-service/tests/test_backfill.py`                          | `1c528f736398558d968d3e5c42d5d89331fbc32c26c37cc3671381a6e696e663` |
| `services/data-plane-service/tests/test_boundaries.py`                        | `c386a20c6951032ed95b412e585a71c1bbe01d4b00b1c0e35ed1d0af3a0a22d7` |
| `services/data-plane-service/tests/test_canonicalization.py`                  | `c79fa531554c0c69d9b59bd94afea56c71e3a01a652e2f33c844f93ebf7bfc3d` |
| `services/data-plane-service/tests/test_compatibility.py`                     | `43aec17119c6336e05954947383d7b7e2fa4a9729f822938d29dfa41393ae5fd` |
| `services/data-plane-service/tests/test_concurrency.py`                       | `d9696b734e36cd8db81b619dfdc0b51f3cd67aee894f1e750648c8472abc81eb` |
| `services/data-plane-service/tests/test_contracts.py`                         | `79b9f6d50d0d7864d5ff6920a1fa784490dfb575a04770daa9266a08faaf9b33` |
| `services/data-plane-service/tests/test_data_plane_application.py`            | `bdf6c6d65a150bfe27e1278e77a17fd1d57a32f65219b3ac2e04d3562003bf0f` |
| `services/data-plane-service/tests/test_delivery.py`                          | `d17aaef86be739bc9844b7537e6674edf87b3ab5b4e1c07e9427bda2024146fa` |
| `services/data-plane-service/tests/test_domain.py`                            | `6a51f9119ae289962039645821c84f2bbef5390c992dffad247dbcccf7bd498e` |
| `services/data-plane-service/tests/test_events.py`                            | `55b5db5d03323404f86036be9f5a691f01f5bc64acb5ab8f3308bcbdb7ddfae8` |
| `services/data-plane-service/tests/test_idempotency.py`                       | `b91910f7f2741ead5edf1ac2e4eb2c80eefbb638149a788c29ce4f2783ea57a7` |
| `services/data-plane-service/tests/test_integration.py`                       | `00f037e672d17b772204a1faceac85542e6c9ea63a7c765c869dae5afa614aa7` |
| `services/data-plane-service/tests/test_migrations.py`                        | `5d297427a28617b8516887bfd82bf72d7e446ffd6f1c7aa7436829caa4df2ed8` |
| `services/data-plane-service/tests/test_outbox.py`                            | `61960492df6ef57d3e2854309977f0b8c552d982bf6f9ee1fb39887c39d7d261` |
| `services/data-plane-service/tests/test_privileged.py`                        | `c66cc9ec52a9e2536a60d3c8b70f6599c942d9d73695c99547b28086ff6dbe72` |
| `services/data-plane-service/tests/test_projections.py`                       | `3465420e1b349d2b927c831cd678acb16a0518a902ddc46ff55f6b6b26fbaf27` |
| `services/data-plane-service/tests/test_registry.py`                          | `66fcbc3c0165b45dbfb681c899858bb8232bb4bc65897729ce2001846d5b0cf6` |
| `services/data-plane-service/tests/test_retention.py`                         | `1e9026b2c601ec07b9cec552dabe199f8d4ae39cfb2d82f2539e8eed2e230b6d` |
| `services/data-plane-service/tests/test_storage.py`                           | `cc2bc8e7723cee4533534619b316b5e40f360bf18a32e7f0ae9b2cfbda1efa73` |
| `tests/repository/test_pack13_fir_matrix.py`                                  | `26872bc04bb7dd0c68eb6629abb82bbf89d311f3e23469e61d4f65bf52c822d7` |

## 14. Status

```text
PACK-13 IMPLEMENTATION CANDIDATE
REPOSITORY_VERSION 0.13.0
CANON_VERSION 0.8.0
NOT PASS
NOT PRODUCTION READY
NOT LEGALLY ACTIVATED
```

`EPD2_PACK-12_PRIVILEGED_ADMIN_SEARCH_EXPORT_0.12.0_FINAL_PASS.zip`
remains the authoritative PASS baseline. This candidate does not replace
it, and nothing here is a production-readiness, compliance or
legal-activation claim.
