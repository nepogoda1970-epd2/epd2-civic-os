# Delegation Service

Owns `Delegation`, `DelegationSnapshot` (canon section 16; ownership matrix
section 22). ADR-005 consolidates two canon-named modules - "Delegation
Service" and "Delegation Resolution Engine" - into this one physical
package.

## No PACK-02 dependency, no PACK-03↔PACK-03 import (ADR-008)

Unlike `voting-service`/`eligibility-service`, this service has **no
PACK-02 dependency at all**. It also never imports `epd2_voting_service`
(ADR-008 item 3 forbids PACK-03↔PACK-03 imports), even though a
`DelegationSnapshot` is conceptually tied to a `Ballot`: every function in
this package accepts `ballot_id: UUID` purely as an opaque reference.
Wherever this service would conceptually need to know "did this
delegator already cast a direct vote for this ballot" (ADR-009 item 10),
it accepts that fact as a plain `frozenset[UUID]` (`direct_voters`)
supplied by the caller - never by reaching into `voting-service`'s own
storage or domain types. `pyproject.toml` declares dependencies on
`epd2-core` and `epd2-audit-core` only.

## Canon section 16.1's four prohibitions ("Запреты") and their enforcement

Canon (`docs/canonical/TZ-00-domain-event-canon.md`, section 16.1):

> - самоделегирование;
> - две конкурирующие активные делегации одного scope;
> - скрытое бессрочное делегирование;
> - изменение snapshot после открытия голосования.

1. **"самоделегирование" (self-delegation).** `domain.Delegation.__post_init__`
   rejects `delegator_actor_id == delegate_actor_id` structurally, raising
   `exceptions.SelfDelegationError` (`DELEGATION_SELF_REFERENCE_FORBIDDEN`)
   no matter how a `Delegation` is constructed.
   `application.create_delegation` performs the identical check again,
   explicitly, _before_ it ever constructs a `Delegation` object -
   belt-and-suspenders, mirroring the pattern other services in this
   monorepo use for their own structural invariants (e.g.
   `epd2_voting_service.domain.Ballot.__post_init__`'s
   `closes_at > opens_at` check, enforced once at the domain layer with
   no separate application-layer re-check needed there since that
   invariant has no adjacent judgment call; here we duplicate the check
   because the task specification explicitly asks for defense-in-depth on
   this specific prohibition).

2. **"две конкурирующие активные делегации одного scope" (two competing
   active delegations of the same scope).** Enforced in `storage.py`:
   `InMemoryDelegationStore.create` rejects a second `Delegation` for the
   same `(delegator_actor_id, scope_type, scope_id)` triple whenever
   another (differently-identified) delegation for that triple already
   has a status in `domain.BLOCKING_SCOPE_STATUSES`. **Documented choice:**
   `BLOCKING_SCOPE_STATUSES = {draft, active}`, not just `{active}` - a
   `draft` delegation already reserves its scope triple, so a second
   `create_delegation` call for the same delegator/scope cannot slip in
   between "created as draft" and "activated". Rejected with
   `exceptions.DelegationScopeConflictError` (`DELEGATION_SCOPE_CONFLICT`).

3. **"скрытое бессрочное делегирование" (hidden indefinite delegation).**
   `Delegation.valid_until: datetime | None` has no default value at any
   construction site in this package - every caller must consciously pass
   either a concrete instant or an explicit `None` for "no end date"; there
   is no way to omit the field and land on an implicit default. This is
   primarily an API-design/documentation guarantee (the dataclass makes
   the field unavoidable to consider), reinforced by a `__post_init__`
   check that a supplied `valid_until`, if not `None`, must be strictly
   after `valid_from` - a `valid_until` that reads as "meaningless" (equal
   to or before `valid_from`) is rejected rather than silently accepted as
   another way to hide an unbounded delegation.

4. **"изменение snapshot после открытия голосования" (changing a
   snapshot after voting has opened).** `DelegationSnapshot` is immutable
   once created. `storage.InMemoryDelegationSnapshotStore.save` enforces
   a freeze keyed on `(ballot_id, input_hash)`, mirroring
   `epd2_eligibility_service.storage.InMemoryEligibilityRuleStore.save`'s
   own "rule freeze" pattern (itself keyed on `(eligibility_rule_id,
rule_version)`) almost exactly: a `save` for an already-used key with
   identical `snapshot_hash` content is an idempotent no-op (returns the
   _original_ stored record); a `save` for an already-used key with
   _different_ `snapshot_hash` content raises
   `exceptions.SnapshotFrozenError` (`DELEGATION_SNAPSHOT_FROZEN`). See
   "Freeze-by-`input_hash`" below for the hash construction itself.

## Maximum delegation depth 1 (ADR-009 item 9) and `DELEGATION_CYCLE`

> "Maximum delegation depth? Proposed: a small, explicit bounded constant
> (depth 1 - no re-delegation chains) for the pilot, configurable later.
> This is a hard cap in addition to, not instead of,
> `delegation.cycle_detected`/`DELEGATION_CYCLE` cycle detection - the two
> are complementary, not redundant." (ADR-009 item 9)

`application.create_delegation` rejects creating a delegation whose
proposed `delegate_actor_id` is themselves _currently_ an active
`delegator_actor_id` on another active `Delegation` for the _same_
`(scope_type, scope_id)` - allowing that would create a depth-2 chain
(A delegates to B, B delegates to C). This reuses the canon section-24
`DELEGATION_CYCLE` code verbatim, treating a depth violation as a
degenerate one-step cycle in this pilot's terms. `tests/test_application.py`
has an explicit regression: create A→B (active) for a scope, then attempt
to create B→C for the _same_ scope, and confirm rejection.

`application.resolve_delegation_snapshot` additionally runs a second,
defensive check during resolution (see its own docstring): for every
delegator→delegate pair it resolves, it checks whether that delegate is
_themselves_ an active delegator for the same scope. Under the depth-1
invariant `create_delegation` maintains, this should never be true; if it
somehow is (e.g. a future depth cap increase, or a bug), the contribution
is excluded from `resolved_weights` and a diagnostic is appended to
`cycle_records` rather than silently double-counting weight or crashing.
**True multi-hop cycle detection (traversing an arbitrary-length chain) is
explicitly out of scope** for this pilot and is future work once the
depth cap is ever raised past 1 - for depth 1, the two checks above
together are the complete guard.

## Direct vote overrides delegation (ADR-009 item 10)

> "Can a delegator override their delegate for one ballot? Proposed: yes -
> a delegator's own valid `VoteEnvelope` for that `Ballot` ... takes
> precedence over any vote cast by their delegate using that specific
> delegation for that same ballot." (ADR-009 item 10)

`application.resolve_active_delegate(delegation_store, *,
delegator_actor_id, scope_type, scope_id, direct_voters)` is the pure
building block: it returns `None` if `delegator_actor_id` is itself in
`direct_voters` (their own direct vote wins - do not resolve any
delegate for them), else the resolved `delegate_actor_id` from their
_active_ `Delegation` for that scope if one exists, else `None` (no
active delegation - they contribute no weight to anyone).
`application.resolve_delegation_snapshot` calls this once per delegator
in `delegator_actor_ids` and accumulates weight per resolved delegate.

## `DelegationSnapshot` freeze-by-`input_hash` (mirrors `EligibilitySnapshot`)

`domain.compute_delegation_snapshot_input_hash` hashes exactly the
_inputs_ to one resolution run (`ballot_id`, `policy_version`,
`scope_type`, `scope_id`, the sorted `delegator_actor_ids` set, the
sorted `direct_voters` set) - this `(ballot_id, input_hash)` pair is the
freeze key, the direct analogue of
`epd2_eligibility_service.domain.compute_snapshot_digest`'s
`(eligibility_rule_id, rule_version)` freeze key.
`domain.compute_delegation_snapshot_hash` then hashes the _result_
(`input_hash` folded together with `resolved_weights`/`cycle_records`),
deliberately excluding `created_at`/`delegation_snapshot_id` so that two
resolution runs producing the same logical result at different wall-clock
instants are recognized as identical content, not a spurious freeze
violation. `storage.InMemoryDelegationSnapshotStore.save` compares this
`snapshot_hash` for records sharing a `(ballot_id, input_hash)` key -
identical hash is an idempotent replay (CT-00-04); different hash is
`SnapshotFrozenError` (canon prohibition #4, the CT-00-10 rule-freeze
analogue this pack's own review calls out for this pack: "assert the
freeze against a real `EligibilitySnapshot` digest" - here, against this
service's own `DelegationSnapshot`'s analogous digest, following the
exact same pattern `EligibilityRule`/`EligibilitySnapshot` established).

## Auditing a rejected delegation-cycle attempt (judgment call)

The task calls out explicitly that a rejected depth-1/cycle violation in
`create_delegation` emits **no** state-changing event (no `Delegation` is
ever created, so no `delegation.created` fires) but should still be
audited, since "a rejected critical action is still politically
significant per INV-04/INV-09". This service's choice: when
`create_delegation`'s depth-1 guard rejects a request, it appends a
lightweight, audit-only `AppendAuditEventRequest` directly (there is no
real `Delegation`/`EventEnvelope` to build the audit request's
`before_hash`/`after_hash` from, so the audit payload instead captures the
_attempted_ delegation's identifying fields -
`delegation_id`/`delegator_actor_id`/`delegate_actor_id`/`scope_type`/
`scope_id`/`conflicting_delegation_id` - hashed into `after_hash`, with
`before_hash` empty since nothing existed before the attempt). The
audit record's `event_type` is the literal string `"delegation.cycle_detected"`
(canon's own event name for this outcome) and its `reason_code` is
`DELEGATION_CYCLE`, even though no matching `EventEnvelope` is ever built
or returned - there is no PACK-03 precedent this service could point to
for "audit a rejected attempt with no real event", so this is this
service's own worked-out, documented answer to that judgment call.
Ordinary validation failures elsewhere in this service (self-delegation,
scope conflict, unknown transitions) are **not** given this same
reject-audit treatment - only the depth-1/cycle case, because the task
specification calls it out by name as the one rejection this pack's
canon event vocabulary (`delegation.cycle_detected`) already has a place
for.

## `resolve_delegation_snapshot`: one function, two descriptions

The task sketches `resolve_delegation_snapshot`'s signature twice, in two
different places, with two different parameter lists: a minimal
resolution-only shape (`delegation_store, *, ballot_id, policy_version,
delegator_actor_ids, scope_type, scope_id, direct_voters, clock`) under
the `DelegationSnapshot` section, and a full command shape (every command
needs `actor`, `actor_is_authorized`, `correlation_id`, `clock`,
`event_id`, plus `append_audit_event`) under "Application commands".
This service implements one function satisfying the latter, superset
signature (`application.resolve_delegation_snapshot`, additionally taking
`snapshot_store`/`audit_store`/`actor`/`actor_is_authorized`/
`correlation_id`/`event_id`) - the minimal shape describes the pure
resolution logic this function performs internally (the
`resolve_active_delegate` loop plus hash computation), not a separate,
second function. There is exactly one `resolve_delegation_snapshot` in
this package.

## `suspend`/`unsuspend`/`invalid` transitions: persist + audit only

Canon section 20.11 lists exactly six events for this service:
`delegation.created`, `delegation.activated`, `delegation.revoked`,
`delegation.expired`, `delegation.cycle_detected`,
`delegation.snapshot_created`. The `suspended`/`invalid` states exist in
canon's own status list (section 16.1) and `ALLOWED_TRANSITIONS` includes
edges into and out of them, but no canon event name covers
`active -> suspended`, `suspended -> active`, `draft|active -> invalid` -
`application.suspend_delegation`/`unsuspend_delegation`/
`mark_delegation_invalid` therefore persist the transition and append an
audit entry (reason code `DELEGATION_STATUS_CHANGED`, same as every other
transition), but return `event=None` on their `DelegationResult` - no
`EventEnvelope` is ever built for these three commands, mirroring
`epd2_voting_service.application.submit_ballot_for_configuration_review`'s
own "no event for this step" precedent. Unlike
`epd2_voting_service`'s `BallotStatus.INVALIDATED` (structurally
unreachable via any `application.py` command per ADR-009 item 14),
`mark_delegation_invalid` here **is** a real, callable command - canon
simply assigns it no event name, it is not forbidden from being reached.

## Delegation is disabled by default at the `Ballot` level (ADR-009 item 8) - not this service's concern

> "Is delegation enabled in the first pilot? Proposed: `Delegation`/
> `DelegationSnapshot` are implemented fully in PACK-03 regardless (canon
> requires them in this pack's scope), but new `Ballot`s default to
> `delegation_policy_version = null` (delegation resolution disabled) for
> the first real ballot type; enabling it is a per-ballot-type
> configuration choice, not a repository-wide switch." (ADR-009 item 8)

This service implements `Delegation`/`DelegationSnapshot` fully and has
no opinion on whether any given `Ballot` actually uses delegation -
`Ballot.delegation_policy_version` is `voting-service`'s own field
(this service is never imported by, and never imports, that one - see
"No PACK-02 dependency" above), and defaulting it to "disabled" for a
given ballot type is entirely `voting-service`'s/its callers' decision.
This service only provides the resolution mechanism (`create_delegation`
through `resolve_delegation_snapshot`) for whichever caller chooses to
invoke it.

## Identity-separation

`Delegation` and `DelegationSnapshot` never carry `account_id`,
`person_id`, or `identity_record_id` - only opaque `*_actor_id`
references (`delegator_actor_id`, `delegate_actor_id`) and an opaque
`ballot_id` reference. `domain.FORBIDDEN_FIELD_NAMES` and
`tests/test_domain.py`'s
`assert set(__dataclass_fields__) & FORBIDDEN_FIELD_NAMES == set()`
checks enforce this on both dataclasses, mirroring
`epd2_voting_service.domain.FORBIDDEN_FIELD_NAMES`'s own pattern.

## Reason codes

Canon section-24 codes reused verbatim: `VALIDATION_UNKNOWN_STATUS`,
`VALIDATION_FORBIDDEN_TRANSITION`, `VALIDATION_RECORD_NOT_FOUND`,
`PERMISSION_DENIED`, `DELEGATION_CYCLE`, `DELEGATION_EXPIRED`.

Additive (this service's own, none conflict with a canon-assigned code):
`DELEGATION_SELF_REFERENCE_FORBIDDEN`, `DELEGATION_SCOPE_CONFLICT`,
`DELEGATION_SNAPSHOT_FROZEN`, `DELEGATION_DUPLICATE_CREATION_CONFLICT`.

Audit-success classification codes (info severity):
`DELEGATION_STATUS_CHANGED` (every `Delegation` status transition -
create/activate/revoke/expire/suspend/unsuspend/mark-invalid),
`DELEGATION_SNAPSHOT_CREATED` (`resolve_delegation_snapshot`).

## `revocation_status` (canon field, no enumerated values)

Canon lists `revocation_status` as a `Delegation` field distinct from
`status`, without giving it an enumerated value list anywhere in section
16.1. Mirroring `epd2_voting_service.domain.Ballot`'s own precedent for
policy strings canon leaves open (`secrecy_mode`, `quorum_rule`,
`threshold_rule` are all plain, unvalidated `str` fields there), this
service treats `revocation_status` the same way: an opaque, caller-supplied
`str` with no service-side enum validation. This service defines no
revocation-_request_ workflow of its own (e.g. no "pending revocation"
approval process) - that would be future scope; `revoke_delegation`
already performs the actual `active|suspended -> revoked` status
transition directly.
