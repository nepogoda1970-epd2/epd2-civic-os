"""PACK-15 voting-side unit, integration, privacy and replay tests.

The properties asserted here are the ones ADR-092 and ADR-093 state
normatively: exactly-once issuance, idempotent retry, an absorbing
`redeemed` state, atomic redemption, replay refusal without attribution,
delivery only inside the isolated origin, and - the load-bearing one - that
**no artifact on this side can carry an assertion reference**.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest

from epd2_credential_service.voting_credential_application import (
    MAX_IDEMPOTENCY_WINDOW_SECONDS,
    AssertionVerifier,
    PresentedAssertion,
    VotingContextTerms,
    VotingCredentialIssuerService,
)
from epd2_credential_service.voting_credential_events import (
    CREDENTIAL_ISSUED,
    DUPLICATE_ISSUANCE_REJECTED,
    build_credential_event,
)
from epd2_credential_service.voting_credential_exceptions import (
    AssertionAlreadyUsedError,
    AssertionAudienceMismatchError,
    AssertionContextMismatchError,
    AssertionExpiredError,
    AssertionInvalidError,
    AssertionPurposeMismatchError,
    CredentialAlreadyRedeemedError,
    CredentialIssuanceWindowClosedError,
    CredentialOriginRefusedError,
    CredentialReplayDetectedError,
    CredentialRevocationCutoffPassedError,
    DeliveryChannelRefusedError,
    ForbiddenCredentialFieldError,
)
from epd2_credential_service.voting_credential_storage import (
    InMemoryCredentialIdempotencyStore,
    InMemoryCredentialRedemptionStore,
    InMemoryCredentialReplayStore,
    InMemorySpentNonceSet,
    InMemoryVotingCredentialStore,
    assert_spent_set_is_not_a_map,
)
from epd2_credential_service.voting_credentials import (
    FORBIDDEN_FIELD_NAMES,
    PERMITTED_DELIVERY_CHANNEL,
    PROHIBITED_DELIVERY_CHANNELS,
    CredentialIssuanceIdempotencyRecord,
    CredentialRedemption,
    CredentialReplayRecord,
    CredentialStatus,
    SpentNonce,
    VotingCredential,
    assert_absorbing_redeemed,
    assert_delivery_channel_permitted,
    assert_no_forbidden_credential_fields,
    transition_permitted,
)

NOW = datetime(2026, 8, 2, 9, 31, 7, tzinfo=UTC)
ORIGIN = "https://vote.epd.example"


def _terms() -> VotingContextTerms:
    return VotingContextTerms(
        voting_context_reference="vc-1",
        credential_type="internal_party_vote",
        audience_origin=ORIGIN,
        issuance_window_start=NOW - timedelta(hours=1),
        issuance_window_end=NOW + timedelta(hours=5),
        redemption_window_end=NOW + timedelta(hours=6),
        revocation_cutoff=NOW + timedelta(hours=4),
        timestamp_granularity_seconds=300,
        minting_delay_min_seconds=5,
        minting_delay_max_seconds=30,
    )


def _service() -> VotingCredentialIssuerService:
    return VotingCredentialIssuerService(
        credentials=InMemoryVotingCredentialStore(),
        spent_nonces=InMemorySpentNonceSet(),
        idempotency=InMemoryCredentialIdempotencyStore(),
        redemptions=InMemoryCredentialRedemptionStore(),
        replays=InMemoryCredentialReplayStore(),
        verifier=AssertionVerifier(
            verify=lambda message, signature: signature == "valid",
            expected_audience="credential-issuer",
        ),
        allowed_origins=(ORIGIN,),
    )


def _assertion(nonce: str = "nonce-1", **overrides: object) -> PresentedAssertion:
    base = {
        "assertion_id": uuid4(),
        "voting_context_reference": "vc-1",
        "eligibility_result": "approved",
        "eligibility_class": "full_member",
        "organizational_scope": "DE-BE-01",
        "required_assurance_satisfied": True,
        "issued_at_bucket": NOW,
        "expires_at": NOW + timedelta(hours=2),
        "audience": "credential-issuer",
        "purpose": "voting_credential_issuance",
        "nonce": nonce,
        "status": "picked_up",
        "signature": "valid",
    }
    base.update(overrides)
    return PresentedAssertion(**base)  # type: ignore[arg-type]


def _issue(service: VotingCredentialIssuerService, **overrides: object):  # type: ignore[no-untyped-def]
    kwargs = {
        "credential_id": uuid4(),
        "assertion": _assertion(),
        "terms": _terms(),
        "origin": ORIGIN,
        "idempotency_key": "k1",
        "canonical_message": b"message",
        "now": NOW,
        "minting_delay_seconds": 10,
        "delivery_channel": PERMITTED_DELIVERY_CHANNEL,
        "event_id": uuid4(),
        "correlation_id": uuid4(),
    }
    kwargs.update(overrides)
    return service.issue(**kwargs)  # type: ignore[arg-type]


# -- the load-bearing structural property (ADR-093) -------------------------


def test_no_credential_artifact_carries_an_assertion_reference() -> None:
    for name in ("assertion_id", "eligibility_assertion_id", "nonce", "context_pseudonym"):
        assert name in FORBIDDEN_FIELD_NAMES
    assert "assertion_id" not in VotingCredential.__dataclass_fields__
    assert "nonce" not in VotingCredential.__dataclass_fields__
    assert "participant_reference" not in VotingCredential.__dataclass_fields__


def test_the_spent_nonce_record_is_a_set_member_not_a_map_entry() -> None:
    fields = set(SpentNonce.__dataclass_fields__)
    assert fields == {"nonce", "voting_context_reference", "spent_at_bucket"}
    assert "voting_credential_id" not in fields


def test_a_spent_nonce_adapter_may_not_resolve_a_nonce_to_a_credential() -> None:
    class MapShaped:
        def get_credential_for(self, nonce: str) -> None:
            return None

    with pytest.raises(ValueError):
        assert_spent_set_is_not_a_map(MapShaped())
    assert_spent_set_is_not_a_map(InMemorySpentNonceSet())


def test_a_payload_carrying_a_forbidden_field_is_refused() -> None:
    with pytest.raises(ForbiddenCredentialFieldError):
        assert_no_forbidden_credential_fields({"assertion_id": "a"})
    with pytest.raises(ForbiddenCredentialFieldError):
        assert_no_forbidden_credential_fields({"account_id": "a"})


def test_the_idempotency_window_is_bounded() -> None:
    record = CredentialIssuanceIdempotencyRecord(
        idempotency_key="k",
        voting_credential_id=uuid4(),
        created_at=NOW,
        expires_at=NOW + timedelta(seconds=300),
    )
    record.assert_not_durable(MAX_IDEMPOTENCY_WINDOW_SECONDS)
    long_record = CredentialIssuanceIdempotencyRecord(
        idempotency_key="k",
        voting_credential_id=uuid4(),
        created_at=NOW,
        expires_at=NOW + timedelta(days=30),
    )
    with pytest.raises(ValueError):
        long_record.assert_not_durable(MAX_IDEMPOTENCY_WINDOW_SECONDS)


def test_a_service_refuses_an_unbounded_idempotency_window() -> None:
    with pytest.raises(ValueError):
        VotingCredentialIssuerService(
            credentials=InMemoryVotingCredentialStore(),
            spent_nonces=InMemorySpentNonceSet(),
            idempotency=InMemoryCredentialIdempotencyStore(),
            redemptions=InMemoryCredentialRedemptionStore(),
            replays=InMemoryCredentialReplayStore(),
            verifier=AssertionVerifier(verify=lambda m, s: True, expected_audience="x"),
            allowed_origins=(ORIGIN,),
            idempotency_window_seconds=MAX_IDEMPOTENCY_WINDOW_SECONDS + 1,
        )


# -- issuance ---------------------------------------------------------------


def test_issuance_mints_one_credential_and_spends_the_nonce() -> None:
    service = _service()
    credential, event = _issue(service)
    assert credential.status is CredentialStatus.ISSUED
    assert service.spent_nonces.contains("nonce-1")
    assert event.event_type == CREDENTIAL_ISSUED


def test_a_retry_with_the_same_key_returns_the_same_credential() -> None:
    service = _service()
    first, _ = _issue(service)
    second, event = _issue(service, credential_id=uuid4())
    assert second.voting_credential_id == first.voting_credential_id
    assert event.event_type == DUPLICATE_ISSUANCE_REJECTED


def test_a_second_issuance_from_a_spent_nonce_is_refused() -> None:
    service = _service()
    _issue(service)
    with pytest.raises(AssertionAlreadyUsedError):
        _issue(service, idempotency_key="k2", credential_id=uuid4())


def test_issuance_from_outside_the_isolated_origin_is_refused() -> None:
    service = _service()
    with pytest.raises(CredentialOriginRefusedError):
        _issue(service, origin="https://app.epd.example")


@pytest.mark.parametrize("channel", sorted(PROHIBITED_DELIVERY_CHANNELS))
def test_every_prohibited_delivery_channel_is_refused(channel: str) -> None:
    with pytest.raises(DeliveryChannelRefusedError):
        assert_delivery_channel_permitted(channel)
    assert_delivery_channel_permitted(PERMITTED_DELIVERY_CHANNEL)


def test_issuance_outside_the_window_is_refused() -> None:
    service = _service()
    with pytest.raises(CredentialIssuanceWindowClosedError):
        _issue(service, now=NOW + timedelta(hours=9))


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        ({"audience": "someone-else"}, AssertionAudienceMismatchError),
        ({"purpose": "login"}, AssertionPurposeMismatchError),
        ({"voting_context_reference": "vc-2"}, AssertionContextMismatchError),
        ({"signature": "forged"}, AssertionInvalidError),
    ],
)
def test_assertion_binding_failures_are_distinct_refusals(
    overrides: dict[str, Any], expected: type[Exception]
) -> None:
    service = _service()
    with pytest.raises(expected):
        _issue(service, assertion=_assertion(**overrides))


def test_an_expired_assertion_is_refused() -> None:
    service = _service()
    with pytest.raises(AssertionExpiredError):
        _issue(service, assertion=_assertion(expires_at=NOW - timedelta(minutes=1)))


def test_the_minting_delay_must_lie_inside_the_governed_window() -> None:
    service = _service()
    with pytest.raises(ValueError):
        _issue(service, minting_delay_seconds=120)


# -- redemption and replay --------------------------------------------------


def test_redemption_is_atomic_and_yields_a_capability_that_is_not_the_credential() -> None:
    service = _service()
    credential, _ = _issue(service)
    redemption, event = service.redeem(
        voting_credential_id=credential.voting_credential_id,
        terms=_terms(),
        origin=ORIGIN,
        now=NOW + timedelta(minutes=1),
        event_id=uuid4(),
        correlation_id=uuid4(),
        replay_id=uuid4(),
    )
    assert redemption.continuation_capability != str(credential.voting_credential_id)
    stored = service.credentials.get(credential.voting_credential_id)
    assert stored is not None and stored.status is CredentialStatus.REDEEMED
    assert "continuation_capability" not in event.payload


def test_a_second_redemption_is_a_replay_and_is_recorded_without_attribution() -> None:
    service = _service()
    credential, _ = _issue(service)
    service.redeem(
        voting_credential_id=credential.voting_credential_id,
        terms=_terms(),
        origin=ORIGIN,
        now=NOW + timedelta(minutes=1),
        event_id=uuid4(),
        correlation_id=uuid4(),
        replay_id=uuid4(),
    )
    with pytest.raises(CredentialReplayDetectedError):
        service.redeem(
            voting_credential_id=credential.voting_credential_id,
            terms=_terms(),
            origin=ORIGIN,
            now=NOW + timedelta(minutes=2),
            event_id=uuid4(),
            correlation_id=uuid4(),
            replay_id=uuid4(),
        )
    assert service.replays.count("vc-1") == 1
    recorded = service.replays.all_for_context("vc-1")[0]
    assert "participant_reference" not in recorded.__dataclass_fields__


def test_a_replay_record_refuses_any_attribution() -> None:
    with pytest.raises(ForbiddenCredentialFieldError):
        CredentialReplayRecord(
            replay_id=uuid4(),
            voting_context_reference="vc-1",
            reason_code="CREDENTIAL_REPLAY_DETECTED",
            detected_at_bucket=NOW,
            forbidden={"account_id": "a"},
        )


def test_redemption_from_the_wrong_origin_is_refused() -> None:
    service = _service()
    credential, _ = _issue(service)
    with pytest.raises(CredentialOriginRefusedError):
        service.redeem(
            voting_credential_id=credential.voting_credential_id,
            terms=_terms(),
            origin="https://app.epd.example",
            now=NOW + timedelta(minutes=1),
            event_id=uuid4(),
            correlation_id=uuid4(),
            replay_id=uuid4(),
        )


# -- revocation and the absorbing state -------------------------------------


def test_redeemed_is_absorbing() -> None:
    assert CredentialStatus.REDEEMED in CredentialStatus
    assert not transition_permitted(CredentialStatus.REDEEMED, CredentialStatus.ISSUED)
    with pytest.raises(CredentialAlreadyRedeemedError):
        assert_absorbing_redeemed(CredentialStatus.REDEEMED)


def test_revocation_after_redemption_is_refused() -> None:
    service = _service()
    credential, _ = _issue(service)
    service.redeem(
        voting_credential_id=credential.voting_credential_id,
        terms=_terms(),
        origin=ORIGIN,
        now=NOW + timedelta(minutes=1),
        event_id=uuid4(),
        correlation_id=uuid4(),
        replay_id=uuid4(),
    )
    with pytest.raises(CredentialAlreadyRedeemedError):
        service.revoke_unredeemed(
            voting_credential_id=credential.voting_credential_id,
            terms=_terms(),
            reason_code="CREDENTIAL_REVOKED",
            authority_role="credential_issuer",
            dual_control_reference=None,
            now=NOW + timedelta(minutes=2),
            event_id=uuid4(),
            correlation_id=uuid4(),
        )


def test_revocation_after_the_cutoff_is_refused() -> None:
    service = _service()
    credential, _ = _issue(service)
    with pytest.raises(CredentialRevocationCutoffPassedError):
        service.revoke_unredeemed(
            voting_credential_id=credential.voting_credential_id,
            terms=_terms(),
            reason_code="CREDENTIAL_REVOKED",
            authority_role="credential_issuer",
            dual_control_reference="dual-1",
            now=NOW + timedelta(hours=5),
            event_id=uuid4(),
            correlation_id=uuid4(),
        )


def test_revocation_cannot_be_targeted_at_a_participant() -> None:
    """The interface cannot express it: there is no such parameter."""
    import inspect

    signature = inspect.signature(VotingCredentialIssuerService.revoke_unredeemed)
    for forbidden in ("participant", "participant_reference", "account_id", "member_number"):
        assert forbidden not in signature.parameters


# -- privacy-safe status ----------------------------------------------------


def test_the_status_lookup_is_not_an_oracle() -> None:
    service = _service()
    credential, _ = _issue(service)
    known = service.privacy_safe_status(credential.voting_credential_id)
    unknown = service.privacy_safe_status(uuid4())
    assert sorted(known) == sorted(unknown)
    assert "participant_reference" not in known


def test_there_is_no_search_operation_on_the_issuer() -> None:
    for forbidden in ("find_by_participant", "list", "search", "all_credentials"):
        assert not hasattr(VotingCredentialIssuerService, forbidden)


# -- events -----------------------------------------------------------------


def test_a_credential_event_carries_no_assertion_reference() -> None:
    credential = VotingCredential(
        voting_credential_id=uuid4(),
        credential_type="internal_party_vote",
        status=CredentialStatus.ISSUED,
        voting_context_reference="vc-1",
        issued_at_bucket=NOW,
        expires_at=NOW + timedelta(hours=2),
        audience_origin=ORIGIN,
    )
    event = build_credential_event(
        event_id=uuid4(),
        event_type=CREDENTIAL_ISSUED,
        credential=credential,
        reason_code="CREDENTIAL_ISSUANCE_AUTHORIZED",
        granularity_seconds=300,
        correlation_id=uuid4(),
        occurred_at=NOW,
    )
    assert "assertion_id" not in event.payload
    assert "nonce" not in event.payload
    assert event.occurred_at.second == 0
    assert event.producer == "credential-service"


def test_a_redemption_record_never_echoes_the_credential_as_the_capability() -> None:
    credential_id = uuid4()
    with pytest.raises(ValueError):
        CredentialRedemption(
            redemption_reference="r",
            voting_credential_id=credential_id,
            voting_context_reference="vc-1",
            redeemed_at_bucket=NOW,
            continuation_capability=str(credential_id),
        )
