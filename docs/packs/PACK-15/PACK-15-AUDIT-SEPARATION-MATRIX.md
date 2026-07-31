# PACK-15 — Audit Separation Matrix

**Round:** PACK-15 — specification and ADR only. **No code. Not implemented. Not a candidate. Not a PASS.**
**Repository version:** unchanged at `0.14.0` · **Canon version:** unchanged at `0.8.0`
**Baseline:** `EPD2_PACK-14_IDENTITY_AUTHENTICATION_ACCOUNT_SECURITY_0.14.0_FINAL_PASS.zip`
**Authoritative register:** `EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER_UPDATED_V6.md`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**
**Architecture correction applied (2026-07-31).**

Audit is where privacy architectures are most often undone, because audit
is the one place where holding everything looks like a virtue. Six
streams. Separately keyed, separately authorized, separately retained,
**never unified**.

**Corrected by this revision:** §5 defines `EvidenceBundle` v1 in full and
closes `OD-P15-04`.

---

## 1. The streams

| ID       | Stream                 | Contains                                                                                        | Must never contain                                       | Primary reader                     |
| -------- | ---------------------- | ----------------------------------------------------------------------------------------------- | -------------------------------------------------------- | ---------------------------------- |
| `AS-01`  | Eligibility audit      | Rule-set version, scoped source references, decision, reason codes, reviewer, evidence reference | Assertion nonce; credential reference; ballot; tally      | Eligibility Officer; Dispute Reviewer |
| `AS-02`  | Assertion audit        | Minting, queueing, release, pickup, expiry, revocation; context; audience; integrity metadata   | Identity; credential reference; redemption outcome        | Eligibility Officer; Security Auditor |
| `AS-03`  | Credential audit       | Issuance, status, revocation, redemption, replay rejection                                      | Identity; assertion reference; pseudonym; ballot; tally   | Credential Issuer; Security Auditor |
| `AS-04`  | Voting integrity audit | Boundary violations, correlation-risk detections, cohort-threshold events, integrity checks     | **Any identity, in any field**                            | Security Auditor; Independent Auditor |
| `AS-05`  | Independent audit      | Versioned privacy-preserving evidence bundles                                                   | Raw stream access; correlation keys; participation data   | Independent Auditor                |
| `AS-06`  | System integrity       | Service health, key events, configuration changes, privileged acts                              | Participation data; outcome-inferring metrics             | Security Auditor; operations       |

---

## 2. Authorization

| Role                      | `AS-01` | `AS-02` | `AS-03` | `AS-04` | `AS-05` | `AS-06` |
| ------------------------- | ------- | ------- | ------- | ------- | ------- | ------- |
| Membership Authority      | —       | —       | —       | —       | —       | —       |
| Eligibility Officer       | read    | read    | —       | —       | —       | —       |
| Eligibility Reviewer      | case    | —       | —       | —       | —       | —       |
| Credential Issuer         | —       | —       | read    | —       | —       | —       |
| Voting Operations Officer | —       | —       | —       | summary | —       | read    |
| Voting Client Operator    | —       | —       | —       | —       | —       | read    |
| Tally Authority           | —       | —       | —       | —       | —       | —       |
| Independent Auditor       | —       | —       | —       | read    | read    | summary |
| Security Auditor          | —       | metadata| metadata| read    | —       | read    |
| Dispute Reviewer          | case    | —       | case-scoped status only | — | —   | —       |

**No role holds read access to both `AS-01`/`AS-02` and `AS-03`.** That row
is the audit-side statement of the whole architecture, and an
implementation that grants a role both has broken it regardless of what its
documentation says.

The Dispute Reviewer's `AS-03` access is deliberately awkward: **case-scoped
status only**, obtainable only against a credential reference the
participant supplies, never by search.

---

## 3. Prohibited constructions

| Construction                                                            | Verdict        |
| ----------------------------------------------------------------------- | -------------- |
| A unified audit table spanning the chain                                | **prohibited** |
| A correlation key present in two streams                                | **prohibited** |
| A join, view, query or report spanning `AS-01`/`AS-02` and `AS-03`      | **prohibited** |
| An export containing two streams                                        | **prohibited** |
| A SIEM, warehouse or lake ingesting two streams into one index          | **prohibited** |
| An incident-response tool with read access to all streams               | **prohibited** |
| A backup archive containing two streams                                 | **prohibited** |
| A "participation journey" or "case timeline" spanning the boundary      | **prohibited** |
| A shared trace or request identifier appearing in two streams           | **prohibited** |
| A break-glass grant covering two streams                                | **prohibited** |
| **An evidence bundle containing per-participation records**             | **prohibited** |
| **A bundle export naming two contexts or two streams' raw content**     | **prohibited** |

Each of these has a plausible operational justification, and each of them
recreates the link. The refusal has to survive the justification, which is
why these are structural acceptance criteria rather than policies.

---

## 4. Stream properties

| Property           | `AS-01`                | `AS-02`               | `AS-03`               | `AS-04`             | `AS-05`               | `AS-06`             |
| ------------------ | ---------------------- | --------------------- | --------------------- | ------------------- | --------------------- | ------------------- |
| Key space          | Eligibility case       | Assertion             | Credential            | Context / detection | Bundle                | Service / act       |
| Identity present?  | **yes** (identity side)| no                    | no                    | **never**           | no                    | operator identity only |
| Timestamps         | ordinary               | **coarsened**         | **coarsened**         | timing class        | coarsened             | ordinary            |
| Retention class    | Eligibility evidence   | Assertion issuance    | Credential evidence   | Integrity evidence  | Auditor evidence      | System evidence     |
| Integrity          | `audit-core`, separate key per stream | same   | same                  | same                | same + bundle signature | same              |
| Immutability       | append-only            | append-only           | append-only           | append-only         | append-only           | append-only         |
| Legal hold         | applicable             | applicable            | applicable            | applicable          | applicable            | applicable          |

---

## 5. `EvidenceBundle` v1 — `OD-P15-04` closed

An independent auditor must be able to say that the election was
administered correctly. Doing that from raw streams would require exactly
the correlation the system forbids, so the auditor works from a
**versioned, privacy-preserving evidence bundle**, scoped to exactly one
voting context.

### 5.1 Permitted content — a closed list of eight sections

| # | Section                                   | Contents                                                                                                                                    |
| - | ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| 1 | Voting-context metadata                   | Context reference, type, organizational scope, windows, revocation cutoff, status history                                                   |
| 2 | Rule-set and configuration versions       | Frozen rule-set version; the `IssuanceTimingProfile` values in force; privacy profile; audit profile; the schema version of every stream summarized |
| 3 | Aggregate eligibility totals              | Requested, approved, denied **by reason code**, review required, superseded, expired, disputed, dispute outcomes                             |
| 4 | Assertion issuance integrity totals       | Minted, queued, released, picked up, expired unused, revoked, replay rejected; batch count; cohort-size **class** distribution               |
| 5 | Credential totals                         | Issued, revoked **by position relative to the cutoff**, expired, redeemed, replay rejected, duplicate requests rejected                      |
| 6 | Integrity commitments and signature metadata | Per-stream integrity commitments; commitment algorithm identifier; key identifier; the bundle signature and its trust-store reference     |
| 7 | Disclosure-control metadata               | Thresholds applied; which cells were suppressed; suppression method; complementary suppressions applied                                      |
| 8 | Bundle provenance                         | Bundle schema version; generation time (coarsened); generating authority; export authorization reference                                    |

### 5.2 Prohibited content — normative

Raw identity of any kind · any member identifier · **any context-scoped
pseudonym** · any credential secret or credential identifier · any
assertion identifier or nonce · any ballot data · **any per-participation
record** · any correlation key spanning two streams · any un-suppressed
cell below `disclosure_min_cell` · any precise timestamp.

### 5.3 Validation

A bundle is valid only if all of the following hold. A bundle failing any
check is **rejected, not repaired**.

| # | Check                                                                                                                     |
| - | ------------------------------------------------------------------------------------------------------------------------- |
| 1 | It declares a supported `bundle_schema_version`                                                                           |
| 2 | Every section is present, or explicitly declared empty or suppressed                                                      |
| 3 | Every per-stream integrity commitment verifies against that stream                                                        |
| 4 | The bundle signature verifies against the audit trust store, using a key distinct from every other function's (§18 of the specification) |
| 5 | **Count consistency:** redeemed ≤ issued; picked up ≤ released ≤ queued ≤ minted; revoked + expired + redeemed ≤ issued; approved ≥ minted |
| 6 | Replay-rejection totals reconcile with `AS-04`'s integrity records                                                        |
| 7 | Disclosure-control metadata is present and its thresholds meet the minimum                                                |
| 8 | No prohibited field is present, by structural scan                                                                        |
| 9 | The bundle is **reproducible by a second auditor** from the same inputs                                                    |

### 5.4 Versioning

Within a major version, sections and fields may be **added** compatibly.
Removing a section, narrowing a total, or changing a definition is a **new
major version**. A bundle always states the schema version of every stream
it summarizes, so that an old bundle remains interpretable after a stream
schema evolves under ADR-074.

### 5.5 Export authorization

| Rule                                                                                             |
| ------------------------------------------------------------------------------------------------ |
| Independent Auditor role **plus** a time-boxed PACK-12 grant                                     |
| **One context per bundle**; a request naming two contexts is refused                             |
| A request for two streams' raw content is refused — there is no "export everything" operation    |
| The export is itself audited, to `AS-05` and `AS-06`                                             |
| **Pre-closure export** is restricted to sections 1, 2, 6, 7 and 8 and requires **dual control**  |
| Sections 3, 4 and 5 are exportable only after the context reaches `voting_closed`                |
| A bundle is signed at generation; an unsigned or re-signed bundle is not a bundle                |

Pre-closure restriction exists because a count is an intermediate tally
(ADR-094), and an auditor's legitimate need to verify *process* before
closure does not extend to *totals*.

### 5.6 Small-cohort suppression

| Rule                                                                                                      |
| --------------------------------------------------------------------------------------------------------- |
| Any cell below `disclosure_min_cell` (default and minimum **5**) is **suppressed, not rounded**            |
| Suppression is flagged in section 7, never silent                                                          |
| **Complementary suppression** is applied so a suppressed cell cannot be recovered by differencing against totals |
| Differencing **across bundles** — two bundles of the same context at different times — must also be prevented |
| Where suppression would empty a section, the section is declared suppressed as a whole                     |
| The suppression threshold is never lowered per context; small electorates raise it, never lower it         |

`T-P15-39` is the threat this section answers: an auditor with two bundles
and arithmetic is a differencing attack unless complementary suppression is
applied across time as well as across cells.

### 5.7 What the auditor still cannot verify, and how it is covered

**That a specific person's participation was handled correctly** is not a
bundle question. It is verified instead through the **dispute path**, where
the participant supplies their own references and consents to the
examination of their own case (ADR-098).

System-level integrity from bundles; individual-level integrity from
participant-initiated cases. That division is the honest one, and between
them the coverage is complete without the chain.

---

## 6. Retention and deletion of evidence

| Stream  | Minimum retention driver              | Deletion constraint                                                     |
| ------- | ------------------------------------- | ----------------------------------------------------------------------- |
| `AS-01` | Dispute and appeal windows            | Not deleted while a dispute or legal hold is open                       |
| `AS-02` | Issuance window plus dispute margin   | **Reduced to counts** after the margin, to shorten the correlation window |
| `AS-03` | Context plus audit margin             | Redemption records reduced to counts after the audit margin             |
| `AS-04` | Integrity investigation window        | Long; contains no identity, so retention costs little privacy           |
| `AS-05` | Governance and legal requirements     | Bundles are the long-lived artifact                                      |
| `AS-06` | Operations and security requirements  | Standard                                                                |

`AS-02`'s reduction to counts is a deliberate privacy control: the
assertion issuance record is the last identity-side artifact that could,
combined with a future compromise, narrow the field.

Periods are `OD-P15-06` and belong to PACK-09; **what this round fixes is
the class and the constraint, not the number.**
