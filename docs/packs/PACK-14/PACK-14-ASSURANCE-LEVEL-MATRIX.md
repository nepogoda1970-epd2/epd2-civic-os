# PACK-14 — Assurance Level Matrix

**Round:** PACK-14 — specification and ADR only. **No code. Not implemented. Not a candidate. Not a PASS.**
**Repository version:** unchanged at `0.13.0` · **Canon version:** unchanged at `0.8.0`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**
**Architecture correction applied (2026-07-30).**

PACK-14 **reuses canon's four-value scale** (canon 19d.2 for identity
assurance, canon 19d.8 for authentication assurance) and invents no new
vocabulary. The informal AAL names are a reading aid, not a second scale.

## 1. Levels

| Informal | Canon value   | Permitted methods                                                     | Idle timeout | Absolute timeout | Device / risk requirement                        |
| -------- | ------------- | --------------------------------------------------------------------- | ------------ | ---------------- | ------------------------------------------------ |
| AAL-0    | `none`        | —                                                                     | n/a          | n/a              | n/a                                              |
| AAL-1    | `low`         | Magic link, email OTP                                                 | 30 min       | 7 d              | None                                             |
| AAL-2    | `substantial` | Password **with MFA**, synced passkey, recovery code, verified device | 30 min       | 24 h             | Known device or accepted risk state              |
| AAL-3    | `high`        | Device-bound passkey, hardware key, eID where assessed                | 15 min       | 8 h              | Origin-bound; device-bound where policy requires |

**SMS OTP appears in no row.** It carries no assurance level and cannot
raise a session to any of them (OD-P14-09). **Password alone appears in no
row either**: password login always requires MFA, so the reachable level is
the `substantial` row and never `low` on its own (OD-P14-03).

### 1.1 Freshness windows

| Freshness window                  | Default    |
| --------------------------------- | ---------- |
| Consequential action step-up      | 15 minutes |
| Ordinary official submission      | 60 minutes |
| Security change or contact change | 15 minutes |

### 1.2 These values are governed configuration — decided

Closing **OD-P14-04**: every duration above is **configuration with a safe
default**, owned by `FIR-CONFIG-001`, not a hard-coded constant and not
canon.

1. A deployment may make any value **stricter** freely.
2. **Relaxing** a value is a governed change with an authority, a reason
   code and an audit record.
3. **No configuration may remove a deadline.** The schema admits no
   "unlimited" value.
4. **No configuration may disable step-up, an audit obligation or a
   separation of duties** (`FIR-INV-006`).
5. Missing or unreadable configuration falls back to these defaults, never
   to permissive behaviour.

## 2. Action mapping

| Action                                 | Required assurance | Freshness     | Step-up required | Notes                                                              |
| -------------------------------------- | ------------------ | ------------- | ---------------- | ------------------------------------------------------------------ |
| Read own dashboard                     | `low`              | session valid | no               |                                                                    |
| Read own security settings             | `substantial`      | 60 min        | no               |                                                                    |
| Change email or phone                  | `substantial`      | 15 min        | **yes**          | Notifies old **and** new channel                                   |
| Add a passkey                          | `substantial`      | 15 min        | **yes**          |                                                                    |
| Remove a passkey                       | `high`             | 15 min        | **yes**          | Removing the last credential additionally requires a recovery path |
| Enroll or remove an MFA factor         | `substantial`      | 15 min        | **yes**          |                                                                    |
| Issue recovery codes                   | `substantial`      | 15 min        | **yes**          |                                                                    |
| Submit a membership application        | `substantial`      | 60 min        | yes              | Canon 19d.9 stage B is a separate human decision                   |
| Submit an official form or declaration | `substantial`      | 60 min        | yes              | Bound to the exact form version (`FIR-FORM-001`)                   |
| Finance approval                       | `high`             | 15 min        | **yes**          | Object-version bound                                               |
| Privileged identity action             | `high`             | 15 min        | **yes**          | Plus a PACK-12 grant and separation of duties                      |
| Account closure request                | `high`             | 15 min        | **yes**          | Cooling-off applies                                                |
| Voting handoff                         | `high`             | 15 min        | **yes**          | Handoff carries no identity (ADR-088)                              |
| Revoke all sessions                    | `substantial`      | 15 min        | yes              | Also reachable from the recovery workflow                          |

## 3. Reauthentication and downgrade

| Trigger                                    | Effect                                                               |
| ------------------------------------------ | -------------------------------------------------------------------- |
| Freshness window elapsed                   | Effective assurance for the pending action drops; step-up required   |
| Absolute session deadline reached          | Session ends; no refresh                                             |
| Credential removed or revoked              | Assurance recomputed; sessions that relied on it are revoked         |
| MFA factor removed                         | Assurance downgraded from the moment of removal                      |
| Risk signal raised                         | Assurance downgraded and/or a challenge required, with a reason code |
| Crossing to a higher-sensitivity workspace | Reauthentication, never token exchange                               |
| Privilege change                           | Session rotation, then reassessment                                  |

**A downgrade does not destroy the session.** It leaves a session that can
still do what it satisfies and cannot do what it does not — which is the
whole point of assurance being per action rather than per login.

## 4. Fail-closed evaluation

Following canon 19d.8 exactly: a requirement is satisfied only if
authentication assurance, identity assurance, session freshness where
applicable and attribute freshness where applicable hold **simultaneously**.
No "or" condition is permitted. A missing, expired or unresolvable
authentication context is a refusal with a reason code, never a default
allow.
