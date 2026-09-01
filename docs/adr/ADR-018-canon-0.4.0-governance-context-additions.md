# ADR-018: Canon 0.4.0 — Governance Context entity, event, and ownership additions

## Status

`accepted`, with amendments to the `TechnicalChallenge` submitter
authorization model, the `GovernanceDecision.finality_outcome`
representation, and the `GovernanceDecision` status enum (see Owner
decision, below).

## Date

2026-07-23

## Owner decision

Accepted with amendments, 2026-07-23. The three new entities, the
twelve-event catalog, the three new ownership-matrix rows, and the D2
`AdministratorRole` clarification are accepted in principle, with the
following three amendments required and now incorporated directly into
this ADR's own text below (not left as a separate addendum the reader
must cross-reference):

1. **`TechnicalChallenge` submitter authorization (D5)** — the original
   proposal's single, mandatory `submitted_by_role_id` field contradicted
   ADR-020's own rule that an eligible participant, without holding any
   governance role, may submit a technical challenge. Replaced with a
   two-field model: `submitter_authorization_type` (enum:
   `participation_credential` | `role_assignment`) and
   `submitter_authorization_reference` (an opaque reference to the
   applicable authorization proof) — an eligible participant submits
   through a valid, ballot-scoped `ParticipationCredential`; an
   authorized observer/reviewer submits through an active, in-scope
   `RoleAssignment`. No `Account`, `IdentityRecord`, person identifier,
   credential secret, `actor_id`, or `RoleAssignment` UUID may appear in
   public output; the raw authorization reference itself remains
   restricted; and challenge adjudicators must not gain a reverse path
   from a `ParticipationCredential` reference back to the participant's
   identity.
2. **Persisted finality outcome separated from derived finality status
   (D4)** — `GovernanceDecision.finality_outcome` now contains only
   persisted, approved outcomes: `final`, `invalidated`. A separate
   query/read model, `FinalityStatus` (`provisional`, `finality_blocked`,
   `final`, `invalidated`), is defined for
   `governance-service.application.get_finality_status`'s return value.
   `provisional` and `finality_blocked` are derived values only and must
   never be stored as `GovernanceDecision.finality_outcome`; `final` and
   `invalidated` require an approved, two-actor `result_finality_
determination` `GovernanceDecision`.
3. **`GovernanceDecision` immutability (D4)** — `superseded` is removed
   from the _stored_ `GovernanceDecision` status enum. Stored statuses
   are now exactly `proposed`, `approved`, `rejected`. A correction or
   reversal remains a new `GovernanceDecision` with
   `supersedes_decision_id`; the older decision's stored status, fields,
   timestamps, and hashes are never changed. Whether a decision has been
   superseded is derived at query time (identical in kind to
   `PublicLedgerEntry`'s own derived-supersession pattern, canon 19a.1),
   never a value written onto the original row — this amendment removes
   the redundant stored value the original proposal still carried
   alongside that same derived-fact logic.

**Per this task's explicit instruction, canon `0.3.0` is not edited as
part of this acceptance.** This ADR reaching `accepted` status
authorizes the canon content described in Decision/D1–D6 (as now
amended) to be added to `docs/canonical/TZ-00-domain-event-canon.md` in
a separate, dedicated, later task — mirroring ADR-010 and ADR-013's own
precedent of proposing full canon text and only editing the document
itself as its own distinct step — but that edit has **not** been
performed here. Canon checksum and `canon_version` remain unchanged at
`0.3.0` as of this acceptance. Implementation of `governance-service`
itself is likewise a separate, later task, not authorized by this
acceptance alone.

## Canon implementation (2026-07-23, follow-on task)

The dedicated canon-edit task referenced above has now been carried out,
as its own separate task following this ADR's (and ADR-020's)
acceptance. Canon section 19b ("Governance Context") now defines
`GovernancePolicy`, `GovernanceDecision`, and `TechnicalChallenge`
exactly as specified in D3–D5 below, including all three Owner-decision
amendments (`TechnicalChallenge.submitter_authorization_type`/
`submitter_authorization_reference` replacing `submitted_by_role_id`;
`GovernanceDecision.finality_outcome`'s two-value stored enum plus the
separate four-value `FinalityStatus` read-model type; and
`GovernanceDecision`'s stored status enum reduced to exactly
`proposed`/`approved`/`rejected`, with no stored `superseded` value).
Section 19b.1 integrates the already-canon-defined `RoleAssignment`
(8.4, unchanged) and resolves D2's `AdministratorRole` clarification.
Section 19b.5 records D6's aggregate result-finality determination
rule; section 19b.6 records ADR-017's accepted cross-pack write
boundary (`voting-service` sole writer of `Ballot`; no
`ResultPublication` mutation; finality via `governance-service`).
Section 20.15 adds the twelve-event Governance catalog; section 22
gained three new ownership-matrix rows; section 23 gained the reworded
`AdministratorRole` entry and the new D4/D5 forbidden-link entries.
`canon_version` moved `0.3.0 → 0.4.0`:

```text
sha256(docs/canonical/TZ-00-domain-event-canon.md) =
  61232dc8488f1dd96ea030fa3c41bd397c1c5cf1c7c8cee484bda0568d02c202
CANON_VERSION = 0.4.0
```

This was a canon-only change — no `services/governance-service`
directory, schema, OpenAPI file, or reason-code registry was created as
part of it, and no PACK-02/03/04 source code was touched.
`governance-service` implementation remains a separate, later task.

## Context

`docs/handover/PACK-05-SPEC.md` section 2 documents a canon-silence
finding closely analogous to the one ADR-013 closed for Transparency:
canon section 5.12 (Governance Context) is an seven-item prose
responsibility list ("системные роли; политика полномочий; версии
правил; emergency procedures; crisis override; audit access; review
procedures"). Unlike Transparency, one Governance-adjacent entity —
`RoleAssignment` (canon 8.4) — is already fully defined with fields and
a status enum, and already has a canon-declared owner ("Permission /
Role Service", section 22). The remainder of 5.12's list — authority
policy, rule versioning, and review procedures — has no formal entity
anywhere in canon, and canon's section 20.1–20.14 event catalog has no
Governance entries at all.

Two prior, already-accepted ADRs explicitly name this exact gap as
something a future Governance pack must resolve: ADR-009 item 14 ("Full
authorization and two-actor approval for invalidation belongs entirely
to the future Governance service") and ADR-010 (the technical-challenge
registration/adjudication mechanism "must be introduced through its own
ADR before real production finality can ever be enabled"). This ADR is
that ADR.

A second, smaller canon-silence finding must also be resolved here:
canon section 23's forbidden-links list contains
`AdministratorRole → право расшифровать тайные голоса` ("the right to
decrypt secret votes"), but `AdministratorRole` is never formally
defined anywhere else in canon — no field list, no status enum, no
section 22 entry. Per the owner's binding instruction for this draft,
this ADR resolves that finding rather than leaving it open.

## Problem

Without canon-level definition, `docs/handover/PACK-05-SPEC.md`'s three
new proposed entities (`GovernancePolicy`, `GovernanceDecision`,
`TechnicalChallenge`) have nowhere authoritative to live, and
`RoleAssignment`'s own implementation would have no canon-declared
Governance-context event catalog to emit into. Left unresolved,
`AdministratorRole` also remains an ambiguous forbidden-link target —
implementable in three structurally different, mutually exclusive ways
depending on which reading is correct, with no way for a contract test
to check against a target that has no defined shape.

## Considered options

- Option A — propose full field-level definitions for
  `GovernancePolicy`, `GovernanceDecision`, and `TechnicalChallenge`,
  their complete event catalog, their ownership-matrix entries, and the
  `AdministratorRole` clarification, in one coherent minor-version
  addition (canon `0.3.0 → 0.4.0`), through this single ADR — mirroring
  exactly how ADR-013 handled Transparency's equivalent gap.
- Option B — propose only `GovernanceDecision` now (the entity every
  other proposed entity and both upstream ADR mandates most directly
  need), deferring `GovernancePolicy` and `TechnicalChallenge` to
  separate, later, narrower ADRs.
- Option C — leave canon silent indefinitely; let `governance-service`
  (ADR-016) define all three new entities as pack-local, non-canonical
  records, documented only in `docs/handover/PACK-05-SPEC.md` and this
  pack's own schemas.

## Decision

**Option A**, per the owner's binding proposal for this draft. The
entities below, their events, and their ownership are proposed as a
canon minor-version bump, `0.3.0 → 0.4.0`, under canon section 25's own
definition of a minor change. **None of this is yet part of the canon
text** — it is what this ADR's acceptance would authorize to be added,
in a separate, dedicated canon-edit task, exactly as ADR-010 and ADR-013
both already established as this project's only legitimate path to
touching the canon document.

### D1 — `RoleAssignment` (no new canon text; implementation-only)

Already fully defined by canon 8.4 (fields: `role_assignment_id`,
`actor_id`, `role_code`, `scope_id`, `valid_from`, `valid_until`,
`assigned_by`, `approval_reference`; statuses: `pending`, `active`,
`suspended`, `expired`, `revoked`) and already owned by "Permission /
Role Service" (section 22). This ADR proposes **no change** to
`RoleAssignment`'s canon text. `role_code`'s closed value set is not a
canon field-shape question — it is a repository-side taxonomy question,
deferred to ADR-020.

### D2 — `AdministratorRole` clarification (resolves canon section 23's undefined reference)

**Resolved, per the owner's binding instruction: `AdministratorRole` is
not a separate entity.** It refers to a `RoleAssignment.role_code` value
(proposed literal: `"administrator"`, finalized by ADR-020's role
taxonomy) — an ordinary `RoleAssignment`, scoped like any other, not a
structurally distinct canonical entity with its own fields or ownership
row. Canon section 23's forbidden-link entry is proposed to be reworded
from `AdministratorRole → право расшифровать тайные голоса` to:

> `RoleAssignment (любой role_code, включая "administrator") →
расшифровка, получение или связывание тайного голоса` — forbidden.

This generalizes the rule beyond the single literal "administrator" role
name: **no `RoleAssignment`, regardless of its `role_code` value, may
ever decrypt, retrieve, or link a secret vote** — per the owner's
explicit instruction. This is not a new capability being restricted; no
code anywhere in this repository today decrypts or links a
`VoteEnvelope` to an identity (CT-00-08/09's existing structural
guarantees already prevent it). This ADR makes the prohibition apply
explicitly and by name to every `RoleAssignment`-scoped role this pack
introduces, closing the possibility that a future "administrator"- or
"governance"-scoped role could be read as an implicit exception to
CT-00-09 simply because it sounds sufficiently privileged.

### D3 — `GovernancePolicy`

Covers canon 5.12's "политика полномочий; версии правил" (authority
policy; rule versions) — a versioned, activatable policy record, the
Governance-context analogue of `DisclosurePolicy` (canon 19a.3).

**Proposed canon-declared owner:** Governance Policy Service (new
section 22 row; physically implemented inside `governance-service`, per
ADR-016).

**Fields:**

- `governance_policy_id` — UUID.
- `policy_type` — enum: `role_taxonomy`, `approval_rule`,
  `challenge_rule`, `oversight_rule` — the category of authority policy
  this version governs. Exhaustive enumeration deferred to ADR-020,
  which fixes the pilot's closed `role_code` taxonomy (`policy_type =
role_taxonomy`) as this ADR's own first real instance.
- `rule_definition` — a JSON object, the versioned policy content itself
  (e.g., for `policy_type = role_taxonomy`, the closed set of permitted
  `role_code` values and which `role_code` may grant which other
  `role_code`, per ADR-020).
- `effective_from` — timestamp.
- `proposed_by_role_id` — UUID, `RoleAssignment` reference — the actor
  proposing this version.
- `approved_by_role_id` — UUID, **not** nullable — every
  `GovernancePolicy` version requires an explicit, two-actor-approved
  activation before it can become `active` (INV-08; the same pattern
  `DisclosurePolicy.approved_by_role_id` already established, canon
  19a.3). Per section 9 of the specification, `approved_by_role_id` must
  differ from `proposed_by_role_id` — this is checked at activation
  time, not merely documented.
- `version` — integer, monotonically increasing per `policy_type`.
- `status` — enum: `draft`, `active`, `superseded`.

**Statuses and transitions:** `draft → active` (requires
`approved_by_role_id` to be set and distinct from `proposed_by_role_id`);
`active → superseded` (only when a new version for the same
`policy_type` becomes `active` — exactly one `active` policy per
`policy_type` at any time, mirroring `DisclosurePolicy`'s own rule). No
transition returns to `draft`.

**Forbidden links:**

- `GovernancePolicy → RoleAssignment.actor_id` in any public-facing
  representation — internal governance data, same category of
  restriction ADR-013 already applied to `DisclosurePolicy.
approved_by_role_id`.

### D4 — `GovernanceDecision`

Covers 5.12's "review procedures" plus the user's "governance decisions
and mandates," "ballot invalidation authorization," and "oversight and
review workflows." One entity with a `decision_type` discriminator,
mirroring `PublicLedgerEntry.subject_type`'s consolidation pattern
(canon 19a.1).

**Proposed canon-declared owner:** Governance Decision Service (new
section 22 row; physically implemented inside `governance-service`).

**Fields:**

- `governance_decision_id` — UUID.
- `decision_type` — enum, **must support at least** (per the owner's
  binding instruction): `ballot_invalidation`,
  `technical_challenge_adjudication`, `result_finality_determination`,
  `mandate`, `oversight_directive`.
- `subject_reference` — a JSON object identifying what this decision is
  about, shaped per `decision_type`:
  - `ballot_invalidation` → `{"ballot_id": <UUID>}`
  - `technical_challenge_adjudication` → `{"technical_challenge_id":
<UUID>}`
  - `result_finality_determination` → `{"result_publication_id":
<UUID>}`
  - `mandate` / `oversight_directive` → free-form, scoped to whatever
    the mandate/directive concerns (e.g. a `RoleAssignment.scope_id`,
    a `ModerationCase.moderation_case_id`) — deliberately not
    over-specified here; a future implementation task, not this ADR,
    fixes the exact allow-listed reference shapes for these two types,
    since neither triggers any cross-pack write (ADR-017).
- `proposed_by_role_id` — UUID, `RoleAssignment` reference.
- `approved_by_role_id` — UUID, nullable while `proposed`, **required
  and distinct from `proposed_by_role_id`** before `status` may reach
  `approved` (INV-08, section 9 of the specification).
- `rejected_by_role_id` — nullable UUID, set only if `status` reaches
  `rejected`; also must differ from `proposed_by_role_id`.
- `reason_code` — string, drawn from `contracts/reason-codes/pack-05.yml`
  (ADR-019) or the reused generic set.
- `evidence_references` — list of strings, free-form references to
  supporting material (mirrors `EmergencyAction.evidence_references`,
  canon 19.1).
- `finality_outcome` — **(amended, Owner decision item 2)** **nullable**
  enum, **meaningful only when `decision_type =
"result_finality_determination"`**, and **containing only persisted,
  approved outcomes: `final`, `invalidated`.** Per the owner's binding
  instruction, this field — not any field on `ResultPublication` — is
  where a result's finality state lives, and it is set exactly once,
  when a `result_finality_determination` `GovernanceDecision` reaches
  `approved` (never before, never on a `rejected` or still-`proposed`
  row). See the "FinalityStatus read model" subsection below for the
  separate, derived four-value representation this field's two stored
  values feed into.
- `created_at` — timestamp.
- `decided_at` — nullable timestamp, set when `status` reaches
  `approved` or `rejected`.
- `supersedes_decision_id` — nullable UUID. **Per the owner's binding
  instruction, every `GovernanceDecision` is immutable once `approved`
  or `rejected`.** A correction or reversal is never an edit to an
  existing decision — it is always a **new** `GovernanceDecision` row
  with `supersedes_decision_id` set to the id of the decision it
  supersedes. Whether a decision has since been superseded is a derived,
  query-time fact, computed the same way `PublicLedgerEntry.
supersedes_entry_id` already establishes this pattern (canon 19a.1) —
  never written back onto the original row, and **(amended, Owner
  decision item 3)** never represented by a stored status value either
  — see Statuses below.
- `status` — **(amended, Owner decision item 3)** enum: `proposed`,
  `approved`, `rejected`. **`superseded` is not a stored value.**

**Statuses and transitions (amended, Owner decision item 3):**
`proposed → approved` (requires `approved_by_role_id`, distinct from
`proposed_by_role_id`); `proposed → rejected` (requires
`rejected_by_role_id`, distinct from `proposed_by_role_id`). **No
transition to any `superseded` value exists, because no such stored
value exists.** Once a row reaches `approved` or `rejected`, its
`status` field is never written again by any command — a decision that
has been superseded is identified exclusively by a derived,
query-time check (does any other `GovernanceDecision` have
`supersedes_decision_id` equal to this row's id), the same "derived
fact, never a stored one" principle `PublicLedgerEntry` (canon 19a.1)
already established, applied here with no residual stored status value
left over from the original (unamended) proposal. No transition returns
to `proposed`.

### FinalityStatus read model (new, Owner decision item 2)

**Not a canonical entity field — a query/read-model type**, returned by
`governance-service.application.get_finality_status(
result_publication_id)` (ADR-017). Four values:

- `provisional` — **derived only.** No `result_finality_determination`
  `GovernanceDecision` yet exists (approved or otherwise) for this
  `ResultPublication`, and no `TechnicalChallenge` against it is
  currently unresolved.
- `finality_blocked` — **derived only.** One or more `TechnicalChallenge`
  records against this `ResultPublication` remain `submitted` or
  `under_review` (D6) — finality determination is structurally
  prohibited while this holds.
- `final` — **reflects a stored value.** The latest, non-superseded,
  `approved` `result_finality_determination` `GovernanceDecision` for
  this `ResultPublication` has `finality_outcome = "final"`.
- `invalidated` — **reflects a stored value.** Symmetric to `final`, for
  `finality_outcome = "invalidated"`.

**`provisional` and `finality_blocked` must never be written as a
`GovernanceDecision.finality_outcome` value** — they exist only as
`FinalityStatus` query results, computed fresh on every call to
`get_finality_status` from `TechnicalChallenge` status data and the
presence/absence of an approved, non-superseded
`result_finality_determination` decision. `final`/`invalidated` are the
**only** two values `finality_outcome` itself may ever hold, and
`FinalityStatus` simply passes them through unchanged when a stored
decision exists. This separation — one persisted, two-value field, plus
a distinct four-value derived read-model type — is deliberate and must
be implemented as two distinct type definitions in schemas and code,
never as one shared four-value enum used inconsistently in both places
(the original, unamended proposal's mistake, corrected by this
amendment).

**Immutability (per the owner's binding instruction, restated as its own
rule):** once a `GovernanceDecision` reaches `approved` or `rejected`,
no field on that row — including `finality_outcome`,
`evidence_references`, or `reason_code` — may ever be rewritten by any
future command. A change of mind, a newly discovered fact, or a
correction of a mistaken ruling is represented **exclusively** as a new
`GovernanceDecision` with `supersedes_decision_id` set, never as an
update to the original.

**Forbidden links:**

- `GovernanceDecision → RoleAssignment.actor_id` in any public-facing
  representation — internal governance data, same restriction as D3.
- `GovernanceDecision.subject_reference → VoteEnvelope` — forbidden;
  no `decision_type` may reference an individual `VoteEnvelope` directly,
  only aggregate `ResultPublication`/`Ballot` identifiers.
- `GovernanceDecision → расшифровка, получение или связывание тайного
голоса` — restating D2's generalized prohibition for this entity
  specifically: no `GovernanceDecision`, regardless of `decision_type`
  or which `RoleAssignment` proposed/approved it, may authorize
  decrypting, retrieving, or linking a secret vote.

### D5 — `TechnicalChallenge`

Directly implements the mechanism ADR-009 item 13 and ADR-010 both name
as still-missing: registration of a challenge against a
`ResultPublication` before its `challenge_deadline_at` (canon 15.6,
ADR-010), and its adjudication — kept structurally distinct from the
`GovernanceDecision` that rules on it (D4's
`technical_challenge_adjudication` decision type), mirroring how
`ModerationCase`/`ModerationDecision` are kept distinct in canon 14.

**Proposed canon-declared owner:** Technical Challenge Service (new
section 22 row; physically implemented inside `governance-service`).

**Fields:**

- `technical_challenge_id` — UUID.
- `result_publication_id` — UUID, the `ResultPublication` (canon 15.6)
  being challenged.
- `submitter_authorization_type` — **(amended, Owner decision item 1,
  replacing the original single, mandatory `submitted_by_role_id`
  field)** enum: `participation_credential` | `role_assignment`.
- `submitter_authorization_reference` — **(amended, Owner decision
  item 1)** an opaque reference to the applicable authorization proof —
  never itself parsed, resolved, or dereferenced by any public-facing
  code path. Its shape depends on `submitter_authorization_type`:
  - `participation_credential` — an eligible participant submits
    through a valid, ballot-scoped `ParticipationCredential` (canon 8.3
    family, owned by Credential Issuer, PACK-02); the reference is an
    opaque credential-commitment-shaped value, never the credential's
    own internal secret material or a resolvable pointer to the
    participant's `Account`/`IdentityRecord`.
  - `role_assignment` — an authorized observer/reviewer submits through
    an active, in-scope `RoleAssignment`; the reference is that
    `RoleAssignment`'s id.

  **The original single-field, `RoleAssignment`-only model is replaced
  because it structurally contradicted ADR-020's own rule that an
  eligible participant, holding no governance role at all, may submit a
  challenge** — a mandatory `RoleAssignment` reference would have made
  that impossible to represent honestly. **Rules (Owner decision
  item 1, verbatim):** an eligible participant submits through a valid,
  ballot-scoped `ParticipationCredential`; an authorized observer/
  reviewer submits through an active, in-scope `RoleAssignment`; no
  `Account`, `IdentityRecord`, person identifier, credential secret,
  `actor_id`, or `RoleAssignment` UUID may appear in public output; the
  raw authorization reference remains restricted; and challenge
  adjudicators must not gain a reverse path from the participation
  credential to the participant's identity.

  **Validation boundary, stated explicitly so this amendment does not
  silently reopen ADR-017's dependency matrix:** `governance-service`
  validates a `role_assignment`-type reference directly — `RoleAssignment`
  is its own entity, an active/in-scope check is a local lookup, no
  cross-pack read is required. A `participation_credential`-type
  reference is **not** independently re-validated against
  `credential-service`/`eligibility-service` by `governance-service` —
  ADR-017 deliberately excludes both services from this pack's
  dependency matrix, and this amendment does not add a new upstream
  read to reopen that boundary. Instead, the reference is accepted as
  caller-supplied, structurally-opaque proof, exactly the same trust
  relationship `transparency-service`'s `publish_ledger_entry`
  established for PACK-04's own caller-supplied `raw_content`
  (`docs/handover/PACK-04-REPORT.md` section 6) — the caller (whatever
  upstream flow already holds and can attest to the participant's
  `ParticipationCredential`) is responsible for the reference's
  validity; `governance-service` stores and structurally protects it,
  but does not itself dereference it. This is also precisely what
  guarantees "challenge adjudicators must not gain a reverse path from
  the participation credential to the participant's identity" —
  `governance-service` never imports `credential-service` or
  `identity-service` at all (ADR-017), so no code path inside it could
  perform that resolution even in error.

- `challenge_reason_code` — string, drawn from
  `contracts/reason-codes/pack-05.yml` (ADR-019).
- `evidence_references` — list of strings.
- `submitted_at` — timestamp. Must be strictly before the referenced
  `ResultPublication.challenge_deadline_at` (read via
  `epd2_tally_service.application.get_result_publication`, ADR-017) —
  enforced at submission time
  (`TECHNICAL_CHALLENGE_WINDOW_CLOSED`, ADR-019).
- `governance_decision_id` — nullable UUID, set once adjudicated: the
  `GovernanceDecision` (D4, `decision_type =
technical_challenge_adjudication`) that rules on this specific
  challenge.
- `status` — enum: `submitted`, `under_review`, `upheld`, `rejected`.

**Statuses and transitions:** `submitted → under_review` (adjudication
begins); `under_review → upheld` or `under_review → rejected` (via the
linked `GovernanceDecision`, D4). **No transition out of `upheld` or
`rejected`** — per the owner's binding instruction (ADR-020 item 3), a
`TechnicalChallenge` is never resubmitted or re-adjudicated once it
reaches either terminal status
(`TECHNICAL_CHALLENGE_ALREADY_ADJUDICATED`, ADR-019); a new integrity
concern about the same `ResultPublication` requires an entirely new
`TechnicalChallenge` row, preserving a complete history rather than
overwriting one outcome with another.

**Forbidden links:**

- `TechnicalChallenge.submitter_authorization_reference → public
content` — **(amended, field renamed per Owner decision item 1)**
  forbidden verbatim in any public-facing view, per the owner's
  instruction that "submitter identity remains restricted and is never
  public" (ADR-020 item 2) — only an approved, generalized role-scope
  label (for the `role_assignment` path), if any representation is
  shown at all, mirroring the `*_role_id` public-exposure restriction
  ADR-013 already established; the `participation_credential` path has
  no public representation at all, per the owner's instruction, not
  even a generalized label.
- `TechnicalChallenge → Account` / `IdentityRecord` / person identifier
  / credential secret / `actor_id` / `RoleAssignment` UUID, in any
  public output — forbidden, restating Owner decision item 1's rule
  explicitly as its own structural link, not merely as prose.
- `TechnicalChallenge → VoteEnvelope` — forbidden; a challenge concerns
  `ResultPublication`-level aggregate integrity, never an individual
  vote.

### D6 — Aggregate result-finality determination rule

Per the owner's binding instruction (ADR-020 item 3), restated here as
canon-level content since it governs how `GovernanceDecision` and
`TechnicalChallenge` interact structurally, not merely as an
implementation default:

- Each `TechnicalChallenge` against a given `ResultPublication` receives
  its **own** `technical_challenge_adjudication` `GovernanceDecision` —
  adjudication is always one-to-one with the challenge it rules on,
  never batched across multiple challenges.
- **Exactly one** aggregate `result_finality_determination`
  `GovernanceDecision` is created for a given `ResultPublication`, and
  only after **every** `TechnicalChallenge` submitted against it has
  reached `upheld` or `rejected`. Finality determination for that
  `ResultPublication` is structurally prohibited while any
  `TechnicalChallenge` remains `submitted` or `under_review`
  (`RESULT_FINALITY_BLOCKED_BY_OPEN_CHALLENGE`, ADR-019).
- **Contradictory finality decisions are forbidden**: once an
  `approved` `result_finality_determination` decision exists for a
  `ResultPublication` (and has not itself been superseded), a second,
  independent `result_finality_determination` decision for the same
  `ResultPublication` may never be created —
  only a new decision with `supersedes_decision_id` pointing at the
  prior one may replace it (`RESULT_FINALITY_DETERMINATION_DUPLICATE`,
  ADR-019), never a second, unrelated ruling standing alongside the
  first.
- If `challenge_deadline_at` elapses with **zero** `TechnicalChallenge`
  records submitted, a `result_finality_determination`
  `GovernanceDecision` is still **required**, explicitly, two-actor
  approved — the elapsed deadline is a precondition for creating it,
  never a substitute (ADR-010's own "no module may auto-declare
  finality" prohibition, restated here as a structural rule this
  entity's own lifecycle enforces).

### Proposed Governance event catalog (new canon section 20.15)

None of the following events exist in canon today (canon sections
20.1–20.14 have no Governance entries). Proposed:

`governance.role_assignment_requested`,
`governance.role_assignment_activated`,
`governance.role_assignment_revoked`,
`governance.policy_proposed`, `governance.policy_activated`,
`governance.policy_superseded`, `governance.decision_proposed`,
`governance.decision_approved`, `governance.decision_rejected`,
`governance.decision_superseded`,
`governance.technical_challenge_submitted`,
`governance.technical_challenge_adjudicated`.

Every event uses canon section 21's envelope verbatim, exactly as every
prior pack's events already do — no new envelope field, no relaxed
idempotency rule.

### Proposed section 22 (ownership matrix) additions

| Entity               | Proposed canon-declared owner |
| -------------------- | ----------------------------- |
| `GovernancePolicy`   | Governance Policy Service     |
| `GovernanceDecision` | Governance Decision Service   |
| `TechnicalChallenge` | Technical Challenge Service   |

Three new rows in canon section 22's 31-row matrix (post-ADR-013),
bringing it to 34. `RoleAssignment`'s existing row ("Permission / Role
Service") is unchanged. ADR-016 proposes all three new rows, plus
`RoleAssignment`'s implementation, physically inside one
`services/governance-service`.

## Consequences

Once the separate, dedicated canon-edit task is carried out (mirroring
ADR-013's own two-step precedent — accept first, edit canon as a later,
distinct task), `docs/canonical/TZ-00-domain-event-canon.md` would gain:
a new entity section for each of `GovernancePolicy`, `GovernanceDecision`,
`TechnicalChallenge` (D3–D5, as amended per Owner decision) with
fields/statuses/forbidden-links exactly as specified above; a new
`## 20.15. Governance` event catalog subsection; three new rows in
section 22's ownership matrix; the D2 rewording of `AdministratorRole`'s
forbidden-link entry in section 23; and D4/D5's forbidden-link
additions. `canon_version` would move `0.3.0 → 0.4.0`, mirrored in
`docs/canonical/canon-version.json`,
`packages/python/epd2-core/src/epd2_core/version.py`, and
`packages/typescript/epd2-types/src/version.ts`. **None of this is
performed by this ADR's acceptance itself** — per this task's explicit
instruction, canon is not modified as part of this acceptance; the
canon-edit task remains separate and has not been performed.

## Security impact

D2's generalized rewording is this ADR's most security-relevant
decision: it converts an undefined, single-literal forbidden-link target
(`AdministratorRole`) into an explicit, general rule that applies to
every `RoleAssignment`-scoped role this and any future pack ever
introduces, closing off the possibility that a newly-invented
governance-sounding role could be read as implicitly exempt from
CT-00-09's vote-linkability guarantee. `GovernanceDecision`'s
immutability rule (D4, amended, Owner decision item 3) is a second
security-relevant control, now strengthened by the amendment: there is
no `superseded` stored value at all for any later, buggy, or malicious
code path to write — a decision's immutability is enforced by the
absence of any status transition out of `approved`/`rejected`, not
merely by a convention not to use one. `TechnicalChallenge`'s amended
submitter-authorization model (D5, Owner decision item 1) is a third,
newly-introduced security-relevant control: it makes participant-
submitted challenges possible without ever requiring a `RoleAssignment`
for them, while the explicit validation-boundary note prevents this from
becoming an implicit new identity-adjacent dependency —
`governance-service` still imports no PACK-02 identity/credential
service (ADR-017 unchanged), so no in-process code path in this pack can
ever resolve a `participation_credential`-type reference back to an
`Account` or `IdentityRecord`, structurally guaranteeing "no reverse path
from the participation credential to the participant's identity" rather
than merely documenting it as a rule to follow.

## Data impact

Three new canonical entities, twelve new canonical events, three new
ownership-matrix rows, one reworded forbidden-link entry (D2), and
several new/amended forbidden-link entries (D4, D5). No existing
canonical entity's fields, statuses, or owner change — `Ballot` and
`ResultPublication` are both **read** (via ADR-017's sanctioned
functions) but neither gains a new field or status under this ADR,
satisfying canon section 25's own definition of a minor version change.
The amendments themselves change no _existing_ canonical entity either —
they revise this ADR's own three new-entity proposals
(`GovernanceDecision.finality_outcome`/`status`,
`TechnicalChallenge.submitter_authorization_type`/
`submitter_authorization_reference`) before any of it has ever become
real canon text, the same kind of pre-canon-edit amendment ADR-013
already made for its own four entities.

## Migration impact

None — no `services/governance-service` exists yet. Once implemented, no
PACK-02/03/04 entity requires backfill; the three new entities start
empty.

## Reversibility

Reversible with cost before code exists (this stage). Once real
`GovernanceDecision`/`TechnicalChallenge` records exist — especially
given D4's immutability-after-approval rule — removing or renaming a
field becomes a major-version-equivalent change under canon section 25,
the same reversibility profile every other canonical entity has once
real data exists under it.

## Related canon version

Authored against canon version `0.3.0`. Accepted with amendments per
Owner decision, above, proposing a minor bump to `0.4.0`; the
corresponding canon edit itself is performed as its own separate,
dedicated follow-on task, mirroring ADR-010 and ADR-013's precedent, not
as part of this ADR's own acceptance — that follow-on task has not been
carried out.
