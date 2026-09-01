"""PACK-15 separation-of-duties matrix (`FIR-ROLE-005`).

Ten election roles, their capabilities, and the structural rules that say
which combinations may never exist. It lives in `governance-service`
because governance owns who may do what to a voting context, and because
placing it in either the eligibility side or the voting side would give
one side the authority to describe the other's limits.

The matrix is data, and the rules are functions over that data. That
split is the point: a rule expressed as a sentence in a policy document
is checked when somebody remembers to check it, whereas
`assert_matrix_is_complete()` runs at import time and takes the process
down if a role was added without capabilities or if a capability grant
assembled a prohibited combination. A deployment that starts is a
deployment whose role matrix held.

Every rule refuses by raising. None of them returns `False`, because a
boolean is something a caller can forget to look at, and the failure mode
of a forgotten separation check is an election in which one person held
the whole chain and nothing said so.

The stream groups come from `epd2_audit_core` rather than being restated
here. Audit-core is the one dependency every service is permitted to have
(`docs/architecture/audit-kernel.md`), and a second copy of "which
streams are the identity side" is a second copy that can drift - which is
exactly how a correlation rule stops being enforced without anyone
editing it.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import ClassVar

from epd2_audit_core.voting_evidence_bundle import (
    IDENTITY_SIDE_STREAMS,
    VOTING_SIDE_STREAMS,
    AuditStream,
)

# ---------------------------------------------------------------------------
# Refusals
# ---------------------------------------------------------------------------


class VotingAuthorizationError(ValueError):
    """Base class for every refusal this module raises.

    Carries no `reason_code` of its own, following ADR-004: a refusal
    without a registered code is not a permissible refusal, so the base
    class is never raised directly.
    """


class PermissionDeniedError(VotingAuthorizationError):
    """The ordinary gate: a role that simply does not hold the capability.

    Deliberately distinct from `SeparationOfDutiesRefusedError`. One says
    "you were not granted this"; the other says "this may never be
    granted to you together with what you already hold". Collapsing them
    would make a structural violation look like a missing permission
    somebody can approve their way out of.
    """

    reason_code = "PERMISSION_DENIED"


class SeparationOfDutiesRefusedError(VotingAuthorizationError):
    reason_code = "SEPARATION_OF_DUTIES_REFUSED"


class DualControlRequiredError(VotingAuthorizationError):
    reason_code = "DUAL_CONTROL_REQUIRED"


class PrivilegedApprovalMissingError(VotingAuthorizationError):
    reason_code = "PRIVILEGED_APPROVAL_MISSING"


class CorrelationRiskDetectedError(VotingAuthorizationError):
    """A grant, query or role that would have permitted the correlation.

    Raised before the correlating act, not after it: once two sides have
    been read by one principal the link exists in that principal's head
    and no later refusal removes it.
    """

    reason_code = "CORRELATION_RISK_DETECTED"


class EvidenceBundleScopeRefusedError(VotingAuthorizationError):
    reason_code = "EVIDENCE_BUNDLE_SCOPE_REFUSED"


class ManualReviewRequiredError(VotingAuthorizationError):
    reason_code = "MANUAL_REVIEW_REQUIRED"


class AuthorizationMatrixIncompleteError(ValueError):
    """A malformed matrix declaration. Raised at import time only.

    Not a domain refusal and therefore not reason-coded: no participant
    ever sees it, because a process that raises it never finishes
    starting.
    """


# ---------------------------------------------------------------------------
# Roles
# ---------------------------------------------------------------------------


class VotingRole(StrEnum):
    """The ten roles of the separation matrix, `R-01` through `R-10`.

    The values are the strings the API layer authorizes against, so a
    member of this enum is usable directly as an entry in
    `EndpointSpec.authorized_roles`. There is no eleventh role and no
    "administrator" that stands above the ten: a role outside the matrix
    is a role no rule below constrains.
    """

    MEMBERSHIP_AUTHORITY = "membership_authority"
    ELIGIBILITY_OFFICER = "eligibility_officer"
    ELIGIBILITY_REVIEWER = "eligibility_reviewer"
    CREDENTIAL_ISSUER = "credential_issuer"
    VOTING_OPERATIONS_OFFICER = "voting_operations_officer"
    VOTING_CLIENT_OPERATOR = "voting_client_operator"
    TALLY_AUTHORITY = "tally_authority"
    INDEPENDENT_AUDITOR = "independent_auditor"
    SECURITY_AUDITOR = "security_auditor"
    DISPUTE_REVIEWER = "dispute_reviewer"


#: The matrix identifiers, kept so evidence and review notes can cite
#: `R-04` and mean the same role the specification means.
ROLE_IDENTIFIERS: Mapping[VotingRole, str] = {
    VotingRole.MEMBERSHIP_AUTHORITY: "R-01",
    VotingRole.ELIGIBILITY_OFFICER: "R-02",
    VotingRole.ELIGIBILITY_REVIEWER: "R-03",
    VotingRole.CREDENTIAL_ISSUER: "R-04",
    VotingRole.VOTING_OPERATIONS_OFFICER: "R-05",
    VotingRole.VOTING_CLIENT_OPERATOR: "R-06",
    VotingRole.TALLY_AUTHORITY: "R-07",
    VotingRole.INDEPENDENT_AUDITOR: "R-08",
    VotingRole.SECURITY_AUDITOR: "R-09",
    VotingRole.DISPUTE_REVIEWER: "R-10",
}

#: The two auditing roles. They are singled out because an auditor is the
#: one principal whose job is to look at everything, which makes the
#: auditor the most plausible place for the whole architecture to be
#: quietly undone (`SD-10`).
AUDITOR_ROLES: frozenset[VotingRole] = frozenset(
    {VotingRole.INDEPENDENT_AUDITOR, VotingRole.SECURITY_AUDITOR}
)

#: The matrix names no separate administrator roles, so the two
#: administrative duties are held by the two roles that actually have
#: them: security administration by the Security Auditor, who reviews
#: whether the boundaries held, and system administration by the Voting
#: Operations Officer, who configures and activates contexts.
#: `assert_security_admin_is_not_system_admin` exists so those two duties
#: cannot converge on one capability set later.
SECURITY_ADMIN_ROLE: VotingRole = VotingRole.SECURITY_AUDITOR
SYSTEM_ADMIN_ROLE: VotingRole = VotingRole.VOTING_OPERATIONS_OFFICER


# ---------------------------------------------------------------------------
# Capabilities
# ---------------------------------------------------------------------------


class Capability(StrEnum):
    """What a role may do, named at the granularity the rules need.

    The names are coarse on purpose. A capability set fine enough to
    describe every endpoint is a capability set nobody reads, and the
    separation rules below are statements about authority - deciding
    eligibility, issuing a credential, producing a tally - not about
    routes.
    """

    MEMBERSHIP_RECORD_MAINTENANCE = "membership.record_maintenance"
    ELIGIBILITY_DECISION = "eligibility.decision"
    MANUAL_ELIGIBILITY_EXCEPTION = "eligibility.manual_exception"
    ASSERTION_ISSUANCE = "assertion.issuance"
    CREDENTIAL_ISSUANCE = "credential.issuance"
    CREDENTIAL_REVOCATION = "credential.revocation"
    CREDENTIAL_SECRET_ACCESS = "credential.secret_access"
    #: Case-scoped credential *status*, obtainable only against a
    #: reference the participant supplies. Deliberately not an audit
    #: stream read: the Dispute Reviewer answers "is this credential
    #: revoked" about a credential already in front of them, and never
    #: searches the voting side.
    CASE_SCOPED_CREDENTIAL_STATUS = "credential.case_scoped_status"
    TALLY_OUTCOME = "tally.outcome"
    IDENTITY_RECORD_ACCESS = "identity.record_access"
    VOTING_CLIENT_OPERATION = "voting_client.operation"
    AUDIT_READ_IDENTITY_SIDE = "audit.read_identity_side"
    AUDIT_READ_VOTING_SIDE = "audit.read_voting_side"
    #: `AS-04`, `AS-05` and `AS-06`: integrity, bundles and system
    #: evidence, none of which holds participation data, which is why
    #: holding it does not correlate anything.
    AUDIT_READ_NEUTRAL = "audit.read_neutral"
    #: Per-stream integrity metadata - sizes, commitments, chain
    #: continuity - without the records. The Security Auditor's
    #: compatibility with every other role in the matrix is true only
    #: while its access stays metadata-only.
    AUDIT_READ_INTEGRITY_METADATA = "audit.read_integrity_metadata"
    PRIVILEGED_EXPORT = "privileged.export"
    BREAK_GLASS = "privileged.break_glass"
    CONFIGURATION_ACTIVATION = "configuration.activation"
    DISPUTE_RESOLUTION = "dispute.resolution"


#: The audit-read capabilities that map onto the two stream groups
#: `epd2_audit_core` separates. Holding both is the correlation, whatever
#: the holder's intent.
AUDIT_READ_CAPABILITY_STREAMS: Mapping[Capability, frozenset[AuditStream]] = {
    Capability.AUDIT_READ_IDENTITY_SIDE: IDENTITY_SIDE_STREAMS,
    Capability.AUDIT_READ_VOTING_SIDE: VOTING_SIDE_STREAMS,
}

#: `SD-06`'s three authorities. Issuance is either kind: an actor who can
#: decide eligibility, mint the assertion that carries that decision and
#: then produce the outcome has the whole chain, and it makes no
#: difference which half of issuance they hold.
ELIGIBILITY_AUTHORITY: Capability = Capability.ELIGIBILITY_DECISION
ISSUANCE_AUTHORITY: frozenset[Capability] = frozenset(
    {Capability.ASSERTION_ISSUANCE, Capability.CREDENTIAL_ISSUANCE}
)
TALLY_AUTHORITY_CAPABILITY: Capability = Capability.TALLY_OUTCOME

#: Capabilities that may only be exercised against a reference the
#: participant supplied. Without one the request is a search, and a
#: search across this boundary is the correlation itself.
CASE_SCOPED_CAPABILITIES: frozenset[Capability] = frozenset(
    {Capability.CASE_SCOPED_CREDENTIAL_STATUS}
)

#: Raw participation reads. `SD-16`: no principal holds one of these
#: together with a bundle export grant.
RAW_PARTICIPATION_READS: frozenset[Capability] = frozenset(
    {Capability.AUDIT_READ_IDENTITY_SIDE, Capability.AUDIT_READ_VOTING_SIDE}
)


# ---------------------------------------------------------------------------
# The matrix
# ---------------------------------------------------------------------------


ROLE_CAPABILITIES: Mapping[VotingRole, frozenset[Capability]] = {
    VotingRole.MEMBERSHIP_AUTHORITY: frozenset(
        {
            Capability.MEMBERSHIP_RECORD_MAINTENANCE,
            Capability.IDENTITY_RECORD_ACCESS,
        }
    ),
    VotingRole.ELIGIBILITY_OFFICER: frozenset(
        {
            Capability.ELIGIBILITY_DECISION,
            Capability.ASSERTION_ISSUANCE,
            Capability.IDENTITY_RECORD_ACCESS,
            Capability.AUDIT_READ_IDENTITY_SIDE,
        }
    ),
    VotingRole.ELIGIBILITY_REVIEWER: frozenset(
        {
            Capability.ELIGIBILITY_DECISION,
            Capability.MANUAL_ELIGIBILITY_EXCEPTION,
            Capability.IDENTITY_RECORD_ACCESS,
            Capability.AUDIT_READ_IDENTITY_SIDE,
        }
    ),
    VotingRole.CREDENTIAL_ISSUER: frozenset(
        {
            Capability.CREDENTIAL_ISSUANCE,
            Capability.CREDENTIAL_REVOCATION,
            Capability.CREDENTIAL_SECRET_ACCESS,
            Capability.AUDIT_READ_VOTING_SIDE,
        }
    ),
    VotingRole.VOTING_OPERATIONS_OFFICER: frozenset(
        {
            Capability.CONFIGURATION_ACTIVATION,
            Capability.BREAK_GLASS,
            Capability.PRIVILEGED_EXPORT,
            Capability.AUDIT_READ_NEUTRAL,
        }
    ),
    VotingRole.VOTING_CLIENT_OPERATOR: frozenset(
        {
            Capability.VOTING_CLIENT_OPERATION,
            Capability.AUDIT_READ_NEUTRAL,
        }
    ),
    VotingRole.TALLY_AUTHORITY: frozenset({Capability.TALLY_OUTCOME}),
    VotingRole.INDEPENDENT_AUDITOR: frozenset(
        {
            Capability.PRIVILEGED_EXPORT,
            Capability.AUDIT_READ_NEUTRAL,
        }
    ),
    VotingRole.SECURITY_AUDITOR: frozenset(
        {
            Capability.AUDIT_READ_NEUTRAL,
            Capability.AUDIT_READ_INTEGRITY_METADATA,
        }
    ),
    VotingRole.DISPUTE_REVIEWER: frozenset(
        {
            Capability.DISPUTE_RESOLUTION,
            Capability.IDENTITY_RECORD_ACCESS,
            Capability.AUDIT_READ_IDENTITY_SIDE,
            Capability.CASE_SCOPED_CREDENTIAL_STATUS,
        }
    ),
}


class RoleCompatibility(StrEnum):
    """The three cells of the incompatibility matrix, section 2."""

    COMPATIBLE = "compatible"
    #: The document's triangle: permitted only under dual control and a
    #: time-boxed PACK-12 grant.
    RESTRICTED = "restricted"
    PROHIBITED = "prohibited"


#: Section 2, transcribed row by row in `R-01` .. `R-10` order. `c`
#: compatible, `d` restricted, `x` prohibited, `-` the diagonal. Kept as
#: rows rather than as a set of pairs so it can be read against the
#: document without decoding, and checked for symmetry at import.
_COMPATIBILITY_ROWS: tuple[str, ...] = (
    "-dxxcxxxcx",
    "d-xxxxxxcx",
    "xx-xxxxxcx",
    "xxx-xxxxcx",
    "cxxx-dxxcc",
    "xxxxd-xxcc",
    "xxxxxx-xcx",
    "xxxxxxx-cc",
    "cccccccc-c",
    "xxxxccxcc-",
)

_COMPATIBILITY_SYMBOLS: Mapping[str, RoleCompatibility] = {
    "c": RoleCompatibility.COMPATIBLE,
    "d": RoleCompatibility.RESTRICTED,
    "x": RoleCompatibility.PROHIBITED,
}

_ORDERED_ROLES: tuple[VotingRole, ...] = tuple(VotingRole)


def _build_compatibility() -> Mapping[frozenset[VotingRole], RoleCompatibility]:
    table: dict[frozenset[VotingRole], RoleCompatibility] = {}
    if len(_COMPATIBILITY_ROWS) != len(_ORDERED_ROLES):
        raise AuthorizationMatrixIncompleteError("the compatibility matrix has one row per role")
    for row_index, row in enumerate(_COMPATIBILITY_ROWS):
        if len(row) != len(_ORDERED_ROLES):
            raise AuthorizationMatrixIncompleteError(
                f"compatibility row {row_index + 1} has one cell per role"
            )
        for column_index, symbol in enumerate(row):
            if row_index == column_index:
                if symbol != "-":
                    raise AuthorizationMatrixIncompleteError(
                        "the compatibility matrix's diagonal is not a pair"
                    )
                continue
            pair = frozenset({_ORDERED_ROLES[row_index], _ORDERED_ROLES[column_index]})
            value = _COMPATIBILITY_SYMBOLS.get(symbol)
            if value is None:
                raise AuthorizationMatrixIncompleteError(f"unknown compatibility symbol {symbol!r}")
            existing = table.get(pair)
            if existing is not None and existing is not value:
                raise AuthorizationMatrixIncompleteError(
                    "the compatibility matrix is asymmetric for "
                    f"{sorted(role.value for role in pair)}"
                )
            table[pair] = value
    return table


ROLE_COMPATIBILITY: Mapping[frozenset[VotingRole], RoleCompatibility] = _build_compatibility()


# ---------------------------------------------------------------------------
# Dual control
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Approver:
    """One approver: a principal and the role they approve in.

    A principal may be a person or a service account. Section 6 is
    explicit that a backup job holding both sides violates the matrix
    exactly as a person would, and it is the likelier violation because
    nobody thinks of a deployment identity as holding an election role.
    """

    principal_reference: str
    role: VotingRole


@dataclass(frozen=True, slots=True)
class PrivilegedActRecord:
    """The evidence a satisfied dual-control check produces.

    Returned rather than logged here: this module decides, and the
    caller's audit adapter records. Its reason code is the positive one -
    a privileged act that succeeded is still an act worth finding later,
    particularly if the context it happened in is contested.
    """

    reason_code: ClassVar[str] = "PRIVILEGED_VOTING_ACTION_PERFORMED"

    capability: Capability
    first_approver: Approver
    second_approver: Approver
    grant_reference: str


#: Which roles may stand as an approver for a dual-controlled act.
#: Approving is not performing: the Security Auditor witnesses
#: break-glass without holding it, which is what makes the witness a
#: witness rather than a second pair of hands.
DUAL_CONTROL_APPROVERS: Mapping[Capability, frozenset[VotingRole]] = {
    Capability.PRIVILEGED_EXPORT: frozenset(
        {VotingRole.INDEPENDENT_AUDITOR, VotingRole.VOTING_OPERATIONS_OFFICER}
    ),
    Capability.BREAK_GLASS: frozenset(
        {VotingRole.VOTING_OPERATIONS_OFFICER, VotingRole.SECURITY_AUDITOR}
    ),
    Capability.CONFIGURATION_ACTIVATION: frozenset(
        {VotingRole.VOTING_OPERATIONS_OFFICER, VotingRole.SECURITY_AUDITOR}
    ),
    Capability.MANUAL_ELIGIBILITY_EXCEPTION: frozenset(
        {VotingRole.ELIGIBILITY_REVIEWER, VotingRole.DISPUTE_REVIEWER}
    ),
}


# ---------------------------------------------------------------------------
# The ordinary gate
# ---------------------------------------------------------------------------


def _as_role(role: VotingRole | str) -> VotingRole:
    """Resolve a role name, refusing anything outside the ten.

    The API layer authorizes against strings, and an unrecognized string
    is refused rather than treated as an unprivileged caller: a typo in a
    role name must fail loudly, not quietly grant whatever the empty set
    happens to allow.
    """
    if isinstance(role, VotingRole):
        return role
    try:
        return VotingRole(role)
    except ValueError as error:
        raise PermissionDeniedError(
            "the actor's role is not one of the ten separation-matrix roles"
        ) from error


def capabilities_of(role: VotingRole | str) -> frozenset[Capability]:
    return ROLE_CAPABILITIES[_as_role(role)]


def roles_with(capability: Capability) -> tuple[str, ...]:
    """The role names holding a capability, for `authorized_roles`.

    Returned as sorted plain strings so an endpoint declaration names the
    roles the matrix says hold the authority, instead of a hand-kept list
    that drifts from it.
    """
    return tuple(
        sorted(role.value for role, held in ROLE_CAPABILITIES.items() if capability in held)
    )


def assert_capability_permitted(role: VotingRole | str, capability: Capability) -> None:
    """The ordinary gate: does this role hold this capability at all.

    This is the check that answers "may you", not "may you together with
    what else you hold". The structural rules below answer the second
    question, and they run at import time precisely because this one
    cannot: by the time a request arrives, a prohibited combination has
    already been granted.
    """
    resolved = _as_role(role)
    if capability not in ROLE_CAPABILITIES[resolved]:
        raise PermissionDeniedError(f"{resolved.value} does not hold {capability.value}")


def assert_case_scoped_access(
    role: VotingRole | str, capability: Capability, *, case_reference: str | None
) -> None:
    """A case-scoped capability exercised without a case is a search.

    The Dispute Reviewer's credential-status access is deliberately
    awkward: it answers a question about a credential the participant put
    in front of them. Allowed without a case reference it becomes a
    lookup facility over the voting side, which is the back door `SD-11`
    names.
    """
    resolved = _as_role(role)
    assert_capability_permitted(resolved, capability)
    if capability in CASE_SCOPED_CAPABILITIES and not case_reference:
        raise CorrelationRiskDetectedError(
            f"{capability.value} is answered against a supplied case reference, never by search"
        )


def assert_manual_exception_reviewed(
    role: VotingRole | str, *, review_reference: str | None
) -> None:
    """A manual eligibility exception is a decision, not an override.

    Without a recorded review the exception is indistinguishable from an
    officer changing an outcome they did not like, which is the reading a
    contested election will put on it.
    """
    resolved = _as_role(role)
    assert_capability_permitted(resolved, Capability.MANUAL_ELIGIBILITY_EXCEPTION)
    if not review_reference:
        raise ManualReviewRequiredError(
            "a manual eligibility exception records the review that produced it"
        )


def assert_no_self_review(
    *, actor_principal: str, raised_by_principal: str, subject_principal: str
) -> None:
    """`SD-08`: nobody decides a case they raised or are the subject of.

    Self-approval is the cheapest way to defeat every other rule here,
    because it needs no extra grant, no flag and no second account.
    """
    if not actor_principal:
        raise SeparationOfDutiesRefusedError("a decision names the principal that made it")
    if actor_principal == subject_principal:
        raise SeparationOfDutiesRefusedError("no reviewer decides a case they are the subject of")
    if actor_principal == raised_by_principal:
        raise SeparationOfDutiesRefusedError("no reviewer decides a case they raised")


# ---------------------------------------------------------------------------
# Structural rules over the matrix
# ---------------------------------------------------------------------------


def _resolve(
    matrix: Mapping[VotingRole, frozenset[Capability]] | None,
) -> Mapping[VotingRole, frozenset[Capability]]:
    """The shipped matrix unless a caller supplied one.

    The rules take a matrix argument so a test - or a review of a
    proposed grant - can run them against a hypothetical assignment
    before anybody is given it.
    """
    return ROLE_CAPABILITIES if matrix is None else matrix


def assert_no_role_controls_eligibility_issuance_and_tally(
    matrix: Mapping[VotingRole, frozenset[Capability]] | None = None,
) -> None:
    """`SD-06`: no actor holds the full chain in one context.

    Eligibility says who may vote, issuance produces the token they vote
    with, and the tally says what the votes were. A role holding all
    three can define the electorate, mint into it and declare the result,
    and no downstream evidence distinguishes that from an election.
    """
    for role, held in _resolve(matrix).items():
        if (
            ELIGIBILITY_AUTHORITY in held
            and held & ISSUANCE_AUTHORITY
            and TALLY_AUTHORITY_CAPABILITY in held
        ):
            raise SeparationOfDutiesRefusedError(
                f"{role.value} holds eligibility, issuance and tally authority at once"
            )


def assert_credential_issuer_has_no_identity_access(
    matrix: Mapping[VotingRole, frozenset[Capability]] | None = None,
) -> None:
    """`SD-03`: the Credential Issuer never sees ordinary identity.

    The credential is unattributable only because the party that mints it
    cannot say who it was minted for. Give that party identity access and
    the credential becomes an ordinary named record, whatever the schema
    says.
    """
    held = _resolve(matrix)[VotingRole.CREDENTIAL_ISSUER]
    if Capability.IDENTITY_RECORD_ACCESS in held:
        raise SeparationOfDutiesRefusedError(
            "the Credential Issuer may not hold ordinary identity-record access"
        )


def assert_eligibility_officer_has_no_credential_secret_access(
    matrix: Mapping[VotingRole, frozenset[Capability]] | None = None,
) -> None:
    """The mirror of `SD-03`, taken from the identity side.

    The Eligibility Officer knows the participant. Handing that role the
    credential secret hands it the other end of the link, and the
    boundary is then held by nothing but the officer's restraint.
    """
    held = _resolve(matrix)[VotingRole.ELIGIBILITY_OFFICER]
    if Capability.CREDENTIAL_SECRET_ACCESS in held:
        raise SeparationOfDutiesRefusedError(
            "the Eligibility Officer may not hold credential secret access"
        )


def assert_auditor_cannot_correlate(
    matrix: Mapping[VotingRole, frozenset[Capability]] | None = None,
) -> None:
    """`SD-10`: an auditor holding both sides is the correlation.

    Auditing is the one job where holding everything looks like a virtue,
    which is why it is the likeliest place for this architecture to be
    undone with good intentions. The Independent Auditor works from
    evidence bundles and the Security Auditor from integrity metadata,
    and neither reads both stream groups.
    """
    resolved = _resolve(matrix)
    for role in sorted(AUDITOR_ROLES, key=lambda item: item.value):
        held = resolved[role]
        if (
            Capability.AUDIT_READ_IDENTITY_SIDE in held
            and Capability.AUDIT_READ_VOTING_SIDE in held
        ):
            raise CorrelationRiskDetectedError(
                f"{role.value} would read the identity-side and voting-side audit streams"
            )


def assert_no_role_spans_audit_stream_groups(
    matrix: Mapping[VotingRole, frozenset[Capability]] | None = None,
) -> None:
    """The same rule for every role, not only the auditors.

    The audit separation matrix states it without exception: no role
    holds read access to both `AS-01`/`AS-02` and `AS-03`. A reporting
    role or a support role granted both breaks it exactly as an auditor
    would, and is less likely to be looked at.
    """
    for role, held in _resolve(matrix).items():
        streams: set[AuditStream] = set()
        for capability, group in AUDIT_READ_CAPABILITY_STREAMS.items():
            if capability in held:
                streams |= group
        if streams & IDENTITY_SIDE_STREAMS and streams & VOTING_SIDE_STREAMS:
            raise CorrelationRiskDetectedError(
                f"{role.value} spans the identity-side and voting-side audit streams"
            )


def assert_security_admin_is_not_system_admin(
    matrix: Mapping[VotingRole, frozenset[Capability]] | None = None,
) -> None:
    """Security administration and system administration stay apart.

    A principal who both operates the system and reviews whether the
    system's boundaries held can grant itself an exception and then
    certify that no exception was granted. Distinct roles are not enough:
    if either capability set contains the other, the separation is
    nominal, so equality and containment are both refused.
    """
    resolved = _resolve(matrix)
    if SECURITY_ADMIN_ROLE is SYSTEM_ADMIN_ROLE:
        raise SeparationOfDutiesRefusedError(
            "security administration and system administration are two roles"
        )
    security = resolved[SECURITY_ADMIN_ROLE]
    system = resolved[SYSTEM_ADMIN_ROLE]
    if security == system:
        raise SeparationOfDutiesRefusedError(
            "the security-administration and system-administration capability sets are identical"
        )
    if security <= system or system <= security:
        raise SeparationOfDutiesRefusedError(
            "neither administration role may hold a superset of the other's capabilities"
        )


def assert_role_combination_permitted(
    roles: Iterable[VotingRole | str],
    *,
    grant_reference: str | None = None,
    dual_control_reference: str | None = None,
) -> None:
    """Section 2, applied to the roles one principal actually holds.

    A prohibited pair is refused outright. A restricted pair - the
    document's triangle - is permitted only with a time-boxed PACK-12
    grant and dual control, so that the combination exists for a stated
    reason and for a stated period rather than as a standing arrangement
    nobody revisits.
    """
    resolved = [_as_role(role) for role in roles]
    for index, first in enumerate(resolved):
        for second in resolved[index + 1 :]:
            if first is second:
                continue
            verdict = ROLE_COMPATIBILITY[frozenset({first, second})]
            names = f"{first.value} and {second.value}"
            if verdict is RoleCompatibility.PROHIBITED:
                raise SeparationOfDutiesRefusedError(
                    f"{names} may never be held by the same principal in one voting context"
                )
            if verdict is RoleCompatibility.RESTRICTED:
                if not grant_reference:
                    raise PrivilegedApprovalMissingError(
                        f"{names} requires a time-boxed privileged-access grant"
                    )
                if not dual_control_reference:
                    raise DualControlRequiredError(
                        f"{names} is held under dual control or not at all"
                    )


def assert_dual_control(
    capability: Capability,
    *,
    first_approver: Approver,
    second_approver: Approver,
    grant_reference: str | None = None,
) -> PrivilegedActRecord:
    """Two distinct principals, in two different roles, plus a grant.

    Distinct principals alone are not dual control. Two accounts held by
    the same office approve the way one account does, so the second
    approver must come from a different role - that is what makes the
    second signature a check rather than a formality. The grant is
    PACK-12's, unchanged: this module adds constraints to it and creates
    no second mechanism.

    Returns the evidence record on success. Nothing is written here; the
    caller records it on the stream the act belongs to.
    """
    permitted = DUAL_CONTROL_APPROVERS.get(capability)
    if permitted is None:
        raise AuthorizationMatrixIncompleteError(
            f"{capability.value} is not a declared dual-control act"
        )
    if not first_approver.principal_reference or not second_approver.principal_reference:
        raise DualControlRequiredError(f"{capability.value} requires two named approvers")
    if first_approver.principal_reference == second_approver.principal_reference:
        raise DualControlRequiredError(
            f"{capability.value} requires two distinct approvers, not one principal twice"
        )
    if first_approver.role is second_approver.role:
        raise SeparationOfDutiesRefusedError(
            f"{capability.value} requires a second approver holding a different role"
        )
    for approver in (first_approver, second_approver):
        if approver.role not in permitted:
            raise PrivilegedApprovalMissingError(
                f"{approver.role.value} may not approve {capability.value}"
            )
    if not grant_reference:
        raise PrivilegedApprovalMissingError(
            f"{capability.value} requires a time-boxed privileged-access grant"
        )
    return PrivilegedActRecord(
        capability=capability,
        first_approver=first_approver,
        second_approver=second_approver,
        grant_reference=grant_reference,
    )


def assert_grant_streams_separable(streams: Sequence[AuditStream]) -> None:
    """No break-glass grant spans the two sides. That grant is the link.

    A grant covering both groups needs no query to correlate: the
    principal holding it can read one side, read the other, and join them
    by hand.
    """
    requested = set(streams)
    if requested & IDENTITY_SIDE_STREAMS and requested & VOTING_SIDE_STREAMS:
        raise CorrelationRiskDetectedError(
            "no privileged grant may span the identity-side and voting-side audit streams"
        )


def assert_privileged_export_authorized(
    role: VotingRole | str,
    *,
    streams: Sequence[AuditStream],
    grant_reference: str | None,
) -> None:
    """`SD-16`: an export grant and a raw participation read never combine.

    A principal who can read a raw stream and also export a bundle can
    publish an aggregate that it alone knows how to decompose, and the
    disclosure control the bundle applies is then applied to nothing.
    """
    resolved = _as_role(role)
    assert_capability_permitted(resolved, Capability.PRIVILEGED_EXPORT)
    if not grant_reference:
        raise PrivilegedApprovalMissingError("an export runs under a time-boxed grant")
    held = ROLE_CAPABILITIES[resolved]
    overlapping = sorted(capability.value for capability in held & RAW_PARTICIPATION_READS)
    if overlapping:
        raise EvidenceBundleScopeRefusedError(
            f"{resolved.value} holds an export grant together with: " + ", ".join(overlapping)
        )
    requested = set(streams)
    if requested & IDENTITY_SIDE_STREAMS and requested & VOTING_SIDE_STREAMS:
        raise EvidenceBundleScopeRefusedError(
            "an export may not name streams from both sides of the boundary"
        )


# ---------------------------------------------------------------------------
# Import-time completeness
# ---------------------------------------------------------------------------


def assert_matrix_is_complete() -> None:
    """Run every structural rule over the shipped matrix, at import time.

    A role added to `VotingRole` without an entry in `ROLE_CAPABILITIES`
    would otherwise be a role with no capabilities and no constraints,
    discovered when somebody is refused something they should have had -
    or, worse, when nobody is refused anything. Failing here means the
    service does not start, which is the only failure mode that cannot be
    deployed past.
    """
    missing = sorted(role.value for role in VotingRole if role not in ROLE_CAPABILITIES)
    if missing:
        raise AuthorizationMatrixIncompleteError(
            "roles declared with no capability entry: " + ", ".join(missing)
        )
    unknown = sorted(str(role) for role in ROLE_CAPABILITIES if not isinstance(role, VotingRole))
    if unknown:
        raise AuthorizationMatrixIncompleteError(
            "capability entries for roles outside the matrix: " + ", ".join(unknown)
        )
    missing_identifiers = sorted(role.value for role in VotingRole if role not in ROLE_IDENTIFIERS)
    if missing_identifiers:
        raise AuthorizationMatrixIncompleteError(
            "roles with no matrix identifier: " + ", ".join(missing_identifiers)
        )
    for role, held in ROLE_CAPABILITIES.items():
        stray = sorted(str(item) for item in held if not isinstance(item, Capability))
        if stray:
            raise AuthorizationMatrixIncompleteError(
                f"{role.value} holds undeclared capabilities: " + ", ".join(stray)
            )
    for capability, approvers in DUAL_CONTROL_APPROVERS.items():
        if len(approvers) < 2:
            raise AuthorizationMatrixIncompleteError(
                f"{capability.value} names fewer than two possible approver roles, "
                "so its dual control could never be satisfied"
            )
    assert_no_role_controls_eligibility_issuance_and_tally()
    assert_credential_issuer_has_no_identity_access()
    assert_eligibility_officer_has_no_credential_secret_access()
    assert_auditor_cannot_correlate()
    assert_no_role_spans_audit_stream_groups()
    assert_security_admin_is_not_system_admin()


assert_matrix_is_complete()
