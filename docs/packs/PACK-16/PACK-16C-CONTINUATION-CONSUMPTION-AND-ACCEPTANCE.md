# PACK-16C — Continuation Consumption and the Acceptance Boundary

**Round:** PACK-16C — Casting, Receipt, Verification Client, Bulletin Board and Election Record. **Specification and ADR only. No code. No cryptographic implementation. Not implemented. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-101`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 1. The decision

```text
ATOMIC VALIDATION + CONSUMPTION + ACCEPTANCE

The capability is consumed inside the same atomic boundary that
durably accepts the ballot, and after every cryptographic check
has already passed.

They succeed together or neither happens.
```

`ADR-101` records it. This document compares the four options, states what
the choice prevents, and is honest about the assumption it rests on (§6).

---

## 2. The four options

|                                          | **A — consume before validation**                                         | **B — consume after validation, separately**         | **C — atomic validation + consumption + acceptance**                       | **D — reservation, then commit**                                      |
| ---------------------------------------- | ------------------------------------------------------------------------- | ---------------------------------------------------- | -------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| **Ballot stuffing**                      | prevented                                                                 | prevented                                            | **prevented**                                                              | prevented                                                             |
| **Capability replay**                    | prevented                                                                 | **window exists** between validation and consumption | **prevented**                                                              | prevented                                                             |
| **Double acceptance**                    | possible — the ballot may still fail and be resubmitted                   | **possible** in the same window                      | **prevented**                                                              | prevented                                                             |
| **Capability loss on transient failure** | **severe** — spent for nothing, on any downstream error                   | moderate                                             | **none** — nothing is spent unless the ballot is accepted                  | **severe** — a reservation stranded by a crash locks the voter out    |
| **Silent duplicate handling**            | tempting, because the capability is already gone                          | tempting                                             | **structurally unnecessary**                                               | tempting                                                              |
| **Redemption ↔ accepted-ballot linkage** | the two writes are separated in time, which is _better_ for unlinkability | same                                                 | **the two writes are adjacent in time — the risk this option carries**, §5 | same                                                                  |
| **Voter-visible failure mode**           | "your vote was lost and you cannot try again"                             | rare but same                                        | "your submission failed; try again"                                        | "your capability is locked; wait"                                     |
| **Implementation honesty**               | simple                                                                    | simple                                               | **requires a stated transaction assumption**, §6                           | requires timeout and release logic, which is a second failure surface |
| **Verdict**                              | **Rejected**                                                              | **Rejected**                                         | **SELECTED**                                                               | **Rejected**                                                          |

### 2.1 Why A and B are rejected

Both admit a state in which **a voter's single-use capability has been
consumed and no ballot exists**. In a system with **no revoting** and **no
re-issue** (`CC-08`), that state is not an inconvenience — it is
disenfranchisement produced by a transient server error.

Option B's window is smaller than A's and is still a window: between
`validated` and `consumed` the same capability can be presented again, and
the only defences are locks and luck.

### 2.2 Why D is rejected

A reservation converts a crash into a **lock**. The voter's capability is
neither usable nor spent, and the remedy is a timeout the voter must wait
out without knowing how long or whether it will work. It also adds a second
state machine — reserve, commit, release, expire — whose failure modes are
precisely the ones this design is trying to remove.

**D is the option that looks safest and is not.** It moves the risk from a
rare atomic-commit failure to a common one: any client that closes its
laptop mid-submission.

---

## 2A. Capability entitlement state

**Added by the bounded-challenge correction.** A capability now carries two
entitlements, not one, and each is spent by a different act.

```text
cast_entitlement_available            : boolean
public_challenge_entitlement_available: boolean
capability_consumed                   : boolean
```

| Moment                                   | `cast`      | `public_challenge` | `consumed`                                            |
| ---------------------------------------- | ----------- | ------------------ | ----------------------------------------------------- |
| **Issued**                               | `true`      | `true`             | `false`                                               |
| After a **local diagnostic challenge**   | `true`      | `true`             | `false` — **no server-side state change of any kind** |
| After a **public evidentiary challenge** | `true`      | **`false`**        | `false`                                               |
| After **final cast acceptance**          | **`false`** | **`false`**        | **`true`**                                            |

| ID      | Rule                                                                                                                                                                                                                                                                                                  |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CN-33` | **A public evidentiary challenge spends the public-challenge entitlement and nothing else.** The cast entitlement is untouched, and the capability is **not** consumed (`CH-44`)                                                                                                                      |
| `CN-34` | **A local diagnostic challenge changes no server-side state.** No request is made, so there is nothing to change (`CH-39`…`CH-42`)                                                                                                                                                                    |
| `CN-35` | **Final cast acceptance consumes the capability and clears both entitlements**, so a capability can produce **at most one public spoiled artefact and at most one accepted cast ballot** — the bound the whole capacity plan rests on (`TC-*` §4.9)                                                   |
| `CN-44` | **The entitlement transition is an internal part of the atomic public-challenge transaction and is not emitted as an event.** Neither it nor the cast path's capability consumption crosses an event bus, and no audit artefact for either carries a capability reference (`EV-71`, `EV-74`, `EV-75`) |
| `CN-36` | **Entitlement state lives only inside the anonymous continuation boundary.** It may not be joined to an identity, a credential, a ballot reference or a public challenge artefact ID, and no identity-domain store may hold any of it (`CC-04`, `DM-10`, `DM-20`)                                     |
| `CN-37` | **Entitlement state is not a counter the voter can query for remaining slots.** The voter is told before acting that the public audit challenge is available once (`CH-51`); the system never reports a residual count that could be aggregated into an activity signal                               |
| `CN-38` | **`K` and `A` are profile constants, not fields.** The state above is three booleans precisely so that no deployment can widen the bound by writing a larger number (`CH-37`, `CH-38`)                                                                                                                |

---

## 2B. The public-challenge atomic boundary

A public evidentiary challenge has **its own** atomic boundary, separate
from the cast boundary of §3.

```text
    ——— PUBLIC-CHALLENGE BOUNDARY OPENS ———
1  validate the challenge artefact on the standard pipeline
2  verify the continuation capability
3  verify public_challenge_entitlement_available is TRUE
4  RESERVE a publication-bearing leaf slot in an allowed window   (TC-* §4.10)
5  mark public_challenge_entitlement_available = FALSE
6  durably record the spoiled artefact
7  create the sealed-batch publication obligation
    ——— PUBLIC-CHALLENGE BOUNDARY CLOSES ———
```

| ID      | Rule                                                                                                                                                                                                                                                                                                      |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CN-39` | **The boundary is atomic and all-or-nothing.** A rollback leaves `public_challenge_entitlement_available = TRUE`, no leaf reserved and no artefact recorded                                                                                                                                               |
| `CN-40` | **It never consumes the cast entitlement, never creates an accepted ballot and never produces tally-eligible material**                                                                                                                                                                                   |
| `CN-41` | **Replay of the same entitlement is impossible.** The same idempotent submission returns the same outcome; a **second, differing** public challenge submission fails closed with `challenge.public_entitlement_exhausted` (`CH-43`)                                                                       |
| `CN-42` | **Leaf reservation precedes durable acceptance, not the reverse.** A challenge is never accepted and then found to have nowhere to go; if no allowed slot can be reserved the submission fails closed with `challenge.public_reservation_unavailable` and the entitlement is **not** spent (`TC-*` §4.10) |
| `CN-43` | **The cast boundary of §3 gains the same reservation step.** Acceptance without a reserved leaf is prohibited on both paths (`submission.cast_capacity_unavailable`)                                                                                                                                      |

---

## 3. The selected boundary, exactly

```text
BEFORE THE BOUNDARY  (repeatable, nothing consumed, nothing durable)
   schema · canonical encoding · profile · parameter set · election context
   manifest binding · ballot-style binding · group membership · subgroup checks
   every well-formedness proof · plaintext-knowledge proof
   contest constraints · confirmation-code recomputation
   duplicate-ballot detection · capability validity check

INSIDE THE BOUNDARY  (atomic — all of it, or none of it)
   re-check capability unspent
   mark capability spent
   durably record ballot acceptance
   assign board sequence reservation
   sign the publication commitment

AFTER THE BOUNDARY  (durable, published, irreversible)
   bulletin-board publication
   receipt issuance
   voter verification
```

| ID      | Rule                                                                                                                                                                                        |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CN-01` | **Consumption is a single atomic act with exactly-once effect** (`CC-01`). A second presentation is refused with a distinct reason code, never silently ignored and never silently accepted |
| `CN-02` | **Every cryptographic check completes before the boundary is entered.** No check may be moved inside it "for performance", and none may be moved after it                                   |
| `CN-03` | **The capability's unspent state is re-checked inside the boundary**, not only before it. The pre-boundary check is an optimisation; the in-boundary check is the guarantee                 |
| `CN-04` | If any step inside the boundary fails, **all of it is rolled back**: the capability is unspent, no acceptance record exists, and the voter may retry                                        |
| `CN-05` | **No partial acceptance state is durable.** There is no "accepted but capability not spent" and no "capability spent but ballot not accepted"                                               |
| `CN-06` | The boundary produces a **signed publication commitment** (`PA-*`) as part of the same act, so acceptance is evidenced even if publication is later delayed                                 |

---

## 4. Idempotency, duplicates and replay

**Both boundaries are idempotent by retry token.** The rules below apply to
the cast boundary and, unchanged in form, to the public-challenge boundary
of §2B.

| ID      | Rule                                                                                                                                                                                                                  |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CN-07` | Each submission carries a **retry token**, client-generated, unique to the attempt, **derived from the ballot and not from the capability** (`CF-29`)                                                                 |
| `CN-08` | **Same token + byte-identical envelope** → the original outcome is returned. No second capability is consumed, no second ballot exists                                                                                |
| `CN-09` | **Same token + different envelope** → rejected, `submission.retry_token_conflict`. This is the check that stops a client from swapping a ballot under cover of a retry                                                |
| `CN-10` | **Different token + already-spent capability** → rejected, `acceptance.capability_already_spent`. This is the replay case, and it is refused after full validation so that the refusal leaks nothing about the ballot |
| `CN-11` | **Duplicate ballot identifier** on the board → rejected, never overwritten (`BM-05`)                                                                                                                                  |
| `CN-12` | Retry tokens are held only as long as the context's submission window plus the published dispute period, and are **never published, never in the receipt, never in the record**                                       |

---

## 5. The linkage risk this choice carries, stated rather than hidden

Atomicity places the credential-side write and the ballot-side write
**adjacent in time**. That is exactly the adjacency `T-P16A-04`
(redemption-to-casting timing correlation) warns about.

**It is not resolved by the atomicity choice. It is bounded by four
controls, none of which is cryptographic:**

| ID      | Control                                                                                                                                                                                                                          |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CN-13` | **The two writes are to different stores under different principals** (`CC-05`). Atomic _in effect_ — the outcome is all-or-nothing — not a single transaction over a joined schema                                              |
| `CN-14` | **Consumption timestamps are coarsened** to the context's `timestamp_granularity` (`CC-06`); the ballot's board timestamp is coarsened independently and **published only at the checkpoint's granularity**                      |
| `CN-15` | **Board publication is a sealed batch commitment on a fixed cadence, opened at closure** (`BB-11` satisfied by `TC-*` §4), and leaf index is randomised, so board order carries no arrival order (`BM-06`, `T-P16A-05`, `TC-31`) |
| `CN-16` | **No shared correlation identifier, trace ID, request ID or session ID crosses the boundary** (`T-P16A-18`). A trace that spans both sides is a cross-boundary trace and is a `FM-P16A-18` incident                              |

**What remains:** an adversary with simultaneous privileged access to both
stores _and_ to fine-grained infrastructure timing could narrow a
correlation. PACK-15 said the same about issuance, and the answer is the
same: **the pair never exists to be joined**, the two principals are
separated, and the residual is recorded rather than denied — `RB-16C-01`.

---

## 6. The assumption this decision rests on

```text
An atomic boundary spanning two stores under two principals
is a DISTRIBUTED-TRANSACTION assumption, and this round does not
pretend otherwise.
```

| ID      | Rule                                                                                                                                                                                                                                                                                                                                     |
| ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CN-17` | **The cross-service transaction assumption is declared, not buried.** PACK-16D must show, concretely, how all-or-nothing is achieved across the credential-side spend and the ballot-side acceptance                                                                                                                                     |
| `CN-18` | **A design that achieves it with a shared database spanning both domains is refused**, because it recreates the join PACK-15 removed. Acceptable shapes include a spend-then-compensate protocol with a published compensation record, a two-phase commit between separated principals, or an outbox whose failure is publicly evidenced |
| `CN-19` | **Whatever shape is chosen, its failure mode must be "capability unspent"**, never "ballot accepted without a spend" and never "spend without a ballot"                                                                                                                                                                                  |
| `CN-20` | If PACK-16D cannot demonstrate `CN-19`, that is an **`ARCHITECTURAL BLOCKER`** for implementation acceptance, not a risk to be accepted — carried as `OD-P16C-01`                                                                                                                                                                        |

**This is the largest single implementation risk this round hands forward,
and it is named as such.**

---

## 7. Capability lifecycle

```text
issued (PACK-15)
   ↓  handoff
held_by_bearer          in client memory only, never stored
   ↓  step 7 probe (no state change)
presented               inside a submission
   ↓  atomic boundary
spent                   terminal — cryptographically and operationally unusable

   ↘ expired            window closed, never presented
   ↘ abandoned          never presented, window closed
```

| ID      | Rule                                                                                                                                                                                                                                                                    |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CN-21` | **After successful consumption the capability is cryptographically and operationally unusable.** Not "marked used" in a mutable flag alone — the construction's own spent-nonce semantics apply, and any later presentation fails the construction, not merely a lookup |
| `CN-22` | **Spent state creates no person-to-ballot linkage.** The spend record contains no ballot identifier, no confirmation code, no board reference and no ballot digest (`CC-04`)                                                                                            |
| `CN-23` | **Expiry is silent to the outside world.** The number of unspent capabilities at any moment is a turnout proxy and is not published, exported or displayed before closure (`CC-10`, `TC-*`)                                                                             |
| `CN-24` | **The capability creates no session.** No cookie, no storage entry, no resumable state, no "continue where you left off" (`CC-07`)                                                                                                                                      |
| `CN-25` | A capability that fails validation for any reason is **not** consumed, and the failure is reported by reason code only — never by echoing any part of the capability                                                                                                    |

---

## 8. Timeout semantics

| Situation                                            | Capability state | Voter's remedy                                                                                  |
| ---------------------------------------------------- | ---------------- | ----------------------------------------------------------------------------------------------- |
| Client closed before submission                      | **unspent**      | Present it again                                                                                |
| Submission sent, no response, boundary never entered | **unspent**      | Re-submit with the **same** retry token                                                         |
| Submission sent, boundary entered and rolled back    | **unspent**      | Re-submit with the same retry token                                                             |
| Submission sent, boundary committed, response lost   | **spent**        | **Status check by confirmation code** — the ballot exists and will publish                      |
| Voting window closes mid-attempt                     | **unspent**      | None. The window is fixed by signed checkpoints (`T-P16A-38`) and is not extended for one voter |
| Capability window expires unused                     | **expired**      | None, and no re-issue (`CC-08`)                                                                 |

| ID      | Rule                                                                                                                                                                             |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CN-26` | **The client never auto-resubmits on timeout.** It offers a status check, because an automatic retry against an unknown outcome is how duplicates and double spends get invented |
| `CN-27` | **The status check is by confirmation code against the board**, on the verification origin — not by capability, and not against the casting service                              |

---

## 9. Privacy-safe audit evidence

**What may be recorded on the credential side:**

```text
that a capability was consumed          coarsened timestamp
the context reference                   the reason code on failure
aggregate consumption counts            after closure only
```

**What may never be recorded anywhere:**

```text
a ballot identifier beside a continuation reference
a confirmation code beside a continuation reference
a board sequence number beside a continuation reference
an exact consumption timestamp in any published or exportable form
a request/trace/correlation ID shared with the ballot side
the capability itself, in any log, backup, export or crash report
an IP address associated with either side of the boundary
```

| ID      | Rule                                                                                                                                                                                        |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CN-28` | **Discovery of any record holding both sides is a `FM-P16A-17` identity-correlation incident** — suspend, investigate, annul if correlation was achievable. It is not a data-hygiene ticket |
| `CN-29` | Backup and restore domains are separated; a restore that lands both streams in one target is `T-P16A-10` and is refused by design, not by procedure                                         |

---

## 10. What this document does not decide

```text
The transaction mechanism                    → PACK-16D, OD-P16C-01
The construction replacing the spent-nonce set, if any → OD-P15-05, PACK-16C §11 boundary only
Retry-token lifetime in wall-clock terms     → PACK-16D
Rate-limit values                            → PACK-16D
```

### 10.1 `OD-P15-05` — the boundary this round adds

PACK-16B closed the cryptographic boundary (`IS-01`…`IS-06`) and reassigned
the construction question here. **PACK-16C's answer is that the casting side
imposes three further constraints and does not select a construction:**

| ID      | Constraint on any future issuance construction                                                                                                                                                  |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CN-30` | It must support an **exactly-once spend that is verifiable inside the acceptance boundary** without contacting the identity side                                                                |
| `CN-31` | It must fail **closed and locally** — a spend attempt that cannot be resolved must leave the capability unspent, not undetermined                                                               |
| `CN-32` | It must not require the ballot side to learn anything about the capability beyond "valid and unspent" — no scope beyond ballot style, no issuer reference, no serial that survives the boundary |

**The current spent-nonce set satisfies all three.** No change is required
by PACK-16C, and none is made.

**SPECIFIED. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY. NOT LEGALLY
ACTIVATED.**
