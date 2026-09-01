# ADR-025: PACK-06 use-class policy, redaction enforcement, providers, and mandatory disclosure

## Status

`accepted`, with an amendment replacing the informal external-
orchestration disclosure rule with an explicit, five-step
`AIDisclosurePackage` protocol (see Owner decision, below).

## Date

2026-07-24

## Owner decision

Accepted with amendment, 2026-07-24. §1 (redaction enforcement), §2
(consequential-use boundary), §3 (reviewer separation), §4 (external
providers), and §6 (provider abstraction) are all accepted exactly as
drafted, no change. **§5 (mandatory transparency for official AI-assisted
output) is replaced** by an explicit, five-step disclosure protocol,
grounded in the new `AIProcessingRecord` disclosure fields and
`DisclosureStatus` read model this same acceptance round adds to
ADR-023 (D6, D7). `AIDisclosurePackage` is confirmed as a contract/value
object, not a new canonical system-of-record entity. Building the
provider-abstraction interface, the redaction-validation pipeline, and
the disclosure protocol itself all remain separate, later implementation
tasks, not authorized by this acceptance alone.

## Canon implementation (2026-07-24, follow-on task)

ADR-023's own dedicated canon-edit task has now been carried out
(2026-07-24), and, per this ADR's own "Related canon version" section
below, it also implements the canon-shaped parts of this ADR's own
content: canon section 19c.6 records `AIDisclosurePackage` as a
contract/value object (never a canonical system-of-record entity,
mirroring the confirmation above) and its required/prohibited content
list; section 19c.7 records the mandatory five-step disclosure protocol
(§5 above) verbatim; section 19c.8 records the consequential-use
boundary (§2 above) and the reviewer-separation cross-reference (§3
above, to ADR-022's `verify_role_assignment_for_action`); section 19c.9
records the redaction (§1), external-provider (§4), and
provider-abstraction (§6) invariants at the structural level. The
reviewer-role taxonomy (ADR-022), the exact `verify_role_assignment_for_action`
signature (ADR-022), the external-provider allow-list's exact category
enumeration, the provider-abstraction interface's exact method
signatures, and the `AIDisclosurePackage` JSON Schema all remain
repository-side content, not canon text — consistent with this ADR's own
"Related canon version" section, unchanged by ADR-023's canon edit:

```text
sha256(docs/canonical/TZ-00-domain-event-canon.md) =
  374b25fddfab88846622bf078b35c4246d8ad8c5d65bf43e6ac4e82653f74f74
CANON_VERSION = 0.5.0
```

## Context

`docs/handover/PACK-06-SPEC.md` section 15 proposed conservative,
fail-closed defaults for AI use-class policy, redaction, and external-
provider restrictions, leaving two items open (external-provider scope,
who may act as reviewer) and leaving redaction enforcement's exact
location undecided. This ADR's own original draft resolved both open
items and specified redaction enforcement, but left the mandatory-
disclosure rule (§5) as an informal "orchestrating human-facing flow"
convention, without a concrete data protocol. The project owner has now
replaced that informal rule with an explicit, ordered protocol built on
`AIProcessingRecord`'s own new disclosure fields (ADR-023, D6/D7, this
same round).

## Problem

An informal orchestration convention — "some layer outside this pack
ensures disclosure happens before an artifact is finalized" — has no
concrete data to check against: no field records whether a disclosure
package was ever built, no field records whether `transparency-service`
ever actually published it, and no owning service has anything concrete
to inspect before finalizing an artifact. Left this way, "the disclosure
step succeeded" would be exactly the kind of caller-asserted claim this
pack's entire design otherwise refuses to trust.

## Considered options

- Option A — adopt the specification's own conservative defaults as
  proposed, leaving the disclosure rule as an informal convention.
- Option B — resolve every open item now, as binding decisions, replacing
  the informal disclosure rule with an explicit, verifiable protocol
  grounded in real `AIProcessingRecord` fields.

## Decision

**Option B.** §1–§4 and §6 below are unchanged from this ADR's original
draft. §5 is replaced by the explicit protocol below.

### 1. Redaction enforcement inside `ai-processing-service` — unchanged

**Redaction is enforced inside `ai-processing-service` itself.** The
service never trusts a caller-supplied redaction claim — it sets
`redaction_manifest` (ADR-023, D4a — the canonical embedded value object
within `AIProcessingRecord`: `redaction_policy_reference`,
`redaction_policy_version`, `input_classification`,
`checked_field_categories`, `removed_field_categories`,
`prepared_input_hash`, `validator_version`, `validated_at`, `result`)
itself, and only after its own validation succeeds or fails.

**Before any provider call**, `ai-processing-service` must, in order: (1)
validate the allowed `purpose_code`/`target_type` combination; (2) apply
deterministic forbidden-field checks against the caller-supplied input;
(3) validate input provenance and classification
(`AI_INPUT_PROVENANCE_UNVERIFIED`, ADR-024, if this cannot be established
with sufficient confidence); (4) construct `redaction_manifest` with
`result = pass` or `result = fail`; (5) compute `input_hash` (ADR-023,
D4) over the prepared, already-redacted input. If `redaction_manifest.
result = fail`, processing is rejected (`processing_status →
rejected_by_policy`, ADR-023 D2; `AI_REDACTION_FAILURE` or
`AI_REDACTION_MANIFEST_INVALID`, ADR-024) — never a soft warning that
still allows the model call to proceed.

### 2. Consequential-use boundary — unchanged

**Consequential output** is any AI output that: becomes official or
public content; is referenced by a human moderation or governance
decision; affects a participant-facing classification; triggers or
recommends a formal review workflow; is incorporated into a canonical
entity; or may materially affect access, participation, reputation,
voting, public information, or governance.

**Consequential output always requires verified human review** — the
full `human_review_status` path (ADR-023, D1) **and** the verified-
reviewer check (ADR-022's `verify_role_assignment_for_action`) for any
use requiring reviewer separation (§3, below).

**Non-consequential internal assistance** may use `human_review_status =
not_required` (ADR-023, D1), but can never cause a state mutation or
official publication (`AI_CONSEQUENTIAL_OUTPUT_NOT_REVIEWED`, ADR-024,
if a caller attempts otherwise).

### 3. Reviewer separation — unchanged

For moderation, governance, ballot-adjacent, or official-publication
uses: the reviewer must hold a verified `RoleAssignment`, confirmed via
`governance-service.verify_role_assignment_for_action` (ADR-022) — never
merely asserted via `actor_is_authorized`; the reviewer must be distinct
from the actor who submitted the AI request
(`AI_REVIEW_SELF_APPROVAL_PROHIBITED`, ADR-024, if violated); the final
human action always remains a command of the owning service, never an
AI-service command.

### 4. External providers — unchanged

External providers are forbidden for voting/tally/participation-pattern/
credential/identity/governance-sensitive/unrestricted-audit data;
self-hosted processing is required for aggregate anomaly indication,
extended to every use class touching those categories; external
providers may be used only for explicitly approved, sufficiently
redacted low-risk classes; provider retention/training must be disabled
where supported; unknown retention mode or region is fail-closed.

### 5. Mandatory transparency for official AI-assisted output (amended — explicit disclosure protocol)

**Replacing the informal orchestration rule this ADR originally drafted,**
the following five-step protocol is binding, grounded in ADR-023's new
`disclosure_required`/`disclosure_package_reference`/
`disclosure_receipt_reference` fields and derived `DisclosureStatus`
(ADR-023, D6/D7):

**Step 1.** A consequential official/public AI output receives verified
human approval (`human_review_status → approved` or
`approved_with_changes`, per §2/§3 above).

**Step 2.** `ai-processing-service` creates an immutable, redacted
`AIDisclosurePackage` (defined below) containing only the approved
public-disclosure fields, and records its reference in
`AIProcessingRecord.disclosure_package_reference` (ADR-023, D6) —
`DisclosureStatus` becomes `pending_publication`.

**Step 3.** `transparency-service` publishes the package through its
existing `publish_ledger_entry` command
(`PublicLedgerEntry.subject_type = ai_processing_record`, ADR-013 D3.5,
already accepted and currently dormant), with the `AIDisclosurePackage`'s
content passed as caller-supplied `raw_content` — no new read or write
edge is introduced between the two services; the existing
caller-supplied-content pattern is sufficient — and returns a
`disclosure_receipt_reference`.

**Step 4.** The receipt reference is recorded against the
`AIProcessingRecord` (`disclosure_receipt_reference`, ADR-023, D6) —
`DisclosureStatus` becomes `published`.

**Step 5.** An owning service may finalize the official/public artifact
**only when**: `disclosure_required = true`; `DisclosureStatus =
published` (ADR-023, D7); and `disclosure_receipt_reference` is present.
Any attempt to finalize before all three hold raises
`AI_PUBLIC_DISCLOSURE_REQUIRED` (ADR-024) in the owning service's own
command — not a check `ai-processing-service` performs on another
service's behalf, since `ai-processing-service` never marks any other
entity "complete."

**Rules, restated explicitly:**

- **The disclosure record's content is unchanged from the original
  draft:** must contain the fact that AI assistance was used,
  `purpose_code`, the approved public model/provider category and
  version reference, the processing date, the human-review status,
  whether the human accepted/changed/rejected the draft, the
  prompt-template and system-policy version references, and the
  `AIProcessingRecord` public reference. Must not contain raw input, raw
  private output (unless separately approved for publication), hidden
  prompts, private reviewer identity, any `RoleAssignment` UUID, identity/
  account/credential data, vote data, or hidden reasoning.
- **`ai-processing-service` never writes Transparency storage** — it only
  constructs the package and passes it as caller-supplied content;
  **`transparency-service` remains the sole writer of
  `PublicLedgerEntry`.**
- **Failure to obtain the receipt is fail-closed** — `DisclosureStatus`
  simply stays at `pending_publication` (or `pending_package`, if step 2
  itself failed) until a real receipt is recorded; there is no
  alternate, degraded path to `published`.
- **An official/public artifact cannot rely only on an orchestration-
  layer convention or a caller's assertion** — Step 5's three-part check
  is against real, persisted `AIProcessingRecord` fields and the derived
  `DisclosureStatus`, not a claim any caller supplies.

### 6. Provider abstraction — unchanged

A provider interface is specified with: submission of prepared input
only; return of structured output; reporting of provider/model/
deployment identifiers; reporting of region and retention mode; bounded,
deterministic timeout and cancellation behavior; deterministic error
mapping to the fail-closed conditions and their reason codes (ADR-024);
and no callback or tool interface capable of mutating Civic OS — the
concrete mechanism behind ADR-021's "no external provider gains Civic OS
mutation authority" decision.

### `AIDisclosurePackage` (new, amendment)

**A contract/value object, not a new canonical system-of-record
entity.** `AIDisclosurePackage` is the transient payload
`ai-processing-service` constructs in Step 2 and hands to
`transparency-service.publish_ledger_entry` as `raw_content` in Step 3 —
it is never itself persisted as a row `ai-processing-service` or
`transparency-service` "owns"; its only durable trace is (a) the
resulting `PublicLedgerEntry` row `transparency-service` already owns and
persists under its own existing ownership (canon 19a.1, unchanged by this
ADR), and (b) the opaque `disclosure_package_reference`/
`disclosure_receipt_reference` values recorded on the originating
`AIProcessingRecord` (ADR-023, D6). Its schema is fixed at
implementation time as a `contracts/schemas/` JSON Schema (ADR-025's own
future implementation task), following the same convention every prior
pack's own payload-shape schemas already use — not a canon addition, and
not a second system-of-record for the same fact `PublicLedgerEntry`
already records.

## Consequences

`ai-processing-service`'s implementation gains a mandatory redaction-
validation step producing a canonical `redaction_manifest` (ADR-023,
D4a), a reviewer-separation check layered on ADR-022's
`verify_role_assignment_for_action` read, an external-provider allow-list,
and a concrete, five-step disclosure protocol with its own tracked
fields (`disclosure_required`/`disclosure_package_reference`/
`disclosure_receipt_reference`, ADR-023 D6) and derived status
(`DisclosureStatus`, ADR-023 D7) — replacing what was an unverifiable
orchestration convention with real, queryable state. `tests/repository/
test_service_boundaries.py` gains no new cross-pack edge from this ADR
specifically (the transparency-publication path reuses the existing
caller-supplied-content pattern).

## Security impact

This ADR remains this pack's entire data-handling and provider-trust
model. The amended §5 closes a gap the original draft's informal
convention still left open: without concrete fields to check,
"disclosure happened" was previously only as trustworthy as whichever
orchestration code called it — now it is a real, three-part structural
check (`disclosure_required`, `DisclosureStatus = published`,
`disclosure_receipt_reference` present) any owning service's own command
can verify directly against `AIProcessingRecord`.

## Data impact

No new canonical entity. `AIDisclosurePackage` is a contract/value
object (a payload shape), never a canonical system-of-record entity —
confirmed explicitly per the owner's instruction. The disclosure-lifecycle
fields and `DisclosureStatus` themselves are ADR-023's own field
additions (D6, D7), not duplicated here.

## Migration impact

None — no `services/ai-processing-service` exists yet.

## Reversibility

The redaction-enforcement and reviewer-separation rules (§1, §3) remain
reversible with significant cost once real data exists, unchanged from
the original draft. The disclosure protocol (§5, amended) is now
somewhat more reversible in one respect than the original informal
convention would have been: because it is grounded in concrete,
versioned fields (ADR-023, D6/D7) rather than orchestration-layer code
scattered across owning services, a future refinement to the protocol
has one clear place (the `AIProcessingRecord` fields and
`DisclosureStatus` derivation) to change rather than many call sites.

## Related canon version

Authored against canon version `0.4.0`. Proposes no canon change itself
beyond what ADR-023 already proposes (the disclosure-lifecycle fields
and `DisclosureStatus` live in ADR-023, not here) — `AIDisclosurePackage`,
the reviewer taxonomy, the external-provider allow-list, and the
provider-abstraction interface are all repository-side content.
