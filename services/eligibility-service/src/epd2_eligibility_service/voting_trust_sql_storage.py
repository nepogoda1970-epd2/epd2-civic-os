"""Durable SQLite adapters for the PACK-15 identity side.

The default runtime binding. The in-memory adapters in
`voting_trust_storage.py` are test bindings, and
`tests/repository/test_pack15_default_binding.py` keeps that difference
real.

Two **separate database files**, because separation that depends on
nobody writing a JOIN is not separation (`OD-P15-01`, ADR-089):

* the eligibility database — cases, decisions, the participation-unit
  ledger. Identified, and identification stops here.
* the assertion-issuer database — assertions, the release queue, the
  one-time pickups, PACK-14 handoff acceptances. Carries no participant
  reference and no case reference at all.

A foreign key from an assertion to a case is therefore not expressible,
and neither file can hold a credential reference because no such
reference exists on this side of the boundary. The chain
`person -> assertion -> credential -> ballot` has no link here to walk.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from uuid import UUID

from epd2_core.sqlite_migrations import (
    MigrationDefinition,
    MigrationKind,
    open_migrated,
)
from epd2_eligibility_service.voting_attributes import AttributeKind, ScopedAttribute
from epd2_eligibility_service.voting_eligibility import (
    AssertionPickup,
    AssertionQueueEntry,
    AssertionStatus,
    EligibilityAssertion,
    EligibilityCase,
    EligibilityCriterion,
    EligibilityDecision,
    EligibilityDecisionReason,
    EligibilityDecisionStatus,
    EligibilityEvidenceReference,
    EligibilityRuleSetReference,
    ParticipationUnitLedgerEntry,
)
from epd2_eligibility_service.voting_handoff import HandoffAcceptance
from epd2_eligibility_service.voting_timing import CohortSizeClass

MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "migrations"
ELIGIBILITY_MIGRATIONS_DIR = MIGRATIONS_DIR / "eligibility"
ASSERTION_ISSUER_MIGRATIONS_DIR = MIGRATIONS_DIR / "assertion-issuer"

#: Expand-only: this round adds tables and indexes and drops nothing.
PACK15_ELIGIBILITY_MIGRATIONS: tuple[MigrationDefinition, ...] = (
    MigrationDefinition(
        identifier="p15-001-eligibility-cases",
        sequence=1,
        kind=MigrationKind.EXPAND,
        summary="Eligibility cases, decisions and the participation-unit ledger.",
        reversible=True,
    ),
)

PACK15_ASSERTION_ISSUER_MIGRATIONS: tuple[MigrationDefinition, ...] = (
    MigrationDefinition(
        identifier="p15-001-assertion-issuer",
        sequence=1,
        kind=MigrationKind.EXPAND,
        summary="Minimized assertions, the release queue and the one-time pickups.",
        reversible=True,
    ),
    MigrationDefinition(
        identifier="p15-002-handoff-acceptance",
        sequence=2,
        kind=MigrationKind.EXPAND,
        summary="PACK-14 handoff acceptance records, keyed on the artifact digest.",
        reversible=True,
    ),
)


def open_eligibility_database(database: str | Path, *, applied_at: datetime) -> sqlite3.Connection:
    """Open the identity-side eligibility database."""
    return open_migrated(
        database,
        PACK15_ELIGIBILITY_MIGRATIONS,
        ELIGIBILITY_MIGRATIONS_DIR,
        applied_at=applied_at,
    )


def open_assertion_issuer_database(
    database: str | Path, *, applied_at: datetime
) -> sqlite3.Connection:
    """Open the Assertion Issuer's own database.

    Deliberately a different path from `open_eligibility_database`. Passing
    the same path to both is refused by
    `assert_storage_boundaries_are_separate`.
    """
    return open_migrated(
        database,
        PACK15_ASSERTION_ISSUER_MIGRATIONS,
        ASSERTION_ISSUER_MIGRATIONS_DIR,
        applied_at=applied_at,
    )


class StorageBoundaryViolationError(RuntimeError):
    """The two identity-side stores were pointed at one database."""


def assert_storage_boundaries_are_separate(
    eligibility_database: str | Path, assertion_issuer_database: str | Path
) -> None:
    """Refuse a deployment that collapses the two storage boundaries.

    In-memory SQLite (`:memory:`) is refused for the same reason: two
    `:memory:` connections are two databases, but the string tells a
    reader nothing, and a shared-cache URI with the same name would be one
    database wearing two names.
    """
    left = str(eligibility_database)
    right = str(assertion_issuer_database)
    if left == right:
        raise StorageBoundaryViolationError(
            "the eligibility store and the Assertion Issuer store may not share a database"
        )
    if left != ":memory:" and right != ":memory:" and Path(left).resolve() == Path(right).resolve():
        raise StorageBoundaryViolationError(
            "the eligibility store and the Assertion Issuer store resolve to one file"
        )


def _iso(moment: datetime | None) -> str | None:
    return moment.isoformat() if moment is not None else None


def _parse(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


# ---------------------------------------------------------------------------
# Eligibility database
# ---------------------------------------------------------------------------


def _case_document(case: EligibilityCase) -> str:
    return json.dumps(
        {
            "scoped_attributes": [
                {
                    "name": attribute.name,
                    "kind": attribute.kind.value,
                    "predicate_value": attribute.predicate_value,
                    "enumeration_value": attribute.enumeration_value,
                    "scope_reference": attribute.scope_reference,
                    "bucket_value": attribute.bucket_value,
                    "source_owner": attribute.source_owner,
                    "source_version": attribute.source_version,
                }
                for attribute in case.scoped_attributes
            ],
            "evidence": [
                {
                    "evidence_reference": item.evidence_reference,
                    "evidence_class": item.evidence_class,
                    "referenced_at": item.referenced_at.isoformat(),
                }
                for item in case.evidence
            ],
        },
        sort_keys=True,
    )


@dataclass
class SqlEligibilityCaseStore:
    """Cases and decisions. Identified, and nothing here crosses over."""

    connection: sqlite3.Connection

    def save_case(self, case: EligibilityCase) -> None:
        self.connection.execute(
            """
            INSERT INTO eligibility_case (
                case_id, voting_context_reference, participant_reference,
                participation_class, status, requested_at, assisted_by, document
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(case_id) DO UPDATE SET
                status = excluded.status,
                assisted_by = excluded.assisted_by,
                document = excluded.document
            """,
            (
                str(case.case_id),
                case.voting_context_reference,
                case.participant_reference,
                case.participation_class,
                case.status.value,
                case.requested_at.isoformat(),
                case.assisted_by,
                _case_document(case),
            ),
        )

    def get_case(self, case_id: UUID) -> EligibilityCase | None:
        row = self.connection.execute(
            "SELECT * FROM eligibility_case WHERE case_id = ?", (str(case_id),)
        ).fetchone()
        if row is None:
            return None
        document = json.loads(row["document"])
        return EligibilityCase(
            case_id=UUID(row["case_id"]),
            voting_context_reference=row["voting_context_reference"],
            participant_reference=row["participant_reference"],
            participation_class=row["participation_class"],
            requested_at=datetime.fromisoformat(row["requested_at"]),
            status=EligibilityDecisionStatus(row["status"]),
            scoped_attributes=tuple(
                ScopedAttribute(
                    name=item["name"],
                    kind=AttributeKind(item["kind"]),
                    predicate_value=item["predicate_value"],
                    enumeration_value=item["enumeration_value"],
                    scope_reference=item["scope_reference"],
                    bucket_value=item["bucket_value"],
                    source_owner=item["source_owner"],
                    source_version=item["source_version"],
                )
                for item in document["scoped_attributes"]
            ),
            evidence=tuple(
                EligibilityEvidenceReference(
                    evidence_reference=item["evidence_reference"],
                    evidence_class=item["evidence_class"],
                    referenced_at=datetime.fromisoformat(item["referenced_at"]),
                )
                for item in document["evidence"]
            ),
            assisted_by=row["assisted_by"],
        )

    def save_decision(self, decision: EligibilityDecision) -> None:
        document = json.dumps(
            {
                "reasons": [
                    {
                        "reason_code": reason.reason_code,
                        "criterion": reason.criterion.value if reason.criterion else None,
                        "note": reason.note,
                    }
                    for reason in decision.reasons
                ],
                "declared_attribute_names": sorted(decision.rule_set.declared_attribute_names),
                "criteria": [criterion.value for criterion in decision.rule_set.criteria],
            },
            sort_keys=True,
        )
        self.connection.execute(
            """
            INSERT INTO eligibility_decision (
                decision_id, case_id, voting_context_reference, status,
                rule_set_reference, rule_set_version, eligibility_class,
                organizational_scope, required_assurance_satisfied, decided_at,
                valid_until, reason_codes, source_versions, document
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(decision_id) DO UPDATE SET
                status = excluded.status,
                reason_codes = excluded.reason_codes,
                document = excluded.document
            """,
            (
                str(decision.decision_id),
                str(decision.case_id),
                decision.voting_context_reference,
                decision.status.value,
                decision.rule_set.rule_set_id,
                decision.rule_set.rule_set_version,
                decision.eligibility_class,
                decision.organizational_scope,
                int(decision.required_assurance_satisfied),
                decision.decided_at.isoformat(),
                decision.valid_until.isoformat(),
                json.dumps([reason.reason_code for reason in decision.reasons]),
                json.dumps(dict(decision.source_versions), sort_keys=True),
                document,
            ),
        )

    def _decision(self, row: sqlite3.Row) -> EligibilityDecision:
        document = json.loads(row["document"])
        return EligibilityDecision(
            decision_id=UUID(row["decision_id"]),
            case_id=UUID(row["case_id"]),
            voting_context_reference=row["voting_context_reference"],
            status=EligibilityDecisionStatus(row["status"]),
            rule_set=EligibilityRuleSetReference(
                rule_set_id=row["rule_set_reference"],
                rule_set_version=row["rule_set_version"],
                declared_attribute_names=frozenset(document["declared_attribute_names"]),
                criteria=tuple(EligibilityCriterion(value) for value in document["criteria"]),
            ),
            source_versions=json.loads(row["source_versions"]),
            reasons=tuple(
                EligibilityDecisionReason(
                    reason_code=item["reason_code"],
                    criterion=(
                        EligibilityCriterion(item["criterion"]) if item["criterion"] else None
                    ),
                    note=item["note"],
                )
                for item in document["reasons"]
            ),
            eligibility_class=row["eligibility_class"],
            organizational_scope=row["organizational_scope"],
            required_assurance_satisfied=bool(row["required_assurance_satisfied"]),
            decided_at=datetime.fromisoformat(row["decided_at"]),
            valid_until=datetime.fromisoformat(row["valid_until"]),
        )

    def get_decision(self, decision_id: UUID) -> EligibilityDecision | None:
        row = self.connection.execute(
            "SELECT * FROM eligibility_decision WHERE decision_id = ?", (str(decision_id),)
        ).fetchone()
        return None if row is None else self._decision(row)

    def decisions_for_case(self, case_id: UUID) -> Sequence[EligibilityDecision]:
        rows = self.connection.execute(
            "SELECT * FROM eligibility_decision WHERE case_id = ? ORDER BY decided_at",
            (str(case_id),),
        ).fetchall()
        return tuple(self._decision(row) for row in rows)


@dataclass
class SqlParticipationUnitLedger:
    """One assertion per participation unit per voting context.

    The uniqueness is the composite primary key, so a concurrent second
    mint loses on the INSERT rather than on a prior read that raced.
    """

    connection: sqlite3.Connection

    def get(
        self, voting_context_reference: str, participation_unit_key: str
    ) -> ParticipationUnitLedgerEntry | None:
        row = self.connection.execute(
            "SELECT * FROM participation_unit_ledger "
            "WHERE voting_context_reference = ? AND participation_unit_key = ?",
            (voting_context_reference, participation_unit_key),
        ).fetchone()
        if row is None:
            return None
        return ParticipationUnitLedgerEntry(
            voting_context_reference=row["voting_context_reference"],
            participation_unit_key=row["participation_unit_key"],
            assertion_minted=bool(row["assertion_minted"]),
            minted_at=_parse(row["minted_at"]),
        )

    def put(self, entry: ParticipationUnitLedgerEntry) -> None:
        self.connection.execute(
            "INSERT INTO participation_unit_ledger (voting_context_reference, "
            "participation_unit_key, assertion_minted, minted_at) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(voting_context_reference, participation_unit_key) DO UPDATE SET "
            "assertion_minted = excluded.assertion_minted, minted_at = excluded.minted_at",
            (
                entry.voting_context_reference,
                entry.participation_unit_key,
                int(entry.assertion_minted),
                _iso(entry.minted_at),
            ),
        )

    def claim(self, entry: ParticipationUnitLedgerEntry) -> bool:
        """Atomically claim a participation unit. `False` if already claimed.

        This, and not `put`, is what the issuance path calls: the INSERT is
        the exactly-once check on the identity side of the split.
        """
        try:
            self.connection.execute(
                "INSERT INTO participation_unit_ledger (voting_context_reference, "
                "participation_unit_key, assertion_minted, minted_at) VALUES (?, ?, ?, ?)",
                (
                    entry.voting_context_reference,
                    entry.participation_unit_key,
                    int(entry.assertion_minted),
                    _iso(entry.minted_at),
                ),
            )
        except sqlite3.IntegrityError:
            return False
        return True

    def count_minted(self, voting_context_reference: str) -> int:
        row = self.connection.execute(
            "SELECT COUNT(*) AS n FROM participation_unit_ledger "
            "WHERE voting_context_reference = ? AND assertion_minted = 1",
            (voting_context_reference,),
        ).fetchone()
        return int(row["n"])


# ---------------------------------------------------------------------------
# Assertion Issuer database
# ---------------------------------------------------------------------------


@dataclass
class SqlAssertionIssuerStore:
    """The issuer's own boundary. No case, no participant, no credential."""

    connection: sqlite3.Connection

    def save_assertion(self, assertion: EligibilityAssertion) -> None:
        integrity: Mapping[str, str] = assertion.integrity_metadata
        self.connection.execute(
            """
            INSERT INTO eligibility_assertion (
                assertion_id, voting_context_reference, eligibility_result,
                eligibility_class, organizational_scope, required_assurance_satisfied,
                issued_at_bucket, expires_at, audience, purpose, nonce, status,
                integrity_algorithm, integrity_key_identifier, integrity_signature
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(assertion_id) DO UPDATE SET status = excluded.status
            """,
            (
                str(assertion.assertion_id),
                assertion.voting_context_reference,
                assertion.eligibility_result,
                assertion.eligibility_class,
                assertion.organizational_scope,
                int(assertion.required_assurance_satisfied),
                assertion.issued_at_bucket.isoformat(),
                assertion.expires_at.isoformat(),
                assertion.audience,
                assertion.purpose,
                assertion.nonce,
                assertion.status.value,
                integrity.get("algorithm", ""),
                integrity.get("key_identifier", ""),
                integrity.get("signature", ""),
            ),
        )

    def get_assertion(self, assertion_id: UUID) -> EligibilityAssertion | None:
        row = self.connection.execute(
            "SELECT * FROM eligibility_assertion WHERE assertion_id = ?", (str(assertion_id),)
        ).fetchone()
        if row is None:
            return None
        return EligibilityAssertion(
            assertion_id=UUID(row["assertion_id"]),
            voting_context_reference=row["voting_context_reference"],
            eligibility_result=row["eligibility_result"],
            eligibility_class=row["eligibility_class"],
            organizational_scope=row["organizational_scope"],
            required_assurance_satisfied=bool(row["required_assurance_satisfied"]),
            issued_at_bucket=datetime.fromisoformat(row["issued_at_bucket"]),
            expires_at=datetime.fromisoformat(row["expires_at"]),
            audience=row["audience"],
            purpose=row["purpose"],
            nonce=row["nonce"],
            status=AssertionStatus(row["status"]),
            integrity_metadata={
                "algorithm": row["integrity_algorithm"],
                "key_identifier": row["integrity_key_identifier"],
                "signature": row["integrity_signature"],
            },
        )

    def save_queue_entry(self, entry: AssertionQueueEntry) -> None:
        self.connection.execute(
            """
            INSERT INTO assertion_queue_entry (
                assertion_id, voting_context_reference, batch_reference, enqueued_at,
                release_not_before, cohort_wait_deadline, released_at, cohort_size_class,
                below_minimum_cohort
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(assertion_id) DO UPDATE SET
                released_at = excluded.released_at,
                cohort_size_class = excluded.cohort_size_class,
                below_minimum_cohort = excluded.below_minimum_cohort
            """,
            (
                str(entry.assertion_id),
                entry.voting_context_reference,
                entry.batch_reference,
                entry.enqueued_at.isoformat(),
                entry.release_not_before.isoformat(),
                entry.cohort_wait_deadline.isoformat(),
                _iso(entry.released_at),
                entry.cohort_size_class.value if entry.cohort_size_class else None,
                int(entry.below_minimum_cohort),
            ),
        )

    def _queue_entry(self, row: sqlite3.Row) -> AssertionQueueEntry:
        return AssertionQueueEntry(
            assertion_id=UUID(row["assertion_id"]),
            voting_context_reference=row["voting_context_reference"],
            batch_reference=row["batch_reference"],
            enqueued_at=datetime.fromisoformat(row["enqueued_at"]),
            release_not_before=datetime.fromisoformat(row["release_not_before"]),
            cohort_wait_deadline=datetime.fromisoformat(row["cohort_wait_deadline"]),
            released_at=_parse(row["released_at"]),
            cohort_size_class=(
                CohortSizeClass(row["cohort_size_class"]) if row["cohort_size_class"] else None
            ),
            below_minimum_cohort=bool(row["below_minimum_cohort"]),
        )

    def get_queue_entry(self, assertion_id: UUID) -> AssertionQueueEntry | None:
        row = self.connection.execute(
            "SELECT * FROM assertion_queue_entry WHERE assertion_id = ?", (str(assertion_id),)
        ).fetchone()
        return None if row is None else self._queue_entry(row)

    def pending_batch(self, batch_reference: str) -> Sequence[AssertionQueueEntry]:
        rows = self.connection.execute(
            "SELECT * FROM assertion_queue_entry WHERE batch_reference = ? "
            "AND released_at IS NULL ORDER BY release_not_before",
            (batch_reference,),
        ).fetchall()
        return tuple(self._queue_entry(row) for row in rows)

    def save_pickup(self, pickup: AssertionPickup) -> None:
        self.connection.execute(
            """
            INSERT INTO assertion_pickup (
                pickup_id, assertion_id, voting_context_reference, handoff_artifact_digest,
                audience_origin, created_at, expires_at, consumed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(pickup_id) DO UPDATE SET consumed_at = excluded.consumed_at
            """,
            (
                str(pickup.pickup_id),
                str(pickup.assertion_id),
                pickup.voting_context_reference,
                pickup.handoff_artifact_digest,
                pickup.audience_origin,
                pickup.created_at.isoformat(),
                pickup.expires_at.isoformat(),
                _iso(pickup.consumed_at),
            ),
        )

    def get_pickup_by_digest(self, handoff_artifact_digest: str) -> AssertionPickup | None:
        row = self.connection.execute(
            "SELECT * FROM assertion_pickup WHERE handoff_artifact_digest = ?",
            (handoff_artifact_digest,),
        ).fetchone()
        if row is None:
            return None
        return AssertionPickup(
            pickup_id=UUID(row["pickup_id"]),
            assertion_id=UUID(row["assertion_id"]),
            voting_context_reference=row["voting_context_reference"],
            handoff_artifact_digest=row["handoff_artifact_digest"],
            audience_origin=row["audience_origin"],
            created_at=datetime.fromisoformat(row["created_at"]),
            expires_at=datetime.fromisoformat(row["expires_at"]),
            consumed_at=_parse(row["consumed_at"]),
        )

    def consume_pickup(self, pickup_id: UUID, *, consumed_at: datetime) -> bool:
        """Consume a pickup exactly once.

        The `consumed_at IS NULL` predicate is part of the UPDATE, so two
        concurrent pickups produce one row change and one `False`.
        """
        cursor = self.connection.execute(
            "UPDATE assertion_pickup SET consumed_at = ? "
            "WHERE pickup_id = ? AND consumed_at IS NULL",
            (consumed_at.isoformat(), str(pickup_id)),
        )
        return int(cursor.rowcount) == 1


@dataclass
class SqlHandoffAcceptanceStore:
    """Single-use handoff acceptance, keyed on the artifact's digest."""

    connection: sqlite3.Connection

    def record(self, acceptance: HandoffAcceptance) -> None:
        self.connection.execute(
            """
            INSERT INTO voting_handoff_acceptance (
                artifact_digest, acceptance_id, voting_context_reference,
                audience, origin, accepted_at, consumed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                acceptance.artifact_digest,
                str(acceptance.acceptance_id),
                acceptance.voting_context_reference,
                acceptance.audience,
                acceptance.origin,
                acceptance.accepted_at.isoformat(),
                _iso(acceptance.consumed_at),
            ),
        )

    def accept_once(self, acceptance: HandoffAcceptance) -> bool:
        """`False` when the artifact has already been presented."""
        try:
            self.record(acceptance)
        except sqlite3.IntegrityError:
            return False
        return True

    def get(self, artifact_digest: str) -> HandoffAcceptance | None:
        row = self.connection.execute(
            "SELECT * FROM voting_handoff_acceptance WHERE artifact_digest = ?",
            (artifact_digest,),
        ).fetchone()
        if row is None:
            return None
        return HandoffAcceptance(
            acceptance_id=UUID(row["acceptance_id"]),
            artifact_digest=row["artifact_digest"],
            voting_context_reference=row["voting_context_reference"],
            audience=row["audience"],
            origin=row["origin"],
            accepted_at=datetime.fromisoformat(row["accepted_at"]),
            consumed_at=_parse(row["consumed_at"]),
        )
