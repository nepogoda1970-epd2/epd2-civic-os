# ADR-003: Append-only Audit Core with sequential hash chaining

## Status

Accepted for CLAUDE-PACK-02 v0.1.0

## Date

2026-07-21

## Context

CLAUDE-PACK-02 requires an Audit Core service that is append-only and
tamper-evident (pack section 9; canon INV-04, INV-05, section 18.1). The
pack explicitly requires this not be presented as a production-grade
blockchain or qualified electronic evidence — only a minimal tamper-evident
mechanism sufficient for contract tests (pack section 9.2).

## Problem

Decide the chaining granularity (one global chain vs. one chain per
aggregate), the canonical serialization used for hashing, and the
idempotency/conflict behavior for repeated `event_id`s, before writing the
storage adapter.

## Considered options

- Option A — one hash chain per `(target_type, target_id)` aggregate.
- Option B — a single global sequential hash chain across all `AuditEvent`
  records, with `list_by_aggregate` as a filtered read over that one chain.
- Option C — no chaining, only a checksum per record (rejected — the pack
  explicitly requires chaining, not per-record checksums, per section 9.2).

## Decision

Option B: a single global, sequential, append-only hash chain.

- Canonical serialization: every `AuditEvent`'s hashable representation is
  produced by `epd2_core.canonical_json.canonical_dumps`, which sorts keys
  and uses a fixed separator style, so the same logical content always
  serializes identically regardless of construction order — a prerequisite
  for both `event_hash` computation and Hypothesis-driven determinism
  tests (pack section 12.5).
- `event_hash = sha256(canonical_dumps(record_without_event_hash) +
previous_event_hash)`, where `previous_event_hash` is the `event_hash` of
  the immediately preceding record in the global chain (a fixed genesis
  constant for the first record).
- **Idempotency**: appending an `event_id` already present with identical
  content is a no-op success (returns the existing record). Appending the
  same `event_id` with different content is rejected fail-closed with a
  stable reason code (`AUDIT_EVENT_CONFLICT`) — the existing record is
  never overwritten.
- **Verification**: `verify_chain()` recomputes every `event_hash` in
  order and confirms each record's stored `previous_event_hash` matches
  the prior record's stored `event_hash`; any mismatch reports the first
  broken link's position, rather than only a boolean.
- A single global chain was chosen over one-chain-per-aggregate because
  `AuditEvent` (canon 18.1) already has a single owner (Audit Core) and a
  single conceptual audit log; per-aggregate chains would let an attacker
  with write access to one aggregate's chain tamper with it without
  affecting any other aggregate's verification, weakening the tamper
  evidence this ADR is meant to provide. `list_by_aggregate` remains a
  read-side filter, not a separate chain.

## Consequences

Every `AuditEvent` ever appended participates in one chain whose head hash
functionally attests to the entire audit history at that point. Verifying
the whole audit log after the fact means recomputing one chain, not N
chains. A future move to a real external ledger or a qualified electronic
evidence service would replace the storage adapter, not the domain
contract (`append`, `get_by_event_id`, `list_by_aggregate`, `verify_chain`).

## Security impact

This mechanism is explicitly **not** cryptographically signed and **not**
distributed — a party with write access to the in-memory/reference store
can, in principle, rebuild a consistent-looking alternate chain from
scratch. It only detects tampering with records that remain in place
without also regenerating every subsequent hash — i.e. it raises the cost
and detectability of undetected retroactive edits, it does not make them
impossible. This limitation is recorded in
`docs/review/PACK-02-THREAT-MODEL.md` ("event tampering" threat) rather
than left implicit.

## Data impact

Establishes the exact `AuditEvent` field set (canon 18.1, unchanged) and
adds no new persisted fields beyond what canon already requires.

## Migration impact

None — no `AuditEvent` records exist before this ADR.

## Reversibility

Reversible with cost: replacing the chaining algorithm later requires
either a documented "chain break" (recorded explicitly, not hidden) or a
recomputation of the entire existing chain under the new algorithm.

## Related canon version

Authored against canon version `0.1.0`. Does not propose a canon version
bump.
