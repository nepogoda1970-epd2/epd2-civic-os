"""Versioned API contracts, at the contract level.

Like PACK-10 through PACK-13, this round exposes **no new HTTP surface**,
so there is deliberately no `contracts/openapi/pack-14.yaml`: an OpenAPI
document describing nothing runnable would make the contract suite assert
against a fiction. What exists instead is this module - the endpoint
catalogue as data, and the request and response view models the eventual
transport will serialize.

Two things are enforced here rather than described in a document:

- **Every consequential endpoint declares its obligations.** `EndpointSpec`
  has no default for `idempotency_key_required`, `version_check_required`,
  `audit_evidence_required` or `required_assurance`; a new endpoint must
  state all four, and `assert_consequential_contract` refuses one that
  claims to be consequential while waiving any of them.
- **Every response carries only view-model fields.** `assert_response_safe`
  runs the same `reject_prohibited_payload_keys` the event builder uses,
  so an API response cannot carry a secret or a raw identifier that an
  event would have been refused for.

Errors are reason-coded, and the authentication surfaces use the uniform
public code from `authentication.py` so a response never becomes an
account-existence oracle.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from epd2_identity_service.domain import AuthenticationAssuranceLevel
from epd2_identity_service.identifiers import (
    ScopedIdentityReference,
    reject_prohibited_payload_keys,
    require_timezone,
)

API_VERSION = "v1"


class ApiArea(StrEnum):
    ACCOUNT = "account"
    CONTACTS = "contacts"
    CREDENTIALS = "credentials"
    AUTHENTICATION = "authentication"
    SESSIONS = "sessions"
    RECOVERY = "recovery"
    PROOFING = "proofing"
    BOOTSTRAP = "bootstrap"
    VOTING_HANDOFF = "voting_handoff"


@dataclass(frozen=True, slots=True)
class EndpointSpec:
    """One contract-level endpoint.

    `consequential` is not a comment: it drives
    `assert_consequential_contract`, which refuses a spec that calls
    itself consequential and then waives an obligation. That is the only
    way "all consequential endpoints require an idempotency key" survives
    the tenth endpoint somebody adds in a hurry.
    """

    operation: str
    area: ApiArea
    consequential: bool
    idempotency_key_required: bool
    version_check_required: bool
    audit_evidence_required: bool
    required_assurance: AuthenticationAssuranceLevel
    step_up_required: bool
    reason_codes: tuple[str, ...]
    #: Set only where an endpoint is consequential AND genuinely
    #: reachable without a session. Two exist - registration and voting
    #: handoff redemption - and each states why in `justification`, so the
    #: exemption is a documented decision rather than a forgotten field.
    unauthenticated_by_design: bool = False
    justification: str = ""

    def __post_init__(self) -> None:
        if not self.operation:
            raise ValueError("an endpoint spec names its operation")
        if not self.reason_codes:
            raise ValueError(
                "an endpoint spec enumerates the registered reason codes it may return"
            )
        if self.unauthenticated_by_design and not self.justification:
            raise ValueError(
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
        raise ValueError(
            f"{spec.operation} is consequential and may not waive: {', '.join(missing)}"
        )
    if spec.required_assurance is AuthenticationAssuranceLevel.NONE and not (
        spec.unauthenticated_by_design
    ):
        raise ValueError(f"{spec.operation} is consequential and requires an assurance level")


def _consequential(
    operation: str,
    area: ApiArea,
    assurance: AuthenticationAssuranceLevel,
    reason_codes: tuple[str, ...],
    *,
    step_up: bool = True,
) -> EndpointSpec:
    return EndpointSpec(
        operation=operation,
        area=area,
        consequential=True,
        idempotency_key_required=True,
        version_check_required=True,
        audit_evidence_required=True,
        required_assurance=assurance,
        step_up_required=step_up,
        reason_codes=reason_codes,
    )


def _read(
    operation: str,
    area: ApiArea,
    assurance: AuthenticationAssuranceLevel,
    reason_codes: tuple[str, ...],
) -> EndpointSpec:
    return EndpointSpec(
        operation=operation,
        area=area,
        consequential=False,
        idempotency_key_required=False,
        version_check_required=False,
        audit_evidence_required=True,
        required_assurance=assurance,
        step_up_required=False,
        reason_codes=reason_codes,
    )


_SUBSTANTIAL = AuthenticationAssuranceLevel.SUBSTANTIAL
_HIGH = AuthenticationAssuranceLevel.HIGH
_LOW = AuthenticationAssuranceLevel.LOW
_NONE = AuthenticationAssuranceLevel.NONE

_ACCOUNT_STATE_CODES = ("ACCOUNT_LOCKED", "ACCOUNT_RESTRICTED", "ACCOUNT_CLOSED")
_ASSURANCE_CODES = ("ASSURANCE_INSUFFICIENT", "ASSURANCE_STALE", "STEP_UP_REQUIRED")
_STEP_UP_CODES = ("STEP_UP_EXPIRED", "STEP_UP_OBJECT_CHANGED", "STEP_UP_BINDING_MISMATCH")

#: The catalogue. Every operation task section 25 names, and nothing
#: else - there is no "list all accounts", no "export", and no
#: administrative read-through, because the universal identity console is
#: exactly what PACK-14 does not build.
ENDPOINTS: tuple[EndpointSpec, ...] = (
    # Account
    EndpointSpec(
        operation="account.create",
        area=ApiArea.ACCOUNT,
        consequential=True,
        idempotency_key_required=True,
        version_check_required=True,
        audit_evidence_required=True,
        # Registration is reachable unauthenticated by design; its
        # consequence is bounded because a new account is `pending` and
        # can do nothing until a channel is verified.
        required_assurance=_NONE,
        step_up_required=False,
        reason_codes=("CONTACT_NOT_NORMALIZABLE", "PASSWORD_ONLY_ACCOUNT_REFUSED"),
        unauthenticated_by_design=True,
        justification=(
            "Registration is reachable without a session by definition. Its consequence "
            "is bounded: a new account is `pending` and can do nothing at all until a "
            "contact channel has been verified."
        ),
    ),
    _consequential(
        "account.activate", ApiArea.ACCOUNT, _LOW, ("CONTACT_NOT_VERIFIED",), step_up=False
    ),
    _read("account.get_security_state", ApiArea.ACCOUNT, _SUBSTANTIAL, _ASSURANCE_CODES),
    _consequential(
        "account.request_closure",
        ApiArea.ACCOUNT,
        _HIGH,
        (*_ASSURANCE_CODES, "ACCOUNT_CLOSURE_ALREADY_REQUESTED"),
    ),
    _consequential(
        "account.cancel_closure", ApiArea.ACCOUNT, _SUBSTANTIAL, ("ACCOUNT_CLOSURE_NOT_REQUESTED",)
    ),
    _consequential(
        "account.close", ApiArea.ACCOUNT, _HIGH, ("ACCOUNT_CLOSURE_NOT_REQUESTED", "ACCOUNT_CLOSED")
    ),
    _read("account.list_restrictions", ApiArea.ACCOUNT, _SUBSTANTIAL, _ACCOUNT_STATE_CODES),
    # Contacts
    _consequential(
        "contacts.add",
        ApiArea.CONTACTS,
        _SUBSTANTIAL,
        ("CONTACT_ALREADY_IN_USE", "CONTACT_NOT_NORMALIZABLE", "CONTACT_REUSE_BLOCKED"),
    ),
    _consequential(
        "contacts.verify",
        ApiArea.CONTACTS,
        _LOW,
        ("CHALLENGE_EXPIRED", "RATE_LIMIT_EXCEEDED"),
        step_up=False,
    ),
    _consequential(
        "contacts.change",
        ApiArea.CONTACTS,
        _SUBSTANTIAL,
        (*_STEP_UP_CODES, "CONTACT_ALREADY_IN_USE", "NOTIFICATION_DELIVERY_FAILED"),
    ),
    _consequential(
        "contacts.remove", ApiArea.CONTACTS, _SUBSTANTIAL, ("CONTACT_LAST_VERIFIED_CHANNEL",)
    ),
    # Credentials
    _consequential(
        "credentials.begin_passkey_enrollment",
        ApiArea.CREDENTIALS,
        _SUBSTANTIAL,
        (*_ASSURANCE_CODES, "RATE_LIMIT_EXCEEDED"),
    ),
    _consequential(
        "credentials.complete_passkey_enrollment",
        ApiArea.CREDENTIALS,
        _SUBSTANTIAL,
        (
            "PASSKEY_VERIFICATION_FAILED",
            "PASSKEY_ORIGIN_MISMATCH",
            "PASSKEY_CHALLENGE_EXPIRED",
            "PASSKEY_MALFORMED_RESPONSE",
            "CREDENTIAL_ALREADY_ENROLLED",
        ),
    ),
    _read("credentials.list", ApiArea.CREDENTIALS, _SUBSTANTIAL, _ASSURANCE_CODES),
    _consequential(
        "credentials.revoke",
        ApiArea.CREDENTIALS,
        _HIGH,
        (*_STEP_UP_CODES, "CREDENTIAL_LAST_REMAINING", "CREDENTIAL_REVOKED"),
    ),
    _consequential(
        "credentials.enroll_mfa",
        ApiArea.CREDENTIALS,
        _SUBSTANTIAL,
        ("MFA_FACTOR_ALREADY_ENROLLED", "SMS_OTP_NOT_AN_AUTHENTICATION_FACTOR"),
    ),
    _consequential(
        "credentials.verify_mfa",
        ApiArea.CREDENTIALS,
        _SUBSTANTIAL,
        ("MFA_FAILED", "MFA_FACTOR_NOT_CONFIRMED"),
        step_up=False,
    ),
    _consequential(
        "credentials.remove_mfa",
        ApiArea.CREDENTIALS,
        _SUBSTANTIAL,
        (*_STEP_UP_CODES, "MFA_FACTOR_REVOKED"),
    ),
    _consequential(
        "credentials.regenerate_recovery_codes",
        ApiArea.CREDENTIALS,
        _SUBSTANTIAL,
        (*_STEP_UP_CODES, "RECOVERY_CODE_SET_EXHAUSTED"),
    ),
    # Authentication
    EndpointSpec(
        operation="authentication.begin",
        area=ApiArea.AUTHENTICATION,
        consequential=False,
        idempotency_key_required=False,
        version_check_required=False,
        audit_evidence_required=True,
        required_assurance=_NONE,
        step_up_required=False,
        # Uniform: the only public code a failed authentication returns.
        reason_codes=("CREDENTIAL_INVALID", "RATE_LIMIT_EXCEEDED"),
    ),
    EndpointSpec(
        operation="authentication.complete",
        area=ApiArea.AUTHENTICATION,
        consequential=False,
        idempotency_key_required=False,
        version_check_required=False,
        audit_evidence_required=True,
        required_assurance=_NONE,
        step_up_required=False,
        reason_codes=("CREDENTIAL_INVALID", "MFA_REQUIRED", "RECOVERY_REQUIRED"),
    ),
    _consequential(
        "authentication.begin_step_up",
        ApiArea.AUTHENTICATION,
        _SUBSTANTIAL,
        (*_ASSURANCE_CODES, "STEP_UP_METHOD_NOT_ELIGIBLE"),
        step_up=False,
    ),
    _consequential(
        "authentication.complete_step_up",
        ApiArea.AUTHENTICATION,
        _SUBSTANTIAL,
        (*_STEP_UP_CODES, "STEP_UP_CANCELLED", "STEP_UP_ALREADY_CONSUMED"),
        step_up=False,
    ),
    # Sessions
    _read("sessions.list", ApiArea.SESSIONS, _SUBSTANTIAL, ("SESSION_EXPIRED", "SESSION_REVOKED")),
    _consequential(
        "sessions.revoke",
        ApiArea.SESSIONS,
        _SUBSTANTIAL,
        ("SESSION_REVOKED", "SESSION_SCOPE_MISMATCH"),
    ),
    _consequential(
        "sessions.revoke_all", ApiArea.SESSIONS, _SUBSTANTIAL, (*_STEP_UP_CODES, "SESSION_REVOKED")
    ),
    # Recovery
    EndpointSpec(
        operation="recovery.request",
        area=ApiArea.RECOVERY,
        consequential=False,
        idempotency_key_required=False,
        version_check_required=False,
        audit_evidence_required=True,
        required_assurance=_NONE,
        step_up_required=False,
        reason_codes=("RECOVERY_CONTACT_RECENTLY_CHANGED", "RATE_LIMIT_EXCEEDED"),
    ),
    _consequential(
        "recovery.submit_evidence_reference",
        ApiArea.RECOVERY,
        _LOW,
        ("RECOVERY_EVIDENCE_MISSING",),
        step_up=False,
    ),
    _consequential(
        "recovery.review",
        ApiArea.RECOVERY,
        _HIGH,
        ("PRIVILEGED_APPROVAL_MISSING", "SEPARATION_OF_DUTIES_VIOLATED"),
    ),
    _consequential(
        "recovery.approve",
        ApiArea.RECOVERY,
        _HIGH,
        (
            "RECOVERY_SELF_APPROVAL_REFUSED",
            "RECOVERY_DUAL_CONTROL_REQUIRED",
            "RECOVERY_COOLING_OFF_ACTIVE",
            "PRIVILEGED_APPROVAL_MISSING",
        ),
    ),
    _consequential("recovery.reject", ApiArea.RECOVERY, _HIGH, ("PRIVILEGED_APPROVAL_MISSING",)),
    _consequential(
        "recovery.complete",
        ApiArea.RECOVERY,
        _HIGH,
        ("RECOVERY_CREDENTIALS_NOT_REVOKED", "RECOVERY_RISK_ACCEPTANCE_REQUIRED"),
    ),
    _consequential(
        "recovery.dispute", ApiArea.RECOVERY, _LOW, ("RECOVERY_ALREADY_COMPLETED",), step_up=False
    ),
    # Proofing
    _consequential(
        "proofing.begin_case",
        ApiArea.PROOFING,
        _SUBSTANTIAL,
        ("IDENTITY_PROOFING_INSUFFICIENT",),
    ),
    _consequential(
        "proofing.attach_evidence_reference",
        ApiArea.PROOFING,
        _SUBSTANTIAL,
        ("IDENTITY_PROOFING_INSUFFICIENT",),
        step_up=False,
    ),
    _consequential(
        "proofing.record_decision",
        ApiArea.PROOFING,
        _HIGH,
        (
            "IDENTITY_PROOFING_INCONCLUSIVE",
            "PRIVILEGED_APPROVAL_MISSING",
            "PROOFING_DOES_NOT_APPROVE_MEMBERSHIP",
        ),
    ),
    _read("proofing.get_state", ApiArea.PROOFING, _SUBSTANTIAL, ("IDENTITY_ASSERTION_EXPIRED",)),
    # Bootstrap
    EndpointSpec(
        operation="bootstrap.create_request",
        area=ApiArea.BOOTSTRAP,
        consequential=False,
        idempotency_key_required=False,
        version_check_required=False,
        audit_evidence_required=True,
        required_assurance=_NONE,
        step_up_required=False,
        reason_codes=("BOOTSTRAP_REDIRECT_URI_INVALID", "ORIGIN_NOT_ALLOWED"),
    ),
    _consequential(
        "bootstrap.authorize",
        ApiArea.BOOTSTRAP,
        _SUBSTANTIAL,
        ("BOOTSTRAP_EXPIRED", "BOOTSTRAP_PROOF_VERIFICATION_FAILED"),
        step_up=False,
    ),
    EndpointSpec(
        operation="bootstrap.redeem",
        area=ApiArea.BOOTSTRAP,
        consequential=True,
        idempotency_key_required=True,
        version_check_required=True,
        audit_evidence_required=True,
        required_assurance=_LOW,
        step_up_required=False,
        reason_codes=(
            "BOOTSTRAP_INVALID",
            "BOOTSTRAP_AUDIENCE_MISMATCH",
            "BOOTSTRAP_ALREADY_USED",
            "BOOTSTRAP_EXPIRED",
            "BOOTSTRAP_NONCE_MISMATCH",
            "BOOTSTRAP_REPLAY_DETECTED",
        ),
    ),
    # Voting handoff
    _consequential(
        "voting_handoff.issue",
        ApiArea.VOTING_HANDOFF,
        _HIGH,
        (*_STEP_UP_CODES, "ASSURANCE_INSUFFICIENT"),
    ),
    EndpointSpec(
        operation="voting_handoff.redeem",
        area=ApiArea.VOTING_HANDOFF,
        consequential=True,
        idempotency_key_required=True,
        version_check_required=True,
        audit_evidence_required=True,
        # No assurance requirement, because there is no session on this
        # side of the boundary at all: the redeeming party is WS-03,
        # presenting an identity-free artifact.
        required_assurance=_NONE,
        step_up_required=False,
        reason_codes=(
            "VOTING_HANDOFF_INVALID",
            "VOTING_HANDOFF_ALREADY_USED",
            "VOTING_HANDOFF_EXPIRED",
            "VOTING_HANDOFF_AUDIENCE_MISMATCH",
            "VOTING_HANDOFF_PURPOSE_MISMATCH",
        ),
        unauthenticated_by_design=True,
        justification=(
            "There is no session on this side of the boundary at all. The redeeming "
            "party is WS-03 presenting an identity-free artifact, and requiring a "
            "session here would be requiring the identity ADR-088 forbids."
        ),
    ),
)

ENDPOINTS_BY_OPERATION: dict[str, EndpointSpec] = {spec.operation: spec for spec in ENDPOINTS}


@dataclass(frozen=True, slots=True)
class ApiError:
    """A reason-coded error response. There is no free-text-only
    variant."""

    reason_code: str
    message: str
    retryable: bool

    def __post_init__(self) -> None:
        if not self.reason_code:
            raise ValueError("an API error carries a registered reason code")


@dataclass(frozen=True, slots=True)
class AccountSecurityStateView:
    """The response behind `account.get_security_state`.

    Counts and classes only. No credential reference, no device
    fingerprint, no contact value - a security summary that would help an
    attacker who obtained it has failed at the one thing it is for.
    """

    account_status: str
    activated: bool
    credential_count: int
    credential_types: tuple[str, ...]
    factor_classes: tuple[str, ...]
    active_session_count: int
    lock_in_force: bool
    restriction_in_force: bool
    closure_requested: bool


@dataclass(frozen=True, slots=True)
class SessionView:
    """One row of the session inventory.

    `device_label` is the label the holder chose, and `origin` is the
    workspace origin. There is no session identifier in this view and
    none in any URL that reaches it - revocation takes an opaque
    reference in the request body.
    """

    session_reference: str
    workspace: str
    origin: str
    assurance: str
    issued_at: datetime
    idle_deadline: datetime
    absolute_deadline: datetime
    device_label: str
    current: bool

    def __post_init__(self) -> None:
        for name in ("issued_at", "idle_deadline", "absolute_deadline"):
            require_timezone(getattr(self, name), name)


@dataclass(frozen=True, slots=True)
class CredentialView:
    credential_reference: str
    credential_type: str
    nickname: str
    binding: str
    backup_eligible: bool
    created_at: datetime
    last_used_at: datetime | None
    status: str


@dataclass(frozen=True, slots=True)
class BootstrapResponseView:
    """What a workspace receives from `bootstrap.authorize`.

    The scoped actor reference and the assurance, and **no account ID**:
    no workspace learns an account identifier from a bootstrap, which is
    §11.1's rule that no account ID is exposed to an unrelated origin
    beyond the permitted scoped reference.
    """

    actor_reference: ScopedIdentityReference
    achieved_assurance: str
    audience_origin: str
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class VotingHandoffView:
    """What the caller receives from `voting_handoff.issue`.

    An opaque value, an audience, a purpose, a voting context and an
    expiry. Nothing else exists on this object, because anything else
    would be the identity the artifact is defined by not carrying.
    """

    value: str
    audience_origin: str
    purpose: str
    voting_context_id: UUID
    expires_at: datetime


def assert_response_safe(payload: dict[str, Any]) -> None:
    """Run the event-builder's own prohibition over an API response.

    The same check, deliberately: a field that would be refused in an
    event has no business in a response either, and having one rule
    rather than two removes the question of which surface is stricter.
    """
    reject_prohibited_payload_keys(payload)


def endpoint(operation: str) -> EndpointSpec:
    try:
        return ENDPOINTS_BY_OPERATION[operation]
    except KeyError as exc:
        raise ValueError(f"unknown PACK-14 API operation: {operation!r}") from exc
