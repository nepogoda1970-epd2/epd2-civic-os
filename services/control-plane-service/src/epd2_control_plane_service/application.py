"""W7/W9 — the control-plane application service.

This is where the invariants become executable. Three properties matter most:

* **Every mutation resolves to exactly one inventory entry.** The runtime
  surface is `routes.ROUTE_TABLE`, maintained independently of `inventory.py`;
  gate G04 reconciles the two in both directions, so a route cannot exist
  without a governed entry and an entry cannot exist without a route.

* **Authorization happens twice.** `submit_request` authorizes the REQUEST
  right; `execute` re-resolves the executor *and every approver* against the
  state at commit time. A grant, authority, session or scope that changed
  between request and commit refuses the commit. There is no code path that
  reuses the request-time decision.

* **A refusal is evidence.** Every refusal appends a reason-coded record to the
  immutable journal before raising, so an attempted escalation is as visible as
  a successful act.
"""

from __future__ import annotations

import itertools
from collections.abc import Mapping, Sequence
from dataclasses import replace
from datetime import datetime
from typing import Any

from epd2_control_plane_service.audit import EvidenceJournal
from epd2_control_plane_service.authority import AuthorityDirectory, AuthorityResolution
from epd2_control_plane_service.breakglass import BreakGlassService
from epd2_control_plane_service.domain import (
    ControlAction,
    ControlRequest,
    CredentialClass,
    CredentialState,
    Principal,
    Right,
    Scope,
    SessionState,
)
from epd2_control_plane_service.exceptions import (
    AuthorizationRefused,
    ControlPlaneError,
    InventoryError,
    VotingBoundaryViolation,
)
from epd2_control_plane_service.intervention import InterventionService
from epd2_control_plane_service.inventory import INVENTORY, ActionInventory
from epd2_control_plane_service.policy import ControlPolicy
from epd2_control_plane_service.routes import ROUTE_TABLE, mutation_action_ids
from epd2_control_plane_service.sod import Responsibility, SodEngine

__all__ = ["PERMITTED_REQUEST_PARAMETERS", "ControlPlane", "ExecutionOutcome"]

#: The only keys a control request may carry. Anything else is refused rather
#: than stored, so there is no field a caller can smuggle onto an authority.
PERMITTED_REQUEST_PARAMETERS: frozenset[str] = frozenset(
    {"justification_ref", "ticket_ref", "effective_from", "effective_until"}
)


class ExecutionOutcome:
    """The result of a committed control action."""

    __slots__ = ("approver_ids", "authority_basis", "evidence_sequence", "request")

    def __init__(
        self,
        request: ControlRequest,
        evidence_sequence: int,
        authority_basis: str,
        approver_ids: tuple[str, ...],
    ) -> None:
        self.request = request
        self.evidence_sequence = evidence_sequence
        self.authority_basis = authority_basis
        self.approver_ids = approver_ids


class ControlPlane:
    def __init__(
        self,
        *,
        directory: AuthorityDirectory,
        journal: EvidenceJournal,
        policy: ControlPolicy | None = None,
        inventory: ActionInventory = INVENTORY,
        sod: SodEngine | None = None,
        interventions: InterventionService | None = None,
        emergency: BreakGlassService | None = None,
        honour_request_parameters: bool = False,
        runtime_action_ids: frozenset[str] | None = None,
    ) -> None:
        self._directory = directory
        self._journal = journal
        self._policy = policy or ControlPolicy.governed()
        self._inventory = inventory
        self._sod = sod or SodEngine(self._policy)
        self._interventions = interventions or InterventionService(self._policy, inventory)
        self._emergency = emergency or BreakGlassService(self._policy, inventory)
        self._requests: dict[str, ControlRequest] = {}
        self._principals: dict[str, Principal] = {}
        self._counter = itertools.count(1)
        # W11 fixture switch. A runtime that copies request parameters onto the
        # acting authority is the mass-assignment defect; the governed runtime
        # never does, and treats an unknown parameter key as a refusal.
        self._honour_request_parameters = honour_request_parameters
        self._runtime_action_ids = runtime_action_ids

    # -- registry -----------------------------------------------------------

    @property
    def emergency(self) -> BreakGlassService:
        return self._emergency

    @property
    def interventions(self) -> InterventionService:
        return self._interventions

    @property
    def sod(self) -> SodEngine:
        return self._sod

    @property
    def journal(self) -> EvidenceJournal:
        return self._journal

    @property
    def directory(self) -> AuthorityDirectory:
        return self._directory

    def register_principal(self, principal: Principal) -> None:
        self._principals[principal.principal_id] = principal

    def principal(self, principal_id: str) -> Principal:
        try:
            return self._principals[principal_id]
        except KeyError:
            raise AuthorizationRefused(
                f"unknown principal {principal_id}", reason_code="CTRL_UNKNOWN_PRINCIPAL"
            ) from None

    def runtime_mutation_ids(self) -> frozenset[str]:
        """The action ids this runtime actually serves a mutating route for.

        Read from `routes.ROUTE_TABLE`, which is maintained separately from the
        inventory on purpose: comparing the inventory against a projection of
        itself would prove nothing.
        """
        if self._runtime_action_ids is not None:
            return self._runtime_action_ids
        return mutation_action_ids()

    def runtime_routes(self) -> Mapping[str, str]:
        return {path: action for (_, path), action in ROUTE_TABLE.items()}

    # -- evidence -----------------------------------------------------------

    def _emit(
        self,
        *,
        moment: datetime,
        principal_id: str,
        actor_class: str,
        authority_basis: str,
        action_id: str,
        scope: Scope,
        object_ref: str,
        result: str,
        reason_code: str,
        approval_refs: Sequence[str] = (),
        correlation_ref: str,
        attributes: Mapping[str, Any] | None = None,
    ) -> int:
        event = self._journal.append(
            occurred_at=moment,
            actor_ref=principal_id,
            actor_class=actor_class,
            authority_basis=authority_basis,
            action_id=action_id,
            scope_key=scope.key,
            object_ref=object_ref,
            result=result,
            reason_code=reason_code,
            approval_refs=approval_refs,
            correlation_ref=correlation_ref,
            attributes=attributes,
        )
        return event.sequence

    def _refuse(
        self,
        *,
        moment: datetime,
        principal_id: str,
        action_id: str,
        scope: Scope,
        object_ref: str,
        reason_code: str,
        detail: str,
        correlation_ref: str,
        authority_basis: str = "NONE",
        error: ControlPlaneError | None = None,
    ) -> ControlPlaneError:
        """Record the refusal as evidence and return the error to raise.

        The original exception instance is returned unchanged where one was
        supplied, so a voting-boundary or privacy refusal keeps its own type
        instead of being flattened into a generic authorization failure.
        """
        known = principal_id in self._principals
        actor_class = self._principals[principal_id].actor_class.value if known else "UNKNOWN"
        self._emit(
            moment=moment,
            principal_id=principal_id,
            actor_class=actor_class,
            authority_basis=authority_basis,
            action_id=action_id,
            scope=scope,
            object_ref=object_ref,
            result="REFUSED",
            reason_code=reason_code,
            correlation_ref=correlation_ref,
            attributes={"detail": detail[:480]},
        )
        return error if error is not None else AuthorizationRefused(detail, reason_code=reason_code)

    # -- shared guards ------------------------------------------------------

    def _action(self, action_id: str) -> ControlAction:
        return self._inventory.get(action_id)

    def _guard_actor_class(self, action: ControlAction, principal: Principal) -> None:
        if not self._policy.enforce_actor_class:
            return
        if principal.actor_class is not action.actor_class:
            raise AuthorizationRefused(
                f"{action.action_id} is reserved for {action.actor_class.value}; "
                f"{principal.principal_id} is {principal.actor_class.value}",
                reason_code="CTRL_ACTOR_CLASS",
            )

    def _guard_session(self, session_id: str | None, principal_id: str, moment: datetime) -> None:
        if not self._policy.enforce_session_state:
            return
        if session_id is None:
            if self._policy.fail_closed_on_unknown:
                raise AuthorizationRefused(
                    "no session context; authority state cannot be established",
                    reason_code="CTRL_SESSION_UNKNOWN",
                )
            return
        session = self._directory.session(session_id)
        if session is None:
            raise AuthorizationRefused(
                f"unknown session {session_id}", reason_code="CTRL_SESSION_UNKNOWN"
            )
        if session.principal_id != principal_id:
            raise AuthorizationRefused(
                "session does not belong to the acting principal",
                reason_code="CTRL_SESSION_MISMATCH",
            )
        if session.state is not SessionState.ACTIVE:
            raise AuthorizationRefused(
                f"session {session_id} is {session.state.value}",
                reason_code="CTRL_SESSION_NOT_ACTIVE",
            )

    def _guard_credential(self, principal_id: str) -> None:
        """A privileged mutation re-evaluates the acting credential at use time.

        A principal with no registered control-plane credential is unaffected
        (workloads, and humans whose credential lifecycle is owned elsewhere);
        a principal whose credential is registered and not ACTIVE is refused.
        """
        if not self._policy.enforce_credential_state:
            return
        credentials = self._directory.credentials_of(principal_id)
        if not credentials:
            return
        if not any(state is CredentialState.ACTIVE for _, state in credentials):
            raise AuthorizationRefused(
                f"no active authentication credential for {principal_id}",
                reason_code="CTRL_CREDENTIAL_NOT_ACTIVE",
            )

    def _guard_voting_boundary(self, action: ControlAction, object_ref: str) -> None:
        if not self._policy.enforce_voting_boundary:
            return
        reference = self._directory.key_reference(object_ref)
        if reference is not None and reference.credential_class is CredentialClass.VOTING_DOMAIN:
            raise VotingBoundaryViolation(
                f"{action.action_id} may not operate voting-domain key material {object_ref}; "
                "voting keys exist here only as external governed references"
            )

    def _guard_restriction(
        self, action: ControlAction, scope: Scope, authority_id: str | None, moment: datetime
    ) -> None:
        blocking = self._directory.blocking_restriction(
            action.action_id, scope, authority_id, moment
        )
        if blocking is not None:
            raise AuthorizationRefused(
                (
                    f"{action.action_id} is frozen in {scope.key} by restriction "
                    f"{blocking.restriction_id}"
                ),
                reason_code="CTRL_RESTRICTION_ACTIVE",
            )

    def _resolve(
        self,
        *,
        subject_ref: str,
        right: Right,
        action: ControlAction,
        scope: Scope,
        moment: datetime,
    ) -> AuthorityResolution:
        return self._directory.resolve(
            subject_ref=subject_ref,
            required_right=right,
            action_id=action.action_id,
            scope=scope,
            moment=moment,
        )

    # -- read path ----------------------------------------------------------

    def read(
        self,
        *,
        action_id: str,
        principal_id: str,
        session_id: str | None,
        scope: Scope,
        object_ref: str,
        moment: datetime,
        correlation_ref: str | None = None,
    ) -> dict[str, Any]:
        correlation = correlation_ref or f"corr-{next(self._counter)}"
        action = self._action(action_id)
        if action.mutation:
            raise self._refuse(
                moment=moment,
                principal_id=principal_id,
                action_id=action_id,
                scope=scope,
                object_ref=object_ref,
                reason_code="CTRL_READ_PATH_MISUSE",
                detail=f"{action_id} is a mutation and cannot be served on the read path",
                correlation_ref=correlation,
            )
        principal = self.principal(principal_id)
        try:
            self._guard_actor_class(action, principal)
            self._guard_session(session_id, principal_id, moment)
            resolution = self._resolve(
                subject_ref=principal_id,
                right=action.required_right_execute,
                action=action,
                scope=scope,
                moment=moment,
            )
            if not resolution.granted:
                raise AuthorizationRefused(resolution.detail, reason_code=resolution.reason_code)
        except AuthorizationRefused as error:
            raise self._refuse(
                moment=moment,
                principal_id=principal_id,
                action_id=action_id,
                scope=scope,
                object_ref=object_ref,
                reason_code=error.reason_code,
                detail=str(error),
                correlation_ref=correlation,
                error=error,
            ) from None
        self._emit(
            moment=moment,
            principal_id=principal_id,
            actor_class=principal.actor_class.value,
            authority_basis=resolution.authority_basis,
            action_id=action_id,
            scope=scope,
            object_ref=object_ref,
            result="READ",
            reason_code="CTRL_AUTHORIZED",
            correlation_ref=correlation,
        )
        return {
            "action_id": action_id,
            "scope": scope.key,
            "object_ref": object_ref,
            "as_of": moment.isoformat(),
        }

    # -- mutation path ------------------------------------------------------

    def submit_request(
        self,
        *,
        request_id: str,
        action_id: str,
        principal_id: str,
        session_id: str | None,
        scope: Scope,
        object_ref: str,
        purpose: str,
        moment: datetime,
        parameters: Mapping[str, str] | None = None,
    ) -> ControlRequest:
        correlation = f"req-{request_id}"
        if self._policy.enforce_inventory_binding and action_id not in self._inventory:
            raise InventoryError(
                f"action {action_id!r} has no governed inventory entry; refusing to execute"
            )
        action = self._action(action_id)
        if not action.mutation:
            raise AuthorizationRefused(
                f"{action_id} is a read action and has no request workflow",
                reason_code="CTRL_READ_PATH_MISUSE",
            )
        principal = self.principal(principal_id)
        try:
            self._guard_actor_class(action, principal)
            self._guard_session(session_id, principal_id, moment)
            self._guard_voting_boundary(action, object_ref)
            resolution = self._resolve(
                subject_ref=principal_id,
                right=action.required_right_request,
                action=action,
                scope=scope,
                moment=moment,
            )
            if not resolution.granted:
                raise AuthorizationRefused(resolution.detail, reason_code=resolution.reason_code)
            self._guard_restriction(
                action,
                scope,
                None if resolution.authority is None else resolution.authority.authority_id,
                moment,
            )
        except (AuthorizationRefused, VotingBoundaryViolation) as error:
            raise self._refuse(
                moment=moment,
                principal_id=principal_id,
                action_id=action_id,
                scope=scope,
                object_ref=object_ref,
                reason_code=error.reason_code,
                detail=str(error),
                correlation_ref=correlation,
                error=error,
            ) from None

        assert resolution.authority is not None
        if self._honour_request_parameters:
            # The defect being modelled: caller-supplied fields are merged onto
            # the acting authority record.
            widened = replace(
                resolution.authority,
                capabilities=resolution.authority.capabilities | set(Right),
                oversight_of=resolution.authority.oversight_of
                | frozenset(
                    str(parameters.get("oversight_of", "")).split(",") if parameters else []
                ),
            )
            self._directory.record_authority(
                widened, recorded_at=moment, recorded_by="request-parameters"
            )
        elif parameters:
            unknown = sorted(set(parameters) - PERMITTED_REQUEST_PARAMETERS)
            if unknown:
                raise self._refuse(
                    moment=moment,
                    principal_id=principal_id,
                    action_id=action_id,
                    scope=scope,
                    object_ref=object_ref,
                    reason_code="CTRL_UNKNOWN_REQUEST_PARAMETER",
                    detail=f"request carries parameters outside the governed set: {unknown}",
                    correlation_ref=correlation,
                )
        request = ControlRequest(
            request_id=request_id,
            action_id=action_id,
            requested_by=principal_id,
            requesting_authority_id=resolution.authority.authority_id,
            target_scope=scope,
            object_ref=object_ref,
            purpose=purpose,
            requested_at=moment,
            parameters=dict(parameters or {}),
        )
        self._requests[request_id] = request
        self._emit(
            moment=moment,
            principal_id=principal_id,
            actor_class=principal.actor_class.value,
            authority_basis=resolution.authority_basis,
            action_id=action_id,
            scope=scope,
            object_ref=object_ref,
            result="REQUESTED",
            reason_code="CTRL_AUTHORIZED",
            correlation_ref=correlation,
            attributes={"purpose": purpose[:200], "request_id": request_id},
        )
        return request

    def approve(
        self, *, request_id: str, principal_id: str, session_id: str | None, moment: datetime
    ) -> ControlRequest:
        request = self._require_request(request_id)
        action = self._action(request.action_id)
        correlation = f"req-{request_id}"
        principal = self.principal(principal_id)
        try:
            if action.required_right_approve is None:
                raise AuthorizationRefused(
                    f"{action.action_id} defines no approval step",
                    reason_code="CTRL_NO_APPROVAL_STEP",
                )
            self._guard_actor_class(action, principal)
            self._guard_session(session_id, principal_id, moment)
            if self._policy.reject_self_approval and principal_id == request.requested_by:
                raise AuthorizationRefused(
                    "the requesting principal may not approve their own request",
                    reason_code="CTRL_SELF_APPROVAL",
                )
            if self._policy.reject_self_approval and principal_id in request.approver_ids():
                raise AuthorizationRefused(
                    "an approver may not contribute two approvals to the same quorum",
                    reason_code="CTRL_QUORUM_DUPLICATE_APPROVER",
                )
            resolution = self._resolve(
                subject_ref=principal_id,
                right=action.required_right_approve,
                action=action,
                scope=request.target_scope,
                moment=moment,
            )
            if not resolution.granted:
                raise AuthorizationRefused(resolution.detail, reason_code=resolution.reason_code)
            if (
                action.secret_visibility_right is not None
                and self._policy.enforce_secret_visibility
            ):
                approver = resolution.authority
                assert approver is not None
                if action.secret_visibility_right in approver.capabilities:
                    # SOD-04: approval never requires - and here never carries -
                    # plaintext secret visibility for the same operation.
                    raise AuthorizationRefused(
                        (
                            "an approver holding secret-visibility rights breaks SOD-04 for this "
                            "action"
                        ),
                        reason_code="CTRL_SECRET_VISIBILITY_APPROVER",
                    )
        except AuthorizationRefused as error:
            raise self._refuse(
                moment=moment,
                principal_id=principal_id,
                action_id=request.action_id,
                scope=request.target_scope,
                object_ref=request.object_ref,
                reason_code=error.reason_code,
                detail=str(error),
                correlation_ref=correlation,
                error=error,
            ) from None

        assert resolution.authority is not None
        updated = replace(
            request,
            approvals=(*request.approvals, (principal_id, resolution.authority.authority_id)),
        )
        self._requests[request_id] = updated
        self._emit(
            moment=moment,
            principal_id=principal_id,
            actor_class=principal.actor_class.value,
            authority_basis=resolution.authority_basis,
            action_id=request.action_id,
            scope=request.target_scope,
            object_ref=request.object_ref,
            result="APPROVED",
            reason_code="CTRL_AUTHORIZED",
            correlation_ref=correlation,
            attributes={"request_id": request_id, "approvals": str(len(updated.approvals))},
        )
        return updated

    def execute(
        self,
        *,
        request_id: str,
        principal_id: str,
        session_id: str | None,
        moment: datetime,
        emergency_grant_id: str | None = None,
        auditor_id: str | None = None,
    ) -> ExecutionOutcome:
        """Commit an approved request.

        Everything here is re-evaluated *now*: the executor's authority, each
        approver's authority, quorum, active restrictions, session state, scope
        and object. A request that was legitimately approved at time T is
        refused at T+1 if any of those changed.
        """
        request = self._require_request(request_id)
        action = self._action(request.action_id)
        correlation = f"req-{request_id}"
        principal = self.principal(principal_id)
        try:
            if request.executed_at is not None:
                raise AuthorizationRefused(
                    f"request {request_id} was already executed", reason_code="CTRL_REQUEST_REPLAY"
                )
            self._guard_actor_class(action, principal)
            self._guard_session(session_id, principal_id, moment)
            self._guard_credential(principal_id)
            self._guard_voting_boundary(action, request.object_ref)

            resolution = self._resolve(
                subject_ref=principal_id,
                right=action.required_right_execute,
                action=action,
                scope=request.target_scope,
                moment=moment,
            )
            emergency_used = False
            if not resolution.granted and emergency_grant_id is not None:
                # A break-glass grant may substitute for the ordinary execute
                # right, and only for the exact approved action and scope.
                self._emergency.use(
                    emergency_grant_id,
                    action_id=action.action_id,
                    scope=request.target_scope,
                    moment=moment,
                    use_ref=correlation,
                )
                emergency_used = True
            elif not resolution.granted:
                raise AuthorizationRefused(resolution.detail, reason_code=resolution.reason_code)

            executor_authority_id = (
                None if resolution.authority is None else resolution.authority.authority_id
            )
            self._guard_restriction(action, request.target_scope, executor_authority_id, moment)

            if self._policy.enforce_quorum and len(request.approvals) < action.quorum_required:
                raise AuthorizationRefused(
                    f"{action.action_id} requires {action.quorum_required} approval(s); "
                    f"{len(request.approvals)} present",
                    reason_code="CTRL_QUORUM_INSUFFICIENT",
                )

            if self._policy.commit_time_reauthorization:
                self._reauthorize_approvals(request, action, moment)

            self._check_sod(request, action, principal_id, auditor_id)

        except (AuthorizationRefused, VotingBoundaryViolation) as error:
            raise self._refuse(
                moment=moment,
                principal_id=principal_id,
                action_id=request.action_id,
                scope=request.target_scope,
                object_ref=request.object_ref,
                reason_code=error.reason_code,
                detail=str(error),
                correlation_ref=correlation,
                error=error,
            ) from None

        committed = replace(request, executed_at=moment)
        self._requests[request_id] = committed
        basis = (
            resolution.authority_basis
            if resolution.granted
            else f"BREAK_GLASS:{emergency_grant_id}"
        )
        sequence = self._emit(
            moment=moment,
            principal_id=principal_id,
            actor_class=principal.actor_class.value,
            authority_basis=basis,
            action_id=request.action_id,
            scope=request.target_scope,
            object_ref=request.object_ref,
            result="EXECUTED",
            reason_code="CTRL_AUTHORIZED",
            approval_refs=tuple(a for _, a in request.approvals),
            correlation_ref=correlation,
            attributes={
                "request_id": request_id,
                "emergency": "true" if emergency_used else "false",
                "quorum": str(len(request.approvals)),
            },
        )
        return ExecutionOutcome(committed, sequence, basis, tuple(p for p, _ in request.approvals))

    def _reauthorize_approvals(
        self, request: ControlRequest, action: ControlAction, moment: datetime
    ) -> None:
        assert action.required_right_approve is not None or action.quorum_required == 0
        if action.required_right_approve is None:
            return
        for approver_id, approver_authority_id in request.approvals:
            resolution = self._resolve(
                subject_ref=approver_id,
                right=action.required_right_approve,
                action=action,
                scope=request.target_scope,
                moment=moment,
            )
            if not resolution.granted:
                raise AuthorizationRefused(
                    (
                        f"approval by {approver_id} is no longer valid at commit time: "
                        f"{resolution.detail}"
                    ),
                    reason_code="CTRL_COMMIT_TIME_REAUTH_FAILED",
                )
            self._guard_credential(approver_id)
            assert resolution.authority is not None
            if resolution.authority.authority_id != approver_authority_id:
                raise AuthorizationRefused(
                    f"approval by {approver_id} was given under authority {approver_authority_id} "
                    f"which no longer resolves at commit time",
                    reason_code="CTRL_COMMIT_TIME_REAUTH_FAILED",
                )
            blocking = self._directory.blocking_restriction(
                action.action_id, request.target_scope, approver_authority_id, moment
            )
            if blocking is not None:
                raise AuthorizationRefused(
                    f"an intervention activated during the workflow blocks {action.action_id}",
                    reason_code="CTRL_RESTRICTION_ACTIVE",
                )

    def _check_sod(
        self,
        request: ControlRequest,
        action: ControlAction,
        executor_id: str,
        auditor_id: str | None,
    ) -> None:
        assignment: dict[Responsibility, tuple[str, ...]] = {
            Responsibility.REQUEST: (request.requested_by,),
            Responsibility.APPROVE: tuple(p for p, _ in request.approvals),
            Responsibility.EXECUTE: (executor_id,),
        }
        if auditor_id is not None:
            assignment[Responsibility.AUDIT] = (auditor_id,)
        if action.secret_visibility_right is not None:
            # Whoever executes an action that carries a secret-visibility right
            # is the principal who can see the material.
            assignment[Responsibility.SECRET_VISIBILITY] = (executor_id,)
        if action.domain == "credential":
            assignment[Responsibility.CREDENTIAL_ISSUANCE] = (executor_id,)
        if action.domain == "emergency":
            assignment[Responsibility.EMERGENCY_GRANT] = (executor_id, request.requested_by)
            if auditor_id is not None:
                assignment[Responsibility.EMERGENCY_REVIEW] = (auditor_id,)
        if action.domain == "key_trust":
            assignment[Responsibility.KEY_CUSTODY] = (executor_id,)
            assignment[Responsibility.POLICY_APPROVAL] = tuple(p for p, _ in request.approvals)
        if action.required_right_execute is Right.DESTROY:
            assignment[Responsibility.DESTRUCTIVE_OPERATION] = (executor_id,)
            assignment[Responsibility.DESTRUCTIVE_CONFIRMATION] = tuple(
                p for p, _ in request.approvals
            )
        if action.domain == "intervention":
            assignment[Responsibility.REGIONAL_ACTION] = (request.requested_by,)
            assignment[Responsibility.BUND_OVERSIGHT] = tuple(p for p, _ in request.approvals)
        violations = self._sod.evaluate(assignment)
        if violations:
            first = violations[0]
            raise AuthorizationRefused(
                f"{first.rule_id} violated: {first.principal_id} discharged both "
                f"{first.left.value} and {first.right.value}",
                reason_code=first.reason_code,
            )

    def _require_request(self, request_id: str) -> ControlRequest:
        try:
            return self._requests[request_id]
        except KeyError:
            raise AuthorizationRefused(
                f"unknown control request {request_id}", reason_code="CTRL_UNKNOWN_REQUEST"
            ) from None

    def request(self, request_id: str) -> ControlRequest | None:
        return self._requests.get(request_id)
