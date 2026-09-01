"""Storage protocols and in-memory reference adapters for Delegation
Service's two owned entities.

`InMemoryDelegationStore.create` is where canon section 16.1's
prohibition #2 ("две конкурирующие активные делегации одного scope") is
structurally enforced, mirroring
`epd2_voting_service.storage.InMemoryBallotStore.save`'s CT-00-10 rule-
freeze pattern in spirit: a scan for any other stored `Delegation` with
the same `(delegator_actor_id, scope_type, scope_id)` and a "blocking"
status (`draft` or `active` - see `domain.BLOCKING_SCOPE_STATUSES`) rejects
the new one before it is ever persisted.

`InMemoryDelegationSnapshotStore.save` is where canon section 16.1's
prohibition #4 ("изменение snapshot после открытия голосования") is
structurally enforced, mirroring
`epd2_eligibility_service.storage.InMemoryEligibilityRuleStore.save`'s
"rule freeze" pattern exactly, keyed on `(ballot_id, input_hash)` instead
of `(eligibility_rule_id, rule_version)`.
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from epd2_delegation_service.domain import (
    BLOCKING_SCOPE_STATUSES,
    Delegation,
    DelegationSnapshot,
    DelegationStatus,
)
from epd2_delegation_service.exceptions import (
    DelegationCreationConflictError,
    DelegationScopeConflictError,
    SnapshotFrozenError,
    UnknownDelegationError,
)


class DelegationStore(Protocol):
    def create(self, delegation: Delegation) -> Delegation:
        """Create a new `Delegation` (must be `status == draft`).

        If `delegation.delegation_id` already exists with identical
        content, returns the existing record (idempotent - CT-00-04).  If
        it exists with different content, raises
        `DelegationCreationConflictError`.

        Also enforces canon prohibition #2: if another delegation (a
        *different* `delegation_id`) already exists for this
        `(delegator_actor_id, scope_type, scope_id)` triple with a status
        in `domain.BLOCKING_SCOPE_STATUSES` (`draft` or `active`), raises
        `DelegationScopeConflictError` - at most one such delegation may
        exist per triple at a time.
        """
        ...

    def save(self, delegation: Delegation) -> Delegation:
        """Persist a status transition to an already-`create`d
        delegation. Raises `UnknownDelegationError` if no delegation with
        this id was ever `create`d. Unconditionally overwrites - callers
        only ever pass a status-derived successor from
        `Delegation.with_status`, which itself enforces the transition
        table."""
        ...

    def get(self, delegation_id: UUID) -> Delegation | None: ...

    def find_active_delegation_for(
        self, delegator_actor_id: UUID, scope_type: str, scope_id: UUID
    ) -> Delegation | None:
        """The current `active` delegation, if any, *from* this
        `(delegator_actor_id, scope_type, scope_id)` triple (i.e. a record
        whose own `delegator_actor_id` field matches). Used both by
        `application.resolve_active_delegate` (actual resolution) and by
        `application.create_delegation`'s ADR-009 item 9 depth-1 guard
        (checking whether the *proposed new delegate* is themselves
        currently forwarding their own vote onward as an active delegator
        for this same scope - the "B->C already exists, now A->B is
        attempted" ordering of the depth-2 violation)."""
        ...

    def find_active_delegation_where_delegate(
        self, delegate_actor_id: UUID, scope_type: str, scope_id: UUID
    ) -> Delegation | None:
        """The current `active` delegation, if any, *to* this
        `(delegate_actor_id, scope_type, scope_id)` triple (i.e. a record
        whose own `delegate_actor_id` field matches - is this actor
        currently *holding* someone else's delegated authority for this
        scope?). Used by `application.create_delegation`'s ADR-009 item 9
        depth-1 guard (checking whether the *proposed new delegator*
        already holds delegated authority they would otherwise be
        re-delegating onward - the "A->B already exists, now B->C is
        attempted" ordering of the depth-2 violation - this is the
        ordering the task's own worked example uses)."""
        ...

    def find_blocking_delegation_for(
        self,
        delegator_actor_id: UUID,
        scope_type: str,
        scope_id: UUID,
        *,
        exclude_delegation_id: UUID | None = None,
    ) -> Delegation | None:
        """Any delegation with a status in `domain.BLOCKING_SCOPE_STATUSES`
        for this triple, other than `exclude_delegation_id` if given.
        Internal-use query backing `create`'s own prohibition #2 check -
        exposed on the protocol so tests can exercise it directly."""
        ...


class InMemoryDelegationStore:
    def __init__(self) -> None:
        self._records: dict[UUID, Delegation] = {}

    def create(self, delegation: Delegation) -> Delegation:
        existing = self._records.get(delegation.delegation_id)
        if existing is not None:
            if existing == delegation:
                return existing
            raise DelegationCreationConflictError(
                f"delegation_id {delegation.delegation_id} already created with different content"
            )

        conflict = self.find_blocking_delegation_for(
            delegation.delegator_actor_id,
            delegation.scope_type,
            delegation.scope_id,
            exclude_delegation_id=delegation.delegation_id,
        )
        if conflict is not None:
            raise DelegationScopeConflictError(
                f"delegator {delegation.delegator_actor_id} already has a "
                f"{conflict.status.value!r} delegation "
                f"({conflict.delegation_id}) for scope "
                f"{delegation.scope_type}:{delegation.scope_id}"
            )

        self._records[delegation.delegation_id] = delegation
        return delegation

    def save(self, delegation: Delegation) -> Delegation:
        if delegation.delegation_id not in self._records:
            raise UnknownDelegationError(f"unknown delegation_id: {delegation.delegation_id}")
        self._records[delegation.delegation_id] = delegation
        return delegation

    def get(self, delegation_id: UUID) -> Delegation | None:
        return self._records.get(delegation_id)

    def find_active_delegation_for(
        self, delegator_actor_id: UUID, scope_type: str, scope_id: UUID
    ) -> Delegation | None:
        for record in self._records.values():
            if (
                record.delegator_actor_id == delegator_actor_id
                and record.scope_type == scope_type
                and record.scope_id == scope_id
                and record.status == DelegationStatus.ACTIVE
            ):
                return record
        return None

    def find_active_delegation_where_delegate(
        self, delegate_actor_id: UUID, scope_type: str, scope_id: UUID
    ) -> Delegation | None:
        for record in self._records.values():
            if (
                record.delegate_actor_id == delegate_actor_id
                and record.scope_type == scope_type
                and record.scope_id == scope_id
                and record.status == DelegationStatus.ACTIVE
            ):
                return record
        return None

    def find_blocking_delegation_for(
        self,
        delegator_actor_id: UUID,
        scope_type: str,
        scope_id: UUID,
        *,
        exclude_delegation_id: UUID | None = None,
    ) -> Delegation | None:
        for record in self._records.values():
            if record.delegation_id == exclude_delegation_id:
                continue
            if (
                record.delegator_actor_id == delegator_actor_id
                and record.scope_type == scope_type
                and record.scope_id == scope_id
                and record.status in BLOCKING_SCOPE_STATUSES
            ):
                return record
        return None


class DelegationSnapshotStore(Protocol):
    def save(self, snapshot: DelegationSnapshot) -> DelegationSnapshot:
        """Idempotent-or-frozen by `(ballot_id, input_hash)` (canon
        prohibition #4 / CT-00-10 analogue):

        - No record yet exists for this key -> stores `snapshot` and
          returns it.
        - A record already exists for this key with the same
          `snapshot_hash` -> idempotent replay; returns the *existing*
          record unchanged (never the freshly-passed-in one - mirrors
          `epd2_eligibility_service.storage.InMemoryEligibilityRuleStore.save`).
        - A record already exists for this key with a *different*
          `snapshot_hash` -> raises `SnapshotFrozenError`.
        """
        ...

    def get(self, delegation_snapshot_id: UUID) -> DelegationSnapshot | None: ...

    def find_by_key(self, ballot_id: UUID, input_hash: str) -> DelegationSnapshot | None: ...


class InMemoryDelegationSnapshotStore:
    def __init__(self) -> None:
        self._by_key: dict[tuple[UUID, str], DelegationSnapshot] = {}
        self._by_id: dict[UUID, DelegationSnapshot] = {}

    def save(self, snapshot: DelegationSnapshot) -> DelegationSnapshot:
        key = (snapshot.ballot_id, snapshot.input_hash)
        existing = self._by_key.get(key)
        if existing is not None:
            if existing.snapshot_hash == snapshot.snapshot_hash:
                return existing
            raise SnapshotFrozenError(
                f"delegation snapshot for ballot_id {snapshot.ballot_id} "
                f"input_hash {snapshot.input_hash} is already frozen with "
                "different content"
            )
        self._by_key[key] = snapshot
        self._by_id[snapshot.delegation_snapshot_id] = snapshot
        return snapshot

    def get(self, delegation_snapshot_id: UUID) -> DelegationSnapshot | None:
        return self._by_id.get(delegation_snapshot_id)

    def find_by_key(self, ballot_id: UUID, input_hash: str) -> DelegationSnapshot | None:
        return self._by_key.get((ballot_id, input_hash))
