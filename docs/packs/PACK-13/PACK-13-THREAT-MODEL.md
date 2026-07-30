# PACK-13 — Threat Model

Specification-only. No code. Not implemented.

Thirty threats. Each records: protected asset; attacker or failure
mode; trust boundary; preventive control; detective control; evidence;
residual risk; dependency on a later pack.

The organising observation: **almost every threat here is a boundary that
persistence would erase.** The application layer refuses; the database,
asked the same question in SQL, answers.

---

## T-P13-01 — Cross-domain direct database access

**Asset:** every domain's authoritative records.
**Mode:** a service, script, analyst or ORM configuration reads or writes
another domain's tables because the connection allows it.
**Boundary:** domain schema boundary.
**Preventive:** domain-owned schemas; per-domain database roles with grants
only on their own schema; no shared application role (`P13-DP-014`,
`P13-OWN-001`).
**Detective:** privilege audit; query provenance by role; cross-schema
access alerting.
**Evidence:** grant inventory; access logs by role.
**Residual:** a superuser can always bypass grants — addressed by
`T-P13-17`.
**Dependency:** PACK-17 for operational monitoring.

## T-P13-02a — Direct write to audit persistence by a non-owner

**Asset:** the append-only, hash-chained audit record — the evidentiary
basis of every other control in the system.
**Mode:** a domain writes to `audit-core` tables directly, because "every
domain appends to audit" is read as permission to insert. A direct write
can skip the chain computation, insert out of order, or backdate.
**Boundary:** ownership, and the ingestion contract.
**Preventive:** _All domains may submit typed audit records through the
governed audit-ingestion contract; only `audit-core` persists authoritative
audit records_ (`P13-DP-014a`, `P13-OWN-014`). Other domains' application
credentials carry **no write grant** on the audit schema; bulk loading and
emergency SQL are not ordinary integration paths.
**Detective:** grant inventory per role; chain verification;
`DATAPLANE_AUDIT_DIRECT_WRITE_DENIED`,
`DATAPLANE_AUDIT_INGESTION_CONTRACT_REQUIRED`.
**Evidence:** grant inventory; ingestion records; chain verification
results.
**Residual:** privileged maintenance under PACK-12 can still reach the
storage — governed, evidenced, and explicitly **not** an ownership
transfer.
**Dependency:** PACK-12 for the privileged path.

## T-P13-02 — Shared-table privilege escalation

**Asset:** authorization decisions.
**Mode:** a "common" table (contacts, persons, settings) becomes writable
by several domains; whoever writes it controls the others' behaviour.
**Boundary:** ownership.
**Preventive:** no shared mutable schema (`P13-DP-015`); every table has
exactly one writing owner.
**Detective:** ownership matrix conformance test over the live catalog.
**Evidence:** ownership matrix; schema grants.
**Residual:** a projection could become a de-facto shared table —
constrained by `P13-PROJ-005`.

## T-P13-03 — Global identity correlation

**Asset:** `FIR-INV-001`.
**Mode:** a convenience key — shared surrogate ID, email uniqueness across
domains, a hash of a personal attribute — becomes a universal join key.
**Boundary:** identity.
**Preventive:** no global person table; no cross-domain identity FK; no
identity-derived idempotency key (`P13-DP-008`, `P13-DP-016`,
`P13-IDEM-003`).
**Detective:** schema scan for cross-schema identity-shaped keys; migration
gate `MIGRATION_GLOBAL_IDENTIFIER_PROHIBITED`.
**Evidence:** migration review records; schema conformance test.
**Residual:** correlation by behavioural pattern (timing, co-occurrence)
remains possible and is **not** eliminated by this pack.
**Dependency:** PACK-14.

## T-P13-04 — Lost organization scope

**Asset:** `FIR-INV-013`, Bund/Land/Kreis isolation.
**Mode:** a migration adds a table without scope; a projection drops it; a
query omits the predicate.
**Boundary:** organizational.
**Preventive:** scope as a first-class column from the first migration
(`P13-DP-005`); scope carried into every projection (`P13-PROJ-011`);
migration gate.
**Detective:** conformance test that every scoped table has the column and
every projection carries it; `MIGRATION_SCOPE_LOSS_DETECTED`.
**Evidence:** migration verification records.
**Residual:** an application query that forgets the predicate — mitigated
by repository-level enforcement, not by review.

## T-P13-05 — Unauthorized migration

**Asset:** schema integrity.
**Mode:** someone with database access applies DDL outside the migration
pipeline.
**Boundary:** privileged operations.
**Preventive:** migration execution requires a scoped PACK-12 grant
(`P13-SEC-002`); no manual production SQL (`P13-MIG-011`); DDL privilege
separated from application roles.
**Detective:** applied-migration ledger vs actual catalog diff; DDL audit.
**Evidence:** privileged session evidence; migration execution records.
**Residual:** a superuser with direct cluster access — `T-P13-17`.

## T-P13-06 — Migration checksum tampering

**Asset:** the guarantee that what was reviewed is what ran.
**Mode:** an applied migration's file is edited, and the checksum is
regenerated to match.
**Boundary:** change control.
**Preventive:** checksums recorded at application and verified on every
run; a mismatch halts and never auto-repairs (`P13-MIG-004`).
**Detective:** `MIGRATION_CHECKSUM_MISMATCH`; version-control history.
**Evidence:** migration ledger; VCS.
**Residual:** an attacker who can edit both the file and the ledger —
mitigated by the ledger being append-only and separately backed up.

## T-P13-07 — Outbox omission

**Asset:** the "event iff state change" guarantee.
**Mode:** a command writes state without writing the outbox record, or
writes it outside the transaction.
**Boundary:** transaction.
**Preventive:** atomic write mandated (`P13-TX-003`); no direct broker
publish from command execution (`P13-OBX-001`); the command frame is the
only write path.
**Detective:** reconciliation between state transitions and outbox records;
sequence gap detection at consumers.
**Evidence:** reconciliation reports; gap events.
**Residual:** a domain that bypasses the command frame entirely — caught by
architecture tests, not at runtime.

## T-P13-08 — Duplicate event effects

**Asset:** correctness of consequential effects (postings, exports,
notifications).
**Mode:** at-least-once delivery redelivers; a non-idempotent consumer acts
twice.
**Boundary:** consumer.
**Preventive:** mandatory consumer idempotency (`P13-DEL-003`); permanent
business-fact guards where expiry is unacceptable (`P13-IDEM-010`).
**Detective:** duplicate counters; business-fact uniqueness violations.
**Evidence:** dedup records.
**Residual:** a duplicate arriving after the dedup record expires —
precisely why the business-fact guard exists.

## T-P13-09 — Poison event

**Asset:** delivery liveness.
**Mode:** an event that fails deterministically is retried forever,
blocking a partition or exhausting the consumer.
**Boundary:** consumer.
**Preventive:** bounded retry; poison classification; dead-letter routing
(`P13-DEL-012`).
**Detective:** `EVENT_POISON_MESSAGE`; retry-count metrics.
**Evidence:** dead-letter records.
**Residual:** a transient fault misclassified as poison, dropping a real
event into dead-letter — mitigated by the mandatory review obligation.

## T-P13-10 — Event replay abuse

**Asset:** historical integrity; downstream state.
**Mode:** replay is used to re-trigger effects, to amplify a bug, or to
resurrect deleted data.
**Boundary:** privileged operations.
**Preventive:** replay is explicit, authorized, scoped
(`P13-DEL-010`); replay never mints new logical event IDs; consumers are
idempotent so replay is normally a no-op.
**Detective:** `event_replay.requested` / `.completed`; effect counters
during replay windows.
**Evidence:** replay reference with authority and scope.
**Residual:** replaying into a consumer whose idempotency window has
expired — scope and dry-run required.

## T-P13-11 — Incompatible consumer

**Asset:** consequential processing.
**Mode:** a producer ships a new schema; a consumer parses it partially and
acts on a misreading.
**Boundary:** contract.
**Preventive:** explicit version declaration; unsupported version fails
closed (`P13-EVO-006`); consumer registry gates publication.
**Detective:** `schema_consumer.incompatibility_detected`;
`EVENT_VERSION_UNSUPPORTED`.
**Evidence:** consumer registrations; incompatibility events.
**Residual:** an unregistered consumer receives no protection — stated to
consumers rather than discovered by them (`P13-REG-009`).

## T-P13-12 — Silent schema breaking change

**Asset:** every consumer.
**Mode:** a change passes the automated checker and breaks meaning.
**Boundary:** contract.
**Preventive:** the invisible-change classes always require semantic review
(`P13-COMPAT-004`); the registry stores tool verdict and human verdict
separately (`P13-COMPAT-007`).
**Detective:** consumer error rates after activation; coexistence-window
monitoring.
**Evidence:** compatibility assessments with both verdicts.
**Residual:** a reviewer who does not understand the semantics — mitigated
by requiring the _owner_, who does.

## T-P13-13 — Enum semantic drift

**Asset:** every decision branching on an enum.
**Mode:** an enum value's meaning is redefined; the wire value is
unchanged; nothing detects it.
**Boundary:** contract.
**Preventive:** enum meaning change is always breaking and always reviewed;
enum extension assessed on its own; unknown values never default
(`P13-EVO-011`, `P13-EVO-012`).
**Detective:** unknown-enum reason codes; assessment records.
**Evidence:** the assessment.
**Residual:** the highest residual risk in this model — no automated
control detects it. The control is procedural and stated as such.

## T-P13-14 — Stale projection used for a consequential decision

**Asset:** decision correctness.
**Mode:** a projection lags; a decision is taken on it as though fresh.
**Boundary:** authoritative vs derived.
**Preventive:** read models are not authoritative (`P13-PROJ-002`); legal
effect reads the authoritative record (`P13-PROJ-003`); staleness is
exposed and consulted (`P13-PROJ-008`).
**Detective:** `projection.lag_detected`; `PROJECTION_STALE`.
**Evidence:** lag metrics; refusal records.
**Residual:** a decision path that reads a projection without checking lag
— an architecture-test target.

## T-P13-15 — Deletion not propagated

**Asset:** PACK-09 deletion; data-subject rights.
**Mode:** a source record is deleted; a projection, cache, index or replica
retains it.
**Boundary:** retention.
**Preventive:** deletion propagates to every derived store
(`P13-PROJ-009`); search tombstones (`P13-SRCH-003`); retention applies to
projections, caches, events and outbox (`P13-RET-006`).
**Detective:** propagation verification; `PROJECTION_DELETION_NOT_PROPAGATED`.
**Evidence:** propagation records.
**Residual:** **backups retain deleted data** — explicitly acknowledged in
`P13-RET-004`, not solved here.
**Dependency:** PACK-17.

## T-P13-16 — Legal hold lost during migration

**Asset:** `FIR-DATA-003`; evidentiary obligations.
**Mode:** a migration drops or fails to carry hold state; the deletion job
then deletes held records.
**Boundary:** retention.
**Preventive:** hold records preserved (`P13-MIG-013`); unknown hold state
fails closed (`MIGRATION_HOLD_STATE_UNKNOWN`).
**Detective:** hold-state reconciliation before and after migration.
**Evidence:** migration verification records.
**Residual:** a hold applied during the migration window — mitigated by
freezing hold changes during destructive steps.

## T-P13-17 — Privileged DBA reading domain content

**Asset:** every domain's content; `FIR-INV-014`.
**Mode:** whoever operates the cluster reads membership, finance or
document content because the engine permits it.
**Boundary:** privileged operations.
**Preventive:** operator privilege is not content authority
(`P13-SEC-001`); no universal DBA (`P13-SEC-005`); separation of the
operating role from any content-reading role; encryption at rest with keys
outside the DBA's control where the engine supports it.
**Detective:** PACK-12 privileged session evidence; query audit.
**Evidence:** session evidence; grant inventory.
**Residual:** **substantial and unresolved at this layer.** A sufficiently
privileged operator can read what the engine can decrypt. Reducing this
further requires HSM-backed key custody and application-level encryption —
**PACK-14 and PACK-17**, not PACK-13. Stated plainly rather than implied
away.

## T-P13-18 — Raw export through the database

**Asset:** PACK-12 export controls.
**Mode:** a dump, replica, analytics copy or backup extract delivers data
to a recipient without passing through governed export.
**Boundary:** export.
**Preventive:** no raw export bypass (`P13-EXPORT-004`); replicas and
backups carry the same classification and access controls as the primary;
dump privileges separated and governed.
**Detective:** dump/replication privilege audit; egress monitoring.
**Evidence:** privilege inventory.
**Residual:** an operator with backup access — `T-P13-17`.
**Dependency:** PACK-17.

## T-P13-19 — Search projection leakage

**Asset:** PACK-12 search policy.
**Mode:** the index holds fields or records the search policy excludes, or
an unrelated domain writes to it.
**Boundary:** search.
**Preventive:** the index is never authoritative (`P13-SRCH-007`); only the
projection owner writes (`P13-SRCH-006`); index policy remains PACK-12's.
**Detective:** index-content conformance against index policy.
**Evidence:** index policy version; removal evidence.
**Residual:** a stale index serving records whose authorization changed —
addressed by PACK-12's result-time re-resolution.

## T-P13-20 — Event payload personal-data leakage

**Asset:** personal data.
**Mode:** a payload carries content "for convenience"; it then exists in
the broker, every consumer, every log and every backup.
**Boundary:** event transport.
**Preventive:** minimal payloads (`P13-OBX-007`); prohibited-key guard
applied **before the outbox write** (`P13-OBX-008`).
**Detective:** payload scans in tests; guard refusals.
**Evidence:** guard refusal records.
**Residual:** a permitted field that is personal data in context — reduced
by review, not eliminated.

## T-P13-21 — Dead-letter sensitive-data exposure

**Asset:** personal data in failed events.
**Mode:** dead-letter is treated as an operational log and given wide
access.
**Boundary:** privileged operations.
**Preventive:** the dead-letter store is classified, access-controlled
under PACK-12, retained under PACK-09, excluded from general operator
visibility (`P13-DEL-014`).
**Detective:** access audit on the dead-letter store.
**Evidence:** access records.
**Residual:** operational pressure to widen access during an incident —
which is exactly what break-glass is for.

## T-P13-22 — Rollback corrupting historical records

**Asset:** immutable history.
**Mode:** a rollback reverts a migration and, with it, rewrites or drops
historical rows.
**Boundary:** immutability.
**Preventive:** immutable-history tables have no `UPDATE`/`DELETE` in the
persistence contract (`P13-DP-010`); rollback of a destructive step is
either tested or declared unavailable (`P13-MIG-009`).
**Detective:** hash-chain verification after any rollback.
**Evidence:** verification records.
**Residual:** a rollback that restores a pre-migration snapshot loses
post-migration history — which is why forward-fix is preferred.

## T-P13-23 — Dual-write divergence

**Asset:** single source of truth.
**Mode:** old and new structures are both written and drift apart; each
looks authoritative.
**Boundary:** migration.
**Preventive:** dual-write forbidden without an approved reconciliation
strategy (`P13-XC-002`, `P13-XC-006`).
**Detective:** reconciliation runs during the dual-write window.
**Evidence:** reconciliation reports.
**Residual:** divergence between reconciliation runs — bounded by run
frequency.

## T-P13-24 — Backfill inventing data

**Asset:** factual integrity.
**Mode:** a backfill fills a required field with a default, an inference or
"the most likely value", and the invention becomes an authoritative fact.
**Boundary:** truth.
**Preventive:** a backfill invents nothing; unresolved records go to review
(`P13-BF-011`, `P13-BF-012`); `BACKFILL_SOURCE_INCOMPLETE`.
**Detective:** the reconciliation report's routed-to-review count.
**Evidence:** the report.
**Residual:** a reviewer who resolves a review item by guessing — a human
control with a human failure mode.

## T-P13-25 — Partial migration

**Asset:** consistency.
**Mode:** a migration halts mid-way, leaving a structure half-changed, and
the system runs on it.
**Boundary:** migration.
**Preventive:** halt-and-preserve on failure; never auto-continue;
checkpoints; expand/contract so that intermediate states are valid by
design (`P13-XC-001`).
**Detective:** `MIGRATION_PARTIAL_FAILURE`; applied-state reconciliation.
**Evidence:** execution records; checkpoints.
**Residual:** an intermediate state that is valid structurally but not
semantically — reduced by dry-run.

## T-P13-26 — Cross-region or replica inconsistency

**Asset:** decision correctness.
**Mode:** a consequential read hits a stale replica and returns an old
answer as current.
**Boundary:** consistency.
**Preventive:** consequential reads go to the primary or refuse
(`P13-DEL-005`, §29); replica staleness surfaced.
**Detective:** replication-lag metrics; `DATAPLANE_REPLICA_STALE`.
**Evidence:** lag metrics.
**Residual:** an unclassified read path treated as non-consequential when
it is not.
**Dependency:** multi-region is explicitly excluded (§34).

## T-P13-27 — Ballot linkage through shared infrastructure

**Asset:** `FIR-INV-002`, the most consequential invariant in the system.
**Mode:** ballots and identity share a database, a broker topic, a
connection identity, a trace correlation ID or a backup, and correlation
becomes possible by timing or co-location even without a shared key.
**Boundary:** voting.
**Preventive — what PACK-13 actually fixes:** no ballot content, voting
secret or credential in the general plane; no identity-to-ballot join in any
general schema; no identity-linked ballot payload on the general event bus;
no global member or account identifier as a Voting Client identifier
(`P13-VOTE-001`..`007`); trace IDs never carry subject references across
domains (`P13-OBS-003`).
**Not decided by PACK-13:** broker topics, separate or shared broker
deployment, connection-pool topology, service names, credential topology,
transport provider (`P13-VOTE-008`). Where the PACK-15/16 threat model
requires it, separate infrastructure is the **preferred reference
direction** (`P13-VOTE-010`) — a direction, not a topology already chosen
here.
**Detective:** structural absence tests — no such table, no such topic, no
such reference type.
**Evidence:** schema and topic inventories.
**Residual:** timing correlation across separate infrastructure remains
theoretically possible and is **not** closed by PACK-13.
**Dependency:** **PACK-15/16 own the voting architecture and must
demonstrate isolation and unlinkability against their own threat model
(`P13-VOTE-009`). PACK-13 supplies the general data-plane constraints and
guarantees only that unlinkability is not defeated from this side.**

## T-P13-27a — Schema-version identity collapsed onto a content digest

**Asset:** the governance record of _why_ a schema version exists.
**Mode:** the registry treats digest equality as version identity. Two
consequences follow, both bad. A deliberate governed re-issue — a changed
compatibility mode, a new effective date, a corrected owner — is silently
merged into the existing version, erasing the decision. Or the registry is
believed to have proved semantic equivalence, which no canonicalization can
do.
**Boundary:** contract governance.
**Preventive:** `content_digest` and `schema_version_id` are separate
fields answering separate questions (`P13-REG-005`..`005g`);
canonicalization removes only enumerated serialization differences; the
registry claims no universal semantic-equivalence proof; identical content
may be bound to a new version only with a `governance_justification`;
historical version identity is never rewritten because of digest equality.
**Detective:** `SCHEMA_DUPLICATE_CONTENT`,
`SCHEMA_DUPLICATE_CONTENT_REVIEW_REQUIRED`,
`SCHEMA_VERSION_IDENTITY_IMMUTABLE`,
`SCHEMA_GOVERNANCE_JUSTIFICATION_MISSING`.
**Evidence:** publication decisions; governance justifications.
**Residual:** a reviewer who approves a re-issue with a perfunctory
justification — a human control with a human failure mode.

## T-P13-28 — Schema registry unavailability weaponised

**Asset:** change control.
**Mode:** the registry is unavailable, and publication is allowed to
proceed "temporarily" without compatibility assessment.
**Boundary:** contract.
**Preventive:** registry unavailable ⇒ **publication blocked**, existing
traffic continues (§29); no bypass flag (`P13-GOV-004`).
**Detective:** `SCHEMA_REGISTRY_UNAVAILABLE`.
**Evidence:** refusal records.
**Residual:** pressure to add an emergency bypass — which `FIR-INV-006`
forbids and which no future round may add without amending that invariant.

---

## Summary of residual risks that PACK-13 does **not** close

| #        | Residual                                            | Owner                   |
| -------- | --------------------------------------------------- | ----------------------- |
| T-P13-13 | Enum semantic drift has no automated detection      | procedural, permanently |
| T-P13-15 | Backups retain deleted data                         | PACK-17                 |
| T-P13-17 | A sufficiently privileged operator can read content | PACK-14 / PACK-17       |
| T-P13-18 | Backup and replica egress                           | PACK-17                 |
| T-P13-03 | Behavioural correlation of a person across domains  | not solved by any pack  |
| T-P13-27 | Timing correlation across isolated infrastructure   | PACK-15/16              |

Stating these is the point. A threat model whose every residual risk is
"mitigated" is a threat model that has stopped looking.
