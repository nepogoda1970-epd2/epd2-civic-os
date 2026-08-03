# PACK-16C — Handover

**Round:** PACK-16C — Casting, Receipt, Verification Client, Bulletin Board and Election Record. **Specification and ADR only. No code. No cryptographic implementation. Not implemented. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-101`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 0. Handover statement

```text
PACK-16C FINAL CORRECTED CANDIDATE

EVENT PRIVACY:
CONTINUATION CAPABILITY REFERENCES ARE PROHIBITED
IN ALL EVENT PAYLOADS

PUBLIC-CHALLENGE ENTITLEMENT TRANSITION:
INTERNAL ATOMIC STATE CHANGE
NOT A STANDALONE EVENT-BUS MESSAGE

CAPACITY PLANNING:
DERIVED FROM FINITE UPPER BOUND

E = MAXIMUM VALID CONTINUATIONS
K = 1 PUBLIC EVIDENTIARY CHALLENGE
A = 1 ACCEPTED CAST
L_MAX = E × (K + A) = E × 2

CONCRETE N, C AND R:
ELECTION-GOVERNED PRE-OPENING CONFIGURATION

EXPECTED OR PLAUSIBLE TURNOUT:
NOT A SUFFICIENT CAPACITY BASIS

NO CHANGE TO CHALLENGE MODEL
NO CHANGE TO SEALED-BATCH MODEL
NO CHANGE TO EPD2-HOM-1
NO CHANGE TO EPD2-CRYPTO-1
NO IMPLEMENTATION

REPOSITORY_VERSION 0.15.0
CANON_VERSION 0.8.0
ADR-101 STATUS: PROPOSED

VO-08 REMAINS OPEN
VO-08 NOT OWNED BY PACK-16C

EXTERNAL ARCHITECTURAL REVIEW REQUIRED
NOT FINAL PASS
NOT PRODUCTION READY
NOT LEGALLY ACTIVATED
PACK-16D MUST NOT START BEFORE ACCEPTANCE
```

---

## 1. Source and digests

```text
Source archive:
EPD2_PACK-16C_CASTING_RECEIPT_VERIFICATION_BULLETIN_BOARD_AND_ELECTION_RECORD_SPEC_ADR_FINAL_REVIEW_CANDIDATE.zip

Source SHA-256:
6ca16ae23342230013e81a26defd374ef5d3b798442c6676510eeeb7fca52446

Final physical ZIP SHA-256:
PUBLISHED EXTERNALLY WITH DELIVERY
```

**Verified before any edit.** The source SHA-256 was recomputed and matched
before extraction; no other tree was used.

### 1.1 Tree content digest

Computed over every file in this tree **except this handover**, as the
SHA-256 of the sorted `sha256␠␠path` manifest:

```text
TREE CONTENT DIGEST (SHA-256)
88bc4b6588b3a96df3c4aed67f79ae892237f56a9f3005036ae61e81065f24d6
```

**Recomputable:**

```python
import hashlib, os
EXC = 'docs/packs/PACK-16/PACK-16C-HANDOVER.md'
rows = []
for root, dirs, files in os.walk('.'):
    dirs.sort()
    for f in sorted(files):
        rel = os.path.relpath(os.path.join(root, f), '.').replace(os.sep, '/')
        if rel == EXC:
            continue
        rows.append(hashlib.sha256(open(os.path.join(root, f), 'rb').read()).hexdigest() + '  ' + rel)
rows.sort()
print(hashlib.sha256(('\n'.join(rows) + '\n').encode()).hexdigest())
```

**A digest of a ZIP cannot be written inside that ZIP.** The archive's
SHA-256 is published externally, with delivery.

---

## 2. Exact diff

```text
Files added ..................................................... 0
Files deleted ................................................... 0
Files modified .................................................. 12   11 documents + ADR-101
Documents in docs/packs/PACK-16/PACK-16C-* ...................... 33   unchanged

architecture changes ............................................ 0
protocol changes ................................................ 0
challenge-limit changes ......................................... 0
capacity-formula changes ........................................ 0
batch-model changes ............................................. 0
API operation changes ........................................... 0   26 operations, unchanged
Canon changes ................................................... 0
FIR-status changes .............................................. 0
source / test / migration / frontend / CI changes ............... 0
uv.lock / package-lock.json ..................................... byte-identical
docs/canonical/ ................................................. byte-identical
docs/roadmap/ Master Register ................................... byte-identical
```

| # | File | Why it changed |
| - | ---- | -------------- |
| 1 | `PACK-16C-EVENT-CATALOG.md` | **Defect 1, primary.** `EV-15` and `EV-19b` deleted; `EV-05` and `EV-71` rewritten; `EV-74`…`EV-78` added; retention table and must-not-exist list updated |
| 2 | `PACK-16C-OPEN-DECISIONS.md` | **Defect 2, primary.** `OD-P16C-10` rewritten as §1.1; `OD-R13`…`OD-R17` added; §2.0.1 architectural-versus-numeric split |
| 3 | `PACK-16C-API-CATALOG.md` | **Stale reference.** The Audit-evidence field of `API-15` and `API-17` described the capability-side half as a separate event stream |
| 4 | `PACK-16C-CONTINUATION-CONSUMPTION-AND-ACCEPTANCE.md` | **Stale reference.** `CN-44` added so the entitlement transition's non-event status is stated where the boundary is specified |
| 5 | `PACK-16C-THREAT-MODEL-EXTENSION.md` | **Stale reference.** `T-P16C-28`'s mitigation cited two event streams; it now cites the stronger fact that one side is not an event |
| 6 | `PACK-16C-TURNOUT-CONFIDENTIALITY-MODEL.md` | **Stale reference.** `TC-26` pointed its supersession at `TC-58` (local challenges occupy no leaf) instead of `TC-59`/`TC-60`, and referred to concrete values without pointing at the rewritten `OD-P16C-10` |
| 7 | `PACK-16C-ACCEPTANCE-MATRIX.md` | **Consistency.** Eight decisions adjusted in place; **no rows added**; counts recomputed |
| 8 | `PACK-16C-FIR-COVERAGE-MATRIX.md` | **Consistency.** `FIR-INV-007` treatment strengthened by the event-payload prohibition |
| 9 | `PACK-16C-CANON-ASSESSMENT.md` | **Consistency.** `CAN-P16C-09` records that removing event-bus propagation needs no canon amendment |
| 10 | `PACK-16C-SPECIFICATION-REPORT.md` | **Consistency.** Correction 3 recorded; event count; two findings; one decision row |
| 11 | `PACK-16C-HANDOVER.md` | This file |
| 12 | `docs/adr/ADR-101-…md` | **Consistency.** Events section corrected; capacity section notes the architecture/numbers split; three PACK-16D obligations added |

**Files 3–6, 8, 9 are the "related stale references" the task permits.**
Each carried an *active* statement that the two named fixes contradict;
leaving any of them would have left the pack self-contradictory.

---

## 3. Defect 1 — continuation capability in event payloads

### 3.1 Removed event

```text
REMOVED   EV-19b   challenge.public_entitlement_consumed
          old payload: capability reference only
          old consumer: entitlement store

REMOVED   EV-15    capability.consumed
          old payload: context reference, capability reference only
          old consumer: capability store
```

**`EV-15` was removed as well, and this is the one change beyond the named
defect.** The audit named `EV-19b`; `EV-15` was the identical defect on the
cast path, and §10 of the correction task requires *`capability reference in
event payloads = 0`*. Leaving `EV-15` would have failed that check, and
stripping only its capability reference would have left a bare
"a capability was spent" tick — an internal live-participation counter,
which is worse than the field it removed.

### 3.2 New transactional treatment

```text
The public-challenge entitlement transition and the cast path's capability
consumption are INTERNAL PARTS of their atomic transactions.

Neither is emitted as a domain event, an integration event, a metric or a
log line.                                                    EV-71, CN-44

Their audit evidence may carry ONLY:
    election_context_id
    transaction outcome
    reason_code
    coarse_time_bucket
    schema_version
    a bounded-context-local transaction reference             EV-74

It may NOT carry:
    continuation capability · capability reference · credential · identity
    challenge artefact public reference · final cast ballot reference
    shared trace ID · cross-context correlation ID
    exact voter timestamp                                     EV-74

Any technical object it requires is non-exportable, bounded-context-local,
never on an event bus, never in the election record, never available to
identity or credential services, and deleted or retained under a short
governed retention policy.                                    EV-75
```

`EV-76` forbids a renamed replacement — an event such as
`challenge.public_entitlement_transition_completed` that still crosses a bus
is the same defect under another name.

`EV-77` states that §0's payload rules bind **every** event without
exception, including `challenge.public_submitted`,
`challenge.public_accepted`, `challenge.public_rejected` and
`challenge.public_published`. All four were checked; none carries a
capability, a credential, an identity, a session identifier or a
cross-domain trace identifier.

`EV-78` records that `EV-15` and `EV-19b` are **retired identifiers, not
missing events** — not reused, not renumbered, and the gap is not to be read
as an omission.

### 3.3 Event-catalogue consistency

```text
events before ............................................. 38
events after .............................................. 36
event IDs unique .......................................... yes
event names unique ........................................ yes
retired identifiers reused ................................ 0
events renumbered ......................................... 0
cross-references updated .................................. EV-05, EV-71,
                                                            retention table,
                                                            must-not-exist list
```

---

## 4. Defect 2 — the plausible-load capacity criterion

### 4.1 Old wording

```text
OD-P16C-10
  "C must exceed the maximum plausible per-window accepted-ballot count;
   shorter N worsens T-P16C-46 and longer N worsens PA-10"
```

That contradicts the accepted architecture, in which capacity derives from a
finite upper bound and never from expected, historical or plausible turnout.
**It also quietly reopened a closed architectural question** by phrasing a
settled derivation as a preference.

### 4.2 New wording — `OD-P16C-10`, §1.1

```text
OD-P16C-10 — Concrete Batch-Capacity Parameters

Status: OPEN — ELECTION-GOVERNED CONFIGURATION

Decision already fixed by architecture. Capacity planning must use a
finite upper-bound model derived from:
    E          maximum valid anonymous continuation capabilities
    K = 1      public evidentiary challenges per capability
    A = 1      accepted cast ballots per capability
    L_max      = E x (K + A) = E x 2
               the number of scheduled publication intervals
               fixed primary and predeclared reserve batch capacity
               cast-reserved and public-challenge-reserved partitions
               the governed incident and election-extension model

Still open — the concrete numeric values of:
    interval duration N · primary batch capacity C
    number of reserve commitments R
    cast / challenge slot partition
    operational safety reserve

Constraint. These values must not be based solely on expected, historical
or plausible turnout. They must be selected before election opening,
published as governed election configuration, and validated against the
finite upper-bound model.

Owner. Election governance, with PACK-16D implementation analysis and
PACK-17 independent verification.

Activation effect. Blocks production activation until concrete election
parameters are demonstrated to satisfy the capacity model.
```

`OD-R13` forbids any PACK-16C document from reintroducing a plausible-load
criterion. `OD-R14` keeps the trade-offs among the open numbers stated
rather than hidden. `OD-R15` restates that capacity is never adjusted during
an election, so these are a pre-opening decision or they are wrong for the
whole election.

### 4.3 Architectural closure versus numeric configuration — §2.0.1

```text
CLOSED ARCHITECTURAL QUESTIONS       OPEN CONFIGURATION QUESTIONS
  capacity must be finite              concrete N
  capacity derives from E, K and A     concrete C
  K = 1                                concrete R
  A = 1                                concrete slot partition
  adaptive overflow prohibited         concrete safety reserve for a
  reserve commitments predeclared        specific election
  challenge cannot take a cast slot
  exhaustion is fail-closed
```

`OD-R16`: no architectural question in the left column is open — recording
one as open invites PACK-16D to re-decide it. `OD-R17`: no numeric question
in the right column is closed — declaring a value settled without a concrete
election population and a governance decision would be a fiction, and
`FM-16C-30` exists to catch it.

---

## 5. Acceptance matrix

```text
Rows                                          223   unchanged
Requirement IDs added                           0
Requirement IDs removed or renumbered           0
Decisions adjusted in place                     8
Rows missing a required column                  0
Duplicate Requirement IDs                       0

SATISFIED                                     189
PARTIALLY SATISFIED                            10
DEFERRED                                       11
BLOCKED                                         3
NOT APPLICABLE                                 10
                                              ---
                                              223
```

The eight adjusted rows: `AC-P16C-028` capability isolation ·
`AC-P16C-122` batch parameters · `AC-P16C-137` event catalogue ·
`AC-P16C-138` no trace spans the boundary · `AC-P16C-139` events that must
not exist · `AC-P16C-203` entitlement linkage · `AC-P16C-206` capacity basis
· `AC-P16C-218` capacity plan publication.

**`AC-P16C-122` is `DEFERRED`, not `SATISFIED`**, because it names concrete
numeric configuration; its owner is election governance with PACK-16D and
PACK-17. The status was already `DEFERRED` before this correction and is
unchanged, so the totals are unchanged.

All 223 document and section references were re-resolved mechanically and
verified to exist.

---

## 6. Canon and FIR

```text
Canon files modified ........................................ 0
CANON_VERSION ............................................... 0.8.0, unchanged
Clarifications recorded ..................................... 8   unchanged
Amendment candidates recorded ............................... 3   unchanged
Amendments proposed ......................................... 0

Master Register ............................................. byte-identical
FIR entries created / removed / downgraded .................. 0
FIR statuses changed ........................................ 0
FIR treatments strengthened by this correction ............... 1   FIR-INV-007
Implementation obligations closed ........................... 0
```

`CAN-P16C-09`: **removing event-bus propagation of a capability reference
requires no canon amendment.** Deleting two integration events creates no
aggregate, changes no canonical field, and **strengthens** 19a.1's
separation rather than touching it.

The Master Register was checked for both stale patterns — a capability
reference event and a plausible-load capacity rule. **Neither appears**, so
the register is not modified.

---

## 7. Verification — commands run, output recorded

```text
$ python3 scripts/check_repository.py
OK: all 983 required paths are present.

$ python3 scripts/verify_versions.py
OK: all version sources are consistent.

$ python3 scripts/check_canon_0_8_0.py
OK: all 18 canon 0.8.0 amendment checks passed.

$ python3 scripts/check_forbidden_files.py
WARNING: repository root is not a git repository; falling back to a
full filesystem walk (local build caches may be flagged).
OK: no forbidden paths found.
```

**Events**

```text
standalone public-entitlement-consumed event .............. 0
continuation capability in event payloads ................. 0
capability reference in event payloads .................... 0
credential ID in event payloads ........................... 0
identity in event payloads ................................ 0
shared cross-domain trace IDs ............................. 0
client-local challenge telemetry events ................... 0   EV-70
duplicate event IDs ....................................... 0
duplicate event names ..................................... 0
generic payload rules bind every event .................... EV-01, EV-03, EV-77
```

**Open decisions**

```text
active "maximum plausible load" criteria ................... 0
OD-P16C-10 includes E ...................................... yes
OD-P16C-10 includes K = 1 .................................. yes
OD-P16C-10 includes A = 1 .................................. yes
OD-P16C-10 includes L_max = E x 2 .......................... yes
OD-P16C-10 includes N, C, R ................................ yes
OD-P16C-10 includes slot partition ......................... yes
OD-P16C-10 includes pre-election governance ................ yes
OD-P16C-10 includes production activation effect ........... yes
numeric values remain open ................................. yes
architecture semantics remain closed ....................... yes   §2.0.1
capacity based on actual turnout ........................... no    TC-60
capacity adjusted during an election ....................... no    TC-24, TC-69, OD-R15
```

**Acceptance matrix**

```text
required columns present on every row ..................... yes
Requirement IDs unique .................................... 223 / 223
existing IDs preserved .................................... 223 / 223
new Requirement IDs ....................................... 0
summary calculated from rows .............................. yes
sum(status counts) == requirement rows .................... 223 == 223
unsupported statuses ...................................... 0
CORRECTED statuses ........................................ 0
section references resolved ............................... 223 / 223
```

**Repository integrity**

```text
REPOSITORY_VERSION ........................................ 0.15.0, unchanged
CANON_VERSION ............................................. 0.8.0, unchanged
ADR-101 ................................................... proposed
EPD2-HOM-1 ................................................ unchanged
EPD2-CRYPTO-1 ............................................. unchanged
VO-08 ..................................................... OPEN; owner
                                                            PACK-16B external
                                                            cryptographic review,
                                                            confirmed by PACK-17
source / test / migration / frontend / CI changes ......... 0
uv.lock ................................................... byte-identical
package-lock.json ......................................... byte-identical
```

**Archive hygiene**

```text
duplicate ZIP paths ....................................... 0
nested ZIPs ............................................... 0
nested repositories ....................................... 0
repository roots .......................................... 1
uv.lock files ............................................. 1
package-lock.json files ................................... 1
Master Register copies .................................... 1
forbidden generated directories ........................... 0
private-key-like artifacts ................................ 0
candidate ZIPs inside archive ............................. 0
external PDFs ............................................. 0
```

| ID | Rule |
| -- | ---- |
| `HO-01` | **No verification result in this document is asserted.** Each is the recorded output of a command or a mechanical check run against this tree, and where a script emitted a warning the warning is reproduced rather than trimmed |

---

## 8. Open decisions and residual risks

**Unchanged by this correction.** Nineteen open decisions; none closed, none
opened, none re-owned. `OD-P16C-10` was **rewritten, not resolved** — its
status is still `OPEN`, its owner is still election governance, and its
activation effect is now stated explicitly rather than implied.

**Residual risks: unchanged.** `RB-16C-01`…`RB-16C-16` stand as written.

**One residual is sharpened rather than added.** The event-privacy
correction removes a *published* correlation surface; it does not remove
`T-P16C-28`, the operator with database-level access to both stores and
precise timing. **That threat is now the only remaining path to the
boundary's two halves**, because neither half is on an event bus. The
defence is still separation of principals and the absence of a join key —
not access control alone.

---

## 9. What an auditor should attack first

```text
1. EV-74 / EV-75 — the internal audit evidence. Six fields are
   permitted. Does any implementation need a seventh, and would that
   seventh be a correlation handle?

2. EV-76 — the renamed replacement. Is there any wording anywhere that
   would let a bus message reappear under a different name?

3. EV-77 — the four public-challenge events. Re-read their payloads
   against EV-01 and EV-03 rather than trusting this summary.

4. OD-P16C-10 §1.1 — is anything in the left column of §2.0.1 in fact
   still open, or anything in the right column in fact still closed?

5. TC-60 / OD-R13 — does any document still let a capacity number be
   justified by what turnout is expected to be?

6. T-P16C-28 — the insider with both stores. Removing the events did
   not remove this, and it is now the sharpest remaining path.

7. Everything the previous two audits passed. This correction touched
   twelve files; the other twenty-two documents are unchanged and
   their findings stand or fall on their own.
```

---

## 10. What must NOT be read into this delivery

```text
NOT a PASS.
NOT an implementation candidate.
NOT externally reviewed.
NOT production ready.
NOT legally activated.
NOT a claim that VO-08 is resolved — it is OPEN and NOT owned here.
NOT a claim of BSI conformity.
NOT a claim that the atomic boundary can be built.
NOT a claim that any verifier can execute the twenty-one checks.
NOT a claim that the per-capability bound is publicly provable.
NOT a claim that a local diagnostic challenge is evidence.
NOT a claim that concrete N, C or R have been chosen.
NOT authorisation to start PACK-16D.
```

---

## 11. Decision history of this correction

| # | Event |
| - | ----- |
| 1 | Source SHA-256 `6ca16ae2…` recomputed and matched before extraction; no other tree used |
| 2 | Both defects inventoried across all 33 documents, `ADR-101` and the Master Register before any edit |
| 3 | **`EV-19b` deleted rather than reshaped**, per the task's preferred fix, and `EV-76` added so a renamed bus message cannot return |
| 4 | **`EV-15` deleted as well** — the identical defect on the cast path. Stripping its capability reference alone would have left a bare consumption tick, an internal live-participation counter, which is worse than the field removed |
| 5 | **Identifiers retired, not renumbered** (`EV-78`), so the gap is documented rather than read as a missing event |
| 6 | **`TC-26`'s cross-reference corrected** — it pointed its own supersession at `TC-58` (local challenges occupy no leaf) instead of `TC-59`/`TC-60`. A wrong pointer in the rule that withdraws the plausible-load criterion would have undermined the fix |
| 7 | **`OD-P16C-10` rewritten in full**, with the architectural derivation stated as closed and only the numbers open |
| 8 | **§2.0.1 added** so that architectural closure and numeric configuration cannot be conflated again |
| 9 | **No Requirement IDs added.** Eight decisions were adjusted in place; the task asked for no new rows without necessity, and there was none |
| 10 | Master Register checked for both stale patterns and **left byte-identical**, because neither appears in it |
| 11 | Canon, lockfiles and every untouched document verified byte-identical |

| ID | Rule |
| -- | ---- |
| `HO-02` | **Rows 4 and 6 are the changes beyond the two named defects, and both are recorded rather than folded in silently.** One is the same defect on the other path; the other is a wrong cross-reference inside the rule that performs the fix |
| `HO-03` | **Row 9 is a refusal.** A correction that grows the acceptance matrix every round stops being a correction |

---

## 12. Next

```text
PACK-16C FINAL CORRECTED CANDIDATE  ->  independent audit
                                    ->  ADR-101 acceptance
                                    ->  PACK-16D implementation candidate

PACK-16D MUST NOT START before architectural acceptance of PACK-16C.
ADR-101 is CONDITIONAL on ADR-100, which is itself `proposed`.
```

**SPECIFIED. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY. NOT LEGALLY
ACTIVATED.**
