**Round:** PACK-14 — implementation candidate. **NOT PASS. NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**
**Repository version:** `0.14.0` · **Canon version:** unchanged at `0.8.0`
**External GitHub Actions has not run against this round.**

# PACK-14 — Implementation Matrix

What the task asked for, what exists, and — where the answer is "part of
it" — exactly which part.

## 1. Bounded contexts (task §4)

| Context                      | Module                                        | Storage boundary                                                         | State                    |
| ---------------------------- | --------------------------------------------- | ------------------------------------------------------------------------ | ------------------------ |
| Account Registry             | `accounts`                                    | `AccountRegistryStore` (accounts, locks, restrictions, closure requests) | reference implementation |
| Credential Registry          | `credentials`, `passkeys`, `passwords`, `mfa` | `CredentialStore`                                                        | reference implementation |
| Authentication               | `authentication`, `assurance`                 | `AuthenticationStore`                                                    | reference implementation |
| Session Security             | `sessions`, `stepup`                          | `SessionStore`                                                           | reference implementation |
| Recovery coordination        | `recovery`                                    | `RecoveryStore`                                                          | reference implementation |
| Identity-proofing references | `proofing`                                    | `IdentityProofingStore`; evidence stays in PACK-11                       | reference implementation |

**No parallel authentication service was created.** `identity-service`
owns all six, as internally separated modules with separate storage
boundaries (specification §4.1, closing OD-P14-02).

## 2. Identity separation (task §5)

| Requirement                     | Where                                                                | State |
| ------------------------------- | -------------------------------------------------------------------- | ----- |
| `AccountId` distinct type       | `identifiers.AccountId` (`NewType`)                                  | done  |
| `PersonRecordId` protected      | `identifiers.PersonRecordId`; optional on a proofing case            | done  |
| `MembershipReference` scoped    | `identifiers.MembershipReference`, opaque string                     | done  |
| `CommunicationPersonaReference` | `identifiers.CommunicationPersonaReference`                          | done  |
| Scoped actor reference          | `identifiers.ScopedIdentityReference` + `derive_scoped_reference`    | done  |
| `IdentityMapping` aggregate     | `mappings` — purpose, scope, owner, policy, retention, audit, expiry | done  |
| No unrestricted lookup          | `mappings.refuse_unrestricted_lookup`; no `list_all` on any port     | done  |

## 3. Account lifecycle (task §6)

Every named operation exists: create, activate, restrict, remove
restriction, lock, unlock, request closure, cancel closure, close, begin
anonymization, complete anonymization, attach/remove/replace contact.
Idempotency is per operation and per request digest; stale-version
protection is `AccountRegistryRecord.assert_version`.

**The canonical enum is not extended.** `AccountLock`,
`AccountRestriction` (security class), `AccountClosureRequest` state and
lifecycle outcomes carry what would otherwise have been three new status
values.

## 4. Credentials, passkeys, password fallback, MFA (task §§8–11)

| Requirement                                 | State                                                                    |
| ------------------------------------------- | ------------------------------------------------------------------------ |
| Credential registry with all seven types    | done                                                                     |
| WebAuthn registration/assertion ceremonies  | done as a **boundary**; verification is a port                           |
| **WebAuthn cryptography**                   | **not implemented, by instruction**; `UnboundWebAuthnVerifier` refuses   |
| Sign-counter replay metadata                | done, and `None` where the authenticator reports none                    |
| Synced vs device-bound classification       | done; synced caps at `substantial`                                       |
| Password fallback, fenced by seven rules    | done                                                                     |
| **Password hashing algorithm**              | **not implemented, by instruction**; `UnavailablePasswordHasher` refuses |
| Breached-password boundary                  | defined; **no corpus ships**, and the unbound checker reports nothing    |
| TOTP enrollment/confirmation/use/revocation | done through a port; the bound test double is named as one               |
| Recovery code sets, single-use              | done                                                                     |
| **SMS OTP as a factor**                     | **deliberately absent**; `refuse_sms_otp_as_factor` always raises        |

## 5. Assurance, step-up, sessions, bootstrap, handoff (task §§12–16)

All models exist under the accepted specification's names rather than the
task's informal `AAL0…AAL3`, because §12 permits "the exact names from the
accepted specification" and the specification reuses canon's four values.

| Requirement                                               | State                                                    |
| --------------------------------------------------------- | -------------------------------------------------------- |
| Governed timeout defaults                                 | done, in `configuration`, with the four constraint rules |
| Step-up bound to actor/session/action/resource/version    | done                                                     |
| Object-version change voids a step-up                     | done (`STEP_UP_OBJECT_CHANGED`)                          |
| Session issue/rotate/refresh/expire/revoke one/revoke all | done                                                     |
| Refresh-token rotation with replay detection              | done                                                     |
| No session ID in a URL                                    | done (`refuse_session_identifier_in_url`)                |
| Secure cookie attributes, no parent domain                | done, unconstructible otherwise                          |
| Cross-origin bootstrap, single-use, audience-bound        | done                                                     |
| PKCE-equivalent proof                                     | done; the `plain` method is refused                      |
| `VotingHandoffArtifact` with nine properties              | done; the issuance record has no account field           |
| **Voting Client**                                         | **not implemented, by exclusion**                        |

## 6. Recovery, proofing, providers, linking, administration (§§17–21)

| Requirement                                    | State                                               |
| ---------------------------------------------- | --------------------------------------------------- |
| Ten-state recovery workflow                    | done                                                |
| Dual control, cooling-off, out-of-band         | done, all three required together                   |
| Revocation **before** completion               | enforced, not documented                            |
| Resulting-confidence rule with risk acceptance | done                                                |
| Proofing case lifecycle and eight methods      | done                                                |
| **Production eID**                             | **not implemented, by exclusion**                   |
| Provider adapter with eight checks             | done; **no provider selected**                      |
| Linking with proof of both sides and step-up   | done; four merges refused with their own call sites |
| PACK-12 roles and separations                  | done as a boundary; the grant is a value object     |
| **A second privileged mechanism**              | **not created**                                     |

## 7. Events, reason codes, persistence, API (§§22–25)

| Requirement               | Count / state                                                                                                         |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| Versioned events          | 59 types, 9 families, PACK-13 envelope unchanged                                                                      |
| Reason codes              | 213 registered (131 additive, 22 redeclared, 60 `*_RECORDED`)                                                         |
| Migrations                | 10 expand-only steps, **10 SQL artefacts on disk**, applied in order in a transaction with a recorded checksum        |
| Schema they create        | 29 tables, 35 indexes                                                                                                 |
| Unique constraints        | 9 unique indexes (2 partial), each with its correctness rationale                                                     |
| Expiry indexes            | 10, each a privacy control                                                                                            |
| Durable adapters          | 11, in `sql_storage`, bound by `runtime.build_identity_service`                                                       |
| Transaction boundary      | `UnitOfWork`; a failed operation leaves no partial state                                                              |
| Optimistic concurrency    | monotonic `WHERE version < ?` guard; a stale write is refused                                                         |
| Replay-prevention records | nonce, idempotency and assertion-id records, **durable**, with expiry indexes; they survive a restart                 |
| Secret storage            | ports; digests at rest; `codecs.encode_value` refuses `bytes`; no secret in any record class                          |
| API contracts             | 42 operations catalogued                                                                                              |
| Runnable API boundary     | `service_api.IdentityServiceApi` routes **12** of them; transport-agnostic, no HTTP surface                           |
| In-memory adapters        | retained as **test** adapters; not the runtime binding, asserted by `tests/repository/test_pack14_default_binding.py` |

**On "reference implementation" in §1.** Each of the six contexts now has
a durable adapter behind its storage port, not only a port. What remains
excluded is a **production data plane**: the reference path is SQLite
through the standard library, and no PostgreSQL, replication, backup or
failover is deployed or claimed.

## 8. Frontend (task §27)

**No frontend change was made this round.** Task §27 permits a
backend/API-first candidate with a test harness where UI is not required
for acceptance, and §22.1 of the accepted specification defers the page
sequence to the `FRONT-PACK Specification + UX/IA` stage. The FRONT-00 /
FRONT-01 baseline is untouched: no page was removed, no public-site
structure changed, and no new design language was created. `FIR-UX-011`
stays **future**.
