"""Provider-neutral models used to close the API layer without redesigning it."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


class FailureMode(StrEnum):
    FAIL_CLOSED = "FAIL_CLOSED"
    DEGRADED_READ_ONLY = "DEGRADED_READ_ONLY"
    RETRYABLE_FAILURE = "RETRYABLE_FAILURE"
    SAFE_REJECTION = "SAFE_REJECTION"


@dataclass(frozen=True)
class ApiError(Exception):
    code: str
    reason: str
    http_status: int
    retryable: bool = False
    user_safe_message: str = "The request could not be completed."
    correlation_ref: str | None = None
    audit_ref: str | None = None

    def public(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "reason": self.reason,
            "http_status": self.http_status,
            "retryable": self.retryable,
            "user_safe_message": self.user_safe_message,
            "correlation_ref": self.correlation_ref,
            "audit_ref": self.audit_ref,
        }


@dataclass(frozen=True)
class AuthoritySnapshot:
    principal_id: str
    audience: str
    authorities: frozenset[str]
    organization_scope: str
    region_scope: str
    issued_at: datetime
    expires_at: datetime
    generation: int
    revoked: bool = False
    session_valid: bool = True
    service_identity: str | None = None
    credential_fingerprint: str | None = None


@dataclass(frozen=True)
class RequestContext:
    authority: AuthoritySnapshot | None
    now: datetime
    headers: Mapping[str, str] = field(default_factory=dict)
    body_size: int = 0
    json_depth: int = 0
    content_type: str = "application/json"


@dataclass(frozen=True)
class EndpointPolicy:
    route_id: str
    method: str
    required_authority: str | None
    audience: str
    organization_scope: str | None = None
    region_scope: str | None = None
    mutation: bool = False
    commit_time_reauthorization: bool = False
    idempotency_required: bool = False
    max_body_bytes: int = 0
    max_json_depth: int = 16
    allowed_fields: frozenset[str] = frozenset()
    server_owned_fields: frozenset[str] = frozenset(
        {
            "role",
            "authority",
            "verified",
            "approved",
            "status",
            "is_admin",
            "region_scope",
            "audit_state",
        }
    )
    trusted_proxy: bool = False
    failure_mode: FailureMode = FailureMode.FAIL_CLOSED
