"""Storage protocols and in-memory reference adapters for Initiative
Service's five owned entities: `Initiative`, `InitiativeVersion`,
`SupportRecord`, `Amendment`, `SourceRecord`.

Every store follows the same two-method creation/update shape PACK-02
established (`CredentialStore.issue`/`save`,
`EligibilityRuleStore.save` with its own freeze check): a `create` (or,
for the freeze-on-version entity, a `save` that behaves like `create`)
that is idempotent for an identical resubmission and raises a
conflict/freeze error for a resubmission with different content under
the same id, plus a plain `save` for legitimate subsequent updates (a
status transition, a support-count change) that does not re-run the
creation-time conflict check.
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from epd2_initiative_service.domain import (
    Amendment,
    Initiative,
    InitiativeVersion,
    SourceRecord,
    SupportRecord,
    SupportStatus,
)
from epd2_initiative_service.exceptions import (
    AmendmentCreationConflictError,
    DuplicateSupportError,
    InitiativeCreationConflictError,
    InitiativeVersionFrozenError,
    SourceRecordCreationConflictError,
    SupportRecordCreationConflictError,
)


class InitiativeStore(Protocol):
    def create(self, initiative: Initiative) -> Initiative:
        """Create a new `Initiative`. If `initiative.initiative_id`
        already exists with identical content, returns the existing
        record (idempotent). If it exists with different content, raises
        `InitiativeCreationConflictError`."""
        ...

    def save(self, initiative: Initiative) -> None:
        """Persist an update to an already-created initiative (e.g. after
        a status transition, a support_count change, or a new
        `current_version_id`)."""
        ...

    def get(self, initiative_id: UUID) -> Initiative | None: ...


class InitiativeVersionStore(Protocol):
    def save(self, version: InitiativeVersion) -> InitiativeVersion:
        """Save a new version. If `(initiative_id, version_number)`
        already exists with identical content, returns the existing
        record (idempotent). If it exists with different content, raises
        `InitiativeVersionFrozenError` - canon section 11.2: a published
        version never changes."""
        ...

    def get(self, initiative_id: UUID, version_number: int) -> InitiativeVersion | None: ...

    def get_by_id(self, initiative_version_id: UUID) -> InitiativeVersion | None:
        """Lookup by the version's own id - needed because
        `Initiative.current_version_id` and `Amendment.target_version_id`
        both reference `initiative_version_id`, not the
        `(initiative_id, version_number)` pair."""
        ...

    def latest_version(self, initiative_id: UUID) -> InitiativeVersion | None: ...


class SupportRecordStore(Protocol):
    def create(self, support: SupportRecord) -> SupportRecord:
        """Create a new `SupportRecord`. If `support.support_record_id`
        already exists with identical content, returns the existing
        record (idempotent). If it exists with different content, raises
        `SupportRecordCreationConflictError`. If the new record's status
        is `active` and another `active` `SupportRecord` already exists
        for the same `(initiative_id, support_actor_reference)`, raises
        `DuplicateSupportError` (canon section 11.3 / canon section 24's
        `DUPLICATE_SUPPORT` reason code) - a participant may have at most
        one active support per initiative."""
        ...

    def save(self, support: SupportRecord) -> None:
        """Persist an update to an already-created support record (a
        status transition to `withdrawn`/`invalidated`)."""
        ...

    def get(self, support_record_id: UUID) -> SupportRecord | None: ...


class AmendmentStore(Protocol):
    def create(self, amendment: Amendment) -> Amendment:
        """Create a new `Amendment`. If `amendment.amendment_id` already
        exists with identical content, returns the existing record
        (idempotent). If it exists with different content, raises
        `AmendmentCreationConflictError`."""
        ...

    def save(self, amendment: Amendment) -> None:
        """Persist an update to an already-created amendment (a status
        transition, or a new `decision_reference`)."""
        ...

    def get(self, amendment_id: UUID) -> Amendment | None: ...


class SourceRecordStore(Protocol):
    def create(self, source: SourceRecord) -> SourceRecord:
        """Create a new `SourceRecord`. If `source.source_id` already
        exists with identical content, returns the existing record
        (idempotent). If it exists with different content, raises
        `SourceRecordCreationConflictError`."""
        ...

    def save(self, source: SourceRecord) -> None:
        """Persist an update to an already-created source record (a
        `verification_status` transition)."""
        ...

    def get(self, source_id: UUID) -> SourceRecord | None: ...


class InMemoryInitiativeStore:
    def __init__(self) -> None:
        self._initiatives: dict[UUID, Initiative] = {}

    def create(self, initiative: Initiative) -> Initiative:
        existing = self._initiatives.get(initiative.initiative_id)
        if existing is not None:
            if existing == initiative:
                return existing
            raise InitiativeCreationConflictError(
                f"initiative_id {initiative.initiative_id} already exists with different content"
            )
        self._initiatives[initiative.initiative_id] = initiative
        return initiative

    def save(self, initiative: Initiative) -> None:
        self._initiatives[initiative.initiative_id] = initiative

    def get(self, initiative_id: UUID) -> Initiative | None:
        return self._initiatives.get(initiative_id)


class InMemoryInitiativeVersionStore:
    def __init__(self) -> None:
        self._by_key: dict[tuple[UUID, int], InitiativeVersion] = {}
        self._by_id: dict[UUID, InitiativeVersion] = {}

    def save(self, version: InitiativeVersion) -> InitiativeVersion:
        key = (version.initiative_id, version.version_number)
        existing = self._by_key.get(key)
        if existing is not None:
            if existing == version:
                return existing
            raise InitiativeVersionFrozenError(
                f"initiative {version.initiative_id} version {version.version_number} "
                "already exists with different content"
            )
        self._by_key[key] = version
        self._by_id[version.initiative_version_id] = version
        return version

    def get(self, initiative_id: UUID, version_number: int) -> InitiativeVersion | None:
        return self._by_key.get((initiative_id, version_number))

    def get_by_id(self, initiative_version_id: UUID) -> InitiativeVersion | None:
        return self._by_id.get(initiative_version_id)

    def latest_version(self, initiative_id: UUID) -> InitiativeVersion | None:
        matching = [v for (iid, _), v in self._by_key.items() if iid == initiative_id]
        if not matching:
            return None
        return max(matching, key=lambda v: v.version_number)


class InMemorySupportRecordStore:
    def __init__(self) -> None:
        self._records: dict[UUID, SupportRecord] = {}

    def create(self, support: SupportRecord) -> SupportRecord:
        existing = self._records.get(support.support_record_id)
        if existing is not None:
            if existing == support:
                return existing
            raise SupportRecordCreationConflictError(
                f"support_record_id {support.support_record_id} "
                "already exists with different content"
            )
        if support.status == SupportStatus.ACTIVE:
            for other in self._records.values():
                if (
                    other.initiative_id == support.initiative_id
                    and other.support_actor_reference == support.support_actor_reference
                    and other.status == SupportStatus.ACTIVE
                ):
                    raise DuplicateSupportError(
                        f"actor reference {support.support_actor_reference} already has an "
                        f"active support record for initiative {support.initiative_id}"
                    )
        self._records[support.support_record_id] = support
        return support

    def save(self, support: SupportRecord) -> None:
        self._records[support.support_record_id] = support

    def get(self, support_record_id: UUID) -> SupportRecord | None:
        return self._records.get(support_record_id)


class InMemoryAmendmentStore:
    def __init__(self) -> None:
        self._amendments: dict[UUID, Amendment] = {}

    def create(self, amendment: Amendment) -> Amendment:
        existing = self._amendments.get(amendment.amendment_id)
        if existing is not None:
            if existing == amendment:
                return existing
            raise AmendmentCreationConflictError(
                f"amendment_id {amendment.amendment_id} already exists with different content"
            )
        self._amendments[amendment.amendment_id] = amendment
        return amendment

    def save(self, amendment: Amendment) -> None:
        self._amendments[amendment.amendment_id] = amendment

    def get(self, amendment_id: UUID) -> Amendment | None:
        return self._amendments.get(amendment_id)


class InMemorySourceRecordStore:
    def __init__(self) -> None:
        self._sources: dict[UUID, SourceRecord] = {}

    def create(self, source: SourceRecord) -> SourceRecord:
        existing = self._sources.get(source.source_id)
        if existing is not None:
            if existing == source:
                return existing
            raise SourceRecordCreationConflictError(
                f"source_id {source.source_id} already exists with different content"
            )
        self._sources[source.source_id] = source
        return source

    def save(self, source: SourceRecord) -> None:
        self._sources[source.source_id] = source

    def get(self, source_id: UUID) -> SourceRecord | None:
        return self._sources.get(source_id)
