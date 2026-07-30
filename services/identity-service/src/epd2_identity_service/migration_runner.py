"""The migration runner: real artefacts, applied in order, in a
transaction, with a checksum.

`services/identity-service/migrations/*.sql` are **actual DDL files**,
not descriptions of DDL. This module is what applies them, following
PACK-13's ADR-075 discipline: an ordered list, an expand/contract kind
per step, a recorded application, and a compatibility check that refuses
to run against a database whose history disagrees with the files on disk.

**On not importing PACK-13's framework.**
`tests/repository/test_service_boundaries.py` forbids an
`identity-service` -> `data-plane-service` import outright, and
`epd2_core`'s charter forbids it holding business rules. So the
discipline is reimplemented here rather than imported, exactly as canon
7.2's status enum is - and kept honest the same way, by
`tests/repository/test_pack14_duplicated_logic_parity.py`, which asserts
that this module's migration-kind vocabulary and ordering rules match
`epd2_data_plane_service.migrations`.

**This is a reference persistence path, not a production data plane.** It
runs on SQLite through the standard library, which is why it adds no
dependency and why `make verify` can execute it. No PostgreSQL is
deployed, no production durability is claimed, and
`PACK-14-MIGRATION-REPORT.md` says so in the same words.
"""

from __future__ import annotations

import hashlib
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from epd2_identity_service.exceptions import (
    MigrationChecksumMismatchError,
    MigrationNotAppliedError,
    MigrationOutOfOrderError,
)
from epd2_identity_service.persistence import PACK14_MIGRATIONS, MigrationDefinition

#: Where the artefacts live. Resolved from this module rather than from
#: the working directory, so the runner works from anywhere.
MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "migrations"

#: The bookkeeping table. Created by the runner itself rather than by a
#: migration, because a migration that creates the table recording
#: migrations cannot record itself.
_BOOKKEEPING_DDL = """
CREATE TABLE IF NOT EXISTS schema_migration (
    identifier   TEXT    NOT NULL PRIMARY KEY,
    sequence     INTEGER NOT NULL,
    kind         TEXT    NOT NULL,
    checksum     TEXT    NOT NULL,
    applied_at   TEXT    NOT NULL
);
"""


@dataclass(frozen=True, slots=True)
class MigrationArtefact:
    """One definition, paired with the SQL that implements it."""

    definition: MigrationDefinition
    path: Path
    sql: str

    @property
    def checksum(self) -> str:
        return hashlib.sha256(self.sql.encode("utf-8")).hexdigest()


def load_artefacts(directory: Path = MIGRATIONS_DIR) -> tuple[MigrationArtefact, ...]:
    """Pair every definition with its file, and refuse a mismatch.

    A definition without a file is a migration that would silently do
    nothing; a file without a definition is DDL nobody declared. Both are
    refused here rather than discovered when a table turns out to be
    missing in production.
    """
    artefacts: list[MigrationArtefact] = []
    seen: set[str] = set()
    for definition in sorted(PACK14_MIGRATIONS, key=lambda item: item.sequence):
        filename = f"{definition.sequence:04d}_{definition.identifier.split('-', 2)[2]}.sql"
        path = directory / filename.replace("-", "_")
        if not path.is_file():
            raise MigrationNotAppliedError(
                f"migration {definition.identifier} declares no artefact at {path}"
            )
        seen.add(path.name)
        artefacts.append(
            MigrationArtefact(
                definition=definition, path=path, sql=path.read_text(encoding="utf-8")
            )
        )
    stray = {p.name for p in directory.glob("*.sql")} - seen
    if stray:
        raise MigrationNotAppliedError(
            f"migration artefacts with no declaration in PACK14_MIGRATIONS: {sorted(stray)}"
        )
    sequences = [artefact.definition.sequence for artefact in artefacts]
    if sequences != list(range(1, len(sequences) + 1)):
        raise MigrationOutOfOrderError(
            f"migration sequence numbers must be contiguous from 1; got {sequences}"
        )
    return tuple(artefacts)


def statements(sql: str) -> tuple[str, ...]:
    """Split an artefact into complete SQL statements.

    `sqlite3.Connection.executescript` cannot be used inside an open
    transaction - it issues an implicit COMMIT first, which would silently
    destroy the atomicity this runner exists to provide. So the artefact
    is split with `sqlite3.complete_statement` (the driver's own notion of
    "this is a whole statement") and each piece is executed individually
    inside the transaction.
    """
    collected: list[str] = []
    buffer = ""
    for line in sql.splitlines(keepends=True):
        stripped = line.strip()
        if not buffer and (not stripped or stripped.startswith("--")):
            continue
        buffer += line
        if sqlite3.complete_statement(buffer):
            collected.append(buffer.strip())
            buffer = ""
    if buffer.strip():
        raise MigrationOutOfOrderError("the artefact ends with an incomplete SQL statement")
    return tuple(collected)


@contextmanager
def transaction(connection: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    """One explicit transaction boundary.

    `isolation_level=None` puts the connection in autocommit, so this is
    the *only* place a transaction begins. A partially applied migration
    or a partially written aggregate is exactly what the rollback here
    prevents, and having one place that begins a transaction is what
    makes that reviewable.
    """
    connection.execute("BEGIN IMMEDIATE")
    try:
        yield connection
    except BaseException:
        connection.execute("ROLLBACK")
        raise
    connection.execute("COMMIT")


def connect(database: str = ":memory:") -> sqlite3.Connection:
    """Open a connection with the settings this package depends on.

    `foreign_keys=ON` is not a default in SQLite and every referential
    constraint in the artefacts would be decorative without it.
    `isolation_level=None` hands transaction control to `transaction()`
    above rather than to the driver's implicit behaviour.
    """
    connection = sqlite3.connect(database, isolation_level=None)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def applied_migrations(connection: sqlite3.Connection) -> dict[str, sqlite3.Row]:
    connection.executescript(_BOOKKEEPING_DDL)
    rows = connection.execute(
        "SELECT identifier, sequence, kind, checksum, applied_at FROM schema_migration"
    ).fetchall()
    return {row["identifier"]: row for row in rows}


def apply_migrations(
    connection: sqlite3.Connection,
    *,
    applied_at: datetime,
    directory: Path = MIGRATIONS_DIR,
) -> tuple[str, ...]:
    """Apply every unapplied artefact, in order, each in its own
    transaction.

    Returns the identifiers actually applied, so a caller can assert that
    a second run applies nothing - which is the operational meaning of
    "idempotent migration".
    """
    artefacts = load_artefacts(directory)
    already = applied_migrations(connection)
    newly: list[str] = []
    for artefact in artefacts:
        record = already.get(artefact.definition.identifier)
        if record is not None:
            if record["checksum"] != artefact.checksum:
                raise MigrationChecksumMismatchError(
                    f"{artefact.definition.identifier} was applied with a different artefact; "
                    "an applied migration is never edited in place (ADR-075)"
                )
            continue
        with transaction(connection):
            for statement in statements(artefact.sql):
                connection.execute(statement)
            connection.execute(
                "INSERT INTO schema_migration"
                " (identifier, sequence, kind, checksum, applied_at)"
                " VALUES (?, ?, ?, ?, ?)",
                (
                    artefact.definition.identifier,
                    artefact.definition.sequence,
                    artefact.definition.kind.value,
                    artefact.checksum,
                    applied_at.isoformat(),
                ),
            )
        newly.append(artefact.definition.identifier)
    return tuple(newly)


def verify_migrations(connection: sqlite3.Connection, *, directory: Path = MIGRATIONS_DIR) -> None:
    """The compatibility check.

    Three failures, each with its own code: an artefact that was never
    applied, an artefact whose content changed after it was applied, and
    a recorded application that no longer has a declaration. The middle
    one is the one that matters - editing an applied migration in place
    is the silent schema divergence ADR-075 forbids.
    """
    artefacts = load_artefacts(directory)
    already = applied_migrations(connection)
    for artefact in artefacts:
        record = already.get(artefact.definition.identifier)
        if record is None:
            raise MigrationNotAppliedError(
                f"migration {artefact.definition.identifier} has not been applied"
            )
        if record["checksum"] != artefact.checksum:
            raise MigrationChecksumMismatchError(
                f"{artefact.definition.identifier}'s artefact changed after it was applied"
            )
    declared = {artefact.definition.identifier for artefact in artefacts}
    orphaned = set(already) - declared
    if orphaned:
        raise MigrationOutOfOrderError(
            "the database records migrations this repository no longer declares: "
            f"{sorted(orphaned)}"
        )


def open_migrated(database: str, *, applied_at: datetime) -> sqlite3.Connection:
    """Connect, apply and verify - the one call an adapter needs.

    Verification runs after application deliberately: it is cheap, and it
    turns "the migrations ran" into "the schema is the one this code was
    written against" without the caller having to remember a second step.
    """
    connection = connect(database)
    apply_migrations(connection, applied_at=applied_at)
    verify_migrations(connection)
    return connection
