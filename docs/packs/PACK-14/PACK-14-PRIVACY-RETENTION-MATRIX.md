# PACK-14 — Privacy and Retention Matrix

**Round:** PACK-14 — specification and ADR only. **No code. Not implemented. Not a candidate. Not a PASS.**
**Repository version:** unchanged at `0.13.0` · **Canon version:** unchanged at `0.8.0`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**
**Architecture correction applied (2026-07-30).**

Required by `FIR-FORM-002`.

**`OD-P14-07` deliberately remains open, and deliberately does not block the
reference implementation.** A retention period is a legal determination and
**PACK-09 owns retention schedules**; this pack may not settle one. What
would block implementation is not an unconfirmed number but an undefined
behaviour — so the behaviour is defined here and only the durations await
confirmation.

| What is settled now                                                                | What awaits legal confirmation             |
| ---------------------------------------------------------------------------------- | ------------------------------------------ |
| Which record classes exist and what each may contain                               | The exact duration for each class          |
| That every class **has** a schedule and none is unbounded                          | Whether a given duration is 90 days or 180 |
| Every deletion prohibition in §3 — they hold whatever the durations turn out to be | —                                          |
| Fail-closed behaviour on unknown legal-hold state                                  | —                                          |
| The data-minimization commitments in §2                                            | —                                          |

The durations below are **safe provisional schedules**: short enough to
limit exposure, long enough to answer a dispute, and adjustable by governed
configuration (`FIR-CONFIG-001`) once PACK-09 and legal review confirm them.
Changing a duration changes a configuration value, not the design.

## 1. Record classes

| Record class                | Contains                                                            | Retention (reference)                                        | Legal hold applies | Deletion effect                                                 |
| --------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------ | ------------------ | --------------------------------------------------------------- |
| Account record              | `account_id`, status, locale, terms version                         | Life of the account + statutory period                       | yes                | Anonymized, not erased, where obligations remain                |
| Contact history             | Channel class, tokenized reference, verification and change history | 24 months after change                                       | yes                | Tokenized reference retained; raw value removed                 |
| Credential metadata         | Type, nickname, binding, created/last-used, revocation              | Life of the credential + 12 months                           | yes                | Metadata retained; **no key material ever existed here**        |
| Authentication attempts     | Method class, outcome, reason code, coarse origin                   | 90 days                                                      | yes                | Aggregated then removed                                         |
| Session history             | Scope, assurance, issue/revoke, device reference                    | 12 months                                                    | yes                | Removed                                                         |
| Suspicious activity         | Signal category, response, reason code                              | 24 months                                                    | yes                | Retained where a case is open                                   |
| Recovery evidence           | Case, assessment, decision, notifications, dual-control record      | 6 years                                                      | **yes**            | **Never deleted while a dispute or hold is open**               |
| Identity proofing evidence  | PACK-11 bundle references; documents                                | Per purpose; document evidence at the shortest lawful period | **yes**            | Governed disposition only, with PACK-09 authorization           |
| Privileged identity actions | Grant, actor role, reason code, approval chain                      | 10 years                                                     | **yes**            | Never deleted while an oversight obligation exists              |
| Voting handoff issuance     | Purpose scope, expiry, redemption fact                              | **Shortest possible**                                        | no                 | Deleted early **and** in a way that creates no correlation (§3) |

## 2. Data minimization commitments

| Commitment                                                                                                  | Where enforced            |
| ----------------------------------------------------------------------------------------------------------- | ------------------------- |
| No password, OTP, recovery code, private key or full WebAuthn assertion is stored in any record class above | Audit rules; AC-P14-077   |
| No identity document content appears outside its PACK-11 bundle                                             | AC-P14-078                |
| Raw contact values are replaced by tokenized references wherever a reference suffices                       | AC-P14-079                |
| No record class carries a cross-domain identifier                                                           | ADR-079; AC-P14-001       |
| Session activity is recorded coarsely; no page-level tracking                                               | Session model             |
| Analytics carries no identity, and WS-03 carries no analytics at all                                        | FRONT-00 telemetry policy |

## 3. Deletion constraints

Deletion must not:

1. **destroy evidence** required by an open dispute, an oversight
   obligation or a legal hold — PACK-09 decides, not the identity domain;
2. **violate a legal hold** — an attempted deletion under hold is a
   refusal with `RECORD_UNDER_LEGAL_HOLD`, and an unknown hold state fails
   closed;
3. **weaken voting unlinkability** — deleting one side of a pair of records
   can make the surviving side identifying. Handoff records are deleted as
   a set, not individually;
4. **create a reuse or correlation vulnerability** — releasing a contact
   handle or an identifier for reuse must not allow a later holder to
   inherit, or a former holder to recover, another person's history.

## 4. Data subject rights

Access, correction, deletion, objection and export requests are governed by
PACK-09 and PACK-12's existing mechanisms. PACK-14 adds no parallel
mechanism and no new export surface. Where a right conflicts with a
retention obligation, the conflict is decided by the governed process, not
by the identity service — and the outcome is reason-coded either way.
