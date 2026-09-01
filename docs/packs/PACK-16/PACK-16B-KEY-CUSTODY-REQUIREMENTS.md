# PACK-16B — Key Custody Requirements

**Round:** PACK-16B — Cryptographic Parameters, Key Ceremony and Trustee Architecture. **Specification and ADR only. No code. No cryptographic code. Not implemented. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-100`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

**No product and no vendor is selected here.** Permitted _classes_ are
selected; the choice within a class is PACK-16D's, against the evaluation
criteria.

---

## 1. What is being held

| Material                                     | Exists from | Until                   | Held by                                |
| -------------------------------------------- | ----------- | ----------------------- | -------------------------------------- |
| Polynomial coefficients `a_{i,j}`, `â_{i,j}` | phase 8     | **ceremony completion** | the guardian, then destroyed (`GL-16`) |
| Initial secrets `s_i`, `ŝ_i`                 | phase 8     | **ceremony completion** | the guardian, then destroyed (`GL-16`) |
| Communication secret `ζ_i`                   | phase 8     | ceremony completion     | the guardian, then destroyed           |
| Schnorr and encryption nonces                | phase 8/10  | immediately after use   | the guardian, then destroyed           |
| **Share `z_i`, `ẑ_i`**                       | phase 11    | **retirement**          | **the guardian, alone**                |

**Only `z_i` and `ẑ_i` survive the ceremony.** The specification permits
discarding the rest `[F-13]`; `GL-16` requires it. That materially shrinks
what custody has to protect — one 32-byte value per key set, per guardian.

---

## 2. Permitted custody classes

| Class                                     | Permitted?                                       | For                                     | Conditions                                                                     |
| ----------------------------------------- | ------------------------------------------------ | --------------------------------------- | ------------------------------------------------------------------------------ |
| **Software-only, general-purpose device** | **No**                                           | —                                       | A guardian share on a laptop that also reads email is not custody              |
| **Software-only, dedicated device**       | **Permitted**                                    | Default profile                         | Dedicated, non-virtualised, minimal software, offline except during ceremonies |
| **Hardware-backed dedicated device**      | **Permitted, preferred**                         | Default and high-assurance              | Key material non-exportable from the hardware element                          |
| **Smart card**                            | **Permitted, preferred**                         | Default and high-assurance              | One card per guardian, in that guardian's sole possession                      |
| **HSM**                                   | **Permitted with conditions**                    | High-assurance, institutional guardians | **One guardian per HSM** (`GI-17`); separate administration; §4                |
| **Air-gapped ceremony device**            | **Permitted, preferred for the ceremony itself** | Both profiles                           | Material generated and retained on it; §3                                      |
| **General-purpose cloud KMS**             | **No**                                           | —                                       | §4.1                                                                           |
| **Consumer hardware wallet**              | **No**                                           | —                                       | §4.2                                                                           |
| **Paper or mnemonic backup**              | **No**                                           | —                                       | Transcribable, photographable, and it makes the share a bearer value           |

| ID      | Rule                                                                                                          |
| ------- | ------------------------------------------------------------------------------------------------------------- |
| `KU-01` | Every guardian's custody class is **declared in due diligence** (`GL-06`) and **published** in the transcript |
| `KU-02` | Two guardians may use different classes; the set is assessed as a whole for independence (`GI-01`)            |
| `KU-03` | The **weakest** custody in the set bounds the profile's assurance, and the assessment says so explicitly      |

---

## 3. Requirements common to every class

| ID      | Requirement                                                                                                                                      |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| `KU-04` | **Exportability:** the share is non-exportable in cleartext. Where a class cannot enforce this technically, the limitation is published          |
| `KU-05` | **Dedication:** the device serves the guardian function and nothing else                                                                         |
| `KU-06` | **No virtualisation, no snapshots** (`RN-12`, `KY-05`) — a snapshot replays generator state and duplicates nonces                                |
| `KU-07` | **Sole possession:** one natural person holds it. Not a team, not a role account, not a shared safe                                              |
| `KU-08` | **No shared administration:** no operator, provider or administrator has access to two guardians' devices (`GI-12`)                              |
| `KU-09` | **No shared imaging or provisioning process** across guardians (test 14)                                                                         |
| `KU-10` | **Attestation** of the device and the ceremony build where available; where not, witnessed provisioning from published media, recorded (`KY-03`) |
| `KU-11` | **Firmware trust** is declared: what is trusted, by whom it is signed, and what happens if that trust is withdrawn                               |
| `KU-12` | **Supply-chain provenance** is recorded: how the device was obtained and by whom                                                                 |
| `KU-13` | **Side-channel exposure** is bounded by dedication and offline operation; constant-time requirements pass to PACK-16D                            |
| `KU-14` | **No vendor lock-in that prevents independent verification** — a class whose output only its own vendor can check is refused                     |
| `KU-15` | Material is **destroyed at retirement**, with an attestation (`GL-17`)                                                                           |
| `KU-16` | Custody is **per context** — a device holding shares for two contexts violates `GQ-09`'s intent and is refused                                   |

---

## 4. An HSM does not convert one administrator into a threshold

The rule is stated in `PACK-16B-GUARDIAN-INDEPENDENCE-MATRIX.md` §4 and is
restated here because this is where it will be tested.

```text
If one operator, one cluster, one provider or one policy engine can
produce k decryption shares, the architecture FAILS — regardless of
what the HSM's authorisation policy says.
```

| ID      | Rule                                                                                                                                                             |
| ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `KU-17` | An HSM holds **exactly one guardian's** material (`GI-17`)                                                                                                       |
| `KU-18` | An HSM policy requiring _m_ operator cards is **not** a threshold in the sense of `KC-01` — it is a control inside one device under one administration (`GI-15`) |
| `KU-19` | A design in which any single party can assemble a quorum is **rejected at design review**, not mitigated                                                         |
| `KU-20` | HSM administration is by the **guardian's own organisation**, not by EPD², not by a shared provider                                                              |

### 4.1 Why a general-purpose cloud KMS is not permitted

A managed key service is administered by its provider and by whoever holds
the account. Two guardians in one tenant are one guardian (`GI-04`, hard).
Two guardians in two tenants of the **same provider** share a provider,
which is test 3 (hard) and, more importantly, is exactly the row of the
collusion matrix that produces a quorum with no guardian's participation.

**Not permitted**, for the default and high-assurance profiles alike.

### 4.2 Why a consumer hardware wallet is not sufficient

It solves key extraction and not the rest: no attestation EPD² can verify,
firmware trust resting on a consumer vendor, a recovery-phrase model that
makes the share transcribable, and an ecosystem whose threat model is theft
of a bearer asset rather than integrity of a public process. **Hardware
custody is not the same as a hardware wallet**, and `KU-04` plus `KU-10`
are where the difference lands.

---

## 5. Remote ceremony and custody

The ceremony decision is **controlled hybrid or in-person**
(`PACK-16B-REMOTE-CEREMONY-ASSESSMENT.md`). Custody consequences:

| ID      | Rule                                                                                                                                  |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| `KU-21` | The device is **physically present with its guardian** at every ceremony session                                                      |
| `KU-22` | No remote-desktop, screen-share or remote-administration path exists to a ceremony device, at any time                                |
| `KU-23` | Transport of a device between sessions is the guardian's own; it is not couriered, shipped or held by an operator                     |
| `KU-24` | Where an institutional guardian's device cannot leave its premises, the ceremony comes to it — a controlled hybrid location (`RC-06`) |

---

## 6. What custody does not protect against

| Not protected                       | Consequence                                                                                                      |
| ----------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| A guardian who chooses to collude   | Custody protects the share from others, not from its holder                                                      |
| `k` guardians colluding             | Undetectable; prevention is organisational (`GI-09`…`GI-12`)                                                     |
| A compromised firmware supply chain | Declared (`KU-11`), not eliminated                                                                               |
| Coercion of a guardian              | Outside every technical control; an incident matter                                                              |
| Loss of the device without backup   | A permanent absence — survivable within `n − k`, and the reason per-guardian backup is permitted (backup doc §3) |

**The honest summary:** custody makes a share hard to take and does nothing
about a share being given. That is why `k ≥ 3`, why `GI-11` forces an
external participant into any collusion, and why guardian identity is
public.

---

## 7. What this document does not decide

```text
The device products and vendors           → PACK-16D
Procurement and funding                    → GOVERNANCE
The attestation technology                 → PACK-16D
Physical security of storage between ceremonies → GOVERNANCE, PACK-17
```

**SPECIFIED. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY. NOT LEGALLY
ACTIVATED.**
