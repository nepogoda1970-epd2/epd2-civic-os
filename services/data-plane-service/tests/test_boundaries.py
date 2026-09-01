"""The structural boundary guards (PACK-13 §5, §27, §28; ADR-070).

Ownership and the four admissible integration mechanisms; the audit
ingestion contract; the identity boundary; the seven voting
prohibitions — and the forbidden-phrase scan that keeps the delivery
guarantee honest across this package's whole source tree.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from _data_plane_builders import (
    AUDIT_DOMAIN,
    NOW,
    OTHER_DOMAIN,
    OWNER_DOMAIN,
    actor,
    scope,
    uid,
)

from epd2_data_plane_service.boundaries import (
    AUDIT_OWNER_DOMAIN,
    IDENTITY_BOUNDARY,
    IDENTITY_BOUNDARY_OWNER_ESTABLISHED_BY,
    INTEGRATION_MECHANISMS,
    VOTING_DECISIONS_DEFERRED_TO_PACK_15_16,
    VOTING_PROHIBITIONS,
    VOTING_RESERVED_SCHEMA_OBJECTS,
    ApplicationCredential,
    AuditSubmission,
    IdentifierKind,
    IntegrationMechanism,
    ProhibitedAccessPattern,
    ScopedSubjectReference,
    TableOwnership,
    VotingProhibition,
    reject_ballot_linkage,
    reject_cross_domain_identity_join,
    reject_direct_audit_write,
    reject_global_identifier_column,
    reject_prohibited_access_pattern,
    reject_shared_schema,
    reject_tally_projection,
    reject_voting_client_identifier,
    reject_voting_material,
    require_ingestion_contract,
)
from epd2_data_plane_service.domain import (
    FORBIDDEN_DELIVERY_CLAIM,
    ReservedBoundary,
)
from epd2_data_plane_service.exceptions import (
    AuditDirectWriteDeniedError,
    AuditIngestionContractRequiredError,
    CrossDomainDirectAccessDeniedError,
    GlobalUserIdentifierProhibitedError,
    VotingMaterialProhibitedError,
)

SRC = Path(__file__).resolve().parent.parent / "src" / "epd2_data_plane_service"


def _table(*, readable_by: tuple[str, ...] = ()) -> TableOwnership:
    return TableOwnership(
        table_name="membership_record",
        owning_domain=OWNER_DOMAIN,
        organization_scoped=True,
        may_be_read_by=readable_by,
    )


# ---------------------------------------------------------------------------
# Ownership
# ---------------------------------------------------------------------------


def test_only_the_owner_writes() -> None:
    """`P13-DP-014`: not for convenience, not for performance, not during
    migration."""
    with pytest.raises(CrossDomainDirectAccessDeniedError):
        _table().require_owner_write(OTHER_DOMAIN)


def test_the_owner_writes_its_own_table() -> None:
    _table().require_owner_write(OWNER_DOMAIN)


def test_a_direct_cross_domain_read_is_not_an_integration_pattern() -> None:
    """`P13-DP-013`: a read that works is not thereby permitted."""
    with pytest.raises(CrossDomainDirectAccessDeniedError, match="happens to compile"):
        _table().require_governed_read(OTHER_DOMAIN, mechanism=None)


def test_an_approved_read_contract_must_actually_name_the_reader() -> None:
    with pytest.raises(CrossDomainDirectAccessDeniedError, match="no approved read contract"):
        _table().require_governed_read(
            OTHER_DOMAIN, mechanism=IntegrationMechanism.APPROVED_READ_CONTRACT
        )


def test_a_named_approved_read_contract_is_admitted() -> None:
    _table(readable_by=(OTHER_DOMAIN.domain_name,)).require_governed_read(
        OTHER_DOMAIN, mechanism=IntegrationMechanism.APPROVED_READ_CONTRACT
    )


def test_the_owner_reads_its_own_table_without_a_mechanism() -> None:
    _table().require_governed_read(OWNER_DOMAIN, mechanism=None)


def test_exactly_four_integration_mechanisms_are_admissible() -> None:
    """ADR-070: the list is closed."""
    assert {m.value for m in INTEGRATION_MECHANISMS} == {
        "owned_api",
        "versioned_events",
        "governed_projection",
        "approved_read_contract",
    }


def test_no_prohibited_pattern_is_an_integration_mechanism() -> None:
    mechanism_values = {m.value for m in IntegrationMechanism}
    for pattern in ProhibitedAccessPattern:
        assert pattern.value not in mechanism_values
        with pytest.raises(CrossDomainDirectAccessDeniedError):
            reject_prohibited_access_pattern(pattern, context="integration")


def test_a_table_claimed_by_two_domains_is_refused() -> None:
    """`P13-DP-015`: no shared 'everything' schema."""
    with pytest.raises(CrossDomainDirectAccessDeniedError, match="claimed by both"):
        reject_shared_schema(
            {
                "membership-service": ["membership_record", "shared_contacts"],
                "finance-service": ["shared_contacts"],
            }
        )


def test_disjoint_ownership_passes() -> None:
    reject_shared_schema(
        {"membership-service": ["membership_record"], "finance-service": ["posting"]}
    )


# ---------------------------------------------------------------------------
# Audit ingestion
# ---------------------------------------------------------------------------


def _submission(payload: dict[str, str] | None = None) -> AuditSubmission:
    return AuditSubmission(
        submission_id=uid(8100),
        submitting_domain=OWNER_DOMAIN,
        actor=actor(),
        scope=scope(),
        action="membership.recorded",
        reason_code="MIGRATION_STARTED_RECORDED",
        submitted_at=NOW,
        payload=payload or {"aggregate_id": str(uid(1))},
    )


def test_a_submission_carries_a_typed_action_and_a_registered_reason_code() -> None:
    assert _submission().action
    assert _submission().reason_code


def test_a_submission_without_an_action_is_refused() -> None:
    with pytest.raises(AuditIngestionContractRequiredError):
        AuditSubmission(
            submission_id=uid(8100),
            submitting_domain=OWNER_DOMAIN,
            actor=actor(),
            scope=scope(),
            action="",
            reason_code="X_RECORDED",
            submitted_at=NOW,
            payload={},
        )


def test_a_submission_payload_passes_the_prohibited_key_guard() -> None:
    with pytest.raises(GlobalUserIdentifierProhibitedError):
        _submission({"person_id": "x"})


def test_no_non_owner_domain_credential_can_write_audit_persistence_directly() -> None:
    """The test §9 of the implementation task names, stated as its own
    sentence: *No non-owner domain credential can write directly to
    audit-core persistence.*"""
    with pytest.raises(AuditDirectWriteDeniedError):
        ApplicationCredential(domain=OWNER_DOMAIN, writable_schemas=frozenset({AUDIT_OWNER_DOMAIN}))


def test_the_audit_owners_own_credential_may_write_its_own_schema() -> None:
    credential = ApplicationCredential(
        domain=AUDIT_DOMAIN, writable_schemas=frozenset({AUDIT_OWNER_DOMAIN})
    )
    assert credential.can_write(AUDIT_OWNER_DOMAIN)


def test_a_non_owner_direct_write_attempt_is_refused_at_the_call_site_too() -> None:
    credential = ApplicationCredential(
        domain=OWNER_DOMAIN, writable_schemas=frozenset({"membership-service"})
    )
    with pytest.raises(AuditDirectWriteDeniedError, match="submission is not persistence"):
        reject_direct_audit_write(credential, target_schema=AUDIT_OWNER_DOMAIN)


def test_a_write_to_the_domains_own_schema_is_unaffected() -> None:
    credential = ApplicationCredential(
        domain=OWNER_DOMAIN, writable_schemas=frozenset({"membership-service"})
    )
    reject_direct_audit_write(credential, target_schema="membership-service")


def test_an_audit_record_arriving_outside_the_ingestion_port_is_refused() -> None:
    with pytest.raises(AuditIngestionContractRequiredError):
        require_ingestion_contract(arrived_via_port=False, context="bulk load")


def test_an_audit_record_arriving_through_the_port_is_accepted() -> None:
    require_ingestion_contract(arrived_via_port=True, context="ingestion port")


# ---------------------------------------------------------------------------
# Identity boundary
# ---------------------------------------------------------------------------


def test_the_four_identifier_kinds_stay_separate() -> None:
    """`P13-ID-002`."""
    assert {k.value for k in IdentifierKind} == {
        "account_reference",
        "person_reference",
        "membership_reference",
        "domain_subject_reference",
    }


def test_two_domains_references_never_correlate_even_with_equal_ids() -> None:
    left = ScopedSubjectReference(
        subject_id=uid(1), kind=IdentifierKind.DOMAIN_SUBJECT_REFERENCE, owning_domain=OWNER_DOMAIN
    )
    right = ScopedSubjectReference(
        subject_id=uid(1), kind=IdentifierKind.DOMAIN_SUBJECT_REFERENCE, owning_domain=OTHER_DOMAIN
    )
    assert not left.correlates_with(right)


def test_two_references_in_one_domain_and_kind_correlate() -> None:
    left = ScopedSubjectReference(
        subject_id=uid(1), kind=IdentifierKind.MEMBERSHIP_REFERENCE, owning_domain=OWNER_DOMAIN
    )
    assert left.correlates_with(left)


def test_two_kinds_in_one_domain_do_not_correlate() -> None:
    left = ScopedSubjectReference(
        subject_id=uid(1), kind=IdentifierKind.ACCOUNT_REFERENCE, owning_domain=OWNER_DOMAIN
    )
    right = ScopedSubjectReference(
        subject_id=uid(1), kind=IdentifierKind.PERSON_REFERENCE, owning_domain=OWNER_DOMAIN
    )
    assert not left.correlates_with(right)


def test_a_cross_domain_identity_join_is_refused() -> None:
    left = ScopedSubjectReference(
        subject_id=uid(1), kind=IdentifierKind.MEMBERSHIP_REFERENCE, owning_domain=OWNER_DOMAIN
    )
    right = ScopedSubjectReference(
        subject_id=uid(2), kind=IdentifierKind.ACCOUNT_REFERENCE, owning_domain=OTHER_DOMAIN
    )
    with pytest.raises(GlobalUserIdentifierProhibitedError):
        reject_cross_domain_identity_join(left, right)


def test_a_global_identifier_column_is_refused() -> None:
    """`P13-DP-008`, `P13-DP-016`."""
    with pytest.raises(GlobalUserIdentifierProhibitedError):
        reject_global_identifier_column(["id", "person_id"], table_name="membership_record")


def test_a_domain_scoped_column_set_passes() -> None:
    reject_global_identifier_column(
        ["membership_record_id", "organization_id"], table_name="membership_record"
    )


def test_the_identity_boundary_owner_is_established_by_pack_14() -> None:
    """`P13-ID-008`: PACK-13 assigns no owner and creates no schema."""
    assert IDENTITY_BOUNDARY is ReservedBoundary.IDENTITY
    assert IDENTITY_BOUNDARY_OWNER_ESTABLISHED_BY == "PACK-14"


# ---------------------------------------------------------------------------
# Voting boundary
# ---------------------------------------------------------------------------


def test_all_seven_voting_prohibitions_are_declared() -> None:
    assert len(VOTING_PROHIBITIONS) == 7
    assert VotingProhibition.NO_PERSON_TO_BALLOT_TABLE in VOTING_PROHIBITIONS
    assert VotingProhibition.NO_GLOBAL_ID_AS_VOTING_CLIENT_ID in VOTING_PROHIBITIONS


def test_no_ballot_content_reaches_the_general_plane() -> None:
    with pytest.raises(VotingMaterialProhibitedError):
        reject_voting_material({"ballot_content": "x"}, context="general event")


def test_no_person_to_ballot_relation_is_constructable() -> None:
    """`P13-VOTE-001`, `P13-VOTE-003`, `P13-DP-017`."""
    with pytest.raises(VotingMaterialProhibitedError, match="eligibility record with a ballot"):
        reject_ballot_linkage(
            left_column_names=["member_id"],
            right_column_names=["ballot_id"],
            relation_name="member_ballot",
        )


def test_an_identity_only_relation_is_not_a_ballot_linkage() -> None:
    reject_ballot_linkage(
        left_column_names=["member_id"],
        right_column_names=["organization_id"],
        relation_name="member_organization",
    )


def test_a_global_identifier_is_not_used_as_a_voting_client_identifier() -> None:
    """`P13-VOTE-007`."""
    with pytest.raises(GlobalUserIdentifierProhibitedError):
        reject_voting_client_identifier("member_id")


def test_a_scoped_identifier_may_be_a_voting_client_identifier() -> None:
    reject_voting_client_identifier("voting_client_session_reference")


def test_no_intermediate_tally_projection_exists() -> None:
    """`P13-VOTE-004`, `P13-VOTE-005`, FIR-INV-005."""
    with pytest.raises(VotingMaterialProhibitedError):
        reject_tally_projection("results-overview", projected_fields=["partial_tally"])


def test_an_ordinary_projection_is_unaffected() -> None:
    reject_tally_projection("membership-overview", projected_fields=["status", "organization_id"])


def test_pack_13_reserves_no_schema_space_for_the_voting_domain() -> None:
    """`P13-VOTE-011`."""
    assert VOTING_RESERVED_SCHEMA_OBJECTS == ()


def test_pack_13_decides_none_of_the_voting_topology_questions() -> None:
    """`P13-VOTE-008`: fixing them here would be deciding a security
    architecture from outside the pack that owns it."""
    deferred = set(VOTING_DECISIONS_DEFERRED_TO_PACK_15_16)
    assert "broker topics or topic naming" in deferred
    assert "connection-pool topology" in deferred
    assert "transport provider" in deferred
    assert "service names" in deferred


def test_no_module_imports_a_broker_client() -> None:
    """PACK-13 prescribes no transport provider (`P13-VOTE-008` for the
    voting plane, and no reason to prescribe one for the general plane
    either). A broker client reaching this package would be a topology
    decision arriving as an import.

    The scan is over *import statements*, not over prose: the package's
    own `__init__` names several broker products in order to say it
    deploys none of them, and a prose scan would flag that honest
    disclaimer while missing an actual dependency added under an alias."""
    forbidden = ("kafka", "rabbitmq", "nats", "pulsar", "boto3", "pika", "confluent")
    for path in sorted(SRC.rglob("*.py")):
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            stripped = line.strip().lower()
            if not (stripped.startswith("import ") or stripped.startswith("from ")):
                continue
            for name in forbidden:
                assert name not in stripped, f"{path.name}:{line_number} imports {name!r}"


# ---------------------------------------------------------------------------
# The forbidden delivery claim
# ---------------------------------------------------------------------------


def test_the_stronger_delivery_phrase_appears_nowhere_in_this_package() -> None:
    """ADR-072, `P13-DEL-002`: enforced by a scan, not by convention.

    The scan covers docstrings, comments, code and log-message strings
    alike, because the failure mode is a team *believing* it has the
    stronger guarantee — and a comment is where that belief would first
    appear."""
    offenders: list[str] = []
    for path in sorted(SRC.rglob("*.py")):
        text = path.read_text(encoding="utf-8").lower()
        for line_number, line in enumerate(text.splitlines(), start=1):
            if FORBIDDEN_DELIVERY_CLAIM in line and "forbidden_delivery_claim" not in line:
                offenders.append(f"{path.name}:{line_number}")
    assert offenders == [], f"the forbidden delivery claim appears at: {offenders}"


def test_the_scan_would_actually_catch_the_phrase() -> None:
    """A scan that could never fail proves nothing, so the matching
    itself is exercised against a synthetic line."""
    assert FORBIDDEN_DELIVERY_CLAIM in "we provide exactly-once delivery".lower()


def test_every_production_readiness_mention_is_a_denial() -> None:
    """FIR-INV-015: no production-readiness claim and no legal-activation
    claim is made by this round.

    The package does mention both phrases — it has to, in order to deny
    them — so the assertion is not that the words are absent but that
    every occurrence is negated. A bare occurrence would be a claim."""
    phrases = ("production ready", "production-ready", "legally activated", "legal activation")
    for path in sorted(SRC.rglob("*.py")):
        lowered = path.read_text(encoding="utf-8").lower()
        for phrase in phrases:
            start = 0
            while (index := lowered.find(phrase, start)) != -1:
                preceding = lowered[max(0, index - 60) : index]
                negations = ("no ", "not ", "nothing", "never", "neither", "without")
                assert any(token in preceding for token in negations), (
                    f"{path.name} mentions {phrase!r} without negating it: "
                    f"...{lowered[max(0, index - 40) : index + len(phrase)]}"
                )
                start = index + len(phrase)
