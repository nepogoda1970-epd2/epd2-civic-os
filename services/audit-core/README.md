# Audit Core

Owns `AuditEvent` (canon section 18.1; ownership matrix section 22). No
other service reads or writes this service's storage directly (INV-03).

## Responsibility

Append-only, hash-chained log of every politically or legally significant
action (INV-04, INV-05). See ADR-003 for the chaining design (single
global sequential chain, canonical-JSON hashing, idempotent append).

## Interface

- `append(request, *, clock)` — append a new `AuditEvent`. Idempotent by
  `audit_event_id`: an identical repeat succeeds as a no-op; a repeat with
  different content is rejected fail-closed (`AUDIT_EVENT_CONFLICT`).
- `get_by_event_id(audit_event_id)`
- `list_by_aggregate(target_type, target_id)`
- `verify_chain()` — recomputes every hash and reports the first broken
  link, if any.

## What this is not

Not a production-grade blockchain or qualified electronic evidence system
(pack section 9.2). Not signed. Not distributed. See
`docs/review/PACK-02-THREAT-MODEL.md` for the residual risk this implies.

## Storage

`InMemoryAuditEventStore` is the reference adapter used by contract tests.
A durable backend can implement the same `AuditEventStore` protocol
(`storage.py`) without changing `application.py` or any caller.
