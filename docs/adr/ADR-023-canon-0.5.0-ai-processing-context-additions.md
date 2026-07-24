# ADR-023: Canon 0.5.0 — AI Processing Context field, status, and event additions

## Status

`accepted`, with amendments making `RedactionManifest` a canonical
embedded value object and adding disclosure-lifecycle fields and a
derived `DisclosureStatus` (see Owner decision, below).

## Date

2026-07-24

## Owner decision

Accepted with amendments, 2026-07-24. Items 1 and 2 below are accepted
exactly as drafted, no change. Items 3 and 4 are new amendments, now
incorporated directly into this ADR's own Decision text (D4a, D6, D7
below):

1. **The independent `processing_status` lifecycle** (D2) —
   `requested`, `input_prepared`, `processing`, `completed`, `failed`,
   `rejected_by_policy` — is accepted exactly as drafted.
2. **Immutable replacement through `supersedes_ai_processing_record_id`**
   (D3) is accepted exactly as drafted — older processing records are
   never mutated to mark them superseded; supersession is always a new
   row plus a derived, query-time fact.
3. **`RedactionManifest` is now canon-shaped, not an implementation-time
   choice.** The original draft (via ADR-025 §1) left `RedactionManifest`'s
   physical representation ("embedded value vs. separate storage row")
   open. This is now resolved: `RedactionManifest` is defined as an
   **immutable, embedded value object within `AIProcessingRecord`
   itself** — not a separate entity, and not an implementation detail
   deferred past this ADR. Its field list is fixed by this ADR (D4a,
   below), replacing the flat `redaction_policy_reference`/
   `redaction_applied` field pair the original draft proposed.
4. **Disclosure-lifecycle fields are added to `AIProcessingRecord`**:
   `disclosure_required`, `disclosure_package_reference`,
   `disclosure_receipt_reference`, plus a derived, non-stored
   `DisclosureStatus` read-model (D7, below) — grounding ADR-025's
   revised, explicit disclosure protocol (ADR-025 §5, this same
   acceptance round) in real `AIProcessingRecord` fields rather than an
   informal orchestration convention.

**Per this task's explicit instruction, canon `0.4.0` is not edited as
part of this acceptance.** This ADR reaching `accepted` status
authorizes the canon content described in D1–D7 (as now amended) to be
added to `docs/canonical/TZ-00-domain-event-canon.md` in a separate,
dedicated, later task, mirroring ADR-010/013/018's own precedent — that
edit has **not** been performed here. Canon checksum and `canon_version`
remain unchanged at `0.4.0` as of this acceptance. Implementation of
`ai-processing-service` itself is likewise a separate, later task, not
authorized by this acceptance alone.

## Canon implementation (2026-07-24, follow-on task)

The dedicated canon-edit task referenced above has now been carried out,
as its own separate task following this ADR's (and ADR-025's)
acceptance. Canon section 19c ("ИИ-обработка — расширение / AI
Processing Context") now extends the already-canon-defined
`AIProcessingRecord` (17.1, twelve existing fields and six-value
`human_review_status` both unchanged) exactly as specified in D1–D7
below, including both Owner-decision amendments (the canonical embedded
`redaction_manifest` value object, D4a; and the disclosure-lifecycle
fields plus derived `DisclosureStatus`, D6/D7). Section 19c.1 records
the new `processing_status` field (D2) and clarifies `human_review_status`
(D1) without modifying it; section 19c.2 records the unified
`supersedes_ai_processing_record_id` mechanism (D3); section 19c.3
records the fifteen further fields (D4); section 19c.4 records
`redaction_manifest` (D4a); section 19c.5 records the disclosure-
lifecycle fields and `DisclosureStatus` (D6/D7); section 19c.6 records
`AIDisclosurePackage` as a contract/value object (ADR-025's own D6/D7
cross-reference and ADR-025 §5); section 19c.7 records the mandatory
five-step disclosure protocol (ADR-025 §5); section 19c.8 records the
consequential-use boundary (ADR-025 §2); section 19c.9 closes with the
structural-separation note and the invariant list (no autonomous
decision, no identity reverse lookup, no vote-linkage reconstruction, no
model-provider mutation authority, no raw private input in disclosure,
no hidden-reasoning claim). Section 20.12's AI event catalog is
corrected (`ai.output.corrected` → `ai.output_corrected`, D5) and gains
six new events; section 22 gains no new ownership-matrix row
(`AIProcessingRecord`'s existing ownership is unchanged); section 23
gains the new forbidden-link entries above. `canon_version` moved
`0.4.0 → 0.5.0`:

```text
sha256(docs/canonical/TZ-00-domain-event-canon.md) =
  374b25fddfab88846622bf078b35c4246d8ad8c5d65bf43e6ac4e82653f74f74
CANON_VERSION = 0.5.0
```

This is a canon-only change: no `services/ai-processing-service`
directory, JSON Schema, OpenAPI file, or reason-code registry was
created, and no PACK-02/03/04/05 source code was touched.
`ai-processing-service` implementation remains a separate, later task,
gated on this canon content but not authorized by it alone.

## Context

`docs/handover/PACK-06-SPEC.md` sections 2, 3, and 6 document that canon
already defines `AIProcessingRecord` (17.1, twelve fields, a six-value
`human_review_status` enum) and an explicit AI allow/forbid list
(INV-07), but has no processing-pipeline status, no model-governance/
provenance/explainability/redaction fields, an inconsistent event name
(`ai.output.corrected`), and two `human_review_status` values with no
corresponding event (`approved`, `superseded`). Section 6 presented the
one genuine design tension this specification found — how a proposed
processing-pipeline lifecycle relates to the already-canonical
`human_review_status` — as an explicit two-option choice rather than
silently resolving it. This ADR records the project owner's decision on
every open item section 6, 3, 2, and 14 raised, and, in this round, makes
`RedactionManifest` and the disclosure-lifecycle fields canon-shaped
rather than implementation deferred.

## Problem

Without this ADR, `ai-processing-service` (ADR-021) would have no
canon-authoritative field set to implement against, no processing-
pipeline status distinct from the review-outcome status, and would
either have to invent one ad hoc (violating canon section 26) or wait
indefinitely. Left unresolved, the user's own originally-requested
ten-value lifecycle would also risk being implemented as a literal
replacement for `human_review_status` — a **major**, not minor, canon
change under section 25, and lossy. Separately, leaving
`RedactionManifest`'s shape and the disclosure protocol's data model as
implementation-time choices would let two different `ai-processing-
service` implementations diverge on exactly the fields this pack's
central safety and transparency guarantees depend on.

## Considered options

- Option A — add a new, orthogonal `processing_status` field scoped only
  to the technical-pipeline dimension; leave `human_review_status`
  completely untouched. Minor canon change.
- Option B — fold the user's full ten-value list into one field,
  replacing `human_review_status`. Major change under canon section 25;
  not authorized here.

## Decision

**Option A, accepted by the project owner**, with the refinements already
recorded in ADR-023's original draft (no stored `processing_status.
superseded` value; a unified `supersedes_ai_processing_record_id` field
instead) **and the two further amendments above (RedactionManifest
canonicalization; disclosure-lifecycle fields), now part of this ADR's
own Decision text.**

### D1 — `human_review_status`: unchanged, semantics clarified

**Canon 17.1's six-value `human_review_status` enum is not modified.**
`not_required`, `pending`, `approved`, `approved_with_changes`,
`rejected`, `superseded` remain exactly as canon already defines them —
no value added, removed, or renamed.

- **`superseded`'s exact semantics.** `human_review_status` reaches
  `superseded` on an existing `AIProcessingRecord` row **only** when a
  new `AIProcessingRecord` row is created with its own
  `supersedes_ai_processing_record_id` set to the superseded row's id —
  never as a standalone transition with no corresponding new row.
  **Rewriting the superseded row's own approved output content is
  prohibited, structurally, not merely by convention:** once a row's
  `human_review_status` reaches `approved`, `approved_with_changes`,
  `rejected`, or `superseded`, no field on that row may ever be written
  again by any command — mirroring `GovernanceDecision`'s own
  immutability-after-decision rule (canon 19b.3) and
  `PublicLedgerEntry`'s creation-time content immutability (canon
  19a.1).
- **`not_required`'s scope.** `not_required` is permitted only for
  **non-consequential** internal advisory output — the precise
  "consequential" test is defined in full by ADR-025 §2; this ADR
  incorporates that test by reference rather than restating it, so the
  two ADRs cannot drift out of agreement. Every **consequential** use
  must begin at `pending` and reach a terminal value only through an
  explicit `approved`/`approved_with_changes`/`rejected` human action —
  silence, a timeout, or a missing reviewer is never read as approval.

### D2 — `processing_status` (new field, new enum) — accepted as drafted

A new field, scoped **only** to the technical processing-pipeline
dimension, kept structurally distinct from `human_review_status`:

- `requested` — the request has been recorded; no model call has yet
  been attempted.
- `input_prepared` — the redaction/provenance validation step (ADR-025
  §1) has completed successfully and `redaction_manifest` (D4a, below)
  is present with `result = "pass"`; the model has not yet been called.
- `processing` — the model call is in flight. (No dedicated event marks
  entry to this transient state, per this project's existing
  convention.)
- `completed` — the model call returned usable output.
- `failed` — the model call could not produce usable output.
- `rejected_by_policy` — processing was refused before or after the
  model call by a policy check.

**`processing_status` has no stored `superseded` value.** Whether a
processing run has been superseded by a later attempt is a **derived,
query-time fact** — computed by checking whether any other
`AIProcessingRecord` row has `supersedes_ai_processing_record_id` equal
to this row's id.

**Allowed transitions:** `requested → input_prepared → processing →
{completed | failed | rejected_by_policy}`. `rejected_by_policy` is also
directly reachable from `requested`. No transition returns to an earlier
value; `completed`, `failed`, and `rejected_by_policy` are all terminal.

### D3 — `supersedes_ai_processing_record_id` (new field) — accepted as drafted

Nullable UUID, referencing another `AIProcessingRecord`'s
`ai_processing_record_id`. Set on a **new** row precisely when that new
row replaces an existing one. **Never set retroactively on the old
row** — the old row's own fields are never rewritten; only the new row
carries the back-reference. Whether a given row **has been** superseded
is always a derived, query-time fact, identical in kind to
`GovernanceDecision.supersedes_decision_id`'s pattern (canon 19b.4) and
`PublicLedgerEntry.supersedes_entry_id`'s pattern (canon 19a.1).

### D4 — Field additions, grouped by purpose (unchanged from the original draft)

- **Model and deployment governance:** `deployment_version`,
  `system_policy_version`, `generation_settings`, `processing_region`,
  `data_retention_mode`, `external_provider_flag`.
- **Provenance and integrity:** `input_hash`, `output_hash`.
- **Confidence and uncertainty:** `confidence_score`,
  `uncertainty_indicator`.
- **Explainability:** `explanation_reference`, `reason_codes`.
- **Human-reviewer provenance:** `human_reviewer_reference` (opaque,
  mirrors `TechnicalChallenge.submitter_authorization_reference`'s
  caller-supplied-opaque-reference pattern, canon 19b.4 — verified, for
  consequential review, via ADR-022's `verify_role_assignment_for_action`
  read, never trusted as an unverified assertion).
- **Lifecycle timestamps:** `completed_at`, `reviewed_at`.

**Superseded by D4a, below:** the original draft's flat
`redaction_policy_reference`/`redaction_applied` field pair is **removed**
from this list and replaced entirely by the `redaction_manifest` embedded
value object.

### D4a — `redaction_manifest` (amended: canonical embedded value object, replacing `redaction_policy_reference`/`redaction_applied`)

**`RedactionManifest` is a canon-shaped, immutable, embedded value object
within `AIProcessingRecord`** — not a separate entity, not an
implementation-time representation choice. `AIProcessingRecord` gains one
new field, `redaction_manifest` (nullable while `processing_status =
requested`; required and immutable from `input_prepared` onward),
containing exactly:

- `redaction_policy_reference` — which redaction policy performed this
  validation.
- `redaction_policy_version` — that policy's version.
- `input_classification` — the caller-declared or locally-inferred
  classification of the input content.
- `checked_field_categories` — which categories of forbidden content
  (identity, credential, vote-linkage, unrestricted audit) were checked.
- `removed_field_categories` — which of those checked categories were
  found present and excluded — **never the removed values themselves.**
- `prepared_input_hash` — the same digest as `input_hash` (D4), duplicated
  here for the manifest's own self-containment.
- `validator_version` — the version of the redaction-validation logic
  itself.
- `validated_at` — timestamp when validation ran.
- `result` — `pass` | `fail`.

**`redaction_manifest` must never contain:** raw input; removed values;
identity values; credential values; vote content; private audit content
— only category-level metadata about what was checked and what was found
and excluded, the same category-not-content boundary
`AuditExportPackage.chain_proof`'s public-safe metadata already
established (canon 19a.2).

**Once written, `redaction_manifest` is never modified** — it is set
exactly once, by `ai-processing-service` itself (never trusted as
caller-supplied), when the redaction/provenance validation step (ADR-025
§1) completes, whether the `result` is `pass` or `fail`. A `fail` result
is itself a recorded, permanent fact about that processing attempt, not
something a later step corrects in place; a corrected attempt is always a
new `AIProcessingRecord` row (D3).

### D5 — Event-name correction and full event catalog (canon 20.12) — accepted as drafted

**Correction:** `ai.output.corrected` → `ai.output_corrected`.

**Full proposed event catalog:**

| Event                              | Fires when                                                                                                 | Status              |
| ---------------------------------- | ---------------------------------------------------------------------------------------------------------- | ------------------- |
| `ai.processing_requested`          | (existing, unchanged) An `AIProcessingRecord` is created.                                                  | Existing            |
| `ai.input_prepared`                | (new) `processing_status → input_prepared` — `redaction_manifest.result = pass`.                           | New                 |
| `ai.output_created`                | (existing, unchanged) `processing_status → completed`.                                                     | Existing            |
| `ai.processing_failed`             | (new) `processing_status → failed`.                                                                        | New                 |
| `ai.processing_rejected_by_policy` | (new) `processing_status → rejected_by_policy` (including a `redaction_manifest.result = fail` outcome).   | New                 |
| `ai.processing_record_superseded`  | (new) A new row's `supersedes_ai_processing_record_id` references this row for a technical re-attempt.     | New                 |
| `ai.output_reviewed`               | (existing, unchanged) `human_review_status → pending`.                                                     | Existing            |
| `ai.output_accepted`               | (new) `human_review_status → approved`.                                                                    | New                 |
| `ai.output_corrected`              | (existing, **name corrected**) `human_review_status → approved_with_changes`.                              | Existing, corrected |
| `ai.output_rejected`               | (existing, unchanged) `human_review_status → rejected`.                                                    | Existing            |
| `ai.review_outcome_superseded`     | (new) A new row's `supersedes_ai_processing_record_id` references this row for a corrected review outcome. | New                 |

No new envelope field; canon section 21's envelope applies verbatim.

### D6 — Disclosure-lifecycle fields (new, amendment)

`AIProcessingRecord` gains three further fields, grounding ADR-025 §5's
revised, explicit disclosure protocol:

- `disclosure_required` — boolean. Set once, at creation or upon
  `processing_status → completed` at the latest, based on whether this
  record's use falls under ADR-025 §5's mandatory-disclosure rule
  (official/public AI-assisted output). Never retroactively flipped.
- `disclosure_package_reference` — nullable, opaque reference to the
  `AIDisclosurePackage` (ADR-025 §5) `ai-processing-service` constructs
  for this record, once constructed. Never contains, or points to
  anything containing, raw input, raw private output, hidden prompts,
  reviewer identity, a `RoleAssignment` UUID, identity data, credential
  data, vote data, or hidden reasoning (ADR-025 §5's exact prohibited-
  content list applies to whatever this reference resolves to).
- `disclosure_receipt_reference` — nullable, opaque reference to the
  receipt `transparency-service.publish_ledger_entry` returns once the
  corresponding `PublicLedgerEntry` is published (ADR-025 §5, step 3–4).
  Set exactly once, never rewritten.

### D7 — `DisclosureStatus` (new, amendment — derived read model, not a stored field)

**Not a canonical entity field — a query/read-model type**, computed
from `disclosure_required`, `disclosure_package_reference`, and
`disclosure_receipt_reference` (D6), the same "persisted fields plus a
derived read-model type" pattern `GovernanceDecision`/`FinalityStatus`
already established (canon 19b.4, ADR-018 amendment item 2):

- `not_required` — `disclosure_required = false`.
- `pending_package` — `disclosure_required = true` and
  `disclosure_package_reference` is not yet set.
- `pending_publication` — `disclosure_required = true`,
  `disclosure_package_reference` is set, `disclosure_receipt_reference`
  is not yet set.
- `published` — `disclosure_required = true` and
  `disclosure_receipt_reference` is set.

**`DisclosureStatus` is derived and not independently mutable** — no
command ever writes a `DisclosureStatus` value directly; it is always
computed fresh from the three D6 fields at query time, the same
"derived, never stored separately" discipline `FinalityStatus` already
established.

## Consequences

Once the separate, dedicated canon-edit task authorized by this ADR's
acceptance is carried out, `docs/canonical/TZ-00-domain-event-canon.md`
section 17.1 gains the fields in D2–D4, D4a, and D6, section 20.12 gains
the corrected/new events in D5, and `canon_version` moves `0.4.0 →
0.5.0`. **None of this is performed by this ADR's acceptance itself.**

## Security impact

`redaction_manifest` being set exclusively by `ai-processing-service`
itself, and being immutable and canon-shaped rather than an
implementation-time choice, closes a gap the original draft still left
open (a future implementation could otherwise have chosen a weaker,
non-canonical representation). The unified `supersedes_ai_processing_
record_id`/derived-supersession mechanism and the immutability-after-
terminal-status rule (D1) together ensure no `AIProcessingRecord` can
ever be rewritten to retroactively alter what an AI produced or what a
human decided about it. `disclosure_receipt_reference`'s "set exactly
once, never rewritten" rule, combined with `DisclosureStatus` being
fully derived, ensures a record cannot be made to appear published
without a real, `transparency-service`-issued receipt.

## Data impact

One existing entity (`AIProcessingRecord`) gains: `processing_status`,
`supersedes_ai_processing_record_id`, `deployment_version`,
`system_policy_version`, `generation_settings`, `processing_region`,
`data_retention_mode`, `external_provider_flag`, `input_hash`,
`output_hash`, `confidence_score`, `uncertainty_indicator`,
`explanation_reference`, `reason_codes`, `redaction_manifest` (an
embedded value object with nine of its own sub-fields), `human_reviewer_reference`,
`completed_at`, `reviewed_at`, `disclosure_required`,
`disclosure_package_reference`, `disclosure_receipt_reference` —
twenty-one top-level fields (precisely counted), plus
`redaction_manifest`'s nine embedded sub-fields, and six new/corrected
events (D5). Its existing twelve fields and six-value
`human_review_status` enum are completely unchanged. No other canonical
entity is affected.

## Migration impact

None — no `services/ai-processing-service` exists yet.

## Reversibility

Reversible with cost before code exists (this stage). Once real
`AIProcessingRecord` rows exist under the extended field set —
especially given D1's immutability rule and D4a's embedded-value-object
shape — removing or restructuring `redaction_manifest` or the disclosure
fields becomes a major-version-equivalent change under canon section 25.

## Related canon version

Authored against canon version `0.4.0`. Accepted with amendments per
Owner decision, above, proposing a minor bump to `0.5.0`; the
corresponding canon edit itself would be performed as its own separate,
dedicated follow-on task, not as part of this ADR's own acceptance —
that follow-on task has not been carried out.
