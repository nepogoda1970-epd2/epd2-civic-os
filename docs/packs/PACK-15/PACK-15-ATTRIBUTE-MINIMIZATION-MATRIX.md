# PACK-15 — Attribute Minimization Matrix

**Round:** PACK-15 — specification and ADR only. **No code. Not implemented. Not a candidate. Not a PASS.**
**Repository version:** unchanged at `0.14.0` · **Canon version:** unchanged at `0.8.0`
**Baseline:** `EPD2_PACK-14_IDENTITY_AUTHENTICATION_ACCOUNT_SECURITY_0.14.0_FINAL_PASS.zip`
**Authoritative register:** `EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER_UPDATED_V6.md`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**
**Architecture correction applied (2026-07-31).**

What each PACK-15 component is permitted to receive, and what it must never
receive. The organizing principle: **a component receives the answer, not
the data the answer was computed from.**

---

## 1. The prohibited set — never delivered to any PACK-15 component

| Attribute                  | Why it is prohibited                                                                   |
| -------------------------- | -------------------------------------------------------------------------------------- |
| Full member record         | Nothing in eligibility needs a record; a record is a correlation surface               |
| Full address               | A quasi-identifier; scope is answered by `scope_reference`                             |
| Email                      | A real-world correlator, and a join key by temptation                                  |
| Phone                      | Same                                                                                   |
| Member number              | Printed, quotable, and therefore public in practice                                    |
| Account ID                 | `FIR-INV-001`; the global identifier this system exists without                        |
| Person record ID           | PACK-14's most sensitive identifier                                                    |
| Communication persona      | Personas exist to avoid correlation, not to create it                                  |
| Raw identity-proofing data | Held under PACK-11; never an input to eligibility evaluation                           |
| Unrelated roles            | The rule-set names the role class it needs; everything else is surplus                 |
| Unrelated restrictions     | Same                                                                                   |
| Date of birth              | A predicate suffices for every eligibility rule that mentions age                      |
| Name                       | No eligibility rule requires a name; a reviewer works from the case, not from a person |

**"Prohibited" means the attribute never arrives**, not that it arrives and
is ignored. An attribute delivered and discarded still passes through a
transport, a deserializer, a request log and, on a bad day, an error
report.

---

## 2. Per-component permitted input

| Component                       | May receive                                                                                                                     | Must never receive                                                                                |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| VC-01 Voting Context Registry   | Context configuration only                                                                                                      | Any participant attribute at all                                                                  |
| VC-02 Eligibility Service       | The scoped predicates named by the frozen rule-set version, plus scope and participation class; PACK-11 evidence **references** | Everything in §1; any credential reference; any ballot data                                       |
| VC-03 Assertion Issuer          | The eligibility decision's **result, class, scope and assurance-satisfied flag**; the context reference                         | The criteria inputs; the reason history; the evidence; everything in §1; any credential reference |
| VC-04 Credential Issuer         | The verified assertion's context, class, scope, audience, purpose, expiry and nonce                                             | Everything in §1; the eligibility decision; the assertion's issuer-side record; any ballot        |
| VC-05 Handoff Boundary          | The fact that a valid single-use artifact was redeemed for a stated context                                                     | The account that obtained it; a session; anything in §1                                           |
| VC-06 Audit Separation Boundary | Per-stream evidence, within one stream                                                                                          | A correlation key spanning streams; a unified view                                                |
| WS-03 Voting Client             | The credential and the context's public presentation                                                                            | Everything in §1; the assertion; the eligibility case; any membership fact                        |
| PACK-16 voting domain           | The redeemed continuation capability                                                                                            | Everything above                                                                                  |

---

## 3. Predicate-at-source rules

| Eligibility question     | Wrong shape (prohibited)               | Required shape                                 |
| ------------------------ | -------------------------------------- | ---------------------------------------------- |
| Is the member active?    | `membership_status: "active"` + record | `membership_active: true`                      |
| Long enough a member?    | `member_since: 2019-04-02`             | `membership_duration_requirement_met: true`    |
| Old enough?              | `date_of_birth: 1974-03-11`            | `age_threshold_met: true`                      |
| In the right Kreis?      | `address: {...}`                       | `scope_reference` matched at source → `true`   |
| Holds the required role? | `roles: [...]`                         | `required_role_held: true` for the named class |
| Restricted?              | `restrictions: [...]`                  | `participation_restricted: false`              |
| Assurance sufficient?    | The authentication method and history  | `required_assurance_satisfied: true`           |

The pattern is the same each time: the source owner already knows the
answer, and the difference between shipping the answer and shipping the
data is the difference between one bit and a dossier.

---

## 4. The adapter that enforces this

The Eligibility Service already receives membership facts as an
**attestation mapping** rather than as a record, with no import path from
`epd2_eligibility_service` to `epd2_membership_service` — this is an
existing structural property of the baseline, not an aspiration, and
PACK-15 extends it rather than inventing it.

The governed adapter must therefore:

| Requirement                                                          | Enforcement at implementation stage                                                     |
| -------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| Accept only the attribute names the frozen rule-set version declares | An attribute not in the rule-set's declared input set is a refusal, not a silent drop   |
| Return predicates, not values, wherever the rule is a predicate      | Type-level: the adapter's return type carries booleans and enums, not dates and strings |
| Carry no attribute from §1 in any field, including diagnostics       | Prohibited-key scan over the adapter's request and response types                       |
| Be scoped per request to one participation in one voting context     | No bulk retrieval, no profile fetch, no "warm the cache"                                |
| Log the **names** of attributes requested, never their values        | A request log is a data store                                                           |
| Have no import path to `voting-service` or `tally-service`           | Structural; the baseline already forbids the edge                                       |

---

## 5. What crosses the trust boundary, in full

The complete list of what the voting side ever receives about a
participation. It is short on purpose.

```text
VotingContextReference       — which vote
EligibilityResult            — approved
EligibilityClass             — which participation class
OrganizationalScope          — the context's scope, matched
RequiredAssuranceSatisfied   — a boolean
IssuedAt / ExpiresAt         — a short window
Audience / Purpose           — binding
Nonce                        — one-time, context-scoped, non-derived
```

Nothing else. Not a pseudonym, not a hash, not a "correlation id for
support", not a request ID that also appears on the identity side, not a
trace ID that spans both sides. **A shared trace identifier across this
boundary is a person-to-credential link with an observability logo on it**,
and the implementation round must break the trace at the boundary
explicitly rather than inherit propagation by default.
