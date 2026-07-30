**Round:** PACK-14 — implementation candidate. **NOT PASS. NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**
**Repository version:** `0.14.0` · **Canon version:** unchanged at `0.8.0`
**External GitHub Actions has not run against this round.**

# PACK-14 — Open Items

## 1. `OD-P14-07` — retention durations

**Status: open, pending legal confirmation. It does not block the
reference implementation.**

A retention period is a legal determination and PACK-09 owns retention
schedules; this pack may not settle one. What would block implementation
is not an unconfirmed number but an undefined behaviour, and the
behaviour is defined:

| What is settled and implemented                                      | Where                                                              |
| -------------------------------------------------------------------- | ------------------------------------------------------------------ |
| Which record classes exist and what each may contain                 | `persistence.PACK14_RETENTION` (10 classes)                        |
| That every class **has** a schedule and none is unbounded            | Every entry carries a duration or names PACK-09's statutory period |
| Deletion under a legal hold refuses                                  | `assert_disposition_permitted`                                     |
| An **unknown** hold state fails closed                               | `legal_hold_state=None` is treated as a hold                       |
| An open dispute preserves the record                                 | Same function                                                      |
| A destructive disposition against an unconfirmed schedule is refused | `RETENTION_SCHEDULE_UNCONFIRMED`                                   |
| Evidence survives closure                                            | Recovery and proofing evidence classes                             |
| Handoff records are deleted as a set                                 | Recorded in the binding's `deletion_effect`                        |

The provisional durations are **safe provisional schedules**: short
enough to limit exposure, long enough to answer a dispute. Every
`duration_confirmed` flag is `False`, and a test asserts that it is.
Confirming the durations changes configuration values, not the design.

**Nothing in this round destroys evidence**, because nothing in this
round can: every destructive path refuses while the flag is `False`.

## 2. Deployment obligations this round does not discharge

| Obligation                           | Consequence while unmet                                                                                            |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------------ |
| Bind a WebAuthn verifier             | Passkey registration and authentication refuse                                                                     |
| Bind a memory-hard password hasher   | Password enrollment and verification refuse                                                                        |
| Bind a breached-password checker     | **Password enrollment and password replacement refuse**                                                            |
| Bind an assertion signature verifier | Every external provider assertion refuses                                                                          |
| Bind a real notification outbox      | Notifications record an intent and go nowhere                                                                      |
| Bind a production data plane         | The reference SQLite path persists and is testable; production durability, replication and backup are not provided |

## 3. Assigned elsewhere, deliberately

| Question                                                                            | Owner                                                         |
| ----------------------------------------------------------------------------------- | ------------------------------------------------------------- |
| How an eligibility statement reaches the voting domain without an identity attached | PACK-15 (§11.2 assigns it)                                    |
| Voting credential issuance, ballots, verification, tally                            | PACK-15 / PACK-16                                             |
| Electronic signature                                                                | `FIR-TRUST-001`                                               |
| Mandate and representation                                                          | `FIR-REPRESENT-001`                                           |
| The complete page sequence and screen-state matrix                                  | `FIR-UX-011`, at the `FRONT-PACK Specification + UX/IA` stage |
| Confirmed retention durations                                                       | PACK-09 plus legal review                                     |

## 4. Known limitations of this candidate

1. **The persistence path is a reference path, not a production data
   plane.** It is real: ten SQL migration artefacts, applied in order in
   a transaction by `migration_runner`, creating twenty-nine tables and
   thirty-five indexes — nine of them the unique constraints and ten of
   them the expiry indexes the specification names; eleven durable adapters in `sql_storage`; a
   `UnitOfWork` transaction boundary; and an optimistic-concurrency guard
   that refuses stale writes. It runs on SQLite through the standard
   library, which is why it adds no dependency and why local verification
   can execute it. **No PostgreSQL is deployed, no replication, backup,
   failover or operational durability is provided, and none is claimed.**
   The in-memory adapters in `account_security_storage` remain as
   explicit **test** adapters and are not the default runtime binding —
   `tests/repository/test_pack14_default_binding.py` asserts that
   `runtime.build_identity_service` binds none of them.
2. **No provider of any kind is integrated** — no IAM, no eID, no email,
   no SMS, no HSM or KMS. All four security ports default to adapters
   that **refuse**, so an unconfigured deployment fails at the first
   attempt rather than after an incident.
3. **The service boundary is a runnable reference adapter, not a
   gateway.** `service_api.IdentityServiceApi` parses and validates
   requests, enforces origin and audience, carries session context,
   honours idempotency keys and version fields, returns reason-coded
   responses and asserts that no response body carries a secret or a raw
   identifier. It routes **twelve** of the forty-two catalogued
   operations (`ROUTED_OPERATIONS` and `CONTRACT_ONLY_OPERATIONS` are
   both named in the module so the count cannot be overstated). It is
   transport-agnostic: **there is no HTTP server, no TLS termination, no
   public deployment and no production gateway.**
4. **No frontend was built.** The FRONT-00/FRONT-01 baseline is
   untouched, and `FIR-UX-011` stays future.
5. **External CI has not run.** Local verification could not execute the
   Node-dependent stages; `PACK-14-IMPLEMENTATION-REPORT.md` §7 lists
   exactly what was and was not run and does not claim the rest.
