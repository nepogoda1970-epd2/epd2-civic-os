# PACK-15 — Acceptance Matrix

**Round:** PACK-15 — specification and ADR only. **No code. Not implemented. Not a candidate. Not a PASS.**
**Repository version:** unchanged at `0.14.0` · **Canon version:** unchanged at `0.8.0`
**Baseline:** `EPD2_PACK-14_IDENTITY_AUTHENTICATION_ACCOUNT_SECURITY_0.14.0_FINAL_PASS.zip`
**Authoritative register:** `EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER_UPDATED_V6.md`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**
**Architecture correction applied (2026-07-31).**

**No criterion below is met by this round, and none may be.** A
specification round produces requirements, not implementations.
`PASS blocker = yes` means the implementation round MUST NOT be declared
PASS while the criterion is unmet. `Dependency` names the pack or layer
that owns the remainder where PACK-15 cannot close the criterion alone.

Total criteria: **126** before the architecture correction, **154** after it (§27). Met by this round: **0**.

---

## 1. No global ID

| ID          | Normative requirement                                                              | Rationale                                  | Responsible component | Required evidence            | Implementation-stage test                                              | PASS blocker | Dependency |
| ----------- | ---------------------------------------------------------------------------------- | ------------------------------------------ | --------------------- | ---------------------------- | ---------------------------------------------------------------------- | ------------ | ---------- |
| AC-P15-001  | No identifier in any PACK-15 artifact correlates a person across domains            | `FIR-INV-001`                              | All contexts          | Identifier inventory         | Prohibited-key scan over every PACK-15 payload and store               | yes          | —          |
| AC-P15-002  | No PACK-15 store holds `account_id`, `person_record_id`, `membership_id` or `member_number` | The four tempting keys              | VC-02 … VC-06         | Schema inventory             | Structural: the field sets do not contain them                         | yes          | —          |
| AC-P15-003  | No assertion or credential field is derivable from participant data across contexts | Derivability, not naming, is the test      | VC-03, VC-04          | Derivation analysis          | Same participant, two contexts → no equal or linkable field            | yes          | —          |
| AC-P15-004  | No cross-context persistent pseudonym exists                                        | It is a global ID in a costume             | VC-03                 | Pseudonym design record      | Cross-context derivability test                                        | yes          | —          |
| AC-P15-005  | Correlation exists only through a governed boundary with purpose, scope, owner, policy, retention and evidence | PACK-14's rule, applied here | Adapters   | Mapping register             | Every mapping carries all six properties                               | yes          | —          |

## 2. Identity minimization

| ID          | Normative requirement                                                     | Rationale                          | Responsible component | Required evidence           | Implementation-stage test                                     | PASS blocker | Dependency |
| ----------- | ------------------------------------------------------------------------- | ---------------------------------- | --------------------- | --------------------------- | ------------------------------------------------------------- | ------------ | ---------- |
| AC-P15-006  | The eligibility adapter accepts only attributes the frozen rule-set declares | Undeclared input is surplus       | VC-02                 | Declared input set          | An undeclared attribute is refused, not dropped               | yes          | —          |
| AC-P15-007  | Age is delivered as a predicate, never as a date of birth                  | One bit vs. a quasi-identifier     | VC-02 + membership     | Adapter contract            | No date of birth in any request or response                   | yes          | Membership |
| AC-P15-008  | Scope is matched at source and delivered as a match, not an address        | Same                               | VC-02 + organization   | Adapter contract            | No address field anywhere                                     | yes          | —          |
| AC-P15-009  | No full member record ever enters a PACK-15 component                      | A record is a correlation surface  | VC-02                 | Import-path analysis        | No import path from eligibility to a membership record type   | yes          | —          |
| AC-P15-010  | Attribute request logs record names, never values                          | A log is a data store              | VC-02                 | Log field inventory         | No attribute value in any log                                 | yes          | —          |

## 3. Eligibility separation

| ID          | Normative requirement                                                | Rationale                       | Responsible component | Required evidence      | Implementation-stage test                                  | PASS blocker | Dependency |
| ----------- | -------------------------------------------------------------------- | ------------------------------- | --------------------- | ---------------------- | ---------------------------------------------------------- | ------------ | ---------- |
| AC-P15-011  | Eligibility is not authentication and neither substitutes for the other | `ELIGIBILITY != AUTHENTICATION` | VC-02                 | Contract review        | An authenticated but ineligible participant is refused     | yes          | —          |
| AC-P15-012  | Eligibility never creates, activates or alters a membership          | Canon 19d.9                     | VC-02                 | Write-path analysis    | No write edge to membership from eligibility               | yes          | —          |
| AC-P15-013  | An eligibility decision is not a voting credential                    | `ELIGIBILITY != VOTING CREDENTIAL` | VC-02              | Contract review        | A decision alone grants no entry                           | yes          | —          |
| AC-P15-014  | The Eligibility Service holds no credential reference                 | The pairing prohibition          | VC-02                 | Schema inventory       | Structural absence                                         | yes          | —          |
| AC-P15-015  | The Eligibility Service has no read edge to `voting-service` or `tally-service` | Canon already forbids it | VC-02                 | Import-path analysis   | No import path; no client                                  | yes          | —          |

## 4. Membership boundary

| ID          | Normative requirement                                            | Rationale                | Responsible component | Required evidence   | Implementation-stage test                        | PASS blocker | Dependency |
| ----------- | ---------------------------------------------------------------- | ------------------------ | --------------------- | ------------------- | ------------------------------------------------ | ------------ | ---------- |
| AC-P15-016  | The Membership Authority issues no voting credential              | `SD-01`                  | Roles                 | Role inventory      | No role holds both                                | yes          | —          |
| AC-P15-017  | Membership facts arrive as attestations, never as records         | Existing baseline property | VC-02               | Adapter type        | The adapter's type carries predicates            | yes          | —          |
| AC-P15-018  | Membership data never crosses the trust boundary                  | `SD-05`                  | H-04, H-05            | Boundary inspection | No membership field in any crossing payload      | yes          | —          |

## 5. Rule-set versioning

| ID          | Normative requirement                                          | Rationale                          | Responsible component | Required evidence     | Implementation-stage test                            | PASS blocker | Dependency |
| ----------- | -------------------------------------------------------------- | ---------------------------------- | --------------------- | --------------------- | ---------------------------------------------------- | ------------ | ---------- |
| AC-P15-019  | A rule-set version is immutable                                | Canon 9.1's freeze                 | VC-02                 | Freeze test           | Re-submitting a version with new content is refused  | yes          | —          |
| AC-P15-020  | A context references a rule-set **version**                    | A rule change cannot alter a running vote | VC-01           | Configuration schema  | The field is a version reference                     | yes          | —          |
| AC-P15-021  | A decision names the rule-set version it was evaluated against | Retroactivity is prevented         | VC-02                 | Decision record       | Present on every decision                            | yes          | —          |
| AC-P15-022  | The rule-set version cannot change after `issuance_open`       | Mid-vote exclusion                 | VC-01                 | Transition guard      | The change is refused with a reason code             | yes          | —          |
| AC-P15-023  | The author of a rule-set version does not approve it           | `SD-04`                            | Governance            | Approval record       | Self-approval refused                                | yes          | —          |

## 6. Assertion minimization

| ID          | Normative requirement                                        | Rationale                | Responsible component | Required evidence | Implementation-stage test                              | PASS blocker | Dependency |
| ----------- | ------------------------------------------------------------ | ------------------------ | --------------------- | ----------------- | ------------------------------------------------------ | ------------ | ---------- |
| AC-P15-024  | The assertion carries exactly the twelve specified fields    | Minimization             | VC-03                 | Field set         | No extension, vendor claim or debug field              | yes          | —          |
| AC-P15-025  | No account, person, membership or member-number field        | Prohibited content       | VC-03                 | Field set         | Structural absence                                     | yes          | —          |
| AC-P15-026  | No email, phone, name, date of birth or address              | Same                     | VC-03                 | Field set         | Structural absence                                     | yes          | —          |
| AC-P15-027  | No communication persona                                     | Personas prevent correlation | VC-03             | Field set         | Structural absence                                     | yes          | —          |
| AC-P15-028  | No eligibility evidence and no reason history                | The voting side has no use for it | VC-03            | Field set         | Structural absence                                     | yes          | —          |
| AC-P15-029  | `EligibilityResult` carries only `approved`                  | A denial is never asserted across | VC-03            | Enum              | The enum has one value                                 | yes          | —          |
| AC-P15-030  | The nonce is random and not derived from participant data    | Derivation recreates the map | VC-03             | Generation record | Statistical and structural check                       | yes          | —          |
| AC-P15-031  | The assertion is audience-, purpose- and context-bound       | It is not a general token | VC-03                 | Binding fields    | Each mismatch is a distinct refusal code               | yes          | —          |
| AC-P15-032  | The assertion is short-lived and expiry is checked at use    | —                        | VC-04                 | Expiry check      | An expired assertion is refused                        | yes          | —          |

## 7. Credential issuance

| ID          | Normative requirement                                          | Rationale                | Responsible component | Required evidence   | Implementation-stage test                             | PASS blocker | Dependency |
| ----------- | -------------------------------------------------------------- | ------------------------ | --------------------- | ------------------- | ----------------------------------------------------- | ------------ | ---------- |
| AC-P15-033  | The credential is opaque and carries no readable structure     | —                        | VC-04                 | Format record       | No parseable claim                                    | yes          | —          |
| AC-P15-034  | The credential carries no identity field, per canon 10.1's set + assertion IDs | Existing prohibition, extended | VC-04 | Field set           | Structural absence                                    | yes          | —          |
| AC-P15-035  | Issuance requires a verified, unexpired, unspent assertion     | —                        | VC-04                 | Issuance path       | Each failure is a distinct refusal                    | yes          | —          |
| AC-P15-036  | Issuance validates the context, scope, audience and window     | —                        | VC-04                 | Validation record   | Each mismatch is a distinct refusal                   | yes          | —          |
| AC-P15-037  | Assurance is verified from the assertion's boolean             | Fail-closed              | VC-04                 | Validation record   | Unsatisfied is refused                                | yes          | —          |
| AC-P15-038  | Issuance writes evidence to `AS-03` only                       | Stream separation        | VC-04                 | Stream binding      | One stream per event                                  | yes          | —          |
| AC-P15-039  | There is no silent reissue                                     | Accountability           | VC-04                 | Reissue path        | Every reissue is a governed request with evidence     | yes          | —          |

## 8. Duplicate prevention

| ID          | Normative requirement                                              | Rationale                | Responsible component | Required evidence   | Implementation-stage test                         | PASS blocker | Dependency |
| ----------- | ------------------------------------------------------------------ | ------------------------ | --------------------- | ------------------- | ------------------------------------------------- | ------------ | ---------- |
| AC-P15-040  | One assertion per participation unit per context                   | Identity-side duplicate prevention | VC-02/VC-03 | Participation ledger | A second request is refused                       | yes          | —          |
| AC-P15-041  | One credential per assertion nonce                                 | Voting-side duplicate prevention | VC-04       | Spent-nonce set     | A spent nonce is refused                          | yes          | —          |
| AC-P15-042  | Concurrent requests on one nonce serialize to exactly one issuance | Race safety              | VC-04                 | Concurrency test    | N concurrent requests → one credential            | yes          | —          |
| AC-P15-043  | Retry with the same idempotency key returns the same outcome       | PACK-13 ADR-077          | VC-04                 | Idempotency record  | No second credential                              | yes          | —          |
| AC-P15-044  | The idempotency cache does not become a durable assertion→credential map | The pairing prohibition | VC-04              | Retention record    | The entry expires; nothing outlives the window    | yes          | —          |

## 9. Replay prevention

| ID          | Normative requirement                                    | Rationale         | Responsible component | Required evidence | Implementation-stage test                        | PASS blocker | Dependency |
| ----------- | -------------------------------------------------------- | ----------------- | --------------------- | ----------------- | ------------------------------------------------ | ------------ | ---------- |
| AC-P15-045  | Assertion nonce spending is atomic with issuance          | No window         | VC-04                 | Transaction record | A crash leaves the nonce unspent, not half-spent | yes          | —          |
| AC-P15-046  | A second assertion presentation is refused                | —                 | VC-04                 | Refusal record    | `ASSERTION_ALREADY_USED`                         | yes          | —          |
| AC-P15-047  | A second credential presentation is refused               | —                 | VC-04                 | Refusal record    | `CREDENTIAL_ALREADY_REDEEMED`                    | yes          | —          |
| AC-P15-048  | Replay records carry no identity and no holder            | —                 | VC-04                 | Field set         | Structural absence                               | yes          | —          |
| AC-P15-049  | The replay store is never bypassed on failure             | Fail-closed       | VC-04                 | Failure path      | Store unavailable → issuance refused             | yes          | —          |

## 10. Revocation

| ID          | Normative requirement                                             | Rationale                    | Responsible component | Required evidence   | Implementation-stage test                          | PASS blocker | Dependency |
| ----------- | ----------------------------------------------------------------- | ---------------------------- | --------------------- | ------------------- | -------------------------------------------------- | ------------ | ---------- |
| AC-P15-050  | Revocation is possible only before redemption and before the cutoff | The cutoff exists to bound privilege | VC-04         | Guard record        | A late revocation is refused with its own code     | yes          | —          |
| AC-P15-051  | The cutoff never exceeds the specified maximum per context type   | Bounded privilege            | VC-01                 | Configuration guard | Configuration outside the maximum is refused       | yes          | —          |
| AC-P15-052  | Late revocation requires dual control and auditor notification    | —                            | VC-04                 | Dual-control record | A single-actor late revocation is refused          | yes          | —          |
| AC-P15-053  | Revocation cannot be targeted at a named participant              | Selective disenfranchisement | VC-04                 | Interface review    | No operation accepts a participant identifier      | yes          | —          |
| AC-P15-054  | Every revocation carries a registered reason code                 | Contestability               | VC-04                 | Event payload       | No revocation without a code                       | yes          | —          |
| AC-P15-055  | Post-redemption revocation cannot find, delete, replace or link a ballot | The central guarantee  | VC-04 + PACK-16       | Interface review    | No operation exists; `redeemed` is absorbing       | yes          | PACK-16    |

## 11. Redemption

| ID          | Normative requirement                                          | Rationale         | Responsible component | Required evidence | Implementation-stage test                       | PASS blocker | Dependency |
| ----------- | -------------------------------------------------------------- | ----------------- | --------------------- | ----------------- | ----------------------------------------------- | ------------ | ---------- |
| AC-P15-056  | Redemption verifies validity, context, audience, expiry and single use | —         | VC-04                 | Validation record | Each failure is a distinct refusal              | yes          | —          |
| AC-P15-057  | Redemption marks the credential redeemed atomically            | Race safety       | VC-04                 | Transaction record | Concurrent redemption → exactly one succeeds   | yes          | —          |
| AC-P15-058  | Redemption returns no identity and no membership data          | —                 | VC-04                 | Response shape    | Structural absence                              | yes          | —          |
| AC-P15-059  | Redemption creates no reusable voting session                  | PACK-14 issued none | VC-04               | Response shape    | The capability is single-use and non-resumable  | yes          | —          |
| AC-P15-060  | The continuation capability is not the credential              | Link prevention   | VC-04 → PACK-16       | Capability format | No derivation from the credential ID            | yes          | PACK-16    |

## 12. No person-to-ballot link

| ID          | Normative requirement                                                          | Rationale               | Responsible component | Required evidence         | Implementation-stage test                                        | PASS blocker | Dependency |
| ----------- | ------------------------------------------------------------------------------ | ----------------------- | --------------------- | ------------------------- | ---------------------------------------------------------------- | ------------ | ---------- |
| AC-P15-061  | **No store, log, cache, backup or stream contains both an assertion reference and a credential reference** | ADR-093; the cut | All | Store and stream inventory | Structural: exhaustive field-pair scan across every persisted schema | yes | — |
| AC-P15-062  | The spent-nonce store is a set, not a map                                      | Same                    | VC-04                 | Schema                    | The schema has no value column that could hold a credential      | yes          | —          |
| AC-P15-063  | No credential ID is used as, or stored beside, a ballot ID                     | Canon 15.3 + this round | VC-04 + PACK-16       | Schema                    | Structural                                                       | yes          | PACK-16    |
| AC-P15-064  | No `correlation_id` chain spans the trust boundary                             | The link via telemetry  | All                   | Event inspection          | Chains terminate at the boundary                                 | yes          | —          |
| AC-P15-065  | No distributed trace propagates across the boundary                            | Same                    | All                   | Instrumentation config    | The break is explicit and tested                                 | yes          | —          |
| AC-P15-066  | No reconciliation job, report or query reads both sides                        | The runtime join        | Operations            | Principal inventory       | No principal has read access to both                             | yes          | —          |
| AC-P15-067  | No backup archive contains stores from both sides                              | The join at rest        | Operations            | Backup topology           | Separate backup domains                                          | yes          | PACK-17    |

## 13. No intermediate tally

| ID          | Normative requirement                                                 | Rationale         | Responsible component | Required evidence      | Implementation-stage test                                | PASS blocker | Dependency |
| ----------- | --------------------------------------------------------------------- | ----------------- | --------------------- | ---------------------- | -------------------------------------------------------- | ------------ | ---------- |
| AC-P15-068  | No distribution, total or partial result is disclosed before closure  | `FIR-INV-005`     | All                   | Surface inventory      | No operation returns outcome-bearing data before closure | yes          | PACK-16    |
| AC-P15-069  | No turnout figure is published before closure                         | Turnout is inferential | All              | Surface inventory      | No endpoint, metric or event carries it                  | yes          | —          |
| AC-P15-070  | No person-level participation state is exposed                        | —                 | All                   | Surface inventory      | No such field exists                                     | yes          | —          |
| AC-P15-071  | Operational metrics carry no participant dimension                    | —                 | Observability         | Metric label inventory | No participant, credential or pseudonym label            | yes          | —          |
| AC-P15-072  | Aggregates pass disclosure control and suppress small cells           | `FIR-INV-011`     | Observability         | Disclosure-control gate | Below-threshold cells are suppressed, not rounded       | yes          | PACK-12    |
| AC-P15-073  | The **set** of published signals is disclosure-controlled jointly     | Composition       | Observability         | Composition analysis   | No combination reconstructs a suppressed cell            | yes          | PACK-12    |
| AC-P15-074  | An outcome-bearing request before closure is refused and recorded     | —                 | All                   | Refusal event          | `IntermediateTallyAttemptRejected`                       | yes          | —          |

## 14. WS-03 isolation

| ID          | Normative requirement                                          | Rationale        | Responsible component | Required evidence   | Implementation-stage test                          | PASS blocker | Dependency |
| ----------- | -------------------------------------------------------------- | ---------------- | --------------------- | ------------------- | -------------------------------------------------- | ------------ | ---------- |
| AC-P15-075  | WS-03 is a separate origin with no shared cookie                | `FIR-INV-003`    | Frontend              | Origin config       | No cookie shared with any workspace                | yes          | FRONT-PACK |
| AC-P15-076  | No localStorage, sessionStorage, IndexedDB or cache is identity | Same             | Frontend              | Storage inventory   | Structural                                         | yes          | FRONT-PACK |
| AC-P15-077  | No shared service worker persists participation state           | Same             | Frontend              | Worker inventory    | Structural                                         | yes          | FRONT-PACK |
| AC-P15-078  | No shared identity session and no parent-domain session         | Same             | Frontend + PACK-14    | Session config      | PACK-14 issues none                                | yes          | —          |
| AC-P15-079  | No analytics, fingerprinting, telemetry or session replay       | Same             | Frontend              | Script inventory    | No third-party script origin at all                | yes          | FRONT-PACK |
| AC-P15-080  | No persistent member identifier, account ID or member number    | Same             | Frontend              | Payload inspection  | Structural                                         | yes          | —          |
| AC-P15-081  | No reusable cross-origin bearer token                           | Same             | PACK-14 + VC-04       | Token inspection    | Single-use, audience-bound                         | yes          | —          |

## 15. Cross-origin boundary

| ID          | Normative requirement                                     | Rationale       | Responsible component | Required evidence | Implementation-stage test                       | PASS blocker | Dependency |
| ----------- | --------------------------------------------------------- | --------------- | --------------------- | ----------------- | ----------------------------------------------- | ------------ | ---------- |
| AC-P15-082  | WS-03 declares its own CSP with `frame-ancestors 'none'`  | Clickjacking, embedding | Frontend      | CSP               | Header present and enforced                     | yes          | FRONT-PACK |
| AC-P15-083  | Redirect targets come from a fixed allow-list             | Open redirect   | Frontend + VC-05      | Allow-list        | A caller-supplied URL is refused                | yes          | FRONT-PACK |
| AC-P15-084  | `no-referrer` on entry and exit navigations               | Referrer leakage | Frontend             | Header            | Header present                                  | yes          | FRONT-PACK |
| AC-P15-085  | `no-store` on credential- and status-bearing responses    | Cache leakage   | VC-04                 | Header            | Header present                                  | yes          | —          |
| AC-P15-086  | Error reporting carries reason codes only                 | Leak via crash reports | Frontend + services | Error payloads | No identity, credential or pseudonym in a report | yes         | FRONT-PACK |

## 16. Separation of duties

| ID          | Normative requirement                                                   | Rationale        | Responsible component | Required evidence      | Implementation-stage test                       | PASS blocker | Dependency |
| ----------- | ----------------------------------------------------------------------- | ---------------- | --------------------- | ---------------------- | ----------------------------------------------- | ------------ | ---------- |
| AC-P15-087  | No actor holds eligibility, issuance and tally authority in one context | `SD-06`          | Roles                 | Role assignment audit  | The combination is refused at assignment        | yes          | —          |
| AC-P15-088  | No reviewer decides a case they raised or are the subject of            | `SD-08`          | VC-02                 | Refusal record         | `ELIGIBILITY_SELF_REVIEW_REFUSED`               | yes          | —          |
| AC-P15-089  | Break-glass requires dual control, a time-box and a reason code         | `SD-09`; PACK-12 | PACK-12               | Privileged evidence    | Reuses PACK-12; no second mechanism             | yes          | PACK-12    |
| AC-P15-090  | No break-glass grant spans both sides of the boundary                   | `SD-09`          | PACK-12               | Grant inventory        | The grant shape cannot express it               | yes          | PACK-12    |
| AC-P15-091  | Prohibitions apply to service accounts and machine principals           | §6 of the SoD matrix | Operations        | Principal inventory    | No principal on both sides                      | yes          | —          |
| AC-P15-092  | No feature flag can assemble a prohibited role combination              | `FIR-INV-006`    | Configuration         | Flag inventory         | Flags cannot alter separation                   | yes          | —          |

## 17. Audit separation

| ID          | Normative requirement                                          | Rationale       | Responsible component | Required evidence   | Implementation-stage test                     | PASS blocker | Dependency |
| ----------- | -------------------------------------------------------------- | --------------- | --------------------- | ------------------- | --------------------------------------------- | ------------ | ---------- |
| AC-P15-093  | Six streams exist, separately keyed and separately authorized  | ADR-097         | VC-06                 | Stream inventory    | Structural                                    | yes          | —          |
| AC-P15-094  | No unified audit table or index spans the chain                | Same            | VC-06                 | Sink inventory      | No sink ingests two streams                   | yes          | —          |
| AC-P15-095  | No role reads both `AS-01`/`AS-02` and `AS-03`                 | Same            | VC-06                 | Authorization matrix | Structural                                   | yes          | —          |
| AC-P15-096  | The Independent Auditor works from bundles, not raw streams    | `SD-10`         | VC-06                 | Bundle format       | No raw stream grant exists                    | yes          | `OD-P15-04` |
| AC-P15-097  | Every consequential act writes evidence to exactly one stream  | Stream discipline | All                 | Event binding       | One stream per event type                     | yes          | —          |
| AC-P15-098  | No consequential act proceeds when its audit stream is unavailable | `FM-10`     | All                   | Failure path        | Fail-closed                                   | yes          | —          |

## 18. Unlinkability

| ID          | Normative requirement                                              | Rationale       | Responsible component | Required evidence   | Implementation-stage test                     | PASS blocker | Dependency |
| ----------- | ------------------------------------------------------------------ | --------------- | --------------------- | ------------------- | --------------------------------------------- | ------------ | ---------- |
| AC-P15-099  | No component possesses enough to reconstruct the full chain        | ADR-093         | All                   | Composition analysis | Per-component data horizon documented and tested | yes       | —          |
| AC-P15-100  | Timing controls (coarsening, timing classes) are implemented       | `T-P15-13`      | VC-03, VC-04          | Timestamp policy    | No precise timestamp in crossing artifacts    | yes          | —          |
| AC-P15-101  | A minimum-cohort issuance policy exists and is configured per context | `OD-P15-02`   | VC-04                 | Policy record       | Cohort-of-one issuance is detected and handled | yes         | `OD-P15-02` |
| AC-P15-102  | `CorrelationRiskDetected` fires on shared keys, shared traces, cross-side reads and cohort-of-one | Near-miss recording | VC-06 | Detection rules | Each condition produces the event    | yes          | —          |
| AC-P15-103  | Ephemeral pseudonyms and their secrets are destroyed at the retention boundary | §10.3   | VC-03                 | Destruction record  | Destruction is audited                        | yes          | PACK-09    |

## 19. Disputes

| ID          | Normative requirement                                             | Rationale   | Responsible component | Required evidence | Implementation-stage test                    | PASS blocker | Dependency |
| ----------- | ----------------------------------------------------------------- | ----------- | --------------------- | ----------------- | -------------------------------------------- | ------------ | ---------- |
| AC-P15-104  | Every denial and refusal names a dispute path                     | ADR-098     | VC-02, VC-04          | Content catalogue | Every refusal text names a next step         | yes          | —          |
| AC-P15-105  | No appeal requires the disclosure of ballot content               | ADR-098     | VC-02                 | Case schema       | No field can hold it                         | yes          | —          |
| AC-P15-106  | The Dispute Reviewer cannot link a person to a ballot, by any route | `SD-11`   | VC-06                 | Authorization     | No grant, no search, no correlation          | yes          | —          |
| AC-P15-107  | Credential status is answerable only against a holder-supplied reference | No oracle | VC-04             | Interface review  | No search operation exists                   | yes          | —          |

## 20. Accessibility

| ID          | Normative requirement                                       | Rationale             | Responsible component | Required evidence | Implementation-stage test                  | PASS blocker | Dependency |
| ----------- | ----------------------------------------------------------- | --------------------- | --------------------- | ----------------- | ------------------------------------------ | ------------ | ---------- |
| AC-P15-108  | Every PACK-15 surface satisfies accessibility as definition of done | `FIR-INV-012` | Frontend              | Accessibility review | Per-surface conformance                  | yes          | FRONT-PACK |
| AC-P15-109  | An assisted path exists for eligibility, issuance and redemption | `FIR-INCLUSION-001` | VC-02, VC-04     | Workflow matrix   | Each assisted act is attributed            | yes          | FRONT-PACK |
| AC-P15-110  | No operator impersonation; every assisted act names the helper | Same                | VC-02, VC-04          | Receipt            | `assisted_by` mandatory in assisted paths  | yes          | —          |
| AC-P15-111  | No helper retains a credential                              | §23                   | VC-04                 | Delivery design   | Delivery is to the holder                  | yes          | `OD-P15-07` |
| AC-P15-112  | Assistance never reveals or controls a ballot choice        | §23                   | Frontend + process    | Channel design    | The helper's path ends at the boundary     | yes          | FRONT-PACK |

## 21. Forms

| ID          | Normative requirement                                    | Rationale      | Responsible component | Required evidence | Implementation-stage test               | PASS blocker | Dependency |
| ----------- | -------------------------------------------------------- | -------------- | --------------------- | ----------------- | --------------------------------------- | ------------ | ---------- |
| AC-P15-113  | All nine required forms exist with versions and receipts | `FIR-FORM-002` | Forms layer           | Form inventory    | Each has a version and a receipt        | yes          | `FIR-FORM-001` |
| AC-P15-114  | No form collects a prohibited attribute                  | §9             | Forms layer           | Field catalogue   | Field-level scan                        | yes          | —          |
| AC-P15-115  | Every form produces an immutable submission receipt      | `FIR-FORM-005` | Forms layer           | Receipt spec      | Receipt fields present                  | yes          | —          |

## 22. German content

| ID          | Normative requirement                                          | Rationale      | Responsible component | Required evidence | Implementation-stage test          | PASS blocker | Dependency |
| ----------- | -------------------------------------------------------------- | -------------- | --------------------- | ----------------- | ---------------------------------- | ------------ | ---------- |
| AC-P15-116  | Every user-facing text exists in German with owner, version and effective date | `FIR-FORM-004` | Content layer | Content catalogue | Fields present                     | yes          | —          |
| AC-P15-117  | Every refusal text names a reason, a responsible body and a next step | §22       | Content layer         | Content catalogue | Per-text check                     | yes          | —          |
| AC-P15-118  | No text confirms ballot content or a person's act of casting   | §16.1          | Content layer         | Content review    | Per-text check                     | yes          | —          |

## 23. Delivery

| ID          | Normative requirement                                    | Rationale           | Responsible component | Required evidence | Implementation-stage test        | PASS blocker | Dependency        |
| ----------- | -------------------------------------------------------- | ------------------- | --------------------- | ----------------- | -------------------------------- | ------------ | ----------------- |
| AC-P15-119  | The nine notification classes exist                      | `FIR-DELIVERY-001`  | Communications        | Class inventory   | Present                          | yes          | `FIR-DELIVERY-001` |
| AC-P15-120  | No credential secret is sent over an ordinary channel    | §24                 | Communications        | Channel rules     | Structural                       | yes          | —                 |
| AC-P15-121  | No notification states a person-level voting status      | §24                 | Communications        | Content review    | Per-message check                | yes          | —                 |

## 24. Retention

| ID          | Normative requirement                                        | Rationale      | Responsible component | Required evidence | Implementation-stage test         | PASS blocker | Dependency |
| ----------- | ------------------------------------------------------------ | -------------- | --------------------- | ----------------- | --------------------------------- | ------------ | ---------- |
| AC-P15-122  | Every artifact has a retention class and a deletion obligation | PACK-09      | All                   | Retention matrix  | Class assigned per artifact       | yes          | PACK-09    |
| AC-P15-123  | Retention permits no long-term cross-context correlation     | §21            | All                   | Retention review  | Assertion records reduce to counts | yes         | PACK-09    |

## 25. Failure modes

| ID          | Normative requirement                                      | Rationale | Responsible component | Required evidence | Implementation-stage test                | PASS blocker | Dependency |
| ----------- | ---------------------------------------------------------- | --------- | --------------------- | ----------------- | ---------------------------------------- | ------------ | ---------- |
| AC-P15-124  | Every dependency failure fails closed and fails visibly    | §27       | All                   | Failure matrix    | Each of the seventeen modes is exercised | yes          | —          |

## 26. Frontend handoff and honest status

| ID          | Normative requirement                                                       | Rationale        | Responsible component | Required evidence | Implementation-stage test               | PASS blocker | Dependency |
| ----------- | --------------------------------------------------------------------------- | ---------------- | --------------------- | ----------------- | --------------------------------------- | ------------ | ---------- |
| AC-P15-125  | The handoff UX carries no identity into WS-03 and no voting identifier back | §25              | Frontend              | Flow review       | Both directions inspected               | yes          | FRONT-PACK |
| AC-P15-126  | **No document, surface, event or claim states production readiness or legal activation** | `FIR-INV-015` | All          | Status banners    | Banner check across every artifact      | yes          | —          |

---

## Summary

| Group                              | Criteria    |
| ---------------------------------- | ----------- |
| No global ID                       | 5           |
| Identity minimization              | 5           |
| Eligibility separation             | 5           |
| Membership boundary                | 3           |
| Rule-set versioning                | 5           |
| Assertion minimization             | 9           |
| Credential issuance                | 7           |
| Duplicate prevention               | 5           |
| Replay prevention                  | 5           |
| Revocation                         | 6           |
| Redemption                         | 5           |
| No person-to-ballot link           | 7           |
| No intermediate tally              | 7           |
| WS-03 isolation                    | 7           |
| Cross-origin boundary              | 5           |
| Separation of duties               | 6           |
| Audit separation                   | 6           |
| Unlinkability                      | 5           |
| Disputes                           | 4           |
| Accessibility                      | 5           |
| Forms                              | 3           |
| German content                     | 3           |
| Delivery                           | 3           |
| Retention                          | 2           |
| Failure modes                      | 1           |
| Frontend handoff and honest status | 2           |
| **Subtotal, groups 1–26**          | **126**     |
| **Met by this round**              | **0**       |
| **PASS blockers, groups 1–26**     | **126**     |

See §27.6 for the totals after the architecture correction: **154**
criteria, **0** met, **154** PASS blockers.

---

## 27. Criteria added by the architecture correction (2026-07-31)

**Twenty-eight criteria added. Total: 154. Met by this round: 0. PASS
blockers: 154.** No criterion above is removed or weakened; each addition
follows from a closed open decision.

### 27.1 Assertion Issuer boundary — `OD-P15-01`

| ID          | Normative requirement                                                             | Rationale             | Responsible component | Required evidence      | Implementation-stage test                                     | PASS blocker | Dependency |
| ----------- | --------------------------------------------------------------------------------- | --------------------- | --------------------- | ---------------------- | ------------------------------------------------------------- | ------------ | ---------- |
| AC-P15-127  | The Assertion Issuer has its own storage boundary — no shared schema, transaction, connection pool or migration lineage with the decision store | ADR-089; ADR-091 | VC-03 | Schema and migration inventory | Structural: separate lineage; no cross-module table access | yes | — |
| AC-P15-128  | The Assertion Issuer holds a separate signing key and a separate service credential | Compromise isolation | VC-03                | Key and credential inventory | The decision store cannot read or derive the signing key | yes          | —          |
| AC-P15-129  | The Assertion Issuer **cannot** read account, person-record or membership stores  | Structural, not policy | VC-03               | Import-path and network-route analysis | No path, client, credential or route exists         | yes          | —          |
| AC-P15-130  | Its declared input is the minimized decision only                                 | Attribute minimization | VC-03               | Input type             | An undeclared field is refused, not ignored                   | yes          | —          |
| AC-P15-131  | It can be extracted to a separate deployable **without a contract change**        | `OD-P15-01`           | VC-03                 | Interface review       | Transport-agnostic; no shared transaction; audience-addressed | yes          | —          |

### 27.2 Timing-correlation controls — `OD-P15-02`

| ID          | Normative requirement                                                           | Rationale        | Responsible component | Required evidence      | Implementation-stage test                                        | PASS blocker | Dependency |
| ----------- | ------------------------------------------------------------------------------- | ---------------- | --------------------- | ---------------------- | ---------------------------------------------------------------- | ------------ | ---------- |
| AC-P15-132  | `issuance_mode` is `queued`; immediate release is not an available mode         | ADR-093          | VC-03                 | Configuration schema   | The enum has one value; no bypass path                           | yes          | —          |
| AC-P15-133  | Every timing parameter is governed configuration with a hard lower bound        | `FIR-CONFIG-001` | VC-01                 | Profile schema         | Out-of-range configuration is **refused**, never clamped         | yes          | —          |
| AC-P15-134  | Release delay is drawn uniformly from `[release_delay_min, release_delay_max]`  | Non-determinism  | VC-03                 | Scheduler design       | Statistical test over release offsets; no fixed offset           | yes          | —          |
| AC-P15-135  | A batch is released only when it holds at least `minimum_cohort_size` assertions | Cohort gate      | VC-03                 | Scheduler design       | A sub-*k* batch is held                                          | yes          | —          |
| AC-P15-136  | **A cohort of one is never minted or released immediately**                     | `T-P15-13`       | VC-03                 | Scheduler design       | Single-assertion batch waits                                     | yes          | —          |
| AC-P15-137  | At `cohort_wait_max` the assertion is released regardless, and the exception is recorded | Access is never denied | VC-03      | Release path           | `IssuanceCohortThresholdNotMet` with cohort **class**            | yes          | —          |
| AC-P15-138  | The queue guarantees release before the issuance window closes                  | No timeout disenfranchisement | VC-01/VC-03 | Window guarantee   | A profile that cannot guarantee it is refused                    | yes          | —          |
| AC-P15-139  | Timestamps on crossing artifacts and voting-side records are coarsened          | `T-P15-13`       | VC-03, VC-04          | Field inspection       | No precise timestamp anywhere on the flow                        | yes          | —          |
| AC-P15-140  | Credential minting applies a randomized delay                                   | `T-P15-13`       | VC-04                 | Minting path           | Statistical test over minting offsets                            | yes          | —          |
| AC-P15-141  | The small-electorate policy applies below the threshold and cannot be relaxed per context | `T-P15-27` | VC-01               | Configuration guard    | `k`, granularity, window and metric rules enforced               | yes          | Governance |
| AC-P15-142  | Queue metadata discloses classes, never exact cohort or queue sizes             | `T-P15-37`       | Observability         | Metric and event inspection | No exact size in any payload, metric or log                 | yes          | —          |

### 27.3 Context-scoped pseudonym — `OD-P15-03`

| ID          | Normative requirement                                                    | Rationale     | Responsible component | Required evidence  | Implementation-stage test                              | PASS blocker | Dependency |
| ----------- | ------------------------------------------------------------------------ | ------------- | --------------------- | ------------------ | ------------------------------------------------------ | ------------ | ---------- |
| AC-P15-143  | No pseudonym exists unless a context explicitly declares one             | Default none  | VC-01, VC-02          | Configuration      | Absent by default                                      | yes          | —          |
| AC-P15-144  | A pseudonym is used **only** for context-local exactly-once enforcement  | `OD-P15-03`   | VC-02                 | Usage inventory    | No other read site exists                              | yes          | —          |
| AC-P15-145  | **A pseudonym never crosses the trust boundary** in any artifact          | ADR-091       | VC-03, VC-04          | Field scan         | Absent from assertion, pickup, credential, redemption, ballot, tally and bundle | yes | — |
| AC-P15-146  | No API resolves a pseudonym to a participant or the reverse              | `OD-P15-03`   | All                   | Interface review   | No such operation exists                               | yes          | —          |
| AC-P15-147  | The pseudonym and its derivation secret are destroyed on schedule, audibly | Retention   | VC-02                 | Destruction record | Destruction is audited; a hold does not extend the secret | yes        | PACK-09    |

### 27.4 Evidence bundle — `OD-P15-04`

| ID          | Normative requirement                                                       | Rationale       | Responsible component | Required evidence    | Implementation-stage test                                 | PASS blocker | Dependency |
| ----------- | --------------------------------------------------------------------------- | --------------- | --------------------- | -------------------- | --------------------------------------------------------- | ------------ | ---------- |
| AC-P15-148  | The bundle contains only the eight permitted sections and no prohibited field | ADR-097        | VC-06                 | Bundle schema        | Structural scan; totals only, never per-participation rows | yes          | —          |
| AC-P15-149  | The bundle is versioned, signed, validated and reproducible by a second auditor | ADR-097      | VC-06                 | Validation suite     | All nine validation checks; two auditors agree             | yes          | —          |
| AC-P15-150  | Suppression is complementary, across cells **and across bundles over time**  | `T-P15-39`      | VC-06                 | Suppression metadata | Differencing two bundles recovers no suppressed cell       | yes          | PACK-12    |

### 27.5 Credential delivery — `OD-P15-07`

Covered by AC-P15-151 … AC-P15-154 below; the group is listed last because
it constrains a surface rather than a store.

| ID          | Normative requirement                                                          | Rationale   | Responsible component | Required evidence    | Implementation-stage test                                | PASS blocker | Dependency |
| ----------- | ------------------------------------------------------------------------------ | ----------- | --------------------- | -------------------- | -------------------------------------------------------- | ------------ | ---------- |
| AC-P15-151  | Credential material exists only in WS-03 page memory, for one visit            | ADR-092; ADR-096 | VC-04, Frontend  | Storage and response scan | Never persisted, displayed, copied or exported      | yes          | FRONT-PACK |
| AC-P15-152  | All ten prohibited delivery channels are structurally unavailable              | `T-P15-38`  | VC-04, Frontend       | Interface inventory  | No operation, affordance or template exists for any       | yes          | FRONT-PACK |
| AC-P15-153  | The ordinary workspace transmits only the one-time handoff artifact            | ADR-090     | Frontend, VC-05       | Payload inspection   | No assertion or credential reaches WS-02                  | yes          | FRONT-PACK |
| AC-P15-154  | No operator, helper or support role can observe credential material            | `SD-05`     | All                   | Channel review       | No screen share, log, error report or support view carries it | yes      | Process    |

**Note on numbering.** AC-P15-151 … AC-P15-154 belong to §27.5 and follow
AC-P15-150 in sequence; the group ordering above is presentational only.

### 27.6 Revised summary

| Group                                        | Criteria |
| -------------------------------------------- | -------- |
| Groups 1 … 26 (pre-correction)               | 126      |
| Assertion Issuer boundary (`OD-P15-01`)      | 5        |
| Timing-correlation controls (`OD-P15-02`)    | 11       |
| Context-scoped pseudonym (`OD-P15-03`)       | 5        |
| Evidence bundle (`OD-P15-04`)                | 3        |
| Credential delivery (`OD-P15-07`)            | 4        |
| **Total**                                    | **154**  |
| **Met by this round**                        | **0**    |
| **PASS blockers**                            | **154**  |
