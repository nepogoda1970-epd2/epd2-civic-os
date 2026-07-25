# ADR-002: Identity/participation separation and canonical event/name resolution for CLAUDE-PACK-02

## Status

Accepted for CLAUDE-PACK-02 v0.1.0

## Date

2026-07-21

## Context

CLAUDE-PACK-02 ("Identity Separation and Audit Kernel") requires implementing
five bounded contexts — Account, Identity, Eligibility, Credential, Audit —
as independent services with no shared storage and no identity-to-credential
linkage (INV-01, INV-02, INV-03). The pack's own specification (section 2)
states that where it conflicts with `docs/canonical/TZ-00-domain-event-canon.md`,
the canon takes priority, and any necessary deviation must be recorded in an
ADR before code changes. Comparing the pack's suggested field/event names
(sections 6.1, 8.1, 8.2) against the canon's actual definitions (sections
7.2, 7.3, 9, 10, 18.1, 20, 21) surfaced several concrete mismatches that this
ADR resolves before any service code was written, per the pack's own
required order of work (section 18, step 3).

## Problem

1. The pack's suggested event envelope fields (section 8.1: `recorded_at`,
   `aggregate_type`, `aggregate_id`, `actor_ref`, `reason_codes`,
   `payload_schema_ref`, `canon_version`) do not match the canon's actual
   event envelope (section 21: `actor {actor_id, actor_type}`,
   `subject {subject_type, subject_id}`, `integrity {payload_hash,
signature}`, no `recorded_at`/`reason_codes`/`payload_schema_ref`/
   `canon_version`).
2. Several event names the pack suggests (section 8.2) do not exist in the
   canon's list of canonical system events (section 20): `account.status_changed`,
   `identity.verification_recorded`, `identity.verification_revoked`,
   `credential.validated`, `audit.event_recorded`.
3. The pack's `ParticipationCredential` field list (section 6.1) and the
   canon's `ParticipationCredential` field list (section 10.1) do not fully
   overlap.

## Considered options

- Option A — follow the pack's suggested envelope/event names literally,
  treating the pack as authoritative for PACK-02.
- Option B — follow the canon literally wherever it defines a shape or
  name, and resolve every gap the pack points at using the canon's own
  existing structures (rather than inventing new non-canonical fields or
  event names), documenting every resulting difference from the pack's
  suggestions here.
- Option C — invent new canon-adjacent fields/events (e.g. add
  `recorded_at` directly to the section-21 envelope, add a
  `credential.validated` / `identity.verification_revoked` / `account.status_changed`
  event) without an accepted canon version bump.

## Decision

Option B. Per the pack's own section 2, the canon wins on conflict. Concretely:

1. **Event envelope**: services emit events using the canon's section-21
   shape exactly (`event_id`, `event_type`, `event_version`, `occurred_at`,
   `producer`, `actor {actor_id, actor_type}`, `subject {subject_type,
subject_id}`, `correlation_id`, `causation_id`, `payload`,
   `integrity {payload_hash, signature}}`), implemented in
   `epd2_core.event_envelope`. The pack's additional suggested fields are
   satisfied by the canon's _separate_ `AuditEvent` entity (section 18.1),
   which already has `recorded_at`, `reason_code`, `previous_event_hash`,
   `event_hash`, `policy_version` — Audit Core derives an `AuditEvent` from
   an emitted event envelope rather than the envelope itself growing those
   fields. `payload_schema_ref` and `canon_version` are repository/tooling
   concerns (schema-registry lookup, version constants already in
   `epd2_core.version`), not wire fields, and are kept out of the envelope.
2. **Event names**: every event a PACK-02 service emits uses a name from
   the canon's section-20 list, not the pack's suggested name, whenever the
   two differ:
   - `account.status_changed` → the specific canonical name for the
     transition (`account.restricted`, `account.suspended`,
     `account.closed`). Transitions with no canonical event name (e.g.
     `pending → active`) do not emit a canonical event; INV-04's mandatory
     audit list does not include generic account activation.
   - `identity.verification_recorded` → `identity.verified` on a
     successful verification, `identity.verification_failed` on a failed
     one (both canonical).
   - `identity.verification_revoked` → the canon defines no revocation
     event for `IdentityRecord`. This ADR maps an explicit revocation to
     `identity.verification_expired` (canonical), since revoking a
     verification early has the same practical effect on downstream
     eligibility as expiry — the record can no longer be relied on. A
     dedicated `identity.verification_revoked` canonical event name is
     recommended as a future canon minor-version proposal (see
     `docs/review/OPEN_QUESTIONS.md`); it is not added unilaterally here.
   - `credential.validated` → the canon has no such event. A successful
     validation is a read/query operation, not a state change, and is not
     independently audited as a domain event (INV-04's list concerns state
     changes, not queries). A _failed_ validation uses the canonical
     `credential.validation_failed`.
   - `audit.event_recorded` → not implemented. An `AuditEvent` is itself
     the durable record; a second event announcing "an audit event was
     recorded" would be a redundant meta-event with no canonical basis.
     CT-00-07 ("critical action creates an AuditEvent") is satisfied by
     every critical command calling Audit Core's `append` directly.
3. **`ParticipationCredential` fields**: implement the union of the pack's
   field list (section 6.1) and the canon's field list (section 10.1) —
   `credential_id`, `credential_type`, `scope_type`, `scope_id`,
   `issued_at`, `valid_from`, `expires_at`, `status`, `usage_limit`,
   `usage_counter`, `revocation_status`, `issuer_signature`,
   `credential_version`, `rule_version`, `eligibility_snapshot_digest`.
   Neither source's requirement is dropped. Fields the pack explicitly
   forbids (section 5.2 — `identity_record_id`, `person_id`, `account_id`,
   `full_name`, `date_of_birth`, `address`, `email`, `eid_subject`, or any
   other identity-linking field) are never added, and this is enforced by
   an automated identity-leakage test that introspects the dataclass.

## Consequences

Every event name and envelope field a PACK-02 service emits is traceable to
an explicit canon section. `contracts/events/` schema file names and
`contracts/openapi/pack-02.yaml` operation names use canonical event names,
not the pack's suggested ones, so a future reader comparing this
implementation against the canon finds no unexplained divergence.

## Security impact

Directly supports INV-01 (identity/participation separation): the
`Eligibility Context` and `Identity Context` never appear as fields on
`ParticipationCredential`, and validation results never include identity
data (enforced by the identity-leakage test suite, section 12.2 of the
pack).

## Data impact

Establishes the exact field set for `ParticipationCredential`,
`EligibilityDecision`, `EligibilitySnapshot`, and `IdentityRecord` used by
this implementation (see `docs/architecture/identity-participation-separation.md`
for the full rationale and data-flow diagram).

## Migration impact

None — no PACK-02 entity existed before this ADR.

## Reversibility

Reversible with cost: changing event names or envelope shape later would
require a coordinated update of `contracts/events/`, `contracts/schemas/`,
`contracts/openapi/pack-02.yaml`, and every service's event-emission code,
plus a canon version bump if the canon itself changes.

## Related canon version

Authored against canon version `0.1.0`. Recommends (but does not itself
perform) a future minor-version proposal to add a canonical
`identity.verification_revoked` event — see
`docs/review/OPEN_QUESTIONS.md`.
