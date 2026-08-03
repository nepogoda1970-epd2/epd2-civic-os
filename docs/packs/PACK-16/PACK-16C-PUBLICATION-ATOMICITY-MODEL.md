# PACK-16C — Publication Atomicity Model

**Round:** PACK-16C — Casting, Receipt, Verification Client, Bulletin Board and Election Record. **Specification and ADR only. No code. No cryptographic implementation. Not implemented. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-101`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 1. The decision

```text
DURABLE ACCEPTANCE WITH A SIGNED PUBLICATION COMMITMENT,
followed by inclusion in a NAMED SEALED BATCH WINDOW,
followed by public opening at closure.

"Accepted but never published" is NOT a permitted terminal state.
It is a published failure with an election-level remedy.
```

**CORRECTED.** The first candidate expressed the deadline as "the published
publication deadline" and published individual entries in batches. Under the
corrected turnout model (`TC-*` §4) publication has **two phases** and the
deadline is **a named batch window**, not an open-ended future.

```text
PHASE 1  COMMITMENT  the ballot's leaf is inside the commitment_root of
                     a NAMED sealed batch window, published at that
                     window's scheduled time                    (TC-23)

PHASE 2  OPENING     the ballot artefact itself is published, with its
                     leaf opening, at closure                   (TC-41)
```

## 2. The options

| Option | Voter certainty at submission | Turnout leakage | Failure mode | Verdict |
| ------ | ----------------------------- | --------------- | ------------ | ------- |
| **Accept only after publication** | High | **Severe** — publication must be immediate, which destroys batching and makes each acceptance a timed public event | Board outage blocks casting entirely | **Rejected** — it trades voter privacy for voter certainty |
| **Durable acceptance, then asynchronous publication, unbounded** | Low | None | "Accepted but never published" is reachable and invisible | **Rejected** |
| **Two-phase publication** (pre-announce, then publish) | Medium | Moderate — the pre-announcement is itself a timed event | Complexity without a new guarantee | Rejected |
| **Durable acceptance + signed publication commitment + published deadline** | **High** — the commitment is verifiable evidence | **None** — batching preserved | Missed deadline is **public and remediable** | **SELECTED** |

| ID | Rule |
| -- | ---- |
| `PA-01` | **The atomic acceptance boundary produces a signed publication commitment** covering the ballot's confirmation code, the context, and the deadline by which it will appear (`CN-06`) |
| `PA-02` | **The commitment is given to the voter in the receipt** and is verifiable against the board's published signing key, so a voter holds evidence of acceptance even before publication |
| `PA-03` | **The publication deadline is a named batch window, not a duration.** The commitment names the `batch_window_id` in which the ballot's leaf will be committed; the window's scheduled time is public and fixed before `voting_open` (`TC-22`, `TC-23`). A deadline expressed as an unbounded asynchronous future is prohibited |
| `PA-10` | **The commitment obligation is bounded by construction.** Because the cadence is fixed and gapless, the longest a ballot can wait for phase 1 is one batch interval, and that interval is a published governed parameter (`TC-25`, `OD-P16C-10`) |
| `PA-11` | **A ballot accepted near a batch boundary is committed in the next window whose commitment has not yet been published**, and never retro-fitted into a window already committed. Retro-fitting would require altering a published root (`TC-54`, `FM-16C-21`) |
| `PA-13` | **Leaf reservation precedes durable acceptance on both paths** — cast and public evidentiary challenge (`TC-70`, `CN-42`, `CN-43`). A publication commitment is only ever issued against a slot that already exists |
| `PA-14` | **Reservation failure is a fail-closed rejection, not a deferral.** `submission.cast_capacity_unavailable` or `challenge.public_reservation_unavailable`; nothing is consumed and no obligation is created (`TC-82`) |
| `PA-15` | **A public evidentiary challenge carries the same publication obligation as a cast ballot** — named window, bounded by one interval, publicly detectable by its own submitter, opened at closure (`CH-46`) |
| `PA-12` | **Phase 1 is publicly detectable per ballot by its own voter**, through the privacy-safe inclusion proof (`TC-36`…`TC-40`), and by nobody else. A voter can therefore detect non-publication **before closure**, which the first candidate's model could not offer |

## 3. Why not "accept only after publication"

It is the intuitive answer and it is wrong here, for one reason:

```text
Publishing each ballot at acceptance makes the moment of acceptance
a publicly observable event, at the granularity of a single voter.

That is exactly the timing channel BB-11 and CN-15 exist to close.
```

**The design chooses batching, and therefore must accept a gap between
acceptance and publication.** Everything in this document is about making
that gap bounded, evidenced and remediable rather than silent.

## 4. The states, and what makes each visible

| Phase | Receipt `publication_status` | Voter sees | Public sees | Duration |
| ----- | ---------------------------- | ---------- | ----------- | -------- |
| Accepted, not yet committed | `ACCEPTED_PENDING_BATCH_COMMITMENT` | Receipt + signed commitment naming the batch window | **Nothing** — by design | ≤ one batch interval |
| Committed in a sealed batch | `COMMITTED` | Inclusion proof against `commitment_root` at a signed checkpoint | **The `sealed_batch_commitment` entry only** — constant size, no occupancy | until closure |
| Opened at closure | `PUBLISHED_AFTER_CLOSURE` | The ballot artefact and its leaf opening | The entry, the opening, the reconciliation | permanent |
| Commitment obligation missed | `PUBLICATION_DISPUTED` | Status check shows the named window passed without the leaf | **A published failure notice** | until remedied or escalated |

| ID | Rule |
| -- | ---- |
| `PA-04` | **A missed commitment obligation is published**, as a board `incident_notice` (`BE-17`) stating that one or more accepted ballots were not committed in their named window, **without identifying which voter and without a count** |
| `PA-05` | **The count of accepted-but-uncommitted ballots is never published before closure** — it is a turnout proxy. The *fact* of the failure is published; the *number* goes to the Auditor immediately and to the public after closure (`TC-07`) |
| `PA-06` | **A voter whose ballot is not published by the deadline has a dispute path** (`DP-*`) that does not require them to reveal their identity or their choice |

## 5. Escalation

| Condition | Response |
| --------- | -------- |
| A scheduled `sealed_batch_commitment` is not published at its window time | **`FM-16C-18` — published immediately.** A gap in the cadence is itself a disclosure (`TC-25`) and is never absorbed silently |
| Batch commitment published late | **`FM-16C-19` — published, with the delay stated.** The cadence is not re-planned around it (`TC-24`) |
| Deadline missed for any ballot | **`publication_disputed`; public incident notice; Auditor informed immediately** |
| Not remedied within the escalation window | **Pause casting** (`FM-P16A-09` lineage) |
| Ballots accepted that cannot be published at all | **Abort — the context is uncertifiable**, because the tallied set cannot be fixed honestly |
| Every predeclared slot in an interval is unavailable | **`FM-16C-29` — fail closed, pause public challenges, preserve cast entitlements, publish a capacity incident, enter governed pause/extension** (`TC-78`) |
| Publication of a ballot that was never accepted | **Abort — annul.** This is board misbehaviour, not a delay |
| Mirror cannot serve the batch | Mirror divergence path (`BA-20`) |

| ID | Rule |
| -- | ---- |
| `PA-07` | **There is no permitted terminal state "accepted but never published".** Either the ballot publishes, or the election records that it did not and the outcome is affected accordingly |
| `PA-08` | **A ballot that was accepted but is absent from the closure checkpoint cannot be tallied**, because the tallied set is exactly the published set (`BM-20`). If that happens, the election's completeness is compromised and `EC-*` governs the consequence |
| `PA-09` | **The remedy is never to insert the ballot after closure.** Late insertion breaks the consistency proof against the closure checkpoint and is indistinguishable from an attack (`AO-12` reasoning) |

**`PA-08` and `PA-09` together state the hard truth:** if publication fails
past closure, the voter's ballot is lost and the election must say so. There
is no repair that preserves both the ballot and the record's integrity, and
this design chooses the record.

## 6. What this document does not decide

```text
Batch interval and capacity            → OD-P16C-10, GOVERNANCE
Escalation window                       → OD-P16C-13, GOVERNANCE
Commitment construction                  → OD-P16C-14, PACK-16D
Inclusion-proof wire format              → OD-P16C-15, PACK-16D
Retry policy inside a window             → PACK-16D
```

**SPECIFIED. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY. NOT LEGALLY
ACTIVATED.**
