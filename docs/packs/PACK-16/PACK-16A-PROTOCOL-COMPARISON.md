# PACK-16A — Protocol Comparison

**Round:** PACK-16A — Verifiable Voting Protocol and Ballot Model Selection. **Specification and ADR only. No code. Not implemented. Not an implementation candidate. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**Baseline:** `EPD2_PACK-15_VOTING_TRUST_BOUNDARY_ELIGIBILITY_CREDENTIAL_SEPARATION_0.15.0_FINAL_PASS.zip`
**ADR:** `ADR-099`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

Every substantive claim below carries a reference of the form `[E-nn]` into
`PACK-16A-PROTOCOL-EVIDENCE-MATRIX.md`, which records the exact document,
version, date, section, URL and whether the claim is a **protocol
property**, an **implementation property** or an **inference**. Claims that
could not be verified from a primary source are marked **UNVERIFIED** and
are not used to support any conclusion.

---

## 0. How candidates were assessed, and how they were not

Four ways of choosing a voting protocol are prohibited by this round, and
they are named because each is a real temptation:

| Prohibited basis                                      | Why                                                                                                                                 |
| ----------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| Implementation convenience                            | The cheapest protocol to integrate is the one whose properties nobody checked                                                       |
| Popularity                                            | Deployment count measures adoption, not security; Helios is widely used and ships a construction broken in 2012 `[E-19]`            |
| Open source as evidence of security                   | Helios, IVXV and Swiss Post/Scytl were all open, and all three had protocol- or implementation-level flaws found by outside parties |
| Governmental use as evidence of applicability to EPD² | Estonia's architecture is lawful and long-running **and** structurally incompatible with `FIR-INV-002` (§4.6)                       |

Two further prohibitions:

- **No new cryptographic voting protocol is invented here.** The field has
  a twenty-year record of published schemes broken by third parties,
  including schemes published by the same groups that broke others'
  (`PACK-16A-PROTOCOL-EVIDENCE-MATRIX.md` §7). EPD² has no cryptographic
  research capacity, and a bespoke construction would carry the one risk
  that cannot be mitigated by process.
- **No incompatible parts of different protocols are combined without a
  composition analysis.** Composing a ballot format from one scheme with a
  tally from another and a receipt from a third is how the Swiss
  Post/Scytl trapdoor arose — a sound proof system (Bayer–Groth) with an
  unsound parameter-generation step around it `[E-33]`.

### 0.1 The filter applied before any comparison

PACK-15's boundary is not a preference. Five properties are **structural
filters**, and a candidate failing one cannot be a base regardless of its
other merits:

```text
F1  The protocol must not require the voting side to hold a per-participant
    persistent identifier, however derived.
F2  The protocol must not require identity to be attached to, signed over,
    or stored beside a ballot at any moment.
F3  The protocol must not require a party that holds both an eligibility-side
    reference and a voting-side reference for the same participation.
F4  The protocol must not require a reusable voting session, persistent
    client storage, or a third-party origin in the voting client.
F5  The protocol's tally must not require decrypting individual ballots
    where the electorate is small enough for a preference pattern to
    identify a voter.
```

`F5` is a filter for **EPD²'s** electorates, not for elections in general.
A national mixnet election with three million ballots does not have a
small-cell problem. A party working group with nineteen members ranking
seven candidates does, and PACK-15 §19.4 already recognises the class.

---

## 1. Candidates assessed

| #   | Family                                               | Verdict                                                                                |
| --- | ---------------------------------------------------- | -------------------------------------------------------------------------------------- |
| 1   | **ElectionGuard** 2.1.0                              | **SUITABLE WITH A FORMAL EPD² PROFILE**                                                |
| 2   | **Belenios** 3.0 / 3.1                               | **SUITABLE ONLY AS REFERENCE**                                                         |
| 3   | **Helios** v3 / v4-spec                              | **NOT SUITABLE**                                                                       |
| 4   | **Estonian IVXV** 1.8.0                              | **NOT SUITABLE** (as a base; valuable as a counter-example)                            |
| 5   | **Verificatum** VMN 3.1.0 (mature verifiable mixnet) | **SUITABLE ONLY AS REFERENCE** at this stage; component candidate for a future profile |
| 6   | **JCJ / Civitas** (coercion-resistant)               | **NOT SUITABLE**                                                                       |
| 7   | **Selene** (tracker-based, coercion-mitigating)      | **REQUIRES FURTHER RESEARCH** — architecturally important                              |
| 8   | **BeleniosRF** (receipt-free)                        | **REQUIRES FURTHER RESEARCH**                                                          |
| 9   | **VoteAgain** (revoting-based coercion resistance)   | **NOT SUITABLE**                                                                       |

Two further bodies of work are assessed as **evidence**, not as candidates:
the **Swiss Post / Scytl 2019 disclosures** (§5) and the **Swiss Federal
Chancellery Ordinance OEV/VEleS** (§6), which is one of the few binding
regulatory frameworks in existence and is used here as a benchmark.

---

## 2. The comparison table

Read column by column; the per-system narrative follows in §4.

### 2.1 Construction

| Property            | ElectionGuard 2.1.0                                                                                 | Belenios 3.0/3.1                                                                                     | Helios v3                                                                     | IVXV 1.8.0                                                      | Verificatum VMN 3.1.0                                      |
| ------------------- | --------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- | --------------------------------------------------------------- | ---------------------------------------------------------- |
| Intended use        | Component toolkit for E2E-verifiable elections, in-person primarily `[E-05]`                        | Remote elections, academic/associative `[E-13]`                                                      | Low-coercion online elections `[E-17]`                                        | National remote i-voting `[E-24]`                               | Mixnet component, not a voting system `[E-30]`             |
| Remote / controlled | Both; internet voting explicitly **not recommended for public elections** `[E-06]`                  | Remote                                                                                               | Remote                                                                        | Remote, with an in-person override channel `[E-28]`             | N/A                                                        |
| Group               | Integer group mod 4096-bit p, q = 2²⁵⁶−189; EC explicitly rejected for verifier simplicity `[E-02]` | BELENIOS-2048 / RFC-3526-2048 / Ed25519, chosen by question type `[E-11]`                            | Integer ElGamal `[E-18]`                                                      | ElGamal mod 2048-bit p, plaintext-carrying `[E-25]`             | Z*_p subgroups and NIST/Brainpool/SECP curves `[E-31]`     |
| Encryption          | Exponential ElGamal `[E-02]`                                                                        | ElGamal; exponential for homomorphic questions `[E-11]`                                              | Exponential ElGamal `[E-18]`                                                  | ElGamal carrying the ballot as message `[E-25]`                 | ElGamal (re-encryption) `[E-30]`                           |
| Tally               | **Homomorphic only**; mixnet on roadmap `[E-08]`                                                    | **Both** — homomorphic, or CHVote-derived mixnet `[E-12]`                                            | Homomorphic (v2+); v1 was a Sako–Kilian mixnet `[E-18]`                       | Mixnet + threshold decryption `[E-26]`                          | Re-encryption mixnet only `[E-30]`                         |
| ZK proofs           | Disjunctive Chaum–Pedersen (CDS), range proofs, Schnorr; strong Fiat–Shamir `[E-03]`                | Schnorr Σ-protocols, interval and blank-vote proofs, SHA-256 FS with full group description `[E-11]` | Disjunctive CDS/CP, **weak Fiat–Shamir over SHA-1 in shipping code** `[E-19]` | **No proof of knowledge of plaintext** `[E-27]`                 | Terelius–Wikström proof of shuffle `[E-30]`                |
| Threshold model     | Pedersen-variant DKG, k-of-n guardians, compensated shares `[E-04]`                                 | Pedersen DKG t+1-of-m, or a single mandatory trustee `[E-11]`                                        | **n-of-n, no threshold** `[E-20]`                                             | Desmedt–Frankel/Shamir, N ≥ 2M−1, shares on smartcards `[E-26]` | k-of-n, up to 25 parties `[E-31]`                          |
| Bulletin board      | **Assumed, not specified** `[E-07]`                                                                 | Append-only hash chain served by the voting server; officially flagged as a caveat `[E-15]`          | Web application, server-controlled                                            | Not a public board in the E2E sense                             | Shipped board is "a convenience, easy to replace" `[E-32]` |

### 2.2 Verifiability and voter-facing properties

| Property                 | ElectionGuard                                                                                                               | Belenios                                                                   | Helios                                                                | IVXV                                                                       | Verificatum                       |
| ------------------------ | --------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- | --------------------------------------------------------------------- | -------------------------------------------------------------------------- | --------------------------------- |
| Cast as intended         | **Cast-or-challenge (Benaloh) is core** `[E-05]`                                                                            | **Not in the base protocol**; active research 2023–24 `[E-16]`             | Cast-or-audit `[E-18]`                                                | Separate-device re-encryption check, 3 attempts in a short window `[E-29]` | Out of scope                      |
| Recorded as cast         | Confirmation code + published election record `[E-05]`                                                                      | Ballot tracker on the board `[E-14]`                                       | Ballot tracker on the board                                           | VoteID + verification app `[E-29]`                                         | Out of scope                      |
| Tallied as recorded      | Verifier spec §6, 8 verification categories `[E-09]`                                                                        | CLI `election verify` `[E-16]`                                             | Public verification scripts                                           | Shuffle-proof and decryption-proof verification `[E-26]`                   | Standalone verifier spec `[E-30]` |
| Individual verifiability | Yes                                                                                                                         | Yes                                                                        | Yes                                                                   | Yes, but empirically **9.9 % take-up at best** `[E-29]`                    | N/A                               |
| Universal verifiability  | Yes, from the published record                                                                                              | Yes, with the board caveat `[E-15]`                                        | Yes, with the weak-FS caveat `[E-19]`                                 | Partial; ODIHR records no statutory definition as of June 2025 `[E-40]`    | Yes, for the shuffle              |
| Eligibility              | **Explicitly out of scope** `[E-06]`                                                                                        | **In scope** — credential authority + ballot signatures `[E-13]`           | Voter list published **with names beside ciphertexts** `[E-21]`       | eID signature over the ciphertext `[E-24]`                                 | No notion of a voter `[E-32]`     |
| Receipt properties       | Confirmation codes; claimed non-compromising **for properly deployed in-person applications** `[E-05]`                      | Board tracker; coercion-resistance officially disclaimed `[E-14]`          | Board tracker plus published name by default                          | VoteID; verification app reveals the choice to the checking device         | N/A                               |
| Coercion position        | No coercion-resistance claim; _"cryptographic means cannot ensure that there are no cameras hidden behind voters"_ `[E-06]` | _**"Belenios fails to achieve coercion resistance"**_ `[E-14]`             | Authors: _"we do not attempt to solve the coercion problem"_ `[E-17]` | Revoting + paper override — procedural, not cryptographic `[E-28]`         | N/A                               |
| Revoting                 | Not a protocol feature                                                                                                      | **Last ballot counts**; subject of caveat #1 `[E-15]`                      | Last vote counts, per-voter replacement                               | Unlimited revoting; paper vote on election day overrides `[E-28]`          | N/A                               |
| Ranked / preferential    | **Not supported**; explicitly `[E-08]`                                                                                      | Supported **via mixnet**, publishing decrypted individual ballots `[E-12]` | Not supported in the homomorphic construction                         | Not applicable to the Estonian ballot                                      | Enables it, at the same cost      |

### 2.3 Maturity, provenance and licence

| Property                       | ElectionGuard                                                                                                                                                                     | Belenios                                                                | Helios                                                             | IVXV                                      | Verificatum                                  |
| ------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- | ------------------------------------------------------------------ | ----------------------------------------- | -------------------------------------------- |
| Specification                  | Design Specification **2.1.0, 12 Aug 2024** `[E-01]`                                                                                                                              | Specification **3.0**, undated; deployed software is 3.1 `[E-10]`       | v3 spec current in code; v4 spec never shipped `[E-22]`            | Protocols **1.8.0, 01.12.2022** `[E-23]`  | VMN **3.1.0, 2022-09-10** `[E-30]`           |
| Peer-reviewed backing          | USENIX Security 2024 `[E-05]`; third-party machine-checked verifiability `[E-09]`                                                                                                 | EasyCrypt machine-checked BPRIV + strong verifiability, CSF'18 `[E-16]` | USENIX 2008, EVT/WOTE 2009 `[E-17]`                                | E-Vote-ID 2016 `[E-23]`                   | AFRICACRYPT 2010, ACISP 2009 `[E-30]`        |
| Independent implementations    | Six independent verifiers referenced; **identities UNVERIFIED** `[E-09]`                                                                                                          | One OCaml implementation `[E-10]`                                       | One Python implementation                                          | One, publication-only repository `[E-23]` | One, Java/C                                  |
| Reference-implementation state | **No production-grade 2.1 implementation**: Rust is self-declared "INCOMPLETE, EXPERIMENTAL"; Python pinned at spec 0.95; best 2.0 implementation is third-party Kotlin `[E-10a]` | Deployed; development moved to a startup structure in 2025 `[E-10]`     | Maintained as software; cryptographic core frozen at 2010 `[E-22]` | Deployed nationally `[E-23]`              | Deployed; vendor reports >3 M votes `[E-31]` |
| Test vectors                   | Kotlin implementation ships JSON vectors; first-party 2.1 vectors **UNVERIFIED** `[E-10a]`                                                                                        | **UNVERIFIED**                                                          | —                                                                  | —                                         | Verifier spec is the conformance target      |
| Licence                        | **MIT** `[E-10a]`                                                                                                                                                                 | **AGPL-3.0** `[E-10]`                                                   | Apache-2.0 `[E-22]`                                                | Published for review `[E-23]`             | **MIT** `[E-31]`                             |
| Cryptographic agility          | Parameters are spec-fixed; version-gated                                                                                                                                          | Group is per-question-type selectable `[E-11]`                          | Fixed                                                              | Fixed                                     | Group-parametric `[E-31]`                    |

### 2.4 Compatibility with the EPD² boundary

This is the column that decides the round.

| Filter                                                    | ElectionGuard | Belenios            | Helios   | IVXV     | Verificatum |
| --------------------------------------------------------- | ------------- | ------------------- | -------- | -------- | ----------- |
| `F1` no per-participant persistent voting-side identifier | **PASS**      | **FAIL**            | **FAIL** | **FAIL** | PASS (n/a)  |
| `F2` no identity bound to a ballot at any moment          | **PASS**      | partial FAIL        | **FAIL** | **FAIL** | PASS (n/a)  |
| `F3` no party holding both-side references                | **PASS**      | **FAIL**            | **FAIL** | **FAIL** | PASS (n/a)  |
| `F4` no reusable session / client persistence / 3P origin | PASS          | PASS                | PASS     | **FAIL** | PASS (n/a)  |
| `F5` no individual-ballot decryption in small electorates | **PASS**      | FAIL in mixnet mode | PASS     | **FAIL** | **FAIL**    |
| PACK-15 unlinkability compatible                          | **yes**       | no                  | no       | no       | n/a         |
| No-intermediate-tally compatible                          | **yes**       | yes                 | yes      | yes      | yes         |
| German publicity-principle posture (§6)                   | partial       | partial             | weak     | weak     | n/a         |

**Belenios `F1`/`F3` explanation.** Belenios's credential authority
generates per-voter signing credentials and sends the voting server a list
pairing **public credentials with voter identity and weight** `[E-13]`.
That list is precisely the row PACK-15 §3 forbids: a single store holding
an eligibility-side reference and a voting-side reference for the same
participation. It is not an incidental implementation choice — the ballot
signature _is_ the eligibility mechanism, and removing it removes Belenios's
defence against server-side ballot stuffing. In the default hosted mode the
server plays the credential-authority role itself, collapsing the
separation entirely `[E-13]`.

**Helios `F2` explanation.** Helios publishes voter names next to
encrypted ballots by default `[E-21]`. Aliasing is available per election,
but the default and documented design is the opposite of PACK-15's
architecture, and the name-beside-ciphertext pairing is exactly what makes
the Cortier–Smyth targeted replay attack possible `[E-19]`.

**IVXV `F1`–`F5` explanation.** See §4.6 — this is the sharpest case.

---

## 3. Per-candidate assessment

### 3.1 ElectionGuard — **SUITABLE WITH A FORMAL EPD² PROFILE**

**What it is.** A cryptographic toolkit, not an election system, and it
says so: _"ElectionGuard is not a complete election system. It instead
provides components…"_ `[E-05]`. Exponential ElGamal in a 4096-bit integer
group with a 256-bit subgroup, homomorphic aggregation, disjunctive
Chaum–Pedersen and range proofs, Pedersen-variant distributed key
generation with k-of-n guardians and compensated decryption shares, a
confirmation-code construction, and Benaloh cast-or-challenge `[E-02]`,
`[E-03]`, `[E-04]`, `[E-05]`.

**Why it fits this architecture, and this is the whole argument.**
ElectionGuard's most-cited limitation is that it does not do eligibility:

> _"An E2E-verifiable election does not guarantee that the recorded votes
> have been cast by legitimate voters: this needs to be ensured through the
> traditional voter identification mechanisms that are already deployed in
> elections."_ `[E-06]`

> _"Eligibility is thereby achieved entirely through publicly-verifiable
> processes that are entirely outside the scope of ElectionGuard, and the
> only intersection is for interested parties to confirm that the number of
> ballots cast does not exceed the number of voters listed."_ `[E-06]`

For most integrators that sentence is a gap to be filled. For EPD² it is a
**specification of the interface PACK-15 already built**. PACK-15 spent a
round establishing eligibility on the far side of a trust boundary with
exactly one artifact crossing and no shared reference; ElectionGuard
requires eligibility to be established outside itself and asks only that
ballots-cast not exceed voters-entitled — an aggregate count, which is the
one figure the two sides can share without a per-participation reference.
The boundary and the protocol were designed independently and meet cleanly.

**Homomorphic-only tally is a feature here, not a limitation.**
Individual ballots are never decrypted. There is no Italian attack, no
preference-pattern signature, no per-ballot plaintext to leak, and
`F5` is satisfied structurally rather than by policy. In a party whose
smallest bodies have single-digit membership, this matters more than
ranked-ballot support.

**Cast-or-challenge is the cast-as-intended mechanism**, and it is core
rather than bolted on `[E-05]`. Version 2.1 made challenged-ballot opening
more efficient by releasing encryption nonces rather than performing
verifiable decryption `[E-03]`.

**What it does not give us, stated plainly.**

| Gap                                                               | Consequence for EPD²                                               | Owner                  |
| ----------------------------------------------------------------- | ------------------------------------------------------------------ | ---------------------- |
| No bulletin board `[E-07]`                                        | EPD² must specify one as a distinct trust boundary                 | PACK-16C               |
| No eligibility, no authentication `[E-06]`                        | Supplied by PACK-15 — this is the fit, not a gap                   | done                   |
| **No ranked-choice / IRV / STV** `[E-08]`                         | Those election types are **not supported** in the selected profile | `EPD2-MIX-1`, deferred |
| No coercion resistance `[E-06]`                                   | Must be stated as a limit, never as a solved property              | PACK-16A §7            |
| Internet voting _"not recommended for public elections"_ `[E-06]` | Reinforces `PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT`      | governance             |
| **No production-grade 2.1 implementation** `[E-10a]`              | The single largest engineering risk in this selection              | PACK-16D               |

**The implementation-maturity risk is the honest weakness of this
choice and is recorded as such.** The only spec-2.1 implementation is
Microsoft Research's Rust codebase, which self-declares _"Project status:
INCOMPLETE, EXPERIMENTAL"_; the historical Python reference implementation
is pinned at spec 0.95; the most complete 2.x implementation is
third-party (VotingWorks Kotlin, at 2.0.0) `[E-10a]`. Selecting the
**specification** as the base is therefore not the same as selecting a
library, and PACK-16A deliberately selects the specification.
`PACK-16A-OPEN-DECISIONS.md` `OD-P16A-04` carries the library question to
PACK-16D, and `PACK-16A-TRUSTEE-AND-CEREMONY-REQUIREMENTS.md` §6 requires
that whatever is chosen be **verifier-checkable by an implementation EPD²
did not write**.

**Receipt nuance — do not overstate.** ElectionGuard's position is _not_
"we fail receipt-freeness". USENIX'24 argues that confirmation codes,
being derived entirely from encryptions, do not compromise privacy _"in
properly deployed in-person applications"_ `[E-05]`. The residual is stated
conditionally in the specification: _"any group that has the ability to
decrypt individual ballots can also coerce voters by demanding to see their
confirmation codes"_ `[E-06]`. EPD² is a **remote** deployment, so the
in-person qualifier does not transfer, and
`PACK-16A-COERCION-AND-RECEIPT-BOUNDARY.md` treats the remote case on its
own terms rather than importing a claim made for a different setting.

**Verdict: SUITABLE WITH A FORMAL EPD² PROFILE.** Not "suitable as base"
unqualified, because the profile must add a bulletin board, a verification
client, a revoting decision, a receipt surface and a set of prohibitions
that ElectionGuard neither provides nor forbids.

### 3.2 Belenios — **SUITABLE ONLY AS REFERENCE**

Belenios is the most honest system in this comparison and the best
documented on its own limits. Its FAQ states, without hedging:

> _**"Belenios fails to achieve coercion resistance: it is easy to sell the
> credentials and the login and passwords (unless a CAS server is
> used)."**_ `[E-14]`

Its caveats document `[E-15]` names three limitations that appear in no
protocol description: a **revoting-enabled verifiability attack** in which
a malicious server replaces a voter's latest ballot with an earlier one
after she has checked it — _"this attack cannot be detected in Belenios 3.1
and earlier"_; the **absence of a proper bulletin board**, since a
dishonest server _"may provide inconsistent views to the participants"_;
and **fragile vote privacy**, because trustees do not verify individual
ballots and, in mixnet mode, skip verification of previous shuffles _"for
usability reasons"_.

It also carries the strongest formal analysis in the field: EasyCrypt
machine-checked BPRIV ballot privacy and strong verifiability `[E-16]` —
with the assumptions stated exactly, and they are load-bearing.
Verifiability is proven **separately** for a dishonest ballot box with an
honest registrar, or a dishonest registrar with an honest ballot box, and
**never both**; corruption is **static**; and the formalisation surfaced a
missing assumption, that privacy requires an honest registrar `[E-16]`.

**Why it is not the base.** The credential-authority model is Belenios's
central contribution and is incompatible with PACK-15 at the structural
level, not at the configuration level. The credential authority holds the
voter → credential mapping; the server holds a list pairing public
credentials with voter identity and weight `[E-13]`. That list is the
prohibited row. Removing it removes the ballot signature, and the ballot
signature is what prevents server-side stuffing — so the mechanism cannot
be subtracted without subtracting the property. In the default hosted
configuration the server generates the credentials itself, collapsing the
separation `[E-13]`.

Three further facts weigh against it: the published specification is for
**3.0** while the deployed software is **3.1** `[E-10]`; the CSPN
certification campaign **did not obtain certification** because the
security target had to be enlarged `[E-16a]`; and the mixnet mode publishes
decrypted individual ballots `[E-12]`, failing `F5` for EPD²'s small
bodies.

**What EPD² takes from it.** Three things, and they are significant.
First, the caveats document is the model for
`PACK-16A-COERCION-AND-RECEIPT-BOUNDARY.md` — a separate, public,
plain-language statement of what the deployed system does not do. Second,
caveat #1 is the strongest published evidence in the revoting decision
(`PACK-16A-REVOTING-AND-BALLOT-LIFECYCLE.md` §2). Third, the machine-checked
proof's _assumption structure_ — never both parties corrupt — is the
template for how `ADR-099` states its own trust assumptions.

**Licence note.** Belenios is AGPL-3.0 `[E-10]`. EPD²'s intended licensing
baseline is `EUPL-1.2` under `FIR-OSS-001` … `FIR-OSS-006`, which are
register obligations this round neither implements nor claims compliance
with. The interaction of AGPL-3.0 with EUPL-1.2 is a licensing question for
those entries and is **not decided here**; it is recorded in
`PACK-16A-OPEN-DECISIONS.md` `OD-P16A-08`. It is noted because a candidate
that would force it is a candidate with a legal dependency, and the
selected candidate (MIT `[E-10a]`) does not create one.

### 3.3 Helios — **NOT SUITABLE**

Helios is the intellectual ancestor of most of this field and should be
credited as such. It is not a candidate, for reasons its own authors state
first:

> _"UCL and the authors do not endorse the use of Helios 2.0 for large,
> high-stakes, governmental elections."_ `[E-17]`

> _"With Helios, we do not attempt to solve the coercion problem."_ `[E-17]`

Beyond the authors' own position, four disqualifying facts:

1. **Weak Fiat–Shamir is still in shipping code.** Bernhard–Pereira–
   Warinschi showed in 2012 that hashing only the commitment yields
   unsound and unextractable proofs when statements are adaptively chosen,
   and that this manifests in Helios `[E-19]`. The **v4 specification
   documents the correct fix** — hashing contextual data into the
   challenge `[E-22]` — and v4 appears never to have shipped: the
   deployed v3 construction, `SHA1` over commitments only, remains in
   `helios-server` master as of 2026 `[E-19]`.
2. **No ballot weeding.** Cortier–Smyth showed Helios does not satisfy
   ballot independence: an adversary reads a target's ciphertext off the
   board — _identifiable because the board carries voter names_ — and has
   corrupted voters resubmit it `[E-19]`. The documented resolution was a
   _"fix scheduled for Helios v3.1 through ballot structure redesign"_;
   duplicate-ciphertext detection is not present in current master `[E-19]`.
3. **n-of-n trustees.** The code comment reads _"For now, no support for
   threshold"_ `[E-20]`. One unavailable trustee makes the election
   untallyable. That is not an acceptable failure mode for a binding party
   vote.
4. **Voter names beside ciphertexts by default** `[E-21]` — a direct `F2`
   failure.

**Verdict: NOT SUITABLE.** Retained as **reference** for the Benaloh
cast-or-audit lineage and as the field's clearest case study in the gap
between a corrected specification and shipped code.

### 3.4 Estonian IVXV — **NOT SUITABLE as a base; the most instructive counter-example**

Estonia runs the largest and longest remote-voting deployment in the world:
312,182 i-votes at 51.1 % of participating voters in 2023 `[E-29]`. Its
engineering is serious, its documentation is public, its threshold key
management uses Desmedt–Frankel/Shamir with shares on smartcards and a
constraint N ≥ 2M−1 `[E-26]`, and its shuffle proofs are
Terelius–Wikström verified against the Verificatum verifier manual
`[E-26]`.

**And its architecture is the one PACK-15 exists to refuse.**

The voter's application encrypts the ballot and then **digitally signs the
ciphertext with the national eID** `[E-24]`. The signed vote is stored by
the collector service under `votes/<voter id>/` `[E-24]`. The
identity ↔ ciphertext binding is therefore materialised in the ballot box
and persists through the entire voting period and both paper-voting
windows — it has to, because a paper vote on election day overrides the
i-vote, and you cannot anonymise until you know who voted on paper
`[E-28]`. The link is severed by an **offline processing application**
that strips signatures and emits the anonymised ballot box `[E-24]`. The
mixnet runs **after** the severing.

Stated as an EPD² finding: **the mixnet is not what protects the voter from
the collector. A trusted offline procedure is.** That is a defensible
national design with legal and procedural controls around it, and it fails
`F1`, `F2`, `F3` and `F5` simultaneously. There is no configuration of
IVXV that satisfies PACK-15's structural rule, because the rule says the
pair never exists to be joined and IVXV's design requires that it exist.

Two further documented findings are recorded because they generalise:

- **Müller's malleability attacks** `[E-27]`: IVXV submits a bare
  ciphertext with **no proof of knowledge of the plaintext**, so an
  attacker controlling one voter can shift or encode a victim's vote and
  read it out of the published result. The fix is a NIZK proof of
  knowledge on submission. **EPD² adopts this as a requirement** —
  `PACK-16A-BALLOT-MODEL-SPECIFICATION.md` `BM-14`.
- **Revoting defeats individual verifiability** `[E-28a]`: a compromised
  voter device can defeat the verification mechanism _by taking advantage
  of the revoting option_, without compromising the verification app or any
  server component. This is the single most important input to the
  revoting decision.

Also recorded: Springall et al. recommended in 2014 that _"Estonia
discontinue the I-voting system"_ `[E-28b]`; Estonia's substantive response
was to build IVXV `[E-23]`. Individual-verification take-up peaked at
**9.9 %** `[E-29]`. And ODIHR's June 2025 Opinion recommends that Estonia
_define in law_ the requirements for individual verifiability and its
associated coercion-resistance measures — meaning that as of that date they
are **not** legally defined `[E-40]`.

**Verdict: NOT SUITABLE.** Retained as the reference for threshold key
custody, for the operational reality of individual verifiability, and as
the worked example of why PACK-15's structural rule is stated as "the pair
never exists" rather than "do not join these tables".

### 3.5 Verificatum — **SUITABLE ONLY AS REFERENCE at this stage**

Verificatum VMN is a mature, independently specified verifiable mixnet:
Sako–Kilian re-encryption with the Terelius–Wikström proof of a shuffle,
k-of-n mix-servers up to 25 parties, a **standalone verifier
specification** so that a verifier can be written without the
implementation, MIT licence `[E-30]`, `[E-31]`.

It is not a voting system and does not claim to be: _"we do not provide
complete services for electronic voting"_ `[E-32]`. Its verifier
specification declares the surrounding formats out of scope — _"All of the
above falls outside the scope of this document, since we cannot anticipate
the scheme used to represent these objects"_ `[E-32]` — and its user manual
carries the warning that decides its role here:

> _**"WARNING! On its own the mix-net provides no protection against
> Pfitzmann's attack (malleability attack)."**_ `[E-32]`

That warning, Cortier–Smyth on Helios and Müller on IVXV are three
instances of one gap. **Ballot independence is the recurring systemic
failure of deployed verifiable voting systems**, and PACK-16A treats "does
the system require a proof of knowledge of the plaintext on submission?" as
a first-class selection axis rather than a detail. The selected family
answers yes by construction; the two rejected deployed systems answered no
or answered it weakly.

**Verdict: SUITABLE ONLY AS REFERENCE** for PACK-16A. Verificatum is the
leading **component candidate** for a future mixnet profile
(`EPD2-MIX-1`), which is deferred and currently prohibited (§4 of
`PACK-16A-BALLOT-MODEL-SPECIFICATION.md`). Nothing in this round selects,
rejects or commits to it as a component.

### 3.6 JCJ / Civitas — **NOT SUITABLE**

JCJ is the origin of the formal definition of coercion-resistance and the
reason this pack can distinguish it from receipt-freeness: JCJ's adversary
may demand that a voter vote a particular way, **abstain**, or **surrender
her keys** `[E-34]`. Receipt-freeness defeats only the proof-of-vote
channel; coercion-resistance additionally defeats forced abstention and
credential surrender. Every honest statement in
`PACK-16A-COERCION-AND-RECEIPT-BOUNDARY.md` rests on that distinction.

Four facts disqualify it as a base:

1. **The untappable-channel assumption.** _"We assume therefore that the
   voter receives her credential from R via an untappable channel"_
   `[E-34]`. Civitas makes it operational: _"Each voter trusts at least one
   registration teller, and the channel from the voter to the voter's
   trusted registration teller is untappable"_, with the authors' own
   fallback — _"we recommend requiring in-person registration"_ `[E-35]`.
   Coercion-resistance here is procured by an unobserved interval, not by
   cryptography.
2. **Quadratic tallying.** _"the overhead for tallying authorities is
   quadratic in the number of voters. Thus the scheme is only practical for
   small elections"_ `[E-34]`; Civitas confirms O(N²) pairwise plaintext
   equivalence tests and mitigates by block partitioning, which _"significantly
   increases leakage"_ `[E-35]`. Linear-time variants buy speed with leakage
   or stronger trust `[E-36]`.
3. **Usability.** Civitas §10: voters may find _"generating fake
   credentials, storing and distinguishing real and fake credentials
   (especially over a long time), and lying convincingly to an adversary to
   be quite difficult"_ `[E-35]`. The scheme offloads an adversarial
   deception task onto ordinary members, indefinitely. For a party
   membership that includes people who need assisted voting, this is not a
   usability inconvenience; it is a disenfranchisement mechanism.
4. **The property itself is contested.** Cortier, Gaudry and Yang show that
   _"even in the JCJ original protocol, the cleansing step leaks more than
   the difference between the sizes of its input and output"_ — the
   cleansing reveals _why_ ballots were removed, letting a coercer detect
   disobedience `[E-37]`.

Civitas is a **research prototype**: _"Although not yet suitable for
deployment in national elections…"_ `[E-35]`, with no production deployment
found.

**Verdict: NOT SUITABLE.** Retained as the source of the vocabulary and of
the honest boundary in §7.

### 3.7 Selene — **REQUIRES FURTHER RESEARCH**, and it matters

Selene assigns each voter a **tracker number** through verifiable
re-encryption mixes, publishes trackers beside votes on the board, and
delivers each voter her tracker **only after the results are posted**, so
that a coerced voter can point at a different tracker `[E-38]`. The
deniability rests on a trapdoor only the voter holds `[E-38]`.

Its authors are explicit about what it is: _"Selene will manage to
**mitigate** such coercion attacks"_; _"targeted at low coercion threat
environments"_ `[E-38]`. An independent assessment states it exactly:
_"Coercion mitigation is weaker than coercion resistance, but may be
appropriate for low-stakes elections"_, and Selene is _"vulnerable to
collisions among such lies"_ `[E-39]`.

**Why it is architecturally important to EPD² anyway.** Selene's stated
motivation is the German constitutional problem restated by cryptographers:

> _"many voters may not really understand the purpose of the encrypted
> ballot and the various checks that they can perform."_ `[E-38]`

The BVerfG requires that citizens be able to scrutinise the key steps
_"zuverlässig und ohne besondere Sachkenntnis"_ — reliably and without
specialist knowledge `[E-41]`. "Check this ciphertext against the board"
sits badly with that. "My number, next to my vote, on a public list" sits
considerably better. That convergence is the most useful cross-over between
the cryptographic and the legal halves of this round, and it is recorded
here rather than acted on.

**Verdict: REQUIRES FURTHER RESEARCH**, owned by PACK-16C as a candidate
**verifiability presentation layer**, not as a base protocol, and gated on:
the collision problem and its successors (Selene II, Hyperion) `[E-39]`;
the pre-publication demand window `[E-38]`; the unmonitored-delivery
assumption `[E-38]`; and whether a tracker can be delivered inside EPD²'s
isolation rules without becoming a transferable receipt.

### 3.8 BeleniosRF — **REQUIRES FURTHER RESEARCH**

BeleniosRF achieves **strong receipt-freeness** — _"even dishonest voters
cannot prove how they voted"_ — by having the voting server re-randomise
each ballot, using signatures on randomizable ciphertexts `[E-42]`. Its
usability advantage over the fake-credential family is real: voters adopt
no anti-coercion strategy at all.

Two limits decide its status. It is **receipt-freeness, not
coercion-resistance**: it addresses the proof channel and not forced
abstention or credential surrender `[E-42]`. And it is a **research
prototype** — not part of the shipped Belenios software, no deployment
reported `[E-42]`.

**Verdict: REQUIRES FURTHER RESEARCH.** Recorded as the most promising
direction if EPD² later needs receipt-freeness stronger than the selected
profile provides.

### 3.9 VoteAgain — **NOT SUITABLE**

VoteAgain provides coercion resistance through revoting with **deterministic
ballot padding**, in O(n log n) `[E-43]` — the design that would most
directly have supported a revoting decision in this round.

It was **broken**. Müller shows verifiability, ballot-privacy and
coercion-resistance attacks, concluding that _"all voting authorities in
VoteAgain need to be trusted for coercion-resistance"_, with **no fix
proposed** `[E-44]`. The implementation is a Python research prototype with
the bulletin board and token protocol unimplemented `[E-43]`.

**Verdict: NOT SUITABLE.** Its failure is a direct input to the revoting
decision: the most credible attempt to make revoting a _cryptographic_
coercion control did not survive review.

---

## 4. Cross-cutting findings

These four findings shaped the selection more than any single system's
feature list.

**Finding 1 — where the identity↔ballot link lives is the sharpest
architectural divide.** Helios never binds identity cryptographically but
publishes the name beside the ciphertext. IVXV binds it with a national
eID signature and severs it in a trusted offline step. Belenios binds it
through a credential list held by two parties. ElectionGuard does not have
the concept at all, because eligibility is outside it. Only the last is
compatible with a boundary that says the pair never exists.

**Finding 2 — ballot independence is the recurring systemic failure.**
Cortier–Smyth on Helios (2010/2012) `[E-19]`, Müller on IVXV (2022/2023)
`[E-27]`, and Verificatum's own Pfitzmann warning `[E-32]` are three
instances of one gap: a submitted ciphertext with no proof of knowledge of
its plaintext is malleable, and malleability is a privacy attack.
**Requirement `BM-14` follows directly.**

**Finding 3 — weak Fiat–Shamir is a repeat offender in production code.**
Found in Helios in 2012 `[E-19]`, found again in Swiss Post/Scytl in 2019
`[E-33]`, and still present in `helios-server` master in 2026 `[E-19]`. The
selected specification uses strong Fiat–Shamir, hashing statement as well
as commitment `[E-03]`; **verifying that the chosen implementation actually
does so is an explicit PACK-16D acceptance criterion**, not an assumption.

**Finding 4 — mixnet risk in practice is parameter-generation and
integration risk, not proof-system risk.** The Bayer–Groth shuffle argument
was sound; Scytl's commitment parameters were generated _"without a proof
of how they arose"_, and the routine that generated them produced _"precisely
the trapdoor that is needed to break the binding property"_ `[E-33]`. A
transcript that passes verification while altering votes is the worst
possible failure, because the verification is the control. **This is why
`PACK-16A-TRUSTEE-AND-CEREMONY-REQUIREMENTS.md` §3 requires published,
independently reproducible parameter provenance, and why no mixnet profile
is activated in this round.**

---

## 5. Swiss Post / Scytl 2019 — evidence, not a candidate

Two disclosures by Lewis, Pereira and Teague in March 2019 `[E-33]`: a
trapdoor-commitment flaw allowing a shuffle-proof transcript that _"passes
verification but actually alters votes"_, and a decryption-proof flaw
allowing proofs that _"verify perfectly but actually prove a decryption
that is different from the true plaintext"_. Both were confirmed; the Swiss
programme was suspended and the system redesigned.

The lesson EPD² takes is Finding 4 above, and one further rule: **a
verification that can be satisfied by a dishonest party is worse than no
verification**, because it converts scrutiny into assurance. Every
verification requirement in this pack therefore names what the verifier
checks, what it cannot check, and who could still cheat.

---

## 6. Regulatory benchmark — Swiss OEV/VEleS

The Swiss Federal Chancellery Ordinance on Electronic Voting (SR 161.116,
in force 1 July 2022) is the most demanding binding framework located
`[E-45]`, and is used here as a yardstick because Germany has none for
political elections (§7 of `PACK-16A-GERMAN-LEGAL-BOUNDARY.md`):

| OEV provision | Requirement                                                                                        | EPD² posture after PACK-16A                                                                 |
| ------------- | -------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| Art. 5(2)     | Individual verifiability — proof that the trustworthy part registered the vote as entered          | **specified**; mechanism owed by PACK-16C                                                   |
| Art. 5(1),(3) | Complete verifiability — detect any manipulation falsifying the result, preserving secrecy         | **specified**; requires a board and a verifier not yet built                                |
| Art. 8        | A trustworthy part built from **control components** with diverse design and independent operation | **partially specified** — threshold trustees and independent mirrors; diversity is PACK-16B |
| Art. 10       | Independent examination of protocol, software, infrastructure, ISMS                                | **required before any activation**; governance gate                                         |
| Art. 11       | Publication of source code and parameters                                                          | consistent with `FIR-OSS-*`; not completed                                                  |
| Annex 2.14    | **A symbolic and a cryptographic proof** of protocol compliance                                    | **not met, and not claimed**; recorded as `OD-P16A-06`                                      |

Recording this benchmark has a purpose beyond comparison: it fixes what
"ready" would have to mean, so that no later round can define readiness
downwards.

---

## 7. The coercion boundary, stated once here and developed elsewhere

The single most important sentence located in the entire body of research:

> _"Note that if the coercer can monitor the voter throughout the vote
> casting period, then resistance is futile … For remote voting, we need to
> assume that voters will have some time when they can interact with the
> voting system unobserved."_ `[E-46]`

Coercion-resistance for remote voting is **not a cryptographic property**.
It is a conditional property contingent on an unobserved interval. A
polling booth _manufactures_ that interval by physical enforcement; remote
voting can only _assume_ it. Every scheme in §3.6–§3.9 relocates the
assumption rather than removing it: JCJ to postal credential delivery,
Civitas to in-person registration, Selene to unmonitored tracker delivery,
VoteAgain to an anonymous channel.

`PACK-16A-COERCION-AND-RECEIPT-BOUNDARY.md` is the full treatment and the
home of the prohibited-claims registry. It exists because this is the
property most likely to be overclaimed, by us, in good faith, later.

---

## 8. Verdicts

| Family                  | Verdict                                 | Recorded reason                                                                                                                                                                                    |
| ----------------------- | --------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **ElectionGuard 2.1.0** | **SUITABLE WITH A FORMAL EPD² PROFILE** | Eligibility explicitly out of scope — the exact interface PACK-15 provides; homomorphic-only tally satisfies `F5`; cast-or-challenge is core; threshold guardians; published verifier spec; MIT    |
| **Belenios 3.0/3.1**    | **SUITABLE ONLY AS REFERENCE**          | Credential list pairs identity with a voting-side reference (`F1`,`F3` fail); mixnet mode fails `F5`; coercion resistance officially disclaimed; spec/software version gap                         |
| **Helios v3**           | **NOT SUITABLE**                        | Weak Fiat–Shamir in shipping code; no ballot weeding; n-of-n trustees; names beside ciphertexts; authors disclaim high-stakes use                                                                  |
| **Estonian IVXV 1.8.0** | **NOT SUITABLE**                        | Identity↔ciphertext binding stored for the whole period and severed by a trusted offline step — fails `F1`,`F2`,`F3`,`F5`; no plaintext-knowledge proof; revoting defeats individual verifiability |
| **Verificatum VMN**     | **SUITABLE ONLY AS REFERENCE**          | Not a voting system; no ballot independence on its own; leading component candidate for a deferred mixnet profile                                                                                  |
| **JCJ / Civitas**       | **NOT SUITABLE**                        | Untappable-channel assumption; O(n²); fake-credential usability; never deployed; coercion-resistance itself contested                                                                              |
| **Selene**              | **REQUIRES FURTHER RESEARCH**           | Coercion _mitigation_ only, with collisions; but lay-comprehensible verifiability is the closest published answer to the BVerfG standard                                                           |
| **BeleniosRF**          | **REQUIRES FURTHER RESEARCH**           | Strong receipt-freeness with no voter strategy required; research prototype, not deployed, not shipped in Belenios                                                                                 |
| **VoteAgain**           | **NOT SUITABLE**                        | Broken by third-party analysis with no fix proposed; all authorities must be trusted                                                                                                               |

**Selected: ElectionGuard 2.1.0 as the specification base, bound into the
EPD² profile `EPD2-HOM-1`.**
`PACK-16A-BALLOT-MODEL-SPECIFICATION.md` is the profile.
`ADR-099` is the decision record, status `proposed`.

**SELECTED FOR ARCHITECTURAL REVIEW. REQUIRES EXTERNAL REVIEW. REQUIRES
LEGAL ASSESSMENT. NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**
