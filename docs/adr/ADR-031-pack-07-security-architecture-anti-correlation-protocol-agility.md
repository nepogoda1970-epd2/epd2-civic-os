# ADR-031: PACK-07 security architecture — domain pseudonyms, anti-correlation, credential-issuer boundary, cryptographic-protocol agility, audit/queue properties, and future-pack boundaries

## Status

`accepted`

## Date

2026-07-24

## Owner decision

Accepted exactly as drafted, 2026-07-25, following architectural
approval of `docs/handover/PACK-07-SPEC-FINAL.md` (v3). No further
amendment: the domain-pseudonym requirement, the anti-correlation
invariant, anonymous-endpoint isolation, the Credential Issuer boundary
restatement, the now-nine-item cryptographic-protocol-agility gate
(fifth amendment, item 6, including timing unlinkability, transport
unlinkability, and privacy-preserving revocation), no-custom-cryptography,
no-mandatory-blockchain, and queue/CQRS safety are all accepted verbatim
(`docs/review/PACK-07-OWNER-DECISIONS.md` section 6).

## Canon implementation (2026-07-25, follow-on task)

Recorded in canon 0.6.0, new section 19d.17: `DomainPseudonymReference`,
`AntiCorrelationInvariant`, and `CryptographicProtocolProfile` are
named and their governing invariants stated, but — consistent with
`docs/handover/PACK-07-SPEC-FINAL.md` section 23's own "identified
only, deferred" framing — none of the three is defined as a fully
fielded canonical entity by this round; concrete definition remains
deferred to a future Identity & Authentication Security pack / a future
Verifiable Voting Cryptography pack's own implementing ADR, per this
ADR's own item 9 (future-pack boundaries). No existing canon entity,
event, or forbidden-link entry outside the new section 19d/22/23
additions is changed.

## Context

The project owner has issued a further, mandatory set of amendments
bearing on architectural and security requirements that go beyond
ADR-026 through ADR-030's own scope (service decomposition, cross-
service boundaries for `eligibility-service`/`membership-service`,
canon field/claim additions, and policy-evaluation mechanics). These
amendments concern: domain-specific pseudonymous identifiers instead of
one universal identity hash; an explicit, itemized prohibition on
correlating identity/credential issuance with anonymous participation
or ballot submission; isolation of the anonymous voting/participation
endpoint; a strengthened statement of the existing Identity → Eligibility
→ Credential Issuer → Anonymous Ballot/Participation → Tally boundary;
cryptographic-protocol agility (no protocol fixed by this pack); an
explicit no-custom-cryptography rule; technology-agnostic immutable-
audit properties; queue/CQRS safety properties for ballot acceptance;
and an explicit statement of which future packs will carry the actual
implementation of all of the above. Per the owner's own routing
instruction (item 13 of the amendment), this content is recorded as one
additional, proposed security ADR, since ADR-026 through ADR-030 —
each scoped to this pack's own participation/membership policy
subject matter — are not the right home for architecture-wide security
and cryptography-agnostic requirements that bear on `credential-service`,
`voting-service`, `tally-service`, and infrastructure this pack's own
two services (`eligibility-service`, `membership-service`) never touch.

None of this content is new invention from nothing: canon already
states, at the principle level, INV-01 ("real participant identity is
never stored alongside secret vote content, delegated-vote records,
anonymous political actions, closed assessments, or ballots; the
Identity contour confirms the right to participate and issues a
limited credential; the Participation contour checks the credential but
must never receive the full `IdentityRecord`") and CT-00-08/CT-00-09
(no identity fields in a participation response; an ordinary
administrator cannot recover an account ID from a `VoteEnvelope`). This
ADR does not restate these as new principles — it elaborates them into
an explicit, itemized, mechanically-checkable list of correlation
vectors and boundary rules, and extends them with genuinely new
concepts (domain-scoped pseudonyms, a protocol-agile cryptographic
abstraction) that canon does not yet name at all.

The project owner has since issued a fifth amendment, strengthening
item 5's future-protocol gate (below) with two additional mandatory
requirements — timing unlinkability and transport unlinkability — and
sharpening its existing "revocation or invalidation semantics" item
into an explicit requirement that credential revocation itself be
privacy-preserving. Both are recorded as gate items on the same future
Verifiable Voting Cryptography pack (item 12B, below) this ADR already
gates every other protocol property on — no new future pack is
introduced, and no protocol, algorithm, or vendor is selected by this
amendment either.

## Problem

Without this ADR: (1) a future implementation could plausibly derive
one permanent, cross-domain identity hash and reuse it everywhere,
which is silently re-linkable the moment two domains compare their
copies of that same hash, even though no single domain ever received
raw identity data — the exact class of error INV-01/CT-00-09 forbid in
principle but do not enumerate mechanically; (2) without an explicit,
protocol-agnostic abstraction, an implementation could hard-code one
cryptographic voting scheme (e.g. a specific blind-signature
construction) directly into this pack's or a future pack's domain
model, making a later, better-reviewed scheme a breaking migration
rather than a version transition; (3) without an explicit prohibition,
a well-intentioned implementer could reach for a bespoke cryptographic
construction "because the general-purpose library doesn't quite fit,"
introducing exactly the kind of unaudited cryptography that has
historically undermined otherwise sound voting-system designs; (4)
without explicit, vendor-neutral audit and queue/CQRS properties, a
future implementation could either over-commit to one vendor (a
specific blockchain or ledger product) the project may not be able to
operate or audit long-term, or under-specify durability (e.g. treating
a message queue or cache as an authoritative ballot store), silently
weakening INV-05 ("history cannot be altered without a trace").

## Considered options

- Option A — leave all of this to a future, unscoped implementation
  pack, with no policy-level or architectural commitment from PACK-07
  at all. Rejected: this would let a future implementer make each of
  these decisions ad hoc, with no cross-pack consistency guarantee and
  no canon-level hook for the eventual concepts (`AuthenticationContext`,
  `DomainPseudonymReference`, `CryptographicProtocolProfile`,
  `AntiCorrelationInvariant`) to attach to.
- Option B (the project owner's decision) — record the architectural
  requirements, invariants, and abstractions now, as `proposed`
  content, explicitly deferring every concrete technology, protocol,
  and implementation choice to three named future packs.
- Option C — fix one concrete cryptographic protocol (e.g. blind
  signatures) and one concrete audit technology (e.g. an append-only
  ledger product) now, so a future pack has less to decide. Rejected
  per the project owner's explicit instruction (items 8–10): naming a
  specific protocol or vendor here would foreclose the "formal threat
  model, audited protocol, external cryptographic review" process
  those choices actually require, and would not be reversible without a
  major migration once real cryptographic material exists.

## Decision

**Option B**, per the project owner's explicit instruction. Every item
below remains `proposed` architectural/policy content; **none of it is
implemented, and no cryptographic protocol, pseudonym algorithm, queue
technology, or audit-storage technology is selected by this ADR.**

### 1. Sector-specific pseudonymous identifiers (item 4)

**Decision:** no single, permanent, universal eID hash is ever computed
and reused across the platform. Canon 7.4 already states the relevant
principle for `Actor` ("Actor ID need not be the same across different
contours") — this ADR extends that principle from `Actor` to the
identity layer itself, with a new, proposed canonical concept,
**`DomainPseudonymReference`**, and makes it a binding requirement
rather than a permitted possibility:

- Separate, domain-scoped pseudonymous identifiers are issued for at
  least five domains: **participant domain**, **membership domain**,
  **eligibility domain**, **credential issuance domain**, and **voting
  domain** (where applicable — voting/credential pseudonymization is
  `credential-service`'s/`voting-service`'s own PACK-02/03 territory,
  referenced here, not re-scoped by this pack).
- **The same person must not be linkable across domains through one
  universal identifier.** Two domains holding two different
  `DomainPseudonymReference` values for the same underlying person must
  not be able to determine, from those values alone, that they refer to
  the same person.
- **Preferred construction, not prescribed as final:** a provider-scoped
  subject identifier, combined with a service-specific pseudonym,
  derived via an HMAC-based (or equivalent keyed, one-way) per-domain
  construction — **subject to formal cryptographic review before any
  implementation**, per item 9, below. This ADR fixes only the
  requirement (domain separation, non-linkability) and the abstract
  reference shape:

  ```text
  DomainPseudonymReference (proposed, abstract shape only):
    domain_code           — one of participant | membership |
                             eligibility | credential_issuance | voting
                             (open string, extensible)
    pseudonym_value        — opaque; never itself a raw identity value
    key_version             — references whichever keyed-derivation
                             configuration produced this value
    issued_at
  ```

  The actual derivation function, its keys, key rotation, and a formal
  proof (or professional cryptographic review) of cross-domain
  non-linkability are **not specified here** — deferred to the future
  Identity & Authentication Security pack (item 12A, below).

- **No homemade cryptographic implementation is prescribed or
  permitted** by this ADR — restated fully in item 9, below.

### 2. Cross-domain correlation prohibition — an explicit invariant (item 5)

**Decision:** a new, proposed canonical invariant,
**`AntiCorrelationInvariant`**, elaborates INV-01/CT-00-08/CT-00-09 into
an explicit, itemized list of prohibited correlation vectors between
identity/credential issuance and anonymous participation or ballot
submission:

- shared user identifiers (the domain-pseudonym requirement, item 1,
  above, is the structural mechanism preventing this);
- shared request identifiers;
- shared trace identifiers;
- shared analytics identifiers;
- exact timestamp correlation (e.g. matching a credential-issuance
  event to a ballot-submission event by comparing near-identical
  timestamps);
- retained IP addresses in the ballot domain;
- browser fingerprinting;
- session cookies shared between an authenticated, identity-bearing
  context and the anonymous endpoint (item 3, below);
- message-order correlation (e.g. inferring identity from the relative
  order credential issuance and ballot submission events were
  processed in a shared queue or log);
- reverse-proxy logs containing identity-bearing metadata alongside
  anonymous-endpoint request records.

**This is a structural, fail-closed invariant, not a best-effort
guideline** — mirroring INV-10's own fail-closed principle: where any
of the above cannot be structurally ruled out for a given
implementation choice (e.g. a shared reverse-proxy log stream), that
choice is not permitted, full stop, rather than accepted with a
documented residual risk. Concrete enforcement (log redaction rules,
network segmentation, proxy configuration) is implementation content
for the future Identity & Authentication Security and Production
Security & Resilience packs (items 12A/12C, below) — this ADR fixes
the invariant's exact scope, not its enforcement mechanism.

### 3. Anonymous endpoint isolation (item 6)

**Decision:** for anonymous voting or other secret participation, the
following are binding architectural requirements, elaborating INV-01's
existing Identity/Participation separation:

- the ballot (or other secret-participation) submission endpoint is
  **logically and operationally separate** from identity and
  eligibility endpoints — a different deployable, a different network
  path, and a different operational access boundary, not merely a
  different code module behind the same edge;
- it must **not receive identity JWTs**, session tokens, or any other
  identity-bearing authentication artifact — only the minimum anonymous
  credential or cryptographic proof (`ParticipationCredential`, canon
  10.1, already scoped this way; a future cryptographic voting
  credential, item 8, below, once specified);
- **logging must exclude identity-bearing and correlatable metadata** —
  extending item 2's invariant to this endpoint's own operational logs
  specifically, not only to cross-domain data flows;
- **administrative access to the anonymous endpoint is separately
  controlled** from administrative access to identity/eligibility
  systems — no single administrative credential or role grants access
  to both sides of the boundary;
- **network and key boundaries must be documented** once a concrete
  deployment exists — this ADR records the requirement that such
  documentation exist, not the documentation itself, which depends on
  infrastructure decisions this pack does not make (item 12C, below).

This requirement governs `voting-service`'s and `credential-service`'s
own future evolution (PACK-02/03 services, unchanged in ownership) —
PACK-07 introduces no new anonymous endpoint itself (neither
`eligibility-service` nor `membership-service` handles secret ballots),
but records this as a binding constraint on how those existing
services, and any future cryptographic-voting pack (item 12B, below),
must evolve.

### 4. Credential Issuer boundary — preserved and strengthened (item 7)

**Decision:** the existing conceptual chain — already implicit in
canon's INV-01 and this project's PACK-02/03 service decomposition
(`identity-service`/`eligibility-service` → `credential-service` →
`voting-service` → `tally-service`) — is restated explicitly as a
binding boundary, strengthened with a precise statement of what each
layer may and may not know:

```text
Identity / Eligibility
        ↓
Credential Issuer
        ↓
Anonymous Ballot or Participation Endpoint
        ↓
Tally / Result
```

- **Identity and Eligibility** (`identity-service`, `eligibility-service`,
  and, per ADR-026/027, `membership-service` for party-specific
  eligibility) know the person and whether the right exists — never the
  ballot content or anonymous participation record.
- **Credential Issuer** (`credential-service`) knows whether the right
  has been issued or consumed (`ParticipationCredential.status`, canon
  10.1, unchanged) — never the person's full `IdentityRecord` (INV-01,
  already binding) and never the ballot content once cast.
- **Anonymous ballot or participation domain** (`voting-service`) knows
  the ballot and the credential's validity — never the person behind
  it (CT-00-09, already binding).
- **Tally** (`tally-service`) knows the accepted encrypted or anonymous
  ballots — never identity, and never (per this pack's own unchanged
  scope) any content this pack's new entities introduce.
- **No service, anywhere in this chain, may reconstruct the complete
  identity-to-ballot link** — restated as an explicit, standing
  invariant this ADR names but does not itself add new enforcement
  machinery for, since PACK-02/03's own CT-00-09 tests and service
  boundaries already implement it; this ADR confirms PACK-07 introduces
  no new entity, read edge, or field capable of weakening that chain
  (`ParticipantEligibilityPolicy`, `ProcessEligibilityPolicy`,
  `PartyMembershipEligibilityPolicy`, `AffiliationDeclaration`,
  `ConflictAssessment`, and `MembershipApplication` — ADR-026/028/030 —
  are all confirmed to have zero read or write edge toward
  `voting-service`/`tally-service`/`VoteEnvelope`, per ADR-027's own
  forbidden-edges section).

### 5. Cryptographic protocol agility (item 8)

**Decision:** PACK-07 does **not** fix Blind Signatures, ElGamal,
homomorphic encryption, mixnets, or zero-knowledge proofs (or any other
specific scheme) as the final protocol for anonymous credentials or
ballot cryptography. A new, proposed, abstract canonical concept,
**`CryptographicProtocolProfile`**, is introduced instead, to let a
future cryptographic-voting pack (item 12B, below) select, version, and
eventually replace a concrete protocol without a breaking change to
this pack's or any consuming pack's own entities:

```text
CryptographicProtocolProfile (proposed, abstract shape only):
  cryptographic_protocol_id
  protocol_version
  proof_scheme              — opaque/open reference; e.g. which
                               zero-knowledge or blind-signature
                               construction, once one is selected
  credential_scheme          — opaque/open reference
  key_version
  verification_profile       — opaque/open reference to whatever
                               verification procedure applies
  protocol_status             — draft | active | superseded |
                               deprecated
  effective_from
  effective_until             — nullable
```

**Any future adoption of a concrete protocol into this abstraction
requires, at minimum** (restated as a binding gate on future
implementation, not merely a recommendation): a formal threat model; an
audited protocol; external cryptographic review; a key-management
design; replay protection; **privacy-preserving revocation or
invalidation semantics** — sharpened by the project owner's fifth
amendment: a revocation or invalidation event must not itself become a
correlation vector (e.g. a naive revocation list that reveals which
specific credential, and by timing, which specific person, was revoked
is not sufficient — the mechanism must be reviewed for this property
specifically, not assumed to have it merely because some revocation
mechanism exists); a documented verification procedure; **timing
unlinkability** — the protocol must structurally prevent linking a
credential-issuance event to a ballot-submission event by their
relative or absolute timing (e.g. through batching, mixing, or
deliberate delay), not merely avoid comparing near-identical
timestamps naively (item 2's own prohibited-vector list already
forbids the naive comparison; this gate item requires the protocol
itself to be robust against more sophisticated timing analysis); and
**transport unlinkability** — the network transport itself must not
allow linking two requests to the same person via connection reuse,
TLS session resumption, IP-address correlation over time, or similar
transport-layer metadata, independent of anything the application layer
does. None of these nine items is performed by this ADR — they are the
Definition-of-Done gate for the future Verifiable Voting Cryptography
pack (item 12B, below).

### 6. No custom cryptography (item 9)

**Decision, restated without qualification:** no proprietary or
homemade voting cryptography; no unaudited blind-signature
implementation; no custom zero-knowledge construction. **Only
established, formally reviewed, and appropriately audited protocols
and libraries may ever be proposed** for adoption into a future
`CryptographicProtocolProfile` (item 5, above) — this applies equally
to the domain-pseudonym derivation function (item 1, above), which,
despite being a comparatively simpler construction than ballot
cryptography, is still subject to the same "no homemade construction,
formal review required" rule before implementation.

### 7. Immutable audit without mandatory blockchain (item 10)

**Decision:** this pack (and no future pack, per this ADR) requires
blockchain, Hyperledger, AWS QLDB, or any other specific vendor or
product for immutable audit. The **required properties** are fixed
instead, technology-agnostically, extending this project's existing
`epd2_audit_core`/`AuditEvent` (canon 18.1) append-only design and
`AuditExportPackage`'s (canon 19a.2) already-established
chain-continuity proof pattern:

- append-only records;
- tamper evidence;
- hash chaining or Merkle commitments, where appropriate;
- signed checkpoints;
- independent backup;
- WORM (write-once-read-many) retention, where legally appropriate;
- reproducible, independent audit verification (mirroring
  `AuditExportPackage`'s own already-established verification-semantics
  discipline, canon 19a.2);
- separation of administrative duties (no single administrator can
  both write and independently re-verify the same audit trail).

**Technology selection is deferred to a future infrastructure/security
ADR** (part of the Production Security & Resilience pack, item 12C,
below) — this ADR fixes only the required properties.

### 8. Queue and CQRS safety (item 11)

**Decision:** no assumption anywhere in this pack's design, or any
future pack's design building on it, treats Kafka, RabbitMQ, or any
other message queue as the authoritative store for an accepted ballot.
For critical ballot acceptance (a future `voting-service`/cryptographic-
voting-pack concern, referenced here as a binding constraint on that
future work), the following properties are required, technology-
agnostically:

- durable acceptance semantics (a ballot is not considered accepted
  until durably fixed in its actual system of record);
- idempotency;
- replay handling;
- duplicate prevention;
- acknowledgement issued only after durable fixation, never before;
- an audit receipt or cryptographic acceptance evidence returned to the
  submitter;
- recovery after partial failure (a crash between "received" and
  "durably fixed" must never silently accept or silently lose a
  ballot);
- exact source-of-truth ownership, explicitly documented for whichever
  storage technology is eventually chosen.

**Redis or any other cache system must never be the source of truth
for:** eligibility, accepted ballots, final tally, membership status,
or audit history — restated explicitly, covering both this pack's own
new entities (`Membership`, `MembershipApplication`,
`ParticipantEligibilityPolicy`, `ProcessEligibilityPolicy`,
`PartyMembershipEligibilityPolicy`) and the pre-existing canonical
entities this rule already implicitly governed
(`EligibilityDecision`, `VoteEnvelope`, `Tally`, `AuditEvent`).

### 9. Future pack boundaries (item 12)

**Decision:** PACK-07 introduces **only** policy and architectural
requirements (this ADR, and ADR-026 through ADR-030). Implementation of
every concrete technology, protocol, and deployment decision named
above is explicitly deferred to three named future packs — none of
which is numbered or scheduled by this ADR, and none of which PACK-07
authorizes any code for:

**A. Identity & Authentication Security pack** — eID provider adapter(s);
step-up authentication (ADR-027/028/030's own policy model, item 1);
assurance levels (`identity_assurance_level`/`authentication_assurance_level`,
ADR-028); attribute freshness (`attribute_verification_level`/
`attribute_verified_at`/`attribute_valid_until`, ADR-028); domain-specific
pseudonyms (item 1, above); a secure session model.

**B. Verifiable Voting Cryptography pack** — the formal threat model;
anonymous credentials or blind signatures; encrypted ballots;
homomorphic tally or mixnet evaluation; zero-knowledge proofs; a
receipt and verification model; coercion-resistance analysis; a key
ceremony; external audit; timing unlinkability; transport unlinkability;
privacy-preserving credential revocation — all gated on item 5/6's
abstraction and no-custom-cryptography rule, above.

**C. Production Security & Resilience pack** — API gateway; rate
limiting; DDoS protection; WORM audit implementation; SIEM; secrets
management; HSM/KMS; queues; CQRS; backups; disaster recovery;
operational monitoring — all gated on item 7/8's technology-agnostic
property requirements, above.

**This pack (PACK-07) does not implement, and does not authorize
implementation of:** eID provider integration; cryptographic voting;
anonymous network endpoints; queues; infrastructure; databases;
blockchain; HSM/KMS; or production deployment of any kind — restated,
unqualified, per the project owner's explicit instruction (item 15).

## Canon content this ADR identifies (not authorized for implementation, and not performed)

Extending ADR-028's own "canon content this ADR authorizes" list with
the concepts this ADR introduces, all similarly gated on a separate,
dedicated, later canon-edit task and on their own future implementing
ADRs (items 12A/12B/12C, above) — **none of the following is added to
canon by this ADR, and this ADR does not itself authorize their
implementation, only identifies that they would need canon
definitions once a future pack actually specifies them:**

- `DomainPseudonymReference` (item 1) — abstract shape only, no
  derivation algorithm.
- `AntiCorrelationInvariant` (item 2) — a new, explicit, itemized
  invariant, elaborating INV-01/CT-00-08/CT-00-09 rather than
  replacing them.
- `CryptographicProtocolProfile` (item 5) — abstract shape only, no
  concrete protocol.

`AuthenticationContext`, `AssuranceRequirement`, and
`AttributeFreshnessRequirement` are ADR-028's own canon-concept
proposals (its own "Canon content this ADR authorizes" list), not
duplicated here.

## Consequences

No PACK-07 code, service, schema, or canon edit is affected by this
ADR — its entire content is a security-architecture and future-pack
scoping decision. Three future packs (Identity & Authentication
Security; Verifiable Voting Cryptography; Production Security &
Resilience) are now named, with their own gating Definition-of-Done
items (item 5's now-nine-item cryptographic gate, widened by the fifth
amendment with timing unlinkability, transport unlinkability, and
privacy-preserving revocation; item 7/8's technology-agnostic property
lists), for the project owner to schedule independently of this pack's
own remaining ADR acceptance/canon-edit/implementation sequence.

## Security impact

This ADR is, in its entirety, a security-impact decision. It closes
four distinct classes of future error: (1) a single, cross-domain
identity hash silently re-linking a person across domains (item 1); (2)
an under-specified or ad hoc correlation surface between identity and
anonymous participation (item 2); (3) an anonymous endpoint that
accidentally shares infrastructure, logging, or administrative access
with an identity-bearing system (item 3); and (4) a prematurely fixed
or homemade cryptographic protocol that cannot be replaced without a
breaking migration, or that was never formally reviewed at all (items
5–6). It also prevents a false sense of durability from an
under-specified queue/cache architecture (item 8) and avoids
vendor lock-in for audit technology (item 7). The fifth amendment closes
a fifth: a future protocol that resists naive timestamp/IP correlation
(item 2's own prohibited-vector list) could still leak correlation
through more sophisticated timing analysis, transport-layer metadata,
or a naively-designed revocation mechanism — item 5's now-nine-item
gate requires the eventual protocol to be reviewed against exactly
these three properties specifically, not merely assumed to have them
because the naive vectors are already closed.

## Data impact

No new field on any existing canonical entity. Three new, abstract,
proposed canonical concepts (`DomainPseudonymReference`,
`AntiCorrelationInvariant`, `CryptographicProtocolProfile`) — none
implemented, none with a concrete algorithm, protocol, or vendor
selected.

## Migration impact

None — no code, service, or canon content exists yet for any concept
this ADR introduces.

## Reversibility

Fully reversible at this stage — this ADR fixes requirements and
abstractions, not implementations. Once a future pack selects a
concrete pseudonym-derivation function, cryptographic protocol, audit
technology, or queue architecture within these abstractions, reversing
that specific choice would carry whatever migration cost is normal for
replacing a cryptographic or infrastructure component — but the
abstractions themselves (`DomainPseudonymReference`,
`CryptographicProtocolProfile`) are specifically designed, per items
1/5, to make that future replacement a version transition rather than a
breaking change.

## Related canon version

Authored against canon version `0.5.0`. Proposes no canon change
itself — identifies three new canon-concept candidates (above) for a
future, separate canon-edit task, gated on their own future
implementing ADRs (items 12A/12B/12C), not on this ADR's own
acceptance.
