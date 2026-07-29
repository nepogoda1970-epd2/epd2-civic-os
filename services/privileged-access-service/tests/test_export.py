"""Governed export (`P12-EXP-*`, `P12-VOTE-*`, ADR-066)."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from epd2_privileged_access_service.classification import (
    SourceClassification,
    resolve_classification,
)
from epd2_privileged_access_service.domain import (
    OrganizationalScopeRef,
    Purpose,
    PurposeBinding,
)
from epd2_privileged_access_service.exceptions import (
    AdminPrivilegeInsufficientError,
    ArtifactExpiredError,
    ArtifactRevokedError,
    BulkExtractionNotAuthorizedError,
    DlpAccessLimitExceededError,
    ExportBallotContentProhibitedError,
    ExportManifestMismatchError,
    ExportOrganizationMismatchError,
    ExportUncertifiedResultProhibitedError,
    FieldNotExportableError,
    ForbiddenTransitionError,
    LegalHoldNotAuthorizationError,
    RecipientNotAuthorizedError,
    ResultPublicationNotOwnedError,
    SearchPermissionInsufficientError,
    SourceRecordRevokedError,
    TransferChannelProhibitedError,
)
from epd2_privileged_access_service.export import (
    DatasetItemReference,
    DatasetManifest,
    ExportArtifact,
    ExportRequest,
    ExportScope,
    ExportState,
    Recipient,
    RecipientCategory,
    RecipientObligation,
    TransferChannel,
    assert_certified_result_not_exported,
    assert_cross_scope_basis,
    assert_export_authority,
    assert_hold_is_not_authorization,
    assert_recipient_eligible,
    assert_source_records_current,
    build_artifact,
    permitted_field_set,
)
from epd2_privileged_access_service.policy import REFERENCE_POLICY

T0 = datetime(2026, 3, 1, 9, 0, tzinfo=UTC)
SCOPE = OrganizationalScopeRef(organization_id=uuid4())
INTERNAL = resolve_classification(SourceClassification.INTERNAL)
RESTRICTED = resolve_classification(SourceClassification.HIGHLY_CONFIDENTIAL)


def _obligation() -> RecipientObligation:
    return RecipientObligation(
        retention_limit=timedelta(days=30),
        resharing_permitted=False,
        destruction_required=True,
        obligation_reference="obligation:1",
    )


def _recipient(
    category: RecipientCategory = RecipientCategory.INTERNAL_SAME_SCOPE,
    scope: OrganizationalScopeRef = SCOPE,
) -> Recipient:
    return Recipient(
        recipient_reference="recipient:1",
        category=category,
        organization_scope=scope,
        obligation=_obligation(),
    )


def _request(**overrides: object) -> ExportRequest:
    base: dict[str, object] = {
        "export_id": uuid4(),
        "requester_reference": "actor:requester",
        "purpose": PurposeBinding(
            purpose=Purpose.DATA_SUBJECT_REQUEST,
            justification_reference="j",
            basis_reference="basis:1",
        ),
        "scope": ExportScope(
            domains=frozenset({"membership"}),
            record_classes=frozenset({"membership_record"}),
            organization_scope=SCOPE,
        ),
        "requested_fields": frozenset({"title"}),
        "requested_format": "csv",
        "recipient": _recipient(),
        "transfer_channel": TransferChannel.PLATFORM_DOWNLOAD,
        "requested_at": T0,
        "data_owner_reference": "actor:owner",
    }
    base.update(overrides)
    return ExportRequest(**base)  # type: ignore[arg-type]


def _manifest(export_id: object, fields: frozenset[str] = frozenset({"title"})) -> DatasetManifest:
    return DatasetManifest(
        manifest_id=uuid4(),
        export_id=export_id,  # type: ignore[arg-type]
        items=(
            DatasetItemReference(
                record_reference="rec:1",
                domain="membership",
                classification=INTERNAL,
                content_digest="a" * 64,
            ),
        ),
        permitted_fields=fields,
        policy_version=REFERENCE_POLICY.policy_version,
        classification_mapping_version=INTERNAL.mapping_version,
        generated_at=T0,
    )


class TestExportAuthority:
    def test_only_data_owner_plus_a_distinct_approver_authorises(self) -> None:
        """`P12-EXP-002`, `P12-EXP-004`..`006`: export authority derives
        from the data owner for the record class plus a distinct
        approver, and from nothing else."""
        assert_export_authority(
            has_search_permission=False,
            has_read_permission=False,
            has_admin_privilege=False,
            has_data_owner_authority=True,
            has_approver=True,
        )

    def test_an_approval_alone_is_not_authority(self) -> None:
        with pytest.raises(AdminPrivilegeInsufficientError):
            assert_export_authority(
                has_search_permission=False,
                has_read_permission=False,
                has_admin_privilege=False,
                has_data_owner_authority=False,
                has_approver=True,
            )

    def test_search_permission_is_not_export_permission(self) -> None:
        """The most tempting of the three substitutions: a caller who can
        find a record assumes they can extract it."""
        with pytest.raises(SearchPermissionInsufficientError):
            assert_export_authority(
                has_search_permission=True,
                has_read_permission=True,
                has_admin_privilege=True,
                has_data_owner_authority=False,
                has_approver=True,
            )

    def test_read_permission_is_not_bulk_export_permission(self) -> None:
        with pytest.raises(BulkExtractionNotAuthorizedError):
            assert_export_authority(
                has_search_permission=False,
                has_read_permission=True,
                has_admin_privilege=True,
                has_data_owner_authority=False,
                has_approver=True,
            )

    def test_administrative_privilege_is_not_data_ownership(self) -> None:
        with pytest.raises(AdminPrivilegeInsufficientError):
            assert_export_authority(
                has_search_permission=False,
                has_read_permission=False,
                has_admin_privilege=True,
                has_data_owner_authority=False,
                has_approver=True,
            )

    def test_a_legal_hold_is_never_an_authorization(self) -> None:
        """A hold can only ever block. Reading it as permission is a
        specific, tempting error, so it has its own refusal."""
        with pytest.raises(LegalHoldNotAuthorizationError):
            assert_hold_is_not_authorization(under_legal_hold=True, has_export_authority=False)


class TestRecipients:
    def test_the_taxonomy_is_closed_and_has_no_generic_external(self) -> None:
        """`OD-P12-07`: "external" is not a category an obligation can be
        attached to."""
        values = {c.value for c in RecipientCategory}
        assert "external" not in values
        assert len(values) == 5

    def test_a_public_recipient_never_receives_restricted_material(self) -> None:
        with pytest.raises(RecipientNotAuthorizedError):
            assert_recipient_eligible(
                _recipient(RecipientCategory.PUBLIC_AUTHORITATIVE_RELEASE),
                [RESTRICTED],
            )

    def test_an_eligible_pairing_passes(self) -> None:
        assert_recipient_eligible(_recipient(), [INTERNAL])

    def test_a_channel_the_category_does_not_permit_is_refused(self) -> None:
        with pytest.raises(TransferChannelProhibitedError):
            _request(
                recipient=_recipient(RecipientCategory.INTERNAL_SAME_SCOPE),
                transfer_channel=TransferChannel.AUTHORITATIVE_PUBLICATION,
            )

    def test_a_cross_scope_export_requires_a_recorded_basis(self) -> None:
        other = OrganizationalScopeRef(organization_id=uuid4())
        request = _request(recipient=_recipient(RecipientCategory.INTERNAL_CROSS_SCOPE, other))
        with pytest.raises(ExportOrganizationMismatchError):
            assert_cross_scope_basis(
                _request(recipient=_recipient(RecipientCategory.INTERNAL_SAME_SCOPE, other)),
                cross_scope_basis_reference="basis:cross-1",
            )
        with pytest.raises(ExportOrganizationMismatchError):
            assert_cross_scope_basis(request, cross_scope_basis_reference=None)
        assert_cross_scope_basis(request, cross_scope_basis_reference="basis:cross-1")


class TestVotingBoundary:
    def test_a_certified_result_is_released_by_its_owner_not_by_export(self) -> None:
        """`P12-VOTE-005`: the authoritative artifact is the publication
        rendition the voting domain issues. An export copy that looked
        authoritative would be a second source of truth for a result."""
        with pytest.raises(ResultPublicationNotOwnedError):
            assert_certified_result_not_exported(domain="certified_result", is_certified=True)

    def test_an_uncertified_result_gets_its_own_distinct_refusal(self) -> None:
        """`P12-VOTE-006`: "not yours to publish" and "not yet a result"
        are different facts and must not share a reason code."""
        with pytest.raises(ExportUncertifiedResultProhibitedError):
            assert_certified_result_not_exported(domain="voting_result", is_certified=False)

    def test_prohibited_tier_material_reaches_no_recipient_category(self) -> None:
        prohibited = resolve_classification(SourceClassification.ABSOLUTELY_EXCLUDED)
        for category in RecipientCategory:
            with pytest.raises(ExportBallotContentProhibitedError):
                assert_recipient_eligible(_recipient(category), [prohibited])


class TestFieldSelection:
    def test_a_fully_permitted_request_passes_unchanged(self) -> None:
        permitted = permitted_field_set(
            frozenset({"title", "notes"}),
            class_fields=frozenset({"title", "notes", "extra"}),
            purpose_fields=frozenset({"title", "notes"}),
            recipient_denied=frozenset(),
        )
        assert permitted == frozenset({"title", "notes"})

    @pytest.mark.parametrize(
        ("class_fields", "purpose_fields", "denied"),
        [
            (frozenset({"title"}), frozenset({"title", "notes"}), frozenset()),
            (frozenset({"title", "notes"}), frozenset({"title"}), frozenset()),
            (frozenset({"title", "notes"}), frozenset({"title", "notes"}), frozenset({"notes"})),
        ],
        ids=["class-policy", "purpose", "recipient"],
    )
    def test_each_stage_refuses_rather_than_silently_dropping(
        self,
        class_fields: frozenset[str],
        purpose_fields: frozenset[str],
        denied: frozenset[str],
    ) -> None:
        """`P12-EXP-008`: a field the caller asked for and did not get is
        a refusal, not a quiet omission. Silent dropping is how an
        operator comes to believe an export contained something it never
        did."""
        with pytest.raises(FieldNotExportableError):
            permitted_field_set(
                frozenset({"title", "notes"}),
                class_fields=class_fields,
                purpose_fields=purpose_fields,
                recipient_denied=denied,
            )

    def test_the_artifact_selects_rather_than_strips(self) -> None:
        """`P12-EXP-008`: a row assembled whole and then stripped has
        existed whole, and something that has existed whole can leak
        whole."""
        request = _request()
        manifest = _manifest(request.export_id)
        artifact = build_artifact(
            request,
            [{"title": "Board minutes", "home_address": "somewhere"}],
            manifest=manifest,
            artifact_id=uuid4(),
            at=T0,
            policy=REFERENCE_POLICY,
        )
        assert artifact.projection == ({"title": "Board minutes"},)


class TestArtifact:
    def _artifact(self, **overrides: object) -> ExportArtifact:
        request = _request()
        manifest = _manifest(request.export_id)
        artifact = build_artifact(
            request,
            [{"title": "Board minutes"}],
            manifest=manifest,
            artifact_id=uuid4(),
            at=T0,
            policy=REFERENCE_POLICY,
        )
        return replace(artifact, **overrides)  # type: ignore[arg-type]

    def test_an_export_artifact_is_never_authoritative(self) -> None:
        """An export is a copy taken under a purpose; the authoritative
        record stays where it lives."""
        assert self._artifact().is_authoritative is False

    def test_expiry_is_enforced_against_the_policy_window(self) -> None:
        artifact = self._artifact()
        artifact.assert_accessible(at=T0, policy=REFERENCE_POLICY)
        with pytest.raises(ArtifactExpiredError):
            artifact.assert_accessible(
                at=T0 + REFERENCE_POLICY.export_artifact_expiry + timedelta(days=1),
                policy=REFERENCE_POLICY,
            )

    def test_revocation_blocks_further_access(self) -> None:
        with pytest.raises(ArtifactRevokedError):
            self._artifact().with_revocation().assert_accessible(at=T0, policy=REFERENCE_POLICY)

    def test_the_access_ceiling_is_part_of_the_artifact(self) -> None:
        """The count cannot be reset by clearing a log elsewhere."""
        artifact = self._artifact(access_count=REFERENCE_POLICY.export_access_limit)
        with pytest.raises(DlpAccessLimitExceededError):
            artifact.assert_accessible(at=T0, policy=REFERENCE_POLICY)

    def test_a_manifest_from_another_export_is_detected(self) -> None:
        artifact = self._artifact()
        foreign = replace(artifact, export_id=uuid4())
        with pytest.raises(ExportManifestMismatchError):
            foreign.verify_manifest()

    def test_a_row_count_that_disagrees_with_the_manifest_is_detected(self) -> None:
        """A manifest that no longer describes the artifact is a manifest
        that proves nothing."""
        artifact = self._artifact()
        artifact.verify_manifest()
        padded = replace(
            artifact,
            projection=(*artifact.projection, {"title": "An extra row"}),
        )
        with pytest.raises(ExportManifestMismatchError):
            padded.verify_manifest()


class TestSourceCurrency:
    def test_a_revoked_source_record_blocks_generation(self) -> None:
        with pytest.raises(SourceRecordRevokedError):
            assert_source_records_current(
                revoked_references=frozenset({"rec:1"}),
                requested_references=frozenset({"rec:1", "rec:2"}),
            )
        assert_source_records_current(
            revoked_references=frozenset({"rec:9"}),
            requested_references=frozenset({"rec:1"}),
        )


class TestLifecycle:
    def test_an_undeclared_transition_is_refused(self) -> None:
        with pytest.raises(ForbiddenTransitionError):
            _request().with_state(ExportState.DELIVERED, action="skip")

    def test_the_declared_path_is_walkable(self) -> None:
        request = _request()
        for state in (
            ExportState.DLP_ASSESSMENT,
            ExportState.DISCLOSURE_ASSESSMENT,
            ExportState.APPROVED,
            ExportState.ARTIFACT_GENERATED,
            ExportState.DELIVERED,
            ExportState.DESTRUCTION_ATTESTED,
        ):
            request = request.with_state(state, action="step")
        assert request.state is ExportState.DESTRUCTION_ATTESTED
