"""Tests for epd2_voting_service.domain.

Covers every `ALLOWED_TRANSITIONS`-style pair (plus at least one
forbidden transition) for each of the four owned entities' status
machines, the CT-00-09 vote-linkability `FORBIDDEN_FIELD_NAMES`
guarantee on `VoteEnvelope`/`VoteReceipt`, and a positive-space
regression test that no code path in this service resolves a
`VoteEnvelope` back to an `Account`/`IdentityRecord`.
"""

from __future__ import annotations

import ast
import inspect
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest

from epd2_voting_service.domain import (
    ALLOWED_OPTION_TRANSITIONS,
    ALLOWED_RECEIPT_TRANSITIONS,
    ALLOWED_TRANSITIONS,
    ALLOWED_VOTE_ENVELOPE_TRANSITIONS,
    DEFAULT_CHALLENGE_WINDOW_HOURS,
    FORBIDDEN_FIELD_NAMES,
    Ballot,
    BallotMethod,
    BallotOption,
    BallotOptionStatus,
    BallotStatus,
    VoteEnvelope,
    VoteEnvelopeStatus,
    VoteReceipt,
    VoteReceiptVerificationStatus,
    compute_ballot_configuration_hash,
    compute_vote_envelope_integrity_hash,
    compute_vote_receipt_hash,
    configuration_fields,
    effective_challenge_window_hours,
    parse_ballot_option_status,
    parse_ballot_status,
    parse_vote_envelope_status,
    parse_vote_receipt_verification_status,
)
from epd2_voting_service.exceptions import (
    ForbiddenBallotOptionTransitionError,
    ForbiddenBallotTransitionError,
    ForbiddenVoteEnvelopeTransitionError,
    ForbiddenVoteReceiptTransitionError,
    UnknownBallotOptionStatusError,
    UnknownBallotStatusError,
    UnknownVoteEnvelopeStatusError,
    UnknownVoteReceiptStatusError,
)

_OPENS_AT = datetime(2026, 1, 1, tzinfo=UTC)
_CLOSES_AT = datetime(2026, 1, 8, tzinfo=UTC)


def _make_ballot(**overrides: object) -> Ballot:
    defaults: dict[str, object] = {
        "ballot_id": uuid4(),
        "space_id": uuid4(),
        "subject_type": "initiative",
        "subject_id": uuid4(),
        "question": "Should we adopt this proposal?",
        "ballot_method": BallotMethod.YES_NO,
        "secrecy_mode": "secret",
        "eligibility_rule_version": 1,
        "delegation_policy_version": 1,
        "quorum_rule": "simple_majority",
        "threshold_rule": "simple_majority",
        "opens_at": _OPENS_AT,
        "closes_at": _CLOSES_AT,
        "status": BallotStatus.DRAFT,
        "configuration_hash": None,
        "challenge_window_hours": None,
    }
    defaults.update(overrides)
    return Ballot(**defaults)  # type: ignore[arg-type]


def _make_option(**overrides: object) -> BallotOption:
    defaults: dict[str, object] = {
        "ballot_option_id": uuid4(),
        "ballot_id": uuid4(),
        "option_code": "yes",
        "label": "Yes",
        "description": "Vote in favor",
        "display_order": 0,
        "status": BallotOptionStatus.ACTIVE,
    }
    defaults.update(overrides)
    return BallotOption(**defaults)  # type: ignore[arg-type]


def _make_envelope(**overrides: object) -> VoteEnvelope:
    submitted_at = datetime(2026, 1, 2, tzinfo=UTC)
    integrity_hash = compute_vote_envelope_integrity_hash(
        ballot_id=overrides.get("ballot_id", uuid4()),  # type: ignore[arg-type]
        credential_proof=overrides.get("credential_proof", uuid4()),  # type: ignore[arg-type]
        encrypted_or_encoded_choice=overrides.get("encrypted_or_encoded_choice", "yes"),  # type: ignore[arg-type]
        submitted_at=submitted_at,
    )
    defaults: dict[str, object] = {
        "vote_envelope_id": uuid4(),
        "ballot_id": uuid4(),
        "credential_proof": uuid4(),
        "encrypted_or_encoded_choice": "yes",
        "submitted_at": submitted_at,
        "integrity_hash": integrity_hash,
        "validation_status": VoteEnvelopeStatus.RECEIVED,
        "included_in_tally": False,
    }
    defaults.update(overrides)
    return VoteEnvelope(**defaults)  # type: ignore[arg-type]


def _make_receipt(**overrides: object) -> VoteReceipt:
    defaults: dict[str, object] = {
        "receipt_id": uuid4(),
        "ballot_id": uuid4(),
        "vote_envelope_reference": uuid4(),
        "receipt_hash": "a" * 64,
        "issued_at": datetime(2026, 1, 2, tzinfo=UTC),
        "verification_status": VoteReceiptVerificationStatus.ISSUED,
    }
    defaults.update(overrides)
    return VoteReceipt(**defaults)  # type: ignore[arg-type]


# --- Ballot status machine ---------------------------------------------------


def test_parse_ballot_status_accepts_known_values() -> None:
    assert parse_ballot_status("open") == BallotStatus.OPEN


def test_parse_ballot_status_rejects_unknown_value() -> None:
    with pytest.raises(UnknownBallotStatusError):
        parse_ballot_status("super_open")


@pytest.mark.parametrize("current,target", sorted(ALLOWED_TRANSITIONS))
def test_every_allowed_ballot_transition_succeeds(
    current: BallotStatus, target: BallotStatus
) -> None:
    ballot = _make_ballot(status=current)
    updated = ballot.with_status(target)
    assert updated.status == target


def test_ballot_transition_closed_never_returns_to_open() -> None:
    """Explicit regression for the spec's own emphasis: `closed` must
    never return to `open`."""
    ballot = _make_ballot(status=BallotStatus.CLOSED)
    with pytest.raises(ForbiddenBallotTransitionError):
        ballot.with_status(BallotStatus.OPEN)


def test_ballot_transition_tallying_never_precedes_closed() -> None:
    ballot = _make_ballot(status=BallotStatus.OPEN)
    with pytest.raises(ForbiddenBallotTransitionError):
        ballot.with_status(BallotStatus.TALLYING)


def test_ballot_forbidden_transition_from_published() -> None:
    ballot = _make_ballot(status=BallotStatus.PUBLISHED)
    with pytest.raises(ForbiddenBallotTransitionError):
        ballot.with_status(BallotStatus.OPEN)


def test_ballot_invalidated_transition() -> None:
    """ADR-009 item 14 (amended): the domain/state-machine level has
    always supported `invalidated` (for CT-00-02/CT-00-03). PACK-05
    (ADR-017 Option B) adds the one narrow `application.invalidate_ballot`
    command that actually reaches it, gated on an approved
    `GovernanceDecision` read from `governance-service` - see
    `tests/test_application.py`'s `test_invalidate_ballot_*` tests."""
    ballot = _make_ballot(status=BallotStatus.DRAFT)
    updated = ballot.with_status(BallotStatus.INVALIDATED)
    assert updated.status == BallotStatus.INVALIDATED


def test_ballot_requires_timezone_aware_datetimes() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        _make_ballot(opens_at=datetime(2026, 1, 1))


def test_ballot_rejects_closes_at_before_opens_at() -> None:
    with pytest.raises(ValueError, match="closes_at"):
        _make_ballot(opens_at=_CLOSES_AT, closes_at=_OPENS_AT)


def test_effective_challenge_window_hours_defaults_to_72() -> None:
    ballot = _make_ballot(challenge_window_hours=None)
    assert effective_challenge_window_hours(ballot) == DEFAULT_CHALLENGE_WINDOW_HOURS == 72


def test_effective_challenge_window_hours_honors_override() -> None:
    ballot = _make_ballot(challenge_window_hours=48)
    assert effective_challenge_window_hours(ballot) == 48


def test_configuration_fields_uses_effective_challenge_window() -> None:
    ballot = _make_ballot(challenge_window_hours=None)
    fields = configuration_fields(ballot)
    assert fields[-1] == DEFAULT_CHALLENGE_WINDOW_HOURS


def test_compute_ballot_configuration_hash_is_deterministic() -> None:
    kwargs = dict(
        ballot_method=BallotMethod.YES_NO,
        secrecy_mode="secret",
        eligibility_rule_version=1,
        delegation_policy_version=1,
        quorum_rule="simple_majority",
        threshold_rule="simple_majority",
        opens_at=_OPENS_AT,
        closes_at=_CLOSES_AT,
        challenge_window_hours=72,
        eligibility_snapshot_digest="a" * 64,
    )
    a = compute_ballot_configuration_hash(**kwargs)  # type: ignore[arg-type]
    b = compute_ballot_configuration_hash(**kwargs)  # type: ignore[arg-type]
    assert a == b
    assert len(a) == 64


def test_compute_ballot_configuration_hash_changes_with_snapshot_digest() -> None:
    """The freeze is checked against a real `EligibilitySnapshot` digest,
    not a bare version number - two different snapshot digests for the
    same otherwise-identical configuration must hash differently."""
    kwargs = dict(
        ballot_method=BallotMethod.YES_NO,
        secrecy_mode="secret",
        eligibility_rule_version=1,
        delegation_policy_version=1,
        quorum_rule="simple_majority",
        threshold_rule="simple_majority",
        opens_at=_OPENS_AT,
        closes_at=_CLOSES_AT,
        challenge_window_hours=72,
    )
    a = compute_ballot_configuration_hash(eligibility_snapshot_digest="a" * 64, **kwargs)  # type: ignore[arg-type]
    b = compute_ballot_configuration_hash(eligibility_snapshot_digest="b" * 64, **kwargs)  # type: ignore[arg-type]
    assert a != b


# --- BallotOption status machine --------------------------------------------


def test_parse_ballot_option_status_rejects_unknown_value() -> None:
    with pytest.raises(UnknownBallotOptionStatusError):
        parse_ballot_option_status("half_locked")


@pytest.mark.parametrize("current,target", sorted(ALLOWED_OPTION_TRANSITIONS))
def test_every_allowed_ballot_option_transition_succeeds(
    current: BallotOptionStatus, target: BallotOptionStatus
) -> None:
    option = _make_option(status=current)
    updated = option.with_status(target)
    assert updated.status == target


def test_ballot_option_locked_never_returns_to_active() -> None:
    option = _make_option(status=BallotOptionStatus.LOCKED)
    with pytest.raises(ForbiddenBallotOptionTransitionError):
        option.with_status(BallotOptionStatus.ACTIVE)


def test_ballot_option_abstain_is_an_ordinary_option_row() -> None:
    """ADR-009 item 3: abstention has no special-cased field or branch -
    it is just an option with `option_code == "abstain"`."""
    option = _make_option(option_code="abstain", label="Abstain")
    assert option.option_code == "abstain"
    assert option.status == BallotOptionStatus.ACTIVE


# --- VoteEnvelope status machine + vote linkability --------------------------


def test_parse_vote_envelope_status_rejects_unknown_value() -> None:
    with pytest.raises(UnknownVoteEnvelopeStatusError):
        parse_vote_envelope_status("half_received")


@pytest.mark.parametrize("current,target", sorted(ALLOWED_VOTE_ENVELOPE_TRANSITIONS))
def test_every_allowed_vote_envelope_transition_succeeds(
    current: VoteEnvelopeStatus, target: VoteEnvelopeStatus
) -> None:
    envelope = _make_envelope(validation_status=current)
    updated = envelope.with_status(target)
    assert updated.validation_status == target


def test_vote_envelope_forbidden_transition_received_to_included() -> None:
    envelope = _make_envelope(validation_status=VoteEnvelopeStatus.RECEIVED)
    with pytest.raises(ForbiddenVoteEnvelopeTransitionError):
        envelope.with_status(VoteEnvelopeStatus.INCLUDED)


def test_vote_envelope_forbidden_transition_rejected_is_terminal() -> None:
    envelope = _make_envelope(validation_status=VoteEnvelopeStatus.REJECTED)
    with pytest.raises(ForbiddenVoteEnvelopeTransitionError):
        envelope.with_status(VoteEnvelopeStatus.VALIDATED)


def test_vote_envelope_included_in_tally_tracks_included_status() -> None:
    envelope = _make_envelope(validation_status=VoteEnvelopeStatus.VALIDATED)
    included = envelope.with_status(VoteEnvelopeStatus.INCLUDED)
    assert included.included_in_tally is True


def test_vote_envelope_validated_to_superseded_clears_included_in_tally() -> None:
    envelope = _make_envelope(validation_status=VoteEnvelopeStatus.VALIDATED)
    superseded = envelope.with_status(VoteEnvelopeStatus.SUPERSEDED)
    assert superseded.included_in_tally is False


def test_vote_envelope_has_no_forbidden_identity_field() -> None:
    """CT-00-09 (Vote Linkability): the structural precondition."""
    field_names = set(VoteEnvelope.__dataclass_fields__)
    assert not (field_names & FORBIDDEN_FIELD_NAMES)
    assert "account_id" not in field_names
    assert "identity_record_id" not in field_names


def test_vote_receipt_has_no_forbidden_identity_field() -> None:
    """A `VoteReceipt` must be exactly as identity-free as the envelope
    it proves inclusion for."""
    field_names = set(VoteReceipt.__dataclass_fields__)
    assert not (field_names & FORBIDDEN_FIELD_NAMES)


def test_vote_envelope_credential_proof_is_not_named_like_an_account_reference() -> None:
    """`credential_proof` must reference a `ParticipationCredential`,
    never an `account_id` (spec's own required wording)."""
    field_names = set(VoteEnvelope.__dataclass_fields__)
    assert "credential_proof" in field_names
    assert "account_id" not in field_names


def test_no_code_path_resolves_a_vote_envelope_to_an_account() -> None:
    """Positive-space regression: no function in this service's own
    `domain.py`/`application.py` ever accepts or returns anything typed
    `Account`/`IdentityRecord`, and neither `epd2_account_service` nor
    `epd2_identity_service` is imported anywhere in this package's
    source. Walks the actual source ASTs rather than trusting docstrings.
    """
    import epd2_voting_service

    package_dir = Path(inspect.getfile(epd2_voting_service)).parent
    forbidden_modules = {"epd2_account_service", "epd2_identity_service"}
    forbidden_names = {"Account", "IdentityRecord"}

    for py_file in package_dir.glob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name.split(".")[0] not in forbidden_modules, (
                        f"{py_file.name} imports forbidden module {alias.name!r}"
                    )
            elif isinstance(node, ast.ImportFrom):
                assert node.module is not None
                assert node.module.split(".")[0] not in forbidden_modules, (
                    f"{py_file.name} imports from forbidden module {node.module!r}"
                )
                for alias in node.names:
                    assert alias.name not in forbidden_names, (
                        f"{py_file.name} imports forbidden name {alias.name!r}"
                    )


def test_compute_vote_envelope_integrity_hash_is_deterministic() -> None:
    kwargs = dict(
        ballot_id=uuid4(),
        credential_proof=uuid4(),
        encrypted_or_encoded_choice="yes",
        submitted_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    a = compute_vote_envelope_integrity_hash(**kwargs)  # type: ignore[arg-type]
    b = compute_vote_envelope_integrity_hash(**kwargs)  # type: ignore[arg-type]
    assert a == b
    assert len(a) == 64


def test_compute_vote_envelope_integrity_hash_changes_with_choice() -> None:
    common = dict(
        ballot_id=uuid4(), credential_proof=uuid4(), submitted_at=datetime(2026, 1, 1, tzinfo=UTC)
    )
    a = compute_vote_envelope_integrity_hash(encrypted_or_encoded_choice="yes", **common)  # type: ignore[arg-type]
    b = compute_vote_envelope_integrity_hash(encrypted_or_encoded_choice="no", **common)  # type: ignore[arg-type]
    assert a != b


# --- VoteReceipt status machine + receipt_hash construction ------------------


def test_parse_vote_receipt_verification_status_rejects_unknown_value() -> None:
    with pytest.raises(UnknownVoteReceiptStatusError):
        parse_vote_receipt_verification_status("half_verified")


@pytest.mark.parametrize("current,target", sorted(ALLOWED_RECEIPT_TRANSITIONS))
def test_every_allowed_receipt_transition_succeeds(
    current: VoteReceiptVerificationStatus, target: VoteReceiptVerificationStatus
) -> None:
    receipt = _make_receipt(verification_status=current)
    updated = receipt.with_status(target)
    assert updated.verification_status == target


def test_receipt_verified_is_terminal() -> None:
    receipt = _make_receipt(verification_status=VoteReceiptVerificationStatus.VERIFIED)
    with pytest.raises(ForbiddenVoteReceiptTransitionError):
        receipt.with_status(VoteReceiptVerificationStatus.ISSUED)


def test_compute_vote_receipt_hash_signature_excludes_the_choice() -> None:
    """Structural guarantee, not just a convention: `compute_vote_receipt_hash`
    has no parameter that could carry `encrypted_or_encoded_choice` at
    all, so a receipt cannot be built in a way that leaks it."""
    signature = inspect.signature(compute_vote_receipt_hash)
    param_names = set(signature.parameters)
    assert param_names == {"vote_envelope_id", "integrity_hash"}


def test_compute_vote_receipt_hash_is_deterministic_and_matches_across_equal_inputs() -> None:
    vote_envelope_id = uuid4()
    integrity_hash = "c" * 64
    a = compute_vote_receipt_hash(vote_envelope_id=vote_envelope_id, integrity_hash=integrity_hash)
    b = compute_vote_receipt_hash(vote_envelope_id=vote_envelope_id, integrity_hash=integrity_hash)
    assert a == b
    assert len(a) == 64


def test_ballot_option_display_order_must_be_non_negative() -> None:
    with pytest.raises(ValueError, match="display_order"):
        _make_option(display_order=-1)


def test_vote_envelope_requires_timezone_aware_submitted_at() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        VoteEnvelope(
            vote_envelope_id=uuid4(),
            ballot_id=uuid4(),
            credential_proof=uuid4(),
            encrypted_or_encoded_choice="yes",
            submitted_at=datetime(2026, 1, 1),
            integrity_hash="a" * 64,
            validation_status=VoteEnvelopeStatus.RECEIVED,
            included_in_tally=False,
        )


def test_only_three_ballot_method_values_exist() -> None:
    """ADR-009 item 4: the pilot restricts `ballot_method` to exactly
    `single_choice`/`yes_no`."""
    assert {m.value for m in BallotMethod} == {"single_choice", "yes_no"}


def test_close_time_after_open_time_smoke() -> None:
    ballot = _make_ballot()
    assert ballot.closes_at > ballot.opens_at
    assert ballot.closes_at - ballot.opens_at == timedelta(days=7)
