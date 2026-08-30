# PACK-16B — Key Ceremony Specification

**Round:** PACK-16B — Cryptographic Parameters, Key Ceremony and Trustee Architecture. **Specification and ADR only. No code. No cryptographic code. Not implemented. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-100`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 1. What this specifies, and what it adds

The ceremony realises the selected specification's distributed key
generation `[F-13]` and adds four things the specification does not have:

```text
1. A pre-publication commitment round               (§4)
2. Publication of the encrypted shares in the transcript  (§6, CT-09)
3. A complaint and disqualification protocol         (separate document)
4. An activation lock as an explicit governed act    (§8, phase 20)
```

**None of the four changes a cryptographic computation.** No challenge, no
proof, no hash input and no field consumed by a conforming verifier is
altered. A conforming verifier reads the election record and never needs to
know the ceremony transcript exists (`DS-13`).

---

## 2. Why additions were necessary

The specification's own treatment of a failed share is complete in three
sentences: the receiving guardian _"complains to the election administrator
and all other guardians. This triggers an out-of-band investigation"_; that
investigation _"does not necessarily allow identification of a misbehaving
guardian"_; and then _"the key generation procedure is started from
scratch"_ `[F-12]`.

That leaves, by the specification's own account: **no disqualification
predicate, no complaint format, no deadline, no adjudicator, no liveness
bound and no accountability.** And the encrypted shares are not part of the
published election record `[F-12]`, so share distribution is **not publicly
verifiable at all**.

For a toolkit that is a reasonable boundary. For an election architecture
it means one malicious guardian can force unbounded restarts while no
evidence distinguishes the accuser from the accused.

---

## 3. Phase overview

```text
 1  Election profile approval          11  Share receipt and verification
 2  Parameter-set approval             12  Complaints and dispute phase
 3  Guardian nomination                13  Disqualification before activation
 4  Guardian independence checks       14  Joint public-key computation
 5  Authentication and attestation     15  Extended base hash derivation
 6  Ceremony session creation          16  Ceremony transcript verification
 7  EPD² PRE-COMMITMENT ROUND          17  Independent auditor verification
 8  Guardian public contribution       18  Election Board acceptance
 9  Proof-of-possession verification   19  Public ceremony checkpoint
10  Encrypted share distribution       20  ACTIVATION LOCK
```

Phase 7 is EPD²'s; phases 9 and 10 are numbered separately here although
the specification treats commitment publication and proofs together.

---

## 4. Phase 7 — the pre-publication commitment round

### 4.1 Why

The specification's distributed key generation **omits the commit-then-open
round** of the construction it derives from — stated as deviation (i) in
the companion peer-reviewed paper `[F-14]`. The established literature
shows that a distributed key generation without that round permits a party
acting last to bias the joint public key: a two-party adversary can force
a chosen predicate on the key with probability 3/4 rather than 1/2
`[F-15]`.

**Two facts make this worth addressing rather than noting.** First, the
same specification deploys exactly the right countermeasure — a hash
pre-commitment before opening — **in its decryption protocol** and not in
key generation `[F-16]`. The asymmetry is visible in the document itself.
Second, without a commitment round a guardian publishing last can resample
its own contribution locally, recompute the resulting joint key and retry
until a predicate holds, while still holding a valid witness for its proof.
That is a grinding variant which needs no disqualification at all, and
**no source states it — it is this round's inference**, marked as such in
`[F-15]`.

**The counterweight, stated in fairness:** published work shows that bias
in this family is survivable for discrete-log schemes at the cost of a
larger modulus `[F-15]`, and this profile uses 4096 bits. The guardians are
publicly identified, and the deviation is an argued trade-off rather than
an oversight `[F-14]`. The only claim made here is that **a cheap
procedural round removes the question**, not that the question is a break.

### 4.2 The round

```text
7.1  Each guardian computes its contribution locally and does not publish it.
7.2  Each guardian publishes  C_i = H(H_X; "commitment_round", ctx, i, T_i)
     where T_i is the guardian's complete phase-8 publication and H_X is
     the EPD² hash domain (DS-10).
7.3  The Coordinator publishes the full set {C_1 … C_n} to the transcript.
7.4  Only after every C_i is published does any guardian publish T_i.
7.5  Every guardian and the Auditor check H(H_X; "commitment_round", ctx, i, T_i)
     against the published C_i for every i.
7.6  A mismatch is a complaint of class `contribution_mismatch` and the
     ceremony halts (complaint model §3).
```

| ID      | Rule                                                                                                                                                                                      |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `KY-07` | No guardian may publish its contribution before **all** commitments are published                                                                                                         |
| `KY-08` | The commitment covers the guardian's **entire** phase-8 publication, not a part of it                                                                                                     |
| `KY-09` | A guardian who fails to commit within the phase deadline is **disqualified before activation** and the ceremony restarts                                                                  |
| `KY-10` | A guardian whose opened contribution does not match its commitment is **disqualified**, and this is the one ceremony fault that is **cryptographically attributable without cooperation** |
| `KY-11` | This round uses the **EPD² hash domain** and enters **no** upstream computation (`DS-09`…`DS-13`)                                                                                         |
| `KY-12` | The commitments and openings are in the ceremony transcript, not the election record                                                                                                      |

`KY-10` is the return on the whole addition. Every other ceremony fault in
this architecture is hard to attribute; this one is arithmetic.

---

## 5. Phases 1–6 — before any key material exists

| #   | Phase                          | Inputs                                     | Outputs                                   | Secret material | Participants                               | Quorum          | Failure code                         | Retry              | Abort                |
| --- | ------------------------------ | ------------------------------------------ | ----------------------------------------- | --------------- | ------------------------------------------ | --------------- | ------------------------------------ | ------------------ | -------------------- |
| 1   | Election profile approval      | Draft manifest, election type, legal basis | Approved profile                          | none            | Election Board, Legal Activation Authority | Board           | `ceremony.profile_not_approved`      | yes                | context not created  |
| 2   | Parameter-set approval         | `EPD2-CRYPTO-1`, its digest and provenance | Bound parameter set                       | none            | Board + Auditor + Cryptographic Reviewer   | Board           | `parameter_set.not_approved`         | yes                | context not created  |
| 3   | Guardian nomination            | Candidate guardians and organisations      | Nomination records                        | none            | Election Board                             | Board           | `guardian.nomination_refused`        | yes                | —                    |
| 4   | Independence checks            | Declarations                               | Pairwise + composition assessment         | none            | Coordinator, Board, **Auditor**            | Board + Auditor | `guardian_independence.hard_failure` | new nomination     | ceremony not started |
| 5   | Authentication and attestation | Guardian credentials, device attestation   | Authenticated enrolment                   | none            | Guardians                                  | all n           | `guardian_authentication.failed`     | limited, then §5.1 | ceremony not started |
| 6   | Session creation               | Context ref, parameter set, roster, k, n   | Ceremony session with a public identifier | none            | Coordinator                                | all n           | `ceremony.session_creation_failed`   | yes                | —                    |

### 5.1 Authentication and device attestation

| ID      | Requirement                                                                                                                       |
| ------- | --------------------------------------------------------------------------------------------------------------------------------- |
| `KY-01` | Each guardian authenticates at **ceremony assurance** under PACK-14, with no shared account and no delegated credential (`KC-06`) |
| `KY-02` | The **device** is attested: it is the declared dedicated device, its software build identity matches the published one            |
| `KY-03` | Where attestation is unavailable, the alternative — witnessed provisioning from published media — is **recorded, not assumed**    |
| `KY-04` | A randomness health check runs and passes **before** any key material is generated (`RN-01`, §2.1 of the randomness architecture) |
| `KY-05` | Ceremony devices are **not virtualised and not snapshotted** (`RN-12`)                                                            |
| `KY-06` | Repeated authentication failure is a ceremony halt, never a lowered assurance requirement                                         |

---

## 6. Phases 8–13 — key generation

| #   | Phase                            | Inputs                                | Outputs                                                | Secret material                           | Public evidence                                                    | Quorum          | Failure code                      |
| --- | -------------------------------- | ------------------------------------- | ------------------------------------------------------ | ----------------------------------------- | ------------------------------------------------------------------ | --------------- | --------------------------------- |
| 8   | Public contribution generation   | Parameters; commitment round complete | `K_{i,j}`, `K̂_{i,j}`, `κ_i`, aggregated Schnorr proofs | coefficients, `ζ_i`, Schnorr nonces       | All commitments and proofs, in the transcript                      | all n           | `dkg.contribution_invalid`        |
| 9   | Proof-of-possession verification | All published contributions           | Verified proofs                                        | none                                      | Verification outcome per guardian                                  | all n           | `dkg.proof_of_possession_invalid` |
| 10  | Encrypted share distribution     | Recipients' `κ_ℓ`                     | `E_ℓ(P_i(ℓ), P̂_i(ℓ))` for every ordered pair           | polynomial evaluations, encryption nonces | **The ciphertexts and their Schnorr proofs — published** (`CT-09`) | all n           | `share_distribution.failed`       |
| 11  | Share receipt and verification   | Received shares; senders' commitments | Per-share verdicts                                     | decrypted shares                          | **Verdict per ordered pair, published** (`CT-10`)                  | all n           | `share_verification.failed`       |
| 12  | Complaints and dispute           | Verdicts, evidence                    | Adjudicated complaints                                 | none                                      | Complaint records and adjudications                                | —               | `complaint.unresolved`            |
| 13  | Disqualification                 | Adjudications                         | Disqualification decisions                             | none                                      | Decision and ground                                                | Board + Auditor | `disqualification.recorded`       |

### 6.1 Publishing the encrypted shares — an EPD² addition

The specification does **not** include the encrypted shares in the election
record, with the consequence that share correctness is not publicly
verifiable `[F-12]`.

| ID      | Rule                                                                                                                                                           |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `KY-13` | Every encrypted share **and its accompanying Schnorr proof of the encryption nonce** is published in the ceremony transcript                                   |
| `KY-14` | Publication is safe: the share is encrypted to the recipient's communication key, and the proof is over the ciphertext                                         |
| `KY-15` | Consequence: **anyone can verify that the ciphertext a guardian complains about is the ciphertext the sender published**, without any party revealing a secret |
| `KY-16` | Full attribution of a bad _plaintext_ share still requires the recipient to open it — §6.2. Publication narrows the ambiguity; it does not remove it           |

### 6.2 What publication does and does not achieve

| Claim about the share exchange                                       | Publicly checkable after `KY-13`?                                                                                                   |
| -------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| "This ciphertext is what the sender published"                       | **Yes** — by hash comparison                                                                                                        |
| "This ciphertext was formed by someone knowing its nonce"            | **Yes** — the Schnorr proof                                                                                                         |
| "The plaintext inside is inconsistent with the sender's commitments" | **Only if the recipient opens it** — §5 of the complaint model                                                                      |
| "The recipient is lying about what they received"                    | Resolvable once the recipient opens, because the opening is checkable against the published ciphertext and the sender's commitments |

**The asymmetry between accuser and accused is reduced, not eliminated.**
That is stated rather than overclaimed, and the complaint model's §5 sets
out the disclosure step that closes it — at a cost that is itself recorded.

---

## 7. Phases 14–19 — closing the ceremony

| #   | Phase                            | Inputs                                   | Outputs                                 | Public evidence                 | Quorum          | Failure code                     |
| --- | -------------------------------- | ---------------------------------------- | --------------------------------------- | ------------------------------- | --------------- | -------------------------------- |
| 14  | Joint public-key computation     | All verified contributions               | `K`, `K̂`                                | Both joint keys                 | all n           | `joint_key.mismatch`             |
| 15  | Extended base hash derivation    | `H_B`, `K`, `K̂`                          | `H_E`                                   | `H_E`                           | —               | `transcript.base_hash_mismatch`  |
| 16  | Transcript verification          | The full transcript                      | Per-guardian confirmation               | Confirmations                   | **all n**       | `transcript.verification_failed` |
| 17  | Independent auditor verification | Transcript, record, published parameters | Auditor verdict                         | The verdict, published          | Auditor         | `ceremony.auditor_refusal`       |
| 18  | Election Board acceptance        | Auditor verdict                          | Board acceptance                        | The acceptance                  | Board + Auditor | `ceremony.board_refusal`         |
| 19  | Public ceremony checkpoint       | Everything above                         | Signed, chained checkpoint on the board | The checkpoint, on every mirror | —               | `transcript.checkpoint_failed`   |

| ID      | Rule                                                                                                                                                   |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `KY-17` | Phase 16 requires **unanimous** guardian confirmation. One unconfirmed guardian is an unfinished ceremony, not a majority                              |
| `KY-18` | Every guardian independently recomputes `K` and `K̂` and confirms they match the published values, and that they appear in the guardian record `[F-13]` |
| `KY-19` | The Auditor's verification is **independent**: separate tooling, separate reading of the transcript, published verdict                                 |
| `KY-20` | An Auditor refusal **halts the ceremony**. It is not overridable by the Board (`R-11` cannot be overruled on a verification question)                  |
| `KY-21` | The ceremony checkpoint is published to **every mirror** before activation (`BB-07`, `BB-28`)                                                          |

---

## 8. Phase 20 — the activation lock

```text
The activation lock is a single, recorded, published, irreversible act
by the Election Board with Independent Auditor concurrence.

Before it:  guardians may be disqualified; the ceremony may restart;
            the context may be discarded.
After it:   the guardian set, k, n and the keys are FIXED for the context.
```

| ID      | Rule                                                                                                                                                                                     |
| ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `KY-22` | Activation requires: all 19 preceding phases complete; unanimous guardian confirmation; the Auditor's positive verdict; the Board's acceptance; the checkpoint published on every mirror |
| `KY-23` | Activation is **one-way**. There is no de-activation that returns a context to a modifiable ceremony state                                                                               |
| `KY-24` | After activation, `GL-14` and `GL-21` apply: no replacement, no substitution, no threshold change, no re-keying                                                                          |
| `KY-25` | The activation act is published with its timestamp coarsened to the context's `timestamp_granularity`                                                                                    |
| `KY-26` | A context may not reach `issuance_open` without an activation lock, and no configuration path bypasses this                                                                              |

---

## 9. Test, rehearsal and production separation

| ID      | Rule                                                                                                                                                                                  |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `KY-27` | Domains: `development`, `test`, `staging`, `ceremony rehearsal`, `production`, `independent verification` — separate keys, separate context identifiers, separate environment markers |
| `KY-28` | **Production guardian material never enters any other domain**, in any direction (`RN-18`)                                                                                            |
| `KY-29` | Test seeds are prohibited in production and structurally unreachable there (`RN-16`)                                                                                                  |
| `KY-30` | A **rehearsal transcript cannot activate a real election** — its domain marker causes configuration validation to refuse (`RN-19`)                                                    |
| `KY-31` | A test key must be **structurally incapable** of validating in the production trust store, demonstrated rather than asserted (`KC-20`)                                                |
| `KY-32` | Rehearsal is **required** before a first production ceremony for a given guardian set, and its material is destroyed after                                                            |
| `KY-33` | The specification's appendix parameters are **permitted in test and rehearsal only**, never in production (`PACK-16B-PARAMETER-SET-SPECIFICATION.md` §6)                              |

`KY-32` is a usability control as much as a security one: a five-person
ceremony that nobody has rehearsed will fail on its first attempt, and it
will fail at the point where restarting is most expensive.

---

## 10. Ceremony accessibility

Guardians are people, and the ceremony must not select for a particular
kind of body. Accessibility here has a hard boundary: **assistance must
never confer guardian capability.**

| ID      | Requirement                                                                                                                                                                                                                 |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `KY-34` | Every ceremony step is operable **by keyboard alone** and with a screen reader; state changes are announced                                                                                                                 |
| `KY-35` | The venue is **physically accessible**, and this is a venue-selection criterion, not an accommodation                                                                                                                       |
| `KY-36` | Sign-language interpretation is provided on request, and requested in due diligence (`GL-09`), not on the day                                                                                                               |
| `KY-37` | Every confirmation is available **both visually and audibly**, and no status is colour-only                                                                                                                                 |
| `KY-38` | Verification output is available in a form a screen reader can read meaningfully — not as an image or a bare hex blob                                                                                                       |
| `KY-39` | **No secret material is ever shared with an assistant.** An assistant may read the interface aloud, operate the keyboard under direction, and confirm published values; they may not see, enter, hold or transport a secret |
| `KY-40` | Where a guardian requires assistance touching the secret path, the arrangement is **dual-control**: two assistants from different organisations, both recorded, neither alone with the guardian's device                    |
| `KY-41` | **An accessibility assistant does not thereby become a guardian**, is not counted toward `n`, holds no share, and is named in the transcript as an assistant                                                                |
| `KY-42` | Ceremony documentation and the guardian's obligations are available in **plain language** as well as in technical form (`AX-21` lineage)                                                                                    |
| `KY-43` | Time pressure is removed: no countdown on any confirmation step, and a guardian may pause the ceremony                                                                                                                      |

`KY-39` and `KY-41` together are the boundary. The temptation in an
accessible ceremony is to let a helper "just do that bit", and that bit is
the whole of the guardian's function.

---

## 11. Failure, retry and abort

| Situation                            | Behaviour                                                    | Restart scope           |
| ------------------------------------ | ------------------------------------------------------------ | ----------------------- |
| Authentication failure               | Retry within limits, then halt                               | none                    |
| Device attestation failure           | Halt                                                         | none                    |
| Randomness health failure            | **Halt; no key material produced**                           | none                    |
| Missing commitment (phase 7)         | Disqualify; **restart from scratch**                         | whole ceremony          |
| Commitment/opening mismatch          | Disqualify; **restart from scratch**                         | whole ceremony          |
| Invalid proof of possession          | Complaint; adjudicate; disqualify; **restart**               | whole ceremony          |
| Share verification failure           | Complaint; adjudicate; disqualify; **restart**               | whole ceremony          |
| Unresolved complaint at deadline     | Complaint model §7                                           | whole ceremony, bounded |
| Joint-key mismatch between guardians | **Halt; restart** — a mismatch means someone's view differs  | whole ceremony          |
| Auditor refusal                      | **Halt.** Not overridable                                    | depends on the ground   |
| Board refusal                        | Halt                                                         | depends on the ground   |
| Checkpoint publication failure       | Halt until published on every mirror                         | none                    |
| Restart limit reached                | **Context discarded**; governance decision on how to proceed | complaint model §7      |

**Every ceremony restart is from scratch**, as the specification requires
`[F-12]`. There is no partial restart, no reuse of contributions from a
halted ceremony, and no carrying over of a "good" guardian's material —
because a contribution generated under one commitment set is not valid
under another.

---

## 12. What this document does not decide

```text
The ceremony application and its interface   → PACK-16D, FRONT-PACK
The venue, the schedule and the logistics     → GOVERNANCE
The device products and their procurement     → PACK-16D
The transcript wire format                    → PACK-16C
The witnessing and observation arrangements   → GOVERNANCE, remote-ceremony assessment
```

**SPECIFIED. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY. NOT LEGALLY
ACTIVATED.**
