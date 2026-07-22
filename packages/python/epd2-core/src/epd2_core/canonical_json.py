"""Deterministic canonical JSON serialization.

Used wherever two independently-constructed representations of the same
logical content must serialize identically - payload hashing in
`epd2_core.event_envelope`, and audit hash chaining in the Audit Core
service. This is a generic serialization utility; it encodes no domain
decisions (CLAUDE-PACK-02 section 4.2 permits "generic validation
utilities" in shared packages, and canonical serialization is the same
kind of generic concern).
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from datetime import date, datetime
from typing import Any
from uuid import UUID


def _default(value: object) -> object:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        if value.tzinfo is None:
            raise ValueError("canonical_dumps requires timezone-aware datetimes")
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    raise TypeError(f"Object of type {type(value).__name__} is not canonically serializable")


def to_canonical_value(value: Any) -> Any:
    """Recursively convert `value` into a structure of only `dict`, `list`,
    `str`, `int`, `float`, `bool`, and `None` - the canonical, hashable
    subset used by `canonical_dumps`.

    Mapping keys are converted to `str`. `UUID`/`datetime`/`date` values
    are converted via `_default`. Any other non-primitive type raises
    `TypeError` rather than silently guessing a representation.
    """
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, Mapping):
        return {str(k): to_canonical_value(v) for k, v in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
        return [to_canonical_value(v) for v in value]
    return _default(value)


def canonical_dumps(value: Any) -> str:
    """Serialize `value` to a JSON string with deterministic key ordering
    and separators, so that two calls with equal logical content always
    produce byte-identical output regardless of dict construction order.
    """
    canonical = to_canonical_value(value)
    return json.dumps(canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
