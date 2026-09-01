"""Storage protocols and in-memory reference adapters for Transparency
Service's four owned entities: `PublicLedgerEntry`, `AuditExportPackage`,
`DisclosurePolicy`, `LobbyLogEntry` (canon section 19a). A durable backend
can implement these same protocols without any change to `application.py`.
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from epd2_transparency_service.domain import (
    LEDGER_GENESIS_HASH,
    AuditExportPackage,
    DisclosurePolicy,
    DisclosurePolicyStatus,
    LobbyLogEntry,
    PublicLedgerEntry,
)
from epd2_transparency_service.exceptions import (
    AuditExportPackageConflictError,
    DisclosurePolicyConflictError,
    LobbyLogEntryConflictError,
    PublicLedgerEntryConflictError,
)


class PublicLedgerEntryStore(Protocol):
    def create(self, entry: PublicLedgerEntry) -> PublicLedgerEntry:
        """Create a new entry. If `entry.public_ledger_entry_id` already
        exists with identical content, returns the existing record
        (idempotent). If it exists with different content, raises
        `PublicLedgerEntryConflictError`. There is no `save` — a
        `PublicLedgerEntry` is never rewritten once created (canon
        section 19a.1)."""
        ...

    def get(self, public_ledger_entry_id: UUID) -> PublicLedgerEntry | None: ...

    def head_hash(self) -> str:
        """Return `content_hash` of the most recently created entry (in
        creation order), or `LEDGER_GENESIS_HASH` if none exist yet — the
        ledger's own light hash chain (`previous_entry_hash`), independent
        of Audit Core's own chain."""
        ...

    def get_by_subject_event_id(self, subject_event_id: UUID) -> PublicLedgerEntry | None:
        """Find the (at most one, non-superseded-by-construction — see
        `application.publish_ledger_entry`) entry originally published for
        `subject_event_id`, used to enforce `LEDGER_ENTRY_ALREADY_PUBLISHED`."""
        ...


class AuditExportPackageStore(Protocol):
    def create(self, package: AuditExportPackage) -> AuditExportPackage:
        """Create a new package. Idempotent by content, the same shape as
        `PublicLedgerEntryStore.create`."""
        ...

    def save(self, package: AuditExportPackage) -> None:
        """Persist a `status` transition (`generated -> published` or
        `published -> superseded`) — content fields are never changed by
        any caller of `save`; only `application.py`'s transition helpers
        construct the replacement via `AuditExportPackage.with_status`."""
        ...

    def get(self, audit_export_package_id: UUID) -> AuditExportPackage | None: ...


class DisclosurePolicyStore(Protocol):
    def create(self, policy: DisclosurePolicy) -> DisclosurePolicy:
        """Create a new policy. Idempotent by content."""
        ...

    def save(self, policy: DisclosurePolicy) -> None:
        """Persist a `status` transition (`draft -> active` or `active ->
        superseded`)."""
        ...

    def get(self, disclosure_policy_id: UUID) -> DisclosurePolicy | None: ...

    def get_active_for_subject_type(self, applies_to_subject_type: str) -> DisclosurePolicy | None:
        """Return the currently `active` policy for
        `applies_to_subject_type`, or `None`. Canon section 19a.3: "не
        более одной активной версии одновременно" — a durable backend
        must enforce this same invariant; the in-memory adapter enforces
        it by construction (see `InMemoryDisclosurePolicyStore.save`)."""
        ...


class LobbyLogEntryStore(Protocol):
    def create(self, entry: LobbyLogEntry) -> LobbyLogEntry:
        """Create a new entry. Idempotent by content."""
        ...

    def save(self, entry: LobbyLogEntry) -> None:
        """Persist the one-shot `submitted -> published` transition."""
        ...

    def get(self, lobby_log_entry_id: UUID) -> LobbyLogEntry | None: ...


class InMemoryPublicLedgerEntryStore:
    def __init__(self) -> None:
        self._entries: dict[UUID, PublicLedgerEntry] = {}
        self._creation_order: list[UUID] = []
        self._by_subject_event_id: dict[UUID, UUID] = {}

    def create(self, entry: PublicLedgerEntry) -> PublicLedgerEntry:
        existing = self._entries.get(entry.public_ledger_entry_id)
        if existing is not None:
            if existing == entry:
                return existing
            raise PublicLedgerEntryConflictError(
                f"public_ledger_entry_id {entry.public_ledger_entry_id} already exists "
                "with different content"
            )
        self._entries[entry.public_ledger_entry_id] = entry
        self._creation_order.append(entry.public_ledger_entry_id)
        if entry.supersedes_entry_id is None:
            self._by_subject_event_id.setdefault(
                entry.subject_event_id, entry.public_ledger_entry_id
            )
        return entry

    def get(self, public_ledger_entry_id: UUID) -> PublicLedgerEntry | None:
        return self._entries.get(public_ledger_entry_id)

    def head_hash(self) -> str:
        if not self._creation_order:
            return LEDGER_GENESIS_HASH
        return self._entries[self._creation_order[-1]].content_hash

    def get_by_subject_event_id(self, subject_event_id: UUID) -> PublicLedgerEntry | None:
        entry_id = self._by_subject_event_id.get(subject_event_id)
        return self._entries.get(entry_id) if entry_id is not None else None


class InMemoryAuditExportPackageStore:
    def __init__(self) -> None:
        self._packages: dict[UUID, AuditExportPackage] = {}

    def create(self, package: AuditExportPackage) -> AuditExportPackage:
        existing = self._packages.get(package.audit_export_package_id)
        if existing is not None:
            if existing == package:
                return existing
            raise AuditExportPackageConflictError(
                f"audit_export_package_id {package.audit_export_package_id} already exists "
                "with different content"
            )
        self._packages[package.audit_export_package_id] = package
        return package

    def save(self, package: AuditExportPackage) -> None:
        self._packages[package.audit_export_package_id] = package

    def get(self, audit_export_package_id: UUID) -> AuditExportPackage | None:
        return self._packages.get(audit_export_package_id)


class InMemoryDisclosurePolicyStore:
    def __init__(self) -> None:
        self._policies: dict[UUID, DisclosurePolicy] = {}
        self._active_by_subject_type: dict[str, UUID] = {}

    def create(self, policy: DisclosurePolicy) -> DisclosurePolicy:
        existing = self._policies.get(policy.disclosure_policy_id)
        if existing is not None:
            if existing == policy:
                return existing
            raise DisclosurePolicyConflictError(
                f"disclosure_policy_id {policy.disclosure_policy_id} already exists "
                "with different content"
            )
        self._policies[policy.disclosure_policy_id] = policy
        return policy

    def save(self, policy: DisclosurePolicy) -> None:
        self._policies[policy.disclosure_policy_id] = policy
        if policy.status is DisclosurePolicyStatus.ACTIVE:
            self._active_by_subject_type[policy.applies_to_subject_type] = (
                policy.disclosure_policy_id
            )
        elif (
            self._active_by_subject_type.get(policy.applies_to_subject_type)
            == policy.disclosure_policy_id
        ):
            del self._active_by_subject_type[policy.applies_to_subject_type]

    def get(self, disclosure_policy_id: UUID) -> DisclosurePolicy | None:
        return self._policies.get(disclosure_policy_id)

    def get_active_for_subject_type(self, applies_to_subject_type: str) -> DisclosurePolicy | None:
        policy_id = self._active_by_subject_type.get(applies_to_subject_type)
        return self._policies.get(policy_id) if policy_id is not None else None


class InMemoryLobbyLogEntryStore:
    def __init__(self) -> None:
        self._entries: dict[UUID, LobbyLogEntry] = {}

    def create(self, entry: LobbyLogEntry) -> LobbyLogEntry:
        existing = self._entries.get(entry.lobby_log_entry_id)
        if existing is not None:
            if existing == entry:
                return existing
            raise LobbyLogEntryConflictError(
                f"lobby_log_entry_id {entry.lobby_log_entry_id} already exists "
                "with different content"
            )
        self._entries[entry.lobby_log_entry_id] = entry
        return entry

    def save(self, entry: LobbyLogEntry) -> None:
        self._entries[entry.lobby_log_entry_id] = entry

    def get(self, lobby_log_entry_id: UUID) -> LobbyLogEntry | None:
        return self._entries.get(lobby_log_entry_id)
