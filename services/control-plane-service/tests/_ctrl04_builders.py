"""Shared CTRL-04 test world builders."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from epd2_control_plane_service.credential_lifecycle import Ctrl02State
from epd2_control_plane_service.operations_adapters import (
    AdapterCapability,
    ReferenceOperationsAdapter,
)
from epd2_control_plane_service.operations_console import (
    ActionType,
    AuthorityProjection,
    AuthorityProjectionSigner,
    ConsoleSession,
    Ctrl03TrustState,
    DeploymentIdentity,
    EnvironmentClass,
    OperationalIncidentRef,
    OperationalTarget,
    OperationsConsoleService,
    OperationsPolicy,
    SessionState,
    TargetClass,
    TargetDomain,
)
from epd2_control_plane_service.regional_operations import (
    ActorClass,
    ApproverClass,
    AuthorityDirectory,
    AuthorityGrant,
    ExactScope,
)

NOW = datetime(2026, 9, 3, 9, 0, tzinfo=UTC)
BERLIN = ExactScope("DE-BE", "org-berlin")
BAVARIA = ExactScope("DE-BY", "org-bavaria")
BUND = ExactScope("DE", "org-bund")
KEY = b"ctrl04-test-projection-key-0123456789"
ARTIFACT_A = "a" * 64
ARTIFACT_B = "b" * 64
ARTIFACT_UNVERIFIED = "c" * 64
ARTIFACT_UNATTESTED = "e" * 64

PRINCIPALS: tuple[tuple[str, str, str, ApproverClass | None, ExactScope], ...] = (
    ("g-reader", "reader", "OPS.READ", None, BERLIN),
    ("g-req", "requester", "OPS.READ", None, BERLIN),
    ("g-req-r", "requester", "OPS.REQUEST", None, BERLIN),
    ("g-req2", "requester-2", "OPS.REQUEST", None, BERLIN),
    ("g-req2-r", "requester-2", "OPS.READ", None, BERLIN),
    ("g-ic", "incident-commander", "OPS.APPROVE", ApproverClass.INCIDENT_COMMANDER, BERLIN),
    ("g-ic-read", "incident-commander", "OPS.READ", None, BERLIN),
    ("g-sec", "security-officer", "OPS.APPROVE", ApproverClass.SECURITY, BERLIN),
    ("g-trust", "trust-custodian", "OPS.APPROVE", ApproverClass.TRUST_CUSTODIAN, BERLIN),
    ("g-exec", "executor", "OPS.EXECUTE", None, BERLIN),
    ("g-exec-read", "executor", "OPS.READ", None, BERLIN),
    ("g-exec2", "executor-2", "OPS.EXECUTE", None, BERLIN),
    ("g-rev", "reviewer", "OPS.REVIEW", None, BERLIN),
    ("g-rev-read", "reviewer", "OPS.READ", None, BERLIN),
    ("g-by-req", "bavaria-requester", "OPS.REQUEST", None, BAVARIA),
    ("g-by-read", "bavaria-requester", "OPS.READ", None, BAVARIA),
    ("g-ro", "readonly-operator", "OPS.READ", None, BERLIN),
    ("g-ro-req", "readonly-operator", "OPS.REQUEST", None, BERLIN),
    ("g-ro-exec", "readonly-operator", "OPS.EXECUTE", None, BERLIN),
    ("g-dual-req", "dual-hat", "OPS.REQUEST", None, BERLIN),
    ("g-dual-app", "dual-hat", "OPS.APPROVE", ApproverClass.INCIDENT_COMMANDER, BERLIN),
    ("g-bund-req", "bund-admin", "OPS.REQUEST", None, BUND),
    ("g-bund-read", "bund-admin", "OPS.READ", None, BUND),
    ("g-root-all", "root", "*", None, BERLIN),
    ("g-root-req", "root", "OPS.REQUEST", None, BERLIN),
    ("g-rx-req", "req-exec", "OPS.REQUEST", None, BERLIN),
    ("g-rx-exec", "req-exec", "OPS.EXECUTE", None, BERLIN),
)


def directory() -> AuthorityDirectory:
    return AuthorityDirectory(
        AuthorityGrant(
            grant_id=grant_id,
            actor_id=actor,
            actor_class=ActorClass.HUMAN,
            capability=capability,
            scope=scope,
            version=1,
            approver_class=approver,
        )
        for grant_id, actor, capability, approver, scope in PRINCIPALS
    )


class World:
    """A fully wired console with a reference adapter and helpers."""

    def __init__(
        self,
        *,
        policy: OperationsPolicy | None = None,
        store: Any | None = None,
        environment: EnvironmentClass = EnvironmentClass.PRODUCTION_LIKE,
    ) -> None:
        self.authorities = directory()
        self.signer = AuthorityProjectionSigner(KEY)
        self.adapter = ReferenceOperationsAdapter("reference-adapter")
        self.ctrl02 = Ctrl02State()
        self.ctrl03 = Ctrl03TrustState()
        self.ctrl03.attest(ARTIFACT_A)
        self.ctrl03.attest(ARTIFACT_B)
        self.service = OperationsConsoleService(
            authorities=self.authorities,
            signer=self.signer,
            adapters={"reference-adapter": self.adapter},
            ctrl02=self.ctrl02,
            ctrl03=self.ctrl03,
            policy=policy,
            store=store,
        )
        self.now = NOW
        self.populate(environment)

    def populate(self, environment: EnvironmentClass) -> None:
        svc = self.service
        svc.register_deployment(
            DeploymentIdentity(
                "dep-web-1",
                ARTIFACT_A,
                "oci://epd2/web@sha256:" + ARTIFACT_A,
                "rel-1.4.0",
                "chg-101",
                1,
                True,
            )
        )
        svc.register_deployment(
            DeploymentIdentity(
                "dep-web-0",
                ARTIFACT_B,
                "oci://epd2/web@sha256:" + ARTIFACT_B,
                "rel-1.3.9",
                "chg-099",
                1,
                True,
            )
        )
        svc.register_deployment(
            DeploymentIdentity(
                "dep-web-x",
                ARTIFACT_UNVERIFIED,
                "oci://epd2/web@sha256:" + ARTIFACT_UNVERIFIED,
                "rel-1.5.0-rc",
                "chg-102",
                1,
                False,
            )
        )
        svc.register_deployment(
            DeploymentIdentity(
                "dep-web-y",
                ARTIFACT_UNATTESTED,
                "oci://epd2/web@sha256:" + ARTIFACT_UNATTESTED,
                "rel-1.2.0",
                "chg-080",
                1,
                True,
            )
        )
        svc.register_deployment(
            DeploymentIdentity(
                "dep-db-1",
                "d" * 64,
                "oci://epd2/db@sha256:" + "d" * 64,
                "rel-db-2",
                "chg-050",
                1,
                True,
            )
        )
        all_caps = frozenset(AdapterCapability)
        targets = [
            (
                "svc-web",
                TargetClass.SERVICE,
                TargetDomain.GENERAL,
                "dep-web-1",
                frozenset(
                    {
                        AdapterCapability.RESTART,
                        AdapterCapability.ROLLBACK,
                        AdapterCapability.MAINTENANCE,
                    }
                ),
            ),
            (
                "svc-api",
                TargetClass.SERVICE,
                TargetDomain.GENERAL,
                "dep-web-1",
                frozenset({AdapterCapability.RESTART, AdapterCapability.MAINTENANCE}),
            ),
            (
                "svc-legacy",
                TargetClass.SERVICE,
                TargetDomain.GENERAL,
                "dep-web-0",
                frozenset({AdapterCapability.MAINTENANCE}),
            ),
            (
                "queue-mail",
                TargetClass.JOB_QUEUE,
                TargetDomain.GENERAL,
                "dep-web-1",
                frozenset({AdapterCapability.QUEUE_CONTROL}),
            ),
            (
                "int-payment",
                TargetClass.INTEGRATION,
                TargetDomain.GENERAL,
                "dep-web-1",
                frozenset(),
            ),
            (
                "db-members",
                TargetClass.DATASTORE,
                TargetDomain.GENERAL,
                "dep-db-1",
                frozenset(
                    {
                        AdapterCapability.BACKUP,
                        AdapterCapability.RESTORE,
                        AdapterCapability.MAINTENANCE,
                    }
                ),
            ),
            (
                "db-archive",
                TargetClass.DATASTORE,
                TargetDomain.GENERAL,
                "dep-db-1",
                frozenset({AdapterCapability.BACKUP}),
            ),
            ("svc-voting-tally", TargetClass.SERVICE, TargetDomain.VOTING, "dep-web-1", all_caps),
        ]
        for target_id, klass, domain, dep, caps in targets:
            svc.register_target(
                OperationalTarget(
                    target_id=target_id,
                    target_class=klass,
                    domain=domain,
                    environment=environment,
                    scope=BERLIN,
                    deployment_identity_ref=dep,
                    adapter_id="reference-adapter",
                    version=1,
                    capabilities=caps,
                    display_name=target_id,
                )
            )
            self.adapter.configure_target(
                target_id,
                capabilities=caps,
                metadata={
                    "provider_region": "eu-central",
                    "api_token": "sk_live_abcdef123456",
                    "secret_ref": "vault://ops/web",
                },
            )
        self.adapter.set_health(
            "int-payment", "DEGRADED", {"latency_ms": "900", "provider_password": "hunter2"}
        )
        self.adapter.set_health("svc-legacy", "UNAVAILABLE")
        self.adapter.set_queue("queue-mail", state="RUNNING", depth=12, oldest_age_seconds=30)
        svc.register_incident(OperationalIncidentRef("INC-1", "svc-web", "SEV2", "OPEN"))
        for principal in {p[1] for p in PRINCIPALS}:
            svc.open_session(
                ConsoleSession(
                    session_id=f"sess-{principal}",
                    principal_id=principal,
                    state=SessionState.ACTIVE,
                    established_at=NOW - timedelta(minutes=5),
                    expires_at=NOW + timedelta(hours=8),
                    read_only=principal == "readonly-operator",
                )
            )

    # helpers -----------------------------------------------------------------

    def tick(self, seconds: int = 1) -> datetime:
        self.now = self.now + timedelta(seconds=seconds)
        return self.now

    def projection(
        self,
        principal: str,
        capability: str,
        *,
        scope: ExactScope = BERLIN,
        approver: ApproverClass | None = None,
    ) -> AuthorityProjection:
        grant = self.authorities.require(
            actor_id=principal,
            capability=capability,
            scope=scope,
            now=self.now,
            approver_class=approver,
        )
        return self.signer.issue(grant, now=self.now)

    def request(
        self,
        action_type: ActionType = ActionType.SERVICE_RESTART,
        target_id: str = "svc-web",
        *,
        principal: str = "requester",
        parameters: dict[str, str] | None = None,
        idempotency_key: str | None = None,
        scope: ExactScope = BERLIN,
    ) -> Any:
        self.tick()
        return self.service.request(
            actor_ref=principal,
            session_id=f"sess-{principal}",
            projection=self.projection(principal, "OPS.REQUEST", scope=scope),
            action_type=action_type,
            target_id=target_id,
            parameters=parameters if parameters is not None else {"reason": "test"},
            idempotency_key=idempotency_key or f"idem-{self.now.timestamp()}",
            purpose="test",
            now=self.now,
        )

    def approve(
        self,
        action_id: str,
        principal: str = "incident-commander",
        approver: ApproverClass = ApproverClass.INCIDENT_COMMANDER,
    ) -> Any:
        self.tick()
        return self.service.approve(
            action_id=action_id,
            approver_ref=principal,
            session_id=f"sess-{principal}",
            projection=self.projection(principal, "OPS.APPROVE", approver=approver),
            approver_class=approver.value,
            now=self.now,
        )

    def commit(
        self, action_id: str, principal: str = "executor", *, scope: ExactScope = BERLIN
    ) -> Any:
        self.tick()
        return self.service.commit(
            action_id=action_id,
            executor_ref=principal,
            session_id=f"sess-{principal}",
            projection=self.projection(principal, "OPS.EXECUTE", scope=scope),
            now=self.now,
        )

    def resolve(self, action_id: str) -> Any:
        self.tick()
        return self.service.resolve(action_id=action_id, now=self.now)

    def review(self, action_id: str, principal: str = "reviewer") -> Any:
        self.tick()
        return self.service.review(
            action_id=action_id,
            reviewer_ref=principal,
            session_id=f"sess-{principal}",
            projection=self.projection(principal, "OPS.REVIEW"),
            now=self.now,
        )

    def full_restart(self, target_id: str = "svc-web") -> Any:
        action = self.request(ActionType.SERVICE_RESTART, target_id)
        if action.required_approver_classes:
            self.approve(action.action_id)
        self.commit(action.action_id)
        return self.resolve(action.action_id)

    def completed_backup(self, target_id: str = "db-members", backup_set_id: str = "set-1") -> Any:
        action = self.request(
            ActionType.BACKUP_REQUEST,
            target_id,
            parameters={"reason": "pre-change", "backup_set_id": backup_set_id},
        )
        if action.required_approver_classes:
            self.approve(action.action_id)
        self.commit(action.action_id)
        self.resolve(action.action_id)
        return next(b for b in self.service.backup_operations() if b.action_id == action.action_id)

    def active_window(self, target_id: str = "db-members", minutes: int = 60) -> Any:
        action = self.request(
            ActionType.MAINTENANCE_ENTER,
            target_id,
            parameters={"reason": "restore", "duration_minutes": str(minutes)},
        )
        if action.required_approver_classes:
            self.approve(action.action_id)
        self.commit(action.action_id)
        self.resolve(action.action_id)
        return self.service.action(action.action_id).maintenance_window_ref
