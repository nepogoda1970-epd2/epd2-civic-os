# ADR-027: PACK-07 cross-service boundaries — narrow reads only

## Status

`accepted`

## Date

2026-07-24

## Owner decision

Accepted exactly as drafted, 2026-07-25, following architectural
approval of `docs/handover/PACK-07-SPEC-FINAL.md` (v3). No further
amendment: the narrow cross-service read boundaries, the
atomic-capability-check/scoped-capability-token enforcement dichotomy
(fifth amendment, item 2), and the `multi_person_approval_met`
extension to `verify_decision_authorizes_policy_activation` (fifth
amendment, item 7) are all accepted verbatim. This acceptance alone
authorizes no service code (`docs/review/PACK-07-OWNER-DECISIONS.md`
section 2).

## Canon implementation (2026-07-25, follow-on task)

Recorded in canon 0.6.0, new section 19d.14 (enforcement mechanism —
atomic capability checks / scoped capability tokens, exclusively) and
19d.7 (critical-policy four-gate activation, including
`multi_person_approval_met`). No existing canon entity's field, status,
or owner is changed by this ADR's content.

## Context

`docs/handover/PACK-07-SPEC.md` section 19 proposed a cross-pack
dependency matrix for a single `membership-service` owning every new
PACK-07 entity. ADR-026 (this same round) splits that ownership across
the existing `eligibility-service` (general participation eligibility)
and a new `membership-service` (party membership, affiliation,
conflict). This ADR defines the narrow read interfaces both services
may use — including, for the first time in this project, a read edge
in the direction of the existing service (`eligibility-service`) toward
the new one (`membership-service`), since a party-membership-derived
fact can legitimately gate a general-participation process (e.g. a
process restricted to party members only).

The project owner has since issued two further amendments, both
bearing directly on this ADR: (1) identity verification must never be
conflated with citizenship — they are separate concepts, evaluated by
separate services, exposed as separate derived claims; and (2)
electoral and process eligibility must never be modeled as one
permanent attribute of a person — every claim is evaluated fresh, for a
concrete process, jurisdiction, territorial scope, effective date, and
policy version, per a new versioned policy entity (`ProcessEligibilityPolicy`,
defined in full by ADR-028). Both amendments are incorporated directly
into this ADR's own boundary design below.

The project owner has since issued a third amendment, bearing on this
ADR's own service and trust boundaries: a strict separation of
identity assurance, authentication assurance, and attribute freshness
(fields and entities fixed by ADR-028); a step-up authentication
requirement for sensitive actions (policy model fixed by ADR-028,
evaluation mechanics fixed by ADR-030); domain-scoped pseudonymous
identifiers instead of one universal identity hash; an explicit
cross-domain correlation prohibition; anonymous-endpoint isolation; and
a strengthened Credential Issuer boundary (all four fixed in full by
the new, proposed ADR-031, since they bear on `credential-service`/
`voting-service`/`tally-service` boundaries this pack's own two
services never touch). This ADR incorporates only the parts of that
amendment that concern `eligibility-service`'s and `membership-service`'s
own boundaries — cross-referencing ADR-028/ADR-030/ADR-031 rather than
restating their content, below.

The project owner has since issued a fifth amendment, bearing directly
on this ADR: `ParticipationRightsProfile` (ADR-026 item 3) is now
characterized as an internal, non-authoritative derived view — this ADR
fixes, in full, the corresponding enforcement-boundary rule: every
actual authorization decision, everywhere in this pack's design, uses
one of exactly two mechanisms, an atomic capability check or a
single-purpose scoped capability token, never a read of the profile
itself (below). The same amendment also requires a multi-person
approval verification for critical policy activation (mechanics fixed
by ADR-030, canon-impact fixed by ADR-028); this ADR fixes only the
corresponding narrow-read boundary consequence, below.

## Problem

Without an explicit boundary, either service could be tempted to read
the other's storage directly, dereference `Membership.organization_id`
against a live `Organization` entity that does not yet exist (deferred
to PACK-08), or expose raw identity/citizenship/affiliation content
across a service boundary — all of which this project's established
CT-00-08 identity-leakage discipline and its narrow-read precedent
(ADR-012, ADR-017, ADR-022) already forbid for every prior pack.
Separately, without an explicit rule distinguishing "a person's
identity was verified" from "a person holds a particular citizenship,"
a future implementation could plausibly (and wrongly) read a
successful eID verification as proof of German citizenship, or treat
`eid_assurance_level` as a citizenship signal — neither of which it is.
Finally, without an explicit rule that electoral/process eligibility is
always process-scoped, a future implementation could cache or store a
single "is this person electorally eligible" fact on the person, which
would silently produce the wrong answer the moment the same person is
evaluated against a second, different process (e.g. eligible for a
Land election but not the Bundestag; eligible for an EPD public
consultation but not yet for a party-member vote).

## Considered options

- Option A — `membership-service` reads raw `Membership` status and
  affiliation details directly into any consumer that asks, on the
  theory that `Membership.membership_status` is already public-shaped
  (canon 8.3). Rejected: item 3 of the originating instruction's ADR-028
  amendment (privacy) makes clear that membership data is restricted by
  default, not merely "already public-shaped" — a raw read would bypass
  that default.
- Option B — the project owner's decision, below: every cross-service
  edge is a narrow, purpose-built read returning only derived booleans
  or opaque references, in both directions, with an explicit,
  enumerated allow-list of what each service may read from the others,
  identity verification kept structurally distinct from citizenship,
  and every electoral/process-eligibility claim evaluated fresh against
  a concrete process/jurisdiction/scope/date/policy-version rather than
  stored as a standing fact.
- Option C — no `eligibility-service → membership-service` edge at all,
  requiring every process that cares about party membership to query
  `membership-service` directly instead of through
  `eligibility-service`'s own evaluation flow. Rejected: this would
  force every future consumer of general eligibility evaluation to
  additionally integrate with `membership-service` directly whenever a
  process happens to be party-membership-gated, duplicating
  `eligibility-service`'s own role as the single evaluation entry point
  every other pack already relies on (canon 5.2's own "отвечает на
  вопрос: имеет ли подтверждённый участник право участвовать в
  конкретном процессе?").
- Option D — let `identity-service` itself decide electoral/process
  eligibility, since it already holds the verified facts. Rejected per
  the project owner's explicit instruction (item 6 of the
  process-eligibility amendment): `identity-service` provides verified
  facts only and must never decide legal or political eligibility for a
  concrete process — that evaluation belongs to `eligibility-service`,
  the service canon 5.2 already names as answering exactly this
  question.

## Decision

**Option B**, per the project owner's explicit instruction.

### `membership-service` may read:

- **Derived identity facts from `identity-service`**, scoped to what
  `membership-service` itself needs to evaluate party-membership
  admission and continuing eligibility (`PartyMembershipEligibilityPolicy`,
  Stage A of ADR-028's two-stage admission process): `identity_verified`,
  `identity_assurance_requirement_met`, `age_requirement_met`,
  `citizenship_requirement_met`, `residence_requirement_met` — one new,
  narrow, purpose-built read (mirroring ADR-022's
  `verify_role_assignment_for_action` precedent: compute the check
  where the raw data already lives, return only booleans plus reason
  codes) — never the raw `date_of_birth`/`citizenship_status`/
  `residence_status`/`eid_assurance_level`/verification fields
  themselves (section 9/14 of the specification, unchanged). **This
  read never resolves any of the four electoral/process-eligibility
  claims** (`active_electoral_eligibility_met`,
  `passive_electoral_eligibility_met`,
  `party_internal_voting_eligibility_met`,
  `party_office_candidacy_eligibility_met`) — those are exclusively
  `eligibility-service`'s own computation, per the process-eligibility
  amendment below; `membership-service` consumes them only indirectly,
  by being read _from_ (not reading them itself), when
  `eligibility-service` needs a membership-status fact to resolve the
  two party-internal claims (see the reused edge below).
- **Participant eligibility results from `eligibility-service`** — a
  narrow read of the subject's current `EligibilityDecision` (canon
  9.2, unchanged, reused) where a concrete process already requires
  one, and, where relevant, whether the subject's
  `ParticipantEligibilityPolicy`-derived participant capabilities are
  currently satisfied — never the raw `ParticipantEligibilityPolicy`
  row or `EligibilityRule` content itself, only the process-scoped
  verdict.
- **Governance authorization for policy activation and consequential
  membership decisions** — the two narrow reads the specification's
  own section 13 already proposed
  (`verify_decision_authorizes_policy_activation`, section 13; and an
  equivalent verification of a `ConflictAssessment`'s
  `decision_authority_reference`, section 11), unchanged by this ADR.

### `eligibility-service` may read (new edge, introduced by this ADR):

`eligibility-service` has had **zero** import dependency on
`epd2_identity_service` since PACK-02 (documented directly in its own
`domain.py`). This ADR introduces `eligibility-service`'s first-ever
cross-pack read dependency, made necessary by the process-eligibility
amendment below: `eligibility-service`, not `identity-service`, is the
service that applies the active `ProcessEligibilityPolicy` version and
returns every derived electoral/process-eligibility claim (item 7 of
the process-eligibility amendment).

- **Derived identity facts from `identity-service`** — the same class
  of narrow, purpose-built read `membership-service` uses (above),
  resolving `identity_verified`, `identity_assurance_requirement_met`,
  `age_requirement_met`, `citizenship_requirement_met`,
  `residence_requirement_met`, and `territorial_scope_requirement_met`
  — never the raw underlying fields. `eligibility-service` uses this
  read to evaluate `active_electoral_eligibility_met` and
  `passive_electoral_eligibility_met` (both depend only on
  identity-layer facts plus the active `ProcessEligibilityPolicy`,
  never on party membership).
- **The minimum party-membership-derived claim from
  `membership-service`, reused, not duplicated** —
  `required_membership_status_met` and
  `membership_duration_requirement_met` (already defined below) are
  the same read `eligibility-service` uses for general
  membership-gated participant processes; `eligibility-service` also
  uses this same read to evaluate `party_internal_voting_eligibility_met`
  and `party_office_candidacy_eligibility_met` under the active
  `ProcessEligibilityPolicy`, when the process being evaluated is
  party-internal (`EPD member vote`, `EPD party-office election`, or
  the party-internal half of `EPD public-candidate nomination`). **No
  second, separate read is introduced for this purpose** — the two
  party-internal electoral claims are resolved by combining this
  existing membership read with `ProcessEligibilityPolicy`'s own
  party-internal rules (ADR-028), inside `eligibility-service`, never by
  `membership-service` computing an electoral-eligibility claim itself.

### `eligibility-service` may read only the minimum party-membership-derived claim when a concrete process explicitly requires membership:

- `required_membership_status_met` — a single boolean, true only when
  the subject holds a `Membership` (canon 8.3, `membership_type =
party`) whose current `membership_status` satisfies whatever the
  calling process concretely requires (e.g. `active`) — never the raw
  `membership_status` value, `organization_id`, or any other
  `Membership` field.
- `membership_duration_requirement_met` — a single boolean, true only
  when the subject's `Membership.effective_from` (canon 8.3) satisfies
  a process-specific minimum-duration requirement — never the raw
  `effective_from` timestamp itself.

Both claims are exposed through one new, narrow, purpose-built
`membership-service` read function, modeled directly on
`verify_role_assignment_for_action`'s (ADR-022) and
`verify_decision_authorizes_policy_activation`'s (specification section 13) own precedent: the calling process supplies a subject reference and
the specific process/action it is evaluating; `membership-service`
computes both booleans internally and returns only the two flags plus a
reason code (populated only when a flag is false, drawn from
`membership-service`'s own registered codes, per ADR-029) — never the
underlying `Membership` row. This is the **only** function
`eligibility-service` may call on `membership-service`; it must not
import `membership-service`'s domain module or call any
`membership-service` command capable of writing `Membership`,
`AffiliationDeclaration`, `ConflictAssessment`, or
`PartyMembershipEligibilityPolicy`.

### Identity verification is not citizenship — separate concepts, extensible verification routes

**Decision, per the project owner's explicit instruction:** identity
verification, identity assurance level, and identity scheme/provider
are structurally separate concepts from citizenship, residence,
habitual residence, territorial connection, and electoral eligibility.
No boundary defined by this ADR ever substitutes one for another.

- **Nine separate concepts, each its own claim or field** (fields fixed
  by ADR-028; the boundary consequence is fixed here): identity
  verification (`identity_verified`); identity assurance level
  (`identity_assurance_requirement_met`, derived from
  `eid_assurance_level`); identity scheme/provider (the verification
  route actually used — never itself a citizenship signal); citizenship
  (`citizenship_requirement_met`, derived from `citizenship_status`);
  residence status (`residence_requirement_met`); habitual residence
  (one value of `residence_status.residence_type`, unchanged from
  section 8); territorial connection
  (`territorial_scope_requirement_met`); active electoral eligibility
  (`active_electoral_eligibility_met`); passive electoral eligibility
  (`passive_electoral_eligibility_met`).
- **`identity_verified` and `identity_assurance_requirement_met` are
  never derived from, and never substitute for, `citizenship_requirement_met`.**
  A successfully verified identity (via any supported route — German
  Personalausweis online function, a German eID card issued to an
  eligible EU/EEA national, a supported foreign national eID via
  eIDAS, or another approved method, per ADR-028's extensible route
  list) establishes only that the person's identity and, where
  applicable, assurance level are verified — it establishes nothing
  about citizenship, which is read exclusively from
  `citizenship_status` (unchanged, section 8).
- **No boundary, read, or claim in this pack's design may encode a rule
  that only German citizens may become verified participants.** A
  citizen of another EU/EEA state, once identity-verified through a
  supported route, may become a verified participant, a
  party-membership applicant, or a party member — subject to whatever
  `ParticipantEligibilityPolicy`/`PartyMembershipEligibilityPolicy`/
  `ProcessEligibilityPolicy` conditions and legal requirements actually
  apply (still policy values, never fixed by this ADR — section
  25/ADR-030 item 1, unchanged).
- **The right to perform a concrete action is always evaluated
  separately** by action type, jurisdiction, territorial scope,
  residence requirement, citizenship requirement (where applicable),
  and active/passive electoral eligibility (where applicable) — never
  as one combined check that could silently substitute a verified-
  identity fact for a citizenship fact or vice versa.

### Process-specific electoral eligibility — always evaluated per process, jurisdiction, scope, date, and policy version

**Decision, per the project owner's explicit instruction:** no claim
this ADR defines is ever modeled, cached, or stored as one permanent
attribute of a person. Every one of the four electoral/process-
eligibility claims is computed fresh, for a concrete tuple of
`(process_type, jurisdiction, scope_type, scope_id, effective_date)`,
against whichever `ProcessEligibilityPolicy` version (ADR-028 defines
the entity; ADR-030 defines the evaluation and reproducibility
mechanics) is applicable at that tuple.

- **`identity-service` provides verified facts only** —
  `identity_verified`, verified age or date-of-birth evidence,
  citizenship set, residence scope, residence duration, and assurance
  level. **`identity-service` never decides legal or political
  eligibility for a concrete process** — it has no notion of
  `process_type`, jurisdiction, or `ProcessEligibilityPolicy` at all.
- **`eligibility-service` applies the active `ProcessEligibilityPolicy`
  version and returns only derived results**:
  `active_electoral_eligibility_met`, `passive_electoral_eligibility_met`,
  `party_internal_voting_eligibility_met`,
  `party_office_candidacy_eligibility_met`, `residence_requirement_met`,
  `citizenship_requirement_met`, `scope_requirement_met`,
  `applicable_policy_version`, and `reason_codes` — never the raw
  identity facts or the raw policy row itself.
- **The same verified person may receive different results for
  different processes evaluated at the same moment** — e.g. an EU
  citizen residing in Berlin may be evaluated as eligible for a Berlin
  municipal/district process and a European Parliament process in
  Germany, not eligible for a Bundestag process (where German
  citizenship is required), eligible for an EPD public consultation
  under the applicable `ParticipantEligibilityPolicy`, and eligible for
  a party-member vote only if `PartyMembershipEligibilityPolicy`'s own
  membership requirements are additionally met. No single stored fact
  could ever represent this correctly — restated here as a structural
  boundary rule, not merely a policy-content observation (ADR-028/030
  own the policy model and evaluation mechanics).
- **Public candidacy distinguishes two independently-required
  conditions, never conflated:** party-internal permission to stand
  (`party_office_candidacy_eligibility_met`, where the nomination is
  party-sponsored) and legal passive electoral eligibility for the
  public election itself (`passive_electoral_eligibility_met`). An `EPD
public-candidate nomination` process may require both; satisfying one
  never implies the other.

### Data minimization toward `voting-service` and candidacy workflows

**Decision, per the project owner's explicit instruction:** any
consumer outside this pack's two services — most notably
`voting-service` (PACK-03) or a future candidacy-nomination
workflow — that needs to know whether a subject may participate in a
concrete process **never receives** identity documents, full
citizenship records, exact address, or full date of birth. It receives
only: a process identifier, the scope, the derived eligibility result
(one or more of the claims above), a participation or candidacy
credential reference (canon 10.1, `ParticipationCredential`, unchanged
— reused, not duplicated), and a policy-version reference
(`applicable_policy_version`). This does not introduce a new
structural edge beyond what canon 5.2 and this project's established
`EligibilityDecision`-consumption pattern already permit (every pack
since PACK-02 already consumes only a derived eligibility verdict, never
raw identity content) — it restates that existing discipline explicitly
for this pack's own new claim set, and confirms it is not weakened by
this pack's four new electoral/process claims or by
`ProcessEligibilityPolicy`'s own party-internal awareness.

### Explicitly prohibited, restated without qualification:

**Raw `Membership` status, affiliation details, identity attributes,
birth date, citizenship documents, or organization names must never be
exposed through any cross-service API** — in either direction, between
any pair of services this ADR governs, or to any third service. This
generalizes CT-00-08's existing identity-leakage discipline (already
binding on `identity-service` toward every other pack) to this pack's
own new `Membership`/`AffiliationDeclaration`/`ConflictAssessment`/
`ProcessEligibilityPolicy` attribute surface, and extends it
symmetrically to the new `eligibility-service ↔ membership-service` and
`eligibility-service → identity-service` read edges this ADR
introduces.

### Regional scope and `Organization` references — unchanged

Regional scope remains generic (`scope_type`/`scope_id`, no enumerated
Bund/Land/Kreis/Bezirk/Ort hierarchy) and `Membership.organization_id`
remains an opaque, caller-supplied reference, never dereferenced by
either `eligibility-service` or `membership-service` — both exactly as
the specification's own Design decision D4 (section 17) already
proposed, unamended by this ADR. Neither service may assume a live
`Organization` or `CivicSpace` entity exists until PACK-08 defines one.
`ProcessEligibilityPolicy`'s own `jurisdiction`/`scope_type`/`scope_id`
fields (ADR-028) follow the same opaque, generic-structure discipline.

### Forbidden edges, restated for this pack's two services

Mirroring section 19's own table: neither `eligibility-service` nor
`membership-service` may read or write `voting-service`,
`tally-service`, `delegation-service`, `credential-service.domain`, or
`identity-service.domain` (only the one narrow, purpose-built read
above is permitted into `identity-service`, never its domain module
directly) — no path from participation, membership, affiliation, or
conflict data to vote content or vote linkability (CT-00-09, section
27 of the specification). Neither service reads or writes
`ai-processing-service` — no AI-assisted decision-making anywhere in
this pack's design, unchanged from section 1.

### Step-up authentication and session-assurance — boundary consequences

**Decision, per the project owner's explicit instruction.** Where a
`StepUpAuthenticationRequirement` (ADR-028 item 7) governs an action
either `eligibility-service` or `membership-service` performs (e.g. a
Stage B admission decision, a `ConflictAssessment` resolution), the
deciding service reads only the derived
`authentication_step_up_satisfied` boolean (and, where unmet, a
`reauthentication_reason` code) — never the raw `AuthenticationContext`
row, never `session_authenticated_at` or `provider_reference` directly,
and never a raw `IdentityRecord.identity_assurance_level`/
`attribute_verification_level` value. This is the same narrow-read
discipline this ADR already applies to every other cross-service edge,
extended to the new `AuthenticationContext` entity (owner:
`identity-service`, ADR-028 item 8): **`AuthenticationContext` is read
through exactly one additional narrow, purpose-built function on
`identity-service`, never through a general session-lookup API**, and
never by `voting-service`, `tally-service`, or any service outside this
pack's own two, which continue to rely on their own existing
credential/session mechanisms (ADR-031 item 4).

### Domain-scoped pseudonyms and anti-correlation — cross-reference, not restated

**Decision, per the project owner's explicit instruction.** Any future
`DomainPseudonymReference` (a new, proposed concept — ADR-031 item 1)
issued for the participant, membership, or eligibility domains is
opaque to both `eligibility-service` and `membership-service`, exactly
as `Membership.organization_id` already is: neither service derives,
compares, or attempts to correlate a pseudonym value across domains.
The full cross-domain correlation prohibition (`AntiCorrelationInvariant`),
anonymous-endpoint isolation, and the strengthened Credential Issuer
boundary are fixed in full by ADR-031, not restated here — this ADR
confirms only that neither of this pack's two services introduces any
read or write edge capable of weakening them (ADR-031 item 4 already
confirms this pack's five new entities have zero edge toward
`voting-service`/`tally-service`/`VoteEnvelope`).

### Enforcement mechanism — atomic capability checks or single-purpose scoped capability tokens, exclusively

**Decision, per the project owner's explicit instruction (fifth
amendment).** `ParticipationRightsProfile` (ADR-026 item 3) being
internal and non-authoritative would be a hollow characterization
without an equally explicit statement of what **is** authoritative.
Exactly two mechanisms are permitted to actually grant or deny an
action, anywhere in this pack's design, and no third:

- **Atomic capability check** — a narrow, purpose-built, synchronous
  read, evaluated at the moment the action is attempted, returning
  exactly one boolean (plus a reason code where false) for exactly one
  question (e.g. `can_vote_as_party_member_for(subject, process)`,
  `authentication_step_up_satisfied_for(subject, action_code)`). This
  is not a new pattern — it is every narrow read already defined
  earlier in this ADR (identity claims, membership-derived claims,
  step-up satisfaction, governance authorization), now named explicitly
  as one of the two only-permitted enforcement mechanisms, so that no
  future consumer mistakes "read `ParticipationRightsProfile` and
  branch on a field" for an equivalent, lighter-weight alternative.
- **Single-purpose scoped capability token** — an existing
  `ParticipationCredential` (canon 10.1, unchanged) or an equivalent
  future credential, scoped to exactly one action/process, presented
  by the caller and verified by the service that issued it — never a
  general-purpose token whose scope a consumer must itself narrow by
  inspecting its claims.

**Binding rule, restated without qualification:** no service, no
OpenAPI path, and no frontend integration may read
`ParticipationRightsProfile` and then use any of its boolean fields to
decide whether to permit an action. A profile read and an atomic
capability check may return different answers at different moments —
this is expected, not an inconsistency to be reconciled, since only the
capability check is authoritative. Where a future implementation wants
to show a user "you appear to be able to do X," it performs a profile
read for **display** and, separately, an atomic capability check (or
requires a scoped token) at the moment the user actually attempts X —
the two calls are never conflated into one.

### Multi-person approval for critical policy activation — boundary consequence

**Decision, per the project owner's explicit instruction (fifth
amendment).** Every policy entity this pack introduces
(`ParticipantEligibilityPolicy`, `ProcessEligibilityPolicy`,
`PartyMembershipEligibilityPolicy`, `StepUpAuthenticationRequirement`)
is a **critical policy** for the purposes of this rule (ADR-028/030
fix the exact classification and mechanics) — activating any version of
any one of them requires `governance-service` to confirm not merely
that an `approved` `GovernanceDecision` exists
(`verify_decision_authorizes_policy_activation`, unchanged), but that
its own approval evidence demonstrates a policy-configured minimum
number of distinct authorized approvers. This ADR extends the existing
narrow-read function's own return shape with one additional boolean,
`multi_person_approval_met`, computed entirely inside
`governance-service` — the calling service (`eligibility-service` or
`membership-service`) never receives the approver list itself, only
the boolean, mirroring every other narrow read in this document.

## Consequences

`eligibility-service`'s `pyproject.toml` will declare two new upstream
package dependencies at implementation time — `epd2_identity_service`
(this pack's first-ever `eligibility-service → identity-service` edge;
`eligibility-service` has had zero identity-service dependency since
PACK-02) and `epd2_membership_service` (the first case in this project
of an _older_, already-implemented pack depending on a _newer_ pack's
service, rather than the usual newer-depends-on-older direction). Both
are deliberate, narrow exceptions, justified by the same "ask the
owning service to confirm and return only a boolean" pattern every
other cross-pack read in this project already follows — neither makes
`eligibility-service` a general consumer of the other service's
storage. `tests/repository/test_service_boundaries.py`'s forbidden-pair
matrix will gain three new allow-list entries at implementation time:
`eligibility-service → identity-service` (scoped to the one new
identity-claim read), `membership-service → identity-service` (scoped
to the same read, used for admission evaluation), and
`eligibility-service → membership-service` (scoped to the one new
`required_membership_status_met`/`membership_duration_requirement_met`
read, reused for both general membership-gating and the two
party-internal electoral claims), alongside the two reads into
`governance-service` the specification's own section 19 already
proposed. A fourth allow-list entry, `membership-service →
identity-service` (or `eligibility-service → identity-service`, per
whichever service is deciding the step-up-gated action), will be scoped
to the new `authentication_step_up_satisfied` read (above) at
implementation time — reusing the identity-service edge already
introduced by this ADR, not a new service pair. The existing
`verify_decision_authorizes_policy_activation` function gains one
additional return field, `multi_person_approval_met` — no new service
pair, since the read already terminates at `governance-service`.

## Security impact

The `required_membership_status_met`/`membership_duration_requirement_met`
boundary is the load-bearing privacy control for the membership-gating
part of this ADR: it lets a general-participation process (owned by
`eligibility-service`) be gated on party membership without
`eligibility-service` ever holding `Membership.membership_status`,
`organization_id`, or any `AffiliationDeclaration`/`ConflictAssessment`
content — closing off the exact "already public-shaped, so why not read
it directly" reasoning Option A above would have invited. The
identity-verification/citizenship separation closes a distinct,
easy-to-make error: a future implementation conflating "eID verified"
with "German citizen" would silently and incorrectly exclude every
verified EU/EEA participant from processes they are legally entitled to
join. The process-scoped, never-stored electoral-eligibility design
closes a third distinct error: a cached or stored "electorally eligible"
fact would silently produce wrong answers the moment the same person is
evaluated against a second process with different rules. Combined with
the unchanged opaque-reference treatment of `organization_id` and the
unchanged `identity-service` narrow-read pattern, this ADR extends
CT-00-08's identity-leakage discipline across three genuinely new
service-pair edges for the first time in this project. The step-up
authentication boundary (above) closes a fourth, distinct error: a
service deciding a sensitive action could otherwise be tempted to
inspect `AuthenticationContext` or `IdentityRecord` assurance fields
directly rather than through a narrow derived-boolean read, silently
reintroducing the same raw-field-exposure risk this ADR's other
boundaries already close — the derived
`authentication_step_up_satisfied` read forecloses that path.
Domain-scoped pseudonyms and the anti-correlation invariant (ADR-031)
are out of this ADR's own scope but confirmed, above, not to be
weakened by any edge this ADR introduces. Naming atomic capability
checks and scoped capability tokens as the **only** two permitted
enforcement mechanisms closes a fifth, distinct error: a future
implementation reading `ParticipationRightsProfile` for convenience and
branching on it directly would silently reintroduce a stale-authorization
risk this ADR's own narrow-read discipline was designed to prevent
everywhere else. The `multi_person_approval_met` boundary consequence
closes a sixth: a critical policy activated by a single compromised or
mistaken approver would otherwise be indistinguishable, at the
`eligibility-service`/`membership-service` boundary, from one properly
approved by the policy-configured minimum number of people.

## Data impact

No new field on any canonical entity. Four new, narrow, purpose-built
read functions (one on `membership-service`'s own application module,
one on `identity-service`'s for identity/citizenship/residence claims,
one further on `identity-service`'s for the new
`authentication_step_up_satisfied` claim, all reused by
`eligibility-service` and `membership-service` as described above) and
their result types — all repository-side, not canon text, mirroring
`verify_role_assignment_for_action`'s own precedent (ADR-022).
`ProcessEligibilityPolicy`, `StepUpAuthenticationRequirement`, and
`AuthenticationContext` are themselves ADR-028's own canonical-entity
proposals, not this ADR's.

## Migration impact

None — neither `services/membership-service` nor the
`eligibility-service` extension exists yet; both are created together
as later implementation tasks.

## Reversibility

Reversible with cost once real cross-service read traffic exists:
narrowing or widening any read function's returned fields later would
require coordinated changes to both the owning service and every
caller. Comparatively easy to reverse before any code exists (this
stage).

## Related canon version

Authored against canon version `0.5.0`. Proposes no canon change
itself — this ADR only authorizes new cross-pack read edges and their
application functions, none of which is canon text.
