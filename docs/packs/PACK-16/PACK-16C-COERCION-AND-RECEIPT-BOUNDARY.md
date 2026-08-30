# PACK-16C — Coercion and Receipt Boundary

**Round:** PACK-16C — Casting, Receipt, Verification Client, Bulletin Board and Election Record. **Specification and ADR only. No code. No cryptographic implementation. Not implemented. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-101`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

**This document extends `PACK-16A-COERCION-AND-RECEIPT-BOUNDARY.md`. That
document's permitted-claims registry (`PC-01`…`PC-11`) and prohibited-claims
registry stand unchanged.** What follows adds the claims that only become
sayable — or only become dangerous — once the receipt, the Verification
Client and the board exist.

---

## 1. The boundary, restated once

```text
EPD2-HOM-1 is COERCION-MITIGATING, not coercion-resistant.

Nothing in PACK-16C changes that, and no artefact PACK-16C
introduces may be described as if it did.
```

---

## 2. The five honest facts about the receipt

| #   | Fact                                      | Consequence                                                                                                     |
| --- | ----------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| 1   | The receipt **proves participation**      | A coercer who demands it learns the person voted (`T-P16A-30`)                                                  |
| 2   | The receipt **does not prove the choice** | It is useless for vote-buying on content                                                                        |
| 3   | **Screenshots can still be coerced**      | Anything on screen during casting can be demanded, including the review screen — which _does_ show the choice   |
| 4   | **Home-device observation is unsolved**   | _"If the coercer can monitor the voter throughout the vote casting period, then resistance is futile"_ `[E-46]` |
| 5   | **The verification UI can be misused**    | A coercer can watch a voter verify, and a fake verifier can lie to a voter (`T-P16A-27`, `T-P16A-28`)           |

| ID      | Rule                                                                                                                                                                                                                  |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CB-01` | **No cryptographic claim of receipt-freeness is made**, and none may be made, unless a formal justification specific to the composed EPD² profile is published and externally reviewed                                |
| `CB-02` | Fact 3 is the sharpest: **the review screen shows the choice**. The receipt is minimal precisely because the screen before it is not, and the interface must not extend the screen's exposure into a durable artefact |

---

## 3. Permitted claims — PACK-16C additions

These extend `PC-01`…`PC-11`. Each is sayable because it is true of what
this round specifies.

| ID      | Permitted claim                                                                                                     |
| ------- | ------------------------------------------------------------------------------------------------------------------- |
| `PC-12` | "Your receipt shows that a ballot was published. It does not show what is in it."                                   |
| `PC-13` | "You can check that your ballot is on the public list, from any device, without logging in."                        |
| `PC-14` | "Nobody needs an account to check that the published result matches the published ballots."                         |
| `PC-15` | "A ballot cannot be removed from the public list without that being visible."                                       |
| `PC-16` | "You can check, before you cast, that the app encrypted what you chose — and you can do that as often as you like." |
| `PC-17` | "A ballot you check in that way is published openly and is not counted. You then cast a fresh one."                 |
| `PC-18` | "No count, no result and no turnout figure is published before voting closes."                                      |
| `PC-19` | "Your receipt does not contain your name, your membership, or anything that links to you."                          |

---

## 4. Prohibited claims — PACK-16C additions

| ID      | **Prohibited** claim                                         | Why                                                                           |
| ------- | ------------------------------------------------------------ | ----------------------------------------------------------------------------- |
| `PB-12` | "Your receipt proves your exact vote"                        | False, and it invites coercers to demand it                                   |
| `PB-13` | "The receipt makes coercion impossible"                      | False — participation coercion is unaffected                                  |
| `PB-14` | "The receipt makes vote buying impossible"                   | False — buying participation, or buying a challenge transcript, is unaffected |
| `PB-15` | "The receipt proves no one can discover your vote"           | Conflates the receipt with the threshold                                      |
| `PB-16` | "Verification proves your device was honest"                 | Verification proves **recorded-as-cast**, not cast-as-intended                |
| `PB-17` | "The challenge guarantees your vote was encrypted correctly" | Probabilistic and dependent on take-up (`CH-25`)                              |
| `PB-18` | "The bulletin board is tamper-proof"                         | It is **tamper-evident**, and only if someone checks                          |
| `PB-19` | "The election record proves nobody voted twice"              | It does not, and cannot — `VP-17`                                             |
| `PB-20` | "Independent verification has confirmed this election"       | Not until an independent verifier has actually run (`BM-28`)                  |
| `PB-21` | Any complete-BSI-conformity or certification claim           | `SB-06`, `VO-08`                                                              |

| ID      | Rule                                                                                                                                                                |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CB-03` | **Every prohibited claim requires a permitted alternative**, and the alternative is in the governed content catalogue rather than left to whoever writes the screen |
| `CB-04` | **The prohibited-claims list is scannable.** Enforcement is a check over published participant-facing text, not a review convention (`FIR-INV-015`)                 |

---

## 5. Where verification itself becomes the weapon

| Threat                                                          | What PACK-16C does                                                                                                                                        | What remains                                                                                     |
| --------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| Coercer watches the voter verify                                | Verification shows **presence of a code**, nothing about content (`BB-22`)                                                                                | The coercer learns the person voted                                                              |
| Coercer demands the confirmation code                           | The code proves publication only                                                                                                                          | Same                                                                                             |
| **Fake verification interface**                                 | Verification runs on a **published, separate origin** with a published build; the record is downloadable and checkable by a third-party verifier (`IV-*`) | A voter who trusts a fake site can be told anything — mitigated by independence, not eliminated  |
| Coercer demands a **challenge transcript** as proof of a choice | A challenged ballot is **never counted** (`CH-05`), so a transcript proves nothing about the cast ballot                                                  | The coercer may still demand the pattern "challenge showing X, then cast" — unsolved, and stated |
| Remote desktop during the session                               | Prohibited in participant guidance; no technical defence                                                                                                  | Unsolved (`T-P16A-31`)                                                                           |
| Assisted session where the assistant coerces                    | PACK-15's assistance boundary unchanged; the choice stays the voter's (`CH-28`)                                                                           | Unsolved in the remote setting                                                                   |

| ID      | Rule                                                                                                                                                                                                                                                                                                                                        |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CB-05` | **The challenge-transcript coercion pattern is named and not solved.** A coercer can ask for a challenge showing a specific vote and then a cast immediately after. Nothing in the record distinguishes that from honest use. It is recorded as `T-P16C-*` and is a reason the in-person channel remains the coercion answer (`OD-P16A-09`) |
| `CB-06` | **No interface text may suggest that a challenge transcript demonstrates how the voter voted**, and the challenge-result screen states explicitly that this ballot was not counted (`CH-29`)                                                                                                                                                |

---

## 6. What is offered instead of a promise

```text
For a voter who is being watched, this system does not have an answer.
The answer is a different channel — in person, or on paper.
```

| ID      | Rule                                                                                                                                                                               |
| ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CB-07` | **Every context with material coercion risk must offer an alternative channel**, and where none exists the context is not activated electronically (`AX-42` lineage, `OD-P16A-09`) |
| `CB-08` | The participant-facing text says this plainly rather than implying the electronic channel is safe for everyone                                                                     |

---

## 7. What this document does not decide

```text
The German participant-facing texts        → PACK-15 content-catalogue lineage
Scope-level channel reconciliation          → OD-P16A-09, GOVERNANCE
A formal receipt-freeness argument          → OD-P16A-06 / TV-08, external review
```

**SPECIFIED. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY. NOT LEGALLY
ACTIVATED.**
