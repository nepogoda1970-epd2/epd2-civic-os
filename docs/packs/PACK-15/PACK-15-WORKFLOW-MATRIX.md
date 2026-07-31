# PACK-15 — Workflow Matrix

**Round:** PACK-15 — specification and ADR only. **No code. Not implemented. Not a candidate. Not a PASS.**
**Repository version:** unchanged at `0.14.0` · **Canon version:** unchanged at `0.8.0`
**Baseline:** `EPD2_PACK-14_IDENTITY_AUTHENTICATION_ACCOUNT_SECURITY_0.14.0_FINAL_PASS.zip`
**Authoritative register:** `EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER_UPDATED_V6.md`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**
**Architecture correction applied (2026-07-31).**

Submission, intake, review, correction, withdrawal, decision and appeal per
form. Required by `FIR-FORM-002`.

---

## 1. Per-form workflow

| Form                                  | Submission                | Intake        | Review                              | Correction           | Withdrawal                     | Decision                              | Appeal   |
| ------------------------------------- | ------------------------- | ------------- | ----------------------------------- | -------------------- | ------------------------------ | ------------------------------------- | -------- |
| `F-P15-01` Prüfung beantragen         | self-service or assisted  | case opened   | automatic; human where triggered    | resubmit evidence    | withdrawable before decision   | automatic, or Eligibility Reviewer    | **yes**  |
| `F-P15-02` Nachweise einreichen       | self-service or assisted  | attached      | **Eligibility Reviewer**            | further evidence     | withdrawable before decision   | Eligibility Reviewer                  | **yes**  |
| `F-P15-03` Widerspruch (Berechtigung) | self-service              | case opened   | **Dispute Reviewer, not the original decider** | further evidence | withdrawable before decision | Dispute Reviewer                   | escalation |
| `F-P15-04` Zugang abrufen             | self-service              | automatic     | none                                | n/a                  | cancel before presentation     | automatic on a valid assertion        | via `F-P15-05` |
| `F-P15-05` Problem mit dem Zugang     | self-service or assisted  | **two records, two streams** | Credential Issuer + Eligibility Officer | n/a  | n/a                            | governed reissue, or refusal with reason | **yes** via `F-P15-06` |
| `F-P15-06` Widerruf überprüfen        | self-service              | case opened   | **Dispute Reviewer**                | further evidence     | withdrawable before decision   | Dispute Reviewer                      | escalation |
| `F-P15-07` Unterstützung anfordern    | self-service or by phone  | request       | none                                | amend                | cancel                         | arranged; confirmed to the participant | n/a      |
| `F-P15-08` Protokoll unterstützte Ausgabe | helper, countersigned | recorded      | sampling by the Security Auditor    | n/a                  | n/a                            | receipt issued to the participant     | n/a      |
| `F-P15-09` Unabhängige Prüfung        | member or Governance      | case opened   | **Independent Auditor**             | scope clarification  | withdrawable                   | audit report                          | escalation |

---

## 2. Consequential operations and their gates

| Operation                          | Step-up | Object-version bound | Notification              | Dual control                    | Cutoff-bound |
| ---------------------------------- | ------- | -------------------- | ------------------------- | ------------------------------- | ------------ |
| Request eligibility evaluation     | no      | rule-set version     | on decision               | no                              | issuance window |
| Record an eligibility decision     | yes     | case version         | yes                       | no                              | no           |
| Grant a manual exception           | yes     | case version         | yes                       | **yes**                         | no           |
| Issue an eligibility assertion     | n/a (system) | decision version | no (implicit in issuance) | no                              | issuance window |
| Revoke an assertion before use     | no      | assertion            | yes                       | admin path only                 | no           |
| Issue a voting credential          | no (assertion carries the authority) | assertion nonce | yes | no                     | issuance window |
| Revoke an unredeemed credential    | n/a     | credential           | yes where possible        | **yes, late in the window**     | **yes**      |
| Governed reissue                   | yes     | both records         | yes                       | **yes**                         | **yes**      |
| Redeem a credential                | no      | credential           | no                        | no                              | redemption window |
| Activate a voting context          | yes     | context version      | announced                 | **yes**                         | n/a          |
| Suspend or cancel a context        | yes     | context version      | announced                 | **yes**                         | n/a          |
| Change a context's windows         | yes     | context version      | announced                 | **yes**                         | n/a          |
| Export an audit bundle             | yes     | bundle scope         | logged                    | no                              | n/a          |

**A credential issuance requires no step-up** because the assertion already
encodes a satisfied assurance requirement that was checked on the identity
side. Requiring a step-up at the voting side would require the voting side
to know who is stepping up, which is the thing it must not know.

---

## 3. Dispute grounds, evidence, reviewer, remedy and limit

| Ground                          | Evidence permitted                       | Reviewer            | Remedy available                                | Hard limit                                              |
| ------------------------------- | ---------------------------------------- | ------------------- | ----------------------------------------------- | ------------------------------------------------------- |
| Eligibility denied              | Case record; PACK-11 references          | Dispute Reviewer    | Re-evaluation; manual review; decision reversal | None beyond the issuance window unless extended         |
| Wrong organizational scope      | Scope match record                       | Dispute Reviewer    | Scope correction; re-evaluation                 | Same                                                    |
| Stale membership data           | Freshness metadata                       | Dispute Reviewer    | Re-evaluation on refreshed facts                | Same                                                    |
| Credential not issued           | Issuance refusal record                  | Dispute Reviewer    | Reissue if before the cutoff                    | **No reissue after the cutoff**                         |
| Credential lost                 | Holder-supplied reference                | Dispute Reviewer    | Revoke-then-reissue before the cutoff           | **No reissue after redemption**                         |
| Credential revoked              | Revocation record                        | Dispute Reviewer    | Reversal and reissue if the revocation was wrong| Same                                                    |
| Duplicate issuance rejected     | Refusal record                           | Dispute Reviewer    | Reissue if the rejection was wrong              | Same                                                    |
| Handoff expired                 | Handoff record                           | Eligibility Officer | New handoff                                     | Within the issuance window                              |
| False replay detection          | Replay record; holder's reference        | Dispute Reviewer    | Reissue; correction of the detection rule       | Same                                                    |
| System outage                   | `AS-06` incident evidence                | Governance          | **Context-level**: window extension or re-run   | Not an individual remedy                                |
| Accessibility failure           | Assistance record                        | Dispute Reviewer + inclusion support | Alternative channel; window extension    | Same                                                    |
| Assisted-channel dispute        | Assisted-action receipt                  | Dispute Reviewer    | Correction; investigation of the helper         | **Never resolved by examining a ballot**                |

**Two rules apply to every row.** No appeal requires or accepts the
disclosure of ballot content. No reviewer, in any of these paths, acquires
the ability to link a person to a ballot — including by correlating case
timing with redemption timing, which is why dispute case records carry
timing classes rather than precise timestamps.

---

## 4. Assisted-channel rules (`FIR-INCLUSION-001`)

| Rule                                                          | Consequence                                                                      |
| ------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| A helper is attributed on every assisted action               | `assisted_by` is mandatory in the assisted path                                  |
| **No operator impersonation**                                 | The system never records an assisted act as if the participant acted alone       |
| Assistance is not authority to decide                         | A helper may prepare and submit; they never approve                              |
| **No helper retains a credential**                            | Delivery is to the holder; the helper declares no retention, and it is receipted |
| **Assistance never reveals or controls a ballot choice**      | The helper's path ends at the boundary of the voting client                      |
| The receipt names the helper and is given to the participant  | The participant can see who acted                                                |
| Offline and in-person paths produce the same evidence classes | No second-class channel                                                          |
| A representative may not cast a ballot on someone's behalf    | `FIR-REPRESENT-001` stops at the boundary                                        |

---

## 5. Failure behaviour in workflows

| Condition                       | Behaviour                                                                                                     |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| Audit unavailable               | Consequential operations refuse. **No unlogged issuance, revocation or redemption**                           |
| Replay store unavailable        | Issuance refuses. **Never bypassed**                                                                          |
| Notification fails              | The operation records the failure; the status remains visible in the workspace                                |
| Reviewer unavailable            | The case waits and is escalated; **never auto-approved and never auto-denied**                                 |
| Source unavailable              | Fail-closed with a reason code; assisted review is offered                                                    |
| Voting origin unavailable       | Refused with a reason code; a prolonged outage becomes a context-level decision                               |
| Partial issuance                | Treated as failure; the nonce remains unspent; the retry is idempotent                                        |
| Ambiguous issuance outcome      | **Never retried with a fresh nonce**; the same key is retried, or the governed reissue path is used           |
| Dispute deadline missed by the organization | The dispute is not closed by the deadline passing; silence is never a decision                    |

---

## 6. Gates added by the architecture correction (2026-07-31)

### 6.1 Additional consequential operations

| Operation                          | Step-up | Object-version bound | Notification            | Dual control | Cutoff-bound |
| ---------------------------------- | ------- | -------------------- | ----------------------- | ------------ | ------------ |
| Mint an eligibility assertion      | n/a (system) | decision version | no                      | no           | issuance window |
| Release a queued assertion         | n/a (system) | assertion       | **yes — "access available"** | no      | issuance window |
| Release below the minimum cohort   | n/a (system) | assertion       | yes                     | no           | recorded to `AS-04` |
| Redeem the one-time pickup         | no      | pickup               | no                      | no           | pickup expiry |
| Configure an `IssuanceTimingProfile`| yes    | context version      | announced               | **yes**      | before activation |
| Generate an evidence bundle        | yes     | bundle scope         | logged                  | no           | n/a          |
| Export a bundle **before closure**  | yes     | bundle scope         | logged                  | **yes**      | n/a          |
| Export a bundle after closure       | yes     | bundle scope         | logged                  | no           | n/a          |

### 6.2 Delivery gates

| Gate                                                                       | Behaviour                                                              |
| -------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| Credential issuance requested from outside the voting origin               | Refused, `CREDENTIAL_ORIGIN_REFUSED`                                   |
| Any non-WS-03 delivery attempted                                            | Refused, `DELIVERY_CHANNEL_REFUSED`, recorded to `AS-04`               |
| Assisted session with screen sharing active during the credential exchange | The exchange is not offered; the participant completes it unobserved   |
| Helper requests the credential on the participant's behalf                  | Refused; there is no operation and no material to hand over            |
| Participant asks for the access to be sent to them                          | Explained, not refused silently (`PACK-15-CONTENT-CATALOGUE-DE.md` §12.7) |

### 6.3 Assisted-channel rules — additions

| Rule                                                                              | Consequence                                                         |
| --------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| Assistance ends at the credential exchange                                        | The helper may bring the participant to WS-03 and no further        |
| **There is no credential material for a helper to retain**                        | The `F-P15-08` non-retention declaration becomes structurally true  |
| No screen sharing, remote control or shadowing during the exchange                | An observed exchange is an operator-visible credential              |
| Offline and in-person fallback confirms **eligibility only**                       | Isolation is never waived for accessibility                         |
| Where an independent accessible path is not achievable, it is a named limitation  | With an owner, not a silent downgrade                               |

### 6.4 Dispute grounds — one added

| Ground                        | Evidence permitted            | Reviewer         | Remedy available                                   | Hard limit                                  |
| ----------------------------- | ----------------------------- | ---------------- | -------------------------------------------------- | ------------------------------------------- |
| Access never released from the queue | Queue and release records (class level) | Dispute Reviewer | Release; window extension; governed reissue | None after the cutoff; then context-level only |
