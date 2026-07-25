"""Organization Service exceptions, tied to stable reason codes (PACK-08
implementation round, canon-0.7.0 section 19e, ADR-032 through ADR-037).

Ten canon-fixed codes (canon section 24, 19e.21) are reused verbatim
below. Every other exception reuses a generic, pre-existing project-wide
code (`VALIDATION_*`, `PERMISSION_DENIED`) or declares a narrowly new
additive code, following the same discipline every prior pack's own
`exceptions.py` module already establishes - never a free-text string in
place of a registered code (canon section 24).
"""

from __future__ import annotations


class UnknownOrganizationStatusError(ValueError):
    reason_code = "VALIDATION_UNKNOWN_STATUS"


class ForbiddenOrganizationTransitionError(ValueError):
    reason_code = "VALIDATION_FORBIDDEN_TRANSITION"


class UnknownOrganizationError(ValueError):
    reason_code = "VALIDATION_RECORD_NOT_FOUND"


class UnknownOrganizationalUnitError(ValueError):
    reason_code = "VALIDATION_RECORD_NOT_FOUND"


class UnknownCivicSpaceError(ValueError):
    reason_code = "VALIDATION_RECORD_NOT_FOUND"


class UnknownOrganizationalRelationError(ValueError):
    reason_code = "VALIDATION_RECORD_NOT_FOUND"


class UnknownOrganizationalAuthorityError(ValueError):
    reason_code = "VALIDATION_RECORD_NOT_FOUND"


class UnknownPolicyError(ValueError):
    reason_code = "VALIDATION_RECORD_NOT_FOUND"


class OrganizationNotActiveError(ValueError):
    """Canon 24: a scope- or authority-check ran against an
    `Organization`/`OrganizationalUnit` node not in `active` status."""

    reason_code = "ORGANIZATION_NOT_ACTIVE"


class OrganizationScopeMismatchError(ValueError):
    """Canon 24: the claimed `OrganizationalScope` does not match the
    target record's own scope."""

    reason_code = "ORGANIZATION_SCOPE_MISMATCH"


class CrossScopeAccessDeniedError(PermissionError):
    """Canon 24: none of the six section 19e.12 modes granted access;
    default-deny applied."""

    reason_code = "CROSS_SCOPE_ACCESS_DENIED"


class AuthorityAssignmentInvalidError(ValueError):
    """Canon 24: an `OrganizationalAuthority` assignment violates a
    section 19e.17 lifecycle rule."""

    reason_code = "AUTHORITY_ASSIGNMENT_INVALID"


class AuthorityRoleIncompatibleError(ValueError):
    """Canon 24: an assignment violates the section 19e.16 minimum
    non-combinable-role baseline."""

    reason_code = "AUTHORITY_ROLE_INCOMPATIBLE"


class AuthorityScopeInvalidError(ValueError):
    """Canon 24: an `OrganizationalAuthority.scope` is structurally
    invalid or does not resolve to one of the four section 19e.2
    concepts."""

    reason_code = "AUTHORITY_SCOPE_INVALID"


class SuccessorTransferRequiresDecisionError(ValueError):
    """Canon 24: an attempt to treat `successor_of`/`merged_into`/
    `split_from` as grounds for an authority transfer without its own
    explicit governed decision (section 19e.10's hard invariant)."""

    reason_code = "SUCCESSOR_TRANSFER_REQUIRES_DECISION"


class OrganizationalRelationOverlapError(ValueError):
    """Canon 24: an overlapping hierarchy-category relation without a
    permitting `OrganizationalHierarchyOverlapPolicy`."""

    reason_code = "ORGANIZATIONAL_RELATION_OVERLAP"


class OrganizationalCycleForbiddenError(ValueError):
    """Canon 24: an attempt to create a cycle in a containment/
    subordination-category relation."""

    reason_code = "ORGANIZATIONAL_CYCLE_FORBIDDEN"


class HistoricalScopeNotEffectiveError(ValueError):
    """Canon 24: a request against a historical scope/authority state
    outside its own `[valid_from, valid_until)` window."""

    reason_code = "HISTORICAL_SCOPE_NOT_EFFECTIVE"


class OrganizationSelfAssignmentForbiddenError(PermissionError):
    """Section 19e.17 rule 4 / 19e.16 rule 6: self-assignment of
    institutional authority is forbidden - the appointing actor may never
    equal the assigned subject."""

    reason_code = "ORGANIZATION_SELF_ASSIGNMENT_FORBIDDEN"


class OrganizationDualControlViolationError(PermissionError):
    """Section 19e.16 rule 8 / 19e.17 rule 5: one person cannot satisfy
    both sides of a dual-control action (e.g. propose and activate)."""

    reason_code = "ORGANIZATION_DUAL_CONTROL_VIOLATION"


class TemporarySupervisionWindowInvalidError(ValueError):
    """Section 19e.14: `temporary_supervision_by` requires both
    `valid_from` and `valid_until`; open-ended supervision, or a window
    exceeding the applicable maximum duration, is forbidden."""

    reason_code = "TEMPORARY_SUPERVISION_WINDOW_INVALID"


class TemporarySupervisionExtensionRequiresDecisionError(ValueError):
    """Section 19e.14: extending a temporary-supervision window beyond
    its current `valid_until` requires a new, separately governed
    decision - never a silent extension of the existing record."""

    reason_code = "TEMPORARY_SUPERVISION_EXTENSION_REQUIRES_DECISION"


class OrganizationalAuthorityNotUsableError(PermissionError):
    """Section 19e.17 rule 7: expired, revoked, or suspended authority
    cannot be used."""

    reason_code = "ORGANIZATIONAL_AUTHORITY_NOT_USABLE"


class PermissionDeniedError(PermissionError):
    reason_code = "PERMISSION_DENIED"
