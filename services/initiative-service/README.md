# Initiative Service

Owns `Initiative`, `InitiativeVersion`, `SupportRecord`, `Amendment`
(canon section 11) and `SourceRecord` (canon section 12.1; ownership
matrix section 22). ADR-005 consolidates three canon-named modules -
"Initiative Service", "Amendment Service", "Evidence Service" - into this
one physical package, the same way `voting-service` consolidates "Ballot
Definition Service"/"Vote Casting Service"/"Receipt Service" and
`eligibility-service` consolidates its own three canon modules.

## Why one package for five entities (ADR-005)

`Initiative`, `InitiativeVersion`, `SupportRecord`, and `Amendment` are
inseparable in practice: an `Amendment` targets a specific
`InitiativeVersion`; a `SupportRecord` only makes sense against a
specific `Initiative`; and the initiative lifecycle (`draft` through
`archived`) is the spine every other entity here hangs off. `SourceRecord`
("Evidence Service" in canon) is consolidated alongside them because
`InitiativeVersion.source_references` points at it directly - splitting
evidence tracking into its own deployable would only add a network hop
between two entities that are read and written together. This mirrors
exactly the reasoning `voting-service`'s and `eligibility-service`'s own
READMEs give for their own consolidations.

## PACK-02 dependencies (ADR-008)

This service calls exactly two PACK-02 `application`-layer functions,
never their `storage`/`domain` modules:

- `epd2_credential_service.application.validate_participation_credential`
  - `add_support` validates the presented `initiative_support` credential
    (scoped to the target `initiative_id`) _before_ accepting a
    `SupportRecord`.
- `epd2_eligibility_service.application.get_eligibility_decision` -
  `add_support` _optionally_ resolves and checks a caller-supplied
  `EligibilityDecision` when a deployment models an eligibility-gated
  support pathway (e.g. "only verified residents of the affected region
  may support this initiative"). This is deliberately **not** mandatory
  on every `add_support` call: canon 11.3 only requires
  `SupportRecord.credential_reference` (credential-gating), never a
  separately-modeled decision record. A caller that wants the additional
  check passes both `eligibility_decision_store` and
  `eligibility_decision_id`; a caller that doesn't, gets credential-only
  gating. See `application.add_support`'s docstring.

Both stores are accepted as `Any`-typed passthrough parameters in
`application.py` - this package never imports
`epd2_credential_service.storage`/`epd2_eligibility_service.storage` (or
their `domain` modules), so it structurally cannot reach past those two
services' own published application-layer contracts. No other PACK-03
service (`voting-service`) is ever imported here either.

## AI cannot silently promote a source to `human_checked` (canon 12.1)

Canon's hard rule, verbatim: "ИИ не может незаметно повысить статус
источника до `human_checked`" (an AI actor may not silently promote a
source's verification status to `human_checked`).
`application.update_source_verification_status` enforces this
structurally: if `target_status == human_checked` and
`actor.actor_type == "ai"`, it raises `PermissionDeniedError`
(`PERMISSION_DENIED`) _before_ any other check, regardless of the
caller-supplied `actor_is_authorized` flag - an upstream authorization
decision is not a substitute for this actor-_type_-based rule, the same
shape `epd2_voting_service.application.approve_ballot_configuration` uses
for its own actor-identity check (ADR-009 item 7). `tests/test_application.py`
exercises both directions explicitly: a `human`-typed actor succeeds,
an `ai`-typed actor is rejected with `PERMISSION_DENIED`.

## One active support per participant per initiative (canon 11.3)

Canon, verbatim: "Один участник не может иметь более одной активной
поддержки одной инициативы" (one participant cannot have more than one
active support on one initiative). Enforced in `storage.py`:
`InMemorySupportRecordStore.create` rejects a second `active`
`SupportRecord` for the same `(initiative_id, support_actor_reference)`
with `DuplicateSupportError` (`DUPLICATE_SUPPORT`, canon section 24's own
code, reused verbatim) - distinct from `SupportRecordCreationConflictError`,
which fires only when the _same_ `support_record_id` is resubmitted with
different content (a CT-00-04 creation-conflict, not a duplicate-support
violation). `support_actor_reference`/`credential_reference` are opaque
UUID references only - `SupportRecord` structurally cannot carry
`account_id`/`person_id`/`identity_record_id` (`domain.FORBIDDEN_FIELD_NAMES`,
checked in `tests/test_domain.py`).

`Initiative.support_count` is a denormalized counter kept consistent with
the live count of `active` `SupportRecord`s: `add_support` increments it
(but only for a genuinely new record - a CT-00-04 replay must not
double-count), and both `withdraw_support` and `invalidate_support`
decrement it, in the same command/audit entry as the underlying
`SupportRecord` transition. It never drifts silently.

## Immutable `InitiativeVersion` / frozen `content_hash` (canon 11.2)

Canon, verbatim: "Опубликованная версия не изменяется. Любая редакция
создаёт новую версию" (a published version never changes; any edit
creates a new version) - this service applies that rule structurally to
_every_ version, not just published ones: `InitiativeVersion` has no
status field and no transition table at all (there is nothing to
transition - a "change" is always a new `(initiative_id, version_number)`
row). `content_hash` covers `title` through `source_references`
(`domain.compute_initiative_version_content_hash`, mirroring
`epd2_eligibility_service.domain.compute_snapshot_digest`'s style).
`application.create_initiative_version` is idempotent for an identical
`(initiative_id, version_number)` + identical content
(`storage.InMemoryInitiativeVersionStore.save` returns the existing
record unchanged); a resubmission of the same key with different content
raises `VersionFrozenError` (`INITIATIVE_VERSION_FROZEN`) - the same
"rule freeze" shape `epd2_eligibility_service.storage.InMemoryEligibilityRuleStore.save`
established for `EligibilityRule`.

`Initiative.current_version_id` is typed `UUID | None` rather than a bare
`UUID` - a judgment call this service had to make, since canon lists the
field but says nothing about whether an `Initiative` can exist before its
first `InitiativeVersion` does, and `InitiativeVersion.initiative_id`
itself must reference an already-existing `Initiative` (some order has to
come first). `create_initiative` creates the `Initiative` shell in
`draft` with `current_version_id = None`; `create_initiative_version`
must be called at least once (`version_number=1`) before
`submit_initiative` will accept the initiative
(`InitiativeHasNoVersionError`, `INITIATIVE_HAS_NO_VERSION`, otherwise).
Every later `create_initiative_version` call also advances
`current_version_id` to the new version, _unless_ a higher
`version_number` is already current (so a delayed retry of an older
version never regresses the pointer).

## Commands with no canon-named domain event (persist + audit only)

Canon section 20.6-20.7 names 17 events total (12 `initiative.*`, 4
`amendment.*`, `initiative.version_created`) - every command below still
persists its state change and calls `append_audit_event` (CT-00-07), it
simply builds no `EventEnvelope`, mirroring
`epd2_voting_service.application.submit_ballot_for_configuration_review`'s
own "no event for this step" precedent. The audit record's own
`event_type` field is still set to a descriptive (synthetic, not
wire-broadcast) label in every case, so the audit trail is never
ambiguous about which transition occurred:

- `Initiative`: `start_completeness_review` (`submitted ->
completeness_review`), `start_support_collection` (`published ->
support_collection`), `reject_initiative` (`support_collection|legal_review|voting
-> rejected`), `start_voting` (`ready_for_ballot -> voting` - the real
  `Ballot` lifecycle events belong to `voting-service`, never this
  service, ADR-008), `mark_adopted` (`voting -> adopted`).
- `SupportRecord`: `invalidate_support` (`active -> invalidated` - not
  even one of canon's own named commands; this service's own additive
  completion of the status canon lists but does not name a path to,
  distinct in the audit trail from a voluntary `withdraw_support` via its
  own `SUPPORT_INVALIDATED` reason code).
- `Amendment`: `create_amendment` (initial `draft` creation),
  `start_amendment_discussion` (`published -> under_discussion`),
  `withdraw_amendment`, `supersede_amendment` (`published|under_discussion
-> superseded` - uses the additive `AMENDMENT_TARGET_SUPERSEDED` reason
  code, not the generic `AMENDMENT_STATUS_CHANGED`, since canon's own text
  calls out this outcome specifically: "this amendment's target version
  no longer exists / was superseded before a decision was reached").
- `SourceRecord`: canon names **no** `source.*` event at all - both
  `add_source_record` and `update_source_verification_status` are
  persist + audit only, always.

## Reason codes

Canon section 24, reused verbatim: `VALIDATION_UNKNOWN_STATUS`,
`VALIDATION_FORBIDDEN_TRANSITION`, `VALIDATION_RECORD_NOT_FOUND`,
`PERMISSION_DENIED`, `DUPLICATE_SUPPORT`.

Additive (this service's own, one per entity plus the two spec-called-out
codes): `INITIATIVE_VERSION_FROZEN`, `AMENDMENT_TARGET_SUPERSEDED`,
`INITIATIVE_DUPLICATE_CREATION_CONFLICT`,
`SUPPORT_RECORD_DUPLICATE_CREATION_CONFLICT`,
`AMENDMENT_DUPLICATE_CREATION_CONFLICT`,
`SOURCE_RECORD_DUPLICATE_CREATION_CONFLICT`, `INITIATIVE_HAS_NO_VERSION`,
`INITIATIVE_NOT_ACCEPTING_SUPPORT`.

Audit-success classification codes (info severity, one per entity, reused
across every transition of that entity - the specific transition is
already visible via `action`/`event_type` on the audit record itself,
mirroring `epd2_voting_service.application`'s single `_BALLOT_STATUS_CHANGED`):
`INITIATIVE_STATUS_CHANGED`, `INITIATIVE_VERSION_CREATED`,
`SUPPORT_RECORDED`, `SUPPORT_WITHDRAWN`, `SUPPORT_INVALIDATED`,
`AMENDMENT_STATUS_CHANGED`, `SOURCE_STATUS_CHANGED`.

## Judgment calls / gaps filled (canon lists statuses, not always edges or events)

- The exact transition graphs (`domain.ALLOWED_*_TRANSITIONS`) are this
  service's own design decision - canon section 11/12 lists statuses, not
  edges between them (the same situation `voting-service`'s own README
  notes for `BallotOption`).
- `add_support` requires `Initiative.status == support_collection`
  (`INITIATIVE_NOT_ACCEPTING_SUPPORT` otherwise) - canon does not spell
  this out explicitly, but it is the only reading consistent with
  `support_collection -> qualified`/`-> rejected` being meaningful
  outcomes of a bounded collection window.
- `Amendment.decision_reference` is `None` until a discussion outcome
  sets it (`accept_amendment`/`reject_amendment` accept an optional
  `decision_reference` parameter) - canon lists the field but not its
  nullability.
- Like `epd2_voting_service.application`'s simple ballot-status
  transitions (`pause_ballot`/`resume_ballot`/`close_ballot`/
  `cancel_ballot`), the single-entity status-transition commands in this
  service (`_initiative_transition`/`_amendment_transition` and the
  `SourceRecord`/`SupportRecord` transition commands) are **not**
  idempotent against a retry _after_ the target status has already been
  reached - a second call raises the entity's own
  `Forbidden*TransitionError`, matching the upstream template's own,
  already-accepted behavior. Idempotency (CT-00-04) is guaranteed at the
  _creation_ layer (`create_initiative`, `create_initiative_version`,
  `add_support`, `create_amendment`, `add_source_record` all detect an
  identical resubmission and return the existing record) and at the audit
  layer (`append_audit_event`'s own `audit_event_id` dedup) - not at the
  "call the same transition twice" layer, which was never guaranteed by
  the sibling services this pack was modeled on either.
