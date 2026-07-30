# PACK-14 — Identity Proofing Matrix

**Round:** PACK-14 — specification and ADR only. **No code. Not implemented. Not a candidate. Not a PASS.**
**Repository version:** unchanged at `0.13.0` · **Canon version:** unchanged at `0.8.0`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**
**Architecture correction applied (2026-07-30).**

## 1. Proofing levels and canon mapping

| Level                      | Evidence                                | Canon identity assurance (19d.2) | Manual review | Typical use                                |
| -------------------------- | --------------------------------------- | -------------------------------- | ------------- | ------------------------------------------ |
| Self-asserted              | The person's statement                  | `none`                           | no            | Account creation                           |
| Email-verified             | Control of an email channel             | `none`                           | no            | Contact reachability only                  |
| Phone-verified             | Control of a phone channel              | `none`                           | no            | Contact reachability only                  |
| Document-assisted          | Identity document, reviewed             | `low`–`substantial`              | yes           | Where a real identity must be plausible    |
| Organizational attestation | A competent body's attestation          | `substantial`                    | yes           | Assisted and offline admission             |
| In-person                  | Physical presentation, recorded         | `substantial`–`high`             | yes           | Inclusion channel; high-assurance cases    |
| eID                        | A recognised electronic identity scheme | `high`                           | no            | Where the scheme is accepted               |
| Manually reviewed          | Any of the above, escalated             | as decided                       | yes           | Ambiguity, conflict, suspected duplication |

**Canon 19d.2's prohibition is carried unchanged:** verification through
any `identity_scheme` is never equivalent to, and never implies, a
particular citizenship. `identity_assurance_level` is computed solely from
the fact and quality of identity verification.

## 2. Proofing case lifecycle

```text
started → evidence received → { verified | rejected | manual review required }
```

Each transition records method, evidence reference, assurance, deciding
authority, reason code and timestamp. A correction is a new case, never a
rewrite — the pattern PACK-11 established for governed documents.

## 3. Boundaries

| Rule                                                   | Consequence                                               |
| ------------------------------------------------------ | --------------------------------------------------------- |
| `person_record_id` is not an integration key           | No domain joins to it                                     |
| A person record is **optional**                        | Accounts that never need proofing never acquire one       |
| Proofing does not approve membership                   | Canon 19d.9 stage B is a separate human decision          |
| Proofing does not authorise anything by itself         | Authorization is decided per act                          |
| Evidence uses PACK-11 mechanisms                       | No second evidence store                                  |
| Retention follows PACK-09                              | Including legal hold and destruction authorization        |
| Derived booleans cross the boundary where they suffice | ADR-027's established pattern; raw attributes stay inside |

## 4. External provider adapter requirements

| Requirement                 | Refusal reason code if unmet    |
| --------------------------- | ------------------------------- |
| Minimum attribute release   | —                               |
| No provider ID as global ID | —                               |
| Purpose limitation          | —                               |
| Audience restriction        | `EXTERNAL_ASSERTION_INVALID`    |
| Issuer validation           | `EXTERNAL_ASSERTION_INVALID`    |
| Assertion freshness         | `IDENTITY_ASSERTION_EXPIRED`    |
| Replay prevention           | `EXTERNAL_ASSERTION_INVALID`    |
| Outage behaviour defined    | `EXTERNAL_PROVIDER_UNAVAILABLE` |
| Compromise response defined | —                               |
| Evidence recorded           | —                               |
| Fallback defined            | —                               |

**No provider is selected by this round.**
