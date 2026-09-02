from __future__ import annotations

from datetime import UTC, datetime, timedelta

from epd2_control_plane_service.credential_lifecycle import (
    AssuranceProfile,
    CredentialClass,
    CredentialLifecycleService,
    LifecycleObject,
    LifecycleOperation,
    LifecycleState,
)
from epd2_control_plane_service.regional_operations import (
    ActorClass,
    ApproverClass,
    AuthorityDirectory,
    AuthorityGrant,
    ExactScope,
)

NOW = datetime(2026, 9, 2, 12, 30, tzinfo=UTC)
BERLIN = ExactScope("DE-BE", "org-berlin")
BAVARIA = ExactScope("DE-BY", "org-bavaria")


def directory() -> AuthorityDirectory:
    rows = [
        ("req", "requester", "LIFECYCLE.REQUEST", None, ActorClass.HUMAN, BERLIN),
        (
            "sec1",
            "security-1",
            "LIFECYCLE.APPROVE",
            ApproverClass.SECURITY,
            ActorClass.HUMAN,
            BERLIN,
        ),
        (
            "trust1",
            "trust-1",
            "LIFECYCLE.APPROVE",
            ApproverClass.TRUST_CUSTODIAN,
            ActorClass.HUMAN,
            BERLIN,
        ),
        (
            "sec2",
            "security-2",
            "LIFECYCLE.APPROVE",
            ApproverClass.SECURITY,
            ActorClass.HUMAN,
            BERLIN,
        ),
        ("exec", "custodian", "LIFECYCLE.EXECUTE", None, ActorClass.HUMAN, BERLIN),
        ("review", "reviewer", "LIFECYCLE.REVIEW", None, ActorClass.HUMAN, BERLIN),
        (
            "svc",
            "service-actor",
            "LIFECYCLE.REQUEST",
            None,
            ActorClass.SERVICE,
            BERLIN,
        ),
        ("by", "bavarian", "LIFECYCLE.REQUEST", None, ActorClass.HUMAN, BAVARIA),
    ]
    return AuthorityDirectory(
        AuthorityGrant(
            grant_id=grant_id,
            actor_id=actor,
            actor_class=actor_class,
            capability=capability,
            scope=scope,
            version=1,
            approver_class=approver_class,
        )
        for grant_id, actor, capability, approver_class, actor_class, scope in rows
    )


def service() -> CredentialLifecycleService:
    return CredentialLifecycleService(directory())


def object_for(
    credential_class: CredentialClass = CredentialClass.SERVICE_CREDENTIAL,
    *,
    object_id: str = "credential:old",
    parent_id: str | None = None,
    scope: ExactScope = BERLIN,
    state: LifecycleState = LifecycleState.ACTIVE,
) -> LifecycleObject:
    profile = None
    algorithm = None
    curve = None
    trust_location = None
    trust_version = None
    purpose = "service-authentication"
    if credential_class is CredentialClass.PASSKEY:
        profile = AssuranceProfile.PASSKEY_ES256
        algorithm, curve = "ES256", "P-256"
        purpose = "human-authentication"
    elif credential_class in {
        CredentialClass.SERVICE_CREDENTIAL,
        CredentialClass.JWS_SIGNING_KEY,
    }:
        profile = AssuranceProfile.SERVICE_JWS_ES256
        algorithm, curve = "ES256", "P-256"
        trust_location, trust_version = "https://trust.epd.invalid/jwks", 3
    elif credential_class is CredentialClass.MTLS_CERTIFICATE:
        profile = AssuranceProfile.MTLS
        algorithm, curve = "X509", "ECDSA-P384"
        purpose = "workload-mtls"
        trust_location, trust_version = "pki://epd/workload", 2
    elif credential_class is CredentialClass.JWKS_ENTRY:
        profile = AssuranceProfile.TRUST_ES384
        algorithm, curve = "ES384", "P-384"
        purpose = "regional-trust"
        trust_location, trust_version = "https://trust.epd.invalid/root", 3
    elif credential_class is CredentialClass.ENCRYPTION_KEY_REFERENCE:
        profile = AssuranceProfile.ENCRYPTION_AES256_GCM
        algorithm, curve = "A256GCM", "AES-256-GCM"
        purpose = "envelope-encryption"
    elif credential_class is CredentialClass.VOTING_KEY_REFERENCE:
        profile = AssuranceProfile.EXTERNAL_VOTING
        algorithm, curve = "EXTERNAL", "VOTING-DOMAIN-OWNED"
        purpose = "voting-external-reference"
    elif credential_class in {
        CredentialClass.HUMAN_CREDENTIAL,
        CredentialClass.RECOVERY_CREDENTIAL,
        CredentialClass.SESSION,
        CredentialClass.AUTHORITY_PROJECTION,
        CredentialClass.PROVIDER_SECRET,
    }:
        purpose = credential_class.value.lower()
    valid_until = (
        NOW + timedelta(hours=12)
        if credential_class is CredentialClass.VOTING_KEY_REFERENCE
        else NOW + timedelta(days=30)
    )
    return LifecycleObject(
        object_id=object_id,
        credential_class=credential_class,
        purpose=purpose,
        scope=scope,
        state=state,
        version=1,
        subject_ref="subject:member-1",
        profile=profile,
        algorithm=algorithm,
        curve_or_mode=curve,
        valid_from=NOW,
        valid_until=valid_until,
        provider_ref=None
        if credential_class is CredentialClass.VOTING_KEY_REFERENCE
        else "provider:neutral",
        custody_ref=None
        if credential_class is CredentialClass.VOTING_KEY_REFERENCE
        else "custody:ref",
        public_reference=f"public:{object_id}",
        trust_location=trust_location,
        trust_version=trust_version,
        parent_id=parent_id,
    )


def request(
    svc: CredentialLifecycleService,
    *,
    operation: LifecycleOperation = LifecycleOperation.REVOKE,
    target_id: str = "credential:old",
    request_id: str = "request-1",
    new_object_id: str | None = None,
    overlap_until=None,
):
    return svc.request_operation(
        request_id=request_id,
        operation=operation,
        target_id=target_id,
        requester_id="requester",
        reason="governed lifecycle change",
        evidence_refs=("evidence:change-1",),
        now=NOW,
        expires_at=NOW + timedelta(hours=2),
        idempotency_key=f"request:{request_id}",
        new_object_id=new_object_id,
        overlap_until=overlap_until,
    )


def approve_security(svc: CredentialLifecycleService, request_id: str = "request-1"):
    return svc.approve(
        request_id,
        approver_id="security-1",
        approver_class=ApproverClass.SECURITY,
        now=NOW + timedelta(minutes=1),
        idempotency_key=f"security:{request_id}",
    )


def approve_trust(svc: CredentialLifecycleService, request_id: str = "request-1"):
    return svc.approve(
        request_id,
        approver_id="trust-1",
        approver_class=ApproverClass.TRUST_CUSTODIAN,
        now=NOW + timedelta(minutes=2),
        idempotency_key=f"trust:{request_id}",
    )


def execute(svc: CredentialLifecycleService, request_id: str = "request-1"):
    return svc.execute(
        request_id,
        custodian_id="custodian",
        now=NOW + timedelta(minutes=3),
        idempotency_key=f"execute:{request_id}",
    )
