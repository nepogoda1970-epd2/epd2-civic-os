"""PACK-14 runnable service boundary tests.

The adapter is exercised end to end against the **durable** reference
persistence path: every request below goes through parsing, origin
validation, session context, idempotency and version checks, a
transaction, the governed command, and serialization.
"""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from uuid import uuid4

import pytest
from _pack14_builders import NOW, SALT, account_id, device, new_session_id, scope

from epd2_core.clock import FixedClock
from epd2_identity_service.api import ENDPOINTS_BY_OPERATION
from epd2_identity_service.assurance import AuthenticationMethod
from epd2_identity_service.exceptions import (
    ApiRequestMalformedError,
    IdempotencyKeyRequiredError,
    OriginNotAllowedError,
    ResourceVersionRequiredError,
    SecretInPayloadRefusedError,
    SessionContextRequiredError,
    UnknownApiOperationError,
)
from epd2_identity_service.identifiers import PROHIBITED_IDENTIFIER_KEYS, PROHIBITED_SECRET_KEYS
from epd2_identity_service.runtime import IdentityRuntime, build_identity_service
from epd2_identity_service.secret_storage import DeterministicSecureRandom
from epd2_identity_service.service_api import (
    CONTRACT_ONLY_OPERATIONS,
    ROUTED_OPERATIONS,
    ApiRequest,
    ApiResponse,
    IdentityServiceApi,
    SessionContext,
)
from epd2_identity_service.workspaces import WorkspaceId, workspace_origin

MEMBER_ORIGIN = workspace_origin(WorkspaceId.MEMBER_APPLICATION)
VOTING_ORIGIN = workspace_origin(WorkspaceId.VOTING_CLIENT)
UNIT = "11111111-1111-4111-8111-111111111111"


def _runtime(database: str = ":memory:") -> IdentityRuntime:
    return build_identity_service(
        clock=FixedClock(NOW),
        derivation_salt=SALT,
        database=database,
        random=DeterministicSecureRandom(),
    )


def _create(
    api: IdentityServiceApi, account: str = "22222222-2222-4222-8222-222222222222"
) -> ApiResponse:
    response: ApiResponse = api.dispatch(
        ApiRequest(
            operation="account.create",
            origin=MEMBER_ORIGIN,
            body={"account_id": account, "scope_level": "land", "scope_unit_id": UNIT},
            idempotency_key=f"create-{account}",
            expected_version=1,
        )
    )
    return response


# --- routing ----------------------------------------------------------------


def test_the_routing_table_is_a_subset_of_the_catalogue_and_names_the_rest() -> None:
    assert set(ENDPOINTS_BY_OPERATION) >= ROUTED_OPERATIONS
    assert ROUTED_OPERATIONS.isdisjoint(CONTRACT_ONLY_OPERATIONS)
    assert set(ENDPOINTS_BY_OPERATION) == ROUTED_OPERATIONS | CONTRACT_ONLY_OPERATIONS
    assert ROUTED_OPERATIONS


def test_an_unrouted_operation_is_refused_rather_than_dispatched_by_name() -> None:
    runtime = _runtime()
    with pytest.raises(UnknownApiOperationError):
        runtime.api.dispatch(ApiRequest(operation="account.invented", origin=MEMBER_ORIGIN))
    for operation in sorted(CONTRACT_ONLY_OPERATIONS)[:3]:
        with pytest.raises(UnknownApiOperationError):
            runtime.api.dispatch(ApiRequest(operation=operation, origin=MEMBER_ORIGIN))
    runtime.connection.close()


# --- envelope validation ----------------------------------------------------


def test_a_request_from_an_undeclared_origin_is_refused() -> None:
    """Envelope refusals come back as reason-coded responses, not as
    exceptions: the boundary's job is to answer, and an answer with a
    registered code is what an operator can act on."""
    runtime = _runtime()
    response = runtime.api.dispatch(
        ApiRequest(
            operation="account.create",
            origin="https://evil.test",
            body={"account_id": str(uuid4()), "scope_level": "land", "scope_unit_id": UNIT},
            idempotency_key="k",
        )
    )
    assert response.status == "refused"
    assert response.reason_code == OriginNotAllowedError.reason_code
    runtime.connection.close()


def test_a_consequential_operation_without_an_idempotency_key_is_refused() -> None:
    runtime = _runtime()
    response = runtime.api.dispatch(
        ApiRequest(
            operation="account.create",
            origin=MEMBER_ORIGIN,
            body={"account_id": str(uuid4()), "scope_level": "land", "scope_unit_id": UNIT},
        )
    )
    assert response.status == "refused"
    assert response.reason_code == IdempotencyKeyRequiredError.reason_code
    runtime.connection.close()


def test_an_operation_requiring_a_session_refuses_without_one() -> None:
    runtime = _runtime()
    response = runtime.api.dispatch(
        ApiRequest(
            operation="sessions.revoke_all",
            origin=MEMBER_ORIGIN,
            body={"account_id": str(uuid4())},
            idempotency_key="k",
            expected_version=1,
        )
    )
    assert response.status == "refused"
    assert response.reason_code == SessionContextRequiredError.reason_code
    runtime.connection.close()


def test_a_versioned_operation_refuses_without_an_expected_version() -> None:
    runtime = _runtime()
    response = runtime.api.dispatch(
        ApiRequest(
            operation="sessions.revoke_all",
            origin=MEMBER_ORIGIN,
            body={"account_id": str(uuid4())},
            idempotency_key="k",
            session=SessionContext(session_id=new_session_id()),
        )
    )
    assert response.status == "refused"
    assert response.reason_code == ResourceVersionRequiredError.reason_code
    runtime.connection.close()


def test_a_malformed_body_is_refused_before_any_domain_code_runs() -> None:
    runtime = _runtime()
    response = runtime.api.dispatch(
        ApiRequest(
            operation="account.create",
            origin=MEMBER_ORIGIN,
            body={"scope_level": "land", "scope_unit_id": UNIT},
            idempotency_key="k",
            expected_version=1,
        )
    )
    assert response.status == "refused"
    assert response.reason_code == "API_REQUEST_MALFORMED"
    with pytest.raises(ApiRequestMalformedError):
        ApiResponse(status="teapot", reason_code="X")
    runtime.connection.close()


# --- successful dispatch ----------------------------------------------------


def test_the_account_lifecycle_runs_end_to_end_through_the_adapter() -> None:
    runtime = _runtime()
    account = "22222222-2222-4222-8222-222222222222"
    created = _create(runtime.api, account)
    assert created.status == "ok"
    assert created.body["account_status"] == "pending"

    added = runtime.api.dispatch(
        ApiRequest(
            operation="contacts.add",
            origin=MEMBER_ORIGIN,
            body={"account_id": account, "channel": "email", "value": "anna@epd.example"},
            session=SessionContext(session_id=new_session_id()),
            idempotency_key="add-1",
            expected_version=1,
        )
    )
    assert added.status == "ok"
    assert added.body["masked"] == "a***@e***.example"

    verified = runtime.api.dispatch(
        ApiRequest(
            operation="contacts.verify",
            origin=MEMBER_ORIGIN,
            body={"contact_reference": added.body["contact_reference"]},
            session=SessionContext(session_id=new_session_id()),
            idempotency_key="verify-1",
            expected_version=1,
        )
    )
    assert verified.body["status"] == "verified"

    activated = runtime.api.dispatch(
        ApiRequest(
            operation="account.activate",
            origin=MEMBER_ORIGIN,
            body={"account_id": account},
            session=SessionContext(session_id=new_session_id()),
            idempotency_key="activate-1",
            expected_version=1,
        )
    )
    assert activated.body["account_status"] == "active"

    state = runtime.api.dispatch(
        ApiRequest(
            operation="account.get_security_state",
            origin=MEMBER_ORIGIN,
            body={"account_id": account},
            session=SessionContext(session_id=new_session_id()),
        )
    )
    assert state.body["activated"] is True
    runtime.connection.close()


def test_every_response_carries_a_reason_code_on_success_too() -> None:
    runtime = _runtime()
    created = _create(runtime.api)
    assert created.reason_code == "ACCOUNT_CREATED_RECORDED"
    assert created.status == "ok"
    runtime.connection.close()


def test_a_domain_refusal_becomes_a_reason_coded_response_not_an_exception() -> None:
    runtime = _runtime()
    account = "22222222-2222-4222-8222-222222222222"
    _create(runtime.api, account)
    response = runtime.api.dispatch(
        ApiRequest(
            operation="account.activate",
            origin=MEMBER_ORIGIN,
            body={"account_id": account},
            session=SessionContext(session_id=new_session_id()),
            idempotency_key="a",
            expected_version=1,
        )
    )
    assert response.status == "refused"
    assert response.reason_code == "CONTACT_NOT_VERIFIED"
    assert response.retryable is False
    runtime.connection.close()


def test_a_failed_dispatch_rolls_back_and_leaves_no_partial_state() -> None:
    runtime = _runtime()
    account = "22222222-2222-4222-8222-222222222222"
    _create(runtime.api, account)
    response = runtime.api.dispatch(
        ApiRequest(
            operation="contacts.add",
            origin=MEMBER_ORIGIN,
            body={"account_id": account, "channel": "email", "value": "not-an-address"},
            session=SessionContext(session_id=new_session_id()),
            idempotency_key="bad-1",
            expected_version=1,
        )
    )
    assert response.status == "refused"
    assert response.reason_code == "CONTACT_NOT_NORMALIZABLE"
    from uuid import UUID as _UUID

    from epd2_identity_service.identifiers import AccountId

    assert runtime.service.contact_store.for_account(AccountId(_UUID(account))) == ()
    runtime.connection.close()


# --- serialization safety ---------------------------------------------------


def test_no_response_body_can_carry_a_prohibited_key() -> None:
    for key in sorted(PROHIBITED_SECRET_KEYS)[:5]:
        with pytest.raises(SecretInPayloadRefusedError):
            ApiResponse(status="ok", reason_code="X_RECORDED", body={key: "value"})
    for key in sorted(PROHIBITED_IDENTIFIER_KEYS)[:5]:
        with pytest.raises(Exception):  # noqa: B017 - GlobalIdentifierRefusedError
            ApiResponse(status="ok", reason_code="X_RECORDED", body={key: "value"})


def test_the_session_inventory_carries_no_token_and_no_account_id() -> None:
    runtime = _runtime()
    account = "22222222-2222-4222-8222-222222222222"
    _create(runtime.api, account)
    from uuid import UUID as _UUID

    from epd2_identity_service.contacts import ContactChannelClass
    from epd2_identity_service.identifiers import AccountId

    typed_account = AccountId(_UUID(account))
    contact = runtime.service.add_contact(
        contact_id=uuid4(),
        account_id=typed_account,
        channel_class=ContactChannelClass.EMAIL,
        raw_value="anna@epd.example",
        correlation_id=uuid4(),
        event_id=uuid4(),
    )
    runtime.service.verify_contact(
        contact_id=contact.contact_id, correlation_id=uuid4(), event_id=uuid4()
    )
    runtime.service.activate_account(
        account_id=typed_account, expected_version=1, correlation_id=uuid4(), event_id=uuid4()
    )
    runtime.service.issue_session(
        session_id=new_session_id(),
        account_id=typed_account,
        workspace=WorkspaceId.MEMBER_APPLICATION,
        methods=(AuthenticationMethod.PASSKEY_DEVICE_BOUND,),
        credential_binding="device_bound",
        device=device(),
        correlation_id=uuid4(),
        event_id=uuid4(),
    )
    listed = runtime.api.dispatch(
        ApiRequest(
            operation="sessions.list",
            origin=MEMBER_ORIGIN,
            body={"account_id": account},
            session=SessionContext(session_id=new_session_id()),
        )
    )
    rendered = str(listed.body)
    assert "refresh" not in rendered
    assert "csrf" not in rendered
    assert account not in rendered
    assert listed.body["sessions"][0]["device_label"] == "Laptop zu Hause"
    runtime.connection.close()


# --- audience binding -------------------------------------------------------


def test_a_voting_handoff_redemption_from_the_wrong_origin_is_refused() -> None:
    runtime = _runtime()
    response = runtime.api.dispatch(
        ApiRequest(
            operation="voting_handoff.redeem",
            origin=MEMBER_ORIGIN,
            body={
                "artifact_reference": str(uuid4()),
                "artifact": "value",
                "voting_context_id": str(uuid4()),
            },
            idempotency_key="r-1",
            expected_version=1,
        )
    )
    assert response.status == "refused"
    assert response.reason_code == "ORIGIN_NOT_ALLOWED"
    runtime.connection.close()


def test_an_unknown_artifact_is_refused_uniformly_at_the_voting_boundary() -> None:
    runtime = _runtime()
    response = runtime.api.dispatch(
        ApiRequest(
            operation="voting_handoff.redeem",
            origin=VOTING_ORIGIN,
            body={
                "artifact_reference": str(uuid4()),
                "artifact": "value",
                "voting_context_id": str(uuid4()),
            },
            idempotency_key="r-2",
            expected_version=1,
        )
    )
    assert response.status == "refused"
    assert response.reason_code == "VOTING_HANDOFF_INVALID"
    runtime.connection.close()


# --- idempotency across a restart -------------------------------------------


def test_an_idempotency_key_is_honoured_across_a_restart(tmp_path: Path) -> None:
    database = str(tmp_path / "identity.sqlite3")
    account = "22222222-2222-4222-8222-222222222222"
    first = _runtime(database)
    _create(first.api, account)
    first.connection.close()

    second = _runtime(database)
    replay = _create(second.api, account)
    assert replay.status == "ok"
    assert replay.body["version"] == 1
    from epd2_identity_service.exceptions import IdempotencyKeyReusedError

    with pytest.raises(IdempotencyKeyReusedError):
        second.service.create_account(
            account_id=account_id("33333333-3333-4333-8333-333333333333"),
            scope=scope(),
            correlation_id=uuid4(),
            event_id=uuid4(),
            idempotency_key=f"create-{account}",
        )
    second.connection.close()


def test_the_governed_defaults_are_still_the_ones_the_specification_names() -> None:
    from epd2_identity_service.account_security_application import DEFAULT_SESSION_WINDOWS

    assert DEFAULT_SESSION_WINDOWS["high"] == (timedelta(minutes=15), timedelta(hours=8))
