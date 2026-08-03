"""Deterministic election fixtures (PACK-16D §39).

**TEST PROFILE ONLY. NOT PRODUCTION DEFAULTS.** Every numeric value here
is chosen to make a test fast and reproducible, never to suggest what a
real election should use.
"""

from __future__ import annotations

import dataclasses
import os
from dataclasses import dataclass

from epd2_voting_service.reference.casting.ballot import (
    BallotStyle,
    ContestDefinition,
    Manifest,
)
from epd2_voting_service.reference.casting.continuation import ContinuationState
from epd2_voting_service.reference.casting.store import ReferenceStore
from epd2_voting_service.reference.casting.transactions import ElectionRuntime
from epd2_voting_service.reference.crypto.parameters import (
    ParameterSet,
    load_profile,
    load_target_profile,
)
from epd2_voting_service.reference.crypto.randomness import (
    TEST_PROFILE_ENV,
    DeterministicTestRandomSource,
    RandomSource,
)
from epd2_voting_service.reference.guardians.ceremony import (
    CeremonyTranscript,
    GuardianSecret,
)
from epd2_voting_service.reference.publication.bulletin_board import BulletinBoard
from epd2_voting_service.reference.publication.capacity import CapacityPlan

TEST_PROFILE_BANNER = "TEST PROFILE ONLY - NOT A PRODUCTION DEFAULT"

_PARAM_CACHE: dict[str, ParameterSet] = {}


def enable_test_profile() -> None:
    """Test-only guard flag. Never set by production code."""
    os.environ[TEST_PROFILE_ENV] = "1"


def deterministic_source(seed: bytes = b"epd2-pack-16d") -> RandomSource:
    enable_test_profile()
    return DeterministicTestRandomSource(seed, allow_in_test=True)


def target_params() -> ParameterSet:
    """`EPD2-CRYPTO-1` — the real ElectionGuard 2.1 family.

    Cached because full validation costs about four seconds: primality of a
    4096-bit prime is not free. The cache holds a *validated* object, so
    nothing here skips a check; it skips repeating one.
    """
    if "target" not in _PARAM_CACHE:
        _PARAM_CACHE["target"] = load_target_profile()
    return _PARAM_CACHE["target"]


def small_params() -> ParameterSet:
    if "small" not in _PARAM_CACHE:
        _PARAM_CACHE["small"] = load_profile("EPD2-TESTONLY-NOTCONFORMANT-P1024-Q160")
    return _PARAM_CACHE["small"]


def production_shaped_params() -> ParameterSet:
    """4096/256, same shape as `EPD2-CRYPTO-1`; not those constants."""
    if "large" not in _PARAM_CACHE:
        _PARAM_CACHE["large"] = load_profile(
            "EPD2-TESTONLY-NOTCONFORMANT-P4096-Q256", check_primality=False
        )
    return _PARAM_CACHE["large"]


@dataclass(frozen=True, slots=True)
class Fixture:
    name: str
    manifest: Manifest
    params: ParameterSet
    secret: int
    public_key: int
    base_hash: bytes
    plan: CapacityPlan
    runtime: ElectionRuntime
    store: ReferenceStore
    board: BulletinBoard
    source: RandomSource
    capabilities: tuple[str, ...]


def _build(
    name: str,
    manifest: Manifest,
    params: ParameterSet,
    plan: CapacityPlan,
    capability_count: int,
    seed: bytes,
) -> Fixture:
    source = deterministic_source(seed)
    secret = 1 + source.random_below(params.q - 1)
    public_key = pow(params.g, secret, params.p)
    base_hash = manifest.digest()
    store = ReferenceStore()
    capabilities = tuple(f"cap-{name}-{i}" for i in range(capability_count))
    for reference in capabilities:
        store.continuations[reference] = ContinuationState(
            capability_reference=reference,
            election_context_id=manifest.election_context_id,
        )
    board = BulletinBoard(
        election_context_id=manifest.election_context_id, signing_key=b"test-board-key"
    )
    runtime = ElectionRuntime(
        manifest=manifest,
        params=params,
        public_key=public_key,
        base_hash=base_hash,
        plan=plan.validate(),
        batch_sequence=0,
        batch_window_id="w0",
        batch_capacity=plan.primary_capacity,
    )
    return Fixture(
        name=name,
        manifest=manifest,
        params=params,
        secret=secret,
        public_key=public_key,
        base_hash=base_hash,
        plan=plan,
        runtime=runtime,
        store=store,
        board=board,
        source=source,
        capabilities=capabilities,
    )


def fixture_a(params: ParameterSet | None = None) -> Fixture:
    """Minimal valid election: one contest, two selections."""
    manifest = Manifest(
        election_context_id="fixture-a",
        ballot_styles=(
            BallotStyle(
                ballot_style_id="style-a",
                contests=(
                    ContestDefinition(
                        contest_id="c1", option_ids=("opt-1", "opt-2"), selection_limit=1
                    ),
                ),
            ),
        ),
    )
    plan = CapacityPlan(
        election_context_id="fixture-a",
        max_valid_continuations=4,
        interval_count=1,
        primary_capacity=16,
        reserve_capacity=8,
        reserve_commitments=1,
        cast_reserved_per_batch=8,
        challenge_reserved_per_batch=4,
        shared_reserve_per_batch=4,
        safety_reserve=2,
    )
    return _build("a", manifest, params or small_params(), plan, 4, b"fixture-a")


def fixture_b(params: ParameterSet | None = None) -> Fixture:
    """Multi-contest election with undervote and a blank contest."""
    manifest = Manifest(
        election_context_id="fixture-b",
        ballot_styles=(
            BallotStyle(
                ballot_style_id="style-b",
                contests=(
                    ContestDefinition(
                        contest_id="c1",
                        option_ids=("a", "b", "c"),
                        selection_limit=2,
                    ),
                    ContestDefinition(contest_id="c2", option_ids=("yes", "no"), selection_limit=1),
                ),
            ),
        ),
    )
    plan = CapacityPlan(
        election_context_id="fixture-b",
        max_valid_continuations=6,
        interval_count=2,
        primary_capacity=16,
        reserve_capacity=8,
        reserve_commitments=1,
        cast_reserved_per_batch=8,
        challenge_reserved_per_batch=4,
        shared_reserve_per_batch=4,
        safety_reserve=0,
    )
    return _build("b", manifest, params or small_params(), plan, 6, b"fixture-b")


def fixture_c(params: ParameterSet | None = None) -> Fixture:
    """Capacity-incident fixture: capacity deliberately tiny."""
    manifest = Manifest(
        election_context_id="fixture-c",
        ballot_styles=(
            BallotStyle(
                ballot_style_id="style-c",
                contests=(
                    ContestDefinition(
                        contest_id="c1", option_ids=("opt-1", "opt-2"), selection_limit=1
                    ),
                ),
            ),
        ),
    )
    plan = CapacityPlan(
        election_context_id="fixture-c",
        max_valid_continuations=1,
        interval_count=1,
        primary_capacity=2,
        reserve_capacity=0,
        reserve_commitments=0,
        cast_reserved_per_batch=1,
        challenge_reserved_per_batch=1,
        shared_reserve_per_batch=0,
        safety_reserve=0,
    )
    return _build("c", manifest, params or small_params(), plan, 3, b"fixture-c")


@dataclass(frozen=True, slots=True)
class ThresholdFixture:
    """A fixture whose joint key comes from a real `k`-of-`n` ceremony.

    `fixture.public_key` is the ceremony's joint public key, so ballots
    encrypted against it can only be opened by a quorum. Nothing here holds
    a joint secret, because no party ever computes one.
    """

    fixture: Fixture
    ceremony: CeremonyTranscript
    secrets: tuple[GuardianSecret, ...]


def threshold_fixture(
    quorum: int = 3,
    guardian_count: int = 5,
    params: ParameterSet | None = None,
    seed: bytes = b"threshold-fixture",
) -> ThresholdFixture:
    from epd2_voting_service.reference.guardians.ceremony import (
        QuorumPolicy,
        run_ceremony,
    )

    base = fixture_a(params)
    result = run_ceremony(
        base.manifest.election_context_id,
        QuorumPolicy(quorum, guardian_count),
        base.params,
        deterministic_source(seed),
    )
    # `secret` is deliberately left at the single-guardian value and is
    # never used on this path: with a threshold key there is no single
    # secret, and a test that reached for one would be testing the wrong
    # thing.
    replaced = Fixture(
        name=base.name,
        manifest=base.manifest,
        params=base.params,
        secret=0,
        public_key=result.transcript.joint_public_key,
        base_hash=base.base_hash,
        plan=base.plan,
        # The runtime carries the key ballots are verified against, so it
        # must move to the joint key too. Leaving it behind would make the
        # transaction verify proofs against a key nobody encrypted to.
        runtime=dataclasses.replace(base.runtime, public_key=result.transcript.joint_public_key),
        store=base.store,
        board=base.board,
        source=base.source,
        capabilities=base.capabilities,
    )
    return ThresholdFixture(fixture=replaced, ceremony=result.transcript, secrets=result.secrets)
