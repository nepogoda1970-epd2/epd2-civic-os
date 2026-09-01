"""Tests for epd2_delegation_service.storage: `InMemoryDelegationStore`'s
idempotent-create/conflict/scope-conflict behavior (canon prohibition #2)
and `InMemoryDelegationSnapshotStore`'s freeze-by-`(ballot_id, input_hash)`
behavior (canon prohibition #4).
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from epd2_delegation_service.domain import Delegation, DelegationSnapshot, DelegationStatus
from epd2_delegation_service.exceptions import (
    DelegationCreationConflictError,
    DelegationScopeConflictError,
    SnapshotFrozenError,
    UnknownDelegationError,
)
from epd2_delegation_service.storage import (
    InMemoryDelegationSnapshotStore,
    InMemoryDelegationStore,
)

_VALID_FROM = datetime(2026, 1, 1, tzinfo=UTC)


def _make_delegation(**overrides: object) -> Delegation:
    defaults: dict[str, object] = {
        "delegation_id": uuid4(),
        "delegator_actor_id": uuid4(),
        "delegate_actor_id": uuid4(),
        "scope_type": "ballot",
        "scope_id": uuid4(),
        "valid_from": _VALID_FROM,
        "valid_until": None,
        "revocation_status": "none",
        "status": DelegationStatus.DRAFT,
    }
    defaults.update(overrides)
    return Delegation(**defaults)  # type: ignore[arg-type]


def _make_snapshot(**overrides: object) -> DelegationSnapshot:
    defaults: dict[str, object] = {
        "delegation_snapshot_id": uuid4(),
        "ballot_id": uuid4(),
        "policy_version": 1,
        "created_at": datetime(2026, 1, 2, tzinfo=UTC),
        "input_hash": "a" * 64,
        "resolved_weights": {},
        "cycle_records": (),
        "snapshot_hash": "b" * 64,
    }
    defaults.update(overrides)
    return DelegationSnapshot(**defaults)  # type: ignore[arg-type]


# --- InMemoryDelegationStore --------------------------------------------------


def test_create_is_idempotent_for_identical_content() -> None:
    store = InMemoryDelegationStore()
    delegation = _make_delegation()
    first = store.create(delegation)
    second = store.create(delegation)
    assert first == second == delegation


def test_create_rejects_same_id_different_content() -> None:
    store = InMemoryDelegationStore()
    delegation_id = uuid4()
    store.create(_make_delegation(delegation_id=delegation_id, scope_type="ballot"))
    with pytest.raises(DelegationCreationConflictError):
        store.create(_make_delegation(delegation_id=delegation_id, scope_type="initiative"))


def test_create_rejects_scope_conflict_for_active_delegation() -> None:
    """Canon section 16.1 prohibition #2: two competing active
    delegations of the same scope."""
    store = InMemoryDelegationStore()
    delegator = uuid4()
    scope_type = "ballot"
    scope_id = uuid4()

    first = store.create(
        _make_delegation(delegator_actor_id=delegator, scope_type=scope_type, scope_id=scope_id)
    )
    activated = store.save(first.with_status(DelegationStatus.ACTIVE))
    assert activated.status == DelegationStatus.ACTIVE

    with pytest.raises(DelegationScopeConflictError):
        store.create(
            _make_delegation(delegator_actor_id=delegator, scope_type=scope_type, scope_id=scope_id)
        )


def test_create_rejects_scope_conflict_for_draft_delegation() -> None:
    """Documented choice: a `draft` also blocks a second create for the
    same scope, not just `active`."""
    store = InMemoryDelegationStore()
    delegator = uuid4()
    scope_type = "ballot"
    scope_id = uuid4()

    store.create(
        _make_delegation(delegator_actor_id=delegator, scope_type=scope_type, scope_id=scope_id)
    )
    with pytest.raises(DelegationScopeConflictError):
        store.create(
            _make_delegation(delegator_actor_id=delegator, scope_type=scope_type, scope_id=scope_id)
        )


def test_create_allows_different_scope_for_same_delegator() -> None:
    store = InMemoryDelegationStore()
    delegator = uuid4()
    store.create(_make_delegation(delegator_actor_id=delegator, scope_type="ballot"))
    # Different scope_id -> no conflict.
    second = store.create(_make_delegation(delegator_actor_id=delegator, scope_type="ballot"))
    assert second.delegator_actor_id == delegator


def test_save_raises_for_unknown_delegation() -> None:
    store = InMemoryDelegationStore()
    with pytest.raises(UnknownDelegationError):
        store.save(_make_delegation())


def test_find_active_delegation_for_only_returns_active_status() -> None:
    store = InMemoryDelegationStore()
    delegator = uuid4()
    scope_type = "ballot"
    scope_id = uuid4()
    draft = store.create(
        _make_delegation(delegator_actor_id=delegator, scope_type=scope_type, scope_id=scope_id)
    )
    assert store.find_active_delegation_for(delegator, scope_type, scope_id) is None

    store.save(draft.with_status(DelegationStatus.ACTIVE))
    found = store.find_active_delegation_for(delegator, scope_type, scope_id)
    assert found is not None
    assert found.delegator_actor_id == delegator


def test_find_blocking_delegation_for_excludes_given_id() -> None:
    store = InMemoryDelegationStore()
    delegator = uuid4()
    scope_type = "ballot"
    scope_id = uuid4()
    delegation = store.create(
        _make_delegation(delegator_actor_id=delegator, scope_type=scope_type, scope_id=scope_id)
    )
    result = store.find_blocking_delegation_for(
        delegator, scope_type, scope_id, exclude_delegation_id=delegation.delegation_id
    )
    assert result is None

    result_including = store.find_blocking_delegation_for(delegator, scope_type, scope_id)
    assert result_including is not None
    assert result_including.delegation_id == delegation.delegation_id


# --- InMemoryDelegationSnapshotStore ------------------------------------------


def test_snapshot_save_is_idempotent_for_identical_content() -> None:
    store = InMemoryDelegationSnapshotStore()
    ballot_id = uuid4()
    snapshot = _make_snapshot(ballot_id=ballot_id, input_hash="fixed-hash")
    first = store.save(snapshot)
    replay = _make_snapshot(
        delegation_snapshot_id=uuid4(),  # different id/created_at ...
        ballot_id=ballot_id,
        input_hash="fixed-hash",
        created_at=datetime(2026, 5, 5, tzinfo=UTC),
        snapshot_hash=snapshot.snapshot_hash,  # ... but identical content fingerprint
    )
    second = store.save(replay)
    assert second is first
    assert second.delegation_snapshot_id == snapshot.delegation_snapshot_id


def test_snapshot_save_raises_frozen_error_for_different_content_same_key() -> None:
    """Canon section 16.1 prohibition #4 / CT-00-10 analogue: a
    `DelegationSnapshot` may not change once frozen under the same
    `(ballot_id, input_hash)` key - mirroring `EligibilityRule`'s own rule
    freeze."""
    store = InMemoryDelegationSnapshotStore()
    ballot_id = uuid4()
    store.save(_make_snapshot(ballot_id=ballot_id, input_hash="fixed-hash", snapshot_hash="a" * 64))
    with pytest.raises(SnapshotFrozenError):
        store.save(
            _make_snapshot(ballot_id=ballot_id, input_hash="fixed-hash", snapshot_hash="c" * 64)
        )


def test_snapshot_find_by_key() -> None:
    store = InMemoryDelegationSnapshotStore()
    ballot_id = uuid4()
    snapshot = store.save(_make_snapshot(ballot_id=ballot_id, input_hash="fixed-hash"))
    found = store.find_by_key(ballot_id, "fixed-hash")
    assert found == snapshot
    assert store.find_by_key(ballot_id, "other-hash") is None


def test_snapshot_get_by_id() -> None:
    store = InMemoryDelegationSnapshotStore()
    snapshot = store.save(_make_snapshot())
    assert store.get(snapshot.delegation_snapshot_id) == snapshot
    assert store.get(uuid4()) is None
