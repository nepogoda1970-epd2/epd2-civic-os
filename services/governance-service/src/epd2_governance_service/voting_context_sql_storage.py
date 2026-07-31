"""Durable SQLite adapter for the PACK-15 voting context registry.

The default runtime binding; `InMemoryVotingContextStore` in
`voting_contexts.py` is the test binding.

The registry is administrative configuration and nothing else. It has no
column for a participant, an assertion, a credential, a ballot or a
turnout figure, so a read of this database yields no fact about any
person - which is what makes it safe for the eligibility side to read
(ADR-089 forbids the reverse edge, not this one).

Versions are immutable: `voting_context` is keyed on
`(voting_context_reference, version)` and a change writes a new row.
`activation_snapshot_digest` is what makes "the critical parameters were
frozen at activation" checkable rather than asserted.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from uuid import UUID

from epd2_core.sqlite_migrations import (
    MigrationDefinition,
    MigrationKind,
    open_migrated,
)
from epd2_governance_service.voting_contexts import (
    ActivationSnapshot,
    DisclosureControlProfile,
    VotingContext,
    VotingContextStatus,
    VotingType,
    VotingWindow,
)

MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "migrations"

PACK15_GOVERNANCE_MIGRATIONS: tuple[MigrationDefinition, ...] = (
    MigrationDefinition(
        identifier="p15-001-voting-context-registry",
        sequence=1,
        kind=MigrationKind.EXPAND,
        summary="The versioned voting context registry and its activation snapshot.",
        reversible=True,
    ),
)


def open_voting_context_registry(
    database: str | Path, *, applied_at: datetime
) -> sqlite3.Connection:
    return open_migrated(
        database, PACK15_GOVERNANCE_MIGRATIONS, MIGRATIONS_DIR, applied_at=applied_at
    )


class VotingContextVersionImmutableError(RuntimeError):
    """An existing (reference, version) row was written a second time.

    A registry whose versions can be edited in place cannot support a
    frozen rule set: the version someone voted under would change
    underneath them.
    """


@dataclass
class SqlVotingContextStore:
    connection: sqlite3.Connection

    def save(self, context: VotingContext) -> None:
        document = json.dumps(
            {
                "voting_context_id": str(context.voting_context_id),
                "activation_parameters": (
                    dict(context.activation_snapshot.parameters)
                    if context.activation_snapshot
                    else None
                ),
            },
            sort_keys=True,
        )
        try:
            self.connection.execute(
                """
                INSERT INTO voting_context (
                    voting_context_reference, version, voting_context_id, voting_type,
                    organizational_scope, status, voting_window_start, voting_window_end,
                    issuance_window_start, issuance_window_end, revocation_cutoff,
                    rule_set_reference, rule_set_version, required_assurance,
                    participation_class, privacy_profile, audit_profile,
                    disclosure_minimum_cell, small_electorate, per_scope_metrics_permitted,
                    eligible_population, activation_snapshot_digest, activation_captured_at,
                    document
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(voting_context_reference, version) DO UPDATE SET
                    status = excluded.status,
                    activation_snapshot_digest = excluded.activation_snapshot_digest,
                    activation_captured_at = excluded.activation_captured_at,
                    document = excluded.document
                WHERE voting_context.activation_snapshot_digest IS NULL
                """,
                (
                    context.voting_context_reference,
                    context.version,
                    str(context.voting_context_id),
                    context.voting_type.value,
                    context.organizational_scope,
                    context.status.value,
                    context.voting_window.starts_at.isoformat(),
                    context.voting_window.ends_at.isoformat(),
                    context.credential_issuance_window.starts_at.isoformat(),
                    context.credential_issuance_window.ends_at.isoformat(),
                    context.revocation_cutoff.isoformat(),
                    context.eligibility_rule_set_reference,
                    context.eligibility_rule_set_version,
                    context.required_assurance,
                    context.participation_class,
                    context.privacy_profile,
                    context.audit_profile,
                    context.disclosure_control.minimum_cell,
                    int(context.disclosure_control.small_electorate),
                    int(context.disclosure_control.per_scope_metrics_permitted),
                    context.eligible_population,
                    (
                        context.activation_snapshot.snapshot_digest
                        if context.activation_snapshot
                        else None
                    ),
                    (
                        context.activation_snapshot.captured_at.isoformat()
                        if context.activation_snapshot
                        else None
                    ),
                    document,
                ),
            )
        except sqlite3.IntegrityError as error:  # pragma: no cover - defensive
            raise VotingContextVersionImmutableError(str(error)) from error

    def _context(self, row: sqlite3.Row) -> VotingContext:
        document = json.loads(row["document"])
        snapshot: ActivationSnapshot | None = None
        if row["activation_snapshot_digest"]:
            snapshot = ActivationSnapshot(
                snapshot_digest=row["activation_snapshot_digest"],
                captured_at=datetime.fromisoformat(row["activation_captured_at"]),
                parameters=document["activation_parameters"] or {},
            )
        return VotingContext(
            voting_context_id=UUID(row["voting_context_id"]),
            voting_context_reference=row["voting_context_reference"],
            version=int(row["version"]),
            voting_type=VotingType(row["voting_type"]),
            organizational_scope=row["organizational_scope"],
            status=VotingContextStatus(row["status"]),
            voting_window=VotingWindow(
                starts_at=datetime.fromisoformat(row["voting_window_start"]),
                ends_at=datetime.fromisoformat(row["voting_window_end"]),
            ),
            credential_issuance_window=VotingWindow(
                starts_at=datetime.fromisoformat(row["issuance_window_start"]),
                ends_at=datetime.fromisoformat(row["issuance_window_end"]),
            ),
            revocation_cutoff=datetime.fromisoformat(row["revocation_cutoff"]),
            eligibility_rule_set_reference=row["rule_set_reference"],
            eligibility_rule_set_version=row["rule_set_version"],
            required_assurance=row["required_assurance"],
            participation_class=row["participation_class"],
            privacy_profile=row["privacy_profile"],
            audit_profile=row["audit_profile"],
            disclosure_control=DisclosureControlProfile(
                minimum_cell=int(row["disclosure_minimum_cell"]),
                small_electorate=bool(row["small_electorate"]),
                per_scope_metrics_permitted=bool(row["per_scope_metrics_permitted"]),
            ),
            eligible_population=int(row["eligible_population"]),
            activation_snapshot=snapshot,
        )

    def get(self, voting_context_reference: str, version: int) -> VotingContext | None:
        row = self.connection.execute(
            "SELECT * FROM voting_context WHERE voting_context_reference = ? AND version = ?",
            (voting_context_reference, version),
        ).fetchone()
        return None if row is None else self._context(row)

    def latest(self, voting_context_reference: str) -> VotingContext | None:
        row = self.connection.execute(
            "SELECT * FROM voting_context WHERE voting_context_reference = ? "
            "ORDER BY version DESC LIMIT 1",
            (voting_context_reference,),
        ).fetchone()
        return None if row is None else self._context(row)

    def versions(self, voting_context_reference: str) -> tuple[VotingContext, ...]:
        rows = self.connection.execute(
            "SELECT * FROM voting_context WHERE voting_context_reference = ? ORDER BY version",
            (voting_context_reference,),
        ).fetchall()
        return tuple(self._context(row) for row in rows)
