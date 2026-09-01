"""The governance-side versioned API: catalogue and reference adapter.

The generic half - the endpoint spec, the obligations, the request and
response values, the response-safety scan and the dispatcher - lives in
`epd2_core.api_contracts`, because four services need it and no service
may import another. What lives here is governance's own **endpoint list**
and its handlers.

Every endpoint below is declared `TrustSide.NEUTRAL`, and that is a claim
about what the registry holds rather than a convenience. A voting context
is administrative configuration - windows, organizational scope, the
frozen rule-set version, the assurance requirement, the revocation cutoff
and the disclosure floor - and nothing else. `assert_no_participant_data`
refuses a request that carries a participant, an assertion, a credential
or an outcome figure, so the neutral declaration is backed by a store
that has no column to put one in. Were it otherwise, a neutral endpoint
readable from both sides would be the join ADR-093 removed from SQL,
rebuilt in routing.

Three properties this catalogue exists to make structural:

* **Nothing is configured without naming the version it acted on.** Every
  consequential endpoint carries `expected_version`, and the handlers
  refuse a version that is no longer current. A configuration change
  computed against a superseded version is a change to parameters that
  have already moved, and applying it would silently reintroduce them.
* **Activation is dual control and nothing else.** `voting_context.activate`
  runs the separation matrix's `assert_dual_control` before the domain's
  own two-approver check, so the second signature has to come from a
  second principal holding a second role, under a time-boxed grant. One
  approver approving twice is refused twice.
* **No status is reported that the registry did not record.** The
  registry freezes an activated version's row, so a status write against
  one is silently ignored by the store rather than rejected.
  `voting_context.transition` therefore reads the row back before it
  commits and refuses when the recorded status is not the requested one.
  Without that read-back an operator would receive a successful
  suspension for a context that is still running, which is the worst
  possible shape for this particular failure.

There is deliberately **no endpoint that deletes or edits a version in
place**. A frozen rule set is only frozen if the row recording it cannot
be rewritten, so the only way to change a critical parameter is
`voting_context.configure`, which writes a successor version that must be
activated again on its own merits.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import datetime
from typing import Any
from uuid import uuid4

from epd2_core.api_contracts import (
    ApiDispatcher,
    ApiRequest,
    ApiRequestMalformedError,
    EndpointSpec,
    TrustSide,
    build_catalogue,
)
from epd2_governance_service.voting_authorization import (
    Approver,
    Capability,
    PermissionDeniedError,
    VotingRole,
    assert_dual_control,
    roles_with,
)
from epd2_governance_service.voting_contexts import (
    DisclosureControlProfile,
    DualControlRequiredError,
    UnknownVotingContextError,
    VotingContext,
    VotingContextConfigurationInvalidError,
    VotingContextStatus,
    VotingContextStore,
    VotingType,
    VotingWindow,
    assert_no_participant_data,
)


class VotingContextVersionConflictError(RuntimeError):
    """The caller acted on a version the registry has already moved past.

    Distinct from an invalid configuration, and deliberately so: this one
    is resolved by re-reading and retrying, and telling an operator
    otherwise during a running ballot would waste the minutes that
    matter.
    """

    reason_code = "VOTING_CONTEXT_VERSION_CONFLICT"


class VotingContextVersionFrozenError(RuntimeError):
    """The change targeted a version whose activation snapshot is captured.

    Retrying will never succeed. The correct action is a new version,
    because the version someone voted under may not change underneath
    them.
    """

    reason_code = "VOTING_CONTEXT_VERSION_FROZEN"


API_AREA_VOTING_CONTEXT = "voting_context"

#: The roles the separation matrix says hold configuration and activation
#: authority, taken from the matrix rather than restated. A hand-kept list
#: here would drift from `ROLE_CAPABILITIES`, and the drift would show up
#: as an endpoint nobody may call or - worse - one everybody may.
CONFIGURATION_ROLES: tuple[str, ...] = roles_with(Capability.CONFIGURATION_ACTIVATION)

#: Who may read a registry version. Wider than the write set on purpose:
#: the registry is the one store both sides read, and every role below
#: needs the administrative definition to do its own job - the eligibility
#: roles need the frozen rule-set version, the Credential Issuer needs the
#: issuance window and the revocation cutoff, and the two auditors need
#: the configuration an election was actually run under. It is still not
#: every role: reading is scoped because an endpoint open to everyone is
#: an endpoint nobody scoped.
REGISTRY_READER_ROLES: tuple[str, ...] = tuple(
    sorted(
        role.value
        for role in (
            VotingRole.VOTING_OPERATIONS_OFFICER,
            VotingRole.ELIGIBILITY_OFFICER,
            VotingRole.ELIGIBILITY_REVIEWER,
            VotingRole.CREDENTIAL_ISSUER,
            VotingRole.INDEPENDENT_AUDITOR,
            VotingRole.SECURITY_AUDITOR,
            VotingRole.DISPUTE_REVIEWER,
        )
    )
)


def _endpoint(
    operation: str,
    area: str,
    *,
    consequential: bool,
    roles: tuple[str, ...],
    reason_codes: tuple[str, ...],
    unauthenticated_by_design: bool = False,
    justification: str = "",
) -> EndpointSpec:
    """Declare one governance-side endpoint.

    Consequential endpoints take all three obligations; read endpoints
    take none. Stating them here rather than defaulting them keeps
    `assert_consequential_contract` meaningful: a new endpoint that calls
    itself consequential cannot quietly waive the version check.
    """
    return EndpointSpec(
        operation=operation,
        area=area,
        trust_side=TrustSide.NEUTRAL,
        consequential=consequential,
        idempotency_key_required=consequential,
        version_check_required=consequential,
        audit_evidence_required=consequential,
        authorized_roles=roles,
        reason_codes=reason_codes,
        unauthenticated_by_design=unauthenticated_by_design,
        justification=justification,
    )


VOTING_CONTEXT_ENDPOINTS: tuple[EndpointSpec, ...] = (
    _endpoint(
        "voting_context.draft",
        API_AREA_VOTING_CONTEXT,
        consequential=True,
        roles=CONFIGURATION_ROLES,
        reason_codes=(
            "VOTING_CONTEXT_CONFIGURATION_INVALID",
            "VOTING_CONTEXT_VERSION_CONFLICT",
            "VOTING_CONTEXT_SCOPE_MISMATCH",
            "TIMING_PROFILE_OUT_OF_BOUNDS",
            "API_REQUEST_MALFORMED",
        ),
    ),
    _endpoint(
        "voting_context.configure",
        API_AREA_VOTING_CONTEXT,
        consequential=True,
        roles=CONFIGURATION_ROLES,
        reason_codes=(
            "VOTING_CONTEXT_CONFIGURATION_INVALID",
            "VOTING_CONTEXT_VERSION_CONFLICT",
            "VOTING_CONTEXT_NOT_FOUND",
            "VOTING_CONTEXT_NOT_ACTIVE",
            "TIMING_PROFILE_OUT_OF_BOUNDS",
            "API_REQUEST_MALFORMED",
        ),
    ),
    _endpoint(
        "voting_context.activate",
        API_AREA_VOTING_CONTEXT,
        consequential=True,
        roles=CONFIGURATION_ROLES,
        reason_codes=(
            "VOTING_CONTEXT_ACTIVATED",
            "VOTING_CONTEXT_NOT_ACTIVE",
            "VOTING_CONTEXT_NOT_FOUND",
            "VOTING_CONTEXT_CONFIGURATION_INVALID",
            "VOTING_CONTEXT_VERSION_CONFLICT",
            "DUAL_CONTROL_REQUIRED",
            "SEPARATION_OF_DUTIES_REFUSED",
            "PRIVILEGED_APPROVAL_MISSING",
            "PERMISSION_DENIED",
        ),
    ),
    _endpoint(
        "voting_context.read",
        API_AREA_VOTING_CONTEXT,
        consequential=False,
        roles=REGISTRY_READER_ROLES,
        reason_codes=(
            "VOTING_CONTEXT_NOT_FOUND",
            "VOTING_CONTEXT_CONFIGURATION_INVALID",
            "VOTING_CONTEXT_VERSION_CONFLICT",
            "PERMISSION_DENIED",
        ),
    ),
    _endpoint(
        "voting_context.transition",
        API_AREA_VOTING_CONTEXT,
        consequential=True,
        roles=CONFIGURATION_ROLES,
        reason_codes=(
            "VOTING_CONTEXT_NOT_ACTIVE",
            "VOTING_CONTEXT_SUSPENDED",
            "VOTING_CONTEXT_CLOSED",
            "VOTING_CONTEXT_NOT_FOUND",
            "VOTING_CONTEXT_CONFIGURATION_INVALID",
            "VOTING_CONTEXT_VERSION_CONFLICT",
            "VOTING_CONTEXT_VERSION_FROZEN",
            "DUAL_CONTROL_REQUIRED",
            "API_REQUEST_MALFORMED",
        ),
    ),
)

VOTING_CONTEXT_CATALOGUE: Mapping[str, EndpointSpec] = build_catalogue(VOTING_CONTEXT_ENDPOINTS)

#: The critical parameters `voting_context.configure` may change. Closed
#: on purpose: a field outside this tuple is a field the registry does not
#: version, and accepting one would let a caller change something that no
#: activation snapshot ever covered.
CONFIGURABLE_TEXT_FIELDS: tuple[str, ...] = (
    "organizational_scope",
    "eligibility_rule_set_reference",
    "eligibility_rule_set_version",
    "required_assurance",
    "participation_class",
    "privacy_profile",
    "audit_profile",
)

#: Every key `voting_context.configure` understands. A request carrying
#: anything else is refused rather than trimmed: a caller that sent an
#: unknown field believed the registry would act on it, and silently
#: dropping it leaves them believing so.
CONFIGURE_REQUEST_KEYS: frozenset[str] = frozenset(
    {
        "voting_context_reference",
        "eligible_population",
        "revocation_cutoff",
        "voting_window_start",
        "voting_window_end",
        "issuance_window_start",
        "issuance_window_end",
        *CONFIGURABLE_TEXT_FIELDS,
    }
)


def _moment(request: ApiRequest, name: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(request.require(name)))
    except ValueError as error:
        raise ApiRequestMalformedError(f"{name} is not an ISO-8601 timestamp") from error
    if parsed.tzinfo is None:
        raise ApiRequestMalformedError(f"{name} must be timezone-aware")
    return parsed


def _integer(request: ApiRequest, name: str) -> int:
    try:
        return int(request.require(name))
    except (TypeError, ValueError) as error:
        raise ApiRequestMalformedError(f"{name} is not a whole number") from error


def _status(request: ApiRequest, name: str) -> VotingContextStatus:
    try:
        return VotingContextStatus(str(request.require(name)))
    except ValueError as error:
        raise ApiRequestMalformedError(f"{name} is not a registry status") from error


def _voting_type(request: ApiRequest, name: str) -> VotingType:
    try:
        return VotingType(str(request.require(name)))
    except ValueError as error:
        raise ApiRequestMalformedError(f"{name} is not one of the seven voting types") from error


def _approver(request: ApiRequest, prefix: str) -> Approver:
    """Read one approver, refusing a role outside the ten.

    An unrecognized role name is refused rather than treated as an
    unprivileged caller: a typo in an approver's role must fail loudly,
    because the failure mode of the alternative is an activation approved
    by a role the matrix never granted approval authority to.
    """
    name = str(request.require(f"{prefix}_role"))
    try:
        role = VotingRole(name)
    except ValueError as error:
        raise PermissionDeniedError(
            "an approver's role is not one of the ten separation-matrix roles"
        ) from error
    return Approver(
        principal_reference=str(request.require(f"{prefix}_principal")),
        role=role,
    )


def _current(
    store: VotingContextStore, reference: str, expected_version: int | None
) -> VotingContext:
    """The version the caller expects, refusing an absent or stale one.

    A change computed against a superseded version is a change to
    parameters that have already moved. Writing it would reintroduce the
    old values under a new version number, which is exactly the drift the
    activation snapshot exists to detect - except that here it would be
    recorded as a legitimate governed change.
    """
    latest = store.latest(reference)
    if latest is None:
        raise UnknownVotingContextError("no voting context is registered under this reference")
    if expected_version != latest.version:
        raise VotingContextVersionConflictError(
            f"the registry is at version {latest.version}; the caller acted on a version "
            "that is no longer current"
        )
    return latest


def _successor(current: VotingContext, changes: Mapping[str, Any]) -> VotingContext:
    """Produce the next version of a context, configured and unactivated.

    A configuration change is always a new row, whether or not the
    predecessor was activated. The registry's `save` only ever updates a
    row whose activation snapshot is still null, so an in-place edit of an
    activated version does nothing at all - and an in-place edit of a
    draft version would persist the status change while quietly dropping
    the parameter change, because the conflict clause updates the status
    column and not the others. Versioning unconditionally removes both
    failure modes.

    The successor starts unactivated and is transitioned to `configured`,
    so it still has to pass dual-control activation on its own merits.
    """
    if current.activation_snapshot is not None:
        draft = current.new_version_with(**changes)
    else:
        draft = replace(
            current,
            version=current.version + 1,
            status=VotingContextStatus.DRAFT,
            **changes,
        )
    return draft.transition(VotingContextStatus.CONFIGURED)


def _configuration_changes(request: ApiRequest) -> dict[str, Any]:
    """The closed set of critical parameters a configure call may change."""
    unknown = sorted(set(request.body) - CONFIGURE_REQUEST_KEYS)
    if unknown:
        raise ApiRequestMalformedError(
            "the registry has no such configurable parameter: " + ", ".join(unknown)
        )
    changes: dict[str, Any] = {
        name: str(request.body[name]) for name in CONFIGURABLE_TEXT_FIELDS if name in request.body
    }
    if "eligible_population" in request.body:
        changes["eligible_population"] = _integer(request, "eligible_population")
    if "revocation_cutoff" in request.body:
        changes["revocation_cutoff"] = _moment(request, "revocation_cutoff")
    for field, start, end in (
        ("voting_window", "voting_window_start", "voting_window_end"),
        ("credential_issuance_window", "issuance_window_start", "issuance_window_end"),
    ):
        if start in request.body or end in request.body:
            changes[field] = VotingWindow(
                starts_at=_moment(request, start), ends_at=_moment(request, end)
            )
    if not changes:
        raise ApiRequestMalformedError("a configuration call states the change it makes")
    return changes


def _drafted(request: ApiRequest, reference: str) -> VotingContext:
    """Assemble version 1 of a context from a draft request.

    Every consistency rule - window ordering, the revocation-cutoff
    maximum for the type, the disclosure floor - is enforced by
    `VotingContext.__post_init__` rather than re-checked here, so there is
    one place a malformed context is caught and no second copy of the
    rules to drift from it.
    """
    small_electorate = bool(request.body.get("small_electorate", False))
    return VotingContext(
        voting_context_id=uuid4(),
        voting_context_reference=reference,
        version=1,
        voting_type=_voting_type(request, "voting_type"),
        organizational_scope=str(request.require("organizational_scope")),
        status=VotingContextStatus.DRAFT,
        voting_window=VotingWindow(
            starts_at=_moment(request, "voting_window_start"),
            ends_at=_moment(request, "voting_window_end"),
        ),
        credential_issuance_window=VotingWindow(
            starts_at=_moment(request, "issuance_window_start"),
            ends_at=_moment(request, "issuance_window_end"),
        ),
        revocation_cutoff=_moment(request, "revocation_cutoff"),
        eligibility_rule_set_reference=str(request.require("eligibility_rule_set_reference")),
        eligibility_rule_set_version=str(request.require("eligibility_rule_set_version")),
        required_assurance=str(request.require("required_assurance")),
        participation_class=str(request.require("participation_class")),
        privacy_profile=str(request.require("privacy_profile")),
        audit_profile=str(request.require("audit_profile")),
        disclosure_control=DisclosureControlProfile(
            minimum_cell=int(request.body.get("disclosure_minimum_cell", 5)),
            small_electorate=small_electorate,
            # A small electorate publishes no per-scope metric at all, so
            # the default follows the flag instead of forcing every caller
            # to remember the pairing.
            per_scope_metrics_permitted=bool(
                request.body.get("per_scope_metrics_permitted", not small_electorate)
            ),
        ),
        eligible_population=_integer(request, "eligible_population"),
    )


@dataclass(frozen=True, slots=True)
class VotingContextRuntime:
    """The registry connection and the store bound to it.

    The store is typed as the `VotingContextStore` protocol rather than as
    the SQL adapter, so this module names no storage flavour and a
    deployment's composition root decides which one it runs. The
    connection is held beside it because every consequential handler
    commits, and a handler that mutated the registry without committing
    would report a governed change that vanishes at the next restart.
    """

    connection: sqlite3.Connection
    contexts: VotingContextStore


@dataclass(frozen=True, slots=True)
class VotingContextApi:
    """Governance's reference adapter.

    Every handler returns a view model, never a domain object: a
    dataclass serialized wholesale is how a field nobody meant to publish
    reaches a caller. The dispatcher scans every body before it leaves.
    """

    runtime: VotingContextRuntime
    dispatcher: ApiDispatcher

    def dispatch(self, request: ApiRequest) -> Any:
        return self.dispatcher.dispatch(request)


def build_voting_context_api(
    runtime: VotingContextRuntime,
    *,
    allowed_origins: tuple[str, ...],
) -> VotingContextApi:
    """Wire the governance catalogue to handlers over one runtime."""
    store = runtime.contexts

    def draft(request: ApiRequest) -> Mapping[str, Any]:
        """Register version 1 of a context, in `draft`.

        `expected_version` is 0 and not omitted. The obligation exists so
        every consequential call states the version it acted on, and a
        create acts on the absence of one - saying so explicitly is what
        stops a create from being the one governed act that carries no
        version claim at all.
        """
        assert_no_participant_data(request.body)
        if request.expected_version != 0:
            raise ApiRequestMalformedError(
                "a draft creates version 1 and therefore expects version 0"
            )
        reference = str(request.require("voting_context_reference"))
        if store.latest(reference) is not None:
            raise VotingContextConfigurationInvalidError(
                "this reference is already registered; a change to it is a new version"
            )
        context = _drafted(request, reference)
        store.save(context)
        runtime.connection.commit()
        return {
            "voting_context_reference": context.voting_context_reference,
            "version": context.version,
            "status": context.status.value,
            "voting_type": context.voting_type.value,
        }

    def configure(request: ApiRequest) -> Mapping[str, Any]:
        """Write the next version, carrying the requested changes."""
        assert_no_participant_data(request.body)
        reference = str(request.require("voting_context_reference"))
        current = _current(store, reference, request.expected_version)
        successor = _successor(current, _configuration_changes(request))
        store.save(successor)
        runtime.connection.commit()
        return {
            "voting_context_reference": reference,
            "version": successor.version,
            "status": successor.status.value,
            "supersedes_version": current.version,
        }

    def activate(request: ApiRequest) -> Mapping[str, Any]:
        """Activate under dual control, freezing the critical parameters.

        The separation matrix's check runs first and the domain's runs
        second, and they are not redundant. `assert_dual_control` decides
        whether these two principals may approve this capability at all -
        two distinct principals, two different roles, one time-boxed
        grant - while `VotingContext.activate` decides whether this
        context is in a state that may be activated. A caller that
        satisfies one and not the other is refused by the one it failed.
        """
        reference = str(request.require("voting_context_reference"))
        current = _current(store, reference, request.expected_version)
        record = assert_dual_control(
            Capability.CONFIGURATION_ACTIVATION,
            first_approver=_approver(request, "first_approver"),
            second_approver=_approver(request, "second_approver"),
            grant_reference=str(request.require("grant_reference")),
        )
        activated = current.activate(
            now=_moment(request, "now"),
            approver=record.first_approver.principal_reference,
            second_approver=record.second_approver.principal_reference,
        )
        store.save(activated)
        runtime.connection.commit()
        snapshot = activated.activation_snapshot
        # The snapshot digest is published deliberately: it is a
        # commitment to configuration, holds no participant data, and is
        # what lets an auditor later show that the parameters an election
        # ran under are the ones that were frozen. The approvers'
        # principal references are not published beside it - who approved
        # is audit-stream material, not a field every reader of the
        # registry receives.
        return {
            "voting_context_reference": reference,
            "version": activated.version,
            "status": activated.status.value,
            "activation_snapshot_digest": snapshot.snapshot_digest if snapshot else "",
            "privileged_act": record.reason_code,
        }

    def read(request: ApiRequest) -> Mapping[str, Any]:
        """Read one version, or the current one when none is named."""
        reference = str(request.require("voting_context_reference"))
        if "version" in request.body:
            context = store.get(reference, _integer(request, "version"))
        else:
            context = store.latest(reference)
        if context is None:
            raise UnknownVotingContextError("no such voting context version")
        # A drifted activated context is refused rather than returned with
        # a warning: a reader that receives parameters differing from the
        # frozen ones has no way to tell which set an election ran under.
        context.assert_snapshot_intact()
        snapshot = context.activation_snapshot
        # `eligible_population` is deliberately absent. The exact size of
        # an electorate is a disclosure-controlled figure in a small
        # scope, and the only thing a reader needs from it is whether the
        # small-electorate rules apply - which is the flag.
        return {
            "voting_context_reference": context.voting_context_reference,
            "version": context.version,
            "status": context.status.value,
            "voting_type": context.voting_type.value,
            "organizational_scope": context.organizational_scope,
            "voting_window_start": context.voting_window.starts_at.isoformat(),
            "voting_window_end": context.voting_window.ends_at.isoformat(),
            "issuance_window_start": context.credential_issuance_window.starts_at.isoformat(),
            "issuance_window_end": context.credential_issuance_window.ends_at.isoformat(),
            "revocation_cutoff": context.revocation_cutoff.isoformat(),
            "eligibility_rule_set_reference": context.eligibility_rule_set_reference,
            "eligibility_rule_set_version": context.eligibility_rule_set_version,
            "required_assurance": context.required_assurance,
            "participation_class": context.participation_class,
            "privacy_profile": context.privacy_profile,
            "audit_profile": context.audit_profile,
            "disclosure_minimum_cell": context.disclosure_control.minimum_cell,
            "small_electorate": context.disclosure_control.small_electorate,
            "activation_snapshot_digest": snapshot.snapshot_digest if snapshot else "",
        }

    def transition(request: ApiRequest) -> Mapping[str, Any]:
        """Move a context to a permitted next status, and prove it landed.

        `VotingContext.transition` refuses a move the transition table
        does not permit, which keeps the lifecycle honest in memory. The
        read-back below keeps it honest in storage: the registry freezes
        an activated version's row, so a status write against one is
        ignored by the store rather than rejected by it. Without this
        check the handler would return a successful suspension for a
        context that is still open for issuance, and the operator who
        asked for the suspension would have no reason to look again.
        """
        reference = str(request.require("voting_context_reference"))
        current = _current(store, reference, request.expected_version)
        target = _status(request, "target_status")
        if target is VotingContextStatus.CANCELLED and not request.body.get(
            "dual_control_reference"
        ):
            raise DualControlRequiredError(
                "cancellation is terminal - the transition table leads nowhere out of it - "
                "so it is taken under dual control or not at all"
            )
        moved = current.transition(target)
        store.save(moved)
        recorded = store.get(reference, moved.version)
        if recorded is None or recorded.status is not target:
            runtime.connection.rollback()
            raise VotingContextVersionFrozenError(
                "the registry did not record the status change: an activated version is "
                "immutable, and a change to one is a new version"
            )
        runtime.connection.commit()
        return {
            "voting_context_reference": reference,
            "version": moved.version,
            "status": recorded.status.value,
            "previous_status": current.status.value,
        }

    dispatcher = ApiDispatcher(
        catalogue=VOTING_CONTEXT_CATALOGUE,
        handlers={
            "voting_context.draft": draft,
            "voting_context.configure": configure,
            "voting_context.activate": activate,
            "voting_context.read": read,
            "voting_context.transition": transition,
        },
        allowed_origins=allowed_origins,
    )
    return VotingContextApi(runtime=runtime, dispatcher=dispatcher)
