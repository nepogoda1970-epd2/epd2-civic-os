"""CTRL-02 bounded regional intervention and privileged operations runtime.

The runtime deliberately models control operations as governed workflows.  A
request, approval, activation, use and review are separate acts; every act is
bound to an exact actor, scope, authority version and append-only evidence.
There is no universal administrator and no hierarchy-derived Bund takeover.
"""

from __future__ import annotations

import hashlib
import json
import threading
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any, Final

from epd2_control_plane_service.exceptions import AuthorizationRefused


class InterventionLevel(StrEnum):
    SESSION_QUARANTINE = "L1_SESSION_QUARANTINE"
    AUTHORITY_SUSPENSION = "L2_AUTHORITY_SUSPENSION"
    REGIONAL_ACTION_RESTRICTION = "L3_REGIONAL_ACTION_RESTRICTION"
    TEMPORARY_SUPERVISION = "L4_TEMPORARY_SUPERVISION"


class WorkflowState(StrEnum):
    REQUESTED = "REQUESTED"
    REVIEWING = "REVIEWING"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"
    COMPLETED = "COMPLETED"
    POST_REVIEWED = "POST_REVIEWED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class PrivilegeKind(StrEnum):
    JIT = "JIT"
    BREAK_GLASS = "BREAK_GLASS"


class ActorClass(StrEnum):
    HUMAN = "HUMAN"
    SERVICE = "SERVICE"


class ApproverClass(StrEnum):
    GOVERNANCE = "GOVERNANCE"
    SECURITY = "SECURITY"
    INCIDENT_COMMANDER = "INCIDENT_COMMANDER"
    TRUST_CUSTODIAN = "TRUST_CUSTODIAN"


class Decision(StrEnum):
    ALLOW = "ALLOW"
    AUTHORITY_REVOKED = "AUTHORITY_REVOKED"
    AUTHORITY_SUSPENDED = "AUTHORITY_SUSPENDED"
    WRONG_SCOPE = "WRONG_SCOPE"
    QUORUM_NOT_MET = "QUORUM_NOT_MET"
    SELF_APPROVAL_FORBIDDEN = "SELF_APPROVAL_FORBIDDEN"
    GRANT_EXPIRED = "GRANT_EXPIRED"
    SESSION_QUARANTINED = "SESSION_QUARANTINED"
    DEPENDENCY_UNAVAILABLE = "DEPENDENCY_UNAVAILABLE"
    VOTING_BOUNDARY = "VOTING_BOUNDARY"
    STALE_AUTHORITY = "STALE_AUTHORITY"
    STALE_TARGET = "STALE_TARGET"
    ACTION_RESTRICTED = "ACTION_RESTRICTED"


TERMINAL_STATES: Final = frozenset(
    {
        WorkflowState.EXPIRED,
        WorkflowState.REVOKED,
        WorkflowState.COMPLETED,
        WorkflowState.POST_REVIEWED,
        WorkflowState.REJECTED,
        WorkflowState.CANCELLED,
    }
)
VOTING_PROHIBITED: Final = frozenset(
    {
        "VOTER.LOOKUP",
        "BALLOT.READ",
        "BALLOT.CORRELATE_PERSON",
        "TALLY.READ_INTERMEDIATE",
        "VOTING.ADMIN",
        "VOTING.SESSION_REUSE",
        "VOTING.KEY.ACCESS",
    }
)
ABSOLUTE_PROHIBITIONS: Final = VOTING_PROHIBITED | frozenset(
    {"SECRET.RAW_READ", "SECRET.EXPORT", "AUTHORITY.UNIVERSAL_ADMIN"}
)
COARSE_TARGETS: Final = frozenset({"*", "ALL", "REGION_DISABLED", "GLOBAL"})
MAX_SUPERVISION: Final = timedelta(days=90)
MAX_JIT: Final = timedelta(hours=8)
MAX_BREAK_GLASS: Final = timedelta(hours=1)
DIRECT_DB_MUTATION_COUNTS_AS_GOVERNED: Final = False
DENIALS_RAISE: Final = True
SELF_STATE: Final = "PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED"
CTRL01_WORKING_PREDECESSOR_SHA256: Final = (
    "490d8ca31d4607da204f03addaf900161257b289d51ec6f0b7e52433fd5cbe71"
)
MUTATION_FIXTURES_REQUIRED: Final = 40
FREEZE_REJECTS_POST_VALIDATION_CHANGE: Final = True


@dataclass(frozen=True, slots=True)
class ExactScope:
    region_id: str
    org_id: str

    def __post_init__(self) -> None:
        if not self.region_id or not self.org_id:
            raise ValueError("scope requires exact region_id and org_id")
        if self.region_id in COARSE_TARGETS or self.org_id in COARSE_TARGETS:
            raise ValueError("coarse or wildcard scope is forbidden")

    @property
    def key(self) -> str:
        return f"{self.region_id}:{self.org_id}"


@dataclass(frozen=True, slots=True)
class AuthorityGrant:
    grant_id: str
    actor_id: str
    actor_class: ActorClass
    capability: str
    scope: ExactScope
    version: int
    active: bool = True
    revoked: bool = False
    suspended: bool = False
    expires_at: datetime | None = None
    approver_class: ApproverClass | None = None

    def usable_at(self, now: datetime) -> bool:
        return (
            self.active
            and not self.revoked
            and not self.suspended
            and (self.expires_at is None or now < self.expires_at)
        )


class AuthorityDirectory:
    """Versioned exact-scope authority source. Unavailability fails closed."""

    def __init__(self, grants: Iterable[AuthorityGrant] = ()) -> None:
        self._grants = {grant.grant_id: grant for grant in grants}
        self.available = True
        self._lock = threading.RLock()

    def add(self, grant: AuthorityGrant) -> None:
        with self._lock:
            self._grants[grant.grant_id] = grant

    def update(self, grant_id: str, **changes: Any) -> AuthorityGrant:
        with self._lock:
            current = self._grants[grant_id]
            updated = replace(current, version=current.version + 1, **changes)
            self._grants[grant_id] = updated
            return updated

    def grant(self, grant_id: str) -> AuthorityGrant:
        if not self.available:
            raise AuthorizationRefused(
                "authority dependency unavailable", reason_code=Decision.DEPENDENCY_UNAVAILABLE
            )
        try:
            return self._grants[grant_id]
        except KeyError as exc:
            raise AuthorizationRefused(
                "authority grant is unknown", reason_code=Decision.AUTHORITY_REVOKED
            ) from exc

    def require(
        self,
        *,
        actor_id: str,
        capability: str,
        scope: ExactScope,
        now: datetime,
        actor_class: ActorClass = ActorClass.HUMAN,
        expected_version: int | None = None,
        approver_class: ApproverClass | None = None,
    ) -> AuthorityGrant:
        if not self.available:
            raise AuthorizationRefused(
                "authority dependency unavailable", reason_code=Decision.DEPENDENCY_UNAVAILABLE
            )
        candidates = [
            item
            for item in self._grants.values()
            if item.actor_id == actor_id
            and item.capability == capability
            and item.scope == scope
            and item.actor_class is actor_class
            and (approver_class is None or item.approver_class is approver_class)
        ]
        if not candidates:
            raise AuthorizationRefused("wrong actor or scope", reason_code=Decision.WRONG_SCOPE)
        grant = max(candidates, key=lambda item: item.version)
        if expected_version is not None and grant.version != expected_version:
            raise AuthorizationRefused(
                "authority version changed", reason_code=Decision.STALE_AUTHORITY
            )
        if grant.revoked:
            raise AuthorizationRefused("authority revoked", reason_code=Decision.AUTHORITY_REVOKED)
        if grant.suspended:
            raise AuthorizationRefused(
                "authority suspended", reason_code=Decision.AUTHORITY_SUSPENDED
            )
        if not grant.usable_at(now):
            raise AuthorizationRefused("authority expired", reason_code=Decision.GRANT_EXPIRED)
        return grant


@dataclass(frozen=True, slots=True)
class Approval:
    approver_id: str
    approver_class: ApproverClass
    authority_grant_id: str
    authority_version: int
    approved_at: datetime


@dataclass(frozen=True, slots=True)
class InterventionRequest:
    request_id: str
    level: InterventionLevel
    requester_id: str
    requester_authority_id: str
    requester_authority_version: int
    governance_basis: str
    scope: ExactScope
    target_ids: tuple[str, ...]
    reason: str
    evidence_refs: tuple[str, ...]
    not_before: datetime
    expires_at: datetime
    allowed_capabilities: frozenset[str]
    prohibited_capabilities: frozenset[str]
    quorum: int
    required_approver_classes: frozenset[ApproverClass]
    emergency: bool
    target_version: int
    state: WorkflowState = WorkflowState.REQUESTED
    approvals: tuple[Approval, ...] = ()
    activated_by: str | None = None
    activated_at: datetime | None = None
    ended_at: datetime | None = None
    review_ref: str | None = None


@dataclass(frozen=True, slots=True)
class PrivilegeGrant:
    grant_id: str
    kind: PrivilegeKind
    principal_id: str
    request_id: str
    scope: ExactScope
    capabilities: frozenset[str]
    not_before: datetime
    expires_at: datetime
    state: WorkflowState
    use_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class AuditEvent:
    sequence: int
    event_id: str
    actor_id: str
    authority_basis: str
    action: str
    target: str
    scope: str
    occurred_at: str
    result: str
    reason: str
    approval_refs: tuple[str, ...]
    prior_state_ref: str
    new_state_ref: str
    correlation_ref: str
    previous_hash: str
    event_hash: str


@dataclass(frozen=True, slots=True)
class ActionSpec:
    action_id: str
    route: str
    method: str
    required_capability: str
    mutation: bool
    commit_reauthorization: bool
    evidence_output: str


CTRL02_ACTIONS: Final = (
    ActionSpec(
        "CTRL02.REQUEST",
        "/ctrl/v2/interventions",
        "POST",
        "INTERVENTION.REQUEST",
        True,
        True,
        "request",
    ),
    ActionSpec(
        "CTRL02.APPROVE",
        "/ctrl/v2/interventions/{id}/approvals",
        "POST",
        "INTERVENTION.APPROVE",
        True,
        True,
        "approval",
    ),
    ActionSpec(
        "CTRL02.REJECT",
        "/ctrl/v2/interventions/{id}/rejection",
        "POST",
        "INTERVENTION.APPROVE",
        True,
        True,
        "rejection",
    ),
    ActionSpec(
        "CTRL02.CANCEL",
        "/ctrl/v2/interventions/{id}/cancellation",
        "POST",
        "INTERVENTION.REQUEST",
        True,
        True,
        "cancellation",
    ),
    ActionSpec(
        "CTRL02.ACTIVATE",
        "/ctrl/v2/interventions/{id}/activation",
        "POST",
        "INTERVENTION.EXECUTE",
        True,
        True,
        "activation",
    ),
    ActionSpec(
        "CTRL02.REVOKE",
        "/ctrl/v2/interventions/{id}/revocation",
        "POST",
        "INTERVENTION.REVOKE",
        True,
        True,
        "revocation",
    ),
    ActionSpec(
        "CTRL02.RESTORE",
        "/ctrl/v2/interventions/{id}/restoration",
        "POST",
        "INTERVENTION.RESTORE",
        True,
        True,
        "restoration",
    ),
    ActionSpec(
        "CTRL02.REVIEW",
        "/ctrl/v2/interventions/{id}/review",
        "POST",
        "INTERVENTION.REVIEW",
        True,
        True,
        "review",
    ),
    ActionSpec(
        "CTRL02.JIT.REQUEST",
        "/ctrl/v2/jit",
        "POST",
        "INTERVENTION.REQUEST",
        True,
        True,
        "jit_request",
    ),
    ActionSpec(
        "CTRL02.JIT.USE", "/ctrl/v2/jit/{id}/use", "POST", "PRIVILEGE.USE", True, True, "jit_use"
    ),
    ActionSpec(
        "CTRL02.BREAKGLASS.REQUEST",
        "/ctrl/v2/break-glass",
        "POST",
        "INTERVENTION.REQUEST",
        True,
        True,
        "breakglass_request",
    ),
    ActionSpec(
        "CTRL02.BREAKGLASS.USE",
        "/ctrl/v2/break-glass/{id}/use",
        "POST",
        "PRIVILEGE.USE",
        True,
        True,
        "breakglass_use",
    ),
    ActionSpec(
        "CTRL02.SERVICE.CONTAIN",
        "/ctrl/v2/service-credentials/{id}/contain",
        "POST",
        "SERVICE_CREDENTIAL.CONTAIN",
        True,
        True,
        "containment_ref",
    ),
    ActionSpec(
        "CTRL02.KEY.REQUEST",
        "/ctrl/v2/trust/requests",
        "POST",
        "TRUST.CHANGE_REQUEST",
        True,
        True,
        "trust_request_ref",
    ),
    ActionSpec(
        "CTRL02.READ.ACTIVE",
        "/ctrl/v2/interventions",
        "GET",
        "INTERVENTION.READ",
        False,
        False,
        "read_model",
    ),
    ActionSpec(
        "CTRL02.READ.PENDING",
        "/ctrl/v2/interventions/pending",
        "GET",
        "INTERVENTION.READ",
        False,
        False,
        "read_model",
    ),
    ActionSpec(
        "CTRL02.READ.HISTORY",
        "/ctrl/v2/interventions/{id}/history",
        "GET",
        "INTERVENTION.AUDIT",
        False,
        False,
        "history",
    ),
)


class RegionalOperationsService:
    """Thread-safe in-memory reference implementation of the CTRL-02 contract."""

    def __init__(self, authorities: AuthorityDirectory) -> None:
        self.authorities = authorities
        self._requests: dict[str, InterventionRequest] = {}
        self._grants: dict[str, PrivilegeGrant] = {}
        self._events: list[AuditEvent] = []
        self._target_versions: dict[str, int] = {}
        self._authority_states: dict[str, str] = {}
        self._sessions: dict[str, str] = {}
        self._idempotency: dict[tuple[str, str], tuple[str, str]] = {}
        self._last_time = datetime.min.replace(tzinfo=UTC)
        self._lock = threading.RLock()

    @property
    def events(self) -> tuple[AuditEvent, ...]:
        return tuple(self._events)

    @property
    def requests(self) -> tuple[InterventionRequest, ...]:
        return tuple(self._requests.values())

    @property
    def grants(self) -> tuple[PrivilegeGrant, ...]:
        return tuple(self._grants.values())

    def set_target_version(self, target_id: str, version: int) -> None:
        self._target_versions[target_id] = version

    def _time(self, supplied: datetime) -> datetime:
        if supplied.tzinfo is None:
            raise ValueError("server time must be timezone-aware")
        if supplied < self._last_time:
            return self._last_time
        self._last_time = supplied
        return supplied

    @staticmethod
    def _validate_exact(values: Iterable[str], label: str) -> tuple[str, ...]:
        result = tuple(sorted(set(values)))
        if not result or any(item in COARSE_TARGETS or "*" in item for item in result):
            raise AuthorizationRefused(
                f"{label} must be exact and non-empty", reason_code=Decision.WRONG_SCOPE
            )
        return result

    @staticmethod
    def _validate_capabilities(values: Iterable[str]) -> frozenset[str]:
        result = frozenset(values)
        if not result or result & ABSOLUTE_PROHIBITIONS or any("*" in item for item in result):
            reason = (
                Decision.VOTING_BOUNDARY if result & VOTING_PROHIBITED else Decision.WRONG_SCOPE
            )
            raise AuthorizationRefused("capability scope is prohibited", reason_code=reason)
        return result

    def _once(
        self, action: str, key: str, payload: Mapping[str, Any], result_id: str
    ) -> str | None:
        digest = hashlib.sha256(
            json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode()
        ).hexdigest()
        prior = self._idempotency.get((action, key))
        if prior is None:
            self._idempotency[(action, key)] = (digest, result_id)
            return None
        if prior[0] != digest:
            raise AuthorizationRefused(
                "idempotency key reused with another payload", reason_code="IDEMPOTENCY_CONFLICT"
            )
        return prior[1]

    def _record(
        self,
        *,
        actor: str,
        authority: str,
        action: str,
        target: str,
        scope: ExactScope,
        now: datetime,
        result: str,
        reason: str,
        approvals: tuple[str, ...] = (),
        prior: str = "NONE",
        new: str = "NONE",
        correlation: str,
    ) -> AuditEvent:
        payload: dict[str, Any] = {
            "sequence": len(self._events) + 1,
            "actor_id": actor,
            "authority_basis": authority,
            "action": action,
            "target": target,
            "scope": scope.key,
            "occurred_at": now.isoformat(),
            "result": result,
            "reason": reason,
            "approval_refs": approvals,
            "prior_state_ref": prior,
            "new_state_ref": new,
            "correlation_ref": correlation,
            "previous_hash": self._events[-1].event_hash if self._events else "GENESIS",
        }
        forbidden = {"ballot", "voter_id", "vote_choice", "raw_secret", "provider_secret"}
        if forbidden & set(payload):
            raise AuthorizationRefused("unsafe evidence fields", reason_code="PRIVACY_BOUNDARY")
        encoded = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
        event_hash = hashlib.sha256(encoded.encode()).hexdigest()
        event = AuditEvent(
            event_id=f"ctrl02-event-{payload['sequence']:08d}", event_hash=event_hash, **payload
        )
        self._events.append(event)
        return event

    @staticmethod
    def _requirements(level: InterventionLevel) -> tuple[int, frozenset[ApproverClass]]:
        if level is InterventionLevel.SESSION_QUARANTINE:
            return 1, frozenset({ApproverClass.SECURITY})
        if level is InterventionLevel.TEMPORARY_SUPERVISION:
            return 2, frozenset({ApproverClass.GOVERNANCE, ApproverClass.SECURITY})
        return 2, frozenset({ApproverClass.GOVERNANCE})

    def request_intervention(
        self,
        *,
        request_id: str,
        level: InterventionLevel,
        requester_id: str,
        governance_basis: str,
        scope: ExactScope,
        target_ids: Iterable[str],
        reason: str,
        evidence_refs: Iterable[str],
        not_before: datetime,
        expires_at: datetime,
        allowed_capabilities: Iterable[str],
        prohibited_capabilities: Iterable[str] = (),
        emergency: bool = False,
        target_version: int,
        idempotency_key: str,
    ) -> InterventionRequest:
        with self._lock:
            now = self._time(not_before)
            targets = self._validate_exact(target_ids, "target")
            allowed = self._validate_capabilities(allowed_capabilities)
            prohibited = frozenset(prohibited_capabilities)
            if not governance_basis.strip() or not reason.strip() or not tuple(evidence_refs):
                raise AuthorizationRefused(
                    "basis, reason and evidence are mandatory",
                    reason_code="MISSING_GOVERNANCE_BASIS",
                )
            if expires_at <= now:
                raise AuthorizationRefused(
                    "expiry must be future", reason_code=Decision.GRANT_EXPIRED
                )
            if (
                level is InterventionLevel.TEMPORARY_SUPERVISION
                and expires_at - now > MAX_SUPERVISION
            ):
                raise AuthorizationRefused(
                    "supervision exceeds maximum TTL", reason_code="TTL_TOO_LONG"
                )
            if level is InterventionLevel.SESSION_QUARANTINE and any(
                not target.startswith(("session:", "subject:")) for target in targets
            ):
                raise AuthorizationRefused(
                    "L1 targets sessions only", reason_code=Decision.WRONG_SCOPE
                )
            if level is InterventionLevel.AUTHORITY_SUSPENSION and any(
                not target.startswith("authority:") for target in targets
            ):
                raise AuthorizationRefused(
                    "L2 targets authority grants only", reason_code=Decision.WRONG_SCOPE
                )
            prior = self._once(
                "request",
                idempotency_key,
                {"id": request_id, "level": level, "scope": scope, "targets": targets},
                request_id,
            )
            if prior is not None:
                return self._requests[prior]
            authority = self.authorities.require(
                actor_id=requester_id,
                capability="INTERVENTION.REQUEST",
                scope=scope,
                now=now,
            )
            quorum, classes = self._requirements(level)
            request = InterventionRequest(
                request_id=request_id,
                level=level,
                requester_id=requester_id,
                requester_authority_id=authority.grant_id,
                requester_authority_version=authority.version,
                governance_basis=governance_basis,
                scope=scope,
                target_ids=targets,
                reason=reason,
                evidence_refs=tuple(evidence_refs),
                not_before=now,
                expires_at=expires_at,
                allowed_capabilities=allowed,
                prohibited_capabilities=prohibited,
                quorum=quorum,
                required_approver_classes=classes,
                emergency=emergency,
                target_version=target_version,
            )
            self._requests[request_id] = request
            self._record(
                actor=requester_id,
                authority=authority.grant_id,
                action="REQUEST",
                target=request_id,
                scope=scope,
                now=now,
                result="RECORDED",
                reason=reason,
                new=WorkflowState.REQUESTED,
                correlation=request_id,
            )
            return request

    def approve(
        self,
        request_id: str,
        *,
        approver_id: str,
        approver_class: ApproverClass,
        now: datetime,
        idempotency_key: str,
    ) -> InterventionRequest:
        with self._lock:
            moment = self._time(now)
            request = self._require_request(request_id)
            prior = self._once(
                "approve",
                idempotency_key,
                {"request": request_id, "approver": approver_id, "class": approver_class},
                request_id,
            )
            if prior is not None:
                return self._requests[prior]
            if request.state not in {WorkflowState.REQUESTED, WorkflowState.REVIEWING}:
                raise AuthorizationRefused("request cannot be approved", reason_code="WRONG_STATE")
            if approver_id == request.requester_id or approver_id in {
                approval.approver_id for approval in request.approvals
            }:
                raise AuthorizationRefused(
                    "self or duplicate approval", reason_code=Decision.SELF_APPROVAL_FORBIDDEN
                )
            authority = self.authorities.require(
                actor_id=approver_id,
                capability="INTERVENTION.APPROVE",
                scope=request.scope,
                now=moment,
                approver_class=approver_class,
            )
            approval = Approval(
                approver_id, approver_class, authority.grant_id, authority.version, moment
            )
            approvals = (*request.approvals, approval)
            classes = {item.approver_class for item in approvals}
            state = (
                WorkflowState.APPROVED
                if len(approvals) >= request.quorum and request.required_approver_classes <= classes
                else WorkflowState.REVIEWING
            )
            updated = replace(request, approvals=approvals, state=state)
            self._requests[request_id] = updated
            self._record(
                actor=approver_id,
                authority=authority.grant_id,
                action="APPROVE",
                target=request_id,
                scope=request.scope,
                now=moment,
                result=state,
                reason="governed approval",
                approvals=tuple(item.authority_grant_id for item in approvals),
                prior=request.state,
                new=state,
                correlation=request_id,
            )
            return updated

    def _reauthorize(self, request: InterventionRequest, now: datetime) -> None:
        self.authorities.require(
            actor_id=request.requester_id,
            capability="INTERVENTION.REQUEST",
            scope=request.scope,
            now=now,
            expected_version=request.requester_authority_version,
        )
        if (
            self._target_versions.get(request.target_ids[0], request.target_version)
            != request.target_version
        ):
            raise AuthorizationRefused("target changed", reason_code=Decision.STALE_TARGET)
        for approval in request.approvals:
            self.authorities.require(
                actor_id=approval.approver_id,
                capability="INTERVENTION.APPROVE",
                scope=request.scope,
                now=now,
                expected_version=approval.authority_version,
                approver_class=approval.approver_class,
            )

    def activate(
        self,
        request_id: str,
        *,
        executor_id: str,
        now: datetime,
        idempotency_key: str,
    ) -> InterventionRequest:
        with self._lock:
            moment = self._time(now)
            request = self._require_request(request_id)
            prior = self._once(
                "activate",
                idempotency_key,
                {"request": request_id, "executor": executor_id},
                request_id,
            )
            if prior is not None:
                return self._requests[prior]
            if request.state is not WorkflowState.APPROVED:
                raise AuthorizationRefused("quorum not met", reason_code=Decision.QUORUM_NOT_MET)
            if executor_id in {request.requester_id, *(a.approver_id for a in request.approvals)}:
                raise AuthorizationRefused(
                    "approval is not execution", reason_code="EXECUTION_SEPARATION"
                )
            if moment < request.not_before or moment >= request.expires_at:
                raise AuthorizationRefused(
                    "request expired or not active", reason_code=Decision.GRANT_EXPIRED
                )
            self._reauthorize(request, moment)
            authority = self.authorities.require(
                actor_id=executor_id,
                capability="INTERVENTION.EXECUTE",
                scope=request.scope,
                now=moment,
            )
            for target in request.target_ids:
                if request.level is InterventionLevel.SESSION_QUARANTINE:
                    self._sessions[target] = "QUARANTINED"
                elif request.level is InterventionLevel.AUTHORITY_SUSPENSION:
                    self._authority_states[target] = "SUSPENDED"
            updated = replace(
                request,
                state=WorkflowState.ACTIVE,
                activated_by=executor_id,
                activated_at=moment,
            )
            self._requests[request_id] = updated
            self._record(
                actor=executor_id,
                authority=authority.grant_id,
                action="ACTIVATE",
                target=request_id,
                scope=request.scope,
                now=moment,
                result="ACTIVE",
                reason=request.reason,
                approvals=tuple(a.authority_grant_id for a in request.approvals),
                prior=request.state,
                new=WorkflowState.ACTIVE,
                correlation=request_id,
            )
            return updated

    def revoke(
        self, request_id: str, *, actor_id: str, now: datetime, idempotency_key: str
    ) -> InterventionRequest:
        with self._lock:
            moment = self._time(now)
            request = self._require_request(request_id)
            prior = self._once(
                "revoke",
                idempotency_key,
                {"request": request_id, "actor": actor_id},
                request_id,
            )
            if prior is not None:
                return self._requests[prior]
            authority = self.authorities.require(
                actor_id=actor_id,
                capability="INTERVENTION.REVOKE",
                scope=request.scope,
                now=moment,
            )
            if request.state in TERMINAL_STATES:
                return request
            updated = replace(request, state=WorkflowState.REVOKED, ended_at=moment)
            self._requests[request_id] = updated
            self._record(
                actor=actor_id,
                authority=authority.grant_id,
                action="REVOKE",
                target=request_id,
                scope=request.scope,
                now=moment,
                result="REVOKED",
                reason="governed revocation",
                prior=request.state,
                new=WorkflowState.REVOKED,
                correlation=request_id,
            )
            return updated

    def reject(
        self,
        request_id: str,
        *,
        approver_id: str,
        approver_class: ApproverClass,
        reason: str,
        now: datetime,
    ) -> InterventionRequest:
        """Reject a pending request without granting execution authority."""
        with self._lock:
            moment = self._time(now)
            request = self._require_request(request_id)
            if request.state not in {
                WorkflowState.REQUESTED,
                WorkflowState.REVIEWING,
                WorkflowState.APPROVED,
            }:
                raise AuthorizationRefused("request cannot be rejected", reason_code="WRONG_STATE")
            authority = self.authorities.require(
                actor_id=approver_id,
                capability="INTERVENTION.APPROVE",
                scope=request.scope,
                now=moment,
                approver_class=approver_class,
            )
            updated = replace(request, state=WorkflowState.REJECTED, ended_at=moment)
            self._requests[request_id] = updated
            self._record(
                actor=approver_id,
                authority=authority.grant_id,
                action="REJECT",
                target=request_id,
                scope=request.scope,
                now=moment,
                result="REJECTED",
                reason=reason,
                prior=request.state,
                new=WorkflowState.REJECTED,
                correlation=request_id,
            )
            return updated

    def cancel(self, request_id: str, *, requester_id: str, now: datetime) -> InterventionRequest:
        """Only the still-authorized requester may cancel before activation."""
        with self._lock:
            moment = self._time(now)
            request = self._require_request(request_id)
            if requester_id != request.requester_id or request.state not in {
                WorkflowState.REQUESTED,
                WorkflowState.REVIEWING,
                WorkflowState.APPROVED,
            }:
                raise AuthorizationRefused("cancellation forbidden", reason_code="WRONG_STATE")
            self.authorities.require(
                actor_id=requester_id,
                capability="INTERVENTION.REQUEST",
                scope=request.scope,
                now=moment,
                expected_version=request.requester_authority_version,
            )
            updated = replace(request, state=WorkflowState.CANCELLED, ended_at=moment)
            self._requests[request_id] = updated
            self._record(
                actor=requester_id,
                authority=request.requester_authority_id,
                action="CANCEL",
                target=request_id,
                scope=request.scope,
                now=moment,
                result="CANCELLED",
                reason="requester cancellation",
                prior=request.state,
                new=WorkflowState.CANCELLED,
                correlation=request_id,
            )
            return updated

    def restore(
        self,
        request_id: str,
        *,
        actor_id: str,
        original_authority_valid: bool,
        newer_conflict: bool,
        now: datetime,
    ) -> InterventionRequest:
        """Restore exact targets only when their original basis remains valid."""
        with self._lock:
            moment = self._time(now)
            request = self._require_request(request_id)
            if request.state not in {
                WorkflowState.REVOKED,
                WorkflowState.EXPIRED,
                WorkflowState.POST_REVIEWED,
            }:
                raise AuthorizationRefused("restoration state invalid", reason_code="WRONG_STATE")
            if not original_authority_valid or newer_conflict:
                raise AuthorizationRefused(
                    "restoration conflicts with authority history",
                    reason_code=Decision.AUTHORITY_REVOKED,
                )
            authority = self.authorities.require(
                actor_id=actor_id,
                capability="INTERVENTION.RESTORE",
                scope=request.scope,
                now=moment,
            )
            for target in request.target_ids:
                if request.level is InterventionLevel.SESSION_QUARANTINE:
                    self._sessions[target] = "ACTIVE"
                elif request.level is InterventionLevel.AUTHORITY_SUSPENSION:
                    self._authority_states[target] = "ACTIVE"
            updated = replace(request, state=WorkflowState.COMPLETED, ended_at=moment)
            self._requests[request_id] = updated
            self._record(
                actor=actor_id,
                authority=authority.grant_id,
                action="RESTORE",
                target=request_id,
                scope=request.scope,
                now=moment,
                result="COMPLETED",
                reason="exact governed restoration",
                prior=request.state,
                new=WorkflowState.COMPLETED,
                correlation=request_id,
            )
            return updated

    def service_credential_control(
        self,
        *,
        credential_id: str,
        operation: str,
        actor_id: str,
        scope: ExactScope,
        now: datetime,
        evidence_ref: str,
        secret_material: str | None = None,
    ) -> str:
        """Control credential state by reference; raw secret material is forbidden."""
        allowed = {"SUSPEND", "REVOKE", "ROTATE_REQUEST", "EMERGENCY_CONTAIN", "STATUS"}
        if operation not in allowed or secret_material is not None:
            raise AuthorizationRefused(
                "unsupported operation or raw secret supplied", reason_code="SECRET_VISIBILITY"
            )
        moment = self._time(now)
        capability = (
            "SERVICE_CREDENTIAL.READ" if operation == "STATUS" else "SERVICE_CREDENTIAL.CONTAIN"
        )
        authority = self.authorities.require(
            actor_id=actor_id, capability=capability, scope=scope, now=moment
        )
        correlation = f"service-credential:{credential_id}:{operation}:{len(self._events) + 1}"
        self._record(
            actor=actor_id,
            authority=authority.grant_id,
            action=f"SERVICE_CREDENTIAL.{operation}",
            target=credential_id,
            scope=scope,
            now=moment,
            result="RECORDED",
            reason=evidence_ref,
            correlation=correlation,
        )
        return correlation

    def key_trust_change_request(
        self,
        *,
        request_ref: str,
        operation: str,
        key_reference: str,
        actor_id: str,
        scope: ExactScope,
        now: datetime,
        evidence_ref: str,
        secret_material: str | None = None,
    ) -> str:
        """Record a governed custody request; never perform provider custody itself."""
        allowed = {"ROTATE", "CONTAIN_COMPROMISE", "REVOKE", "DISABLE", "TRUST_SET_CHANGE"}
        if operation not in allowed or secret_material is not None:
            raise AuthorizationRefused("key custody boundary", reason_code="KEY_CUSTODY_BOUNDARY")
        moment = self._time(now)
        authority = self.authorities.require(
            actor_id=actor_id,
            capability="TRUST.CHANGE_REQUEST",
            scope=scope,
            now=moment,
        )
        self._record(
            actor=actor_id,
            authority=authority.grant_id,
            action=f"TRUST.{operation}.REQUEST",
            target=key_reference,
            scope=scope,
            now=moment,
            result="REQUEST_RECORDED_NOT_EXECUTED",
            reason=evidence_ref,
            correlation=request_ref,
        )
        return request_ref

    def expire_due(self, now: datetime) -> tuple[str, ...]:
        with self._lock:
            moment = self._time(now)
            expired: list[str] = []
            for request_id, request in tuple(self._requests.items()):
                if request.state is WorkflowState.ACTIVE and moment >= request.expires_at:
                    self._requests[request_id] = replace(
                        request, state=WorkflowState.EXPIRED, ended_at=moment
                    )
                    expired.append(request_id)
            for grant_id, grant in tuple(self._grants.items()):
                if grant.state is WorkflowState.ACTIVE and moment >= grant.expires_at:
                    self._grants[grant_id] = replace(grant, state=WorkflowState.EXPIRED)
                    expired.append(grant_id)
            return tuple(expired)

    def post_review(
        self, request_id: str, *, reviewer_id: str, review_ref: str, now: datetime
    ) -> InterventionRequest:
        with self._lock:
            moment = self._time(now)
            request = self._require_request(request_id)
            if request.state not in {
                WorkflowState.EXPIRED,
                WorkflowState.REVOKED,
                WorkflowState.COMPLETED,
            }:
                raise AuthorizationRefused("review is post-use", reason_code="WRONG_STATE")
            participants = {
                request.requester_id,
                request.activated_by,
                *(approval.approver_id for approval in request.approvals),
            }
            if reviewer_id in participants:
                raise AuthorizationRefused("independent review required", reason_code="SELF_REVIEW")
            authority = self.authorities.require(
                actor_id=reviewer_id,
                capability="INTERVENTION.REVIEW",
                scope=request.scope,
                now=moment,
            )
            updated = replace(request, state=WorkflowState.POST_REVIEWED, review_ref=review_ref)
            self._requests[request_id] = updated
            self._record(
                actor=reviewer_id,
                authority=authority.grant_id,
                action="POST_REVIEW",
                target=request_id,
                scope=request.scope,
                now=moment,
                result="POST_REVIEWED",
                reason=review_ref,
                prior=request.state,
                new=WorkflowState.POST_REVIEWED,
                correlation=request_id,
            )
            return updated

    def create_privilege_request(
        self,
        *,
        request_id: str,
        kind: PrivilegeKind,
        principal_id: str,
        requester_id: str,
        scope: ExactScope,
        capabilities: Iterable[str],
        reason: str,
        evidence_refs: Iterable[str],
        now: datetime,
        expires_at: datetime,
        target_version: int,
        idempotency_key: str,
    ) -> InterventionRequest:
        lifetime = expires_at - now
        limit = MAX_JIT if kind is PrivilegeKind.JIT else MAX_BREAK_GLASS
        if lifetime <= timedelta(0) or lifetime > limit:
            raise AuthorizationRefused("privilege TTL invalid", reason_code="TTL_TOO_LONG")
        return self.request_intervention(
            request_id=request_id,
            level=InterventionLevel.TEMPORARY_SUPERVISION,
            requester_id=requester_id,
            governance_basis=f"{kind.value}_POLICY",
            scope=scope,
            target_ids=(f"principal:{principal_id}",),
            reason=reason,
            evidence_refs=evidence_refs,
            not_before=now,
            expires_at=expires_at,
            allowed_capabilities=capabilities,
            prohibited_capabilities=ABSOLUTE_PROHIBITIONS,
            emergency=kind is PrivilegeKind.BREAK_GLASS,
            target_version=target_version,
            idempotency_key=idempotency_key,
        )

    def materialize_privilege(
        self, request_id: str, *, kind: PrivilegeKind, principal_id: str
    ) -> PrivilegeGrant:
        with self._lock:
            request = self._require_request(request_id)
            if request.state is not WorkflowState.ACTIVE:
                raise AuthorizationRefused("request is not active", reason_code="WRONG_STATE")
            if request.target_ids != (f"principal:{principal_id}",):
                raise AuthorizationRefused(
                    "wrong privilege target", reason_code=Decision.WRONG_SCOPE
                )
            grant_id = f"{kind.value.lower()}:{request_id}"
            grant = PrivilegeGrant(
                grant_id=grant_id,
                kind=kind,
                principal_id=principal_id,
                request_id=request_id,
                scope=request.scope,
                capabilities=request.allowed_capabilities,
                not_before=request.not_before,
                expires_at=request.expires_at,
                state=WorkflowState.ACTIVE,
            )
            self._grants[grant_id] = grant
            return grant

    def use_privilege(
        self,
        grant_id: str,
        *,
        principal_id: str,
        capability: str,
        scope: ExactScope,
        now: datetime,
        use_ref: str,
    ) -> PrivilegeGrant:
        with self._lock:
            moment = self._time(now)
            self.expire_due(moment)
            grant = self._grants[grant_id]
            if grant.state is not WorkflowState.ACTIVE or moment >= grant.expires_at:
                raise AuthorizationRefused("grant expired", reason_code=Decision.GRANT_EXPIRED)
            if principal_id != grant.principal_id or scope != grant.scope:
                raise AuthorizationRefused(
                    "wrong target or scope", reason_code=Decision.WRONG_SCOPE
                )
            if capability not in grant.capabilities or capability in ABSOLUTE_PROHIBITIONS:
                raise AuthorizationRefused(
                    "capability not granted", reason_code=Decision.WRONG_SCOPE
                )
            decision = self.effective_decision(
                session_id=None,
                authority_id=None,
                capability=capability,
                scope=scope,
                now=moment,
            )
            if decision is not Decision.ALLOW:
                raise AuthorizationRefused("active restriction wins", reason_code=decision)
            updated = replace(grant, use_refs=(*grant.use_refs, use_ref))
            self._grants[grant_id] = updated
            return updated

    def effective_decision(
        self,
        *,
        session_id: str | None,
        authority_id: str | None,
        capability: str,
        scope: ExactScope,
        now: datetime,
        session_owner_id: str | None = None,
    ) -> Decision:
        moment = self._time(now)
        if not self.authorities.available:
            return Decision.DEPENDENCY_UNAVAILABLE
        if capability in VOTING_PROHIBITED:
            return Decision.VOTING_BOUNDARY
        if authority_id and self._authority_states.get(authority_id) == "REVOKED":
            return Decision.AUTHORITY_REVOKED
        if authority_id and self._authority_states.get(authority_id) == "SUSPENDED":
            return Decision.AUTHORITY_SUSPENDED
        if session_id and self._sessions.get(session_id) == "QUARANTINED":
            return Decision.SESSION_QUARANTINED
        if session_owner_id and self._sessions.get(f"subject:{session_owner_id}") == "QUARANTINED":
            return Decision.SESSION_QUARANTINED
        for request in self._requests.values():
            if request.state is not WorkflowState.ACTIVE or request.scope != scope:
                continue
            if moment >= request.expires_at:
                continue
            if (
                request.level is InterventionLevel.REGIONAL_ACTION_RESTRICTION
                and capability in request.allowed_capabilities
            ):
                return Decision.ACTION_RESTRICTED
        return Decision.ALLOW

    def active_interventions(self) -> tuple[InterventionRequest, ...]:
        return tuple(item for item in self._requests.values() if item.state is WorkflowState.ACTIVE)

    def pending_requests(self) -> tuple[InterventionRequest, ...]:
        return tuple(
            item
            for item in self._requests.values()
            if item.state
            in {WorkflowState.REQUESTED, WorkflowState.REVIEWING, WorkflowState.APPROVED}
        )

    def pending_reviews(self) -> tuple[InterventionRequest, ...]:
        return tuple(
            item
            for item in self._requests.values()
            if item.state in {WorkflowState.EXPIRED, WorkflowState.REVOKED, WorkflowState.COMPLETED}
            and item.review_ref is None
        )

    def checkpoint(self) -> dict[str, Any]:
        """Return recovery data. Terminal states are preserved verbatim."""
        return {
            "requests": {key: asdict(value) for key, value in self._requests.items()},
            "grants": {key: asdict(value) for key, value in self._grants.items()},
            "authority_states": dict(self._authority_states),
            "sessions": dict(self._sessions),
            "events": [asdict(event) for event in self._events],
            "last_time": self._last_time.isoformat(),
        }

    @classmethod
    def from_checkpoint(
        cls, authorities: AuthorityDirectory, snapshot: Mapping[str, Any]
    ) -> RegionalOperationsService:
        """Recover durable state without reviving terminal grants or requests."""
        service = cls(authorities)
        service._last_time = datetime.fromisoformat(str(snapshot["last_time"]))
        service._authority_states = dict(snapshot["authority_states"])
        service._sessions = dict(snapshot["sessions"])
        for request_id, raw in dict(snapshot["requests"]).items():
            data = dict(raw)
            data["level"] = InterventionLevel(data["level"])
            data["scope"] = ExactScope(**dict(data["scope"]))
            data["state"] = WorkflowState(data["state"])
            data["allowed_capabilities"] = frozenset(data["allowed_capabilities"])
            data["prohibited_capabilities"] = frozenset(data["prohibited_capabilities"])
            data["required_approver_classes"] = frozenset(
                ApproverClass(value) for value in data["required_approver_classes"]
            )
            data["target_ids"] = tuple(data["target_ids"])
            data["evidence_refs"] = tuple(data["evidence_refs"])
            data["approvals"] = tuple(
                Approval(
                    approver_id=item["approver_id"],
                    approver_class=ApproverClass(item["approver_class"]),
                    authority_grant_id=item["authority_grant_id"],
                    authority_version=item["authority_version"],
                    approved_at=_as_datetime(item["approved_at"]),
                )
                for item in data["approvals"]
            )
            for field_name in ("not_before", "expires_at", "activated_at", "ended_at"):
                if data[field_name] is not None:
                    data[field_name] = _as_datetime(data[field_name])
            service._requests[str(request_id)] = InterventionRequest(**data)
        for grant_id, raw in dict(snapshot["grants"]).items():
            data = dict(raw)
            data["kind"] = PrivilegeKind(data["kind"])
            data["scope"] = ExactScope(**dict(data["scope"]))
            data["capabilities"] = frozenset(data["capabilities"])
            data["state"] = WorkflowState(data["state"])
            data["use_refs"] = tuple(data["use_refs"])
            data["not_before"] = _as_datetime(data["not_before"])
            data["expires_at"] = _as_datetime(data["expires_at"])
            service._grants[str(grant_id)] = PrivilegeGrant(**data)
        for raw in snapshot["events"]:
            data = dict(raw)
            data["approval_refs"] = tuple(data["approval_refs"])
            service._events.append(AuditEvent(**data))
        return service

    def _require_request(self, request_id: str) -> InterventionRequest:
        try:
            return self._requests[request_id]
        except KeyError as exc:
            raise AuthorizationRefused("unknown request", reason_code="UNKNOWN_REQUEST") from exc


def action_inventory() -> list[dict[str, Any]]:
    """Machine-readable route/action inventory derived from runtime declarations."""
    return [asdict(item) for item in CTRL02_ACTIONS]


def _as_datetime(value: object) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))
