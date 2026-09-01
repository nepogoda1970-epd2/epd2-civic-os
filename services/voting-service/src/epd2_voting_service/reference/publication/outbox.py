"""Transactional outbox (PACK-16D §25).

The outbox row carries **no continuation capability and no capability
reference**. It exists to move a publication obligation across a crash
boundary, not to correlate anything.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class ObligationState(StrEnum):
    PENDING = "pending"
    DISPATCHED = "dispatched"
    ACKNOWLEDGED = "acknowledged"


FORBIDDEN_OUTBOX_FIELDS: frozenset[str] = frozenset(
    {
        "capability_reference",
        "continuation_capability",
        "credential_id",
        "identity",
        "voter_id",
        "trace_id",
        "correlation_id",
        "exact_timestamp",
    }
)


@dataclass(frozen=True, slots=True)
class PublicationObligation:
    publication_obligation_id: str
    election_context_id: str
    artifact_internal_reference: str
    artifact_type: str
    batch_window_id: str
    coarse_creation_bucket: str
    schema_version: str = "EPD2-OBLIGATION-1"
    state: ObligationState = ObligationState.PENDING


@dataclass
class Outbox:
    rows: list[PublicationObligation] = field(default_factory=list)

    def enqueue(self, obligation: PublicationObligation) -> None:
        self.rows.append(obligation)

    def pending(self) -> list[PublicationObligation]:
        return [r for r in self.rows if r.state is ObligationState.PENDING]

    def mark(self, obligation_id: str, state: ObligationState) -> None:
        for index, row in enumerate(self.rows):
            if row.publication_obligation_id == obligation_id:
                self.rows[index] = PublicationObligation(
                    publication_obligation_id=row.publication_obligation_id,
                    election_context_id=row.election_context_id,
                    artifact_internal_reference=row.artifact_internal_reference,
                    artifact_type=row.artifact_type,
                    batch_window_id=row.batch_window_id,
                    coarse_creation_bucket=row.coarse_creation_bucket,
                    schema_version=row.schema_version,
                    state=state,
                )
                return
        raise KeyError(obligation_id)
