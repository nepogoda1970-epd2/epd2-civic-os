"""Document Service scoped authorization and separation of duties
(PACK-11; ADR-056).

Pure, like `domain` and `versions`: no I/O, no clock, no storage. The one
concession to the outside world is `AuthorizationPort`, a `Protocol` the
application layer implements against PACK-08. That port is the **only**
way this service learns anything about authority: PACK-08 owns the
`OrganizationalAuthority` assignments themselves (who holds which
`role_code`, in which scope, effective from when), and PACK-12 will own
privileged and break-glass access. This service neither stores an
assignment nor mints one, and it never reads another service's storage.

Four rules shape everything below.

- **A role name is not an authority.** `AuthorityReference.role_code` is a
  caller-supplied string; on its own it proves nothing. Every check here
  resolves the presented authority object through
  `AuthorizationPort.resolve_active_authority`, which answers whether an
  *active, effective-dated, scope-matching* assignment exists behind it.
- **Incompatibility is checked at the moment of the act.** PACK-08
  enforces the matrix at assignment time. That is not enough on its own:
  an assignment made compatible on Monday can be incompatible on Friday
  because a second role was granted in between, and the act happens on
  Friday. `assert_authorized` therefore re-runs the matrix over the roles
  the acting actor actually holds, in that scope, now.
- **Separation of duties is per act, not per role set.** An organization
  small enough that one person holds both author and approver roles is
  not thereby allowed to have that person approve their own document.
  `assert_not_self_approval` compares the *actors* on the two acts, which
  is a different and stricter question than whether the role set is legal.
- **There is no break-glass.** See `NO_BREAK_GLASS_NOTE`. No feature flag,
  no emergency path, no "temporary" operational exception and no
  privileged-access grant may bypass any function in this module
  (FIR-INV-006: feature flags must never disable hard invariants, audit
  obligations, separation of duties or security gates).

## Institutional roles versus action-level authorities

`DocumentRole` holds the institutional roles PACK-08 assigns and this
service resolves. `DocumentAction` names the governed acts, and
`ACTION_REQUIREMENTS` maps each act to the roles that may perform it.
Nothing in `ACTION_REQUIREMENTS` grants a role: it states which resolved
role is *accepted* for an act, and an act with no entry denies rather than
defaulting open.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from enum import StrEnum
from typing import Protocol

from epd2_document_service.domain import (
    QUALIFIED_OPINION_KINDS,
    AccessProfile,
    AuthorityReference,
    DocumentKind,
    OrganizationalScopeRef,
    SensitivityClass,
)
from epd2_document_service.exceptions import (
    AuditorIndependenceViolationError,
    AuthorityRoleIncompatibleError,
    DocumentAuthorityMissingError,
    OrganizationScopeMismatchError,
    OrganizationScopeUndeterminedError,
    RestrictedAccessDeniedError,
    SelfApprovalProhibitedError,
)

# ---------------------------------------------------------------------------
# The no-break-glass rule
# ---------------------------------------------------------------------------

#: FIR-INV-006, recorded as a module constant rather than a comment so
#: that it is quotable in a review, a test and an ADR, and so that anyone
#: reading the call sites finds the rule next to them.
#:
#: Nothing in this module is conditional. There is no `force=True`, no
#: `skip_checks`, no environment switch and no privileged-caller shortcut,
#: and none may be added: separation of duties that a flag can disable is
#: separation of duties that was never in force. PACK-12 will own
#: privileged and emergency access, and a PACK-12 grant is explicitly
#: **not** an accepted path through these checks - it can make a caller
#: able to *reach* a document command, never able to *pass* one.
NO_BREAK_GLASS_NOTE: str = (
    "FIR-INV-006: no feature flag, environment switch, deployment mode, privileged-access "
    "grant or emergency path may bypass any check in this module. Separation of duties a "
    "flag can disable was never in force. Acting without an ordinary authority is possible "
    "only through a governed, reason-coded decision that leaves its own record."
)


# ---------------------------------------------------------------------------
# Roles
# ---------------------------------------------------------------------------


class DocumentRole(StrEnum):
    """The institutional roles this context resolves.

    Seven roles, not more. Every additional privileged role widens the
    platform's privileged surface, and the acts below decompose cleanly
    into these seven. `role_code` strings arriving from PACK-08 are
    resolved through `resolve_document_role`; an unrecognised code is not
    an error, it is simply not one of this context's roles, and an act
    requiring one of them will deny."""

    DOCUMENT_CUSTODIAN = "document_custodian"
    DOCUMENT_AUTHOR = "document_author"
    DOCUMENT_REVIEWER = "document_reviewer"
    DOCUMENT_APPROVER = "document_approver"
    LEGAL_REVIEWER = "legal_reviewer"
    PUBLICATION_OFFICER = "publication_officer"
    EVIDENCE_CUSTODIAN = "evidence_custodian"
    INDEPENDENT_READER = "independent_reader"


def resolve_document_role(role_code: str) -> DocumentRole | None:
    """Resolve a PACK-08 `role_code` to a `DocumentRole`, or `None`.

    `None` rather than an exception: a caller may legitimately hold roles
    belonging to other contexts, and treating "not one of ours" as an
    error would make an ordinary finance authority look like an attack."""
    try:
        return DocumentRole(role_code)
    except ValueError:
        return None


#: The incompatibility matrix. Symmetric by construction (see
#: `incompatible_roles_for`), because an asymmetric incompatibility is a
#: bug that only shows up when the roles are granted in the other order.
#:
#: Reading the entries:
#:
#: - author / reviewer / approver are mutually incompatible: the
#:   three-eyes structure is the whole point of a controlled review, and
#:   one person holding two of the three collapses it.
#: - `PUBLICATION_OFFICER` is incompatible with `DOCUMENT_AUTHOR`: an
#:   author who can publish their own text needs neither review nor
#:   approval to reach the public, which would make both optional in
#:   practice while remaining mandatory on paper.
#: - `INDEPENDENT_READER` is incompatible with everything operational.
#:   Independence is not a permission level, it is the absence of a stake
#:   in the material being read.
#: - `DOCUMENT_CUSTODIAN` is compatible with everything except
#:   `INDEPENDENT_READER`: custody is administrative (registering a
#:   document, binding retention) and separating it from authorship would
#:   make ordinary record-keeping need two people for no governance gain.
_INCOMPATIBLE_PAIRS: frozenset[frozenset[DocumentRole]] = frozenset(
    {
        frozenset({DocumentRole.DOCUMENT_AUTHOR, DocumentRole.DOCUMENT_REVIEWER}),
        frozenset({DocumentRole.DOCUMENT_AUTHOR, DocumentRole.DOCUMENT_APPROVER}),
        frozenset({DocumentRole.DOCUMENT_REVIEWER, DocumentRole.DOCUMENT_APPROVER}),
        frozenset({DocumentRole.DOCUMENT_AUTHOR, DocumentRole.LEGAL_REVIEWER}),
        frozenset({DocumentRole.DOCUMENT_AUTHOR, DocumentRole.PUBLICATION_OFFICER}),
        frozenset({DocumentRole.LEGAL_REVIEWER, DocumentRole.DOCUMENT_APPROVER}),
        frozenset({DocumentRole.INDEPENDENT_READER, DocumentRole.DOCUMENT_CUSTODIAN}),
        frozenset({DocumentRole.INDEPENDENT_READER, DocumentRole.DOCUMENT_AUTHOR}),
        frozenset({DocumentRole.INDEPENDENT_READER, DocumentRole.DOCUMENT_REVIEWER}),
        frozenset({DocumentRole.INDEPENDENT_READER, DocumentRole.DOCUMENT_APPROVER}),
        frozenset({DocumentRole.INDEPENDENT_READER, DocumentRole.LEGAL_REVIEWER}),
        frozenset({DocumentRole.INDEPENDENT_READER, DocumentRole.PUBLICATION_OFFICER}),
        frozenset({DocumentRole.INDEPENDENT_READER, DocumentRole.EVIDENCE_CUSTODIAN}),
    }
)


def incompatible_roles_for(role: DocumentRole) -> frozenset[DocumentRole]:
    """Every role that may not be held together with `role` in one scope.

    Derived from `_INCOMPATIBLE_PAIRS` rather than written out per role,
    so the matrix cannot become asymmetric through an edit that updates
    one direction and forgets the other."""
    return frozenset(
        other for pair in _INCOMPATIBLE_PAIRS if role in pair for other in pair if other is not role
    )


def assert_roles_compatible(roles: Iterable[DocumentRole]) -> None:
    """Raise if the given role set contains an incompatible pair."""
    held = set(roles)
    for pair in _INCOMPATIBLE_PAIRS:
        if pair.issubset(held):
            first, second = sorted(pair, key=str)
            raise AuthorityRoleIncompatibleError(
                f"roles {first.value!r} and {second.value!r} may not be held together in one "
                "organizational scope"
            )


# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------


class DocumentAction(StrEnum):
    """The governed acts of this context.

    One entry per state-changing command in `application`, plus the two
    governed determinations ADR-053 requires PACK-11 to expose. An action
    absent from `ACTION_REQUIREMENTS` denies - which is why this enum and
    that table are maintained together and tested against each other."""

    REGISTER_DOCUMENT = "register_document"
    RECORD_VERSION = "record_version"
    SUBMIT_FOR_REVIEW = "submit_for_review"
    RECORD_REVIEW = "record_review"
    RECORD_LEGAL_REVIEW = "record_legal_review"
    APPROVE_VERSION = "approve_version"
    RETURN_FOR_REVISION = "return_for_revision"
    AUTHORIZE_PUBLICATION = "authorize_publication"
    PUBLISH_VERSION = "publish_version"
    ISSUE_PUBLICATION_RENDITION = "issue_publication_rendition"
    SUPERSEDE_VERSION = "supersede_version"
    REVOKE_VERSION = "revoke_version"
    BIND_RETENTION = "bind_retention"
    RECORD_LEGAL_HOLD = "record_legal_hold"
    AUTHORIZE_DISPOSITION = "authorize_disposition"
    REGISTER_EVIDENCE = "register_evidence"
    TRANSFER_CUSTODY = "transfer_custody"
    SEAL_EVIDENCE_BUNDLE = "seal_evidence_bundle"
    DETERMINE_SIGNATURE_STATUS = "determine_signature_status"
    DETERMINE_ADMISSIBILITY = "determine_admissibility"
    READ_RESTRICTED_DOCUMENT = "read_restricted_document"


#: Which resolved roles are accepted for each act. Frozen sets, so the
#: table cannot be mutated at runtime by a caller that got hold of it.
#:
#: **`APPROVE_VERSION` accepts only `DOCUMENT_APPROVER`.** Not the
#: custodian, not the reviewer, not "an approver or a custodian in a
#: hurry". Approval is the act that turns a proposal into a record, and
#: every widening of who may perform it is a narrowing of what approval
#: means.
ACTION_REQUIREMENTS: dict[DocumentAction, frozenset[DocumentRole]] = {
    DocumentAction.REGISTER_DOCUMENT: frozenset(
        {DocumentRole.DOCUMENT_CUSTODIAN, DocumentRole.DOCUMENT_AUTHOR}
    ),
    DocumentAction.RECORD_VERSION: frozenset(
        {DocumentRole.DOCUMENT_AUTHOR, DocumentRole.DOCUMENT_CUSTODIAN}
    ),
    DocumentAction.SUBMIT_FOR_REVIEW: frozenset(
        {DocumentRole.DOCUMENT_AUTHOR, DocumentRole.DOCUMENT_CUSTODIAN}
    ),
    DocumentAction.RECORD_REVIEW: frozenset({DocumentRole.DOCUMENT_REVIEWER}),
    DocumentAction.RECORD_LEGAL_REVIEW: frozenset({DocumentRole.LEGAL_REVIEWER}),
    DocumentAction.APPROVE_VERSION: frozenset({DocumentRole.DOCUMENT_APPROVER}),
    DocumentAction.RETURN_FOR_REVISION: frozenset(
        {
            DocumentRole.DOCUMENT_REVIEWER,
            DocumentRole.LEGAL_REVIEWER,
            DocumentRole.DOCUMENT_APPROVER,
        }
    ),
    DocumentAction.AUTHORIZE_PUBLICATION: frozenset({DocumentRole.PUBLICATION_OFFICER}),
    DocumentAction.PUBLISH_VERSION: frozenset({DocumentRole.PUBLICATION_OFFICER}),
    DocumentAction.ISSUE_PUBLICATION_RENDITION: frozenset({DocumentRole.PUBLICATION_OFFICER}),
    DocumentAction.SUPERSEDE_VERSION: frozenset(
        {DocumentRole.DOCUMENT_APPROVER, DocumentRole.DOCUMENT_CUSTODIAN}
    ),
    DocumentAction.REVOKE_VERSION: frozenset({DocumentRole.DOCUMENT_APPROVER}),
    DocumentAction.BIND_RETENTION: frozenset({DocumentRole.DOCUMENT_CUSTODIAN}),
    DocumentAction.RECORD_LEGAL_HOLD: frozenset({DocumentRole.DOCUMENT_CUSTODIAN}),
    DocumentAction.AUTHORIZE_DISPOSITION: frozenset({DocumentRole.DOCUMENT_CUSTODIAN}),
    DocumentAction.REGISTER_EVIDENCE: frozenset({DocumentRole.EVIDENCE_CUSTODIAN}),
    DocumentAction.TRANSFER_CUSTODY: frozenset({DocumentRole.EVIDENCE_CUSTODIAN}),
    DocumentAction.SEAL_EVIDENCE_BUNDLE: frozenset({DocumentRole.EVIDENCE_CUSTODIAN}),
    DocumentAction.DETERMINE_SIGNATURE_STATUS: frozenset(
        {DocumentRole.DOCUMENT_CUSTODIAN, DocumentRole.EVIDENCE_CUSTODIAN}
    ),
    DocumentAction.DETERMINE_ADMISSIBILITY: frozenset({DocumentRole.LEGAL_REVIEWER}),
    DocumentAction.READ_RESTRICTED_DOCUMENT: frozenset(
        {
            DocumentRole.DOCUMENT_CUSTODIAN,
            DocumentRole.DOCUMENT_REVIEWER,
            DocumentRole.LEGAL_REVIEWER,
            DocumentRole.DOCUMENT_APPROVER,
            DocumentRole.EVIDENCE_CUSTODIAN,
            DocumentRole.INDEPENDENT_READER,
        }
    ),
}


# ---------------------------------------------------------------------------
# The port
# ---------------------------------------------------------------------------


class AuthorizationPort(Protocol):
    """The only way this service learns anything about authority.

    Implemented by the application layer against PACK-08's
    `organization-service`. Two methods, deliberately:

    - `resolve_active_authority` answers "is there a live, effective-dated,
      scope-matching assignment behind this presented authority object?";
    - `held_roles` answers "which of this context's roles does this actor
      actually hold in this scope?", which is what makes the
      incompatibility re-check at act time possible.

    A port with a single "is this allowed?" method would have hidden the
    second question inside PACK-08 and left this service unable to enforce
    FIR-INV-006 for itself."""

    def resolve_active_authority(
        self, authority: AuthorityReference, scope: OrganizationalScopeRef
    ) -> bool:
        """True if an active, effective-dated assignment exists behind
        `authority` in exactly `scope`."""
        ...

    def held_roles(
        self, actor_reference: str, scope: OrganizationalScopeRef
    ) -> tuple[DocumentRole, ...]:
        """The document-context roles `actor_reference` holds in `scope`."""
        ...


# ---------------------------------------------------------------------------
# The assertions
# ---------------------------------------------------------------------------


def _partition_by_scope(
    authorities: Sequence[AuthorityReference], scope: OrganizationalScopeRef
) -> list[AuthorityReference]:
    """The presented authorities that claim exactly `scope`.

    Scope is never inherited into authority here: a Bund-level assignment
    does not carry into a Kreis, and asking PACK-08 to widen it would put
    the six cross-scope access modes behind an implicit default. A caller
    that genuinely holds cross-scope authority presents the authority for
    the scope it is acting in."""
    return [a for a in authorities if a.scope.organization_id == scope.organization_id]


def assert_authorized(
    action: DocumentAction,
    authorities: Sequence[AuthorityReference],
    scope: OrganizationalScopeRef,
    *,
    port: AuthorizationPort,
) -> AuthorityReference:
    """Resolve and return the authority that may perform `action`.

    The order matters and is the guarantee:

    1. the action must have a requirement entry - an unlisted action
       denies rather than defaulting open;
    2. only authorities presented for exactly this scope are considered;
    3. each candidate's `role_code` must resolve to an accepted
       `DocumentRole`;
    4. the presented authority object must resolve to a live assignment
       through the port - this is where a fabricated `role_code` fails;
    5. the roles the actor *actually* holds in this scope are re-checked
       against the incompatibility matrix, including the accepted role.

    Step 5 is the one that catches the case PACK-08's assignment-time
    check cannot: a second, conflicting role granted after the first."""
    accepted = ACTION_REQUIREMENTS.get(action)
    if accepted is None:
        raise DocumentAuthorityMissingError(
            f"{action.value!r} has no assigned authority requirement - default deny"
        )

    in_scope = _partition_by_scope(authorities, scope)
    if not in_scope:
        raise DocumentAuthorityMissingError(
            f"{action.value}: no authority was presented for this organizational scope"
        )

    for candidate in in_scope:
        role = resolve_document_role(candidate.role_code)
        if role is None or role not in accepted:
            continue
        if not port.resolve_active_authority(candidate, scope):
            continue
        actor = candidate.actor_reference.strip()
        if actor:
            assert_roles_compatible((*port.held_roles(actor, scope), role))
        return candidate

    raise DocumentAuthorityMissingError(
        f"{action.value}: no active, scope-matching authority with an accepted role "
        f"({', '.join(sorted(r.value for r in accepted))}) was resolved"
    )


def assert_not_self_approval(
    acting_actor_reference: str, prior_actor_reference: str, *, action: str
) -> None:
    """Raise if the acting actor is the actor who performed the prior act.

    Compared on the opaque `actor_reference`, which resolves to nothing
    inside this service - the comparison needs only equality, never
    identity, and asking for identity would be asking for exactly the
    global person identifier FIR-INV-001 forbids.

    An empty prior reference does **not** pass silently: an act whose
    prior actor was not recorded cannot be shown to be a different person,
    and this check exists precisely to prevent "cannot be shown" from
    being read as "is"."""
    acting = acting_actor_reference.strip()
    prior = prior_actor_reference.strip()
    if not acting or not prior:
        raise SelfApprovalProhibitedError(
            f"{action}: separation of duties cannot be verified because an actor reference is "
            "missing - unverifiable separation is refused, not assumed"
        )
    if acting == prior:
        raise SelfApprovalProhibitedError(
            f"{action}: the acting actor performed the prior act on this version; the same "
            "actor may not perform both"
        )


def assert_reviewer_qualified(kind: DocumentKind, role: DocumentRole) -> None:
    """Raise unless `role` may review a document of `kind`.

    Legal and expert opinions require the qualified reviewer role: a
    general reviewer signing off a legal opinion would put a
    qualification claim on a review nobody qualified made. This is the
    structural foundation FIR-PROG-002's mandatory pre-adoption legal and
    expert review will build its adoption gate on; PACK-11 provides the
    governed shape, not the gate."""
    if kind in QUALIFIED_OPINION_KINDS and role is not DocumentRole.LEGAL_REVIEWER:
        raise DocumentAuthorityMissingError(
            f"a document of kind {kind.value!r} requires review by "
            f"{DocumentRole.LEGAL_REVIEWER.value!r}, not {role.value!r}"
        )


def assert_access_permitted(
    profile: AccessProfile | None,
    sensitivity: SensitivityClass,
    scope: OrganizationalScopeRef,
) -> AccessProfile:
    """Raise unless `profile` covers `sensitivity` in `scope`.

    A missing profile denies. It is tempting to treat "no profile
    presented" as "ordinary internal access", and that temptation is
    exactly the bug: the caller who forgot to present a profile is
    indistinguishable from the caller who has none."""
    if profile is None:
        raise RestrictedAccessDeniedError(
            "no access profile was presented - a read of governed material requires one"
        )
    if profile.scope.organization_id != scope.organization_id:
        raise OrganizationScopeMismatchError(
            "the presented access profile belongs to another organizational scope"
        )
    if not profile.permits(sensitivity):
        raise RestrictedAccessDeniedError(
            f"the presented access profile permits at most {profile.max_sensitivity.value!r}; "
            f"this material is classified {sensitivity.value!r}"
        )
    return profile


def assert_reader_independent(
    authority: AuthorityReference,
    scope: OrganizationalScopeRef,
    *,
    port: AuthorizationPort,
) -> None:
    """Raise unless an independent reader really is independent here.

    Independence is re-verified at the moment of the read and never
    assumed from the grant: a reader who acquired an operational role
    after being granted independent access is no longer independent, and
    the grant does not know that."""
    if resolve_document_role(authority.role_code) is not DocumentRole.INDEPENDENT_READER:
        return
    actor = authority.actor_reference.strip()
    if not actor:
        raise AuditorIndependenceViolationError(
            "an independent read requires an actor reference so independence can be verified"
        )
    held = set(port.held_roles(actor, scope))
    conflicting = held & incompatible_roles_for(DocumentRole.INDEPENDENT_READER)
    if conflicting:
        raise AuditorIndependenceViolationError(
            "the reader is not independent in this scope: also holds "
            + ", ".join(sorted(r.value for r in conflicting))
        )


def assert_scope_determined(scope: OrganizationalScopeRef | None) -> OrganizationalScopeRef:
    """Return `scope`, refusing `None`. The first check of every command
    frame, before any read and any write."""
    if scope is None:
        raise OrganizationScopeUndeterminedError(
            "organizational scope is undetermined - default deny"
        )
    return scope
