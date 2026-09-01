# PACK-15 — Voting Credential Lifecycle Matrix

**Round:** PACK-15 — specification and ADR only. **No code. Not implemented. Not a candidate. Not a PASS.**
**Repository version:** unchanged at `0.14.0` · **Canon version:** unchanged at `0.8.0`
**Baseline:** `EPD2_PACK-14_IDENTITY_AUTHENTICATION_ACCOUNT_SECURITY_0.14.0_FINAL_PASS.zip`
**Authoritative register:** `EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER_UPDATED_V6.md`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**
**Architecture correction applied (2026-07-31).**

**Corrected by this revision:** the credential delivery boundary and its
prohibited channels (`OD-P15-07`), single-visit issuance and its
consequences, and the randomized minting delay (`OD-P15-02`).

---

## 1. Fields

| Field                    | Type              | Req | Rule                                                                       |
| ------------------------ | ----------------- | --- | -------------------------------------------------------------------------- |
| `VotingCredentialId`     | opaque            | R   | Random, non-derived. **Never used as, or stored beside, a ballot ID**      |
| `CredentialType`         | enum              | R   | Per context type; a nomination credential is not a consultation credential |
| `CredentialStatus`       | enum              | R   | §2                                                                         |
| `VotingContextReference` | context reference | R   | Exactly one                                                                |
| `IssuedAt`               | timestamp         | R   | **Coarsened to `timestamp_granularity`**                                   |
| `ExpiresAt`              | timestamp         | R   | Coarsened; never beyond the context's redemption window                    |
| `RedeemedAt`             | timestamp         | C   | Coarsened; set atomically at redemption                                    |
| `RevokedAt`              | timestamp         | C   | Coarsened; set only before redemption and before the cutoff                |
| `RevocationReason`       | reason code       | C   | Registered code; never free text                                           |
| `RedemptionReference`    | opaque            | C   | Scoped to the redemption act; never a ballot reference                     |

**Structurally absent**, following canon 10.1's existing prohibition on
`ParticipationCredential`: `identity_record_id`, `person_id`, `account_id`,
`membership_id`, `member_number`, `full_name`, `date_of_birth`, `address`,
`email`, `eid_subject`, communication persona, **any assertion identifier
or nonce**, and **any context-scoped pseudonym**. The last two are
PACK-15's additions to the existing list and are the load-bearing ones.

---

## 2. States

| State             | Meaning                                                      | Terminal |
| ----------------- | ------------------------------------------------------------ | -------- |
| `requested`       | An issuance request exists                                   | no       |
| `eligible`        | The assertion verified; issuance authorized                  | no       |
| `issued`          | The credential exists and has not been used                  | no       |
| `revoked`         | Withdrawn before redemption, before the cutoff               | yes      |
| `expired`         | Validity elapsed unused                                      | yes      |
| `redeemed`        | Consumed; a continuation capability was handed to the client | yes      |
| `replay_rejected` | A further presentation of a spent credential was refused     | n/a      |
| `cancelled`       | The context was cancelled or suspended terminally            | yes      |
| `disputed`        | A dispute is open against this credential's handling         | no       |

`replay_rejected` is an **event**, not a resting state.

---

## 3. Transitions

| From        | To          | Trigger                                         | Authorized actor                        | Atomic with                   | Evidence       |
| ----------- | ----------- | ----------------------------------------------- | --------------------------------------- | ----------------------------- | -------------- |
| —           | `requested` | Assertion presented **from WS-03**              | The isolated client                     | —                             | `AS-03`        |
| `requested` | `eligible`  | Assertion verified, nonce unspent               | Credential Issuer                       | Nonce spent-marking           | `AS-03`        |
| `requested` | _refused_   | Any verification failure                        | Credential Issuer                       | —                             | `AS-03`        |
| `eligible`  | `issued`    | Credential minted, after the minting delay (§6) | Credential Issuer                       | Same transaction as above     | `AS-03`        |
| `issued`    | `redeemed`  | Redemption in the same WS-03 visit              | Credential Issuer                       | Continuation capability issue | `AS-03`        |
| `issued`    | `revoked`   | Governed condition, before the cutoff           | Credential Issuer (+ dual control late) | —                             | `AS-03`        |
| `issued`    | `expired`   | Validity elapsed                                | Clock, checked on use                   | —                             | `AS-03`        |
| `issued`    | `cancelled` | Context cancelled                               | Voting Operations Officer               | —                             | `AS-03`        |
| `redeemed`  | —           | **Nothing.** No transition leaves `redeemed`    | —                                       | —                             | —              |
| any         | `disputed`  | A dispute is opened                             | Dispute Reviewer                        | —                             | Dispute record |

**`redeemed` is absorbing.** No administrative act, no break-glass grant,
no incident response and no legal compulsion executed through this system
moves a credential out of `redeemed`, because doing so would imply the
ability to find and act on what it produced.

---

## 4. Required properties

| Property                     | Requirement                                                                    | Violation code                 |
| ---------------------------- | ------------------------------------------------------------------------------ | ------------------------------ |
| Opaque                       | No parseable structure; no embedded claims                                     | —                              |
| Single-use                   | One redemption, ever                                                           | `CREDENTIAL_ALREADY_REDEEMED`  |
| Short-lived                  | Expiry checked at redemption                                                   | `CREDENTIAL_EXPIRED`           |
| Context-bound                | One context; no partial match                                                  | `CREDENTIAL_CONTEXT_MISMATCH`  |
| Audience-bound               | The isolated voting origin only                                                | `CREDENTIAL_AUDIENCE_MISMATCH` |
| **Never leaves WS-03**       | Volatile page memory only; never persisted, displayed, copied or exported (§5) | `DELIVERY_CHANNEL_REFUSED`     |
| Non-transferable             | As far as is technically enforceable — and no further (§8)                     | —                              |
| Non-replayable               | Spent state checked atomically                                                 | `CREDENTIAL_REPLAY_DETECTED`   |
| Unlinkable from voting side  | Nothing in it resolves to a participant                                        | —                              |
| No identity fields           | Structural, per canon 10.1 and §1                                              | —                              |
| No reusable bearer semantics | Possession after redemption grants nothing                                     | —                              |
| No cross-context use         | —                                                                              | `CREDENTIAL_CONTEXT_MISMATCH`  |

---

## 5. Delivery — `OD-P15-07` closed

**Credential material is delivered only inside the isolated WS-03
boundary.**

### 5.1 The reference flow

| Step | Where | What happens                                                                    | What is held afterwards      |
| ---- | ----- | ------------------------------------------------------------------------------- | ---------------------------- |
| 1    | WS-02 | The ordinary workspace transmits **only** a one-time handoff artifact           | Nothing about the assertion  |
| 2    | WS-03 | The artifact is redeemed; the assertion is obtained                             | Assertion, volatile memory   |
| 3    | WS-03 | The assertion is presented; the minting delay elapses; the credential is issued | Credential, volatile memory  |
| 4    | WS-03 | The credential is redeemed                                                      | Continuation capability only |

The ordinary workspace never receives, holds, displays, logs or forwards an
assertion or a credential. The artifact is PACK-14's
`VotingHandoffArtifact` — opaque, single-use, short-lived, audience-bound,
context-bound, identity-free (ADR-088), unchanged by this round.

### 5.2 Prohibited delivery channels — normative

| Channel                                             | Why it is refused                                              |
| --------------------------------------------------- | -------------------------------------------------------------- |
| Email                                               | Mailboxes are shared, forwarded, archived and breached         |
| SMS                                                 | Same, plus carrier-side exposure                               |
| Clipboard                                           | Readable by other origins and by extensions                    |
| Ordinary URL query or fragment                      | Logged by proxies, servers, history and referrers              |
| Downloadable file                                   | Persists outside the isolation boundary                        |
| On-screen display as copyable or transcribable text | Becomes a transferable bearer value, and a coercion instrument |
| Push notification payload                           | Delivered through third-party infrastructure                   |
| Print or PDF rendition                              | Persists, and is operator-visible in an assisted setting       |
| Any operator-visible surface                        | A helper who can see it can retain it                          |
| Any persistent client storage in WS-03              | ADR-096 forbids the storage; this forbids the content too      |

**No operator, helper or support role ever sees credential material** — not
in a screen share, a log, an error report or a support tool.

### 5.3 Single-visit issuance — the consequence, stated

Because credential material may not persist outside WS-03 and may not be
displayed, **issuance and redemption occur within one WS-03 visit.**
`CredentialIssuanceWindow` governs when a participant may _enter_ the
voting origin, not a period in which they hold a credential outside it.

If the page is lost between issuance and redemption, the credential remains
`issued` and unredeemed. The remedy is the governed revoke-then-reissue
path before the cutoff — **not** a recovery that would require identifying
the holder.

**Advance issuance across separate visits is out of scope for this round**
and is deferred to PACK-16 (`OD-P15-05`): holding a credential between
visits requires a holder-side custody decision that WS-03's isolation rules
forbid and that a cryptographic construction may solve properly.

### 5.4 Accessible and assisted delivery

| Requirement                                                                                        | Consequence                                                          |
| -------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| Assistance ends at the boundary of the credential exchange                                         | A helper may bring the participant to WS-03 and no further           |
| **No helper or operator retains credential material** — there is none to retain                    | The exchange is machine-to-machine inside the page                   |
| No screen sharing, remote control or shadowing during the exchange                                 | An observed exchange is an operator-visible credential               |
| Assisted-action receipts record the assistance, never the credential                               | `F-P15-08`                                                           |
| The accessible path is an **independent** path, not a supervised one                               | Screen-reader, keyboard-only and low-bandwidth flows are first-class |
| Where an independent accessible path is not achievable, it is a named limitation with an owner     | Not a silent downgrade                                               |
| Offline and in-person fallback confirms **eligibility**, never delivers a credential outside WS-03 | The isolation is not waived for accessibility                        |

---

## 6. Issuance controls

| Control                                          | Enforced by                                                                                     | Failure code                                                 |
| ------------------------------------------------ | ----------------------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| Single issuance per participation unit           | Identity side, at assertion minting                                                             | `CREDENTIAL_ALREADY_ISSUED`                                  |
| Idempotency on retry                             | Credential Issuer, keyed on the assertion nonce                                                 | — (same outcome)                                             |
| Duplicate request detection                      | Spent-nonce set                                                                                 | `ASSERTION_ALREADY_USED`                                     |
| Stale eligibility rejection                      | Assertion expiry; issuer-side supersession before minting                                       | `ELIGIBILITY_SOURCE_STALE` / `ASSERTION_EXPIRED`             |
| Assurance verification                           | `RequiredAssuranceSatisfied` must be true                                                       | `ELIGIBILITY_ASSURANCE_INSUFFICIENT`                         |
| Issuance-window validation                       | Voting Context Registry                                                                         | `CREDENTIAL_ISSUANCE_WINDOW_CLOSED`                          |
| Context validation                               | Credential Issuer                                                                               | `CREDENTIAL_CONTEXT_MISMATCH`                                |
| Organizational-scope validation                  | Credential Issuer                                                                               | `VOTING_CONTEXT_SCOPE_MISMATCH`                              |
| Origin validation — request must come from WS-03 | Credential Issuer                                                                               | `CREDENTIAL_AUDIENCE_MISMATCH`                               |
| Replay prevention                                | Spent-nonce set, atomic                                                                         | `ASSERTION_ALREADY_USED`                                     |
| **Randomized minting delay**                     | Credential Issuer, uniform over `[minting_delay_min, minting_delay_max]`, default `[5 s, 30 s]` | `CREDENTIAL_MINTING_DELAYED` (progress state, not a failure) |
| Reason-coded denial                              | All of the above                                                                                | Registered codes only                                        |
| Issuance evidence                                | `AS-03` only                                                                                    | —                                                            |

**No silent reissue.** A reissue is a distinct governed request with its own
decision, dual control where the policy requires it, and evidence on both
streams as two independent records.

---

## 7. Exceptional cases

| Case                                           | Behaviour                                                                                                                                                   | Exactly-once preserved by                  |
| ---------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------ |
| Repeated request, same idempotency key         | Same outcome returned; nothing new minted                                                                                                                   | Idempotency cache keyed on the nonce       |
| Repeated request, new key, spent nonce         | Refused `ASSERTION_ALREADY_USED`                                                                                                                            | Spent-nonce set                            |
| Lost handoff artifact                          | The artifact is one-time; a new one is issued only against the same participation unit, and mints no second assertion unless a governed reissue is approved | Participation-unit ledger                  |
| Pickup consumed but page lost                  | The assertion is `picked_up` and cannot be picked up again; governed reissue before the cutoff                                                              | Pickup one-time state                      |
| Expired assertion                              | Refused `ASSERTION_EXPIRED`; a fresh assertion requires a fresh decision within the issuance window                                                         | Both ledgers                               |
| Credential issued, page lost before redemption | Remains `issued`, unredeemed; governed revoke-then-reissue before the cutoff                                                                                | Revoke-then-reissue, never issue-then-hope |
| Delivery uncertain                             | Same as above; there is no out-of-band delivery to fall back to, by design                                                                                  | Same                                       |
| Credential already redeemed                    | Refused `CREDENTIAL_ALREADY_REDEEMED`; no reissue, no recovery, no attempt to locate what it produced                                                       | Absorbing `redeemed` state                 |
| Concurrent requests                            | Serialized on the nonce; exactly one wins, the others receive the winner's outcome or a refusal                                                             | Atomic spent-marking                       |
| Retry after timeout                            | Idempotent; the client retries with the same key and learns the outcome                                                                                     | Idempotency cache                          |
| User reports loss                              | Dispute path (`F-P15-05`); reissue only before the cutoff, through the governed path                                                                        | Revoke-then-reissue                        |
| Manual operator retry                          | Permitted only through the governed reissue path with attribution and dual control; **never** an unattributed re-mint                                       | Same                                       |

Four obligations hold in every row: **exactly-once effect · safe idempotent
retry · no double credential · no identity leakage.**

### 7.1 The case this round refuses to solve

_Credential redeemed, participant reports they did not redeem it._
Resolving this by locating what the credential produced would require the
link the whole architecture forbids. It is handled as a **security incident
against the context** — the report is recorded, the integrity stream is
examined for replay and boundary-violation signals, and if the evidence
supports it the remedy is at context level (suspension, annulment, re-run)
under governance authority. The participant is told this plainly
(`PACK-15-CONTENT-CATALOGUE-DE.md` §5). **Trading the central guarantee for
one recovery is refused.**

---

## 8. Non-transferability, stated honestly

A credential is non-transferable **as far as is technically enforceable**.
The delivery boundary of §5 makes transfer materially harder than it was
before the correction — there is no value to email, screenshot, copy or
write down, because credential material never appears on any surface — but
nothing prevents a person from handing over their unlocked device mid-visit
or from being watched while they use it.

What is enforced: single use; context binding; audience binding; origin
binding to WS-03; short lifetime; no bearer semantics after redemption; no
persistence anywhere; and detection of the _patterns_ that mass transfer
produces (`T-P15-22`).

Coercion resistance and receipt-freeness are **not** provided by this round
and are named as PACK-16 obligations.
