"""The canonical event catalog (`P12-EVT-*`, ADR-068)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from epd2_core.event_envelope import ActorRef
from epd2_privileged_access_service import events
from epd2_privileged_access_service.domain import OrganizationalScopeRef
from epd2_privileged_access_service.exceptions import (
    AssignmentNotEffectiveDatedError,
    ExportBallotContentProhibitedError,
    PrivilegedSessionSecretForbiddenError,
    UnknownStatusError,
)

T0 = datetime(2026, 3, 1, 9, 0, tzinfo=UTC)
SCOPE = OrganizationalScopeRef(organization_id=uuid4())
ACTOR = ActorRef(actor_id=uuid4(), actor_type="organizational_authority")


def _build(event_type: str, payload: dict[str, object] | None = None) -> object:
    return events.build_privileged_event(
        event_id=uuid4(),
        event_type=event_type,
        occurred_at=T0,
        actor=ACTOR,
        aggregate_id=uuid4(),
        scope=SCOPE,
        payload=payload or {"grant_id": str(uuid4())},
        correlation_id=uuid4(),
    )


class TestCatalog:
    def test_there_are_exactly_forty_four_event_types(self) -> None:
        assert len(events.PRIVILEGED_ACCESS_EVENT_TYPES) == 44

    def test_no_event_type_is_declared_twice(self) -> None:
        assert len(set(events.PRIVILEGED_ACCESS_EVENT_TYPES)) == 44

    def test_every_name_carries_an_aggregate_prefix_not_a_service_prefix(self) -> None:
        """Canon section 20's convention: `privileged_access.requested`,
        never `pack12.privileged_access_requested` (`P12-EVT-004`). A
        service prefix ties an event name to a deployment, and a
        deployment is not a domain concept."""
        for name in events.PRIVILEGED_ACCESS_EVENT_TYPES:
            prefix, _, suffix = name.partition(".")
            assert suffix, name
            assert prefix in events.EVENT_AGGREGATE_BY_PREFIX, name
            assert not prefix.startswith("pack"), name

    def test_every_prefix_resolves_to_an_aggregate(self) -> None:
        for name in events.PRIVILEGED_ACCESS_EVENT_TYPES:
            assert events.aggregate_for(name)

    def test_an_unknown_event_type_is_refused(self) -> None:
        with pytest.raises(UnknownStatusError):
            events.assert_known_event_type("privileged_access.superuser_granted")

    def test_an_unknown_prefix_is_refused(self) -> None:
        with pytest.raises(UnknownStatusError):
            events.aggregate_for("nonsense.happened")


class TestEnvelope:
    def test_the_envelope_version_is_unchanged(self) -> None:
        """`P12-EVT-002`: PACK-12 adds no envelope field and
        reinterprets none."""
        assert events.EVENT_VERSION == "1.0"
        assert frozenset({1}) == events.SUPPORTED_MAJOR_VERSIONS

    def test_scope_and_aggregate_id_are_added_centrally(self) -> None:
        """Added once, here - not by forty-four hand-written copies, so
        no builder can forget them."""
        envelope = _build("privileged_access.requested")
        assert envelope.payload["organization_scope"] == SCOPE.to_payload()  # type: ignore[attr-defined]
        assert "aggregate_id" in envelope.payload  # type: ignore[attr-defined]

    def test_a_naive_timestamp_is_refused(self) -> None:
        with pytest.raises(AssignmentNotEffectiveDatedError):
            events.build_privileged_event(
                event_id=uuid4(),
                event_type="privileged_access.requested",
                occurred_at=datetime(2026, 3, 1, 9, 0),
                actor=ACTOR,
                aggregate_id=uuid4(),
                scope=SCOPE,
                payload={},
                correlation_id=uuid4(),
            )

    def test_every_declared_event_type_builds(self) -> None:
        for name in events.PRIVILEGED_ACCESS_EVENT_TYPES:
            assert _build(name) is not None


class TestPayloadGuards:
    def test_a_secret_never_becomes_an_event(self) -> None:
        """Both guards run before the envelope exists, so a payload that
        would carry a credential never becomes an event - not even
        briefly (`P12-EVT-003`)."""
        with pytest.raises(PrivilegedSessionSecretForbiddenError):
            _build("privileged_access.requested", {"password": "hunter2"})

    def test_voting_material_never_becomes_an_event(self) -> None:
        """Two independent guards, and this exercises the second.

        `ballot_id` is caught by the prohibited-key registry; a key like
        `tally_id` is caught only by `assert_no_voting_material`. Testing
        the first alone would leave the voting guard unexercised and
        silently removable."""
        with pytest.raises(PrivilegedSessionSecretForbiddenError):
            _build("privileged_access.requested", {"ballot_id": str(uuid4())})
        with pytest.raises(ExportBallotContentProhibitedError):
            _build("privileged_access.requested", {"tally_id": str(uuid4())})

    def test_a_query_payload_carries_a_digest_never_the_query(self) -> None:
        """A query string can itself contain personal data."""
        payload = events.query_submitted_payload(
            query_id=uuid4(),
            mode="scoped_domain",
            purpose="operations",
            query_digest="d" * 64,
            domains=frozenset({"membership"}),
        )
        assert "query_digest" in payload
        assert "query" not in payload
        assert "query_text" not in payload

    def test_an_execution_payload_reports_a_band_never_a_count(self) -> None:
        """An exact suppression count is itself a disclosure of how many
        restricted records matched."""
        payload = events.query_executed_payload(
            query_id=uuid4(),
            authorized_count=3,
            suppressed_band="1-5",
            policy_version="v1",
        )
        assert payload["suppressed_band"] == "1-5"
        assert "suppressed_count" not in payload

    def test_a_notification_payload_exists_for_failures_too(self) -> None:
        """`P12-BG-008`: a failed dispatch is a governed fact that
        escalates, so the event exists in both cases and carries the
        reason."""
        payload = events.notification_dispatched_payload(
            activation_id=uuid4(),
            recipient_class="security_oversight",
            delivered=False,
            dispatch_reference="dispatch:1",
            failure_reason="channel_unavailable",
        )
        assert payload["delivered"] is False
        assert payload["failure_reason"] == "channel_unavailable"

    def test_the_revocation_payload_never_claims_retrieval(self) -> None:
        """`P12-EXP-013`: revocation withdraws authorization; it does not
        reach a delivered copy, and no field says otherwise."""
        payload = events.export_revoked_payload(
            export_id=uuid4(), revoking_authority="authority:1", reason_code="X"
        )
        assert not {"deleted", "destroyed", "retrieved", "recalled"} & set(payload)

    def test_the_destruction_payload_records_an_attestation(self) -> None:
        payload = events.destruction_attested_payload(
            export_id=uuid4(),
            attesting_party="recipient:1",
            attestation_reference="attestation:1",
            attested_at=T0.isoformat(),
        )
        assert "attesting_party" in payload
        assert "destroyed" not in payload

    def test_the_publication_observation_carries_no_result_content(self) -> None:
        """`P12-VOTE-005`: PACK-12 does not certify, decide closure or
        publish. An event of this type is never evidence that PACK-12
        released anything."""
        payload = events.governed_publication_observed_payload(
            publication_reference="publication:1",
            certification_reference="certification:1",
            publication_decision_reference="decision:1",
        )
        assert set(payload) == {
            "publication_reference",
            "certification_reference",
            "publication_decision_reference",
        }


class TestPublicProjection:
    def test_no_pack12_event_is_publicly_projectable(self) -> None:
        """An empty set is the honest answer, not an oversight: every
        PACK-12 event describes a privileged act, a search, an export or
        a disclosure decision, and none of those is public
        information."""
        assert frozenset() == events.PUBLIC_PROJECTION_ALLOWED
