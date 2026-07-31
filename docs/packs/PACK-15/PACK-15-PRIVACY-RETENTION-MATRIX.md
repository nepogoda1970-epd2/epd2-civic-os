# PACK-15 — Privacy and Retention Matrix

**Round:** PACK-15 — specification and ADR only. **No code. Not implemented. Not a candidate. Not a PASS.**
**Repository version:** unchanged at `0.14.0` · **Canon version:** unchanged at `0.8.0`
**Baseline:** `EPD2_PACK-14_IDENTITY_AUTHENTICATION_ACCOUNT_SECURITY_0.14.0_FINAL_PASS.zip`
**Authoritative register:** `EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER_UPDATED_V6.md`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**
**Architecture correction applied (2026-07-31).**

Required by `FIR-FORM-002`. **Retention periods are not set by this
round** — PACK-09 owns schedules and a period is a legal determination
(`OD-P15-06`). What this round fixes is the **class** each artifact belongs
to, the constraint its schedule must respect, and the deletion obligation
that follows.

---

## 1. Per-artifact classes

| Artifact                        | Class                | Contains identity?             | Retention driver                            | Deletion obligation                                                                                                                  | Legal hold                 |
| ------------------------------- | -------------------- | ------------------------------ | ------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ | -------------------------- |
| Voting context configuration    | Governance record    | no                             | Governance and audit                        | Long; it is the record of what the rules were                                                                                        | applicable                 |
| Eligibility case                | Eligibility case     | **yes**                        | Dispute and appeal windows                  | Deleted or minimized after the dispute window unless held                                                                            | applicable                 |
| Eligibility decision            | Eligibility decision | **yes**                        | Dispute, appeal, audit                      | Same                                                                                                                                 | applicable                 |
| Source-data snapshot reference  | Evidence reference   | indirect                       | Reproducibility of the decision             | Reference retained; the source's own retention governs the content                                                                   | applicable                 |
| Eligibility evidence (PACK-11)  | Governed document    | **yes**                        | Dispute and appeal                          | PACK-11's schedule; not deleted on denial                                                                                            | applicable                 |
| Participation-unit ledger entry | Duplicate-prevention | **yes** (identity side)        | The issuance window plus the dispute margin | **Reduced to a context-scoped flag** after the margin                                                                                | applicable                 |
| Eligibility assertion record    | Assertion issuance   | **yes** (identity side)        | Issuance window plus dispute margin         | **Reduced to counts** after the margin — a deliberate privacy control                                                                | applicable                 |
| Ephemeral context pseudonym     | Ephemeral            | pseudonymous                   | The context's own need                      | **Deleted or made irreversible at the context boundary; the derivation secret is destroyed with it, and the destruction is audited** | **not extendable by hold** |
| Spent-nonce set                 | Replay prevention    | no                             | The issuance window                         | Deleted at the context's close; it protects nothing afterwards                                                                       | applicable                 |
| Credential issuance record      | Credential evidence  | no                             | Context plus audit margin                   | Reduced to counts after the audit margin                                                                                             | applicable                 |
| Redemption record               | Redemption evidence  | no                             | Context plus audit margin                   | Reduced to counts after the audit margin                                                                                             | applicable                 |
| Replay-detection record         | Integrity evidence   | no                             | Investigation window                        | Long; contains no identity                                                                                                           | applicable                 |
| Dispute case                    | Dispute record       | **yes**                        | Legal and governance requirements           | Per schedule                                                                                                                         | applicable                 |
| Assisted-action receipt         | Assistance evidence  | **yes** (helper + participant) | Dispute and oversight                       | Per schedule                                                                                                                         | applicable                 |
| Auditor evidence bundle         | Auditor evidence     | no                             | Governance and legal requirements           | Long; bundles are the durable artifact                                                                                               | applicable                 |
| Operational metrics             | Metrics              | no                             | Operations                                  | Short; aggregated; never per-participant                                                                                             | not typically              |
| Notification delivery records   | Delivery evidence    | **yes**                        | `FIR-DELIVERY-001`                          | That entry's own round                                                                                                               | applicable                 |

**The ephemeral pseudonym row is the only one where a legal hold does not
extend retention.** A hold that preserved a live derivation secret would
preserve a cross-context correlation capability, which is precisely what
the pseudonym's design forbids; where evidence is genuinely needed, it is
the _decision_ and the _case_ that are held, not the derivation secret.
This exception must be reviewed by counsel at the implementation round and
is recorded here rather than assumed.

---

## 2. Constraints every schedule must respect

| Constraint                                                               | Why                                                                                                                                |
| ------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------- |
| No long-term cross-context correlation                                   | A long-retained identity-side artifact narrows the field for a future compromise                                                   |
| No destruction of evidence a dispute or audit requires                   | A destroyed record cannot answer a contested election                                                                              |
| No violation of a legal hold                                             | PACK-09 and PACK-13 own the hold mechanism                                                                                         |
| **No hidden person-to-ballot linkage**                                   | A backup, archive or long-retained log preserving a pairing the live system refuses to hold is the same failure with a delay on it |
| Reduction to counts is preferred over deletion where audit needs numbers | Keeps the audit answerable while removing the individual record                                                                    |
| Deletion is verifiable                                                   | A deletion nobody can demonstrate is a policy, not a control                                                                       |

---

## 3. Backups, replicas and archives

| Rule                                                                             | Reason                                                     |
| -------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| No backup archive contains both identity-side and voting-side stores             | The join at rest                                           |
| No restore target holds both                                                     | The join after recovery                                    |
| Backup retention does not exceed the artifact's own retention class              | Otherwise the schedule is fiction                          |
| Restores are audited and, during an open context, notify the Independent Auditor | A restore is a privileged act at the worst possible moment |
| Archive exports follow the one-stream rule                                       | Audit separation matrix §3                                 |

---

## 4. Participant rights

| Right                                | How it is honoured                                                                      | Limit                                                                                     |
| ------------------------------------ | --------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| Information about processing         | Governed German texts state what is collected, why, and what is deliberately not linked | —                                                                                         |
| Access to their own eligibility case | The case, its decision, its reason codes and its evidence references                    | Not another participant's case                                                            |
| Access to their credential status    | Only against a reference they hold                                                      | **No search; no oracle**                                                                  |
| Correction                           | Through the dispute path                                                                | Correction of source facts happens at the source                                          |
| Objection to a decision              | Through `F-P15-03` / `F-P15-06`                                                         | Not after the remedy window, except at context level                                      |
| **Access to "how I voted"**          | **Not available, and cannot be made available**                                         | The link does not exist; this is stated plainly rather than presented as a policy refusal |
| Erasure                              | Applied to the eligibility case per schedule                                            | Not applied to voting-side records, which contain no personal data to erase               |

The last two rows deserve care in implementation: a data-subject request
asking for "everything you hold about my participation" is answered with
the identity-side artifacts, and the answer explains that the voting-side
records contain no personal data **and cannot be attributed to the
requester even by the organization**. That is a true statement about this
architecture, and it is the kind of statement that must be true rather than
merely written.

---

## 5. Deletion obligations that are also security controls

| Deletion                                   | Why it is a control, not housekeeping                                               |
| ------------------------------------------ | ----------------------------------------------------------------------------------- |
| Assertion issuance records → counts        | Removes the last identity-side artifact that could narrow a field                   |
| Participation-unit ledger → flag           | Keeps duplicate prevention while dropping the per-context detail                    |
| Ephemeral pseudonym and its secret         | Ends the only cross-request correlation capability that ever existed                |
| Spent-nonce set at context close           | Protects nothing afterwards; retains a set of one-time values that need not persist |
| Idempotency cache entries after the window | Prevents the cache from becoming the durable assertion→credential map               |

Each of these has a defined moment, a responsible component and an audited
act. **A deletion without evidence that it happened is not one of this
round's controls.**

---

## 6. Artifacts added by the architecture correction (2026-07-31)

| Artifact                           | Class              | Contains identity?      | Retention driver                        | Deletion obligation                                                                              | Legal hold                 |
| ---------------------------------- | ------------------ | ----------------------- | --------------------------------------- | ------------------------------------------------------------------------------------------------ | -------------------------- |
| Assertion queue entry              | Assertion issuance | **yes** (identity side) | Until release, plus a short margin      | Deleted at release; the fact of release is retained as a count                                   | applicable                 |
| Batch and cohort record            | Integrity evidence | no                      | Integrity investigation window          | Retained as **class distributions**, never as sizes or membership                                | applicable                 |
| One-time pickup record             | Assertion issuance | **yes** (identity side) | Consumed at pickup, plus dispute margin | **Reduced to a fact** after the margin                                                           | applicable                 |
| Idempotency cache entry (issuance) | Transient          | no                      | The bounded retry window only           | **Discarded at the end of the window** — it must never become a durable assertion→credential map | **not extendable by hold** |
| Credential material                | —                  | no                      | —                                       | **Never persisted anywhere.** It exists only in WS-03 page memory during one visit               | n/a                        |
| `IssuanceTimingProfile` record     | Governance record  | no                      | Governance and audit                    | Long; it is the record of what the controls were                                                 | applicable                 |
| Evidence bundle                    | Auditor evidence   | no                      | Governance and legal requirements       | Long; bundles are the durable audit artifact                                                     | applicable                 |
| Bundle export authorization record | Privileged action  | operator identity       | Oversight                               | Per schedule                                                                                     | applicable                 |

**Two rows carry a hold exception, and both are deliberate.** The
context-scoped pseudonym's derivation secret (§1) and the issuance
idempotency cache entry must be destroyed on schedule even under a legal
hold, because each is a live correlation capability rather than a record: a
preserved secret and a preserved assertion→credential mapping are exactly
the artifacts this architecture declines to hold. Where evidence is
genuinely required, it is the **decision** and the **case** that are held.
Both exceptions must be reviewed by counsel at the implementation round and
are recorded here rather than assumed.

## 7. Deletion obligations that are also security controls — additions

| Deletion                                | Why it is a control                                                      |
| --------------------------------------- | ------------------------------------------------------------------------ |
| Assertion queue entry at release        | The queue is the only place holding "this participant is about to cross" |
| Pickup record → a fact after the margin | Removes the last identity-side handle on the crossing                    |
| Idempotency cache at window end         | Prevents the cache from becoming the map ADR-093 forbids                 |
| Batch records → class distributions     | An exact cohort size in a small electorate is a participation statement  |
