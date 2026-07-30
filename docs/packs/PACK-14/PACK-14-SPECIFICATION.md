# PACK-14 — Identity, Authentication & Account Security

**Round type:** specification and ADR only. **No code. Not implemented. Not a candidate. Not a PASS.**

**Architecture correction applied (2026-07-30).** Ten implementation-blocking
open decisions are resolved in this revision — account lifecycle
representation, bounded-context ownership, password fallback, session and
freshness defaults, the session model's status, cross-origin authentication
bootstrap, the voting handoff boundary, passkey attestation, SMS OTP, and
recovery assurance. §31 lists them. No architecture decision already
accepted was reversed; ADR-079 … ADR-088 keep their decisions.

**Target version:** `0.14.0` — a target, not a setting. This round changes
no version. `REPOSITORY_VERSION` remains `0.13.0` and `CANON_VERSION`
remains `0.8.0`.

**Baseline:** `EPD2_PACK-13_PRODUCTION_DATA_PLANE_CONTRACT_EVOLUTION_0.13.0_FINAL_PASS.zip`
(PACK-01 through PACK-13: FINAL PASS).

**Register entry:** `FIR-ROADMAP-004`.

**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**

---

## 0. What this round is, and the one thing it must not become

Thirteen packs have been careful never to know who anyone is. PACK-14 is
the round that has to answer the question directly — who is operating this
session, by what method, with what confidence, and how do they get back in
when they lose the device — and it is therefore the round in which the
system's central guarantee is easiest to lose.

The guarantee is `FIR-INV-001`: **no global user ID**. It has survived
thirteen packs because none of them needed one. PACK-14 needs an identifier
for authentication, and the moment that identifier exists, every downstream
domain has a reason to store it. One `account_id` column added to a
membership table, a finance record and an event payload, and the
correlation the architecture was built to prevent exists — not as a
policy failure, but as an ordinary schema convenience nobody objected to.

So the governing rule of this pack is the mirror of PACK-13's:

> **Authentication establishes who is operating a session. It does not
> establish who a person is, what they are entitled to, or what they have
> agreed to.**

Everything in this specification follows from taking that seriously.

This round produces documents. It produces no service, no module, no test,
no migration, no CI change and no version change. `services/` is untouched.

---

## 1. Scope

PACK-14 specifies the architecture of:

1. account identity;
2. authentication;
3. session security;
4. assurance levels;
5. step-up authentication;
6. account lifecycle;
7. credential lifecycle;
8. account recovery;
9. the identity proofing boundary;
10. account takeover protection;
11. privileged identity administration;
12. cross-workspace session boundaries;
13. privacy-preserving identity references;
14. forms and official receipts;
15. the minimum frontend interaction contract.

### 1.1 Out of scope, explicitly

No production IAM. No passkey provider, email provider or SMS provider is
selected. No eID or government identity provider is selected. No
authentication service is created. No voting credential, eligibility
determination, ballot, tally or cryptographic voting protocol
(PACK-15/16). No electronic-signature layer (`FIR-TRUST-001`). No mandate
or representation model (`FIR-REPRESENT-001`). No full FRONT-PACK.

## 2. Relationship to the existing canon and to existing services

PACK-14 is bound by what already exists and does not restate it in
different words, because a restated contract can disagree with the
original.

| Canon / service                                                            | What it already fixes                                                                                                                                | What PACK-14 does                                               |
| -------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| Canon 7.2 `Account`, owner Account Service                                 | `account_id`, `email_status`, `mfa_status`, `account_status` and six statuses                                                                        | Extends operationally; redefines nothing                        |
| Canon 7.3 / 19d.2 `IdentityRecord`, owner Identity Verification            | Ten original plus eight added fields; `identity_assurance_level` on `none`/`low`/`substantial`/`high`; verification is never a proxy for citizenship | Reuses the scale; adds the proofing **case** around it          |
| Canon 19d.8 `AuthenticationContext`, owner `identity-service`              | Five never-interchangeable concepts; `authentication_assurance_level` on the same four values                                                        | Reuses both; adds session, credential and recovery models       |
| Canon 19d.8 `StepUpAuthenticationRequirement`, owner `eligibility-service` | Step-up **policy**, evaluated fail-closed as a conjunction with no "or"                                                                              | Reuses it as the policy source; adds action and version binding |
| Canon 19d.9 `MembershipApplication`                                        | Two-stage admission with a mandatory human decision                                                                                                  | Adds no path around it                                          |
| PACK-12 `privileged-access-service`                                        | JIT grants, break-glass, separation of duties, audit-before-event                                                                                    | Reuses it; defines no new privileged mechanism                  |
| PACK-13 data plane                                                         | Canonical envelope, outbox, projections, `GLOBAL_IDENTITY_KEYS` prohibition                                                                          | Uses the envelope unchanged; adds no prohibited key             |
| PACK-11 governed documents                                                 | Evidence bundles, custody, immutable versions                                                                                                        | Uses them for proofing and recovery evidence                    |
| PACK-09 retention                                                          | Retention schedules, legal hold, destruction authorization                                                                                           | Binds every identity record class to a schedule                 |
| FRONT-00 workspaces                                                        | WS-01…WS-10, `sessionSharing: forbidden`, WS-03's isolation policy                                                                                   | Issues sessions that honour every declaration                   |

**A consequence worth stating plainly:** PACK-14 reuses canon's four-value
assurance scale rather than inventing an AAL-0…AAL-3 vocabulary of its own.
Section 6 gives the mapping. This is the single largest reason the canon
assessment concludes that no amendment is required.

## 3. Identity layers

Five identifier spaces, normatively distinct (ADR-079, ADR-080).

### 3.1 Account identity — `account_id`

A technical record for authentication and session management. It is **not**
a person, a membership, a public number, a voting identity or a
communication identity. It is not an integration key: no domain outside the
Account Registry receives it.

### 3.2 Protected person record — `person_record_id`

Exists only where identity proofing requires it. Domain-controlled,
protected, purpose-limited, unavailable as a general integration key, and
**optional** — many accounts never acquire one, and none acquires one by
default.

### 3.3 Membership identity — `membership_id`, `member_number`

Separate from both. `member_number` may be a visible organizational number
on organizational documents. It is **not** a login identifier and **not** a
cross-domain correlation key.

### 3.4 Applicant identity

An applicant holds an application-scoped reference and **never** receives
membership identity automatically. Canon 19d.9's two stages are unchanged.

### 3.5 Communication persona — `communication_persona_id`

For permitted internal communication only. Never an authentication subject,
never an input to a membership decision, never a voting linkage.

### 3.6 Scoped actor reference

Domains and events carry a **purpose-scoped actor reference** — derived per
purpose, per organizational scope and per domain owner — not a raw
`account_id`. This is what makes the absence of a global identifier
structural rather than aspirational.

### 3.7 Voting credential

A separate identity space, owned by PACK-15/16, **not implemented and not
specified here** beyond the handoff boundary in section 11 (ADR-088).

## 4. Bounded contexts

| Context                       | Responsibility                                                                                                                                                  |
| ----------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Account Registry              | Account identity, status, contact login handles, allowed authentication methods, lifecycle, restrictions, account security metadata                             |
| Authentication                | Credential verification, passkeys, password fallback where permitted, magic link, MFA, outcome, assurance, failed attempts, risk signals                        |
| Session Security              | Issuance, rotation, idle and absolute timeout, device and session inventory, revoke one, revoke all, assurance freshness, suspicious session handling           |
| Identity Proofing Boundary    | Declared identity, verification methods, evidence, assurance, manual review, external provider boundary — and **not** a general person database                 |
| Recovery and Credential Reset | Recovery request, risk assessment, cooling-off, alternate verification, out-of-band notification, credential replacement, session revocation, evidence, dispute |
| Identity Administration       | Account restriction, recovery support, credential revocation, suspicious-activity review, privileged reset, break-glass, separation of duties                   |

### 4.1 Ownership — decided

**`identity-service` owns all six contexts.** It is already canon 19d.8's
owner of `AuthenticationContext`, and splitting authentication away from the
service that owns the authentication context would put the two halves of one
decision in two places.

Owned by `identity-service`:

| Context                      | Module boundary  | Storage boundary                                            |
| ---------------------------- | ---------------- | ----------------------------------------------------------- |
| Account Registry             | `accounts`       | account, contact, lock, restriction, closure-request stores |
| Credential Registry          | `credentials`    | credential and factor stores                                |
| Authentication               | `authentication` | attempt, challenge, risk stores                             |
| Session Security             | `sessions`       | session and device stores                                   |
| Recovery coordination        | `recovery`       | recovery case and evidence stores                           |
| Identity-proofing references | `proofing`       | proofing case store; evidence stays in PACK-11              |

Binding rules:

1. **No parallel authentication service is created.** One owner, one audit
   path, one place where an authentication decision is made.
2. The six are **internally separated modules with separate storage
   boundaries**. A module reaches another module's store through that
   module's own interface, never directly — the same discipline PACK-13's
   ADR-070 applies between domains, applied here between modules.
3. Ownership of `Account` (canon 7.2, Account Service) and `IdentityRecord`
   (canon 7.3/19d.2, Identity Verification Service) is **unchanged**.
   PACK-14 adds the registry, credential, session and recovery models around
   them; it does not move a canonical aggregate to a new owner.

This closes **OD-P14-02**.

## 5. Authentication methods

Preferred: **passkeys / WebAuthn** (ADR-081).

Controlled alternatives, each with an explicit assurance class rather than
an assumption of equivalence: password with MFA; magic link; recovery code;
verified-device assisted login; federated identity provider; eID-mediated
login; in-person assisted recovery.

No production provider is selected for any of them.
`PACK-14-AUTHENTICATION-METHOD-MATRIX.md` records, per method: assurance
class, phishing resistance, replay resistance, device binding, recovery
impact, fallback, allowed actions, step-up eligibility, revocation and
audit evidence.

### 5.1 Passkeys

Multiple passkeys per account are expected and encouraged. Each credential
records nickname, `created_at`, `last_used_at`, authenticator metadata,
attestation state, backup eligibility, and whether it is device-bound or
synced. Discoverable and non-discoverable credentials are both considered.

Two rules exist because their opposites are common and wrong:

- **Attestation is not required universally.** Where required, it is
  required by a named risk assessment for a named action class.
- **A synced passkey is not automatically a hardware-grade credential.**
  Treating it as one silently promotes the syncing cloud account into the
  real authenticator.

**Attestation — decided (closes OD-P14-08).**

| Rule                                                                               | Consequence                                                                                           |
| ---------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| **No universal attestation requirement**                                           | An ordinary member with a platform authenticator is never excluded                                    |
| **A synced passkey reaches at most `substantial`** in the reference model          | The syncing cloud account is part of its trust chain, and that account is not this system's to assess |
| **`high` requires a device-bound credential**, or a separately approved equivalent | Named per action class, not assumed                                                                   |
| **Hardware attestation only for specifically governed privileged action classes**  | Each such class names the risk assessment that requires it                                            |
| **No member is excluded from ordinary participation for lack of attestation**      | `FIR-INCLUSION-001`; exclusion by hardware is exclusion                                               |

Compromised-device response, lost-device recovery and credential revocation
are specified in the recovery control matrix.

### 5.2 Password fallback — decided

**The reference implementation supports controlled password fallback.**
Excluding passwords entirely would have been the cleaner security story and
the worse inclusion outcome: it makes participation depend on owning a
passkey-capable device, which is not a condition a party may place on its
members. The fallback therefore exists and is fenced.

| Rule                                                                                                                 | Why                                                                          |
| -------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| **Passkeys remain preferred** and are offered first everywhere                                                       | ADR-081 is unchanged                                                         |
| **No new password-only account may be created**                                                                      | A password account is a fallback for someone who has one, not a default path |
| **A password never authorizes a consequential action alone**                                                         | It is phishable by construction                                              |
| **Password login always requires MFA**                                                                               | Single-factor password authentication does not exist in this system          |
| **Password login can be disabled through governed configuration**, globally, per organizational scope or per account | An organization that can require passkeys should be able to                  |
| Storage uses a modern memory-hard hash; no plaintext, no reversible form                                             | Non-negotiable                                                               |
| Rate limiting applies; a breached-password checking boundary is defined                                              | Credential stuffing and spraying                                             |
| **No security questions**, ever                                                                                      | The answers are campaign material for candidates                             |
| No forced periodic rotation without a risk reason                                                                    | Rotation without cause produces weaker passwords                             |
| Compromise revokes the credential and its sessions                                                                   | —                                                                            |
| Recovery is separated from password reset                                                                            | ADR-085                                                                      |

Maximum assurance reachable with password + MFA is **`substantial`**. It
never reaches `high`, so it never satisfies a `high` action on its own.

This closes **OD-P14-03**.

### 5.3 MFA

Classes: passkey as a single phishing-resistant factor; TOTP; hardware
security key; recovery code; email OTP for channel verification;
provider-based MFA.

For each factor the specification defines enrollment, confirmation, removal,
replacement, recovery, factor inventory, factor loss, factor compromise,
administrative reset and the assurance downgrade each implies.

### 5.4 SMS OTP — decided

**SMS OTP is not an authentication method and not a step-up factor.**

| Rule                                                                                                       |
| ---------------------------------------------------------------------------------------------------------- |
| **SMS OTP is not a login method.** No authentication ceremony accepts it                                   |
| **SMS OTP is not an authentication step-up factor.** It cannot satisfy any assurance requirement           |
| It may **verify the phone channel itself** — proving control of a number, which is what it actually proves |
| It may contribute as a **low-weight signal in recovery**, never as the deciding evidence                   |
| **It grants no authentication assurance by itself.** It carries no AAL                                     |
| **The system must operate with no SMS provider at all.** Every flow has a path that does not involve one   |

SIM swap is a named threat (T-25) and the control is structural: an attacker
who takes over a phone number gains a verified channel and no authentication.
Any mapping that assigned SMS OTP an assurance level has been removed from
the method and assurance matrices.

This closes **OD-P14-09**.

## 6. Assurance levels

PACK-14 uses **canon's existing four-value scale** (canon 19d.2, 19d.8).

| Informal | Canon value   | Meaning                                                       |
| -------- | ------------- | ------------------------------------------------------------- |
| AAL-0    | `none`        | Unauthenticated                                               |
| AAL-1    | `low`         | Single non-phishing-resistant factor                          |
| AAL-2    | `substantial` | Multi-factor, or single factor with compensating controls     |
| AAL-3    | `high`        | Phishing-resistant, origin-bound, device-bound where required |

`PACK-14-ASSURANCE-LEVEL-MATRIX.md` records per level: permitted methods,
freshness, maximum session age, device and risk requirements, allowed
actions, reauthentication triggers and downgrade conditions — and maps
example actions (reading a dashboard, changing an email, adding a passkey,
submitting an application, approving finance, performing a privileged
action, voting handoff) onto required levels.

**One login is never sufficient for all actions**, and the matrix is the
place that says so per action rather than in general.

## 7. Step-up authentication

Step-up is bound to a **specific consequential action** and to a **specific
object version** (ADR-082). The specification defines: trigger, required
assurance, freshness window, risk escalation, transaction binding,
object/version binding, cancellation, timeout, failed step-up, fallback and
receipt.

**If the object changes, the confirmation is void.** A step-up obtained
against version _n_ does not authorise version _n+1_. This is the rule that
prevents an approval being harvested for one thing and spent on another.

Evaluation is fail-closed, exactly as canon 19d.8 requires: every
applicable condition must hold simultaneously; no "or" is permitted; a
missing, expired or unresolvable authentication context is a refusal.

## 8. Session model

**`SessionRecord` is a PACK-14 service-level aggregate. It is not added to
canon, and its events use PACK-13's canonical envelope unchanged.** The
precedent is PACK-12's `PrivilegedSession`, which is likewise a pack-level
aggregate: a session is an operational fact about a running system, not a
governed institutional record of the kind canon holds. This closes
**OD-P14-05**.

Minimum models: `SessionId`, `SessionRecord`, `SessionAssurance`,
`SessionStatus`, `SessionOrigin`, `SessionScope`, `SessionIssuedAt`,
`SessionExpiresAt`, `SessionIdleDeadline`, `SessionAbsoluteDeadline`,
`SessionLastActivity`, `SessionRevocation`, `SessionRiskState`,
`StepUpReference`, `DeviceReference`.

Mandatory rules (ADR-083), each recorded with its acceptance criterion in
`PACK-14-SESSION-SECURITY-MATRIX.md`:

- rotation after authentication and after any privilege change;
- idle timeout **and** absolute timeout; no infinite session;
- revoke one session; revoke all sessions;
- a compromised credential invalidates the sessions it could have produced;
- a revoked session cannot silently refresh;
- refresh-token rotation where refresh tokens are used, with **reuse
  treated as replay** — revoke the family, raise a security event;
- no session identifier in a URL;
- `Secure`, `HttpOnly` and appropriate `SameSite` cookie attributes;
- a CSRF strategy for every state-changing request;
- origin binding where the flow permits it.

### 8.1 Governed defaults for timeouts and freshness — decided

**These are governed configuration with safe defaults, not hard-coded
constants and not canon.** `FIR-CONFIG-001` owns the configuration
framework; PACK-14 supplies the defaults and the safety rules around
changing them.

| Assurance     | Idle timeout | Absolute timeout |
| ------------- | ------------ | ---------------- |
| `low`         | 30 minutes   | 7 days           |
| `substantial` | 30 minutes   | 24 hours         |
| `high`        | 15 minutes   | 8 hours          |

| Freshness window                  | Default    |
| --------------------------------- | ---------- |
| Consequential action step-up      | 15 minutes |
| Ordinary official submission      | 60 minutes |
| Security change or contact change | 15 minutes |

Rules that constrain the configuration itself:

1. A deployment may make these values **stricter** freely.
2. Relaxing a value is a **governed change** with an authority, a reason
   code and an audit record — not an environment variable someone edits.
3. **No configuration may remove a deadline.** There is no "unlimited"
   value; the schema does not admit one.
4. **No configuration may disable step-up, an audit obligation or a
   separation of duties** (`FIR-INV-006`).
5. Missing or unreadable configuration **falls back to these defaults**, not
   to permissive behaviour.

This closes **OD-P14-04**.

## 9. Account lifecycle

**The canonical `AccountStatus` enum is not extended.** Canon 7.2's six
values are the whole normative list and PACK-14 adds none:

```text
pending · active · restricted · suspended · recovery_pending · closed
```

`locked`, `closure_pending` and `deleted_or_anonymized` are **not account
statuses** and appear in no normative status list in this pack. Each is
represented by the construct that actually owns it:

| Situation             | Representation                                                                                    | Why not a status                                                                     |
| --------------------- | ------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| Technical lock        | **`AccountLock` record** — cause, threshold, expiry, unlock condition, reason code                | A lock is temporary, automatic and self-clearing; a status is a governed state       |
| Security quarantine   | **`AccountRestriction` of the security class** — authority, scope, reason code, review obligation | It is a restriction with a named authority, not a different kind of account          |
| Closure requested     | **`AccountClosureRequest` state** — requested, cooling-off, cancelled, completed                  | The request has the lifecycle; the account is still `active` until closure completes |
| Anonymized or deleted | **Lifecycle outcome and events** — `account.closed`, `account.anonymization_completed`            | An anonymized account is not in a state; it is an account that reached an end        |

Several may hold at once, and that is the point: an account can be `active`
with a lock in force and a closure request pending, and each of the three
facts is separately queryable, separately explainable and separately
reversible. Collapsing them into one enum value would have destroyed exactly
that.

**Four situations are never the same thing:** a technical lock
(`AccountLock`), a security quarantine (`AccountRestriction`), a membership
suspension decided by a party organ (`AccountStatus.suspended`, with the
decision owned by the membership domain), and a voluntary closure
(`AccountClosureRequest`). Each carries its own authority reference, reason
code and reversal path.

Operations: create, activate, verify contact, restrict, lift restriction,
lock, unlock, suspend, reinstate, begin recovery, complete recovery, request
closure, cancel closure, close, anonymize where permitted, retain where
required.

This closes **OD-P14-01**, and it closes it **without a canon amendment** —
which is the reason this representation was chosen over extending the enum.

## 10. Contact identifiers

Email and phone are **mutable attributes, never identifiers**. They may
change; they may be reused only under a governed policy; they require
verification. A change notifies **both** the old and the new channel —
notifying only the new one is how a takeover goes unnoticed. A high-risk
change requires step-up. **A recently changed contact may not be the sole
basis for recovery.** Normalization rules, uniqueness scope, shared family
email handling, organizational email handling and deleted-account reuse
policy are specified.

## 11. Cross-workspace session boundaries

FRONT-00's ten workspaces each declare `sessionSharing: forbidden`.
PACK-14 issues sessions that honour that.
`PACK-14-CROSS-WORKSPACE-SESSION-MATRIX.md` records, per workspace: origin,
sensitivity, permitted authentication bootstrap, permitted cookies,
prohibited storage, isolation rule and the reauthentication requirement for
crossing a risk boundary.

**No browser storage is an identity bridge**, no shared analytics identity
exists, and no token is reusable cross-origin.

### 11.1 Authentication bootstrap across origins — decided

**This is not SSO, and the specification refuses the word.** There is no
shared application session. What exists is a per-workspace authentication
ceremony that may reuse a completed identity verification without reusing a
session.

The ceremony:

1. **Each protected workspace starts its own authentication ceremony.** The
   workspace, not the browser, initiates; nothing is inherited by being on a
   sibling origin.
2. `identity-service` performs the verification and returns a **single-use,
   short-lived, audience-bound authorization response** naming the workspace
   it is for and the assurance achieved.
3. **Each workspace creates its own origin-local session** from that
   response. The response is spent at that moment and cannot be presented
   again.
4. **No parent-domain cookie is ever issued.**
5. **No token is reusable across origins.** An authorization response
   presented to an audience other than its own is refused with
   `CROSS_WORKSPACE_HANDOFF_INVALID`.
6. **No browser-storage identity is shared.** Not localStorage, not
   sessionStorage, not IndexedDB, not a cache entry, not an analytics
   identifier.
7. **Crossing into a higher-risk boundary requires a new authentication or a
   step-up**, never a token exchange.

The difference from SSO is not cosmetic. Under SSO, one credential
compromise yields sessions everywhere and one cookie theft crosses every
boundary. Here each workspace holds only what it minted for itself, each
revocation is scoped, and the authorization response is worthless the moment
after it is used.

This closes **OD-P14-06** for the workspace bootstrap. The voting handoff,
which uses the same single-use audience-bound shape but carries strictly
less, is §11.2.

### 11.2 WS-03 — Voting Client

Separate origin. No shared cookies, localStorage, sessionStorage,
IndexedDB, cache storage or service worker. No shared identity session. No
analytics, no fingerprinting, no shared telemetry. No persistent member
identifier, no general account ID, no membership number, no reusable bearer
token.

Entry is by the outbound **`VotingHandoffArtifact`**, whose boundary PACK-14
defines and whose contents it deliberately keeps empty of identity:

| Property                           | Requirement                                                                                                                                             |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Opaque**                         | No structure a holder can read, parse or correlate                                                                                                      |
| **Single-use**                     | A second presentation is refused with `VOTING_HANDOFF_ALREADY_USED`                                                                                     |
| **Short-lived**                    | Expiry checked at redemption                                                                                                                            |
| **Audience-bound**                 | The WS-03 origin only                                                                                                                                   |
| **Purpose-bound**                  | Entry to a voting context, and nothing else                                                                                                             |
| **Voting-context-bound**           | One voting context; not transferable to another                                                                                                         |
| **Carries no identifier**          | No account, person record, membership, member number, communication persona or contact value                                                            |
| **No reusable bearer semantics**   | It is not a token that grants access on possession after redemption                                                                                     |
| **No reverse identity resolution** | Neither the artifact nor the issuance and redemption records, jointly or separately, permit resolving a redemption back to the account that obtained it |

**Outside PACK-14, explicitly:** the eligibility assertion, voting
credential issuance, ballot casting, verification and tally. Those are
PACK-15 and PACK-16, taken with PACK-15's own threat model. PACK-14 defines
the **boundary the artifact crosses** and not the protocol on the other
side (ADR-088).

**How an eligibility statement reaches the voting domain without an identity
attached is PACK-15's problem, not a gap in PACK-14** — this pack discovers
the requirement and records it rather than solving it from outside the pack
that owns the threat model. This closes **OD-P14-10** by assignment.

## 12. Account recovery

The governed workflow (ADR-085):

```text
recovery requested
→ risk assessed
→ alternate verification
→ cooling-off if required
→ old credentials revoked
→ sessions revoked
→ new credential enrolled
→ out-of-band notification
→ recovery completed
```

### 12.1 Recovery assurance — decided

The earlier wording — "recovery is never weaker than the authentication it
replaces" — was too absolute to implement. Recovery by definition uses
_different_ evidence from the credential that was lost; demanding the same
evidence would mean demanding the lost credential. The rule is therefore
stated in terms of **resulting confidence**, not identical means:

| Rule                                                                                                                                                                     |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Recovery may use different evidence** from the lost credential — that is what recovery is                                                                              |
| **The resulting confidence must be equivalent**, or the shortfall must carry an **explicit, reason-coded risk acceptance** by a named authority                          |
| **High-assurance recovery requires dual control, a cooling-off period and out-of-band notification** — all three, not a choice among them                                |
| **Emergency recovery cannot immediately authorize high-risk actions.** It restores access; elevated capability returns only after the normal assurance path is satisfied |
| **Old credentials and all sessions are revoked before completion**, never after                                                                                          |

No support agent can unilaterally take over an account. No security
questions and no reliance on publicly discoverable personal facts.
Cooling-off, fraud indicators, evidence, dispute, suspicious-recovery
notification and emergency recovery are specified in
`PACK-14-RECOVERY-CONTROL-MATRIX.md`.

This closes **OD-P14-10**'s recovery half; the eligibility-to-voting
question it also carried is assigned to PACK-15 in §11.2.

## 13. Account takeover protection and suspicious activity

The threat model covers phishing, credential stuffing, password spraying,
stolen session, refresh-token replay, SIM swap, email compromise, device
theft, malicious recovery, insider reset, support impersonation, cookie
theft, CSRF, XSS-assisted session theft, session fixation, passkey removal
abuse, MFA downgrade, shared-device risk, malicious browser extension,
cross-origin leakage and correlation through telemetry.

Suspicious-activity signals — suspicious login, new device, unusual origin,
repeated failures, credential addition or removal, recovery attempt,
session replay, contact change, privileged operation — are named
individually. **Impossible travel is a weak signal only.**

**An opaque risk score is never the sole basis for a consequential
denial.** Every denial carries a reason code, an explainable decision, user
notification, a challenge path, review, appeal where applicable, and
false-positive handling.

## 14. Identity proofing

Levels: self-asserted, email-verified, phone-verified, document-assisted,
in-person, eID, organizational attestation, manually reviewed — each mapped
onto canon 19d.2's existing identity assurance scale.

The four-way separation is normative (ADR-086):

```text
authentication ≠ identity proofing ≠ membership eligibility ≠ authorization
```

## 15. External identity providers

An adapter boundary is defined; **no provider is selected**. Any adapter
must satisfy: minimum attribute release, no provider-specific identifier as
a global user ID, purpose limitation, account-linking governance,
unlinking, provider outage behaviour, provider compromise response,
assertion freshness, audience restriction, issuer validation, replay
prevention, evidence and fallback.

## 16. Account linking

User-initiated only. Step-up required. Proof of control of both sides.
**No automatic merge by email. No merge by name or date of birth.**
Duplicate-account review, unlinking, recovery consequences, conflict
handling, notification and audit are specified. Linking never creates a
cross-domain global identity.

## 17. Privileged identity administration

Roles — Security Admin, System Admin, Support Agent, Recovery Reviewer,
Identity Proofing Reviewer, Auditor — and their separations are defined in
ADR-087 and carried by PACK-12's existing mechanism. **PACK-14 defines no
new privileged mechanism and no universal identity console.**

## 18. Audit and observability

Loggable: account-scoped technical reference, authentication method class,
assurance result, session issue and revoke, recovery state, factor
lifecycle, suspicious event category, reason code.

**Never logged:** password, OTP, recovery code, private key, full WebAuthn
assertion, full identity document, ballot data, unnecessary personal
attributes, or raw contact details where a tokenized reference suffices.

## 19. Data model

Entities are enumerated in full in the acceptance matrix and the event
catalog. Summary:

- **Account** — `Account`, `AccountStatus` (canon 7.2's six values,
  unextended), **`AccountLock`**, `AccountRestriction` (including the
  security-quarantine class), `AccountContact`, `AccountLifecycleEvent`,
  `AccountClosureRequest`.
- **Credentials** — `Credential`, `CredentialType`, `CredentialStatus`,
  `PasskeyCredential`, `PasswordCredentialReference`, `MfaFactor`,
  `RecoveryCodeSet`, `CredentialRevocation`.
- **Authentication** — `AuthenticationAttempt`, `AuthenticationMethod`,
  `AuthenticationOutcome`, `AuthenticationAssurance`,
  `AuthenticationChallenge`, `RiskSignal`, `AuthenticationDecision`.
- **Sessions** — `SessionRecord` (service-level aggregate, not canon),
  `SessionScope`, `SessionAssurance`, `SessionRevocation`,
  `SessionRiskState`, `DeviceReference`,
  **`WorkspaceAuthorizationResponse`** (single-use, audience-bound),
  **`VotingHandoffArtifact`** (opaque, single-use, identity-free).
- **Recovery** — `RecoveryRequest`, `RecoveryMethod`, `RecoveryAssessment`,
  `RecoveryDecision`, `RecoveryCoolingOff`, `RecoveryEvidence`,
  `RecoveryDispute`.
- **Identity proofing** — `IdentityProofingCase`, `IdentityProofingMethod`,
  `IdentityAssertion`, `IdentityEvidenceReference`, `IdentityAssurance`,
  `IdentityProofingDecision`.
- **Mapping boundary** — `ScopedIdentityReference`, `IdentityMapping`,
  `MappingPurpose`, `MappingScope`, `MappingLifecycle`.

## 20. Events and reason codes

All events use PACK-13's canonical envelope unchanged.
`PACK-14-EVENT-CATALOG.md` defines the versioned families;
`PACK-14-REASON-CODE-CATALOG.md` defines the stable reason-code families.

**There is no generic `AUTH_ERROR`**, for the same reason PACK-13 forbade a
generic `DATA_ERROR`: where two failures differ in what the person or the
operator must do next, they are two codes.

## 21. Forms and official documents coverage

Per `FIR-FORM-002`'s mandatory PACK reporting rule, this round produces
`PACK-14-FORM-INVENTORY.md`, `PACK-14-FIELD-CATALOGUE.md`,
`PACK-14-CONTENT-CATALOGUE-DE.md`, `PACK-14-WORKFLOW-MATRIX.md`,
`PACK-14-ATTACHMENT-MATRIX.md`, `PACK-14-RENDITION-SPECIFICATION.md` and
`PACK-14-PRIVACY-RETENTION-MATRIX.md`, and the acceptance matrix carries a
**Forms and Official Documents Coverage** section.

The German content catalogue contains **real texts**, not placeholders.

## 22. Frontend contract

PACK-14 is not FRONT-PACK. It defines the minimum surfaces — login,
registration, passkey enrollment, MFA enrollment, account security, session
inventory, recovery, suspicious activity, step-up, contact change, account
closure — and their state, error and recovery behaviour.

**The FRONT-00/FRONT-01 visual baseline is authoritative** (`FIR-UX-003` …
`FIR-UX-011`). Before any redesign: inventory the existing components,
extract the actual tokens, classify each pattern as `reuse` / `extend` /
`replace`, justify every replacement, and preserve continuity. The
inventory and token extraction are performed in
`PACK-14-RENDITION-SPECIFICATION.md` against the real files. **No new
independent design language is created.**

### 22.1 What PACK-14 does not define — the page sequence

`FIR-UX-011` (Page Specification and Screen Content Governance) requires an
approved Page Specification Catalogue and Screen-State Matrix before any
user-facing domain is considered fully designed. **PACK-14 does not produce
them, and does not claim the identity journey is designed.**

What PACK-14 supplies is the domain side of `FIR-UX-011`'s responsibility
split: the process, the authoritative data, the permissions and assurance
requirements per action, the forms and official documents, the decisions,
the mandatory governed content, and the state semantics each surface must
carry. What it deliberately leaves open is the frontend side: page order,
screen structure, navigation model, content hierarchy, responsive layout
and interaction states.

**The complete first-page-to-final-page structure — entry screen,
subsequent pages, decision points, branch conditions, return and
cancellation paths, interrupted-process recovery, completion page and
receipt page — will be defined during the relevant `FRONT-PACK
Specification + UX/IA` stage, before frontend implementation.** That stage
owns the artefacts `FIR-UX-011` names: `PAGE-CATALOGUE.md`,
`PAGE-SEQUENCE-MAP.md`, `NAVIGATION-MAP.md`, `CONTENT-MAP.md`,
`ACTION-MAP.md`, `SCREEN-STATE-MATRIX.md`,
`PERMISSION-AND-ASSURANCE-MATRIX.md`,
`RESPONSIVE-LAYOUT-SPECIFICATION.md`, `ACCESSIBILITY-FLOW.md` and
`ACCEPTANCE-SCREENSHOT-INVENTORY.md`.

A FRONT-PACK implementation candidate must not start before those are
accepted, and frontend developers must not invent missing process logic or
consequential content — the governed content catalogue in
`PACK-14-CONTENT-CATALOGUE-DE.md` exists precisely so that they do not have
to.

## 23. Official delivery integration

Per `FIR-DELIVERY-001`, notifications are classified — informational
message, security alert, action-required notice, official decision — for
credential added and removed, contact changed, recovery started and
completed, account restricted, suspicious login, all sessions revoked, and
account closure requested.

## 24. Signature and representation boundaries

**Authentication is not an electronic signature.** PACK-14 defines
authenticated confirmation, step-up confirmation and transaction-bound
consent, and their relation to the future e-signature layer
(`FIR-TRUST-001`), which it does not implement.

The distinction between **actor**, **principal**, **beneficiary** and
**authorizing authority** is preserved. An account session identifies the
**actor**. The right to act for a principal is a future mandate boundary
(`FIR-REPRESENT-001`), not a session property.

## 25. Inclusion and alternative channels

Assisted registration, assisted recovery, offline identity proofing and
in-person fallback are specified, with accessibility obligations,
**no operator impersonation**, an immutable assisted-action receipt, and
attribution of the helper or operator. **Assistance is never authority to
decide for the user.**

## 26. Retention and deletion

Per PACK-09, retention is defined separately for the account record,
authentication attempts, session history, credential metadata, recovery
evidence, identity proofing evidence, contact history, suspicious activity
and privileged identity actions.

Deletion must not destroy evidence, violate a legal hold, weaken voting
unlinkability, or create a reuse or correlation vulnerability.

## 27. Failure modes

Specified behaviour for: authenticator unavailable, passkey unsupported,
email unavailable, SMS unavailable, eID provider unavailable, clock skew,
session store unavailable, risk engine unavailable, recovery reviewer
unavailable, notification failure, contact verification failure, identity
proofing inconclusive, duplicate account suspected, partial session
revocation, audit service unavailable.

**For consequential actions the behaviour is fail-closed or a governed
fallback with a reason code — never a silent permit.**

## 28. Canon assessment

`PACK-14-CANON-ASSESSMENT.md` records the verdict:
**CANON AMENDMENT NOT REQUIRED**, with the reasoning. Canon is not changed
by this round.

## 29. Open decisions

**Nine of ten are closed by the architecture correction; one remains open
for a reason that is not this pack's to remove.**

| ID            | Question                                                             | Resolution                                                                                                                                                                                                                                                                                                      |
| ------------- | -------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| OD-P14-01     | Where do `locked`, `closure_pending`, `deleted_or_anonymized` live?  | **Closed** — §9. Not statuses. `AccountLock`, `AccountRestriction`, `AccountClosureRequest` state, and lifecycle outcomes/events. Canonical enum untouched                                                                                                                                                      |
| OD-P14-02     | Extend `identity-service` or add a bounded context beside it?        | **Closed** — §4.1. `identity-service` owns all six contexts as internally separated modules; no parallel authentication service                                                                                                                                                                                 |
| OD-P14-03     | Does password fallback exist?                                        | **Closed** — §5.2. Yes, controlled: passkey-first, no new password-only account, MFA always, never sole assurance for a consequential action, disableable by governed configuration                                                                                                                             |
| OD-P14-04     | Freshness and session-age values                                     | **Closed** — §8.1. Governed configuration with safe defaults; stricter freely, relaxation governed, no deadline removable                                                                                                                                                                                       |
| OD-P14-05     | Is the session model canonical?                                      | **Closed** — §8. `SessionRecord` is a PACK-14 service-level aggregate, not canon; events use PACK-13's envelope                                                                                                                                                                                                 |
| OD-P14-06     | Cross-origin bootstrap and handoff shape                             | **Closed** — §11.1 and §11.2. Per-workspace ceremony with a single-use audience-bound authorization response; the `VotingHandoffArtifact` boundary defined, the protocol left to PACK-15/16                                                                                                                     |
| **OD-P14-07** | **Retention periods**                                                | **Open — pending legal confirmation.** PACK-09 owns retention schedules and this pack may not settle them. **It does not block the reference implementation:** `PACK-14-PRIVACY-RETENTION-MATRIX.md` defines safe provisional schedules and the deletion prohibitions that hold regardless of the final numbers |
| OD-P14-08     | Which actions require attestation?                                   | **Closed** — §5.1. No universal attestation; synced passkey caps at `substantial`; `high` needs device-bound or an approved equivalent; hardware attestation only for governed privileged classes; no member excluded for lack of it                                                                            |
| OD-P14-09     | Is SMS OTP permitted?                                                | **Closed** — §5.4. Not a login method, not a step-up factor, no assurance level; channel verification and a low-weight recovery signal only; the system runs with no SMS provider                                                                                                                               |
| OD-P14-10     | Recovery assurance, and eligibility reaching voting without identity | **Closed** — §12.1 for recovery assurance; §11.2 assigns the eligibility question to PACK-15, which owns the threat model it belongs to                                                                                                                                                                         |

**Why OD-P14-07 may stay open.** A retention period is a legal
determination, and PACK-09 is its owner. What would block implementation is
not an unconfirmed number but an undefined behaviour — and the behaviour is
defined: provisional schedules exist, deletion under legal hold refuses,
unknown hold state fails closed, evidence survives closure, and no deletion
may create a reuse or correlation vulnerability. Confirming the durations
changes configuration values, not the design.

## 30. What this round is not

It is not an implementation, a candidate or a PASS. It is not production
readiness, legal activation, a compliance statement, a procurement decision
or a provider commitment. No authentication service exists. No identity is
verified. No session is issued. No account can be recovered, because
nothing has been built.
