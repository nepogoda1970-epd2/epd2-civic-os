"""W10 — privacy-safe immutable control-plane evidence.

Two properties are enforced here rather than assumed:

* **Immutability.** The journal is append-only and hash-chained. There is no
  update or delete operation; `verify()` recomputes the whole chain, so a
  rewritten or removed historical record is detected rather than trusted.
* **Minimization.** Evidence is screened *before* it is appended. A record
  carrying a secret, a protected payload or a voting-linkable identifier is
  refused; it is never written and then filtered at the reader.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from epd2_control_plane_service.domain import VOTING_DOMAIN_FORBIDDEN_FIELDS
from epd2_control_plane_service.exceptions import EvidenceIntegrityError, PrivacyBoundaryViolation
from epd2_control_plane_service.policy import ControlPolicy
from epd2_core.canonical_json import canonical_dumps

__all__ = [
    "GENESIS_PREVIOUS_HASH",
    "SECRET_FIELD_MARKERS",
    "ControlEvidenceEvent",
    "EvidenceJournal",
]

GENESIS_PREVIOUS_HASH = "0" * 64

#: Substrings that indicate raw secret material rather than a governed handle.
#: A *reference* is permitted (`..._ref`, `..._reference_id`); the material is not.
SECRET_FIELD_MARKERS = (
    "private_key",
    "secret_value",
    "plaintext",
    "password",
    "passphrase",
    "seed_material",
)

#: Values that must never appear verbatim in evidence, whatever the field name.
_FORBIDDEN_VALUE_PREFIXES = ("-----BEGIN", "sk_live_", "eyJhbGciOi")


@dataclass(frozen=True, slots=True)
class ControlEvidenceEvent:
    """One immutable evidence record.

    `actor_ref` is a non-voting-domain control-plane principal reference. The
    record deliberately has no field for the acted-on natural person's identity
    beyond a governed object reference.
    """

    sequence: int
    occurred_at: datetime
    actor_ref: str
    actor_class: str
    authority_basis: str
    action_id: str
    scope_key: str
    object_ref: str
    result: str
    reason_code: str
    approval_refs: tuple[str, ...]
    correlation_ref: str
    attributes: Mapping[str, str] = field(default_factory=dict)
    previous_event_hash: str = GENESIS_PREVIOUS_HASH
    event_hash: str = ""

    def hashable(self) -> dict[str, Any]:
        return {
            "sequence": self.sequence,
            "occurred_at": self.occurred_at.isoformat(),
            "actor_ref": self.actor_ref,
            "actor_class": self.actor_class,
            "authority_basis": self.authority_basis,
            "action_id": self.action_id,
            "scope_key": self.scope_key,
            "object_ref": self.object_ref,
            "result": self.result,
            "reason_code": self.reason_code,
            "approval_refs": list(self.approval_refs),
            "correlation_ref": self.correlation_ref,
            "attributes": dict(sorted(self.attributes.items())),
        }

    def compute_hash(self) -> str:
        serialized = canonical_dumps(self.hashable())
        return hashlib.sha256((serialized + self.previous_event_hash).encode("utf-8")).hexdigest()


def screen_attributes(attributes: Mapping[str, Any]) -> None:
    """Refuse evidence attributes that breach the privacy or voting boundary."""
    for key, value in attributes.items():
        lowered = key.lower()
        if lowered in VOTING_DOMAIN_FORBIDDEN_FIELDS:
            raise PrivacyBoundaryViolation(
                (
                    f"evidence attribute {key!r} would create a voting-linkable or excess-personal "
                    f"reference"
                ),
                reason_code="CTRL_VOTING_LINKABLE_FIELD",
            )
        if any(marker in lowered for marker in SECRET_FIELD_MARKERS):
            raise PrivacyBoundaryViolation(
                f"evidence attribute {key!r} would place secret material in generic audit",
                reason_code="CTRL_SECRET_IN_AUDIT",
            )
        text = str(value)
        if any(text.startswith(prefix) for prefix in _FORBIDDEN_VALUE_PREFIXES):
            raise PrivacyBoundaryViolation(
                f"evidence attribute {key!r} carries raw secret material",
                reason_code="CTRL_SECRET_IN_AUDIT",
            )
        if len(text) > 512:
            raise PrivacyBoundaryViolation(
                (
                    f"evidence attribute {key!r} exceeds the minimization budget; store a "
                    f"reference instead"
                ),
                reason_code="CTRL_PRIVACY_MINIMIZATION",
            )


class EvidenceJournal:
    """Append-only, hash-chained evidence store.

    The journal exposes no mutating operation other than `append`. The private
    list is reachable only through `records()`, which returns a tuple, so a
    caller cannot reorder or truncate the history through the public surface.
    Deliberate tampering (used by the W11 mutation suite) is therefore visible
    to `verify()` by design.
    """

    def __init__(self, policy: ControlPolicy | None = None) -> None:
        self._records: list[ControlEvidenceEvent] = []
        self._policy = policy or ControlPolicy.governed()
        # Anchors, kept outside the record list. Without them a tamperer who
        # deletes the newest record, or who rewrites a record and recomputes
        # every hash forward, leaves a chain that validates perfectly.
        self._appended = 0
        self._anchor_head = GENESIS_PREVIOUS_HASH

    def append(
        self,
        *,
        occurred_at: datetime,
        actor_ref: str,
        actor_class: str,
        authority_basis: str,
        action_id: str,
        scope_key: str,
        object_ref: str,
        result: str,
        reason_code: str,
        approval_refs: Sequence[str] = (),
        correlation_ref: str,
        attributes: Mapping[str, Any] | None = None,
    ) -> ControlEvidenceEvent:
        attrs = {str(k): str(v) for k, v in (attributes or {}).items()}
        if self._policy.enforce_privacy_minimization:
            screen_attributes(attrs)
        previous = self._records[-1].event_hash if self._records else GENESIS_PREVIOUS_HASH
        event = ControlEvidenceEvent(
            sequence=len(self._records) + 1,
            occurred_at=occurred_at,
            actor_ref=actor_ref,
            actor_class=actor_class,
            authority_basis=authority_basis,
            action_id=action_id,
            scope_key=scope_key,
            object_ref=object_ref,
            result=result,
            reason_code=reason_code,
            approval_refs=tuple(approval_refs),
            correlation_ref=correlation_ref,
            attributes=attrs,
            previous_event_hash=previous,
        )
        # Slotted frozen dataclasses cannot be updated in place; the sealed
        # record is rebuilt with its computed hash and only then appended.
        sealed = ControlEvidenceEvent(
            sequence=event.sequence,
            occurred_at=event.occurred_at,
            actor_ref=event.actor_ref,
            actor_class=event.actor_class,
            authority_basis=event.authority_basis,
            action_id=event.action_id,
            scope_key=event.scope_key,
            object_ref=event.object_ref,
            result=event.result,
            reason_code=event.reason_code,
            approval_refs=event.approval_refs,
            correlation_ref=event.correlation_ref,
            attributes=event.attributes,
            previous_event_hash=event.previous_event_hash,
            event_hash=event.compute_hash(),
        )
        self._records.append(sealed)
        self._appended += 1
        self._anchor_head = sealed.event_hash
        return sealed

    def records(self) -> tuple[ControlEvidenceEvent, ...]:
        return tuple(self._records)

    def head_hash(self) -> str:
        return self._records[-1].event_hash if self._records else GENESIS_PREVIOUS_HASH

    def __len__(self) -> int:
        return len(self._records)

    def find(
        self, *, action_id: str | None = None, result: str | None = None
    ) -> tuple[ControlEvidenceEvent, ...]:
        return tuple(
            r
            for r in self._records
            if (action_id is None or r.action_id == action_id)
            and (result is None or r.result == result)
        )

    def anchor(self) -> tuple[int, str]:
        """The count and head hash observed at append time.

        These are the external reference `verify` checks the chain against. They
        are updated only by `append`, never derived from the record list.
        """
        return self._appended, self._anchor_head

    def verify(self) -> None:
        """Recompute the chain and compare it against the append-time anchor.

        Raises on any rewrite, deletion, truncation or reorder — including a
        deletion of the newest record and a rewrite that re-chains every
        subsequent hash, neither of which an unanchored walk can see.
        """
        if not self._policy.enforce_evidence_immutability:
            return
        if len(self._records) != self._appended:
            raise EvidenceIntegrityError(
                f"evidence count {len(self._records)} does not match the "
                f"{self._appended} record(s) appended"
            )
        if self.head_hash() != self._anchor_head:
            raise EvidenceIntegrityError("evidence head does not match the append-time anchor")
        previous = GENESIS_PREVIOUS_HASH
        for index, record in enumerate(self._records, start=1):
            if record.sequence != index:
                raise EvidenceIntegrityError(
                    f"evidence sequence break at position {index}: record claims {record.sequence}"
                )
            if record.previous_event_hash != previous:
                raise EvidenceIntegrityError(f"evidence chain break at sequence {record.sequence}")
            if record.compute_hash() != record.event_hash:
                raise EvidenceIntegrityError(
                    f"evidence record {record.sequence} was rewritten after sealing"
                )
            previous = record.event_hash

    def export(self) -> list[dict[str, Any]]:
        return [
            {
                **r.hashable(),
                "previous_event_hash": r.previous_event_hash,
                "event_hash": r.event_hash,
            }
            for r in self._records
        ]


def journal_digest(events: Iterable[ControlEvidenceEvent]) -> str:
    payload = canonical_dumps([e.event_hash for e in events])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
