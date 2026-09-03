"""CTRL-04 governed Operations Console reference runtime.

The console is a bounded, auditable, policy-constrained command surface over
operational capabilities that INFRA/OPS/runtime domains already own. It is
not a deployment engine, a backup engine, a monitoring backend, a secret store
or a universal admin surface. Every privileged operation follows

    REQUEST -> POLICY/AUTHORITY CHECK -> OPTIONAL APPROVAL
            -> COMMIT-TIME REAUTHORIZATION -> EXECUTION DISPATCH
            -> RESULT -> EVIDENCE -> REVIEW STATE

and no stage collapses request, approval, execution, secret visibility and
review into one operator capability. Provider-specific execution stays behind
the `OperationsAdapter` boundary in `operations_adapters.py`.

Authority comes from the CTRL-02 exact-scope `AuthorityDirectory`; active
CTRL-02 restrictions and quarantines arrive through the explicit CTRL-03
`Ctrl02State` adapter; artifact trust for rollback comes from an explicit
CTRL-03 trust-set adapter. Nothing here creates authority that is absent from
those governed sources.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import threading
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field, fields, replace
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any, Final

from epd2_control_plane_service.audit import EvidenceJournal
from epd2_control_plane_service.credential_lifecycle import Ctrl02State
from epd2_control_plane_service.exceptions import AuthorizationRefused
from epd2_control_plane_service.operations_adapters import (
    AdapterCapability,
    BackendOutcome,
    BackendState,
    DispatchRequest,
    OperationsAdapter,
    redact_metadata,
    scrub_text,
)
from epd2_control_plane_service.regional_operations import (
    ActorClass,
    ApproverClass,
    AuthorityDirectory,
    AuthorityGrant,
    ExactScope,
)
from epd2_core.canonical_json import canonical_dumps

__all__ = [
    "ACTION_CATALOGUE",
    "CTRL04_ACTIONS",
    "ActionState",
    "ActionType",
    "ApprovalState",
    "AuthorityProjection",
    "AuthorityProjectionSigner",
    "AuthorizationDecision",
    "BackupRestoreOperationRef",
    "ConsoleSession",
    "Ctrl03TrustState",
    "DeploymentIdentity",
    "EnvironmentClass",
    "EvidenceSealer",
    "ExecutionState",
    "FailureClassification",
    "HealthSnapshot",
    "HealthState",
    "ImpactClass",
    "JobQueueSnapshot",
    "MaintenanceWindowRef",
    "MaintenanceWindowState",
    "OperationalActionRequest",
    "OperationalActionSpec",
    "OperationalApproval",
    "OperationalEvidenceRef",
    "OperationalExecution",
    "OperationalIncidentRef",
    "OperationalResult",
    "OperationalTarget",
    "OperationsConsoleService",
    "OperationsPolicy",
    "OpsRefusal",
    "ResultState",
    "ReviewState",
    "SessionState",
    "TargetClass",
    "TargetDomain",
    "parameters_digest",
]

# ---------------------------------------------------------------------------
# Governed constants. Each is a declared obligation; the mutation suite flips
# them one at a time and proves that the executable tests notice.
# ---------------------------------------------------------------------------

SELF_STATE: Final = "CANDIDATE_NOT_ACCEPTED"
STAGE: Final = "CTRL-04"
POLICY_VERSION: Final = "ctrl04-policy/1"
UNIVERSAL_ADMIN_EXISTS: Final = False
DIRECT_SHELL_SURFACE_EXISTS: Final = False
ARBITRARY_SQL_SURFACE_EXISTS: Final = False
BROWSER_STATE_IS_AUTHORITATIVE: Final = False
DISPATCH_ACK_IS_SUCCESS: Final = False
MUTATION_FIXTURES_REQUIRED: Final = 48
GATES_REQUIRED: Final = 52
CTRL01_ACCEPTED_SHA256: Final = "07134db175587a9aa441fe87a811c7cfca6cc8dfbd30006279dd0edb598783b5"
CTRL02_ACCEPTED_SHA256: Final = "f58bafe758f19c0b40d3a525d85d0315052c01bc9ed14eae9973079a4dfb993e"
CTRL03_ACCEPTED_SHA256: Final = "89fca0f6c975a7c0e1eb70c2e3ad5229830e781c91d86637a81f99e39ac7b0ff"
MAX_REQUEST_LIFETIME: Final = timedelta(hours=4)
MAX_APPROVAL_LIFETIME: Final = timedelta(minutes=30)
MAX_PROJECTION_LIFETIME: Final = timedelta(minutes=5)
MAX_MAINTENANCE_WINDOW: Final = timedelta(hours=8)
MAX_EXECUTION_WAIT: Final = timedelta(minutes=30)
DESTRUCTIVE_CONFIRMATION_PREFIX: Final = "CONFIRM-DESTRUCTIVE:"
COARSE_TARGETS: Final = frozenset({"*", "ALL", "GLOBAL", "REGION", "REGION_DISABLED"})
GENERAL_CONSOLE_ID: Final = "CONSOLE_OPERATIONS"
GENERAL_DESK_ID: Final = "DESK_PLATFORM_OPERATIONS"


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class TargetClass(StrEnum):
    SERVICE = "SERVICE"
    ENVIRONMENT = "ENVIRONMENT"
    JOB_QUEUE = "JOB_QUEUE"
    INTEGRATION = "INTEGRATION"
    DATASTORE = "DATASTORE"
    BACKUP_SET = "BACKUP_SET"


class TargetDomain(StrEnum):
    GENERAL = "GENERAL"
    VOTING = "VOTING"


class EnvironmentClass(StrEnum):
    PRODUCTION_LIKE = "PRODUCTION_LIKE"
    NON_PRODUCTION = "NON_PRODUCTION"


class HealthState(StrEnum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"
    UNKNOWN = "UNKNOWN"


class ImpactClass(StrEnum):
    READ = "READ"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    DESTRUCTIVE = "DESTRUCTIVE"


class ActionType(StrEnum):
    STATUS_READ = "OPS.STATUS.READ"
    HEALTH_READ = "OPS.HEALTH.READ"
    JOBS_READ = "OPS.JOBS.READ"
    INTEGRATION_READ = "OPS.INTEGRATION.READ"
    DEPLOYMENT_IDENTITY_READ = "OPS.DEPLOYMENT_IDENTITY.READ"
    RECOVERY_READINESS_READ = "OPS.RECOVERY_READINESS.READ"
    BACKUP_STATUS_READ = "OPS.BACKUP.STATUS.READ"
    INCIDENT_READ = "OPS.INCIDENT.READ"
    ACTION_HISTORY_READ = "OPS.ACTION_HISTORY.READ"
    EVIDENCE_LOOKUP = "OPS.EVIDENCE.LOOKUP"
    SERVICE_RESTART = "OPS.SERVICE.RESTART"
    DEPLOYMENT_ROLLBACK = "OPS.DEPLOYMENT.ROLLBACK"
    MAINTENANCE_ENTER = "OPS.MAINTENANCE.ENTER"
    MAINTENANCE_EXIT = "OPS.MAINTENANCE.EXIT"
    JOB_QUEUE_PAUSE = "OPS.JOB_QUEUE.PAUSE"
    JOB_QUEUE_RESUME = "OPS.JOB_QUEUE.RESUME"
    BACKUP_REQUEST = "OPS.BACKUP.REQUEST"
    RESTORE_REQUEST = "OPS.RESTORE.REQUEST"
    INCIDENT_LINK = "OPS.INCIDENT.LINK"


class ActionState(StrEnum):
    REQUESTED = "REQUESTED"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    APPROVED = "APPROVED"
    EXECUTING = "EXECUTING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    PARTIAL_FAILURE = "PARTIAL_FAILURE"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    UNSUPPORTED = "UNSUPPORTED"
    REFUSED = "REFUSED"


TERMINAL_ACTION_STATES: Final = frozenset(
    {
        ActionState.SUCCEEDED,
        ActionState.FAILED,
        ActionState.PARTIAL_FAILURE,
        ActionState.CANCELLED,
        ActionState.EXPIRED,
        ActionState.UNSUPPORTED,
        ActionState.REFUSED,
    }
)


class ApprovalState(StrEnum):
    NOT_REQUIRED = "NOT_REQUIRED"
    PENDING = "PENDING"
    GRANTED = "GRANTED"
    EXPIRED = "EXPIRED"
    INVALIDATED = "INVALIDATED"


class ExecutionState(StrEnum):
    NOT_DISPATCHED = "NOT_DISPATCHED"
    DISPATCHED = "DISPATCHED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"
    TIMED_OUT = "TIMED_OUT"
    UNSUPPORTED = "UNSUPPORTED"


class ResultState(StrEnum):
    PENDING = "PENDING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    PARTIAL_FAILURE = "PARTIAL_FAILURE"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    UNSUPPORTED = "UNSUPPORTED"


class ReviewState(StrEnum):
    NOT_REVIEWED = "NOT_REVIEWED"
    REVIEWED = "REVIEWED"


class FailureClassification(StrEnum):
    NONE = "NONE"
    PROVIDER_FAILURE = "PROVIDER_FAILURE"
    PARTIAL_PROVIDER_FAILURE = "PARTIAL_PROVIDER_FAILURE"
    TIMEOUT = "TIMEOUT"
    UNSUPPORTED_CAPABILITY = "UNSUPPORTED_CAPABILITY"
    AUTHORIZATION_REFUSED = "AUTHORIZATION_REFUSED"
    PRECONDITION_FAILED = "PRECONDITION_FAILED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    ADAPTER_UNAVAILABLE = "ADAPTER_UNAVAILABLE"


class SessionState(StrEnum):
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"


class MaintenanceWindowState(StrEnum):
    REQUESTED = "REQUESTED"
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    CLOSED = "CLOSED"


class BackupOperationState(StrEnum):
    REQUESTED = "REQUESTED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    UNSUPPORTED = "UNSUPPORTED"


class OpsRefusal(StrEnum):
    """Stable reason codes. Every refusal is evidence-bearing."""

    NO_SESSION = "OPS_NO_SESSION"
    SESSION_REVOKED = "OPS_SESSION_REVOKED"
    SESSION_EXPIRED = "OPS_SESSION_EXPIRED"
    SESSION_PRINCIPAL_MISMATCH = "OPS_SESSION_PRINCIPAL_MISMATCH"
    READ_ONLY_SESSION = "OPS_READ_ONLY_SESSION"
    PROJECTION_UNTRUSTED = "OPS_AUTHORITY_PROJECTION_UNTRUSTED"
    PROJECTION_EXPIRED = "OPS_AUTHORITY_PROJECTION_EXPIRED"
    PROJECTION_MISMATCH = "OPS_AUTHORITY_PROJECTION_MISMATCH"
    NO_AUTHORITY = "OPS_NO_AUTHORITY"
    WRONG_SCOPE = "OPS_WRONG_SCOPE"
    ENVIRONMENT_MISMATCH = "OPS_ENVIRONMENT_MISMATCH"
    STALE_AUTHORITY = "OPS_STALE_AUTHORITY"
    STALE_APPROVAL = "OPS_STALE_APPROVAL"
    STALE_TARGET = "OPS_STALE_TARGET"
    STALE_DEPLOYMENT_IDENTITY = "OPS_STALE_DEPLOYMENT_IDENTITY"
    STALE_PARAMETERS = "OPS_STALE_PARAMETERS"
    STALE_POLICY = "OPS_STALE_POLICY"
    STALE_CTRL02 = "OPS_STALE_CTRL02_STATE"
    STALE_CTRL03_TRUST = "OPS_STALE_CTRL03_TRUST"
    CTRL02_RESTRICTED = "OPS_CTRL02_RESTRICTED"
    CTRL03_ARTIFACT_UNVERIFIED = "OPS_CTRL03_ARTIFACT_UNVERIFIED"
    SELF_APPROVAL = "OPS_SELF_APPROVAL_FORBIDDEN"
    APPROVER_EXECUTES = "OPS_APPROVER_MAY_NOT_EXECUTE"
    REQUESTER_EXECUTES = "OPS_REQUESTER_MAY_NOT_EXECUTE_HIGH_IMPACT"
    EXECUTOR_REVIEWS = "OPS_EXECUTOR_MAY_NOT_REVIEW"
    QUORUM_NOT_MET = "OPS_QUORUM_NOT_MET"
    APPROVER_CLASS_MISSING = "OPS_APPROVER_CLASS_MISSING"
    APPROVAL_NOT_REQUIRED = "OPS_APPROVAL_NOT_REQUIRED"
    APPROVAL_EXPIRED = "OPS_APPROVAL_EXPIRED"
    DUPLICATE_APPROVAL = "OPS_DUPLICATE_APPROVAL"
    REQUEST_EXPIRED = "OPS_REQUEST_EXPIRED"
    WRONG_STATE = "OPS_WRONG_STATE"
    IDEMPOTENCY_CONFLICT = "OPS_IDEMPOTENCY_CONFLICT"
    DUPLICATE_EXECUTION = "OPS_DUPLICATE_EXECUTION"
    CONFLICTING_EXECUTION = "OPS_CONFLICTING_EXECUTION"
    REPLAYED_REQUEST = "OPS_REPLAYED_REQUEST"
    VOTING_BOUNDARY = "OPS_VOTING_BOUNDARY"
    UNKNOWN_TARGET = "OPS_UNKNOWN_TARGET"
    COARSE_TARGET = "OPS_COARSE_TARGET_FORBIDDEN"
    UNSUPPORTED_CAPABILITY = "OPS_UNSUPPORTED_CAPABILITY"
    ADAPTER_UNAVAILABLE = "OPS_ADAPTER_UNAVAILABLE"
    ADAPTER_CONTRACT = "OPS_ADAPTER_CONTRACT_VIOLATION"
    UNVERIFIED_ARTIFACT = "OPS_ROLLBACK_ARTIFACT_UNVERIFIED"
    BACKUP_IDENTITY_MISMATCH = "OPS_BACKUP_IDENTITY_MISMATCH"
    CONFIRMATION_MISSING = "OPS_DESTRUCTIVE_CONFIRMATION_MISSING"
    MAINTENANCE_WINDOW_INVALID = "OPS_MAINTENANCE_WINDOW_INVALID"
    MAINTENANCE_WINDOW_EXPIRED = "OPS_MAINTENANCE_WINDOW_EXPIRED"
    MAINTENANCE_REQUIRED = "OPS_MAINTENANCE_WINDOW_REQUIRED"
    PARAMETER_INVALID = "OPS_PARAMETER_INVALID"
    CLOCK_ROLLBACK = "OPS_CLOCK_ROLLBACK"
    EVIDENCE_IMMUTABLE = "OPS_EVIDENCE_IMMUTABLE"
    NOT_FOUND = "OPS_NOT_FOUND"
    UNKNOWN_ACTION = "OPS_UNKNOWN_ACTION"
    SECRET_VISIBILITY = "OPS_SECRET_VISIBILITY_FORBIDDEN"
    UNIVERSAL_ADMIN = "OPS_UNIVERSAL_ADMIN_FORBIDDEN"
    BROWSER_STATE_REJECTED = "OPS_BROWSER_STATE_NOT_AUTHORITATIVE"


# ---------------------------------------------------------------------------
# Policy
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class OperationsPolicy:
    """Enforcement obligations. All default to enforced; only `governed()` is
    permitted inside a candidate. The anti-cheat suite flips them one by one."""

    enforce_session_state: bool = True
    enforce_read_only_sessions: bool = True
    enforce_projection_signature: bool = True
    enforce_projection_freshness: bool = True
    enforce_exact_scope: bool = True
    enforce_environment_match: bool = True
    commit_time_reauthorization: bool = True
    enforce_approval_freshness: bool = True
    enforce_target_version: bool = True
    enforce_deployment_identity: bool = True
    enforce_parameters_digest: bool = True
    reject_self_approval: bool = True
    separate_approval_from_execution: bool = True
    separate_execution_from_review: bool = True
    enforce_quorum: bool = True
    enforce_idempotency: bool = True
    enforce_concurrency_guard: bool = True
    enforce_ctrl02_state: bool = True
    enforce_ctrl03_trust: bool = True
    enforce_voting_boundary: bool = True
    enforce_unsupported_explicit: bool = True
    dispatch_is_not_success: bool = True
    enforce_destructive_confirmation: bool = True
    enforce_maintenance_window: bool = True
    enforce_request_expiry: bool = True
    enforce_secret_redaction: bool = True
    enforce_evidence_on_refusal: bool = True
    enforce_evidence_immutability: bool = True

    @classmethod
    def governed(cls) -> OperationsPolicy:
        return cls()

    def is_governed(self) -> bool:
        return all(getattr(self, item.name) is True for item in fields(self))

    def disabled_obligations(self) -> tuple[str, ...]:
        return tuple(item.name for item in fields(self) if getattr(self, item.name) is not True)

    def without(self, obligation: str) -> OperationsPolicy:
        if obligation not in {item.name for item in fields(self)}:
            raise KeyError(obligation)
        return replace(self, **{obligation: False})


# ---------------------------------------------------------------------------
# Typed records
# ---------------------------------------------------------------------------


_SAFE_SEGMENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_HEX_DIGEST = re.compile(r"^[0-9a-f]{64}$")


def _require_id(value: str, label: str) -> str:
    if not value or len(value) > 128 or value in COARSE_TARGETS or any(c.isspace() for c in value):
        raise ValueError(f"{label} must be an exact, non-coarse identifier")
    return value


def parameters_digest(parameters: Mapping[str, str]) -> str:
    return hashlib.sha256(canonical_dumps(dict(sorted(parameters.items()))).encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class DeploymentIdentity:
    deployment_id: str
    artifact_digest: str
    artifact_ref: str
    release_ref: str
    change_ref: str
    version: int
    verified: bool

    def __post_init__(self) -> None:
        _require_id(self.deployment_id, "deployment_id")
        if len(self.artifact_digest) != 64:
            raise ValueError("artifact_digest must be a sha256 hex digest")


@dataclass(frozen=True, slots=True)
class OperationalTarget:
    target_id: str
    target_class: TargetClass
    domain: TargetDomain
    environment: EnvironmentClass
    scope: ExactScope
    deployment_identity_ref: str
    adapter_id: str
    version: int
    capabilities: frozenset[AdapterCapability] = frozenset()
    display_name: str = ""

    def __post_init__(self) -> None:
        _require_id(self.target_id, "target_id")
        _require_id(self.adapter_id, "adapter_id")


@dataclass(frozen=True, slots=True)
class HealthSnapshot:
    target_id: str
    state: HealthState
    observed_at: datetime
    deployment_identity_ref: str
    details: Mapping[str, str] = field(default_factory=dict)
    redacted_fields: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class JobQueueSnapshot:
    queue_id: str
    target_id: str
    state: str
    depth: int
    oldest_age_seconds: int
    observed_at: datetime


@dataclass(frozen=True, slots=True)
class BackupRestoreOperationRef:
    operation_id: str
    kind: str
    target_id: str
    backup_set_id: str
    backup_identity_digest: str
    state: BackupOperationState
    action_id: str
    requested_at: datetime
    backend_operation_ref: str | None = None
    completed_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class MaintenanceWindowRef:
    window_id: str
    target_id: str
    state: MaintenanceWindowState
    starts_at: datetime
    ends_at: datetime
    reason: str
    action_id: str
    closed_by_action_id: str | None = None

    def is_active_at(self, moment: datetime) -> bool:
        return (
            self.state is MaintenanceWindowState.ACTIVE and self.starts_at <= moment < self.ends_at
        )


@dataclass(frozen=True, slots=True)
class OperationalIncidentRef:
    incident_id: str
    target_id: str
    severity: str
    state: str
    linked_action_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ConsoleSession:
    session_id: str
    principal_id: str
    state: SessionState
    established_at: datetime
    expires_at: datetime
    read_only: bool
    assurance_level: str = "AAL2"

    def usable_at(self, moment: datetime) -> tuple[bool, OpsRefusal | None]:
        if self.state is SessionState.REVOKED:
            return False, OpsRefusal.SESSION_REVOKED
        if self.state is SessionState.EXPIRED or moment >= self.expires_at:
            return False, OpsRefusal.SESSION_EXPIRED
        return True, None


@dataclass(frozen=True, slots=True)
class AuthorityProjection:
    """A short-lived signed projection of the authoritative CTRL-02 grant.

    The console verifies signature and freshness and then still re-resolves
    against the live directory at commit. A projection supplied by a browser
    without a valid signature authorizes nothing.
    """

    principal_id: str
    grant_id: str
    capability: str
    scope_key: str
    version: int
    approver_class: str | None
    issued_at: datetime
    expires_at: datetime
    signature: str

    def payload(self) -> dict[str, Any]:
        return {
            "principal_id": self.principal_id,
            "grant_id": self.grant_id,
            "capability": self.capability,
            "scope_key": self.scope_key,
            "version": self.version,
            "approver_class": self.approver_class,
            "issued_at": self.issued_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
        }


class EvidenceSealer:
    """Keyed anchor for persisted evidence.

    The journal chain is an unkeyed hash chain; a tamperer who can rewrite the
    checkpoint file can recompute the chain and its in-file anchor. The sealer
    keys the anchor with material that never enters the checkpoint, so a
    rewritten history cannot produce a valid seal.
    """

    def __init__(self, key: bytes) -> None:
        if len(key) < 16:
            raise ValueError("evidence key too short")
        self._key = key

    def seal(self, count: int, head: str) -> str:
        return hmac.new(self._key, f"{count}:{head}".encode(), "sha256").hexdigest()

    def verify(self, count: int, head: str, seal: str) -> bool:
        return hmac.compare_digest(self.seal(count, head), seal)


class AuthorityProjectionSigner:
    """Issues and verifies projections with a keyed digest held by the
    authority source side. The key never enters evidence or read models."""

    def __init__(self, key: bytes) -> None:
        if len(key) < 16:
            raise ValueError("projection key too short")
        self._key = key

    def _mac(self, payload: Mapping[str, Any]) -> str:
        return hmac.new(self._key, canonical_dumps(dict(payload)).encode(), "sha256").hexdigest()

    def issue(self, grant: AuthorityGrant, *, now: datetime) -> AuthorityProjection:
        unsigned = AuthorityProjection(
            principal_id=grant.actor_id,
            grant_id=grant.grant_id,
            capability=grant.capability,
            scope_key=grant.scope.key,
            version=grant.version,
            approver_class=None if grant.approver_class is None else grant.approver_class.value,
            issued_at=now,
            expires_at=now + MAX_PROJECTION_LIFETIME,
            signature="",
        )
        return replace(unsigned, signature=self._mac(unsigned.payload()))

    def verify(self, projection: AuthorityProjection) -> bool:
        return hmac.compare_digest(self._mac(projection.payload()), projection.signature)


@dataclass(frozen=True, slots=True)
class AuthorizationDecision:
    allowed: bool
    reason_code: str
    stage: str
    actor_ref: str
    authority_ref: str | None
    authority_version: int | None
    policy_version: str
    detail: str = ""


@dataclass(frozen=True, slots=True)
class OperationalApproval:
    approval_id: str
    action_id: str
    approver_ref: str
    approver_class: str
    authority_ref: str
    authority_version: int
    approved_at: datetime
    expires_at: datetime
    bound_parameters_digest: str
    bound_target_version: int
    bound_deployment_identity_ref: str
    state: ApprovalState
    session_id: str = ""


@dataclass(frozen=True, slots=True)
class OperationalExecution:
    execution_id: str
    action_id: str
    executor_ref: str
    executor_authority_ref: str
    adapter_id: str
    dispatched_at: datetime
    deadline: datetime
    state: ExecutionState
    backend_operation_ref: str | None = None
    last_observed_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class OperationalResult:
    result_id: str
    action_id: str
    execution_id: str | None
    state: ResultState
    failure_classification: FailureClassification
    detail: str
    completed_at: datetime
    backend_metadata: Mapping[str, str] = field(default_factory=dict)
    redacted_fields: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class OperationalEvidenceRef:
    evidence_id: str
    action_id: str
    journal_sequence: int
    event_hash: str
    evidence_digest: str


@dataclass(frozen=True, slots=True)
class OperationalActionRequest:
    action_id: str
    request_id: str
    idempotency_key: str
    action_type: ActionType
    impact: ImpactClass
    actor_ref: str
    session_id: str
    authority_ref: str
    authority_version: int
    target_id: str
    target_version: int
    deployment_identity_ref: str
    environment: EnvironmentClass
    scope_key: str
    parameters: Mapping[str, str]
    parameters_digest: str
    policy_version: str
    ctrl02_revision: int
    ctrl03_trust_revision: int
    requested_at: datetime
    expires_at: datetime
    state: ActionState
    approval_state: ApprovalState
    required_approver_classes: tuple[str, ...]
    execution_state: ExecutionState = ExecutionState.NOT_DISPATCHED
    result_state: ResultState = ResultState.PENDING
    review_state: ReviewState = ReviewState.NOT_REVIEWED
    approval_ids: tuple[str, ...] = ()
    execution_id: str | None = None
    result_id: str | None = None
    incident_ref: str | None = None
    maintenance_window_ref: str | None = None
    backend_operation_ref: str | None = None
    refusal_reason: str | None = None
    reviewed_by: str | None = None
    purpose: str = ""


# ---------------------------------------------------------------------------
# Action catalogue
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class OperationalActionSpec:
    action_type: ActionType
    impact: ImpactClass
    mutation: bool
    capability: AdapterCapability | None
    required_right: str
    target_classes: frozenset[TargetClass]
    approver_classes_production: tuple[str, ...]
    approver_classes_non_production: tuple[str, ...]
    requester_may_execute: bool
    destructive_confirmation: bool
    requires_maintenance_window: bool
    allowed_parameters: frozenset[str]
    route: str
    description: str

    def approver_classes(self, environment: EnvironmentClass) -> tuple[str, ...]:
        if environment is EnvironmentClass.PRODUCTION_LIKE:
            return self.approver_classes_production
        return self.approver_classes_non_production


def _read(
    action: ActionType, classes: frozenset[TargetClass], route: str, text: str
) -> tuple[ActionType, OperationalActionSpec]:
    return action, OperationalActionSpec(
        action_type=action,
        impact=ImpactClass.READ,
        mutation=False,
        capability=None,
        required_right="OPS.READ",
        target_classes=classes,
        approver_classes_production=(),
        approver_classes_non_production=(),
        requester_may_execute=True,
        destructive_confirmation=False,
        requires_maintenance_window=False,
        allowed_parameters=frozenset(),
        route=route,
        description=text,
    )


_ALL_CLASSES = frozenset(TargetClass)
_IC = ApproverClass.INCIDENT_COMMANDER.value
_SEC = ApproverClass.SECURITY.value
_TRUST = ApproverClass.TRUST_CUSTODIAN.value

ACTION_CATALOGUE: Final[dict[ActionType, OperationalActionSpec]] = dict(
    [
        _read(ActionType.STATUS_READ, _ALL_CLASSES, "/ops/v1/status", "deployment/runtime status"),
        _read(ActionType.HEALTH_READ, _ALL_CLASSES, "/ops/v1/health", "service/environment health"),
        _read(
            ActionType.JOBS_READ, frozenset({TargetClass.JOB_QUEUE}), "/ops/v1/jobs", "jobs/queues"
        ),
        _read(
            ActionType.INTEGRATION_READ,
            frozenset({TargetClass.INTEGRATION}),
            "/ops/v1/integrations",
            "integration status",
        ),
        _read(
            ActionType.DEPLOYMENT_IDENTITY_READ,
            _ALL_CLASSES,
            "/ops/v1/deployment-identity",
            "artifact/deployment identity and change/release references",
        ),
        _read(
            ActionType.RECOVERY_READINESS_READ,
            _ALL_CLASSES,
            "/ops/v1/recovery-readiness",
            "recovery readiness",
        ),
        _read(
            ActionType.BACKUP_STATUS_READ,
            frozenset({TargetClass.DATASTORE, TargetClass.BACKUP_SET}),
            "/ops/v1/backups",
            "backup/restore operation status",
        ),
        _read(ActionType.INCIDENT_READ, _ALL_CLASSES, "/ops/v1/incidents", "incident linkage"),
        _read(ActionType.ACTION_HISTORY_READ, _ALL_CLASSES, "/ops/v1/actions", "action history"),
        _read(
            ActionType.EVIDENCE_LOOKUP, _ALL_CLASSES, "/ops/v1/evidence", "evidence by action id"
        ),
        (
            ActionType.SERVICE_RESTART,
            OperationalActionSpec(
                ActionType.SERVICE_RESTART,
                ImpactClass.MEDIUM,
                True,
                AdapterCapability.RESTART,
                "OPS.REQUEST",
                frozenset({TargetClass.SERVICE}),
                (_IC,),
                (),
                True,
                False,
                False,
                frozenset({"reason", "drain_seconds"}),
                "/ops/v1/actions#OPS.SERVICE.RESTART",
                "controlled restart of one exact service target",
            ),
        ),
        (
            ActionType.DEPLOYMENT_ROLLBACK,
            OperationalActionSpec(
                ActionType.DEPLOYMENT_ROLLBACK,
                ImpactClass.HIGH,
                True,
                AdapterCapability.ROLLBACK,
                "OPS.REQUEST",
                frozenset({TargetClass.SERVICE, TargetClass.ENVIRONMENT}),
                (_IC, _SEC),
                (_IC,),
                False,
                False,
                False,
                frozenset({"reason", "target_artifact_digest"}),
                "/ops/v1/actions#OPS.DEPLOYMENT.ROLLBACK",
                "rollback to a verified, allowed artifact identity",
            ),
        ),
        (
            ActionType.MAINTENANCE_ENTER,
            OperationalActionSpec(
                ActionType.MAINTENANCE_ENTER,
                ImpactClass.MEDIUM,
                True,
                AdapterCapability.MAINTENANCE,
                "OPS.REQUEST",
                frozenset({TargetClass.SERVICE, TargetClass.ENVIRONMENT, TargetClass.DATASTORE}),
                (_IC,),
                (),
                True,
                False,
                False,
                frozenset({"reason", "duration_minutes"}),
                "/ops/v1/actions#OPS.MAINTENANCE.ENTER",
                "bounded maintenance window activation",
            ),
        ),
        (
            ActionType.MAINTENANCE_EXIT,
            OperationalActionSpec(
                ActionType.MAINTENANCE_EXIT,
                ImpactClass.LOW,
                True,
                AdapterCapability.MAINTENANCE,
                "OPS.REQUEST",
                frozenset({TargetClass.SERVICE, TargetClass.ENVIRONMENT, TargetClass.DATASTORE}),
                (),
                (),
                True,
                False,
                False,
                frozenset({"reason", "window_id"}),
                "/ops/v1/actions#OPS.MAINTENANCE.EXIT",
                "close an active maintenance window",
            ),
        ),
        (
            ActionType.JOB_QUEUE_PAUSE,
            OperationalActionSpec(
                ActionType.JOB_QUEUE_PAUSE,
                ImpactClass.MEDIUM,
                True,
                AdapterCapability.QUEUE_CONTROL,
                "OPS.REQUEST",
                frozenset({TargetClass.JOB_QUEUE}),
                (_IC,),
                (),
                True,
                False,
                False,
                frozenset({"reason"}),
                "/ops/v1/actions#OPS.JOB_QUEUE.PAUSE",
                "pause one exact job queue",
            ),
        ),
        (
            ActionType.JOB_QUEUE_RESUME,
            OperationalActionSpec(
                ActionType.JOB_QUEUE_RESUME,
                ImpactClass.LOW,
                True,
                AdapterCapability.QUEUE_CONTROL,
                "OPS.REQUEST",
                frozenset({TargetClass.JOB_QUEUE}),
                (),
                (),
                True,
                False,
                False,
                frozenset({"reason"}),
                "/ops/v1/actions#OPS.JOB_QUEUE.RESUME",
                "resume one exact job queue",
            ),
        ),
        (
            ActionType.BACKUP_REQUEST,
            OperationalActionSpec(
                ActionType.BACKUP_REQUEST,
                ImpactClass.MEDIUM,
                True,
                AdapterCapability.BACKUP,
                "OPS.REQUEST",
                frozenset({TargetClass.DATASTORE}),
                (_IC,),
                (),
                True,
                False,
                False,
                frozenset({"reason", "backup_set_id"}),
                "/ops/v1/actions#OPS.BACKUP.REQUEST",
                "request a backup operation from the owning backup engine",
            ),
        ),
        (
            ActionType.RESTORE_REQUEST,
            OperationalActionSpec(
                ActionType.RESTORE_REQUEST,
                ImpactClass.DESTRUCTIVE,
                True,
                AdapterCapability.RESTORE,
                "OPS.REQUEST",
                frozenset({TargetClass.DATASTORE}),
                (_IC, _SEC, _TRUST),
                (_IC, _TRUST),
                False,
                True,
                True,
                frozenset({"reason", "backup_set_id", "backup_identity_digest", "confirmation"}),
                "/ops/v1/actions#OPS.RESTORE.REQUEST",
                "restore/recovery request guarded by dual control, confirmation and identity",
            ),
        ),
        (
            ActionType.INCIDENT_LINK,
            OperationalActionSpec(
                ActionType.INCIDENT_LINK,
                ImpactClass.LOW,
                True,
                None,
                "OPS.REQUEST",
                _ALL_CLASSES,
                (),
                (),
                True,
                False,
                False,
                frozenset({"incident_id", "linked_action_id"}),
                "/ops/v1/actions#OPS.INCIDENT.LINK",
                "link an action to an operational incident record",
            ),
        ),
    ]
)

CTRL04_ACTIONS: Final = tuple(
    {
        "action_id": spec.action_type.value,
        "impact": spec.impact.value,
        "mutation": spec.mutation,
        "required_right": spec.required_right,
        "approval_production": list(spec.approver_classes_production),
        "approval_non_production": list(spec.approver_classes_non_production),
        "requester_may_execute": spec.requester_may_execute,
        "destructive_confirmation": spec.destructive_confirmation,
        "requires_maintenance_window": spec.requires_maintenance_window,
        "adapter_capability": None if spec.capability is None else spec.capability.value,
        "route": spec.route,
        "console_id": GENERAL_CONSOLE_ID,
        "desk_id": GENERAL_DESK_ID,
        "commit_time_reauthorization": spec.mutation,
        "immutable_evidence": True,
    }
    for spec in ACTION_CATALOGUE.values()
)


# ---------------------------------------------------------------------------
# CTRL-03 trust adapter
# ---------------------------------------------------------------------------


class Ctrl03TrustState:
    """Explicit adapter for the CTRL-03 artifact trust set.

    Rollback may only target an artifact identity the trust set attests as
    verified. The revision is re-checked at commit so that a trust retraction
    between request and execution fails closed.
    """

    def __init__(self) -> None:
        self.available = True
        self.revision = 1
        self.verified_artifacts: set[str] = set()

    def attest(self, artifact_digest: str) -> None:
        self.verified_artifacts.add(artifact_digest)
        self.revision += 1

    def retract(self, artifact_digest: str) -> None:
        self.verified_artifacts.discard(artifact_digest)
        self.revision += 1

    def require(self, expected_revision: int | None) -> None:
        if not self.available:
            raise AuthorizationRefused(
                "CTRL-03 trust state unavailable", reason_code=OpsRefusal.ADAPTER_UNAVAILABLE
            )
        if expected_revision is not None and self.revision != expected_revision:
            raise AuthorizationRefused(
                "CTRL-03 trust set changed", reason_code=OpsRefusal.STALE_CTRL03_TRUST
            )

    def is_verified(self, artifact_digest: str) -> bool:
        return artifact_digest in self.verified_artifacts


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


def _iso(value: datetime | None) -> str | None:
    return None if value is None else value.isoformat()


def _dt(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    parsed = datetime.fromisoformat(str(value))
    if parsed.tzinfo is None:
        raise ValueError("timestamps must be timezone-aware")
    return parsed


class OperationsConsoleService:
    """The CTRL-04 governed command surface."""

    def __init__(
        self,
        *,
        authorities: AuthorityDirectory,
        signer: AuthorityProjectionSigner,
        adapters: Mapping[str, OperationsAdapter],
        ctrl02: Ctrl02State | None = None,
        ctrl03: Ctrl03TrustState | None = None,
        policy: OperationsPolicy | None = None,
        store: Any | None = None,
        sealer: EvidenceSealer | None = None,
    ) -> None:
        self.authorities = authorities
        self.signer = signer
        self.sealer = sealer
        self.adapters = dict(adapters)
        self.ctrl02 = ctrl02 or Ctrl02State()
        self.ctrl03 = ctrl03 or Ctrl03TrustState()
        self.policy = policy or OperationsPolicy.governed()
        self.journal = EvidenceJournal()
        self._store = store
        self._lock = threading.RLock()
        self._targets: dict[str, OperationalTarget] = {}
        self._deployments: dict[str, DeploymentIdentity] = {}
        self._sessions: dict[str, ConsoleSession] = {}
        self._actions: dict[str, OperationalActionRequest] = {}
        self._approvals: dict[str, OperationalApproval] = {}
        self._executions: dict[str, OperationalExecution] = {}
        self._results: dict[str, OperationalResult] = {}
        self._evidence_refs: dict[str, list[OperationalEvidenceRef]] = {}
        self._decisions: dict[str, list[AuthorizationDecision]] = {}
        self._idempotency: dict[str, str] = {}
        self._executing_targets: dict[str, str] = {}
        self._windows: dict[str, MaintenanceWindowRef] = {}
        self._backups: dict[str, BackupRestoreOperationRef] = {}
        self._incidents: dict[str, OperationalIncidentRef] = {}
        self._counter = 0
        self._last_time = datetime(1970, 1, 1, tzinfo=UTC)

    # -- registration --------------------------------------------------------

    def register_target(self, target: OperationalTarget) -> None:
        with self._lock:
            self._targets[target.target_id] = target
            self._persist()

    def bump_target_version(self, target_id: str) -> OperationalTarget:
        with self._lock:
            current = self._targets[target_id]
            updated = replace(current, version=current.version + 1)
            self._targets[target_id] = updated
            self._persist()
            return updated

    def register_deployment(self, identity: DeploymentIdentity) -> None:
        with self._lock:
            self._deployments[identity.deployment_id] = identity
            self._persist()

    def rebind_deployment(self, target_id: str, deployment_id: str) -> OperationalTarget:
        with self._lock:
            if deployment_id not in self._deployments:
                raise KeyError(deployment_id)
            current = self._targets[target_id]
            updated = replace(
                current, deployment_identity_ref=deployment_id, version=current.version + 1
            )
            self._targets[target_id] = updated
            self._persist()
            return updated

    def register_incident(self, incident: OperationalIncidentRef) -> None:
        with self._lock:
            self._incidents[incident.incident_id] = incident
            self._persist()

    def open_session(self, session: ConsoleSession) -> None:
        with self._lock:
            self._sessions[session.session_id] = session
            self._persist()

    def revoke_session(self, session_id: str) -> None:
        with self._lock:
            current = self._sessions[session_id]
            self._sessions[session_id] = replace(current, state=SessionState.REVOKED)
            self._persist()

    # -- helpers -------------------------------------------------------------

    def _time(self, supplied: datetime) -> datetime:
        if supplied.tzinfo is None:
            raise ValueError("timestamps must be timezone-aware")
        with self._lock:
            return self._advance_clock(supplied)

    def _advance_clock(self, supplied: datetime) -> datetime:
        if supplied < self._last_time:
            raise AuthorizationRefused(
                "clock moved backwards; refusing to act on a rolled-back clock",
                reason_code=OpsRefusal.CLOCK_ROLLBACK,
            )
        self._last_time = supplied
        return supplied

    def _next_id(self, prefix: str) -> str:
        self._counter += 1
        return f"{prefix}-{self._counter:06d}"

    def _persist(self) -> None:
        if self._store is not None:
            self._store.save(self.checkpoint())

    def _record(
        self,
        *,
        now: datetime,
        actor_ref: str,
        authority_basis: str,
        action_type: str,
        scope_key: str,
        object_ref: str,
        result: str,
        reason_code: str,
        action_id: str,
        approval_refs: tuple[str, ...] = (),
        attributes: Mapping[str, Any] | None = None,
    ) -> OperationalEvidenceRef:
        attrs = dict(attributes or {})
        if self.policy.enforce_secret_redaction:
            # Secret-looking keys are dropped from evidence entirely (a redacted
            # key name is still a disclosure); their names are listed instead.
            attrs, redacted = redact_metadata(attrs)
            for key in redacted:
                del attrs[key]
            if redacted:
                attrs["evidence_redacted_fields"] = ",".join(sorted(redacted))
        event = self.journal.append(
            occurred_at=now,
            actor_ref=actor_ref,
            actor_class=ActorClass.HUMAN.value,
            authority_basis=authority_basis,
            action_id=action_type,
            scope_key=scope_key,
            object_ref=object_ref,
            result=result,
            reason_code=reason_code,
            approval_refs=approval_refs,
            correlation_ref=action_id,
            attributes=attrs,
        )
        digest = hashlib.sha256(
            canonical_dumps({"event_hash": event.event_hash, "action_id": action_id}).encode()
        ).hexdigest()
        ref = OperationalEvidenceRef(
            evidence_id=f"EVD-{event.sequence:06d}",
            action_id=action_id,
            journal_sequence=event.sequence,
            event_hash=event.event_hash,
            evidence_digest=digest,
        )
        self._evidence_refs.setdefault(action_id, []).append(ref)
        return ref

    def _refuse(
        self,
        *,
        now: datetime,
        actor_ref: str,
        action_type: str,
        scope_key: str,
        object_ref: str,
        reason: OpsRefusal | str,
        action_id: str,
        detail: str = "",
        authority_basis: str = "NONE",
    ) -> AuthorizationRefused:
        code = reason.value if isinstance(reason, OpsRefusal) else reason
        if self.policy.enforce_evidence_on_refusal:
            self._record(
                now=now,
                actor_ref=actor_ref,
                authority_basis=authority_basis,
                action_type=action_type,
                scope_key=scope_key,
                object_ref=object_ref,
                result="REFUSED",
                reason_code=code,
                action_id=action_id,
                attributes={"detail": scrub_text(detail)[:200]} if detail else None,
            )
            self._persist()
        return AuthorizationRefused(detail or code, reason_code=code)

    def _target(self, target_id: str) -> OperationalTarget:
        if target_id in COARSE_TARGETS:
            raise AuthorizationRefused(
                "coarse or wildcard target is forbidden", reason_code=OpsRefusal.COARSE_TARGET
            )
        try:
            return self._targets[target_id]
        except KeyError as exc:
            raise AuthorizationRefused(
                f"unknown target {target_id}", reason_code=OpsRefusal.UNKNOWN_TARGET
            ) from exc

    def _session(self, session_id: str, principal_id: str, now: datetime) -> ConsoleSession:
        session = self._sessions.get(session_id)
        if session is None:
            raise AuthorizationRefused("no session", reason_code=OpsRefusal.NO_SESSION)
        if session.principal_id != principal_id:
            raise AuthorizationRefused(
                "session does not belong to actor",
                reason_code=OpsRefusal.SESSION_PRINCIPAL_MISMATCH,
            )
        if self.policy.enforce_session_state:
            usable, why = session.usable_at(now)
            if not usable:
                assert why is not None
                raise AuthorizationRefused(f"session {why.value}", reason_code=why)
        return session

    def _verify_projection(
        self,
        projection: AuthorityProjection,
        *,
        principal_id: str,
        capability: str,
        scope: ExactScope,
        now: datetime,
        approver_class: str | None = None,
    ) -> AuthorityGrant:
        """Verify the presented projection, then resolve the live grant."""
        # A principal holding any wildcard/universal capability is refused every
        # act: no universal admin may exist, and if the authority source ever
        # carries one, the console fails closed rather than honouring it.
        universal = [
            g
            for g in self.authorities._grants.values()
            if g.actor_id == principal_id
            and ("*" in g.capability or g.capability.upper() in {"ADMIN", "SUPER_ADMIN", "ROOT"})
        ]
        if universal or "*" in capability or "*" in projection.capability:
            raise AuthorizationRefused(
                "universal or wildcard authority is forbidden in the operations console",
                reason_code=OpsRefusal.UNIVERSAL_ADMIN,
            )
        if self.policy.enforce_projection_signature and not self.signer.verify(projection):
            raise AuthorizationRefused(
                "authority projection is unsigned or untrusted",
                reason_code=OpsRefusal.PROJECTION_UNTRUSTED,
            )
        if self.policy.enforce_projection_freshness and now >= projection.expires_at:
            raise AuthorizationRefused(
                "authority projection expired", reason_code=OpsRefusal.PROJECTION_EXPIRED
            )
        if (
            projection.principal_id != principal_id
            or projection.capability != capability
            or (approver_class is not None and projection.approver_class != approver_class)
        ):
            raise AuthorizationRefused(
                "projection does not match the requested act",
                reason_code=OpsRefusal.PROJECTION_MISMATCH,
            )
        if self.policy.enforce_exact_scope and projection.scope_key != scope.key:
            raise AuthorizationRefused(
                "authority scope does not match target scope; hierarchy grants nothing",
                reason_code=OpsRefusal.WRONG_SCOPE,
            )
        try:
            grant = self.authorities.require(
                actor_id=principal_id,
                capability=capability,
                scope=scope
                if self.policy.enforce_exact_scope
                else self._any_scope(principal_id, capability, scope),
                now=now,
                approver_class=None if approver_class is None else ApproverClass(approver_class),
            )
        except AuthorizationRefused as exc:
            raise AuthorizationRefused(
                f"no live authority: {exc}", reason_code=f"OPS_{exc.reason_code}"
            ) from exc
        if grant.grant_id != projection.grant_id or grant.version != projection.version:
            raise AuthorizationRefused(
                "projection is stale against the live authority source",
                reason_code=OpsRefusal.STALE_AUTHORITY,
            )
        return grant

    def _any_scope(self, principal_id: str, capability: str, fallback: ExactScope) -> ExactScope:
        # Only reachable with exact-scope enforcement disabled (mutation path).
        for grant in self.authorities._grants.values():
            if grant.actor_id == principal_id and grant.capability == capability:
                return grant.scope
        return fallback

    def _decide(
        self,
        *,
        stage: str,
        actor_ref: str,
        grant: AuthorityGrant | None,
        allowed: bool,
        reason: str,
        action_id: str,
        detail: str = "",
    ) -> AuthorizationDecision:
        decision = AuthorizationDecision(
            allowed=allowed,
            reason_code=reason,
            stage=stage,
            actor_ref=actor_ref,
            authority_ref=None if grant is None else grant.grant_id,
            authority_version=None if grant is None else grant.version,
            policy_version=POLICY_VERSION,
            detail=detail,
        )
        self._decisions.setdefault(action_id, []).append(decision)
        return decision

    def _check_ctrl02(self, target_id: str, session_id: str, expected: int | None) -> None:
        if not self.policy.enforce_ctrl02_state:
            return
        try:
            self.ctrl02.require(target_id, self.ctrl02.revision if expected is None else expected)
            self.ctrl02.require(session_id, self.ctrl02.revision if expected is None else expected)
        except AuthorizationRefused as exc:
            code = {
                "STALE_CTRL02_STATE": OpsRefusal.STALE_CTRL02.value,
                "CTRL02_RESTRICTED": OpsRefusal.CTRL02_RESTRICTED.value,
                "CTRL02_QUARANTINED": OpsRefusal.CTRL02_RESTRICTED.value,
                "DEPENDENCY_UNAVAILABLE": OpsRefusal.ADAPTER_UNAVAILABLE.value,
            }.get(str(exc.reason_code), OpsRefusal.CTRL02_RESTRICTED.value)
            raise AuthorizationRefused(str(exc), reason_code=code) from exc

    def _voting_guard(self, target: OperationalTarget) -> None:
        if self.policy.enforce_voting_boundary and target.domain is TargetDomain.VOTING:
            raise AuthorizationRefused(
                "voting-domain targets are outside the general operations console",
                reason_code=OpsRefusal.VOTING_BOUNDARY,
            )

    def _validate_parameters(
        self, spec: OperationalActionSpec, parameters: Mapping[str, str]
    ) -> dict[str, str]:
        clean: dict[str, str] = {}
        for key, value in parameters.items():
            if key not in spec.allowed_parameters:
                raise AuthorizationRefused(
                    f"parameter {key!r} is not governed for {spec.action_type.value}",
                    reason_code=OpsRefusal.PARAMETER_INVALID,
                )
            if not isinstance(value, str) or len(value) > 512:
                raise AuthorizationRefused(
                    f"parameter {key!r} must be a bounded string",
                    reason_code=OpsRefusal.PARAMETER_INVALID,
                )
            clean[key] = value
        if spec.action_type is ActionType.MAINTENANCE_ENTER:
            try:
                minutes = int(clean.get("duration_minutes", "0") or "0")
            except ValueError as exc:
                raise AuthorizationRefused(
                    "duration_minutes must be an integer", reason_code=OpsRefusal.PARAMETER_INVALID
                ) from exc
            if minutes <= 0 or timedelta(minutes=minutes) > MAX_MAINTENANCE_WINDOW:
                raise AuthorizationRefused(
                    "maintenance window must be positive and bounded",
                    reason_code=OpsRefusal.MAINTENANCE_WINDOW_INVALID,
                )
        for key in ("backup_set_id", "window_id", "incident_id", "linked_action_id"):
            if key in clean and not _SAFE_SEGMENT.match(clean[key]):
                raise AuthorizationRefused(
                    f"parameter {key!r} must be a single safe identifier",
                    reason_code=OpsRefusal.PARAMETER_INVALID,
                )
        for key in ("target_artifact_digest", "backup_identity_digest"):
            if key in clean and not _HEX_DIGEST.match(clean[key]):
                raise AuthorizationRefused(
                    f"parameter {key!r} must be a sha256 hex digest",
                    reason_code=OpsRefusal.PARAMETER_INVALID,
                )
        if spec.action_type is ActionType.DEPLOYMENT_ROLLBACK and not clean.get(
            "target_artifact_digest"
        ):
            raise AuthorizationRefused(
                "rollback requires an exact target artifact digest",
                reason_code=OpsRefusal.PARAMETER_INVALID,
            )
        if spec.action_type is ActionType.RESTORE_REQUEST:
            for key in ("backup_set_id", "backup_identity_digest"):
                if not clean.get(key):
                    raise AuthorizationRefused(
                        f"restore requires {key}", reason_code=OpsRefusal.PARAMETER_INVALID
                    )
        return clean

    # -- read surface ---------------------------------------------------------

    def authorize_read(
        self,
        *,
        actor_ref: str,
        session_id: str,
        projection: AuthorityProjection,
        action_type: ActionType,
        target_id: str,
        now: datetime,
    ) -> tuple[OperationalTarget, AuthorityGrant]:
        moment = self._time(now)
        spec = ACTION_CATALOGUE[action_type]
        if spec.mutation:
            raise AuthorizationRefused("not a read action", reason_code=OpsRefusal.UNKNOWN_ACTION)
        with self._lock:
            target = self._target(target_id)
            self._voting_guard(target)
            self._session(session_id, actor_ref, moment)
            grant = self._verify_projection(
                projection,
                principal_id=actor_ref,
                capability=spec.required_right,
                scope=target.scope,
                now=moment,
            )
            return target, grant

    def health(self, target_id: str, *, now: datetime) -> HealthSnapshot:
        target = self._target(target_id)
        self._voting_guard(target)
        adapter = self.adapters.get(target.adapter_id)
        if adapter is None or not adapter.available:
            return HealthSnapshot(
                target_id, HealthState.UNAVAILABLE, now, target.deployment_identity_ref, {}, ()
            )
        raw = adapter.health(target.target_id)
        details, redacted = redact_metadata(dict(raw.metadata))
        if not self.policy.enforce_secret_redaction:
            details, redacted = dict(raw.metadata), []
        state = (
            HealthState(raw.state) if raw.state in HealthState.__members__ else HealthState.UNKNOWN
        )
        return HealthSnapshot(
            target_id, state, now, target.deployment_identity_ref, details, tuple(redacted)
        )

    def job_queue(self, target_id: str, *, now: datetime) -> JobQueueSnapshot:
        target = self._target(target_id)
        self._voting_guard(target)
        adapter = self.adapters.get(target.adapter_id)
        if adapter is None or not adapter.available:
            return JobQueueSnapshot(target_id, target_id, "UNAVAILABLE", -1, -1, now)
        raw = adapter.queue_state(target_id)
        return JobQueueSnapshot(
            queue_id=target_id,
            target_id=target_id,
            state=str(raw.get("state", "UNKNOWN")),
            depth=int(raw.get("depth", -1)),
            oldest_age_seconds=int(raw.get("oldest_age_seconds", -1)),
            observed_at=now,
        )

    def deployment_identity(self, target_id: str) -> DeploymentIdentity | None:
        target = self._target(target_id)
        self._voting_guard(target)
        return self._deployments.get(target.deployment_identity_ref)

    def recovery_readiness(self, target_id: str, *, now: datetime) -> dict[str, Any]:
        target = self._target(target_id)
        self._voting_guard(target)
        adapter = self.adapters.get(target.adapter_id)
        backups = [b for b in self._backups.values() if b.target_id == target_id]
        completed = [b for b in backups if b.state is BackupOperationState.COMPLETED]
        restore_supported = bool(
            adapter is not None
            and adapter.available
            and AdapterCapability.RESTORE in adapter.capabilities(target_id)
        )
        return {
            "target_id": target_id,
            "as_of": now.isoformat(),
            "backup_supported": bool(
                adapter is not None
                and adapter.available
                and AdapterCapability.BACKUP in adapter.capabilities(target_id)
            ),
            "restore_supported": restore_supported,
            "completed_backups": len(completed),
            "latest_backup_identity": completed[-1].backup_identity_digest if completed else None,
            "readiness": "READY" if completed and restore_supported else "NOT_READY",
        }

    def targets(self) -> tuple[OperationalTarget, ...]:
        return tuple(
            t
            for t in sorted(self._targets.values(), key=lambda x: x.target_id)
            if not (self.policy.enforce_voting_boundary and t.domain is TargetDomain.VOTING)
        )

    def target(self, target_id: str) -> OperationalTarget:
        return self._target(target_id)

    def action(self, action_id: str) -> OperationalActionRequest:
        try:
            return self._actions[action_id]
        except KeyError as exc:
            raise AuthorizationRefused(
                f"unknown action {action_id}", reason_code=OpsRefusal.NOT_FOUND
            ) from exc

    def actions(self) -> tuple[OperationalActionRequest, ...]:
        return tuple(self._actions.values())

    def approvals_of(self, action_id: str) -> tuple[OperationalApproval, ...]:
        return tuple(self._approvals[a] for a in self.action(action_id).approval_ids)

    def execution_of(self, action_id: str) -> OperationalExecution | None:
        execution_id = self.action(action_id).execution_id
        return None if execution_id is None else self._executions[execution_id]

    def result_of(self, action_id: str) -> OperationalResult | None:
        result_id = self.action(action_id).result_id
        return None if result_id is None else self._results[result_id]

    def evidence_of(self, action_id: str) -> tuple[OperationalEvidenceRef, ...]:
        return tuple(self._evidence_refs.get(action_id, ()))

    def decisions_of(self, action_id: str) -> tuple[AuthorizationDecision, ...]:
        return tuple(self._decisions.get(action_id, ()))

    def maintenance_windows(self) -> tuple[MaintenanceWindowRef, ...]:
        return tuple(self._windows.values())

    def backup_operations(self) -> tuple[BackupRestoreOperationRef, ...]:
        return tuple(self._backups.values())

    def incidents(self) -> tuple[OperationalIncidentRef, ...]:
        return tuple(self._incidents.values())

    def sessions(self) -> tuple[ConsoleSession, ...]:
        return tuple(self._sessions.values())

    def session(self, session_id: str) -> ConsoleSession | None:
        return self._sessions.get(session_id)

    def evidence_record(self, action_id: str) -> dict[str, Any]:
        """The `epd2.ctrl04.evidence.v1` record for one immutable action id.

        A refused request never becomes a stored action, but its action id is
        still immutable and its refusal is journaled; the lookup therefore
        answers for refused ids too, from the journal alone.
        """
        if action_id not in self._actions and action_id in self._evidence_refs:
            return self._refused_evidence_record(action_id)
        action = self.action(action_id)
        decisions = self.decisions_of(action_id)
        refs = self.evidence_of(action_id)
        approvals = self.approvals_of(action_id)
        digest = hashlib.sha256(canonical_dumps([r.event_hash for r in refs]).encode()).hexdigest()
        record: dict[str, Any] = {
            "schema": "epd2.ctrl04.evidence.v1",
            "action_id": action.action_id,
            "request_id": action.request_id,
            "action_type": action.action_type.value,
            "actor_ref": action.actor_ref,
            "authority_ref": f"{action.authority_ref}@v{action.authority_version}",
            "target_ref": f"{action.target_id}@v{action.target_version}",
            "environment": action.environment.value,
            "region_scope": action.scope_key,
            "parameters_digest": action.parameters_digest,
            "requested_at": action.requested_at.isoformat(),
            "authorization_decision": [asdict(d) for d in decisions],
            "execution_state": action.execution_state.value,
            "result_state": action.result_state.value,
            "deployment_identity_ref": action.deployment_identity_ref,
            "evidence_digest": digest,
            "evidence_refs": [asdict(r) for r in refs],
            "approval_ref": [
                {
                    "approval_id": a.approval_id,
                    "approver_ref": a.approver_ref,
                    "approver_class": a.approver_class,
                    "authority_ref": f"{a.authority_ref}@v{a.authority_version}",
                    "approved_at": a.approved_at.isoformat(),
                    "state": a.state.value,
                }
                for a in approvals
            ],
            "maintenance_window_ref": action.maintenance_window_ref,
            "incident_ref": action.incident_ref,
            "backend_operation_ref": action.backend_operation_ref,
            "failure_classification": None,
            "review_state": action.review_state.value,
        }
        result = self.result_of(action_id)
        if result is not None:
            record["failure_classification"] = result.failure_classification.value
        return record

    def _refused_evidence_record(self, action_id: str) -> dict[str, Any]:
        refs = self.evidence_of(action_id)
        events = {r.journal_sequence: r for r in refs}
        records = [r for r in self.journal.records() if r.sequence in events]
        first = records[0]
        digest = hashlib.sha256(canonical_dumps([r.event_hash for r in refs]).encode()).hexdigest()
        return {
            "schema": "epd2.ctrl04.evidence.v1",
            "action_id": action_id,
            "request_id": None,
            "action_type": first.action_id,
            "actor_ref": first.actor_ref,
            "authority_ref": first.authority_basis,
            "target_ref": first.object_ref,
            "environment": None,
            "region_scope": first.scope_key,
            "parameters_digest": None,
            "requested_at": first.occurred_at.isoformat(),
            "authorization_decision": [asdict(d) for d in self.decisions_of(action_id)],
            "execution_state": ExecutionState.NOT_DISPATCHED.value,
            "result_state": "REFUSED",
            "deployment_identity_ref": None,
            "evidence_digest": digest,
            "evidence_refs": [asdict(r) for r in refs],
            "approval_ref": [],
            "failure_classification": FailureClassification.AUTHORIZATION_REFUSED.value,
            "refusal_reason": first.reason_code,
            "review_state": ReviewState.NOT_REVIEWED.value,
        }

    # -- lifecycle -----------------------------------------------------------

    def request(
        self,
        *,
        actor_ref: str,
        session_id: str,
        projection: AuthorityProjection,
        action_type: ActionType,
        target_id: str,
        parameters: Mapping[str, str],
        idempotency_key: str,
        purpose: str,
        now: datetime,
        incident_ref: str | None = None,
    ) -> OperationalActionRequest:
        moment = self._time(now)
        with self._lock:
            spec = ACTION_CATALOGUE.get(action_type)
            if spec is None or not spec.mutation:
                raise AuthorizationRefused(
                    "unknown or non-mutating action", reason_code=OpsRefusal.UNKNOWN_ACTION
                )
            action_id = self._next_id("OPA")
            scope_key = "UNKNOWN"
            try:
                if not isinstance(idempotency_key, str) or not isinstance(target_id, str):
                    raise AuthorizationRefused(
                        "identifiers must be strings", reason_code=OpsRefusal.PARAMETER_INVALID
                    )
                if incident_ref is not None and not isinstance(incident_ref, str):
                    raise AuthorizationRefused(
                        "incident_ref must be a string", reason_code=OpsRefusal.PARAMETER_INVALID
                    )
                try:
                    _require_id(idempotency_key, "idempotency_key")
                except ValueError as exc:
                    raise AuthorizationRefused(
                        str(exc), reason_code=OpsRefusal.PARAMETER_INVALID
                    ) from exc
                target = self._target(target_id)
                scope_key = target.scope.key
                self._voting_guard(target)
                if target.target_class not in spec.target_classes:
                    raise AuthorizationRefused(
                        f"{action_type.value} is not applicable to {target.target_class.value}",
                        reason_code=OpsRefusal.PARAMETER_INVALID,
                    )
                session = self._session(session_id, actor_ref, moment)
                if self.policy.enforce_read_only_sessions and session.read_only:
                    raise AuthorizationRefused(
                        "read-only session may not request mutations",
                        reason_code=OpsRefusal.READ_ONLY_SESSION,
                    )
                clean = self._validate_parameters(spec, parameters)
                digest = parameters_digest(clean)
                if self.policy.enforce_idempotency:
                    existing_id = self._idempotency.get(f"{actor_ref}:{idempotency_key}")
                    if existing_id is not None:
                        existing = self._actions[existing_id]
                        if (
                            existing.parameters_digest == digest
                            and existing.target_id == target_id
                            and existing.action_type is action_type
                        ):
                            return existing
                        raise AuthorizationRefused(
                            "idempotency key reused with different content",
                            reason_code=OpsRefusal.IDEMPOTENCY_CONFLICT,
                        )
                grant = self._verify_projection(
                    projection,
                    principal_id=actor_ref,
                    capability=spec.required_right,
                    scope=target.scope,
                    now=moment,
                )
                self._check_ctrl02(target_id, session_id, None)
                if spec.destructive_confirmation and self.policy.enforce_destructive_confirmation:
                    expected = f"{DESTRUCTIVE_CONFIRMATION_PREFIX}{target_id}"
                    if clean.get("confirmation") != expected:
                        raise AuthorizationRefused(
                            "destructive operation requires the exact confirmation phrase",
                            reason_code=OpsRefusal.CONFIRMATION_MISSING,
                        )
                if spec.action_type is ActionType.RESTORE_REQUEST:
                    self._require_backup_identity(target, clean)
                if spec.action_type is ActionType.DEPLOYMENT_ROLLBACK:
                    self._require_verified_artifact(clean["target_artifact_digest"], None)
                if spec.action_type is ActionType.INCIDENT_LINK:
                    if clean.get("incident_id") not in self._incidents:
                        raise AuthorizationRefused(
                            "unknown incident", reason_code=OpsRefusal.NOT_FOUND
                        )
                    if clean.get("linked_action_id") not in self._actions:
                        raise AuthorizationRefused(
                            "unknown linked action", reason_code=OpsRefusal.NOT_FOUND
                        )
                if spec.action_type is ActionType.MAINTENANCE_EXIT:
                    window = self._windows.get(clean.get("window_id", ""))
                    if window is None or window.target_id != target_id:
                        raise AuthorizationRefused(
                            "unknown maintenance window for target",
                            reason_code=OpsRefusal.MAINTENANCE_WINDOW_INVALID,
                        )
                if incident_ref is not None and incident_ref not in self._incidents:
                    raise AuthorizationRefused("unknown incident", reason_code=OpsRefusal.NOT_FOUND)
            except (ValueError, TypeError) as exc:
                # A malformed request is a governed refusal with evidence, never
                # an unlogged crash.
                self._decide(
                    stage="REQUEST",
                    actor_ref=actor_ref,
                    grant=None,
                    allowed=False,
                    reason=OpsRefusal.PARAMETER_INVALID.value,
                    action_id=action_id,
                    detail=str(exc),
                )
                raise self._refuse(
                    now=moment,
                    actor_ref=actor_ref,
                    action_type=action_type.value,
                    scope_key=scope_key,
                    object_ref=str(target_id),
                    reason=OpsRefusal.PARAMETER_INVALID,
                    action_id=action_id,
                    detail=f"malformed request: {exc}",
                ) from exc
            except AuthorizationRefused as exc:
                self._decide(
                    stage="REQUEST",
                    actor_ref=actor_ref,
                    grant=None,
                    allowed=False,
                    reason=str(exc.reason_code),
                    action_id=action_id,
                    detail=str(exc),
                )
                raise self._refuse(
                    now=moment,
                    actor_ref=actor_ref,
                    action_type=action_type.value,
                    scope_key=scope_key,
                    object_ref=target_id,
                    reason=str(exc.reason_code),
                    action_id=action_id,
                    detail=str(exc),
                ) from exc

            required = spec.approver_classes(target.environment)
            approval_state = ApprovalState.PENDING if required else ApprovalState.NOT_REQUIRED
            action = OperationalActionRequest(
                action_id=action_id,
                request_id=self._next_id("REQ"),
                idempotency_key=idempotency_key,
                action_type=action_type,
                impact=spec.impact,
                actor_ref=actor_ref,
                session_id=session_id,
                authority_ref=grant.grant_id,
                authority_version=grant.version,
                target_id=target_id,
                target_version=target.version,
                deployment_identity_ref=target.deployment_identity_ref,
                environment=target.environment,
                scope_key=target.scope.key,
                parameters=clean,
                parameters_digest=digest,
                policy_version=POLICY_VERSION,
                ctrl02_revision=self.ctrl02.revision,
                ctrl03_trust_revision=self.ctrl03.revision,
                requested_at=moment,
                expires_at=moment + MAX_REQUEST_LIFETIME,
                state=ActionState.AWAITING_APPROVAL if required else ActionState.APPROVED,
                approval_state=approval_state,
                required_approver_classes=required,
                incident_ref=incident_ref,
                purpose=purpose,
            )
            self._actions[action_id] = action
            self._idempotency[f"{actor_ref}:{idempotency_key}"] = action_id
            self._decide(
                stage="REQUEST",
                actor_ref=actor_ref,
                grant=grant,
                allowed=True,
                reason="OPS_AUTHORIZED",
                action_id=action_id,
            )
            self._record(
                now=moment,
                actor_ref=actor_ref,
                authority_basis=f"{grant.grant_id}@v{grant.version}",
                action_type=action_type.value,
                scope_key=target.scope.key,
                object_ref=target_id,
                result="REQUESTED",
                reason_code="OPS_AUTHORIZED",
                action_id=action_id,
                attributes={
                    "request_id": action.request_id,
                    "parameters_digest": digest,
                    "deployment_identity_ref": target.deployment_identity_ref,
                    "target_version": target.version,
                    "environment": target.environment.value,
                    "impact": spec.impact.value,
                    "approval_required": ",".join(required) or "NONE",
                },
            )
            self._persist()
            return action

    def _require_backup_identity(
        self, target: OperationalTarget, parameters: Mapping[str, str]
    ) -> None:
        backup_set_id = parameters["backup_set_id"]
        digest = parameters["backup_identity_digest"]
        matches = [
            b
            for b in self._backups.values()
            if b.kind == "BACKUP"
            and b.backup_set_id == backup_set_id
            and b.state is BackupOperationState.COMPLETED
        ]
        if not matches:
            raise AuthorizationRefused(
                "no completed backup with that set id",
                reason_code=OpsRefusal.BACKUP_IDENTITY_MISMATCH,
            )
        latest = matches[-1]
        if latest.target_id != target.target_id or latest.backup_identity_digest != digest:
            raise AuthorizationRefused(
                "backup identity does not match the exact target and digest",
                reason_code=OpsRefusal.BACKUP_IDENTITY_MISMATCH,
            )

    def _require_verified_artifact(self, digest: str, expected_revision: int | None) -> None:
        if not self.policy.enforce_ctrl03_trust:
            return
        self.ctrl03.require(expected_revision)
        if not self.ctrl03.is_verified(digest):
            raise AuthorizationRefused(
                "rollback target artifact is not attested by the CTRL-03 trust set",
                reason_code=OpsRefusal.UNVERIFIED_ARTIFACT,
            )
        known = [d for d in self._deployments.values() if d.artifact_digest == digest]
        if not known or not all(d.verified for d in known):
            raise AuthorizationRefused(
                "rollback target artifact is not a verified deployment identity",
                reason_code=OpsRefusal.UNVERIFIED_ARTIFACT,
            )

    def approve(
        self,
        *,
        action_id: str,
        approver_ref: str,
        session_id: str,
        projection: AuthorityProjection,
        approver_class: str,
        now: datetime,
    ) -> OperationalActionRequest:
        moment = self._time(now)
        with self._lock:
            action = self.action(action_id)
            try:
                if action.state is not ActionState.AWAITING_APPROVAL:
                    raise AuthorizationRefused(
                        f"action is {action.state.value}; approval not applicable",
                        reason_code=OpsRefusal.WRONG_STATE
                        if action.approval_state is ApprovalState.PENDING
                        else OpsRefusal.APPROVAL_NOT_REQUIRED,
                    )
                self._expire_if_due(action, moment)
                if self.policy.reject_self_approval and approver_ref == action.actor_ref:
                    raise AuthorizationRefused(
                        "requester may not approve", reason_code=OpsRefusal.SELF_APPROVAL
                    )
                if approver_class not in action.required_approver_classes:
                    raise AuthorizationRefused(
                        "approver class not required for this action",
                        reason_code=OpsRefusal.APPROVER_CLASS_MISSING,
                    )
                if any(
                    self._approvals[a].approver_class == approver_class
                    and self._approvals[a].state is ApprovalState.GRANTED
                    for a in action.approval_ids
                ):
                    raise AuthorizationRefused(
                        "that approver class already approved",
                        reason_code=OpsRefusal.DUPLICATE_APPROVAL,
                    )
                if any(
                    self._approvals[a].approver_ref == approver_ref for a in action.approval_ids
                ):
                    raise AuthorizationRefused(
                        "one principal supplies one approval",
                        reason_code=OpsRefusal.DUPLICATE_APPROVAL,
                    )
                session = self._session(session_id, approver_ref, moment)
                if self.policy.enforce_read_only_sessions and session.read_only:
                    raise AuthorizationRefused(
                        "read-only session may not approve",
                        reason_code=OpsRefusal.READ_ONLY_SESSION,
                    )
                target = self._target(action.target_id)
                grant = self._verify_projection(
                    projection,
                    principal_id=approver_ref,
                    capability="OPS.APPROVE",
                    scope=target.scope,
                    now=moment,
                    approver_class=approver_class,
                )
                if self.policy.enforce_target_version and target.version != action.target_version:
                    raise AuthorizationRefused(
                        "target changed since request", reason_code=OpsRefusal.STALE_TARGET
                    )
                self._check_ctrl02(action.target_id, session_id, None)
            except AuthorizationRefused as exc:
                self._decide(
                    stage="APPROVE",
                    actor_ref=approver_ref,
                    grant=None,
                    allowed=False,
                    reason=str(exc.reason_code),
                    action_id=action_id,
                    detail=str(exc),
                )
                raise self._refuse(
                    now=moment,
                    actor_ref=approver_ref,
                    action_type=action.action_type.value,
                    scope_key=action.scope_key,
                    object_ref=action.target_id,
                    reason=str(exc.reason_code),
                    action_id=action_id,
                    detail=str(exc),
                ) from exc
            approval = OperationalApproval(
                approval_id=self._next_id("APR"),
                action_id=action_id,
                approver_ref=approver_ref,
                approver_class=approver_class,
                authority_ref=grant.grant_id,
                authority_version=grant.version,
                approved_at=moment,
                expires_at=moment + MAX_APPROVAL_LIFETIME,
                bound_parameters_digest=action.parameters_digest,
                bound_target_version=action.target_version,
                bound_deployment_identity_ref=action.deployment_identity_ref,
                state=ApprovalState.GRANTED,
                session_id=session_id,
            )
            self._approvals[approval.approval_id] = approval
            approval_ids = (*action.approval_ids, approval.approval_id)
            granted_classes = {
                self._approvals[a].approver_class
                for a in approval_ids
                if self._approvals[a].state is ApprovalState.GRANTED
            }
            complete = (
                set(action.required_approver_classes) <= granted_classes
                if self.policy.enforce_quorum
                else True
            )
            updated = replace(
                action,
                approval_ids=approval_ids,
                approval_state=ApprovalState.GRANTED if complete else ApprovalState.PENDING,
                state=ActionState.APPROVED if complete else ActionState.AWAITING_APPROVAL,
            )
            self._actions[action_id] = updated
            self._decide(
                stage="APPROVE",
                actor_ref=approver_ref,
                grant=grant,
                allowed=True,
                reason="OPS_AUTHORIZED",
                action_id=action_id,
            )
            self._record(
                now=moment,
                actor_ref=approver_ref,
                authority_basis=f"{grant.grant_id}@v{grant.version}",
                action_type=action.action_type.value,
                scope_key=action.scope_key,
                object_ref=action.target_id,
                result="APPROVED" if complete else "APPROVAL_RECORDED",
                reason_code="OPS_AUTHORIZED",
                action_id=action_id,
                approval_refs=(approval.approval_id,),
                attributes={
                    "approver_class": approver_class,
                    "bound_parameters_digest": action.parameters_digest,
                    "bound_target_version": action.target_version,
                    "bound_deployment_identity_ref": action.deployment_identity_ref,
                },
            )
            self._persist()
            return updated

    def _expire_if_due(self, action: OperationalActionRequest, moment: datetime) -> None:
        if self.policy.enforce_request_expiry and moment >= action.expires_at:
            self._terminate(
                action.action_id,
                moment,
                ActionState.EXPIRED,
                ResultState.EXPIRED,
                FailureClassification.EXPIRED,
                "request lifetime exceeded before commit",
                actor_ref="system",
            )
            raise AuthorizationRefused("request expired", reason_code=OpsRefusal.REQUEST_EXPIRED)

    def _reauthorize(
        self,
        action: OperationalActionRequest,
        *,
        executor_ref: str,
        session_id: str,
        projection: AuthorityProjection,
        moment: datetime,
    ) -> tuple[AuthorityGrant, OperationalTarget, tuple[str, ...]]:
        """Commit-time reauthorization. Every element of the decision input is
        re-evaluated against the live state; any drift fails closed."""
        spec = ACTION_CATALOGUE[action.action_type]
        target = self._target(action.target_id)
        self._voting_guard(target)
        session = self._session(session_id, executor_ref, moment)
        if self.policy.enforce_read_only_sessions and session.read_only:
            raise AuthorizationRefused(
                "read-only session may not execute", reason_code=OpsRefusal.READ_ONLY_SESSION
            )
        grant = self._verify_projection(
            projection,
            principal_id=executor_ref,
            capability="OPS.EXECUTE",
            scope=target.scope,
            now=moment,
        )
        if not self.policy.commit_time_reauthorization:
            return grant, target, tuple(action.approval_ids)
        # Requester's own authority must still be live and unchanged.
        try:
            requester_grant = self.authorities.grant(action.authority_ref)
        except AuthorizationRefused as exc:
            raise AuthorizationRefused(
                "requesting authority no longer resolvable",
                reason_code=OpsRefusal.STALE_AUTHORITY,
            ) from exc
        if requester_grant.version != action.authority_version or not requester_grant.usable_at(
            moment
        ):
            raise AuthorizationRefused(
                "requesting authority changed or is no longer usable",
                reason_code=OpsRefusal.STALE_AUTHORITY,
            )
        requester_session = self._sessions.get(action.session_id)
        if self.policy.enforce_session_state and (
            requester_session is None or not requester_session.usable_at(moment)[0]
        ):
            raise AuthorizationRefused(
                "requesting session revoked or expired", reason_code=OpsRefusal.SESSION_REVOKED
            )
        if self.policy.enforce_target_version and target.version != action.target_version:
            raise AuthorizationRefused(
                "target identity/version changed since request",
                reason_code=OpsRefusal.STALE_TARGET,
            )
        if (
            self.policy.enforce_deployment_identity
            and target.deployment_identity_ref != action.deployment_identity_ref
        ):
            raise AuthorizationRefused(
                "deployment identity changed since request",
                reason_code=OpsRefusal.STALE_DEPLOYMENT_IDENTITY,
            )
        if self.policy.enforce_environment_match and target.environment is not action.environment:
            raise AuthorizationRefused(
                "environment changed since request", reason_code=OpsRefusal.ENVIRONMENT_MISMATCH
            )
        if self.policy.enforce_exact_scope and target.scope.key != action.scope_key:
            raise AuthorizationRefused(
                "region/scope changed since request", reason_code=OpsRefusal.WRONG_SCOPE
            )
        if (
            self.policy.enforce_parameters_digest
            and parameters_digest(action.parameters) != action.parameters_digest
        ):
            raise AuthorizationRefused(
                "parameters digest changed", reason_code=OpsRefusal.STALE_PARAMETERS
            )
        if action.policy_version != POLICY_VERSION:
            raise AuthorizationRefused(
                "policy version changed since request", reason_code=OpsRefusal.STALE_POLICY
            )
        self._check_ctrl02(action.target_id, action.session_id, action.ctrl02_revision)
        # The executor's own session is subject to the current CTRL-02 state.
        self._check_ctrl02(action.target_id, session_id, None)
        if spec.action_type is ActionType.DEPLOYMENT_ROLLBACK:
            self._require_verified_artifact(
                action.parameters["target_artifact_digest"], action.ctrl03_trust_revision
            )
        if spec.action_type is ActionType.RESTORE_REQUEST:
            self._require_backup_identity(target, action.parameters)
        # Approvals: fresh, bound to the same digest/target/deployment, distinct.
        valid_approvals: list[str] = []
        for approval_id in action.approval_ids:
            approval = self._approvals[approval_id]
            if approval.state is not ApprovalState.GRANTED:
                continue
            stale = (
                (self.policy.enforce_approval_freshness and moment >= approval.expires_at)
                or approval.bound_parameters_digest != action.parameters_digest
                or approval.bound_target_version != action.target_version
                or approval.bound_deployment_identity_ref != action.deployment_identity_ref
            )
            if not stale:
                try:
                    approver_grant = self.authorities.grant(approval.authority_ref)
                    stale = approver_grant.version != approval.authority_version or (
                        not approver_grant.usable_at(moment)
                    )
                except AuthorizationRefused:
                    stale = True
            if not stale and self.policy.enforce_ctrl02_state:
                try:
                    self._check_ctrl02(action.target_id, approval.session_id, None)
                except AuthorizationRefused:
                    stale = True
            if stale:
                self._approvals[approval_id] = replace(approval, state=ApprovalState.EXPIRED)
                continue
            valid_approvals.append(approval_id)
        required = set(action.required_approver_classes)
        granted = {self._approvals[a].approver_class for a in valid_approvals}
        if self.policy.enforce_quorum and not required <= granted:
            missing = sorted(required - granted)
            raise AuthorizationRefused(
                f"approval missing, stale or invalidated for {missing}",
                reason_code=OpsRefusal.STALE_APPROVAL
                if action.approval_ids
                else OpsRefusal.QUORUM_NOT_MET,
            )
        if self.policy.separate_approval_from_execution and any(
            self._approvals[a].approver_ref == executor_ref for a in action.approval_ids
        ):
            raise AuthorizationRefused(
                "an approver may not execute the act they approved",
                reason_code=OpsRefusal.APPROVER_EXECUTES,
            )
        if not spec.requester_may_execute and executor_ref == action.actor_ref:
            raise AuthorizationRefused(
                "high-impact and destructive operations require a distinct executor",
                reason_code=OpsRefusal.REQUESTER_EXECUTES,
            )
        if spec.requires_maintenance_window and self.policy.enforce_maintenance_window:
            active = [
                w
                for w in self._windows.values()
                if w.target_id == action.target_id and w.is_active_at(moment)
            ]
            if not active:
                raise AuthorizationRefused(
                    "destructive restore requires an active maintenance window on the target",
                    reason_code=OpsRefusal.MAINTENANCE_REQUIRED,
                )
        return grant, target, tuple(valid_approvals)

    def commit(
        self,
        *,
        action_id: str,
        executor_ref: str,
        session_id: str,
        projection: AuthorityProjection,
        now: datetime,
    ) -> OperationalActionRequest:
        """Commit-time reauthorization followed by execution dispatch.

        Returns the action in EXECUTING state (dispatch acknowledged, which is
        never success) or in a terminal state when dispatch itself was refused
        by the adapter or the capability is unsupported.
        """
        moment = self._time(now)
        with self._lock:
            action = self.action(action_id)
            try:
                if action.state in TERMINAL_ACTION_STATES or action.state is ActionState.EXECUTING:
                    raise AuthorizationRefused(
                        f"action already {action.state.value}; no duplicate execution",
                        reason_code=OpsRefusal.DUPLICATE_EXECUTION,
                    )
                if action.execution_id is not None:
                    raise AuthorizationRefused(
                        "action already carries an execution; no duplicate execution",
                        reason_code=OpsRefusal.DUPLICATE_EXECUTION,
                    )
                if action.state is ActionState.AWAITING_APPROVAL:
                    raise AuthorizationRefused(
                        "approval quorum not met", reason_code=OpsRefusal.QUORUM_NOT_MET
                    )
                self._expire_if_due(action, moment)
                grant, target, approvals = self._reauthorize(
                    action,
                    executor_ref=executor_ref,
                    session_id=session_id,
                    projection=projection,
                    moment=moment,
                )
                if self.policy.enforce_concurrency_guard:
                    other = self._executing_targets.get(action.target_id)
                    if other is not None and other != action_id:
                        raise AuthorizationRefused(
                            f"target already has executing action {other}",
                            reason_code=OpsRefusal.CONFLICTING_EXECUTION,
                        )
            except AuthorizationRefused as exc:
                self._decide(
                    stage="COMMIT",
                    actor_ref=executor_ref,
                    grant=None,
                    allowed=False,
                    reason=str(exc.reason_code),
                    action_id=action_id,
                    detail=str(exc),
                )
                raise self._refuse(
                    now=moment,
                    actor_ref=executor_ref,
                    action_type=action.action_type.value,
                    scope_key=action.scope_key,
                    object_ref=action.target_id,
                    reason=str(exc.reason_code),
                    action_id=action_id,
                    detail=str(exc),
                ) from exc
            self._decide(
                stage="COMMIT",
                actor_ref=executor_ref,
                grant=grant,
                allowed=True,
                reason="OPS_REAUTHORIZED",
                action_id=action_id,
            )
            self._record(
                now=moment,
                actor_ref=executor_ref,
                authority_basis=f"{grant.grant_id}@v{grant.version}",
                action_type=action.action_type.value,
                scope_key=action.scope_key,
                object_ref=action.target_id,
                result="COMMIT_REAUTHORIZED",
                reason_code="OPS_REAUTHORIZED",
                action_id=action_id,
                approval_refs=approvals,
                attributes={
                    "parameters_digest": action.parameters_digest,
                    "deployment_identity_ref": action.deployment_identity_ref,
                    "target_version": action.target_version,
                },
            )
            return self._dispatch(action, grant, target, executor_ref, approvals, moment)

    def _dispatch(
        self,
        action: OperationalActionRequest,
        grant: AuthorityGrant,
        target: OperationalTarget,
        executor_ref: str,
        approvals: tuple[str, ...],
        moment: datetime,
    ) -> OperationalActionRequest:
        spec = ACTION_CATALOGUE[action.action_type]
        execution = OperationalExecution(
            execution_id=self._next_id("EXE"),
            action_id=action.action_id,
            executor_ref=executor_ref,
            executor_authority_ref=f"{grant.grant_id}@v{grant.version}",
            adapter_id=target.adapter_id,
            dispatched_at=moment,
            deadline=moment + MAX_EXECUTION_WAIT,
            state=ExecutionState.NOT_DISPATCHED,
        )
        self._executions[execution.execution_id] = execution
        action = replace(
            action, execution_id=execution.execution_id, approval_ids=action.approval_ids
        )
        self._actions[action.action_id] = action

        # Actions that the console itself owns (no backend capability).
        if spec.capability is None:
            return self._complete_internal(action, execution, moment)

        adapter = self.adapters.get(target.adapter_id)
        if adapter is None or not adapter.available:
            return self._terminate(
                action.action_id,
                moment,
                ActionState.FAILED,
                ResultState.FAILED,
                FailureClassification.ADAPTER_UNAVAILABLE,
                "backend adapter unavailable at dispatch",
                actor_ref=executor_ref,
                execution_state=ExecutionState.FAILED,
            )
        if self.policy.enforce_unsupported_explicit and spec.capability not in adapter.capabilities(
            target.target_id
        ):
            return self._terminate(
                action.action_id,
                moment,
                ActionState.UNSUPPORTED,
                ResultState.UNSUPPORTED,
                FailureClassification.UNSUPPORTED_CAPABILITY,
                f"backend does not support {spec.capability.value} for this target",
                actor_ref=executor_ref,
                execution_state=ExecutionState.UNSUPPORTED,
            )
        request = DispatchRequest(
            execution_id=execution.execution_id,
            action_id=action.action_id,
            action_type=action.action_type.value,
            capability=spec.capability,
            target_id=target.target_id,
            deployment_identity_ref=target.deployment_identity_ref,
            parameters=dict(action.parameters),
            parameters_digest=action.parameters_digest,
            requested_by=action.actor_ref,
            executed_by=executor_ref,
            approval_refs=approvals,
        )
        try:
            ack = adapter.dispatch(request)
        except Exception as exc:
            return self._terminate(
                action.action_id,
                moment,
                ActionState.FAILED,
                ResultState.FAILED,
                FailureClassification.ADAPTER_UNAVAILABLE,
                f"dispatch raised {type(exc).__name__}; outcome unknown, not retried",
                actor_ref=executor_ref,
                execution_state=ExecutionState.FAILED,
            )
        if ack.duplicate:
            return self._terminate(
                action.action_id,
                moment,
                ActionState.FAILED,
                ResultState.FAILED,
                FailureClassification.PRECONDITION_FAILED,
                "adapter reported replayed execution id",
                actor_ref=executor_ref,
                execution_state=ExecutionState.FAILED,
            )
        if not ack.accepted:
            return self._terminate(
                action.action_id,
                moment,
                ActionState.FAILED,
                ResultState.FAILED,
                FailureClassification.PROVIDER_FAILURE,
                f"dispatch refused by backend: {ack.detail}",
                actor_ref=executor_ref,
                execution_state=ExecutionState.FAILED,
                backend_operation_ref=ack.backend_operation_ref,
            )
        execution = replace(
            execution,
            state=ExecutionState.DISPATCHED,
            backend_operation_ref=ack.backend_operation_ref,
        )
        self._executions[execution.execution_id] = execution
        action = replace(
            action,
            state=ActionState.EXECUTING,
            execution_state=ExecutionState.DISPATCHED,
            backend_operation_ref=ack.backend_operation_ref,
        )
        if self.policy.dispatch_is_not_success:
            # A dispatch acknowledgement is a pending state, never a result.
            action = replace(action, result_state=ResultState.PENDING)
        else:  # pragma: no cover - mutation path only
            action = replace(
                action, state=ActionState.SUCCEEDED, result_state=ResultState.SUCCEEDED
            )
        self._actions[action.action_id] = action
        self._executing_targets[action.target_id] = action.action_id
        self._record(
            now=moment,
            actor_ref=executor_ref,
            authority_basis=execution.executor_authority_ref,
            action_type=action.action_type.value,
            scope_key=action.scope_key,
            object_ref=action.target_id,
            result="DISPATCHED",
            reason_code="OPS_DISPATCH_ACKNOWLEDGED_NOT_SUCCESS",
            action_id=action.action_id,
            approval_refs=approvals,
            attributes={
                "execution_id": execution.execution_id,
                "backend_operation_ref": ack.backend_operation_ref,
                "adapter_id": target.adapter_id,
            },
        )
        self._persist()
        return action

    def _complete_internal(
        self,
        action: OperationalActionRequest,
        execution: OperationalExecution,
        moment: datetime,
    ) -> OperationalActionRequest:
        if action.action_type is ActionType.INCIDENT_LINK:
            incident = self._incidents[action.parameters["incident_id"]]
            linked = action.parameters["linked_action_id"]
            self._incidents[incident.incident_id] = replace(
                incident, linked_action_ids=(*incident.linked_action_ids, linked)
            )
            target_action = self._actions[linked]
            self._actions[linked] = replace(target_action, incident_ref=incident.incident_id)
        self._executions[execution.execution_id] = replace(
            execution, state=ExecutionState.COMPLETED
        )
        return self._terminate(
            action.action_id,
            moment,
            ActionState.SUCCEEDED,
            ResultState.SUCCEEDED,
            FailureClassification.NONE,
            "console-owned mutation completed",
            actor_ref=execution.executor_ref,
            execution_state=ExecutionState.COMPLETED,
        )

    def resolve(self, *, action_id: str, now: datetime) -> OperationalActionRequest:
        """Observe the backend outcome and, if terminal, record the result.

        The result is derived from the adapter's own report, never from a
        caller-supplied state.
        """
        moment = self._time(now)
        with self._lock:
            action = self.action(action_id)
            if action.state is not ActionState.EXECUTING:
                if self._executing_targets.get(action.target_id) == action_id:
                    return self._reconcile_timed_out(action, moment)
                return action
            execution = self._executions[action.execution_id or ""]
            target = self._targets[action.target_id]
            adapter = self.adapters.get(target.adapter_id)
            assert execution.backend_operation_ref is not None
            if adapter is None or not adapter.available:
                outcome = BackendOutcome(BackendState.RUNNING, "adapter unavailable", {})
            else:
                outcome = adapter.poll(execution.backend_operation_ref)
            self._executions[execution.execution_id] = replace(
                execution, last_observed_at=moment, state=ExecutionState.RUNNING
            )
            if outcome.state is BackendState.RUNNING:
                if moment >= execution.deadline:
                    return self._terminate(
                        action_id,
                        moment,
                        ActionState.FAILED,
                        ResultState.FAILED,
                        FailureClassification.TIMEOUT,
                        "backend did not reach a terminal state before the deadline",
                        actor_ref=execution.executor_ref,
                        execution_state=ExecutionState.TIMED_OUT,
                        metadata=outcome.metadata,
                    )
                self._actions[action_id] = replace(action, execution_state=ExecutionState.RUNNING)
                self._persist()
                return self._actions[action_id]
            mapping = {
                BackendState.COMPLETED: (
                    ActionState.SUCCEEDED,
                    ResultState.SUCCEEDED,
                    FailureClassification.NONE,
                    ExecutionState.COMPLETED,
                ),
                BackendState.FAILED: (
                    ActionState.FAILED,
                    ResultState.FAILED,
                    FailureClassification.PROVIDER_FAILURE,
                    ExecutionState.FAILED,
                ),
                BackendState.PARTIAL: (
                    ActionState.PARTIAL_FAILURE,
                    ResultState.PARTIAL_FAILURE,
                    FailureClassification.PARTIAL_PROVIDER_FAILURE,
                    ExecutionState.PARTIAL,
                ),
                BackendState.UNSUPPORTED: (
                    ActionState.UNSUPPORTED,
                    ResultState.UNSUPPORTED,
                    FailureClassification.UNSUPPORTED_CAPABILITY,
                    ExecutionState.UNSUPPORTED,
                ),
            }
            state, result_state, classification, execution_state = mapping[outcome.state]
            updated = self._terminate(
                action_id,
                moment,
                state,
                result_state,
                classification,
                outcome.detail,
                actor_ref=execution.executor_ref,
                execution_state=execution_state,
                metadata=outcome.metadata,
            )
            self._apply_side_effects(updated, moment, outcome)
            return self._actions[action_id]

    def _reconcile_timed_out(
        self, action: OperationalActionRequest, moment: datetime
    ) -> OperationalActionRequest:
        """Observe a late backend outcome after TIMEOUT and release the guard.

        The action's terminal FAILED/TIMEOUT result is never rewritten; the
        late outcome is appended as its own evidence record.
        """
        execution = self._executions[action.execution_id or ""]
        target = self._targets[action.target_id]
        adapter = self.adapters.get(target.adapter_id)
        if adapter is None or not adapter.available or execution.backend_operation_ref is None:
            return action
        outcome = adapter.poll(execution.backend_operation_ref)
        if outcome.state is BackendState.RUNNING:
            return action
        del self._executing_targets[action.target_id]
        meta, _ = redact_metadata(dict(outcome.metadata))
        self._record(
            now=moment,
            actor_ref="system",
            authority_basis=execution.executor_authority_ref,
            action_type=action.action_type.value,
            scope_key=action.scope_key,
            object_ref=action.target_id,
            result="LATE_BACKEND_OUTCOME",
            reason_code=f"OPS_LATE_{outcome.state.value}",
            action_id=action.action_id,
            attributes={"late_backend_state": outcome.state.value, **meta},
        )
        self._persist()
        return action

    def _apply_side_effects(
        self, action: OperationalActionRequest, moment: datetime, outcome: BackendOutcome
    ) -> None:
        if (
            action.action_type is ActionType.MAINTENANCE_ENTER
            and action.state is ActionState.SUCCEEDED
        ):
            minutes = int(action.parameters.get("duration_minutes", "0"))
            window = MaintenanceWindowRef(
                window_id=self._next_id("MW"),
                target_id=action.target_id,
                state=MaintenanceWindowState.ACTIVE,
                starts_at=moment,
                ends_at=moment + timedelta(minutes=minutes),
                reason=action.parameters.get("reason", ""),
                action_id=action.action_id,
            )
            self._windows[window.window_id] = window
            self._actions[action.action_id] = replace(
                action, maintenance_window_ref=window.window_id
            )
        elif (
            action.action_type is ActionType.MAINTENANCE_EXIT
            and action.state is ActionState.SUCCEEDED
        ):
            window = self._windows[action.parameters["window_id"]]
            self._windows[window.window_id] = replace(
                window, state=MaintenanceWindowState.CLOSED, closed_by_action_id=action.action_id
            )
            self._actions[action.action_id] = replace(
                action, maintenance_window_ref=window.window_id
            )
        elif action.action_type in {ActionType.BACKUP_REQUEST, ActionType.RESTORE_REQUEST}:
            kind = "BACKUP" if action.action_type is ActionType.BACKUP_REQUEST else "RESTORE"
            state = {
                ActionState.SUCCEEDED: BackupOperationState.COMPLETED,
                ActionState.UNSUPPORTED: BackupOperationState.UNSUPPORTED,
            }.get(action.state, BackupOperationState.FAILED)
            digest = (
                outcome.metadata.get("backup_identity_digest", "")
                if kind == "BACKUP"
                else (action.parameters.get("backup_identity_digest", ""))
            )
            operation = BackupRestoreOperationRef(
                operation_id=self._next_id("BRO"),
                kind=kind,
                target_id=action.target_id,
                backup_set_id=action.parameters.get("backup_set_id", ""),
                backup_identity_digest=str(digest),
                state=state,
                action_id=action.action_id,
                requested_at=action.requested_at,
                backend_operation_ref=action.backend_operation_ref,
                completed_at=moment,
            )
            self._backups[operation.operation_id] = operation
        self._persist()

    def _terminate(
        self,
        action_id: str,
        moment: datetime,
        state: ActionState,
        result_state: ResultState,
        classification: FailureClassification,
        detail: str,
        *,
        actor_ref: str,
        execution_state: ExecutionState | None = None,
        backend_operation_ref: str | None = None,
        metadata: Mapping[str, str] | None = None,
    ) -> OperationalActionRequest:
        action = self._actions[action_id]
        meta, redacted = redact_metadata(dict(metadata or {}))
        if not self.policy.enforce_secret_redaction:
            meta, redacted = dict(metadata or {}), []
        result = OperationalResult(
            result_id=self._next_id("RES"),
            action_id=action_id,
            execution_id=action.execution_id,
            state=result_state,
            failure_classification=classification,
            detail=scrub_text(detail)[:512],
            completed_at=moment,
            backend_metadata=meta,
            redacted_fields=tuple(redacted),
        )
        self._results[result.result_id] = result
        if action.execution_id is not None and execution_state is not None:
            execution = self._executions[action.execution_id]
            self._executions[action.execution_id] = replace(
                execution,
                state=execution_state,
                last_observed_at=moment,
                backend_operation_ref=execution.backend_operation_ref or backend_operation_ref,
            )
        updated = replace(
            action,
            state=state,
            result_state=result_state,
            result_id=result.result_id,
            execution_state=execution_state or action.execution_state,
            backend_operation_ref=action.backend_operation_ref or backend_operation_ref,
            refusal_reason=None,
        )
        self._actions[action_id] = updated
        if (
            self._executing_targets.get(action.target_id) == action_id
            and execution_state is not ExecutionState.TIMED_OUT
        ):
            # A timed-out backend may still be working: the target stays guarded
            # until a late terminal outcome is observed (`_reconcile_timed_out`).
            del self._executing_targets[action.target_id]
        self._record(
            now=moment,
            actor_ref=actor_ref,
            authority_basis=(
                self._executions[action.execution_id].executor_authority_ref
                if action.execution_id
                else "SYSTEM"
            ),
            action_type=action.action_type.value,
            scope_key=action.scope_key,
            object_ref=action.target_id,
            result=state.value,
            reason_code=f"OPS_RESULT_{result_state.value}",
            action_id=action_id,
            approval_refs=tuple(action.approval_ids),
            attributes={
                "result_id": result.result_id,
                "failure_classification": classification.value,
                "detail": scrub_text(detail)[:200],
                "deployment_identity_ref": action.deployment_identity_ref,
                "redacted_fields": ",".join(redacted) or "NONE",
                **{f"backend.{k}": v for k, v in (metadata or {}).items()},
            },
        )
        self._persist()
        return updated

    def cancel(
        self, *, action_id: str, actor_ref: str, session_id: str, now: datetime
    ) -> OperationalActionRequest:
        moment = self._time(now)
        with self._lock:
            action = self.action(action_id)
            try:
                session = self._session(session_id, actor_ref, moment)
                if self.policy.enforce_read_only_sessions and session.read_only:
                    raise AuthorizationRefused(
                        "read-only session may not cancel", reason_code=OpsRefusal.READ_ONLY_SESSION
                    )
                if action.state in TERMINAL_ACTION_STATES or action.state is ActionState.EXECUTING:
                    raise AuthorizationRefused(
                        f"cannot cancel an action in {action.state.value}",
                        reason_code=OpsRefusal.WRONG_STATE,
                    )
                if actor_ref != action.actor_ref:
                    raise AuthorizationRefused(
                        "only the requester may cancel before execution",
                        reason_code=OpsRefusal.WRONG_STATE,
                    )
            except AuthorizationRefused as exc:
                raise self._refuse(
                    now=moment,
                    actor_ref=actor_ref,
                    action_type=action.action_type.value,
                    scope_key=action.scope_key,
                    object_ref=action.target_id,
                    reason=str(exc.reason_code),
                    action_id=action_id,
                    detail=str(exc),
                ) from exc
            return self._terminate(
                action_id,
                moment,
                ActionState.CANCELLED,
                ResultState.CANCELLED,
                FailureClassification.CANCELLED,
                "cancelled by requester before execution",
                actor_ref=actor_ref,
            )

    def expire_due(self, *, now: datetime) -> tuple[str, ...]:
        moment = self._time(now)
        expired: list[str] = []
        with self._lock:
            for action in list(self._actions.values()):
                if action.state in {ActionState.AWAITING_APPROVAL, ActionState.APPROVED} and (
                    moment >= action.expires_at
                ):
                    self._terminate(
                        action.action_id,
                        moment,
                        ActionState.EXPIRED,
                        ResultState.EXPIRED,
                        FailureClassification.EXPIRED,
                        "request lifetime exceeded",
                        actor_ref="system",
                    )
                    expired.append(action.action_id)
            for window in list(self._windows.values()):
                if window.state is MaintenanceWindowState.ACTIVE and moment >= window.ends_at:
                    self._windows[window.window_id] = replace(
                        window, state=MaintenanceWindowState.EXPIRED
                    )
                    self._record(
                        now=moment,
                        actor_ref="system",
                        authority_basis="SYSTEM",
                        action_type=ActionType.MAINTENANCE_ENTER.value,
                        scope_key=self._targets[window.target_id].scope.key,
                        object_ref=window.target_id,
                        result="MAINTENANCE_WINDOW_EXPIRED",
                        reason_code="OPS_MAINTENANCE_WINDOW_EXPIRED",
                        action_id=window.action_id,
                        attributes={"window_id": window.window_id},
                    )
            self._persist()
        return tuple(expired)

    def review(
        self,
        *,
        action_id: str,
        reviewer_ref: str,
        session_id: str,
        projection: AuthorityProjection,
        now: datetime,
    ) -> OperationalActionRequest:
        moment = self._time(now)
        with self._lock:
            action = self.action(action_id)
            try:
                if action.state not in TERMINAL_ACTION_STATES:
                    raise AuthorizationRefused(
                        "only terminal actions are reviewed", reason_code=OpsRefusal.WRONG_STATE
                    )
                session = self._session(session_id, reviewer_ref, moment)
                if self.policy.enforce_read_only_sessions and session.read_only:
                    raise AuthorizationRefused(
                        "read-only session may not review", reason_code=OpsRefusal.READ_ONLY_SESSION
                    )
                target = self._target(action.target_id)
                grant = self._verify_projection(
                    projection,
                    principal_id=reviewer_ref,
                    capability="OPS.REVIEW",
                    scope=target.scope,
                    now=moment,
                )
                execution = self.execution_of(action_id)
                if self.policy.separate_execution_from_review and (
                    reviewer_ref == action.actor_ref
                    or (execution is not None and execution.executor_ref == reviewer_ref)
                    or any(
                        self._approvals[a].approver_ref == reviewer_ref for a in action.approval_ids
                    )
                ):
                    raise AuthorizationRefused(
                        "a participant of the act may not review it",
                        reason_code=OpsRefusal.EXECUTOR_REVIEWS,
                    )
            except AuthorizationRefused as exc:
                self._decide(
                    stage="REVIEW",
                    actor_ref=reviewer_ref,
                    grant=None,
                    allowed=False,
                    reason=str(exc.reason_code),
                    action_id=action_id,
                    detail=str(exc),
                )
                raise self._refuse(
                    now=moment,
                    actor_ref=reviewer_ref,
                    action_type=action.action_type.value,
                    scope_key=action.scope_key,
                    object_ref=action.target_id,
                    reason=str(exc.reason_code),
                    action_id=action_id,
                    detail=str(exc),
                ) from exc
            updated = replace(action, review_state=ReviewState.REVIEWED, reviewed_by=reviewer_ref)
            self._actions[action_id] = updated
            self._decide(
                stage="REVIEW",
                actor_ref=reviewer_ref,
                grant=grant,
                allowed=True,
                reason="OPS_REVIEWED",
                action_id=action_id,
            )
            self._record(
                now=moment,
                actor_ref=reviewer_ref,
                authority_basis=f"{grant.grant_id}@v{grant.version}",
                action_type=action.action_type.value,
                scope_key=action.scope_key,
                object_ref=action.target_id,
                result="REVIEWED",
                reason_code="OPS_REVIEWED",
                action_id=action_id,
            )
            self._persist()
            return updated

    # -- checkpoint ----------------------------------------------------------

    def checkpoint(self) -> dict[str, Any]:
        def dump(value: Any) -> Any:
            if isinstance(value, datetime):
                return value.isoformat()
            if isinstance(value, StrEnum):
                return value.value
            if isinstance(value, ExactScope):
                return {"region_id": value.region_id, "org_id": value.org_id}
            if isinstance(value, frozenset | set):
                return sorted(dump(v) for v in value)
            if isinstance(value, tuple | list):
                return [dump(v) for v in value]
            if isinstance(value, dict):
                return {k: dump(v) for k, v in value.items()}
            return value

        return {
            "schema": "epd2.ctrl04.checkpoint/1",
            "targets": {k: dump(asdict(v)) for k, v in self._targets.items()},
            "deployments": {k: dump(asdict(v)) for k, v in self._deployments.items()},
            "sessions": {k: dump(asdict(v)) for k, v in self._sessions.items()},
            "actions": {k: dump(asdict(v)) for k, v in self._actions.items()},
            "approvals": {k: dump(asdict(v)) for k, v in self._approvals.items()},
            "executions": {k: dump(asdict(v)) for k, v in self._executions.items()},
            "results": {k: dump(asdict(v)) for k, v in self._results.items()},
            "evidence_refs": {
                k: [dump(asdict(r)) for r in v] for k, v in self._evidence_refs.items()
            },
            "decisions": {k: [dump(asdict(d)) for d in v] for k, v in self._decisions.items()},
            "idempotency": dict(self._idempotency),
            "executing_targets": dict(self._executing_targets),
            "windows": {k: dump(asdict(v)) for k, v in self._windows.items()},
            "backups": {k: dump(asdict(v)) for k, v in self._backups.items()},
            "incidents": {k: dump(asdict(v)) for k, v in self._incidents.items()},
            "counter": self._counter,
            "last_time": self._last_time.isoformat(),
            "journal": self.journal.export(),
            "journal_anchor": list(self.journal.anchor()),
            "journal_seal": (
                None if self.sealer is None else self.sealer.seal(*self.journal.anchor())
            ),
        }

    @classmethod
    def from_checkpoint(
        cls,
        payload: Mapping[str, Any],
        *,
        authorities: AuthorityDirectory,
        signer: AuthorityProjectionSigner,
        adapters: Mapping[str, OperationsAdapter],
        ctrl02: Ctrl02State | None = None,
        ctrl03: Ctrl03TrustState | None = None,
        policy: OperationsPolicy | None = None,
        store: Any | None = None,
        sealer: EvidenceSealer | None = None,
    ) -> OperationsConsoleService:
        service = cls(
            authorities=authorities,
            signer=signer,
            adapters=adapters,
            ctrl02=ctrl02,
            ctrl03=ctrl03,
            policy=policy,
            store=None,
            sealer=sealer,
        )
        if payload.get("schema") != "epd2.ctrl04.checkpoint/1":
            raise ValueError("unknown checkpoint schema")

        def scope(value: Mapping[str, str]) -> ExactScope:
            return ExactScope(value["region_id"], value["org_id"])

        for key, value in payload["targets"].items():
            service._targets[key] = OperationalTarget(
                target_id=value["target_id"],
                target_class=TargetClass(value["target_class"]),
                domain=TargetDomain(value["domain"]),
                environment=EnvironmentClass(value["environment"]),
                scope=scope(value["scope"]),
                deployment_identity_ref=value["deployment_identity_ref"],
                adapter_id=value["adapter_id"],
                version=int(value["version"]),
                capabilities=frozenset(AdapterCapability(c) for c in value["capabilities"]),
                display_name=value.get("display_name", ""),
            )
        for key, value in payload["deployments"].items():
            service._deployments[key] = DeploymentIdentity(**value)
        for key, value in payload["sessions"].items():
            service._sessions[key] = ConsoleSession(
                session_id=value["session_id"],
                principal_id=value["principal_id"],
                state=SessionState(value["state"]),
                established_at=_dt(value["established_at"]),
                expires_at=_dt(value["expires_at"]),
                read_only=bool(value["read_only"]),
                assurance_level=value.get("assurance_level", "AAL2"),
            )
        for key, value in payload["actions"].items():
            service._actions[key] = OperationalActionRequest(
                action_id=value["action_id"],
                request_id=value["request_id"],
                idempotency_key=value["idempotency_key"],
                action_type=ActionType(value["action_type"]),
                impact=ImpactClass(value["impact"]),
                actor_ref=value["actor_ref"],
                session_id=value["session_id"],
                authority_ref=value["authority_ref"],
                authority_version=int(value["authority_version"]),
                target_id=value["target_id"],
                target_version=int(value["target_version"]),
                deployment_identity_ref=value["deployment_identity_ref"],
                environment=EnvironmentClass(value["environment"]),
                scope_key=value["scope_key"],
                parameters=dict(value["parameters"]),
                parameters_digest=value["parameters_digest"],
                policy_version=value["policy_version"],
                ctrl02_revision=int(value["ctrl02_revision"]),
                ctrl03_trust_revision=int(value["ctrl03_trust_revision"]),
                requested_at=_dt(value["requested_at"]),
                expires_at=_dt(value["expires_at"]),
                state=ActionState(value["state"]),
                approval_state=ApprovalState(value["approval_state"]),
                required_approver_classes=tuple(value["required_approver_classes"]),
                execution_state=ExecutionState(value["execution_state"]),
                result_state=ResultState(value["result_state"]),
                review_state=ReviewState(value["review_state"]),
                approval_ids=tuple(value["approval_ids"]),
                execution_id=value.get("execution_id"),
                result_id=value.get("result_id"),
                incident_ref=value.get("incident_ref"),
                maintenance_window_ref=value.get("maintenance_window_ref"),
                backend_operation_ref=value.get("backend_operation_ref"),
                refusal_reason=value.get("refusal_reason"),
                reviewed_by=value.get("reviewed_by"),
                purpose=value.get("purpose", ""),
            )
        for key, value in payload["approvals"].items():
            service._approvals[key] = OperationalApproval(
                **{
                    **value,
                    "approved_at": _dt(value["approved_at"]),
                    "expires_at": _dt(value["expires_at"]),
                    "state": ApprovalState(value["state"]),
                }
            )
        for key, value in payload["executions"].items():
            service._executions[key] = OperationalExecution(
                **{
                    **value,
                    "dispatched_at": _dt(value["dispatched_at"]),
                    "deadline": _dt(value["deadline"]),
                    "state": ExecutionState(value["state"]),
                    "last_observed_at": None
                    if value.get("last_observed_at") is None
                    else _dt(value["last_observed_at"]),
                }
            )
        for key, value in payload["results"].items():
            service._results[key] = OperationalResult(
                **{
                    **value,
                    "state": ResultState(value["state"]),
                    "failure_classification": FailureClassification(
                        value["failure_classification"]
                    ),
                    "completed_at": _dt(value["completed_at"]),
                    "backend_metadata": dict(value["backend_metadata"]),
                    "redacted_fields": tuple(value["redacted_fields"]),
                }
            )
        for key, value in payload["evidence_refs"].items():
            service._evidence_refs[key] = [OperationalEvidenceRef(**r) for r in value]
        for key, value in payload["decisions"].items():
            service._decisions[key] = [AuthorizationDecision(**d) for d in value]
        service._idempotency = dict(payload["idempotency"])
        service._executing_targets = dict(payload["executing_targets"])
        for key, value in payload["windows"].items():
            service._windows[key] = MaintenanceWindowRef(
                **{
                    **value,
                    "state": MaintenanceWindowState(value["state"]),
                    "starts_at": _dt(value["starts_at"]),
                    "ends_at": _dt(value["ends_at"]),
                }
            )
        for key, value in payload["backups"].items():
            service._backups[key] = BackupRestoreOperationRef(
                **{
                    **value,
                    "state": BackupOperationState(value["state"]),
                    "requested_at": _dt(value["requested_at"]),
                    "completed_at": None
                    if value.get("completed_at") is None
                    else _dt(value["completed_at"]),
                }
            )
        for key, value in payload["incidents"].items():
            service._incidents[key] = OperationalIncidentRef(
                **{**value, "linked_action_ids": tuple(value["linked_action_ids"])}
            )
        service._counter = int(payload["counter"])
        service._last_time = _dt(payload["last_time"])
        service._restore_journal(
            payload["journal"], payload["journal_anchor"], payload.get("journal_seal")
        )
        service._verify_state_against_journal()
        service._store = store
        return service

    def _restore_journal(
        self, records: list[dict[str, Any]], anchor: list[Any], seal: str | None
    ) -> None:
        """Re-append every historical record and refuse a rewritten history.

        The stored hashes are recomputed through the same append path; a
        mismatch means the persisted evidence was altered and the console
        fails closed rather than trusting it.
        """
        for record in records:
            event = self.journal.append(
                occurred_at=_dt(record["occurred_at"]),
                actor_ref=record["actor_ref"],
                actor_class=record["actor_class"],
                authority_basis=record["authority_basis"],
                action_id=record["action_id"],
                scope_key=record["scope_key"],
                object_ref=record["object_ref"],
                result=record["result"],
                reason_code=record["reason_code"],
                approval_refs=tuple(record["approval_refs"]),
                correlation_ref=record["correlation_ref"],
                attributes=record["attributes"],
            )
            if self.policy.enforce_evidence_immutability and (
                event.event_hash != record["event_hash"]
                or event.previous_event_hash != record["previous_event_hash"]
                or event.sequence != record["sequence"]
            ):
                raise AuthorizationRefused(
                    f"persisted evidence record {record['sequence']} does not re-verify",
                    reason_code=OpsRefusal.EVIDENCE_IMMUTABLE,
                )
        if self.policy.enforce_evidence_immutability and list(self.journal.anchor()) != list(
            anchor
        ):
            raise AuthorizationRefused(
                "persisted evidence anchor does not match",
                reason_code=OpsRefusal.EVIDENCE_IMMUTABLE,
            )
        if self.policy.enforce_evidence_immutability:
            count, head = self.journal.anchor()
            if self.sealer is None:
                if seal is not None:
                    raise AuthorizationRefused(
                        "sealed evidence cannot be verified without the evidence key",
                        reason_code=OpsRefusal.EVIDENCE_IMMUTABLE,
                    )
            elif seal is None or not self.sealer.verify(count, head, seal):
                raise AuthorizationRefused(
                    "persisted evidence seal does not verify; history may have been rewritten",
                    reason_code=OpsRefusal.EVIDENCE_IMMUTABLE,
                )
        self.journal.verify()

    def _verify_state_against_journal(self) -> None:
        """Refuse a checkpoint whose action tables disagree with the journal.

        Action/result tables are convenience projections; the journal is the
        evidence. A terminal action must be backed by a matching terminal
        journal record, and a non-terminal action must not have one.
        """
        if not self.policy.enforce_evidence_immutability:
            return
        # A REFUSED journal record marks a refused *attempt* (e.g. a stale commit)
        # on an action that continues to exist; it never terminates the action.
        terminal_values = {
            state.value for state in TERMINAL_ACTION_STATES if state is not ActionState.REFUSED
        }
        by_action: dict[str, list[Any]] = {}
        for record in self.journal.records():
            by_action.setdefault(record.correlation_ref, []).append(record)
        for action in self._actions.values():
            trail = by_action.get(action.action_id, [])
            terminal = [r for r in trail if r.result in terminal_values]
            if action.state in TERMINAL_ACTION_STATES:
                if not terminal or terminal[-1].result != action.state.value:
                    raise AuthorizationRefused(
                        f"action {action.action_id} state {action.state.value} is not backed "
                        f"by its evidence trail",
                        reason_code=OpsRefusal.EVIDENCE_IMMUTABLE,
                    )
                if terminal[-1].reason_code != f"OPS_RESULT_{action.result_state.value}":
                    raise AuthorizationRefused(
                        f"action {action.action_id} result does not match its evidence",
                        reason_code=OpsRefusal.EVIDENCE_IMMUTABLE,
                    )
                if action.result_id is not None:
                    result = self._results[action.result_id]
                    if (
                        result.state is not action.result_state
                        or terminal[-1].attributes.get("failure_classification")
                        != result.failure_classification.value
                    ):
                        raise AuthorizationRefused(
                            f"result {action.result_id} disagrees with its evidence",
                            reason_code=OpsRefusal.EVIDENCE_IMMUTABLE,
                        )
            elif terminal:
                raise AuthorizationRefused(
                    f"action {action.action_id} is non-terminal but evidence shows "
                    f"{terminal[-1].result}",
                    reason_code=OpsRefusal.EVIDENCE_IMMUTABLE,
                )
            if not trail or trail[0].actor_ref != action.actor_ref:
                raise AuthorizationRefused(
                    f"action {action.action_id} actor is not backed by its evidence trail",
                    reason_code=OpsRefusal.EVIDENCE_IMMUTABLE,
                )

    # -- read model ----------------------------------------------------------

    def read_model(self, *, now: datetime) -> dict[str, Any]:
        """Console read model: typed states, redacted details, no secrets."""
        with self._lock:
            return self._read_model(now)

    def _read_model(self, now: datetime) -> dict[str, Any]:
        payload = {
            "schema": "epd2.ctrl04.operations-read-model/1",
            "stage": STAGE,
            "self_state": SELF_STATE,
            "as_of": now.isoformat(),
            "targets": [
                {
                    "target_id": t.target_id,
                    "target_class": t.target_class.value,
                    "environment": t.environment.value,
                    "production_like": t.environment is EnvironmentClass.PRODUCTION_LIKE,
                    "scope": t.scope.key,
                    "deployment_identity_ref": t.deployment_identity_ref,
                    "artifact_digest": (
                        self._deployments[t.deployment_identity_ref].artifact_digest
                        if t.deployment_identity_ref in self._deployments
                        else None
                    ),
                    "version": t.version,
                    "adapter_id": t.adapter_id,
                    "supported_capabilities": sorted(c.value for c in t.capabilities),
                    "display_name": t.display_name,
                }
                for t in self.targets()
            ],
            "actions": [self.action_view(a.action_id) for a in self._actions.values()],
            "maintenance_windows": [
                {
                    **asdict(w),
                    "starts_at": _iso(w.starts_at),
                    "ends_at": _iso(w.ends_at),
                    "state": w.state.value,
                    "active_now": w.is_active_at(now),
                }
                for w in self._windows.values()
            ],
            "backup_operations": [
                {
                    **asdict(b),
                    "state": b.state.value,
                    "requested_at": _iso(b.requested_at),
                    "completed_at": _iso(b.completed_at),
                }
                for b in self._backups.values()
            ],
            "incidents": [asdict(i) for i in self._incidents.values()],
            "evidence_head": self.journal.head_hash(),
            "evidence_count": len(self.journal),
        }
        scrubbed: dict[str, Any] = json.loads(scrub_text(json.dumps(payload)))
        return scrubbed

    def action_view(self, action_id: str) -> dict[str, Any]:
        action = self.action(action_id)
        result = self.result_of(action_id)
        execution = self.execution_of(action_id)
        return {
            "action_id": action.action_id,
            "request_id": action.request_id,
            "action_type": action.action_type.value,
            "impact": action.impact.value,
            "state": action.state.value,
            "approval_state": action.approval_state.value,
            "execution_state": action.execution_state.value,
            "result_state": action.result_state.value,
            "review_state": action.review_state.value,
            "actor_ref": action.actor_ref,
            "authority_ref": f"{action.authority_ref}@v{action.authority_version}",
            "target_id": action.target_id,
            "target_version": action.target_version,
            "deployment_identity_ref": action.deployment_identity_ref,
            "environment": action.environment.value,
            "scope": action.scope_key,
            "parameters_digest": action.parameters_digest,
            "required_approver_classes": list(action.required_approver_classes),
            "approvals": [
                {
                    "approval_id": a.approval_id,
                    "approver_ref": a.approver_ref,
                    "approver_class": a.approver_class,
                    "state": a.state.value,
                    "expires_at": a.expires_at.isoformat(),
                }
                for a in self.approvals_of(action_id)
            ],
            "execution": None
            if execution is None
            else {
                "execution_id": execution.execution_id,
                "executor_ref": execution.executor_ref,
                "state": execution.state.value,
                "backend_operation_ref": execution.backend_operation_ref,
                "adapter_id": execution.adapter_id,
            },
            "result": None
            if result is None
            else {
                "result_id": result.result_id,
                "state": result.state.value,
                "failure_classification": result.failure_classification.value,
                "detail": result.detail,
                "backend_metadata": dict(result.backend_metadata),
                "redacted_fields": list(result.redacted_fields),
            },
            "requested_at": action.requested_at.isoformat(),
            "expires_at": action.expires_at.isoformat(),
            "incident_ref": action.incident_ref,
            "maintenance_window_ref": action.maintenance_window_ref,
            "evidence_refs": [asdict(r) for r in self.evidence_of(action_id)],
            "purpose": scrub_text(action.purpose),
        }
