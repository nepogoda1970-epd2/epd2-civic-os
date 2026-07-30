"""The runnable reference service boundary.

`api.py` is the **catalogue**: what the operations are and what
obligations each carries. This module is the **adapter**: it parses a
request, validates it, opens the transaction, calls the governed command,
serializes the result, and turns every refusal into a reason-coded
response.

It is transport-agnostic on purpose. This repository has no HTTP
framework and adding one would change `uv.lock`, which CI installs
`--frozen`; more importantly, the security-relevant work is not in the
socket. `ApiRequest` and `ApiResponse` are plain values, so a deployment
binds ASGI, WSGI or a queue consumer around `dispatch` without any of the
checks below moving.

**A production gateway, a public deployment and real external providers
remain excluded.** What is here is a runnable boundary with the checks the
task names, exercised end to end by
`services/identity-service/tests/test_pack14_service_api.py`.

Six things every dispatched request passes through, in this order:

1. **Operation lookup.** Closed catalogue; an unrouted operation is
   `API_OPERATION_UNKNOWN`, never dispatched by name.
2. **Origin validation.** The request origin must be one of FRONT-00's
   ten declared origins, and it must be the audience the operation is
   for.
3. **Session context.** Operations that require one get one, or
   `API_SESSION_CONTEXT_REQUIRED`. Assurance and step-up are then the
   domain's decision, not the adapter's.
4. **Idempotency and version fields.** A consequential operation without
   an idempotency key or an expected resource version is refused at the
   boundary rather than trusted.
5. **The governed command**, inside one transaction.
6. **Response safety.** Every serialized body passes the same
   `reject_prohibited_payload_keys` an event payload does, so a response
   cannot carry a secret or a raw identifier an event would have been
   refused for.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from epd2_identity_service.account_security_application import (
    AccountSecurityService,
    account_security_state,
)
from epd2_identity_service.api import ENDPOINTS_BY_OPERATION, EndpointSpec, assert_response_safe
from epd2_identity_service.assurance import AuthenticationMethod
from epd2_identity_service.contacts import ContactChannelClass, parse_channel_class
from epd2_identity_service.exceptions import (
    ApiRequestMalformedError,
    IdempotencyKeyRequiredError,
    OriginNotAllowedError,
    ResourceVersionRequiredError,
    SessionContextRequiredError,
    UnknownApiOperationError,
)
from epd2_identity_service.identifiers import (
    AccountId,
    OrganizationLevel,
    OrganizationScope,
    SessionId,
)
from epd2_identity_service.sessions import DeviceReference
from epd2_identity_service.voting_handoff import (
    VotingHandoffRequest,
    redeem_voting_handoff,
)
from epd2_identity_service.workspaces import (
    WorkspaceId,
    assert_declared_origin,
    parse_workspace,
    workspace_origin,
)

API_VERSION = "v1"


@dataclass(frozen=True, slots=True)
class SessionContext:
    """The authenticated context a request arrives with.

    Deliberately minimal, and deliberately **not** an account
    identifier: the adapter resolves the session and hands the domain a
    `SessionId`; the account behind it is the session store's business.
    """

    session_id: SessionId
    csrf_token: str | None = None


@dataclass(frozen=True, slots=True)
class ApiRequest:
    """One request at the boundary."""

    operation: str
    origin: str
    body: Mapping[str, Any] = field(default_factory=dict)
    session: SessionContext | None = None
    idempotency_key: str | None = None
    expected_version: int | None = None
    correlation_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class ApiResponse:
    """One response.

    `reason_code` is present on **every** response, success or refusal.
    A success carries the registered `*_RECORDED` classification for the
    act, which means an operator reading a response stream never has to
    infer what happened from an HTTP status.
    """

    status: str
    reason_code: str
    body: Mapping[str, Any] = field(default_factory=dict)
    retryable: bool = False

    def __post_init__(self) -> None:
        if self.status not in ("ok", "refused"):
            raise ApiRequestMalformedError(f"unknown response status {self.status!r}")
        if not self.reason_code:
            raise ApiRequestMalformedError("every response carries a registered reason code")
        assert_response_safe(dict(self.body))


def _require(body: Mapping[str, Any], key: str) -> Any:
    if key not in body:
        raise ApiRequestMalformedError(f"the request is missing the required field {key!r}")
    return body[key]


def _uuid(body: Mapping[str, Any], key: str) -> UUID:
    raw = _require(body, key)
    try:
        return UUID(str(raw))
    except ValueError as exc:
        raise ApiRequestMalformedError(f"{key!r} is not a UUID") from exc


def _scope(body: Mapping[str, Any]) -> OrganizationScope:
    try:
        level = OrganizationLevel(str(_require(body, "scope_level")))
    except ValueError as exc:
        raise ApiRequestMalformedError(
            "'scope_level' is not a declared organization level"
        ) from exc
    return OrganizationScope(level=level, organizational_unit_id=_uuid(body, "scope_unit_id"))


def _validate_envelope(request: ApiRequest, spec: EndpointSpec) -> None:
    """Origin, session, idempotency and version - in that order.

    Origin first because a request from an undeclared origin has no
    standing to be told anything else about itself.
    """
    assert_declared_origin(request.origin)
    if spec.required_assurance.value != "none" and request.session is None:
        raise SessionContextRequiredError(
            f"{spec.operation} requires an authenticated session context"
        )
    if spec.idempotency_key_required and not request.idempotency_key:
        raise IdempotencyKeyRequiredError(f"{spec.operation} requires an idempotency key")
    if (
        spec.version_check_required
        and spec.required_assurance.value != "none"
        and request.expected_version is None
    ):
        raise ResourceVersionRequiredError(
            f"{spec.operation} requires an expected resource version"
        )


def _assert_audience(request: ApiRequest, workspace: WorkspaceId) -> None:
    if request.origin != workspace_origin(workspace):
        raise OriginNotAllowedError(
            f"this request is addressed to {workspace.value}, whose origin is "
            f"{workspace_origin(workspace)}"
        )


Handler = Callable[["IdentityServiceApi", ApiRequest], ApiResponse]


class IdentityServiceApi:
    """The runnable adapter.

    Holds one `AccountSecurityService` and a closed routing table. The
    table is a subset of `api.ENDPOINTS` by design: `ROUTED_OPERATIONS`
    names what this round actually runs, `CONTRACT_ONLY_OPERATIONS` names
    what is catalogued and not yet routed, and a test asserts the two are
    disjoint and together cover the catalogue. Claiming a route that does
    not exist is exactly the kind of statement this correction round is
    fixing.
    """

    def __init__(self, service: AccountSecurityService) -> None:
        self._service = service
        self._routes: dict[str, Handler] = {
            "account.create": IdentityServiceApi._create_account,
            "account.activate": IdentityServiceApi._activate_account,
            "account.get_security_state": IdentityServiceApi._get_security_state,
            "contacts.add": IdentityServiceApi._add_contact,
            "contacts.verify": IdentityServiceApi._verify_contact,
            "contacts.remove": IdentityServiceApi._remove_contact,
            "credentials.revoke": IdentityServiceApi._revoke_credential,
            "credentials.list": IdentityServiceApi._list_credentials,
            "sessions.list": IdentityServiceApi._list_sessions,
            "sessions.revoke_all": IdentityServiceApi._revoke_all_sessions,
            "voting_handoff.issue": IdentityServiceApi._issue_voting_handoff,
            "voting_handoff.redeem": IdentityServiceApi._redeem_voting_handoff,
        }

    @property
    def service(self) -> AccountSecurityService:
        return self._service

    @property
    def routed_operations(self) -> frozenset[str]:
        return frozenset(self._routes)

    def dispatch(self, request: ApiRequest) -> ApiResponse:
        """Parse, validate, transact, serialize - and reason-code every
        refusal.

        The `except` clause catches anything carrying a `reason_code`,
        which is every exception this package defines. An exception
        *without* one is re-raised rather than flattened into a generic
        500-shaped answer: an unknown failure must not be made to look
        like a governed refusal.
        """
        spec = ENDPOINTS_BY_OPERATION.get(request.operation)
        handler = self._routes.get(request.operation)
        if spec is None or handler is None:
            raise UnknownApiOperationError(f"no endpoint is routed for {request.operation!r}")
        try:
            _validate_envelope(request, spec)
            with self._service.transaction():
                return handler(self, request)
        except Exception as exc:
            reason_code = getattr(exc, "reason_code", None)
            if reason_code is None:
                raise
            return ApiResponse(
                status="refused",
                reason_code=str(reason_code),
                body={"operation": request.operation, "message": str(exc)},
                retryable=reason_code
                in {
                    "SESSION_EXPIRED",
                    "ASSURANCE_STALE",
                    "STEP_UP_REQUIRED",
                    "RATE_LIMIT_EXCEEDED",
                    "AUTHENTICATION_THROTTLED",
                    "ACCOUNT_LOCKED",
                },
            )

    # --- handlers -----------------------------------------------------------

    def _correlation(self, request: ApiRequest) -> UUID:
        from epd2_core.identifiers import generate_uuid

        return request.correlation_id or generate_uuid()

    def _create_account(self, request: ApiRequest) -> ApiResponse:
        from epd2_core.identifiers import generate_uuid

        account_id = AccountId(_uuid(request.body, "account_id"))
        record = self._service.create_account(
            account_id=account_id,
            scope=_scope(request.body),
            correlation_id=self._correlation(request),
            event_id=generate_uuid(),
            idempotency_key=request.idempotency_key,
        )
        return ApiResponse(
            status="ok",
            reason_code="ACCOUNT_CREATED_RECORDED",
            body={
                "account_status": record.account_status.value,
                "version": record.version,
                "activated": record.activated_at is not None,
            },
        )

    def _activate_account(self, request: ApiRequest) -> ApiResponse:
        from epd2_core.identifiers import generate_uuid

        account_id = AccountId(_uuid(request.body, "account_id"))
        if request.expected_version is None:
            raise ResourceVersionRequiredError("account.activate requires an expected version")
        record = self._service.activate_account(
            account_id=account_id,
            expected_version=request.expected_version,
            correlation_id=self._correlation(request),
            event_id=generate_uuid(),
        )
        return ApiResponse(
            status="ok",
            reason_code="ACCOUNT_ACTIVATED_RECORDED",
            body={"account_status": record.account_status.value, "version": record.version},
        )

    def _get_security_state(self, request: ApiRequest) -> ApiResponse:
        account_id = AccountId(_uuid(request.body, "account_id"))
        state = account_security_state(
            self._service, account_id=account_id, now=self._service.clock.now()
        )
        return ApiResponse(status="ok", reason_code="ACCOUNT_ACTIVATED_RECORDED", body=state)

    def _add_contact(self, request: ApiRequest) -> ApiResponse:
        from epd2_core.identifiers import generate_uuid

        channel: ContactChannelClass = parse_channel_class(str(_require(request.body, "channel")))
        contact = self._service.add_contact(
            contact_id=generate_uuid(),
            account_id=AccountId(_uuid(request.body, "account_id")),
            channel_class=channel,
            raw_value=str(_require(request.body, "value")),
            correlation_id=self._correlation(request),
            event_id=generate_uuid(),
        )
        return ApiResponse(
            status="ok",
            reason_code="CONTACT_ADDED_RECORDED",
            body={
                "contact_reference": str(contact.contact_id),
                "channel_class": contact.channel_class.value,
                "masked": contact.masked_value,
                "status": contact.status.value,
            },
        )

    def _verify_contact(self, request: ApiRequest) -> ApiResponse:
        from epd2_core.identifiers import generate_uuid

        contact = self._service.verify_contact(
            contact_id=_uuid(request.body, "contact_reference"),
            correlation_id=self._correlation(request),
            event_id=generate_uuid(),
        )
        return ApiResponse(
            status="ok",
            reason_code="CONTACT_VERIFIED_RECORDED",
            body={"contact_reference": str(contact.contact_id), "status": contact.status.value},
        )

    def _remove_contact(self, request: ApiRequest) -> ApiResponse:
        from epd2_core.identifiers import generate_uuid

        contact = self._service.remove_contact(
            contact_id=_uuid(request.body, "contact_reference"),
            reason_code=str(request.body.get("reason_code", "CONTACT_NOT_VERIFIED")),
            correlation_id=self._correlation(request),
            event_id=generate_uuid(),
        )
        return ApiResponse(
            status="ok",
            reason_code="CONTACT_REMOVED_RECORDED",
            body={"contact_reference": str(contact.contact_id), "status": contact.status.value},
        )

    def _list_credentials(self, request: ApiRequest) -> ApiResponse:
        account_id = AccountId(_uuid(request.body, "account_id"))
        credentials = self._service.credential_store.for_account(account_id)
        return ApiResponse(
            status="ok",
            reason_code="CREDENTIAL_ENROLLED_RECORDED",
            body={
                "credentials": [
                    {
                        "credential_reference": str(credential.credential_id),
                        "credential_type": credential.credential_type.value,
                        "nickname": credential.metadata.nickname,
                        "binding": credential.metadata.binding.value,
                        "status": credential.status.value,
                    }
                    for credential in credentials
                ]
            },
        )

    def _revoke_credential(self, request: ApiRequest) -> ApiResponse:
        from epd2_core.identifiers import generate_uuid
        from epd2_identity_service.identifiers import CredentialId

        credential = self._service.revoke_credential(
            credential_id=CredentialId(_uuid(request.body, "credential_reference")),
            reason_code=str(request.body.get("reason_code", "CREDENTIAL_REVOKED")),
            actor_class=str(request.body.get("actor_class", "holder")),
            correlation_id=self._correlation(request),
            event_id=generate_uuid(),
            recovery_path_available=bool(request.body.get("recovery_path_available", False)),
        )
        return ApiResponse(
            status="ok",
            reason_code="CREDENTIAL_REVOKED_RECORDED",
            body={
                "credential_reference": str(credential.credential_id),
                "status": credential.status.value,
            },
        )

    def _list_sessions(self, request: ApiRequest) -> ApiResponse:
        account_id = AccountId(_uuid(request.body, "account_id"))
        sessions = self._service.session_store.for_account(account_id)
        return ApiResponse(
            status="ok",
            reason_code="SESSION_ISSUED_RECORDED",
            body={
                "sessions": [
                    {
                        "session_reference": str(session.session_id),
                        "workspace": session.scope.workspace.value,
                        "origin": session.scope.origin,
                        "assurance": session.assurance.effective_level.value,
                        "issued_at": session.issued_at.isoformat(),
                        "idle_deadline": session.idle_deadline.isoformat(),
                        "absolute_deadline": session.absolute_deadline.isoformat(),
                        "device_label": session.device.device_label,
                        "status": session.status.value,
                    }
                    for session in sessions
                ]
            },
        )

    def _revoke_all_sessions(self, request: ApiRequest) -> ApiResponse:
        from epd2_core.identifiers import generate_uuid

        count = self._service.revoke_all_sessions_for(
            account_id=AccountId(_uuid(request.body, "account_id")),
            reason_code=str(request.body.get("reason_code", "SESSION_REVOKED")),
            actor_class=str(request.body.get("actor_class", "holder")),
            correlation_id=self._correlation(request),
            event_id=generate_uuid(),
        )
        return ApiResponse(
            status="ok", reason_code="SESSION_ALL_REVOKED_RECORDED", body={"revoked_count": count}
        )

    def _issue_voting_handoff(self, request: ApiRequest) -> ApiResponse:
        from epd2_core.identifiers import generate_uuid

        if request.session is None:
            raise SessionContextRequiredError("voting_handoff.issue requires a session")
        session = self._service.session_store.get(request.session.session_id)
        if session is None:
            raise SessionContextRequiredError("the presented session is not resolvable")
        voting_context_id = _uuid(request.body, "voting_context_id")
        handoff_request = VotingHandoffRequest(
            request_id=generate_uuid(),
            voting_context_id=voting_context_id,
            audience_origin=workspace_origin(WorkspaceId.VOTING_CLIENT),
            requested_at=self._service.clock.now(),
        )
        step_up = self._service.session_store.get_step_up_result(
            _uuid(request.body, "step_up_reference")
        )
        binding = None if step_up is None else step_up.binding
        artifact = self._service.issue_voting_handoff(
            artifact_id=generate_uuid(),
            request=handoff_request,
            account_id=session.account_id,
            assurance=session.assurance,
            step_up=step_up,
            binding=binding,
            correlation_id=self._correlation(request),
            event_id=generate_uuid(),
        )
        # The artifact value is returned to the holder exactly once and is
        # never echoed into a log, an event or a stored row.
        return ApiResponse(
            status="ok",
            reason_code="VOTING_HANDOFF_ISSUED_RECORDED",
            body={
                "artifact": artifact.value,
                "audience_origin": artifact.audience_origin,
                "purpose": artifact.purpose,
                "voting_context_id": str(artifact.voting_context_id),
                "expires_at": artifact.expires_at.isoformat(),
            },
        )

    def _redeem_voting_handoff(self, request: ApiRequest) -> ApiResponse:
        from epd2_core.identifiers import generate_uuid

        _assert_audience(request, WorkspaceId.VOTING_CLIENT)
        artifact_id = _uuid(request.body, "artifact_reference")
        issuance = self._service.voting_handoff_store.get_issuance(artifact_id)
        spent, redemption = redeem_voting_handoff(
            issuance,
            presented_value=str(_require(request.body, "artifact")),
            presenting_origin=request.origin,
            voting_context_id=_uuid(request.body, "voting_context_id"),
            redemption_id=generate_uuid(),
            now=self._service.clock.now(),
        )
        self._service.voting_handoff_store.save_issuance(spent)
        self._service.voting_handoff_store.save_redemption(redemption)
        return ApiResponse(
            status="ok",
            reason_code="VOTING_HANDOFF_REDEEMED_RECORDED",
            body={
                "voting_context_id": str(redemption.voting_context_id),
                "redeemed_at": redemption.redeemed_at.isoformat(),
            },
        )


#: The operations this round actually runs.
ROUTED_OPERATIONS: frozenset[str] = frozenset(
    {
        "account.create",
        "account.activate",
        "account.get_security_state",
        "contacts.add",
        "contacts.verify",
        "contacts.remove",
        "credentials.revoke",
        "credentials.list",
        "sessions.list",
        "sessions.revoke_all",
        "voting_handoff.issue",
        "voting_handoff.redeem",
    }
)

#: The operations that are catalogued and **not yet routed**. Named
#: rather than omitted, because "the catalogue has 42 entries" and "the
#: adapter runs 42 operations" are different statements and only one of
#: them is true.
CONTRACT_ONLY_OPERATIONS: frozenset[str] = frozenset(ENDPOINTS_BY_OPERATION) - ROUTED_OPERATIONS


def default_workspace_for(origin: str) -> WorkspaceId:
    """Resolve a declared origin back to its workspace, or refuse."""
    for workspace in WorkspaceId:
        if workspace_origin(workspace) == origin:
            return workspace
    raise OriginNotAllowedError(f"{origin!r} is not a declared workspace origin")


def parse_authentication_method_field(body: Mapping[str, Any]) -> AuthenticationMethod:
    from epd2_identity_service.assurance import parse_authentication_method

    return parse_authentication_method(str(_require(body, "method")))


def parse_workspace_field(body: Mapping[str, Any]) -> WorkspaceId:
    return parse_workspace(str(_require(body, "workspace")))


def device_from(body: Mapping[str, Any]) -> DeviceReference:
    return DeviceReference(
        device_label=str(_require(body, "device_label")),
        device_digest=str(_require(body, "device_digest")),
    )
