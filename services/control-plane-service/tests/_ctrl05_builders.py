"""Shared CTRL-05 test world builders.

The oversight world reads **real** evidence: a real CTRL-02
`RegionalOperationsService` intervention, a real CTRL-03
`CredentialLifecycleService` revocation and a real CTRL-04 operations console
action, each producing its own hash-chained records. Nothing here fabricates
an evidence row.
"""

from __future__ import annotations

import contextlib
from datetime import UTC, datetime, timedelta
from typing import Any

import _ctrl02_builders as c02
import _ctrl03_builders as c03
from _ctrl04_builders import World as Ctrl04World
from epd2_control_plane_service.credential_lifecycle import CredentialClass
from epd2_control_plane_service.exceptions import AuthorizationRefused
from epd2_control_plane_service.operations_console import ActionType, TargetDomain
from epd2_control_plane_service.oversight_console import (
    AuditRight,
    OversightConsoleService,
    OversightMandate,
    OversightPolicy,
    OversightScope,
    OversightSession,
    SessionState,
)
from epd2_control_plane_service.oversight_sources import (
    Ctrl02EvidenceSource,
    Ctrl03EvidenceSource,
    Ctrl04EvidenceSource,
    EvidencePlane,
    VotingVerificationReference,
    VotingVerificationSource,
)
from epd2_control_plane_service.regional_operations import (
    ActorClass,
    AuthorityDirectory,
    AuthorityGrant,
    ExactScope,
)

NOW = datetime(2026, 9, 3, 12, 0, tzinfo=UTC)

BERLIN_ORG = ExactScope("DE-BE", "org-berlin")
BAVARIA_ORG = ExactScope("DE-BY", "org-bavaria")

#: Two oversight units inside the *same* organization. Neither reaches the
#: other: unit scope is exact, not hierarchical.
OPS_UNIT = OversightScope("DE-BE", "org-berlin", "unit-operations-audit")
PRIVACY_UNIT = OversightScope("DE-BE", "org-berlin", "unit-privacy-oversight")
BAVARIA_UNIT = OversightScope("DE-BY", "org-bavaria", "unit-operations-audit")

RULE = "FIR-GOV-005/oversight-rule-v1"
DECISION = "decision:oversight-board-2026-07"

ALL_PLANES = frozenset(EvidencePlane)

#: (grant_id, actor, capability, scope)
AUDIT_GRANTS: tuple[tuple[str, str, str, ExactScope], ...] = (
    ("ag-read", "auditor", "AUDIT.READ", BERLIN_ORG),
    ("ag-corr", "auditor", "AUDIT.CORRELATE", BERLIN_ORG),
    ("ag-rev", "auditor", "AUDIT.REVIEW", BERLIN_ORG),
    ("ag-exp", "auditor", "AUDIT.EXPORT", BERLIN_ORG),
    ("ag-att-read", "attestor", "AUDIT.READ", BERLIN_ORG),
    ("ag-att-rev", "attestor", "AUDIT.REVIEW", BERLIN_ORG),
    ("ag-att", "attestor", "AUDIT.ATTEST", BERLIN_ORG),
    ("ag-att-exp", "attestor", "AUDIT.EXPORT", BERLIN_ORG),
    ("ag-ro", "read-only-auditor", "AUDIT.READ", BERLIN_ORG),
    ("ag-privacy", "privacy-officer", "AUDIT.READ", BERLIN_ORG),
    ("ag-privacy-rev", "privacy-officer", "AUDIT.REVIEW", BERLIN_ORG),
    ("ag-by", "bavaria-auditor", "AUDIT.READ", BAVARIA_ORG),
    ("ag-by-rev", "bavaria-auditor", "AUDIT.REVIEW", BAVARIA_ORG),
    ("ag-by-corr", "bavaria-auditor", "AUDIT.CORRELATE", BAVARIA_ORG),
    # A principal who also holds a CTRL-04 execution right: oversight must not
    # give them any operational reach, and their operational reach must not
    # give them oversight.
    ("ag-dual-read", "dual-hat-operator", "AUDIT.READ", BERLIN_ORG),
    ("ag-dual-rev", "dual-hat-operator", "AUDIT.REVIEW", BERLIN_ORG),
    ("ag-dual-ops", "dual-hat-operator", "OPS.EXECUTE", BERLIN_ORG),
    # A universal capability holder: refused everywhere.
    ("ag-super", "super-admin", "*", BERLIN_ORG),
    ("ag-super-read", "super-admin", "AUDIT.READ", BERLIN_ORG),
    # A mandate whose backing grant was replaced by a newer version.
    ("ag-stale", "stale-auditor", "AUDIT.READ", BERLIN_ORG),
    ("ag-nomandate", "unmandated", "AUDIT.READ", BERLIN_ORG),
    # A principal whose *only* backing capability is operational: a mandate
    # that binds an audit right to it must be refused outright.
    ("ag-ops-borrow", "right-borrower", "OPS.EXECUTE", BERLIN_ORG),
)

PRINCIPALS = tuple(sorted({row[1] for row in AUDIT_GRANTS}))


def directory() -> AuthorityDirectory:
    return AuthorityDirectory(
        AuthorityGrant(
            grant_id=grant_id,
            actor_id=actor,
            actor_class=ActorClass.HUMAN,
            capability=capability,
            scope=scope,
            version=1,
        )
        for grant_id, actor, capability, scope in AUDIT_GRANTS
    )


def _mandate(
    mandate_id: str,
    subject: str,
    scope: OversightScope,
    rights: frozenset[AuditRight],
    bindings: dict[AuditRight, str],
    *,
    planes: frozenset[EvidencePlane] = ALL_PLANES,
    valid_from: datetime = NOW - timedelta(days=1),
    valid_until: datetime = NOW + timedelta(days=30),
) -> OversightMandate:
    return OversightMandate(
        mandate_id=mandate_id,
        subject_ref=subject,
        scope=scope,
        planes=planes,
        rights=rights,
        rule_version=RULE,
        source_decision_ref=DECISION,
        authority_bindings=frozenset((r.value, g) for r, g in bindings.items()),
        valid_from=valid_from,
        valid_until=valid_until,
    )


R = AuditRight


class World:
    """A CTRL-05 console reading real CTRL-02/03/04 evidence."""

    def __init__(
        self,
        *,
        policy: OversightPolicy | None = None,
        store: Any | None = None,
        sealer: Any | None = None,
        with_voting_reference: bool = True,
    ) -> None:
        self.now = NOW
        self.authorities = directory()

        # -- real CTRL-02 evidence -------------------------------------------
        self.ctrl02 = c02.service()
        c02.request(self.ctrl02, request_id="request-1")
        c02.approve_twice(self.ctrl02, "request-1")
        c02.activate(self.ctrl02, "request-1")

        # -- real CTRL-03 evidence -------------------------------------------
        self.ctrl03 = c03.service()
        self.ctrl03.register(c03.object_for(CredentialClass.JWS_SIGNING_KEY))
        c03.request(self.ctrl03, request_id="request-1")
        c03.approve_security(self.ctrl03, "request-1")
        c03.approve_trust(self.ctrl03, "request-1")
        c03.execute(self.ctrl03, "request-1")

        # -- real CTRL-04 evidence -------------------------------------------
        self.ctrl04_world = Ctrl04World()
        self.ctrl04 = self.ctrl04_world.service
        action = self.ctrl04_world.request(ActionType.SERVICE_RESTART, "svc-web")
        self.ctrl04_world.approve(action.action_id)
        self.ctrl04_world.commit(action.action_id)
        self.ctrl04_world.resolve(action.action_id)
        self.ctrl04_action_id = action.action_id
        self.ctrl04_correlation = action.action_id

        # Real voting-domain evidence: CTRL-04 refuses an operation on a
        # voting-domain target and journals the refusal. That record exists in
        # the plane, so CTRL-05's voting boundary is exercised against a real
        # envelope rather than a hypothetical one.
        with contextlib.suppress(AuthorizationRefused):
            self.ctrl04_world.request(ActionType.SERVICE_RESTART, "svc-voting-tally")

        # The voting-domain object set is *declared by CTRL-04*, which owns the
        # target registry; CTRL-05 never infers it from a name.
        # `targets()` already hides voting-domain targets from operators, so
        # the declaration is read from the governed registry itself.
        voting_refs = frozenset(
            t.target_id for t in self.ctrl04._targets.values() if t.domain is TargetDomain.VOTING
        )
        self.voting_domain_refs = voting_refs

        self.ctrl02_source = Ctrl02EvidenceSource(self.ctrl02, voting_domain_refs=voting_refs)
        self.ctrl03_source = Ctrl03EvidenceSource(self.ctrl03, voting_domain_refs=voting_refs)
        self.ctrl04_source = Ctrl04EvidenceSource(self.ctrl04, voting_domain_refs=voting_refs)

        self.voting = VotingVerificationSource()
        if with_voting_reference:
            self.voting.register(
                VotingVerificationReference(
                    interface_id="voting-verifier-berlin",
                    published_digest="9" * 64,
                    verification_status="PUBLISHED_AND_VERIFIED",
                    published_at=NOW.isoformat(),
                )
            )

        # Every source stream is mapped to exactly one governed oversight unit.
        self.evidence_units = {
            f"{EvidencePlane.CTRL02.value}:{self.ctrl02_source.stream_id()}": OPS_UNIT.key,
            f"{EvidencePlane.CTRL03.value}:{self.ctrl03_source.stream_id()}": OPS_UNIT.key,
            f"{EvidencePlane.CTRL04.value}:{self.ctrl04_source.stream_id()}": OPS_UNIT.key,
        }

        self.service = OversightConsoleService(
            authorities=self.authorities,
            sources={
                EvidencePlane.CTRL02.value: self.ctrl02_source,
                EvidencePlane.CTRL03.value: self.ctrl03_source,
                EvidencePlane.CTRL04.value: self.ctrl04_source,
            },
            evidence_units=self.evidence_units,
            voting_verification=self.voting,
            policy=policy,
            store=store,
            sealer=sealer,
        )
        self.register_mandates()
        self.open_sessions()

    # -- registration ---------------------------------------------------------

    def register_mandates(self) -> None:
        svc = self.service
        svc.register_mandate(
            _mandate(
                "MND-auditor",
                "auditor",
                OPS_UNIT,
                frozenset({R.READ, R.CORRELATE, R.REVIEW, R.EXPORT}),
                {
                    R.READ: "ag-read",
                    R.CORRELATE: "ag-corr",
                    R.REVIEW: "ag-rev",
                    R.EXPORT: "ag-exp",
                },
            )
        )
        svc.register_mandate(
            _mandate(
                "MND-attestor",
                "attestor",
                OPS_UNIT,
                frozenset({R.READ, R.REVIEW, R.ATTEST, R.EXPORT}),
                {
                    R.READ: "ag-att-read",
                    R.REVIEW: "ag-att-rev",
                    R.ATTEST: "ag-att",
                    R.EXPORT: "ag-att-exp",
                },
            )
        )
        svc.register_mandate(
            _mandate(
                "MND-readonly",
                "read-only-auditor",
                OPS_UNIT,
                frozenset({R.READ}),
                {R.READ: "ag-ro"},
            )
        )
        # Same organization, a different oversight unit: reaches nothing of the
        # operations-audit unit's evidence.
        svc.register_mandate(
            _mandate(
                "MND-privacy",
                "privacy-officer",
                PRIVACY_UNIT,
                frozenset({R.READ, R.REVIEW}),
                {R.READ: "ag-privacy", R.REVIEW: "ag-privacy-rev"},
            )
        )
        svc.register_mandate(
            _mandate(
                "MND-bavaria",
                "bavaria-auditor",
                BAVARIA_UNIT,
                frozenset({R.READ, R.REVIEW, R.CORRELATE}),
                {R.READ: "ag-by", R.REVIEW: "ag-by-rev", R.CORRELATE: "ag-by-corr"},
            )
        )
        svc.register_mandate(
            _mandate(
                "MND-dual",
                "dual-hat-operator",
                OPS_UNIT,
                frozenset({R.READ, R.REVIEW}),
                {R.READ: "ag-dual-read", R.REVIEW: "ag-dual-rev"},
            )
        )
        svc.register_mandate(
            _mandate(
                "MND-super",
                "super-admin",
                OPS_UNIT,
                frozenset({R.READ}),
                {R.READ: "ag-super-read"},
            )
        )
        # Bound to a grant id that is not the live one.
        svc.register_mandate(
            _mandate(
                "MND-stale",
                "stale-auditor",
                OPS_UNIT,
                frozenset({R.READ}),
                {R.READ: "ag-does-not-exist"},
            )
        )
        # A mandate that only covers CTRL-02.
        svc.register_mandate(
            _mandate(
                "MND-ctrl02-only",
                "read-only-auditor",
                OPS_UNIT,
                frozenset({R.READ}),
                {R.READ: "ag-ro"},
                planes=frozenset({EvidencePlane.CTRL02}),
            )
        )

    def open_sessions(self) -> None:
        for principal in PRINCIPALS:
            self.service.open_session(
                OversightSession(
                    session_id=f"sess-{principal}",
                    principal_id=principal,
                    state=SessionState.ACTIVE,
                    established_at=NOW - timedelta(minutes=5),
                    expires_at=NOW + timedelta(hours=8),
                    csrf_token=f"csrf-{principal}",
                )
            )

    # -- helpers --------------------------------------------------------------

    def tick(self, seconds: int = 1) -> datetime:
        self.now = self.now + timedelta(seconds=seconds)
        return self.now

    def csrf(self, principal: str) -> str:
        return f"csrf-{principal}"

    def references(self, plane: EvidencePlane | None = None) -> list[str]:
        """Every reference key the auditor can currently see."""
        result = self.search()
        keys = [r["reference"]["key"] for r in result["records"]]
        if plane is None:
            return keys
        return [k for k in keys if k.startswith(plane.value + ":")]

    def search(
        self,
        *,
        principal: str = "auditor",
        scope: OversightScope = OPS_UNIT,
        **kwargs: Any,
    ) -> dict[str, Any]:
        from epd2_control_plane_service.oversight_console import EvidenceQuery

        self.tick()
        return self.service.search(
            actor_ref=principal,
            session_id=f"sess-{principal}",
            query=EvidenceQuery(scope=scope, **kwargs),
            now=self.now,
        )

    def open_case(
        self,
        *,
        principal: str = "auditor",
        scope: OversightScope = OPS_UNIT,
        title: str = "restart under review",
        evidence_refs: list[str] | None = None,
        idempotency_key: str | None = None,
    ) -> Any:
        self.tick()
        refs = evidence_refs if evidence_refs is not None else self.references()[:2]
        return self.service.open_case(
            actor_ref=principal,
            session_id=f"sess-{principal}",
            csrf_token=self.csrf(principal),
            scope=scope,
            title=title,
            evidence_refs=refs,
            idempotency_key=idempotency_key or f"open-{self.now.timestamp()}",
            now=self.now,
        )

    def prepare(
        self,
        case_id: str,
        act: str,
        right: AuditRight,
        *,
        principal: str = "auditor",
    ) -> dict[str, Any]:
        self.tick()
        return self.service.prepare(
            actor_ref=principal,
            session_id=f"sess-{principal}",
            csrf_token=self.csrf(principal),
            case_id=case_id,
            act=act,
            right=right,
            now=self.now,
        )

    def dispose(
        self,
        case_id: str,
        disposition: Any,
        *,
        principal: str = "auditor",
        rationale: str = "evidence reviewed",
        idempotency_key: str | None = None,
    ) -> Any:
        ticket = self.prepare(case_id, "DISPOSE", R.REVIEW, principal=principal)
        self.tick()
        return self.service.dispose(
            actor_ref=principal,
            session_id=f"sess-{principal}",
            csrf_token=self.csrf(principal),
            ticket_id=ticket["ticket_id"],
            disposition=disposition,
            rationale=rationale,
            idempotency_key=idempotency_key or f"disp-{self.now.timestamp()}",
            now=self.now,
        )

    def raise_finding(
        self,
        case_id: str,
        severity: Any,
        evidence_ref: str,
        *,
        principal: str = "auditor",
        summary: str = "authority basis not recorded",
        idempotency_key: str | None = None,
    ) -> Any:
        ticket = self.prepare(case_id, "FINDING", R.REVIEW, principal=principal)
        self.tick()
        return self.service.raise_finding(
            actor_ref=principal,
            session_id=f"sess-{principal}",
            csrf_token=self.csrf(principal),
            ticket_id=ticket["ticket_id"],
            severity=severity,
            summary=summary,
            evidence_ref=evidence_ref,
            idempotency_key=idempotency_key or f"find-{self.now.timestamp()}",
            now=self.now,
        )

    def attest(
        self,
        case_id: str,
        *,
        principal: str = "attestor",
        statement: str = "the case was reviewed under the mandate named here",
        idempotency_key: str | None = None,
    ) -> Any:
        ticket = self.prepare(case_id, "ATTEST", R.ATTEST, principal=principal)
        self.tick()
        return self.service.attest(
            actor_ref=principal,
            session_id=f"sess-{principal}",
            csrf_token=self.csrf(principal),
            ticket_id=ticket["ticket_id"],
            statement=statement,
            idempotency_key=idempotency_key or f"att-{self.now.timestamp()}",
            now=self.now,
        )

    def export(
        self,
        case_id: str,
        purpose: str,
        evidence_refs: list[str],
        *,
        principal: str = "auditor",
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        ticket = self.prepare(case_id, "EXPORT", R.EXPORT, principal=principal)
        self.tick()
        return self.service.export(
            actor_ref=principal,
            session_id=f"sess-{principal}",
            csrf_token=self.csrf(principal),
            ticket_id=ticket["ticket_id"],
            purpose=purpose,
            evidence_refs=evidence_refs,
            idempotency_key=idempotency_key or f"exp-{self.now.timestamp()}",
            now=self.now,
        )

    def reviewed_case(self) -> Any:
        """A case carrying a disposition, ready for attestation."""
        from epd2_control_plane_service.oversight_console import ReviewState

        case = self.open_case()
        self.dispose(case.case_id, ReviewState.FINDING_RAISED)
        return self.service.case(case.case_id)
