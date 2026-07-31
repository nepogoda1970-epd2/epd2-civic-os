"""Storage ports for the PACK-15 voting credential issuer (VC-04).

Three stores, deliberately separate, and the separation is the point:

* `SpentNonceSet` - **a set**. Its only question is "was this nonce
  spent?". It has no value column and no method that returns anything
  produced by a nonce.
* `VotingCredentialStore` - credentials and their status. No assertion
  reference, no nonce, no participant.
* `CredentialIdempotencyStore` - a **bounded** retry-window cache. Entries
  expire; `purge_expired` is what stops the cache from becoming the
  durable assertion-to-credential map ADR-093 forbids.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Protocol
from uuid import UUID

from epd2_credential_service.voting_credentials import (
    CredentialIssuanceIdempotencyRecord,
    CredentialRedemption,
    CredentialReplayRecord,
    CredentialStatus,
    SpentNonce,
    VotingCredential,
)


class SpentNonceSet(Protocol):
    """Set membership only. Adding a `get_credential_for(nonce)` method to
    this Protocol would be the ADR-093 violation."""

    def contains(self, nonce: str) -> bool: ...

    def add(self, spent: SpentNonce) -> bool:
        """Add atomically. Returns False if the nonce was already spent."""
        ...

    def count(self, voting_context_reference: str) -> int: ...


class VotingCredentialStore(Protocol):
    def save(self, credential: VotingCredential) -> None: ...

    def get(self, voting_credential_id: UUID) -> VotingCredential | None: ...

    def count_by_status(self, voting_context_reference: str, status: CredentialStatus) -> int: ...


class CredentialIdempotencyStore(Protocol):
    def get(self, idempotency_key: str) -> CredentialIssuanceIdempotencyRecord | None: ...

    def put(self, record: CredentialIssuanceIdempotencyRecord) -> None: ...

    def purge_expired(self, now: datetime) -> int: ...


class CredentialRedemptionStore(Protocol):
    def save(self, redemption: CredentialRedemption) -> None: ...

    def get(self, redemption_reference: str) -> CredentialRedemption | None: ...

    def count(self, voting_context_reference: str) -> int: ...


class CredentialReplayStore(Protocol):
    def record(self, replay: CredentialReplayRecord) -> None: ...

    def count(self, voting_context_reference: str) -> int: ...

    def all_for_context(
        self, voting_context_reference: str
    ) -> Sequence[CredentialReplayRecord]: ...


# ---------------------------------------------------------------------------
# In-memory reference adapters (test bindings)
# ---------------------------------------------------------------------------


class InMemorySpentNonceSet:
    def __init__(self) -> None:
        self._spent: dict[str, SpentNonce] = {}

    def contains(self, nonce: str) -> bool:
        return nonce in self._spent

    def add(self, spent: SpentNonce) -> bool:
        if spent.nonce in self._spent:
            return False
        self._spent[spent.nonce] = spent
        return True

    def count(self, voting_context_reference: str) -> int:
        return sum(
            1
            for spent in self._spent.values()
            if spent.voting_context_reference == voting_context_reference
        )


class InMemoryVotingCredentialStore:
    def __init__(self) -> None:
        self._credentials: dict[UUID, VotingCredential] = {}

    def save(self, credential: VotingCredential) -> None:
        self._credentials[credential.voting_credential_id] = credential

    def get(self, voting_credential_id: UUID) -> VotingCredential | None:
        return self._credentials.get(voting_credential_id)

    def count_by_status(self, voting_context_reference: str, status: CredentialStatus) -> int:
        return sum(
            1
            for credential in self._credentials.values()
            if credential.voting_context_reference == voting_context_reference
            and credential.status is status
        )


class InMemoryCredentialIdempotencyStore:
    def __init__(self) -> None:
        self._records: dict[str, CredentialIssuanceIdempotencyRecord] = {}

    def get(self, idempotency_key: str) -> CredentialIssuanceIdempotencyRecord | None:
        return self._records.get(idempotency_key)

    def put(self, record: CredentialIssuanceIdempotencyRecord) -> None:
        self._records[record.idempotency_key] = record

    def purge_expired(self, now: datetime) -> int:
        expired = [key for key, record in self._records.items() if record.expired(now)]
        for key in expired:
            del self._records[key]
        return len(expired)


class InMemoryCredentialRedemptionStore:
    def __init__(self) -> None:
        self._redemptions: dict[str, CredentialRedemption] = {}

    def save(self, redemption: CredentialRedemption) -> None:
        self._redemptions[redemption.redemption_reference] = redemption

    def get(self, redemption_reference: str) -> CredentialRedemption | None:
        return self._redemptions.get(redemption_reference)

    def count(self, voting_context_reference: str) -> int:
        return sum(
            1
            for redemption in self._redemptions.values()
            if redemption.voting_context_reference == voting_context_reference
        )


class InMemoryCredentialReplayStore:
    def __init__(self) -> None:
        self._replays: list[CredentialReplayRecord] = []

    def record(self, replay: CredentialReplayRecord) -> None:
        self._replays.append(replay)

    def count(self, voting_context_reference: str) -> int:
        return sum(
            1
            for replay in self._replays
            if replay.voting_context_reference == voting_context_reference
        )

    def all_for_context(self, voting_context_reference: str) -> Sequence[CredentialReplayRecord]:
        return tuple(
            replay
            for replay in self._replays
            if replay.voting_context_reference == voting_context_reference
        )


def assert_spent_set_is_not_a_map(store: object) -> None:
    """Refuse a spent-nonce adapter that can answer the forbidden question.

    ADR-093 as a runtime check over the adapter's own surface: a method
    that returns what a nonce produced turns the set into a map.
    """
    forbidden_methods = {
        "get_credential",
        "credential_for",
        "get_credential_for",
        "lookup_credential",
        "resolve",
    }
    offending = sorted(name for name in forbidden_methods if hasattr(store, name))
    if offending:
        raise ValueError(
            "a spent-nonce set may not resolve a nonce to a credential: " + ", ".join(offending)
        )
