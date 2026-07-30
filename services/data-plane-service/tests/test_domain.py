"""Domain primitives: payload guards, scope, references, reserved
boundaries (PACK-13 §4, §5, §27, §28).

The guards here are the structural backstop the whole package relies on,
so they are tested at every depth a real payload could hide a key at.
"""

from __future__ import annotations

import pytest
from _data_plane_builders import OWNER_DOMAIN, evidence, scope, uid

from epd2_data_plane_service.domain import (
    BULK_CONTENT_KEYS,
    DATA_PLANE_IMPLEMENTATION_STATUS,
    DELIVERY_GUARANTEE,
    FORBIDDEN_DELIVERY_CLAIM,
    GLOBAL_IDENTITY_KEYS,
    PROHIBITED_PAYLOAD_KEYS,
    RESERVED_BOUNDARY_OWNER_ESTABLISHED_BY,
    SECRET_PAYLOAD_KEYS,
    VOTING_MATERIAL_KEYS,
    ActorReference,
    DomainReference,
    EvidenceReference,
    OrganizationScopeKind,
    OrganizationScopeReference,
    PayloadNotMinimalError,
    ReservedBoundary,
    content_digest,
    reject_prohibited_payload_keys,
    reject_reserved_boundary_schema,
    request_digest,
    require_organization_scope,
    require_timezone,
)
from epd2_data_plane_service.exceptions import (
    GlobalUserIdentifierProhibitedError,
    OrganizationScopeMissingError,
    ReservedBoundarySchemaProhibitedError,
    VotingMaterialProhibitedError,
)


def test_voting_material_is_refused_with_its_own_reason_code() -> None:
    with pytest.raises(VotingMaterialProhibitedError) as exc:
        reject_prohibited_payload_keys({"ballot_content": "x"}, context="test")
    assert exc.value.reason_code == "DATAPLANE_VOTING_MATERIAL_PROHIBITED"


def test_global_identity_key_is_refused_with_its_own_reason_code() -> None:
    with pytest.raises(GlobalUserIdentifierProhibitedError) as exc:
        reject_prohibited_payload_keys({"person_id": "x"}, context="test")
    assert exc.value.reason_code == "DATAPLANE_GLOBAL_USER_IDENTIFIER_PROHIBITED"


def test_secret_and_bulk_keys_are_refused_as_not_minimal() -> None:
    with pytest.raises(PayloadNotMinimalError):
        reject_prohibited_payload_keys({"api_key": "x"}, context="test")
    with pytest.raises(PayloadNotMinimalError):
        reject_prohibited_payload_keys({"raw_query": "select 1"}, context="test")


def test_a_prohibited_key_nested_three_levels_down_is_still_refused() -> None:
    payload = {"outer": {"middle": [{"inner": {"voter_id": "x"}}]}}
    with pytest.raises(VotingMaterialProhibitedError):
        reject_prohibited_payload_keys(payload, context="nested")


def test_key_matching_is_case_insensitive() -> None:
    with pytest.raises(GlobalUserIdentifierProhibitedError):
        reject_prohibited_payload_keys({"Person_ID": "x"}, context="case")


def test_a_minimal_payload_passes() -> None:
    reject_prohibited_payload_keys(
        {"schema_version_id": str(uid(1)), "reason_code": "SCHEMA_RETIRED", "position": 4},
        context="minimal",
    )


def test_the_prohibited_set_is_the_union_of_the_four_families() -> None:
    assert PROHIBITED_PAYLOAD_KEYS == (
        SECRET_PAYLOAD_KEYS | GLOBAL_IDENTITY_KEYS | VOTING_MATERIAL_KEYS | BULK_CONTENT_KEYS
    )


def test_the_voting_family_covers_ballot_credential_and_tally() -> None:
    """`P13-VOTE-002` names three things; all three are refused by name."""
    for key in ("ballot_content", "voting_credential", "intermediate_tally"):
        assert key in VOTING_MATERIAL_KEYS


def test_scope_is_required_where_the_record_class_is_scoped() -> None:
    with pytest.raises(OrganizationScopeMissingError):
        require_organization_scope(None, context="projection row")


def test_scope_matching_compares_organization_and_kind() -> None:
    a = OrganizationScopeReference(organization_id=uid(1), scope_kind=OrganizationScopeKind.LAND)
    b = OrganizationScopeReference(organization_id=uid(1), scope_kind=OrganizationScopeKind.KREIS)
    assert not a.matches(b)
    assert a.matches(
        OrganizationScopeReference(organization_id=uid(1), scope_kind=OrganizationScopeKind.LAND)
    )


def test_a_reserved_boundary_gets_no_schema() -> None:
    reserved = DomainReference(domain_name="future_identity_domain", is_reserved_boundary=True)
    with pytest.raises(ReservedBoundarySchemaProhibitedError):
        reject_reserved_boundary_schema(reserved, context="schema ownership")


def test_an_established_domain_may_own_a_schema() -> None:
    reject_reserved_boundary_schema(OWNER_DOMAIN, context="schema ownership")


def test_every_reserved_boundary_names_the_pack_that_establishes_its_owner() -> None:
    """`P13-OWN-013`: PACK-13 assigns none of these owners itself."""
    for boundary in ReservedBoundary:
        assert boundary in RESERVED_BOUNDARY_OWNER_ESTABLISHED_BY
        assert RESERVED_BOUNDARY_OWNER_ESTABLISHED_BY[boundary]


def test_pack_13_assigns_no_owner_to_identity_eligibility_credential_or_voting() -> None:
    for boundary, expected in (
        (ReservedBoundary.IDENTITY, "PACK-14"),
        (ReservedBoundary.ELIGIBILITY, "PACK-15"),
        (ReservedBoundary.CREDENTIAL, "PACK-15"),
        (ReservedBoundary.VOTING, "PACK-15/16"),
        (ReservedBoundary.TALLY, "PACK-15/16"),
    ):
        assert RESERVED_BOUNDARY_OWNER_ESTABLISHED_BY[boundary] == expected


def test_actor_reference_is_scoped_to_its_acting_domain() -> None:
    """`P13-ID-003`: there is no field here that could be joined to
    another domain's actor reference."""
    reference = ActorReference(actor_id=uid(1), actor_type="steward", acting_domain=OWNER_DOMAIN)
    assert reference.acting_domain.domain_name == OWNER_DOMAIN.domain_name
    assert not hasattr(reference, "person_id")
    assert not hasattr(reference, "global_user_id")


def test_evidence_reference_requires_a_digest() -> None:
    with pytest.raises(ValueError, match="content digest"):
        EvidenceReference(evidence_bundle_id=uid(1), content_digest="")


def test_content_and_request_digests_are_deterministic_and_sha256() -> None:
    assert content_digest("abc") == content_digest("abc")
    assert len(content_digest("abc")) == 64
    assert request_digest("abc") == content_digest("abc")


def test_naive_timestamps_are_refused() -> None:
    from datetime import datetime

    with pytest.raises(ValueError, match="timezone-aware"):
        require_timezone(datetime(2026, 1, 1), field="test")


def test_the_delivery_guarantee_is_stated_once_and_never_overclaimed() -> None:
    assert "at-least-once" in DELIVERY_GUARANTEE
    assert "effectively-once" in DELIVERY_GUARANTEE
    assert FORBIDDEN_DELIVERY_CLAIM not in DELIVERY_GUARANTEE


def test_the_implementation_status_is_the_truthful_one() -> None:
    assert DATA_PLANE_IMPLEMENTATION_STATUS == "reference_implementation"


def test_evidence_builder_produces_a_usable_reference() -> None:
    assert evidence().content_digest
    assert scope().organization_id
