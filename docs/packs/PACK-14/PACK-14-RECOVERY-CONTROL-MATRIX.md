# PACK-14 — Recovery Control Matrix

**Round:** PACK-14 — specification and ADR only. **No code. Not implemented. Not a candidate. Not a PASS.**
**Repository version:** unchanged at `0.13.0` · **Canon version:** unchanged at `0.8.0`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**
**Architecture correction applied (2026-07-30).**

Recovery is where strong authentication is actually defeated. This matrix
is the control set that answers that.

## 1. The governed workflow

| Step                     | Actor                      | Required                                             | Refusal reason code                 |
| ------------------------ | -------------------------- | ---------------------------------------------------- | ----------------------------------- |
| Recovery requested       | Account holder or assisted | Identified account; channel not the one just changed | `RECOVERY_CONTACT_RECENTLY_CHANGED` |
| Risk assessed            | System + Recovery Reviewer | Explainable signals, not a bare score                | `RECOVERY_RISK_TOO_HIGH`            |
| Alternate verification   | Account holder             | A method independent of the lost one                 | `ALTERNATE_VERIFICATION_FAILED`     |
| Cooling-off              | System                     | Notification out of band during the window           | `RECOVERY_COOLING_OFF_ACTIVE`       |
| Old credentials revoked  | System                     | All credentials the request covers                   | —                                   |
| Sessions revoked         | System                     | Every session for the account                        | —                                   |
| New credential enrolled  | Account holder             | Passkey preferred                                    | —                                   |
| Out-of-band notification | System                     | To every verified channel, including the old one     | —                                   |
| Recovery completed       | Recovery Reviewer          | Not the actor who initiated; not the subject         | `PRIVILEGED_APPROVAL_MISSING`       |

## 2. Binding rules

### 2.1 Recovery assurance — decided (OD-P14-10)

The earlier wording — "recovery is never weaker than the authentication it
replaces" — was too absolute to implement: recovery necessarily uses
different evidence from the credential that was lost, and demanding the same
evidence would mean demanding the lost credential. The rule is restated in
terms of **resulting confidence**, not identical means.

| Rule                                                                                                                                          | Why                                                                                     |
| --------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| **Recovery may use different evidence from the lost credential**                                                                              | That is what recovery is                                                                |
| **The resulting confidence must be equivalent** — or the shortfall carries an **explicit, reason-coded risk acceptance by a named authority** | Otherwise recovery silently becomes the account's real assurance level                  |
| **High-assurance recovery requires dual control, a cooling-off period and out-of-band notification — all three**                              | Each closes a different attack: collusion, speed, and the legitimate holder not knowing |
| **Emergency recovery restores access and does not immediately authorize high-risk actions**                                                   | Elevated capability returns only once the normal assurance path is satisfied            |
| **Old credentials and all sessions are revoked before completion, never after**                                                               | A recovery that leaves the attacker logged in has recovered nothing                     |

### 2.2 The remaining binding rules

| Rule                                                                               | Why                                                            |
| ---------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| No support agent completes a recovery alone                                        | Support impersonation is a first-class threat                  |
| No reviewer approves their own recovery action                                     | Insider reset is a first-class threat                          |
| **No security questions**                                                          | The answers are public for candidates and office-holders       |
| **No reliance on publicly discoverable personal facts**                            | Same                                                           |
| Cooling-off with notification where risk warrants                                  | Gives the legitimate holder time to stop a fraudulent recovery |
| A recently changed contact may not be the sole basis                               | Contact-change takeover is a first-class threat                |
| **SMS OTP may contribute only as a low-weight signal**, never as deciding evidence | It carries no assurance level at all (OD-P14-09)               |
| Evidence is produced and retained per PACK-09                                      | A disputed recovery must be answerable from a record           |
| Dispute path exists                                                                | "I did not request this" must lead somewhere                   |
| Emergency recovery is reason-coded, notified and reviewed afterwards               | Emergencies are where controls get skipped                     |

## 3. Fraud indicators

New device plus new location plus immediate credential change; recovery
requested within the notification window of a contact change; repeated
partial recoveries; recovery for an account holding a privileged grant;
recovery requested during an active election or ballot window; assisted
recovery where the helper is also the requester.

Each raises the required assurance, extends cooling-off, or routes to
manual review — and each is named, so a denial can be explained.

## 4. Credential-specific recovery impact

| Lost or compromised          | Immediate effect                                   | Recovery path                                |
| ---------------------------- | -------------------------------------------------- | -------------------------------------------- |
| One passkey of several       | That credential revoked                            | Continue with another; enroll a replacement  |
| The only passkey             | Account cannot authenticate at `high`              | Full recovery workflow                       |
| Device stolen                | Device-bound credentials revoked; sessions revoked | Full recovery workflow, elevated risk        |
| Device lost, not compromised | Credential revoked on request                      | Second credential, or recovery workflow      |
| TOTP factor                  | Factor removed                                     | Recovery codes, or recovery workflow         |
| Recovery code set            | Whole set revoked                                  | Reissue under step-up                        |
| Email account compromised    | Email-based methods suspended                      | Recovery workflow with an independent method |
| SIM swapped                  | SMS methods suspended                              | Recovery workflow with an independent method |
