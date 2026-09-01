"""Data Plane Service domain primitives (PACK-13).

Value objects, the structural prohibitions and the pure predicate
functions every other module in this package is built on. No I/O, no
clock, no storage: everything here is deterministic and testable in
isolation, exactly as `finance-service.domain` is for PACK-10 and
`privileged_access_service.domain` is for PACK-12.

Five rules shape everything below, and each one is the specification's
governing sentence expressed as a type:

- **The data plane is infrastructure, not an authority.** Nothing in this
  module decides anything a domain owns. Retention decisions are PACK-09's,
  authorization is PACK-12's, meaning is the canon's; this package carries
  references to those decisions and refuses when they are absent.
- **Scope travels with everything.** Every scoped record carries an
  `OrganizationScopeReference`; scope is never added by a projection and
  never dropped in transit (`P13-CTX-002`, `P13-DP-005`).
- **No global person key exists.** There is deliberately no value object
  here capable of correlating a person across domains, and
  `GLOBAL_IDENTITY_KEYS` is the structural backstop for a payload
  assembled somewhere else (`P13-DP-008`, `P13-DP-016`, FIR-INV-001).
- **No voting reference type exists.** Nothing in this package can point
  at ballot content, a vote envelope, a voting credential or an
  intermediate tally. The prohibition is structural, so there is nothing
  to misconfigure (`P13-DP-012`, `P13-VOTE-001`..`007`).
- **A reserved boundary is a boundary, not a service.** The identity,
  eligibility, credential, voting and tally/result-certification
  boundaries have owners *to be established* by PACK-14 and PACK-15/16.
  This package creates no schema, table or namespace for any of them
  (`P13-OWN-009`..`013`).
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from epd2_data_plane_service.exceptions import (
    GlobalUserIdentifierProhibitedError,
    OrganizationScopeMissingError,
    ReservedBoundarySchemaProhibitedError,
    VotingMaterialProhibitedError,
)

# ---------------------------------------------------------------------------
# Payload minimisation
# ---------------------------------------------------------------------------

#: Secrets and credential-shaped field names that may never appear in an
#: outbox payload, an idempotency record, a projection row, a migration
#: artifact or any telemetry this package produces (`P13-OBX-008`,
#: `P13-OBS-002`). Enforced **before** the record is written, not before
#: it is dispatched: a payload that reached storage has already leaked
#: into backups.
SECRET_PAYLOAD_KEYS: frozenset[str] = frozenset(
    {
        "password",
        "passphrase",
        "secret",
        "token",
        "access_token",
        "refresh_token",
        "session_token",
        "api_key",
        "apikey",
        "private_key",
        "privatekey",
        "key_material",
        "credential",
        "credentials",
        "certificate_key",
        "signing_key",
        "seed",
        "nonce_secret",
        "connection_string",
        "dsn",
        "database_password",
    }
)

#: Field names that would make a payload a cross-domain person
#: correlation key. These are the load-bearing entries for FIR-INV-001:
#: an idempotency key, a projection column or an event payload carrying
#: one of these is the global identifier the whole architecture forbids.
GLOBAL_IDENTITY_KEYS: frozenset[str] = frozenset(
    {
        "user_id",
        "userid",
        "person_id",
        "personid",
        "global_user_id",
        "global_person_id",
        "global_member_id",
        "global_subject_id",
        "universal_id",
        "universal_person_key",
        "member_id",
        "membership_id",
        "email",
        "email_address",
        "phone",
        "phone_number",
        "full_name",
        "first_name",
        "last_name",
        "address",
        "postal_address",
        "date_of_birth",
        "birth_date",
        "national_id",
        "iban",
        "bic",
    }
)

#: Voting material. PACK-13 defines no type that could carry any of
#: these; this set refuses a payload assembled elsewhere
#: (`P13-VOTE-002`, `P13-VOTE-006`).
VOTING_MATERIAL_KEYS: frozenset[str] = frozenset(
    {
        "ballot",
        "ballot_id",
        "ballot_content",
        "ballot_reference",
        "vote",
        "vote_id",
        "vote_content",
        "vote_envelope",
        "vote_selection",
        "voter_id",
        "voter_choice",
        "choice",
        "tally",
        "partial_tally",
        "intermediate_tally",
        "tally_input",
        "eligibility_token",
        "voting_credential",
        "voting_client_id",
    }
)

#: Bulk content that a minimal payload never carries (`P13-OBX-007`,
#: `P13-EVT-005`..`008`): the digest and the reference travel, the body
#: stays where its owner put it.
BULK_CONTENT_KEYS: frozenset[str] = frozenset(
    {
        "content",
        "body",
        "raw_content",
        "schema_body",
        "schema_document",
        "document_bytes",
        "file_bytes",
        "export_payload",
        "artifact_bytes",
        "extracted_text",
        "ocr_text",
        "query_text",
        "raw_query",
        "sql",
        "sql_text",
        "statement_text",
        "row_data",
        "rows",
        "failed_payload",
    }
)

#: The union applied at every payload boundary in this package.
PROHIBITED_PAYLOAD_KEYS: frozenset[str] = (
    SECRET_PAYLOAD_KEYS | GLOBAL_IDENTITY_KEYS | VOTING_MATERIAL_KEYS | BULK_CONTENT_KEYS
)


class PayloadNotMinimalError(PermissionError):
    """A secret-shaped or bulk-content key reached a payload boundary.

    Deliberately *not* a new registered reason code: the catalog's
    `P13-RSN-002` forbids inventing a generic code, and the refusal an
    operator sees for this case is PACK-02's `PERMISSION_DENIED`, which
    this class carries. It exists so the structural check has a distinct
    Python type for callers and tests to assert on."""

    reason_code = "PERMISSION_DENIED"


def _walk_keys(payload: object) -> list[str]:
    """Return every mapping key appearing anywhere in `payload`, at any
    depth. A prohibited key one level down is the same leak as one at the
    top, so the walk is exhaustive rather than shallow."""
    found: list[str] = []
    if isinstance(payload, Mapping):
        for key, value in payload.items():
            found.append(str(key))
            found.extend(_walk_keys(value))
    elif isinstance(payload, Sequence) and not isinstance(payload, str | bytes):
        for item in payload:
            found.extend(_walk_keys(item))
    return found


def reject_prohibited_payload_keys(payload: object, *, context: str) -> None:
    """Raise the *narrowest* registered refusal if any prohibited key
    appears anywhere in `payload`.

    The order of the three checks is deliberate. Voting material and
    global identity keys get their own reason codes, because
    `DATAPLANE_VOTING_MATERIAL_PROHIBITED` and
    `DATAPLANE_GLOBAL_USER_IDENTIFIER_PROHIBITED` are the two refusals an
    auditor most needs to be able to find by code; a generic
    "forbidden payload" refusal would bury both.
    """
    keys = {key.lower() for key in _walk_keys(payload)}
    voting = sorted(keys & VOTING_MATERIAL_KEYS)
    if voting:
        raise VotingMaterialProhibitedError(
            f"{context}: voting material is prohibited in the general data plane; "
            f"forbidden key(s): {voting}"
        )
    identity = sorted(keys & GLOBAL_IDENTITY_KEYS)
    if identity:
        raise GlobalUserIdentifierProhibitedError(
            f"{context}: a cross-domain person correlation key is prohibited; "
            f"forbidden key(s): {identity}"
        )
    other = sorted(keys & (SECRET_PAYLOAD_KEYS | BULK_CONTENT_KEYS))
    if other:
        raise PayloadNotMinimalError(
            f"{context}: a minimal payload carries references and digests, not content or "
            f"secrets; forbidden key(s): {other}"
        )


def require_timezone(value: datetime, *, field: str) -> datetime:
    """Return `value` unchanged, or raise if it is naive.

    Every timestamp in this package is timezone-aware. A naive timestamp
    in a data plane is a clock-skew bug waiting for a deployment in a
    second region (`P13-ORD-009`)."""
    if value.tzinfo is None:
        raise ValueError(f"{field} must be timezone-aware")
    return value


def content_digest(canonical_text: str) -> str:
    """The SHA-256 hex digest of an already-canonicalized text.

    Deliberately takes *canonical text*, not an object: canonicalization
    is format-specific (`P13-REG-005a`) and lives in
    `epd2_data_plane_service.canonicalization`, so this function cannot
    be called on a raw document by accident."""
    return hashlib.sha256(canonical_text.encode("utf-8")).hexdigest()


def request_digest(canonical_text: str) -> str:
    """The digest an idempotency record stores *instead of* the request.

    Same algorithm as `content_digest`, different name, because the two
    answer different questions and conflating them is how a request body
    ends up in a registry row (`P13-IDEM-008`)."""
    return hashlib.sha256(canonical_text.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Scope, ownership and typed references
# ---------------------------------------------------------------------------


class OrganizationScopeKind(StrEnum):
    """The scope kinds PACK-08 models, carried into persistence as a
    first-class column rather than buried in a payload (`P13-DP-005`)."""

    BUND = "bund"
    LAND = "land"
    KREIS = "kreis"
    LOCAL = "local"


@dataclass(frozen=True, slots=True)
class OrganizationScopeReference:
    """A reference to one organizational scope.

    A *reference*, not an authorization: holding one confers nothing
    (`P13-OWN-003`). It exists so that every record in this package can
    carry the scope its source domain assigned it, and so that a
    projection can be proven to preserve it."""

    organization_id: UUID
    scope_kind: OrganizationScopeKind

    def matches(self, other: OrganizationScopeReference) -> bool:
        return self.organization_id == other.organization_id and self.scope_kind == other.scope_kind


def require_organization_scope(
    scope: OrganizationScopeReference | None, *, context: str
) -> OrganizationScopeReference:
    """Return `scope`, or refuse. A scoped record without scope is not a
    broader record; it is a missing isolation boundary (FIR-INV-013)."""
    if scope is None:
        raise OrganizationScopeMissingError(
            f"{context}: this record class is organization-scoped and no scope was supplied"
        )
    return scope


@dataclass(frozen=True, slots=True)
class DomainReference:
    """The owning domain of a record, a schema or a table.

    An owner is a **domain**, never a platform team and never a database
    role (ownership matrix §1). `is_reserved_boundary` marks the
    conceptual boundaries whose owner a later pack establishes."""

    domain_name: str
    is_reserved_boundary: bool = False

    def __post_init__(self) -> None:
        if not self.domain_name:
            raise ValueError("domain_name must not be empty")


class ReservedBoundary(StrEnum):
    """The conceptual data-plane boundaries PACK-13 does **not** own and
    for which it creates no schema (`P13-OWN-009`..`011`).

    These are boundary names, not service names: `P13-OWN-010` states
    that PACK-13 assigns no final service name to any of them, and the
    reference-implementation services that exist in the baseline settle
    nothing about production ownership."""

    IDENTITY = "future_identity_domain"
    ELIGIBILITY = "future_eligibility_domain"
    CREDENTIAL = "future_credential_domain"
    VOTING = "future_voting_domain"
    TALLY = "future_tally_result_certification_domain"
    COMMUNICATIONS = "future_communications_domain"
    ASSEMBLIES = "future_assemblies_domain"
    CANDIDACY = "future_candidacy_domain"


#: Which pack establishes each reserved boundary's owner. Recorded as
#: data so a test can assert that PACK-13 assigns none of them itself.
RESERVED_BOUNDARY_OWNER_ESTABLISHED_BY: Mapping[ReservedBoundary, str] = {
    ReservedBoundary.IDENTITY: "PACK-14",
    ReservedBoundary.ELIGIBILITY: "PACK-15",
    ReservedBoundary.CREDENTIAL: "PACK-15",
    ReservedBoundary.VOTING: "PACK-15/16",
    ReservedBoundary.TALLY: "PACK-15/16",
    ReservedBoundary.COMMUNICATIONS: "not yet established",
    ReservedBoundary.ASSEMBLIES: "not yet established",
    ReservedBoundary.CANDIDACY: "not yet established",
}


def reject_reserved_boundary_schema(domain: DomainReference, *, context: str) -> None:
    """Refuse to create schema ownership on behalf of a future pack.

    Reserving space in a schema for a domain that does not exist is how a
    shared table is born (ADR-070)."""
    if domain.is_reserved_boundary:
        raise ReservedBoundarySchemaProhibitedError(
            f"{context}: {domain.domain_name!r} is a reserved future ownership boundary; "
            f"PACK-13 creates no table, column, namespace or schema for it"
        )


@dataclass(frozen=True, slots=True)
class AggregateReference:
    """A stable reference to one aggregate instance in one domain.

    Carries the owning domain explicitly, so a cross-domain write is a
    comparison rather than a code-review observation."""

    aggregate_type: str
    aggregate_id: UUID
    owning_domain: DomainReference

    def __post_init__(self) -> None:
        if not self.aggregate_type:
            raise ValueError("aggregate_type must not be empty")


@dataclass(frozen=True, slots=True)
class ActorReference:
    """A **scoped** actor reference (`P13-ID-003`).

    The audit trail records the acting authority, not the human behind
    it, and the reference is meaningful only inside `acting_domain`.
    There is no field here that could be joined to another domain's actor
    reference, which is the point."""

    actor_id: UUID
    actor_type: str
    acting_domain: DomainReference

    def __post_init__(self) -> None:
        if not self.actor_type:
            raise ValueError("actor_type must not be empty")


@dataclass(frozen=True, slots=True)
class ClassificationReference:
    """A reference to the sensitivity classification its source domain
    assigned. PACK-13 reads it; it never assigns one (`P13-DP-006`)."""

    classification_id: UUID
    tier: str


@dataclass(frozen=True, slots=True)
class RecordClassReference:
    """A reference to the PACK-09 record class a persistent class maps to
    (`P13-RET-001`). PACK-09 decides; PACK-13 binds."""

    record_class_id: UUID
    record_class_name: str
    consequential: bool


@dataclass(frozen=True, slots=True)
class EvidenceReference:
    """A PACK-11 evidence-bundle reference (`P13-DOC-002`).

    Migration plans, verification reports and schema publication
    decisions carry these instead of ad-hoc file paths, and no second
    evidence system is created (ADR-078)."""

    evidence_bundle_id: UUID
    content_digest: str

    def __post_init__(self) -> None:
        if not self.content_digest:
            raise ValueError("EvidenceReference requires a content digest")


@dataclass(frozen=True, slots=True)
class DocumentReference:
    """A PACK-11 governed-document reference. A pointer plus a promise
    about its shape — not a licence to open the row (ownership matrix
    §1.3)."""

    document_id: UUID
    version_digest: str


@dataclass(frozen=True, slots=True)
class PrivilegedGrantReference:
    """A reference to a PACK-12 scoped privileged grant (`P13-SEC-002`).

    Purpose-bound, time-bound, approved and evidenced *there*; PACK-13
    only checks that one was presented and that it covers the operation
    and the scope."""

    grant_id: UUID
    purpose: str
    operation: str
    scope: OrganizationScopeReference
    expires_at: datetime

    def __post_init__(self) -> None:
        require_timezone(self.expires_at, field="PrivilegedGrantReference.expires_at")
        if not self.purpose:
            raise ValueError("PrivilegedGrantReference requires a purpose")


@dataclass(frozen=True, slots=True)
class RetentionScheduleReference:
    """A reference to the PACK-09 retention schedule bound to a
    persistent class (`P13-RET-002`). None of infrastructure is exempt by
    virtue of being infrastructure (ADR-078)."""

    schedule_id: UUID
    schedule_name: str


@dataclass(frozen=True, slots=True)
class ApprovalReference:
    """A reference to one approval decision, recording the subject who
    approved and the object version approved (`P13-CC-004`)."""

    approval_id: UUID
    approver: ActorReference
    approved_object_version: int
    decided_at: datetime

    def __post_init__(self) -> None:
        require_timezone(self.decided_at, field="ApprovalReference.decided_at")
        if self.approved_object_version < 0:
            raise ValueError("approved_object_version must not be negative")


# ---------------------------------------------------------------------------
# Delivery-guarantee honesty
# ---------------------------------------------------------------------------

#: The delivery guarantee this package provides, stated once so that
#: every surface quotes the same words (ADR-072, `P13-DEL-001`,
#: `P13-DEL-002`). The stronger phrase is claimed nowhere — not here, not
#: in a docstring, not in a log message, not on an operator surface — and
#: `tests/test_boundaries.py` scans the package source to prove it.
DELIVERY_GUARANTEE = "at-least-once delivery with effectively-once consumer effect"

#: The phrase the scan looks for. Kept as data rather than inline in the
#: test so the prohibition is part of the package's own contract.
FORBIDDEN_DELIVERY_CLAIM = "exactly-once"

#: What this package is, stated in the one word that is true.
DATA_PLANE_IMPLEMENTATION_STATUS = "reference_implementation"

#: Restated at the package boundary because §34 and FIR-INV-015 both turn
#: on it: nothing here is production infrastructure and nothing here is
#: legally activated.
NO_PRODUCTION_CLAIM_NOTE = (
    "Every adapter in this package is an in-memory reference double. No production "
    "database, broker, schema-registry product, search engine or IAM is deployed, "
    "configured or claimed, and no legal activation follows from anything here."
)
