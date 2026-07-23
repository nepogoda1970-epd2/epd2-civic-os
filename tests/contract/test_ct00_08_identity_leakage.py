"""CT-00-08 Identity Leakage (canon section 27) and the pack's identity-
leakage suite (pack section 12.2): a participation response never
contains identity fields.

Checked here, per pack section 12.2's explicit list:
- credential schema does not contain forbidden identity fields;
- credential events do not contain identity fields;
- validation result does not contain identity fields;
- the OpenAPI contract's credential-service-tagged paths (and the schemas
  they `$ref`) do not reference identity fields - scoped to
  credential-service only, since other services' paths (identity-service's
  `/identity/verifications`, in particular) legitimately reference their
  own canonical fields such as `identity_record_id`;
- the audit event *payload* for credential operations does not contain
  identity claims (only structural target_type/target_id references);
- a serialized credential cannot be linked to an account or identity
  record through an explicit ID (no shared identifier field at all).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from _schema_helpers import (
    OPENAPI_PATH,
    PACK03_OPENAPI_PATH,
    load_event_schema,
    load_schema,
    to_jsonable,
)

from epd2_audit_core.storage import InMemoryAuditEventStore
from epd2_core.clock import FixedClock
from epd2_core.event_envelope import ActorRef
from epd2_credential_service.application import (
    IssueResult,
    issue_participation_credential,
    revoke_participation_credential,
    validate_participation_credential,
)
from epd2_credential_service.domain import FORBIDDEN_FIELD_NAMES, CredentialType
from epd2_credential_service.events import credential_full_state_payload
from epd2_credential_service.storage import InMemoryCredentialStore
from epd2_delegation_service.domain import FORBIDDEN_FIELD_NAMES as DELEGATION_FORBIDDEN
from epd2_initiative_service.domain import FORBIDDEN_FIELD_NAMES as SUPPORT_FORBIDDEN
from epd2_tally_service.domain import FORBIDDEN_FIELD_NAMES as TALLY_FORBIDDEN
from epd2_voting_service.domain import FORBIDDEN_FIELD_NAMES as VOTING_FORBIDDEN


def _issue(
    credential_store: InMemoryCredentialStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
    **overrides: object,
) -> IssueResult:
    defaults = dict(
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
    defaults.update(overrides)
    return issue_participation_credential(
        credential_store,
        audit_store,
        **defaults,  # type: ignore[arg-type]
    )


def test_credential_schema_forbids_identity_fields() -> None:
    schema = load_schema("participation-credential.schema.json")
    assert schema["additionalProperties"] is False
    for forbidden in FORBIDDEN_FIELD_NAMES:
        assert forbidden not in schema["properties"]


def test_credential_issued_event_payload_has_no_identity_fields(
    credential_store: InMemoryCredentialStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    result = _issue(credential_store, audit_store, actor, clock)
    payload_text = json.dumps(to_jsonable(result.event.payload))
    for forbidden in FORBIDDEN_FIELD_NAMES:
        assert forbidden not in payload_text


def test_credential_revoked_event_payload_has_no_identity_fields(
    credential_store: InMemoryCredentialStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    issued = _issue(credential_store, audit_store, actor, clock)
    result = revoke_participation_credential(
        credential_store,
        audit_store,
        credential_id=issued.credential.credential_id,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        causation_id=None,
        clock=clock,
    )
    payload_text = json.dumps(to_jsonable(result.event.payload))
    for forbidden in FORBIDDEN_FIELD_NAMES:
        assert forbidden not in payload_text


def test_credential_event_payload_schemas_forbid_identity_fields() -> None:
    for name in (
        "credential-issued-or-revoked-payload.v1.schema.json",
        "credential-validation-failed-payload.v1.schema.json",
    ):
        schema = load_event_schema(name)
        assert schema["additionalProperties"] is False
        for forbidden in FORBIDDEN_FIELD_NAMES:
            assert forbidden not in schema["properties"]


def test_validation_result_has_no_identity_fields(
    credential_store: InMemoryCredentialStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    issued = _issue(credential_store, audit_store, actor, clock)
    result = validate_participation_credential(
        credential_store,
        credential_id=issued.credential.credential_id,
        required_scope_type=None,
        required_scope_id=None,
        expected_rule_version=None,
        expected_digest=None,
        actor=actor,
        correlation_id=uuid4(),
        clock=clock,
    )
    field_names = set(result.result.__dataclass_fields__)
    assert not (field_names & FORBIDDEN_FIELD_NAMES)


def test_audit_event_payload_for_credential_operations_has_no_identity_claims(
    credential_store: InMemoryCredentialStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    """The AuditEvent itself (docs/canonical/TZ-00-domain-event-canon.md,
    section 18.1) only ever carries structural target_type/target_id
    references (e.g. "participation_credential" + a credential UUID) -
    never an identity claim such as a name, email, or identity_record_id."""
    result = _issue(credential_store, audit_store, actor, clock)
    audit_event = result.audit_event
    assert audit_event.target_type == "participation_credential"
    # The audit entry's own hashed state snapshot (before/after) is
    # derived from credential_full_state_payload, which structurally
    # cannot contain identity fields either.
    state_text = json.dumps(to_jsonable(credential_full_state_payload(result.credential)))
    for forbidden in FORBIDDEN_FIELD_NAMES:
        assert forbidden not in state_text


def test_serialized_credential_has_no_id_shared_with_identity_or_account(
    credential_store: InMemoryCredentialStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    """A serialized credential cannot be linked to an account or identity
    record via an explicit shared identifier - the only IDs present are
    the credential's own (credential_id, scope_id), neither of which is
    ever an account_id or identity_record_id (structural boundary, see
    services/credential-service/README.md)."""
    result = _issue(credential_store, audit_store, actor, clock)
    payload = to_jsonable(credential_full_state_payload(result.credential))
    assert set(payload) & {"account_id", "identity_record_id", "person_id"} == set()


def _credential_service_paths(
    spec: dict[str, object], service_tag: str = "credential-service"
) -> dict[str, object]:
    """The subset of the OpenAPI `paths` mapping owned by `service_tag`
    (`tags: [service_tag]` on at least one HTTP method) - CT-00-08 is
    about a given service's own responses never leaking identity fields,
    not about every path in the shared, multi-service contract. Other
    services' paths (e.g. identity-service's `/identity/verifications`)
    legitimately reference fields such as `identity_record_id`, since
    that is their own canonical primary key, not a leak into a
    participation artifact.

    Generalized (PACK-03) from a credential-service-only helper: the
    original name is kept (existing PACK-02 call sites below rely on the
    `service_tag="credential-service"` default and pass no second
    argument, so they are completely unaffected) rather than introducing
    a same-shaped second helper under a new name, since the body is
    identical for every service - only the tag string differs."""
    paths = spec.get("paths", {})
    assert isinstance(paths, dict)
    result: dict[str, object] = {}
    for path, item in paths.items():
        assert isinstance(item, dict)
        operations = [op for op in item.values() if isinstance(op, dict)]
        if any(service_tag in (op.get("tags") or []) for op in operations):
            result[path] = item
    return result


def _referenced_local_schema_names(node: object, found: set[str]) -> None:
    """Recursively collect the basenames of every local `../schemas/*.json`
    `$ref` reachable from `node`, so a credential-service path's response
    schema (e.g. `participation-credential.schema.json`) is checked too,
    not just the inline path/operation text."""
    if isinstance(node, dict):
        ref = node.get("$ref")
        if isinstance(ref, str) and ref.startswith("../schemas/"):
            found.add(ref.rsplit("/", 1)[-1])
        for value in node.values():
            _referenced_local_schema_names(value, found)
    elif isinstance(node, list):
        for item in node:
            _referenced_local_schema_names(item, found)


def _declared_property_names(node: object, names: set[str]) -> None:
    """Recursively collect the keys of every JSON-Schema `properties`
    mapping reachable from `node` - i.e. actual declared field names, not
    arbitrary text. A naive full-text/substring scan of the serialized
    spec is the wrong shape for this check: this schema file's own
    `description` legitimately *names* every forbidden field in prose
    (`participation-credential.schema.json`'s description literally reads
    "...identity_record_id, person_id, account_id, ... are all forbidden
    and cannot appear...", to document the `additionalProperties: false`
    guarantee) - a substring match over that text is a false positive in
    the opposite direction from the bug this test is fixing. Checking
    structural `properties` keys instead - the same approach already used
    by `test_credential_schema_forbids_identity_fields` and
    `test_credential_event_payload_schemas_forbid_identity_fields` above -
    catches only an actual declared field, exactly what CT-00-08 cares
    about."""
    if isinstance(node, dict):
        properties = node.get("properties")
        if isinstance(properties, dict):
            names.update(properties)
        for value in node.values():
            _declared_property_names(value, names)
    elif isinstance(node, list):
        for item in node:
            _declared_property_names(item, names)


def test_openapi_credential_responses_do_not_reference_identity_fields() -> None:
    """CT-00-08 / pack section 12.2: credential-service's own OpenAPI paths
    - and the schemas they `$ref` to - never *declare* a forbidden identity
    field as an actual property. Scoped to credential-service only (see
    `_credential_service_paths`) so that other services' legitimate use of
    their own identity fields (e.g. identity-service's `identity_record_id`)
    is not a false positive; see
    `test_identity_service_paths_may_reference_identity_record_id` below
    for the explicit, positive counterpart proving that scoping is real
    and not just vacuously narrow. Checks declared `properties` keys, not
    a full-text substring scan (see `_declared_property_names` for why a
    substring scan is itself a false-positive trap here)."""
    pytest.importorskip("yaml")
    import yaml

    spec = yaml.safe_load(OPENAPI_PATH.read_text(encoding="utf-8"))
    credential_paths = _credential_service_paths(spec)
    assert credential_paths, "expected at least one credential-service-tagged OpenAPI path"

    referenced_schema_names: set[str] = set()
    _referenced_local_schema_names(credential_paths, referenced_schema_names)

    declared: set[str] = set()
    _declared_property_names(credential_paths, declared)
    for name in referenced_schema_names:
        _declared_property_names(load_schema(name), declared)

    leaked = declared & FORBIDDEN_FIELD_NAMES
    assert leaked == set(), (
        f"credential-service OpenAPI paths/schemas declare forbidden identity "
        f"field(s) as an actual property: {sorted(leaked)}"
    )


def test_identity_service_paths_may_reference_identity_record_id() -> None:
    """Negative-space check for the scoping above: identity-service's own
    OpenAPI path legitimately declares `identity_record_id` (its own
    canonical primary key, docs/canonical/TZ-00-domain-event-canon.md
    section 22's ownership matrix) and must NOT be flagged or stripped by
    CT-00-08 - that field only becomes forbidden in a *credential/
    participation*-facing artifact, never in identity-service's own
    contract. This proves `_credential_service_paths` truly excludes
    identity-service rather than the previous (buggy) whole-spec scan
    happening to still pass."""
    pytest.importorskip("yaml")
    import yaml

    spec = yaml.safe_load(OPENAPI_PATH.read_text(encoding="utf-8"))
    identity_path = spec["paths"]["/identity/verifications"]
    identity_path_text = json.dumps(identity_path)
    assert "identity_record_id" in identity_path_text


# =============================================================================
# PACK-03: the generalized `_credential_service_paths(spec, service_tag)`
# helper exercised against `pack-03.yaml` for voting-service, tally-service,
# and initiative-service, plus schema-forbids-identity-fields tests for the
# six PACK-03 entities each own an identity-separation guarantee for
# (VoteEnvelope, VoteReceipt, Tally, ResultPublication, SupportRecord,
# Delegation) - mirroring `test_credential_schema_forbids_identity_fields`
# above exactly.
# =============================================================================


def test_vote_envelope_schema_forbids_identity_fields() -> None:
    schema = load_schema("vote-envelope.schema.json")
    assert schema["additionalProperties"] is False
    for forbidden in VOTING_FORBIDDEN:
        assert forbidden not in schema["properties"]


def test_vote_receipt_schema_forbids_identity_fields() -> None:
    schema = load_schema("vote-receipt.schema.json")
    assert schema["additionalProperties"] is False
    for forbidden in VOTING_FORBIDDEN:
        assert forbidden not in schema["properties"]


def test_tally_schema_forbids_identity_fields() -> None:
    schema = load_schema("tally.schema.json")
    assert schema["additionalProperties"] is False
    for forbidden in TALLY_FORBIDDEN:
        assert forbidden not in schema["properties"]


def test_result_publication_schema_forbids_identity_fields() -> None:
    schema = load_schema("result-publication.schema.json")
    assert schema["additionalProperties"] is False
    for forbidden in TALLY_FORBIDDEN:
        assert forbidden not in schema["properties"]


def test_support_record_schema_forbids_identity_fields() -> None:
    schema = load_schema("support-record.schema.json")
    assert schema["additionalProperties"] is False
    for forbidden in SUPPORT_FORBIDDEN:
        assert forbidden not in schema["properties"]


def test_delegation_schema_forbids_identity_fields() -> None:
    schema = load_schema("delegation.schema.json")
    assert schema["additionalProperties"] is False
    for forbidden in DELEGATION_FORBIDDEN:
        assert forbidden not in schema["properties"]


def _pack03_spec() -> dict[str, object]:
    pytest.importorskip("yaml")
    import yaml

    loaded: dict[str, object] = yaml.safe_load(PACK03_OPENAPI_PATH.read_text(encoding="utf-8"))
    return loaded


def test_openapi_voting_responses_do_not_reference_identity_fields() -> None:
    spec = _pack03_spec()
    voting_paths = _credential_service_paths(spec, service_tag="voting-service")
    assert voting_paths, "expected at least one voting-service-tagged OpenAPI path"

    referenced_schema_names: set[str] = set()
    _referenced_local_schema_names(voting_paths, referenced_schema_names)

    declared: set[str] = set()
    _declared_property_names(voting_paths, declared)
    for name in referenced_schema_names:
        _declared_property_names(load_schema(name), declared)

    leaked = declared & VOTING_FORBIDDEN
    assert leaked == set(), (
        f"voting-service OpenAPI paths/schemas declare forbidden identity "
        f"field(s) as an actual property: {sorted(leaked)}"
    )


def test_openapi_tally_responses_do_not_reference_identity_fields() -> None:
    spec = _pack03_spec()
    tally_paths = _credential_service_paths(spec, service_tag="tally-service")
    assert tally_paths, "expected at least one tally-service-tagged OpenAPI path"

    referenced_schema_names: set[str] = set()
    _referenced_local_schema_names(tally_paths, referenced_schema_names)

    declared: set[str] = set()
    _declared_property_names(tally_paths, declared)
    for name in referenced_schema_names:
        _declared_property_names(load_schema(name), declared)

    leaked = declared & TALLY_FORBIDDEN
    assert leaked == set(), (
        f"tally-service OpenAPI paths/schemas declare forbidden identity "
        f"field(s) as an actual property: {sorted(leaked)}"
    )


def test_openapi_initiative_responses_do_not_reference_identity_fields() -> None:
    spec = _pack03_spec()
    initiative_paths = _credential_service_paths(spec, service_tag="initiative-service")
    assert initiative_paths, "expected at least one initiative-service-tagged OpenAPI path"

    referenced_schema_names: set[str] = set()
    _referenced_local_schema_names(initiative_paths, referenced_schema_names)

    declared: set[str] = set()
    _declared_property_names(initiative_paths, declared)
    for name in referenced_schema_names:
        _declared_property_names(load_schema(name), declared)

    leaked = declared & SUPPORT_FORBIDDEN
    assert leaked == set(), (
        f"initiative-service OpenAPI paths/schemas declare forbidden identity "
        f"field(s) as an actual property: {sorted(leaked)}"
    )
