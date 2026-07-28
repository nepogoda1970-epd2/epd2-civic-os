"""Finance Service separation of duties - institutional roles, the
incompatibility matrix, the action-authority requirements and the
independence checks (PACK-10 sections 4.10 and 8.2.19; canon 0.8.0
sections 19f.14 and 19f.18).

Pure, like `ledger` and `records`: no I/O, no clock, no storage. The one
concession to the outside world is `AuthorizationPort`, a `Protocol` the
application layer implements against PACK-08. That port is the **only**
way this service learns anything about authority: PACK-08 owns the
`OrganizationalAuthority` assignments themselves (who holds which
`role_code`, in which scope, effective from when), and PACK-12 owns
privileged and emergency access. Finance neither stores an assignment
nor mints one, and it never reads another service's storage directly
(`ФИН-44`).

Four rules shape everything below:

- **A role name is not an authority.** `AuthorityReference.role_code` is
  a caller-supplied string; on its own it proves nothing. Every check
  here resolves the presented authority object through
  `AuthorizationPort.resolve_active_authority`, which answers whether an
  *active, effective-dated, scope-matching* assignment exists behind it
  (`ФИН-45`, canon 19f.14).
- **Incompatibility is checked twice.** Canon 19f.14 requires the matrix
  to be enforced at assignment *and re-checked at the moment of the
  act*. PACK-08 does the first; `assert_authorized` does the second, by
  asking the port which roles the acting actor actually holds in that
  scope and running `assert_roles_compatible` over them (`ФИН-30`).
- **Scope is never inherited into authority.** Every authority is bound
  to exactly one `OrganizationalScope`; a global scope implies no
  finance administration, and an undeterminable scope denies rather than
  defaulting (`ФИН-03`, `ФИН-04`, canon 19f.14).
- **There is no break-glass.** See `NO_BREAK_GLASS_NOTE`. No feature
  flag, no emergency path, no "temporary" operational exception and no
  privileged-access grant may bypass any function in this module
  (`ФИН-42`). A path that needs to act without one of these checks is
  not an emergency path; it is an unauthorised act with a nicer name.

**Institutional roles versus action-level authorities.** Canon 19f.14
enumerates five finance institutional roles and confirms a sixth,
pre-existing organizational one; it then names four *action-level*
authorities - transaction creator, transaction reviewer, report
preparer, report approver - which are recorded **on the act** and
deliberately do **not** become institutional roles, because inventing
nine privileged roles where four suffice would widen the platform's
privileged surface for no governance gain. `FinanceRole` holds the
former; `FinanceActionAuthority` holds the latter, and nothing in
`ACTION_REQUIREMENTS` grants one of them.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from enum import StrEnum
from typing import Protocol

from epd2_finance_service.domain import (
    AuthorityReference,
    ConflictDeclaration,
    OrganizationalScopeRef,
)
from epd2_finance_service.exceptions import (
    AuditorIndependenceViolationError,
    AuthorityRoleIncompatibleError,
    ConflictOfInterestBlockingError,
    ConflictOfInterestUndeclaredError,
    FinanceAuthorityMissingError,
    OrganizationScopeMismatchError,
    OrganizationScopeUndeterminedError,
    SelfApprovalProhibitedError,
)

# ---------------------------------------------------------------------------
# The no-break-glass rule
# ---------------------------------------------------------------------------

#: Canon `ФИН-42`: "feature flags do not switch off hard financial
#: rules". Recorded as a module constant rather than a comment so that it
#: is quotable in a review, a test and an ADR, and so that anyone reading
#: the call sites finds the rule next to them.
#:
#: Nothing in this module is conditional. There is no `force=True`, no
#: `skip_checks`, no environment switch and no privileged-caller
#: shortcut, and none may be added: separation of duties that a flag can
#: disable is separation of duties that was never in force. PACK-12 owns
#: privileged and emergency access, and a PACK-12 grant is explicitly
#: **not** an accepted path through these checks - it can make a caller
#: able to *reach* a finance command, never able to *pass* one. The
#: governed way to act without an ordinary authority is a governed,
#: reason-coded, dual-controlled decision that leaves a record (a period
#: reopening, a policy exception, a superseding report version), never a
#: silent bypass.
NO_BREAK_GLASS_NOTE: str = (
    "FIN-42: no feature flag, environment switch, deployment mode, privileged-access "
    "grant or emergency path may bypass any check in this module. Separation of duties "
    "a flag can disable was never in force. Acting without an ordinary authority is "
    "possible only through a governed, reason-coded, dual-controlled decision that "
    "leaves its own record."
)


# ---------------------------------------------------------------------------
# Institutional roles and action-level authorities
# ---------------------------------------------------------------------------


class FinanceRole(StrEnum):
    """The institutional roles this context resolves (canon 19f.14).

    Five of these are finance's own - four added by canon 0.8.0 plus
    `finance_auditor`, which 19e.15/19e.16 already named - and
    `organizational_administrator` is the pre-existing PACK-08 role the
    matrix below makes incompatible with `finance_administrator`. The
    enum is closed on purpose: `role_code` is an open list in PACK-08,
    but the roles *finance* acts on are exactly these, and an unknown
    code resolves to no role and therefore to a denial (`ФИН-45`).

    None of these is a universal administrator, and none is introduced
    by scope inheritance: technical or system administration never
    implies a financial authority (canon 19f.14)."""

    FINANCE_ADMINISTRATOR = "finance_administrator"
    PAYMENT_AUTHORIZER = "payment_authorizer"
    PAYMENT_EXECUTOR = "payment_executor"
    REPORT_SIGNATORY = "report_signatory"
    FINANCE_AUDITOR = "finance_auditor"
    ORGANIZATIONAL_ADMINISTRATOR = "organizational_administrator"


class FinanceActionAuthority(StrEnum):
    """The four action-level authorities recorded **on an act** (canon
    19f.14).

    Deliberately a separate enum from `FinanceRole`, and deliberately
    absent from `ACTION_REQUIREMENTS`: these are never granted as
    institutional roles. Each is a reference to the authority that
    performed one specific act, carried by that act's own audit record
    with its own reason code, and each is subject to the same
    incompatibility rules - a transaction creator does not approve the
    same object, and a report preparer does not audit their own report
    (canon 19f.14, `ФИН-30`, `ФИН-31`).

    The distinction is what keeps the privileged surface at four
    institutional finance roles instead of nine."""

    TRANSACTION_CREATOR = "transaction_creator"
    TRANSACTION_REVIEWER = "transaction_reviewer"
    REPORT_PREPARER = "report_preparer"
    REPORT_APPROVER = "report_approver"


def resolve_finance_role(role_code: str) -> FinanceRole | None:
    """Map a caller-supplied `role_code` onto a known institutional role,
    or `None`.

    Parsing, never proof: knowing that a string spells
    `payment_authorizer` says nothing about whether an active assignment
    exists behind it, which is what `AuthorizationPort` answers
    (`ФИН-45`). An unknown code returns `None` and therefore denies -
    PACK-08's `role_code` list is open, and a role finance does not model
    is a role finance does not act on."""
    try:
        return FinanceRole(role_code.strip())
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# The incompatibility matrix
# ---------------------------------------------------------------------------

#: The canon 19f.14 hard incompatibility matrix, as unordered pairs.
#:
#: Read directly off the canon table, stricter never softer:
#:
#: - `finance_auditor` against each of `finance_administrator`,
#:   `payment_authorizer`, `payment_executor` and `report_signatory` -
#:   independence is not a matter of degree, and an auditor who
#:   administers, authorises, executes or signs is auditing their own
#:   work (canon 19e.16 rule 3, 19f.14, 19f.18);
#: - `payment_authorizer` against `payment_executor` - authorising and
#:   executing are two acts precisely so that one person cannot complete
#:   a payment alone (`ФИН-31`, canon 19f.10);
#: - `finance_administrator` against `organizational_administrator` in
#:   one legally relevant scope - the adopted owner decision of canon
#:   19f.14. Any operational exception for a small scope must be a
#:   governed, documented policy decision, **never a silent
#:   combination**.
#:
#: The canon table also lists the *action-level* incompatibilities
#: (auditor against report preparer and report approver, transaction
#: creator against approver of the same object, claimant against
#: reviewer/approver/authoriser/executor of their own claim). Those are
#: not role pairs and are therefore not here: they are enforced per act
#: by `assert_not_self_approval`, by `assert_auditor_independent` and by
#: `records.assert_not_self_acting`, because they compare two *actors on
#: one object*, not two grants.
INCOMPATIBLE_ROLE_PAIRS: frozenset[frozenset[FinanceRole]] = frozenset(
    {
        frozenset({FinanceRole.FINANCE_AUDITOR, FinanceRole.FINANCE_ADMINISTRATOR}),
        frozenset({FinanceRole.FINANCE_AUDITOR, FinanceRole.PAYMENT_AUTHORIZER}),
        frozenset({FinanceRole.FINANCE_AUDITOR, FinanceRole.PAYMENT_EXECUTOR}),
        frozenset({FinanceRole.FINANCE_AUDITOR, FinanceRole.REPORT_SIGNATORY}),
        frozenset({FinanceRole.PAYMENT_AUTHORIZER, FinanceRole.PAYMENT_EXECUTOR}),
        frozenset({FinanceRole.FINANCE_ADMINISTRATOR, FinanceRole.ORGANIZATIONAL_ADMINISTRATOR}),
    }
)


def incompatible_roles_for(role: FinanceRole) -> frozenset[FinanceRole]:
    """Every role `role` may not be combined with, derived from the
    matrix rather than restated.

    Derivation matters: a second, hand-maintained list would drift from
    `INCOMPATIBLE_ROLE_PAIRS`, and a drifted copy of a separation-of-
    duties rule is the rule silently weakening (canon 19f.14)."""
    return frozenset(
        other
        for pair in INCOMPATIBLE_ROLE_PAIRS
        if role in pair
        for other in pair
        if other is not role
    )


#: The roles a `finance_auditor` may not also hold in the audited scope,
#: derived from the matrix for use by `assert_auditor_independent`
#: (canon 19f.18, `ФИН-29`, `ФИН-30`).
AUDITOR_INCOMPATIBLE_ROLES: frozenset[FinanceRole] = incompatible_roles_for(
    FinanceRole.FINANCE_AUDITOR
)


def assert_roles_compatible(roles: Iterable[FinanceRole]) -> None:
    """Raise unless the presented role set is a combination canon 19f.14
    permits.

    Checked at assignment by PACK-08 and **re-checked here at the moment
    of the act**, because an assignment made before an incompatible one
    was granted must not stay usable afterwards: canon 19f.14 requires
    both passes, and an ordinary role grant never overrides a hard
    incompatibility (`ФИН-30`). The failure names both offending roles,
    since "incompatible" without the pair is not actionable."""
    held = frozenset(roles)
    for pair in INCOMPATIBLE_ROLE_PAIRS:
        if pair <= held:
            first, second = sorted(str(role) for role in pair)
            raise AuthorityRoleIncompatibleError(
                f"roles {first} and {second} are hard-incompatible in one organizational scope"
            )


# ---------------------------------------------------------------------------
# Which roles may perform which governed action
# ---------------------------------------------------------------------------

#: The roles permitted to perform each governed finance action.
#:
#: A closed mapping, consulted by `assert_authorized`: an action absent
#: from it has no permitted role and therefore denies, so adding a
#: command without deciding who may run it fails closed rather than
#: defaulting open (`ФИН-04`, `ФИН-45`).
#:
#: Three separations are visible in the values and are the point of the
#: table: `authorize_payment` and `execute_payment` never share a role
#: (canon 19f.10); `record_audit_opinion` is the only action a
#: `finance_auditor` may perform at all, because the audit module writes
#: into nothing it audits (canon 19f.18); and preparing, approving,
#: submitting and publishing a report are four different entries, so no
#: single role walks a report from draft to publication (canon 19f.17,
#: spec 8.2.17).
#:
#: `organizational_administrator` appears only where a *second*,
#: non-finance authority is the governance point - approving a period
#: reopening, approving a report, requesting an audit, authorising a
#: publication - and never on an ordinary posting path; it is
#: hard-incompatible with `finance_administrator` in the same scope, so
#: those entries cannot collapse into one actor.
ACTION_REQUIREMENTS: dict[str, frozenset[FinanceRole]] = {
    # -- periods (canon 19f.5, `ФИН-10`, `ФИН-11`) ----------------------
    "open_period": frozenset({FinanceRole.FINANCE_ADMINISTRATOR}),
    "close_period": frozenset({FinanceRole.FINANCE_ADMINISTRATOR}),
    "request_period_reopening": frozenset({FinanceRole.FINANCE_ADMINISTRATOR}),
    # Dual control: the approver is a different authority, and may be the
    # organizational administrator, who cannot also be the finance
    # administrator that requested it.
    "approve_period_reopening": frozenset(
        {FinanceRole.FINANCE_ADMINISTRATOR, FinanceRole.ORGANIZATIONAL_ADMINISTRATOR}
    ),
    # -- the register (canon 19f.4, 19f.6) -----------------------------
    "manage_chart_of_accounts": frozenset({FinanceRole.FINANCE_ADMINISTRATOR}),
    "post_transaction": frozenset({FinanceRole.FINANCE_ADMINISTRATOR}),
    "correct_transaction": frozenset({FinanceRole.FINANCE_ADMINISTRATOR}),
    "reverse_transaction": frozenset({FinanceRole.FINANCE_ADMINISTRATOR}),
    # Canon 19f.6 treats ingestion as its own act: an import applies many
    # facts at once under a source provenance nobody inside the party
    # produced, and duplicate/replay detection hangs off it. It is listed
    # separately from `post_transaction` so that a future policy can grant
    # posting without granting ingestion; both currently resolve to the
    # finance administrator, and collapsing them into one key would make
    # that future separation invisible.
    "register_import_batch": frozenset({FinanceRole.FINANCE_ADMINISTRATOR}),
    "reclassify_transaction": frozenset({FinanceRole.FINANCE_ADMINISTRATOR}),
    # -- contributions and sponsorship (canon 19f.7-19f.9) -------------
    "record_contribution": frozenset({FinanceRole.FINANCE_ADMINISTRATOR}),
    "assess_contribution": frozenset({FinanceRole.FINANCE_ADMINISTRATOR}),
    "accept_contribution": frozenset({FinanceRole.FINANCE_ADMINISTRATOR}),
    # Returning an already-received contribution moves money outward, so it
    # is an execution act, not an intake act: canon 19f.7 has the return
    # *obligation* decided by the finance administrator and the return
    # itself performed by whoever may move funds (`ФИН-33`).
    "return_contribution": frozenset({FinanceRole.PAYMENT_EXECUTOR}),
    "record_sponsorship": frozenset({FinanceRole.FINANCE_ADMINISTRATOR}),
    "approve_sponsorship": frozenset({FinanceRole.FINANCE_ADMINISTRATOR}),
    # Canon 19f.9 keeps external financial benefit distinct from
    # sponsorship - it is precisely the case where no agreement was signed -
    # so it gets its own key rather than borrowing the sponsorship one.
    "record_external_benefit": frozenset({FinanceRole.FINANCE_ADMINISTRATOR}),
    # -- expenses, payments, obligations (canon 19f.10, 19f.11) --------
    "record_expense": frozenset({FinanceRole.FINANCE_ADMINISTRATOR}),
    "approve_expense": frozenset({FinanceRole.FINANCE_ADMINISTRATOR}),
    "authorize_payment": frozenset({FinanceRole.PAYMENT_AUTHORIZER}),
    "execute_payment": frozenset({FinanceRole.PAYMENT_EXECUTOR}),
    "record_obligation": frozenset({FinanceRole.FINANCE_ADMINISTRATOR}),
    "settle_obligation": frozenset({FinanceRole.PAYMENT_EXECUTOR}),
    "record_transfer": frozenset({FinanceRole.FINANCE_ADMINISTRATOR}),
    # Canon 19f.11 names a write-off authority the policy defines, and
    # `ФИН-31`'s dual control on top. Mapping it onto `record_obligation`
    # would have made recording a debt and erasing it the same privilege.
    # The second, distinct approving authority is enforced by the command,
    # not by this table - a table of role sets cannot express "two
    # different actors".
    "write_off_position": frozenset(
        {FinanceRole.FINANCE_ADMINISTRATOR, FinanceRole.ORGANIZATIONAL_ADMINISTRATOR}
    ),
    # -- reporting (canon 19f.16, 19f.17) ------------------------------
    "create_snapshot": frozenset({FinanceRole.FINANCE_ADMINISTRATOR}),
    "prepare_report": frozenset({FinanceRole.FINANCE_ADMINISTRATOR}),
    "submit_for_review": frozenset({FinanceRole.FINANCE_ADMINISTRATOR}),
    "record_review": frozenset({FinanceRole.FINANCE_ADMINISTRATOR, FinanceRole.REPORT_SIGNATORY}),
    "approve_report": frozenset(
        {FinanceRole.REPORT_SIGNATORY, FinanceRole.ORGANIZATIONAL_ADMINISTRATOR}
    ),
    # Canon 19f.17 reserves signing for the legally responsible
    # `report_signatory` alone, and `ФИН-33` makes it an act distinct from
    # approval. The organizational administrator is deliberately absent:
    # nobody signs a statutory report on the strength of an administrative
    # role.
    "sign_report": frozenset({FinanceRole.REPORT_SIGNATORY}),
    # -- audit (canon 19f.18) ------------------------------------------
    "request_audit": frozenset(
        {FinanceRole.FINANCE_ADMINISTRATOR, FinanceRole.ORGANIZATIONAL_ADMINISTRATOR}
    ),
    "record_audit_opinion": frozenset({FinanceRole.FINANCE_AUDITOR}),
    # Recording the *reference* to a concluded engagement onto the report
    # version is a report-side act, because canon 19f.18 rule 3 forbids the
    # audit contour writing into an aggregate it audits. It is separated
    # from `record_review` so that "an internal review happened" and "an
    # external conclusion exists" are not one privilege - and the
    # `finance_auditor` is absent from it for the same reason.
    "record_auditor_review": frozenset(
        {FinanceRole.FINANCE_ADMINISTRATOR, FinanceRole.REPORT_SIGNATORY}
    ),
    # -- versions, submission, publication (canon 19f.17, `ФИН-28`) ----
    "create_report_version": frozenset({FinanceRole.FINANCE_ADMINISTRATOR}),
    "supersede_report": frozenset({FinanceRole.FINANCE_ADMINISTRATOR}),
    "record_external_submission": frozenset({FinanceRole.REPORT_SIGNATORY}),
    "record_external_acceptance": frozenset(
        {FinanceRole.REPORT_SIGNATORY, FinanceRole.FINANCE_ADMINISTRATOR}
    ),
    "create_publication_projection": frozenset(
        {FinanceRole.REPORT_SIGNATORY, FinanceRole.ORGANIZATIONAL_ADMINISTRATOR}
    ),
    # -- the party reference (canon 19f.15, `ФИН-01`) -------------------
    # Minting a purpose-scoped handle is an ordinary finance-administration
    # act. **Resolving** one is not in this table at all, deliberately: it
    # requires a separate resolution authority that is not any of the six
    # institutional roles, so putting it here would make it grantable by
    # holding a finance role. The command resolves it directly and refuses
    # with `FINANCE_PARTY_HANDLE_RESOLUTION_DENIED` otherwise.
    "mint_party_handle": frozenset({FinanceRole.FINANCE_ADMINISTRATOR}),
}

#: The exact `role_code` a caller must hold to resolve a
#: `FinancePartyHandle` back to a party (canon 19f.15). Not a
#: `FinanceRole`: none of the six institutional roles carries resolution
#: authority, and modelling it as one would make the party join reachable
#: from an ordinary finance grant. Kept as a bare string so that
#: `resolve_finance_role` returns `None` for it and no role-based path can
#: ever satisfy it by accident.
PARTY_HANDLE_RESOLUTION_ROLE_CODE: str = "finance_party_handle_resolver"


# ---------------------------------------------------------------------------
# The authorization port
# ---------------------------------------------------------------------------


class AuthorizationPort(Protocol):
    """The only way finance learns about authority (canon 19f.14,
    `ФИН-44`, `ФИН-45`).

    A `Protocol`, not a class: PACK-10 defines the question, PACK-08
    answers it. **PACK-08 owns the real assignments** - the
    `OrganizationalAuthority` records, their effective dating, their
    revocation history and the assignment-time incompatibility check.
    **PACK-12 owns privileged and emergency access.** Finance stores no
    assignment, mints none, and never reads either service's storage
    directly; it asks these two questions through a published interface
    and believes the answers (`ФИН-44`).

    **Break-glass is explicitly not an accepted path.** An adapter that
    returned `True` from `resolve_active_authority` because a caller
    held an emergency grant, a support session or an operational
    override would be implementing exactly the bypass `ФИН-42` forbids -
    see `NO_BREAK_GLASS_NOTE`. The correct answer for a caller with no
    ordinary, active, scope-matching assignment is `False`, whatever
    privileged access it otherwise enjoys.

    Both methods must be *read-only and side-effect-free from finance's
    point of view* beyond emitting their own access-audit records: this
    module calls them inside pure invariant checks."""

    def resolve_active_authority(
        self, authority: AuthorityReference, scope: OrganizationalScopeRef
    ) -> bool:
        """Whether `authority` resolves to an **active, effective-dated
        assignment in `scope`**.

        The whole content of `ФИН-45`: the caller presents an authority
        object, and this answers whether there is a live grant behind
        it. A revoked, expired, not-yet-effective, differently-scoped or
        entirely invented authority answers `False`. The role *name* on
        the presented object is never sufficient and is not what is
        being resolved here."""
        ...

    def held_roles(
        self, actor_reference: str, scope: OrganizationalScopeRef
    ) -> frozenset[FinanceRole]:
        """Every finance-relevant role `actor_reference` actually holds
        in `scope`, for the act-time incompatibility re-check canon
        19f.14 requires.

        `actor_reference` is the opaque actor pointer PACK-08 puts on an
        authority assignment - never a person identifier, a membership
        id or anything resolvable to a natural person inside finance
        (`ФИН-01`, `ФИН-36`). Roles outside `FinanceRole` are omitted:
        finance asks only about what it models. An unknown actor answers
        with the empty set, which denies nothing on its own but clears
        nothing either."""
        ...


# ---------------------------------------------------------------------------
# The authorization check
# ---------------------------------------------------------------------------


def _partition_by_scope(
    authorities: Sequence[AuthorityReference], scope: OrganizationalScopeRef
) -> tuple[tuple[AuthorityReference, ...], tuple[AuthorityReference, ...]]:
    """Split presented authorities into in-scope and out-of-scope.

    Comparison is on `organization_id` alone, exactly as
    `OrganizationalScopeRef.assert_matches` does: this service never
    interprets the organizational hierarchy itself, so "a parent scope"
    is not "this scope" here, and a consolidating scope reads a lower
    one but never acts in it (canon 19f.19, `ФИН-03`)."""
    matching: list[AuthorityReference] = []
    foreign: list[AuthorityReference] = []
    for authority in authorities:
        target = matching if authority.scope.organization_id == scope.organization_id else foreign
        target.append(authority)
    return tuple(matching), tuple(foreign)


def assert_authorized(
    action: str,
    authorities: Sequence[AuthorityReference],
    scope: OrganizationalScopeRef | None,
    *,
    port: AuthorizationPort,
) -> AuthorityReference:
    """Raise unless one presented authority may perform `action` in
    `scope`, and return the authority that carried it.

    `port` is required and keyword-only on purpose. A `role_code` string
    is never proof of authority (`ФИН-45`), so there is deliberately no
    overload that decides on the presented object alone: every accepted
    authority has been resolved to an active, effective-dated assignment
    in this exact scope. Returning the resolved authority - rather than
    `None` - is what lets the caller record *which* authority acted in
    the act's history, instead of re-deriving it (`ФИН-40`).

    The order of refusals is fixed, and each is a distinct code:

    1. an action absent from `ACTION_REQUIREMENTS` denies, because a
       command nobody assigned a role to is not thereby open to everyone
       (`FinanceAuthorityMissingError`, `ФИН-04`);
    2. an undeterminable scope denies rather than defaulting
       (`OrganizationScopeUndeterminedError`, `ФИН-04`);
    3. authorities presented **only** for other scopes raise
       `OrganizationScopeMismatchError` - the caller holds something,
       just not here, and conflating that with "holds nothing" would
       lose the distinction the reason-code registry draws (`ФИН-03`);
    4. no presented authority carrying a required role, or none of them
       resolving to an active assignment, raises
       `FinanceAuthorityMissingError`. Which of the two failed is
       deliberately *not* distinguished in the message: telling a caller
       that its role was right but its assignment inactive discloses the
       assignment state of a scope it has no authority in;
    5. finally, the roles the acting actor really holds in this scope
       are re-checked against the incompatibility matrix, raising
       `AuthorityRoleIncompatibleError` - canon 19f.14's second pass. An
       authority carrying no `actor_reference` skips only this last
       step, and skipping it clears nothing: it means finance had no
       actor to ask about."""
    required = ACTION_REQUIREMENTS.get(action)
    if required is None:
        raise FinanceAuthorityMissingError(
            f"{action!r} is not a governed finance action with an assigned authority - default deny"
        )
    if scope is None:
        raise OrganizationScopeUndeterminedError(
            f"{action}: organizational scope is undetermined - default deny"
        )

    presented = tuple(authorities)
    if not presented:
        raise FinanceAuthorityMissingError(
            f"{action} requires an active finance authority; none was presented"
        )

    in_scope, foreign = _partition_by_scope(presented, scope)
    if not in_scope:
        raise OrganizationScopeMismatchError(
            f"{action}: the {len(foreign)} presented authority reference(s) belong to another "
            "organizational scope"
        )

    for authority in in_scope:
        role = resolve_finance_role(authority.role_code)
        if role is None or role not in required:
            continue
        if not port.resolve_active_authority(authority, scope):
            continue
        actor = authority.actor_reference.strip()
        if actor:
            assert_roles_compatible(port.held_roles(actor, scope) | {role})
        return authority

    permitted = ", ".join(sorted(str(role) for role in required))
    raise FinanceAuthorityMissingError(
        f"{action} requires an active, scope-matching authority for one of: {permitted}"
    )


# ---------------------------------------------------------------------------
# Self-approval
# ---------------------------------------------------------------------------


def assert_not_self_approval(
    acting_actor_reference: str, prior_actor_reference: str, *, action: str
) -> None:
    """Raise if the actor performing `action` is the actor whose earlier
    act it reviews, approves, authorises or executes (`ФИН-31`, canon
    19f.10/19f.14).

    The comparison is on opaque actor references, the only actor-level
    value finance holds, and it is deliberately blind to role: holding
    `payment_authorizer` does not make authorising one's own creation
    lawful, and holding `report_signatory` does not make signing off
    one's own preparation lawful. This is the canon table's "creator of
    the transaction against approver of the same object" row, and it is
    checked per object rather than per grant, because both acts can sit
    inside one perfectly compatible role set.

    Either reference being blank is *not* a pass and *not* a failure: it
    is the absence of the fact this function decides on, so the check
    abstains and the caller's other rules - `assert_authorized`, dual
    control, `records.assert_not_self_acting` - still apply."""
    acting = acting_actor_reference.strip()
    prior = prior_actor_reference.strip()
    if acting and prior and acting == prior:
        raise SelfApprovalProhibitedError(
            f"{action}: the acting authority may not act on its own earlier act - "
            "self-approval is prohibited"
        )


# ---------------------------------------------------------------------------
# Conflict of interest
# ---------------------------------------------------------------------------


def assert_conflict_declared(
    conflict: ConflictDeclaration | None, *, action: str = "this protected action"
) -> None:
    """Raise unless the acting authority's conflict state permits
    `action` (`ФИН-32`, canon 19f.7/19f.10).

    Two refusals, and the first is the important one. `None` and
    `undeclared` are the same answer - *unknown* - and both raise
    `ConflictOfInterestUndeclaredError`, because silence is not "no
    conflict"; treating it as one is precisely how an undeclared
    conflict becomes an approved act. A declared blocking conflict
    raises `ConflictOfInterestBlockingError` and is a different fact
    with a different code: the state was declared, and it refuses.

    `declared_non_blocking` and `none` pass, and both remain recorded on
    the act, so a later reviewer sees which of the two it was."""
    if conflict is None or conflict.is_undeclared:
        raise ConflictOfInterestUndeclaredError(
            f"{action} requires a declared conflict-of-interest state - undeclared fails closed"
        )
    if conflict.is_blocking:
        raise ConflictOfInterestBlockingError(f"a declared blocking conflict refuses {action}")


# ---------------------------------------------------------------------------
# Auditor independence
# ---------------------------------------------------------------------------


def assert_auditor_independent(
    auditor: AuthorityReference,
    operational_actor_references: Iterable[str],
    engagement_scope: OrganizationalScopeRef,
    *,
    port: AuthorizationPort | None = None,
) -> None:
    """Raise unless `auditor` is independent of the operation it audits
    (canon 19f.18, `ФИН-29`, `ФИН-30`).

    Canon 19f.18 requires this to run **at engagement opening, at every
    finding and at conclusion** - not once at opening - which is why it
    is a free function taking everything it needs rather than a property
    latched onto an engagement. `reporting.AuditEngagement` calls it at
    all three points.

    Four checks, in order:

    1. the authority must be scoped to the audited scope; a foreign
       authority raises `OrganizationScopeMismatchError` through
       `OrganizationalScopeRef.assert_matches`, the same refusal every
       other cross-scope act gets (`ФИН-03`);
    2. its `role_code` must be `finance_auditor` - the only role canon
       19f.18 permits to conclude;
    3. the auditor's own actor reference must not appear among
       `operational_actor_references`: the actors who prepared,
       reviewed, approved, authorised, executed or signed the material
       under audit. This is the canon table's "auditor against
       report preparer" and "auditor against report approver" rows, which are
       *action-level* and therefore invisible to any role check;
    4. where a `port` is given, the roles the auditor actually holds in
       that scope are checked against `AUDITOR_INCOMPATIBLE_ROLES`, so
       an auditor who is also the finance administrator there is refused
       even though each grant is individually valid (canon 19e.16 rule
       3, 19f.14).

    All four failures raise `AuditorIndependenceViolationError` except
    the scope one, which keeps its own code. Omitting `port` runs checks
    1-3 only: that is finance answering with what it can see, and it is
    never a clearance - a caller that can reach PACK-08 should pass the
    port, and `AuditEngagement` threads it through."""
    engagement_scope.assert_matches(auditor.scope)

    role = resolve_finance_role(auditor.role_code)
    if role is not FinanceRole.FINANCE_AUDITOR:
        raise AuditorIndependenceViolationError(
            f"an audit engagement requires a {FinanceRole.FINANCE_AUDITOR!s} authority, "
            f"not {auditor.role_code!r}"
        )

    actor = auditor.actor_reference.strip()
    operational = {
        reference.strip() for reference in operational_actor_references if reference.strip()
    }
    if actor and actor in operational:
        raise AuditorIndependenceViolationError(
            "the auditor acted operationally on the material under audit and is not independent "
            "of it"
        )

    if port is not None and actor:
        held = port.held_roles(actor, engagement_scope)
        conflicting = held & AUDITOR_INCOMPATIBLE_ROLES
        if conflicting:
            names = ", ".join(sorted(str(role) for role in conflicting))
            raise AuditorIndependenceViolationError(
                f"the auditor also holds {names} in the audited scope - "
                "independence fails whichever grant came first"
            )
