# Identity/Participation Separation

Status: implemented for CLAUDE-PACK-02 (`Account`, `IdentityRecord`,
`EligibilityRule`, `EligibilityDecision`, `EligibilitySnapshot`,
`ParticipationCredential`). This document explains how the five PACK-02
services jointly enforce canon `INV-01` ("real identity is not stored next
to secret vote content, delegated-vote records, anonymous political
actions, closed assessments, or ballots") together with `INV-02` (single
owner per entity) and `INV-03` (no direct access to another module's
storage). It supersedes the "Not implemented" placeholder previously
carried in `docs/architecture/data-ownership.md` for these seven entities.

See `docs/adr/ADR-002-identity-participation-separation.md` for the
decision record behind the specific field/event/name choices below, and
`docs/review/PACK-02-THREAT-MODEL.md` for the threat analysis this
separation is meant to defend against.

## 1. The mandatory data-flow

```text
Identity verification
  -> IdentityRecord               (Identity Service, owns IdentityRecord)
  -> Eligibility evaluation
  -> EligibilityDecision          (Eligibility Service, owns EligibilityRule/
  -> EligibilitySnapshot             EligibilityDecision/EligibilitySnapshot)
  -> ParticipationCredential      (Credential Service, owns ParticipationCredential)
  -> participation systems validate credential only
```

Each arrow is a one-way, one-time hand-off through an explicit application
call (not a shared table): a caller supplies the upstream result as an
input value to the downstream service's own command. No PACK-02 service
reads another PACK-02 service's storage adapter directly — this is the
same structural rule `docs/architecture/service-boundaries.md` states for
the platform generally, applied concretely to this one chain.

A future participation system (voting, delegation, discussion — none of
which PACK-02 implements) is expected to call only
`ValidateParticipationCredential` and see only what section 3 below lists.
It has no code path to `IdentityRecord`, full name, date of birth, address,
or the eID-provider subject identifier, because `ParticipationCredential`
never carries them (section 2) and no PACK-02 API exposes `IdentityRecord`
to a caller outside Identity Service.

## 2. Forbidden fields (enforced, not just documented)

Per pack section 5.2, `ParticipationCredential` must never gain any of:
`identity_record_id`, `person_id`, `account_id`, `full_name`,
`date_of_birth`, `address`, `email`, `eid_subject`, or any other direct or
reversibly-encoded identity reference.

This is enforced structurally, not by convention:

- `services/credential-service/src/epd2_credential_service/domain.py`
  defines `FORBIDDEN_FIELD_NAMES` and `ParticipationCredential` as a
  frozen dataclass whose field set is introspected by
  `tests/contract/test_ct00_08_identity_leakage.py` and
  `tests/contract/test_property_based.py` (Hypothesis: arbitrary subsets
  of `FORBIDDEN_FIELD_NAMES` are asserted absent from
  `ParticipationCredential.__dataclass_fields__`, not just the specific
  names anticipated at write time).
- `contracts/schemas/participation-credential.schema.json` sets
  `"additionalProperties": false`, so a schema-valid credential payload
  cannot carry an extra identity field even if some future code change
  tried to add one — a wire-level backstop independent of the Python
  dataclass.
- `tests/contract/test_ct00_09_vote_linkability.py` checks the weaker but
  still-meaningful structural property that `ParticipationCredential`
  shares no `*_id`-suffixed field name with `Account` or `IdentityRecord`
  — i.e. there is no join key between the credential and either identity
  entity, even indirectly.

## 3. What `ValidateParticipationCredential` actually returns

Per pack section 6.3, validation returns only: valid/invalid, the
permitted scope, the expiry, reason codes, and the credential version. It
never returns identity data, because there is none to return —
`ParticipationCredential` (section 2) and the validation result type both
lack any identity field, which
`tests/contract/test_ct00_08_identity_leakage.py` checks directly against
the real `ValidationResult` dataclass returned by
`epd2_credential_service.application.validate_participation_credential`.

## 4. The issuance reference (`issuance_reference`)

Credential Service is permitted (pack section 5.3) to keep an internal,
non-public `issuance_reference` for idempotency, revocation, and internal
issuance audit — but it must never be an identity identifier, must be
randomly generated (not derived from identity data — pack section 13.1
explicitly forbids deterministic credential ids computed from identity
data), must not be sent to downstream services, and must not appear in any
public event. In this implementation, Credential Service's own internal
`credential_id` plus its storage-level content dedup (see
`services/credential-service/src/epd2_credential_service/storage.py`)
serves this role directly; no separate identity-derived value is
introduced anywhere in the issuance path.

## 5. Eligibility as the deliberate chokepoint

`EligibilityDecision` (Eligibility Service) is the only entity in the chain
permitted to reference an identity attestation, and only "within the
strictly permitted service boundary" (pack section 7.2) — meaning
Eligibility Service may read whatever Identity Service passes it as an
input to `EvaluateEligibility`, but does not itself become a second copy
of `IdentityRecord`, and does not forward identity data past itself.
`EligibilitySnapshot` (pack section 7.3) is the immutable, minimal
issuance contract Credential Service actually receives — a digest
(`eligibility_snapshot_digest`) and the `rule_version`, not the underlying
claims. This is why `ParticipationCredential` carries
`eligibility_snapshot_digest` and `rule_version` rather than a reference
back to the `EligibilityDecision` or any identity attestation: a credential
holder's proof of eligibility is a fixed cryptographic digest of a
point-in-time decision, not a live pointer into Eligibility Service's own
data.

## 6. Rule-version freezing (CT-00-10)

`EligibilityRule` is versioned and immutable once created — an update to
an existing `(eligibility_rule_id, rule_version)` pair with different
content is rejected fail-closed (`ELIGIBILITY_RULE_VERSION_FROZEN`); a
genuinely new rule requires a new `rule_version`. The frozen rule version
that produced a given `EligibilityDecision`/`EligibilitySnapshot` is
carried forward unchanged onto the resulting `ParticipationCredential`
(`rule_version` field), so a credential's validity can always be checked
against the exact rule version that authorized it, not whatever rule
happens to be current at validation time. See
`tests/contract/test_ct00_10_rule_freeze.py`.

## 7. Ownership summary (this chain only)

| Entity                    | Owning service      | Never read directly by                      |
| ------------------------- | ------------------- | ------------------------------------------- |
| `Account`                 | account-service     | identity-, eligibility-, credential-service |
| `IdentityRecord`          | identity-service    | account-, eligibility-, credential-service  |
| `EligibilityRule`         | eligibility-service | account-, identity-, credential-service     |
| `EligibilityDecision`     | eligibility-service | account-, identity-, credential-service     |
| `EligibilitySnapshot`     | eligibility-service | account-, identity-, credential-service     |
| `ParticipationCredential` | credential-service  | account-, identity-, eligibility-service    |

Structural enforcement of "no service imports another service's internals"
is checked by AST-based service-boundary analysis (no PACK-02 service's
`src/` imports another PACK-02 service's `src/` package); each service
depends only on `epd2-core` (shared, non-domain primitives — see
`docs/architecture/service-boundaries.md`) and `epd2-audit-core` (the one
deliberate, one-directional dependency every domain service takes so it
can append its own `AuditEvent`s — see `docs/architecture/audit-kernel.md`).

## 8. What this document does not claim

This implementation is an in-memory reference implementation with opaque
credential references (pack section 6) — it does not implement blind
signatures, zero-knowledge proofs, or any cryptographic anonymity
guarantee, and none is claimed. "Unlinkability" here means exactly what
section 2's tests check: no shared identifier field between the credential
and the identity/account entities, not a cryptographic unlinkability
property. See `docs/review/PACK-02-THREAT-MODEL.md` for the residual risks
this leaves open (in particular: an operator with database-level access
across services, or correlation via timestamps/side channels, is out of
scope for this reference implementation).
