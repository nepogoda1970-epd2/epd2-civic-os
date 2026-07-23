"""`AuditEventStore` protocol and the in-memory reference adapter.

A durable backend (e.g. an append-only table with a unique index on
`audit_event_id` and a sequence column) can implement this same protocol
without any change to `application.py` or any calling service (pack
section 4.1: "storage interface; in-memory reference adapter for contract
tests").
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from epd2_audit_core.domain import AuditEvent
from epd2_audit_core.exceptions import AuditEventConflictError
from epd2_audit_core.hash_chain import GENESIS_PREVIOUS_HASH, compute_event_hash


@dataclass(frozen=True, slots=True)
class ChainVerificationResult:
    """Result of `verify_chain()`."""

    is_intact: bool
    broken_at_index: int | None
    broken_audit_event_id: UUID | None
    checked_count: int


class AuditEventStore(Protocol):
    """Storage interface Audit Core's application layer depends on."""

    def head_hash(self) -> str:
        """Return the `event_hash` of the most recently appended record,
        or `GENESIS_PREVIOUS_HASH` if the chain is empty."""
        ...

    def append(self, event: AuditEvent) -> AuditEvent:
        """Append `event`. If `event.audit_event_id` already exists with
        identical hashable content, returns the existing stored record
        (idempotent no-op). If it exists with different content, raises
        `AuditEventConflictError`.
        """
        ...

    def get_by_event_id(self, audit_event_id: UUID) -> AuditEvent | None: ...

    def list_by_aggregate(self, target_type: str, target_id: UUID) -> tuple[AuditEvent, ...]: ...

    def verify_chain(self) -> ChainVerificationResult: ...

    def list_all(self) -> tuple[AuditEvent, ...]:
        """Return every recorded event, in append (chain) order.

        Additive (PACK-04, ADR-012 item 4): backs
        `application.list_by_target_types`, which
        `epd2_transparency_service.application.generate_audit_export_package`
        uses to build an `AuditExportPackage`'s `chain_proof`. Does not
        change any existing method's signature or behavior.
        """
        ...


class InMemoryAuditEventStore:
    """Reference `AuditEventStore` adapter: a single append-only list plus
    an id index, held in process memory only.
    """

    def __init__(self) -> None:
        self._events: list[AuditEvent] = []
        self._by_id: dict[UUID, AuditEvent] = {}

    def head_hash(self) -> str:
        if not self._events:
            return GENESIS_PREVIOUS_HASH
        return self._events[-1].event_hash

    def append(self, event: AuditEvent) -> AuditEvent:
        existing = self._by_id.get(event.audit_event_id)
        if existing is not None:
            if existing == event:
                return existing
            raise AuditEventConflictError(
                f"audit_event_id {event.audit_event_id} already recorded with different content"
            )
        self._events.append(event)
        self._by_id[event.audit_event_id] = event
        return event

    def get_by_event_id(self, audit_event_id: UUID) -> AuditEvent | None:
        return self._by_id.get(audit_event_id)

    def list_by_aggregate(self, target_type: str, target_id: UUID) -> tuple[AuditEvent, ...]:
        return tuple(
            e for e in self._events if e.target_type == target_type and e.target_id == target_id
        )

    def list_all(self) -> tuple[AuditEvent, ...]:
        return tuple(self._events)

    def verify_chain(self) -> ChainVerificationResult:
        previous_hash = GENESIS_PREVIOUS_HASH
        for index, event in enumerate(self._events):
            if event.previous_event_hash != previous_hash:
                return ChainVerificationResult(
                    is_intact=False,
                    broken_at_index=index,
                    broken_audit_event_id=event.audit_event_id,
                    checked_count=index,
                )
            if compute_event_hash(event) != event.event_hash:
                return ChainVerificationResult(
                    is_intact=False,
                    broken_at_index=index,
                    broken_audit_event_id=event.audit_event_id,
                    checked_count=index,
                )
            previous_hash = event.event_hash
        return ChainVerificationResult(
            is_intact=True,
            broken_at_index=None,
            broken_audit_event_id=None,
            checked_count=len(self._events),
        )
