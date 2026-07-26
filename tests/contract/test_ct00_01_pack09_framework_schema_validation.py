"""CT-00-01 Schema Validation (canon section 27), Architecture & Domain
Framework 0.8.1 additions to PACK-09 - added alongside (never replacing)
`test_ct00_01_pack09_schema_validation.py`'s round-1 coverage, following
the same precedent that file itself set.

Validates every Framework-0.8.1 entity schema under `contracts/schemas/`
and every new event payload schema under `contracts/events/` against
real, directly-constructed domain instances and real event envelopes
built by `epd2_compliance_service.events`. Every instance satisfies every
structural `__post_init__` invariant its class enforces - nothing here is
a mock. A schema that drifted from the code it documents fails here
rather than in production.

Requires nothing beyond `epd2_core.minimal_json_schema` (always
available, stdlib-only) for validation itself.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from _pack09_framework_samples import entity_samples, event_samples, to_wire
from _schema_helpers import (
    envelope_to_jsonable,
    load_event_schema,
    load_schema,
    to_jsonable,
)

from epd2_core.event_envelope import EventEnvelope
from epd2_core.minimal_json_schema import validate

_ENTITY_SAMPLES = entity_samples()
_EVENT_SAMPLES = event_samples()

_CONTRACTS = Path(__file__).resolve().parents[2] / "contracts"


@pytest.mark.parametrize("stem", sorted(_ENTITY_SAMPLES), ids=sorted(_ENTITY_SAMPLES))
def test_entity_instance_validates_against_its_schema(stem: str) -> None:
    """Every Framework-0.8.1 entity schema accepts a real instance of the
    dataclass it documents."""
    schema = load_schema(f"{stem}.schema.json")
    validate(to_wire(_ENTITY_SAMPLES[stem]), schema)


@pytest.mark.parametrize("stem", sorted(_EVENT_SAMPLES), ids=sorted(_EVENT_SAMPLES))
def test_event_payload_validates_against_its_schema(stem: str) -> None:
    """Every new event payload schema accepts the payload its own builder
    actually produces."""
    schema = load_event_schema(f"{stem}.v1.schema.json")
    validate(to_jsonable(_EVENT_SAMPLES[stem].payload), schema)


@pytest.mark.parametrize("stem", sorted(_EVENT_SAMPLES), ids=sorted(_EVENT_SAMPLES))
def test_event_envelope_validates_against_the_canonical_envelope_schema(stem: str) -> None:
    """Each new event is a canonical envelope, not a bespoke shape."""
    schema = load_schema("event-envelope.schema.json")
    validate(envelope_to_jsonable(_EVENT_SAMPLES[stem]), schema)


def _all_new_schema_paths() -> list[Path]:
    paths = [_CONTRACTS / "schemas" / f"{stem}.schema.json" for stem in _ENTITY_SAMPLES]
    paths += [_CONTRACTS / "events" / f"{stem}.v1.schema.json" for stem in _EVENT_SAMPLES]
    return paths


@pytest.mark.parametrize(
    "path", _all_new_schema_paths(), ids=[p.name for p in _all_new_schema_paths()]
)
def test_schema_is_closed_and_self_describing(path: Path) -> None:
    """Structural rules every schema in this repository follows: draft
    2020-12, a stable `$id`, a title, a non-trivial description, closed
    objects (`additionalProperties: false`) and an explicit `required`
    list.

    `additionalProperties: false` is the load-bearing one. An open schema
    would silently accept a payload that grew an identity field, which is
    exactly the drift the identity-leakage tests exist to catch."""
    document: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    assert document["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert document["$id"].startswith("https://epd2.example/contracts/")
    assert document["title"]
    assert len(document["description"]) > 200, "a schema description must explain the contract"
    assert document["additionalProperties"] is False
    assert document["required"], "every object schema declares its required fields"
    assert set(document["required"]) <= set(document["properties"])


@pytest.mark.parametrize(
    "path", _all_new_schema_paths(), ids=[p.name for p in _all_new_schema_paths()]
)
def test_no_schema_declares_a_forbidden_identity_field(path: Path) -> None:
    """No Framework-0.8.1 schema - entity or payload, at any nesting depth
    - declares a property that could carry an identity attribute, a global
    person identifier, a document body, message content, or a
    ballot/vote/tally/delegation reference.

    This is the schema-level counterpart to
    `test_ct00_08_identity_leakage.py`'s dataclass-level check: a field
    could in principle be added to a schema without being added to a
    dataclass, and it would be caught here."""
    from epd2_compliance_service.domain import FORBIDDEN_IDENTITY_FIELD_NAMES

    forbidden = set(FORBIDDEN_IDENTITY_FIELD_NAMES) | {
        "ballot_id",
        "vote_id",
        "tally_id",
        "delegation_id",
        "document_body",
        "document_bytes",
        "content",
        "message_body",
        "notice_body",
        "reasons_text",
        "narrative",
    }

    declared: set[str] = set()

    def walk(node: object) -> None:
        if isinstance(node, dict):
            properties = node.get("properties")
            if isinstance(properties, dict):
                declared.update(properties)
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(json.loads(path.read_text(encoding="utf-8")))
    leaked = declared & forbidden
    assert not leaked, f"{path.name} declares forbidden field(s): {sorted(leaked)}"


def test_no_wire_payload_carries_a_party_or_authority_reference() -> None:
    """The strongest of the payload rules, and the one worth stating as
    its own test: not one of the thirty-three new wire payloads contains a
    party handle or an authority handle.

    Those handles are unlinkable across cases by construction, but a
    broadcast payload is still the wrong place for them - a subscriber
    that never needs to know *who* acted should not be handed a handle it
    could accumulate. They live in the audit snapshots instead, which are
    hashed into Audit Core and never published."""
    from _pack09_framework_samples import (
        APPLICANT,
        AUTHORITY,
        REPLACEMENT,
        REPRESENTATIVE,
        RESPONDENT,
        REVIEWER,
    )

    handles = {APPLICANT, RESPONDENT, REPRESENTATIVE, AUTHORITY, REVIEWER, REPLACEMENT}
    for stem, envelope in _EVENT_SAMPLES.items():
        serialized = json.dumps(to_jsonable(envelope.payload))
        for handle in handles:
            assert str(handle) not in serialized, (
                f"{stem} leaks a party/authority reference into its wire payload"
            )
        for key in envelope.payload:
            assert not key.endswith("party_reference"), f"{stem} declares {key}"
            assert not key.endswith("authority_reference"), f"{stem} declares {key}"


def test_the_two_telemetry_events_deny_legal_effect_in_data() -> None:
    """`official_notice.issued` and `service_attempt.recorded` each carry
    `establishes_legal_effect: false` as a literal field, and only
    `notice_effect.determined` may carry it true.

    Framework hard invariants 39 and 40. Stated as data rather than as
    documentation so a subscriber that wires the wrong event to a deadline
    has to override an explicit denial rather than merely omit a check."""
    from epd2_compliance_service.events import (
        EVENT_TYPE_NOTICE_EFFECT_DETERMINED,
        NON_LEGAL_EFFECT_NOTICE_EVENT_TYPES,
    )

    for stem in ("official-notice-issued-payload", "service-attempt-recorded-payload"):
        envelope: EventEnvelope = _EVENT_SAMPLES[stem]
        assert envelope.event_type in NON_LEGAL_EFFECT_NOTICE_EVENT_TYPES
        assert envelope.payload["establishes_legal_effect"] is False

    effect = _EVENT_SAMPLES["notice-effect-determined-payload"]
    assert effect.event_type == EVENT_TYPE_NOTICE_EFFECT_DETERMINED
    assert effect.payload["establishes_legal_effect"] is True


def test_every_declared_event_type_has_a_payload_schema() -> None:
    """`events.ALL_EVENT_TYPES` and the payload schemas on disk agree.

    An event added in code but not in `contracts/` fails here, which is
    the point: the contract directory is the published interface and it
    must not lag the implementation."""
    from epd2_compliance_service.events import ALL_EVENT_TYPES

    covered = {envelope.event_type for envelope in _EVENT_SAMPLES.values()}
    round_one = {
        "governed_record.retention_started",
        "governed_record.disposal_authorized",
        "governed_record.destroyed",
        "legal_hold.status_changed",
        "processing_activity.status_changed",
        "procedural_case.status_changed",
        "procedural_deadline.state_changed",
        "data_subject_request.status_changed",
    }
    assert covered | round_one == ALL_EVENT_TYPES
    for stem in _EVENT_SAMPLES:
        assert (_CONTRACTS / "events" / f"{stem}.v1.schema.json").is_file()
