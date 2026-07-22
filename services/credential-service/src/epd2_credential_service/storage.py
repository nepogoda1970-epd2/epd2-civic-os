"""Credential storage.

`_CredentialRecord` is internal-only: it carries `issuance_reference` (pack
section 5.3) alongside the public `ParticipationCredential`.
`issuance_reference` is never exposed by any public method here - only
`public_credential()` fields ever leave this module.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from epd2_credential_service.domain import ParticipationCredential
from epd2_credential_service.exceptions import CredentialIssuanceConflictError


@dataclass(frozen=True, slots=True)
class _CredentialRecord:
    public: ParticipationCredential
    issuance_reference: str


class CredentialStore(Protocol):
    def issue(
        self, credential: ParticipationCredential, issuance_reference: str
    ) -> ParticipationCredential:
        """Store a newly issued credential. If `credential.credential_id`
        already exists with identical public content, returns the
        existing public credential (idempotent). If it exists with
        different content, raises `CredentialIssuanceConflictError`.
        """
        ...

    def save(self, credential: ParticipationCredential) -> None:
        """Persist an update to an already-issued credential (e.g. after
        a status transition). Does not change `issuance_reference`."""
        ...

    def get(self, credential_id: UUID) -> ParticipationCredential | None: ...

    def issuance_reference_for(self, credential_id: UUID) -> str | None:
        """Internal-only lookup, used solely for this service's own
        idempotency/revocation bookkeeping - never exposed outside this
        service (see README.md)."""
        ...


class InMemoryCredentialStore:
    def __init__(self) -> None:
        self._records: dict[UUID, _CredentialRecord] = {}

    def issue(
        self, credential: ParticipationCredential, issuance_reference: str
    ) -> ParticipationCredential:
        existing = self._records.get(credential.credential_id)
        if existing is not None:
            if existing.public == credential:
                return existing.public
            raise CredentialIssuanceConflictError(
                f"credential_id {credential.credential_id} already issued with different content"
            )
        self._records[credential.credential_id] = _CredentialRecord(
            public=credential, issuance_reference=issuance_reference
        )
        return credential

    def save(self, credential: ParticipationCredential) -> None:
        existing = self._records.get(credential.credential_id)
        issuance_reference = existing.issuance_reference if existing is not None else ""
        self._records[credential.credential_id] = _CredentialRecord(
            public=credential, issuance_reference=issuance_reference
        )

    def get(self, credential_id: UUID) -> ParticipationCredential | None:
        record = self._records.get(credential_id)
        return record.public if record is not None else None

    def issuance_reference_for(self, credential_id: UUID) -> str | None:
        record = self._records.get(credential_id)
        return record.issuance_reference if record is not None else None
