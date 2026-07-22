"""`AccountStore` protocol and the in-memory reference adapter."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from epd2_account_service.domain import Account


class AccountStore(Protocol):
    def save(self, account: Account) -> None: ...

    def get(self, account_id: UUID) -> Account | None: ...


class InMemoryAccountStore:
    def __init__(self) -> None:
        self._accounts: dict[UUID, Account] = {}

    def save(self, account: Account) -> None:
        self._accounts[account.account_id] = account

    def get(self, account_id: UUID) -> Account | None:
        return self._accounts.get(account_id)
