# PACK-15 — Voting Trust Boundary, Eligibility & Credential Separation

**Round type:** specification and ADR only. **No code. Not implemented. Not a candidate. Not a PASS.**

**Architecture correction applied (2026-07-31).** Five implementation-blocking
open decisions are resolved in this revision — the Assertion Issuer
boundary (`OD-P15-01`), timing-correlation controls with governed reference
defaults (`OD-P15-02`), the context-scoped pseudonym (`OD-P15-03`), the
independent-auditor evidence bundle (`OD-P15-04`) and credential delivery
(`OD-P15-07`). §32 lists them. **No architecture decision already accepted
was reversed**; ADR-089 … ADR-098 keep their decisions, and every closure
was resolved in the direction that tightens an existing prohibition rather
than relaxing one.

**Target version:** `0.15.0` — a target, not a setting. This round changes
no version. `REPOSITORY_VERSION` remains `0.14.0` and `CANON_VERSION`
remains `0.8.0`.

**Baseline:** `EPD2_PACK-14_IDENTITY_AUTHENTICATION_ACCOUNT_SECURITY_0.14.0_FINAL_PASS.zip`
(PACK-01 through PACK-14: FINAL PASS, external GitHub Actions verified).

**Authoritative register:** `EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER_UPDATED_V6.md`,
carried in this archive at its canonical path
`docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md`. It supersedes
the register version carried in the pre-correction PACK-15 SPEC+ADR
archive, preserves every prior FIR entry unchanged and adds `FIR-OSS-001` …
`FIR-OSS-006`. **There is one canonical register copy and no standalone
second copy.**

**Register entry:** `FIR-ROADMAP-005`.

**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**

---

## 0. What this round is, and the two things it must not become

Fourteen packs have been careful never to know who anyone is, and PACK-14
was the round that finally had to. It answered the question narrowly — who
is operating this session — and then, at the edge of the voting domain, it
stopped. ADR-088 defined the `VotingHandoffArtifact` and said, in as many
words, that how an eligibility statement reaches the voting domain with no
identity attached is PACK-15's problem, taken with PACK-15's own threat
model.

This is that round. Its subject is the single most dangerous transition in
the system:

```text
ordinary identity domain
→ eligibility determination
→ minimized eligibility assertion
→ credential issuance
→ isolated voting boundary
```

The purpose is to let the organization confirm that a particular
participant is entitled to take part in a particular vote, and to hand that
participant a one-time right of entry to the voting domain — **without
sending ordinary identity across the boundary and without creating a path
`person → credential → ballot` anywhere in the system, at any time, under
any join of any two stores.**

There are two ways this round can fail, and they are opposites.

**The first failure is a link.** Eligibility is inherently identified: you
cannot decide whether *this member* may vote without knowing which member.
A credential is inherently unidentified: the moment it carries anything
that resolves backwards, the ballot it eventually redeems is attributable.
Between those two facts sits a temptation that has defeated most systems
that tried this — a single row somewhere holding both the eligibility
reference and the credential reference, written for the best of reasons
(idempotency, support, reconciliation, "we needed it for the audit").
**That row is the vulnerability.** It is not a policy problem that can be
solved by access control, because access control fails and joins do not
un-happen. It has to be structurally absent.

**The second failure is a false claim.** The counter-temptation, once the
first is understood, is to describe the resulting design as anonymous,
unlinkable or verifiable in a stronger sense than it is. This round
specifies a **separation architecture**, not a cryptographic voting
protocol. It chooses no blind-signature scheme, no anonymous-credential
scheme, no mix network, no homomorphic tally and no threshold key
ceremony. Those are PACK-16's, and choosing them from here — from outside
the round that owns the ballot threat model — would repeat exactly the
mistake PACK-13 refused to make and PACK-14 inherited. What this round
guarantees is what a separation architecture can guarantee: **no component
holds enough to reconstruct the chain, and no two stores can be joined to
recover it.** Timing, operational metadata and infrastructure-level
correlation are named as residual risks with owners and, since the
architecture correction, with **specified controls and default values** —
not waved away and not claimed solved.

So the governing rule of this pack is:

> **Eligibility says that someone may vote. A credential says that someone
> may enter. Neither says who, and nothing in the system may be able to put
> the two answers back together.**

Everything below follows from taking that seriously.

---

## 1. Scope

PACK-15 defines, as documents only:

1. the voting context and its registry;
2. the eligibility request;
3. eligibility rule evaluation and rule-set versioning;
4. the eligibility decision, its validity and its reason codes;
5. manual review;
6. eligibility evidence references;
7. the minimized eligibility assertion, **its queued release and its
   one-time pickup**;
8. the credential issuance request;
9. the voting credential lifecycle **and its delivery boundary**;
10. revocation before redemption;
11. the redemption boundary;
12. replay prevention;
13. unlinkability, non-correlation **and timing-correlation controls**;
14. separation of duties across election administration;
15. isolated audit streams **and the independent-auditor evidence bundle**;
16. dispute and appeal without ballot linkage;
17. exceptional cases;
18. failure modes;
19. the frontend handoff contract;
20. forms and governed content;
21. the threat model;
22. retention and deletion;
23. the canon assessment;
24. implementation acceptance criteria.

### 1.1 Out of scope, explicitly

Ballot casting. Tally. The Voting Client itself. Production cryptography.
Real HSM or KMS integration. Ballot encryption. Verifiability protocols.
Receipt-freeness and coercion-resistance mechanisms. **Advance credential
issuance across separate visits** (§13.4). The page-by-page frontend
structure. Any change to a service, a test, a migration, a contract
fixture, a CI workflow, `REPOSITORY_VERSION` or `CANON_VERSION`.

**PACK-15 is not implemented, is not a candidate, and is not a PASS.**

---

## 2. Relationship to the existing canon, services and packs

| Source                     | What PACK-15 takes from it                                                                                       | What PACK-15 does not do                                              |
| -------------------------- | ---------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| Canon 9 / 19d.4            | `EligibilityRule`, `EligibilityDecision`, `EligibilitySnapshot`, `ParticipantEligibilityPolicy`, rule freeze      | Redefine them, move their owner, or add a second eligibility scale    |
| Canon 10.1                 | `ParticipationCredential` and its forbidden-field prohibition                                                    | Replace it or weaken its prohibition                                  |
| Canon 15.1–15.4            | `Ballot`, `VoteEnvelope`, `VoteReceipt` and their structural identity-freedom                                    | Touch them at all — PACK-16 owns them                                 |
| Canon 19d.8 / 19d.9        | Assurance separation; the two-stage membership boundary                                                          | Cross the membership boundary or invent a third assurance vocabulary  |
| Canon §21                  | The canonical event envelope                                                                                     | Add transport metadata or a second envelope                           |
| PACK-11                    | Governed documents and evidence references                                                                       | Inline evidence content anywhere                                      |
| PACK-12                    | Privileged access, dual control, break-glass, statistical disclosure control                                     | Build a second privileged-access mechanism                            |
| PACK-13                    | Outbox, idempotent consumers, contract evolution, retention and legal hold                                        | Choose the voting domain's broker topics or transport                 |
| PACK-14 / ADR-088          | The outbound `VotingHandoffArtifact`, WS-03 isolation, no global ID, scoped actor references                     | Re-open the handoff's properties or issue a session for WS-03         |
| FRONT-00 / FRONT-01        | The visual baseline and `sessionSharing: forbidden` on every workspace                                           | Introduce a new design language or a page sequence                    |
| Register §29 / `FIR-OSS-*` | The intended `EUPL-1.2` licensing baseline and its boundaries                                                    | Complete legal licensing, or claim any release compliance             |

**Nothing above is modified by this round.**

---

## 3. The invariants this round exists to preserve

```text
ELIGIBILITY != AUTHENTICATION
ELIGIBILITY != MEMBERSHIP
ELIGIBILITY != VOTING CREDENTIAL
VOTING CREDENTIAL != BALLOT
NO GLOBAL USER ID
NO PERSON-TO-BALLOT LINK
NO INTERMEDIATE TALLY
NO SHARED VOTING SESSION
NO SHARED STORAGE WITH WS-03
NO PERMANENT MEMBER IDENTIFIER IN VOTING DOMAIN
```

And the structural rule from which most of PACK-15's design falls out:

> **No service, no database, no cache, no log, no metric, no backup and no
> audit stream may contain, at any moment, both an eligibility-side
> reference and a voting-side reference for the same participation.**

That rule is stronger than "do not join these tables". It says the pair
never exists to be joined, which is why it survives an operator with
database access, a misconfigured replica, a support export and a subpoena.

**No single component may see more than one of:** account identity;
membership identity; eligibility; voting credential; ballot; tally.

---

## 4. Bounded contexts

Six contexts. Each is named with its responsibility, what it must never
hold, and its decided owner.

### 4.0 The voting-trust service — naming, decided

The **voting-trust service** is this round's name for the deployment unit
that hosts the identity-side PACK-15 contexts: eligibility evaluation
(VC-02), assertion issuance (VC-03) and the handoff boundary (VC-05). In
the existing repository that unit is **`eligibility-service`**, which canon
9 and 19d.4 already make the owner of `EligibilityRule`,
`EligibilityDecision` and `EligibilitySnapshot`.

**PACK-15 names a role; it does not create a service and does not move a
canonical aggregate.** Where this specification says "the voting-trust
service" it means `eligibility-service` acting in that role, and the name
exists so that the internal boundaries below can be stated without implying
that they are service boundaries today.

### 4.1 VC-01 — Voting Context Registry

**Responsibility.** The definition of a vote as an administrative object:
election or decision identifier, organizational scope, voting window,
eligible-population policy reference, governing rule-set reference,
assurance requirements, credential issuance window, revocation cutoff,
audit policy, privacy profile, **issuance timing profile** (§19.2), status.

**Never holds.** Any participant identity, eligibility case, assertion,
credential, ballot or tally.

**Owner.** `governance-service`, in a `voting_contexts` module with its own
storage boundary. It is deliberately **not** `voting-service`:
`voting-service` owns `Ballot`, `VoteEnvelope` and `VoteReceipt`, and the
registry is read by the eligibility side, which must have no read edge to
anything that holds a cast ballot.

### 4.2 VC-02 — Eligibility Service

**Responsibility.** Eligibility request, rule evaluation against a frozen
rule-set version, eligibility decision, reason codes, manual review,
evidence references, validity window, dispute, and the
**participation-unit ledger** that enforces one assertion per participation
unit.

**Never holds.** Voting credentials. Ballot data. Redemption records.
Anything that identifies which credential resulted from which decision.

**Owner.** The voting-trust service (`eligibility-service`), `eligibility`
module, own storage boundary.

### 4.3 VC-03 — Eligibility Assertion Issuer — `OD-P15-01` closed

**Responsibility.** Minting the minimized eligibility assertion, holding it
in the **issuance queue** until its governed release time (§19), releasing
it into a **one-time pickup**, and producing issuance evidence.

**Never holds.** Ordinary identity in anything it emits. Any credential
reference. Any redemption outcome. Any record that pairs an assertion with
a credential.

**Decision — the boundary, closed.** The Assertion Issuer is:

1. **A separately bounded module with its own storage boundary** inside the
   voting-trust service. It does not share a schema, a transaction, a
   connection pool or a migration lineage with the eligibility decision
   store. VC-02 reaches it only through its declared interface, never
   directly into its tables — the discipline ADR-070 applies between
   domains, applied here between modules.
2. **Holder of separate signing keys and separate service credentials.**
   The assertion signing key is not held by, readable by or derivable from
   the eligibility decision store, and the issuer's service credential is
   distinct from the eligibility module's. A compromise of one does not
   yield the other.
3. **Structurally unable to read ordinary account, person-record or
   membership stores.** No import path, no client, no connection, no
   credential, no network route. Not "does not"; *cannot*.
4. **A consumer of minimized eligibility decisions only.** Its declared
   input is the decision's result, class, organizational scope,
   assurance-satisfied flag and context reference — nothing else, and
   nothing that carries a criteria input, a reason history or an evidence
   reference.
5. **Designed so that it can later become a separate deployable without a
   contract change.** Its interface is transport-agnostic and
   version-governed under ADR-074; it takes part in no shared transaction
   with VC-02; it is addressed by audience identity rather than by
   in-process reference; and its storage is already a separate boundary. A
   later extraction is a deployment change, not a contract change.

**Why not a separate service today.** The assertion is the minimized
projection of an eligibility decision, and moving it out of the canonical
owner's deployment unit today would ship the decision across a network for
no privacy gain — the separation that the invariant actually needs is
between the **issuer of the assertion** and the **issuer of the
credential** (§4.4), which is already a service boundary and always will
be. Point 5 makes the remaining question a deployment decision that can be
taken later without re-opening anything.

### 4.4 VC-04 — Voting Credential Issuer

**Responsibility.** Credential issuance, credential status, revocation
before redemption, duplicate-issuance prevention, redemption status, replay
rejection.

**Never holds.** Raw membership or identity data. Any account, person,
membership or persona reference. Any eligibility decision. **Any assertion
identifier retained alongside a credential identifier.** Any context-scoped
pseudonym.

**Owner.** `credential-service` — canon 10.1's owner of
`ParticipationCredential`, which already forbids identity fields
structurally. **This is a service boundary, not a module boundary, and it
is not negotiable.**

### 4.5 VC-05 — Voting Handoff Boundary

**Responsibility.** Transforming PACK-14's outbound `VotingHandoffArtifact`
into the start of a PACK-15 flow, and serving the **one-time assertion
pickup** to the isolated origin: one-time semantics, audience binding,
origin binding, and no reverse identity resolution.

**Never holds.** An account reference. A session. Anything that lets the
voting side learn which account crossed.

**Owner.** The voting-trust service, `handoff` module, own storage
boundary.

### 4.6 VC-06 — Audit Separation Boundary

**Responsibility.** Six evidence streams that are never unified, and the
**versioned independent-auditor evidence bundle** (§20.2).

**Owner.** `audit-core` provides the evidence primitives; the streams are
separately keyed, separately retained and separately authorized.

### 4.7 What is deliberately not a context here

**Ballot casting, verification and tally.** `voting-service` and
`tally-service` are untouched by this round. PACK-15 hands the voting
domain a redeemed capability and stops.

---

## 5. The flow, end to end — corrected

```text
[WS-02, authenticated ordinary workspace]
  member selects a voting context
    → eligibility requested                    (VC-02, identity side)
    → rules evaluated against frozen rule-set  (VC-02)
    → eligibility decision + reason codes      (VC-02)
    → [manual review, if required]             (VC-02, Eligibility Reviewer)
    → participation-unit ledger marked         (VC-02)
    → assertion minted and QUEUED              (VC-03) ← §19 timing controls
    → assertion RELEASED into a one-time pickup(VC-03/VC-05)
    → participant notified: access available
    → participant initiates the one-time handoff and leaves WS-02
─────────────────────────── trust boundary ───────────────────────────
[WS-03, isolated voting origin]
    → handoff artifact redeemed → assertion obtained, volatile memory only
    → assertion presented                      (VC-04)
    → short randomized minting delay           (§19.3)
    → nonce marked spent (set only) + credential issued (VC-04)
    → credential redeemed                      (VC-04)
    → minimum continuation capability
─────────────────────────── PACK-16 begins ───────────────────────────
    → ballot cast                              (voting-service, PACK-16)
    → tally                                    (tally-service, PACK-16)
```

Four properties of this flow carry the whole architecture.

**One. Eligibility is decided on the identity side, before the boundary.**
The voting side never evaluates eligibility, never sees a rule input and
never learns why anyone was approved.

**Two. Duplicate prevention and replay prevention live on opposite sides.**
The identity side enforces **one assertion per participation unit per
voting context**; the voting side enforces **one credential per assertion
nonce**. Neither needs the other's identifier, and between them the effect
is exactly-once (§13).

**Three. The consumption record is a set, not a map.** When the Credential
Issuer accepts an assertion it records the assertion's nonce as *spent*. It
does not record which credential it then issued. **There is no row anywhere
that contains both.** ADR-093 is its decision record.

**Four. Credential material never exists outside WS-03.** The ordinary
workspace transmits **only** a one-time handoff artifact; the assertion is
picked up inside the isolated origin; the credential is minted, held in
volatile memory and redeemed inside the same isolated origin; and what
survives the visit is the minimum continuation capability. §13.3 is the
delivery specification and closes `OD-P15-07`.

---

## 6. Separation of duties

Ten roles; the full incompatibility matrix, the acts requiring dual control
and the break-glass constraints are
`PACK-15-SEPARATION-OF-DUTIES-MATRIX.md`, which is the `FIR-ROLE-005`
Election Administration Separation Matrix for this domain.

| Role                     | May do                                                              | May never                                                        |
| ------------------------ | ------------------------------------------------------------------- | ---------------------------------------------------------------- |
| Membership Authority     | Maintain membership facts                                           | Issue a voting credential; see an assertion                      |
| Eligibility Officer      | Configure and operate eligibility evaluation                        | See a ballot; see a credential; issue a credential               |
| Eligibility Reviewer     | Decide manual-review cases                                          | Approve a case they raised or are the subject of; see a ballot   |
| Credential Issuer        | Issue, revoke and mark redeemed                                     | See ordinary identity; see a ballot; see a tally                 |
| Voting Operations Officer| Operate the voting context and its windows                          | Evaluate eligibility; issue credentials; read the tally early    |
| Voting Client Operator   | Operate WS-03                                                       | Receive membership data; hold identity; retain credential material |
| Tally Authority          | Perform the official tally (PACK-16)                                | Receive identity; receive credentials; publish before closure    |
| Independent Auditor      | Verify integrity from evidence bundles                              | Hold unrestricted identity correlation access                    |
| Security Auditor         | Review integrity and security evidence                              | Read ballot content; join two evidence streams                   |
| Dispute Reviewer         | Decide eligibility and issuance disputes                            | Link a person to a ballot; require ballot content as evidence    |

Hard prohibitions: the Membership Authority does not issue credentials; the
Eligibility Service never sees a ballot; the Credential Issuer never sees
ordinary identity; the Voting Client never receives membership data and
**never retains credential material**; the Tally Authority never receives
identity; **no operator holds eligibility, issuance and tally authority at
once**, and no grant, emergency, feature flag or break-glass path may
produce that combination; break-glass requires dual control through
PACK-12's existing mechanism; an auditor's access is **evidence-bundle
access**, never unrestricted identity correlation access.

---

## 7. Voting context

```text
VotingContext
  VotingContextId              VotingType
  OrganizationalScope          VotingWindow
  CredentialIssuanceWindow     RevocationCutoff
  EligibilityRuleSetReference  RequiredAssurance
  ParticipationClass           AuditProfile
  PrivacyProfile               IssuanceTimingProfile      ← added by the correction
  Status
```

### 7.1 Context types

Seven, and they are **not** interchangeable in their eligibility, assurance
or revocation rules.

| Type                        | Typical eligible population              | Assurance                | Revocation cutoff        | Notes                                                                          |
| --------------------------- | ---------------------------------------- | ------------------------ | ------------------------ | ------------------------------------------------------------------------------ |
| `internal_party_vote`       | Active members in scope                  | `substantial`            | Issuance window close    | The default case                                                               |
| `programme_vote`            | Active members in scope                  | `substantial`            | Issuance window close    | May carry a longer window and a wider scope                                    |
| `organizational_election`   | Active members in scope, duration rule   | `substantial` … `high`   | Strict, early            | Contest and appeal pressure is highest here                                    |
| `candidate_nomination`      | Members in the nominating body           | `high`                   | Strict, early            | Conflict-of-interest and candidacy-status criteria apply                       |
| `assembly_decision`         | Present and entitled assembly members    | `substantial`            | Session-bound            | Bound to an assembly session; `FIR-ASM-*` owns the meeting side                |
| `advisory_consultation`     | May extend beyond members                | `low` … `substantial`    | Lenient                  | Non-binding; **must be labelled as such in every surface**                     |
| `public_election_profile`   | Defined by law                           | Defined by law           | Defined by law           | **Profile only. Not activated, not permitted, not claimed. No legal effect.**  |

### 7.2 Status lifecycle

```text
draft → configured → active → issuance_open → issuance_closed
      → voting_open → voting_closed → tallied → archived
              ↘ suspended ↗            ↘ cancelled
```

No transition is automatic on a deadline alone where the effect is a
decision — silence is never approval, following canon 19d's `INV-10`.

---

## 8. Eligibility

```text
EligibilityCase          EligibilityRequest        EligibilityRuleSet
EligibilityCriterion     EligibilityEvidenceReference
EligibilityDecision      EligibilityDecisionStatus EligibilityValidity
EligibilityReview        EligibilityDispute        ParticipationUnitLedgerEntry
```

Fourteen criteria with their minimized inputs, source owners, staleness
rules and reason codes are `PACK-15-ELIGIBILITY-MATRIX.md`.

An eligibility decision is rule-set-version-bound, context-bound,
time-bound, reason-coded, reviewable, evidenced, and **superseded** when a
fact it relied on changes before an assertion is minted. Canon 9.1's rule
freeze extends to the rule-set: a version is immutable, a context
references a version, and the version cannot change after `issuance_open`.

Statuses: `requested` · `evaluating` · `approved` · `denied` ·
`review_required` · `under_review` · `superseded` · `expired` · `disputed`
· `withdrawn`. `review_required` is not a denial and must never be
presented as one.

Manual review never auto-approves and never auto-denies; an unavailable
reviewer means the case waits, escalates, and the participant is told it is
waiting. No reviewer decides a case they raised or are the subject of.

**Eligibility is not authentication, not membership and not a credential.**
An approved decision by itself lets nobody enter anything.

---

## 9. The membership and identity boundary

**PACK-15 owns no membership data and stores none.** The Eligibility
Service receives a **minimized input** through a governed adapter, in the
shape canon already sanctions: an attestation mapping, not a record.

Never passed downstream, to any PACK-15 component, in any form: full member
record · full address · email · phone · member number · account ID · person
record ID · communication persona · raw identity-proofing data · unrelated
roles · unrelated restrictions · date of birth where an age *predicate*
suffices · name.

`PACK-15-ATTRIBUTE-MINIMIZATION-MATRIX.md` states, per criterion, the
maximum permissible input — and in most rows that maximum is a **boolean
predicate evaluated at the source**, not a value.

---

## 10. The eligibility assertion

```text
EligibilityAssertion
  EligibilityAssertionId   VotingContextReference
  EligibilityResult        EligibilityClass
  OrganizationalScope      RequiredAssuranceSatisfied
  IssuedAt                 ExpiresAt
  Audience                 Purpose
  Nonce                    Status
```

### 10.1 Required properties

Minimized. Integrity-protected through the governed trust boundary (§18).
Purpose-bound. Audience-bound. Context-bound. Short-lived.
Replay-protected. Revocable before pickup and before use where the
context's policy permits it. Unusable for any other voting context.
**Unusable as a general identity token.**

### 10.2 Prohibited content — normative

An assertion **must not contain**, in any field, in any encoding, in any
extension, and not in a form from which they can be derived: account ID ·
person record ID · membership ID · member number · email · phone · name ·
date of birth · address · communication persona · eligibility evidence ·
raw reason history · **any persistent cross-context subject identifier** ·
**any context-scoped pseudonym** (§10.3).

The prohibition is on *derivability*, not on field names. A hash of the
member number is the member number. A per-member salt reused across
contexts is a persistent subject identifier wearing a costume.

### 10.3 Context-scoped pseudonym — `OD-P15-03` closed

**The default is no pseudonym.** A voting context has none unless its
configuration explicitly declares one, and the declaration requires a
governed justification.

A context-scoped pseudonym is **permitted only where it is required for
context-local exactly-once enforcement** — that is, where the context's
privacy profile forbids the voting-trust service from keying its
participation-unit ledger on a participant reference, so the ledger needs a
key of its own. It exists for that purpose and no other. It is **not** a
subject-continuity feature, **not** an analytics key, and **not** a support
handle.

Binding rules:

1. **Unique per voting context.** Derived per `(participant,
   VotingContextId)` with a context-scoped secret held only inside the
   voting-trust service.
2. **Never reusable across contexts**, never derivable from another
   context's pseudonym, and never derivable from the participant's
   identifiers.
3. **Never exposed to WS-03 as an identity field — or as any field.** It is
   not in the assertion (§10.2), not in the pickup, not in the credential,
   not in a redemption record, not in a ballot, not in a tally, not in an
   evidence bundle. **It never crosses the trust boundary.**
4. **Not reverse-resolvable through ordinary APIs.** No operation accepts a
   pseudonym and returns a participant, and none accepts a participant and
   returns a pseudonym. Resolution exists only inside the ledger's own
   enforcement path and is reachable through no interface.
5. **Governed retention and destruction.** The pseudonym and its derivation
   secret are destroyed at the context's retention boundary; the
   destruction is an audited act; and a legal hold does not extend the life
   of the derivation secret, because a preserved secret is a preserved
   correlation capability (`PACK-15-PRIVACY-RETENTION-MATRIX.md` §1).

**This closure tightens the pre-correction text**, which permitted a
pseudonym as a subject-continuity mechanism that could appear on the voting
side. It cannot. Contexts that appeared to need continuity across the
boundary — two-round elections, resumed sessions — are served instead by
separate contexts with separate eligibility decisions, or by the
single-visit delivery flow of §13.4.

### 10.4 Assertion statuses

`minted` · `queued` · `released` · `picked_up` · `revoked` · `expired` ·
`redeemed` · `replay_rejected`.

There is no partial spend. An assertion is picked up once and spent once,
each in one atomic act.

---

## 11. The voting credential

```text
VotingCredential
  VotingCredentialId   CredentialType     CredentialStatus
  VotingContextReference
  IssuedAt             ExpiresAt          RedeemedAt
  RevokedAt            RevocationReason   RedemptionReference
```

Opaque; single-use; short-lived; context-bound; audience-bound;
non-transferable as far as is technically enforceable and no further;
non-replayable; unlinkable from the voting side; **no ordinary identity
field, no assertion identifier and no context-scoped pseudonym**; no
reusable bearer semantics outside the defined redemption; no cross-context
use.

`VotingCredentialId` is **never** used as, derived into, or stored beside a
ballot identifier.

Lifecycle, transitions, issuance controls and the eleven exceptional cases
are `PACK-15-CREDENTIAL-LIFECYCLE-MATRIX.md`.

```text
requested → eligible → issued → redeemed
                    ↘ revoked ↘ expired ↘ replay_rejected ↘ cancelled ↘ disputed
```

`redeemed` is **absorbing**: no administrative act, break-glass grant,
incident response or privileged path moves a credential out of it.

---

## 12. Redemption

```text
CredentialRedemptionRequest   CredentialRedemptionDecision
CredentialRedemptionReference ReplayDetectionRecord
```

Redemption must, in one atomic act: verify validity, context, audience,
expiry and single use; mark the credential redeemed; and reject a replay
with a distinct reason code.

Redemption must **not** expose identity, return membership data, return
anything about the participant, or create a reusable voting session. What
the voting domain receives is a **minimal continuation capability**: scoped
to one context, valid for one casting act, bounded in time, carrying no
identity and no persistent identifier, consumed by PACK-16. It is not a
session and is not resumable after use.

---

## 13. Duplicate issuance, exactly-once, and delivery

### 13.1 The split

| Concern                                | Enforced by                | Using                                        |
| -------------------------------------- | -------------------------- | -------------------------------------------- |
| One participation per eligible person  | Identity side (VC-02)      | The participation-unit ledger                |
| One pickup per released assertion      | Identity side (VC-05)      | The pickup's one-time state                  |
| One credential per assertion           | Voting side (VC-04)        | The spent-nonce set                          |
| One redemption per credential          | Voting side (VC-04)        | The credential's own status                  |
| One ballot per redemption              | PACK-16                    | The continuation capability                   |

Four obligations hold in every exceptional case: **exactly-once effect ·
safe idempotent retry · no double credential · no identity leakage.**

### 13.2 The uncomfortable cases

*Credential issued, delivery uncertain* cannot be resolved by asking the
voting side who the credential belongs to. It is resolved by: the assertion
being already spent, the credential being obtainable only inside the same
WS-03 visit, and — if that fails — a governed reissue that revokes the
undelivered credential before the cutoff and mints a fresh assertion under
dual control. Where the cutoff has passed, the participation is lost for
that context and the dispute path records it. **Inventing a recovery that
requires linking a person to a credential would trade the system's central
guarantee for one voter's convenience, and that trade is refused.**

### 13.3 Credential delivery — `OD-P15-07` closed

**Credential material is delivered only inside the isolated WS-03
boundary.** The reference delivery flow:

1. **The ordinary workspace transmits only a one-time handoff artifact.**
   It never receives, holds, displays, logs or forwards an assertion or a
   credential. The artifact is PACK-14's `VotingHandoffArtifact` — opaque,
   single-use, short-lived, audience-bound, context-bound, identity-free
   (ADR-088), unchanged.
2. **WS-03 redeems the artifact and receives the assertion**, in volatile
   page memory only.
3. **WS-03 presents the assertion and receives the credential**, in
   volatile page memory only, after the minting delay of §19.3.
4. **WS-03 redeems the credential and receives the minimum continuation
   capability.** That capability is what survives the exchange.

**Prohibited absolutely, as delivery channels for credential material:**

| Prohibited                                          | Note                                                                 |
| --------------------------------------------------- | -------------------------------------------------------------------- |
| Email                                                | Ordinary mailboxes are shared, forwarded, archived and breached      |
| SMS                                                  | Same, plus carrier-side exposure                                     |
| Clipboard                                            | Readable by other origins and by extensions                          |
| Ordinary URL query or fragment                       | Logged by proxies, servers, history and referrers                    |
| Downloadable file                                    | Persists outside the isolation boundary                              |
| On-screen display as copyable or transcribable text  | Becomes a transferable bearer value, and a coercion instrument       |
| Push notification payload                            | Delivered through third-party infrastructure                         |
| Print or PDF rendition                               | Persists, and is operator-visible in an assisted setting             |
| Any operator-visible surface                         | A helper who can see it can retain it                                |
| Any persistent client storage in WS-03               | ADR-096 already forbids the storage; this forbids the content too    |

5. **No operator, helper or support role ever sees credential material.**
   Not in a screen share, not in a log, not in an error report, not in a
   support tool.

### 13.4 Single-visit issuance — a consequence, stated

Because credential material may not persist outside WS-03 and may not be
displayed, **credential issuance and redemption occur within one WS-03
visit** in the reference flow. `CredentialIssuanceWindow` therefore governs
when a participant may *enter* the voting origin, not a period during which
they hold a credential outside it.

If the WS-03 page is lost between issuance and redemption, the credential
remains `issued` and unredeemed, and the remedy is the governed
revoke-then-reissue path before the cutoff — not a recovery that would
require identifying the holder.

**Advance issuance across separate visits is out of scope for this round**
and is deferred to PACK-16, because holding a credential between visits
requires a holder-side custody decision that WS-03's isolation rules forbid
and that a cryptographic construction may solve properly (`OD-P15-05`).

### 13.5 Accessible and assisted delivery

The assisted and accessible paths must preserve isolation and must not
create helper custody:

| Requirement                                                                                 | Consequence                                                        |
| ------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| Assistance ends at the boundary of the voting origin's credential exchange                  | A helper may bring the participant to WS-03 and no further         |
| **No helper or operator retains credential material** — there is none to retain             | The exchange is machine-to-machine inside the page                 |
| No screen sharing, remote control or shadowing during the credential exchange               | An observed exchange is an operator-visible credential             |
| Assisted-action receipts record the assistance, never the credential                        | `F-P15-08`                                                         |
| The accessible path is an **independent** path, not a supervised one                        | Screen-reader, keyboard-only and low-bandwidth flows are first-class |
| Where an independent accessible path is not achievable, it is a named limitation with an owner | Not a silent downgrade                                            |
| Offline and in-person fallback confirms **eligibility**, never delivers a credential outside WS-03 | The isolation is not waived for accessibility               |

---

## 14. Revocation — normative rule, explicit

| Moment                            | What may be invalidated | By whom                                          | Effect on a ballot |
| --------------------------------- | ----------------------- | ------------------------------------------------ | ------------------ |
| **Before issuance**               | The eligibility decision, and the assertion before pickup | Eligibility Service; Assertion Issuer | none — nothing exists |
| **After issuance, before redemption** | The credential      | Credential Issuer, before `RevocationCutoff`     | none               |
| **After redemption**              | **Nothing**             | **Nobody**                                       | **none, ever**     |

Stated normatively, because these are the sentences an implementation must
be able to point at:

1. **Before issuance, eligibility may be invalidated.** A source change, a
   restriction, a scope change or a corrected fact supersedes the decision
   and prevents assertion minting; a minted assertion may be revoked before
   pickup and before use where the context's declared policy permits.
2. **After issuance and before redemption, the credential may be revoked**
   on governed conditions and before the cutoff, with dual control and
   Independent Auditor notification inside the final window.
3. **After redemption, no person-level revocation and no ballot lookup is
   possible.** Not by an operator, not by an administrator, not under
   break-glass, not under legal compulsion executed through this system.
4. **No identity-side operation may locate, delete, replace or invalidate a
   specific ballot.** No such operation exists, and none may be added; the
   identity side holds nothing that could address one.
5. **Any later election-wide invalidation belongs to PACK-16 governance** —
   annulment, re-run, suspension of a result — **and must not create
   identity linkage.** An invalidation that required knowing whose ballots
   were affected would be the link, and is refused; an election-wide
   invalidation acts on the context, not on participants.

`RevocationCutoff` maxima, the trade-off and the evidence requirements are
`PACK-15-REVOCATION-MATRIX.md`, which is normative.

---

## 15. No intermediate tally

```text
NO INTERMEDIATE TALLY
```

Before the official tally, the system must not disclose the distribution of
votes, option or candidate totals, ballot content, turnout, participation
correlated with identity, person-level participation state, or **any
real-time operational data from which an outcome can be inferred**.

Permitted operational information and its controls — including the
**minimum cell size of 5** and the rule that disclosure control applies to
the **set** of published signals rather than to each one alone — are
`PACK-15-INTERMEDIATE-TALLY-PROHIBITION-MATRIX.md`.

---

## 16. Participation-status minimization — explicit

Four different things, and they do not travel together.

| Status                        | Who may know it                                        | Who may never                                            |
| ----------------------------- | ------------------------------------------------------ | -------------------------------------------------------- |
| Eligibility status            | The participant; Eligibility Service                    | The voting domain                                        |
| **Issuance availability**     | The participant; the identity side, as a fact           | The tally side                                           |
| Credential redemption status  | The Credential Issuer; the holder, against a reference  | **The identity domain**                                  |
| Ballot cast status            | PACK-16's voting domain; the participant's own receipt  | **Everyone else, including the identity domain**         |

Normative statements:

1. **The identity-side UI may show eligibility state and issuance
   availability** — that a decision was made, and that access is queued,
   available, used-up-by-entry or expired. It needs the second to prevent
   double participation and to tell the participant what to do next.
2. **The identity side must not receive or display person-level credential
   redemption status or ballot-cast status.** No API returns it to the
   identity side, no event carries it there, no projection derives it, and
   no UI element has a slot for it. "Did this member vote?" is a question
   this system must be unable to answer, and the issuance fact does not
   answer it.
3. **Notifications must not confirm whether a person participated.** "Your
   access for {context} expired unused" is a statement about access the
   recipient was offered and is permitted; "your vote was counted" and "you
   have not yet voted" are person-level participation statements and are
   prohibited.
4. **Operational redemption data remains inside the credential boundary and
   its separated audit stream** (`AS-03`). It is not exported to the
   identity side in aggregate either, because an aggregate scoped narrowly
   enough is a person-level statement.

Privacy-safe wording states the **step of the process**, never the
**content of the vote**, and never presents the absence of a status as a
statement about the participant. The governed German texts are
`PACK-15-CONTENT-CATALOGUE-DE.md`.

---

## 17. WS-03 isolation

PACK-14's `PACK-14-CROSS-WORKSPACE-SESSION-MATRIX.md` §2 stands unchanged
and is confirmed here. Prohibited, structurally and completely, in WS-03:
shared cookies · local identity cookies · localStorage · sessionStorage ·
IndexedDB · cache storage as identity · shared service worker · shared
identity session · parent-domain session · analytics · fingerprinting ·
shared telemetry · shared error-reporting identity · persistent member
identifier · general account ID · membership number · contact data ·
ordinary device identifier · reusable cross-origin token · cross-workspace
frontend state · **persisted assertion or credential material**.

Boundary controls — CSP with `frame-ancestors 'none'` and no third-party
script origin at all; an explicit redirect allow-list; `no-referrer` on
entry and exit; `no-store`; no shared service worker; error reporting by
reason code only; a return navigation carrying neither an identity token
nor a voting-side identifier — are
`PACK-15-CROSS-BOUNDARY-DATA-FLOW-MATRIX.md`.

---

## 18. Cryptographic boundary

| Function                             | Key owner                        | Never the same key or trust root as               |
| ------------------------------------ | -------------------------------- | ------------------------------------------------- |
| Ordinary authentication credential   | `identity-service` (PACK-14)     | Everything below                                  |
| Eligibility assertion integrity      | Assertion Issuer (VC-03)         | Credential issuance; ballot; tally; audit; **and the eligibility decision store** |
| Voting credential issuance           | Credential Issuer (VC-04)        | Assertion; ballot; tally; audit                   |
| Ballot credential                    | **PACK-16**                      | All of the above                                  |
| Ballot encryption                    | **PACK-16**                      | All of the above                                  |
| Tally keys                           | **PACK-16**, Tally Authority     | All of the above                                  |
| Audit / evidence integrity           | `audit-core`, per stream         | All of the above, and not shared between streams  |
| **Evidence bundle signature**        | Audit trust boundary (§20.2)     | All of the above                                  |

**No single key and no single trust root serves two of these functions.**

Required of the implementation round, per function: key ownership; rotation
schedule and procedure; compromise response; signing audience; verification
boundary; key identifiers and resolution; trust-store governance; the
future HSM/KMS boundary; and **test-key restrictions** — a test key must be
structurally incapable of validating in a non-test trust store, and this
must be demonstrated rather than asserted.

**PACK-15 chooses no production cryptographic scheme for ballot casting.**

---

## 19. Timing-correlation controls — `OD-P15-02` closed

The residual named before the correction was that an assertion issued and a
credential minted within the same quiet minute in a low-turnout context are
plausibly the same participation. It is now addressed with governed
controls and **reference default values**, which the implementation round
and its tests bind to.

### 19.1 The controls

| # | Control                          | Where it applies                          |
| - | -------------------------------- | ----------------------------------------- |
| 1 | **Queued issuance**              | Assertion minting → release (VC-03)       |
| 2 | **Coarsened timestamps**         | Every crossing artifact and voting-side record |
| 3 | **Randomized delay**             | Assertion release, and credential minting |
| 4 | **Batching**                     | Assertion release                         |
| 5 | **Minimum cohort**               | Assertion release                         |
| 6 | **No immediate minting for a cohort of one** | Assertion release             |
| 7 | **Explicit small-electorate policy** | Contexts below the small-electorate threshold |
| 8 | **Disclosure-control integration**   | Every operational signal               |
| 9 | **Configurable values with safe lower bounds** | All of the above             |

The long waits happen **before** the participant is told access is
available, so that a participant is never left waiting on a page for a
cohort to fill.

### 19.2 Reference defaults and bounds — `IssuanceTimingProfile`

Every value is governed configuration (`FIR-CONFIG-001`), not a constant.
Every value has a **safe lower bound that configuration cannot go below**;
a configuration outside the permitted range is refused with
`VOTING_CONTEXT_CONFIGURATION_INVALID` rather than clamped silently.

| Parameter                        | Default   | Permitted range        | Hard lower bound | Notes                                                        |
| -------------------------------- | --------- | ---------------------- | ---------------- | ------------------------------------------------------------ |
| `issuance_mode`                  | `queued`  | `queued` only          | —                | **Immediate minting is not a permitted mode**                |
| `timestamp_granularity`          | 300 s     | 60 s … 3600 s          | 60 s             | Applied to `IssuedAt`/`ExpiresAt` and every voting-side record |
| `release_delay_min`              | 30 s      | 10 s … 300 s           | 10 s             | Randomized release, lower edge                               |
| `release_delay_max`              | 300 s     | ≥ 4 × min, ≤ 1800 s    | 60 s             | Randomized release, upper edge                               |
| `release_delay_distribution`     | uniform   | uniform                | —                | Never deterministic; never a fixed offset                    |
| `batch_interval`                 | 120 s     | 60 s … 900 s           | 60 s             | Releases are grouped into intervals                          |
| `batch_max_size`                 | 250       | 50 … 2000              | 50               | An oversized batch is split across intervals                 |
| `minimum_cohort_size` (*k*)      | 5         | 3 … 50                 | 3                | A release batch must contain at least *k* assertions         |
| `cohort_wait_max`                | 3600 s    | 600 s … 21600 s        | 600 s            | The longest an assertion waits for its cohort                |
| `minting_delay_min`              | 5 s       | 2 s … 60 s             | 2 s              | Voting-side, inside WS-03; a participant waits through it    |
| `minting_delay_max`              | 30 s      | ≥ 3 × min, ≤ 300 s     | 10 s             | Same                                                         |
| `small_electorate_threshold`     | 50        | 20 … 200               | 20               | Eligible population below this triggers §19.4                |
| `disclosure_min_cell`            | 5         | ≥ 5                    | 5                | PACK-12's mechanism; never lowered per context               |
| `issuance_window_min_duration`   | 4 h       | ≥ 4 h                  | 4 h              | 24 h for small electorates (§19.4)                           |

### 19.3 Behaviour

1. **Queued release.** A minted assertion enters the queue in status
   `queued`. It is released when its batch interval closes **and** the
   batch holds at least *k* assertions, at a time drawn uniformly from
   `[release_delay_min, release_delay_max]` after the interval boundary.
2. **Cohort of one.** A batch below *k* is **never released immediately**.
   It waits for further assertions until `cohort_wait_max`.
3. **At `cohort_wait_max`.** The assertion is released regardless, at a
   randomized time within a further `release_delay_max` window, and
   `IssuanceCohortThresholdNotMet` is written to the integrity stream with
   the cohort-size **class** (not the exact size). **Access is never
   denied for want of a cohort** — disenfranchising a participant to
   protect their unlinkability is not an acceptable trade.
4. **Window guarantee.** The queue must guarantee release at least
   `cohort_wait_max + release_delay_max` before
   `CredentialIssuanceWindow.end`. A configuration that cannot guarantee
   this is invalid. Requests arriving after that point are released on a
   best-effort delay with a recorded correlation-risk event.
5. **Minting delay.** Inside WS-03, credential minting is delayed by a time
   drawn uniformly from `[minting_delay_min, minting_delay_max]`, with a
   visible waiting state and no countdown pressure.
6. **Coarsening.** `IssuedAt` and `ExpiresAt` on the assertion, and every
   timestamp in `AS-02`, `AS-03` and the redemption records, are coarsened
   to `timestamp_granularity`. Logs record a **timing class**, never a
   microsecond value.
7. **Notification timing.** The "access available" notification is sent on
   the release schedule, not on the decision schedule, so that notification
   metadata does not undo the queue.

### 19.4 Small-electorate policy — explicit

Where a context's eligible population is below
`small_electorate_threshold` (default 50), the following apply and cannot
be relaxed per context:

| Rule                                                                         | Value                                            |
| ---------------------------------------------------------------------------- | ------------------------------------------------ |
| Minimum cohort                                                               | `k = max(3, ceil(0.1 × N))`                      |
| Timestamp granularity                                                        | ≥ 3600 s                                         |
| Issuance window minimum duration                                             | ≥ 24 h                                           |
| Per-scope operational metrics                                                | **None at all** — not thresholded, not delayed   |
| Aggregate credential-processing counts                                       | Published only after `voting_closed`             |
| Disclosure-control suppression                                               | Applies to every published figure, jointly       |
| Context activation                                                           | Requires an explicit governance acknowledgement that the electorate is small and that unlinkability is correspondingly weaker |

**The honest statement that accompanies this policy:** in a body of eleven
people, no timing control makes participation unlinkable to an observer who
knows the eleven. The controls reduce what the *system* discloses; they do
not change what a small group knows about itself. The governance
acknowledgement exists so that this is decided rather than discovered.

### 19.5 What remains residual

Timing correlation is **reduced and bounded, not eliminated**
(`T-P15-13`). Infrastructure and network-level metadata are outside the
application boundary entirely (`T-P15-14`, PACK-17). The strongest answer
— a cryptographic issuance construction in which the issuer cannot
correlate even in principle — remains PACK-16's (`OD-P15-05`), and §5's
design is deliberately the weakest structure achieving exactly-once so that
it can be replaced without redesigning the boundary.

---

## 20. Audit streams and the evidence bundle

### 20.1 Six streams

| Stream                | Contains                                                                                   | Must not contain                                  |
| --------------------- | ------------------------------------------------------------------------------------------ | ------------------------------------------------- |
| `AS-01` Eligibility   | Rule-set version, scoped source references, decision, reason codes, reviewer, evidence ref | Assertion nonce; credential ref; ballot; tally    |
| `AS-02` Assertion     | Minting, queueing, release, pickup, expiry, revocation; context; audience; integrity data  | Identity; credential ref; redemption outcome      |
| `AS-03` Credential    | Issuance, status, revocation, redemption, replay rejection                                 | Identity; assertion ref; ballot; tally            |
| `AS-04` Voting integrity | Boundary violations, correlation-risk detections, cohort-threshold events, integrity checks | **Any identity, in any field**                |
| `AS-05` Independent   | Versioned privacy-preserving evidence bundles                                              | Raw stream access; correlation keys               |
| `AS-06` System        | Service health, key events, configuration changes, privileged acts                          | Participation data; outcome-inferring metrics     |

**No unified audit table may be created**, and no query, export, dashboard,
warehouse, SIEM, backup restore or incident tool may join across the
eligibility-side and voting-side streams.
`PACK-15-AUDIT-SEPARATION-MATRIX.md` is normative.

### 20.2 The independent-auditor evidence bundle — `OD-P15-04` closed

A **versioned, privacy-preserving evidence bundle**, `EvidenceBundle`
schema version `1`, scoped to exactly one voting context.

**Permitted content — a closed list of eight sections:**

1. **Voting-context metadata** — context reference, type, organizational
   scope, windows, revocation cutoff, status history.
2. **Rule-set and configuration versions** — the frozen rule-set version,
   the `IssuanceTimingProfile` values in force, the privacy profile, the
   audit profile, and the version of each stream schema summarized.
3. **Aggregate eligibility totals** — requested, approved, denied by reason
   code, review required, superseded, expired, disputed, dispute outcomes.
4. **Assertion issuance integrity totals** — minted, queued, released,
   picked up, expired unused, revoked, replay rejected; batch count;
   cohort-size **class** distribution.
5. **Credential totals** — issued, revoked (by position relative to the
   cutoff), expired, redeemed, replay rejected, duplicate requests
   rejected.
6. **Integrity commitments and signature metadata** — per-stream integrity
   commitments, the commitment algorithm identifier, the key identifier,
   the signature and its trust-store reference.
7. **Disclosure-control metadata** — the thresholds applied, which cells
   were suppressed, the suppression method, and the complementary
   suppressions applied to prevent differencing.
8. **Bundle provenance** — bundle version, generation time (coarsened),
   generating authority, export authorization reference.

**Prohibited content — normative:** raw identity of any kind · any member
identifier · **any context-scoped pseudonym** · any credential secret or
credential identifier · any assertion identifier or nonce · any ballot data
· any per-participation record · any correlation key spanning two streams ·
any un-suppressed cell below `disclosure_min_cell`.

**Validation.** A bundle is valid only if: it declares a supported schema
version; every section is present or explicitly declared empty; every
per-stream integrity commitment verifies; the signature verifies against
the audit trust store; the **count-consistency checks** hold — redeemed ≤
issued, picked up ≤ released ≤ minted, revoked + expired + redeemed ≤
issued, replay rejections reconcilable with the integrity stream;
disclosure-control metadata is present and its thresholds meet the minimum;
and the bundle is **reproducible by a second auditor** from the same
inputs. A bundle failing any check is rejected, not repaired.

**Versioning.** Within a major version, sections and fields may be added
compatibly; removing a section, narrowing a total or changing a definition
is a new major version. A bundle always states the version of every stream
schema it summarizes, so that an old bundle remains interpretable.

**Export authorization.** Independent Auditor role plus a time-boxed
PACK-12 grant; one context per bundle; **a request naming two contexts or
two streams' raw content is refused**; the export is itself audited to
`AS-05` and `AS-06`. Export **before** the context reaches `voting_closed`
is restricted to sections 1, 2, 6, 7 and 8 — the non-outcome-bearing ones —
and requires dual control, because a pre-closure count is an intermediate
tally (ADR-094).

**Small-cohort suppression.** Any cell below `disclosure_min_cell` (5) is
**suppressed, not rounded**; suppression is flagged; and **complementary
suppression** is applied so that a suppressed cell cannot be recovered by
differencing against totals or against another bundle. Where suppression
would empty a section, the section is declared suppressed as a whole.

---

## 21. Retention and deletion

Per-artifact schedules, legal-hold interaction and deletion obligations are
`PACK-15-PRIVACY-RETENTION-MATRIX.md`. Retention must not permit long-term
cross-context correlation, must not destroy evidence a dispute or audit
requires, must not violate a legal hold, and **must not create a hidden
person-to-ballot linkage**.

Context-scoped pseudonyms and their derivation secrets are destroyed at the
context's retention boundary, and the destruction is an audited act.

Retention *periods* remain PACK-09's (`OD-P15-06`).

---

## 22. Dispute and appeal

Twelve dispute grounds with evidence, reviewer, remedy and limit are
`PACK-15-WORKFLOW-MATRIX.md` §3. Two rules govern all of them: **an appeal
never requires the disclosure of ballot content**, and **the Dispute
Reviewer must not be able to link a person to a ballot** — not through
evidence, not through timing correlation, not through a grant.

---

## 23. Assisted and alternative channels

`FIR-INCLUSION-001`. Specified: assisted eligibility review; in-person
eligibility confirmation; accessibility support; an offline fallback path
for **eligibility**; no operator impersonation; **no operator retention of
credential material — because none exists outside WS-03** (§13.5); an
immutable assisted-action receipt; and helper attribution on every assisted
act.

The hard limit: **assistance must never reveal or control a ballot
choice**, and the accessible path must be an *independent* path. Where it
cannot be, that is a named limitation with an owner.

---

## 24. Official communications

`FIR-DELIVERY-001`. Notification classes: eligibility review required;
eligibility denied; eligibility approved; **access queued**; **access
available**; issuance failed; access expired unused; access revoked before
use; dispute opened; dispute resolved.

Never sent: credential material or any secret over any channel (§13.3);
ballot content; person-level voting status; any confirmation that a person
did or did not participate; any participation information that has not
passed privacy review.

---

## 25. Frontend handoff contract

PACK-15 does **not** build the Voting Client and does not define its
pages. It defines the contract:

```text
[WS-02] authenticated workspace
  → the participant sees the voting context and its window
  → the participant sees their eligibility state, in words, with a reason
  → the participant sees issuance availability: queued / available / expired
  → a denial or review state is shown with its registered reason and next step
  → the participant initiates a one-time handoff
  → the participant leaves the ordinary workspace
[WS-03] isolated voting origin
  → the assertion is picked up; the credential is minted and redeemed
  → no credential material is ever displayed
  → no ordinary identity UI continues
  → no shared navigation, no profile, no account menu, no analytics
  → the return carries no identity-bearing token and no voting-side identifier
```

`FIR-UX-003` … `FIR-UX-011` apply in full. PACK-15 produces the **domain
side** of `FIR-UX-011`'s responsibility split and **none** of its ten
artefacts; **the complete first-page-to-final-page structure is defined
during the relevant `FRONT-PACK Specification + UX/IA` stage, before
frontend implementation.**

---

## 26. Threat model

`PACK-15-THREAT-MODEL.md` covers thirty-nine threats. The four that a
correct-looking implementation is still most likely to fail are
`T-P15-18` (audit-stream joins), `T-P15-13` (timing correlation),
`T-P15-12` (operator correlation) and `T-P15-27` (small-group disclosure).
The correction adds `T-P15-37` (queue side channel), `T-P15-38` (credential
material escaping WS-03) and `T-P15-39` (evidence-bundle differencing).

---

## 27. Failure modes

Eighteen dependencies with fail behaviour, retry semantics, manual path,
user-visible status, evidence and recovery are
`PACK-15-FAILURE-MODE-MATRIX.md`. **Fail closed wherever failing open would
produce a wrong participation, and fail visibly always.** Two dependencies
are never bypassed under any load with any flag: **the audit stream and the
replay store.**

---

## 28. Reason codes

`PACK-15-REASON-CODE-CATALOG.md`. **There is no generic `VOTING_ERROR`, and
none may be added.** Where two failures differ in what the participant must
do next, they are two codes; a code's meaning never changes.

---

## 29. Events

Every event uses **PACK-13's canonical envelope unchanged** (canon §21).
No payload carries ballot content or ordinary identity; **no payload
carries both an assertion reference and a credential reference**; and
`correlation_id` chains terminate at the trust boundary.
`PACK-15-EVENT-CATALOG.md` is the catalogue.

---

## 30. API catalogue

`PACK-15-API-CATALOG.md` catalogues the future versioned contracts. Every
operation declares a `boundary_side`, and no operation may declare both.
**No transport is implemented and no OpenAPI document is produced.**

---

## 31. Canon assessment

```text
CANON AMENDMENT NOT REQUIRED
```

`CANON_VERSION` remains `0.8.0` and the canon file is not modified. The
reasoning, including the six canonical questions raised and closed without
an amendment, is `PACK-15-CANON-ASSESSMENT.md`.

---

## 32. Open decisions — after the architecture correction

**Closed by this correction:**

| ID        | Question                                          | Resolution                                                                      |
| --------- | ------------------------------------------------- | ------------------------------------------------------------------------------- |
| OD-P15-01 | Assertion Issuer packaging                        | **Closed** — §4.3: separately bounded module and storage, separate signing keys and service credentials, no read path to account/person/membership stores, minimized-decision input only, extractable later without contract change |
| OD-P15-02 | Timing-correlation controls                       | **Closed** — §19: nine controls with reference defaults, permitted ranges and hard lower bounds; cohort-of-one never minted immediately; explicit small-electorate policy |
| OD-P15-03 | Context-scoped pseudonym                          | **Closed** — §10.3: default none; permitted only for context-local exactly-once enforcement; per-context, non-reusable, never exposed to WS-03, not reverse-resolvable, governed destruction |
| OD-P15-04 | Auditor evidence bundle                           | **Closed** — §20.2: `EvidenceBundle` v1 with eight permitted sections, a prohibited-content list, validation, versioning, export authorization and complementary small-cohort suppression |
| OD-P15-07 | Credential delivery                               | **Closed** — §13.3–13.5: delivery only inside WS-03; ten prohibited channels; one-time handoff artifact from the ordinary workspace; single-visit issuance; assisted and accessible fallbacks preserve isolation and create no helper custody |

**Remaining open:**

| ID        | Question                                                                                | Owner      | Must close by         |
| --------- | --------------------------------------------------------------------------------------- | ---------- | --------------------- |
| OD-P15-05 | Whether PACK-16 replaces the spent-nonce set with a cryptographic issuance construction, and the migration | **PACK-16** | PACK-16 specification |
| OD-P15-06 | Retention periods per artifact class                                                    | **PACK-09** | Before production     |
| OD-P15-08 | Whether `advisory_consultation` may extend beyond members, and under what governed rule  | **Governance** | Before first advisory use |

**None of the three remaining blocks the acceptance of this
specification**, and none may be closed by an implementation making a
choice quietly.

---

## 33. What this round is not

It is not an implementation. It is not a candidate. It is not a PASS. It
does not create a service, a module, a migration, a test, a contract
fixture or a CI stage. It changes no version and amends no canon. It
integrates no cryptography, no HSM and no KMS. It does not cast a ballot,
count a vote, build a Voting Client or make this system usable for a public
election. It selects no licence and completes no licensing —
`FIR-OSS-001` … `FIR-OSS-006` are register obligations, and this round
neither implements nor claims compliance with any of them.

It draws one boundary carefully, and says exactly what is on each side of
it.

**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**
