# Eligibility Service

Owns `EligibilityRule`, `EligibilityDecision`, `EligibilitySnapshot` (canon
section 9; ownership matrix section 22). No other service reads or writes
this service's storage directly (INV-03).

## Boundary with Identity Service

This service accepts identity **attestations** (e.g.
`{"verification_level": "verified", "membership_status": "active"}`) as a
plain `Mapping[str, str]` input to evaluation - it has **zero import
dependency** on `epd2_identity_service` and never receives an
`IdentityRecord` object. The caller (whatever wires services together —
tests, or a future orchestration layer) is responsible for extracting only
the attestation fields eligibility evaluation actually needs. This is what
makes the INV-02/INV-03 ownership boundary structurally, not just
procedurally, true: there is no import path from this package to Identity
Service's package.

## Rule immutability ("Rule Freeze", canon section 9.1)

An `EligibilityRule` is versioned and immutable: creating a new version
never mutates a previous one, and re-submitting the same
`(eligibility_rule_id, rule_version)` with different content is rejected
(CT-00-10 analogue for this entity — the pack's own CT-00-10 concerns
`Ballot`, out of scope here, but section 9.1's freeze requirement applies
equally to `EligibilityRule`).

## Snapshot

`EligibilitySnapshot` is immutable once created, carries `rule_version`
and a deterministic `digest` (canon section 9.3: "имеет hash"), and
records `eligible_count` so the number of admitted persons can be
independently verified without exposing any individual's identity.

## PACK-03 read boundary (ADR-008)

`application.get_eligibility_decision` and `application.get_eligibility_snapshot`
are two small, additive, unaudited read-only query functions added under
`docs/adr/ADR-008-pack-03-pack-02-integration-boundary.md`, which names
this module (never `epd2_eligibility_service.storage`) as the only
legitimate way `initiative-service` and `voting-service` may read this
service's already-published state (`SupportRecord` validation and
`Ballot.eligibility_rule_version` rule-freeze, respectively). Both are pure
lookups with no state change and no canonical event, the same shape
`validate_participation_credential` already established in
credential-service for a query that is not itself a domain command.
