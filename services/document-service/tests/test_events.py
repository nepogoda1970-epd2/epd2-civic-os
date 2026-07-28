"""Canonical events: the closed catalogue, the envelope, safe metadata and
the emission boundary (CT-00-05, CT-00-08).
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from _builders import (
    T0,
    Fixture,
    governed_document,
    reason,
    retention_binding,
    version,
)

from epd2_core.event_envelope import ActorRef, compute_payload_hash
from epd2_document_service import events as document_events
from epd2_document_service.domain import (
    FORBIDDEN_CONTENT_KEYS,
    PROHIBITED_IDENTITY_KEYS,
    PROHIBITED_VOTING_KEYS,
    DispositionAuthorization,
    HoldState,
    LegalHoldBinding,
)
from epd2_document_service.events import (
    DOCUMENT_EVENT_AGGREGATE_BY_PREFIX,
    DOCUMENT_EVENT_AGGREGATES,
    DOCUMENT_EVENT_TYPES,
    EVENT_VERSION,
    PUBLIC_PROJECTION_ALLOWED,
    assert_known_event_type,
    assert_supported_version,
    build_document_event,
    event_aggregate,
    is_publicly_projectable,
)
from epd2_document_service.exceptions import (
    DocumentContentLeakError,
    ForbiddenIdentityLinkageError,
    UnknownDocumentEventTypeError,
    UnsupportedEventVersionError,
    VotingLinkageForbiddenError,
)


def _actor() -> ActorRef:
    return ActorRef(actor_id=uuid4(), actor_type="organizational_authority")


# ---------------------------------------------------------------------------
# The catalogue
# ---------------------------------------------------------------------------


def test_the_catalogue_is_unique_and_closed() -> None:
    assert len(DOCUMENT_EVENT_TYPES) == len(set(DOCUMENT_EVENT_TYPES))
    with pytest.raises(UnknownDocumentEventTypeError):
        assert_known_event_type("document_version.quietly_edited")


def test_every_event_type_has_a_known_aggregate_prefix() -> None:
    for event_type in DOCUMENT_EVENT_TYPES:
        prefix = event_type.split(".", 1)[0]
        assert prefix in DOCUMENT_EVENT_AGGREGATE_BY_PREFIX, event_type
        assert event_aggregate(event_type) == DOCUMENT_EVENT_AGGREGATES[event_type]


def test_no_event_type_carries_a_service_prefix() -> None:
    """Canon section 20 writes `finance_account.created`, not
    `finance.finance_account_created`."""
    assert not any(t.startswith("document.") for t in DOCUMENT_EVENT_TYPES)


def test_the_public_projection_allow_list_is_a_subset_of_the_catalogue() -> None:
    assert PUBLIC_PROJECTION_ALLOWED.issubset(set(DOCUMENT_EVENT_TYPES))


def test_only_publication_shaped_events_are_publicly_projectable() -> None:
    """A public stream carrying "a legal opinion was registered for case X"
    would disclose the existence of proceedings the publication rules
    never authorized disclosing."""
    for event_type in DOCUMENT_EVENT_TYPES:
        expected = event_type in PUBLIC_PROJECTION_ALLOWED
        assert is_publicly_projectable(event_type) is expected
    assert not any(
        t.startswith(("document_evidence.", "document_determination."))
        for t in PUBLIC_PROJECTION_ALLOWED
    )
    assert "governed_document.registered" not in PUBLIC_PROJECTION_ALLOWED


def test_the_allow_list_is_closed_rather_than_a_deny_list() -> None:
    """A deny-list would admit every event type somebody adds later, and
    the default for a governance stream must be "not public"."""
    with pytest.raises(UnknownDocumentEventTypeError):
        is_publicly_projectable("document_publication.invented_later")


# ---------------------------------------------------------------------------
# Versioning (CT-00-05)
# ---------------------------------------------------------------------------


def test_the_supported_major_version_is_one() -> None:
    assert EVENT_VERSION == "1.0"
    assert_supported_version("1.7")


def test_an_unknown_major_version_is_not_processed() -> None:
    for bad in ("2.0", "0.9", "banana"):
        with pytest.raises(UnsupportedEventVersionError):
            assert_supported_version(bad)


# ---------------------------------------------------------------------------
# The envelope
# ---------------------------------------------------------------------------


def _build(payload: dict[str, object], event_type: str = "governed_document.registered"):
    fixture = Fixture()
    return build_document_event(
        event_id=uuid4(),
        event_type=event_type,
        occurred_at=T0,
        actor=_actor(),
        aggregate_id=uuid4(),
        scope=fixture.scope,
        payload=payload,
        correlation_id=uuid4(),
    )


def test_safe_metadata_is_added_by_the_builder_not_by_each_payload() -> None:
    """So no builder can forget the organizational scope or the stable
    aggregate identifier."""
    envelope = _build({"document_id": str(uuid4())})
    assert "organization_id" in envelope.payload
    assert "aggregate_id" in envelope.payload


def test_the_subject_type_is_derived_from_the_event_type() -> None:
    envelope = _build({"a": 1}, event_type="document_evidence.registered")
    assert envelope.subject.subject_type == "EvidenceRecord"


def test_the_payload_hash_is_deterministic() -> None:
    payload = {"document_id": "1", "b": [1, 2, 3]}
    envelope = _build(dict(payload))
    assert envelope.integrity.payload_hash == compute_payload_hash(envelope.payload)


def test_the_producer_is_the_document_service() -> None:
    assert _build({"a": 1}).producer == "document-service"


def test_an_unknown_event_type_cannot_be_built() -> None:
    with pytest.raises(UnknownDocumentEventTypeError):
        _build({"a": 1}, event_type="document_version.silently_edited")


# ---------------------------------------------------------------------------
# The emission boundary (CT-00-08)
# ---------------------------------------------------------------------------


def test_an_identity_key_cannot_reach_an_event() -> None:
    for key in sorted(PROHIBITED_IDENTITY_KEYS):
        with pytest.raises(ForbiddenIdentityLinkageError):
            _build({key: "x"})


def test_a_voting_linkage_cannot_reach_an_event() -> None:
    """FIR-INV-002 / FIR-INV-003: a minutes document may record that a vote
    happened; it may never carry a reference that could join a ballot to a
    person."""
    for key in sorted(PROHIBITED_VOTING_KEYS):
        with pytest.raises(VotingLinkageForbiddenError):
            _build({key: "x"})


def test_document_content_cannot_reach_an_event() -> None:
    for key in sorted(FORBIDDEN_CONTENT_KEYS):
        with pytest.raises(DocumentContentLeakError):
            _build({key: "x"})


def test_a_nested_leak_is_caught() -> None:
    with pytest.raises(ForbiddenIdentityLinkageError):
        _build({"reviewers": [{"detail": {"email": "a@b.c"}}]})


# ---------------------------------------------------------------------------
# Payload builders
# ---------------------------------------------------------------------------


def _fixture_document() -> tuple[Fixture, object, object]:
    fixture = Fixture()
    document = governed_document(fixture.scope, fixture.custodian)
    recorded = version(document, fixture.author)
    return fixture, document, recorded


def test_a_version_payload_carries_the_digest_and_the_chain_linkage() -> None:
    """So a consumer can verify the chain from the stream alone, without
    asking this service for anything."""
    _fixture, _document, recorded = _fixture_document()
    payload = document_events.version_recorded_payload(recorded)
    assert payload["version_hash"] == recorded.version_hash
    assert payload["previous_version_hash"] == recorded.previous_version_hash
    assert payload["content_descriptor"]["content_digest"] == recorded.content.digest
    assert "content" not in payload


def test_a_version_payload_carries_a_title_reference_and_never_a_title() -> None:
    """A document's title is content: "Beschwerde gegen den
    Aufnahmebescheid von …" names a person as reliably as a `full_name`
    field would."""
    _fixture, _document, recorded = _fixture_document()
    payload = document_events.version_recorded_payload(recorded)
    assert payload["title_reference"] == recorded.title_reference
    assert "title" not in payload


def test_the_wire_authority_drops_the_actor_reference() -> None:
    """`actor_reference` is the closest thing this service holds to an
    actor-level identifier, and an event carrying it would put a
    correlatable per-actor handle on every governed act in the stream."""
    _fixture, _document, recorded = _fixture_document()
    payload = document_events.version_recorded_payload(recorded)
    authority = payload["recorded_by"]
    assert set(authority) == {"authority_id", "role_code"}
    assert recorded.recorded_by.actor_reference not in str(payload)


def test_a_legal_hold_payload_carries_no_matter_substance_beyond_a_reference() -> None:
    fixture, document, _recorded = _fixture_document()
    binding = LegalHoldBinding(
        hold_reference="pack-09:hold:12",
        scope=fixture.scope,
        state=HoldState.ACTIVE,
        observed_at=T0,
        matter_reference="pack-09:matter:5",
    )
    payload = document_events.legal_hold_observed_payload(document, binding)
    hold = payload["legal_hold"]
    assert set(hold) == {"hold_reference", "hold_state", "observed_at", "matter_reference"}


def test_a_retention_payload_carries_the_pack_09_references_only() -> None:
    _fixture, document, _recorded = _fixture_document()
    payload = document_events.retention_bound_payload(document, retention_binding())
    assert payload["retention"]["record_class_reference"].startswith("pack-09:")


def test_a_disposition_payload_carries_the_authorization_reference() -> None:
    fixture, document, _recorded = _fixture_document()
    authorization = DispositionAuthorization(
        authorization_reference="pack-09:auth:1",
        scope=fixture.scope,
        authorized_at=T0,
        authorized_version_count=1,
        disposition_action="delete",
    )
    payload = document_events.disposition_authorized_payload(document, authorization)
    assert payload["disposition_authorization"]["authorization_reference"] == "pack-09:auth:1"


def test_an_integrity_payload_reports_a_failure_rather_than_swallowing_it() -> None:
    """A negative result that stayed inside the service would leave the
    only party who could act on it uninformed."""
    from epd2_document_service.versions import ChainVerificationResult

    result = ChainVerificationResult(
        document_id=uuid4(),
        valid=False,
        version_count=3,
        head_hash="a" * 64,
        broken_at_version=2,
        detail="stored version_hash does not match the recomputed hash",
    )
    payload = document_events.integrity_verified_payload(result)
    assert payload["valid"] is False
    assert payload["broken_at_version"] == 2


def test_every_payload_builder_output_passes_the_emission_boundary() -> None:
    """A blanket sweep: each builder's own output goes through the same
    check `build_document_event` applies, so a builder that grew a
    forbidden key is caught here rather than in production."""
    _fixture, document, recorded = _fixture_document()
    payloads = [
        document_events.document_registered_payload(document),
        document_events.document_state_changed_payload(document, reason()),
        document_events.retention_bound_payload(document, retention_binding()),
        document_events.version_recorded_payload(recorded),
        document_events.version_state_changed_payload(recorded, reason()),
    ]
    for payload in payloads:
        _build(dict(payload))
