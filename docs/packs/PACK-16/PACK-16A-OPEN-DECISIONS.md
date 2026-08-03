# PACK-16A — Open Decisions

**Round:** PACK-16A — Verifiable Voting Protocol and Ballot Model Selection. **Specification and ADR only. No code. Not implemented. Not an implementation candidate. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-099`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

Twelve open decisions. Each has a question, an owner, a closing round, and
what happens if it is not closed. **None of them may be closed by an
implementation making a choice quietly** — that is the rule PACK-15 §32
set and this round keeps.

---

## 1. Inherited from PACK-15

| ID          | Question                                                                                            | Owner       | Status after PACK-16A                                                                                             |
| ----------- | --------------------------------------------------------------------------------------------------- | ----------- | ------------------------------------------------------------------------------------------------------------------- |
| `OD-P15-05` | Whether PACK-16 replaces the spent-nonce set with a cryptographic issuance construction, and the migration | **PACK-16** | **Still open, and deliberately not closed here.** PACK-16A selects a ballot model; the issuance construction is a credential-side question that PACK-16B is better placed to answer alongside the parameter decisions. Re-owned to **PACK-16B** |
| `OD-P15-06` | Retention periods per artifact class                                                                | **PACK-09** | Still open; PACK-16A adds the ballot-domain tension as `OD-P16A-07`                                                |
| `OD-P15-08` | Whether `advisory_consultation` may extend beyond members                                           | **Governance** | Still open; mode A of the legal boundary records it                                                             |

---

## 2. Opened by PACK-16A

### `OD-P16A-01` — Revoting for future profiles

**Question.** Under what construction, if any, may a future profile permit
supersession without a persistent voting-side per-participant handle?

**Why open.** The decision for `EPD2-HOM-1` is closed — **no revoting** —
and the reasoning is in `PACK-16A-REVOTING-AND-BALLOT-LIFECYCLE.md` §2. The
general question is not closed, because a construction may exist that
discharges `SU-05`.

**Owner.** A future profile round · **Closes by.** Before any profile
reaching `superseded_if_permitted`
**If not closed.** No revoting. That is a stable, safe default.

### `OD-P16A-02` — The mixnet profile

**Question.** Should `EPD2-MIX-1` ever be activated, and under what
electorate-size floor and pattern-signature assessment?

**Why open.** Ranked ballots are unsupported without it `[E-08]`, and its
individual-ballot decryption is unsafe for EPD²'s small bodies `[E-12]`.
`MX-01`…`MX-06` fix the conditions now so they cannot be softened later.

**Owner.** A future round · **Closes by.** Before any ranked binding vote
**If not closed.** Ranked methods stay unavailable electronically; bodies
that need them use another channel.

### `OD-P16A-03` — Cryptographic parameters against German guidance

**Question.** Are the selected specification's fixed parameters — a
4096-bit integer group with a 256-bit subgroup, chosen deliberately over
elliptic curves *"in order to make construction of election verifiers as
simple as possible"* `[E-02]` — acceptable under **BSI TR-02102-1 (2026-01)**
`[E-52]`, and if not, what divergence must be declared?

**Why open.** It is a substantive cryptographic-policy question that this
round is not equipped to answer and must not assume.

**Owner.** **PACK-16B** · **Closes by.** PACK-16B specification
**If not closed.** No context may be activated (`KC-21`).

### `OD-P16A-04` — Implementation selection

**Question.** Which implementation, if any, satisfies `KC-23`–`KC-25`?

**Why open.** There is **no production-grade implementation of the selected
specification version** `[E-10a]`. This is the largest engineering risk in
the selection (`RR-01`).

**Owner.** **PACK-16D** · **Closes by.** Before any implementation candidate
**If not closed.** `FM-P16A-22` — do not proceed. Options then include
funding an implementation, contributing to an existing one, or writing a
conforming implementation against the published specification and having it
independently verified. **All three are outside this round.**

### `OD-P16A-05` — Specification stewardship

**Question.** Who is the long-term custodian of the selected
specification, and what happens if it is abandoned?

**Why open.** Stewardship appears distributed between the original
organisation and a successor initiative, and **no primary document
formally transferring it was located** `[E-10a]`.

**Owner.** Governance, with PACK-16B input · **Closes by.** PACK-16B
**If not closed.** A monitored risk (`RR-08`); abandonment is a condition
that re-opens `ADR-099` (§12 of the ballot model).

### `OD-P16A-06` — Formal proof of the composed profile

**Question.** Can a symbolic and a cryptographic proof of compliance be
produced for `EPD2-HOM-1` **as composed** — the selected construction plus
the EPD² bulletin board, the PACK-15 boundary and the no-revoting policy?

**Why open.** The Swiss ordinance requires exactly this `[E-45]` Annex 2.14,
and EPD² has neither (`RR-09`). Composition is where the field's failures
have concentrated (`F-INF-3`).

**Owner.** PACK-16C, with external cryptographic review · **Closes by.**
Before any binding activation
**If not closed.** No claim of formal verification may be made, and the
gap must be stated wherever the architecture is described.

### `OD-P16A-07` — Retention of the published record

**Question.** How long is a published election record retained, given that
universal verifiability wants permanence and ballot secrecy wants
destruction?

**Why open.** A long-retained public set of encrypted ballots is a
long-term secrecy liability against a future cryptanalytic adversary
(`T-P16A-40`, `RR-14`). The two requirements are in genuine tension and
neither can simply win.

**Owner.** **PACK-09 and PACK-17**, with PACK-16C input · **Closes by.**
Before production
**If not closed.** No context may be archived under a defined policy.
**No round may resolve it by quietly choosing one side.**

### `OD-P16A-08` — Licensing interaction

**Question.** How do the licences of any adopted component interact with
the intended `EUPL-1.2` baseline?

**Why open.** The selected specification is MIT `[E-10a]` and creates no
dependency; a rejected alternative is AGPL-3.0 `[E-10]`. `FIR-OSS-001` and
`FIR-OSS-003` own the question and **this round implements neither and
claims compliance with neither**.

**Owner.** `FIR-OSS-001`, `FIR-OSS-003` · **Closes by.** Before release
**If not closed.** No release; no licensing claim.

### `OD-P16A-09` — Scope-level channel reconciliation

**Question.** Can an in-person or paper channel supersede an electronic
context at **scope level** — for a declared sub-population — without any
per-person reconciliation?

**Why open.** In-person override is the strongest coercion control
available (`CRB` §5.1), and per-person reconciliation requires the link
PACK-15 forbids. Estonia solves it by keeping the identity binding
`[E-24]`, which is closed to EPD².

**Owner.** Governance, with PACK-16C input · **Closes by.** Before the
first context with material coercion risk
**If not closed.** The fallback operates as a **separate context or
separate scope** with its own manifest and result, combined at governance
level (`AX-43`).

### `OD-P16A-10` — Lay-comprehensible verifiability

**Question.** Can a tracker-style, lay-comprehensible verifiability
presentation be layered onto `EPD2-HOM-1` without creating a transferable
receipt?

**Why open.** The German standard is comprehension without specialist
knowledge `[E-41]`, restated in the party-law objection `[E-55]`. Selene was
designed for exactly this problem and is **coercion mitigation, not
resistance**, with a documented collision problem `[E-38]`, `[E-39]`. The
property that makes a tracker comprehensible is the property that makes it
demandable — that is the difficulty, and it is not a detail.

**Owner.** **PACK-16C** · **Closes by.** PACK-16C specification
**If not closed.** Verification remains confirmation-code presence, with
`AX-21`…`AX-27` doing the comprehension work in language rather than in
mechanism.

### `OD-P16A-11` — What *"Stand der Technik"* requires

**Question.** Does § 15 Abs. 2a PartG's *Stand der Technik* condition
`[E-49]` map to BSI TR-03169, PP-0121 and TR-02102-1, and if so, how
closely?

**Why open.** **No source states that mapping**; it is this round's
inference. It is the operative legal condition for every binding internal
vote, so guessing at it is not acceptable.

**Owner.** **LEGAL/GOVERNANCE** · **Closes by.** Before the first binding
internal vote
**If not closed.** Gate item 1 (legal basis) cannot be completed, and no
binding context is activated.

### `OD-P16A-12` — Canon repository-compatibility bound

**Question.** `docs/canonical/canon-version.json` declares
`repository_compatibility: ">=0.1.0 <0.16.0"`. A future implementation
candidate targeting `0.16.0` falls outside it. Who revises the bound, and
in which round?

**Why open.** It is a version-governance act rather than a canon amendment,
and it is the kind of thing discovered at packaging time if nobody writes
it down (`CAN` §5).

**Owner.** **PACK-16D** · **Closes by.** The implementation candidate
**If not closed.** The candidate fails version-consistency checking at
packaging, which is a late and avoidable failure.

---

## 3. Which of these block acceptance of PACK-16A

| Blocks acceptance of **this specification**?             | Entries                                              |
| -------------------------------------------------------- | ---------------------------------------------------- |
| **No**                                                   | All twelve                                           |
| Blocks the start of **PACK-16B**                         | None                                                 |
| Blocks the start of **PACK-16C**                         | `OD-P16A-03`, `OD-P16A-05`                           |
| Blocks the start of **PACK-16D**                         | `OD-P16A-04`, `OD-P16A-06`                           |
| Blocks **any activation of any context**                 | `OD-P16A-03`, `OD-P16A-04`, `OD-P16A-06`, `OD-P16A-11` |
| Blocks **release**                                       | `OD-P16A-08`                                         |
| Blocks **archiving a context**                           | `OD-P16A-07`                                         |

**None of the twelve blocks the architectural acceptance of this
specification**, and none may be closed by an implementation making a
choice quietly.

**SPECIFIED. TWELVE DECISIONS OPEN WITH NAMED OWNERS. REQUIRES EXTERNAL
REVIEW. NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**
