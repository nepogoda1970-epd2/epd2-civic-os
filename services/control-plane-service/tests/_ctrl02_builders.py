from __future__ import annotations

from datetime import UTC, datetime, timedelta

from epd2_control_plane_service.regional_operations import (
    ActorClass,
    ApproverClass,
    AuthorityDirectory,
    AuthorityGrant,
    ExactScope,
    InterventionLevel,
    RegionalOperationsService,
)

NOW = datetime(2026, 9, 2, 10, 0, tzinfo=UTC)
BERLIN = ExactScope("DE-BE", "org-berlin")
BAVARIA = ExactScope("DE-BY", "org-bavaria")


def directory() -> AuthorityDirectory:
    rows = [
        ("req", "requester", "INTERVENTION.REQUEST", None, ActorClass.HUMAN, BERLIN),
        (
            "a1",
            "approver-1",
            "INTERVENTION.APPROVE",
            ApproverClass.GOVERNANCE,
            ActorClass.HUMAN,
            BERLIN,
        ),
        (
            "a2",
            "approver-2",
            "INTERVENTION.APPROVE",
            ApproverClass.GOVERNANCE,
            ActorClass.HUMAN,
            BERLIN,
        ),
        (
            "sec",
            "security-1",
            "INTERVENTION.APPROVE",
            ApproverClass.SECURITY,
            ActorClass.HUMAN,
            BERLIN,
        ),
        ("exec", "executor", "INTERVENTION.EXECUTE", None, ActorClass.HUMAN, BERLIN),
        ("revoke", "revoker", "INTERVENTION.REVOKE", None, ActorClass.HUMAN, BERLIN),
        ("review", "reviewer", "INTERVENTION.REVIEW", None, ActorClass.HUMAN, BERLIN),
        ("restore", "restorer", "INTERVENTION.RESTORE", None, ActorClass.HUMAN, BERLIN),
        (
            "credential",
            "security-operator",
            "SERVICE_CREDENTIAL.CONTAIN",
            None,
            ActorClass.HUMAN,
            BERLIN,
        ),
        (
            "trust",
            "trust-requester",
            "TRUST.CHANGE_REQUEST",
            None,
            ActorClass.HUMAN,
            BERLIN,
        ),
        (
            "svc",
            "service-actor",
            "INTERVENTION.APPROVE",
            ApproverClass.GOVERNANCE,
            ActorClass.SERVICE,
            BERLIN,
        ),
        ("bund", "bund-actor", "INTERVENTION.REQUEST", None, ActorClass.HUMAN, BAVARIA),
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


def service() -> RegionalOperationsService:
    return RegionalOperationsService(directory())


def request(
    svc: RegionalOperationsService,
    *,
    request_id: str = "request-1",
    level: InterventionLevel = InterventionLevel.REGIONAL_ACTION_RESTRICTION,
    targets: tuple[str, ...] = ("action:MEMBER.UPDATE",),
    capabilities: tuple[str, ...] = ("MEMBER.UPDATE",),
    target_version: int = 1,
):
    return svc.request_intervention(
        request_id=request_id,
        level=level,
        requester_id="requester",
        governance_basis="FIR-GOV-004/rule-v1",
        scope=BERLIN,
        target_ids=targets,
        reason="bounded incident response",
        evidence_refs=("evidence:incident-1",),
        not_before=NOW,
        expires_at=NOW + timedelta(hours=2),
        allowed_capabilities=capabilities,
        target_version=target_version,
        idempotency_key=f"idem:{request_id}",
    )


def approve_twice(svc: RegionalOperationsService, request_id: str = "request-1"):
    svc.approve(
        request_id,
        approver_id="approver-1",
        approver_class=ApproverClass.GOVERNANCE,
        now=NOW + timedelta(minutes=1),
        idempotency_key=f"approve-1:{request_id}",
    )
    return svc.approve(
        request_id,
        approver_id="approver-2",
        approver_class=ApproverClass.GOVERNANCE,
        now=NOW + timedelta(minutes=2),
        idempotency_key=f"approve-2:{request_id}",
    )


def activate(svc: RegionalOperationsService, request_id: str = "request-1"):
    return svc.activate(
        request_id,
        executor_id="executor",
        now=NOW + timedelta(minutes=3),
        idempotency_key=f"activate:{request_id}",
    )
