# PACK-16C — Casting Flow Specification

**Round:** PACK-16C — Casting, Receipt, Verification Client, Bulletin Board and Election Record. **Specification and ADR only. No code. No cryptographic implementation. Not implemented. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-101`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 1. The flow, and the one line that shapes it

```text
The voter arrives holding nothing that identifies them, and leaves
holding nothing that proves how they voted.
```

Everything below is arranged so that both halves of that sentence stay true.

**Two moments in the flow are irreversible**, and the whole design turns on
placing them correctly:

```text
STEP 13  the cast-or-challenge choice     — irreversible for that ballot
STEP 17  the atomic acceptance boundary   — irreversible for the capability
```

---

## 2. The twenty-two steps

Each step below is specified with actor, input, output, cryptographic
operation, privacy-sensitive data, public evidence, audit evidence, failure
code, retry and timeout rule, and whether it is irreversible. Reason codes
resolve in `PACK-16C-REASON-CODE-CATALOG.md`; failure conditions in
`PACK-16C-FAILURE-AND-ABORT-MATRIX.md`.

---

### Step 1 — Isolated Voting Client launch

| | |
| --- | --- |
| **Actor** | Voter · Voting Client (`R-05` operates it, does not see the ballot) |
| **Input** | Election context reference |
| **Output** | A client instance on its **own origin**, with no identity session |
| **Crypto** | none |
| **Privacy-sensitive** | The fact of launching. **No account, no cookie, no storage entry, no analytics** (`CC-07`, `T-P16A-07`) |
| **Public evidence** | none |
| **Audit evidence** | Aggregate launch counts only, after the safe delay (`PM-*`) |
| **Failure** | `manifest.client_build_mismatch` → `FM-16C-01` |
| **Retry / timeout** | Freely retryable; no state to lose |
| **Irreversible** | No |

| ID       | Rule                                                                                                              |
| -------- | --------------------------------------------------------------------------------------------------------------------- |
| `CF-01`  | The Voting Client runs on an origin that carries **no identity session and no credential state** (`FIR-INV-003`)      |
| `CF-02`  | **No third-party script, no CDN without pinning, no analytics, no session replay, no fingerprinting surface**         |
| `CF-03`  | The client's build identity is **published and reproducible**; a mismatch is refused, not warned                      |

---

### Step 2 — Election-manifest retrieval

| | |
| --- | --- |
| **Actor** | Voting Client |
| **Input** | Election context reference |
| **Output** | `ElectionManifest` + its signature + `manifest_digest` |
| **Crypto** | Signature verification |
| **Privacy-sensitive** | none — the manifest is public |
| **Public evidence** | The manifest is a board entry (`BE-01`) |
| **Audit evidence** | none per-request |
| **Failure** | `manifest.unavailable`, `manifest.signature_invalid` → `FM-16C-02` |
| **Retry / timeout** | Retryable; bounded backoff |
| **Irreversible** | No |

---

### Step 3 — Manifest verification

| | |
| --- | --- |
| **Actor** | Voting Client |
| **Input** | Manifest, signature, published signer set |
| **Output** | Verified manifest, or refusal |
| **Crypto** | Signature verification; digest recomputation |
| **Failure** | `manifest.digest_mismatch`, `manifest.signer_unknown`, `manifest.context_closed` → `FM-16C-02` |
| **Irreversible** | No |

| ID       | Rule                                                                                                          |
| -------- | ----------------------------------------------------------------------------------------------------------------- |
| `CF-04`  | **The client verifies the manifest before showing a ballot.** A ballot is never rendered against an unverified manifest |
| `CF-05`  | The manifest digest is **bound into the ballot envelope** (`BP-*`) and into the confirmation code's derivation context, so a ballot cast against one manifest cannot be replayed against another |

---

### Step 4 — Parameter-set verification

| | |
| --- | --- |
| **Actor** | Voting Client |
| **Input** | `parameter_set_id`, the published parameter definition, the pinned specification digest |
| **Output** | Verified parameter set, or refusal |
| **Crypto** | Bit-equality comparison against the fixed values (`[F-05]` lineage) |
| **Failure** | `parameter_set.not_approved`, `parameter_set.digest_mismatch`, `parameter_set.deprecated`, `parameter_set.prohibited` → `FM-16C-03` |
| **Irreversible** | No |

| ID       | Rule                                                                                                            |
| -------- | ------------------------------------------------------------------------------------------------------------------- |
| `CF-06`  | **Downgrade is refused, not warned** (`BM-32`). There is no negotiation, no fallback and no "reduced parameters" path |
| `CF-07`  | The client validates every received group element for **subgroup membership** before use — no exceptions, no sampling |

---

### Step 5 — Election public-key verification

| | |
| --- | --- |
| **Actor** | Voting Client |
| **Input** | Joint public key, its ceremony evidence, the ceremony transcript checkpoint |
| **Output** | Verified key, or refusal |
| **Crypto** | Group membership; recomputation of the joint key from published guardian contributions; base-hash chain check |
| **Public evidence** | `joint_key.published` board entry (`BE-04`) |
| **Failure** | `manifest.joint_key_mismatch`, `manifest.ceremony_checkpoint_missing` → `FM-16C-04` |
| **Irreversible** | No |

| ID       | Rule                                                                                                          |
| -------- | ----------------------------------------------------------------------------------------------------------------- |
| `CF-08`  | The client **recomputes** the joint public key from the published contributions rather than trusting a served value. A mismatch refuses casting |
| `CF-09`  | **No ballot may be encrypted before `joint_key.published`** (`IN-11` lineage), and no ballot may be encrypted under a key whose ceremony checkpoint is absent from the board |

---

### Step 6 — Continuation-capability handoff

| | |
| --- | --- |
| **Actor** | Voter (bearer) → Voting Client |
| **Input** | The single-use capability, from PACK-15's handoff |
| **Output** | The capability held **in memory only** for the life of this attempt |
| **Privacy-sensitive** | **The capability itself.** It is never stored, logged, echoed, put in a URL, placed in browser storage, or sent to any origin other than the acceptance endpoint |
| **Public evidence** | **none, ever** (`CC-03`) |
| **Failure** | `continuation.absent`, `continuation.malformed` → `FM-16C-05` |
| **Retry / timeout** | The client discards it on tab close; the voter re-presents it |
| **Irreversible** | No |

| ID       | Rule                                                                                                              |
| -------- | --------------------------------------------------------------------------------------------------------------------- |
| `CF-10`  | The capability exists **in client memory only**. No `localStorage`, no `sessionStorage`, no IndexedDB, no cookie, no service-worker cache, no URL parameter, no referrer |
| `CF-11`  | The capability is transmitted **only** to the acceptance endpoint, **only** at step 15, and **never** to the board, the verification origin or any third party |

---

### Step 7 — Continuation-capability validation

| | |
| --- | --- |
| **Actor** | Casting service |
| **Input** | The capability, presented for a **stateless validity probe** |
| **Output** | A boolean and a reason code — **no reservation, no consumption** |
| **Crypto** | Whatever PACK-15's construction requires |
| **Privacy-sensitive** | The probe must not create a correlatable record; see `CN-*` |
| **Failure** | `continuation.invalid`, `continuation.already_spent`, `continuation.window_closed` → `FM-16C-06` |
| **Irreversible** | **No — and this is the point.** §3 |

| ID       | Rule                                                                                                          |
| -------- | ----------------------------------------------------------------------------------------------------------------- |
| `CF-12`  | Step 7 is a **probe, not a consumption**. It tells the voter early that their capability is unusable, before they spend ten minutes filling in a ballot |
| `CF-13`  | The probe is **rate-limited per capability, not per participant**, and produces no durable per-capability record beyond what PACK-15 already keeps |

---

### Step 8 — Ballot-style retrieval

| | |
| --- | --- |
| **Actor** | Voting Client |
| **Input** | Manifest, the capability's declared scope |
| **Output** | The `BallotStyle` — contests, options, selection limits |
| **Privacy-sensitive** | **A ballot style can be a small cohort.** Where a style is served to fewer than `disclosure_min_cell = 5` capabilities, the context is refused (`PM-*`) |
| **Failure** | `manifest.ballot_style_unknown` → `FM-16C-02` |
| **Irreversible** | No |

---

### Step 9 — Voter selection

| | |
| --- | --- |
| **Actor** | Voter |
| **Input** | Ballot style |
| **Output** | A plaintext selection set, **in client memory only** |
| **Privacy-sensitive** | **The choice itself.** It exists in the client, for the duration of this step and step 11, and nowhere else, ever |
| **Public evidence** | none |
| **Audit evidence** | **none — not even a count** |
| **Failure** | `ballot_preparation.contest_invalid`, `ballot_preparation.overvote` → `FM-16C-07` |
| **Retry / timeout** | Freely revisable until step 13 |
| **Irreversible** | No |

| ID       | Rule                                                                                                              |
| -------- | --------------------------------------------------------------------------------------------------------------------- |
| `CF-14`  | **The plaintext selection never leaves the client and is never persisted**, including in a draft, an autosave, a crash report or a screenshot-assist feature |
| `CF-15`  | A review screen is mandatory before step 13 and must present the selection in the same words as the ballot (`XA-*`) |

---

### Step 10 — Local ballot construction

| | |
| --- | --- |
| **Actor** | Voting Client |
| **Input** | Selections, ballot style, manifest |
| **Output** | The canonical plaintext ballot, including **placeholder selections** to bring each contest to its selection limit |
| **Crypto** | none yet |
| **Failure** | `ballot_preparation.placeholder_failure` → `FM-16C-07` |
| **Irreversible** | No |

---

### Step 11 — Local encryption

| | |
| --- | --- |
| **Actor** | Voting Client |
| **Input** | Plaintext ballot, joint public key, fresh randomness |
| **Output** | Encrypted contests and selections; the **ballot nonce** |
| **Crypto** | Exponential ElGamal per selection, under `EPD2-CRYPTO-1` |
| **Privacy-sensitive** | **The ballot nonce.** For a cast ballot it is destroyed and never revealed (`CH-*`) |
| **Failure** | `ballot.randomness_insufficient` (inherited from PACK-16B, **not re-minted**) → **fail closed**, `FM-16C-08`; `ballot_encryption.failed` → `FM-16C-08` |
| **Retry / timeout** | Retryable **only by re-encrypting from the same plaintext with fresh randomness**, before step 13 |
| **Irreversible** | No |

| ID       | Rule                                                                                                          |
| -------- | ----------------------------------------------------------------------------------------------------------------- |
| `CF-16`  | **A randomness self-test precedes encryption. On failure the client refuses to encrypt and produces no ballot** (`FM-16B-06`, `T-P16A-35`) — it does not degrade, retry silently or fall back |
| `CF-17`  | Every encryption uses **fresh randomness**; no nonce is reused across selections, contests, ballots or attempts (`RN-19` lineage) |

---

### Step 12 — Local proof generation

| | |
| --- | --- |
| **Actor** | Voting Client |
| **Input** | Ciphertexts, nonces, manifest context, extended base hash |
| **Output** | Per-selection range proofs, per-contest sum proofs, and the **proof of knowledge of the plaintext** (`BM-14`) |
| **Crypto** | NIZK under strong Fiat–Shamir, statement and context in every challenge (`FS-*`) |
| **Failure** | `ballot_proof.generation_failed` → **fail closed**, `FM-16C-09` |
| **Irreversible** | No |

| ID       | Rule                                                                                                              |
| -------- | --------------------------------------------------------------------------------------------------------------------- |
| `CF-18`  | **Proof generation happens in the client, before submission.** A ballot without complete proofs is never submitted, and a server never generates a proof on a voter's behalf |

---

### Step 13 — Cast-or-challenge decision · **IRREVERSIBLE**

| | |
| --- | --- |
| **Actor** | **The voter, and only the voter** |
| **Input** | The **committed** confirmation code (`BM-07`), displayed before the choice |
| **Output** | `cast` or `challenge`, bound to this specific encrypted ballot |
| **Crypto** | Confirmation-code derivation from the ballot's own encryptions and the extended base hash (`BM-03`) |
| **Privacy-sensitive** | The choice of *whether* to challenge is not published before closure (`BM-10`) |
| **Public evidence** | Later, at step 19, as `ballot_accepted` or `ballot_challenged` |
| **Failure** | `challenge.commitment_missing` → `FM-16C-10` — **the flow stops; no ballot may be cast without a prior commitment** |
| **Retry / timeout** | **None. The choice is final for this ballot** |
| **Irreversible** | **YES** |

| ID       | Rule                                                                                                          |
| -------- | ----------------------------------------------------------------------------------------------------------------- |
| `CF-19`  | **The commitment to the confirmation code precedes the choice** (`BM-07`). A client that learns the choice before committing can cheat, and this ordering is what stops it |
| `CF-20`  | **The client cannot decide after seeing a server response**, and the server cannot influence the choice — nothing is sent to the server between the commitment and the voter's decision |

---

### Step 14 — Challenge / spoil handling

| | |
| --- | --- |
| **Actor** | Voting Client → Casting service → Board |
| **Input** | The challenged ballot **and its opening** (nonces) |
| **Output** | A published, openly verifiable spoiled ballot; **the ballot is never counted** |
| **Crypto** | Publication of the ballot and its randomness, so anyone can re-encrypt and compare |
| **Privacy-sensitive** | The revealed plaintext is a **real choice the voter made** — the voter is warned before challenging (`CH-*`, `XA-*`) |
| **Public evidence** | `ballot_challenged` + `ballot_spoiled` board entries |
| **Failure** | `challenge.opening_incomplete` → `FM-16C-11` |
| **Irreversible** | **YES** — a challenged ballot can never become a cast ballot |
| **Capability** | **NOT consumed.** The voter proceeds to a fresh ballot — §4 |

---

### Step 15 — Cast submission

| | |
| --- | --- |
| **Actor** | Voting Client → Casting service |
| **Input** | The canonical envelope (`BP-*`) + the continuation capability + a client-generated **retry token** |
| **Output** | A submission accepted for validation |
| **Privacy-sensitive** | The capability travels here, once, over an authenticated channel |
| **Failure** | `submission.malformed`, `submission.too_large`, `submission.window_closed` → `FM-16C-12` |
| **Retry / timeout** | **Idempotent on the retry token** — §5 |
| **Irreversible** | No — until step 17 |

---

### Step 16 — Server cryptographic validation

| | |
| --- | --- |
| **Actor** | Casting service |
| **Input** | The envelope |
| **Output** | Valid / invalid, with a distinct reason code per failure class |
| **Crypto** | The full ordered pipeline of `PACK-16C-BALLOT-VALIDATION-PIPELINE.md` — schema, canonical encoding, profile, parameters, context, manifest binding, style binding, group membership, subgroup checks, every proof, contest constraints, confirmation code |
| **Failure** | `ballot_proof.invalid`, `ballot_proof.range_failed`, `ballot_proof.contest_sum_failed`, `submission.non_canonical_encoding` → `FM-16C-13` |
| **Irreversible** | No |

| ID       | Rule                                                                                                              |
| -------- | --------------------------------------------------------------------------------------------------------------------- |
| `CF-21`  | **Every cryptographic check completes before the capability is consumed.** There is no "accept now, verify later" (`VP-*`) |
| `CF-22`  | A ballot failing any check is **rejected without consuming the capability**, with a distinct reason code — never normalised, coerced or partially accepted |

---

### Step 17 — Capability consumption · **IRREVERSIBLE**

| | |
| --- | --- |
| **Actor** | Casting service, inside the **atomic acceptance boundary** |
| **Input** | A cryptographically valid ballot + a valid, unspent capability |
| **Output** | Capability marked spent **and** ballot durably accepted — **or neither** |
| **Privacy-sensitive** | The spend record is written to the **credential-side stream only** (`CC-05`), with a coarsened timestamp (`CC-06`) |
| **Public evidence** | **none** — no consumption event is ever published (`CC-10`) |
| **Failure** | `acceptance.capability_already_spent`, `acceptance.atomic_boundary_failed` → `FM-16C-14` |
| **Irreversible** | **YES** |

| ID       | Rule                                                                                                          |
| -------- | ----------------------------------------------------------------------------------------------------------------- |
| `CF-23`  | **Consumption and durable acceptance succeed together or not at all** (`CN-*`). A capability is never spent against a ballot that was not accepted, and a ballot is never accepted against a capability that was not spent |
| `CF-24`  | **No record holds a continuation reference and a ballot identifier together** (`CC-04`), including inside this boundary — the boundary is atomic in effect, not in storage |

---

### Step 18 — Ballot acceptance

| | |
| --- | --- |
| **Actor** | Casting service |
| **Input** | The committed acceptance |
| **Output** | State `accepted_pending_publication`; a **signed publication commitment** returned to the client |
| **Public evidence** | The commitment is verifiable and later matched against the board entry |
| **Failure** | `acceptance.commitment_signing_failed` → `FM-16C-15` |
| **Irreversible** | **YES** |

---

### Step 19 — Sealed batch commitment, then closure publication

**CORRECTED.** The first candidate published a `ballot_accepted` entry in a
delayed batch. Under the corrected turnout model publication has two phases
(`PA-*` §4, `TC-*` §4).

| | |
| --- | --- |
| **Actor** | Bulletin-Board Operator (`R-06`) |
| **Input** | The accepted ballot's leaf — a hiding commitment over its artefact digests (`TC-27`) |
| **Output, phase 1** | The leaf is inside the `commitment_root` of the **named** `sealed_batch_commitment` (`BE-24`), published at that window's scheduled time |
| **Output, phase 2** | At closure, the `ballot_accepted` entry itself, with its `sealed_batch_opening` (`BE-05`, `BE-25`) |
| **Privacy-sensitive** | **Occupancy.** The commitment is constant-size over fixed capacity `C`, so phase 1 discloses nothing about how many ballots exist (`TC-29`, `TC-33`) |
| **Public evidence** | Phase 1: the commitment entry and its checkpoint. Phase 2: the entry, the opening, the reconciliation |
| **Voter evidence** | Phase 1: a privacy-safe inclusion proof, available **before closure** (`TC-36`…`TC-40`) |
| **Failure** | `publication.batch_delayed`, `publication.deadline_missed`, `bulletin_board.batch_commitment_missing` → `FM-16C-18`, `FM-16C-19`, `FM-16C-20`; **never silent** |
| **Irreversible** | **YES** — a published commitment root cannot be altered |

| ID       | Rule                                                                                                              |
| -------- | --------------------------------------------------------------------------------------------------------------------- |
| `CF-25`  | **`accepted but never published` is not a permitted terminal state.** It is a published failure with an election-level remedy (`PA-*`) |
| `CF-35`  | **The obligation is bounded by one batch interval**, because the cadence is fixed and gapless (`PA-10`). The voter's receipt names the window (`RE-17`) |
| `CF-36`  | **No individual ballot entry is published before closure**, and step 19 phase 2 therefore happens for every ballot at the same moment — the closure opening (`BA-24`, `BE-28`) |

---

### Step 20 — Receipt issuance

| | |
| --- | --- |
| **Actor** | Casting service → Voter |
| **Input** | Confirmation code, publication commitment, verification instructions |
| **Output** | The receipt (`RE-*`) |
| **Privacy-sensitive** | **The receipt must not reveal the choice**, and must not carry a credential reference, an identity, or an exact consumption timestamp |
| **Failure** | `receipt.generation_failed` → `FM-16C-17` — **the ballot stays accepted**; the receipt is re-derivable |
| **Irreversible** | No — the receipt can be re-issued from public data |

---

### Step 21 — Voter-side recorded-as-cast verification

| | |
| --- | --- |
| **Actor** | Voter, via the **Verification Client on a separate origin** (`BB-14`) |
| **Input** | Confirmation code |
| **Output** | Present / absent, plus the current checkpoint (`BB-22`…`BB-25`) |
| **Privacy-sensitive** | Lookup timing and source (`T-P16A-08`); the query is **unauthenticated and rate-limited per code** |
| **Failure** | `verification.code_not_found` → a **first-class outcome with a dispute path** (`BM-19`), never a generic error |
| **Irreversible** | No |

---

### Step 22 — Independent verification option

| | |
| --- | --- |
| **Actor** | Anyone — no account, no credential, no terms (`BB-36`) |
| **Input** | The published election record |
| **Output** | A machine-readable verification result (`IV-*`) |
| **Failure** | Any of the `VERIFICATION_*` results |
| **Irreversible** | No |

---

## 3. Why step 7 probes and step 17 consumes

Splitting the capability check into a **probe** and a **consumption** is a
deliberate decision with a cost.

**What it buys:** a voter with an already-spent or expired capability learns
it in five seconds instead of after completing a ballot — and completing a
ballot means making a choice, which is the thing this system tries hardest
not to waste.

**What it costs:** the probe is an extra observable event on the
credential side. It is mitigated by `CF-13` (rate-limited per capability,
no new durable record) and by the fact that the probe reveals nothing the
consumption would not.

**What it must never become:** a reservation. A probe that reserved the
capability would create a window in which the capability is neither usable
nor spent, and that window is a denial-of-service surface against an
individual voter. §5 and `CN-*` treat reservation as a rejected option.

---

## 4. A challenge does not consume the capability

```text
CHALLENGE  ballot spoiled and published · capability NOT consumed
CAST       ballot accepted and published · capability consumed
```

| ID       | Rule                                                                                                          |
| -------- | ----------------------------------------------------------------------------------------------------------------- |
| `CF-26`  | **Checking costs the voter nothing but time.** The **cast entitlement** survives every challenge of either kind, and the voter prepares a fresh ballot with fresh randomness (`CH-44`) |
| `CF-27`  | There is **no limit on local diagnostic challenges** (`BM-12`). A limit would be a ceiling on how hard a voter may check their own device. **The public evidentiary challenge is bounded to one per capability in the initial profile** (`CH-37`, `CH-43`) |
| `CF-28`  | A fresh ballot after a challenge is a **new ballot with a new identifier and new randomness** — never a re-submission of the opened one (`CH-48`) |
| `CF-37`  | **A local diagnostic challenge never reaches step 15.** It completes inside the client, submits nothing, and produces no board or record artefact (`CH-39`…`CH-42`) |
| `CF-38`  | **A public evidentiary challenge passes through its own atomic boundary** (`CN-*` §2B), which spends the public-challenge entitlement and **never** the cast entitlement |

**The consequence is stated plainly because it matters:** unlimited *local*
checking plus a cast entitlement that survives every challenge means a voter
can test their client as many times as they like. What is bounded is
**publication**, not checking — because an unbounded number of published
spoiled artefacts against a finite batch capacity is not a bound at all
(`CH-36`, `TC-*` §4.9).

---

## 5. Retry, timeout and the uncertain submission

The genuinely hard case is: **the client submits, the network dies, and the
voter does not know whether their ballot was accepted.**

| ID       | Rule                                                                                                              |
| -------- | --------------------------------------------------------------------------------------------------------------------- |
| `CF-29`  | Every submission carries a **client-generated retry token**, unique to the attempt and **derived from the ballot, not from the capability** |
| `CF-30`  | Re-submission with the same retry token and the same envelope is **idempotent**: it returns the original outcome and never consumes a second capability |
| `CF-31`  | Re-submission with the same retry token and a **different** envelope is **rejected** — `submission.retry_token_conflict` |
| `CF-32`  | On timeout the client enters `submission_uncertain` and **offers the voter a status check by confirmation code**, not an automatic re-submission |
| `CF-33`  | **Recovery never issues a second capability** (`CC-08`). If the ballot was accepted, the voter has voted; if it was not, the capability was not consumed and the voter may retry |
| `CF-34`  | The retry token is **not published, not in the receipt, and not in the election record** |

**The one case that is not fully solvable** is a capability consumed inside
the atomic boundary followed by total loss of the client before any receipt
reaches the voter. The ballot is accepted and will publish; the voter has no
confirmation code and cannot look it up. `DP-*` specifies the support path,
and it deliberately **cannot find the ballot by identity** — the remedy is
publication of the board state and, if the voter is genuinely stranded, an
election-level record of irreducible loss.

---

## 6. Where the flow stops, per class of failure

| Class                                    | Stops at | Capability | Ballot state             |
| ---------------------------------------- | -------- | ---------- | ------------------------ |
| Manifest, parameter or key failure        | 2–5      | untouched  | none exists              |
| Capability invalid                        | 7        | untouched  | none exists              |
| Randomness or proof failure               | 11–12    | untouched  | `prepared`, discarded    |
| Voter challenges                          | 14       | **untouched** | `challenged` → `spoiled` |
| Submission malformed                      | 15       | untouched  | `submitted` → `rejected` |
| Any cryptographic check fails             | 16       | **untouched** | `rejected`            |
| Atomic boundary fails                     | 17       | **untouched** | `submitted`, retryable |
| Publication fails                         | 19       | **spent**  | `accepted_pending_publication` → `publication_disputed` |

**The column that matters is the third.** The capability is spent in exactly
one place, and every failure before it leaves the voter able to try again.

---

## 7. What this document does not decide

```text
The exact wire formats                     → PACK-16C-API-CATALOG.md
The envelope's field list                  → PACK-16C-BALLOT-PREPARATION-...
The consumption mechanism's internals      → PACK-16C-CONTINUATION-...
Batching interval and delay distribution   → OD-P16C-*, PACK-16D
Client framework, storage and packaging    → PACK-16D
```

**SPECIFIED. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY. NOT LEGALLY
ACTIVATED.**
