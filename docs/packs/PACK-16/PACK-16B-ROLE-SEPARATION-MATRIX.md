# PACK-16B — Role Separation Matrix

**Round:** PACK-16B — Cryptographic Parameters, Key Ceremony and Trustee Architecture. **Specification and ADR only. No code. No cryptographic code. Not implemented. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-100`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

**This document does not restate `PACK-16A-ROLE-SEPARATION-MATRIX.md`.** It
extends it for the ceremony: it adds the two roles the ceremony needs and
PACK-16A did not name, assigns responsibility phase by phase, and states the
prohibitions in a form that can be checked at appointment rather than
discovered at a ceremony.

The PACK-16A role identifiers `R-01`…`R-16` are used unchanged. **No
PACK-16A role is redefined, renamed, merged or removed here.**

---

## 1. The roles the ceremony uses

| ID      | Role                          | In the ceremony                                                                             | Holds secret material? |
| ------- | ----------------------------- | ------------------------------------------------------------------------------------------- | ---------------------- |
| `R-01`  | **Election Board**            | Approves the profile, the parameter set, the guardian set and the completed ceremony        | **No — never**         |
| `R-02`  | **Election Officer**          | Operates the context and its windows within the Board's decisions                           | **No**                 |
| `R-03`  | **Eligibility Administrator** | No ceremony function                                                                        | **No**                 |
| `R-04`  | **Credential Authority**      | No ceremony function                                                                        | **No**                 |
| `R-05`  | **Voting-System Operator**    | No ceremony function; consumes the published joint key only                                 | **No**                 |
| `R-06`  | **Bulletin-Board Operator**   | Publishes the transcript and checkpoints; verifies nothing on the Board's behalf             | **No**                 |
| `R-07`  | **Cryptographic Trustee (Guardian)** | Generates, holds and uses exactly one share                                          | **Yes — one share**    |
| `R-08`  | **Ceremony Coordinator**      | Convenes, sequences and records. **Holds nothing** (`RS-16B-03`)                            | **No — never**         |
| `R-09`  | **Security Administrator**    | Operates security configuration and non-guardian keys                                       | Non-guardian keys only |
| `R-10`  | **System Administrator**      | Infrastructure and availability                                                             | **No**                 |
| `R-11`  | **Independent Auditor**       | Verifies the transcript independently; **cannot change it** (`RS-16B-10`)                   | **No**                 |
| `R-14`  | **Incident Commander**        | Coordinates response inside declared boundaries; **authorises no decryption** (`RS-16B-11`) | **No**                 |
| `R-15`  | **Legal Activation Authority**| Decides whether the context may be activated at all                                         | **No**                 |
| `R-16`  | **Archive Custodian**         | Preserves and re-verifies the ceremony record                                               | **No**                 |
| **`R-17`** | **Guardian Organization**  | **New in PACK-16B.** The legal body that nominates and supports a guardian                  | **No — the person holds the share, not the body** |
| **`R-18`** | **Cryptographic Reviewer** | **New in PACK-16B.** Independent expert review of parameters, transcript and implementation | **No**                 |

`R-12` Election Observer and `R-13` DPO are carried forward from PACK-16A
unchanged and have no ceremony-specific duties beyond observation and
data-protection oversight respectively.

### 1.1 Why `R-17` exists as a role and not as an attribute

A guardian is a **natural person**; a guardian organization is the body that
nominated them and that can, in practice, apply pressure to them. Naming it
as a role makes three things checkable that were previously implicit:

```text
The organization is declared and published, so independence can be assessed
   at the level where dependence actually lives (GI-01…GI-08).
The organization has obligations — support, non-interference, notification —
   and can be found to have breached them.
The organization HOLDS NOTHING. Nominating a guardian confers no capability
   whatsoever, and the organization cannot instruct, replace or speak for
   the guardian's share.
```

### 1.2 Why `R-18` exists

`OD-P16A-06` and `TV-01`…`TV-08` create obligations that no other role can
discharge: neither the Independent Auditor (who verifies *this* ceremony
against *this* specification) nor the Security Administrator (who operates)
is the person who assesses whether the construction is sound. Leaving the
duty unassigned is how it becomes nobody's.

**`R-18` is not an EPD² employee or contractor by default.** Where the
reviewer is engaged by EPD², the engagement is published, and the review is
labelled as commissioned (`GI-06` reasoning, applied to review).

---

## 2. RACI over the twenty ceremony phases

**R** responsible (does it) · **A** accountable (answers for it, exactly
one per phase) · **C** consulted · **I** informed.

| # | Phase                                     | R-01 | R-02 | R-07 | R-08 | R-11 | R-15 | R-16 | R-17 | R-18 |
| - | ----------------------------------------- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| 1 | Election profile approval                 | **A/R** | C | I | I | C | C | – | – | C |
| 2 | Parameter-set approval                    | **A** | I | I | R | C | I | – | – | **R** |
| 3 | Guardian nomination                       | **A** | C | I | R | I | – | **R** | – | – |
| 4 | Guardian independence checks              | **A** | – | C | R | **C** | – | – | C | – |
| 5 | Guardian authentication, device attestation | I  | – | **R** | **A** | C | – | – | C | – |
| 6 | Ceremony session creation                 | I    | C | I | **A/R** | I | – | – | – | – |
| 7 | Guardian public contribution generation   | I    | – | **A/R** | C | I | – | – | – | – |
| 8 | Proof-of-possession verification          | I    | – | **R** | C | **A** | – | – | – | – |
| 9 | Polynomial commitment generation          | I    | – | **A/R** | C | I | – | – | – | – |
| 10 | Encrypted share distribution             | I    | – | **A/R** | C | I | – | – | – | – |
| 11 | Share receipt and verification           | I    | – | **A/R** | C | C | – | – | – | – |
| 12 | Complaints and dispute phase             | **A** | I | R | R | **C** | – | – | I | – |
| 13 | Disqualification handling before activation | **A/R** | I | C | R | C | I | – | **I** | – |
| 14 | Joint public-key computation             | I    | – | **R** | R | **A** | – | – | – | – |
| 15 | Extended base hash / context hash derivation | I | – | R | R | **A** | – | – | – | C |
| 16 | Ceremony transcript verification         | I    | – | C | R | **A/R** | – | C | – | C |
| 17 | Independent auditor verification         | I    | I | I | I | **A/R** | I | I | I | C |
| 18 | Election Board acceptance                | **A/R** | C | I | C | **C** | I | I | I | I |
| 19 | Public ceremony checkpoint               | I    | C | I | R | C | I | **R** | I | I |
| 20 | Activation lock                          | C    | R | I | R | C | **A** | I | I | I |

**Three properties of this table are deliberate and load-bearing:**

```text
Phase 8 and phase 14 are ACCOUNTABLE to the Auditor, not to the
   Coordinator. The party who convenes the ceremony does not certify it.
Phase 20 is ACCOUNTABLE to the Legal Activation Authority alone.
   No cryptographic success authorises an election.
Phase 7, 9, 10, 11 are accountable to the GUARDIANS. Nobody else can be
   accountable for a value nobody else may possess.
```

`R-06` appends and publishes at phases 16, 19 and on every event the
notification model requires; it is **R** for publication and never **A** for
content. `R-09` and `R-10` appear nowhere in this table, and that is the
point (`RS-16B-04`, `RS-16B-05`).

---

## 3. The eleven prohibitions — normative

| ID           | Prohibition                                                                                                                  |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------ |
| `RS-16B-01`  | **Every ceremony role is appointed per context, published by name and organisation before phase 5, and does not transfer between contexts** |
| `RS-16B-02`  | **A "role" means a natural person or a named service principal.** A shared account, a rota, a team inbox or an unnamed office cannot hold a ceremony role, and cannot hold a share at all |
| `RS-16B-03`  | **The Ceremony Coordinator holds no guardian secret material** — no share, no share backup, no decryption capability, no share-decryption key, at any time, in any form, in any context. The Coordinator convenes and records |
| `RS-16B-04`  | **The System Administrator is not a guardian**, and administers no guardian device (`KU-08`)                                   |
| `RS-16B-05`  | **The Security Administrator is not a guardian**, and holds no guardian key material alongside the system keys they do hold      |
| `RS-16B-06`  | **The Voting-System Operator is not a guardian.** The party that runs the casting service may not hold a share of the key that opens what it collected |
| `RS-16B-07`  | **The Credential Authority is not a guardian.** PACK-15's boundary is preserved: the party that knows who was entitled to vote holds no capability to open a ballot |
| `RS-16B-08`  | **The Eligibility Administrator is not a guardian**, for the same reason                                                        |
| `RS-16B-09`  | **The Bulletin-Board Operator is not a guardian.** The party that publishes the record may not also hold the material whose misuse the record exists to detect |
| `RS-16B-10`  | **The Independent Auditor cannot mutate ceremony state.** It reads, recomputes, and produces a verdict. It appends nothing to the transcript except its own signed verdict, and can neither halt nor continue the ceremony by acting on it — only by saying so (`CT-24`) |
| `RS-16B-11`  | **The Incident Commander cannot authorise decryption, cannot direct a guardian, cannot alter a quorum and cannot instruct a ceremony to proceed.** Incident authority is response coordination, not election authority. An incident is precisely the moment at which this would be attempted |
| `RS-16B-12`  | **The Election Officer cannot lower a quorum**, change `k` or `n`, excuse a guardian, or shorten a ceremony phase. `k` and `n` are fixed in the manifest before `issuance_open` and are immutable for the context (`GQ-04`, `GQ-05`) |
| `RS-16B-13`  | **The Election Board cannot reconstruct secrets.** The Board decides, and possesses nothing. There is no arrangement — quorate, minuted, court-ordered or emergency — by which the Board obtains a share, a decryption or a plaintext ballot |

### 3.1 Two more, from this round's own findings

| ID           | Prohibition                                                                                                                  |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------ |
| `RS-16B-14`  | **The Guardian Organization (`R-17`) holds nothing and instructs nothing.** It nominates, supports and is informed. It may not require its guardian to participate, abstain, disclose, delegate or surrender material, and an attempt is an independence violation (`GI-07`) and a complaint ground |
| `RS-16B-15`  | **The Cryptographic Reviewer (`R-18`) holds no share, operates nothing and approves nothing.** A review is evidence for a decision, not the decision, and a favourable review does not authorise activation |
| `RS-16B-16`  | **The Archive Custodian (`R-16`) can verify and cannot decrypt.** Archive integrity re-verification uses public material exclusively; no archival process ever requires a guardian to act |

---

## 4. Non-combinable roles — ceremony extension

`✗` never held by the same natural person or service principal, in the same
context · `△` only under dual control with recorded evidence · `✓`
permitted. **This table extends PACK-16A §2 for `R-17` and `R-18` and
tightens three cells around `R-07`; every other PACK-16A cell stands.**

|                                | R-01 | R-07 | R-08 | R-11 | R-14 | R-15 | R-16 | R-17 | R-18 |
| ------------------------------ | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| **R-01** Election Board        | —    | ✗    | **✗** | ✗   | ✗    | △    | ✗    | **△** | ✗   |
| **R-07** Guardian              | ✗    | —    | ✗    | ✗    | ✗    | ✗    | ✗    | **✗** | **✗** |
| **R-08** Ceremony Coordinator  | **✗** | ✗   | —    | ✗    | ✗    | ✗    | ✗    | **✗** | ✗   |
| **R-11** Independent Auditor   | ✗    | ✗    | ✗    | —    | ✗    | ✗    | ✗    | ✗    | **△** |
| **R-14** Incident Commander    | ✗    | ✗    | ✗    | ✗    | —    | ✗    | ✗    | ✗    | ✗    |
| **R-15** Legal Activation      | △    | ✗    | ✗    | ✗    | ✗    | —    | ✗    | ✗    | ✗    |
| **R-16** Archive Custodian     | ✗    | ✗    | ✗    | ✗    | ✗    | ✗    | —    | ✗    | ✓    |
| **R-17** Guardian Organization | **△** | **✗** | **✗** | ✗ | ✗    | ✗    | ✗    | —    | ✗    |
| **R-18** Cryptographic Reviewer| ✗    | **✗** | ✗   | **△** | ✗   | ✗    | ✓    | ✗    | —    |

**The three tightened cells, and why:**

| Cell            | PACK-16A | PACK-16B  | Reason                                                                                       |
| --------------- | -------- | --------- | ---------------------------------------------------------------------------------------------- |
| `R-01` × `R-08` | `△`      | **`✗`**   | Under `RS-16B-03` the Coordinator holds nothing, so the dual-control mitigation has nothing left to mitigate — but a Board member who also sequences the ceremony can determine *when* a complaint window closes. Separated outright |
| `R-07` × `R-17` | not covered | **`✗`** | A guardian may not simultaneously be the organ of their own nominating body. The person is nominated; the body does not nominate itself |
| `R-07` × `R-18` | not covered | **`✗`** | A reviewer who holds a share reviews their own participation                                  |

`R-11` × `R-18` is `△` rather than `✗`: a small ecosystem may have few
qualified people, and a reviewer who later audits is tolerable **if
declared, if the review predates the audit engagement, and if the Board
records that it accepted a narrowed independence** — which is the honest
form of a compromise that would otherwise be made silently.

`R-01` × `R-17` is `△` because in a party context a Board member very
plausibly belongs to a nominating body; the mitigation is that they take no
part in the independence assessment of that body's guardian (`GI-04`).

---

## 5. What each role may never do — the short form

```text
Election Board            decides everything, possesses nothing
Election Officer          operates windows, touches no quorum
Ceremony Coordinator      sequences and records, holds nothing
Guardian                  holds one share, and only its own
Guardian Organization     nominates, and holds nothing at all
Independent Auditor       recomputes and reports, changes nothing
Cryptographic Reviewer    assesses, approves nothing
Security Administrator    secures the system, not the election secret
System Administrator      keeps it running, is not in the ceremony
Bulletin-Board Operator   publishes, verifies nothing on anyone's behalf
Incident Commander        coordinates response, authorises no decryption
Legal Activation Authority  says whether it may happen at all
Archive Custodian         preserves and re-verifies, never decrypts
```

---

## 6. Enforcement — where each prohibition is actually checked

| Prohibition                              | Checked at                                     | Detected by                                        | On violation      |
| ---------------------------------------- | ------------------------------------------------ | ---------------------------------------------------- | ----------------- |
| `RS-16B-01`, `RS-16B-02`                 | Appointment; phase 3                            | Published role register vs. transcript participants  | `FM-16B-11`       |
| `RS-16B-03`                              | Phase 6 and phase 10; custody declaration        | The Coordinator appears in no share recipient list; `KU-01` declarations name no Coordinator | `FM-16B-22` if material is found |
| `RS-16B-04`…`RS-16B-09`                  | Phase 3 and phase 4                             | Cross-check of the guardian set against the operating role register (`GI-12`) | `FM-16B-11`, ceremony does not start |
| `RS-16B-10`                              | Continuous                                      | Transcript append rights; the Auditor's verdict is a distinct object (`CT-24`) | `FM-16B-16` if the transcript diverges |
| `RS-16B-11`                              | Incident time — **the only moment it matters**   | Every decryption authorisation carries the authorising role; the value `incident_commander` is not permitted to appear | `FM-16B-25` |
| `RS-16B-12`                              | Phase 1 fixing, then any change attempt          | `k`, `n` are inputs to `H_X` and to the transcript; altering them changes the context | `FM-16B-26`      |
| `RS-16B-13`                              | Architecturally — there is no such operation     | Absence of the operation is the control; a proposal to add one is `FM-16B-21` | design-review rejection |
| `RS-16B-14`                              | Phase 4; complaint phase                        | Declared in due diligence; alleged by the guardian    | complaint ground `guardian_independence_violation` |
| `RS-16B-15`, `RS-16B-16`                 | Engagement; archive procedure                    | Published engagement terms; archive procedure uses public inputs only | `FM-16B-33`      |

**`RS-16B-13` is enforced by absence and nothing else**, and that is
stronger than any control that could be enforced by a check: a check can be
bypassed by the party who operates it, whereas an operation that was never
specified has to be *added*, in public, against `BR-09`, `GQ-13` and `CM-18`.

---

## 7. Small organisations

The uncomfortable case is a Kreisverband with eleven active members that
wants an internal vote.

```text
The roles do not shrink. The vote does.
```

| ID           | Rule                                                                                                                   |
| ------------ | -------------------------------------------------------------------------------------------------------------------------- |
| `RS-16B-17`  | Where an organisation cannot fill the ceremony roles separately, the correct outcome is **not to hold the vote electronically** — PACK-16A `RS-07`, restated because this is where it will be tested first |
| `RS-16B-18`  | **Roles may be filled from outside the organisation** — a guardian from a sister association, an auditor from the federal level, an observer from a neutral body. This is the intended remedy, and `GQ-11` already requires it in part |
| `RS-16B-19`  | A **federal-level shared roster** of qualified auditors, coordinators and candidate guardians may be maintained so that small units can draw on it. Drawing from a shared roster is declared, and two guardians drawn from the same roster are **not** thereby dependent — the roster confers nothing (`GI-02` applies to the *organisation*, not to the list) |

---

## 8. What this document does not decide

```text
Appointment procedure and terms of office        → GOVERNANCE
Remuneration, expenses, insurance                 → GOVERNANCE
The role register's data model                    → PACK-16D
Sanctions for a role-holder who breaches a duty   → GOVERNANCE, LEGAL
Whether R-18 is a standing or per-context role    → OD-P16B-03
```

**SPECIFIED. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY. NOT LEGALLY
ACTIVATED.**
