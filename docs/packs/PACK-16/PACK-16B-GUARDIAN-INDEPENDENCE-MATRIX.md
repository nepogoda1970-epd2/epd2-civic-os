# PACK-16B — Guardian Independence and Collusion Matrix

**Round:** PACK-16B — Cryptographic Parameters, Key Ceremony and Trustee Architecture. **Specification and ADR only. No code. No cryptographic code. Not implemented. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-100`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 0. Independence is a factual claim, not a formal one

The threshold model's entire security rests on `k` guardians being unable
to act as one. Nothing in the cryptography enforces that; it is an
organisational property, and it is the property most easily satisfied on
paper and violated in fact.

**The failure mode is specific and mundane:** five guardians with five
names, five accounts and five devices, all administered by one person,
backed up by one operator, on one cloud tenant. Formally five. Actually
one. `BB-28` records the same failure for mirrors — *"three mirrors in
three availability zones look like three mirrors and are one operator"* —
and it is the same mistake with higher stakes here, because mirror
divergence is detectable and quorum collusion is not.

> **Two guardians who share any single point of control are one guardian.**

---

## 1. The Guardian Independence Matrix

Assessed for **every pair** of nominated guardians, before approval. A pair
failing any **hard** test is not independent and the nomination is refused.
A pair failing a **soft** test requires a recorded, published mitigation.

| #  | Test — do the two guardians share…      | Class    | Why it matters                                                                             | Acceptable mitigation                                    |
| -- | ---------------------------------------- | -------- | -------------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| 1  | **The same employer**                    | **hard** | One employer can instruct both                                                              | none — a different guardian is nominated                  |
| 2  | **The same reporting line**              | **hard** | One manager can instruct both, even across employers                                        | none                                                      |
| 3  | **The same contractor or service provider** for ceremony support | **hard** | The provider is a single point of control over both       | Distinct providers, contractually independent             |
| 4  | **The same cloud account or tenant**     | **hard** | One account owner reaches both                                                              | Separate tenants under separate billing and ownership     |
| 5  | **The same password manager or vault**   | **hard** | One vault holder reaches both                                                               | none — separate custody                                   |
| 6  | **The same HSM or HSM cluster**          | **hard** | *An HSM does not convert one administrator into a threshold* (§4)                            | Separate devices under separate administration            |
| 7  | **The same backup operator**             | **hard** | The backup operator holds both                                                              | Per-guardian custody only (backup doc §3)                 |
| 8  | **The same legal entity**                | **hard** | One entity decides for both                                                                 | none                                                      |
| 9  | **The same system administrator**        | **hard** | Administrative access is control                                                            | none                                                      |
| 10 | **The same funding control**             | **soft** | Financial dependence is instruction by another name                                          | Published declaration; Board and Auditor assessment       |
| 11 | **The same office or physical premises** | **soft** | Proximity enables coordination and shared physical compromise                                | Acceptable if 1, 2, 8 and 9 all pass; recorded            |
| 12 | **The same incident commander**          | **soft** | An incident is when independence is most likely to be overridden                             | Declared; the Incident Commander may not direct guardians (`RS-16B-11`) |
| 13 | **The same household or family relationship** | **soft** | Personal dependence                                                                     | Declared and assessed                                     |
| 14 | **The same device supply and imaging process** | **soft** | A single build compromises all                                                        | Distinct procurement, or independent attestation of each  |
| 15 | **The same network egress under one operator's control** | **soft** | Traffic manipulation and availability control                                | Declared; controlled-hybrid ceremony reduces it           |

### 1.1 The rule

| ID       | Rule                                                                                                                       |
| -------- | ------------------------------------------------------------------------------------------------------------------------------ |
| `GI-01`  | Independence is assessed **pairwise**, for all `n(n−1)/2` pairs, before ceremony enrolment                                  |
| `GI-02`  | A **hard** failure makes the pair non-independent. The nomination is refused; there is no mitigation and no waiver          |
| `GI-03`  | A **soft** failure requires a **published** mitigation and Independent Auditor concurrence                                  |
| `GI-04`  | Guardians **declare** their relationships; the declaration is part of the ceremony transcript and is public                 |
| `GI-05`  | A false or incomplete declaration discovered later is a `guardian_independence.violation_detected` event and is treated under §5 |
| `GI-06`  | The assessment is **re-run** if any guardian's employer, organisation or custody arrangement changes before activation      |
| `GI-07`  | After activation the assessment cannot be re-run to any effect, because no guardian may be replaced (`GL-14`) — which is why §1 happens **before** enrolment |
| `GI-08`  | **Distinctness of usernames, accounts, email addresses or device serial numbers is not evidence of independence** and may not be cited as such |

`GI-08` exists because it is the argument that will actually be made.

---

## 2. The composition test

Pairwise independence is necessary and not sufficient. The **set** must
also satisfy:

| ID       | Test                                                                                                                 |
| -------- | ------------------------------------------------------------------------------------------------------------------------ |
| `GI-09`  | **No organisation supplies `k` guardians** (`GQ-01`)                                                                  |
| `GI-10`  | Guardians come from at least **`k` organisationally distinct bodies** (`GQ-03`)                                        |
| `GI-11`  | **At most `k − 1`** guardians are Election Officers or Election Board members (`GQ-11`) — so any collusion needs an external participant |
| `GI-12`  | No **transitive** dependency chain of hard class exists linking `k` guardians through a common controller             |
| `GI-13`  | The set is assessed as a whole by the Election Board **with Independent Auditor concurrence**, and the assessment is published |

`GI-12` is the test that catches the arrangement pairwise checks miss: A
and B independent, B and C independent, A and C independent — and all three
administered by the same managed-service provider two levels down. **The
question is not whether pairs are independent; it is whether any single
party can reach `k` of them.**

---

## 3. The Guardian Collusion Matrix

What each combination achieves, and what stops it.

| Combination                                    | Achieves                                                                            | Detectable? | Control                                                                 |
| ---------------------------------------------- | ------------------------------------------------------------------------------------- | ----------- | ------------------------------------------------------------------------- |
| 1 guardian alone                               | **Nothing.** One share reveals nothing about the secret                              | n/a         | The construction                                                        |
| `k − 1` guardians                              | **Nothing.** Below threshold                                                         | n/a         | The construction                                                        |
| **`k` guardians**                              | **Decrypt every individual ballot; compute an early tally offline**                  | **No**      | `GI-09`…`GI-12`; publication of guardian identity; nothing technical    |
| `k` guardians + Bulletin-Board Operator        | The above, plus correlation of decrypted content with board entries                  | No          | `BB-29`; `GQ` role table; separate organisations                        |
| `k` guardians + Credential Authority           | The above, plus a path toward participation attribution                              | No          | Role table; PACK-15 boundary; separate audit streams                    |
| `k` guardians + Voting-System Operator         | The above, plus casting-path visibility                                              | No          | Role table                                                              |
| `k` guardians + System Administrator           | The above, plus infrastructure cover for the act                                     | No          | `KC-16`; role table                                                     |
| `k` guardians + Election Officer               | The above, plus window control — enabling a chosen decryption moment                 | No          | `GQ-11`, `GQ-12`                                                        |
| **Ceremony Coordinator + any guardians**       | Nothing additional — the Coordinator holds **no** secret material                    | n/a         | `RS-16B-03`                                                             |
| **Independent Auditor + guardians**            | Nothing additional — the Auditor cannot mutate ceremony state                        | n/a         | Role table                                                              |
| A single **managed-service provider** reaching `k` guardians' devices | **A quorum, without any guardian consenting**                     | **No**      | **`GI-12` — this is the combination the composition test exists for**   |
| `k` guardians **across two elections** via key reuse | Retroactive decryption of a completed election                                  | No          | **`GQ-09` — key reuse prohibited**                                      |

### 3.1 The row that matters most

**A single managed-service provider reaching `k` guardians' devices is a
quorum that no guardian participated in.** It is invisible, it requires no
conspiracy, and every guardian passes a pairwise independence check.

`GI-12` and the custody rules of `PACK-16B-KEY-CUSTODY-REQUIREMENTS.md` §3
exist for this row alone: dedicated devices, per-guardian custody, no
shared administration, no shared imaging, no shared vault.

---

## 4. An HSM does not convert one administrator into a threshold

Stated as a rule because it is the most attractive shortcut available.

```text
If one operator can invoke a quorum through one HSM cluster,
the architecture FAILS, regardless of what the HSM policy says.
```

| ID       | Rule                                                                                                            |
| -------- | ------------------------------------------------------------------------------------------------------------------- |
| `GI-14`  | Two guardians' key material **may not reside in the same HSM or the same HSM cluster** (test 6, hard)            |
| `GI-15`  | An HSM authorisation policy requiring `m` operator cards is **not** a threshold in the sense of `KC-01`; it is a control inside one device under one administration |
| `GI-16`  | A design in which any single operator, provider or cluster can produce `k` decryption shares is **rejected at design review**, not mitigated |
| `GI-17`  | Where an HSM is used it holds **exactly one guardian's** material, under that guardian's organisation's sole administration |

---

## 5. When independence turns out to be false

Discovered after enrolment, independence failures cannot be fixed by
substitution, because **no guardian may be replaced after activation**
(`GL-14`).

| When discovered                        | Outcome                                                                                                |
| -------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| Before ceremony enrolment              | Nomination refused; another guardian nominated. Ordinary                                              |
| During the ceremony, before activation | **Guardian disqualified**; ceremony **restarts from scratch** with a new set (complaint model §6)      |
| After activation, before voting opens  | **The election context is discarded and reconstituted** — new context, new ceremony, new keys          |
| After voting opens                     | **Governance decision, bounded**: `pause` → `abort` and `re-run`, or `continue with a published notice` where the affected guardians number fewer than `k` and the dependency does not reach `k` |
| After closure, before tally             | The tally proceeds; the finding is published with the result                                          |
| After the result is published           | Published as a **finding against a completed election**; the result is not retroactively annulled unless the dependency reached `k`, in which case **ballot secrecy must be treated as lost** and `PACK-16B-COMPROMISE-AND-QUORUM-LOSS-MODEL.md` §4 governs |

**Where a dependency is found to have reached `k`, the secrecy claim for
that context does not survive**, and no amount of after-the-fact process
restores it. The election's *integrity* claim may survive — the guardians
protect confidentiality, not integrity `[F-13]` — and the two must be
reported separately rather than collapsed into "the election was fine" or
"the election was compromised".

---

## 6. Publication

| Published                                                          | Not published                                        |
| ------------------------------------------------------------------ | ----------------------------------------------------- |
| Guardian identity and organisation (`GQ-06`)                       | Guardian home address or personal contact data       |
| The independence declarations                                      | Commercially confidential contract terms             |
| The pairwise assessment outcome (pass / soft-with-mitigation)      | The deliberations behind a refusal of a nomination   |
| Soft-failure mitigations                                           | —                                                     |
| The composition-test outcome and the Auditor's concurrence         | —                                                     |
| Any later independence finding and its consequence                 | —                                                     |

**Guardian identity is the one deliberate identity in this architecture,
and it is public.** A guardian nobody can name is a guardian nobody can
hold to account, and `TP-07` already required it.

---

## 7. What this document does not decide

```text
Who the guardians are                       → GOVERNANCE
Contractual and liability arrangements       → GOVERNANCE, LEGAL
Due-diligence procedure detail               → GOVERNANCE, lifecycle §2
Device procurement                           → PACK-16D, custody requirements
```

**SPECIFIED. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY. NOT LEGALLY
ACTIVATED.**
