# CLAUDE-PACK-07 — Participation & Membership Policy: Final Consolidated Specification

**Status: consolidated, final draft.** This document supersedes
`docs/handover/PACK-07-SPEC.md` (the original working draft, now marked
superseded in place) and is the single, internally consistent
specification for PACK-07, synthesizing the original specification with
the project owner's approved ADR-026 through ADR-031 (all `proposed`)
and `docs/review/PACK-07-OWNER-DECISIONS.md`. **This document is not
itself an ADR, edits no canon text, and authorizes no implementation
code.** Per canon section 26, ADR-026 through ADR-031 must each reach
`accepted` status before any corresponding working code is written —
that acceptance has not happened yet; this document consolidates their
**drafted, `proposed`** content into one place so a future acceptance
and implementation pass has a single, non-contradictory reference
instead of six separate ADRs plus a superseded specification.

Every design decision below that originated as a specification proposal
and was subsequently amended by an ADR is stated here **only in its
final, ADR-amended form** — the original specification's now-superseded
alternative is not repeated as a live option, though it is cross-
referenced where useful for traceability. Where the specification and
the ADRs agree, this document restates the agreed design once, in one
place, rather than requiring a reader to cross-check seven documents.

**Updated to incorporate a fifth amendment round**, issued after the
owner approved ADR-026 through ADR-031 as the drafting direction:
`ParticipationRightsProfile` is now internal and non-authoritative
(section 10); atomic capability checks or single-purpose scoped
capability tokens are the only permitted enforcement mechanisms
(section 5); a hard invariant, widened to cover denial of any
fundamental member right, restates the two-stage admission rule
(section 14); canon's polymorphic `Appeal` is now this pack's own
standing default for any future appealable decision type (section 15);
`AffiliationDeclaration` gains temporal and verification fields
(section 14); timing unlinkability, transport unlinkability, and
privacy-preserving credential revocation are added to the future
cryptographic-protocol gate (section 17); and a `critical policy`
classification with multi-person approval, signed policy digests,
transparency-log commitments, and a policy-freeze rule now governs
activation of every policy entity this pack introduces (sections 6,
13, 17). One further item from this round — deterministic source-
reference mapping and coverage metadata for AI-generated summaries —
is, on inspection, PACK-06 (`AIProcessingRecord`) territory, not
PACK-07's implementation scope; PACK-07 itself still introduces no
AI-generated summary capability and CT-00-11 remains not applicable to
PACK-07's own implementation (section 1). Per the owner's sixth-round
correction below, the underlying future requirement is now preserved
here as an approved future architectural requirement (section 24),
rather than left as an open question.

**Updated a sixth time to apply three owner-directed consistency
corrections**, architectural approval having already been given to the
fifth-amendment content above: (1) the deterministic-source-reference/
AI-summary item is now stated as an approved **future** architectural
requirement, explicitly deferred to a future AI Processing amendment
pack and explicitly not modifying PACK-06 in this drafting round
(section 24); (2) the canon-impact section's new-entity count is
corrected from nine to the correct **ten** (section 23) — the list
itself was always complete; only the count word was wrong; (3) the
canon-impact section's new-`IdentityRecord`-field count is corrected
from seven to the correct **eight** (section 23) — likewise, the list
itself was always complete. None of these three corrections changes
any design decision, canon text, code, schema, OpenAPI content,
version, checksum, or ADR status.

## 0. Canon dependency and version state

```text
sha256(docs/canonical/TZ-00-domain-event-canon.md) =
  374b25fddfab88846622bf078b35c4246d8ad8c5d65bf43e6ac4e82653f74f74
CANON_VERSION = 0.5.0
REPOSITORY_VERSION = 0.6.0 (CLAUDE-PACK-06, externally PASSed)
```

Canon has **not** been opened for editing to produce this document and
remains byte-identical to the PACK-06 PASS state. Every reference below
to "proposed for canon `0.6.0`" is analysis, not an edit — no canon text
has been touched by this document, by any of ADR-026 through ADR-031,
or by `PACK-07-OWNER-DECISIONS.md`. `REPOSITORY_VERSION` would
separately move `0.6.0 → 0.7.0` at implementation time (a future, later
task), unchanged from the original specification's own section 0
observation.

**Governance record this document consolidates:**

- `docs/handover/PACK-07-SPEC.md` — the original specification (now
  superseded in place, retained as a historical draft).
- `docs/adr/ADR-026-pack-07-service-decomposition-policy-separation.md`
  — service decomposition and participant/party-membership policy
  separation. Status: `proposed`.
- `docs/adr/ADR-027-pack-07-cross-service-boundaries.md` — narrow-read
  cross-service boundaries, identity-verification/citizenship
  separation, process-specific electoral eligibility (boundary rules),
  step-up authentication and pseudonym boundary consequences. Status:
  `proposed`.
- `docs/adr/ADR-028-canon-0.6.0-participation-membership-context-additions.md`
  — canon `0.5.0 → 0.6.0` additions: electoral-eligibility claim
  separation, two-stage admission, membership privacy, identity/
  citizenship separation, `ProcessEligibilityPolicy`, step-up
  authentication policy model, assurance/freshness separation,
  `decision_effect`/formal-confirmation model. Status: `proposed`.
- `docs/adr/ADR-029-pack-07-reason-code-additions.md` — reason-code
  registry additions. Status: `proposed`.
- `docs/adr/ADR-030-pack-07-policy-mechanics-human-decisions.md` —
  `MembershipApplication` lifecycle mechanics, consequential human
  decisions, appeal-model resolution, `ProcessEligibilityPolicy`
  evaluation/reproducibility mechanics, step-up-authentication
  evaluation mechanics, digital-decision confirmation mechanics. Status:
  `proposed`.
- `docs/adr/ADR-031-pack-07-security-architecture-anti-correlation-protocol-agility.md`
  — domain pseudonyms, anti-correlation invariant, anonymous-endpoint
  isolation, Credential Issuer boundary, cryptographic-protocol
  agility, no-custom-cryptography, audit/queue properties, future-pack
  boundaries. Status: `proposed`.
- `docs/review/PACK-07-OWNER-DECISIONS.md` — the owner's own
  accept/amend/reject checklist for all six ADRs; **no ADR has been
  formally accepted as of this document**, notwithstanding the user's
  own framing of ADR-026 through ADR-031 as "the owner direction" for
  drafting purposes. This document treats every ADR's content as
  settled design for specification purposes, while leaving formal
  `proposed → accepted` status transitions to a separate, later
  governance action, per this project's established
  drafting-then-accepting-then-canon-editing sequence.

## 1. Goals

PACK-07 defines, without fixing any final political or legal value, how
EPD² Civic OS distinguishes and evaluates: (a) general platform
participation eligibility, (b) party membership eligibility and the
two-stage human-gated admission process, (c) process-specific electoral
and internal-voting eligibility, (d) conflicts of interest and
organizational-affiliation incompatibility, (e) the legal effect and,
where required, formal confirmation of a digital participation or
voting result, and (f) the identity-assurance, authentication-
assurance, and anti-correlation architecture that the above five areas
depend on without themselves re-implementing. Consistent with every
prior governance round in this project, no final age, citizenship rule,
incompatibility list, residence requirement, electoral threshold,
assurance-level minimum, or legal-effect value is selected anywhere in
this document — every one remains a `governance-service`-activated
policy value (section 6) or a party-statute-aligned configuration,
identified here only as a decision point and its configuration
location.

This document additionally goals to leave PACK-07 **internally
non-contradictory**: every claim, entity, ownership assignment, and
boundary rule below reflects exactly one design, the one the project
owner's approved ADRs settled on — not the original specification's
now-superseded alternative and not the ADR's amendment side by side.

## 2. Terminology

| Term                                       | Meaning in this document                                                                                                                                                                                                                                |
| ------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Platform participant**                   | A derived classification (never a stored entity): `Account.account_status = active` plus a passing `EligibilityDecision` for the action attempted. Requires no `Membership`.                                                                            |
| **Party member**                           | An active `Membership` row (canon 8.3, `membership_type = party`) satisfying `PartyMembershipEligibilityPolicy`'s continuing-eligibility conditions. A strict subset of platform participants — every party member is also a platform participant.      |
| **Identity verification**                  | Whether a specific identity was successfully verified (`verification_status`, canon 7.3, unchanged) — a distinct question from citizenship (section 7).                                                                                                 |
| **Identity assurance**                     | The assurance level of the identity **verification** itself (`identity_assurance_level`, renamed from the specification's `eid_assurance_level` — section 13).                                                                                          |
| **Authentication assurance**               | The assurance level of the **current authenticated session** (`authentication_assurance_level`, `AuthenticationContext` — section 13) — may be lower than identity assurance.                                                                           |
| **Attribute freshness**                    | How recently a specific verified attribute (e.g. current address) was reconfirmed (`attribute_verification_level`/`attribute_verified_at`/`attribute_valid_until` — section 13).                                                                        |
| **Step-up authentication**                 | A requirement that a sensitive action be authorized only by a sufficiently strong and fresh `AuthenticationContext`, evaluated per action (`StepUpAuthenticationRequirement` — section 13).                                                             |
| **Domain-scoped pseudonym**                | A `DomainPseudonymReference` — a per-domain (participant/membership/eligibility/credential-issuance/voting) opaque identifier; no universal cross-domain identity hash exists (section 17).                                                             |
| **Process-specific electoral eligibility** | Any of the four separated electoral/process-eligibility claims (section 9), always evaluated for a concrete process/jurisdiction/scope/date/policy version, never as one permanent attribute of a person.                                               |
| **`decision_effect`**                      | The declared legal/organizational effect of a digital participation or voting process's own result (section 16) — `advisory` \| `politically_binding` \| `internally_binding` \| `legally_final` \| `requires_formal_confirmation`.                     |
| **Formal confirmation lifecycle**          | The `DigitalDecision → AssemblyDecision` record pair used whenever a process's `decision_effect = requires_formal_confirmation` (section 16).                                                                                                           |
| **Narrow read**                            | A cross-service function returning only a derived boolean (plus a reason code where false) or an opaque reference — never a raw underlying field. The uniform cross-service discipline this entire pack, and every prior pack since PACK-04, relies on. |

## 3. Canonical and proposed entities

Legend: **C** = canonical, unchanged, already in `CANON_VERSION 0.5.0`.
**C+** = canonical, fields/statuses extended by this pack (proposed for
`0.6.0`). **P** = proposed, new entity (proposed for `0.6.0`). **P-fut**
= proposed concept, canon-impact identified only, deferred to a future
pack's own implementing ADR (not authorized by this document or by
ADR-031).

| Entity / concept                                                  | Status                                                                           | Canon section (if any) | Owner                                                                                                   |
| ----------------------------------------------------------------- | -------------------------------------------------------------------------------- | ---------------------- | ------------------------------------------------------------------------------------------------------- |
| `Account`                                                         | C                                                                                | 7.2                    | `account-service`                                                                                       |
| `IdentityRecord`                                                  | C+                                                                               | 7.3                    | `identity-service`                                                                                      |
| `EligibilityRule` / `EligibilityDecision` / `EligibilitySnapshot` | C                                                                                | 9.1–9.3                | `eligibility-service`                                                                                   |
| `ParticipationCredential`                                         | C                                                                                | 10.1                   | `credential-service`                                                                                    |
| `RoleAssignment`                                                  | C                                                                                | 8.4                    | `governance-service`                                                                                    |
| `GovernancePolicy` / `GovernanceDecision`                         | C                                                                                | 19b.2–19b.3            | `governance-service`                                                                                    |
| `Appeal`                                                          | C+                                                                               | 14.3                   | "Appeal Service" (canon's existing owner label) — reused, documentation-only clarification (section 15) |
| `Organization`, `CivicSpace`                                      | C, not implemented by this pack                                                  | 8.1, 8.2               | Deferred to PACK-08                                                                                     |
| `Membership`                                                      | C, implemented for the first time by this pack, `membership_type = party` scoped | 8.3                    | `membership-service`                                                                                    |
| `ParticipantEligibilityPolicy`                                    | P                                                                                | _(new)_                | **`eligibility-service`**                                                                               |
| `ProcessEligibilityPolicy`                                        | P                                                                                | _(new)_                | **`eligibility-service`**                                                                               |
| `PartyMembershipEligibilityPolicy`                                | P                                                                                | _(new)_                | `membership-service`                                                                                    |
| `AffiliationDeclaration`                                          | P                                                                                | _(new)_                | `membership-service`                                                                                    |
| `ConflictAssessment`                                              | P                                                                                | _(new)_                | `membership-service`                                                                                    |
| `MembershipApplication`                                           | P                                                                                | _(new)_                | `membership-service`                                                                                    |
| `StepUpAuthenticationRequirement`                                 | P                                                                                | _(new)_                | `eligibility-service` (versioned-policy ownership, mirrors `ParticipantEligibilityPolicy`)              |
| `AuthenticationContext`                                           | P                                                                                | _(new)_                | `identity-service`                                                                                      |
| `AssuranceRequirement` (reusable value shape)                     | P                                                                                | _(new)_                | Not independently owned — embedded by `StepUpAuthenticationRequirement`/`ProcessEligibilityPolicy`      |
| `AttributeFreshnessRequirement` (reusable value shape)            | P                                                                                | _(new)_                | Not independently owned — referenced by `AssuranceRequirement`                                          |
| `DigitalDecision`                                                 | P                                                                                | _(new)_                | `eligibility-service`                                                                                   |
| `AssemblyDecision`                                                | P                                                                                | _(new)_                | `eligibility-service`                                                                                   |
| `ParticipationRightsProfile`                                      | P, derived read model, never stored                                              | _(new)_                | Composed across `eligibility-service`/`membership-service`/`governance-service` (section 10)            |
| `DomainPseudonymReference`                                        | P-fut                                                                            | _(identified only)_    | Deferred — Identity & Authentication Security pack (section 24)                                         |
| `AntiCorrelationInvariant`                                        | P-fut                                                                            | _(identified only)_    | Deferred — elaborates existing INV-01/CT-00-08/CT-00-09 (section 17)                                    |
| `CryptographicProtocolProfile`                                    | P-fut                                                                            | _(identified only)_    | Deferred — Verifiable Voting Cryptography pack (section 24)                                             |

"Participant status" is deliberately **not** a stored entity — every
participant category (platform participant, eID-verified participant,
party member, role holder, observer/expert) remains a derived
classification, unchanged from the original specification's section 4,
computed from the entities above, never a field anyone sets directly.

## 4. Ownership

Resolving ADR-026's amendment to the original specification's section
18 in full — this is the **final, approved** ownership split, not one
of two options:

**`eligibility-service`** (existing service since PACK-02, extended by
this pack) owns:

- `ParticipantEligibilityPolicy` — general platform-participation
  policy (`account_registration`, `public_participation`, `discussion`,
  `initiative_creation`, `initiative_support`, `civic_consultation`).
- `ProcessEligibilityPolicy` — process-specific electoral/participation
  eligibility policy (section 9).
- General participant eligibility evaluation — the service's own,
  already-existing `EligibilityDecision`-producing machinery (canon
  9.2, unchanged), extended to consult `ParticipantEligibilityPolicy`
  and `ProcessEligibilityPolicy` as additional `rule_version` sources
  alongside the existing `EligibilityRule` (canon 9.1) mechanism.
- Participant-side capability derivation — the participant-facing half
  of `ParticipationRightsProfile` (`can_read_public`, `can_discuss`,
  `can_create_initiative`, `can_support_initiative`,
  `can_join_civic_consultation`).
- Process-specific electoral eligibility evaluation — `eligibility-service`
  is the **sole computing party** for all four electoral/process-
  eligibility claims (section 9), including the two party-internal
  ones, which it resolves by combining `ProcessEligibilityPolicy` with
  the narrow read into `membership-service` (section 5) — never by
  `identity-service` (which supplies verified facts only) and never by
  `membership-service` (which is read _from_, never the computing
  party).
- `StepUpAuthenticationRequirement` — the step-up authentication policy
  model (section 13), mirroring `ParticipantEligibilityPolicy`'s own
  versioned-policy ownership.
- `DigitalDecision` and `AssemblyDecision` — the legal-effect and
  formal-confirmation record pair (section 16), owned alongside
  `ProcessEligibilityPolicy` since both record the outcome of a process
  `ProcessEligibilityPolicy` already governs.

**`membership-service`** (new service, this pack's first implementation)
owns:

- `Membership` (canon 8.3, implemented for the first time by this pack,
  `membership_type = party` scoped — the field itself stays open for
  future non-party membership types).
- `MembershipApplication` — the six-state party-membership application
  lifecycle (section 8).
- `PartyMembershipEligibilityPolicy` — party-specific eligibility
  policy (party-scoped age thresholds, citizenship/residence
  conditions, incompatibility rules, membership-duration rules,
  exemptions, transitional rules).
- `AffiliationDeclaration` — declared external affiliations (section
  14).
- `ConflictAssessment` — conflict-of-interest and incompatibility
  review lifecycle (section 14).
- Human membership admission and continuing-membership workflows — the
  two-stage admission process (section 8), suspension, termination, and
  re-evaluation lifecycle.

**Unchanged owners, reused, not duplicated:** `identity-service`
(`IdentityRecord`, `AuthenticationContext`), `credential-service`
(`ParticipationCredential`), `governance-service` (`RoleAssignment`,
`GovernancePolicy`, `GovernanceDecision`, and the sole activation
authority for every new policy entity above), "Appeal Service"
(`Appeal`, reused per section 15).

**Binding rules, restated without qualification (ADR-026 item 4):**

- Participant policy and party-membership policy remain independently
  versioned and independently activated — activating one never
  activates, supersedes, or otherwise affects the other.
- A platform participant does not require a `Membership` record — every
  participant-level capability is reachable through
  `ParticipantEligibilityPolicy` alone.
- `eligibility-service` must not create or mutate `Membership`,
  `AffiliationDeclaration`, `ConflictAssessment`, `MembershipApplication`,
  or `PartyMembershipEligibilityPolicy` — those remain exclusively
  `membership-service` commands.
- `membership-service` must not become the owner of general Civic OS
  participation eligibility — `EligibilityRule`, `EligibilityDecision`,
  `EligibilitySnapshot`, `ParticipantEligibilityPolicy`, and
  `ProcessEligibilityPolicy` remain exclusively `eligibility-service`'s,
  even though the latter two are new content this pack introduces.

## 5. Service boundaries

Every cross-service edge is a narrow, purpose-built read returning only
derived booleans, opaque references, or reason codes — modeled directly
on `verify_role_assignment_for_action`'s (ADR-022) and
`verify_decision_authorizes_policy_activation`'s own established
precedent. This is the **final, approved** boundary set (ADR-027,
including its amendments):

| Edge                                                                                                                                                   | Direction                                                                  | Purpose                                                                                                                                                                                                                                                                                                                                                                                                                  |
| ------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `membership-service → identity-service`                                                                                                                | Read-only, narrow                                                          | Resolve `identity_verified`, `identity_assurance_requirement_met`, `age_requirement_met`, `citizenship_requirement_met`, `residence_requirement_met` — **never** any of the four electoral/process-eligibility claims, and never raw `IdentityRecord` fields.                                                                                                                                                            |
| `eligibility-service → identity-service`                                                                                                               | Read-only, narrow (first-ever `eligibility-service` cross-pack dependency) | Resolve the same identity-layer claims above, plus `territorial_scope_requirement_met`, for `active_electoral_eligibility_met`/`passive_electoral_eligibility_met` evaluation.                                                                                                                                                                                                                                           |
| `eligibility-service → membership-service`                                                                                                             | Read-only, narrow (new edge, reused for two purposes, never duplicated)    | Resolve `required_membership_status_met` / `membership_duration_requirement_met` — used both for general membership-gated participant processes and, combined with the identity-service read above, to resolve `party_internal_voting_eligibility_met`/`party_office_candidacy_eligibility_met`.                                                                                                                         |
| `membership-service → eligibility-service`                                                                                                             | Read-only, reused unchanged                                                | Read an existing `EligibilityDecision` (canon 9.2) where a concrete process already requires one, plus whether `ParticipantEligibilityPolicy`-derived participant capabilities are currently satisfied — never the raw policy row.                                                                                                                                                                                       |
| `membership-service` / `eligibility-service → governance-service`                                                                                      | Read-only, narrow                                                          | `verify_decision_authorizes_policy_activation` (policy activation) — **as of the fifth amendment, this read's return shape additionally includes `multi_person_approval_met`** (ADR-027, ADR-028 item 12, ADR-030 item 9), one of the four independent critical-policy activation gates (section 6); a second narrow read verifies a `ConflictAssessment`'s or `MembershipApplication`'s `decision_authority_reference`. |
| `membership-service` / `eligibility-service → identity-service` (step-up)                                                                              | Read-only, narrow (new)                                                    | Resolve `authentication_step_up_satisfied` plus a `reauthentication_reason` code — never the raw `AuthenticationContext` row or any raw assurance/freshness field.                                                                                                                                                                                                                                                       |
| `membership-service → credential-service`                                                                                                              | Read-only, reused unchanged                                                | Optional: verify an existing `ParticipationCredential` where an action already requires one.                                                                                                                                                                                                                                                                                                                             |
| `governance-service → membership-service` / `eligibility-service`                                                                                      | **None proposed**                                                          | `GovernanceDecision.subject_reference` is generic enough to reference a policy-activation or conflict subject without a new typed read.                                                                                                                                                                                                                                                                                  |
| `{membership,eligibility}-service → voting-service` / `tally-service` / `delegation-service` / `credential-service.domain` / `identity-service.domain` | **Forbidden, structural**                                                  | No path from participation/membership/affiliation/conflict/process data to vote content or vote linkability (CT-00-09).                                                                                                                                                                                                                                                                                                  |
| `{membership,eligibility}-service → ai-processing-service`                                                                                             | **None**                                                                   | No AI-assisted decision-making anywhere in this pack's design.                                                                                                                                                                                                                                                                                                                                                           |

**Enforcement mechanism — atomic capability checks or single-purpose
scoped capability tokens, exclusively (fifth amendment, item 2; ADR-026,
ADR-027).** Every one of the edges in the table above, and every
cross-service or frontend consumer of this pack's data more generally,
must enforce an action using exactly one of two mechanisms:

1. **Atomic capability check** — a narrow, synchronous, single-purpose
   read that returns one boolean (or a small closed set of booleans plus
   reason codes) answering exactly one authorization question for
   exactly one action, in the same style as every read in the table
   above. The caller branches on that one boolean and nothing else.
2. **Single-purpose scoped capability token** — an existing
   `ParticipationCredential` (canon 10.1), scoped to exactly one action
   or process, presented and verified at the point of use.

No third mechanism is permitted. In particular, **no service, no
frontend, and no future consumer of any kind may read
`ParticipationRightsProfile` and branch on its fields as the means of
granting or denying an action** — that profile is internal and
non-authoritative by design (section 10) and carries no enforcement
authority whatsoever, however convenient reading it might seem.

**Explicitly prohibited, restated without qualification:** raw
`Membership` status, affiliation details, identity attributes, birth
date, citizenship documents, or organization names must never be
exposed through any cross-service API, in either direction. Domain-
scoped pseudonyms (section 17) are opaque to both `eligibility-service`
and `membership-service`; neither service derives, compares, or
correlates a pseudonym value across domains.

**Regional scope and `Organization` references (section 11):** both
services treat `Membership.organization_id` and every
`scope_type`/`scope_id`/`jurisdiction` field as opaque, caller-supplied
references, never dereferenced — neither service assumes a live
`Organization`/`CivicSpace` entity exists until PACK-08 defines one.

## 6. Policy models

Both `ParticipantEligibilityPolicy` and `PartyMembershipEligibilityPolicy`
share one common versioned shape (mirroring `GovernancePolicy`'s own
`draft → active → superseded` pattern, canon 19b.2):

```text
{Participant|PartyMembership}EligibilityPolicy:
  policy_id
  policy_version
  status                     — draft | active | superseded
  scope_type                 — open string (structure only, no
                                enumerated regional hierarchy)
  scope_id                   — opaque, nullable
  effective_from
  effective_until            — nullable
  adopted_by_decision_id      — non-nullable; a `GovernanceDecision`
                                reference
  age_thresholds              — list of {action_code, minimum_age,
                                maximum_age}
  citizenship_conditions       — list of structured conditions
  residence_conditions         — list of structured conditions
  incompatibility_rules        — list of `conflict_type` values
                                (`PartyMembershipEligibilityPolicy` only)
  membership_duration_rules    — nullable (`PartyMembershipEligibilityPolicy`
                                only)
  exemptions                  — list of structured exemption records
  transitional_rules           — structured payload, never silently
                                applied
  supersedes_policy_id         — nullable; corrections are always a new
                                version, never a rewrite

  # Critical-policy activation fields (fifth amendment, item 7;
  # ADR-027, ADR-028 item 12, ADR-030 item 9 — see below):
  signed_policy_digest_reference        — non-nullable once `active`
  transparency_log_commitment_reference — non-nullable once `active`
```

`ProcessEligibilityPolicy` (owner: `eligibility-service`, ADR-028 item
6, amended by item 9 with the legal-effect fields in section 16 below)
shares the same versioning discipline but is keyed by a concrete
process, not by a generic scope alone:

```text
ProcessEligibilityPolicy:
  policy_id
  policy_version
  status                          — draft | active | superseded
  process_type                    — open string; at least the nine
                                     categories in section 9
  jurisdiction                    — open string
  scope_type                      — open string
  scope_id                        — opaque, nullable
  eligible_citizenship_set        — list of ISO 3166-1 codes or a
                                     citizenship rule reference
  residence_rule
  habitual_residence_rule
  minimum_age                     — integer | null
  active_electoral_eligibility_rule
  passive_electoral_eligibility_rule
  party_internal_voting_rule       — nullable for non-party process types
  party_office_candidacy_rule      — nullable for non-party process types
  effective_from
  effective_until                 — nullable
  legal_basis                     — illustrative/reference only, never a
                                     fixed value
  adopted_by                      — non-nullable `GovernanceDecision`
                                     reference
  supersedes_policy_id            — nullable

  # Additional fields (section 16, legal effect and confirmation):
  decision_effect                 — advisory | politically_binding |
                                     internally_binding | legally_final |
                                     requires_formal_confirmation
  formal_confirmation_required    — boolean
  formal_confirmation_authority    — open string/reference, opaque
  secret_ballot_required           — boolean
  permitted_participation_mode     — open string/set; never a universal
                                     physical-presence rule
  required_assurance_level         — nullable `AssuranceRequirement`
                                     reference (section 13)
  accessibility_profile            — open string/reference; deferred in
                                     detail (section 24)

  # Critical-policy activation fields (fifth amendment, item 7;
  # ADR-027, ADR-028 item 12, ADR-030 item 9 — see below):
  signed_policy_digest_reference        — non-nullable once `active`
  transparency_log_commitment_reference — non-nullable once `active`
```

**Invariant, restated without qualification:** exactly one `active`
version per `(policy_type, scope_type, scope_id)` tuple for the two
generic policies, and exactly one `active` version per
`(process_type, jurisdiction, scope_type, scope_id)` tuple at any given
`effective_date` for `ProcessEligibilityPolicy` — resolved fresh for
every evaluation, never cached as a standing fact (section 9's
mechanics). Every superseded version remains immutable and queryable.

**Governance boundary (ADR-026/027, restated):** both policy entities
are physically owned and evaluated by their respective owning service,
but every transition into `active` status requires a non-nullable
`adopted_by_decision_id`/`adopted_by` referencing a real, `approved`
`GovernanceDecision`, verified by
`governance-service.verify_decision_authorizes_policy_activation`.
Neither owning service may: silently modify an active policy in place;
activate a new version itself without a verified `GovernanceDecision`;
waive a requirement without an authorized exception rule; or self-
approve an eligibility conflict.

**Critical policy classification and four-gate activation (fifth
amendment, item 7; ADR-027, ADR-028 item 12, ADR-030 item 9).**
`ParticipantEligibilityPolicy`, `ProcessEligibilityPolicy`,
`PartyMembershipEligibilityPolicy`, and `StepUpAuthenticationRequirement`
(section 13) are each classified as a **critical policy**. A critical
policy's transition into `active` status requires all four of the
following, independently and without substitution — if any one is
missing, activation fails closed:

1. A verified, `approved` `GovernanceDecision`
   (`adopted_by_decision_id`/`adopted_by`, as already required above).
2. `multi_person_approval_met = true`, returned by the extended
   `verify_decision_authorizes_policy_activation` read (section 5).
3. `signed_policy_digest_reference` populated with a reference to a
   cryptographic signature over the policy's own content.
4. `transparency_log_commitment_reference` populated with a reference
   to a public commitment recorded via PACK-04's existing Transparency
   Context machinery (`PublicLedgerEntry`/`AuditExportPackage`) — no new
   publication infrastructure is introduced.

**Policy-freeze rule (fifth amendment, item 7; ADR-030 item 9,
extending CT-00-10):** once a critical policy version is `active` and
has been used by an in-progress process, it cannot be superseded until
that process reaches a terminal state — mirroring `EligibilityRule`'s
freeze-on-ballot-open precedent (canon 9.1). This is derived from
existing facts (which policy version an evaluation resolved, and
whether that evaluation's downstream process is terminal); no new
persisted "frozen" boolean is introduced.

## 7. Participant verification — identity rules

**Nine separate concepts, never conflated (ADR-028 item 5, ADR-027):**

1. Identity verification — `verification_status` (canon 7.3, unchanged).
2. Identity assurance level — `identity_assurance_level` (renamed from
   `eid_assurance_level`; section 13).
3. Identity scheme/provider — `identity_scheme` (renamed from
   `identity_verification_method`) — open, extensible, non-exhaustive:
   `de_personalausweis_online`, `eu_eea_eid_card`, `eidas_foreign_eid`,
   `other_approved_method`. Never itself a citizenship signal, and
   never a closed list.
4. Citizenship — `citizenship_status` (list of citizenships, supports
   statelessness and multiple citizenship — never a single boolean).
5. Residence status — `residence_status.residence_type`.
6. Habitual residence — one value of `residence_status.residence_type`.
7. Territorial connection — `residence_status.territorial_connection`.
8. Active electoral eligibility — `active_electoral_eligibility_met`
   (section 9).
9. Passive electoral eligibility — `passive_electoral_eligibility_met`
   (section 9).

**Binding rules, restated without qualification:**

- No rule anywhere in this pack's design may equate a successful
  identity verification — through any route — with German citizenship,
  or with any specific citizenship. `identity_verified` and
  `identity_assurance_requirement_met` are derived exclusively from
  `verification_status`/`identity_assurance_level`; they never feed,
  substitute for, or are derived from `citizenship_requirement_met`.
- No rule anywhere in this pack's design may restrict verified
  participation, party-membership application, or party membership to
  German citizens. A citizen of another EU/EEA state, once identity-
  verified through any supported route, may become a verified
  participant, applicant, or member — subject only to whichever policy
  conditions and legal requirements actually apply (policy values,
  never fixed here).
- Verification routes are extensible and non-exhaustive — a new route
  is added by configuration, never by canon edit.
- Multiple citizenships are never collapsed into a single German/
  non-German boolean.
- Raw identity documents, full citizenship records, exact address, or
  full date of birth are never distributed across services.
- The right to perform a concrete action is always evaluated separately
  by action type, jurisdiction, territorial scope, residence
  requirement, citizenship requirement, and active/passive electoral
  eligibility (where applicable) — never as one combined check.

**`IdentityRecord` (canon 7.3) fields, existing vs. proposed:**

| Field                                                                                                                                                                      | Status                                              |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| `identity_record_id`, `account_id`, `verification_provider`, `verification_status`, `verified_at`, `expires_at`, `country`, `duplicate_check_status`, `provider_reference` | Canon 0.5.0, unchanged                              |
| `date_of_birth`, `citizenship_status`, `residence_status`                                                                                                                  | Proposed for 0.6.0, additive, nullable              |
| `identity_assurance_level` (renamed from `eid_assurance_level`)                                                                                                            | Proposed for 0.6.0, additive, nullable              |
| `identity_scheme` (renamed from `identity_verification_method`)                                                                                                            | Proposed for 0.6.0, additive, nullable              |
| `attribute_verification_level`, `attribute_verified_at`, `attribute_valid_until`                                                                                           | Proposed for 0.6.0, additive, nullable (section 13) |

## 8. Membership application

**Two-stage process, mandatory, restated without qualification
(ADR-028 item 2, ADR-030 item 2):** `Membership.membership_status`
(canon 8.3) may never move directly from an application state to
`active` as the automatic output of a policy evaluation.

- **Stage A — formal eligibility evaluation.** `membership-service`
  evaluates the applicant against the currently-active
  `PartyMembershipEligibilityPolicy` and produces a formal eligibility
  result, carrying its own `reason_codes` where negative. **A passing
  Stage A result never, by itself, creates or activates a `Membership`
  row.**
- **Stage B — authorized human membership-application decision.** A
  `Membership` row may reach `active` status only after an explicit,
  approved decision carrying: a decision-maker/competent-body reference;
  the `policy_version` Stage A was evaluated against; a `reason_code`;
  `decided_at`; an audit reference (`AuditEvent`).

**`MembershipApplication` — a new, dedicated entity (ADR-030 item 2),
never overloading `Membership.membership_status`:**

Six states: `application_pending`, `eligibility_review`,
`human_decision_pending`, `approved`, `rejected`, `activated`, mapped
onto `Membership.membership_status` (canon 8.3) as follows:

| `MembershipApplication.status` | Corresponding `Membership` row state                                                                                          |
| ------------------------------ | ----------------------------------------------------------------------------------------------------------------------------- |
| `application_pending`          | No `Membership` row yet, or an existing row at canon's own `application_pending`                                              |
| `eligibility_review`           | Stage A in progress; `Membership`, if created, remains `application_pending`/`verification_pending`                           |
| `human_decision_pending`       | Stage A produced a result; Stage B's decision not yet recorded; `Membership.membership_status` remains `verification_pending` |
| `approved`                     | Stage B decision recorded, positive; `Membership.membership_status` **not yet** `active`                                      |
| `rejected`                     | Stage B decision recorded, negative; `Membership.membership_status → rejected` in the same transaction                        |
| `activated`                    | Following an `approved` application, `Membership.membership_status → active` — a distinct, final step                         |

**Binding rule:** no code path may set `Membership.membership_status =
active` except as the `activated` step following a recorded `approved`
`MembershipApplication`. `MembershipApplication` is immutable per state
reached — a correction is always a new row (mirroring
`AffiliationDeclaration`'s/`ConflictAssessment`'s own `supersedes_*`
pattern).

**The same two-stage principle applies symmetrically to suspension,
termination/expulsion, and restoration** — no automated system may
permanently admit, reject, suspend, or expel a person without a human
decision (section 14).

## 9. Process-specific electoral eligibility

**Never one permanent attribute of a person (ADR-028 item 6, ADR-027,
ADR-030 item 6).** Electoral and process eligibility is always evaluated
for a concrete `(process_type, jurisdiction, scope_type, scope_id,
effective_date)` tuple, against exactly one applicable
`ProcessEligibilityPolicy` version (section 6).

**Four separated claims, replacing the original specification's single,
generic `electoral_eligibility_met` — this replacement applies
everywhere in this document and in every future implementation,
without exception:**

- `active_electoral_eligibility_met` — the right to vote in the
  applicable public electoral process.
- `passive_electoral_eligibility_met` — the right to stand as a
  candidate in that same public electoral process.
- `party_internal_voting_eligibility_met` — the right to vote in
  internal party decisions.
- `party_office_candidacy_eligibility_met` — the right to stand for a
  party office.

**No single field or flag ever represents "electoral eligibility"
generically** — every consumer states which of the four questions it is
asking. `active_electoral_eligibility_met`/`passive_electoral_eligibility_met`
are resolved using only identity-layer facts (age, citizenship,
residence, territorial scope); `party_internal_voting_eligibility_met`/
`party_office_candidacy_eligibility_met` additionally combine the
`eligibility-service → membership-service` narrow read (section 5) — no
second read is introduced for this purpose, and `membership-service`
never computes an electoral-eligibility claim itself.

**Supported process categories** (open string, extensible, at least
these nine): `bundestag_election`, `european_parliament_election_de`,
`land_election`, `municipal_district_election`,
`epd_public_consultation`, `epd_participant_poll`, `epd_member_vote`,
`epd_party_office_election`, `epd_public_candidate_nomination`.

**Same person, different results — worked example (illustrative, not a
fixed legal determination):** an EU citizen residing in Berlin is
eligible for the Berlin municipal/district process and the European
Parliament process in Germany; **not** eligible for the Bundestag
process (German citizenship required); eligible for an EPD public
consultation under `ParticipantEligibilityPolicy`; eligible for a
party-member vote only if `PartyMembershipEligibilityPolicy`'s own
membership requirements are additionally met.

**Public candidacy distinguishes two independently-required conditions,
never conflated:** party-internal permission to stand
(`party_office_candidacy_eligibility_met`) and legal passive electoral
eligibility (`passive_electoral_eligibility_met`) — an
`epd_public_candidate_nomination` process may require both; satisfying
one never implies the other.

**Evaluation mechanics (ADR-030 item 6):** exactly one applicable
`ProcessEligibilityPolicy` version is resolved per evaluation request,
never persisted as a standing per-person fact; a past determination
remains reproducible against the `applicable_policy_version` it was
actually decided under, never re-evaluated against whatever version is
current at query time; a legal change creates a new policy version and
never rewrites a past determination. For `epd_public_candidate_nomination`,
this resolution procedure runs twice, independently, for the two
conditions above, and the two results are never merged into one
combined boolean.

**No current German (or other jurisdiction's) legal value is fixed
anywhere in this document** — the Bundestag/European Parliament/Land/
municipal examples are illustrative and legal-basis references only.

## 10. Rights derivation — `ParticipationRightsProfile`

**Internal, non-authoritative, non-persisted derived view (fifth
amendment, item 1; ADR-026 item 3).** `ParticipationRightsProfile` is
strictly an internal display/summary aid — for example, rendering a
"what can I currently do" view to a participant. **It is never persisted,
never returned as an authorization decision, and never the mechanism
that grants or denies an action.** The only two permitted enforcement
mechanisms for any action are the atomic capability check and the
single-purpose scoped capability token fixed in section 5; no service,
frontend, or future consumer may read this profile and branch on its
fields as an authorization step. A derived, non-stored read model
(mirroring `FinalityStatus`/`DisclosureStatus`'s own established
stored-vs-derived split — computed at query time, never itself a
system-of-record row):

```text
ParticipationRightsProfile (derived, computed on demand):
  subject_reference
  evaluated_at
  can_read_public
  can_discuss
  can_create_initiative
  can_support_initiative
  can_join_civic_consultation
  can_apply_for_party_membership
  can_vote_as_party_member
  can_stand_for_party_office
  can_hold_special_role
```

**Composed from three independently-computed inputs, no single service
required to hold all three's raw state (ADR-026 item 3):**

- **Participant eligibility results**, computed by `eligibility-service`
  (`can_read_public` through `can_join_civic_consultation`, plus
  process/scope requirements via `ProcessEligibilityPolicy` where the
  process being evaluated needs one).
- **Membership-derived minimum claims**, computed by `membership-service`
  (`can_apply_for_party_membership`, `can_vote_as_party_member`,
  `can_stand_for_party_office`, from `Membership.membership_status` and
  `PartyMembershipEligibilityPolicy` evaluation — exposed to
  `eligibility-service` only as `required_membership_status_met`/
  `membership_duration_requirement_met`, section 5).
- **Applicable `RoleAssignment` checks**, read unchanged from
  `governance-service` (`can_hold_special_role`) — no new field on
  `RoleAssignment` itself.

Whichever service or thin composing caller ultimately assembles the
full profile, each service answers only for the dimension it owns,
mirroring this project's established narrow-read discipline rather than
centralizing composition logic inside one service with read access to
the other two's storage.

## 11. Regional scope preparation

Unchanged from the original specification's Design decision D4, retained
by ADR-027 (regional-scope/`Organization`-reference handling):
`Membership.organization_id` and every `scope_type`/`scope_id`/
`jurisdiction` field (on both generic policies and
`ProcessEligibilityPolicy`) are treated as opaque, caller-supplied
references, never dereferenced by `eligibility-service` or
`membership-service`. `scope_type = region` is deliberately left an open
string with **no** enumerated Bund/Land/Kreis/Bezirk/Ort values, so
PACK-08 can slot a real hierarchy in later without this pack's own
schema needing to change. A single, well-known identifier representing
"the party" (EPD Plattform e.V.) is provisioned as repository-level
configuration rather than requiring a live `Organization` entity or
service to exist first. Neither service may assume a live `Organization`
or `CivicSpace` entity exists until PACK-08 defines one.

## 12. Privacy

**Membership data is restricted by default, not public by default
(ADR-028 item 3), notwithstanding canon 8.3's own already-public-shaped
`membership_status` enum.** The following facts must **not** be public
by default: the existence or status of a membership application; active
membership; suspension; rejection; termination; membership history.

**Publication is permitted only through one of:** an explicit legal
basis; a statutory requirement specific to the applicable jurisdiction
or party form; a public-office/candidacy rule; informed, voluntary
consent from the subject. No default publication path exists absent one
of these four bases — a structural default, not a documented
recommendation, restated as **binding** by ADR-030 item 5, never merely
descriptive.

**Cross-service and public outputs use only the minimum derived claims**
already established by this document — never a raw `membership_status`
value, application record, or history listing.

| Layer                       | Contains                                                                                                                                                 | Who may read it                                                                                                    |
| --------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| Raw verified attributes     | `IdentityRecord.date_of_birth`, `.citizenship_status`, `.residence_status`, `.identity_assurance_level`, `.attribute_*`                                  | `identity-service` only, never exposed raw                                                                         |
| Derived eligibility claims  | `age_requirement_met`, `citizenship_requirement_met`, `residence_requirement_met`, the four electoral/process claims, `authentication_step_up_satisfied` | `membership-service`, `eligibility-service`, and any consumer needing a yes/no answer — never the underlying value |
| Public membership status    | `Membership.membership_status`, subject to section 12's own restricted-by-default rule                                                                   | Only per one of the four permitted publication bases above                                                         |
| Restricted affiliation data | `AffiliationDeclaration.declared_reference`, evidence content                                                                                            | `membership-service` and an authorized `ConflictAssessment` reviewer only                                          |
| Conflict-review evidence    | `ConflictAssessment.evidence_references` (opaque)                                                                                                        | Authorized reviewer only                                                                                           |

**Binding rule, restated without qualification:** raw birth date,
identity documents, citizenship documents, or affiliation details are
never spread across services — every cross-service signal is one of the
derived boolean claims above, plus opaque references. This is the same
discipline CT-00-08 already enforces project-wide.

## 13. Assurance and step-up authentication

**Five distinct concepts, strictly separated, never substitutable
(ADR-028 item 8):**

1. **Identity assurance level** — `identity_assurance_level` (renamed
   from `eid_assurance_level`; `IdentityRecord`, 7.3) — the assurance
   of the identity **verification** itself, at the time it was
   performed. Does not expire on its own and does not reflect the
   current session.
2. **Authentication assurance level** — `authentication_assurance_level`
   (`AuthenticationContext`, new) — the assurance of **this specific
   authentication event**, which may be lower than the identity
   verification's own assurance level.
3. **Attribute verification level, verified-at, valid-until** —
   `attribute_verification_level`/`attribute_verified_at`/
   `attribute_valid_until` (`IdentityRecord`) — freshness of a
   **specific verified attribute**, distinct from overall identity
   verification.
4. **Session authentication time and method** —
   `session_authenticated_at`/`authentication_method`
   (`AuthenticationContext`).
5. **Provider reference** — `IdentityRecord.provider_reference`
   (identity-verification provider, unchanged) is distinct from
   `AuthenticationContext.provider_reference` (authentication provider
   for a specific session) — same field name, different entity,
   deliberately never compared to each other.

```text
AuthenticationContext (proposed):
  authentication_context_id
  account_id
  authentication_method          — open string, extensible
  authentication_assurance_level — none | low | substantial | high
  session_authenticated_at
  provider_reference             — opaque; distinct from
                                    IdentityRecord.provider_reference
  step_up_completed_at           — nullable
```

**Step-up authentication (ADR-028 item 7, ADR-030 item 7):** sensitive
actions require authentication stronger or fresher than whatever
ambient session authentication otherwise suffices.

```text
AssuranceRequirement (proposed, reusable value shape):
  required_identity_assurance_level
  required_authentication_assurance_level
  required_attribute_freshness   — nullable AttributeFreshnessRequirement reference

StepUpAuthenticationRequirement:
  requirement_id
  requirement_version
  status                          — draft | active | superseded
  action_code                     — open string, extensible
  required_authentication_context
  assurance_requirement           — embedded AssuranceRequirement
  fresh_authentication_required   — boolean
  maximum_authentication_age      — duration | null
  reauthentication_reason         — reason code (ADR-029 scope)
  effective_from
  effective_until                 — nullable
  supersedes_requirement_id        — nullable

  # Critical-policy activation fields (fifth amendment, item 7;
  # ADR-027, ADR-028 item 12, ADR-030 item 9 — see section 6):
  signed_policy_digest_reference        — non-nullable once `active`
  transparency_log_commitment_reference — non-nullable once `active`
```

**`StepUpAuthenticationRequirement` is itself a critical policy
(section 6).** Its transition into `active` status is subject to the
same four-gate rule as `ParticipantEligibilityPolicy`,
`ProcessEligibilityPolicy`, and `PartyMembershipEligibilityPolicy` —
verified `GovernanceDecision`, `multi_person_approval_met`, signed
policy digest, and transparency-log commitment, all four independent —
and to the same policy-freeze rule once a version is in active use by
an in-progress process.

Illustrative, non-exhaustive named sensitive actions: casting a vote or
other secret-participation submission; an authorized Stage B membership
admission/rejection/suspension/termination decision; a
`ConflictAssessment` resolution decision; a policy activation; an
`AssemblyDecision` confirmation; any change to a person's own linked
identity or authentication settings.

**Evaluation mechanics, fail-closed (ADR-030 item 7):** a
`StepUpAuthenticationRequirement` is satisfied only if authentication
assurance, identity assurance, session freshness (where required), and
attribute freshness (where required) **all independently** hold — any
single failed condition fails the whole requirement, never combined
with an "or." A missing, expired, or unresolvable `AuthenticationContext`
fails closed — the action is blocked, never permitted by default. The
caller receives the requirement's own `reauthentication_reason`.
`step_up_completed_at` is set only on the specific session that
satisfied the requirement and never satisfies a different action's own
requirement without an independent, fresh evaluation. No caching of a
"step-up satisfied" result across actions.

## 14. Conflict and incompatibility

**`AffiliationDeclaration` (temporal and verification fields added,
fifth amendment item 5; ADR-028 item 11):**

```text
AffiliationDeclaration:
  affiliation_declaration_id
  subject_reference
  affiliation_type          — other_party_membership,
                              political_association_membership,
                              public_office, elected_office,
                              lobbying_or_interest_representation,
                              organizational_leadership_or_employment,
                              declared_incompatible_organization
  declared_reference         — opaque, never a free-text organization
                              name at the schema level
  declared_at
  status                     — draft | submitted | under_review |
                              acknowledged | superseded | withdrawn
  supersedes_declaration_id   — nullable

  # Temporal and verification fields (fifth amendment, item 5):
  valid_from                  — the affiliation's own effective start,
                              distinct from declared_at (when it was
                              declared)
  valid_until                 — nullable; the affiliation's own
                              effective end, where known
  verification_status          — declared | verified | disputed |
                              unverifiable
  verified_at                  — nullable
  verified_by                  — nullable, opaque `RoleAssignment`
                              reference; never the declarant
```

Declarations are purpose-scoped — feeding `ConflictAssessment` only,
never a general political-profiling system. Only the data required for
a concrete compatibility/conflict check may be read by any consuming
service.

**`ConflictAssessment` (unchanged from the original specification):**

```text
ConflictAssessment:
  conflict_assessment_id
  subject_reference
  affiliation_declaration_id      — nullable
  conflict_type                    — dual_party_membership,
                                    political_association_conflict,
                                    public_office_incompatibility,
                                    lobbying_role_incompatibility,
                                    organizational_affiliation_conflict,
                                    declared_incompatible_organization
  incompatibility_level             — none | disclosed_no_conflict |
                                    conditional_restriction | incompatible
  status                            — pending | under_review |
                                    resolved_no_conflict |
                                    resolved_conditional |
                                    resolved_incompatible | appealed |
                                    overturned | expired_reevaluation_due
  reason_codes
  evidence_references                — opaque
  reviewed_by_role_reference          — opaque `RoleAssignment` reference
  decision_authority_reference         — nullable `GovernanceDecision`
                                       reference, required for
                                       `resolved_incompatible`
  decided_at
  supersedes_conflict_assessment_id    — nullable
  re_evaluation_due_at                 — nullable
```

**Consequential human control — explicit list, restated as a hard
invariant (ADR-030 item 3, widened by the fifth amendment's item 3):**
admission (`MembershipApplication` reaching `approved`/`activated`);
rejection (`rejected`); suspension (`Membership.membership_status →
suspended`); termination/expulsion (`→ terminated`); incompatibility
finding (`ConflictAssessment.status → resolved_incompatible`);
restoration of membership rights; and, as a seventh, open-ended
category, **denial of a fundamental member right, however produced.**
No code path reaches any of these seven outcomes purely from a
policy-evaluation boolean, a timeout, or a missing reviewer defaulting
to a decision — silence is never approval. The reviewer verifying a
`ConflictAssessment`'s `decision_authority_reference` is never the same
actor who submitted the underlying `AffiliationDeclaration`.

**Hard invariant, restated without qualification (fifth amendment,
item 3):** no final membership deprivation, suspension, expulsion,
incompatibility decision, or denial of a fundamental member right may
be produced solely by automated policy evaluation. This binds by
**effect, not by label** — a new outcome type this pack has not yet
named, but which in effect deprives a member of a fundamental right, is
covered by this invariant exactly as if it appeared on the explicit
list above. A policy evaluation may only ever recommend, flag, or
compute an input; an authorized human decision, referencing a real
`GovernanceDecision`/`decision_authority_reference` where required, is
always the final and only proximate cause of any of these seven
outcomes.

## 15. Appeals and reconsideration

**Resolved, not deferred (ADR-030 item 4):** canon's existing `Appeal`
entity (14.3) is **reused** for both `ConflictAssessment` appeals and
`MembershipApplication` rejection appeals — no dedicated
`MembershipAppeal` entity is introduced. Direct inspection of canon
14.3 confirms `Appeal.decision_id` carries no `ModerationDecision`-
specific constraint; `Appeal`'s own status enum (`submitted`,
`admissibility_review`, `under_review`, `upheld`, `partially_upheld`,
`rejected`, `withdrawn`) and its existing rule ("an appeal must not be
finally decided by the author of the original decision") both transfer
without any change in meaning.

**Mechanically:** an appeal sets `Appeal.decision_id` to the
`conflict_assessment_id` or `membership_application_id` being appealed.
`ConflictAssessment`'s own reviewer-separation rule
(`CONFLICT_REVIEW_SELF_APPROVAL_PROHIBITED`) governs the original
decision; `Appeal`'s own reviewer-separation rule governs the appeal
decision — the two reviewers need not, and are structurally encouraged
not to, be the same person.

**Canon impact:** reusing `Appeal` generically requires a small,
additive canon clarification — `decision_id` may reference a
`ConflictAssessment` or `MembershipApplication` in addition to a
`ModerationDecision` — folded into the canon-impact scope below, not a
separate canon change.

**Standing default for any future appealable decision type (fifth
amendment, item 4; ADR-030 item 4).** The reuse decision above is not
scoped narrowly to `ConflictAssessment` and `MembershipApplication`
alone. Canon's polymorphic `Appeal`, with `decision_id` treated as a
polymorphic target reference, is this pack's **standing default** for
any further appealable decision type it introduces now or in a later
amendment — a dedicated appeal entity is introduced only where a
dedicated ADR proves, by the same direct-field-inspection standard used
above, that `Appeal`'s existing shape is actually insufficient for that
specific decision type. No such proof has been made for any decision
type in this pack's current scope; the presumption is reuse, not a new
entity, absent that proof.

## 16. Legal effect and formal confirmation

**No digital participation or voting process result is assumed legally
final by default (ADR-028 item 9, ADR-030 item 8).**
`ProcessEligibilityPolicy` (section 6) carries the following additional
fields, resolved by the same policy-version-resolution procedure as
every other field on that entity:

- `decision_effect` — `advisory` \| `politically_binding` \|
  `internally_binding` \| `legally_final` \| `requires_formal_confirmation`
  (at least these five; open to extension).
- `formal_confirmation_required` — boolean.
- `formal_confirmation_authority` — open string/reference, opaque.
- `secret_ballot_required` — boolean.
- `permitted_participation_mode` — open string/set (e.g. `digital_only`,
  `physical_only`, `hybrid`, `digital_with_confirmation`) — **never a
  universal physical-presence rule**; the permitted form depends on
  applicable law, party statute, process type, jurisdiction, and
  effective date, resolved the same way every other
  `ProcessEligibilityPolicy` field is resolved.
- `required_assurance_level` — nullable `AssuranceRequirement` reference
  (section 13), reused, not duplicated.
- `accessibility_profile` — open string/reference, deferred in detail to
  a future Accessibility & Assisted Participation pack (section 24).

`legal_basis` (already present on `ProcessEligibilityPolicy`, section 6)
is reused unchanged for this section's purposes.

**Where formal confirmation is required, a separate, explicit lifecycle
applies — never collapsed into the digital result itself:**

```text
DigitalDecision (proposed):
  digital_decision_id
  process_reference              — opaque
  digital_result
  decision_effect                 — copied, immutable, from the
                                    applicable ProcessEligibilityPolicy
  formal_confirmation_required     — boolean, copied likewise
  status                           — final | formal_confirmation_required
  recorded_at

AssemblyDecision (proposed; created only where
DigitalDecision.status = formal_confirmation_required):
  assembly_decision_id
  digital_decision_id
  confirming_authority              — copied from
                                     formal_confirmation_authority
  legal_basis
  confirmation_deadline
  protocol_or_evidence_reference     — opaque
  final_legal_decision
  divergence_explanation             — nullable; **mandatory** whenever
                                     final_legal_decision diverges from
                                     digital_result
  status                             — pending | confirmed | rejected |
                                     returned_for_revision
  decided_at
```

**Lifecycle, restated exactly as specified:** `DigitalDecision` (status
`formal_confirmation_required`) → `AssemblyDecision` (status `pending`)
→ `AssemblyDecision` (status `confirmed` \| `rejected` \|
`returned_for_revision`). A `DigitalDecision` whose `decision_effect`
does not require formal confirmation reaches `status = final` directly,
with no `AssemblyDecision` created.

**Mechanics (ADR-030 item 8):** a passed `confirmation_deadline` never
auto-finalizes or auto-transitions the outcome — silence is never
approval, mirroring INV-10. A divergence between `final_legal_decision`
and `digital_result` always requires an explicit
`divergence_explanation`; a transition without it, where the two
results differ, is rejected by validation. Neither `DigitalDecision` nor
`AssemblyDecision` is ever rewritten in place — a correction is always a
new, superseding pair.

**Candidate-selection support distinguishes three stages, never
collapsed into one:** a digital proposal/preselection (typically
`advisory`/`internally_binding`), a formal nomination procedure
(typically `requires_formal_confirmation`, producing its own
`DigitalDecision`/`AssemblyDecision` pair), and the legally final
candidate selection (typically `legally_final`) — evaluated and
recorded as up to three independent `DigitalDecision`/`AssemblyDecision`
chains for `epd_public_candidate_nomination`.

## 17. Security invariants

**Domain-scoped pseudonymous identifiers, not one universal hash
(ADR-031 item 1, canon-impact only):** no single, permanent, universal
identity hash is computed and reused across the platform. A new,
proposed concept, `DomainPseudonymReference`, requires separate,
domain-scoped pseudonymous identifiers for at least five domains:
participant, membership, eligibility, credential issuance, and voting.
The same person must not be linkable across domains through one
universal identifier. No derivation algorithm, key, or implementation is
selected here — deferred to the future Identity & Authentication
Security pack (section 24), subject to formal cryptographic review.

**Cross-domain correlation prohibition (ADR-031 item 2, canon-impact
only):** a new, proposed invariant, `AntiCorrelationInvariant`,
elaborates canon's existing INV-01/CT-00-08/CT-00-09 into an explicit,
itemized, fail-closed list of prohibited correlation vectors: shared
user/request/trace/analytics identifiers; exact timestamp correlation;
retained IP addresses in the ballot domain; browser fingerprinting;
shared session cookies between an identity-bearing context and the
anonymous endpoint; message-order correlation; identity-bearing
reverse-proxy logs. This is a structural, fail-closed invariant, not a
best-effort guideline.

**Anonymous endpoint isolation (ADR-031 item 3):** for anonymous voting
or other secret participation — a logically and operationally separate
deployable, network path, and administrative access boundary; no
identity JWTs or session tokens accepted, only the minimum anonymous
credential or cryptographic proof; logging excludes identity-bearing
and correlatable metadata; administrative access separately controlled;
network/key boundaries documented once a concrete deployment exists.
This governs `voting-service`'s/`credential-service`'s own future
evolution — PACK-07 introduces no anonymous endpoint itself.

**Credential Issuer boundary, preserved and strengthened (ADR-031 item
4):**

```text
Identity / Eligibility
        ↓
Credential Issuer
        ↓
Anonymous Ballot or Participation Endpoint
        ↓
Tally / Result
```

Identity and Eligibility know the person and whether the right
exists — never the ballot content. Credential Issuer knows whether the
right has been issued or consumed — never the full `IdentityRecord` and
never the ballot content once cast. The anonymous ballot/participation
domain knows the ballot and the credential's validity — never the
person behind it. Tally knows the accepted ballots — never identity.
No service, anywhere in this chain, may reconstruct the complete
identity-to-ballot link. This pack's own new entities
(`ParticipantEligibilityPolicy`, `ProcessEligibilityPolicy`,
`PartyMembershipEligibilityPolicy`, `AffiliationDeclaration`,
`ConflictAssessment`, `MembershipApplication`, `StepUpAuthenticationRequirement`,
`AuthenticationContext`, `DigitalDecision`, `AssemblyDecision`) all have
zero read or write edge toward `voting-service`/`tally-service`/
`VoteEnvelope`.

**Cryptographic protocol agility (ADR-031 item 5, canon-impact only;
gate widened from seven to nine items by the fifth amendment, item 6):**
PACK-07 does **not** fix Blind Signatures, ElGamal, homomorphic
encryption, mixnets, zero-knowledge proofs, or any other specific
scheme. A new, proposed, abstract concept, `CryptographicProtocolProfile`,
lets a future pack select, version, and eventually replace a concrete
protocol without a breaking change. Any future concrete adoption
requires, at minimum: a formal threat model; an audited protocol;
external cryptographic review; a key-management design; replay
protection; **timing unlinkability** — the protocol must structurally
resist timing-based correlation, not merely avoid naive timestamp
comparison; **transport unlinkability** — the network transport must
not allow linking via connection reuse, TLS session resumption, or IP
correlation; **privacy-preserving revocation** — a revocation event
must not itself leak which credential or person was revoked (sharpened
from a plain "revocation/invalidation semantics" requirement); a
documented verification procedure.

**No custom cryptography (ADR-031 item 6):** no proprietary or
homemade voting cryptography; no unaudited blind-signature
implementation; no custom zero-knowledge construction. Only
established, formally reviewed, and appropriately audited protocols and
libraries may ever be proposed — applying equally to the domain-
pseudonym derivation function.

**Immutable audit without mandatory blockchain (ADR-031 item 7):** no
blockchain, Hyperledger, AWS QLDB, or other specific vendor/product is
required. Required properties, technology-agnostically: append-only
records; tamper evidence; hash chaining or Merkle commitments where
appropriate; signed checkpoints; independent backup; WORM retention
where legally appropriate; reproducible, independent audit verification;
separation of administrative duties. Technology selection is deferred
to a future infrastructure/security ADR.

**Queue and CQRS safety (ADR-031 item 8):** no assumption anywhere in
this pack's design, or any future pack's design building on it, treats
Kafka, RabbitMQ, or any other message queue as the authoritative store
for an accepted ballot. Required, technology-agnostically: durable
acceptance semantics; idempotency; replay handling; duplicate
prevention; acknowledgement only after durable fixation; an audit
receipt; recovery after partial failure; documented source-of-truth
ownership. Redis or any other cache system must never be the source of
truth for eligibility, accepted ballots, final tally, membership
status, or audit history.

## 18. Events

Canon already defines `membership.applied` / `membership.activated` /
`membership.suspended` (20.5) for the generic `Membership` entity — this
pack's implementation would be the first to actually emit them.
Proposed additions:

- `membership.terminated`, `membership.rejected`, `membership.expired`
  (completing `Membership`'s own status-transition coverage).
- `membership_application.created`, `.eligibility_reviewed`,
  `.human_decision_recorded`, `.approved`, `.rejected`, `.activated`.
- `participant_eligibility_policy.activated`, `.superseded`.
- `process_eligibility_policy.activated`, `.superseded`.
- `party_membership_eligibility_policy.activated`, `.superseded`.
- `affiliation_declaration.submitted`, `.updated`, `.withdrawn`.
- `conflict_assessment.opened`, `.decided`, `.appealed`, `.overturned`,
  `.reevaluation_due`.
- `step_up_authentication_requirement.activated`, `.superseded`.
- `authentication_context.step_up_completed`.
- `digital_decision.recorded`, `.finalized`.
- `assembly_decision.opened`, `.confirmed`, `.rejected`,
  `.returned_for_revision`.

`ParticipationRightsProfile` is derived and never stored — it emits no
events of its own.

## 19. Reason codes

**Final, approved list (ADR-029), the generic electoral code removed
and replaced everywhere by one of the four specific codes:**

Carried forward from the original specification:
`PARTICIPANT_AGE_REQUIREMENT_NOT_MET`,
`PARTY_MEMBERSHIP_AGE_REQUIREMENT_NOT_MET`,
`CITIZENSHIP_REQUIREMENT_NOT_MET`, `RESIDENCE_REQUIREMENT_NOT_MET`,
`EID_ASSURANCE_LEVEL_INSUFFICIENT`,
`MEMBERSHIP_DURATION_REQUIREMENT_NOT_MET`,
`DUAL_PARTY_MEMBERSHIP_CONFLICT`, `POLITICAL_ASSOCIATION_CONFLICT`,
`PUBLIC_OFFICE_INCOMPATIBILITY`, `LOBBYING_ROLE_INCOMPATIBILITY`,
`ORGANIZATIONAL_AFFILIATION_CONFLICT`,
`DECLARED_INCOMPATIBLE_ORGANIZATION`, `CONFLICT_ASSESSMENT_PENDING`,
`CONFLICT_ASSESSMENT_REQUIRES_HUMAN_REVIEW`,
`PARTY_MEMBERSHIP_APPLICATION_REJECTED`, `PARTY_MEMBERSHIP_SUSPENDED`,
`PARTY_MEMBERSHIP_TERMINATED`, `PARTICIPATION_RIGHTS_RESTRICTED`,
`POLICY_EXCEPTION_NOT_AUTHORIZED`, `POLICY_VERSION_SUPERSEDED`,
`AFFILIATION_DECLARATION_INCOMPLETE`,
`AFFILIATION_DECLARATION_REQUIRES_UPDATE`,
`CONFLICT_REVIEW_SELF_APPROVAL_PROHIBITED`.

**Removed, per the project owner's explicit instruction:**
`ELECTORAL_ELIGIBILITY_NOT_MET` — no code path in this pack's design may
raise this generic name; whichever of the four specific questions
actually failed determines which specific code is raised.

**Added by ADR-029:**

| Code                                         | Raised when                                                                                          |
| -------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| `ACTIVE_ELECTORAL_ELIGIBILITY_NOT_MET`       | `active_electoral_eligibility_met` evaluates false.                                                  |
| `PASSIVE_ELECTORAL_ELIGIBILITY_NOT_MET`      | `passive_electoral_eligibility_met` evaluates false.                                                 |
| `PARTY_INTERNAL_VOTING_ELIGIBILITY_NOT_MET`  | `party_internal_voting_eligibility_met` evaluates false.                                             |
| `PARTY_OFFICE_CANDIDACY_ELIGIBILITY_NOT_MET` | `party_office_candidacy_eligibility_met` evaluates false.                                            |
| `MEMBERSHIP_HUMAN_APPROVAL_REQUIRED`         | A membership action is attempted while Stage B's decision has not yet been recorded.                 |
| `MEMBERSHIP_DECISION_AUTHORITY_INVALID`      | A membership decision's decision-maker/competent-body reference cannot be verified as authorized.    |
| `MEMBERSHIP_STATUS_DISCLOSURE_PROHIBITED`    | A caller attempts to expose restricted membership data outside the four permitted publication bases. |
| `MEMBERSHIP_PUBLICATION_CONSENT_MISSING`     | Publication on the consent basis is attempted without a recorded consent reference.                  |

**Not yet formally registered by any ADR, needed at implementation time
for step-up authentication and formal confirmation (identified here as
an implementation-time gap, resolved by whichever code the requirement's
own `reauthentication_reason` and confirmation-lifecycle validation
name — no new canon-fixed code list is proposed by this document; exact
wording remains an implementation-time registry addition, mirroring
every prior pack's own registry-file precedent).**

**Reused generic codes, unchanged:** `PERMISSION_DENIED`,
`VALIDATION_UNKNOWN_STATUS`, `VALIDATION_FORBIDDEN_TRANSITION`,
`VALIDATION_RECORD_NOT_FOUND`. Reused canon-fixed codes:
`EVENT_VERSION_UNSUPPORTED`, `INTEGRITY_CHECK_FAILED`.

## 20. OpenAPI scope

Not created by this document, but scoped for a future implementation
pass, per ADR-026's ownership split: `contracts/openapi/pack-07.yaml`
would need two service tags, not one — `eligibility-service`
(`ParticipantEligibilityPolicy`/`ProcessEligibilityPolicy` reads,
process-eligibility evaluation, `StepUpAuthenticationRequirement`
reads, `DigitalDecision`/`AssemblyDecision` reads) and
`membership-service` (`MembershipApplication` submission/decision,
`AffiliationDeclaration` submission, `ConflictAssessment` read/appeal,
`Membership` read). A `ParticipationRightsProfile` read endpoint is
documented once, composing both tags' outputs. Every narrow
cross-service function in section 5 is documented as having no
HTTP-shaped path of its own, mirroring `verify_role_assignment_for_action`'s
own precedent.

## 21. Schema scope

Not created by this document, but scoped: one entity JSON Schema per
new/extended entity — `Membership` (never had one), `MembershipApplication`,
`ParticipantEligibilityPolicy`, `ProcessEligibilityPolicy`,
`PartyMembershipEligibilityPolicy`, `AffiliationDeclaration`,
`ConflictAssessment`, `StepUpAuthenticationRequirement`,
`AuthenticationContext`, `DigitalDecision`, `AssemblyDecision` — eleven
schemas total, plus two reusable value-shape schemas
(`AssuranceRequirement`, `AttributeFreshnessRequirement`) and one
event-payload schema per new event family (section 18).

## 22. CT-00 mapping

| Check                              | Applicability for PACK-07                                                                                                                                                                                                                                  |
| ---------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CT-00-01 Schema Validation         | Applicable, standard.                                                                                                                                                                                                                                      |
| CT-00-02 Unknown Status            | Applicable, standard — every new status enum rejects unrecognized values.                                                                                                                                                                                  |
| CT-00-03 Forbidden Transition      | Applicable, standard — `Membership`/`MembershipApplication`/`ConflictAssessment`/`DigitalDecision`/`AssemblyDecision`/policy status transition tables.                                                                                                     |
| CT-00-04 Event Idempotency         | Applicable, standard.                                                                                                                                                                                                                                      |
| CT-00-05 Unsupported Event Version | Applicable, standard.                                                                                                                                                                                                                                      |
| CT-00-06 Missing Permission        | Applicable, standard.                                                                                                                                                                                                                                      |
| CT-00-07 Audit Creation            | Applicable, standard.                                                                                                                                                                                                                                      |
| **CT-00-08 Identity Leakage**      | **Central** — no raw identity/assurance/freshness field ever reaches a public payload, event, schema, or audit-visible field outside `identity-service` itself.                                                                                            |
| CT-00-09 Vote Linkability          | Applicable — a structural proof that no entity this pack introduces can reconstruct a link to `VoteEnvelope` (section 17's Credential Issuer boundary confirmation).                                                                                       |
| **CT-00-10 Rule Freeze**           | **Central** — once a policy version is `active`, its evaluated rule content is frozen for any decision already made under it; extended to `ProcessEligibilityPolicy`'s own reproducibility guarantee (section 9).                                          |
| CT-00-11 AI Human Control          | Not applicable to PACK-07's own implementation — no `AIProcessingRecord` content anywhere in this pack's design. A related future architectural requirement for consequential AI-generated summaries is preserved, implementation deferred, in section 24. |
| CT-00-12 Emergency Stop            | Not applicable — no `EmergencyAction` dependency.                                                                                                                                                                                                          |

## 23. Canon impact

**What already exists in `CANON_VERSION 0.5.0`, unchanged:** `Account`
(7.2); `IdentityRecord`'s existing nine fields (7.3); `EligibilityRule`/
`EligibilityDecision`/`EligibilitySnapshot` (9.1–9.3); `ParticipationCredential`
(10.1); `RoleAssignment` (8.4); `GovernancePolicy`/`GovernanceDecision`
(19b.2–19b.3); `Appeal` (14.3); `Organization`/`CivicSpace`/`Membership`
(8.1–8.3, all three fully fielded but `Membership` never before
implemented); INV-01, CT-00-08, CT-00-09 (existing invariants, canon
7.4's "Actor ID need not be the same across contours" principle).

**Proposed for `CANON_VERSION 0.6.0` (minor bump — every change additive,
nothing existing altered, removed, or redefined; not performed by this
document):**

- Eight new `IdentityRecord` fields: `date_of_birth`, `citizenship_status`,
  `residence_status`, `identity_assurance_level` (renamed from
  `eid_assurance_level`), `identity_scheme` (renamed from
  `identity_verification_method`), `attribute_verification_level`,
  `attribute_verified_at`, `attribute_valid_until`.
- Implementation authorization for `Membership` (already fielded), plus
  new canon events completing its status coverage.
- Ten new canonical entities: `ParticipantEligibilityPolicy`,
  `ProcessEligibilityPolicy`, `StepUpAuthenticationRequirement`,
  `DigitalDecision`, `AssemblyDecision` (owner: "Eligibility Engine" /
  `eligibility-service`); `PartyMembershipEligibilityPolicy`,
  `AffiliationDeclaration`, `ConflictAssessment`, `MembershipApplication`
  (owner: "Membership Service" / `membership-service`); `AuthenticationContext`
  (owner: `identity-service`).
  `ProcessEligibilityPolicy` additionally carries the seven legal-effect
  fields (section 16).
- The four separated electoral-eligibility claims — new derived-claim
  definitions, not stored fields.
- The nine-concept identity-verification/citizenship separation
  (section 7) as a new structural invariant and forbidden-link entry.
- The two-stage admission rule (section 8) as a new structural
  invariant.
- The membership-privacy default (section 12) as a new forbidden-link/
  default-visibility rule in section 23.
- A small, additive documentation clarification on `Appeal.decision_id`
  (section 15) — may also reference a `ConflictAssessment` or
  `MembershipApplication` — and, per the fifth amendment's item 4, a
  standing default treating `decision_id` as a polymorphic target
  reference for any further appealable decision type this pack
  introduces.
- New section 22 ownership-matrix rows for all ten new entities, plus
  new section 23 forbidden-link entries (vote-linkability exclusion for
  every new entity; the membership-privacy default; the identity-
  verification/citizenship non-substitution rule).

**Additional proposed `CANON_VERSION 0.6.0` content from the fifth
amendment round (additive only; ADR-026 through ADR-031 as amended;
`PACK-07-OWNER-DECISIONS.md`):**

- A new, seventh, open-ended category on the consequential-human-control
  hard invariant (section 14): "denial of a fundamental member right,
  however produced" — binding by effect, not by label; restated as a
  structural, fail-closed hard invariant alongside the existing six
  named categories.
- Five new `AffiliationDeclaration` fields (section 14): `valid_from`,
  `valid_until`, `verification_status` (`declared | verified | disputed
| unverifiable`), `verified_at`, `verified_by`.
- A new "critical policy" classification (sections 6, 13) covering
  `ParticipantEligibilityPolicy`, `ProcessEligibilityPolicy`,
  `PartyMembershipEligibilityPolicy`, and
  `StepUpAuthenticationRequirement` — each gaining two new fields,
  `signed_policy_digest_reference` and
  `transparency_log_commitment_reference`, both non-nullable once
  `active`.
- A new four-gate critical-policy activation rule (verified
  `GovernanceDecision`; `multi_person_approval_met`, an extension to
  `verify_decision_authorizes_policy_activation`'s existing return
  shape; `signed_policy_digest_reference`; `transparency_log_commitment_reference`)
  as a new structural invariant, all four independently required.
- A new policy-freeze invariant (sections 6, 13), extending existing
  CT-00-10: an active critical policy version in use by an in-progress
  process cannot be superseded until that process reaches a terminal
  state — derived from existing facts, no new persisted field.
- `ParticipationRightsProfile`'s own characterization as internal and
  non-authoritative (section 10) — a documentation/usage-constraint
  clarification, not a new stored field, since the profile was already
  specified as derived and non-stored.
- Sharpened cryptographic-protocol-agility gate wording (section 17):
  "timing unlinkability" and "transport unlinkability" as two new named
  gate items, and "revocation/invalidation semantics" sharpened to
  "privacy-preserving revocation" — all still abstract, non-implementing
  documentation clarifications on the already-proposed
  `CryptographicProtocolProfile` concept, selecting no algorithm.

```text
CANON_VERSION: 0.5.0 → 0.6.0 (proposed, not performed by this document)
```

**Identified only, deferred to a future pack's own implementing ADR —
not authorized by this document, by ADR-031, or by any ADR-026 through
ADR-030 content:** `DomainPseudonymReference`, `AntiCorrelationInvariant`
(elaborating existing INV-01/CT-00-08/CT-00-09, not replacing them),
`CryptographicProtocolProfile` — abstract shapes only, no derivation
algorithm, protocol, or vendor selected by anything in this document.

**Not proposed or performed anywhere in this document:** any change to
`EligibilityRule`, `EligibilityDecision`, `EligibilitySnapshot`,
`RoleAssignment`, `GovernancePolicy`, `GovernanceDecision`,
`TechnicalChallenge`, `AIProcessingRecord`, `PublicLedgerEntry`, or any
other existing entity's own field shape, beyond `Appeal`'s documentation
clarification above.

## 24. Exclusions

- The full `Organization`/`CivicSpace` implementation and any Bund/
  Land/Kreis/Bezirk/Ort regional hierarchy — deferred to PACK-08.
- Any final age, citizenship, residence, incompatibility, membership-
  duration, assurance-level minimum, or legal-effect value — every one
  is a policy decision, not fixed anywhere in this document.
- Real eIDAS integration or any live external eID provider connection.
- eID provider adapter implementation; step-up authentication
  implementation; domain-pseudonym derivation implementation; a secure
  session model implementation — deferred to a future **Identity &
  Authentication Security pack**.
- The formal threat model; anonymous credentials or blind signatures;
  encrypted ballots; homomorphic tally or mixnet evaluation; zero-
  knowledge proofs; a receipt/verification model; coercion-resistance
  analysis; a key ceremony; external audit — deferred to a future
  **Verifiable Voting Cryptography pack**.
- API gateway; rate limiting; DDoS protection; WORM audit
  implementation; SIEM; secrets management; HSM/KMS; queues; CQRS;
  backups; disaster recovery; operational monitoring — deferred to a
  future **Production Security & Resilience pack**.
- The actual legal-effect determination logic; jurisdiction-specific
  confirmation-authority integration; enforcement of `decision_effect`/
  confirmation outcomes — deferred to a future **Legal Decision
  Validity pack**.
- Data-protection impact assessment obligations the `DigitalDecision`/
  `AssemblyDecision` pair may trigger — deferred to a future **Privacy
  Governance & DSFA pack**.
- Any public, verifiable-evidence presentation of
  `protocol_or_evidence_reference` content — deferred to a future
  **Public Verifiability pack**.
- The `accessibility_profile` field's own concrete implementation —
  deferred to a future **Accessibility & Assisted Participation pack**.
- Any change to `EligibilityRule`, `EligibilityDecision`,
  `EligibilitySnapshot`, `RoleAssignment`, `GovernancePolicy`,
  `GovernanceDecision`, `TechnicalChallenge`, `AIProcessingRecord`, or
  `PublicLedgerEntry`'s own field shape.
- Any new `AIProcessingRecord`-assisted decision-making anywhere in
  eligibility, membership, conflict, or confirmation evaluation.
- **Approved future architectural requirement — consequential
  AI-generated summaries (sixth-round correction of the fifth
  amendment's item 8; owner-architecturally-approved, implementation
  deferred).** PACK-07 itself does **not** implement AI processing, and
  CT-00-11 remains **not applicable** to PACK-07's own implementation —
  no `AIProcessingRecord` content exists anywhere in this pack's design
  (section 1, section 22). This document nonetheless **preserves**, as
  an approved future architectural requirement rather than an
  unresolved question, the owner's direction that any consequential
  AI-generated summary — wherever in the platform it is eventually
  introduced — must support:
  - deterministic source-reference mapping from each material summary
    segment to its source `Contribution` references;
  - coverage metadata (what proportion/which parts of the source
    material the summary actually covers);
  - explicit human-review status (never silently implied, never
    defaulted to reviewed);
  - immutable `AIProcessingRecord` linkage (canon 17.1), so the summary
    is always traceable back to the record of the AI processing that
    produced it.

  **This requirement's implementation is deferred to a future AI
  Processing amendment pack and is not authorized, drafted, or
  performed by this document, by any of ADR-026 through ADR-031, or by
  PACK-07 in this drafting round.** It does not modify PACK-06's
  already-`accepted`, already-implemented `AIProcessingRecord`/
  disclosure machinery (ADR-021 through ADR-025, canon 19c) — a
  dedicated PACK-06 addendum ADR remains the correct vehicle for that
  future amendment pack to actually wire this requirement into
  `AIProcessingRecord`'s own field shape, exactly as recorded in
  `PACK-07-OWNER-DECISIONS.md` section 8.

- Assembly workflow tooling, DSFA tooling, public-verifiability
  infrastructure, or accessibility infrastructure.
- Any service directory, schema, OpenAPI file, ADR status change, or
  canon edit — this document is a specification only.

## 25. Definition of Done (for a future implementation pass)

1. All six ADRs (026–031) reviewed and **formally accepted** (with or
   without further amendment) before any code is written — drafting and
   the owner's direction to proceed with drafting (this document's own
   trigger) are not themselves acceptance.
2. Canon `0.5.0 → 0.6.0` implemented as its own dedicated task, strictly
   after ADR acceptance.
3. `services/membership-service/` implemented: domain models, status
   transition tables, application commands, storage Protocols with
   in-memory adapters, `Membership`/`MembershipApplication`/
   `PartyMembershipEligibilityPolicy`/`AffiliationDeclaration`/
   `ConflictAssessment`, and every narrow cross-pack read this document
   assigns to it.
4. `services/eligibility-service/` extended: `ParticipantEligibilityPolicy`,
   `ProcessEligibilityPolicy`, `StepUpAuthenticationRequirement`,
   `DigitalDecision`, `AssemblyDecision`, and every narrow cross-pack
   read this document assigns to it (its first content addition since
   PACK-02).
5. `services/identity-service/` extended: `AuthenticationContext` and
   the eight new `IdentityRecord` fields.
6. `contracts/openapi/pack-07.yaml`, `contracts/reason-codes/pack-07.yml`
   (including the step-up/confirmation codes flagged in section 19 as
   still needing exact registration), and every new entity/event JSON
   Schema, all validated against real constructed objects.
7. `tests/contract/test_ct00_01` through `test_ct00_10` extended with
   real PACK-07 cases (section 22); CT-00-11/12 remain documented
   not-applicable.
8. `scripts/check_repository.py`'s `REQUIRED_PATHS` extended; `scripts/
verify_versions.py` passing; canon checksum changed and re-confirmed
   exactly once, matching the accepted ADRs.
9. Full local verification suite green (Ruff, mypy, pytest, Prettier),
   followed by the established external-GitHub-Actions revision cycle
   through to a genuine, externally-confirmed PASS.
10. Root `README.md` and `CHANGELOG.md` updated only once that PASS is
    real.

## 26. Implementation plan (sequencing, non-binding on timing)

1. **Owner acceptance pass** on ADR-026 through ADR-031 (with or without
   further amendment), using `docs/review/PACK-07-OWNER-DECISIONS.md`'s
   own checklists — a separate governance action from this document.
2. **Canon `0.5.0 → 0.6.0` edit**, as its own dedicated task, once
   acceptance is recorded — the ten new entities, eight `IdentityRecord`
   field additions, and the `Appeal.decision_id` documentation
   clarification (section 23).
3. **`identity-service` extension** — `AuthenticationContext` and the
   `IdentityRecord` field additions, since both `eligibility-service`
   and `membership-service` depend on the identity-layer narrow reads
   from day one of their own implementation.
4. **`eligibility-service` extension** — `ParticipantEligibilityPolicy`,
   `ProcessEligibilityPolicy`, `StepUpAuthenticationRequirement`,
   `DigitalDecision`, `AssemblyDecision`, and the new narrow read into
   `identity-service`.
5. **`membership-service` implementation** — `Membership`,
   `MembershipApplication`, `PartyMembershipEligibilityPolicy`,
   `AffiliationDeclaration`, `ConflictAssessment`, and the narrow reads
   into `identity-service`/`eligibility-service`/`governance-service`.
6. **Cross-service boundary tests** (`test_service_boundaries.py`
   allow-list entries per section 5) and **CT-00 contract-test
   extensions** (section 22), in parallel with steps 4–5.
7. **Reason-code registry** (`contracts/reason-codes/pack-07.yml`),
   finalizing the exact wording for the step-up/confirmation codes
   section 19 flags as not yet formally registered.
8. **OpenAPI and schema authoring** (sections 20–21), validated against
   real constructed objects.
9. **Full local verification suite**, then the established external-
   GitHub-Actions PASS cycle.

Future packs referenced throughout this document — **Identity &
Authentication Security**, **Verifiable Voting Cryptography**,
**Production Security & Resilience**, **Legal Decision Validity**,
**Privacy Governance & DSFA**, **Public Verifiability**, and
**Accessibility & Assisted Participation** — are none of them scheduled,
numbered, or sequenced by this plan; each remains a separate, later
specification of its own, gated on its own future owner decision to
proceed.
