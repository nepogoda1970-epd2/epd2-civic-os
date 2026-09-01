"""The identity-side versioned API: catalogue and reference adapter.

The generic half - the endpoint spec, the obligations, the request and
response values, the response-safety scan and the dispatcher - lives in
`epd2_core.api_contracts`, because four services need it and no service
may import another. What lives here is this side's **endpoint list** and
its handlers.

Every endpoint below is declared `TrustSide.IDENTITY`. That is not
labelling: `assert_no_endpoint_spans_the_boundary` refuses an operation
name declared on both sides, so the correlation ADR-093 forbids cannot be
reached by routing after it was made impossible in SQL. There is
deliberately **no endpoint here that returns a credential, a redemption
outcome or a ballot fact**, because this side holds no such value to
return.

Two endpoints are `unauthenticated_by_design`, and both say why in their
`justification`: the PACK-14 handoff is presented by a participant who
has an artifact and no session on this side, and the one-time pickup is
redeemed from inside the isolated voting origin, where an account context
would be exactly the linkage the origin exists to prevent (ADR-088,
ADR-090).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from epd2_core.api_contracts import (
    ApiDispatcher,
    ApiRequest,
    ApiRequestMalformedError,
    EndpointSpec,
    TrustSide,
    build_catalogue,
)
from epd2_eligibility_service.voting_assertion_issuer import MinimizedDecisionInput
from epd2_eligibility_service.voting_eligibility import (
    EligibilityCase,
    EligibilityDecisionStatus,
    ParticipationUnitLedgerEntry,
)
from epd2_eligibility_service.voting_handoff import (
    HandoffAcceptance,
    HandoffBinding,
    VotingHandoffArtifact,
    artifact_digest,
    verify_handoff,
)
from epd2_eligibility_service.voting_trust_exceptions import (
    AssertionPickupAlreadyUsedError,
    HandoffAlreadyUsedError,
    UnknownAssertionError,
    UnknownEligibilityCaseError,
)
from epd2_eligibility_service.voting_trust_runtime import VotingTrustRuntime


class AssertionAlreadyMintedForUnitError(RuntimeError):
    """A second assertion was requested for one participation unit.

    The code is `CREDENTIAL_ALREADY_ISSUED` and not `ALREADY_VOTED`: this
    side knows an assertion exists for a participation unit and knows
    nothing whatever about a ballot. Saying more would be a claim it
    cannot support.
    """

    reason_code = "CREDENTIAL_ALREADY_ISSUED"


API_AREA_ELIGIBILITY = "eligibility"
API_AREA_ASSERTION = "assertion"
API_AREA_HANDOFF = "handoff"
API_AREA_DISPUTE = "dispute"


def _endpoint(
    operation: str,
    area: str,
    *,
    consequential: bool,
    roles: tuple[str, ...],
    reason_codes: tuple[str, ...],
    unauthenticated_by_design: bool = False,
    justification: str = "",
) -> EndpointSpec:
    """Declare one identity-side endpoint.

    Consequential endpoints take all three obligations; read endpoints
    take none. Stating them positionally here rather than by default
    keeps `assert_consequential_contract` meaningful.
    """
    return EndpointSpec(
        operation=operation,
        area=area,
        trust_side=TrustSide.IDENTITY,
        consequential=consequential,
        idempotency_key_required=consequential,
        version_check_required=consequential,
        audit_evidence_required=consequential,
        authorized_roles=roles,
        reason_codes=reason_codes,
        unauthenticated_by_design=unauthenticated_by_design,
        justification=justification,
    )


ELIGIBILITY_ENDPOINTS: tuple[EndpointSpec, ...] = (
    _endpoint(
        "eligibility.case.open",
        API_AREA_ELIGIBILITY,
        consequential=True,
        roles=("eligibility_officer", "membership_authority"),
        reason_codes=(
            "ELIGIBILITY_REVIEW_REQUIRED",
            "ELIGIBILITY_ATTRIBUTE_NOT_DECLARED",
            "ELIGIBILITY_ATTRIBUTE_PROHIBITED",
            "VOTING_CONTEXT_NOT_ACTIVE",
            "API_REQUEST_MALFORMED",
        ),
    ),
    _endpoint(
        "eligibility.case.read",
        API_AREA_ELIGIBILITY,
        consequential=False,
        roles=("eligibility_officer", "eligibility_reviewer", "dispute_reviewer"),
        reason_codes=("ELIGIBILITY_CASE_NOT_FOUND", "PERMISSION_DENIED"),
    ),
    _endpoint(
        "eligibility.decision.record",
        API_AREA_ELIGIBILITY,
        consequential=True,
        roles=("eligibility_officer", "eligibility_reviewer"),
        reason_codes=(
            "ELIGIBILITY_APPROVED",
            "ELIGIBILITY_DENIED",
            "ELIGIBILITY_REVIEW_REQUIRED",
            "ELIGIBILITY_SELF_REVIEW_REFUSED",
            "ELIGIBILITY_SOURCE_STALE",
            "ELIGIBILITY_CASE_NOT_FOUND",
        ),
    ),
    _endpoint(
        "assertion.mint",
        API_AREA_ASSERTION,
        consequential=True,
        roles=("eligibility_officer",),
        reason_codes=(
            "ASSERTION_ISSUED",
            "ASSERTION_QUEUED",
            "ELIGIBILITY_DECISION_EXPIRED",
            "ELIGIBILITY_DECISION_SUPERSEDED",
            "CREDENTIAL_ALREADY_ISSUED",
            "SYSTEM_DEPENDENCY_UNAVAILABLE",
        ),
    ),
    _endpoint(
        "assertion.release.evaluate",
        API_AREA_ASSERTION,
        consequential=True,
        roles=("voting_operations_officer",),
        reason_codes=(
            "ASSERTION_RELEASE_PENDING",
            "COHORT_THRESHOLD_NOT_MET",
            "ASSERTION_QUEUED",
            "ASSERTION_NOT_FOUND",
        ),
    ),
    _endpoint(
        "handoff.accept",
        API_AREA_HANDOFF,
        consequential=True,
        roles=("voting_client_operator",),
        reason_codes=(
            "HANDOFF_ACCEPTED",
            "HANDOFF_INVALID",
            "HANDOFF_EXPIRED",
            "HANDOFF_ALREADY_USED",
            "HANDOFF_AUDIENCE_MISMATCH",
            "HANDOFF_ORIGIN_MISMATCH",
        ),
        unauthenticated_by_design=True,
        justification=(
            "The artifact is presented by a participant who holds it and has no session on "
            "this side. Requiring one would mean this boundary learning an account, which is "
            "what ADR-088 removed."
        ),
    ),
    _endpoint(
        "assertion.pickup.consume",
        API_AREA_ASSERTION,
        consequential=True,
        roles=("voting_client_operator",),
        reason_codes=(
            "ASSERTION_PICKUP_PENDING",
            "ASSERTION_PICKUP_ALREADY_USED",
            "ASSERTION_PICKUP_EXPIRED",
            "ASSERTION_NOT_FOUND",
            "ASSERTION_REVOKED",
            "ASSERTION_EXPIRED",
        ),
        unauthenticated_by_design=True,
        justification=(
            "Redeemed from inside the isolated voting origin, where an account context would "
            "be precisely the linkage the origin exists to prevent (ADR-090)."
        ),
    ),
    _endpoint(
        "dispute.open",
        API_AREA_DISPUTE,
        consequential=True,
        roles=("dispute_reviewer", "eligibility_officer"),
        reason_codes=("DISPUTE_OPEN", "ELIGIBILITY_CASE_NOT_FOUND"),
    ),
    _endpoint(
        "dispute.resolve",
        API_AREA_DISPUTE,
        consequential=True,
        roles=("dispute_reviewer",),
        reason_codes=(
            "DISPUTE_RESOLVED",
            "ELIGIBILITY_SELF_REVIEW_REFUSED",
            "ELIGIBILITY_CASE_NOT_FOUND",
        ),
    ),
)

ELIGIBILITY_CATALOGUE: Mapping[str, EndpointSpec] = build_catalogue(ELIGIBILITY_ENDPOINTS)


def _uuid(request: ApiRequest, name: str) -> UUID:
    try:
        return UUID(str(request.require(name)))
    except ValueError as error:
        raise ApiRequestMalformedError(f"{name} is not a well-formed identifier") from error


def _moment(request: ApiRequest, name: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(request.require(name)))
    except ValueError as error:
        raise ApiRequestMalformedError(f"{name} is not an ISO-8601 timestamp") from error
    if parsed.tzinfo is None:
        raise ApiRequestMalformedError(f"{name} must be timezone-aware")
    return parsed


@dataclass(frozen=True, slots=True)
class EligibilityApi:
    """The identity side's reference adapter.

    Every handler returns a view model, never a domain object: a
    dataclass serialized wholesale is how a field nobody meant to publish
    reaches a caller. The dispatcher scans every body before it leaves.
    """

    runtime: VotingTrustRuntime
    handoff_binding: HandoffBinding
    dispatcher: ApiDispatcher

    def dispatch(self, request: ApiRequest) -> Any:
        return self.dispatcher.dispatch(request)


def build_eligibility_api(
    runtime: VotingTrustRuntime,
    *,
    handoff_binding: HandoffBinding,
    allowed_origins: tuple[str, ...],
) -> EligibilityApi:
    """Wire the identity-side catalogue to handlers over one runtime."""

    def open_case(request: ApiRequest) -> Mapping[str, Any]:
        case = EligibilityCase(
            case_id=_uuid(request, "case_id"),
            voting_context_reference=str(request.require("voting_context_reference")),
            participant_reference=str(request.require("participant_reference")),
            participation_class=str(request.require("participation_class")),
            requested_at=_moment(request, "requested_at"),
            status=EligibilityDecisionStatus.REQUESTED,
        )
        runtime.case_store.save_case(case)
        runtime.eligibility_connection.commit()
        # The participant reference is identity-side data and stays here:
        # the response confirms the case, it does not echo the subject.
        return {"case_id": str(case.case_id), "status": case.status.value}

    def read_case(request: ApiRequest) -> Mapping[str, Any]:
        case = runtime.case_store.get_case(_uuid(request, "case_id"))
        if case is None:
            raise UnknownEligibilityCaseError("no such eligibility case")
        decisions = runtime.case_store.decisions_for_case(case.case_id)
        return {
            "case_id": str(case.case_id),
            "voting_context_reference": case.voting_context_reference,
            "participation_class": case.participation_class,
            "status": case.status.value,
            "decision_count": len(decisions),
        }

    def record_decision(request: ApiRequest) -> Mapping[str, Any]:
        case_id = _uuid(request, "case_id")
        if runtime.case_store.get_case(case_id) is None:
            raise UnknownEligibilityCaseError("no such eligibility case")
        status = EligibilityDecisionStatus(str(request.require("status")))
        return {
            "case_id": str(case_id),
            "status": status.value,
            "reason_codes": tuple(request.require("reason_codes")),
        }

    def mint_assertion(request: ApiRequest) -> Mapping[str, Any]:
        """Claim the participation unit, then mint. Never the reverse.

        Claiming first is what makes the identity-side half of the split
        exactly-once rule hold under a retry: a second call loses on the
        ledger's primary key before a second assertion exists.
        """
        decision = MinimizedDecisionInput(
            voting_context_reference=str(request.require("voting_context_reference")),
            eligibility_class=str(request.require("eligibility_class")),
            organizational_scope=str(request.require("organizational_scope")),
            required_assurance_satisfied=bool(request.require("required_assurance_satisfied")),
            eligibility_result="approved",
        )
        now = _moment(request, "now")
        claimed = runtime.participation_ledger.claim(
            ParticipationUnitLedgerEntry(
                voting_context_reference=decision.voting_context_reference,
                participation_unit_key=str(request.require("participation_unit_key")),
                assertion_minted=True,
                minted_at=now,
            )
        )
        if not claimed:
            runtime.eligibility_connection.rollback()
            raise AssertionAlreadyMintedForUnitError(
                "this participation unit already has an assertion in this voting context"
            )
        # Everything after the claim runs under a rollback guard. A mint
        # that fails - an unbound key service, a malformed field, a
        # storage error - must not leave the claim behind: an uncommitted
        # INSERT that the next successful write commits would mark the
        # participation unit as used while no assertion exists, and the
        # participant would be refused forever with `CREDENTIAL_ALREADY_
        # ISSUED` for an assertion they never received. That is the one
        # failure in this flow that silently disenfranchises someone.
        try:
            assertion = runtime.issuer.mint(
                assertion_id=uuid4(),
                decision=decision,
                now=now,
                expires_at=_moment(request, "expires_at"),
                eligible_population=int(request.require("eligible_population")),
            )
            entry = runtime.issuer.enqueue(
                assertion,
                batch_reference=str(request.require("batch_reference")),
                now=now,
                jitter_fraction=float(request.require("jitter_fraction")),
            )
            runtime.assertion_store.save_assertion(assertion)
            runtime.assertion_store.save_queue_entry(entry)
        except BaseException:
            runtime.assertion_issuer_connection.rollback()
            runtime.eligibility_connection.rollback()
            raise
        runtime.assertion_issuer_connection.commit()
        runtime.eligibility_connection.commit()
        # The assertion identifier is not returned: the participant
        # collects the artifact through the one-time pickup, and an
        # identifier handed back here would be a second copy of it in a
        # channel that has an account context attached.
        return {
            "status": assertion.status.value,
            "batch_reference": entry.batch_reference,
            "release_not_before": entry.release_not_before.isoformat(),
        }

    def evaluate_release(request: ApiRequest) -> Mapping[str, Any]:
        entry = runtime.assertion_store.get_queue_entry(_uuid(request, "assertion_id"))
        if entry is None:
            raise UnknownAssertionError("no such queued assertion")
        release_now, cohort_class, below_minimum = runtime.issuer.release_decision(
            entry,
            cohort_size=int(request.require("cohort_size")),
            now=_moment(request, "now"),
            eligible_population=int(request.require("eligible_population")),
        )
        # The cohort is reported as a class, never as a number: an exact
        # cohort size in a small electorate is a participation statement.
        return {
            "release_now": release_now,
            "cohort_size_class": cohort_class.value,
            "below_minimum_cohort": below_minimum,
        }

    def accept_handoff(request: ApiRequest) -> Mapping[str, Any]:
        artifact = VotingHandoffArtifact(
            value=str(request.require("artifact_value")),
            voting_context_reference=str(request.require("voting_context_reference")),
            audience=str(request.require("audience")),
            origin=request.origin,
            expires_at=_moment(request, "expires_at"),
        )
        now = _moment(request, "now")
        digest = verify_handoff(
            artifact,
            binding=handoff_binding,
            voting_context_reference=artifact.voting_context_reference,
            now=now,
            previous=runtime.handoff_store.get(artifact_digest(artifact.value)),
        )
        accepted = runtime.handoff_store.accept_once(
            HandoffAcceptance(
                acceptance_id=uuid4(),
                artifact_digest=digest,
                voting_context_reference=artifact.voting_context_reference,
                audience=artifact.audience,
                origin=artifact.origin,
                accepted_at=now,
            )
        )
        if not accepted:
            runtime.assertion_issuer_connection.rollback()
            raise HandoffAlreadyUsedError(
                "a handoff artifact is single-use; a second presentation is refused"
            )
        runtime.assertion_issuer_connection.commit()
        # The digest is not returned either. It is this side's key, and a
        # caller holding it could probe whether a given artifact was used.
        return {"accepted": True, "voting_context_reference": artifact.voting_context_reference}

    def consume_pickup(request: ApiRequest) -> Mapping[str, Any]:
        digest = str(request.require("handoff_artifact_digest"))
        pickup = runtime.assertion_store.get_pickup_by_digest(digest)
        if pickup is None:
            raise UnknownAssertionError("no assertion is available for this handoff")
        now = _moment(request, "now")
        runtime.issuer.consume_pickup(pickup, now=now)
        if not runtime.assertion_store.consume_pickup(pickup.pickup_id, consumed_at=now):
            runtime.assertion_issuer_connection.rollback()
            raise AssertionPickupAlreadyUsedError(
                "the one-time assertion pickup has already been consumed"
            )
        assertion = runtime.assertion_store.get_assertion(pickup.assertion_id)
        if assertion is None:
            runtime.assertion_issuer_connection.rollback()
            raise UnknownAssertionError("the pickup refers to an assertion that no longer exists")
        assertion.assert_live(now)
        runtime.assertion_issuer_connection.commit()
        # `wire_payload` is the closed twelve-field crossing artifact of
        # ADR-091. It is the one place an assertion identifier and a
        # nonce legitimately leave this service, and only into the
        # isolated voting origin.
        return {"assertion": assertion.wire_payload()}

    def open_dispute(request: ApiRequest) -> Mapping[str, Any]:
        case_id = _uuid(request, "case_id")
        if runtime.case_store.get_case(case_id) is None:
            raise UnknownEligibilityCaseError("no such eligibility case")
        return {"case_id": str(case_id), "dispute_status": "open"}

    def resolve_dispute(request: ApiRequest) -> Mapping[str, Any]:
        case_id = _uuid(request, "case_id")
        if runtime.case_store.get_case(case_id) is None:
            raise UnknownEligibilityCaseError("no such eligibility case")
        return {
            "case_id": str(case_id),
            "dispute_status": "resolved",
            "outcome": str(request.require("outcome")),
        }

    dispatcher = ApiDispatcher(
        catalogue=ELIGIBILITY_CATALOGUE,
        handlers={
            "eligibility.case.open": open_case,
            "eligibility.case.read": read_case,
            "eligibility.decision.record": record_decision,
            "assertion.mint": mint_assertion,
            "assertion.release.evaluate": evaluate_release,
            "handoff.accept": accept_handoff,
            "assertion.pickup.consume": consume_pickup,
            "dispute.open": open_dispute,
            "dispute.resolve": resolve_dispute,
        },
        allowed_origins=allowed_origins,
    )
    return EligibilityApi(runtime=runtime, handoff_binding=handoff_binding, dispatcher=dispatcher)
