"""Deployment-time bootstrap seed for Governance Service's initial
authority (ADR-020 item 6, this project's own requirement 6 for PACK-05).

This module is deliberately separate from `application.py`'s normal
command surface — `run_bootstrap_seed` is not one of the paths documented
in `contracts/openapi/pack-05.yaml` and is never reachable through the
ordinary application/API layer. It exists to solve the one genuine
chicken-and-egg problem in this pack: every ordinary `RoleAssignment`
grant (`application.request_role_assignment`) requires an existing,
active, non-self granting `RoleAssignment`, and none can exist yet the
very first time a deployment is seeded.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from epd2_audit_core.application import AppendAuditEventRequest, append_audit_event
from epd2_audit_core.domain import AuditEvent
from epd2_audit_core.storage import AuditEventStore
from epd2_core.clock import Clock
from epd2_core.event_envelope import compute_payload_hash
from epd2_core.identifiers import generate_uuid
from epd2_governance_service.domain import PILOT_ROLE_CODES, RoleAssignment, RoleAssignmentStatus
from epd2_governance_service.events import role_assignment_full_state_payload
from epd2_governance_service.exceptions import SameActorApprovalRejectedError
from epd2_governance_service.storage import RoleAssignmentStore

AUDIT_POLICY_VERSION = "1.0"
_SOURCE_SERVICE = "governance-service-bootstrap"
_ROLE_ASSIGNMENT_AUDIT = "GOVERNANCE_ROLE_ASSIGNMENT_STATUS_CHANGED"

#: The `assigned_by` marker stored on both bootstrap-seeded
#: `RoleAssignment` rows — neither references the other's
#: `role_assignment_id` as its granter (both are created atomically, in
#: the same seed) and neither references itself. A fixed, well-known
#: sentinel so any later auditor can unambiguously tell that a given
#: `RoleAssignment`'s authority traces back to the one-time deployment
#: seed rather than an ordinary two-actor grant.
BOOTSTRAP_ASSIGNED_BY_MARKER: UUID = UUID("00000000-0000-0000-0000-0000000b0075")


class BootstrapAlreadyExecutedError(RuntimeError):
    """Raised by `run_bootstrap_seed` on any call after the first
    successful execution (ADR-020 item 6: "permanently disabled after
    first successful execution")."""

    reason_code = "GOVERNANCE_BOOTSTRAP_ALREADY_EXECUTED"


@dataclass(frozen=True, slots=True)
class BootstrapSeedManifest:
    """Immutable record of exactly one bootstrap seed execution. Never
    rewritten once created; a second attempted execution raises
    `BootstrapAlreadyExecutedError` instead of ever producing a second
    manifest."""

    manifest_id: UUID
    executed_at: datetime
    first_role_assignment_id: UUID
    first_actor_id: UUID
    first_role_code: str
    second_role_assignment_id: UUID
    second_actor_id: UUID
    second_role_code: str
    checksum: str


class BootstrapSeedStore(Protocol):
    def has_run(self) -> bool:
        """`True` if `run_bootstrap_seed` has already executed
        successfully once."""
        ...

    def record(self, manifest: BootstrapSeedManifest) -> None:
        """Persist the one-and-only manifest, permanently marking
        bootstrap as executed."""
        ...

    def get_manifest(self) -> BootstrapSeedManifest | None: ...


class InMemoryBootstrapSeedStore:
    def __init__(self) -> None:
        self._manifest: BootstrapSeedManifest | None = None

    def has_run(self) -> bool:
        return self._manifest is not None

    def record(self, manifest: BootstrapSeedManifest) -> None:
        self._manifest = manifest

    def get_manifest(self) -> BootstrapSeedManifest | None:
        return self._manifest


def _compute_manifest_checksum(
    *,
    first_role_assignment_id: UUID,
    first_actor_id: UUID,
    first_role_code: str,
    second_role_assignment_id: UUID,
    second_actor_id: UUID,
    second_role_code: str,
    executed_at: datetime,
) -> str:
    canonical = "|".join(
        [
            str(first_role_assignment_id),
            str(first_actor_id),
            first_role_code,
            str(second_role_assignment_id),
            str(second_actor_id),
            second_role_code,
            executed_at.isoformat(),
        ]
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class BootstrapResult:
    manifest: BootstrapSeedManifest
    first_assignment: RoleAssignment
    second_assignment: RoleAssignment
    first_audit_event: AuditEvent
    second_audit_event: AuditEvent


def run_bootstrap_seed(
    role_store: RoleAssignmentStore,
    bootstrap_store: BootstrapSeedStore,
    audit_store: AuditEventStore,
    *,
    first_role_assignment_id: UUID,
    first_actor_id: UUID,
    first_role_code: str,
    first_scope_id: UUID,
    second_role_assignment_id: UUID,
    second_actor_id: UUID,
    second_role_code: str,
    second_scope_id: UUID,
    valid_from: datetime,
    correlation_id: UUID,
    clock: Clock,
) -> BootstrapResult:
    """Create exactly two distinct, already-`active` `RoleAssignment`
    rows (ADR-020 item 6), atomically, and permanently disable any
    further call. Raises `BootstrapAlreadyExecutedError` if a manifest
    already exists. Raises `SameActorApprovalRejectedError` if
    `first_actor_id == second_actor_id` ("no actor may seed or approve
    their own assignment" — a single actor cannot serve as its own
    second, distinct co-founder either)."""
    if bootstrap_store.has_run():
        raise BootstrapAlreadyExecutedError(
            "governance-service bootstrap seed has already executed once and is "
            "permanently disabled"
        )
    if first_actor_id == second_actor_id:
        raise SameActorApprovalRejectedError(
            "bootstrap seed requires two distinct initial actors (ADR-020 item 6)"
        )
    for role_code in (first_role_code, second_role_code):
        if role_code not in PILOT_ROLE_CODES:
            raise ValueError(
                f"role_code {role_code!r} is not part of the pilot role taxonomy "
                f"({sorted(PILOT_ROLE_CODES)})"
            )

    now = clock.now()
    first_assignment = RoleAssignment(
        role_assignment_id=first_role_assignment_id,
        actor_id=first_actor_id,
        role_code=first_role_code,
        scope_id=first_scope_id,
        valid_from=valid_from,
        valid_until=None,
        assigned_by=BOOTSTRAP_ASSIGNED_BY_MARKER,
        approval_reference="bootstrap-seed",
        status=RoleAssignmentStatus.ACTIVE,
    )
    second_assignment = RoleAssignment(
        role_assignment_id=second_role_assignment_id,
        actor_id=second_actor_id,
        role_code=second_role_code,
        scope_id=second_scope_id,
        valid_from=valid_from,
        valid_until=None,
        assigned_by=BOOTSTRAP_ASSIGNED_BY_MARKER,
        approval_reference="bootstrap-seed",
        status=RoleAssignmentStatus.ACTIVE,
    )
    stored_first = role_store.create(first_assignment)
    stored_second = role_store.create(second_assignment)

    checksum = _compute_manifest_checksum(
        first_role_assignment_id=first_role_assignment_id,
        first_actor_id=first_actor_id,
        first_role_code=first_role_code,
        second_role_assignment_id=second_role_assignment_id,
        second_actor_id=second_actor_id,
        second_role_code=second_role_code,
        executed_at=now,
    )
    manifest = BootstrapSeedManifest(
        manifest_id=generate_uuid(),
        executed_at=now,
        first_role_assignment_id=first_role_assignment_id,
        first_actor_id=first_actor_id,
        first_role_code=first_role_code,
        second_role_assignment_id=second_role_assignment_id,
        second_actor_id=second_actor_id,
        second_role_code=second_role_code,
        checksum=checksum,
    )
    bootstrap_store.record(manifest)

    first_audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=generate_uuid(),
            event_type="governance.role_assignment_activated",
            occurred_at=now,
            actor_id=first_actor_id,
            actor_type="bootstrap_seed",
            target_type="role_assignment",
            target_id=stored_first.role_assignment_id,
            action="bootstrap_seed_role_assignment",
            reason_code=_ROLE_ASSIGNMENT_AUDIT,
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash="",
            after_hash=compute_payload_hash(role_assignment_full_state_payload(stored_first)),
        ),
        clock=clock,
    )
    second_audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=generate_uuid(),
            event_type="governance.role_assignment_activated",
            occurred_at=now,
            actor_id=second_actor_id,
            actor_type="bootstrap_seed",
            target_type="role_assignment",
            target_id=stored_second.role_assignment_id,
            action="bootstrap_seed_role_assignment",
            reason_code=_ROLE_ASSIGNMENT_AUDIT,
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash="",
            after_hash=compute_payload_hash(role_assignment_full_state_payload(stored_second)),
        ),
        clock=clock,
    )
    return BootstrapResult(
        manifest=manifest,
        first_assignment=stored_first,
        second_assignment=stored_second,
        first_audit_event=first_audit_event,
        second_audit_event=second_audit_event,
    )
