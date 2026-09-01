# PACK-14 — Workflow Matrix

**Round:** PACK-14 — specification and ADR only. **No code. Not implemented. Not a candidate. Not a PASS.**
**Repository version:** unchanged at `0.13.0` · **Canon version:** unchanged at `0.8.0`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**
**Architecture correction applied (2026-07-30).**

Submission, intake, review, correction, withdrawal, decision and appeal per
form. Required by `FIR-FORM-002`.

## 1. Per-form workflow

| Form                                 | Submission               | Intake           | Review                         | Correction            | Withdrawal                          | Decision                                            | Appeal     |
| ------------------------------------ | ------------------------ | ---------------- | ------------------------------ | --------------------- | ----------------------------------- | --------------------------------------------------- | ---------- |
| `F-P14-01` Registrierung             | self-service             | automatic        | none                           | resubmit              | abandon before activation           | automatic on contact verification                   | n/a        |
| `F-P14-02/03` Kontaktbestätigung     | self-service             | automatic        | none                           | new code              | expire                              | automatic                                           | n/a        |
| `F-P14-04` Passkey einrichten        | self-service, step-up    | automatic        | none                           | rename                | cancel before confirm               | automatic                                           | n/a        |
| `F-P14-05` Passkey entfernen         | self-service, step-up    | automatic        | last-credential guard          | n/a                   | cancel before confirm               | automatic unless guarded                            | n/a        |
| `F-P14-06/07` MFA                    | self-service, step-up    | automatic        | none                           | replace               | cancel                              | automatic                                           | n/a        |
| `F-P14-08` Wiederherstellungscodes   | self-service, step-up    | automatic        | none                           | reissue               | cancel                              | automatic                                           | n/a        |
| `F-P14-09` **Wiederherstellung**     | self-service or assisted | case opened      | **risk assessment + reviewer** | additional evidence   | **withdrawable during cooling-off** | Recovery Reviewer, dual control where risk warrants | **yes**    |
| `F-P14-10` Verdächtige Anmeldung     | notified                 | automatic        | security case if "was_not_me"  | n/a                   | n/a                                 | automatic revocation                                | n/a        |
| `F-P14-11` Kontaktdaten ändern       | self-service, step-up    | automatic        | protective window              | reverse within window | cancel before verification          | automatic                                           | n/a        |
| `F-P14-12` Sitzungen beenden         | self-service, step-up    | automatic        | none                           | n/a                   | n/a                                 | automatic                                           | n/a        |
| `F-P14-13` Konto schließen           | self-service, step-up    | request recorded | retention check                | n/a                   | **cancellable during cooling-off**  | automatic after cooling-off                         | n/a        |
| `F-P14-14` Identitätsprüfung         | self-service or assisted | case opened      | **Identity Proofing Reviewer** | further evidence      | withdrawable before decision        | reviewer, or automatic for eID                      | **yes**    |
| `F-P14-15` Privilegierte Genehmigung | reviewer only            | case             | **dual control**               | n/a                   | n/a                                 | reviewer + second approver                          | escalation |

## 2. Consequential operations and their gates

| Operation                   | Step-up                                   | Object-version bound | Notification     | Dual control                | Cooling-off       |
| --------------------------- | ----------------------------------------- | -------------------- | ---------------- | --------------------------- | ----------------- |
| Add credential              | yes                                       | n/a                  | all channels     | no                          | no                |
| Remove credential           | yes (`high`)                              | credential reference | all channels     | no                          | no                |
| Remove last credential      | **refused** unless a recovery path exists | —                    | —                | —                           | —                 |
| Enroll or remove MFA        | yes                                       | factor reference     | all channels     | no                          | no                |
| Change contact              | yes                                       | —                    | **old and new**  | no                          | protective window |
| Revoke all sessions         | yes                                       | —                    | all channels     | no                          | no                |
| Complete recovery           | n/a                                       | case reference       | all channels     | **yes** where risk warrants | **yes**           |
| Close account               | yes (`high`)                              | —                    | all channels     | no                          | **yes**           |
| Submit proofing             | yes                                       | form version         | confirmation     | no                          | no                |
| Approve privileged recovery | yes (`high`)                              | case version         | subject notified | **yes**                     | n/a               |

## 3. Assisted-channel rules (`FIR-INCLUSION-001`)

| Rule                                                | Consequence                                                                             |
| --------------------------------------------------- | --------------------------------------------------------------------------------------- |
| A helper is attributed on every assisted action     | `assisted_by` is mandatory in the assisted path                                         |
| **No operator impersonation**                       | The system never records an assisted action as if the account holder performed it alone |
| Assistance is not authority to decide               | A helper may prepare and submit; they never approve                                     |
| The receipt names the helper                        | The account holder can see who acted                                                    |
| Offline proofing produces the same evidence classes | No second-class channel                                                                 |

## 4. Failure behaviour in workflows

| Condition                      | Behaviour                                                                                                            |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------- |
| Audit unavailable              | Consequential operations refuse. **No unlogged privileged act**                                                      |
| Notification fails             | The operation records the failure; security-relevant operations that depend on notification do not silently complete |
| Reviewer unavailable           | The case waits and is escalated; it is never auto-approved                                                           |
| Risk engine unavailable        | Fail-closed for consequential actions; governed fallback for the rest, with a reason code                            |
| Identity proofing inconclusive | Manual review, never a default verdict                                                                               |
| Partial session revocation     | Treated as failure; retried and reported, never reported as complete                                                 |
