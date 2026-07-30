"""The PACK-14 canonical events, on PACK-13's envelope **unchanged**.

Fifty-nine event types in nine families. Names carry the **aggregate
prefix**, never a service or pack prefix (`account.created`, never
`pack14.account_created`) - the convention PACK-13's `P13-EVT-002`
established and this pack follows.

The envelope is canon §21's, used as it is: `event_id`, `event_type`,
`event_version`, `occurred_at`, `producer`, `actor`, `subject`,
`correlation_id`, `causation_id`, `payload`, `integrity`. PACK-14 adds no
field, removes none and reinterprets none.

Seven payload rules apply to every builder here, and the first five are
enforced rather than described - every assembled payload passes
`reject_prohibited_payload_keys` before an envelope exists, so a future
builder that reaches for a raw identifier or a secret fails closed rather
than shipping it:

1. **No global identifier.** Subjects and actors carry purpose-scoped
   references, not a raw `account_id` outside the account contexts.
2. **No secret material.** No password, OTP value, recovery code value,
   private key or full WebAuthn assertion - ever, in any field.
3. **No raw contact details** where a tokenized reference suffices.
4. **No identity document content.**
5. **No voting material of any kind.**
6. Every failure-shaped event carries a **registered reason code**.
7. Payloads are minimal: an event says what happened, not everything
   known.

Following PACK-13's pattern, each event type has a `*_RECORDED` audit
classification derived mechanically from its name by
`recorded_reason_code_for`, so the registry and the catalog cannot drift
apart.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any
from uuid import UUID

from epd2_core.event_envelope import (
    ActorRef,
    EventEnvelope,
    SubjectRef,
    assert_supported_major_version,
    build_event_envelope,
)
from epd2_identity_service.exceptions import (
    UnknownAccountSecurityEventTypeError,
    UnsupportedAccountSecurityEventVersionError,
)
from epd2_identity_service.identifiers import (
    ScopedIdentityReference,
    reject_prohibited_payload_keys,
    require_timezone,
)

EVENT_VERSION = "1.0"
SUPPORTED_MAJOR_VERSIONS = frozenset({1})
_PRODUCER = "identity-service"

ACCOUNT_EVENTS: tuple[str, ...] = (
    "account.created",
    "account.activated",
    "account.restricted",
    "account.restriction_removed",
    "account.locked",
    "account.unlocked",
    "account.closure_requested",
    "account.closure_cancelled",
    "account.closed",
    "account.anonymization_started",
    "account.anonymization_completed",
)

CONTACT_EVENTS: tuple[str, ...] = (
    "contact.added",
    "contact.verification_requested",
    "contact.verified",
    "contact.changed",
    "contact.removed",
)

CREDENTIAL_EVENTS: tuple[str, ...] = (
    "credential.enrolled",
    "credential.verified",
    "credential.revoked",
    "credential.passkey_added",
    "credential.passkey_removed",
    "credential.mfa_enrolled",
    "credential.mfa_removed",
    "credential.recovery_codes_issued",
    "credential.recovery_code_used",
    "credential.recovery_codes_revoked",
)

AUTHENTICATION_EVENTS: tuple[str, ...] = (
    "authentication.started",
    "authentication.succeeded",
    "authentication.failed",
    "authentication.step_up_requested",
    "authentication.step_up_succeeded",
    "authentication.step_up_failed",
    "authentication.suspicious_detected",
)

SESSION_EVENTS: tuple[str, ...] = (
    "session.issued",
    "session.rotated",
    "session.refreshed",
    "session.assurance_changed",
    "session.revoked",
    "session.all_revoked",
    "session.replay_detected",
)

RECOVERY_EVENTS: tuple[str, ...] = (
    "recovery.requested",
    "recovery.assessment_completed",
    "recovery.cooling_off_started",
    "recovery.approved",
    "recovery.rejected",
    "recovery.credential_replacement_started",
    "recovery.completed",
    "recovery.disputed",
)

PROOFING_EVENTS: tuple[str, ...] = (
    "proofing.started",
    "proofing.evidence_referenced",
    "proofing.verified",
    "proofing.rejected",
    "proofing.manual_review_required",
)

BOOTSTRAP_EVENTS: tuple[str, ...] = (
    "authentication_bootstrap.issued",
    "authentication_bootstrap.redeemed",
    "authentication_bootstrap.replay_rejected",
)

VOTING_HANDOFF_EVENTS: tuple[str, ...] = (
    "voting_handoff.issued",
    "voting_handoff.redeemed",
    "voting_handoff.replay_rejected",
)

ACCOUNT_SECURITY_EVENT_TYPES: tuple[str, ...] = (
    *ACCOUNT_EVENTS,
    *CONTACT_EVENTS,
    *CREDENTIAL_EVENTS,
    *AUTHENTICATION_EVENTS,
    *SESSION_EVENTS,
    *RECOVERY_EVENTS,
    *PROOFING_EVENTS,
    *BOOTSTRAP_EVENTS,
    *VOTING_HANDOFF_EVENTS,
)

_EVENT_TYPE_SET = frozenset(ACCOUNT_SECURITY_EVENT_TYPES)

#: Which aggregate each prefix names, used for the envelope's `subject`.
EVENT_SUBJECT_BY_PREFIX: dict[str, str] = {
    "account": "account",
    "contact": "account_contact",
    "credential": "credential",
    "authentication": "authentication_context",
    "session": "session",
    "recovery": "recovery_case",
    "proofing": "identity_proofing_case",
    "authentication_bootstrap": "authentication_bootstrap",
    "voting_handoff": "voting_handoff",
}

#: **Empty, deliberately.** Not one event in this module describes public
#: information: every one of them is about a specific person's account
#: security, and an empty allow-set is the honest answer rather than an
#: oversight. PACK-13's `P13-EVT-004` set the precedent for saying so
#: explicitly.
PUBLIC_PROJECTION_ALLOWED: frozenset[str] = frozenset()

#: Event types whose payload must carry a registered reason code, because
#: each of them records a refusal, a revocation or an adverse outcome and
#: "it failed" without a code tells an operator nothing.
REQUIRES_REASON_CODE: frozenset[str] = frozenset(
    {
        "account.restricted",
        "account.restriction_removed",
        "account.locked",
        "account.unlocked",
        "account.closed",
        "contact.removed",
        "credential.revoked",
        "credential.recovery_codes_revoked",
        "authentication.failed",
        "authentication.step_up_failed",
        "authentication.suspicious_detected",
        "session.assurance_changed",
        "session.revoked",
        "session.all_revoked",
        "session.replay_detected",
        "recovery.assessment_completed",
        "recovery.rejected",
        "recovery.disputed",
        "proofing.rejected",
        "proofing.manual_review_required",
        "authentication_bootstrap.replay_rejected",
        "voting_handoff.replay_rejected",
    }
)


def assert_known_event_type(event_type: str) -> None:
    if event_type not in _EVENT_TYPE_SET:
        raise UnknownAccountSecurityEventTypeError(f"unknown PACK-14 event type {event_type!r}")


def recorded_reason_code_for(event_type: str) -> str:
    """The registered `*_RECORDED` code for a successfully-audited act.

    Derived mechanically from the event name, exactly as PACK-13's
    `recorded_reason_code_for` does, so `contracts/reason-codes/
    pack-14.yml` and this tuple cannot drift.
    """
    assert_known_event_type(event_type)
    return f"{event_type.replace('.', '_').upper()}_RECORDED"


ACCOUNT_SECURITY_RECORDED_REASON_CODES: tuple[str, ...] = tuple(
    f"{event_type.replace('.', '_').upper()}_RECORDED"
    for event_type in ACCOUNT_SECURITY_EVENT_TYPES
)


def subject_type_for(event_type: str) -> str:
    assert_known_event_type(event_type)
    prefix = event_type.split(".", 1)[0]
    return EVENT_SUBJECT_BY_PREFIX[prefix]


def to_actor_ref(actor: ScopedIdentityReference) -> ActorRef:
    """Project a scoped reference onto the envelope's `actor` object.

    The purpose and the domain owner are folded into `actor_type` rather
    than dropped, because the envelope has no purpose field and a bare
    actor identifier would be exactly the unscoped reference ADR-079
    forbids. `actor_id` is a UUID derived from the reference digest -
    deterministic for one purpose, and unrelatable to the same account's
    reference for any other purpose.
    """
    return ActorRef(
        actor_id=UUID(hex=actor.reference[:32]),
        actor_type=f"{actor.domain_owner}:{actor.purpose.value}",
    )


def to_subject_ref(event_type: str, subject_id: UUID) -> SubjectRef:
    return SubjectRef(subject_type=subject_type_for(event_type), subject_id=subject_id)


def build_account_security_event(
    *,
    event_id: UUID,
    event_type: str,
    subject_id: UUID,
    actor: ScopedIdentityReference,
    payload: Mapping[str, Any],
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
    event_version: str = EVENT_VERSION,
) -> EventEnvelope:
    """The single builder every PACK-14 event goes through.

    One function rather than fifty-nine, because the checks that matter
    are the same for all of them and a per-event builder is fifty-nine
    opportunities to forget one. What varies - the payload - is assembled
    by the caller and validated here.
    """
    assert_known_event_type(event_type)
    try:
        assert_supported_major_version(event_version, SUPPORTED_MAJOR_VERSIONS)
    except Exception as exc:
        raise UnsupportedAccountSecurityEventVersionError(str(exc)) from exc
    reject_prohibited_payload_keys(payload)
    if event_type in REQUIRES_REASON_CODE and not payload.get("reason_code"):
        raise UnknownAccountSecurityEventTypeError(
            f"{event_type} records an adverse outcome and must carry a registered reason code"
        )
    return build_event_envelope(
        event_id=event_id,
        event_type=event_type,
        event_version=event_version,
        occurred_at=require_timezone(occurred_at, "occurred_at"),
        producer=_PRODUCER,
        actor=to_actor_ref(actor),
        subject=to_subject_ref(event_type, subject_id),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=dict(payload),
    )


def account_payload(
    *,
    account_status: str,
    reason_code: str | None = None,
    authority_reference: str | None = None,
    lock_reference: str | None = None,
    restriction_class: str | None = None,
    expires_at: datetime | None = None,
    retention_class: str | None = None,
) -> dict[str, Any]:
    """The account family's payload.

    Note what `account.locked` carries and what it does not: a lock
    reference, a cause, an expiry and a reason code - and the account's
    status, **unchanged**, because a lock is not a status (OD-P14-01).
    """
    payload: dict[str, Any] = {"account_status": account_status}
    for key, value in (
        ("reason_code", reason_code),
        ("authority_reference", authority_reference),
        ("lock_reference", lock_reference),
        ("restriction_class", restriction_class),
        ("retention_class", retention_class),
    ):
        if value is not None:
            payload[key] = value
    if expires_at is not None:
        payload["expires_at"] = require_timezone(expires_at, "expires_at").isoformat()
    return payload


def contact_payload(
    *,
    channel_class: str,
    channel_reference: str,
    verified_at: datetime | None = None,
    notified_old: bool | None = None,
    notified_new: bool | None = None,
    reason_code: str | None = None,
) -> dict[str, Any]:
    """The contact family's payload.

    `channel_reference` is the **tokenized** reference - the contact's
    own digest - never the address and never the masked form. A masked
    address is still an address, and an event is read by more consumers
    than a UI is.
    """
    payload: dict[str, Any] = {
        "channel_class": channel_class,
        "channel_reference": channel_reference,
    }
    if verified_at is not None:
        payload["verified_at"] = require_timezone(verified_at, "verified_at").isoformat()
    for key, flag in (("notified_old", notified_old), ("notified_new", notified_new)):
        if flag is not None:
            payload[key] = flag
    if reason_code is not None:
        payload["reason_code"] = reason_code
    return payload


def credential_payload(
    *,
    credential_reference: str,
    credential_type: str,
    binding: str | None = None,
    attestation_state: str | None = None,
    backup_eligible: bool | None = None,
    nickname: str | None = None,
    factor_class: str | None = None,
    remaining_credential_count: int | None = None,
    recovery_path_present: bool | None = None,
    resulting_assurance: str | None = None,
    set_reference: str | None = None,
    code_count: int | None = None,
    reason_code: str | None = None,
    actor_class: str | None = None,
) -> dict[str, Any]:
    """The credential family's payload.

    `credential_reference` is this service's own credential identifier,
    not the authenticator's. No public key, no counter value, no
    attestation object and no assertion - the metadata classes the event
    catalog §4 permits, and nothing that would let a consumer fingerprint
    a device.
    """
    payload: dict[str, Any] = {
        "credential_reference": credential_reference,
        "credential_type": credential_type,
    }
    for key, value in (
        ("binding", binding),
        ("attestation_state", attestation_state),
        ("nickname", nickname),
        ("factor_class", factor_class),
        ("resulting_assurance", resulting_assurance),
        ("set_reference", set_reference),
        ("reason_code", reason_code),
        ("actor_class", actor_class),
    ):
        if value is not None:
            payload[key] = value
    for key, number in (
        ("remaining_credential_count", remaining_credential_count),
        ("code_count", code_count),
    ):
        if number is not None:
            payload[key] = number
    for key, flag in (
        ("backup_eligible", backup_eligible),
        ("recovery_path_present", recovery_path_present),
    ):
        if flag is not None:
            payload[key] = flag
    return payload


def authentication_payload(
    *,
    method_class: str,
    workspace: str,
    assurance_achieved: str | None = None,
    freshness_seconds: int | None = None,
    action_code: str | None = None,
    required_assurance: str | None = None,
    object_version: int | None = None,
    signal_category: str | None = None,
    signal_weight: str | None = None,
    response_taken: str | None = None,
    attempt_counter_class: str | None = None,
    reason_code: str | None = None,
) -> dict[str, Any]:
    """The authentication family's payload.

    `attempt_counter_class` is a **class** (`first`, `few`, `many`) and
    not a count: an exact failure count for a named account is a
    brute-force progress report for anyone who can read the stream.
    """
    payload: dict[str, Any] = {"method_class": method_class, "workspace": workspace}
    for key, value in (
        ("assurance_achieved", assurance_achieved),
        ("action_code", action_code),
        ("required_assurance", required_assurance),
        ("signal_category", signal_category),
        ("signal_weight", signal_weight),
        ("response_taken", response_taken),
        ("attempt_counter_class", attempt_counter_class),
        ("reason_code", reason_code),
    ):
        if value is not None:
            payload[key] = value
    if freshness_seconds is not None:
        payload["freshness_seconds"] = freshness_seconds
    if object_version is not None:
        payload["object_version"] = object_version
    return payload


def session_payload(
    *,
    workspace: str,
    assurance: str | None = None,
    idle_deadline: datetime | None = None,
    absolute_deadline: datetime | None = None,
    rotation_trigger: str | None = None,
    assurance_from: str | None = None,
    assurance_to: str | None = None,
    revoked_count: int | None = None,
    family_reference: str | None = None,
    actor_class: str | None = None,
    reason_code: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"workspace": workspace}
    for key, value in (
        ("assurance", assurance),
        ("rotation_trigger", rotation_trigger),
        ("assurance_from", assurance_from),
        ("assurance_to", assurance_to),
        ("family_reference", family_reference),
        ("actor_class", actor_class),
        ("reason_code", reason_code),
    ):
        if value is not None:
            payload[key] = value
    for key, moment in (
        ("idle_deadline", idle_deadline),
        ("absolute_deadline", absolute_deadline),
    ):
        if moment is not None:
            payload[key] = require_timezone(moment, key).isoformat()
    if revoked_count is not None:
        payload["revoked_count"] = revoked_count
    return payload


def recovery_payload(
    *,
    entry_channel_class: str | None = None,
    risk_classification: str | None = None,
    named_signals: tuple[str, ...] | None = None,
    cooling_off_ends_at: datetime | None = None,
    notification_channels: tuple[str, ...] | None = None,
    reviewer_role: str | None = None,
    dual_control_satisfied: bool | None = None,
    credentials_revoked: bool | None = None,
    sessions_revoked: bool | None = None,
    new_credential_class: str | None = None,
    dispute_reference: str | None = None,
    appeal_path_reference: str | None = None,
    reason_code: str | None = None,
) -> dict[str, Any]:
    """The recovery family's payload.

    `named_signals` rather than a score, `reviewer_role` rather than a
    reviewer identity, and `dual_control_satisfied` as the
    separation-of-duties evidence the event catalog §7 asks for - enough
    for an oversight body to see that the control held, and not enough to
    identify the reviewer to every consumer of the stream.
    """
    payload: dict[str, Any] = {}
    for key, value in (
        ("entry_channel_class", entry_channel_class),
        ("risk_classification", risk_classification),
        ("reviewer_role", reviewer_role),
        ("new_credential_class", new_credential_class),
        ("dispute_reference", dispute_reference),
        ("appeal_path_reference", appeal_path_reference),
        ("reason_code", reason_code),
    ):
        if value is not None:
            payload[key] = value
    for key, sequence in (
        ("named_signals", named_signals),
        ("notification_channels", notification_channels),
    ):
        if sequence is not None:
            payload[key] = list(sequence)
    for key, flag in (
        ("dual_control_satisfied", dual_control_satisfied),
        ("credentials_revoked", credentials_revoked),
        ("sessions_revoked", sessions_revoked),
    ):
        if flag is not None:
            payload[key] = flag
    if cooling_off_ends_at is not None:
        payload["cooling_off_ends_at"] = require_timezone(
            cooling_off_ends_at, "cooling_off_ends_at"
        ).isoformat()
    return payload


def proofing_payload(
    *,
    method: str,
    requested_assurance: str | None = None,
    evidence_reference: str | None = None,
    achieved_assurance: str | None = None,
    deciding_authority: str | None = None,
    trigger: str | None = None,
    appeal_path_reference: str | None = None,
    reason_code: str | None = None,
) -> dict[str, Any]:
    """The proofing family's payload.

    `evidence_reference` is a PACK-11 bundle reference and **never the
    content**. No declared name, no date of birth, no document field -
    canon 19d.2's attributes stay inside the proofing context, exactly as
    `events.build_identity_event` has kept them since PACK-07.
    """
    payload: dict[str, Any] = {"method": method}
    for key, value in (
        ("requested_assurance", requested_assurance),
        ("evidence_reference", evidence_reference),
        ("achieved_assurance", achieved_assurance),
        ("deciding_authority", deciding_authority),
        ("trigger", trigger),
        ("appeal_path_reference", appeal_path_reference),
        ("reason_code", reason_code),
    ):
        if value is not None:
            payload[key] = value
    return payload


def bootstrap_payload(
    *,
    workspace: str,
    audience_origin: str,
    expires_at: datetime | None = None,
    reason_code: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"workspace": workspace, "audience_origin": audience_origin}
    if expires_at is not None:
        payload["expires_at"] = require_timezone(expires_at, "expires_at").isoformat()
    if reason_code is not None:
        payload["reason_code"] = reason_code
    return payload


def voting_handoff_payload(
    *,
    purpose: str,
    voting_context_id: UUID,
    expires_at: datetime | None = None,
    redeemed_at: datetime | None = None,
    reason_code: str | None = None,
) -> dict[str, Any]:
    """The voting handoff family's payload.

    Purpose scope, voting context, expiry, redemption time and - for a
    refusal - a reason code. **No identity of any kind**, and no field
    that would let an issuance and a redemption be joined back to an
    account (ADR-088).
    """
    payload: dict[str, Any] = {
        "purpose": purpose,
        "voting_context_id": str(voting_context_id),
    }
    for key, moment in (("expires_at", expires_at), ("redeemed_at", redeemed_at)):
        if moment is not None:
            payload[key] = require_timezone(moment, key).isoformat()
    if reason_code is not None:
        payload["reason_code"] = reason_code
    return payload
