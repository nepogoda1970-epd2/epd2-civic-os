"""The voting-side versioned API: catalogue and reference adapter.

The generic half lives in `epd2_core.api_contracts`. What lives here is
the voting side's **endpoint list** and its handlers.

Three properties this catalogue exists to make structural:

* **No person-level status.** `credential.status` answers about a
  credential reference the caller already holds, and never about a
  participant. There is no search endpoint, no "has this person voted"
  endpoint, and no endpoint that takes a participant reference - because
  none can be declared without a field that does not exist on this side.
* **No identity input.** Not one endpoint accepts an account, a session,
  a membership number or a pseudonym. `PresentedAssertion` is the only
  inbound shape carrying anything from the identity side, and it is the
  closed twelve-field crossing artifact of ADR-091.
* **Origin isolation.** Every endpoint is refused from an origin other
  than the isolated voting workspace (WS-03). A credential operation
  reached from the ordinary workspace returns `API_ORIGIN_REFUSED` and is
  not redirected, because a redirect would make the ordinary workspace a
  participant in the flow.

`credential.revoke` deliberately has **no participant parameter**. A
revocation is targeted at a credential, and the interface cannot express
anything else - which is what stops "revoke this person's vote" from
being a request someone can make.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from epd2_core.api_contracts import (
    ApiDispatcher,
    ApiRequest,
    ApiRequestMalformedError,
    EndpointSpec,
    TrustSide,
    build_catalogue,
)
from epd2_credential_service.voting_credential_application import (
    PresentedAssertion,
    VotingContextTerms,
)
from epd2_credential_service.voting_credential_runtime import VotingCredentialRuntime

API_AREA_CREDENTIAL = "credential"
API_AREA_STATUS = "status"


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
    return EndpointSpec(
        operation=operation,
        area=area,
        trust_side=TrustSide.VOTING,
        consequential=consequential,
        idempotency_key_required=consequential,
        version_check_required=consequential,
        audit_evidence_required=consequential,
        authorized_roles=roles,
        reason_codes=reason_codes,
        unauthenticated_by_design=unauthenticated_by_design,
        justification=justification,
    )


CREDENTIAL_ENDPOINTS: tuple[EndpointSpec, ...] = (
    _endpoint(
        "credential.issue",
        API_AREA_CREDENTIAL,
        consequential=True,
        roles=("credential_issuer", "voting_client_operator"),
        reason_codes=(
            "CREDENTIAL_ISSUANCE_AUTHORIZED",
            "CREDENTIAL_DUPLICATE_REQUEST",
            "CREDENTIAL_ALREADY_ISSUED",
            "CREDENTIAL_ISSUANCE_WINDOW_CLOSED",
            "CREDENTIAL_CONTEXT_MISMATCH",
            "CREDENTIAL_AUDIENCE_MISMATCH",
            "CREDENTIAL_ORIGIN_REFUSED",
            "ASSERTION_INVALID",
            "ASSERTION_EXPIRED",
            "ASSERTION_ALREADY_USED",
            "ASSERTION_AUDIENCE_MISMATCH",
            "ASSERTION_CONTEXT_MISMATCH",
            "ELIGIBILITY_ASSURANCE_INSUFFICIENT",
            "DELIVERY_CHANNEL_REFUSED",
            "API_REQUEST_MALFORMED",
        ),
        unauthenticated_by_design=True,
        justification=(
            "Called from inside the isolated voting origin, which by construction has no "
            "account context. Requiring one here would recreate the link the origin removes "
            "(ADR-090)."
        ),
    ),
    _endpoint(
        "credential.revoke",
        API_AREA_CREDENTIAL,
        consequential=True,
        roles=("voting_operations_officer",),
        reason_codes=(
            "CREDENTIAL_REVOKED",
            "CREDENTIAL_ALREADY_REDEEMED",
            "CREDENTIAL_REVOCATION_CUTOFF_PASSED",
            "CREDENTIAL_NOT_FOUND",
            "DUAL_CONTROL_REQUIRED",
        ),
    ),
    _endpoint(
        "credential.redeem",
        API_AREA_CREDENTIAL,
        consequential=True,
        roles=("voting_client_operator",),
        reason_codes=(
            "CREDENTIAL_REDEEMED",
            "CREDENTIAL_ALREADY_REDEEMED",
            "CREDENTIAL_REVOKED",
            "CREDENTIAL_EXPIRED",
            "CREDENTIAL_REDEMPTION_WINDOW_CLOSED",
            "CREDENTIAL_ORIGIN_REFUSED",
            "CREDENTIAL_NOT_FOUND",
            "CREDENTIAL_REPLAY_DETECTED",
        ),
        unauthenticated_by_design=True,
        justification=(
            "Redemption happens inside the isolated voting origin. The presenter proves it "
            "holds the credential; who they are is not asked and is not knowable here."
        ),
    ),
    _endpoint(
        "credential.status",
        API_AREA_STATUS,
        consequential=False,
        roles=("voting_client_operator",),
        reason_codes=("CREDENTIAL_NOT_FOUND",),
        unauthenticated_by_design=True,
        justification=(
            "Answers only against a reference the caller already holds. An unknown reference "
            "returns the same shape as a withdrawn one, so the lookup is not an oracle."
        ),
    ),
)

CREDENTIAL_CATALOGUE: Mapping[str, EndpointSpec] = build_catalogue(CREDENTIAL_ENDPOINTS)

#: Refused as an inbound field on every voting-side endpoint. A caller
#: sending one is not accommodated by dropping it: the request is
#: refused, because whoever sent it built a client that had the value.
PROHIBITED_REQUEST_FIELDS: frozenset[str] = frozenset(
    {
        "account_id",
        "person_id",
        "person_record_id",
        "membership_id",
        "member_number",
        "participant_reference",
        "communication_persona_id",
        "context_pseudonym",
        "pseudonym",
        "session_id",
        "device_id",
        "email",
        "phone",
        "full_name",
    }
)


class IdentityFieldInVotingRequestError(RuntimeError):
    """A voting-side request carried an identity field.

    The voting side has no use for one, so a request containing one is
    either a misconfigured client or an attempt to establish the link
    ADR-093 forbids. Both are refused the same way.
    """

    reason_code = "VOTING_BOUNDARY_INTEGRITY_VIOLATION"


class RevocationDualControlRequiredError(RuntimeError):
    """A revocation arrived with one signature.

    The domain layer accepts one because it is not the layer that decides
    who signs. This boundary is, and it declares `DUAL_CONTROL_REQUIRED`
    on `credential.revoke` - a declared code no path can return is a
    contract that reads stricter than the system is.
    """

    reason_code = "DUAL_CONTROL_REQUIRED"


def _keys_at_every_depth(node: object) -> set[str]:
    """Every key name in a nested body, at any depth.

    A top-level-only scan is worth very little here: the shape a caller
    would actually send an identity field in is a nested one, because the
    inbound bodies are nested (`assertion`, `terms`). `assert_response_safe`
    walks every depth on the way out, and the way in has to match.
    """
    found: set[str] = set()
    if isinstance(node, Mapping):
        for key, value in node.items():
            found.add(str(key))
            found |= _keys_at_every_depth(value)
    elif isinstance(node, (list, tuple)):
        for value in node:
            found |= _keys_at_every_depth(value)
    return found


def assert_no_identity_field(body: Mapping[str, Any]) -> None:
    offending = sorted(_keys_at_every_depth(body) & PROHIBITED_REQUEST_FIELDS)
    if offending:
        raise IdentityFieldInVotingRequestError(
            "a voting-side request may not carry: " + ", ".join(offending)
        )


def _uuid(request: ApiRequest, name: str) -> UUID:
    try:
        return UUID(str(request.require(name)))
    except ValueError as error:
        raise ApiRequestMalformedError(f"{name} is not a well-formed identifier") from error


def _moment(request: ApiRequest, name: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(request.require(name)))
    except ValueError as error:
        raise ApiRequestMalformedError(f"{name} is not an ISO-8601 timestamp") from error
    if parsed.tzinfo is None:
        raise ApiRequestMalformedError(f"{name} must be timezone-aware")
    return parsed


def _terms(payload: Mapping[str, Any]) -> VotingContextTerms:
    try:
        return VotingContextTerms(
            voting_context_reference=str(payload["voting_context_reference"]),
            credential_type=str(payload["credential_type"]),
            audience_origin=str(payload["audience_origin"]),
            issuance_window_start=datetime.fromisoformat(str(payload["issuance_window_start"])),
            issuance_window_end=datetime.fromisoformat(str(payload["issuance_window_end"])),
            redemption_window_end=datetime.fromisoformat(str(payload["redemption_window_end"])),
            revocation_cutoff=datetime.fromisoformat(str(payload["revocation_cutoff"])),
            timestamp_granularity_seconds=int(payload["timestamp_granularity_seconds"]),
            minting_delay_min_seconds=int(payload["minting_delay_min_seconds"]),
            minting_delay_max_seconds=int(payload["minting_delay_max_seconds"]),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ApiRequestMalformedError("the voting context terms are incomplete") from error


def _presented(payload: Mapping[str, Any]) -> PresentedAssertion:
    try:
        return PresentedAssertion(
            assertion_id=UUID(str(payload["assertion_id"])),
            voting_context_reference=str(payload["voting_context_reference"]),
            eligibility_result=str(payload["eligibility_result"]),
            eligibility_class=str(payload["eligibility_class"]),
            organizational_scope=str(payload["organizational_scope"]),
            required_assurance_satisfied=bool(payload["required_assurance_satisfied"]),
            issued_at_bucket=datetime.fromisoformat(str(payload["issued_at_bucket"])),
            expires_at=datetime.fromisoformat(str(payload["expires_at"])),
            audience=str(payload["audience"]),
            purpose=str(payload["purpose"]),
            nonce=str(payload["nonce"]),
            status=str(payload["status"]),
            signature=str(payload.get("signature", "")),
            key_identifier=str(payload.get("key_identifier", "")),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ApiRequestMalformedError("the presented assertion is malformed") from error


@dataclass(frozen=True, slots=True)
class VotingCredentialApi:
    runtime: VotingCredentialRuntime
    dispatcher: ApiDispatcher

    def dispatch(self, request: ApiRequest) -> Any:
        return self.dispatcher.dispatch(request)


def build_voting_credential_api(
    runtime: VotingCredentialRuntime,
    *,
    allowed_origins: tuple[str, ...],
    canonical_message_of: Any,
) -> VotingCredentialApi:
    """Wire the voting-side catalogue to handlers over one runtime.

    `canonical_message_of` builds the byte string an assertion's
    signature is verified against. It is injected rather than imported so
    this service holds no import path to `eligibility-service`, which
    `tests/repository/test_service_boundaries.py` forbids and which would
    also be an architectural claim this side must not be able to make.
    """
    service = runtime.service

    def issue(request: ApiRequest) -> Mapping[str, Any]:
        assert_no_identity_field(request.body)
        assertion = _presented(request.require("assertion"))
        terms = _terms(request.require("terms"))
        minting_delay_seconds = int(request.require("minting_delay_seconds"))
        # A client-controlled number outside the governed window is a
        # malformed request, not a crash. The domain raises a bare
        # ValueError for it, which the dispatcher would re-raise rather
        # than reason-code, so it is bounded here where the value arrives.
        if not (
            terms.minting_delay_min_seconds
            <= minting_delay_seconds
            <= terms.minting_delay_max_seconds
        ):
            raise ApiRequestMalformedError(
                "minting_delay_seconds is outside this context's governed minting window"
            )
        credential, _event = service.issue(
            credential_id=uuid4(),
            assertion=assertion,
            terms=terms,
            origin=request.origin,
            idempotency_key=str(request.idempotency_key),
            canonical_message=canonical_message_of(assertion),
            now=_moment(request, "now"),
            minting_delay_seconds=minting_delay_seconds,
            delivery_channel=str(request.require("delivery_channel")),
            event_id=uuid4(),
            correlation_id=uuid4(),
        )
        runtime.connection.commit()
        # The nonce that authorized this issuance is deliberately absent
        # from the response: returning it beside the credential reference
        # would be the ADR-093 pairing, in a payload rather than a table.
        return {
            "voting_credential_id": str(credential.voting_credential_id),
            "status": credential.status.value,
            "expires_at": credential.expires_at.isoformat(),
        }

    def revoke(request: ApiRequest) -> Mapping[str, Any]:
        assert_no_identity_field(request.body)
        dual_control_reference = request.body.get("dual_control_reference")
        # Revoking a credential removes a participation. The domain
        # accepts a revocation without a second signature because it is
        # the wrong layer to decide who signs; the boundary is the right
        # one, and it requires four eyes rather than declaring a code no
        # path can return.
        if not dual_control_reference:
            raise RevocationDualControlRequiredError(
                "withdrawing a participation is taken under dual control or not at all"
            )
        credential, _event = service.revoke_unredeemed(
            voting_credential_id=_uuid(request, "voting_credential_id"),
            terms=_terms(request.require("terms")),
            reason_code=str(request.require("reason_code")),
            authority_role=request.actor_role,
            dual_control_reference=str(dual_control_reference),
            now=_moment(request, "now"),
            event_id=uuid4(),
            correlation_id=uuid4(),
        )
        runtime.connection.commit()
        return {
            "voting_credential_id": str(credential.voting_credential_id),
            "status": credential.status.value,
        }

    def redeem(request: ApiRequest) -> Mapping[str, Any]:
        assert_no_identity_field(request.body)
        redemption, _event = service.redeem(
            voting_credential_id=_uuid(request, "voting_credential_id"),
            terms=_terms(request.require("terms")),
            origin=request.origin,
            now=_moment(request, "now"),
            event_id=uuid4(),
            correlation_id=uuid4(),
            replay_id=uuid4(),
        )
        runtime.connection.commit()
        # The continuation capability is returned to the caller in the
        # moment and never persisted; `SqlCredentialRedemptionStore.get`
        # reads it back as `withheld` by construction.
        return {
            "redemption_reference": redemption.redemption_reference,
            "continuation_capability": redemption.continuation_capability,
        }

    def status(request: ApiRequest) -> Mapping[str, Any]:
        assert_no_identity_field(request.body)
        return service.privacy_safe_status(_uuid(request, "voting_credential_id"))

    dispatcher = ApiDispatcher(
        catalogue=CREDENTIAL_CATALOGUE,
        handlers={
            "credential.issue": issue,
            "credential.revoke": revoke,
            "credential.redeem": redeem,
            "credential.status": status,
        },
        allowed_origins=allowed_origins,
    )
    return VotingCredentialApi(runtime=runtime, dispatcher=dispatcher)
