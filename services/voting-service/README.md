# Voting Service

Owns `Ballot`, `BallotOption`, `VoteEnvelope`, `VoteReceipt` (canon
sections 15.1-15.4; ownership matrix section 22). ADR-005 consolidates
three canon-named modules - "Ballot Definition Service", "Vote Casting
Service", "Receipt Service" - into this one physical package. This is the
single most safety-critical service in CLAUDE-PACK-03.

## Vote linkability (CT-00-09, canon section 15.3 "Запрет")

`VoteEnvelope` never has, and structurally cannot have: `account_id`,
`person_id`, `identity_record_id`, `full_name`, `email`, `membership_id`,
or `identity_provider_reference`. `VoteReceipt` is held to exactly the
same standard - a receipt must be exactly as identity-free as the
envelope it proves inclusion for. Both are enforced by
`domain.FORBIDDEN_FIELD_NAMES` and `tests/test_domain.py`'s
`assert set(__dataclass_fields__) & FORBIDDEN_FIELD_NAMES == set()`
checks, mirrored in style from
`epd2_credential_service.domain.FORBIDDEN_FIELD_NAMES`.

`VoteEnvelope.credential_proof` must reference a `ParticipationCredential`,
never an `account_id` - it is that credential's own opaque
`credential_id` (a UUID), validated via
`epd2_credential_service.application.validate_participation_credential`
_before_ `application.cast_vote` ever constructs a `VoteEnvelope`. No
function in `domain.py`/`application.py`/`storage.py` accepts or returns
anything typed `Account`/`IdentityRecord`, and neither
`epd2_account_service` nor `epd2_identity_service` is imported anywhere in
this package - see `tests/test_domain.py::test_no_code_path_resolves_a_vote_envelope_to_an_account`.

`VoteReceipt.receipt_hash` is built only from the referenced
`VoteEnvelope`'s own `vote_envelope_id`/`integrity_hash`
(`compute_vote_receipt_hash`) - never from
`encrypted_or_encoded_choice`, even hashed, since `BallotMethod`'s small
option sets (`single_choice`/`yes_no`) would make a direct hash of the
choice itself dictionary-attackable. A receipt lets a voter verify
inclusion without publicly revealing what they chose (canon 15.4).

## Ballot invalidation (ADR-009 item 14, amended; PACK-05, ADR-017 Option B)

`ALLOWED_TRANSITIONS` includes `draft/configuration_review/scheduled ->
invalidated` at the domain/state-machine level (unchanged since
CLAUDE-PACK-03); CT-00-02/CT-00-03 already exercise
`BallotStatus.INVALIDATED`'s structural existence. Until PACK-05, no
command in `application.py` ever produced this transition. PACK-05 adds
exactly one narrow command, `application.invalidate_ballot`, per ADR-017's
accepted Option B: it reads an already-`approved`, correctly-scoped,
non-superseded `GovernanceDecision` (`decision_type =
ballot_invalidation`, `subject_reference.ballot_id` matching this
`Ballot`) via `epd2_governance_service.application.
get_governance_decision`/`is_current_approved_decision` (never
`.storage`/`.domain` - the same ADR-008-style `.application`-only
boundary this service already respects for `epd2_credential_service`/
`epd2_eligibility_service`, now exercised in the reverse direction for
the first time in this project: PACK-03 reading PACK-05). `voting-service`
remains the sole writer of `Ballot` throughout - `governance-service`
never receives a write path into this service's storage.
`BallotInvalidationNotAuthorizedError` is raised when no such decision
can be found. `cancel_ballot` (a normal, always-available withdrawal
path with no special authorization concern) remains the only early-exit
command available with no upstream dependency.

## Second-actor ballot approval (ADR-009 item 7 / INV-08)

`approve_ballot_configuration` (`configuration_review -> scheduled`)
requires the approving actor to differ from the ballot's own creator.
The creator is tracked as `created_by_actor_id` in
`storage.InMemoryBallotStore`'s internal `_BallotRecord` - **internal
bookkeeping, not a canon `Ballot` field** - the same pattern
`epd2_credential_service.storage._CredentialRecord.issuance_reference`
already established. The same actor attempting to approve their own
ballot raises `PermissionDeniedError`.

## One command, two events: `approve_ballot_configuration`

`ALLOWED_TRANSITIONS` has exactly one edge landing on `scheduled`
(`configuration_review -> scheduled`), so `schedule_ballot` is _not_ a
separate command - there is no second transition for it to perform.
`approve_ballot_configuration` performs that single transition and emits
**both** `ballot.configuration_locked` and `ballot.scheduled` (two
`EventEnvelope`s, two audit entries, same underlying state change) since
canon's own command list (section 20.10) names both events. See
`application.ApproveBallotConfigurationResult`.

## Configuration freeze / rule freeze (CT-00-10)

`configuration_hash` covers exactly: `ballot_method`, `secrecy_mode`,
`eligibility_rule_version`, `delegation_policy_version`, `quorum_rule`,
`threshold_rule`, `opens_at`, `closes_at`, `challenge_window_hours`
(using the _effective_, default-resolved value - see
`domain.effective_challenge_window_hours`), plus every `BallotOption` row
for the ballot. `application.submit_ballot_for_configuration_review`
(`draft -> configuration_review`) computes and freezes this hash,
confirming the referenced `EligibilitySnapshot` is real via
`epd2_eligibility_service.application.get_eligibility_snapshot` (ADR-008)
and folding its `digest` - not a bare `rule_version` number - into the
hash (`domain.compute_ballot_configuration_hash`). The snapshot's own
`digest` is separately recorded as `frozen_eligibility_snapshot_digest`
(again internal bookkeeping in `storage.py`, not a canon field), later
used by `cast_vote` to cross-check a presented credential's
`eligibility_snapshot_digest` against the exact snapshot this ballot's
configuration was frozen to.

Enforcement mirrors `EligibilityRuleStore.save`'s "rule freeze" pattern
directly: `storage.InMemoryBallotStore.save` compares
`domain.configuration_fields(...)` between the currently-stored ballot
and the incoming one whenever the stored ballot's status has already
left `draft`, raising `BallotConfigurationLockedError` on any difference.
`BallotOption` rows are frozen the same way at the application layer:
`add_ballot_option` refuses once `Ballot.status != draft`.

`challenge_window_hours` is optional; `DEFAULT_CHALLENGE_WINDOW_HOURS =
72` applies when absent (ADR-010, canon 0.2.0), overridable per ballot.

## Vote change / latest-valid-vote (ADR-009 items 1-2)

A participant may change their vote before `Ballot.closes_at`.
`cast_vote` supersedes the previous `validated` envelope for the same
`(ballot_id, credential_proof)` (transitioning it to `superseded` and
emitting `vote.superseded`) as part of accepting the new one. `DUPLICATE_VOTE`
is reserved for a genuinely late resubmission attempt _after_
`closes_at` when a `validated` envelope already exists for that
credential - a pre-close vote change is never an error.

## Abstention (ADR-009 item 3)

Abstention is modeled purely as an ordinary `BallotOption` row (e.g.
`option_code = "abstain"`) - there is no special-cased abstention field,
branch, or check anywhere in this service.

## Pilot method restriction (ADR-009 item 4)

`BallotMethod` has exactly two values: `single_choice`, `yes_no`.
Ranked-choice/multi-select are out of scope for this pilot and would
require their own future ADR before being added.

## PACK-02 dependency (ADR-008)

This service calls exactly two PACK-02 `application`-layer functions,
never their `storage`/`domain` modules:

- `epd2_credential_service.application.validate_participation_credential`
  - `cast_vote` validates the presented `ballot_access` credential
    _before_ accepting a `VoteEnvelope`.
- `epd2_eligibility_service.application.get_eligibility_snapshot` -
  `submit_ballot_for_configuration_review` freezes a ballot's
  configuration against a real `EligibilitySnapshot`.

Both stores are accepted as `Any`-typed passthrough parameters in
`application.py` - this package never imports
`epd2_credential_service.storage`/`epd2_eligibility_service.storage` (or
their `domain` modules), so it structurally cannot reach past those two
services' own published contracts.
