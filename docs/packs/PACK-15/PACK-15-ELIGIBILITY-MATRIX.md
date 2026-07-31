# PACK-15 — Eligibility Matrix

**Round:** PACK-15 — specification and ADR only. **No code. Not implemented. Not a candidate. Not a PASS.**
**Repository version:** unchanged at `0.14.0` · **Canon version:** unchanged at `0.8.0`
**Baseline:** `EPD2_PACK-14_IDENTITY_AUTHENTICATION_ACCOUNT_SECURITY_0.14.0_FINAL_PASS.zip`
**Authoritative register:** `EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER_UPDATED_V6.md`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**
**Architecture correction applied (2026-07-31).**

Every eligibility criterion, the **minimized input** it is permitted to
receive, the owner of the authoritative source, its staleness rule, its
reason code on failure, and whether it can be evaluated mechanically.

The column that matters most is **minimized input**. In most rows it is a
boolean predicate evaluated *at the source*, not a value delivered to the
Eligibility Service. `age_threshold_met = true` leaks one bit;
`date_of_birth = 1974-03-11` leaks a quasi-identifier that outlives the
vote in every log it touches. `PACK-15-ATTRIBUTE-MINIMIZATION-MATRIX.md`
states the same boundary from the data side and is normative alongside
this document.

---

## 1. Criteria

| ID       | Criterion                     | Minimized input permitted                                                            | Authoritative source owner        | Staleness rule                              | Failure reason code                     | Mechanical? |
| -------- | ----------------------------- | ------------------------------------------------------------------------------------ | --------------------------------- | ------------------------------------------- | --------------------------------------- | ----------- |
| `EC-01`  | Membership status             | `membership_active` (boolean, evaluated at source)                                   | `membership-service`              | Must be ≤ context freshness bound           | `ELIGIBILITY_MEMBERSHIP_INACTIVE`       | yes         |
| `EC-02`  | Membership start date         | `membership_duration_requirement_met` (boolean)                                       | `membership-service`              | Re-evaluated at decision time               | `ELIGIBILITY_RULE_NOT_SATISFIED`        | yes         |
| `EC-03`  | Organizational level          | `organizational_level_class` (enum, from the context's own taxonomy)                  | `organization-service`            | Re-evaluated at decision time               | `ELIGIBILITY_SCOPE_MISMATCH`            | yes         |
| `EC-04`  | Bund / Land / Kreis scope     | `scope_reference` (the context's scope, matched at source)                            | `organization-service`            | Re-evaluated at decision time               | `ELIGIBILITY_SCOPE_MISMATCH`            | yes         |
| `EC-05`  | Role                          | `required_role_held` (boolean, per the rule-set's named role class)                   | `governance-service` (`RoleAssignment`) | Re-evaluated at decision time         | `ELIGIBILITY_RULE_NOT_SATISFIED`        | yes         |
| `EC-06`  | Age threshold                 | `age_threshold_met` (boolean) — **never a date of birth**                             | `membership-service` / proofing   | Re-evaluated at decision time               | `ELIGIBILITY_RULE_NOT_SATISFIED`        | yes         |
| `EC-07`  | Suspension / restriction      | `participation_restricted` (boolean) + restriction class                              | `membership-service`              | **Fail-closed if unresolvable**             | `ELIGIBILITY_RULE_NOT_SATISFIED`        | yes         |
| `EC-08`  | Participation class           | `participation_class` (enum)                                                          | `eligibility-service` (canon 19d) | Re-evaluated at decision time               | `ELIGIBILITY_RULE_NOT_SATISFIED`        | yes         |
| `EC-09`  | Conflict of interest          | `conflict_declared` (boolean) + declaration reference                                 | Election administration            | Per context; may require review             | `ELIGIBILITY_REVIEW_REQUIRED`           | partly      |
| `EC-10`  | Candidacy status              | `is_candidate_in_context` (boolean)                                                   | `initiative-service` / nomination  | Re-evaluated at decision time               | `ELIGIBILITY_RULE_NOT_SATISFIED`        | yes         |
| `EC-11`  | Voting window                 | The context's own window vs. evaluation time                                          | VC-01 Voting Context Registry      | Evaluated at request and at issuance        | `VOTING_CONTEXT_NOT_ACTIVE`             | yes         |
| `EC-12`  | Assurance level               | `required_assurance_satisfied` (boolean, asserted by `identity-service`)               | `identity-service` (PACK-14)      | Bound to the context's freshness window     | `ELIGIBILITY_ASSURANCE_INSUFFICIENT`    | yes         |
| `EC-13`  | Manual exception              | Decision reference + reason code                                                      | Eligibility Reviewer               | Single-context, single-use                  | `MANUAL_REVIEW_REQUIRED`                | no          |
| `EC-14`  | Governed legal / statutory rule | Rule-set reference + evaluation outcome                                             | Governed rules registry (`FIR-RULE-001`) | Rule-set version frozen              | `ELIGIBILITY_RULE_NOT_SATISFIED`        | depends     |

**`EC-06` is the row to defend in review.** Every implementation will be
tempted to fetch a date of birth "because we already have it and the
predicate is trivial". The predicate must be evaluated at the source and
only its result delivered — otherwise the eligibility case, its audit
record, its backup and its export all carry a date of birth that the vote
never needed.

---

## 2. Rule-set versioning and freeze

| Rule                                                                                                                  | Consequence                                                                       |
| --------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| A rule-set version is **immutable** (canon 9.1's freeze, extended from `EligibilityRule` to the set)                   | Re-submitting the same version with different content is refused                  |
| A `VotingContext` references a **rule-set version**, never a rule-set                                                  | A rule change cannot silently alter a running vote                                |
| A decision names the rule-set version it was evaluated against                                                        | A later version does not retroactively change a decision                          |
| Changing a context's rule-set version after `issuance_open` is **prohibited**                                          | Refused with `VOTING_CONTEXT_CONFIGURATION_INVALID`                               |
| A rule-set version's criteria set is closed at freeze                                                                 | A criterion cannot be added mid-vote to exclude someone                           |
| Rule-set authorship and approval are separated                                                                        | The author of a rule-set does not approve it (separation-of-duties matrix, `SD-04`) |

---

## 3. Decision statuses and their transitions

| From             | To                | Trigger                                                  | Who                   | Evidence                    |
| ---------------- | ----------------- | -------------------------------------------------------- | --------------------- | --------------------------- |
| —                | `requested`       | Participant or assisted channel submits a request        | Participant / helper  | Request record              |
| `requested`      | `evaluating`      | Evaluation starts                                        | Eligibility Service   | Evaluation start event      |
| `evaluating`     | `approved`        | All criteria satisfied                                   | Eligibility Service   | Decision + reason codes     |
| `evaluating`     | `denied`          | A criterion not satisfied                                | Eligibility Service   | Decision + reason codes     |
| `evaluating`     | `review_required` | A criterion needs a human                                | Eligibility Service   | Review case opened          |
| `review_required`| `under_review`    | A reviewer takes the case                                | Eligibility Reviewer  | Assignment record           |
| `under_review`   | `approved`/`denied` | Reviewer decides                                       | Eligibility Reviewer  | Decision + reason + reviewer|
| `approved`       | `superseded`      | A source fact changed **before** assertion issuance      | Eligibility Service   | Supersession event          |
| any              | `expired`         | Validity window elapsed                                  | Eligibility Service   | Expiry event                |
| any              | `disputed`        | Dispute opened                                           | Participant           | Dispute case                |
| `requested`      | `withdrawn`       | Participant withdraws before decision                    | Participant           | Withdrawal record           |

**`approved` → `superseded` is impossible after an assertion has been
issued.** From that moment invalidation acts on the assertion, not on the
decision — otherwise the decision store would need to know that an
assertion exists *and which one*, which is the pairing this architecture
forbids. What the decision store may know is a single boolean: an
assertion has been issued for this participation unit. Not which.

---

## 4. Validity

| Property                        | Rule                                                                                            |
| ------------------------------- | ----------------------------------------------------------------------------------------------- |
| Context binding                 | One `VotingContextId`. A decision is worthless in any other context                             |
| Validity window                 | Explicit, bounded by the context's credential issuance window                                   |
| Maximum validity                | Never beyond `CredentialIssuanceWindow.end`                                                     |
| Freshness of inputs             | Each criterion carries its own freshness bound; the strictest governs                           |
| Re-evaluation trigger           | Any source change affecting a criterion the decision relied on                                  |
| Expiry behaviour                | `ELIGIBILITY_DECISION_EXPIRED`; a new request is required, and is not automatic                 |

---

## 5. Manual review

| Trigger                                            | Reviewer role        | Permitted evidence            | Prohibited                                     |
| -------------------------------------------------- | -------------------- | ----------------------------- | ---------------------------------------------- |
| Incomplete evidence                                | Eligibility Reviewer | PACK-11 references            | Evidence content in the case record            |
| Conflicting sources                                | Eligibility Reviewer | Both source attestations      | Fetching a full member record to "check"       |
| Stale source inside the window                     | Eligibility Reviewer | Freshness metadata            | Overriding staleness without a reason code     |
| Conflict of interest                               | Eligibility Reviewer | Declaration reference         | Deciding one's own case                        |
| Manual exception request                           | Eligibility Reviewer | Request + governed basis      | An exception without a named basis             |
| Governed rule requiring a human                    | Eligibility Reviewer | Rule-set reference            | Mechanical approval                            |

Binding rules: no reviewer decides a case they raised or are the subject of
(`ELIGIBILITY_SELF_REVIEW_REFUSED`); every decision carries a registered
reason code and no free text as the reason; **an unavailable reviewer never
yields an automatic approval or an automatic denial** — the case waits, is
escalated, and the participant is told it is waiting.

---

## 6. Evidence references

| Rule                                                                       | Reason                                                                  |
| -------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| Evidence is a PACK-11 governed document reference, never inline content    | Evidence needs custody, versioning and retention a field does not have  |
| Events and logs carry the reference, never the content                     | Audit minimization                                                      |
| Evidence is readable only within its own eligibility case                  | Least privilege                                                         |
| A denied case's evidence is retained per schedule, not deleted on denial   | A denial may be disputed; destroyed evidence cannot answer the dispute  |
| Evidence never crosses the trust boundary                                  | The voting side has no reason to hold it and no right to see it         |

---

## 7. What eligibility must never do

| Prohibition                                                                    | Why                                                        |
| ------------------------------------------------------------------------------ | ---------------------------------------------------------- |
| Create, activate or alter a `Membership`                                       | Canon 19d.9's two-stage admission; `eligibility-service` never writes membership |
| Serve as authentication                                                        | `ELIGIBILITY != AUTHENTICATION`                             |
| Serve as a voting credential                                                   | `ELIGIBILITY != VOTING CREDENTIAL`                          |
| Hold, reference or resolve a credential                                        | The pairing prohibition (specification §3)                  |
| Read anything owned by `voting-service` or `tally-service`                     | Canon already forbids the edge; PACK-15 does not add one    |
| Be read as an authorization mechanism via `ParticipationRightsProfile`         | Canon 19d.13/19d.14 — that model never authorizes an action |
| Produce a decision without a reason code                                       | An unexplainable decision is not contestable                |
