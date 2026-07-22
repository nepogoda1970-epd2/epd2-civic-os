"""Account Service application layer: `CreateAccount` and
`ChangeAccountStatus` commands.

Permission checks here are intentionally minimal (a boolean the caller
supplies) - a full RBAC/permission engine is out of PACK-02 scope (pack
section 3.2 excludes organizations/membership/roles); this is the
fail-closed enforcement point CT-00-06 requires, deferred to a real
permission service in a later pack. See
`docs/handover/PACK-02-REPORT.md`, "Deferred work for PACK-03".
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from epd2_account_service.domain import (
    CANONICAL_EVENT_FOR_TRANSITION,
    Account,
    AccountStatus,
    assert_transition_allowed,
)
from epd2_account_service.events import account_state_payload, build_account_event
from epd2_account_service.exceptions import UnknownAccountError
from epd2_account_service.storage import AccountStore
from epd2_audit_core.application import AppendAuditEventRequest, append_audit_event
from epd2_audit_core.domain import AuditEvent
from epd2_audit_core.storage import AuditEventStore
from epd2_core.clock import Clock
from epd2_core.event_envelope import ActorRef, EventEnvelope, compute_payload_hash
from epd2_core.identifiers import generate_uuid

#: Audit Core's own policy version for entries this service appends -
#: independent of the wire event schema version.
AUDIT_POLICY_VERSION = "1.0"
_SOURCE_SERVICE = "account-service"
_TARGET_TYPE = "account"


class PermissionDeniedError(PermissionError):
    reason_code = "PERMISSION_DENIED"


@dataclass(frozen=True, slots=True)
class CommandResult:
    account: Account
    event: EventEnvelope | None
    audit_event: AuditEvent | None = None


def create_account(
    store: AccountStore,
    audit_store: AuditEventStore,
    *,
    locale: str,
    terms_version: str,
    consent_status: str,
    actor: ActorRef,
    correlation_id: UUID,
    clock: Clock,
) -> CommandResult:
    """Create a new `Account` in status `pending` and emit `account.created`."""
    now = clock.now()
    account = Account(
        account_id=generate_uuid(),
        email_status="unverified",
        mfa_status="disabled",
        account_status=AccountStatus.PENDING,
        created_at=now,
        last_login_at=None,
        locale=locale,
        terms_version=terms_version,
        consent_status=consent_status,
    )
    store.save(account)
    event = build_account_event(
        event_id=generate_uuid(),
        event_type="account.created",
        account=account,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    # CT-00-07 / INV-04: creating an account is a critical action.
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=event.event_id,
            event_type=event.event_type,
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type=_TARGET_TYPE,
            target_id=account.account_id,
            action="create",
            reason_code="ACCOUNT_CREATED",
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash="",
            after_hash=compute_payload_hash(account_state_payload(account)),
        ),
        clock=clock,
    )
    return CommandResult(account=account, event=event, audit_event=audit_event)


def change_account_status(
    store: AccountStore,
    audit_store: AuditEventStore,
    *,
    account_id: UUID,
    target_status: AccountStatus,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    causation_id: UUID | None,
    clock: Clock,
) -> CommandResult:
    """Transition an existing account's status. Fail-closed if the
    account is unknown, the actor is not authorized (CT-00-06), or the
    transition is forbidden (CT-00-03).
    """
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to change account status")

    account = store.get(account_id)
    if account is None:
        raise UnknownAccountError(f"unknown account_id: {account_id}")

    before_hash = compute_payload_hash(account_state_payload(account))
    previous_status = account.account_status
    assert_transition_allowed(previous_status, target_status)
    updated = account.with_status(target_status)
    store.save(updated)

    event_type = CANONICAL_EVENT_FOR_TRANSITION.get((previous_status, target_status))
    event: EventEnvelope | None = None
    audit_event: AuditEvent | None = None
    if event_type is not None:
        now = clock.now()
        event = build_account_event(
            event_id=generate_uuid(),
            event_type=event_type,
            account=updated,
            actor=actor,
            correlation_id=correlation_id,
            causation_id=causation_id,
            occurred_at=now,
        )
        # CT-00-07 / INV-04: only transitions that reach a canonical event
        # are audited here, per ADR-002 - canon's own INV-04 mandatory
        # audit list does not include transitions with no canonical event
        # name (e.g. pending -> active).
        audit_event = append_audit_event(
            audit_store,
            AppendAuditEventRequest(
                audit_event_id=event.event_id,
                event_type=event.event_type,
                occurred_at=now,
                actor_id=actor.actor_id,
                actor_type=actor.actor_type,
                target_type=_TARGET_TYPE,
                target_id=updated.account_id,
                action="change_status",
                reason_code="ACCOUNT_STATUS_CHANGED",
                policy_version=AUDIT_POLICY_VERSION,
                correlation_id=correlation_id,
                source_service=_SOURCE_SERVICE,
                before_hash=before_hash,
                after_hash=compute_payload_hash(account_state_payload(updated)),
            ),
            clock=clock,
        )
    return CommandResult(account=updated, event=event, audit_event=audit_event)
