# Identity Service

Owns `IdentityRecord` (canon section 7.3; ownership matrix section 22). No
other service reads or writes this service's storage directly (INV-03),
and in particular **Credential Service never receives an `IdentityRecord`
or any of its fields** (INV-01, pack section 5.1).

## Forbidden fields

Per canon section 7.3, `IdentityRecord` never contains: voting history,
chosen ballot options, initiative lists, political preferences, or
delegations. This is enforced structurally (the dataclass only has the
canon's fields) and by an automated identity-leakage test
(`tests/test_identity_leakage.py` at the repository root).

## Event naming resolution (see ADR-002)

- A recorded, successful verification emits canonical `identity.verified`.
- A recorded, failed verification emits canonical `identity.verification_failed`.
- An explicit revocation of a previously-verified record emits canonical
  `identity.verification_expired` — canon defines no dedicated revocation
  event; revoking has the same downstream effect as expiry (the record can
  no longer be relied on). A canonical `identity.verification_revoked`
  event name is recommended as a future canon minor-version proposal (see
  `docs/review/OPEN_QUESTIONS.md`), not added unilaterally here.
