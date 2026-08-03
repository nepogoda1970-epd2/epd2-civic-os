# PACK-16A — Trustee and Key-Ceremony Requirements

**Round:** PACK-16A — Verifiable Voting Protocol and Ballot Model Selection. **Specification and ADR only. No code. Not implemented. Not an implementation candidate. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-099`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

**PACK-16A does not design a key ceremony.** It states the obligations
PACK-16B inherits, and the properties of the selected protocol family that
make a ceremony necessary at all. **No cryptographic library, HSM, KMS, key
provider, guardian count or quorum value is chosen here.**

---

## 1. Why a ceremony is required by the selection

The selected family generates the election key through a **distributed key
generation** among n guardians with a quorum k, using a Pedersen-variant
DKG with Shamir secret sharing; decryption produces per-guardian shares
combined by Lagrange interpolation, with **compensated shares** covering
guardians who are absent at decryption `[E-04]`.

Two consequences follow, and they are the reason this document exists:

1. **The private key never exists in one place at one time.** There is
   therefore no key to protect, back up, escrow or lose — there is a
   *distribution* to protect. That is a fundamentally different
   operational problem, and treating it as key management is how a hidden
   master key gets created.
2. **The guardians' role is confidentiality, not integrity.** The
   specification is explicit: *"Compromised guardians — whether instantiated
   as humans or hardware — cannot compromise the integrity of the election
   tallies"*; *"the role of guardians is to protect confidentiality of
   votes"* `[E-04]`. A dishonest guardian can refuse to participate or leak,
   but cannot change a result. This shapes the whole threat treatment: the
   ceremony protects secrecy; the board and the proofs protect the outcome.

---

## 2. Obligations handed to PACK-16B

| ID       | Obligation                                                                                                                                            |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `KC-01`  | **Threshold trust.** Decryption requires a quorum k of n guardians. k > 1 always                                                                       |
| `KC-02`  | **No single-admin decryption.** No principal, role, grant, emergency path, feature flag or break-glass mechanism may assemble a quorum                 |
| `KC-03`  | **Minimum guardian count principles.** n is chosen so that quorum loss is survivable and collusion is expensive; the principle, not the number, is fixed here (§3.1) |
| `KC-04`  | **Quorum principles.** k is chosen so that a single organisation cannot reach it (§3.1)                                                                |
| `KC-05`  | **Independent trustee organizations.** Guardians are drawn from organisationally distinct bodies, not from roles within one body                       |
| `KC-06`  | **Guardian authentication.** Each guardian authenticates at ceremony assurance under PACK-14's mechanisms; no shared account, no delegated credential  |
| `KC-07`  | **Ceremony evidence.** Every ceremony step produces published, verifiable evidence with a coarsened timestamp and an attributable actor                |
| `KC-08`  | **Public key evidence.** The joint public key is published with the proofs that each guardian's contribution was well formed (Schnorr proofs, `[E-03]`)|
| `KC-09`  | **Key-generation evidence.** Polynomial commitments and share-distribution evidence are published; the ceremony is reproducible in verification, not in secret material |
| `KC-10`  | **Decryption-share verification.** Every share carries a proof; a share failing verification **halts the tally** rather than being dropped (`BM-23`)   |
| `KC-11`  | **Lost-trustee handling.** Compensated shares cover an absent guardian **within the quorum**; absence is published, not concealed                      |
| `KC-12`  | **Compromised-trustee handling.** A compromised guardian is a **context-level event**: the context is suspended and governance decides. A key is not "rotated" mid-election |
| `KC-13`  | **Quorum-loss handling.** Below quorum, the result is **unobtainable**. That is the designed outcome (§4)                                              |
| `KC-14`  | **Backup limitations.** Guardian material may be backed up **only** in a form that does not reduce the threshold — a backup that lets one party reconstruct is a hidden master key |
| `KC-15`  | **Recovery limitations.** No recovery mechanism may reconstruct the private key outside a quorum ceremony (§4.2)                                       |
| `KC-16`  | **Separation of Security Admin and System Admin.** `FIR-INV-008` applies unchanged; neither may hold guardian material                                 |
| `KC-17`  | **Out-of-band notification.** Ceremony start, completion, quorum shortfall and any guardian change notify the Independent Auditor out of band          |
| `KC-18`  | **No silent break-glass.** No privileged path touches guardian material without dual control, out-of-band notification and published evidence           |
| `KC-19`  | **Parameter provenance.** How the cryptographic parameters arose is published and independently reproducible (`BM-33`, `F-INF-3`)                      |
| `KC-20`  | **Test-key isolation.** A test key must be **structurally incapable** of validating in a production trust store, demonstrated rather than asserted (PACK-15 §18) |

---

## 3. Trust assumptions and collusion thresholds

### 3.1 The principles that constrain k and n

**PACK-16B chooses the numbers. PACK-16A fixes the principles they must
satisfy.**

| ID       | Principle                                                                                                                             |
| -------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| `TP-01`  | k ≥ 3. A two-party quorum is one meeting                                                                                              |
| `TP-02`  | **No single organisation may supply k guardians.** Collusion must require cross-organisational agreement                              |
| `TP-03`  | n − k ≥ 2. At least two guardians may be unavailable without losing the result                                                        |
| `TP-04`  | k > n/2 is **not** required; the construction tolerates a dishonest majority for integrity `[E-04]`, and confidentiality is what k protects |
| `TP-05`  | k and n are fixed in the manifest before `issuance_open` and cannot change during a context                                           |
| `TP-06`  | For a small electorate, k and n are **not** reduced. A small vote is not a low-stakes vote                                            |
| `TP-07`  | Guardian identity and organisation are published in the manifest; a secret guardian is not a check on anyone                          |

`TP-06` exists because the temptation runs the other way: a vote among
nineteen people feels like it should not need five trustees from four
organisations. It needs them more, because in a small body the
consequences of a leak are individual.

### 3.2 Honest-quorum assumptions, stated

| Assumption                                              | If it fails                                                             | Detectable?                                              |
| ------------------------------------------------------- | ----------------------------------------------------------------------- | ---------------------------------------------------------- |
| Fewer than k guardians collude                          | **Individual ballots become decryptable.** Ballot secrecy is lost       | **No.** Offline collusion leaves no trace                 |
| Guardians generate their contributions honestly         | Reduced key entropy                                                     | Partly — Schnorr proofs check well-formedness `[E-03]`    |
| Guardian material is not copied                         | The effective threshold is lower than k                                 | No                                                        |
| Guardians do not decrypt before closure                 | Intermediate tally                                                      | No, if done offline against a copied ballot set           |
| Parameters were honestly generated                      | The whole construction can be subverted `[E-33]`                        | Yes, **if** provenance is published and reproduced        |

**Three of the five are undetectable.** That is why `TP-02` and `KC-05` are
organisational rather than technical: where detection is impossible,
prevention has to come from making collusion require agreement between
parties who do not want to agree.

### 3.3 Collusion thresholds

```text
< k guardians colluding        → no ballot is decryptable
= k guardians colluding        → every individual ballot is decryptable
                                 and an early tally is computable offline
k guardians + board operator   → the above, plus the ability to correlate
                                 board entries with decrypted content
k guardians + credential issuer→ the above, plus a path toward
                                 participation attribution
```

The last two combinations are the ones
`PACK-16A-ROLE-SEPARATION-MATRIX.md` §5 names as **dangerous collusion
combinations** and forbids as role assignments.

---

## 4. Quorum loss, and the trade this architecture makes

### 4.1 What happens

```text
Quorum available          → decryption proceeds
Quorum temporarily short  → PAUSE; guardians are contacted; recorded
Quorum permanently lost   → the result is UNOBTAINABLE
                            the context is ANNULLED
                            a RE-RUN is the only remedy
```

`FM-P16A-12` in `PACK-16A-FAILURE-AND-ABORT-MODEL.md` is the operative
entry.

### 4.2 What may not happen

| Prohibited "recovery"                                             | Why it is prohibited                                                          |
| ----------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| Key escrow held by the organisation                               | It **is** the master key; the threshold becomes decoration                     |
| A "recovery guardian" holding a reconstructing share              | Same, wearing a costume                                                        |
| Backing up shares to one location                                 | One compromise yields a quorum                                                 |
| An administrative override to decrypt without a quorum            | `KC-02`; and its existence is the vulnerability, not its use                   |
| Lowering k after ballots are cast                                 | The threshold protected ballots cast under the original assumption             |
| Reconstructing a lost share from the others outside a ceremony    | That is reconstruction of the key by another name                              |

**The trade, stated once:** an unrecoverable election is preferable to a
recoverable secret. A recovery mechanism that can produce a result without a
quorum can produce a result without an election. PACK-15 made the identical
trade for credential delivery (§13.2), and this round keeps it.

**The cost, stated once:** if a quorum is genuinely lost, every participant
in that context voted for nothing and must vote again. That is a real harm
to real people, it is the direct consequence of `KC-15`, and it is accepted
with its name attached rather than engineered away.

---

## 5. What is published, and when

| Artifact                                              | Published                          | Audience |
| ----------------------------------------------------- | ---------------------------------- | -------- |
| Guardian list with organisations                      | Before `issuance_open`             | public   |
| k and n                                               | Before `issuance_open`             | public   |
| Cryptographic parameter set and identifier            | Before `issuance_open`             | public   |
| **Parameter provenance**                              | Before `issuance_open`             | public   |
| Joint public key and per-guardian well-formedness proofs | After the key ceremony          | public   |
| Polynomial commitments and share-distribution evidence | After the key ceremony            | public   |
| Ceremony record (steps, actors, coarsened times)      | After the key ceremony             | public   |
| Guardian absence or substitution                      | When it occurs                     | public   |
| **Decryption shares and their proofs**                | **After closure, with the result** | public   |
| Quorum shortfall event                                | When it occurs                     | public + out-of-band to the auditor |

**Nothing in this table is published before `voting_closed` if it bears on
an outcome**, and nothing here does: a public key, a commitment and a
ceremony record disclose no votes.

### 5.1 Acts possible only after closure

```text
production of any decryption share
combination of shares
decryption of any ciphertext, aggregate or individual
publication of any share
```

`BM-21` makes this a property of the construction's use rather than a
policy: no operation exists that decrypts before `voting_closed`, and none
may be added.

---

## 6. Cryptographic agility and the library question

| ID       | Obligation on PACK-16B / PACK-16D                                                                                                         |
| -------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| `KC-21`  | Justify the chosen parameters against **BSI TR-02102-1, current version 2026-01** `[E-52]`, including where the selected specification's fixed parameters diverge from it |
| `KC-22`  | Record whether the specification's integer-group choice `[E-02]` is acceptable under that guidance, or whether a divergence must be declared and justified |
| `KC-23`  | Verify that the chosen implementation uses **strong Fiat–Shamir**, by test against the specification, not by assumption (`F-INF-2`)        |
| `KC-24`  | Verify the implementation's output against an **independent verifier it did not ship**                                                    |
| `KC-25`  | Pin and record the implementation's version, provenance and supply chain                                                                  |
| `KC-26`  | Where no implementation satisfies `KC-23`–`KC-25`, **do not proceed** (`FM-P16A-22`)                                                      |
| `KC-27`  | Define a migration path to a different group or a post-quantum construction that does not require re-opening a past election's record (`BM-35`) |

`KC-22` is an open question, not a rhetorical one. The selected
specification deliberately uses an integer group rather than an elliptic
curve *"in order to make construction of election verifiers as simple as
possible"* `[E-02]`, and whether that choice is comfortable under current
German cryptographic guidance is `OD-P16A-03`, owned by PACK-16B. **This
round does not answer it and does not assume the answer.**

---

## 7. What PACK-16A does not decide

```text
The guardian count n and the quorum k
The ceremony script, venue, and witnessing arrangements
The custody medium (smartcard, HSM, air-gapped device)
The cryptographic library
The KMS or HSM product
The key identifiers and trust-store governance
The rotation schedule for board and archive signing keys
The guardian selection and appointment procedure
```

All of the above are **PACK-16B's**, except guardian appointment, which is
**LEGAL/GOVERNANCE**.

**SPECIFIED. DEFERRED TO PACK-16B. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION
READY. NOT LEGALLY ACTIVATED.**
