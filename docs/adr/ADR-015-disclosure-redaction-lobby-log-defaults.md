# ADR-015: Disclosure, redaction, public audit export, and Lobby Log defaults (PACK-04)

## Status

`accepted`, with amendments to the Lobby Log publication timing and
resolution of the two previously-open items (moderator/reviewer
identity, small-cell threshold), plus adoption of ADR-013's corrected
audit-proof verification semantics (see Owner decision, below).

## Date

2026-07-23

## Owner decision

Accepted with amendments, 2026-07-23:

1. The four disclosure classes and the non-overridable `prohibited`
   class (Decision, Disclosure classes) — accepted as proposed, no
   amendment.
2. Separation-of-authority and versioned policy changes (Redaction
   approval and override rules) — accepted as proposed, no amendment.
3. Lobby Log mandatory fields — accepted as proposed, no amendment.
4. Lobby Log publication timing — **amended**: 14 → **7** calendar days;
   no mandatory human pre-publication review by default; **mandatory
   automated** completeness, prohibited-field, and disclosure-policy
   validation before publication is now required (not merely implied by
   the original text); corrections remain possible only through a new
   superseding entry, now explicitly cross-referenced to ADR-013 D3.4's
   amended immutability rule.
5. Moderator and appeal reviewer identity — **resolved** (previously
   open item 1): publish only a generalized role-scope label; never a
   personal name, `actor_id`, `RoleAssignment` UUID, account reference,
   or identity reference; full reviewer information remains restricted
   to authorized audit and oversight access only.
6. Small-cell threshold — **resolved** (previously open item 2): `n = 10`;
   values 1 through 9 shown banded as `"1–9"` for public analytics and
   non-legally-required aggregate views; `0` shown exactly; the formally
   required official `ResultPublication` ledger entry is exempt from
   suppression/banding and must disclose exact counts regardless of
   population size; this distinction is now recorded explicitly in
   `DisclosurePolicy` field rules (ADR-013 D3.3, as amended).
7. Public audit proof — the integrity semantics in this ADR are
   corrected to match ADR-013's amended D3.2/Verification-semantics
   text; this ADR's own earlier claim that "an external verifier can
   recompute and confirm the hash chain independently" is **withdrawn**
   and replaced throughout this document.

No canon edit is performed by this acceptance — this ADR was never
itself a canon-editing proposal (Related canon version, below); its
content governs policy fields ADR-013 proposes adding to canon, and
takes effect only once ADR-013's own canon content is actually written
into the canon document, a separate task not yet performed. Canon
`0.2.0` remains unchanged.

## Context

ADR-013 proposes four Transparency entities but deliberately left their
governing policy content undecided at the canon/entity-definition level —
`DisclosurePolicy`'s field-level rules, `small_cell_threshold`, and
`LobbyLogEntry`'s exact publication timing were all fields whose _shape_
ADR-013 defines but whose _values_ are a policy question, not a schema
question. This ADR is that policy proposal, in the same spirit as
ADR-009's section-29 defaults for PACK-03: conservative, fail-closed
proposals for the project owner's review. Two items were originally
presented as fully open questions this ADR did not default, per the
task's instruction not to silently pick an answer where the underlying
tradeoff was genuinely the owner's to weigh — both are now resolved
(Owner decision, above).

## Problem

Without an explicit disclosure-classification scheme, "public," "OK to
redact," and "never publishable" have no shared vocabulary across the
four ADR-013 entities, `transparency-service`'s implementation, and
future contract tests — each would otherwise be decided ad hoc per field,
per entity, with no single place recording the classification rule or who
approved it (INV-08's separation-of-authority concern, applied here to
disclosure decisions rather than ballot configuration).

## Considered options

- Option A — define four disclosure classes (`public`, `redacted`,
  `restricted`, `prohibited`) as a fixed vocabulary every
  `DisclosurePolicy` (ADR-013 D3.3) must classify its subject's fields
  into, with `prohibited` fields structurally unable to enter the
  candidate content set at all (ADR-013's Structural prohibition
  subsection, not merely policy-enforced).
- Option B — a binary public/non-public classification only, simpler but
  unable to express "redacted-but-still-published-in-generalized-form"
  (e.g. a moderator's role-scope label without their specific `Actor`
  reference) versus "restricted to authorized readers only, never fully
  public" (e.g. an internal completeness note on why an initiative was
  sent back for revision, useful to the initiative's own submitter but
  not to the general public).
- Option C — no fixed vocabulary; each `DisclosurePolicy` instance defines
  its own ad hoc classification scheme per subject type.

## Decision

Option A, accepted as proposed (Owner decision item 1). Four disclosure
classes, applied uniformly across all four ADR-013 entities:

### Disclosure classes

1. **`public`** — visible to anyone, no authentication required. Example:
   `PublicLedgerEntry.content_snapshot`'s non-redacted fields, a
   published `LobbyLogEntry`'s full content, an `AuditExportPackage`'s
   `chain_proof`, `package_digest`, and `redaction_notice`.
2. **`redacted`** — derived from non-public source data but published in
   a generalized, non-reversible form. Example: a `ModerationDecision`
   ledger entry's reviewer field, generalized to a role-scope label
   rather than the specific `Actor`/`RoleAssignment` reference (item 5,
   resolved below).
3. **`restricted`** — accessible only to an authenticated, role-gated
   reader (e.g. the initiative's own submitter, an auditor role), never
   published to the general public. Example: full,
   un-redacted `ModerationDecision` detail, made available to the
   decision's own subject but not to the general public ledger.
4. **`prohibited`** — never enters any publication artifact this pack
   produces, under any role or authorization. This is not merely a
   policy setting — per ADR-013's Structural prohibition subsection, the
   fields in this class (`account_id`, `person_id`, `identity_record_id`,
   `participation_credential_id`, `vote_envelope_id`,
   `encrypted_or_encoded_choice`, `credential_proof`, `AuditEvent.actor_id`/
   `actor_type`/`before_hash`/`after_hash` in export context, and the
   four internal `*_role_id` references — ADR-013 Owner decision item 4)
   are structurally excluded from the candidate content set before any
   `DisclosurePolicy` is even consulted. A `DisclosurePolicy` cannot
   reclassify a `prohibited` field into any other class — this is a
   ceiling no policy version, however approved, may raise.

Every candidate field of every ADR-013 entity's publishable content must
be assigned exactly one of these four classes by the active
`DisclosurePolicy`'s `field_rules` for its `applies_to_subject_type`
(ADR-013 D3.3, as amended); a field with no assigned class, or an
ambiguous (more than one) assignment, defaults to `prohibited`
(fail-closed, INV-10).

### Redaction approval and override rules

Accepted as proposed (Owner decision item 2), no amendment:

- A `DisclosurePolicy` moves `draft → active` only with
  `approved_by_role_id` set (ADR-013 D3.3) — a role distinct from the
  role that authored the draft, mirroring ADR-009 item 7's separation-of-
  authority pattern for ballot configuration approval.
- No override of a `prohibited` classification is possible by any role,
  including the approving role itself — this is the one classification
  this ADR treats as non-negotiable at the policy layer (see Disclosure
  classes, item 4).
- An override from `restricted` to `public` (i.e. making previously
  restricted content fully public) requires a **new** `DisclosurePolicy`
  version, approved the same way as any other version change — never an
  in-place mutation of an existing policy's `field_rules` (INV-05).
- Redaction is applied at `PublicLedgerEntry`/`LobbyLogEntry` construction
  time (ADR-013 D3.1/D3.4), using whichever `DisclosurePolicy` version was
  `active` at that moment — a later policy change does not retroactively
  alter already-published `content_snapshot` values (INV-05); it only
  governs future publications, consistent with `PublicLedgerEntry`'s own
  correction-as-new-entry pattern (ADR-013 D3.1, amended) being the only
  way to change what was already shown.

### Lobby Log mandatory fields and publication timing

**Mandatory fields** — accepted as proposed (Owner decision item 3), no
amendment (restated for cross-reference): `organization_name`,
`related_subject_type` + `related_subject_id`, `contact_date`,
`topic_summary`, `submitted_by_role_id`. An entry missing any of these is
rejected at submission with `LOBBY_LOG_ENTRY_INCOMPLETE` (ADR-014) — never
published incomplete and backfilled later.

**Publication timing (amended, Owner decision item 4):** a submitted
`LobbyLogEntry` is published no later than **7 calendar days** after
`submitted_at` — amended down from the originally proposed 14-day
default. There is no mandatory _human_ pre-publication review step by
default (a `DisclosurePolicy` for `applies_to_subject_type =
"lobby_log_entry"` may add one). What **is** mandatory, and was only
implied rather than stated outright in the original proposal: before
publication, `transparency-service` must run **automated validation**
covering (a) completeness — every mandatory field present, else
`LOBBY_LOG_ENTRY_INCOMPLETE`; (b) prohibited-field absence — a defensive
check that no structurally-forbidden field (ADR-013's Structural
prohibition subsection) is present, even though this should already be
impossible upstream; and (c) conformance to the active `DisclosurePolicy`'s
`field_rules` for `lobby_log_entry`, else `DISCLOSURE_POLICY_VIOLATION`.
Corrections remain possible only through a new, superseding
`LobbyLogEntry` (ADR-013 D3.4's amended correction rule) — never an edit
of the original entry.

### Public audit proof (revised, adopts ADR-013's amended semantics — Owner decision item 7)

An `AuditExportPackage`'s public `chain_proof` (ADR-013 D3.2, as amended)
is an ordered list of structured proof items, each containing
`event_hash`, `previous_event_hash`, public-safe `public_metadata`
(`event_type`, `occurred_at`, `target_type`, `target_id` restricted to
the allow-list, `action`, `reason_code`, `correlation_id`,
`source_service`), and `sequence_position` — plus a package-level
`package_digest` and reserved `integrity_proof` field (ADR-013 D3.2).

This lets an external verifier confirm **chain continuity, ordering, and
non-modification of the exported segment** (ADR-013 D3.2's Verification
semantics). It does **not** let a verifier recompute the original,
private `AuditEvent.event_hash` values from scratch, since those are
computed over fields (`actor_id`, `actor_type`, `before_hash`,
`after_hash`) this package never surfaces. **This ADR's original text
claimed** that the chosen field set was "exactly what is needed to let an
external verifier recompute and confirm the hash chain independently" —
**that claim is withdrawn.** It conflated two different guarantees (proof
that the public segment itself is intact, versus recomputation of a
private hash from public inputs) that ADR-013's amended D3.2 now keeps
explicitly distinct. ADR-013 D3.2's "Verification semantics" subsection
is the operative text on this topic going forward; this section restates
it here only for this ADR's own internal consistency.

### What is never publicly publishable (summary, cross-referencing the four entities)

- Any `account_id`, `person_id`, or `identity_record_id`, in any form, in
  any of the four ADR-013 entities' public content.
- Any `VoteEnvelope`, `VoteReceipt`, or `ParticipationCredential` content
  or reference, in full or redacted form — `result_publication` ledger
  entries carry only `ResultPublication`'s own pre-existing aggregate
  fields (ADR-013 D3.6), never anything derived from individual envelopes.
- Any `Delegation`/`DelegationSnapshot` content or reference (ADR-012's
  dependency-matrix exclusion makes this a structural impossibility, not
  merely a policy choice).
- `AuditEvent.actor_id`/`actor_type`/`before_hash`/`after_hash` in any
  `AuditExportPackage`'s public content (see Public audit proof, above).
- Any `published_by_role_id`, `requested_by_role_id`,
  `approved_by_role_id`, or `submitted_by_role_id` value in raw form —
  these are internal governance references; only an approved
  `replacement_label` may appear publicly (ADR-013 D3.1–D3.4, Owner
  decision item 4).
- A personal name, `actor_id`, `RoleAssignment` UUID, account reference,
  or identity reference for a moderation/appeal reviewer — only a
  generalized role-scope label may appear (item 5, resolved below).
- Any field a `DisclosurePolicy` has not explicitly assigned a class to
  via `field_rules`, or that has more than one ambiguous assignment —
  silence or ambiguity defaults to `prohibited`, never to `public`
  (fail-closed, INV-10).

## Moderator and appeal reviewer identity (resolved — Owner decision item 5)

Publish only a generalized role-scope label (e.g. `"moderator"`,
`"appeal reviewer"`). **Never** publish a personal name, `actor_id`,
`RoleAssignment` UUID, account reference, or identity reference of any
kind for the deciding/reviewing actor. Full reviewer information (the
actual `decided_by`/`reviewer_actor_id` value) remains available only
through `restricted`-class access to authorized audit and oversight
roles — never through any `public`-class `PublicLedgerEntry` content.
This was previously left open in this ADR's original text; ADR-013 D3.6
has been updated to state this as the operative rule, not a pending
default.

## Small-cell / low-count suppression threshold (resolved — Owner decision item 6)

`DisclosurePolicy.small_cell_threshold` (ADR-013 D3.3) is set to **n =
10** for public analytics and non-legally-required aggregate views: any
true count from 1 through 9 is shown banded as `"1–9"`; zero (`0`) is
shown exactly (zero carries no re-identification risk, since there is no
individual to distinguish among an empty set). This suppression/banding
rule does **not** apply to the formally required official
`ResultPublication`-derived `PublicLedgerEntry` (`subject_type =
"result_publication"`, ADR-013 D3.6) — that ledger entry must disclose
its exact aggregate counts regardless of population size, since the
official result is required to be exact, not banded. This distinction —
banded for analytics, exact for the official record — must be recorded
explicitly as two different `field_rules` transformations (`band_small_cell`
vs. `none`) in the relevant `DisclosurePolicy` versions for their
respective `applies_to_subject_type` values (ADR-013 D3.3), never left as
an implicit assumption.

## Consequences

Every `DisclosurePolicy` version (ADR-013 D3.3, as amended) must classify
each candidate field using exactly these four classes via structured
`field_rules`; `transparency-service`'s publication logic checks this
classification before constructing any `content_snapshot`/`chain_proof`,
on top of (not instead of) ADR-013's own structural field exclusion.
`contracts/reason-codes/pack-04.yml` (ADR-014)'s
`DISCLOSURE_POLICY_VIOLATION` and `REDACTION_REQUIRED` codes are the
enforcement mechanism for a publish attempt that does not respect an
active policy's classifications. The Lobby Log 7-day/automated-validation
rule and the two now-resolved items (moderator identity, small-cell
threshold) all become concrete, testable acceptance criteria for
`transparency-service`'s eventual implementation and its CT-00 contract
tests, rather than open design questions carried into that phase.

## Security impact

This ADR is the disclosure/redaction control surface CT-00-08 (Identity
Leakage) is verified against for this pack specifically. The
non-overridable `prohibited` class (Disclosure classes, item 4) remains
the single most important security property this ADR states: no policy,
however approved, can move a structurally-excluded field back into
publishable content. Resolving the two previously-open items (moderator
identity, small-cell threshold) removes two places where an
implementation could otherwise have made an ad hoc, unreviewed choice
under time pressure; withdrawing the overclaimed "full recomputation"
audit-proof language (item 7) prevents a future consumer of
`AuditExportPackage` from relying on a guarantee this pack does not
actually provide.

## Data impact

No new canonical entity — this ADR only assigns policy content and
concrete defaults to fields ADR-013 proposes on `DisclosurePolicy` and
`LobbyLogEntry`. If ADR-013 is ever superseded or materially re-amended,
this ADR would need to be revisited in step.

## Migration impact

None — no `transparency-service` or `DisclosurePolicy` record exists yet.

## Reversibility

The four-class vocabulary itself is cheap to amend before any policy
version exists under it. Once real `DisclosurePolicy` versions and
published content exist, narrowing a class (e.g. moving a field from
`public` to `restricted`) is straightforward going forward but cannot
retroactively un-publish already-published `content_snapshot` values
(INV-05) — only stop further disclosure of the same kind going forward.
The 7-day Lobby Log window and `n = 10` small-cell threshold are ordinary
configuration values on future `DisclosurePolicy` versions and can be
changed by a new version without any structural change to this ADR.

## Related canon version

Authored against canon version `0.2.0`. Proposes no canon change directly
— this ADR is a policy-content proposal governing fields ADR-013
proposes adding to canon; it does not itself touch canon text, and its
acceptance does not perform or authorize any canon edit on its own (that
remains gated on ADR-013's own separate canon-edit task).
