# PACK-16C — Turnout Confidentiality Model

**Round:** PACK-16C — Casting, Receipt, Verification Client, Bulletin Board and Election Record. **Specification and ADR only. No code. No cryptographic implementation. Not implemented. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-101`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

**CORRECTED.** The first PACK-16C candidate selected *fixed-size batches
with padding entries*. That model was **rejected on audit** and is retired
in §3. The active model is **fixed-cadence sealed fixed-capacity batch
commitments**, §4.

---

## 0. The inherited prohibition

PACK-16A's `NIT-01`…`NIT-07` prohibit intermediate tallies. **PACK-16C
inherits that unchanged and extends it**, because a public append-only board
leaks turnout by existing — the count of entries *is* a turnout figure.

```text
NO intermediate result.
NO intermediate turnout.
NO live participation counter.
NO derivable proxy for any of the above.

The prohibition is on the INFORMATION, not on the endpoint.
```

| ID       | Rule                                                                                                              |
| -------- | --------------------------------------------------------------------------------------------------------------------- |
| `TC-01`  | **Removing an endpoint that returns a count is not compliance.** If the number is derivable from what is published, it is published (`NIT-04` lineage) |
| `TC-02`  | **The board is the hardest case in the whole design**, because publishing ballots as they are accepted is exactly a live turnout feed. Everything in §4 exists to break that equivalence |

---

## 1. Why intermediate turnout is harmful

| Harm | Mechanism |
| ---- | --------- |
| **Strategic mobilisation** | A faction that can see participation lagging can target activation in the closing hours |
| **Strategic abstention** | Visible turnout changes the calculus of whether voting is worth it |
| **Coercion enforcement** | A coercer who can watch a small context's counter learns whether the people they control have complied |
| **Re-identification in small contexts** | With few voters, a counter that moves at a known moment identifies a person |
| **Pressure on the process** | A visible counter invites "get it up" behaviour from organisers, which is participation pressure by another name |

| ID       | Rule                                                                                                          |
| -------- | ----------------------------------------------------------------------------------------------------------------- |
| `TC-03`  | **The fourth harm is the sharpest and the least discussed.** In an EPD² context of a few dozen members, a moving counter and a known schedule are close to a participation register |

---

## 2. Mechanisms retained from the first model

### 2.1 Fixed cadence

| ID       | Rule                                                                                                          |
| -------- | ----------------------------------------------------------------------------------------------------------------- |
| `TC-04`  | **Nothing about a ballot is published individually on acceptance.** The unit of pre-closure publication is a **batch window**, never a ballot (`BB-11` lineage, `PA-*`) |
| `TC-05`  | **Batch windows are on a fixed, published cadence, frozen before voting opens.** Under the corrected model the cadence is **not** randomised and **not** adaptive — see `TC-23` and `TC-24`, which supersede the first candidate's randomised-boundary rule |
| `TC-06`  | **Board position never encodes arrival order.** Under the corrected model this is realised by randomised leaf-index assignment inside a batch (`TC-31`) rather than by shuffling a list of published entries |

### 2.2 Not publishing counts

| ID       | Rule                                                                                                          |
| -------- | ----------------------------------------------------------------------------------------------------------------- |
| `TC-07`  | **No accepted-count, submitted-count, rejected-count, challenge-count or participation-rate is published before the closure checkpoint** — not in an API, not in a UI, not in an admin view, not in a metrics endpoint reachable from outside the operating principal |
| `TC-08`  | **No per-voter participation flag exists anywhere that is queryable** — not "has this member voted", not by an administrator, not by the member's own organisation. The system does not hold that fact in a form that can be asked (`CC-04`) |
| `TC-09`  | **Progress indication to a voter is about their own ballot only**, and never about the election's state |

---

## 3. The rejected model — `SUPERSEDED`, retained for the record

```text
REJECTED — SUPERSEDED — NOT ACTIVE PROFILE

TC-10  padding entries are a catalogued board entry type
TC-11  a padding entry carries no ciphertext
TC-12  padding bounds the leak but does not eliminate it
TC-13  where a context is too small for padding, the answer is TC-16

These four identifiers are RETIRED. They define nothing in the active
profile, they support no claim, and they must not be cited except as
history. They are not re-pointed at the new model.
```

**Why the model failed.**

| # | Defect |
| - | ------ |
| 1 | **The entry type was never catalogued.** `TC-10` asserted a catalogued padding entry type; `PACK-16C-BULLETIN-BOARD-ENTRY-CATALOG.md` contained none, and the catalogue was closed to new types without an ADR. The specification contradicted itself |
| 2 | **A padding entry without a ciphertext is structurally distinguishable from an accepted ballot.** An observer counts the entries that carry a ciphertext and has the live turnout figure exactly. `TC-11` did not hide occupancy — it labelled it |
| 3 | **Therefore the inherited invariant `NO TURNOUT DISCLOSURE BEFORE CLOSURE` was not satisfied**, and `TC-12`'s "bounds the leak" was an over-claim: the leak was not bounded, it was open |
| 4 | **Padding exhaustion leaked more sharply than no padding at all** — a full batch and an over-full interval are distinguishable events |

| ID       | Rule                                                                                                          |
| -------- | ----------------------------------------------------------------------------------------------------------------- |
| `TC-21`  | **The failure was structural indistinguishability, not sizing.** No choice of padding volume repairs a scheme in which real and cover entries have different shapes. The corrected model makes them **the same object** (`TC-29`) |

---

## 4. The active model — fixed-cadence sealed fixed-capacity batch commitments

```text
Before closure the public bulletin board publishes NO individual
accepted-ballot entry and NO count of accepted ballots.

At each fixed batch window it publishes ONE entry:

    sealed_batch_commitment

a commitment to a FIXED-CAPACITY batch of C commitment leaves,
revealing nothing about how many of those leaves are real.
```

### 4.1 Cadence and capacity

| ID       | Rule                                                                                                          |
| -------- | ----------------------------------------------------------------------------------------------------------------- |
| `TC-22`  | **Governance fixes, before voting opens and immutably thereafter:** the batch interval, the batch capacity, the first pre-closure publication time, the last pre-closure publication time, the late-batch rule and the empty-batch rule. These are governed configuration published with the manifest (`FIR-CONFIG-001`) |
| `TC-23`  | **The cadence is fixed and public.** One `sealed_batch_commitment` every interval, from the first publication time to the last, with **no gaps** |
| `TC-24`  | **Adaptive cadence is prohibited.** The interval, the capacity and the schedule may never be changed in response to turnout, load, traffic shape or any observed property of the election. A cadence that reacts to participation *is* a turnout channel (`T-P16C-39`) |
| `TC-25`  | **A batch window with zero accepted ballots still publishes its commitment**, indistinguishable from a full one. **Absence of an entry is itself a disclosure**, so absence is not permitted |
| `TC-26`  | **Interval `N` and capacity `C` are election configuration parameters with normative bounds, not values chosen in this document.** `N` must be short enough that a ballot's publication obligation is bounded (`PA-*`). **`C` is derived from the provable upper bound of §4.9, not from a plausible load** — the first candidate's *"C exceeds the maximum plausible load"* was a hope, not a bound, and is superseded by `TC-59` and `TC-60`. Concrete values are election-governed configuration and are settled before opening (`OD-P16C-10` §1.1) |

### 4.2 Commitment leaves

A batch is exactly **`C` commitment leaves**, indexed `0 … C−1`.

**A real leaf** commits to one **ballot artefact** — an accepted ballot or a
spoiled (challenged) ballot — with at least:

```text
election_context_id
public ballot reference (ballot_id)
encrypted-ballot hash
confirmation_code
canonical envelope digest
acceptance record digest
random commitment salt
```

**A cover leaf** is a cryptographically random value drawn uniformly from
the same space, of the same length and format as a real leaf's commitment
output.

| ID       | Rule                                                                                                          |
| -------- | ----------------------------------------------------------------------------------------------------------------- |
| `TC-27`  | **A leaf is a hiding commitment.** A real leaf is the output of the domain-separated hash of the fields above under a high-entropy random salt, so the leaf reveals nothing about the ballot without its opening |
| `TC-28`  | **A cover leaf is a uniformly random value of the leaf's exact size.** It is not a hash of anything, has no preimage, and is generated by the same randomness discipline PACK-16B specified |
| `TC-29`  | **Before closure, real and cover leaves are structurally indistinguishable in the published commitment.** Same size, same format, same position semantics. **This is the property the rejected model lacked** |
| `TC-30`  | **The commitment root is a Merkle root over exactly `C` leaves in leaf-index order**, so the root's size and shape are independent of how many leaves are real |
| `TC-31`  | **Leaf indices are assigned to accepted ballots by a per-batch random assignment.** Index does not encode arrival order, and the assignment randomness is never published — only the resulting mapping is, at closure (`TC-06`) |
| `TC-32`  | **A cover leaf is not a ballot.** It is not accepted, is not eligible for tally, contains no ciphertext, consumes no continuation capability, produces no receipt, and creates no ballot state anywhere in `BL-*` |
| `TC-57`  | **A leaf has exactly one class, bound privately at reservation and revealed only at closure:** `accepted_cast`, `public_challenged_spoiled` or `cover`. **Public evidentiary spoiled ballots occupy leaves too**, so that challenge activity — which is participation activity — is no more visible before closure than casting is (`CH-32`). Before closure the three classes are indistinguishable, and **no pre-closure commitment distinguishes cast from challenge in any way** (`BE-24`) |
| `TC-58`  | **Local diagnostic challenges occupy no leaf.** They are not submitted, not committed, not published and not in the record (`CH-39`…`CH-42`). Only publication-bearing artefacts — accepted casts and public evidentiary challenges — consume capacity |

### 4.3 The pre-closure board entry

The catalogued entry type is `sealed_batch_commitment` (`BE-*`).

**Public fields, and only these:**

```text
election_context_id        batch_sequence
batch_window_id            fixed_capacity_profile_id
commitment_root            previous_checkpoint reference
schema_version             signature
checkpoint linkage
```

**Prohibited fields:**

```text
real ballot count          leaf occupancy bitmap
individual ballot hash     confirmation code
acceptance timestamp       capability reference
identity data              any value whose size or presence
                           varies with occupancy
```

| ID       | Rule                                                                                                          |
| -------- | ----------------------------------------------------------------------------------------------------------------- |
| `TC-33`  | **The entry's serialized size is constant across batches**, because every field is fixed-width or drawn from a fixed profile. A size that varied with occupancy would restore the leak the model removes (`T-P16C-41`) |
| `TC-34`  | **`fixed_capacity_profile_id` names a published profile, not a number computed per batch.** All batches in a context share one capacity profile |
| `TC-35`  | **The entry is signed and chained into the checkpoint sequence** exactly as every other board entry (`AO-*`), so a missing or late batch commitment is publicly detectable |

### 4.4 Individual verification before closure

**A voter must be able to check `recorded-as-cast` before closure without
anyone learning batch occupancy.**

A voter holding a confirmation code obtains a **privacy-safe commitment
inclusion proof**:

```text
this confirmation reference belongs to a committed leaf
in sealed batch B, under commitment root R,
signed at checkpoint K
```

| ID       | Rule                                                                                                          |
| -------- | ----------------------------------------------------------------------------------------------------------------- |
| `TC-36`  | **The lookup is by confirmation code and by nothing else.** No identity, no credential, no capability, no account, no terms (`API-20`) |
| `TC-37`  | **The response carries the voter's own leaf opening and a Merkle inclusion path.** The path consists of sibling leaf hashes, every one of which is a fixed-size value that is either a hiding commitment or a uniform random value — so the path **reveals nothing about occupancy** |
| `TC-38`  | **No public API enumerates real leaves before closure.** There is no operation that lists occupied indices, counts them, or returns a leaf opening for a code the caller does not hold (`API-34`) |
| `TC-39`  | **The lookup must not become an occupancy oracle.** Confirmation codes are high-entropy and unguessable; the operation is rate-limited under `API-*`'s policy; and the response for an absent code is indistinguishable in shape and timing from the response for a code in a batch the caller may not yet query (`T-P16C-42`) |
| `TC-40`  | **The lookup reveals nothing beyond the voter's own leaf**: not identity, not credential, not capability, not the exact acceptance timestamp, not any other occupant of the batch, and not the real occupancy count |

**Residual, stated:** a party that already holds many voters' confirmation
codes can learn that those specific ballots are committed. That party
already knows those people participated — a receipt proves participation
(`RE-14`) — so the lookup transfers no new information to them. It does
**not** let them learn the occupancy of leaves they hold no code for.

### 4.5 Closure reveal and reconciliation

At a valid `election_closed`, the board publishes for **every** batch
window:

```text
sealed_batch_opening        every leaf opening, real and cover,
                            in leaf-index order
                            + the leaf-index → ballot mapping
                            + every real leaf's salt and committed fields
                            + every cover leaf's value

batch_reconciliation_record occupancy declaration per batch,
                            per-batch and global totals,
                            and the mapping to accepted-ballot artefacts
```

together with all accepted encrypted ballots and their canonical public
references (`ER-*`).

| ID       | Rule                                                                                                          |
| -------- | ----------------------------------------------------------------------------------------------------------------- |
| `TC-41`  | **Every batch root must recompute** from its published opening. A root that does not recompute is `INCOMPLETE_RECORD` at minimum and blocks certification (`IV-*`) |
| `TC-42`  | **Every ballot artefact must map to exactly one occupied leaf, and every occupied leaf to exactly one ballot artefact of its declared class.** Neither direction may fail, and neither may be many-to-one. An `accepted` leaf maps to an accepted ballot; a `spoiled` leaf maps to a published opening |
| `TC-43`  | **Neither a cover leaf nor a spoiled leaf may become tally-eligible**, and the reconciliation states, per batch, the count in each class and that only `accepted` leaves entered the tally |
| `TC-44`  | **Every scheduled batch window must be accounted for.** A window with no published commitment, or a commitment with no published opening, makes the record incomplete (`EC-*`) |
| `TC-45`  | **Selective opening is prohibited.** A batch is opened in full or the record is incomplete; there is no partial opening, no withheld leaf and no "opening on request" |

**After closure the total accepted-ballot count is public**, as the election
record model already requires. Turnout becomes public **at closure and not
before**.

### 4.6 No change to the ballot or tally profile

```text
The sealed batch commitment layer does not modify
the ElectionGuard encrypted-ballot format,
the ciphertext structure,
the proof system,
the parameter profile EPD2-CRYPTO-1,
or the homomorphic tally.
```

| ID       | Rule                                                                                                          |
| -------- | ----------------------------------------------------------------------------------------------------------------- |
| `TC-46`  | **The commitment layer sits strictly above the ballot layer.** It commits to *digests of* ballot artefacts; it never alters, wraps or re-encodes a ballot |
| `TC-47`  | **Cover leaves exist only on the publication-commitment layer.** They never appear in an encrypted ballot, a ballot acceptance record, the `eligible_for_tally` set, the homomorphic accumulation, any decryption, or the plaintext tally |
| `TC-48`  | **A conforming ElectionGuard 2.1 verifier reads the ballots and the tally exactly as before.** The commitment layer adds checks; it removes none and changes none (`IV-*`) |

### 4.7 Why this is not a ballot-stuffing channel

| ID       | Rule                                                                                                          |
| -------- | ----------------------------------------------------------------------------------------------------------------- |
| `TC-49`  | **Only an accepted ballot backed by an atomically consumed continuation capability can occupy an `accepted` leaf.** Occupancy is written inside the same acceptance path, after the boundary commits (`CN-*`, `PA-*`). A `spoiled` leaf consumes no capability and can never be reclassified as `accepted` |
| `TC-50`  | **A cover leaf cannot be converted into an accepted ballot after its batch commitment is published.** Doing so would require finding a preimage of a uniformly random value under the leaf commitment construction — a second-preimage break, not an operational choice |
| `TC-51`  | **Closure reconciliation binds every real leaf to a durable `BallotAcceptanceRecord`** by the acceptance record digest committed inside the leaf (`TC-27`) |
| `TC-52`  | **The accepted-ballot count must equal the unique consumed-capability acceptance count** in restricted audit evidence held by the Independent Auditor. **This is a comparison of two counts produced independently by two stores, not a join between them** — the evidence carries totals and per-batch subtotals, never a pairing, and therefore cannot reconstruct identity-to-ballot linkage (`DM-10`, `PM-03`) |
| `TC-83`  | **The per-capability bound is checked, and its construction is an open question stated as one.** A verifier can check publicly that `accepted_cast ≤ E` and `public_challenged_spoiled ≤ E × K`. Checking that **each individual capability** contributed at most one of each requires privacy-preserving restricted reconciliation evidence that does not publish a capability-to-artefact mapping. **This round does not specify that construction**; it is `OD-P16C-19`, owned by PACK-16D with independent review by PACK-17, and it is recorded as a gap rather than claimed as solved (`IV-19`, `IV-20`) |
| `TC-53`  | **An independent verifier rejects any tally input not mapped to a valid committed accepted-ballot artefact.** A ballot that appears in the tally but in no pre-closure commitment is a late insertion and is `TALLY_MISMATCH` (`IV-*`) |

**What this does and does not buy.** `TC-49`…`TC-53` make **late insertion**
detectable and make **cover-to-real conversion** infeasible. They do **not**
make ballot stuffing at the *issuance* boundary detectable from the record —
that limit is `VP-17` and is unchanged.

### 4.8 Failure handling

Every sealed-batch failure case is specified in
`PACK-16C-FAILURE-AND-ABORT-MATRIX.md` (`FM-16C-18`…`FM-16C-27`) with a
detection point, a system action, a voter-facing action, capability and
ballot state, publication state, audit evidence and an election-level
consequence.

| ID       | Rule                                                                                                          |
| -------- | ----------------------------------------------------------------------------------------------------------------- |
| `TC-54`  | **No silent repair.** A missing, late, mismatched or unopenable batch is published as such. There is no operation that re-issues a commitment, back-dates a window, or quietly re-derives a root |

### 4.9 The provable finite capacity bound

**This is the section the first candidate did not have.** A fixed capacity
`C` is only a bound if the number of publication-bearing artefacts is
provably finite.

```text
E = the maximum number of continuation capabilities that may be VALID for
    this election under the eligibility snapshot and the issuance policy

K = the maximum number of PUBLIC EVIDENTIARY CHALLENGES per capability
    fixed by the protocol profile

A = the maximum number of ACCEPTED CAST BALLOTS per capability

Initial profile:  K = 1,  A = 1

L_max = E × (K + A) = E × 2
```

| ID       | Rule                                                                                                          |
| -------- | ----------------------------------------------------------------------------------------------------------------- |
| `TC-59`  | **`L_max` is the maximum number of publication-bearing real leaves the election can produce**, and it is computable **before voting opens**, from `E` and the profile constants alone |
| `TC-60`  | **`E` comes from the eligibility snapshot and the issuance policy, not from expected or plausible turnout.** Capacity is planned against every capability that *could* be used, because a capacity plan that assumes turnout fails exactly when turnout surprises it |
| `TC-61`  | **`K` and `A` are profile constants** (`CH-37`). A deployment cannot widen `L_max` by configuration; widening it requires a new protocol-profile version and a recomputed plan (`CH-38`) |
| `TC-62`  | **Cover leaves are not publication-bearing and are not counted in `L_max`.** They are what the plan pads *with*; they consume no entitlement and represent no artefact (`TC-32`) |
| `TC-63`  | **Only explicitly enumerated system leaves may be added to `L_max`, and only if they genuinely occupy the same batches.** Checkpoint metadata, board entries and incident notices are **not** leaves and must not be mixed into this arithmetic |
| `TC-64`  | **Total scheduled real-leaf capacity across the election must satisfy** `Σ C_interval ≥ L_max + operational safety reserve`, where the reserve is a published governed figure. A plan that does not satisfy it is `election.capacity_plan_invalid` and the context is **not activated** |
| `TC-65`  | **The privacy shape may not depend on the bound being tight.** Whether `L_max` is reached, approached or barely touched, the published cadence, capacity and entry shape are identical (`TC-29`, `TC-33`) |

### 4.10 Per-window capacity, reservation and predeclared reserves

Total election capacity is not enough: a single window can overflow while
the election as a whole has room.

**Predeclared reserve commitments.**

```text
For every publication interval, governance predeclares:

    1 primary batch commitment       capacity C_primary
    R reserve batch commitments      capacity C_reserve each

    C_interval = C_primary + R × C_reserve

ALL of them are published on schedule, EVEN WHEN EMPTY, with fixed
capacity and indistinguishable public structure.
```

| ID       | Rule                                                                                                          |
| -------- | ----------------------------------------------------------------------------------------------------------------- |
| `TC-66`  | **`C_primary`, `C_reserve`, `R` and the interval count are fixed before the election opens** by governance, from the `§4.9` bound, and are published with the manifest (`TC-22`) |
| `TC-67`  | **Every predeclared reserve commitment is published on schedule whether it is used or not.** A reserve that appears only under load is an activity signal, and its appearance would announce a busy interval (`T-P16C-54`) |
| `TC-68`  | **Adaptive creation of an unscheduled batch is prohibited**, at any time, for any reason, by any authority. `publication.unscheduled_batch_prohibited` |
| `TC-69`  | **`R` may not be increased after the election opens**, and `C` may not be enlarged. Both are part of the published shape |

**Atomic leaf reservation.**

| ID       | Rule                                                                                                          |
| -------- | ----------------------------------------------------------------------------------------------------------------- |
| `TC-70`  | **No publication-bearing submission is durably accepted without an atomically reserved leaf slot** in the current window or in a predeclared reserve window for that interval. **Accept-then-find-room is prohibited** (`CN-42`, `CN-43`) |
| `TC-71`  | **Reservation is inside the acceptance boundary and is released on any fail-closed rejection.** A reservation that outlives a rejected submission is a leak and is a defect (`T-P16C-57`) |
| `TC-72`  | **Reservations carry a timeout.** An unclaimed reservation is released so that a crashed client cannot silently consume capacity |
| `TC-73`  | **Reservation state is anonymous.** It binds a slot to a submission in flight, never to a capability, an identity or a voter (`CN-36`) |

**Capacity partition — cast slots are protected.**

| ID       | Rule                                                                                                          |
| -------- | ----------------------------------------------------------------------------------------------------------------- |
| `TC-74`  | **Each interval's capacity is partitioned in advance** into `cast-reserved` slots, `public-challenge-reserved` slots and, optionally, a `shared emergency reserve`. The partition is published with the manifest |
| `TC-75`  | **A public evidentiary challenge may never consume a cast-reserved slot.** Checking may never crowd out voting (`T-P16C-53`) |
| `TC-76`  | **Unused challenge-reserved slots stay cover leaves.** They are never adaptively converted into cast capacity, because a conversion visible in the published shape would be an activity signal (`T-P16C-54`) |
| `TC-77`  | **Any use of the shared emergency reserve is defined in advance and does not change the public batch shape.** If it cannot be used without changing the shape, it does not exist |

**Window-overflow rule.**

```text
If every predeclared slot allowed to a submission in the current interval
is unavailable, the submission is NOT ACCEPTED.

The system:
  fails closed for new publication-bearing submissions
  pauses new public evidentiary challenges immediately
  preserves unused cast entitlements
  preserves prepared local ballot state where safe
  issues a privacy-safe, election-wide capacity incident
  enters the governed pause / extension procedure
```

| ID       | Rule                                                                                                          |
| -------- | ----------------------------------------------------------------------------------------------------------------- |
| `TC-78`  | **Indefinite retry is not a remedy for a cast submission.** The election-level remedies are: pause voting; extend the election after governed approval; activate predeclared future capacity **only if it is already part of the published schedule**; or declare the election uncertifiable, abort, or re-run (`FM-16C-29`) |
| `TC-79`  | **Prohibited under exhaustion, categorically:** silently creating an unscheduled batch; silently enlarging `C`; dropping a challenged artefact; accepting a cast ballot without a committed leaf; moving an artefact to a hidden queue without a bounded publication commitment |
| `TC-80`  | **There is no hidden overflow queue.** Every publication-bearing artefact is either reserved into a scheduled leaf or was never accepted (`T-P16C-55`) |
| `TC-81`  | **A capacity incident publishes no occupancy, no remaining-slot count and no turnout figure.** It states that capacity is constrained, that publication-bearing submissions are paused, and what happens next — nothing more (`T-P16C-58`, `RN-16C-32`) |
| `TC-82`  | **The capability state of a failed reservation is unchanged.** Nothing is consumed, no entitlement is spent, and the voter's cast entitlement survives (`CN-39`, `CN-42`) |

---

## 5. Closure

| ID       | Rule                                                                                                          |
| -------- | ----------------------------------------------------------------------------------------------------------------- |
| `TC-14`  | **Turnout becomes public at closure and not before**, together with the count reconciliation, because the tally requires the set to be public |
| `TC-15`  | **Nothing about the closing moment is early.** The closure checkpoint is the first artefact from which turnout is exactly derivable, and it is published after the voting window has ended |

---

## 6. Small contexts

| ID       | Rule                                                                                                          |
| -------- | ----------------------------------------------------------------------------------------------------------------- |
| `TC-16`  | **A minimum electorate size is a precondition for electronic activation of a context.** Below it, the anonymity set is too small for any mechanism in §4 to protect anyone, and the context uses a different channel (`CB-07`, `OD-P16A-09`) |
| `TC-17`  | **Aggregate statistics are suppressed below a published threshold**, including challenge ratios, rejection counts by class, and any per-contest breakdown that would partition a small electorate |
| `TC-18`  | **The threshold is published with the context**, so that a member can see the protection they are relying on rather than being told it exists |
| `TC-19`  | **Suppression is not the same as secrecy.** A suppressed figure is stated as suppressed, with the reason and the threshold — never omitted silently, which would be indistinguishable from a figure that was never produced |

**The sealed-batch model does not remove `TC-16`.** It hides occupancy
before closure; it cannot hide the electorate's size, and at closure a small
context's turnout is public.

---

## 7. What remains derivable, and is stated

```text
An UPPER BOUND on turnout per window        = the fixed capacity C,
                                              which is public and constant
                                              — it says nothing about
                                              this election

Exact turnout                               at closure, by design

Whether a batch window occurred             yes — by design; the cadence
                                              is public and gapless

Whether a window contained ANY ballots      NO — an empty window and a
                                              full one are indistinguishable
                                              (TC-25, TC-29)

Global network-layer participation signals  T-P16A-04, PM-* #34 — unsolved

Out-of-band knowledge                       an organiser who watches a room
                                              learns more than the board shows
```

| ID       | Rule                                                                                                          |
| -------- | ----------------------------------------------------------------------------------------------------------------- |
| `TC-20`  | **The last row matters more than the rest in practice.** No board-level mechanism defends against an observer of the physical or social setting, and participant guidance says so rather than implying the electronic channel is private in that sense |
| `TC-55`  | **The third and fourth rows are the correction's whole point.** Under the rejected model an observer learned the real count from the board directly. Under the active model the board publishes a constant-size commitment on a constant cadence, and **no pre-closure observation distinguishes an election with one ballot from an election with `C` per window** |
| `TC-56`  | **Network-layer correlation is not eliminated by this model and is not claimed to be.** An observer of the casting service's traffic still sees submissions; the board simply stops confirming what that observer inferred (`T-P16A-04`, `RB-16C-01`) |

---

## 8. What this document does not decide

```text
Numeric C_primary, C_reserve, R and interval  → OD-P16C-10, GOVERNANCE
Reservation storage implementation             → OD-P16C-17, PACK-16D
Capacity stress-testing thresholds             → OD-P16C-18, PACK-17
Commitment construction details               → OD-P16C-14, PACK-16D
Inclusion-proof wire format                    → OD-P16C-15, PACK-16D
Closure opening format                         → OD-P16C-16, PACK-16D
Minimum electorate size per context            → GOVERNANCE, TC-16
Suppression thresholds                         → GOVERNANCE, TC-17
Rate-limit values for the lookup                → API-*, PACK-16D
Network-layer participation signals            → PACK-17, unsolved
```

**SPECIFIED. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY. NOT LEGALLY
ACTIVATED.**
