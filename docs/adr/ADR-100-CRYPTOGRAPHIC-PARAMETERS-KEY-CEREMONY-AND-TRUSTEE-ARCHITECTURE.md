# ADR-100 — The cryptographic parameters are adopted unmodified, and the trust that depends on them is placed in five people who have never met

**Status:** proposed
**Round:** PACK-16B — Cryptographic Parameters, Key Ceremony and Trustee Architecture (specification and ADR only)
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`

**NO CODE. NO CRYPTOGRAPHIC CODE. NOT IMPLEMENTED. NOT A CANDIDATE FOR
IMPLEMENTATION. NOT A PASS. NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.
PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

Evidence references `[F-nn]` resolve in
`docs/packs/PACK-16/PACK-16B-PROTOCOL-EVIDENCE-MATRIX.md`.
Evidence references `[E-nn]` resolve in
`docs/packs/PACK-16/PACK-16A-PROTOCOL-EVIDENCE-MATRIX.md`, unchanged.

---

## Context

ADR-099 selected `EPD2-HOM-1` — a homomorphic, threshold-decrypted,
challengeable ballot model in the ElectionGuard 2.1 lineage — and left four
things open on purpose: what the parameters actually are, who holds the
threshold, how the key comes into existence, and what happens when a
guardian is lost or turns.

Those four are one decision, because each constrains the others. A parameter
choice that forks the verifier changes what "threshold" can be verified by.
A quorum chosen for convenience changes what a compromise costs. A ceremony
without a witness changes what a transcript proves.

```text
PACK-16A chose the protocol.
PACK-16B chooses the numbers, the people, and the room.
PACK-16C will choose how a ballot is cast and verified.
PACK-16D will choose what code runs.
```

This ADR records the second of those four.

---

## Inherited decisions — not reopened

```text
EPD2-HOM-1                       ElectionGuard 2.1 protocol lineage
homomorphic tally model          exponential-ElGamal construction family
Benaloh cast-or-challenge        NIZK well-formedness proofs
BM-14                            no revoting
EPD2-MIX-1 deferred              PACK-15 identity boundary
Voting Client isolation          no intermediate tally
bulletin board required          NO PERSON-TO-BALLOT LINK
```

**None of these is revisited, weakened or reinterpreted here.** Where this
round found a fact that contradicted a PACK-16A _statement_, it corrected
the statement and left the _requirement_ standing — once, in `KC-11`, and
the correction is recorded rather than applied silently.

---

## Decision drivers

| Driver                                                                 | Weight in this decision                                            |
| ---------------------------------------------------------------------- | ------------------------------------------------------------------ |
| A record must be verifiable by **any conforming verifier**             | Decisive for the parameter choice                                  |
| A record must remain verifiable **decades later, with no live system** | Decisive for pinning and for `PS-10`                               |
| **No fewer than `k` parties may ever decrypt**, by any path            | Decisive for backup, recovery and break-glass                      |
| German cryptographic guidance                                          | Strong; alignment is diligence, not compliance                     |
| The **absence of independent review** of the key ceremony `[F-31]`     | Decisive wherever a choice was between conservative and convenient |
| Volunteers, not institutions, will hold the shares                     | Decisive for quorum size and for accessibility                     |
| Performance                                                            | **Explicitly non-decisive** (`IM-46`)                              |

---

## Parameter candidates

Four options were assessed against sixteen criteria
(`PACK-16B-PARAMETER-SET-SPECIFICATION.md` §2):

| Option | Description                                                            | Verdict                                                                                                                                        |
| ------ | ---------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| **A**  | The specification's fixed 4096-bit finite-field parameters, unmodified | **SELECTED**                                                                                                                                   |
| B      | Different finite-field parameters (larger `p`, different `q`)          | **Rejected** — forks every conforming verifier `[F-05]`, and `H_q` would need redesign `[F-07]`                                                |
| C      | An elliptic-curve adaptation                                           | **Rejected** — a protocol adaptation, not a parameter choice; outside BSI's recommended curve set `[F-23]`; security proofs need re-derivation |
| D      | A post-quantum or hybrid construction                                  | **Rejected for now** — a different protocol entirely; carried as `OD-P16B-06` with a dated deadline                                            |

**The decisive discovery** is that the specification _fixes_ its parameters
`[F-04]` and requires bit-equality at verification `[F-05]`. That converts
B and C from parameter choices into verifier-forking protocol adaptations,
each needing its own ADR, its own proofs and its own verifier — which is a
different decision from the one this round was asked to make.

**Elliptic curves were not rejected for being slower or faster.** They were
rejected because choosing them would mean no conforming verifier could read
an EPD² election record.

---

## Selected parameter profile

```text
EPD2-CRYPTO-1

  Construction        exponential ElGamal over a prime-order subgroup of Z_p*
  p                   4096 bits, fixed, ln(2)-derived middle with printed δ   [F-02]
  q                   2^256 − 189, fixed                                       [F-01]
  r                   (p − 1)/q, r/2 prime                                     [F-02]
  g                   2^r mod p                                                [F-02]
  H                   HMAC-SHA-256 as a random oracle, 32-byte key slot        [F-06]
  H_q                 H(...) mod q — valid only for this q                     [F-07]
  KDF                 SP 800-108r1 counter-mode HMAC                           [F-10]
  Encoding            fixed-length big-endian 512 / 32 / 4 bytes, no separators [F-09]
  Specification pin   SHA-256 a263ab3cd2cf28f05de324ecd2d9752ffed45f814709582b4c2bb23d1826b936

  deprecation_date    2030-12-31 (high assurance) / 2031-12-31
  prohibition_date    2032-12-31
```

**The parameters are not EPD²'s to change.** `PS-01`…`PS-04` make that
architectural rather than procedural: there is no negotiation, no fallback
and no reduced-parameter mode to select.

Provenance was **independently regenerated** by this round — `p`, `q`, `r`
and `g` reproduced byte for byte, with `(p−1) mod q = 0`, `g^q mod p = 1`
and the required primalities `[F-03]` — and `TV-01` makes that a standing
acceptance test rather than a memory.

---

## ElectionGuard compatibility

```text
EXPECTED SPECIFICATION COMPATIBILITY,
CONDITIONAL ON INDEPENDENT VERIFIER TESTING.
```

**No known verifier-consumed ElectionGuard 2.1 field is changed by the
PACK-16B orchestration profile.** Full interoperability with independent
conforming verifiers **has not yet been demonstrated**, and
`TV-07`/`TV-19` — independent implementation and independent conforming-
verifier interoperability testing — **remain mandatory before implementation
acceptance**. `TV-11` is unchanged and still binds the scope of any review.

EPD² adds two things the upstream specification leaves unspecified — a
complaint and disqualification protocol, and a pre-publication commitment
round — and **both sit at the orchestration layer**. No hash input, no
challenge, no proof and no verifier-consumed field is changed. The
`H_X = H(H_B; "epd2_ceremony_v1")` domain uses **string** tags precisely so
that EPD² cannot squat an upstream tag byte.

**What EPD² may honestly say:** it implements the specification unmodified,
with additional published governance around the ceremony.
**What it may not say:** that the specification endorses the additions.

---

## German-guidance assessment

Against **BSI TR-02102-1, Version 2026-01, 23 January 2026** `[F-20]`:

| Item                     | EPD²                                                              | Guidance                                                                                                                                               | Result                                                        |
| ------------------------ | ----------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------- |
| Security-level target    | ≈128 bits (inference `[F-01]`)                                    | ≥ 120 bits                                                                                                                                             | **meets**                                                     |
| DH in `F_p` modulus      | 4096                                                              | 3000 recommended `[F-21]`                                                                                                                              | **exceeds**                                                   |
| Subgroup order `\|q\|`   | 256                                                               | **250** — TR-02102-1 (2026-01) §2.3.3 p. 34 and §2.3.5 p. 36, read first-hand `[F-36]`; 250 — ECCG `[F-33]`; 256 — German signature catalogue `[F-34]` | **satisfies every located minimum, current edition included** |
| Hash / MAC               | SHA-256 / HMAC-SHA-256, 256-bit                                   | 128 minimum                                                                                                                                            | **meets**                                                     |
| Prime-order subgroup     | yes                                                               | required `[F-21]` §2.3                                                                                                                                 | **meets**                                                     |
| Randomness               | AIS 20/31 v3.0 classes `[F-26]`, SP 800-90A/B/C `[F-27]`…`[F-29]` | —                                                                                                                                                      | **aligned**                                                   |
| Classical-crypto horizon | —                                                                 | end-2031 / end-2030 `[F-25]`                                                                                                                           | **a dated limit, carried as `OD-P16B-06`**                    |

**The subgroup-order check is complete, on the document this decision names,
read first-hand.**

```text
CURRENT BSI SUBGROUP-ORDER CHECK: SATISFIED

BSI TR-02102-1, Version 2026-01, 23 January 2026
  §2.3.3 DLIES, p. 34, "Key Length":
    "The length of the prime number p should be at least 3000 bits.
     The length of the prime q should be at least 250 bits in both cases."
  §2.3.5 Diffie-Hellman Key Agreement, p. 36, "System Parameters", step 2:
    "Choose an element g in F*p with ord(g) prime and q := ord(g) >= 2^250."

EPD² value:   q = 2^256 − 189  —  256 bits
Comparison:   256 >= 250   SATISFIED, 6 bits of margin
              q >= 2^250 · ord(g) prime · |p| = 4096 >= 3000   all SATISFIED
```

> The selected 256-bit subgroup order satisfies the reviewed BSI
> TR-02102-1 Version 2026-01 minimum for this specific parameter dimension.

**Limited to the subgroup-order dimension.** It establishes none of:
complete BSI conformity of `EPD2-CRYPTO-1`; BSI certification; approval for
political-election use; implementation security; side-channel resistance;
protocol-composition security; legal activation.

**How it was read.** The official PDF was supplied locally by the project's
reviewer and read directly — 92 pages, SHA-256
`f601cdf2…9367a62a`, printed folios matching PDF pages. Four earlier rounds
could not obtain it over any network route (`[F-22]`, kept as history). This
decision was closed once on substitute sources and withdrawn, once on an
attestation, and now on the document itself; every step is on the record.

**A figure corrected on reading.** The previously attested minimum of **240**
is a different figure in this document — Table 1.1 (p. 18) uses it as the
ECDSA/ECIES break-even for a 120-bit level, and p. 18 gives it separately as
the minimum hash-digest length. **The subgroup-order minimum is 250**, and
`|q| = 256` satisfies it.

**One divergence, declared.** Remark 2.12 (p. 34) recommends MODP or ffdhe
groups where published parameters are used, with `q = (p−1)/2`.
`EPD2-CRYPTO-1` uses published parameters that are neither, with a 256-bit
prime `q`. The `log₂(p) ≥ 3000` condition is met and §2.3.5 step 2 permits
any `g` of prime order `≥ 2²⁵⁰`, so this is a **recommendation-level
divergence, not a failed requirement** — carried as `VO-08` and `RB-09`, and
constrained by `PS-01`…`PS-04`, since the parameters are fixed upstream and
cannot be swapped without forking every conforming verifier.

**`VO-08` is owned by the PACK-16B external cryptographic review**, with
independent confirmation in **PACK-17** and implementation consequences, if
any, in **PACK-16D**. **It is not PACK-16C's**, which cannot resolve
parameter-family acceptability; PACK-16C inherits it as a constraint and may
not alter or claim approval of the family. **`VO-08` blocks production
implementation acceptance, production activation, legal activation, complete
BSI-conformity claims and final cryptographic assurance**, and does **not**
block completion of this specification round or the drafting of PACK-16C.

**No BSI certification, conformance assessment or legal-compliance claim is
made anywhere in this round.**

---

## Fiat–Shamir model

Strong Fiat–Shamir throughout: every challenge includes the **statement and
the context**, not merely the commitment, in all three proof families
`[F-08]`. This is the direct architectural answer to the weak-Fiat–Shamir
failure class that broke deployed systems `[E-19]`, `[E-22]`.

`FS-01`…`FS-15` fix the construction; `VF-01`…`VF-08` fix what a verifier
must recompute; `TV-06` makes it testable rather than asserted, which is
`KC-23`'s actual requirement.

---

## Domain separation

The 27 upstream tag bytes are adopted exactly `[F-09]`, with the four base
hashes chained `ver → H_P → H_B → H_E → H_I`. EPD²'s own ceremony
constructs hash under a **separate domain**:

```text
H_X = H(H_B; "epd2_ceremony_v1")     — string tags, never a tag byte
```

Two internal inconsistencies in the specification's hash section were found
by this round `[F-19]` and resolved locally — `0x32` keyed to `H_I`; `0x44`
without the spurious `"LOCK"` constant — with `DS-16` deferring to upstream
should it resolve them differently. **These are EPD²'s readings, not
confirmed errata**, and `CA-27` exists because upstream has no errata
process to confirm them through `[F-30]`.

---

## Canonical encoding

Fixed-length big-endian — 512 bytes mod `p`, 32 bytes mod `q`, 4 bytes for
small integers, **no separators** `[F-09]`. `DS-01`…`DS-06` require every
hashed input to be in that form, and **non-canonical input is rejected
rather than normalised** (`IM-06`) — a lenient decoder silently destroys
domain separation, which is why this is a mandatory implementation
criterion and a vector class of its own (`VC-06`).

---

## Randomness architecture

Profile `EPD2-RND-1`. Long-term key material comes from a `PTG.3` source, or
from `DRG.3`/`DRG.4` seeded by `PTG.2`, `PTG.3` or `NTG.1`; **a `PTG.2`
source is never used directly for keys, shares, coefficients or nonces**
`[F-26]`. DRBGs are SP 800-90A Rev 1 mechanisms only `[F-27]`, entropy
sources satisfy SP 800-90B `[F-28]`, and the SP 800-90C construction class
is **recorded in the ceremony transcript** `[F-29]`.

**Fail-closed, with no degraded mode:** a failed health test stops a
ceremony (`FM-16B-05`); a failed client self-test refuses to encrypt and no
ballot is produced (`FM-16B-06`).

The uncomfortable fact is stated rather than buried: **a nonce failure in a
browser is silent, and no verifier can detect it.** Benaloh
cast-or-challenge is a detection mechanism for a malicious client, not for a
weak generator.

---

## Cryptographic agility

Six kinds of agility are separated, and the profile has different answers
for each:

```text
Parameter migration      DOES NOT EXIST in this profile — the values are fixed [F-04]
Algorithm migration      A new profile and a new ADR
Hash migration           Not available without forking the verifier
Encoding migration       Not available
Implementation migration Available, and governed by IM-01…IM-48
Successor construction   OD-P16B-06, dated, not started
```

Governance: the pinned document is authoritative **by digest, not by URL**;
EPD² maintains **its own errata record and advisory intake** because
upstream has neither `[F-30]`; the Election Board approves a profile on a
Cryptographic Reviewer's assessment; **no administrator, operator,
implementer or vendor may change a parameter, ever.**

**Downgrade is prohibited architecturally** — there is no negotiation to
lose, because there is no negotiation.

---

## Guardian count

```text
DEFAULT           n = 5
HIGH ASSURANCE    n = 7
Bounds            n ≥ 5, n ≤ 9, and n ≥ k + 2 always
```

Upstream constrains only `1 ≤ k ≤ n` `[F-18]` — which admits `k = 1`, a
single-administrator decryption — so the real bound is EPD²'s.

---

## Quorum

```text
DEFAULT           k = 3   (3-of-5)      absence tolerance n − k = 2
HIGH ASSURANCE    k = 4   (4-of-7)      absence tolerance 3
PERMITTED         k = 5   (5-of-9)
PROHIBITED        k = 2   (2-of-3) — two people are not a threshold in a party context
```

Four configurations were compared on collusion cost, loss survivability,
recruitment burden and ceremony logistics. **`k` may never be reduced, and
`n` may never fall below `k + 2`, at any time, for any reason, by any
authority** (`GQ-05`). The Election Officer cannot lower a quorum
(`RS-16B-12`); the Election Board cannot reconstruct a secret (`GQ-13`,
`RS-16B-13`).

---

## Guardian independence

Independence is **factual, not formal**: fifteen pairwise tests, classified
hard (disqualifying) or soft (assessed and published), plus composition
tests over the set as a whole. At most `k − 1` guardians may be Election
Officers or Board members in total (`GQ-11`), so **any collusion reaching
`k` must include someone outside EPD²'s own operations.**

```text
An HSM does not convert one administrator into a threshold.
If one operator, one cluster, one provider or one policy engine
can produce k decryption shares, the architecture FAILS.
```

Two guardians in one cloud tenant are one guardian. Two guardians in two
tenants of the same provider share a provider, and that is the row of the
collusion matrix that produces a quorum with no guardian's participation.

---

## Key ceremony

Twenty phases, from profile approval to the activation lock, each with entry
and exit conditions, published evidence and a named accountable role.

**One EPD² addition, and the reason for it.** The specification's DKG omits
Pedersen's commit-then-open round. GJKR shows that a party acting last can
then bias the joint public key — a chosen predicate with probability 3/4
rather than 1/2 `[F-15]`. The same specification deploys exactly the right
countermeasure — a hash pre-commitment before opening — **in its decryption
protocol and not in key generation** `[F-16]`. EPD² therefore adds a
pre-publication commitment round (`KY-07`…`KY-12`) using the document's own
pattern, at the orchestration layer, changing no hash input.

**This is claimed as a mitigation of an analogous exposure, not as a fix**,
and `TV-08` must assess it. `F-32` — Pedersen-DKG bias is provably
survivable for some DL-based schemes at the cost of a larger modulus — is
the counterweight, and it says _some schemes_, not _this scheme_.

---

## Complaint handling

The specification's entire treatment of misbehaviour is: abort, investigate
**out of band**, restart from scratch `[F-12]`. That is not a protocol — it
names no roles, no deadlines, no evidence standard and no adjudicator.

EPD² specifies one: eleven grounds, **seven of them publicly checkable by
arithmetic**, signed complaints published before adjudication, a respondent
deadline, and **no administrator may mark a complaint resolved** (`CD-08`).
Where a ground is arithmetic, there is no discretion (`CD-09`).

The one ground that cannot be settled arithmetically — contradictory
sender/recipient claims about a share — is resolved by opening **one** share
under Board order with Auditor concurrence, from a key set that is discarded
immediately afterwards. The specification's broader suggestion that _all_
guardians release _all_ secret information `[F-12]` is **prohibited**: it is
a quorum-equivalent disclosure. A construction making this publicly
adjudicable without disclosure would be better, does not exist here, and is
`OD-P16B-04` rather than an invention.

---

## Key custody

Permitted: dedicated software-only devices, hardware-backed dedicated
devices, smart cards, HSMs one-guardian-per-module, air-gapped ceremony
devices. **Refused: general-purpose cloud KMS, consumer hardware wallets,
paper or mnemonic backup, and any share on a device that also reads email.**

Only `z_i` and `ẑ_i` survive the ceremony `[F-13]`; `GL-16` requires
everything else destroyed. That shrinks what custody must protect to one
32-byte value per key set per guardian.

**Custody makes a share hard to take and does nothing about a share being
given.** That is why `k ≥ 3`, why `GQ-11` forces an external participant
into any collusion, and why guardian identity is public.

---

## Backup and recovery

```text
PERMITTED    one encrypted backup, of a guardian's OWN share,
             in that guardian's OWN sole custody, on a second dedicated medium
PROHIBITED   split custody · hardware duplication · escrow · central backup ·
             cloud backup · shared passphrase · vendor master key ·
             any "sealed envelope in a safe"
```

The backup **does not change the threshold**: one share backed up is still
one share, the number of parties who can reach any share is unchanged, and
so the number who must collude to reach `k` is unchanged. That is exactly
what `KC-14` asks. The trade is that the guardian's own exposure grows from
one medium to two, borne by the person who chose it, in exchange for a
device failure no longer costing the election a guardian.

**No backup is mandatory**, and its absence is not a defect.

---

## Compensated decryption

**It does not exist in the pinned specification version.**

The word does not appear in 2.1; the mechanism belonged to the 1.x lineage.
What 2.1 does is compute partial decryptions over the available set `U` with
`|U| = h ≥ k`, and it explicitly refuses to reconstruct an absent guardian's
secret: _"it is preferable to not release any missing secret … and instead
only release the partial decryptions that the secret would have produced.
This prevents the secret from being used for additional decryptions without
the cooperation of at least `k` guardians."_ `[F-11]`

**That is `KC-15`'s policy, arrived at independently by the specification's
authors.**

Consequently: no compensation material is created, stored, authenticated or
retained; absence tolerance is **exactly `n − k`**; and the round task's
rule — compensation may restore availability within the approved threshold
but may not create a new one — is satisfied **vacuously**.

**This is a factual correction to PACK-16A `KC-11`'s described mechanism.
The requirement is unchanged.** A construction with no compensation material
cannot drift; one with it has five places where the effective threshold can
move without anyone deciding that it should.

---

## Compromise handling

Nine severity classes, and secrecy and integrity claims are never collapsed
into one: a compromised guardian can break confidentiality within a quorum
and cannot forge a tally.

**Outcomes are bounded by activation state, not by preference:**

```text
Pre-activation      restart the ceremony without that guardian
Post-activation     annul the context — the ballots are never decrypted
```

Suspicion pauses participation and is **published within 24 hours with its
class**; confirmation is the Election Board's alone, with Auditor
concurrence. The Incident Commander — the role most likely to be asked —
**cannot authorise decryption, direct a guardian, alter a quorum or order a
ceremony to proceed** (`RS-16B-11`).

---

## Quorum-loss handling

Below `k` available guardians, **the result is unobtainable**. Declaration
follows a documented recovery attempt, a published waiting period and
contact with every guardian; the context is annulled and participants are
told the result cannot be produced; a re-run is a **new** context with new
keys; and the annulled context's ballots are **never decrypted, by anyone,
ever** — including after the re-run.

```text
An unrecoverable election is preferable to a recoverable secret.
```

What that costs when it bites is stated and not minimised: everyone who
voted in that context voted for nothing and must vote again. What reduces
the cost honestly is `n − k = 2`, per-guardian backup, and publishing the
margin when it reaches 1 (`IN-12`) rather than when it reaches 0.

---

## No-break-glass rule

```text
There is no break-glass decryption.
There is no emergency quorum.
There is no administrative, judicial, incident or vendor path
   that produces a plaintext ballot.
The Election Board decides everything and possesses nothing.
```

This is enforced by **absence**, which is stronger than any check: a check
can be bypassed by whoever operates it; an operation that was never
specified has to be added, in public, against `BR-09`, `GQ-13` and `CM-18`.
Discovery that such a capability exists is `FM-16B-22` — activation blocked,
or annulment, with a published finding naming the capability and how it came
to exist.

---

## Pre-closure prohibition

**No operation exists that produces a decryption share before the context
reaches `voting_closed`** (`CM-20`). An attempt is `FM-16B-25` — abort and
annul — because the attempt is evidence of either a defect or an intent, and
both disqualify the context.

The specification's own pre-decryption gating — every guardian confirming
the ballot-set verifications before any key material is applied `[F-11]` —
is adopted as a requirement rather than an option. Readiness checks are
permitted, and use **test keys and synthetic ciphertexts only**; a readiness
check that requires a production ciphertext is not a readiness check.

---

## Remote-ceremony decision

```text
FULLY IN-PERSON        permitted
CONTROLLED HYBRID      permitted  ← the expected form
FULLY REMOTE           PROHIBITED
```

Four grounds, of which the fourth decides it: device trust is unverifiable
remotely; the faults that most need a witness leave no cryptographic trace;
guardian coercion is unaddressed — _"if the coercer can monitor the voter
throughout the vote casting period, then resistance is futile"_ `[E-46]`
applies equally to a guardian alone with a device; and **no evidence
base was located** `[F-31]` — an absence of evidence, which is not evidence
of absence, and which is why the answer is "not yet" rather than "never".

**Fully remote is prohibited because the evidence to permit it does not
exist**, not because it is impossible. `RCA` §5 states the four conditions
that would change the answer, carried as `OD-P16B-05`. The defining control
of the permitted hybrid form is that **no guardian is ever alone with their
device during a session** (`RC-03`), and the decryption ceremony is held
under the same form or a stricter one (`RC-15`).

---

## Implementation requirements

`OD-P16A-04` is **not closed**; it is given a standard. Mandatory criteria
(failure = rejection, with no aggregate that overrides): bit-exact upstream
vector reproduction, parameter reproduction, exact canonical encoding with
rejection of non-canonical input, exact `H`/`H_q`/tag implementation,
mandatory group-membership validation, constant-time secret-dependent
operations, zeroisation, and **no secret in logs, exceptions, telemetry,
dumps, URLs or browser storage** — plus reproducible builds, pinned
dependency provenance and no network access from the ceremony application.

**The browser/native boundary is categorical:**

```text
Ballot encryption, proofs, challenge  →  browser PERMITTED
Any guardian secret material          →  browser PROHIBITED, always
The independent verifier              →  must exist outside a browser
```

**Performance may not be the reason for a cryptographic choice**, and FIPS
validation is evidence rather than a verdict — and specifically is not
evidence of BSI compatibility.

---

## Formal-review requirements

`TV-01`…`TV-08`, fourteen vector classes, and a property-by-method
assurance mapping. `TV-01`…`TV-06` are things EPD² can do to itself;
**`TV-07` (independent implementation) and `TV-08` (external cryptographic
review) are not**, and they are the two that matter.

**`OD-P16A-06` is NOT closed and is recorded as `blocked pending
cryptographic review`.** Its deliverable is named — an external written
review covering the parameter profile, the Fiat–Shamir construction as EPD²
uses it, the upstream DKG and threshold decryption, **the two EPD²
additions**, and the randomness architecture, published in full including
findings EPD² did not act on. What does not count is enumerated: an internal
review, a review by the implementation's authors, a FIPS or Common Criteria
certificate, a vendor assurance, or this document.

**Activation of any binding context is blocked until that review exists and
its blocking findings are closed.**

---

## Rejected alternatives

| Alternative                                            | Rejected because                                                                                                        |
| ------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------- |
| Different finite-field parameters                      | Forks every conforming verifier `[F-05]`; `H_q` needs redesign `[F-07]`                                                 |
| An elliptic-curve adaptation                           | A protocol adaptation, not a parameter change; outside BSI's recommended set `[F-23]`; proofs need re-derivation        |
| A post-quantum construction now                        | A different protocol; guidance says quantum-safe mechanisms are not yet trusted equally `[F-25]`. Dated as `OD-P16B-06` |
| `k = 2` of 3                                           | Two people are not a threshold for a binding party vote                                                                 |
| `n > 9`                                                | Ceremony logistics and recruitment make it unworkable for the organisations that will actually run it                   |
| Split-custody backup under independent custodians      | An escrow with extra steps — it reduces the effective threshold                                                         |
| Hardware-token duplication                             | Two places to steal one share                                                                                           |
| Escrowed recovery shares                               | The escrow holder is a shadow quorum                                                                                    |
| Reintroducing compensated decryption                   | It does not exist in 2.1, and its absence removes a drift surface `[F-11]`                                              |
| A break-glass decryption under Board or judicial order | A mechanism that can produce a result without a quorum can produce a result without an election                         |
| Fully remote ceremonies                                | No evidence base **located** `[F-31]`; coercion unaddressed `[E-46]`; device trust unverifiable                         |
| Cloud KMS custody                                      | Two guardians in one tenant are one guardian                                                                            |
| Consumer hardware wallets                              | Solves extraction and nothing else; no verifiable attestation                                                           |
| Making the ceremony transcript a `PublicLedgerEntry`   | Imports a trust model the transcript deliberately does not have                                                         |
| Proposing PACK-16A's `CA-02` amendment now             | This round's finding is that the transcript should **not** be a canonical aggregate; the right amendment is smaller     |

---

## Residual risks

| ID      | Risk                                                                                                                                                                                                                                                                                                                                                                                                                                    | Rating   | Carried by                                       |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- | ------------------------------------------------ |
| `RB-09` | **Published parameter family normative divergence** — `EPD2-CRYPTO-1` uses the ElectionGuard 2.1 family rather than a MODP or ffdhe family preferred by Remark 2.12. **The numerical conditions are satisfied**; the residual is normative acceptability, provenance reviewability, and the consequences of retaining or replacing the family. **Not a claim that the parameters are insecure.** Blocks production and legal activation | medium   | `VO-08` — external cryptographic review, PACK-17 |
| `RB-02` | The classical-cryptography recommendation lapses end-2031 / end-2030                                                                                                                                                                                                                                                                                                                                                                    | **high** | `OD-P16B-06`, `CA-08`                            |
| `RB-05` | Two specification inconsistencies resolved on EPD²'s own reading `[F-19]`                                                                                                                                                                                                                                                                                                                                                               | low      | `DS-16`, `CA-27`                                 |
| `RB-06` | Upstream has no errata process and marks two versions "Recommended" `[F-30]`                                                                                                                                                                                                                                                                                                                                                            | medium   | `CA-19`…`CA-27`                                  |
| `RR-01` | **No production-grade implementation of the pinned version exists**                                                                                                                                                                                                                                                                                                                                                                     | **high** | `OD-P16A-04`, `OD-P16B-02`                       |
| `RR-09` | **No peer-reviewed analysis of the key ceremony was located by this round** `[F-31]`                                                                                                                                                                                                                                                                                                                                                    | **high** | `TV-08`, `OD-P16A-06`                            |
| —       | A silent nonce failure in a browser is undetectable by any verifier                                                                                                                                                                                                                                                                                                                                                                     | medium   | `IM-43`, PACK-16D                                |
| —       | Guardian volunteers bear real personal exposure through publication                                                                                                                                                                                                                                                                                                                                                                     | medium   | GOVERNANCE                                       |
| —       | Independence declarations are self-reported                                                                                                                                                                                                                                                                                                                                                                                             | medium   | `GI-*`, GOVERNANCE                               |
| —       | A quorum loss makes a result genuinely unobtainable                                                                                                                                                                                                                                                                                                                                                                                     | accepted | `CM-14`…`CM-19`                                  |

---

## Open decisions

**Closed by this ADR:** `OD-P16A-03` (parameters vs. German guidance),
`OD-P16A-05` (stewardship), and the **cryptographic boundary** of
`OD-P15-05` (`IS-01`…`IS-06`), whose construction question is reassigned to
PACK-16C.

**Opened, and one since closed:** `OD-P16B-01` (the finite-field
subgroup-order minimum — **closed by primary-source evidence, read
first-hand**: `256 ≥ 250` against TR-02102-1 (2026-01) §2.3.3 p. 34 and
§2.3.5 p. 36 `[F-36]`, with one recommendation-level divergence carried as
`VO-08`, owned by the external cryptographic review and PACK-17, which
blocks production and legal activation), `OD-P16B-02` (whether EPD² may write its own implementation — blocks
implementation), `OD-P16B-03` (the Cryptographic Reviewer's standing),
`OD-P16B-04` (publicly checkable share correctness), `OD-P16B-05` (remote
ceremony), `OD-P16B-06` (the post-quantum successor — **blocks new contexts
after 2030-12-31**).

**Contributed to, not closed:** `OD-P16A-04`, `OD-P16A-06`, `OD-P16A-07`,
`OD-P16A-08`, `OD-P16A-11`, `OD-P16A-12`.

```text
Three independent activation blocks remain open — OD-P16A-04,
OD-P16A-06 and OD-P16A-11 — plus the dated OD-P16B-06 and the
open validation obligations VO-02…VO-05.
None is closed by assertion. OD-P16B-01 was closed once on
substitute sources, withdrawn, closed again on an attestation,
and finally closed on the document itself, read first-hand.
```

---

## Consequences for PACK-16C

- The joint public key, its evidence and the parameter-set identifier are
  **inputs** to the bulletin board and the casting service; the board
  consumes them and produces none of them.
- **No ballot may be encrypted before `joint_key.published`** (`IN-11`).
- **No decryption operation may exist before `voting_closed`** — PACK-16C
  must not create one, even for a readiness check.
- The board is still **not** a `PublicLedgerEntry`; `CAM-P16B-01` is the
  narrow canonical reference PACK-16C should propose if it proposes
  anything.
- `OD-P15-05`'s construction question and `OD-P16B-04` land here.
- `VO-02` and `VO-03` — the remaining BSI first-hand readings — are
  PACK-16C's to discharge and still block activation. `VO-01`, `VO-06` and
  `VO-07` are satisfied. **`VO-08` is not PACK-16C's** — it belongs to the
  external cryptographic review and PACK-17; PACK-16C inherits it as a
  constraint and may not alter or claim approval of the parameter family.

## Consequences for PACK-16D

- `OD-P16A-04` is decided against `IM-01`…`IM-48`, and the assessment is
  published with its evidence including the criteria the chosen candidate
  fails.
- `TV-01`…`TV-07` and the fourteen vector classes are deliverables, not
  aspirations.
- **No guardian secret material in a browser context**, categorically.
- Reproducible build, pinned provenance and no ceremony network access are
  mandatory, not preferred.
- `OD-P16B-02` must be answered before the implementation track opens.
- `OD-P16A-12`'s repository-compatibility bound arrives here.

## Consequences for PACK-17

- Ceremony rehearsal, incident runbooks and archive re-verification
  operations (`FM-16B-33`, `archive_verification.*`).
- `VC-14` historical-verification: a complete archived context re-verified
  from published material alone, by someone with no access to EPD² systems.
- `OD-P16B-05` — after two completed controlled-hybrid ceremonies with
  published transcripts and Auditor verdicts, the remote question can be
  reopened on evidence.

---

## Canon assessment

```text
CANON CLARIFICATION REQUIRED
CANON_VERSION REMAINS 0.8.0
NO CANON CHANGE MADE
```

Five clarifications (`CQ-P16B-01`…`05`). The ceremony transcript is
**not** a canonical aggregate and **not** a `PublicLedgerEntry`: its
integrity comes from independent recomputation and cross-location
comparison, not from the system's own chain, and canonising it would place
the ceremony's evidence inside the system the ceremony exists to constrain.
The `PublicLedgerEntry → VoteEnvelope` prohibition is untouched and
reinforced from the ceremony side.

Three amendment candidates are **recorded, not proposed**
(`CAM-P16B-01`…`03`), and PACK-16A's `CA-02` is **narrowed rather than
discharged**.

---

## FIR impact

```text
FIR entries marked implemented          0
FIR entries created                     0
FIR entries removed or downgraded       0
FIR statuses changed                    0
Register copies in the archive          1
```

`FIR-ROADMAP-006` stays `approved` and moves to **selected for
architectural review**. `FIR-INV-002` is **not closed and cannot be by this
round.** `FIR-UX-011`, `FIR-OSS-001`…`006`, `FIR-INV-002`, `FIR-INV-008`,
`FIR-INV-015` and `FIR-ROADMAP-006` are preserved unchanged.

`FIR-INV-005` (no intermediate tally), `FIR-INV-009` (no break-glass) and
`FIR-INV-014` (no universal administration) are strengthened structurally
rather than procedurally.

---

## Status of this decision

```text
PROPOSED. NOT ACCEPTED.
SPECIFICATION AND ADR ONLY. NO CODE. NO CRYPTOGRAPHIC CODE.
EXTERNAL ARCHITECTURAL REVIEW REQUIRED.
EXTERNAL CRYPTOGRAPHIC REVIEW REQUIRED BEFORE ANY ACTIVATION.
NOT A FINAL PASS. NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.
PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.
PACK-16C MUST NOT START BEFORE ACCEPTANCE.
```
