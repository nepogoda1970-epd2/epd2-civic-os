"""Finance Service reporting - the reporting obligation, the
effective-dated perimeter, the create-once snapshot, the twelve report
states and the independent audit engagement (PACK-10 sections 4.9-4.10
and 8.2.15-8.2.19; canon 0.8.0 sections 19f.16-19f.18).

Pure, like `ledger` and `records`: no I/O, no clock, no storage. Every
aggregate is a frozen, slotted dataclass with an append-only `history`
tuple, and every transition returns a NEW instance carrying one more
`RecordHistoryEntry` with the acting authority and its `ReasonCoded`
(`ФИН-05`, `ФИН-40`).

Five rules run through the module, structural here rather than procedural
in a caller:

- **No snapshot, no report.** A version is preparable only from a frozen
  `ReportSnapshot` and names exactly one for life; the snapshot freezes
  the perimeter too, so a reorganisation never changes the perimeter of a
  closed or submitted period (canon 19f.16, `ФИН-24`, `ФИН-25`).
- **Silence is never acceptance.** `accepted_reference_recorded` is
  reachable **only** from an explicit authoritative external reference -
  a PACK-09 notice-effect reference from a governed
  `NoticeEffectDecision`. Delivery, receipt and read telemetry are
  recorded as their own facts and refused as transition inputs (canon
  19f.17, `ФИН-26`, `ФИН-27`).
- **Approval is not publication, and publication is not approval.**
  Publication requires an approval **and** a separate publication
  authorisation, checked independently (`ФИН-28`, `ФИН-34`).
- **A correction is a new version, never a rewrite.** The predecessor is
  `superseded` and stays readable; the only delete path is
  `delete_report_version`, which exists to refuse (`ФИН-05`).
- **The audit writes into nothing it audits.** Append-only findings, one
  create-once conclusion, independence re-verified at opening, at every
  finding and at conclusion (canon 19f.18, `ФИН-29`, `ФИН-30`).

**On the state names.** Canon 19f.17 fixes *twelve* report states; this
module spells them with the names PACK-10 adopted, which say in the
identifier what the canon list says in prose: a recorded *reference* to
an external act is not the external act, and acceptance is a recorded
reference and never an inference.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, datetime
from enum import StrEnum
from typing import ClassVar
from uuid import UUID

from epd2_finance_service.authorization import (
    AuthorizationPort,
    assert_auditor_independent,
    assert_not_self_approval,
)
from epd2_finance_service.domain import (
    AuthorityReference,
    EvidenceReference,
    OrganizationalScopeRef,
    PolicyBinding,
    ReasonCoded,
    ReportingPeriodRef,
    deterministic_digest,
    require_timezone,
)
from epd2_finance_service.exceptions import (
    AuditIncompleteError,
    AuditorIndependenceViolationError,
    ExternalAcceptanceMissingError,
    ExternalAcknowledgementNotAuthoritativeError,
    GovernedRecordDeletionForbiddenError,
    ImmutableRecordModificationAttemptedError,
    MonetaryAmountInvalidError,
    PublicationNotAllowedError,
    ReportApprovalMissingError,
    ReportingPerimeterUndeterminedError,
    ReportSignOffMissingError,
    ReportSnapshotMismatchError,
    ReportSnapshotMissingError,
    ReportValidationIncompleteError,
    UnauthorizedStateTransitionError,
)
from epd2_finance_service.records import GovernedAct, RecordHistoryEntry

# ---------------------------------------------------------------------------
# Shared structural helpers
# ---------------------------------------------------------------------------


def _require_text(value: str, field_name: str) -> None:
    """Structural non-emptiness check, raising the code `domain.py` uses
    for field validation rather than a bare `ValueError` (`ФИН-40`)."""
    if not value or not value.strip():
        raise MonetaryAmountInvalidError(f"{field_name} must be a non-empty string")


def _require_positive(value: int, field_name: str) -> None:
    if value < 1:
        raise MonetaryAmountInvalidError(f"{field_name} must be a positive integer")


def _appended(
    history: tuple[RecordHistoryEntry, ...], act: GovernedAct, action: str, state_after: str
) -> tuple[RecordHistoryEntry, ...]:
    """Append one history entry, numbering it from the existing tuple."""
    entry = RecordHistoryEntry(
        sequence=len(history) + 1,
        occurred_at=act.at,
        action=action,
        reason=act.reason,
        acting_authority=act.by_authority,
        state_after=state_after,
        policy=act.policy,
    )
    return (*history, entry)


# ---------------------------------------------------------------------------
# Reporting obligation
# ---------------------------------------------------------------------------


class ReportingObligationKind(StrEnum):
    """Structural families of reporting obligation (spec 8.2.15). The
    legally exact catalogue is a versioned
    `FinancePolicy(reporting_obligation)` value, not a code change (canon
    19f.20); this enum is only the family the lifecycle needs."""

    STATUTORY_ANNUAL_REPORT = "statutory_annual_report"
    INTERIM_REPORT = "interim_report"
    CAMPAIGN_FINANCE_REPORT = "campaign_finance_report"
    DONATION_DISCLOSURE = "donation_disclosure"
    AUDIT_REPORT = "audit_report"
    OTHER_OBLIGATION = "other_obligation"


class ReportingObligationState(StrEnum):
    """`created` -> `active` -> (`fulfilled` | `waived` | `superseded`)
    (canon 19f.16, spec 8.2.15)."""

    CREATED = "created"
    ACTIVE = "active"
    FULFILLED = "fulfilled"
    WAIVED = "waived"
    SUPERSEDED = "superseded"


#: Permitted obligation transitions. Fulfilment, waiver and supersession
#: are reachable only from `active`: a "fulfilled" obligation that was
#: never active would be a silent exemption wearing a status (19f.16).
_ALLOWED_OBLIGATION_TRANSITIONS: frozenset[
    tuple[ReportingObligationState, ReportingObligationState]
] = frozenset(
    {
        (ReportingObligationState.CREATED, ReportingObligationState.ACTIVE),
        (ReportingObligationState.ACTIVE, ReportingObligationState.FULFILLED),
        (ReportingObligationState.ACTIVE, ReportingObligationState.WAIVED),
        (ReportingObligationState.ACTIVE, ReportingObligationState.SUPERSEDED),
    }
)


@dataclass(frozen=True, slots=True)
class ReportingObligation:
    """A legal duty to report, for one scope and one period (spec 8.2.15,
    canon 19f.16).

    `statutory_deadline_reference` is a PACK-09 `DeadlineRef` carried as
    an **opaque string** (`ФИН-44`); the scope may sit higher than the
    scopes whose data it consolidates (canon 19f.19). Fulfilment is
    possible **only** through a recorded submission reference, and a
    silent waiver cannot be expressed at all (`ФИН-40`)."""

    obligation_id: UUID
    scope: OrganizationalScopeRef
    period: ReportingPeriodRef
    obligation_kind: ReportingObligationKind
    statutory_deadline_reference: str
    state: ReportingObligationState = ReportingObligationState.CREATED
    fulfilling_submission_reference: str | None = None
    history: tuple[RecordHistoryEntry, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.statutory_deadline_reference, "statutory_deadline_reference")
        self.scope.assert_matches(self.period.scope)
        if (
            self.state is ReportingObligationState.FULFILLED
            and self.fulfilling_submission_reference is None
        ):
            raise UnauthorizedStateTransitionError(
                "a fulfilled reporting obligation must name the submission that fulfilled it"
            )

    def _to(
        self,
        target: ReportingObligationState,
        act: GovernedAct,
        action: str,
        *,
        fulfilling_submission_reference: str | None = None,
    ) -> ReportingObligation:
        if (self.state, target) not in _ALLOWED_OBLIGATION_TRANSITIONS:
            raise UnauthorizedStateTransitionError(
                f"a {self.state!s} reporting obligation cannot transition to {target!s}"
            )
        self.scope.assert_matches(act.by_authority.scope)
        return replace(
            self,
            state=target,
            fulfilling_submission_reference=(
                fulfilling_submission_reference or self.fulfilling_submission_reference
            ),
            history=_appended(self.history, act, action, str(target)),
        )

    def activate(self, act: GovernedAct) -> ReportingObligation:
        """Make the obligation live for its period (canon 19f.16)."""
        return self._to(ReportingObligationState.ACTIVE, act, "activated")

    def fulfil(self, act: GovernedAct, *, submission_reference: str) -> ReportingObligation:
        """Record fulfilment against the submission that achieved it.

        The reference is mandatory, and its absence is a forbidden
        transition rather than a missing field: canon 19f.16 says
        fulfilment happens *only* through a submission record, never
        through publication."""
        if not submission_reference or not submission_reference.strip():
            raise UnauthorizedStateTransitionError(
                "a reporting obligation is fulfilled only by a recorded submission - "
                "fulfilment is never derived from publication or from elapsed time"
            )
        return self._to(
            ReportingObligationState.FULFILLED,
            act,
            "fulfilled",
            fulfilling_submission_reference=submission_reference,
        )

    def waive(self, act: GovernedAct) -> ReportingObligation:
        """Waive the obligation. Never silent: `GovernedAct` carries the
        authority policy names and the `ReasonCoded` (`ФИН-40`)."""
        return self._to(ReportingObligationState.WAIVED, act, "waived")

    def supersede(self, act: GovernedAct) -> ReportingObligation:
        """Supersede the obligation because the legal basis or perimeter
        changed. The record stays readable (`ФИН-05`)."""
        return self._to(ReportingObligationState.SUPERSEDED, act, "superseded")


# ---------------------------------------------------------------------------
# Reporting perimeter
# ---------------------------------------------------------------------------


class PerimeterDefinitionState(StrEnum):
    """`draft` -> `active` -> `superseded` (canon 19f.16, spec 8.2.16)."""

    DRAFT = "draft"
    ACTIVE = "active"
    SUPERSEDED = "superseded"


_ALLOWED_PERIMETER_TRANSITIONS: frozenset[
    tuple[PerimeterDefinitionState, PerimeterDefinitionState]
] = frozenset(
    {
        (PerimeterDefinitionState.DRAFT, PerimeterDefinitionState.ACTIVE),
        (PerimeterDefinitionState.ACTIVE, PerimeterDefinitionState.SUPERSEDED),
        (PerimeterDefinitionState.DRAFT, PerimeterDefinitionState.SUPERSEDED),
    }
)


@dataclass(frozen=True, slots=True)
class ReportingPerimeterDefinition:
    """The effective-dated, versioned authoritative record of which
    scopes a report covers (spec 8.2.16, canon 19f.16).

    Authoritative on purpose: canon 19f.16 forbids deriving the perimeter
    from the hierarchy as it stands at report time, which would make a
    report's meaning depend on a later reorganisation. An active
    definition is not editable - `amend_draft` is the only edit path -
    and a change is a new version (`ФИН-05`, `ФИН-25`)."""

    definition_id: UUID
    scope: OrganizationalScopeRef
    version: int
    effective_from: date
    included_scopes: tuple[OrganizationalScopeRef, ...]
    effective_until: date | None = None
    state: PerimeterDefinitionState = PerimeterDefinitionState.DRAFT
    history: tuple[RecordHistoryEntry, ...] = ()

    def __post_init__(self) -> None:
        _require_positive(self.version, "version")
        if self.effective_until is not None and self.effective_until < self.effective_from:
            raise ReportingPerimeterUndeterminedError(
                "effective_until must not precede effective_from"
            )
        if self.state is PerimeterDefinitionState.ACTIVE and not self.included_scopes:
            raise ReportingPerimeterUndeterminedError(
                "an active perimeter definition must include at least one organizational scope"
            )

    def amend_draft(
        self,
        *,
        included_scopes: tuple[OrganizationalScopeRef, ...] | None = None,
        effective_from: date | None = None,
        effective_until: date | None = None,
    ) -> ReportingPerimeterDefinition:
        """Edit a draft definition, returning a new instance.

        The **only** edit path here, refusing anything that is not a
        draft, so "editing an active definition" and "retroactively
        changing a definition a snapshot already used" both raise by
        construction rather than by a per-field check (`ФИН-25`)."""
        if self.state is not PerimeterDefinitionState.DRAFT:
            raise ImmutableRecordModificationAttemptedError(
                f"a {self.state!s} perimeter definition is immutable; "
                "a changed perimeter is a new version"
            )
        return replace(
            self,
            included_scopes=(self.included_scopes if included_scopes is None else included_scopes),
            effective_from=self.effective_from if effective_from is None else effective_from,
            effective_until=(self.effective_until if effective_until is None else effective_until),
        )

    def _to(
        self, target: PerimeterDefinitionState, act: GovernedAct, action: str
    ) -> ReportingPerimeterDefinition:
        if (self.state, target) not in _ALLOWED_PERIMETER_TRANSITIONS:
            raise UnauthorizedStateTransitionError(
                f"a {self.state!s} perimeter definition cannot transition to {target!s}"
            )
        self.scope.assert_matches(act.by_authority.scope)
        return replace(
            self, state=target, history=_appended(self.history, act, action, str(target))
        )

    def activate(self, act: GovernedAct) -> ReportingPerimeterDefinition:
        """Make this version the effective perimeter. An empty perimeter
        is refused: an undeterminable perimeter fails closed
        (`ФИН-41`)."""
        if not self.included_scopes:
            raise ReportingPerimeterUndeterminedError(
                "an active perimeter definition must include at least one organizational scope"
            )
        return self._to(PerimeterDefinitionState.ACTIVE, act, "activated")

    def supersede(self, act: GovernedAct) -> ReportingPerimeterDefinition:
        """Supersede this version with a later one. The superseded
        definition stays readable, because reports frozen against it must
        remain interpretable (`ФИН-05`)."""
        return self._to(PerimeterDefinitionState.SUPERSEDED, act, "superseded")


@dataclass(frozen=True, slots=True)
class PerimeterSnapshot:
    """The frozen perimeter a report version was computed against.

    Frozen separately from the definition for the canon's reason: *a
    later reorganisation never changes the perimeter of a closed or
    submitted period* (19e.9, 19e.10, 19f.16). It holds scope references
    and a digest - never a live pointer that would be re-resolved at read
    time, and never document bytes."""

    definition_id: UUID
    definition_version: int
    included_scopes: tuple[OrganizationalScopeRef, ...]
    digest: str
    frozen_at: datetime

    def __post_init__(self) -> None:
        _require_text(self.digest, "digest")
        require_timezone(self.frozen_at, context="PerimeterSnapshot.frozen_at")
        if not self.included_scopes:
            raise ReportingPerimeterUndeterminedError(
                "a perimeter snapshot must include at least one organizational scope"
            )


def freeze_perimeter(definition: ReportingPerimeterDefinition, at: datetime) -> PerimeterSnapshot:
    """Freeze an active perimeter definition into an immutable snapshot
    (canon 19f.16).

    Only an **active** definition may be frozen: a draft has not been
    decided and a superseded one has been replaced, so neither can be
    what a report claims to cover - both raise
    `ReportingPerimeterUndeterminedError` (`ФИН-41`). The digest covers
    the identity, the version and the scope ids **in sorted order**
    (`ФИН-24`)."""
    if definition.state is not PerimeterDefinitionState.ACTIVE:
        raise ReportingPerimeterUndeterminedError(
            f"only an active perimeter definition can be frozen; this one is {definition.state!s}"
        )
    if not definition.included_scopes:
        raise ReportingPerimeterUndeterminedError(
            "a perimeter definition with no included scope cannot be frozen"
        )
    require_timezone(at, context="freeze_perimeter.at")
    scope_ids = sorted(str(scope.organization_id) for scope in definition.included_scopes)
    digest = deterministic_digest(
        str(definition.definition_id), str(definition.version), "|".join(scope_ids)
    )
    return PerimeterSnapshot(
        definition_id=definition.definition_id,
        definition_version=definition.version,
        included_scopes=definition.included_scopes,
        digest=digest,
        frozen_at=at,
    )


# ---------------------------------------------------------------------------
# The report snapshot
# ---------------------------------------------------------------------------


def compute_snapshot_content_digest(
    perimeter: PerimeterSnapshot,
    included_transaction_ids: tuple[UUID, ...],
    included_entry_ids: tuple[UUID, ...],
    policy_bindings: tuple[PolicyBinding, ...],
) -> str:
    """The content digest of a report snapshot (`ФИН-24`, canon 19f.16).

    Identifiers are sorted as strings and policy bindings serialised
    field by field, so the digest depends on *what* was frozen and never
    on the order the application layer read it in. Two freezes of the
    same register state therefore agree, which is what makes "a snapshot
    is never recomputed into something different" checkable rather than
    merely asserted (spec 8.2.18)."""
    transactions = "|".join(sorted(str(identifier) for identifier in included_transaction_ids))
    entries = "|".join(sorted(str(identifier) for identifier in included_entry_ids))
    policies = "|".join(
        sorted(
            f"{binding.policy_kind}:{binding.policy_id}:{binding.policy_version}"
            f":{binding.effective_from.isoformat()}"
            for binding in policy_bindings
        )
    )
    return deterministic_digest(
        perimeter.digest, "#t:", transactions, "#e:", entries, "#p:", policies
    )


@dataclass(frozen=True, slots=True)
class ReportSnapshot:
    """The create-once, terminal `frozen` record of the source data a
    report version was computed from (spec 8.2.18, canon 19f.16).

    Holds scope references and computed identifiers, never document bytes
    (`ФИН-21`). `content_digest` is re-derived in `__post_init__` and
    compared, so a snapshot whose digest does not match its own contents
    cannot be constructed and "recomputation that would change the
    digest" is refused at the door (`ФИН-24`)."""

    snapshot_id: UUID
    scope: OrganizationalScopeRef
    period: ReportingPeriodRef
    perimeter: PerimeterSnapshot
    content_digest: str
    frozen_at: datetime
    policy_bindings: tuple[PolicyBinding, ...] = ()
    included_transaction_ids: tuple[UUID, ...] = ()
    included_entry_ids: tuple[UUID, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.content_digest, "content_digest")
        require_timezone(self.frozen_at, context="ReportSnapshot.frozen_at")
        self.scope.assert_matches(self.period.scope)
        expected = compute_snapshot_content_digest(
            self.perimeter,
            self.included_transaction_ids,
            self.included_entry_ids,
            self.policy_bindings,
        )
        if expected != self.content_digest:
            raise ImmutableRecordModificationAttemptedError(
                "the snapshot's content_digest does not match its frozen contents - "
                "a snapshot is never recomputed or edited"
            )

    @classmethod
    def freeze(
        cls,
        *,
        snapshot_id: UUID,
        scope: OrganizationalScopeRef,
        period: ReportingPeriodRef,
        perimeter: PerimeterSnapshot,
        frozen_at: datetime,
        policy_bindings: tuple[PolicyBinding, ...] = (),
        included_transaction_ids: tuple[UUID, ...] = (),
        included_entry_ids: tuple[UUID, ...] = (),
    ) -> ReportSnapshot:
        """Freeze the source set into a snapshot, computing its digest.

        A classmethod rather than a bare constructor call so the digest
        is never hand-supplied by a caller that could get it wrong
        (`ФИН-24`)."""
        return cls(
            snapshot_id=snapshot_id,
            scope=scope,
            period=period,
            perimeter=perimeter,
            content_digest=compute_snapshot_content_digest(
                perimeter, included_transaction_ids, included_entry_ids, policy_bindings
            ),
            frozen_at=frozen_at,
            policy_bindings=policy_bindings,
            included_transaction_ids=included_transaction_ids,
            included_entry_ids=included_entry_ids,
        )

    def with_changes(self, **changes: object) -> ReportSnapshot:
        """Always raises `ImmutableRecordModificationAttemptedError`.

        **Why a method that only refuses exists.** `ReportSnapshot` has a
        terminal `frozen` lifecycle with no allowed transitions (spec
        8.2.18), so the honest API for "give me a modified copy" is a
        refusal, not an omission that leaves the next reader unsure
        whether editing is forbidden or unimplemented. It also closes the
        gap the digest check cannot: a caller changing only `snapshot_id`
        or `frozen_at` would slip past `__post_init__` (`ФИН-24`)."""
        raise ImmutableRecordModificationAttemptedError(
            "a frozen report snapshot is create-once and terminal: it is never edited, "
            f"replaced or recomputed (requested changes: {sorted(changes)})"
        )


# ---------------------------------------------------------------------------
# The twelve report states
# ---------------------------------------------------------------------------


class ReportState(StrEnum):
    """The twelve canonical states of a `FinanceReportVersion`, in the
    order canon 19f.17 lists them.

    The names are the canon's own, verbatim. The governing implementation
    brief's section 10 used a different, longer vocabulary
    (`prepared`, `under_internal_review`, `internally_approved`,
    `audit_requested`, `audit_opinion_recorded`,
    `ready_for_external_submission`,
    `externally_submitted_reference_recorded`,
    `accepted_reference_recorded`, `correction_required`) while also
    instructing that the exact canonical state names be used where the
    canon already defines them, and that where canon 0.8.0 is more
    specific the canon controls. Canon 19f.17 does define all twelve, so
    the canon's names are authoritative here and the brief's vocabulary
    is recorded as an operational synonym map in
    `OPERATIONAL_STATE_SYNONYMS` and in
    `docs/architecture/finance-reporting-lifecycle.md`.

    Three names carry their own rule: `submitted` is not
    `externally_acknowledged` and neither is `externally_accepted`
    (`ФИН-26`, `ФИН-27`); `amended` and `restated` are two distinct
    correction routes, each producing a new version rather than an
    overwrite (`ФИН-05`); and `superseded` is terminal in the strict
    sense while staying readable forever."""

    DRAFT = "draft"
    INTERNALLY_REVIEWED = "internally_reviewed"
    AUDITOR_REVIEWED = "auditor_reviewed"
    APPROVED = "approved"
    SIGNED = "signed"
    SUBMITTED = "submitted"
    EXTERNALLY_ACKNOWLEDGED = "externally_acknowledged"
    EXTERNALLY_ACCEPTED = "externally_accepted"
    PUBLISHED = "published"
    AMENDED = "amended"
    RESTATED = "restated"
    SUPERSEDED = "superseded"


#: The governing brief's section-10 operational vocabulary mapped onto the
#: canonical states, so an operational reader can translate without the
#: two vocabularies ever both being live in code. Read-only documentation
#: of an intended equivalence - nothing dispatches on it.
#:
#: `prepared` and `draft` are the same state under two names: canon 19f.17
#: has preparation *produce* the `draft` version from a frozen snapshot,
#: so there is no separate post-preparation state to name.
#: `audit_requested` has no canonical state at all: requesting an audit
#: opens an `AuditEngagement`, which is a separate aggregate with its own
#: lifecycle (19f.18) and does not move the report version. Likewise
#: `correction_required` is not a report state in the canon: a recorded
#: correction request is a `ReviewRecord` with a
#: `changes_required` outcome, and the version only leaves its state when
#: an actual `amended`/`restated` successor is created.
OPERATIONAL_STATE_SYNONYMS: dict[str, ReportState | None] = {
    "prepared": ReportState.DRAFT,
    "under_internal_review": ReportState.DRAFT,
    "internally_approved": ReportState.INTERNALLY_REVIEWED,
    "audit_requested": None,
    "audit_opinion_recorded": ReportState.AUDITOR_REVIEWED,
    "ready_for_external_submission": ReportState.SIGNED,
    "externally_submitted_reference_recorded": ReportState.SUBMITTED,
    "accepted_reference_recorded": ReportState.EXTERNALLY_ACCEPTED,
    "correction_required": None,
}


#: The one ordered path through the lifecycle, from which
#: `ALLOWED_REPORT_TRANSITIONS` is derived: each state's ordinary
#: successor is the next entry. `amended`, `restated` and `superseded`
#: are not on it, because none is a step forward along one version's own
#: life - the first two create a *successor version*, and the third is
#: what happens to a version a successor displaces.
_REPORT_PROGRESSION: tuple[ReportState, ...] = (
    ReportState.DRAFT,
    ReportState.INTERNALLY_REVIEWED,
    ReportState.AUDITOR_REVIEWED,
    ReportState.APPROVED,
    ReportState.SIGNED,
    ReportState.SUBMITTED,
    ReportState.EXTERNALLY_ACKNOWLEDGED,
    ReportState.EXTERNALLY_ACCEPTED,
    ReportState.PUBLISHED,
)

#: The two states a successor version starts in. Canon 19f.17: a
#: correction yields either an amendment (`amended`) or a restatement
#: (`restated`), each carrying a typed backward reference - a correction
#: never overwrites the version it corrects. Both entry states behave
#: exactly like `draft` - a corrected version must be reviewed, audited,
#: approved and signed again, never resuming with decisions given for
#: different figures.
CORRECTION_ENTRY_STATES: frozenset[ReportState] = frozenset(
    {ReportState.AMENDED, ReportState.RESTATED}
)

#: The state from which publication is reachable **only** through the
#: guard in `FinanceReportVersion.publish`, never through the table.
#:
#: Canon 19f.17 lets a version be published once it carries the legally
#: responsible signature *and* a separate publication authorisation has
#: been issued - for a report whose legal route does not run through an
#: external acceptance decision at all. A free `signed -> published` edge
#: would make publication look like an ordinary next step and drop the
#: authorisation requirement for anyone consulting the table alone. It is
#: a guard instead: three facts, checked at the call site (`ФИН-28`,
#: `ФИН-34`). `approved` is deliberately *not* the guarded source: an
#: approved-but-unsigned version has nobody legally answerable for it.
PUBLICATION_GUARDED_SOURCE_STATE: ReportState = ReportState.SIGNED


def _build_report_transitions() -> dict[ReportState, frozenset[ReportState]]:
    """Derive the transition graph from `_REPORT_PROGRESSION`.

    Derived rather than typed out so the canon's *order* is stated once
    and the graph cannot drift from it. Three additions:

    - every state may go to `superseded` (canon 19f.17: a displaced
      version becomes `superseded` and stays readable);
    - `submitted` may go straight to `externally_accepted`, because canon
      19f.17 says acknowledgement is not implied by submission and
      acceptance is not implied by acknowledgement - so an acceptance
      decision that arrives without any acknowledgement having been
      recorded must not be unreachable;
    - `amended` and `restated` are correction *entry* states and behave
      like `draft`: their only forward edge is `internally_reviewed`.

    The guarded publication path is absent by design. There is no
    `correction_required` state: canon 19f.17 does not define one, and a
    recorded correction request is a `CorrectionRequest` on the version,
    not a status of it."""
    graph: dict[ReportState, frozenset[ReportState]] = {}
    for index, state in enumerate(_REPORT_PROGRESSION):
        targets = {ReportState.SUPERSEDED}
        if index + 1 < len(_REPORT_PROGRESSION):
            targets.add(_REPORT_PROGRESSION[index + 1])
        graph[state] = frozenset(targets)
    graph[ReportState.SUBMITTED] = frozenset(
        {*graph[ReportState.SUBMITTED], ReportState.EXTERNALLY_ACCEPTED}
    )
    for entry_state in CORRECTION_ENTRY_STATES:
        graph[entry_state] = frozenset({ReportState.INTERNALLY_REVIEWED, ReportState.SUPERSEDED})
    graph[ReportState.SUPERSEDED] = frozenset()
    return graph


#: The ordinary report-version transition graph (canon 19f.17). See
#: `_build_report_transitions` for what it contains and why the
#: publication fast path is not in it.
ALLOWED_REPORT_TRANSITIONS: dict[ReportState, frozenset[ReportState]] = _build_report_transitions()

#: States in which a version is externally visible or externally relied
#: upon, and therefore field-immutable (`ФИН-25`). Governed transitions
#: out of them still exist - an accepted version may be published, a
#: published one superseded - but no field of one may be edited.
_IMMUTABLE_REPORT_STATES: frozenset[ReportState] = frozenset(
    {
        ReportState.SUBMITTED,
        ReportState.EXTERNALLY_ACKNOWLEDGED,
        ReportState.EXTERNALLY_ACCEPTED,
        ReportState.PUBLISHED,
        ReportState.SUPERSEDED,
    }
)


def assert_report_transition_allowed(current: ReportState, target: ReportState) -> None:
    """Raise unless `current -> target` is in the ordinary transition
    graph (canon 19f.17).

    Separate from the aggregate so the graph is testable on its own and
    every method consults the same table; the publication guard is the
    single documented exception and says so at its call site."""
    if target not in ALLOWED_REPORT_TRANSITIONS[current]:
        raise UnauthorizedStateTransitionError(
            f"a {current!s} report version cannot transition to {target!s}"
        )


# ---------------------------------------------------------------------------
# The records a version accumulates
# ---------------------------------------------------------------------------


class ReviewOutcome(StrEnum):
    """The outcome of one internal review pass (spec 8.2.17).

    `FINDINGS_OPEN` is neither failure nor completion: it records that
    the review happened and did not clear, which is why approval asks for
    a `COMPLETE` review and not for "at least one review" (`ФИН-33`)."""

    COMPLETE = "complete"
    FINDINGS_OPEN = "findings_open"


@dataclass(frozen=True, slots=True)
class ReviewRecord:
    """One append-only internal review of a report version (spec 8.2.17).
    `finding_references` are opaque pointers at validation findings;
    finance records that findings exist and stays out of their
    content."""

    review_id: UUID
    reviewed_at: datetime
    reviewer: AuthorityReference
    outcome: ReviewOutcome
    finding_references: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        require_timezone(self.reviewed_at, context="ReviewRecord.reviewed_at")

    @property
    def is_complete(self) -> bool:
        return self.outcome is ReviewOutcome.COMPLETE


@dataclass(frozen=True, slots=True)
class ApprovalRecord:
    """The create-once internal approval of a report version (`ФИН-33`).
    Carries the approving authority and the policy version the approval
    rule came from, so a later policy change never rewrites what this
    approval meant (`ФИН-23`)."""

    approval_id: UUID
    approved_at: datetime
    approved_by: AuthorityReference
    reason: ReasonCoded
    policy: PolicyBinding | None = None

    def __post_init__(self) -> None:
        require_timezone(self.approved_at, context="ApprovalRecord.approved_at")


@dataclass(frozen=True, slots=True)
class CorrectionRequest:
    """One append-only recorded request that a version be corrected
    (event `finance_report.correction_requested`).

    Deliberately **not** a report state: canon 19f.17's twelve statuses do
    not include one, and inventing a thirteenth would let a version sit in
    a status the canon does not define. A request is a fact recorded
    against the version, with an author, a timestamp and a reason code
    (`ФИН-40`); the version's status only changes when an actual `amended`
    or `restated` successor is created."""

    request_id: UUID
    requested_at: datetime
    requested_by: AuthorityReference
    reason: ReasonCoded
    finding_references: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        require_timezone(self.requested_at, context="CorrectionRequest.requested_at")


class CorrectionKind(StrEnum):
    """Which of canon 19f.17's two correction routes produced a successor
    version. The successor's own entry status is this value."""

    AMENDMENT = "amended"
    RESTATEMENT = "restated"

    @property
    def entry_state(self) -> ReportState:
        return ReportState(self.value)


@dataclass(frozen=True, slots=True)
class SignatureRecord:
    """The create-once legally responsible signature of a report version
    (canon 19f.17: "подписание — юридически ответственный
    `report_signatory`").

    A distinct object from `ApprovalRecord` because canon 19f.13's
    `ФИН-33` makes preparation, approval, signing, audit, submission and
    publication six distinguishable acts with distinct authorities. The
    signature is a *record that a named authority signed*, never a
    cryptographic signature value - PACK-10 implements no signing
    primitive and claims none."""

    signature_id: UUID
    signed_at: datetime
    signed_by: AuthorityReference
    reason: ReasonCoded
    policy: PolicyBinding | None = None

    def __post_init__(self) -> None:
        require_timezone(self.signed_at, context="SignatureRecord.signed_at")


@dataclass(frozen=True, slots=True)
class AuditOpinionReference:
    """A reference to a concluded `AuditEngagement` (canon 19f.18).

    A *reference*: the conclusion itself lives on the engagement, which
    the report may not write into. Its canonical name is
    `AuditConclusion` and never "opinion" - no object may read as the
    conclusion of a statutory audit - while the report-side act keeps the
    `record_audit_opinion` name PACK-10 assigned to it."""

    engagement_id: UUID
    conclusion_reference: str
    auditor: AuthorityReference
    recorded_at: datetime

    def __post_init__(self) -> None:
        _require_text(self.conclusion_reference, "conclusion_reference")
        require_timezone(self.recorded_at, context="AuditOpinionReference.recorded_at")


@dataclass(frozen=True, slots=True)
class ExternalSubmissionReference:
    """The create-once record that a version was submitted (canon
    19f.17). Submission implies neither acknowledgement nor acceptance;
    it is one fact and nothing follows from it (`ФИН-26`)."""

    submission_reference: str
    recipient_reference: str
    submitted_at: datetime

    def __post_init__(self) -> None:
        _require_text(self.submission_reference, "submission_reference")
        _require_text(self.recipient_reference, "recipient_reference")
        require_timezone(self.submitted_at, context="ExternalSubmissionReference.submitted_at")


class ExternalStatusKind(StrEnum):
    """What an external status reference actually is (canon 19f.17,
    `ФИН-26`, `ФИН-27`).

    Four of these five are **telemetry**: an acknowledgement, a receipt,
    a delivery record and a read status say something arrived or was
    opened, and none is a legal decision. Only a governed PACK-09 notice
    effect decision is an input to the acceptance transition; they are
    enumerated together so the refusal can name what was offered."""

    ACKNOWLEDGEMENT = "acknowledgement"
    RECEIPT = "receipt"
    DELIVERY_TELEMETRY = "delivery_telemetry"
    READ_STATUS = "read_status"
    AUTHORITATIVE_ACCEPTANCE_DECISION = "authoritative_acceptance_decision"


#: The only external status kind that may drive a transition to
#: `accepted_reference_recorded` (canon 19f.17).
AUTHORITATIVE_ACCEPTANCE_KIND: ExternalStatusKind = (
    ExternalStatusKind.AUTHORITATIVE_ACCEPTANCE_DECISION
)


@dataclass(frozen=True, slots=True)
class ExternalAcceptanceReference:
    """A recorded external status about a submitted report version.

    Constructible for *any* `ExternalStatusKind`, deliberately: telemetry
    is a real fact deserving a create-once record of its own. What is
    governed is the *transition*, and putting the check there rather than
    in this constructor is what lets a delivery record be stored honestly
    instead of discarded or quietly promoted. `notice_effect_reference`
    is a PACK-09 `NoticeEffectRef` carried opaquely (`ФИН-26`)."""

    notice_effect_reference: str
    kind: ExternalStatusKind
    decided_at: datetime
    deciding_authority_reference: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.notice_effect_reference, "notice_effect_reference")
        require_timezone(self.decided_at, context="ExternalAcceptanceReference.decided_at")

    @property
    def is_authoritative(self) -> bool:
        """Whether this reference may drive the acceptance transition."""
        return self.kind is AUTHORITATIVE_ACCEPTANCE_KIND


@dataclass(frozen=True, slots=True)
class PublicationAuthorization:
    """The separate authorisation to publish a report version (`ФИН-28`,
    `ФИН-34`). A distinct object from `ApprovalRecord` because approval
    says the report is right and publication says it may be made public,
    and canon 19f.17 states in both directions that neither implies the
    other."""

    authorization_id: UUID
    scope: OrganizationalScopeRef
    authorized_by: AuthorityReference
    authorized_at: datetime
    reason: ReasonCoded
    policy: PolicyBinding | None = None

    def __post_init__(self) -> None:
        require_timezone(self.authorized_at, context="PublicationAuthorization.authorized_at")
        self.scope.assert_matches(self.authorized_by.scope)


@dataclass(frozen=True, slots=True)
class PublicationReference:
    """The create-once record of one publication, naming the
    authorisation that permitted it (canon 19f.17)."""

    publication_reference: str
    authorization_id: UUID
    published_at: datetime

    def __post_init__(self) -> None:
        _require_text(self.publication_reference, "publication_reference")
        require_timezone(self.published_at, context="PublicationReference.published_at")


# ---------------------------------------------------------------------------
# The report version
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class FinanceReportVersion:
    """One append-only version of a `Rechenschaftsbericht` (spec 8.2.17,
    canon 19f.17).

    A version is bound to **exactly one** snapshot for its whole life:
    `prepare` binds it, `assert_snapshot` refuses any other, and no
    method rebinds it. That is what makes its figures answerable - the
    snapshot froze the register state, the period locks, the policy
    versions and the perimeter (`ФИН-24`, `ФИН-25`). `scope` and `period`
    are carried alongside the specification's identifiers because every
    transition checks the acting authority's scope (`ФИН-03`).

    Once submitted, accepted, published or superseded a version is
    field-immutable: `with_changes` is the only edit path and refuses in
    those states, as `ledger.amend_draft` refuses a posted entry.
    Governed transitions out of them still exist, because publishing an
    accepted version is a decision, not an edit (`ФИН-25`)."""

    version_id: UUID
    report_id: UUID
    scope: OrganizationalScopeRef
    period: ReportingPeriodRef
    version: int
    state: ReportState = ReportState.DRAFT
    snapshot_id: UUID | None = None
    restatement_of_version_reference: UUID | None = None
    correction_kind: CorrectionKind | None = None
    review_records: tuple[ReviewRecord, ...] = ()
    correction_requests: tuple[CorrectionRequest, ...] = ()
    approval_record: ApprovalRecord | None = None
    signature_record: SignatureRecord | None = None
    audit_reference: AuditOpinionReference | None = None
    external_submission_reference: ExternalSubmissionReference | None = None
    external_acknowledgement_reference: ExternalAcceptanceReference | None = None
    external_acceptance_reference: ExternalAcceptanceReference | None = None
    publication_reference: PublicationReference | None = None
    history: tuple[RecordHistoryEntry, ...] = ()

    #: The states in which a version has not yet been reviewed and may
    #: still bind its snapshot: `draft` and the two correction entry
    #: states.
    _PREPARABLE_STATES: ClassVar[frozenset[ReportState]] = frozenset(
        {ReportState.DRAFT, ReportState.AMENDED, ReportState.RESTATED}
    )

    def __post_init__(self) -> None:
        _require_positive(self.version, "version")
        self.scope.assert_matches(self.period.scope)
        if self.restatement_of_version_reference == self.version_id:
            raise UnauthorizedStateTransitionError("a report version cannot restate itself")
        if self.state not in self._PREPARABLE_STATES and self.snapshot_id is None:
            raise ReportSnapshotMissingError(
                f"a {self.state!s} report version must name the frozen snapshot it was "
                "computed from"
            )
        if self.state in CORRECTION_ENTRY_STATES:
            if self.restatement_of_version_reference is None:
                raise UnauthorizedStateTransitionError(
                    f"a {self.state!s} version must carry the typed backward reference to the "
                    "version it corrects (canon 19f.17)"
                )
            if self.correction_kind is None or self.correction_kind.entry_state is not self.state:
                raise UnauthorizedStateTransitionError(
                    f"a {self.state!s} version must record the matching correction kind"
                )

    # -- snapshot binding ----------------------------------------------

    def assert_snapshot(self, snapshot: ReportSnapshot | None) -> ReportSnapshot:
        """Raise unless `snapshot` is the one snapshot this version is
        bound to, and return it narrowed.

        `ReportSnapshotMissingError` means no snapshot exists to work
        from - no preparation, no validation, no submission (`ФИН-24`);
        `ReportSnapshotMismatchError` means a *different* one was
        presented, an attempt to move a version onto figures it was not
        computed from (`ФИН-25`)."""
        if snapshot is None:
            raise ReportSnapshotMissingError(
                "this act requires the frozen report snapshot the version is bound to"
            )
        if self.snapshot_id is not None and self.snapshot_id != snapshot.snapshot_id:
            raise ReportSnapshotMismatchError(
                "this report version is bound to a different snapshot than the one presented"
            )
        return snapshot

    # -- actors ---------------------------------------------------------

    def actor_references_for(self, *actions: str) -> frozenset[str]:
        """The opaque actor references that performed the named actions,
        read off the append-only history rather than stored twice - a
        second copy could disagree with it (`ФИН-40`)."""
        wanted = set(actions)
        return frozenset(
            entry.acting_authority.actor_reference.strip()
            for entry in self.history
            if entry.action in wanted and entry.acting_authority.actor_reference.strip()
        )

    @property
    def operational_actor_references(self) -> frozenset[str]:
        """Everyone who acted operationally on this version: preparers,
        reviewers, approvers, submitters and publishers - what an auditor
        must be independent *of*. Canon 19f.14's "auditor against report
        preparer" and "auditor against report approver" rows are
        action-level and invisible to any role check, so the set is
        derived per version, not from role grants (`ФИН-30`)."""
        return self.actor_references_for(
            "prepared",
            "review_recorded",
            "internally_reviewed",
            "approved",
            "signed",
            "submitted",
            "published",
        )

    # -- transitions ----------------------------------------------------

    def _to(
        self, target: ReportState, act: GovernedAct, action: str, **updates: object
    ) -> FinanceReportVersion:
        """Apply one tabled transition, appending history. Every governed
        change runs through here, so none can quietly skip the scope
        check or the history entry (`ФИН-03`, `ФИН-40`)."""
        assert_report_transition_allowed(self.state, target)
        self.scope.assert_matches(act.by_authority.scope)
        return replace(
            self,
            state=target,
            history=_appended(self.history, act, action, str(target)),
            **updates,  # type: ignore[arg-type]
        )

    def prepare(self, snapshot: ReportSnapshot | None, act: GovernedAct) -> FinanceReportVersion:
        """Bind the frozen snapshot this version is computed from (event
        `finance_report.prepared`).

        Not a state transition: canon 19f.17 says preparation is performed
        *from* a frozen snapshot and lists no post-preparation status, so
        the version stays `draft` (or in its correction entry state) and
        gains the binding. Every later state requires that binding
        (`ФИН-24`). The snapshot must cover this version's own scope and
        period; one frozen for another period is not this report's source
        data."""
        if self.state not in self._PREPARABLE_STATES:
            raise UnauthorizedStateTransitionError(
                f"a {self.state!s} report version has already been prepared; a correction is a "
                "new version"
            )
        bound = self.assert_snapshot(snapshot)
        self.scope.assert_matches(bound.scope)
        self.scope.assert_matches(act.by_authority.scope)
        if bound.period.period_id != self.period.period_id:
            raise ReportSnapshotMismatchError(
                "the presented snapshot was frozen for another reporting period"
            )
        return replace(
            self,
            snapshot_id=bound.snapshot_id,
            history=_appended(self.history, act, "prepared", str(self.state)),
        )

    def record_review(self, review: ReviewRecord, act: GovernedAct) -> FinanceReportVersion:
        """Append one internal review outcome.

        Deliberately **not** a state transition: a version may carry
        several reviews - a first pass with findings open, a later one
        complete - and recording each as a transition would either invent
        a self-edge or make every review look like progress it may not
        represent. The state guard is explicit instead (`ФИН-33`)."""
        if self.state not in self._PREPARABLE_STATES:
            raise UnauthorizedStateTransitionError(
                f"an internal review can only be recorded on a version still open to review, "
                f"not a {self.state!s} one"
            )
        self.scope.assert_matches(act.by_authority.scope)
        return replace(
            self,
            review_records=(*self.review_records, review),
            history=_appended(self.history, act, "review_recorded", str(self.state)),
        )

    def record_correction_request(
        self, request: CorrectionRequest, act: GovernedAct
    ) -> FinanceReportVersion:
        """Append a recorded request that this version be corrected (event
        `finance_report.correction_requested`).

        Not a transition, because canon 19f.17 defines no
        `correction_required` status: what the request changes is the
        record, not the status. An immutable version refuses - a submitted
        or published version is corrected by an `amended`/`restated`
        successor, which `create_successor_version` produces (`ФИН-25`)."""
        if self.state in _IMMUTABLE_REPORT_STATES:
            raise ImmutableRecordModificationAttemptedError(
                f"a {self.state!s} report version cannot take a correction request; a correction "
                "is a new version"
            )
        self.scope.assert_matches(act.by_authority.scope)
        return replace(
            self,
            correction_requests=(*self.correction_requests, request),
            history=_appended(self.history, act, "correction_requested", str(self.state)),
        )

    def complete_internal_review(self, act: GovernedAct) -> FinanceReportVersion:
        """Close internal review (`draft`/`amended`/`restated` ->
        `internally_reviewed`).

        Requires a bound snapshot and at least one **completed** review:
        closing review on top of open findings would make the review
        decorative (`ФИН-33`, `ФИН-34`)."""
        if self.snapshot_id is None:
            raise ReportSnapshotMissingError(
                "internal review cannot be completed on a version that was never prepared from a "
                "frozen snapshot"
            )
        if not any(review.is_complete for review in self.review_records):
            raise ReportValidationIncompleteError(
                "completing internal review requires at least one completed review of this version"
            )
        return self._to(ReportState.INTERNALLY_REVIEWED, act, "internally_reviewed")

    def record_auditor_review(
        self,
        reference: AuditOpinionReference,
        act: GovernedAct,
        *,
        port: AuthorizationPort | None = None,
    ) -> FinanceReportVersion:
        """Record the independent auditor's review of this version
        (`internally_reviewed` -> `auditor_reviewed`).

        Canon 19f.17: "ревизорское рассмотрение требует завершённого
        `AuditEngagement` в той же scope и за тот же период". The
        engagement reference is required, and independence is re-verified
        **here**, against the actor set read from this version's own
        history rather than from role grants (`ФИН-29`, `ФИН-30`)."""
        assert_auditor_independent(
            reference.auditor, self.operational_actor_references, self.scope, port=port
        )
        return self._to(
            ReportState.AUDITOR_REVIEWED,
            act,
            "auditor_reviewed",
            audit_reference=reference,
        )

    def approve(self, approval: ApprovalRecord, act: GovernedAct) -> FinanceReportVersion:
        """Approve the version (`auditor_reviewed` -> `approved`).

        Canon 19f.17: "утверждение выполняет названный политикой орган".
        A version with no recorded audit reference raises
        `AuditIncompleteError`; the approver may not be the actor who
        prepared it - canon 19f.14's "creator against approver of the same
        object" row, checked per object because both acts fit one
        compatible role set (`ФИН-31`)."""
        if self.audit_reference is None:
            raise AuditIncompleteError(
                "approval requires a recorded conclusion from a concluded audit engagement for "
                "this scope and period"
            )
        for preparer in self.actor_references_for("prepared"):
            assert_not_self_approval(
                approval.approved_by.actor_reference, preparer, action="report approval"
            )
        return self._to(ReportState.APPROVED, act, "approved", approval_record=approval)

    def sign(self, signature: SignatureRecord, act: GovernedAct) -> FinanceReportVersion:
        """Record the legally responsible signature (`approved` ->
        `signed`).

        Canon 19f.17: signing is performed by a `report_signatory`, and
        `ФИН-33` makes it an act distinct from approval. Refuses without a
        recorded approval, and refuses when the signatory is the same
        actor as the approver: signing one's own approval collapses two of
        the six distinguishable acts into one (`ФИН-31`, `ФИН-33`)."""
        if self.approval_record is None:
            raise ReportApprovalMissingError("signing requires a recorded approval of this version")
        assert_not_self_approval(
            signature.signed_by.actor_reference,
            self.approval_record.approved_by.actor_reference,
            action="report signing",
        )
        return self._to(ReportState.SIGNED, act, "signed", signature_record=signature)

    def record_submission(
        self, reference: ExternalSubmissionReference, act: GovernedAct
    ) -> FinanceReportVersion:
        """Record the submission reference (`signed` -> `submitted`).

        Refuses without the legally responsible signature: canon 19f.17
        orders signing before submission, and re-asserting it here keeps
        the rule true if a future path reaches this call differently
        (`ФИН-33`). Submission is one fact and implies nothing further:
        not acknowledgement, not acceptance, not fulfilment - that last is
        recorded on the obligation itself (canon 19f.16, `ФИН-26`)."""
        if self.signature_record is None:
            raise ReportSignOffMissingError(
                "submission requires the legally responsible signature of this version"
            )
        return self._to(
            ReportState.SUBMITTED,
            act,
            "submitted",
            external_submission_reference=reference,
        )

    def record_external_acknowledgement(
        self, reference: ExternalAcceptanceReference, act: GovernedAct
    ) -> FinanceReportVersion:
        """Record that the recipient acknowledged receipt (`submitted` ->
        `externally_acknowledged`).

        Storable, and *only* that: canon 19f.17 states acknowledgement
        does not imply legal acceptance (`ФИН-26`, `ФИН-27`). An
        authoritative acceptance decision offered here is refused rather
        than silently downgraded to an acknowledgement - it belongs on
        `record_external_acceptance`, which is where the acceptance
        transition and its guard live."""
        if reference.is_authoritative:
            raise UnauthorizedStateTransitionError(
                "an authoritative acceptance decision is not an acknowledgement; record it "
                "through the acceptance transition"
            )
        return self._to(
            ReportState.EXTERNALLY_ACKNOWLEDGED,
            act,
            "external_acknowledgement_recorded",
            external_acknowledgement_reference=reference,
        )

    def record_external_acceptance(
        self, reference: ExternalAcceptanceReference | None, act: GovernedAct
    ) -> FinanceReportVersion:
        """Record an authoritative external acceptance decision
        (`submitted`/`externally_acknowledged` -> `externally_accepted`).

        The narrowest gate in this module (canon 19f.17, `ФИН-26`,
        `ФИН-27`). No reference raises `ExternalAcceptanceMissingError`,
        since acceptance is never inferred and no elapsed-time path to it
        exists (see `assert_no_inferred_acceptance`). An acknowledgement,
        receipt, delivery telemetry or read status offered *instead*
        raises `ExternalAcknowledgementNotAuthoritativeError`, naming
        what was offered: all four are legitimate, storable facts, and
        none is a decision."""
        if reference is None:
            raise ExternalAcceptanceMissingError(
                "acceptance requires an explicit authoritative external reference - "
                "a governed PACK-09 notice-effect decision"
            )
        if not reference.is_authoritative:
            raise ExternalAcknowledgementNotAuthoritativeError(
                f"a {reference.kind!s} reference is delivery or receipt telemetry, not a legal "
                "acceptance decision, and can never be the input to the acceptance transition"
            )
        return self._to(
            ReportState.EXTERNALLY_ACCEPTED,
            act,
            "acceptance_recorded",
            external_acceptance_reference=reference,
        )

    def publish(
        self,
        reference: PublicationReference,
        act: GovernedAct,
        *,
        publication_authorization: PublicationAuthorization | None,
    ) -> FinanceReportVersion:
        """Publish the version against a separate publication
        authorisation.

        Publication is not approval and approval is not publication
        (canon 19f.17, `ФИН-28`, `ФИН-34`), so three independent facts
        are required and each refuses on its own: a recorded approval; a
        publication authorisation presented and scoped here; and a
        publication record naming *that* authorisation - all three raising
        `PublicationNotAllowedError`.

        From `externally_accepted` this is an ordinary tabled transition;
        from `signed` it is the guarded path at
        `PUBLICATION_GUARDED_SOURCE_STATE`, absent from
        `ALLOWED_REPORT_TRANSITIONS` so nothing consulting the table
        alone can take it. Every other state refuses through the
        table."""
        if publication_authorization is None:
            raise PublicationNotAllowedError(
                "publication requires a separate publication authorisation; approval is not "
                "publication"
            )
        if self.approval_record is None:
            raise PublicationNotAllowedError(
                "publication requires a recorded approval of this version"
            )
        self.scope.assert_matches(publication_authorization.scope)
        if reference.authorization_id != publication_authorization.authorization_id:
            raise PublicationNotAllowedError(
                "the publication record does not name the publication authorisation presented"
            )
        if self.state is PUBLICATION_GUARDED_SOURCE_STATE:
            # The guarded second path: not a tabled edge, permitted here
            # only because an approval and a separate publication
            # authorisation have both been checked above.
            self.scope.assert_matches(act.by_authority.scope)
            return replace(
                self,
                state=ReportState.PUBLISHED,
                publication_reference=reference,
                history=_appended(self.history, act, "published", str(ReportState.PUBLISHED)),
            )
        return self._to(ReportState.PUBLISHED, act, "published", publication_reference=reference)

    def supersede(self, act: GovernedAct) -> FinanceReportVersion:
        """Mark this version superseded by a later one.

        Reachable from every state and terminal in the strict sense. A
        superseded version is never destroyed, overwritten or removed
        from the chain: a submitted or published version that later
        turned out wrong is part of the record of what was reported
        (canon 19f.17, `ФИН-05`)."""
        return self._to(ReportState.SUPERSEDED, act, "superseded")

    def create_successor_version(
        self, act: GovernedAct, *, version_id: UUID, correction_kind: CorrectionKind
    ) -> tuple[FinanceReportVersion, FinanceReportVersion]:
        """Create the successor a material correction requires, and
        supersede this version.

        Returns both halves of one act, so a caller cannot record the
        successor while leaving its predecessor live - which is how two
        versions of one report end up both current. The successor starts
        in `amended` or `restated` per `correction_kind` with no snapshot,
        since changed figures need their own, and carries the typed
        backward link canon 19f.17 requires. Nothing about the
        predecessor is rewritten: it becomes `superseded` and stays
        readable forever (`ФИН-05`, `ФИН-25`)."""
        superseded = self.supersede(act)
        successor = FinanceReportVersion(
            version_id=version_id,
            report_id=self.report_id,
            scope=self.scope,
            period=self.period,
            version=self.version + 1,
            state=correction_kind.entry_state,
            correction_kind=correction_kind,
            restatement_of_version_reference=self.version_id,
        )
        return superseded, successor

    # -- the single edit path -------------------------------------------

    def with_changes(
        self,
        *,
        snapshot_id: UUID | None = None,
        restatement_of_version_reference: UUID | None = None,
    ) -> FinanceReportVersion:
        """Edit a still-internal version, returning a new instance.

        The **only** field-edit path, refusing once the version has been
        submitted, accepted, published or superseded, so "editing a
        submitted or published version" raises by construction rather
        than by a per-field check (`ФИН-25`). Rebinding a bound snapshot
        is refused separately: a version names exactly one for life
        (`ФИН-24`)."""
        if self.state in _IMMUTABLE_REPORT_STATES:
            raise ImmutableRecordModificationAttemptedError(
                f"a {self.state!s} report version is immutable; a correction is a new version"
            )
        if (
            snapshot_id is not None
            and self.snapshot_id is not None
            and snapshot_id != self.snapshot_id
        ):
            raise ReportSnapshotMismatchError(
                "a report version names exactly one snapshot and never rebinds it"
            )
        return replace(
            self,
            snapshot_id=self.snapshot_id if snapshot_id is None else snapshot_id,
            restatement_of_version_reference=(
                self.restatement_of_version_reference
                if restatement_of_version_reference is None
                else restatement_of_version_reference
            ),
        )


def assert_no_inferred_acceptance(version: FinanceReportVersion, now: datetime) -> None:
    """Raise unless acceptance has been *recorded* - never inferred
    (canon 19f.17, `ФИН-26`, `ФИН-27`).

    The answer to a question the system will be asked: "the authority has
    not replied in six weeks, may we treat the report as accepted?" No -
    and no whatever `now` says, which is why `now` is validated as
    timezone-explicit and then never compared to anything. An absent
    reference raises `ExternalAcceptanceMissingError`; a stored delivery
    receipt read back as acceptance raises
    `ExternalAcknowledgementNotAuthoritativeError`."""
    require_timezone(now, context="assert_no_inferred_acceptance.now")
    reference = version.external_acceptance_reference
    if reference is None:
        raise ExternalAcceptanceMissingError(
            "no authoritative acceptance decision has been recorded for this report version - "
            "elapsed time, silence, delivery and publication never produce one"
        )
    if not reference.is_authoritative:
        raise ExternalAcknowledgementNotAuthoritativeError(
            f"the recorded external reference is a {reference.kind!s}, which is not a legal "
            "acceptance decision"
        )


def delete_report_version(version: FinanceReportVersion) -> None:
    """Always raises `GovernedRecordDeletionForbiddenError`.

    Present for the same reason `ReportSnapshot.with_changes` is: the
    honest API for an act the domain forbids is a refusal with a reason
    code, not a missing function. A newer version never destroys an
    earlier submitted, acknowledged or published one - the earlier
    version is `superseded` and stays readable (`ФИН-05`)."""
    raise GovernedRecordDeletionForbiddenError(
        f"report version {version.version_id} is a governed record and is never deleted; "
        "a replaced version is superseded and remains readable"
    )


# ---------------------------------------------------------------------------
# The independent audit engagement
# ---------------------------------------------------------------------------


class AuditEngagementState(StrEnum):
    """`opened` -> `in_progress` -> `concluded` (canon 19f.18, spec
    8.2.19)."""

    OPENED = "opened"
    IN_PROGRESS = "in_progress"
    CONCLUDED = "concluded"


@dataclass(frozen=True, slots=True)
class AuditFinding:
    """One append-only audit finding (canon 19f.18).

    A recorded finding is never edited and survives every later
    engagement; a correction is a further finding. `summary_reference` is
    a pointer, not prose: findings are disclosed only per disclosure
    policy and never in a form identifying individuals (`ФИН-35`). An
    auditor's own reconciliation is *a finding*, never an authoritative
    `ReconciliationRecord`: the audit writes into nothing it audits."""

    finding_id: UUID
    recorded_at: datetime
    recorded_by: AuthorityReference
    severity: str
    summary_reference: str
    evidence: tuple[EvidenceReference, ...] = ()

    def __post_init__(self) -> None:
        require_timezone(self.recorded_at, context="AuditFinding.recorded_at")
        _require_text(self.severity, "severity")
        _require_text(self.summary_reference, "summary_reference")


@dataclass(frozen=True, slots=True)
class AuditConclusion:
    """The create-once conclusion of an audit engagement (canon 19f.18).
    The canonical name is `AuditConclusion` and never "opinion": no
    object here may be read as the opinion of a statutory audit. Written
    once and never edited (`ФИН-05`)."""

    conclusion_id: UUID
    concluded_at: datetime
    concluded_by: AuthorityReference
    conclusion_class: str
    reason: ReasonCoded
    evidence: tuple[EvidenceReference, ...] = ()

    def __post_init__(self) -> None:
        require_timezone(self.concluded_at, context="AuditConclusion.concluded_at")
        _require_text(self.conclusion_class, "conclusion_class")


_ALLOWED_ENGAGEMENT_TRANSITIONS: frozenset[tuple[AuditEngagementState, AuditEngagementState]] = (
    frozenset(
        {
            (AuditEngagementState.OPENED, AuditEngagementState.IN_PROGRESS),
            (AuditEngagementState.IN_PROGRESS, AuditEngagementState.IN_PROGRESS),
            (AuditEngagementState.OPENED, AuditEngagementState.CONCLUDED),
            (AuditEngagementState.IN_PROGRESS, AuditEngagementState.CONCLUDED),
        }
    )
)


@dataclass(frozen=True, slots=True)
class AuditEngagement:
    """An independent financial audit of one scope and period (spec
    8.2.19, canon 19f.18).

    Append-only findings, one create-once conclusion, and independence
    re-verified at **opening, at every finding and at conclusion** -
    checking only at opening would miss a role granted mid-engagement
    (`ФИН-29`, `ФИН-30`). Every check runs through
    `authorization.assert_auditor_independent`, so this aggregate holds
    no second copy of the incompatibility matrix."""

    engagement_id: UUID
    scope: OrganizationalScopeRef
    period: ReportingPeriodRef
    auditor: AuthorityReference
    state: AuditEngagementState = AuditEngagementState.OPENED
    findings: tuple[AuditFinding, ...] = ()
    conclusion: AuditConclusion | None = None
    history: tuple[RecordHistoryEntry, ...] = ()

    def __post_init__(self) -> None:
        self.scope.assert_matches(self.period.scope)
        if self.state is AuditEngagementState.CONCLUDED and self.conclusion is None:
            raise AuditIncompleteError(
                "a concluded audit engagement must carry the conclusion it concluded with"
            )

    @classmethod
    def open(
        cls,
        act: GovernedAct,
        *,
        engagement_id: UUID,
        scope: OrganizationalScopeRef,
        period: ReportingPeriodRef,
        auditor: AuthorityReference,
        operational_actor_references: tuple[str, ...] = (),
        port: AuthorizationPort | None = None,
    ) -> AuditEngagement:
        """Open an engagement, checking independence first.

        A classmethod rather than a bare constructor call so the opening
        history entry cannot be omitted, and so the first of the three
        independence checks cannot be skipped (`ФИН-40`)."""
        assert_auditor_independent(auditor, operational_actor_references, scope, port=port)
        scope.assert_matches(act.by_authority.scope)
        return cls(
            engagement_id=engagement_id,
            scope=scope,
            period=period,
            auditor=auditor,
            state=AuditEngagementState.OPENED,
            history=_appended((), act, "opened", str(AuditEngagementState.OPENED)),
        )

    def _assert_open(self, action: str) -> None:
        if self.state is AuditEngagementState.CONCLUDED:
            raise ImmutableRecordModificationAttemptedError(
                f"a concluded audit engagement refuses {action}; a further audit is a new "
                "engagement superseding this one"
            )

    def record_finding(
        self,
        finding: AuditFinding,
        act: GovernedAct,
        *,
        operational_actor_references: tuple[str, ...] = (),
        port: AuthorizationPort | None = None,
    ) -> AuditEngagement:
        """Append a finding, re-checking independence (canon 19f.18).

        The second of the three checks: the canon requires it *at every
        finding*, and this is where a role granted after the engagement
        opened surfaces. A concluded engagement refuses - findings
        survive it, and a further audit is a new engagement
        (`ФИН-05`)."""
        self._assert_open("further findings")
        assert_auditor_independent(
            self.auditor, operational_actor_references, self.scope, port=port
        )
        target = AuditEngagementState.IN_PROGRESS
        if (self.state, target) not in _ALLOWED_ENGAGEMENT_TRANSITIONS:
            raise UnauthorizedStateTransitionError(
                f"a {self.state!s} audit engagement cannot record a finding"
            )
        self.scope.assert_matches(act.by_authority.scope)
        return replace(
            self,
            state=target,
            findings=(*self.findings, finding),
            history=_appended(self.history, act, "finding_recorded", str(target)),
        )

    def conclude(
        self,
        conclusion: AuditConclusion,
        act: GovernedAct,
        *,
        operational_actor_references: tuple[str, ...] = (),
        port: AuthorizationPort | None = None,
        minimum_findings: int = 0,
    ) -> AuditEngagement:
        """Conclude the engagement, create-once (canon 19f.18).

        Four refusals: a second conclusion raises
        `ImmutableRecordModificationAttemptedError`, since a changed
        opinion is a new engagement (`ФИН-05`); a concluding authority
        other than this engagement's own auditor, and a failed
        independence re-check - the third of the three - both raise
        `AuditorIndependenceViolationError`; and fewer findings than
        `minimum_findings` raises `AuditIncompleteError`, that count
        being a versioned policy value, not a code constant."""
        if self.conclusion is not None:
            raise ImmutableRecordModificationAttemptedError(
                "an audit conclusion is create-once; a changed conclusion is a new engagement"
            )
        if conclusion.concluded_by.authority_id != self.auditor.authority_id:
            raise AuditorIndependenceViolationError(
                "the concluding authority is not the auditor this engagement was opened for"
            )
        assert_auditor_independent(
            conclusion.concluded_by, operational_actor_references, self.scope, port=port
        )
        if len(self.findings) < minimum_findings:
            raise AuditIncompleteError(
                f"policy requires at least {minimum_findings} recorded finding(s) before an "
                f"audit engagement may conclude; {len(self.findings)} recorded"
            )
        target = AuditEngagementState.CONCLUDED
        if (self.state, target) not in _ALLOWED_ENGAGEMENT_TRANSITIONS:
            raise UnauthorizedStateTransitionError(
                f"a {self.state!s} audit engagement cannot conclude"
            )
        self.scope.assert_matches(act.by_authority.scope)
        return replace(
            self,
            state=target,
            conclusion=conclusion,
            history=_appended(self.history, act, "concluded", str(target)),
        )
