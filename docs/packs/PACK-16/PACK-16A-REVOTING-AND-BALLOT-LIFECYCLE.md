# PACK-16A — Revoting Decision and Ballot Lifecycle

**Round:** PACK-16A — Verifiable Voting Protocol and Ballot Model Selection. **Specification and ADR only. No code. Not implemented. Not an implementation candidate. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-099`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 1. The decision

```text
REVOTING DECISION FOR EPD2-HOM-1

NO REVOTING.
One authorised participation produces at most one accepted ballot.
There is no supersession, no ballot replacement and no cancel-and-recast.
```

**This is an explicit architectural decision, not a deferral.** It is taken
because the alternative could not be shown to satisfy the constraints
PACK-15 leaves in place, and PACK-16A is required to prove supersession
rather than assume it.

**It is bounded, and the boundary is stated honestly:** no revoting means
the coercion mitigation that Estonia and Belenios rely on is unavailable to
EPD², and §5 states what is put in its place and what that costs.

`OD-P16A-01` carries the question forward for `EPD2-MIX-1` and for any
future profile, under conditions fixed in §6.

---

## 2. The options considered

| Option                                | Assessed                                                                                 | Verdict                    |
| ------------------------------------- | ---------------------------------------------------------------------------------------- | -------------------------- |
| **No revoting**                       | One authorisation, one ballot                                                            | **SELECTED**               |
| First valid ballot counts             | Later submissions rejected                                                               | rejected                   |
| **Last valid ballot counts**          | Later submissions supersede earlier ones — Belenios `last(B)` `[E-14]`; Estonia `[E-28]` | rejected                   |
| Explicit cancellation and recast      | A cancel act, then a new casting act                                                     | rejected                   |
| Online revote with in-person override | Estonia's model: paper on election day overrides the i-vote `[E-28]`                     | rejected for now; see §5.3 |
| Election-profile-dependent revoting   | Some contexts permit it, some do not                                                     | rejected                   |

### 2.1 Per-option assessment

| Criterion                            | No revoting                                           | First counts                             | **Last counts**                                                                                | Cancel + recast           | In-person override                                                  | Profile-dependent                                |
| ------------------------------------ | ----------------------------------------------------- | ---------------------------------------- | ---------------------------------------------------------------------------------------------- | ------------------------- | ------------------------------------------------------------------- | ------------------------------------------------ |
| Coercion mitigation                  | **none from this mechanism**                          | none                                     | **moderate**, and only if the coercer cannot occupy the end of the window `[E-14]`             | moderate                  | **strongest available**, because it changes the environment         | inconsistent, and inconsistency is itself a risk |
| Vote-buying risk                     | unchanged                                             | unchanged                                | **reduced** for a buyer who cannot observe the last act; unchanged otherwise                   | reduced                   | reduced                                                             | varies                                           |
| Continuation-capability implications | **clean** — `CC-01` exactly-once, `CC-08` no re-issue | clean                                    | **requires re-obtainable or multi-use authorisation** — conflicts with `CC-01`, `CC-08`        | same conflict             | none in the online path                                             | conflicting rules in one system                  |
| **Identity-linkage risk**            | **none added**                                        | none added                               | **requires a per-participant handle on the voting side to know which ballot supersedes which** | same                      | requires knowing **who** voted on paper — Estonia's design `[E-24]` | varies                                           |
| Duplicate-detection requirements     | board rejects duplicate `BallotId` (`BM-05`)          | same                                     | requires grouping ballots by participant — the handle again                                    | same                      | requires reconciling two channels by identity                       | varies                                           |
| Bulletin-board representation        | one entry per ballot; simple                          | simple                                   | superseded entries must remain on the board and be marked, or the board lies                   | same, plus cancel records | the online board must reflect an offline event                      | varies                                           |
| Ballot-secrecy consequences          | none added                                            | none added                               | superseded ballots must stay secret (CoE Std 25 `[E-56]`); grouping leaks the count of revotes | same                      | the paper channel is secret by other means                          | varies                                           |
| Dispute consequences                 | simple: cast or not cast                              | simple                                   | "which of my ballots counted?" is not answerable without a link — `ADR-098` conflict           | same                      | the override is a governance fact, not a per-ballot one             | varies                                           |
| German legal consequences            | neutral                                               | neutral                                  | neutral for internal votes; CoE Std 25 applies `[E-56]`                                        | neutral                   | closest to the paper-ballot baseline the law prefers `[E-51]`       | risk of an unexplainable rule                    |
| Usability                            | **one clear act**; a mistake is unrecoverable         | same, plus confusion about which counted | forgiving; but "did my revote work?" is a new anxiety                                          | most explicit; most steps | requires an in-person channel to exist                              | confusing across contexts                        |
| Accessibility                        | simplest to explain                                   | simple                                   | hardest to explain without cryptographic vocabulary                                            | hard                      | good, where a physical channel is reachable                         | worst                                            |

### 2.2 The proof that was required, and could not be given

The task of this round is not to choose a revoting policy by preference. If
supersession were selected, PACK-16A would have to show that it:

```text
does not require a person-to-ballot link
does not reuse credential ID
does not expose ballot choice
is visible in append-only evidence
cannot be performed silently by an administrator
```

**Requirement 1 could not be satisfied.** Supersession requires the system
to know that ballot B replaces ballot A — that is, to know that A and B
came from the same participation. Every deployed system that does this
supplies the knowledge the same way, with a per-participant handle on the
voting side:

- **Belenios** groups by the voter's **public credential**, and the server
  holds a list pairing public credentials with voter identity `[E-13]`.
- **Estonia** groups by **voter id**, with votes stored under
  `votes/<voter id>/` and the last vote selected by an offline processing
  application `[E-24]`.

PACK-15 forbids exactly this: `NO PERSISTENT MEMBER IDENTIFIER IN VOTING
DOMAIN`, and the structural rule that no store may hold an eligibility-side
and a voting-side reference for the same participation. A supersession
handle is a persistent voting-side per-participant identifier by
definition — it must be stable across at least two casting acts, which is
what "persistent" means.

**A handle that is not derived from identity is still a handle.** It could
be a random value issued at first cast and required at second cast. That
construction avoids identity but reintroduces a **reusable voting session**
(`CC-07` forbids it), requires client-side custody of a secret that
PACK-15 §13.3 prohibits from persisting outside the isolated origin, and
creates a bearer value whose surrender is a coercion instrument — which is
the JCJ **simulation attack** `[E-34]` reproduced in a simpler form.

### 2.3 The published evidence against last-counts

Four independent findings, each from a primary source:

1. **Revoting enables a verifiability attack.** Belenios's own caveats
   document: a malicious server can replace a voter's latest ballot with an
   earlier one after she has checked it, and _"this attack cannot be
   detected in Belenios 3.1 and earlier"_ `[E-15]`.
2. **Revoting defeats individual verifiability in the largest deployment.**
   A compromised voter device can defeat Estonia's verification mechanism
   _by taking advantage of the revoting option_, without compromising the
   verification app or any server component `[E-28a]`.
3. **Revoting-based coercion resistance was attempted properly and
   broken.** VoteAgain's deterministic ballot padding was the most credible
   attempt to make revoting a cryptographic control; third-party analysis
   found verifiability, privacy and coercion-resistance attacks and
   concluded that _"all voting authorities in VoteAgain need to be trusted
   for coercion-resistance"_, with **no fix proposed** `[E-44]`.
4. **The cleansing step leaks.** Even in JCJ, _"the cleansing step leaks
   more than the difference Δ between the sizes of its input and output"_ —
   revealing _why_ ballots were removed, and so whether a voter disobeyed
   `[E-37]`.

Taken together: **revoting is a temporal control that costs a
cryptographic property.** It mitigates a coercer who cannot occupy the end
of the voting window, and in exchange it weakens the verifiability that is
this architecture's central claim.

### 2.4 What is lost by refusing it, stated plainly

**Revoting is the only coercion mitigation Estonia has, and Belenios calls
it a "(moderate) protection against coercion"** `[E-14]`. Refusing it means:

- a voter coerced during her single casting act has **no in-system remedy**;
- a voter who casts under family or workplace pressure cannot quietly undo
  it later;
- a voter who makes a mistake cannot correct it.

These are real costs to real people and they are not offset by a
cryptographic property. §5 states what is offered instead. **The position
of this round is that a control which weakens verifiability while
protecting only against a coercer who leaves before the window closes is
not a good trade for EPD²'s contexts — and that the honest response to
coercion risk is to change the channel, not to add a second chance in a
compromised one.**

---

## 3. Ballot lifecycle

### 3.1 States

```text
prepared
encrypted
challenged
spoiled
submitted
cryptographically_validated
accepted
published
superseded_if_permitted        ← unreachable in EPD2-HOM-1; see §3.4
eligible_for_tally
excluded_with_public_reason
included_in_tally
tallied
archived
```

### 3.2 Transitions

Reversibility values: **none** (absorbing), **client-local** (reversible
inside the client before submission), **governed** (reversible only by a
recorded governance act).

| From → To                                   | Actor              | Input                                   | Proof                                         | Public evidence                        | Audit evidence                  | Failure code                        | Reversibility | Privacy constraint                                   |
| ------------------------------------------- | ------------------ | --------------------------------------- | --------------------------------------------- | -------------------------------------- | ------------------------------- | ----------------------------------- | ------------- | ---------------------------------------------------- |
| — → `prepared`                              | Voter, in client   | Selections; manifest; parameters        | none                                          | none                                   | none                            | `BALLOT_PREPARATION_REFUSED`        | client-local  | Selections never leave the client in the clear       |
| `prepared` → `encrypted`                    | Client             | Selections; randomness                  | Well-formedness proofs generated              | none                                   | none                            | `BALLOT_PROOF_GENERATION_FAILED`    | client-local  | Randomness never leaves the client                   |
| `encrypted` → `challenged`                  | Voter              | Challenge choice, after code commitment | Nonce release `[E-03]`                        | Spoiled ballot on the board            | Board stream                    | `BALLOT_CHALLENGE_FAILED`           | **none**      | Opening reveals a **test** ballot, not a cast vote   |
| `challenged` → `spoiled`                    | System             | Opening verified                        | Opening proof                                 | Published as spoiled                   | Board stream                    | —                                   | **none**      | Never tallied (`BM-09`)                              |
| `encrypted` → `submitted`                   | Voter              | Cast choice; casting authorisation      | Proof of knowledge of plaintext (`BM-14`)     | none yet                               | Credential stream (consumption) | `BALLOT_SUBMISSION_REFUSED`         | **none**      | Authorisation consumed atomically (`CC-01`)          |
| `submitted` → `cryptographically_validated` | Voting service     | Ballot and proofs                       | All proofs verified (`BM-15`,`BM-16`)         | none yet                               | Board stream                    | `BALLOT_PROOF_INVALID`              | **none**      | Verification reveals nothing about the choice        |
| `cryptographically_validated` → `accepted`  | Voting service     | Uniqueness and window checks            | Duplicate check (`BM-05`)                     | none yet                               | Board stream                    | `BALLOT_DUPLICATE_REJECTED`         | **none**      | —                                                    |
| `accepted` → `published`                    | Bulletin board     | Accepted ballot                         | Board append + checkpoint                     | **Board entry and confirmation code**  | Board stream                    | `BOARD_PUBLICATION_FAILED`          | **none**      | Published within the stated bound; batched (`BB-11`) |
| `published` → `eligible_for_tally`          | Board, at closure  | Closure checkpoint                      | Checkpoint signature                          | Closure checkpoint                     | Board stream                    | —                                   | **none**      | The set is fixed; no later addition (`BM-20`)        |
| `published` → `excluded_with_public_reason` | **Election Board** | Formalised ground                       | Recorded decision + reason code               | **Exclusion with reason on the board** | Board + governance              | `TALLY_EXCLUSION_REFUSED`           | **governed**  | Reason is privacy-safe; no identity, no choice (§4)  |
| `eligible_for_tally` → `included_in_tally`  | Tally process      | Ballot set                              | Aggregation is deterministic and reproducible | Published aggregate                    | Ceremony stream                 | —                                   | **none**      | No individual decryption                             |
| `included_in_tally` → `tallied`             | Trustee quorum     | Decryption shares                       | Share proofs (`BM-23`)                        | Result, shares and proofs              | Ceremony stream                 | `TALLY_SHARE_INVALID`               | **none**      | Only the aggregate is decrypted                      |
| `tallied` → `archived`                      | Archive Custodian  | Complete record                         | Archive integrity commitment                  | Archive manifest                       | Archive stream                  | `ARCHIVE_VERIFICATION_FAILED`       | **none**      | Archive is append-only; §6 of the failure model      |
| any → `superseded_if_permitted`             | **not reachable**  | —                                       | —                                             | —                                      | —                               | `BALLOT_SUPERSESSION_NOT_PERMITTED` | —             | §3.4                                                 |

### 3.3 Prohibited transitions — normative

```text
NO transition removes a published ballot.
NO transition alters a published ballot's ciphertext or proofs.
NO transition moves a ballot out of `spoiled`.
NO transition moves a ballot out of `tallied`.
NO transition is performed by a single administrator without recorded
   evidence and, where it affects inclusion, without Election Board decision
   and Independent Auditor concurrence.
NO transition is performed as a side effect of a support, incident or
   break-glass action.
NO transition is triggered by a deadline alone where its effect is a
   decision — canon 19d INV-10 applies here as it does in PACK-15.
```

Explicitly prohibited:

```text
silent replacement
silent deletion
silent exclusion
administrator-only invisible correction
post-hoc identity lookup
individual ballot correction through dispute handling
```

### 3.4 `superseded_if_permitted` — defined, and unreachable

The state exists in the specification-level model because the required
state list names it, and because a later profile may need it. **In
`EPD2-HOM-1` no transition reaches it, and any attempt is refused with
`BALLOT_SUPERSESSION_NOT_PERMITTED`.**

Should a later round make it reachable, the five obligations of §2.2 must
be discharged **in that round's documents**, plus:

| ID      | Obligation on any future supersession                                                                                   |
| ------- | ----------------------------------------------------------------------------------------------------------------------- |
| `SU-01` | Supersession must be visible on the board: the superseded entry stays, marked, and its absence would make the board lie |
| `SU-02` | The count of superseded ballots is subject to disclosure control and is not published before closure                    |
| `SU-03` | Supersession must be impossible for an administrator to perform, silently or otherwise                                  |
| `SU-04` | Superseded ballots must remain secret — Council of Europe standard 25 `[E-56]`                                          |
| `SU-05` | The grouping mechanism must be shown not to be a persistent voting-side per-participant identifier                      |

`SU-05` is the one that failed in this round.

---

## 4. Exclusion — the only way a ballot leaves the tally

A published ballot may be excluded from the tally **only** through
`excluded_with_public_reason`, and only under the following conditions.

| ID      | Condition                                                                                                                                 |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `EX-01` | The ground is **formalised in advance** and drawn from a closed list published with the election manifest                                 |
| `EX-02` | The exclusion carries a **privacy-safe reason code** revealing neither identity nor choice                                                |
| `EX-03` | The exclusion is recorded in **append-only evidence** and published on the board with the ballot's identifier and its reason              |
| `EX-04` | The exclusion is decided by the **Election Board** with **Independent Auditor concurrence**, never by an operator                         |
| `EX-05` | The exclusion is **independently verifiable**: a reader can confirm from the record that the excluded ballot is absent from the aggregate |
| `EX-06` | An exclusion that would change the outcome triggers the escalation in `PACK-16A-FAILURE-AND-ABORT-MODEL.md` `FM-P16A-18`                  |
| `EX-07` | **No exclusion may be based on who cast the ballot**, because that is not knowable and must not become knowable                           |

Closed list of permitted grounds:

```text
BALLOT_PROOF_INVALID              — a proof failed verification after publication
BALLOT_DUPLICATE_REJECTED         — a duplicate identifier or ciphertext
BALLOT_OUTSIDE_WINDOW             — published after the closure checkpoint
BALLOT_MANIFEST_MISMATCH          — contests do not match the frozen manifest
BALLOT_PARAMETER_MISMATCH         — encrypted under a different parameter set
```

**Nothing else.** A ground that is not on this list is not a ground, and
adding one is a manifest change made before `voting_open`, never after.

---

## 5. What replaces revoting

Refusing revoting removes a mitigation, so this section states what is put
in its place, and — more importantly — what those substitutes do **not** do.

| Control                                                          | What it mitigates                       | What it does **not** mitigate                           |
| ---------------------------------------------------------------- | --------------------------------------- | ------------------------------------------------------- |
| Single-visit casting inside an isolated origin (PACK-15 §13.4)   | Credential custody and helper retention | An observer present during the visit                    |
| No transferable receipt (`BM-03`)                                | Proof-of-vote sale after the fact       | Coercion during casting                                 |
| Challenge/spoil (`BM-07`…`BM-13`)                                | A cheating client                       | A coercer; challenging under observation proves nothing |
| A long voting window, so the participant chooses their moment    | An opportunistic observer               | A sustained household or workplace coercer              |
| Governed content stating that voting must be done in private     | Uninformed exposure                     | Anything, technically                                   |
| **An alternative in-person channel for the same context** (§5.3) | **The coercer's environment itself**    | Requires the channel to exist and to be reachable       |

### 5.1 The statement that must accompany every context

> This system cannot prevent someone from watching you vote, and it cannot
> undo a vote cast under pressure. If you may be watched or pressured, vote
> at a time and place where you are alone, or use the alternative channel
> if one is offered for this vote.

Plain-language wording, translation and placement are
`PACK-16A-ACCESSIBILITY-REQUIREMENTS.md` §5 and a governed-content
obligation for the relevant FRONT-PACK stage.

### 5.2 Why not simply adopt Estonia's model

Estonia's revoting **and** its paper override are causally linked to its
architecture: you cannot anonymise the ballot box until you know who voted
on paper, which is why the identity↔ciphertext binding persists through the
whole period and is severed by a trusted offline step `[E-24]`, `[E-28]`.
**The coercion mitigation and the late anonymisation are the same design
decision.** EPD² cannot take the mitigation without taking the
architecture, and the architecture is the one PACK-15 exists to refuse.

### 5.3 In-person override — assessed, not adopted

An in-person channel that supersedes an online vote is the **strongest**
coercion control available, because it changes the environment rather than
adding a second chance in a compromised one. It is **not adopted in this
round** for one reason: reconciling the two channels requires knowing which
participants voted in person, which is a per-participant fact that must
reach the tally. Estonia solves it by keeping the identity binding; that
route is closed here.

A route that might work — the in-person channel invalidating the **whole
online context** for a declared sub-population, at scope level rather than
per person — is recorded as `OD-P16A-09` and is not designed here. What is
**not** deferred is the alternative already available today: for a context
with high coercion risk, **governance may decide not to hold it
electronically at all**, and
`PACK-16A-GERMAN-LEGAL-BOUNDARY.md` §8 makes that an explicit outcome of
the activation gate rather than an admission of failure.

---

## 6. Conditions under which the revoting decision would be re-opened

1. A published construction achieving supersession **without** a persistent
   voting-side per-participant handle, with a machine-checked proof.
2. Activation of a profile where the handle problem does not arise.
3. A governance finding that coercion risk in a specific context class
   outweighs the verifiability cost — which would still require §2.2's five
   obligations to be discharged, not waived.
4. A legal requirement that revoting be offered.

`OD-P16A-01` records the question. **Until then, the answer is no, and it
is written down rather than left to an implementation to decide quietly.**

**SPECIFIED. DECIDED. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY. NOT
LEGALLY ACTIVATED.**
