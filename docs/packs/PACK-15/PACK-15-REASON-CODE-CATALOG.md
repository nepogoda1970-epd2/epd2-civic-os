# PACK-15 — Reason Code Catalog

**Round:** PACK-15 — specification and ADR only. **No code. Not implemented. Not a candidate. Not a PASS.**
**Repository version:** unchanged at `0.14.0` · **Canon version:** unchanged at `0.8.0`
**Baseline:** `EPD2_PACK-14_IDENTITY_AUTHENTICATION_ACCOUNT_SECURITY_0.14.0_FINAL_PASS.zip`
**Authoritative register:** `EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER_UPDATED_V6.md`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**
**Architecture correction applied (2026-07-31).**

## 0. The prohibition that shapes this catalog

**There is no generic `VOTING_ERROR`, and none may be added.** PACK-13's
`P13-RSN-002` and PACK-14's restatement apply unchanged, and in this domain
the stakes are highest: in a contested election the difference between
`CREDENTIAL_EXPIRED` and `CREDENTIAL_REVOKED` is the difference between an
administrative fact and an allegation, and the difference between
`ELIGIBILITY_DENIED` and `ELIGIBILITY_REVIEW_REQUIRED` is the difference
between an appeal and a wait.

Where two failures differ in what the participant must do next, they are
two codes. **A code's meaning never changes; a new meaning is a new code.**

Every code below is also a **user-facing obligation**: each maps to a
governed German text in `PACK-15-CONTENT-CATALOGUE-DE.md` that names the
reason, the responsible body and the next possible step.

---

## 1. Eligibility

| Code                                 | Meaning                                                           | Next step for the participant                |
| ------------------------------------ | ----------------------------------------------------------------- | -------------------------------------------- |
| `ELIGIBILITY_APPROVED`               | All criteria satisfied for this context                           | Obtain the credential                        |
| `ELIGIBILITY_DENIED`                 | A criterion was not satisfied                                     | Appeal (`F-P15-03`)                          |
| `ELIGIBILITY_REVIEW_REQUIRED`        | A human decision is needed; **this is not a denial**              | Wait; supply evidence if asked               |
| `ELIGIBILITY_MEMBERSHIP_INACTIVE`    | Membership is not active for this context                         | Membership process, then re-request          |
| `ELIGIBILITY_SCOPE_MISMATCH`         | The participant is outside the context's organizational scope     | Check the scope; appeal if wrong             |
| `ELIGIBILITY_RULE_NOT_SATISFIED`     | A named criterion of the frozen rule-set was not met              | Appeal                                       |
| `ELIGIBILITY_ASSURANCE_INSUFFICIENT` | The context's required assurance is not satisfied                 | Raise assurance (PACK-14), then re-request   |
| `ELIGIBILITY_SOURCE_STALE`           | A source fact is outside its freshness bound                      | Wait for refresh; assisted review            |
| `ELIGIBILITY_SOURCE_UNAVAILABLE`     | A source could not be reached; fail-closed                        | Retry; assisted review                       |
| `ELIGIBILITY_EVIDENCE_INCOMPLETE`    | Required evidence is missing                                      | Submit evidence (`F-P15-02`)                 |
| `ELIGIBILITY_DECISION_EXPIRED`       | The decision's validity window elapsed                            | Re-request within the issuance window        |
| `ELIGIBILITY_SELF_REVIEW_REFUSED`    | A reviewer attempted to decide their own or their own raised case | Reassignment; not a participant-facing state |

## 2. Assertion

| Code                          | Meaning                                                |
| ----------------------------- | ------------------------------------------------------ |
| `ASSERTION_INVALID`           | Integrity verification failed                          |
| `ASSERTION_EXPIRED`           | Presented past its expiry                              |
| `ASSERTION_AUDIENCE_MISMATCH` | Presented to a party it was not issued for             |
| `ASSERTION_PURPOSE_MISMATCH`  | Presented for a purpose other than credential issuance |
| `ASSERTION_CONTEXT_MISMATCH`  | Presented for a different voting context               |
| `ASSERTION_ALREADY_USED`      | The nonce is in the spent set                          |
| `ASSERTION_REVOKED`           | Revoked before presentation                            |

## 3. Credential

| Code                                  | Meaning                                                 |
| ------------------------------------- | ------------------------------------------------------- |
| `CREDENTIAL_ISSUED`                   | A credential was issued                                 |
| `CREDENTIAL_DUPLICATE_REQUEST`        | A duplicate request was detected and refused            |
| `CREDENTIAL_ALREADY_ISSUED`           | This participation unit already holds a credential      |
| `CREDENTIAL_REVOKED`                  | Withdrawn before redemption                             |
| `CREDENTIAL_EXPIRED`                  | Validity elapsed unused                                 |
| `CREDENTIAL_ALREADY_REDEEMED`         | Already consumed                                        |
| `CREDENTIAL_REPLAY_DETECTED`          | A further presentation of a spent credential            |
| `CREDENTIAL_CONTEXT_MISMATCH`         | Presented in a different context                        |
| `CREDENTIAL_AUDIENCE_MISMATCH`        | Presented at an origin it was not issued for            |
| `CREDENTIAL_ISSUANCE_WINDOW_CLOSED`   | Outside the issuance window                             |
| `CREDENTIAL_REDEMPTION_WINDOW_CLOSED` | Outside the redemption window                           |
| `CREDENTIAL_REVOCATION_CUTOFF_PASSED` | A revocation was requested after the cutoff and refused |

## 4. Handoff

| Code                        | Meaning                                      |
| --------------------------- | -------------------------------------------- |
| `HANDOFF_INVALID`           | The artifact did not verify                  |
| `HANDOFF_EXPIRED`           | Past its expiry at presentation              |
| `HANDOFF_ALREADY_USED`      | A second presentation                        |
| `HANDOFF_AUDIENCE_MISMATCH` | Presented to the wrong audience              |
| `HANDOFF_ORIGIN_MISMATCH`   | Presented from an origin it was not bound to |

PACK-14's `VOTING_HANDOFF_ALREADY_USED` and
`CROSS_WORKSPACE_HANDOFF_INVALID` remain the identity-side codes and are
**not renamed**; the family above is the PACK-15 inbound side of the same
boundary.

## 5. Voting context

| Code                                   | Meaning                                                  |
| -------------------------------------- | -------------------------------------------------------- |
| `VOTING_CONTEXT_NOT_ACTIVE`            | The context is not in a state that permits this act      |
| `VOTING_CONTEXT_SCOPE_MISMATCH`        | The organizational scope does not match                  |
| `VOTING_CONTEXT_CONFIGURATION_INVALID` | The context's configuration is not internally consistent |
| `VOTING_CONTEXT_SUSPENDED`             | Suspended; issuance and redemption are stopped           |
| `VOTING_CONTEXT_CANCELLED`             | Terminally cancelled                                     |

## 6. Governance, review and system

| Code                            | Meaning                                                              |
| ------------------------------- | -------------------------------------------------------------------- |
| `MANUAL_REVIEW_REQUIRED`        | A human decision is required before proceeding                       |
| `DUAL_CONTROL_REQUIRED`         | A second authorized approver is required                             |
| `PRIVILEGED_APPROVAL_MISSING`   | A required PACK-12 grant is absent or expired                        |
| `DISPUTE_OPEN`                  | A dispute is open against this artifact                              |
| `DISPUTE_RESOLVED`              | A dispute was resolved                                               |
| `SYSTEM_DEPENDENCY_UNAVAILABLE` | A required dependency was unreachable; the act failed closed         |
| `AUDIT_UNAVAILABLE`             | The audit stream was unreachable; no consequential act was performed |
| `SEPARATION_OF_DUTIES_REFUSED`  | The actor's role combination is prohibited                           |
| `INTERMEDIATE_TALLY_REFUSED`    | A request would have disclosed outcome-bearing data before closure   |
| `DISCLOSURE_CONTROL_SUPPRESSED` | An aggregate was suppressed below the threshold                      |

---

## 7. Codes that must not exist

| Proposed code       | Why it is refused                                                             |
| ------------------- | ----------------------------------------------------------------------------- |
| `VOTING_ERROR`      | The generic code this catalog exists to prevent                               |
| `ELIGIBILITY_ERROR` | Same, one level down                                                          |
| `CREDENTIAL_ERROR`  | Same                                                                          |
| `NOT_ALLOWED`       | Names no reason and no next step                                              |
| `INTERNAL_ERROR`    | Acceptable as a transport status; never as a participant-facing reason        |
| `ALREADY_VOTED`     | A person-level participation statement; the system must not be able to say it |
| `INELIGIBLE`        | Too coarse: eleven distinct eligibility outcomes differ in the remedy         |

`ALREADY_VOTED` deserves its own note. It will be proposed, it reads as
helpful, and it is the one code in this table whose existence would prove
the architecture had failed — because to emit it, some component would have
to know that this participant's credential was redeemed and a ballot cast.
The nearest permissible codes are `CREDENTIAL_ALREADY_ISSUED` (identity
side, about issuance) and `CREDENTIAL_ALREADY_REDEEMED` (voting side, about
a credential the presenter is holding). Neither says a person voted.

---

## 8. Reason-code obligations

| Obligation                                                       | Stage          |
| ---------------------------------------------------------------- | -------------- |
| Every refusal carries exactly one primary registered code        | Implementation |
| Every code maps to a governed German text with a next step       | Implementation |
| No code is reused with a changed meaning                         | Always         |
| Codes are taxonomy candidates for `FIR-REF-001`                  | Deferred       |
| The catalogue is data, not prose, so a test can assert over it   | Implementation |
| No participant-facing code discloses another participant's state | Always         |

---

## 9. Codes added by the architecture correction (2026-07-31)

### 9.1 Assertion queue and pickup

| Code                            | Meaning                                                                              | Next step for the participant      |
| ------------------------------- | ------------------------------------------------------------------------------------ | ---------------------------------- |
| `ASSERTION_QUEUED`              | Access has been prepared and is waiting for its release schedule                     | Wait; a notification follows       |
| `ASSERTION_RELEASE_PENDING`     | The release schedule has not yet elapsed                                             | Wait                               |
| `ASSERTION_PICKUP_PENDING`      | Released, not yet collected                                                          | Enter the voting area              |
| `ASSERTION_PICKUP_ALREADY_USED` | The one-time pickup has been consumed                                                | Report the problem (`F-P15-05`)    |
| `ASSERTION_PICKUP_EXPIRED`      | The pickup was not collected in time                                                 | Report the problem                 |
| `COHORT_THRESHOLD_NOT_MET`      | Released below the minimum cohort after the maximum wait — recorded, never a refusal | none; informational to the auditor |

### 9.2 Credential delivery

| Code                         | Meaning                                                                       |
| ---------------------------- | ----------------------------------------------------------------------------- |
| `CREDENTIAL_MINTING_DELAYED` | The randomized minting delay is in progress — a progress state, not a failure |
| `DELIVERY_CHANNEL_REFUSED`   | A delivery outside the isolated voting origin was attempted and refused       |
| `CREDENTIAL_ORIGIN_REFUSED`  | The issuance or redemption request did not originate from the voting origin   |

### 9.3 Evidence bundle

| Code                                 | Meaning                                                         |
| ------------------------------------ | --------------------------------------------------------------- |
| `EVIDENCE_BUNDLE_INVALID`            | A validation check failed; the bundle is rejected, not repaired |
| `EVIDENCE_BUNDLE_SUPPRESSED`         | A section or cell was suppressed by disclosure control          |
| `EVIDENCE_BUNDLE_SCOPE_REFUSED`      | The export named two contexts, or requested raw stream content  |
| `EVIDENCE_BUNDLE_PRECLOSURE_REFUSED` | An outcome-bearing section was requested before `voting_closed` |

### 9.4 Configuration

| Code                                    | Meaning                                                                                                               |
| --------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| `TIMING_PROFILE_OUT_OF_BOUNDS`          | A configured value is outside its permitted range or below its hard lower bound — **refused, never clamped silently** |
| `ISSUANCE_WINDOW_GUARANTEE_UNSATISFIED` | The profile cannot guarantee release before the issuance window closes                                                |

### 9.5 Codes that must still not exist

`VOTING_ERROR`, `ELIGIBILITY_ERROR`, `CREDENTIAL_ERROR`, `NOT_ALLOWED`,
`INELIGIBLE` and **`ALREADY_VOTED`** remain refused for the reasons in §7.
The correction adds one: **`PARTICIPATION_CONFIRMED`** — a code whose
existence would be a person-level participation statement, and which is
therefore prohibited in the same way and for the same reason.
