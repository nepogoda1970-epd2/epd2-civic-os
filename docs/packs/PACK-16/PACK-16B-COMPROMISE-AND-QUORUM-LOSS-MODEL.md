# PACK-16B — Compromise and Quorum-Loss Model

**Round:** PACK-16B — Cryptographic Parameters, Key Ceremony and Trustee Architecture. **Specification and ADR only. No code. No cryptographic code. Not implemented. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-100`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 0. Two claims that must never be collapsed

The guardians protect **confidentiality**, not **integrity**. The
specification states it directly: *"Compromised guardians — whether
instantiated as humans or hardware — cannot compromise the integrity of the
election tallies"*, and *"the role of guardians is to protect
confidentiality of votes"* `[F-13]`.

```text
SECRECY CLAIM     — can ballots be read by anyone who should not?
INTEGRITY CLAIM   — is the published result the correct count of the
                    published ballots?
```

**A guardian compromise attacks the first and not the second**, and every
row below reports them separately. Collapsing them into "the election was
compromised" or "the election was fine" is the reporting failure this
document exists to prevent.

---

## 1. Severity classification

| Class                              | Definition                                                                       | Detection                                              |
| ---------------------------------- | ---------------------------------------------------------------------------------- | -------------------------------------------------------- |
| `suspected_exposure`               | Credible indication that material *may* have been exposed                        | Report, anomaly, third-party notification              |
| `confirmed_device_compromise`      | A guardian's device is confirmed compromised; extraction unproven                | Forensics, vendor advisory, guardian report            |
| `confirmed_key_extraction`         | The share itself is confirmed disclosed                                          | Forensics, disclosure, observed use                    |
| `shared_operator_compromise`       | One party is found to have reached **two or more** guardians' devices             | Independence finding (`GI-05`), audit                  |
| `multiple_guardian_compromise`     | Two or more guardians compromised, **below** `k`                                  | Aggregation of the above                               |
| **`quorum_compromise`**            | **`k` or more guardians compromised or colluding**                                 | **Usually none** — `T-P16A-19`                         |
| `parameter_generation_compromise`  | The parameters are not what the published rule produces                          | **Reproduction — `TV-01`**                             |
| `ceremony_transcript_compromise`   | The transcript is altered, forked or inconsistent across mirrors                 | Checkpoint chain, mirror comparison (`CT-20`)          |
| `verifier_compromise`              | A verifier reports success on material that does not verify                      | A second, independent verifier                         |

---

## 2. The matrix

Columns: **detection · immediate action · election-state effect ·
notification · public disclosure · evidence preservation · secrecy claim ·
integrity claim · may continue? · may certify?**

| Class                             | Immediate action                                          | State effect                            | Notification                       | Public disclosure                     | Secrecy claim | Integrity claim | Continue?                     | Certify?                     |
| --------------------------------- | ----------------------------------------------------------- | ----------------------------------------- | ------------------------------------ | --------------------------------------- | ------------- | --------------- | ------------------------------- | ------------------------------ |
| `suspected_exposure`              | Guardian → `suspected_compromise`; investigate; **do not move, delete or rotate the material — it is evidence** | none yet | Auditor + Board, out of band | On confirmation or clearance, always | **intact, provisionally** | intact | yes, pending outcome | pending |
| `confirmed_device_compromise`     | Guardian → `confirmed_compromise`; §3                      | §3                                       | Auditor + Board + guardians          | **Yes, with the class**                 | **degraded**  | intact          | §3                             | §3                            |
| `confirmed_key_extraction`        | Treat that share as public                                 | §3                                       | Same                                  | Yes                                     | **degraded**  | intact          | §3                             | §3                            |
| `shared_operator_compromise`      | Assess **how many** guardians the operator reaches         | §3 or §4                                 | Same                                  | Yes                                     | degraded or **lost** | intact  | §3 or §4                       | §3 or §4                      |
| `multiple_guardian_compromise` (< `k`) | Count against `k`; §3                                 | §3                                       | Same                                  | Yes, with the count                     | **degraded**  | intact          | §3                             | §3                            |
| **`quorum_compromise` (≥ `k`)**   | **§4**                                                     | **§4**                                   | Same, immediately                     | **Yes, in full**                        | **LOST**      | intact          | **No**                         | **Integrity only, §4**        |
| `parameter_generation_compromise` | **Halt everything using the parameter set**                 | Parameter set → `prohibited`             | Auditor + Board + Cryptographic Reviewer | Yes, in full                        | **LOST**      | **LOST**        | **No**                         | **No — annul**                |
| `ceremony_transcript_compromise`  | Halt; publish every divergent view                          | Ceremony halts; if activated, §4-adjacent | Same                                  | Yes, with all views                     | intact        | **in question** | No                             | **Uncertifiable** until resolved |
| `verifier_compromise`             | Re-verify with an independent verifier                      | none, if the record is sound             | Auditor + Board                       | Yes                                     | intact        | **unproven until re-verified** | yes | after re-verification |

---

## 3. Compromise below the threshold

Fewer than `k` guardians compromised. The secret is **not** reconstructible
from what the adversary holds.

| Election phase                        | Outcome                                                                                                     |
| ------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| Before activation                     | **Disqualify; restart the ceremony from scratch** (complaint model §6). Cheap and clean                     |
| After activation, before `issuance_open` | **Discard and reconstitute the context** — new ceremony, new keys. Still no ballots exist                |
| After `issuance_open`, before voting  | **Governance decision, bounded:** `pause` → `discard and reconstitute`, or `continue with a published notice` |
| **During voting**                     | **Governance decision, bounded:** `pause` · `continue with a published notice` · `abort and re-run`. **Never re-key** |
| After closure, before tally           | **Continue.** The ballots are fixed; the compromised guardian's share is one of `n`, and `< k` cannot decrypt |
| After the tally                       | Publish the finding against the completed election                                                          |

| ID       | Rule                                                                                                                    |
| -------- | -------------------------------------------------------------------------------------------------------------------------- |
| `CM-01`  | **No re-keying of a running election.** Re-keying either invalidates cast ballots or requires decrypting them (`KC-12`, `GL-14`) |
| `CM-02`  | A compromised guardian is **not replaced**. They become an expected absence at decryption                                |
| `CM-03`  | The **remaining margin** — how many further losses the context can absorb — is published with the finding               |
| `CM-04`  | Where compromise consumes the margin so that `n − k` is exhausted, §5 applies **pre-emptively**: the Board decides before quorum is actually lost |
| `CM-05`  | The secrecy claim is reported as **degraded, with the count**: "one of five guardians compromised; three are required to decrypt" — not as "unaffected" |

`CM-05` is the honest middle position. Nothing was decrypted; the margin
against decryption shrank. Reporting that as "no impact" is false and
reporting it as "compromised" is also false.

---

## 4. Quorum compromise — `k` or more

**The secret is reconstructible by the adversary. Ballot secrecy for that
context is lost, and no process restores it.**

| ID       | Rule                                                                                                            |
| -------- | ------------------------------------------------------------------------------------------------------------------- |
| `CM-06`  | The context is **suspended immediately**. No further ballots are accepted                                        |
| `CM-07`  | **The secrecy claim is publicly withdrawn**, in those words, naming the context and the date range affected       |
| `CM-08`  | **The integrity claim may survive** and is assessed separately — the guardians cannot alter the tally `[F-13]`, and the board, the proofs and the checkpoints are untouched by a guardian compromise |
| `CM-09`  | Governance decides, from a bounded set: **annul and re-run** · **complete the tally and publish it with the withdrawn secrecy claim** · **abandon the vote and decide by another means** |
| `CM-10`  | **Completing the tally is permissible** where the integrity claim holds and the participants are told plainly that their ballots were readable by the adversary. It is not the comfortable option and it is sometimes the right one — a re-run does not un-disclose what was already disclosed |
| `CM-11`  | Every participant in the context is notified that ballot secrecy for that vote is lost, **without stating or implying how any individual voted** |
| `CM-12`  | The compromised material is **preserved as evidence**, not destroyed, until the investigation concludes            |
| `CM-13`  | **No re-keying, no threshold change, no guardian substitution.** The context is finished one way or the other      |

`CM-10` is the paragraph that will be argued about. A re-run restores
future secrecy and restores nothing about the ballots already cast; where
the integrity claim is intact, annulling additionally discards a correct
count. The decision belongs to governance, the options are bounded, and
**the one thing that may not happen is quiet continuation.**

---

## 5. Quorum loss

More than `n − k` guardians permanently unavailable. **Nobody can decrypt.**

```text
Available guardians < k
   → the result is UNOBTAINABLE
   → the context is ANNULLED
   → a RE-RUN is the only remedy
```

| ID       | Rule                                                                                                          |
| -------- | ----------------------------------------------------------------------------------------------------------------- |
| `CM-14`  | Quorum loss is declared by the **Election Board with Independent Auditor concurrence**, on published evidence   |
| `CM-15`  | Declaration is preceded by a **documented recovery attempt**: contacting every guardian, exhausting the backup path of `BR-01`, and a published waiting period |
| `CM-16`  | On declaration the context is **annulled** and the participants are told that the result cannot be produced      |
| `CM-17`  | A re-run is a **new context**: new manifest, new ceremony, new guardians where needed, new keys, new board namespace |
| `CM-18`  | **The prohibited responses of `PACK-16B-BACKUP-RECOVERY-AND-COMPENSATION.md` §4 apply with full force here**, because this is the moment they will be proposed |
| `CM-19`  | The ballots of the annulled context are **never decrypted**, by anyone, ever — including after the re-run        |

### 5.1 The list that must be refused at this exact moment

```text
NO key escrow, produced now or discovered now.
NO recovery guardian.
NO reconstruction of a missing share from the others outside a quorum.
NO lowering of k "just for this decryption".
NO administrative override.
NO vendor assistance that yields a share.
NO "the guardians agreed informally" quorum.
```

**This is where the architecture is tested**, because the cost is concrete,
the people affected are identifiable, and the fix looks small. The answer
is `BR-09` and `BR-10`: any arrangement in which fewer than `k` parties can
reconstruct a decryption capability is prohibited, whatever it is called,
and discovering that one exists is `FM-16B-22`.

---

## 6. What may never happen, in any class

```text
NO break-glass decryption.
NO emergency master key.
NO administrative quorum override.
NO temporary threshold reduction.
NO support-vendor recovery key.
NO re-keying of a running election.
NO guardian replacement after activation.
NO decryption before formal closure (pre-closure prohibition, §7).
NO reconstruction of any absent guardian's secret.
```

Break-glass **may** stop a service, block further operations, preserve
evidence and notify. It **may not** decrypt, reconstruct, replace a
guardian, alter a quorum, publish a tally or modify a ceremony transcript
(`KC-18`, and `PACK-16A-ROLE-SEPARATION-MATRIX.md` §7).

---

## 7. Pre-closure prohibition

Before formal closure of voting, the following are prohibited absolutely:

```text
decryption share generation
compensated decryption            (does not exist — BR-13)
partial decryption
test decryption using the production key
proof generation that leaks an aggregate
trustee preview of any ciphertext
trustee readiness testing against real ciphertexts
```

| ID       | Rule                                                                                                          |
| -------- | ----------------------------------------------------------------------------------------------------------------- |
| `CM-20`  | **No operation exists** that produces a decryption share before the context reaches `voting_closed` (`BM-21`)   |
| `CM-21`  | Production key material is **never used in rehearsal** (`KY-28`, `KY-32`)                                       |
| `CM-22`  | An attempted pre-closure decryption is `FM-16B-25` — **abort and annul**, because the attempt is evidence of either a defect or an intent |
| `CM-23`  | The specification's own pre-decryption gating — every guardian confirming the ballot-set verifications **before** any key material is applied `[F-11]` — is adopted as a requirement, not an option |

### 7.1 Permitted pre-closure checks

```text
public-key validation, from published values
synthetic test vectors under SEPARATE TEST KEYS
guardian authentication and device health
ceremony software integrity verification
transcript availability and checkpoint chain verification
mirror agreement
```

| ID       | Rule                                                                                                    |
| -------- | ----------------------------------------------------------------------------------------------------------- |
| `CM-24`  | Every readiness check uses **test keys and synthetic ciphertexts**, never production ballots              |
| `CM-25`  | A readiness check that requires a production ciphertext is **not a readiness check** and is refused       |
| `CM-26`  | Readiness outcomes are published as outcomes; they carry no count and no aggregate (`ADR-094`)            |

---

## 8. Notification

| Event                        | Public | Participants | Auditor | Out of band | Timing                                     |
| ---------------------------- | ------ | ------------ | ------- | ----------- | -------------------------------------------- |
| `suspected_exposure`         | on outcome | no       | **yes** | **yes**     | Immediately to the Auditor                  |
| `confirmed_device_compromise`| **yes** | if the state changes | yes | yes      | On confirmation                             |
| **`quorum_compromise`**      | **yes, in full** | **yes** | yes | yes      | **Immediately**                             |
| `parameter_generation_compromise` | **yes, in full** | yes | yes | yes  | Immediately                                 |
| `ceremony_transcript_compromise` | **yes, with every divergent view** | yes | yes | yes | Immediately                          |
| Quorum shortfall approaching | **yes** | yes      | yes     | yes         | When the margin reaches 1 (`IN-12`)         |
| **Quorum loss**              | **yes** | **yes**  | yes     | yes         | On declaration                              |
| Verifier compromise          | yes    | no           | yes     | yes         | On confirmation                             |

**Never notified:** any ballot content · any person-level participation
statement · any partial outcome · anything implying how anyone voted
(`CM-11`, PACK-15 §24).

---

## 9. What this document does not decide

```text
Forensic procedure and tooling            → PACK-17
Incident-response runbooks                 → PACK-17
Legal consequences of a compromise         → LEGAL/GOVERNANCE
Insurance and liability                    → GOVERNANCE
```

**SPECIFIED. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY. NOT LEGALLY
ACTIVATED.**
