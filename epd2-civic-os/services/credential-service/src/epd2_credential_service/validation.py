"""Fail-closed credential validation, per pack section 6.4.

A credential is invalid if ANY of these hold: unknown status, unknown
`credential_version`, expired, missing required scope, `rule_version`
mismatch, corrupted digest, revoked, or a required field cannot be
verified. `ValidateParticipationCredential` never returns identity data
(pack section 6.3) - `ValidationResult` structurally cannot carry it.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from epd2_credential_service.domain import (
    SUPPORTED_CREDENTIAL_VERSIONS,
    CredentialStatus,
    ParticipationCredential,
    ValidationResult,
)


def validate_credential(
    credential: ParticipationCredential,
    *,
    now: datetime,
    required_scope_type: str | None = None,
    required_scope_id: UUID | None = None,
    expected_rule_version: int | None = None,
    expected_digest: str | None = None,
) -> ValidationResult:
    reasons: list[str] = []

    if credential.credential_version not in SUPPORTED_CREDENTIAL_VERSIONS:
        reasons.append("EVENT_VERSION_UNSUPPORTED")

    if credential.status == CredentialStatus.REVOKED:
        reasons.append("CREDENTIAL_REVOKED")

    if credential.status in (CredentialStatus.EXPIRED,) or now >= credential.expires_at:
        reasons.append("CREDENTIAL_EXPIRED")

    if (
        credential.status == CredentialStatus.USED
        and credential.usage_limit is not None
        and credential.usage_counter >= credential.usage_limit
    ):
        reasons.append("CREDENTIAL_ALREADY_USED")

    if required_scope_type is not None and credential.scope_type != required_scope_type:
        reasons.append("CREDENTIAL_SCOPE_MISMATCH")
    if required_scope_id is not None and credential.scope_id != required_scope_id:
        reasons.append("CREDENTIAL_SCOPE_MISMATCH")

    if expected_rule_version is not None and credential.rule_version != expected_rule_version:
        reasons.append("CREDENTIAL_RULE_VERSION_MISMATCH")

    if expected_digest is not None and credential.eligibility_snapshot_digest != expected_digest:
        reasons.append("CREDENTIAL_DIGEST_MISMATCH")

    if not credential.eligibility_snapshot_digest:
        reasons.append("CREDENTIAL_REQUIRED_FIELD_MISSING")

    # De-duplicate while preserving first-seen order (a credential could
    # trigger the same reason from more than one check above).
    unique_reasons = tuple(dict.fromkeys(reasons))

    if unique_reasons:
        return ValidationResult(
            valid=False,
            scope_type=None,
            scope_id=None,
            expires_at=None,
            reason_codes=unique_reasons,
            credential_version=credential.credential_version,
        )

    return ValidationResult(
        valid=True,
        scope_type=credential.scope_type,
        scope_id=credential.scope_id,
        expires_at=credential.expires_at,
        reason_codes=(),
        credential_version=credential.credential_version,
    )
