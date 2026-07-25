# CLAUDE-PACK-07 — Participation & Membership Policy: Technical Specification

> **SUPERSEDED — historical draft only.** This document is the
> **original** PACK-07 working draft, authored before ADR-026 through
> ADR-031 were drafted and before the project owner's four rounds of
> binding amendments were incorporated. It is retained here **only** as
> a historical record of PACK-07's starting point. **It no longer
> reflects the approved PACK-07 design** and must not be used as an
> implementation reference. The single, current, internally consistent
> specification is
> **[`docs/handover/PACK-07-SPEC-FINAL.md`](./PACK-07-SPEC-FINAL.md)**,
> which supersedes this document in full — in particular, this
> document's single `electoral_eligibility_met` claim, its
> single-service (`membership-service`-owns-everything) decomposition,
> and its unresolved `ConflictAssessment` appeal-path question are all
> since resolved differently by the approved ADRs; see
> `PACK-07-SPEC-FINAL.md` for the resolved design. Everything below this
> notice is preserved unedited from the original draft.

**Status: proposed.** This document specifies the next candidate
implementation package. It is not itself an ADR and authorizes no code.
Per canon section 26, every design decision below marked "requires ADR"
must reach `accepted` status before any corresponding working code is
written. **No PACK-07 service directory, schema, contract, ADR, or
implementation code exists yet, and canon is not edited by this
document** — this specification is the entire PACK-07 deliverable at
this stage. No final political, legal, or numeric value (an age, a
citizenship rule, an incompatibility list) is selected here — every such
value is identified as a policy decision and left to a future,
Governance-approved policy activation, per this task's own explicit
instruction (item 17).

This pack is a different shape again from every prior one. PACK-04 and
PACK-05 each proposed entirely new entities for a context canon only
sketched in a one-line responsibility list. PACK-06 started from a
fully fielded, already-owned entity (`AIProcessingRecord`). PACK-07's
subject — who may participate, and on what terms may someone additionally
become and remain a party member — sits **between** those two shapes:
canon already names two responsibility areas that between them cover it
(5.2 Eligibility Context, 5.4 Organization Context) and already defines
three real, fielded entities in this space (`EligibilityRule`/
`EligibilityDecision`/`EligibilitySnapshot`, section 9; `Organization`/
`CivicSpace`/`Membership`, section 8.1–8.3) — but **all three of
`Organization`, `CivicSpace`, and `Membership` remain fully
unimplemented** (no service directory exists for any of them), and
**age, citizenship, residence, multiple citizenship, habitual residence,
electoral eligibility, eID assurance level, party affiliation, and
conflict-of-interest/incompatibility are entirely absent from canon and
code alike** — confirmed by exhaustive repository search (section 2).
This is, in that specific sense, the most canon-silent pack since
PACK-04/05 for its _newest_ content, while simultaneously being the
first pack required to finally implement three long-dormant canonical
entities (`Organization`, `CivicSpace`, `Membership`) that have sat
unimplemented since the original canon text was written — though, per
this task's explicit instruction (item 16), only `Membership` is in this
pack's own scope; `Organization`/`CivicSpace` and the full Bund/Land/
Kreis/Bezirk/Ort regional hierarchy are deliberately deferred to a future
PACK-08.

## 0. Canon dependency

This specification was authored against the current, unchanged canon
state:

```text
sha256(docs/canonical/TZ-00-domain-event-canon.md) =
  374b25fddfab88846622bf078b35c4246d8ad8c5d65bf43e6ac4e82653f74f74
CANON_VERSION = 0.5.0
REPOSITORY_VERSION = 0.6.0 (CLAUDE-PACK-06, externally PASSed)
```

Canon was not opened for editing to produce this specification and
remains byte-identical to the PACK-06 PASS state. Section 24 identifies
that canon would need to move `0.5.0 → 0.6.0` (a **minor** bump per
canon section 25 — additive fields, additive statuses, additive events,
and new entities in a previously one-line-sketched area, none of it
altering or removing existing field semantics) if the design decisions
below are accepted — this is analysis, not an edit; no canon text has
been touched. `REPOSITORY_VERSION` would separately move `0.6.0 → 0.7.0`
at implementation time (a future, later task), coincidentally landing on
the same numeric value canon would reach — the same harmless
coincidence this project has already seen twice before (PACK-04,
PACK-05), the two versions remaining tracked and bumped independently.

## 1. Scope — context separation

The user's request for this pack is explicit that participant policy and
party-member policy must remain conceptually distinct, that no final
political value may be hard-coded, and that the full regional
organizational model (Bund/Land/Kreis/Bezirk/Ort) is out of scope,
deferred to PACK-08. Checked directly against canon and the current
repository:

| Context / concern                                                                   | Canon section           | In PACK-07 scope                                                                                     | Why                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| ----------------------------------------------------------------------------------- | ----------------------- | ---------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Eligibility Context (`EligibilityRule`/`EligibilityDecision`/`EligibilitySnapshot`) | 5.2, 9                  | **Yes — reused, extended in effect, not replaced**                                                   | The existing generic eligibility-evaluation machinery (`eligibility-service`) remains the canonical mechanism that produces an `EligibilityDecision` for a concrete process; this pack proposes two new, richer policy _sources_ (section 3) that a decision's `rule_version` can point to, without duplicating or bypassing the existing entities.                                                                                                     |
| Organization Context — `Membership` only                                            | 5.4, 8.3                | **Yes**                                                                                              | Canon already names both the entity and its owner ("Membership Service") but nothing implements it; PACK-07 is the first pack to do so, scoped specifically to party membership as one `membership_type` value on the existing canonical `Membership` entity.                                                                                                                                                                                           |
| Organization Context — `Organization`, `CivicSpace`, full regional hierarchy        | 5.4, 8.1, 8.2           | **No, explicitly deferred to PACK-08 per this task's instruction**                                   | `Membership.organization_id` is treated as an opaque, caller-supplied reference (section 17, Design decision D4) rather than requiring a live `Organization` entity to exist first. No Bund/Land/Kreis/Bezirk/Ort hierarchy, no `CivicSpace` lifecycle, no organizational role structure beyond the already-existing `RoleAssignment` is proposed here.                                                                                                 |
| Identity Context (`IdentityRecord`)                                                 | 5.1, 7.3                | **Yes — extended, not replaced**                                                                     | Age, citizenship, residence, and eID assurance level are all, by their nature, verified _identity_ attributes; this pack proposes additive fields on the existing `IdentityRecord` (section 9, Design decision D2) rather than a parallel identity-shaped entity.                                                                                                                                                                                       |
| Credential Context (`ParticipationCredential`)                                      | 10                      | **No new fields, referenced only**                                                                   | Existing `ParticipationCredential` machinery is reused unchanged as the mechanism that already carries an `eligibility_snapshot_digest` (a PACK-02 repository-level addition, section 3f of the PACK-06 research — see this pack's own section 2) into downstream services; no new credential type or field is proposed.                                                                                                                                |
| Governance Context (`GovernancePolicy`/`GovernanceDecision`/`RoleAssignment`)       | 5.12, 19b               | **Yes — as policy-activation authority only, no new fields on canon's existing Governance entities** | Per this task's explicit instruction (item 10), `governance-service` remains sole authority for adopting and activating the two new policy entities this pack proposes (section 3); PACK-07 proposes zero new fields on `GovernancePolicy`, `GovernanceDecision`, `TechnicalChallenge`, or `RoleAssignment` themselves.                                                                                                                                 |
| AI Processing Context (`AIProcessingRecord`)                                        | 19c                     | **No**                                                                                               | PACK-06, already implemented and PASSed. Nothing in this pack reads, writes, or references `AIProcessingRecord`; no AI-assisted decision-making is proposed anywhere in eligibility, membership, or conflict evaluation.                                                                                                                                                                                                                                |
| Transparency Context (`PublicLedgerEntry` etc.)                                     | 19a                     | **No new fields; disclosure pattern reused if adopted later**                                        | Not exercised in this specification; a future implementation pass may choose to publish redacted membership-policy summaries via `transparency-service`'s existing `publish_ledger_entry` path, exactly as PACK-06 reused it — this specification takes no position on whether that is required, since the user's item 7 rule ("public disclosure, where required, must use redacted summaries") does not itself mandate that disclosure exists at all. |
| Emergency / Crisis Override (`EmergencyAction`)                                     | 19, 19.1                | **No**                                                                                               | No dependency in either direction, same reasoning PACK-05/06 already gave for the same exclusion.                                                                                                                                                                                                                                                                                                                                                       |
| Regional/territorial hierarchy (Bund/Land/Kreis/Bezirk/Ort)                         | _(none — canon-silent)_ | **No, explicitly deferred to PACK-08**                                                               | Section 22 (this pack) proposes only generic, open `scope_type`/`scope_id`/`jurisdiction_code` fields sufficient for a future PACK-08 to slot a real hierarchy into, per this task's item 16 instruction.                                                                                                                                                                                                                                               |

## 2. Canon-textual basis and canon-silence findings

Unlike PACK-06, which started from a fully fielded, already-owned entity,
PACK-07's subject is split across two responsibility areas that canon
sketches only in one line each, plus three fully fielded but wholly
unimplemented entities, plus a subject area (age/citizenship/residence/
party/conflict) that is **completely and confirmedly absent** from both
canon and code. Quoted in full, because each is short:

> **5.2. Eligibility Context** — членство; регион; возрастные и временные
> условия; статус права участия; eligibility snapshot; reason codes
> допуска и недопуска. Отвечает на вопрос: имеет ли подтверждённый
> участник право участвовать в конкретном процессе?

> **5.4. Organization Context** — организация; подразделения; Civic
> Spaces; рабочие группы; роли; членство; организационная структура.

> **9.1. EligibilityRule** — Поля: `eligibility_rule_id`, `rule_version`,
> `scope_type`, `scope_id`, `required_membership_status`,
> `required_verification_level`, `region_constraint`,
> `minimum_membership_age`, `exclusion_conditions`, `valid_from`,
> `valid_until`. После открытия голосования используемая версия правила
> замораживается.

> **9.2. EligibilityDecision** — Поля: `eligibility_decision_id`,
> `subject_reference`, `process_id`, `rule_version`, `decision`,
> `reason_codes`, `evaluated_at`, `expires_at`. Значения `decision`:
> `eligible`, `not_eligible`, `pending`, `expired`,
> `manual_review_required`.

> **8.3. Membership** — Поля: `membership_id`, `account_reference`,
> `organization_id`, `membership_type`, `membership_status`,
> `effective_from`, `effective_until`, `region_code`. Статусы:
> `application_pending`, `verification_pending`, `active`, `suspended`,
> `terminated`, `rejected`, `expired`.

> **7.3. IdentityRecord** — Поля: `identity_record_id`, `account_id`,
> `verification_provider`, `verification_level`, `verification_status`,
> `verified_at`, `expires_at`, `country`, `duplicate_check_status`,
> `provider_reference`. Запрет: IdentityRecord не содержит список
> голосований, выбранные варианты, список инициатив, политические
> предпочтения, делегирования.

Checked systematically for what is genuinely silent, missing, or only
loosely sketched:

- **No age field exists anywhere.** `EligibilityRule.minimum_membership_age`
  is a _rule_ input (a threshold), but no field anywhere holds a
  subject's actual, verifiable age or date of birth — not on
  `IdentityRecord`, not on `Account`, not anywhere. Confirmed by
  exhaustive grep: `date_of_birth` appears in the repository **only** as
  a name inside `credential-service`'s own `FORBIDDEN_FIELD_NAMES`
  frozenset (`services/credential-service/src/epd2_credential_service/domain.py:85`)
  and in three docs — always as something a credential must _never_
  carry, never as a real field anywhere else.
- **No citizenship or residence field exists anywhere.** Grep for
  `citizenship`, `residence`, `Staatsangehörigkeit`, `Wohnsitz` across
  the entire repository (code, canon, docs, contracts) returns **zero
  genuine hits**. `IdentityRecord.country` exists but canon never states
  whether it means nationality, residence, or the verification
  provider's own jurisdiction — it is a single open string with no
  documented semantics at all, and cannot safely be repurposed to mean
  citizenship without an explicit ADR decision (section 9 below).
- **No eID assurance level exists anywhere.** Grep for `assurance_level`
  returns **zero hits** in the entire repository. `IdentityRecord.
verification_level` exists as an open string (no eIDAS-style
  low/substantial/high enum defined anywhere in canon or code) —
  canon-silent on whether "eID-verified participant" (item 1) is even a
  distinguishable state from ordinary identity verification today.
- **No party, affiliation, or conflict-of-interest concept exists
  anywhere.** Grep for `party`, `Partei`, `affiliation`,
  `conflict_of_interest`, `incompatib` across the whole repository
  returns no genuine hits beyond unrelated English usages (third-party
  integrations, mypy's "incompatible type" messages, a version-policy
  phrase in `contracts/README.md`). The only textual acknowledgment
  anywhere in canon that EPD² is a _party_-political platform at all is
  section 2's target-function line, "EPD² — цифровая гражданская и
  партийная платформа" (a civic **and party** platform) — never
  operationalized as an entity, field, status, or event.
- **`Organization`, `CivicSpace`, and `Membership` are fully defined but
  100% unimplemented.** No `services/organization-service` or
  `services/membership-service` directory exists anywhere in this
  repository (confirmed directly against the `services/` listing, not
  merely against the stale `docs/architecture/data-ownership.md`, which
  is frozen at PACK-02 state and incorrectly still shows `RoleAssignment`
  as "not implemented" even though PACK-05 implemented it — that
  document cannot be trusted as a current-state source past PACK-02).
  Canon's section 22 ownership matrix already names "Membership
  Service" as `Membership`'s owner — this pack reuses that exact,
  already-canonical name rather than inventing a new one (section 18).
- **`EligibilitySnapshot` (9.3) is conspicuously absent from the section
  22 ownership matrix** despite being fully defined and already
  physically implemented in `eligibility-service` — a pre-existing canon
  gap, not introduced by this pack, noted here for completeness but out
  of this pack's own scope to fix.
- **Membership's own `region_code` field and `EligibilityRule`'s own
  `region_constraint` field are both plain, open, undefined strings** —
  canon's only other gesture toward regional structure is `CivicSpace`'s
  illustrative example list literally naming "Landesverband," which is
  an example, not a modeled hierarchy. This confirms the user's own
  framing (item 16) that a full regional model is genuinely deferred,
  novel territory, not something already half-built that this pack could
  simply finish.
- **No existing forbidden-link entry (canon section 23) mentions
  `Membership`, `Organization`, `CivicSpace`, party affiliation, or
  region at all** — open territory this pack must define from scratch
  (section 14).

## 3. Proposed vs. canonical entities — at a glance

This section exists specifically because the user's instructions
(item 3) require this pack to state, explicitly and without ambiguity,
what already exists in canon versus what is newly proposed here. Nothing
in this table should be read as already accepted; every "proposed" row
requires its own ADR (sections 18/24) before implementation.

| Entity                                                            | Status                                                                                       | Canon section (if any)                        | Owner (proposed physical service)                                                                                                              |
| ----------------------------------------------------------------- | -------------------------------------------------------------------------------------------- | --------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| `Account`                                                         | Canonical, unchanged                                                                         | 7.2                                           | `account-service` (unchanged)                                                                                                                  |
| `IdentityRecord`                                                  | Canonical, **fields extended** (section 9)                                                   | 7.3                                           | `identity-service` (unchanged owner, extended fields)                                                                                          |
| `EligibilityRule` / `EligibilityDecision` / `EligibilitySnapshot` | Canonical, unchanged                                                                         | 9.1–9.3                                       | `eligibility-service` (unchanged)                                                                                                              |
| `ParticipationCredential`                                         | Canonical, unchanged                                                                         | 10.1                                          | `credential-service` (unchanged)                                                                                                               |
| `RoleAssignment`                                                  | Canonical, unchanged                                                                         | 8.4                                           | `governance-service` (unchanged)                                                                                                               |
| `GovernancePolicy` / `GovernanceDecision`                         | Canonical, unchanged                                                                         | 19b.2–19b.3                                   | `governance-service` (unchanged; sole activation authority for the two new policy entities below, item 10)                                     |
| `Organization`, `CivicSpace`                                      | Canonical, **not implemented by this pack**                                                  | 8.1, 8.2                                      | Deferred to PACK-08                                                                                                                            |
| `Membership`                                                      | Canonical, **implemented for the first time by this pack**, `membership_type = party` scoped | 8.3                                           | **`membership-service`** (new, reuses canon's own owner name)                                                                                  |
| `ParticipantEligibilityPolicy`                                    | **Proposed, new**                                                                            | _(none — new, requires ADR + canon addition)_ | `membership-service`                                                                                                                           |
| `PartyMembershipEligibilityPolicy`                                | **Proposed, new**                                                                            | _(none — new, requires ADR + canon addition)_ | `membership-service`                                                                                                                           |
| `AffiliationDeclaration`                                          | **Proposed, new**                                                                            | _(none — new, requires ADR + canon addition)_ | `membership-service`                                                                                                                           |
| `ConflictAssessment`                                              | **Proposed, new**                                                                            | _(none — new, requires ADR + canon addition)_ | `membership-service`                                                                                                                           |
| `ParticipationRightsProfile`                                      | **Proposed, new — derived read model, never stored as system of record**                     | _(none — new, requires ADR + canon addition)_ | Computed by `membership-service`, mirroring `FinalityStatus`/`DisclosureStatus`'s own established stored-vs-derived pattern (ADR-018, ADR-023) |

"Participant status" (item 1, item 13) is deliberately **not** a new
persisted entity in this table — see section 4.

## 4. Participant categories (item 1)

The five categories the user's item 1 asks this pack to distinguish are
not proposed here as five stored account "types," per this task's own
item 12 instruction ("define rights as policy-derived capabilities, not
fixed account types"). Instead, each is a **derived classification**,
computed from already-existing or newly-proposed state, never itself a
field anyone sets directly:

| Category                             | Derived from                                                                                                                                                                                                                                                                                                                                                                                                                          |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Platform participant                 | `Account.account_status = active` (existing, unchanged) plus a passing `EligibilityDecision` for whichever action is being attempted (existing machinery, section 20's evaluation flow)                                                                                                                                                                                                                                               |
| eID-verified participant             | The above, plus `IdentityRecord.eid_assurance_level` (new proposed field, section 9) meeting a policy-defined minimum for the action in question                                                                                                                                                                                                                                                                                      |
| Party member                         | An **active** `Membership` row (canon 8.3, `membership_type = party`) whose current status further satisfies `PartyMembershipEligibilityPolicy`'s continuing-eligibility conditions (section 12)                                                                                                                                                                                                                                      |
| Holder of a special role             | An **active** `RoleAssignment` (canon 8.4, unchanged) — entirely orthogonal to party membership; a non-member observer/expert can hold a role, and a party member need not hold any role                                                                                                                                                                                                                                              |
| Observer / expert (where applicable) | A `RoleAssignment` whose `role_code` is drawn from a repository-level, participation-specific taxonomy analogous to `governance-service`'s own 8-code pilot taxonomy (ADR-020 §5) — proposed here as a **new**, separate taxonomy (e.g. `civic_observer`, `subject_matter_expert`), never overlapping the governance-specific role codes, since observers/experts are a participation-context concept, not a governance-authority one |

No category above is mutually exclusive with any other except platform
participant vs. party member being a strict superset relationship (every
party member is necessarily also a platform participant; the reverse is
not true). This mirrors, and deliberately does not collapse into,
`GovernanceDecision`/`RoleAssignment`'s own precedent of layering
authority on top of, rather than instead of, base participation.

## 5. Policy dimensions covered — reference table (item 2)

Every dimension the user's item 2 lists is addressed below with an
explicit statement of where it lives and whether a value is fixed here
(answer, per item 17: **no value is ever fixed in this document** — see
section 25 for the full policy-decision inventory).

| Dimension                                 | Lives on                                                                                                            | Fixed here?                    |
| ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------- | ------------------------------ |
| Minimum / maximum age                     | `ParticipantEligibilityPolicy` / `PartyMembershipEligibilityPolicy`, per-action (section 7)                         | No — policy value              |
| Citizenship (incl. multiple citizenships) | `IdentityRecord` (new field, section 9) + policy condition on the two new Policy entities                           | No — policy value              |
| Residence status, habitual residence      | `IdentityRecord` (new field, section 9) + policy condition                                                          | No — policy value              |
| Electoral eligibility                     | Derived claim (`electoral_eligibility_met`, section 15), never a raw stored fact                                    | No — derivation rule is policy |
| Regional affiliation                      | Generic `scope_type`/`scope_id` on `Membership`/the two Policy entities (section 17, deferred structure to PACK-08) | No — structure only            |
| eID assurance level                       | `IdentityRecord` (new field, section 9)                                                                             | No — policy value              |
| Membership duration                       | Derived from `Membership.effective_from` vs. policy-defined minimum duration                                        | No — policy value              |
| Simultaneous membership in other parties  | `AffiliationDeclaration` (section 10) → `ConflictAssessment` (section 11)                                           | No — policy value              |
| Participation in political associations   | `AffiliationDeclaration` → `ConflictAssessment`                                                                     | No — policy value              |
| Public/elected office                     | `AffiliationDeclaration` → `ConflictAssessment`                                                                     | No — policy value              |
| Lobbying / interest-representation roles  | `AffiliationDeclaration` → `ConflictAssessment`                                                                     | No — policy value              |
| Organizational affiliations               | `AffiliationDeclaration` → `ConflictAssessment`                                                                     | No — policy value              |
| Conflicts of interest                     | `ConflictAssessment` (section 11)                                                                                   | No — case-by-case              |
| Incompatibility rules                     | `PartyMembershipEligibilityPolicy.incompatibility_rules` (section 12)                                               | No — policy value              |
| Exemptions and transitional provisions    | `*_transitional_rules` field on both Policy entities (section 12)                                                   | No — policy value              |

## 6. Design decision D1 — Participant policy vs. party-membership policy separation (item 4, requires ADR-026)

**Context.** The user's item 4 requires participant rules and
party-member rules to remain fully separate, with an explicit,
non-overlapping capability list for each.

**Decision:** two independent policy entities,
`ParticipantEligibilityPolicy` and `PartyMembershipEligibilityPolicy`
(section 3), each independently versioned, independently activated, and
each producing its own independent set of derived capabilities
(section 15) — never one combined policy with an internal party/
non-party branch. A party member's capabilities are the **union** of
whatever `ParticipantEligibilityPolicy` already grants (every party
member remains, and is separately evaluated as, a platform participant)
plus whatever `PartyMembershipEligibilityPolicy` additionally grants —
never a replacement of the participant grant.

| Participant policy may permit (item 4)   | Party-member policy may additionally govern (item 4) |
| ---------------------------------------- | ---------------------------------------------------- |
| `can_read_public`                        | `can_vote_as_party_member` (internal party voting)   |
| `can_discuss`                            | Election of party organs                             |
| `can_create_initiative` (drafting)       | `can_stand_for_party_office` (candidacy)             |
| Working-group participation              | Candidate nomination                                 |
| `can_join_civic_consultation` (selected) | Binding internal decisions                           |
| Expert/observer participation            | Access to party-only documents                       |
| —                                        | Party membership duties                              |

Rejected alternative: a single `ParticipationPolicy` with a boolean
`applies_to_party_members` discriminator per rule. Rejected because it
would make it structurally possible to accidentally grant a
party-specific right (e.g. `can_vote_as_party_member`) through the
participant policy's own activation path, which is exactly the kind of
silent conflation this task's item 4 explicitly forbids.

## 7. Age (item 5)

**Design.** Both new Policy entities carry an `age_thresholds` list, not
a single scalar:

```text
AgeThreshold (embedded, repeated, on both Policy entities):
  action_code            — open string; expected initial values:
                           account_registration, public_participation,
                           discussion, initiative_creation,
                           initiative_support, civic_consultation,
                           party_membership, internal_party_voting,
                           candidacy, organizational_role
  minimum_age            — integer | null
  maximum_age            — integer | null (rare; e.g. a youth-quota role)
```

**Derivation rule (item 5, binding on this design):** age is derived
from a verified date of birth held on `IdentityRecord` (new field,
section 9) and is **never** exposed downstream as a raw value. Every
other service — `eligibility-service`, `membership-service`, and any
future consumer — receives only a per-action boolean derived claim,
`age_requirement_met` (section 15), computed inside `identity-service`
or by a narrow, purpose-built read analogous to
`governance-service.verify_role_assignment_for_action` (ADR-022's own
precedent: compute the check where the raw data already lives, return
only a boolean plus a reason code, never the underlying value). This is
the same identity-leakage discipline CT-00-08 already enforces
project-wide (section 27).

Exact threshold values (e.g. "16 for public participation," "18 for
party membership," "21 for candidacy") are **not** selected here — every
one is a policy value, activated by `governance-service`, per item 17
and section 25.

## 8. Citizenship and residence (item 6)

**Design.** `IdentityRecord` gains two new structured fields (not a
single boolean, per item 6's explicit instruction):

```text
citizenship_status (new, proposed):
  citizenships           — list of ISO 3166-1 country codes (empty list
                           permitted, representing statelessness)
  is_stateless           — boolean, derived-or-declared (implementation
                           detail; not fixed here)

residence_status (new, proposed):
  residence_type         — open string; expected initial values:
                           permanent_resident, habitual_resident,
                           non_resident
  territorial_connection — open string scope reference (municipality,
                           district, Land, or federal — generic, per
                           item 16; no enumerated hierarchy defined here)
  electoral_eligibility_declared — boolean; a verified-provider input,
                           not itself the final `electoral_eligibility_met`
                           derived claim (section 15), which also factors
                           in age and any policy-defined exclusion
```

Both new Policy entities carry citizenship/residence **conditions**
(e.g. "German citizenship required," "EU citizenship sufficient,"
"any citizenship with permanent residence sufficient," "stateless
persons: [policy-defined]") referencing these fields — never a single
German/non-German boolean, per item 6's explicit instruction. Multiple
citizenships are a first-class case: a policy condition can require
"German citizenship present in the list" without requiring it to be the
only one, and can separately flag dual citizenship itself as a
declarable fact for a future conflict check (section 10) if a
jurisdiction's rules ever require it — this specification does not
assume they do.

## 9. Design decision D2 — where do age/citizenship/residence/eID-assurance fields live (requires ADR-026)

**Context.** None of these four attribute groups exist anywhere today.
Two placement options exist.

**Option A (recommended): extend the existing canonical `IdentityRecord`
(7.3)** with four new, nullable, additive fields:
`date_of_birth` (verified, never exposed raw downstream), `citizenship_status`
(section 8), `residence_status` (section 8), and `eid_assurance_level`
(new enum, `none | low | substantial | high`, modeled on eIDAS
assurance levels but not itself an eIDAS integration — see section 29's
explicit exclusions). This keeps every verified-identity attribute under
one canonical owner ("Identity Verification Service" — unchanged),
consistent with `IdentityRecord`'s own existing purpose statement and
with this project's established precedent of extending an existing
canonical entity rather than forking a parallel one when the new
content is squarely within that entity's existing responsibility
(compare ADR-023's own `AIProcessingRecord` extension, PACK-06, rather
than a new entity).

**Option B (rejected): a new, separate `CitizenshipRecord`/
`ResidenceRecord` entity.** Rejected because it would duplicate
`IdentityRecord`'s own verification/provenance metadata
(`verification_provider`, `verified_at`, `provider_reference`) for no
structural benefit, and would create a second identity-shaped entity
this project's own CT-00-08 identity-leakage tests would then need to
cover independently rather than reusing `IdentityRecord`'s own,
already-hardened boundary.

**Consequence if Option A is accepted:** `IdentityRecord`'s existing
forbidden-content list (7.3: "не содержит список голосований, выбранные
варианты, список инициатив, политические предпочтения, делегирования")
is unaffected — none of the four new fields are voting- or
initiative-adjacent. `IdentityRecord.country`'s own undocumented
semantics (section 2) are **not** repurposed to mean citizenship — a new,
separate `citizenship_status.citizenships` field is added instead,
leaving `country`'s existing meaning exactly as ambiguous (and as
untouched) as it is today, to avoid silently redefining an existing
field's semantics without its own dedicated ADR.

## 10. Simultaneous participation, affiliation declarations (item 7)

**Design.** `AffiliationDeclaration` (new, proposed):

```text
AffiliationDeclaration:
  affiliation_declaration_id
  subject_reference        — opaque; the account or membership this
                             declaration concerns
  affiliation_type         — open string; expected initial values:
                             other_party_membership,
                             political_association_membership,
                             public_office, elected_office,
                             lobbying_or_interest_representation,
                             organizational_leadership_or_employment,
                             declared_incompatible_organization
  declared_reference        — opaque; never a free-text organization name
                             at the schema level (item 7's own rule:
                             "organization names and sensitive details
                             are restricted by default")
  declared_at
  status                    — draft | submitted | under_review |
                             acknowledged | superseded | withdrawn
  supersedes_declaration_id — nullable; corrections are always a new row,
                             mirroring `GovernanceDecision`'s own
                             immutable-correction pattern (ADR-018)
```

**Binding rules, directly from item 7:**

- Declarations are purpose-scoped — this entity exists to feed
  `ConflictAssessment` (section 11), never to build a general
  political-profiling system. No query interface is proposed that lists
  a person's declarations for any purpose other than an open
  `ConflictAssessment` or a policy-defined compliance check.
- Only the data required for a concrete compatibility or conflict check
  may be read by any consuming service — `declared_reference` is opaque
  at the schema level specifically so that no service other than
  `membership-service` itself (and, for review purposes, an authorized
  `ConflictAssessment` reviewer) ever sees an actual organization name.
- Public disclosure, if a future implementation pass ever adds it (this
  specification does not require it, section 1), must use redacted
  summaries — e.g. "one active affiliation declaration under review,"
  never the `declared_reference` itself — mirroring
  `DisclosurePolicy`'s own field-level redaction-rule pattern (ADR-014,
  PACK-04) rather than inventing a new redaction mechanism.

## 11. Conflict and incompatibility — `ConflictAssessment` lifecycle (item 8)

**Design.**

```text
ConflictAssessment:
  conflict_assessment_id
  subject_reference
  affiliation_declaration_id   — nullable (a conflict can also be
                                 opened directly by an authorized
                                 reviewer without a prior declaration,
                                 e.g. on discovered evidence)
  conflict_type                — open string; expected initial values:
                                 dual_party_membership,
                                 political_association_conflict,
                                 public_office_incompatibility,
                                 lobbying_role_incompatibility,
                                 organizational_affiliation_conflict,
                                 declared_incompatible_organization
  incompatibility_level         — none | disclosed_no_conflict |
                                 conditional_restriction | incompatible
  status                        — pending | under_review |
                                 resolved_no_conflict |
                                 resolved_conditional |
                                 resolved_incompatible | appealed |
                                 overturned | expired_reevaluation_due
  reason_codes                  — list, section 23
  evidence_references           — list of opaque references, never raw
                                 evidence content inline
  reviewed_by_role_reference     — opaque `RoleAssignment` reference of
                                 the authorized human reviewer
  decision_authority_reference   — nullable `GovernanceDecision`
                                 reference, required whenever the
                                 outcome is `resolved_incompatible` (a
                                 party-membership-ending outcome) —
                                 see item 18 / section 26
  decided_at
  supersedes_conflict_assessment_id — nullable; corrections/re-evaluations
                                 are always a new row, never a rewrite,
                                 mirroring `GovernanceDecision`'s own
                                 immutability pattern
  re_evaluation_due_at           — nullable; supports item 9's
                                 "expiry and re-evaluation" requirement
```

**Lifecycle sequence:** `pending` (opened, from a declaration or
directly) → `under_review` (an authorized reviewer, `RoleAssignment`
holding a to-be-defined `conflict_reviewer` role code, is actively
assessing) → one of the four `resolved_*`/terminal outcomes. An
`appealed` status is available from any `resolved_*` outcome; whether it
resolves through a new `ConflictAssessment` row (`supersedes_*`) or
through canon's existing generic `Appeal` entity (owned by "Appeal
Service," used today for `ModerationDecision` appeals) is an **open
question this specification does not resolve** — `Appeal`'s exact field
shape was not confirmed against `ModerationCase`-specific fields during
this pack's own research, so this is flagged honestly as a question for
the implementing ADR (ADR-026 or a dedicated appeal-path ADR) rather
than asserted either way here.

**Binding rule, directly from item 8, restated without qualification:**
**no automated system may permanently reject or expel a person without
a human decision.** `resolved_incompatible` (and any status that
functionally suspends or terminates party membership) is only ever
reachable through an authorized human reviewer's decision, carrying a
`reason_code` and, for the membership-ending case specifically, a
`GovernanceDecision` reference — never a rule-engine output alone. See
section 26.

## 12. Policy versioning (item 9)

Both `ParticipantEligibilityPolicy` and `PartyMembershipEligibilityPolicy`
share one common shape, mirroring `GovernancePolicy`'s own established
`draft → active → superseded` pattern (19b.2) plus the additional fields
item 9 requires:

```text
{Participant|PartyMembership}EligibilityPolicy:
  policy_id
  policy_version
  status                  — draft | active | superseded
  scope_type               — open string; e.g. platform_wide,
                             organization, region (structure only,
                             per section 17/29 — no enumerated regional
                             hierarchy defined here)
  scope_id                 — opaque, nullable (null = platform_wide)
  effective_from
  effective_until          — nullable
  adopted_by_decision_id   — non-nullable; a `GovernanceDecision`
                             reference (item 10's governance-boundary
                             rule, section 13)
  age_thresholds           — list, section 7
  citizenship_conditions    — list of structured conditions, section 8
  residence_conditions      — list of structured conditions, section 8
  incompatibility_rules     — list of `conflict_type` values this policy
                             treats as automatically triggering a
                             `ConflictAssessment` (PartyMembership policy
                             only — the Participant policy has no
                             incompatibility concept, section 6)
  membership_duration_rules — nullable (PartyMembership policy only)
  exemptions                — list of structured exemption records
                             (item 9's "exemptions and transitional
                             provisions")
  transitional_rules        — free-form structured payload describing
                             how existing members/participants are
                             treated across a version transition (e.g.
                             grandfather clauses) — never silently
                             applied; always an explicit, versioned rule
  supersedes_policy_id      — nullable; corrections are always a new
                             version, never a rewrite
```

**Invariant, directly from item 9:** exactly one `active` version per
`(policy_type, scope_type, scope_id)` tuple at any evaluated time, unless
a future canon addition explicitly permits overlapping regional scopes
— which this specification does not propose (section 17 keeps regional
scope generic and single-valued for now). Every superseded version
remains immutable and queryable — the same historical-record guarantee
`GovernancePolicy`/`GovernanceDecision` already provide.

## 13. Design decision D3 — policy entity ownership and the governance boundary (item 10, requires ADR-027)

**Context.** Item 10 requires `governance-service` to remain sole
authority for policy adoption and activation, while a participation/
membership service may only _evaluate_ the active policy.

**Decision:** `ParticipantEligibilityPolicy` and
`PartyMembershipEligibilityPolicy` are **physically owned and stored by
the new `membership-service`**, not by `governance-service` — but every
transition into `active` status requires a non-nullable
`adopted_by_decision_id` referencing a real, `approved`
`GovernanceDecision` (section 12), verified by a narrow,
purpose-built read into `governance-service` modeled directly on
ADR-022's own precedent (`verify_role_assignment_for_action`): a new
`governance-service.application.verify_decision_authorizes_policy_activation(
decision_id, policy_type, scope_id) -> bool` function that
`membership-service` calls and never bypasses. This mirrors, rather than
duplicates, the exact reviewer-verification pattern this project already
established and refined once (PACK-06's own ADR-022 amendment,
rejecting a "read the row and check it locally" design in favor of "ask
the owning service to confirm authorization and return only a
boolean").

**Rejected alternative:** make the two policy entities new `policy_type`
values on canon's existing `GovernancePolicy` (19b.2), which already has
a `rule_definition` free-form field. Rejected because `GovernancePolicy`
today has a comparatively narrow rule shape and no established convention
for the scope of structured content this pack's two policies need
(age thresholds, citizenship conditions, exemptions, incompatibility
lists); folding this pack's entire domain into `GovernancePolicy.
rule_definition` would make that field's shape effectively
unconstrained and would put party-membership-specific fields directly
inside a Governance-owned entity, which item 4's separation principle
argues against by the same logic that keeps participant and
party-member rules apart.

**What `membership-service` must never do (item 10's explicit list):**

- Silently modify an active policy in place — every change is a new
  `policy_version`, never an in-place field edit.
- Activate a new version itself — only a verified `GovernanceDecision`
  reference can move a `draft` policy to `active`.
- Waive a requirement without an authorized exception rule — any
  exemption must trace to the `exemptions` list on the active policy
  itself (section 12), never an ad hoc runtime bypass.
- Self-approve an eligibility conflict — a `ConflictAssessment` reaching
  `resolved_incompatible` requires the separate `decision_authority_reference`
  (section 11), and the reviewer verifying that reference is never the
  same actor who submitted the underlying `AffiliationDeclaration`,
  mirroring PACK-05's own two-actor-approval / self-review-prohibition
  precedent (ADR-020, PACK-06's own `AI_REVIEW_SELF_APPROVAL_PROHIBITED`
  reason code).

## 14. Privacy and data minimization (item 11)

| Layer                       | Contains                                                                                                                                                                              | Who may read it                                                                                                    |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| Raw verified attributes     | `IdentityRecord.date_of_birth`, `.citizenship_status`, `.residence_status`, `.eid_assurance_level`                                                                                    | `identity-service` only, never exposed raw to any other service or API response                                    |
| Derived eligibility claims  | `age_requirement_met`, `citizenship_requirement_met`, `residence_requirement_met`, `affiliation_compatibility_met`, `electoral_eligibility_met` (booleans, per action/policy version) | `membership-service`, `eligibility-service`, and any consumer needing a yes/no answer — never the underlying value |
| Public membership status    | `Membership.membership_status` (canon 8.3, already public-shaped: active/suspended/etc.)                                                                                              | Anyone with a legitimate reason to see membership status (exact disclosure rules are a policy value, section 25)   |
| Restricted affiliation data | `AffiliationDeclaration.declared_reference`, evidence content                                                                                                                         | `membership-service` and an authorized `ConflictAssessment` reviewer only                                          |
| Conflict-review evidence    | `ConflictAssessment.evidence_references` (opaque; content lives wherever the evidence itself is stored, out of this pack's scope)                                                     | Authorized reviewer only, never a general query surface                                                            |

**Binding rule, directly from item 11:** raw birth date, identity
documents, citizenship documents, or affiliation details are never
spread across services — every cross-service signal is one of the five
derived boolean claims above, plus opaque references. This is the exact
same discipline CT-00-08 already enforces for `ParticipationCredential`
(canon 10.1's own "не содержит ФИО, email или адрес" rule) — this pack
extends that discipline to a new attribute surface rather than
introducing a new one.

## 15. Rights as derived capabilities — `ParticipationRightsProfile` (item 12)

**Design.** A derived, non-stored read model (mirroring `FinalityStatus`,
ADR-018, and `DisclosureStatus`, ADR-023's own established
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

Each boolean is computed from: the currently-`active`
`ParticipantEligibilityPolicy` and/or `PartyMembershipEligibilityPolicy`
(section 12), the subject's current `EligibilityDecision` (canon 9.2,
unchanged, reused), the subject's current `Membership` status if any
(canon 8.3), and — for `can_hold_special_role` only — an active
`RoleAssignment` (canon 8.4, unchanged, read-only). No new field is
proposed on `RoleAssignment` itself; `can_hold_special_role` reflects
whether the subject is _eligible to be granted_ a role under current
policy, not whether one is already held (a separate, already-answerable
question via `RoleAssignment` directly).

## 16. Entity separation table (item 13)

| Concept                        | What it is                                                                                                                                            | Owned by                                  |
| ------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------- |
| Participant status             | Derived classification only (section 4) — never a stored entity                                                                                       | N/A — computed                            |
| `PartyMembership`              | An **active** `Membership` row (canon 8.3) with `membership_type = party`                                                                             | `membership-service`                      |
| `EligibilityDecision`          | Canonical, unchanged (9.2) — the generic process-eligibility verdict                                                                                  | `eligibility-service`                     |
| `ParticipationCredential`      | Canonical, unchanged (10.1) — the scoped action-permission token                                                                                      | `credential-service`                      |
| `RoleAssignment`               | Canonical, unchanged (8.4) — authority/role holding, orthogonal to membership                                                                         | `governance-service`                      |
| `GovernancePolicy`             | Canonical, unchanged (19b.2) — governance's own policy shape, never reused for this pack's policies (section 13)                                      | `governance-service`                      |
| Regional scope                 | Generic `scope_type`/`scope_id` fields only (section 17) — no hierarchy defined                                                                       | Deferred structure, PACK-08               |
| Identity and Credential layers | `IdentityRecord` (extended, section 9) and `ParticipationCredential` (unchanged) remain two separate entities with two separate owners — never merged | `identity-service` / `credential-service` |

## 17. Design decision D4 — `Organization` reference handling and regional-scope readiness (items 15, 16, requires ADR-028)

**Context.** `Membership.organization_id` (canon 8.3) is a required
field, but `Organization` (8.1) is explicitly out of this pack's scope
(section 1, per item 16).

**Option A (recommended):** treat `organization_id` as an opaque,
caller-supplied reference, never dereferenced by `membership-service` —
exactly the established pattern this project already uses for
`TechnicalChallenge.submitter_authorization_reference` (ADR-018) and
`AIProcessingRecord.target_id` (ADR-022). A single, well-known
identifier representing "the party" (EPD Plattform e.V., canon section
3's own legal-operator text) is provisioned as repository-level
configuration — analogous to how ADR-020's bootstrap seed provisions
initial `RoleAssignment` rows out-of-band — rather than requiring a live
`Organization` entity or service to exist first. `scope_type`/`scope_id`
on the two new Policy entities (section 12) follow the same opaque-
reference discipline, with `scope_type = region` deliberately left an
open string with **no** enumerated Bund/Land/Kreis/Bezirk/Ort values,
so that PACK-08 can slot a real hierarchy in later without this pack's
own schema needing to change.

**Option B (rejected):** implement a minimal stub `Organization` entity
now, just enough to satisfy the foreign-key-shaped reference. Rejected
per this task's explicit item 16 instruction not to implement the full
Regional Organization model, and because even a "minimal stub" would
need its own lifecycle/ownership decisions that properly belong to
PACK-08's own specification, not this one.

## 18. Design decision D5 — service decomposition (item 15, requires ADR-026)

**Decision:** one new service, `membership-service` — reusing canon's
own already-declared owner name for `Membership` (section 22) rather
than inventing a new one — owning: `Membership` (canon 8.3, implemented
for the first time, `membership_type = party` as this pack's only
populated value — the field itself stays open for future non-party
membership types), `ParticipantEligibilityPolicy`,
`PartyMembershipEligibilityPolicy`, `AffiliationDeclaration`,
`ConflictAssessment` (all four new, section 3), and the derived
`ParticipationRightsProfile` read model (section 15). This mirrors every
prior pack's own one-new-service-per-pack decomposition (PACK-04
transparency-service, PACK-05 governance-service, PACK-06
ai-processing-service), with the internal module boundary between
"participant policy" and "party-membership policy" logic enforced at
the Python-module level (two separate `domain.py` sections or two
sibling modules), not at the physical-service level — since item 4's
separation requirement is about rule content and evaluation independence,
not about deployment topology, and a second service would need its own
cross-service boundary with `membership-service` for the shared
`Membership`/`ConflictAssessment` machinery both policy types ultimately
feed into.

**Rejected alternative:** two services, `participation-policy-service`
and `party-membership-service`. Rejected because `ConflictAssessment`
and `Membership` themselves are not cleanly splittable between the two
(a `ConflictAssessment` opened against a party member's declared
affiliation is squarely party-membership subject matter, but the
`AffiliationDeclaration` mechanism itself is dimension-neutral) — the
resulting cross-service read/write traffic would be heavier than the
one-service-with-internal-separation alternative, without a
corresponding benefit this task's instructions actually require.

## 19. Cross-pack dependency matrix and read boundary (item 15, requires ADR-027)

| Edge                                                                                                                                       | Direction                   | Purpose                                                                                                                                                                                                                                                 |
| ------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `membership-service` → `identity-service`                                                                                                  | Read-only, narrow           | Resolve `age_requirement_met`/`citizenship_requirement_met`/`residence_requirement_met`/`electoral_eligibility_met` via a new, purpose-built function returning only booleans plus reason codes — never the raw `IdentityRecord` fields (section 9, 14) |
| `membership-service` → `eligibility-service`                                                                                               | Read-only, reused unchanged | Read an existing `EligibilityDecision` where one already exists for the process in question — no duplicate evaluation machinery                                                                                                                         |
| `membership-service` → `governance-service`                                                                                                | Read-only, narrow           | `verify_decision_authorizes_policy_activation` (section 13); a second, separate narrow read verifies a `ConflictAssessment`'s `decision_authority_reference` the same way                                                                               |
| `membership-service` → `credential-service`                                                                                                | Read-only, reused unchanged | Optional: verify an existing `ParticipationCredential` where an action already requires one (e.g. `initiative_support` eligibility gating, mirroring `initiative-service`'s own existing optional eligibility read)                                     |
| `governance-service` → `membership-service`                                                                                                | **None proposed**           | No reverse read edge is proposed; `GovernanceDecision`'s existing `subject_reference` field is generic enough to reference a `ConflictAssessment` or policy-activation subject without a new typed read                                                 |
| `membership-service` → `voting-service` / `tally-service` / `delegation-service` / `credential-service.domain` / `identity-service.domain` | **Forbidden, structural**   | No path from membership/affiliation/conflict data to vote content or vote linkability — see section 27's CT-00-09 treatment                                                                                                                             |
| `membership-service` → `ai-processing-service`                                                                                             | **None**                    | No AI-assisted decision-making anywhere in this pack's design (section 1)                                                                                                                                                                               |

## 20. Policy evaluation flow (item 15)

```text
1. A subject attempts action X (e.g. "apply for party membership").
2. membership-service resolves the currently-active policy for X's
   policy_type and the subject's scope (section 12) — exactly one
   active version exists per (policy_type, scope_type, scope_id).
3. membership-service calls identity-service's narrow read to obtain
   age_requirement_met / citizenship_requirement_met /
   residence_requirement_met / electoral_eligibility_met for action X
   under the active policy's thresholds/conditions (raw values never
   cross this boundary, section 9/14).
4. If the action requires an existing EligibilityDecision (e.g. because
   eligibility-service already governs the same process), that decision
   is read, unchanged, per section 19.
5. If PartyMembershipEligibilityPolicy is in play and any
   incompatibility_rules-listed conflict_type applies (from the
   subject's own AffiliationDeclaration history), a ConflictAssessment
   is opened (or an existing one is checked) before the action can
   proceed (section 11).
6. Every negative outcome carries an explicit reason_code (section 23);
   a manual_review_required-shaped path is always available, mirroring
   EligibilityDecision's own existing value (9.2).
7. On success, membership-service updates Membership.membership_status
   (for membership-specific actions) or simply allows the caller to
   proceed (for participant-only actions, which produce no new stored
   entity at all — only a policy check).
8. ParticipationRightsProfile (section 15) is always computable on
   demand by re-running steps 2-6 read-only, without any of them being
   re-executed as a side-effecting action.
```

## 21. Schemas and OpenAPI scope (item 15)

Not created by this specification (item 22), but scoped for the future
implementation pass: two entity JSON Schemas per new entity (four new
entities plus `Membership` itself, since `Membership` has never had one
— five schemas total), one event-payload schema, and one OpenAPI file
(`contracts/openapi/pack-07.yaml`) tagged `membership-service`,
documenting: policy read endpoints (no write endpoint that bypasses
`adopted_by_decision_id`, section 13), `AffiliationDeclaration`
submission, `ConflictAssessment` read/appeal endpoints, and a
`ParticipationRightsProfile` read endpoint. `verify_decision_authorizes_policy_activation`
and the new `identity-service` narrow read are both documented as
having no HTTP-shaped path of their own, mirroring
`verify_role_assignment_for_action`'s own precedent (ADR-022,
`pack-06.yaml`'s explicit note).

## 22. Event catalog (item 15)

Canon already defines `membership.applied` / `membership.activated` /
`membership.suspended` (20.5) for the generic `Membership` entity — this
pack's own implementation would be the first to actually emit them.
Proposed additions, all new:

- `membership.terminated`, `membership.rejected`, `membership.expired`
  (completing `Membership`'s own status-transition coverage — canon
  20.5 does not yet cover every status in 8.3's own enum)
- `participant_eligibility_policy.activated`,
  `participant_eligibility_policy.superseded`
- `party_membership_eligibility_policy.activated`,
  `party_membership_eligibility_policy.superseded`
- `affiliation_declaration.submitted`, `.updated`, `.withdrawn`
- `conflict_assessment.opened`, `.decided`, `.appealed`, `.overturned`,
  `.reevaluation_due`

`ParticipationRightsProfile` is derived and never stored — it emits no
events of its own, mirroring `FinalityStatus`/`DisclosureStatus`'s own
precedent.

## 23. Reason codes (item 15)

Proposed additions (final list and exact wording to be fixed at
ADR-029, mirroring ADR-024's own PACK-06 precedent):

`PARTICIPANT_AGE_REQUIREMENT_NOT_MET`,
`PARTY_MEMBERSHIP_AGE_REQUIREMENT_NOT_MET`,
`CITIZENSHIP_REQUIREMENT_NOT_MET`, `RESIDENCE_REQUIREMENT_NOT_MET`,
`ELECTORAL_ELIGIBILITY_NOT_MET`, `EID_ASSURANCE_LEVEL_INSUFFICIENT`,
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
`CONFLICT_REVIEW_SELF_APPROVAL_PROHIBITED` (mirroring PACK-06's own
`AI_REVIEW_SELF_APPROVAL_PROHIBITED` precedent for the self-approval
prohibition in section 13).

## 24. Canon version impact (item 20)

Accepting the design decisions above (sections 6, 9, 11–13, 17–18) would
require:

- New fields on `IdentityRecord` (7.3): `date_of_birth`,
  `citizenship_status`, `residence_status`, `eid_assurance_level` —
  additive, nullable, non-breaking.
- Implementation authorization (not a canon-text change itself, since
  `Membership` (8.3) is already fully fielded) for `Membership`, plus
  new canon events completing its status coverage (section 22).
- Four new canonical entities: `ParticipantEligibilityPolicy`,
  `PartyMembershipEligibilityPolicy`, `AffiliationDeclaration`,
  `ConflictAssessment` — each with its own new canon subsection, fields,
  statuses, owner, and forbidden links (section 14's open item).
- A new section 22 ownership-matrix row for each of the four new
  entities (`Membership`'s own row already exists), and new section 23
  forbidden-link entries (e.g. `AffiliationDeclaration`/
  `ConflictAssessment` → `VoteEnvelope`/vote-linkage, analogous to every
  prior pack's own vote-linkability exclusion).

This is a **minor** version bump per canon section 25 — every change is
additive (new nullable fields, new entities, new events), nothing
existing is altered, removed, or redefined:

```text
CANON_VERSION: 0.5.0 → 0.6.0 (proposed, not performed by this document)
```

Not proposed or performed here: any change to `EligibilityRule`,
`EligibilityDecision`, `EligibilitySnapshot`, `RoleAssignment`,
`GovernancePolicy`, `GovernanceDecision`, `TechnicalChallenge`,
`AIProcessingRecord`, `PublicLedgerEntry`, or any other existing entity's
own field shape.

## 25. Legal/political values — policy-decision inventory, not fixed here (item 17)

Every dimension below is identified as a **policy decision**, its
configuration location, and whether it requires `governance-service`
approval, party-statute alignment, or both. No value is selected.

| Decision                                                    | Configured via                                                       | Requires Governance approval?           | Requires party-statute alignment?                            |
| ----------------------------------------------------------- | -------------------------------------------------------------------- | --------------------------------------- | ------------------------------------------------------------ |
| Minimum/maximum age per action                              | `age_thresholds` on both Policy entities                             | Yes (policy activation, section 13)     | Yes, for party-specific actions (candidacy, internal voting) |
| Citizenship conditions (German/EU/other/stateless/multiple) | `citizenship_conditions` on both Policy entities                     | Yes                                     | Yes, for party membership specifically                       |
| Residence conditions                                        | `residence_conditions`                                               | Yes                                     | Yes, for party membership specifically                       |
| Membership duration minimums                                | `membership_duration_rules`                                          | Yes                                     | Yes                                                          |
| Incompatible organizations/roles list                       | `PartyMembershipEligibilityPolicy.incompatibility_rules`             | Yes                                     | Yes — this is squarely party-statute territory               |
| eID assurance level minimums per action                     | `age_thresholds`-analogous list (not detailed above; same mechanism) | Yes                                     | Only where a party-specific action is gated                  |
| Exemptions and transitional provisions                      | `exemptions` / `transitional_rules`                                  | Yes                                     | Case-by-case, depending on what is being exempted            |
| Regional/jurisdiction scoping rules                         | `scope_type`/`scope_id` (structure only, PACK-08 fills in values)    | Yes, once PACK-08 defines the hierarchy | Only if statutes define region-specific membership rules     |

## 26. Human control (item 18)

Restated without qualification, directly from item 18: any
**consequential** rejection, suspension, expulsion, incompatibility
finding, conflict decision, or denial of party membership requires an
authorized human decision, carrying a `reason_code` and a review path.
Concretely: `ConflictAssessment.status` reaching any `resolved_*`
terminal value requires `reviewed_by_role_reference` to be set to a real,
active `RoleAssignment` (never null, never a system/automation actor);
`resolved_incompatible` additionally requires
`decision_authority_reference` (a `GovernanceDecision`, section 11);
`Membership.membership_status` reaching `rejected`, `suspended`, or
`terminated` always traces to either a `ConflictAssessment` decision or
a separate, equally human-authorized membership-application review —
no code path in this design reaches any of those three statuses purely
from a policy-evaluation boolean without a human decision record
attached. An `appealed` path is always available from a terminal
`resolved_*`/rejection outcome (section 11).

## 27. CT-00 applicability (item 19)

| Check                              | Applicability for PACK-07                                                                                                                                                                                                                                                                                                                                  |
| ---------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CT-00-01 Schema Validation         | Applicable, standard — every new entity/event schema validated against real constructed objects                                                                                                                                                                                                                                                            |
| CT-00-02 Unknown Status            | Applicable, standard — every new status enum (`Membership`, `AffiliationDeclaration`, `ConflictAssessment`, both Policy entities) rejects unrecognized values                                                                                                                                                                                              |
| CT-00-03 Forbidden Transition      | Applicable, standard — `Membership`/`ConflictAssessment`/Policy status transition tables                                                                                                                                                                                                                                                                   |
| CT-00-04 Event Idempotency         | Applicable, standard                                                                                                                                                                                                                                                                                                                                       |
| CT-00-05 Unsupported Event Version | Applicable, standard                                                                                                                                                                                                                                                                                                                                       |
| CT-00-06 Missing Permission        | Applicable, standard — every write command requires authorization                                                                                                                                                                                                                                                                                          |
| CT-00-07 Audit Creation            | Applicable, standard — every critical action (policy activation, conflict decision, membership status change) creates an `AuditEvent`                                                                                                                                                                                                                      |
| **CT-00-08 Identity Leakage**      | **Central** — this pack's core discipline (sections 9, 14): no raw `date_of_birth`/`citizenship_status`/`residence_status`/`eid_assurance_level` ever reaches a public payload, event, schema, or audit-visible field outside `identity-service` itself                                                                                                    |
| CT-00-09 Vote Linkability          | Applicable, narrow — a structural, future-safety proof (mirroring PACK-02's own original treatment) that no `Membership`/`AffiliationDeclaration`/`ConflictAssessment` field or read path can reconstruct a link to `VoteEnvelope`                                                                                                                         |
| **CT-00-10 Rule Freeze**           | **Central** — the natural home for this pack's own version-immutability guarantee: once a policy version is `active` its evaluated rule content is frozen for any decision already made under it, mirroring `EligibilityRule`'s own freeze-on-ballot-open precedent (9.1) and PACK-02's own original `EligibilityRule`-based treatment of this exact check |
| CT-00-11 AI Human Control          | Not applicable — no `AIProcessingRecord` content anywhere in this pack's design (section 1)                                                                                                                                                                                                                                                                |
| CT-00-12 Emergency Stop            | Not applicable — no `EmergencyAction` dependency (section 1), consistent with every pack since PACK-02                                                                                                                                                                                                                                                     |

## 28. Definition of Done (for a future implementation pass)

Mirroring every prior pack's own Definition of Done structure
(`PACK-06-SPEC.md` section 19):

1. All five ADRs (026–030, section 30) drafted, reviewed, and accepted
   (with or without amendment) before any code is written.
2. Canon `0.5.0 → 0.6.0` implemented as its own dedicated task, strictly
   after ADR acceptance, per this project's established
   drafting-then-accepting-then-canon-editing sequence.
3. `services/membership-service/` implemented: domain models, status
   transition tables, application commands, storage Protocols with
   in-memory adapters, all four new entities plus `Membership` itself,
   the `ParticipationRightsProfile` derived read model, and the two new
   narrow cross-pack reads (into `identity-service` and
   `governance-service`).
4. `contracts/openapi/pack-07.yaml`, `contracts/reason-codes/pack-07.yml`,
   and every new entity/event JSON Schema, all validated against real
   constructed objects.
5. `tests/contract/test_ct00_01` through `test_ct00_10` extended with
   real PACK-07 cases (section 27); CT-00-11/12 remain documented
   not-applicable.
6. `scripts/check_repository.py`'s `REQUIRED_PATHS` extended with every
   new path; `scripts/verify_versions.py` passing; canon checksum
   changed and re-confirmed exactly once, matching the accepted ADRs.
7. Full local verification suite green (Ruff, mypy, pytest, Prettier),
   followed by the established external-GitHub-Actions revision cycle
   through to a genuine, externally-confirmed PASS — exactly as PACK-02
   through PACK-06 each did.
8. Root `README.md` and `CHANGELOG.md` updated only once that PASS is
   real, per this project's own closeout convention (never claiming
   PASS before external confirmation).

## 29. Explicitly excluded from this pack

- The full `Organization`/`CivicSpace` implementation and any
  Bund/Land/Kreis/Bezirk/Ort regional hierarchy — deferred to PACK-08
  (item 16; section 17).
- Any final age, citizenship, residence, incompatibility, or
  membership-duration value — every one is a policy decision, not fixed
  here (item 17; section 25).
- Real eIDAS integration or any live external eID provider connection —
  `eid_assurance_level` is a repository-side classification field only,
  not an eIDAS protocol implementation.
- Any change to `EligibilityRule`, `EligibilityDecision`,
  `EligibilitySnapshot`, `RoleAssignment`, `GovernancePolicy`,
  `GovernanceDecision`, `TechnicalChallenge`, `AIProcessingRecord`, or
  `PublicLedgerEntry`'s own field shape.
- Any new `AIProcessingRecord`-assisted decision-making anywhere in
  eligibility, membership, or conflict evaluation (item "no automated
  system," section 26, applies to rule-engine automation generally, not
  only AI specifically — this pack proposes no AI involvement of either
  kind).
- Definitive resolution of the `ConflictAssessment` appeal-path question
  (section 11) — whether it reuses canon's existing `Appeal` entity or
  introduces its own — left to the implementing ADR.
- Any service directory, schema, OpenAPI file, ADR, or canon edit (item 22) — this specification is the entire PACK-07 deliverable at this
  stage.

## 30. Summary — ADRs required before any implementation

Following the established five-ADR-per-pack precedent (PACK-04:
011–015; PACK-05: 016–020; PACK-06: 021–025), this pack proposes
**ADR-026 through ADR-030**:

- **ADR-026** — service decomposition (`membership-service`, section 18)
  and the participant/party-membership policy-separation design
  (section 6).
- **ADR-027** — cross-pack boundary: the two new narrow reads into
  `identity-service` and `governance-service` (sections 13, 19), and the
  `Organization`-reference/regional-scope-readiness decision (section 17).
- **ADR-028** — canon `0.5.0 → 0.6.0` additions: `IdentityRecord`
  extensions (section 9), the four new entities' full field/status/event
  definitions (sections 3, 10–12), and new section 22/23 ownership and
  forbidden-link entries (section 24).
- **ADR-029** — reason-code additions (section 23).
- **ADR-030** — policy defaults, exemption/transitional-rule mechanics,
  and the `ConflictAssessment` appeal-path decision (section 11's open
  question) — mirroring ADR-025's own PACK-06 role as the pack's
  "defaults and mechanics" ADR.

No ADR has been drafted yet. No canon edit has been performed. No
`services/membership-service` directory, schema, OpenAPI file, or
implementation code exists. This specification, `PACK-07-SPEC.md`, is
the entire PACK-07 deliverable at this stage — exactly as
`PACK-04-SPEC.md`, `PACK-05-SPEC.md`, and `PACK-06-SPEC.md` each were at
their own equivalent starting point.
