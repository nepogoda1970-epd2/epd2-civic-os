"""The audit-side versioned API: catalogue and reference adapter.

The generic half - the endpoint spec, the obligations, the request and
response values, the response-safety scan and the dispatcher - lives in
`epd2_core.api_contracts`, because four services need it and no service
may import another. What lives here is audit-core's own **endpoint list**
and its handlers.

Every endpoint below is declared `TrustSide.NEUTRAL`, which is a statement
about the adapter and not about the streams it reaches. The six streams
are emphatically not neutral - AS-01 and AS-02 are the identity side,
AS-03 and AS-04 the voting side - and the neutrality claimed here is that
**one request never touches more than one of those groups**. Three
mechanisms hold that claim up, and they are deliberately redundant,
because this is the one boundary whose failure cannot be undone after the
fact:

* **The request is refused.** `evidence.stream.read` runs
  `assert_streams_separable` over the streams a caller names, so a query
  spanning the boundary is rejected before anything is read. A refusal
  after the read would be theatre: once one principal has seen both
  sides, the link exists in that principal's head and no later error
  removes it.
* **The connection does not exist.** `VotingEvidenceRuntime` holds three
  stores over three different databases and refuses to be built with two
  of them sharing a connection. The `evidence.stream.*` handlers route a
  stream to the one store whose database owns it, so an identity-side
  read and a voting-side read are issued against different files and a
  join between AS-02 and AS-03 has no syntax to be written in.
* **The export is scoped.** `evidence.bundle.export` re-derives the
  bundle from the same inputs it authorizes, rather than accepting a
  bundle somebody assembled elsewhere and posted in - a bundle built
  outside this module is a bundle whose disclosure suppression nobody
  applied, and its signature would say only that the sender had a key.

There is deliberately **no endpoint that searches a stream by subject
across contexts**, and none that returns a record from one side beside a
record from the other. Neither can be declared here, because no handler
holds two connections at once.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import uuid4

from epd2_audit_core.voting_audit_sql_storage import (
    SqlEvidenceBundleExportStore,
    SqlVotingAuditStreamStore,
    VotingAuditRecord,
)
from epd2_audit_core.voting_evidence_bundle import (
    BUNDLE_SECTIONS,
    AuditStream,
    BundleSigningCustody,
    EvidenceBundle,
    EvidenceBundleScopeRefusedError,
    assert_export_authorized,
    assert_no_intermediate_tally,
    assert_streams_separable,
    build_bundle,
    validate_bundle,
)
from epd2_core.api_contracts import (
    PROHIBITED_RESPONSE_KEYS,
    ApiDispatcher,
    ApiRequest,
    ApiRequestMalformedError,
    EndpointSpec,
    TrustSide,
    build_catalogue,
)

API_AREA_EVIDENCE = "evidence"

#: The roles that record onto a stream. Appending is not a privilege of
#: the auditors: an auditor who can write the evidence they later read is
#: an auditor whose findings are their own composition.
STREAM_WRITER_ROLES: tuple[str, ...] = (
    "credential_issuer",
    "eligibility_officer",
    "voting_operations_officer",
)

#: The roles that read a stream. Which streams any of them can actually
#: reach is not decided here but by the deployment: a process is handed
#: the store for the side it serves, and the separation matrix in
#: `governance-service` refuses to grant one principal both. This module
#: cannot consult that matrix - audit-core is the dependency every service
#: has, and importing a service from it would invert the arrow - so it
#: enforces the half it owns, which is that one read touches one stream.
STREAM_READER_ROLES: tuple[str, ...] = (
    "credential_issuer",
    "dispute_reviewer",
    "eligibility_officer",
    "eligibility_reviewer",
    "independent_auditor",
    "security_auditor",
)

#: Bundle assembly is open to the two roles holding an export grant.
BUNDLE_BUILDER_ROLES: tuple[str, ...] = ("independent_auditor", "voting_operations_officer")

#: Export names one role because `assert_export_authorized` accepts one.
#: Declaring a second here would advertise an endpoint that can only ever
#: refuse the caller it invited.
BUNDLE_EXPORT_ROLES: tuple[str, ...] = ("independent_auditor",)


class AuditDatabaseNotSeparatedError(RuntimeError):
    """A runtime was assembled with two sides sharing one connection.

    Raised while the runtime is being built, not while a request is being
    served, because by request time the correlation is already reachable:
    one connection over both sides is a join anybody holding it can write,
    whatever the API in front of it refuses.
    """

    reason_code = "CORRELATION_RISK_DETECTED"


class AuditRecordPayloadRefusedError(RuntimeError):
    """A record was offered a payload no response may carry.

    Refused at append rather than filtered at read. A record written with
    a participant reference in it is a record that either cannot be read
    back at all - the dispatcher's response scan would refuse it - or,
    worse, one that is read back before anybody notices. Neither is a
    state an append-only store should be able to reach, and an append-only
    store is precisely one that cannot be corrected afterwards.
    """

    reason_code = "VOTING_BOUNDARY_INTEGRITY_VIOLATION"


def assert_payload_recordable(payload: Mapping[str, Any]) -> None:
    """Refuse an audit payload carrying what no response may carry.

    The prohibited set is `epd2_core`'s, not a second copy: a stream whose
    write rule and whose read rule are maintained separately is a stream
    where the two eventually disagree.
    """
    offending = sorted(set(payload) & PROHIBITED_RESPONSE_KEYS)
    if offending:
        raise AuditRecordPayloadRefusedError(
            "an audit record may not carry: " + ", ".join(offending)
        )


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
    """Declare one audit-side endpoint.

    Consequential endpoints take all three obligations; read endpoints
    take none. Stating them here rather than defaulting them keeps
    `assert_consequential_contract` meaningful, which is what makes "every
    consequential endpoint carries an idempotency key" survive the tenth
    endpoint somebody adds in a hurry.
    """
    return EndpointSpec(
        operation=operation,
        area=area,
        trust_side=TrustSide.NEUTRAL,
        consequential=consequential,
        idempotency_key_required=consequential,
        version_check_required=consequential,
        audit_evidence_required=consequential,
        authorized_roles=roles,
        reason_codes=reason_codes,
        unauthenticated_by_design=unauthenticated_by_design,
        justification=justification,
    )


EVIDENCE_ENDPOINTS: tuple[EndpointSpec, ...] = (
    _endpoint(
        "evidence.stream.append",
        API_AREA_EVIDENCE,
        consequential=True,
        roles=STREAM_WRITER_ROLES,
        reason_codes=(
            "EVIDENCE_BUNDLE_SCOPE_REFUSED",
            "VOTING_BOUNDARY_INTEGRITY_VIOLATION",
            "AUDIT_UNAVAILABLE",
            "API_REQUEST_MALFORMED",
        ),
    ),
    _endpoint(
        "evidence.stream.read",
        API_AREA_EVIDENCE,
        consequential=False,
        roles=STREAM_READER_ROLES,
        reason_codes=(
            "EVIDENCE_BUNDLE_SCOPE_REFUSED",
            "CORRELATION_RISK_DETECTED",
            "VOTING_BOUNDARY_INTEGRITY_VIOLATION",
            "PERMISSION_DENIED",
            "API_REQUEST_MALFORMED",
        ),
    ),
    _endpoint(
        "evidence.bundle.build",
        API_AREA_EVIDENCE,
        consequential=True,
        roles=BUNDLE_BUILDER_ROLES,
        reason_codes=(
            "EVIDENCE_BUNDLE_INVALID",
            "EVIDENCE_BUNDLE_PRECLOSURE_REFUSED",
            "EVIDENCE_BUNDLE_SUPPRESSED",
            "DISCLOSURE_CONTROL_SUPPRESSED",
            "INTERMEDIATE_TALLY_PROHIBITED",
            "API_REQUEST_MALFORMED",
        ),
    ),
    _endpoint(
        "evidence.bundle.export",
        API_AREA_EVIDENCE,
        consequential=True,
        roles=BUNDLE_EXPORT_ROLES,
        reason_codes=(
            "EVIDENCE_BUNDLE_EXPORTED",
            "EVIDENCE_BUNDLE_SCOPE_REFUSED",
            "EVIDENCE_BUNDLE_PRECLOSURE_REFUSED",
            "EVIDENCE_BUNDLE_INVALID",
            "INTERMEDIATE_TALLY_PROHIBITED",
            "API_REQUEST_MALFORMED",
        ),
    ),
)

EVIDENCE_CATALOGUE: Mapping[str, EndpointSpec] = build_catalogue(EVIDENCE_ENDPOINTS)


def _moment(request: ApiRequest, name: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(request.require(name)))
    except ValueError as error:
        raise ApiRequestMalformedError(f"{name} is not an ISO-8601 timestamp") from error
    if parsed.tzinfo is None:
        raise ApiRequestMalformedError(f"{name} must be timezone-aware")
    return parsed


def _integer(request: ApiRequest, name: str, default: int | None = None) -> int:
    if default is not None and name not in request.body:
        return default
    try:
        return int(request.require(name))
    except (TypeError, ValueError) as error:
        raise ApiRequestMalformedError(f"{name} is not a whole number") from error


def _stream(value: object) -> AuditStream:
    try:
        return AuditStream(str(value))
    except ValueError as error:
        raise ApiRequestMalformedError(f"{value!r} is not one of the six audit streams") from error


def _streams(request: ApiRequest, name: str) -> tuple[AuditStream, ...]:
    raw = request.require(name)
    if isinstance(raw, (str, bytes)) or not isinstance(raw, (list, tuple)):
        raise ApiRequestMalformedError(f"{name} is a list of stream identifiers")
    return tuple(_stream(item) for item in raw)


def _mapping(request: ApiRequest, name: str) -> Mapping[str, Any]:
    value = request.body.get(name, {})
    if not isinstance(value, Mapping):
        raise ApiRequestMalformedError(f"{name} is a mapping")
    return value


def _counts(request: ApiRequest, name: str) -> dict[str, int]:
    """Read one totals section, refusing a value that is not a count.

    A total that arrives as a string is not coerced. Disclosure control
    compares each cell against the minimum, and a cell that silently
    became a string would compare as something else entirely - which is a
    suppression rule that did not run, reported as one that did.
    """
    section = _mapping(request, name)
    counts: dict[str, int] = {}
    for cell, value in section.items():
        if isinstance(value, bool) or not isinstance(value, int):
            raise ApiRequestMalformedError(f"{name}.{cell} is not a count")
        counts[str(cell)] = value
    return counts


@dataclass(frozen=True, slots=True)
class VotingEvidenceRuntime:
    """Three stream stores over three databases, plus the export log.

    The three stores are separate fields rather than one keyed by stream,
    because a single field would be an invitation to open one connection
    across both sides of the boundary - and one connection is all a
    correlating query needs. `__post_init__` refuses a runtime whose
    stores share a connection or whose stream sets overlap, so a
    deployment that starts is a deployment whose audit separation held.

    The export log is required to live in the neutral database. Placing it
    beside either side's records would make "which bundles were exported"
    a question answerable only by a principal holding that side.
    """

    identity_side: SqlVotingAuditStreamStore
    voting_side: SqlVotingAuditStreamStore
    neutral: SqlVotingAuditStreamStore
    exports: SqlEvidenceBundleExportStore
    custody: BundleSigningCustody

    def __post_init__(self) -> None:
        stores = self.stream_stores()
        if len({id(store.connection) for store in stores}) != len(stores):
            raise AuditDatabaseNotSeparatedError(
                "the identity-side, voting-side and neutral audit stores are three "
                "connections over three databases, never one connection over all of them"
            )
        for index, first in enumerate(stores):
            for second in stores[index + 1 :]:
                shared = sorted(
                    stream.value for stream in first.permitted_streams & second.permitted_streams
                )
                if shared:
                    raise AuditDatabaseNotSeparatedError(
                        "two audit databases claim the same streams: " + ", ".join(shared)
                    )
        if self.exports.connection is not self.neutral.connection:
            raise AuditDatabaseNotSeparatedError(
                "the evidence-bundle export log belongs to the neutral audit database"
            )

    def stream_stores(self) -> tuple[SqlVotingAuditStreamStore, ...]:
        return (self.identity_side, self.voting_side, self.neutral)

    def store_for(self, stream: AuditStream) -> SqlVotingAuditStreamStore:
        """The one store whose database owns this stream.

        A stream with no store is refused rather than defaulted to the
        neutral one: writing an unrouted stream somewhere plausible is how
        an identity-side record ends up in a database the voting side can
        read.
        """
        for store in self.stream_stores():
            if stream in store.permitted_streams:
                return store
        raise EvidenceBundleScopeRefusedError(
            f"{stream.value} is not served by any audit database this runtime holds"
        )


@dataclass(frozen=True, slots=True)
class VotingEvidenceApi:
    """Audit-core's reference adapter.

    Every handler returns a view model, never a domain object: a
    dataclass serialized wholesale is how a field nobody meant to publish
    reaches a caller. The dispatcher scans every body before it leaves.
    """

    runtime: VotingEvidenceRuntime
    dispatcher: ApiDispatcher

    def dispatch(self, request: ApiRequest) -> Any:
        return self.dispatcher.dispatch(request)


def _bundle(request: ApiRequest, custody: BundleSigningCustody) -> EvidenceBundle:
    """Assemble and validate a bundle from the request's own inputs.

    Shared by `evidence.bundle.build` and `evidence.bundle.export` so the
    two cannot drift. An export that accepted a prepared `EvidenceBundle`
    would be an export of whatever the caller signed, and the disclosure
    suppression, the pre-closure rule and the count-consistency checks
    would all have run - if at all - somewhere this module cannot see.
    """
    context_closed = bool(request.require("context_closed"))
    # Outcome-bearing keys in the request itself are refused before the
    # bundle exists: a caller sending `turnout` before closure is asking
    # for an intermediate tally regardless of which section it lands in.
    assert_no_intermediate_tally(request.body, context_closed=context_closed)
    bundle = build_bundle(
        voting_context_reference=str(request.require("voting_context_reference")),
        context_metadata=_mapping(request, "context_metadata"),
        configuration_versions=_mapping(request, "configuration_versions"),
        eligibility_totals=_counts(request, "eligibility_totals"),
        assertion_totals=_counts(request, "assertion_totals"),
        credential_totals=_counts(request, "credential_totals"),
        integrity_commitments={
            str(key): str(value)
            for key, value in _mapping(request, "integrity_commitments").items()
        },
        provenance=_mapping(request, "provenance"),
        minimum_cell=_integer(request, "minimum_cell", 5),
        generated_at_bucket=_moment(request, "generated_at_bucket"),
        custody=custody,
        context_closed=context_closed,
    )
    validate_bundle(bundle, custody=custody)
    return bundle


def build_voting_evidence_api(
    runtime: VotingEvidenceRuntime,
    *,
    allowed_origins: tuple[str, ...],
) -> VotingEvidenceApi:
    """Wire the audit-side catalogue to handlers over one runtime."""

    def append_record(request: ApiRequest) -> Mapping[str, Any]:
        """Append one record to exactly one stream.

        The stream is resolved to a store before the record is built, so a
        stream this runtime does not serve is refused without a row being
        assembled for it. The store then refuses it a second time if it
        does not belong to that database - the two checks are the same
        rule stated at the routing layer and at the storage layer, and the
        second is the one that still holds if somebody later hands the
        handler a store directly.
        """
        stream = _stream(request.require("stream"))
        store = runtime.store_for(stream)
        subject = str(request.require("subject"))
        if not subject:
            raise ApiRequestMalformedError(
                "a record names its stream-local subject or observation class"
            )
        payload = _mapping(request, "payload")
        assert_payload_recordable(payload)
        record = VotingAuditRecord(
            record_id=uuid4(),
            stream=stream,
            voting_context_reference=str(request.require("voting_context_reference")),
            event_type=str(request.require("event_type")),
            reason_code=str(request.require("reason_code")),
            recorded_at_bucket=_moment(request, "recorded_at_bucket"),
            subject=subject,
            payload_hash=str(request.require("payload_hash")),
            payload=payload,
            retention_class=str(request.require("retention_class")),
            legal_hold=bool(request.body.get("legal_hold", False)),
        )
        store.append(record)
        store.connection.commit()
        # The subject is not echoed. The caller supplied it, so returning
        # it teaches nobody anything, and a response carrying an
        # identity-side subject is a copy of it in a channel with weaker
        # retention than the stream it was written to.
        return {
            "record_id": str(record.record_id),
            "stream": record.stream.value,
            "voting_context_reference": record.voting_context_reference,
            "event_type": record.event_type,
            "recorded_at_bucket": record.recorded_at_bucket.isoformat(),
        }

    def read_stream(request: ApiRequest) -> Mapping[str, Any]:
        """Read one stream for one context, or refuse.

        `assert_streams_separable` runs first and refuses a request naming
        streams from both groups. The single-stream rule that follows is
        not the same check: two identity-side streams do not span the
        boundary, but serving them in one response still hands a reader a
        joined view of AS-01 and AS-02 that no store produced. One read,
        one stream, one context - and the response therefore carries
        exactly one key space, which is why the records below can name
        their subject at all.
        """
        streams = _streams(request, "streams")
        assert_streams_separable(streams)
        if len(set(streams)) != 1:
            raise EvidenceBundleScopeRefusedError(
                "one stream per read; a combined view is assembled by the reader, not served"
            )
        stream = streams[0]
        store = runtime.store_for(stream)
        reference = str(request.require("voting_context_reference"))
        records = store.records(stream, reference)
        return {
            "stream": stream.value,
            "voting_context_reference": reference,
            "record_count": len(records),
            "records": [
                {
                    "record_id": str(record.record_id),
                    "event_type": record.event_type,
                    "reason_code": record.reason_code,
                    "recorded_at_bucket": record.recorded_at_bucket.isoformat(),
                    "subject": record.subject,
                    "payload_hash": record.payload_hash,
                    "payload": dict(record.payload),
                    "retention_class": record.retention_class,
                    "legal_hold": record.legal_hold,
                }
                for record in records
            ],
        }

    def build_evidence_bundle(request: ApiRequest) -> Mapping[str, Any]:
        """Build a bundle and validate it before anybody sees a summary.

        The bundle itself is not returned. It is a signed artifact whose
        delivery is the export, and handing a copy back here would put a
        second one in a channel that ran none of the export's
        authorization - no grant, no dual control, no single-context
        check. What comes back is what a caller needs to decide whether to
        export: the schema version, the signature and key it would be
        exported under, whether it is pre-closure, and how much of it
        disclosure control suppressed.
        """
        bundle = _bundle(request, runtime.custody)
        return {
            "voting_context_reference": bundle.voting_context_reference,
            "bundle_schema_version": bundle.bundle_schema_version,
            "key_identifier": bundle.key_identifier,
            "signature": bundle.signature,
            "pre_closure": bundle.pre_closure,
            "generated_at_bucket": bundle.generated_at_bucket.isoformat(),
            "sections": list(BUNDLE_SECTIONS),
            "suppressed_cell_count": len(bundle.suppressed),
        }

    def export_evidence_bundle(request: ApiRequest) -> Mapping[str, Any]:
        """Authorize the export, then persist it.

        Authorization runs against the bundle's own context rather than a
        list the caller supplied, so "one context per bundle" cannot be
        satisfied by naming one context and exporting another. A
        pre-closure export additionally needs a dual-control reference,
        and the export table's CHECK requires the same thing - the second
        copy of the rule is the one that still holds if this handler is
        ever bypassed.
        """
        bundle = _bundle(request, runtime.custody)
        dual_control_reference = request.body.get("dual_control_reference")
        grant_reference = str(request.require("grant_reference"))
        assert_export_authorized(
            role=request.actor_role,
            grant_reference=grant_reference,
            contexts=(bundle.voting_context_reference,),
            streams=_streams(request, "streams"),
            context_closed=not bundle.pre_closure,
            dual_control_reference=dual_control_reference,
        )
        bundle_id = uuid4()
        runtime.exports.record_export(
            bundle,
            bundle_id=bundle_id,
            exported_by_role=request.actor_role,
            grant_reference=grant_reference,
            dual_control_reference=(
                None if dual_control_reference is None else str(dual_control_reference)
            ),
        )
        runtime.exports.connection.commit()
        return {
            "bundle_id": str(bundle_id),
            "voting_context_reference": bundle.voting_context_reference,
            "bundle_schema_version": bundle.bundle_schema_version,
            "key_identifier": bundle.key_identifier,
            "pre_closure": bundle.pre_closure,
            "reason_code": "EVIDENCE_BUNDLE_EXPORTED",
        }

    dispatcher = ApiDispatcher(
        catalogue=EVIDENCE_CATALOGUE,
        handlers={
            "evidence.stream.append": append_record,
            "evidence.stream.read": read_stream,
            "evidence.bundle.build": build_evidence_bundle,
            "evidence.bundle.export": export_evidence_bundle,
        },
        allowed_origins=allowed_origins,
    )
    return VotingEvidenceApi(runtime=runtime, dispatcher=dispatcher)
