# PACK-16C — Open Decisions

**Round:** PACK-16C — Casting, Receipt, Verification Client, Bulletin Board and Election Record. **Specification and ADR only. No code. No cryptographic implementation. Not implemented. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-101`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 0. What belongs here

```text
An OPEN DECISION is a question this round deliberately did not answer,
with a named owner, a named consequence of leaving it open, and a
statement of what it blocks.

It is NOT a to-do list. It is NOT a place to move a decision that
should have been made. Every entry says why it was RIGHT to leave it
open at specification stage.
```

| ID       | Rule                                                                                                                                                                              |
| -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `OD-R01` | **Every open decision names what it blocks.** An entry that blocks nothing is not a decision; it is a preference                                                                  |
| `OD-R02` | **No open decision is a licence to proceed.** Where an entry blocks production implementation acceptance, PACK-16D may specify around it but may not close it by choosing quietly |
| `OD-R03` | **`VO-08` is not listed here.** It is PACK-16B's, it is OPEN, and PACK-16C neither owns, closes, narrows nor re-owns it (`SB-06`, `T-P16C-37`)                                    |

---

## 1. The register

| ID           | Question                                                                                                                                                                 | Owner                                                                                               | Blocks                                                                                                    | Why it is open                                                                                                                                                                                                                                                                                                                                                                                                                        |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `OD-P16C-01` | **What distributed-transaction mechanism gives the atomic acceptance boundary its exactly-once guarantee across the capability store and the ballot store?**             | PACK-16D                                                                                            | **Production implementation acceptance**                                                                  | The boundary's _semantics_ are specified (`CN-17`…`CN-20`). The mechanism is an implementation choice with real trade-offs, and choosing it here would be specifying a database from a specification round. **If PACK-16D cannot demonstrate `CN-19`, that is an `ARCHITECTURAL BLOCKER`, not a risk to accept**                                                                                                                      |
| `OD-P16C-02` | **Are write-in candidates supported, and if so how?**                                                                                                                    | A future ADR                                                                                        | Any context requiring write-ins                                                                           | Free text inside a ballot defeats the homomorphic tally and is a first-class re-identification channel in small electorates. The honest answer at this stage is "not in this profile", not a half-designed mechanism (`BP-*`)                                                                                                                                                                                                         |
| `OD-P16C-03` | **What attestation technology, if any, binds the served client to the published build?**                                                                                 | PACK-16D                                                                                            | Nothing at specification stage; **weakens `FM-16C-01`** if never answered                                 | Attestation availability differs by platform and changes fast. The requirement — _build_ attestation, never device or user — is fixed (`BP-17`); the technology is not                                                                                                                                                                                                                                                                |
| `OD-P16C-04` | **What is the wire and record serialization format?** (JSON, CBOR, other)                                                                                                | PACK-16D                                                                                            | Verifier interoperability; test-vector production                                                         | The **canonicalisation rules** are normative now (`BP-*`, `ER-12`) and are the part that matters for signatures. The container is a later choice                                                                                                                                                                                                                                                                                      |
| `OD-P16C-05` | **What is the receipt's encoding and presentation format?**                                                                                                              | PACK-16D                                                                                            | Nothing; **accessibility gate** applies either way                                                        | The receipt's _contents_ and prohibitions are fixed (`RE-*`). The rendering is a design question that must clear `XA-*`                                                                                                                                                                                                                                                                                                               |
| `OD-P16C-06` | **Is a QR encoding offered, and under what policy?**                                                                                                                     | PACK-16D + GOVERNANCE                                                                               | Nothing                                                                                                   | `RE-10` and `RE-11` already bound it: never the only form, contents displayed in text beside it, no ballot content. Whether to offer it at all is a usability decision                                                                                                                                                                                                                                                                |
| `OD-P16C-07` | **What is the offline verification bundle's format?**                                                                                                                    | PACK-16D                                                                                            | **Independent verification under `BM-28`** if never answered                                              | Offline verification is a _required capability_ (`VC-09`, `IV-*`). Its packaging depends on `OD-P16C-04`                                                                                                                                                                                                                                                                                                                              |
| `OD-P16C-08` | **Who is engaged as the independent reference verifier?**                                                                                                                | GOVERNANCE                                                                                          | **Binding use of any context** (`BM-28`, `IV-06`)                                                         | This is an organisational and funding decision, not a technical one. Naming a party in a specification would not bind anyone                                                                                                                                                                                                                                                                                                          |
| `OD-P16C-09` | **How are independent verification reports governed, published and cited?**                                                                                              | GOVERNANCE                                                                                          | Certification                                                                                             | `IV-11` and `IV-12` fix what a report must contain. Who publishes it, on what timeline, and how a negative report is handled is governance                                                                                                                                                                                                                                                                                            |
| `OD-P16C-10` | **Concrete batch-capacity parameters** — see §1.1 for the full entry                                                                                                     | **Election governance**, with PACK-16D implementation analysis and PACK-17 independent verification | **Production activation**, until concrete parameters are demonstrated to satisfy the capacity model       | The architecture is closed; only the numbers are open. **The plausible-load criterion is withdrawn** — §1.1                                                                                                                                                                                                                                                                                                                           |
| `OD-P16C-11` | **Who operates the mirrors, and how is their independence established?**                                                                                                 | GOVERNANCE                                                                                          | **Split-view resistance** (`AO-13`, `T-P16C-16`)                                                          | Mirror independence is organisational. Specifying "independent" without naming who and how would be the kind of claim this pack refuses to make                                                                                                                                                                                                                                                                                       |
| `OD-P16C-12` | **Is external witness cosigning adopted, and in which ecosystem?**                                                                                                       | PACK-17                                                                                             | **Production implementation acceptance** — `AO-14`                                                        | `G-03` shows the IETF's gossip work died; `G-04` shows a community construction exists but claims no split-view property. Adopting an ecosystem that does not yet exist for elections is premature; **pretending the gap is closed is worse**                                                                                                                                                                                         |
| `OD-P16C-13` | **What is the escalation window after a missed commitment obligation?**                                                                                                  | GOVERNANCE                                                                                          | **`FM-16C-16`'s and `FM-16C-20`'s remedy paths**                                                          | The _deadline_ is no longer open: it is the named batch window (`PA-03`, `PA-10`). Only the **escalation window** — how long a `publication_disputed` may stand before the election-level outcome — remains a governance decision                                                                                                                                                                                                     |
| `OD-P16C-14` | **What is the exact leaf-commitment construction?** — hash function binding, domain tag, salt length, field ordering and the encoding of the committed tuple             | PACK-16D                                                                                            | **Verifier interoperability**; nothing at specification stage                                             | The _properties_ are fixed: domain-separated, hiding, fixed-size, indistinguishable from a uniform random value of the same length (`TC-27`…`TC-29`, `AO-17`). The construction must be pinned before test vectors exist, and pinning it here would pre-empt the review that `EPD2-CRYPTO-1` is still awaiting                                                                                                                        |
| `OD-P16C-15` | **What is the wire format of a privacy-safe inclusion proof?**                                                                                                           | PACK-16D                                                                                            | Nothing at specification stage                                                                            | The _content_ is fixed (`TC-37`, `API-20`); the container depends on `OD-P16C-04`                                                                                                                                                                                                                                                                                                                                                     |
| `OD-P16C-16` | **What is the format of `sealed_batch_opening` and `batch_reconciliation_record`?**                                                                                      | PACK-16D                                                                                            | **Independent verification of checks 17–21** if never answered                                            | The _contents_ are fixed (`BE-25`, `BE-26`, `TC-41`…`TC-45`); the serialization is not                                                                                                                                                                                                                                                                                                                                                |
| `OD-P16C-17` | **How is leaf reservation stored and made atomic with the acceptance boundary?**                                                                                         | PACK-16D                                                                                            | **Production implementation acceptance**                                                                  | The _semantics_ are fixed (`TC-70`…`TC-73`): reservation precedes durable acceptance, is inside the boundary, is released on rejection, times out, and is anonymous. The storage and the transaction mechanism ride on `OD-P16C-01`                                                                                                                                                                                                   |
| `OD-P16C-18` | **What are the capacity stress-testing thresholds and the operational safety reserve?**                                                                                  | PACK-17 + GOVERNANCE                                                                                | **Confidence that `FM-16C-29` will not fire in practice** — not the round                                 | `TC-64` requires a published reserve; how large it should be is an empirical and governance question                                                                                                                                                                                                                                                                                                                                  |
| `OD-P16C-19` | **What is the privacy-preserving construction that proves each anonymous continuation contributed at most one cast artefact and at most one public challenge artefact?** | PACK-16D specification, **independent cryptographic review by PACK-17**                             | **Certification** — and, if it proves impossible, the per-capability bound is checkable only in aggregate | Public totals are checkable now (`IV-18`, check 20). The **per-capability** statement needs evidence that does not publish a capability-to-artefact mapping. **This round does not know how to construct it and says so** rather than asserting it is solved (`TC-83`, `IV-19`, `IV-20`). If PACK-16D cannot construct a sufficient evidence boundary, that is an **`ARCHITECTURAL BLOCKER` for certification**, not a risk to accept |

### 1.1 `OD-P16C-10` — Concrete Batch-Capacity Parameters

**Status: OPEN — ELECTION-GOVERNED CONFIGURATION**

**CORRECTED.** The previous wording required that _"`C` must exceed the
maximum plausible per-window accepted-ballot count"_. That criterion is
**withdrawn**: it contradicts the accepted architecture, in which capacity
is derived from a finite upper bound and never from expected, historical or
plausible turnout.

**Decision already fixed by architecture.** Capacity planning must use a
finite upper-bound model derived from:

```text
E          maximum number of valid anonymous continuation capabilities
K = 1      public evidentiary challenges per continuation capability
A = 1      accepted cast ballots per continuation capability
L_max      = E x (K + A) = E x 2
           the number of scheduled publication intervals
           fixed primary and predeclared reserve batch capacity
           cast-reserved and public-challenge-reserved slot partitions
           the governed incident and election-extension model
```

**Still open — the concrete numeric values of:**

```text
interval duration        N
primary batch capacity   C
reserve commitments      R
cast / challenge slot partition
operational safety reserve
```

**Constraint.** These values **must not be based solely on expected,
historical or plausible turnout**. They must be selected **before election
opening**, published as governed election configuration, and validated
against the finite upper-bound model (`TC-59`, `TC-64`).

**Owner.** Election governance, with PACK-16D implementation analysis and
PACK-17 independent verification.

**Activation effect.** **Blocks production activation** until concrete
election parameters are demonstrated to satisfy the capacity model.
`election.capacity_plan_invalid` and `FM-16C-30` are the enforcement path.

| ID       | Rule                                                                                                                                                                                                                                                                                     |
| -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `OD-R13` | **A plausible-load criterion is not a capacity criterion**, and no PACK-16C document may reintroduce one. `TC-60` is the governing rule                                                                                                                                                  |
| `OD-R14` | **Trade-offs among the open numbers are stated, not hidden:** a shorter `N` worsens the acceptance-time resolution at closure (`T-P16C-46`), a longer `N` worsens the publication obligation (`PA-10`), and a mis-sized partition refuses checks while cast capacity idles (`T-P16C-53`) |
| `OD-R15` | **Capacity is never adjusted during an election** (`TC-24`, `TC-69`), so these numbers are a pre-opening decision or they are wrong for the whole election                                                                                                                               |

---

## 2. What each entry blocks, collected

```text
BLOCKS PRODUCTION IMPLEMENTATION ACCEPTANCE
   OD-P16C-01   atomic boundary mechanism
   OD-P16C-12   external witness cosigning
   OD-P16C-17   leaf reservation storage and atomicity

BLOCKS BINDING USE OF A CONTEXT
   OD-P16C-08   independent reference verifier engaged
   OD-P16C-07   offline verification bundle (via BM-28)
   OD-P16C-16   opening and reconciliation format (via checks 17-21)

BLOCKS CERTIFICATION
   OD-P16C-09   verification-report governance
   OD-P16C-19   privacy-preserving per-capability reconciliation proof
                — ARCHITECTURAL BLOCKER if it cannot be constructed

BLOCKS A PROPERTY IN PRACTICE, WITHOUT BLOCKING THE ROUND
   OD-P16C-10   batch interval, capacity and partition sizing
   OD-P16C-11   split-view resistance
   OD-P16C-13   the publication-failure escalation window
   OD-P16C-18   capacity stress-testing thresholds

BLOCKS ONLY A CONTEXT THAT NEEDS THE FEATURE
   OD-P16C-02   write-ins

BLOCKS NOTHING AT SPECIFICATION STAGE
   OD-P16C-03   build attestation technology
   OD-P16C-04   serialization format
   OD-P16C-05   receipt encoding
   OD-P16C-06   QR policy
   OD-P16C-14   leaf-commitment construction
   OD-P16C-15   inclusion-proof wire format
```

### 2.0 What the capacity correction CLOSED

```text
CLOSED   whether public challenge publication is bounded
         ANSWERED: yes. Bounded per anonymous continuation capability.

CLOSED   the initial-profile K value
         ANSWERED: K = 1, an architectural constant of the protocol
         profile, not runtime configuration.        CH-37, CH-38

CLOSED   whether local diagnostic challenges occupy board leaves
         ANSWERED: no. They are not submitted, not committed, not
         published, not in the record, not events.  CH-39 ... CH-42, TC-58

CLOSED   the basic finite-capacity formula
         ANSWERED: L_max = E x (K + A) = E x 2, computed from the
         maximum number of VALID continuation capabilities, not from
         plausible turnout.                          TC-59, TC-60
```

| ID       | Rule                                                                                                                                                                                                                                                                           |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `OD-R11` | **These four are decided and may not be reopened as implementation choices.** PACK-16D may not raise `K`, may not publish local challenges, and may not plan capacity from expected turnout                                                                                    |
| `OD-R12` | **What remains is implementation-level and is named:** the commitment construction (`OD-P16C-14`), the per-capability reconciliation proof (`OD-P16C-19`), numeric `C` and `R` (`OD-P16C-10`), reservation storage (`OD-P16C-17`) and stress-testing thresholds (`OD-P16C-18`) |

### 2.0.1 Architectural closure versus numeric configuration

The two are different kinds of open, and conflating them is how a settled
architecture drifts back into being a preference.

```text
CLOSED ARCHITECTURAL QUESTIONS
  capacity must be finite
  capacity derives from E, K and A
  K = 1
  A = 1
  adaptive overflow is prohibited
  reserve commitments are predeclared
  a public challenge cannot consume a cast-reserved slot
  capacity exhaustion is fail-closed

OPEN CONFIGURATION QUESTIONS
  concrete N
  concrete C
  concrete R
  concrete slot partition
  concrete safety reserve for a specific election
```

| ID       | Rule                                                                                                                                                                                                     |
| -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `OD-R16` | **No architectural question in the left column is open.** Recording one as open would invite PACK-16D to re-decide it                                                                                    |
| `OD-R17` | **No numeric question in the right column is closed.** Declaring a value settled without a concrete election population and a governance decision would be a fiction, and `FM-16C-30` exists to catch it |

### 2.1 What the turnout correction CLOSED

```text
CLOSED   whether live turnout confidentiality is achieved by padding
         entries or by sealed commitments

         ANSWERED: fixed-cadence sealed fixed-capacity batch
         commitments (TC-* §4). The padding model is REJECTED and
         SUPERSEDED (TC-21). This question is not open and must not
         be reopened as an implementation choice.
```

| ID       | Rule                                                                                                                                                                                                                                                                                                                                                        |
| -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `OD-R09` | **Live-turnout confidentiality is no longer an open decision.** The model is selected; only its parameters (`OD-P16C-10`) and its encodings (`OD-P16C-14`…`OD-P16C-16`) remain. PACK-16D may not substitute a different turnout model                                                                                                                       |
| `OD-R10` | **Architecture-critical semantics are settled now, parameters later.** Cadence fixedness, gaplessness, non-adaptivity, capacity fixedness, leaf indistinguishability, cover-leaf non-ballot status, closure completeness and reconciliation are **specification-stage decisions and are made**. Interval, capacity and serialization are the only deferrals |

| ID       | Rule                                                                                                                                                                                                                                                                                      |
| -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `OD-R04` | **Nothing in this register blocks completion of the PACK-16C specification round**, and nothing in it is a reason to treat the round as incomplete. Every entry is a decision correctly deferred to a party better placed to make it                                                      |
| `OD-R05` | **Two entries could become blockers of a different kind.** `OD-P16C-01` becomes an `ARCHITECTURAL BLOCKER` if the guarantee cannot be demonstrated; `OD-P16C-12` becomes a permanent limitation on what may be claimed if no ecosystem emerges. Both are stated now, not discovered later |

---

## 3. Open decisions inherited and still open

**Listed for completeness. None is owned, advanced or closed by this round.**

| ID           | Question                                                                       | Owner                                                         | Status                                                           |
| ------------ | ------------------------------------------------------------------------------ | ------------------------------------------------------------- | ---------------------------------------------------------------- |
| `OD-P16A-04` | Verification library selection                                                 | PACK-16D                                                      | open                                                             |
| `OD-P16A-05` | Specification stewardship of the selected family                               | GOVERNANCE                                                    | open                                                             |
| `OD-P16A-06` | Formal / symbolic analysis of the composed EPD² profile                        | External review                                               | open — `TV-08`                                                   |
| `OD-P16A-09` | Scope-level reconciliation of the electronic and alternative channels          | GOVERNANCE                                                    | open — **cited repeatedly by this round as the coercion answer** |
| `OD-P15-05`  | The PACK-15 boundary constraint this round works inside                        | PACK-15 lineage                                               | open — `CN-30`…`CN-32`                                           |
| `VO-08`      | ElectionGuard 2.1 published parameter family versus BSI TR-02102-1 Remark 2.12 | **PACK-16B external cryptographic review**; assurance PACK-17 | **OPEN — not owned by PACK-16C**                                 |

| ID       | Rule                                                                                                                                                                                                                                      |
| -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `OD-R06` | **`OD-P16A-09` is cited by seven PACK-16C documents as the answer to a problem this round cannot solve.** That concentration is itself a finding: the electronic channel's coercion limits are not closable inside the electronic channel |
| `OD-R07` | **This section is a pointer, not a registry.** Each inherited entry remains defined in its own round's open-decisions document, with its status unchanged                                                                                 |

---

## 4. Counts

```text
PACK-16C open decisions                                  19
   blocking production implementation acceptance          3
   blocking binding use of a context                      3
   blocking certification                                 2
   blocking a property in practice only                   4
   blocking a feature-specific context only               1
   blocking nothing at specification stage                6
Opened by the turnout correction                          3   OD-P16C-14 … 16
Opened by the capacity correction                         3   OD-P16C-17 … 19
Narrowed by the turnout correction                        2   OD-P16C-10, OD-P16C-13
Architectural questions CLOSED by the turnout correction   1   §2.1
Architectural questions CLOSED by the capacity correction  4   §2.0
Inherited open decisions cited, not owned                 6
Inherited open decisions closed by this round             0
Open decisions re-owned by this round                     0
```

| ID       | Rule                                                                                                                                                                                                                                                                                                                  |
| -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `OD-R08` | **"Inherited closed by this round = 0" is correct and deliberate.** A specification round that closed inherited open decisions while adding its own would be moving problems rather than solving them. The one question this correction _did_ close is its own (§2.1), and closing it was the point of the correction |

---

## 5. What this document does not decide

```text
Everything in §1 — that is the point.
Priority and sequencing of the entries        → PACK-16D planning
Governance timelines                           → GOVERNANCE
```

**SPECIFIED. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY. NOT LEGALLY
ACTIVATED.**
