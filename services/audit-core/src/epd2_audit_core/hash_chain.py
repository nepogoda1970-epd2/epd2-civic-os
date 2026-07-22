"""Sequential hash chaining for `AuditEvent`, per ADR-003.

`event_hash = sha256(canonical_dumps(hashable_fields(event)) + previous_event_hash)`.
Uses `epd2_core.canonical_json` so the same logical content always hashes
identically regardless of construction order (a prerequisite for
Hypothesis-driven determinism tests, pack section 12.5).
"""

from __future__ import annotations

import hashlib

from epd2_audit_core.domain import AuditEvent, hashable_fields
from epd2_core.canonical_json import canonical_dumps

GENESIS_PREVIOUS_HASH = "0" * 64


def compute_event_hash(event: AuditEvent) -> str:
    """Compute the `event_hash` for `event`, given its own
    `previous_event_hash` (already set on `event`)."""
    serialized = canonical_dumps(hashable_fields(event))
    return hashlib.sha256((serialized + event.previous_event_hash).encode("utf-8")).hexdigest()
