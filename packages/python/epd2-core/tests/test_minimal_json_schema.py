"""Tests for epd2_core.minimal_json_schema."""

from __future__ import annotations

import pytest

from epd2_core.minimal_json_schema import SchemaValidationError, is_valid, validate

_SCHEMA = {
    "type": "object",
    "required": ["event_id", "event_type", "status"],
    "additionalProperties": False,
    "properties": {
        "event_id": {"type": "string", "format": "uuid"},
        "event_type": {"type": "string", "minLength": 1},
        "status": {"type": "string", "enum": ["active", "closed"]},
        "count": {"type": "integer"},
    },
}


def test_valid_instance_passes() -> None:
    instance = {
        "event_id": "12345678-1234-5678-1234-567812345678",
        "event_type": "account.created",
        "status": "active",
        "count": 3,
    }
    validate(instance, _SCHEMA)
    assert is_valid(instance, _SCHEMA)


def test_missing_required_field_is_rejected() -> None:
    instance = {"event_id": "12345678-1234-5678-1234-567812345678", "status": "active"}
    with pytest.raises(SchemaValidationError, match="missing required"):
        validate(instance, _SCHEMA)


def test_unknown_enum_value_is_rejected() -> None:
    instance = {
        "event_id": "12345678-1234-5678-1234-567812345678",
        "event_type": "account.created",
        "status": "not-a-real-status",
    }
    with pytest.raises(SchemaValidationError):
        validate(instance, _SCHEMA)


def test_additional_property_is_rejected() -> None:
    instance = {
        "event_id": "12345678-1234-5678-1234-567812345678",
        "event_type": "account.created",
        "status": "active",
        "unexpected_field": "should not be here",
    }
    with pytest.raises(SchemaValidationError, match="additional property"):
        validate(instance, _SCHEMA)


def test_invalid_uuid_format_is_rejected() -> None:
    instance = {
        "event_id": "not-a-uuid",
        "event_type": "account.created",
        "status": "active",
    }
    with pytest.raises(SchemaValidationError, match="uuid"):
        validate(instance, _SCHEMA)


def test_wrong_type_is_rejected() -> None:
    instance = {
        "event_id": "12345678-1234-5678-1234-567812345678",
        "event_type": "account.created",
        "status": "active",
        "count": "not-an-integer",
    }
    with pytest.raises(SchemaValidationError, match="expected type"):
        validate(instance, _SCHEMA)


def test_boolean_is_not_accepted_as_integer() -> None:
    with pytest.raises(SchemaValidationError):
        validate(True, {"type": "integer"})


def test_is_valid_returns_false_without_raising() -> None:
    assert is_valid({"event_id": "bad"}, _SCHEMA) is False


def test_array_items_are_validated() -> None:
    schema = {"type": "array", "items": {"type": "string"}}
    validate(["a", "b"], schema)
    with pytest.raises(SchemaValidationError):
        validate(["a", 2], schema)


def test_date_time_format_accepts_iso8601() -> None:
    validate("2026-01-01T00:00:00+00:00", {"type": "string", "format": "date-time"})


def test_date_time_format_rejects_garbage() -> None:
    with pytest.raises(SchemaValidationError):
        validate("not-a-date", {"type": "string", "format": "date-time"})


def test_nullable_uuid_format_accepts_none() -> None:
    """A schema combining `"type": ["string", "null"]` with
    `"format": "uuid"` (used by contracts/schemas/event-envelope.schema.json
    for causation_id) must accept `None` - format only constrains string
    instances per JSON Schema semantics, it does not forbid null."""
    schema = {"type": ["string", "null"], "format": "uuid"}
    validate(None, schema)
    validate("11111111-1111-1111-1111-111111111111", schema)
    with pytest.raises(SchemaValidationError):
        validate("not-a-uuid", schema)
    with pytest.raises(SchemaValidationError):
        validate(123, schema)
