# PACK-16A — Protocol and Legal Evidence Matrix

**Round:** PACK-16A — Verifiable Voting Protocol and Ballot Model Selection. **Specification and ADR only. No code. Not implemented. Not an implementation candidate. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-099`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 0. This document is the single canonical Evidence Registry

> **All PACK-16A Evidence IDs are canonically defined in
> `PACK-16A-PROTOCOL-EVIDENCE-MATRIX.md`.**

There is **one** evidence registry in PACK-16A, and it is this file. Every
`E-nn` identifier used anywhere in `docs/packs/PACK-16/` or in
`docs/adr/ADR-099-VERIFIABLE-VOTING-PROTOCOL-AND-BALLOT-MODEL.md` has
exactly one definition, and that definition is here.

`PACK-16A-GERMAN-LEGAL-BOUNDARY.md` §9 carries a **short local pointer
table** for reading convenience. That table is **not** a second registry: it
defines nothing, it may not introduce an identifier, and it points here.
This consolidation was performed as a narrow documentation correction after
the PACK-16A architectural audit; **no evidence content, no verdict and no
architectural decision was changed by it.**

### 0.1 Rules of the registry

```text
One definition per Evidence ID. A mention is not a definition.
An ID is defined here or it does not exist.
An ID is never reused for a different source.
An ID whose source is withdrawn is retired, never re-pointed.
A RESERVED ID carries no source and supports no claim.
A claim marked UNVERIFIED supports no conclusion anywhere in PACK-16A.
Marketing material is not evidence and appears in no entry.
```

---

## 1. How to read an entry

Each entry carries eleven fields.

| Field                            | Meaning                                                                                                 |
| -------------------------------- | ------------------------------------------------------------------------------------------------------- |
| **Evidence ID**                  | The canonical identifier, in the entry heading                                                          |
| **Source title**                 | The document's own title                                                                                |
| **Author / issuing institution** | Who wrote or issued it                                                                                  |
| **Version / date**               | Version and publication date as printed by the source                                                   |
| **Source type**                  | Specification · peer-reviewed paper · official documentation · repository · disclosure · law · standard |
| **URL / stable reference**       | Where it was retrieved, or its DOI / official citation                                                  |
| **Relevant section / page**      | Where in the source the supported material sits                                                         |
| **Property supported**           | What the source is cited _for_                                                                          |
| **Scope of support**             | How far the citation reaches — and where it stops                                                       |
| **Limitations**                  | What the source does **not** establish; retrieval caveats; unverified elements                          |
| **Used by**                      | The PACK-16A documents that cite this entry                                                             |

Each entry heading also carries a **Kind**, which is the discipline this
pack imposes on itself:

| Kind  | Meaning                                                                                     |
| ----- | ------------------------------------------------------------------------------------------- |
| `P`   | **Protocol property** — stated in a protocol specification or defining paper                |
| `I`   | **Implementation property** — a property of a codebase, deployment, project or organisation |
| `L`   | **Legal** — binding law, judgment, ordinance or official standard                           |
| `INF` | **Inference** — reasoning by this round from cited sources; not stated verbatim anywhere    |

**A claim marked `INF` may not be presented as a source's statement.**

**Retrieval date for every web source: 2026-08-01.**

Short forms used in **Used by**: `SCOPE` · `CMP` (comparison) · `EVD` (this
registry) · `TM` (threat model) · `BM` (ballot model) · `EPM` (election
profile matrix) · `RBL` (revoting and lifecycle) · `CRB` (coercion and
receipt boundary) · `BB` (bulletin board) · `TCR` (trustee and ceremony) ·
`RSM` (role separation) · `GLB` (German legal boundary) · `PDF` (privacy
data flows) · `FAM` (failure and abort) · `AXR` (accessibility) · `RCS`
(reason codes) · `FIR` (FIR coverage) · `CAN` (canon assessment) · `ACC`
(acceptance matrix) · `ODM` (open decisions) · `REP` (specification report)
· `HAND` (handover) · `ADR` (`ADR-099`).

---

## 2. Registry summary

```text
ALLOCATED EVIDENCE IDs .................. 60
SUBSTANTIVE EVIDENCE DEFINITIONS ........ 59
RESERVED IDs ............................  1   (E-48)
HIGHEST EVIDENCE ID ..................... E-56
UNIQUE REFERENCES RESOLVED .............. 58
UNRESOLVED REFERENCES ...................  0
CONFLICTING DEFINITIONS .................  0
DUPLICATE DEFINITIONS ...................  0
CANONICAL REGISTRIES ....................  1
```

Reconciliation, so that the arithmetic is checkable rather than asserted:

```text
numeric slots E-01 … E-56 ......................... 56
  of which reserved (E-48) ........................  1
  substantive numbered entries ....................  55
sub-lettered entries (E-10a, E-16a, E-28a, E-28b) ..  4
substantive definitions = 55 + 4 .................. 59
allocated IDs = 59 substantive + 1 reserved ....... 60
```

**Do not write "56 evidence entries".** That figure counted numeric slots,
omitted the four sub-lettered entries and counted the reserved slot as a
source. The correct figures are those above.

`E-47` is defined and is **not cited by any other document**. It is
retained deliberately as recorded context (§8), and **no PACK-16A claim
depends on it** — which is why the reconciliation shows 58 references
against 59 definitions.

---

## 3. ElectionGuard

##### `E-01` · ElectionGuard Design Specification — Kind `I`

- **Source title:** _ElectionGuard Design Specification_
- **Author / issuing institution:** Josh Benaloh, Michael Naehrig, Olivier Pereira — Microsoft Research
- **Version / date:** **2.1.0**, **12 August 2024** (title page)
- **Source type:** official protocol specification
- **URL / stable reference:** canonical asset `https://github.com/microsoft/electionguard/releases/download/v2.1/EG_Spec_2_1.pdf`; official index `https://electionguard.vote/spec/`
- **Relevant section / page:** title page; official specification index
- **Property supported:** the current specification version, its authorship, and that v2.1 and v2.0 are both marked "Recommended" while 1.1, 1.0, 0.95 and 0.85 are not
- **Scope of support:** identifies the document adopted as the base of `EPD2-HOM-1`. Supports no security property by itself
- **Limitations:** GitHub release-page dates rendered inconsistently against the title page and are treated as **UNVERIFIED**; the title-page date is the reliable one. The deep-read copy was a mirror whose title page matches the official version and date. No version newer than 2.1 was found
- **Used by:** `CMP` §2.3, §3.1 · `ADR` · `ACC` `AC-P16A-029` · `EVD`

##### `E-02` · Cryptographic construction — group and encryption — Kind `P`

- **Source title:** _ElectionGuard Design Specification_
- **Author / issuing institution:** Benaloh, Naehrig, Pereira — Microsoft Research
- **Version / date:** 2.1.0, 12 August 2024
- **Source type:** official protocol specification
- **URL / stable reference:** as `E-01`
- **Relevant section / page:** §3.1, §3.3.1
- **Property supported:** exponential ElGamal in an **integer group modulo a 4096-bit prime** with subgroup order q = 2²⁵⁶ − 189. Verbatim: _"ElectionGuard uses integers to instantiate the encryption rather than elliptic curves in order to make construction of election verifiers as simple as possible."_ Votes encoded in the exponent, giving homomorphic aggregation
- **Scope of support:** establishes the construction and the deliberate rejection of elliptic curves, and is the basis of the open question about German cryptographic guidance
- **Limitations:** does **not** establish that the parameters are acceptable under BSI TR-02102-1 — that is `OD-P16A-03` and is explicitly unanswered
- **Used by:** `CMP` §2.1 · `TCR` §6 (`KC-22`) · `ODM` `OD-P16A-03` · `EVD`

##### `E-03` · Proof system and Fiat–Shamir — Kind `P`

- **Source title:** _ElectionGuard Design Specification_
- **Author / issuing institution:** Benaloh, Naehrig, Pereira — Microsoft Research
- **Version / date:** 2.1.0, 12 August 2024
- **Source type:** official protocol specification
- **URL / stable reference:** as `E-01`
- **Relevant section / page:** §3.3.5–§3.3.6; v2.1 change notes
- **Property supported:** disjunctive Chaum–Pedersen proofs via the Cramer–Damgård–Schoenmakers technique; range proofs for cardinal methods; **Fiat–Shamir with the statement included**; Schnorr proofs of guardian key correctness. v2.1 opens challenged ballots by releasing encryption nonces rather than by verifiable decryption
- **Scope of support:** supports the requirement that the _specification_ uses strong Fiat–Shamir
- **Limitations:** **says nothing about any implementation.** That an implementation uses strong Fiat–Shamir must be shown by test — `AC-P16A-039`, `KC-23`. Detailed §3.4.4 ballot-chaining text and §3.6 Lagrange formulas were not extracted and are **UNVERIFIED in detail**; the structure is verified
- **Used by:** `CMP` §2.1 · `BM` §8.2 · `RBL` §3.2 · `TCR` §6 · `EVD`

##### `E-04` · Threshold key generation and decryption — Kind `P`

- **Source title:** _ElectionGuard Design Specification_; _ElectionGuard: a Cryptographic Toolkit to Enable Verifiable Elections_
- **Author / issuing institution:** Benaloh, Naehrig, Pereira (spec); Benaloh, Naehrig, Pereira, Wallach (paper)
- **Version / date:** spec 2.1.0, 12 August 2024; paper USENIX Security 2024
- **Source type:** official protocol specification + peer-reviewed paper
- **URL / stable reference:** as `E-01`; `https://www.usenix.org/system/files/usenixsecurity24-benaloh.pdf`
- **Relevant section / page:** spec §3.2, §3.6
- **Property supported:** **Pedersen-variant distributed key generation**, n guardians with quorum k, Shamir sharing; Lagrange-interpolated partial decryptions; **compensated decryption shares** for missing guardians. Paper: _"a variant of Pedersen's DKG protocol supporting a dishonest majority at the price of reduced robustness."_ Spec footnote: _"Compromised guardians—whether instantiated as humans or hardware—cannot compromise the integrity of the election tallies"_; _"the role of guardians is to protect confidentiality of votes"_
- **Scope of support:** the basis of `NO SINGLE-ADMIN DECRYPTION` as a construction property, and of `TP-04` (integrity tolerates a dishonest majority; confidentiality is what k protects)
- **Limitations:** does not establish that any particular k and n are adequate; those are `TP-01`…`TP-07` and PACK-16B's
- **Used by:** `CMP` §2.1 · `BM` §1.1 · `TM` §4 · `TCR` §1, §2 · `ACC` `AC-P16A-010`, `AC-P16A-070` · `ADR` · `EVD`

##### `E-05` · Scope statement, cast-or-challenge, confirmation codes — Kind `P`

- **Source title:** _ElectionGuard Design Specification_; _ElectionGuard: a Cryptographic Toolkit to Enable Verifiable Elections_
- **Author / issuing institution:** Benaloh, Naehrig, Pereira, Wallach — Microsoft Research; UCLouvain; Rice University
- **Version / date:** spec 2.1.0, 12 August 2024; paper **USENIX Security 2024** (33rd USENIX Security Symposium, 14–16 August 2024, Philadelphia)
- **Source type:** official protocol specification + peer-reviewed paper
- **URL / stable reference:** as `E-01`; `https://www.usenix.org/system/files/usenixsecurity24-benaloh.pdf`
- **Relevant section / page:** spec §1, §3.4; paper §2.6.4, §2.8.1
- **Property supported:** _"ElectionGuard is not a complete election system. It instead provides components that are designed to be flexible and to promote innovation by election officials and system developers."_ Cast-or-challenge is core: _"the encryption device must commit to the ballot confirmation code and offer the choice to either cast or challenge the prepared ballot. The two choices are mutually exclusive, since the challenging operation reveals the selections on the ballot."_ And on receipts: confirmation codes derived entirely from encryptions do not compromise privacy _"in properly deployed in-person applications"_
- **Scope of support:** supports `BM-03` (the code reveals nothing about the choice) and `BM-07`…`BM-13` (challenge/spoil)
- **Limitations:** **the in-person qualifier is load-bearing and does not transfer to EPD²'s remote deployment.** The receipt-freeness argument is made for a setting EPD² is not in; `CRB` treats the remote case independently. The spec does not use the phrase "Benaloh challenge" — the lineage is documented in the paper
- **Used by:** `CMP` §2.2, §3.1 · `BM` §1.1, §4 · `CRB` §2.1, §3 · `EPM` §7 · `TM` §5 · `CAN` `CQ-04` · `ACC` `AC-P16A-014`, `AC-P16A-058`, `AC-P16A-062` · `ADR` · `EVD`

##### `E-06` · Declared non-provisions — eligibility, internet voting, coercion — Kind `P`

- **Source title:** _ElectionGuard Design Specification_; _ElectionGuard: a Cryptographic Toolkit to Enable Verifiable Elections_
- **Author / issuing institution:** as `E-05`
- **Version / date:** spec 2.1.0, 12 August 2024; paper USENIX Security 2024
- **Source type:** official protocol specification + peer-reviewed paper
- **URL / stable reference:** as `E-05`
- **Relevant section / page:** spec §1, §2 fn. 1, Note 3.2; paper §2.8, §2.9, §3.5, §6.3
- **Property supported:** _"An E2E-verifiable election does not guarantee that the recorded votes have been cast by legitimate voters: this needs to be ensured through the traditional voter identification mechanisms that are already deployed in elections."_ · _"Eligibility is thereby achieved entirely through publicly-verifiable processes that are entirely outside the scope of ElectionGuard, and the only intersection is for interested parties to confirm that the number of ballots cast does not exceed the number of voters listed."_ · internet voting _"not recommended for public elections"_ · _"cryptographic means cannot ensure that there are no cameras hidden behind voters recording their actions"_ · _"any group that has the ability to decrypt individual ballots can also coerce voters by demanding to see their confirmation codes"_
- **Scope of support:** **the central argument of the selection** — the declared eligibility gap is the interface PACK-15 built. Also supports the `PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT` posture and the honest statement of the CoE Standard 18 shortfall
- **Limitations:** the aggregate count check is **weaker** than ballot-level eligibility verifiability, and PACK-16A says so rather than claiming the standard is met
- **Used by:** `CMP` §2.2, §3.1 · `BM` §1.1, §9 · `GLB` §6 · `REP` §2.1 · `ACC` `AC-P16A-025`, `AC-P16A-026`, `AC-P16A-054` · `ADR` · `EVD`

##### `E-07` · No bulletin board is provided — Kind `P`

- **Source title:** _ElectionGuard: a Cryptographic Toolkit to Enable Verifiable Elections_
- **Author / issuing institution:** Benaloh, Naehrig, Pereira, Wallach
- **Version / date:** USENIX Security 2024
- **Source type:** peer-reviewed paper
- **URL / stable reference:** `https://www.usenix.org/system/files/usenixsecurity24-benaloh.pdf`
- **Relevant section / page:** §2.2
- **Property supported:** _"In many verifiable election systems, it is assumed that a public bulletin board exists for publishing these records. In practice, it has most often taken the form of a simple web page."_ ElectionGuard assumes the administrator provides a broadcast channel with similar properties
- **Scope of support:** establishes that the board is **not** supplied by the selected family and is entirely EPD²'s to build — `RR-10`
- **Limitations:** states an assumption; provides no requirements, no format and no protocol. Everything in `BB` is EPD²'s own
- **Used by:** `CMP` §2.1, §3.1 · `BM` §3 (gap table) · `BB` §1 · `ACC` `AC-P16A-067` · `ADR` · `EVD`

##### `E-08` · Supported and unsupported ballot methods — Kind `P`

- **Source title:** _ElectionGuard Design Specification_; USENIX Security 2024 paper
- **Author / issuing institution:** as `E-05`
- **Version / date:** spec 2.1.0, 12 August 2024
- **Source type:** official protocol specification + peer-reviewed paper
- **URL / stable reference:** as `E-05`
- **Relevant section / page:** spec §3.3.5 and the contest / selection-limit model
- **Property supported:** _"Ranked choice voting is not supported in this version of ElectionGuard, but it may be enabled in a future version."_ · _"This so-called homomorphic tallying approach is usually not suitable for voting methods like Instant-Runoff Voting (IRV) or Single Transferable Vote (STV)."_ Supported: 1-of-m, n-of-m, approval (selection limit = option count), cumulative, score/range, STAR and Borda via range proofs added in v2.0. A mixnet alternative is _"on the ElectionGuard road map"_. Write-ins: _"Verifiable tallying of free-form write-ins may be best done with a mixnet design"_
- **Scope of support:** determines the supported and unsupported election types of `EPD2-HOM-1`, and the existence of `EPD2-MIX-1` as a separate, deferred profile
- **Limitations:** a roadmap statement is not a commitment; no mixnet capability is assumed to arrive
- **Used by:** `CMP` §2.2, §3.1 · `BM` §2.2, §10 · `EPM` §2, §3 · `ODM` `OD-P16A-02` · `ACC` `AC-P16A-041`…`044` · `EVD`

##### `E-09` · Verifier specification and independent verifiers — Kind `P` / `I`

- **Source title:** _ElectionGuard Design Specification_ §6; USENIX Security 2024 paper; _Machine-Checking the Universal Verifiability of ElectionGuard_
- **Author / issuing institution:** Microsoft Research (spec); Thomas Haines, Rajeev Goré, Jack Stodart (machine-checking)
- **Version / date:** spec 2.1.0, 12 August 2024; NordSec / _Secure IT Systems_ 2021
- **Source type:** official protocol specification + peer-reviewed papers
- **URL / stable reference:** as `E-01`; DOI `10.1007/978-3-030-70852-8_4`
- **Relevant section / page:** spec §6; paper §2.8.4
- **Property supported:** verifier construction spans eight verification categories — parameters; key-ceremony Schnorr and commitment checks; extended base hash; ballot well-formedness and contest sums; tally aggregation and decryption; contest-data decryption; challenged ballots; pre-encrypted ballots. USENIX'24 states the website offers links to _"six independent verifiers"_. Independent machine-checking of universal verifiability exists
- **Scope of support:** supports `BM-27`, `BB-33`–`BB-34` — that verification steps can be specified in prose sufficient to write an independent verifier
- **Limitations:** **the identities of the six verifiers are UNVERIFIED** — the candidate verifier index pages returned 404. **The prover and specification version used by Haines et al. are UNVERIFIED.** Neither gap supports any conclusion
- **Used by:** `CMP` §2.2, §3.1 · `BM` §7 · `BB` §6 · `EVD`

##### `E-10a` · Licence, implementations and their maturity — Kind `I`

- **Source title:** repository metadata and READMEs; ElectionGuard sample-data pages
- **Author / issuing institution:** Election-Tech-Initiative and Microsoft GitHub organisations; VotingWorks
- **Version / date:** as observed 2026-08-01
- **Source type:** official repositories and project documentation
- **URL / stable reference:** `https://github.com/Election-Tech-Initiative/electionguard`; `https://github.com/microsoft/electionguard-rust`; `https://github.com/votingworks/electionguard-kotlin-multiplatform`; `https://electionguard.vote/develop/Sample_Data/`
- **Relevant section / page:** repository landing pages, licence files, README status lines
- **Property supported:** **Licence MIT.** No production-grade spec-2.1 implementation exists: `microsoft/electionguard-rust` targets 2.1.0 and self-declares _"Project status: INCOMPLETE, EXPERIMENTAL"_; `electionguard-python` carries a 0.95.0 badge; the most complete 2.x implementation is third-party `votingworks/electionguard-kotlin-multiplatform` at 2.0.0, which ships JSON test vectors and a verifier. Published sample election data is Data Version 0.95
- **Scope of support:** the basis of `RR-01`, `OD-P16A-04`, and of selecting a **specification rather than a library**. The MIT licence is why the selection creates no `FIR-OSS-*` dependency
- **Limitations:** **first-party 2.1 test vectors: UNVERIFIED.** Stewardship: `electionguard.vote` states the project is _"steered by Microsoft"_ while code and documentation sit under the Election-Tech-Initiative organisation and specification release assets are still served from `github.com/microsoft/electionguard`; **no primary document formally transferring stewardship was located — UNVERIFIED**, and that gap is `OD-P16A-05` / `RR-08`
- **Used by:** `CMP` §2.3, §3.1 · `BM` §1, §11 · `FIR` §5.1 · `ODM` `OD-P16A-04`, `OD-P16A-05`, `OD-P16A-08` · `ACC` `AC-P16A-029` · `ADR` · `EVD`

---

## 4. Belenios

##### `E-10` · Specification and software versions, licence, governance — Kind `I`

- **Source title:** _Belenios specification_; Belenios project pages
- **Author / issuing institution:** Stéphane Glondu; Inria / CNRS / Loria
- **Version / date:** specification **3.0** (**no date printed — UNVERIFIED**); deployed software **3.1**; governance page as at 2025
- **Source type:** official protocol specification + official project documentation
- **URL / stable reference:** `https://www.belenios.org/specification.pdf`; `https://www.belenios.org/software.html`; `https://www.belenios.org/aboutus.html`
- **Relevant section / page:** title page; software and about-us pages
- **Property supported:** the published specification is for **3.0** while the deployed software is **3.1**, and the official caveats document is titled for 3.1. **Licence AGPL-3.0.** As of 2025 development moved to a startup structure operating independently of the research institutions
- **Scope of support:** a maturity and governance finding weighing against Belenios as base; and the AGPL note that makes the licensing question `OD-P16A-08` real for that candidate and absent for the selected one
- **Limitations:** **the existence of a 3.1 specification document is UNVERIFIED**; the specification's date is **UNVERIFIED**. No 3.1-only property is asserted anywhere in PACK-16A. Belenios deployment statistics after 2020 are **UNVERIFIED** and are not used
- **Used by:** `CMP` §2.3, §3.2 · `FIR` §5.1 · `ODM` `OD-P16A-08` · `ACC` `AC-P16A-030` · `EVD`

##### `E-11` · Cryptographic construction — Kind `P`

- **Source title:** _Belenios specification_
- **Author / issuing institution:** Stéphane Glondu; Inria / CNRS / Loria
- **Version / date:** 3.0
- **Source type:** official protocol specification
- **URL / stable reference:** `https://www.belenios.org/specification.pdf`
- **Relevant section / page:** §1, §3.1.1, §4.9–§4.16, §5
- **Property supported:** ElGamal over one of three groups — BELENIOS-2048, RFC-3526-2048 or **Ed25519** — selected by question type; threshold decryption in "Single" or Pedersen (t+1 of m) mode; Schnorr Σ-protocols with SHA-256 Fiat–Shamir; interval, sum and blank-vote proofs; _"Zero-knowledge proofs include the complete description of the group to avoid attacks"_
- **Scope of support:** the contrast column in the comparison — notably that Belenios has a deployed elliptic-curve option where the selected specification deliberately does not
- **Limitations:** **the default group of the hosted 3.1 platform is UNVERIFIED**; no claim depends on it
- **Used by:** `CMP` §2.1, §2.3 · `EVD`

##### `E-12` · Counting methods — homomorphic versus mixnet — Kind `P`

- **Source title:** _Belenios specification_; Belenios "alternative voting methods" page
- **Author / issuing institution:** Stéphane Glondu; Inria / CNRS / Loria
- **Version / date:** specification 3.0; project page as at 2026-08-01
- **Source type:** official protocol specification + official project documentation
- **URL / stable reference:** `https://www.belenios.org/specification.pdf`; `https://www.belenios.org/mixnet.html`
- **Relevant section / page:** §4.18–§4.21, §6
- **Property supported:** **homomorphic** questions tally by ciphertext product and never decrypt individual ballots; **non-homomorphic** and **Lists** questions require shuffling, and _"the decrypted ballots are provided as election data"_. Mixnet mode surfaces Condorcet (Schulze), STV and Majority Judgment. Shuffle algorithms _"taken from the CHVote specification"_ v1.3.2. Weighted voting is an error in mixnet mode
- **Scope of support:** the basis of filter `F5` failing for Belenios's mixnet mode, and of `EPD2-MIX-1` being deferred rather than adopted
- **Limitations:** the **privacy consequence** — that publishing decrypted preference vectors reintroduces a pattern-signature channel — is PACK-16A's inference from the mechanism; **no official Belenios document was found naming it as a caveat**, and it is presented as inference, not as Belenios's statement
- **Used by:** `CMP` §2.2, §2.4, §3.2 · `BM` §2.2 · `EPM` §2, §3 · `ODM` `OD-P16A-02` · `ACC` `AC-P16A-042`, `AC-P16A-047` · `ADR` · `EVD`

##### `E-13` · Registrar / credential-authority separation — Kind `P` / `I`

- **Source title:** _Belenios specification_; _How it works_ (official page)
- **Author / issuing institution:** Stéphane Glondu; Inria / CNRS / Loria
- **Version / date:** specification 3.0; project page as at 2026-08-01
- **Source type:** official protocol specification + official project documentation
- **URL / stable reference:** `https://www.belenios.org/specification.pdf`; `https://www.belenios.org/howitworks.html`
- **Relevant section / page:** §2, §3.1
- **Property supported:** the credential authority **C** generates private credentials, distributes them to voters, and sends the server a list **L** of sorted public credentials **paired with voter identity and weight**; C may optionally forget the private credentials. In the default hosted mode _"The election server generates and sends one credential for each voter"_, collapsing the separation
- **Scope of support:** **the decisive rejection ground.** List L is precisely the row PACK-15 §3 forbids — one store holding an eligibility-side and a voting-side reference for the same participation. Also the ground on which the revoting analysis identifies Belenios's supersession handle
- **Limitations:** does not imply Belenios is insecure on its own terms; the mechanism is what prevents server-side ballot stuffing. The incompatibility is with **this** architecture, and PACK-16A says so
- **Used by:** `CMP` §2.2, §2.4, §3.2 · `BM` §9.1 · `RBL` §2.2 · `ACC` `AC-P16A-026`, `AC-P16A-027` · `ADR` · `EVD`

##### `E-14` · Official coercion-resistance position and revoting — Kind `I`

- **Source title:** Belenios FAQ
- **Author / issuing institution:** Belenios project (Inria / CNRS / Loria)
- **Version / date:** as retrieved 2026-08-01
- **Source type:** official project documentation
- **URL / stable reference:** `https://www.belenios.org/faq.html`
- **Relevant section / page:** "Can Belenios be used for high stake elections?"; revoting entries
- **Property supported:** _**"Belenios fails to achieve coercion resistance: it is easy to sell the credentials and the login and passwords (unless a CAS server is used)."**_ Revoting is _"a (moderate) protection against coercion"_; _"Only the last ballot is kept."_ Without a decryption authority _"the server has the technical ability to know who voted what"_
- **Scope of support:** the strongest single citation for the honest coercion boundary, and for the assessment of revoting as a moderate temporal control
- **Limitations:** an FAQ is official project documentation, not a peer-reviewed result; it is cited for the project's **own stated position**, which is what it establishes. The exact phrase _"receipt-free"_ does not appear in official non-academic documentation — **UNVERIFIED**, and PACK-16A does not attribute it
- **Used by:** `CMP` §2.2, §3.2 · `CRB` §5, §8 · `RBL` §2, §2.3 · `TM` §5 · `ACC` `AC-P16A-058`, `AC-P16A-060` · `ADR` · `EVD`

##### `E-15` · Known caveats of Belenios 3.1 — Kind `I`

- **Source title:** _Known caveats of Belenios 3.1_
- **Author / issuing institution:** Véronique Cortier and Pierrick Gaudry — CNRS, Loria
- **Version / date:** **28 April 2025**
- **Source type:** official limitation documentation
- **URL / stable reference:** `https://www.belenios.org/caveats.pdf`
- **Relevant section / page:** caveats 1–3
- **Property supported:** (1) a **revoting-enabled verifiability attack** — a malicious server replaces a voter's latest ballot with an earlier one after she has checked it, and _"this attack cannot be detected in Belenios 3.1 and earlier"_; (2) _"Belenios strongly assumes that all participants have access to a public, append-only bulletin board"_ while in practice a dishonest server _"may provide inconsistent views to the participants"_; (3) fragile vote privacy — trustees do not verify individual ballots and, in mixnet mode, skip verification of previous shuffles _"for usability reasons"_
- **Scope of support:** the strongest published evidence in the **revoting decision**; the evidence that the board is the field's weakest published surface; and the model for `PACK-16A-COERCION-AND-RECEIPT-BOUNDARY.md` as a separate public limitations document
- **Limitations:** the document explicitly does **not** treat coercion-resistance or cast-as-intended, and is not cited for either
- **Used by:** `CMP` §3.2 · `BB` §1, §5 · `CRB` §5 · `RBL` §2.3 · `ACC` `AC-P16A-011`, `AC-P16A-012`, `AC-P16A-060`, `AC-P16A-065`, `AC-P16A-068` · `ADR` · `EVD`

##### `E-16` · Machine-checked formal analysis — Kind `P`

- **Source title:** _Machine-checked proofs for electronic voting: privacy and verifiability for Belenios_
- **Author / issuing institution:** Véronique Cortier, Constantin Cătălin Drăgan, François Dupressoir, Bogdan Warinschi
- **Version / date:** **IEEE CSF 2018** (31st IEEE Computer Security Foundations Symposium)
- **Source type:** peer-reviewed paper
- **URL / stable reference:** `https://members.loria.fr/VCortier/files/Papers/CSF18-Belenios.pdf`
- **Relevant section / page:** Theorem 1 and the surrounding assumption discussion; Belenios specification §3.5.2 for the audit tooling
- **Property supported:** **EasyCrypt machine-checked** BPRIV ballot privacy, strong correctness, strong consistency and strong verifiability for Belenios[Policy], Policy ∈ {first, last}. **Static corruption only.** Verifiability proven separately for a dishonest ballot box _or_ a dishonest registrar, **never both**. The formalisation surfaced that **privacy requires an honest registrar**. Audit is performed by the CLI `election verify` / `election verify-diff`
- **Scope of support:** the template for how `ADR-099` states its own trust assumptions — a proof is only as strong as the corruption model it quantifies over
- **Limitations:** the paper's venue is recorded per the official Belenios documentation page; an extractor reading of the PDF header reporting a different venue is treated as unreliable. The proof covers the protocol and _"assumes security of the cryptographic primitives"_
- **Used by:** `CMP` §2.3, §3.2 · `EVD`

##### `E-16a` · CSPN certification campaign outcome — Kind `I`

- **Source title:** _Belenios: the Certification Campaign_
- **Author / issuing institution:** Bossuat, Brocas, Cortier, Gaudry, Glondu, Kovacs
- **Version / date:** **SSTIC 2024**, Rennes
- **Source type:** peer-reviewed conference paper
- **URL / stable reference:** `https://www.sstic.org/media/SSTIC2024/SSTIC-actes/belenios_the_certification_campaign/`
- **Relevant section / page:** campaign outcome and findings sections
- **Property supported:** **certification was not obtained** in that campaign: _"the scope of security target required to be enlarged, which precluded the certification."_ Findings patched included too few PBKDF2 iterations against OWASP guidance and a salt too short against ANSSI guidance
- **Scope of support:** a maturity finding, and evidence that a certification attempt on a mature system can fail on scope rather than on defect
- **Limitations:** does not establish that Belenios is insecure, and is not cited to that effect
- **Used by:** `CMP` §3.2 · `ACC` `AC-P16A-030` · `EVD`

---

## 5. Helios

##### `E-17` · Authors' own position on high-stakes use — Kind `P`

- **Source title:** _Helios: Web-based Open-Audit Voting_; _Electing a University President using Open-Audit Voting: Analysis of Real-World Use of Helios_
- **Author / issuing institution:** Ben Adida (2008); Adida, de Marneffe, Pereira, Quisquater (2009)
- **Version / date:** **USENIX Security 2008**; **EVT/WOTE 2009**
- **Source type:** peer-reviewed papers
- **URL / stable reference:** `http://usenix.org/event/sec08/tech/full_papers/adida/adida.pdf`; `https://csrc.nist.gov/csrc/media/events/end-to-end-voting-system-workshop/documents/papers/demarneffe_papere2e.pdf`
- **Relevant section / page:** 2008 §1, §5.1; 2009 §1
- **Property supported:** _"Helios is ideal for online software communities, local clubs, student government, and other environments where trustworthy, secret-ballot elections are required but coercion is not a serious concern."_ · _"With Helios, we do not attempt to solve the coercion problem."_ · **"UCL and the authors do not endorse the use of Helios 2.0 for large, high-stakes, governmental elections."**
- **Scope of support:** the authors' own disclaimer, cited as the first reason Helios is not a candidate; and part of the honest coercion boundary
- **Limitations:** the current Helios landing page markets it more broadly, which is **marketing and is not used as evidence**; the papers and FAQ are primary for the authors' position
- **Used by:** `CMP` §2.2, §3.3 · `BM` §3.4 · `CRB` §2.2 · `TM` §6 · `ACC` `AC-P16A-031` · `ADR` · `EVD`

##### `E-18` · Cryptographic construction by version — Kind `P`

- **Source title:** Helios papers 2008 and 2009; Helios v3 verification specifications
- **Author / issuing institution:** Ben Adida; Adida, de Marneffe, Pereira, Quisquater; Helios project
- **Version / date:** 2008; 2009; v3 specification as published
- **Source type:** peer-reviewed papers + official protocol documentation
- **URL / stable reference:** as `E-17`; `https://documentation.heliosvoting.org/verification-specs/helios-v3-verification-specs`
- **Relevant section / page:** 2008 §2, §2.1, §5.4; 2009 §2.1, §2.2
- **Property supported:** v1 was Benaloh cast-or-audit over a **Sako–Kilian mixnet**; v2+ is **exponential ElGamal with homomorphic tally** and disjunctive zero-knowledge proofs; trustee keys are _"combined via multiplication (first option chosen over threshold decryption for implementation simplicity)"_
- **Scope of support:** the lineage of the selected construction, and the origin of the n-of-n trustee limitation
- **Limitations:** historical; describes Helios, not the selected profile
- **Used by:** `CMP` §2.1, §3.3 · `EVD`

##### `E-19` · Weak Fiat–Shamir and ballot independence — Kind `P` / `I`

- **Source title:** _How Not to Prove Yourself: Pitfalls of the Fiat-Shamir Heuristic and Applications to Helios_; _Attacking and fixing Helios: An analysis of ballot secrecy_; Helios _Attacks and Defenses_
- **Author / issuing institution:** Bernhard, Pereira, Warinschi; Cortier and Smyth; Helios project
- **Version / date:** **ASIACRYPT 2012**; _Journal of Computer Security_ 21(1):89–148, 2013 (earlier CSF 2011); official docs as retrieved 2026-08-01
- **Source type:** peer-reviewed papers + official documentation + repository inspection
- **URL / stable reference:** DOI `10.1007/978-3-642-34961-4_38`; `https://members.loria.fr/VCortier/files/Papers/JCS2012-Ben.pdf`; `https://documentation.heliosvoting.org/attacks-and-defenses`; `https://github.com/benadida/helios-server`
- **Relevant section / page:** Cortier–Smyth §1.1, §3.1, §4.1; repository files `helios/crypto/algs.py`, `views.py`, `models.py`
- **Property supported:** hashing only the commitment yields unsound and unextractable proofs under adaptively chosen statements, and this manifests in Helios. The v3 challenge is `SHA1` over commitments only, and that construction is present in `helios/crypto/algs.py` on master as inspected on 2026-08-01. Ballot independence fails: an adversary replays a target's ciphertext, identifiable because the board carries voter names; the official docs record the resolution as a _"fix scheduled for Helios v3.1 through ballot structure redesign"_, and duplicate-ciphertext detection is not present in current master
- **Scope of support:** finding `F-INF-1` (ballot independence) and `F-INF-2` (weak Fiat–Shamir), which become `BM-14` and `AC-P16A-039`
- **Limitations:** the repository inspection covered `algs.py`, `views.py` and `models.py`; weeding enforced elsewhere in the stack (for example a database constraint) would not have been seen. Whether any production Helios instance uses strong Fiat–Shamir is **UNVERIFIED**
- **Used by:** `CMP` §0, §2.1, §3.3, §4 · `BM` §5, §8.2 · `ACC` `AC-P16A-031`, `AC-P16A-039`, `AC-P16A-040` · `ADR` · `EVD`

##### `E-20` · n-of-n trustees — Kind `I`

- **Source title:** `helios/crypto/algs.py`; Helios FAQ
- **Author / issuing institution:** Helios project / Ben Adida
- **Version / date:** master as inspected 2026-08-01
- **Source type:** official repository + official documentation
- **URL / stable reference:** `https://github.com/benadida/helios-server/blob/master/helios/crypto/algs.py`; `https://vote.heliosvoting.org/faq`
- **Relevant section / page:** the `decrypt` method and its in-code comment; FAQ trustee entry
- **Property supported:** trustees are **n-of-n**; the in-code comment reads _"For now, no support for threshold."_ The FAQ states _"All trustees must be involved in decryption"_
- **Scope of support:** a disqualifying availability property — one unavailable trustee makes the election untallyable
- **Limitations:** a code comment is evidence of the code's state, not of project intent
- **Used by:** `CMP` §2.1, §3.3 · `ADR` · `EVD`

##### `E-21` · Voter names published beside ciphertexts — Kind `P` / `I`

- **Source title:** _Helios: Web-based Open-Audit Voting_; Helios v3 verification specifications; _Electing a University President…_
- **Author / issuing institution:** Ben Adida; Helios project; Adida, de Marneffe, Pereira, Quisquater
- **Version / date:** 2008; v3 specification; 2009
- **Source type:** peer-reviewed papers + official protocol documentation
- **URL / stable reference:** as `E-17`, `E-18`
- **Relevant section / page:** 2008 §4.5, §5.2; v3 voter representations; 2009 §3.2
- **Property supported:** _"Helios publishes a list of voter names and corresponding encrypted votes."_ Three voter representations exist; the aliased mode is controlled per election by `use_voter_aliases` and was used for the UCL 2009 election because the bylaws required the fact of voting to be confidential
- **Scope of support:** a direct filter `F2` failure, and the surface that makes the Cortier–Smyth replay attack targetable. It is the design `BB-21`'s voter-roll prohibition explicitly rejects
- **Limitations:** aliasing is available, so this is a **default**, not an inescapable property; PACK-16A says so
- **Used by:** `CMP` §2.2, §2.4, §3.3 · `BM` §9.1 · `BB` §2.1 · `ADR` · `EVD`

##### `E-22` · The v4 fix that never shipped — Kind `P` / `I`

- **Source title:** Helios v4 specification; repository metadata
- **Author / issuing institution:** Helios project / Ben Adida
- **Version / date:** v4 specification targeted for _"release in Fall 2012"_; repository as at 2026-08-01
- **Source type:** official protocol documentation + repository metadata
- **URL / stable reference:** `https://documentation.heliosvoting.org/verification-specs/helios-v4`; `https://github.com/benadida/helios-server`
- **Relevant section / page:** v4 challenge-generation section; repository licence and commit history
- **Property supported:** the **v4 specification documents the fix** — contextual data (election UUID, trustee, question, ciphertext) incorporated into the challenge, _"preventing proof exchangeability"_. Licence Apache-2.0; the repository still receives commits, most recently Django and database housekeeping in January 2026
- **Scope of support:** finding `F-INF-2` — a corrected specification does not correct shipped code, which is why `KC-23` requires a test rather than a reading
- **Limitations:** **whether v4 ever shipped is UNVERIFIED**; the inference that it did not is stated as an inference
- **Used by:** `CMP` §3.3, §4 · `ACC` `AC-P16A-031` · `ADR` · `EVD`

---

## 6. Estonian IVXV

##### `E-23` · Official specification set and provenance — Kind `I` / `P`

- **Source title:** _IVXV protocols Specification_ (`IVXV-PR-EN-1.8.0`); _IVXV architecture_ (`IVXV-AR-EN-1.8.0`); IVXV source repository; _Improving the Verifiability of the Estonian Internet Voting Scheme_
- **Author / issuing institution:** Estonian State Electoral Office; Heiberg, Martens, Vinkel, Willemson (E-Vote-ID 2016)
- **Version / date:** both specifications **1.8.0, 01.12.2022**; paper E-Vote-ID 2016
- **Source type:** official protocol specification + official repository + peer-reviewed paper
- **URL / stable reference:** `https://www.valimised.ee/sites/default/files/2023-02/IVXV-protocols.pdf`; `.../IVXV-architecture.pdf`; `https://github.com/valimised/ivxv`; DOI `10.1007/978-3-319-52240-1_6`
- **Relevant section / page:** document headers; repository README; paper abstract
- **Property supported:** the published specification set and its versions; the repository is publication-only — _"The intention behind this repository is to make source code of the Estonian online voting system available for public review"_; the cryptographic basis _"addresses central system verification rather than end-to-end voter verification"_
- **Scope of support:** identifies the documents assessed and establishes that Estonia's own foundational paper does not claim end-to-end voter verification
- **Limitations:** **whether a specification newer than 1.8.0 exists is UNVERIFIED**; the 2023, 2024 and 2025 elections have since run
- **Used by:** `CMP` §2.3, §3.4 · `ACC` `AC-P16A-032` · `EVD`

##### `E-24` · The identity↔ciphertext binding and where it is severed — Kind `P`

- **Source title:** _IVXV protocols Specification_; _IVXV architecture_
- **Author / issuing institution:** Estonian State Electoral Office
- **Version / date:** 1.8.0, 01.12.2022
- **Source type:** official protocol specification
- **URL / stable reference:** as `E-23`
- **Relevant section / page:** protocols §4.3, §5, §8.4, §8.5; architecture §3.3
- **Property supported:** _"Before it is sent to be stored by the collector service, the encrypted ballot has to be signed digitally"_ with the national eID. Votes are stored under **`votes/<voter id>/`**. The processing application removes ballots of paper voters, selects the last vote per voter, **removes the signatures**, and emits the anonymised ballot box: _"Anonymized ballot box does not contain voter information"_
- **Scope of support:** **the decisive rejection ground for IVXV** — the pair exists in a store for the whole voting period, and anonymity is created by a trusted offline procedure rather than cryptographically. Also the source of the revoting supersession handle in the revoting analysis, and of the reason an in-person override cannot be copied into EPD²
- **Limitations:** this is a description of a lawful national system operating with legal and procedural controls around it. It establishes **incompatibility with PACK-15's structural rule**, not that IVXV is unsound on its own terms — and PACK-16A says so
- **Used by:** `CMP` §2.2, §2.4, §3.4, §4 · `BM` §9.1 · `RBL` §2.2, §5.2 · `CRB` §5.1 · `ODM` `OD-P16A-09` · `ACC` `AC-P16A-027`, `AC-P16A-032` · `ADR` · `EVD`

##### `E-25` · Encryption scheme — Kind `P`

- **Source title:** _IVXV protocols Specification_
- **Author / issuing institution:** Estonian State Electoral Office
- **Version / date:** 1.8.0, 01.12.2022
- **Source type:** official protocol specification
- **URL / stable reference:** as `E-23`
- **Relevant section / page:** §4.2
- **Property supported:** ElGamal over a 2048-bit residue class set, carrying the ballot as message with PKCS#1-style padding; SHA-256 throughout
- **Scope of support:** the comparison's construction row — a plaintext-carrying rather than exponential ElGamal, consistent with mixnet-and-decrypt rather than homomorphic tally
- **Limitations:** none material; descriptive
- **Used by:** `CMP` §2.1 · `EVD`

##### `E-26` · Shuffle proof and threshold decryption — Kind `P`

- **Source title:** _IVXV protocols Specification_; _IVXV architecture_; official Estonian i-voting FAQ
- **Author / issuing institution:** Estonian State Electoral Office
- **Version / date:** specifications 1.8.0, 01.12.2022; FAQ as retrieved 2026-08-01
- **Source type:** official protocol specification + official documentation
- **URL / stable reference:** as `E-23`; `https://www.valimised.ee/en/internet-voting/frequently-asked-questions/questions-about-reliability-i-voting`
- **Relevant section / page:** architecture §3.2, §3.4; protocols §9.1–§9.3
- **Property supported:** the shuffle proof is **Terelius–Wikström, Verificatum**, verified per _"the Verificatum verifier implementing manual"_; wide ciphertexts carry election, district, station and question alongside the ballot. The key application uses the **Desmedt–Frankel threshold scheme with Shamir secret sharing**, N ≥ 2M − 1, shares on chip cards; _"More than half of the members of the National Electoral Committee have to be present"_
- **Scope of support:** independently corroborates Verificatum's Estonian deployment (`E-31`), and is the reference for threshold custody on physical media
- **Limitations:** **the exact (M, N) values used in any election are UNVERIFIED**; no claim depends on them
- **Used by:** `CMP` §2.1, §3.4, §3.5 · `EVD`

##### `E-27` · Malleability attacks — no plaintext-knowledge proof — Kind `P`

- **Source title:** _Breaking and Fixing Vote Privacy of the Estonian E-Voting Protocol IVXV_
- **Author / issuing institution:** Johannes Müller (University of Luxembourg)
- **Version / date:** Voting'22 / **FC 2023 Workshops**, LNCS 13953
- **Source type:** peer-reviewed paper
- **URL / stable reference:** `https://orbilu.uni.lu/bitstream/10993/49442/1/main.pdf`; DOI `10.1007/978-3-031-32415-4_22`
- **Relevant section / page:** §2.3, §3.2, §3.3, §4.1, §4.3
- **Property supported:** IVXV submits a bare ciphertext with **no proof of knowledge of the plaintext**, enabling a shifting attack and an encoding attack that recover victims' votes from the published result. The vote collector _"should also not be trusted in terms of vote privacy"_. Fix: attach a NIZK proof of knowledge of plaintext and randomness
- **Scope of support:** finding `F-INF-1`, adopted directly as requirement `BM-14`. Also independently corroborates the severing step described in `E-24`
- **Limitations:** whether the attack has been patched in a version after 1.8.0 is **UNVERIFIED**; PACK-16A cites it for the requirement it generates, not to characterise Estonia's current state
- **Used by:** `CMP` §3.4, §4 · `BM` §5 · `TM` §6 · `ACC` `AC-P16A-005`, `AC-P16A-040` · `ADR` · `EVD`

##### `E-28` · Revoting and the paper override — Kind `L` / `I`

- **Source title:** _Introduction to i-voting_ (official); OSCE/ODIHR Opinion ELE-EST/527/2025
- **Author / issuing institution:** Estonian State Electoral Office; OSCE Office for Democratic Institutions and Human Rights
- **Version / date:** official page as retrieved 2026-08-01; Opinion of **17 June 2025**
- **Source type:** official documentation + intergovernmental opinion
- **URL / stable reference:** `https://www.valimised.ee/en/internet-voting/more-about-i-voting/introduction-i-voting`; `https://www.osce.org/files/f/documents/e/a/593435.pdf`
- **Relevant section / page:** official page, revoting and override sections; Opinion ¶46
- **Property supported:** _"Only the last i-vote cast is taken into account, and earlier votes are annulled."_ **From 2021** a voter may override the i-vote with a paper ballot at a polling place on election day, and the paper vote counts. Confirmed in force mid-2025 by ODIHR ¶46
- **Scope of support:** the comparator for the revoting decision and for the in-person-override analysis
- **Limitations:** **the exact Riigikogu Election Act sections are UNVERIFIED** — the official gazette was not retrievable in this session. The substance is verified from two independent official sources
- **Used by:** `CMP` §2.2, §3.4 · `RBL` §2, §5.2 · `EVD`

##### `E-28a` · Revoting defeats individual verifiability — Kind `P`

- **Source title:** _Individual Verifiability and Revoting in the Estonian Internet Voting System_
- **Author / issuing institution:** Heiberg, Krips, Willemson / Pereira (FC 2022 Workshops proceedings)
- **Version / date:** **FC 2022 International Workshops**, LNCS 13412 (2023)
- **Source type:** peer-reviewed paper
- **URL / stable reference:** DOI `10.1007/978-3-031-32415-4_21`
- **Relevant section / page:** abstract and attack description
- **Property supported:** _"We show that a compromised voter device can defeat the individual verifiability mechanism of the current Estonian voting system. Our attack takes advantage of the revoting option that is available in the Estonian voting system, and only requires to compromise the voting client application: it does not require compromising the mobile device verification app, or any server side component."_
- **Scope of support:** **the single most important input to the revoting decision** — the feature added for coercion mitigation is the attack surface that breaks the verifiability property. Also the basis of `AX-11` / §5.2 declining to _require_ a second verification device
- **Limitations:** establishes an interaction in **Estonia's** deployment. PACK-16A cites it as a general warning about the revoting/verifiability interaction, and marks that generalisation as reasoning rather than as the paper's claim
- **Used by:** `CMP` §3.4, §4 · `CRB` §5 · `RBL` §2.3 · `AXR` §1, §5.2 · `PDF` §13.1 · `ACC` `AC-P16A-060` · `ADR` · `EVD`

##### `E-28b` · Security analysis of the pre-IVXV system — Kind `I`

- **Source title:** _Security Analysis of the Estonian Internet Voting System_
- **Author / issuing institution:** Springall, Finkenauer, Durumeric, Kitcat, Hursti, MacAlpine, Halderman
- **Version / date:** **ACM CCS 2014**, 3–7 November 2014
- **Source type:** peer-reviewed paper
- **URL / stable reference:** `https://jhalderm.com/pub/papers/ivoting-ccs14.pdf`; DOI `10.1145/2660267.2660315`
- **Relevant section / page:** §3.1–§3.3, §5.1–§5.3, recommendation
- **Property supported:** documented procedural, operational and transparency failures and demonstrated client- and server-side attacks including _Ghost Click_, which waits out the verification window. Recommendation, verbatim: _"We recommend that Estonia discontinue the I-voting system."_ Also, on coercion: revoting is _"a relatively strong protection against in-person, individual coercion… More sophisticated attacks remain possible"_
- **Scope of support:** evidence on the limits of device trust and of verification windows; and a balanced assessment of revoting as a coercion control
- **Limitations:** **analyses the pre-IVXV system**, not IVXV. Estonia's substantive response was to build IVXV. **The Estonian authorities' formal response document was not located — UNVERIFIED and not cited**
- **Used by:** `CMP` §3.4 · `BM` §3.4 · `CRB` §2.2, §5 · `TM` §6 · `EVD`

##### `E-29` · Verification window and empirical take-up — Kind `I`

- **Source title:** _Checking of an i-vote_; i-voting reliability FAQ; _Statistics about Internet voting in Estonia_
- **Author / issuing institution:** Estonian State Electoral Office
- **Version / date:** as retrieved 2026-08-01
- **Source type:** official documentation and official statistics
- **URL / stable reference:** `https://www.valimised.ee/en/internet-voting/guidelines/checking-i-vote`; `.../questions-about-reliability-i-voting`; `https://www.valimised.ee/en/archive/statistics-about-internet-voting-estonia`
- **Relevant section / page:** verification guidance; FAQ Q16; statistics table
- **Property supported:** verification is possible **three times** in a short window after casting. Verified-vote share peaked at **9.9 %** (2024 European Parliament); **5.5 %** (2023 Riigikogu, 312,182 i-votes, 51.1 % of participating voters)
- **Scope of support:** the empirical ceiling on individual verifiability, used throughout PACK-16A to bound what verification can be claimed to achieve
- **Limitations:** **two official pages disagree on the window length** — _"up to three times during half an hour"_ versus _"during 15 minutes up to three times"_. The discrepancy is recorded and **not resolved**, and **no EPD² requirement depends on either figure**. The "three attempts" figure is consistent across sources
- **Used by:** `CMP` §2.2, §3.4, §4 · `BM` §11 · `BB` §5, §7 · `CRB` §4 · `AXR` §1 · `TM` §3 · `ACC` `AC-P16A-049`, `AC-P16A-051` · `ADR` · `EVD`

##### `E-40` · ODIHR Opinion on the regulation of internet voting — Estonia — Kind `L`

- **Source title:** _Opinion on the Regulation of Internet Voting — Estonia_, Opinion-Nr. **ELE-EST/527/2025**
- **Author / issuing institution:** OSCE Office for Democratic Institutions and Human Rights (ODIHR), Warsaw
- **Version / date:** **17 June 2025**
- **Source type:** intergovernmental legal opinion
- **URL / stable reference:** `https://www.osce.org/files/f/documents/e/a/593435.pdf`
- **Relevant section / page:** Recommendation I; ¶45–47; ¶65
- **Property supported:** **Recommendation I** — _"To define in the REA the legal requirements for individual verifiability and its associated coercion-resistance measures, as well as for universal verifiability."_ ¶65: individual and universal verifiability comprise _"cast-as-intended, recorded-as-cast and tallied-as-recorded without compromising the secrecy of the vote"_, and there is _"always a risk that parts of the system may not function correctly"_. ¶45–47: remote channels are more vulnerable, with particular risk in group settings _"such as care homes"_
- **Scope of support:** establishes that **deployment scale is not a compliance argument** — the largest deployment in the world still lacked a statutory definition of verifiability as of June 2025. Also supports the accessibility and coercion treatment of group settings
- **Limitations:** an ODIHR Opinion is authoritative guidance, not binding law
- **Used by:** `CMP` §2.2, §3.4 · `GLB` §7 · `CRB` §2.6 · `AXR` §6.1 · `ACC` `AC-P16A-032` · `EVD`

---

## 7. Verifiable mixnets, implementation disclosures and binding regulation

##### `E-30` · Verificatum Mix-Net and its proof of shuffle — Kind `P`

- **Source title:** _User Manual for the Verificatum Mix-Net_; _How to Implement a Stand-alone Verifier for the Verificatum Mix-Net_; _Proofs of Restricted Shuffles_; _A Commitment-Consistent Proof of a Shuffle_
- **Author / issuing institution:** Douglas Wikström / Verificatum AB; Terelius and Wikström
- **Version / date:** VMN **3.1.0, 2022-09-10**; AFRICACRYPT 2010; ACISP 2009
- **Source type:** official specification and manual + peer-reviewed papers
- **URL / stable reference:** `http://verificatum.org/files/vmnum-3.1.0.pdf`; `https://www.verificatum.org/files/vmnv-3.1.0.pdf`; DOI `10.1007/978-3-642-12678-9_7`
- **Relevant section / page:** verifier specification §1, §2.2
- **Property supported:** _"an implementation of an El Gamal-based mix-net which uses the Fiat-Shamir heuristic to produce a non-interactive universally verifiable zero-knowledge proof."_ Construction: _"the re-encryption approach of Sako and Kilian and the proof of a shuffle of Terelius and Wikström"_. A **standalone verifier specification** exists
- **Scope of support:** the leading component candidate for a future `EPD2-MIX-1`, and the model for `BB-34` — verification steps specified in prose sufficient to write an independent verifier
- **Limitations:** a mixnet is not a voting system; see `E-32`
- **Used by:** `CMP` §2.1, §3.5 · `BM` §2.3 · `BB` §6 · `ACC` `AC-P16A-033` · `EVD`

##### `E-31` · Verificatum groups, threshold model, licence and deployments — Kind `I`

- **Source title:** VMN user manual; repository licence; Verificatum product page
- **Author / issuing institution:** Douglas Wikström / Verificatum AB
- **Version / date:** VMN 3.1.0, 2022-09-10; pages as retrieved 2026-08-01
- **Source type:** official manual + repository + vendor product page
- **URL / stable reference:** `https://github.com/verificatum/verificatum-vmn/blob/master/LICENSE`; `https://www.verificatum.org/html/product_vmn.html`
- **Relevant section / page:** manual §2.1, App. B, App. H
- **Property supported:** groups: prime-order subgroups of Z*_p and standard prime-field curves (P-192…P-521, Brainpool, SECP). **k-of-n threshold**, up to 25 parties. **Licence MIT.** The vendor states use _"in real binding elections to tally more than 3,000,000 votes"_, naming Israel, Norway, Spain and Estonia
- **Scope of support:** maturity and licensing context for a possible future component
- **Limitations:** **the Estonian deployment is independently corroborated by `E-26`; Norway, Israel and Spain are vendor claims and are UNVERIFIED.** Whether a release newer than 3.1.0 exists is **UNVERIFIED**. The vendor product page is used only for the deployment claim, which is labelled as a vendor claim
- **Used by:** `CMP` §2.1, §2.3, §3.5 · `EVD`

##### `E-32` · What a mixnet does not provide — Kind `P` / `I`

- **Source title:** Verificatum standalone-verifier specification; VMN user manual; Verificatum FAQ
- **Author / issuing institution:** Douglas Wikström / Verificatum AB
- **Version / date:** 3.1.0, 2022-09-10; FAQ as retrieved 2026-08-01
- **Source type:** official specification, manual and documentation
- **URL / stable reference:** as `E-30`; `https://www.verificatum.org/html/faq.html`
- **Relevant section / page:** verifier specification §11; manual §2.3, §3
- **Property supported:** _"All of the above falls outside the scope of this document, since we cannot anticipate the scheme used to represent these objects."_ The shipped bulletin board is a convenience — _"it is easy to replace"_. FAQ: _"we do not provide complete services for electronic voting."_ And decisively: _**"WARNING! On its own the mix-net provides no protection against Pfitzmann's attack (malleability attack)."**_ README: _"this software is meant to be run in a secure environment. You are responsible for providing this environment."_
- **Scope of support:** the third instance of finding `F-INF-1`, and part of the basis for `MX-02` and for treating the board as a separate trust boundary
- **Limitations:** these are honest scope statements by the vendor, not defects
- **Used by:** `CMP` §2.1, §3.5, §4 · `BM` §2.3, §5 · `BB` §1 · `ACC` `AC-P16A-033`, `AC-P16A-040` · `ADR` · `EVD`

##### `E-33` · Swiss Post / Scytl 2019 disclosures — Kind `I`

- **Source title:** _Ceci n'est pas une preuve: The use of trapdoor commitments in Bayer-Groth proofs…_; _How not to prove your election outcome…_
- **Author / issuing institution:** Sarah Jamie Lewis, Olivier Pereira, Vanessa Teague
- **Version / date:** **11 March 2019** and **25 March 2019**
- **Source type:** independent security disclosures
- **URL / stable reference:** `https://blog.fdik.org/2019-03/UniversalVerifiabilitySwissPost.pdf`; `https://sarahjamielewis.com/evoting/HowNotToProveElectionOutcome.pdf`
- **Relevant section / page:** commitment-parameter analysis; decryption-proof analysis
- **Property supported:** the Bayer–Groth shuffle proof's Pedersen commitment parameters were _"just randomly generated without a proof of how they arose"_, and the generating routine's exponent _"is precisely the trapdoor that is needed to break the binding property of the commitment scheme"_, permitting a transcript that _"passes verification but actually alters votes"_. A second disclosure showed decryption proofs that _"verify perfectly but actually prove a decryption that is different from the true plaintext"_. Both were confirmed; the Swiss programme was suspended and the system redesigned
- **Scope of support:** finding `F-INF-3` — mixnet risk in practice is parameter-generation and integration risk — which becomes `BM-33`, `KC-19` and `MX-01`; and the rule that a verification satisfiable by a dishonest party is worse than none
- **Limitations:** concerns a system that has since been redesigned. **The current Swiss Post cryptographic documentation was not retrieved and no claim is made about the present system**
- **Used by:** `CMP` §0, §3.5, §4, §5 · `BM` §8 · `TM` §6 · `TCR` §3.2 · `ACC` `AC-P16A-024`, `AC-P16A-037`, `AC-P16A-039`, `AC-P16A-074` · `ADR` · `EVD`

##### `E-45` · Swiss Federal Chancellery Ordinance on Electronic Voting — Kind `L`

- **Source title:** _Federal Chancellery Ordinance on Electronic Voting_ (OEV / VEleS / OVotE), **SR 161.116**
- **Author / issuing institution:** Swiss Federal Chancellery (Schweizerische Bundeskanzlei)
- **Version / date:** enacted **25 May 2022**, in force **1 July 2022**
- **Source type:** binding national ordinance
- **URL / stable reference:** `https://www.fedlex.admin.ch/eli/cc/2022/336/en`; official English PDF at `https://www.fedlex.admin.ch/filestore/fedlex.data.admin.ch/eli/cc/2022/336/20220701/en/pdf-a/fedlex-data-admin-ch-eli-cc-2022-336-20220701-en-pdf-a.pdf`
- **Relevant section / page:** Art. 5(1)–(3); Art. 8; Art. 10; Art. 11; Annex No. 2.14
- **Property supported:** Art. 5(1),(3) complete verifiability — _"It must be possible to detect any manipulation that leads to a falsification of the result while preserving voting secrecy"_; Art. 5(2) individual verifiability; Art. 8 _"The trustworthy part of the system includes one or more groups of control components"_ with diverse design and independent operation; Art. 10 independent examinations commissioned by the Federal Chancellery; Art. 11 publication of source code and parameters; **Annex No. 2.14 — _"A symbolic and a cryptographic proof of compliance must demonstrate that the cryptographic protocol meets the requirements."_**
- **Scope of support:** the regulatory benchmark used so that "ready" cannot later be defined downwards; the source of `BB-28`'s organisational-independence requirement; and the basis of `RR-09` / `OD-P16A-06`, where EPD² does not meet the requirement and **says so**
- **Limitations:** **Swiss law. It does not bind EPD² and PACK-16A does not claim compliance with it.** It is used as a comparator because Germany has no equivalent for political online elections
- **Used by:** `CMP` §6 · `BM` §11 · `BB` §5.1 · `GLB` §7 · `RSM` §5 · `ODM` `OD-P16A-06` · `ACC` `AC-P16A-052`, `AC-P16A-057`, `AC-P16A-071`, `AC-P16A-084`, `AC-P16A-093` · `EVD`

---

## 8. Coercion-resistance and receipt-freeness literature

##### `E-34` · JCJ — the definition of coercion resistance — Kind `P`

- **Source title:** _Coercion-Resistant Electronic Elections_
- **Author / issuing institution:** Ari Juels, Dario Catalano, Markus Jakobsson
- **Version / date:** IACR ePrint 2002/165; **WPES 2005**; reprint in _Towards Trustworthy Elections_, LNCS 6000 (2010), pp. 37–63
- **Source type:** peer-reviewed paper
- **URL / stable reference:** `https://eprint.iacr.org/2002/165`; DOI `10.1145/1102199.1102213`; author-hosted reprint `http://www.arijuels.com/wp-content/uploads/2013/09/JCJ10.pdf`
- **Relevant section / page:** §1.1, §1.2, §2.2, §3, §4.1
- **Property supported:** the adversary may demand that a voter _"vote in a particular manner, abstain from voting, or even disclose their secret keys"_ — subsuming the randomization, forced-abstention and simulation attacks. Requires an **untappable registration channel**: _"the voter receives her credential from R via an untappable channel… For example, a voter might receive her registration through the postal service"_, plus **anonymous casting channels**. Complexity: _"the overhead for tallying authorities is quadratic in the number of voters. Thus the scheme is only practical for small elections"_
- **Scope of support:** supplies the vocabulary separating **coercion resistance** from **receipt-freeness**, on which every honest claim in `CRB` rests; and the disqualifying assumptions and complexity
- **Limitations:** the exact WPES 2005 page range is **UNVERIFIED**; text was read from the paginated author-hosted reprint
- **Used by:** `CMP` §3.6, §7 · `CRB` §1, §5 · `RBL` §2.2 · `ACC` `AC-P16A-034`, `AC-P16A-059` · `ADR` · `EVD`

##### `E-35` · Civitas — the registration assumption and its cost — Kind `P` / `I`

- **Source title:** _Civitas: Toward a Secure Voting System_
- **Author / issuing institution:** Michael R. Clarkson, Stephen Chong, Andrew C. Myers — Cornell University
- **Version / date:** **IEEE Symposium on Security and Privacy 2008**
- **Source type:** peer-reviewed paper
- **URL / stable reference:** `https://www.cs.cornell.edu/projects/civitas/papers/clarkson_civitas.pdf`
- **Relevant section / page:** §3.3, §4 (Trust Assumption 2), §5.3, §10; abstract
- **Property supported:** _"Each voter trusts at least one registration teller, and the channel from the voter to the voter's trusted registration teller is untappable."_ Fallback: _"we recommend requiring in-person registration."_ Tabulation is quadratic: _"these pairwise tests cause credential elimination to take quadratic time."_ Usability: voters may find _"generating fake credentials, storing and distinguishing real and fake credentials (especially over a long time), and lying convincingly to an adversary to be quite difficult."_ Status: _"Although not yet suitable for deployment in national elections…"_ Voters must trust their clients
- **Scope of support:** shows the untappable-channel assumption made operational, and the usability cost that makes fake-credential schemes a disenfranchisement risk for a membership including assisted voters
- **Limitations:** **no production deployment was located**, and the absence-of-deployment conclusion is stated as an inference from the authors' own non-readiness statement plus an unsuccessful search
- **Used by:** `CMP` §3.6, §7 · `CRB` §1 · `ADR` · `EVD`

##### `E-36` · Linear-time JCJ variants and their cost — Kind `P`

- **Source title:** _A New Approach towards Coercion-Resistant Remote E-Voting in Linear Time_; _Coercion-Resistant Voting in Linear Time via Fully Homomorphic Encryption_; encrypted-sorting work
- **Author / issuing institution:** Spycher, Koenig, Haenni, Schläpfer; Roenne et al.; ePrint 2023/837 authors
- **Version / date:** **FC 2011**, LNCS 7035, pp. 182–189; FC 2019/2020; ePrint 2023/837
- **Source type:** peer-reviewed papers
- **URL / stable reference:** DOI `10.1007/978-3-642-27576-0_15`; `https://arxiv.org/abs/1901.02560`; `https://eprint.iacr.org/2023/837.pdf`
- **Relevant section / page:** abstracts and complexity discussions
- **Property supported:** linear-time variants exist, but _"The improvements that have been proposed either require stronger trust assumptions or turned out to be insecure"_, and reduced complexity generally costs leakage
- **Scope of support:** closes the obvious objection that JCJ's quadratic cost is a solved problem
- **Limitations:** cited for the general trade-off; individual schemes were not read in depth
- **Used by:** `CMP` §3.6 · `EVD`

##### `E-37` · JCJ's coercion resistance is itself contested — Kind `P`

- **Source title:** _Is the JCJ voting system really coercion-resistant?_
- **Author / issuing institution:** Véronique Cortier, Pierrick Gaudry, Quentin Yang
- **Version / date:** IACR ePrint **2022/430**, April 2022
- **Source type:** peer-reviewed preprint
- **URL / stable reference:** `https://eprint.iacr.org/2022/430.pdf`
- **Relevant section / page:** cleansing-leakage analysis
- **Property supported:** _"even in the JCJ original protocol, the cleansing step leaks more than the difference Δ between the sizes of its input and output"_, letting a coercer detect disobedience; and for the linear variants _"this gain of efficiency comes with a deterioration of the coercion-resistance"_
- **Scope of support:** part of the revoting evidence base — supersession and cleansing leak whether a voter disobeyed — and the reason coercion resistance is not claimed even by reference to JCJ
- **Limitations:** a preprint; cited for its stated finding
- **Used by:** `CMP` §3.6 · `CRB` §8 · `RBL` §2.3 · `ACC` `AC-P16A-059` · `ADR` · `EVD`

##### `E-38` · Selene — tracker-based coercion mitigation — Kind `P`

- **Source title:** _Selene: Voting with Transparent Verifiability and Coercion-Mitigation_
- **Author / issuing institution:** Peter Y. A. Ryan, Peter B. Rønne, Vincenzo Iovino
- **Version / date:** **FC 2016 International Workshops**, LNCS 9604, pp. 176–192
- **Source type:** peer-reviewed paper
- **URL / stable reference:** DOI `10.1007/978-3-662-53357-4_12`; `https://orbilu.uni.lu/bitstream/10993/24802/1/SeleneEprint.pdf`
- **Relevant section / page:** abstract; tracker mechanism; limitations discussion
- **Property supported:** trackers assigned via verifiable re-encryption mixes; the α term is delivered _"only after"_ the board is posted; the voter's private key is the trapdoor for computing a fake α. Authors' framing: _"Selene will manage to mitigate such coercion attacks"_; _"targeted at low coercion threat environments"_. Stated limits: tracker collision; a coercer who demands the tracker before publication; the assumption _"that the attacker cannot monitor the communication of the α terms"_; forced abstention not covered by base Selene; receipt-freeness conditional on the casting layer. Motivation: _"many voters may not really understand the purpose of the encrypted ballot"_
- **Scope of support:** the cryptographic statement of the German lay-comprehensibility problem, and the reason Selene is `REQUIRES FURTHER RESEARCH` rather than dismissed — `OD-P16A-10`
- **Limitations:** **coercion mitigation, not resistance**, by the authors' own framing; and it relocates rather than removes the unobserved-interval assumption
- **Used by:** `CMP` §3.7, §7 · `GLB` §2.4 · `AXR` §4.1 · `CRB` §1 · `ODM` `OD-P16A-10` · `ACC` `AC-P16A-034` · `EVD`

##### `E-39` · Independent assessment of Selene — Kind `P`

- **Source title:** _Coercion Mitigation for Voting Systems with Trackers: A Selene Case Study_
- **Author / issuing institution:** Kristian Gjøsteen, Thomas Haines, Morten Rotvold Solberg
- **Version / date:** **E-Vote-ID 2023**; IACR ePrint 2023/1102
- **Source type:** peer-reviewed paper
- **URL / stable reference:** `https://eprint.iacr.org/2023/1102.pdf`
- **Relevant section / page:** definitional discussion; collision analysis
- **Property supported:** _"Coercion mitigation is weaker than coercion resistance, but may be appropriate for low-stakes elections"_; _"Selene is vulnerable to collisions among such lies"_. Successors Selene II and Hyperion address collisions
- **Scope of support:** the independent confirmation that keeps Selene's status at `REQUIRES FURTHER RESEARCH` and fixes the conditions `OD-P16A-10` must satisfy
- **Limitations:** none material for the use made of it
- **Used by:** `CMP` §3.7 · `ODM` `OD-P16A-10` · `EVD`

##### `E-42` · BeleniosRF — strong receipt-freeness — Kind `P` / `I`

- **Source title:** _BeleniosRF: A Non-interactive Receipt-Free Electronic Voting Scheme_
- **Author / issuing institution:** Pyrros Chaidos, Véronique Cortier, Georg Fuchsbauer, David Galindo
- **Version / date:** **ACM CCS 2016**, pp. 1614–1625
- **Source type:** peer-reviewed paper
- **URL / stable reference:** DOI `10.1145/2976749.2978337`; `https://eprint.iacr.org/2015/629.pdf`
- **Relevant section / page:** abstract; sRF definition; implementation notes
- **Property supported:** achieves **strong receipt-freeness (sRF)** — _"even dishonest voters cannot prove how they voted"_ — via signatures on randomizable ciphertexts, the server re-randomising each ballot; voters adopt no anti-coercion strategy. It is **not** part of the shipped Belenios software and no deployment is reported
- **Scope of support:** the most promising direction should EPD² later need receipt-freeness stronger than the selected profile provides
- **Limitations:** **receipt-freeness, not coercion resistance** — it addresses the proof channel and neither forced abstention nor credential surrender. Research prototype
- **Used by:** `CMP` §3.8 · `CRB` §7 · `ACC` `AC-P16A-034`, `AC-P16A-058` · `EVD`

##### `E-43` · VoteAgain — revoting-based coercion resistance — Kind `P` / `I`

- **Source title:** _VoteAgain: A scalable coercion-resistant voting system_
- **Author / issuing institution:** Wouter Lueks, Iñigo Querejeta-Azurmendi, Carmela Troncoso — EPFL
- **Version / date:** **29th USENIX Security Symposium (2020)**, pp. 1553–1570
- **Source type:** peer-reviewed paper
- **URL / stable reference:** `https://www.usenix.org/system/files/sec20-lueks.pdf`
- **Relevant section / page:** abstract; complexity and trust-assumption sections; implementation notes
- **Property supported:** revoting-based coercion resistance with deterministic ballot padding in **O(n log n)**. The implementation is a Python research prototype: _"We did not implement the GetToken protocol"_; the bulletin board is unimplemented. The Polling Authority is trusted for verifiability **and** coercion resistance
- **Scope of support:** the most credible attempt to make revoting a cryptographic control, which is why its failure (`E-44`) carries weight in the revoting decision
- **Limitations:** superseded by `E-44`; not cited as a viable option
- **Used by:** `CMP` §3.9 · `CRB` §1 · `EVD`

##### `E-44` · VoteAgain is broken — Kind `P`

- **Source title:** _How not to VoteAgain: Pitfalls of Scalable Coercion-Resistant E-Voting_
- **Author / issuing institution:** Johannes Müller (University of Luxembourg)
- **Version / date:** IACR ePrint **2020/1406**
- **Source type:** peer-reviewed preprint
- **URL / stable reference:** `https://eprint.iacr.org/2020/1406.pdf`
- **Relevant section / page:** attack sections; conclusion
- **Property supported:** verifiability, ballot-privacy and coercion-resistance attacks, concluding _"all voting authorities in VoteAgain need to be trusted for coercion-resistance"_. **No fix proposed**
- **Scope of support:** a direct input to the revoting decision — the most credible cryptographic revoting scheme did not survive review
- **Limitations:** a preprint; cited for its stated results
- **Used by:** `CMP` §3.9 · `CRB` §5 · `RBL` §2.3 · `ACC` `AC-P16A-060` · `ADR` · `EVD`

##### `E-46` · The remote-coercion boundary statement — Kind `P`

- **Source title:** _Public Evidence from Secret Ballots_
- **Author / issuing institution:** Bernhard, Benaloh, Halderman, Rivest, Ryan, Stark, Teague, Vora, Wallach
- **Version / date:** **E-Vote-ID 2017**; arXiv 1707.08619
- **Source type:** peer-reviewed paper
- **URL / stable reference:** `https://people.csail.mit.edu/rivest/pubs/BHRVx17.pdf`
- **Relevant section / page:** §3.2 (Privacy, Receipt Freeness, and Coercion Resistance)
- **Property supported:** _"Because remote systems enable voters to fill out their ballots outside a controlled environment, anyone can watch over the voter's shoulder… Note that if the coercer can monitor the voter throughout the vote casting period, then resistance is futile … For remote voting, we need to assume that voters will have some time when they can interact with the voting system unobserved."_
- **Scope of support:** **the single most load-bearing citation in `PACK-16A-COERCION-AND-RECEIPT-BOUNDARY.md`** — it is why coercion resistance is not claimed, and why `T-P16A-26` and `T-P16A-30` are recorded as unmitigated
- **Limitations:** a statement about remote voting generally; PACK-16A applies it to its own case and says so
- **Used by:** `CMP` §7 · `CRB` §1, §2.4 · `TM` §5 · `ACC` `AC-P16A-059` · `ADR` · `EVD`

##### `E-47` · National Academies position on internet return of ballots — Kind `L`-adjacent

- **Source title:** _Securing the Vote: Protecting American Democracy_
- **Author / issuing institution:** National Academies of Sciences, Engineering, and Medicine (United States)
- **Version / date:** **2018**
- **Source type:** national scientific academy consensus study
- **URL / stable reference:** `https://nap.nationalacademies.org/catalog/25120`
- **Relevant section / page:** Recommendation 5.11; chapter 5
- **Property supported:** _"At the present time, the Internet (or any network connected to the Internet) should not be used for the return of marked ballots… Internet voting should not be used in the future until and unless very robust guarantees of security and verifiability are developed and in place."_ On coercion: individuals voting by mail, fax or internet _"can be coerced or paid to vote for particular candidates outside the oversight of election administrators"_
- **Scope of support:** **recorded context only.** It concerns United States public elections, and EPD² is not proposing internet voting for public elections — mode F–I activation is prohibited by default. It is retained because a registry that dropped the most prominent adverse consensus position on internet voting would be a curated registry rather than a complete one
- **Limitations:** **no PACK-16A claim depends on this entry**, which is why it is defined and not cited elsewhere. It is not binding law and does not address internal association voting
- **Used by:** `EVD` only — deliberately

---

## 9. German legal, constitutional and standards sources

These entries were previously defined in `PACK-16A-GERMAN-LEGAL-BOUNDARY.md`
§9 and were consolidated here as the narrow correction. **Their content,
their scope and the conclusions drawn from them are unchanged.**

##### `E-41` · BVerfG 2 BvC 3/07 — the Wahlcomputer judgment — Kind `L`

- **Source title:** Judgment of the Second Senate, **2 BvC 3/07, 2 BvC 4/07** (joined _Wahlprüfungsbeschwerden_), officially reported at **BVerfGE 123, 39**; 163 Randnummern
- **Author / issuing institution:** Bundesverfassungsgericht, Zweiter Senat
- **Version / date:** **3 March 2009**
- **Source type:** binding constitutional judgment
- **URL / stable reference:** German `https://www.bundesverfassungsgericht.de/SharedDocs/Entscheidungen/DE/2009/03/cs20090303_2bvc000307.html`; official English `https://www.bundesverfassungsgericht.de/SharedDocs/Entscheidungen/EN/2009/03/cs20090303_2bvc000307en.html`; Pressemitteilung Nr. 19/2009
- **Relevant section / page:** Leitsätze 1–2; Rn. 106–125; Tenor
- **Property supported:** **Leitsatz 1** — _"Der Grundsatz der Öffentlichkeit der Wahl aus Art. 38 in Verbindung mit Art. 20 Abs. 1 und Abs. 2 GG gebietet, dass alle wesentlichen Schritte der Wahl öffentlicher Überprüfbarkeit unterliegen, soweit nicht andere verfassungsrechtliche Belange eine Ausnahme rechtfertigen."_ **Leitsatz 2** — _"Beim Einsatz elektronischer Wahlgeräte müssen die wesentlichen Schritte der Wahlhandlung und der Ergebnisermittlung vom Bürger zuverlässig und ohne besondere Sachkenntnis überprüft werden können."_ Rn. 109 requires citizens to verify and understand the key steps without specialist technical knowledge; Rn. 120 forbids exclusively electronic storage of cast votes; **Rn. 121 does not prohibit electronic voting** — _"The legislator is not precluded from using electronic voting machines… provided that the constitutionally required possibility of reliable scrutiny is guaranteed"_; Rn. 123–124 foreclose device certification and organisational measures as substitutes for citizen scrutiny; Rn. 125 holds that no conflicting constitutional principle justifies far-reaching restrictions on publicity. The **Tenor** struck the _Bundeswahlgeräteverordnung_, while § 35 BWG was _"verfassungsrechtlich zwar nicht zu beanstanden"_
- **Scope of support:** the constitutional frame for modes F–I; the source of `PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT`; and the lay-comprehensibility standard that makes accessibility a protocol-level requirement
- **Limitations:** **the Court decided nothing about cryptographic verifiability.** The case concerned electronic recording devices. Any statement that a cryptographic protocol is or is not BVerfG-compliant is an **extrapolation**, and `BVerfG COMPLIANT` is a prohibited claim. **Verbatim German at Rn. 109/118/120/121 should be re-checked against BVerfGE 123, 39 or juris before use in a filing** — it was retrieved here via the official English translation, which shares the paragraph numbering, and cross-checked against Deutscher Bundestag WD 3-3000-129/19
- **Used by:** `CMP` §3.7 · `GLB` §2 · `AXR` §1, §4.1 · `CRB` §8 · `BB` §3.1 · `ODM` `OD-P16A-10` · `ACC` `AC-P16A-088`…`091` · `ADR` · `EVD`

##### `E-49` · Parteiengesetz — virtual congresses and binding electronic votes — Kind `L`

- **Source title:** **Parteiengesetz (PartG)** — § 9 Abs. 1, § 15 Abs. 2, § 15 Abs. 2a; and **VMVDigG** amending **§ 32 BGB**
- **Author / issuing institution:** Deutscher Bundestag (federal legislature)
- **Version / date:** PartG as amended by the **11. PartGÄndG of 27 February 2024** (BGBl. 2024 I Nr. 70), **in force 5 March 2024**; VMVDigG **in force 21 March 2023**
- **Source type:** binding federal statute
- **URL / stable reference:** official consolidated text of the Parteiengesetz and of § 32 BGB
- **Relevant section / page:** § 9 Abs. 1; § 15 Abs. 2; § 15 Abs. 2a Nr. 1 and Nr. 2
- **Property supported:** § 15 Abs. 2a — _"Der Vorstand kann entscheiden, dass die Stimmabgabe unter Wahrung der Rechte aller Stimmberechtigten bei Beschlussfassungen und Wahlen ganz oder teilweise im Wege der elektronischen Kommunikation erfolgen kann, wenn dabei die Sicherheit, auch mit Blick auf den Schutz personenbezogener Daten, auf dem Stand der Technik gewährleistet ist… Dies gilt nicht, soweit die Satzung etwas anderes bestimmt."_ § 15 Abs. 2 requires secrecy for _Vorstandswahlen_. § 9 Abs. 1 permits _Präsenz_, **virtuelle** and two forms of **hybride** party congresses. VMVDigG made hybrid and virtual member assemblies permanently available for associations generally
- **Scope of support:** **the legal basis for modes B, D and E** — binding electronic voting is permitted for internal party resolutions and internal board elections. This is the enabling provision the whole architecture is aimed at
- **Limitations:** _"Stand der Technik"_ is **undefined** in the statute; whether it maps to BSI TR-03169, PP-0121 and TR-02102-1 is **PACK-16A's inference and no source states it** — recorded as `OD-P16A-11`. The provision **has not been tested at the BVerfG** and was enacted over the published objection at `E-55`. The verbatim current text of § 32 BGB is **UNVERIFIED**
- **Used by:** `GLB` §4.1, §4.4, §4.5, §5 · `EPM` §5 · `ODM` `OD-P16A-11` · `ACC` `AC-P16A-090` · `ADR` · `EVD`

##### `E-50` · § 17 PartG and the electoral-law delegation — Kind `L`

- **Source title:** **§ 17 PartG** — _Aufstellung von Wahlbewerbern_; **§ 21 Abs. 3 Satz 1 BWahlG**; **§ 27 Abs. 5 BWahlG**
- **Author / issuing institution:** Deutscher Bundestag (federal legislature)
- **Version / date:** PartG i.d.F. 11. PartGÄndG, in force 5 March 2024; BWahlG in the version of 7 March 2024
- **Source type:** binding federal statute
- **URL / stable reference:** official consolidated texts of the Parteiengesetz and the Bundeswahlgesetz
- **Relevant section / page:** § 17 sentences 1 and 2; § 21 Abs. 3 Satz 1; § 27 Abs. 5
- **Property supported:** § 17 — _"Die Aufstellung von Bewerbern für Wahlen zu Volksvertretungen muss in geheimer Abstimmung erfolgen. Die Aufstellung regeln die Wahlgesetze und die Satzungen der Parteien."_ § 21 Abs. 3 Satz 1 — _"Die Bewerber und die Vertreter für die Vertreterversammlungen werden in geheimer Abstimmung gewählt."_
- **Scope of support:** **the structural hinge of mode C.** Sentence 2 delegates outward to the _Wahlgesetze_, so PartG permissions do not override BWahlG requirements for candidate nomination
- **Limitations:** the statutes state the secrecy requirement; **what secrecy operationally requires comes from `E-51`**, not from the statutory text itself
- **Used by:** `GLB` §4.3, §4.4, §5 · `EPM` §5 · `FIR` §4 · `ACC` `AC-P16A-092` · `ADR` · `EVD`

##### `E-51` · Operative guidance on nomination assemblies — Kind `L`

- **Source title:** _Leitfaden Aufstellungsversammlung_ for the 2025 Bundestag election; supporting Bundestag _Wissenschaftliche Dienste_ opinion WD 3-3000-249/20, _Verfassungsrechtliche Zulässigkeit von Online-Parteitagen und elektronischen Abstimmungen_
- **Author / issuing institution:** **Die Bundeswahlleiterin** (Federal Returning Officer); Deutscher Bundestag, Wissenschaftliche Dienste
- **Version / date:** guidance **Stand September 2024**; WD opinion **28 October 2020**
- **Source type:** official operative electoral guidance + parliamentary research opinion
- **URL / stable reference:** Bundeswahlleiterin guidance PDF; `https://www.bundestag.de/resource/blob/803404/…/WD-3-249-20-pdf-data.pdf`
- **Relevant section / page:** guidance sections on assembly form, candidate presentation, electronic procedures and secrecy
- **Property supported:** _"Eine solche Versammlung setzt nach herrschender Meinung die gleichzeitige körperliche Anwesenheit der stimmberechtigten Personen an einem Ort voraus."_ · _"Elektronische Verfahren können nur zur Vorermittlung, Sammlung und Vorauswahl der Bewerbungen benutzt werden, also nur im Vorfeld und als Vorverfahren zur eigentlichen, schriftlichen mit Stimmzetteln und geheim durchzuführenden Abstimmung."_ · _"Die Gelegenheit, sich nur digital vorzustellen, genügt danach nicht."_ · _"Der Grundsatz der Öffentlichkeit der Wahl gebietet, dass alle wesentlichen Schritte der Wahl öffentlicher Überprüfbarkeit unterliegen."_ · _"Der Grundsatz der geheimen Wahl erfordert eine Abstimmung von mindestens drei Personen."_
- **Scope of support:** **mode C is prohibited for statutory nomination**; the electorate floor of three below which a secret ballot is refused (`EPM` §6.2); and the correction that the COVID-era "digital nomination with subsequent confirmation" model is **not** the current rule
- **Limitations:** this is **guidance interpreting § 21 BWahlG plus _herrschende Meinung_**, not an explicit statutory prohibition — which makes it legislatively movable. PACK-16A marks that as an inference. It is nonetheless the operative rule, and deviation risks _Zurückweisung des Wahlvorschlags_. The enacted text and expiry of the COVID-era § 52 BWahlG are **UNVERIFIED**
- **Used by:** `GLB` §4.3, §4.4, §5 · `EPM` §5, §6.2 · `CRB` §5.2 · `RBL` §5 · `FIR` §4 · `ACC` `AC-P16A-080`, `AC-P16A-092` · `ADR` · `EVD`

##### `E-52` · BSI TR-02102-1 — cryptographic recommendations — Kind `L`

- **Source title:** **BSI TR-02102-1**, _Kryptographische Verfahren: Empfehlungen und Schlüssellängen_
- **Author / issuing institution:** Bundesamt für Sicherheit in der Informationstechnik (BSI)
- **Version / date:** version **2026-01**, published **23 January 2026**
- **Source type:** official national technical guideline
- **URL / stable reference:** `https://www.bsi.bund.de/SharedDocs/Downloads/DE/BSI/Publikationen/TechnischeRichtlinien/TR02102/BSI-TR-02102.html`
- **Relevant section / page:** the guideline as a whole; companion parts TR-02102-2/-3/-4
- **Property supported:** the current German reference for cryptographic algorithms and key lengths
- **Scope of support:** named as the baseline PACK-16B must justify its parameter choices against, including any divergence from the selected specification's fixed integer-group parameters — `KC-21`, `KC-22`, `OD-P16A-03`
- **Limitations:** **PACK-16A does not assess the selected parameters against it and does not assume the answer.** The guideline's stated validity horizon was not read — **UNVERIFIED**
- **Used by:** `GLB` §3 · `BM` §8.1 · `TCR` §6 · `ODM` `OD-P16A-03` · `ACC` `AC-P16A-055` · `ADR` · `EVD`

##### `E-53` · BSI protection profiles for online voting products — Kind `L`

- **Source title:** **BSI-CC-PP-0037-2008**, _Basissatz von Sicherheitsanforderungen an Online-Wahlprodukte_, v1.0; **BSI-CC-PP-0121-2024**, _Common Criteria Protection Profile for E-Voting Systems for non-political Elections_, v1.0
- **Author / issuing institution:** Bundesamt für Sicherheit in der Informationstechnik (BSI)
- **Version / date:** PP-0037 certified **21 May 2008**, EAL2+ — **ARCHIVED**; PP-0121 certified **20 February 2024**, EAL4+ ALC_FLR.2, CC:2022 R1, **valid to 19 February 2034**
- **Source type:** official Common Criteria protection profiles
- **URL / stable reference:** `https://www.bsi.bund.de/SharedDocs/Zertifikate_CC/PP/Archiv/PP_0037.html`; `https://www.bsi.bund.de/SharedDocs/Zertifikate_CC/PP/aktuell/PP_0121.html`
- **Relevant section / page:** certification metadata; archive status text
- **Property supported:** PP-0037 is _"ein archiviertes Schutzprofil, welches nicht mehr grundsätzlich für Produktzertifizierungen zu Verfügung steht"_. PP-0121 is the **current** profile and is scoped to **non-political** elections
- **Scope of support:** corrects the common error of citing PP-0037 as current; and establishes that the applicable German profile covers exactly the class of election this architecture targets
- **Limitations:** **no explicit withdrawal date is published for PP-0037 — UNVERIFIED.** The scope of the related **BSI-CC-PP-0122-2024 is UNVERIFIED** and no claim depends on it. **Nothing in EPD² is certified, no certification has been sought, and `BSI CERTIFIED` is a prohibited claim**
- **Used by:** `GLB` §3, §5 · `CRB` §8 · `EVD`

##### `E-54` · BSI technical guidance scoped to non-political elections — Kind `L`

- **Source title:** **BSI TR-03169**, _IT-sicherheitstechnische Anforderungen zur Durchführung von nicht-politischen Online-Wahlen und -Abstimmungen_; _Ende-zu-Ende Verifizierbare Onlinewahlen: Handlungsleitfaden für Wahlorganisatoren_; the BSI Online-Wahlen portal
- **Author / issuing institution:** Bundesamt für Sicherheit in der Informationstechnik (BSI)
- **Version / date:** TR-03169 published 2023, page last updated 2024 (**version number UNVERIFIED**); Handlungsleitfaden **25 April 2025**
- **Source type:** official national technical guidance
- **URL / stable reference:** `https://www.bsi.bund.de/DE/Themen/Unternehmen-und-Organisationen/Standards-und-Zertifizierung/Technische-Richtlinien/TR-nach-Thema-sortiert/tr03169/TR-03169_node.html`; the BSI Online-Wahlen portal
- **Relevant section / page:** scope statements; portal scope line
- **Property supported:** the guidance scope is _"Bei der Durchführung von **nicht-politischen** Abstimmungen und Wahlen"_, and both TR-03169 and PP-0121 carry _nicht-politisch_ in their titles. The E2E-verifiability guidance explicitly addresses _Ende-zu-Ende-Verifizierbarkeit_
- **Scope of support:** **the structural finding that there is no German technical baseline for political online elections, and that the exclusion is deliberate** — which is why modes F–I are prohibited by default and why the framework that does exist is the one covering internal party votes
- **Limitations:** **the TR-03169 version number is UNVERIFIED**, as is its stated relationship to the archived PP-0037. The body of the Handlungsleitfaden was not read in full
- **Used by:** `GLB` §3, §5, §7 · `ODM` `OD-P16A-11` · `CRB` §8 · `ADR` · `EVD`

##### `E-55` · The constitutional objection to § 15 Abs. 2a PartG — Kind `L`

- **Source title:** _Stellungnahme zum Gesetz zur Änderung des Parteiengesetzes_, Ausschussdrucksache **20(4)340-A**; government bill BT-Drs. **20/9147**
- **Author / issuing institution:** **Prof. Dr. Sophie Schönberger**, Institut für Deutsches und Internationales Parteienrecht und Parteienforschung (PRuF), Heinrich-Heine-Universität Düsseldorf; Deutscher Bundestag
- **Version / date:** Stellungnahme **20 November 2023**; bill **7 November 2023**
- **Source type:** expert opinion submitted to a parliamentary committee
- **URL / stable reference:** `https://www.bundestag.de/resource/blob/979344/…/20-4-340-A.pdf`; `https://dserver.bundestag.de/btd/20/091/2009147.pdf`
- **Relevant section / page:** assessment of Art. 1 Nr. 1 and Nr. 2
- **Property supported:** the provision is assessed as _"verfassungsrechtlich als auch verfassungspolitisch höchst problematisch"_, with the core objection: _"bei elektronischen Abstimmungssystemen ohne Kenntnis und Verständnis des verwandten Algorithmus die konkrete Abstimmungssituation nicht nachvollzogen werden kann."_
- **Scope of support:** **directive rather than defensive** — it is the BVerfG Rn. 109 argument transposed into party law, and it makes lay-comprehensible verifiability a design constraint answering the strongest published objection to the architecture's own legal basis
- **Limitations:** an expert opinion, not a judgment. The provision **was enacted over it** and remains in force; it has not been tested at the BVerfG
- **Used by:** `GLB` §4.2 · `AXR` §1, §4.1 · `ODM` `OD-P16A-10` · `ACC` `AC-P16A-088`, `AC-P16A-089` · `EVD`

##### `E-56` · Council of Europe Recommendation CM/Rec(2017)5 — Kind `L`

- **Source title:** _Recommendation CM/Rec(2017)5 of the Committee of Ministers to member States on standards for e-voting_, with Explanatory Memorandum and Guidelines
- **Author / issuing institution:** Council of Europe, Committee of Ministers
- **Version / date:** adopted **14 June 2017**, at the 1289th meeting of the Ministers' Deputies; replaces Rec(2004)11
- **Source type:** intergovernmental recommendation (soft law)
- **URL / stable reference:** `https://rm.coe.int/1680726f6f`; Explanatory Memorandum `https://rm.coe.int/168071bc84`
- **Relevant section / page:** Standards 1, 2, 3, 10, 15, 17, 18, 19, 23, 24, 25, 26, 27, 30, 31; EM ¶45, ¶70, ¶82–83
- **Property supported:** Standard 1 — the interface _"shall be easy to understand and use by all voters"_; Standard 3 — remote e-voting _"shall be only an additional and optional means of voting"_ unless universally accessible; Standard 15 — the voter shall be able to verify; **Standard 23 — _"An e-voting system shall not provide the voter with proof of the content of the vote cast for use by third parties"_**; Standard 24 — no disclosure of counts before closure; **Standard 25 — the secrecy of previous choices recorded and erased before the final vote must be respected**; Standard 18 — sound evidence that only eligible voters' votes are included; Standard 27 — introduce e-voting _"in a gradual and progressive manner"_; Standard 30 — any observer shall be able to observe the count
- **Scope of support:** the receipt-freeness requirement (`BM-03`); the tension between Standards 15, 23 and 25 that shapes the whole receipt boundary; `SU-04` binding any future supersession; the additional-channel posture; and the gradual sequencing that PACK-16A…D applies
- **Limitations:** **a Recommendation — soft law, not binding.** PACK-16A records honestly that **Standard 18 is only partially met**, because ballot-level eligibility verifiability would require the link this architecture forbids
- **Used by:** `GLB` §6 · `CRB` §3, §5 · `AXR` §1, §7 · `RBL` §2.1, §3.4 · `EPM` §3 · `ACC` `AC-P16A-048`…`051`, `AC-P16A-054`, `AC-P16A-058`, `AC-P16A-063`, `AC-P16A-088` · `ADR` · `EVD`

---

## 10. Reserved Evidence IDs

##### `E-48` · **RESERVED / INTENTIONALLY UNUSED**

- **Source title:** — (no source)
- **Author / issuing institution:** —
- **Version / date:** —
- **Source type:** **reserved identifier**
- **URL / stable reference:** —
- **Relevant section / page:** —
- **Property supported:** **none**
- **Scope of support:** **none**
- **Limitations:** Reserved during PACK-16A source consolidation. **No substantive claim relies on `E-48`.** The identifier must not be reused without an explicit registry update recording what it was assigned to and by which round
- **Used by:** nothing, and nothing may cite it

**Why the gap was not closed by renumbering.** `E-49` … `E-56` are cited
across eight documents. Renumbering them to remove a one-slot gap would
produce reference churn across the whole pack for no informational gain,
and every renumbering is an opportunity to mis-point a legal citation. The
slot is therefore recorded as reserved and left where it is.

---

## 11. Cross-cutting findings

Three findings emerge from the sources above rather than from any single
one of them. Each is marked `INF` because **no source states it in this
form**, and each became a binding requirement rather than a remark.

| ID        | Finding                                                                                                                                                                                                                                                           | Kind  | Grounded in            | Became                                                     |
| --------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----- | ---------------------- | ---------------------------------------------------------- |
| `F-INF-1` | **Ballot independence is the recurring systemic failure of deployed verifiable voting systems.** A submitted ciphertext with no proof of knowledge of its plaintext is malleable, and malleability is a privacy attack, not merely an integrity one               | `INF` | `E-19`, `E-27`, `E-32` | `BM-14`                                                    |
| `F-INF-2` | **Weak Fiat–Shamir recurs in production code across independent projects and survives its own published fix.** Found in Helios in 2012, found again in Swiss Post/Scytl in 2019, and present in Helios master in 2026 despite a v4 specification that corrects it | `INF` | `E-19`, `E-22`, `E-33` | `AC-P16A-039`, `KC-23`                                     |
| `F-INF-3` | **Mixnet risk in practice is parameter-generation and integration risk, not proof-system risk.** The proof system was sound in the case where a transcript could pass verification while altering votes; the flaw was in how the commitment parameters arose      | `INF` | `E-33`, `E-30`, `E-32` | `BM-33`, `KC-19`, `MX-01`, and no mixnet profile activated |

---

## 12. Contradictions between sources — shown, not hidden

| #   | Contradiction                                                                                                                                                                                                                                | Treatment                                                                                                                                                                          |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Estonia's official pages state the i-vote verification window as **30 minutes** and as **15 minutes** (`E-29`)                                                                                                                               | **Not resolved.** Both are official. Recorded; **no EPD² requirement depends on either figure**                                                                                    |
| 2   | Helios's landing page markets it for _"your book club… or state"_, while the FAQ and both defining papers advise against high-stakes and governmental use (`E-17`)                                                                           | The **papers and FAQ are primary** for the authors' position; the landing page is marketing and is not used as evidence                                                            |
| 3   | ElectionGuard release-page dates rendered inconsistently against the specification title page (`E-01`)                                                                                                                                       | The **title-page date (2024-08-12)** is used; release-page dates are treated as **UNVERIFIED**                                                                                     |
| 4   | Belenios publishes a **3.0** specification while deploying **3.1**, and the caveats document is titled for 3.1 (`E-10`, `E-15`)                                                                                                              | Both facts recorded; the version gap is itself cited as a maturity finding, and **no 3.1-only property is asserted**                                                               |
| 5   | ElectionGuard claims confirmation codes do not enable coercion _in properly deployed in-person applications_, while also stating that a party able to decrypt individual ballots can coerce by demanding confirmation codes (`E-05`, `E-06`) | **Not a contradiction — a conditional.** The in-person qualifier is load-bearing and does **not** transfer to EPD²'s remote deployment; `CRB` treats the remote case independently |

**No EPD² security claim is created to resolve a contradiction between
external sources.** Where sources disagree, the disagreement is the
finding.

---

## 13. Registry integrity

Verifiable by re-running the extraction described in
`PACK-16A-HANDOVER.md` §5.2.

```text
canonical evidence registries ................. 1   (this file)
substantive evidence definitions .............. 59
reserved IDs .................................. 1   (E-48)
allocated Evidence IDs ........................ 60
highest Evidence ID ........................... E-56
duplicate definitions ......................... 0
conflicting definitions ....................... 0
IDs with two different sources ................ 0
unique references resolved .................... 58
unresolved references ......................... 0
orphaned references ........................... 0
definitions not cited elsewhere ............... 1   (E-47, deliberate — §8)
IDs defined outside this file ................. 0
```

A **definition** is an entry heading in this file. A **reference** is a
`[E-nn]` citation in any PACK-16A document or in `ADR-099`. A **mention**
of an identifier in prose is neither, and creates no definition.

---

## 14. Source list

Primary specifications and papers: ElectionGuard Design Specification
2.1.0; ElectionGuard USENIX Security 2024; Belenios specification 3.0;
Belenios _Known caveats of Belenios 3.1_ (28 April 2025); Belenios FAQ and
project pages; Cortier–Drăgan–Dupressoir–Warinschi CSF 2018; SSTIC 2024
certification-campaign paper; Adida USENIX Security 2008; Adida–de
Marneffe–Pereira–Quisquater EVT/WOTE 2009; Helios v3 and v4 verification
specifications and _Attacks and Defenses_; Cortier–Smyth JCS 2013;
Bernhard–Pereira–Warinschi ASIACRYPT 2012; IVXV protocols and architecture
1.8.0; Heiberg et al. E-Vote-ID 2016; Springall et al. CCS 2014; Müller
Voting'22/FC 2023; FC 2022 Workshops LNCS 13412; Verificatum VMN user
manual and standalone-verifier specification 3.1.0; Terelius–Wikström
AFRICACRYPT 2010; Lewis–Pereira–Teague March 2019 disclosures;
Juels–Catalano–Jakobsson; Clarkson–Chong–Myers IEEE S&P 2008;
Cortier–Gaudry–Yang ePrint 2022/430; Ryan–Rønne–Iovino FC 2016;
Gjøsteen–Haines–Solberg E-Vote-ID 2023; Chaidos–Cortier–Fuchsbauer–Galindo
CCS 2016; Lueks–Querejeta-Azurmendi–Troncoso USENIX Security 2020; Müller
ePrint 2020/1406; Bernhard et al. _Public Evidence from Secret Ballots_;
National Academies _Securing the Vote_ (2018).

Legal, constitutional and standards sources: BVerfG 2 BvC 3/07 (`E-41`);
Swiss OEV/VEleS SR 161.116 (`E-45`); OSCE/ODIHR ELE-EST/527/2025 (`E-40`);
Parteiengesetz and VMVDigG (`E-49`); § 17 PartG and §§ 21(3), 27(5) BWahlG
(`E-50`); Bundeswahlleiterin _Leitfaden Aufstellungsversammlung_ and
Bundestag WD opinion (`E-51`); BSI TR-02102-1 (`E-52`); BSI-CC-PP-0037 and
BSI-CC-PP-0121 (`E-53`); BSI TR-03169 and E2E-verifiability guidance
(`E-54`); Schönberger Stellungnahme 20(4)340-A (`E-55`); Council of Europe
CM/Rec(2017)5 (`E-56`).

**No source in this registry is marketing material, and no conclusion in
PACK-16A rests on an UNVERIFIED item.**
