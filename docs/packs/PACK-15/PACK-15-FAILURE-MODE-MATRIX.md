# PACK-15 — Failure Mode Matrix

**Round:** PACK-15 — specification and ADR only. **No code. Not implemented. Not a candidate. Not a PASS.**
**Repository version:** unchanged at `0.14.0` · **Canon version:** unchanged at `0.8.0`
**Baseline:** `EPD2_PACK-14_IDENTITY_AUTHENTICATION_ACCOUNT_SECURITY_0.14.0_FINAL_PASS.zip`
**Authoritative register:** `EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER_UPDATED_V6.md`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**
**Architecture correction applied (2026-07-31).**

**The governing principle: fail closed wherever failing open would produce
a wrong participation, and fail visibly always.** A participant who
silently receives nothing has been disenfranchised by a timeout, which is
indistinguishable from being disenfranchised on purpose.

---

## 1. Dependency failures

| #       | Failure                               | Behaviour                                      | Retry                           | Manual path                    | User-visible status                               | Evidence             | Recovery                                                  |
| ------- | ------------------------------------- | ---------------------------------------------- | ------------------------------- | ------------------------------ | ------------------------------------------------- | -------------------- | --------------------------------------------------------- |
| `FM-01` | Membership source unavailable         | **fail-closed**                                | Bounded, backoff                | Assisted eligibility review    | „Prüfung derzeit nicht möglich", with a next step | `AS-01` + `AS-06`    | Resume; extend the issuance window if the outage spans it |
| `FM-02` | Eligibility rule registry unavailable | **fail-closed**                                | Bounded                         | None — no rule, no decision    | Same                                              | `AS-01`              | Resume                                                    |
| `FM-03` | Stale source data                     | **fail-closed** if outside the freshness bound | None                            | Manual review                  | „Angaben veraltet", with the next step            | `AS-01`              | Re-evaluate on refresh                                    |
| `FM-04` | Identity service unavailable          | **fail-closed**                                | Bounded                         | Assisted channel               | „Anmeldung derzeit nicht möglich"                 | `AS-06`              | Resume                                                    |
| `FM-05` | Credential issuer unavailable         | **fail-closed**                                | Idempotent retry on the nonce   | Deferred issuance queue        | „Ausgabe verzögert", with the retry statement     | `AS-03` + `AS-06`    | The assertion remains unspent and valid until expiry      |
| `FM-06` | Assertion signer unavailable          | **fail-closed**                                | Bounded                         | Deferred issuance              | Same                                              | `AS-02`              | Resume; no assertion is issued unsigned                   |
| `FM-07` | Clock skew beyond tolerance           | **fail-closed**                                | None                            | Operator escalation            | „Zeitprüfung fehlgeschlagen"                      | `AS-06`              | Fix time sync; windows are re-checked, never assumed      |
| `FM-08` | Duplicate request                     | idempotent                                     | Same key → same outcome         | None needed                    | The original outcome                              | `AS-03`              | —                                                         |
| `FM-09` | Database partial failure              | **fail-closed**                                | Transactional; no partial write | Operator escalation            | „Vorgang nicht abgeschlossen"                     | `AS-06`              | A half-issued credential must not exist                   |
| `FM-10` | Audit service unavailable             | **fail-closed** for every consequential act    | Bounded                         | Operator escalation            | „Aus Sicherheitsgründen nicht ausgeführt"         | Local durable buffer | **No unlogged issuance, revocation or redemption**        |
| `FM-11` | Notification failure                  | proceed, record                                | Bounded                         | Alternative channel            | Status visible in the workspace regardless        | `AS-06`              | Delivery evidence is `FIR-DELIVERY-001`'s round           |
| `FM-12` | Handoff timeout                       | refuse                                         | New handoff required            | Assisted channel               | „Übergang abgelaufen", with a restart action      | `AS-06`              | Start again; nothing was consumed                         |
| `FM-13` | Credential redemption timeout         | **fail-closed**, idempotent                    | Same request → same outcome     | Deferred                       | „Einlösung nicht bestätigt", with a retry action  | `AS-03`              | Atomic redemption means either it happened or it did not  |
| `FM-14` | Replay store unavailable              | **fail-closed**                                | Bounded                         | None — never bypassed          | „Prüfung nicht möglich"                           | `AS-03` + `AS-06`    | **Never issue without the spent-set check**               |
| `FM-15` | Operator review unavailable           | wait + escalate                                | n/a                             | Escalation path                | „In Prüfung", with the escalation stated          | `AS-01`              | Never auto-approve, never auto-deny                       |
| `FM-16` | Voting origin unavailable             | refuse                                         | Client retry                    | Assisted / alternative channel | „Wahlbereich derzeit nicht erreichbar"            | `AS-06`              | Context-level extension if it spans the window            |
| `FM-17` | Key service unavailable               | **fail-closed**                                | Bounded                         | Operator escalation            | „Vorgang derzeit nicht möglich"                   | `AS-06`              | No unsigned assertion, no unverified credential           |

---

## 2. The rule behind `FM-10` and `FM-14`

Two dependencies are never bypassed, under any load, for any reason, with
any flag: **the audit stream and the replay store.**

- An issuance without audit evidence is an issuance nobody can account
  for, in the one domain where accounting for it is the entire point.
- An issuance without the spent-set check is a double credential, which is
  a double vote.

`FIR-INV-006` applies directly: no feature flag may disable either.

---

## 3. Failure modes that require a context-level decision

Fail-closed protects correctness and can, at scale, disenfranchise. Where a
dependency is down for a large part of the issuance or voting window, the
answer is **not** to relax a control automatically.

| Situation                                                 | Governed remedy                                      | Authority                                        | Evidence                        |
| --------------------------------------------------------- | ---------------------------------------------------- | ------------------------------------------------ | ------------------------------- |
| Outage spanning a significant part of the issuance window | Extend the issuance window                           | Voting Operations Officer + Governance           | Context change record           |
| Outage spanning a significant part of the voting window   | Extend the voting window                             | Governance                                       | Context change record           |
| Outage making the context unusable                        | Suspend, then re-run                                 | Governance                                       | Suspension + announcement       |
| Systematic wrong denials discovered mid-window            | Suspend issuance; correct; re-open with an extension | Governance + Eligibility Officer                 | Both, plus auditor notification |
| Integrity violation detected                              | Suspend the context immediately                      | Security Auditor may trigger; Governance decides | `AS-04`                         |

Every one of these is announced. A window extended quietly is a window
extended for whoever noticed.

---

## 4. What must never happen on failure

| Prohibited failure behaviour                                       | Why                                                       |
| ------------------------------------------------------------------ | --------------------------------------------------------- |
| Auto-approving eligibility because a source is down                | The electorate becomes whoever asked during the outage    |
| Auto-denying eligibility because a source is down                  | Silent disenfranchisement                                 |
| Issuing a credential without the spent-set check                   | Double participation                                      |
| Issuing a credential without audit evidence                        | Unaccountable issuance                                    |
| Retrying an issuance with a fresh nonce after an ambiguous failure | Double credential                                         |
| Falling back to a shared session for WS-03 during an outage        | The isolation is not conditional on the weather           |
| Logging identifiers "temporarily, for the incident"                | The classic breach                                        |
| Enabling a cross-boundary trace to debug an outage                 | Same                                                      |
| Reporting a failure without a reason code                          | The participant cannot act, and the auditor cannot review |
| Failing silently                                                   | Indistinguishable from targeted denial                    |

---

## 5. User-visible status on failure

Every failure produces a statement with three parts: **what happened**, in
plain German; **what it means for the participant**; and **what they can do
next**, including the dispute path where nothing else is available. The
governed texts are `PACK-15-CONTENT-CATALOGUE-DE.md` §9.

A failure message that names no next step is not an acceptable message in
this system, and a failure that produces no message is not an acceptable
failure.

---

## 6. Failure modes added by the architecture correction (2026-07-31)

| #       | Failure                                         | Behaviour                                             | Retry            | Manual path         | User-visible status                                  | Evidence          | Recovery                                                                                                                                                                |
| ------- | ----------------------------------------------- | ----------------------------------------------------- | ---------------- | ------------------- | ---------------------------------------------------- | ----------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `FM-18` | Issuance queue or release scheduler unavailable | **fail-closed for release**, assertions stay `queued` | Bounded, backoff | Operator escalation | „Zugang wird vorbereitet" — access is being prepared | `AS-02` + `AS-06` | On recovery the queue drains under the same cohort and delay rules; if the outage threatens the window guarantee, the context window is extended by a governed decision |

### 6.1 Behaviour changes to existing modes

| #       | Change                                                                                                                                                                                                       |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `FM-05` | Credential issuer unavailable: the participant is inside WS-03, so the visible state is a waiting state with a retry action, not a background queue. The assertion remains `picked_up` and its nonce unspent |
| `FM-13` | Redemption timeout: because issuance and redemption are one visit, an ambiguous redemption leaves the credential `issued`; the retry is idempotent and no second credential can arise                        |
| `FM-16` | Voting origin unavailable: **the only path to a credential**, so a prolonged outage is a context-level decision (window extension) rather than an inconvenience                                              |

### 6.2 The rule the correction adds

**A dependency failure may never be resolved by delivering credential
material through another channel.** There is no fallback delivery, by
design: email, SMS, file, print and operator handover are prohibited
regardless of the operational pressure. Where the isolated origin cannot
serve a participant, the remedy is a governed window extension or re-run,
never an out-of-band credential.

**And: a timing control may never be disabled to recover throughput.** The
queue, the cohort gate and the delays are not performance settings. Under
load the queue lengthens; it does not open.
