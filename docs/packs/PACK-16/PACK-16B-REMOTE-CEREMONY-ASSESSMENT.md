# PACK-16B — Remote Ceremony Assessment

**Round:** PACK-16B — Cryptographic Parameters, Key Ceremony and Trustee Architecture. **Specification and ADR only. No code. No cryptographic code. Not implemented. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-100`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 1. The decision

```text
INITIAL EPD2-HOM-1 PROFILE

  FULLY IN-PERSON CEREMONY          permitted
  CONTROLLED HYBRID CEREMONY        permitted  ← the expected form
  FULLY REMOTE CEREMONY             PROHIBITED
```

**Fully remote is prohibited because the evidence to permit it does not
exist**, not because remote ceremonies are impossible. §5 states exactly
what would have to change.

---

## 2. Definitions, because "hybrid" is used loosely

| Form                     | Meaning                                                                                                                    |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------ |
| **Fully in-person**      | All guardians, the Coordinator and the Auditor physically present in one supervised room for every ceremony session         |
| **Controlled hybrid**    | Guardians physically present at **two or more supervised locations**, each with an independent observer present, connected over an authenticated channel. **Every guardian is physically with their own device and with at least one independent witness** |
| **Fully remote**         | Guardians participate from locations of their own choosing, unobserved, over the public internet                            |

**Controlled hybrid is not "remote with a webcam".** Its defining property
is that **no guardian is ever alone with their device during a ceremony
session**, and that each location is supervised by someone who is not a
guardian.

---

## 3. The assessment

| Criterion                        | Fully in-person                                     | **Controlled hybrid**                                        | Fully remote                                                        |
| -------------------------------- | ----------------------------------------------------- | -------------------------------------------------------------- | --------------------------------------------------------------------- |
| **Guardian authentication**      | Strongest — recognised in person                     | **Strong** — in person at each location, by the local observer | Weak — credential-based only; a credential can be surrendered        |
| **Device trust**                 | Devices inspected together                            | **Devices inspected locally by an observer**                   | **Unverifiable.** The claimed device may not be the device            |
| **Secure share transport**       | The construction encrypts shares regardless          | Same                                                           | Same — this criterion does not distinguish                            |
| **Independent observation**      | Direct                                               | **Per location**                                               | **Absent** — the central weakness                                     |
| **Recording**                    | Controllable; screens excluded from frame            | Controllable per location                                      | Uncontrollable — anything on any screen may be recorded elsewhere     |
| **Coercion**                     | Very low — a coercer would have to be in the room     | **Low** — an observer is present                               | **Unmitigated.** A guardian may be coerced off-camera, and this is the same limit `[E-46]` identifies for voters |
| **Malware**                      | Dedicated devices, inspected                         | Dedicated devices, inspected locally                           | Dedicated devices, **uninspected**                                    |
| **Network compromise**           | Local or air-gapped                                  | Authenticated inter-site channel, small and known               | Public internet, adversary-reachable                                  |
| **Transcript consistency**       | One view, checked together                           | Per-site views compared, then mirrored                          | Split-view is easiest here — and split view is `T-P16A-14`            |
| **Accessibility**                | Travel burden; venue must be accessible               | **Best** — a guardian attends the nearest accessible site       | Best on travel, worst on assisted-participation control (`KY-39`)     |
| **Logistics**                    | Hardest — one place, one time                        | **Workable** — the reason it is the expected form              | Easiest                                                                |
| **Legal / governance acceptance**| Highest                                              | High                                                            | **Untested**, and the German posture on unobserved electronic acts is not favourable |
| **Evidence base**                | Long-established practice                            | Established practice                                            | **No peer-reviewed analysis of this specification's key ceremony was located by this round's survey** `[F-31]` |

---

## 4. Why fully remote is prohibited

Four reasons, of which the fourth is decisive.

**One — device trust is unverifiable.** `KU-05` and `KU-10` require a
dedicated, attested device. Remotely, EPD² can verify an attestation
statement and cannot verify that the statement describes the machine in
front of the guardian.

**Two — the fault that most needs a witness is the one with no
cryptographic trace.** The complaint model attributes seven of eleven
grounds arithmetically. The remaining four — compromise, independence
violation, and the two directions of `share_inconsistent` — are assessed
from evidence, and remotely there is very little.

**Three — coercion of a guardian is unaddressed.** The same statement that
governs voters applies: *"if the coercer can monitor the voter throughout
the vote casting period, then resistance is futile"* `[E-46]`. A guardian
alone with a device is a guardian who can be accompanied by someone the
record never sees. In-person and controlled-hybrid forms **manufacture the
witness** that remote participation only assumes.

**Four — no evidence base was located.** **No peer-reviewed security
analysis specifically covering the selected ElectionGuard 2.1 key-ceremony
composition was located in the sources reviewed for PACK-16B** `[F-31]`, and
**this absence of evidence must not be read as proof that no such analysis
exists.** What follows from it is narrower and still sufficient: the
component this architecture's confidentiality depends on most is the
component for which this round could find the least independent scrutiny.
Permitting the *weakest* operational form of that component, on evidence
EPD² has not been able to locate, would be a choice made by preference.

**The honest summary:** remote ceremony is prohibited because EPD² cannot
currently say what it would be relying on. If such an analysis is later
produced or located, §5 states what would change.

---

## 5. What would change the decision

```text
1. A peer-reviewed security analysis of this specification's key ceremony,
   addressing remote participation.
2. A device-attestation arrangement a third party can verify remotely and
   that EPD² does not itself operate.
3. An observation model that survives an adversary controlling the
   guardian's location — which, on current evidence, means a witness.
4. Operational experience: at least two completed controlled-hybrid
   ceremonies with published transcripts and Auditor verdicts.
```

`OD-P16B-05` carries the question. **Until then the answer is no**, and it
is written down rather than left for an operator to decide when scheduling
becomes difficult.

---

## 6. Mandatory controls for the controlled hybrid form

| ID       | Control                                                                                                              |
| -------- | ------------------------------------------------------------------------------------------------------------------------ |
| `RC-01`  | **Every guardian is physically present with their own device.** No guardian operates a device remotely                |
| `RC-02`  | **Every location has at least one independent observer** who is not a guardian, not an operator and not a candidate    |
| `RC-03`  | **No guardian is alone with their device during a session.** This is the defining control                            |
| `RC-04`  | The inter-site channel is **authenticated and integrity-protected**, and its endpoints are published                  |
| `RC-05`  | **The channel is not trusted for confidentiality of secret material** — shares are encrypted by the construction regardless, and no secret is transported by the channel in any other form |
| `RC-06`  | Where an institutional guardian's device cannot leave its premises, that becomes **a location**, with its own observer (`KU-24`) |
| `RC-07`  | Each location produces its **own view of the transcript**, and the views are compared before any checkpoint is signed  |
| `RC-08`  | **A divergence between location views halts the ceremony** and is published in full (`CT-20`)                        |
| `RC-09`  | **No screen sharing, no remote control, no remote administration** of any ceremony device, at any time (`KU-22`)      |
| `RC-10`  | Recording, where used, **excludes device screens** and is retained under the transcript's retention rules             |
| `RC-11`  | Observers are named in the transcript; their independence is declared and assessed as guardians' is (`GI-04`)          |
| `RC-12`  | The Coordinator is present at one location and **holds no secret material anywhere** (`RS-16B-03`)                    |
| `RC-13`  | The **Independent Auditor may attend any location unannounced**, and this right is published                          |
| `RC-14`  | Maximum **three locations** for the default profile — beyond that, per-site observation stops being verifiable in practice |

---

## 7. Accessibility consequences of this decision

Requiring physical presence has an accessibility cost, and pretending
otherwise would undo `KY-34`…`KY-43`.

| Cost                                                        | Treatment                                                                                       |
| ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| Travel burden on a guardian with limited mobility           | **Controlled hybrid exists mainly for this** — a guardian attends the nearest accessible location |
| A guardian unable to attend any location                    | They should not be nominated, and this is identified in due diligence (`GL-08`, `GL-09`) rather than discovered on the day |
| Venue accessibility                                         | A **selection criterion**, not an accommodation (`KY-35`)                                        |
| Assisted participation                                      | `KY-39`…`KY-41`: assistance never touches secret material, dual-control where it approaches it, and the assistant is named as an assistant |
| Interpretation                                              | Arranged in advance per `KY-36`, at each location that needs it                                  |

**A guardian set that cannot be assembled accessibly is a guardian set that
has not been assembled**, and `GQ-10` applies: the correct outcome may be
not to hold the vote electronically.

---

## 8. The decryption ceremony

Everything above applies to the **decryption** ceremony as well as the key
ceremony, with one addition:

| ID       | Rule                                                                                                          |
| -------- | ----------------------------------------------------------------------------------------------------------------- |
| `RC-15`  | The decryption ceremony is held under the same form as the key ceremony for that context, or a stricter one — never a looser one |
| `RC-16`  | Absence at the decryption ceremony is tolerated within `n − k` and is **published** (`KC-11`); it is not a reason to relax the ceremony form |

`RC-15` closes the obvious drift: a key ceremony held in person, followed
six weeks later by a decryption "over a call because everyone is busy",
would place the entire confidentiality boundary in the looser session.

**SPECIFIED. DECIDED. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY. NOT
LEGALLY ACTIVATED.**
