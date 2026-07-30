# PACK-14 — Session Security Matrix

**Round:** PACK-14 — specification and ADR only. **No code. Not implemented. Not a candidate. Not a PASS.**
**Repository version:** unchanged at `0.13.0` · **Canon version:** unchanged at `0.8.0`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**
**Architecture correction applied (2026-07-30).**

## 0. Status of the session model — decided

**`SessionRecord` is a PACK-14 service-level aggregate.** It is **not**
added to canon, and its events use PACK-13's canonical envelope unchanged.
The precedent is PACK-12's `PrivilegedSession`: a session is an operational
fact about a running system, not the kind of governed institutional record
canon holds. Owner: `identity-service`, `sessions` module (OD-P14-05,
OD-P14-02).

## 0.1 Governed timeout defaults — decided

Configuration with safe defaults, owned by `FIR-CONFIG-001`. Not constants,
not canon (OD-P14-04).

| Assurance     | Idle timeout | Absolute timeout |
| ------------- | ------------ | ---------------- |
| `low`         | 30 minutes   | 7 days           |
| `substantial` | 30 minutes   | 24 hours         |
| `high`        | 15 minutes   | 8 hours          |

| Freshness window             | Default    |
| ---------------------------- | ---------- |
| Consequential action step-up | 15 minutes |
| Ordinary official submission | 60 minutes |
| Security or contact change   | 15 minutes |

Stricter is free; relaxing is a governed change with an authority and a
reason code; **no configuration removes a deadline**, and none may disable
step-up, an audit obligation or a separation of duties. Missing
configuration falls back to these defaults, never to permissive behaviour.

## 1. Session model fields

| Field                     | Meaning                                                    | Notes                                       |
| ------------------------- | ---------------------------------------------------------- | ------------------------------------------- |
| `SessionId`               | Opaque identifier                                          | Never appears in a URL                      |
| `SessionRecord`           | The session aggregate                                      | Owned by the Session Security context       |
| `SessionAssurance`        | Current effective assurance                                | Recomputed on trigger, not cached forever   |
| `SessionStatus`           | `active` / `idle` / `expired` / `revoked` / `quarantined`  |                                             |
| `SessionOrigin`           | Issuing origin                                             | Bound to one workspace                      |
| `SessionScope`            | Workspace scope and permitted capability set               | Never spans a risk boundary                 |
| `SessionIssuedAt`         | Issue time                                                 |                                             |
| `SessionExpiresAt`        | Effective expiry                                           | Min of idle and absolute deadlines          |
| `SessionIdleDeadline`     | Idle timeout                                               | Mandatory                                   |
| `SessionAbsoluteDeadline` | Absolute timeout                                           | Mandatory; no infinite session              |
| `SessionLastActivity`     | Last observed activity                                     | Minimised: no page-level tracking           |
| `SessionRevocation`       | Revocation record with reason code and actor               | Immutable                                   |
| `SessionRiskState`        | Current risk classification                                | Explainable, never an opaque score alone    |
| `StepUpReference`         | The step-up that authorised a pending consequential action | Action- and object-version-bound            |
| `DeviceReference`         | Device the user can recognise in the session inventory     | Not a stable cross-domain device identifier |

## 2. Mandatory rules and how each is verified at implementation stage

| Rule                                              | Implementation-stage test                                                  |
| ------------------------------------------------- | -------------------------------------------------------------------------- |
| Rotation after authentication                     | The post-authentication session ID differs from the pre-authentication one |
| Rotation after step-up and after privilege change | Same, for each trigger                                                     |
| Idle timeout enforced                             | A session past its idle deadline is refused, not renewed                   |
| Absolute timeout enforced                         | A continuously active session still ends at the absolute deadline          |
| No infinite session                               | No code path constructs a session without both deadlines                   |
| Revoke one session                                | The targeted session is refused; siblings survive                          |
| Revoke all sessions                               | Every session for the account is refused                                   |
| Revoked session cannot refresh                    | A refresh attempt on a revoked session is a refusal with `SESSION_REVOKED` |
| Credential compromise invalidates its sessions    | Revoking a credential revokes the sessions it could have produced          |
| Refresh-token rotation                            | A rotated token is single-use                                              |
| Rotated-token reuse treated as replay             | Reuse revokes the family and raises `SESSION_REPLAY_DETECTED`              |
| No session identifier in a URL                    | Route and link inspection finds none                                       |
| Secure cookie attributes                          | `Secure`, `HttpOnly`, appropriate `SameSite` on every session cookie       |
| CSRF strategy on state-changing requests          | A state-changing request without the required token is refused             |
| Origin binding where the flow permits             | An assertion or token presented from another origin is refused             |

## 3. Suspicious session handling

| Signal                           | Weight   | Response                                          |
| -------------------------------- | -------- | ------------------------------------------------- |
| New device                       | medium   | Notify; optional challenge                        |
| Unusual origin                   | medium   | Challenge                                         |
| Repeated authentication failures | high     | Rate limit; lock per policy; notify               |
| Session replay detected          | **high** | Revoke family; security alert; evidence           |
| Impossible travel                | **weak** | Signal only. Never a sole basis for denial        |
| Credential added or removed      | high     | Notify old and new channels; assurance recomputed |
| Recovery attempt                 | high     | Out-of-band notification; cooling-off per policy  |
| Privileged operation             | high     | PACK-12 grant checks; audit before event          |

**No opaque risk score is ever the sole basis for a consequential denial.**
Every denial carries a reason code, an explanation, a notification, a
challenge or review path, and false-positive handling.
