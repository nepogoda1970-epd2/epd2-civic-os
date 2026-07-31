# PACK-15 — Separation of Duties Matrix

### Election Administration Separation Matrix (`FIR-ROLE-005`) for the voting trust boundary

**Round:** PACK-15 — specification and ADR only. **No code. Not implemented. Not a candidate. Not a PASS.**
**Repository version:** unchanged at `0.14.0` · **Canon version:** unchanged at `0.8.0`
**Baseline:** `EPD2_PACK-14_IDENTITY_AUTHENTICATION_ACCOUNT_SECURITY_0.14.0_FINAL_PASS.zip`
**Authoritative register:** `EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER_UPDATED_V6.md`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**
**Architecture correction applied (2026-07-31).**

`FIR-ROLE-005` requires a matrix of incompatible and separated election
roles. This is that matrix for the eligibility and credential boundary.
`FIR-ROLE-002` (election board / election officer) and `FIR-ROLE-003`
(independent auditor) are the register entries these roles serve, and
neither is marked implemented by this round.

---

## 1. Roles

| ID      | Role                       | Authority                                                          | Data horizon                                  |
| ------- | -------------------------- | ------------------------------------------------------------------ | --------------------------------------------- |
| `R-01`  | Membership Authority       | Maintain membership facts                                          | Membership domain only                        |
| `R-02`  | Eligibility Officer        | Configure and operate eligibility evaluation                       | Eligibility cases; rule-sets                  |
| `R-03`  | Eligibility Reviewer       | Decide manual-review cases                                         | The case in front of them                     |
| `R-04`  | Credential Issuer          | Issue, revoke, mark redeemed                                       | Credentials and their status                  |
| `R-05`  | Voting Operations Officer  | Operate contexts and windows                                       | Context configuration and health              |
| `R-06`  | Voting Client Operator     | Operate WS-03                                                      | The client's own operation                    |
| `R-07`  | Tally Authority            | Perform the official tally (PACK-16)                               | Ballots and results, after closure            |
| `R-08`  | Independent Auditor        | Verify integrity                                                   | Privacy-preserving evidence bundles           |
| `R-09`  | Security Auditor           | Review security and integrity evidence                             | Integrity and system streams                  |
| `R-10`  | Dispute Reviewer           | Decide eligibility and issuance disputes                           | The dispute case                              |

---

## 2. Incompatibility matrix

`✗` = must never be held by the same natural person, or by the same
service account, in the same voting context.
`△` = permitted only with dual control and a time-boxed PACK-12 grant.
`✓` = compatible.

|          | R-01 | R-02 | R-03 | R-04 | R-05 | R-06 | R-07 | R-08 | R-09 | R-10 |
| -------- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| **R-01** | —    | △    | ✗    | ✗    | ✓    | ✗    | ✗    | ✗    | ✓    | ✗    |
| **R-02** | △    | —    | ✗    | ✗    | ✗    | ✗    | ✗    | ✗    | ✓    | ✗    |
| **R-03** | ✗    | ✗    | —    | ✗    | ✗    | ✗    | ✗    | ✗    | ✓    | ✗    |
| **R-04** | ✗    | ✗    | ✗    | —    | ✗    | ✗    | ✗    | ✗    | ✓    | ✗    |
| **R-05** | ✓    | ✗    | ✗    | ✗    | —    | △    | ✗    | ✗    | ✓    | ✓    |
| **R-06** | ✗    | ✗    | ✗    | ✗    | △    | —    | ✗    | ✗    | ✓    | ✓    |
| **R-07** | ✗    | ✗    | ✗    | ✗    | ✗    | ✗    | —    | ✗    | ✓    | ✗    |
| **R-08** | ✗    | ✗    | ✗    | ✗    | ✗    | ✗    | ✗    | —    | ✓    | ✓    |
| **R-09** | ✓    | ✓    | ✓    | ✓    | ✓    | ✓    | ✓    | ✓    | —    | ✓    |
| **R-10** | ✗    | ✗    | ✗    | ✗    | ✓    | ✓    | ✗    | ✓    | ✓    | —    |

The Security Auditor (`R-09`) is compatible with everything because the
role is **read-only over integrity evidence and holds no participation
data** — it reviews whether the boundaries held, not who crossed them. If
an implementation gives `R-09` read access to a participation store, the
row above becomes false and the matrix must be rejected in review.

---

## 3. Named prohibitions

| ID      | Prohibition                                                                                          | Consequence if violated                                            |
| ------- | ---------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| `SD-01` | The Membership Authority does not issue voting credentials                                            | Membership becomes the credential authority; the separation is gone |
| `SD-02` | The Eligibility Service never sees a ballot                                                           | `ELIGIBILITY != BALLOT` fails                                       |
| `SD-03` | The Credential Issuer never sees ordinary identity                                                    | The credential becomes attributable                                 |
| `SD-04` | The author of a rule-set version does not approve it                                                  | The electorate can be defined by one person                         |
| `SD-05` | The Voting Client never receives membership data                                                      | WS-03 isolation fails                                               |
| `SD-06` | **No actor holds eligibility, issuance and tally authority in the same context**                      | The full chain is reconstructible by one person                     |
| `SD-07` | The Tally Authority never receives identity                                                           | The result becomes attributable                                     |
| `SD-08` | No reviewer decides a case they raised or are the subject of                                          | Self-approval                                                       |
| `SD-09` | Break-glass requires dual control, a time-boxed grant and a reason code (PACK-12's mechanism, reused) | Unreviewable privilege                                              |
| `SD-10` | The Independent Auditor holds no unrestricted identity correlation access                             | The auditor becomes the correlation the system prevents             |
| `SD-11` | The Dispute Reviewer cannot link a person to a ballot, by any route including a grant                 | Dispute handling becomes the back door                              |
| `SD-12` | No feature flag, emergency path or configuration may assemble a prohibited combination                | `FIR-INV-006` in this domain                                        |

---

## 4. Acts requiring dual control

| Act                                                            | Second approver must be            | Evidence                                    |
| -------------------------------------------------------------- | ---------------------------------- | ------------------------------------------- |
| Approving a rule-set version for a context                     | Not the author                     | Approval record + reason code               |
| Activating a voting context                                    | Voting Operations Officer + Governance | Activation record                       |
| Cancelling a voting context                                    | Governance                         | Cancellation record + reason code           |
| Revoking a credential inside the final window before the cutoff| A second Credential Issuer         | Revocation record + auditor notification    |
| Governed reissue after uncertain delivery                      | Eligibility Officer + Credential Issuer | Reissue record on both streams         |
| Manual eligibility exception                                   | A second Eligibility Reviewer      | Exception record + governed basis           |
| Break-glass access to any PACK-15 store                        | PACK-12's dual-control mechanism   | Privileged session evidence                 |
| Changing an audit stream's retention or authorization          | Security Auditor + Governance      | Configuration change record                 |

---

## 5. Break-glass

Break-glass reuses **PACK-12's existing mechanism unchanged** — no second
mechanism is created here. Additional constraints that apply in this
domain:

| Constraint                                                                             | Reason                                                          |
| -------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| No break-glass grant may span the eligibility side and the voting side                 | That grant *is* the link                                        |
| No break-glass grant may include ballot or tally access together with any PACK-15 store| Same                                                            |
| Grants are time-boxed and purpose-scoped                                                | PACK-12                                                          |
| Every break-glass act during an open voting context notifies the Independent Auditor    | The window in which privilege is most dangerous                 |
| Break-glass during an open context is reported in the context's own integrity evidence  | So that a contested result can be examined for it               |
| Break-glass cannot move a credential out of `redeemed`                                  | The absorbing state is absorbing for privileged actors too      |

---

## 6. Service accounts are roles too

Every prohibition above applies to service accounts, deployment identities,
CI credentials, database roles and backup operators, not only to people. A
service account that can read the assertion issuance store and the
credential store violates `SD-06` exactly as a person would, and it is the
more likely violation because nobody thinks of a backup job as holding an
election role.

The implementation round's evidence must therefore include, per store, the
list of principals that can read it — human and machine — and a
demonstration that no principal appears on both sides of the boundary.

---

## 7. Acts added by the architecture correction (2026-07-31)

| Act                                                        | Second approver must be              | Evidence                                  |
| ---------------------------------------------------------- | ------------------------------------ | ----------------------------------------- |
| Configuring or changing an `IssuanceTimingProfile`         | Governance, not the configuring officer | Configuration change record + `AS-06`  |
| Activating a context with a **small electorate**           | Governance, with an explicit acknowledgement that unlinkability is weaker | Activation record |
| Exporting an evidence bundle **before** `voting_closed`     | A second Independent Auditor or Governance | Export record on `AS-05` and `AS-06`  |
| Declaring a context-scoped pseudonym for a context          | Governance, with a written justification | Configuration record                    |
| Destroying a pseudonym derivation secret                    | Security Auditor witnesses            | Destruction record on `AS-06`             |

### 7.1 Prohibitions added

| ID      | Prohibition                                                                                          |
| ------- | ---------------------------------------------------------------------------------------------------- |
| `SD-13` | No role may disable, shorten or bypass a timing control to recover throughput — the queue is not a performance setting |
| `SD-14` | No role may deliver credential material through any channel outside the isolated voting origin       |
| `SD-15` | No role may resolve a context-scoped pseudonym to a participant, or a participant to a pseudonym     |
| `SD-16` | No role may hold a bundle export grant together with read access to any raw participation stream     |

`SD-13` … `SD-16` bind service accounts and machine principals exactly as
they bind people, per §6.
