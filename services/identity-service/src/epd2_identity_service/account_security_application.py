"""The governed commands.

Every consequential operation in PACK-14 enters here, and every one of
them does the same five things in the same order:

1. **Idempotency.** A replayed request with an identical body returns the
   first result; the same key with a different body is refused.
2. **Gate.** Account usability, assurance, freshness, step-up binding,
   privileged grant - whichever apply, evaluated fail-closed as a
   conjunction (canon 19d.8, no "or").
3. **Audit before effect.** The audit record is appended *before* the
   domain change is persisted. If audit is unavailable the operation
   refuses: there is no unlogged privileged act (workflow matrix §4).
4. **Persist.** Through the owning module's own store, never another
   module's.
5. **Emit.** On PACK-13's canonical envelope, through the one builder
   that rejects prohibited payload keys.

`AccountSecurityService` holds the six stores, the ports and the
configuration. It is a composition root rather than a god object: it
contains no policy of its own, and every rule it applies lives in the
module that owns that rule.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID

from epd2_audit_core.application import AppendAuditEventRequest, append_audit_event
from epd2_audit_core.storage import AuditEventStore
from epd2_core.canonical_json import canonical_dumps
from epd2_core.clock import Clock
from epd2_core.event_envelope import EventEnvelope
from epd2_identity_service.account_security_events import (
    account_payload,
    build_account_security_event,
    contact_payload,
    credential_payload,
    recorded_reason_code_for,
    session_payload,
    voting_handoff_payload,
)
from epd2_identity_service.account_security_storage import (
    AccountContactStore,
    AccountRegistryStore,
    AuthenticationStore,
    BootstrapStore,
    CredentialStore,
    IdentityMappingStore,
    IdentityProofingStore,
    RecoveryStore,
    ReplayPreventionStore,
    SessionStore,
    VotingHandoffStore,
)
from epd2_identity_service.accounts import (
    AccountLock,
    AccountRegistryRecord,
    AccountRegistryStatus,
    AccountRestriction,
    activate_account_record,
    assert_account_usable,
    create_account_record,
)
from epd2_identity_service.assurance import (
    ACTION_REQUIREMENTS,
    AssuranceEvidence,
    AuthenticationAssurance,
    AuthenticationMethod,
    RiskState,
    evaluate_assurance,
    evaluate_requirement,
)
from epd2_identity_service.configuration import IdentityConfiguration, default_configuration
from epd2_identity_service.contacts import (
    AccountContact,
    ContactChannelClass,
    ContactStatus,
    assert_not_last_verified_channel,
    assert_unique_within_scope,
    build_contact,
)
from epd2_identity_service.credentials import (
    Credential,
    CredentialMetadata,
    CredentialRevocation,
    CredentialStatus,
    CredentialType,
    assert_removal_leaves_a_way_in,
    enroll_credential,
)
from epd2_identity_service.domain import AuthenticationAssuranceLevel
from epd2_identity_service.exceptions import (
    AuditUnavailableError,
    NotificationDeliveryFailedError,
    UnknownAccountRegistryRecordError,
    UnknownCredentialError,
    UnknownSessionRecordError,
)
from epd2_identity_service.identifiers import (
    AccountId,
    CredentialId,
    IdentifierSpace,
    MappingPurpose,
    OrganizationScope,
    ScopedIdentityReference,
    SessionId,
    derive_scoped_reference,
)
from epd2_identity_service.observability import MetricLabels, MetricName, MetricsRecorder
from epd2_identity_service.passkeys import (
    UnboundWebAuthnVerifier,
    WebAuthnVerifier,
)
from epd2_identity_service.persistence import IdempotencyRecord, assert_idempotent
from epd2_identity_service.secret_storage import (
    BreachedPasswordChecker,
    DeterministicTotpVerifier,
    PasswordHasher,
    SecureRandom,
    SystemSecureRandom,
    TotpVerifier,
    UnavailablePasswordHasher,
    UnboundBreachedPasswordChecker,
)
from epd2_identity_service.sessions import (
    DeviceReference,
    SessionRecord,
    SessionScope,
    issue_session,
    revoke_all_sessions,
    revoke_session,
)
from epd2_identity_service.sql_storage import UnitOfWork
from epd2_identity_service.stepup import StepUpBinding, StepUpResult, redeem_step_up
from epd2_identity_service.voting_handoff import (
    VotingHandoffArtifact,
    VotingHandoffRequest,
    issue_voting_handoff,
)
from epd2_identity_service.workspaces import (
    WorkspaceId,
    assert_declared_origin,
    assert_issues_identity_session,
    workspace_origin,
)

#: Audit Core's policy version for entries this module appends -
#: independent of the wire event schema version, exactly as
#: `application.AUDIT_POLICY_VERSION` already is for PACK-02's paths.
PACK14_AUDIT_POLICY_VERSION = "1.0"
_SOURCE_SERVICE = "identity-service"


class NotificationOutbox:
    """The delivery boundary, as a port with an in-memory reference
    adapter.

    `FIR-DELIVERY-001` classifies notifications; PACK-14 hands them over
    and does not deliver them. **No email or SMS provider is integrated
    by this round** - `dispatch` records an intent, and a deployment
    binds a real outbox.

    A failed dispatch is a real failure: a security-relevant operation
    that depends on notification does not silently complete (workflow
    matrix §4), so `dispatch` raises rather than returning `False`.
    """

    def __init__(self) -> None:
        self.dispatched: list[tuple[str, str, str]] = []
        self.fail_next = False

    def dispatch(self, *, notification_class: str, channel_class: str, reference: str) -> None:
        if self.fail_next:
            raise NotificationDeliveryFailedError(
                "the notification could not be handed to the delivery outbox"
            )
        self.dispatched.append((notification_class, channel_class, reference))


@dataclass
class AccountSecurityService:
    """The composition root for PACK-14's governed commands."""

    account_store: AccountRegistryStore
    contact_store: AccountContactStore
    credential_store: CredentialStore
    authentication_store: AuthenticationStore
    session_store: SessionStore
    recovery_store: RecoveryStore
    proofing_store: IdentityProofingStore
    bootstrap_store: BootstrapStore
    voting_handoff_store: VotingHandoffStore
    mapping_store: IdentityMappingStore
    replay_store: ReplayPreventionStore
    audit_store: AuditEventStore
    clock: Clock
    derivation_salt: bytes
    configuration: IdentityConfiguration = None  # type: ignore[assignment]
    random: SecureRandom = None  # type: ignore[assignment]
    password_hasher: PasswordHasher = None  # type: ignore[assignment]
    breach_checker: BreachedPasswordChecker = None  # type: ignore[assignment]
    totp_verifier: TotpVerifier = None  # type: ignore[assignment]
    webauthn_verifier: WebAuthnVerifier = None  # type: ignore[assignment]
    outbox: NotificationOutbox = None  # type: ignore[assignment]
    metrics: MetricsRecorder = None  # type: ignore[assignment]
    audit_available: bool = True
    #: The transaction boundary, when one is bound. `build_identity_service`
    #: binds it; a unit test that is not exercising persistence leaves it
    #: `None` and every command runs unwrapped, exactly as before.
    unit_of_work: UnitOfWork | None = None

    def __post_init__(self) -> None:
        """Bind the fail-closed defaults.

        Every unbound port defaults to the refusing adapter, never to a
        permissive one: an unconfigured deployment cannot hash a
        password, verify a passkey or check a breach corpus, and it says
        so rather than pretending.
        """
        if self.configuration is None:
            self.configuration = default_configuration()
        if self.random is None:
            self.random = SystemSecureRandom()
        if self.password_hasher is None:
            self.password_hasher = UnavailablePasswordHasher()
        if self.breach_checker is None:
            self.breach_checker = UnboundBreachedPasswordChecker()
        if self.totp_verifier is None:
            self.totp_verifier = DeterministicTotpVerifier()
        if self.webauthn_verifier is None:
            self.webauthn_verifier = UnboundWebAuthnVerifier()
        if self.outbox is None:
            self.outbox = NotificationOutbox()
        if self.metrics is None:
            self.metrics = MetricsRecorder()

    # --- shared machinery ---------------------------------------------------

    @contextmanager
    def transaction(self) -> Iterator[None]:
        """Run a block inside the bound transaction boundary.

        The **request** boundary owns the transaction: `service_api`
        opens one per dispatched operation, so a request that fails
        half-way leaves no partial account, credential or session state.
        The two commands below that are inherently multi-row - credential
        revocation and revoke-all - open one themselves as well, because
        they are multi-row whether or not a request wrapped them.

        With no unit of work bound this is a no-op, which is what keeps
        the in-memory test adapters usable without a database.
        """
        if self.unit_of_work is None:
            yield
            return
        with self.unit_of_work():
            yield

    def scoped_reference(
        self,
        account_id: AccountId,
        *,
        purpose: MappingPurpose,
        scope: OrganizationScope,
        domain_owner: str = _SOURCE_SERVICE,
    ) -> ScopedIdentityReference:
        """Derive the reference that leaves this service.

        Every event, audit record and API response uses one of these
        rather than the `account_id`. Two references derived for two
        purposes do not compare equal, which is what makes the absence of
        a global identifier structural.
        """
        return derive_scoped_reference(
            space=IdentifierSpace.ACCOUNT,
            value=str(account_id),
            purpose=purpose,
            scope=scope,
            domain_owner=domain_owner,
            derivation_salt=self.derivation_salt,
        )

    def _assert_idempotent(
        self, *, idempotency_key: str | None, operation: str, request_body: dict[str, object]
    ) -> bool:
        if idempotency_key is None:
            return False
        digest = hashlib.sha256(canonical_dumps(request_body).encode("utf-8")).hexdigest()
        replayed = assert_idempotent(
            self.replay_store.get_idempotency(idempotency_key),
            idempotency_key=idempotency_key,
            request_digest=digest,
            operation=operation,
        )
        if not replayed:
            self.replay_store.record_idempotency(
                IdempotencyRecord(
                    idempotency_key=idempotency_key,
                    request_digest=digest,
                    operation=operation,
                    recorded_at=self.clock.now(),
                )
            )
        return replayed

    def _audit(
        self,
        *,
        event: EventEnvelope,
        action: str,
        reason_code: str,
        before_hash: str = "",
        after_hash: str = "",
    ) -> None:
        """Audit **before** the effect is published.

        `audit_available` gates it: when the audit path is down, a
        consequential operation refuses rather than proceeding unlogged.
        """
        if not self.audit_available:
            raise AuditUnavailableError(
                "the audit path is unavailable; this operation does not proceed unlogged"
            )
        append_audit_event(
            self.audit_store,
            AppendAuditEventRequest(
                audit_event_id=event.event_id,
                event_type=event.event_type,
                occurred_at=event.occurred_at,
                actor_id=event.actor.actor_id,
                actor_type=event.actor.actor_type,
                target_type=event.subject.subject_type,
                target_id=event.subject.subject_id,
                action=action,
                reason_code=reason_code,
                policy_version=PACK14_AUDIT_POLICY_VERSION,
                correlation_id=event.correlation_id,
                source_service=_SOURCE_SERVICE,
                before_hash=before_hash,
                after_hash=after_hash,
            ),
            clock=self.clock,
        )

    def _emit(
        self,
        *,
        event_type: str,
        subject_id: UUID,
        actor: ScopedIdentityReference,
        payload: dict[str, object],
        correlation_id: UUID,
        causation_id: UUID | None,
        event_id: UUID,
        action: str,
    ) -> EventEnvelope:
        event = build_account_security_event(
            event_id=event_id,
            event_type=event_type,
            subject_id=subject_id,
            actor=actor,
            payload=payload,
            correlation_id=correlation_id,
            causation_id=causation_id,
            occurred_at=self.clock.now(),
        )
        self._audit(
            event=event,
            action=action,
            reason_code=str(payload.get("reason_code") or recorded_reason_code_for(event_type)),
            after_hash=event.integrity.payload_hash,
        )
        return event

    def _require_account(self, account_id: AccountId) -> AccountRegistryRecord:
        record = self.account_store.get(account_id)
        if record is None:
            raise UnknownAccountRegistryRecordError(
                "no account registry record exists for the given identifier"
            )
        return record

    def assert_action_permitted(
        self,
        *,
        account_id: AccountId,
        action_code: str,
        assurance: AuthenticationAssurance | None,
        step_up: StepUpResult | None,
        binding: StepUpBinding | None,
    ) -> StepUpResult | None:
        """The gate, in one place, for every consequential action.

        Order matters: account usability first (a locked account is told
        it is locked rather than that its assurance is too low), then the
        assurance conjunction, then the step-up redemption which consumes
        the confirmation.
        """
        record = self._require_account(account_id)
        now = self.clock.now()
        assert_account_usable(
            record,
            locks=self.account_store.locks_for(account_id),
            restrictions=self.account_store.restrictions_for(account_id),
            now=now,
        )
        requirement = ACTION_REQUIREMENTS[action_code]
        evaluate_requirement(
            assurance=assurance,
            identity_assurance=None,
            requirement=requirement,
            configuration=self.configuration,
            now=now,
        )
        if not requirement.step_up_required:
            return None
        if binding is None:
            raise UnknownSessionRecordError(
                "a step-up-protected action names the object it is bound to"
            )
        consumed = redeem_step_up(step_up, binding=binding, now=now)
        self.session_store.save_step_up_result(consumed)
        return consumed

    # --- account lifecycle --------------------------------------------------

    def create_account(
        self,
        *,
        account_id: AccountId,
        scope: OrganizationScope,
        correlation_id: UUID,
        event_id: UUID,
        idempotency_key: str | None = None,
    ) -> AccountRegistryRecord:
        """Create a `pending` account.

        It becomes `active` only when a contact channel has been
        verified. An unverified account that can act is an unowned
        account that can act.
        """
        if self._assert_idempotent(
            idempotency_key=idempotency_key,
            operation="create_account",
            request_body={"account_id": str(account_id)},
        ):
            return self._require_account(account_id)
        record = create_account_record(
            account_id=account_id, scope=scope, created_at=self.clock.now()
        )
        actor = self.scoped_reference(
            account_id, purpose=MappingPurpose.ACCOUNT_SECURITY, scope=scope
        )
        self._emit(
            event_type="account.created",
            subject_id=account_id,
            actor=actor,
            payload=account_payload(account_status=record.account_status.value),
            correlation_id=correlation_id,
            causation_id=None,
            event_id=event_id,
            action="create_account",
        )
        self.account_store.save(record)
        return record

    def activate_account(
        self,
        *,
        account_id: AccountId,
        expected_version: int,
        correlation_id: UUID,
        event_id: UUID,
    ) -> AccountRegistryRecord:
        """Activate, and only on a verified contact.

        The verified-channel check is here rather than in the caller
        because activation is the moment the account becomes able to act,
        and "we meant to verify first" is not a state this service
        should be able to reach.
        """
        record = self._require_account(account_id)
        contacts = self.contact_store.for_account(account_id)
        if not any(contact.is_verified() for contact in contacts):
            from epd2_identity_service.exceptions import ContactNotVerifiedError

            raise ContactNotVerifiedError(
                "activation requires at least one verified contact channel"
            )
        activated = activate_account_record(
            record, expected_version=expected_version, activated_at=self.clock.now()
        )
        actor = self.scoped_reference(
            account_id, purpose=MappingPurpose.ACCOUNT_SECURITY, scope=record.scope
        )
        self._emit(
            event_type="account.activated",
            subject_id=account_id,
            actor=actor,
            payload=account_payload(account_status=activated.account_status.value),
            correlation_id=correlation_id,
            causation_id=None,
            event_id=event_id,
            action="activate_account",
        )
        self.account_store.save(activated)
        return activated

    def apply_lock(
        self,
        *,
        lock: AccountLock,
        correlation_id: UUID,
        event_id: UUID,
    ) -> AccountLock:
        """Apply a technical lock **without touching the account status**.

        The emitted payload carries the account's status unchanged, which
        is OD-P14-01 visible on the wire: a consumer that reads
        `account.locked` learns about a lock and sees that the account is
        still whatever it was.
        """
        record = self._require_account(lock.account_id)
        actor = self.scoped_reference(
            lock.account_id, purpose=MappingPurpose.ACCOUNT_SECURITY, scope=record.scope
        )
        self._emit(
            event_type="account.locked",
            subject_id=lock.account_id,
            actor=actor,
            payload=account_payload(
                account_status=record.account_status.value,
                reason_code=lock.reason_code,
                lock_reference=str(lock.lock_id),
                expires_at=lock.expires_at,
            ),
            correlation_id=correlation_id,
            causation_id=None,
            event_id=event_id,
            action="apply_lock",
        )
        self.account_store.save_lock(lock)
        return lock

    def apply_restriction(
        self,
        *,
        restriction: AccountRestriction,
        correlation_id: UUID,
        event_id: UUID,
    ) -> AccountRestriction:
        record = self._require_account(restriction.account_id)
        actor = self.scoped_reference(
            restriction.account_id, purpose=MappingPurpose.ACCOUNT_SECURITY, scope=record.scope
        )
        self._emit(
            event_type="account.restricted",
            subject_id=restriction.account_id,
            actor=actor,
            payload=account_payload(
                account_status=record.account_status.value,
                reason_code=restriction.reason_code,
                authority_reference=restriction.authority_reference,
                restriction_class=restriction.restriction_class.value,
                expires_at=restriction.expires_at,
            ),
            correlation_id=correlation_id,
            causation_id=None,
            event_id=event_id,
            action="apply_restriction",
        )
        self.account_store.save_restriction(restriction)
        return restriction

    # --- contacts -----------------------------------------------------------

    def add_contact(
        self,
        *,
        contact_id: UUID,
        account_id: AccountId,
        channel_class: ContactChannelClass,
        raw_value: str,
        correlation_id: UUID,
        event_id: UUID,
    ) -> AccountContact:
        record = self._require_account(account_id)
        contact = build_contact(
            contact_id=contact_id,
            account_id=account_id,
            channel_class=channel_class,
            raw_value=raw_value,
            scope=record.scope,
            added_at=self.clock.now(),
        )
        assert_unique_within_scope(contact, self.contact_store.within_scope(contact))
        actor = self.scoped_reference(
            account_id, purpose=MappingPurpose.ACCOUNT_SECURITY, scope=record.scope
        )
        self._emit(
            event_type="contact.added",
            subject_id=contact_id,
            actor=actor,
            payload=contact_payload(
                channel_class=channel_class.value,
                channel_reference=contact.normalized_digest.digest,
            ),
            correlation_id=correlation_id,
            causation_id=None,
            event_id=event_id,
            action="add_contact",
        )
        self.contact_store.save(contact)
        return contact

    def verify_contact(
        self,
        *,
        contact_id: UUID,
        correlation_id: UUID,
        event_id: UUID,
    ) -> AccountContact:
        contact = self.contact_store.get(contact_id)
        if contact is None:
            from epd2_identity_service.exceptions import UnknownAccountContactError

            raise UnknownAccountContactError("no account contact exists for the given identifier")
        pending = (
            contact.transitioned(ContactStatus.VERIFICATION_PENDING, at=self.clock.now())
            if contact.status is ContactStatus.UNVERIFIED
            else contact
        )
        verified = pending.transitioned(ContactStatus.VERIFIED, at=self.clock.now())
        record = self._require_account(contact.account_id)
        actor = self.scoped_reference(
            contact.account_id, purpose=MappingPurpose.ACCOUNT_SECURITY, scope=record.scope
        )
        self._emit(
            event_type="contact.verified",
            subject_id=contact_id,
            actor=actor,
            payload=contact_payload(
                channel_class=contact.channel_class.value,
                channel_reference=contact.normalized_digest.digest,
                verified_at=verified.verified_at,
            ),
            correlation_id=correlation_id,
            causation_id=None,
            event_id=event_id,
            action="verify_contact",
        )
        self.contact_store.save(verified)
        return verified

    def remove_contact(
        self, *, contact_id: UUID, reason_code: str, correlation_id: UUID, event_id: UUID
    ) -> AccountContact:
        contact = self.contact_store.get(contact_id)
        if contact is None:
            from epd2_identity_service.exceptions import UnknownAccountContactError

            raise UnknownAccountContactError("no account contact exists for the given identifier")
        assert_not_last_verified_channel(
            contact, self.contact_store.for_account(contact.account_id)
        )
        removed = contact.transitioned(ContactStatus.REMOVED, at=self.clock.now())
        record = self._require_account(contact.account_id)
        actor = self.scoped_reference(
            contact.account_id, purpose=MappingPurpose.ACCOUNT_SECURITY, scope=record.scope
        )
        self._emit(
            event_type="contact.removed",
            subject_id=contact_id,
            actor=actor,
            payload=contact_payload(
                channel_class=contact.channel_class.value,
                channel_reference=contact.normalized_digest.digest,
                reason_code=reason_code,
            ),
            correlation_id=correlation_id,
            causation_id=None,
            event_id=event_id,
            action="remove_contact",
        )
        self.contact_store.save(removed)
        return removed

    # --- credentials --------------------------------------------------------

    def enroll_credential(
        self,
        *,
        credential_id: CredentialId,
        account_id: AccountId,
        credential_type: CredentialType,
        metadata: CredentialMetadata,
        correlation_id: UUID,
        event_id: UUID,
        requires_confirmation: bool = True,
    ) -> Credential:
        record = self._require_account(account_id)
        credential = enroll_credential(
            credential_id=credential_id,
            account_id=account_id,
            credential_type=credential_type,
            metadata=metadata,
            created_at=self.clock.now(),
            existing=self.credential_store.for_account(account_id),
            requires_confirmation=requires_confirmation,
        )
        actor = self.scoped_reference(
            account_id, purpose=MappingPurpose.ACCOUNT_SECURITY, scope=record.scope
        )
        self._emit(
            event_type="credential.enrolled",
            subject_id=credential_id,
            actor=actor,
            payload=credential_payload(
                credential_reference=str(credential_id),
                credential_type=credential_type.value,
                binding=metadata.binding.value,
                attestation_state=metadata.attestation.value,
                backup_eligible=metadata.backup_eligible,
                nickname=metadata.nickname,
            ),
            correlation_id=correlation_id,
            causation_id=None,
            event_id=event_id,
            action="enroll_credential",
        )
        self.credential_store.save(credential)
        self._notify_all_channels(account_id, notification_class="security_alert")
        return credential

    def revoke_credential(
        self,
        *,
        credential_id: CredentialId,
        reason_code: str,
        actor_class: str,
        correlation_id: UUID,
        event_id: UUID,
        recovery_path_available: bool = False,
    ) -> Credential:
        """Revoke a credential, and the sessions it could have produced.

        Both halves happen here so a compromise response cannot leave the
        attacker's session running - the failure mode the session
        security matrix names explicitly.
        """
        with self.transaction():
            return self._revoke_credential(
                credential_id=credential_id,
                reason_code=reason_code,
                actor_class=actor_class,
                correlation_id=correlation_id,
                event_id=event_id,
                recovery_path_available=recovery_path_available,
            )

    def _revoke_credential(
        self,
        *,
        credential_id: CredentialId,
        reason_code: str,
        actor_class: str,
        correlation_id: UUID,
        event_id: UUID,
        recovery_path_available: bool,
    ) -> Credential:
        credential = self.credential_store.get(credential_id)
        if credential is None:
            raise UnknownCredentialError("no credential exists for the given identifier")
        assert_removal_leaves_a_way_in(
            credential=credential,
            all_credentials=self.credential_store.for_account(credential.account_id),
            recovery_path_available=recovery_path_available,
        )
        now = self.clock.now()
        revoked = credential.revoked(
            CredentialRevocation(revoked_at=now, reason_code=reason_code, actor_class=actor_class)
        )
        record = self._require_account(credential.account_id)
        actor = self.scoped_reference(
            credential.account_id, purpose=MappingPurpose.ACCOUNT_SECURITY, scope=record.scope
        )
        self._emit(
            event_type="credential.revoked",
            subject_id=credential_id,
            actor=actor,
            payload=credential_payload(
                credential_reference=str(credential_id),
                credential_type=credential.credential_type.value,
                reason_code=reason_code,
                actor_class=actor_class,
            ),
            correlation_id=correlation_id,
            causation_id=None,
            event_id=event_id,
            action="revoke_credential",
        )
        self.credential_store.save(revoked)
        for session in self.session_store.for_account(credential.account_id):
            if session.status.value == "revoked":
                continue
            self.session_store.save(
                revoke_session(
                    session,
                    reason_code="CREDENTIAL_REVOKED",
                    actor_class=actor_class,
                    revoked_at=now,
                )
            )
        self._notify_all_channels(credential.account_id, notification_class="security_alert")
        return revoked

    # --- sessions -----------------------------------------------------------

    def issue_session(
        self,
        *,
        session_id: SessionId,
        account_id: AccountId,
        workspace: WorkspaceId,
        methods: tuple[AuthenticationMethod, ...],
        credential_binding: str,
        device: DeviceReference,
        correlation_id: UUID,
        event_id: UUID,
        risk_state: RiskState = RiskState.NORMAL,
        named_signals: tuple[str, ...] = (),
    ) -> tuple[SessionRecord, str, str]:
        """Issue an origin-local session.

        `assert_issues_identity_session` refuses WS-03 here, so the
        Voting Client cannot be given an ordinary session by any
        combination of arguments.
        """
        assert_issues_identity_session(workspace)
        record = self._require_account(account_id)
        now = self.clock.now()
        assert_account_usable(
            record,
            locks=self.account_store.locks_for(account_id),
            restrictions=self.account_store.restrictions_for(account_id),
            now=now,
        )
        from epd2_identity_service.credentials import CredentialBinding

        assurance = evaluate_assurance(
            evidence=AssuranceEvidence(
                methods=methods,
                credential_binding=CredentialBinding(credential_binding),
                risk_state=risk_state,
                named_signals=named_signals,
            ),
            authenticated_at=now,
        )
        actor = self.scoped_reference(
            account_id, purpose=MappingPurpose.SESSION, scope=record.scope
        )
        session, refresh_token, csrf_token = issue_session(
            session_id=session_id,
            account_id=account_id,
            actor_reference=actor,
            scope=SessionScope(
                workspace=workspace,
                origin=workspace_origin(workspace),
                capabilities=frozenset({"member-shell"}),
            ),
            assurance=assurance,
            device=device,
            issued_at=now,
            configuration=self.configuration,
            random=self.random,
        )
        self._emit(
            event_type="session.issued",
            subject_id=session_id,
            actor=actor,
            payload=session_payload(
                workspace=workspace.value,
                assurance=assurance.effective_level.value,
                idle_deadline=session.idle_deadline,
                absolute_deadline=session.absolute_deadline,
            ),
            correlation_id=correlation_id,
            causation_id=None,
            event_id=event_id,
            action="issue_session",
        )
        self.session_store.save(session)
        self.metrics.record(
            MetricName.SESSION_ISSUED,
            MetricLabels(
                values={
                    "workspace": workspace.value,
                    "assurance_level": assurance.effective_level.value,
                }
            ),
        )
        return session, refresh_token, csrf_token

    def revoke_all_sessions_for(
        self,
        *,
        account_id: AccountId,
        reason_code: str,
        actor_class: str,
        correlation_id: UUID,
        event_id: UUID,
    ) -> int:
        """Revoke every session, and report the count.

        Partial revocation is treated as failure by the caller: the count
        is returned so "some sessions survived" can never be reported as
        complete (workflow matrix §4).
        """
        with self.transaction():
            return self._revoke_all_sessions_for(
                account_id=account_id,
                reason_code=reason_code,
                actor_class=actor_class,
                correlation_id=correlation_id,
                event_id=event_id,
            )

    def _revoke_all_sessions_for(
        self,
        *,
        account_id: AccountId,
        reason_code: str,
        actor_class: str,
        correlation_id: UUID,
        event_id: UUID,
    ) -> int:
        record = self._require_account(account_id)
        sessions = self.session_store.for_account(account_id)
        now = self.clock.now()
        revoked = revoke_all_sessions(
            sessions, reason_code=reason_code, actor_class=actor_class, revoked_at=now
        )
        for session in revoked:
            self.session_store.save(session)
        actor = self.scoped_reference(
            account_id, purpose=MappingPurpose.SESSION, scope=record.scope
        )
        self._emit(
            event_type="session.all_revoked",
            subject_id=account_id,
            actor=actor,
            payload=session_payload(
                workspace="all",
                reason_code=reason_code,
                actor_class=actor_class,
                revoked_count=len(revoked),
            ),
            correlation_id=correlation_id,
            causation_id=None,
            event_id=event_id,
            action="revoke_all_sessions",
        )
        self.metrics.record(
            MetricName.SESSION_REVOKED,
            MetricLabels(values={"reason_code": reason_code}),
            value=len(revoked),
        )
        return len(revoked)

    # --- voting handoff -----------------------------------------------------

    def issue_voting_handoff(
        self,
        *,
        artifact_id: UUID,
        request: VotingHandoffRequest,
        account_id: AccountId,
        assurance: AuthenticationAssurance | None,
        step_up: StepUpResult | None,
        binding: StepUpBinding | None,
        correlation_id: UUID,
        event_id: UUID,
    ) -> VotingHandoffArtifact:
        """Issue the outbound artifact.

        The account is gated here - assurance `high`, a bound step-up,
        a usable account - and then **nothing about it is carried
        forward**. The issuance record has no account field, and the
        emitted event carries purpose and expiry only, so no pair of
        records can be joined back to the holder (ADR-088).
        """
        self.assert_action_permitted(
            account_id=account_id,
            action_code="voting_handoff",
            assurance=assurance,
            step_up=step_up,
            binding=binding,
        )
        artifact, issuance = issue_voting_handoff(
            request,
            artifact_id=artifact_id,
            issued_at=self.clock.now(),
            configuration=self.configuration,
            random=self.random,
        )
        record = self._require_account(account_id)
        actor = self.scoped_reference(
            account_id, purpose=MappingPurpose.VOTING_ENTRY, scope=record.scope
        )
        self._emit(
            event_type="voting_handoff.issued",
            subject_id=artifact_id,
            actor=actor,
            payload=voting_handoff_payload(
                purpose=issuance.purpose,
                voting_context_id=issuance.voting_context_id,
                expires_at=issuance.expires_at,
            ),
            correlation_id=correlation_id,
            causation_id=None,
            event_id=event_id,
            action="issue_voting_handoff",
        )
        self.voting_handoff_store.save_issuance(issuance)
        self.metrics.record(
            MetricName.VOTING_HANDOFF_ISSUED, MetricLabels(values={"outcome": "issued"})
        )
        return artifact

    # --- notification -------------------------------------------------------

    def _notify_all_channels(self, account_id: AccountId, *, notification_class: str) -> None:
        """Notify every verified channel, old ones included.

        A credential change that only reaches the newest address is a
        credential change the previous holder never hears about.
        """
        for contact in self.contact_store.for_account(account_id):
            if contact.is_verified():
                self.outbox.dispatch(
                    notification_class=notification_class,
                    channel_class=contact.channel_class.value,
                    reference=contact.normalized_digest.digest,
                )


def account_security_state(
    service: AccountSecurityService, *, account_id: AccountId, now: datetime
) -> dict[str, object]:
    """The read model behind "get account security state".

    Counts and classes, never values: how many credentials, which
    factor classes, how many active sessions, whether a lock or a
    restriction is in force. Nothing here would help an attacker who
    obtained it, which is the test a security-summary endpoint has to
    pass.
    """
    record = service.account_store.get(account_id)
    if record is None:
        raise UnknownAccountRegistryRecordError("no account registry record exists")
    credentials = service.credential_store.for_account(account_id)
    sessions = service.session_store.for_account(account_id)
    factors = service.credential_store.factors_for(account_id)
    return {
        "account_status": record.account_status.value,
        "activated": record.activated_at is not None,
        "credential_count": sum(1 for c in credentials if c.status is CredentialStatus.ACTIVE),
        "credential_types": sorted(
            {c.credential_type.value for c in credentials if c.status is CredentialStatus.ACTIVE}
        ),
        "factor_classes": sorted({f.factor_class.value for f in factors}),
        "active_session_count": sum(1 for s in sessions if s.status.value == "active"),
        "lock_in_force": any(
            lock.is_in_force(now) for lock in service.account_store.locks_for(account_id)
        ),
        "restriction_in_force": any(
            restriction.is_in_force(now)
            for restriction in service.account_store.restrictions_for(account_id)
        ),
        "closure_requested": service.account_store.open_closure_request(account_id) is not None,
    }


def assurance_from_methods(
    methods: tuple[AuthenticationMethod, ...],
    *,
    credential_binding: str,
    authenticated_at: datetime,
    risk_state: RiskState = RiskState.NORMAL,
    named_signals: tuple[str, ...] = (),
) -> AuthenticationAssurance:
    """A convenience for callers and tests that need an assurance value
    without a session."""
    from epd2_identity_service.credentials import CredentialBinding

    return evaluate_assurance(
        evidence=AssuranceEvidence(
            methods=methods,
            credential_binding=CredentialBinding(credential_binding),
            risk_state=risk_state,
            named_signals=named_signals,
        ),
        authenticated_at=authenticated_at,
    )


#: Re-exported for callers that need the canonical status vocabulary
#: without importing the accounts module directly.
ACCOUNT_STATUS_VALUES: tuple[str, ...] = tuple(status.value for status in AccountRegistryStatus)

#: The governed default session lifetimes, exposed so an API layer can
#: describe them without reaching into the configuration module.
DEFAULT_SESSION_WINDOWS: dict[str, tuple[timedelta, timedelta]] = {
    level.value: (
        default_configuration().idle_timeout(level),
        default_configuration().absolute_timeout(level),
    )
    for level in (
        AuthenticationAssuranceLevel.LOW,
        AuthenticationAssuranceLevel.SUBSTANTIAL,
        AuthenticationAssuranceLevel.HIGH,
    )
}


def assert_request_origin(origin: str) -> None:
    """Origin validation at the edge of every command."""
    assert_declared_origin(origin)
