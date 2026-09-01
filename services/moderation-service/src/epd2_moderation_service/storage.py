"""Storage protocols and in-memory reference adapters for Moderation
Service's three owned entities: `ModerationCase`, `ModerationDecision`,
`Appeal` (canon sections 14.1/14.2/14.3). A durable backend can implement
these same protocols without any change to `application.py`.
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from epd2_moderation_service.domain import Appeal, ModerationCase, ModerationDecision
from epd2_moderation_service.exceptions import (
    AppealConflictError,
    ModerationCaseConflictError,
    ModerationDecisionConflictError,
)


class ModerationCaseStore(Protocol):
    def create(self, case: ModerationCase) -> ModerationCase:
        """Create a new case. If `case.moderation_case_id` already exists
        with identical content, returns the existing record (idempotent).
        If it exists with different content, raises
        `ModerationCaseConflictError`."""
        ...

    def save(self, case: ModerationCase) -> None:
        """Persist an update to an already-created case (e.g. after a
        status transition)."""
        ...

    def get(self, moderation_case_id: UUID) -> ModerationCase | None: ...


class ModerationDecisionStore(Protocol):
    def create(self, decision: ModerationDecision) -> ModerationDecision:
        """Create a new decision. `ModerationDecision` is immutable
        (`domain.py`) — there is no `save` for updates, only this
        idempotent creation (identical content on a repeat
        `moderation_decision_id` returns the existing record; different
        content raises `ModerationDecisionConflictError`)."""
        ...

    def get(self, moderation_decision_id: UUID) -> ModerationDecision | None: ...


class AppealStore(Protocol):
    def create(self, appeal: Appeal) -> Appeal:
        """Create a new appeal. Idempotent by content, the same shape as
        `ModerationCaseStore.create`."""
        ...

    def save(self, appeal: Appeal) -> None:
        """Persist an update to an already-created appeal (e.g. after
        `application.decide_appeal` moves it toward a final outcome)."""
        ...

    def get(self, appeal_id: UUID) -> Appeal | None: ...


class InMemoryModerationCaseStore:
    def __init__(self) -> None:
        self._cases: dict[UUID, ModerationCase] = {}

    def create(self, case: ModerationCase) -> ModerationCase:
        existing = self._cases.get(case.moderation_case_id)
        if existing is not None:
            if existing == case:
                return existing
            raise ModerationCaseConflictError(
                f"moderation_case_id {case.moderation_case_id} already exists "
                "with different content"
            )
        self._cases[case.moderation_case_id] = case
        return case

    def save(self, case: ModerationCase) -> None:
        self._cases[case.moderation_case_id] = case

    def get(self, moderation_case_id: UUID) -> ModerationCase | None:
        return self._cases.get(moderation_case_id)


class InMemoryModerationDecisionStore:
    def __init__(self) -> None:
        self._decisions: dict[UUID, ModerationDecision] = {}

    def create(self, decision: ModerationDecision) -> ModerationDecision:
        existing = self._decisions.get(decision.moderation_decision_id)
        if existing is not None:
            if existing == decision:
                return existing
            raise ModerationDecisionConflictError(
                f"moderation_decision_id {decision.moderation_decision_id} "
                "already exists with different content"
            )
        self._decisions[decision.moderation_decision_id] = decision
        return decision

    def get(self, moderation_decision_id: UUID) -> ModerationDecision | None:
        return self._decisions.get(moderation_decision_id)


class InMemoryAppealStore:
    def __init__(self) -> None:
        self._appeals: dict[UUID, Appeal] = {}

    def create(self, appeal: Appeal) -> Appeal:
        existing = self._appeals.get(appeal.appeal_id)
        if existing is not None:
            if existing == appeal:
                return existing
            raise AppealConflictError(
                f"appeal_id {appeal.appeal_id} already exists with different content"
            )
        self._appeals[appeal.appeal_id] = appeal
        return appeal

    def save(self, appeal: Appeal) -> None:
        self._appeals[appeal.appeal_id] = appeal

    def get(self, appeal_id: UUID) -> Appeal | None:
        return self._appeals.get(appeal_id)
