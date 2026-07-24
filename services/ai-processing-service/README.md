# AI Processing Service

Owns `AIProcessingRecord` (canon `docs/canonical/TZ-00-domain-event-canon.md`
section 17.1, extended by section 19c — "ИИ-обработка — расширение / AI
Processing Context", added by canon 0.5.0 / ADR-023/ADR-025), the
embedded, immutable `RedactionManifest` value object (19c.4), the
derived, never-stored `DisclosureStatus` read model (19c.5), and
`AIDisclosurePackage` (19c.6) — a contract/value object this service
constructs and hands to `transparency-service`, never a second entity it
persists itself. ADR-021 consolidates all of this into one physical
package (canon section 22's "AI Accountability Service" ownership-matrix
row resolves here).

## Two independent status planes (19c.1)

`AIProcessingRecord` carries two closed, canon-fixed statuses that never
move together:

- `processing_status` — the technical pipeline plane: `requested ->
  input_prepared -> processing -> {completed | failed |
  rejected_by_policy}`, with `rejected_by_policy` also directly reachable
  from `requested` or `input_prepared`
  (`domain.PROCESSING_STATUS_ALLOWED_TRANSITIONS`). Has **no stored
  `superseded` value** — whether a processing attempt has been superseded
  is always a derived, query-time fact
  (`storage.AIProcessingRecordStore.find_superseding`), never a value
  this enum itself carries.
- `human_review_status` — the unchanged six-value enum from canon 17.1
  (`not_required`, `pending`, `approved`, `approved_with_changes`,
  `rejected`, `superseded`). Only `not_required -> {nothing further}`
  (assigned once, at creation, for non-consequential output, 19c.8) and
  `pending -> {approved | approved_with_changes | rejected}`
  (`domain.HUMAN_REVIEW_STATUS_ALLOWED_TRANSITIONS`) are ever stored by a
  command. `superseded` is never a command-stored value —
  `AIProcessingRecord.__post_init__` rejects constructing one with it set
  directly; it is surfaced only by the derived accessor
  `derive_effective_human_review_status`
  (`application.get_effective_human_review_status`), the same "derived,
  not stored" principle `governance-service.FinalityStatus` already
  establishes for its own supersession concept.

Both statuses' `superseded` meaning routes through exactly one shared
field, `supersedes_ai_processing_record_id` (19c.2) —
`application.supersede_ai_processing_record` is the *only* mechanism by
which either a technical processing attempt or a human review outcome is
ever corrected: it always creates a brand-new row, never rewrites the
superseded row's own fields. Its `supersession_kind` parameter
(`"processing"` or `"review"`) selects which of the two canon events
fires (`ai.processing_record_superseded` vs.
`ai.review_outcome_superseded`) — the caller's own reason for the
replacement decides this, not the field's mere presence.

`human_review_status` is decided exactly once, at `request_ai_processing`
time: `pending` if the caller declares the output consequential, else
`not_required` (19c.8 — `not_required` is only ever admissible for
non-consequential output). Every consequential output must reach
`pending` and may finish only through an explicit
`approved`/`approved_with_changes`/`rejected` outcome via
`review_ai_output` — silence, timeout, a missing reviewer, or a missing
role verification never implies approval
(`application.assert_consequential_output_reviewed` is the fail-closed
gate every downstream disclosure/finalization step calls first).

## RedactionManifest (19c.4) — service-performed, never caller-supplied

`RedactionManifest` is a canonical, immutable, embedded value object
(nine fields: `redaction_policy_reference`, `redaction_policy_version`,
`input_classification`, `checked_field_categories`,
`removed_field_categories`, `prepared_input_hash`, `validator_version`,
`validated_at`, `result`). **This service performs redaction/provenance
validation itself**, via `redaction.RedactionValidator.validate` —
`application.prepare_input` never trusts a caller-supplied
`redaction_applied`-style flag. Raw input and removed values are never
stored — only category-level metadata about what was checked and
excluded. An unclassified/unverifiable input
(`declared_input_classification` empty) is rejected
(`AIInputProvenanceUnverifiedError`) before any validator call runs at
all; a `result = fail` outcome routes `prepare_input` directly to
`processing_status = rejected_by_policy`, never to `input_prepared`.

## The strict data boundary (required scope item 7)

This service never accepts, as processing input: raw `Account`/
`IdentityRecord` data, credential secrets, `ParticipationCredential`
secret content, `VoteEnvelope` content, vote-linkability data,
secret-ballot content, an unrestricted `AuditEvent` export, or hidden
reasoning/chain-of-thought. Nothing in `domain.py`, `application.py`, or
`provider.py` has a field or parameter shaped to carry any of these —
the boundary is structural, not merely a runtime check
(`tests/repository/test_service_boundaries.py`,
`tests/contract/test_ct00_09_vote_linkability.py`'s AST-based import
scan confirming this package never even imports
`epd2_voting_service`/`epd2_tally_service`/`epd2_delegation_service`/
`epd2_account_service`/`epd2_identity_service`/`epd2_credential_service`).

## Cross-pack boundary (ADR-022) — one narrow governance read

This service imports exactly one `governance-service` function,
`epd2_governance_service.application.verify_role_assignment_for_action`
— never `.domain`, never any other `.application` function, and never
duplicates Governance's own role-validity logic locally. Its own
`role_assignment_store` parameter is accepted as `Any` (the same
`epd2_voting_service.application.invalidate_ballot`/
`epd2_governance_service.application`-passthrough convention every prior
cross-pack edge in this project already uses) — this module has no
import of `epd2_governance_service.storage`/`.domain` anywhere.
`publish_ai_disclosure` similarly calls
`epd2_transparency_service.application.publish_ledger_entry` directly
(`ledger_store`/`policy_store`/`transparency_audit_store` are likewise
`Any` passthroughs) — `ai-processing-service` never writes
`PublicLedgerEntry` itself; `transparency-service` remains the sole
writer.

## Reviewer roles and use classes (ADR-022, ADR-025 §2/§3)

Four reviewer roles (`domain.REVIEWER_ROLE_CODES`): `ai_output_reviewer`,
`ai_moderation_reviewer`, `ai_governance_reviewer`,
`ai_publication_reviewer`. Six use classes
(`domain.UseClass`/`PURPOSE_CODES`): `summarization`, `classification`,
`recommendation`, `drafting`, `anomaly_indication`,
`policy_compliance_assistance` — each with its own closed
`purpose_code`/`target_type` allow-list
(`domain.PERMITTED_PURPOSE_TARGET_COMBINATIONS`,
`assert_purpose_target_combination_allowed`).
`domain.required_reviewer_role_codes` maps a use class/target type to its
required base reviewer role; `is_official_publication = True` overrides
this and requires `ai_publication_reviewer` specifically. Self-review is
*prohibited*, not merely discouraged, for moderation-, governance-,
ballot-adjacent-, and official-publication uses
(`domain.review_requires_independent_reviewer`,
`AIReviewSelfApprovalProhibitedError`) — `review_ai_output` compares the
verified reviewer's own actor reference against the caller-supplied
`requesting_actor_reference` to enforce this.

## Provider and redaction abstractions (required scope item 12; ADR-025 §6)

`provider.AIModelProvider` is a deliberately narrow `Protocol`: one
`submit` method, one best-effort `cancel` method. **No callback,
tool-calling, or command-issuing parameter exists anywhere on it** — a
provider implementation is structurally incapable of mutating Civic OS,
because no such interface is ever constructed or passed to it.
`provider.assert_external_provider_use_allowed` fail-closes an external
(non-self-hosted) submission unless the use class is one of the three
approved low-risk classes (`summarization`, `drafting`,
`recommendation` — `anomaly_indication` is always self-hosted-only) *and*
`processing_region`/`data_retention_mode` are both recognized values;
unknown region or retention mode is fail-closed. `ScriptedAIModelProvider`
and `redaction.ScriptedRedactionValidator` are the only implementations
this pack ships — real external provider credentials and any live
third-party integration are explicitly out of scope (required scope item
19).

## Mandatory disclosure protocol (19c.7, ADR-025 §5)

Five steps, each a distinct application command/read: (1) verified human
approval first (`assert_consequential_output_reviewed`); (2)
`create_disclosure_package` constructs the immutable
`AIDisclosurePackage` and records its own freshly-minted opaque reference
in `disclosure_package_reference` (`DisclosureStatus` becomes
`pending_publication`); (3)–(4) `publish_ai_disclosure` publishes the
package through `transparency-service.publish_ledger_entry` and records
the returned `public_ledger_entry_id` as `disclosure_receipt_reference`
(`DisclosureStatus` becomes `published`); (5)
`assert_disclosure_complete_for_official_finalization` is the read-only
gate an *owning* service calls, from its own finalize command, before
completing an official/public artifact — `ai-processing-service` never
marks another entity "finalized" itself, mirroring
`governance-service.get_finality_status`'s own role as a read another
service's command consults.

## Fail-closed behavior

Fourteen named conditions across `exceptions.py` fail closed rather than
default-permit: unauthorized actor
(`PermissionDeniedError`/`AIReviewerRoleInvalidError`/
`AIReviewerScopeMismatchError`), self-review
(`AIReviewSelfApprovalProhibitedError`), unverified input provenance
(`AIInputProvenanceUnverifiedError`), a failed redaction check
(`AIRedactionFailureError`), suspected prompt injection
(`AIPromptInjectionSuspectedError`), a prohibited-input finding
(`AIProhibitedInputDetectedError`), an unavailable/timed-out/malformed
provider result or unsupported model version
(`AIModelUnavailableError`/`AIProcessingTimeoutError`/
`AIOutputMalformedError`/`AIModelVersionUnsupportedError`), below-
threshold confidence (`AIConfidenceBelowThresholdError`), a missing
reviewer or rejected output blocking disclosure
(`AIHumanReviewerMissingError`/`AIOutputRejectedByHumanError`/
`AIConsequentialOutputNotReviewedError`), a policy conflict
(`AIPolicyConflictError`), an already-superseded record
(`AIProcessingRecordSupersededError`), a required-but-missing published
disclosure (`AIPublicDisclosureRequiredError`), and an attempted
autonomous mutating action (`AIAutonomousActionProhibitedError`, never
raised by this pack's own code since no such interface exists to trigger
it — kept as a defense-in-depth reason code per required scope item 11).

## Application commands -> canon events (section 20.12)

| Command                                | Transition                                        | Event                                |
| --------------------------------------- | -------------------------------------------------- | -------------------------------------- |
| `request_ai_processing`                 | (create) `-> requested`                            | `ai.processing_requested` (+ `ai.output_reviewed` if consequential) |
| `prepare_input`                         | `requested -> input_prepared` or `-> rejected_by_policy` | `ai.input_prepared` or `ai.processing_rejected_by_policy` |
| `begin_processing`                      | `input_prepared -> processing`                     | _(none — audited only)_                |
| `complete_processing_with_provider`     | `processing -> completed` or `-> failed`           | `ai.output_created` or `ai.processing_failed` |
| `fail_processing`                       | `processing -> failed`                             | `ai.processing_failed`                 |
| `reject_processing_by_policy`           | `* -> rejected_by_policy`                           | `ai.processing_rejected_by_policy`     |
| `review_ai_output`                      | `pending -> {approved \| approved_with_changes \| rejected}` | `ai.output_accepted`/`ai.output_corrected`/`ai.output_rejected` |
| `supersede_ai_processing_record`        | (create new row)                                    | `ai.processing_record_superseded` or `ai.review_outcome_superseded` |
| `create_disclosure_package`             | n/a (sets `disclosure_package_reference`)           | _(none — audited only)_                |
| `publish_ai_disclosure`                 | n/a (sets `disclosure_receipt_reference`)           | _(none — audited only; delegates to `transparency-service`)_ |

Every command follows the shared shape: `actor: ActorRef,
actor_is_authorized: bool, correlation_id: UUID, clock: Clock, event_id:
UUID | None = None`, and every state-changing command calls
`append_audit_event` (CT-00-07). `event_id` is the CT-00-04 idempotency
key.

## Never published verbatim

`human_reviewer_reference` is a real, stored domain field but is never
part of any published event payload or OpenAPI response body shaped for
public consumption per canon 19c.3/ADR-022 — it is present only in the
internal `AIProcessingRecord` representation. `AIDisclosurePackage.
to_raw_content()` is, by construction, the only place this pack's own
data ever becomes public — every field on it is already public-safe.

## Known gaps (documented, not silently dropped)

- **No cryptographic signing.** Disclosure receipts and redaction
  manifests are plain, hash-stamped records, not cryptographically
  signed — out of this pack's scope (required scope item 19).
- **No autonomous tool execution.** `AIModelProvider` has no callback,
  tool, or command-issuing interface at all — this is a structural
  property, not a runtime check with a bypass to guard against.
- **Emergency/Crisis Override is out of scope** (required scope item
  19) — nothing in this pack reads, writes, or references
  `EmergencyAction`.

## Reason codes

Canon codes reused verbatim: `VALIDATION_UNKNOWN_STATUS`,
`VALIDATION_FORBIDDEN_TRANSITION`, `VALIDATION_RECORD_NOT_FOUND`,
`PERMISSION_DENIED`.

Additive, ADR-024 (`exceptions.py`): `AI_MODEL_UNAVAILABLE`,
`AI_PROCESSING_TIMEOUT`, `AI_OUTPUT_MALFORMED`,
`AI_MODEL_VERSION_UNSUPPORTED`, `AI_CONFIDENCE_BELOW_THRESHOLD`,
`AI_POLICY_CONFLICT`, `AI_REDACTION_FAILURE`,
`AI_PROMPT_INJECTION_SUSPECTED`, `AI_PROHIBITED_INPUT_DETECTED`,
`AI_HUMAN_REVIEWER_MISSING`, `AI_HUMAN_REVIEW_REQUIRED`,
`AI_OUTPUT_REJECTED_BY_HUMAN`, `AI_PROCESSING_RECORD_SUPERSEDED`,
`AI_AUTONOMOUS_ACTION_PROHIBITED`, `AI_REVIEWER_ROLE_INVALID`,
`AI_REVIEWER_SCOPE_MISMATCH`, `AI_REVIEW_SELF_APPROVAL_PROHIBITED`,
`AI_REDACTION_MANIFEST_INVALID`, `AI_INPUT_PROVENANCE_UNVERIFIED`,
`AI_PUBLIC_DISCLOSURE_REQUIRED`, `AI_CONSEQUENTIAL_OUTPUT_NOT_REVIEWED`,
`AI_TARGET_REFERENCE_MALFORMED` (this last one defined in `domain.py`,
alongside its own allow-lists).

Additive, this service's own duplicate-conflict code (`exceptions.py`):
`AI_PROCESSING_RECORD_DUPLICATE_CONFLICT`.

Additive, audit-success classification (`application.py`, info
severity): `AI_PROCESSING_RECORD_STATUS_CHANGED`.

Cross-pack, read-only reference (governance-service-owned, re-registered
here since `review_ai_output` reads it as a control-flow discriminator
against `verification.reason_code`, never raises it itself):
`ROLE_ASSIGNMENT_SCOPE_MISMATCH`.
