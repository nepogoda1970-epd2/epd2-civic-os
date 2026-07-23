"""`PublicLedgerEntry`, `AuditExportPackage`, `DisclosurePolicy`,
`LobbyLogEntry`, per `docs/canonical/TZ-00-domain-event-canon.md`,
section 19a (added by canon 0.3.0, ADR-013, with the amendments recorded
in ADR-013's own "Owner decision" section).

This package consolidates canon's four Transparency-Context entities into
one physical `uv` workspace member, `transparency-service` (ADR-011). The
four entities share one hard structural rule, enforced here as
`FORBIDDEN_FIELD_NAMES` plus `assert_no_forbidden_fields`: none of them may
ever carry an identity/credential/vote/delegation-linkage field, and the
four internal `*_role_id` reference fields must never appear verbatim in
any *public* payload (see `events.py` for where that boundary is actually
drawn — this module stores the real role id; only the events/public-payload
layer strips it).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from uuid import UUID

from epd2_transparency_service.exceptions import (
    ForbiddenAuditExportPackageTransitionError,
    ForbiddenDisclosurePolicyTransitionError,
    ForbiddenLobbyLogEntryTransitionError,
    UnknownAuditExportPackageStatusError,
    UnknownDisclosurePolicyStatusError,
    UnknownLobbyLogEntryStatusError,
)

#: Canon section 19a.6's structural prohibition, verbatim: no entity in
#: this section may ever carry one of these field names, under any
#: disclosure policy (INV-10, fail-closed) — a `DisclosurePolicy` rule can
#: never reclassify one of these into anything other than `prohibited`.
#: The four `*_role_id` fields are included here too: they are legitimate
#: *stored* domain fields (see each entity below), but must never appear
#: verbatim in a *public* payload — see `events.py`'s `*_public_payload`
#: builders, which are the only place this second half of the rule is
#: actually enforced.
FORBIDDEN_FIELD_NAMES: frozenset[str] = frozenset(
    {
        "account_id",
        "person_id",
        "identity_record_id",
        "participation_credential_id",
        "vote_envelope_id",
        "encrypted_or_encoded_choice",
        "credential_proof",
        "published_by_role_id",
        "requested_by_role_id",
        "approved_by_role_id",
        "submitted_by_role_id",
    }
)

#: `AuditExportPackage` additionally never reveals these `AuditEvent`
#: fields for any included event (canon section 19a.2/19a.6) — kept
#: separate from `FORBIDDEN_FIELD_NAMES` because these are fields of the
#: *upstream* `AuditEvent`, not of any Transparency-Context entity itself.
FORBIDDEN_AUDIT_EVENT_FIELDS: frozenset[str] = frozenset(
    {"actor_id", "actor_type", "before_hash", "after_hash", "recorded_at", "policy_version"}
)


def assert_no_forbidden_fields(candidate_fields: Mapping[str, object]) -> None:
    """Fail-closed structural check (INV-10): raise `ValueError` if any key
    of `candidate_fields` is one of `FORBIDDEN_FIELD_NAMES`. Used before
    any content is accepted into a `PublicLedgerEntry.content_snapshot` or
    `LobbyLogEntry` payload, independent of and prior to whatever a
    `DisclosurePolicy` would otherwise allow — a policy rule can never
    override this.
    """
    present = set(candidate_fields) & FORBIDDEN_FIELD_NAMES
    if present:
        raise ValueError(f"structurally forbidden field(s) present: {sorted(present)}")


# ---------------------------------------------------------------------------
# PublicLedgerEntry (canon 19a.1)
# ---------------------------------------------------------------------------


class LedgerSubjectType(StrEnum):
    """Canon section 19a.1's exact `subject_type` list. `ai_processing_record`
    is used exclusively to publish an already-existing `AIProcessingRecord`
    (canon section 17.1) — this package never creates, modifies, or
    requires one to exist."""

    INITIATIVE = "initiative"
    INITIATIVE_VERSION = "initiative_version"
    MODERATION_DECISION = "moderation_decision"
    RESULT_PUBLICATION = "result_publication"
    AI_PROCESSING_RECORD = "ai_processing_record"


#: `subject_type` values that are exempt from `DisclosurePolicy.
#: small_cell_threshold` suppression/banding (canon section 19a.3/19a.5):
#: the formally required official result must always disclose exact
#: counts, independent of sample size.
SMALL_CELL_EXEMPT_SUBJECT_TYPES: frozenset[LedgerSubjectType] = frozenset(
    {LedgerSubjectType.RESULT_PUBLICATION}
)


class PublicLedgerEntryStatus(StrEnum):
    """Canon section 19a.1: the only status a `PublicLedgerEntry` ever
    has. There is no transition table — this status never changes after
    creation."""

    PUBLISHED = "published"


#: Genesis previous-hash marker for the ledger's own light hash chain
#: (canon section 19a.1's `previous_entry_hash` field) — same shape as
#: `epd2_audit_core.hash_chain.GENESIS_PREVIOUS_HASH`, but this is a
#: separate chain: the ledger's own publication order, not Audit Core's.
LEDGER_GENESIS_HASH = "0" * 64


@dataclass(frozen=True, slots=True)
class PublicLedgerEntry:
    """Canon section 19a.1 fields exactly.

    Immutable once created — there is no `save`/update path in
    `storage.py` (mirrors `ModerationDecision`'s precedent: canon gives
    this entity exactly one status value and an explicit "never
    rewritten" rule, so there is nothing here for a transition table to
    validate). A correction is always a *new* `PublicLedgerEntry` with
    `supersedes_entry_id` set — see `application.correct_ledger_entry`.
    Whether any other entry supersedes this one is a derived, query-time
    fact (`storage.PublicLedgerEntryStore` never mutates a stored row).

    `published_by_role_id` is a real, stored, internal `RoleAssignment`
    reference (canon section 8.4) — it is deliberately still a field of
    this domain object; the "never published verbatim" rule (canon
    section 19a.6) is enforced one layer up, in `events.py`'s
    `ledger_entry_public_payload`, which is the only function anyone
    should serialize a `PublicLedgerEntry` through for external
    consumption.
    """

    public_ledger_entry_id: UUID
    subject_type: LedgerSubjectType
    subject_id: UUID
    subject_event_id: UUID
    published_at: datetime
    published_by_role_id: UUID
    content_snapshot: Mapping[str, object]
    content_hash: str
    previous_entry_hash: str
    disclosure_policy_id: UUID
    redaction_notice: str | None
    supersedes_entry_id: UUID | None
    status: PublicLedgerEntryStatus

    def __post_init__(self) -> None:
        if self.published_at.tzinfo is None:
            raise ValueError("published_at must be timezone-aware")
        if not self.content_hash:
            raise ValueError("content_hash must not be empty")
        if not self.previous_entry_hash:
            raise ValueError("previous_entry_hash must not be empty")
        assert_no_forbidden_fields(self.content_snapshot)


# ---------------------------------------------------------------------------
# AuditExportPackage (canon 19a.2)
# ---------------------------------------------------------------------------


class IncludedTargetType(StrEnum):
    """Canon section 19a.2's exact `included_target_types` allow-list.
    `vote_envelope` and `delegation` are deliberately absent — canon names
    them explicitly as never included, under any circumstance."""

    INITIATIVE = "initiative"
    INITIATIVE_VERSION = "initiative_version"
    BALLOT = "ballot"
    MODERATION_CASE = "moderation_case"
    MODERATION_DECISION = "moderation_decision"
    RESULT_PUBLICATION = "result_publication"


class AuditExportPackageStatus(StrEnum):
    """Canon section 19a.2's exact status list."""

    GENERATED = "generated"
    PUBLISHED = "published"
    SUPERSEDED = "superseded"


#: Canon section 19a.2's transition table, verbatim: `generated ->
#: published`; `published -> superseded` (only ever driven by
#: `application.publish_audit_export_package` superseding an old package
#: when a new one names it via `supersedes_package_id` — never a
#: standalone "mark superseded" command). No return to `generated`.
AUDIT_EXPORT_PACKAGE_ALLOWED_TRANSITIONS: frozenset[
    tuple[AuditExportPackageStatus, AuditExportPackageStatus]
] = frozenset(
    {
        (AuditExportPackageStatus.GENERATED, AuditExportPackageStatus.PUBLISHED),
        (AuditExportPackageStatus.PUBLISHED, AuditExportPackageStatus.SUPERSEDED),
    }
)


def parse_audit_export_package_status(value: str) -> AuditExportPackageStatus:
    try:
        return AuditExportPackageStatus(value)
    except ValueError as exc:
        raise UnknownAuditExportPackageStatusError(
            f"unknown audit export package status: {value!r}"
        ) from exc


def assert_audit_export_package_transition_allowed(
    current: AuditExportPackageStatus, target: AuditExportPackageStatus
) -> None:
    if (current, target) not in AUDIT_EXPORT_PACKAGE_ALLOWED_TRANSITIONS:
        raise ForbiddenAuditExportPackageTransitionError(
            f"transition {current.value!r} -> {target.value!r} is not allowed"
        )


@dataclass(frozen=True, slots=True)
class ChainProofItem:
    """One element of `AuditExportPackage.chain_proof` (canon section
    19a.2, ADR-013 amendment 1). `previous_event_hash` here is the
    `event_hash` of the *previous element in this exported segment* —
    deliberately NOT the original `AuditEvent.previous_event_hash` from
    Audit Core's own full chain, since an export is typically a filtered
    subset. Public-safe metadata only: no `actor_id`, `actor_type`,
    `before_hash`, `after_hash`, `recorded_at`, or `policy_version` (see
    `domain.FORBIDDEN_AUDIT_EVENT_FIELDS`).
    """

    event_hash: str
    previous_event_hash: str
    event_type: str
    occurred_at: datetime
    target_type: str
    target_id: UUID
    action: str
    reason_code: str
    correlation_id: UUID
    source_service: str
    sequence_position: int

    def __post_init__(self) -> None:
        if not self.event_hash:
            raise ValueError("event_hash must not be empty")
        if self.occurred_at.tzinfo is None:
            raise ValueError("occurred_at must be timezone-aware")
        if self.sequence_position < 1:
            raise ValueError("sequence_position must be >= 1")


@dataclass(frozen=True, slots=True)
class AuditExportPackage:
    """Canon section 19a.2 fields exactly, with the amended (ADR-013
    amendment 1) `chain_proof` shape: a list of structured `ChainProofItem`
    entries plus package-level `package_digest` and `integrity_proof`
    fields. See `events.py`'s "Verification semantics" note for exactly
    what this package does and does not prove.

    Content (`chain_proof`, `package_digest`, `integrity_proof`,
    `event_count`, `included_target_types`, `scope_description`) is never
    rewritten once generated — only `status` transitions
    (`with_status`), per `domain.AUDIT_EXPORT_PACKAGE_ALLOWED_TRANSITIONS`.
    """

    audit_export_package_id: UUID
    scope_description: str
    requested_by_role_id: UUID
    included_target_types: tuple[IncludedTargetType, ...]
    event_count: int
    chain_proof: tuple[ChainProofItem, ...]
    package_digest: str
    integrity_proof: str
    generated_at: datetime
    redaction_notice: str | None
    supersedes_package_id: UUID | None
    status: AuditExportPackageStatus

    def __post_init__(self) -> None:
        if not self.scope_description:
            raise ValueError("scope_description must not be empty")
        if not self.included_target_types:
            raise ValueError("included_target_types must not be empty")
        if self.event_count != len(self.chain_proof):
            raise ValueError("event_count must equal len(chain_proof)")
        if self.generated_at.tzinfo is None:
            raise ValueError("generated_at must be timezone-aware")
        if not self.package_digest:
            raise ValueError("package_digest must not be empty")
        if not self.integrity_proof:
            raise ValueError("integrity_proof must not be empty")
        expected_positions = tuple(range(1, len(self.chain_proof) + 1))
        actual_positions = tuple(item.sequence_position for item in self.chain_proof)
        if actual_positions != expected_positions:
            raise ValueError(
                "chain_proof sequence_position values must be contiguous, starting at 1, "
                "with no gaps"
            )

    def with_status(self, new_status: AuditExportPackageStatus) -> AuditExportPackage:
        assert_audit_export_package_transition_allowed(self.status, new_status)
        return _replace_package(self, status=new_status)


def _replace_package(
    package: AuditExportPackage, *, status: AuditExportPackageStatus
) -> AuditExportPackage:
    return AuditExportPackage(
        audit_export_package_id=package.audit_export_package_id,
        scope_description=package.scope_description,
        requested_by_role_id=package.requested_by_role_id,
        included_target_types=package.included_target_types,
        event_count=package.event_count,
        chain_proof=package.chain_proof,
        package_digest=package.package_digest,
        integrity_proof=package.integrity_proof,
        generated_at=package.generated_at,
        redaction_notice=package.redaction_notice,
        supersedes_package_id=package.supersedes_package_id,
        status=status,
    )


# ---------------------------------------------------------------------------
# DisclosurePolicy (canon 19a.3)
# ---------------------------------------------------------------------------


class DisclosureClass(StrEnum):
    """Canon section 19a.3 / ADR-015 item 1's exact four classes.
    `PROHIBITED` can never be overridden by any rule or transformation."""

    PUBLIC = "public"
    REDACTED = "redacted"
    RESTRICTED = "restricted"
    PROHIBITED = "prohibited"


class Transformation(StrEnum):
    """Canon section 19a.3's exact `transformation` list."""

    NONE = "none"
    GENERALIZE_TO_ROLE_SCOPE = "generalize_to_role_scope"
    BAND_SMALL_CELL = "band_small_cell"
    SUPPRESS = "suppress"
    HASH = "hash"


class DisclosurePolicyStatus(StrEnum):
    """Canon section 19a.3's exact status list."""

    DRAFT = "draft"
    ACTIVE = "active"
    SUPERSEDED = "superseded"


#: Canon section 19a.3's transition table: `draft -> active` (requires
#: `approved_by_role_id`, INV-08 separation of authority); `active ->
#: superseded` (only when a new version is activated for the same
#: `applies_to_subject_type` — never a standalone command; see
#: `application.activate_disclosure_policy`). No return to `draft`.
DISCLOSURE_POLICY_ALLOWED_TRANSITIONS: frozenset[
    tuple[DisclosurePolicyStatus, DisclosurePolicyStatus]
] = frozenset(
    {
        (DisclosurePolicyStatus.DRAFT, DisclosurePolicyStatus.ACTIVE),
        (DisclosurePolicyStatus.ACTIVE, DisclosurePolicyStatus.SUPERSEDED),
    }
)


def parse_disclosure_policy_status(value: str) -> DisclosurePolicyStatus:
    try:
        return DisclosurePolicyStatus(value)
    except ValueError as exc:
        raise UnknownDisclosurePolicyStatusError(
            f"unknown disclosure policy status: {value!r}"
        ) from exc


def assert_disclosure_policy_transition_allowed(
    current: DisclosurePolicyStatus, target: DisclosurePolicyStatus
) -> None:
    if (current, target) not in DISCLOSURE_POLICY_ALLOWED_TRANSITIONS:
        raise ForbiddenDisclosurePolicyTransitionError(
            f"transition {current.value!r} -> {target.value!r} is not allowed"
        )


#: Default `small_cell_threshold` (canon section 19a.3: "Значение по
#: умолчанию — 10").
DEFAULT_SMALL_CELL_THRESHOLD = 10


@dataclass(frozen=True, slots=True)
class FieldRule:
    """One structured rule of `DisclosurePolicy.field_rules` (canon
    section 19a.3, ADR-013 amendment 2). `replacement_label` is only
    meaningful when `transformation` is `generalize_to_role_scope` (or an
    analogous label-substituting transformation) — otherwise it must be
    `None`.
    """

    field_path: str
    disclosure_class: DisclosureClass
    transformation: Transformation
    replacement_label: str | None = None

    def __post_init__(self) -> None:
        if not self.field_path:
            raise ValueError("field_path must not be empty")
        if self.disclosure_class is DisclosureClass.PROHIBITED and self.transformation not in (
            Transformation.SUPPRESS,
            Transformation.NONE,
        ):
            raise ValueError(
                "a prohibited field_rule must use transformation 'suppress' or 'none' "
                "(a prohibited field is never partially disclosed)"
            )


@dataclass(frozen=True, slots=True)
class DisclosurePolicy:
    """Canon section 19a.3 fields exactly, with the amended (ADR-013
    amendment 2) structured `field_rules` list replacing the original
    single `disclosure_class` + loose `field_redaction_rules` design.

    A field with no matching rule, or more than one applicable rule, is
    fail-closed `prohibited` (INV-10) — enforced by
    `application.resolve_field_rule`/`apply_disclosure_policy`, not by
    this dataclass itself (this object only stores the rules that DO
    exist; "no rule matched" is a property of the *lookup*, not of the
    stored list).
    """

    disclosure_policy_id: UUID
    applies_to_subject_type: str
    field_rules: tuple[FieldRule, ...]
    small_cell_threshold: int
    effective_from: datetime
    approved_by_role_id: UUID | None
    version: int
    status: DisclosurePolicyStatus

    def __post_init__(self) -> None:
        if not self.applies_to_subject_type:
            raise ValueError("applies_to_subject_type must not be empty")
        if self.small_cell_threshold < 0:
            raise ValueError("small_cell_threshold must not be negative")
        if self.effective_from.tzinfo is None:
            raise ValueError("effective_from must be timezone-aware")
        if self.version < 1:
            raise ValueError("version must be >= 1")
        forbidden_rule_paths = {r.field_path for r in self.field_rules} & FORBIDDEN_FIELD_NAMES
        non_prohibited = {
            r.field_path
            for r in self.field_rules
            if r.field_path in forbidden_rule_paths
            and r.disclosure_class != DisclosureClass.PROHIBITED
        }
        if non_prohibited:
            raise ValueError(
                "a field_rule must not reclassify a structurally forbidden field to "
                f"anything other than 'prohibited': {sorted(non_prohibited)}"
            )
        if self.status is not DisclosurePolicyStatus.DRAFT and self.approved_by_role_id is None:
            raise ValueError(
                "approved_by_role_id must be set once a DisclosurePolicy leaves 'draft'"
            )

    def with_status(
        self, new_status: DisclosurePolicyStatus, *, approved_by_role_id: UUID | None = None
    ) -> DisclosurePolicy:
        assert_disclosure_policy_transition_allowed(self.status, new_status)
        if new_status is DisclosurePolicyStatus.ACTIVE and approved_by_role_id is None:
            raise ValueError("activating a DisclosurePolicy requires approved_by_role_id (INV-08)")
        return _replace_policy(
            self,
            status=new_status,
            approved_by_role_id=(
                approved_by_role_id if approved_by_role_id is not None else self.approved_by_role_id
            ),
        )


def _replace_policy(
    policy: DisclosurePolicy, *, status: DisclosurePolicyStatus, approved_by_role_id: UUID | None
) -> DisclosurePolicy:
    return DisclosurePolicy(
        disclosure_policy_id=policy.disclosure_policy_id,
        applies_to_subject_type=policy.applies_to_subject_type,
        field_rules=policy.field_rules,
        small_cell_threshold=policy.small_cell_threshold,
        effective_from=policy.effective_from,
        approved_by_role_id=approved_by_role_id,
        version=policy.version,
        status=status,
    )


def resolve_field_rule(policy: DisclosurePolicy, field_path: str) -> FieldRule:
    """Resolve exactly one applicable rule for `field_path`. Missing or
    ambiguous (more than one matching rule) resolves to a synthetic
    `prohibited`/`suppress` rule (canon section 19a.3: "отсутствие правила
    или неоднозначность ... переводит поле в класс prohibited",
    fail-closed, INV-10) — this function never raises for that case; it
    always returns a usable rule.
    """
    matches = [r for r in policy.field_rules if r.field_path == field_path]
    if len(matches) != 1:
        return FieldRule(
            field_path=field_path,
            disclosure_class=DisclosureClass.PROHIBITED,
            transformation=Transformation.SUPPRESS,
            replacement_label=None,
        )
    return matches[0]


def band_small_cell_value(value: int, threshold: int) -> str | int:
    """Canon section 19a.3's small-cell banding: `0` is shown exactly;
    `1` through `threshold - 1` are banded as `"1-<threshold-1>"`; values
    `>= threshold` are shown exactly."""
    if value == 0:
        return 0
    if value < threshold:
        return f"1-{threshold - 1}"
    return value


def apply_disclosure_policy(
    policy: DisclosurePolicy, raw_fields: Mapping[str, object]
) -> dict[str, object]:
    """Apply `policy` to `raw_fields`, returning the public-safe payload.

    Structurally forbidden fields (`FORBIDDEN_FIELD_NAMES`) are dropped
    unconditionally first — no `field_rule` can ever reclassify them
    (canon section 19a.3/19a.6). Every remaining field is resolved via
    `resolve_field_rule`; `prohibited`/`restricted`-class fields and
    `suppress`-transformation fields are dropped from the *public*
    payload (canon section 19a.3: `restricted` is not part of this
    section's own public-content model — see ADR-015 item 1). `public`
    fields with `transformation = none` pass through unchanged.
    `generalize_to_role_scope` substitutes `replacement_label`.
    `band_small_cell` applies `band_small_cell_value` (only meaningful
    for integer-valued fields; a non-int value under this transformation
    is dropped rather than mis-banded). `hash` replaces the value with a
    SHA-256 hex digest of its string form.
    """
    import hashlib

    result: dict[str, object] = {}
    for field_path, value in raw_fields.items():
        if field_path in FORBIDDEN_FIELD_NAMES:
            continue
        rule = resolve_field_rule(policy, field_path)
        if rule.disclosure_class in (DisclosureClass.PROHIBITED, DisclosureClass.RESTRICTED):
            continue
        if rule.transformation is Transformation.SUPPRESS:
            continue
        if rule.transformation is Transformation.NONE:
            result[field_path] = value
        elif rule.transformation is Transformation.GENERALIZE_TO_ROLE_SCOPE:
            result[field_path] = rule.replacement_label
        elif rule.transformation is Transformation.BAND_SMALL_CELL:
            if isinstance(value, int) and not isinstance(value, bool):
                result[field_path] = band_small_cell_value(value, policy.small_cell_threshold)
        elif rule.transformation is Transformation.HASH:
            result[field_path] = hashlib.sha256(str(value).encode("utf-8")).hexdigest()
    return result


# ---------------------------------------------------------------------------
# LobbyLogEntry (canon 19a.4)
# ---------------------------------------------------------------------------


class LobbyLogRelatedSubjectType(StrEnum):
    """Canon section 19a.4's exact `related_subject_type` list."""

    INITIATIVE = "initiative"
    BALLOT = "ballot"
    AMENDMENT = "amendment"


class LobbyLogContactMethod(StrEnum):
    """Canon section 19a.4's exact `contact_method` list."""

    MEETING = "meeting"
    WRITTEN_SUBMISSION = "written_submission"
    CALL = "call"
    OTHER = "other"


class LobbyLogEntryStatus(StrEnum):
    """Canon section 19a.4's exact status list."""

    SUBMITTED = "submitted"
    PUBLISHED = "published"


#: Canon section 19a.4's transition table: `submitted -> published`,
#: one-shot, no return. A correction is always a new row (canon section
#: 19a.4/19a.1's shared correction pattern), never a further transition
#: of this same row.
LOBBY_LOG_ENTRY_ALLOWED_TRANSITIONS: frozenset[tuple[LobbyLogEntryStatus, LobbyLogEntryStatus]] = (
    frozenset({(LobbyLogEntryStatus.SUBMITTED, LobbyLogEntryStatus.PUBLISHED)})
)

#: Canon section 19a.4's publication deadline: not later than 7 calendar
#: days after `submitted_at`. This is an SLA the automated
#: pre-publication validation is expected to meet operationally; canon
#: names no dedicated reason code for a *missed* deadline (unlike, e.g.,
#: `LOBBY_LOG_ENTRY_INCOMPLETE` for missing mandatory fields), so
#: `application.publish_lobby_log_entry` does not hard-block a late
#: publish on this alone — see `is_within_publication_deadline`, which is
#: informational/observability-only, and README.md's "Known gaps".
LOBBY_LOG_PUBLICATION_WINDOW = timedelta(days=7)


def parse_lobby_log_entry_status(value: str) -> LobbyLogEntryStatus:
    try:
        return LobbyLogEntryStatus(value)
    except ValueError as exc:
        raise UnknownLobbyLogEntryStatusError(f"unknown lobby log entry status: {value!r}") from exc


def assert_lobby_log_entry_transition_allowed(
    current: LobbyLogEntryStatus, target: LobbyLogEntryStatus
) -> None:
    if (current, target) not in LOBBY_LOG_ENTRY_ALLOWED_TRANSITIONS:
        raise ForbiddenLobbyLogEntryTransitionError(
            f"transition {current.value!r} -> {target.value!r} is not allowed"
        )


@dataclass(frozen=True, slots=True)
class LobbyLogEntry:
    """Canon section 19a.4 fields exactly. `organization_name`,
    `related_subject_type`, `related_subject_id`, `contact_date`,
    `topic_summary`, and `submitted_by_role_id` are mandatory (canon: an
    entry "отсутствующим обязательным полем отклоняется при подаче",
    i.e. rejected on submission if a mandatory field is missing) —
    enforced in `application.submit_lobby_log_entry`, not here (this
    dataclass only enforces non-emptiness of the string fields it already
    requires structurally; see `__post_init__`).
    """

    lobby_log_entry_id: UUID
    submitted_by_role_id: UUID
    organization_name: str
    related_subject_type: LobbyLogRelatedSubjectType
    related_subject_id: UUID
    contact_date: datetime
    contact_method: LobbyLogContactMethod
    topic_summary: str
    submitted_at: datetime
    published_at: datetime | None
    supersedes_entry_id: UUID | None
    status: LobbyLogEntryStatus

    def __post_init__(self) -> None:
        if not self.organization_name:
            raise ValueError("organization_name must not be empty")
        if not self.topic_summary:
            raise ValueError("topic_summary must not be empty")
        if self.contact_date.tzinfo is None:
            raise ValueError("contact_date must be timezone-aware")
        if self.submitted_at.tzinfo is None:
            raise ValueError("submitted_at must be timezone-aware")
        if self.published_at is not None and self.published_at.tzinfo is None:
            raise ValueError("published_at must be timezone-aware")
        if (self.status is LobbyLogEntryStatus.PUBLISHED) != (self.published_at is not None):
            raise ValueError("published_at must be set if and only if status is 'published'")

    def with_published(self, published_at: datetime) -> LobbyLogEntry:
        assert_lobby_log_entry_transition_allowed(self.status, LobbyLogEntryStatus.PUBLISHED)
        return _replace_lobby_log_entry(
            self, status=LobbyLogEntryStatus.PUBLISHED, published_at=published_at
        )


def _replace_lobby_log_entry(
    entry: LobbyLogEntry, *, status: LobbyLogEntryStatus, published_at: datetime | None
) -> LobbyLogEntry:
    return LobbyLogEntry(
        lobby_log_entry_id=entry.lobby_log_entry_id,
        submitted_by_role_id=entry.submitted_by_role_id,
        organization_name=entry.organization_name,
        related_subject_type=entry.related_subject_type,
        related_subject_id=entry.related_subject_id,
        contact_date=entry.contact_date,
        contact_method=entry.contact_method,
        topic_summary=entry.topic_summary,
        submitted_at=entry.submitted_at,
        published_at=published_at,
        supersedes_entry_id=entry.supersedes_entry_id,
        status=status,
    )


def is_within_publication_deadline(entry: LobbyLogEntry, at: datetime) -> bool:
    """Observability-only check of canon section 19a.4's 7-day window —
    see `LOBBY_LOG_PUBLICATION_WINDOW`'s docstring for why this is never
    used to hard-block `application.publish_lobby_log_entry`."""
    return at - entry.submitted_at <= LOBBY_LOG_PUBLICATION_WINDOW
