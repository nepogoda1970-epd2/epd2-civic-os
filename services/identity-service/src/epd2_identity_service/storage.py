"""`IdentityRecordStore`/`AuthenticationContextStore` protocols and their
in-memory reference adapters. `AuthenticationContextStore` (canon 19d.8,
canon-0.6.0) added in the PACK-07 implementation round."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from epd2_identity_service.domain import AuthenticationContext, IdentityRecord


class IdentityRecordStore(Protocol):
    def save(self, record: IdentityRecord) -> None: ...

    def get(self, identity_record_id: UUID) -> IdentityRecord | None: ...

    def get_by_account_id(self, account_id: UUID) -> IdentityRecord | None: ...


class InMemoryIdentityRecordStore:
    def __init__(self) -> None:
        self._records: dict[UUID, IdentityRecord] = {}

    def save(self, record: IdentityRecord) -> None:
        self._records[record.identity_record_id] = record

    def get(self, identity_record_id: UUID) -> IdentityRecord | None:
        return self._records.get(identity_record_id)

    def get_by_account_id(self, account_id: UUID) -> IdentityRecord | None:
        for record in self._records.values():
            if record.account_id == account_id:
                return record
        return None


class AuthenticationContextStore(Protocol):
    def save(self, context: AuthenticationContext) -> None: ...

    def get(self, authentication_context_id: UUID) -> AuthenticationContext | None: ...

    def get_latest_for_account(self, account_id: UUID) -> AuthenticationContext | None: ...


class InMemoryAuthenticationContextStore:
    """Reference adapter. `get_latest_for_account` returns the most
    recently saved context for the account - a durable backend would
    order by `session_authenticated_at` instead; this in-memory adapter
    uses insertion order, sufficient for tests and contract fixtures."""

    def __init__(self) -> None:
        self._contexts: dict[UUID, AuthenticationContext] = {}
        self._by_account_order: list[UUID] = []

    def save(self, context: AuthenticationContext) -> None:
        if context.authentication_context_id not in self._contexts:
            self._by_account_order.append(context.authentication_context_id)
        self._contexts[context.authentication_context_id] = context

    def get(self, authentication_context_id: UUID) -> AuthenticationContext | None:
        return self._contexts.get(authentication_context_id)

    def get_latest_for_account(self, account_id: UUID) -> AuthenticationContext | None:
        for context_id in reversed(self._by_account_order):
            context = self._contexts[context_id]
            if context.account_id == account_id:
                return context
        return None
