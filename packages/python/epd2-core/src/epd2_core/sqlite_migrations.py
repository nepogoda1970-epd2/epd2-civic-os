"""A small, dependency-free SQLite migration runner shared by services.

PACK-14 reimplemented this discipline inside `identity-service` because the
framework it mirrors lives in `data-plane-service`, and
`tests/repository/test_service_boundaries.py` forbids a service importing
another service. PACK-15 needs the same discipline in four services at
once, so the generic part lives here instead - `epd2-core` is the shared
library every service already depends on, so no service boundary is
crossed and nothing is duplicated four times.

What is generic and lives here: the definition record, the checksum, the
bookkeeping table, statement splitting, the transaction helper, apply and
verify. What stays per service: the migration **list** and the SQL files
themselves, which are that service's own storage boundary.
"""

from __future__ import annotations

import hashlib
import sqlite3
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path

BOOKKEEPING_TABLE = "schema_migration"


class MigrationError(RuntimeError):
    """Base class for migration failures."""


class MigrationFileMissingError(MigrationError):
    pass


class MigrationChecksumMismatchError(MigrationError):
    """An applied migration's file changed after the fact.

    Refused rather than re-applied: a silently edited migration is a
    schema whose history no longer explains it.
    """


class UnexpectedMigrationFileError(MigrationError):
    pass


class MigrationKind(StrEnum):
    EXPAND = "expand"
    CONTRACT = "contract"


@dataclass(frozen=True, slots=True)
class MigrationDefinition:
    """One migration, declared in Python and stored as SQL on disk."""

    identifier: str
    sequence: int
    kind: MigrationKind
    summary: str
    reversible: bool

    def __post_init__(self) -> None:
        if self.sequence < 1:
            raise MigrationError("migration sequences start at 1")
        if not self.identifier or not self.summary:
            raise MigrationError("a migration names itself and says what it does")

    def filename(self) -> str:
        """`p15-001-voting-contexts` -> `0001_voting_contexts.sql`."""
        parts = self.identifier.split("-", 2)
        if len(parts) != 3:
            raise MigrationError(f"{self.identifier!r} must be <pack>-<sequence>-<slug>")
        return f"{self.sequence:04d}_{parts[2]}.sql".replace("-", "_")


@dataclass(frozen=True, slots=True)
class MigrationArtefact:
    definition: MigrationDefinition
    path: Path
    sql: str
    checksum: str


def compute_checksum(sql: str) -> str:
    return hashlib.sha256(sql.encode("utf-8")).hexdigest()


def load_artefacts(
    definitions: Sequence[MigrationDefinition], directory: Path
) -> tuple[MigrationArtefact, ...]:
    """Load every declared migration and refuse any stray `.sql` file."""
    artefacts: list[MigrationArtefact] = []
    expected: set[str] = set()
    for definition in sorted(definitions, key=lambda item: item.sequence):
        filename = definition.filename()
        expected.add(filename)
        path = directory / filename
        if not path.exists():
            raise MigrationFileMissingError(f"missing migration file {path}")
        sql = path.read_text(encoding="utf-8")
        artefacts.append(
            MigrationArtefact(
                definition=definition, path=path, sql=sql, checksum=compute_checksum(sql)
            )
        )
    present = {item.name for item in directory.glob("*.sql")}
    stray = sorted(present - expected)
    if stray:
        raise UnexpectedMigrationFileError(
            "migration files not declared in the migration list: " + ", ".join(stray)
        )
    return tuple(artefacts)


def statements(sql: str) -> tuple[str, ...]:
    """Split a migration file into complete SQL statements."""
    found: list[str] = []
    buffer = ""
    for line in sql.splitlines(keepends=True):
        buffer += line
        if sqlite3.complete_statement(buffer):
            statement = buffer.strip()
            if statement:
                found.append(statement)
            buffer = ""
    if buffer.strip():
        raise MigrationError("a migration file ends with an incomplete statement")
    return tuple(found)


@contextmanager
def transaction(connection: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    """All-or-nothing. A partial apply is a schema nobody can reason about."""
    try:
        yield connection
    except BaseException:
        connection.rollback()
        raise
    connection.commit()


def connect(database: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(database, isolation_level="DEFERRED")
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _ensure_bookkeeping(connection: sqlite3.Connection) -> None:
    connection.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {BOOKKEEPING_TABLE} (
            identifier TEXT NOT NULL PRIMARY KEY,
            sequence   INTEGER NOT NULL,
            kind       TEXT NOT NULL,
            checksum   TEXT NOT NULL,
            applied_at TEXT NOT NULL
        )
        """
    )


def applied_migrations(connection: sqlite3.Connection) -> dict[str, str]:
    _ensure_bookkeeping(connection)
    rows = connection.execute(f"SELECT identifier, checksum FROM {BOOKKEEPING_TABLE}").fetchall()
    return {row["identifier"]: row["checksum"] for row in rows}


def apply_migrations(
    connection: sqlite3.Connection,
    artefacts: Sequence[MigrationArtefact],
    *,
    applied_at: datetime,
) -> tuple[str, ...]:
    """Apply every not-yet-applied migration inside one transaction."""
    already = applied_migrations(connection)
    newly: list[str] = []
    with transaction(connection):
        for artefact in artefacts:
            identifier = artefact.definition.identifier
            if identifier in already:
                if already[identifier] != artefact.checksum:
                    raise MigrationChecksumMismatchError(
                        f"{identifier} was applied with a different file"
                    )
                continue
            for statement in statements(artefact.sql):
                connection.execute(statement)
            connection.execute(
                f"INSERT INTO {BOOKKEEPING_TABLE} "
                "(identifier, sequence, kind, checksum, applied_at) VALUES (?, ?, ?, ?, ?)",
                (
                    identifier,
                    artefact.definition.sequence,
                    artefact.definition.kind.value,
                    artefact.checksum,
                    applied_at.isoformat(),
                ),
            )
            newly.append(identifier)
    return tuple(newly)


def verify_migrations(
    connection: sqlite3.Connection, artefacts: Sequence[MigrationArtefact]
) -> None:
    """Refuse a database whose applied history does not match the files."""
    already = applied_migrations(connection)
    for artefact in artefacts:
        identifier = artefact.definition.identifier
        if identifier not in already:
            raise MigrationError(f"{identifier} has not been applied")
        if already[identifier] != artefact.checksum:
            raise MigrationChecksumMismatchError(f"{identifier} was applied with a different file")


def open_migrated(
    database: str | Path,
    definitions: Sequence[MigrationDefinition],
    directory: Path,
    *,
    applied_at: datetime,
) -> sqlite3.Connection:
    """Open a connection with every declared migration applied."""
    artefacts = load_artefacts(definitions, directory)
    connection = connect(database)
    apply_migrations(connection, artefacts, applied_at=applied_at)
    verify_migrations(connection, artefacts)
    return connection


def table_columns(connection: sqlite3.Connection, table: str) -> tuple[str, ...]:
    """The column names of a table, for the boundary tests."""
    rows = connection.execute(f"PRAGMA table_info({table})").fetchall()
    return tuple(str(row["name"]) for row in rows)


def foreign_keys(connection: sqlite3.Connection, table: str) -> tuple[str, ...]:
    """The tables a table references, for the boundary tests."""
    rows = connection.execute(f"PRAGMA foreign_key_list({table})").fetchall()
    return tuple(str(row["table"]) for row in rows)


def table_names(connection: sqlite3.Connection) -> tuple[str, ...]:
    rows = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
    ).fetchall()
    return tuple(str(row["name"]) for row in rows)
