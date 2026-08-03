# PACK-16B — Complaint and Disqualification Model

**Round:** PACK-16B — Cryptographic Parameters, Key Ceremony and Trustee Architecture. **Specification and ADR only. No code. No cryptographic code. Not implemented. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-100`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 0. What the upstream specification provides, in full

> *"If any of the above verification steps fails, guardian G_ℓ complains to
> the election administrator and all other guardians. This triggers an
> out-of-band investigation to identify the cause of the verification
> failure.*
>
> *One possible way to investigate verification failures is to have all
> guardians release their secret information such that detailed checks can
> identify parties that provided false information or carried out erroneous
> computations. **This does not necessarily allow identification of a
> misbehaving guardian, but might do so.***
>
> *After possibly excluding or replacing a misbehaving guardian, the key
> generation procedure is started from scratch."* `[F-12]`

That is the whole of it. It supplies a **detect-and-abort** model and
names a recipient. It supplies **no** disqualification predicate, **no**
complaint format, **no** deadline, **no** adjudicator, **no** liveness
bound and **no** accountability — and it says so.

This document is EPD²'s specification of the missing layer. It adds
process and publication; it changes no computation.

---

## 1. The three problems being solved

| Problem                                                                                       | Consequence if unsolved                                                     | Solved by                        |
| --------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- | ---------------------------------- |
| **Symmetry** — a complaint is unattributable; accuser and accused look identical to observers | Any guardian can accuse any other, indefinitely, with no cost                | `KY-13` publication + §5 opening |
| **Liveness** — no bound on restarts                                                            | One malicious guardian forces unbounded restarts and the election never runs | §7 restart bound                 |
| **Authority** — no adjudicator                                                                 | Disputes end in argument, or in an administrator deciding by fiat            | §4 adjudication                  |

---

## 2. Complaint grounds

A complaint is admissible only on one of these grounds. There is no
general-purpose complaint.

| Ground                                     | Raised by                       | Evidence                                                                 | Publicly checkable without any opening? |
| ------------------------------------------ | ------------------------------- | -------------------------------------------------------------------------- | ---------------------------------------- |
| `contribution_missing`                     | Coordinator, any guardian       | Absence of a published contribution at the deadline                      | **Yes**                                 |
| `commitment_missing`                       | Coordinator, any guardian       | Absence of a pre-commitment at the deadline (`KY-09`)                    | **Yes**                                 |
| `contribution_mismatch`                    | Any guardian, Auditor, anyone   | Opened contribution ≠ published commitment (`KY-10`)                     | **Yes — arithmetically**                |
| `proof_of_possession_invalid`              | Any guardian, Auditor, anyone   | The aggregated Schnorr proof fails                                       | **Yes**                                 |
| `share_not_delivered`                      | Receiving guardian              | No ciphertext published for the ordered pair                             | **Yes**                                 |
| `share_ciphertext_malformed`               | Receiving guardian, anyone      | The nonce proof over the published ciphertext fails                      | **Yes**                                 |
| `share_inconsistent`                       | **Receiving guardian only**     | The decrypted share fails the Feldman check against the sender's commitments | **No — requires §5**                 |
| `transcript_conflict`                      | Any guardian, Auditor, mirror   | Divergent checkpoints (`CT-20`)                                          | **Yes**                                 |
| `guardian_device_lost_before_activation`   | The guardian                    | Self-declaration                                                         | n/a — no dispute                        |
| `guardian_compromise_suspected`            | Anyone, with evidence           | Incident record                                                          | Assessed, not arithmetic                |
| `guardian_independence_violation`          | Anyone, with evidence           | Undeclared relationship of a hard class (`GI-05`)                        | Assessed, not arithmetic                |

**Seven of the eleven grounds are publicly checkable without anyone
revealing a secret** — which is the direct return on publishing the
encrypted shares and running the commitment round.

---

## 3. Complaint format and deadlines

| ID       | Requirement                                                                                                   |
| -------- | ----------------------------------------------------------------------------------------------------------------- |
| `CD-01`  | A complaint is a **structured, published record**: ground, complainant, respondent, phase, evidence reference, and the complainant's signature under their published communication key |
| `CD-02`  | **Complaints are signed.** An unsigned complaint is not a complaint                                            |
| `CD-03`  | Complaints are **published in the ceremony transcript** immediately, before adjudication                       |
| `CD-04`  | A complaint on a publicly checkable ground carries **no free-text allegation** — the evidence is the arithmetic |
| `CD-05`  | The **respondent has a published deadline** to answer, stated in the manifest and not less than the ceremony's declared response window |
| `CD-06`  | Silence from a respondent past the deadline is **treated as non-contest**, and the complaint is adjudicated on the evidence |
| `CD-07`  | Every complaint is adjudicated. **None expires unadjudicated**, and none is withdrawn without a published record |
| `CD-08`  | **No administrator may mark a complaint resolved.** Resolution requires either arithmetic or an adjudication under §4 |

`CD-08` is the rule the task's prohibition names, and it is worth stating
why it matters: a complaint that can be closed administratively converts a
cryptographic dispute into an availability decision by whoever holds the
console.

---

## 4. Adjudication

| Ground class                                     | Adjudicated by                                          | Standard                                                          |
| ------------------------------------------------ | --------------------------------------------------------- | ------------------------------------------------------------------- |
| Publicly checkable (seven grounds of §2)         | **Arithmetic.** The Coordinator records the outcome; the Auditor confirms | The check either passes or fails; there is nothing to weigh |
| `share_inconsistent`                             | **Election Board with Independent Auditor concurrence**, after §5 | Evidence-based                                          |
| `guardian_compromise_suspected`                  | Election Board + Auditor                                  | Evidence-based; compromise model §3                               |
| `guardian_independence_violation`                | Election Board + Auditor                                  | Hard-test failure is decisive; soft-test is assessed              |
| `guardian_device_lost_before_activation`         | Coordinator records; no dispute                           | n/a                                                                |

| ID       | Rule                                                                                                     |
| -------- | ------------------------------------------------------------------------------------------------------------ |
| `CD-09`  | For arithmetic grounds, **no discretion exists**. A failed check is a failed check                        |
| `CD-10`  | The **Independent Auditor cannot be overruled** on whether a check passed (`KY-20`)                       |
| `CD-11`  | The adjudication, its ground and its basis are **published**                                              |
| `CD-12`  | An adjudication may not be revisited except on new published evidence, and the revisiting is itself published |
| `CD-13`  | The Ceremony Coordinator **may not adjudicate** — they convene and record (`RS-16B-03`)                    |

---

## 5. The `share_inconsistent` ground — and the disclosure it needs

This is the one ground that is not publicly checkable, and it is the one
the upstream specification's warning is about.

**The situation.** `G_ℓ` decrypts a share from `G_i` and finds it fails the
Feldman check against `G_i`'s published commitments. To an observer, two
stories are equally consistent: `G_i` sent a bad share, or `G_ℓ` is lying.

**What publication already fixes** (`KY-13`): the ciphertext is public, and
its nonce proof is public. So *which* ciphertext is in dispute is settled,
and neither party can substitute a different one afterwards. That is a real
narrowing.

**What remains.** The plaintext is inside, readable only by `G_ℓ`.

### 5.1 The opening procedure

```text
5.1  G_ℓ publishes the decryption of the disputed ciphertext, together
     with the derived symmetric keys and the value P_i(ℓ) it obtained.
5.2  Anyone recomputes k_{i,ℓ} from the published ciphertext and G_ℓ's
     communication key, checks the KDF derivation, and checks that the
     published plaintext is the XOR the ciphertext implies.
5.3  Anyone then checks the Feldman equation for the recovered P_i(ℓ)
     against G_i's published commitments.
5.4  If step 5.2 fails, G_ℓ's complaint is false and G_ℓ is disqualified.
     If step 5.2 passes and 5.3 fails, G_i sent a bad share and G_i is
     disqualified.
```

| ID       | Rule                                                                                                                     |
| -------- | -------------------------------------------------------------------------------------------------------------------------- |
| `CD-14`  | Opening is **permitted only before activation** (`GL-19`)                                                                |
| `CD-15`  | **Only the single disputed share is opened.** Never the recipient's other shares, never their own coefficients, never any other guardian's material |
| `CD-16`  | Opening reveals `P_i(ℓ)` — **one point on one guardian's polynomial**. It does not reveal the election secret, and with `k ≥ 3` it does not reach a threshold |
| `CD-17`  | Because the ceremony **restarts from scratch** after any disqualification, the opened share belongs to a discarded key set and protects nothing thereafter |
| `CD-18`  | The specification's broader suggestion — *all* guardians releasing *all* secret information `[F-12]` — is **prohibited**. It is a quorum-equivalent disclosure and `CD-15` supersedes it |
| `CD-19`  | Opening is ordered by the Election Board with Auditor concurrence, and the order and the opening are published                |

`CD-16` and `CD-17` together are why this procedure is safe here and would
not be safe after activation: one point on a discarded polynomial is
information about nothing.

**Residual, stated:** if `G_ℓ` is malicious and has published a false
complaint, it learns nothing it did not already have, and it is
disqualified. If `G_i` is malicious, it is disqualified. If **both** are
honest and a transport fault corrupted the ciphertext, the nonce proof at
step 5.2 will fail and `G_ℓ` will be wrongly disqualified — so `CD-20`
requires that a transport-fault hypothesis be tested by re-delivery before
a complaint of this ground is filed.

| ID       | Rule                                                                                                    |
| -------- | ----------------------------------------------------------------------------------------------------------- |
| `CD-20`  | Before filing `share_inconsistent`, the recipient requests **one re-delivery**, published as such. Only a second failure is a complaint |

---

## 6. Disqualification

| ID       | Rule                                                                                                              |
| -------- | --------------------------------------------------------------------------------------------------------------------- |
| `CD-21`  | Disqualification is decided by the **Election Board with Independent Auditor concurrence**, on a published ground   |
| `CD-22`  | Disqualification is possible **only before activation** (`GL-14`). After activation there is no such act            |
| `CD-23`  | A disqualified guardian's material is **destroyed**, and the destruction is attested                                |
| `CD-24`  | The ceremony **restarts from scratch** with a new guardian set — no contribution from the halted ceremony is reused |
| `CD-25`  | A replacement guardian passes the full lifecycle from `nominated`, including independence assessment (`GI-01`)      |
| `CD-26`  | The disqualification, its ground and the restart are published                                                     |
| `CD-27`  | A guardian disqualified for a **false complaint** is recorded as such, so that the record distinguishes the two directions of fault |

### 6.1 If a disqualification is needed after the joint key is formed

The joint key is formed in phase 14, and the activation lock is phase 20.
Between them, disqualification is still possible, and its consequence is
absolute:

```text
A disqualification after the joint key is computed but before activation
requires a FULL RESTART with a NEW ELECTION CONTEXT.

The joint key is discarded.
The manifest binding it is discarded.
No key material, no contribution and no share is carried forward.
```

| ID       | Rule                                                                                                          |
| -------- | ----------------------------------------------------------------------------------------------------------------- |
| `CD-28`  | A joint key formed with a contribution later found faulty is **never used**, even if arithmetically valid       |
| `CD-29`  | The discarded context is **published as discarded**, with its ground, so that its existence is not a gap in the record |
| `CD-30`  | A new context is created; it is not a continuation, and it does not inherit the old context's identifier         |

`CD-28` is the conservative call and it is deliberate: a key to which a
disqualified guardian contributed is a key whose distribution is unknown,
and the cost of discarding it before any ballot exists is a repeated
ceremony rather than a compromised election.

---

## 7. Liveness — the restart bound

Unbounded restarts are the denial-of-service the upstream model permits.

| ID       | Rule                                                                                                                    |
| -------- | -------------------------------------------------------------------------------------------------------------------------- |
| `CD-31`  | **Maximum three ceremony attempts** for one election context                                                             |
| `CD-32`  | A guardian disqualified on an arithmetic ground **may not be nominated again** for that context                          |
| `CD-33`  | On the third failure the **context is discarded** and the matter escalates to governance under `FM-16B-27`                |
| `CD-34`  | Governance's permitted outcomes are bounded: **re-run with an entirely new guardian set** · **hold the vote by another means** · **postpone with a published reason**. There is no fourth |
| `CD-35`  | Every attempt, every disqualification and the escalation are published, so that a pattern of obstruction is visible rather than inferred |

`CD-35` is the actual defence against a determined obstructor. The bound
stops the loop; the publication is what makes the obstruction attributable
to an organisation that has to explain it.

---

## 8. What this model does not achieve

| Not achieved                                                                             | Why                                                                            |
| ---------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| Full cryptographic accountability for `share_inconsistent` without any disclosure        | Would require a publicly verifiable encryption or a designated-verifier proof, which the selected construction does not provide |
| Attribution of a compromise                                                              | Compromise is assessed, not proved                                             |
| Attribution of an independence violation                                                 | Organisational fact, not arithmetic                                            |
| Prevention of obstruction                                                                | Only bounding and publication (`CD-31`, `CD-35`)                               |
| Anything at all after activation                                                         | By design — `GL-14`, `CD-22`                                                   |

| ID       | Rule                                                                                                          |
| -------- | ----------------------------------------------------------------------------------------------------------------- |
| `CD-36`  | This limitation table is **published with the ceremony transcript** (`CT-22`), so that a reader knows which faults the record can and cannot attribute |

**A better construction would make `share_inconsistent` publicly checkable
without disclosure.** That is not available in the selected specification,
it is recorded as `OD-P16B-04`, and inventing one here would be exactly the
bespoke cryptography `PACK-16A` refused.

**SPECIFIED. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY. NOT LEGALLY
ACTIVATED.**
