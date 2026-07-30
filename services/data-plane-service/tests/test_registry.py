"""The canonical schema registry (PACK-13 §12; ADR-073).

Lifecycle, ownership, digest canonicalization, the digest/version
separation, duplicate-content review, justified republication,
deprecation and supersession.
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from _data_plane_builders import (
    BASE_EXAMPLE,
    BASE_SCHEMA,
    NOW,
    OWNER_DOMAIN,
    actor,
    canonical,
    classification,
    definition,
    evidence,
    family,
    owner,
    uid,
)

from epd2_data_plane_service.canonicalization import SchemaFormat, canonicalize
from epd2_data_plane_service.domain import DomainReference
from epd2_data_plane_service.exceptions import (
    SchemaDigestMismatchError,
    SchemaDuplicateContentError,
    SchemaDuplicateContentReviewRequiredError,
    SchemaExamplesInvalidError,
    SchemaGovernanceJustificationMissingError,
    SchemaLifecycleTransitionForbiddenError,
    SchemaNotApprovedError,
    SchemaOwnerMissingError,
    SchemaRetiredError,
    SchemaVersionIdentityImmutableError,
)
from epd2_data_plane_service.registry import (
    SCHEMA_LIFECYCLE_TRANSITIONS,
    CompatibilityMode,
    ConsumerRegistration,
    DuplicateContentDisposition,
    RegistryAvailability,
    SchemaDeprecation,
    SchemaLifecycleState,
    SchemaOwner,
    SchemaPublicationDecision,
    SchemaSupersession,
    SchemaVersion,
    assess_consumer_readiness,
    assess_duplicate_content,
    reject_version_identity_rewrite,
    require_duplicate_content_admissible,
)


def _decision(
    *,
    justification: str | None = None,
    disposition: DuplicateContentDisposition | None = None,
) -> SchemaPublicationDecision:
    return SchemaPublicationDecision(
        publication_decision_id=uid(500),
        decided_by=actor(2),
        decided_at=NOW,
        evidence=evidence(),
        governance_justification=justification,
        duplicate_content_disposition=disposition,
    )


def _version(
    *,
    n: int = 1,
    digest: str | None = None,
    state: SchemaLifecycleState = SchemaLifecycleState.APPROVED,
    decision: SchemaPublicationDecision | None = None,
) -> SchemaVersion:
    return SchemaVersion(
        schema_version_id=uid(600 + n),
        family=family(),
        version_label=f"1.{n}.0",
        content_digest=digest or canonical().digest,
        lifecycle_state=state,
        classification=classification(),
        publication_decision=decision or _decision(),
    )


# ---------------------------------------------------------------------------
# Ownership
# ---------------------------------------------------------------------------


def test_a_schema_owner_requires_an_accountable_domain_role() -> None:
    with pytest.raises(SchemaOwnerMissingError):
        SchemaOwner(domain=OWNER_DOMAIN, accountable_role="")


def test_a_reserved_boundary_cannot_own_a_schema() -> None:
    from epd2_data_plane_service.exceptions import ReservedBoundarySchemaProhibitedError

    reserved = DomainReference(domain_name="future_voting_domain", is_reserved_boundary=True)
    with pytest.raises(ReservedBoundarySchemaProhibitedError):
        SchemaOwner(domain=reserved, accountable_role="steward")


def test_the_owner_is_a_domain() -> None:
    assert owner().domain.domain_name == OWNER_DOMAIN.domain_name


# ---------------------------------------------------------------------------
# Definition and fixtures
# ---------------------------------------------------------------------------


def test_example_fixtures_are_mandatory() -> None:
    with pytest.raises(SchemaExamplesInvalidError):
        definition(examples=())


def test_a_definition_refuses_a_format_that_is_not_its_familys() -> None:
    with pytest.raises(SchemaDigestMismatchError):
        definition(fam=family(schema_format=SchemaFormat.OPENAPI))


def test_a_definition_with_a_valid_fixture_constructs() -> None:
    assert definition(examples=[BASE_EXAMPLE]).canonical_content.digest


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------


def test_every_declared_transition_is_permitted_and_nothing_else_is() -> None:
    for state, permitted in SCHEMA_LIFECYCLE_TRANSITIONS.items():
        version = _version(state=state)
        for target in SchemaLifecycleState:
            if target in permitted:
                assert version.with_state(target).lifecycle_state is target
            else:
                with pytest.raises(SchemaLifecycleTransitionForbiddenError):
                    version.with_state(target)


def test_retired_and_superseded_are_terminal_but_not_deleted() -> None:
    """`P13-REG-004`: a historical event validated against a retired
    schema must remain interpretable."""
    assert SCHEMA_LIFECYCLE_TRANSITIONS[SchemaLifecycleState.RETIRED] == frozenset()
    assert SCHEMA_LIFECYCLE_TRANSITIONS[SchemaLifecycleState.SUPERSEDED] == frozenset()
    retired = _version(state=SchemaLifecycleState.RETIRED)
    assert retired.content_digest


def test_a_retired_version_is_refused_for_new_traffic() -> None:
    with pytest.raises(SchemaRetiredError):
        _version(state=SchemaLifecycleState.RETIRED).usable_for_new_traffic()


def test_a_draft_version_is_refused_for_traffic() -> None:
    with pytest.raises(SchemaNotApprovedError):
        _version(state=SchemaLifecycleState.DRAFT).usable_for_new_traffic()


def test_active_and_deprecated_versions_serve_traffic() -> None:
    _version(state=SchemaLifecycleState.ACTIVE).usable_for_new_traffic()
    _version(state=SchemaLifecycleState.DEPRECATED).usable_for_new_traffic()


# ---------------------------------------------------------------------------
# Digest and version identity
# ---------------------------------------------------------------------------


def test_the_seven_governance_fields_are_separate_from_the_digest() -> None:
    """§12.3 and the implementation task's §7.4 require these to stay
    distinct; each is separately readable here."""
    version = _version(decision=_decision(justification="re-issue under a new effective date"))
    assert version.content_digest != str(version.schema_version_id)
    assert version.publication_decision_id == uid(500)
    assert version.governance_justification == "re-issue under a new effective date"
    assert version.deprecated_at is None
    assert version.supersession_reference is None
    assert version.effective_at is None


def test_a_content_digest_must_be_a_sha256_hex_digest() -> None:
    with pytest.raises(SchemaDigestMismatchError):
        _version(digest="short")


def test_identical_content_without_intent_is_blocked() -> None:
    existing = _version()
    assessment = assess_duplicate_content(
        submitted_digest=existing.content_digest,
        existing_versions=[existing],
        governance_justification=None,
        intentional_republication=False,
    )
    assert assessment is not None
    assert assessment.disposition is DuplicateContentDisposition.BLOCKED
    assert assessment.reason_code == "SCHEMA_DUPLICATE_CONTENT"
    with pytest.raises(SchemaDuplicateContentError):
        require_duplicate_content_admissible(assessment, context="family")


def test_intentional_republication_without_justification_requires_review() -> None:
    existing = _version()
    assessment = assess_duplicate_content(
        submitted_digest=existing.content_digest,
        existing_versions=[existing],
        governance_justification=None,
        intentional_republication=True,
    )
    assert assessment is not None
    assert assessment.reason_code == "SCHEMA_DUPLICATE_CONTENT_REVIEW_REQUIRED"
    with pytest.raises(SchemaDuplicateContentReviewRequiredError):
        require_duplicate_content_admissible(assessment, context="family")


def test_justified_republication_is_approved_and_carries_its_justification() -> None:
    existing = _version()
    assessment = assess_duplicate_content(
        submitted_digest=existing.content_digest,
        existing_versions=[existing],
        governance_justification="corrected ownership assignment",
        intentional_republication=True,
    )
    assert assessment is not None
    assert assessment.reason_code == "SCHEMA_IDENTICAL_CONTENT_REPUBLICATION_APPROVED"
    assert assessment.governance_justification == "corrected ownership assignment"
    require_duplicate_content_admissible(assessment, context="family")


def test_new_content_produces_no_duplicate_assessment_at_all() -> None:
    other = canonicalize(SchemaFormat.JSON_SCHEMA, {"type": "object", "properties": {}})
    assert (
        assess_duplicate_content(
            submitted_digest=other.digest,
            existing_versions=[_version()],
            governance_justification=None,
            intentional_republication=False,
        )
        is None
    )


def test_no_duplicate_branch_creates_a_new_version_identity_automatically() -> None:
    """`P13-REG-005c`: `schema_version_id` is established by a
    publication decision, never derived from digest equality."""
    existing = _version()
    for intentional, justification in ((False, None), (True, None), (True, "justified")):
        assessment = assess_duplicate_content(
            submitted_digest=existing.content_digest,
            existing_versions=[existing],
            governance_justification=justification,
            intentional_republication=intentional,
        )
        assert assessment is not None
        assert assessment.matching_version_id == existing.schema_version_id


def test_a_historical_version_identity_is_never_re_pointed() -> None:
    with pytest.raises(SchemaVersionIdentityImmutableError):
        reject_version_identity_rewrite(
            existing_version_id=uid(601), proposed_version_id=uid(601), context="republication"
        )


def test_a_genuinely_new_identity_is_admitted() -> None:
    reject_version_identity_rewrite(
        existing_version_id=uid(601), proposed_version_id=uid(602), context="republication"
    )


def test_a_republication_decision_without_justification_is_refused() -> None:
    with pytest.raises(SchemaGovernanceJustificationMissingError):
        _decision(disposition=DuplicateContentDisposition.REPUBLICATION_APPROVED)


# ---------------------------------------------------------------------------
# Deprecation, supersession, consumers
# ---------------------------------------------------------------------------


def test_a_deprecation_window_ends_after_it_begins() -> None:
    with pytest.raises(ValueError, match="must end after"):
        SchemaDeprecation(
            deprecated_at=NOW,
            coexistence_ends_at=NOW,
            replacement_version_id=uid(602),
            reason_code="SCHEMA_RETIRED",
        )


def test_supersession_points_forward_and_never_rewrites_the_old_version() -> None:
    supersession = SchemaSupersession(
        superseding_version_id=uid(603), superseded_at=NOW, reason_code="SCHEMA_RETIRED"
    )
    assert supersession.superseding_version_id == uid(603)
    assert not hasattr(supersession, "superseded_version_id_overwrite")


def test_consumer_readiness_distinguishes_migrated_from_not() -> None:
    fam = family()
    ready = ConsumerRegistration(
        consumer_id=uid(700),
        consumer_name="search-projection",
        consumer_domain=OWNER_DOMAIN,
        family_id=fam.family_id,
        supported_version_ids=(uid(601),),
        registered_at=NOW,
        migrated_to_version_id=uid(601),
    )
    lagging = ConsumerRegistration(
        consumer_id=uid(701),
        consumer_name="finance-projection",
        consumer_domain=OWNER_DOMAIN,
        family_id=fam.family_id,
        supported_version_ids=(uid(600),),
        registered_at=NOW,
    )
    readiness = assess_consumer_readiness(
        family_id=fam.family_id, target_version_id=uid(601), registrations=[ready, lagging]
    )
    assert readiness.ready_consumer_ids == (uid(700),)
    assert readiness.not_ready_consumer_ids == (uid(701),)
    assert not readiness.all_ready


def test_readiness_states_that_it_can_only_speak_for_registered_consumers() -> None:
    """`P13-REG-009`: an unregistered consumer receives no compatibility
    protection, and the readiness answer states its own limit."""
    readiness = assess_consumer_readiness(
        family_id=uid(1), target_version_id=uid(2), registrations=[]
    )
    assert readiness.all_ready
    assert readiness.unregistered_consumers_are_unprotected


def test_an_unreachable_registry_must_carry_its_reason_code() -> None:
    with pytest.raises(ValueError, match="reason code"):
        RegistryAvailability(reachable=False, checked_at=NOW)


def test_an_unreachable_registry_blocks_publication_by_construction() -> None:
    availability = RegistryAvailability(
        reachable=False, checked_at=NOW, unreachable_reason_code="SCHEMA_REGISTRY_UNAVAILABLE"
    )
    assert not availability.reachable


def test_a_family_declares_exactly_one_compatibility_mode() -> None:
    assert family(mode=CompatibilityMode.FULL).compatibility_mode is CompatibilityMode.FULL


def test_a_deprecated_version_exposes_its_deprecation_date() -> None:
    version = _version(state=SchemaLifecycleState.ACTIVE)
    from dataclasses import replace

    deprecated = replace(
        version,
        deprecation=SchemaDeprecation(
            deprecated_at=NOW,
            coexistence_ends_at=NOW + timedelta(days=90),
            replacement_version_id=uid(602),
            reason_code="SCHEMA_RETIRED",
        ),
    )
    assert deprecated.deprecated_at == NOW


def test_the_base_schema_fixture_canonicalizes_stably() -> None:
    assert canonicalize(SchemaFormat.JSON_SCHEMA, BASE_SCHEMA).digest == canonical().digest
