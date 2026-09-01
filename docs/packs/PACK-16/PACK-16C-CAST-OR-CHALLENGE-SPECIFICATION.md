# PACK-16C — Cast-or-Challenge Specification

**Round:** PACK-16C — Casting, Receipt, Verification Client, Bulletin Board and Election Record. **Specification and ADR only. No code. No cryptographic implementation. Not implemented. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-101`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 1. What the challenge is for, in one paragraph

The voter's device is the one component nobody can verify. It could encrypt
a different choice than the one displayed, and no proof in the election
record would reveal it. **The challenge is the only answer anyone has:** the
voter can demand that the device open a ballot it has already committed to,
proving that it encrypted what the screen showed. A device that cheats
cannot know in advance which ballots will be opened.

```text
The challenge DETECTS a lying device. It does not PREVENT one.
Detection is probabilistic and depends on take-up.  (RR-03, T-P16A-33)
```

That sentence is repeated in the participant-facing text, in the ADR, and
in the permitted-claims registry, because everything in this document is
worthless if a reader thinks the challenge makes device compromise
impossible.

---

## 1A. The two-tier challenge model

**CORRECTED.** The first candidate offered one challenge action, repeatable
without limit, and every repetition produced a **published** spoiled ballot.
Against a batch of finite capacity `C` that permits an unbounded number of
publication-bearing artefacts, which is not a bound at all. The audit was
right: _"C exceeds the maximum plausible load"_ is a hope, not a bound.

Benaloh cast-or-challenge is **not** weakened. It is **split into the two
things it was always doing at once**:

```text
LOCAL DIAGNOSTIC CHALLENGE          unlimited
  the voter checks THIS DEVICE, locally, as often as they like
  nothing is submitted, nothing is published, nothing is spent

PUBLIC EVIDENTIARY CHALLENGE        bounded — K = 1 in the initial profile
  the voter produces PUBLIC AUDIT EVIDENCE against a dishonest client
  submitted, validated, committed to a sealed-batch leaf, published at
  closure, never counted

FINAL CAST BALLOT                   A = 1
  the vote
```

| ID      | Rule                                                                                                                                                                                                                                                                             |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CH-36` | **The repeatable part of Benaloh's mechanism is preserved in full, and moved where it belongs.** A voter may test their client as many times as they wish; what is bounded is not the _checking_, it is the _publishing_                                                         |
| `CH-37` | **`K_PUBLIC_CHALLENGES_PER_CONTINUATION = 1` and `A_ACCEPTED_CASTS_PER_CONTINUATION = 1` are architectural constants of the initial protocol profile**, not runtime configuration. They may not vary per user, per device, per session, by turnout, or during an active election |
| `CH-38` | **Changing `K` requires a new governed protocol-profile version**, an architectural review, a recomputed capacity plan (`TC-*` §4.9) and a privacy review. It is not a feature flag and must not be implemented as one                                                           |

### 1A.1 Local Diagnostic Challenge

A check performed **entirely inside the Voting Client, before any
submission**.

```text
does not submit a ballot artefact to the server
does not create a Bulletin Board entry
does not occupy a sealed-batch leaf
does not consume the continuation capability
does not create a public receipt
does not enter the Election Record
does not create tally-eligible material
does not change any server-side state
```

The client may: reveal the locally generated nonces, recompute the
plaintext-to-ciphertext relation, display the verification result, discard
the challenged local ballot, and construct a fresh ballot with fresh
randomness.

| ID      | Rule                                                                                                                                                                                                                                                                  |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CH-39` | **A locally challenged ballot must never be cast**, must never have its nonce reused, and must be **irreversibly discarded** before a fresh ballot is constructed (`CH-15` lineage)                                                                                   |
| `CH-40` | **A local diagnostic challenge is not evidence against a malicious client**, and no interface text, document or receipt may present it as one                                                                                                                         |
| `CH-41` | **The honest limitation, stated in the participant text and in the record:** _A malicious client can fake a purely local diagnostic challenge. Public evidentiary challenges and independent verification remain necessary for evidence against client misbehaviour._ |
| `CH-42` | **A local diagnostic challenge emits no server event and no telemetry.** `challenge.local_completed` exists as a client-local outcome only and is never transmitted (`EV-*`)                                                                                          |

### 1A.2 Public Evidentiary Challenge

A challenged ballot **submitted to the casting service** with a publicly
verifiable opening.

```text
is submitted to the casting service
is cryptographically validated on the same pipeline as a cast ballot
is marked challenged / spoiled
is NEVER tally eligible
is committed into the sealed-batch publication layer
is included in the Election Record after closure
DOES NOT consume the final cast entitlement
```

| ID      | Rule                                                                                                                                                                                                         |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `CH-43` | **One per anonymous continuation capability in the initial profile.** A second, differing public evidentiary challenge **fails closed** with `challenge.public_entitlement_exhausted`                        |
| `CH-44` | **A public evidentiary challenge never consumes the final cast entitlement.** After using it the voter still holds exactly one cast (`CN-*` §2A)                                                             |
| `CH-45` | **Further checking after the entitlement is spent remains possible — as local diagnostic challenges only.** The voter is told this plainly rather than being told they have "used up" their ability to check |
| `CH-46` | **The public challenge occupies exactly one publication-bearing leaf** and is bounded by the capacity plan (`TC-*` §4.9, `TC-*` §4.10)                                                                       |

### 1A.3 The cast flow after a public evidentiary challenge

| ID      | Rule                                                                                                                                                                                                                                                   |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `CH-47` | **After one public evidentiary challenge the voter constructs a fresh ballot with fresh randomness**, may perform further local diagnostic challenges, and submits one final cast ballot                                                               |
| `CH-48` | **The final cast ballot may not reuse the challenged ciphertext, the challenged nonce, the challenged `ballot_id` or the challenged confirmation code.** Reuse is `ballot_preparation.style_shape_mismatch` at best and a client defect at worst       |
| `CH-49` | **The public challenged ballot and the final cast ballot carry independent public references**, and nothing published links them. Linking them would tell an observer that this voter challenged and then cast — a behavioural signal about one person |

### 1A.4 Why not simply keep unlimited public challenges

| Rejected                                                            | Why                                                                                                                                                                                                                                                                                                       |
| ------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Unlimited publicly committed challenge artefacts per capability** | **No finite capacity bound exists.** One capability could fill every sealed batch with spoiled artefacts, exhausting the board (`T-P16C-51`), starving cast submissions of leaf slots (`T-P16C-53`), and making the fixed-shape publication model — which requires a computable maximum — unimplementable |
| Bounding by rate rather than by entitlement                         | A rate limit bounds _speed_, not _total_. `L_max` must be computable before the election opens                                                                                                                                                                                                            |
| Bounding public challenges globally rather than per capability      | A global cap is a race: the first voters to check exhaust the budget, and the rest cannot                                                                                                                                                                                                                 |
| Charging a public challenge against the cast entitlement            | Makes checking cost the vote — the exact trade the mechanism exists to avoid                                                                                                                                                                                                                              |

**SELECTED: bounded per-capability entitlement, `K = 1`.** It is the only
option that yields a finite, per-capability, pre-computable bound while
leaving both the checking and the vote intact.

---

## 2. The flow, and the commitment that makes it work

```text
1  client encrypts the ballot and generates all proofs
2  client derives the confirmation code from the encryptions and H_E
3  client DISPLAYS the confirmation code                    ← the commitment
4  ONLY NOW is the voter asked: cast, or challenge?
5a CAST      → nonce destroyed, envelope submitted
5b CHALLENGE → nonces revealed, ballot published as spoiled,
               ballot never counted, capability NOT consumed
```

| ID      | Rule                                                                                                                                                                                                 |
| ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CH-01` | **The commitment precedes the choice** (`BM-07`). The confirmation code is derived and shown before the voter is asked, so a dishonest client must commit before it learns whether it will be caught |
| `CH-02` | **Nothing is sent to the server between the commitment and the choice.** The server cannot influence, observe or pre-empt the decision (`CF-20`)                                                     |
| `CH-03` | **The voter chooses, and only the voter.** Not the client by policy, not the server by response, not an administrator, not a feature flag                                                            |
| `CH-04` | **Cast and challenge are mutually exclusive and irreversible** (`BM-08`). There is no challenge-after-cast and no cast-after-challenge                                                               |
| `CH-05` | **A challenged ballot is never counted** (`BM-09`), in any circumstance, by any authority, for any reason. `spoiled` is absorbing                                                                    |
| `CH-06` | **A cast ballot's nonce is never revealed** — not to the voter, not to support, not to an auditor, not under a legal order executed through this system. The client destroys it at step 5a           |

---

## 3. What is committed, revealed, published and destroyed

| Artefact                      | On **cast**                        | On **challenge**                                              |
| ----------------------------- | ---------------------------------- | ------------------------------------------------------------- |
| Ciphertexts                   | published                          | published                                                     |
| Well-formedness proofs        | published                          | published                                                     |
| Plaintext-knowledge proof     | published                          | published                                                     |
| Confirmation code             | published, and given to the voter  | published, marked spoiled                                     |
| **Ballot nonce / randomness** | **destroyed in the client**        | **published in full**                                         |
| **Plaintext selections**      | **never exist outside the client** | **derivable by anyone from the opening**                      |
| Board marking                 | `ballot_accepted`                  | `ballot_challenged` + `ballot_spoiled`, **distinctly marked** |
| Counted?                      | yes                                | **never**                                                     |
| Capability                    | **consumed**                       | **not consumed**                                              |

| ID      | Rule                                                                                                                                                                                                                                                                                        |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CH-07` | **A spoiled ballot is published with its complete opening**, so that any reader can re-encrypt and compare against the published ciphertexts (`BM-09`)                                                                                                                                      |
| `CH-08` | **A spoiled ballot is publicly distinguishable from a cast one** by its board entry type, not by inference from its contents                                                                                                                                                                |
| `CH-09` | **The challenge outcome is independently verifiable**: the verifier recomputes the encryption from the published nonces and plaintext and checks equality with the published ciphertexts (`IV-*`)                                                                                           |
| `CH-10` | **The server cannot silently convert a challenge to a cast, or a cast to a challenge.** `submission_class` is inside the envelope, covered by the confirmation code's derivation context and by the proofs' challenge — a server that flips it invalidates the ballot it is trying to forge |

**`CH-10` is the structural defence and is worth stating plainly:** the
protection against a dishonest server here is not a policy or an audit log.
It is that the class is cryptographically bound, so flipping it is
detectable by anyone re-verifying the record.

---

## 4. Why a challenged ballot is a real vote, and why the voter must be told

The opened ballot contains **the choice the voter actually made**. Publishing
it publishes that choice.

| ID      | Rule                                                                                                                                                                                                                                                                                                                                    |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CH-11` | **Before the first challenge, the voter is told, in plain language, that a challenged ballot is published in the open, is readable by anyone, and is not counted**                                                                                                                                                                      |
| `CH-12` | The warning is **not a scare-off**. It is factual, one screen, and immediately followed by the two actions with equal weight (`CH-14`)                                                                                                                                                                                                  |
| `CH-13` | The voter is offered the option to **challenge with a deliberately different selection** — choose something you do not intend to vote for, verify the device encrypted _that_, then cast your real choice. This is the safe pattern and it is recommended in the interface, **for both the local check and the public audit challenge** |

**`CH-13` is the single most useful piece of guidance in this document.** It
converts the challenge from "publish my real vote to test my phone" into a
test that costs the voter nothing at all, and it is the pattern the
interface should lead with.

---

## 5. Interface rules

### 5.0 Three actions, three names — never one button

```text
LOCAL CHECK
  verifies this device locally; not published; does not count;
  can be repeated as often as you like.

PUBLIC AUDIT CHALLENGE
  published as audit evidence; does not count;
  available once.

CAST BALLOT
  final submission; counts if accepted;
  cannot be replaced, because revoting is disabled.
```

| ID      | Rule                                                                                                                                                                                                                                 |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `CH-50` | **An ambiguous single "Challenge" control is prohibited.** The local check and the public audit challenge are different actions with different consequences and must be separately named, separately explained and separately chosen |
| `CH-51` | **The public audit challenge is never the default and never a destructive-styled action**, and the interface states that it is available once **before** the voter takes it                                                          |
| `CH-52` | **The three explanations above are governed catalogue content in plain-language German** and are held to the same accessibility standard as the rest of the flow (`XA-14`, `XA-16`)                                                  |
| `CH-53` | **No interface text may imply that using the public audit challenge reduces the voter's ability to check.** It does not: local checks remain unlimited (`CH-45`)                                                                     |

| ID      | Rule                                                                                                                                                                                                                                                                                                                                  |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CH-14` | **Challenging is as easy as casting** (`BM-11`): same screen, same visual weight, same number of actions. Not behind a link, not in a menu, not labelled "advanced"                                                                                                                                                                   |
| `CH-15` | **Challenge is never the default and never the destructive-styled action.** Neither is cast. Both are affirmative choices with equal prominence                                                                                                                                                                                       |
| `CH-16` | **Challenge is not presented as an error path** (`BM-11`). No warning icon, no red, no "are you sure something is wrong?"                                                                                                                                                                                                             |
| `CH-17` | **Accidental challenge is recoverable**: the voter simply prepares a fresh ballot. The interface says so on the challenge-result screen, and **the cast entitlement is still theirs** (`CF-26`, `CH-44`). An accidental _public_ audit challenge costs the public-challenge entitlement and nothing else                              |
| `CH-18` | **A voter may run a LOCAL DIAGNOSTIC CHALLENGE as many times as they like** (`BM-12`). No limit, no counter shown, no escalating friction, no "you have checked 3 times" message. **The PUBLIC AUDIT CHALLENGE is available once in the initial profile** (`CH-43`), and the interface says so before the voter uses it — never after |
| `CH-19` | **The explanation is comprehensible without cryptographic knowledge** (`BM-13`, `XA-*`). "Check that this app encrypted what you chose" — not "verify the Benaloh challenge transcript"                                                                                                                                               |
| `CH-20` | **No wording may enhance coercion.** Nothing that says "prove you voted as instructed", nothing that frames the opened ballot as evidence, nothing that suggests showing it to anyone                                                                                                                                                 |
| `CH-21` | **The receipt never indicates the ballot choice**, and a spoiled ballot's receipt — if any is issued — states only that a ballot was spoiled and not counted (`RE-*`)                                                                                                                                                                 |
| `CH-35` | **A challenging voter's own cast-as-intended check is local re-encryption and does not wait for publication.** The public opening at closure serves third-party audit, not the voter's immediate check (`BE-07`)                                                                                                                      |

---

## 6. Challenge probability — the decision, and what is not claimed

**Nothing is randomised behind the voter's back.**

| Option                                                                                              | Assessment                                                                                                                                                                                       | Verdict                                                                    |
| --------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------- |
| **Voter manually chooses; unlimited LOCAL diagnostic challenges, ONE public evidentiary challenge** | Honest, no hidden behaviour, take-up is low; effectiveness depends entirely on voters choosing to check. **Bounded on the published side so that a finite capacity bound exists** (`CH-37`, §1A) | **SELECTED for the initial profile**                                       |
| Voter manually chooses, unlimited **published** challenges                                          | No finite publication-bearing bound; one capability can exhaust the board                                                                                                                        | **Rejected on audit** — §1A.4                                              |
| System prompts an optional challenge                                                                | Raises take-up; risks training voters to click through a prompt; may be added as a **prompt**, never as an action                                                                                | Permitted as an interface refinement (`CH-23`)                             |
| System recommends a random challenge                                                                | The system deciding when to test itself is the wrong actor, and a compromised client would simply not recommend                                                                                  | **Rejected**                                                               |
| Mandatory challenge sample                                                                          | Forces publication of a real ballot from a sampled voter, or forces a fake one; both are worse than the disease                                                                                  | **Rejected**                                                               |
| Separate test-ballot flow                                                                           | A test flow that is not the real flow tests the test flow                                                                                                                                        | **Rejected as a substitute**; permitted as _additional_ practice (`CH-24`) |

| ID      | Rule                                                                                                                                                                                                                                    |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CH-22` | **No hidden challenge probability exists.** The system never challenges on the voter's behalf, never samples ballots for challenge, and never varies behaviour by voter                                                                 |
| `CH-23` | An **optional prompt** offering the challenge — once, before the first cast, dismissible, non-blocking — is permitted and is the recommended way to raise take-up. It is a prompt to _choose_, never an action taken for the voter      |
| `CH-24` | A **practice ballot** against a non-binding context is permitted and encouraged, and is clearly labelled as practice. It does not replace `CH-23`                                                                                       |
| `CH-25` | **No statistical detection guarantee is claimed** without an explicit published model naming the assumed challenge rate, the assumed cheating rate, and the resulting detection probability. Absent that model, the claim is prohibited |

### 6.1 What the honest statement looks like

```text
PERMITTED
  "If enough voters check, a device that encrypts the wrong choice
   will very likely be caught by someone."
  "Checking is the only way to catch a compromised device."

PROHIBITED
  "The challenge guarantees your vote was encrypted correctly."
  "Device compromise is detected automatically."
  "The system verifies your device for you."
  any percentage, unless CH-25's model is published alongside it
```

**The evidence for the concern is not hypothetical:** individual
verification take-up in the most mature comparable deployment was 9.9 % at
best (`RR-04`). A detection argument that assumes high take-up is an
argument about a system nobody has.

---

## 7. Accessibility of the choice

| ID      | Rule                                                                                                                                                                                                                          |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CH-26` | The cast/challenge choice is **fully keyboard operable**, correctly labelled for screen readers as two equal actions, and never conveyed by colour alone (`XA-*`)                                                             |
| `CH-27` | The confirmation code is presented in an **accessible, readable, transcribable form** — grouped characters, an unambiguous alphabet, and an audio-readable rendering. **QR is never the only form** (`XA-*`)                  |
| `CH-28` | **Assistance does not transfer the choice.** An assistant may read the screen and operate the device at the voter's direction; the decision remains the voter's, and PACK-15's assistance boundary is unchanged (`T-P16A-32`) |
| `CH-29` | The challenge result screen is comprehensible without cryptographic knowledge and states three things: what was checked, what the result means, and that this ballot was not counted                                          |

---

## 8. Failure handling

| Situation                                               | Outcome                                                           | Reason code                       |
| ------------------------------------------------------- | ----------------------------------------------------------------- | --------------------------------- |
| Commitment could not be derived                         | **Flow stops.** No ballot may be cast without a prior commitment  | `challenge.commitment_missing`    |
| Voter chooses challenge, opening incomplete             | Ballot is **spoiled anyway** and the failure is published         | `challenge.opening_incomplete`    |
| Challenge submitted, board publication fails            | `publication_disputed`; the ballot is still **not counted**       | `publication.failed`              |
| Re-encryption by a verifier does not match              | **Client compromise is indicated** — a first-class public finding | `challenge.reencryption_mismatch` |
| Client crashes after commitment, before choice          | Nothing was submitted; capability untouched; voter restarts       | `challenge.abandoned`             |
| Server returns a class different from the submitted one | Detected on verification; the record is invalid                   | `challenge.class_mismatch`        |

| ID      | Rule                                                                                                                                                                                                                                                      |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CH-30` | **`challenge.reencryption_mismatch` is an election-level event, not a voter-support ticket.** It is evidence that a client encrypted something other than what was shown, and it escalates under `FM-16C-*` to investigation and, if substantiated, abort |
| `CH-31` | **A failed challenge is still a spoiled ballot.** It is never quietly converted into a cast ballot to "recover" the voter's intent                                                                                                                        |

---

## 9. Publication constraints

| ID      | Rule                                                                                                                                                                                                                                                                                                                                                                                 |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `CH-54` | **A local diagnostic challenge is never published, never committed and never counted anywhere.** It leaves no board artefact, no record artefact and no event (`CH-42`)                                                                                                                                                                                                              |
| `CH-32` | **The number of public evidentiary challenges is not published before closure** (`BM-10`), and is not derivable from anything that is — a spoiled ballot's leaf is indistinguishable from an accepted one's and from a cover leaf (`TC-29`, `TC-57`). Per-context challenge counts are subject to disclosure control at `disclosure_min_cell = 5` afterwards                         |
| `CH-33` | **Public evidentiary spoiled ballots occupy leaves in the same sealed batches as accepted ones and are opened with them at closure** (`TC-57`, `BE-06`, `BE-07`), so that challenging is neither a timing signal nor a participation signal. **This replaces the first candidate's batched-and-delayed publication, which would have made the challenge rate visible during voting** |
| `CH-34` | **A spoiled ballot carries no participation signal** (`NIT-07`): it is not counted toward turnout, not toward the accepted set, and not toward any published figure before closure                                                                                                                                                                                                   |

**`CH-33` is easy to miss and matters:** if spoiled ballots published
immediately while cast ballots published in delayed batches, the act of
challenging would be a visible, timed event attributable to whoever was
using the system at that moment.

---

## 10. What this document does not decide

```text
Prompt wording and its German text        → PACK-15 content-catalogue lineage
Interface layout                           → FRONT-PACK, XA-* constraints bind it
Practice-context governance                → GOVERNANCE
Any published detection percentage         → CH-25 model, a future round
```

**SPECIFIED. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY. NOT LEGALLY
ACTIVATED.**
