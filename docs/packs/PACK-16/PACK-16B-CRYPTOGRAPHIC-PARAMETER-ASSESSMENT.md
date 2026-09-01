# PACK-16B — Cryptographic Parameter Assessment

**Round:** PACK-16B — Cryptographic Parameters, Key Ceremony and Trustee Architecture. **Specification and ADR only. No code. No cryptographic code. Not implemented. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-100`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

Evidence `[F-nn]` resolves in `PACK-16B-PROTOCOL-EVIDENCE-MATRIX.md`.

---

## 1. What is being assessed

The ElectionGuard 2.1.0 standard baseline parameters, as the candidate
cryptographic foundation of `EPD2-HOM-1`.

| Item               | Value                                                                                                                               |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------------------- |
| Subgroup order `q` | `2²⁵⁶ − 189` — the largest prime below 2²⁵⁶ `[F-01]`                                                                                |
| Modulus `p`        | 4096 bits, first and last 256 bits all ones, middle 3584 bits from the binary expansion of ln(2) plus a printed offset `δ` `[F-02]` |
| Cofactor `r`       | `(p − 1)/q`, with `r/2` required prime `[F-02]`                                                                                     |
| Generator `g`      | `2^r mod p` — an `r`-th residue, generating the order-`q` subgroup `Z_p^r` `[F-02]`                                                 |
| Hash function `H`  | **HMAC-SHA-256**, used as a random oracle with a fixed 32-byte key slot `[F-06]`                                                    |
| Reduction to `Z_q` | `H_q(B₀,B₁) = H(B₀,B₁) mod q`, valid because `q` is within `189/2²⁵⁶` of `2²⁵⁶` `[F-07]`                                            |
| Encoding           | Fixed-length big-endian: 512 bytes mod `p`, 32 bytes mod `q`, 4 bytes for small integers `[F-09]`                                   |
| KDF                | NIST SP 800-108r1 counter-mode HMAC, for share and nonce encryption `[F-10]`                                                        |

The specification pinned for this assessment:

```text
ElectionGuard Design Specification, Version 2.1.0
Josh Benaloh, Michael Naehrig, Olivier Pereira — Microsoft Research
Title page: "Version 2.1.0 / August 12, 2024"
110 pages · 813 495 bytes
SHA-256 a263ab3cd2cf28f05de324ecd2d9752ffed45f814709582b4c2bb23d1826b936
```

---

## 2. Are alternative parameters even possible? — the decisive constraint

This question had to be answered before any comparison, and the answer
removes most of the design space.

The specification says three things that must be read together `[F-04]`:

1. _"Alternative parameter sets are possible and may be allowed in future
   versions of ElectionGuard."_
2. A conditional footnote listing what a verifier would have to check _if_
   alternative parameters were allowed.
3. **Note 3.1, which is the operative rule:** _"Allowing alternate
   non-standard parameters would force election verifiers to recognize and
   check that parameters are correctly generated… allowing such parameters
   would add substantial complexity to election verifiers. **For this
   reason, this version of ElectionGuard fixes the parameters as above.**"_

And Verification 1 requires bit-equality with the printed constants —
**1.B** the large prime, **1.C** the small prime, **1.D** the generator —
and states that they _"may be hardcoded"_ `[F-05]`.

**Consequence.** In version 2.1 the parameters are **fixed, not
negotiable**. A conforming verifier rejects anything else — including the
3072-bit alternative printed in the specification's own appendix `[F-04]`.
Any EPD² parameter change is therefore not a configuration choice but a
**fork of the verifier ecosystem**, which directly attacks `BM-28` (an
independent verifier not written by EPD²) and `BB-33`.

This is also, incidentally, the strongest anti-downgrade property available
anywhere in this architecture: **a protocol with no parameter negotiation
has no downgrade surface to defend.**

---

## 3. Assessment against German guidance

Reference: **BSI TR-02102-1, "Cryptographic Mechanisms: Recommendations and
Key Lengths", Version 2026-01, published 23 January 2026** `[F-20]`.

### 3.1 What is verified

| BSI statement                                                                                                                                                                      | Source                     | EPD² relevance                                                                                     |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------- | -------------------------------------------------------------------------------------------------- |
| _"all cryptographic mechanisms specified in this Technical Guideline achieve a security level of **at least 120 bits**"_                                                           | Ch. 1 `[F-20]`             | The target to meet                                                                                 |
| _"The information provided in this Technical Guideline is therefore only limited to a period **until the end of 2032**."_                                                          | Ch. 1 `[F-20]`             | The guidance's own horizon                                                                         |
| **Table 1.2** recommended key lengths: **DH in F_p 3000 bits**; ECDH/ECDSA 250; MAC 128; block cipher 128                                                                          | Table 1.2 `[F-21]`         | `p` = 4096 ≥ 3000 ✓                                                                                |
| **Table 2.2**: DLIES 3000, DH 3000, ECIES 250, ECDH 250 — each **"Recommended until 2031"**                                                                                        | Table 2.2 `[F-21]`         | The deprecation date (§5)                                                                          |
| **Table 1.1** (p. 18) key lengths at which a 120-bit level _"is just achieved"_: DSA/DLIES 2800; ECDSA/ECIES **240**                                                               | Table 1.1 `[F-21]`         | A break-even illustration, **not the subgroup-order minimum** — that is 250, §2.3.3 p. 34 `[F-36]` |
| *"it is assumed that no mechanism exists to solve the Diffie-Hellman problem in a subgroup U ⊂ F*p with ord(U) prime more efficiently than by computing discrete logarithms in U"* | §2.3 `[F-21]`              | Confirms the prime-order-subgroup framing                                                          |
| **§2.3.3, p. 34:** _"The length of the prime number p should be at least 3000 bits. The length of the prime q should be at least 250 bits in both cases."_                         | §2.3.3 p. 34 `[F-36]`      | **The operative requirement** — `\|q\|` = 256 ≥ 250 ✓, `\|p\|` = 4096 ≥ 3000 ✓                     |
| **§2.3.5, p. 36:** _"Choose an element g ∈ F∗p with ord(g) prime and q := ord(g) ≥ 2²⁵⁰."_                                                                                         | §2.3.5 p. 36 `[F-36]`      | `q = 2²⁵⁶ − 189 ≥ 2²⁵⁰` ✓ and `ord(g)` prime ✓                                                     |
| **Remark 2.12, p. 34:** published parameters — _"recommends using the MODP groups … or the ffdhe groups"_, `q = (p−1)/2`, common `p` only when `log₂(p) ≥ 3000`                    | Remark 2.12 p. 34 `[F-36]` | **A declared divergence** — §3.2.4, `VO-08`                                                        |
| Classical key agreement recommended **only until end of 2031**; **end of 2030** for very high protection; classical signatures until **end of 2035**                               | Ch. 2 `[F-25]`             | §5                                                                                                 |
| Quantum-safe mechanisms are to be used **in hybrid combination** with classical ones, because they are _"generally not yet trusted to the same extent"_                            | §2.2 `[F-25]`              | The successor-profile obligation                                                                   |

### 3.2 The subgroup-order check — completed against the official document

```text
CURRENT BSI SUBGROUP-ORDER CHECK:
SATISFIED

BSI TR-02102-1, Version 2026-01, 23 January 2026
  §2.3.3 DLIES Encryption Scheme, page 34, "Key Length":
    "The length of the prime number p should be at least 3000 bits.
     The length of the prime q should be at least 250 bits in both cases."

  §2.3.5 Diffie-Hellman Key Agreement, page 36, "System Parameters", step 2:
    "Choose an element g in F*p with ord(g) prime and q := ord(g) >= 2^250."

  §2.3.5, page 36, "Key Length":
    "The length of p should be at least 3000 bits."

BSI minimum:            subgroup order at least 250 bits
EPD² selected value:    q = 2^256 − 189   —   256 bits
Comparison:             256 >= 250        SATISFIED, 6 bits of margin
                        q >= 2^250        SATISFIED
                        ord(g) prime      SATISFIED
                        |p| = 4096 >= 3000  SATISFIED
```

> The selected 256-bit subgroup order satisfies the reviewed BSI
> TR-02102-1 Version 2026-01 minimum for this specific parameter dimension.

**This conclusion is limited to the subgroup-order dimension. It does not
establish:**

```text
- complete BSI conformity of EPD2-CRYPTO-1;
- BSI certification;
- approval for political-election use;
- implementation security;
- side-channel resistance;
- protocol-composition security;
- legal activation.
```

#### 3.2.1 The document, and how it was read

The official PDF was **supplied locally to EPD² by the project's reviewer
and read directly** — 92 pages, title page _"Version: 2026-01"_, _"As of:
January 23, 2026"_, file SHA-256
`f601cdf25c000b431573a307a3c125f3c51d301897089e7e63dde0449367a62a`. The
citations above are page numbers in that file; **the printed folios match
the PDF page numbers**, so §2.3.3 is p. 34 in both and §2.3.5 is p. 36 in
both.

Four earlier rounds could not obtain the document over any network route
available here — `[F-22]` keeps that log as history. **The limitation was
resolved by supplying the file directly, not by working around it**, and
`[F-36]` is now a first-hand reading rather than an attestation.

#### 3.2.2 A figure corrected on reading: 250, not 240

An earlier round recorded the requirement as **240 bits**, on an attestation
that could not then be checked. **Reading the document shows that 240 is a
different figure in it:**

| Where 240 actually appears | What it is                                                                                                                       |
| -------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| **Table 1.1, p. 18**       | The **ECDSA/ECIES** key length at which a 120-bit security level _"is just achieved"_ — a break-even illustration, not a minimum |
| **p. 18, narrative**       | The general minimum **hash digest** length for the guideline's security level                                                    |

**Neither is the finite-field subgroup-order minimum, which is 250.** The
figure is corrected everywhere in this pack. **The conclusion is unchanged:**
`|q| = 256` satisfies 250 with 6 bits of margin, as it satisfied every other
located figure.

#### 3.2.3 Corroboration from the same document, read first-hand

| Location              | Figure                                                                                                                                                       |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Table 1.2, p. 19**  | Block cipher 128 · MAC 128 · RSA 3000 · **DH F_p 3000** · ECDH 250 · ECDSA 250                                                                               |
| **Table 2.2, p. 33**  | RSA 3000 · DLIES 3000 · ECIES 250 · **DH 3000** · ECDH 250 — each _"Recommended until 2031"_                                                                 |
| **§2.3 introduction** | Sole use of these classical mechanisms is _"only recommended until the end of 2031"_; beyond 2031 only combined with a quantum-safe KEM and a key derivation |
| **Ch. 1**             | _"all cryptographic mechanisms specified in this Technical Guideline achieve a security level of at least 120 bits"_                                         |

The external sources recorded earlier remain in the registry as
corroboration and are now clearly subordinate to the direct primary source:
ECCG `log₂(q) ≥ 250` `[F-33]`, BSI 2025-01 Table 1.2 `[F-35]`, the German
signature catalogue `[F-34]`. **All four agree with the 250 figure or exceed
it, and `|q| = 256` satisfies every one.**

#### 3.2.4 One divergence found on reading, recorded rather than glossed

**Remark 2.12, p. 34** states that where published parameters are used, the
guideline _"recommends using the MODP groups from [78] or the ffdhe groups
from [60]"_, in which _"q = (p − 1)/2 and g = 2"_, and that a common `p` is
recommended _"only when log₂(p) ≥ 3000"_.

```text
EPD2-CRYPTO-1 uses published parameters that are NEITHER MODP NOR ffdhe,
and its q is a 256-bit prime rather than (p − 1)/2.
The log2(p) >= 3000 condition IS met: |p| = 4096.
```

**What this is, and what it is not.** §2.3.5 step 2 explicitly permits any
`g` of prime order `q ≥ 2²⁵⁰` in `F*p` — the small-prime-order-subgroup
shape `EPD2-CRYPTO-1` uses is the shape that section describes. The
divergence is from a **recommendation about which published family to
prefer**, not from a stated requirement, and the stated key-length
conditions are all met.

**It is nonetheless a divergence, and this round does not hide it.** It is
carried as `VO-08` and `RB-09`, and it interacts with `PS-01`…`PS-04`: the
parameters are fixed upstream and EPD² cannot switch to a MODP or ffdhe
group without forking every conforming verifier (`[F-04]`, `[F-05]`).

**Who owns it, and who does not.** The question is whether retaining the
ElectionGuard 2.1 published parameter family is normatively acceptable
despite a BSI preference. That is a **cryptographic and standards
judgement**, not a casting-and-verification question, so it belongs to the
**PACK-16B external cryptographic review**, with independent confirmation in
**PACK-17** and any implementation consequences in **PACK-16D**. **It is not
owned by PACK-16C**, which specifies casting, receipts, the verification
client and the bulletin board and cannot resolve parameter-family
acceptability. PACK-16C inherits `VO-08` as a constraint and may not alter
or claim approval of the parameter family.

#### 3.2.4.1 `VO-08` — stated in full

```text
VO-08 — ElectionGuard 2.1 published parameter family
        versus BSI TR-02102-1 Remark 2.12 preference

FINDING
  EPD2-CRYPTO-1 satisfies the reviewed numerical BSI requirements for
  p, q and prime subgroup order:
      |p| = 4096 >= 3000 · |q| = 256 >= 250 · ord(g) prime
  However, the selected published parameter family is neither an RFC
  MODP group nor an RFC ffdhe group of the type preferred in Remark 2.12.

REQUIRED WORK
  An independent cryptographic review must assess the security, standards
  implications and normative acceptability of retaining the ElectionGuard
  2.1 published parameter family despite this BSI preference.

OWNER
  Primary owner:               PACK-16B external cryptographic review
  Independent assurance:       PACK-17
  Implementation consequences: PACK-16D, if any
  NOT owned by:                PACK-16C

STATUS
  OPEN

SPECIFICATION-STAGE EFFECT
  Does not require changing EPD2-CRYPTO-1 at this stage.
  Non-blocking for completion of the PACK-16B specification review.
  Non-blocking for drafting the PACK-16C specification, provided
  PACK-16C does not alter or claim approval of the parameter family.

BLOCKS
  production implementation acceptance
  production election activation
  legal activation
  complete BSI-conformity claims
  final cryptographic assurance
```

#### 3.2.5 Disposition

| ID           | Disposition                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| ------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `OD-P16B-01` | **CLOSED BY PRIMARY-SOURCE EVIDENCE** — read first-hand, subgroup-order dimension                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| `VO-01`      | **SATISFIED** — the document was read and the minimum recorded                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| `VO-06`      | **SATISFIED BY PRIMARY-SOURCE REVIEW**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `VO-07`      | **SATISFIED** — exact chapter, subsections, pages and verbatim wording are recorded in `[F-36]` and above                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| `VO-08`      | **NEW and OPEN.** Assess the normative acceptability of retaining the ElectionGuard 2.1 published parameter family despite Remark 2.12. **Primary owner: PACK-16B external cryptographic review** · **Independent assurance: PACK-17** · implementation consequences, if any: PACK-16D · **not owned by PACK-16C**. **Non-blocking for PACK-16B review and for PACK-16C drafting; BLOCKS production implementation acceptance, production and legal activation, complete BSI-conformity claims and final cryptographic assurance** — §3.2.4.1 |
| `RB-01`      | **CLOSED** — the check is complete and its citation is exact                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| `RB-09`      | **NEW** — the Remark 2.12 divergence                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |

**Unchanged and still open:** `VO-02`, `VO-03`, `VO-04`, `VO-05`,
`OD-P16A-06` / `TV-08` (external cryptographic review), `TV-07` / `TV-11` /
`TV-19` (independent verifier testing), `OD-P16A-04` (implementation
selection), side-channel assessment, certification assessment,
`OD-P16A-11` (legal assessment).

**`BSI CERTIFIED`, `BSI COMPLIANT` and `FULL BSI COMPATIBILITY` remain
prohibited claims and are made nowhere in this pack.**

### 3.3 Verdict against German guidance

```text
BSI COMPATIBILITY VERDICT — EPD2-CRYPTO-1

Modulus p = 4096 bits           ≥ 3000 recommended         PASS (verified)
Subgroup order q = 256 bits     ≥ 240 break-even           PASS (verified)
                                ≥ 250 recommendation       PASS (verified)
                                ≥ 250 ECCG FF-DLOG agreed  PASS (verified, [F-33])
                                ≥ 256 German signature
                                       algorithm catalogue PASS (verified, [F-34])
                                TR-02102-1 2026-01 §2.3.3 p.34
                                  and §2.3.5 p.36:
                                       q ≥ 250 bits        PASS (read, [F-36])
Hash SHA-256 within HMAC        ≥ 256-bit digest set       PASS (verified: the
                                                           recommended set has a
                                                           minimum length of 256)
Security level                  ≥ 120 bits targeted        PASS by inference — see §4
Recommended until                                          END OF 2031
Very-high-protection migration                             BY END OF 2030

OVERALL: COMPATIBLE WITH EVERY KEY-LENGTH RECOMMENDATION LOCATED,
         READ OR ATTESTED, WITH A DATED CLIFF.
         THE SUBGROUP-ORDER CHECK AGAINST THE CURRENT EDITION IS
         COMPLETE AND EXACTLY CITED. ONE RECOMMENDATION-LEVEL
         DIVERGENCE IS RECORDED (Remark 2.12 — VO-08), WHICH BLOCKS
         PRODUCTION AND LEGAL ACTIVATION AND ANY COMPLETE-CONFORMITY
         CLAIM, AND IS OWNED BY THE EXTERNAL CRYPTOGRAPHIC REVIEW.
         NOT CERTIFIED. NOT ASSESSED BY BSI. NOT ASSESSED BY ANY
         CRYPTOGRAPHIC REVIEWER.
         COMPLETE BSI CONFORMITY OF THE COMPOSED VOTING PROFILE
         IS NEITHER ESTABLISHED NOR CLAIMED.
```

**`BSI CERTIFIED` remains a prohibited claim** (`PACK-16A-COERCION-AND-RECEIPT-BOUNDARY.md`
§8). Meeting a published key-length recommendation is not certification,
and the applicable BSI protection profile is scoped to non-political
elections in any case `[E-53]`.

---

## 4. Security strength — stated as an inference, because the source states none

**The specification never states a security level in bits.** The only two
occurrences of the phrase are comparative `[F-01]`. Neither does the
companion peer-reviewed paper.

The inference, marked as such:

```text
The binding constraint is the 256-bit subgroup order.
Generic discrete-log attack (Pollard rho) ≈ 2^128 operations.
A 4096-bit finite-field modulus exceeds the 3072-bit size conventionally
   rated at 128-bit security against index calculus.
Effective strength ≈ 128 bits, capped by q.
```

That comfortably exceeds BSI's ≥ 120-bit target. **But no bit figure may be
attributed to the specification**, and `PACK-16B-REASON-CODE-SPECIFICATION.md`
§9 forbids a reason-code text from asserting one.

---

## 5. The date that shapes the whole agility model

BSI's verified statements `[F-25]`:

> _"The sole use of classic key agreement mechanisms is only recommended
> **until the end of 2031**."_
>
> _"For applications with very high protection requirements, the transition
> to quantum-safe mechanisms should already take place **by the end of
> 2030**."_

`EPD2-CRYPTO-1` is a purely classical discrete-log profile. It therefore
has a **recommendation cliff that is already dated**, and the honest
architectural response is not a risk-register entry but a field:

| Parameter-set field  | Value                                                                                                                           |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| `deprecation_date`   | **2030-12-31** for any context declared high-assurance; **2031-12-31** otherwise                                                |
| `prohibition_date`   | **2032-12-31** — the outer edge of the guidance's own horizon                                                                   |
| Successor obligation | A quantum-safe or hybrid successor profile must exist **before** the deprecation date, or no new context may be opened after it |

`PACK-16B-PARAMETER-SET-SPECIFICATION.md` §3 carries these as registry
fields and `PACK-16B-CRYPTOGRAPHIC-AGILITY-MODEL.md` §4 carries the
migration model. **Deprecation stops new contexts; it does not invalidate
archived ones** (§6 of the agility model).

A caution that belongs here rather than in a footnote: a hybrid
quantum-safe successor is **not** a parameter change to `EPD2-CRYPTO-1`. It
is a different construction, and under §2 it would be a protocol
adaptation with its own ADR, its own proofs and its own verifier. That work
does not start in this round and is `OD-P16B-06`.

---

## 6. Parameter provenance — the requirement that is discharged best

`KC-19`, `BM-33` and `MX-01` all demand published, independently
reproducible parameter provenance, and they exist because of `F-INF-3`.

The selected parameters are derived, not drawn:

```text
q = 2^256 − 189                             (the largest prime below 2^256)
p : first 256 bits ones, last 256 bits ones,
    middle 3584 bits = binary expansion of ln(2), plus a printed offset δ,
    subject to p prime, q | (p−1), and (p−1)/2q prime
r = (p − 1)/q,  with r/2 prime
g = 2^r mod p
```

The offset `δ` is printed in full, and the specification records that
finding it required enumerating roughly 2.49 million candidates `[F-02]`.
The source of the ln(2) bits is cited to a public integer sequence `[F-02]`.
The stated design purpose of the ln(2) middle is to prevent the modulus
having the sparse form that the Special Number Field Sieve exploits — a
security rationale, not merely an aesthetic one `[F-02]`.

**The research supporting this round regenerated `p`, `q`, `r` and `g` from
the published rule and confirmed byte-for-byte agreement with the printed
hex, together with `(p−1) mod q = 0`, `g^q mod p = 1`, and the primality of
`p`, `q` and `r/2`** `[F-03]`.

Set against the failure that motivated the requirement — commitment
parameters _"just randomly generated without a proof of how they arose"_,
whose generating routine produced exactly the trapdoor needed to break
binding `[E-33]` — this is the opposite situation, and it is the strongest
single argument for Option A in §7.

`TV-01` makes the reproduction a standing acceptance test, so that it is
re-run rather than remembered.

---

## 7. Per-parameter assessment

| Parameter            | Selected value / rule                              | Authoritative source               | Strength  | Validity | EG 2.1 compatible                      | German guidance                            | Downgrade rule                | Failure rule                            |
| -------------------- | -------------------------------------------------- | ---------------------------------- | --------- | -------- | -------------------------------------- | ------------------------------------------ | ----------------------------- | --------------------------------------- |
| Group type           | Prime-order subgroup `Z_p^r` of `F_p*`             | spec §3.1 `[F-02]`                 | —         | to 2031  | required                               | permitted                                  | not selectable                | `parameter_set.group_invalid`           |
| Modulus `p`          | The 4096-bit constant                              | spec §3.1.1 `[F-02]`               | ≥128 inf. | to 2031  | bit-equality                           | ≥3000 ✓                                    | **no alternative exists**     | `parameter_set.modulus_mismatch`        |
| Subgroup order `q`   | `2²⁵⁶ − 189`                                       | spec §3.1.1 `[F-01]`               | ≈128      | to 2031  | bit-equality                           | **≥250 ✓** (§2.3.3 p. 34)                  | **no alternative exists**     | `parameter_set.order_mismatch`          |
| Cofactor `r`         | `(p−1)/q`, `r/2` prime                             | spec §3.1 `[F-02]`                 | —         | —        | derived                                | —                                          | —                             | `parameter_set.cofactor_invalid`        |
| Generator `g`        | `2^r mod p`                                        | spec §3.1.1 `[F-02]`               | —         | —        | bit-equality                           | —                                          | **no alternative exists**     | `parameter_set.generator_mismatch`      |
| Subgroup membership  | `0 ≤ x < p` and `x^q mod p = 1`                    | spec §6 `[F-05]`                   | —         | —        | required                               | aligns with SP 800-56A §5.6.2.3.1 `[F-24]` | never skipped                 | `parameter_set.membership_failed`       |
| Hash `H`             | HMAC-SHA-256, 32-byte key slot                     | spec §5.2 `[F-06]`                 | 256       | to 2031  | required                               | SHA-2 set ✓                                | not selectable                | `transcript.hash_mismatch`              |
| `H_q`                | `H(...) mod q`                                     | spec §5.4 `[F-07]`                 | —         | —        | **not portable to other `q`** `[F-07]` | —                                          | not selectable                | —                                       |
| Domain separation    | The 27-entry tag table                             | spec §5.5 `[F-13]`                 | —         | —        | required                               | —                                          | not selectable                | `transcript.domain_separation_invalid`  |
| Encoding             | Fixed-length big-endian, no separators             | spec §5.1/§5.3 `[F-09]`            | —         | —        | required                               | —                                          | **non-canonical is rejected** | `transcript.encoding_non_canonical`     |
| KDF                  | SP 800-108r1 counter-mode HMAC                     | spec §3.2.2 `[F-10]`               | 256       | —        | required                               | permitted                                  | not selectable                | `dkg.kdf_failure`                       |
| Randomness           | See the randomness architecture                    | AIS 20/31 v3.0 `[F-26]`            | —         | —        | not specified by EG                    | required                                   | **no fallback**               | `parameter_set.randomness_insufficient` |
| Proof challenges     | Strong Fiat–Shamir, statement and context included | spec §3.2.2/§3.3.7/§3.6.5 `[F-08]` | —         | —        | required                               | —                                          | not selectable                | `transcript.challenge_invalid`          |
| Confirmation code    | `H(H_I; 0x29, …)`                                  | spec §5.5.3 `[F-13]`               | —         | —        | required                               | —                                          | not selectable                | —                                       |
| Base hashes          | `H_P → H_B → H_E → H_I`                            | spec §5.5.1 `[F-13]`               | —         | —        | required                               | —                                          | not selectable                | `transcript.base_hash_mismatch`         |
| Guardian commitments | `K_{i,j} = g^{a_{i,j}}`, aggregated Schnorr PoK    | spec §3.2.2 `[F-13]`               | —         | —        | required                               | —                                          | not selectable                | `dkg.proof_of_possession_invalid`       |

**`H_q`'s non-portability deserves emphasis.** The specification records
that plain reduction _"is tailored to the specific choice of `q = 2²⁵⁶ −
189`"_ and that other parameters _"might be much further away from 2²⁵⁶ and
care must be taken"_ `[F-07]`. Any group change therefore also changes the
challenge derivation — which is a second, independent reason why §8's
Option C is a protocol adaptation and not a parameter swap.

---

## 8. Interoperability, migration and verification consequences

| Consequence class     | Under Option A (selected)                                                                                                                                      | Under a group change                                                             |
| --------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| Interoperability      | **No verifier-consumed 2.1 field is changed** — acceptance by an independent conforming verifier is _expected_ and **not yet demonstrated** (`TV-07`, `TV-19`) | **Every conforming verifier rejects it**; `BM-28` becomes unsatisfiable          |
| Security proofs       | The published IND-CPA theorem applies as stated `[F-17]`                                                                                                       | The theorem's parameter hypothesis no longer holds as stated; re-analysis needed |
| Test vectors          | Upstream vectors apply                                                                                                                                         | All vectors must be regenerated; no upstream vectors exist                       |
| Challenge derivation  | `H_q` valid as specified                                                                                                                                       | `H_q` must be redesigned `[F-07]`                                                |
| Encoding              | 512/32/4-byte lengths as specified                                                                                                                             | All lengths change; every domain-separation input length changes                 |
| Archival verification | Records remain interpretable by an unmodified verifier                                                                                                         | Archived records require a bespoke verifier maintained by EPD² indefinitely      |
| Lineage claim         | "ElectionGuard 2.1 lineage" is accurate                                                                                                                        | The claim must be withdrawn or heavily qualified                                 |

---

## 9. Verification obligations arising from this assessment

| ID      | Obligation                                                                                                                                     | Owner                                                                                                                         | Blocking?                                                                                                                                                                                                          |
| ------- | ---------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `VO-01` | ~~Read BSI TR-02102-1 Version 2026-01 and record the minimum for `q`~~ — **SATISFIED** by `[F-36]`: §2.3.3 p. 34 and §2.3.5 p. 36; `256 ≥ 250` | —                                                                                                                             | **satisfied**                                                                                                                                                                                                      |
| `VO-07` | ~~Record the exact chapter, subsection, table, PDF page, printed page and wording~~ — **SATISFIED** by `[F-36]`                                | —                                                                                                                             | **satisfied**                                                                                                                                                                                                      |
| `VO-08` | Assess the normative acceptability of retaining the ElectionGuard 2.1 published parameter family despite Remark 2.12 (p. 34)                   | **PACK-16B external cryptographic review**; independent confirmation **PACK-17**; consequences **PACK-16D**. **Not PACK-16C** | **BLOCKS production implementation acceptance, production activation, legal activation, complete BSI-conformity claims and final cryptographic assurance.** Non-blocking for PACK-16B review and PACK-16C drafting |
| `VO-02` | Read TR-02102-1 Ch. 8 and record which AIS 20/31 functionality classes are required                                                            | PACK-16C                                                                                                                      | blocks activation                                                                                                                                                                                                  |
| `VO-03` | Read TR-02102-1 Table 4.1 and Tables 5.1/5.2 and confirm SHA-256 and HMAC-SHA-256 appear in the recommended sets                               | PACK-16C                                                                                                                      | blocks activation                                                                                                                                                                                                  |
| `VO-04` | Confirm the pinned specification digest independently over a second network path                                                               | PACK-16D                                                                                                                      | blocks implementation                                                                                                                                                                                              |
| `VO-05` | Obtain a cryptographic reviewer's assessment of the profile as composed                                                                        | GOVERNANCE                                                                                                                    | **blocks activation**                                                                                                                                                                                              |

**None of these is closed by assertion in this round, and none is
described as met.**

---

## 10. Residual risks from the parameter layer

| ID      | Risk                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | Severity | Owner              |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- | ------------------ |
| `RB-01` | ~~The current-edition requirement was not read first-hand~~ — **CLOSED.** The document was read; `[F-36]` records §2.3.3 p. 34 and §2.3.5 p. 36 verbatim, and `256 ≥ 250`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | closed   | —                  |
| `RB-09` | **Published parameter family normative divergence.** `EPD2-CRYPTO-1` uses the ElectionGuard 2.1 published finite-field parameter family rather than a MODP or ffdhe family preferred by Remark 2.12 (p. 34). **The reviewed numerical conditions are satisfied** — `\|p\|` 4096 ≥ 3000, `\|q\|` 256 ≥ 250, `ord(g)` prime. The residual concerns **normative acceptability, reviewability of parameter provenance, the interoperability consequences of any replacement, and the security consequences of retaining or changing the family** — **not a claim that the parameters are insecure.** Mitigation: independent cryptographic review under `VO-08`, confirmed in PACK-17. **Blocks production and legal activation until resolved** | medium   | `VO-08`            |
| `RB-02` | The profile has a dated recommendation cliff at **end of 2031** / **end of 2030** for high assurance                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | **high** | `OD-P16B-06`       |
| `RB-03` | No cryptographic reviewer has assessed the profile as composed                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | **high** | `VO-05`            |
| `RB-04` | The specification states no security level; every bit figure EPD² publishes is EPD²'s inference                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | medium   | claims registry    |
| `RB-05` | Two internal inconsistencies exist in the specification's hash section and must be resolved by EPD² `[F-19]`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | medium   | Fiat–Shamir doc §7 |
| `RB-06` | The specification has no errata process and marks two versions simultaneously "Recommended" `[F-30]`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | **high** | stewardship model  |
| `RB-07` | Pinning by digest protects against silent change but not against an unfixed defect                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           | medium   | `VO-05`            |
| `RB-08` | **A weak or duplicated nonce in a voting client is silent**: nothing in the election record reveals it and no verifier can detect it (`PACK-16B-RANDOMNESS-ARCHITECTURE.md` §7)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | **high** | `IM-43`, PACK-16D  |

**SPECIFIED. ASSESSED. REQUIRES EXTERNAL CRYPTOGRAPHIC REVIEW. NOT
PRODUCTION READY. NOT LEGALLY ACTIVATED.**
