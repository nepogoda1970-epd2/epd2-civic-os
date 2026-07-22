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
