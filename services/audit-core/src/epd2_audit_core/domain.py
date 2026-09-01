"""`AuditEvent`, per `docs/canonical/TZ-00-domain-event-canon.md`, section
18.1. Audit Core is the sole owner of this entity (section 22).

`before_hash`/`after_hash` are opaque, caller-computed hash strings of the
audited target entity's state immediately before/after the action (empty
string if not applicable to a particular action) - Audit Core does not
know the internal shape of any other service's entities (INV-03), so it
cannot compute these itself; the owning service computes them (typically
via `epd2_core.canonical_json` + a hash function) and passes them in.
`reason_code` must already have been validated by the calling service
against its own reason-code registry (see ADR-002); Audit Core does not
re-validate it against a registry to avoid coupling Audit Core to every
other service's registry contents.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class AuditEvent:
    """A single, immutable append-only audit log entry."""

    audit_event_id: UUID
    event_type: str
    occurred_at: datetime
    recorded_at: datetime
    actor_id: UUID
    actor_type: str
    target_type: str
    target_id: UUID
    action: str
    reason_code: str
    policy_version: str
    before_hash: str
    after_hash: str
    correlation_id: UUID
    source_service: str
    previous_event_hash: str
    event_hash: str

    def __post_init__(self) -> None:
        if not self.event_type:
            raise ValueError("event_type must not be empty")
        if not self.actor_type:
            raise ValueError("actor_type must not be empty")
        if not self.target_type:
            raise ValueError("target_type must not be empty")
        if not self.action:
            raise ValueError("action must not be empty")
        if not self.reason_code:
            raise ValueError("reason_code must not be empty")
        if not self.source_service:
            raise ValueError("source_service must not be empty")
        if self.occurred_at.tzinfo is None or self.recorded_at.tzinfo is None:
            raise ValueError("occurred_at and recorded_at must be timezone-aware")
        if self.recorded_at < self.occurred_at:
            raise ValueError("recorded_at must not be before occurred_at")


def hashable_fields(event: AuditEvent) -> dict[str, object]:
    """Return the subset of `event`'s fields that participate in
    `event_hash` computation - every field except `event_hash` itself
    (which is the output, not an input, of that computation).
    """
    return {
        "audit_event_id": event.audit_event_id,
        "event_type": event.event_type,
        "occurred_at": event.occurred_at,
        "recorded_at": event.recorded_at,
        "actor_id": event.actor_id,
        "actor_type": event.actor_type,
        "target_type": event.target_type,
        "target_id": event.target_id,
        "action": event.action,
        "reason_code": event.reason_code,
        "policy_version": event.policy_version,
        "before_hash": event.before_hash,
        "after_hash": event.after_hash,
        "correlation_id": event.correlation_id,
        "source_service": event.source_service,
        "previous_event_hash": event.previous_event_hash,
    }
