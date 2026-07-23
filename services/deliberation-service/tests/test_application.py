"""Tests for epd2_deliberation_service.application."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from epd2_audit_core.storage import InMemoryAuditEventStore
from epd2_core.clock import FixedClock
from epd2_core.event_envelope import ActorRef
from epd2_deliberation_service.application import (
    PermissionDeniedError,
    archive_discussion,
    close_discussion,
    create_contribution,
    edit_contribution,
    flag_contribution,
    hide_contribution,
    limit_discussion,
    open_discussion,
    reopen_discussion,
    restore_contribution,
    set_discussion_read_only,
)
from epd2_deliberation_service.domain import (
    Contribution,
    ContributionType,
    ContributionVisibilityStatus,
    DiscussionStatus,
)
from epd2_deliberation_service.exceptions import (
    ForbiddenContributionVisibilityTransitionError,
    ForbiddenDiscussionTransitionError,
    UnknownContributionError,
    UnknownDiscussionError,
)
from epd2_deliberation_service.storage import InMemoryContributionStore, InMemoryDiscussionStore

_CLOCK = FixedClock(datetime(2026, 1, 1, tzinfo=UTC))
_ACTOR = ActorRef(actor_id=uuid4(), actor_type="service")


def _open(
    store: InMemoryDiscussionStore, audit_store: InMemoryAuditEventStore, **overrides: object
) -> object:
    defaults: dict[str, object] = {
        "discussion_id": uuid4(),
        "subject_type": "initiative",
        "subject_id": uuid4(),
        "space_id": uuid4(),
        "moderation_policy_id": None,
        "actor": _ACTOR,
        "actor_is_authorized": True,
        "correlation_id": uuid4(),
        "clock": _CLOCK,
    }
    defaults.update(overrides)
    return open_discussion(store, audit_store, **defaults)  # type: ignore[arg-type]


def _create_contribution(
    contribution_store: InMemoryContributionStore,
    discussion_store: InMemoryDiscussionStore,
    audit_store: InMemoryAuditEventStore,
    **overrides: object,
) -> object:
    defaults: dict[str, object] = {
        "contribution_id": uuid4(),
        "author_actor_id": uuid4(),
        "parent_contribution_id": None,
        "contribution_type": ContributionType.COMMENT,
        "content": "hello world",
        "actor": _ACTOR,
        "actor_is_authorized": True,
        "correlation_id": uuid4(),
        "causation_id": None,
        "clock": _CLOCK,
    }
    defaults.update(overrides)
    return create_contribution(
        contribution_store,
        discussion_store,
        audit_store,
        **defaults,  # type: ignore[arg-type]
    )


# --- open_discussion ---------------------------------------------------------


def test_open_discussion_emits_discussion_opened_event() -> None:
    store = InMemoryDiscussionStore()
    result = _open(store, InMemoryAuditEventStore())
    assert result.event.event_type == "discussion.opened"  # type: ignore[attr-defined]
    assert result.discussion.status.value == "open"  # type: ignore[attr-defined]


def test_open_discussion_creates_audit_event() -> None:
    store = InMemoryDiscussionStore()
    audit_store = InMemoryAuditEventStore()
    result = _open(store, audit_store)
    audit_event = result.audit_event  # type: ignore[attr-defined]
    assert audit_event.action == "open"
    assert audit_event.reason_code == "DISCUSSION_STATUS_CHANGED"
    assert audit_event.target_type == "discussion"
    assert audit_store.get_by_event_id(audit_event.audit_event_id) is not None


def test_open_discussion_without_permission_is_denied() -> None:
    store = InMemoryDiscussionStore()
    with pytest.raises(PermissionDeniedError):
        _open(store, InMemoryAuditEventStore(), actor_is_authorized=False)


def test_open_discussion_is_idempotent_for_repeated_event_id() -> None:
    """CT-00-04: calling the same command twice with the same event_id
    and identical inputs must not create a duplicate audit entry."""
    store = InMemoryDiscussionStore()
    audit_store = InMemoryAuditEventStore()
    discussion_id = uuid4()
    event_id = uuid4()
    # subject_id/space_id/correlation_id must be pinned across both calls:
    # `_open`'s defaults otherwise generate a *fresh* uuid4() each
    # invocation, which would make the "replay" carry different content
    # than the original call and spuriously trip
    # DiscussionCreationConflictError / AuditEventConflictError - a bug in
    # the test, not in `open_discussion` itself (content-based dedup is
    # working correctly; the test just wasn't holding content fixed).
    subject_id = uuid4()
    space_id = uuid4()
    correlation_id = uuid4()
    first = _open(
        store,
        audit_store,
        discussion_id=discussion_id,
        event_id=event_id,
        subject_id=subject_id,
        space_id=space_id,
        correlation_id=correlation_id,
    )
    second = _open(
        store,
        audit_store,
        discussion_id=discussion_id,
        event_id=event_id,
        subject_id=subject_id,
        space_id=space_id,
        correlation_id=correlation_id,
    )
    assert first.discussion == second.discussion  # type: ignore[attr-defined]
    assert first.audit_event == second.audit_event  # type: ignore[attr-defined]
    assert len(audit_store.list_by_aggregate("discussion", discussion_id)) == 1


# --- close_discussion ---------------------------------------------------------


def test_close_discussion_transitions_and_emits_event() -> None:
    store = InMemoryDiscussionStore()
    audit_store = InMemoryAuditEventStore()
    discussion = _open(store, audit_store).discussion  # type: ignore[attr-defined]
    result = close_discussion(
        store,
        audit_store,
        discussion_id=discussion.discussion_id,
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        causation_id=None,
        clock=_CLOCK,
    )
    assert result.discussion.status.value == "closed"
    assert result.event.event_type == "discussion.closed"
    assert result.audit_event.action == "close"
    assert result.audit_event.reason_code == "DISCUSSION_STATUS_CHANGED"


def test_close_discussion_without_permission_is_denied() -> None:
    store = InMemoryDiscussionStore()
    audit_store = InMemoryAuditEventStore()
    discussion = _open(store, audit_store).discussion  # type: ignore[attr-defined]
    with pytest.raises(PermissionDeniedError):
        close_discussion(
            store,
            audit_store,
            discussion_id=discussion.discussion_id,
            actor=_ACTOR,
            actor_is_authorized=False,
            correlation_id=uuid4(),
            causation_id=None,
            clock=_CLOCK,
        )


def test_close_discussion_unknown_discussion_raises() -> None:
    store = InMemoryDiscussionStore()
    audit_store = InMemoryAuditEventStore()
    with pytest.raises(UnknownDiscussionError):
        close_discussion(
            store,
            audit_store,
            discussion_id=uuid4(),
            actor=_ACTOR,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            causation_id=None,
            clock=_CLOCK,
        )


def test_close_already_archived_discussion_is_forbidden() -> None:
    store = InMemoryDiscussionStore()
    audit_store = InMemoryAuditEventStore()
    discussion = _open(store, audit_store).discussion  # type: ignore[attr-defined]
    closed = close_discussion(
        store,
        audit_store,
        discussion_id=discussion.discussion_id,
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        causation_id=None,
        clock=_CLOCK,
    ).discussion
    store.save(closed.with_status(DiscussionStatus.ARCHIVED))
    with pytest.raises(ForbiddenDiscussionTransitionError):
        close_discussion(
            store,
            audit_store,
            discussion_id=discussion.discussion_id,
            actor=_ACTOR,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            causation_id=None,
            clock=_CLOCK,
            event_id=uuid4(),
        )


def test_close_discussion_is_idempotent_for_repeated_event_id() -> None:
    """CT-00-04: a naive replay would hit closed->closed (forbidden) on
    the store's already-mutated state; the command must instead detect
    the replay via the existing audit record and short-circuit."""
    store = InMemoryDiscussionStore()
    audit_store = InMemoryAuditEventStore()
    discussion = _open(store, audit_store).discussion  # type: ignore[attr-defined]
    event_id = uuid4()
    correlation_id = uuid4()

    first = close_discussion(
        store,
        audit_store,
        discussion_id=discussion.discussion_id,
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=correlation_id,
        causation_id=None,
        clock=_CLOCK,
        event_id=event_id,
    )
    second = close_discussion(
        store,
        audit_store,
        discussion_id=discussion.discussion_id,
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=correlation_id,
        causation_id=None,
        clock=_CLOCK,
        event_id=event_id,
    )
    assert first.discussion == second.discussion
    assert first.audit_event == second.audit_event
    assert (
        len(audit_store.list_by_aggregate("discussion", discussion.discussion_id)) == 2
    )  # one from open, one from close


# --- no-domain-event Discussion transitions ------------------------------------


def test_limit_discussion_transitions_and_audits_without_event() -> None:
    store = InMemoryDiscussionStore()
    audit_store = InMemoryAuditEventStore()
    discussion = _open(store, audit_store).discussion  # type: ignore[attr-defined]
    result = limit_discussion(
        store,
        audit_store,
        discussion_id=discussion.discussion_id,
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.discussion.status.value == "limited"
    assert result.audit_event.action == "limit"
    assert result.audit_event.reason_code == "DISCUSSION_STATUS_CHANGED"
    assert not hasattr(result, "event")


def test_limit_discussion_without_permission_is_denied() -> None:
    store = InMemoryDiscussionStore()
    audit_store = InMemoryAuditEventStore()
    discussion = _open(store, audit_store).discussion  # type: ignore[attr-defined]
    with pytest.raises(PermissionDeniedError):
        limit_discussion(
            store,
            audit_store,
            discussion_id=discussion.discussion_id,
            actor=_ACTOR,
            actor_is_authorized=False,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


def test_limit_discussion_unknown_discussion_raises() -> None:
    store = InMemoryDiscussionStore()
    audit_store = InMemoryAuditEventStore()
    with pytest.raises(UnknownDiscussionError):
        limit_discussion(
            store,
            audit_store,
            discussion_id=uuid4(),
            actor=_ACTOR,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


def test_limit_discussion_from_read_only_is_forbidden() -> None:
    store = InMemoryDiscussionStore()
    audit_store = InMemoryAuditEventStore()
    discussion = _open(store, audit_store).discussion  # type: ignore[attr-defined]
    set_discussion_read_only(
        store,
        audit_store,
        discussion_id=discussion.discussion_id,
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    with pytest.raises(ForbiddenDiscussionTransitionError):
        limit_discussion(
            store,
            audit_store,
            discussion_id=discussion.discussion_id,
            actor=_ACTOR,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=_CLOCK,
            event_id=uuid4(),
        )


def test_limit_discussion_is_idempotent_for_repeated_event_id() -> None:
    store = InMemoryDiscussionStore()
    audit_store = InMemoryAuditEventStore()
    discussion = _open(store, audit_store).discussion  # type: ignore[attr-defined]
    event_id = uuid4()
    correlation_id = uuid4()
    first = limit_discussion(
        store,
        audit_store,
        discussion_id=discussion.discussion_id,
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=correlation_id,
        clock=_CLOCK,
        event_id=event_id,
    )
    second = limit_discussion(
        store,
        audit_store,
        discussion_id=discussion.discussion_id,
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=correlation_id,
        clock=_CLOCK,
        event_id=event_id,
    )
    assert first.discussion == second.discussion
    assert first.audit_event == second.audit_event
    assert (
        len(audit_store.list_by_aggregate("discussion", discussion.discussion_id)) == 2
    )  # one from open, one from limit


def test_set_discussion_read_only_from_open_and_from_limited() -> None:
    store = InMemoryDiscussionStore()
    audit_store = InMemoryAuditEventStore()
    discussion_open = _open(store, audit_store).discussion  # type: ignore[attr-defined]
    result = set_discussion_read_only(
        store,
        audit_store,
        discussion_id=discussion_open.discussion_id,
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.discussion.status.value == "read_only"
    assert result.audit_event.action == "set_read_only"

    discussion_limited = _open(store, audit_store).discussion  # type: ignore[attr-defined]
    limit_discussion(
        store,
        audit_store,
        discussion_id=discussion_limited.discussion_id,
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    result2 = set_discussion_read_only(
        store,
        audit_store,
        discussion_id=discussion_limited.discussion_id,
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result2.discussion.status.value == "read_only"


def test_reopen_discussion_from_limited_and_read_only() -> None:
    store = InMemoryDiscussionStore()
    audit_store = InMemoryAuditEventStore()
    discussion_a = _open(store, audit_store).discussion  # type: ignore[attr-defined]
    limit_discussion(
        store,
        audit_store,
        discussion_id=discussion_a.discussion_id,
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    reopened_a = reopen_discussion(
        store,
        audit_store,
        discussion_id=discussion_a.discussion_id,
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert reopened_a.discussion.status.value == "open"
    assert reopened_a.audit_event.action == "reopen"

    discussion_b = _open(store, audit_store).discussion  # type: ignore[attr-defined]
    set_discussion_read_only(
        store,
        audit_store,
        discussion_id=discussion_b.discussion_id,
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    reopened_b = reopen_discussion(
        store,
        audit_store,
        discussion_id=discussion_b.discussion_id,
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert reopened_b.discussion.status.value == "open"


def test_reopen_discussion_without_permission_is_denied() -> None:
    store = InMemoryDiscussionStore()
    audit_store = InMemoryAuditEventStore()
    discussion = _open(store, audit_store).discussion  # type: ignore[attr-defined]
    limit_discussion(
        store,
        audit_store,
        discussion_id=discussion.discussion_id,
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    with pytest.raises(PermissionDeniedError):
        reopen_discussion(
            store,
            audit_store,
            discussion_id=discussion.discussion_id,
            actor=_ACTOR,
            actor_is_authorized=False,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


def test_reopen_discussion_unknown_discussion_raises() -> None:
    store = InMemoryDiscussionStore()
    audit_store = InMemoryAuditEventStore()
    with pytest.raises(UnknownDiscussionError):
        reopen_discussion(
            store,
            audit_store,
            discussion_id=uuid4(),
            actor=_ACTOR,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


def test_archive_discussion_from_closed() -> None:
    store = InMemoryDiscussionStore()
    audit_store = InMemoryAuditEventStore()
    discussion = _open(store, audit_store).discussion  # type: ignore[attr-defined]
    close_discussion(
        store,
        audit_store,
        discussion_id=discussion.discussion_id,
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        causation_id=None,
        clock=_CLOCK,
    )
    result = archive_discussion(
        store,
        audit_store,
        discussion_id=discussion.discussion_id,
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.discussion.status.value == "archived"
    assert result.audit_event.action == "archive"


def test_archive_discussion_from_open_is_forbidden() -> None:
    store = InMemoryDiscussionStore()
    audit_store = InMemoryAuditEventStore()
    discussion = _open(store, audit_store).discussion  # type: ignore[attr-defined]
    with pytest.raises(ForbiddenDiscussionTransitionError):
        archive_discussion(
            store,
            audit_store,
            discussion_id=discussion.discussion_id,
            actor=_ACTOR,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


def test_archive_discussion_without_permission_is_denied() -> None:
    store = InMemoryDiscussionStore()
    audit_store = InMemoryAuditEventStore()
    discussion = _open(store, audit_store).discussion  # type: ignore[attr-defined]
    close_discussion(
        store,
        audit_store,
        discussion_id=discussion.discussion_id,
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        causation_id=None,
        clock=_CLOCK,
    )
    with pytest.raises(PermissionDeniedError):
        archive_discussion(
            store,
            audit_store,
            discussion_id=discussion.discussion_id,
            actor=_ACTOR,
            actor_is_authorized=False,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


def test_archive_discussion_unknown_discussion_raises() -> None:
    store = InMemoryDiscussionStore()
    audit_store = InMemoryAuditEventStore()
    with pytest.raises(UnknownDiscussionError):
        archive_discussion(
            store,
            audit_store,
            discussion_id=uuid4(),
            actor=_ACTOR,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


def test_archive_discussion_is_idempotent_for_repeated_event_id() -> None:
    store = InMemoryDiscussionStore()
    audit_store = InMemoryAuditEventStore()
    discussion = _open(store, audit_store).discussion  # type: ignore[attr-defined]
    close_discussion(
        store,
        audit_store,
        discussion_id=discussion.discussion_id,
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        causation_id=None,
        clock=_CLOCK,
    )
    event_id = uuid4()
    correlation_id = uuid4()
    first = archive_discussion(
        store,
        audit_store,
        discussion_id=discussion.discussion_id,
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=correlation_id,
        clock=_CLOCK,
        event_id=event_id,
    )
    second = archive_discussion(
        store,
        audit_store,
        discussion_id=discussion.discussion_id,
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=correlation_id,
        clock=_CLOCK,
        event_id=event_id,
    )
    assert first.discussion == second.discussion
    assert first.audit_event == second.audit_event
    assert (
        len(audit_store.list_by_aggregate("discussion", discussion.discussion_id)) == 3
    )  # open, close, archive


# --- create_contribution -----------------------------------------------------


def test_create_contribution_emits_contribution_created_event() -> None:
    discussion_store = InMemoryDiscussionStore()
    contribution_store = InMemoryContributionStore()
    audit_store = InMemoryAuditEventStore()
    discussion = _open(discussion_store, audit_store).discussion  # type: ignore[attr-defined]
    result = _create_contribution(
        contribution_store, discussion_store, audit_store, discussion_id=discussion.discussion_id
    )
    assert result.event.event_type == "contribution.created"  # type: ignore[attr-defined]
    assert result.contribution.visibility_status.value == "visible"  # type: ignore[attr-defined]
    assert result.audit_event.reason_code == "CONTRIBUTION_CREATED"  # type: ignore[attr-defined]


def test_create_contribution_without_permission_is_denied() -> None:
    discussion_store = InMemoryDiscussionStore()
    contribution_store = InMemoryContributionStore()
    audit_store = InMemoryAuditEventStore()
    discussion = _open(discussion_store, audit_store).discussion  # type: ignore[attr-defined]
    with pytest.raises(PermissionDeniedError):
        _create_contribution(
            contribution_store,
            discussion_store,
            audit_store,
            discussion_id=discussion.discussion_id,
            actor_is_authorized=False,
        )


def test_create_contribution_unknown_discussion_raises() -> None:
    discussion_store = InMemoryDiscussionStore()
    contribution_store = InMemoryContributionStore()
    audit_store = InMemoryAuditEventStore()
    with pytest.raises(UnknownDiscussionError):
        _create_contribution(
            contribution_store, discussion_store, audit_store, discussion_id=uuid4()
        )


def test_create_contribution_with_unresolvable_parent_raises() -> None:
    discussion_store = InMemoryDiscussionStore()
    contribution_store = InMemoryContributionStore()
    audit_store = InMemoryAuditEventStore()
    discussion = _open(discussion_store, audit_store).discussion  # type: ignore[attr-defined]
    with pytest.raises(UnknownContributionError):
        _create_contribution(
            contribution_store,
            discussion_store,
            audit_store,
            discussion_id=discussion.discussion_id,
            parent_contribution_id=uuid4(),
        )


def test_create_contribution_with_parent_from_different_discussion_raises() -> None:
    discussion_store = InMemoryDiscussionStore()
    contribution_store = InMemoryContributionStore()
    audit_store = InMemoryAuditEventStore()
    discussion_a = _open(discussion_store, audit_store).discussion  # type: ignore[attr-defined]
    discussion_b = _open(discussion_store, audit_store).discussion  # type: ignore[attr-defined]
    parent = _create_contribution(
        contribution_store, discussion_store, audit_store, discussion_id=discussion_a.discussion_id
    ).contribution  # type: ignore[attr-defined]
    with pytest.raises(UnknownContributionError):
        _create_contribution(
            contribution_store,
            discussion_store,
            audit_store,
            discussion_id=discussion_b.discussion_id,
            parent_contribution_id=parent.contribution_id,
        )


def test_create_contribution_with_valid_parent_in_same_discussion_succeeds() -> None:
    discussion_store = InMemoryDiscussionStore()
    contribution_store = InMemoryContributionStore()
    audit_store = InMemoryAuditEventStore()
    discussion = _open(discussion_store, audit_store).discussion  # type: ignore[attr-defined]
    parent = _create_contribution(
        contribution_store, discussion_store, audit_store, discussion_id=discussion.discussion_id
    ).contribution  # type: ignore[attr-defined]
    child = _create_contribution(
        contribution_store,
        discussion_store,
        audit_store,
        discussion_id=discussion.discussion_id,
        parent_contribution_id=parent.contribution_id,
        content="a reply",
    ).contribution  # type: ignore[attr-defined]
    assert child.parent_contribution_id == parent.contribution_id


def test_create_contribution_is_idempotent_for_repeated_event_id() -> None:
    discussion_store = InMemoryDiscussionStore()
    contribution_store = InMemoryContributionStore()
    audit_store = InMemoryAuditEventStore()
    discussion = _open(discussion_store, audit_store).discussion  # type: ignore[attr-defined]
    contribution_id = uuid4()
    event_id = uuid4()
    # author_actor_id/correlation_id must be pinned across both calls for
    # the same reason subject_id/space_id/correlation_id must be pinned
    # in test_open_discussion_is_idempotent_for_repeated_event_id above:
    # `_create_contribution`'s defaults otherwise generate a fresh
    # uuid4() each invocation, making the "replay" carry different
    # content than the original call.
    author_actor_id = uuid4()
    correlation_id = uuid4()
    first = _create_contribution(
        contribution_store,
        discussion_store,
        audit_store,
        discussion_id=discussion.discussion_id,
        contribution_id=contribution_id,
        event_id=event_id,
        author_actor_id=author_actor_id,
        correlation_id=correlation_id,
    )
    second = _create_contribution(
        contribution_store,
        discussion_store,
        audit_store,
        discussion_id=discussion.discussion_id,
        contribution_id=contribution_id,
        event_id=event_id,
        author_actor_id=author_actor_id,
        correlation_id=correlation_id,
    )
    assert first.contribution == second.contribution  # type: ignore[attr-defined]
    assert first.audit_event == second.audit_event  # type: ignore[attr-defined]
    assert len(audit_store.list_by_aggregate("contribution", contribution_id)) == 1


# --- edit_contribution --------------------------------------------------------


def _setup_contribution(
    discussion_store: InMemoryDiscussionStore,
    contribution_store: InMemoryContributionStore,
    audit_store: InMemoryAuditEventStore,
) -> Contribution:
    discussion = _open(discussion_store, audit_store).discussion  # type: ignore[attr-defined]
    result: Contribution = _create_contribution(
        contribution_store, discussion_store, audit_store, discussion_id=discussion.discussion_id
    ).contribution  # type: ignore[attr-defined]
    return result


def test_edit_contribution_increments_version_and_emits_event() -> None:
    discussion_store = InMemoryDiscussionStore()
    contribution_store = InMemoryContributionStore()
    audit_store = InMemoryAuditEventStore()
    contribution = _setup_contribution(discussion_store, contribution_store, audit_store)
    result = edit_contribution(
        contribution_store,
        audit_store,
        contribution_id=contribution.contribution_id,
        new_content="updated content",
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        causation_id=None,
        clock=_CLOCK,
    )
    assert result.contribution.content == "updated content"
    assert result.contribution.edited_version == 2
    assert result.contribution.visibility_status == contribution.visibility_status
    assert result.event.event_type == "contribution.edited"
    assert result.audit_event.reason_code == "CONTRIBUTION_EDITED"


def test_edit_contribution_without_permission_is_denied() -> None:
    discussion_store = InMemoryDiscussionStore()
    contribution_store = InMemoryContributionStore()
    audit_store = InMemoryAuditEventStore()
    contribution = _setup_contribution(discussion_store, contribution_store, audit_store)
    with pytest.raises(PermissionDeniedError):
        edit_contribution(
            contribution_store,
            audit_store,
            contribution_id=contribution.contribution_id,
            new_content="updated content",
            actor=_ACTOR,
            actor_is_authorized=False,
            correlation_id=uuid4(),
            causation_id=None,
            clock=_CLOCK,
        )


def test_edit_unknown_contribution_raises() -> None:
    contribution_store = InMemoryContributionStore()
    audit_store = InMemoryAuditEventStore()
    with pytest.raises(UnknownContributionError):
        edit_contribution(
            contribution_store,
            audit_store,
            contribution_id=uuid4(),
            new_content="x",
            actor=_ACTOR,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            causation_id=None,
            clock=_CLOCK,
        )


def test_edit_contribution_is_idempotent_for_repeated_event_id() -> None:
    """A naive replay would increment edited_version twice; the command
    must detect the replay via the existing audit record instead."""
    discussion_store = InMemoryDiscussionStore()
    contribution_store = InMemoryContributionStore()
    audit_store = InMemoryAuditEventStore()
    contribution = _setup_contribution(discussion_store, contribution_store, audit_store)
    event_id = uuid4()
    correlation_id = uuid4()

    first = edit_contribution(
        contribution_store,
        audit_store,
        contribution_id=contribution.contribution_id,
        new_content="updated content",
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=correlation_id,
        causation_id=None,
        clock=_CLOCK,
        event_id=event_id,
    )
    second = edit_contribution(
        contribution_store,
        audit_store,
        contribution_id=contribution.contribution_id,
        new_content="updated content",
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=correlation_id,
        causation_id=None,
        clock=_CLOCK,
        event_id=event_id,
    )
    assert first.contribution == second.contribution
    assert first.contribution.edited_version == 2  # not 3
    assert first.audit_event == second.audit_event
    assert (
        len(audit_store.list_by_aggregate("contribution", contribution.contribution_id)) == 2
    )  # one from create, one from edit


# --- flag_contribution --------------------------------------------------------


def test_flag_contribution_emits_event_without_visibility_change() -> None:
    discussion_store = InMemoryDiscussionStore()
    contribution_store = InMemoryContributionStore()
    audit_store = InMemoryAuditEventStore()
    contribution = _setup_contribution(discussion_store, contribution_store, audit_store)
    result = flag_contribution(
        contribution_store,
        audit_store,
        contribution_id=contribution.contribution_id,
        flag_reason_code="MODERATION_POLICY_VIOLATION",
        note="looks off-topic",
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        causation_id=None,
        clock=_CLOCK,
    )
    assert result.event.event_type == "contribution.flagged"
    assert result.event.payload["flag_reason_code"] == "MODERATION_POLICY_VIOLATION"
    assert result.contribution.visibility_status == contribution.visibility_status
    assert result.audit_event.reason_code == "CONTRIBUTION_FLAGGED"
    assert result.audit_event.before_hash == result.audit_event.after_hash


def test_flag_contribution_without_permission_is_denied() -> None:
    discussion_store = InMemoryDiscussionStore()
    contribution_store = InMemoryContributionStore()
    audit_store = InMemoryAuditEventStore()
    contribution = _setup_contribution(discussion_store, contribution_store, audit_store)
    with pytest.raises(PermissionDeniedError):
        flag_contribution(
            contribution_store,
            audit_store,
            contribution_id=contribution.contribution_id,
            flag_reason_code="MODERATION_POLICY_VIOLATION",
            note=None,
            actor=_ACTOR,
            actor_is_authorized=False,
            correlation_id=uuid4(),
            causation_id=None,
            clock=_CLOCK,
        )


def test_flag_contribution_rejects_empty_reason_code() -> None:
    discussion_store = InMemoryDiscussionStore()
    contribution_store = InMemoryContributionStore()
    audit_store = InMemoryAuditEventStore()
    contribution = _setup_contribution(discussion_store, contribution_store, audit_store)
    with pytest.raises(ValueError, match="flag_reason_code"):
        flag_contribution(
            contribution_store,
            audit_store,
            contribution_id=contribution.contribution_id,
            flag_reason_code="",
            note=None,
            actor=_ACTOR,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            causation_id=None,
            clock=_CLOCK,
        )


def test_flag_unknown_contribution_raises() -> None:
    contribution_store = InMemoryContributionStore()
    audit_store = InMemoryAuditEventStore()
    with pytest.raises(UnknownContributionError):
        flag_contribution(
            contribution_store,
            audit_store,
            contribution_id=uuid4(),
            flag_reason_code="MODERATION_POLICY_VIOLATION",
            note=None,
            actor=_ACTOR,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            causation_id=None,
            clock=_CLOCK,
        )


def test_flag_contribution_is_idempotent_for_repeated_event_id() -> None:
    discussion_store = InMemoryDiscussionStore()
    contribution_store = InMemoryContributionStore()
    audit_store = InMemoryAuditEventStore()
    contribution = _setup_contribution(discussion_store, contribution_store, audit_store)
    event_id = uuid4()
    correlation_id = uuid4()
    first = flag_contribution(
        contribution_store,
        audit_store,
        contribution_id=contribution.contribution_id,
        flag_reason_code="MODERATION_POLICY_VIOLATION",
        note=None,
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=correlation_id,
        causation_id=None,
        clock=_CLOCK,
        event_id=event_id,
    )
    second = flag_contribution(
        contribution_store,
        audit_store,
        contribution_id=contribution.contribution_id,
        flag_reason_code="MODERATION_POLICY_VIOLATION",
        note=None,
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=correlation_id,
        causation_id=None,
        clock=_CLOCK,
        event_id=event_id,
    )
    assert first.audit_event == second.audit_event
    assert (
        len(audit_store.list_by_aggregate("contribution", contribution.contribution_id)) == 2
    )  # one from create, one from flag


# --- hide_contribution --------------------------------------------------------


def test_hide_contribution_transitions_and_emits_event() -> None:
    discussion_store = InMemoryDiscussionStore()
    contribution_store = InMemoryContributionStore()
    audit_store = InMemoryAuditEventStore()
    contribution = _setup_contribution(discussion_store, contribution_store, audit_store)
    result = hide_contribution(
        contribution_store,
        audit_store,
        contribution_id=contribution.contribution_id,
        target_status=ContributionVisibilityStatus.TEMPORARILY_HIDDEN,
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        causation_id=None,
        clock=_CLOCK,
    )
    assert result.contribution.visibility_status.value == "temporarily_hidden"
    assert result.event.event_type == "contribution.hidden"
    assert result.audit_event.reason_code == "CONTRIBUTION_STATUS_CHANGED"


def test_hide_contribution_rejects_invalid_target_status() -> None:
    discussion_store = InMemoryDiscussionStore()
    contribution_store = InMemoryContributionStore()
    audit_store = InMemoryAuditEventStore()
    contribution = _setup_contribution(discussion_store, contribution_store, audit_store)
    with pytest.raises(ForbiddenContributionVisibilityTransitionError):
        hide_contribution(
            contribution_store,
            audit_store,
            contribution_id=contribution.contribution_id,
            target_status=ContributionVisibilityStatus.RESTORED,
            actor=_ACTOR,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            causation_id=None,
            clock=_CLOCK,
        )


def test_hide_contribution_without_permission_is_denied() -> None:
    discussion_store = InMemoryDiscussionStore()
    contribution_store = InMemoryContributionStore()
    audit_store = InMemoryAuditEventStore()
    contribution = _setup_contribution(discussion_store, contribution_store, audit_store)
    with pytest.raises(PermissionDeniedError):
        hide_contribution(
            contribution_store,
            audit_store,
            contribution_id=contribution.contribution_id,
            target_status=ContributionVisibilityStatus.RESTRICTED,
            actor=_ACTOR,
            actor_is_authorized=False,
            correlation_id=uuid4(),
            causation_id=None,
            clock=_CLOCK,
        )


def test_hide_unknown_contribution_raises() -> None:
    contribution_store = InMemoryContributionStore()
    audit_store = InMemoryAuditEventStore()
    with pytest.raises(UnknownContributionError):
        hide_contribution(
            contribution_store,
            audit_store,
            contribution_id=uuid4(),
            target_status=ContributionVisibilityStatus.RESTRICTED,
            actor=_ACTOR,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            causation_id=None,
            clock=_CLOCK,
        )


def test_hide_contribution_is_idempotent_for_repeated_event_id() -> None:
    discussion_store = InMemoryDiscussionStore()
    contribution_store = InMemoryContributionStore()
    audit_store = InMemoryAuditEventStore()
    contribution = _setup_contribution(discussion_store, contribution_store, audit_store)
    event_id = uuid4()
    correlation_id = uuid4()
    first = hide_contribution(
        contribution_store,
        audit_store,
        contribution_id=contribution.contribution_id,
        target_status=ContributionVisibilityStatus.RESTRICTED,
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=correlation_id,
        causation_id=None,
        clock=_CLOCK,
        event_id=event_id,
    )
    second = hide_contribution(
        contribution_store,
        audit_store,
        contribution_id=contribution.contribution_id,
        target_status=ContributionVisibilityStatus.RESTRICTED,
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=correlation_id,
        causation_id=None,
        clock=_CLOCK,
        event_id=event_id,
    )
    assert first.contribution == second.contribution
    assert first.audit_event == second.audit_event
    assert (
        len(audit_store.list_by_aggregate("contribution", contribution.contribution_id)) == 2
    )  # one from create, one from hide


# --- restore_contribution ------------------------------------------------------


def test_restore_contribution_from_hidden_reaches_restored() -> None:
    discussion_store = InMemoryDiscussionStore()
    contribution_store = InMemoryContributionStore()
    audit_store = InMemoryAuditEventStore()
    contribution = _setup_contribution(discussion_store, contribution_store, audit_store)
    hidden = hide_contribution(
        contribution_store,
        audit_store,
        contribution_id=contribution.contribution_id,
        target_status=ContributionVisibilityStatus.TEMPORARILY_HIDDEN,
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        causation_id=None,
        clock=_CLOCK,
    ).contribution
    result = restore_contribution(
        contribution_store,
        audit_store,
        contribution_id=hidden.contribution_id,
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        causation_id=None,
        clock=_CLOCK,
    )
    assert result.contribution.visibility_status.value == "restored"
    assert result.event.event_type == "contribution.restored"
    assert result.audit_event.reason_code == "CONTRIBUTION_STATUS_CHANGED"


def test_restore_contribution_from_restored_reaches_visible() -> None:
    """The second leg of the two-hop restore design: restored -> visible,
    still emitting contribution.restored (canon defines no other event
    name for this direction)."""
    discussion_store = InMemoryDiscussionStore()
    contribution_store = InMemoryContributionStore()
    audit_store = InMemoryAuditEventStore()
    contribution = _setup_contribution(discussion_store, contribution_store, audit_store)
    hidden = hide_contribution(
        contribution_store,
        audit_store,
        contribution_id=contribution.contribution_id,
        target_status=ContributionVisibilityStatus.RESTRICTED,
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        causation_id=None,
        clock=_CLOCK,
    ).contribution
    restored = restore_contribution(
        contribution_store,
        audit_store,
        contribution_id=hidden.contribution_id,
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        causation_id=None,
        clock=_CLOCK,
    ).contribution
    assert restored.visibility_status.value == "restored"
    visible_again = restore_contribution(
        contribution_store,
        audit_store,
        contribution_id=restored.contribution_id,
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        causation_id=None,
        clock=_CLOCK,
    )
    assert visible_again.contribution.visibility_status.value == "visible"
    assert visible_again.event.event_type == "contribution.restored"


def test_restore_contribution_from_visible_is_forbidden() -> None:
    discussion_store = InMemoryDiscussionStore()
    contribution_store = InMemoryContributionStore()
    audit_store = InMemoryAuditEventStore()
    contribution = _setup_contribution(discussion_store, contribution_store, audit_store)
    with pytest.raises(ForbiddenContributionVisibilityTransitionError):
        restore_contribution(
            contribution_store,
            audit_store,
            contribution_id=contribution.contribution_id,
            actor=_ACTOR,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            causation_id=None,
            clock=_CLOCK,
        )


def test_restore_contribution_without_permission_is_denied() -> None:
    discussion_store = InMemoryDiscussionStore()
    contribution_store = InMemoryContributionStore()
    audit_store = InMemoryAuditEventStore()
    contribution = _setup_contribution(discussion_store, contribution_store, audit_store)
    hidden = hide_contribution(
        contribution_store,
        audit_store,
        contribution_id=contribution.contribution_id,
        target_status=ContributionVisibilityStatus.TEMPORARILY_HIDDEN,
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        causation_id=None,
        clock=_CLOCK,
    ).contribution
    with pytest.raises(PermissionDeniedError):
        restore_contribution(
            contribution_store,
            audit_store,
            contribution_id=hidden.contribution_id,
            actor=_ACTOR,
            actor_is_authorized=False,
            correlation_id=uuid4(),
            causation_id=None,
            clock=_CLOCK,
        )


def test_restore_unknown_contribution_raises() -> None:
    contribution_store = InMemoryContributionStore()
    audit_store = InMemoryAuditEventStore()
    with pytest.raises(UnknownContributionError):
        restore_contribution(
            contribution_store,
            audit_store,
            contribution_id=uuid4(),
            actor=_ACTOR,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            causation_id=None,
            clock=_CLOCK,
        )


def test_restore_contribution_is_idempotent_for_repeated_event_id() -> None:
    discussion_store = InMemoryDiscussionStore()
    contribution_store = InMemoryContributionStore()
    audit_store = InMemoryAuditEventStore()
    contribution = _setup_contribution(discussion_store, contribution_store, audit_store)
    hidden = hide_contribution(
        contribution_store,
        audit_store,
        contribution_id=contribution.contribution_id,
        target_status=ContributionVisibilityStatus.TEMPORARILY_HIDDEN,
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        causation_id=None,
        clock=_CLOCK,
    ).contribution
    event_id = uuid4()
    correlation_id = uuid4()
    first = restore_contribution(
        contribution_store,
        audit_store,
        contribution_id=hidden.contribution_id,
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=correlation_id,
        causation_id=None,
        clock=_CLOCK,
        event_id=event_id,
    )
    second = restore_contribution(
        contribution_store,
        audit_store,
        contribution_id=hidden.contribution_id,
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=correlation_id,
        causation_id=None,
        clock=_CLOCK,
        event_id=event_id,
    )
    assert first.contribution == second.contribution
    assert first.contribution.visibility_status.value == "restored"  # not visible
    assert first.audit_event == second.audit_event
    assert (
        len(audit_store.list_by_aggregate("contribution", hidden.contribution_id)) == 3
    )  # create, hide, restore


def test_permission_denied_does_not_create_audit_event() -> None:
    """A refused command must not fabricate a false audit trail entry for
    an action that never happened."""
    discussion_store = InMemoryDiscussionStore()
    contribution_store = InMemoryContributionStore()
    audit_store = InMemoryAuditEventStore()
    contribution = _setup_contribution(discussion_store, contribution_store, audit_store)
    before_count = len(audit_store.list_by_aggregate("contribution", contribution.contribution_id))
    with pytest.raises(PermissionDeniedError):
        edit_contribution(
            contribution_store,
            audit_store,
            contribution_id=contribution.contribution_id,
            new_content="x",
            actor=_ACTOR,
            actor_is_authorized=False,
            correlation_id=uuid4(),
            causation_id=None,
            clock=_CLOCK,
        )
    after_count = len(audit_store.list_by_aggregate("contribution", contribution.contribution_id))
    assert after_count == before_count
