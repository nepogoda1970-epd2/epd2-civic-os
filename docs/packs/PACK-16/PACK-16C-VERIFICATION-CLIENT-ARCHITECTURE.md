# PACK-16C — Verification Client Architecture

**Round:** PACK-16C — Casting, Receipt, Verification Client, Bulletin Board and Election Record. **Specification and ADR only. No code. No cryptographic implementation. Not implemented. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-101`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 1. The decision

```text
A SEPARATE VERIFICATION CLIENT ON A SEPARATE ORIGIN,
holding no identity state, no credential state and no ballot state.

Plus, mandatory: an INDEPENDENT VERIFIER that is not a web page at all
(PACK-16C-INDEPENDENT-VERIFIER-REQUIREMENTS.md).
```

## 2. The options

| Option                               | Assessment                                                                  | Verdict                                        |
| ------------------------------------ | --------------------------------------------------------------------------- | ---------------------------------------------- |
| The Voting Client verifies           | Zero independence: a compromised client lies twice                          | **Rejected**                                   |
| Separate route, same origin          | Shares storage, cookies, service worker and compromise surface with casting | **Rejected**                                   |
| Separate application, same origin    | Same shared origin problem                                                  | **Rejected**                                   |
| **Separate origin, EPD²-operated**   | Independent of casting state; still EPD²-operated, so not sufficient alone  | **SELECTED as the convenience path** (`BB-14`) |
| Independent downloadable verifier    | Does not depend on EPD² at run time                                         | **SELECTED as the mandatory path**             |
| Third-party verifier implementations | The only route to universal verifiability                                   | **REQUIRED before binding use** (`BM-28`)      |

| ID      | Rule                                                                                                                                                              |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `VC-01` | **The Verification Client is a third origin** — not the casting origin, not the identity origin (`BB-14`, `FIR-INV-003`)                                          |
| `VC-02` | **No EPD²-operated verifier is sufficient for universal verifiability.** The separate origin is a convenience; the independent verifier is the guarantee (`IV-*`) |

## 3. What it holds and what it must not

| Property         | Rule                                                                                                              |
| ---------------- | ----------------------------------------------------------------------------------------------------------------- |
| **Origin**       | Own origin, own certificate, own build, published separately                                                      |
| **Storage**      | **None.** No cookie, no `localStorage`, no `sessionStorage`, no IndexedDB, no service-worker cache of results     |
| **Identity**     | **None.** No account, no login, no credential, no session (`BB-36`)                                               |
| **Ballot state** | **None.** It never sees a plaintext, a nonce, an envelope in preparation, or a capability                         |
| **Network**      | Manifest, election record, checkpoints, inclusion and consistency proofs — all public reads                       |
| **Analytics**    | **Prohibited.** No third-party script, no CDN without pinning, no telemetry, no session replay, no fingerprinting |
| **Offline**      | An offline mode over a downloaded record bundle is **required** (`VC-09`)                                         |

| ID      | Rule                                                                                                                                                                                                                                                                                                        |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `VC-03` | **The Verification Client requires no credential, no account and no agreement to terms** (`BB-36`)                                                                                                                                                                                                          |
| `VC-04` | **It stores nothing between visits.** A voter's lookup leaves no trace in the browser that a coercer could later demand                                                                                                                                                                                     |
| `VC-05` | **It is reproducibly built and its artefact digest is published**, so a voter can compare what they loaded against what was released                                                                                                                                                                        |
| `VC-06` | **It performs its own cryptographic checks locally** — checkpoint signatures, hash-chain linkage, inclusion proofs — and does not accept a server's assertion of validity                                                                                                                                   |
| `VC-07` | **Lookups are unauthenticated and rate-limited per confirmation code, not per person** (`BB-24`)                                                                                                                                                                                                            |
| `VC-08` | **A lookup returns presence-or-absence, the voter's own leaf opening, a Merkle inclusion path and the current signed checkpoint, and nothing else** — no leaf index, no neighbours' openings, no occupancy, no total, no timestamp finer than the context's granularity (`BB-23`, `BB-25`, `TC-36`…`TC-40`) |
| `VC-21` | **Before closure the client verifies a commitment inclusion proof, not a published ballot.** It recomputes the leaf from the opening it was given, walks the inclusion path to `commitment_root`, and checks that root against a signed checkpoint it validated itself (`VC-06`, `API-20`)                  |
| `VC-22` | **The client must not become an occupancy oracle.** It issues one lookup per confirmation code the voter holds, and offers no enumeration, no batch browsing and no "how many so far" view (`TC-38`, `TC-39`)                                                                                               |
| `VC-23` | **The client states which phase it verified** — `COMMITTED` before closure, `PUBLISHED_AFTER_CLOSURE` afterwards — and never presents a commitment check as proof that the ballot artefact is public (`RE-*`, `PA-*` §4)                                                                                    |
| `VC-24` | **After closure the client verifies the full chain**: the opened ballot artefact → its leaf opening → the batch root the voter already saw → the checkpoint. A voter who kept their receipt can close that loop themselves (`RE-19`)                                                                        |
| `VC-09` | **Offline verification over a downloaded record bundle is a required capability**, so that a voter can verify without contacting EPD² at all                                                                                                                                                                |

## 4. Same-device versus second-device

| Route                            | Trust assumption                       | Client-malware risk                             | Fake-interface risk | Accessibility                 | Privacy                                   | Usability            |
| -------------------------------- | -------------------------------------- | ----------------------------------------------- | ------------------- | ----------------------------- | ----------------------------------------- | -------------------- |
| **Same device, separate origin** | Device honest                          | **High** — one compromised device can fake both | Moderate            | Best                          | Best — no second device needed            | Best                 |
| **Second device**                | At least one device honest             | **Low**                                         | Moderate            | Needs a second device         | Reveals interest to that device's network | Moderate             |
| **Offline verifier**             | Downloaded artefact honest             | Low                                             | Low                 | Requires technical capability | Best                                      | Poor for most voters |
| **Third-party verifier**         | Third party honest **and** independent | Lowest                                          | Lowest              | Technical                     | Best                                      | Poor for most voters |

| ID      | Rule                                                                                                                                                                                                 |
| ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `VC-10` | **Same-device verification alone does not establish cast-as-intended**, and the interface says so. A compromised device can encrypt one thing and display another _and_ verify a comforting lie      |
| `VC-11` | **The recommended flow is: same-device convenience verification, plus an explicit offer of second-device or third-party verification**, with the difference between them explained in plain language |
| `VC-12` | **Second-device verification is never required**, because requiring it would exclude voters who have one device — and exclusion is a worse failure than a weaker check (`XA-*`)                      |
| `VC-13` | **The published record is the fallback for everyone**: any person, on any device, at any time, without EPD²'s cooperation                                                                            |

**The honest summary:** the convenient route is the weakest, the strong
routes are inconvenient, and this document refuses to describe the
convenient one as if it were strong.

## 5. Fake verifiers

| ID      | Rule                                                                                                                                       |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `VC-14` | **The canonical verification origin is published in the manifest and on the board**, before `voting_open`, and is not changed mid-election |
| `VC-15` | **The record is downloadable in full** (`BB-09`), so a suspicious voter can bypass every interface                                         |
| `VC-16` | **Verification instructions name the origin explicitly** and warn that a verifier reached from a link sent by someone else may be false    |
| `VC-17` | A fake verifier is **not preventable** by EPD², and this is stated rather than implied away (`T-P16A-28`)                                  |

## 6. What it shows

```text
PRESENT      "A ballot with this confirmation code is published,
              under checkpoint <id>."
ABSENT       "No ballot with this confirmation code is published
              under the current checkpoint." + the dispute path
PENDING      "Not yet published. Publication is due by <deadline>."
```

| ID      | Rule                                                                                                                                                                |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `VC-18` | **Absence is a first-class outcome with a reason code and a dispute path** (`BM-19`, `BB-26`), never a generic error and never styled as a user mistake             |
| `VC-19` | **The client never displays or infers the ballot's contents**, and has no capability to do so                                                                       |
| `VC-20` | **What cannot be checked is displayed beside what can** (`BB-37`) — specifically that presence on the board does not prove the device encrypted the intended choice |

## 7. What this document does not decide

```text
Framework, packaging and hosting        → PACK-16D
Offline bundle format                    → OD-P16C-07, PACK-16D
Inclusion-proof wire format               → OD-P16C-15, PACK-16D
Rate-limit values                        → PACK-16D
Interface layout                          → FRONT-PACK, bound by XA-*
```

**SPECIFIED. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY. NOT LEGALLY
ACTIVATED.**
