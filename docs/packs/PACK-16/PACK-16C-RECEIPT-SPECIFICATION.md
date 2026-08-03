# PACK-16C — Receipt Specification

**Round:** PACK-16C — Casting, Receipt, Verification Client, Bulletin Board and Election Record. **Specification and ADR only. No code. No cryptographic implementation. Not implemented. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-101`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 1. What the receipt is allowed to prove

```text
A ballot artefact carrying this confirmation reference
was accepted and published in this election record.

That is all. Nothing about the choice inside it.
```

**What it must never prove:**

```text
which candidate or option was selected
the plaintext ballot content
an identity-to-ballot link
a credential-to-ballot link
a continuation-to-ballot link
```

---

## 2. Contents

| Field | Purpose | Notes |
| ----- | ------- | ----- |
| `election_context_reference` | Which election | Public value |
| `confirmation_code` | What the voter looks up | Derived only from the ballot's encryptions and `H_E` (`BM-03`) |
| `board_checkpoint_reference` | The checkpoint current at issuance | Lets the voter detect a later rollback (`BB-25`) |
| `sealed_batch_reference` | The `batch_window_id` in which the ballot's leaf will be — or has been — committed | The bounded publication obligation (`PA-03`, `PA-10`) |
| `publication_status` | `ACCEPTED_PENDING_BATCH_COMMITMENT`, `COMMITTED`, `PUBLISHED_AFTER_CLOSURE` or `PUBLICATION_DISPUTED` | Honest about both phases (`PA-*` §4) |
| `verification_instructions` | Where and how to check | Includes the **separate verification origin** |
| `receipt_schema_version` | Interpretability over time | — |

**Prohibited in the receipt:**

```text
ballot plaintext                  human-readable choice
any nonce or opening              challenge secret
credential reference              identity
continuation reference            exact consumption timestamp
exact submission timestamp        board sequence number
internal object ID                retry token
IP address                        device or build fingerprint
leaf index within the batch       batch occupancy or any count
any other occupant's leaf         position among real ballots
remaining cast entitlement        remaining challenge entitlement
any link to a challenge artefact  any link to a cast artefact
```

| ID       | Rule                                                                                                              |
| -------- | --------------------------------------------------------------------------------------------------------------------- |
| `RE-01`  | **The receipt is derivable entirely from public data plus the confirmation code.** It contains no secret, so losing it costs nothing and copying it proves nothing beyond publication |
| `RE-02`  | **No timestamp finer than the context's `timestamp_granularity`** appears on the receipt (`BB-23`, `CC-06`). An exact time is a correlation handle |
| `RE-03`  | **No board position, index, neighbour or total** appears on the receipt (`BB-23`) |
| `RE-04`  | The receipt is **re-issuable** from the confirmation code at any time via the Verification Client; it is not a bearer token and nothing depends on retaining it |
| `RE-05`  | A **public evidentiary challenge** receives a receipt carrying the public-challenge confirmation reference, the sealed-batch commitment reference, verification instructions and an **explicit `NOT COUNTED` status**, and no indication of its contents beyond what the opening will intentionally disclose (`CH-21`, `API-54`) |
| `RE-20`  | **A local diagnostic challenge produces no receipt of any kind**, because it produces no artefact anywhere (`CH-42`, `TC-58`) |
| `RE-21`  | **No receipt reveals the remaining cast entitlement, the remaining public-challenge entitlement, or any residual counter.** The voter is told before acting that the public audit challenge is available once (`CH-51`, `CN-37`) |
| `RE-22`  | **The public-challenge receipt and the final cast receipt are independent artefacts with independent references** and nothing on either links them (`CH-49`) |

---

## 3. Publication status, stated honestly

At step 20 the ballot is accepted but is not yet committed in a sealed batch, and will not be individually published until closure (`PA-*` §4).

| ID       | Rule                                                                                                          |
| -------- | ----------------------------------------------------------------------------------------------------------------- |
| `RE-06`  | The receipt states `publication_status` truthfully. **A receipt never claims publication that has not happened**, and never conflates `COMMITTED` with `PUBLISHED_AFTER_CLOSURE` |
| `RE-07`  | Where status is `ACCEPTED_PENDING_BATCH_COMMITMENT`, the receipt carries the **signed publication commitment** (`CN-06`) naming the batch window, and tells the voter when to check and what to do if the leaf never appears (`BM-19`, `DP-*`) |
| `RE-08`  | **Absence of the code from its named sealed batch after that window's scheduled time is a first-class outcome with its own reason code and dispute path**, never a generic "not found" (`FM-16C-20`) |
| `RE-17`  | **The receipt names a bounded obligation, not an open-ended one.** `sealed_batch_reference` lets the voter know exactly when to check and exactly what should have happened (`PA-10`, `PA-12`) |
| `RE-18`  | **Before closure the receipt reveals nothing about occupancy.** It carries no leaf index, no position among real ballots, no submission order and no exact acceptance timestamp (`TC-40`) |
| `RE-19`  | **After closure the voter can check the opened ballot artefact against the commitment their receipt already named**, closing the loop from acceptance to published record without any privileged lookup |

---

## 4. Format and accessibility

| ID       | Rule                                                                                                          |
| -------- | ----------------------------------------------------------------------------------------------------------------- |
| `RE-09`  | The confirmation code is presented in a **human-readable, transcribable form** — grouped characters, an unambiguous alphabet excluding easily confused glyphs, and an audio-readable rendering (`XA-*`) |
| `RE-10`  | **A QR or machine-readable encoding is optional and never the only form.** Every receipt has a complete human-readable equivalent |
| `RE-11`  | Where a QR is offered it contains **only** the confirmation code and the verification URL — no ballot content, no credential, no identity — and its contents are displayed in text beside it so substitution is detectable |
| `RE-12`  | The receipt is available **printable and non-printable**, and the interface never requires printing, downloading, screenshotting or camera use |
| `RE-13`  | **No verification method may require a camera**, and a keyboard-entry path to the same lookup always exists |

---

## 5. What the receipt makes possible for a coercer

Stated here rather than in a footnote, because it is the receipt's real
cost.

```text
A receipt PROVES PARTICIPATION.
A coercer who demands to see a receipt learns that the person voted.
```

| ID       | Rule                                                                                                          |
| -------- | ----------------------------------------------------------------------------------------------------------------- |
| `RE-14`  | **This is accepted, recorded, and not solved by this design.** Forced abstention and proof-of-participation coercion are outside what a receipt can defend against (`T-P16A-30`) |
| `RE-15`  | The receipt is therefore **minimal**: it proves publication and nothing more, and it is designed so that showing it to a coercer transfers no information about the choice |
| `RE-16`  | The interface **never encourages sharing, exporting, emailing or posting a receipt**, and never frames it as evidence of anything |

`PACK-16C-COERCION-AND-RECEIPT-BOUNDARY.md` carries the full treatment and
the permitted/prohibited claims registries.

---

## 6. What this document does not decide

```text
Receipt encoding format            → OD-P16C-05, PACK-16D
QR policy details                   → OD-P16C-06
German receipt text                 → PACK-15 content-catalogue lineage
Retention of receipts by voters     → not EPD²'s to decide
```

**SPECIFIED. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY. NOT LEGALLY
ACTIVATED.**
