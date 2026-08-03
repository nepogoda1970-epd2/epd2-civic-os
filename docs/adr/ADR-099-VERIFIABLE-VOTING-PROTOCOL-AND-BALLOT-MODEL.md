# ADR-099 — The verifiable voting protocol is a homomorphic, threshold-decrypted, challengeable ballot model, adopted as a bounded EPD² profile

**Status:** proposed
**Round:** PACK-16A — Verifiable Voting Protocol and Ballot Model Selection (specification and ADR only)
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`

**NO CODE. NOT IMPLEMENTED. NOT A CANDIDATE FOR IMPLEMENTATION. NOT A PASS.
NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION
PROHIBITED BY DEFAULT.**

Evidence references `[E-nn]` resolve in
`docs/packs/PACK-16/PACK-16A-PROTOCOL-EVIDENCE-MATRIX.md`.

---

## Context

PACK-15 closed the identity side of the voting problem and stopped one step
short of the ballot. Its closing statement to PACK-16 was precise: the
voting side receives **a minimal single-use continuation capability** and
nothing else, and PACK-16 inherits an obligation PACK-15 could not
discharge — to prove that `credential → redemption → ballot` cannot be
reassembled.

```text
FIR-INV-002  =  (identity → credential)  ∧  (credential → ballot)
                 ─────── PACK-15 ───────     ─────── PACK-16 ───────
```

ADR-090 also fixed the standard of proof: it is **not** sufficient to show
that no code pairs two records; the architecture must show that the records
**cannot be paired**.

PACK-16 is too large for one round. Choosing a protocol, fixing its
parameters, running a ceremony, specifying casting and verification, and
implementing all of it are four different decisions with four different
failure modes. Bundling them produces the outcome this project has
consistently refused: a security architecture settled by whoever was
writing code that week. PACK-16 is therefore sequenced 16A → 16B → 16C →
16D, and **PACK-16B must not begin before PACK-16A is architecturally
accepted**.

This ADR records the first decision: which protocol family, and which
ballot model.

## Baseline constraints

Inherited and not re-openable by this decision:

```text
NO IDENTITY IN BALLOT · NO CREDENTIAL ID AS BALLOT ID
NO CONTINUATION REFERENCE AS BALLOT ID · NO PERSON-TO-BALLOT LINK
NO IDENTITY RECOVERY BY CORRELATION · NO REUSABLE VOTING SESSION
NO INTERMEDIATE TALLY · NO PARTIAL OUTCOME DISCLOSURE
NO TURNOUT DISCLOSURE BEFORE CLOSURE · NO SINGLE-ADMIN DECRYPTION
NO SILENT BALLOT REPLACEMENT · NO SILENT BALLOT DELETION
NO UNEXPLAINED BALLOT EXCLUSION · NO RECEIPT THAT REVEALS CHOICE
NO THIRD-PARTY ANALYTICS · NO FINGERPRINTING
NO BALLOT CONTENT IN DISPUTE RECORDS
NO INDIVIDUAL BALLOT CORRECTION THROUGH IDENTITY LINKAGE
APPEND-ONLY VERIFIABLE ELECTION EVIDENCE
```

Plus the infrastructure boundary of ADR-090 §7 and the WS-03 isolation of
ADR-096, both unchanged, and PACK-15 §19's timing-correlation controls with
their governed defaults and hard lower bounds.

## Decision drivers

1. **Structural compatibility with the inherited boundary**, expressed as
   five filters that a candidate must pass regardless of its other merits:
   no per-participant persistent voting-side identifier; no identity bound
   to a ballot at any moment; no party holding both-side references; no
   reusable session or client persistence; and no individual-ballot
   decryption where the electorate is small enough for a preference pattern
   to identify a voter.
2. **Published, citable properties** — protocol properties distinguishable
   from implementation properties, with named assumptions.
3. **Small electorates.** EPD²'s bodies are frequently smaller than fifty
   and sometimes smaller than ten. This changes which properties matter.
4. **The German legal frame**, which permits binding internal electronic
   votes and does not permit statutory candidate nomination or public
   elections.
5. **Honest claim discipline** — `FIR-INV-015`.

## Protocol candidates

Nine families were assessed against primary sources.

| Family                   | Verdict                                    |
| ------------------------ | ------------------------------------------ |
| **ElectionGuard 2.1.0**  | **SUITABLE WITH A FORMAL EPD² PROFILE**    |
| Belenios 3.0/3.1         | SUITABLE ONLY AS REFERENCE                 |
| Helios v3                | NOT SUITABLE                               |
| Estonian IVXV 1.8.0      | NOT SUITABLE                               |
| Verificatum VMN 3.1.0    | SUITABLE ONLY AS REFERENCE                 |
| JCJ / Civitas            | NOT SUITABLE                               |
| Selene                   | REQUIRES FURTHER RESEARCH                  |
| BeleniosRF               | REQUIRES FURTHER RESEARCH                  |
| VoteAgain                | NOT SUITABLE                               |

`docs/packs/PACK-16/PACK-16A-PROTOCOL-COMPARISON.md` is the assessment.

## Evidence standard

**All PACK-16A Evidence IDs are canonically defined in
`docs/packs/PACK-16/PACK-16A-PROTOCOL-EVIDENCE-MATRIX.md`.** There is one
registry and no second one; `PACK-16A-GERMAN-LEGAL-BOUNDARY.md` §9 carries
a pointer table that defines nothing.

```text
allocated Evidence IDs .......... 60
substantive definitions ......... 59
reserved IDs ....................  1   (E-48)
highest Evidence ID ............. E-56
unique references resolved ...... 58
unresolved references ...........  0
conflicting definitions .........  0
```

Every substantive claim carries the source title, issuing institution,
version and date, source type, URL or stable reference, relevant section,
the property supported, the scope of that support, its limitations, the
documents citing it, and a classification as **protocol property**,
**implementation property**, **legal** or **inference**. Items that could
not be verified are marked **UNVERIFIED** and support no conclusion.
Marketing material is not evidence. Where sources contradict each other the
contradiction is shown rather than resolved by assertion.

## Selected protocol family

**Homomorphic encrypted ballots with exponential ElGamal, distributed
threshold key generation and decryption, non-interactive zero-knowledge
well-formedness proofs, and Benaloh cast-or-challenge, in the lineage
specified by the ElectionGuard Design Specification 2.1.0** `[E-01]`…`[E-05]`.

**A specification is selected, not a library.** There is currently no
production-grade implementation of that specification version `[E-10a]`;
selecting a codebase from here would select the least mature option
available. The library question is `OD-P16A-04`.

**The reason, stated once.** The selected family's most-cited limitation is
that it performs no eligibility and no authentication and requires these to
be established outside it, asking only that interested parties be able to
confirm that ballots cast do not exceed voters entitled `[E-06]`. For every
other integrator that is a gap to be filled. For EPD² it is a description
of the interface PACK-15 already built. The boundary and the protocol were
designed independently and meet without either being bent.

## Selected EPD² profile

```text
EPD2-HOM-1   cardinal ballots, homomorphic tally   — SELECTED FOR REVIEW
EPD2-MIX-1   ordinal ballots, mixnet tally         — DEFINED, NOT SELECTED,
                                                     PROHIBITED PENDING RESEARCH
```

A context declares exactly one profile, cannot change it after
`configured`, cannot mix contests across profiles, and an unactivated
profile is refused rather than defaulted. **There is no hybrid profile and
none may be created without a new ADR.**

## Selected ballot model

Encrypted ballot with per-contest selections, per-selection range proofs, a
contest-sum proof, **a proof of knowledge of the plaintext** (`BM-14`), a
confirmation code derived only from the ballot's own encryptions, and a
client-generated ballot identifier unrelated to anything received from the
identity side. `docs/packs/PACK-16/PACK-16A-BALLOT-MODEL-SPECIFICATION.md`
is the profile.

## Supported election types

Yes/no referendum · single-choice · multiple-choice n-of-m · approval ·
multi-seat by approval or n-of-m · candidate nomination **as internal,
non-statutory selection only** · constitutional amendment as a yes/no ·
party-policy consultation · binding member resolution.

## Unsupported election types

Ranked choice · STV · Condorcet · Majority Judgment · any tally depending
on the joint pattern within a ballot · free-form write-ins (**prohibited
pending research**) · **every public political election (prohibited by
default)**.

## Identity and credential compatibility

The construction has no notion of a voter, so it requires no
per-participant identifier, no signature over the ballot and no credential
list. The continuation capability is consumed on the credential side and
produces a casting authorisation that is never stored beside a ballot
(`CC-01`…`CC-10`). The only figure the two sides share is an aggregate
count, published after closure.

The three rejected deployed systems each fail this differently and
instructively: Helios publishes voter names beside ciphertexts `[E-21]`;
Belenios's server holds a list pairing public credentials with voter
identity `[E-13]`; Estonia stores signed ciphertexts under `votes/<voter id>/`
and severs the link in a **trusted offline procedure** `[E-24]`.

## Verifiability model

| Property                 | Mechanism                                              | Claim status                                        |
| ------------------------ | ------------------------------------------------------ | ----------------------------------------------------- |
| Cast as intended         | Benaloh cast-or-challenge, required, non-disablable    | **specified**; probabilistic; depends on take-up    |
| Recorded as cast         | Confirmation code + board presence check + checkpoint  | **specified**; take-up 9.9 % at best `[E-29]`       |
| Tallied as recorded      | Published aggregate, shares and proofs                 | **specified**; needs an independent verifier        |
| Universal verifiability  | Full record published at closure; mirrors              | **specified**; the board is unbuilt                 |
| Software independence    | Verify without trusting any EPD² component             | **objective specified, not demonstrated**           |
| Eligibility verifiability| Aggregate count check only                             | **weaker than CoE Standard 18, and said so**        |

## Receipt model

A confirmation code derived entirely from the ballot's own encryptions. It
locates the ballot on the board and reveals nothing about the choice
(`BM-03`, `[E-05]`, CoE Standard 23 `[E-56]`). **It does prove
participation**, which is itself coercive information in some settings, and
that residual cannot be removed without removing verifiability
(`T-P16A-25`).

## Coercion-resistance boundary

**Coercion resistance is not claimed and is not achievable for remote
voting.** It is a conditional property depending on the voter having an
unobserved interval: *"if the coercer can monitor the voter throughout the
vote casting period, then resistance is futile"* `[E-46]`. Every
coercion-resistant scheme relocates that assumption rather than removing it.

Two threats are recorded as **unmitigated**: coercion during casting
(`T-P16A-26`) and forced abstention (`T-P16A-30`). The only control that
addresses them is a **different channel**, which the governance gate makes
an explicit permitted outcome.

`docs/packs/PACK-16/PACK-16A-COERCION-AND-RECEIPT-BOUNDARY.md` carries the
permitted- and prohibited-claims registries, and they are enforceable.

## Revoting decision

```text
NO REVOTING in EPD2-HOM-1.
```

Explicit, not deferred. Supersession requires the system to know that one
ballot replaces another — a **persistent voting-side per-participant
handle**, which PACK-15 forbids. Belenios supplies it with the public
credential `[E-13]`; Estonia with the voter id `[E-24]`. A non-identity
handle reintroduces a reusable session and a demandable bearer value.

The published evidence also weighs against it: a malicious server can
undetectably roll back a revoted ballot `[E-15]`; revoting is the vector
that defeats individual verifiability in the largest deployment `[E-28a]`;
the most credible cryptographic revoting scheme was broken with no fix
proposed `[E-44]`; and even JCJ's cleansing leaks whether a voter disobeyed
`[E-37]`.

**What this costs is stated rather than minimised:** a voter coerced during
her single casting act has no in-system remedy, and a mistake cannot be
corrected. `OD-P16A-01` carries the general question.

## Ballot lifecycle

Fourteen specification-level states from `prepared` to `archived`, each
transition naming actor, input, proof, public evidence, audit evidence,
failure code, reversibility and privacy constraint. `spoiled` and `tallied`
are absorbing. `superseded_if_permitted` is defined and **unreachable** in
this profile. Silent replacement, deletion, exclusion, administrator-only
invisible correction, post-hoc identity lookup and individual correction
through dispute handling are prohibited. Exclusion is possible only through
`excluded_with_public_reason`, on one of five closed grounds, with Election
Board decision, Independent Auditor concurrence, a privacy-safe reason
code, publication and independent verifiability.

## Bulletin-board model

The selected family **does not provide a board** `[E-07]`, and neither does
any assessed alternative in a form EPD² could adopt `[E-15]`, `[E-32]`. The
board is therefore a **distinct trust boundary** with 37 requirements:
append-only, canonical election-scoped namespace, canonical ordering by
board sequence, signed chained checkpoints, **at least two mirrors under
distinct organisational control**, full-content download, batched and
delayed publication, and a closed prohibited-content list refusing
publication rather than redacting afterwards.

Publication model: **layered public and audit views.** Ballot entries are
withheld before closure because a live public entry list is a live turnout
counter, which `ADR-094` prohibits. Individual verification before closure
is preserved through a presence query returning a checkpoint the voter can
later check against the published chain.

## Threshold-trust implications

Threshold key generation with k of n guardians, quorum required for any
decryption, decryption bound to `voting_closed`, share proofs verified,
compensated shares for absent guardians within the quorum. Principles fixed
now: k ≥ 3; **no single organisation may supply k guardians**; n − k ≥ 2;
k and n fixed in the manifest before `issuance_open`; **k and n are not
reduced for a small electorate**; trustee identity and organisation
published.

**No escrow, no master key, no recovery outside a quorum ceremony.** If a
quorum is lost, the result is unobtainable and the context is annulled and
re-run. **An unrecoverable election is preferable to a recoverable secret**
— PACK-15's trade at §13.2, kept.

## Privacy and metadata consequences

Twelve data flows specified. The dominant residual is
**redemption-to-casting timing correlation** (`T-P16A-04`, extending
PACK-15 `T-P15-13`), addressed by coarsened timestamps, the inherited
minting delay, submission batching and randomized board publication —
and **reduced and bounded, not eliminated**. Network and infrastructure
correlation remain outside the application layer and are owned by PACK-17.
**Timing correlation is not declared solved by the existence of separate
origins.**

## German legal boundary

Nine modes assessed. Binding electronic voting is permitted for internal
party resolutions and internal board elections under § 15 Abs. 2a PartG
`[E-49]`. It is **not** permitted for statutory candidate nomination, where
the operative guidance requires simultaneous physical presence and written
secret paper ballots `[E-50]`, `[E-51]`. Public political elections have no
legal basis, no BSI framework — the entire current German technical
framework is scoped to **non-political** elections by construction `[E-54]`
— and face a constitutional standard requiring citizens to scrutinise the
key steps *"zuverlässig und ohne besondere Sachkenntnis"* `[E-41]`, on which
the Court has never ruled for cryptographic verifiability.

```text
PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT
```

A ten-item governance gate governs every activation, and **refusing to hold
a vote electronically is an explicit permitted outcome of that gate**.

## Accessibility consequences

Accessibility is treated as protocol-level because three properties of the
selected model make it so: challenge is the only cast-as-intended
mechanism, verification is voluntary and lightly used, and the German
standard is lay comprehensibility rather than availability. Forty-three
requirements, with every accessibility-versus-security conflict named
rather than silently downgraded. Notably: **a second verification device is
recommended and not required**, because requiring one excludes voters for a
protection the published evidence shows to be partial `[E-28a]`.

## Operational consequences

Debugging remains hard, as ADR-090 accepted, and is now harder: an engineer
cannot follow a participation from authorisation to ballot, by design.
Incident response is constrained further — no break-glass path decrypts,
assembles a quorum, writes to the board or spans the boundary. A context
requires at least three trustees from independent organisations, at least
two independently operated mirrors, and an independent verifier. **Small
organisations may be unable to meet those requirements, and the correct
answer there is not to hold the vote electronically** (`RS-07`).

## Failure and abort model

Twenty-five conditions with outcomes from `continue` to `re-run`, deciders,
auditor concurrence, preserved evidence, participant communication and
publication. A re-run never reuses a key, a parameter set, an authorisation
or a board. **Uncertifiable results** are defined, published as such, and
cannot be withdrawn by later assertion — aligning with canon 15.6's rule
that the passing of `challenge_deadline_at` is necessary but not sufficient
for finality.

## Rejected alternatives

**Belenios as base.** Rejected: the credential authority's list pairs voter
identity with a public credential `[E-13]` — the row PACK-15 §3 forbids —
and the signature that list supports is what prevents server-side stuffing,
so the mechanism cannot be subtracted without subtracting the property. Its
mixnet mode publishes decrypted individual ballots `[E-12]`. Its own FAQ
states that *"Belenios fails to achieve coercion resistance"* `[E-14]`.
Retained as the model for honest limitation documentation.

**Helios as base.** Rejected: weak Fiat–Shamir remains in shipping code
fourteen years after publication of the attack and after a corrected
specification `[E-19]`, `[E-22]`; ballot weeding was never implemented
`[E-19]`; trustees are n-of-n `[E-20]`; voter names are published beside
ciphertexts `[E-21]`; and the authors do not endorse it for high-stakes use
`[E-17]`.

**Estonian IVXV as base.** Rejected: the identity↔ciphertext binding is
stored for the whole voting period and severed by a **trusted offline
procedure** `[E-24]`. There is no configuration of it satisfying PACK-15's
structural rule, because the rule says the pair never exists and the design
requires that it exist. Also: no proof of knowledge of the plaintext
`[E-27]`, and revoting defeats individual verifiability `[E-28a]`.

**A mixnet profile now.** Rejected for this round: individual-ballot
decryption is a preference-pattern channel that `disclosure_min_cell`
cannot close in small bodies, and mixnet risk in practice is
parameter-generation and integration risk `[E-33]`.

**Coercion-resistant schemes.** Rejected: JCJ/Civitas require an untappable
registration channel, are quadratic, ask ordinary voters to lie
convincingly and indefinitely, have never been deployed, and the property
itself is contested `[E-34]`, `[E-35]`, `[E-37]`. VoteAgain was broken with
no fix `[E-44]`. Selene and BeleniosRF are recorded as **REQUIRES FURTHER
RESEARCH**.

**Inventing a protocol.** Rejected: EPD² has no cryptographic research
capacity, and a bespoke construction carries the one risk process cannot
mitigate.

## Residual risks

`RR-01` no production-grade implementation of the selected specification
version · `RR-02` ranked ballots unsupported · `RR-03` cast-as-intended is
probabilistic · `RR-04` verification take-up is empirically low ·
`RR-05` device compromise is out of scope for every candidate ·
`RR-06` timing correlation reduced, not eliminated · `RR-07` small
electorates weaken every unlinkability property · `RR-08` specification
stewardship undocumented · `RR-09` **no symbolic or cryptographic proof of
the composed profile** · `RR-10` the board is entirely EPD²'s to build ·
`RR-11` pre-closure public scrutiny is given up · `RR-12` mirror
independence is organisational · `RR-13` detection depends on someone
checking · `RR-14` a long-retained encrypted record is a long-term secrecy
liability · `RR-15` board availability is a single point of failure for
casting.

## Open decisions

Twelve, each with an owner and a closing round:
`OD-P16A-01` revoting for future profiles · `OD-P16A-02` the mixnet profile
· `OD-P16A-03` parameters against BSI TR-02102-1 · `OD-P16A-04`
implementation selection · `OD-P16A-05` specification stewardship ·
`OD-P16A-06` formal proof of the composed profile · `OD-P16A-07` retention
of the published record · `OD-P16A-08` licensing interaction ·
`OD-P16A-09` scope-level channel reconciliation · `OD-P16A-10`
lay-comprehensible verifiability · `OD-P16A-11` what *Stand der Technik*
requires · `OD-P16A-12` the canon repository-compatibility bound.

**None blocks acceptance of this specification. None may be closed by an
implementation making a choice quietly.**

## Consequences for PACK-16B

Choose the group, key size and hash, and justify them against BSI
TR-02102-1 (2026-01) including any divergence from the specification's
fixed parameters (`OD-P16A-03`). Choose k and n within `TP-01`…`TP-07`.
Design the ceremony to `KC-01`…`KC-20`. Publish parameter provenance that
an outside party can reproduce. Build **no** escrow, **no** recovery
guardian and **no** administrative decryption path. Re-own `OD-P15-05`.

## Consequences for PACK-16C

Specify the bulletin board to `BB-01`…`BB-37`, the casting protocol, the
verification client on a third origin, the receipt surface, the mirror
protocol, and the batch and delay parameters of `BB-11`. Answer
`OD-P16A-10`. Pursue `OD-P16A-06`. Register the reason codes. Produce the
election-record format and the verifier prose of `BB-34`.

## Consequences for PACK-16D

Select an implementation satisfying `KC-23`–`KC-25`, or **do not proceed**
(`FM-P16A-22`). Verify strong Fiat–Shamir by test (`AC-P16A-039`). Obtain
an independent verifier (`BM-28`). Implement the prohibited-phrase scan
enforcing the claims registries. Close `OD-P16A-12` before packaging.

## Consequences for PACK-17

Network and infrastructure metadata correlation; backup topology and
restore separation; board and mirror availability; incident readiness;
independent-verification operations; and `OD-P16A-07` jointly with PACK-09.

## Canon assessment

```text
CANON CLARIFICATION REQUIRED — CQ-01 … CQ-06
CANON AMENDMENT NOT REQUIRED AND NOT PROPOSED
CANON AMENDMENT CANDIDATES RECORDED — CA-01, CA-02, CA-03
CANON_VERSION REMAINS 0.8.0
```

Notably, canon 19a.1 forbids `PublicLedgerEntry → VoteEnvelope`. The
prohibition is correct and stands, and its consequence is that the bulletin
board cannot be modelled as `PublicLedgerEntry` — which is the amendment
candidate most likely to be needed at PACK-16C, and is recorded rather than
proposed.

## FIR impact

`FIR-ROADMAP-006` — **status unchanged at `approved`**, treatment *selected
for architectural review*; not implemented, target version `0.16.0`
unchanged. `FIR-INV-002` — **partially addressed; the architecture of the
second half is specified and is not proven, and this round does not close
the invariant.** Twenty entries specified, eight deferred with named
owners, one blocked pending legal assessment. **No entry marked
`implemented`. No entry created, removed, renamed or downgraded.**
`FIR-UX-011` and `FIR-OSS-001` … `FIR-OSS-006` preserved unchanged.

---

**This ADR is `proposed` and must not be recorded as `accepted`.** Separate
architectural acceptance follows an audit of the candidate archive.
PACK-16B must not start before that acceptance.

**SELECTED FOR ARCHITECTURAL REVIEW. REQUIRES EXTERNAL REVIEW. REQUIRES
LEGAL ASSESSMENT. NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.
PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**
