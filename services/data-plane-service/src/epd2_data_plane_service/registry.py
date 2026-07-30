"""The canonical schema registry (PACK-13 §12; ADR-073).

The registry records, for every schema version, the attributes §12.3
enumerates — and it records **governance context, effective date and
publication decision separately from the content digest**, so that the
question "what does this version mean, and who decided it" is answerable
without inspecting bytes (`P13-REG-005f`).

Four refusals here are the substance of ADR-073's correction:

- **Accidental republication of identical content is blocked**
  (`SCHEMA_DUPLICATE_CONTENT`), never silently accepted and never
  silently deduplicated into the existing version.
- **Identical content submitted as a new version without a
  justification** goes to reason-coded review
  (`SCHEMA_DUPLICATE_CONTENT_REVIEW_REQUIRED`).
- **Identical content deliberately bound to a new governed version**
  with a recorded justification is approved and says so
  (`SCHEMA_IDENTICAL_CONTENT_REPUBLICATION_APPROVED`) — the legitimate
  cases exist: a re-issue under a changed compatibility mode, a new
  effective date, a corrected ownership assignment, a republication
  after a governance defect.
- **A historical `schema_version_id` is never re-pointed, merged or
  rewritten because of digest equality**
  (`SCHEMA_VERSION_IDENTITY_IMMUTABLE`).

The registry is **not a second canon** (`P13-REG-002`). Where the two
disagree, the canon governs and the disagreement is a defect to be
resolved — there is deliberately no precedence field in any model here
that could encode the opposite.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from epd2_data_plane_service.canonicalization import (
    CanonicalContent,
    SchemaFormat,
)
from epd2_data_plane_service.domain import (
    ActorReference,
    ClassificationReference,
    DomainReference,
    EvidenceReference,
    reject_reserved_boundary_schema,
    require_timezone,
)
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

# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------


class SchemaLifecycleState(StrEnum):
    """§12.2's lifecycle. `retired` and `superseded` do **not** delete the
    schema version: a historical event validated against a retired schema
    must remain interpretable (`P13-REG-004`)."""

    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    RETIRED = "retired"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


#: The declared transitions. Anything not listed is refused with
#: `SCHEMA_LIFECYCLE_TRANSITION_FORBIDDEN`; there is no wildcard and no
#: "administrative override" edge, because an override edge is the one a
#: future incident would use to skip review (`P13-REG-003`).
SCHEMA_LIFECYCLE_TRANSITIONS: Mapping[SchemaLifecycleState, frozenset[SchemaLifecycleState]] = {
    SchemaLifecycleState.DRAFT: frozenset(
        {SchemaLifecycleState.UNDER_REVIEW, SchemaLifecycleState.REJECTED}
    ),
    SchemaLifecycleState.UNDER_REVIEW: frozenset(
        {SchemaLifecycleState.APPROVED, SchemaLifecycleState.REJECTED}
    ),
    SchemaLifecycleState.APPROVED: frozenset(
        {SchemaLifecycleState.ACTIVE, SchemaLifecycleState.REJECTED}
    ),
    SchemaLifecycleState.ACTIVE: frozenset(
        {SchemaLifecycleState.DEPRECATED, SchemaLifecycleState.SUPERSEDED}
    ),
    SchemaLifecycleState.DEPRECATED: frozenset(
        {SchemaLifecycleState.RETIRED, SchemaLifecycleState.SUPERSEDED}
    ),
    SchemaLifecycleState.RETIRED: frozenset(),
    SchemaLifecycleState.REJECTED: frozenset(),
    SchemaLifecycleState.SUPERSEDED: frozenset(),
}


class CompatibilityMode(StrEnum):
    """The declared compatibility mode a family is governed under
    (`P13-COMPAT-001`). `UNKNOWN` is a real, first-class outcome, never a
    placeholder (`P13-COMPAT-002`)."""

    BACKWARD = "backward_compatible"
    FORWARD = "forward_compatible"
    FULL = "full_compatible"
    BREAKING = "breaking"
    UNKNOWN = "unknown_manual_review_required"


class DuplicateContentDisposition(StrEnum):
    """The three reason-coded outcomes §15 of the implementation task and
    `P13-REG-005d`/`P13-REG-005e` require, kept as an enum so that a
    caller cannot invent a fourth."""

    BLOCKED = "blocked"
    REVIEW_REQUIRED = "review_required"
    REPUBLICATION_APPROVED = "republication_approved"


#: The reason code each disposition carries. Kept beside the enum so the
#: mapping is one fact in one place.
DUPLICATE_CONTENT_REASON_CODES: Mapping[DuplicateContentDisposition, str] = {
    DuplicateContentDisposition.BLOCKED: "SCHEMA_DUPLICATE_CONTENT",
    DuplicateContentDisposition.REVIEW_REQUIRED: "SCHEMA_DUPLICATE_CONTENT_REVIEW_REQUIRED",
    DuplicateContentDisposition.REPUBLICATION_APPROVED: (
        "SCHEMA_IDENTICAL_CONTENT_REPUBLICATION_APPROVED"
    ),
}


# ---------------------------------------------------------------------------
# Registry entities
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SchemaOwner:
    """Every schema has exactly one owner, and the owner is a domain, not
    a platform team (`P13-REG-006`). A platform team can maintain a file;
    only the domain knows what a change means."""

    domain: DomainReference
    accountable_role: str

    def __post_init__(self) -> None:
        if not self.accountable_role:
            raise SchemaOwnerMissingError("a schema owner requires an accountable domain role")
        reject_reserved_boundary_schema(self.domain, context="schema ownership")


@dataclass(frozen=True, slots=True)
class SchemaFamily:
    """A named family of schema versions with one owner, one format and
    one declared compatibility mode."""

    family_id: UUID
    family_name: str
    owner: SchemaOwner
    schema_format: SchemaFormat
    compatibility_mode: CompatibilityMode

    def __post_init__(self) -> None:
        if not self.family_name:
            raise ValueError("family_name must not be empty")


@dataclass(frozen=True, slots=True)
class SchemaDefinition:
    """The submitted artifact: its family, its canonical content and its
    example fixtures.

    The document body lives here and **nowhere else** — no event payload,
    no projection row and no audit record in this package carries it
    (`P13-EVT-005`)."""

    family: SchemaFamily
    canonical_content: CanonicalContent
    documentation_reference: DocumentationReference
    examples: tuple[Mapping[str, object], ...] = ()

    def __post_init__(self) -> None:
        if self.canonical_content.schema_format is not self.family.schema_format:
            raise SchemaDigestMismatchError(
                f"definition format {self.canonical_content.schema_format.value!r} does not "
                f"match family format {self.family.schema_format.value!r}; a digest is never "
                f"compared across formats"
            )
        if not self.examples:
            raise SchemaExamplesInvalidError(
                "example fixtures are mandatory (P13-REG-008); a schema whose own examples "
                "are absent cannot have them validated at publication"
            )


@dataclass(frozen=True, slots=True)
class DocumentationReference:
    """Where the human-readable documentation for a schema version
    lives. A reference, never the text."""

    documentation_id: UUID
    title: str


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """The recorded outcome of validating a schema's own fixtures
    (`P13-REG-008`)."""

    all_examples_valid: bool
    failures: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.all_examples_valid and self.failures:
            raise ValueError("a valid result carries no failures")


@dataclass(frozen=True, slots=True)
class SchemaPublicationDecision:
    """The governance fact that establishes a schema version's identity.

    `schema_version_id` is established **by this decision** and is never
    derived from, nor overwritten because of, digest equality
    (`P13-REG-005c`)."""

    publication_decision_id: UUID
    decided_by: ActorReference
    decided_at: datetime
    evidence: EvidenceReference
    governance_justification: str | None = None
    duplicate_content_disposition: DuplicateContentDisposition | None = None

    def __post_init__(self) -> None:
        require_timezone(self.decided_at, field="SchemaPublicationDecision.decided_at")
        if (
            self.duplicate_content_disposition is DuplicateContentDisposition.REPUBLICATION_APPROVED
            and not self.governance_justification
        ):
            raise SchemaGovernanceJustificationMissingError(
                "identical content may be bound to a new governed version only with an "
                "explicit governance_justification recorded on the new version "
                "(P13-REG-005e)"
            )


@dataclass(frozen=True, slots=True)
class SchemaDeprecation:
    """A dated, announced, discoverable deprecation (`P13-API-004`)."""

    deprecated_at: datetime
    coexistence_ends_at: datetime
    replacement_version_id: UUID | None
    reason_code: str

    def __post_init__(self) -> None:
        require_timezone(self.deprecated_at, field="SchemaDeprecation.deprecated_at")
        require_timezone(self.coexistence_ends_at, field="SchemaDeprecation.coexistence_ends_at")
        if self.coexistence_ends_at <= self.deprecated_at:
            raise ValueError("the coexistence window must end after the deprecation begins")


@dataclass(frozen=True, slots=True)
class SchemaSupersession:
    """Replacement is supersession, never overwrite (`P13-DOC-004`).

    The superseded version is retained with its digest and its history
    intact; this record points forward, and nothing points backwards into
    the old version to rewrite it."""

    superseding_version_id: UUID
    superseded_at: datetime
    reason_code: str

    def __post_init__(self) -> None:
        require_timezone(self.superseded_at, field="SchemaSupersession.superseded_at")


@dataclass(frozen=True, slots=True)
class MigrationReference:
    """A reference from a schema version to the migration that carries
    it, where one exists (`P13-REG` §12.1)."""

    migration_id: str
    ordering_position: int


@dataclass(frozen=True, slots=True)
class ConsumerRegistration:
    """How the registry knows who breaks (`P13-REG-009`).

    An unregistered consumer receives no compatibility protection, and
    that consequence is stated here in the type's own documentation
    rather than left to be discovered by the consumer."""

    consumer_id: UUID
    consumer_name: str
    consumer_domain: DomainReference
    family_id: UUID
    supported_version_ids: tuple[UUID, ...]
    registered_at: datetime
    migrated_to_version_id: UUID | None = None

    def __post_init__(self) -> None:
        require_timezone(self.registered_at, field="ConsumerRegistration.registered_at")
        if not self.consumer_name:
            raise ValueError("consumer_name must not be empty")

    def supports(self, version_id: UUID) -> bool:
        return version_id in self.supported_version_ids


@dataclass(frozen=True, slots=True)
class SchemaVersion:
    """One governed schema version, carrying every attribute §12.3
    requires.

    The seven fields the implementation task requires to stay separate
    are separate here and never derived from one another:
    `content_digest`, `schema_version_id`, `publication_decision_id`,
    `effective_at`, `deprecated_at`, `supersession_reference` and
    `governance_justification`."""

    schema_version_id: UUID
    family: SchemaFamily
    version_label: str
    content_digest: str
    lifecycle_state: SchemaLifecycleState
    classification: ClassificationReference
    publication_decision: SchemaPublicationDecision | None = None
    validation_result: ValidationResult | None = None
    effective_at: datetime | None = None
    deprecation: SchemaDeprecation | None = None
    supersession: SchemaSupersession | None = None
    migration_reference: MigrationReference | None = None
    dependent_consumer_ids: tuple[UUID, ...] = ()
    documentation_reference: DocumentationReference | None = None

    def __post_init__(self) -> None:
        if not self.version_label:
            raise ValueError("version_label must not be empty")
        if len(self.content_digest) != 64:
            raise SchemaDigestMismatchError("content_digest must be a SHA-256 hex digest")
        if self.effective_at is not None:
            require_timezone(self.effective_at, field="SchemaVersion.effective_at")

    @property
    def publication_decision_id(self) -> UUID | None:
        """Exposed as its own accessor because §12.3 names it as its own
        mandatory attribute: the decision that established this identity
        must be answerable without reading the whole decision record."""
        return (
            None
            if self.publication_decision is None
            else self.publication_decision.publication_decision_id
        )

    @property
    def governance_justification(self) -> str | None:
        return (
            None
            if self.publication_decision is None
            else self.publication_decision.governance_justification
        )

    @property
    def deprecated_at(self) -> datetime | None:
        return None if self.deprecation is None else self.deprecation.deprecated_at

    @property
    def supersession_reference(self) -> UUID | None:
        return None if self.supersession is None else self.supersession.superseding_version_id

    def with_state(self, new_state: SchemaLifecycleState) -> SchemaVersion:
        """Return a copy in `new_state`, refusing an undeclared
        transition (`P13-REG-003`)."""
        permitted = SCHEMA_LIFECYCLE_TRANSITIONS[self.lifecycle_state]
        if new_state not in permitted:
            raise SchemaLifecycleTransitionForbiddenError(
                f"schema version {self.schema_version_id}: "
                f"{self.lifecycle_state.value} -> {new_state.value} is not a declared "
                f"transition; declared: {sorted(s.value for s in permitted)}"
            )
        return _replace_version(self, lifecycle_state=new_state)

    def usable_for_new_traffic(self) -> None:
        """Refuse a retired version for new traffic, while leaving it
        readable for historical interpretation (`P13-REG-004`)."""
        if self.lifecycle_state is SchemaLifecycleState.RETIRED:
            raise SchemaRetiredError(
                f"schema version {self.schema_version_id} is retired and is not used for new "
                f"traffic; it is retained, not deleted, so historical events validated "
                f"against it remain interpretable"
            )
        if self.lifecycle_state not in (
            SchemaLifecycleState.ACTIVE,
            SchemaLifecycleState.DEPRECATED,
        ):
            raise SchemaNotApprovedError(
                f"schema version {self.schema_version_id} is in state "
                f"{self.lifecycle_state.value!r}; only an active or deprecated version "
                f"serves traffic"
            )


def _replace_version(version: SchemaVersion, **changes: object) -> SchemaVersion:
    """A thin wrapper over `dataclasses.replace` for `SchemaVersion`.

    Exists so that every mutation of a registry version goes through one
    named function that a reader can grep for — the registry's whole
    contract is which fields may change and when, and a scattered set of
    ad-hoc `replace` calls would make that unanswerable."""
    return replace(version, **changes)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Duplicate-content assessment
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class DuplicateContentAssessment:
    """The reason-coded outcome of comparing submitted content against
    every registered version of the same family."""

    disposition: DuplicateContentDisposition
    reason_code: str
    matching_version_id: UUID | None
    governance_justification: str | None = None

    @property
    def admits_publication(self) -> bool:
        return self.disposition is DuplicateContentDisposition.REPUBLICATION_APPROVED


def assess_duplicate_content(
    *,
    submitted_digest: str,
    existing_versions: Sequence[SchemaVersion],
    governance_justification: str | None,
    intentional_republication: bool,
) -> DuplicateContentAssessment | None:
    """Classify a submission against the family's existing versions.

    Returns `None` when the content is new — the common case — and one of
    the three dispositions otherwise. The branch order encodes
    ADR-073's correction:

    - Not intentional → **blocked**. An accidental republication is
      caught before it becomes a governance record.
    - Intentional but unjustified → **review required**. Wanting a new
      version is not itself a reason for one.
    - Intentional and justified → **approved**, with the justification
      carried forward onto the new version.

    In no branch is the existing version's identity touched: digest
    equality never merges, re-points or rewrites it (`P13-REG-005g`).
    """
    match = next((v for v in existing_versions if v.content_digest == submitted_digest), None)
    if match is None:
        return None
    if not intentional_republication:
        return DuplicateContentAssessment(
            disposition=DuplicateContentDisposition.BLOCKED,
            reason_code=DUPLICATE_CONTENT_REASON_CODES[DuplicateContentDisposition.BLOCKED],
            matching_version_id=match.schema_version_id,
        )
    if not governance_justification:
        return DuplicateContentAssessment(
            disposition=DuplicateContentDisposition.REVIEW_REQUIRED,
            reason_code=DUPLICATE_CONTENT_REASON_CODES[DuplicateContentDisposition.REVIEW_REQUIRED],
            matching_version_id=match.schema_version_id,
        )
    return DuplicateContentAssessment(
        disposition=DuplicateContentDisposition.REPUBLICATION_APPROVED,
        reason_code=DUPLICATE_CONTENT_REASON_CODES[
            DuplicateContentDisposition.REPUBLICATION_APPROVED
        ],
        matching_version_id=match.schema_version_id,
        governance_justification=governance_justification,
    )


def require_duplicate_content_admissible(
    assessment: DuplicateContentAssessment | None, *, context: str
) -> None:
    """Raise the registered refusal for a blocked or review-required
    assessment; return silently for new content or an approved
    republication."""
    if assessment is None or assessment.admits_publication:
        return
    if assessment.disposition is DuplicateContentDisposition.BLOCKED:
        raise SchemaDuplicateContentError(
            f"{context}: content is identical after canonicalization to version "
            f"{assessment.matching_version_id}; accidental republication is blocked and is "
            f"never silently deduplicated into the existing version"
        )
    raise SchemaDuplicateContentReviewRequiredError(
        f"{context}: identical content was submitted as a new version without a "
        f"governance_justification; a re-issue is a governance fact, not a content fact, "
        f"and requires reason-coded review"
    )


def reject_version_identity_rewrite(
    *, existing_version_id: UUID, proposed_version_id: UUID, context: str
) -> None:
    """Refuse any attempt to re-point, merge or rewrite a historical
    `schema_version_id` (`P13-REG-005g`).

    Called wherever a caller supplies an existing version's identifier
    for a *new* publication — the shape a well-meaning deduplication
    would take."""
    if existing_version_id == proposed_version_id:
        raise SchemaVersionIdentityImmutableError(
            f"{context}: schema version {existing_version_id} already exists and its identity "
            f"is established by its own publication decision; a later publication does not "
            f"retroactively merge into, replace or re-point it"
        )


# ---------------------------------------------------------------------------
# Consumer readiness
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ConsumerReadiness:
    """Which registered consumers have migrated, and which have not.

    `unregistered_consumers_are_unprotected` is carried as a field rather
    than assumed, so the readiness answer states its own limit: the
    registry can only speak for consumers it knows about
    (`P13-REG-009`)."""

    family_id: UUID
    target_version_id: UUID
    ready_consumer_ids: tuple[UUID, ...]
    not_ready_consumer_ids: tuple[UUID, ...]
    unregistered_consumers_are_unprotected: bool = True

    @property
    def all_ready(self) -> bool:
        return not self.not_ready_consumer_ids


def assess_consumer_readiness(
    *, family_id: UUID, target_version_id: UUID, registrations: Sequence[ConsumerRegistration]
) -> ConsumerReadiness:
    """Compute readiness for a target version across registered
    consumers of one family."""
    ready: list[UUID] = []
    not_ready: list[UUID] = []
    for registration in registrations:
        if registration.family_id != family_id:
            continue
        if registration.migrated_to_version_id == target_version_id or registration.supports(
            target_version_id
        ):
            ready.append(registration.consumer_id)
        else:
            not_ready.append(registration.consumer_id)
    return ConsumerReadiness(
        family_id=family_id,
        target_version_id=target_version_id,
        ready_consumer_ids=tuple(ready),
        not_ready_consumer_ids=tuple(not_ready),
    )


@dataclass(frozen=True, slots=True)
class RegistryAvailability:
    """Whether the registry can be reached.

    Modelled explicitly because §29 assigns it a required posture:
    publication is **blocked** while existing traffic continues on
    already-resolved schemas. An unavailable registry is not a reason to
    publish optimistically."""

    reachable: bool
    checked_at: datetime
    unreachable_reason_code: str | None = field(default=None)

    def __post_init__(self) -> None:
        require_timezone(self.checked_at, field="RegistryAvailability.checked_at")
        if not self.reachable and self.unreachable_reason_code is None:
            raise ValueError("an unreachable registry must carry its reason code")
