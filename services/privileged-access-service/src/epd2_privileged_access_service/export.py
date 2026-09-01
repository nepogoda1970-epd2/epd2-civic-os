"""Bounded context 3 of 3 - governed data export (ADR-066).

Export is where data leaves the trust boundary. Every control in every
earlier pack applies to data inside the system; export is the moment they
stop applying, which is what makes it a governed object rather than a
download (`P12-EXP-001`).

```text
requested -> dlp_assessment -> disclosure_assessment -> approved | denied
          -> artifact_generated -> delivered -> accessed*
          -> expired | revoked -> destruction_attested
```

Five decisions carry most of the weight:

- **Authority is never inherited.** Search permission is not export
  permission, read permission is not bulk-export permission, and
  administrative privilege is not export authority (`P12-EXP-004`,
  `P12-EXP-005`, `P12-EXP-006`).
- **Denied fields never reach the artifact.** `build_artifact` computes
  the permitted field set first and projects only those fields; there is
  no path that generates the full row and filters afterwards
  (`P12-EXP-008`).
- **Every artifact expires** and every access is audited.
- **Revocation is not deletion** (`P12-EXP-013`). `revoke` withdraws
  authorization and blocks further platform-mediated access. It does not
  reach a copy the recipient already holds, and no docstring, field name
  or reason code in this module says otherwise.
- **Each export is formed against current state** (`P12-EXP-019`): the
  policy version and the authorization are re-resolved at generation.

Voting material: ballot-level and intermediate, partial or non-certified
tally material is never exportable (`P12-VOTE-001`). A final **certified**
result is not prohibited - but it is released by the authoritative voting
and result-certification domain through an approved publication
rendition, never through this pipeline (`P12-VOTE-004`,
`P12-VOTE-005`).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from enum import StrEnum
from uuid import UUID

from epd2_privileged_access_service.classification import (
    ClassificationDecision,
    EnforcementTier,
)
from epd2_privileged_access_service.domain import (
    OrganizationalScopeRef,
    PurposeBinding,
    deterministic_digest,
    reject_prohibited_payload_keys,
    require_text,
    require_timezone,
)
from epd2_privileged_access_service.exceptions import (
    AdminPrivilegeInsufficientError,
    ArtifactExpiredError,
    ArtifactRevokedError,
    BulkExtractionNotAuthorizedError,
    DlpAccessLimitExceededError,
    ExportBallotContentProhibitedError,
    ExportManifestMismatchError,
    ExportManifestMissingError,
    ExportOrganizationMismatchError,
    ExportPurposeMissingError,
    ExportSelfApprovalProhibitedError,
    ExportUncertifiedResultProhibitedError,
    FieldNotExportableError,
    ForbiddenTransitionError,
    LegalHoldNotAuthorizationError,
    RecipientNotAuthorizedError,
    RecipientObligationMissingError,
    ResultPublicationNotOwnedError,
    SearchPermissionInsufficientError,
    SourceRecordRevokedError,
    TransferChannelProhibitedError,
    UnknownStatusError,
)
from epd2_privileged_access_service.policy import PrivilegedAccessPolicy
from epd2_privileged_access_service.search import (
    ABSOLUTELY_EXCLUDED_DOMAINS,
    UNCERTIFIED_RESULT_DOMAINS,
)


class ExportState(StrEnum):
    REQUESTED = "requested"
    DLP_ASSESSMENT = "dlp_assessment"
    DISCLOSURE_ASSESSMENT = "disclosure_assessment"
    APPROVED = "approved"
    DENIED = "denied"
    ARTIFACT_GENERATED = "artifact_generated"
    DELIVERED = "delivered"
    EXPIRED = "expired"
    REVOKED = "revoked"
    DESTRUCTION_ATTESTED = "destruction_attested"


_ALLOWED_TRANSITIONS: frozenset[tuple[ExportState, ExportState]] = frozenset(
    {
        (ExportState.REQUESTED, ExportState.DLP_ASSESSMENT),
        (ExportState.DLP_ASSESSMENT, ExportState.DISCLOSURE_ASSESSMENT),
        (ExportState.DLP_ASSESSMENT, ExportState.DENIED),
        (ExportState.DISCLOSURE_ASSESSMENT, ExportState.APPROVED),
        (ExportState.DISCLOSURE_ASSESSMENT, ExportState.DENIED),
        (ExportState.APPROVED, ExportState.ARTIFACT_GENERATED),
        (ExportState.APPROVED, ExportState.REVOKED),
        (ExportState.ARTIFACT_GENERATED, ExportState.DELIVERED),
        (ExportState.ARTIFACT_GENERATED, ExportState.REVOKED),
        (ExportState.DELIVERED, ExportState.EXPIRED),
        (ExportState.DELIVERED, ExportState.REVOKED),
        (ExportState.DELIVERED, ExportState.DESTRUCTION_ATTESTED),
        (ExportState.EXPIRED, ExportState.DESTRUCTION_ATTESTED),
        (ExportState.REVOKED, ExportState.DESTRUCTION_ATTESTED),
    }
)


class RecipientCategory(StrEnum):
    """The closed recipient taxonomy (resolution of `OD-P12-07`).

    Deliberately closed and deliberately without a generic `external`:
    "external" is not a category an obligation can be attached to, and a
    recipient whose category nobody chose is a recipient whose controls
    nobody chose."""

    INTERNAL_SAME_SCOPE = "internal_same_scope"
    INTERNAL_CROSS_SCOPE = "internal_cross_scope"
    INDEPENDENT_OVERSIGHT = "independent_oversight"
    REGULATED_EXTERNAL = "regulated_external"
    PUBLIC_AUTHORITATIVE_RELEASE = "public_authoritative_release"


#: Which tiers each recipient category may ever receive. The public row
#: is the important one: highly confidential material never reaches a
#: public recipient, whatever purpose is declared.
_RECIPIENT_TIER_ELIGIBILITY: dict[RecipientCategory, frozenset[EnforcementTier]] = {
    RecipientCategory.INTERNAL_SAME_SCOPE: frozenset(
        {
            EnforcementTier.T0_OPEN,
            EnforcementTier.T0_OPEN_AUTHORITATIVE,
            EnforcementTier.T1_INTERNAL,
            EnforcementTier.T1_DERIVED,
            EnforcementTier.T2_CONFIDENTIAL,
            EnforcementTier.T2_CASE_METADATA,
            EnforcementTier.T3_RESTRICTED,
        }
    ),
    RecipientCategory.INTERNAL_CROSS_SCOPE: frozenset(
        {
            EnforcementTier.T0_OPEN,
            EnforcementTier.T0_OPEN_AUTHORITATIVE,
            EnforcementTier.T1_INTERNAL,
            EnforcementTier.T1_DERIVED,
            EnforcementTier.T2_CONFIDENTIAL,
            EnforcementTier.T2_CASE_METADATA,
        }
    ),
    RecipientCategory.INDEPENDENT_OVERSIGHT: frozenset(
        {
            EnforcementTier.T0_OPEN,
            EnforcementTier.T0_OPEN_AUTHORITATIVE,
            EnforcementTier.T1_INTERNAL,
            EnforcementTier.T1_DERIVED,
            EnforcementTier.T2_CONFIDENTIAL,
            EnforcementTier.T2_CASE_METADATA,
            EnforcementTier.T3_RESTRICTED,
        }
    ),
    RecipientCategory.REGULATED_EXTERNAL: frozenset(
        {
            EnforcementTier.T0_OPEN,
            EnforcementTier.T0_OPEN_AUTHORITATIVE,
            EnforcementTier.T1_INTERNAL,
            EnforcementTier.T2_CONFIDENTIAL,
            EnforcementTier.T2_CASE_METADATA,
        }
    ),
    RecipientCategory.PUBLIC_AUTHORITATIVE_RELEASE: frozenset(
        {EnforcementTier.T0_OPEN, EnforcementTier.T0_OPEN_AUTHORITATIVE}
    ),
}

#: Categories that require an explicit legal or organizational basis.
BASIS_REQUIRED_CATEGORIES: frozenset[RecipientCategory] = frozenset(
    {
        RecipientCategory.INTERNAL_CROSS_SCOPE,
        RecipientCategory.REGULATED_EXTERNAL,
        RecipientCategory.PUBLIC_AUTHORITATIVE_RELEASE,
    }
)

#: Categories that require a destruction attestation on completion.
ATTESTATION_REQUIRED_CATEGORIES: frozenset[RecipientCategory] = frozenset(
    {RecipientCategory.REGULATED_EXTERNAL}
)


class TransferChannel(StrEnum):
    PLATFORM_DOWNLOAD = "platform_download"
    GOVERNED_TRANSFER = "governed_transfer"
    AUTHORITATIVE_PUBLICATION = "authoritative_publication"


_CHANNEL_ELIGIBILITY: dict[RecipientCategory, frozenset[TransferChannel]] = {
    RecipientCategory.INTERNAL_SAME_SCOPE: frozenset({TransferChannel.PLATFORM_DOWNLOAD}),
    RecipientCategory.INTERNAL_CROSS_SCOPE: frozenset({TransferChannel.PLATFORM_DOWNLOAD}),
    RecipientCategory.INDEPENDENT_OVERSIGHT: frozenset(
        {TransferChannel.PLATFORM_DOWNLOAD, TransferChannel.GOVERNED_TRANSFER}
    ),
    RecipientCategory.REGULATED_EXTERNAL: frozenset({TransferChannel.GOVERNED_TRANSFER}),
    RecipientCategory.PUBLIC_AUTHORITATIVE_RELEASE: frozenset(
        {TransferChannel.AUTHORITATIVE_PUBLICATION}
    ),
}


@dataclass(frozen=True, slots=True)
class RecipientObligation:
    """The downstream obligations attached to an export
    (`P12-EXP-014`)."""

    retention_limit: timedelta
    resharing_permitted: bool
    destruction_required: bool
    obligation_reference: str

    def __post_init__(self) -> None:
        require_text(self.obligation_reference, "obligation_reference")
        if self.retention_limit <= timedelta(0):
            raise RecipientObligationMissingError("retention_limit must be a positive duration")

    def to_payload(self) -> dict[str, object]:
        return {
            "retention_limit_days": self.retention_limit.days,
            "resharing_permitted": self.resharing_permitted,
            "destruction_required": self.destruction_required,
            "obligation_reference": self.obligation_reference,
        }


@dataclass(frozen=True, slots=True)
class Recipient:
    recipient_reference: str
    category: RecipientCategory
    organization_scope: OrganizationalScopeRef
    obligation: RecipientObligation

    def __post_init__(self) -> None:
        require_text(self.recipient_reference, "recipient_reference")

    def to_payload(self) -> dict[str, object]:
        return {
            "recipient_reference": self.recipient_reference,
            "category": str(self.category),
            "organization_id": str(self.organization_scope.organization_id),
            "obligation": self.obligation.to_payload(),
        }


@dataclass(frozen=True, slots=True)
class ExportScope:
    domains: frozenset[str]
    record_classes: frozenset[str]
    organization_scope: OrganizationalScopeRef
    time_range_start: datetime | None = None
    time_range_end: datetime | None = None

    def __post_init__(self) -> None:
        if not self.domains or not self.record_classes:
            raise ExportPurposeMissingError(
                "an export scope must name at least one domain and one record class"
            )
        for domain in self.domains:
            if domain in UNCERTIFIED_RESULT_DOMAINS:
                raise ExportUncertifiedResultProhibitedError(
                    f"domain {domain!r} is intermediate or non-certified tally material and is "
                    "never exportable; a final certified result is released by the "
                    "authoritative voting and result-certification domain"
                )
            if domain in ABSOLUTELY_EXCLUDED_DOMAINS:
                raise ExportBallotContentProhibitedError(f"domain {domain!r} may never be exported")


@dataclass(frozen=True, slots=True)
class DatasetItemReference:
    """One item in the manifest. A reference and a digest, never the
    row."""

    record_reference: str
    domain: str
    classification: ClassificationDecision
    content_digest: str

    def __post_init__(self) -> None:
        require_text(self.record_reference, "record_reference")
        require_text(self.content_digest, "content_digest")

    def to_payload(self) -> dict[str, object]:
        return {
            "record_reference": self.record_reference,
            "domain": self.domain,
            "classification": self.classification.to_payload(),
            "content_digest": self.content_digest,
        }


@dataclass(frozen=True, slots=True)
class DatasetManifest:
    """The immutable description of what an artifact contains.

    Describes composition without unnecessarily disclosing sensitive
    content (`P12-EXP-009`): item references and digests, counts and
    field names - never values."""

    manifest_id: UUID
    export_id: UUID
    items: tuple[DatasetItemReference, ...]
    permitted_fields: frozenset[str]
    policy_version: str
    classification_mapping_version: str
    generated_at: datetime

    def __post_init__(self) -> None:
        require_timezone(self.generated_at, context="DatasetManifest.generated_at")
        if not self.permitted_fields:
            raise FieldNotExportableError("a manifest must name the permitted field set")

    def digest(self) -> str:
        return deterministic_digest(
            str(self.export_id),
            *(item.content_digest for item in self.items),
            *sorted(self.permitted_fields),
            self.policy_version,
        )

    def to_payload(self) -> dict[str, object]:
        payload = {
            "manifest_id": str(self.manifest_id),
            "export_id": str(self.export_id),
            "item_count": len(self.items),
            "item_references": [item.record_reference for item in self.items],
            "permitted_fields": sorted(self.permitted_fields),
            "policy_version": self.policy_version,
            "classification_mapping_version": self.classification_mapping_version,
            "generated_at": self.generated_at.isoformat(),
            "manifest_digest": self.digest(),
        }
        reject_prohibited_payload_keys(payload, context="DatasetManifest")
        return payload


@dataclass(frozen=True, slots=True)
class ExportArtifact:
    """The generated artifact.

    `projection` holds only permitted fields, because `build_artifact`
    never materialises the denied ones (`P12-EXP-008`). The artifact is
    explicitly not an authoritative domain record (`P12-EXP-020`), and
    `is_authoritative` is a read-only property rather than a field, so no
    payload can construct it `True`."""

    artifact_id: UUID
    export_id: UUID
    manifest: DatasetManifest
    projection: tuple[Mapping[str, str], ...]
    expires_at: datetime
    access_count: int = 0
    revoked: bool = False

    def __post_init__(self) -> None:
        require_timezone(self.expires_at, context="ExportArtifact.expires_at")
        for row in self.projection:
            extra = set(row) - self.manifest.permitted_fields
            if extra:
                raise FieldNotExportableError(
                    f"the artifact carries fields outside the permitted set: {sorted(extra)}"
                )

    @property
    def is_authoritative(self) -> bool:
        """Always `False`. A property, not a field: a field could be
        constructed `True` and would survive `replace`."""
        return False

    def assert_accessible(self, *, at: datetime, policy: PrivilegedAccessPolicy) -> None:
        require_timezone(at, context="ExportArtifact.assert_accessible")
        if self.revoked:
            raise ArtifactRevokedError("authorization for this artifact was withdrawn")
        if at >= self.expires_at:
            raise ArtifactExpiredError("the artifact's expiry has passed")
        if self.access_count >= policy.export_access_limit:
            raise DlpAccessLimitExceededError("the artifact's access limit has been reached")

    def with_access(self) -> ExportArtifact:
        return replace(self, access_count=self.access_count + 1)

    def with_revocation(self) -> ExportArtifact:
        """Withdraw authorization.

        This blocks further platform-mediated access. It does **not**
        delete a copy the recipient already holds, and nothing in this
        codebase may describe it as doing so (`P12-EXP-013`)."""
        return replace(self, revoked=True)

    def verify_manifest(self) -> None:
        """Re-check the artifact against its manifest before delivery.

        Three checks, not one. `__post_init__` already refuses a
        construction whose projection carries an unpermitted field, but
        `dataclasses.replace` can swap either side afterwards, so the
        binding is re-verified here rather than assumed: the manifest
        belongs to this export, the projection carries no field outside
        the permitted set, and there is exactly one projected row per
        manifest item. A manifest that no longer describes the artifact
        is a manifest that proves nothing."""
        if self.manifest.export_id != self.export_id:
            raise ExportManifestMismatchError("the manifest belongs to a different export")
        for row in self.projection:
            extra = set(row) - self.manifest.permitted_fields
            if extra:
                raise ExportManifestMismatchError(
                    f"the artifact carries fields the manifest does not permit: {sorted(extra)}"
                )
        if len(self.projection) != len(self.manifest.items):
            raise ExportManifestMismatchError(
                f"the artifact carries {len(self.projection)} rows but the manifest describes "
                f"{len(self.manifest.items)}"
            )


@dataclass(frozen=True, slots=True)
class ExportRequest:
    """One export request, with the 21 attributes `P12-EXP-002`
    requires."""

    export_id: UUID
    requester_reference: str
    purpose: PurposeBinding
    scope: ExportScope
    requested_fields: frozenset[str]
    requested_format: str
    recipient: Recipient
    transfer_channel: TransferChannel
    requested_at: datetime
    data_owner_reference: str
    redaction_required: bool = False
    pseudonymization_required: bool = False
    watermark_required: bool = False
    state: ExportState = ExportState.REQUESTED
    approver_reference: str | None = None
    dlp_assessment_reference: str | None = None
    disclosure_assessment_reference: str | None = None
    history: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        require_text(self.requester_reference, "requester_reference")
        require_text(self.requested_format, "requested_format")
        require_text(self.data_owner_reference, "data_owner_reference")
        require_timezone(self.requested_at, context="ExportRequest.requested_at")
        if not self.requested_fields:
            raise FieldNotExportableError("an export request must name the fields it wants")
        if self.recipient.category in BASIS_REQUIRED_CATEGORIES and not (
            self.purpose.basis_reference
        ):
            raise RecipientObligationMissingError(
                f"recipient category {self.recipient.category!s} requires an explicit basis "
                "reference"
            )
        allowed_channels = _CHANNEL_ELIGIBILITY[self.recipient.category]
        if self.transfer_channel not in allowed_channels:
            raise TransferChannelProhibitedError(
                f"channel {self.transfer_channel!s} is not permitted for recipient category "
                f"{self.recipient.category!s}"
            )
        if (
            self.recipient.category in ATTESTATION_REQUIRED_CATEGORIES
            and not self.recipient.obligation.destruction_required
        ):
            raise RecipientObligationMissingError(
                f"recipient category {self.recipient.category!s} requires a destruction "
                "attestation obligation"
            )

    def with_state(self, target: ExportState, *, action: str) -> ExportRequest:
        if (self.state, target) not in _ALLOWED_TRANSITIONS:
            raise ForbiddenTransitionError(
                f"invalid export transition {self.state.value} -> {target.value}"
            )
        return replace(self, state=target, history=(*self.history, action))

    def with_approver(self, approver_reference: str) -> ExportRequest:
        if approver_reference == self.requester_reference:
            raise ExportSelfApprovalProhibitedError("the requester of an export may not approve it")
        if approver_reference == self.data_owner_reference:
            raise ExportSelfApprovalProhibitedError(
                "the data owner proposes; a distinct approver decides"
            )
        return replace(self, approver_reference=approver_reference)

    def to_state_payload(self) -> dict[str, object]:
        return {
            "export_id": str(self.export_id),
            "requester_reference": self.requester_reference,
            "purpose": self.purpose.to_payload(),
            "domains": sorted(self.scope.domains),
            "record_classes": sorted(self.scope.record_classes),
            "organization_scope": self.scope.organization_scope.to_payload(),
            "requested_fields": sorted(self.requested_fields),
            "requested_format": self.requested_format,
            "recipient": self.recipient.to_payload(),
            "transfer_channel": str(self.transfer_channel),
            "requested_at": self.requested_at.isoformat(),
            "data_owner_reference": self.data_owner_reference,
            "redaction_required": self.redaction_required,
            "pseudonymization_required": self.pseudonymization_required,
            "watermark_required": self.watermark_required,
            "state": str(self.state),
            "approver_reference": self.approver_reference,
            "dlp_assessment_reference": self.dlp_assessment_reference,
            "disclosure_assessment_reference": self.disclosure_assessment_reference,
        }


def assert_export_authority(
    *,
    has_search_permission: bool,
    has_read_permission: bool,
    has_admin_privilege: bool,
    has_data_owner_authority: bool,
    has_approver: bool,
) -> None:
    """Export authority derives from the data owner plus a distinct
    approver, and from nothing else.

    Each wrong basis gets its own reason code, because "you may read it"
    and "you administer the system" are different mistakes with different
    corrections (`P12-EXP-004`, `P12-EXP-005`, `P12-EXP-006`)."""
    if has_data_owner_authority and has_approver:
        return
    if has_search_permission and not has_data_owner_authority:
        raise SearchPermissionInsufficientError("search permission is not export permission")
    if has_read_permission and not has_data_owner_authority:
        raise BulkExtractionNotAuthorizedError("read permission is not bulk-export permission")
    if has_admin_privilege and not has_data_owner_authority:
        raise AdminPrivilegeInsufficientError("administrative privilege is not export authority")
    raise AdminPrivilegeInsufficientError(
        "export requires the data owner for the record class plus a distinct approver"
    )


def assert_recipient_eligible(
    recipient: Recipient, classifications: Sequence[ClassificationDecision]
) -> None:
    """Raise unless every classification in the set may reach this
    recipient category."""
    eligible = _RECIPIENT_TIER_ELIGIBILITY[recipient.category]
    for decision in classifications:
        if decision.tier is EnforcementTier.T4_PROHIBITED:
            raise ExportBallotContentProhibitedError(
                "prohibited-tier material may never be exported to any recipient"
            )
        if decision.tier not in eligible:
            raise RecipientNotAuthorizedError(
                f"recipient category {recipient.category!s} may not receive tier {decision.tier!s}"
            )


def assert_cross_scope_basis(
    request: ExportRequest, *, cross_scope_basis_reference: str | None
) -> None:
    """Cross-organizational export needs its own basis (`P12-ORG-006`)."""
    same_org = (
        request.recipient.organization_scope.organization_id
        == request.scope.organization_scope.organization_id
    )
    if same_org:
        return
    if request.recipient.category is RecipientCategory.INTERNAL_SAME_SCOPE:
        raise ExportOrganizationMismatchError(
            "a cross-organizational export cannot use the same-scope recipient category"
        )
    if not cross_scope_basis_reference:
        raise ExportOrganizationMismatchError(
            "a cross-organizational export requires its own scope and basis"
        )


def assert_hold_is_not_authorization(*, under_legal_hold: bool, has_export_authority: bool) -> None:
    """A legal hold preserves; it never authorises (`P12-EXP-017`)."""
    if under_legal_hold and not has_export_authority:
        raise LegalHoldNotAuthorizationError(
            "a legal hold preserves a record from disposal; it is not permission to export it"
        )


def assert_source_records_current(
    *, revoked_references: frozenset[str], requested_references: frozenset[str]
) -> None:
    """Records revoked or deleted at source never enter a new export
    (`P12-EXP-018`)."""
    overlap = revoked_references & requested_references
    if overlap:
        raise SourceRecordRevokedError(
            f"source records {sorted(overlap)} are revoked or deleted and may not enter a new "
            "export"
        )


def permitted_field_set(
    requested: frozenset[str],
    *,
    class_fields: frozenset[str],
    purpose_fields: frozenset[str],
    recipient_denied: frozenset[str],
) -> frozenset[str]:
    """Compute the permitted field set before any artifact exists.

    The order is the decision order from the data matrix: class policy,
    then purpose, then recipient. A field failing any stage never reaches
    generation, which is the whole of `P12-EXP-008`."""
    permitted = requested & class_fields & purpose_fields
    permitted -= recipient_denied
    denied = requested - permitted
    if denied:
        raise FieldNotExportableError(
            f"fields {sorted(denied)} are denied by policy and are excluded before generation"
        )
    return permitted


def build_artifact(
    request: ExportRequest,
    rows: Sequence[Mapping[str, str]],
    *,
    manifest: DatasetManifest,
    artifact_id: UUID,
    at: datetime,
    policy: PrivilegedAccessPolicy,
) -> ExportArtifact:
    """Project only permitted fields into the artifact.

    The projection is built by *selecting* permitted keys, never by
    copying the row and deleting denied ones: a delete-after-copy
    implementation leaves the denied value in memory and, in a real
    serialiser, frequently in the output."""
    if manifest.export_id != request.export_id:
        raise ExportManifestMismatchError("the manifest belongs to a different export")
    if not manifest.items:
        raise ExportManifestMissingError("an artifact requires a non-empty manifest")
    permitted = manifest.permitted_fields
    projection = tuple(
        {name: value for name, value in row.items() if name in permitted} for row in rows
    )
    return ExportArtifact(
        artifact_id=artifact_id,
        export_id=request.export_id,
        manifest=manifest,
        projection=projection,
        expires_at=at + policy.export_artifact_expiry,
    )


@dataclass(frozen=True, slots=True)
class ExportAccessEvent:
    access_id: UUID
    artifact_id: UUID
    accessor_reference: str
    accessed_at: datetime

    def __post_init__(self) -> None:
        require_timezone(self.accessed_at, context="ExportAccessEvent.accessed_at")
        require_text(self.accessor_reference, "accessor_reference")


@dataclass(frozen=True, slots=True)
class ExportDestructionAttestation:
    """A statement by the recipient, not a verified fact.

    Nothing in this type or its use may be read as evidence that a copy
    outside the platform ceased to exist (`P12-EXP-013`,
    `P12-DLP-004`)."""

    attestation_id: UUID
    export_id: UUID
    attesting_party: str
    attested_at: datetime
    attestation_reference: str

    def __post_init__(self) -> None:
        require_timezone(self.attested_at, context="ExportDestructionAttestation.attested_at")
        require_text(self.attesting_party, "attesting_party")
        require_text(self.attestation_reference, "attestation_reference")


def assert_certified_result_not_exported(*, domain: str, is_certified: bool) -> None:
    """A certified result is released by the authoritative domain, never
    through this pipeline (`P12-VOTE-004`, `P12-VOTE-005`).

    The refusal is deliberately distinct from the ballot-content one: a
    caller trying to export a certified result is not doing the same
    thing as a caller trying to export ballots, and the reason codes must
    not conflate them."""
    if domain in {"certified_result", "voting_result"} and is_certified:
        raise ResultPublicationNotOwnedError(
            "a final certified result is released only by the authoritative voting and "
            "result-certification domain, through an approved publication rendition; "
            "PACK-12 may audit that a governed publication occurred and nothing more"
        )
    if domain in {"certified_result", "voting_result"} and not is_certified:
        raise ExportUncertifiedResultProhibitedError(
            "result material that is not yet closed and certified remains absolutely prohibited"
        )


def resolve_export_state(value: str) -> ExportState:
    try:
        return ExportState(value)
    except ValueError as exc:
        raise UnknownStatusError(f"unknown export state {value!r}") from exc
