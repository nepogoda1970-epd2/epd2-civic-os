# PACK-13 — Production Data Plane & Contract Evolution

**Round type:** specification and ADR only. **No code. Not implemented. Not a candidate. Not a PASS.**

> **Superseding status note, added by the PACK-13 FINAL PASS round
> (2026-07-30).** The line above describes the _specification_ round that
> wrote this document and is retained unchanged as the historical record.
> The implementation round has since happened: PACK-13 reached **FINAL
> PASS** at repository version `0.13.0`, verified by an external GitHub
> Actions run. The specification is implemented in **reference form** — the
> contracts, gates and refusals are real and externally verified, and no
> production database, broker, schema registry, search engine or IAM is
> deployed. **NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.** See
> `docs/handover/PACK-13-FINAL-PASS-REPORT.md`.

**Target version:** `0.13.0` — a target, not a setting. This round changes
no version. `REPOSITORY_VERSION` remains `0.12.0` and `CANON_VERSION`
remains `0.8.0`.

**Baseline:** `EPD2_PACK-12_PRIVILEGED_ADMIN_SEARCH_EXPORT_0.12.0_FINAL_PASS.zip`
(PACK-01 through PACK-12: FINAL PASS).

**Register entry:** `FIR-ROADMAP-003`.

---

## 0. What this round is, and the one thing it must not become

PACK-01 through PACK-12 built twenty-one services whose every storage
adapter is in memory. That was deliberate and it was honest: the governed
workflows, the separation models and the refusal surfaces are real and
externally verified, and the production data plane was never claimed. This
round specifies that data plane.

The danger in a round like this is specific and worth naming before any
requirement is written. A data-plane round is where an architecture
quietly loses its boundaries. Everything must be persisted, so it is
tempting to persist everything in one place; everything must be queried,
so it is tempting to join across domains; everything must be correlated,
so it is tempting to mint one identifier that correlates it. Each of those
temptations is efficient, each is normal industry practice, and each would
destroy an invariant this system spent twelve packs establishing.

So the governing rule of PACK-13 is stated first, before the architecture:

> **The data plane is infrastructure. It is not an authority.**
>
> Persistence must not create a capability that the domain layer refuses.
> A join that no API permits is not permitted because the tables happen to
> sit in one database. A correlation that `FIR-INV-001` forbids is not
> permitted because a foreign key would be convenient. A read that PACK-12
> would refuse is not permitted because a projection already computed it.

Everything below is an elaboration of that sentence.

---

## 1. Scope

Thirteen areas, each with normative requirements in this document:

1. production relational data plane (§4, §5);
2. event transport and delivery semantics (§8, §9, §10);
3. canonical schema registry (§12, §13);
4. API contract evolution (§15);
5. event contract evolution (§16);
6. database migration discipline (§18, §19, §20);
7. transaction and consistency boundaries (§6);
8. idempotency and deduplication (§11);
9. compatibility and deprecation policy (§14, §17);
10. projection and read-model governance (§21);
11. retention, deletion and legal-hold integration (§24);
12. operational data-plane observability (§30);
13. reference-to-production migration path (§19, §33).

## 2. What PACK-13 inherits and must not weaken

| Source          | Inherited obligation                                                                           | What PACK-13 may not do                                                   |
| --------------- | ---------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| **canon 0.8.0** | The event envelope (§21), aggregate-prefixed event names (§20), the reason-code registry (§24) | Introduce a second envelope, rename events, or redefine a registered code |
| **PACK-02**     | Append-only hash-chained `AuditEvent`                                                          | Write a second audit log; let a migration or replay rewrite the chain     |
| **PACK-08**     | `OrganizationalScope`, effective dating, the pairwise role incompatibility baseline            | Lose scope in persistence; let a database role escape the matrix          |
| **PACK-09**     | Record classes, retention schedules, legal hold, destruction evidence                          | Decide retention itself; delete under hold; treat a hold as authorization |
| **PACK-10**     | Finance separation of duties                                                                   | Bypass it through a data-plane import path                                |
| **PACK-11**     | Immutable hash-linked document versions, evidence bundles, custody                             | Rewrite history; create a second evidence system                          |
| **PACK-12**     | Privileged access, authorization-aware search, governed export, DLP, disclosure control        | Rewrite search or export policy; create a database path around them       |

**PACK-13 owns the transport. The domains keep the meaning.**

---

## 3. Bounded contexts

Five logical contexts. They are logical: this specification does not
mandate five deployables, and the implementation round decides packaging
under its own ADR.

| Context                                  | Owns                                                                                                                     | Does **not** own                                                        |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------- |
| **Transactional Data Plane** (§4–§7)     | Authoritative record persistence, aggregate versions, transaction and unit-of-work boundaries, deterministic identifiers | Domain invariants, retention decisions, authorization decisions         |
| **Event Transport** (§8–§10)             | Outbox, dispatch, delivery, retry, dead-letter, replay, consumer checkpoints                                             | Event _meaning_; the envelope; whether an event may be published at all |
| **Canonical Schema Registry** (§12–§14)  | Schema identity, version, family, compatibility mode, lifecycle, publication                                             | The canon; domain semantics; approval authority                         |
| **Contract Evolution** (§15–§17)         | API and event versioning, compatibility classification, deprecation windows, migration obligations                       | The decision that a change is worth making                              |
| **Projection and Read Models** (§21–§23) | Read projections, rebuild, lag, staleness, deletion propagation                                                          | Authoritative truth; authorization; legal effect                        |

`P13-CTX-001` No context above may become a general-purpose platform that
bypasses a domain owner. In particular there is **no** universal
projection service that any domain may write into, and **no** universal
data-access layer through which any domain may read another's records.

`P13-CTX-002` Each context's records carry `OrganizationalScope` where the
underlying domain record does. Scope is not added by projection and is
never dropped in transit.

---

## 4. Production relational data plane

`P13-DP-001` The reference direction is a **PostgreSQL-compatible
relational database**. This is an architectural direction, not a
procurement commitment and not a vendor lock-in claim: any engine meeting
the requirements in this section is admissible, and the implementation
round records its choice under its own ADR.

`P13-DP-002` Transaction boundaries are **explicit**. No implicit
auto-commit per statement for a command that spans more than one write.

`P13-DP-003` Persistence is organised by **domain-owned schemas**, or an
equivalent strict logical isolation the implementation round justifies. A
single shared mutable schema holding every domain's tables is forbidden.

`P13-DP-004` Every authoritative record carries a **stable domain
identifier**, minted by and meaningful to its owning domain.

`P13-DP-005` Every authoritative record that its domain scopes carries
`organization_id` (and the scope kind where the domain models one) as a
**first-class column**, not as a value buried in a JSON blob.
Organizational scope exists from the first migration, not as a later
retrofit (`FIR-INV-013`).

`P13-DP-006` A record whose domain assigns it a sensitivity or record
class carries a **classification reference** and a **record-class
reference** (PACK-09), so that retention, export and search decisions have
something to read.

`P13-DP-007` **No generic JSON dump is an authoritative model.** A JSON
column may carry an opaque payload the database does not interpret; it may
not be the place where a domain's structured, invariant-bearing fields
live, because a database cannot enforce an invariant it cannot see.

`P13-DP-008` **No global person table** exists, and no column anywhere is
a universal person key (`FIR-INV-001`). Account, person, membership and
each domain's own subject reference remain distinct identifiers with
distinct lifecycles. A foreign key that would make them one is forbidden
however convenient.

`P13-DP-009` Foreign key constraints are permitted **within** a domain
schema. Across domain schemas they are permitted only for the narrow,
enumerated references the owning domains have agreed under ADR, and never
for identity correlation.

`P13-DP-010` Immutable history is preserved where a domain requires it:
PACK-02 audit events, PACK-11 document versions and evidence, PACK-12
sealed sessions. For these, `UPDATE` and `DELETE` are not part of the
persistence contract at all; the implementation round enforces this at the
database privilege level as well as in code.

`P13-DP-011` Effective dating (PACK-08) is preserved in persistence:
a record with a validity window stores both bounds explicitly, and
"currently effective" is a query, never a mutable flag that some job
maintains.

`P13-DP-012` **Voting secrets do not enter the general data plane.** No
ballot content, vote envelope, voting credential or intermediate tally is
stored in any schema covered by this specification. The voting domains use
an isolated data plane defined by a future architecture (§27).

## 5. What the data plane must not make possible

These are stated as prohibitions because each describes a capability that
correct-looking schema design would silently create.

`P13-DP-013` **No direct cross-domain table join is a public application
contract.** A query that reads two domains' tables is not an integration
pattern; it is a boundary violation that happens to compile.

`P13-DP-014` **No service writes to another domain's tables.** Not for
convenience, not for performance, not during migration.

`P13-DP-014a` **All domains may submit typed audit records through the
governed audit-ingestion contract; only `audit-core` persists authoritative
audit records.** Submission is not persistence: other domains reach audit
through the ingestion port/API or a versioned audit command or event, never
by writing to the audit schema. Their application credentials carry no
write grant on it, bulk loading and emergency SQL are not ordinary
integration paths, and privileged maintenance under PACK-12 does not
transfer ownership. Append-only describes ingestion semantics and
authoritative storage alike.

`P13-DP-015` **No shared "everything" schema** and no cross-domain
"common" tables holding identity, contact or membership facts that several
domains read directly.

`P13-DP-016` **No database-level convenience key correlates a person
across domains** — no shared surrogate key, no deterministic hash of a
personal attribute used as a join key, no "same email means same person"
uniqueness constraint spanning domains.

`P13-DP-017` **Identity/ballot unlinkability may not be defeated by
database design** (`FIR-INV-002`). No table, index, foreign key, audit
column, timestamp correlation or physical co-location may make it possible
to associate an eligibility record with a ballot.

---

## 6. Transaction and consistency boundaries

`P13-TX-001` One domain command executes within **one local transaction
boundary** in one domain's schema.

`P13-TX-002` **Distributed transactions across domains are not the
integration pattern.** Two-phase commit spanning domain boundaries is
forbidden as a normal mechanism; cross-domain consistency is reached
through governed contracts and events, with explicitly modelled
compensation.

`P13-TX-003` The authoritative state change and its **outbox record are
written atomically**, in the same transaction. This is the single most
load-bearing requirement in this document: it is what makes "the event
happened if and only if the state changed" true rather than aspirational.

`P13-TX-004` **No external side effect executes inside a database
transaction.** No HTTP call, no broker publish, no file write, no email.
An external effect begins only after durable intent is committed.

`P13-TX-005` A rolled-back transaction leaves **no published event**. This
follows from `P13-TX-003` and is restated because the failure it prevents
— an event describing state that does not exist — is unrecoverable by any
downstream consumer.

`P13-TX-006` A published event never references **uncommitted** state.

`P13-TX-007` A retry produces **no duplicate authoritative effect**. Retry
safety is achieved through idempotency (§11), not through hoping the
first attempt failed cleanly.

`P13-TX-008` A long-running workflow is modelled as a **saga or process
manager** with explicit steps, explicit compensation and its own persisted
state — never as a transaction held open across steps, user interaction or
external calls.

`P13-TX-009` **No legal deadline, governance workflow or statutory period
depends on an open transaction.** A deadline that is only correct while a
transaction is uncommitted is a deadline that a connection reset can
alter.

`P13-TX-010` Read-your-own-writes within a command is guaranteed inside
the transaction boundary; across boundaries it is not assumed, and any
workflow requiring it says so and provides for it explicitly.

---

## 7. Optimistic concurrency

`P13-CC-001` Every mutable aggregate carries an **aggregate version**,
incremented on every state-changing commit.

`P13-CC-002` Every state-changing command accepts an **expected version**.
A mismatch produces a reason-coded conflict, never a silent overwrite.

`P13-CC-003` **Last-write-wins is forbidden for consequential records** —
anything bearing a decision, an authorization, a financial fact, a
governed document state, a privileged grant, a retention or hold state, or
any legal effect. Where last-write-wins is admissible at all, the record
class says so explicitly and the specification names it.

`P13-CC-004` A submitted snapshot is **immutable**. A decision is taken
against the exact version presented, and that version is recorded with the
decision.

`P13-CC-005` **An approval does not apply to a version that has changed
since the approver saw it.** If the aggregate moved, the approval is
refused with a distinct reason code and returned for a fresh decision.
This is the concurrency expression of PACK-12's activation re-check.

`P13-CC-006` **Effective-dated authority is re-checked at command
execution**, not only at command construction. Authority that lapsed
between the two is not authority.

`P13-CC-007` A stale decision never silently overwrites current state.

`P13-CC-008` Conflict is **user-visible and actionable**: the caller
learns that a conflict occurred, on which aggregate, at which version, and
what to do — not merely that the request failed.

### 7.1 Minimum models

| Model                       | Purpose                                                                                                              |
| --------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| `AggregateVersion`          | The monotonically increasing version of one aggregate instance                                                       |
| `ExpectedVersion`           | The version a command asserts it is acting upon; may express "must not exist" and "any" as distinct, explicit cases  |
| `ConcurrencyDecision`       | The outcome of the version check: proceed, or conflict with a reason                                                 |
| `ConcurrencyConflict`       | Aggregate reference, expected version, actual version, reason code, whether retry is admissible                      |
| `CommandExecutionReference` | A stable reference to one command execution, linking the idempotency record, the audit row and the resulting version |

`P13-CC-009` `ExpectedVersion` distinguishes "any version" from "no
version" (create). Collapsing them makes a create-if-absent silently
overwrite an existing record.

---

## 8. Transactional outbox

`P13-OBX-001` The **transactional outbox is the mandatory reference
pattern** for publishing domain events. No domain publishes to a broker
directly from command execution.

`P13-OBX-002` Domain state and outbox record are written atomically
(`P13-TX-003`).

`P13-OBX-003` An outbox record is **immutable after commit**, except for
delivery metadata (status, attempt count, timestamps, acknowledgement
references). The event's identity, type, version and payload never change.

`P13-OBX-004` The event envelope is built to the **existing canon
envelope** (canon §21). PACK-13 adds no envelope field.

`P13-OBX-005` The **event ID is stable**. Republication after a failed
delivery reuses the same logical event ID; it does not mint a new one. A
consumer that has seen the ID has seen the event.

`P13-OBX-006` The **event version is explicit** in the envelope. There is
no implicit "current" version.

`P13-OBX-007` The payload is **minimal**: identifiers, enum values,
timestamps, one reason code, version and policy references, opaque
references. Not domain content.

`P13-OBX-008` **Secrets and unnecessary personal data are forbidden in
event payloads.** The PACK-12 prohibited-key discipline applies to every
outbox payload, enforced before the record is written, not before it is
dispatched — a payload that reached storage has already leaked into
backups.

`P13-OBX-009` The **dispatcher changes no domain semantics.** It reads,
publishes, records the outcome. It does not enrich, transform, filter on
business rules, or decide whether an event "should" be sent.

`P13-OBX-010` Delivery attempts are **auditable**: each attempt records
when, to which destination, with what outcome.

`P13-OBX-011` **Published state and delivery evidence are distinct.**
"We dispatched it" and "the broker acknowledged it" are different facts
and are stored as different fields. Conflating them makes a lost
acknowledgement look like a successful delivery.

`P13-OBX-012` Outbox cleanup obeys **retention policy** (PACK-09) and is
itself a governed deletion, not a maintenance script's side effect.

`P13-OBX-013` A **legal hold does not widen access** to an outbox payload.
Hold preserves; it never authorizes reading.

### 8.1 Minimum models

| Model                            | Purpose                                                                                                  |
| -------------------------------- | -------------------------------------------------------------------------------------------------------- |
| `OutboxRecord`                   | Event ID, type, version, envelope, aggregate reference, organization scope, created-at, status           |
| `OutboxStatus`                   | `pending`, `dispatching`, `published`, `acknowledged`, `failed`, `dead_lettered`, `superseded_by_replay` |
| `DeliveryAttempt`                | Attempt number, started-at, outcome, error reference, destination reference                              |
| `DispatchDecision`               | Whether to dispatch now, defer, or dead-letter, with reason code                                         |
| `PublicationEvidence`            | What was published, when, and the acknowledgement that proves it                                         |
| `BrokerAcknowledgementReference` | An opaque reference to the broker's own acknowledgement — never the broker's internal payload            |

---

## 9. Event delivery semantics

`P13-DEL-001` The delivery guarantee is **at-least-once**.

`P13-DEL-002` **Exactly-once delivery is not claimed** as a universal
guarantee, is not designed for, and must not be described as available in
any PACK-13 document, code comment, API description or operator interface.
What the system provides is at-least-once delivery with **effectively-once
consumer effect**, achieved by consumer idempotency (§11). The distinction
is not pedantry: a system that believes it has exactly-once delivery stops
writing idempotent consumers.

`P13-DEL-003` Every consumer is idempotent. A consumer that cannot be made
idempotent is a design defect, not a tolerated exception.

### 9.1 Situations that must be specified, not discovered

For each, the implementation round must provide detection, retry, evidence,
escalation, operator action and a stated residual risk. The
`PACK-13-EVENT-DELIVERY-MATRIX.md` carries the full table; the normative
requirements are here.

`P13-DEL-004` **Duplicate delivery** is expected, detected by
deduplication key, and produces no second effect.

`P13-DEL-005` **Delayed delivery** is expected. A consumer never assumes
an event is recent, and a decision whose correctness depends on freshness
reads a freshness marker rather than assuming one.

`P13-DEL-006` **Out-of-order delivery** within an ordering scope is
detected via the sequence field and handled with a reason code — never
silently applied as if in order.

`P13-DEL-007` A **missing acknowledgement** is treated as _unknown_, not
as failure and not as success. The record moves to a state that says so,
and redelivery is safe because consumers are idempotent.

`P13-DEL-008` **Consumer retry** is bounded, backed off, and terminates in
dead-lettering rather than in unbounded retry.

`P13-DEL-009` **Dead-lettering** preserves the event and its failure
context, is alertable, and is reviewable. A dead-letter store is not a
dumping ground: it has retention, access control and a review obligation.

`P13-DEL-010` **Replay** is explicit, authorized, scoped and evidenced. It
never rewrites history and never mints new logical event IDs for events
that already existed.

`P13-DEL-011` A **consumer checkpoint** records what a consumer has
durably processed. Advancing it is a governed act, and moving it backwards
is a distinct, authorized operation.

`P13-DEL-012` A **poison event** — one that fails deterministically — is
detected as such rather than retried forever, and is routed to dead-letter
with its own reason code.

`P13-DEL-013` A **compatibility failure** at the consumer fails closed for
consequential consumers: the consumer does not guess, does not skip, and
does not apply a partial interpretation.

`P13-DEL-014` A **dead-letter store may contain personal data** and is
therefore classified, access-controlled under PACK-12, retained under
PACK-09, and excluded from general operator visibility.

---

## 10. Ordering

`P13-ORD-001` **Global total ordering across all events is not promised**
and must not be relied upon.

`P13-ORD-002` Admissible ordering scopes are: **per aggregate**, **per
stream**, and **per organization and aggregate** where justified. An
ordering scope is declared per event family, not assumed.

`P13-ORD-003` Every event carries an **explicit sequence field** within
its ordering scope.

`P13-ORD-004` Consumers must not rely on global order.

`P13-ORD-005` Out-of-order events are handled with a **reason code**, not
silently.

`P13-ORD-006` A **sequence gap is detected** and is a governed fact that
raises an event, not a silent absence.

`P13-ORD-007` **Replay does not change the historical event sequence.**

`P13-ORD-008` An **event timestamp is not the ordering mechanism.**
Timestamps are metadata; sequence is order.

`P13-ORD-009` **Clock skew does not break ordering semantics**, because
ordering never depends on comparing clocks across producers.

---

## 11. Idempotency and deduplication

`P13-IDEM-001` Idempotency is required for: commands; event consumers;
external-provider callbacks; export generation; document rendition
generation; finance imports; deadline jobs; notification dispatch; schema
publication; migrations.

### 11.1 Minimum models

`IdempotencyKey`, `IdempotencyScope`, `IdempotencyRecord`,
`IdempotencyDecision`, `DeduplicationRecord`, `ReplayReference`.

### 11.2 Rules

`P13-IDEM-002` A key has **domain and operation scope**. A key is never
global across the system, because a global key space lets one domain's
retry collide with another's.

`P13-IDEM-003` **An idempotency key is never a global user identifier**,
and never derived from one (`FIR-INV-001`).

`P13-IDEM-004` **Reuse of a key with a different payload is a conflict**,
with its own reason code. It is never treated as a replay.

`P13-IDEM-005` The **result of the first successful operation is
reproducible** — a replay returns what the first execution produced,
without re-performing the effect.

`P13-IDEM-006` **An expired idempotency record must not permit a silent
duplicate** of a consequential action. Where expiry could allow one, the
operation carries a second, longer-lived deduplication guard tied to the
business fact rather than the request.

`P13-IDEM-007` Idempotency-record **retention is policy-driven** (PACK-09),
and the policy states the consequence of expiry for each operation class.

`P13-IDEM-008` Idempotency storage holds **no unnecessary sensitive
payload** — a request digest, not the request.

`P13-IDEM-009` Deduplication at the consumer is keyed on the **event ID**
plus the consumer's own scope, so the same event consumed by two consumers
is two independent effects, each deduplicated once.

---

## 12. Canonical Schema Registry

`P13-REG-001` A canonical schema registry is the single place where a
schema's identity, version, ownership, compatibility mode and lifecycle
state are recorded.

`P13-REG-002` **The registry is not a second canon.** The canon defines the
domain and event model; the registry records the machine-readable artifacts
that implement it and their evolution. Where the two disagree, the canon
governs and the disagreement is a defect to be resolved, not a precedence
rule to be applied.

### 12.1 Minimum entities

`SchemaFamily`, `SchemaDefinition`, `SchemaVersion`, `SchemaOwner`,
`SchemaLifecycleState`, `CompatibilityMode`, `CompatibilityAssessment`,
`SchemaPublicationDecision`, `SchemaDeprecation`, `SchemaSupersession`,
`ConsumerRegistration`, `MigrationReference`.

### 12.2 Lifecycle states

```text
draft → under_review → approved → active → deprecated → retired
                    ↘ rejected
         active/deprecated → superseded
```

`P13-REG-003` Every transition is a governed act with an actor, a reason
code and an event.

`P13-REG-004` `retired` and `superseded` do **not** delete the schema
version. A historical event validated against a retired schema must remain
interpretable; deleting the schema would orphan the history.

### 12.3 Mandatory attributes of every schema version

`schema_version_id` (stable); family; version; owner; format;
`content_digest`; `publication_decision_id`; compatibility mode;
classification; `effective_at`; `deprecated_at` where one exists;
`supersession_reference` where superseded; documentation; example fixtures;
validation result; dependent consumers; approval evidence; and
`governance_justification` where identical content is published as a new
governed version.

### 12.4 Content digest and schema-version identity are separate

`P13-REG-005` **Content that is identical after the registry's
format-specific canonicalization produces the same content digest. Digest
equality does not itself define schema-version identity.**

The distinction matters because conflating them would make the registry
claim something it cannot prove. A digest answers a narrow question — are
these bytes the same after a defined normalization — and nothing more.

`P13-REG-005a` **Format-specific canonicalization removes only enumerated
serialization differences** (key ordering, insignificant whitespace,
equivalent number or string encodings as each format defines them). It is
not a semantic normalizer, and the enumerated set is recorded per format in
§13.

`P13-REG-005b` **The registry claims no universal proof of semantic
equivalence.** Two documents with the same digest are byte-identical after
canonicalization; two documents with different digests may still mean the
same thing, and the registry does not adjudicate that.

`P13-REG-005c` **`schema_version_id` is a distinct, governed identity.** It
is established by a publication decision and is never derived from, nor
overwritten because of, digest equality.

`P13-REG-005d` **Accidental republication of identical content is
blocked**, or requires reason-coded review — never silently accepted and
never silently deduplicated into the existing version.

`P13-REG-005e` **Identical content may be bound to a new governed version
only with an explicit `governance_justification`** recorded on the new
version. Legitimate cases exist — a re-issue under a changed compatibility
mode, a new effective date, a corrected ownership assignment, a
republication after a governance defect — and each is a _governance_ fact,
not a content fact.

`P13-REG-005f` **Governance context, effective date and publication
decision are stored separately** from the content digest, so that the
question "what does this version mean, and who decided it" is answerable
without inspecting bytes.

`P13-REG-005g` **Historical version identity is never rewritten because of
digest equality.** A later publication does not retroactively merge into,
replace or re-point an earlier version.

`P13-REG-006` **Every schema has exactly one owner**, and the owner is a
domain, not a platform team.

`P13-REG-007` A schema with **no registered owner cannot be published.**

`P13-REG-008` **Example fixtures are mandatory**, and they are validated
against the schema at publication. A schema whose own examples do not
validate is not publishable.

`P13-REG-009` Consumer registration is how the registry knows who breaks.
A consumer that is not registered receives no compatibility protection —
and this consequence is stated to consumers, not discovered by them.

---

## 13. Schema formats

`P13-FMT-001` Multiple formats are supported: **JSON Schema**, **OpenAPI**,
**AsyncAPI**, **SQL migration metadata**. Protobuf/Avro are admissible as a
future-compatible extension where justified.

`P13-FMT-002` **No universal format abstraction** is created that hides the
real differences between these formats. A layer that pretends OpenAPI and
SQL migrations are the same kind of object produces compatibility answers
that are wrong in both.

`P13-FMT-003` For each format the specification records: source of truth;
canonical serialization; digest calculation; validation toolchain;
compatibility checker; publication path.

| Format                 | Source of truth                                            | Canonical form                                          | Compatibility checker                                 |
| ---------------------- | ---------------------------------------------------------- | ------------------------------------------------------- | ----------------------------------------------------- |
| JSON Schema            | The schema file in the owning domain's contracts directory | Canonical JSON, key-sorted, no insignificant whitespace | Structural checker plus semantic review (§14)         |
| OpenAPI                | The API description owned by the exposing domain           | Canonical YAML→JSON projection                          | Endpoint/parameter/response diff plus semantic review |
| AsyncAPI               | The event channel description                              | As OpenAPI                                              | Channel/message/schema diff plus semantic review      |
| SQL migration metadata | The migration file itself                                  | Migration ID, statement digest, ordering position       | Migration-control checks (§18), not a schema differ   |
| protobuf/Avro (future) | The IDL file                                               | The format's own canonical form                         | The format's own rules, plus semantic review          |

`P13-FMT-004` **The compatibility checker is necessary and not
sufficient.** Every format's automated check is followed by the semantic
assessment in §14, because no differ understands meaning.

---

## 14. Compatibility modes

`P13-COMPAT-001` Modes: **backward compatible**, **forward compatible**,
**full compatible**, **breaking**, **unknown / manual review required**.

`P13-COMPAT-002` **`unknown` is a real, first-class outcome**, not a
placeholder. A change the checker cannot classify is `unknown` and requires
manual review; it is never defaulted to compatible.

`P13-COMPAT-003` **An additive change is not automatically safe.** Adding a
field changes what a payload means if the field's absence previously
carried meaning, if a consumer's validation is strict, or if the new field
creates an obligation the consumer does not know about.

### 14.1 Changes that are potentially breaking regardless of shape

| Change                             | Why it can break                                                               |
| ---------------------------------- | ------------------------------------------------------------------------------ |
| Removing a field                   | A consumer reads it                                                            |
| Changing a type                    | Parsing and comparison change                                                  |
| **Changing an enum's meaning**     | The wire value is unchanged, so no differ sees it; every consumer is now wrong |
| Tightening required fields         | Previously valid producers become invalid                                      |
| Changing a default                 | The absent case now means something else                                       |
| **Changing reason-code semantics** | A refusal now means something different to every reader, including auditors    |
| Changing event meaning             | As above, across history                                                       |
| Changing organization scope        | An isolation boundary moves                                                    |
| **Changing identity linkage**      | Potentially defeats `FIR-INV-001` or `FIR-INV-002`                             |
| Changing retention semantics       | A record's lawful lifetime changes                                             |
| Changing authorization implication | A field that gated access no longer does                                       |
| **Changing legal effect**          | The most dangerous of all, and invisible to every automated tool               |

`P13-COMPAT-004` The four rows in bold are **never** classifiable by an
automated checker and always require the semantic review in §17.

---

## 15. API contract evolution

`P13-API-001` **Endpoint identity is stable.** A path that means one thing
never comes to mean another.

`P13-API-002` Request and response schemas are **versioned**.

`P13-API-003` **Additive evolution is preferred** — subject to
`P13-COMPAT-003`.

`P13-API-004` **Deprecation is explicit**, announced, dated and
discoverable through the registry.

`P13-API-005` **No silent semantic change.** If the meaning changes, the
version changes.

`P13-API-006` **A field is never reused for a new meaning.** A retired
field name stays retired.

`P13-API-007` **Reason-code meaning never changes.** A new meaning needs a
new code.

`P13-API-008` **No hidden privilege expansion.** A contract change that
widens what a caller can reach is a privileged change requiring PACK-12
authority, whatever its shape.

`P13-API-009` **No field is removed before consumer migration** is
demonstrated through the consumer registry.

`P13-API-010` Pagination, error and idempotency contracts are **stable
across versions** unless explicitly versioned themselves.

`P13-API-011` **Version negotiation** is explicit; there is no "latest"
that silently moves under a caller.

`P13-API-012` A **coexistence window** is defined per breaking change, with
a stated end date.

`P13-API-013` Consumer telemetry carries **no sensitive payload** — which
consumers use which version, not what they sent.

`P13-API-014` A **rollback path** exists and is stated, or the change is
explicitly declared forward-fix-only with that consequence accepted.

Minimum models: `ApiContract`, `ApiVersion`, `ApiDeprecation`,
`ConsumerCompatibilityStatus`, `ApiMigrationPlan`.

---

## 16. Event contract evolution

`P13-EVO-001` **Event names are stable** and follow canon §20's
aggregate-prefixed convention.

`P13-EVO-002` Envelope version, payload version and schema version are
**distinct and separately recorded**.

`P13-EVO-003` **A historical event is never rewritten.** Not by a
migration, not by a replay, not by an upcaster, not to fix a mistake. A
mistake is corrected by a new, corrective event that references the
original.

`P13-EVO-004` **A new schema does not change the meaning of an old event.**

`P13-EVO-005` A consumer **declares the versions it supports**.

`P13-EVO-006` An **unsupported version fails closed** or goes to a
controlled dead-letter — never a best-effort partial parse.

`P13-EVO-007` **Upcasters are deterministic and testable.** The same input
always produces the same output, and the transformation is covered by
tests over recorded historical payloads.

`P13-EVO-008` **An upcaster invents no legal facts.** It may restructure,
rename and set values that are provably implied by the original. It may
not supply a consent, an authority, an approval, a classification or a
date that the original did not carry. Where the new schema requires a fact
the old event lacks, the correct outcome is an explicit "not determined"
value or a refusal — never a plausible default.

`P13-EVO-009` **Downcasting is permitted only where losslessness is
demonstrated**, and the demonstration is recorded.

`P13-EVO-010` **Field removal requires a deprecation cycle** with consumer
migration evidence.

`P13-EVO-011` **Enum extension is assessed on its own**, never assumed
additive-safe.

`P13-EVO-012` **An unknown enum value never silently maps to a default.**
It is surfaced as unknown and handled with a reason code. Defaulting an
unknown status to "normal" is how a novel failure becomes invisible.

---

## 17. Contract change governance

`P13-GOV-001` Every contract change follows:

```text
change proposed
→ impact assessed
→ compatibility classified
→ security / privacy / legal review where required
→ consumer impact reviewed
→ migration plan approved
→ schema published
→ coexistence period
→ consumer migration
→ deprecation
→ retirement
```

`P13-GOV-002` A **breaking change** must record: explicit reason; owner;
impact; affected domains; migration plan; rollback; data migration; event
replay impact; API coexistence; deadline; approval; evidence; final
retirement decision. A breaking change missing any of these is not
approvable.

`P13-GOV-003` **Security, privacy or legal review is mandatory** where the
change touches classification, retention, authorization implication,
identity linkage, organizational scope or legal effect.

`P13-GOV-004` **A feature flag may not be used to bypass a compatibility
or migration gate.** This restates `FIR-INV-006` in the contract domain: a
gate a flag can skip was never a gate. A flag may control _rollout_ of an
already-approved, already-compatible change; it may not stand in for the
approval.

`P13-GOV-005` Approval authority for a breaking change is separated from
the authority that proposed it (PACK-12 separation of duties).

---

## 18. Database migration discipline

`P13-MIG-001` **A migration is immutable once applied.** Editing an applied
migration is forbidden; a correction is a **new** migration.

`P13-MIG-002` Every migration has a **stable ID**.

`P13-MIG-003` Migration **order is deterministic** and does not depend on
filesystem ordering, timestamps of authorship or discovery order.

`P13-MIG-004` A **checksum is mandatory** and verified before application.
A checksum mismatch on an applied migration halts and escalates; it is
never auto-repaired.

`P13-MIG-005` The **expand/contract pattern is preferred** (§19).

`P13-MIG-006` A **destructive migration requires separate approval** with
separation of duties.

`P13-MIG-007` **Data migration is separated from schema migration** where
the risk is material, so that a failure in one does not force a rollback of
the other.

`P13-MIG-008` A large migration has a **batching and resume strategy**.

`P13-MIG-009` **Rollback is either real or explicitly declared
forward-fix-only.** A rollback script that has never been exercised is
declared as untested rather than presented as a safety net.

`P13-MIG-010` A migration has a **dry-run and evidence** of it.

`P13-MIG-011` **No manual, undocumented production SQL.** Direct SQL is a
governed act under PACK-12 (§26), performed in a migration or emergency
context that leaves session evidence.

`P13-MIG-012` **Organizational scope is never lost** by a migration.

`P13-MIG-013` **Retention and legal-hold records are not deleted** by a
migration without an explicit policy decision.

`P13-MIG-014` **Document and evidence linkage (PACK-11) is never broken**,
and no migration rewrites a hash-linked history.

`P13-MIG-015` **No migration creates a global user identifier**
(`FIR-INV-001`), and this is checked as an explicit acceptance criterion,
not left to reviewer vigilance.

`P13-MIG-016` **No migration weakens voting unlinkability**
(`FIR-INV-002`).

Minimum models: `MigrationDefinition`, `MigrationPlan`,
`MigrationExecution`, `MigrationCheckpoint`, `MigrationVerification`,
`MigrationRollbackDecision`, `DataBackfillReference`.

---

## 19. Expand/contract

`P13-XC-001` The normative sequence:

1. add the new compatible structure;
2. deploy dual-read or dual-write **only if governed**;
3. backfill;
4. verify;
5. migrate consumers;
6. stop old writes;
7. observe;
8. remove the old structure;
9. archive evidence.

`P13-XC-002` **Dual-write requires a reconciliation strategy** — a defined
way to detect and resolve divergence between the two destinations, with
its own evidence. Dual-write without reconciliation is two sources of
truth pretending to be one.

`P13-XC-003` Step 7 (observe) has a **stated minimum duration** per change
class, so that "remove the old structure" is never same-day with "stop old
writes".

`P13-XC-004` Step 8 is a destructive migration and inherits `P13-MIG-006`.

---

## 20. Data backfill

`P13-BF-001` Deterministic. `P13-BF-002` Restartable.
`P13-BF-003` Idempotent. `P13-BF-004` Checkpointed.
`P13-BF-005` Rate-limited. `P13-BF-006` Organization-aware.
`P13-BF-007` Policy-aware (retention, hold, classification).
`P13-BF-008` Audited. `P13-BF-009` Verifiable.

`P13-BF-010` **A backfill does not bypass domain invariants.** Writing
through the database rather than the domain does not make an invalid
record valid.

`P13-BF-011` **A backfill invents no missing facts.** Where the source
lacks a value the target requires, the record is routed to review — never
filled with a default, an inference, or "the most likely value".

`P13-BF-012` **Unresolved records go to a review queue** with their reason,
and the backfill reports them rather than completing silently.

`P13-BF-013` **No sensitive data in backfill logs.**

`P13-BF-014` A **final reconciliation report** states counts processed,
succeeded, routed to review, and failed, and is retained as evidence.

---

## 21. Projections and read models

`P13-PROJ-001` Every projection has a **named owner**, declared **source
events**, a **schema version** and a **rebuild strategy**.

`P13-PROJ-002` A read model is **not authoritative**.

`P13-PROJ-003` A read model **creates no legal effect**. A decision with
legal effect reads the authoritative record.

`P13-PROJ-004` **A projection never widens source authorization.** If the
reader could not read the source, the projection does not let them read
the derivative.

`P13-PROJ-005` **A projection is not a hidden cross-domain database.** A
projection joining several domains is admissible only where every source
domain has approved that specific projection under ADR, and the result
carries the narrowest authorization of its inputs.

`P13-PROJ-006` **No projection uses a global identity bridge**
(`FIR-INV-001`).

`P13-PROJ-007` A projection declared rebuildable **is** rebuildable from
approved sources alone, and this is tested, not asserted.

`P13-PROJ-008` **Staleness is visible.** Where a consequential decision
depends on freshness, the projection exposes its lag and the decision path
reads it. A stale projection that looks fresh is worse than one that is
plainly unavailable.

`P13-PROJ-009` **Deletion propagates.** When a source record is deleted or
tombstoned under PACK-09, every projection derived from it is updated, and
the propagation is evidenced. A projection that outlives its source is an
undeletable copy.

`P13-PROJ-010` **Legal hold propagates** to projections as a preservation
obligation — and, per `P13-RET-005`, still authorizes no access.

`P13-PROJ-011` Organizational scope is carried into every projection.

`P13-PROJ-012` A projection **failure state is explicit** and alertable.

---

## 22. Search integration (PACK-12 remains the policy owner)

`P13-SRCH-001` PACK-13 supplies **delivery and persistence contracts** for
PACK-12's search. It does not restate, extend or relax PACK-12 search
policy.

`P13-SRCH-002` A search projection carries **index version**, **source
version** and **authorization version**, so PACK-12's staleness and
cache-partitioning rules have real values to read.

`P13-SRCH-003` Deletion produces an **index tombstone**, and removal from
the index produces **index-removal evidence** referencing the source
decision (PACK-12 `P12-SRCH-015`).

`P13-SRCH-004` **Reindex** is a governed operation with its own event.

`P13-SRCH-005` **Projection lag is exposed** to the search path.

`P13-SRCH-006` **No unrelated domain writes to the search engine.**

`P13-SRCH-007` **The search engine is never an authoritative source.** It
holds pointers and permitted fields; the truth stays with the owning
domain.

---

## 23. Export integration (PACK-12 remains the policy owner)

`P13-EXPORT-001` PACK-13 supplies persistence and delivery contracts for
PACK-12 governed export, and changes no export policy.

`P13-EXPORT-002` Export request persistence; **immutable manifest**;
artifact metadata; delivery reference; access log; expiry; revocation;
destruction attestation; cumulative release history are all persisted with
the semantics PACK-12 defines.

`P13-EXPORT-003` **No forbidden ballot content is stored** anywhere in the
export data plane.

`P13-EXPORT-004` **There is no raw database export bypass.** A dump,
replica, backup extract or analytics copy is not an export route; any path
that produces data for a recipient goes through PACK-12's governed export.
This is the single most likely way the export controls get defeated, and it
is defeated by infrastructure, not by application code.

---

## 24. Records, retention and legal hold (PACK-09 remains the owner)

`P13-RET-001` Every persistent class maps to a **record class** where
PACK-09 defines one.

`P13-RET-002` Each carries a **retention schedule reference**, a
**deletion eligibility** state and a **legal hold** state.

`P13-RET-003` Deletion produces **deletion evidence** and, where the domain
requires it, a **tombstone** that records that something was deleted
without preserving what.

`P13-RET-004` **Backup retention is considered explicitly.** A record
deleted from the live database but present in backups is not deleted; the
policy states the backup horizon and the consequence.

`P13-RET-005` **A legal hold preserves data. It does not authorize access,
search, export or publication.** This is restated here because the data
plane is exactly where the confusion would be operationalised: the
practical meaning of a hold is "the deletion job skips this", never "the
investigator may read this".

`P13-RET-006` Retention applies to **projections and caches**, **events and
outbox records**, **schema registry entries** and **migration evidence** —
each with its own schedule, none exempt by virtue of being infrastructure.

---

## 25. Governed documents and evidence (PACK-11 remains the owner)

`P13-DOC-001` A schema definition **may itself be a governed document**
where the domain requires it, in which case it lives under PACK-11's
version chain.

`P13-DOC-002` Migration plans and verification reports use **evidence
references** (PACK-11), not ad-hoc file paths.

`P13-DOC-003` A **schema publication decision has evidence**.

`P13-DOC-004` **Historical schemas remain immutable**; replacement is
**supersession**, and digest and version history are preserved.

`P13-DOC-005` A generated artifact never replaces the authoritative
governed record.

---

## 26. Security and privileged operations (PACK-12 remains the owner)

`P13-SEC-001` **Database operator privilege is not domain-content
authority.** Holding `SUPERUSER` on the cluster confers no right to read a
membership record.

`P13-SEC-002` **Migration execution requires a scoped privileged grant**
under PACK-12 — purpose-bound, time-bound, approved, evidenced.

`P13-SEC-003` **Direct SQL requires a governed migration or emergency
context**, and produces PACK-12 session evidence.

`P13-SEC-004` **Schema publication and destructive migration require
separation of duties.**

`P13-SEC-005` **There is no universal database administrator with
unrestricted domain-content access.** The role that operates the cluster
and the role that may read a domain's content are different roles, and
`FIR-INV-014` makes them incompatible.

`P13-SEC-006` **Break-glass disables no audit and no invariant**
(`FIR-INV-006`).

`P13-SEC-007` Export and search boundaries hold in the data plane
(`P13-EXPORT-004`, `P13-SRCH-006`).

---

## 27. Identity boundary (PACK-14 establishes the owner)

`P13-ID-001` **No global user ID** (`FIR-INV-001`).

`P13-ID-002` Account, person, membership and each domain's subject
reference remain **separate identifiers**.

`P13-ID-003` **Actor references are scoped**, and the audit trail records
the acting authority rather than the human behind it.

`P13-ID-004` **No identity correlation through database convenience keys.**

`P13-ID-005` Any future identity mapping crosses an **explicit governed
boundary** with its own authorization, not a foreign key.

`P13-ID-008` The identity boundary is a **reserved future ownership
boundary**: its owner is **to be established by PACK-14**, PACK-13 assigns
no final service name and creates no schema for it, and whatever owner is
established must comply with the PACK-13 data-plane contracts
(`P13-OWN-009`..`013`).

`P13-ID-006` **No shared session semantics are encoded in persistence.**

`P13-ID-007` **Voting credentials remain separate** and outside this data
plane.

---

## 28. Voting boundary (PACK-15/16 own the voting architecture)

### 28.1 What PACK-13 fixes — general data-plane constraints

Prohibited without exception:

`P13-VOTE-001` No common person-to-ballot table.
`P13-VOTE-002` No ballot content or voting secret in any general domain
database.
`P13-VOTE-003` No linkage between an eligibility record and a ballot in any
general schema.
`P13-VOTE-004` No intermediate tally in any general analytics projection.
`P13-VOTE-005` No publication of partial results.
`P13-VOTE-006` No identity-linked ballot payload on the general event bus.
`P13-VOTE-007` No global member or account identifier used as a Voting
Client identifier.

These are constraints on **the general data plane** — the thing PACK-13
actually specifies. Each is testable as a structural absence.

### 28.2 What PACK-13 deliberately does not decide

`P13-VOTE-008` PACK-13 **does not prescribe** the voting domain's:

- broker topics or topic naming;
- whether its broker deployment is separate from or shared with the general
  plane;
- connection-pool topology;
- service names;
- credential topology;
- transport provider.

Each of those is a **PACK-15/16 decision**, taken together with that pack's
own threat model. Fixing them here would be deciding a security
architecture from outside the pack that owns it, on the basis of a threat
model that has not been written — and a topology chosen that way tends to
be defended later rather than reconsidered.

`P13-VOTE-009` **The future voting architecture must demonstrate isolation
and unlinkability** against its own threat model. PACK-13 supplies the
general data-plane constraints in §28.1 and no more; it does not discharge
that obligation and does not claim to.

`P13-VOTE-010` Where the PACK-15/16 threat model requires it, **separate
infrastructure is the preferred reference direction**. This is a stated
direction, not a topology decision already taken by PACK-13.

`P13-VOTE-011` PACK-13 **reserves no space** for the voting domain in the
general schema (`P13-OWN-011`).

---

## 29. Availability and failure modes

For every condition below the implementation round defines detection,
degraded behaviour, operator action and residual risk. For **consequential
actions** the behaviour is **fail-closed or safe-degraded**, never
optimistic.

| Condition                     | Required posture                                                              |
| ----------------------------- | ----------------------------------------------------------------------------- |
| Database unavailable          | Fail closed; no consequential action proceeds on cached state                 |
| Read replica stale            | Staleness surfaced; consequential reads go to primary or refuse               |
| Broker unavailable            | Commands still commit; outbox backlog grows; publication is pending, not lost |
| Outbox backlog                | Alerted with thresholds; backlog is a first-class health signal               |
| Schema registry unavailable   | Publication blocked; existing traffic continues on already-resolved schemas   |
| Consumer lag                  | Exposed; consequential consumers surface it                                   |
| Migration partial failure     | Halt, preserve state, escalate; never auto-continue                           |
| Projection rebuild failure    | Projection marked failed and stale; not silently serving partial data         |
| Duplicate event               | Absorbed by idempotency; counted                                              |
| Incompatible schema           | Fail closed for consequential consumers; dead-letter                          |
| Dead-letter accumulation      | Alerted; review obligation                                                    |
| Storage nearing capacity      | Alerted before write failure; retention review triggered                      |
| Clock skew                    | Detected; ordering unaffected by design (`P13-ORD-009`)                       |
| Corrupted checksum            | Halt and escalate; never auto-repair                                          |
| Failed legal-hold propagation | **Fail closed** — deletion does not proceed where hold state is unknown       |

---

## 30. Observability

`P13-OBS-001` Metrics, traces, structured logs, health endpoints, queue
lag, outbox backlog, migration progress, schema compatibility failures,
consumer errors, retry counts, dead-letter volume, projection staleness and
database saturation are all exposed.

`P13-OBS-002` **Forbidden in any telemetry**: plaintext secrets; full
personal records; ballot content; document payload; export payload; global
identity correlation; unrestricted query text.

`P13-OBS-003` A trace correlation identifier is **not** an identity
correlation identifier, and must not become one by carrying a subject
reference across domains.

`P13-OBS-004` **Log volume is not an excuse for lower classification.**
Operational logs containing personal data are classified and retained as
such.

---

## 31. Backup and recovery boundary (PACK-17 is not implemented here)

`P13-BAK-001` Requirements are defined here; the capability belongs to
PACK-17.

`P13-BAK-002` Backup **consistency** is defined (what is captured together).

`P13-BAK-003` The **schema version** is captured with the backup.

`P13-BAK-004` **Migration state** is captured.

`P13-BAK-005` An **encryption reference** is recorded.

`P13-BAK-006` **Restore ordering** is defined across schemas.

`P13-BAK-007` **Outbox and broker reconciliation after restore** is
defined — a restore that replays already-delivered events is a duplicate
storm, and a restore that drops undelivered ones is silent loss.

`P13-BAK-008` **Replay checkpoints** are captured.

`P13-BAK-009` **Legal hold is preserved** across backup and restore.

`P13-BAK-010` **Audit and evidence are preserved.**

`P13-BAK-011` **Backup readiness is not claimed without a restore test.**
An untested backup is a hypothesis.

---

## 32. Frontend boundary

`P13-FE-001` PACK-13 is **not** FRONT-PACK. Only administrative surfaces
are specified: schema registry review; compatibility assessment; migration
approval; migration status; consumer readiness; dead-letter review;
projection health; outbox backlog; read-model staleness; operational
data-plane status.

`P13-FE-002` **No universal admin console.**

`P13-FE-003` The frontend is **not a security boundary**; the backend
re-checks every action.

`P13-FE-004` No secrets, no unrestricted raw database content.

`P13-FE-005` **No arbitrary SQL execution from any surface.**

`P13-FE-006` No surface bypasses a PACK-12 privileged grant.

`P13-FE-007` Accessibility obligations are preserved (`FIR-INV-012`).

`P13-FE-008` **No surface claims that production infrastructure is
active.**

---

## 33. Reference-to-production migration path

`P13-PATH-001` The existing in-memory storage **ports** are the migration
seam. A production adapter implements the same port; the domain layer does
not change.

`P13-PATH-002` A port that cannot be implemented against a real database
without changing domain semantics is a **defect in the port**, to be fixed
in the port, not worked around in the adapter.

`P13-PATH-003` The in-memory adapters are **retained as test doubles**
after the production adapters exist.

`P13-PATH-004` Migration proceeds **domain by domain**, each with its own
acceptance evidence. A single big-bang cutover is not the plan.

`P13-PATH-005` **No storage port acquires a delete method** in the course
of this work (PACK-11, PACK-12).

---

## 34. Explicit exclusions

PACK-13 does not implement, provide or activate: external IAM and
authentication; real eID/KYC; the Voting Client; any voting protocol;
production event broker deployment; a managed PostgreSQL provider;
multi-region deployment; HSM/PKI; an incident-response platform; backup
recovery testing; real payment or banking integrations; full frontend
workspaces; public transparency portal changes; a production observability
vendor; legal activation; data-centre or provider procurement.

**No production-readiness claim and no legal-activation claim is made by
this round** (`FIR-INV-015`).

---

## 35. Requirement index

| Prefix         | Area                        | Section |
| -------------- | --------------------------- | ------- |
| `P13-CTX-*`    | Bounded contexts            | §3      |
| `P13-DP-*`     | Data plane and prohibitions | §4, §5  |
| `P13-TX-*`     | Transactions                | §6      |
| `P13-CC-*`     | Concurrency                 | §7      |
| `P13-OBX-*`    | Outbox                      | §8      |
| `P13-DEL-*`    | Delivery                    | §9      |
| `P13-ORD-*`    | Ordering                    | §10     |
| `P13-IDEM-*`   | Idempotency                 | §11     |
| `P13-REG-*`    | Schema registry             | §12     |
| `P13-FMT-*`    | Formats                     | §13     |
| `P13-COMPAT-*` | Compatibility               | §14     |
| `P13-API-*`    | API evolution               | §15     |
| `P13-EVO-*`    | Event evolution             | §16     |
| `P13-GOV-*`    | Change governance           | §17     |
| `P13-MIG-*`    | Migrations                  | §18     |
| `P13-XC-*`     | Expand/contract             | §19     |
| `P13-BF-*`     | Backfill                    | §20     |
| `P13-PROJ-*`   | Projections                 | §21     |
| `P13-SRCH-*`   | Search integration          | §22     |
| `P13-EXPORT-*` | Export integration          | §23     |
| `P13-RET-*`    | Retention and hold          | §24     |
| `P13-DOC-*`    | Documents and evidence      | §25     |
| `P13-SEC-*`    | Security and privilege      | §26     |
| `P13-ID-*`     | Identity boundary           | §27     |
| `P13-VOTE-*`   | Voting boundary             | §28     |
| `P13-OBS-*`    | Observability               | §30     |
| `P13-BAK-*`    | Backup boundary             | §31     |
| `P13-FE-*`     | Frontend boundary           | §32     |
| `P13-PATH-*`   | Migration path              | §33     |
