# PACK-16A — Ballot Model Specification

**Round:** PACK-16A — Verifiable Voting Protocol and Ballot Model Selection. **Specification and ADR only. No code. Not implemented. Not an implementation candidate. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**Baseline:** `EPD2_PACK-15_VOTING_TRUST_BOUNDARY_ELIGIBILITY_CREDENTIAL_SEPARATION_0.15.0_FINAL_PASS.zip`
**ADR:** `ADR-099`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

Evidence references `[E-nn]` resolve in
`PACK-16A-PROTOCOL-EVIDENCE-MATRIX.md`.

---

## 1. The selection

```text
RECOMMENDED PROTOCOL FAMILY
  Homomorphic encrypted ballots with exponential ElGamal,
  threshold distributed key generation and decryption,
  non-interactive zero-knowledge well-formedness proofs,
  and Benaloh cast-or-challenge,
  in the lineage specified by the ElectionGuard Design Specification 2.1.0.

RECOMMENDED BOUNDED EPD² PROFILE
  EPD2-HOM-1
```

**What is selected is a specification, not a library.** The distinction is
load-bearing: there is currently **no production-grade implementation of
ElectionGuard 2.1** `[E-10a]`, and selecting a codebase from here would be
selecting the least mature of the available options. What PACK-16A selects
is the cryptographic construction, its proof obligations and its published
verifier requirements. The library question is `OD-P16A-04`, owned by
PACK-16D, and is subject to the rule in §8.2.

### 1.1 Why this family, in one paragraph

ElectionGuard's most-cited limitation is that it does no eligibility and no
authentication, and requires that these be established outside it — asking
only that interested parties be able to confirm that the number of ballots
cast does not exceed the number of voters entitled `[E-06]`. For every
other integrator that is a gap. For EPD² it is a description of the
interface PACK-15 spent an entire round building: eligibility settled on
the far side of a trust boundary, one artifact crossing, no shared
per-participation reference, and an aggregate count as the only figure the
two sides may share. The boundary and the protocol were designed
independently, by people who did not know about each other, and they meet
without either being bent. That is the argument.

The supporting reasons: a homomorphic-only tally never decrypts an
individual ballot, which removes the preference-pattern channel entirely
and satisfies filter `F5` structurally rather than by policy; cast-or-
challenge is core to the design rather than added to it `[E-05]`; threshold
guardians with a quorum make `NO SINGLE-ADMIN DECRYPTION` a property of the
construction rather than of an access-control list `[E-04]`; the verifier
requirements are published as a specification section so that an
independent verifier can be written without reading anyone's code `[E-09]`;
and the licence is MIT `[E-10a]`, which creates no dependency on the
unresolved `FIR-OSS-*` licensing work.

### 1.2 What is deliberately not selected here

```text
NO specific group, curve or key size          → PACK-16B
NO specific hash function                     → PACK-16B
NO specific cryptographic library             → PACK-16D (OD-P16A-04)
NO specific HSM                               → PACK-16B
NO specific production key provider           → PACK-16B
NO deployment implementation                  → PACK-16D
NO guardian count or quorum value             → PACK-16B
```

---

## 2. Profiles

EPD²'s election types do not fit one cryptographic profile, and pretending
they do would produce the hidden universal hybrid this round is required to
refuse. **Two profiles are defined. Exactly one is selected for
architectural review. The other is defined so that it cannot be reached by
accident.**

| Profile      | Purpose                                                                | Tally           | Status after PACK-16A                                  | Activation rule                                              |
| ------------ | ---------------------------------------------------------------------- | --------------- | ------------------------------------------------------ | ------------------------------------------------------------ |
| `EPD2-HOM-1` | Cardinal ballots — yes/no, single choice, n-of-m, approval, multi-seat | **Homomorphic** | **SELECTED FOR ARCHITECTURAL REVIEW**                  | Governance gate (`PACK-16A-GERMAN-LEGAL-BOUNDARY.md` §8)     |
| `EPD2-MIX-1` | Ordinal ballots — ranked choice, STV, Condorcet, Majority Judgment     | **Mixnet**      | **DEFINED, NOT SELECTED, PROHIBITED PENDING RESEARCH** | May not be activated; requires its own ADR and its own round |

### 2.1 The separation rule

Each profile has a separate purpose, a separate threat assessment, its own
compatible ballot types, its own tally method and its own explicit
activation rule.

```text
A voting context declares exactly one profile.
A voting context may not change profile after `configured`.
A context may not contain contests from two profiles.
No profile is inferred from ballot content.
An unrecognised or unactivated profile is refused at configuration time,
  with VOTING_PROFILE_NOT_ACTIVATED, not defaulted.
```

**There is no hybrid profile and none may be created without a new ADR.**
The prohibition exists because a hybrid is how a mixnet's individual-ballot
decryption gets into a context that was assessed as homomorphic.

### 2.2 Why `EPD2-MIX-1` is defined but prohibited

A mixnet profile is the only route to ranked ballots — ElectionGuard does
not support them `[E-08]`, and Belenios supports them only by publishing
decrypted individual ballots after shuffling `[E-12]`. That publication is
the problem, and it is worse for EPD² than for a national election:

1. **Preference patterns are quasi-identifiers in small bodies.** A body of
   nineteen members ranking seven candidates produces 5,040 possible
   orderings. A published set of nineteen distinct orderings, in a group
   whose members know each other's opinions, is not anonymous. PACK-15
   §19.4 already recognises the class; `disclosure_min_cell = 5` cannot
   protect a ranked ballot because the ballot _is_ the cell.
2. **It creates a signature channel usable for coercion.** A coercer who
   dictates an unusual full ranking can look for it in the published
   output. This is the classic Italian attack, and a mixnet does not
   prevent it — the mixnet hides _who_, and the ranking supplies it back.
3. **Mixnet risk in practice is parameter-generation and integration
   risk** (`F-INF-3`, `[E-33]`), which is precisely the risk EPD² is least
   equipped to carry today.

`EPD2-MIX-1` is therefore documented — its requirements, its residual risks
and its conditions — so that the eventual decision is taken against a
written standard rather than reinvented. **It is not selected and may not
be activated.** Its owning stage is a future round, and
`PACK-16A-OPEN-DECISIONS.md` `OD-P16A-02` carries it.

### 2.3 `EPD2-MIX-1` — recorded requirements, not authorisation

Should a later round consider it, these are the minimum conditions
established now, so that they cannot be softened later:

| ID      | Condition                                                                                                                             |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| `MX-01` | A published, independently reproducible provenance for every commitment and group parameter, with a proof of how it arose (`F-INF-3`) |
| `MX-02` | A proof of knowledge of the plaintext on submission — mixnets provide no ballot independence on their own `[E-32]`                    |
| `MX-03` | k-of-n independent mix servers under distinct organisational control, with a standalone verifier specification                        |
| `MX-04` | A minimum electorate size below which the profile is refused, derived from the ballot's cardinality, not a fixed constant             |
| `MX-05` | An explicit assessment of the pattern-signature channel for the specific ballot type, published with the context                      |
| `MX-06` | Its own ADR, its own threat model and its own acceptance matrix                                                                       |

---

## 3. `EPD2-HOM-1` — the ballot

### 3.1 Structure, at specification level

```text
EncryptedBallot
  BallotId                    ElectionManifestReference
  ProfileIdentifier           CryptographicParameterReference
  Contest[]                   BallotWellFormednessProof[]
  ConfirmationCode            DeviceInformationReference
  SubmissionClass             BallotStatus

Contest
  ContestId                   SelectionLimit
  OptionSelectionLimit        EncryptedSelection[]
  ContestSumProof             ContestId-scoped proofs
```

### 3.2 Prohibited content — normative

An encrypted ballot, its proofs, its confirmation code, its board entry and
every record derived from any of them **must not contain**, in any field,
in any encoding, in any extension, and not in a form from which they can be
derived:

```text
account ID · person record ID · membership ID · member number · email
phone · name · date of birth · address · communication persona
any persistent cross-context subject identifier
any context-scoped pseudonym
any eligibility reference · any eligibility decision reference
any assertion identifier or nonce
any voting credential identifier
any continuation-capability reference
any request ID, correlation ID, trace ID or idempotency key
   originating on the identity side
any device fingerprint
any network address
any uncoarsened timestamp
```

**The prohibition is on derivability, not on field names.** PACK-15 §10.2's
formulation applies unchanged: a hash of the credential identifier is the
credential identifier.

### 3.3 The identifier rules that discharge the inherited invariants

| ID      | Rule                                                                                                                                                                                     | Discharges                                                                |
| ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| `BM-01` | `BallotId` is generated **inside the Voting Client**, from client-side randomness, independently of any value received from the identity side                                            | `NO CREDENTIAL ID AS BALLOT ID`, `NO CONTINUATION REFERENCE AS BALLOT ID` |
| `BM-02` | No component may compute `BallotId` from, or verify it against, a continuation reference or credential identifier                                                                        | `CC-03`, `CC-04`                                                          |
| `BM-03` | `ConfirmationCode` is derived **only** from the ballot's own encryptions and the election's extended base hash                                                                           | `NO RECEIPT THAT REVEALS CHOICE`                                          |
| `BM-04` | No store, log, metric, backup, export or audit stream holds a `BallotId` and any identity-side reference together                                                                        | PACK-15 §3 structural rule                                                |
| `BM-05` | `BallotId` uniqueness is enforced on the board; a duplicate is **rejected**, never silently overwritten                                                                                  | `NO SILENT BALLOT REPLACEMENT`                                            |
| `BM-06` | The order of ballots on the board is **canonical by board sequence**, not by arrival time, and the board publishes no arrival timestamp finer than the context's `timestamp_granularity` | order-of-arrival correlation                                              |

### 3.4 Ballot secrecy — what is claimed and under which assumptions

**Claimed:** an individual ballot's content is not disclosed to any party,
at any time, in the `EPD2-HOM-1` profile, because **no individual ballot is
ever decrypted**. Only the homomorphic aggregate is decrypted, and only
after closure, and only by a quorum of trustees.

**Assumptions this rests on, stated because a claim without its assumptions
is a marketing statement:**

| #   | Assumption                                                                     | If it fails                                                  | Owner        |
| --- | ------------------------------------------------------------------------------ | ------------------------------------------------------------ | ------------ |
| 1   | Fewer than the quorum of trustees collude                                      | Individual ballots become decryptable                        | PACK-16B     |
| 2   | The voting client encrypts what the voter selected                             | Cast-as-intended fails; challenge is the detection mechanism | PACK-16C     |
| 3   | The cryptographic parameters are correctly generated and published             | The construction can be silently subverted (`F-INF-3`)       | PACK-16B     |
| 4   | The board does not present divergent views                                     | Recorded-as-cast fails; mirrors are the detection mechanism  | PACK-16C     |
| 5   | The electorate is large enough that an aggregate is not a per-person statement | Small-cell disclosure                                        | Governance   |
| 6   | The voter's device is not compromised                                          | Choice may leak locally; **no cryptography addresses this**  | out of scope |

Assumption 6 is stated flatly because every system in the comparison has
the same limit and two of them say so in their own documentation `[E-17]`,
`[E-28b]`.

---

## 4. Cast as intended — challenge / spoil

**Decision: challenge/spoil is REQUIRED and is available in every context
using `EPD2-HOM-1`. It may not be disabled by configuration or by a feature
flag** (`FIR-INV-006`).

```text
The client encrypts the selections and commits to the confirmation code.
The voter is then offered exactly two mutually exclusive options:
    CAST      — the ballot is submitted and never decrypted individually
    CHALLENGE — the ballot is opened, published as spoiled, never tallied
A challenged ballot is spoiled by the act of challenging it.
After a challenge the voter prepares a fresh ballot.
```

| ID      | Requirement                                                                                                                              |
| ------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `BM-07` | The commitment to the confirmation code precedes the cast/challenge choice; a client that learns the choice first can cheat undetectably |
| `BM-08` | Cast and challenge are mutually exclusive and irreversible; there is no "challenge after casting"                                        |
| `BM-09` | A spoiled ballot is published with its opening, is marked `spoiled` on the board, and is **excluded from the tally by construction**     |
| `BM-10` | The number of challenges is not published before closure, and per-context challenge counts are subject to disclosure control             |
| `BM-11` | Challenging must be **as easy as casting** in the interface, must not be presented as an error path, and must not warn or discourage     |
| `BM-12` | A voter may challenge more than once; a per-voter challenge limit is prohibited, because a limit is a ceiling on the device check        |
| `BM-13` | The challenge explanation must be comprehensible without cryptographic knowledge (`PACK-16A-ACCESSIBILITY-REQUIREMENTS.md` §4)           |

`BM-11` and `BM-12` exist because challenge is the _only_ cast-as-intended
mechanism in this profile, and a mechanism that is discouraged or capped is
a mechanism that is not used. `BM-10` exists because a live challenge rate
is operational data that correlates with a specific context's activity, and
`ADR-094` governs it.

**Honest limitation.** Challenge detects a cheating encryption device
**probabilistically and in aggregate**. A device that cheats on one ballot
in a hundred is likely to be caught across an electorate and unlikely to be
caught by any individual voter. This is a property of the mechanism, not a
deficiency of this implementation, and it is stated in
`PACK-16A-COERCION-AND-RECEIPT-BOUNDARY.md` §4 in the words a participant
should be told.

---

## 5. Recorded as cast

| ID      | Requirement                                                                                                                                      |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| `BM-14` | **Every submitted ballot carries a non-interactive proof of knowledge of its plaintext and randomness.** A bare ciphertext is not accepted       |
| `BM-15` | Every contest carries well-formedness proofs: per-selection range proofs and a contest-sum proof against the declared selection limit            |
| `BM-16` | Proof verification is performed **before acceptance**, and a ballot failing any proof is rejected with a distinct reason code, never repaired    |
| `BM-17` | An accepted ballot is published on the board with its proofs and its confirmation code, within the board's stated publication bound              |
| `BM-18` | The voter can confirm the presence of their confirmation code on the board through a **Verification Client on a separate origin**                |
| `BM-19` | Absence of a confirmation code from the board is a **first-class outcome** with its own reason code and its own dispute path, not a support case |

**`BM-14` is the direct consequence of finding `F-INF-1`.** Cortier–Smyth
on Helios `[E-19]`, Müller on IVXV `[E-27]` and Verificatum's own Pfitzmann
warning `[E-32]` are three instances of the same gap: a ciphertext admitted
without a proof of knowledge of its plaintext is malleable, and malleability
is a privacy attack. Two nationally or widely deployed systems learned this
from outside researchers years after deployment. EPD² adopts it as a
requirement at specification time, which costs nothing now and cannot be
retrofitted cheaply.

**`BM-05` plus `BM-14` together give ballot independence**: duplicates are
rejected rather than counted, and a copied ciphertext cannot be resubmitted
by a party who does not know its plaintext.

---

## 6. Tallied as recorded, and the no-intermediate-tally discharge

```text
Ballots on the board  →  homomorphic aggregation per contest
                      →  trustee quorum produces decryption shares
                      →  shares combined; aggregate decrypted
                      →  aggregate, proofs and shares published
```

No individual ballot is decrypted at any point in this path.

| ID      | Requirement                                                                                                                                        |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| `BM-20` | Aggregation is over the **published, accepted** ballot set only, and the set is fixed by a signed board checkpoint at closure                      |
| `BM-21` | Decryption is bound to context status `voting_closed`; there is no operation that decrypts before it, and none may be added                        |
| `BM-22` | Decryption requires a quorum of trustees; **no single principal may hold a quorum**, and no break-glass, incident or emergency path may create one |
| `BM-23` | Every decryption share carries a verifiable proof; a share failing verification halts the tally rather than being excluded silently                |
| `BM-24` | The published tally artifacts are sufficient for an **independent verifier written by a party other than EPD²** to check the result end to end     |
| `BM-25` | A ballot excluded from the tally is excluded with a **published privacy-safe reason code**, and the exclusion is visible in append-only evidence   |

### 6.1 Discharging `NIT-01` … `NIT-07`

| Requirement from scope §6.1 | Discharged by                                                                                           |
| --------------------------- | ------------------------------------------------------------------------------------------------------- |
| `NIT-01`                    | `BM-15`, `BM-16` — proofs verify against ciphertext and yield a boolean, not a count                    |
| `NIT-02`                    | Same; verification is per-ballot and per-contest and produces no aggregate                              |
| `NIT-03`                    | `BM-21` — no partial decryption exists before closure; the decryption ceremony has no pre-closure entry |
| `NIT-04`                    | Permitted-signal list; PACK-12 disclosure control at `disclosure_min_cell = 5`; `BM-10`                 |
| `NIT-05`                    | `BM-22` — threshold, not access control                                                                 |
| `NIT-06`                    | `FIR-INV-006`; a flag capable of relaxing `BM-21` or `BM-22` may not exist                              |
| `NIT-07`                    | `BM-09` — a spoiled ballot carries no participation and no outcome, and `spoiled` is absorbing          |

---

## 7. Software independence

**Objective, specified; not demonstrated.** A system is software-independent
when an undetected change or error in its software cannot cause an
undetectable change or error in the outcome.

| ID      | Requirement                                                                                                                             |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| `BM-26` | The published election record must be sufficient to verify the outcome **without trusting any EPD² component**                          |
| `BM-27` | The verifier's checks must be specified in prose sufficient to write an independent verifier, following the model of `[E-09]`, `[E-30]` |
| `BM-28` | At least one verifier not written or commissioned by EPD² must verify a real context before any binding use                             |
| `BM-29` | Where a property cannot be verified from the record — notably cast-as-intended for a compromised device — that limit is published       |

`BM-28` is a governance gate, not a technical requirement, and it appears in
`PACK-16A-GERMAN-LEGAL-BOUNDARY.md` §8 for that reason.

---

## 8. Cryptographic agility

| ID      | Requirement                                                                                                                               |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `BM-30` | Every context binds a **cryptographic parameter set identifier**, published in the manifest and reproduced in the record                  |
| `BM-31` | A parameter set is **immutable** once a context reaches `issuance_open`; changing it is a new context, never an in-place edit             |
| `BM-32` | **Downgrade is refused, not warned**: a context whose declared parameter set is below the governed minimum fails configuration validation |
| `BM-33` | Parameter provenance is published: how the parameters arose, by whom, verifiable independently (`F-INF-3`)                                |
| `BM-34` | The record states the specification version it conforms to, so an old record stays interpretable after a parameter migration              |
| `BM-35` | A migration path to a different group or a post-quantum construction must not require re-opening a past election's record                 |

### 8.1 Parameters are deferred

No group, curve, key size, hash function or library is chosen here. The
German reference for cryptographic parameters, **BSI TR-02102-1**, current
version **2026-01**, published 23 January 2026 `[E-52]`, is named as the
baseline PACK-16B must justify against — including where the selected
specification's fixed parameters do or do not align with it, which is an
open question and is recorded as `OD-P16A-03`.

### 8.2 The library rule

Whatever implementation PACK-16D selects must satisfy, as acceptance
criteria and not as expectations:

1. It implements **strong Fiat–Shamir** — the statement is hashed, not only
   the commitment — and this is verified by test against the specification,
   not assumed (`F-INF-2`, `AC-P16A-039`).
2. Its output verifies against **an independent verifier it did not ship**.
3. Its parameter generation is reproducible from published provenance.
4. Its version, provenance and supply chain are recorded and pinned.
5. Where no implementation satisfies 1–4, **the correct outcome is not to
   proceed**, and `PACK-16A-FAILURE-AND-ABORT-MODEL.md` `FM-P16A-22` states
   what happens then.

---

## 9. Compatibility checks against the inherited architecture

| Check                                                                                   | Result                              | Basis                                                           |
| --------------------------------------------------------------------------------------- | ----------------------------------- | --------------------------------------------------------------- |
| Does the profile require identity on the voting side?                                   | **No**                              | Eligibility is out of the protocol's scope `[E-06]`             |
| Does it require a per-participant persistent voting-side identifier?                    | **No**                              | No voter object exists in the construction                      |
| Does it require any party to hold both an eligibility-side and a voting-side reference? | **No**                              | The only shared figure is an aggregate count `[E-06]`           |
| Does it require a reusable voting session or client persistence?                        | **No**                              | Ballot preparation is a single act; `CC-07` forbids persistence |
| Does it decrypt individual ballots?                                                     | **No** (`EPD2-HOM-1`)               | Homomorphic tally only `[E-08]`                                 |
| Does it create an intermediate tally?                                                   | **No**                              | `BM-21`, `BM-22`                                                |
| Does it create a receipt revealing choice?                                              | **No**                              | `BM-03` — the code derives from encryptions only `[E-05]`       |
| **Does it create a hidden individual dispute link?**                                    | **No**                              | §9.1                                                            |
| Does it satisfy PACK-15's continuation-capability constraints?                          | **Yes**, subject to `CC-01`…`CC-10` | Scope §3.2                                                      |

### 9.1 The dispute-link check, performed explicitly

`ADR-098` requires that no mechanism link a person to a ballot, including
with consent. The selected profile is checked against the ways such a link
could appear:

| Possible link                                               | Present?       | Why not                                                                            |
| ----------------------------------------------------------- | -------------- | ---------------------------------------------------------------------------------- |
| A voter roll published beside ciphertexts                   | No             | Helios's design `[E-21]`; not adopted, and `BM-04` forbids it                      |
| A signature over the ballot binding an identity             | No             | IVXV's design `[E-24]`; not adopted, and §3.2 forbids it                           |
| A credential list pairing identity with a public credential | No             | Belenios's design `[E-13]`; not adopted, and §3.2 forbids it                       |
| A confirmation code resolvable to a participant             | No             | `BM-03` — derived from encryptions only; no lookup table exists                    |
| A "show me how my ballot was counted" operation             | No             | No individual ballot is decrypted; the operation is not expressible                |
| A trustee-assisted individual decryption for a dispute      | **Prohibited** | `BM-21`, `BM-22`; and `PACK-16A-ROLE-SEPARATION-MATRIX.md` §4 forbids it as an act |

The last row is the one to watch. The construction _could_ decrypt a single
ballot if a trustee quorum chose to, and that is exactly the capability a
sympathetic dispute process would ask for. It is prohibited as an act, it
has no operation, and `PACK-16A-THREAT-MODEL.md` `T-P16A-33` treats the
request for it as an attack path rather than as a feature request.

---

## 10. Supported and unsupported election types

Full treatment with per-type analysis is
`PACK-16A-ELECTION-PROFILE-MATRIX.md`. Summary:

**Supported by `EPD2-HOM-1`:** yes/no referendum · single-choice election ·
multiple-choice (n-of-m) election · approval voting · multi-seat election
by approval or n-of-m · candidate nomination **as an internal
non-statutory selection only** · constitutional-amendment vote as a
yes/no · party-policy consultation · binding member resolution.

**Not supported by `EPD2-HOM-1`:** ranked-choice voting · STV · Condorcet ·
Majority Judgment · any tally depending on the joint pattern within a
ballot · free-form write-ins.

**Prohibited pending research:** everything in `EPD2-MIX-1`; any election
type for a public political office (§8 of the legal boundary); write-ins.

---

## 11. Residual risks of this selection

Named here so that they appear in the decision rather than only in the
threat model.

| ID      | Residual risk                                                                                                 | Severity | Owner                |
| ------- | ------------------------------------------------------------------------------------------------------------- | -------- | -------------------- |
| `RR-01` | **No production-grade implementation of the selected specification version exists** `[E-10a]`                 | high     | PACK-16D             |
| `RR-02` | Ranked ballots are unsupported; bodies that use them today must change method or stay on the existing process | medium   | Governance           |
| `RR-03` | Cast-as-intended relies on challenge, which is probabilistic and depends on take-up                           | medium   | PACK-16C, FRONT      |
| `RR-04` | Individual verifiability take-up is empirically low — 9.9 % at best in the most mature deployment `[E-29]`    | medium   | PACK-16C, FRONT      |
| `RR-05` | Device compromise is out of scope for every candidate assessed                                                | high     | out of scope; stated |
| `RR-06` | Timing correlation is reduced and bounded, not eliminated (PACK-15 `T-P15-13`)                                | medium   | PACK-16C, PACK-17    |
| `RR-07` | Small electorates weaken every unlinkability property, and no cryptography changes this                       | high     | Governance           |
| `RR-08` | Specification stewardship is not formally documented `[E-10a]`                                                | medium   | `OD-P16A-05`         |
| `RR-09` | No symbolic or cryptographic proof of protocol compliance exists for the EPD² profile as composed             | high     | `OD-P16A-06`         |
| `RR-10` | The bulletin board is not provided by the selected family and is entirely EPD²'s to build `[E-07]`            | high     | PACK-16C             |

`RR-09` deserves emphasis. The Swiss ordinance requires _"a symbolic and a
cryptographic proof of compliance"_ `[E-45]`. EPD² has neither, for the
profile as composed, and **does not claim to**. That is the single largest
gap between this architecture and the most demanding regulatory framework
located.

---

## 12. Conditions that invalidate this decision

`ADR-099` is `proposed`, and these are the conditions under which it must
be re-opened rather than amended:

1. A published break of the selected construction's ballot-privacy or
   verifiability properties.
2. Discovery that the selected specification's proof construction, as
   implemented in the chosen library, uses weak Fiat–Shamir (`F-INF-2`).
3. Abandonment of the specification by its stewards without a successor
   (`RR-08`).
4. A governance decision that ranked ballots are required for a binding
   context — which makes `EPD2-HOM-1` insufficient rather than wrong.
5. A German legal development that changes the boundary in
   `PACK-16A-GERMAN-LEGAL-BOUNDARY.md` §8.
6. Failure to obtain an independent verifier per `BM-28`.

**SPECIFIED. ASSESSED. SELECTED FOR ARCHITECTURAL REVIEW. REQUIRES EXTERNAL
REVIEW. REQUIRES LEGAL ASSESSMENT. NOT PRODUCTION READY. NOT LEGALLY
ACTIVATED.**
