"""PACK-15 event payload schemas, checked against the real builders.

The eight `contracts/events/pack15-*.v1.schema.json` files follow
`identity-event-payload.v1.schema.json`: one schema per **payload shape**,
not one per event type. PACK-15 emits far more event types than it has
payload shapes - the nine `eligibility.*` types share one shape, the ten
`voting_credential.*` types share three - so a per-type schema set would be
eight shapes copied thirty-odd times, and the copies would drift.

Each schema therefore names, in its own `description`, the builder that
produces it and the event types that use it. This module is the check that
those descriptions stay true: every payload here comes from the real
builder in `voting_trust_events` / `voting_credential_events`, applied to
real domain objects, never from a hand-written literal.

Three PACK-15 invariants are asserted at the schema level, where they hold
for every payload that ever validates rather than only for the payloads
this module happens to build:

* no schema declares an identity, ballot or credential-secret field;
* no schema declares both an assertion-side and a credential-side
  reference - ADR-093's pairing prohibition, expressed in the contract;
* every schema is `additionalProperties: false`, without which the two
  checks above would be advisory.

Validation here is structural and deliberately dependency-free
(`_assert_matches_schema`): `jsonschema` is not a guaranteed dependency of
this suite, and required-keys / no-unknown-keys / enum-range is exactly the
part of the contract these payloads are asserted against.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from _schema_helpers import EVENTS_DIR, load_event_schema, to_jsonable

from epd2_core.event_envelope import ActorRef, EventEnvelope
from epd2_credential_service.voting_credential_events import (
    CREDENTIAL_ISSUED,
    CREDENTIAL_REDEEMED,
    CREDENTIAL_REPLAY_REJECTED,
    VOTING_CREDENTIAL_EVENT_TYPES,
    build_credential_event,
    build_redemption_event,
    build_replay_event,
)
from epd2_credential_service.voting_credentials import (
    CredentialRedemption,
    CredentialReplayRecord,
    CredentialStatus,
    VotingCredential,
)
from epd2_eligibility_service.voting_assertion_issuer import (
    AssertionIssuer,
    MinimizedDecisionInput,
    SystemSecureRandom,
    TestKeyCustody,
)
from epd2_eligibility_service.voting_eligibility import (
    ASSERTION_RESULT_APPROVED,
    EligibilityAssertion,
    EligibilityCase,
    EligibilityCriterion,
    EligibilityDecision,
    EligibilityDecisionReason,
    EligibilityDecisionStatus,
    EligibilityRuleSetReference,
)
from epd2_eligibility_service.voting_timing import CohortSizeClass, IssuanceTimingProfile
from epd2_eligibility_service.voting_trust_events import (
    ALL_EVENT_TYPES,
    ASSERTION_MINTED,
    ASSERTION_QUEUED,
    CORRELATION_RISK_DETECTED,
    ELIGIBILITY_APPROVED,
    HANDOFF_ACCEPTED,
    build_assertion_event,
    build_eligibility_event,
    build_handoff_event,
    build_integrity_event,
    build_queue_event,
)

NOW = datetime(2026, 8, 1, 10, 7, 42, tzinfo=UTC)
AUDIENCE = "credential-issuer"
ORIGIN = "https://vote.epd.example"
GRANULARITY_SECONDS = 300

#: Every PACK-15 schema file, by the payload shape it describes.
ELIGIBILITY_SCHEMA = "pack15-eligibility-payload.v1.schema.json"
ASSERTION_SCHEMA = "pack15-assertion-payload.v1.schema.json"
QUEUE_SCHEMA = "pack15-assertion-queue-payload.v1.schema.json"
HANDOFF_SCHEMA = "pack15-handoff-acceptance-payload.v1.schema.json"
INTEGRITY_SCHEMA = "pack15-voting-boundary-integrity-payload.v1.schema.json"
CREDENTIAL_SCHEMA = "pack15-voting-credential-payload.v1.schema.json"
REDEMPTION_SCHEMA = "pack15-credential-redemption-payload.v1.schema.json"
REPLAY_SCHEMA = "pack15-credential-replay-payload.v1.schema.json"

PACK15_SCHEMA_NAMES: tuple[str, ...] = (
    ELIGIBILITY_SCHEMA,
    ASSERTION_SCHEMA,
    QUEUE_SCHEMA,
    HANDOFF_SCHEMA,
    INTEGRITY_SCHEMA,
    CREDENTIAL_SCHEMA,
    REDEMPTION_SCHEMA,
    REPLAY_SCHEMA,
)

#: Never a declared property of any PACK-15 event payload schema. The union
#: of `voting_eligibility.FORBIDDEN_FIELD_NAMES` and
#: `voting_credentials.FORBIDDEN_FIELD_NAMES`, plus the two secrets that are
#: handed to a client but are not audit facts (`credential_secret`,
#: `continuation_capability`) and the two pseudonym spellings.
SCHEMA_FORBIDDEN_PROPERTY_NAMES: frozenset[str] = frozenset(
    {
        "account_id",
        "person_id",
        "person_record_id",
        "identity_record_id",
        "membership_id",
        "member_number",
        "email",
        "phone",
        "full_name",
        "date_of_birth",
        "address",
        "communication_persona_id",
        "eid_subject",
        "ballot_id",
        "vote_content",
        "credential_secret",
        "continuation_capability",
        "context_pseudonym",
        "pseudonym",
    }
)

#: ADR-093's pairing prohibition, at the level of a schema's property set.
ASSERTION_SIDE_PROPERTY_NAMES: frozenset[str] = frozenset({"assertion_id", "nonce"})
CREDENTIAL_SIDE_PROPERTY_NAMES: frozenset[str] = frozenset(
    {"voting_credential_id", "credential_id"}
)


# ---------------------------------------------------------------------------
# A dependency-free structural validator
# ---------------------------------------------------------------------------

_JSON_TYPES: dict[str, type | tuple[type, ...]] = {
    "string": str,
    "boolean": bool,
    "object": dict,
    "array": list,
    "integer": int,
    "number": (int, float),
}


def _assert_matches_schema(payload: dict[str, Any], schema: dict[str, Any]) -> None:
    """Structurally validate `payload` against `schema` without jsonschema.

    Checks exactly the three properties the PACK-15 contract turns on:
    every `required` key is present, no key outside `properties` appears
    (which is what `additionalProperties: false` means for a payload), and
    every declared `enum` value is in range. Declared JSON types are
    checked too, since that is free once the property is located.
    """
    properties = schema["properties"]
    for name in schema["required"]:
        assert name in payload, f"required property {name!r} is missing from the built payload"
    unknown = sorted(set(payload) - set(properties))
    assert not unknown, f"payload carries undeclared propert(ies): {unknown}"
    for name, value in payload.items():
        declared = properties[name]
        expected = _JSON_TYPES.get(declared.get("type", ""))
        if expected is not None:
            # `bool` is a subclass of `int`; a boolean is never an integer here.
            assert isinstance(value, expected) and not (
                expected is not bool and isinstance(value, bool)
            ), f"{name}={value!r} is not of declared type {declared['type']!r}"
        if "enum" in declared:
            assert value in declared["enum"], (
                f"{name}={value!r} is outside the declared enum {declared['enum']}"
            )
        if declared.get("type") == "array" and "items" in declared:
            item_type = _JSON_TYPES.get(declared["items"].get("type", ""))
            if item_type is not None:
                for item in value:
                    assert isinstance(item, item_type), f"{name} item {item!r} has the wrong type"
        if declared.get("type") == "object" and isinstance(
            declared.get("additionalProperties"), dict
        ):
            value_type = _JSON_TYPES.get(declared["additionalProperties"].get("type", ""))
            if value_type is not None:
                for key, item in value.items():
                    assert isinstance(item, value_type), (
                        f"{name}[{key!r}]={item!r} has the wrong type"
                    )


# ---------------------------------------------------------------------------
# Real domain objects, mirroring the two services' own PACK-15 unit tests
# ---------------------------------------------------------------------------


def _actor() -> ActorRef:
    return ActorRef(actor_id=uuid4(), actor_type="service")


def _case() -> EligibilityCase:
    return EligibilityCase(
        case_id=uuid4(),
        voting_context_reference="vc-1",
        participant_reference="participant-1",
        participation_class="full_member",
        requested_at=NOW,
        status=EligibilityDecisionStatus.APPROVED,
        assisted_by="assistant-1",
    )


def _decision(case: EligibilityCase) -> EligibilityDecision:
    return EligibilityDecision(
        decision_id=uuid4(),
        case_id=case.case_id,
        voting_context_reference=case.voting_context_reference,
        status=EligibilityDecisionStatus.APPROVED,
        rule_set=EligibilityRuleSetReference(
            rule_set_id="rs-1",
            rule_set_version="1.0.0",
            declared_attribute_names=frozenset({"membership_status"}),
            criteria=(EligibilityCriterion.MEMBERSHIP_STATUS,),
        ),
        source_versions={"membership": "2026-08-01T00:00:00+00:00"},
        reasons=(
            EligibilityDecisionReason(
                reason_code="ELIGIBILITY_APPROVED",
                criterion=EligibilityCriterion.MEMBERSHIP_STATUS,
            ),
        ),
        eligibility_class="full_member",
        organizational_scope="DE-BE-01",
        required_assurance_satisfied=True,
        decided_at=NOW,
        valid_until=NOW + timedelta(hours=8),
    )


def _issuer() -> AssertionIssuer:
    return AssertionIssuer(
        custody=TestKeyCustody(),
        random=SystemSecureRandom(),
        profile=IssuanceTimingProfile(),
        audience=AUDIENCE,
    )


def _assertion() -> EligibilityAssertion:
    return _issuer().mint(
        assertion_id=uuid4(),
        decision=MinimizedDecisionInput(
            voting_context_reference="vc-1",
            eligibility_result=ASSERTION_RESULT_APPROVED,
            eligibility_class="full_member",
            organizational_scope="DE-BE-01",
            required_assurance_satisfied=True,
        ),
        now=NOW,
        expires_at=NOW + timedelta(hours=4),
        eligible_population=800,
    )


def _credential() -> VotingCredential:
    return VotingCredential(
        voting_credential_id=uuid4(),
        credential_type="internal_party_vote",
        status=CredentialStatus.ISSUED,
        voting_context_reference="vc-1",
        issued_at_bucket=NOW,
        expires_at=NOW + timedelta(hours=2),
        audience_origin=ORIGIN,
    )


def _eligibility_event() -> EventEnvelope:
    case = _case()
    return build_eligibility_event(
        event_id=uuid4(),
        event_type=ELIGIBILITY_APPROVED,
        case=case,
        decision=_decision(case),
        actor=_actor(),
        correlation_id=uuid4(),
        causation_id=None,
        occurred_at=NOW,
    )


def _assertion_event() -> EventEnvelope:
    return build_assertion_event(
        event_id=uuid4(),
        event_type=ASSERTION_MINTED,
        assertion=_assertion(),
        granularity_seconds=GRANULARITY_SECONDS,
        actor=_actor(),
        correlation_id=uuid4(),
        causation_id=None,
        occurred_at=NOW,
    )


def _queue_event() -> EventEnvelope:
    issuer = _issuer()
    entry = issuer.enqueue(_assertion(), batch_reference="b1", now=NOW, jitter_fraction=0.5)
    return build_queue_event(
        event_id=uuid4(),
        event_type=ASSERTION_QUEUED,
        entry=entry,
        cohort_size_class=CohortSizeClass.AT_MINIMUM,
        granularity_seconds=GRANULARITY_SECONDS,
        actor=_actor(),
        correlation_id=uuid4(),
        causation_id=None,
        occurred_at=NOW,
    )


def _handoff_event() -> EventEnvelope:
    return build_handoff_event(
        event_id=uuid4(),
        event_type=HANDOFF_ACCEPTED,
        acceptance_id=uuid4(),
        voting_context_reference="vc-1",
        audience=AUDIENCE,
        origin=ORIGIN,
        reason_code="HANDOFF_ACCEPTED",
        actor=_actor(),
        correlation_id=uuid4(),
        causation_id=None,
        occurred_at=NOW,
    )


def _integrity_event() -> EventEnvelope:
    return build_integrity_event(
        event_id=uuid4(),
        event_type=CORRELATION_RISK_DETECTED,
        detection_id=uuid4(),
        voting_context_reference="vc-1",
        risk_class="timing_correlation",
        severity="high",
        reason_code="CORRELATION_RISK_DETECTED",
        actor=_actor(),
        correlation_id=uuid4(),
        causation_id=None,
        occurred_at=NOW,
    )


def _credential_event() -> EventEnvelope:
    return build_credential_event(
        event_id=uuid4(),
        event_type=CREDENTIAL_ISSUED,
        credential=_credential(),
        reason_code="CREDENTIAL_ISSUANCE_AUTHORIZED",
        granularity_seconds=GRANULARITY_SECONDS,
        correlation_id=uuid4(),
        occurred_at=NOW,
    )


def _redemption_event() -> EventEnvelope:
    credential = _credential()
    return build_redemption_event(
        event_id=uuid4(),
        redemption=CredentialRedemption(
            redemption_reference="redemption-1",
            voting_credential_id=credential.voting_credential_id,
            voting_context_reference=credential.voting_context_reference,
            redeemed_at_bucket=NOW,
            continuation_capability="continuation-capability-1",
        ),
        correlation_id=uuid4(),
    )


def _replay_event() -> EventEnvelope:
    return build_replay_event(
        event_id=uuid4(),
        event_type=CREDENTIAL_REPLAY_REJECTED,
        replay=CredentialReplayRecord(
            replay_id=uuid4(),
            voting_context_reference="vc-1",
            reason_code="CREDENTIAL_REPLAY_DETECTED",
            detected_at_bucket=NOW,
        ),
        correlation_id=uuid4(),
        occurred_at=NOW,
    )


#: (schema file, builder, expected producer, the module's exported type
#: tuple) for every PACK-15 payload shape.
BUILT_EVENTS: tuple[tuple[str, Callable[[], EventEnvelope], str, tuple[str, ...]], ...] = (
    (ELIGIBILITY_SCHEMA, _eligibility_event, "eligibility-service", ALL_EVENT_TYPES),
    (ASSERTION_SCHEMA, _assertion_event, "eligibility-service", ALL_EVENT_TYPES),
    (QUEUE_SCHEMA, _queue_event, "eligibility-service", ALL_EVENT_TYPES),
    (HANDOFF_SCHEMA, _handoff_event, "eligibility-service", ALL_EVENT_TYPES),
    (INTEGRITY_SCHEMA, _integrity_event, "eligibility-service", ALL_EVENT_TYPES),
    (
        CREDENTIAL_SCHEMA,
        _credential_event,
        "credential-service",
        VOTING_CREDENTIAL_EVENT_TYPES,
    ),
    (
        REDEMPTION_SCHEMA,
        _redemption_event,
        "credential-service",
        VOTING_CREDENTIAL_EVENT_TYPES,
    ),
    (REPLAY_SCHEMA, _replay_event, "credential-service", VOTING_CREDENTIAL_EVENT_TYPES),
)


# ---------------------------------------------------------------------------
# Payload <-> schema
# ---------------------------------------------------------------------------


def test_every_built_payload_validates_against_its_schema() -> None:
    """The real builders' output, checked shape by shape - so a builder
    that gains a field without the schema gaining it fails here."""
    for schema_name, build, _producer, _types in BUILT_EVENTS:
        schema = load_event_schema(schema_name)
        payload = to_jsonable(build().payload)
        _assert_matches_schema(payload, schema)


def test_an_optional_eligibility_payload_omits_the_decision_properties() -> None:
    """`build_eligibility_event` takes `decision=None` before a decision
    exists. The four required properties are still present; the six
    decision-derived ones are simply absent, which is why the schema marks
    them optional rather than required."""
    schema = load_event_schema(ELIGIBILITY_SCHEMA)
    event = build_eligibility_event(
        event_id=uuid4(),
        event_type=ELIGIBILITY_APPROVED,
        case=_case(),
        decision=None,
        actor=_actor(),
        correlation_id=uuid4(),
        causation_id=None,
        occurred_at=NOW,
    )
    payload = to_jsonable(event.payload)
    _assert_matches_schema(payload, schema)
    assert "decision_id" not in payload
    assert "status" not in payload


def test_a_revoked_credential_payload_carries_the_optional_revocation_reason() -> None:
    """The one optional property of the credential shape, exercised - so
    `revocation_reason` is proven declared, not merely absent."""
    schema = load_event_schema(CREDENTIAL_SCHEMA)
    credential = VotingCredential(
        voting_credential_id=uuid4(),
        credential_type="internal_party_vote",
        status=CredentialStatus.REVOKED,
        voting_context_reference="vc-1",
        issued_at_bucket=NOW,
        expires_at=NOW + timedelta(hours=2),
        revoked_at=NOW + timedelta(minutes=10),
        revocation_reason="CREDENTIAL_REVOKED",
        audience_origin=ORIGIN,
    )
    event = build_credential_event(
        event_id=uuid4(),
        event_type=CREDENTIAL_ISSUED,
        credential=credential,
        reason_code="CREDENTIAL_REVOKED",
        granularity_seconds=GRANULARITY_SECONDS,
        correlation_id=uuid4(),
        occurred_at=NOW,
    )
    payload = to_jsonable(event.payload)
    _assert_matches_schema(payload, schema)
    assert payload["revocation_reason"] == "CREDENTIAL_REVOKED"


def test_the_validator_rejects_a_payload_the_schema_forbids() -> None:
    """Negative-space check for `_assert_matches_schema` itself: a helper
    that accepted everything would make every test above vacuous."""
    schema = load_event_schema(REDEMPTION_SCHEMA)
    payload = to_jsonable(_redemption_event().payload)

    with_extra = dict(payload, continuation_capability="secret")
    try:
        _assert_matches_schema(with_extra, schema)
    except AssertionError:
        pass
    else:
        raise AssertionError("an undeclared property was accepted")

    without_required = {k: v for k, v in payload.items() if k != "redemption_reference"}
    try:
        _assert_matches_schema(without_required, schema)
    except AssertionError:
        pass
    else:
        raise AssertionError("a missing required property was accepted")

    bad_enum = dict(to_jsonable(_credential_event().payload), status="not_a_status")
    try:
        _assert_matches_schema(bad_enum, load_event_schema(CREDENTIAL_SCHEMA))
    except AssertionError:
        pass
    else:
        raise AssertionError("an out-of-range enum value was accepted")


# ---------------------------------------------------------------------------
# Schema-level invariants
# ---------------------------------------------------------------------------


def _pack15_schema_files() -> list[tuple[str, dict[str, Any]]]:
    files = sorted(EVENTS_DIR.glob("pack15-*.json"))
    assert files, "expected the PACK-15 event payload schemas to exist"
    return [(path.name, json.loads(path.read_text(encoding="utf-8"))) for path in files]


def test_every_pack15_schema_file_is_present_and_well_formed() -> None:
    found = {name for name, _ in _pack15_schema_files()}
    assert found == set(PACK15_SCHEMA_NAMES), f"unexpected PACK-15 schema file set: {sorted(found)}"
    for name, schema in _pack15_schema_files():
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema["$id"] == f"https://epd2.example/contracts/events/{name}"
        assert schema["type"] == "object"
        assert schema["title"]
        assert schema["description"]
        assert set(schema["required"]) <= set(schema["properties"])


def test_every_pack15_schema_forbids_additional_properties() -> None:
    """Without this, the two prohibitions below would be advisory: a
    payload could carry an identity field and still validate."""
    for name, schema in _pack15_schema_files():
        assert schema["additionalProperties"] is False, (
            f"{name} must set additionalProperties: false"
        )


def test_no_pack15_schema_declares_an_identity_or_secret_property() -> None:
    for name, schema in _pack15_schema_files():
        leaked = sorted(set(schema["properties"]) & SCHEMA_FORBIDDEN_PROPERTY_NAMES)
        assert not leaked, f"{name} declares forbidden propert(ies): {leaked}"


def test_no_pack15_schema_pairs_an_assertion_with_a_credential_reference() -> None:
    """ADR-093 at the level of the contract: a schema that declared both
    would license a payload carrying the link the whole boundary exists to
    prevent - regardless of whether any builder ever produced one."""
    for name, schema in _pack15_schema_files():
        declared = set(schema["properties"])
        assert not (declared & ASSERTION_SIDE_PROPERTY_NAMES) or not (
            declared & CREDENTIAL_SIDE_PROPERTY_NAMES
        ), (
            f"{name} declares both an assertion-side reference "
            f"({sorted(declared & ASSERTION_SIDE_PROPERTY_NAMES)}) and a credential-side "
            f"reference ({sorted(declared & CREDENTIAL_SIDE_PROPERTY_NAMES)})"
        )


def test_the_redemption_schema_cannot_carry_the_continuation_capability() -> None:
    """Stated on its own, because it is the one field a redemption record
    really holds and really must not publish."""
    schema = load_event_schema(REDEMPTION_SCHEMA)
    assert "continuation_capability" not in schema["properties"]
    assert schema["additionalProperties"] is False


# ---------------------------------------------------------------------------
# Canonical envelope compatibility (PACK-13, canon section 21)
# ---------------------------------------------------------------------------


def test_every_built_envelope_is_canonical() -> None:
    for schema_name, build, producer, event_types in BUILT_EVENTS:
        envelope = build()
        assert envelope.event_version == "1.0", f"{schema_name}: unexpected event_version"
        assert envelope.occurred_at.tzinfo is not None, f"{schema_name}: naive occurred_at"
        assert envelope.producer == producer, f"{schema_name}: unexpected producer"
        assert envelope.integrity.payload_hash, f"{schema_name}: empty payload_hash"
        assert envelope.event_type in event_types, (
            f"{schema_name}: {envelope.event_type} is not an exported PACK-15 event type"
        )


def test_the_redemption_event_type_is_fixed_by_its_builder() -> None:
    """`build_redemption_event` takes no `event_type`: the shape and the
    type are one-to-one, which is what the schema's description claims."""
    assert _redemption_event().event_type == CREDENTIAL_REDEEMED
