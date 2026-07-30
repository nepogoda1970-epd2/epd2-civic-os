**Round:** PACK-14 — implementation candidate. **NOT PASS. NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**
**Repository version:** `0.14.0` · **Canon version:** unchanged at `0.8.0`
**External GitHub Actions has not run against this round.**

# PACK-14 — Migration Report

## 1. What this round migrates

**A reference schema, really applied — and no production database.**

The two halves of that sentence both matter, so neither is left implied.

**What is real.** `services/identity-service/migrations/` holds ten
**actual SQL artefacts**, not descriptions of SQL.
`epd2_identity_service.migration_runner` applies them: in declared order,
each inside a single `BEGIN IMMEDIATE` transaction, each statement split
with `sqlite3.complete_statement` because `executescript` would issue an
implicit commit and destroy the atomicity the discipline depends on. Each
application is recorded in a `schema_migration` table with a SHA-256
checksum of the artefact, `apply_migrations` is idempotent, and
`verify_migrations` refuses to run against a database whose recorded
history disagrees with the files on disk — an applied migration edited in
place is a `MigrationChecksumMismatchError`, not a surprise at runtime.
Applying all ten produces **29 tables and 35 indexes**, of which 9 are the
unique constraints and 10 the expiry indexes sections 3 and 4 name.
`services/identity-service/tests/test_pack14_persistence.py` executes
this path, and it is the same path `runtime.build_identity_service`
opens.

**What is not real.** No PostgreSQL is deployed. The reference path runs
on **SQLite through the Python standard library**, which is why it adds
no dependency to `uv.lock` and why local verification can execute it end
to end. Replication, backup, failover, connection pooling, online
schema-change tooling and the five automated gates PACK-13's production
data plane runs are **not** provided here and are not claimed. Production
durability is a PACK-13 deployment concern; this is the domain-side
artefact set that a production migration would be authored from.

**On not importing PACK-13's framework.**
`tests/repository/test_service_boundaries.py` forbids an
`identity-service` → `data-plane-service` import outright, and
`epd2_core`'s charter forbids it holding business rules. So ADR-075's
discipline is reimplemented in-service rather than imported — exactly as
canon 7.2's status enum is — and kept honest the same way, by
`tests/repository/test_pack14_duplicated_logic_parity.py` §3, which
asserts that this service's migration-kind vocabulary is a strict subset
of `epd2_data_plane_service.migrations.MigrationClass`, classified
identically, and that every declared step has an artefact on disk.
**Ownership of the migration model is unchanged: it stays with
`data-plane-service`.**

## 2. The definitions and their artefacts

Ten steps, declared in
`epd2_identity_service.persistence.PACK14_MIGRATIONS` and paired
one-to-one with the files in `services/identity-service/migrations/`.
`load_artefacts` refuses both a declaration with no file and a file with
no declaration, so the list below cannot drift from the directory.

| #   | Identifier                      | Kind   | Reversible | Summary                                                     |
| --- | ------------------------------- | ------ | ---------- | ----------------------------------------------------------- |
| 1   | `p14-001-account-registry`      | expand | yes        | Account records, locks, restrictions, closure requests      |
| 2   | `p14-002-account-contacts`      | expand | yes        | Contacts holding digests and masked values only             |
| 3   | `p14-003-credential-registry`   | expand | yes        | Credentials, passkeys, MFA factors, recovery code sets      |
| 4   | `p14-004-sessions`              | expand | yes        | Sessions, refresh-token families, device references         |
| 5   | `p14-005-step-up`               | expand | yes        | Step-up challenges and results                              |
| 6   | `p14-006-recovery`              | expand | yes        | Recovery cases, assessments, evidence, decisions, disputes  |
| 7   | `p14-007-proofing`              | expand | yes        | Proofing cases and PACK-11 evidence references              |
| 8   | `p14-008-bootstrap-and-handoff` | expand | yes        | Bootstrap requests/responses/redemptions, handoff issuances |
| 9   | `p14-009-identity-mappings`     | expand | yes        | Governed identity mappings                                  |
| 10  | `p14-010-replay-prevention`     | expand | yes        | Nonce and idempotency records with expiry indexes           |

**Every step is `expand`.** This round adds tables and indexes and drops
nothing, so the contract phase is empty and every step is honestly
reversible. That is the state of a first implementation round, not a
deferral of the contract phase.

## 3. Constraints that are correctness, not performance

Declared in `PACK14_UNIQUE_CONSTRAINTS` and **created by the artefacts**:
nine unique indexes exist in the applied schema. Each states its
rationale in the code, and each is a rule the domain enforces that a
concurrent writer would otherwise be able to break — contact uniqueness
within a scope, one record per authenticator credential reference, one
open closure request per account, one open recovery case per account, one
active factor per MFA class, and the digest uniqueness the three
single-use artifacts depend on.

Two of them are **partial** indexes, because the rule they encode is
conditional: `uq_open_closure_request` applies
`WHERE state IN ('requested','cooling_off')`, so a settled request does
not block a later one, and `uq_contact_scope_digest` applies
`WHERE status NOT IN ('removed','replaced')`, so a removed contact does
not permanently reserve an address. A test asserts the database itself
refuses the duplicate, not merely that the domain does.

## 4. Indexes that are a privacy control

Declared in `PACK14_EXPIRY_INDEXES`; ten expiry indexes exist in the
applied schema. The one worth naming is
`ix_voting_handoff_expires_at`: the retention matrix requires handoff
issuance records to be deleted early **and as a set**, and without an
index that disposal is a table scan somebody eventually stops running.

## 5. One thing the schema deliberately does not have

`voting_handoff_issuance` has **no account column of any kind**, and
`0008_bootstrap_and_handoff.sql` says so in a comment next to the table:
a later migration adding one would reverse ADR-088, which is the decision
that a voting handoff carries no reversible link to an account. A schema
is where that decision is either kept or quietly lost, so it is recorded
where the next person to write a migration will read it.

For the same reason `credential.factor_class` carries
`CHECK (factor_class IN ('totp','security_key','recovery_code','email_otp','provider_mfa'))`
— `sms_otp` is deliberately absent, because SMS OTP carries no assurance
level at all in this system and therefore has no `MfaFactorClass` member
to store.

## 6. What a deployment still has to do

1. Author the production migrations from these artefacts, under PACK-13's
   migration framework and its five automated gates, and bind a
   production data-plane adapter. The reference adapters in `sql_storage`
   are the shape that has to be met, not the deployment.
2. Bind a durable audit store. `runtime.build_identity_service` binds
   `InMemoryAuditEventStore` and records why: `audit-core` owns durable
   audit persistence and PACK-14 does not get to bind it on that
   service's behalf.
3. Confirm the retention durations (`OD-P14-07`) before any disposal job
   is enabled — `assert_disposition_permitted` refuses destruction while
   the schedule is unconfirmed, so an early deployment is safe by
   refusal rather than by hope.
