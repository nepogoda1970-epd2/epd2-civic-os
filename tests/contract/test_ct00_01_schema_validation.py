"""CT-00-01 Schema Validation (canon section 27): invalid structure is
rejected. Positive cases validate real, service-produced instances against
`contracts/schemas/*.json` and `contracts/events/*.json`; negative cases
confirm a deliberately invalid instance is rejected by the same schema.

Validated here with `epd2_core.minimal_json_schema` (always available,
stdlib-only). The same schema files are also standard JSON Schema and are
validated by the real `jsonschema` package in CI - see
`contracts/README.md`.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from _schema_helpers import envelope_to_jsonable, load_schema, to_jsonable

from epd2_account_service.application import create_account
from epd2_account_service.events import account_state_payload
from epd2_account_service.storage import InMemoryAccountStore
from epd2_audit_core.storage import InMemoryAuditEventStore
from epd2_core.clock import FixedClock
from epd2_core.event_envelope import ActorRef
from epd2_core.minimal_json_schema import SchemaValidationError, validate
from epd2_credential_service.application import issue_participation_credential
from epd2_credential_service.domain import CredentialType
from epd2_credential_service.events import credential_full_state_payload
from epd2_credential_service.storage import InMemoryCredentialStore

# --- PACK-03 imports (added alongside the PACK-02 imports above) -----------
from epd2_delegation_service.application import create_delegation
from epd2_delegation_service.events import delegation_state_payload
from epd2_delegation_service.storage import InMemoryDelegationStore
from epd2_eligibility_service.application import (
    create_eligibility_rule,
    create_eligibility_snapshot,
)
from epd2_eligibility_service.storage import (
    InMemoryEligibilityRuleStore,
    InMemoryEligibilitySnapshotStore,
)
from epd2_identity_service.application import start_identity_verification
from epd2_identity_service.events import identity_record_payload
from epd2_identity_service.storage import InMemoryIdentityRecordStore
from epd2_initiative_service.application import create_initiative
from epd2_initiative_service.events import initiative_full_state_payload
from epd2_initiative_service.storage import InMemoryInitiativeStore
from epd2_tally_service.application import (
    complete_tally,
    publish_result,
    start_tally,
    verify_tally,
)
from epd2_tally_service.events import result_publication_state_payload, tally_full_state_payload
from epd2_tally_service.storage import InMemoryResultPublicationStore, InMemoryTallyStore
from epd2_voting_service.application import (
    CastVoteResult,
    approve_ballot_configuration,
    cast_vote,
    create_ballot,
    open_ballot,
    submit_ballot_for_configuration_review,
)
from epd2_voting_service.domain import BallotMethod
from epd2_voting_service.events import ballot_full_state_payload, vote_envelope_full_state_payload
from epd2_voting_service.storage import (
    InMemoryBallotOptionStore,
    InMemoryBallotStore,
    InMemoryVoteEnvelopeStore,
)


def test_account_instance_validates_against_account_schema(
    account_store: InMemoryAccountStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    result = create_account(
        account_store,
        audit_store,
        locale="en",
        terms_version="1.0",
        consent_status="granted",
        actor=actor,
        correlation_id=uuid4(),
        clock=clock,
    )
    validate(to_jsonable(account_state_payload(result.account)), load_schema("account.schema.json"))


def test_account_missing_required_field_is_rejected() -> None:
    schema = load_schema("account.schema.json")
    instance = {
        "account_id": str(uuid4()),
        "email_status": "unverified",
        "mfa_status": "disabled",
        "account_status": "pending",
        "created_at": datetime(2026, 1, 1, tzinfo=UTC).isoformat(),
        "last_login_at": None,
        "locale": "en",
        "terms_version": "1.0",
        # consent_status omitted - required field missing
    }
    with pytest.raises(SchemaValidationError):
        validate(instance, schema)


def test_account_unknown_status_is_rejected_by_schema() -> None:
    schema = load_schema("account.schema.json")
    instance = {
        "account_id": str(uuid4()),
        "email_status": "unverified",
        "mfa_status": "disabled",
        "account_status": "not_a_real_status",
        "created_at": datetime(2026, 1, 1, tzinfo=UTC).isoformat(),
        "last_login_at": None,
        "locale": "en",
        "terms_version": "1.0",
        "consent_status": "granted",
    }
    with pytest.raises(SchemaValidationError):
        validate(instance, schema)


def test_identity_record_instance_validates(
    identity_store: InMemoryIdentityRecordStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    result = start_identity_verification(
        identity_store,
        audit_store,
        account_id=uuid4(),
        verification_provider="provider-x",
        verification_level="basic",
        country="DE",
        provider_reference="ref-1",
        actor=actor,
        correlation_id=uuid4(),
        clock=clock,
    )
    validate(
        to_jsonable(identity_record_payload(result.record)),
        load_schema("identity-record.schema.json"),
    )


def test_eligibility_rule_instance_validates(
    eligibility_rule_store: InMemoryEligibilityRuleStore,
) -> None:
    rule = create_eligibility_rule(
        eligibility_rule_store,
        eligibility_rule_id=uuid4(),
        rule_version=1,
        scope_type="civic_space",
        scope_id=uuid4(),
        required_membership_status="active",
        required_verification_level="basic",
        region_constraint=None,
        minimum_membership_age=None,
        exclusion_conditions=(),
        valid_from=datetime(2026, 1, 1, tzinfo=UTC),
        valid_until=None,
    )
    instance = {
        "eligibility_rule_id": str(rule.eligibility_rule_id),
        "rule_version": rule.rule_version,
        "scope_type": rule.scope_type,
        "scope_id": str(rule.scope_id),
        "required_membership_status": rule.required_membership_status,
        "required_verification_level": rule.required_verification_level,
        "region_constraint": rule.region_constraint,
        "minimum_membership_age": rule.minimum_membership_age,
        "exclusion_conditions": list(rule.exclusion_conditions),
        "valid_from": rule.valid_from.isoformat(),
        "valid_until": rule.valid_until,
    }
    validate(instance, load_schema("eligibility-rule.schema.json"))


def test_participation_credential_instance_validates(
    credential_store: InMemoryCredentialStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    result = issue_participation_credential(
        credential_store,
        audit_store,
        credential_id=uuid4(),
        credential_type=CredentialType.SPACE_ACCESS,
        scope_type="civic_space",
        scope_id=uuid4(),
        valid_from=datetime(2026, 1, 1, tzinfo=UTC),
        expires_at=datetime(2027, 1, 1, tzinfo=UTC),
        usage_limit=None,
        rule_version=1,
        eligibility_snapshot_digest="a" * 64,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    validate(
        to_jsonable(credential_full_state_payload(result.credential)),
        load_schema("participation-credential.schema.json"),
    )
    # Envelope structure itself is also validated (CT-00-01 applies to the
    # canonical envelope, not just entity bodies).
    validate(envelope_to_jsonable(result.event), load_schema("event-envelope.schema.json"))


def test_participation_credential_with_forbidden_identity_field_is_rejected() -> None:
    """A credential-shaped payload that a bug somehow attached an identity
    field to must fail schema validation - `additionalProperties: false`
    is the structural backstop for CT-00-08."""
    schema = load_schema("participation-credential.schema.json")
    instance = {
        "credential_id": str(uuid4()),
        "credential_type": "space_access",
        "scope_type": "civic_space",
        "scope_id": str(uuid4()),
        "issued_at": datetime(2026, 1, 1, tzinfo=UTC).isoformat(),
        "valid_from": datetime(2026, 1, 1, tzinfo=UTC).isoformat(),
        "expires_at": datetime(2027, 1, 1, tzinfo=UTC).isoformat(),
        "status": "issued",
        "usage_limit": None,
        "usage_counter": 0,
        "revocation_status": "not_revoked",
        "issuer_signature": None,
        "credential_version": 1,
        "rule_version": 1,
        "eligibility_snapshot_digest": "a" * 64,
        "identity_record_id": str(uuid4()),  # forbidden - must be rejected
    }
    with pytest.raises(SchemaValidationError, match="identity_record_id"):
        validate(instance, schema)


def test_event_envelope_missing_integrity_is_rejected() -> None:
    schema = load_schema("event-envelope.schema.json")
    instance = {
        "event_id": str(uuid4()),
        "event_type": "account.created",
        "event_version": "1.0",
        "occurred_at": datetime(2026, 1, 1, tzinfo=UTC).isoformat(),
        "producer": "account-service",
        "actor": {"actor_id": str(uuid4()), "actor_type": "service"},
        "subject": {"subject_type": "account", "subject_id": str(uuid4())},
        "correlation_id": str(uuid4()),
        "causation_id": None,
        "payload": {},
        # integrity omitted - required field missing
    }
    with pytest.raises(SchemaValidationError):
        validate(instance, schema)


# =============================================================================
# PACK-03 (added alongside the PACK-02 tests above): Ballot, VoteEnvelope,
# Initiative, Delegation, Tally, ResultPublication against their new
# `contracts/schemas/*.json` files.
# =============================================================================


def _cast_real_vote(
    *,
    ballot_store: InMemoryBallotStore,
    option_store: InMemoryBallotOptionStore,
    envelope_store: InMemoryVoteEnvelopeStore,
    audit_store: InMemoryAuditEventStore,
    credential_store: InMemoryCredentialStore,
    eligibility_rule_store: InMemoryEligibilityRuleStore,
    eligibility_snapshot_store: InMemoryEligibilitySnapshotStore,
    clock: FixedClock,
    actor: ActorRef,
) -> CastVoteResult:
    """Full real chain producing an actual, service-constructed
    `VoteEnvelope`: an eligibility rule + snapshot (eligibility-service), a
    `ballot_access` participation credential scoped/digested to match
    (credential-service), and a `Ballot` walked all the way from `draft`
    to `open` (voting-service), then one real `cast_vote` call. Used here
    for CT-00-01's schema-validation round-trip; the same shape is used
    again, independently, by CT-00-09 and CT-00-04's own PACK-03 tests."""
    from datetime import timedelta

    rule = create_eligibility_rule(
        eligibility_rule_store,
        eligibility_rule_id=uuid4(),
        rule_version=1,
        scope_type="ballot",
        scope_id=uuid4(),
        required_membership_status="active",
        required_verification_level="basic",
        region_constraint=None,
        minimum_membership_age=None,
        exclusion_conditions=(),
        valid_from=clock.now(),
        valid_until=None,
    )
    snapshot = create_eligibility_snapshot(
        eligibility_snapshot_store,
        audit_store,
        eligibility_rule_id=rule.eligibility_rule_id,
        rule_version=1,
        eligible_decisions=(),
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        causation_id=None,
        clock=clock,
    ).snapshot

    ballot_id = uuid4()
    credential = issue_participation_credential(
        credential_store,
        audit_store,
        credential_id=uuid4(),
        credential_type=CredentialType.BALLOT_ACCESS,
        scope_type="ballot",
        scope_id=ballot_id,
        valid_from=clock.now(),
        expires_at=clock.now() + timedelta(days=365),
        usage_limit=None,
        rule_version=1,
        eligibility_snapshot_digest=snapshot.digest,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    ).credential

    creator = ActorRef(actor_id=uuid4(), actor_type="service")
    create_ballot(
        ballot_store,
        audit_store,
        ballot_id=ballot_id,
        space_id=uuid4(),
        subject_type="initiative",
        subject_id=uuid4(),
        question="Shall this pass?",
        ballot_method=BallotMethod.YES_NO,
        secrecy_mode="secret",
        eligibility_rule_version=1,
        delegation_policy_version=1,
        quorum_rule="none",
        threshold_rule="simple_majority",
        opens_at=clock.now(),
        closes_at=clock.now() + timedelta(days=1),
        challenge_window_hours=None,
        actor=creator,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    submit_ballot_for_configuration_review(
        ballot_store,
        audit_store,
        eligibility_snapshot_store,
        ballot_id=ballot_id,
        eligibility_snapshot_id=snapshot.eligibility_snapshot_id,
        actor=creator,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    approve_ballot_configuration(
        ballot_store,
        audit_store,
        ballot_id=ballot_id,
        actor=actor,  # a different actor than the ballot's own creator
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    open_ballot(
        ballot_store,
        option_store,
        audit_store,
        ballot_id=ballot_id,
        actor=creator,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    return cast_vote(
        ballot_store,
        envelope_store,
        audit_store,
        credential_store,
        vote_envelope_id=uuid4(),
        ballot_id=ballot_id,
        credential_proof=credential.credential_id,
        encrypted_or_encoded_choice="yes",
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )


def test_ballot_instance_validates_against_ballot_schema(
    ballot_store: InMemoryBallotStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    from datetime import timedelta

    result = create_ballot(
        ballot_store,
        audit_store,
        ballot_id=uuid4(),
        space_id=uuid4(),
        subject_type="initiative",
        subject_id=uuid4(),
        question="Shall this pass?",
        ballot_method=BallotMethod.YES_NO,
        secrecy_mode="secret",
        eligibility_rule_version=1,
        delegation_policy_version=1,
        quorum_rule="none",
        threshold_rule="simple_majority",
        opens_at=clock.now(),
        closes_at=clock.now() + timedelta(days=1),
        challenge_window_hours=None,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    validate(
        to_jsonable(ballot_full_state_payload(result.ballot)), load_schema("ballot.schema.json")
    )


def test_ballot_unknown_status_is_rejected_by_schema() -> None:
    schema = load_schema("ballot.schema.json")
    instance = {
        "ballot_id": str(uuid4()),
        "space_id": str(uuid4()),
        "subject_type": "initiative",
        "subject_id": str(uuid4()),
        "question": "Shall this pass?",
        "ballot_method": "yes_no",
        "secrecy_mode": "secret",
        "eligibility_rule_version": 1,
        "delegation_policy_version": 1,
        "quorum_rule": "none",
        "threshold_rule": "simple_majority",
        "opens_at": datetime(2026, 1, 1, tzinfo=UTC).isoformat(),
        "closes_at": datetime(2026, 1, 2, tzinfo=UTC).isoformat(),
        "status": "not_a_real_status",
        "configuration_hash": None,
        "challenge_window_hours": None,
    }
    with pytest.raises(SchemaValidationError):
        validate(instance, schema)


def test_vote_envelope_instance_validates_against_vote_envelope_schema(
    ballot_store: InMemoryBallotStore,
    ballot_option_store: InMemoryBallotOptionStore,
    vote_envelope_store: InMemoryVoteEnvelopeStore,
    audit_store: InMemoryAuditEventStore,
    credential_store: InMemoryCredentialStore,
    eligibility_rule_store: InMemoryEligibilityRuleStore,
    eligibility_snapshot_store: InMemoryEligibilitySnapshotStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    result = _cast_real_vote(
        ballot_store=ballot_store,
        option_store=ballot_option_store,
        envelope_store=vote_envelope_store,
        audit_store=audit_store,
        credential_store=credential_store,
        eligibility_rule_store=eligibility_rule_store,
        eligibility_snapshot_store=eligibility_snapshot_store,
        clock=clock,
        actor=actor,
    )
    validate(
        to_jsonable(vote_envelope_full_state_payload(result.envelope)),
        load_schema("vote-envelope.schema.json"),
    )


def test_vote_envelope_with_forbidden_identity_field_is_rejected() -> None:
    """CT-00-08/CT-00-09 structural backstop, mirroring
    `test_participation_credential_with_forbidden_identity_field_is_rejected`
    above."""
    schema = load_schema("vote-envelope.schema.json")
    instance = {
        "vote_envelope_id": str(uuid4()),
        "ballot_id": str(uuid4()),
        "credential_proof": str(uuid4()),
        "encrypted_or_encoded_choice": "yes",
        "submitted_at": datetime(2026, 1, 1, tzinfo=UTC).isoformat(),
        "integrity_hash": "a" * 64,
        "validation_status": "received",
        "included_in_tally": False,
        "account_id": str(uuid4()),  # forbidden - must be rejected
    }
    with pytest.raises(SchemaValidationError, match="account_id"):
        validate(instance, schema)


def test_initiative_instance_validates_against_initiative_schema(
    initiative_store: InMemoryInitiativeStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    result = create_initiative(
        initiative_store,
        audit_store,
        initiative_id=uuid4(),
        space_id=uuid4(),
        author_actor_id=uuid4(),
        initiative_type="civic_space",
        workflow_id=uuid4(),
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    validate(
        to_jsonable(initiative_full_state_payload(result.initiative)),
        load_schema("initiative.schema.json"),
    )


def test_delegation_instance_validates_against_delegation_schema(
    delegation_store: InMemoryDelegationStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    result = create_delegation(
        delegation_store,
        audit_store,
        delegation_id=uuid4(),
        delegator_actor_id=uuid4(),
        delegate_actor_id=uuid4(),
        scope_type="ballot",
        scope_id=uuid4(),
        valid_from=clock.now(),
        valid_until=None,
        revocation_status="not_revoked",
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    validate(
        to_jsonable(delegation_state_payload(result.delegation)),
        load_schema("delegation.schema.json"),
    )


def test_tally_instance_validates_against_tally_schema(
    tally_store: InMemoryTallyStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    result = start_tally(
        tally_store,
        audit_store,
        tally_id=uuid4(),
        ballot_id=uuid4(),
        input_set_hash="a" * 64,
        algorithm_version="1.0",
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    validate(to_jsonable(tally_full_state_payload(result.tally)), load_schema("tally.schema.json"))


def test_result_publication_instance_validates_against_schema(
    tally_store: InMemoryTallyStore,
    result_publication_store: InMemoryResultPublicationStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    ballot_id = uuid4()
    started = start_tally(
        tally_store,
        audit_store,
        tally_id=uuid4(),
        ballot_id=ballot_id,
        input_set_hash="a" * 64,
        algorithm_version="1.0",
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    ).tally
    completed = complete_tally(
        tally_store,
        audit_store,
        tally_id=started.tally_id,
        result_data={"yes": 10, "no": 5},
        invalid_vote_count=0,
        tally_signature=None,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    ).tally
    verified = verify_tally(
        tally_store,
        audit_store,
        tally_id=completed.tally_id,
        verification_passed=True,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    ).tally
    result = publish_result(
        tally_store,
        result_publication_store,
        audit_store,
        result_publication_id=uuid4(),
        ballot_id=ballot_id,
        tally_id=verified.tally_id,
        eligible_count=20,
        credential_count=18,
        accepted_vote_count=15,
        rejected_vote_count=0,
        quorum_threshold=None,
        option_counts={"yes": 10, "no": 5},
        challenge_window_hours=None,
        audit_package_reference="audit-ref-1",
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    validate(
        to_jsonable(result_publication_state_payload(result.result)),
        load_schema("result-publication.schema.json"),
    )
