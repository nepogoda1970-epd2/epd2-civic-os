"""Durable SQLite adapters for the six PACK-15 audit streams.

Three migration sets, three **separate database files**:

* identity-side — AS-01 (eligibility), AS-02 (assertion);
* voting-side — AS-03 (credential), AS-04 (voting integrity);
* neutral — AS-05 (independent), AS-06 (system integrity), and the
  evidence-bundle export log.

`assert_streams_separable` refuses a *request* that spans the boundary.
This module makes the same rule structural: an identity-side query and a
voting-side query run against different files, so a join between AS-02
and AS-03 has no syntax, and a role that holds one connection does not
hold the other (ADR-097).

Every stream table has its own key space - AS-01 carries a case
reference, AS-02 an assertion reference, AS-03 a credential reference,
and AS-04 to AS-06 carry no subject at all. No table carries two of
them, which is the ADR-093 pairing prohibition expressed in DDL.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from uuid import UUID

from epd2_audit_core.voting_evidence_bundle import (
    AuditStream,
    EvidenceBundle,
    EvidenceBundleScopeRefusedError,
)
from epd2_core.sqlite_migrations import (
    MigrationDefinition,
    MigrationKind,
    open_migrated,
)

MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "migrations"
IDENTITY_SIDE_MIGRATIONS_DIR = MIGRATIONS_DIR / "identity-side"
VOTING_SIDE_MIGRATIONS_DIR = MIGRATIONS_DIR / "voting-side"
NEUTRAL_MIGRATIONS_DIR = MIGRATIONS_DIR / "neutral"

PACK15_IDENTITY_SIDE_AUDIT_MIGRATIONS: tuple[MigrationDefinition, ...] = (
    MigrationDefinition(
        identifier="p15-001-identity-side-audit-streams",
        sequence=1,
        kind=MigrationKind.EXPAND,
        summary="Audit streams AS-01 (eligibility) and AS-02 (assertion).",
        reversible=True,
    ),
)

PACK15_VOTING_SIDE_AUDIT_MIGRATIONS: tuple[MigrationDefinition, ...] = (
    MigrationDefinition(
        identifier="p15-001-voting-side-audit-streams",
        sequence=1,
        kind=MigrationKind.EXPAND,
        summary="Audit streams AS-03 (credential) and AS-04 (voting integrity).",
        reversible=True,
    ),
)

PACK15_NEUTRAL_AUDIT_MIGRATIONS: tuple[MigrationDefinition, ...] = (
    MigrationDefinition(
        identifier="p15-001-neutral-audit-streams",
        sequence=1,
        kind=MigrationKind.EXPAND,
        summary="Audit streams AS-05, AS-06 and the evidence-bundle export log.",
        reversible=True,
    ),
)

#: Which stream lives in which database, and under which table. A stream
#: added without an entry here has nowhere to be written, which is the
#: intended failure mode.
STREAM_TABLES: Mapping[AuditStream, str] = {
    AuditStream.ELIGIBILITY: "audit_record_as01_eligibility",
    AuditStream.ASSERTION: "audit_record_as02_assertion",
    AuditStream.CREDENTIAL: "audit_record_as03_credential",
    AuditStream.VOTING_INTEGRITY: "audit_record_as04_voting_integrity",
    AuditStream.INDEPENDENT: "audit_record_as05_independent",
    AuditStream.SYSTEM_INTEGRITY: "audit_record_as06_system_integrity",
}

#: The per-stream subject column. `None` means the stream is
#: aggregate-only and has no subject at all.
STREAM_SUBJECT_COLUMNS: Mapping[AuditStream, str] = {
    AuditStream.ELIGIBILITY: "case_reference",
    AuditStream.ASSERTION: "assertion_reference",
    AuditStream.CREDENTIAL: "credential_reference",
    AuditStream.VOTING_INTEGRITY: "observation_class",
    AuditStream.INDEPENDENT: "observer_role",
    AuditStream.SYSTEM_INTEGRITY: "component",
}

IDENTITY_SIDE_DATABASE_STREAMS: frozenset[AuditStream] = frozenset(
    {AuditStream.ELIGIBILITY, AuditStream.ASSERTION}
)
VOTING_SIDE_DATABASE_STREAMS: frozenset[AuditStream] = frozenset(
    {AuditStream.CREDENTIAL, AuditStream.VOTING_INTEGRITY}
)
NEUTRAL_DATABASE_STREAMS: frozenset[AuditStream] = frozenset(
    {AuditStream.INDEPENDENT, AuditStream.SYSTEM_INTEGRITY}
)


def open_identity_side_audit_database(
    database: str | Path, *, applied_at: datetime
) -> sqlite3.Connection:
    return open_migrated(
        database,
        PACK15_IDENTITY_SIDE_AUDIT_MIGRATIONS,
        IDENTITY_SIDE_MIGRATIONS_DIR,
        applied_at=applied_at,
    )


def open_voting_side_audit_database(
    database: str | Path, *, applied_at: datetime
) -> sqlite3.Connection:
    return open_migrated(
        database,
        PACK15_VOTING_SIDE_AUDIT_MIGRATIONS,
        VOTING_SIDE_MIGRATIONS_DIR,
        applied_at=applied_at,
    )


def open_neutral_audit_database(
    database: str | Path, *, applied_at: datetime
) -> sqlite3.Connection:
    return open_migrated(
        database,
        PACK15_NEUTRAL_AUDIT_MIGRATIONS,
        NEUTRAL_MIGRATIONS_DIR,
        applied_at=applied_at,
    )


@dataclass(frozen=True, slots=True)
class VotingAuditRecord:
    """One append-only audit record in exactly one stream."""

    record_id: UUID
    stream: AuditStream
    voting_context_reference: str
    event_type: str
    reason_code: str
    recorded_at_bucket: datetime
    subject: str
    payload_hash: str
    payload: Mapping[str, object]
    retention_class: str
    legal_hold: bool = False

    def __post_init__(self) -> None:
        if not self.subject:
            raise ValueError("a record names its stream-local subject or observation class")
        if self.recorded_at_bucket.tzinfo is None:
            raise ValueError("timestamps are timezone-aware")


@dataclass
class SqlVotingAuditStreamStore:
    """An append-only store bound to one database and its streams.

    `permitted_streams` is the database's own stream set, so an attempt to
    append an AS-03 record through the identity-side connection is refused
    here rather than failing later on a missing table.
    """

    connection: sqlite3.Connection
    permitted_streams: frozenset[AuditStream]

    def append(self, record: VotingAuditRecord) -> None:
        if record.stream not in self.permitted_streams:
            raise EvidenceBundleScopeRefusedError(
                f"{record.stream.value} does not belong to this audit database"
            )
        table = STREAM_TABLES[record.stream]
        subject_column = STREAM_SUBJECT_COLUMNS[record.stream]
        self.connection.execute(
            f"""
            INSERT INTO {table} (
                record_id, stream, voting_context_reference, event_type, reason_code,
                recorded_at_bucket, {subject_column}, payload_hash, document,
                retention_class, legal_hold
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(record.record_id),
                record.stream.value,
                record.voting_context_reference,
                record.event_type,
                record.reason_code,
                record.recorded_at_bucket.isoformat(),
                record.subject,
                record.payload_hash,
                json.dumps(dict(record.payload), sort_keys=True, default=str),
                record.retention_class,
                int(record.legal_hold),
            ),
        )

    def records(
        self, stream: AuditStream, voting_context_reference: str
    ) -> Sequence[VotingAuditRecord]:
        if stream not in self.permitted_streams:
            raise EvidenceBundleScopeRefusedError(
                f"{stream.value} is not readable through this audit database"
            )
        table = STREAM_TABLES[stream]
        subject_column = STREAM_SUBJECT_COLUMNS[stream]
        rows = self.connection.execute(
            f"SELECT * FROM {table} WHERE voting_context_reference = ? "
            "ORDER BY recorded_at_bucket, record_id",
            (voting_context_reference,),
        ).fetchall()
        return tuple(
            VotingAuditRecord(
                record_id=UUID(row["record_id"]),
                stream=AuditStream(row["stream"]),
                voting_context_reference=row["voting_context_reference"],
                event_type=row["event_type"],
                reason_code=row["reason_code"],
                recorded_at_bucket=datetime.fromisoformat(row["recorded_at_bucket"]),
                subject=row[subject_column],
                payload_hash=row["payload_hash"],
                payload=json.loads(row["document"]),
                retention_class=row["retention_class"],
                legal_hold=bool(row["legal_hold"]),
            )
            for row in rows
        )

    def count(self, stream: AuditStream, voting_context_reference: str) -> int:
        return len(self.records(stream, voting_context_reference))


@dataclass
class SqlEvidenceBundleExportStore:
    """The export log. Lives in the neutral database, beside neither side."""

    connection: sqlite3.Connection

    def record_export(
        self,
        bundle: EvidenceBundle,
        *,
        bundle_id: UUID,
        exported_by_role: str,
        grant_reference: str,
        dual_control_reference: str | None,
    ) -> None:
        """Persist an export.

        A pre-closure export without a dual-control reference violates the
        table's CHECK, so four-eyes is a storage constraint rather than a
        step someone can forget.
        """
        self.connection.execute(
            """
            INSERT INTO evidence_bundle_export (
                bundle_id, voting_context_reference, bundle_schema_version, key_identifier,
                signature, pre_closure, exported_by_role, grant_reference,
                dual_control_reference, generated_at_bucket, document
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(bundle_id),
                bundle.voting_context_reference,
                bundle.bundle_schema_version,
                bundle.key_identifier,
                bundle.signature,
                int(bundle.pre_closure),
                exported_by_role,
                grant_reference,
                dual_control_reference,
                bundle.generated_at_bucket.isoformat(),
                json.dumps(
                    {name: dict(section) for name, section in bundle.sections.items()},
                    sort_keys=True,
                    default=str,
                ),
            ),
        )

    def exports_for_context(
        self, voting_context_reference: str
    ) -> tuple[Mapping[str, object], ...]:
        rows = self.connection.execute(
            "SELECT * FROM evidence_bundle_export WHERE voting_context_reference = ? "
            "ORDER BY generated_at_bucket",
            (voting_context_reference,),
        ).fetchall()
        return tuple(dict(row) for row in rows)
