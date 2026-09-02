"""W6 — bounded break-glass lifecycle.

`REQUEST -> APPROVE -> ACTIVATE -> USE -> EXPIRE/REVOKE -> REVIEW`

The lifecycle has no renewal transition. Expiry is computed from activation
against the inventory's `max_grant_seconds` and is absolute: `use` re-checks it
at every call, so an open console page or a cached grant object never extends a
grant past its expiry. Certain acts remain prohibited even under break-glass.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timedelta

from epd2_control_plane_service.domain import BreakGlassGrant, BreakGlassState, Scope
from epd2_control_plane_service.exceptions import AuthorizationRefused
from epd2_control_plane_service.inventory import INVENTORY, ActionInventory
from epd2_control_plane_service.policy import ControlPolicy

__all__ = ["PROHIBITED_UNDER_BREAK_GLASS", "BreakGlassService"]

#: Acts that no emergency grant may ever authorize, whatever its scope
#: (`FIR-CTRL-001` break-glass boundary, `FIR-TRUST-002` section 7).
PROHIBITED_UNDER_BREAK_GLASS: frozenset[str] = frozenset(
    {
        "AUTH.ASSIGN",
        "AUTH.RESTORE",
        "OFFICE.ASSIGN_MANDATE",
        "REPORTING.CUSTODY_ACCESS",
        "KEY.DESTROY",
        "RECORDS.APPLY_RETENTION",
    }
)


class BreakGlassService:
    def __init__(
        self, policy: ControlPolicy | None = None, inventory: ActionInventory = INVENTORY
    ) -> None:
        self._policy = policy or ControlPolicy.governed()
        self._inventory = inventory
        self._grants: dict[str, BreakGlassGrant] = {}

    def grants(self) -> tuple[BreakGlassGrant, ...]:
        return tuple(self._grants.values())

    def grant(self, grant_id: str) -> BreakGlassGrant | None:
        return self._grants.get(grant_id)

    def request(
        self,
        *,
        grant_id: str,
        principal_id: str,
        requested_by: str,
        reason: str,
        scope: Scope,
        action_codes: Iterable[str],
        requested_at: datetime,
    ) -> BreakGlassGrant:
        codes = frozenset(action_codes)
        if not codes:
            raise AuthorizationRefused(
                "break-glass requires an exact action scope", reason_code="CTRL_EMERGENCY_SCOPE"
            )
        unknown = sorted(c for c in codes if c not in self._inventory)
        if unknown:
            raise AuthorizationRefused(
                f"break-glass references unknown action codes {unknown}",
                reason_code="CTRL_INVENTORY_INCONSISTENT",
            )
        prohibited = sorted(codes & PROHIBITED_UNDER_BREAK_GLASS)
        if prohibited:
            raise AuthorizationRefused(
                f"{prohibited} remain prohibited even under break-glass",
                reason_code="CTRL_EMERGENCY_PROHIBITED_ACTION",
            )
        not_eligible = sorted(c for c in codes if not self._inventory.get(c).emergency_eligible)
        if not_eligible:
            raise AuthorizationRefused(
                f"{not_eligible} are not emergency-eligible in the governed inventory",
                reason_code="CTRL_EMERGENCY_NOT_ELIGIBLE",
            )
        grant = BreakGlassGrant(
            grant_id=grant_id,
            principal_id=principal_id,
            reason=reason,
            scope=scope,
            action_codes=codes,
            state=BreakGlassState.REQUESTED,
            requested_at=requested_at,
            requested_by=requested_by,
            prohibited_action_codes=PROHIBITED_UNDER_BREAK_GLASS,
        )
        self._grants[grant_id] = grant
        return grant

    def approve(self, grant_id: str, *, approver_id: str, approved_at: datetime) -> BreakGlassGrant:
        grant = self._require(grant_id)
        if grant.state is not BreakGlassState.REQUESTED:
            raise AuthorizationRefused(
                f"grant {grant_id} is {grant.state.value} and cannot be approved",
                reason_code="CTRL_EMERGENCY_STATE",
            )
        if self._policy.reject_self_approval and approver_id in {
            grant.requested_by,
            grant.principal_id,
        }:
            raise AuthorizationRefused(
                "break-glass approval requires a distinct controller",
                reason_code="CTRL_SELF_APPROVAL",
            )
        updated = _replace(
            grant, state=BreakGlassState.APPROVED, approved_by=approver_id, approved_at=approved_at
        )
        self._grants[grant_id] = updated
        return updated

    def activate(self, grant_id: str, *, activated_at: datetime) -> BreakGlassGrant:
        grant = self._require(grant_id)
        if grant.state is not BreakGlassState.APPROVED:
            raise AuthorizationRefused(
                f"grant {grant_id} is {grant.state.value} and cannot be activated",
                reason_code="CTRL_EMERGENCY_STATE",
            )
        lifetime = min(
            self._inventory.get(code).max_grant_seconds or 0 for code in grant.action_codes
        )
        if lifetime <= 0:
            raise AuthorizationRefused(
                "emergency grant lifetime is not bounded by the inventory",
                reason_code="CTRL_EMERGENCY_UNBOUNDED",
            )
        updated = _replace(
            grant,
            state=BreakGlassState.ACTIVE,
            activated_at=activated_at,
            expires_at=activated_at + timedelta(seconds=lifetime),
        )
        self._grants[grant_id] = updated
        return updated

    def use(
        self, grant_id: str, *, action_id: str, scope: Scope, moment: datetime, use_ref: str
    ) -> BreakGlassGrant:
        grant = self._require(grant_id)
        grant = self.expire_due(moment).get(grant_id, grant)
        if self._policy.enforce_emergency_expiry and not grant.is_usable_at(moment):
            raise AuthorizationRefused(
                f"grant {grant_id} is not usable at {moment.isoformat()}",
                reason_code="CTRL_EMERGENCY_EXPIRED",
            )
        if self._policy.enforce_emergency_scope:
            if action_id not in grant.action_codes:
                raise AuthorizationRefused(
                    f"{action_id} is outside the approved emergency scope",
                    reason_code="CTRL_EMERGENCY_SCOPE",
                )
            if not grant.scope.contains(scope):
                raise AuthorizationRefused(
                    f"scope {scope.key} is outside the approved emergency scope",
                    reason_code="CTRL_EMERGENCY_SCOPE",
                )
        updated = _replace(grant, used_action_refs=(*grant.used_action_refs, use_ref))
        self._grants[grant_id] = updated
        return updated

    def revoke(self, grant_id: str, *, revoked_at: datetime) -> BreakGlassGrant:
        grant = self._require(grant_id)
        updated = _replace(grant, state=BreakGlassState.REVOKED, revoked_at=revoked_at)
        self._grants[grant_id] = updated
        return updated

    def expire_due(self, moment: datetime) -> dict[str, BreakGlassGrant]:
        """Automatic expiry. No silent renewal path exists."""
        if not self._policy.enforce_emergency_expiry:
            return self._grants
        for grant_id, grant in list(self._grants.items()):
            if (
                grant.state is BreakGlassState.ACTIVE
                and grant.expires_at is not None
                and moment >= grant.expires_at
            ):
                self._grants[grant_id] = _replace(grant, state=BreakGlassState.EXPIRED)
        return self._grants

    def review(self, grant_id: str, *, reviewer_id: str, review_ref: str) -> BreakGlassGrant:
        grant = self._require(grant_id)
        if grant.state not in {BreakGlassState.EXPIRED, BreakGlassState.REVOKED}:
            raise AuthorizationRefused(
                "post-use review runs after expiry or revocation",
                reason_code="CTRL_EMERGENCY_STATE",
            )
        if reviewer_id in {grant.requested_by, grant.principal_id, grant.approved_by}:
            raise AuthorizationRefused(
                "an actor of the grant may not conduct its post-use review",
                reason_code="CTRL_EMERGENCY_SELF_REVIEW",
            )
        updated = _replace(grant, state=BreakGlassState.REVIEWED, review_ref=review_ref)
        self._grants[grant_id] = updated
        return updated

    def unreviewed(self) -> tuple[BreakGlassGrant, ...]:
        """Grants that ended without the mandatory review."""
        return tuple(
            g
            for g in self._grants.values()
            if g.state in {BreakGlassState.EXPIRED, BreakGlassState.REVOKED}
            and g.review_ref is None
        )

    def _require(self, grant_id: str) -> BreakGlassGrant:
        grant = self._grants.get(grant_id)
        if grant is None:
            raise AuthorizationRefused(
                f"unknown emergency grant {grant_id}", reason_code="CTRL_EMERGENCY_UNKNOWN"
            )
        return grant


def _replace(grant: BreakGlassGrant, **changes: object) -> BreakGlassGrant:
    from dataclasses import replace as _dc_replace

    return _dc_replace(grant, **changes)  # type: ignore[arg-type]
