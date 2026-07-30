"""The structural boundary guards (PACK-13 §5, §27, §28; ADR-070).

Every guard here refuses a capability that correct-looking design would
silently create. They are grouped by the boundary they defend.

**Ownership (§5, ADR-070).** Every table has exactly one owning domain,
and exactly four integration mechanisms are admissible: an owned API,
versioned events, a governed projection, an approved read contract. The
list is closed, and `INTEGRATION_MECHANISMS` is that closed list.

**Audit ingestion (`P13-DP-014a`).** The one case that looks like an
exception and is not. *All domains may submit typed audit records through
the governed audit-ingestion contract; only `audit-core` persists
authoritative audit records.* Submission is not persistence:
`AuditIngestionPort` is how every other domain reaches audit, and
`reject_direct_audit_write` refuses the alternative.

**Identity (§27).** No global user ID. Account, person, membership and
each domain's subject reference remain separate identifiers with separate
lifecycles, and there is no type in this package that could join them.

**Voting (§28.1).** Seven prohibitions, each testable as a *structural
absence*. PACK-13 fixes only the general-plane constraints and
deliberately decides nothing about broker topology, connection pools,
service names, credential topology or transport provider — those are
PACK-15/16's, taken with their own threat model (`P13-VOTE-008`).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol
from uuid import UUID

from epd2_data_plane_service.domain import (
    GLOBAL_IDENTITY_KEYS,
    VOTING_MATERIAL_KEYS,
    ActorReference,
    DomainReference,
    OrganizationScopeReference,
    ReservedBoundary,
    reject_prohibited_payload_keys,
    require_timezone,
)
from epd2_data_plane_service.exceptions import (
    AuditDirectWriteDeniedError,
    AuditIngestionContractRequiredError,
    CrossDomainDirectAccessDeniedError,
    GlobalUserIdentifierProhibitedError,
    VotingMaterialProhibitedError,
)

# ---------------------------------------------------------------------------
# Ownership and integration
# ---------------------------------------------------------------------------


class IntegrationMechanism(StrEnum):
    """The four admissible integration mechanisms (ownership matrix §2).

    The list is closed. A shared table, a cross-schema join, a replica
    query, a backup extract and an analytics warehouse copy are each a
    way the boundary is lost while every code review passes, and none of
    them is a member here."""

    OWNED_API = "owned_api"
    VERSIONED_EVENTS = "versioned_events"
    GOVERNED_PROJECTION = "governed_projection"
    APPROVED_READ_CONTRACT = "approved_read_contract"


INTEGRATION_MECHANISMS: frozenset[IntegrationMechanism] = frozenset(IntegrationMechanism)


class ProhibitedAccessPattern(StrEnum):
    """The patterns that are *not* integration mechanisms.

    Enumerated by name so a refusal can say which one was attempted, and
    so a test can assert that none of them appears in
    `INTEGRATION_MECHANISMS`."""

    SHARED_TABLE = "shared_table"
    CROSS_SCHEMA_JOIN = "cross_schema_join"
    REPLICA_QUERY = "replica_query"
    BACKUP_EXTRACT = "backup_extract"
    ANALYTICS_WAREHOUSE_COPY = "analytics_warehouse_copy"
    EMERGENCY_SQL_AS_INTEGRATION = "emergency_sql_as_integration"


@dataclass(frozen=True, slots=True)
class TableOwnership:
    """One table, one owning domain (ADR-070).

    `may_be_read_by` lists the domains that hold an approved read
    contract — a *contract*, not access: the entry means "there is a
    named, versioned read the owner agreed to", never "this domain may
    query the table"."""

    table_name: str
    owning_domain: DomainReference
    organization_scoped: bool
    immutable_history: bool = False
    may_be_read_by: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.table_name:
            raise ValueError("table_name must not be empty")

    def require_owner_write(self, writing_domain: DomainReference) -> None:
        """Only the owner writes (`P13-DP-014`).

        No other service issues an insert, update or delete against an
        owned table, under any circumstance including migration and
        incident response."""
        if writing_domain.domain_name != self.owning_domain.domain_name:
            raise CrossDomainDirectAccessDeniedError(
                f"{writing_domain.domain_name!r} attempted to write {self.table_name!r}, "
                f"owned by {self.owning_domain.domain_name!r}; only the owner writes, not for "
                f"convenience, not for performance, not during migration"
            )

    def require_governed_read(
        self, reading_domain: DomainReference, *, mechanism: IntegrationMechanism | None
    ) -> None:
        """Direct reads by others are not an integration pattern
        (`P13-DP-013`). A read that works is not thereby permitted."""
        if reading_domain.domain_name == self.owning_domain.domain_name:
            return
        if mechanism is None:
            raise CrossDomainDirectAccessDeniedError(
                f"{reading_domain.domain_name!r} attempted a direct read of "
                f"{self.table_name!r}; a query that reads two domains' tables is not an "
                f"integration pattern, it is a boundary violation that happens to compile"
            )
        if mechanism is IntegrationMechanism.APPROVED_READ_CONTRACT and (
            reading_domain.domain_name not in self.may_be_read_by
        ):
            raise CrossDomainDirectAccessDeniedError(
                f"{reading_domain.domain_name!r} holds no approved read contract for "
                f"{self.table_name!r}"
            )


def reject_prohibited_access_pattern(pattern: ProhibitedAccessPattern, *, context: str) -> None:
    """Refuse a non-mechanism presented as integration."""
    raise CrossDomainDirectAccessDeniedError(
        f"{context}: {pattern.value!r} is not one of the four admissible integration "
        f"mechanisms ({sorted(m.value for m in INTEGRATION_MECHANISMS)}); the list is closed"
    )


def reject_shared_schema(table_names_by_domain: Mapping[str, Sequence[str]]) -> None:
    """Refuse a table claimed by more than one domain (`P13-DP-015`).

    A shared "everything" schema and cross-domain "common" tables holding
    identity, contact or membership facts are how the boundary is lost at
    design time rather than at query time."""
    seen: dict[str, str] = {}
    for domain_name, tables in table_names_by_domain.items():
        for table in tables:
            owner = seen.get(table)
            if owner is not None and owner != domain_name:
                raise CrossDomainDirectAccessDeniedError(
                    f"table {table!r} is claimed by both {owner!r} and {domain_name!r}; there "
                    f"is no shared schema and no cross-domain common table"
                )
            seen[table] = domain_name


# ---------------------------------------------------------------------------
# Audit ingestion
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class AuditSubmission:
    """A typed audit record submitted by a non-owner domain.

    A *submission*, not a persisted record. The distinction is the whole
    of `P13-DP-014a`: every domain submits, exactly one domain
    persists."""

    submission_id: UUID
    submitting_domain: DomainReference
    actor: ActorReference
    scope: OrganizationScopeReference
    action: str
    reason_code: str
    submitted_at: datetime
    payload: Mapping[str, str]

    def __post_init__(self) -> None:
        require_timezone(self.submitted_at, field="AuditSubmission.submitted_at")
        if not self.action or not self.reason_code:
            raise AuditIngestionContractRequiredError(
                "an audit submission carries a typed action and a registered reason code"
            )
        reject_prohibited_payload_keys(
            dict(self.payload), context=f"audit submission {self.submission_id}"
        )


#: The one domain that persists authoritative audit records.
AUDIT_OWNER_DOMAIN = "audit-core"


class AuditIngestionPort(Protocol):
    """The governed ingestion contract every other domain reaches audit
    through (`P13-DP-014a`).

    A `Protocol` with exactly one method, and the method takes a
    submission rather than a record: there is no parameter here through
    which a caller could supply a chain position, a previous hash or a
    sequence number. The chain stays with PACK-02."""

    def submit(self, submission: AuditSubmission) -> UUID:
        """Submit a typed audit record; return the submission's
        acknowledgement identifier."""
        ...


@dataclass(frozen=True, slots=True)
class ApplicationCredential:
    """What a domain's application credential grants in the data plane.

    Modelled because `P13-DP-014a` states it as a property of the
    *credential*, not of the code: other domains' application credentials
    carry **no write grant** on the audit schema, and a credential that
    claimed one could not be constructed."""

    domain: DomainReference
    writable_schemas: frozenset[str]
    readable_schemas: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if (
            self.domain.domain_name != AUDIT_OWNER_DOMAIN
            and AUDIT_OWNER_DOMAIN in self.writable_schemas
        ):
            raise AuditDirectWriteDeniedError(
                f"{self.domain.domain_name!r} cannot hold a write grant on the "
                f"{AUDIT_OWNER_DOMAIN!r} schema; other domains submit through the governed "
                f"audit-ingestion contract and only {AUDIT_OWNER_DOMAIN} persists"
            )

    def can_write(self, schema_name: str) -> bool:
        return schema_name in self.writable_schemas


def reject_direct_audit_write(credential: ApplicationCredential, *, target_schema: str) -> None:
    """Refuse a direct write to audit persistence by a non-owner.

    Bulk loading and emergency SQL are not ordinary integration paths,
    and privileged maintenance under PACK-12 does not transfer
    ownership."""
    if target_schema != AUDIT_OWNER_DOMAIN:
        return
    if credential.domain.domain_name != AUDIT_OWNER_DOMAIN:
        raise AuditDirectWriteDeniedError(
            f"{credential.domain.domain_name!r} attempted a direct write to audit "
            f"persistence; submission is not persistence, and append-only describes "
            f"ingestion semantics and authoritative storage alike"
        )


def require_ingestion_contract(*, arrived_via_port: bool, context: str) -> None:
    """Refuse an audit record that arrived by any other path
    (`DATAPLANE_AUDIT_INGESTION_CONTRACT_REQUIRED`)."""
    if not arrived_via_port:
        raise AuditIngestionContractRequiredError(
            f"{context}: an audit record reaches audit-core through the ingestion port, its "
            f"API or a versioned audit command — never by another path"
        )


# ---------------------------------------------------------------------------
# Identity boundary (PACK-14 establishes the owner)
# ---------------------------------------------------------------------------


class IdentifierKind(StrEnum):
    """The identifier kinds §27 keeps separate.

    Four kinds, four lifecycles, and no type in this package that holds
    two of them together. `P13-ID-002` is enforced by that absence more
    than by any check."""

    ACCOUNT_REFERENCE = "account_reference"
    PERSON_REFERENCE = "person_reference"
    MEMBERSHIP_REFERENCE = "membership_reference"
    DOMAIN_SUBJECT_REFERENCE = "domain_subject_reference"


@dataclass(frozen=True, slots=True)
class ScopedSubjectReference:
    """A subject reference meaningful only inside one domain
    (`P13-ID-002`, `P13-ID-004`).

    It carries the owning domain, so two references from two domains are
    two different things even when their UUIDs happen to be equal — and
    `correlates_with` returns `False` across domains by construction
    rather than by policy."""

    subject_id: UUID
    kind: IdentifierKind
    owning_domain: DomainReference

    def correlates_with(self, other: ScopedSubjectReference) -> bool:
        """Whether these two references are the same subject.

        Only ever true within one domain and one kind. There is no
        cross-domain branch, because a cross-domain correlation is the
        thing FIR-INV-001 forbids and this method is the obvious place
        someone would add one."""
        return (
            self.owning_domain.domain_name == other.owning_domain.domain_name
            and self.kind is other.kind
            and self.subject_id == other.subject_id
        )


def reject_global_identifier_column(column_names: Sequence[str], *, table_name: str) -> None:
    """Refuse a column that would be a universal person key
    (`P13-DP-008`, `P13-DP-016`).

    Structural and name-based, which is a real limit: it catches the
    column called `person_id` and not the one called `ref_7`. The
    residual is recorded in the known-limitations document rather than
    implied to be closed."""
    offending = sorted({name.lower() for name in column_names} & GLOBAL_IDENTITY_KEYS)
    if offending:
        raise GlobalUserIdentifierProhibitedError(
            f"table {table_name!r} would carry column(s) {offending}; no column anywhere is a "
            f"universal person key, and a foreign key that would make account, person and "
            f"membership one identifier is forbidden however convenient"
        )


def reject_cross_domain_identity_join(
    left: ScopedSubjectReference, right: ScopedSubjectReference
) -> None:
    """Refuse an attempt to join two domains' subject references
    (`P13-ID-004`, `P13-ID-005`).

    Any future identity mapping crosses an explicit governed boundary
    with its own authorization — not a foreign key, and not this."""
    if left.owning_domain.domain_name != right.owning_domain.domain_name:
        raise GlobalUserIdentifierProhibitedError(
            f"a join between {left.owning_domain.domain_name!r}'s {left.kind.value} and "
            f"{right.owning_domain.domain_name!r}'s {right.kind.value} would correlate a "
            f"person across domains; any identity mapping crosses an explicit governed "
            f"boundary with its own authorization"
        )


#: The identity boundary is a reserved future ownership boundary whose
#: owner PACK-14 establishes (`P13-ID-008`). Recorded so a test can
#: assert that PACK-13 assigns no owner and creates no schema for it.
IDENTITY_BOUNDARY = ReservedBoundary.IDENTITY
IDENTITY_BOUNDARY_OWNER_ESTABLISHED_BY = "PACK-14"


# ---------------------------------------------------------------------------
# Voting boundary (PACK-15/16 own the voting architecture)
# ---------------------------------------------------------------------------


class VotingProhibition(StrEnum):
    """§28.1's seven prohibitions, without exception.

    Each is a constraint on **the general data plane** — the thing
    PACK-13 actually specifies — and each is testable as a structural
    absence."""

    NO_PERSON_TO_BALLOT_TABLE = "no_common_person_to_ballot_table"
    NO_BALLOT_CONTENT_IN_GENERAL_DATABASE = "no_ballot_content_or_secret_in_general_database"
    NO_ELIGIBILITY_TO_BALLOT_LINKAGE = "no_eligibility_to_ballot_linkage_in_general_schema"
    NO_INTERMEDIATE_TALLY_PROJECTION = "no_intermediate_tally_in_general_analytics_projection"
    NO_PARTIAL_RESULT_PUBLICATION = "no_publication_of_partial_results"
    NO_IDENTITY_LINKED_BALLOT_EVENT = "no_identity_linked_ballot_payload_on_general_event_bus"
    NO_GLOBAL_ID_AS_VOTING_CLIENT_ID = (
        "no_global_member_or_account_identifier_as_voting_client_identifier"
    )


VOTING_PROHIBITIONS: frozenset[VotingProhibition] = frozenset(VotingProhibition)

#: What PACK-13 deliberately does **not** decide (`P13-VOTE-008`).
#: Recorded as data so a test can assert that no value in this package
#: settles any of them: fixing them here would be deciding a security
#: architecture from outside the pack that owns it, on the basis of a
#: threat model that has not been written.
VOTING_DECISIONS_DEFERRED_TO_PACK_15_16: tuple[str, ...] = (
    "broker topics or topic naming",
    "whether the broker deployment is separate from or shared with the general plane",
    "connection-pool topology",
    "service names",
    "credential topology",
    "transport provider",
    "deployment topology",
)


def reject_voting_material(payload: Mapping[str, object], *, context: str) -> None:
    """Refuse ballot, credential or tally material anywhere in the
    general plane (`P13-VOTE-002`, `P13-VOTE-006`)."""
    reject_prohibited_payload_keys(dict(payload), context=context)


def reject_ballot_linkage(
    *, left_column_names: Sequence[str], right_column_names: Sequence[str], relation_name: str
) -> None:
    """Refuse a structure linking an eligibility-shaped reference to a
    ballot-shaped one (`P13-VOTE-001`, `P13-VOTE-003`).

    The check is over *column names on both sides of a relation*, which
    is the shape a person-to-ballot table takes: identity-ish on one
    side, ballot-ish on the other."""
    left = {name.lower() for name in left_column_names}
    right = {name.lower() for name in right_column_names}
    identity_side = (left | right) & GLOBAL_IDENTITY_KEYS
    ballot_side = (left | right) & VOTING_MATERIAL_KEYS
    if identity_side and ballot_side:
        raise VotingMaterialProhibitedError(
            f"relation {relation_name!r} would associate {sorted(identity_side)} with "
            f"{sorted(ballot_side)}; no table, index, foreign key, audit column, timestamp "
            f"correlation or physical co-location may make it possible to associate an "
            f"eligibility record with a ballot (P13-DP-017, FIR-INV-002)"
        )


def reject_voting_client_identifier(identifier_field_name: str) -> None:
    """Refuse a global member or account identifier used as a Voting
    Client identifier (`P13-VOTE-007`)."""
    if identifier_field_name.lower() in GLOBAL_IDENTITY_KEYS:
        raise GlobalUserIdentifierProhibitedError(
            f"{identifier_field_name!r} is a global member or account identifier and is not "
            f"used as a Voting Client identifier"
        )


def reject_tally_projection(projection_name: str, *, projected_fields: Sequence[str]) -> None:
    """Refuse an intermediate-tally-shaped projection
    (`P13-VOTE-004`, `P13-VOTE-005`, FIR-INV-005)."""
    offending = sorted({name.lower() for name in projected_fields} & VOTING_MATERIAL_KEYS)
    if offending:
        raise VotingMaterialProhibitedError(
            f"projection {projection_name!r} would carry {offending}; no intermediate tally "
            f"exists in any general analytics projection and no partial result is published"
        )


#: PACK-13 reserves **no space** for the voting domain in the general
#: schema (`P13-VOTE-011`). Stated as an empty tuple rather than omitted,
#: so the claim is a value a test can assert on.
VOTING_RESERVED_SCHEMA_OBJECTS: tuple[str, ...] = ()
