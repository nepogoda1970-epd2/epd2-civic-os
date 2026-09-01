# PACK-07 — Decisions requiring explicit owner approval

**Status: all decisions resolved — no open items remain.** The project
owner architecturally approved `docs/handover/PACK-07-SPEC-FINAL.md`
(v3, with the three consistency corrections applied) and acted on
ADR-026 through ADR-031 on 2026-07-25, accepting all six exactly as
drafted, with no further amendment. ADR-028's own dedicated canon-edit
task has since been carried out the same day. **No
`services/membership-service` directory exists; the `eligibility-service`
extension has not begun; no implementation schema, OpenAPI file, or
reason-code registry file exists for PACK-07.** Implementation itself
remains separate and has not begun.

```text
sha256(docs/canonical/TZ-00-domain-event-canon.md) =
  8b378292e075de6ee312c99ba53c37113f9fe395ed8d2c722714008891580f3c
CANON_VERSION = 0.6.0
REPOSITORY_VERSION = 0.6.0
```

`CANON_VERSION` moved `0.5.0 → 0.6.0` (ADR-026 through ADR-031, all
`accepted`) — new canon section 19d ("Участие и членство —
Participation & Membership Context") adds ten new canonical entities
(`ParticipantEligibilityPolicy`, `ProcessEligibilityPolicy`,
`StepUpAuthenticationRequirement`, `DigitalDecision`, `AssemblyDecision`,
`PartyMembershipEligibilityPolicy`, `AffiliationDeclaration`,
`ConflictAssessment`, `MembershipApplication`, `AuthenticationContext`),
extends `IdentityRecord` (7.3) with eight new fields, replaces the
generic `electoral_eligibility_met` concept with four separated
electoral-eligibility claims, and canonicalizes the two-stage membership
admission rule, the widened seven-category human-control hard invariant,
the critical-policy four-gate activation/policy-freeze rule, the
enforcement-mechanism dichotomy (atomic capability check / scoped
capability token), and the `ParticipationRightsProfile`
internal/non-authoritative characterization; section 20 gains a new
event catalog subsection (20.16) and three completing `Membership`
(20.5) event names; sections 22 and 23 gain new ownership-matrix rows
and forbidden-link entries respectively. `REPOSITORY_VERSION` is
unchanged at `0.6.0` — this is a canon-only change, since no
`membership-service` or `eligibility-service` extension code exists
yet, consistent with this project's own established versioning
precedent (every prior canon-only round — PACK-03, PACK-04, PACK-05,
PACK-06 — left `REPOSITORY_VERSION` unchanged until the corresponding
service was actually implemented; see
`docs/handover/PACK-07-CANON-AMENDMENT-REPORT.md` for the full
citation).

## 1. Service decomposition and policy separation (ADR-026) — accepted

`eligibility-service` owns `ParticipantEligibilityPolicy`,
`ProcessEligibilityPolicy`, general participation-rights evaluation,
participant-side capability derivation, and all four electoral/process-
eligibility claims. `membership-service` (new) owns `Membership`,
`PartyMembershipEligibilityPolicy`, `AffiliationDeclaration`,
`ConflictAssessment`, `MembershipApplication`, and party-membership
application/continuing-membership workflows. Participant policy and
party-membership policy remain independently versioned and activated;
`eligibility-service` must not create or mutate party `Membership`;
`membership-service` must not become the owner of general Civic OS
participation eligibility. `ParticipationRightsProfile` remains one
derived, non-stored read model composed from all three services'
results without any one service holding another's raw state, and is
explicitly internal and non-authoritative: it is never the mechanism
that grants or denies an action — the actual enforcement mechanism is
always one of the two patterns ADR-027 fixes. No sub-item was rejected
or amended.

## 2. Cross-service boundaries (ADR-027) — accepted

Every cross-service edge is a narrow, purpose-built read returning only
derived booleans, opaque references, or reason codes: `membership-service`
reads derived identity-eligibility claims from `identity-service` and
Governance authorization for policy activation/consequential decisions;
`eligibility-service` reads only `required_membership_status_met`/
`membership_duration_requirement_met` from `membership-service`, and
gains its first-ever cross-pack read into `identity-service` for the
identity-layer claims underlying the four electoral/process-eligibility
claims it alone computes. Raw `Membership` status, affiliation details,
identity attributes, birth date, citizenship documents, and organization
names are never exposed through any cross-service API; regional scope
stays generic and `Organization` references opaque until PACK-08.
Identity verification is never derived from, substituted for, or used
to infer citizenship — no boundary or claim may restrict verified
participation to German citizens. Step-up authentication is checked
through one narrow, purpose-built `identity-service` function returning
only `authentication_step_up_satisfied` plus a reason code, never a raw
`AuthenticationContext` field. **Exactly two mechanisms may ever grant
or deny an action** — an atomic capability check or a single-purpose
scoped capability token — never a read of `ParticipationRightsProfile`.
Every policy entity this pack introduces is a `critical policy`;
activation requires `governance-service`'s existing authorization read
to additionally confirm `multi_person_approval_met`, without ever
exposing the approver list itself. No sub-item was rejected or amended.

## 3. Canon additions (ADR-028) — accepted

Four separated electoral-eligibility claims
(`active_electoral_eligibility_met`, `passive_electoral_eligibility_met`,
`party_internal_voting_eligibility_met`,
`party_office_candidacy_eligibility_met`) replace the specification's
single generic `electoral_eligibility_met`/`ELECTORAL_ELIGIBILITY_NOT_MET`
everywhere, with no generic operational claim retained anywhere in
canon or in any future implementation. Party membership admission is
mandatory two-stage (formal eligibility evaluation, then an authorized
human decision); a passing evaluation never automatically creates
active membership. Membership data is restricted by default. `IdentityRecord`
gains eight new fields (`date_of_birth`, `citizenship_status`,
`residence_status`, `identity_assurance_level`, `identity_scheme`,
`attribute_verification_level`, `attribute_verified_at`,
`attribute_valid_until`) implementing a strict five-concept separation
(identity assurance, authentication assurance, attribute freshness,
session authentication time/method, provider reference) — no consumer
may treat any of these as interchangeable. A new, versioned
`ProcessEligibilityPolicy` parameterizes every electoral/process-
eligibility evaluation by concrete process, jurisdiction, scope, and
effective date, and carries the legal-effect fields (`decision_effect`,
`formal_confirmation_required`, `formal_confirmation_authority`,
`secret_ballot_required`, `permitted_participation_mode`,
`required_assurance_level`, `accessibility_profile`) supporting at
least `advisory`, `politically_binding`, `internally_binding`,
`legally_final`, and `requires_formal_confirmation`; where formal
confirmation is required, the `DigitalDecision → AssemblyDecision`
lifecycle applies, with a mandatory divergence explanation wherever the
final legal decision differs from the digital result. No current legal
value of any jurisdiction is fixed anywhere in this content. A new,
versioned `StepUpAuthenticationRequirement` (and reusable
`AssuranceRequirement` value shape) parameterizes step-up requirements
per sensitive action, never fixed in code. The hard invariant on
consequential human control is widened to a seventh, open-ended
category — denial of a fundamental member right, however produced,
binding by effect not by label. `AffiliationDeclaration` gains
`valid_from`/`valid_until` (temporal) and `verification_status`/
`verified_at`/`verified_by` (verification, `declared` by default). Four
future packs (Legal Decision Validity; Privacy Governance & DSFA;
Public Verifiability; Accessibility & Assisted Participation) remain
named but unimplemented. No sub-item was rejected or amended.

**Canon edit status:** performed, 2026-07-25, as its own separate,
dedicated task following this acceptance. New canon section 19d
("Участие и членство — Participation & Membership Context") now carries
the content above; `canon_version` moved `0.5.0 → 0.6.0`. See
`docs/handover/PACK-07-CANON-AMENDMENT-REPORT.md` for the exact section
map.

## 4. Reason-code additions (ADR-029) — accepted

The specification's original code list, minus the removed generic
`ELECTORAL_ELIGIBILITY_NOT_MET`, plus the eight new codes
(`ACTIVE_ELECTORAL_ELIGIBILITY_NOT_MET`,
`PASSIVE_ELECTORAL_ELIGIBILITY_NOT_MET`,
`PARTY_INTERNAL_VOTING_ELIGIBILITY_NOT_MET`,
`PARTY_OFFICE_CANDIDACY_ELIGIBILITY_NOT_MET`,
`MEMBERSHIP_HUMAN_APPROVAL_REQUIRED`,
`MEMBERSHIP_DECISION_AUTHORITY_INVALID`,
`MEMBERSHIP_STATUS_DISCLOSURE_PROHIBITED`,
`MEMBERSHIP_PUBLICATION_CONSENT_MISSING`), is accepted exactly as
proposed. No amendment. The generic electoral code is fully replaced
wherever a more precise code applies; no code path may raise it.
Consistent with every prior pack's own precedent (PACK-02 through
PACK-06 alike — canon section 24 has never gained a pack-specific
entry; every pack's additive codes live only in that pack's own
executable `contracts/reason-codes/pack-0N.yml`, created alongside that
pack's service implementation), `contracts/reason-codes/pack-07.yml`
itself remains deferred to the future `membership-service`/
`eligibility-service` implementation round — no code exists yet to
reference these codes by literal, and
`tests/contract/test_reason_codes_registry.py` has nothing to check
them against yet.

## 5. Policy mechanics and human decisions (ADR-030) — accepted

`MembershipApplication` (new) tracks the two-stage admission workflow
through six states (`application_pending`, `eligibility_review`,
`human_decision_pending`, `approved`, `rejected`, `activated`), mapped
onto — but never overloading — `Membership.membership_status` (canon
8.3, left unchanged); no code path may set `Membership.membership_status
= active` except as the `activated` step following a recorded
`approved` `MembershipApplication`. The same two-stage principle applies
symmetrically to suspension, termination/expulsion, and restoration.
The consequential-human-control hard invariant is widened and restated
as structural (section 3, above). Canon's polymorphic `Appeal` (14.3),
with `decision_id` as a polymorphic target reference, is confirmed as
this pack's standing default for `ConflictAssessment`/
`MembershipApplication` appeals and for any further appealable decision
type this pack introduces, overridable only by a dedicated ADR meeting
the same direct-field-inspection proof standard. Where formal
confirmation is required, `DigitalDecision → AssemblyDecision` applies
exactly as specified in ADR-028 (section 3, above); a passed
`confirmation_deadline` never auto-finalizes — silence is never
approval. Every policy entity this pack introduces requires four
independent activation gates (verified `GovernanceDecision`,
`multi_person_approval_met`, a signed policy digest, a transparency-log
commitment) and is subject to a policy-freeze rule once an active
version is in use by an in-progress process. No sub-item was rejected
or amended.

## 6. Security architecture — domain pseudonyms, anti-correlation, Credential Issuer boundary, cryptographic-protocol agility (ADR-031) — accepted

No single, permanent, universal identity hash is computed and reused
across the platform; a `DomainPseudonymReference` concept requires
separate, domain-scoped pseudonymous identifiers for at least five
domains, with no derivation algorithm, key, or implementation selected.
`AntiCorrelationInvariant` elaborates canon's existing
INV-01/CT-00-08/CT-00-09 into an explicit, itemized, fail-closed list
of ten prohibited correlation vectors. Anonymous voting/participation
endpoint isolation, the Identity/Eligibility → Credential Issuer →
Anonymous Ballot/Participation → Tally boundary, and cryptographic-
protocol agility (no specific voting/credential cryptography fixed) are
all accepted as specified. The future cryptographic-protocol gate is
widened from seven to nine items — timing unlinkability and transport
unlinkability added, and "revocation or invalidation semantics"
sharpened to require that revocation itself be privacy-preserving — all
three still gated on a future Verifiable Voting Cryptography pack, no
protocol or vendor selected. Three named future packs (Identity &
Authentication Security; Verifiable Voting Cryptography; Production
Security & Resilience) carry all implementation; this pack implements
none of it. No sub-item was rejected or amended.

**Canon edit status:** performed, 2026-07-25. New canon section 19d.17
names `DomainPseudonymReference`, `AntiCorrelationInvariant`, and
`CryptographicProtocolProfile` and states their governing invariants,
without defining any of the three as a fully fielded canonical entity —
concrete definition remains deferred to a future implementing ADR, per
ADR-031's own item 9.

## 7. Approved future architectural requirement — consequential AI-generated summaries — resolved, implementation deferred

PACK-07 itself introduces no AI-generated summary capability anywhere
in its design — section 1 of the specification and CT-00-11's own "not
applicable" finding are both unaffected. The underlying requirement
raised during drafting is architecturally approved as a future
requirement, stated explicitly in both this document and
`docs/handover/PACK-07-SPEC-FINAL.md` section 24: any consequential
AI-generated summary, wherever in the platform it is eventually
introduced, must support (1) deterministic source-reference mapping
from each material summary segment to its source `Contribution`
references, (2) coverage metadata, (3) explicit human-review status,
and (4) immutable `AIProcessingRecord` linkage. **Implementation, and
any corresponding `AIProcessingRecord` field addition, remain deferred
to a future AI Processing amendment pack (a PACK-06 addendum) and are
not authorized, drafted, or performed by this document, by any of
ADR-026 through ADR-031, or by the canon 0.6.0 edit.** This round makes
no change to PACK-06, its accepted ADRs, or `AIProcessingRecord`'s own
field shape; canon 0.6.0's new section 19d.17 records this future
requirement by reference only, alongside the deferred security
concepts above, without modifying section 17/19c. This item requires
no further owner action; a dedicated PACK-06 addendum ADR is the
correct future vehicle if and when this requirement is actually
implemented.

## 8. Not requiring a decision right now

- Exact API shapes, JSON Schemas, and OpenAPI paths — implementation
  detail once `membership-service`/`eligibility-service` implementation
  begins, not an owner decision.
- Frontend/UI work — out of scope per `docs/handover/PACK-07-SPEC.md`.
- The full `Organization`/`CivicSpace` implementation and regional
  hierarchy — deferred to PACK-08, unchanged.
- Real eIDAS integration or any live external eID provider connection —
  out of scope, unchanged from the specification's own section 29.
- `docs/review/OPEN_QUESTIONS.md` item 10 (additive reason codes never
  folded back into canon) — flagged again by ADR-029, still not
  required for this pack's own Definition of Done.

## 9. What this acceptance round, and the subsequent canon-edit round, do not authorize

Per this task's explicit instructions: no PACK-07 service directory,
implementation schema, OpenAPI file, or reason-code registry file was
created as part of the acceptance round or the follow-on canon-edit
round. `services/membership-service` does not exist; no PACK-02 through
PACK-06 source code was touched. The canon-edit task itself (ADR-026
through ADR-031, `0.5.0 → 0.6.0`) has now been performed, 2026-07-25, as
its own separate, dedicated task — but `membership-service`
implementation and the `eligibility-service` extension both remain
separate, later tasks, gated on the six accepted ADRs and the
now-implemented canon content, but not authorized by either alone.
**Not implemented by this round, restated per the owner's own explicit
instructions:** eID provider integration; cryptographic voting;
anonymous network endpoints; queues; infrastructure; databases;
blockchain; HSM/KMS; production deployment; assembly workflow tooling,
DSFA tooling, public-verifiability infrastructure, or accessibility
infrastructure — none of the seven future packs named across ADR-028
and ADR-031 (Identity & Authentication Security; Verifiable Voting
Cryptography; Production Security & Resilience; Legal Decision
Validity; Privacy Governance & DSFA; Public Verifiability; Accessibility
& Assisted Participation) is scheduled, numbered, or authorized for any
implementation by this round. No signing protocol, transparency-log
technology, capability-token format, or multi-person-approval threshold
is selected or implemented by this round.
