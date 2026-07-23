# ADR-013: Canon 0.3.0 — Transparency Context entity, event, and ownership additions

## Status

`accepted`, with amendments to the `AuditExportPackage` proof semantics,
the `DisclosurePolicy` field model, `PublicLedgerEntry`/`LobbyLogEntry`
correction semantics, and role-reference public-exposure rules (see
Owner decision, below).

## Date

2026-07-23

## Owner decision

Accepted with amendments, 2026-07-23. The four entities, event catalog,
and ownership-matrix additions (Decision, D3.1–D3.6) are accepted in
principle, with the following four amendments required and now
incorporated directly into this ADR's own text below (not left as a
separate addendum the reader must cross-reference):

1. **`AuditExportPackage` proof semantics (D3.2)** — the original
   proposal's `chain_proof` (a bare list of `event_hash` values) and its
   companion claim (originally stated in ADR-015) that "an external
   verifier can recompute and confirm the hash chain independently"
   contradicted this same package's own redaction guarantees:
   `AuditEvent.event_hash` (canon 18.1) is computed over fields
   (`actor_id`, `actor_type`, `before_hash`, `after_hash`) this package
   deliberately never surfaces, so no external verifier could actually
   recompute it from the public export alone. `chain_proof` is now a list
   of structured proof items (`event_hash`, `previous_event_hash`,
   public-safe metadata, `sequence_position`), plus new package-level
   `package_digest` and `integrity_proof` fields, and a new "Verification
   semantics" subsection (D3.2) explicitly distinguishing public
   chain-continuity/ordering/non-modification verification (what this
   package proves) from full private `AuditEvent` hash recomputation
   (what it does not, and never claims to, prove).
2. **`DisclosurePolicy` field model (D3.3)** — the single policy-level
   `disclosure_class` field plus a loose `field_redaction_rules` list is
   replaced with a structured `field_rules` list, each entry carrying
   `field_path`, `disclosure_class`, `transformation`, and an optional
   `replacement_label`. Every candidate public field must resolve to
   exactly one applicable rule; a field with no matching rule, or more
   than one, defaults to `prohibited` (fail-closed) rather than erring
   toward disclosure. Structurally forbidden fields (identity, credential,
   vote-envelope, delegation, private audit fields, and — per amendment 4
   below — the internal `*_role_id` references) remain outside the
   candidate set entirely and cannot be reclassified by any policy,
   however written or approved.
3. **`PublicLedgerEntry` corrections (D3.1)** — a published entry's
   stored `status`, `content_snapshot`, and hash fields are now never
   rewritten after creation, full stop; there is no `corrected` stored
   status value. A correction is exclusively a new `PublicLedgerEntry`
   row with `supersedes_entry_id` set. Whether an entry has since been
   superseded is a derived, query-time fact, never written back onto the
   original row. The identical rule is extended to `LobbyLogEntry` (D3.4)
   for consistency, since it has the same `supersedes_entry_id`
   correction shape and the owner's underlying principle applies equally
   — flagged here explicitly as this ADR's own consistent generalization
   of an owner-specified rule, not a separate owner instruction.
4. **Role references (D3.1–D3.4)** — `published_by_role_id` and
   `submitted_by_role_id` are confirmed as internal governance references
   that must never appear verbatim in public content; only an approved,
   generalized role-scope `replacement_label` (via D3.3's `field_rules`)
   may appear publicly. This ADR extends the identical rule to
   `requested_by_role_id` (D3.2) and `approved_by_role_id` (D3.3) for
   consistency, as the same category of internal reference for the same
   reason — an extension beyond the two fields named in the owner's
   decision, flagged here explicitly as this ADR's own generalization,
   not a separate owner instruction.

**Per this task's explicit instruction, canon `0.2.0` is not edited as
part of this acceptance.** This ADR reaching `accepted` status authorizes
the canon content described in Decision/D3.1–D3.6 (as now amended) to be
added to `docs/canonical/TZ-00-domain-event-canon.md` in a separate,
dedicated, later task — mirroring ADR-010's own precedent of proposing
full canon text and only editing the document itself as its own distinct
step — but that edit has **not** been performed here. Canon checksum and
`canon_version` remain unchanged at `0.2.0` as of this acceptance.
Implementation of `transparency-service` itself is likewise a separate,
later task, not authorized by this acceptance alone.

## Canon implementation (2026-07-23, follow-on task)

The dedicated canon-edit task referenced above has now been carried out,
as its own separate task following this ADR's acceptance. Canon section
19a ("Прозрачность / Transparency Context") now defines
`PublicLedgerEntry`, `AuditExportPackage`, `DisclosurePolicy`, and
`LobbyLogEntry` exactly as specified in D3.1–D3.6 below, including all
four Owner-decision amendments (`chain_proof`'s structured proof items
plus `package_digest`/`integrity_proof`; `DisclosurePolicy.field_rules`;
`PublicLedgerEntry`/`LobbyLogEntry` creation-time immutability; and the
four internal `*_role_id` fields' public-exposure restriction). Section
20.14 adds the ten-event Transparency catalog; section 22 gained four new
ownership-matrix rows; section 23 gained the new forbidden-link entries.
`canon_version` moved `0.2.0 → 0.3.0`:

```text
sha256(docs/canonical/TZ-00-domain-event-canon.md) =
  9fc04b928ff043d25354039165eb7a9d0683396c6712210594eef232d6daf9ad
CANON_VERSION = 0.3.0
```

This was a canon-only change — no `services/transparency-service`
directory, schema, OpenAPI file, or reason-code registry was created as
part of it, and no PACK-02/03 source code was touched.
`transparency-service` implementation remains a separate, later task.

## Context

`docs/handover/PACK-04-SPEC.md` section 2 documents a canon-silence
finding: canon section 5.11 (Transparency Context) is a nine-item prose
responsibility list only. Unlike PACK-03's eighteen entities, which
canon had already fully defined (sections 11–16) before PACK-03's own
ADR-005/006/008/009/010 governance round began, canon defines **zero**
formal Transparency entities, **zero** Transparency events in its
section 20.1–20.13 catalog, and **no** Transparency entry in section 22's
27-row ownership matrix. The only Transparency-context entity canon names
anywhere is `PublicLedgerEntry`, and only once, in passing, as the
subject of a forbidden-link rule (section 23: `PublicLedgerEntry →
непубличные персональные данные`) — it has never been given a field
list, an identifier scheme, or a canon-declared owning module.

This is the same category of gap ADR-010 closed for `Ballot.challenge_window_hours`/
`ResultPublication.challenge_deadline_at` — a property that belongs to
the canon document itself, not to a pack-level registry file — but larger
in scope: ADR-010 added two fields to two already-defined entities;
this ADR proposes defining four entities from nothing, plus their entire
event catalog, plus their ownership-matrix entries. This is, by a wide
margin, the largest single canon addition this project has proposed to
date, and was treated with commensurately higher scrutiny — including a
full amendment round (Owner decision, above) before acceptance.

## Problem

Without canon-level definition, `docs/handover/PACK-04-SPEC.md`'s four
proposed entities (`PublicLedgerEntry`, `AuditExportPackage`,
`DisclosurePolicy`, `LobbyLogEntry`) have nowhere authoritative to live.
Any implementation would either invent undocumented, pack-local field
lists (exactly the kind of undocumented deviation canon section 26 exists
to prevent — and a worse instance of it than any prior pack risked,
since these are new entities with no existing canon text to even diverge
from) or leave "what exactly gets published, and how" as an
implementation-time judgment call for a domain (public disclosure of
politically significant decisions) where INV-04, INV-09, and INV-10 all
demand explicit, explainable, fail-closed behavior.

## Considered options

- Option A — propose full field-level definitions for all four entities,
  their complete event catalog, and their ownership-matrix entries in one
  coherent minor-version addition (canon `0.2.0 → 0.3.0`), through this
  single ADR.
- Option B — propose only `PublicLedgerEntry` now (the one entity canon
  already names), deferring `AuditExportPackage`, `DisclosurePolicy`, and
  `LobbyLogEntry` to separate, later, narrower ADRs as each is actually
  needed by implementation.
- Option C — leave canon silent indefinitely; let `transparency-service`
  (ADR-011) define these four entities as pack-local, non-canonical
  records, documented only in `docs/handover/PACK-04-SPEC.md` and this
  pack's own schemas, never in the canon document itself.

## Decision

Option A, accepted with amendments (Owner decision, above). The four
entities below, their events, and their ownership are proposed as a
canon minor-version bump, `0.2.0 → 0.3.0`, under canon section 25's own
definition of a minor change ("добавление обратно совместимой сущности,
поля, события или статуса"). **None of this is yet part of the canon
text** — it is what this ADR's acceptance authorizes to be added, in a
separate, dedicated canon-edit task, exactly as ADR-010 established as
this project's only legitimate path to touching the canon document.

### D3.1 — `PublicLedgerEntry`

The one entity canon already references (section 23). Proposed as the
single, generic "published record" wrapper for
"публичный реестр инициатив, реестр решений, история версий, результаты,
журналы модерации" (canon 5.11) — one entity type with a `subject_type`
discriminator, not five near-duplicate entities, following the same
consolidation reasoning PACK-03-SPEC.md section 3 used for its own
service groupings.

**Canon-declared owner:** Public Ledger Service (new section 22 row;
physically implemented inside `transparency-service`, per ADR-011).

**Fields:**

- `public_ledger_entry_id` — UUID, canonical identifier (canon section 6).
- `subject_type` — enum: `initiative`, `initiative_version`,
  `moderation_decision`, `result_publication`, `ai_processing_record`.
  The fifth value is proposed but structurally dormant — see D3.5 below.
- `subject_id` — UUID, the canonical identifier of the underlying entity
  this ledger entry publishes a record of (e.g. `Initiative.initiative_id`).
- `subject_event_id` — UUID, the canonical event (section 20.x) whose
  occurrence this ledger entry publishes (e.g. the `initiative.published`
  event's own `event_id`). Ties every ledger entry to a specific,
  already-recorded canonical event rather than to a live, mutable read of
  the source entity — the ledger entry is a historical record of "this
  event happened," not a cache of "this is the entity's current state."
- `published_at` — timestamp.
- `published_by_role_id` — nullable UUID, a `RoleAssignment` (canon 8.4)
  reference. Null for publications that are a direct, automatic
  consequence of a canonical status transition (e.g. an `Initiative`
  reaching `published` status); set only when a human, role-gated
  decision was required to publish (e.g. a `ModerationDecision` entry
  under a `DisclosurePolicy` requiring explicit review, D3.3 below).
  **Never** a reference to an `Account` or `IdentityRecord` — a
  `RoleAssignment` is a scoped permission grant, not a person.
  **Amended (Owner decision item 4):** this field is internal governance
  data and never appears verbatim in public content; a public view may
  expose only an approved, generalized role-scope `replacement_label`
  (D3.3's `field_rules`), never the raw `RoleAssignment` id itself.
- `content_snapshot` — a JSON object: the redacted, publication-eligible
  fields of the subject entity, copied at publication time. Never a live
  foreign-key pointer to the source entity's current (possibly since-
  changed) state — this is what makes correction-as-new-entry (below)
  meaningful and satisfies INV-05 ("нельзя бесследно изменять историю").
- `content_hash` — SHA-256 hex digest of `content_snapshot`, chaining
  into `AuditExportPackage` (D3.2) for hash-chain proof.
- `previous_entry_hash` — nullable SHA-256 hex digest: the `content_hash`
  of the immediately preceding `PublicLedgerEntry` for the same
  `subject_id`, forming a per-subject hash chain (not a single global
  chain) — this gives each published subject (an `Initiative`, a
  `Ballot`'s `ResultPublication`, etc.) its own independently verifiable
  version history, distinct from `epd2_audit_core`'s own repository-wide
  chain.
- `disclosure_policy_id` — UUID, the active `DisclosurePolicy` (D3.3)
  applied at publication time.
- `redaction_notice` — nullable string/enum, a machine-readable note of
  what was omitted (e.g. `"reviewer_actor_identity_redacted"`),
  satisfying INV-09 (a refusal or omission must be explicable) without
  disclosing the redacted content itself.
- `supersedes_entry_id` — nullable UUID, set only on a **correcting**
  entry, pointing at the `PublicLedgerEntry` it corrects. See Corrections,
  below (amended).
- `status` — enum, see Statuses below.

**Statuses (amended, Owner decision item 3):** `published` is the
**only** stored value this field ever takes. There is no `corrected`
stored status. A `PublicLedgerEntry`'s own `status` field never changes
after creation.

**Corrections (amended, replaces the original "Allowed transitions"
text):** A correction is represented **exclusively** as a new
`PublicLedgerEntry` row with `supersedes_entry_id` set to the id of the
entry it corrects — never as an in-place update. The corrected (older)
entry's own stored `status`, `content_snapshot`, `content_hash`,
`previous_entry_hash`, and every other field are **never rewritten**
after creation — no code path may write to an existing `PublicLedgerEntry`
row post-creation, full stop. Whether an entry has since been superseded
is a **derived, query-time fact**, computed by checking whether any
other `PublicLedgerEntry` has `supersedes_entry_id` equal to this entry's
id — never a value written back onto the original row. This implements
INV-05 at the strongest level this repository has applied it so far: not
merely "preserve the previous version somewhere," but "never touch the
original row again once written."

**Forbidden links** (structural, extending canon section 23's existing
generic rule with the specific reference targets this entity must never
declare):

- `PublicLedgerEntry → Account` — forbidden.
- `PublicLedgerEntry → IdentityRecord` — forbidden.
- `PublicLedgerEntry → ParticipationCredential` — forbidden.
- `PublicLedgerEntry → VoteEnvelope` — forbidden (a `result_publication`
  ledger entry may only ever carry `ResultPublication`'s own aggregate
  fields, never any individual `VoteEnvelope`).
- `PublicLedgerEntry → Delegation` / `DelegationSnapshot` — forbidden (no
  `subject_type` value references either; see ADR-012's exclusion of
  `delegation-service` from this pack's dependency matrix entirely).
- `PublicLedgerEntry.published_by_role_id → public content` — forbidden
  verbatim (amended, Owner decision item 4); only an approved
  `replacement_label` (D3.3) may appear in any public-facing view.

### D3.2 — `AuditExportPackage`

Implements canon 5.11's "audit exports" line and directly operationalizes
INV-03's fourth legitimate integration mechanism, "специальный audit
export" (section 102–116) — a batched, hash-chain-provable export of
`epd2_audit_core`'s `AuditEvent` records, redacted for public
consumption.

**Canon-declared owner:** Audit Export Service (new section 22 row;
physically implemented inside `transparency-service`).

**Fields (amended, Owner decision item 1):**

- `audit_export_package_id` — UUID.
- `scope_description` — string, human-readable (e.g. "Ballot
  `<ballot_id>` full results audit export").
- `requested_by_role_id` — nullable UUID (`RoleAssignment` reference);
  null for scheduled/automatic exports, set for a manually-triggered one.
  **Amended (Owner decision item 4, extended for consistency):** internal
  governance data; never appears verbatim in public content.
- `included_target_types` — list of enum, drawn only from an explicit
  public-safe allow-list: `initiative`, `initiative_version`, `ballot`,
  `moderation_case`, `moderation_decision`, `result_publication`. Any
  `AuditEvent` whose `target_type` (canon 18.1) is not on this allow-list
  is never eligible for inclusion, regardless of who requests the export.
- `event_count` — integer, the number of underlying `AuditEvent` records
  the package attests to (a count, not the records themselves).
- `chain_proof` — **(amended)** an ordered list of structured proof-item
  objects, one per included `AuditEvent`, each containing:
  - `event_hash` — the source `AuditEvent`'s own `event_hash` (canon
    18.1), included verbatim as this position's public chain-continuity
    anchor.
  - `previous_event_hash` — the `event_hash` of the immediately preceding
    proof item in this exported segment (matching the prior item's own
    `event_hash`, forming the externally-checkable link between them).
  - `public_metadata` — an object containing only: `event_type`,
    `occurred_at`, `target_type`, `target_id`, `action`, `reason_code`,
    `correlation_id`, `source_service` — never `actor_id`, `actor_type`,
    `before_hash`, `after_hash`, `recorded_at`, or `policy_version` (see
    Verification semantics and Structural prohibition, below).
  - `sequence_position` — integer, the 0-based index of this item within
    the exported segment; contiguous, no gaps or duplicates, matching
    `event_count`.
- `package_digest` — **(new)** a SHA-256 hex digest computed over the
  canonical, deterministic serialization of the full ordered `chain_proof`
  array. Changes if any item is reordered, altered, added, or removed
  after export — lets a verifier confirm they received the package
  unmodified.
- `integrity_proof` — **(new)** nullable string: a reserved slot for a
  future cryptographic attestation (e.g. a detached signature over
  `package_digest` by a to-be-defined signing authority). **Not populated**
  by this pack's own implementation — no signing infrastructure exists
  yet, and introducing one is out of this pack's scope
  (`docs/handover/PACK-04-SPEC.md` section 13's "cryptographic proof
  beyond hash-chaining" exclusion). Present in the schema now so a future
  ADR can populate it without a breaking schema change.
- `generated_at` — timestamp.
- `redaction_notice` — string, mandatory (not nullable, unlike
  `PublicLedgerEntry`'s own field): a fixed, standard notice that
  `actor_id`, `actor_type`, `before_hash`, `after_hash`, and this
  package's own `requested_by_role_id` are always omitted from the
  package's public content — this field documents the redaction rule as
  data, not merely as this ADR's prose.
- `supersedes_package_id` — nullable UUID, set only when a package is
  reissued to fix an error in a prior package (the prior package is never
  edited in place).
- `status` — enum: `generated`, `published`, `superseded`.

**Verification semantics (new subsection, Owner decision item 1):** an
external verifier, given an `AuditExportPackage`, can independently
confirm:

1. **Chain continuity** — for every consecutive pair of items in
   `chain_proof`, the later item's `previous_event_hash` equals the
   earlier item's `event_hash`.
2. **Ordering/completeness** — `sequence_position` values are contiguous
   starting from the first exported item, with no gaps or duplicates,
   and their count equals `event_count`.
3. **Non-modification after export** — recomputing a digest over the
   received, ordered `chain_proof` array reproduces `package_digest`
   exactly; any reordering, insertion, deletion, or field alteration of
   any item after the package left `transparency-service` changes this
   digest and is therefore detectable.

An external verifier **cannot**, from this package alone, recompute the
original private `AuditEvent.event_hash` values from scratch —
`event_hash` (canon 18.1) is computed over that `AuditEvent`'s full
canonical field set, which includes fields this package deliberately
never surfaces (`actor_id`, `actor_type`, `before_hash`, `after_hash`,
and any field of a `target_type` not on the public-safe allow-list). This
package proves the **published segment's own continuity and integrity**;
it does not, and is not claimed to, provide independent proof of the
**private** `AuditEvent` records' own hash computation. Full audit of the
underlying private hash chain remains available only through
`epd2_audit_core`'s own "отдельные права чтения" (separate read
permissions, canon 18.1) — a different, non-public access path than this
package.

**Statuses and transitions:** `generated → published` (a package must be
generated before it is published — no direct creation-as-published);
`published → superseded` (only via a new package with
`supersedes_package_id` set, mirroring `PublicLedgerEntry`'s own
correction pattern). No transition ever returns to `generated`.

**Forbidden links:**

- `AuditExportPackage → AuditEvent.actor_id` / `actor_type` — forbidden
  in the package's own public content (see Structural prohibition,
  below) — a stricter rule than canon strictly requires (canon 7.4
  already scopes `Actor` per-context, not universally resolvable to a
  person), adopted here as the simpler, more auditable guarantee.
- `AuditExportPackage → AuditEvent.before_hash` / `after_hash` — forbidden
  outright, for every included event, not only `vote_envelope`- or
  `delegation`-targeted ones (amended: the original proposal scoped this
  prohibition only to those two `target_type` values; the revised
  `public_metadata` shape in the amended `chain_proof` above excludes
  `before_hash`/`after_hash` for every proof item unconditionally, which
  is simpler to audit and was already the practical effect once
  `included_target_types`' allow-list excludes `vote_envelope`/
  `delegation` entirely).
- `AuditExportPackage.requested_by_role_id → public content` — forbidden
  verbatim (amended, Owner decision item 4).
- `AuditExportPackage → непубличные персональные данные` — restating
  canon section 23's generic rule for this entity specifically.

### D3.3 — `DisclosurePolicy`

Not named anywhere in canon's existing text, but required as soon as any
entity above needs a documented, versioned, structural answer to "what
gets redacted before publication, and under what authority." Every
proposal in `docs/handover/PACK-04-SPEC.md` section 8 (aggregate-only
result counts, moderator-identity handling, small-cell suppression)
needs a place to live as governed, versioned data, not only as a
paragraph of specification prose.

**Canon-declared owner:** Disclosure Policy Service (new section 22 row;
physically implemented inside `transparency-service`).

**Fields (amended, Owner decision item 2):**

- `disclosure_policy_id` — UUID.
- `applies_to_subject_type` — enum, matching the union of
  `PublicLedgerEntry.subject_type` values plus `audit_export_package` and
  `lobby_log_entry` — one policy version governs exactly one subject
  type at a time.
- `field_rules` — **(replaces the original single `disclosure_class`
  field and loose `field_redaction_rules` list)** a JSON list of
  structured rule objects. Each rule object contains, at minimum:
  - `field_path` — string, a dot-path identifying the candidate field
    within the subject's content schema (e.g.
    `"moderation_decision.decided_by"`,
    `"result_publication.accepted_vote_count"`).
  - `disclosure_class` — enum: `public`, `redacted`, `restricted`,
    `prohibited` (ADR-015 defines these four classes precisely).
  - `transformation` — how the field's value is transformed before
    appearing in that class's output, e.g. `none` (verbatim), `generalize_to_role_scope`,
    `band_small_cell`, `suppress`, `hash`.
  - `replacement_label` — optional string, used only when `transformation`
    is a label-substitution (e.g. `generalize_to_role_scope`) — the
    fixed public-facing value shown in place of the real one (e.g.
    `"moderator"`).
- `small_cell_threshold` — integer; ADR-015's accepted default is `10`
  for public analytics/non-legally-required aggregate views, with an
  explicit exception (via a `none`-transformation `field_rules` entry,
  never an implicit assumption) for subject types where a formally
  required official record must disclose exact counts regardless of
  population size (e.g. `result_publication` — see D3.6 and ADR-015
  item 6).
- `effective_from` — timestamp.
- `approved_by_role_id` — UUID, **not** nullable — every `DisclosurePolicy`
  version requires an explicit, role-gated approval before it can become
  `active` (INV-08 separation-of-authority precedent, the same pattern
  ADR-009 item 7 already established for ballot configuration approval).
  **Amended (Owner decision item 4, extended for consistency):** internal
  governance data; never appears verbatim in public content.
- `version` — integer, monotonically increasing per `applies_to_subject_type`.
- `status` — enum: `draft`, `active`, `superseded`.

**Statuses and transitions:** `draft → active` (requires
`approved_by_role_id` to be set); `active → superseded` (only when a new
version for the same `applies_to_subject_type` becomes `active` — exactly
one `active` policy per `applies_to_subject_type` at any time). No
transition returns to `draft`.

**Validation semantics (amended, replaces "Forbidden links, and a
structural ceiling..."):** every candidate field of a subject_type's
publishable content (i.e., every field that survives the Structural
prohibition subsection's upstream exclusion) should be covered by
exactly one `field_rules` entry in the active `DisclosurePolicy` for that
subject_type — enforced as a validation goal at policy-authoring/
activation time. As a runtime fail-safe on top of that validation (not
instead of it), two failure modes are both treated identically: a
candidate field with **no** matching `field_rules` entry, and a candidate
field matched by **more than one** entry (ambiguous) — both default the
field to `prohibited` (excluded from any output), never erring toward
disclosure.

A `DisclosurePolicy`'s `field_rules` can only ever operate on fields that
already made it into the **candidate** content set for
`content_snapshot`/`chain_proof` construction (D3.1/D3.2) — and that
candidate set is itself constructed upstream with `account_id`,
`person_id`, `identity_record_id`, `participation_credential_id`,
`vote_envelope_id`, `encrypted_or_encoded_choice`, `credential_proof`,
and (amended, Owner decision item 4) `published_by_role_id`/
`requested_by_role_id`/`approved_by_role_id`/`submitted_by_role_id`
already structurally absent or non-reclassifiable (see the Structural
prohibition subsection below). This means a misconfigured or malicious
`DisclosurePolicy` can never be used to "un-redact" identity-, vote-, or
role-linked data into a public record — there is nothing to reveal,
because it was never eligible candidate data in the first place. This is
a stronger guarantee than "the policy correctly redacts sensitive
fields," which would still depend on the policy being configured
correctly; this design does not depend on that.

### D3.4 — `LobbyLogEntry`

Implements canon 5.11's explicit "lobbying log" line. Flagged, as
`docs/handover/PACK-04-SPEC.md` section 3 already flagged it, as the
entity with the weakest canon grounding of the four: canon's Organization
Context (5.4) owns "организация, подразделения, Civic Spaces, рабочие
группы, роли, членство, организационная структура" but has no concept of
an external lobbying actor or disclosure obligation. The schema proposed
here is deliberately minimal; real lobbying-actor registration is left to
a future Organization Context extension (`docs/handover/PACK-04-SPEC.md`
section 13).

**Canon-declared owner:** Lobby Log Service (new section 22 row;
physically implemented inside `transparency-service`).

**Fields:**

- `lobby_log_entry_id` — UUID.
- `submitted_by_role_id` — UUID, **not** nullable, a `RoleAssignment`
  reference (never an `Account`/`IdentityRecord`) — the authenticated
  role submitting on behalf of an external organization. **Amended
  (Owner decision item 4):** internal governance data; never appears
  verbatim in public content — a public view may expose only an approved
  `replacement_label` (D3.3).
- `organization_name` — string, mandatory, free text (explicitly not a
  canon `Organization` entity reference — see the grounding caveat above).
- `related_subject_type` — enum: `initiative`, `ballot`, `amendment`.
- `related_subject_id` — UUID, mandatory.
- `contact_date` — date, mandatory.
- `contact_method` — enum: `meeting`, `written_submission`, `call`,
  `other`.
- `topic_summary` — string, mandatory, free text.
- `submitted_at` — timestamp.
- `published_at` — nullable timestamp, set once published. **Amended:**
  per ADR-015's accepted default, no later than **7 calendar days**
  (amended down from a proposed 14) after `submitted_at`, with mandatory
  automated (not human) completeness/prohibited-field/disclosure-policy
  validation before publication — see ADR-015.
- `supersedes_entry_id` — nullable UUID, correction pattern identical to
  `PublicLedgerEntry`'s own (amended, see Statuses below).
- `status` — enum, see Statuses below.

**Mandatory fields (restated for ADR-015 cross-reference):**
`organization_name`, `related_subject_type` + `related_subject_id`,
`contact_date`, `topic_summary`, `submitted_by_role_id` — an entry
missing any of these is rejected at submission, never published
incomplete (`LOBBY_LOG_ENTRY_INCOMPLETE`, ADR-014).

**Statuses and transitions (amended, Owner decision item 3, extended for
consistency):** `submitted → published` is a genuine, one-time stored
transition (unlike `PublicLedgerEntry`, a `LobbyLogEntry` legitimately
starts in a pre-publication `submitted` state). Once `published`, the
entry's stored content, status, and metadata are **never mutated again**.
There is no stored `corrected` status. A correction is exclusively a new
`LobbyLogEntry` row with `supersedes_entry_id` set — never an edit of the
original entry, mirroring D3.1's rule exactly. Whether a published entry
has since been corrected is likewise a derived, query-time fact, never
written back onto the original row.

**Forbidden links:**

- `LobbyLogEntry → IdentityRecord` / `Account` of the submitting natural
  person — forbidden. `submitted_by_role_id` references a `RoleAssignment`
  only; the entry's own public content is the organization's declared
  identity (`organization_name`), which is the intended public fact, not
  the submitting individual's private identity.
- `LobbyLogEntry.submitted_by_role_id → public content` — forbidden
  verbatim (amended, Owner decision item 4).

### D3.5 — AI transparency: publication only, no AI-processing implementation

Canon 5.11 lists "журналы ИИ" (AI logs) among the Transparency Context's
responsibilities. This ADR proposes representing that responsibility
**exclusively** as a publication capability, never as AI-processing
implementation:

- `PublicLedgerEntry.subject_type` includes `ai_processing_record` as a
  fifth, currently-dormant value (D3.1).
- This value may only ever be used to publish a redacted summary of an
  **already-existing** `AIProcessingRecord` (canon 17.1, owned by "AI
  Accountability Service" per canon section 22, out of PACK-04's scope
  entirely).
- This pack creates, mutates, requires, or depends on **no**
  `AIProcessingRecord`. If no future pack ever implements the AI
  Accountability Service, `subject_type = "ai_processing_record"` simply
  never has any rows — a structurally guaranteed, not merely documented,
  consequence of ADR-012 excluding any dependency on an AI-processing
  service.
- CT-00-11 (AI Human Control) therefore remains a genuine **not-applicable**
  marker for this pack, exactly as `docs/handover/PACK-04-SPEC.md` section
  1 already concluded — this subsection exists to make the reasoning
  canon-level and explicit, not to reverse that conclusion.

### D3.6 — `PublicLedgerEntry`'s relationship to `Initiative`, `InitiativeVersion`, `ModerationDecision`, `ResultPublication`, and `AuditEvent`

- **`Initiative`** (canon 11.1): a `PublicLedgerEntry` with
  `subject_type = "initiative"` is created when `Initiative.status`
  reaches `published` (existing canon status), triggered by the already-
  canonical `initiative.published` event (canon 20.6). `content_snapshot`
  is a redacted copy of that `Initiative`'s public fields at the moment
  of publication — never a live reference that could silently diverge
  from the historical record as the source `Initiative` later changes
  (INV-05).
- **`InitiativeVersion`** (canon 11.2): a `PublicLedgerEntry` with
  `subject_type = "initiative_version"` is created per new published
  version, triggered by `initiative.version_created` (canon 20.6),
  directly implementing canon 5.11's "история версий" (version history)
  line.
- **`ModerationDecision`** (canon 14.2): a `PublicLedgerEntry` with
  `subject_type = "moderation_decision"` is created when a decision is
  issued or enforced (`moderation.decision_issued` /
  `moderation.decision_enforced`, canon 20.9), implementing canon 5.11's
  "журналы модерации" line. **Amended (resolves the item this text
  previously left open, per ADR-015 item 5):** `content_snapshot` never
  includes the reviewer's `actor_id`, `RoleAssignment` UUID, or any
  personal/account/identity reference; only a generalized role-scope
  label (e.g. `"moderator"`) is exposed as `decided_by`'s public
  representation. Full reviewer information remains `restricted`-class,
  available only to authorized audit/oversight roles, never part of any
  `public`-class `PublicLedgerEntry` content.
- **`ResultPublication`** (canon 15.6): a `PublicLedgerEntry` with
  `subject_type = "result_publication"` is created when `result.published`
  fires (canon 20.10). `content_snapshot` is restricted to exactly the
  aggregate fields ADR-009 item 15 already scoped (`eligible_count`,
  `credential_count`, `accepted_vote_count`, `rejected_vote_count`,
  `quorum_result`, `threshold_result`, `challenge_deadline_at`) — never
  `Tally.result_data`'s internal representation if it differs, and never
  any `VoteEnvelope` content, per D3.1's forbidden links. **This
  subject_type is exempt from small-cell suppression/banding** (ADR-015
  item 6): the formally required official result must disclose its exact
  aggregate counts regardless of population size; small-cell banding
  applies instead to any separate, non-legally-required aggregate
  analytics views this pack may offer, never to this canonical ledger
  entry itself. This distinction must be recorded as an explicit
  `none`-transformation `field_rules` entry for this subject_type
  (D3.3), not left implicit.
- **`AuditEvent`** (canon 18.1): related but distinct from
  `PublicLedgerEntry` in what each attests to. Every `PublicLedgerEntry`
  publication (or correction) is itself one of INV-04's explicitly
  audit-required actions — "публикация" and "снятие с публикации" both
  appear by name in INV-04's list — so creating a `PublicLedgerEntry`
  always also creates an ordinary (non-public) `AuditEvent` in
  `epd2_audit_core`, exactly like every other PACK-02/03 write.
  `AuditExportPackage` (D3.2) is a separate, coarser mechanism: it
  packages a range of _already-existing_ `AuditEvent` records (including
  the ones documenting `PublicLedgerEntry` publication itself) into a
  publicly verifiable, redacted proof of chain continuity and integrity
  (D3.2's Verification semantics). In short: `PublicLedgerEntry`
  publishes **content**; `AuditExportPackage` publishes **proof that the
  published segment's own process was followed correctly** — not proof
  of the underlying private `AuditEvent` hash computation itself. Neither
  substitutes for the other, and both are required by this pack's
  Definition of Done (`docs/handover/PACK-04-SPEC.md` section 12).

### Structural prohibition (applies to all four entities)

- No schema for any of the four entities above may declare a field
  named, or aliased to, `account_id`, `person_id`, `identity_record_id`,
  `participation_credential_id`, `vote_envelope_id`,
  `encrypted_or_encoded_choice`, or `credential_proof` — extending the
  existing `FORBIDDEN_FIELD_NAMES` set CT-00-08/09 already enforce
  elsewhere in this repository to cover these four new entities.
  `additionalProperties: false` JSON Schemas (once implementation begins)
  plus the same forbidden-field-name structural test pattern must be
  applied here exactly as they were for every PACK-02/03 entity.
- **(Amended, Owner decision item 4)** `published_by_role_id` (D3.1),
  `requested_by_role_id` (D3.2), `approved_by_role_id` (D3.3), and
  `submitted_by_role_id` (D3.4) — all four `RoleAssignment` references
  are internal governance data. None may appear verbatim (as a raw UUID)
  in any public-facing content, view, or export this pack produces.
  Where a public view needs to convey "who acted in what capacity," it
  may show only an approved, generalized role-scope `replacement_label`
  (D3.3's `field_rules`), never the underlying `RoleAssignment` id
  itself. (The owner's decision names `published_by_role_id`/
  `submitted_by_role_id` explicitly; the identical rule is extended here
  to `requested_by_role_id`/`approved_by_role_id` for consistency, as the
  same category of internal reference for the same reason.)
- `AuditExportPackage` additionally must never surface `AuditEvent.actor_id`,
  `actor_type`, `before_hash`, or `after_hash` in its own public content,
  for any included event (D3.2, amended).
- A positive-space regression test (mirroring PACK-02/03's own "prove no
  code path resolves X to Y" pattern, e.g.
  `test_identity_service_paths_may_reference_identity_record_id`) must be
  written once implementation begins, proving no code path can resolve
  any `PublicLedgerEntry`, `AuditExportPackage`, or `LobbyLogEntry` back
  to an `Account`, a `VoteEnvelope`, or a raw `RoleAssignment` id in
  public output — not merely that no field exists for it.

### Proposed Transparency event catalog (new canon section 20.14)

None of the following events exist in canon today (canon sections
20.1–20.13 have no Transparency entries — `docs/handover/PACK-04-SPEC.md`
section 2's canon-silence finding). Proposed, accepted per this ADR:

`transparency.ledger_entry_published`, `transparency.ledger_entry_corrected`,
`transparency.audit_export_generated`, `transparency.audit_export_published`,
`transparency.disclosure_policy_defined`, `transparency.disclosure_policy_activated`,
`transparency.disclosure_policy_superseded`, `transparency.lobby_log_entry_submitted`,
`transparency.lobby_log_entry_published`, `transparency.lobby_log_entry_corrected`.

Every event would use canon section 21's envelope verbatim (the same
shape every prior pack's events already use) — no new envelope field, no
relaxed idempotency rule. `transparency.ledger_entry_corrected` and
`transparency.lobby_log_entry_corrected` fire when a **new**, superseding
entry is created (D3.1/D3.4, amended) — never when an existing row is
mutated, since no such mutation exists in the amended design.

### Proposed section 22 (ownership matrix) additions

| Entity               | Proposed canon-declared owner |
| -------------------- | ----------------------------- |
| `PublicLedgerEntry`  | Public Ledger Service         |
| `AuditExportPackage` | Audit Export Service          |
| `DisclosurePolicy`   | Disclosure Policy Service     |
| `LobbyLogEntry`      | Lobby Log Service             |

Four new rows in canon section 22's 27-row matrix, bringing it to 31.
ADR-011 proposes all four physically implemented inside one
`services/transparency-service`, the same "module ≠ physical service"
relationship every prior consolidated service in this repository already
has.

## Consequences

Once the separate, dedicated canon-edit task (Owner decision, above) is
carried out, `docs/canonical/TZ-00-domain-event-canon.md` will gain: a
new `## 11a` (or equivalently numbered) entity section for each of the
four entities above with their fields/statuses/forbidden-links exactly
as specified in D3.1–D3.4 (as amended); a new `## 20.14. Transparency`
event catalog subsection; four new rows in section 22's ownership matrix;
and the forbidden-link entries in section 23 extended per D3.1/D3.2's
specific additions. `canon_version` would move `0.2.0 → 0.3.0`, mirrored
in `docs/canonical/canon-version.json`,
`packages/python/epd2-core/src/epd2_core/version.py`, and
`packages/typescript/epd2-types/src/version.ts`, exactly as ADR-010
performed its own `0.1.0 → 0.2.0` bump. **None of this was performed by
this ADR's acceptance itself** — per that task's explicit instruction,
the canon edit was deferred to a separate, dedicated follow-on task,
mirroring ADR-010's own precedent (propose in full, accept, then edit
canon as its own reviewed step) — the difference being that acceptance
and the canon edit were two distinct, separately-instructed tasks rather
than performed together. **That follow-on task has since been carried
out** — see "Canon implementation," above, for the resulting checksum
and version.

## Security impact

This ADR's entire purpose is to define a public-disclosure data model
without weakening CT-00-08/09. The Structural prohibition subsection is
the load-bearing security control: every one of the four entities'
candidate content is constructed with identity/credential/vote/role-
reference fields already absent or non-reclassifiable, not merely
redacted after the fact. The amendments (Owner decision) strengthen this
further: `AuditExportPackage`'s corrected verification semantics prevent
an overclaimed guarantee (recomputing private hashes) from being relied
upon; `DisclosurePolicy`'s structured `field_rules` close the "no rule
matched" ambiguity that a loose rule list could have left open; and
`PublicLedgerEntry`/`LobbyLogEntry`'s immutability-from-creation rule
removes any code path that could ever mutate already-published content in
place.

## Data impact

Four new canonical entities, ten new canonical events, four new
ownership-matrix rows, and an extension of section 23's forbidden-links
list. No existing canonical entity's fields, statuses, or owner change —
this is purely additive, satisfying canon section 25's own definition of
a minor version. `ResultPublication`, `Initiative`, `InitiativeVersion`,
`ModerationDecision`, and `AuditEvent` are all **read**, never modified,
by anything this ADR proposes.

## Migration impact

None — no `services/transparency-service` exists yet (only the canon
content itself has been added, per "Canon implementation," above). Once
implemented, no PACK-02/03 entity requires backfill or migration; the
four new entities start empty and are populated only going forward from
first publication.

## Reversibility

Reversible with cost before code exists (this stage). Once real
`PublicLedgerEntry`/`AuditExportPackage`/`LobbyLogEntry` records exist and
have been publicly disclosed, removing or renaming a field becomes a
major-version-equivalent change under canon section 25 ("изменение
обязательного поля"), the same reversibility profile every other
canonical entity has once real data exists under it — and arguably higher
cost here, since these records are, by design, public and potentially
already referenced externally once published. The amended immutability
rule (D3.1/D3.4) makes this an especially firm commitment: once a row is
written, no future implementation may ever add a code path that writes to
it again.

## Related canon version

Authored against canon version `0.2.0`. Accepted with amendments per
Owner decision, above; the corresponding canon edit to `0.3.0` has since
been performed as its own follow-on task — see "Canon implementation,"
above. This is the largest single canon addition this project has made
to date.
