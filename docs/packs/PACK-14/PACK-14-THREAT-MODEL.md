# PACK-14 — Threat Model

**Round:** PACK-14 — specification and ADR only. **No code. Not implemented. Not a candidate. Not a PASS.**
**Repository version:** unchanged at `0.13.0` · **Canon version:** unchanged at `0.8.0`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**
**Architecture correction applied (2026-07-30).**

Each row states the protected asset, the attacker or failure, the trust
boundary crossed, the preventive control, the detective control, the
evidence produced, the residual risk this round cannot close, and the pack
that owns the remainder.

## 1. Identity architecture threats

| #    | Threat                                                                       | Asset                            | Attacker / failure                                | Boundary              | Preventive control                                                                          | Detective control                          | Evidence                          | Residual risk                                                                                                | Dependency           |
| ---- | ---------------------------------------------------------------------------- | -------------------------------- | ------------------------------------------------- | --------------------- | ------------------------------------------------------------------------------------------- | ------------------------------------------ | --------------------------------- | ------------------------------------------------------------------------------------------------------------ | -------------------- |
| T-01 | **Global ID emergence** — an identifier quietly becomes universal            | Unlinkability across all domains | Ordinary engineering convenience, not an attacker | Every domain boundary | ADR-079; scoped actor references; `GLOBAL_IDENTITY_KEYS` prohibition inherited from PACK-13 | Structural scans over payloads and schemas | Schema and payload review records | A hashed or opaque re-derivation is not name-detectable — the same residual `FIR-INV-001` has always carried | Implementation round |
| T-02 | **Email-based correlation** — email used as a join key                       | Unlinkability                    | Analytics, support tooling, imports               | Domain boundaries     | Email is an attribute, never an identifier (ADR-080)                                        | Prohibited-key checks                      | Review records                    | Email remains a real-world correlator outside the system                                                     | —                    |
| T-03 | **Provider identifier correlation** — an IdP subject claim stored everywhere | Unlinkability                    | Federated login integration                       | Adapter boundary      | ADR-086: no provider ID as a global ID; minimum attribute release                           | Adapter conformance review                 | Adapter assessment                | Provider-side correlation is outside this system's control                                                   | PACK-14 impl.        |
| T-04 | **Account enumeration** — learning which addresses have accounts             | Member privacy                   | External prober                                   | Public surface        | Uniform responses and timing for existent and non-existent accounts                         | Rate anomaly detection                     | Reason-coded refusals             | Perfect uniformity is hard under load                                                                        | Implementation round |
| T-05 | **Duplicate account merge** — two people's records joined                    | Personal data integrity          | Well-meaning support                              | Account Registry      | No automatic merge by email, name or date of birth (ADR-080)                                | Duplicate review queue                     | Review decision and reason code   | Manual review can still err                                                                                  | —                    |

## 2. Credential and authentication threats

| #    | Threat                                                  | Preventive control                                                          | Detective control            | Residual risk                                                                                                    |
| ---- | ------------------------------------------------------- | --------------------------------------------------------------------------- | ---------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| T-06 | **Phishing**                                            | Passkey-first, origin-bound assertions (ADR-081)                            | Suspicious-login signals     | Non-passkey fallback methods remain phishable — hence their lower assurance class and restricted allowed actions |
| T-07 | **Credential stuffing**                                 | Rate limiting; MFA requirement; breached-password boundary                  | Failure-rate signals         | Depends on the password fallback decision (OD-P14-03)                                                            |
| T-08 | **Password spraying**                                   | Per-account and per-origin rate limits                                      | Distributed failure patterns | Same                                                                                                             |
| T-09 | **Passkey downgrade** — being pushed to a weaker method | Method assurance classes are ceilings; high-risk actions require `high`     | Assurance-change events      | A user with only weak methods simply cannot perform those actions — inclusion, not security, is the cost         |
| T-10 | **MFA downgrade**                                       | Factor removal is a step-up action and downgrades assurance immediately     | `credential.mfa_removed`     | —                                                                                                                |
| T-11 | **Passkey removal abuse**                               | Removing the last credential requires step-up and an existing recovery path | `credential.passkey_removed` | —                                                                                                                |

## 3. Session threats

| #    | Threat                            | Preventive control                                                       | Detective control                  | Residual risk                                     |
| ---- | --------------------------------- | ------------------------------------------------------------------------ | ---------------------------------- | ------------------------------------------------- |
| T-12 | **Session fixation**              | Mandatory rotation after authentication and privilege change             | Rotation events                    | —                                                 |
| T-13 | **Token replay**                  | Refresh-token rotation; reuse revokes the family                         | `session.replay_detected`          | Detection is post hoc by construction             |
| T-14 | **Refresh-token theft**           | Short lifetimes; rotation; origin binding                                | Replay detection                   | —                                                 |
| T-15 | **Cookie theft**                  | `Secure`, `HttpOnly`, `SameSite`; no session ID in URLs                  | Unusual-origin signals             | A compromised endpoint still holds a live session |
| T-16 | **XSS-assisted session theft**    | `HttpOnly`; CSP as a frontend obligation; no identity in browser storage | —                                  | XSS remains a frontend risk owned by FRONT-PACK   |
| T-17 | **CSRF**                          | Required CSRF strategy on every state-changing request                   | Refusals with `CSRF_TOKEN_INVALID` | —                                                 |
| T-18 | **Cross-origin leakage**          | No parent-domain cookie; no cross-origin token reuse; no storage bridge  | Origin-mismatch refusals           | —                                                 |
| T-19 | **Voting Client session leakage** | WS-03 shares nothing; one-time, identity-free handoff (ADR-088)          | `voting_handoff.refused`           | The credential protocol itself is PACK-15/16's    |

## 4. Recovery and human-channel threats

| #    | Threat                                    | Preventive control                                                                                             | Detective control           | Residual risk                                                            |
| ---- | ----------------------------------------- | -------------------------------------------------------------------------------------------------------------- | --------------------------- | ------------------------------------------------------------------------ |
| T-20 | **Recovery takeover**                     | Governed workflow; cooling-off; independent verification (ADR-085)                                             | Fraud indicators            | A determined attacker with several compromised channels                  |
| T-21 | **Support-engineering attack**            | Support cannot complete recovery alone                                                                         | Privileged action audit     | Social engineering of two people is harder, not impossible               |
| T-22 | **Insider reset**                         | No self-approval; separation of duties re-checked at the act (ADR-087)                                         | Audit before event          | Collusion                                                                |
| T-23 | **Malicious account linking**             | User-initiated only; step-up; proof of control of both sides                                                   | Linking events              | —                                                                        |
| T-24 | **Contact-change takeover**               | Notify both old and new channel; protective window; recently changed contact cannot be the sole recovery basis | `contact.changed`           | —                                                                        |
| T-25 | **SIM swap**                              | SMS is a lower-assurance fallback; never sole for high-risk                                                    | Channel-change signals      | Carrier-side control is outside the system                               |
| T-26 | **Email compromise**                      | Email methods are `low`; recovery requires an independent method                                               | Suspicious-recovery signals | Email remains the weakest common channel                                 |
| T-27 | **Device theft**                          | Device-bound credential revocation; session revocation                                                         | Session inventory           | The window before the user notices                                       |
| T-28 | **Shared-device leakage**                 | No persistent identity in browser storage; explicit sign-out; session inventory                                | —                           | Physical access remains physical access                                  |
| T-29 | **Malicious browser extension**           | Origin-bound assertions limit the value of what is observable                                                  | —                           | An extension in the page is inside the trust boundary. Named, not solved |
| T-30 | **Privilege escalation through recovery** | Recovery of a privileged account raises required assurance and review                                          | Fraud indicator             | —                                                                        |

## 5. Data-exposure and observability threats

| #    | Threat                             | Preventive control                                                            | Residual risk                                      |
| ---- | ---------------------------------- | ----------------------------------------------------------------------------- | -------------------------------------------------- |
| T-31 | **Identity-document exposure**     | Evidence held via PACK-11; never in events or logs; purpose-limited retention | Held evidence is still held                        |
| T-32 | **Excessive observability**        | Named allow-list of loggable fields; explicit never-log list                  | Operational pressure to log more                   |
| T-33 | **Analytics correlation**          | No shared analytics identity; WS-03 has no analytics at all                   | Third-party analytics remain a governance question |
| T-34 | **Browser-storage leakage**        | No identity in localStorage, sessionStorage or IndexedDB                      | —                                                  |
| T-35 | **Clock skew affecting freshness** | Explicit skew tolerance; fail-closed beyond it                                | Time is an external dependency                     |

## 6. Residual risks this round explicitly does not close

1. Password fallback **exists** and is fenced (OD-P14-03): passkey-first,
   no new password-only account, MFA always, never sole assurance for a
   consequential action, ceiling `substantial`, disableable by governed
   configuration. The residual is the one every password system carries — a
   correct password narrows an attacker's search — and the second factor is
   what answers it. The alternative, excluding passwords entirely, was
   rejected because it makes participation depend on owning a
   passkey-capable device.
2. Risk-signal evaluation is specified as explainable and reason-coded; the
   actual detection quality is an implementation and operations question.
3. Provider-side compromise and carrier-side compromise are outside this
   system's control and are recorded rather than mitigated.
4. The voting credential protocol and its threat model are **PACK-15's**.
   PACK-14 defines the `VotingHandoffArtifact` boundary only — opaque,
   single-use, short-lived, audience-bound, purpose-bound,
   voting-context-bound, carrying no identifier and permitting no reverse
   resolution.
5. **Cross-origin bootstrap is not SSO** (OD-P14-06). Each workspace runs
   its own ceremony and mints its own origin-local session from a
   single-use, audience-bound authorization response. The residual is that
   a compromise of `identity-service` itself compromises every ceremony —
   which is true of any identity provider and is why that service carries
   the pack's strictest privileged controls (ADR-087).
