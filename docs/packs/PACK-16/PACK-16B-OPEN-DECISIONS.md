# PACK-16B — Open Decisions

**Round:** PACK-16B — Cryptographic Parameters, Key Ceremony and Trustee Architecture. **Specification and ADR only. No code. No cryptographic code. Not implemented. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-100`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 0. The rule this document follows

```text
A decision is CLOSED only if this round actually decided it.
A decision is REASSIGNED only with a named owner, a named closing round,
   and a stated consequence if it is not closed.
Nothing is closed by describing it at greater length.
```

---

## 1. The three this round was required to close or reassign

### `OD-P15-05` — Cryptographic issuance construction

**Question.** Does PACK-16 need to replace the current spent-nonce set with
a different cryptographic issuance construction?

**Status: CLOSED for the cryptographic boundary; the construction question
is REASSIGNED to PACK-16C with an exact obligation.**

**What this round decided.** The parameter and key architecture selected
here **imposes no requirement to change the issuance construction**, and it
constrains what any future change may do:

| ID      | Boundary — binding on any future issuance construction                                                                                                                                                                         |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `IS-01` | An issuance construction may not use the election key set, any guardian key, or any value derived from them                                                                                                                    |
| `IS-02` | An issuance construction may not place identity, a persistent voter identifier, or a reusable credential in the ballot domain                                                                                                  |
| `IS-03` | No credential ID, issuance secret or continuation capability may become a ballot ID, a nonce, or an input to any ballot-domain hash                                                                                            |
| `IS-04` | No credential-to-ballot lookup may exist, be derivable, or be constructible by combining published material                                                                                                                    |
| `IS-05` | An issuance construction operating in a different group or with different parameters is a **separate cryptographic domain**, and its parameters are registered separately (`PS-*`) — it may not silently share `EPD2-CRYPTO-1` |
| `IS-06` | Any construction offering "verifiable eligibility" that binds a credential to a ballot is **prohibited by construction**, not assessed                                                                                         |

**Why the construction question is not decided here.** Whether a blind
signature, an anonymous credential or the current spent-nonce set is right
depends on the casting and bulletin-board design, which is PACK-16C's.
Deciding it here would fix the credential side before the side that consumes
it exists.

**Owner.** **PACK-16C** · **Closes by.** PACK-16C specification
**If not closed.** The spent-nonce set stands unchanged. That is a working
position, not a gap — `IS-01`…`IS-06` bound whatever replaces it.

---

### `OD-P16A-03` — Cryptographic parameters against German guidance

**Question.** Are the fixed parameters acceptable under BSI TR-02102-1
(2026-01), and if not, what divergence must be declared?

**Status: CLOSED, with one named unverified element carried forward as
`OD-P16B-01`.**

**The decision.**

```text
Parameter profile:   EPD2-CRYPTO-1
Construction:        unmodified, as specified upstream
Modulus p:           4096 bits    vs. BSI recommended 3000 for DH in F_p   ✓
Subgroup order q:    256 bits     vs. 250 (EC recommendation), 240 (break-even), 250 (verified 2020 edition)
Hash / MAC:          SHA-256 / HMAC-SHA-256, 256-bit output
Verdict:             MEETS every BSI figure this round verified first-hand
Horizon:             recommendation cliff at end-2031 (end-2030 high assurance)
Divergence to declare: NONE on key length. Subgroup order confirmed — §3
```

**Why it is closed rather than deferred.** The question asked whether the
parameters are acceptable and what divergence must be declared. Both are
answered: they meet every verified figure, and the only divergence is a
**temporal** one — the classical-cryptography horizon — which is converted
into registry fields (`deprecation_date`, `prohibition_date`) and an
obligation, not left as an open question.

**What is explicitly not claimed.** No BSI certification, no BSI conformance
assessment, no statement that a technical guideline is a legal requirement.

**Consequence tracked.** `KC-21` — no context may be activated until
`VO-02` and `VO-03` are discharged. (`VO-01` is closed — §3.)

---

### `OD-P16A-05` — Specification stewardship

**Question.** Who is the long-term custodian of the selected specification,
and what happens if it is abandoned?

**Status: CLOSED — by deciding that EPD² does not depend on the answer.**

The honest finding is that **no primary document formally transferring
stewardship was located**, there is **no errata process**, **no
specification-level security-reporting path**, and **two versions are marked
"Recommended" simultaneously** `[F-30]`. That is not a custodian EPD² can
rely on being told by.

**The decision is therefore a stewardship model that survives abandonment:**

| Element                       | Decision                                                                                                                                                                                      | Where            |
| ----------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------- |
| **Authoritative upstream**    | The pinned document, identified by SHA-256, not by a project or a URL                                                                                                                         | `PS-*`, `CA-01`  |
| **Version pinning**           | By digest; a new digest is a new profile, never an update in place                                                                                                                            | `CA-02`…`CA-05`  |
| **Accepted errata**           | **EPD² maintains its own errata record** — `CA-27` — because upstream has none                                                                                                                | `AGIL` §6        |
| **Advisory intake**           | EPD² operates its own intake covering upstream, the literature and its own findings                                                                                                           | `CA-19`…`CA-23`  |
| **Deprecation**               | Dated, published, with a successor required before the date                                                                                                                                   | `CA-08`, `CA-14` |
| **Emergency prohibition**     | Named authority, bounded outcomes, no discretion to continue                                                                                                                                  | `PS-08`, `PS-14` |
| **Parameter-set governance**  | The Election Board approves a profile; **nobody may alter one**                                                                                                                               | `PS-*`, `CA-11`  |
| **Who may approve a profile** | The Election Board, on a Cryptographic Reviewer's assessment                                                                                                                                  | `RS-16B-15`      |
| **Who may not**               | Any administrator, operator, implementer, vendor or incident authority — categorically                                                                                                        | `CA-12`, `CA-13` |
| **If upstream is abandoned**  | The pinned document does not stop working. EPD² continues on the pinned digest, publishes that upstream is dormant, and the successor question becomes `OD-P16B-06` on its existing timetable | `AGIL` §7        |

**Why abandonment is survivable here and would not be for a library:** what
EPD² depends on is a **document**, which cannot be withdrawn from a digest.
What EPD² would lose is future review and future fixes — which `F-30` shows
it does not currently have.

**Owner.** Closed by PACK-16B. Ongoing operation: **Election Board**, per
`CA-11`…`CA-13`.

---

## 2. Contributions to the six this round was required to feed

| ID                                                    | This round's contribution                                                                                                                                                                                                                                        | Still owned by               | Status after PACK-16B             |
| ----------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------- | --------------------------------- |
| `OD-P16A-04` **Implementation selection**             | **Mandatory evaluation criteria fixed** — `IM-04`…`IM-38` are pass/fail, `IM-39`…`IM-45` weighted, performance explicitly non-decisive (`IM-46`). The browser/native split is decided (`IM-28`…`IM-32`): **no guardian secret ever exists in a browser context** | **PACK-16D**                 | **Open — with a standard**        |
| `OD-P16A-06` **Formal proof of the composed profile** | **A named deliverable, a named gate and a status** — `TV-08`, `blocked pending cryptographic review`. What does not count is enumerated. `TV-11` prevents a review of upstream alone from discharging it                                                         | PACK-16C + external          | **Open — and NOT falsely closed** |
| `OD-P16A-07` **Retention of the published record**    | Ceremony-side inputs only: transcript retention (`CT-*`), incident-evidence retention with a published destruction date (`IN-40`), destruction attestations (`GL-17`, `BR-06`). **No retention period is chosen here**                                           | PACK-09, PACK-17             | Open                              |
| `OD-P16A-08` **Licensing interaction**                | One fact: the pinned artefact is a **specification document**, and this round creates **no code dependency of any licence**. The question is unchanged and untouched                                                                                             | `FIR-OSS-001`, `FIR-OSS-003` | Open                              |
| `OD-P16A-11` **What _Stand der Technik_ requires**    | Evidence toward it: the profile meets every verified BSI figure, uses AIS 20/31 v3.0 classes, and follows the SP 800-90 series. **Whether that satisfies § 15 Abs. 2a PartG is a legal question this round cannot answer and does not**                          | **LEGAL/GOVERNANCE**         | Open                              |
| `OD-P16A-12` **Canon repository-compatibility bound** | One input: PACK-16B changes no version and stays inside `>=0.1.0 <0.16.0`. The bound question arrives with the implementation candidate, unchanged                                                                                                               | PACK-16D                     | Open                              |

---

## 3. Opened by PACK-16B

### `OD-P16B-01` — The finite-field subgroup-order minimum

**Question.** What minimum applies to the order of the subgroup in
finite-field discrete-logarithm systems, and does `|q| = 256` meet it?

**Status: CLOSED BY PRIMARY-SOURCE EVIDENCE — read first-hand.**

```text
BSI TR-02102-1, Version 2026-01, 23 January 2026

  §2.3.3 DLIES Encryption Scheme, page 34, "Key Length":
    "The length of the prime number p should be at least 3000 bits.
     The length of the prime q should be at least 250 bits in both cases."

  §2.3.5 Diffie-Hellman Key Agreement, page 36, "System Parameters", step 2:
    "Choose an element g in F*p with ord(g) prime and q := ord(g) >= 2^250."

BSI minimum:          subgroup order at least 250 bits
EPD² value:           q = 2^256 − 189  —  256 bits
Comparison:           256 >= 250       SATISFIED, 6 bits of margin
Also satisfied:       q >= 2^250 · ord(g) prime · |p| = 4096 >= 3000
```

> The selected 256-bit subgroup order satisfies the reviewed BSI
> TR-02102-1 Version 2026-01 minimum for this specific parameter dimension.

**Limited to the subgroup-order dimension.** It establishes none of:
complete BSI conformity of `EPD2-CRYPTO-1`; BSI certification; approval for
political-election use; implementation security; side-channel resistance;
protocol-composition security; legal activation.

#### How the document was obtained and read

The official PDF was **supplied locally by the project's reviewer and read
directly** — 92 pages, title page _"Version: 2026-01"_, _"As of: January 23,
2026"_, SHA-256
`f601cdf25c000b431573a307a3c125f3c51d301897089e7e63dde0449367a62a`. Printed
folios match PDF page numbers. `[F-36]` carries the full entry.

**This decision has a history worth keeping.** It was closed once on
substitute sources and that closure was withdrawn; it was then closed on a
reviewer's attestation, labelled as such; it is now closed on the named
document, read. Each step is recorded rather than overwritten.

#### A figure corrected on reading

The attested value carried into the previous candidate was **240**. The
document shows 240 is a **different figure**: Table 1.1 (p. 18) uses it as
the ECDSA/ECIES key length at which a 120-bit level _"is just achieved"_,
and p. 18 separately gives 240 bits as the general minimum **hash digest**
length. **The finite-field subgroup-order minimum is 250**, and `|q| = 256`
satisfies it.

#### One divergence recorded, not glossed

**Remark 2.12, p. 34** recommends, for published parameters, _"the MODP
groups from [78] or the ffdhe groups from [60]"_, where _"q = (p − 1)/2 and
g = 2"_. `EPD2-CRYPTO-1` uses published parameters that are neither, with a
256-bit prime `q`. The `log₂(p) ≥ 3000` condition is met, and §2.3.5 step 2
explicitly permits any `g` of prime order `≥ 2²⁵⁰`. It is a
**recommendation-level divergence, not a failed requirement**, and it is
carried as **`VO-08`** and `RB-09`. It does not affect this decision's
subject.

**`VO-08` is owned by the PACK-16B external cryptographic review**, with
independent confirmation in **PACK-17** and any implementation consequences
in **PACK-16D**. **It is not owned by PACK-16C**: whether retaining the
ElectionGuard 2.1 published parameter family is normatively acceptable is a
cryptographic and standards judgement, and PACK-16C — casting, receipts, the
verification client and the bulletin board — cannot resolve it. PACK-16C
inherits it as a constraint and may not alter or claim approval of the
parameter family. **`VO-08` blocks production implementation acceptance,
production activation, legal activation, complete BSI-conformity claims and
final cryptographic assurance**, while remaining non-blocking for the
completion of this specification round and for drafting PACK-16C.

#### Validation obligations

| ID               | Status                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `VO-01`          | **SATISFIED** — document read, minimum recorded, comparison made                                                                                                                                                                                                                                                                                                                                                                                                                      |
| `VO-06`          | **SATISFIED BY PRIMARY-SOURCE REVIEW**                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| `VO-07`          | **SATISFIED** — exact chapter, subsections, pages and verbatim wording recorded                                                                                                                                                                                                                                                                                                                                                                                                       |
| `VO-08`          | **NEW and OPEN** — assess the normative acceptability of retaining the ElectionGuard 2.1 published parameter family despite Remark 2.12. Owner: **PACK-16B external cryptographic review**; independent assurance **PACK-17**; consequences **PACK-16D**. **Not PACK-16C.** Non-blocking for this round and for PACK-16C drafting; **blocks production implementation acceptance, production and legal activation, complete BSI-conformity claims and final cryptographic assurance** |
| Other dimensions | `VO-02` (AIS 20/31 classes) and `VO-03` (hash and MAC tables) remain **OPEN and block activation**                                                                                                                                                                                                                                                                                                                                                                                    |

### `OD-P16B-02` — Whether an EPD²-written implementation is permitted

**Question.** May EPD² write its own conforming implementation, given that
**no production-grade implementation of the pinned version exists**
(`OD-P16A-04`, `RR-01`)?

**Why open.** It is the question `OD-P16A-04` will run into immediately, and
it is a governance question as much as a technical one: an in-house
implementation removes a dependency and removes an independent party at the
same time. `TV-07`'s differential-testing requirement partly compensates and
does not settle it.

**Owner.** **GOVERNANCE, with PACK-16D input** · **Closes by.** Before
implementation begins
**If not closed.** PACK-16D cannot start its implementation track. Specifying
and reviewing may continue.

### `OD-P16B-03` — The Cryptographic Reviewer's standing

**Question.** Is `R-18` a standing appointment or engaged per context, and
who engages them?

**Why open.** A standing reviewer accumulates the context needed to review
well and accumulates a relationship that narrows independence. A per-context
reviewer is more independent and reviews from a cold start each time.
Neither is obviously right, and `RS-16B-15` holds regardless of the answer.

**Owner.** **GOVERNANCE** · **Closes by.** Before `TV-08` is commissioned
**If not closed.** `TV-08` is commissioned per context, which is the
conservative default and the more expensive one.

### `OD-P16B-04` — Publicly checkable share correctness

**Question.** Is there a construction, compatible with the pinned
specification, that makes `share_inconsistent` **publicly adjudicable
without disclosing the share**?

**Why open.** It is the one complaint ground the current design cannot
resolve arithmetically: sender and recipient can make contradictory claims,
and the resolution requires opening one share under `CD-15`. A construction
with a publicly verifiable encryption proof would remove the disclosure
entirely. **Inventing one here would be precisely the kind of unreviewed
cryptographic innovation this round refuses to make.**

**Owner.** **PACK-16C, with external cryptographic input** · **Closes by.**
Open-ended; reassessed each round
**If not closed.** `CD-15`…`CD-19` stand: a single share is opened, by Board
order with Auditor concurrence, from a key set that is discarded immediately
afterwards.

### `OD-P16B-05` — Remote ceremony

**Question.** Under what evidence may a **fully remote** key ceremony be
permitted?

**Why open.** The current answer is **no**, and the four conditions that
would change it are written down (`RCA` §5): a peer-reviewed analysis of the
key ceremony addressing remote participation; a remotely verifiable device
attestation EPD² does not itself operate; an observation model that survives
an adversary controlling the guardian's location; and at least two completed
controlled-hybrid ceremonies with published transcripts and Auditor
verdicts.

**Owner.** **PACK-17, with governance** · **Closes by.** Not before two
controlled-hybrid ceremonies have completed
**If not closed.** Fully remote stays prohibited. Controlled hybrid is
permitted and is the expected form.

### `OD-P16B-06` — The post-quantum successor profile

**Question.** What replaces `EPD2-CRYPTO-1` before the classical-cryptography
recommendation lapses at the end of 2031 (end of 2030 for very high
protection) `[F-25]`?

**Why open.** It is the **highest-rated residual risk of this round**
(`RB-02`). A successor is not a parameter change: the selected construction
is a discrete-log construction, so a quantum-safe successor is a **different
protocol**, with its own ADR, its own proofs and its own verifier. Current
guidance recommends hybrid schemes and states that quantum-safe mechanisms
are _"generally not yet trusted to the same extent as the established
classical mechanisms"_ `[F-25]`.

**Owner.** **A future round — not started here** (`CA-10`) · **Closes by.**
A successor profile must be `active` **before** 2030-12-31 (`CA-08`)
**If not closed.** No new context may be opened after the deprecation date.
Running contexts complete; the system stops taking new binding votes rather
than continuing on a lapsed recommendation.

---

## 4. Which of these block what

| Open decision | Blocks specification? | Blocks implementation? | Blocks **activation**?                    |
| ------------- | --------------------- | ---------------------- | ----------------------------------------- |
| `OD-P16B-01`  | No                    | No                     | **CLOSED** — read first-hand; `256 ≥ 250` |
| `OD-P16B-02`  | No                    | **YES**                | —                                         |
| `OD-P16B-03`  | No                    | No                     | Indirectly, via `TV-08`                   |
| `OD-P16B-04`  | No                    | No                     | No                                        |
| `OD-P16B-05`  | No                    | No                     | No — the answer is already "no"           |
| `OD-P16B-06`  | No                    | No                     | **After 2030-12-31**                      |
| `OD-P16A-04`  | No                    | **YES**                | **YES**                                   |
| `OD-P16A-06`  | No                    | No                     | **YES** (`TV-08`)                         |
| `OD-P16A-11`  | No                    | No                     | **YES** for binding votes                 |

**Three independent activation blocks remain open** — `OD-P16A-04`,
`OD-P16A-06` and `OD-P16A-11` — plus the dated `OD-P16B-06` and the
still-open validation obligations `VO-02`…`VO-05`. `OD-P16B-01` is now
closed on the **named** document, **read first-hand** from the official PDF
— not on substitute sources, which is what an earlier round tried and what
was withdrawn.

---

## 5. Register of dispositions

| ID                                | Before PACK-16B            | After PACK-16B                                                                                                                                                                                                                                                                                                              |
| --------------------------------- | -------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `OD-P15-05`                       | open, re-owned to PACK-16B | **cryptographic boundary CLOSED** (`IS-01`…`IS-06`); construction question **reassigned to PACK-16C**                                                                                                                                                                                                                       |
| `OD-P16A-03`                      | open, owned by PACK-16B    | **CLOSED for the dimensions assessed** — key lengths, group choice, divergence declaration, and the current-edition subgroup-order dimension via `OD-P16B-01`. **One divergence is now declared** (Remark 2.12, `VO-08`). **General BSI compatibility of the whole profile is NOT closed**, and `VO-02`/`VO-03` remain open |
| `OD-P16A-05`                      | open, owned by governance  | **CLOSED**; stewardship model fixed                                                                                                                                                                                                                                                                                         |
| `OD-P16A-04`                      | open                       | open — **criteria fixed**                                                                                                                                                                                                                                                                                                   |
| `OD-P16A-06`                      | open                       | open — **deliverable and gate fixed**, status `blocked pending cryptographic review`                                                                                                                                                                                                                                        |
| `OD-P16A-07`                      | open                       | open — ceremony-side inputs contributed                                                                                                                                                                                                                                                                                     |
| `OD-P16A-08`                      | open                       | open — unchanged; no dependency created                                                                                                                                                                                                                                                                                     |
| `OD-P16A-11`                      | open                       | open — evidence contributed, legal question untouched                                                                                                                                                                                                                                                                       |
| `OD-P16A-12`                      | open                       | open — unchanged; no version changed                                                                                                                                                                                                                                                                                        |
| `OD-P16A-01`, `-02`, `-09`, `-10` | open                       | **untouched by this round** — not in scope                                                                                                                                                                                                                                                                                  |
| `OD-P15-06`, `OD-P15-08`          | open                       | **untouched**                                                                                                                                                                                                                                                                                                               |
| `OD-P16B-01`                      | opened by PACK-16B         | **CLOSED BY PRIMARY-SOURCE EVIDENCE, read first-hand** — subgroup-order dimension; `256 ≥ 250` `[F-36]`, §2.3.3 p. 34 and §2.3.5 p. 36                                                                                                                                                                                      |
| `OD-P16B-02`…`OD-P16B-06`         | —                          | **opened here**, and unchanged by the correction                                                                                                                                                                                                                                                                            |

```text
Closed by this round:        4   (OD-P15-05 boundary, OD-P16A-03 in part,
                                  OD-P16A-05, OD-P16B-01)
Reassigned with obligation:  1   (OD-P15-05 construction → PACK-16C)
Contributed to:              6
Opened:                      6   (OD-P16B-01 … OD-P16B-06)
Still open of those opened:  5
Closures withdrawn and later
   re-established on the
   named source:             1   (OD-P16B-01)
Falsely closed:              0
```

**Nothing else was closed by the correction round.** Independent verifier
testing, external cryptographic review, formal-proof obligations,
implementation-library evaluation and legal assessment all remain open, and
no certification or full-interoperability claim is made anywhere.

**SPECIFIED. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY. NOT LEGALLY
ACTIVATED.**
