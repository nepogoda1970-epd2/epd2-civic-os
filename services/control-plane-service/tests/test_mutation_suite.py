"""W11 — every mutation in the corpus must be detected.

Two properties are asserted, not one. A mutation must be detected *at all*, and
it must be detected by the check that is supposed to catch it — otherwise the
corpus would silently degrade into "something, somewhere, failed".
"""

from __future__ import annotations

import pytest
from epd2_control_plane_service.mutations import MUTATIONS, apply_and_detect
from epd2_control_plane_service.verification import CHECK_IDS, run_checks


def test_the_governed_baseline_passes_every_check() -> None:
    """The control case. Without it, a suite that fails everything would score
    a perfect mutation result."""
    failures = [(r.check_id, r.detail) for r in run_checks() if not r.passed]
    assert failures == []


def test_corpus_meets_the_required_minimum_size() -> None:
    assert len(MUTATIONS) >= 24
    assert len({m.mutation_id for m in MUTATIONS}) == len(MUTATIONS)


def test_corpus_covers_every_required_mutation_theme() -> None:
    titles = " | ".join(m.title.lower() for m in MUTATIONS)
    for theme in (
        "universal admin",
        "region scope check removed",
        "self-approval enabled",
        "quorum reduced",
        "commit-time reauthorization removed",
        "revoked authority accepted",
        "emergency expiry removed",
        "renewable forever",
        "service identity accepted as human",
        "audit event removed",
        "history overwritten",
        "mass-assigned",
        "coarse regional disable",
        "implicit bund takeover",
        "readable to an ordinary approver",
        "identifier added to control telemetry",
        "direct database mutation",
        "unsafe failure converted to success",
        "stale evidence",
        "candidate changed after verification",
        "route absent from the inventory",
        "undocumented mutation endpoint",
        "package/freeze mismatch",
        "preseal state changed to accepted",
    ):
        assert theme in titles, f"uncovered mutation theme: {theme}"


@pytest.mark.parametrize("mutation", MUTATIONS, ids=[m.mutation_id for m in MUTATIONS])
def test_mutation_is_detected(mutation) -> None:  # type: ignore[no-untyped-def]
    outcome = apply_and_detect(mutation)
    assert outcome.detected, f"{mutation.mutation_id} ({mutation.title}) was NOT detected"
    assert outcome.caught_by_expected, (
        f"{mutation.mutation_id} was detected, but not by {mutation.expected_check}; "
        f"failing checks were {outcome.failing_checks}"
    )


def test_every_check_has_a_stable_id() -> None:
    from epd2_control_plane_service.verification import CHECKS

    assert {c.__name__ for c in CHECKS} == set(CHECK_IDS)
    assert len(set(CHECK_IDS.values())) == len(CHECK_IDS)


def test_every_check_is_exercised_by_at_least_one_mutation() -> None:
    """A check no mutation can break is a check that proves nothing."""
    exercised: set[str] = set()
    for mutation in MUTATIONS:
        exercised.update(apply_and_detect(mutation).failing_checks)
    unexercised = sorted(set(CHECK_IDS.values()) - exercised)
    assert unexercised == [], f"checks never exercised by any mutation: {unexercised}"
