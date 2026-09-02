"""CTRL-03 governed credential, trust and key lifecycle reference runtime.

This module controls lifecycle intent and evidence. It never owns or returns
private keys, password equivalents, raw tokens, recovery secrets or provider
secret values. Provider custody remains an explicit external dependency.
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
from epd2_control_plane_service.regional_operations import (
    ActorClass,
    ApproverClass,
    AuthorityDirectory,
    ExactScope,
)


class CredentialClass(StrEnum):
    HUMAN_CREDENTIAL = "HUMAN_CREDENTIAL"
    PASSKEY = "PASSKEY"
    RECOVERY_CREDENTIAL = "RECOVERY_CREDENTIAL"
    SESSION = "SESSION"
    AUTHORITY_PROJECTION = "AUTHORITY_PROJECTION"
    SERVICE_CREDENTIAL = "SERVICE_CREDENTIAL"
    MTLS_CERTIFICATE = "MTLS_CERTIFICATE"
    JWS_SIGNING_KEY = "JWS_SIGNING_KEY"
    JWKS_ENTRY = "JWKS_ENTRY"
    ENCRYPTION_KEY_REFERENCE = "ENCRYPTION_KEY_REFERENCE"
    PROVIDER_SECRET = "PROVIDER_SECRET"
    VOTING_KEY_REFERENCE = "VOTING_KEY_REFERENCE"


class LifecycleState(StrEnum):
    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    PENDING_ACTIVATION = "PENDING_ACTIVATION"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    ROTATING = "ROTATING"
    RETIRED = "RETIRED"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"
    COMPROMISED = "COMPROMISED"
    DISABLED = "DISABLED"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class LifecycleOperation(StrEnum):
    STATUS = "STATUS"
    SUSPEND = "SUSPEND"
    REVOKE = "REVOKE"
    ACTIVATE = "ACTIVATE"
    ROTATE = "ROTATE"
    RETIRE = "RETIRE"
    RECOVER = "RECOVER"
    REBIND = "REBIND"
    REISSUE = "REISSUE"
    CONTAIN_COMPROMISE = "CONTAIN_COMPROMISE"
    TRUST_ADD = "TRUST_ADD"
    TRUST_ACTIVATE = "TRUST_ACTIVATE"
    TRUST_RETRACT = "TRUST_RETRACT"
    EXTERNAL_ACTION_REQUEST = "EXTERNAL_ACTION_REQUEST"


class BreakGlassPhase(StrEnum):
    DECLARED = "DECLARED"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    CONTAINED = "CONTAINED"
    REMEDIATED = "ROTATED_OR_REVOKED"
    VERIFIED = "VERIFIED"
    REVIEWED = "REVIEWED"
    EXPIRED = "EXPIRED"


class AssuranceProfile(StrEnum):
    HUMAN = "HUMAN-AAL2-v1"
    PASSKEY_ES256 = "WEBAUTHN-ES256-v1"
    SERVICE_JWS_ES256 = "SERVICE-JWS-ES256-v1"
    TRUST_ES384 = "TRUST-ES384-v1"
    MTLS = "MTLS-X509-v1"
    ENCRYPTION_AES256_GCM = "ENCRYPTION-AES256-GCM-v1"
    EXTERNAL_VOTING = "EXTERNAL-VOTING-REFERENCE-v1"


class Refusal(StrEnum):
    WRONG_SCOPE = "WRONG_SCOPE"
    WRONG_PURPOSE = "WRONG_CREDENTIAL_PURPOSE"
    WRONG_ALGORITHM = "WRONG_ALGORITHM"
    ALGORITHM_DOWNGRADE = "ALGORITHM_DOWNGRADE"
    TRUST_LOCATION_MISMATCH = "TRUST_LOCATION_MISMATCH"
    STALE_TRUST_SET = "STALE_TRUST_SET"
    STALE_TARGET = "STALE_TARGET"
    STALE_AUTHORITY = "STALE_AUTHORITY"
    STALE_PROVIDER = "STALE_PROVIDER_STATE"
    STALE_CTRL02 = "STALE_CTRL02_STATE"
    SECRET_VISIBILITY = "SECRET_VISIBILITY_FORBIDDEN"
    VOTING_BOUNDARY = "VOTING_KEY_BOUNDARY"
    QUORUM = "QUORUM_NOT_MET"
    SELF_APPROVAL = "SELF_APPROVAL_FORBIDDEN"
    EXECUTION_SEPARATION = "APPROVAL_IS_NOT_EXECUTION"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"
    DEPENDENCY_UNAVAILABLE = "DEPENDENCY_UNAVAILABLE"
    UNSUPPORTED_OPERATION = "UNSUPPORTED_OPERATION"


@dataclass(frozen=True, slots=True)
class AlgorithmRule:
    profile: AssuranceProfile
    algorithm: str
    curve_or_mode: str
    maximum_lifetime: timedelta
    allowed_classes: frozenset[CredentialClass]


ALGORITHM_RULES: Final = {
    AssuranceProfile.PASSKEY_ES256: AlgorithmRule(
        AssuranceProfile.PASSKEY_ES256,
        "ES256",
        "P-256",
        timedelta(days=730),
        frozenset({CredentialClass.PASSKEY}),
    ),
    AssuranceProfile.SERVICE_JWS_ES256: AlgorithmRule(
        AssuranceProfile.SERVICE_JWS_ES256,
        "ES256",
        "P-256",
        timedelta(days=90),
        frozenset({CredentialClass.SERVICE_CREDENTIAL, CredentialClass.JWS_SIGNING_KEY}),
    ),
    AssuranceProfile.TRUST_ES384: AlgorithmRule(
        AssuranceProfile.TRUST_ES384,
        "ES384",
        "P-384",
        timedelta(days=365),
        frozenset({CredentialClass.JWKS_ENTRY, CredentialClass.JWS_SIGNING_KEY}),
    ),
    AssuranceProfile.MTLS: AlgorithmRule(
        AssuranceProfile.MTLS,
        "X509",
        "ECDSA-P384",
        timedelta(days=90),
        frozenset({CredentialClass.MTLS_CERTIFICATE}),
    ),
    AssuranceProfile.ENCRYPTION_AES256_GCM: AlgorithmRule(
        AssuranceProfile.ENCRYPTION_AES256_GCM,
        "A256GCM",
        "AES-256-GCM",
        timedelta(days=365),
        frozenset({CredentialClass.ENCRYPTION_KEY_REFERENCE}),
    ),
    AssuranceProfile.EXTERNAL_VOTING: AlgorithmRule(
        AssuranceProfile.EXTERNAL_VOTING,
        "EXTERNAL",
        "VOTING-DOMAIN-OWNED",
        timedelta(days=1),
        frozenset({CredentialClass.VOTING_KEY_REFERENCE}),
    ),
}
PQ_TRACK_ACTIVE: Final = False
PQ_TRACK: Final = ("ML-KEM-768", "ML-DSA-65")
MAX_ROTATION_OVERLAP: Final = timedelta(hours=24)
MAX_SECRET_JIT: Final = timedelta(minutes=15)
MAX_BREAK_GLASS: Final = timedelta(hours=1)
UNIVERSAL_ADMIN_EXISTS: Final = False
UNIVERSAL_SECRET_READER_EXISTS: Final = False
DIRECT_DB_COUNTS_AS_LIFECYCLE: Final = False
SELF_STATE: Final = "PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED"
MUTATION_FIXTURES_REQUIRED: Final = 44
FREEZE_REJECTS_POST_VALIDATION_CHANGE: Final = True
CTRL01_ACCEPTED_SHA256: Final = "07134db175587a9aa441fe87a811c7cfca6cc8dfbd30006279dd0edb598783b5"
CTRL02_WORKING_SHA256: Final = "f58bafe758f19c0b40d3a525d85d0315052c01bc9ed14eae9973079a4dfb993e"


@dataclass(frozen=True, slots=True)
class LifecycleObject:
    object_id: str
    credential_class: CredentialClass
    purpose: str
    scope: ExactScope
    state: LifecycleState
    version: int
    subject_ref: str
    profile: AssuranceProfile | None = None
    algorithm: str | None = None
    curve_or_mode: str | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    provider_ref: str | None = None
    custody_ref: str | None = None
    public_reference: str | None = None
    trust_location: str | None = None
    trust_version: int | None = None
    parent_id: str | None = None
    compromised: bool = False


@dataclass(frozen=True, slots=True)
class LifecycleApproval:
    actor_id: str
    approver_class: ApproverClass
    authority_id: str
    authority_version: int
    approved_at: datetime


@dataclass(frozen=True, slots=True)
class LifecycleRequest:
    request_id: str
    operation: LifecycleOperation
    target_id: str
    requester_id: str
    requester_authority_id: str
    requester_authority_version: int
    reason: str
    evidence_refs: tuple[str, ...]
    requested_at: datetime
    expires_at: datetime
    expected_target_version: int
    expected_provider_version: int
    expected_ctrl02_revision: int
    expected_trust_version: int | None
    quorum: int
    required_approver_classes: frozenset[ApproverClass]
    state: LifecycleState = LifecycleState.REQUESTED
    approvals: tuple[LifecycleApproval, ...] = ()
    executed_by: str | None = None
    review_ref: str | None = None
    new_object_id: str | None = None
    overlap_until: datetime | None = None


@dataclass(frozen=True, slots=True)
class TrustSetVersion:
    trust_set_id: str
    version: int
    entries: frozenset[str]
    active_from: datetime
    retired_at: datetime | None = None
    previous_version: int | None = None


@dataclass(frozen=True, slots=True)
class SecretAccessGrant:
    grant_id: str
    actor_id: str
    target_ref: str
    capability: str
    scope: ExactScope
    valid_from: datetime
    expires_at: datetime
    approval_refs: tuple[str, ...]
    state: LifecycleState = LifecycleState.ACTIVE
    use_refs: tuple[str, ...] = ()
    review_ref: str | None = None


@dataclass(frozen=True, slots=True)
class RecoveryCeremony:
    ceremony_id: str
    key_reference: str
    participant_ids: tuple[str, ...]
    threshold: int
    previous_threshold: int
    evidence_ref: str
    state: LifecycleState
    created_at: datetime
    completed_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class BreakGlassApproval:
    actor_id: str
    approver_class: ApproverClass
    authority_version: int


@dataclass(frozen=True, slots=True)
class BreakGlassCase:
    case_id: str
    target_id: str
    requester_id: str
    requester_authority_version: int
    scope: ExactScope
    reason: str
    evidence_refs: tuple[str, ...]
    declared_at: datetime
    expires_at: datetime
    phase: BreakGlassPhase = BreakGlassPhase.DECLARED
    approvals: tuple[BreakGlassApproval, ...] = ()
    activated_by: str | None = None
    review_ref: str | None = None


@dataclass(frozen=True, slots=True)
class LifecycleAuditEvent:
    sequence: int
    event_id: str
    actor_id: str
    authority_basis: str
    object_class: str
    target_ref: str
    action: str
    prior_state: str
    new_state: str
    occurred_at: str
    result: str
    reason: str
    approval_refs: tuple[str, ...]
    provider_ref: str | None
    trust_version: int | None
    evidence_correlation: str
    previous_hash: str
    event_hash: str


class ProviderState:
    """Metadata-only view of custody/provider state."""

    def __init__(self) -> None:
        self.available = True
        self.versions: dict[str, int] = {}

    def version(self, target_id: str) -> int:
        if not self.available:
            raise AuthorizationRefused(
                "custody/provider state unavailable", reason_code=Refusal.DEPENDENCY_UNAVAILABLE
            )
        return self.versions.get(target_id, 1)


class Ctrl02State:
    """Explicit adapter for active CTRL-02 restrictions and quarantine state."""

    def __init__(self) -> None:
        self.available = True
        self.revision = 1
        self.restricted_targets: set[str] = set()
        self.quarantined_sessions: set[str] = set()

    def require(self, target_id: str, expected_revision: int) -> None:
        if not self.available:
            raise AuthorizationRefused(
                "CTRL-02 state unavailable", reason_code=Refusal.DEPENDENCY_UNAVAILABLE
            )
        if self.revision != expected_revision:
            raise AuthorizationRefused("CTRL-02 state changed", reason_code=Refusal.STALE_CTRL02)
        if target_id in self.restricted_targets:
            raise AuthorizationRefused(
                "target restricted by CTRL-02", reason_code="CTRL02_RESTRICTED"
            )
        if target_id in self.quarantined_sessions:
            raise AuthorizationRefused(
                "session quarantined by CTRL-02", reason_code="CTRL02_QUARANTINED"
            )


@dataclass(frozen=True, slots=True)
class LifecycleAction:
    action_id: str
    route: str
    credential_class: str
    authority: str
    quorum: int
    secret_visibility: str
    commit_reauthorization: bool
    evidence_output: str


CTRL03_ACTIONS: Final = (
    LifecycleAction(
        "CTRL03.STATUS",
        "/ctrl/v3/lifecycle/{id}",
        "ANY",
        "LIFECYCLE.READ",
        0,
        "NONE",
        False,
        "read_model",
    ),
    LifecycleAction(
        "CTRL03.REQUEST",
        "/ctrl/v3/lifecycle/requests",
        "ANY",
        "LIFECYCLE.REQUEST",
        1,
        "NONE",
        True,
        "request",
    ),
    LifecycleAction(
        "CTRL03.APPROVE",
        "/ctrl/v3/lifecycle/{id}/approve",
        "ANY",
        "LIFECYCLE.APPROVE",
        1,
        "NONE",
        True,
        "approval",
    ),
    LifecycleAction(
        "CTRL03.EXECUTE",
        "/ctrl/v3/lifecycle/{id}/execute",
        "ANY",
        "LIFECYCLE.EXECUTE",
        1,
        "NONE",
        True,
        "execution",
    ),
    LifecycleAction(
        "CTRL03.REVIEW",
        "/ctrl/v3/lifecycle/{id}/review",
        "ANY",
        "LIFECYCLE.REVIEW",
        1,
        "NONE",
        True,
        "review",
    ),
    LifecycleAction(
        "CTRL03.HUMAN.RECOVER",
        "/ctrl/v3/human/{id}/recover",
        "HUMAN_CREDENTIAL",
        "LIFECYCLE.REQUEST",
        2,
        "NONE",
        True,
        "recovery",
    ),
    LifecycleAction(
        "CTRL03.PASSKEY.REVOKE",
        "/ctrl/v3/passkeys/{id}/revoke",
        "PASSKEY",
        "LIFECYCLE.REQUEST",
        1,
        "NONE",
        True,
        "revocation",
    ),
    LifecycleAction(
        "CTRL03.SESSION.REVOKE",
        "/ctrl/v3/sessions/{id}/revoke",
        "SESSION",
        "LIFECYCLE.REQUEST",
        1,
        "NONE",
        True,
        "revocation",
    ),
    LifecycleAction(
        "CTRL03.SERVICE.ROTATE",
        "/ctrl/v3/service/{id}/rotate",
        "SERVICE_CREDENTIAL",
        "LIFECYCLE.REQUEST",
        2,
        "NONE",
        True,
        "rotation",
    ),
    LifecycleAction(
        "CTRL03.MTLS.REISSUE",
        "/ctrl/v3/mtls/{id}/reissue",
        "MTLS_CERTIFICATE",
        "LIFECYCLE.REQUEST",
        2,
        "NONE",
        True,
        "reissue",
    ),
    LifecycleAction(
        "CTRL03.JWS.ROLLOVER",
        "/ctrl/v3/jws/{id}/rollover",
        "JWS_SIGNING_KEY",
        "LIFECYCLE.REQUEST",
        2,
        "NONE",
        True,
        "rotation",
    ),
    LifecycleAction(
        "CTRL03.JWKS.UPDATE",
        "/ctrl/v3/trust-sets/{id}/versions",
        "JWKS_ENTRY",
        "LIFECYCLE.REQUEST",
        2,
        "NONE",
        True,
        "trust_version",
    ),
    LifecycleAction(
        "CTRL03.ENCRYPTION.ROTATE",
        "/ctrl/v3/encryption/{id}/rotate",
        "ENCRYPTION_KEY_REFERENCE",
        "LIFECYCLE.REQUEST",
        2,
        "NONE",
        True,
        "rotation_request",
    ),
    LifecycleAction(
        "CTRL03.PROVIDER.CONTAIN",
        "/ctrl/v3/provider-secrets/{id}/contain",
        "PROVIDER_SECRET",
        "LIFECYCLE.REQUEST",
        2,
        "NONE",
        True,
        "containment",
    ),
    LifecycleAction(
        "CTRL03.VOTING.REQUEST",
        "/ctrl/v3/voting-key-refs/{id}/requests",
        "VOTING_KEY_REFERENCE",
        "LIFECYCLE.REQUEST",
        2,
        "NONE",
        True,
        "external_request",
    ),
    LifecycleAction(
        "CTRL03.SECRET.JIT",
        "/ctrl/v3/secret-access",
        "REFERENCE_ONLY",
        "SECRET.ACCESS_REQUEST",
        2,
        "EXPLICIT_JIT",
        True,
        "access_session",
    ),
    LifecycleAction(
        "CTRL03.COMPROMISE",
        "/ctrl/v3/compromise/{id}/contain",
        "ANY",
        "LIFECYCLE.REQUEST",
        2,
        "NONE",
        True,
        "incident",
    ),
    LifecycleAction(
        "CTRL03.TRUST.RECOVER",
        "/ctrl/v3/trust/recovery",
        "JWKS_ENTRY",
        "TRUST.RECOVER",
        3,
        "NONE",
        True,
        "ceremony",
    ),
)


class CredentialLifecycleService:
    def __init__(
        self,
        authorities: AuthorityDirectory,
        provider: ProviderState | None = None,
        ctrl02: Ctrl02State | None = None,
    ) -> None:
        self.authorities = authorities
        self.provider = provider or ProviderState()
        self.ctrl02 = ctrl02 or Ctrl02State()
        self._objects: dict[str, LifecycleObject] = {}
        self._requests: dict[str, LifecycleRequest] = {}
        self._trust_sets: dict[str, list[TrustSetVersion]] = {}
        self._secret_grants: dict[str, SecretAccessGrant] = {}
        self._ceremonies: dict[str, RecoveryCeremony] = {}
        self._break_glass: dict[str, BreakGlassCase] = {}
        self._events: list[LifecycleAuditEvent] = []
        self._idempotency: dict[tuple[str, str], tuple[str, str]] = {}
        self._last_time = datetime.min.replace(tzinfo=UTC)
        self._lock = threading.RLock()

    @property
    def objects(self) -> tuple[LifecycleObject, ...]:
        return tuple(self._objects.values())

    @property
    def requests(self) -> tuple[LifecycleRequest, ...]:
        return tuple(self._requests.values())

    @property
    def events(self) -> tuple[LifecycleAuditEvent, ...]:
        return tuple(self._events)

    @property
    def secret_grants(self) -> tuple[SecretAccessGrant, ...]:
        return tuple(self._secret_grants.values())

    @property
    def ceremonies(self) -> tuple[RecoveryCeremony, ...]:
        return tuple(self._ceremonies.values())

    def _time(self, supplied: datetime) -> datetime:
        if supplied.tzinfo is None:
            raise ValueError("server time must be timezone-aware")
        if supplied < self._last_time:
            return self._last_time
        self._last_time = supplied
        return supplied

    @staticmethod
    def _safe_text(value: str, label: str) -> str:
        forbidden = ("PRIVATE KEY", "password=", "token=", "secret=", "recovery_code=")
        if any(item.lower() in value.lower() for item in forbidden):
            raise AuthorizationRefused(
                f"{label} contains secret material", reason_code=Refusal.SECRET_VISIBILITY
            )
        return value

    def register(self, item: LifecycleObject) -> LifecycleObject:
        with self._lock:
            if item.object_id in self._objects:
                raise AuthorizationRefused("object exists", reason_code="DUPLICATE_OBJECT")
            self._safe_text(item.subject_ref, "subject_ref")
            if item.credential_class is CredentialClass.VOTING_KEY_REFERENCE and (
                item.custody_ref or item.provider_ref
            ):
                raise AuthorizationRefused(
                    "voting key custody cannot enter generic CTRL",
                    reason_code=Refusal.VOTING_BOUNDARY,
                )
            if item.profile is not None:
                self._validate_profile(item)
            if item.valid_until is not None and item.valid_from is not None:
                rule = ALGORITHM_RULES.get(item.profile) if item.profile else None
                if item.valid_until <= item.valid_from or (
                    rule and item.valid_until - item.valid_from > rule.maximum_lifetime
                ):
                    raise AuthorizationRefused("cryptoperiod exceeded", reason_code=Refusal.EXPIRED)
            self._objects[item.object_id] = item
            self.provider.versions.setdefault(item.object_id, 1)
            return item

    def request_regional_issuance(
        self,
        item: LifecycleObject,
        *,
        issuer_scope: ExactScope,
        root_hot_path: bool,
    ) -> LifecycleObject:
        """Register bounded regional issuance without central-root hot-path use."""
        if item.scope != issuer_scope:
            raise AuthorizationRefused("cross-region issuance", reason_code=Refusal.WRONG_SCOPE)
        if root_hot_path:
            raise AuthorizationRefused("root hot path forbidden", reason_code="ROOT_HOT_PATH")
        if item.credential_class not in {
            CredentialClass.SERVICE_CREDENTIAL,
            CredentialClass.MTLS_CERTIFICATE,
            CredentialClass.JWS_SIGNING_KEY,
        }:
            raise AuthorizationRefused("issuer purpose mismatch", reason_code=Refusal.WRONG_PURPOSE)
        return self.register(item)

    def declare_break_glass(
        self,
        *,
        case_id: str,
        target_id: str,
        requester_id: str,
        reason: str,
        evidence_refs: Iterable[str],
        now: datetime,
        expires_at: datetime,
    ) -> BreakGlassCase:
        moment = self._time(now)
        item = self._require_object(target_id)
        evidence = tuple(evidence_refs)
        if (
            not reason.strip()
            or not evidence
            or expires_at <= moment
            or expires_at - moment > MAX_BREAK_GLASS
        ):
            raise AuthorizationRefused("invalid break-glass declaration", reason_code="BREAK_GLASS")
        authority = self.authorities.require(
            actor_id=requester_id,
            capability="LIFECYCLE.REQUEST",
            scope=item.scope,
            now=moment,
            actor_class=ActorClass.HUMAN,
        )
        case = BreakGlassCase(
            case_id=case_id,
            target_id=target_id,
            requester_id=requester_id,
            requester_authority_version=authority.version,
            scope=item.scope,
            reason=self._safe_text(reason, "break-glass reason"),
            evidence_refs=evidence,
            declared_at=moment,
            expires_at=expires_at,
        )
        self._break_glass[case_id] = case
        return case

    def approve_break_glass(
        self,
        case_id: str,
        *,
        approver_id: str,
        approver_class: ApproverClass,
        now: datetime,
    ) -> BreakGlassCase:
        moment = self._time(now)
        case = self._break_glass[case_id]
        if moment >= case.expires_at or case.phase not in {
            BreakGlassPhase.DECLARED,
            BreakGlassPhase.APPROVED,
        }:
            raise AuthorizationRefused("break-glass not approvable", reason_code="WRONG_STATE")
        if approver_id == case.requester_id or approver_id in {
            approval.actor_id for approval in case.approvals
        }:
            raise AuthorizationRefused(
                "independent approval required", reason_code=Refusal.SELF_APPROVAL
            )
        authority = self.authorities.require(
            actor_id=approver_id,
            capability="LIFECYCLE.APPROVE",
            scope=case.scope,
            now=moment,
            actor_class=ActorClass.HUMAN,
            approver_class=approver_class,
        )
        approvals = (
            *case.approvals,
            BreakGlassApproval(approver_id, approver_class, authority.version),
        )
        classes = {approval.approver_class for approval in approvals}
        approved = (
            len(approvals) >= 2
            and {ApproverClass.SECURITY, ApproverClass.TRUST_CUSTODIAN} <= classes
        )
        updated = replace(
            case,
            approvals=approvals,
            phase=BreakGlassPhase.APPROVED if approved else BreakGlassPhase.DECLARED,
        )
        self._break_glass[case_id] = updated
        return updated

    def activate_break_glass(
        self, case_id: str, *, custodian_id: str, now: datetime
    ) -> BreakGlassCase:
        moment = self._time(now)
        case = self._break_glass[case_id]
        if case.phase is not BreakGlassPhase.APPROVED or moment >= case.expires_at:
            raise AuthorizationRefused("break-glass quorum/TTL invalid", reason_code=Refusal.QUORUM)
        if custodian_id in {case.requester_id, *(item.actor_id for item in case.approvals)}:
            raise AuthorizationRefused(
                "approval is not emergency execution", reason_code=Refusal.EXECUTION_SEPARATION
            )
        self.authorities.require(
            actor_id=case.requester_id,
            capability="LIFECYCLE.REQUEST",
            scope=case.scope,
            now=moment,
            expected_version=case.requester_authority_version,
        )
        for approval in case.approvals:
            self.authorities.require(
                actor_id=approval.actor_id,
                capability="LIFECYCLE.APPROVE",
                scope=case.scope,
                now=moment,
                expected_version=approval.authority_version,
                approver_class=approval.approver_class,
            )
        self.authorities.require(
            actor_id=custodian_id,
            capability="LIFECYCLE.EXECUTE",
            scope=case.scope,
            now=moment,
        )
        self.ctrl02.require(case.target_id, self.ctrl02.revision)
        updated = replace(case, phase=BreakGlassPhase.ACTIVE, activated_by=custodian_id)
        self._break_glass[case_id] = updated
        return updated

    def advance_break_glass(
        self, case_id: str, *, next_phase: BreakGlassPhase, now: datetime
    ) -> BreakGlassCase:
        case = self._break_glass[case_id]
        moment = self._time(now)
        transitions = {
            BreakGlassPhase.ACTIVE: BreakGlassPhase.CONTAINED,
            BreakGlassPhase.CONTAINED: BreakGlassPhase.REMEDIATED,
            BreakGlassPhase.REMEDIATED: BreakGlassPhase.VERIFIED,
        }
        if moment >= case.expires_at or transitions.get(case.phase) is not next_phase:
            raise AuthorizationRefused("break-glass sequence invalid", reason_code="WRONG_STATE")
        updated = replace(case, phase=next_phase)
        self._break_glass[case_id] = updated
        return updated

    def review_break_glass(
        self, case_id: str, *, reviewer_id: str, review_ref: str
    ) -> BreakGlassCase:
        case = self._break_glass[case_id]
        participants = {
            case.requester_id,
            case.activated_by,
            *(approval.actor_id for approval in case.approvals),
        }
        if case.phase is not BreakGlassPhase.VERIFIED or reviewer_id in participants:
            raise AuthorizationRefused("independent review required", reason_code="SELF_REVIEW")
        updated = replace(case, phase=BreakGlassPhase.REVIEWED, review_ref=review_ref)
        self._break_glass[case_id] = updated
        return updated

    @staticmethod
    def _validate_profile(item: LifecycleObject) -> None:
        if item.profile is None:
            return
        rule = ALGORITHM_RULES[item.profile]
        if item.credential_class not in rule.allowed_classes:
            raise AuthorizationRefused(
                "profile purpose mismatch", reason_code=Refusal.WRONG_PURPOSE
            )
        if item.algorithm in {None, "none", "NONE"} or item.algorithm != rule.algorithm:
            raise AuthorizationRefused(
                "algorithm profile mismatch", reason_code=Refusal.WRONG_ALGORITHM
            )
        if item.curve_or_mode != rule.curve_or_mode:
            raise AuthorizationRefused(
                "key/algorithm mismatch", reason_code=Refusal.WRONG_ALGORITHM
            )
        if not PQ_TRACK_ACTIVE and any(
            value in {"ML-KEM-768", "ML-DSA-65"} for value in (item.algorithm, item.curve_or_mode)
        ):
            raise AuthorizationRefused(
                "PQ track is inactive", reason_code=Refusal.ALGORITHM_DOWNGRADE
            )

    @staticmethod
    def _operation_allowed(item: LifecycleObject, operation: LifecycleOperation) -> bool:
        common = {
            LifecycleOperation.STATUS,
            LifecycleOperation.SUSPEND,
            LifecycleOperation.REVOKE,
            LifecycleOperation.ACTIVATE,
            LifecycleOperation.CONTAIN_COMPROMISE,
        }
        by_class = {
            CredentialClass.HUMAN_CREDENTIAL: common
            | {LifecycleOperation.RECOVER, LifecycleOperation.REBIND},
            CredentialClass.PASSKEY: common
            | {LifecycleOperation.RECOVER, LifecycleOperation.REBIND},
            CredentialClass.RECOVERY_CREDENTIAL: common | {LifecycleOperation.REISSUE},
            CredentialClass.SESSION: common,
            CredentialClass.AUTHORITY_PROJECTION: common | {LifecycleOperation.REISSUE},
            CredentialClass.SERVICE_CREDENTIAL: common
            | {LifecycleOperation.ROTATE, LifecycleOperation.REISSUE},
            CredentialClass.MTLS_CERTIFICATE: common
            | {LifecycleOperation.ROTATE, LifecycleOperation.REISSUE},
            CredentialClass.JWS_SIGNING_KEY: common
            | {LifecycleOperation.ROTATE, LifecycleOperation.RETIRE},
            CredentialClass.JWKS_ENTRY: common
            | {
                LifecycleOperation.TRUST_ADD,
                LifecycleOperation.TRUST_ACTIVATE,
                LifecycleOperation.TRUST_RETRACT,
            },
            CredentialClass.ENCRYPTION_KEY_REFERENCE: common | {LifecycleOperation.ROTATE},
            CredentialClass.PROVIDER_SECRET: {
                LifecycleOperation.STATUS,
                LifecycleOperation.REVOKE,
                LifecycleOperation.ROTATE,
                LifecycleOperation.CONTAIN_COMPROMISE,
            },
            CredentialClass.VOTING_KEY_REFERENCE: {
                LifecycleOperation.STATUS,
                LifecycleOperation.EXTERNAL_ACTION_REQUEST,
            },
        }
        return operation in by_class[item.credential_class]

    @staticmethod
    def _approval_requirements(
        item: LifecycleObject, operation: LifecycleOperation
    ) -> tuple[int, frozenset[ApproverClass]]:
        high_impact = item.credential_class in {
            CredentialClass.JWS_SIGNING_KEY,
            CredentialClass.JWKS_ENTRY,
            CredentialClass.ENCRYPTION_KEY_REFERENCE,
            CredentialClass.PROVIDER_SECRET,
            CredentialClass.VOTING_KEY_REFERENCE,
        } or operation in {LifecycleOperation.RECOVER, LifecycleOperation.CONTAIN_COMPROMISE}
        if high_impact:
            return 2, frozenset({ApproverClass.SECURITY, ApproverClass.TRUST_CUSTODIAN})
        return 1, frozenset({ApproverClass.SECURITY})

    def _once(
        self, action: str, key: str, payload: Mapping[str, Any], result_id: str
    ) -> str | None:
        digest = hashlib.sha256(
            json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode()
        ).hexdigest()
        previous = self._idempotency.get((action, key))
        if previous is None:
            self._idempotency[(action, key)] = (digest, result_id)
            return None
        if previous[0] != digest:
            raise AuthorizationRefused("idempotency conflict", reason_code="IDEMPOTENCY_CONFLICT")
        return previous[1]

    def request_operation(
        self,
        *,
        request_id: str,
        operation: LifecycleOperation,
        target_id: str,
        requester_id: str,
        reason: str,
        evidence_refs: Iterable[str],
        now: datetime,
        expires_at: datetime,
        idempotency_key: str,
        new_object_id: str | None = None,
        overlap_until: datetime | None = None,
    ) -> LifecycleRequest:
        with self._lock:
            moment = self._time(now)
            item = self._require_object(target_id)
            prior = self._once(
                "request",
                idempotency_key,
                {"request": request_id, "operation": operation, "target": target_id},
                request_id,
            )
            if prior is not None:
                return self._requests[prior]
            if not self._operation_allowed(item, operation):
                reason_code = (
                    Refusal.VOTING_BOUNDARY
                    if item.credential_class is CredentialClass.VOTING_KEY_REFERENCE
                    else Refusal.UNSUPPORTED_OPERATION
                )
                raise AuthorizationRefused(
                    "operation is outside class boundary", reason_code=reason_code
                )
            if not reason.strip() or not tuple(evidence_refs):
                raise AuthorizationRefused(
                    "reason and evidence required", reason_code="EVIDENCE_REQUIRED"
                )
            if expires_at <= moment:
                raise AuthorizationRefused("request expired", reason_code=Refusal.EXPIRED)
            if operation is LifecycleOperation.ROTATE:
                if new_object_id is None or new_object_id == target_id:
                    raise AuthorizationRefused(
                        "rotation needs linked new identity", reason_code="ROTATION_LINK"
                    )
                if (
                    overlap_until is None
                    or overlap_until <= moment
                    or overlap_until - moment > MAX_ROTATION_OVERLAP
                ):
                    raise AuthorizationRefused(
                        "rotation overlap invalid", reason_code="ROTATION_OVERLAP"
                    )
            authority = self.authorities.require(
                actor_id=requester_id,
                capability="LIFECYCLE.REQUEST",
                scope=item.scope,
                now=moment,
                actor_class=ActorClass.HUMAN,
            )
            quorum, classes = self._approval_requirements(item, operation)
            request = LifecycleRequest(
                request_id=request_id,
                operation=operation,
                target_id=target_id,
                requester_id=requester_id,
                requester_authority_id=authority.grant_id,
                requester_authority_version=authority.version,
                reason=self._safe_text(reason, "reason"),
                evidence_refs=tuple(evidence_refs),
                requested_at=moment,
                expires_at=expires_at,
                expected_target_version=item.version,
                expected_provider_version=self.provider.version(target_id),
                expected_ctrl02_revision=self.ctrl02.revision,
                expected_trust_version=item.trust_version,
                quorum=quorum,
                required_approver_classes=classes,
                new_object_id=new_object_id,
                overlap_until=overlap_until,
            )
            self._requests[request_id] = request
            self._record(
                actor=requester_id,
                authority=authority.grant_id,
                item=item,
                action=f"REQUEST_{operation.value}",
                prior=item.state,
                new=item.state,
                now=moment,
                result="REQUESTED",
                reason=reason,
                approvals=(),
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
    ) -> LifecycleRequest:
        with self._lock:
            moment = self._time(now)
            request = self._require_request(request_id)
            item = self._require_object(request.target_id)
            prior = self._once(
                "approve",
                idempotency_key,
                {"request": request_id, "approver": approver_id, "class": approver_class},
                request_id,
            )
            if prior is not None:
                return self._requests[prior]
            if request.state not in {LifecycleState.REQUESTED, LifecycleState.PENDING_ACTIVATION}:
                raise AuthorizationRefused("request not approvable", reason_code="WRONG_STATE")
            if approver_id == request.requester_id or approver_id in {
                approval.actor_id for approval in request.approvals
            }:
                raise AuthorizationRefused(
                    "self or duplicate approval", reason_code=Refusal.SELF_APPROVAL
                )
            authority = self.authorities.require(
                actor_id=approver_id,
                capability="LIFECYCLE.APPROVE",
                scope=item.scope,
                now=moment,
                actor_class=ActorClass.HUMAN,
                approver_class=approver_class,
            )
            approval = LifecycleApproval(
                approver_id, approver_class, authority.grant_id, authority.version, moment
            )
            approvals = (*request.approvals, approval)
            classes = {value.approver_class for value in approvals}
            state = (
                LifecycleState.APPROVED
                if len(approvals) >= request.quorum and request.required_approver_classes <= classes
                else LifecycleState.PENDING_ACTIVATION
            )
            updated = replace(request, approvals=approvals, state=state)
            self._requests[request_id] = updated
            return updated

    def _reauthorize(self, request: LifecycleRequest, custodian_id: str, now: datetime) -> str:
        item = self._require_object(request.target_id)
        if item.version != request.expected_target_version:
            raise AuthorizationRefused("target changed", reason_code=Refusal.STALE_TARGET)
        if self.provider.version(item.object_id) != request.expected_provider_version:
            raise AuthorizationRefused("provider drift", reason_code=Refusal.STALE_PROVIDER)
        if item.trust_version != request.expected_trust_version:
            raise AuthorizationRefused("trust version changed", reason_code=Refusal.STALE_TRUST_SET)
        self.ctrl02.require(item.object_id, request.expected_ctrl02_revision)
        self.authorities.require(
            actor_id=request.requester_id,
            capability="LIFECYCLE.REQUEST",
            scope=item.scope,
            now=now,
            expected_version=request.requester_authority_version,
        )
        for approval in request.approvals:
            self.authorities.require(
                actor_id=approval.actor_id,
                capability="LIFECYCLE.APPROVE",
                scope=item.scope,
                now=now,
                expected_version=approval.authority_version,
                approver_class=approval.approver_class,
            )
        execution = self.authorities.require(
            actor_id=custodian_id,
            capability="LIFECYCLE.EXECUTE",
            scope=item.scope,
            now=now,
        )
        return execution.grant_id

    def execute(
        self,
        request_id: str,
        *,
        custodian_id: str,
        now: datetime,
        idempotency_key: str,
    ) -> LifecycleObject:
        with self._lock:
            moment = self._time(now)
            request = self._require_request(request_id)
            item = self._require_object(request.target_id)
            previous = self._idempotency.get(("execute", idempotency_key))
            if previous is not None:
                return self._objects[previous[1]]
            if request.state is not LifecycleState.APPROVED:
                raise AuthorizationRefused("quorum not met", reason_code=Refusal.QUORUM)
            if custodian_id in {request.requester_id, *(a.actor_id for a in request.approvals)}:
                raise AuthorizationRefused(
                    "approval is not custody execution", reason_code=Refusal.EXECUTION_SEPARATION
                )
            if moment >= request.expires_at:
                raise AuthorizationRefused("request expired", reason_code=Refusal.EXPIRED)
            authority_ref = self._reauthorize(request, custodian_id, moment)
            self._once(
                "execute",
                idempotency_key,
                {"request": request_id, "custodian": custodian_id},
                item.object_id,
            )
            updated = self._apply(item, request, moment)
            self._objects[item.object_id] = updated
            self._requests[request_id] = replace(
                request, state=LifecycleState.COMPLETED, executed_by=custodian_id
            )
            self.provider.versions[item.object_id] = request.expected_provider_version + 1
            self._record(
                actor=custodian_id,
                authority=authority_ref,
                item=updated,
                action=request.operation,
                prior=item.state,
                new=updated.state,
                now=moment,
                result="COMPLETED",
                reason=request.reason,
                approvals=tuple(value.authority_id for value in request.approvals),
                correlation=request.request_id,
            )
            return updated

    def _apply(
        self, item: LifecycleObject, request: LifecycleRequest, now: datetime
    ) -> LifecycleObject:
        operation = request.operation
        states = {
            LifecycleOperation.SUSPEND: LifecycleState.SUSPENDED,
            LifecycleOperation.REVOKE: LifecycleState.REVOKED,
            LifecycleOperation.ACTIVATE: LifecycleState.ACTIVE,
            LifecycleOperation.RETIRE: LifecycleState.RETIRED,
            LifecycleOperation.CONTAIN_COMPROMISE: LifecycleState.COMPROMISED,
            LifecycleOperation.RECOVER: LifecycleState.REVOKED,
            LifecycleOperation.REBIND: LifecycleState.REVOKED,
            LifecycleOperation.REISSUE: LifecycleState.REVOKED,
            LifecycleOperation.TRUST_RETRACT: LifecycleState.RETIRED,
            LifecycleOperation.EXTERNAL_ACTION_REQUEST: item.state,
        }
        if operation is LifecycleOperation.ROTATE:
            if request.new_object_id is None or request.overlap_until is None:
                raise AuthorizationRefused("rotation link missing", reason_code="ROTATION_LINK")
            replacement = self._require_object(request.new_object_id)
            if (
                replacement.credential_class is not item.credential_class
                or replacement.scope != item.scope
            ):
                raise AuthorizationRefused(
                    "rotation purpose mismatch", reason_code=Refusal.WRONG_PURPOSE
                )
            if replacement.parent_id != item.object_id:
                raise AuthorizationRefused("old/new linkage missing", reason_code="ROTATION_LINK")
            self._validate_profile(replacement)
            self._objects[replacement.object_id] = replace(
                replacement, state=LifecycleState.ACTIVE, version=replacement.version + 1
            )
            return replace(item, state=LifecycleState.ROTATING, version=item.version + 1)
        state = states.get(operation, item.state)
        compromised = item.compromised or operation is LifecycleOperation.CONTAIN_COMPROMISE
        updated = replace(item, state=state, compromised=compromised, version=item.version + 1)
        if operation in {
            LifecycleOperation.REVOKE,
            LifecycleOperation.RECOVER,
            LifecycleOperation.REBIND,
        } and item.credential_class in {
            CredentialClass.HUMAN_CREDENTIAL,
            CredentialClass.PASSKEY,
            CredentialClass.RECOVERY_CREDENTIAL,
        }:
            self._invalidate_subject_sessions(item.subject_ref, now)
        return updated

    def _invalidate_subject_sessions(self, subject_ref: str, now: datetime) -> None:
        for object_id, value in tuple(self._objects.items()):
            if (
                value.credential_class is CredentialClass.SESSION
                and value.subject_ref == subject_ref
                and value.state is LifecycleState.ACTIVE
            ):
                self._objects[object_id] = replace(
                    value, state=LifecycleState.REVOKED, version=value.version + 1
                )

    def publish_trust_version(
        self,
        *,
        trust_set_id: str,
        entries: Iterable[str],
        now: datetime,
        previous_version: int | None,
    ) -> TrustSetVersion:
        with self._lock:
            moment = self._time(now)
            values = frozenset(entries)
            if not values:
                raise AuthorizationRefused(
                    "empty trust set", reason_code=Refusal.TRUST_LOCATION_MISMATCH
                )
            history = self._trust_sets.setdefault(trust_set_id, [])
            actual_previous = history[-1].version if history else None
            if previous_version != actual_previous:
                raise AuthorizationRefused("stale trust set", reason_code=Refusal.STALE_TRUST_SET)
            version = TrustSetVersion(
                trust_set_id=trust_set_id,
                version=(actual_previous or 0) + 1,
                entries=values,
                active_from=moment,
                previous_version=actual_previous,
            )
            history.append(version)
            return version

    def validate_assertion(
        self,
        object_id: str,
        *,
        expected_purpose: str,
        expected_scope: ExactScope,
        trusted_locations: frozenset[str],
        minimum_trust_version: int,
        now: datetime,
    ) -> bool:
        moment = self._time(now)
        item = self._require_object(object_id)
        self._validate_profile(item)
        if item.purpose != expected_purpose:
            raise AuthorizationRefused("cross-purpose reuse", reason_code=Refusal.WRONG_PURPOSE)
        if item.scope != expected_scope:
            raise AuthorizationRefused("cross-region use", reason_code=Refusal.WRONG_SCOPE)
        if item.state is not LifecycleState.ACTIVE or item.compromised:
            raise AuthorizationRefused("credential revoked", reason_code=Refusal.REVOKED)
        if item.valid_until is None or moment >= item.valid_until:
            raise AuthorizationRefused("credential expired", reason_code=Refusal.EXPIRED)
        if item.trust_location not in trusted_locations:
            raise AuthorizationRefused(
                "trust location is not governed", reason_code=Refusal.TRUST_LOCATION_MISMATCH
            )
        if item.trust_version is None or item.trust_version < minimum_trust_version:
            raise AuthorizationRefused("stale trust version", reason_code=Refusal.STALE_TRUST_SET)
        return True

    def grant_secret_access(
        self,
        *,
        grant_id: str,
        actor_id: str,
        target_ref: str,
        capability: str,
        scope: ExactScope,
        now: datetime,
        expires_at: datetime,
        approval_refs: Iterable[str],
    ) -> SecretAccessGrant:
        moment = self._time(now)
        approvals = tuple(dict.fromkeys(approval_refs))
        if (
            expires_at <= moment
            or expires_at - moment > MAX_SECRET_JIT
            or len(approvals) < 2
            or capability != "SECRET.USE_IN_CUSTODY_SESSION"
        ):
            raise AuthorizationRefused("secret JIT boundary", reason_code=Refusal.SECRET_VISIBILITY)
        grant = SecretAccessGrant(
            grant_id=grant_id,
            actor_id=actor_id,
            target_ref=target_ref,
            capability=capability,
            scope=scope,
            valid_from=moment,
            expires_at=expires_at,
            approval_refs=approvals,
        )
        self._secret_grants[grant_id] = grant
        return grant

    def use_secret_access(
        self, grant_id: str, *, actor_id: str, now: datetime, use_ref: str
    ) -> str:
        moment = self._time(now)
        grant = self._secret_grants[grant_id]
        if (
            grant.actor_id != actor_id
            or grant.state is not LifecycleState.ACTIVE
            or moment >= grant.expires_at
        ):
            raise AuthorizationRefused("secret access expired", reason_code=Refusal.EXPIRED)
        self._secret_grants[grant_id] = replace(grant, use_refs=(*grant.use_refs, use_ref))
        return f"custody-session:{grant_id}"

    def review_secret_access(self, grant_id: str, *, reviewer_id: str, review_ref: str) -> None:
        grant = self._secret_grants[grant_id]
        if grant.state not in {LifecycleState.EXPIRED, LifecycleState.REVOKED}:
            raise AuthorizationRefused("review follows expiry/revoke", reason_code="WRONG_STATE")
        if reviewer_id == grant.actor_id:
            raise AuthorizationRefused("independent review required", reason_code="SELF_REVIEW")
        self._secret_grants[grant_id] = replace(grant, review_ref=review_ref)

    def begin_recovery_ceremony(
        self,
        *,
        ceremony_id: str,
        key_reference: str,
        participant_ids: Iterable[str],
        threshold: int,
        previous_threshold: int,
        evidence_ref: str,
        now: datetime,
    ) -> RecoveryCeremony:
        participants = tuple(dict.fromkeys(participant_ids))
        if key_reference.startswith("voting:"):
            raise AuthorizationRefused(
                "voting recovery remains external", reason_code=Refusal.VOTING_BOUNDARY
            )
        if (
            len(participants) < 3
            or threshold < previous_threshold
            or threshold < 2
            or threshold > len(participants)
        ):
            raise AuthorizationRefused("recovery quorum weakened", reason_code=Refusal.QUORUM)
        ceremony = RecoveryCeremony(
            ceremony_id=ceremony_id,
            key_reference=key_reference,
            participant_ids=participants,
            threshold=threshold,
            previous_threshold=previous_threshold,
            evidence_ref=evidence_ref,
            state=LifecycleState.REQUESTED,
            created_at=self._time(now),
        )
        self._ceremonies[ceremony_id] = ceremony
        return ceremony

    def complete_recovery_ceremony(
        self, ceremony_id: str, *, approving_participants: Iterable[str], now: datetime
    ) -> RecoveryCeremony:
        ceremony = self._ceremonies[ceremony_id]
        approvals = set(approving_participants)
        if len(approvals) < ceremony.threshold or not approvals <= set(ceremony.participant_ids):
            raise AuthorizationRefused("recovery quorum not met", reason_code=Refusal.QUORUM)
        updated = replace(
            ceremony,
            state=LifecycleState.COMPLETED,
            completed_at=self._time(now),
        )
        self._ceremonies[ceremony_id] = updated
        return updated

    def expire_due(self, now: datetime) -> tuple[str, ...]:
        moment = self._time(now)
        expired: list[str] = []
        for object_id, item in tuple(self._objects.items()):
            if (
                item.state is LifecycleState.ACTIVE
                and item.valid_until is not None
                and moment >= item.valid_until
            ):
                self._objects[object_id] = replace(
                    item, state=LifecycleState.EXPIRED, version=item.version + 1
                )
                expired.append(object_id)
        for grant_id, grant in tuple(self._secret_grants.items()):
            if grant.state is LifecycleState.ACTIVE and moment >= grant.expires_at:
                self._secret_grants[grant_id] = replace(grant, state=LifecycleState.EXPIRED)
                expired.append(grant_id)
        for case_id, case in tuple(self._break_glass.items()):
            if case.phase not in {BreakGlassPhase.REVIEWED, BreakGlassPhase.EXPIRED} and (
                moment >= case.expires_at
            ):
                self._break_glass[case_id] = replace(case, phase=BreakGlassPhase.EXPIRED)
                expired.append(case_id)
        return tuple(expired)

    def post_review(self, request_id: str, *, reviewer_id: str, review_ref: str) -> None:
        request = self._require_request(request_id)
        participants = {
            request.requester_id,
            request.executed_by,
            *(approval.actor_id for approval in request.approvals),
        }
        if reviewer_id in participants or request.state is not LifecycleState.COMPLETED:
            raise AuthorizationRefused(
                "independent post-use review required", reason_code="SELF_REVIEW"
            )
        self._requests[request_id] = replace(request, review_ref=review_ref)

    def safe_read_model(self) -> list[dict[str, Any]]:
        fields = (
            "object_id",
            "credential_class",
            "purpose",
            "scope",
            "state",
            "version",
            "profile",
            "algorithm",
            "valid_until",
            "public_reference",
            "trust_location",
            "trust_version",
            "compromised",
        )
        return [
            {field: getattr(item, field) for field in fields} for item in self._objects.values()
        ]

    def checkpoint(self) -> dict[str, Any]:
        return {
            "objects": {key: asdict(value) for key, value in self._objects.items()},
            "requests": {key: asdict(value) for key, value in self._requests.items()},
            "trust_sets": {
                key: [asdict(value) for value in values] for key, values in self._trust_sets.items()
            },
            "secret_grants": {key: asdict(value) for key, value in self._secret_grants.items()},
            "ceremonies": {key: asdict(value) for key, value in self._ceremonies.items()},
            "break_glass": {key: asdict(value) for key, value in self._break_glass.items()},
            "events": [asdict(value) for value in self._events],
            "last_time": self._last_time.isoformat(),
        }

    def _record(
        self,
        *,
        actor: str,
        authority: str,
        item: LifecycleObject,
        action: str | LifecycleOperation,
        prior: str | LifecycleState,
        new: str | LifecycleState,
        now: datetime,
        result: str,
        reason: str,
        approvals: tuple[str, ...],
        correlation: str,
    ) -> LifecycleAuditEvent:
        payload: dict[str, Any] = {
            "sequence": len(self._events) + 1,
            "actor_id": actor,
            "authority_basis": authority,
            "object_class": item.credential_class.value,
            "target_ref": item.object_id,
            "action": str(action),
            "prior_state": str(prior),
            "new_state": str(new),
            "occurred_at": now.isoformat(),
            "result": result,
            "reason": self._safe_text(reason, "audit reason"),
            "approval_refs": approvals,
            "provider_ref": item.provider_ref,
            "trust_version": item.trust_version,
            "evidence_correlation": correlation,
            "previous_hash": self._events[-1].event_hash if self._events else "GENESIS",
        }
        serialized = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
        event = LifecycleAuditEvent(
            event_id=f"ctrl03-event-{payload['sequence']:08d}",
            event_hash=hashlib.sha256(serialized.encode()).hexdigest(),
            **payload,
        )
        self._events.append(event)
        return event

    def _require_object(self, object_id: str) -> LifecycleObject:
        try:
            return self._objects[object_id]
        except KeyError as exc:
            raise AuthorizationRefused(
                "unknown lifecycle object", reason_code="UNKNOWN_TARGET"
            ) from exc

    def _require_request(self, request_id: str) -> LifecycleRequest:
        try:
            return self._requests[request_id]
        except KeyError as exc:
            raise AuthorizationRefused(
                "unknown lifecycle request", reason_code="UNKNOWN_REQUEST"
            ) from exc


def action_inventory() -> list[dict[str, Any]]:
    return [asdict(item) for item in CTRL03_ACTIONS]
