# ADR-028: Canon 0.6.0 (proposed) — Participation and Membership Policy context additions

## Status

`accepted`

## Date

2026-07-24

## Owner decision

Accepted exactly as drafted, 2026-07-25, following architectural
approval of `docs/handover/PACK-07-SPEC-FINAL.md` (v3). No further
amendment: the ten new canonical entities, the eight new `IdentityRecord`
fields, the four separated electoral-eligibility claims, the
`AffiliationDeclaration` temporal/verification fields (item 11), the
critical-policy classification and its two new fields per entity (item
12), and the hard invariant on denial of a fundamental member right
(item 10) are all accepted verbatim. This acceptance authorizes the
dedicated canon-edit task below; it does not itself authorize any
service code (`docs/review/PACK-07-OWNER-DECISIONS.md` section 3).

## Canon implementation (2026-07-25, follow-on task)

Carried out in the same acceptance round: `docs/canonical/TZ-00-domain-event-canon.md`
canon version `0.5.0 → 0.6.0`, new section 19d ("Участие и членство —
Participation & Membership Context"), inserted between existing
sections 19c and 20 (the same non-renumbering technique used for 19a,
19b, and 19c). New section 22 ownership-matrix rows for all ten new
entities; new section 23 forbidden-link entries; new section 20.16
event catalog; three new `Membership` (20.5) event names
(`membership.terminated`, `.rejected`, `.expired`) completing its
existing status-transition coverage, with `Membership`'s own fields,
statuses, and owner (8.3) otherwise unchanged. `REPOSITORY_VERSION` is
unchanged (`0.6.0`) — no `membership-service` or `eligibility-service`
extension code exists yet; this is a canon-only change, per this
project's own established versioning precedent (see
`docs/handover/PACK-07-CANON-AMENDMENT-REPORT.md`).

## Context

`docs/handover/PACK-07-SPEC.md` sections 7, 8, 9, 11, 12, 15, and 24
proposed: a single `electoral_eligibility_met` derived claim; an
implicit single-stage membership-admission model (a passing eligibility
evaluation feeding directly into `Membership.membership_status`); no
explicit default-visibility rule for membership/affiliation/conflict
data beyond the general privacy table in section 14; and a canon
`0.5.0 → 0.6.0` minor bump (section 24) for the `IdentityRecord`
extensions and four new entities. The project owner has reviewed this
proposal and requires four amendments before this content may be
written into canon: separated electoral-eligibility claims, a mandatory
two-stage admission process, an explicit membership-privacy default,
and confirmation that the immutable policy-version/`ConflictAssessment`
semantics the specification already proposed are preserved.

The project owner has since issued two further, mandatory amendments,
both incorporated directly into this ADR's own Decision text as items 5
and 6, below: (5) identity verification must never be modeled or
conflated as citizenship — they are separate canonical concepts, with
extensible, non-exhaustive verification routes, and no rule anywhere in
this pack's design may restrict verified participation, party-
membership application, or party membership to German citizens; and (6)
electoral and process eligibility must never be modeled as one
permanent attribute of a person — a new, versioned policy entity,
`ProcessEligibilityPolicy`, must parameterize every electoral/process-
eligibility evaluation by process type, jurisdiction, territorial
scope, effective date, and policy version, with historical
determinations remaining reproducible against the policy version they
were actually decided under.

The project owner has since issued a further, mandatory set of
amendments concerning step-up authentication and a strictly separated
identity-assurance/authentication-assurance/attribute-freshness model,
incorporated directly into this ADR's own Decision text as items 7 and
8, below. These amendments also rename this ADR's own item 5 field,
`identity_verification_method`, to **`identity_scheme`** — the name
the owner's own amendment uses — with no change in meaning: it remains
the open, extensible record of which verification route was actually
used, distinct from `verification_provider` (the technical integration)
and from citizenship.

The project owner has since issued a fourth, mandatory amendment,
incorporated directly into this ADR's own Decision text as item 9,
below: every participation or voting process must declare its own
legal and organizational effect (`decision_effect` and related
fields), and no digital result may be assumed legally final by
default — where formal confirmation is required, a separate, explicit
`DigitalDecision → AssemblyDecision` confirmation lifecycle applies,
never collapsed into the digital result itself.

The project owner has since issued a fifth, mandatory set of
amendments, incorporated directly into this ADR's own Decision text as
items 10 through 12, below: (10) a hard invariant, widened from item
2's own two-stage admission rule, that no final membership deprivation,
suspension, expulsion, incompatibility decision, or denial of a
fundamental member right may ever be produced solely by automated
policy evaluation; (11) two new temporal fields and three new
verification fields on `AffiliationDeclaration`; and (12) a
`critical policy` classification covering every policy entity this
pack introduces, with two new fields recording a signed policy digest
and a transparency-log commitment for each critical-policy activation
(mechanics and the corresponding multi-person-approval requirement
fixed by ADR-030; the corresponding narrow-read boundary consequence
fixed by ADR-027).

## Problem

A single `electoral_eligibility_met` boolean would conflate four
genuinely distinct legal questions — the right to vote publicly, the
right to stand publicly, the right to vote internally within a party,
and the right to stand for a party office — into one flag, which is
exactly the kind of collapsing this pack's own item 6 instruction
(citizenship "not reduced to a single boolean") already warns against
for a different dimension. Separately, if a passing
`PartyMembershipEligibilityPolicy` evaluation could, by itself, move
`Membership.membership_status` to `active`, party admission would
become fully automatable — contradicting item 8's "no automated system
may permanently reject or expel" principle by omission (an automated
_admission_ is the mirror-image gap that principle did not explicitly
close). Finally, without an explicit default-visibility rule, a future
implementation could reasonably assume `Membership.membership_status`
being "already public-shaped" in canon 8.3 means it is public by
default — the opposite of what party-membership data protection
actually requires. Separately, without an explicit separation between
identity verification and citizenship, a future implementation could
plausibly treat a successful eID verification (any route) as proof of
German citizenship — silently and wrongly excluding verified EU/EEA
participants from processes they are legally entitled to join. Finally,
without a versioned, process-parameterized policy entity for electoral/
process eligibility, a future implementation might store a single
"electorally eligible" fact per person, which would produce the wrong
answer the instant that same person is evaluated against a second
process with different jurisdiction, scope, or legal-basis rules — and
would have no way to reproduce a past determination once policy
changes. Separately, without a strict separation between identity
assurance, authentication assurance, and attribute freshness, a future
implementation could treat "the person was verified once, at some
assurance level, at some point in the past" as sufficient authorization
for a sensitive action taken much later in a much weaker session —
silently permitting a stale or weakly-authenticated session to perform
an action that should have required a fresh, step-up authentication
event. Finally, without an explicit `decision_effect`/formal-
confirmation model, a future implementation could silently assume every
digital participation result is legally final by default, or conflate
"physical presence" with "legally valid" as a universal rule — either
of which would misrepresent a merely advisory or internally-binding
digital result as legally final, or wrongly block a legally valid
all-digital process that applicable law, statute, or jurisdiction
actually permits. Separately, item 2's own two-stage admission rule, as
originally scoped, named only admission, rejection, suspension,
termination/expulsion, incompatibility finding, and restoration —
leaving "denial of a fundamental member right" that does not squarely
fit one of those six labels (e.g. a policy evaluation that would
otherwise silently and permanently withhold a right without ever
routing through one of the six named actions) as an unstated gap a
future implementation could exploit by mis-labeling a consequential
action to avoid the human-decision requirement. Separately, without
temporal and verification fields on `AffiliationDeclaration`, a stale
or never-verified declaration could feed a `ConflictAssessment`
indefinitely, with no way to express that a declared affiliation has
since ended or was never independently confirmed. Finally, without an
explicit `critical policy` classification and stronger activation
safeguards, a single compromised or mistaken approver, an unsigned
policy version, or an unpublished activation could each, individually,
let a policy governing fundamental participation or membership rights
take effect with materially weaker assurance than this pack's other
invariants already require for consequential membership decisions.

## Considered options

- Option A — adopt the specification's sections 7–15/24 exactly as
  drafted: one `electoral_eligibility_met` claim, implicit single-stage
  admission, no explicit privacy-default rule beyond section 14's
  general table.
- Option B (the project owner's decision) — four separated electoral-
  eligibility claims; a mandatory two-stage admission process with a
  new decision record; an explicit restricted-by-default privacy rule
  for membership data; confirmation that the specification's own
  immutable policy-version/`ConflictAssessment` semantics are preserved
  unchanged; identity verification modeled as strictly separate from
  citizenship, with an extensible, non-exhaustive set of verification
  routes and no citizenship restriction on verified participation; and
  a new, versioned `ProcessEligibilityPolicy` entity parameterizing
  every electoral/process-eligibility evaluation by process, jurisdiction,
  scope, date, and policy version; a strict separation of identity
  assurance, authentication assurance, and attribute freshness, with a
  versioned step-up authentication policy for named sensitive actions;
  and an explicit `decision_effect`/formal-confirmation model so that no
  digital process result is assumed legally final by default.

## Decision

**Option B**, per the project owner's explicit instruction. **Per this
task's own instruction, canon `0.5.0` is not edited as part of this
ADR reaching `accepted` status** — this ADR authorizes the canon
content below to be added in a separate, dedicated, later task, mirroring
ADR-010/013/018/023's own precedent. That edit has **not** been
performed here; canon checksum and `canon_version` remain unchanged at
`0.5.0` as of this drafting.

### 1. Separate electoral eligibility claims (replacing the specification's single `electoral_eligibility_met`)

The specification's section 15 `electoral_eligibility_met` claim, and
section 8's `residence_status.electoral_eligibility_declared` input
feeding it, are both retained as **inputs**, but the single **output**
claim is replaced with four independent, separately-derived booleans:

- **`active_electoral_eligibility_met`** — the right to vote in the
  applicable public electoral process (e.g. a formally recognized
  public election or referendum this platform's process concerns).
- **`passive_electoral_eligibility_met`** — the right to stand as a
  candidate in that same public electoral process.
- **`party_internal_voting_eligibility_met`** — the right to vote in
  internal party decisions (e.g. `can_vote_as_party_member`'s own
  underlying eligibility condition).
- **`party_office_candidacy_eligibility_met`** — the right to stand for
  a party office (e.g. `can_stand_for_party_office`'s own underlying
  eligibility condition).

Each claim is derived independently — from citizenship, residence,
age, and (for the two party-internal claims) current `Membership`
status and `PartyMembershipEligibilityPolicy` conditions — under
whichever policy version is active for the specific action being
evaluated. **No single field or flag ever represents "electoral
eligibility" generically** — every consumer must state which of the
four questions it is actually asking. This mirrors, and extends to a
new dimension, item 6's own citizenship rule ("not reduced to a single
boolean") and this project's established discipline of naming derived
claims precisely rather than generically (compare
`age_requirement_met`/`citizenship_requirement_met`/
`residence_requirement_met` each remaining separate claims, section
14).

**Ownership, per ADR-026/ADR-027, amended by item 6 below:** all four
claims are computed by **`eligibility-service`**, applying the active
`ProcessEligibilityPolicy` version (item 6, below) — never by
`identity-service` (which supplies only verified facts, never a
process-eligibility decision, per item 6) and never by
`membership-service` (which is read _from_, not the computing party,
for the two party-internal claims). `active_electoral_eligibility_met`
and `passive_electoral_eligibility_met` are resolved using only
identity-layer facts (age, citizenship, residence, territorial scope)
read via `eligibility-service`'s own new narrow read into
`identity-service` (ADR-027), since public electoral eligibility never
depends on party membership. `party_internal_voting_eligibility_met`
and `party_office_candidacy_eligibility_met` are resolved by
`eligibility-service` combining that same identity-layer read with the
existing `eligibility-service → membership-service` narrow read
(`required_membership_status_met`/`membership_duration_requirement_met`,
ADR-027) — no new read edge is introduced for this purpose, and
`membership-service` never computes an electoral-eligibility claim
itself. This corrects, and supersedes, this item's original drafting
(which had proposed `membership-service` as the computing party for the
two party-internal claims) — the correction is required by item 6's
process-eligibility policy model, below, which centralizes all
process-scoped electoral evaluation in `eligibility-service`, the
service canon 5.2 already names as answering exactly "does a confirmed
participant have the right to participate in a concrete process."

### 2. Party membership admission — mandatory two-stage process

`Membership.membership_status` (canon 8.3) may never move directly
from an application state to `active` as the automatic output of a
policy evaluation. Admission is always:

- **Stage A — formal eligibility evaluation.** `membership-service`
  evaluates the applicant against the currently-active
  `PartyMembershipEligibilityPolicy` (age, citizenship, residence,
  incompatibility, membership-duration-not-applicable-yet) and produces
  a formal eligibility result, carrying its own `reason_codes` where the
  result is negative. **A passing Stage A result never, by itself,
  creates or activates a `Membership` row.**
- **Stage B — authorized human membership-application decision.** A
  `Membership` row may reach `active` status only after an explicit,
  approved membership decision, carrying:
  - a decision-maker or competent-body reference (an opaque reference to
    the authorized human or body making the decision — a `RoleAssignment`
    reference where the decision is made by a role-holder, or an
    equivalent competent-body reference where party statutes designate a
    collective body, e.g. an executive committee);
  - the `policy_version` (of `PartyMembershipEligibilityPolicy`) that
    Stage A was evaluated against;
  - a `reason_code`;
  - `decided_at`;
  - an audit reference (`AuditEvent`, via `epd2_audit_core`, unchanged
    project-wide convention).

**A new record type, distinct from `Membership` itself, carries this
two-stage process** — see item 3 of section 30's ADR-030, which resolves
the exact status-mapping and whether a new `MembershipApplication`/
decision entity is introduced, rather than overloading
`Membership.membership_status` with process-intermediate values it was
never designed to carry. This ADR fixes the **rule** (two-stage,
human-decision-gated admission); ADR-030 fixes the **mechanics**
(exact entity/status shape).

**The same two-stage principle applies symmetrically to suspension,
termination/expulsion, and restoration** — mirroring item 8's existing
"no automated system may permanently reject or expel" rule (section 26
of the specification, unchanged), now explicitly extended to admission
as its own, separately-stated rule rather than left as an unstated
mirror image.

### 3. Membership privacy — restricted by default

`Membership` and its related records are **restricted by default**,
not public by default, notwithstanding canon 8.3's own
already-public-shaped `membership_status` enum. The following facts
must **not** be public by default:

- the existence or status of a membership application;
- active membership;
- suspension;
- rejection;
- termination;
- membership history (any record of a past, non-current membership
  state).

**Cross-service and public outputs use only the minimum derived
claims** already established by this specification and this ADR — e.g.
`required_membership_status_met` (ADR-027), the four electoral-
eligibility claims (item 1, above), or `ParticipationRightsProfile`'s
own boolean fields (section 15) — never a raw `membership_status`
value, application record, or history listing.

**Publication is permitted only through one of:**

- an explicit legal basis (e.g. a statutory public-register
  requirement);
- a statutory requirement specific to the applicable jurisdiction or
  party form;
- a public-office/candidacy rule (e.g. a candidate's party affiliation
  being a legally required disclosure for that specific candidacy);
- informed, voluntary consent from the subject.

No default publication path exists absent one of the four bases above
— this is a **structural default**, not merely a documented
recommendation: any future implementation exposing membership status
publicly must be able to point to which of the four bases applies,
mirroring `DisclosurePolicy`'s own "missing/ambiguous defaults to
`prohibited`" rule (canon 19a.3, ADR-013/ADR-015) rather than
`Membership`'s own already-public-shaped status enum being read as an
implicit disclosure default.

### 4. Preserve immutable policy-version and `ConflictAssessment` semantics — confirmed unchanged

The specification's own immutability guarantees are **confirmed,
unamended, and carried forward into canon exactly as proposed**:

- **Policy versioning (section 12):** exactly one `active` version per
  `(policy_type, scope_type, scope_id)` tuple; every superseded version
  remains immutable and queryable; corrections are always a new
  `policy_version` via `supersedes_policy_id`, never an in-place edit —
  unchanged from `GovernancePolicy`'s own established pattern (canon
  19b.2).
- **`ConflictAssessment` (section 11):** the `pending → under_review →
resolved_*/appealed/overturned/expired_reevaluation_due` lifecycle,
  the mandatory `reviewed_by_role_reference` and (for
  `resolved_incompatible`) `decision_authority_reference`, and the
  `supersedes_conflict_assessment_id` immutable-correction mechanism are
  all unchanged from the specification's own section 11 design.

Nothing in this ADR reopens or weakens either guarantee; item 2's
two-stage admission process and item 1's four electoral-eligibility
claims are additions layered on top of these already-immutable
structures, not replacements for them.

### 5. Identity verification is not citizenship — separate concepts, extensible verification routes, no citizenship restriction

**Decision, per the project owner's explicit instruction.** `IdentityRecord`
(7.3) models nine distinct concepts, never conflated with one another:

1. **Identity verification** — canon's existing `verification_status`
   (7.3, unchanged) — whether this specific identity was successfully
   verified, independent of who the person is a citizen of.
2. **Identity assurance level** — **`identity_assurance_level`**
   (renamed from the specification's own `eid_assurance_level`, section
   9, Design decision D2 — see item 8, below, for the rename rationale:
   `none | low | substantial | high`, modeled on eIDAS assurance
   levels, not itself an eIDAS protocol integration, and now named for
   the general, protocol-agnostic concept since a future pack may add
   non-eID verification routes under the same assurance scale, per
   ADR-031's cryptographic-protocol-agility principle).
3. **Identity scheme/provider** — a new field, **`identity_scheme`**
   (renamed from this item's original drafting, `identity_verification_method`
   — see Context, above; open string, deliberately extensible, never a
   closed enum), recording _which_ verification route was actually
   used, distinct from canon's existing `verification_provider` (7.3,
   unchanged — the technical provider integration) and carrying no
   citizenship implication whatsoever.
   Expected initial values, illustrative and non-exhaustive: `de_personalausweis_online`
   (the German Personalausweis's own online authentication function);
   `eu_eea_eid_card` (a German eID card issued to an eligible EU/EEA
   national under the applicable domestic implementing rule);
   `eidas_foreign_eid` (a supported foreign national eID, notified
   under the eIDAS Regulation); `other_approved_method` (any further
   route a future policy approves). **This list must never be treated
   as closed or exhaustive** — a new route is added by extending the
   open string's accepted values at the repository-configuration
   level, never by a canon edit, mirroring `action_code`/`affiliation_type`'s
   own already-established open-string, extensible-by-configuration
   pattern (sections 7, 10 of the specification).
4. **Citizenship** — `citizenship_status` (section 8, unchanged: a list
   of citizenships, supporting statelessness and multiple citizenship —
   never a single boolean).
5. **Residence status** — `residence_status.residence_type` (section 8,
   unchanged).
6. **Habitual residence** — one value of `residence_status.residence_type`
   (`habitual_resident`, section 8, unchanged) — its own distinct
   concept, not a synonym for permanent residence or citizenship.
7. **Territorial connection** — `residence_status.territorial_connection`
   (section 8, unchanged) — the generic, non-enumerated scope reference
   feeding `territorial_scope_requirement_met`/`scope_requirement_met`
   (ADR-027, item 6, below).
8. **Active electoral eligibility** — `active_electoral_eligibility_met`
   (item 1, above, now process-scoped per item 6, below).
9. **Passive electoral eligibility** — `passive_electoral_eligibility_met`
   (item 1, above, now process-scoped per item 6, below).

**Binding rules, restated without qualification:**

- **No rule anywhere in this pack's design may equate a successful
  identity verification — through any route — with German citizenship,
  or with any specific citizenship.** `identity_verified` and
  `identity_assurance_requirement_met` (ADR-027) are derived
  exclusively from `verification_status`/`identity_assurance_level`
  (renamed from `eid_assurance_level`, item 8, below); they
  never feed, substitute for, or are derived from
  `citizenship_requirement_met`.
- **No rule anywhere in this pack's design may restrict verified
  participation, party-membership application, or party membership to
  German citizens.** A citizen of another EU/EEA state, once
  identity-verified through any supported route, may become a verified
  participant, a party-membership applicant, or a party member —
  subject only to whichever `ParticipantEligibilityPolicy`/
  `PartyMembershipEligibilityPolicy`/`ProcessEligibilityPolicy`
  conditions and legal requirements actually apply (policy values,
  never fixed here — section 25/ADR-030 item 1, unchanged).
- **Multiple citizenships are never collapsed into a single German/
  non-German boolean** — restated, unchanged from section 8/9.
- **Raw identity documents, full citizenship records, exact address, or
  full date of birth are never distributed across services** — this
  extends section 14's existing raw/derived split (which already names
  `date_of_birth`/`citizenship_status`/`residence_status`/
  `identity_assurance_level` (renamed from `eid_assurance_level`, item
  8, below) as never-raw-exposed) to also cover identity
  documents and exact address as a standing prohibition, should either
  ever be modeled by a future field — no such field is proposed by this
  ADR.

### 6. Process-specific electoral and participation eligibility — a new, versioned `ProcessEligibilityPolicy`

**Decision, per the project owner's explicit instruction.** Electoral
and process eligibility is never modeled as one permanent attribute of
a person. A new, versioned, proposed canonical entity,
**`ProcessEligibilityPolicy`**, parameterizes every evaluation of the
four electoral/process-eligibility claims (item 1, above) by a concrete
`(process_type, jurisdiction, scope_type, scope_id, effective_date)`
tuple, resolved against exactly one applicable policy version.

**Fields** (mirroring `ParticipantEligibilityPolicy`/
`PartyMembershipEligibilityPolicy`'s own established shape, sections 12,
extended with the process/jurisdiction dimensions this entity uniquely
needs):

```text
ProcessEligibilityPolicy:
  policy_id
  policy_version
  status                          — draft | active | superseded
  process_type                    — open string; see the nine
                                     categories below
  jurisdiction                    — open string; e.g. a country or
                                     supranational-body code — never an
                                     enumerated hierarchy (structure
                                     only, per section 17/29)
  scope_type                      — open string; e.g. federal, land,
                                     municipal, epd_platform_wide,
                                     epd_organization (structure only)
  scope_id                        — opaque, nullable
  eligible_citizenship_set        — list of ISO 3166-1 codes, or a
                                     citizenship rule reference — never
                                     a single boolean (mirrors section
                                     8's own citizenship_conditions)
  residence_rule                  — structured condition, mirrors
                                     section 8's residence_conditions
  habitual_residence_rule         — structured condition, distinct from
                                     residence_rule (item 5, above)
  minimum_age                     — integer | null
  active_electoral_eligibility_rule    — structured condition
  passive_electoral_eligibility_rule   — structured condition
  party_internal_voting_rule           — structured condition,
                                          nullable for non-party
                                          process types
  party_office_candidacy_rule          — structured condition,
                                          nullable for non-party
                                          process types
  effective_from
  effective_until                 — nullable
  legal_basis                     — open string/reference; e.g. a
                                     statute or party-statute citation
                                     — illustrative only, never a fixed
                                     value (item 12, below)
  adopted_by                      — non-nullable; a `GovernanceDecision`
                                     reference, mirroring section 13's
                                     governance-boundary rule
  supersedes_policy_id            — nullable; corrections are always a
                                     new version, never a rewrite
```

**Supported process categories** (open string, extensible, at least
these nine): `bundestag_election`, `european_parliament_election_de`,
`land_election`, `municipal_district_election`,
`epd_public_consultation`, `epd_participant_poll`, `epd_member_vote`,
`epd_party_office_election`, `epd_public_candidate_nomination`. The
first four are public electoral processes this platform does not
itself administer but whose eligibility rules this entity can still
model for informational, discussion, or candidacy-support purposes; the
last five are EPD-internal processes, spanning both participant-level
(`epd_public_consultation`, `epd_participant_poll`) and party-internal
(`epd_member_vote`, `epd_party_office_election`) scope, with
`epd_public_candidate_nomination` spanning both (item 9 below).

**Same person, different results:** the same verified person may
receive different results for different processes evaluated at the
same effective date — e.g. an EU citizen residing in Berlin: eligible
for the Berlin municipal/district process; eligible for the European
Parliament process in Germany; **not** eligible for the Bundestag
process where German citizenship is required; eligible for an EPD
public consultation per the applicable `ParticipantEligibilityPolicy`;
eligible for a party-member vote only if `PartyMembershipEligibilityPolicy`'s
membership requirements are also met. This is a worked example
illustrating the model, not a fixed legal determination this ADR makes.

**Ownership:** `ProcessEligibilityPolicy` is owned by
`eligibility-service` (amending ADR-026 to name this entity explicitly
alongside `ParticipantEligibilityPolicy`) — consistent with canon 5.2's
own framing of `eligibility-service` as the concrete-process evaluation
authority, and with item 1's corrected ownership, above, under which
`eligibility-service` is the sole computing party for all four
electoral/process-eligibility claims.

**Evaluation and reproducibility mechanics** (exact procedure fixed by
ADR-030, not restated in full here): exactly one `active`
`ProcessEligibilityPolicy` version applies per
`(process_type, jurisdiction, scope_type, scope_id)` tuple at any given
`effective_date` — mirroring section 12's own "exactly one active
version" invariant, extended with `effective_date` as an explicit
resolution dimension, since a real election's own date may need to
resolve against a policy version that has since been superseded. A
past eligibility determination remains reproducible against the
version it was actually decided under; a legal change creates a new
policy version and never rewrites a past determination (ADR-030).

**No current German legal value is fixed by this ADR.** Every
`eligible_citizenship_set`/residence/age/electoral-eligibility rule
`ProcessEligibilityPolicy` can express is a policy value, activated by
`governance-service`, per section 25/ADR-030 item 1 — the Bundestag/
European Parliament/Land/municipal examples above illustrate the model
and its intended legal-basis references only, never a value this
pack's design fixes in specification, ADR, or (were it to exist)
implementation code.

### 7. Step-up authentication — a new, versioned policy model

**Decision, per the project owner's explicit instruction.** Sensitive
actions require authentication stronger, or fresher, than whatever
ambient session authentication is otherwise sufficient for ordinary
participation. A new, versioned, proposed canonical entity,
**`StepUpAuthenticationRequirement`**, and a reusable, proposed value
shape it embeds, **`AssuranceRequirement`**, parameterize exactly which
actions require step-up, and to what level:

```text
AssuranceRequirement (proposed, reusable value shape — embedded by
StepUpAuthenticationRequirement, below, and available for reuse by any
future policy needing to state a minimum assurance bar, e.g. item 9's
`required_assurance_level`, below):
  required_identity_assurance_level       — none | low | substantial |
                                             high (item 8, below)
  required_authentication_assurance_level — none | low | substantial |
                                             high (item 8, below)
  required_attribute_freshness            — nullable; an
                                             AttributeFreshnessRequirement
                                             reference (item 8, below)

StepUpAuthenticationRequirement:
  requirement_id
  requirement_version
  status                        — draft | active | superseded
  action_code                   — open string, extensible; the specific
                                   sensitive action this requirement
                                   governs (illustrative, non-exhaustive
                                   examples below)
  required_authentication_context — open string/reference; which kind
                                   of `AuthenticationContext` (item 8,
                                   below) satisfies this requirement
                                   (e.g. a specific authentication
                                   method or method class)
  assurance_requirement          — an embedded `AssuranceRequirement`
                                   (above)
  fresh_authentication_required  — boolean
  maximum_authentication_age     — duration | null; how old
                                   `AuthenticationContext.session_authenticated_at`
                                   (item 8, below) may be before step-up
                                   is required
  reauthentication_reason        — reason code surfaced when this
                                   requirement is not met (ADR-029 scope
                                   — not added by this ADR)
  effective_from
  effective_until                — nullable
  supersedes_requirement_id      — nullable; corrections are always a
                                   new version, never a rewrite (mirrors
                                   section 12's own policy-versioning
                                   pattern)
```

**Illustrative, non-exhaustive named sensitive actions** (an open list,
extended by configuration, never a canon-fixed closed enum, mirroring
`identity_scheme`'s and `action_code`'s own established open-string
pattern): casting a vote or other secret-participation submission
(`voting-service`'s own future territory, referenced here as a binding
requirement on that service's eventual evolution, not implemented by
this pack); an authorized Stage B membership-admission, rejection,
suspension, or termination decision (item 2, above); a `ConflictAssessment`
resolution decision (ADR-030 item 4); a `ProcessEligibilityPolicy`,
`ParticipantEligibilityPolicy`, or `PartyMembershipEligibilityPolicy`
activation (a `governance-service` decision, section 25/ADR-030 item
1); an `AssemblyDecision` confirmation (item 9, below); and any change
to a person's own linked identity or authentication settings.

**Evaluation mechanics** (exact procedure fixed by ADR-030, not
restated in full here): whether a given `AuthenticationContext` (item
8, below) satisfies an active `StepUpAuthenticationRequirement` for a
given `action_code` is evaluated at the moment the action is attempted,
never cached as a standing fact about the account, and fails closed —
restated fully in ADR-030's own new step-up-mechanics item.

### 8. Separate identity assurance, authentication assurance, and attribute freshness

**Decision, per the project owner's explicit instruction.** Five
distinct concepts, previously at risk of being conflated into a single
"the person was verified" fact, are modeled as strictly separate
fields and, where the concept is inherently session-scoped rather than
identity-scoped, a new entity:

1. **Identity assurance level** — `identity_assurance_level` (renamed
   from `eid_assurance_level`, item 5 above; `IdentityRecord`, 7.3) —
   the assurance level of the identity **verification** itself, at the
   time it was performed. Does not expire on its own and does not
   reflect anything about the current session.
2. **Authentication assurance level** — a new field,
   `authentication_assurance_level` (`none | low | substantial | high`,
   same scale as `identity_assurance_level`, deliberately, so the two
   can be compared against one `AssuranceRequirement`, item 7, above) —
   the assurance level of **this specific authentication event**,
   which may be lower than the identity verification's own assurance
   level (e.g. a password-only login following a one-time,
   high-assurance eID verification).
3. **Attribute verification level, verified-at, and valid-until** —
   three new fields, `attribute_verification_level`,
   `attribute_verified_at`, `attribute_valid_until` (`IdentityRecord`,
   7.3) — the assurance level and freshness of a **specific verified
   attribute** (e.g. current address, current citizenship status),
   distinct from the overall identity verification: an identity may
   remain verified while a specific attribute's freshness has expired,
   requiring re-verification of that attribute alone, not the whole
   identity. A new, reusable, proposed value shape,
   **`AttributeFreshnessRequirement`**, expresses a freshness rule
   (`attribute_code` — open string; `maximum_attribute_age` — duration)
   that `attribute_valid_until` is checked against, and that
   `AssuranceRequirement.required_attribute_freshness` (item 7, above)
   references.
4. **Session authentication time and method** — two new fields on a
   new entity, below: `session_authenticated_at`, `authentication_method`
   (open string; e.g. `password_mfa`, `eid_online_authentication`,
   `federated_identity_provider` — extensible, never a closed list).
5. **Provider reference** — canon's existing `IdentityRecord.provider_reference`
   (7.3, unchanged) refers to the **identity-verification** provider
   integration; a new, session-scoped `provider_reference` field (same
   name, different entity, deliberately — the two are never the same
   value and are never compared to each other) refers to the
   **authentication** provider integration for a specific session, and
   may name a different provider than the one that originally verified
   identity.

**New entity, `AuthenticationContext`** (proposed, representing one
authenticated session, distinct from `IdentityRecord`, which represents
identity verification, not session authentication):

```text
AuthenticationContext (proposed):
  authentication_context_id
  account_id
  authentication_method          — open string, extensible (above)
  authentication_assurance_level — none | low | substantial | high
  session_authenticated_at
  provider_reference             — opaque; the authentication
                                    provider/session reference, distinct
                                    from `IdentityRecord.provider_reference`
  step_up_completed_at           — nullable; timestamp of the most
                                    recent step-up authentication event
                                    satisfying a `StepUpAuthenticationRequirement`
                                    (item 7, above), if any
```

**Why the rename (`eid_assurance_level` → `identity_assurance_level`,
item 5, above):** with authentication assurance now modeled separately
and named generically (`authentication_assurance_level`, not
`eid_authentication_assurance_level`), keeping the identity-verification
counterpart named after one specific technology (`eid_`) would be an
inconsistent, protocol-specific name for what item 8 establishes as a
protocol-agnostic concept — consistent with ADR-031's own cryptographic-
protocol-agility principle (no protocol or technology fixed in a field
name that is meant to outlive any one implementation choice). The value
scale and meaning are otherwise unchanged from the specification's own
Design decision D2.

**Binding rule, restated without qualification:** no consumer may treat
`identity_assurance_level`, `authentication_assurance_level`,
`attribute_verification_level`, or their respective freshness fields as
interchangeable, or substitute one for another — each answers a
different question (was the identity ever verified, and how strongly;
is the current session strongly authenticated; is a specific attribute's
verification still fresh), and a `StepUpAuthenticationRequirement`
(item 7, above) may require any combination of the three independently.

### 9. Legal effect and confirmation of digital processes — `decision_effect` and a separate `DigitalDecision → AssemblyDecision` confirmation lifecycle

**Decision, per the project owner's explicit instruction.** No digital
participation or voting process result is assumed legally final by
default. `ProcessEligibilityPolicy` (item 6, above) is extended — the
same entity, not a duplicate, since it already carries exactly the
`(process_type, jurisdiction, scope_type, scope_id, effective_date)`
key a process's legal effect must also be resolved against — with the
following additional fields:

```text
ProcessEligibilityPolicy, additional fields (extends item 6, above):
  decision_effect               — advisory | politically_binding |
                                   internally_binding | legally_final |
                                   requires_formal_confirmation
  formal_confirmation_required  — boolean
  formal_confirmation_authority — open string/reference; the competent
                                   body or office (e.g. a party
                                   assembly, a statutory authority) —
                                   opaque, never dereferenced by this
                                   pack
  secret_ballot_required        — boolean
  permitted_participation_mode  — open string/set; e.g. digital_only,
                                   physical_only, hybrid,
                                   digital_with_confirmation — never a
                                   universal rule (see below)
  required_assurance_level      — nullable; an `AssuranceRequirement`
                                   reference (item 7, above), reused
                                   rather than duplicated
  accessibility_profile         — open string/reference; deferred in
                                   detail to the future Accessibility &
                                   Assisted Participation pack (below)
```

`legal_basis` (item 6, above, already present) is reused unchanged for
this item's purposes — no second `legal_basis` field is introduced.

**Supported `decision_effect` values, restated:** `advisory`,
`politically_binding`, `internally_binding`, `legally_final`,
`requires_formal_confirmation` — at least these five; open to
extension, never a closed list a future process type cannot fit.

**Where formal confirmation is required, a separate, explicit
lifecycle applies** — never collapsed into the digital result itself,
and never modeled as a status value on an existing entity that was not
designed to carry it (mirroring item 2's own "a new record type, not an
overloaded status field" discipline):

```text
DigitalDecision (proposed):
  digital_decision_id
  process_reference       — opaque reference to the process/vote/
                             submission that produced this result
                             (never dereferenced by this pack)
  digital_result           — the outcome as computed digitally
  decision_effect          — copied from the applicable
                             `ProcessEligibilityPolicy` at the time of
                             the decision (immutable once recorded)
  formal_confirmation_required — boolean, copied likewise
  status                   — final | formal_confirmation_required
  recorded_at

AssemblyDecision (proposed; created only where
DigitalDecision.status = formal_confirmation_required):
  assembly_decision_id
  digital_decision_id       — references the `DigitalDecision` above
  confirming_authority       — copied from
                              `formal_confirmation_authority`
  legal_basis
  confirmation_deadline
  protocol_or_evidence_reference — opaque reference to the assembly's
                              own protocol, minutes, or other evidence
                              record (never dereferenced by this pack)
  final_legal_decision       — the confirming authority's own,
                              independent legal decision
  divergence_explanation     — nullable; **mandatory** whenever
                              `final_legal_decision` diverges from
                              `digital_result` above
  status                    — pending | confirmed | rejected |
                              returned_for_revision
  decided_at
```

**The lifecycle, restated as the project owner specified it:**
`DigitalDecision` (status `formal_confirmation_required`) →
`AssemblyDecision` (status `pending`) → `AssemblyDecision` (status
`confirmed` | `rejected` | `returned_for_revision`). A `DigitalDecision`
whose `decision_effect` does not require formal confirmation reaches
`status = final` directly, with no `AssemblyDecision` created at all.
Exact evaluation, deadline-handling, and reproducibility mechanics are
fixed by ADR-030's own new confirmation-mechanics item, not restated in
full here.

**No universal physical-presence rule.** This ADR does not, and no
future implementation may, hard-code a rule that all `legally_final`
decisions require physical presence. `permitted_participation_mode`
(above) is resolved the same way every other `ProcessEligibilityPolicy`
field is resolved — per concrete `process_type`, `jurisdiction`,
`scope_type`/`scope_id`, and `effective_date`, against whichever
applicable law, party statute, or policy version is active — never as
a platform-wide constant.

**Candidate-selection support distinguishes three stages, never
collapsed into one.** Referenced forward from item 6's own
`epd_public_candidate_nomination` process category, above: a digital
proposal or preselection (typically `decision_effect = advisory` or
`internally_binding`), a formal nomination procedure (typically
`requires_formal_confirmation`, producing its own `DigitalDecision`/
`AssemblyDecision` pair), and the legally final candidate selection
(typically `decision_effect = legally_final`, itself possibly the
output of the formal nomination's own `AssemblyDecision`) are three
distinct, separately-tracked process stages — this ADR records the
requirement that they remain distinguishable, not a fixed mapping of
every jurisdiction's own candidacy procedure onto these three stages,
which remains a policy-configuration matter.

**Deferred to future packs, per the project owner's explicit
instruction** — this ADR introduces only the policy fields and
entities above, no implementation:

- **Legal Decision Validity Pack** — the actual legal-effect
  determination logic, jurisdiction-specific confirmation-authority
  integration, and enforcement of `decision_effect`/confirmation
  outcomes.
- **Privacy Governance & DSFA Pack** — data-protection impact
  assessment obligations this new entity pair may trigger.
- **Public Verifiability Pack** — any public, verifiable-evidence
  presentation of `protocol_or_evidence_reference` content.
- **Accessibility & Assisted Participation Pack** — the
  `accessibility_profile` field's own concrete implementation.

**Not implemented by this pack:** assembly workflow tooling, DSFA
tooling, public-verifiability infrastructure, or accessibility
infrastructure — restated, unqualified, per the project owner's
explicit instruction.

### 10. Hard invariant — no consequential membership action or denial of a fundamental member right may be produced solely by automated policy evaluation

**Decision, per the project owner's explicit instruction.** Widening,
not replacing, item 2's own two-stage admission rule and the
specification's own "no automated system may permanently reject or
expel" principle: **no final membership deprivation, suspension,
expulsion, incompatibility decision, or denial of a fundamental member
right may ever be produced solely by automated policy evaluation** —
restated as a **hard, structural invariant**, proposed for canon
alongside INV-01/INV-08/INV-10's own existing fail-closed/human-control
invariants, not merely a documented convention.

- **"Final membership deprivation"** covers every terminal
  `Membership.membership_status` transition away from `active`
  (`suspended`, `terminated`) and every terminal `MembershipApplication`
  outcome away from a pending state (`rejected`) — restated from item
  2, unchanged in substance.
- **"Denial of a fundamental member right"** is the amendment's own new
  category, closing the gap the Problem section above identifies:
  **any** policy-evaluation outcome that would withhold a right a
  member would otherwise hold — whether or not it is labeled admission,
  rejection, suspension, termination, or incompatibility — still
  requires the same authorized human decision, `reason_code`, and
  review path. A future implementation may not invent a seventh label
  to route around this invariant; the invariant binds by **effect**
  (a right is withheld), not by which of the six named actions, if any,
  produced that effect.
- **Mechanically** (exact list and fail-closed evaluation fixed by
  ADR-030's own item 3, restated as a hard invariant here, not
  duplicated): admission, rejection, suspension, termination/expulsion,
  incompatibility finding, restoration of membership rights, and any
  other action whose effect is to deny a fundamental member right, are
  the exhaustive, open-ended set this invariant governs.

### 11. `AffiliationDeclaration` — temporal and verification fields

**Decision, per the project owner's explicit instruction.**
`AffiliationDeclaration` (section 10 of the specification, unchanged in
its other fields) gains two temporal fields and three verification
fields, additive and nullable:

```text
AffiliationDeclaration, additional fields:
  valid_from            — the date from which the declared affiliation
                           is asserted to hold
  valid_until            — nullable; when the declared affiliation is
                           asserted to have ended
  verification_status     — declared | verified | disputed |
                           unverifiable
  verified_at             — nullable
  verified_by              — opaque `RoleAssignment` reference of
                           whichever authorized reviewer performed the
                           verification, nullable
```

**Binding rules:** an `AffiliationDeclaration` with no `valid_until` is
treated as an ongoing, currently-asserted affiliation, not a
permanent one — a `ConflictAssessment` evaluating it must still confirm
it has not since lapsed. `verification_status` defaults to `declared`
(the subject's own unverified assertion) and moves to `verified` only
via an authorized reviewer recording `verified_at`/`verified_by` —
never automatically, and never by the same reviewer who would go on to
decide a `ConflictAssessment` opened against the same declaration
(mirroring `CONFLICT_REVIEW_SELF_APPROVAL_PROHIBITED`'s own existing
self-review prohibition). `disputed` and `unverifiable` are both
terminal-for-verification-purposes states that a `ConflictAssessment`
may weigh but that never, by themselves, resolve the conflict —
`incompatibility_level`/`status` (section 11) remain the only fields
that actually resolve a `ConflictAssessment`.

### 12. Critical policy classification, signed policy digest, and transparency-log commitment for critical policy activation

**Decision, per the project owner's explicit instruction.** Every
policy entity this pack introduces —
`ParticipantEligibilityPolicy`, `ProcessEligibilityPolicy`,
`PartyMembershipEligibilityPolicy`, and `StepUpAuthenticationRequirement`
— is a **critical policy**: each governs a fundamental participation or
membership right (general participation, electoral/process
eligibility, party membership, and the assurance bar sensitive actions
require), and each therefore carries two additional fields, additive
and nullable at `draft` status but **mandatory before a version may
reach `active`**:

```text
{critical policy entity}, additional fields:
  signed_policy_digest_reference       — opaque reference to a
                                          cryptographic signature over
                                          this version's own canonical
                                          content, using whichever
                                          protocol a future
                                          `CryptographicProtocolProfile`
                                          (ADR-031) selects — no
                                          protocol is fixed by this ADR
  transparency_log_commitment_reference — opaque reference to a
                                          publication of the digest
                                          above via this project's
                                          existing Transparency Context
                                          machinery (`PublicLedgerEntry`/
                                          `AuditExportPackage`, canon
                                          19a, unchanged) — no new
                                          publication infrastructure is
                                          introduced
```

**Binding rules:** a critical policy version may not transition
`draft → active` without both fields populated, in addition to the
existing `adopted_by_decision_id`/`adopted_by` and (per ADR-027) the
`multi_person_approval_met` confirmation — the four requirements are
independent and all four must hold; none substitutes for another. The
signing protocol and the transparency-log technology are both deferred,
unimplemented, and unselected by this ADR — restated, unqualified, from
ADR-031's own no-custom-cryptography and vendor-neutral-audit
principles, now applied specifically to this pack's own policy
activation rather than to ballot cryptography or audit infrastructure
generally. **Policy-freeze rule, extending CT-00-10 explicitly to
critical policies:** once a critical policy version is `active` and
has been used to evaluate at least one in-progress process or decision,
that version may not be superseded for the duration of that process —
mirroring `EligibilityRule`'s own freeze-on-ballot-open precedent
(canon 9.1) — a new version may still be created and activated
prospectively, but never in a way that would retroactively change the
rule an in-progress process is being evaluated under (exact mechanics:
ADR-030).

## Canon content this ADR authorizes (once implemented as its own separate task)

- New fields on `IdentityRecord` (7.3): `date_of_birth`,
  `citizenship_status`, `residence_status` — unchanged from the
  specification's section 9 (Design decision D2, Option A), additive
  and nullable — plus `identity_assurance_level` (renamed from the
  specification's own `eid_assurance_level`, item 8, below — same
  values, `none | low | substantial | high`, now named for the general,
  protocol-agnostic concept rather than the eID-specific one), plus
  `identity_scheme` (renamed from this ADR's own original drafting,
  `identity_verification_method`, item 5, above — open string,
  extensible, additive, nullable), plus three further new fields, per
  item 8, below: `attribute_verification_level`, `attribute_verified_at`,
  `attribute_valid_until` (all additive, nullable).
- Implementation authorization for `Membership` (8.3, already fully
  fielded), plus new canon events completing its status coverage
  (specification section 22), unchanged.
- Five new canonical entities, ownership split per ADR-026 (as amended
  by item 6, above): `ParticipantEligibilityPolicy` and
  `ProcessEligibilityPolicy` (owner: "Eligibility Engine", the existing
  canon 22 label for `eligibility-service`) and
  `PartyMembershipEligibilityPolicy`/`AffiliationDeclaration`/
  `ConflictAssessment` (owner: "Membership Service", canon's own
  existing, already-declared label, unchanged) — each with its own new
  canon subsection, fields, statuses, and forbidden links.
- The four separated electoral-eligibility claims (item 1, above,
  computation ownership corrected by item 6) — new derived-claim
  definitions, not stored fields, computed by `eligibility-service`
  against the active `ProcessEligibilityPolicy` version.
- The nine-concept identity-verification/citizenship separation (item
  5, above) as a new structural invariant and forbidden-link entry
  (no verification-route-implies-citizenship rule permitted).
- The two-stage admission rule (item 2, above) as a new structural
  invariant, with the exact entity/status mechanics fixed by ADR-030
  before the canon text is finalized.
- The membership-privacy default (item 3, above) as a new forbidden-
  link/default-visibility rule in section 23, alongside the existing
  vote-linkability and identity-leakage entries.
- New section 22 ownership-matrix rows for `ParticipantEligibilityPolicy`
  and `ProcessEligibilityPolicy` (both under "Eligibility Engine") and
  `PartyMembershipEligibilityPolicy`/`AffiliationDeclaration`/
  `ConflictAssessment` (under "Membership Service", already present in
  the matrix today with no populated entity), plus new section 23
  forbidden-link entries (e.g. `AffiliationDeclaration`/
  `ConflictAssessment` → `VoteEnvelope`/vote linkage, analogous to
  every prior pack's own vote-linkability exclusion; the
  membership-privacy default from item 3; the identity-verification/
  citizenship non-substitution rule from item 5).
- Three further new `IdentityRecord` (7.3) fields, per item 8, above:
  `attribute_verification_level`, `attribute_verified_at`,
  `attribute_valid_until`.
- Two new, proposed entities, per items 7–8, above: `StepUpAuthenticationRequirement`
  (owner: "Eligibility Engine", mirroring `ParticipantEligibilityPolicy`'s
  own versioned-policy ownership, since step-up requirements govern
  actions across this pack's own participation/membership scope) and
  `AuthenticationContext` (owner: `identity-service`, the existing
  canon 22 label — session authentication is an identity-layer concept,
  distinct from `IdentityRecord` itself), plus two new, proposed,
  reusable value shapes not independently owned:
  `AssuranceRequirement` and `AttributeFreshnessRequirement`.
- Six additional fields on `ProcessEligibilityPolicy` (extending item 6,
  above, per item 9): `decision_effect`, `formal_confirmation_required`,
  `formal_confirmation_authority`, `secret_ballot_required`,
  `permitted_participation_mode`, `required_assurance_level`,
  `accessibility_profile`.
- Two further new, proposed entities, per item 9, above: `DigitalDecision`
  and `AssemblyDecision` (owner: "Eligibility Engine", alongside
  `ProcessEligibilityPolicy`, since both record the outcome of a process
  `ProcessEligibilityPolicy` already governs) — each with its own new
  canon subsection, fields, statuses, and forbidden links (in particular,
  zero read or write edge toward `voting-service`/`tally-service`/
  `VoteEnvelope`, mirroring ADR-031 item 4's Credential Issuer boundary).
- A new, hard structural invariant, per item 10, above: no final
  membership deprivation, suspension, expulsion, incompatibility
  decision, or denial of a fundamental member right may be produced
  solely by automated policy evaluation — proposed for canon alongside
  INV-01/INV-08/INV-10.
- Two temporal fields (`valid_from`, `valid_until`) and three
  verification fields (`verification_status`, `verified_at`,
  `verified_by`) on `AffiliationDeclaration`, per item 11, above.
- A new `critical policy` classification, covering
  `ParticipantEligibilityPolicy`, `ProcessEligibilityPolicy`,
  `PartyMembershipEligibilityPolicy`, and
  `StepUpAuthenticationRequirement`, plus two new fields on each —
  `signed_policy_digest_reference`, `transparency_log_commitment_reference`
  — and a policy-freeze structural invariant extending CT-00-10, per
  item 12, above.

This remains a **minor** version bump per canon section 25 — every
change is additive (new nullable fields, new entities, new derived
claims, new structural invariants), nothing existing is altered,
removed, or redefined:

```text
CANON_VERSION: 0.5.0 → 0.6.0 (proposed, not performed by this document)
```

## Consequences

Once the separate, dedicated canon-edit task authorized by this ADR's
acceptance is carried out, `docs/canonical/TZ-00-domain-event-canon.md`
gains the `IdentityRecord` field extensions (including
`identity_scheme`, `identity_assurance_level`,
`attribute_verification_level`, `attribute_verified_at`,
`attribute_valid_until`), a new lettered-suffix section (mirroring
19a/19b/19c's own convention) for the Participation and Membership
Policy context, nine new entity definitions split across three owner
labels (`ParticipantEligibilityPolicy`/`ProcessEligibilityPolicy`/
`StepUpAuthenticationRequirement`/`DigitalDecision`/`AssemblyDecision`
under "Eligibility Engine"; `PartyMembershipEligibilityPolicy`/
`AffiliationDeclaration`/`ConflictAssessment` under "Membership
Service"; `AuthenticationContext` under `identity-service`), and
`canon_version` moves `0.5.0 → 0.6.0`. **None of this is performed by
this ADR's own drafting or acceptance.** Canon additionally gains a new
hard invariant (item 10), two additional `AffiliationDeclaration`
fields (item 11), and a `critical policy` classification with two
additional fields on four existing new entities plus a policy-freeze
invariant (item 12).

## Security impact

The two-stage admission rule (item 2) closes the "automated admission"
gap symmetrically to item 8's already-existing "automated
rejection/expulsion" prohibition — together they ensure no
`Membership.membership_status` transition into or out of `active`
happens without a recorded, authorized human decision. The four
separated electoral-eligibility claims (item 1) prevent a future
consumer from accidentally treating "eligible to vote publicly" as
equivalent to "eligible to vote internally in the party," which could
otherwise silently misapply a public electoral rule to an internal
party process or vice versa. The membership-privacy default (item 3)
closes a plausible-but-wrong reading of canon 8.3's already-public-
shaped status enum as an implicit disclosure default. The identity-
verification/citizenship separation (item 5) prevents a distinct,
easy-to-make error — silently excluding legally-entitled EU/EEA
participants because their verification route was mistaken for a
citizenship signal. The `ProcessEligibilityPolicy` model (item 6)
prevents electoral/process eligibility from ever being cached or stored
as a single, stale fact, and ensures every historical determination
remains reproducible against the exact policy version it was decided
under, rather than silently re-evaluating against whatever version is
current at query time. The step-up authentication model (items 7–8)
closes a distinct gap: without it, a sensitive action could be
authorized on the strength of a stale or weakly-authenticated session,
even where the underlying identity was, at some point in the past,
verified at a high assurance level — the strict separation of
`identity_assurance_level`, `authentication_assurance_level`, and
attribute-freshness fields ensures each question is asked
independently, and `StepUpAuthenticationRequirement`'s fail-closed
evaluation (ADR-030) ensures a missing or insufficient
`AuthenticationContext` blocks the action rather than defaulting to
permit. The `decision_effect`/confirmation model (item 9) prevents a
merely advisory or internally-binding digital result from being
silently presented, consumed, or relied upon as legally final, and
ensures any divergence between a digital result and a confirming
authority's own final legal decision is always explicitly recorded,
never silently overwritten. The hard invariant (item 10) closes the
one gap the original six-action list left open: a future implementation
could not previously be held to the two-stage rule for an action that
withholds a fundamental member right without fitting neatly into one of
the six named labels — the invariant now binds by effect, not by label.
`AffiliationDeclaration`'s new temporal/verification fields (item 11)
prevent a `ConflictAssessment` from being decided against a
long-lapsed or never-verified declaration without that fact being
visible to the reviewer. The `critical policy` classification (item 12)
closes a fourth class of error: a single compromised approver, an
unsigned policy version, or an unpublished activation could otherwise
each, individually, let a policy governing fundamental rights take
effect with materially weaker assurance than the two-stage admission
rule already requires for individual membership decisions — the four
independent requirements (verified `GovernanceDecision`,
`multi_person_approval_met`, signed digest, transparency-log
commitment) close that gap, and the policy-freeze rule prevents an
in-progress process from being retroactively re-governed by a
superseding version.

## Data impact

`IdentityRecord` gains seven new fields: `date_of_birth`,
`citizenship_status`, `residence_status` (unchanged from the
specification), `identity_assurance_level` (renamed from
`eid_assurance_level`, item 8), `identity_scheme` (renamed from this
ADR's own original drafting, `identity_verification_method`, item 5),
and `attribute_verification_level`/`attribute_verified_at`/
`attribute_valid_until` (item 8, new). `ProcessEligibilityPolicy` (item 6) gains seven additional fields (item 9): `decision_effect`,
`formal_confirmation_required`, `formal_confirmation_authority`,
`secret_ballot_required`, `permitted_participation_mode`,
`required_assurance_level`, `accessibility_profile`. Nine new canonical
entities are introduced in total — `ParticipantEligibilityPolicy`,
`ProcessEligibilityPolicy`, `StepUpAuthenticationRequirement`,
`DigitalDecision`, `AssemblyDecision` (owner: "Eligibility Engine" /
`eligibility-service`), `PartyMembershipEligibilityPolicy`,
`AffiliationDeclaration`, `ConflictAssessment` (owner: "Membership
Service" / `membership-service`), and `AuthenticationContext` (owner:
`identity-service`) — per ADR-026 as amended by item 6, above.
`AffiliationDeclaration` gains five additional fields (item 11):
`valid_from`, `valid_until`, `verification_status`, `verified_at`,
`verified_by`. Four entities — `ParticipantEligibilityPolicy`,
`ProcessEligibilityPolicy`, `PartyMembershipEligibilityPolicy`,
`StepUpAuthenticationRequirement` — each gain two additional fields
(item 12): `signed_policy_digest_reference`,
`transparency_log_commitment_reference`. One new structural invariant
is proposed (item 10), and one existing structural invariant
(CT-00-10) is extended, not altered (item 12). No existing entity's
field shape is altered; every change is additive.

## Migration impact

None — no canon edit has been performed; no `services/membership-service`
directory exists; `eligibility-service`'s own extension has not begun.

## Reversibility

Reversible with cost before code exists (this stage). Once real
`ParticipantEligibilityPolicy`/`PartyMembershipEligibilityPolicy`/
`Membership` data exists — especially given the two-stage admission
rule's own audit/decision-record dependencies — narrowing or
restructuring any of this content becomes a major-version-equivalent
change under canon section 25.

## Related canon version

Authored against canon version `0.5.0`. Proposes a minor bump to
`0.6.0`, per section 24 of the specification and the summary above; the
corresponding canon edit itself would be performed as its own separate,
dedicated follow-on task, not as part of this ADR's own drafting or
acceptance — that follow-on task has not been carried out.
