"""Durable SQLite adapters for the PACK-15 voting credential issuer.

The default runtime binding. The in-memory adapters in
`voting_credential_storage.py` are test bindings.

Two properties are enforced by the **database**, not by application code:

* `uq_credential_redemption_credential` makes a second redemption a
  constraint violation rather than a check-then-act race;
* `spent_nonce` has the nonce as its primary key and no value column, so
  the atomic `INSERT` is the spent-set check and there is nowhere for a
  credential reference to be recorded beside it.

The voting-side database is a **separate file** from every identity-side
database, so a foreign key from a credential to an assertion is not
expressible - which is a stronger guarantee than not writing one.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from uuid import UUID

from epd2_core.sqlite_migrations import (
    MigrationDefinition,
    MigrationKind,
    open_migrated,
)
from epd2_credential_service.voting_credentials import (
    CredentialIssuanceIdempotencyRecord,
    CredentialRedemption,
    CredentialReplayRecord,
    CredentialStatus,
    SpentNonce,
    VotingCredential,
)

MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "migrations"

#: Expand-only: this round adds tables and indexes and drops nothing.
PACK15_CREDENTIAL_MIGRATIONS: tuple[MigrationDefinition, ...] = (
    MigrationDefinition(
        identifier="p15-001-voting-credentials",
        sequence=1,
        kind=MigrationKind.EXPAND,
        summary="Voting credentials, their status and their revocation metadata.",
        reversible=True,
    ),
    MigrationDefinition(
        identifier="p15-002-spent-nonce-set",
        sequence=2,
        kind=MigrationKind.EXPAND,
        summary="The spent-nonce set and the bounded issuance idempotency window.",
        reversible=True,
    ),
    MigrationDefinition(
        identifier="p15-003-redemption-and-replay",
        sequence=3,
        kind=MigrationKind.EXPAND,
        summary="Atomic redemption, replay records and revocation records.",
        reversible=True,
    ),
)


def open_voting_side_database(database: str | Path, *, applied_at: datetime) -> sqlite3.Connection:
    """Open the voting-side database with its migrations applied."""
    return open_migrated(
        database, PACK15_CREDENTIAL_MIGRATIONS, MIGRATIONS_DIR, applied_at=applied_at
    )


def _iso(moment: datetime | None) -> str | None:
    return moment.isoformat() if moment is not None else None


def _parse(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


@dataclass
class SqlSpentNonceSet:
    """The spent-nonce **set**. Three columns, no value column, ever."""

    connection: sqlite3.Connection

    def contains(self, nonce: str) -> bool:
        row = self.connection.execute(
            "SELECT 1 FROM spent_nonce WHERE nonce = ?", (nonce,)
        ).fetchone()
        return row is not None

    def add(self, spent: SpentNonce) -> bool:
        """Atomic: the INSERT itself is the check.

        A concurrent second issuance loses on the primary key rather than
        on a prior `contains()` that raced.
        """
        try:
            self.connection.execute(
                "INSERT INTO spent_nonce (nonce, voting_context_reference, spent_at_bucket) "
                "VALUES (?, ?, ?)",
                (
                    spent.nonce,
                    spent.voting_context_reference,
                    spent.spent_at_bucket.isoformat(),
                ),
            )
        except sqlite3.IntegrityError:
            return False
        return True

    def count(self, voting_context_reference: str) -> int:
        row = self.connection.execute(
            "SELECT COUNT(*) AS n FROM spent_nonce WHERE voting_context_reference = ?",
            (voting_context_reference,),
        ).fetchone()
        return int(row["n"])


@dataclass
class SqlVotingCredentialStore:
    connection: sqlite3.Connection

    def save(self, credential: VotingCredential) -> None:
        document = json.dumps(
            {
                "credential_type": credential.credential_type,
                "status": credential.status.value,
                "audience_origin": credential.audience_origin,
            },
            sort_keys=True,
        )
        self.connection.execute(
            """
            INSERT INTO voting_credential (
                voting_credential_id, credential_type, status, voting_context_reference,
                issued_at_bucket, expires_at, redeemed_at, revoked_at, revocation_reason,
                redemption_reference, audience_origin, document
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(voting_credential_id) DO UPDATE SET
                status = excluded.status,
                redeemed_at = excluded.redeemed_at,
                revoked_at = excluded.revoked_at,
                revocation_reason = excluded.revocation_reason,
                redemption_reference = excluded.redemption_reference,
                document = excluded.document
            """,
            (
                str(credential.voting_credential_id),
                credential.credential_type,
                credential.status.value,
                credential.voting_context_reference,
                credential.issued_at_bucket.isoformat(),
                credential.expires_at.isoformat(),
                _iso(credential.redeemed_at),
                _iso(credential.revoked_at),
                credential.revocation_reason,
                credential.redemption_reference,
                credential.audience_origin,
                document,
            ),
        )

    def get(self, voting_credential_id: UUID) -> VotingCredential | None:
        row = self.connection.execute(
            "SELECT * FROM voting_credential WHERE voting_credential_id = ?",
            (str(voting_credential_id),),
        ).fetchone()
        if row is None:
            return None
        return VotingCredential(
            voting_credential_id=UUID(row["voting_credential_id"]),
            credential_type=row["credential_type"],
            status=CredentialStatus(row["status"]),
            voting_context_reference=row["voting_context_reference"],
            issued_at_bucket=datetime.fromisoformat(row["issued_at_bucket"]),
            expires_at=datetime.fromisoformat(row["expires_at"]),
            redeemed_at=_parse(row["redeemed_at"]),
            revoked_at=_parse(row["revoked_at"]),
            revocation_reason=row["revocation_reason"],
            redemption_reference=row["redemption_reference"],
            audience_origin=row["audience_origin"],
        )

    def count_by_status(self, voting_context_reference: str, status: CredentialStatus) -> int:
        row = self.connection.execute(
            "SELECT COUNT(*) AS n FROM voting_credential "
            "WHERE voting_context_reference = ? AND status = ?",
            (voting_context_reference, status.value),
        ).fetchone()
        return int(row["n"])


@dataclass
class SqlCredentialIdempotencyStore:
    connection: sqlite3.Connection

    def get(self, idempotency_key: str) -> CredentialIssuanceIdempotencyRecord | None:
        row = self.connection.execute(
            "SELECT * FROM credential_issuance_idempotency WHERE idempotency_key = ?",
            (idempotency_key,),
        ).fetchone()
        if row is None:
            return None
        return CredentialIssuanceIdempotencyRecord(
            idempotency_key=row["idempotency_key"],
            voting_credential_id=UUID(row["voting_credential_id"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            expires_at=datetime.fromisoformat(row["expires_at"]),
        )

    def put(self, record: CredentialIssuanceIdempotencyRecord) -> None:
        self.connection.execute(
            "INSERT OR REPLACE INTO credential_issuance_idempotency "
            "(idempotency_key, voting_credential_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
            (
                record.idempotency_key,
                str(record.voting_credential_id),
                record.created_at.isoformat(),
                record.expires_at.isoformat(),
            ),
        )

    def purge_expired(self, now: datetime) -> int:
        cursor = self.connection.execute(
            "DELETE FROM credential_issuance_idempotency WHERE expires_at <= ?",
            (now.isoformat(),),
        )
        return int(cursor.rowcount)


@dataclass
class SqlCredentialRedemptionStore:
    connection: sqlite3.Connection

    def save(self, redemption: CredentialRedemption) -> None:
        """A second redemption of one credential violates the unique index."""
        self.connection.execute(
            "INSERT INTO credential_redemption (redemption_reference, voting_credential_id, "
            "voting_context_reference, redeemed_at_bucket) VALUES (?, ?, ?, ?)",
            (
                redemption.redemption_reference,
                str(redemption.voting_credential_id),
                redemption.voting_context_reference,
                redemption.redeemed_at_bucket.isoformat(),
            ),
        )

    def get(self, redemption_reference: str) -> CredentialRedemption | None:
        row = self.connection.execute(
            "SELECT * FROM credential_redemption WHERE redemption_reference = ?",
            (redemption_reference,),
        ).fetchone()
        if row is None:
            return None
        return CredentialRedemption(
            redemption_reference=row["redemption_reference"],
            voting_credential_id=UUID(row["voting_credential_id"]),
            voting_context_reference=row["voting_context_reference"],
            redeemed_at_bucket=datetime.fromisoformat(row["redeemed_at_bucket"]),
            continuation_capability="withheld",
        )

    def count(self, voting_context_reference: str) -> int:
        row = self.connection.execute(
            "SELECT COUNT(*) AS n FROM credential_redemption WHERE voting_context_reference = ?",
            (voting_context_reference,),
        ).fetchone()
        return int(row["n"])


@dataclass
class SqlCredentialReplayStore:
    connection: sqlite3.Connection

    def record(self, replay: CredentialReplayRecord) -> None:
        self.connection.execute(
            "INSERT INTO credential_replay_record (replay_id, voting_context_reference, "
            "reason_code, detected_at_bucket, timing_class) VALUES (?, ?, ?, ?, ?)",
            (
                str(replay.replay_id),
                replay.voting_context_reference,
                replay.reason_code,
                replay.detected_at_bucket.isoformat(),
                replay.timing_class,
            ),
        )

    def count(self, voting_context_reference: str) -> int:
        row = self.connection.execute(
            "SELECT COUNT(*) AS n FROM credential_replay_record WHERE voting_context_reference = ?",
            (voting_context_reference,),
        ).fetchone()
        return int(row["n"])

    def all_for_context(self, voting_context_reference: str) -> Sequence[CredentialReplayRecord]:
        rows = self.connection.execute(
            "SELECT * FROM credential_replay_record WHERE voting_context_reference = ? "
            "ORDER BY detected_at_bucket",
            (voting_context_reference,),
        ).fetchall()
        return tuple(
            CredentialReplayRecord(
                replay_id=UUID(row["replay_id"]),
                voting_context_reference=row["voting_context_reference"],
                reason_code=row["reason_code"],
                detected_at_bucket=datetime.fromisoformat(row["detected_at_bucket"]),
                timing_class=row["timing_class"],
            )
            for row in rows
        )


def record_revocation(
    connection: sqlite3.Connection,
    *,
    voting_credential_id: UUID,
    reason_code: str,
    revoked_at: datetime,
    authority_role: str,
    dual_control_reference: str | None,
) -> None:
    """Persist a revocation. The CHECK refuses one after the cutoff."""
    connection.execute(
        "INSERT OR REPLACE INTO credential_revocation (voting_credential_id, reason_code, "
        "revoked_at, authority_role, dual_control_reference, before_cutoff) "
        "VALUES (?, ?, ?, ?, ?, 1)",
        (
            str(voting_credential_id),
            reason_code,
            revoked_at.isoformat(),
            authority_role,
            dual_control_reference,
        ),
    )
