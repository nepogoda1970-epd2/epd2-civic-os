"""A minimal, dependency-free validator for a deliberately small subset of
JSON Schema (roughly draft 2020-12).

This exists so CLAUDE-PACK-02's CT-00-01 ("Schema Validation") can run in
this repository's sandboxed CI-less environment, which has no network
access to install the `jsonschema` package (see `LOCAL_VERIFICATION.md`).
The schema *documents* under `contracts/schemas/` and `contracts/events/`
remain standard JSON Schema and are also validated with the real
`jsonschema` package in CI (`.github/workflows/verify-and-package.yml`),
where network access is available - this module is a supplementary,
always-available check, not a replacement for that.

Supported keywords: `type`, `required`, `properties`,
`additionalProperties` (bool only), `enum`, `items`, `minLength`,
`format: "uuid"` / `"date-time"` (checked structurally, not exhaustively).
Any other keyword in a schema is ignored, not silently "passed" as
meaningful - callers that need full JSON Schema semantics should treat
this as a fast local pre-check only.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

_UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)

_TYPE_MAP: dict[str, tuple[type, ...]] = {
    "object": (dict,),
    "array": (list,),
    "string": (str,),
    "integer": (int,),
    "number": (int, float),
    "boolean": (bool,),
    "null": (type(None),),
}


class SchemaValidationError(ValueError):
    """Raised when an instance fails validation, with the failing path."""

    def __init__(self, path: str, message: str) -> None:
        super().__init__(f"{path or '$'}: {message}")
        self.path = path
        self.message = message


def _check_format(path: str, value: Any, fmt: str) -> None:
    if fmt == "uuid":
        if not isinstance(value, str) or not _UUID_RE.match(value):
            raise SchemaValidationError(path, f"is not a valid uuid string: {value!r}")
    elif fmt == "date-time":
        if not isinstance(value, str):
            raise SchemaValidationError(path, "is not a date-time string")
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            message = f"is not a valid ISO-8601 date-time: {value!r}"
            raise SchemaValidationError(path, message) from exc


def validate(instance: Any, schema: dict[str, Any], *, path: str = "") -> None:
    """Validate `instance` against `schema`. Raises `SchemaValidationError`
    on the first violation found. Returns `None` on success.
    """
    if "type" in schema:
        expected = schema["type"]
        expected_types = expected if isinstance(expected, list) else [expected]
        allowed_py_types: tuple[type, ...] = tuple(
            t for name in expected_types for t in _TYPE_MAP.get(name, ())
        )
        # bool is a subclass of int in Python; only accept bool for
        # "boolean" and reject it for "integer"/"number" unless explicitly
        # listed, matching JSON Schema's distinct boolean/number types.
        if isinstance(instance, bool) and "boolean" not in expected_types:
            raise SchemaValidationError(path, f"expected type {expected!r}, got boolean")
        if not isinstance(instance, allowed_py_types):
            raise SchemaValidationError(
                path, f"expected type {expected!r}, got {type(instance).__name__}"
            )

    if "enum" in schema and instance not in schema["enum"]:
        raise SchemaValidationError(path, f"{instance!r} is not one of {schema['enum']!r}")

    if "minLength" in schema and isinstance(instance, str) and len(instance) < schema["minLength"]:
        message = f"length {len(instance)} < minLength {schema['minLength']}"
        raise SchemaValidationError(path, message)

    if "format" in schema and isinstance(instance, str):
        # Per JSON Schema semantics, "format" (uuid/date-time here) only
        # constrains string instances; a schema combining
        # `"type": ["string", "null"]` with `"format": "uuid"` to express
        # a nullable UUID must not fail validation when the instance is
        # `None` - only when it is a string that isn't a valid UUID.
        _check_format(path, instance, schema["format"])

    if isinstance(instance, dict):
        required = schema.get("required", [])
        missing = [f for f in required if f not in instance]
        if missing:
            raise SchemaValidationError(path, f"missing required field(s): {missing}")

        properties: dict[str, Any] = schema.get("properties", {})
        for key, value in instance.items():
            if key in properties:
                validate(value, properties[key], path=f"{path}.{key}" if path else key)
            elif schema.get("additionalProperties") is False:
                raise SchemaValidationError(path, f"additional property {key!r} is not allowed")

    if isinstance(instance, list) and "items" in schema:
        for i, item in enumerate(instance):
            validate(item, schema["items"], path=f"{path}[{i}]")


def is_valid(instance: Any, schema: dict[str, Any]) -> bool:
    """Return `True` if `instance` validates against `schema`, else `False`."""
    try:
        validate(instance, schema)
    except SchemaValidationError:
        return False
    return True
