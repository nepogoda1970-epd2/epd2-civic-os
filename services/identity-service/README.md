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

## PACK-14 — Identity, Authentication & Account Security

PACK-14 extends this service **in place** with the six bounded contexts
its specification §4.1 assigns here: Account Registry, Credential
Registry, Authentication, Session Security, Recovery coordination and
Identity-Proofing references. Ownership of canon 7.3's `IdentityRecord`
and canon 7.2's `Account` is unchanged.

### Running the reference service

```python
from datetime import UTC, datetime
from epd2_identity_service.runtime import build_identity_service

runtime = build_identity_service(
    clock=my_clock,
    derivation_salt=my_32_byte_salt,
    database="identity.sqlite3",   # ":memory:" is the default
)
response = runtime.api.dispatch(request)
```

`build_identity_service` is the **only** composition root. It opens the
database through `migration_runner`, so the ten SQL artefacts in
`migrations/` are applied and verified before anything reads the schema,
and it binds the durable adapters from `sql_storage`.

### What is real, and what is not

| Real                                                                                             | Not provided                                                            |
| ------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------- |
| 10 SQL migration artefacts, applied in order in one transaction with a recorded SHA-256 checksum | A production database. This runs on SQLite through the standard library |
| 29 tables, 35 indexes (9 unique constraints, 10 expiry indexes)                                  | Replication, backup, failover, operational durability                   |
| 11 durable adapters, a `UnitOfWork`, an optimistic-concurrency guard                             | A production data plane — PACK-13 owns that                             |
| A runnable request/response boundary for 12 of 42 catalogued operations                          | An HTTP server, TLS, a gateway, a public deployment                     |
| Reason-coded responses; no secret or raw identifier can be serialized                            | Any real external provider                                              |

### Security ports refuse when unbound

`WebAuthnVerifier`, `PasswordHasher`, `BreachedPasswordChecker` and
`AssertionSignatureVerifier` all default to adapters that **raise**, so
an unconfigured deployment fails at the first attempt rather than after
an incident. In particular **no password may be enrolled or replaced
while no breached-password checker is bound**; the one governed
exception, `PasswordDegradedModeDecision`, permits authentication against
an already stored hash and has no field that could permit anything else.

### The in-memory adapters are test adapters

`account_security_storage` still holds an `InMemory*` adapter per port —
they are the cheapest way to unit-test a domain rule — but they are **not
the default runtime binding**, and
`tests/repository/test_pack14_default_binding.py` asserts that the
composition root names none of them.

The full picture is in `docs/packs/PACK-14/`.
