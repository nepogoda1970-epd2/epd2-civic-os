# PACK-16C — Accessibility Requirements

**Round:** PACK-16C — Casting, Receipt, Verification Client, Bulletin Board and Election Record. **Specification and ADR only. No code. No cryptographic implementation. Not implemented. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-101`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 0. Why this is a cryptography document

```text
A verification step a person cannot perform is a verification step
that does not exist for them.

Accessibility here is not a compliance layer over a finished design.
It decides whether the guarantees are real for the whole electorate
or only for the part of it that can use the interface.
```

| ID      | Rule                                                                                                                                                                                                                                         |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `XA-01` | **Every guarantee this pack specifies must be exercisable by every eligible voter.** Where it is not, the gap is named in §6 and is an activation consideration, not a backlog item                                                          |
| `XA-02` | **No accessibility accommodation may weaken ballot secrecy, and no secrecy mechanism may be allowed to make the system unusable.** Where the two genuinely conflict, the conflict is stated and the alternative channel is offered (`CB-07`) |

---

## 1. Baseline

| ID      | Rule                                                                                                                                                                                                                                                  |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `XA-03` | **BITV 2.0 / EN 301 549 / WCAG 2.1 AA is the floor for every participant-facing surface**, including the casting flow, the review screen, the challenge screens, the receipt, the Verification Client and the published record's human-readable views |
| `XA-04` | **The Verification Client is held to the same standard as the casting client.** A verification path that only sighted, mouse-using, technically confident people can follow makes individual verifiability a privilege                                |
| `XA-05` | **Accessibility conformance is tested with assistive technology and with disabled users**, not asserted from an automated audit alone                                                                                                                 |

---

## 2. Requirements by barrier

### 2.1 Vision

| ID      | Requirement                                                                                                                          |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| `XA-06` | **The full flow is operable with a screen reader**, including the review screen, the cast/challenge choice and the challenge result  |
| `XA-07` | **The confirmation code has an audio-readable rendering** with an unambiguous spoken alphabet, and can be repeated at will (`RE-09`) |
| `XA-08` | **No step depends on colour alone**, including the challenge result and any accepted/rejected indication                             |
| `XA-09` | **No step depends on a camera or a QR scan** (`RE-13`); a keyboard-entry path to the same lookup always exists                       |
| `XA-10` | **Text scales to at least 200 % without loss of function**, and the review screen does not truncate selections at large sizes        |

### 2.2 Motor

| ID      | Requirement                                                                                                                                                  |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `XA-11` | **The whole flow is keyboard-operable**, with a visible focus order that follows the logical order of the ballot                                             |
| `XA-12` | **No step has a time limit that cannot be extended**, subject only to the election window itself — and the window's end is announced with sufficient warning |
| `XA-13` | **No step requires a gesture, drag, precise pointing or double-action** that a switch or single-pointer user cannot perform                                  |

### 2.3 Cognition and literacy

| ID      | Requirement                                                                                                                                                                                                                                                                                  |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `XA-14` | **Plain-language German is the primary register** for every participant-facing string, with the governed catalogue owning the wording (PACK-15 lineage)                                                                                                                                      |
| `XA-15` | **The irreversible step is explained before it is offered**, in plain language, and the explanation does not depend on understanding cryptography (`CF-*` step 13)                                                                                                                           |
| `XA-16` | **The cast / local-check / public-audit-challenge choice is presented as three separately named decisions with understandable outcomes**, never as a technical option, and never with checking framed as an advanced feature. A single ambiguous "Challenge" control is prohibited (`CH-50`) |
| `XA-33` | **The one-per-capability limit on the public audit challenge is stated before the voter takes it, in plain language, and never as an error afterwards** (`CH-51`, `RN-16C-30`)                                                                                                               |
| `XA-34` | **A capacity-pause message is plain-language and carries no figures** (`TC-81`), because a message a voter cannot act on must at least be one they can understand                                                                                                                            |
| `XA-17` | **Nothing in the flow requires the voter to understand encryption, proofs, hashes or thresholds** in order to vote correctly and safely                                                                                                                                                      |
| `XA-18` | **Error messages are governed text explaining what happened and what to do** — never a reason code alone, never a raw error (`VP-12`)                                                                                                                                                        |

### 2.4 Hearing

| ID      | Requirement                                                                         |
| ------- | ----------------------------------------------------------------------------------- |
| `XA-19` | **No step depends on audio alone**, and every audio rendering has a text equivalent |

### 2.5 Device and connectivity

| ID      | Requirement                                                                                                                                                                                                             |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `XA-20` | **The flow works on modest hardware and slow connections.** Proof generation is the heaviest step; where a device is too slow, the client says so honestly before the voter begins rather than failing partway (`CF-*`) |
| `XA-21` | **Verification works on a second device and offline** (`VC-*`, `IV-*`), because requiring the voting device to verify itself is both a security weakness and an accessibility barrier                                   |
| `XA-22` | **No step requires installing an application**, and no step requires a specific operating system, browser vendor or app store                                                                                           |

---

## 3. Assistance

| ID      | Rule                                                                                                                                                                                  |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `XA-23` | **Assisted voting is permitted under PACK-15's assistance boundary, unchanged.** The choice remains the voter's; the assistant may operate the interface and may not decide (`CH-28`) |
| `XA-24` | **Assistance is recorded as a fact of the session where the governing rules require it, and never in a way that links an assistant to a ballot**                                      |
| `XA-25` | **An assisted session is a coercion risk that this design does not solve** in the remote setting, and the alternative channel is offered wherever that risk is material (`CB-07`)     |

---

## 4. Accessibility of the public record

Often forgotten, and load-bearing for public trust.

| ID      | Rule                                                                                                                                                                                                                                  |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `XA-26` | **The record's human-readable views meet the same standard** as the participant surfaces                                                                                                                                              |
| `XA-27` | **The record is obtainable without JavaScript, without an account and without a modern browser** — plain files over plain HTTP(S), because a record only reachable through a rich application is not universally accessible (`ER-13`) |
| `XA-28` | **The "what you cannot check" statement is published in plain language** alongside the technical form (`ER-18`)                                                                                                                       |

---

## 5. Testing

| ID      | Rule                                                                                                                                                                                      |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `XA-29` | **Accessibility acceptance is a gate on activation of a context, not a phase of PACK-16D.** A context whose flow has not been tested with assistive technology is not activated           |
| `XA-30` | **Test evidence is published**: what was tested, with what technology, by whom, and what failed                                                                                           |
| `XA-31` | **Known unresolved barriers are published before the election opens**, so that a voter who will hit one can choose the alternative channel in advance rather than discovering it mid-flow |

---

## 6. Known tensions, stated rather than resolved

| Tension                                              | Why it is real                                                                                                       | What is done                                                                                                                                                                                                                                             |
| ---------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Challenge complexity vs. cognitive accessibility** | Cast-or-challenge is genuinely hard to explain, and **three named actions are harder to explain than two** (`CH-50`) | Plain-language framing (`XA-16`), explicit "this was not counted" result (`CH-29`), **unlimited local checks**, an explicit "available once" statement **before** the public audit challenge (`CH-51`), and the cast entitlement is never lost (`CF-26`) |
| **Second-device verification vs. device access**     | Verification on a second device is the stronger design and assumes a second device exists                            | Same-device verification is permitted with its limitation published (`VC-*`); neither is required to vote                                                                                                                                                |
| **Code transcription vs. motor and vision barriers** | A code long enough to be secure is long enough to be hard to transcribe                                              | Grouped characters, unambiguous alphabet, audio rendering, machine-readable option that is never the only form (`RE-09`…`RE-11`)                                                                                                                         |
| **Assistance vs. secrecy**                           | An assistant sees the choice                                                                                         | PACK-15 boundary; alternative channel where coercion risk is material (`XA-25`)                                                                                                                                                                          |
| **Proof generation vs. modest devices**              | The cryptography has a real cost on old hardware                                                                     | Honest pre-flight check (`XA-20`); the alternative channel where it fails                                                                                                                                                                                |
| **Accessibility vs. anti-coercion**                  | Every accommodation that makes the flow easier to observe also makes it easier to coerce                             | Stated, not resolved; the in-person channel remains the coercion answer (`CB-07`)                                                                                                                                                                        |

| ID      | Rule                                                                                                                                                                      |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `XA-32` | **None of these six is claimed as solved.** Each is a published limitation of the electronic channel, and each is a reason the electronic channel is not the only channel |

---

## 7. What this document does not decide

```text
Concrete German interface texts             → PACK-15 content-catalogue lineage
Interface implementation                     → PACK-16D
Assistive-technology test plan                → PACK-16D, XA-29 gate
Minimum device baseline                       → PACK-16D
Alternative-channel design                    → OD-P16A-09, GOVERNANCE
```

**SPECIFIED. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY. NOT LEGALLY
ACTIVATED.**
