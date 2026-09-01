# PACK-16C — Specification Report

**Round:** PACK-16C — Casting, Receipt, Verification Client, Bulletin Board and Election Record. **Specification and ADR only. No code. No cryptographic implementation. Not implemented. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-101`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 0. What this round did

```text
PACK-16A chose the protocol.        EPD2-HOM-1, no revoting
PACK-16B fixed the parameters,      EPD2-CRYPTO-1, k of n guardians,
         the key and the ceremony.  no pre-closure decryption

PACK-16C specifies what happens between a person deciding to vote
and a stranger being able to check the result.
```

Thirty-three documents under `docs/packs/PACK-16/` and `ADR-101`. **No
code. No implementation. Nothing built, tested or reviewed.**

---

## 1. The three questions, and the answers

### 1.0 What the two corrections changed

```text
CORRECTION 1  turnout — padding entries rejected; fixed-cadence sealed
              fixed-capacity batch commitments adopted.

CORRECTION 2  bounded challenge and finite capacity — unlimited PUBLISHED
              challenges rejected; unlimited LOCAL checking preserved;
              K = 1 public evidentiary challenge per capability;
              L_max = E x (K + A) computed before the election opens;
              per-window reservation, predeclared reserves, cast-reserved
              slots and a fail-closed exhaustion path.

CORRECTION 3  event privacy and open-decision consistency — the
              capability-side half of each atomic boundary is no longer an
              event; capability.consumed and
              challenge.public_entitlement_consumed DELETED; the
              plausible-load capacity criterion WITHDRAWN and OD-P16C-10
              rewritten around E, K, A and L_max.
```

### 1.1 When is the continuation capability consumed?

**Inside an atomic acceptance boundary, after every cryptographic check has
passed, immediately before durable acceptance.**

```text
Stages 1–18   repeatable · nothing consumed · a failure costs a retry
Stages 19–22  ATOMIC · all or nothing · the only irreversible step
Stage 23      published · failure is public, never silent
```

Four orderings were compared. This one was selected because it is the only
one in which **a ballot that fails any check costs the voter nothing**, and
in which **nothing cryptographic happens after the capability is spent**.

**What it costs:** an exactly-once guarantee across two stores that must not
share a key. The semantics are specified (`CN-17`…`CN-20`); the mechanism is
`OD-P16C-01`, and **if PACK-16D cannot demonstrate it, that is an
`ARCHITECTURAL BLOCKER`, not a risk to accept.**

### 1.2 What may a voter be given afterwards?

**A receipt that proves publication and nothing else.**

It carries a confirmation code derived only from the ballot's encryptions
and `H_E`, the checkpoint current at issuance, and an honest publication
status. It carries no nonce, no opening, no credential, no board position
and no exact time. It is re-derivable from public data, so losing it costs
nothing and copying it proves nothing.

**What it costs:** a receipt **proves participation**. A coercer who demands
to see one learns the person voted. That is accepted, recorded, and not
solved by this design.

### 1.3 What must be published?

**Thirty-seven mandatory artefacts, sufficient for twenty-one checks, plus a
statement of the seven things the record cannot show.**

The completeness matrix joins the two lists in both directions: 31 artefacts
serve at least one check, 4 exist to make the record honest rather than
verifiable, and **no check lacks an artefact**.

**Before closure the record is a sequence of constant-size sealed batch
commitments and nothing else.** Checks 17–19 — cadence completeness, root
recomputation and reconciliation — exist only after closure, because the
openings that make them possible are what make occupancy public. That is the
turnout guarantee expressed as a limit on verification (`EC-14`).

---

## 2. Decisions taken

| Decision                      | Selected                                                                                                    | Alternatives rejected                                                                                                                                                                                        |
| ----------------------------- | ----------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Consumption point             | **Atomic validation + consumption + acceptance**                                                            | Consume on issue of intent; consume after publication; two-phase with compensation                                                                                                                           |
| Ballot identity               | **Four separated values** — `ballot_id`, `confirmation_code`, `board_sequence`, `internal_object_id`        | One identifier reused; server-assigned `ballot_id`; hash-derived `ballot_id`                                                                                                                                 |
| Challenge policy              | **Two-tier: unlimited local diagnostic checks + one public evidentiary challenge per capability (`K = 1`)** | Fixed probability; system-forced; **unlimited _published_ challenges — rejected on audit, no finite capacity bound**; rate-bounding instead of entitlement-bounding; a global rather than per-capability cap |
| Capacity planning             | **`L_max = E × (K + A) = E × 2`, from maximum valid continuations**                                         | Planning from plausible turnout; adaptive overflow batches; a hidden overflow queue                                                                                                                          |
| Capability-side observability | **Not an event.** Internal transactional state change with privacy-restricted audit evidence                | A `capability.consumed` event; a renamed `…_transition_completed` event that still crosses a bus                                                                                                             |
| Board structure               | **Merkle transparency log with chained signed checkpoints, mirror co-signing, published gossip**            | Signed flat log; database with audit table; blockchain                                                                                                                                                       |
| Pre-closure publication       | **One constant-size sealed batch commitment per fixed window**                                              | Individual ballot entries; padding entries; nothing at all until closure                                                                                                                                     |
| Publication                   | **Durable acceptance + signed commitment naming a batch window + closure opening**                          | Publish-then-accept; accept-and-hope; synchronous publication inside the boundary; an unbounded asynchronous deadline                                                                                        |
| Verification origin           | **Separate published origin**                                                                               | Same origin as the voting client; a native application                                                                                                                                                       |
| Turnout confidentiality       | **Fixed-cadence sealed fixed-capacity batch commitments, opened in full at closure**                        | Unpadded batches; **padding entries — rejected on audit**; withholding the board until closure; adaptive cadence; publishing per-window occupancy                                                            |

| ID       | Rule                                                                                                                                                                           |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `REP-01` | **Every rejected alternative is recorded with the reason it was rejected**, in the document that owns the decision. A selection with no visible alternatives is not a decision |

---

## 3. What this round did not solve, listed plainly

```text
0. THIS ROUND WAS CORRECTED. The first candidate's turnout model
   leaked the live figure, its API catalogue had no schemas, and its
   acceptance matrix had no traceability. All three are fixed here.
   The correction is recorded, not smoothed over.

1. A COERCER PRESENT WITH THE VOTER.
   Unsolved. The answer is a different channel (CB-07, OD-P16A-09).

2. THE CHALLENGE-TRANSCRIPT COERCION PATTERN.
   Named, not solved. Nothing in the record distinguishes it from
   honest use (CB-05, T-P16C-10).

3. BALLOT STUFFING, FROM THE RECORD ALONE.
   Structurally impossible to check without creating the link the
   design removes (VP-17, EC-09). The controls are PACK-15's.

4. SPLIT-VIEW RESISTANCE, CRYPTOGRAPHICALLY.
   Rests on ORGANISATIONAL mirror independence until external
   witnesses exist. The IETF's own gossip work expired without
   becoming an RFC (G-03, G-05, AO-13).

5. VERIFICATION TAKE-UP.
   9.9 % at best in the most mature deployment (E-29). Detection is
   probabilistic across the electorate; no per-voter guarantee follows.

6. NETWORK-LAYER CORRELATION.
   Reduced and bounded, not eliminated (T-P16A-04, RB-16C-01).

7. THE OPERATOR WITH ACCESS TO BOTH STORES.
   The boundary's two halves share no key and no trace, but an
   operator with database access to both plus precise timing remains
   a stated residual (T-P16C-28).

8. LOST PARTICIPATION AFTER A PUBLICATION FAILURE.
   If the boundary commits and publication then fails past every
   window, the participation is lost. The record's integrity is
   chosen over repairing it, deliberately (PA-08, PA-09).

9. ACCEPTANCE-TIME RESOLUTION AT CLOSURE.
   Once the batches are opened, a ballot's acceptance is localised to
   one interval. Strictly less than a running total; not nothing
   (T-P16C-46, RB-16C-11).

10. COVER-LEAF GENERATOR QUALITY.
    A weak generator would break leaf indistinguishability silently,
    before closure, with nothing published revealing it. This is the
    sharpest new implementation risk (T-P16C-45, RB-16C-10).

11. THE PER-CAPABILITY BOUND IS ONLY AGGREGATE-CHECKABLE.
    A public verifier can check that accepted casts <= E and public
    challenges <= E x K. Proving that EACH capability contributed at
    most one of each needs privacy-preserving evidence this round
    could not construct. Recorded as OD-P16C-19, an ARCHITECTURAL
    BLOCKER for certification if it proves impossible.

12. A MALICIOUS CLIENT CAN FAKE A LOCAL DIAGNOSTIC CHALLENGE.
    Moving unlimited checking to an unpublished local tier removes
    board exhaustion and returns exactly this to the attacker. The
    one public audit challenge is what remains to catch it
    (T-P16C-62, T-P16C-63).

13. A LEAKED LEAF RESERVATION SHRINKS REAL CAPACITY SILENTLY,
    with no public sign until the closure reconciliation
    (T-P16C-57, RB-16C-13).

14. L_max SCALES WITH E. An issuance policy that over-issues
    capabilities inflates the plan and the record with it
    (T-P16C-51, RB-16C-12).
```

| ID       | Rule                                                                                                                                                                                                                                        |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `REP-02` | **None of the eight is softened anywhere in the pack.** Each appears in the document that owns it, in the threat model, in the acceptance matrix, and — where a voter is affected — in participant-facing text before the irreversible step |

---

## 4. What was found while writing

| Finding                                                                                                                                                                                                                                    | Where it went                                                          |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------- |
| **A public append-only board is a live turnout feed by construction.** Removing a counter endpoint does not remove the number                                                                                                              | `TC-01`, `TC-02`; fixed-cadence sealed batch commitments               |
| **A padding entry that carries no ciphertext does not hide occupancy — it labels it.** The first candidate's model was structurally, not numerically, wrong                                                                                | `TC-21` — the correction; rejected and superseded                      |
| **Absence of a scheduled publication is itself a disclosure**, so empty windows must publish too                                                                                                                                           | `TC-25`, `FM-16C-18`                                                   |
| **A named batch window turns an unbounded publication promise into a bounded one**, and lets a voter detect non-publication _during_ voting                                                                                                | `PA-10`, `PA-12`, `DP-19`                                              |
| **A fixed capacity is not a bound unless the number of publication-bearing artefacts is provably finite.** Unlimited published challenges against finite `C` is not a bound at all                                                         | `CH-36`, `TC-59` — the capacity correction                             |
| **Benaloh's repeatability and public evidence were doing two different jobs in one action.** Separating them keeps unlimited checking _and_ yields a finite bound                                                                          | `CH-36`, §1A                                                           |
| **A reserve batch that appears only under load announces that the interval was busy**, so reserves must publish on schedule whether used or not                                                                                            | `TC-67`, `T-P16C-54`                                                   |
| **Accept-then-find-room is the same class of error as accept-now-verify-later**, and is prohibited for the same reason                                                                                                                     | `TC-70`, `VP-00`                                                       |
| **The canon has no primitive for a public ballot-bearing board**, because its only append-only public primitive correctly prohibits touching vote envelopes                                                                                | `CQ-P16C-01`, `CAM-P16C-01` — recorded as a gap, not filled by analogy |
| **Certificate Transparency — the most deployed transparency-log ecosystem — has never standardised split-view detection.** RFC 6962 deferred it in 2013, RFC 9162 declared it out of scope in 2021, and the IETF gossip draft died in 2020 | `G-03`, `G-05`, `AO-13`, `OD-P16C-12`                                  |
| **RFC 6962's Maximum Merge Delay is a decade-old precedent for a signed promise to publish by a deadline**                                                                                                                                 | `G-02`; `PA-*` is adapted from it, not invented                        |
| **A distributed trace spanning the atomic boundary reconstructs exactly the link the architecture removes**                                                                                                                                | `EV-06` — tracing prohibited across the boundary                       |
| **An event that names the capability it just spent is a correlation identifier wearing a domain name.** The capability-side half of an atomic boundary should never have been an event                                                     | `EV-71`, `EV-74` — the event-privacy correction                        |
| **"Capacity must exceed the plausible load" is a preference, not a criterion**, and leaving it in an open decision quietly reopened a closed architectural question                                                                        | `OD-R13`, `OD-R16` — the open-decision correction                      |
| **A spoiled ballot's opening and a cast ballot's absence of one must be separated at the data-model level**, not by a conditional                                                                                                          | `DM-11`, `ER-08`                                                       |
| **Six of this round's central decisions rest on no external source at all**                                                                                                                                                                | `G-R04` — stated, not disguised as evidenced                           |

---

## 5. Counts

```text
Documents written                                    33
ADR                                                   1   ADR-101, status `proposed`
Casting flow steps                                   22
Validation pipeline stages                           23
Ballot lifecycle states                              16   `published` has two phases
Election record artefacts                            37
Independent verifier checks                          21
Board entry types                                    21
Reason codes defined                                 88
Reason codes reused without redefinition              7
Failure modes                                        34
Threats added                                        57
Data models                                          16   plus 6 data-model rules
API operations                                       26   9 casting · 1 client-local ·
                                                          10 board · 6 batch/capacity
   each with all sixteen required fields             26
Events                                               36   `EV-15` and `EV-19b` deleted;
                                                          identifiers retired, not reused
Open decisions opened                                19
Inherited open decisions closed                       0
Architectural questions closed by correction 1        1   live-turnout confidentiality
Architectural questions closed by correction 2        4   bounded publication · K · local
                                                          challenges · capacity formula
Evidence entries defined                              5
New primary sources read first-hand                   4
Acceptance rows                                     223
   SATISFIED                                        189
   PARTIALLY SATISFIED                               10
   DEFERRED                                          11
   BLOCKED                                            3
   NOT APPLICABLE                                    10
Canon clarifications recorded                         8
Canon amendments proposed                             0
FIR statuses changed                                  0
Lines of code written                                 0
```

---

## 6. What must happen before any of this is used

```text
1. External cryptographic review of the composed EPD² profile
                                              OD-P16A-06 / TV-08
2. Resolution of VO-08                        PACK-16B external review
3. Demonstration of the atomic boundary       OD-P16C-01, PACK-16D
4. An independent verifier, not written or commissioned by EPD²,
   verifying a real context — including checks 17-21
                                              BM-28, OD-P16C-08, OD-P16C-16
4a. A privacy-preserving construction for the per-capability bound,
    or a declaration that none exists      OD-P16C-19, PACK-16D, PACK-17
5. Accessibility acceptance with assistive technology, per context
                                              XA-29
6. Legal assessment                           OD-P16A-11
7. Governance decision on the alternative channel
                                              OD-P16A-09
```

**Eight gates. None is closed by this round or by either correction, and
none may be closed by assertion.**

---

## 7. Verdict

```text
PACK-16C SPECIFICATION AND ADR — COMPLETE AS A SPECIFICATION ROUND.

NOT A PASS.
NOT AN IMPLEMENTATION CANDIDATE.
NOT PRODUCTION READY.
NOT LEGALLY ACTIVATED.
PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.

ADR-101 status: proposed. It stays proposed.
```

**SPECIFIED. REQUIRES EXTERNAL REVIEW.**
