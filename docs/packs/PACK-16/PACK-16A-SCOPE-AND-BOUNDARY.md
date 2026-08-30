# PACK-16A — Scope and Boundary

**Round:** PACK-16A — Verifiable Voting Protocol and Ballot Model Selection. **Specification and ADR only. No code. Not implemented. Not an implementation candidate. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**Baseline:** `EPD2_PACK-15_VOTING_TRUST_BOUNDARY_ELIGIBILITY_CREDENTIAL_SEPARATION_0.15.0_FINAL_PASS.zip`
SHA-256 `38697c0a0bca9d211bf9f44ec5c2f7b475d86bd38eb1ccc10bc9521c3f2f087a`
**Authoritative register:** `docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md` (one canonical copy)
**Register entry:** `FIR-ROADMAP-006` — status unchanged at `approved`
**ADR:** `ADR-099`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 0. What this round is

PACK-15 spent an entire round proving that eligibility can reach the voting
domain without identity, and then stopped one step short of the ballot. Its
closing sentence to PACK-16 was precise: the voting side receives **a
minimal single-use continuation capability** and nothing else, and PACK-16
inherits the obligation to prove the second half of an invariant whose
first half PACK-15 closed.

```text
FIR-INV-002  =  (identity → credential)  ∧  (credential → ballot)
                 ─────── PACK-15 ───────     ─────── PACK-16 ───────
```

PACK-16 is too large to take in one round. Choosing a cryptographic voting
protocol, fixing its parameters, running a key ceremony, specifying casting
and verification and then implementing all of it is four different kinds of
decision with four different failure modes, and bundling them produces the
one outcome this project has consistently refused: a security architecture
settled by whoever happened to be writing code that week.

So PACK-16 is sequenced, and this document is the first stage.

```text
PACK-16A  protocol research, comparative assessment, threat-model
          extension, ballot-model selection, specification, proposed ADR
PACK-16B  cryptographic parameters, key ceremony, trustee architecture
PACK-16C  casting, verification, receipt and bulletin-board specification
PACK-16D  implementation candidate
```

**PACK-16B must not begin before PACK-16A is architecturally accepted.**
Acceptance is a separate act performed after an audit of the candidate
archive; it is not conferred by this document existing.

---

## 1. Scope of PACK-16A

PACK-16A produces, **as documents only**:

1. the boundary PACK-16 inherits from PACK-15, restated as obligations
   rather than as description (§3, §4);
2. a comparative assessment of mature verifiable-voting protocol families
   against primary sources (`PACK-16A-PROTOCOL-COMPARISON.md`);
3. an evidence matrix recording, per claim, the exact document, version,
   section and whether the claim is a protocol property, an implementation
   property or an inference (`PACK-16A-PROTOCOL-EVIDENCE-MATRIX.md`);
4. a threat model continuing — not replacing — PACK-15's
   (`PACK-16A-THREAT-MODEL.md`);
5. a selected protocol family and a bounded EPD² profile
   (`PACK-16A-BALLOT-MODEL-SPECIFICATION.md`);
6. an election-type applicability matrix
   (`PACK-16A-ELECTION-PROFILE-MATRIX.md`);
7. an explicit revoting decision and a specification-level ballot state
   machine (`PACK-16A-REVOTING-AND-BALLOT-LIFECYCLE.md`);
8. an honest statement of what receipts and coercion controls can and
   cannot do, with a permitted- and prohibited-claims registry
   (`PACK-16A-COERCION-AND-RECEIPT-BOUNDARY.md`);
9. bulletin-board requirements as a distinct trust boundary
   (`PACK-16A-BULLETIN-BOARD-REQUIREMENTS.md`);
10. trustee and key-ceremony obligations handed to PACK-16B
    (`PACK-16A-TRUSTEE-AND-CEREMONY-REQUIREMENTS.md`);
11. roles and a separation-of-duties matrix for the ballot domain
    (`PACK-16A-ROLE-SEPARATION-MATRIX.md`);
12. the German legal and governance boundary, separated from technical
    capability (`PACK-16A-GERMAN-LEGAL-BOUNDARY.md`);
13. a privacy and metadata data-flow model
    (`PACK-16A-PRIVACY-DATA-FLOW-MATRIX.md`);
14. a failure and election-abort model
    (`PACK-16A-FAILURE-AND-ABORT-MODEL.md`);
15. protocol-level accessibility requirements
    (`PACK-16A-ACCESSIBILITY-REQUIREMENTS.md`);
16. specification-level reason-code namespaces
    (`PACK-16A-REASON-CODE-SPECIFICATION.md`);
17. FIR coverage (`PACK-16A-FIR-COVERAGE-MATRIX.md`);
18. a canon assessment (`PACK-16A-CANON-ASSESSMENT.md`);
19. an acceptance matrix (`PACK-16A-ACCEPTANCE-MATRIX.md`);
20. open decisions (`PACK-16A-OPEN-DECISIONS.md`);
21. a specification report (`PACK-16A-SPECIFICATION-REPORT.md`);
22. a handover (`PACK-16A-HANDOVER.md`);
23. `docs/adr/ADR-099-VERIFIABLE-VOTING-PROTOCOL-AND-BALLOT-MODEL.md`,
    status `proposed`.

### 1.1 Out of scope, explicitly

```text
NO PRODUCTION CODE
NO MIGRATIONS
NO API IMPLEMENTATION
NO EVENT IMPLEMENTATION
NO FRONTEND IMPLEMENTATION
NO CRYPTOGRAPHIC IMPLEMENTATION
NO TEST IMPLEMENTATION
NO CI CHANGES
NO DEPENDENCY CHANGES
NO VERSION BUMP
```

Also out of scope for **this stage** and deferred by name:

| Deferred to | What                                                                                                                        |
| ----------- | --------------------------------------------------------------------------------------------------------------------------- |
| PACK-16B    | Group, curve, key size, hash, library, HSM/KMS, key ceremony script, guardian count and quorum values, parameter provenance |
| PACK-16C    | Casting protocol messages, verification-client specification, receipt surface, bulletin-board wire format, mirror protocol  |
| PACK-16D    | Any code, schema, migration, contract fixture, test or CI stage                                                             |
| PACK-17     | Network and infrastructure metadata, resilience, incident readiness, independent-verification operations                    |
| FRONT-PACK  | The page-by-page Voting Client and Verification Client structure                                                            |
| Governance  | Any activation of any election profile; any legal assessment                                                                |

**PACK-16A selects a family and a profile. It does not build one, and it
does not authorise one to be used.**

---

## 2. Relationship to FIR-ROADMAP-006

`FIR-ROADMAP-006` — _PACK-16 Verifiable Voting Implementation_, status
`approved`, target version `0.16.0` — records the scope:

```text
verifiable voting
audited cryptographic protocol integration
ballot casting
vote verification
tally controls
no intermediate tally
eligibility without identity-vote linkage
```

**PACK-16A does not implement `FIR-ROADMAP-006` and does not change its
status.** It researches, compares, specifies, selects a recommended
protocol family, records constraints and defines further obligations. The
register entry stays `approved`; the target version stays `0.16.0`; and the
version bump belongs to the implementation candidate, not to a
specification stage. `REPOSITORY_VERSION` therefore remains `0.15.0` in
this archive, exactly as PACK-15 left it.

---

## 3. The boundary PACK-15 hands over

PACK-15 §12 defines what crosses into PACK-16:

> a **minimal continuation capability**: scoped to one context, valid for
> one casting act, bounded in time, carrying no identity and no persistent
> identifier, consumed by PACK-16. It is not a session and is not
> resumable after use.

Restated as the constraints PACK-16A is bound by, and which no protocol
selection may relax:

```text
The continuation capability is not the credential.
The continuation capability is not the credential ID.
Its reference must never become a ballot ID.
A ballot ID must never echo or derive from it.
It contains no civil identity.
It contains no member identity.
It contains no account identity.
It contains no persistent member identifier.
It cannot be reverse-resolved to identity.
It must not create a reusable voting session.
It must not create a cross-origin identity session.
```

### 3.1 The obligation PACK-15 left open, stated exactly

PACK-15 ADR-090 §4 and ADR-093 set the standard of proof for the
identity-side records, and PACK-16 inherits it for the voting side:

> The implementation must demonstrate that the two records **cannot be
> paired** — a stronger obligation than demonstrating that no code pairs
> them.

Applied to this round: it is **not sufficient** to show that no current
code joins a redemption record to a ballot. The architecture must show that
records cannot be paired, including through:

| Correlation channel   | Owning stage                                  |
| --------------------- | --------------------------------------------- |
| Exact timestamps      | PACK-16A (requirements), PACK-16C             |
| Order of arrival      | PACK-16A (requirements), PACK-16C             |
| Request IDs           | PACK-16A (prohibition), PACK-16D              |
| Correlation IDs       | PACK-15 rule, restated here                   |
| Trace IDs             | PACK-15 rule, restated here                   |
| Idempotency keys      | PACK-16A (prohibition), PACK-16D              |
| Log sequencing        | PACK-16A (requirements), PACK-16D             |
| Metrics labels        | PACK-16A (prohibition), PACK-16D              |
| Backup snapshots      | PACK-17                                       |
| Shared infrastructure | PACK-17                                       |
| Administrator access  | PACK-16A (role separation), PACK-12 mechanism |
| Network metadata      | PACK-17                                       |

`PACK-16A-PRIVACY-DATA-FLOW-MATRIX.md` is the per-flow treatment.
`PACK-16A-THREAT-MODEL.md` §2 is the adversarial treatment.

### 3.2 Continuation-capability consumption — requirements only

PACK-16A defines **what consumption must satisfy**. It does not implement
consumption, does not define its wire format and does not choose its
construction.

| ID      | Requirement                                                                                                               |
| ------- | ------------------------------------------------------------------------------------------------------------------------- |
| `CC-01` | Consumption is a single atomic act with exactly-once effect; a second presentation is refused with a distinct reason code |
| `CC-02` | Consumption produces a **casting authorisation** that is not stored beside any ballot and is not derivable from one       |
| `CC-03` | No ballot identifier, confirmation code, tracker or board entry is derived from the continuation reference                |
| `CC-04` | No record anywhere holds a continuation reference and a ballot identifier together                                        |
| `CC-05` | Consumption writes to the credential-side stream (`AS-03` lineage) only; the ballot record is written on the board side   |
| `CC-06` | Consumption timestamps are coarsened to the context's `timestamp_granularity`; no microsecond value is logged             |
| `CC-07` | Consumption does not create a session, a cookie, a storage entry or a resumable state in the Voting Client                |
| `CC-08` | A failed casting act after consumption does **not** restore the capability; the remedy is governed, not automatic (§6)    |
| `CC-09` | Consumption is refused if the election manifest, the cryptographic parameters or the board checkpoint fail validation     |
| `CC-10` | The count of consumptions is not published, exported or displayed before closure — it is turnout (ADR-094)                |

`CC-08` is uncomfortable and is stated deliberately. A capability that can
be re-obtained after a failed cast is a capability that can be re-obtained
after a _successful_ cast if the success signal is lost, and that is a
double-vote path. PACK-15 refused the equivalent trade for credential
delivery (§13.2) and PACK-16A refuses it here for the same reason.
`PACK-16A-FAILURE-AND-ABORT-MODEL.md` `FM-P16A-07` states the governed
remedy and its honest cost.

---

## 4. Infrastructure separation inherited unchanged

PACK-15 ADR-090 §7 and ADR-096 bind infrastructure, not only code. **This
round confirms every item and relaxes none.**

Prohibited across the identity and voting sides:

```text
shared database
shared backup domain
shared restore target
shared log index
shared metrics label space
shared distributed trace
shared correlation ID
shared request ID
shared identity session
principal with read access to both sides
```

The Voting Client (WS-03) remains:

```text
separate workspace
separate origin
no shared cookies
no shared localStorage
no shared IndexedDB
no shared identity session
no analytics
no advertising
no fingerprinting
no shared telemetry
no persistent member identifier
purpose-scoped one-time handoff only
```

**No protocol integration may weaken these.** A protocol implementation
that needs a per-voter persistent client-side secret, a resumable voting
session, a third-party script origin or a shared analytics endpoint is, on
that ground alone, not selectable — and §5 of
`PACK-16A-PROTOCOL-COMPARISON.md` applies this as a filter, not as a
preference.

**A new prohibition this round adds, in the same spirit:** the
**Verification Client** is a third origin, separate from both WS-02 and
WS-03, holding no session and no identity, and it may not be served from
the Voting Client's origin. A verification surface inside the casting
origin is a surface an attacker who owns the casting origin also owns.
`PACK-16A-BULLETIN-BOARD-REQUIREMENTS.md` §7 and
`PACK-16A-THREAT-MODEL.md` `T-P16A-31` carry it.

---

## 5. Invariants that are not open decisions

The following are **inherited or established constraints**, not choices
this round or any later round may reconsider without a governed amendment:

```text
NO IDENTITY IN BALLOT
NO CREDENTIAL ID AS BALLOT ID
NO CONTINUATION REFERENCE AS BALLOT ID
NO PERSON-TO-BALLOT LINK
NO IDENTITY RECOVERY BY CORRELATION
NO REUSABLE VOTING SESSION
NO INTERMEDIATE TALLY
NO PARTIAL OUTCOME DISCLOSURE
NO TURNOUT DISCLOSURE BEFORE CLOSURE
NO SINGLE-ADMIN DECRYPTION
NO SILENT BALLOT REPLACEMENT
NO SILENT BALLOT DELETION
NO UNEXPLAINED BALLOT EXCLUSION
NO RECEIPT THAT REVEALS CHOICE
NO THIRD-PARTY ANALYTICS
NO FINGERPRINTING
NO BALLOT CONTENT IN DISPUTE RECORDS
NO INDIVIDUAL BALLOT CORRECTION THROUGH IDENTITY LINKAGE
APPEND-ONLY VERIFIABLE ELECTION EVIDENCE
```

Separately, PACK-16A must define **requirements** for the following
properties. Defining a requirement is not the same as claiming the
property, and the distinction is enforced throughout this pack:

| Property                   | Where its requirement is defined           | Claim status after PACK-16A                                |
| -------------------------- | ------------------------------------------ | ---------------------------------------------------------- |
| Cast as intended           | Ballot model §4; coercion boundary §3      | **specified**; evidence obligation on PACK-16C             |
| Recorded as cast           | Ballot model §5; bulletin board §2         | **specified**; depends on board properties not yet built   |
| Tallied as recorded        | Ballot model §6; trustee requirements §4   | **specified**; depends on a verifier not yet specified     |
| Individual verifiability   | Ballot model §5; coercion boundary §4      | **specified**, with a stated take-up limitation            |
| Universal verifiability    | Bulletin board §2; trustee requirements §5 | **specified**; requires an independent verifier (PACK-16C) |
| Software independence      | Ballot model §7                            | **specified as an objective**; not demonstrated            |
| Ballot secrecy             | Ballot model §3; privacy data flows        | **specified**; bounded by §5.1 below                       |
| Receipt-freeness           | Coercion boundary §2, §5                   | **bounded claim only**; see the prohibited-claims registry |
| Coercion-resistance limits | Coercion boundary §5, §6                   | **limits stated**; the property itself is **not claimed**  |
| Cryptographic agility      | Ballot model §8; trustee requirements §6   | **specified**; parameters deferred to PACK-16B             |
| Fail-closed behaviour      | Failure and abort model                    | **specified**                                              |
| Independent verification   | Bulletin board §6; roles §3                | **specified**; operations owned by PACK-17                 |

### 5.1 The rule that governs every claim in this pack

> **A property may be stated only where the selected model is shown to
> provide it, under named assumptions, with a cited source. Where the model
> provides it partially, the partiality is the statement. Where it does not
> provide it, the absence is the statement.**

This is not decoration. Three of the four systems compared in this round
published a stronger claim than their deployed code supported at some point
in their history, and in two cases the gap was found by third parties years
later (`PACK-16A-PROTOCOL-EVIDENCE-MATRIX.md` §7). The prohibited-claims
registry in `PACK-16A-COERCION-AND-RECEIPT-BOUNDARY.md` §8 is the
enforcement surface.

---

## 6. Intermediate tally — restated, with the additions this round makes

`ADR-094` and `PACK-15-INTERMEDIATE-TALLY-PROHIBITION-MATRIX.md` stand
unchanged. Before formal closure, nothing may disclose or permit inference
of:

```text
vote distribution
partial results
results by organizational scope
results by geography
results by demographic or other dimension
ballot content
turnout
current standing
leaderboards
forecasts
projections
sampling of ballots
spot checks of ballots
outcome-bearing audit evidence
partial decryption revealing an outcome
```

**Sampling and spot checks of ballot content may not be presented as a
verification mechanism before closure.** PACK-15's `IT-15` states it; this
round restates it because the selected protocol family makes a
pre-closure integrity check _possible_, and the temptation to describe it
as "auditing a few ballots" is exactly the failure mode.

### 6.1 What PACK-16A adds

The architecture must make the following true, and
`PACK-16A-BALLOT-MODEL-SPECIFICATION.md` §6 is where each is discharged:

| ID       | Requirement                                                                                                            | How the selected model discharges it                                                               |
| -------- | ---------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| `NIT-01` | Encrypted ballots are checkable without revealing any choice                                                           | Ballot well-formedness proofs verify against ciphertext only; no decryption is involved            |
| `NIT-02` | Cryptographic validity is checkable without a partial tally                                                            | Proof verification is per-ballot and per-contest, and yields a boolean, not a count                |
| `NIT-03` | No trustee action before closure discloses an outcome                                                                  | The decryption ceremony is bound to `voting_closed`; no partial decryption exists before it        |
| `NIT-04` | Operational dashboards contain no outcome-bearing data                                                                 | Permitted-signal list plus PACK-12 disclosure control, `disclosure_min_cell = 5`                   |
| `NIT-05` | A privileged administrator cannot obtain an early tally                                                                | Threshold decryption; no single principal holds a quorum; `NO SINGLE-ADMIN DECRYPTION`             |
| `NIT-06` | **No feature flag may disable this constraint**                                                                        | `FIR-INV-006`; the prohibition is structural, and a flag that could relax it may not exist         |
| `NIT-07` | Challenged/spoiled ballots are decrypted **and are never tallied**, and their publication is not an intermediate tally | Challenged ballots are excluded from the tally by construction and are marked as such on the board |

`NIT-07` deserves a sentence, because it is the one place where the
selected family decrypts something before closure. A challenged ballot is
decrypted precisely **because** it is not a vote — it is a test of the
encryption device, and it is spoiled by the act of challenging it. It
carries no participation and no outcome. Publishing a spoiled ballot
discloses a device check, not a preference.
`PACK-16A-REVOTING-AND-BALLOT-LIFECYCLE.md` §3 makes `spoiled` an
absorbing state so that the distinction cannot erode.

---

## 7. Dispute boundary — inherited unchanged

`ADR-098` stands. PACK-16A creates **no** mechanism for:

```text
find my ballot
correct my ballot
delete my ballot
replace my ballot after identity lookup
show how my ballot was counted
waive secrecy for my dispute
```

The dispute process does not accept ballot content, does not accept
screenshots carrying a ballot choice, receives no correlation capability,
receives no cross-stream read, cannot link a person to a ballot, and
**cannot create that link even with the participant's consent** — because a
consent-based linkage is a linkage capability that exists, and a capability
that exists can be compelled.

Remedies remain context-level:

```text
re-evaluation
scope correction
window extension
re-run
annulment
recorded irreducible loss
```

`PACK-16A-BALLOT-MODEL-SPECIFICATION.md` §9 records the check that the
selected protocol creates no hidden individual dispute link, and
`PACK-16A-THREAT-MODEL.md` `T-P16A-33` treats the attempt to build one.

---

## 8. Small-group disclosure — inherited, extended, not silently changed

PACK-15 §19.2 and `PACK-15-INTERMEDIATE-TALLY-PROHIBITION-MATRIX.md`
establish `disclosure_min_cell = 5` with complementary suppression, and
PACK-15 §19.4 establishes the small-electorate policy. **This round changes
neither value and proposes no change to either.**

What PACK-16A adds is the treatment of **published results**, which PACK-15
did not have to consider because it stopped before the tally.
`PACK-16A-ELECTION-PROFILE-MATRIX.md` §6 is the full treatment; the
governing statements are:

1. A result is published for the **context**, not for organizational
   sub-scopes, unless the context's configuration declares sub-scope
   publication and every sub-scope cell passes `disclosure_min_cell`.
2. Complementary suppression applies **jointly across the published set**,
   including across the result, the aggregate participation figures and any
   previously published bundle for the same context, so that a suppressed
   cell cannot be recovered by differencing.
3. Where suppression would empty a breakdown, the breakdown is declared
   suppressed as a whole rather than partially shown.
4. Where the **whole electorate** is below the small-electorate threshold,
   the context publishes the aggregate outcome only, and the governance
   acknowledgement of PACK-15 §19.4 is a precondition of activation.
5. The disclosure decision is taken by the **Election Board**, recorded as
   an act, and reflected in append-only evidence. It is not an operator
   setting.
6. A **full unsuppressed result** may be available to the Independent
   Auditor under a time-boxed PACK-12 grant **after closure**, one context
   per grant, and never before.
7. Small-cell dashboards may not be used to reconstruct an intermediate
   tally: per-scope operational metrics are prohibited outright below the
   small-electorate threshold (PACK-15 §19.4), and thresholded elsewhere.

**Any future proposal to change `disclosure_min_cell` is a finding or a
Canon assessment, never an inline edit.** None is proposed here.

---

## 9. What this round is not

It is not an implementation. It is not an implementation candidate. It is
not a PASS. It does not create a service, a module, a migration, a test, a
contract fixture, a schema or a CI stage. It changes no version and amends
no canon. It integrates no cryptography, chooses no curve, no key size, no
library, no HSM and no KMS. It does not cast a ballot, count a vote, build
a Voting Client or a Verification Client, and it does not make this system
usable for any election, internal or public.

It reads a field that has been trying to solve this problem for twenty
years, records honestly what those systems do and do not achieve, chooses
the family whose declared gap is exactly the gap PACK-15 fills, bounds it
to a profile, and writes down every property it is not yet entitled to
claim.

**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION
PROHIBITED BY DEFAULT.**
