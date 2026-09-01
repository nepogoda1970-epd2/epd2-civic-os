"""Shared, transport-agnostic API contract primitives.

PACK-14 built this shape inside `identity-service` (`api.py` for the
catalogue, `service_api.py` for the adapter). PACK-15 needs the same
discipline in four services at once, and
`tests/repository/test_service_boundaries.py` forbids one service
importing another, so the generic half lives here - `epd2-core` is the
shared library every service already depends on, so no boundary is
crossed and nothing is written four times.

What is generic and lives here: the endpoint spec and its obligations,
the request and response values, the response-safety scan, and the
dispatcher skeleton. What stays per service: the **endpoint list** and the
handlers, which are that service's own contract.

There is deliberately no HTTP framework. This repository has none, adding
one would change `uv.lock` (which CI installs `--frozen`), and the
security-relevant work is not in the socket. `ApiRequest` and
`ApiResponse` are plain values, so a deployment binds ASGI, WSGI or a
queue consumer around `dispatch` without any of the checks below moving.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

API_VERSION = "v1"


class ApiContractError(ValueError):
    """A malformed endpoint declaration. Raised at import time."""


class UnknownApiOperationError(LookupError):
    """An operation that is not in the closed catalogue."""

    reason_code = "API_OPERATION_UNKNOWN"


class ApiRequestMalformedError(ValueError):
    reason_code = "API_REQUEST_MALFORMED"


class OriginNotAllowedError(PermissionError):
    reason_code = "API_ORIGIN_REFUSED"


class IdempotencyKeyRequiredError(ValueError):
    reason_code = "API_IDEMPOTENCY_KEY_REQUIRED"


class ResourceVersionRequiredError(ValueError):
    reason_code = "API_VERSION_CHECK_REQUIRED"


class ApiResponseUnsafeError(RuntimeError):
    """A response body carried a field no response may carry.

    Raised rather than filtered: a response that has to be scrubbed on the
    way out was built by code that had the value in hand, and silently
    dropping it hides that.
    """

    reason_code = "VOTING_BOUNDARY_INTEGRITY_VIOLATION"


class TrustSide(StrEnum):
    """Which side of the voting trust boundary an endpoint serves.

    Not decoration: `assert_no_endpoint_spans_the_boundary` uses it to
    refuse a single operation that reads identity-side and voting-side
    state, which is how a convenience endpoint would become the join
    nobody wrote in SQL.
    """

    IDENTITY = "identity"
    VOTING = "voting"
    #: Administrative configuration and neutral audit surfaces, which
    #: hold facts about a context and never about a participation.
    NEUTRAL = "neutral"


@dataclass(frozen=True, slots=True)
class EndpointSpec:
    """One contract-level endpoint.

    `consequential` is not a comment: it drives
    `assert_consequential_contract`, which refuses a spec that calls
    itself consequential and then waives an obligation. That is the only
    way "every consequential endpoint requires an idempotency key"
    survives the tenth endpoint somebody adds in a hurry.

    There are no defaults for the four obligation fields, so a new
    endpoint has to state all of them.
    """

    operation: str
    area: str
    trust_side: TrustSide
    consequential: bool
    idempotency_key_required: bool
    version_check_required: bool
    audit_evidence_required: bool
    authorized_roles: tuple[str, ...]
    reason_codes: tuple[str, ...]
    #: Set only where a consequential endpoint is genuinely reachable
    #: without an authenticated session, with the reason stated - so the
    #: exemption is a decision on the record rather than a forgotten
    #: field.
    unauthenticated_by_design: bool = False
    justification: str = ""

    def __post_init__(self) -> None:
        if not self.operation:
            raise ApiContractError("an endpoint spec names its operation")
        if not self.reason_codes:
            raise ApiContractError(
                f"{self.operation} must enumerate the registered reason codes it may return"
            )
        if not self.authorized_roles:
            raise ApiContractError(
                f"{self.operation} must name the roles permitted to call it; "
                "an endpoint open to every role is an endpoint nobody scoped"
            )
        if self.unauthenticated_by_design and not self.justification:
            raise ApiContractError(
                f"{self.operation} claims to be unauthenticated by design and must say why"
            )


def assert_consequential_contract(spec: EndpointSpec) -> None:
    """A consequential endpoint waives nothing."""
    if not spec.consequential:
        return
    missing = [
        name
        for name in (
            "idempotency_key_required",
            "version_check_required",
            "audit_evidence_required",
        )
        if not getattr(spec, name)
    ]
    if missing:
        raise ApiContractError(
            f"{spec.operation} is consequential and may not waive: {', '.join(missing)}"
        )


def assert_no_endpoint_spans_the_boundary(specs: Sequence[EndpointSpec]) -> None:
    """No operation name may exist on both sides of the boundary.

    One operation served by both an identity-side and a voting-side
    catalogue is a single call that reads both, which is the correlation
    ADR-093 forbids - arrived at through routing rather than through SQL.
    """
    by_operation: dict[str, TrustSide] = {}
    for spec in specs:
        existing = by_operation.get(spec.operation)
        if existing is not None and existing is not spec.trust_side:
            raise ApiContractError(
                f"{spec.operation} is declared on both the {existing.value} and the "
                f"{spec.trust_side.value} side"
            )
        by_operation[spec.operation] = spec.trust_side


def build_catalogue(specs: Sequence[EndpointSpec]) -> Mapping[str, EndpointSpec]:
    """Validate a service's endpoint list and index it by operation."""
    catalogue: dict[str, EndpointSpec] = {}
    for spec in specs:
        if spec.operation in catalogue:
            raise ApiContractError(f"{spec.operation} is declared twice")
        assert_consequential_contract(spec)
        catalogue[spec.operation] = spec
    assert_no_endpoint_spans_the_boundary(specs)
    return catalogue


@dataclass(frozen=True, slots=True)
class ApiRequest:
    """A parsed request. Transport-agnostic by construction."""

    operation: str
    origin: str
    body: Mapping[str, Any] = field(default_factory=dict)
    actor_role: str = ""
    idempotency_key: str | None = None
    expected_version: int | None = None
    #: Present only on the voting side, and only inside the isolated
    #: voting origin. Never an account or a session (ADR-088).
    capability: str | None = None

    def require(self, name: str) -> Any:
        if name not in self.body:
            raise ApiRequestMalformedError(f"{self.operation} requires {name!r}")
        return self.body[name]


@dataclass(frozen=True, slots=True)
class ApiResponse:
    """A reason-coded response. `ok=False` always carries a reason code."""

    operation: str
    ok: bool
    body: Mapping[str, Any] = field(default_factory=dict)
    reason_code: str | None = None
    api_version: str = API_VERSION

    def __post_init__(self) -> None:
        if not self.ok and not self.reason_code:
            raise ApiContractError("a refusal always carries a registered reason code")


#: Never present in any response body, in any service, under any name or
#: nesting. The union of the identity fields, the ballot fields and the
#: two references whose co-occurrence is the ADR-093 pairing.
PROHIBITED_RESPONSE_KEYS: frozenset[str] = frozenset(
    {
        "account_id",
        "person_id",
        "person_record_id",
        "identity_record_id",
        "membership_id",
        "member_number",
        "email",
        "phone",
        "full_name",
        "date_of_birth",
        "address",
        "communication_persona_id",
        "eid_subject",
        "session_id",
        "device_id",
        "context_pseudonym",
        "pseudonym",
        "credential_secret",
        "ballot_id",
        "vote_content",
        "password",
        "password_hash",
        "recovery_code",
    }
)

#: The two reference families whose co-occurrence in one payload is the
#: link ADR-093 forbids.
_ASSERTION_KEYS = frozenset({"assertion_id", "assertion_reference", "nonce"})
_CREDENTIAL_KEYS = frozenset(
    {"voting_credential_id", "credential_id", "credential_reference", "redemption_reference"}
)


def _walk(node: object, path: str = "") -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    if isinstance(node, Mapping):
        for key, value in node.items():
            here = f"{path}.{key}" if path else str(key)
            found.append((str(key), here))
            found.extend(_walk(value, here))
    elif isinstance(node, (list, tuple)):
        for index, value in enumerate(node):
            found.extend(_walk(value, f"{path}[{index}]"))
    return found


def assert_response_safe(body: Mapping[str, Any]) -> None:
    """Refuse a response body that carries what an event may not carry.

    Two rules, applied at every nesting depth:

    1. no prohibited key, and
    2. no payload holding both an assertion reference and a credential
       reference - the pairing is forbidden in a response for exactly the
       reason it is forbidden in a store.
    """
    seen = _walk(body)
    offending = sorted({key for key, _ in seen if key in PROHIBITED_RESPONSE_KEYS})
    if offending:
        raise ApiResponseUnsafeError("a response may not carry: " + ", ".join(offending))
    keys = {key for key, _ in seen}
    if keys & _ASSERTION_KEYS and keys & _CREDENTIAL_KEYS:
        raise ApiResponseUnsafeError(
            "a response may never carry both an assertion reference and a credential reference"
        )


Handler = Callable[[ApiRequest], Mapping[str, Any]]


@dataclass(frozen=True, slots=True)
class ApiDispatcher:
    """The adapter skeleton, shared by all four PACK-15 services.

    Every request passes through the same six steps, in this order:

    1. **Operation lookup** against the closed catalogue.
    2. **Origin validation** against the endpoint's declared origins.
    3. **Role authorization** against the endpoint's declared roles.
    4. **Idempotency and version fields**, refused at the boundary rather
       than trusted.
    5. **The handler**, which is the service's own governed command.
    6. **Response safety**, so a response cannot carry what an event
       would have been refused for.

    A refusal is reason-coded and never carries the refused value back.
    """

    catalogue: Mapping[str, EndpointSpec]
    handlers: Mapping[str, Handler]
    allowed_origins: tuple[str, ...]

    def __post_init__(self) -> None:
        missing = sorted(set(self.catalogue) - set(self.handlers))
        if missing:
            raise ApiContractError("declared endpoints with no handler: " + ", ".join(missing))
        unrouted = sorted(set(self.handlers) - set(self.catalogue))
        if unrouted:
            raise ApiContractError("handlers for undeclared operations: " + ", ".join(unrouted))

    def dispatch(self, request: ApiRequest) -> ApiResponse:
        spec = self.catalogue.get(request.operation)
        if spec is None:
            return ApiResponse(
                operation=request.operation,
                ok=False,
                reason_code=UnknownApiOperationError.reason_code,
            )
        try:
            self._assert_origin(request)
            self._assert_role(spec, request)
            self._assert_obligations(spec, request)
            body = self.handlers[spec.operation](request)
            assert_response_safe(body)
        except Exception as error:
            reason_code = getattr(error, "reason_code", None)
            if reason_code is None:
                raise
            return ApiResponse(operation=spec.operation, ok=False, reason_code=str(reason_code))
        return ApiResponse(operation=spec.operation, ok=True, body=body)

    def _assert_origin(self, request: ApiRequest) -> None:
        if request.origin not in self.allowed_origins:
            raise OriginNotAllowedError("the request origin is not one this boundary serves")

    def _assert_role(self, spec: EndpointSpec, request: ApiRequest) -> None:
        if spec.unauthenticated_by_design and not request.actor_role:
            return
        if request.actor_role not in spec.authorized_roles:
            raise OriginNotAllowedError(f"{spec.operation} is not available to this role")

    def _assert_obligations(self, spec: EndpointSpec, request: ApiRequest) -> None:
        if spec.idempotency_key_required and not request.idempotency_key:
            raise IdempotencyKeyRequiredError(
                f"{spec.operation} is consequential and requires an idempotency key"
            )
        if spec.version_check_required and request.expected_version is None:
            raise ResourceVersionRequiredError(
                f"{spec.operation} requires the resource version it expects to act on"
            )
