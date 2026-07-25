"""Storage protocols and in-memory reference adapters for Tally Service's
two owned entities, `Tally` and `ResultPublication`.
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from epd2_tally_service.domain import ResultPublication, Tally
from epd2_tally_service.exceptions import ResultPublicationConflictError, TallyRecordConflictError


class TallyStore(Protocol):
    def create(self, tally: Tally) -> Tally:
        """Store a newly created `Tally` (`start_tally`'s own creation
        step). If `tally.tally_id` already exists with identical content,
        returns the existing record (idempotent - CT-00-04). If it exists
        with different content, raises `TallyRecordConflictError`."""
        ...

    def save(self, tally: Tally) -> None:
        """Persist an update to an already-created `Tally` (e.g. after a
        status transition via `with_status`/`with_completion`)."""
        ...

    def get(self, tally_id: UUID) -> Tally | None: ...


class ResultPublicationStore(Protocol):
    def create(self, result: ResultPublication) -> ResultPublication:
        """Store a newly created `ResultPublication` (`publish_result`'s
        own creation step - `ResultPublication` has no further mutation
        after creation, see `domain.py`). If
        `result.result_publication_id` already exists with identical
        content, returns the existing record (idempotent - CT-00-04). If
        it exists with different content, raises
        `ResultPublicationConflictError`."""
        ...

    def get(self, result_publication_id: UUID) -> ResultPublication | None: ...


class InMemoryTallyStore:
    def __init__(self) -> None:
        self._tallies: dict[UUID, Tally] = {}

    def create(self, tally: Tally) -> Tally:
        existing = self._tallies.get(tally.tally_id)
        if existing is not None:
            if existing == tally:
                return existing
            raise TallyRecordConflictError(
                f"tally_id {tally.tally_id} already exists with different content"
            )
        self._tallies[tally.tally_id] = tally
        return tally

    def save(self, tally: Tally) -> None:
        self._tallies[tally.tally_id] = tally

    def get(self, tally_id: UUID) -> Tally | None:
        return self._tallies.get(tally_id)


class InMemoryResultPublicationStore:
    def __init__(self) -> None:
        self._results: dict[UUID, ResultPublication] = {}

    def create(self, result: ResultPublication) -> ResultPublication:
        existing = self._results.get(result.result_publication_id)
        if existing is not None:
            if existing == result:
                return existing
            raise ResultPublicationConflictError(
                f"result_publication_id {result.result_publication_id} "
                "already exists with different content"
            )
        self._results[result.result_publication_id] = result
        return result

    def get(self, result_publication_id: UUID) -> ResultPublication | None:
        return self._results.get(result_publication_id)
