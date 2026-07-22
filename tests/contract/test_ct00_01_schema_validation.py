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
from epd2_eligibility_service.application import create_eligibility_rule
from epd2_eligibility_service.storage import InMemoryEligibilityRuleStore
from epd2_identity_service.application import start_identity_verification
from epd2_identity_service.events import identity_record_payload
from epd2_identity_service.storage import InMemoryIdentityRecordStore


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
