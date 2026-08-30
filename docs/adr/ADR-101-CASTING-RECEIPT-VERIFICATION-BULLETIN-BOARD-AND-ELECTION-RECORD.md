# ADR-101 — A ballot becomes irreversible at one atomic instant, and everything after it is published so that a stranger can check it

**Status:** proposed
**Round:** PACK-16C — Casting, Receipt, Verification Client, Bulletin Board and Election Record (specification and ADR only)
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`

**NO CODE. NO CRYPTOGRAPHIC IMPLEMENTATION. NOT IMPLEMENTED. NOT A
CANDIDATE FOR IMPLEMENTATION. NOT A PASS. NOT PRODUCTION READY. NOT LEGALLY
ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

Evidence references `[G-nn]` resolve in
`docs/packs/PACK-16/PACK-16C-PROTOCOL-EVIDENCE-MATRIX.md`.
`[F-nn]` resolve in `PACK-16B-PROTOCOL-EVIDENCE-MATRIX.md`, unchanged.
`[E-nn]` resolve in `PACK-16A-PROTOCOL-EVIDENCE-MATRIX.md`, unchanged.

---

## Context

`ADR-099` chose the protocol. `ADR-100` chose the parameters, the guardians
and the ceremony. Neither says what happens in the minutes when a member
actually votes, or what anyone can check afterwards.

```text
PACK-16A chose the protocol.        EPD2-HOM-1, no revoting
PACK-16B chose the numbers,         EPD2-CRYPTO-1, k of n,
         the people and the room.   no pre-closure decryption
PACK-16C chooses the moment a
         ballot becomes final, and
         what the world may see.
PACK-16D will choose what code runs.
```

Three questions had to be answered together, because each constrains the
others:

1. **When exactly is the continuation capability consumed**, relative to
   cryptographic validation and acceptance — and what does that ordering
   prevent?
2. **What may a voter be given afterwards** that lets them check their
   ballot without letting anyone else learn their choice?
3. **What must be published** so that a stranger with no account, no
   credential and no trust in EPD² can check the outcome?

This ADR records the third of the four decisions.

---

## Inherited decisions — not reopened

```text
EPD2-HOM-1                 homomorphic exponential ElGamal, threshold
                           decryption, NIZK well-formedness proofs,
                           Benaloh cast-or-challenge
NO REVOTING                a voter casts once; no supersession exists
EPD2-CRYPTO-1              the parameter family, adopted unmodified
BASE-HASH CHAIN            ver → H_P → H_B → H_E → H_I
k OF n GUARDIANS           k ≥ 3 always; k may never be reduced
NO BREAK-GLASS             no hidden key, no compensated decryption
NO PRE-CLOSURE DECRYPTION  nothing is decrypted before closure
NO INTERMEDIATE TALLY      NIT-01 … NIT-07
CONTINUATION CAPABILITY    PACK-15's one-time, unlinkable, non-identity
                           capability — never joined to a ballot
VO-08                      OPEN. Owned by PACK-16B external cryptographic
                           review, confirmed by PACK-17. NOT owned here.
```

**This ADR alters none of them, and claims approval of none of them.**

---

## Decision drivers

| Driver                                                    | Consequence                                                         |
| --------------------------------------------------------- | ------------------------------------------------------------------- |
| A voter must never lose a participation to a system fault | Nothing is consumed until every check has passed                    |
| A voter must never be able to vote twice                  | Consumption is exactly-once, inside the boundary                    |
| Nobody may learn who voted for what                       | The two halves of the boundary share no key, no trace, no timestamp |
| A stranger must be able to check the result               | Everything needed is published, in bulk, without an account         |
| A publication failure must be impossible to hide          | Signed commitment, published deadline, public dispute state         |
| Nothing may be claimed that is not true                   | The prohibited-claims registry is enforced over published text      |
| The record is permanent and cannot be unpublished         | Every field is decided before publication exists                    |

---

## Consumption-point candidates

| Option | Consume at                                                                 | Failure cost to the voter                      | Double-vote risk                                               | Verdict      |
| ------ | -------------------------------------------------------------------------- | ---------------------------------------------- | -------------------------------------------------------------- | ------------ |
| A      | Statement of intent, before encryption                                     | **A client defect costs the voter their vote** | none                                                           | rejected     |
| B      | On receipt of the envelope, before validation                              | A malformed ballot costs the vote              | none                                                           | rejected     |
| C      | **Inside an atomic boundary, after all checks, before durable acceptance** | **none — a failed check costs a retry**        | none                                                           | **selected** |
| D      | After publication, two-phase with compensation                             | none                                           | **A crash between accept and consume permits a second ballot** | rejected     |

Option D was rejected not because compensation is impossible but because a
compensating transaction across the capability store and the ballot store
**requires a join between them** in order to know what to compensate —
which is precisely the link the architecture removes.

---

## Selected consumption point

```text
Stages 1–18   repeatable · nothing consumed · nothing durable
              a failure here costs the voter a retry, and nothing else

    ——— ATOMIC BOUNDARY OPENS ———
Stage 19      re-check the capability is unspent, INSIDE the boundary
Stage 20      consume it, exactly once
Stage 21      record the ballot as durably accepted
Stage 22      sign and return the publication commitment
    ——— ATOMIC BOUNDARY CLOSES ———

Stage 23      commit the leaf in the NAMED sealed batch window, then
              open it at closure, append-only
              failure here is PUBLIC, never silent
```

**Every cryptographic check is before the boundary and may never be moved
into or after it. Nothing cryptographic happens after consumption.**

---

## Atomicity requirements

The boundary must give an **exactly-once** effect across two stores that
**must not share a key, a surrogate key or a correlation column**
(`DM-10`). The semantics are specified (`CN-17`…`CN-20`). The mechanism is
not.

```text
If PACK-16D cannot demonstrate the exactly-once property under
concurrency, crash and partition, that is an ARCHITECTURAL BLOCKER
for implementation acceptance — not a risk to be accepted.
```

Carried as `OD-P16C-01`.

---

## Ballot identity model

Four values, four purposes, none derivable from another:

```text
ballot_id            client-random, structureless, published
confirmation_code    derived from the encryptions and H_E, published,
                     what the voter looks up
board_sequence       the board's ordering; NEVER on the receipt
internal_object_id   operational only; NEVER published, never in the record
```

A single reused identifier was rejected: every purpose it would serve makes
a different value observable to a different party, and collapsing them
creates a join.

---

## Envelope and canonical encoding

Canonical serialization is **normative now**, because signatures depend on
it and a record that re-serialises differently from what was signed cannot
be checked against its own signatures. Envelopes are **fixed-length per
ballot style**, because a length that varies with selections leaks the
selection. The wire container — JSON, CBOR or other — is `OD-P16C-04`.

---

## Cast-or-challenge policy — CORRECTED

**Commitment before choice.** The confirmation code is committed and shown
_before_ the voter chooses, so a dishonest client cannot decide what to
encrypt after learning which path the voter took. Unchanged.

**The correction: unlimited challenge semantics apply only to LOCAL
diagnostic challenge repetitions.**

The previous candidate offered one challenge action, repeatable without
limit, and every repetition produced a **published** spoiled ballot. Against
a sealed batch of finite capacity `C`, an unbounded number of
publication-bearing artefacts is not a bound at all. _"C exceeds the maximum
plausible load"_ was a hope, not a bound, and the audit was right to reject
it.

Benaloh cast-or-challenge is **not** weakened. It is split into the two
things it was always doing at once:

```text
LOCAL DIAGNOSTIC CHALLENGE     unlimited
  the voter checks THIS DEVICE, locally, as often as they like.
  Nothing is submitted, nothing published, nothing spent, no server
  state changed, no event emitted.                    CH-39 ... CH-42

PUBLIC EVIDENTIARY CHALLENGE   K = 1 in the initial profile
  public audit evidence against a dishonest client: submitted,
  validated, committed to a sealed-batch leaf, opened at closure,
  NEVER counted, and it does NOT consume the cast entitlement.
                                                      CH-43 ... CH-46

FINAL CAST BALLOT              A = 1
```

**A capability can therefore generate at most one public challenged/spoiled
artefact and at most one final accepted cast ballot** (`CN-35`). That is the
finite publication-bearing bound the whole capacity plan rests on.

`K = 1` and `A = 1` are **architectural constants of the initial protocol
profile**, not runtime configuration. They may not vary per user, per
device, per session, by turnout, or during an election, and changing `K`
requires a new governed profile version, an architectural review, a
recomputed capacity plan and a privacy review (`CH-37`, `CH-38`).

**The honest limitation, stated in the interface and in the record:** _a
malicious client can fake a purely local diagnostic challenge. Public
evidentiary challenges and independent verification remain necessary for
evidence against client misbehaviour_ (`CH-40`, `CH-41`, `T-P16C-62`).

**No detection guarantee is claimed.** Detection is probabilistic and
depends on take-up, which is empirically low `[E-29]`.

---

## The finite publication-bearing bound

```text
E = maximum number of continuation capabilities that may be VALID for
    the election under the eligibility snapshot and issuance policy
K = maximum public evidentiary challenges per capability   = 1
A = maximum accepted cast ballots per capability            = 1

L_max = E x (K + A) = E x 2
```

**Capacity is planned from `E`, not from plausible turnout** (`TC-60`). A
plan that assumes turnout fails exactly when turnout surprises it. **The
architecture is closed and the numbers are open**: `N`, `C`, `R`, the slot
partition and the safety reserve are election-governed configuration,
selected before opening and validated against `L_max` (`OD-P16C-10` §1.1,
`OD-R16`, `OD-R17`). Cover
leaves are not publication-bearing and are not counted in `L_max`
(`TC-62`); only explicitly enumerated system leaves may be added, and
checkpoint metadata is not a leaf (`TC-63`).

**Total scheduled capacity must satisfy** `Σ C_interval ≥ L_max + published
safety reserve`. A plan that does not is `election.capacity_plan_invalid`
and the context is **not activated** (`TC-64`, `FM-16C-30`).

---

## Per-window capacity, reservation and exhaustion

Total capacity is not enough: one window can overflow while the election has
room.

```text
Per interval, governance predeclares
    1 primary commitment        capacity C_primary
    R reserve commitments       capacity C_reserve each
    C_interval = C_primary + R x C_reserve

ALL of them publish on schedule, EVEN WHEN EMPTY, with fixed capacity
and indistinguishable public structure.                 TC-66, TC-67

A reserve that appears only under load would announce a busy interval.
Adaptive creation of an unscheduled batch is PROHIBITED. TC-68, BA-27

No publication-bearing submission is durably accepted without an
ATOMICALLY RESERVED leaf slot. Accept-then-find-room is prohibited.
                                                        TC-70, CN-42, CN-43

Capacity is PARTITIONED in advance into cast-reserved and
public-challenge-reserved slots. A public challenge may NEVER consume a
cast-reserved slot — checking may never crowd out voting.
                                                        TC-74, TC-75, FM-16C-34
```

**On exhaustion** (`FM-16C-29`): fail closed for new publication-bearing
submissions, pause public challenges immediately, **preserve unused cast
entitlements**, publish a privacy-safe capacity incident carrying **no
figure**, and enter the governed pause / extension / abort / re-run path.
Indefinite client retry is not a remedy (`TC-78`).

**Prohibited categorically:** silently creating an unscheduled batch;
silently enlarging `C`; dropping a challenged artefact; accepting a cast
ballot without a committed leaf; moving an artefact to a hidden queue
(`TC-79`, `TC-80`).

---

## Validation pipeline

Twenty-three ordered stages, each with a **distinct reason code**. Fail
closed throughout: no provisional acceptance, no asynchronous validation
queue, no normalisation of a proof before verifying it, no coercion of a
field, and **no sampled subgroup checks** — every element, every ballot,
every time.

A single `BALLOT_INVALID` is prohibited: the difference between a
range-proof failure and a canonical-encoding failure is the difference
between a defective client and an attack.

---

## Ballot lifecycle

Sixteen states. PACK-16A's fourteen are **extended, not redefined**; every
prohibited transition remains prohibited; `superseded_if_permitted` remains
**defined and unreachable**, because a future profile that permits
supersession must not have to invent a state silently.

The five new states — `submission_uncertain`, `cryptographically_validating`,
`accepted_pending_publication`, `publication_disputed`, `rejected` — make
existing failure modes **nameable**. None creates a new path into the tally.

---

## Receipt

The receipt proves that **a ballot carrying this confirmation reference was
accepted and published**. Nothing else. It carries no nonce, no opening, no
credential, no board position and no exact time. It is re-derivable from
public data, so it is not a bearer token and nothing depends on retaining
it.

**Its real cost is that it proves participation.** A coercer who demands to
see one learns the person voted. That is accepted, recorded, and not solved.

---

## Coercion and receipt boundary

`EPD2-HOM-1` is **coercion-mitigating, not coercion-resistant**, and nothing
in this round changes that. PACK-16A's permitted and prohibited claims
registries are **extended and not altered**: eight permitted claims added,
ten prohibited claims added, each prohibited claim paired with a permitted
alternative in the governed catalogue.

The sharpest unsolved case is the **challenge-transcript pattern** — a
coercer demanding "challenge showing X, then cast". Nothing in the record
distinguishes that from honest use. It is named, not solved, and it is one
reason the in-person channel remains the coercion answer.

---

## Verification Client

A **separate published origin**, with a published build digest and a
reproducible build, reachable without an account, without accepting terms
and without JavaScript for the underlying data. Verification on a second
device is the stronger design and is not required, because requiring it
would exclude voters who have only one device.

**Offline verification is a required capability**, not an option.

---

## Independent verifier requirements

Twenty-one checks, all performable from the published record alone. The
**official verifier is never sufficient** — a system verifying itself has
proved nothing to anyone who does not already trust it — and **at least one
verifier not written or commissioned by EPD² must verify a real context
before any binding use** (`BM-28`).

Every verifier result states **what it did not check**. A `VERIFIED` result
that omits its limits is misleading and is prohibited. A `VERIFIED` result
is **not** a certification.

---

## Bulletin board structure

A **Merkle transparency log** with chained signed checkpoints, mirror
co-signing and published checkpoint gossip. The construction is the one
specified in RFC 6962 and RFC 9162 `[G-01]` `[G-02]`: append-only Merkle
tree, inclusion proofs, consistency proofs, periodically signed tree heads.

A signed flat log was rejected as unable to prove non-insertion; a database
with an audit table was rejected because the audit table is under the same
authority as the data; a blockchain was rejected as adding a consensus
problem EPD² does not have and a governance problem it cannot solve.

---

## Append-only and consistency model

Inclusion and consistency proofs must be **recomputable offline** from bulk
board data, because a verifier must never have to ask a server for the proof
it is checking that server with `[G-04]`.

Publication order within a batch is **randomised**, so board position does
not encode arrival order.

---

## Split-view resistance — the honest position

```text
The board is TAMPER-EVIDENT, and only if someone checks.
It is NOT tamper-proof, and may never be described as such.
```

RFC 9162 §11.3 states that a misbehaving log showing different views to
different clients can circumvent auditing, and puts the fix **out of scope**
`[G-01]`. RFC 6962 §5 deferred the gossip mechanism to a separate document
`[G-02]`. That document — `draft-ietf-trans-gossip` — **expired at revision
05 in 2020 and never became an RFC** `[G-03]`. The community witness
protocol that exists today does not claim the property and explicitly flags
partitioning `[G-04]`.

**Until external witnesses exist, EPD²'s split-view resistance rests on
organisational mirror independence, not on cryptography** `[G-05]`. Carried
as `OD-P16C-12`; a blocker for production implementation acceptance, not for
this specification round.

---

## Publication atomicity

**Durable acceptance + signed publication commitment + published deadline.**
Publication inside the atomic boundary was rejected because it makes the
board's availability a precondition for accepting a ballot; publish-then-
accept was rejected because it publishes unverified ballots.

The construction is adapted from RFC 6962's **Maximum Merge Delay** — _"the
log's promise to incorporate the certificate in the Merkle Tree within a
fixed amount of time"_ `[G-02]` — with the consequences of a broken promise
being entirely different, and treated as such.

**There is no permitted terminal state "accepted but never published".**

---

## Publication failure and lost participation

If the boundary commits and publication then fails past the deadline and
past the escalation window, the ballot is cast, the capability is spent, and
**that participation is lost for this context**.

```text
The capability is NEVER restored. Restoring it would permit a second
ballot from a voter who may already have one on the board.

The record's integrity is chosen over repairing an individual
participation. This is a deliberate, published trade-off, and it is
told to voters in advance rather than discovered at a dispute desk.
```

---

## Election record

**Thirty-seven mandatory artefacts**, sufficient for a stranger with no
account, no credential and no trust in anyone who ran the election to check
the announced result using software they can rebuild themselves.

The record is self-describing, downloadable in bulk, byte-identical across
mirrors, and **does not depend on any EPD² service being alive**. A copy
taken today must remain checkable when the organisation no longer exists —
that is the point of publishing it.

---

## Record completeness

The completeness matrix joins artefacts and checks **in both directions**.
Thirty-three artefacts serve at least one check. **Four serve none** —
aggregate rejection counts, published failure notices, independent verifier
reports, and the "what you cannot check" statement — and are mandatory
anyway, because they are what makes the record honest rather than merely
verifiable. **No check lacks an artefact.**

**Twenty-one checks**, of which five — cadence completeness, root
recomputation, reconciliation, capacity-bound conformance and
capacity-incident completeness — are performable only after closure,
because the openings that make them possible are what make occupancy public
(`EC-14`).

Seven questions can never be served by any artefact, and adding one to close
the first — _did each ballot come from a distinct entitled person_ — is
**prohibited**, because any such artefact would by construction create a
person-to-ballot link.

---

## Turnout confidentiality — CORRECTED

A public append-only board **is a live turnout feed by construction**.
Removing a counter endpoint does not remove the number.

**The first candidate's answer — fixed-size batches with padding entries —
was rejected on audit and is superseded** (`TC-21`). It failed for a
structural reason, not a sizing one: a padding entry carrying no ciphertext
is distinguishable from an accepted ballot, so an observer counted the
ciphertext-bearing entries and had the live figure exactly. It also asserted
an entry type the board catalogue never contained.

**The accepted decision is fixed-cadence sealed fixed-capacity batch
commitments.**

```text
Before closure the board publishes NO individual ballot entry and NO
count of accepted ballots.

At each fixed window it publishes ONE constant-size entry:

    sealed_batch_commitment

a Merkle commitment to a FIXED-CAPACITY batch of C leaves.

A real leaf is a hiding commitment over one ballot artefact's digests
under a high-entropy salt. A cover leaf is a uniformly random value of
the leaf's exact size. Before closure they are INDISTINGUISHABLE.

An empty window publishes its commitment like any other, because
absence of an entry would itself be a disclosure.

At closure every batch is opened in full — real leaves with their
salts and committed fields, cover leaves with their values — and a
batch_reconciliation_record maps every ballot artefact to exactly one
occupied leaf and back.
```

**What this buys.** No pre-closure observation distinguishes an election
with one ballot from one with `C` per window. Turnout becomes public at
closure and not before.

**What it costs.** At closure, leaf index and batch membership localise a
ballot's acceptance to one interval (`T-P16C-46`). That is strictly less
than a running total, and it is not nothing.

Where a context is too small for the anonymity set to protect anyone, the
answer is not a longer window: **the context is not activated
electronically** (`TC-16`).

---

## Individual verification under the sealed batch layer

The obvious objection to hiding ballots until closure is that a voter can no
longer check their ballot while the election runs. **That objection is
answered, not accepted.**

A voter holding a confirmation code obtains a **privacy-safe commitment
inclusion proof**: their own leaf opening plus a Merkle path to the batch's
`commitment_root`, anchored to a signed checkpoint. Every value on that path
is either a hiding commitment or a uniform random value, so the proof
**reveals nothing about occupancy** (`TC-36`…`TC-40`, `API-20`).

**This is strictly stronger than the rejected model offered.** Because the
publication commitment names a _specific_ batch window, a voter can detect
non-publication **at that window, during voting** — where the first
candidate's model gave them no definite moment to check (`PA-12`,
`FM-16C-20`, `DP-19`).

---

## Why cover leaves are not ballots, and why this is not ballot stuffing

```text
A cover leaf is NOT accepted, NOT tally-eligible, carries NO ciphertext,
consumes NO continuation capability, produces NO receipt and creates NO
ballot state anywhere in BL-*.

Only an accepted ballot backed by an atomically consumed capability can
occupy an `accepted` leaf.

A cover leaf cannot be converted after its commitment is published:
doing so requires a second preimage of a uniformly random value.

Closure reconciliation binds every real leaf to a durable
BallotAcceptanceRecord by the acceptance-record digest inside the leaf.

The accepted-ballot count is compared with the unique consumed-capability
acceptance count in Auditor-restricted evidence. That comparison is TWO
COUNTS PRODUCED INDEPENDENTLY BY TWO STORES, never a join — it cannot
reconstruct identity-to-ballot linkage (TC-52, DM-10).
```

**The commitment layer sits strictly above the ballot layer.** It does not
modify the ElectionGuard encrypted-ballot format, the ciphertext structure,
the proof system, `EPD2-CRYPTO-1`, or the homomorphic tally. A conforming
ElectionGuard 2.1 verifier reads the ballots and the tally exactly as before
(`TC-46`…`TC-48`).

**What it does not buy:** issuance-side ballot stuffing remains outside what
the record can show. That limit is `VP-17` and is unchanged.

---

## Privacy and metadata

Thirty-four metadata fields enumerated, each with who sees it, whether it is
published, whether it is retained, and what is done about it. **The default
is non-retention.** The prohibition is on the **join**, not the field: a log
line that would let two "never joined" fields be correlated is prohibited
even where each field alone is permitted.

Four channels remain open and are declared rather than mitigated away:
network-layer observation, issuance-to-submission timing, small-context
statistics, and gateway/edge infrastructure.

---

## Accessibility

A verification step a person cannot perform is a verification step that does
not exist for them. BITV 2.0 / EN 301 549 / WCAG 2.1 AA is the floor for
**every** surface, including the Verification Client and the record's
human-readable views. **Accessibility acceptance is a gate on activating a
context**, not a phase of PACK-16D.

Six tensions — challenge complexity against cognitive accessibility, second-
device verification against device access, code length against transcription,
assistance against secrecy, proof cost against modest hardware, and
accessibility against anti-coercion — are **stated rather than resolved**.

---

## Dispute and support boundary

```text
Support can help a voter USE the system.
Support can NEVER help a voter's BALLOT.
```

This is architectural, not procedural: no operator at any permission level
can find, read, change, re-cast, recover or delete a specific person's
ballot, because the system does not contain the link that would let them.
Eight dispute classes, each with one owner and a published outcome. **No
dispute is resolved by acting on an individual ballot.**

---

## API and data-model boundaries

No operation takes an identity, a credential, a session or a membership as
input. Every board and record read is public. Ten operations are listed as
**prohibited**, so that their absence is checkable rather than assumed — and
a prohibition is **not** satisfied by requiring elevated permission.

`DM-10` is the single most important schema statement in the pack: the
acceptance record and the capability consumption record are **separate
stores with no foreign key, no shared surrogate key and no common
correlation column**. The boundary writes to both; nothing ever reads them
together.

---

## Events and observability

An event stream is a correlation surface with a nice name. **No trace, span
or correlation identifier spans the atomic boundary** — distributed tracing
that joins the submission to the consumption reconstructs exactly the link
the design removes.

**Corrected: the capability-side half of each atomic boundary is not an
event at all.** Capability consumption on the cast path and public-challenge
entitlement consumption on the challenge path are **internal transactional
state changes**, atomic with acceptance, recorded only as privacy-restricted
audit evidence that carries no capability reference. Neither crosses an
event bus, and a renamed replacement that still does is the same defect
under another name (`EV-71`, `EV-74`, `EV-75`, `EV-76`). Two events —
`capability.consumed` and `challenge.public_entitlement_consumed` — were
**deleted**, and their identifiers are retired rather than reused
(`EV-78`).

**Eleven event classes are listed as must not exist**, including
`voter.voted`, any live turnout counter, any lookup event, and any payload
carrying a continuation capability or a derived form of one. **A voter
checking their confirmation code emits nothing, anywhere, ever**, and a
local diagnostic challenge emits nothing either (`EV-70`).

---

## Reason codes

Eighty-eight codes across sixteen new namespaces; seven codes reused from
earlier rounds **without redefinition**. No generic code exists and none may
be added. **The code names the check, never the value.**

Registration happens in PACK-16D; nothing is written to the Canonical Schema
Registry in this round.

---

## Failure and abort model

Thirty-four failure modes. **No outcome anywhere acts on an individual
accepted ballot.** `reject` and `retry` are voter-level and act on an
envelope; `pause`, `abort`, `annul` and `re-run` are election-level.
Nineteen modes require Independent Auditor concurrence in some branch.

**The capacity correction adds six more** (`FM-16C-29`…`FM-16C-34`), including `FM-16C-29` —
batch-capacity exhaustion — which fails closed, pauses public evidentiary
challenges, **preserves unused cast entitlements**, publishes a figure-free
incident and enters the governed pause / extension / abort / re-run path.
**Silent recovery is prohibited** (`TC-79`, `FMR-20`).

A confirmed `challenge.reencryption_mismatch` — a client encrypting
something other than what a voter chose — is the system's alarm: published
in full, suspends the build, and is a candidate for annulment.

---

## Threat model extension

Fifty-seven new threats, **each with a residual**, plus one new adversary:
the **board reader**, who fetches every public artefact forever and
correlates them with what they already know. Everything published is
designed against that adversary.

```text
Threats fully solved by this round: 0.

A threat model whose mitigations close every row is describing a
system that does not exist.
```

---

## Evidence base

Five evidence entries. **Four new primary sources, all read first-hand on
2026-08-01** and quoted with section numbers; one inference, marked as such.
Fourteen inherited entries cited **as inherited**, with no re-attestation of
a reading this round did not perform.

**All four new sources are from the certificate and software-supply-chain
domain. None concerns elections.** The construction transfers; the threat
model does not. Stated plainly rather than glossed.

**Six of this round's central decisions rest on no external source at all**,
and are marked as reasoned rather than evidenced.

---

## Rejected alternatives

| Rejected                                                                      | Why                                                                                                                                                                                                                                                                                                                  |
| ----------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Consume the capability before validation                                      | A client defect would cost a voter their vote                                                                                                                                                                                                                                                                        |
| Two-phase consumption with compensation                                       | Compensation requires the join the architecture removes                                                                                                                                                                                                                                                              |
| One reused ballot identifier                                                  | Collapses four observability domains into one join                                                                                                                                                                                                                                                                   |
| Fixed challenge probability                                                   | Makes detection a lottery the voter does not control                                                                                                                                                                                                                                                                 |
| System-forced challenge                                                       | Removes agency; trains voters to click through                                                                                                                                                                                                                                                                       |
| Signed flat log                                                               | Cannot prove non-insertion                                                                                                                                                                                                                                                                                           |
| Database with an audit table                                                  | The audit table is under the same authority as the data                                                                                                                                                                                                                                                              |
| Blockchain                                                                    | Adds a consensus problem EPD² does not have and a governance problem it cannot solve                                                                                                                                                                                                                                 |
| Publish inside the atomic boundary                                            | Makes board availability a precondition for accepting a ballot                                                                                                                                                                                                                                                       |
| Publish before validation                                                     | Publishes unverified ballots                                                                                                                                                                                                                                                                                         |
| Withhold the board until closure                                              | Destroys voter verification during voting                                                                                                                                                                                                                                                                            |
| **Unlimited publicly committed challenge artefacts per capability**           | **No finite capacity bound exists**; one capability can exhaust the board; DoS by a single capability; incompatible with a fixed-shape turnout-hiding publication model that requires a computable maximum. **Rejected on audit** (`CH-36`, §1A.4)                                                                   |
| Bounding public challenges by rate rather than by entitlement                 | A rate limit bounds speed, not total. `L_max` must be computable before the election opens                                                                                                                                                                                                                           |
| Bounding public challenges globally rather than per capability                | A race: the first voters to check exhaust the budget and the rest cannot                                                                                                                                                                                                                                             |
| Adaptive overflow batches created under load                                  | A batch that appears only when busy announces that it is busy (`T-P16C-54`)                                                                                                                                                                                                                                          |
| A hidden overflow queue for artefacts with no slot                            | Accepted-but-unscheduled is the state `PA-07` exists to forbid                                                                                                                                                                                                                                                       |
| Unpadded batches                                                              | Batch size is exact turnout per interval                                                                                                                                                                                                                                                                             |
| **Public real-time ballot entries with structurally distinguishable padding** | **Leaks live turnout** — an observer counts the ciphertext-bearing entries; **creates a catalogue inconsistency** — the padding type was asserted in prose and never catalogued; and **does not satisfy the inherited invariant** `NO TURNOUT DISCLOSURE BEFORE CLOSURE`. Rejected on audit and superseded (`TC-21`) |
| Adaptive batch cadence                                                        | A cadence that reacts to turnout is a turnout channel (`TC-24`, `T-P16C-43`)                                                                                                                                                                                                                                         |
| Withholding the board entirely until closure                                  | Destroys individual verification during voting, which the sealed commitment preserves                                                                                                                                                                                                                                |
| Publishing occupancy counts per window                                        | That is the turnout figure                                                                                                                                                                                                                                                                                           |
| Same-origin Verification Client                                               | A compromised origin verifies itself                                                                                                                                                                                                                                                                                 |
| Camera-only verification                                                      | Excludes voters and adds a substitution surface                                                                                                                                                                                                                                                                      |
| Restoring a spent capability after a publication failure                      | Permits a second ballot from a voter who may already have one on the board                                                                                                                                                                                                                                           |

---

## Residual risks

| ID          | Risk                                                                                                                                                                    | Severity | Owner                              |
| ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- | ---------------------------------- |
| `RB-16C-01` | **Issuance-to-submission timing correlation is reduced and bounded, not eliminated.** A global observer of both sides retains signal                                    | high     | PACK-17                            |
| `RB-16C-02` | Split-view resistance rests on **organisational** mirror independence until witnesses exist                                                                             | high     | `OD-P16C-12`, PACK-17              |
| `RB-16C-03` | An operator with database access to **both** boundary stores plus precise timing could correlate                                                                        | high     | PACK-16D, governance               |
| `RB-16C-04` | Challenge take-up is empirically low; detection is probabilistic across the electorate                                                                                  | medium   | governance, front end              |
| `RB-16C-05` | A publication failure past every window **loses a participation**                                                                                                       | medium   | `PA-08`, governance                |
| `RB-16C-06` | Turnout is public at closure by design; the sealed batch layer bounds pre-closure disclosure to nothing, not to less                                                    | medium   | `OD-P16C-10`                       |
| `RB-16C-07` | Ballot stuffing is not checkable from the record; the controls are PACK-15's                                                                                            | high     | PACK-15, PACK-17                   |
| `RB-16C-08` | The atomic boundary's mechanism is unproven                                                                                                                             | high     | `OD-P16C-01`, PACK-16D             |
| `RB-16C-09` | Six central decisions rest on no external source; the sealed batch layer is `INF`-grade throughout (`G-R09`)                                                            | medium   | external review                    |
| `RB-16C-10` | **A weak cover-leaf generator would break leaf indistinguishability silently before closure**, and nothing published would reveal it                                    | high     | PACK-16D, `T-P16C-45`              |
| `RB-16C-11` | At closure, leaf index and batch membership localise a ballot's acceptance to one interval                                                                              | medium   | `OD-P16C-10`, `T-P16C-46`          |
| `RB-16C-12` | **`L_max` scales with `E`.** An issuance policy that over-issues capabilities inflates the capacity plan and the published record with it                               | medium   | governance, `T-P16C-51`            |
| `RB-16C-13` | **A leaked leaf reservation shrinks real capacity with no public sign** until the closure reconciliation                                                                | medium   | PACK-16D, `T-P16C-57`, `FM-16C-33` |
| `RB-16C-14` | **A capacity incident's existence is itself a signal** that the election is busier than planned; it is published anyway, because concealing a capacity failure is worse | low      | accepted, `T-P16C-58`              |
| `RB-16C-15` | **The per-capability bound is publicly checkable only in aggregate.** The privacy-preserving per-capability proof is not specified by this round                        | high     | `OD-P16C-19`, PACK-16D, PACK-17    |
| `RB-16C-16` | **A malicious client can fake a local diagnostic challenge**, and moving unlimited checking to the local tier returns exactly that to the attacker                      | medium   | accepted and stated, `T-P16C-62`   |

**`RB-16C-01` is the residual this ADR would most like to have closed and
could not.**

---

## Open decisions

Nineteen, each with an owner and a named consequence: `OD-P16C-01` …
`OD-P16C-19`. Two block production implementation acceptance, three block
binding use of a context, one blocks certification, three block a property
in practice, one blocks a feature-specific context, and six block nothing at
specification stage.

**The capacity correction closed four architectural questions** — whether
public challenge publication is bounded, the initial-profile `K`, whether
local challenges occupy leaves, and the finite-capacity formula — **and
opened three implementation ones**: reservation storage (`OD-P16C-17`),
stress-testing thresholds (`OD-P16C-18`) and the privacy-preserving
per-capability reconciliation proof (`OD-P16C-19`), the last of which is an
**`ARCHITECTURAL BLOCKER` for certification** if no sufficient evidence
boundary can be constructed.

**The turnout correction closed one architectural question and opened three
encoding ones.** Live-turnout confidentiality is no longer open: the model
is selected and PACK-16D may not substitute another (`OD-R09`). What remains
are the interval and capacity (`OD-P16C-10`), the leaf-commitment
construction (`OD-P16C-14`), the inclusion-proof format (`OD-P16C-15`) and
the opening and reconciliation formats (`OD-P16C-16`).

**No inherited open decision is closed, advanced or re-owned by this round —
`VO-08` least of all.**

---

## Consequences for PACK-16D

```text
MUST demonstrate the atomic boundary's exactly-once property under
     concurrency, crash and partition               OD-P16C-01
MUST keep the two boundary stores free of any shared key     DM-10
MUST NOT introduce a trace spanning the boundary             EV-06
MUST NOT emit capability consumption or entitlement transition
     as an event, under any name                              EV-71, EV-76
MUST NOT place a continuation capability or a capability
     reference in any event payload                           EV-01, EV-03
MUST select N, C, R, the slot partition and the safety
     reserve before opening, validated against L_max — never
     from expected, historical or plausible turnout           OD-P16C-10
MUST build both clients reproducibly, with published digests IV-07…IV-10
MUST implement the pipeline in the specified order, with no
     configuration that reorders it                          VP-00
MUST register the reason codes without merging any of them   RN-16C-*
MUST add a privacy-matrix row and an acceptance row before
     adding any field or event                       PM-12, EV-66
MUST NOT build any operation on the prohibited list           API-34
MUST generate cover leaves from a sound generator under
     PACK-16B's randomness discipline                          RB-16C-10
MUST NOT publish any individual ballot entry before closure    BE-28
MUST NOT vary a sealed_batch_commitment's serialized size
     with occupancy, including under transport compression     TC-33
MUST implement every operation with all sixteen catalogue
     fields, a privacy class and a rate-limit policy           API-49
MUST implement K and A as protocol-profile constants, never
     as feature flags or configuration                         CH-37, CH-38
MUST reserve a leaf slot atomically before durable acceptance
     on BOTH the cast and public-challenge paths               TC-70
MUST NOT transmit a local diagnostic challenge as an event,
     a metric or a log line                                    EV-70
MUST NOT build any occupancy, remaining-slot or residual
     entitlement read at any permission level                  API-34
MUST construct the privacy-preserving per-capability
     reconciliation evidence, or declare it impossible         OD-P16C-19
MUST clear accessibility acceptance per context               XA-29
```

---

## Consequences for PACK-17

```text
Independent verification operations and their governance
Board resilience, mirror operation, and the witness ecosystem
Independent execution of verifier checks 17-21 against a real record
Independent cryptographic review of the per-capability reconciliation proof
Capacity stress testing and safety-reserve sizing
Archive re-verification over time
Network-layer correlation — the residual this round could not close
Incident rehearsal for the published failure paths
```

---

## Canon assessment

`CANON CLARIFICATION REQUIRED`. **No amendment proposed.** Eight
clarifications (`CQ-P16C-01`…`08`) and three amendment candidates
(`CAM-P16C-01`…`03`) recorded. `CANON_VERSION` unchanged at `0.8.0`; the
canon files are byte-identical.

The finding: **the canon has no publication primitive for a public
ballot-bearing board**, because its only append-only public primitive —
`PublicLedgerEntry` (19a.1) — correctly prohibits a link to `VoteEnvelope`.
The board is therefore specified on its own terms, and the gap is recorded
rather than filled by analogy. **The three entry types added by the turnout
correction raise the same question and no new one**, and a commitment is not
a link: `PublicLedgerEntry → VoteEnvelope` prohibits a reference, and a
`commitment_root` is a hash over hiding commitments from which no envelope
is reachable (`CQ-P16C-07`, `CAN-P16C-05`).

**The public-challenge entitlement introduces no new public canonical
identity-bearing aggregate.** It is private anonymous capability state —
three booleans inside the continuation boundary — and must never appear in
the public election record. A canonical aggregate for it would be a defect,
not an improvement, because modelling it canonically invites publication
(`CQ-P16C-08`, `CAN-P16C-06`, `CAN-P16C-07`). **That prohibition is the one this whole
architecture exists to protect, and it is not weakened by a single line of
this pack.**

---

## FIR impact

```text
FIR entries created                    0
FIR entries removed or downgraded      0
FIR statuses changed                   0
FIR entries marked implemented         0
FIR entries specified or partially     32
FIR-ROADMAP-006                        stays `approved`, target 0.16.0
FIR-INV-002                            partially addressed and future —
                                       advanced on the ballot side,
                                       NOT closed
FIR-ASM-006, FIR-ASM-007               deferred to PACK-16C by PACK-16B;
                                       taken up, partially specified
```

---

## Dependency on `ADR-100`'s status

`ADR-100` states that PACK-16C must not start before its acceptance.
**`ADR-100` remains `proposed`.** This round was nevertheless drafted, as a
specification round, on the instruction that governs it.

```text
This is recorded rather than glossed over.

ADR-101 is therefore CONDITIONAL on ADR-100. If ADR-100's parameters,
quorum or ceremony change under review, this ADR must be re-examined
before acceptance — the casting flow, the validation pipeline and the
election record all bind to them directly.
```

---

## Status of this decision

```text
PROPOSED. NOT ACCEPTED.
SPECIFICATION AND ADR ONLY. NO CODE. NO CRYPTOGRAPHIC IMPLEMENTATION.
CONDITIONAL ON ADR-100, WHICH IS ITSELF PROPOSED.
EXTERNAL ARCHITECTURAL REVIEW REQUIRED.
EXTERNAL CRYPTOGRAPHIC REVIEW REQUIRED BEFORE ANY ACTIVATION.
INDEPENDENT VERIFICATION OF A REAL CONTEXT REQUIRED BEFORE BINDING USE.
NOT A FINAL PASS. NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.
PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.
PACK-16D MUST NOT START BEFORE ACCEPTANCE.
```
