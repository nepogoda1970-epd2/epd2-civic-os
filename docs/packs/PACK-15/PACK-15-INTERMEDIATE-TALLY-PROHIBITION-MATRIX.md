# PACK-15 — Intermediate Tally Prohibition Matrix

**Round:** PACK-15 — specification and ADR only. **No code. Not implemented. Not a candidate. Not a PASS.**
**Repository version:** unchanged at `0.14.0` · **Canon version:** unchanged at `0.8.0`
**Baseline:** `EPD2_PACK-14_IDENTITY_AUTHENTICATION_ACCOUNT_SECURITY_0.14.0_FINAL_PASS.zip`
**Authoritative register:** `EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER_UPDATED_V6.md`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**
**Architecture correction applied (2026-07-31).**

```text
NO INTERMEDIATE TALLY
```

`FIR-INV-005`. Before the official tally, nothing may disclose an outcome
or allow one to be inferred. The rule is easy to state and easy to violate
by accident, because the violations are almost never called tallies — they
are called dashboards, health metrics, participation rates and progress
indicators.

---

## 1. Prohibited disclosures

| ID       | Disclosure                                                    | Verdict          | Why                                                            |
| -------- | ------------------------------------------------------------- | ---------------- | -------------------------------------------------------------- |
| `IT-01`  | Distribution of votes                                         | **prohibited**   | The definition of an intermediate tally                        |
| `IT-02`  | Candidate or option totals                                    | **prohibited**   | Same                                                           |
| `IT-03`  | Partial results by any dimension                              | **prohibited**   | Same, sliced                                                   |
| `IT-04`  | Ballot content, in any form, to anyone                        | **prohibited**   | Not disclosable at any time, before or after closure           |
| `IT-05`  | Turnout for an identifiable small group                       | **prohibited**   | Near-identifying; and turnout in a small body predicts outcome |
| `IT-06`  | Person-level participation state                              | **prohibited**   | "Did X vote?" is not answerable                                |
| `IT-07`  | Participation correlated with identity                        | **prohibited**   | The central guarantee                                          |
| `IT-08`  | Redemption counts broken down by organizational scope, live   | **prohibited**   | Outcome-inferring where scopes are small or politically aligned |
| `IT-09`  | Redemption counts broken down by time, live, in a small context | **prohibited**  | Same                                                           |
| `IT-10`  | A progress bar toward a quorum, live                          | **prohibited** unless disclosure-controlled | Quorum progress is turnout, and turnout is inferential |
| `IT-11`  | "N of M eligible have voted", live                            | **prohibited**   | Turnout, stated plainly                                        |
| `IT-12`  | A leaderboard, forecast, projection or "current standing"     | **prohibited**   | An intermediate tally with a product name                      |
| `IT-13`  | Any export of voting-side data before closure                 | **prohibited**   | An export is a tally waiting to be computed                    |
| `IT-14`  | Auditor access to outcome-bearing data before closure         | **prohibited**   | The auditor verifies integrity, not results                    |
| `IT-15`  | Sampling, "spot checks" or partial verification of ballots    | **prohibited**   | A sample is a tally with error bars                            |

---

## 2. Permitted operational information

Permitted **only** subject to every control in §3.

| ID       | Signal                                       | Permitted | Conditions                                                                    |
| -------- | -------------------------------------------- | --------- | ----------------------------------------------------------------------------- |
| `OP-01`  | Service health (up / degraded / down)        | yes       | No per-scope decomposition                                                    |
| `OP-02`  | Queue depth                                  | yes       | Aggregate only; no per-scope series                                           |
| `OP-03`  | Issuance failure counts                      | yes       | Aggregate; by reason code; above the aggregation threshold                    |
| `OP-04`  | Replay-attempt counts                        | yes       | Aggregate; by reason code                                                     |
| `OP-05`  | Aggregate credential-processing counts       | **conditional** | Must pass disclosure control; suppressed below threshold; delayed where the privacy profile requires |
| `OP-06`  | Error rates by reason code                   | yes       | No participant dimension                                                      |
| `OP-07`  | Latency percentiles                          | yes       | No participant dimension                                                      |
| `OP-08`  | Integrity-violation counts                   | yes       | To the Security Auditor and the integrity stream                              |
| `OP-09`  | Late-revocation counts per context           | yes       | To the Independent Auditor; a governance signal, not an outcome signal        |

---

## 3. Controls that every permitted signal must satisfy

| Control                        | Requirement                                                                                          |
| ------------------------------ | ---------------------------------------------------------------------------------------------------- |
| Minimum aggregation threshold  | A cell below the threshold is suppressed, not rounded, and the suppression is visible                |
| No small-cell decomposition    | No combination of permitted signals may reconstruct a suppressed cell                                |
| Disclosure control             | PACK-12's mechanism (`FIR-INV-011`), reused unchanged                                                |
| Delay                          | Where the context's privacy profile requires it, publication is delayed past the inference window    |
| No participant dimension       | No metric, ever, carries a participant, a credential or a pseudonym as a label                       |
| No scope dimension below threshold | Scope labels are permitted only where the scope's eligible population exceeds the threshold      |
| Access scoping                 | Operational dashboards are visible to operations, not published                                      |
| Retention                      | Operational metrics are retained per the metrics class, not the participation class                  |

**The composition rule is the one that gets missed:** three individually
permitted metrics can jointly reveal a suppressed cell. Disclosure control
must be applied to the *set* of published signals, not to each one alone.

---

## 4. Enforcement

| Mechanism                                          | Stage                    |
| -------------------------------------------------- | ------------------------ |
| `IntermediateTallyAttemptRejected` event            | Implementation           |
| Refusal of any query returning outcome-bearing data before closure | Implementation |
| Disclosure-control gate on every published aggregate | Implementation (PACK-12 mechanism) |
| Dashboard review before a context is activated      | Governance, per context  |
| Auditor check that no outcome-bearing surface existed during the window | Independent Auditor |
| Acceptance criteria `AC-P15-068` … `AC-P15-074`     | Implementation PASS blockers |

---

## 5. What "official tally" means here

The official tally is PACK-16's act, performed by the Tally Authority after
the context reaches `voting_closed`, under its own governance. PACK-15
neither performs it nor defines it. What PACK-15 fixes is that **nothing
before it may pre-empt it** — including by accident, including for
operations, and including for people who are entitled to see the result
afterwards.

An operator who can see the outcome an hour early has the outcome an hour
early, and in a political organization that hour has value. The prohibition
is not about secrecy for its own sake; it is about removing an asymmetry
that would otherwise be worth acquiring.

---

## 6. Values and additions fixed by the architecture correction (2026-07-31)

### 6.1 The thresholds are now numbers

| Parameter                        | Value                                                        |
| -------------------------------- | ------------------------------------------------------------ |
| `disclosure_min_cell`            | **5** — a floor, not a default; never lowered per context    |
| Small-electorate threshold       | Eligible population **< 50**                                 |
| Small-electorate metrics         | **No per-scope operational metric at all** — not thresholded, not delayed |
| Small-electorate aggregate counts| Published only after `voting_closed`                          |
| Suppression method               | **Suppressed, not rounded**, and flagged                     |
| Complementary suppression        | Applied across cells **and across bundles over time**        |

### 6.2 Disclosures added to the prohibited list

| ID       | Disclosure                                                          | Verdict        | Why                                                       |
| -------- | ------------------------------------------------------------------- | -------------- | --------------------------------------------------------- |
| `IT-16`  | Queue depth or release-batch size, per scope, in a small electorate | **prohibited** | Reveals cohort structure (`T-P15-37`)                     |
| `IT-17`  | Exact cohort size in any payload, metric, log or event              | **prohibited** | Classes only; an exact size is a participation statement  |
| `IT-18`  | Queue position or estimated wait shown to a participant             | **prohibited** | Leaks cohort structure, and applies pressure              |
| `IT-19`  | Outcome-bearing evidence-bundle sections before `voting_closed`     | **prohibited** | A pre-closure count is an intermediate tally              |
| `IT-20`  | Two evidence bundles of one context differenced against each other  | **prohibited** | `T-P15-39`; prevented by complementary suppression over time |

### 6.3 Operational signals — one clarification

`OP-02` (queue depth) and `OP-05` (aggregate credential-processing counts)
remain permitted **only** in the aggregate, above the threshold, without a
scope dimension, and **not at all** in a small electorate. The issuance
queue introduced by `OD-P15-02` is a privacy control, and instrumenting it
the way one would instrument an ordinary work queue would defeat it.
