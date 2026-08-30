# PACK-16A — Accessibility Requirements

**Round:** PACK-16A — Verifiable Voting Protocol and Ballot Model Selection. **Specification and ADR only. No code. Not implemented. Not an implementation candidate. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-099`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

`FIR-INV-012` — accessibility is a Definition of Done, not a later pass.
`FIR-INCLUSION-001` — assisted and alternative channels.

**Accessibility is not delegated wholesale to FRONT-PACK.** This document
records the constraints that are **protocol-level** — properties of the
selected ballot model that determine what any interface can possibly
achieve — and hands the interface work onward with those constraints
attached.

---

## 1. Why some of this is protocol-level

Three properties of the selected model create accessibility obligations
that no frontend can discharge alone:

1. **Challenge/spoil is the only cast-as-intended mechanism.** If a voter
   cannot understand or perform a challenge, they have no protection
   against a dishonest client. That is a **protocol-level** exclusion, not
   a usability defect.
2. **Verification is voluntary and lightly used** — 9.9 % at best in the
   most mature deployment `[E-29]`. Any friction lands hardest on the
   voters who already face the most.
3. **The German standard is lay comprehensibility**, not availability of
   verification: _"zuverlässig und ohne besondere Sachkenntnis"_ `[E-41]`,
   and its party-law restatement — the objection that with electronic
   voting _"ohne Kenntnis und Verständnis des verwandten Algorithmus die
   konkrete Abstimmungssituation nicht nachvollzogen werden kann"_ `[E-55]`.

**Comprehensibility is therefore an architectural requirement in this
project, not a content-design preference.** Council of Europe Standard 1
says the same thing from the other direction: _"The voter interface of an
e-voting system shall be easy to understand and use by all voters"_
`[E-56]`.

---

## 2. General requirements

| ID      | Requirement                                                                                                                                                            |
| ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `AX-01` | **Keyboard-only operation** for the entire flow: selection, challenge, cast, verification. No step requires a pointer                                                  |
| `AX-02` | **Screen-reader support** with a meaningful reading order and announced state changes, including the cast/challenge decision point                                     |
| `AX-03` | **Zoom and reflow** to at least 400 % without loss of function or content                                                                                              |
| `AX-04` | **Low-vision support**: contrast, focus visibility, no reliance on fine detail                                                                                         |
| `AX-05` | **Cognitive accessibility**: one decision per screen, no time pressure, no countdown on the cast/challenge choice                                                      |
| `AX-06` | **Plain-language verification** — §4                                                                                                                                   |
| `AX-07` | **No colour-only status.** Accepted, spoiled, published, refused each carry text and shape                                                                             |
| `AX-08` | **Error recovery**: every refusal states what happened, what to do next, and what it does **not** mean                                                                 |
| `AX-09` | **Multilingual support**, with the governed German texts authoritative (PACK-15 `PACK-15-CONTENT-CATALOGUE-DE.md` lineage)                                             |
| `AX-10` | **Assisted voting** without helper custody and without the helper seeing the choice — §6                                                                               |
| `AX-11` | **Independent verification** possible without a second device — §5.2                                                                                                   |
| `AX-12` | **A fallback procedure** exists and is published before the vote opens — §7                                                                                            |
| `AX-13` | **No accessibility feature reduces a security property.** Where the two genuinely conflict, the conflict is a named limitation with an owner, never a silent downgrade |

`AX-05`'s prohibition on countdowns is specific: PACK-15 §19.3 already
requires the credential-minting delay to present "a visible waiting state
and no countdown pressure", and the same applies to the cast/challenge
decision. A voter hurried at that point is a voter who does not challenge.

---

## 3. Protocol-level constraints on accessibility

| ID      | Constraint                                                                                                  | Consequence                                                                                                     |
| ------- | ----------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `AX-14` | Ballot preparation and encryption occur **in the client**                                                   | A very low-capability device may be unable to encrypt; `AX-12`'s fallback must exist                            |
| `AX-15` | Credential material never persists outside WS-03 (PACK-15 §13.3)                                            | The flow is **single-visit**; a voter who cannot complete one visit needs the fallback                          |
| `AX-16` | A challenged ballot is discarded (`BM-09`)                                                                  | The interface must make "you will start again" unmistakable **before** the choice, not after                    |
| `AX-17` | The confirmation code must be **transferable to the voter's own record** but must never be operator-visible | It may be shown and copied by the voter; it may not appear in a screen share, a support tool or a log           |
| `AX-18` | Verification requires no account (`BB-36`)                                                                  | No registration barrier; but also no "resend my code" path, because none can exist                              |
| `AX-19` | No individual ballot is decrypted                                                                           | "Show me what I voted for" cannot be offered as an accessibility aid, and must be explained rather than implied |
| `AX-20` | Proof generation may take noticeable time on modest hardware                                                | Progress must be announced accessibly, with no timeout that fails the voter rather than the device              |

`AX-19` matters more than it looks. A voter with memory difficulties may
reasonably ask the system to remind them how they voted. **It cannot, and
the reason must be explained in the interface** rather than presented as a
missing feature — otherwise the honest answer arrives as an apparent
failure.

---

## 4. Plain-language verification

The most consequential requirement in this document.

| ID      | Requirement                                                                                                                                                      |
| ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `AX-21` | Every voter-facing explanation of casting, challenging and verifying must be comprehensible **without cryptographic vocabulary**                                 |
| `AX-22` | The words _encryption_, _ciphertext_, _zero-knowledge_, _homomorphic_, _trustee share_ and _proof_ may appear only in optional detail, never in the primary path |
| `AX-23` | The primary explanation of the confirmation code is: _"a reference that lets you find your ballot on the public list, and that does not show how you voted"_     |
| `AX-24` | The primary explanation of challenge is: _"check that the app locked in what you actually chose — the ballot you check is thrown away, and you vote again"_      |
| `AX-25` | The limits are stated in the same register as the capabilities, in the same place, at the same prominence — not in a linked policy                               |
| `AX-26` | Explanations are tested with people who are **not** technical, and the test result is evidence for the accessibility assessment (gate item 5)                    |
| `AX-27` | No explanation asserts a prohibited claim (`PACK-16A-COERCION-AND-RECEIPT-BOUNDARY.md` §8)                                                                       |

### 4.1 The BVerfG connection, stated as a design constraint

The German standard requires the citizen to be able to scrutinise the key
steps **reliably and without specialist knowledge** `[E-41]`. A verification
act whose meaning is "the mathematics checks out" does not obviously meet
it. A verification act whose meaning is "my reference is on the public
list, and the list adds up" is materially closer.

**This is why Selene is recorded as `REQUIRES FURTHER RESEARCH` rather than
dismissed** `[E-38]`: tracker-based verifiability was designed for exactly
this problem. `OD-P16A-10` carries the question of whether a
lay-comprehensible verifiability presentation can be layered onto
`EPD2-HOM-1` without creating a transferable receipt — which is the whole
difficulty, since the property that makes a tracker comprehensible is the
property that makes it demandable.

---

## 5. Verification without barriers

### 5.1 Requirements

| ID      | Requirement                                                                                                                            |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| `AX-28` | Verification requires **no account, no app install, no QR scan and no second device**                                                  |
| `AX-29` | The verification page is operable by keyboard and screen reader, at 400 % zoom                                                         |
| `AX-30` | The result is stated in words — "your reference is on the list" / "your reference is not on the list" — with no colour-only signal     |
| `AX-31` | The absent-code path is a **first-class, calm outcome** with a clear next step, not an error state (`BB-26`)                           |
| `AX-32` | The confirmation code is presented in a form a person can write down: grouped characters, an unambiguous alphabet, read-aloud friendly |

### 5.2 The second-device question

Estonia requires a separate device for verification. Estonia's own
individual-verifiability mechanism was nonetheless defeated by a
voting-client attack that did **not** require compromising the verification
app `[E-28a]`.

**Decision: a second device is recommended and not required** (`AX-11`).
Requiring one excludes voters who have only one device, which is a
disenfranchisement cost paid for a protection the published evidence shows
to be partial. The interface states the trade honestly: verifying on the
same device is better than not verifying, and verifying on a different
device is better still.

---

## 6. Assisted voting

PACK-15 §13.5 governs assisted **credential delivery** and is unchanged.
This section extends it to the casting act.

| ID      | Requirement                                                                                                                               |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `AX-33` | The accessible path is an **independent** path, not a supervised one. Where it cannot be, that is a named limitation with an owner        |
| `AX-34` | A helper may bring the participant to the voting origin and no further                                                                    |
| `AX-35` | **No screen sharing, remote control or shadowing during the casting act.** Stated in the interface and in governed content                |
| `AX-36` | An assisted-action receipt records **that** assistance occurred, never the choice                                                         |
| `AX-37` | No operator, helper or support role ever sees the selection, the confirmation code or any client state                                    |
| `AX-38` | The interface offers a way to **leave without casting** at every step, unremarked, so that a coerced voter can abandon without signalling |

### 6.1 The assistant as coercer

The threat is `T-P16A-32`, and there is no technical control for it.

| Risk                                    | Treatment                                                                                                                                          |
| --------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| Assistant sees or controls the choice   | `AX-33` independent path; `AX-34` boundary; **and, where the risk is material, the correct answer is a different channel**, not a better interface |
| Screen-reader output overheard          | Headphone guidance; and the plain acknowledgement that audio output in a shared room is exposure                                                   |
| Shared device retains state             | Nothing persists (ADR-096, `CC-07`); the interface says so                                                                                         |
| Remote support session observes casting | `AX-35` prohibition; support tooling must be structurally unable to attach to the voting origin                                                    |
| Care-home and group settings            | ODIHR names this class explicitly `[E-40]`; **a governance question, not an interface one**                                                        |

**`AX-38` is the only control in this document that helps a coerced voter
directly**, and it is a small one: an exit that is always available and
never remarked upon means that abandoning does not itself signal
resistance.

---

## 7. Fallback

| ID      | Requirement                                                                                                                          |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| `AX-39` | Every context publishes its fallback **before** `voting_open`, in the manifest and in participant-facing content                     |
| `AX-40` | The fallback is a **different channel** — in person, on paper, at an assembly — not a different screen                               |
| `AX-41` | Using the fallback must not require disclosing why                                                                                   |
| `AX-42` | Where no fallback exists, the context **may not be activated** for a population that cannot use the electronic channel               |
| `AX-43` | The fallback's reconciliation with the electronic channel is a **scope-level** governance act, never a per-person one (`OD-P16A-09`) |

`AX-43` is the constraint that makes fallback hard, and it is the same
constraint that ruled out an in-person override in
`PACK-16A-REVOTING-AND-BALLOT-LIFECYCLE.md` §5.3: reconciling two channels
per person requires knowing who used which. Until `OD-P16A-09` is answered,
a fallback operates as a **separate context or a separate scope**, with its
own manifest and its own result, combined at the governance level.

Council of Europe Standard 3 supports the shape of this: _"Unless channels
of remote e-voting are universally accessible, they shall be only an
additional and optional means of voting"_ `[E-56]`. **Electronic voting is
an additional channel in this architecture, never the only one.**

---

## 8. Conflicts between accessibility and security, named

`AX-13` forbids silent downgrades. The known conflicts:

| Conflict                                                        | Resolution                                                                                         | Owner            |
| --------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- | ---------------- |
| Single-visit flow vs. voters who cannot complete a visit        | **Fallback channel** (`AX-12`); the isolation is not waived                                        | GOVERNANCE       |
| No credential display vs. voters who need a written token       | **No exception.** PACK-15 §13.3 stands; the fallback channel is the answer                         | PACK-15, binding |
| Second-device verification vs. single-device voters             | Recommended, not required (`AX-11`, §5.2)                                                          | PACK-16C         |
| Assistance vs. ballot secrecy                                   | Independent path; where impossible, a **named limitation with an owner** (`AX-33`)                 | PACK-16C, FRONT  |
| Plain language vs. precision                                    | Plain language in the primary path, precision in optional detail; **never a false simplification** | PACK-16C         |
| Client encryption cost vs. low-capability devices               | Progress announcement, no failing timeout, and the fallback (`AX-20`, `AX-12`)                     | PACK-16C         |
| Longer window for accessibility vs. coercion exposure over time | A governance trade per context, recorded, not defaulted                                            | GOVERNANCE       |

---

## 9. What PACK-16A does not decide

```text
Page structure, component design and interaction detail   → FRONT-PACK
Governed German content for the ballot domain             → FRONT-PACK, PACK-16C
The accessibility conformance target and test suite       → FRONT-PACK, FIR-INV-012
The fallback channel's operational design                 → GOVERNANCE, PACK-16C
```

PACK-16A produces the **protocol-side constraints** and none of the
interface artefacts. `FIR-UX-003` … `FIR-UX-011` apply in full and are
untouched; the complete first-page-to-final-page structure is defined
during the relevant FRONT-PACK stage, as PACK-15 §25 requires.

**SPECIFIED. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY. NOT LEGALLY
ACTIVATED.**
