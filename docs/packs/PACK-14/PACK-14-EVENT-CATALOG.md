# PACK-14 — Event Catalog

**Part A round:** PACK-14 — specification and ADR only. Retained unchanged; Part B below records the implementation candidate.
**Round:** PACK-14 — specification and ADR only. **No code. Not implemented. Not a candidate. Not a PASS.**
**Repository version:** unchanged at `0.13.0` · **Canon version:** unchanged at `0.8.0`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**
**Architecture correction applied (2026-07-30).**

Every event uses **PACK-13's canonical envelope unchanged** (canon §21):
`event_id`, `event_type`, `event_version`, `occurred_at`, `producer`,
`actor`, `subject`, `correlation_id`, `causation_id`, `payload`,
`integrity`. No transport metadata is added to the envelope; PACK-13's
ADR-071 keeps that boundary and PACK-14 does not move it.

## 1. Payload rules that apply to every family below

1. **No global identifier appears in any payload.** Subjects and actors
   carry purpose-scoped references, not raw `account_id` outside the
   account contexts (ADR-079).
2. **No secret material.** No password, OTP value, recovery code value,
   private key or full WebAuthn assertion — ever, in any field.
3. **No raw contact details** where a tokenized reference suffices.
4. **No identity document content.**
5. **No voting material of any kind.**
6. Every failure-shaped event carries a **registered reason code**.
7. Payloads are minimal: an event says what happened, not everything known.

## 2. Account family

| Event                             | Subject | Notable payload                                                                                                                          |
| --------------------------------- | ------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `account.created`                 | account | account status, creation channel                                                                                                         |
| `account.activated`               | account | activating condition                                                                                                                     |
| `account.restricted`              | account | restriction class, reason code, authority, expiry                                                                                        |
| `account.locked`                  | account | **`AccountLock` reference**, cause, expiry, unlock condition, reason code. The account's `AccountStatus` does **not** change (OD-P14-01) |
| `account.unlocked`                | account | `AccountLock` reference, reason code, authority                                                                                          |
| `account.closure_requested`       | account | requested at, cooling-off end                                                                                                            |
| `account.closed`                  | account | reason code, retention class applied                                                                                                     |
| `account.anonymization_completed` | account | what was retained and why                                                                                                                |

## 3. Contact family

| Event                            | Notable payload                                    |
| -------------------------------- | -------------------------------------------------- |
| `contact.added`                  | channel class, tokenized channel reference         |
| `contact.verification_requested` | channel class                                      |
| `contact.verified`               | channel class, verified at                         |
| `contact.changed`                | channel class, notified-old and notified-new flags |
| `contact.removed`                | channel class, reason code                         |

## 4. Credential family

| Event                               | Notable payload                                                    |
| ----------------------------------- | ------------------------------------------------------------------ |
| `credential.enrolled`               | credential type, device-bound or synced, nickname, backup eligible |
| `credential.verified`               | credential reference, method class                                 |
| `credential.revoked`                | credential reference, reason code, actor class                     |
| `credential.passkey_added`          | authenticator metadata class, attestation state                    |
| `credential.passkey_removed`        | remaining credential count, recovery path present                  |
| `credential.mfa_enrolled`           | factor class                                                       |
| `credential.mfa_removed`            | factor class, resulting assurance                                  |
| `credential.recovery_codes_issued`  | set reference, code count                                          |
| `credential.recovery_codes_revoked` | set reference, reason code                                         |

## 5. Authentication family

| Event                                | Notable payload                                           |
| ------------------------------------ | --------------------------------------------------------- |
| `authentication.started`             | method class, workspace scope                             |
| `authentication.succeeded`           | method class, assurance achieved, freshness               |
| `authentication.failed`              | reason code, attempt counter class                        |
| `authentication.step_up_requested`   | action code, required assurance, object version reference |
| `authentication.step_up_succeeded`   | action code, achieved assurance, object version reference |
| `authentication.step_up_failed`      | action code, reason code                                  |
| `authentication.suspicious_detected` | signal category, weight, response taken, reason code      |

## 6. Session family

| Event                       | Notable payload                            |
| --------------------------- | ------------------------------------------ |
| `session.issued`            | workspace scope, assurance, both deadlines |
| `session.rotated`           | rotation trigger                           |
| `session.assurance_changed` | from, to, trigger, reason code             |
| `session.revoked`           | reason code, actor class                   |
| `session.all_revoked`       | reason code, count, actor class            |
| `session.replay_detected`   | family reference, reason code              |

## 7. Recovery family

| Event                           | Notable payload                                             |
| ------------------------------- | ----------------------------------------------------------- |
| `recovery.requested`            | entry channel class                                         |
| `recovery.assessment_completed` | risk classification, named signals, reason code             |
| `recovery.cooling_off_started`  | window end, notification channels used                      |
| `recovery.approved`             | reviewer role, separation-of-duties evidence                |
| `recovery.rejected`             | reason code, appeal path reference                          |
| `recovery.completed`            | credentials revoked, sessions revoked, new credential class |
| `recovery.disputed`             | dispute reference, reason code                              |

## 8. Identity proofing family

| Event                             | Notable payload                                 |
| --------------------------------- | ----------------------------------------------- |
| `proofing.started`                | method, requested assurance                     |
| `proofing.evidence_received`      | evidence reference (PACK-11), never the content |
| `proofing.verified`               | assurance achieved, deciding authority          |
| `proofing.rejected`               | reason code, appeal path                        |
| `proofing.manual_review_required` | trigger, reason code                            |

## 9. Voting handoff

| Event                     | Notable payload                                         |
| ------------------------- | ------------------------------------------------------- |
| `voting_handoff.issued`   | purpose scope, expiry. **No identity of any kind**      |
| `voting_handoff.redeemed` | redemption time. No linkage back to the issuing account |
| `voting_handoff.refused`  | reason code (`VOTING_HANDOFF_ALREADY_USED` or invalid)  |

The issuance and redemption records must not, jointly or separately,
permit resolving a redemption back to the account that obtained it
(ADR-088).

## 10. Audit classifications

Following the pattern PACK-13 established, each event above has a
corresponding `*_RECORDED` audit classification derived mechanically from
its type. The implementation round registers them; this round names the
rule rather than pre-generating a list it cannot yet verify.

---

# Part A ends here.

# Part B — implementation record (PACK-14 candidate, repository `0.14.0`)

Part A above is the accepted specification round's own text, retained
**unchanged**, including its round header. It is the record of that
round and is deliberately not rewritten to read as though it had always
been an implementation - the discipline PACK-13's FINAL PASS round
applied to its own candidate report.

Everything below records what the implementation candidate actually
built.

## B.0 What the implementation emits

59 event types in nine families, all on **PACK-13's canonical envelope,
unchanged** (canon §21). PACK-14 adds no envelope field, removes none and
reinterprets none.

## 1. The families

| Family                   | Prefix                      | Types |
| ------------------------ | --------------------------- | ----- |
| Account                  | `account.`                  | 11    |
| Contact                  | `contact.`                  | 5     |
| Credential               | `credential.`               | 10    |
| Authentication           | `authentication.`           | 7     |
| Session                  | `session.`                  | 7     |
| Recovery                 | `recovery.`                 | 8     |
| Proofing                 | `proofing.`                 | 5     |
| Authentication bootstrap | `authentication_bootstrap.` | 3     |
| Voting handoff           | `voting_handoff.`           | 3     |

Names carry the **aggregate prefix**, never a service or pack prefix —
`account.created`, never `pack14.account_created` (PACK-13's
`P13-EVT-002`).

## 2. The seven payload rules

1. No global identifier — subjects and actors carry purpose-scoped
   references.
2. No secret material — no password, OTP, recovery code, private key or
   full WebAuthn assertion, in any field.
3. No raw contact details where a tokenized reference suffices.
4. No identity document content.
5. No voting material of any kind.
6. Every failure-shaped event carries a registered reason code.
7. Payloads are minimal.

**The first five are enforced, not described.** Every assembled payload
passes `reject_prohibited_payload_keys` before an envelope exists, and a
test constructs all 59 event types with a secret in the payload and
asserts that every one of them refuses.

Rule 6 is enforced by `REQUIRES_REASON_CODE`: 22 adverse-outcome event
types cannot be built without one.

## 3. Three payloads worth reading closely

**`account.locked`** carries the account's `account_status`
**unchanged**, plus a lock reference, a cause, an expiry and a reason
code. A consumer learns about a lock and sees that the account is still
whatever it was — OD-P14-01, visible on the wire.

**`recovery.assessment_completed`** carries `named_signals` and
`reviewer_role`. There is no `risk_score` field and no reviewer
identifier: an oversight body can see that the control held without every
consumer of the stream learning who the reviewer was.

**`voting_handoff.issued`** carries exactly three keys — purpose, voting
context and expiry. A test asserts the key set is exactly that.

## 4. `PUBLIC_PROJECTION_ALLOWED` is empty

Not one event here describes public information: every one is about a
specific person's account security. An empty allow-set is the honest
answer rather than an oversight, and PACK-13's `P13-EVT-004` set the
precedent for saying so explicitly.

## 5. The `*_RECORDED` classifications

Canon §24 is refusal-only, and an act that succeeds still needs a
registered classification for its audit row. There is exactly one per
event type, derived mechanically by `recorded_reason_code_for`, so
`contracts/reason-codes/pack-14.yml` and this catalogue cannot drift.

## 6. Actor projection

`to_actor_ref` folds the purpose and the domain owner into `actor_type`
rather than dropping them, because the envelope has no purpose field and
a bare actor identifier would be exactly the unscoped reference ADR-079
forbids. `actor_id` is derived from the scoped reference digest:
deterministic within one purpose, and unrelatable to the same account's
reference for any other.
