**Round:** PACK-14 — implementation candidate. **NOT PASS. NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**
**Repository version:** `0.14.0` · **Canon version:** unchanged at `0.8.0`
**External GitHub Actions has not run against this round.**

# PACK-14 — Data Model

Every entity, where it lives, and — for the three that people expect to
find and will not — where the fact went instead.

## 1. Account context (`accounts`)

| Entity                  | Notes                                                                                        |
| ----------------------- | -------------------------------------------------------------------------------------------- |
| `AccountRegistryStatus` | Canon 7.2's six values, verbatim. Not extended                                               |
| `AccountRegistryRecord` | Status, scope, created/activated, anonymization state, optimistic `version`                  |
| `AccountLock`           | Cause, reason code, `locked_at`, **mandatory** `expires_at`, unlock condition                |
| `AccountRestriction`    | Class (incl. `security_quarantine`), **mandatory** authority, reason code, scope, review due |
| `AccountClosureRequest` | Its own four-state lifecycle; the account stays `active` while it is open                    |
| `AnonymizationState`    | An outcome an account reaches, not a status it is reported as being in                       |

**Three things you will not find**, and where they went instead:
`locked` → `AccountLock`; `closure_pending` → `AccountClosureRequest`
state; `deleted_or_anonymized` → `AnonymizationState` plus the
`account.closed` and `account.anonymization_completed` events.

## 2. Contacts (`contacts`)

`AccountContact` holds a **hashed** normalized value, a masked display
form, a status, a scoped uniqueness key, timestamps and a retention
class. There is no field that can hold the raw address.

## 3. Credentials (`credentials`, `passkeys`, `passwords`, `mfa`)

| Entity                        | Notes                                                                                          |
| ----------------------------- | ---------------------------------------------------------------------------------------------- |
| `Credential`                  | Type, status, metadata, timestamps, revocation, `version`                                      |
| `CredentialMetadata`          | Nickname, binding, attestation state, backup eligible/state, authenticator class, sign counter |
| `CredentialRevocation`        | Immutable; reason code and **actor class**, not an actor ID                                    |
| `PasskeyCredentialRecord`     | Credential reference, **public** key, counter, binding, origin                                 |
| `PasswordCredentialReference` | Opaque stored hash and its algorithm label. No password field                                  |
| `MfaFactor`                   | Class, status, opaque secret **reference**, lifecycle timestamps                               |
| `RecoveryCodeSet`             | Digests plus a consumed set. The plaintext exists once, in a return value                      |

## 4. Authentication and assurance

`AuthenticationAttempt`, `AuthenticationChallenge`,
`AuthenticationOutcome` (internal **and** public reason code),
`RiskSignal`, `RiskAssessment`, `RateLimitBucket`,
`AuthenticationThrottleState`; `AuthenticationAssurance`,
`AssuranceEvidence`, `AssuranceRequirement`.

## 5. Sessions and step-up

`SessionRecord` (**service-level**, not canon), `SessionScope`,
`SessionRevocation`, `RefreshTokenFamily`, `DeviceReference`,
`SessionCookieAttributes`; `StepUpChallenge`, `StepUpResult`,
`StepUpBinding`, `StepUpFreshness`.

## 6. Bootstrap and voting handoff

`AuthenticationBootstrapRequest`, `AuthenticationBootstrapResponse`,
`BootstrapRedemption`; `VotingHandoffRequest`, `VotingHandoffArtifact`,
`VotingHandoffIssuance`, `VotingHandoffRedemptionReference`.

**`VotingHandoffIssuance` has seven fields and none of them identifies a
person.** That is the whole of ADR-088's non-reversibility property,
expressed as a field set rather than as a policy.

## 7. Recovery and proofing

`RecoveryRequest` with its ten states, `RecoveryAssessment`,
`RecoveryEvidenceReference`, `RecoveryDecision`, `RecoveryRiskAcceptance`,
`RecoveryDispute`; `IdentityProofingCase`, `IdentityEvidenceReference`,
`IdentityAssertion`, `IdentityProofingDecision`.

## 8. Mapping boundary and providers

`ScopedIdentityReference`, `IdentityMapping`, `MappingPurpose`,
`MappingAccessPolicy`, `MappingStatus`, `MappingResolutionRequest`;
`ExternalIdentityProvider`, `ExternalIdentityAssertion`,
`AssertionValidationResult`, `ProviderSubjectReference`.

## 9. Sensitive-column minimization

| Would-be column           | What is stored instead                                 |
| ------------------------- | ------------------------------------------------------ |
| email / phone             | SHA-256 digest + masked display form                   |
| password                  | opaque hash from the bound hasher                      |
| TOTP seed                 | an opaque reference into the deployment's secret store |
| recovery code             | SHA-256 digest, plus a consumed-digest set             |
| WebAuthn private key      | nothing — it never leaves the authenticator            |
| refresh / CSRF token      | SHA-256 digest                                         |
| bootstrap / handoff value | SHA-256 digest                                         |
| provider subject claim    | SHA-256 digest salted with the issuer                  |

## 10. Where these entities are actually stored

The model above is not only a set of dataclasses. Ten SQL artefacts in
`services/identity-service/migrations/` create **29 tables** and **35
indexes** for it, applied in order and in a transaction by
`epd2_identity_service.migration_runner`, and eleven adapters in
`epd2_identity_service.sql_storage` read and write them. The mapping is
one aggregate family per migration:

| Migration                        | Tables it creates                                                    |
| -------------------------------- | -------------------------------------------------------------------- |
| `0001_account_registry.sql`      | Accounts, locks, restrictions, closure requests, anonymization state |
| `0002_account_contacts.sql`      | Contacts, holding digests and masked forms only                      |
| `0003_credential_registry.sql`   | Credentials, passkey metadata, MFA factors, recovery-code sets       |
| `0004_sessions.sql`              | Sessions, refresh families, device references                        |
| `0005_step_up.sql`               | Step-up challenges and results                                       |
| `0006_recovery.sql`              | Recovery cases, assessments, evidence refs, decisions, disputes      |
| `0007_proofing.sql`              | Proofing cases, evidence references, assertions, decisions           |
| `0008_bootstrap_and_handoff.sql` | Bootstrap requests/responses/redemptions, handoff issuances          |
| `0009_identity_mappings.sql`     | Governed identity mappings and access policy                         |
| `0010_replay_prevention.sql`     | Nonce, idempotency and assertion-id records with expiry indexes      |

**The schema keeps the decisions §1 and §6 describe, rather than
restating them.**

- `voting_handoff_issuance` has **no account column of any kind**, and
  `0008` carries a comment saying that a migration adding one would
  reverse ADR-088. §6's "seven fields and none of them identifies a
  person" is enforced by the absence of a column, not by a convention.
- `credential.factor_class` carries
  `CHECK (factor_class IN ('totp','security_key','recovery_code','email_otp','provider_mfa'))`.
  `sms_otp` is absent because it has no `MfaFactorClass` member to store.
- `uq_open_closure_request` is a **partial** unique index
  (`WHERE state IN ('requested','cooling_off')`), which is §1's "the
  account stays `active` while it is open" made unbreakable by a
  concurrent writer.
- `uq_contact_scope_digest` is partial on
  `WHERE status NOT IN ('removed','replaced')`, so a removed contact does
  not permanently reserve an address.
- Every versioned table is written through a **monotonic** guard
  (`WHERE version < ?`), so a stale write is refused rather than merged.
- §9's minimization is checked, not asserted: a persistence test sweeps
  **every row of every table** for a raw contact value or a secret and
  fails if it finds one, and `codecs.encode_value` refuses `bytes`
  outright — the one Python type a raw key or salt would arrive as.

`services/identity-service/tests/test_pack14_persistence.py` runs this
path against a **file-backed** database and asserts that the state, the
session deadlines, and the bootstrap and voting-handoff replay protection
all survive recreating the application.

**This is a reference persistence path, not a production data plane.** It
runs on SQLite through the standard library. No PostgreSQL is deployed,
and no replication, backup, failover or operational durability is
provided or claimed.
