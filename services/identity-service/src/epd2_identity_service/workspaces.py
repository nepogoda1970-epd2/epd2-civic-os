"""The ten workspaces, from the server side.

`frontend/web-shell/foundation/workspaces.ts` is the authoritative
declaration and every entry in it already carries
`sessionSharing: "forbidden"`. This module is the identity service's
read of that same declaration - the origins a session may be bound to,
the sensitivity tiers that decide whether crossing into a workspace
requires reauthentication, and the one workspace that gets no session at
all.

**PACK-14 changes nothing about the ten-workspace / ten-origin model.**
It adds no workspace, moves no origin and relaxes no isolation rule; it
issues sessions that honour what is already declared. The parity between
this table and the TypeScript one is asserted by
`tests/repository/test_pack14_workspace_parity.py`, so the two cannot
drift.

**WS-03 is the exception that shapes the rest.** The Voting Client
receives no session, no cookie, no browser-storage identity and no
authentication bootstrap. Its only entry is the one-time
`VotingHandoffArtifact` in `voting_handoff.py`, which carries no
identifier of any kind.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from epd2_identity_service.exceptions import (
    OriginNotAllowedError,
    SessionScopeMismatchError,
    UnknownWorkspaceError,
)


class WorkspaceId(StrEnum):
    PUBLIC_WEBSITE = "WS-01"
    MEMBER_APPLICATION = "WS-02"
    VOTING_CLIENT = "WS-03"
    MANDATE_HOLDER = "WS-04"
    CITIZEN_OFFICE = "WS-05"
    INSTITUTIONAL_ADMINISTRATION = "WS-06"
    COMPLIANCE_AND_LEGAL = "WS-07"
    FINANCE = "WS-08"
    INDEPENDENT_OVERSIGHT = "WS-09"
    TRANSPARENCY_PORTAL = "WS-10"


def parse_workspace(value: str) -> WorkspaceId:
    try:
        return WorkspaceId(value)
    except ValueError as exc:
        raise UnknownWorkspaceError(f"unknown workspace: {value!r}") from exc


class BootstrapMode(StrEnum):
    """What kind of entry a workspace permits.

    `HANDOFF_ONLY` exists for exactly one workspace and is what makes
    WS-03's isolation structural rather than procedural: there is no
    value of any parameter that gives the Voting Client an ordinary
    session.
    """

    NONE_REQUIRED = "none_required"
    FULL = "full"
    FULL_WITH_PRIVILEGED_GRANT = "full_with_privileged_grant"
    FULL_WITH_INDEPENDENCE_CHECK = "full_with_independence_check"
    HANDOFF_ONLY = "handoff_only"


@dataclass(frozen=True, slots=True)
class WorkspacePolicy:
    """One row of the cross-workspace session matrix."""

    workspace: WorkspaceId
    name: str
    origin: str
    sensitivity: str
    bootstrap: BootstrapMode
    issues_identity_session: bool
    #: Reauthentication tier. A session crossing from a lower tier into a
    #: higher one re-authenticates; it never exchanges a token.
    risk_tier: int
    #: Always `False`. Present as a field rather than assumed, so a test
    #: can assert the whole column and a future edit that flips one is a
    #: visible change rather than an invisible one.
    session_sharing_permitted: bool = False
    browser_storage_identity_permitted: bool = False

    def __post_init__(self) -> None:
        if self.session_sharing_permitted or self.browser_storage_identity_permitted:
            raise ValueError(
                "every workspace declares sessionSharing: forbidden and permits no "
                "browser-storage identity; PACK-14 does not relax that"
            )


WORKSPACE_POLICIES: dict[WorkspaceId, WorkspacePolicy] = {
    WorkspaceId.PUBLIC_WEBSITE: WorkspacePolicy(
        workspace=WorkspaceId.PUBLIC_WEBSITE,
        name="Public Website",
        origin="https://www.epd.example",
        sensitivity="PUBLIC_APPROVED",
        bootstrap=BootstrapMode.NONE_REQUIRED,
        issues_identity_session=False,
        risk_tier=0,
    ),
    WorkspaceId.MEMBER_APPLICATION: WorkspacePolicy(
        workspace=WorkspaceId.MEMBER_APPLICATION,
        name="Member Application",
        origin="https://app.epd.example",
        sensitivity="INTERNAL; CONFIDENTIAL_CASE_SCOPED",
        bootstrap=BootstrapMode.FULL,
        issues_identity_session=True,
        risk_tier=1,
    ),
    WorkspaceId.VOTING_CLIENT: WorkspacePolicy(
        workspace=WorkspaceId.VOTING_CLIENT,
        name="Voting Client",
        origin="https://vote.epd.example",
        sensitivity="VOTING_SCOPED; NO_DIRECT_IDENTITY",
        bootstrap=BootstrapMode.HANDOFF_ONLY,
        issues_identity_session=False,
        risk_tier=3,
    ),
    WorkspaceId.MANDATE_HOLDER: WorkspacePolicy(
        workspace=WorkspaceId.MANDATE_HOLDER,
        name="Mandate Holder Workspace",
        origin="https://represent.epd.example",
        sensitivity="MANDATE_INTERNAL; CASE_CONFIDENTIAL",
        bootstrap=BootstrapMode.FULL,
        issues_identity_session=True,
        risk_tier=2,
    ),
    WorkspaceId.CITIZEN_OFFICE: WorkspacePolicy(
        workspace=WorkspaceId.CITIZEN_OFFICE,
        name="Citizen Office Portal",
        origin="https://office.epd.example",
        sensitivity="CASE_CONFIDENTIAL; SPECIAL_CATEGORY_POSSIBLE",
        bootstrap=BootstrapMode.FULL,
        issues_identity_session=True,
        risk_tier=2,
    ),
    WorkspaceId.INSTITUTIONAL_ADMINISTRATION: WorkspacePolicy(
        workspace=WorkspaceId.INSTITUTIONAL_ADMINISTRATION,
        name="Institutional Administration",
        origin="https://admin.epd.example",
        sensitivity="RESTRICTED_ADMIN; SECURITY_SENSITIVE",
        bootstrap=BootstrapMode.FULL_WITH_PRIVILEGED_GRANT,
        issues_identity_session=True,
        risk_tier=3,
    ),
    WorkspaceId.COMPLIANCE_AND_LEGAL: WorkspacePolicy(
        workspace=WorkspaceId.COMPLIANCE_AND_LEGAL,
        name="Compliance & Legal Workspace",
        origin="https://legal.epd.example",
        sensitivity="LEGAL_PRIVILEGED; EVIDENCE_RESTRICTED",
        bootstrap=BootstrapMode.FULL_WITH_PRIVILEGED_GRANT,
        issues_identity_session=True,
        risk_tier=3,
    ),
    WorkspaceId.FINANCE: WorkspacePolicy(
        workspace=WorkspaceId.FINANCE,
        name="Finance Workspace",
        origin="https://finance.epd.example",
        sensitivity="FINANCIAL_CONFIDENTIAL",
        bootstrap=BootstrapMode.FULL_WITH_PRIVILEGED_GRANT,
        issues_identity_session=True,
        risk_tier=3,
    ),
    WorkspaceId.INDEPENDENT_OVERSIGHT: WorkspacePolicy(
        workspace=WorkspaceId.INDEPENDENT_OVERSIGHT,
        name="Independent Oversight & Verification",
        origin="https://verify.epd.example",
        sensitivity="OVERSIGHT_RESTRICTED; PUBLIC_VERIFICATION",
        bootstrap=BootstrapMode.FULL_WITH_INDEPENDENCE_CHECK,
        issues_identity_session=True,
        risk_tier=3,
    ),
    WorkspaceId.TRANSPARENCY_PORTAL: WorkspacePolicy(
        workspace=WorkspaceId.TRANSPARENCY_PORTAL,
        name="Transparency Publication Portal",
        origin="https://transparency.epd.example",
        sensitivity="PUBLIC_APPROVED; AGGREGATED_DISCLOSURE_CONTROLLED",
        bootstrap=BootstrapMode.NONE_REQUIRED,
        issues_identity_session=False,
        risk_tier=0,
    ),
}

#: Every declared origin, for origin validation. A request from anything
#: else is refused rather than tolerated.
DECLARED_ORIGINS: frozenset[str] = frozenset(
    policy.origin for policy in WORKSPACE_POLICIES.values()
)


def workspace_policy(workspace: WorkspaceId) -> WorkspacePolicy:
    return WORKSPACE_POLICIES[workspace]


def workspace_origin(workspace: WorkspaceId) -> str:
    return WORKSPACE_POLICIES[workspace].origin


def assert_declared_origin(origin: str) -> None:
    if origin not in DECLARED_ORIGINS:
        raise OriginNotAllowedError(f"{origin!r} is not a declared workspace origin")


def assert_issues_identity_session(workspace: WorkspaceId) -> None:
    """WS-03's structural refusal.

    The Voting Client is never issued an ordinary session, and this is
    the function that makes that true regardless of what a caller passes.
    """
    policy = workspace_policy(workspace)
    if not policy.issues_identity_session:
        raise SessionScopeMismatchError(
            f"{policy.workspace.value} ({policy.name}) is never issued an identity session; "
            "its only entry is the one-time voting handoff artifact"
        )


def requires_reauthentication(*, source: WorkspaceId, target: WorkspaceId) -> bool:
    """Crossing into a higher-risk boundary requires a new
    authentication or a step-up, never a token exchange."""
    return workspace_policy(target).risk_tier > workspace_policy(source).risk_tier
