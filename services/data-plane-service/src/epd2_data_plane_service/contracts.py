"""API and event contract evolution (PACK-13 §15, §16, §17; ADR-074).

Two halves that share one governance model.

**APIs.** Endpoint identity is stable; a field is never reused for a new
meaning; a reason code's meaning never changes; no contract change
silently widens privilege; no field is removed before consumer migration
is demonstrated; version negotiation is explicit with no silently-moving
"latest".

**Events.** A historical event is never rewritten — a mistake is
corrected by a new, corrective event that references the original. An
unsupported version fails closed or goes to a controlled dead-letter,
never a best-effort partial parse. An upcaster is deterministic, tested,
and **invents no legal facts**: where the new schema requires a fact the
old event lacks, the correct outcome is an explicit `not_determined`
value or a refusal, never a plausible default. An unknown enum value
never silently maps to a default.

The governance sequence `P13-GOV-001` names is modelled as
`ContractChangeStage`, and `BreakingChangeRecord` enforces
`P13-GOV-002`'s thirteen mandatory fields: a breaking change missing any
one of them is not approvable. `P13-GOV-004` is expressed as a refusal
rather than a note — a feature flag may control the *rollout* of an
already-approved change and may not stand in for the approval.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from epd2_data_plane_service.domain import (
    ActorReference,
    DomainReference,
    EvidenceReference,
    require_timezone,
)
from epd2_data_plane_service.exceptions import (
    BreakingChangeNotApprovedError,
    ConsumerNotReadyError,
    ConsumerNotRegisteredError,
    DeprecationWindowIncompleteError,
    EventVersionUnsupportedError,
    SemanticReviewRequiredError,
)
from epd2_data_plane_service.registry import CompatibilityMode

# ---------------------------------------------------------------------------
# API contract evolution
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ApiContract:
    """One versioned API contract owned by one domain.

    `endpoint_identity` is the stable thing (`P13-API-001`): a path that
    means one thing never comes to mean another, so this value is
    compared across versions rather than replaced by them."""

    contract_id: UUID
    endpoint_identity: str
    owner: DomainReference
    retired_field_names: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if not self.endpoint_identity:
            raise ValueError("endpoint_identity must not be empty")

    def reject_field_reuse(self, proposed_field_names: Sequence[str]) -> None:
        """Refuse to reintroduce a retired field name (`P13-API-006`).

        A retired field name stays retired. The refusal is here rather
        than in review because the shape of the mistake — reusing a
        familiar name for a new meaning — is exactly the one a reviewer
        reads past."""
        reused = sorted(set(proposed_field_names) & self.retired_field_names)
        if reused:
            raise SemanticReviewRequiredError(
                f"{self.endpoint_identity}: field name(s) {reused} were retired and are never "
                f"reused for a new meaning; a new meaning takes a new name"
            )


@dataclass(frozen=True, slots=True)
class ApiVersion:
    """One version of an API contract.

    `is_latest_alias` is fixed to `False` and validated: `P13-API-011`
    requires explicit version negotiation with no "latest" that silently
    moves under a caller, and a field that can only be `False` is a rule
    a future edit has to argue with rather than forget."""

    version_id: UUID
    contract_id: UUID
    version_label: str
    request_schema_version_id: UUID
    response_schema_version_id: UUID
    published_at: datetime
    widens_privilege: bool = False
    is_latest_alias: bool = False

    def __post_init__(self) -> None:
        require_timezone(self.published_at, field="ApiVersion.published_at")
        if self.is_latest_alias:
            raise ValueError(
                "version negotiation is explicit; there is no 'latest' that silently moves "
                "under a caller (P13-API-011)"
            )


@dataclass(frozen=True, slots=True)
class ApiDeprecation:
    """An explicit, announced, dated and discoverable deprecation
    (`P13-API-004`), with the coexistence window `P13-API-012` requires
    per breaking change."""

    version_id: UUID
    announced_at: datetime
    coexistence_ends_at: datetime
    replacement_version_id: UUID
    reason_code: str

    def __post_init__(self) -> None:
        require_timezone(self.announced_at, field="ApiDeprecation.announced_at")
        require_timezone(self.coexistence_ends_at, field="ApiDeprecation.coexistence_ends_at")
        if self.coexistence_ends_at <= self.announced_at:
            raise ValueError("the coexistence window must end after the announcement")

    def require_window_elapsed(self, now: datetime) -> None:
        """Refuse retirement before the stated end date."""
        require_timezone(now, field="now")
        if now < self.coexistence_ends_at:
            raise DeprecationWindowIncompleteError(
                f"api version {self.version_id}: the coexistence window ends at "
                f"{self.coexistence_ends_at.isoformat()} and retirement was attempted at "
                f"{now.isoformat()}"
            )


class ConsumerReadinessState(StrEnum):
    MIGRATED = "migrated"
    IN_PROGRESS = "in_progress"
    NOT_STARTED = "not_started"
    UNREGISTERED = "unregistered"


@dataclass(frozen=True, slots=True)
class ConsumerCompatibilityStatus:
    """One registered consumer's readiness for one target version.

    Consumer telemetry carries **no sensitive payload** (`P13-API-013`):
    which consumers use which version, never what they sent. There is
    deliberately no field here that could hold a request body."""

    consumer_id: UUID
    consumer_name: str
    target_version_id: UUID
    state: ConsumerReadinessState
    observed_at: datetime

    def __post_init__(self) -> None:
        require_timezone(self.observed_at, field="ConsumerCompatibilityStatus.observed_at")


@dataclass(frozen=True, slots=True)
class ApiMigrationPlan:
    """The migration plan a breaking change requires (`P13-GOV-002`)."""

    plan_id: UUID
    contract_id: UUID
    from_version_id: UUID
    to_version_id: UUID
    steps: tuple[str, ...]
    evidence: EvidenceReference
    rollback_available: bool
    forward_fix_only: bool = False

    def __post_init__(self) -> None:
        if not self.steps:
            raise ValueError("an API migration plan requires at least one step")
        if self.rollback_available and self.forward_fix_only:
            raise ValueError(
                "a change is either rollback-capable or explicitly forward-fix-only, "
                "not both (P13-API-014)"
            )
        if not self.rollback_available and not self.forward_fix_only:
            raise ValueError(
                "a rollback path exists and is stated, or the change is explicitly declared "
                "forward-fix-only with that consequence accepted (P13-API-014)"
            )


# ---------------------------------------------------------------------------
# Contract change governance
# ---------------------------------------------------------------------------


class ContractChangeStage(StrEnum):
    """`P13-GOV-001`'s sequence, as an ordered enum. Every stage is
    passed through; there is no edge that skips one."""

    PROPOSED = "change_proposed"
    IMPACT_ASSESSED = "impact_assessed"
    COMPATIBILITY_CLASSIFIED = "compatibility_classified"
    REVIEWED = "security_privacy_legal_reviewed"
    CONSUMER_IMPACT_REVIEWED = "consumer_impact_reviewed"
    MIGRATION_PLAN_APPROVED = "migration_plan_approved"
    SCHEMA_PUBLISHED = "schema_published"
    COEXISTENCE = "coexistence_period"
    CONSUMER_MIGRATION = "consumer_migration"
    DEPRECATION = "deprecation"
    RETIREMENT = "retirement"


#: The ordered stage list, used to check that a change has not skipped
#: one. Kept as data so the sequence is one fact in one place.
CONTRACT_CHANGE_SEQUENCE: tuple[ContractChangeStage, ...] = tuple(ContractChangeStage)


@dataclass(frozen=True, slots=True)
class BreakingChangeRecord:
    """The thirteen fields `P13-GOV-002` makes mandatory.

    Every one is required by the type. A breaking change missing any of
    them is not approvable, and the enforcement is construction-time
    rather than review-time so the gap cannot reach a reviewer's desk
    looking complete."""

    change_id: UUID
    explicit_reason: str
    owner: DomainReference
    impact_summary: str
    affected_domains: tuple[str, ...]
    migration_plan: ApiMigrationPlan
    rollback_statement: str
    data_migration_reference: UUID | None
    event_replay_impact: str
    api_coexistence_ends_at: datetime
    deadline_at: datetime
    approval_by: ActorReference
    proposed_by: ActorReference
    evidence: EvidenceReference
    final_retirement_decision: str
    rollout_flag_name: str | None = None

    def __post_init__(self) -> None:
        require_timezone(
            self.api_coexistence_ends_at, field="BreakingChangeRecord.api_coexistence_ends_at"
        )
        require_timezone(self.deadline_at, field="BreakingChangeRecord.deadline_at")
        for name in (
            "explicit_reason",
            "impact_summary",
            "rollback_statement",
            "event_replay_impact",
            "final_retirement_decision",
        ):
            if not getattr(self, name):
                raise BreakingChangeNotApprovedError(
                    f"a breaking change records {name!r}; a breaking change missing any of "
                    f"P13-GOV-002's mandatory fields is not approvable"
                )
        if not self.affected_domains:
            raise BreakingChangeNotApprovedError(
                "a breaking change records the domains it affects, even where the answer is "
                "one domain; an empty list is an unanswered question, not an answer"
            )
        if self.approval_by.actor_id == self.proposed_by.actor_id:
            raise BreakingChangeNotApprovedError(
                "approval authority for a breaking change is separated from the authority "
                "that proposed it (P13-GOV-005)"
            )


def reject_flag_bypassing_gate(
    *, flag_name: str | None, change_approved: bool, gate_name: str
) -> None:
    """Refuse a feature flag standing in for an approval
    (`P13-GOV-004`, FIR-INV-006).

    A flag may control the rollout of an already-approved,
    already-compatible change. Where the change is not approved, the flag
    is a gate-skip with a friendly name, and a gate a flag can skip was
    never a gate."""
    if flag_name is not None and not change_approved:
        raise BreakingChangeNotApprovedError(
            f"feature flag {flag_name!r} cannot stand in for the {gate_name} gate; a flag may "
            f"control rollout of an approved, compatible change and may not substitute for "
            f"the approval"
        )


def reject_hidden_privilege_expansion(
    version: ApiVersion, *, privileged_grant_present: bool
) -> None:
    """A contract change that widens what a caller can reach is a
    privileged change requiring PACK-12 authority, whatever its shape
    (`P13-API-008`)."""
    if version.widens_privilege and not privileged_grant_present:
        raise BreakingChangeNotApprovedError(
            f"api version {version.version_id} widens what a caller can reach; that is a "
            f"privileged change requiring PACK-12 authority regardless of how small the "
            f"structural diff is"
        )


def require_consumers_migrated(
    statuses: Sequence[ConsumerCompatibilityStatus], *, context: str
) -> None:
    """Refuse field removal or retirement before consumer migration is
    demonstrated through the consumer registry (`P13-API-009`)."""
    unregistered = [s for s in statuses if s.state is ConsumerReadinessState.UNREGISTERED]
    if unregistered:
        raise ConsumerNotRegisteredError(
            f"{context}: consumer(s) {[s.consumer_name for s in unregistered]} are not "
            f"registered and therefore receive no compatibility protection; this is the "
            f"stated consequence of non-registration, not a surprise"
        )
    pending = [s for s in statuses if s.state is not ConsumerReadinessState.MIGRATED]
    if pending:
        raise ConsumerNotReadyError(
            f"{context}: registered consumer(s) {[s.consumer_name for s in pending]} have not "
            f"migrated; no field is removed before consumer migration is demonstrated"
        )


# ---------------------------------------------------------------------------
# Event contract evolution
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class EventContractVersion:
    """Envelope version, payload version and schema version, recorded as
    three distinct fields (`P13-EVO-002`).

    They are three because they change for three different reasons, and a
    single "version" field would make an envelope change look like a
    payload change to every consumer."""

    event_family: str
    envelope_version: str
    payload_version: str
    schema_version_id: UUID
    semantic_version: str

    def __post_init__(self) -> None:
        if not self.event_family:
            raise ValueError("event_family must not be empty")
        if "." not in self.envelope_version:
            raise ValueError("envelope_version follows the canon's '<major>.<minor>' form")


@dataclass(frozen=True, slots=True)
class EventConsumerVersionSupport:
    """The versions a consumer declares it supports (`P13-EVO-005`)."""

    consumer_name: str
    consumer_domain: DomainReference
    event_family: str
    supported_payload_versions: frozenset[str]
    fails_closed_on_unsupported: bool = True

    def __post_init__(self) -> None:
        if not self.fails_closed_on_unsupported:
            raise ValueError(
                "an unsupported version fails closed or goes to a controlled dead-letter; "
                "a best-effort partial parse is not an option (P13-EVO-006)"
            )
        if not self.supported_payload_versions:
            raise ValueError("a consumer declares at least one supported payload version")

    def require_supported(self, payload_version: str) -> None:
        if payload_version not in self.supported_payload_versions:
            raise EventVersionUnsupportedError(
                f"consumer {self.consumer_name!r} supports "
                f"{sorted(self.supported_payload_versions)} of {self.event_family!r} and "
                f"received {payload_version!r}; it fails closed rather than guessing"
            )


#: The value an upcaster produces where the new schema requires a fact
#: the old event did not carry (`P13-EVO-008`). An explicit
#: not-determined value, never a plausible default: a consent, an
#: authority, an approval, a classification or a date that the original
#: did not carry is a legal fact, and inventing one is worse than
#: refusing.
NOT_DETERMINED = "not_determined"


class UpcastOutcome(StrEnum):
    TRANSFORMED = "transformed"
    NOT_DETERMINED_RECORDED = "not_determined_recorded"
    REFUSED = "refused"


@dataclass(frozen=True, slots=True)
class UpcastResult:
    """What an upcaster produced, and how honest it had to be about it."""

    outcome: UpcastOutcome
    payload: Mapping[str, Any]
    undetermined_fields: tuple[str, ...] = ()
    reason_code: str | None = None


@dataclass(frozen=True, slots=True)
class EventUpcasterReference:
    """A deterministic, testable upcaster (`P13-EVO-007`).

    The transformation function is held by reference so the registry can
    record *which* upcaster ran without owning its implementation. The
    two guarantees the type enforces are that the same input always
    produces the same output — checked by
    `assert_deterministic` — and that required facts the source lacks
    become `NOT_DETERMINED` rather than a guess."""

    upcaster_id: UUID
    event_family: str
    from_payload_version: str
    to_payload_version: str
    transform: Callable[[Mapping[str, Any]], Mapping[str, Any]]
    required_target_fields: tuple[str, ...] = ()

    def upcast(self, payload: Mapping[str, Any]) -> UpcastResult:
        """Transform `payload`, recording any fact the source could not
        supply.

        Never fills a missing required field. Where one is missing the
        result carries `NOT_DETERMINED` for it and says so in
        `undetermined_fields`, so a downstream consumer sees an explicit
        absence rather than a plausible value."""
        transformed = dict(self.transform(payload))
        undetermined: list[str] = []
        for field_name in self.required_target_fields:
            if transformed.get(field_name) in (None, ""):
                transformed[field_name] = NOT_DETERMINED
                undetermined.append(field_name)
        if undetermined:
            return UpcastResult(
                outcome=UpcastOutcome.NOT_DETERMINED_RECORDED,
                payload=transformed,
                undetermined_fields=tuple(sorted(undetermined)),
                reason_code="SEMANTIC_REVIEW_REQUIRED",
            )
        return UpcastResult(outcome=UpcastOutcome.TRANSFORMED, payload=transformed)

    def assert_deterministic(self, samples: Sequence[Mapping[str, Any]]) -> bool:
        """Run each recorded historical payload twice and compare.

        Returns a bool rather than raising so a test can assert on it and
        an operator surface can display it. Determinism over *recorded
        historical payloads* is the specific obligation `P13-EVO-007`
        states; determinism over synthetic inputs would prove less."""
        for sample in samples:
            first = self.upcast(sample)
            second = self.upcast(sample)
            if first != second:
                return False
        return True


@dataclass(frozen=True, slots=True)
class EventCompatibilityAssessment:
    """A compatibility assessment for one event family's payload change.

    Distinct from `CompatibilityAssessment` because an event carries
    history: the same change is assessed both for new events and for the
    replayability of old ones (`P13-EVO-004`)."""

    assessment_id: UUID
    event_family: str
    from_payload_version: str
    to_payload_version: str
    verdict: CompatibilityMode
    historical_events_remain_interpretable: bool
    upcaster: EventUpcasterReference | None = None

    def __post_init__(self) -> None:
        if not self.historical_events_remain_interpretable:
            raise SemanticReviewRequiredError(
                f"{self.event_family}: a new schema does not change the meaning of an old "
                f"event (P13-EVO-004), and a historical event is never rewritten "
                f"(P13-EVO-003); an assessment that cannot assert this is not complete"
            )


def resolve_unknown_enum_value(value: str, *, known_values: frozenset[str], context: str) -> str:
    """Return `value` when known; otherwise surface it as unknown.

    Never maps to a default. Defaulting an unknown status to "normal" is
    how a novel failure becomes invisible (`P13-EVO-012`), so the unknown
    value is returned marked rather than replaced, and the caller handles
    it with a reason code."""
    if value in known_values:
        return value
    return f"{NOT_DETERMINED}:{context}:{value}"
