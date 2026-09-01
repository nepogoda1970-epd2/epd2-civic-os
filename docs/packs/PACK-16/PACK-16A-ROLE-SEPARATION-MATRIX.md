# PACK-16A — Role Separation Matrix

**Round:** PACK-16A — Verifiable Voting Protocol and Ballot Model Selection. **Specification and ADR only. No code. Not implemented. Not an implementation candidate. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-099`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

This extends `PACK-15-SEPARATION-OF-DUTIES-MATRIX.md`, which is the
`FIR-ROLE-005` Election Administration Separation Matrix and **remains in
force unchanged**. PACK-15's ten roles are carried forward; this document
adds the ballot-domain roles and states the incompatibilities that arise
once a ballot exists.

---

## 1. Roles

| ID     | Role                           | Responsibility                                                                             | Origin                                      |
| ------ | ------------------------------ | ------------------------------------------------------------------------------------------ | ------------------------------------------- |
| `R-01` | **Election Board**             | Constitutes the election; approves the manifest; decides exclusions, aborts and annulments | new in PACK-16A                             |
| `R-02` | **Election Officer**           | Operates the context and its windows within the Board's decisions                          | PACK-15 Voting Operations Officer, extended |
| `R-03` | **Eligibility Administrator**  | Configures and operates eligibility evaluation                                             | PACK-15 Eligibility Officer                 |
| `R-04` | **Credential Authority**       | Issues, revokes and marks redeemed voting credentials                                      | PACK-15 Credential Issuer                   |
| `R-05` | **Voting-System Operator**     | Operates the casting service and the Voting Client                                         | PACK-15 Voting Client Operator, extended    |
| `R-06` | **Bulletin-Board Operator**    | Operates the board; appends, checkpoints, publishes                                        | new in PACK-16A                             |
| `R-07` | **Cryptographic Trustee**      | Holds one guardian share; contributes to key generation and to decryption                  | new in PACK-16A                             |
| `R-08` | **Ceremony Coordinator**       | Convenes and records the key ceremony; holds **no** share                                  | new in PACK-16A                             |
| `R-09` | **Security Administrator**     | Security configuration, keys other than guardian shares, monitoring                        | PACK-12 / `FIR-INV-008`                     |
| `R-10` | **System Administrator**       | Infrastructure, deployment, availability                                                   | PACK-12 / `FIR-INV-008`                     |
| `R-11` | **Independent Auditor**        | Verifies integrity from evidence bundles and the published record; concurs in grave acts   | PACK-15, extended                           |
| `R-12` | **Election Observer**          | Observes the process; reads only what is public                                            | new in PACK-16A                             |
| `R-13` | **DPO**                        | Data-protection oversight                                                                  | `FIR-ROLE-001`                              |
| `R-14` | **Incident Commander**         | Coordinates incident response within declared boundaries                                   | PACK-12 lineage                             |
| `R-15` | **Legal Activation Authority** | Decides whether a context may be activated at all                                          | new in PACK-16A                             |
| `R-16` | **Archive Custodian**          | Preserves the record; verifies archival integrity                                          | new in PACK-16A                             |

**Roles carried forward unchanged from PACK-15 and not restated here:**
Membership Authority, Eligibility Reviewer, Tally Authority (now discharged
by `R-01` + `R-07` acting together), Security Auditor, Dispute Reviewer.

---

## 2. The separation-of-duties matrix

`✓` may hold together · `✗` incompatible, must never be held by the same
natural person or the same service principal · `△` may hold together only
under dual control with recorded evidence.

|                               | R-01 | R-02 | R-03 | R-04 | R-05 | R-06 | R-07 | R-08 | R-09 | R-10 | R-11 | R-12 | R-13 | R-14 | R-15 | R-16 |
| ----------------------------- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| **R-01** Election Board       | —    | △    | ✗    | ✗    | ✗    | ✗    | ✗    | △    | ✗    | ✗    | ✗    | ✓    | ✗    | ✗    | △    | ✗    |
| **R-02** Election Officer     | △    | —    | ✗    | ✗    | ✗    | ✗    | ✗    | ✓    | ✗    | ✗    | ✗    | ✗    | ✗    | ✗    | ✗    | ✗    |
| **R-03** Eligibility Admin    | ✗    | ✗    | —    | ✗    | ✗    | ✗    | ✗    | ✗    | ✗    | ✗    | ✗    | ✗    | ✗    | ✗    | ✗    | ✗    |
| **R-04** Credential Authority | ✗    | ✗    | ✗    | —    | ✗    | ✗    | ✗    | ✗    | ✗    | ✗    | ✗    | ✗    | ✗    | ✗    | ✗    | ✗    |
| **R-05** Voting-System Op.    | ✗    | ✗    | ✗    | ✗    | —    | ✗    | ✗    | ✗    | ✗    | △    | ✗    | ✗    | ✗    | ✓    | ✗    | ✗    |
| **R-06** Board Operator       | ✗    | ✗    | ✗    | ✗    | ✗    | —    | ✗    | ✗    | ✗    | △    | ✗    | ✗    | ✗    | ✓    | ✗    | ✗    |
| **R-07** Trustee              | ✗    | ✗    | ✗    | ✗    | ✗    | ✗    | —    | ✗    | ✗    | ✗    | ✗    | ✗    | ✗    | ✗    | ✗    | ✗    |
| **R-08** Ceremony Coordinator | △    | ✓    | ✗    | ✗    | ✗    | ✗    | ✗    | —    | ✗    | ✗    | ✗    | ✗    | ✗    | ✗    | ✗    | ✗    |
| **R-09** Security Admin       | ✗    | ✗    | ✗    | ✗    | ✗    | ✗    | ✗    | ✗    | —    | ✗    | ✗    | ✗    | ✗    | ✓    | ✗    | ✗    |
| **R-10** System Admin         | ✗    | ✗    | ✗    | ✗    | △    | △    | ✗    | ✗    | ✗    | —    | ✗    | ✗    | ✗    | ✓    | ✗    | ✗    |
| **R-11** Independent Auditor  | ✗    | ✗    | ✗    | ✗    | ✗    | ✗    | ✗    | ✗    | ✗    | ✗    | —    | ✓    | ✗    | ✗    | ✗    | ✗    |
| **R-12** Observer             | ✓    | ✗    | ✗    | ✗    | ✗    | ✗    | ✗    | ✗    | ✗    | ✗    | ✓    | —    | ✓    | ✗    | ✓    | ✓    |
| **R-13** DPO                  | ✗    | ✗    | ✗    | ✗    | ✗    | ✗    | ✗    | ✗    | ✗    | ✗    | ✗    | ✓    | —    | ✓    | ✗    | ✗    |
| **R-14** Incident Commander   | ✗    | ✗    | ✗    | ✗    | ✓    | ✓    | ✗    | ✗    | ✓    | ✓    | ✗    | ✗    | ✓    | —    | ✗    | ✗    |
| **R-15** Legal Activation     | △    | ✗    | ✗    | ✗    | ✗    | ✗    | ✗    | ✗    | ✗    | ✗    | ✗    | ✓    | ✗    | ✗    | —    | ✗    |
| **R-16** Archive Custodian    | ✗    | ✗    | ✗    | ✗    | ✗    | ✗    | ✗    | ✗    | ✗    | ✗    | ✗    | ✓    | ✗    | ✗    | ✗    | —    |

**A `✓` is permission, not encouragement.** In any context with more than
one available person, roles are held separately.

---

## 3. Minimum prohibitions — normative

Each is stated as a sentence an implementation must be able to point at.

```text
The Eligibility Administrator cannot access ballots.
The Credential Authority cannot identify a ballot choice.
The Voting-System Operator cannot reconstruct identity.
No single Trustee can decrypt.
The System Administrator cannot silently alter election records.
The Security Administrator and the System Administrator are separate.
The Election Officer cannot bypass threshold rules.
The Auditor cannot mutate election state.
The DPO does not receive plaintext ballot access by role.
The Archive Custodian cannot rewrite election evidence.
The Bulletin-Board Operator cannot create accepted ballots.
```

### 3.1 How each is enforced

| Prohibition                                     | Enforcement                                                                                                                      | Detection                             |
| ----------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------- |
| Eligibility Administrator ↛ ballots             | **Structural**: no read path, no client, no route from the identity side to the board (ADR-090 §7)                               | Principal inventory per store         |
| Credential Authority ↛ ballot choice            | **Structural**: no individual ballot is decrypted; no credential reference appears on the board (`BB-21`)                        | Prohibited-key scan                   |
| Voting-System Operator ↛ identity               | **Structural**: nothing crossing the boundary carries identity (PACK-15 ADR-091)                                                 | Boundary payload inspection           |
| No single Trustee decrypts                      | **Cryptographic**: threshold k > 1 (`KC-01`, `TP-01`)                                                                            | Share proofs (`KC-10`)                |
| System Administrator ↛ silent record alteration | **Cryptographic + structural**: append-only board, chained signed checkpoints, independent mirrors                               | Mirror divergence (`BB-31`)           |
| Security Admin ≠ System Admin                   | **Organisational**, per `FIR-INV-008`                                                                                            | Privileged-session evidence (PACK-12) |
| Election Officer ↛ threshold bypass             | **Cryptographic**: no operation decrypts below quorum, and none may be added (`BM-21`, `BM-22`)                                  | Ceremony evidence                     |
| Auditor ↛ mutation                              | **Structural**: auditor access is read-only, time-boxed, one context per grant (PACK-15 §20.2)                                   | `AS-05`, `AS-06`                      |
| DPO ↛ plaintext ballots by role                 | **Structural**: no plaintext individual ballot exists                                                                            | —                                     |
| Archive Custodian ↛ rewrite                     | **Cryptographic**: archive integrity commitment; archival verification without a live service (`BB-20`)                          | Archive verification                  |
| Board Operator ↛ create accepted ballots        | **Cryptographic**: `BM-14` — an accepted ballot requires a proof of knowledge of its plaintext, which the operator does not have | Proof verification                    |

**The last row is the one that makes the board operator survivable.** A
board operator who could mint accepted ballots would be a single point of
outcome control. Because every accepted ballot carries a proof of knowledge
of its plaintext, an operator can drop or reorder — both detectable — but
cannot fabricate. `BM-14` therefore does double duty: it closes the
ballot-independence gap (`F-INF-1`) _and_ it bounds the board operator.

---

## 4. Acts requiring dual control and auditor concurrence

| Act                                             | Decider          | Dual control | Independent Auditor | Published                |
| ----------------------------------------------- | ---------------- | ------------ | ------------------- | ------------------------ |
| Approving the election manifest                 | `R-01`           | yes          | notified            | yes                      |
| Opening or closing a window early               | `R-01`           | yes          | **concurrence**     | yes                      |
| Excluding a published ballot (`EX-04`)          | `R-01`           | yes          | **concurrence**     | yes                      |
| Pausing a context                               | `R-01` or `R-14` | yes          | notified            | yes                      |
| Aborting or annulling a context                 | `R-01`           | yes          | **concurrence**     | yes                      |
| Substituting a trustee before the ceremony      | `R-01`           | yes          | **concurrence**     | yes                      |
| Declaring quorum loss                           | `R-01`           | yes          | **concurrence**     | yes                      |
| Adding a mirror mid-election (`BB-32`)          | `R-01`           | yes          | notified            | yes                      |
| Releasing an unsuppressed result to an auditor  | `R-01`           | yes          | is the recipient    | recorded                 |
| Any archive access that alters storage location | `R-16`           | yes          | notified            | recorded                 |
| **Decrypting an individual ballot**             | **nobody**       | —            | —                   | **prohibited as an act** |

The last row is not an omission. There is no decider, because there is no
act. `PACK-16A-BALLOT-MODEL-SPECIFICATION.md` §9.1 and
`PACK-16A-THREAT-MODEL.md` `T-P16A-42` treat the request for it as an
attack path.

---

## 5. Dangerous collusion combinations

Combinations that defeat a guarantee even where each participant holds a
legitimate role. **Each is a prohibited role assignment**, and where the
parties are distinct people the combination is a monitored risk rather than
a permitted arrangement.

| #   | Combination                                            | What it defeats                                                               | Control                                                                      |
| --- | ------------------------------------------------------ | ----------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| 1   | **k Trustees**                                         | Ballot secrecy entirely; and an early tally computed offline                  | `TP-02` cross-organisational quorum; `KC-05`; undetectable — prevention only |
| 2   | **k Trustees + Bulletin-Board Operator**               | Secrecy **and** the ability to correlate board entries with decrypted content | Combination prohibited; mirrors are independent of trustees (`BB-29`)        |
| 3   | **k Trustees + Credential Authority**                  | A path toward participation attribution                                       | `R-04` ✗ `R-07`; separate organisations; separate audit streams              |
| 4   | **Eligibility Administrator + Voting-System Operator** | The identity→ballot chain, by observation across the boundary                 | `R-03` ✗ `R-05`; PACK-15 `SD-06`; no principal reads both sides              |
| 5   | **Board Operator + System Administrator**              | Silent alteration with infrastructure cover                                   | `△` only, under dual control; mirrors make alteration detectable             |
| 6   | **Election Officer + Trustee**                         | Window control plus decryption capability                                     | `R-02` ✗ `R-07`                                                              |
| 7   | **Independent Auditor + any operational role**         | The check becomes self-certification                                          | `R-11` ✗ everything operational                                              |
| 8   | **Incident Commander + Trustee**                       | Break-glass authority plus a share                                            | `R-14` ✗ `R-07`; `KC-18` no silent break-glass                               |
| 9   | **Backup Administrator + Board Operator**              | Restore-based rollback of the board                                           | Separate backup domains (ADR-090 §7); **PACK-17**                            |
| 10  | **Archive Custodian + Election Board**                 | The ability to rewrite history and to authorise it                            | `R-16` ✗ `R-01`                                                              |

**Combination 1 is the one that cannot be detected**, only prevented. That
is why the quorum must span organisations rather than roles, and why
`TP-02` is a principle rather than a recommendation.

---

## 6. Role rules that are not incompatibilities

| ID      | Rule                                                                                                                                                                                                |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `RS-01` | A trustee's identity and organisation are **published** in the manifest (`TP-07`)                                                                                                                   |
| `RS-02` | An **Election Observer** reads only what is public and holds no grant; observation requires no accreditation to read the board (`BB-36`)                                                            |
| `RS-03` | The **Legal Activation Authority** is separate from the Election Board in any binding context; a body cannot authorise itself                                                                       |
| `RS-04` | A person who is a **candidate** in a context may hold no role in that context, including trustee, and this is checked at appointment                                                                |
| `RS-05` | A role held for one context does not transfer to another; every appointment is per context and published                                                                                            |
| `RS-06` | **No operator holds eligibility, issuance and tally authority at once**, and no grant, emergency, feature flag or break-glass path may produce that combination — PACK-15's rule, extended to tally |
| `RS-07` | Where an organisation is too small to separate roles, the correct outcome is **not to hold the vote electronically** — not to merge roles                                                           |

`RS-04` and `RS-07` are the two most likely to be inconvenient in practice
and are stated for that reason. A small local body will often have exactly
the people who are also the candidates, and merging the roles would be the
natural response; `RS-07` names the alternative instead.

---

## 7. Break-glass

PACK-12's mechanism applies unchanged. Additional constraints for the
ballot domain:

```text
No break-glass path grants read access to both sides of the trust boundary.
No break-glass path assembles a trustee quorum.
No break-glass path writes to, deletes from or reorders the bulletin board.
No break-glass path decrypts anything.
No break-glass path is silent: dual control, out-of-band auditor
   notification and published evidence are required (KC-18).
An incident that genuinely requires any of the above is a context-level
   event — suspension, annulment, re-run — decided by governance.
```

That last sentence is PACK-15 ADR-090's, unchanged, and it is the sentence
that keeps incident pressure from becoming architecture.

**SPECIFIED. EXTENDS `FIR-ROLE-005`. REQUIRES EXTERNAL REVIEW. NOT
PRODUCTION READY. NOT LEGALLY ACTIVATED.**
