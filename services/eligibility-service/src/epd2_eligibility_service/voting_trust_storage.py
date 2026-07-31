"""Storage ports for the PACK-15 voting-trust service.

Protocol ports plus in-memory **test** adapters, following the repository's
existing `storage.py` shape. The durable adapters are
`voting_trust_sql_storage.py`; `voting_trust_runtime.py` binds those, never
these (asserted by `tests/repository/test_pack15_default_binding.py`).

Two storage boundaries are separate on purpose (`OD-P15-01`, ADR-089):

* the **eligibility** stores (cases, decisions, disputes, the
  participation-unit ledger), and
* the **assertion issuer** stores (assertions, the release queue, the
  one-time pickups, the issuer's own signing-key custody).

`AssertionIssuerStore` therefore never exposes a case, a participant or a
decision, and `EligibilityCaseStore` never exposes an assertion. Neither
exposes a credential: no store in this service can, because no credential
reference exists in this service at all.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Protocol
from uuid import UUID

from epd2_eligibility_service.voting_eligibility import (
    AssertionPickup,
    AssertionQueueEntry,
    EligibilityAssertion,
    EligibilityCase,
    EligibilityDecision,
    ParticipationUnitLedgerEntry,
)
from epd2_eligibility_service.voting_handoff import HandoffAcceptance


class EligibilityCaseStore(Protocol):
    def save_case(self, case: EligibilityCase) -> None: ...

    def get_case(self, case_id: UUID) -> EligibilityCase | None: ...

    def save_decision(self, decision: EligibilityDecision) -> None: ...

    def get_decision(self, decision_id: UUID) -> EligibilityDecision | None: ...

    def decisions_for_case(self, case_id: UUID) -> Sequence[EligibilityDecision]: ...


class ParticipationUnitLedger(Protocol):
    """One assertion per participation unit per voting context.

    Records *that* an assertion was minted, never *which one*.
    """

    def get(
        self, voting_context_reference: str, participation_unit_key: str
    ) -> ParticipationUnitLedgerEntry | None: ...

    def put(self, entry: ParticipationUnitLedgerEntry) -> None: ...


class AssertionIssuerStore(Protocol):
    """The Assertion Issuer's own storage boundary.

    No shared schema, transaction or connection with the eligibility
    stores above.
    """

    def save_assertion(self, assertion: EligibilityAssertion) -> None: ...

    def get_assertion(self, assertion_id: UUID) -> EligibilityAssertion | None: ...

    def save_queue_entry(self, entry: AssertionQueueEntry) -> None: ...

    def get_queue_entry(self, assertion_id: UUID) -> AssertionQueueEntry | None: ...

    def pending_batch(self, batch_reference: str) -> Sequence[AssertionQueueEntry]: ...

    def save_pickup(self, pickup: AssertionPickup) -> None: ...

    def get_pickup_by_digest(self, handoff_artifact_digest: str) -> AssertionPickup | None: ...


class HandoffAcceptanceStore(Protocol):
    def record(self, acceptance: HandoffAcceptance) -> None: ...

    def get(self, artifact_digest: str) -> HandoffAcceptance | None: ...


# ---------------------------------------------------------------------------
# In-memory reference adapters (test bindings)
# ---------------------------------------------------------------------------


class InMemoryEligibilityCaseStore:
    def __init__(self) -> None:
        self._cases: dict[UUID, EligibilityCase] = {}
        self._decisions: dict[UUID, EligibilityDecision] = {}

    def save_case(self, case: EligibilityCase) -> None:
        self._cases[case.case_id] = case

    def get_case(self, case_id: UUID) -> EligibilityCase | None:
        return self._cases.get(case_id)

    def save_decision(self, decision: EligibilityDecision) -> None:
        self._decisions[decision.decision_id] = decision

    def get_decision(self, decision_id: UUID) -> EligibilityDecision | None:
        return self._decisions.get(decision_id)

    def decisions_for_case(self, case_id: UUID) -> Sequence[EligibilityDecision]:
        return tuple(d for d in self._decisions.values() if d.case_id == case_id)


class InMemoryParticipationUnitLedger:
    def __init__(self) -> None:
        self._entries: dict[tuple[str, str], ParticipationUnitLedgerEntry] = {}

    def get(
        self, voting_context_reference: str, participation_unit_key: str
    ) -> ParticipationUnitLedgerEntry | None:
        return self._entries.get((voting_context_reference, participation_unit_key))

    def put(self, entry: ParticipationUnitLedgerEntry) -> None:
        self._entries[(entry.voting_context_reference, entry.participation_unit_key)] = entry


class InMemoryAssertionIssuerStore:
    def __init__(self) -> None:
        self._assertions: dict[UUID, EligibilityAssertion] = {}
        self._queue: dict[UUID, AssertionQueueEntry] = {}
        self._pickups: dict[str, AssertionPickup] = {}

    def save_assertion(self, assertion: EligibilityAssertion) -> None:
        self._assertions[assertion.assertion_id] = assertion

    def get_assertion(self, assertion_id: UUID) -> EligibilityAssertion | None:
        return self._assertions.get(assertion_id)

    def save_queue_entry(self, entry: AssertionQueueEntry) -> None:
        self._queue[entry.assertion_id] = entry

    def get_queue_entry(self, assertion_id: UUID) -> AssertionQueueEntry | None:
        return self._queue.get(assertion_id)

    def pending_batch(self, batch_reference: str) -> Sequence[AssertionQueueEntry]:
        return tuple(
            entry
            for entry in self._queue.values()
            if entry.batch_reference == batch_reference and entry.released_at is None
        )

    def save_pickup(self, pickup: AssertionPickup) -> None:
        self._pickups[pickup.handoff_artifact_digest] = pickup

    def get_pickup_by_digest(self, handoff_artifact_digest: str) -> AssertionPickup | None:
        return self._pickups.get(handoff_artifact_digest)


class InMemoryHandoffAcceptanceStore:
    def __init__(self) -> None:
        self._records: dict[str, HandoffAcceptance] = {}

    def record(self, acceptance: HandoffAcceptance) -> None:
        self._records[acceptance.artifact_digest] = acceptance

    def get(self, artifact_digest: str) -> HandoffAcceptance | None:
        return self._records.get(artifact_digest)


def assert_no_credential_reference(store_columns: Iterable[str]) -> None:
    """Refuse a storage schema that could hold a credential reference.

    Used by the persistence tests over the SQL adapters' column lists: the
    identity side may not hold a voting-side reference in any column, under
    any name (ADR-093).
    """
    forbidden = {
        "credential_id",
        "voting_credential_id",
        "credential_reference",
        "redemption_reference",
        "ballot_id",
    }
    offending = sorted(set(store_columns) & forbidden)
    if offending:
        raise ValueError(
            "an eligibility-side store may not carry a voting-side reference: "
            + ", ".join(offending)
        )
