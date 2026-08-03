"""Deterministic scenario helpers for the PACK-16D harness (§39, §58).

Everything here is deterministic. No test in this suite depends on wall
clock, on the OS CSPRNG, or on the order in which pytest happens to
collect it.
"""

from __future__ import annotations

from dataclasses import dataclass

from epd2_voting_service.reference.casting.ballot import (
    BallotEnvelope,
    BallotOpening,
    encrypt_ballot,
)
from epd2_voting_service.reference.crypto.parameters import ParameterSet
from epd2_voting_service.reference.election_record.builder import (
    ElectionRecord,
    GuardianShare,
    ReconciliationRecord,
    reconcile,
    tally_accepted,
    tally_accepted_threshold,
)
from epd2_voting_service.reference.guardians.ceremony import (
    CeremonyTranscript,
    GuardianSecret,
)
from epd2_voting_service.reference.guardians.threshold import ThresholdShare
from epd2_voting_service.reference.publication.bulletin_board import EntryType
from epd2_voting_service.reference.publication.sealed_batches import (
    BatchOpening,
    SealedBatch,
)
from epd2_voting_service.reference.publication.sealing import seal_batch
from epd2_voting_service.reference.testing.fixtures import (
    Fixture,
    deterministic_source,
    fixture_a,
)


def make_ballot(
    fixture: Fixture,
    selections: dict[str, tuple[str, ...]],
    seed: bytes,
    style: str | None = None,
) -> tuple[BallotEnvelope, BallotOpening]:
    """Encrypt one ballot from a named seed, so the result is reproducible."""
    style_id = style or fixture.manifest.ballot_styles[0].ballot_style_id
    return encrypt_ballot(
        fixture.manifest,
        style_id,
        selections,
        fixture.public_key,
        fixture.params,
        fixture.base_hash,
        deterministic_source(seed),
    )


@dataclass(frozen=True, slots=True)
class ClosedElection:
    fixture: Fixture
    batches: tuple[SealedBatch, ...]
    openings: tuple[BatchOpening, ...]
    accepted: tuple[BallotEnvelope, ...]
    spoiled: tuple[BallotEnvelope, ...]
    reconciliation: ReconciliationRecord
    record: ElectionRecord


def close_and_build(
    fixture: Fixture,
    accepted: list[BallotEnvelope],
    spoiled: list[BallotEnvelope],
    *,
    seed: bytes = b"close",
    ceremony: CeremonyTranscript | None = None,
    secrets: tuple[GuardianSecret, ...] = (),
    quorum_selection: tuple[int, ...] | None = None,
) -> ClosedElection:
    """Seal, publish, close, tally and reconcile — the ordinary happy path.

    The order is load-bearing: the batch is sealed and its commitment
    published *before* closure; the opening, reconciliation and every tally
    artefact are published only after. Reversing any of that is what the
    no-intermediate-tally tests attack.
    """
    source = deterministic_source(seed)
    batch, opening = seal_batch(
        fixture.store,
        election_context_id=fixture.manifest.election_context_id,
        batch_sequence=fixture.runtime.batch_sequence,
        batch_window_id=fixture.runtime.batch_window_id,
        capacity=fixture.runtime.batch_capacity,
        capacity_profile_id="test-capacity-profile",
        source=source,
    )
    board = fixture.board
    board.append(EntryType.ELECTION_MANIFEST, fixture.manifest.canonical_bytes())
    board.append(EntryType.PARAMETER_SET, fixture.params.canonical_bytes())
    board.publish_checkpoint()
    board.append(EntryType.SEALED_BATCH_COMMITMENT, batch.canonical_bytes())
    board.publish_checkpoint()
    board.close()
    board.append(EntryType.SEALED_BATCH_OPENING, opening.recompute_root())
    board.publish_checkpoint()

    threshold_shares: list[ThresholdShare] = []
    shares: list[GuardianShare] = []
    if ceremony is not None:
        tallies, threshold_shares = tally_accepted_threshold(
            accepted,
            fixture.manifest,
            fixture.params,
            ceremony,
            secrets,
            source,
            board_closed=board.closed,
            quorum_selection=quorum_selection,
        )
    else:
        tallies, shares = tally_accepted(
            accepted,
            fixture.manifest,
            fixture.params,
            fixture.secret,
            fixture.public_key,
            source,
            board_closed=board.closed,
        )
    reconciliation = reconcile([opening], accepted, spoiled, fixture.plan.max_valid_continuations)
    record = ElectionRecord(
        manifest=fixture.manifest,
        params=fixture.params,
        joint_public_key=fixture.public_key,
        base_hash=fixture.base_hash,
        sealed_batches=(batch,),
        batch_openings=(opening,),
        accepted_ballots=tuple(accepted),
        spoiled_ballots=tuple(spoiled),
        reconciliation=reconciliation,
        tallies=tuple(tallies),
        shares=tuple(shares),
        ceremony=ceremony,
        threshold_shares=tuple(threshold_shares),
    )
    return ClosedElection(
        fixture=fixture,
        batches=(batch,),
        openings=(opening,),
        accepted=tuple(accepted),
        spoiled=tuple(spoiled),
        reconciliation=reconciliation,
        record=record,
    )


def small_fixture(params: ParameterSet | None = None) -> Fixture:
    return fixture_a(params)
