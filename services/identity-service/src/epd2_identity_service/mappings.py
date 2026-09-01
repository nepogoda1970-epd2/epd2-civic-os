"""The governed mapping boundary.

A correlation between two identifier spaces exists **only** through this
module, and only when the mapping carries all seven properties the
identity separation matrix requires: purpose, organizational scope,
domain owner, access policy, retention, audit evidence, and the stated
prohibition on uncontrolled correlation.

The single most important thing here is the operation that does **not**
exist. There is no `list_mappings`, no `find_by_source`, no
`resolve_any`. Every resolution is `(purpose, scope, source)` -> one
target, and an attempt to enumerate raises
`UNRESTRICTED_MAPPING_LOOKUP_REFUSED`. A mapping boundary that anyone may
join is a table, and a table of correlations is the global identifier
this architecture was built to prevent - arrived at by convenience rather
than by decision.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from epd2_identity_service.exceptions import (
    IdentityMappingExpiredError,
    IdentityMappingNotPermittedError,
    IdentityMappingPurposeMismatchError,
    IdentityMappingScopeMismatchError,
    UnknownIdentityMappingStatusError,
    UnrestrictedMappingLookupRefusedError,
)
from epd2_identity_service.identifiers import (
    IdentifierSpace,
    MappingPurpose,
    OrganizationScope,
    ScopedIdentityReference,
    require_timezone,
)


class MappingStatus(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    REVOKED = "revoked"


def parse_mapping_status(value: str) -> MappingStatus:
    try:
        return MappingStatus(value)
    except ValueError as exc:
        raise UnknownIdentityMappingStatusError(f"unknown mapping status: {value!r}") from exc


@dataclass(frozen=True, slots=True)
class MappingAccessPolicy:
    """Who may resolve a mapping, and for what.

    `permitted_domain_owners` is an explicit allowlist of domain owners.
    There is no wildcard: "any domain may resolve this" is not an access
    policy, it is the absence of one.
    """

    permitted_domain_owners: frozenset[str]
    requires_privileged_grant: bool

    def __post_init__(self) -> None:
        if not self.permitted_domain_owners:
            raise ValueError("a mapping access policy names at least one permitted domain owner")
        if "*" in self.permitted_domain_owners:
            raise ValueError("a mapping access policy admits no wildcard")

    def permits(self, domain_owner: str, *, has_privileged_grant: bool) -> bool:
        if domain_owner not in self.permitted_domain_owners:
            return False
        return has_privileged_grant if self.requires_privileged_grant else True


@dataclass(frozen=True, slots=True)
class IdentityMapping:
    """One governed correlation.

    `expires_at` is mandatory. A mapping that never expires becomes the
    global identifier by longevity, which is the failure mode that does
    not look like a failure while it is happening.
    """

    mapping_id: UUID
    purpose: MappingPurpose
    scope: OrganizationScope
    domain_owner: str
    source_space: IdentifierSpace
    target_space: IdentifierSpace
    source_reference: ScopedIdentityReference
    target_reference: ScopedIdentityReference
    access_policy: MappingAccessPolicy
    status: MappingStatus
    retention_class: str
    audit_reference: str
    created_at: datetime
    expires_at: datetime

    def __post_init__(self) -> None:
        require_timezone(self.created_at, "created_at")
        require_timezone(self.expires_at, "expires_at")
        if self.expires_at <= self.created_at:
            raise ValueError("a mapping must expire after it was created")
        if not self.retention_class:
            raise ValueError("every mapping carries a retention class")
        if not self.audit_reference:
            raise ValueError("every mapping carries an audit evidence reference")
        if self.source_reference.purpose is not self.purpose:
            raise IdentityMappingPurposeMismatchError(
                "the source reference was derived for a different purpose"
            )
        if self.target_reference.purpose is not self.purpose:
            raise IdentityMappingPurposeMismatchError(
                "the target reference was derived for a different purpose"
            )

    def is_active(self, now: datetime) -> bool:
        return self.status is MappingStatus.ACTIVE and now < self.expires_at

    def revoked(self) -> IdentityMapping:
        return replace(self, status=MappingStatus.REVOKED)


@dataclass(frozen=True, slots=True)
class MappingResolutionRequest:
    """Every resolution states its purpose, its scope and who is asking.

    All three are required arguments rather than optional context,
    because an optional purpose is a purpose that gets omitted, and an
    omitted purpose is the general-purpose mapping this module exists to
    refuse.
    """

    purpose: MappingPurpose
    scope: OrganizationScope
    requesting_domain_owner: str
    source_reference: ScopedIdentityReference
    has_privileged_grant: bool = False


def resolve_mapping(
    mapping: IdentityMapping | None,
    request: MappingResolutionRequest,
    *,
    now: datetime,
) -> ScopedIdentityReference:
    """Resolve one mapping, or refuse with the code that says why.

    Four separate refusals, deliberately not collapsed: a purpose
    mismatch, a scope mismatch, an expiry and an access-policy denial
    each require a different response from whoever hit them, and a single
    "mapping unavailable" would tell them none of it.
    """
    if mapping is None:
        raise IdentityMappingNotPermittedError(
            "no mapping exists for this purpose, scope and source reference"
        )
    if mapping.purpose is not request.purpose:
        raise IdentityMappingPurposeMismatchError(
            f"the mapping exists for purpose {mapping.purpose.value!r}, "
            f"not {request.purpose.value!r}"
        )
    if not mapping.scope.matches(request.scope):
        raise IdentityMappingScopeMismatchError(
            "the mapping is scoped to a different organizational scope"
        )
    if require_timezone(now, "now") >= mapping.expires_at or mapping.status is not (
        MappingStatus.ACTIVE
    ):
        raise IdentityMappingExpiredError("the mapping has expired or is no longer active")
    if not mapping.access_policy.permits(
        request.requesting_domain_owner, has_privileged_grant=request.has_privileged_grant
    ):
        raise IdentityMappingNotPermittedError(
            f"{request.requesting_domain_owner!r} may not resolve this mapping"
        )
    return mapping.target_reference


def refuse_unrestricted_lookup(
    *, purpose: MappingPurpose | None, scope: OrganizationScope | None
) -> None:
    """The operation this module refuses to provide.

    Called by any storage adapter or administrative surface that is asked
    for "all mappings". It raises whenever a purpose or a scope is
    missing, so the refusal is a code path rather than the absence of a
    feature somebody can add later without noticing what they are adding.
    """
    if purpose is None or scope is None:
        raise UnrestrictedMappingLookupRefusedError(
            "enumeration across mappings requires a purpose and an organizational scope; "
            "there is no operation that lists mappings without both"
        )
