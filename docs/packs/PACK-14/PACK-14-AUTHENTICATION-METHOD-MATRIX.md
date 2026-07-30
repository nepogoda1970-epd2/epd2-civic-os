# PACK-14 — Authentication Method Matrix

**Round:** PACK-14 — specification and ADR only. **No code. Not implemented. Not a candidate. Not a PASS.**
**Repository version:** unchanged at `0.13.0` · **Canon version:** unchanged at `0.8.0`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**
**Architecture correction applied (2026-07-30).**

No production provider, vendor or platform is selected by this round. The
assurance column uses canon 19d.8's four-value scale.

## 1. Methods

| Method                         | Assurance class           | Phishing resistant | Replay resistant   | Device bound      | Step-up eligible | Allowed actions                                                                                                   |
| ------------------------------ | ------------------------- | ------------------ | ------------------ | ----------------- | ---------------- | ----------------------------------------------------------------------------------------------------------------- |
| Passkey, device-bound          | `high`                    | yes                | yes                | yes               | yes              | All, subject to per-action policy                                                                                 |
| Passkey, synced                | `substantial` (cap)       | yes                | yes                | no — cloud-synced | yes              | All except actions requiring `high`                                                                               |
| Hardware security key          | `high`                    | yes                | yes                | yes               | yes              | All, subject to per-action policy                                                                                 |
| Password + MFA                 | `substantial` (cap)       | no                 | partial            | no                | yes              | Ordinary member actions; never a `high` action                                                                    |
| Password alone                 | **not permitted**         | no                 | no                 | no                | no               | **None.** Password login always requires MFA                                                                      |
| Magic link (email)             | `low`                     | no                 | no                 | no                | no               | Bootstrap and low-risk only                                                                                       |
| Email OTP                      | `low`                     | no                 | partial            | no                | no               | Verification of the email channel itself                                                                          |
| **SMS OTP**                    | **none — carries no AAL** | no                 | partial            | no                | **no**           | **Not a login method and not a step-up factor.** Phone-channel verification and a low-weight recovery signal only |
| Recovery code                  | `substantial`             | partial            | yes — single use   | no                | no               | Recovery entry only                                                                                               |
| Verified-device assisted login | `substantial`             | partial            | yes                | yes               | yes              | Per policy                                                                                                        |
| Federated identity provider    | provider-dependent        | provider-dependent | provider-dependent | no                | conditional      | Per adapter assessment; never above its own assurance                                                             |
| eID-mediated login             | `high` (expected)         | yes                | yes                | scheme-dependent  | yes              | Per adapter assessment                                                                                            |
| In-person assisted recovery    | `substantial`–`high`      | n/a                | n/a                | n/a               | n/a              | Recovery only, with dual control                                                                                  |

### 1.1 Decisions this table now carries

- **Password fallback exists and is controlled** (OD-P14-03). Passkeys stay
  preferred; no new password-only account may be created; password login
  always requires MFA and never authorizes a consequential action alone; it
  can be disabled through governed configuration, globally, per
  organizational scope or per account; security questions remain
  prohibited. Its ceiling is `substantial`.
- **A synced passkey caps at `substantial`** (OD-P14-08). `high` requires a
  device-bound credential or a separately approved equivalent. Attestation
  is not universal, is required only for specifically governed privileged
  action classes, and **no ordinary member is excluded for lack of it**.
- **SMS OTP carries no assurance level at all** (OD-P14-09). Every mapping
  that previously assigned it one has been removed. It verifies a phone
  channel and contributes a low-weight recovery signal; it is neither a
  login method nor a step-up factor, and the system operates with no SMS
  provider.

## 2. Recovery impact, fallback, revocation and evidence

| Method                 | Loss impact                                                  | Fallback                           | Revocation                     | Audit evidence recorded                     |
| ---------------------- | ------------------------------------------------------------ | ---------------------------------- | ------------------------------ | ------------------------------------------- |
| Passkey, device-bound  | Device loss locks that credential                            | Second passkey; recovery workflow  | Per credential; immediate      | Method class, credential reference, outcome |
| Passkey, synced        | Cloud account compromise compromises it                      | Second passkey; recovery workflow  | Per credential; immediate      | Same, plus synced flag                      |
| Hardware key           | Physical loss                                                | Second key; recovery workflow      | Per credential                 | Same                                        |
| Password + MFA         | Either factor lost blocks login                              | Recovery codes; recovery workflow  | Password reset; factor removal | Method class, factor class, outcome         |
| Magic link / email OTP | Email compromise **is** account compromise                   | Not a fallback for itself          | Channel re-verification        | Channel reference (tokenized), outcome      |
| SMS OTP                | SIM swap yields a verified channel and **no authentication** | n/a — it authenticates nothing     | Channel re-verification        | Channel reference (tokenized), outcome      |
| Recovery code          | Set exhaustion                                               | Reissue under step-up              | Whole set revoked and reissued | Set reference, consumption count            |
| Federated / eID        | Provider outage blocks login                                 | Local credential; assisted channel | Unlink                         | Issuer, audience, assertion freshness       |

**Never recorded:** the password, the OTP value, the recovery code value,
any private key, or the full WebAuthn assertion.

## 3. Rules that constrain the table

1. A method's assurance class is a **ceiling**, not a floor: risk signals
   may lower the effective assurance of a session, never raise it.
2. **Email is `low`; SMS carries no assurance at all.** Neither suffices
   for a high-risk action, and SMS suffices for no authentication.
3. A federated provider never grants assurance above what its own adapter
   assessment establishes, and never becomes a global user ID (ADR-079).
4. A method with "step-up eligible: no" can never satisfy a step-up
   requirement, whatever the session already holds.
5. A method's **cap** — `substantial` for synced passkeys and for password
   plus MFA — is not raised by combining it with another capped method. Two
   `substantial` paths do not add up to a `high` one.
