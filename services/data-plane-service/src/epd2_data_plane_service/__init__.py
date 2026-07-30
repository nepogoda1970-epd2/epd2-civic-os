"""Data Plane Service — PACK-13's one wholly new service (ADR-069..078).

**PACK-13 IMPLEMENTATION CANDIDATE. NOT PASS. NOT PRODUCTION READY. NOT
LEGALLY ACTIVATED.**

The bounded implementation area for the five logical contexts the PACK-13
specification's §3 assigns to PACK-13 itself. It is one package because
they are one seam — the place where a domain command becomes a durable
fact and a published event — and it is deliberately **not** a
general-purpose platform: `P13-CTX-001` forbids any context here becoming
something a domain owner can be bypassed through, and nothing in this
package writes another domain's records.

Module map, in dependency order — each module imports only from those
above it:

- `exceptions` — one class per registered reason code, no domain knowledge.
- `domain` — scope, ownership, typed references, the prohibited payload
  keys, the reserved boundaries, the digest helpers. No I/O, no clock,
  no storage.
- `concurrency` — aggregate and expected version, conflict decisions,
  transaction and unit-of-work boundaries, command execution references.
- `idempotency` — scoped keys, records, decisions, deduplication and the
  permanent business-fact guard.
- `canonicalization` — the format-specific canonical forms and the
  content digest, kept separate from schema-version identity.
- `registry` — schema families, versions, lifecycle, ownership,
  publication decisions, consumers, deprecation and supersession.
- `compatibility` — the deterministic structural checker and the
  semantic-risk escalation to manual review.
- `contracts` — API and event contract evolution, deprecation windows,
  upcasters, consumer version support.
- `migrations` — definitions, plans, executions, checkpoints,
  verification, rollback decisions, expand/contract control.
- `backfill` — the deterministic, restartable, checkpointed runner and
  its review queue.
- `outbox` — the transactional outbox record, statuses, delivery
  attempts, publication evidence.
- `delivery` — dispatcher and consumer simulation, ordering scopes,
  gap detection, dead-letter, replay, consumer checkpoints.
- `projections` — definitions, lag, staleness, rebuild, deletion
  propagation, tombstones.
- `integration` — search-projection and governed-export persistence
  contracts. PACK-12 remains the policy owner of both.
- `retention` — retention bindings, deletion eligibility, legal hold and
  PACK-11 evidence references.
- `privileged` — the PACK-12 gates: scoped grants for migration
  execution, direct SQL, schema activation, operator privilege.
- `boundaries` — the structural guards: cross-domain access, audit
  ingestion, identity linkage, voting isolation.
- `events` — the thirty-seven canonical event builders, on the unchanged
  canon §21 envelope.
- `storage` — storage ports and in-memory reference adapters. No delete
  method exists on any port.
- `application` — the governed commands that compose all of the above.
- `administration` — contract-level reference administrative surfaces.

**The data plane is infrastructure. It is not an authority.** Persistence
here creates no capability the domain layer refuses: no join that no API
permits, no correlation `FIR-INV-001` forbids, no read PACK-12 would
decline. Every refusal in this package exists to keep that sentence true
when a convenient shortcut would make it false.

**Delivery guarantee: at-least-once, with effectively-once consumer
effect through idempotency.** The stronger phrase is claimed nowhere —
not in a document, not in a docstring, not in a comment, not in a log
message, not on any surface — and `tests/test_boundaries.py` scans this
package's own source to prove it (ADR-072, `P13-DEL-002`).

**What this service is not.** It carries no production data plane: every
adapter in `storage` is in memory. It deploys no PostgreSQL, no cloud
database, no Kafka, RabbitMQ or NATS broker, no external schema-registry
product, no production search engine, no production IAM. It implements no
identity domain (PACK-14), no eligibility, credential, voting or tally
domain (PACK-15/16), and no backup or restore capability (PACK-17). It
offers no arbitrary-SQL console and no universal administration surface.

**No second anything.** This package creates no parallel architecture, no
second audit framework, no second evidence system, no second reason-code
registry and no second master register. It submits audit records through
`audit-core`'s governed ingestion contract and holds no mutating control
over the chain, references PACK-11's evidence bundles rather than
inventing a data-plane evidence store, observes PACK-09's retention and
legal-hold decisions without making them, defers every search and export
policy question to PACK-12, and registers its reason codes in
`contracts/reason-codes/pack-13.yml` alongside every earlier pack's.

**No claim of production readiness or legal validity.** Nothing here
establishes that a production database exists, that a migration was
lawfully executed, that a schema is in production use, or that any of it
is operationally ready. See
`docs/handover/PACK-13-KNOWN-LIMITATIONS.md`.
"""

from __future__ import annotations

from epd2_core.version import CANON_VERSION, REPOSITORY_VERSION

#: The contexts this service implements, and the status that
#: implementation has. `reference_implementation` is the truthful value:
#: the governed workflows, the contract-evolution model and the refusal
#: surface are real and tested; the production data plane is not.
DATA_PLANE_CONTEXT_IMPLEMENTATION_STATUS = "reference_implementation"

#: The FIR entries this package fully implements. Every other entry the
#: PACK-13 FIR Coverage Matrix touches is foundation-only, contract-only
#: or a recorded dependency on PACK-14, PACK-15/16 or PACK-17, and is
#: deliberately absent here — a contract is not an implementation.
IMPLEMENTED_FIR_ENTRIES: tuple[str, ...] = ()

#: Recorded so a test can assert it: PACK-13's own roadmap entry is a
#: *candidate*, not an implementation, until an external pipeline says
#: otherwise.
CANDIDATE_FIR_ENTRIES: tuple[str, ...] = ("FIR-ROADMAP-003",)

__all__ = [
    "CANDIDATE_FIR_ENTRIES",
    "CANON_VERSION",
    "DATA_PLANE_CONTEXT_IMPLEMENTATION_STATUS",
    "IMPLEMENTED_FIR_ENTRIES",
    "REPOSITORY_VERSION",
]
