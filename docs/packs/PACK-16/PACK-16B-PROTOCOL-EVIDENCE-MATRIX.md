# PACK-16B — Protocol Evidence Matrix

**Round:** PACK-16B — Cryptographic Parameters, Key Ceremony and Trustee Architecture. **Specification and ADR only. No code. No cryptographic code. Not implemented. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-100`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 1. This is the single canonical PACK-16B evidence registry

**Every `[F-nn]` reference in every PACK-16B document resolves here, and
nowhere else.** No other PACK-16B document defines an evidence entry, adds a
field, or introduces an identifier. The first PACK-16A candidate made
exactly that mistake — a second registry grew inside a subject-matter
document — and the narrow correction round consolidated it. This round does
not repeat it.

```text
ONE registry.        PACK-16B-PROTOCOL-EVIDENCE-MATRIX.md
ONE namespace.       F-01 … F-36
NO gaps.             every identifier in the range is defined
NO shadow entries.   no other document defines evidence
```

### 1.1 Field schema — twelve fields, every entry

```text
Evidence ID · Source title · Institution / author · Version / date ·
Source type · Stable reference · Relevant section / page ·
Property supported · Scope · Limitations · Documents using evidence ·
Classification
```

### 1.2 Classification vocabulary

| Code | Meaning                                                                                    |
| ---- | ------------------------------------------------------------------------------------------ |
| `P`  | **Protocol** — the normative construction as its own specification states it               |
| `A`  | **Analysis** — peer-reviewed or published cryptographic analysis                           |
| `N`  | **Normative standard or guidance** — BSI, NIST, ISO                                        |
| `G`  | **Governance / stewardship** — how the upstream artefact is maintained                     |
| `X`  | **EPD²-generated** — verification, reproduction or negative finding produced by this round |

**`X` entries are marked as EPD²'s own work and are never presented as
external corroboration.**

### 1.2a Evidence weight — direct, supporting, historical

Classification says _what kind_ of source an entry is. **Weight** says how
much a conclusion may lean on it, and it is stated per entry wherever a
normative conclusion depends on it:

| Weight                                | Meaning                                                                                                                                                                                                                                                  |
| ------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **direct primary**                    | The current, applicable edition of the document the conclusion names                                                                                                                                                                                     |
| **supporting contextual**             | A different edition of that document, or an adjacent normative source                                                                                                                                                                                    |
| **historical**                        | A superseded regime, cited for corroboration of a requirement class only                                                                                                                                                                                 |
| **direct primary, reviewer-attested** | The current, applicable edition — read by the reviewer and attested to EPD², not opened by EPD² itself. Always labelled. **No entry currently carries this weight:** `F-36` was upgraded to _read first-hand_ when the official PDF was supplied locally |

**A supporting or historical source may corroborate a conclusion; it may not
stand in for the direct primary source.** This distinction exists because a
previous correction round used supporting and historical sources to close a
decision that names BSI TR-02102-1's current edition, and that closure has
been withdrawn (`OD-P16B-01`).

### 1.3 Relationship to the PACK-16A registry

PACK-16B documents cite six PACK-16A entries — `[E-04]`, `[E-19]`,
`[E-22]`, `[E-33]`, `[E-46]`, `[E-53]`. Those resolve to
`PACK-16A-PROTOCOL-EVIDENCE-MATRIX.md`, which is **unchanged by this
round**. The `E-` and `F-` namespaces are disjoint and neither redefines the
other.

**One PACK-16A entry is now known to be partly outdated:** `E-04`'s
"compensated decryption shares for missing guardians" describes the 1.x
lineage, not the pinned 2.1 specification. The correction is recorded in
`PACK-16B-SCOPE-AND-BOUNDARY.md` §5 and evidenced by `F-11` below.
**`E-04` itself is not edited by this round**, because editing an accepted
pack's evidence registry from a later pack is how registries stop being
trustworthy; the correction is additive and traceable.

---

## 2. Registry summary

| Classification     | Entries | IDs                                                           |
| ------------------ | ------- | ------------------------------------------------------------- |
| `P` Protocol       | 15      | `F-01`, `F-02`, `F-04`…`F-13`, `F-16`, `F-17`, `F-18`         |
| `A` Analysis       | 3       | `F-14`, `F-15`, `F-32`                                        |
| `N` Normative      | 13      | `F-20`, `F-21`, `F-23`…`F-29`, `F-33`, `F-34`, `F-35`, `F-36` |
| `G` Governance     | 1       | `F-30`                                                        |
| `X` EPD²-generated | 4       | `F-03`, `F-19`, `F-22`, `F-31`                                |
| **Total**          | **36**  | `F-01` … `F-36`, contiguous                                   |

**Each entry is counted once, under its primary classification.** Two
entries carry a secondary one — `F-10` (`P` / `N`) and `F-12` (`P` / `A`) —
and the secondary is recorded in the entry, not in this census. §4 states
the arithmetic.

**Added in the narrow correction round:** `F-33`, `F-34`, `F-35` — the
sources that complete the subgroup-order assessment. `F-22` and `F-31` were
**rewritten in place**: `F-22` because its earlier text asserted an
inability to assess the BSI threshold that no longer holds, and `F-31`
because an absolute non-existence claim is not what a bounded survey
establishes. No identifier was reused, renumbered or removed.

---

## 3. The registry

---

##### `F-01` · Subgroup order, and the absence of any stated security level — Kind `P`

- **Source title:** _ElectionGuard Design Specification_
- **Institution / author:** Josh Benaloh, Michael Naehrig, Olivier Pereira — Microsoft Research
- **Version / date:** 2.1.0, 12 August 2024, 110 pp.
- **Source type:** official protocol specification
- **Stable reference:** `https://github.com/microsoft/electionguard/releases/download/v2.1/EG_Spec_2_1.pdf` · SHA-256 `a263ab3cd2cf28f05de324ecd2d9752ffed45f814709582b4c2bb23d1826b936`
- **Relevant section / page:** §3.1.1 pp. 14–15; Note 3.1 p. 16; Appendix p. 101
- **Property supported:** `q = 2²⁵⁶ − 189`, the largest prime below `2²⁵⁶`, chosen so that a 256-bit hash reduced mod `q` is near-uniform without rejection sampling. **The specification states no security level in bits**; the only two occurrences of the phrase are comparative
- **Scope:** fixes the subgroup order used by `EPD2-CRYPTO-1`; establishes that any bit-level security figure EPD² uses is an **inference**, not a quotation
- **Limitations:** an absence of a stated level is not a claim that the level is low; it means the source cannot be cited for one
- **Documents using evidence:** `CPA` §1, §4
- **Classification:** `P` (with a negative finding)

##### `F-02` · Parameter derivation and provenance — Kind `P`

- **Source title:** _ElectionGuard Design Specification_
- **Institution / author:** Benaloh, Naehrig, Pereira — Microsoft Research
- **Version / date:** 2.1.0, 12 August 2024
- **Source type:** official protocol specification
- **Stable reference:** as `F-01`
- **Relevant section / page:** §3.1, §3.1.1 pp. 14–16
- **Property supported:** `p` is 4096 bits with the first and last 256 bits all ones and the middle 3584 bits taken from the binary expansion of `ln 2` plus a printed offset `δ`, subject to `p` prime, `q | (p−1)` and `(p−1)/2q` prime; `r = (p−1)/q` with `r/2` prime; `g = 2^r mod p`. The specification records that finding `δ` required enumerating roughly 2.49 million candidates and cites a public integer sequence for the `ln 2` bits. The stated design purpose of the `ln 2` middle is to prevent the modulus taking the sparse form the Special Number Field Sieve exploits
- **Scope:** discharges `KC-19`, `BM-33` and `MX-01` — published, independently reproducible parameter provenance
- **Limitations:** the specification never uses the phrase "nothing up my sleeve" and makes **no explicit rigidity claim**; treating the construction as NUMS is EPD²'s inference and is marked as one
- **Documents using evidence:** `CPA` §1, §6 · `PSS` §2 · `SCOPE`
- **Classification:** `P`

##### `F-03` · Independent computational reproduction of the parameters — Kind `X`

- **Source title:** EPD² PACK-16B parameter reproduction
- **Institution / author:** **EPD² — this round's own research**
- **Version / date:** performed 2026-08, against the pinned specification digest
- **Source type:** **EPD²-generated computational verification**
- **Stable reference:** procedure recorded in `PACK-16B-CRYPTOGRAPHIC-PARAMETER-ASSESSMENT.md` §6; standing obligation `TV-01`
- **Relevant section / page:** `CPA` §6
- **Property supported:** `p`, `q`, `r` and `g` were regenerated from the published rule and agree byte for byte with the printed hexadecimal; `(p−1) mod q = 0`; `g^q mod p = 1`; `p`, `q` and `r/2` are prime
- **Scope:** converts the provenance claim from "documented" to "reproduced", which is the difference the Swiss Post commitment-parameter failure `[E-33]` turned on
- **Limitations:** **this is EPD²'s own computation, not an independent third party's.** It is made a standing acceptance test (`TV-01`) precisely so that it is re-run by others rather than trusted from this document
- **Documents using evidence:** `CPA` §6 · `SCOPE`
- **Classification:** `X`

##### `F-04` · Parameters are fixed; alternatives are out of scope — Kind `P`

- **Source title:** _ElectionGuard Design Specification_
- **Institution / author:** Benaloh, Naehrig, Pereira
- **Version / date:** 2.1.0, 12 August 2024
- **Source type:** official protocol specification
- **Stable reference:** as `F-01`
- **Relevant section / page:** §3.1.1 Note 3.1, p. 16
- **Property supported:** the standard baseline parameters are **fixed by the specification**; reduced parameters are described only as offering _"better performance at a lower security level"_ and are not a conforming production option
- **Scope:** this is the finding that converts options B and C of the finite-field/elliptic-curve decision from _parameter choices_ into _verifier-forking protocol adaptations_, and so decides `PSS` §2 in favour of Option A
- **Limitations:** the note fixes parameters; it does not prohibit a fork. What a fork costs is `F-05`'s subject
- **Documents using evidence:** `CPA` §2 · `PSS` §2 · `AGIL` §1 · `SCOPE`
- **Classification:** `P`

##### `F-05` · Verifier bit-equality and mandatory membership validation — Kind `P`

- **Source title:** _ElectionGuard Design Specification_
- **Institution / author:** Benaloh, Naehrig, Pereira
- **Version / date:** 2.1.0, 12 August 2024
- **Source type:** official protocol specification
- **Stable reference:** as `F-01`
- **Relevant section / page:** §3.1.4 p. 20 = §6.2.1 p. 80 (Verification 1.B–1.D); §6 membership checks
- **Property supported:** a conforming verifier checks the parameters for **bit-equality** with the fixed values; every received group element must satisfy `0 ≤ x < p` and `x^q mod p = 1` before use
- **Scope:** establishes that a parameter change breaks every conforming verifier — the load-bearing fact behind `PS-01`…`PS-04`, `CA-01` and `BM-28` — and that subgroup validation is mandatory rather than defensive
- **Limitations:** says nothing about whether the fixed values are _adequate_; that is `F-20`…`F-25`
- **Documents using evidence:** `CPA` §2, §7 · `PSS` §2 · `FSDS` · `AGIL` §1
- **Classification:** `P`

##### `F-06` · `H` as HMAC-SHA-256 with a fixed key slot — Kind `P`

- **Source title:** _ElectionGuard Design Specification_
- **Institution / author:** Benaloh, Naehrig, Pereira
- **Version / date:** 2.1.0, 12 August 2024
- **Source type:** official protocol specification
- **Stable reference:** as `F-01`
- **Relevant section / page:** §5.2 pp. 71–72
- **Property supported:** `H` is HMAC-SHA-256 used as a random oracle, with a fixed 32-byte value in the key slot; the specification cites indifferentiability of HMAC with fixed-length keys shorter than the block length
- **Scope:** fixes the hash construction for every challenge, base hash and commitment in `EPD2-CRYPTO-1`; the basis of `FS-01`…`FS-15`
- **Limitations:** the random-oracle treatment is an assumption of the construction, not a proved property of HMAC-SHA-256
- **Documents using evidence:** `CPA` §1, §7 · `FSDS` §1
- **Classification:** `P`

##### `F-07` · `H_q` and its non-portability — Kind `P`

- **Source title:** _ElectionGuard Design Specification_
- **Institution / author:** Benaloh, Naehrig, Pereira
- **Version / date:** 2.1.0, 12 August 2024
- **Source type:** official protocol specification
- **Stable reference:** as `F-01`
- **Relevant section / page:** §5.4 and its footnote on reduction bias
- **Property supported:** `H_q(B₀,B₁) = H(B₀,B₁) mod q`, whose near-uniformity depends on `q` lying within `189/2²⁵⁶` of `2²⁵⁶`; the reduction is _"tailored to the specific choice of `q = 2²⁵⁶ − 189`"_
- **Scope:** shows that changing the group order requires redesigning challenge derivation — a second independent reason Option A is not merely convenient
- **Limitations:** a different `q` is not insecure; it requires a different, re-analysed derivation
- **Documents using evidence:** `CPA` §1, §7 · `PSS` §2 · `FSDS` §2
- **Classification:** `P`

##### `F-08` · Strong Fiat–Shamir in all three proof families — Kind `P`

- **Source title:** _ElectionGuard Design Specification_
- **Institution / author:** Benaloh, Naehrig, Pereira
- **Version / date:** 2.1.0, 12 August 2024
- **Source type:** official protocol specification
- **Stable reference:** as `F-01`
- **Relevant section / page:** §3.2.2, §3.3.7, §3.6.5
- **Property supported:** every challenge includes the **statement and the context**, not only the commitment — strong Fiat–Shamir, in the key-generation, ballot and decryption proof families alike
- **Scope:** the direct answer to the weak-Fiat–Shamir failure class `[E-19]`, `[E-22]`; the basis of `FS-03`…`FS-09`
- **Limitations:** strong FS is a property of the specified construction; whether an implementation preserves it is `IM-07` and `TV-06`
- **Documents using evidence:** `CPA` §7 · `FSDS` §3 · `SCOPE`
- **Classification:** `P`

##### `F-09` · Canonical fixed-length encoding — Kind `P`

- **Source title:** _ElectionGuard Design Specification_
- **Institution / author:** Benaloh, Naehrig, Pereira
- **Version / date:** 2.1.0, 12 August 2024
- **Source type:** official protocol specification
- **Stable reference:** as `F-01`
- **Relevant section / page:** §5.1 pp. 69–71; §5.3
- **Property supported:** fixed-length big-endian encoding — 512 bytes for values mod `p`, 32 bytes for values mod `q`, 4 bytes for small integers — with _"no separator byte or character"_
- **Scope:** makes hash inputs unambiguous without delimiters; the basis of `DS-01`…`DS-06` and of the rejection requirement `IM-06`
- **Limitations:** the absence of separators makes correct fixed-length encoding **load-bearing for domain separation**; a lenient decoder silently breaks it
- **Documents using evidence:** `CPA` §7 · `PSS` §3 · `FSDS` §4
- **Classification:** `P`

##### `F-10` · Key derivation — Kind `P`

- **Source title:** _ElectionGuard Design Specification_
- **Institution / author:** Benaloh, Naehrig, Pereira
- **Version / date:** 2.1.0, 12 August 2024
- **Source type:** official protocol specification
- **Stable reference:** as `F-01`
- **Relevant section / page:** §3.2.2 pp. 25–26
- **Property supported:** share and nonce encryption keys are derived with the **NIST SP 800-108r1 counter-mode HMAC KDF**, using HMAC directly rather than `H`, with UTF-8 string labels (`share_enc_keys`, `share_encrypt`, `data_enc_keys`, and the others)
- **Scope:** fixes the KDF and the label set; the reason EPD²'s own domain (`H_X`) uses **string** tags and cannot squat an upstream tag byte
- **Limitations:** the mixture of byte tags (for `H`) and string labels (for the KDF) is a source of implementation error and is called out in `DS-14`
- **Documents using evidence:** `CPA` §7 · `FSDS` §5
- **Classification:** `P` / `N`

##### `F-11` · Decryption in 2.1, and the absence of compensated decryption — Kind `P`

- **Source title:** _ElectionGuard Design Specification_
- **Institution / author:** Benaloh, Naehrig, Pereira
- **Version / date:** 2.1.0, 12 August 2024
- **Source type:** official protocol specification
- **Stable reference:** as `F-01`
- **Relevant section / page:** §3.6
- **Property supported:** each available guardian `i ∈ U` computes `M_i = A^{z_i}`; `|U| = h ≥ k`; Lagrange coefficients are computed over `U`; **the word "compensated" does not appear in version 2.1**, and the specification states: _"a missing secret `s_j` could be computed directly … However, it is preferable to not release any missing secret `s_j` (or the secret `s`) and instead only release the partial decryptions that the secret would have produced. This prevents the secret from being used for additional decryptions without the cooperation of at least `k` guardians."_
- **Scope:** the evidential basis of the narrow factual correction to PACK-16A `KC-11`; of `BR-13`…`BR-16`; and of absence tolerance being exactly `n − k`
- **Limitations:** this is a version-specific finding. It is true of the **pinned** specification and was not true of the 1.x lineage, which is why `CA-*` pinning matters
- **Documents using evidence:** `BRC` §5, §6 · `CQL` §5, §7 · `GL` · `SCOPE` §5
- **Classification:** `P`

##### `F-12` · Bad shares: abort, investigate out of band, restart from scratch — Kind `P`

- **Source title:** _ElectionGuard Design Specification_; _ElectionGuard: a Cryptographic Toolkit to Enable Verifiable Elections_
- **Institution / author:** Benaloh, Naehrig, Pereira (spec); Benaloh, Naehrig, Pereira, Wallach (paper)
- **Version / date:** spec 2.1.0, 12 August 2024; paper USENIX Security 2024, pp. 5485–5502
- **Source type:** official protocol specification + peer-reviewed paper
- **Stable reference:** as `F-01`; `https://www.usenix.org/system/files/usenixsecurity24-benaloh.pdf`
- **Relevant section / page:** spec §3.2.2 (bad-share handling); paper §2.5
- **Property supported:** the specification's complete treatment of misbehaviour is that guardians abort, investigate **out of band**, and restart from scratch, _"After possibly excluding or replacing a misbehaving guardian"_; the paper's justification is that key generation _"runs between publicly identified parties, and there is little benefit for a malicious participant in introducing errors … if these errors are detected before the keys are actually used"_. The specification also suggests, for forensic purposes, that **all** guardians release their secret information
- **Scope:** identifies the gap `PACK-16B-COMPLAINT-AND-DISQUALIFICATION-MODEL.md` fills at the orchestration layer, and the source of `GL-19`'s prohibition after activation and `CD-18`'s prohibition of the broad release
- **Limitations:** _"investigate out of band"_ is not a protocol. It assigns no roles, no deadlines, no evidence standard and no adjudicator, which is why EPD² had to specify one
- **Documents using evidence:** `CDM` §1, §5 · `CTS` §1 · `GL` `GL-19` · `KCS` · `SCOPE` §4
- **Classification:** `P` / `A`

##### `F-13` · Share encryption, key sets, and what may be discarded — Kind `P`

- **Source title:** _ElectionGuard Design Specification_
- **Institution / author:** Benaloh, Naehrig, Pereira
- **Version / date:** 2.1.0, 12 August 2024
- **Source type:** official protocol specification
- **Stable reference:** as `F-01`
- **Relevant section / page:** §3.2, §3.2.2 pp. 25–27 (Eqs. 28–29)
- **Property supported:** three key sets per guardian in 2.1 (vote, ballot-data, communication); coefficient commitments with Schnorr proofs; share encryption whose integrity rests on a proof of knowledge of the encryption nonce, **with no MAC on the payload** and with the sender's index as a _hash input rather than a signed identity_; the share-verification equation; and that **initial secrets "may be discarded"** once shares are formed. Parameter and construction facts are read from the pinned specification, never from its changelog, which disclaims completeness
- **Scope:** the most-used entry in this round — it underlies `GL-16` (destroy initial secrets), `KU-01`…`KU-03` (only `z_i`, `ẑ_i` survive), `CT-11`'s honest limit, `GQ-09`, and the randomness architecture's per-consumer table
- **Limitations:** **guardian-to-guardian authenticity is not cryptographic identity.** It rests on the record-comparison step, and EPD² states this rather than implying signatures exist
- **Documents using evidence:** `CTS` §2 · `CQL` · `CPA` · `FSDS` · `GIM` · `GL` · `KCS` · `KCR` §1 · `RND` · `SCOPE`
- **Classification:** `P`

##### `F-14` · Record comparison in place of signed key shares — Kind `A`

- **Source title:** _ElectionGuard: a Cryptographic Toolkit to Enable Verifiable Elections_
- **Institution / author:** Josh Benaloh, Michael Naehrig, Olivier Pereira, Dan S. Wallach
- **Version / date:** 33rd USENIX Security Symposium, August 2024, pp. 5485–5502
- **Source type:** peer-reviewed conference paper
- **Stable reference:** `https://www.usenix.org/system/files/usenixsecurity24-benaloh.pdf`
- **Relevant section / page:** §2.5
- **Property supported:** _"ElectionGuard relies on guardians checking authentic election records instead of signing their key shares."_ The paper also describes only **two** key sets, the third (communication) key being a 2.1 addition
- **Scope:** confirms `F-13`'s limitation as a deliberate design choice rather than an omission, and is why `CT-11`'s non-repudiation limit is stated explicitly and why the transcript's comparison step is mandatory rather than advisory
- **Limitations:** **the paper must not be cited for the three-key structure**, which post-dates it. Section numbers were obtained by text extraction rather than local PDF parsing and are marked `[UNVERIFIED]` at character level in the underlying research, though the quoted sentence reproduced consistently across independent fetches
- **Documents using evidence:** `CTS` §2 · `KCS` · `SCOPE`
- **Classification:** `A`

##### `F-15` · Distributed-key-generation bias without a commit-then-open round — Kind `A`

- **Source title:** _Secure Distributed Key Generation for Discrete-Log Based Cryptosystems_
- **Institution / author:** Rosario Gennaro, Stanislaw Jarecki, Hugo Krawczyk, Tal Rabin
- **Version / date:** Journal of Cryptology, Vol. 20, No. 1 (2007), pp. 51–83; earlier version EUROCRYPT '99, LNCS 1592, pp. 295–310
- **Source type:** peer-reviewed journal article
- **Stable reference:** DOI `10.1007/s00145-006-0347-3`; earlier version DOI `10.1007/3-540-48910-X_21`
- **Relevant section / page:** §3 (the attack on Pedersen-style DKG)
- **Property supported:** a distributed key generation without a commit-then-open round permits a party acting last to bias the joint public key — a two-party adversary can force a chosen predicate with probability **3/4 rather than 1/2**
- **Scope:** the evidential basis of EPD²'s pre-publication commitment round (`KY-07`…`KY-12`), which is added at the orchestration layer and changes no hash input
- **Limitations:** the result concerns key **distribution uniformity**, which is orthogonal to the specification's own IND-CPA secrecy theorem `[F-17]`; the practical exploit path in an ElGamal _encryption_ setting is far less direct than in a signature setting. `F-32` is the counterweight and must be read with this entry
- **Documents using evidence:** `KCS` §4 · `SCOPE` §4
- **Classification:** `A`

##### `F-16` · The countermeasure exists upstream — in decryption only — Kind `P`

- **Source title:** _ElectionGuard Design Specification_
- **Institution / author:** Benaloh, Naehrig, Pereira
- **Version / date:** 2.1.0, 12 August 2024
- **Source type:** official protocol specification
- **Stable reference:** as `F-01`
- **Relevant section / page:** §5.5.4 (domain tag `0x30`); §3.6
- **Property supported:** an anti-rushing hash **pre-commitment before opening** is present in the decryption protocol and **absent from key generation**
- **Scope:** the asymmetry is visible within the specification itself, which is why EPD² treats the commitment round as an application of the document's own pattern rather than as an invention
- **Limitations:** the presence of the pattern in one protocol is not the specification's endorsement of it in another. EPD² claims consistency, not upstream authority
- **Documents using evidence:** `KCS` §4 · `SCOPE` §4
- **Classification:** `P`

##### `F-17` · The published security theorem — Kind `P`

- **Source title:** _ElectionGuard Design Specification_
- **Institution / author:** Benaloh, Naehrig, Pereira
- **Version / date:** 2.1.0, 12 August 2024
- **Source type:** official protocol specification
- **Stable reference:** as `F-01`
- **Relevant section / page:** Theorem 1 and its statement of hypotheses
- **Property supported:** an **IND-CPA** statement under at most `k − 1` static corruptions, for the specified parameters
- **Scope:** the only published security claim for the construction; applies **as stated** under Option A, and would need re-analysis under any group change — a decisive input to `PSS` §2
- **Limitations:** IND-CPA secrecy is not a key-distribution claim `[F-15]`, is not a claim about the ceremony's orchestration, and is not peer-reviewed independently of the authors `[F-31]`
- **Documents using evidence:** `CPA` §8 · `PSS` §2
- **Classification:** `P`

##### `F-18` · The only upstream constraint on `k` and `n` — Kind `P`

- **Source title:** _ElectionGuard Design Specification_
- **Institution / author:** Benaloh, Naehrig, Pereira
- **Version / date:** 2.1.0, 12 August 2024
- **Source type:** official protocol specification
- **Stable reference:** as `F-01`
- **Relevant section / page:** §3.2 p. 20
- **Property supported:** the specification constrains only `1 ≤ k ≤ n`, and states the purpose of the threshold — that it takes `k` guardians acting jointly to decrypt individual ballots, so that a voter cannot be shown their own vote by any smaller group
- **Scope:** establishes that the guardian count and quorum are **EPD²'s decision entirely**, which is why `PACK-16B-GUARDIAN-AND-QUORUM-MODEL.md` compares four configurations rather than citing a recommendation
- **Limitations:** `1 ≤ k ≤ n` admits `k = 1`, which would be a single-administrator decryption. The upstream constraint is therefore not a safety property, and EPD² supplies the real bound (`k ≥ 3`, `n ≥ k + 2`)
- **Documents using evidence:** `GQM` §1, §2, §3
- **Classification:** `P`

##### `F-19` · Two internal inconsistencies in the specification's hash section — Kind `X`

- **Source title:** EPD² PACK-16B reading of the pinned specification
- **Institution / author:** **EPD² — this round's own finding**
- **Version / date:** 2026-08, against the pinned digest
- **Source type:** **EPD²-generated negative finding**, not confirmed against any official errata
- **Stable reference:** recorded in `PACK-16B-FIAT-SHAMIR-AND-DOMAIN-SEPARATION.md` §7
- **Relevant section / page:** spec §5.5 (Eq. 99 key slot; Eq. 120 constant list)
- **Property supported:** Eq. 99 uses `H_E` where the surrounding construction requires `H_I`; Eq. 120 carries a `"LOCK"` constant that appears nowhere else in the tag table. EPD² resolves them locally (`0x32` → `H_I`; `0x44` without `"LOCK"`) and defers to upstream if upstream resolves differently (`DS-16`)
- **Scope:** the direct evidence for `CA-27` — that EPD² maintains its own errata record — and for `RB-05`
- **Limitations:** **these are EPD²'s readings, found by one reading pass, and are not confirmed by the authors.** They may be errors in EPD²'s reading rather than in the specification, and `DS-16` is written so that either outcome is handled
- **Documents using evidence:** `FSDS` §7 · `AGIL` §6 · `CPA`
- **Classification:** `X`

##### `F-20` · German guidance — security target and horizon — Kind `N`

- **Source title:** _BSI TR-02102-1: Cryptographic Mechanisms: Recommendations and Key Lengths_
- **Institution / author:** Bundesamt für Sicherheit in der Informationstechnik
- **Version / date:** Version 2026-01, published 23 January 2026
- **Source type:** national normative technical guideline
- **Stable reference:** `https://www.bsi.bund.de/` → TR-02102-1
- **Relevant section / page:** Chapter 1
- **Property supported:** _"all cryptographic mechanisms specified in this Technical Guideline achieve a security level of at least 120 bits"_; _"The information provided in this Technical Guideline is therefore only limited to a period until the end of 2032."_
- **Scope:** the target `EPD2-CRYPTO-1` must meet, and the horizon beyond which no current recommendation speaks
- **Limitations:** a technical guideline, **not a legal requirement for a party-internal vote**; conformance is evidence of diligence, not of legality
- **Documents using evidence:** `CPA` §3 · `PSS` §2
- **Classification:** `N`

##### `F-21` · German guidance — recommended key lengths — Kind `N`

- **Source title:** _BSI TR-02102-1_
- **Institution / author:** BSI
- **Version / date:** Version 2026-01, 23 January 2026
- **Source type:** national normative technical guideline
- **Stable reference:** as `F-20`
- **Relevant section / page:** Table 1.2; §2.3
- **Property supported:** recommended key lengths — **Diffie–Hellman in `F_p`: 3000 bits**; ECDH/ECDSA: 250; MAC: 128; block cipher: 128. §2.3 states the requirement that the subgroup be of prime order, on the ground that no method is known to solve the Diffie–Hellman problem in such a subgroup more efficiently than by computing discrete logarithms in it
- **Scope:** `p = 4096 ≥ 3000` and `q = 256` exceeds every adjacent recommended figure — the substance of the BSI verdict in `CPA` §3
- **Limitations:** the specific minimum BSI states for `|q|` in finite-field groups is not quoted from this document — its body is not retrievable from the publisher `[F-22]`. The requirement itself is established by `[F-33]`, `[F-34]` and `[F-35]`, and the comparison above uses only figures that were read first-hand
- **Documents using evidence:** `CPA` §3, §3.2 · `SCOPE` · `ADR-100`
- **Provenance note (narrow correction round):** the 3000 / 250 / 250 figures were **re-confirmed first-hand** against BSI's own Table 1.2 in the 2025-01 edition (`F-35`); the 2026-01 edition's title, version and date are confirmed from the publisher's publication pages
- **Classification:** `N`

##### `F-22` · The publisher-retrieval limitation, with the full attempt log — Kind `X`

- **Source title:** EPD² PACK-16B source-retrieval record
- **Institution / author:** **EPD² — this round's own finding**
- **Version / date:** 2026-08; extended in the narrow correction round and again in the final BSI evidence round
- **Source type:** **EPD²-generated negative finding about evidence availability**
- **Stable reference:** `PACK-16B-CRYPTOGRAPHIC-PARAMETER-ASSESSMENT.md` §3.2.2; obligation `VO-01`
- **Relevant section / page:** BSI TR-02102-1 Version 2026-01 — the finite-field subgroup-order sentence
- **Property supported:** **The body of BSI TR-02102-1 Version 2026-01 was not retrievable over any network route available to this environment** — the document was ultimately obtained by direct local supply instead. Attempt log, each performed and recorded:

  | Route                                                                   | Result                                   |
  | ----------------------------------------------------------------------- | ---------------------------------------- |
  | `bsi.bund.de` EN PDF, `?__blob=publicationFile&v=7`                     | HTML landing page                        |
  | `bsi.bund.de` EN PDF, `?__blob=publicationFile&v=10` (the 2026-01 file) | HTML landing page                        |
  | `bsi.bund.de` EN PDF, no query string                                   | HTML landing page                        |
  | `bsi.bund.de` DE PDF                                                    | HTML landing page                        |
  | `bsi.bund.de` TR-03111 PDF (control)                                    | HTML landing page                        |
  | `bsi.bund.de` signature-catalogue PDF (control)                         | HTML landing page                        |
  | `allianz-fuer-cybersicherheit.de` EN PDF — BSI's second official host   | HTML landing page (same CMS)             |
  | Text-extraction proxy                                                   | HTTP 403                                 |
  | Web-archive snapshot                                                    | rejected by the fetch proxy              |
  | Search for a third-party mirror of the **2026-01** edition              | none found                               |
  | Interactive browser session                                             | not available in this environment        |
  | **Control — third-party mirror of TR-02102-1 2025-01**                  | **PDF body extracted normally** (`F-35`) |
  | **Control — Bundesnetzagentur PDF on a non-BSI government host**        | **PDF body extracted normally** (`F-34`) |

  The two controls establish that PDF extraction works in general, and that the limitation lies in the publisher's delivery rather than in the tooling. The **existence** of the finite-field sentence is corroborated — the phrase _"the order of the subgroup generated by g"_ is indexed inside the current English PDF — but **its value, chapter, subsection, table and page were not read**

- **Scope:** the record of why four rounds could not obtain the document from its publisher. **The limitation was resolved outside the network path**: the reviewer supplied the official PDF locally, and `[F-36]` is a first-hand reading of it. This entry stands as the retrieval history, not as a live constraint
- **Limitations:** **this entry establishes a retrieval limitation, not a cryptographic one, and it is not a substitute for the reading it describes.** It does not show that the sentence is unobtainable generally — only that it was not obtainable here. Anyone with the official PDF closes `VO-01` in one reading
- **Documents using evidence:** `CPA` §3.2 · `OD` §3 · `SCOPE` · `ADR-100` · `HANDOVER`
- **Classification:** `X` · **Weight:** n/a — this is a record of absence, and no normative conclusion rests on it

##### `F-23` · German guidance — recommended elliptic curves — Kind `N`

- **Source title:** _BSI TR-02102-1_
- **Institution / author:** BSI
- **Version / date:** Version 2026-01, 23 January 2026
- **Source type:** national normative technical guideline
- **Stable reference:** as `F-20`
- **Relevant section / page:** §3 (elliptic-curve recommendations)
- **Property supported:** the recommended curve set, which does **not** include the curves an ElectionGuard-style adaptation would most naturally use
- **Scope:** removes the last superficial attraction of the elliptic-curve options in `PSS` §2: an EC adaptation would fork the verifier **and** land outside the recommended curve set
- **Limitations:** a curve outside the recommended set is not thereby insecure; it is outside the guidance EPD² has chosen to align with
- **Documents using evidence:** `PSS` §2
- **Classification:** `N`

##### `F-24` · Domain-parameter and key validation — Kind `N`

- **Source title:** _NIST SP 800-56A Rev. 3: Recommendation for Pair-Wise Key-Establishment Schemes Using Discrete Logarithm Cryptography_
- **Institution / author:** National Institute of Standards and Technology
- **Version / date:** Revision 3, April 2018
- **Source type:** international normative standard
- **Stable reference:** `https://doi.org/10.6028/NIST.SP.800-56Ar3`
- **Relevant section / page:** §5.6.2.3.1, §5.6.2.3.2; safe-prime group treatment
- **Property supported:** the standard public-key validation routines for finite-field groups, including full and partial validation
- **Scope:** independent corroboration that the specification's mandatory membership check `[F-05]` is the standard practice and not a local invention
- **Limitations:** SP 800-56A governs key establishment, not voting; the alignment is on the validation routine only
- **Documents using evidence:** `CPA` §7
- **Classification:** `N`

##### `F-25` · The classical-cryptography horizon — Kind `N`

- **Source title:** _BSI TR-02102-1_
- **Institution / author:** BSI
- **Version / date:** Version 2026-01, 23 January 2026
- **Source type:** national normative technical guideline
- **Stable reference:** as `F-20`
- **Relevant section / page:** Chapter 2
- **Property supported:** classical key agreement is recommended **only until the end of 2031**, and **until the end of 2030** for very high protection requirements; classical signatures until the end of 2035; hybrid post-quantum schemes are recommended, while quantum-safe mechanisms are _"generally not yet trusted to the same extent as the established classical mechanisms"_
- **Scope:** converted into registry fields rather than a risk-register note — `deprecation_date` 2030-12-31/2031-12-31 and `prohibition_date` 2032-12-31 in `PS-*`, with the notification obligations in `CA-14`…`CA-18` and the successor question carried as `OD-P16B-06`
- **Limitations:** a recommendation with a date is not a prohibition on that date; EPD²'s dates are its own, chosen to sit at or inside the guidance
- **Documents using evidence:** `CPA` §5 · `PSS` §3 · `AGIL` §3 · `SCOPE`
- **Classification:** `N`

##### `F-26` · Random number generator functionality classes — Kind `N`

- **Source title:** _AIS 20/31 — A proposal for: Functionality classes for random number generators_
- **Institution / author:** BSI
- **Version / date:** **Version 3.0, 17 September 2024**
- **Source type:** national normative guidance
- **Stable reference:** `https://www.bsi.bund.de/` → AIS 20/31
- **Relevant section / page:** class definitions `PTG.2`, `PTG.3`, `DRG.3`, `DRG.4`, `DRT.1`, `NTG.1`; the recommendation against direct use of a PTG.2 source
- **Property supported:** _"It is thus recommended not to use a PTG.2-compliant PTRNG 'directly' to generate sensitive data like keys, signature parameters, nonces, etc."_; `DRT.1` for DRNG trees is new in v3.0
- **Scope:** the rule that governs the whole randomness architecture — `RN-01`, `RN-02` — and the reason a physical source seeds a DRNG rather than producing key material
- **Limitations:** **which class current German guidance actually requires for this application is `VO-02` and is not assumed here**
- **Documents using evidence:** `RND` §1 · `CPA` §7
- **Classification:** `N`

##### `F-27` · DRBG mechanisms — Kind `N`

- **Source title:** _NIST SP 800-90A Rev. 1: Recommendation for Random Number Generation Using Deterministic Random Bit Generators_
- **Institution / author:** NIST
- **Version / date:** Revision 1, June 2015
- **Source type:** international normative standard
- **Stable reference:** `https://doi.org/10.6028/NIST.SP.800-90Ar1`
- **Relevant section / page:** Hash_DRBG, HMAC_DRBG, CTR_DRBG
- **Property supported:** the three approved DRBG mechanisms
- **Scope:** `RN-03` — a DRBG in EPD² is one of these three and no other
- **Limitations:** the revision's history (the removal of Dual_EC_DRBG) is a reason to name mechanisms explicitly rather than to say "an approved DRBG"
- **Documents using evidence:** `RND` §1
- **Classification:** `N`

##### `F-28` · Entropy sources — Kind `N`

- **Source title:** _NIST SP 800-90B: Recommendation for the Entropy Sources Used for Random Bit Generation_
- **Institution / author:** NIST
- **Version / date:** January 2018
- **Source type:** international normative standard
- **Stable reference:** `https://doi.org/10.6028/NIST.SP.800-90B`
- **Relevant section / page:** health tests; min-entropy estimation
- **Property supported:** requirements on entropy sources, including continuous health testing and min-entropy estimation
- **Scope:** `RN-04`, and the health-test obligations whose failure is `FM-16B-05`
- **Limitations:** governs the source, not the whole generator; `F-29` covers the construction
- **Documents using evidence:** `RND` §1
- **Classification:** `N`

##### `F-29` · RBG constructions — Kind `N`

- **Source title:** _NIST SP 800-90C: Recommendation for Random Bit Generator (RBG) Constructions_
- **Institution / author:** NIST
- **Version / date:** **final, 24 September 2025**
- **Source type:** international normative standard
- **Stable reference:** `https://doi.org/10.6028/NIST.SP.800-90C`
- **Relevant section / page:** construction classes
- **Property supported:** how sources and DRBGs are combined into a generator
- **Scope:** `RN-05`, and the requirement that the construction class used is **recorded in the ceremony transcript** rather than left to the platform
- **Limitations:** newly final; implementations claiming conformance are correspondingly new, which `IM-48` accounts for
- **Documents using evidence:** `RND` §1
- **Classification:** `N`

##### `F-30` · Upstream stewardship — Kind `G`

- **Source title:** ElectionGuard specification index; repository releases and `SECURITY.md`
- **Institution / author:** Microsoft Research (authors); Election Tech Initiative (repository)
- **Version / date:** as observed 2026-08
- **Source type:** governance and project-stewardship observation from primary project artefacts
- **Stable reference:** `https://electionguard.vote/spec/` · `https://github.com/Election-Tech-Initiative/electionguard/releases` · `.../blob/main/SECURITY.md`
- **Relevant section / page:** specification index; release list; security policy
- **Property supported:** there is **no errata document**, **no specification-level security-reporting path**, and **two versions are marked "Recommended" simultaneously**; authorship and maintenance are not separated, and no specification editor is named apart from the authors
- **Scope:** the evidential basis of the whole stewardship model — version pinning by digest, EPD²'s own errata record (`CA-27`), an advisory intake EPD² operates itself, and `OD-P16A-05`'s disposition
- **Limitations:** an observation of a project's current state, which can change; `CA-*` requires it to be re-observed, and a change is an advisory-intake event
- **Documents using evidence:** `AGIL` §6 · `CPA` · `FSDS` · `PSS` · `TVR` §5
- **Classification:** `G`

##### `F-31` · The peer-review gap, as a bounded survey finding — Kind `X`

- **Source title:** EPD² PACK-16B literature survey
- **Institution / author:** **EPD² — this round's own survey**
- **Version / date:** 2026-08
- **Source type:** **EPD²-generated negative finding** from a bounded literature survey
- **Stable reference:** recorded in `PACK-16B-CRYPTOGRAPHIC-PARAMETER-ASSESSMENT.md`; carried as `OD-P16A-06` with the deliverable in `PACK-16B-TEST-VECTOR-AND-FORMAL-REVIEW-REQUIREMENTS.md` §4
- **Relevant section / page:** —
- **Property supported:** **No peer-reviewed security analysis specifically covering the selected ElectionGuard 2.1 key-ceremony composition was located in the sources reviewed for PACK-16B.** The only security argument for the DKG found in the reviewed literature is the authors' own `[F-14]` §2.5 together with Theorem 1 `[F-17]`
- **Scope:** decisive in the remote-ceremony decision (`RCA` §4), determinative of `TV-08`'s status as `blocked pending cryptographic review`, and the reason this round is conservative wherever it could have been convenient
- **Limitations:** **This is an absence-of-evidence finding from a bounded survey and must not be interpreted as proof that no such analysis exists.** It states what this round did not find, in the sources it reviewed. A survey cannot establish non-existence, and no document in this pack may restate it as though it could. If such an analysis is later located or published, it is evidence toward `TV-08` and does not by itself discharge it (`TV-12`)
- **Documents using evidence:** `RCA` §3, §4 · `TVR` §0, §5 · `SCOPE` · `ACC` §4 · `ADR-100`
- **Classification:** `X`

##### `F-32` · The counterweight to `F-15` — Kind `A`

- **Source title:** _Secure Applications of Pedersen's Distributed Key Generation Protocol_
- **Institution / author:** Rosario Gennaro, Stanislaw Jarecki, Hugo Krawczyk, Tal Rabin
- **Version / date:** CT-RSA 2003, LNCS 2612, pp. 373–390
- **Source type:** peer-reviewed conference paper
- **Stable reference:** DOI `10.1007/3-540-36563-X_26`
- **Relevant section / page:** main result
- **Property supported:** _"We show that threshold versions of some schemes whose security reduces to the hardness of the discrete logarithm problem, remain secure when implemented with Pedersen DKG."_ The stated cost is a **larger modulus** for equivalent security, the reduction being loose
- **Scope:** the fairness counterweight to `F-15` — Pedersen-DKG bias is a proof-quality problem and for some schemes provably survivable, and the selected profile uses a 4096-bit modulus with a 256-bit `q`. Cited here so that `F-15` is never used one-sidedly
- **Limitations:** _"some schemes"_ is not _"this scheme"_. The result does not cover the specification's construction specifically, and `F-31` is why nobody has said whether it does
- **Documents using evidence:** this document §1.3, §5 · `TVR` §5
- **Classification:** `A`

##### `F-33` · The European agreed minimum for finite-field subgroup order — Kind `N`

- **Source title:** _Agreed Cryptographic Mechanisms_
- **Institution / author:** European Cybersecurity Certification Group (ECCG), Sub-group on Cryptography
- **Version / date:** **Version 2.0, April 2025**
- **Source type:** European normative agreement on cryptographic mechanisms
- **Stable reference:** `https://certification.enisa.europa.eu/` — _ECCG Agreed Cryptographic Mechanisms version 2_
- **Relevant section / page:** **§4.2 "Agreed FF-DLOG Parameters"**
- **Property supported:** for finite-field discrete-logarithm mechanisms the agreed parameter table requires **`log₂(q) ≥ 250`** for recommended mechanisms and `log₂(q) ≥ 200` for legacy mechanisms (deadline `L[2025]`); for all agreed subgroups `r = q = (p − 1)/2`
- **Scope:** the current European normative minimum for **exactly the parameter dimension** `OD-P16B-01` asked about. `EPD2-CRYPTO-1`'s `|q| = 256` satisfies it
- **Limitations:** this is the ECCG's agreement, **not BSI TR-02102-1**. It cites TR-02102-1 in its related-documents section as having _"partly inspired some of the concepts, definitions, recommendations, or caveats"_, and is **not** cited as BSI's own wording. It establishes a European agreed minimum, not German certification, and nothing here is a conformity assessment
- **Documents using evidence:** `CPA` §3.2 · `OD` §3 · `ACC` · `HANDOVER` · `ADR-100`
- **Classification:** `N` · **Weight: direct primary** — the current European normative agreement, read in its applicable edition

##### `F-34` · The German signature algorithm catalogue's finite-field requirement — Kind `N`

- **Source title:** _Bekanntmachung zur elektronischen Signatur nach dem Signaturgesetz und der Signaturverordnung (Übersicht über geeignete Algorithmen)_
- **Institution / author:** Bundesnetzagentur für Elektrizität, Gas, Telekommunikation, Post und Eisenbahnen, prepared with BSI
- **Version / date:** **9 December 2015**, published in the Bundesanzeiger (the 2016 catalogue)
- **Source type:** German official normative algorithm catalogue
- **Stable reference:** `https://www.bundesnetzagentur.de/EVD/SharedDocuments/Downloads/QES/Algorithmen/2016Algorithmenkatalog.pdf`
- **Relevant section / page:** **§3.2 "DSA", pp. 9–10, Table 2**; and §3.2.a, p. 9, Table 3
- **Property supported:** for DSA in the multiplicative group of a prime field, **`p ≥ 2048` bits and `q ≥ 256` bits from 2016 onward** (Table 2). For the elliptic-curve variant, verbatim: _"Die Länge von q muss mindestens 224 Bit betragen, und ab Anfang 2016 sind für q mindestens 250 Bit erforderlich."_
- **Scope:** a German official source stating a **finite-field** subgroup-order minimum explicitly — the requirement class `OD-P16B-01` asked about — at a value `EPD2-CRYPTO-1`'s `|q| = 256` exactly meets
- **Limitations:** **this catalogue is historical.** It belongs to the Signaturgesetz regime, is superseded by the eIDAS framework, and is scoped to qualified electronic signatures rather than to voting. It is cited as corroboration of the requirement class and its order of magnitude, **not** as the currently applicable rule, and it supports no certification claim. Section, table and page numbers are as reported by an automated text extractor over the published PDF
- **Documents using evidence:** `CPA` §3.2 · `OD` §3 · `ACC` · `HANDOVER` · `ADR-100`
- **Classification:** `N` · **Weight: historical** — a superseded signature regime, corroborating the requirement class only, never standing in for TR-02102-1

##### `F-35` · BSI TR-02102-1 (2025-01), read first-hand via an institutional mirror — Kind `N`

- **Source title:** _BSI TR-02102-1: Kryptographische Verfahren: Empfehlungen und Schlüssellängen_
- **Institution / author:** Bundesamt für Sicherheit in der Informationstechnik
- **Version / date:** **Version 2025-01, Stand 31. Januar 2025**
- **Source type:** national normative technical guideline, retrieved from an institutional mirror because the publisher's own endpoints are not retrievable here `[F-22]`
- **Stable reference:** `https://www.hoever-downloads.fh-aachen.de/krypto/BSI_Empfehlungen2025.pdf` (mirror); publisher: `https://www.bsi.bund.de/` → TR-02102-1
- **Relevant section / page:** **Table 1.2, p. 20**
- **Property supported:** recommended key lengths, read first-hand: **block cipher 128 · MAC 128 · RSA 3000 · DH `F_p` 3000 · ECDH 250 · ECDSA 250**
- **Scope:** first-hand confirmation, from BSI's own document, of the figures the candidate had asserted for the adjacent dimensions; combined with `F-33` and `F-34` it completes the subgroup-order assessment in `CPA` §3.2
- **Limitations:** **this is the 2025-01 edition, not the 2026-01 edition that `OD-P16B-01` names.** The 2026-01 edition's title, version and publication date (23 January 2026) are confirmed first-hand from the publisher's own publication pages; **its body could not be retrieved** `[F-22]`. This extraction reached page 27 and therefore does **not** cover the DLIES or key-agreement subsections, and **this entry does not record any finite-field subgroup-order sentence from any edition.** It must not be cited as though it did
- **Documents using evidence:** `CPA` §3.2, §3.3 · `OD` §3 · `HANDOVER` · `ADR-100`
- **Classification:** `N` · **Weight: supporting contextual** — BSI's own document, previous edition, adjacent tables only

##### `F-36` · The current BSI subgroup-order requirement, read first-hand — Kind `N`

- **Evidence ID:** `F-36`
- **Source title:** _BSI TR-02102-1 — Cryptographic Mechanisms: Recommendations and Key Lengths_
- **Issuing institution:** Bundesamt für Sicherheit in der Informationstechnik (BSI)
- **Document version:** **2026-01** (title page: _"Version: 2026-01"_)
- **Publication date:** **23 January 2026** (title page: _"As of: January 23, 2026"_)
- **Language:** English edition · 92 pages
- **Official URL:** `https://www.bsi.bund.de/SharedDocs/Downloads/EN/BSI/Publications/TechGuidelines/TG02102/BSI-TR-02102-1.pdf?__blob=publicationFile&v=10`
- **Source type:** **direct primary source — national normative technical guideline**
- **Weight:** **direct primary, READ FIRST-HAND.** The official PDF was supplied to EPD² locally by the project's reviewer and read directly; file SHA-256 `f601cdf25c000b431573a307a3c125f3c51d301897089e7e63dde0449367a62a`
- **Exact chapter:** 2.3 _Classical Asymmetric Mechanisms_
- **Exact subsections:** **§2.3.3 DLIES Encryption Scheme** and **§2.3.5 Diffie-Hellman Key Agreement**
- **Exact table / equation:** the _Key Length_ paragraph of §2.3.3; step 2 of _System Parameters_ in §2.3.5. Corroborating: Table 1.1 (p. 18), Table 1.2 (p. 19), Table 2.2 (p. 33)
- **Exact PDF page:** **34** (§2.3.3) and **36** (§2.3.5)
- **Exact printed page:** **34** and **36** — the printed folios match the PDF page numbers
- **Applicable requirement, verbatim:**

  §2.3.3, p. 34, _Key Length_:

  > _"The length of the prime number p should be at least 3000 bits. The length of the prime q should be at least 250 bits in both cases."_

  §2.3.5, p. 36, _System Parameters_, step 2:

  > _"Choose an element g ∈ F∗p with ord(g) prime and q := ord(g) ≥ 2²⁵⁰."_

  §2.3.5, p. 36, _Key Length_:

  > _"The length of p should be at least 3000 bits."_

- **Parameter dimension assessed:** subgroup order `|q|` for finite-field discrete-logarithm mechanisms
- **EPD² value compared:** `q = 2²⁵⁶ − 189` — bit length **256**, value `> 2²⁵⁵` (`[F-01]`); `p` = **4096** bits; `q` prime and `g` of order `q` (`[F-02]`, `[F-03]`)
- **Comparison:**

  ```text
  §2.3.3   |q| = 256  >=  250 bits          SATISFIED   (6 bits of margin)
  §2.3.5   q = 2^256 − 189  >=  2^250       SATISFIED   (a factor of ~2^6)
  §2.3.5   ord(g) prime                     SATISFIED   ([F-02], [F-03])
  §2.3.3 / §2.3.5   |p| = 4096  >=  3000    SATISFIED
  ```

- **Conclusion:** _The selected 256-bit subgroup order satisfies the reviewed BSI TR-02102-1 Version 2026-01 minimum for this specific parameter dimension._
- **Scope:** **limited to the subgroup-order dimension** (with the `p` length recorded alongside it because the same paragraphs state both). It establishes none of the following: complete BSI conformity of `EPD2-CRYPTO-1`; BSI certification; approval for political-election use; implementation security; side-channel resistance; protocol-composition security; legal activation
- **Limitations, and one correction and one divergence found on reading:**
  - **The requirement is 250 bits, not 240.** An earlier round recorded 240 on an attestation. First-hand reading shows **240 is a different figure in this document**: in **Table 1.1, p. 18** it is the ECDSA/ECIES key length at which a 120-bit security level _"is just achieved"_, and separately p. 18 gives 240 bits as the general minimum **hash digest** length. Neither is the finite-field subgroup-order minimum. **`q = 256` satisfies the true requirement of 250 with 6 bits of margin**, so the conclusion is unchanged — but the figure is corrected everywhere
  - **A recommendation-level divergence, recorded rather than glossed.** Remark 2.12, p. 34, states that where published parameters are used the guideline _"recommends using the MODP groups from [78] or the ffdhe groups from [60]"_, in which _"q = (p − 1)/2 and g = 2"_, and that a common `p` is recommended _"only when log₂(p) ≥ 3000"_. `EPD2-CRYPTO-1` uses published parameters that are **neither MODP nor ffdhe**, and its `q` is a 256-bit prime rather than `(p−1)/2`. The `log₂(p) ≥ 3000` condition **is** met (4096). The construction shape is explicitly contemplated by §2.3.5 step 2, which permits any `g` of prime order `≥ 2²⁵⁰`; the divergence is from a **recommendation about which published family to prefer**, not from a stated requirement. It is classified as a **published-parameter-family preference**, not as a numerical minimum, and is carried as `VO-08` — owned by the **PACK-16B external cryptographic review** with independent confirmation in **PACK-17**, **not by PACK-16C** — and as `RB-09`
  - **The classical-mechanism horizon is confirmed from the same chapter:** §2.3 states the sole use of these mechanisms is _"only recommended until the end of 2031"_, and beyond 2031 only in combination with a quantum-safe KEM and a key derivation. This corroborates `[F-25]` and `OD-P16B-06`
  - This entry assesses one parameter dimension. It is **not** a conformity assessment of the profile
- **Documents using the evidence:** `CPA` §3.2 · `OD` §3 · `ACC` `AC-P16B-021` · `HANDOVER` §0.5 · `ADR-100`
- **Classification:** `N`

---

## 4. Integrity block — computed, not asserted

```text
Entries defined                        36   (F-01 … F-36, contiguous)
Distinct identifiers                   36
Duplicate definitions                   0
Gaps in the sequence                    0
RESERVED entries                        0
Registries in PACK-16B                  1
References resolving to this registry  ALL
Unresolved references                   0
Conflicting definitions                 0
```

**Primary-classification census, and its arithmetic:**

```text
P  Protocol          15
A  Analysis           3
N  Normative         13
G  Governance         1
X  EPD²-generated     4
                     --
sum                  36   ==  entries defined (36)   ✓
```

**Secondary classifications, recorded and not counted:**

| Entry  | Primary | Secondary | Reason                                                                 |
| ------ | ------- | --------- | ---------------------------------------------------------------------- |
| `F-10` | `P`     | `N`       | The construction is protocol text; the KDF it names is a NIST standard |
| `F-12` | `P`     | `A`       | The specification text and the peer-reviewed paper state it jointly    |

**Coverage check:** every `[F-nn]` reference appearing in any PACK-16B
document is defined above. `F-32` is cited by this document and by
`PACK-16B-TEST-VECTOR-AND-FORMAL-REVIEW-REQUIREMENTS.md` §5; it is defined
because `F-15` must never be read without it.

---

## 5. What the evidence does **not** establish

Stated here so that no reader has to reconstruct it from thirty-two entries.

| Claim EPD² does **not** make                                                   | Why not                                                                                                                                                                                                             |
| ------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| That the selected construction is proved secure                                | `F-17` is IND-CPA under stated hypotheses; `F-31` is the review gap                                                                                                                                                 |
| That the key ceremony has been independently analysed                          | `F-31` — and equally, that no such analysis exists anywhere is **not** claimed                                                                                                                                      |
| That **complete BSI conformity** of the composed voting profile is established | Only the subgroup-order dimension is assessed, and only against sources other than the edition named by the decision; conformity of the whole profile is neither assessed nor claimed                               |
| That the profile conforms to **all** of TR-02102-1                             | `F-36` assesses the subgroup-order dimension only. Remark 2.12's published-parameter **preference** is a recorded divergence (`VO-08`, which blocks any complete-conformity claim), and `VO-02`/`VO-03` remain open |
| That the DKG produces a uniformly distributed joint key                        | `F-15`; `F-32` softens it and does not settle it                                                                                                                                                                    |
| That EPD²'s commitment round fixes the GJKR issue                              | It mitigates the analogous exposure at the orchestration layer, and `TV-08` must assess it                                                                                                                          |
| That reproducing the parameters proves them safe                               | `F-03` proves provenance, not adequacy                                                                                                                                                                              |
| That an independent conforming verifier accepts an EPD² record                 | No verifier-consumed field is changed, and **that has not been demonstrated by test** — `TV-07`, `TV-19`                                                                                                            |
| That BSI or NIST conformance is legal compliance                               | `F-20`'s limitation; `OD-P16A-12` is where legal assessment lives                                                                                                                                                   |
| That the upstream project will notify EPD² of a problem                        | `F-30` — there is no errata process to notify through                                                                                                                                                               |

---

## 6. Maintenance

| Rule                                                                                                                                                                                            |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A new evidence item gets the **next free `F-nn`**; identifiers are never reused and never renumbered                                                                                            |
| An entry whose source is superseded gains a **superseded-by note**; the original text stays                                                                                                     |
| **No other document may define an `F-nn`.** A future round adding evidence adds it here                                                                                                         |
| An `X` entry that is later confirmed externally **keeps its `X` classification** and gains a note naming the external source — EPD²'s own work does not become independent by being agreed with |

**SPECIFIED. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY. NOT LEGALLY
ACTIVATED.**
