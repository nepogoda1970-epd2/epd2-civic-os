from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta

import pytest
from epd2_api_closure_runtime import (
    ApiError,
    AuthoritySnapshot,
    ClosureGuard,
    EndpointPolicy,
    IdempotencyLedger,
    RequestContext,
)

NOW = datetime(2026, 9, 1, 20, tzinfo=UTC)


def authority(**changes):
    values = {
        "principal_id": "principal-1",
        "audience": "epd2.member-runtime",
        "authorities": frozenset({"membership:write"}),
        "organization_scope": "org-1",
        "region_scope": "berlin",
        "issued_at": NOW - timedelta(minutes=5),
        "expires_at": NOW + timedelta(minutes=5),
        "generation": 7,
    }
    values.update(changes)
    return AuthoritySnapshot(**values)


def policy(**changes):
    values = {
        "route_id": "membership-write",
        "method": "POST",
        "required_authority": "membership:write",
        "audience": "epd2.member-runtime",
        "organization_scope": "org-1",
        "region_scope": "berlin",
        "mutation": True,
        "commit_time_reauthorization": True,
        "idempotency_required": True,
        "max_body_bytes": 1024,
        "allowed_fields": frozenset({"application_id"}),
    }
    values.update(changes)
    return EndpointPolicy(**values)


def context(auth=None, **changes):
    values = {
        "authority": auth if auth is not None else authority(),
        "now": NOW,
        "body_size": 20,
        "json_depth": 2,
    }
    values.update(changes)
    return RequestContext(**values)


def refusal(exc: str, **auth_changes):
    with pytest.raises(ApiError) as caught:
        ClosureGuard().validate_request(
            policy(), context(authority(**auth_changes)), {"application_id": "a"}
        )
    assert caught.value.code == exc


def test_valid_bounded_authority_is_accepted():
    assert (
        ClosureGuard().validate_request(policy(), context(), {"application_id": "a"}) == authority()
    )


def test_anonymous_mutation_is_refused():
    ctx = RequestContext(None, NOW, body_size=20, json_depth=1)
    with pytest.raises(ApiError, match="AUTHENTICATION_REQUIRED"):
        ClosureGuard().validate_request(policy(), ctx, {"application_id": "a"})


def test_wrong_audience_is_refused():
    refusal("WRONG_AUDIENCE", audience="another-service")


def test_missing_authority_is_refused():
    refusal("AUTHORITY_REQUIRED", authorities=frozenset())


def test_wrong_organization_is_refused():
    refusal("ORGANIZATION_SCOPE_REFUSED", organization_scope="org-2")


def test_wrong_region_is_refused():
    refusal("REGION_SCOPE_REFUSED", region_scope="bund")


@pytest.mark.parametrize("changes", [{"revoked": True}, {"session_valid": False}])
def test_revocation_and_session_invalidation_fail_closed(changes):
    refusal("AUTHORITY_REVOKED", **changes)


def test_expired_authority_is_refused():
    refusal("AUTHORITY_EXPIRED", expires_at=NOW)


def test_future_authority_is_refused():
    refusal("AUTHORITY_EXPIRED", issued_at=NOW + timedelta(minutes=1))


def test_clock_rollback_cannot_resurrect_expired_authority():
    guard = ClosureGuard()
    guard.validate_request(
        policy(), context(now=NOW + timedelta(minutes=4)), {"application_id": "a"}
    )
    expired = authority(expires_at=NOW + timedelta(minutes=3))
    with pytest.raises(ApiError, match="AUTHORITY_EXPIRED"):
        guard.validate_request(policy(), context(expired, now=NOW), {"application_id": "a"})


def test_commit_time_reauthorization_refuses_generation_change():
    with pytest.raises(ApiError, match="AUTHORITY_CHANGED"):
        ClosureGuard().reauthorize_commit(policy(), authority(), authority(generation=8), NOW)


def test_commit_time_reauthorization_refuses_mid_request_revocation():
    with pytest.raises(ApiError, match="AUTHORITY_REVOKED"):
        ClosureGuard().reauthorize_commit(policy(), authority(), authority(revoked=True), NOW)


def test_server_owned_field_is_never_mass_assigned():
    with pytest.raises(ApiError, match="MASS_ASSIGNMENT_REFUSED"):
        ClosureGuard().validate_request(
            policy(), context(), {"application_id": "a", "is_admin": True}
        )


def test_unknown_field_is_refused():
    with pytest.raises(ApiError, match="UNKNOWN_FIELD"):
        ClosureGuard().validate_request(policy(), context(), {"application_id": "a", "extra": 1})


@pytest.mark.parametrize(
    "header", ["X-User", "X-Role", "X-Member-ID", "X-Region", "X-Forwarded-For"]
)
def test_untrusted_proxy_identity_headers_are_refused(header):
    with pytest.raises(ApiError, match="UNTRUSTED_IDENTITY_HEADER"):
        ClosureGuard().validate_request(
            policy(), context(headers={header: "spoof"}), {"application_id": "a"}
        )


def test_oversized_body_is_refused():
    with pytest.raises(ApiError, match="REQUEST_TOO_LARGE"):
        ClosureGuard().validate_request(policy(), context(body_size=1025), {"application_id": "a"})


def test_deep_json_is_refused():
    with pytest.raises(ApiError, match="JSON_TOO_DEEP"):
        ClosureGuard().validate_request(policy(), context(json_depth=17), {"application_id": "a"})


def test_content_type_confusion_is_refused():
    with pytest.raises(ApiError, match="CONTENT_TYPE_UNSUPPORTED"):
        ClosureGuard().validate_request(
            policy(), context(content_type="text/plain"), {"application_id": "a"}
        )


def test_idempotent_retry_returns_one_effect():
    ledger = IdempotencyLedger()
    effects = []

    def operation():
        effects.append("created")
        return {"id": "m-1"}

    first, replayed_1 = ledger.execute("p", "key", {"a": 1}, operation)
    second, replayed_2 = ledger.execute("p", "key", {"a": 1}, operation)
    assert first == second == {"id": "m-1"}
    assert (replayed_1, replayed_2) == (False, True)
    assert effects == ["created"]


def test_idempotency_key_is_payload_bound():
    ledger = IdempotencyLedger()
    ledger.execute("p", "key", {"a": 1}, lambda: "first")
    with pytest.raises(ApiError, match="IDEMPOTENCY_CONFLICT"):
        ledger.execute("p", "key", {"a": 2}, lambda: "second")


def test_concurrent_duplicate_mutation_has_one_effect():
    ledger = IdempotencyLedger()
    effects = []

    def attempt():
        return ledger.execute("p", "key", {"a": 1}, lambda: effects.append(1) or "ok")

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: attempt(), range(20)))
    assert effects == [1]
    assert sum(replayed for _, replayed in results) == 19


def test_unexpected_error_is_redacted_and_retryable():
    body = ClosureGuard.safe_error(RuntimeError("SQL password=/tmp/key"), "corr-1")
    assert body["code"] == "INTERNAL_FAILURE"
    assert body["retryable"] is True
    assert "SQL" not in str(body) and "/tmp" not in str(body)


def test_governed_error_is_public_but_contains_no_exception_detail():
    body = ClosureGuard.safe_error(ApiError("REFUSED", "bounded refusal", 403), "corr-2")
    assert body["http_status"] == 403
    assert body["correlation_ref"] == "corr-2"
    assert set(body) == {
        "code",
        "reason",
        "http_status",
        "retryable",
        "user_safe_message",
        "correlation_ref",
        "audit_ref",
    }
