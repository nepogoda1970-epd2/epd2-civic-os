**Round:** PACK-14 — implementation candidate. **NOT PASS. NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**
**Repository version:** `0.13.0` → `0.14.0` · **Canon version:** unchanged at `0.8.0`

> **Superseding status note, added by the PACK-14 FINAL PASS round
> (2026-07-30).** The header above records the implementation-candidate
> round that wrote this document and is retained unchanged as the
> historical record. External GitHub Actions has since run against this
> exact tree and **passed every stage**, so PACK-14 is now **FINAL PASS**
> at `REPOSITORY_VERSION 0.14.0` / `CANON_VERSION 0.8.0`. The PASS changes
> the _round's_ status and nothing else: no limitation below is closed by
> it, and **NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.** See
> `docs/handover/PACK-14-FINAL-PASS-REPORT.md` and
> `docs/handover/PACK-14-EXTERNAL-CI-VERIFICATION-RESULT.md`.

# PACK-14 — Implementation Candidate Report (handover)

This is the handover companion to
`docs/packs/PACK-14/PACK-14-IMPLEMENTATION-REPORT.md`, which carries the
detail. This document carries the three things a reviewer needs before
opening anything else.

## 1. What to check first

| Claim                                             | Where to verify it                                                                                                                                                          |
| ------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| No global user ID exists                          | `services/identity-service/tests/test_pack14_invariants.py`, 41 parametrized key tests plus the identifier-space test                                                       |
| The canonical status enum is not extended         | `tests/repository/test_pack14_duplicated_logic_parity.py`                                                                                                                   |
| The ten-workspace / ten-origin model is unchanged | Same file, part 2                                                                                                                                                           |
| The voting handoff carries no identity            | `test_a_voting_handoff_artifact_carries_no_identifier_of_any_kind`                                                                                                          |
| No secret can reach an event                      | `test_no_event_type_can_carry_a_secret` (all 59 types)                                                                                                                      |
| No CI gate was weakened                           | `.github/workflows/ci.yml` is unchanged                                                                                                                                     |
| The Master Register was not rolled back           | 141 FIR entries before and after; four named changes                                                                                                                        |
| Persistence is real, not metadata                 | `services/identity-service/migrations/*.sql` (10 artefacts) and `services/identity-service/tests/test_pack14_persistence.py` (22 tests, one against a file-backed database) |
| In-memory stores are not the default binding      | `tests/repository/test_pack14_default_binding.py`                                                                                                                           |
| No password bypasses the breach check             | `test_an_unbound_breach_checker_refuses_password_enrollment` and the five tests beside it                                                                                   |
| The service boundary runs                         | `services/identity-service/tests/test_pack14_service_api.py`, `test_the_account_lifecycle_runs_end_to_end_through_the_adapter`                                              |
| Only 12 of the 42 operations are routed           | `service_api.ROUTED_OPERATIONS` and `CONTRACT_ONLY_OPERATIONS`, both named constants, both asserted against the catalogue                                                   |

## 2. What this round does not claim

No external GitHub Actions run has verified it. The Node-dependent CI
stages could not run in the authoring sandbox and are **not** claimed as
passing — `PACK-14-IMPLEMENTATION-REPORT.md` §7.1 lists them
individually.

No production IAM, no real eID, no real email or SMS delivery, no
production HSM or KMS, no complete Voting Client, and no full legal
electronic signature. **All four** security ports are unbound and all
four **refuse**.

No production database. The persistence path is real and testable — ten
applied SQL migration artefacts, 29 tables, 35 indexes, eleven durable
adapters, a transaction boundary and an optimistic-concurrency guard —
and it is a **reference** path on SQLite through the standard library.
No replication, backup, failover or operational durability is provided or
claimed.

No HTTP surface and no production gateway. The service boundary is a
runnable, transport-agnostic reference adapter for **12** of the 42
catalogued operations.

## 2.1 The correction round

This archive supersedes
`EPD2_PACK-14_IDENTITY_AUTHENTICATION_ACCOUNT_SECURITY_0.14.0_CANDIDATE.zip`,
which was reviewed before external CI. Three findings were returned and
fixed: persistence that was metadata rather than persistence, a
breached-password default that reported nothing as breached, and an
`api.py` that was an endpoint catalogue rather than a boundary.
`PACK-14-IMPLEMENTATION-REPORT.md` §12 records all three in full,
including what the correction deliberately did **not** do — no scope
expansion, no frontend, no new dependency, no weakened CI gate, no
deleted test, and no version change.

## 3. Predecessor documents, retained unchanged

`docs/handover/PACK-14-SPEC-ADR-REPORT.md` and the twenty-two
specification documents keep their own round headers. They are the record
of the specification round and are deliberately not rewritten to read as
though they had always been an implementation — the discipline the
PACK-13 FINAL PASS round applied to its own candidate report.

## 4. SHA-256 — every file the correction round added or changed

Recalculated against the delivered tree. The comparison baseline is the
superseded archive
`EPD2_PACK-14_IDENTITY_AUTHENTICATION_ACCOUNT_SECURITY_0.14.0_CANDIDATE.zip`;
**no file was removed** by the correction round, and the 1035-file
inventory of that archive is otherwise unchanged, so every file not
listed below carries the digest it carried there.

### 4.1 Added (18 files)

| Path                                                                      | SHA-256                                                            |
| ------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| `services/identity-service/migrations/0001_account_registry.sql`          | `2c4257e8bcd316cd4329e1426b367391c1de5018c8e46851e3641e369b6e9580` |
| `services/identity-service/migrations/0002_account_contacts.sql`          | `b9a03965c73fd490b069f0a004fa4a6de090ec823d0612fad4ec02f51f3f17f6` |
| `services/identity-service/migrations/0003_credential_registry.sql`       | `80c798fd9641a9944cc0351bc3ae553da610441efc8e86da909e72652561c006` |
| `services/identity-service/migrations/0004_sessions.sql`                  | `eb0a5b6e01a2fc68b6cbbdc5a1bfdce2da600c269d730abe5f57d1d122a10c88` |
| `services/identity-service/migrations/0005_step_up.sql`                   | `de1134206834579143a421765ba3c18ea1f61d39434e4ee40a6af360ce7697fd` |
| `services/identity-service/migrations/0006_recovery.sql`                  | `c6e74f50e173b55d9060e1de80385e69c6db690501aeebd1d2ae56511a614195` |
| `services/identity-service/migrations/0007_proofing.sql`                  | `4c7215060fee4feb9fd32f24cfdd7ea7ac42f1da55091122fa52a0f0c194f70c` |
| `services/identity-service/migrations/0008_bootstrap_and_handoff.sql`     | `a6806016e686b50da1413dbf0ccd0cc671f0ea58e34e075ddce192527f077012` |
| `services/identity-service/migrations/0009_identity_mappings.sql`         | `6937806b6909b3cd96dfc7a731678a5c77be653d589f6c0a015350b8d33a5630` |
| `services/identity-service/migrations/0010_replay_prevention.sql`         | `f7478f02cd6f001aa3ac6fae237859af570caca282ab8385bc6a3d1f3fba3f57` |
| `services/identity-service/src/epd2_identity_service/codecs.py`           | `3fe9edd8047882ef8b723e083389bdad0e939b0beacafca5bf67a1c03d55512c` |
| `services/identity-service/src/epd2_identity_service/migration_runner.py` | `7e2546918237993deb4b65941a19d68038f741535eca083f00d9b638c6cbab52` |
| `services/identity-service/src/epd2_identity_service/runtime.py`          | `2f50e1b4600f5bfd402d25c4f23111f8f9fc6953410f5a124c643998b73ff1fb` |
| `services/identity-service/src/epd2_identity_service/service_api.py`      | `2938b13a506a21823aef7576987fd8ab23b3cf7241d00c79f440f8060beec0ef` |
| `services/identity-service/src/epd2_identity_service/sql_storage.py`      | `5644e0ac37283e43cc3bd5883090694325b53608f91c60b549a8cb5af008f878` |
| `services/identity-service/tests/test_pack14_persistence.py`              | `a06c743479a779982fc57c68b6cbd849c86d98129d5a64cbc5861b9361916334` |
| `services/identity-service/tests/test_pack14_service_api.py`              | `d1c4fda8fe885c3d7d304c55aa5a7849d66834f3f1ca3ce217b720003f8e6240` |
| `tests/repository/test_pack14_default_binding.py`                         | `56e51898d6b414b5b59ec16805cd7e8e3b558869492f584d88c2d5d580c0488a` |

### 4.2 Changed (26 files)

| Path                                                                                  | SHA-256                                                                                          |
| ------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| `CHANGELOG.md`                                                                        | `79218dcbade0044ce834182d3df1dadc9a99ba10e26efce9015c4c21dccd8015`                               |
| `contracts/reason-codes/pack-14.yml`                                                  | `8b67a912f9de0bdb612a33a1645cf318b3ba3af6b249214c7effd03b6fff2e33`                               |
| `docs/handover/PACK-14-IMPLEMENTATION-CANDIDATE-REPORT.md`                            | _self-referential — a file cannot contain its own digest; compute it from the delivered archive_ |
| `docs/packs/PACK-14/PACK-14-API-CATALOG.md`                                           | `e81fbe831c9f0dd5b17db75e1dbd695ec54bada792586bf6904ef7df3c3051a6`                               |
| `docs/packs/PACK-14/PACK-14-DATA-MODEL.md`                                            | `373804ded749aa12ebbea8db6ef8ef5a9d6a6e64d5944b18ec1f411676435102`                               |
| `docs/packs/PACK-14/PACK-14-DEPENDENCY-REPORT.md`                                     | `ae5c9f3012b7059acecc3ad8f9bf7a832b65e1026bbe418d6e83dd9c07f10d46`                               |
| `docs/packs/PACK-14/PACK-14-IMPLEMENTATION-MATRIX.md`                                 | `f09fc5963604d2db0a0c2feefcb391b1831615d3175faa95d40769517aabca07`                               |
| `docs/packs/PACK-14/PACK-14-IMPLEMENTATION-REPORT.md`                                 | `d62a7f544dade0bd1dc40e3329f3087d767abe6560a4633c6a35871bbf24f3be`                               |
| `docs/packs/PACK-14/PACK-14-MIGRATION-REPORT.md`                                      | `5108102db0bdad0af0d3698c1d42408176575f63ec7c37c3308c25d5473ba6f5`                               |
| `docs/packs/PACK-14/PACK-14-OPEN-ITEMS.md`                                            | `7240cf6991a746d6396173982139be257b96ff563e747497aa510c7820d741c5`                               |
| `docs/packs/PACK-14/PACK-14-PRIVACY-VERIFICATION.md`                                  | `b421309b18aa622b41d27d3e6df4938f648070fb507aba570679013400b0d86c`                               |
| `docs/packs/PACK-14/PACK-14-REASON-CODE-CATALOG.md`                                   | `05d3863783addbcb942bb374d911f028fc8dd9ec043f4b301d3b37eb66e980f4`                               |
| `docs/packs/PACK-14/PACK-14-SECURITY-VERIFICATION.md`                                 | `f21357b9f9ea6c26d88cac8465acb902dd117a21d2b6a27a1b21c6456ad6188a`                               |
| `docs/packs/PACK-14/PACK-14-TEST-MATRIX.md`                                           | `ba821e001e3c6dc98bc2d2c6d314ded0cf4cd27a469ae2abbc2fdd5a9ea7d348`                               |
| `docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md`                          | `89704a86824100a4189722dd0fb4b42e4c8bb3b3b9a3265c08afb67656096965`                               |
| `scripts/check_repository.py`                                                         | `fa9cc403584557f30c50a8c65b887137cdb3fa4fdc11d70f29594b55ba4d8a56`                               |
| `services/identity-service/README.md`                                                 | `4d61fc192a81f43ea9f2db361bc110c3c698974cba2795095c2180b3793415f7`                               |
| `services/identity-service/src/epd2_identity_service/__init__.py`                     | `066d7373f3df7ba10819f376551cd97331362f2696c943dd11dfd14aa5d9dd47`                               |
| `services/identity-service/src/epd2_identity_service/account_security_application.py` | `3f1ae834b2292212f82235ef674dcd6aa639017a2d9c6258f14dbebb88500bb1`                               |
| `services/identity-service/src/epd2_identity_service/exceptions.py`                   | `8ed8bbb53f73467227cb6dae4e5d284076f0d13288f2484661e73d97caae9562`                               |
| `services/identity-service/src/epd2_identity_service/persistence.py`                  | `4648524e6b2ca25d7243aeba6a6508c8edcd86987cf3931afdb207bc17a5e382`                               |
| `services/identity-service/src/epd2_identity_service/secret_storage.py`               | `74a4359f84bb0ccf3d6068197a5c9de3d7e3b232b46085a5b852ac0a60d83d29`                               |
| `services/identity-service/tests/test_pack14_integration.py`                          | `efcf9d4e8de528884413566c1a7582727c2741d2a9d656b9319e424aa5a8a941`                               |
| `services/identity-service/tests/test_pack14_security.py`                             | `cc77ad2b0d4fd038b73800155afc5ccd78920eac549a2095c0505cfd8ccad4e4`                               |
| `tests/contract/test_reason_codes_registry.py`                                        | `e882702a827464c5b9283b9c18ea8ec3363e910d182f246268287ec73a2e98ef`                               |
| `tests/repository/test_pack14_duplicated_logic_parity.py`                             | `a4f2368de1f3d66828e9008e46929e85e766abd3a4d9024f096900e882f6dd33`                               |

### 4.3 Prettier formatting fix, after the first external CI run

The external pipeline failed at `make format-check` on one file:
`contracts/reason-codes/pack-14.yml` was not Prettier-formatted. It was
reformatted with `prettier --write` and nothing else. The change is
**whitespace only** — 215 blank lines between entries removed, no code,
meaning, description, severity, owner, ordering or count altered; the
registry still parses to the same 213 entries in the same order, and
`tests/contract/test_reason_codes_registry.py` passes unchanged. The
digest above is the reformatted file's. **No version, architecture, test,
CI configuration, Master Register entry or PACK-14 behaviour changed, and
this remains the same candidate — not a new one and not a PASS.**

## 5. Status

```text
PACK-14 IMPLEMENTATION CANDIDATE COMPLETE
REPOSITORY_VERSION 0.14.0
CANON_VERSION 0.8.0
LOCAL VERIFICATION COMPLETE
EXTERNAL CI NOT YET VERIFIED
NOT FINAL PASS
NOT PRODUCTION READY
NOT LEGALLY ACTIVATED
```
