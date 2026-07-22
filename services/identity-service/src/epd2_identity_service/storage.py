"""`IdentityRecordStore` protocol and the in-memory reference adapter."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from epd2_identity_service.domain import IdentityRecord


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
