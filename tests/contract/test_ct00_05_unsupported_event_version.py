"""CT-00-05 Unsupported Event Version (canon section 27): an unknown
major version is never processed."""

from __future__ import annotations

import pytest

from epd2_audit_core.storage import InMemoryAuditEventStore
from epd2_core.clock import FixedClock
from epd2_core.event_envelope import (
    ActorRef,
    UnsupportedEventVersionError,
    assert_supported_major_version,
)
from epd2_credential_service.events import SUPPORTED_MAJOR_VERSIONS as CREDENTIAL_MAJORS

# --- PACK-03 majors (added alongside the PACK-02 majors above) -------------
from epd2_delegation_service.events import SUPPORTED_MAJOR_VERSIONS as DELEGATION_MAJORS
from epd2_deliberation_service.events import SUPPORTED_MAJOR_VERSIONS as DELIBERATION_MAJORS
from epd2_eligibility_service.events import SUPPORTED_MAJOR_VERSIONS as ELIGIBILITY_MAJORS
from epd2_identity_service.events import SUPPORTED_MAJOR_VERSIONS as IDENTITY_MAJORS
from epd2_initiative_service.events import SUPPORTED_MAJOR_VERSIONS as INITIATIVE_MAJORS
from epd2_moderation_service.events import SUPPORTED_MAJOR_VERSIONS as MODERATION_MAJORS
from epd2_tally_service.events import SUPPORTED_MAJOR_VERSIONS as TALLY_MAJORS
from epd2_voting_service.events import SUPPORTED_MAJOR_VERSIONS as VOTING_MAJORS
from epd2_voting_service.storage import InMemoryBallotStore


@pytest.mark.parametrize(
    "supported_majors",
    [
        CREDENTIAL_MAJORS,
        ELIGIBILITY_MAJORS,
        IDENTITY_MAJORS,
        DELEGATION_MAJORS,
        DELIBERATION_MAJORS,
        INITIATIVE_MAJORS,
        MODERATION_MAJORS,
        TALLY_MAJORS,
        VOTING_MAJORS,
        frozenset({1}),
    ],
)
def test_unsupported_major_version_is_rejected(supported_majors: frozenset[int]) -> None:
    with pytest.raises(UnsupportedEventVersionError):
        assert_supported_major_version("99.0", supported_majors)


def test_supported_major_version_passes() -> None:
    assert_supported_major_version("1.0", frozenset({1}))


def test_malformed_event_version_is_rejected() -> None:
    from epd2_core.event_envelope import InvalidEventEnvelopeError, parse_major_version

    with pytest.raises(InvalidEventEnvelopeError):
        parse_major_version("not-a-version")


def test_real_pack03_ballot_opened_envelope_rejects_an_unsupported_major_version(
    ballot_store: InMemoryBallotStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    """Exercises `assert_supported_major_version` against a real PACK-03
    event envelope's own `event_version` (a `ballot.created` envelope,
    voting-service) - the envelope's actual major (1) is accepted against
    its own service's `SUPPORTED_MAJOR_VERSIONS`, but rejected against a
    frozenset that does not contain it (mirroring the same shape as
    `test_unsupported_major_version_is_rejected` above, but against a real,
    service-produced envelope rather than a synthetic version string)."""
    from datetime import timedelta
    from uuid import uuid4

    from epd2_voting_service.application import create_ballot
    from epd2_voting_service.domain import BallotMethod

    result = create_ballot(
        ballot_store,
        audit_store,
        ballot_id=uuid4(),
        space_id=uuid4(),
        subject_type="initiative",
        subject_id=uuid4(),
        question="Shall this pass?",
        ballot_method=BallotMethod.YES_NO,
        secrecy_mode="secret",
        eligibility_rule_version=1,
        delegation_policy_version=1,
        quorum_rule="none",
        threshold_rule="simple_majority",
        opens_at=clock.now(),
        closes_at=clock.now() + timedelta(days=1),
        challenge_window_hours=None,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    envelope = result.event
    assert envelope is not None

    # Accepted against the real, matching major version set.
    assert_supported_major_version(envelope.event_version, VOTING_MAJORS)

    # Rejected against a frozenset that deliberately excludes it.
    with pytest.raises(UnsupportedEventVersionError):
        assert_supported_major_version(envelope.event_version, frozenset({99}))
