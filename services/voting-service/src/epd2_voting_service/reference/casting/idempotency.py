"""Idempotency and replay model (PACK-16D §26)."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass


class IdempotencyConflictError(ValueError):
    reason_code = "SUBMISSION_IDEMPOTENCY_CONFLICT"


def request_digest(canonical_request: bytes) -> str:
    """Binding is to the canonical request bytes, never to a loose summary."""
    return hashlib.sha256(canonical_request).hexdigest()


@dataclass(frozen=True, slots=True)
class IdempotencyRecord:
    """Key is scoped to one election and one operation, and is never a
    capability, a credential or a public ballot reference."""

    idempotency_key: str
    election_context_id: str
    operation: str
    request_digest: str
    outcome_code: str
    outcome_payload: tuple[tuple[str, str], ...]

    @property
    def scope(self) -> tuple[str, str, str]:
        return (self.election_context_id, self.operation, self.idempotency_key)
