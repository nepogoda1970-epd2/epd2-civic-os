# Credential Service

Owns `ParticipationCredential` (canon section 10.1; ownership matrix
section 22). This is the service INV-01 depends on most directly: **no
field, event, or validation result this service produces may ever
identify the person behind a credential.**

## Forbidden fields (pack section 5.2, canon section 10.1 "Запрет")

`ParticipationCredential` never has: `identity_record_id`, `person_id`,
`account_id`, `full_name`, `date_of_birth`, `address`, `email`,
`eid_subject`, or any other direct or reversibly-encoded identity
reference. Enforced structurally (the public dataclass's field set) and
by the repository-wide identity-leakage test suite
(`tests/contract/test_identity_leakage.py`).

## `issuance_reference` (pack section 5.3)

Internally, `storage.py` keeps a `_CredentialRecord` with one additional
field, `issuance_reference` — a randomly generated, non-identity-derived
string used only for idempotency and revocation bookkeeping _within this
service_. It is never included in the public `ParticipationCredential`
DTO, never returned from any command or query, and never appears in any
event payload (see `test_issuance_reference_never_leaves_the_service` in
`tests/test_storage.py`).

## Fail-closed validation (pack section 6.4)

`ValidateParticipationCredential` treats a credential as invalid on:
unknown status, unknown `credential_version`, expiry, missing required
scope, `rule_version` mismatch, a digest that does not match what was
recorded at issuance, revocation, or a duplicate/conflicting issuance
request. The validation result never includes identity data — only
valid/invalid, allowed scope, expiry, reason codes, and
`credential_version` (pack section 6.3).

## Field set (ADR-002)

`ParticipationCredential`'s fields are the union of the pack's own list
(section 6.1) and canon's list (section 10.1) — see ADR-002 for why
neither is dropped.
