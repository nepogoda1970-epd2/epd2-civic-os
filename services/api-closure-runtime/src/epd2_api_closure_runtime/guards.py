"""Fail-closed closure guards for representative reachable API paths."""

from __future__ import annotations

import hashlib
import json
import threading
from collections.abc import Callable, Mapping
from dataclasses import replace
from datetime import datetime
from typing import Any

from .models import ApiError, AuthoritySnapshot, EndpointPolicy, RequestContext

SPOOFABLE_IDENTITY_HEADERS = frozenset(
    {"x-user", "x-role", "x-member-id", "x-region", "x-forwarded-for"}
)


class MonotonicAuthorityClock:
    """Prevents a wall-clock rollback from resurrecting authority."""

    def __init__(self) -> None:
        self._high_watermark: datetime | None = None
        self._lock = threading.Lock()

    def observe(self, now: datetime) -> datetime:
        with self._lock:
            if self._high_watermark is None or now > self._high_watermark:
                self._high_watermark = now
            return self._high_watermark


class IdempotencyLedger:
    """Thread-safe exactly-once-equivalent ledger bound to request payload."""

    def __init__(self) -> None:
        self._rows: dict[tuple[str, str], tuple[str, Any]] = {}
        self._lock = threading.Lock()

    @staticmethod
    def digest(payload: Mapping[str, Any]) -> str:
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(canonical.encode()).hexdigest()

    def execute(
        self,
        principal_id: str,
        key: str,
        payload: Mapping[str, Any],
        operation: Callable[[], Any],
    ) -> tuple[Any, bool]:
        digest = self.digest(payload)
        with self._lock:
            existing = self._rows.get((principal_id, key))
            if existing:
                if existing[0] != digest:
                    raise ApiError("IDEMPOTENCY_CONFLICT", "key reused with another payload", 409)
                return existing[1], True
            result = operation()
            self._rows[(principal_id, key)] = (digest, result)
            return result, False


class ClosureGuard:
    def __init__(self, clock: MonotonicAuthorityClock | None = None) -> None:
        self.clock = clock or MonotonicAuthorityClock()

    def validate_request(
        self,
        policy: EndpointPolicy,
        context: RequestContext,
        payload: Mapping[str, Any],
    ) -> AuthoritySnapshot | None:
        if context.content_type != "application/json" and context.body_size:
            raise ApiError("CONTENT_TYPE_UNSUPPORTED", "strict JSON required", 415)
        if context.body_size > policy.max_body_bytes:
            raise ApiError("REQUEST_TOO_LARGE", "body exceeds governed limit", 413)
        if context.json_depth > policy.max_json_depth:
            raise ApiError("JSON_TOO_DEEP", "JSON nesting exceeds governed limit", 400)
        supplied = set(payload)
        privileged = supplied & set(policy.server_owned_fields)
        if privileged:
            raise ApiError("MASS_ASSIGNMENT_REFUSED", "server-owned field supplied", 400)
        unknown = supplied - set(policy.allowed_fields)
        if unknown:
            raise ApiError("UNKNOWN_FIELD", "unknown input field", 400)
        headers = {k.lower() for k in context.headers}
        if not policy.trusted_proxy and headers & SPOOFABLE_IDENTITY_HEADERS:
            raise ApiError(
                "UNTRUSTED_IDENTITY_HEADER", "identity header outside trust boundary", 400
            )
        authority = context.authority
        if policy.required_authority is not None and authority is None:
            raise ApiError("AUTHENTICATION_REQUIRED", "missing authenticated authority", 401)
        if authority is None:
            return None
        effective_now = self.clock.observe(context.now)
        if authority.revoked or not authority.session_valid:
            raise ApiError("AUTHORITY_REVOKED", "authority is revoked or session invalid", 401)
        if effective_now < authority.issued_at or effective_now >= authority.expires_at:
            raise ApiError("AUTHORITY_EXPIRED", "authority is outside validity window", 401)
        if authority.audience != policy.audience:
            raise ApiError("WRONG_AUDIENCE", "credential audience mismatch", 403)
        if policy.required_authority not in authority.authorities:
            raise ApiError("AUTHORITY_REQUIRED", "required authority is absent", 403)
        if policy.organization_scope and authority.organization_scope != policy.organization_scope:
            raise ApiError("ORGANIZATION_SCOPE_REFUSED", "organization boundary mismatch", 403)
        if policy.region_scope and authority.region_scope != policy.region_scope:
            raise ApiError("REGION_SCOPE_REFUSED", "regional boundary mismatch", 403)
        return authority

    def reauthorize_commit(
        self,
        policy: EndpointPolicy,
        initial: AuthoritySnapshot,
        current: AuthoritySnapshot,
        now: datetime,
    ) -> None:
        if not policy.commit_time_reauthorization:
            return
        if current.principal_id != initial.principal_id or current.generation != initial.generation:
            raise ApiError("AUTHORITY_CHANGED", "authority generation changed before commit", 409)
        self.validate_request(policy, RequestContext(current, now), {})

    @staticmethod
    def safe_error(exc: Exception, correlation_ref: str) -> dict[str, Any]:
        if isinstance(exc, ApiError):
            return replace(exc, correlation_ref=correlation_ref).public()
        return ApiError(
            "INTERNAL_FAILURE",
            "internal dependency failure",
            503,
            retryable=True,
            correlation_ref=correlation_ref,
        ).public()
