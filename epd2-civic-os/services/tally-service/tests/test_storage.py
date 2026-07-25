"""Tests for epd2_tally_service.storage: create/get/save idempotency and
conflict behavior for both `InMemoryTallyStore` and
`InMemoryResultPublicationStore` (CT-00-04).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from epd2_tally_service.domain import (
    QuorumResult,
    ResultPublication,
    Tally,
    TallyVerificationStatus,
    ThresholdResult,
)
from epd2_tally_service.exceptions import (
    ResultPublicationConflictError,
    TallyRecordConflictError,
)
from epd2_tally_service.storage import (
    InMemoryResultPublicationStore,
    InMemoryTallyStore,
)

_STARTED_AT = datetime(2026, 1, 1, tzinfo=UTC)
_PUBLISHED_AT = datetime(2026, 1, 10, tzinfo=UTC)


def _make_tally(**overrides: object) -> Tally:
    defaults: dict[str, object] = {
        "tally_id": uuid4(),
        "ballot_id": uuid4(),
        "input_set_hash": "a" * 64,
        "algorithm_version": "1.0",
        "started_at": _STARTED_AT,
        "completed_at": None,
        "result_data": {},
        "invalid_vote_count": 0,
        "tally_signature": None,
        "verification_status": TallyVerificationStatus.PENDING,
    }
    defaults.update(overrides)
    return Tally(**defaults)  # type: ignore[arg-type]


def _make_result(**overrides: object) -> ResultPublication:
    defaults: dict[str, object] = {
        "result_publication_id": uuid4(),
        "ballot_id": uuid4(),
        "tally_id": uuid4(),
        "eligible_count": 100,
        "credential_count": 90,
        "accepted_vote_count": 80,
        "rejected_vote_count": 5,
        "quorum_result": QuorumResult.NOT_REQUIRED,
        "threshold_result": ThresholdResult.THRESHOLD_MET,
        "published_at": _PUBLISHED_AT,
        "audit_package_reference": "audit-package-1",
        "challenge_deadline_at": _PUBLISHED_AT + timedelta(hours=72),
    }
    defaults.update(overrides)
    return ResultPublication(**defaults)  # type: ignore[arg-type]


# --- InMemoryTallyStore -------------------------------------------------------


def test_create_then_get_tally() -> None:
    store = InMemoryTallyStore()
    tally = _make_tally()
    stored = store.create(tally)
    assert store.get(tally.tally_id) == stored


def test_get_unknown_tally_returns_none() -> None:
    store = InMemoryTallyStore()
    assert store.get(uuid4()) is None


def test_idempotent_recreate_of_identical_tally_succeeds() -> None:
    store = InMemoryTallyStore()
    tally = _make_tally()
    first = store.create(tally)
    second = store.create(tally)
    assert first == second


def test_conflicting_recreate_of_tally_is_rejected() -> None:
    store = InMemoryTallyStore()
    tally = _make_tally()
    store.create(tally)
    conflicting = _make_tally(tally_id=tally.tally_id, algorithm_version="2.0")
    with pytest.raises(TallyRecordConflictError):
        store.create(conflicting)


def test_save_updates_an_already_created_tally() -> None:
    store = InMemoryTallyStore()
    tally = _make_tally()
    store.create(tally)
    running = tally.with_status(TallyVerificationStatus.RUNNING)
    store.save(running)
    fetched = store.get(tally.tally_id)
    assert fetched is not None
    assert fetched.verification_status == TallyVerificationStatus.RUNNING


def test_save_of_never_created_tally_still_stores_it() -> None:
    """Unlike `InMemoryBallotStore.save` (which enforces a freeze and
    therefore must reject an unknown id), `TallyStore.save` has no such
    invariant to protect - it is a plain upsert used only after `create`
    in `application.py`, but the reference adapter itself does not need to
    reject a bare `save` call to satisfy this service's own contract."""
    store = InMemoryTallyStore()
    tally = _make_tally()
    store.save(tally)
    assert store.get(tally.tally_id) == tally


# --- InMemoryResultPublicationStore -------------------------------------------


def test_create_then_get_result_publication() -> None:
    store = InMemoryResultPublicationStore()
    result = _make_result()
    stored = store.create(result)
    assert store.get(result.result_publication_id) == stored


def test_get_unknown_result_publication_returns_none() -> None:
    store = InMemoryResultPublicationStore()
    assert store.get(uuid4()) is None


def test_idempotent_recreate_of_identical_result_publication_succeeds() -> None:
    store = InMemoryResultPublicationStore()
    result = _make_result()
    first = store.create(result)
    second = store.create(result)
    assert first == second


def test_conflicting_recreate_of_result_publication_is_rejected() -> None:
    store = InMemoryResultPublicationStore()
    result = _make_result()
    store.create(result)
    conflicting = _make_result(
        result_publication_id=result.result_publication_id, audit_package_reference="other"
    )
    with pytest.raises(ResultPublicationConflictError):
        store.create(conflicting)
