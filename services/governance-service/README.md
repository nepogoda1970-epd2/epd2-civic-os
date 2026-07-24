# Governance Service

Owns `RoleAssignment` (canon `docs/canonical/TZ-00-domain-event-canon.md`
section 8.4, fields unchanged; physically relocated into this pack by
ADR-016), `GovernancePolicy`, `GovernanceDecision`, `TechnicalChallenge`
(canon section 19b, added by canon 0.4.0 / ADR-018), plus the derived,
never-stored `FinalityStatus` read model. ADR-016 consolidates all four
into this one physical package (the Permission/Role Service, Governance
Policy Service, Governance Decision Service, and Technical Challenge
Service rows of canon section 22's ownership matrix all resolve here).

## Cross-pack boundary (ADR-017) — the first bidirectional edge

This pack reads two upstream `.application` modules:
`epd2_voting_service.application` (`get_ballot`, already sanctioned) and
`epd2_tally_service.application.get_result_publication` (already
sanctioned by ADR-012, called directly from
`submit_technical_challenge`). Uniquely, it is also read _back_:
`voting-service` imports `epd2_governance_service.application`
(`get_governance_decision`, `is_current_approved_decision`) for its own
new `invalidate_ballot` command (ADR-017 Option B) — the first
bidirectional, same-generation cross-pack `.application`-only edge in
this project. `governance-service` never imports any of the excluded
identity/account/eligibility/credential/initiative/deliberation/
moderation/delegation/transparency services, and never imports another
upstream service's `.storage`/`.domain` module, even for a type
annotation — a passthrough store parameter (`submit_technical_challenge`'s
`result_publication_store`) is typed `Any` instead, the same convention
`epd2_voting_service.application`/`epd2_transparency_service.application`
already use for their own cross-pack store parameters
(`tests/repository/test_service_boundaries.py`).

## Entities and their state machines

### `RoleAssignment` (canon 8.4)

`pending -> active`, `active <-> suspended`, `active|suspended ->
expired|revoked`, `pending -> revoked`
(`domain.ROLE_ASSIGNMENT_ALLOWED_TRANSITIONS`). `role_code` remains an
**open string** at canon level (canon 19b.1 says so explicitly) — the
closed 8-value pilot taxonomy (`domain.PILOT_ROLE_CODES`, ADR-020 §5:
`governance_policy_proposer`, `governance_policy_approver`,
`governance_reviewer`, `technical_challenge_reviewer`,
`ballot_invalidation_proposer`, `ballot_invalidation_approver`,
`oversight_reviewer`, `observer`) is enforced only at the application
layer (`request_role_assignment`, `bootstrap.run_bootstrap_seed`), never
as a domain-level closed enum. `domain.GLOBAL_SCOPE_ID` is a sentinel
`scope_id` meaning "covers every subject scope"
(`domain.scope_covers`). Universal rule (canon 19b.1): no
`RoleAssignment`, of any `role_code`, may ever decrypt, retrieve, or link
a secret vote.

### `GovernancePolicy` (canon 19b.2)

`draft -> active -> superseded`
(`domain.GOVERNANCE_POLICY_ALLOWED_TRANSITIONS`). Unlike
`epd2_transparency_service.domain.DisclosurePolicy.approved_by_role_id`
(nullable until `active`), canon 19b.2 states `approved_by_role_id` is
"не nullable" — this package's reading (documented in
`domain.GovernancePolicy`'s own docstring, since canon leaves the exact
mechanics to implementation) is that both the proposer and the
_designated_ approver are known and recorded from the moment a policy is
proposed; `activate_governance_policy` re-validates both are still
active, in the correct role, in scope, and distinct actors
(ADR-020 item 1) at the moment of activation, since validity can change
in between. At most one `active` policy per `policy_type` at a time —
activating a new version automatically supersedes the previously-active
one for the same type, never a standalone command. `version` is
monotonic per `policy_type`.

### `GovernanceDecision` (canon 19b.3)

One entity with a `decision_type` discriminator (minimum required by
canon: `ballot_invalidation`, `technical_challenge_adjudication`,
`result_finality_determination`, `mandate`, `oversight_directive`).
Stored `status` is **only** `proposed`/`approved`/`rejected` —
`superseded` is never a stored value; whether a decision has been
superseded is always derived by checking whether another decision's
`supersedes_decision_id` points at it
(`storage.GovernanceDecisionStore.find_superseding`, only ever matching
an `approved` superseding candidate). `proposed -> approved`/`proposed ->
rejected` only (`domain.GOVERNANCE_DECISION_ALLOWED_TRANSITIONS`) —
immutable once decided; a correction is always a _new_ row with
`supersedes_decision_id` set. `finality_outcome` (`final`/`invalidated`)
is only ever meaningful for `result_finality_determination`, set exactly
once at approval — a deliberately _different_ type from the derived
`FinalityStatus` read model (`provisional`/`finality_blocked`/`final`/
`invalidated`, `application.get_finality_status`), never a single shared
four-value enum (canon 19b.3's own explicit instruction).

### `TechnicalChallenge` (canon 19b.4)

`submitted -> under_review -> upheld|rejected`
(`domain.TECHNICAL_CHALLENGE_ALLOWED_TRANSITIONS`); `upheld`/`rejected`
are terminal. `submitter_authorization_type` is
`participation_credential` (accepted as an opaque, caller-supplied proof
and never dereferenced — mirroring `publish_ledger_entry`'s `raw_content`
precedent) or `role_assignment` (validated locally: must resolve to an
active, in-scope `RoleAssignment` for the referenced
`result_publication_id` — no new cross-pack read is needed). Adjudication
(`under_review -> upheld|rejected`) is never a standalone command — it is
always a side effect of `approve_governance_decision`/
`reject_governance_decision` when `decision_type =
technical_challenge_adjudication`
(`application._adjudicate_linked_challenge_if_any`). `begin_technical_
challenge_review` (`submitted -> under_review`) deliberately emits no
canonical event — canon section 20.15's twelve-event catalog names only
`governance.technical_challenge_submitted` and
`governance.technical_challenge_adjudicated`; this transition is audited
(CT-00-07) but not represented as a domain event, since inventing a
thirteenth event not in canon 0.4.0 is out of this pack's scope.

## Aggregate finality rule (canon 19b.5)

Each `TechnicalChallenge` gets its own adjudication decision (1:1) — no
challenge is ever adjudicated as a side effect of a _different_
challenge's decision. Finality is blocked
(`ResultFinalityBlockedByOpenChallengeError`) while any challenge for a
`result_publication_id` remains `submitted`/`under_review`
(`storage.TechnicalChallengeStore.has_unresolved_challenges`). Exactly
one `approved`, non-superseded `result_finality_determination` decision
may exist per `result_publication_id` at a time
(`ResultFinalityDeterminationDuplicateError`); a correction is always a
new, superseding decision. A zero-challenge result still requires an
explicit two-actor `result_finality_determination` decision — deadline
expiry alone is never sufficient for finality.

## Bootstrap authority (ADR-020 item 6) — deployment-time only

`bootstrap.run_bootstrap_seed` is **not** exposed through the normal
command surface or `contracts/openapi/pack-05.yaml` at all. It creates
exactly two distinct-actor, already-`active` `RoleAssignment`s
atomically, with `assigned_by` set to a fixed sentinel
(`bootstrap.BOOTSTRAP_ASSIGNED_BY_MARKER`), produces an immutable,
SHA-256-checksummed `BootstrapSeedManifest`, records real `AuditEvent`s,
and is permanently disabled after its first successful execution
(`bootstrap.InMemoryBootstrapSeedStore.has_run`,
`BootstrapAlreadyExecutedError`). No actor may seed or approve their own
assignment (enforced the same way ordinary grants are:
`_assert_distinct_actors`).

## Two-actor approval (ADR-020 item 1, canon 19b's own repeated

requirement)

Proposer and approver/rejecter must resolve to **distinct `actor_id`s**
(`application._assert_distinct_actors`, comparing `.actor_id`, not
`.role_assignment_id` — the same real actor holding two different
`RoleAssignment` records still fails this check), and both must be an
`active`, correctly-`role_code`d, in-scope `RoleAssignment`
(`application._require_active_in_scope_role`). Required for
`GovernancePolicy` activation, every `GovernanceDecision`
approval/rejection (which includes ballot invalidation and result-finality
determination as named `decision_type` values), and — transitively, via
`voting-service.invalidate_ballot`'s read of an approved
`ballot_invalidation` decision — ballot invalidation itself.

## Ballot invalidation (ADR-017 Option B)

`voting-service` remains the **sole writer** of `Ballot`.
`epd2_voting_service.application.invalidate_ballot` is the one narrow,
additional command that verifies an approved, correctly-scoped
`ballot_invalidation` `GovernanceDecision` (via
`get_governance_decision`/`is_current_approved_decision`) before
transitioning `Ballot` to `invalidated`. `governance-service` never
writes `voting-service` storage directly, and never writes
`ResultPublication` at all — `get_finality_status` is the sole
authoritative way to learn a result's finality.

## Application commands -> canon events (section 20.15, verbatim list)

| Command                                               | Transition                                  | Event                                      |
| ----------------------------------------------------- | ------------------------------------------- | ------------------------------------------ | -------------------------------------------- |
| `request_role_assignment`                             | (create) `-> pending`                       | `governance.role_assignment_requested`     |
| `activate_role_assignment`                            | `pending -> active`                         | `governance.role_assignment_activated`     |
| `revoke_role_assignment`                              | `* -> revoked`                              | `governance.role_assignment_revoked`       |
| `propose_governance_policy`                           | (create) `-> draft`                         | `governance.policy_proposed`               |
| `activate_governance_policy`                          | `draft -> active` (+ old `-> superseded`)   | `governance.policy_activated`              |
| _(side effect of the above)_                          | `active -> superseded`                      | `governance.policy_superseded`             |
| `propose_governance_decision`                         | (create) `-> proposed`                      | `governance.decision_proposed`             |
| `approve_governance_decision`                         | `proposed -> approved`                      | `governance.decision_approved`             |
| `reject_governance_decision`                          | `proposed -> rejected`                      | `governance.decision_rejected`             |
| _(side effect of approving a superseding decision)_   | n/a (superseded row's status never changes) | `governance.decision_superseded`           |
| `submit_technical_challenge`                          | (create) `-> submitted`                     | `governance.technical_challenge_submitted` |
| `begin_technical_challenge_review`                    | `submitted -> under_review`                 | _(none — see above)_                       |
| _(side effect of approve/reject_governance_decision)_ | `under_review -> upheld                     | rejected`                                  | `governance.technical_challenge_adjudicated` |

Every command follows the shared shape: `actor: ActorRef,
actor_is_authorized: bool, correlation_id: UUID, clock: Clock, event_id:
UUID | None = None`, and every state-changing command calls
`append_audit_event` (CT-00-07). `event_id` is the CT-00-04 idempotency
key.

## Never published verbatim (canon 19b.1/19b.3/19b.4)

`actor_id`, `assigned_by` (`RoleAssignment`), `proposed_by_role_id`,
`approved_by_role_id`, `rejected_by_role_id` (`GovernancePolicy`/
`GovernanceDecision`), and `submitter_authorization_reference`
(`TechnicalChallenge`) are real, stored domain fields but are omitted
entirely from every `*_public_payload` function in `events.py` — the
only place any of these four entities is serialized for a public event.
`GovernanceDecision.subject_reference` structurally rejects a
`vote_envelope_id` key (`domain.GovernanceDecision.__post_init__`) — no
reverse vote-linkability path exists anywhere in this pack.

## Known gaps (documented, not silently dropped)

- **`GovernancePolicy.rule_definition` is not interpreted by a rule
  engine.** It is stored and versioned exactly as proposed; enforcement
  of its content against a live command is reserved future work
  (`GOVERNANCE_POLICY_VIOLATION` is a defined, defense-in-depth reason
  code with no current caller).
- **`ResultFinalityNotAuthorizedError` has no current caller.** ADR-017
  narrows its meaning to a would-be direct query/action against
  `ResultPublication` finality state that bypasses
  `get_finality_status` entirely — no `tally-service` command exists yet
  for it to gate.
- **No cryptographic signing.** `BootstrapSeedManifest`'s checksum is a
  deterministic SHA-256 digest, not a signature — out of this pack's
  scope (required scope item 13).

## Reason codes

Canon codes reused verbatim: `VALIDATION_UNKNOWN_STATUS`,
`VALIDATION_FORBIDDEN_TRANSITION`, `VALIDATION_RECORD_NOT_FOUND`,
`PERMISSION_DENIED`.

Carried forward from the PACK-05 spec (`exceptions.py`):
`ROLE_ASSIGNMENT_NOT_ACTIVE`, `ROLE_ASSIGNMENT_SCOPE_MISMATCH`,
`GOVERNANCE_POLICY_VIOLATION`, `TWO_ACTOR_APPROVAL_REQUIRED`,
`SAME_ACTOR_APPROVAL_REJECTED`, `TECHNICAL_CHALLENGE_WINDOW_CLOSED`,
`TECHNICAL_CHALLENGE_ALREADY_ADJUDICATED`,
`GOVERNANCE_DECISION_NOT_APPROVED`, `BALLOT_INVALIDATION_NOT_AUTHORIZED`
(also independently redeclared in `contracts/reason-codes/pack-03.yml`,
since the literal is used by a real `voting-service` guard).

Additive, ADR-019 (`exceptions.py`):
`RESULT_FINALITY_BLOCKED_BY_OPEN_CHALLENGE`,
`RESULT_FINALITY_DETERMINATION_DUPLICATE`,
`GOVERNANCE_DECISION_SUPERSEDED`,
`TECHNICAL_CHALLENGE_SUBMITTER_INELIGIBLE`. `RESULT_FINALITY_NOT_
AUTHORIZED` is retained but narrowed (see "Known gaps" above).

Additive, this service's own duplicate-conflict codes (`exceptions.py`):
`ROLE_ASSIGNMENT_DUPLICATE_CONFLICT`,
`GOVERNANCE_POLICY_DUPLICATE_CONFLICT`,
`GOVERNANCE_DECISION_DUPLICATE_CONFLICT`,
`TECHNICAL_CHALLENGE_DUPLICATE_CONFLICT`,
`GOVERNANCE_BOOTSTRAP_ALREADY_EXECUTED`.

Additive, audit-success classifications (`application.py`, info
severity): `GOVERNANCE_ROLE_ASSIGNMENT_STATUS_CHANGED`,
`GOVERNANCE_POLICY_STATUS_CHANGED`,
`GOVERNANCE_DECISION_STATUS_CHANGED`,
`TECHNICAL_CHALLENGE_STATUS_CHANGED`.
