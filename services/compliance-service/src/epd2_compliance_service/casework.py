"""PACK-09's common legal-case substrate (Framework 0.8.1 section 13.1).

Framework 0.8.1 corrected PACK-09's acceptance criteria: it keeps its
name and purpose, but must now provide a *reusable* legal-case /
workflow substrate that PACK-19 (candidacy), PACK-21 (assemblies),
PACK-22 (communications), PACK-23 (complaints/ombuds) and PACK-24
(protected reporting) will build products on top of. This module is that
substrate.

It deliberately stops at primitives. There is no candidacy application,
no nomination, no ballot admission, no assembly, no quorum, no motion, no
message, no inbox, no complaint form and no investigation workflow here -
those are the later packs' products (Framework 13.2 and section 8's
proposed roadmap). What is here is the machinery all of them need and
none of them should re-invent:

| Primitive | Why every downstream pack needs it |
| --- | --- |
| `LegalCase` | one governed matter, one scope, one lifecycle, one docket |
| `JurisdictionDetermination` | who is competent to decide, recorded and challengeable |
| `CaseParty` / `Representation` | who is involved and who may act for them |
| `Filing` | an append-only docket entry, correctable only by superseding |
| `Hearing` | a scheduled procedural event with attendance and minutes references |
| `InterimMeasure` | a time-bounded provisional order with a human decision-maker |
| `ProceduralDecision` | issuance, effect, finality and enforceability as four states |
| `Remedy` | the appeal/review route attached to a decision |
| `RecusalRecord` | conflict hooks that block capability without erasing history |

## Cross-cutting rules this module enforces structurally

- **No global person identifier** (Framework hard invariant 1). Every
  human appears as a `CasePartyReference`: a random UUID minted per case
  by `mint_case_party_reference`, never reused across cases, never
  derived from identity, membership or account data, unresolvable inside
  this service. `CaseParty` has no name, address, email or date of
  birth, and there is no field on any entity here that could carry one.
- **No identity/ballot linkage** (hard invariants 2 and 38). Nothing here
  references a ballot, vote, tally, delegation or credential, and this
  module imports nothing from those services.
- **Jurisdiction before substance** (hard invariant 52). A case cannot
  reach a substantive decision without a confirmed
  `JurisdictionDetermination`; `assert_may_decide_substantively` is the
  one gate, and it fails closed.
- **Role name is not authority** (hard invariant 15). Competence is a
  recorded determination naming a specific authority reference, not a
  string that looks official.
- **Append-only everywhere it matters** (hard invariants 8 and 26). The
  docket, the case's own transition history, the jurisdiction history,
  the representation history and every decision-state change are tuples
  that only ever grow. Historical documents are not rewritten
  retroactively.
- **Retry never repeats a legal effect** (hard invariant 59). Every
  consequential transition is guarded so a replay returns the recorded
  outcome instead of producing a second one.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from epd2_compliance_service.exceptions import (
    DecisionNotEffectiveError,
    DecisionNotEnforceableError,
    DecisionNotFinalError,
    DueProcessPrerequisiteMissingError,
    FilingSequenceConflictError,
    HearingTransitionInvalidError,
    InterimMeasureAuthorityDeniedError,
    JurisdictionMissingError,
    JurisdictionNotCompetentError,
    JurisdictionScopeMismatchError,
    JurisdictionTransferRequiredError,
    ProceduralCaseTransitionInvalidError,
    ProceduralRoleConflictError,
    RecusedActorDeniedError,
    RemedyUnavailableError,
    RepresentationExpiredError,
    RepresentationInvalidError,
    RepresentationRevokedError,
)
from epd2_compliance_service.references import (
    DocumentRef,
    EvidenceRef,
    MinutesRef,
)
from epd2_core.identifiers import generate_uuid


def _require_aware(value: datetime, field_name: str) -> None:
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")


def _require_text(value: str, field_name: str) -> None:
    if not value or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")


def mint_case_party_reference() -> UUID:
    """Mint a fresh, meaningless, per-case party handle.

    Re-exported from this module (and identical in behaviour to
    `domain.mint_case_party_reference`) so the legal-case substrate is
    readable without cross-importing: this is the ONLY way a natural
    person is represented anywhere in PACK-09."""
    return generate_uuid()


# ===========================================================================
# 1. Jurisdiction (Framework 13.1, hard invariants 15 and 52)
# ===========================================================================


class CaseKind(StrEnum):
    """The kinds of governed matter this substrate carries.

    Framework hard invariant 51: complaint, petition, initiative, appeal,
    disciplinary case and whistleblowing report are *different case
    kinds* and must not be collapsed into one. The list is closed and
    extensible only by contract change, so a later pack cannot quietly
    reinterpret an existing kind."""

    DISCIPLINARY = "disciplinary"
    ARBITRATION = "arbitration"
    INTERNAL_DISPUTE = "internal_dispute"
    APPEAL = "appeal"
    COMPLAINT = "complaint"
    PETITION = "petition"
    DATA_SUBJECT_REQUEST = "data_subject_request"
    LEGAL_REQUEST = "legal_request"
    COMPLIANCE_REVIEW = "compliance_review"
    PROTECTED_REPORT = "protected_report"


class JurisdictionType(StrEnum):
    """How a competent authority derives its competence."""

    STATUTORY = "statutory"
    PARTY_STATUTE = "party_statute"
    DELEGATED = "delegated"
    APPELLATE = "appellate"
    ARBITRAL = "arbitral"


class JurisdictionStatus(StrEnum):
    """Lifecycle of a jurisdiction determination.

    `INDETERMINATE` is a real state, not an absence: it is what a
    determination carries when competence could not be established. A
    case whose jurisdiction is indeterminate fails closed rather than
    proceeding (Framework 13.3 acceptance gate 6)."""

    ASSERTED = "asserted"
    CONFIRMED = "confirmed"
    CHALLENGED = "challenged"
    DECLINED = "declined"
    TRANSFERRED = "transferred"
    INDETERMINATE = "indeterminate"


#: Only a confirmed determination lets a case proceed to substance.
_SUBSTANTIVE_JURISDICTION_STATES: frozenset[JurisdictionStatus] = frozenset(
    {JurisdictionStatus.CONFIRMED}
)


@dataclass(frozen=True, slots=True)
class JurisdictionDetermination:
    """The recorded decision that a specific competent authority has
    jurisdiction over a specific case kind in a specific scope.

    Effective-dated (`valid_from`/`valid_until`) because competence
    changes over time and a past decision has to stay explicable under
    the competence that applied when it was made.

    `competent_authority_reference` is an opaque organizational authority
    reference (a PACK-08 `OrganizationalAuthority`), never a person and
    never a role *name*: Framework hard invariant 15 states that a role
    name is not proof of authority, so this substrate never accepts one
    as such."""

    jurisdiction_id: UUID
    case_id: UUID
    organization_id: UUID
    jurisdiction_type: JurisdictionType
    case_kind: CaseKind
    competent_authority_reference: UUID
    status: JurisdictionStatus
    determined_at: datetime
    determined_by_authority_reference: UUID
    valid_from: datetime
    valid_until: datetime | None = None
    basis_reference: str = ""
    transferred_to_jurisdiction_id: UUID | None = None
    supersedes_jurisdiction_id: UUID | None = None
    reason_code: str | None = None

    def __post_init__(self) -> None:
        _require_aware(self.determined_at, "determined_at")
        _require_aware(self.valid_from, "valid_from")
        if self.valid_until is not None:
            _require_aware(self.valid_until, "valid_until")
            if self.valid_until <= self.valid_from:
                raise ValueError("valid_until must be after valid_from")
        if self.status is JurisdictionStatus.TRANSFERRED and (
            self.transferred_to_jurisdiction_id is None
        ):
            raise ValueError("a transferred determination must name its successor")

    def is_effective_at(self, at: datetime) -> bool:
        _require_aware(at, "at")
        if at < self.valid_from:
            return False
        return self.valid_until is None or at < self.valid_until

    def permits_substantive_decision_at(self, at: datetime) -> bool:
        return self.status in _SUBSTANTIVE_JURISDICTION_STATES and self.is_effective_at(at)

    def challenge(self, at: datetime, *, reason_code: str) -> JurisdictionDetermination:
        """Record a challenge. The determination keeps its identity and
        its dates; only its status moves, and the previous state stays
        recoverable from the case's jurisdiction history."""
        _require_aware(at, "at")
        if self.status in {JurisdictionStatus.TRANSFERRED, JurisdictionStatus.DECLINED}:
            raise JurisdictionNotCompetentError(
                f"a {self.status.value} jurisdiction determination cannot be challenged"
            )
        return replace(self, status=JurisdictionStatus.CHALLENGED, reason_code=reason_code)

    def transfer_to(
        self, successor_jurisdiction_id: UUID, *, at: datetime, reason_code: str
    ) -> JurisdictionDetermination:
        """Mark this determination transferred.

        The determination is NOT rewritten to describe the new authority:
        it keeps its own authority reference and gains a pointer to its
        successor, so "who was competent, and until when" stays
        answerable after any number of transfers (Framework 13.1: "preserved
        jurisdiction history")."""
        _require_aware(at, "at")
        if successor_jurisdiction_id == self.jurisdiction_id:
            raise ValueError("a transfer must name a different determination")
        return replace(
            self,
            status=JurisdictionStatus.TRANSFERRED,
            valid_until=at,
            transferred_to_jurisdiction_id=successor_jurisdiction_id,
            reason_code=reason_code,
        )


# ===========================================================================
# 2. Parties and representation (Framework 13.1)
# ===========================================================================


class PartyRole(StrEnum):
    """A party's procedural standing in one case."""

    APPLICANT = "applicant"
    CLAIMANT = "claimant"
    RESPONDENT = "respondent"
    AFFECTED_PARTY = "affected_party"
    PROCEDURAL_PARTICIPANT = "procedural_participant"
    REPRESENTATIVE = "representative"


#: Roles whose holder is a party to the matter and therefore can never be
#: its independent decision-maker.
ADVERSARIAL_PARTY_ROLES: frozenset[PartyRole] = frozenset(
    {
        PartyRole.APPLICANT,
        PartyRole.CLAIMANT,
        PartyRole.RESPONDENT,
        PartyRole.AFFECTED_PARTY,
    }
)


@dataclass(frozen=True, slots=True)
class CaseParty:
    """A participant in one case.

    Carries a `party_reference` (a per-case minted handle), a role, and a
    flag for whether this party is the authorized recipient of official
    service. It carries no name, no contact detail and no identity
    attribute - Framework hard invariant 1, enforced by there being no
    such field to populate."""

    case_party_id: UUID
    case_id: UUID
    organization_id: UUID
    party_reference: UUID
    role: PartyRole
    registered_at: datetime
    is_authorized_service_recipient: bool = False
    display_label_code: str = ""

    def __post_init__(self) -> None:
        _require_aware(self.registered_at, "registered_at")


class RepresentationStatus(StrEnum):
    ACTIVE = "active"
    REVOKED = "revoked"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"


class RepresentationAuthority(StrEnum):
    """What a mandate authorizes, enumerated rather than free text.

    Framework hard invariant 14: a downstream actor never widens scope. A
    representative holds exactly the authorities the mandate lists and
    nothing adjacent to them."""

    FILE_SUBMISSIONS = "file_submissions"
    RECEIVE_SERVICE = "receive_service"
    ATTEND_HEARING = "attend_hearing"
    REQUEST_REMEDY = "request_remedy"
    WITHDRAW_CASE = "withdraw_case"


@dataclass(frozen=True, slots=True)
class RepresentationMandate:
    """A mandate letting one per-case reference act for another.

    Both `represented_party_reference` and `representative_reference` are
    per-case handles. A mandate never crosses cases: representing someone
    in case A says nothing about case B, which is what keeps the party
    model from becoming a correlation graph."""

    mandate_id: UUID
    case_id: UUID
    organization_id: UUID
    represented_party_reference: UUID
    representative_reference: UUID
    authorities: frozenset[RepresentationAuthority]
    valid_from: datetime
    status: RepresentationStatus = RepresentationStatus.ACTIVE
    valid_until: datetime | None = None
    revoked_at: datetime | None = None
    revocation_reason_code: str | None = None
    mandate_basis_reference: str = ""

    def __post_init__(self) -> None:
        _require_aware(self.valid_from, "valid_from")
        if self.valid_until is not None:
            _require_aware(self.valid_until, "valid_until")
            if self.valid_until <= self.valid_from:
                raise ValueError("valid_until must be after valid_from")
        if self.revoked_at is not None:
            _require_aware(self.revoked_at, "revoked_at")
        if not self.authorities:
            raise ValueError("a representation mandate must grant at least one authority")
        if self.represented_party_reference == self.representative_reference:
            raise ProceduralRoleConflictError(
                "a party cannot be its own representative on the same case"
            )

    def revoke(self, at: datetime, *, reason_code: str) -> RepresentationMandate:
        """Revoke the mandate.

        Prior filings made under it are untouched - revocation removes the
        ability to act from now on, it does not reach back into the
        docket (Framework 13.1: "прекращение representation не стирает
        prior filings")."""
        _require_aware(at, "at")
        if self.status is not RepresentationStatus.ACTIVE:
            raise RepresentationInvalidError(
                f"only an active mandate can be revoked; this one is {self.status.value}"
            )
        return replace(
            self,
            status=RepresentationStatus.REVOKED,
            revoked_at=at,
            revocation_reason_code=reason_code,
        )

    def assert_permits(self, authority: RepresentationAuthority, *, at: datetime) -> None:
        """Raise unless this mandate authorizes `authority` at `at`.

        Three distinct refusals, three distinct codes, because a caller
        needs to know whether to renew, re-obtain, or widen the
        mandate."""
        _require_aware(at, "at")
        if self.status is RepresentationStatus.REVOKED:
            raise RepresentationRevokedError(f"mandate {self.mandate_id} was revoked")
        if self.status is RepresentationStatus.WITHDRAWN:
            raise RepresentationRevokedError(f"mandate {self.mandate_id} was withdrawn")
        if self.status is RepresentationStatus.EXPIRED or (
            self.valid_until is not None and at >= self.valid_until
        ):
            raise RepresentationExpiredError(f"mandate {self.mandate_id} has expired")
        if at < self.valid_from:
            raise RepresentationInvalidError(f"mandate {self.mandate_id} is not yet in force")
        if authority not in self.authorities:
            raise RepresentationInvalidError(
                f"mandate {self.mandate_id} does not grant {authority.value}"
            )


# ===========================================================================
# 3. Filings and the immutable docket (Framework 13.1, AGR-09)
# ===========================================================================


class FilingType(StrEnum):
    INITIATING_SUBMISSION = "initiating_submission"
    RESPONSE = "response"
    EVIDENCE_SUBMISSION = "evidence_submission"
    PROCEDURAL_REQUEST = "procedural_request"
    OBJECTION = "objection"
    WITHDRAWAL = "withdrawal"
    CORRECTION = "correction"


class FilingIntakeState(StrEnum):
    RECEIVED = "received"
    ADMITTED = "admitted"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


@dataclass(frozen=True, slots=True)
class Filing:
    """One entry on a case's append-only docket.

    `submitted_at` and `received_at` are separate because they routinely
    differ and the difference is procedurally material - a submission made
    before a deadline but received after it is a real situation, and a
    model with one timestamp cannot express it.

    Documents and evidence are *references only* (`document_references`,
    `evidence_references`): PACK-09 holds no bytes (Framework 13.2), and
    PACK-11 will own the objects these point at.

    A filing is never edited and never deleted. A correction is a NEW
    filing whose `supersedes_filing_id` names the one it replaces; the
    superseded entry stays on the docket with its own sequence number."""

    filing_id: UUID
    case_id: UUID
    organization_id: UUID
    docket_sequence: int
    filing_type: FilingType
    filed_by_party_reference: UUID
    submitted_at: datetime
    received_at: datetime
    intake_state: FilingIntakeState
    filed_by_representative_reference: UUID | None = None
    document_references: tuple[DocumentRef, ...] = ()
    evidence_references: tuple[EvidenceRef, ...] = ()
    supersedes_filing_id: UUID | None = None
    superseded_by_filing_id: UUID | None = None
    rejection_reason_code: str | None = None

    def __post_init__(self) -> None:
        _require_aware(self.submitted_at, "submitted_at")
        _require_aware(self.received_at, "received_at")
        if self.received_at < self.submitted_at:
            raise ValueError("received_at must not precede submitted_at")
        if self.docket_sequence < 1:
            raise FilingSequenceConflictError("docket_sequence must be a positive integer")
        if self.intake_state is FilingIntakeState.REJECTED and not self.rejection_reason_code:
            raise ValueError("a rejected filing must carry a rejection reason code")
        if self.supersedes_filing_id == self.filing_id:
            raise FilingSequenceConflictError("a filing cannot supersede itself")

    def admit(self) -> Filing:
        if self.intake_state is not FilingIntakeState.RECEIVED:
            raise FilingSequenceConflictError(
                f"only a received filing can be admitted; this one is {self.intake_state.value}"
            )
        return replace(self, intake_state=FilingIntakeState.ADMITTED)

    def reject(self, *, reason_code: str) -> Filing:
        """Reject at intake.

        The filing stays on the docket in `rejected` state carrying the
        reason - it is not removed, because "this was filed and refused"
        is itself a fact the record has to preserve."""
        if self.intake_state is not FilingIntakeState.RECEIVED:
            raise FilingSequenceConflictError(
                f"only a received filing can be rejected; this one is {self.intake_state.value}"
            )
        return replace(
            self, intake_state=FilingIntakeState.REJECTED, rejection_reason_code=reason_code
        )

    def mark_superseded(self, successor_filing_id: UUID) -> Filing:
        if successor_filing_id == self.filing_id:
            raise FilingSequenceConflictError("a filing cannot supersede itself")
        return replace(
            self,
            intake_state=FilingIntakeState.SUPERSEDED,
            superseded_by_filing_id=successor_filing_id,
        )


# ===========================================================================
# 4. Hearings and procedural events (Framework 13.1)
# ===========================================================================


class HearingStatus(StrEnum):
    SCHEDULED = "scheduled"
    RESCHEDULED = "rescheduled"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


_ALLOWED_HEARING_TRANSITIONS: frozenset[tuple[HearingStatus, HearingStatus]] = frozenset(
    {
        (HearingStatus.SCHEDULED, HearingStatus.RESCHEDULED),
        (HearingStatus.SCHEDULED, HearingStatus.CANCELLED),
        (HearingStatus.SCHEDULED, HearingStatus.COMPLETED),
        (HearingStatus.RESCHEDULED, HearingStatus.RESCHEDULED),
        (HearingStatus.RESCHEDULED, HearingStatus.CANCELLED),
        (HearingStatus.RESCHEDULED, HearingStatus.COMPLETED),
    }
)


class AttendanceState(StrEnum):
    """Whether a party was present.

    This is a *procedural* attendance record for one hearing. It is not
    assembly attendance, it confers no mandate, and it has nothing to do
    with quorum or voting eligibility - Framework hard invariants 37 and
    38 keep those separate, and PACK-21 owns them."""

    PRESENT = "present"
    ABSENT = "absent"
    EXCUSED = "excused"
    REPRESENTED = "represented"


@dataclass(frozen=True, slots=True)
class HearingAttendance:
    party_reference: UUID
    state: AttendanceState
    recorded_at: datetime

    def __post_init__(self) -> None:
        _require_aware(self.recorded_at, "recorded_at")


@dataclass(frozen=True, slots=True)
class HearingHistoryEntry:
    sequence: int
    status_after: HearingStatus
    occurred_at: datetime
    scheduled_at_before: datetime | None
    scheduled_at_after: datetime | None
    reason_code: str
    actor_authority_reference: UUID

    def __post_init__(self) -> None:
        _require_aware(self.occurred_at, "occurred_at")
        _require_text(self.reason_code, "reason_code")
        if self.sequence < 1:
            raise ValueError("sequence must be a positive integer")
        for name, value in (
            ("scheduled_at_before", self.scheduled_at_before),
            ("scheduled_at_after", self.scheduled_at_after),
        ):
            if value is not None:
                _require_aware(value, name)


@dataclass(frozen=True, slots=True)
class Hearing:
    """A scheduled procedural event in a case.

    Deliberately minimal. This is NOT the assemblies domain and NOT a
    video-meeting implementation: there is no quorum, no motion, no
    amendment, no assembly voting and no channel here, by explicit scope
    instruction. What it does carry is what a legal case needs -
    who convened it, when, who attended, what the agenda was, which
    submissions deadline it relates to, and where the minutes and
    evidence live.

    Like every other timeline in this pack, `history` is append-only:
    rescheduling records both the old and the new time."""

    hearing_id: UUID
    case_id: UUID
    organization_id: UUID
    convening_authority_reference: UUID
    agenda_code: str
    scheduled_at: datetime
    timezone: str
    history: tuple[HearingHistoryEntry, ...]
    attendance: tuple[HearingAttendance, ...] = ()
    submissions_deadline_id: UUID | None = None
    minutes_reference: MinutesRef | None = None
    evidence_references: tuple[EvidenceRef, ...] = ()

    def __post_init__(self) -> None:
        _require_aware(self.scheduled_at, "scheduled_at")
        _require_text(self.agenda_code, "agenda_code")
        _require_text(self.timezone, "timezone")
        if not self.history:
            raise HearingTransitionInvalidError(
                "a hearing must be created with at least its 'scheduled' history entry"
            )
        if self.history[0].status_after is not HearingStatus.SCHEDULED:
            raise HearingTransitionInvalidError(
                "the first hearing history entry must be 'scheduled'"
            )
        if [entry.sequence for entry in self.history] != list(range(1, len(self.history) + 1)):
            raise HearingTransitionInvalidError(
                "hearing history sequences must be contiguous and start at 1"
            )

    @property
    def status(self) -> HearingStatus:
        return self.history[-1].status_after

    def _append(
        self,
        *,
        status_after: HearingStatus,
        occurred_at: datetime,
        scheduled_at_after: datetime | None,
        reason_code: str,
        actor_authority_reference: UUID,
    ) -> Hearing:
        _require_aware(occurred_at, "occurred_at")
        if (self.status, status_after) not in _ALLOWED_HEARING_TRANSITIONS:
            raise HearingTransitionInvalidError(
                f"invalid hearing transition {self.status.value} -> {status_after.value}"
            )
        entry = HearingHistoryEntry(
            sequence=len(self.history) + 1,
            status_after=status_after,
            occurred_at=occurred_at,
            scheduled_at_before=self.scheduled_at,
            scheduled_at_after=scheduled_at_after,
            reason_code=reason_code,
            actor_authority_reference=actor_authority_reference,
        )
        return replace(
            self,
            scheduled_at=scheduled_at_after
            if scheduled_at_after is not None
            else self.scheduled_at,
            history=(*self.history, entry),
        )

    def reschedule(
        self,
        at: datetime,
        *,
        new_scheduled_at: datetime,
        reason_code: str,
        actor_authority_reference: UUID,
    ) -> Hearing:
        _require_aware(new_scheduled_at, "new_scheduled_at")
        return self._append(
            status_after=HearingStatus.RESCHEDULED,
            occurred_at=at,
            scheduled_at_after=new_scheduled_at,
            reason_code=reason_code,
            actor_authority_reference=actor_authority_reference,
        )

    def cancel(self, at: datetime, *, reason_code: str, actor_authority_reference: UUID) -> Hearing:
        return self._append(
            status_after=HearingStatus.CANCELLED,
            occurred_at=at,
            scheduled_at_after=None,
            reason_code=reason_code,
            actor_authority_reference=actor_authority_reference,
        )

    def complete(
        self,
        at: datetime,
        *,
        reason_code: str,
        actor_authority_reference: UUID,
        minutes_reference: MinutesRef | None = None,
    ) -> Hearing:
        completed = self._append(
            status_after=HearingStatus.COMPLETED,
            occurred_at=at,
            scheduled_at_after=None,
            reason_code=reason_code,
            actor_authority_reference=actor_authority_reference,
        )
        if minutes_reference is None:
            return completed
        return replace(completed, minutes_reference=minutes_reference)

    def with_attendance(self, record: HearingAttendance) -> Hearing:
        return replace(self, attendance=(*self.attendance, record))


# ===========================================================================
# 5. Interim measures (Framework 13.1, hard invariants 5, 7 and 69)
# ===========================================================================


class ActorClass(StrEnum):
    """What kind of actor is asking.

    Present so `AUTOMATED` can be refused explicitly rather than by
    omission. Framework hard invariant 69: AI does not decide candidacy
    admission, guilt, sanction, notice effect, conflict finding, finance
    certification, evidence admission, office assignment or publication
    approval. An interim measure is a sanction-shaped act, so an
    automated actor is refused at the gate with its own reason code."""

    HUMAN_AUTHORITY = "human_authority"
    HUMAN_CASE_HANDLER = "human_case_handler"
    SERVICE = "service"
    AUTOMATED = "automated"


class InterimMeasureStatus(StrEnum):
    REQUESTED = "requested"
    GRANTED = "granted"
    REFUSED = "refused"
    LAPSED = "lapsed"
    REVOKED = "revoked"


@dataclass(frozen=True, slots=True)
class InterimMeasure:
    """A time-bounded provisional order made before a case is decided.

    Four things are mandatory and structural:

    1. a `legal_basis_reference` - a measure with no recorded basis is
       not constructible;
    2. an authorized *human* decision-maker (`ActorClass.HUMAN_AUTHORITY`)
       - an automated actor and an ordinary case handler are both refused;
    3. an explicit end: either `ends_at` or `review_due_at` must be set,
       so a measure cannot run indefinitely unreviewed;
    4. a `remedy_reference` route once granted, because a provisional
       restriction the affected party cannot contest is exactly what
       Framework hard invariant 52 forbids."""

    measure_id: UUID
    case_id: UUID
    organization_id: UUID
    measure_kind: str
    requested_by_party_reference: UUID
    decided_by_authority_reference: UUID
    decided_by_actor_class: ActorClass
    legal_basis_reference: str
    scope_description_code: str
    status: InterimMeasureStatus
    decided_at: datetime
    starts_at: datetime
    ends_at: datetime | None = None
    review_due_at: datetime | None = None
    reasons_reference: str = ""
    evidence_references: tuple[EvidenceRef, ...] = ()
    remedy_id: UUID | None = None
    lapsed_at: datetime | None = None
    revoked_at: datetime | None = None

    def __post_init__(self) -> None:
        _require_aware(self.decided_at, "decided_at")
        _require_aware(self.starts_at, "starts_at")
        _require_text(self.measure_kind, "measure_kind")
        _require_text(self.legal_basis_reference, "legal_basis_reference")
        _require_text(self.scope_description_code, "scope_description_code")
        for name, value in (
            ("ends_at", self.ends_at),
            ("review_due_at", self.review_due_at),
            ("lapsed_at", self.lapsed_at),
            ("revoked_at", self.revoked_at),
        ):
            if value is not None:
                _require_aware(value, name)
        if self.status is InterimMeasureStatus.GRANTED:
            if self.decided_by_actor_class is not ActorClass.HUMAN_AUTHORITY:
                raise InterimMeasureAuthorityDeniedError(
                    "an interim measure may only be granted by an authorized human authority; "
                    f"got {self.decided_by_actor_class.value}"
                )
            if self.ends_at is None and self.review_due_at is None:
                # Reason-coded rather than a bare ValueError: an indefinite
                # measure is a governance refusal a party can be told about
                # and can appeal, not a programming mistake (canon section
                # 24; PACK-09 required invariant 14).
                raise InterimMeasureAuthorityDeniedError(
                    "a granted interim measure must carry an end date or a review date - "
                    "it may not run indefinitely without review"
                )
            if not self.reasons_reference:
                raise DueProcessPrerequisiteMissingError(
                    "a granted interim measure must record its reasons"
                )

    def is_in_force_at(self, at: datetime) -> bool:
        _require_aware(at, "at")
        if self.status is not InterimMeasureStatus.GRANTED:
            return False
        if at < self.starts_at:
            return False
        return self.ends_at is None or at < self.ends_at

    def lapse(self, at: datetime) -> InterimMeasure:
        """End the measure at its recorded expiry.

        Never silent: lapsing is an explicit, timestamped transition that
        produces its own event, because a restriction quietly evaporating
        is as much a governance failure as one quietly persisting."""
        _require_aware(at, "at")
        if self.status is not InterimMeasureStatus.GRANTED:
            raise ProceduralCaseTransitionInvalidError(
                f"only a granted measure can lapse; this one is {self.status.value}"
            )
        if self.ends_at is None or at < self.ends_at:
            raise ProceduralCaseTransitionInvalidError(
                "a measure cannot lapse before its recorded end"
            )
        return replace(self, status=InterimMeasureStatus.LAPSED, lapsed_at=at)

    def revoke(self, at: datetime) -> InterimMeasure:
        _require_aware(at, "at")
        if self.status is not InterimMeasureStatus.GRANTED:
            raise ProceduralCaseTransitionInvalidError(
                f"only a granted measure can be revoked; this one is {self.status.value}"
            )
        return replace(self, status=InterimMeasureStatus.REVOKED, revoked_at=at)


# ===========================================================================
# 6. Procedural decisions: issuance / effect / finality / enforceability
# ===========================================================================


class DecisionType(StrEnum):
    ADMISSIBILITY = "admissibility"
    INTERIM = "interim"
    SUBSTANTIVE = "substantive"
    SANCTION = "sanction"
    DISMISSAL = "dismissal"
    PROCEDURAL_ORDER = "procedural_order"
    APPEAL_OUTCOME = "appeal_outcome"


class OperativeResult(StrEnum):
    UPHELD = "upheld"
    PARTIALLY_UPHELD = "partially_upheld"
    DISMISSED = "dismissed"
    INADMISSIBLE = "inadmissible"
    SETTLED = "settled"
    WITHDRAWN = "withdrawn"
    REFERRED = "referred"


class EffectStatus(StrEnum):
    """Whether the decision's operative content is currently operating.

    Separate from finality and from enforceability - Framework 13.1
    requires all three, and collapsing any two is the defect this
    tripartite model exists to prevent."""

    PENDING = "pending"
    IN_EFFECT = "in_effect"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"


class FinalityStatus(StrEnum):
    """Whether a remedy route is still open."""

    OPEN_TO_REMEDY = "open_to_remedy"
    FINAL = "final"
    SUPERSEDED_ON_APPEAL = "superseded_on_appeal"


class EnforceabilityStatus(StrEnum):
    """Whether the decision may actually be acted upon."""

    NOT_ENFORCEABLE = "not_enforceable"
    ENFORCEABLE = "enforceable"
    STAYED = "stayed"


@dataclass(frozen=True, slots=True)
class DecisionStateEntry:
    """One append-only entry in a decision's own state history.

    Records all three dimensions at every change, so "was this
    enforceable on 3 March" is answerable without replaying anything."""

    sequence: int
    occurred_at: datetime
    effect_status: EffectStatus
    finality_status: FinalityStatus
    enforceability_status: EnforceabilityStatus
    reason_code: str
    actor_authority_reference: UUID

    def __post_init__(self) -> None:
        _require_aware(self.occurred_at, "occurred_at")
        _require_text(self.reason_code, "reason_code")
        if self.sequence < 1:
            raise ValueError("sequence must be a positive integer")


@dataclass(frozen=True, slots=True)
class ProceduralDecision:
    """A decision in a governed case.

    Issuance, effect, finality and enforceability are four separate
    facts, each with its own status and its own transition path, all
    recorded together in an append-only `state_history`. A decision can
    be issued but not yet in effect; in effect but not final; final but
    stayed. Modelling them as one status would make each of those
    situations inexpressible.

    `reasons_reference` is mandatory for sanction-type decisions
    (Framework hard invariant 52). Evidence is referenced, never
    embedded."""

    decision_id: UUID
    case_id: UUID
    organization_id: UUID
    decision_type: DecisionType
    deciding_authority_reference: UUID
    decided_by_party_reference: UUID
    operative_result: OperativeResult
    issued_at: datetime
    state_history: tuple[DecisionStateEntry, ...]
    reason_code: str
    effective_at: datetime | None = None
    reasons_reference: str = ""
    evidence_references: tuple[EvidenceRef, ...] = ()
    remedy_id: UUID | None = None
    appeal_case_id: UUID | None = None
    reopening_case_id: UUID | None = None
    enforcement_action_reference: str | None = None
    supersedes_decision_id: UUID | None = None
    decision_version: int = 1

    def __post_init__(self) -> None:
        _require_aware(self.issued_at, "issued_at")
        _require_text(self.reason_code, "reason_code")
        if self.effective_at is not None:
            _require_aware(self.effective_at, "effective_at")
        if self.decision_version < 1:
            raise ValueError("decision_version must be a positive integer")
        if not self.state_history:
            raise ProceduralCaseTransitionInvalidError(
                "a decision must be created with at least its issuance state entry"
            )
        if [entry.sequence for entry in self.state_history] != list(
            range(1, len(self.state_history) + 1)
        ):
            raise ProceduralCaseTransitionInvalidError(
                "decision state history sequences must be contiguous and start at 1"
            )
        if self.decision_type is DecisionType.SANCTION and not self.reasons_reference:
            raise DueProcessPrerequisiteMissingError(
                "a sanction decision must record its reasons (Framework hard invariant 52)"
            )

    @property
    def effect_status(self) -> EffectStatus:
        return self.state_history[-1].effect_status

    @property
    def finality_status(self) -> FinalityStatus:
        return self.state_history[-1].finality_status

    @property
    def enforceability_status(self) -> EnforceabilityStatus:
        return self.state_history[-1].enforceability_status

    def _append_state(
        self,
        *,
        occurred_at: datetime,
        effect_status: EffectStatus,
        finality_status: FinalityStatus,
        enforceability_status: EnforceabilityStatus,
        reason_code: str,
        actor_authority_reference: UUID,
    ) -> ProceduralDecision:
        _require_aware(occurred_at, "occurred_at")
        entry = DecisionStateEntry(
            sequence=len(self.state_history) + 1,
            occurred_at=occurred_at,
            effect_status=effect_status,
            finality_status=finality_status,
            enforceability_status=enforceability_status,
            reason_code=reason_code,
            actor_authority_reference=actor_authority_reference,
        )
        return replace(
            self,
            state_history=(*self.state_history, entry),
            decision_version=self.decision_version + 1,
        )

    def commence_effect(
        self, at: datetime, *, reason_code: str, actor_authority_reference: UUID
    ) -> ProceduralDecision:
        if self.effect_status is not EffectStatus.PENDING:
            raise DecisionNotEffectiveError(
                f"effect can only commence from pending; this decision is "
                f"{self.effect_status.value}"
            )
        commenced = self._append_state(
            occurred_at=at,
            effect_status=EffectStatus.IN_EFFECT,
            finality_status=self.finality_status,
            enforceability_status=self.enforceability_status,
            reason_code=reason_code,
            actor_authority_reference=actor_authority_reference,
        )
        return replace(commenced, effective_at=at)

    def suspend_effect(
        self, at: datetime, *, reason_code: str, actor_authority_reference: UUID
    ) -> ProceduralDecision:
        """Suspend the decision's effect - typically because a remedy was
        filed. Enforceability is stayed at the same time: a suspended
        decision that stayed enforceable would be a contradiction the
        model must not permit."""
        if self.effect_status is not EffectStatus.IN_EFFECT:
            raise DecisionNotEffectiveError(
                f"only a decision in effect can be suspended; this one is "
                f"{self.effect_status.value}"
            )
        return self._append_state(
            occurred_at=at,
            effect_status=EffectStatus.SUSPENDED,
            finality_status=self.finality_status,
            enforceability_status=EnforceabilityStatus.STAYED,
            reason_code=reason_code,
            actor_authority_reference=actor_authority_reference,
        )

    def resume_effect(
        self, at: datetime, *, reason_code: str, actor_authority_reference: UUID
    ) -> ProceduralDecision:
        if self.effect_status is not EffectStatus.SUSPENDED:
            raise DecisionNotEffectiveError(
                f"only a suspended decision can resume; this one is {self.effect_status.value}"
            )
        return self._append_state(
            occurred_at=at,
            effect_status=EffectStatus.IN_EFFECT,
            finality_status=self.finality_status,
            enforceability_status=self.enforceability_status,
            reason_code=reason_code,
            actor_authority_reference=actor_authority_reference,
        )

    def become_final(
        self, at: datetime, *, reason_code: str, actor_authority_reference: UUID
    ) -> ProceduralDecision:
        if self.finality_status is not FinalityStatus.OPEN_TO_REMEDY:
            raise DecisionNotFinalError(
                f"finality can only be reached from open_to_remedy; this decision is "
                f"{self.finality_status.value}"
            )
        return self._append_state(
            occurred_at=at,
            effect_status=self.effect_status,
            finality_status=FinalityStatus.FINAL,
            enforceability_status=self.enforceability_status,
            reason_code=reason_code,
            actor_authority_reference=actor_authority_reference,
        )

    def become_enforceable(
        self, at: datetime, *, reason_code: str, actor_authority_reference: UUID
    ) -> ProceduralDecision:
        """Make the decision enforceable.

        Refuses unless it is actually in effect. Enforceability is a
        *third* fact, not a synonym for either of the other two: a final
        decision whose effect is suspended is not enforceable, and this
        guard is what makes that inexpressible-by-accident."""
        if self.effect_status is not EffectStatus.IN_EFFECT:
            raise DecisionNotEnforceableError(
                "a decision cannot become enforceable while its effect is "
                f"{self.effect_status.value}"
            )
        if self.enforceability_status is EnforceabilityStatus.ENFORCEABLE:
            raise DecisionNotEnforceableError("this decision is already enforceable")
        return self._append_state(
            occurred_at=at,
            effect_status=self.effect_status,
            finality_status=self.finality_status,
            enforceability_status=EnforceabilityStatus.ENFORCEABLE,
            reason_code=reason_code,
            actor_authority_reference=actor_authority_reference,
        )

    def with_remedy(self, remedy_id: UUID) -> ProceduralDecision:
        return replace(self, remedy_id=remedy_id)

    def with_appeal(self, appeal_case_id: UUID) -> ProceduralDecision:
        """Link an appeal.

        The original decision's operative content, reasons and history are
        untouched - the appeal is a separate case and a separate decision
        (Framework hard invariant 26: historical documents are not
        rewritten retroactively)."""
        if appeal_case_id == self.case_id:
            raise ValueError("an appeal must reference a different case")
        return replace(self, appeal_case_id=appeal_case_id)


class RemedyKind(StrEnum):
    APPEAL = "appeal"
    REVIEW = "review"
    OBJECTION = "objection"
    RECONSIDERATION = "reconsideration"


class RemedyStatus(StrEnum):
    AVAILABLE = "available"
    EXERCISED = "exercised"
    EXPIRED = "expired"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True, slots=True)
class Remedy:
    """The remedy route attached to a decision.

    Recorded as its own object rather than a flag on the decision,
    because "what could be done about this, by when, and to whom" is
    exactly the information an affected party needs and a later pack
    (PACK-19's candidacy appeals, PACK-23's ombuds review) has to
    consume."""

    remedy_id: UUID
    case_id: UUID
    organization_id: UUID
    decision_id: UUID
    remedy_kind: RemedyKind
    status: RemedyStatus
    available_from: datetime
    available_until: datetime | None
    competent_authority_reference: UUID
    deadline_id: UUID | None = None
    exercised_at: datetime | None = None
    resulting_case_id: UUID | None = None

    def __post_init__(self) -> None:
        _require_aware(self.available_from, "available_from")
        if self.available_until is not None:
            _require_aware(self.available_until, "available_until")
        if self.exercised_at is not None:
            _require_aware(self.exercised_at, "exercised_at")

    def assert_available_at(self, at: datetime) -> None:
        _require_aware(at, "at")
        if self.status is not RemedyStatus.AVAILABLE:
            raise RemedyUnavailableError(f"remedy {self.remedy_id} is {self.status.value}")
        if at < self.available_from:
            raise RemedyUnavailableError(f"remedy {self.remedy_id} is not yet available")
        if self.available_until is not None and at >= self.available_until:
            raise RemedyUnavailableError(f"remedy {self.remedy_id} has expired")

    def exercise(self, at: datetime, *, resulting_case_id: UUID) -> Remedy:
        self.assert_available_at(at)
        return replace(
            self,
            status=RemedyStatus.EXERCISED,
            exercised_at=at,
            resulting_case_id=resulting_case_id,
        )


# ===========================================================================
# 7. Recusal hooks (Framework 13.1, hard invariants 53 and 54)
# ===========================================================================


class ConflictAssessmentOutcome(StrEnum):
    NO_CONFLICT = "no_conflict"
    CONFLICT_MITIGATED = "conflict_mitigated"
    RECUSAL_REQUIRED = "recusal_required"


@dataclass(frozen=True, slots=True)
class RecusalRecord:
    """A recorded recusal.

    Framework hard invariant 53: recusal immediately blocks decision
    capability *without erasing history*. Both halves are structural
    here - `effective_at` is what
    `assert_actor_not_recused` checks, and `prior_participation_codes`
    keeps what the actor did before the recusal permanently visible.

    Framework hard invariant 54: conflict declarations are versioned;
    superseding is allowed, overwriting is not. A later declaration
    points at the one it supersedes via `supersedes_recusal_id`; neither
    record is mutated."""

    recusal_id: UUID
    case_id: UUID
    organization_id: UUID
    party_reference: UUID
    conflict_declaration_id: UUID
    assessment_outcome: ConflictAssessmentOutcome
    effective_at: datetime
    reviewed_by_party_reference: UUID
    prior_participation_codes: tuple[str, ...] = ()
    replacement_assignment_id: UUID | None = None
    supersedes_recusal_id: UUID | None = None

    def __post_init__(self) -> None:
        _require_aware(self.effective_at, "effective_at")
        if self.reviewed_by_party_reference == self.party_reference:
            raise ProceduralRoleConflictError(
                "a conflict assessment may not be reviewed by the party it concerns"
            )
        if self.supersedes_recusal_id == self.recusal_id:
            raise ValueError("a recusal record cannot supersede itself")

    @property
    def blocks_decision_capability(self) -> bool:
        return self.assessment_outcome is ConflictAssessmentOutcome.RECUSAL_REQUIRED


@dataclass(frozen=True, slots=True)
class ReplacementAssignment:
    """The separate, governed assignment of a replacement after a
    recusal.

    A replacement is never automatic: Framework 13.1 requires it to be
    its own assignment, so the recusal record only *points* at one and
    the workflow refuses to proceed until it exists."""

    assignment_id: UUID
    case_id: UUID
    organization_id: UUID
    recusal_id: UUID
    replacement_party_reference: UUID
    assigned_by_authority_reference: UUID
    assigned_at: datetime

    def __post_init__(self) -> None:
        _require_aware(self.assigned_at, "assigned_at")


def assert_actor_not_recused(
    *, actor_party_reference: UUID, recusals: tuple[RecusalRecord, ...], at: datetime
) -> None:
    """Raise `RecusedActorDeniedError` if `actor_party_reference` is
    recused from this matter at `at`.

    Called by every command that lets somebody decide, order or rule on
    anything. Uses `effective_at` rather than "is there any recusal
    record", so a recusal recorded for a future effective date does not
    retroactively invalidate what the actor did before it."""
    _require_aware(at, "at")
    for recusal in recusals:
        if (
            recusal.party_reference == actor_party_reference
            and recusal.blocks_decision_capability
            and at >= recusal.effective_at
        ):
            raise RecusedActorDeniedError(
                f"party {actor_party_reference} is recused from case {recusal.case_id} "
                f"with effect from {recusal.effective_at.isoformat()}"
            )


# ===========================================================================
# 8. The LegalCase itself
# ===========================================================================


class ConfidentialityClass(StrEnum):
    """Framework section 11's data classification, applied to a case.

    `HIGHLY_CONFIDENTIAL` is the class PACK-24 (protected reporting) will
    require: Framework section 11 excludes it from general search
    entirely and restricts it to a dedicated index or a named case team.
    PACK-09 records the classification and the access profile; it does
    not implement the search or admin surfaces that must honour them -
    those are PACK-12's."""

    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    HIGHLY_CONFIDENTIAL = "highly_confidential"


class CaseAccessProfile(StrEnum):
    """The "case wall" - who may see the case at all.

    Framework AGR-09/AGR-11 both name case walls as mandatory. This is
    the declared profile; enforcement of search and admin surfaces is
    PACK-12's, and PACK-09 exports the value so PACK-12 has something
    authoritative to enforce against."""

    SCOPE_WIDE = "scope_wide"
    CASE_TEAM_ONLY = "case_team_only"
    NAMED_PARTIES_ONLY = "named_parties_only"
    RESTRICTED_REPORTING = "restricted_reporting"


class LegalCaseStatus(StrEnum):
    INTAKE = "intake"
    JURISDICTION_REVIEW = "jurisdiction_review"
    ADMISSIBILITY_REVIEW = "admissibility_review"
    SUBSTANTIVE_REVIEW = "substantive_review"
    HEARING = "hearing"
    DECIDED = "decided"
    CLOSED = "closed"
    REOPENED = "reopened"


_ALLOWED_LEGAL_CASE_TRANSITIONS: frozenset[tuple[LegalCaseStatus, LegalCaseStatus]] = frozenset(
    {
        (LegalCaseStatus.INTAKE, LegalCaseStatus.JURISDICTION_REVIEW),
        (LegalCaseStatus.JURISDICTION_REVIEW, LegalCaseStatus.ADMISSIBILITY_REVIEW),
        (LegalCaseStatus.JURISDICTION_REVIEW, LegalCaseStatus.CLOSED),
        (LegalCaseStatus.ADMISSIBILITY_REVIEW, LegalCaseStatus.SUBSTANTIVE_REVIEW),
        (LegalCaseStatus.ADMISSIBILITY_REVIEW, LegalCaseStatus.CLOSED),
        (LegalCaseStatus.SUBSTANTIVE_REVIEW, LegalCaseStatus.HEARING),
        (LegalCaseStatus.HEARING, LegalCaseStatus.SUBSTANTIVE_REVIEW),
        (LegalCaseStatus.SUBSTANTIVE_REVIEW, LegalCaseStatus.DECIDED),
        (LegalCaseStatus.HEARING, LegalCaseStatus.DECIDED),
        (LegalCaseStatus.DECIDED, LegalCaseStatus.CLOSED),
        (LegalCaseStatus.CLOSED, LegalCaseStatus.REOPENED),
        (LegalCaseStatus.REOPENED, LegalCaseStatus.SUBSTANTIVE_REVIEW),
    }
)

#: Statuses at or past which the matter is being decided on its merits.
#: Reaching any of them requires confirmed jurisdiction.
#:
#: Public because the application layer gates on exactly this set before
#: it lets a case transition; two copies of the list would be two places
#: to forget a status (Framework hard invariant 52).
SUBSTANTIVE_CASE_STATUSES: frozenset[LegalCaseStatus] = frozenset(
    {
        LegalCaseStatus.SUBSTANTIVE_REVIEW,
        LegalCaseStatus.HEARING,
        LegalCaseStatus.DECIDED,
    }
)

_SUBSTANTIVE_CASE_STATUSES = SUBSTANTIVE_CASE_STATUSES


@dataclass(frozen=True, slots=True)
class CaseTransitionEntry:
    """One append-only entry in a case's own lifecycle history."""

    sequence: int
    status_after: LegalCaseStatus
    occurred_at: datetime
    reason_code: str
    actor_authority_reference: UUID

    def __post_init__(self) -> None:
        _require_aware(self.occurred_at, "occurred_at")
        _require_text(self.reason_code, "reason_code")
        if self.sequence < 1:
            raise ValueError("sequence must be a positive integer")


@dataclass(frozen=True, slots=True)
class LegalCase:
    """One governed legal matter - PACK-09's central reusable primitive.

    `legal_case_id` is a random UUID. It is not derived from any person,
    not sequential within an organization, and carries no meaning: a
    caller holding one learns nothing about who is involved and cannot
    enumerate an organization's caseload from it (Framework 13.1: "Case
    ID не должен позволять cross-scope enumeration"). Cross-scope reads
    are refused with the same not-found error as a nonexistent case, so
    a foreign id is not even an existence oracle.

    `status` is derived from an append-only `transition_history`, the
    same structural choice `ProceduralDeadline` makes: there is no status
    field to overwrite, so the lifecycle cannot be rewritten.

    Reopening is a *linked transition*, not an edit: `reopened_at` and
    `reopened_from_case_id` record it, the closure that preceded it stays
    in the history, and any deadline the reopening needs is a new,
    explicitly-linked deadline rather than a reset of the old one."""

    legal_case_id: UUID
    organization_id: UUID
    case_kind: CaseKind
    opened_at: datetime
    subject_reference: str
    confidentiality_class: ConfidentialityClass
    access_profile: CaseAccessProfile
    transition_history: tuple[CaseTransitionEntry, ...]
    governing_policy_reference: str
    jurisdiction_id: UUID | None = None
    parent_case_id: UUID | None = None
    prior_case_id: UUID | None = None
    closed_at: datetime | None = None
    closure_reason_code: str | None = None
    reopened_at: datetime | None = None
    reopened_from_case_id: UUID | None = None
    case_version: int = 1

    def __post_init__(self) -> None:
        _require_aware(self.opened_at, "opened_at")
        _require_text(self.subject_reference, "subject_reference")
        _require_text(self.governing_policy_reference, "governing_policy_reference")
        if self.case_version < 1:
            raise ValueError("case_version must be a positive integer")
        for name, value in (
            ("closed_at", self.closed_at),
            ("reopened_at", self.reopened_at),
        ):
            if value is not None:
                _require_aware(value, name)
        if not self.transition_history:
            raise ProceduralCaseTransitionInvalidError(
                "a legal case must be created with at least its intake transition entry"
            )
        if self.transition_history[0].status_after is not LegalCaseStatus.INTAKE:
            raise ProceduralCaseTransitionInvalidError(
                "the first legal-case transition entry must be 'intake'"
            )
        if [entry.sequence for entry in self.transition_history] != list(
            range(1, len(self.transition_history) + 1)
        ):
            raise ProceduralCaseTransitionInvalidError(
                "legal-case transition sequences must be contiguous and start at 1"
            )
        if self.parent_case_id == self.legal_case_id or self.prior_case_id == self.legal_case_id:
            raise ValueError("a case cannot be its own parent or prior case")

    @property
    def status(self) -> LegalCaseStatus:
        return self.transition_history[-1].status_after

    @property
    def is_closed(self) -> bool:
        return self.status is LegalCaseStatus.CLOSED

    def transition(
        self,
        target: LegalCaseStatus,
        at: datetime,
        *,
        reason_code: str,
        actor_authority_reference: UUID,
        closure_reason_code: str | None = None,
    ) -> LegalCase:
        _require_aware(at, "at")
        if (self.status, target) not in _ALLOWED_LEGAL_CASE_TRANSITIONS:
            raise ProceduralCaseTransitionInvalidError(
                f"invalid legal-case transition {self.status.value} -> {target.value}"
            )
        if target is LegalCaseStatus.CLOSED and not closure_reason_code:
            raise ProceduralCaseTransitionInvalidError(
                "closing a case requires an explicit closure reason code"
            )
        if target in _SUBSTANTIVE_CASE_STATUSES and self.jurisdiction_id is None:
            raise JurisdictionMissingError(
                f"case {self.legal_case_id} has no confirmed jurisdiction; it cannot move to "
                f"{target.value}"
            )
        entry = CaseTransitionEntry(
            sequence=len(self.transition_history) + 1,
            status_after=target,
            occurred_at=at,
            reason_code=reason_code,
            actor_authority_reference=actor_authority_reference,
        )
        return replace(
            self,
            transition_history=(*self.transition_history, entry),
            closed_at=at if target is LegalCaseStatus.CLOSED else self.closed_at,
            closure_reason_code=(
                closure_reason_code
                if target is LegalCaseStatus.CLOSED
                else self.closure_reason_code
            ),
            reopened_at=at if target is LegalCaseStatus.REOPENED else self.reopened_at,
            case_version=self.case_version + 1,
        )

    def with_jurisdiction(self, determination: JurisdictionDetermination) -> LegalCase:
        if determination.case_id != self.legal_case_id:
            raise JurisdictionScopeMismatchError(
                "jurisdiction determination does not belong to this case"
            )
        if determination.organization_id != self.organization_id:
            raise JurisdictionScopeMismatchError(
                "jurisdiction determination belongs to a different organization"
            )
        return replace(
            self, jurisdiction_id=determination.jurisdiction_id, case_version=self.case_version + 1
        )


def assert_may_decide_substantively(
    *,
    case: LegalCase,
    jurisdiction: JurisdictionDetermination | None,
    acting_authority_reference: UUID,
    at: datetime,
) -> None:
    """The single gate between a case and a substantive decision.

    Framework hard invariant 52 in executable form. Refuses, in this
    order and each with its own code:

    1. no jurisdiction determination at all -> `JURISDICTION_MISSING`
       (fail closed; an unknown jurisdiction is never permissive);
    2. determination belongs to another case or organization ->
       `JURISDICTION_SCOPE_MISMATCH`;
    3. determination is transferred -> `JURISDICTION_TRANSFER_REQUIRED`
       (the successor decides, not this authority);
    4. determination is not confirmed and effective, or is challenged,
       declined or indeterminate -> `JURISDICTION_NOT_COMPETENT`;
    5. the acting authority is not the one the determination names ->
       `JURISDICTION_NOT_COMPETENT` again, because holding a plausible
       role is not competence (hard invariant 15)."""
    _require_aware(at, "at")
    if case.jurisdiction_id is None or jurisdiction is None:
        raise JurisdictionMissingError(
            f"case {case.legal_case_id} has no jurisdiction determination"
        )
    if (
        jurisdiction.case_id != case.legal_case_id
        or jurisdiction.organization_id != case.organization_id
    ):
        raise JurisdictionScopeMismatchError(
            "jurisdiction determination does not belong to this case or organization"
        )
    if jurisdiction.status is JurisdictionStatus.TRANSFERRED:
        raise JurisdictionTransferRequiredError(
            f"jurisdiction over case {case.legal_case_id} was transferred to "
            f"{jurisdiction.transferred_to_jurisdiction_id}"
        )
    if not jurisdiction.permits_substantive_decision_at(at):
        raise JurisdictionNotCompetentError(
            f"jurisdiction determination {jurisdiction.jurisdiction_id} is "
            f"{jurisdiction.status.value} and does not permit a substantive decision"
        )
    if jurisdiction.competent_authority_reference != acting_authority_reference:
        raise JurisdictionNotCompetentError(
            "the acting authority is not the competent authority recorded for this case; "
            "a role name is not proof of authority"
        )


def assert_due_process_complete(
    *,
    jurisdiction_confirmed: bool,
    notice_effect_established: bool,
    response_opportunity_given: bool,
    decided_by_actor_class: ActorClass,
    reasons_reference: str,
    remedy_available: bool,
) -> None:
    """Framework hard invariant 52, checked as a unit before a sanction
    or any restriction of a fundamental right.

    All six prerequisites are named explicitly rather than folded into a
    single boolean, so the refusal message says which one is missing and
    a reviewer can see at the call site that none was quietly dropped."""
    missing: list[str] = []
    if not jurisdiction_confirmed:
        missing.append("jurisdiction")
    if not notice_effect_established:
        missing.append("notice")
    if not response_opportunity_given:
        missing.append("opportunity to respond")
    if decided_by_actor_class not in {ActorClass.HUMAN_AUTHORITY, ActorClass.HUMAN_CASE_HANDLER}:
        missing.append("human decision")
    if not reasons_reference:
        missing.append("reasons")
    if not remedy_available:
        missing.append("remedy")
    if missing:
        raise DueProcessPrerequisiteMissingError(
            "a sanction requires jurisdiction, notice, opportunity to respond, a human "
            f"decision, reasons and a remedy; missing: {missing}"
        )
