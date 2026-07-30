"""Durable reference persistence for every PACK-14 aggregate.

These adapters satisfy the same `Protocol`s as the in-memory ones in
`account_security_storage`, and they are the **default runtime binding**.
The in-memory adapters remain, explicitly, as *test* adapters: they are
the ones a unit test reaches for when it is not exercising persistence,
and `tests/repository/test_pack14_default_binding.py` asserts that the
runtime composition root does not use them.

The storage engine is SQLite through the standard library. That choice is
what makes this path **real and testable in CI without adding a
dependency**, and it is the whole of the claim: **no production database
is deployed and no production durability is claimed.** A deployment binds
PostgreSQL behind the same ports, and `PACK14_MIGRATIONS`' artefacts are
the DDL it starts from.

Four properties this module exists to make real rather than described:

- **Transaction boundaries.** `UnitOfWork` is the only place a
  multi-statement change commits. A failure inside it rolls back, so a
  half-written account with a credential and no session cannot survive.
- **Optimistic concurrency.** Versioned aggregates update
  `WHERE version = <expected>`; a zero row count is
  `RESOURCE_VERSION_STALE`, not a silent overwrite.
- **The constraints are the database's.** Contact uniqueness, one open
  closure request, one open recovery case, single-use artifact digests
  and nonce uniqueness are enforced by the schema, so a concurrent writer
  cannot get past them.
- **Nothing secret is stored.** Every column and every `document` blob is
  produced by `codecs`, which refuses raw bytes and encodes secrets only
  as `HashedSecret` digests.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Any, TypeVar
from uuid import UUID

from epd2_identity_service.accounts import (
    AccountClosureRequest,
    AccountLock,
    AccountRegistryRecord,
    AccountRestriction,
)
from epd2_identity_service.authentication import AuthenticationAttempt, AuthenticationChallenge
from epd2_identity_service.bootstrap import (
    AuthenticationBootstrapRequest,
    AuthenticationBootstrapResponse,
    BootstrapRedemption,
)
from epd2_identity_service.codecs import decode_dataclass, encode_dataclass
from epd2_identity_service.contacts import AccountContact
from epd2_identity_service.credentials import Credential
from epd2_identity_service.exceptions import (
    ResourceVersionStaleError,
    UnrestrictedMappingLookupRefusedError,
)
from epd2_identity_service.identifiers import (
    AccountId,
    CredentialId,
    MappingPurpose,
    OrganizationScope,
    SessionId,
)
from epd2_identity_service.linking import AccountLinkRequest
from epd2_identity_service.mappings import (
    IdentityMapping,
    MappingResolutionRequest,
    refuse_unrestricted_lookup,
)
from epd2_identity_service.mfa import MfaFactor, RecoveryCodeSet
from epd2_identity_service.passkeys import PasskeyCredentialRecord, WebAuthnChallenge
from epd2_identity_service.persistence import IdempotencyRecord, ReplayNonceRecord
from epd2_identity_service.proofing import IdentityProofingCase
from epd2_identity_service.recovery import RecoveryRequest, RecoveryState
from epd2_identity_service.sessions import SessionRecord
from epd2_identity_service.stepup import StepUpChallenge, StepUpResult
from epd2_identity_service.voting_handoff import (
    VotingHandoffIssuance,
    VotingHandoffRedemptionReference,
)

T = TypeVar("T")


def _document(instance: Any) -> str:
    """The canonical JSON blob. Sorted keys, so two writes of one value
    produce one byte string and a checksum over a row means something."""
    return json.dumps(encode_dataclass(instance), sort_keys=True, separators=(",", ":"))


def _load(cls: type[T], row: sqlite3.Row | None) -> T | None:  # noqa: UP047 - PEP 695 generics are not parsed by the pinned mypy
    if row is None:
        return None
    return decode_dataclass(cls, json.loads(row["document"]))


def _text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    return str(value)


@dataclass
class UnitOfWork:
    """The transaction boundary, as an object a command holds.

    A command opens one, does its reads and writes through the stores,
    and either commits or rolls back as a whole. Nothing in this package
    writes outside one, which is what makes "no partial account,
    credential or session state" a property rather than an intention.
    """

    connection: sqlite3.Connection
    _depth: int = 0

    @contextmanager
    def __call__(self) -> Iterator[UnitOfWork]:
        if self._depth == 0:
            self.connection.execute("BEGIN IMMEDIATE")
        self._depth += 1
        try:
            yield self
        except BaseException:
            self._depth -= 1
            if self._depth == 0:
                self.connection.execute("ROLLBACK")
            raise
        self._depth -= 1
        if self._depth == 0:
            self.connection.execute("COMMIT")


class _SqlStore:
    """Shared row mechanics. Every adapter below inherits exactly this."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def _replace(self, table: str, columns: dict[str, Any]) -> None:
        names = ", ".join(columns)
        placeholders = ", ".join("?" for _ in columns)
        self._connection.execute(
            f"INSERT OR REPLACE INTO {table} ({names}) VALUES ({placeholders})",
            tuple(columns.values()),
        )

    def _insert(self, table: str, columns: dict[str, Any]) -> None:
        names = ", ".join(columns)
        placeholders = ", ".join("?" for _ in columns)
        self._connection.execute(
            f"INSERT INTO {table} ({names}) VALUES ({placeholders})", tuple(columns.values())
        )

    def _save_versioned(
        self, table: str, *, key: str, key_value: str, columns: dict[str, Any], version: int
    ) -> None:
        """Insert at version 1, otherwise update guarded by monotonicity.

        The guard is `version < :new_version` rather than
        `version = :new_version - 1`, because a single command may apply
        several domain transitions before it saves - `verify_contact`
        moves a contact through `verification_pending` to `verified` and
        writes once, arriving at version 3 over a stored version 1. What
        must never happen is a write that does **not** advance the
        version, and that is exactly what this refuses.

        A zero row count means another writer moved the aggregate to at
        least this version between this caller's read and its write. That
        is a refusal (`RESOURCE_VERSION_STALE`), never a
        last-writer-wins overwrite - overwriting is how a revoked
        credential comes back.
        """
        if version == 1:
            self._insert(table, {key: key_value, **columns})
            return
        assignments = ", ".join(f"{name} = ?" for name in columns)
        cursor = self._connection.execute(
            f"UPDATE {table} SET {assignments} WHERE {key} = ? AND version < ?",
            (*columns.values(), key_value, version),
        )
        if cursor.rowcount != 1:
            raise ResourceVersionStaleError(
                f"{table} row {key_value} is already at version {version} or beyond; "
                "the write is stale"
            )

    def _one(self, sql: str, parameters: tuple[Any, ...]) -> sqlite3.Row | None:
        row: sqlite3.Row | None = self._connection.execute(sql, parameters).fetchone()
        return row

    def _all(self, sql: str, parameters: tuple[Any, ...]) -> list[sqlite3.Row]:
        return self._connection.execute(sql, parameters).fetchall()


# --- Account registry -------------------------------------------------------


class SqlAccountRegistryStore(_SqlStore):
    def save(self, record: AccountRegistryRecord) -> None:
        self._save_versioned(
            "account_registry_record",
            key="account_id",
            key_value=str(record.account_id),
            columns={
                "account_status": record.account_status.value,
                "scope_level": record.scope.level.value,
                "scope_unit_id": str(record.scope.organizational_unit_id),
                "created_at": _text(record.created_at),
                "activated_at": _text(record.activated_at),
                "anonymization_state": record.anonymization_state.value,
                "version": record.version,
                "retention_class": "account_record",
                "legal_hold": 0,
                "document": _document(record),
            },
            version=record.version,
        )

    def get(self, account_id: AccountId) -> AccountRegistryRecord | None:
        return _load(
            AccountRegistryRecord,
            self._one(
                "SELECT document FROM account_registry_record WHERE account_id = ?",
                (str(account_id),),
            ),
        )

    def save_lock(self, lock: AccountLock) -> None:
        self._replace(
            "account_lock",
            {
                "lock_id": str(lock.lock_id),
                "account_id": str(lock.account_id),
                "cause": lock.cause.value,
                "reason_code": lock.reason_code,
                "locked_at": _text(lock.locked_at),
                "expires_at": _text(lock.expires_at),
                "released_at": _text(lock.released_at),
                "retention_class": "suspicious_activity",
                "legal_hold": 0,
                "document": _document(lock),
            },
        )

    def locks_for(self, account_id: AccountId) -> tuple[AccountLock, ...]:
        rows = self._all(
            "SELECT document FROM account_lock WHERE account_id = ? ORDER BY locked_at",
            (str(account_id),),
        )
        return tuple(decode_dataclass(AccountLock, json.loads(row["document"])) for row in rows)

    def save_restriction(self, restriction: AccountRestriction) -> None:
        self._replace(
            "account_restriction",
            {
                "restriction_id": str(restriction.restriction_id),
                "account_id": str(restriction.account_id),
                "restriction_class": restriction.restriction_class.value,
                "authority_reference": restriction.authority_reference,
                "reason_code": restriction.reason_code,
                "applied_at": _text(restriction.applied_at),
                "review_due_at": _text(restriction.review_due_at),
                "expires_at": _text(restriction.expires_at),
                "lifted_at": _text(restriction.lifted_at),
                "retention_class": "suspicious_activity",
                "legal_hold": 0,
                "document": _document(restriction),
            },
        )

    def restrictions_for(self, account_id: AccountId) -> tuple[AccountRestriction, ...]:
        rows = self._all(
            "SELECT document FROM account_restriction WHERE account_id = ? ORDER BY applied_at",
            (str(account_id),),
        )
        return tuple(
            decode_dataclass(AccountRestriction, json.loads(row["document"])) for row in rows
        )

    def save_closure_request(self, request: AccountClosureRequest) -> None:
        self._replace(
            "account_closure_request",
            {
                "closure_request_id": str(request.closure_request_id),
                "account_id": str(request.account_id),
                "state": request.state.value,
                "requested_at": _text(request.requested_at),
                "cooling_off_ends_at": _text(request.cooling_off_ends_at),
                "resolved_at": _text(request.resolved_at),
                "retention_class": "account_record",
                "legal_hold": 0,
                "document": _document(request),
            },
        )

    def open_closure_request(self, account_id: AccountId) -> AccountClosureRequest | None:
        return _load(
            AccountClosureRequest,
            self._one(
                "SELECT document FROM account_closure_request"
                " WHERE account_id = ? AND state IN ('requested','cooling_off')",
                (str(account_id),),
            ),
        )


# --- Contacts ---------------------------------------------------------------


class SqlAccountContactStore(_SqlStore):
    def save(self, contact: AccountContact) -> None:
        self._save_versioned(
            "account_contact",
            key="contact_id",
            key_value=str(contact.contact_id),
            columns={
                "account_id": str(contact.account_id),
                "channel_class": contact.channel_class.value,
                "normalized_digest": contact.normalized_digest.digest,
                "masked_value": contact.masked_value,
                "status": contact.status.value,
                "scope_level": contact.uniqueness_scope.scope.level.value,
                "scope_unit_id": str(contact.uniqueness_scope.scope.organizational_unit_id),
                "added_at": _text(contact.added_at),
                "verified_at": _text(contact.verified_at),
                "changed_at": _text(contact.changed_at),
                "retention_class": contact.retention_class,
                "legal_hold": 0,
                "version": contact.version,
                "document": _document(contact),
            },
            version=contact.version,
        )

    def get(self, contact_id: UUID) -> AccountContact | None:
        return _load(
            AccountContact,
            self._one(
                "SELECT document FROM account_contact WHERE contact_id = ?", (str(contact_id),)
            ),
        )

    def for_account(self, account_id: AccountId) -> tuple[AccountContact, ...]:
        rows = self._all(
            "SELECT document FROM account_contact WHERE account_id = ? ORDER BY added_at",
            (str(account_id),),
        )
        return tuple(decode_dataclass(AccountContact, json.loads(row["document"])) for row in rows)

    def within_scope(self, contact: AccountContact) -> tuple[AccountContact, ...]:
        rows = self._all(
            "SELECT document FROM account_contact"
            " WHERE channel_class = ? AND scope_level = ? AND scope_unit_id = ?",
            (
                contact.channel_class.value,
                contact.uniqueness_scope.scope.level.value,
                str(contact.uniqueness_scope.scope.organizational_unit_id),
            ),
        )
        return tuple(decode_dataclass(AccountContact, json.loads(row["document"])) for row in rows)


# --- Credentials ------------------------------------------------------------


class SqlCredentialStore(_SqlStore):
    def save(self, credential: Credential) -> None:
        self._save_versioned(
            "credential",
            key="credential_id",
            key_value=str(credential.credential_id),
            columns={
                "account_id": str(credential.account_id),
                "credential_type": credential.credential_type.value,
                "status": credential.status.value,
                "created_at": _text(credential.created_at),
                "last_used_at": _text(credential.last_used_at),
                "expires_at": _text(credential.expires_at),
                "version": credential.version,
                "retention_class": "credential_metadata",
                "legal_hold": 0,
                "document": _document(credential),
            },
            version=credential.version,
        )

    def get(self, credential_id: CredentialId) -> Credential | None:
        return _load(
            Credential,
            self._one(
                "SELECT document FROM credential WHERE credential_id = ?", (str(credential_id),)
            ),
        )

    def for_account(self, account_id: AccountId) -> tuple[Credential, ...]:
        rows = self._all(
            "SELECT document FROM credential WHERE account_id = ? ORDER BY created_at",
            (str(account_id),),
        )
        return tuple(decode_dataclass(Credential, json.loads(row["document"])) for row in rows)

    def save_passkey(self, record: PasskeyCredentialRecord) -> None:
        self._replace(
            "passkey_credential",
            {
                "credential_id": str(record.credential_id),
                "account_id": str(record.account_id),
                "credential_reference": record.credential_reference,
                "public_key": record.public_key,
                "sign_counter": record.sign_counter,
                "binding": record.binding.value,
                "relying_party_origin": record.relying_party_origin,
                "retention_class": "credential_metadata",
                "legal_hold": 0,
                "document": _document(record),
            },
        )

    def passkey_by_reference(self, credential_reference: str) -> PasskeyCredentialRecord | None:
        return _load(
            PasskeyCredentialRecord,
            self._one(
                "SELECT document FROM passkey_credential WHERE credential_reference = ?",
                (credential_reference,),
            ),
        )

    def save_factor(self, factor: MfaFactor) -> None:
        self._replace(
            "mfa_factor",
            {
                "factor_id": str(factor.factor_id),
                "account_id": str(factor.account_id),
                "factor_class": factor.factor_class.value,
                "status": factor.status.value,
                "enrolled_at": _text(factor.enrolled_at),
                "confirmed_at": _text(factor.confirmed_at),
                "revoked_at": _text(factor.revoked_at),
                "retention_class": "credential_metadata",
                "legal_hold": 0,
                "document": _document(factor),
            },
        )

    def factors_for(self, account_id: AccountId) -> tuple[MfaFactor, ...]:
        rows = self._all(
            "SELECT document FROM mfa_factor WHERE account_id = ? ORDER BY enrolled_at",
            (str(account_id),),
        )
        return tuple(decode_dataclass(MfaFactor, json.loads(row["document"])) for row in rows)

    def save_recovery_codes(self, code_set: RecoveryCodeSet) -> None:
        self._replace(
            "recovery_code_set",
            {
                "set_id": str(code_set.set_id),
                "account_id": str(code_set.account_id),
                "issued_at": _text(code_set.issued_at),
                "revoked_at": _text(code_set.revoked_at),
                "retention_class": "credential_metadata",
                "legal_hold": 0,
                "document": _document(code_set),
            },
        )

    def active_recovery_codes(self, account_id: AccountId) -> RecoveryCodeSet | None:
        rows = self._all(
            "SELECT document FROM recovery_code_set"
            " WHERE account_id = ? AND revoked_at IS NULL ORDER BY issued_at DESC",
            (str(account_id),),
        )
        for row in rows:
            code_set = decode_dataclass(RecoveryCodeSet, json.loads(row["document"]))
            if code_set.is_active():
                return code_set
        return None


# --- Authentication ---------------------------------------------------------


class SqlAuthenticationStore(_SqlStore):
    def save_attempt(self, attempt: AuthenticationAttempt) -> None:
        self._replace(
            "authentication_attempt",
            {
                "attempt_id": str(attempt.attempt_id),
                "workspace": attempt.workspace.value,
                "method_class": attempt.method.value,
                "outcome_kind": attempt.outcome.kind.value,
                "reason_code": attempt.outcome.internal_reason_code,
                "attempted_at": _text(attempt.attempted_at),
                "retention_class": "authentication_attempts",
                "document": _document(attempt),
            },
        )

    def save_challenge(self, challenge: AuthenticationChallenge) -> None:
        self._replace(
            "authentication_challenge",
            {
                "challenge_id": str(challenge.challenge_id),
                "workspace": challenge.workspace.value,
                "method": challenge.method.value,
                "issued_at": _text(challenge.issued_at),
                "expires_at": _text(challenge.expires_at),
                "consumed_at": _text(challenge.consumed_at),
                "document": _document(challenge),
            },
        )

    def get_challenge(self, challenge_id: UUID) -> AuthenticationChallenge | None:
        return _load(
            AuthenticationChallenge,
            self._one(
                "SELECT document FROM authentication_challenge WHERE challenge_id = ?",
                (str(challenge_id),),
            ),
        )

    def save_webauthn_challenge(self, challenge: WebAuthnChallenge) -> None:
        self._replace(
            "webauthn_challenge",
            {
                "challenge_id": str(challenge.challenge_id),
                "account_id": str(challenge.account_id),
                "ceremony": challenge.ceremony,
                "issued_at": _text(challenge.issued_at),
                "expires_at": _text(challenge.expires_at),
                "consumed_at": _text(challenge.consumed_at),
                "document": _document(challenge),
            },
        )

    def get_webauthn_challenge(self, challenge_id: UUID) -> WebAuthnChallenge | None:
        return _load(
            WebAuthnChallenge,
            self._one(
                "SELECT document FROM webauthn_challenge WHERE challenge_id = ?",
                (str(challenge_id),),
            ),
        )


# --- Sessions and step-up ---------------------------------------------------


class SqlSessionStore(_SqlStore):
    def save(self, session: SessionRecord) -> None:
        self._replace(
            "session_record",
            {
                "session_id": str(session.session_id),
                "account_id": str(session.account_id),
                "workspace": session.scope.workspace.value,
                "origin": session.scope.origin,
                "status": session.status.value,
                "assurance": session.assurance.effective_level.value,
                "issued_at": _text(session.issued_at),
                "last_activity_at": _text(session.last_activity_at),
                "idle_deadline": _text(session.idle_deadline),
                "absolute_deadline": _text(session.absolute_deadline),
                "refresh_family_id": str(session.refresh_family.family_id),
                "retention_class": "session_history",
                "legal_hold": 0,
                "document": _document(session),
            },
        )

    def get(self, session_id: SessionId) -> SessionRecord | None:
        return _load(
            SessionRecord,
            self._one(
                "SELECT document FROM session_record WHERE session_id = ?", (str(session_id),)
            ),
        )

    def for_account(self, account_id: AccountId) -> tuple[SessionRecord, ...]:
        rows = self._all(
            "SELECT document FROM session_record WHERE account_id = ? ORDER BY issued_at",
            (str(account_id),),
        )
        return tuple(decode_dataclass(SessionRecord, json.loads(row["document"])) for row in rows)

    def save_step_up_challenge(self, challenge: StepUpChallenge) -> None:
        self._replace(
            "step_up_challenge",
            {
                "challenge_id": str(challenge.challenge_id),
                "actor_reference": challenge.binding.actor_reference.reference,
                "session_id": str(challenge.binding.session_id),
                "action_code": challenge.binding.action_code,
                "resource_type": challenge.binding.resource_type,
                "resource_id": str(challenge.binding.resource_id),
                "resource_version": challenge.binding.resource_version,
                "required_assurance": challenge.required_assurance.value,
                "status": challenge.status.value,
                "issued_at": _text(challenge.issued_at),
                "expires_at": _text(challenge.expires_at),
                "document": _document(challenge),
            },
        )

    def get_step_up_challenge(self, challenge_id: UUID) -> StepUpChallenge | None:
        return _load(
            StepUpChallenge,
            self._one(
                "SELECT document FROM step_up_challenge WHERE challenge_id = ?",
                (str(challenge_id),),
            ),
        )

    def save_step_up_result(self, result: StepUpResult) -> None:
        self._replace(
            "step_up_result",
            {
                "challenge_id": str(result.challenge_id),
                "actor_reference": result.binding.actor_reference.reference,
                "session_id": str(result.binding.session_id),
                "action_code": result.binding.action_code,
                "resource_id": str(result.binding.resource_id),
                "resource_version": result.binding.resource_version,
                "status": result.status.value,
                "completed_at": _text(result.completed_at),
                "expires_at": _text(result.expires_at),
                "document": _document(result),
            },
        )

    def get_step_up_result(self, challenge_id: UUID) -> StepUpResult | None:
        return _load(
            StepUpResult,
            self._one(
                "SELECT document FROM step_up_result WHERE challenge_id = ?", (str(challenge_id),)
            ),
        )


# --- Recovery and proofing --------------------------------------------------


class SqlRecoveryStore(_SqlStore):
    def save(self, request: RecoveryRequest) -> None:
        self._save_versioned(
            "recovery_case",
            key="recovery_id",
            key_value=str(request.recovery_id),
            columns={
                "account_id": str(request.account_id),
                "state": request.state.value,
                "requester_reference": request.requester_reference.reference,
                "requested_at": _text(request.requested_at),
                "cooling_off_ends_at": _text(request.cooling_off_ends_at),
                "emergency": int(request.emergency),
                "credentials_revoked": int(request.credentials_revoked),
                "sessions_revoked": int(request.sessions_revoked),
                "dispute_open": int(request.dispute is not None),
                "version": request.version,
                "retention_class": "recovery_evidence",
                "legal_hold": 0,
                "document": _document(request),
            },
            version=request.version,
        )

    def get(self, recovery_id: UUID) -> RecoveryRequest | None:
        return _load(
            RecoveryRequest,
            self._one(
                "SELECT document FROM recovery_case WHERE recovery_id = ?", (str(recovery_id),)
            ),
        )

    def open_case_for(self, account_id: AccountId) -> RecoveryRequest | None:
        terminal = (
            RecoveryState.COMPLETED.value,
            RecoveryState.REJECTED.value,
            RecoveryState.CANCELLED.value,
        )
        return _load(
            RecoveryRequest,
            self._one(
                "SELECT document FROM recovery_case"
                " WHERE account_id = ? AND state NOT IN (?, ?, ?)",
                (str(account_id), *terminal),
            ),
        )


class SqlIdentityProofingStore(_SqlStore):
    def save(self, case: IdentityProofingCase) -> None:
        self._save_versioned(
            "identity_proofing_case",
            key="case_id",
            key_value=str(case.case_id),
            columns={
                "account_id": str(case.account_id),
                "person_record_id": _text(case.person_record_id),
                "method": case.method.value,
                "requested_assurance": case.requested_assurance.value,
                "state": case.state.value,
                "started_at": _text(case.started_at),
                "version": case.version,
                "retention_class": "proofing_evidence",
                "legal_hold": 0,
                "document": _document(case),
            },
            version=case.version,
        )

    def get(self, case_id: UUID) -> IdentityProofingCase | None:
        return _load(
            IdentityProofingCase,
            self._one(
                "SELECT document FROM identity_proofing_case WHERE case_id = ?", (str(case_id),)
            ),
        )

    def for_account(self, account_id: AccountId) -> tuple[IdentityProofingCase, ...]:
        rows = self._all(
            "SELECT document FROM identity_proofing_case WHERE account_id = ? ORDER BY started_at",
            (str(account_id),),
        )
        return tuple(
            decode_dataclass(IdentityProofingCase, json.loads(row["document"])) for row in rows
        )


# --- Bootstrap and voting handoff -------------------------------------------


class SqlBootstrapStore(_SqlStore):
    def save_request(self, request: AuthenticationBootstrapRequest) -> None:
        self._replace(
            "bootstrap_request",
            {
                "request_id": str(request.request_id),
                "workspace": request.workspace.value,
                "audience_origin": request.audience_origin,
                "created_at": _text(request.created_at),
                "expires_at": _text(request.expires_at),
                "document": _document(request),
            },
        )

    def get_request(self, request_id: UUID) -> AuthenticationBootstrapRequest | None:
        return _load(
            AuthenticationBootstrapRequest,
            self._one(
                "SELECT document FROM bootstrap_request WHERE request_id = ?", (str(request_id),)
            ),
        )

    def save_response(self, response: AuthenticationBootstrapResponse) -> None:
        self._replace(
            "bootstrap_response",
            {
                "response_id": str(response.response_id),
                "request_id": str(response.request_id),
                "workspace": response.workspace.value,
                "audience_origin": response.audience_origin,
                "value_digest": response.value_digest.digest,
                "issued_at": _text(response.issued_at),
                "expires_at": _text(response.expires_at),
                "redeemed_at": _text(response.redeemed_at),
                "document": _document(response),
            },
        )

    def get_response(self, response_id: UUID) -> AuthenticationBootstrapResponse | None:
        return _load(
            AuthenticationBootstrapResponse,
            self._one(
                "SELECT document FROM bootstrap_response WHERE response_id = ?",
                (str(response_id),),
            ),
        )

    def save_redemption(self, redemption: BootstrapRedemption) -> None:
        self._replace(
            "bootstrap_redemption",
            {
                "response_id": str(redemption.response_id),
                "redemption_id": str(redemption.redemption_id),
                "workspace": redemption.workspace.value,
                "redeemed_at": _text(redemption.redeemed_at),
                "value_digest": redemption.value_digest.digest,
                "document": _document(redemption),
            },
        )

    def redemption_for(self, response_id: UUID) -> BootstrapRedemption | None:
        return _load(
            BootstrapRedemption,
            self._one(
                "SELECT document FROM bootstrap_redemption WHERE response_id = ?",
                (str(response_id),),
            ),
        )


class SqlVotingHandoffStore(_SqlStore):
    """Note what this class does not have.

    There is no `issuances_for_account`, because the table has no account
    column; and there is no `account_for_redemption`, because that
    question is the reverse bridge ADR-088 forbids. Adding either would
    require a migration that adds a column, which is why the absence is
    visible in `0008_bootstrap_and_handoff.sql` too.
    """

    def save_issuance(self, issuance: VotingHandoffIssuance) -> None:
        self._replace(
            "voting_handoff_issuance",
            {
                "artifact_id": str(issuance.artifact_id),
                "value_digest": issuance.value_digest.digest,
                "voting_context_id": str(issuance.voting_context_id),
                "purpose": issuance.purpose,
                "audience_origin": issuance.audience_origin,
                "issued_at": _text(issuance.issued_at),
                "expires_at": _text(issuance.expires_at),
                "redeemed_at": _text(issuance.redeemed_at),
                "retention_class": "voting_handoff_issuance",
                "document": _document(issuance),
            },
        )

    def get_issuance(self, artifact_id: UUID) -> VotingHandoffIssuance | None:
        return _load(
            VotingHandoffIssuance,
            self._one(
                "SELECT document FROM voting_handoff_issuance WHERE artifact_id = ?",
                (str(artifact_id),),
            ),
        )

    def save_redemption(self, redemption: VotingHandoffRedemptionReference) -> None:
        self._replace(
            "voting_handoff_redemption",
            {
                "redemption_id": str(redemption.redemption_id),
                "artifact_id": str(redemption.artifact_id),
                "voting_context_id": str(redemption.voting_context_id),
                "redeemed_at": _text(redemption.redeemed_at),
                "document": _document(redemption),
            },
        )


# --- Mappings, linking and replay prevention --------------------------------


class SqlIdentityMappingStore(_SqlStore):
    def save(self, mapping: IdentityMapping) -> None:
        self._replace(
            "identity_mapping",
            {
                "mapping_id": str(mapping.mapping_id),
                "purpose": mapping.purpose.value,
                "scope_level": mapping.scope.level.value,
                "scope_unit_id": str(mapping.scope.organizational_unit_id),
                "domain_owner": mapping.domain_owner,
                "source_reference": mapping.source_reference.reference,
                "status": mapping.status.value,
                "retention_class": mapping.retention_class,
                "audit_reference": mapping.audit_reference,
                "created_at": _text(mapping.created_at),
                "expires_at": _text(mapping.expires_at),
                "legal_hold": 0,
                "document": _document(mapping),
            },
        )

    def resolve(self, request: MappingResolutionRequest) -> IdentityMapping | None:
        return _load(
            IdentityMapping,
            self._one(
                "SELECT document FROM identity_mapping"
                " WHERE purpose = ? AND scope_level = ? AND scope_unit_id = ?"
                " AND source_reference = ?",
                (
                    request.purpose.value,
                    request.scope.level.value,
                    str(request.scope.organizational_unit_id),
                    request.source_reference.reference,
                ),
            ),
        )

    def enumerate(
        self, *, purpose: MappingPurpose | None, scope: OrganizationScope | None
    ) -> tuple[IdentityMapping, ...]:
        """There is no query shape here that returns every mapping.

        `refuse_unrestricted_lookup` raises when either a purpose or a
        scope is missing, so the SQL below can only ever be reached with
        both bound - which is the whole reason the refusal is a call and
        not a comment.
        """
        refuse_unrestricted_lookup(purpose=purpose, scope=scope)
        if purpose is None or scope is None:  # pragma: no cover - refused above
            raise UnrestrictedMappingLookupRefusedError("a purpose and a scope are required")
        rows = self._all(
            "SELECT document FROM identity_mapping"
            " WHERE purpose = ? AND scope_level = ? AND scope_unit_id = ?",
            (purpose.value, scope.level.value, str(scope.organizational_unit_id)),
        )
        return tuple(decode_dataclass(IdentityMapping, json.loads(row["document"])) for row in rows)


class SqlAccountLinkStore(_SqlStore):
    def save(self, request: AccountLinkRequest) -> None:
        self._replace(
            "account_link_request",
            {
                "link_request_id": str(request.link_request_id),
                "account_id": str(request.account_id),
                "kind": request.kind.value,
                "state": request.state.value,
                "requested_at": _text(request.requested_at),
                "decided_at": _text(request.decided_at),
                "document": _document(request),
            },
        )

    def get(self, link_request_id: UUID) -> AccountLinkRequest | None:
        return _load(
            AccountLinkRequest,
            self._one(
                "SELECT document FROM account_link_request WHERE link_request_id = ?",
                (str(link_request_id),),
            ),
        )

    def for_account(self, account_id: AccountId) -> tuple[AccountLinkRequest, ...]:
        rows = self._all(
            "SELECT document FROM account_link_request WHERE account_id = ? ORDER BY requested_at",
            (str(account_id),),
        )
        return tuple(
            decode_dataclass(AccountLinkRequest, json.loads(row["document"])) for row in rows
        )


class SqlReplayPreventionStore(_SqlStore):
    """The store that has to survive a restart to mean anything.

    A nonce set held in a process is a nonce set that resets when the
    process does, and an artifact that was single-use before the restart
    is replayable after it. These four tables are the reason
    `test_pack14_persistence.py` restarts the application and presents a
    spent artifact again.
    """

    def record_nonce(self, record: ReplayNonceRecord) -> None:
        self._replace(
            "replay_nonce",
            {
                "nonce_digest": record.nonce_digest.digest,
                "purpose": record.purpose,
                "consumed_at": _text(record.consumed_at),
                "expires_at": _text(record.expires_at),
            },
        )

    def seen_nonce_digests(self) -> frozenset[str]:
        rows = self._all("SELECT nonce_digest FROM replay_nonce", ())
        return frozenset(row["nonce_digest"] for row in rows)

    def record_idempotency(self, record: IdempotencyRecord) -> None:
        self._replace(
            "idempotency_record",
            {
                "idempotency_key": record.idempotency_key,
                "operation": record.operation,
                "request_digest": record.request_digest,
                "recorded_at": _text(record.recorded_at),
            },
        )

    def get_idempotency(self, idempotency_key: str) -> IdempotencyRecord | None:
        row = self._one(
            "SELECT idempotency_key, operation, request_digest, recorded_at"
            " FROM idempotency_record WHERE idempotency_key = ?",
            (idempotency_key,),
        )
        if row is None:
            return None
        return IdempotencyRecord(
            idempotency_key=row["idempotency_key"],
            request_digest=row["request_digest"],
            operation=row["operation"],
            recorded_at=datetime.fromisoformat(row["recorded_at"]),
        )

    def seen_assertion_ids(self) -> frozenset[str]:
        rows = self._all("SELECT assertion_id FROM external_assertion_seen", ())
        return frozenset(row["assertion_id"] for row in rows)

    def record_assertion_id(self, assertion_id: str) -> None:
        """`seen_at` comes from the database rather than from a Python
        clock, because this store has no `Clock` and inventing one here
        would put a second source of time in the package."""
        self._connection.execute(
            "INSERT OR REPLACE INTO external_assertion_seen (assertion_id, seen_at)"
            " VALUES (?, strftime('%Y-%m-%dT%H:%M:%SZ','now'))",
            (assertion_id,),
        )
