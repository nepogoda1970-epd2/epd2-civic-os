# PACK-15 — Eligibility Assertion Matrix

**Round:** PACK-15 — specification and ADR only. **No code. Not implemented. Not a candidate. Not a PASS.**
**Repository version:** unchanged at `0.14.0` · **Canon version:** unchanged at `0.8.0`
**Baseline:** `EPD2_PACK-14_IDENTITY_AUTHENTICATION_ACCOUNT_SECURITY_0.14.0_FINAL_PASS.zip`
**Authoritative register:** `EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER_UPDATED_V6.md`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**
**Architecture correction applied (2026-07-31).**

The assertion is the only thing that crosses the trust boundary. This
document states what it contains, what it must not contain, what it is
bound to, **how it is queued and released**, how it is picked up and spent,
and how it dies.

**Corrected by this revision:** the queued-release lifecycle and its
governed defaults (`OD-P15-02`), the one-time pickup, the removal of the
context-scoped pseudonym from the assertion entirely (`OD-P15-03`), and the
Assertion Issuer's boundary (`OD-P15-01`).

---

## 1. Fields

| Field                        | Type                | Req | Rule                                                                                    |
| ---------------------------- | ------------------- | --- | --------------------------------------------------------------------------------------- |
| `EligibilityAssertionId`     | opaque              | R   | Random, non-derived; unique per assertion; never reused; not a subject identifier       |
| `VotingContextReference`     | context reference   | R   | Exactly one context                                                                     |
| `EligibilityResult`          | enum                | R   | `approved` only — a denial is never asserted across the boundary                        |
| `EligibilityClass`           | enum                | R   | The participation class the context defines                                             |
| `OrganizationalScope`        | scope reference     | R   | The context's scope, already matched at source                                          |
| `RequiredAssuranceSatisfied` | boolean             | R   | A boolean, never the method, the level history or the session                           |
| `IssuedAt`                   | timestamp           | R   | **Coarsened to `timestamp_granularity`** (§4)                                           |
| `ExpiresAt`                  | timestamp           | R   | Coarsened; never beyond `CredentialIssuanceWindow.end`                                  |
| `Audience`                   | audience identifier | R   | The Credential Issuer only                                                              |
| `Purpose`                    | enum                | R   | `voting_credential_issuance` and nothing else                                           |
| `Nonce`                      | opaque              | R   | One-time, context-scoped, randomly generated, **not derived from any participant data** |
| `Status`                     | enum                | R   | §5                                                                                      |

Twelve fields, a closed list. Adding a field is an amendment to ADR-091.

**`EligibilityResult` carries only `approved`.** There is no reason to
transmit a denial across the boundary: a denied participant obtains no
credential, and telling the voting side that someone was denied would give
it a fact about a person it has no business holding.

---

## 2. Required properties

| Property                     | Requirement                                                                            | Violation reason code           |
| ---------------------------- | -------------------------------------------------------------------------------------- | ------------------------------- |
| Minimized                    | Exactly the twelve fields above; no extension field, no vendor claim, no debug payload | —                               |
| Integrity-protected          | Signed through the Assertion Issuer's **own** key (§7)                                 | `ASSERTION_INVALID`             |
| Purpose-bound                | Usable only for credential issuance                                                    | `ASSERTION_PURPOSE_MISMATCH`    |
| Audience-bound               | Verifiable only by the Credential Issuer                                               | `ASSERTION_AUDIENCE_MISMATCH`   |
| Context-bound                | One voting context                                                                     | `ASSERTION_CONTEXT_MISMATCH`    |
| Short-lived                  | Expiry checked at pickup and at presentation                                           | `ASSERTION_EXPIRED`             |
| Replay-protected             | Nonce checked against the spent set, marked atomically                                 | `ASSERTION_ALREADY_USED`        |
| Pickup-once                  | The one-time pickup is consumed on first successful retrieval                          | `ASSERTION_PICKUP_ALREADY_USED` |
| Revocable before pickup      | Where the context's policy permits it                                                  | `ASSERTION_REVOKED`             |
| Not a general identity token | Authenticates nothing, authorizes nothing else                                         | `ASSERTION_PURPOSE_MISMATCH`    |
| Not cross-context            | Presenting it in another context is a refusal, never a partial match                   | `ASSERTION_CONTEXT_MISMATCH`    |

---

## 3. Prohibited content — normative

| Prohibited                                      | Note                                                                               |
| ----------------------------------------------- | ---------------------------------------------------------------------------------- |
| Account ID                                      | `FIR-INV-001`                                                                      |
| Person record ID                                | —                                                                                  |
| Membership ID                                   | —                                                                                  |
| Member number                                   | —                                                                                  |
| Email                                           | —                                                                                  |
| Phone                                           | —                                                                                  |
| Name                                            | —                                                                                  |
| Date of birth                                   | —                                                                                  |
| Address                                         | —                                                                                  |
| Communication persona                           | —                                                                                  |
| Eligibility evidence                            | Neither content nor reference                                                      |
| Raw reason history                              | The voting side has no use for why someone qualified                               |
| **Persistent cross-context subject identifier** | The single most dangerous field that could be added, and the easiest to justify    |
| **Context-scoped pseudonym**                    | **Added by the correction.** The pseudonym is identity-side only and never crosses |
| Precise issuance time                           | Coarsened; a microsecond timestamp is a correlation key                            |

**The prohibition is on derivability, not on field names.** A hash of the
member number is the member number. A per-member salt reused across
contexts is a persistent subject identifier in a costume. A "stable
anonymous ID for analytics" is a global user ID with a marketing
department. The implementation-stage test is not a field-name scan alone:
it must also demonstrate that no field is a function of participant data
that is stable across contexts.

---

## 4. Queued release — `OD-P15-02` closed

An approved decision does not produce an immediately available assertion.
The assertion is minted, **queued**, and released on a governed schedule,
so that the identity-side issuance moment and the voting-side minting
moment are not a matched pair.

### 4.1 Governed reference defaults

Normative values are `PACK-15-SPECIFICATION.md` §19.2 and are restated here
for the implementation and its tests. Every value is governed configuration
with a **hard lower bound**; a configuration outside its range is refused
with `VOTING_CONTEXT_CONFIGURATION_INVALID`, never clamped silently.

| Parameter                    | Default  | Permitted range     | Hard lower bound |
| ---------------------------- | -------- | ------------------- | ---------------- |
| `issuance_mode`              | `queued` | `queued` only       | —                |
| `timestamp_granularity`      | 300 s    | 60 s … 3600 s       | 60 s             |
| `release_delay_min`          | 30 s     | 10 s … 300 s        | 10 s             |
| `release_delay_max`          | 300 s    | ≥ 4 × min, ≤ 1800 s | 60 s             |
| `release_delay_distribution` | uniform  | uniform             | —                |
| `batch_interval`             | 120 s    | 60 s … 900 s        | 60 s             |
| `batch_max_size`             | 250      | 50 … 2000           | 50               |
| `minimum_cohort_size` (_k_)  | 5        | 3 … 50              | 3                |
| `cohort_wait_max`            | 3600 s   | 600 s … 21600 s     | 600 s            |
| `minting_delay_min`          | 5 s      | 2 s … 60 s          | 2 s              |
| `minting_delay_max`          | 30 s     | ≥ 3 × min, ≤ 300 s  | 10 s             |
| `small_electorate_threshold` | 50       | 20 … 200            | 20               |

### 4.2 Release rules

| #   | Rule                                                                                                                                             |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1   | **Immediate release is not a permitted mode.** `issuance_mode` has one value                                                                     |
| 2   | A batch is released when its interval closes **and** it holds at least _k_ assertions                                                            |
| 3   | Release time is drawn **uniformly** from `[release_delay_min, release_delay_max]` after the interval boundary — never a fixed offset             |
| 4   | **A cohort of one is never minted or released immediately.** It waits for further assertions                                                     |
| 5   | At `cohort_wait_max` the assertion is released regardless, within a further `release_delay_max` window                                           |
| 6   | Sub-_k_ release writes `IssuanceCohortThresholdNotMet` to `AS-04` with the cohort-size **class**, never the exact size                           |
| 7   | **Access is never denied for want of a cohort.** Disenfranchising a participant to protect their unlinkability is not an acceptable trade        |
| 8   | The queue must guarantee release ≥ `cohort_wait_max + release_delay_max` before `CredentialIssuanceWindow.end`; a profile that cannot is invalid |
| 9   | The "access available" notification follows the **release** schedule, not the decision schedule                                                  |

### 4.3 Small electorates

Where the eligible population is below `small_electorate_threshold`
(default 50): `k = max(3, ceil(0.1 × N))`; `timestamp_granularity` ≥ 3600 s;
issuance window ≥ 24 h; **no per-scope operational metric at all**;
aggregate counts published only after `voting_closed`; and context
activation requires an explicit governance acknowledgement that
unlinkability is correspondingly weaker.

**In a body of eleven people, no timing control makes participation
unlinkable to an observer who knows the eleven.** The controls reduce what
the _system_ discloses; they do not change what a small group knows about
itself.

---

## 5. Lifecycle

```text
minted ──queued──► queued ──release schedule──► released
                                                   │
                                    pickup (one-time, in WS-03)
                                                   ▼
                                              picked_up
                                                   │
                                 presented and verified (VC-04)
                                                   ▼
                                              redeemed
   ├──policy revocation (before pickup)──► revoked
   ├──expiry──────────────────────────────► expired
   └──second presentation or second pickup─► replay_rejected
```

| Transition                      | Actor                     | Atomicity                                            | Evidence stream |
| ------------------------------- | ------------------------- | ---------------------------------------------------- | --------------- |
| → `minted`                      | Assertion Issuer (VC-03)  | Single act, after decision approval                  | `AS-02`         |
| `minted` → `queued`             | Assertion Issuer          | Immediate; no assertion skips the queue              | `AS-02`         |
| `queued` → `released`           | Assertion Issuer          | On the batch schedule                                | `AS-02`         |
| `released` → `picked_up`        | Handoff Boundary (VC-05)  | **Atomic** with consuming the one-time pickup        | `AS-02`         |
| `picked_up` → `redeemed`        | Credential Issuer (VC-04) | **Atomic** with marking the nonce spent              | `AS-03`         |
| any → `revoked`                 | Assertion Issuer          | Before pickup only                                   | `AS-02`         |
| any → `expired`                 | Clock                     | Checked at pickup and at presentation, never assumed | `AS-02`         |
| `redeemed` → `replay_rejected`  | Credential Issuer         | On any further presentation                          | `AS-03`         |
| `picked_up` → `replay_rejected` | Handoff Boundary          | On any further pickup attempt                        | `AS-02`         |

**There is no partial spend.** An assertion is picked up once and spent
once, each in one atomic act.

---

## 6. What the two sides record — and what neither records

| Side                        | Records                                                                                                      | Never records                                       |
| --------------------------- | ------------------------------------------------------------------------------------------------------------ | --------------------------------------------------- |
| Assertion Issuer (identity) | That an assertion was minted, queued, released and picked up for this participation unit; its ID; its expiry | Any credential reference; the redemption outcome    |
| Handoff Boundary (identity) | That a pickup was consumed for a context                                                                     | The credential; the account that crossed            |
| Credential Issuer (voting)  | The nonce as **spent** — a set membership, not a mapping                                                     | The assertion ID beside the credential ID; identity |

This is the pairing prohibition made concrete. The Credential Issuer needs
to know _that_ a nonce was used; it never needs to know _what it produced_,
because the credential's own status already answers every operational
question the issuer has.

Idempotency is preserved without the pair: the idempotency key of an
issuance is derived from the assertion nonce, and the outcome cached
against that key is held for a **bounded, explicit and tested retry
window** and then discarded. Nothing outlives that window.

---

## 7. The Assertion Issuer's boundary — `OD-P15-01` closed

| Property                                                   | Requirement                                                                                                                                           |
| ---------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| Module boundary                                            | Separately bounded module inside the voting-trust service (`eligibility-service`)                                                                     |
| Storage boundary                                           | Own store; **no shared schema, transaction, connection pool or migration lineage** with VC-02                                                         |
| Access from VC-02                                          | Through the declared interface only; never directly into its tables                                                                                   |
| Signing key                                                | **Separate**; not held by, readable by or derivable from the eligibility decision store                                                               |
| Service credential                                         | **Separate** from the eligibility module's; one compromise does not yield the other                                                                   |
| Read access to account, person-record or membership stores | **Structurally impossible** — no import path, client, connection, credential or network route                                                         |
| Declared input                                             | Decision result, class, organizational scope, assurance-satisfied flag, context reference                                                             |
| Prohibited input                                           | Criteria inputs, reason history, evidence references, anything in the §3 prohibited set                                                               |
| Read access to `credential-service`                        | **None**                                                                                                                                              |
| Later extraction to a separate deployable                  | Possible **without a contract change**: transport-agnostic interface, no shared transaction, addressed by audience identity, storage already separate |

---

## 8. Timing controls, summarized

| Control                                      | Status after the correction                                            |
| -------------------------------------------- | ---------------------------------------------------------------------- |
| Coarsened `IssuedAt` / `ExpiresAt`           | **Specified**, default 300 s (≥ 3600 s for small electorates)          |
| Queued release with batching and cohort gate | **Specified**, §4                                                      |
| Randomized release delay                     | **Specified**, uniform over `[30 s, 300 s]` by default                 |
| No immediate minting for a cohort of one     | **Specified**, hard rule                                               |
| Randomized voting-side minting delay         | **Specified**, uniform over `[5 s, 30 s]` by default                   |
| Timing-class-only logging                    | **Specified**                                                          |
| Small-electorate policy                      | **Specified**, §4.3                                                    |
| Disclosure-control integration               | **Specified**, `disclosure_min_cell` = 5, joint over the published set |
| Network-boundary controls                    | PACK-17                                                                |

Timing correlation is **reduced and bounded, not eliminated**
(`T-P15-13`). A low-turnout context with a wide-open dashboard defeats
every control above, which is why operational metrics are treated as an
outcome-disclosure surface rather than as telemetry.
