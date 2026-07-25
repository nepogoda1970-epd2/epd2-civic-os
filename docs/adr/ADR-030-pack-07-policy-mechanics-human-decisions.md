# ADR-030: PACK-07 policy mechanics, application lifecycle, and human decisions

## Status

`accepted`

## Date

2026-07-24

## Owner decision

Accepted exactly as drafted, 2026-07-25, following architectural
approval of `docs/handover/PACK-07-SPEC-FINAL.md` (v3). No further
amendment: the two-stage `MembershipApplication` lifecycle, the
widened, seven-category hard invariant on consequential human control
(fifth amendment, item 3), the `Appeal` polymorphic-reuse standing
default (fifth amendment, item 4), the formal-confirmation lifecycle
(`DigitalDecision → AssemblyDecision`), and the critical-policy
multi-person-approval/policy-freeze mechanics (fifth amendment, item 7)
are all accepted verbatim (`docs/review/PACK-07-OWNER-DECISIONS.md`
section 5).

## Canon implementation (2026-07-25, follow-on task)

Recorded in canon 0.6.0: new section 19d.9 (`MembershipApplication`,
six-state lifecycle, `Membership` 8.3 left unchanged), 19d.12
(`DigitalDecision`/`AssemblyDecision` formal-confirmation lifecycle),
19d.15 (`Appeal` 14.3 polymorphic-target documentation clarification,
unchanged fields), 19d.16 (the seven-category human-control hard
invariant), and 19d.7 (critical-policy activation and policy-freeze
mechanics).

## Context

`docs/handover/PACK-07-SPEC.md` sections 7, 12, 20, 25, and 26 left
every final age/citizenship/incompatibility/residence/electoral-
threshold value as a policy decision, described a single, undifferentiated
application-to-active flow (section 20's evaluation flow), and flagged
the `ConflictAssessment` appeal-path question (whether to reuse canon's
existing `Appeal` entity, canon 14.3, or introduce a dedicated entity)
as explicitly unresolved (section 11, section 29). The project owner has
reviewed this and requires: continued non-fixation of political values;
a precisely-specified application lifecycle, mapped carefully onto
canon's existing `Membership` statuses (8.3) without silently redefining
them; an explicit list of which actions require consequential human
control; a resolved (not deferred) position on the appeal model; and
confirmation that public disclosure of membership status is opt-in or
legally mandated, never default.

The project owner has since issued a further, mandatory amendment,
incorporated directly into this ADR's own Decision text as item 6,
below: the exact evaluation and historical-reproducibility mechanics
for ADR-028's new `ProcessEligibilityPolicy` entity — how exactly one
applicable policy version is resolved for a concrete evaluation, and
how a past determination remains reproducible after a legal change
creates a new policy version.

The project owner has since issued a third, mandatory amendment,
incorporated directly into this ADR's own Decision text as item 7,
below: the exact evaluation mechanics for step-up authentication —
freshness-window checks, fail-closed behavior, and
`reauthentication_reason` surfacing — for the
`StepUpAuthenticationRequirement` policy model ADR-028 (item 7) fixes.

The project owner has since issued a fourth, mandatory amendment,
incorporated directly into this ADR's own Decision text as item 8,
below: the exact evaluation, deadline-handling, and reproducibility
mechanics for the `decision_effect`/`DigitalDecision`/`AssemblyDecision`
confirmation model ADR-028 (item 9) fixes.

The project owner has since issued a fifth, mandatory amendment,
incorporated directly into this ADR's own Decision text as amendments
to items 3 and 4 and as a new item 9, below: item 3's consequential-
action list is widened, and restated as a hard invariant
(ADR-028 item 10 fixes the canon-level statement); item 4's
`Appeal`-reuse decision is restated as this pack's own standing default
for any future appealable decision type, not only the two named here;
and item 9 fixes the exact mechanics for critical-policy activation —
multi-person approval verification and the policy-freeze rule
(ADR-028 item 12 fixes the canon-level classification and fields; the
corresponding narrow-read boundary consequence is fixed by ADR-027).

## Problem

Without this ADR, a future implementation would have no fixed
application-lifecycle shape to build against — `Membership.membership_status`
(8.3: `application_pending`, `verification_pending`, `active`,
`suspended`, `terminated`, `rejected`, `expired`) does not, by itself,
distinguish "eligibility review in progress" from "awaiting a human
decision," and overloading it with additional ad hoc values would
redefine an existing canonical field's semantics without its own
dedicated ADR — precisely the kind of silent field-redefinition this
project's established precedent (e.g. ADR-018's own D2/D3 treatment of
`GovernanceDecision`) always avoids. Leaving the `ConflictAssessment`
appeal-path question open past this drafting round would mean
implementation could begin without knowing whether `Appeal` (canon
14.3) is reused or a new entity is required — a canon-shape decision
that must be fixed before, not during, implementation.

## Considered options

- Option A — adopt the specification's sections 7/12/20/25/26 largely
  as drafted: policy values left open (unchanged), a single
  undifferentiated evaluation flow, and the appeal-path question left
  open past this round.
- Option B (the project owner's decision) — policy values remain
  unfixed; a precise six-state application lifecycle is defined and
  mapped onto `Membership.membership_status` via a new, dedicated
  record rather than overloading that field; the appeal model is
  resolved now, preferring reuse of `Appeal` where it fits, with a
  dedicated fallback entity otherwise; public disclosure defaults are
  restated as binding, not merely described; and `ProcessEligibilityPolicy`
  evaluations always resolve exactly one applicable version per a
  concrete process/jurisdiction/scope/date tuple, with every historical
  determination remaining reproducible against the version it was
  actually decided under.

## Decision

**Option B**, per the project owner's explicit instruction.

### 1. No final values fixed in code — restated, unchanged

No final ages, citizenship limits, incompatibility lists, residence
requirements, or electoral thresholds are fixed in code, in this ADR,
or anywhere in this pack's design. Every value identified in the
specification's own section 25 policy-decision inventory remains a
`governance-service`-activated policy value, configured via
`age_thresholds`/`citizenship_conditions`/`residence_conditions`/
`incompatibility_rules`/`membership_duration_rules` on
`ParticipantEligibilityPolicy`/`PartyMembershipEligibilityPolicy`
(sections 7, 8, 12, unchanged; ownership split per ADR-026).

### 2. Party-membership application lifecycle — a new, dedicated `MembershipApplication` record

**Decision (resolving item 4's "otherwise" branch below in favor of a
dedicated record):** a party-membership application's process states —
`application_pending`, `eligibility_review`, `human_decision_pending`,
`approved`, `rejected`, `activated` — are carried by a **new,
dedicated `MembershipApplication` entity**, owned by
`membership-service`, rather than overloading `Membership.membership_status`
(canon 8.3) with process-intermediate values it was never designed to
carry.

**Mapping onto canon's existing `Membership` statuses, carefully, not
silently:**

| `MembershipApplication.status` | Corresponding `Membership` row state                                                                                                                                                                                                                                                                                                                                |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `application_pending`          | No `Membership` row exists yet, **or** an existing row is at canon's own `application_pending` status (8.3) — the two are intentionally aligned in name, since both describe the same real-world moment.                                                                                                                                                            |
| `eligibility_review`           | Stage A (ADR-028, item 2) is in progress. `Membership` row, if created at this point, remains at `application_pending`/`verification_pending` (8.3) — never `active`.                                                                                                                                                                                               |
| `human_decision_pending`       | Stage A has produced a formal eligibility result; Stage B's authorized human decision has not yet been recorded. `Membership.membership_status` remains `verification_pending` (8.3).                                                                                                                                                                               |
| `approved`                     | The Stage B decision (ADR-028, item 2's decision-maker/policy-version/reason-code/decided-at/audit-reference record) has been recorded with a positive outcome. `Membership.membership_status` is **not yet** `active` at this point — see `activated`, below.                                                                                                      |
| `rejected`                     | The Stage B decision has been recorded with a negative outcome. `Membership.membership_status` moves to `rejected` (8.3, unchanged existing value) in the same transaction.                                                                                                                                                                                         |
| `activated`                    | Following an `approved` `MembershipApplication`, `Membership.membership_status` is set to `active` (8.3, unchanged existing value) — a distinct, final step from `approved`, so that "a human approved this application" and "this membership is now legally/organizationally in effect" remain two separately recorded facts, never collapsed into one transition. |

**Binding rule:** no code path may set `Membership.membership_status =
active` except as the `activated` step following a recorded `approved`
`MembershipApplication` — restating, in mechanical terms, ADR-028 item
2's "a passing eligibility evaluation must never automatically create
active party membership" rule. `MembershipApplication` itself is
immutable per state reached — a correction is always a new
`MembershipApplication` row (mirroring `AffiliationDeclaration`'s and
`ConflictAssessment`'s own `supersedes_*` pattern, sections 10–11 of the
specification), never an in-place status rewrite.

This resolves item 4 below's instruction not to leave the record-shape
question to implementation time: `MembershipApplication` is introduced
now, at the ADR level, specifically because canon's `Membership.membership_status`
enum (8.3) cannot safely carry `eligibility_review`/
`human_decision_pending` without redefining its existing meaning.

### 3. Consequential human control — explicit list, restated as a hard invariant

**Decision, amended by the project owner's fifth amendment.** The
following actions are, without exception, **consequential** and
require an authorized human decision, a `reason_code`, and a review
path (mirroring section 26 of the specification and INV-08's existing
critical-action/two-actor discipline where applicable):

- **Admission** — `MembershipApplication` reaching `approved`/`activated`
  (item 2, above).
- **Rejection** — `MembershipApplication` reaching `rejected`.
- **Suspension** — `Membership.membership_status → suspended` (8.3).
- **Termination or expulsion** — `Membership.membership_status →
terminated` (8.3).
- **Incompatibility finding** — `ConflictAssessment.status →
resolved_incompatible` (section 11 of the specification, unchanged).
- **Restoration of membership rights** — any transition out of
  `suspended` back toward `active`, or any `ConflictAssessment`
  re-evaluation (`expired_reevaluation_due` → a new, superseding
  `ConflictAssessment`) that lifts a prior restriction.
- **Denial of a fundamental member right, however produced** — the
  fifth amendment's own new, open-ended seventh category: any policy-
  evaluation outcome whose **effect** is to withhold a right a member
  would otherwise hold, whether or not it fits one of the six named
  labels above. This category exists precisely so a future
  implementation cannot route around the six named labels by producing
  the same practical denial through some other, unlabeled path.

**This list, together with the rule below, is now a hard, structural
invariant (ADR-028 item 10 fixes the canon-level statement), not merely
a documented convention:** no code path in this pack's design reaches
any of the seven outcomes above purely from a policy-evaluation
boolean, a timeout, or a missing reviewer defaulting to a decision —
silence is never approval, mirroring this project's established
fail-closed convention (INV-10, ADR-023 D1's identical rule for
`human_review_status`). The invariant binds by effect, not by label —
a future implementation that produces the practical effect of one of
the seven outcomes above through a code path not named here is still
bound by this rule, and a review that finds such a path must treat it
as a defect against this invariant, not as content this ADR simply
failed to anticipate.

### 4. Appeal model — resolved, not deferred

**Decision:** the specification's own section 11/29 open question is
now resolved. **Canon's existing `Appeal` entity (14.3) is reused**
for both `ConflictAssessment` appeals and `MembershipApplication`
rejection appeals, rather than introducing a dedicated
`MembershipAppeal` entity — `Appeal.decision_id` (14.3's own field
name, already generic — not `moderation_decision_id` or similarly
narrowly named) is confirmed, by direct inspection of canon 14.3, to be
a plain, undifferentiated reference with no field-level constraint
tying it to `ModerationDecision` specifically; `Appeal`'s own status
enum (`submitted`, `admissibility_review`, `under_review`, `upheld`,
`partially_upheld`, `rejected`, `withdrawn`) and its existing rule ("an
appeal must not be finally decided by the author of the original
decision") both transfer to a `ConflictAssessment`/`MembershipApplication`
target without any change in meaning.

**Mechanically:** an appeal of a `ConflictAssessment.status =
resolved_incompatible` (or any other terminal `resolved_*` outcome) or
of a `MembershipApplication.status = rejected` sets `Appeal.decision_id`
to the `conflict_assessment_id` or `membership_application_id` being
appealed (both new, opaque UUID-shaped identifiers, structurally
indistinguishable at the field level from any other `decision_id` this
entity already accepts). `Appeal`'s own reviewer-separation rule
(14.3) supplies the same self-review prohibition
`CONFLICT_REVIEW_SELF_APPROVAL_PROHIBITED` (ADR-029) already enforces
at the `ConflictAssessment` level — the two mechanisms are
complementary, not duplicative: `ConflictAssessment`'s own reviewer
separation governs the original decision; `Appeal`'s own reviewer
separation governs the appeal decision, and the two reviewers need not
be, and structurally are encouraged not to be, the same person.

**Fallback, not exercised by this decision:** had `Appeal.decision_id`
turned out to carry any `ModerationDecision`-specific constraint (it
does not, per the direct canon inspection above), a dedicated
`MembershipAppeal` entity would have been required instead — this ADR
records that this fallback was considered and is not needed, rather
than silently assuming reuse is safe.

**Canon impact:** reusing `Appeal` (14.3) generically for a second
target type requires no new entity, but does require a small,
additive canon clarification — `Appeal`'s own field documentation
(14.3) should note that `decision_id` may reference a
`ConflictAssessment` or `MembershipApplication` in addition to a
`ModerationDecision`, once ADR-028's canon-edit task is performed. This
is folded into ADR-028's own canon-addition scope, not a separate canon
change.

**Standing default, per the project owner's fifth amendment:** the
reasoning above — reuse canon's polymorphic `Appeal` entity via its
already-generic `decision_id` field, rather than introduce a
target-specific appeal entity — is now this pack's own **standing
default** for any future appealable decision type this pack, or a later
amendment to it, might introduce (for example, were a future amendment
to grant an appeal right against an `AssemblyDecision`'s own
`final_legal_decision`, `Appeal.decision_id` would be set to the
`assembly_decision_id` being appealed, exactly as it is set to a
`conflict_assessment_id`/`membership_application_id` today, with no new
entity and no new canon clarification beyond documenting the additional
target type). **This default may be overridden only where a dedicated
ADR demonstrates, by the same direct-field-inspection method used
here, that `Appeal`'s existing shape is actually insufficient for the
new target type** — the presumption runs in favor of reuse; departing
from it requires the same standard of proof this ADR itself applied
(a concrete, cited field-level constraint `Appeal` cannot accommodate),
not merely a preference for a dedicated entity.

### 5. Public disclosure — opt-in or legally mandated, never default

Restated as binding, not merely descriptive (extending ADR-028 item 3):
public disclosure of membership status is always either **opt-in** (the
subject's own informed, voluntary consent, evidenced and referenced —
`MEMBERSHIP_PUBLICATION_CONSENT_MISSING`, ADR-029, if claimed without
evidence) or **legally mandated** (one of ADR-028 item 3's other three
permitted bases: explicit legal basis, statutory requirement, or a
public-office/candidacy rule) — **never** a default arising merely from
`Membership.membership_status`'s own already-public-shaped enum values,
and never inferred from a caller's own assertion that disclosure is
"probably fine" for a given case.

### 6. `ProcessEligibilityPolicy` evaluation and historical-reproducibility mechanics

**Decision, per the project owner's explicit instruction.** Extending
item 1's "no final values fixed" rule and ADR-028 item 6's
`ProcessEligibilityPolicy` entity with the exact evaluation procedure:

- **Resolution.** For a concrete evaluation request — a subject
  reference, a `process_type`, a `jurisdiction`, a `scope_type`/
  `scope_id`, and an `effective_date` (defaulting to "now" for a live
  evaluation, but always an explicit, named input, never implicit) —
  `eligibility-service` resolves **exactly one** `ProcessEligibilityPolicy`
  version whose `(process_type, jurisdiction, scope_type, scope_id)`
  matches and whose `[effective_from, effective_until)` window covers
  `effective_date`. This mirrors, and extends with the explicit
  `effective_date` dimension, section 12's own "exactly one active
  version per tuple" invariant (unchanged for
  `ParticipantEligibilityPolicy`/`PartyMembershipEligibilityPolicy`,
  which do not carry a process/jurisdiction dimension).
- **No permanent per-person attribute.** The four electoral/process-
  eligibility claims (ADR-028, item 1) are never written to
  `IdentityRecord`, `Membership`, or any other entity as a standing
  fact — every evaluation is computed fresh from the resolved policy
  version plus the identity/membership facts current at
  `effective_date`, and the result is returned to the caller, never
  persisted as a reusable cache the next, differently-scoped evaluation
  could accidentally read.
- **Historical reproducibility.** Once a concrete determination has
  been made and recorded elsewhere (e.g. referenced by a
  `ParticipationCredential`, a `MembershipApplication` decision, or a
  `GovernanceDecision`), that determination's own recorded
  `applicable_policy_version` (ADR-027) is what must be used to
  reproduce it later — **never** the version currently active at the
  time of the later query. **A legal change creates a new
  `ProcessEligibilityPolicy` version (`supersedes_policy_id`, unchanged
  immutable-versioning pattern, section 12/ADR-028 item 4) and never
  rewrites, reinterprets, or silently re-evaluates a past determination
  under the new version.** This mirrors `GovernancePolicy`'s and this
  pack's own two Policy entities' established immutable-version
  guarantee (canon 19b.2; specification section 12), extended here to
  cover reproducibility of the _evaluation result_, not merely
  immutability of the _policy row_.
- **Public candidacy's two independent conditions (ADR-027).** When
  evaluating an `epd_public_candidate_nomination` process, this
  resolution procedure is run **twice**, independently — once for
  `party_office_candidacy_eligibility_met` (if the nomination is
  party-sponsored, resolved using `eligibility-service`'s combined
  identity/membership read, per ADR-028 item 1's corrected ownership)
  and once for `passive_electoral_eligibility_met` (the public
  election's own legal requirement, resolved using only the
  identity-layer read) — the two results are returned separately and
  are never merged into one combined boolean, per ADR-027's own
  "both may be required" rule.
- **No current German legal value is fixed by this mechanics
  definition** — restated from ADR-028 item 6: the Bundestag/European
  Parliament/Land/municipal process categories and their example
  citizenship/residence rules are illustrative and legal-basis
  references only; this ADR fixes only the _procedure_ by which
  whatever values a future `governance-service`-activated policy
  version actually contains are resolved and reproduced, never the
  values themselves.

### 7. Step-up authentication — evaluation mechanics

**Decision, per the project owner's explicit instruction.** Extending
ADR-028 item 7's `StepUpAuthenticationRequirement` policy model with
the exact evaluation procedure:

- **Resolution.** For a concrete action attempt — a subject reference,
  an `action_code`, and the subject's current `AuthenticationContext`
  (ADR-028 item 8) — the deciding service (whichever of
  `eligibility-service`/`membership-service` performs the action, per
  ADR-027's new step-up boundary) resolves the single **active**
  `StepUpAuthenticationRequirement` version for that `action_code`,
  mirroring item 6's own single-active-version resolution discipline
  (no separate mechanism is introduced for this second policy type).
- **Freshness-window checks.** The requirement is satisfied only if
  **all** of the following hold: the `AuthenticationContext`'s
  `authentication_assurance_level` meets or exceeds
  `assurance_requirement.required_authentication_assurance_level`; the
  underlying `IdentityRecord`'s `identity_assurance_level` meets or
  exceeds `assurance_requirement.required_identity_assurance_level`;
  where `fresh_authentication_required` is true, `now() -
session_authenticated_at` does not exceed `maximum_authentication_age`;
  and, where `assurance_requirement.required_attribute_freshness` names
  an `AttributeFreshnessRequirement`, the corresponding
  `attribute_valid_until` has not passed. **Any single failed condition
  fails the whole requirement** — conditions are never combined with an
  "or," and a stronger result on one dimension never compensates for a
  weaker result on another (restating ADR-028 item 8's own
  non-substitutability rule mechanically).
- **Fail-closed, unconditionally.** Where an applicable
  `AuthenticationContext` is missing, expired, or the resolution itself
  cannot be completed (e.g. no active `StepUpAuthenticationRequirement`
  version can be resolved for the given `action_code` and the caller
  has not supplied an explicit fallback), the action is **blocked**,
  never permitted by default — mirroring INV-10's fail-closed principle
  and ADR-023 D1's identical `human_review_status` rule (item 3,
  above). This is a structural invariant, not a best-effort check.
- **`reauthentication_reason` surfacing.** Where the requirement is not
  met, the caller receives the `reauthentication_reason` code from the
  resolved `StepUpAuthenticationRequirement` (never a generic failure)
  so that a future UI/API layer can prompt the correct kind of
  re-authentication (e.g. "re-enter your eID" vs. "re-authenticate with
  your second factor") — this ADR fixes only that the reason is
  surfaced, not any UI/API shape, which remains out of PACK-07's own
  scope.
- **`step_up_completed_at` is set only on success**, and only on the
  specific `AuthenticationContext` row that satisfied the requirement —
  it is never backfilled onto a different session, and never satisfies
  a _different_, subsequently-evaluated `StepUpAuthenticationRequirement`
  for a different `action_code` without that second requirement's own
  freshness-window check independently passing.
- **No caching of a "step-up satisfied" result across actions.**
  Exactly like item 6's own "no permanent per-person attribute" rule,
  a step-up evaluation's result is computed fresh for the specific
  action attempted and is never persisted as a standing fact usable by
  a later, different action.

### 8. Digital-decision confirmation — evaluation, deadline, and reproducibility mechanics

**Decision, per the project owner's explicit instruction.** Extending
ADR-028 item 9's `decision_effect`/`DigitalDecision`/`AssemblyDecision`
model with the exact mechanics:

- **Creation.** A `DigitalDecision` is recorded with `decision_effect`
  and `formal_confirmation_required` copied, immutably, from the
  `ProcessEligibilityPolicy` version active for that process at the
  moment the digital result is produced — mirroring item 6's own
  "recorded `applicable_policy_version` is what must be used to
  reproduce it later" rule, applied here to a process's legal-effect
  fields rather than its eligibility fields.
- **Immediate finality path.** Where `formal_confirmation_required` is
  false, `DigitalDecision.status` is set to `final` in the same
  transaction that records the digital result — no `AssemblyDecision`
  is ever created for such a `DigitalDecision`.
- **Confirmation-required path.** Where `formal_confirmation_required`
  is true, `DigitalDecision.status` is set to
  `formal_confirmation_required` and exactly one `AssemblyDecision` row
  is created, referencing it, with `status = pending` and
  `confirmation_deadline` copied from the applicable
  `ProcessEligibilityPolicy`.
- **Deadline handling — no silent auto-finalization.** A
  `confirmation_deadline` passing with `AssemblyDecision.status` still
  `pending` **never** causes the digital result to become final by
  default, and never causes any automatic transition of
  `AssemblyDecision.status` — mirroring item 3's "silence is never
  approval" rule (INV-10) exactly: a missed deadline is an operational/
  governance escalation concern for a future pack (ADR-028 item 9's
  Legal Decision Validity Pack), never a code-level default-to-confirmed
  or default-to-rejected transition.
- **Divergence is always explicit.** Where `AssemblyDecision.final_legal_decision`
  differs from the referenced `DigitalDecision.digital_result`,
  `AssemblyDecision.divergence_explanation` is **mandatory** — a
  transition to `confirmed`, `rejected`, or `returned_for_revision`
  without it, where the two results differ, is rejected by validation,
  never silently accepted with a null explanation.
- **Historical reproducibility.** Once recorded, neither `DigitalDecision`
  nor `AssemblyDecision` is ever rewritten in place — a correction
  (e.g. a re-run digital tally, a superseding assembly session) is
  always a new `DigitalDecision`/`AssemblyDecision` pair, referencing
  the original via an opaque `supersedes_*_id`-style field, mirroring
  every other immutable-versioning entity in this pack (`ProcessEligibilityPolicy`,
  `MembershipApplication`, `ConflictAssessment`) — never an in-place
  status or `final_legal_decision` rewrite.
- **`epd_public_candidate_nomination`'s three stages (ADR-028 item 9)**
  are evaluated and recorded as up to three independent
  `DigitalDecision`/`AssemblyDecision` chains — a preselection result
  reaching `final` does not imply the formal nomination's own
  `DigitalDecision` is final, and the formal nomination's own
  confirmation does not imply the legally final candidate-selection
  stage's result — each stage's own `decision_effect` and
  `formal_confirmation_required` are resolved independently, per item
  6's own "never merged into one combined boolean" discipline (ADR-027).
- **No universal physical-presence value fixed here** — restated from
  ADR-028 item 9: `permitted_participation_mode` is resolved by the
  same policy-version-resolution procedure as every other
  `ProcessEligibilityPolicy` field (item 6, above), never a
  code-level constant.

### 9. Critical policy activation — multi-person approval and policy-freeze mechanics

**Decision, per the project owner's explicit instruction.** Extending
ADR-028 item 12's `critical policy` classification
(`ParticipantEligibilityPolicy`, `ProcessEligibilityPolicy`,
`PartyMembershipEligibilityPolicy`, `StepUpAuthenticationRequirement`)
with the exact activation procedure:

- **Four independent gates, all required, none substituting for
  another.** A critical policy version transitions `draft → active`
  only when all of the following hold simultaneously: (1) a real,
  `approved` `GovernanceDecision` exists, verified via
  `verify_decision_authorizes_policy_activation` (unchanged); (2) that
  same read additionally confirms `multi_person_approval_met` — the
  `GovernanceDecision`'s own approval evidence names at least the
  policy-configured minimum number of distinct authorized approvers (the
  minimum itself is a policy value, never fixed here, mirroring every
  other numeric threshold in this pack); (3)
  `signed_policy_digest_reference` is populated with a reference to a
  signature over this exact version's canonical content; (4)
  `transparency_log_commitment_reference` is populated with a reference
  to that digest's own publication. A version missing any one of the
  four remains `draft` — there is no partial-activation state.
- **Fail-closed, unconditionally.** Where any of the four gates cannot
  be confirmed — including where the narrow read itself cannot be
  completed — the activation attempt is rejected outright, mirroring
  item 3's own hard-invariant fail-closed rule and INV-10 generally.
- **Policy-freeze mechanics.** Once a critical policy version is
  `active` and has been read by at least one evaluation for an
  in-progress process or decision (tracked as a simple "has this version
  ever been the resolved version for a live evaluation" fact, not a new
  persisted counter), that version may not be marked `superseded` until
  every process or decision that read it while `active` has itself
  reached a terminal state. A new version may still be created and even
  reach `active` status **for future evaluations** — the freeze applies
  only to retroactively changing the rule an already-in-progress
  evaluation is being judged under, mirroring `EligibilityRule`'s own
  freeze-on-ballot-open precedent (canon 9.1) and this pack's own item
  6 "historical reproducibility" rule, now extended from the evaluation
  _result_ to the policy _version's own supersession timing_.
- **No new field for the freeze check itself.** The freeze is derived
  from existing recorded facts (which policy version an evaluation
  actually resolved, per item 6's own resolution procedure, and whether
  that evaluation's own downstream process/decision has reached a
  terminal state) — never a new stored "is this version frozen" boolean
  that could itself drift out of sync with the facts it is meant to
  summarize.

## Consequences

`services/membership-service`'s eventual implementation gains one
additional entity, `MembershipApplication`, beyond the four the
specification's own section 3 table proposed — five new entities in
total once ADR-026's split is also accounted for
(`ParticipantEligibilityPolicy` under `eligibility-service`;
`PartyMembershipEligibilityPolicy`, `AffiliationDeclaration`,
`ConflictAssessment`, `MembershipApplication` under `membership-service`).
The appeal-path question the specification left open is now closed:
`Appeal` (14.3) is reused, requiring one small, additive canon
clarification (item 4, folded into ADR-028's scope) rather than a sixth
new entity. `eligibility-service`'s eventual implementation additionally
gains a concrete, testable resolution procedure for
`ProcessEligibilityPolicy` (item 6) — a version-resolution function
keyed on `(process_type, jurisdiction, scope_type, scope_id,
effective_date)`, returned results never persisted as a standing fact,
and every recorded `applicable_policy_version` reference remaining
independently reproducible against its own version, never the
currently-active one. `identity-service`'s eventual implementation
additionally gains a concrete, testable step-up-authentication
evaluation function (item 7) — a fail-closed, multi-condition freshness
check keyed on `action_code` plus the subject's current
`AuthenticationContext`, never cached across actions. Two new
canonical entities, `DigitalDecision` and `AssemblyDecision` (ADR-028
item 9), gain a concrete, testable confirmation-lifecycle procedure
(item 8) — immediate finality where no confirmation is required, an
explicit, non-auto-finalizing confirmation path otherwise, and a
mandatory divergence explanation wherever a confirming authority's
final legal decision differs from the digital result. The
consequential-action list (item 3) gains a seventh, open-ended category
and is now treated as a hard invariant rather than a documented
convention. `governance-service`'s eventual implementation gains one
additional check inside its existing
`verify_decision_authorizes_policy_activation` function
(`multi_person_approval_met`, item 9) — no new function, no new service
pair. `eligibility-service`'s and `membership-service`'s own critical
policy entities each gain a concrete, testable four-gate activation
check (item 9) before any version may reach `active`.

## Security impact

The explicit consequential-action list (item 3) and the
`MembershipApplication`/`Membership` two-step admission mechanics (item 2) together make ADR-028's two-stage admission rule concretely
checkable in code, not merely a documented intention. Reusing `Appeal`'s
own already-tested reviewer-separation rule for
`ConflictAssessment`/`MembershipApplication` appeals avoids introducing
a second, independently-implemented self-review-prohibition mechanism
that could drift from the first. The step-up-authentication mechanics
(item 7) close a distinct gap: without a fail-closed, multi-condition
evaluation procedure, a sensitive action could be authorized on a
session that is authenticated but stale, or on an identity that was
verified at a high assurance level long ago but whose current session
is weak — the "any single failed condition fails the whole requirement"
rule and the unconditional fail-closed default together foreclose that
class of error. The digital-decision confirmation mechanics (item 8)
close another: without an explicit, non-auto-finalizing deadline rule
and a mandatory divergence explanation, a missed confirmation deadline
or an unrecorded divergence between a digital result and a confirming
authority's own decision could each silently misrepresent what is, and
is not, legally final. The widened consequential-action list (item 3)
closes the residual gap a fixed, six-label list would otherwise leave
open — a future implementation cannot escape the human-decision
requirement by producing the same practical denial through an
unlabeled path. The critical-policy activation mechanics (item 9) close
a fourth class of error, distinct from the three above: a single
compromised or mistaken approver, an unsigned policy version, or an
unpublished activation could each, individually, let a policy governing
fundamental participation or membership rights take effect with
materially weaker assurance than an individual membership decision
already requires — the four independent gates and the policy-freeze
rule together close that gap without introducing any new persisted
"frozen" state that could itself drift out of sync with the facts it
summarizes.

## Data impact

One new canonical entity, `MembershipApplication` (owner:
`membership-service`, per ADR-026), with the six-state lifecycle in
item 2. `Appeal` (14.3) gains a documentation clarification (its
`decision_id` field may reference a `ConflictAssessment` or
`MembershipApplication`) but no new field, status, or ownership change.
Item 6 fixes evaluation _procedure_ only — `ProcessEligibilityPolicy`
itself is ADR-028's own entity, not introduced by this ADR, and item 6
adds no new field to it. Item 7 likewise fixes evaluation procedure
only — `StepUpAuthenticationRequirement` and `AuthenticationContext`
are ADR-028's own entities (items 7–8), not introduced by this ADR, and
item 7 adds no new field to either. Item 8 likewise fixes evaluation,
deadline, and reproducibility procedure only — `DigitalDecision` and
`AssemblyDecision` are ADR-028's own entities (item 9), not introduced
by this ADR, and item 8 adds no new field to either. Item 9 likewise
fixes activation procedure only — the `multi_person_approval_met`
check, `signed_policy_digest_reference`, and
`transparency_log_commitment_reference` fields are ADR-027's boundary
consequence and ADR-028's own canonical-field proposals (item 12)
respectively, not introduced by this ADR. No other canonical entity is
affected by this ADR.

## Migration impact

None — no `services/membership-service` directory, and no
`MembershipApplication` entity, exists yet.

## Reversibility

Reversible with cost before code exists (this stage). Once real
`MembershipApplication`/`Appeal`-reuse data exists, restructuring the
six-state lifecycle or reversing the `Appeal`-reuse decision in favor of
a dedicated `MembershipAppeal` entity would become a
migration-bearing, canon-level change.

## Related canon version

Authored against canon version `0.5.0`. Proposes canon content folded
into ADR-028's own `0.5.0 → 0.6.0` scope (the `MembershipApplication`
entity definition and the `Appeal.decision_id` documentation
clarification) — no separate canon-version bump beyond ADR-028's own.
