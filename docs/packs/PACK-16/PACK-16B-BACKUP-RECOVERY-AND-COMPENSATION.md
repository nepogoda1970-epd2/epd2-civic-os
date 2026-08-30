# PACK-16B — Backup, Recovery and Compensation

**Round:** PACK-16B — Cryptographic Parameters, Key Ceremony and Trustee Architecture. **Specification and ADR only. No code. No cryptographic code. Not implemented. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-100`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 1. The inherited rules

`PACK-16A-TRUSTEE-AND-CEREMONY-REQUIREMENTS.md` §4.2 fixed three:

```text
backup must not reduce the threshold      (KC-14)
no recovery outside a quorum ceremony     (KC-15)
no hidden master key                      (KC-02, KC-15)
```

This document turns them into an exact model, and records one thing that
turned out to be simpler than expected.

---

## 2. The comparison

| Model                                                                              | Threshold reduced?                                      | Collusion change                        | Availability gain                            | Loss scenario                      | Compromise scenario                                                    | Auditable?                      | Verdict                                               |
| ---------------------------------------------------------------------------------- | ------------------------------------------------------- | --------------------------------------- | -------------------------------------------- | ---------------------------------- | ---------------------------------------------------------------------- | ------------------------------- | ----------------------------------------------------- |
| **No backup at all**                                                               | No                                                      | none                                    | none — a lost device is a permanent absence  | Absence, survivable within `n − k` | none added                                                             | n/a                             | **Permitted**; the conservative floor                 |
| **Per-guardian, guardian-custodied encrypted backup of that guardian's own share** | **No** — one share stays one share                      | **none**                                | **Real** — device loss stops being permanent | Recoverable by that guardian alone | The guardian's own exposure surface grows slightly; nobody else's does | Yes — its existence is declared | **SELECTED**                                          |
| Split backup under independent custodians                                          | **Yes, effectively**                                    | `m` custodians become a path to a share | Real                                         | Recoverable                        | The custodians become targets                                          | Partly                          | **PROHIBITED** — an escrow with extra steps           |
| Hardware-token duplication                                                         | **Yes** — two tokens, one share, two places to steal it | Doubles the physical attack surface     | Real                                         | Recoverable                        | Either token compromises the share                                     | Poorly                          | **PROHIBITED**                                        |
| Escrowed recovery shares                                                           | **Yes**                                                 | The escrow holder is a shadow quorum    | Real                                         | Recoverable                        | The escrow is the single point                                         | No                              | **PROHIBITED**                                        |
| Compensated decryption                                                             | n/a                                                     | n/a                                     | n/a                                          | n/a                                | n/a                                                                    | n/a                             | **DOES NOT EXIST** in the selected specification — §5 |

---

## 3. The selected model

```text
PER-GUARDIAN, GUARDIAN-CUSTODIED, ENCRYPTED BACKUP
OF THAT GUARDIAN'S OWN SHARE — AND NOTHING ELSE.
```

| ID      | Rule                                                                                                                                             |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| `BR-01` | A guardian **may** hold one encrypted backup of **its own** `z_i` and `ẑ_i`. It may hold no other guardian's material                            |
| `BR-02` | The backup is under the **same guardian's sole custody**, on a second dedicated medium, meeting the same custody requirements (`KU-04`…`KU-16`)  |
| `BR-03` | **The backup does not change the threshold.** One share backed up is still one share; recovering it recovers one share, and `k` are still needed |
| `BR-04` | The backup is encrypted under a secret **only that guardian holds**. No EPD² component, no operator and no provider holds it or can compel it    |
| `BR-05` | The **existence** of a backup is declared and published; its content, location and key are not                                                   |
| `BR-06` | The backup is **destroyed at retirement** alongside the primary, with the same attestation (`GL-17`)                                             |
| `BR-07` | A guardian may decline to hold a backup. **No backup is mandatory**, and its absence is not a defect                                             |
| `BR-08` | The backup is **never transported to, held by, or accessible from** any EPD² system                                                              |

### 3.1 Why this is not an escrow

An escrow is a party other than the key holder who can produce the key. Here
the only party who can produce the guardian's share is the guardian. The
number of parties who can reach any share is unchanged, so the number who
must collude to reach `k` shares is unchanged, so **the threshold is
unchanged** — which is precisely what `KC-14` asks.

The trade is honest and small: the guardian's own exposure surface grows
from one medium to two, and that risk falls on the person who chose to take
it, in exchange for their own device loss no longer costing the election a
guardian.

---

## 4. Prohibited, absolutely

```text
NO central backup of all guardian secrets.
NO cloud backup accessible by one operator.
NO shared recovery password or passphrase.
NO vendor recovery master key.
NO single DPO, administrator or officer escrow.
NO reconstruction of any secret outside a governed quorum ceremony.
NO split backup under independent custodians.
NO backup of one guardian's material held by another guardian.
NO backup held by EPD² in any form, encrypted or otherwise.
NO "sealed envelope in a safe" arrangement — it is an escrow with furniture.
```

| ID      | Rule                                                                                                                                                                          |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `BR-09` | Any arrangement in which **fewer than `k` parties can reconstruct a decryption capability** is prohibited, whatever it is called                                              |
| `BR-10` | Any arrangement in which **a party other than the guardian can produce that guardian's share** is prohibited                                                                  |
| `BR-11` | A proposal for either is a **design-review rejection** (`FM-16B-21`), not a risk to be accepted                                                                               |
| `BR-12` | Discovery that such an arrangement exists is a **hidden-master-key detection** — `FM-16B-22`, and it blocks activation or, after activation, forces the compromise model's §4 |

---

## 5. Compensated decryption — the correction

**Compensated decryption does not exist in the selected specification
version.** The word does not appear in it; the mechanism belonged to the
1.x lineage `[F-11]`.

### 5.1 What version 2.1 actually does

```text
Each available guardian i ∈ U computes its partial decryption M_i = A^{z_i}.
U is the set of AVAILABLE guardians, with |U| = h ≥ k.
All available guardians participate, even if h > k.
Lagrange coefficients are computed over U.
The partial decryptions are combined.
```

And the specification refuses to reconstruct an absent guardian's secret,
in terms `[F-11]`:

> _"a missing secret `s_j` could be computed directly … **However, it is
> preferable to not release any missing secret `s_j` (or the secret `s`) and
> instead only release the partial decryptions** that the secret would have
> produced. This prevents the secret from being used for additional
> decryptions without the cooperation of at least `k` guardians."_

**That is the same policy `KC-15` states, arrived at independently by the
specification's authors.**

### 5.2 Consequences

| Question                                                    | Answer                                                                  |
| ----------------------------------------------------------- | ----------------------------------------------------------------------- |
| Who stores backup shares for compensation?                  | **Nobody. There are none.**                                             |
| When is compensation material generated?                    | Never                                                                   |
| How is it authenticated, encrypted, requested?              | Not applicable                                                          |
| Does compensation change the effective collusion threshold? | Not applicable — and this is why its absence is welcome                 |
| Can one guardian compensate for several absentees?          | **No such operation exists**                                            |
| Maximum permitted absences                                  | **Exactly `n − k`** — 2 in the default profile, 3 in high-assurance     |
| Does anything persist after the election?                   | Only what `GL-16`/`GL-17` permit: the guardian's share until retirement |

| ID      | Rule                                                                                                                                                                                                               |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `BR-13` | **Compensation material is not created, not stored and not permitted.** No EPD² profile reintroduces it                                                                                                            |
| `BR-14` | Absence tolerance is exactly `n − k` and is a property of the quorum, not of a recovery feature                                                                                                                    |
| `BR-15` | The mandatory rule of the round task — _compensation may recover availability within the approved threshold model; it may not create a new threshold_ — is satisfied **vacuously**, because no compensation exists |
| `BR-16` | The correction to `PACK-16A` `KC-11` is recorded in `PACK-16B-SCOPE-AND-BOUNDARY.md` §5 and changes **no requirement**                                                                                             |

### 5.3 Why this is a better position than the one PACK-16A expected

A compensation mechanism is stored material whose possession is
consequential: it must be generated, protected, authenticated, retained and
eventually destroyed, and every one of those is a place where the effective
threshold can drift without anyone deciding that it should. **A
construction that has none of it cannot drift.**

The cost is that absence beyond `n − k` is unrecoverable — which was
already the position `KC-15` took, and which §5 of the compromise model
prices honestly.

---

## 6. Recovery — the complete list of what is possible

| Situation                                           | Recoverable?                 | By whom              | How                                                 |
| --------------------------------------------------- | ---------------------------- | -------------------- | --------------------------------------------------- |
| A guardian's primary device fails, backup exists    | **Yes**                      | That guardian, alone | Restore from their own backup (`BR-01`)             |
| A guardian's device fails, no backup                | **No** — a permanent absence | —                    | Survivable while `\|U\| ≥ k`                        |
| A guardian is unavailable at decryption             | Not needed                   | —                    | The remaining quorum decrypts `[F-11]`              |
| Up to `n − k` guardians lost                        | Not needed                   | —                    | The remaining quorum decrypts                       |
| **More than `n − k` guardians lost**                | **No**                       | **Nobody**           | **The result is unobtainable.** Compromise model §5 |
| A guardian is compromised                           | n/a — this is not a loss     | —                    | Compromise model §4                                 |
| The election secret is needed for any other purpose | **No**                       | **Nobody**           | No operation exists, and none may be added          |

**There is no other recovery path, and there is no authority that can
create one.** Not the Election Board, not governance, not a court order
executed through this system, not an incident, not a vendor.

---

## 7. The trade, stated once and not minimised

```text
An unrecoverable election is preferable to a recoverable secret.
```

**What that costs when it bites:** every participant in that context voted
for nothing and must vote again. Their time was wasted, their turnout is
lost, and the organisation's confidence in the process takes damage that is
entirely deserved.

**Why it is still right:** a recovery mechanism that can produce a result
without a quorum can produce a result without an election. It exists before
it is used, it can be compelled, and its existence is exactly what the
threshold was adopted to prevent.

PACK-15 made the identical trade for credential delivery, in the same words
— _"Inventing a recovery that requires linking a person to a credential
would trade the system's central guarantee for one voter's convenience"_ —
and this round keeps it for the same reason.

**What reduces the cost honestly:** `n − k = 2` in the default profile, so
three simultaneous losses are needed; per-guardian backup, so a single
device failure is not a loss at all; and published absence, so the margin
being consumed is visible before it runs out (`IN-12`).

---

## 8. What this document does not decide

```text
The backup medium and its encryption          → PACK-16D, custody requirements
Guardian device procurement                    → PACK-16D
Retention of destruction attestations          → OD-P16A-07, PACK-09
Insurance and liability                        → GOVERNANCE, LEGAL
```

**SPECIFIED. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY. NOT LEGALLY
ACTIVATED.**
