# PACK-16C — Protocol Evidence Matrix

**Round:** PACK-16C — Casting, Receipt, Verification Client, Bulletin Board and Election Record. **Specification and ADR only. No code. No cryptographic implementation. Not implemented. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-101`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 0. This document is the single canonical PACK-16C Evidence Registry

> **All PACK-16C Evidence IDs are canonically defined in
> `PACK-16C-PROTOCOL-EVIDENCE-MATRIX.md`.**

`PACK-16A-PROTOCOL-EVIDENCE-MATRIX.md` (`E-*`) and
`PACK-16B-PROTOCOL-EVIDENCE-MATRIX.md` (`F-*`) remain the canonical
registries for their own rounds. **PACK-16C defines no `E-*` and no `F-*`
identifier, redefines none, and retires none.**

### 0.1 Rules of the registry

```text
One definition per Evidence ID. A mention is not a definition.
An ID is defined here or it does not exist.
An ID is never reused for a different source.
A claim marked INF may not be presented as a source's statement.
A source that was not read is never cited as if it had been.
Marketing material is not evidence and appears in no entry.
```

### 0.2 Evidence weight vocabulary — inherited from PACK-16B, unchanged

| Weight                                | Meaning                                                                                           |
| ------------------------------------- | ------------------------------------------------------------------------------------------------- |
| **direct primary, read first-hand**   | The official document was retrieved and read in this round; section and quotation recorded        |
| **direct primary, reviewer-attested** | A named reviewer read the primary source and attested to it; the round did not read it itself     |
| **supporting contextual**             | Genuine and relevant, but does not by itself establish the property                               |
| **historical**                        | A superseded version, retained because the change itself is informative                           |
| **inherited**                         | Defined in an earlier round's registry, cited here with its original weight and no re-attestation |

**Retrieval date for every web source newly read in this round: 2026-08-01.**

**Kinds** are PACK-16A's: `P` protocol property · `I` implementation
property · `L` legal · `INF` inference by this round.

---

## 1. Registry summary

```text
SUBSTANTIVE PACK-16C DEFINITIONS ........  5   G-01 … G-05
  of which read first-hand in this round   4   G-01, G-02, G-03, G-04
  of which inference (INF) ...............  1   G-05
RESERVED IDs ...........................   0
INHERITED ENTRIES CITED, NOT REDEFINED ..  14  §3
NEW PRIMARY SOURCES RETRIEVED ..........   4
DUPLICATE OR CONFLICTING DEFINITIONS ...   0
CANONICAL REGISTRIES FOR PACK-16C ......   1   (this file)
```

**This round's new evidence is narrow on purpose.** PACK-16C's protocol
substance — the ballot model, the challenge mechanism, the coercion
boundary, the legal frame — was established and evidenced in PACK-16A, and
its parameters in PACK-16B. **The one domain PACK-16C genuinely enters for
the first time is the append-only public log**, and that is where the four
new sources sit.

| ID      | Rule                                                                                                                                                                                     |
| ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `G-R01` | **No PACK-16C document claims an evidential basis it does not have.** Where a design choice rests on inherited evidence, §3 says so; where it rests on nothing but reasoning, §4 says so |

---

## 2. New entries

##### `G-01` · Certificate Transparency Version 2.0 — Kind `P`

- **Source title:** _Certificate Transparency Version 2.0_
- **Author / issuing institution:** IETF — B. Laurie, E. Messeri (Google), R. Stradling (Sectigo)
- **Version / date:** RFC 9162, **Experimental**, December 2021
- **Source type:** standards-body specification (Experimental track)
- **URL:** `https://www.rfc-editor.org/rfc/rfc9162.txt`
- **Relevant sections:** §2.1.1, §2.1.3, §2.1.4, §4, §4.10, §11.3
- **Evidence weight:** **direct primary, read first-hand (2026-08-01)**
- **Property supported:**
  - §4 — _"A log is a single, append-only Merkle Tree of submitted certificate and precertificate entries."_
  - §2.1.3 — _"A Merkle inclusion proof for a leaf in a Merkle Tree is the shortest list of additional nodes in the Merkle Tree required to compute the Merkle Tree Hash for that tree."_
  - §2.1.4 — _"Merkle consistency proofs prove the append-only property of the tree."_
  - §4.10 — _"Periodically, each log SHOULD sign its current tree head information."_
  - §2.1.1 — domain separation between leaf and node hashes is _"required to give second preimage resistance."_
- **Scope of support:** Establishes that the Merkle transparency log with inclusion proofs, consistency proofs and periodically signed tree heads is a specified, standards-body-reviewed construction — the construction `PACK-16C-APPEND-ONLY-AND-CONSISTENCY-MODEL.md` selects. Supports `AO-*`, `BA-*`, `API-21`, `API-22`, `API-23`.
- **Limitations, and the load-bearing one:** §11.3 states that log auditing _"can be circumvented by a misbehaving log that shows different, inconsistent views of itself to different clients"_, and that mechanisms to address this are **outside the scope of the document**. **Split-view detection is explicitly out of scope of RFC 9162.** The RFC is also **Experimental**, not Standards Track. Nothing here concerns elections, ballot secrecy or coercion.
- **Used by:** `AO`, `BA`, `BE`, `IV`, `TM`, `ADR`

##### `G-02` · Certificate Transparency (v1) — Kind `P`

- **Source title:** _Certificate Transparency_
- **Author / issuing institution:** IETF — B. Laurie, A. Langley, E. Kasper (Google)
- **Version / date:** RFC 6962, **Experimental**, June 2013
- **Source type:** standards-body specification (Experimental track)
- **URL:** `https://www.rfc-editor.org/rfc/rfc6962.txt`
- **Relevant sections:** §1, §2.1.1, §2.1.2, §3, §5, §7.3
- **Evidence weight:** **direct primary, read first-hand (2026-08-01)**
- **Property supported:**
  - §3 — _"The SCT is the log's promise to incorporate the certificate in the Merkle Tree within a fixed amount of time known as the Maximum Merge Delay (MMD)."_
  - §1 — the append-only property _"can be used to show that any particular version of the log is a superset of any particular previous version."_
  - §2.1.1, §2.1.2 — audit path and consistency proof definitions, materially as in `G-01`.
- **Scope of support:** **This is the precedent for `PACK-16C-PUBLICATION-ATOMICITY-MODEL.md`.** A signed promise to publish, issued at acceptance and redeemable against a published deadline, is a deployed, decade-old construction rather than an EPD² invention. Supports `PA-*`, `CN-06`, `RE-07`, `EV-24`.
- **Limitations:** §5 states _"The exact mechanism for gossip will be described in a separate document"_, and §7.3 makes detection of append-only violations depend on _"global gossiping"_. The RFC therefore **specifies the promise but not the mechanism by which a broken promise is globally detected.** Experimental track. Not an election document; an MMD violation costs a certificate's timeliness, not a vote.
- **Used by:** `PA`, `CN`, `RE`, `EV`, `FAM`, `ADR`

##### `G-03` · Gossiping in CT — Kind `I`

- **Source title:** _Gossiping in CT_
- **Author / issuing institution:** IETF `trans` Working Group — L. Nordberg, D. K. Gillmor, T. Ritter
- **Version / date:** `draft-ietf-trans-gossip-05`, **2020-02-25**
- **Source type:** expired Internet-Draft
- **URL:** `https://datatracker.ietf.org/doc/draft-ietf-trans-gossip/`
- **Status, verbatim:** _"Expired Internet-Draft (trans WG) Expired & archived"_ — IESG state **Dead**
- **Evidence weight:** **direct primary, read first-hand (2026-08-01)**
- **Property supported:** The IETF's own work item for the gossip mechanism that `G-01` §11.3 and `G-02` §5 defer to **expired at revision 05 and never became an RFC.**
- **Scope of support:** This is the evidence behind `AO-13`, `OD-P16C-12` and `T-P16C-16`. In the most widely deployed transparency-log ecosystem in existence, the mechanism for detecting a log that shows different views to different readers **was specified as necessary, was worked on for years, and was not standardised.** EPD² therefore may not treat split-view resistance as a solved, off-the-shelf property.
- **Limitations:** An expired draft is evidence about the standardisation process, **not** evidence that split-view detection is impossible or that no deployed system does it. Work continued outside the `trans` WG — see `G-04`. This entry establishes the absence of an IETF standard, and nothing stronger.
- **Used by:** `AO`, `TM`, `ODM`, `ADR`

##### `G-04` · Transparency Log Witness Protocol — Kind `I`

- **Source title:** _Transparency Log Witness Protocol_ (`tlog-witness`)
- **Author / issuing institution:** C2SP — Community Cryptography Specification Project
- **Version / date:** repository main branch, retrieved 2026-08-01
- **Source type:** community specification, **no stated maturity level**
- **URL:** `https://github.com/C2SP/C2SP/blob/main/tlog-witness.md`
- **Evidence weight:** **direct primary, read first-hand (2026-08-01)**
- **Property supported:** Witness cosigning exists as a specified construction outside the IETF. A witness _"is an entity exposing an HTTP service identified by a name and a public key"_ which verifies _"that the checkpoint is consistent with their previously recorded state of the log"_, enabling _"self-contained inclusion proofs that can be verified offline"_.
- **Scope of support:** Supports `AO-*`'s mirror-cosigning design and `API-21`/`API-31`'s requirement that proofs be verifiable offline rather than fetched from the party being checked. Establishes that external witnessing is a real construction EPD² could adopt — which is why `OD-P16C-12` is a deferral rather than a dead end.
- **Limitations:** The document **states no maturity level** and is a community specification, not a standards-body product. It does **not** name split-view or equivocation resistance among the properties it provides. It notes that for a transparency system to be effective _"it must not be possible to partition clients from monitors"_ — i.e. **witnessing alone does not defeat partitioning.** No election deployment is cited.
- **Used by:** `AO`, `BA`, `IV`, `ODM`, `ADR`

##### `G-05` · Split-view resistance is unstandardised after thirteen years — Kind `INF`

- **Grounded in:** `G-01` §11.3, `G-02` §5 and §7.3, `G-03`, `G-04`
- **Evidence weight:** **inference by this round — no source states it in this form**
- **The inference:** The transparency-log construction EPD² adopts is mature, specified and widely deployed **for inclusion and consistency**. Its defence against a log that shows different views to different readers is **not** standardised: RFC 6962 deferred it in 2013, RFC 9162 declared it out of scope in 2021, the IETF's own gossip draft died in 2020, and the community witness protocol that exists today does not claim it and explicitly flags partitioning.
- **What it became:** `AO-13` (external witness cosigning is not in the initial profile, and until it exists split-view resistance rests on **organisational** mirror independence, not cryptography), `OD-P16C-12`, `T-P16C-16`, `T-P16C-21`, and `IV-*`'s requirement that a `VERIFIED` result state that a consistent view was checked only against the mirrors actually consulted.
- **What it does not support:** It does **not** support a claim that EPD²'s board is insecure, nor that any deployed transparency log is broken. It supports exactly one thing: **EPD² may not present its board as tamper-proof or split-view-resistant**, which is `PB-18`.

---

## 3. Inherited evidence this round relies on

**Cited with their original weight. Not redefined, not re-attested, not
re-read in this round.**

| Inherited ID             | Registry | What PACK-16C rests on it for                                                                    | PACK-16C artefacts                       |
| ------------------------ | -------- | ------------------------------------------------------------------------------------------------ | ---------------------------------------- |
| `E-01`                   | PACK-16A | ElectionGuard design specification — confirmation codes, ballot encryption, proofs               | `BP-*`, `VP-*`, `RE-*`                   |
| `E-05`                   | PACK-16A | Cast-or-challenge and confirmation codes as specified properties                                 | `CH-*`, `RE-*`                           |
| `E-06`                   | PACK-16A | Declared non-provisions — eligibility, internet voting, coercion are **not** provided            | `SB-*`, `CB-*`, `VP-17`                  |
| `E-07`                   | PACK-16A | **No bulletin board is provided by the selected family** — the board is entirely EPD²'s to build | `BA-*`, `AO-*`, `RR-10`                  |
| `E-10a`                  | PACK-16A | No production-grade implementation of the selected specification version exists                  | `SB-*`, `ADR-101` §risks                 |
| `E-19`, `E-27`, `E-32`   | PACK-16A | Ballot independence and malleability — via `F-INF-1` → `BM-14`                                   | `VP-*` stage 11                          |
| `E-29`                   | PACK-16A | Individual-verification take-up empirically low; verification-window figures contradictory       | `CH-25`, `VC-*`, `IV-*`, `T-P16C-15`     |
| `E-38`                   | PACK-16A | Selene — tracker-based coercion mitigation, and why EPD² does not adopt it                       | `CB-*`, `RE-*`                           |
| `E-41`                   | PACK-16A | BVerfG 2 BvC 3/07 — public verifiability of the essential steps without special expertise        | `IV-*`, `ER-*` §4, `XA-*`                |
| `E-46`                   | PACK-16A | The remote-coercion boundary statement                                                           | `CB-*` fact 4, `RE-14`                   |
| `E-55`, `E-56`           | PACK-16A | German legal and Council of Europe frame                                                         | `SB-*`, `DP-*`                           |
| `F-*` (parameter family) | PACK-16B | `EPD2-CRYPTO-1` parameters, base-hash chain, domain separation, pinned spec digest               | `BP-*`, `VP-*`, `ER-*` artefacts 4 and 7 |
| `F-36`                   | PACK-16B | BSI TR-02102-1 Version 2026-01 §2.3.3 p. 34 and §2.3.5 p. 36, read first-hand in PACK-16B        | `ER-*` artefact 5, `VO-08`               |
| `ADR-099`, `ADR-100`     | —        | No revoting; ceremony, quorum, no pre-closure decryption                                         | `BL-07`, `ER-21`                         |

| ID      | Rule                                                                                                                                                                                                                                         |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `G-R02` | **`VO-08` is inherited as OPEN and is not touched by this round.** PACK-16C cites `F-36` for what it says and neither closes, narrows nor re-owns the obligation (`SB-06`, `T-P16C-37`)                                                      |
| `G-R03` | **`E-41` is the sharpest inherited constraint on this round.** A record whose verification requires expertise the public does not have does not satisfy what that judgment demands, which is why `IV-*`, `ER-*` §4 and `XA-26`…`XA-28` exist |

---

## 4. Decisions in this round that rest on no external source

Stated so that no reader mistakes a reasoned choice for an evidenced one.

| Decision                                                                              | Basis                                                                                                                                                                                                                      | Where           |
| ------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| **Consumption inside the atomic acceptance boundary**                                 | Reasoning from the inherited requirement that a rejected ballot must not spend a capability. No external source specifies this ordering for a voting system                                                                | `CN-*`          |
| **Four separated ballot identity values**                                             | Reasoning from `PM-*`'s correlation analysis. No source prescribes four                                                                                                                                                    | `BP-*`          |
| **Fixed-cadence sealed fixed-capacity batch commitments for turnout confidentiality** | Reasoning from `NIT-*` plus the observation that a public board is a turnout feed. **The first candidate's padding variant was rejected on audit** (`TC-21`). No source prescribes either construction for an election     | `TC-*` §4       |
| **Cover leaves as uniform random values of the leaf's exact size**                    | Reasoning from the requirement that real and cover leaves be structurally indistinguishable (`TC-29`). The hiding property is standard; **its application to turnout confidentiality in an election board is not sourced** | `TC-27`…`TC-29` |
| **Publication deadline with a signed commitment**                                     | Structurally analogous to `G-02`'s MMD, **adapted**, not adopted — the consequences differ entirely                                                                                                                        | `PA-*`          |
| **The 32-artefact record contents**                                                   | Derived from the 16 verifier checks by construction, not from any published record schema                                                                                                                                  | `ER-*`, `EC-*`  |
| **The 16-state ballot lifecycle**                                                     | Extension of PACK-16A's 14 states by this round's reasoning                                                                                                                                                                | `BL-*`          |

| ID      | Rule                                                                                                                                                                                                                                                             |
| ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `G-R04` | **Six of this round's central decisions are reasoned, not evidenced.** That is not a defect — no source exists for several of them — but it is the reason `ADR-101` is `proposed` and the reason external cryptographic review is a gate rather than a formality |

---

## 5. Contradictions and gaps — shown, not hidden

| #   | Finding                                                                                                                                                                                                                                                        | Treatment                                                                                                                                                                                                  |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Both CT RFCs are **Experimental**, not Standards Track, yet CT is among the most deployed transparency systems in existence                                                                                                                                    | Recorded. Deployment is cited as maturity evidence; the track is cited as a caution. Neither is suppressed                                                                                                 |
| 2   | `G-02` §1 says a log showing different views _"can be efficiently detected by comparing tree roots and consistency proofs"_, while `G-01` §11.3 says such a log _"can circumvent"_ auditing and puts the fix out of scope                                      | **Not resolved, and the tension is the finding.** Detection is possible _if comparison actually happens_; nothing in either RFC makes it happen. This is exactly `AO-13`'s position                        |
| 3   | `G-04` provides the construction `G-03` failed to standardise, but claims no split-view property and flags partitioning                                                                                                                                        | Recorded as why `OD-P16C-12` is a deferral with a named path, not an unsolved unknown                                                                                                                      |
| 4   | **No source read in this round concerns elections.** All four new sources are from the certificate and software-supply-chain domain                                                                                                                            | **Stated plainly.** The construction transfers; the threat model does not. Nothing in `G-01`…`G-04` supports any claim about ballot secrecy, coercion or voter behaviour                                   |
| 5   | The sealed batch layer uses Merkle commitments, as `G-01` and `G-02` describe — but **neither source publishes a fixed-capacity, cover-padded commitment for confidentiality**. Certificate Transparency has no reason to hide how many certificates it logged | **The data structure is sourced; the use is not.** `G-01`/`G-02` support the tree, the inclusion proof and the consistency proof. They support **nothing** about turnout confidentiality, which is `G-R08` |

| ID      | Rule                                                                                                                                                                                                                                                                                                                                                                                 |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `G-R05` | **No EPD² claim is created to resolve a contradiction between external sources.** Where sources disagree, the disagreement is the finding — PACK-16A §12's rule, unchanged                                                                                                                                                                                                           |
| `G-R06` | **Finding 4 is the honest limit of this round's new evidence.** The board's _construction_ is well-sourced; the board's _fitness for an election_ is not, and that is a question for external review and PACK-17, not for this registry                                                                                                                                              |
| `G-R08` | **The evidence boundary, stated in the form it must be cited in.** _Transparency-log sources support the selected append-only and consistency mechanisms at the data-structure level. Election-specific suitability, governance, coercion implications and certification effects remain subject to independent review._ No PACK-16C document may cite `G-01`…`G-04` beyond that line |
| `G-R09` | **The sealed batch layer is `INF`-grade throughout.** No source supports fixed-capacity cover-padded commitments as an election turnout control. It is reasoning from an inherited invariant, and `ADR-101` records it as such                                                                                                                                                       |

---

## 6. Registry integrity

```text
canonical PACK-16C evidence registries ........ 1   (this file)
substantive PACK-16C definitions .............. 5   G-01 … G-05
  read first-hand this round .................. 4
  inference (INF) ............................. 1
reserved IDs .................................. 0
duplicate definitions ......................... 0
conflicting definitions ....................... 0
IDs defined outside this file ................. 0
E-* or F-* identifiers defined here ........... 0
E-* or F-* identifiers redefined here ......... 0
inherited entries cited in §3 ................. 14
sources cited but not read .................... 0
```

| ID      | Rule                                                                                                                                                                                                                                                           |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `G-R07` | **"Sources cited but not read = 0" is the claim this registry stands or falls on.** Every `G-*` entry was retrieved on 2026-08-01 and quoted from; every inherited entry is cited as inherited, with no re-attestation of a reading this round did not perform |

---

## 7. Source list

```text
G-01  RFC 9162 · Certificate Transparency Version 2.0 · IETF · Experimental · 2021-12
      https://www.rfc-editor.org/rfc/rfc9162.txt
G-02  RFC 6962 · Certificate Transparency · IETF · Experimental · 2013-06
      https://www.rfc-editor.org/rfc/rfc6962.txt
G-03  draft-ietf-trans-gossip-05 · Gossiping in CT · IETF trans WG · Expired 2020-02-25
      https://datatracker.ietf.org/doc/draft-ietf-trans-gossip/
G-04  tlog-witness · Transparency Log Witness Protocol · C2SP · retrieved 2026-08-01
      https://github.com/C2SP/C2SP/blob/main/tlog-witness.md
G-05  (INF) no source — inference by this round from G-01 … G-04
```

**SPECIFIED. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY. NOT LEGALLY
ACTIVATED.**
