# Finance separation of duties

Status: implemented for CLAUDE-PACK-10. This document describes
`services/finance-service/src/epd2_finance_service/authorization.py` and
the per-object checks that live with the aggregates: the six
institutional roles, the four action-level authorities, the canon 19f.14
incompatibility matrix, the action-requirements table, the checks a role
table cannot express, the conflict-declaration rule, the separate
party-handle resolution authority, and why a role name is never proof.
The decision record is
`docs/adr/ADR-052-finance-authority-separation-and-independent-audit.md`.

`authorization.py` is pure. Its one concession to the outside world is
`AuthorizationPort`, a `Protocol` the application layer implements
against PACK-08. That port is the only way this service learns anything
about authority: PACK-08 owns the assignments, their effective dating
and their revocation history; PACK-12 owns privileged and emergency
access. Finance neither stores an assignment nor mints one, and it never
reads another service's storage (`ФИН-44`).

## 1. Six institutional roles

`FinanceRole` is a closed enum. Canon 19f.14 adds four finance roles to
PACK-08's open `role_code` list and confirms a fifth that 19e.15/19e.16
already named; the sixth is the pre-existing organizational role the
matrix makes incompatible with `finance_administrator`.

| Role                           | What it may do                                             |
| ------------------------------ | ---------------------------------------------------------- |
| `finance_administrator`        | Accounts, periods, register, contributions, preparation    |
| `payment_authorizer`           | Authorise a payment                                        |
| `payment_executor`             | Execute an authorised payment, return a contribution       |
| `report_signatory`             | Legally responsible signing of a report                    |
| `finance_auditor`              | Conclude an independent audit — and nothing else           |
| `organizational_administrator` | Second-authority governance points, never an ordinary post |

The enum is closed on purpose. PACK-08's `role_code` list is open, but
the roles finance acts on are exactly these six, and
`resolve_finance_role` returns `None` for anything else — which denies
(`ФИН-45`). None of the six is a universal administrator, none is
introduced by scope inheritance, and technical or system administration
implies no financial authority at all.

## 2. Four action-level authorities

`FinanceActionAuthority` holds the four authorities canon 19f.14 records
on the act rather than granting as roles:

```text
transaction_creator   transaction_reviewer
report_preparer       report_approver
```

They are a separate enum from `FinanceRole` and appear nowhere in
`ACTION_REQUIREMENTS`. Canon 19f.14's reason is explicit: inventing nine
privileged roles where four suffice would widen the platform's
privileged surface for no governance gain. Each is a reference to the
authority that performed one specific act, carried by that act's own
audit record with its own reason code, and each is subject to the same
incompatibility rules — a transaction creator does not approve the same
object, a report preparer does not audit their own report. Those rules
are enforced per act, in section 5.

## 3. The incompatibility matrix

`INCOMPATIBLE_ROLE_PAIRS` holds the canon 19f.14 rows that are genuinely
pairs of roles, as unordered `frozenset` pairs. Six of them:

| Role A                  | Role B                         | Why                                                                   |
| ----------------------- | ------------------------------ | --------------------------------------------------------------------- |
| `finance_auditor`       | `finance_administrator`        | An auditor who administers is auditing their own work (19e.16 rule 3) |
| `finance_auditor`       | `payment_authorizer`           | Same, for authorisation                                               |
| `finance_auditor`       | `payment_executor`             | Same, for execution                                                   |
| `finance_auditor`       | `report_signatory`             | Same, for signing                                                     |
| `payment_authorizer`    | `payment_executor`             | Authorising and executing are two acts so one person cannot pay alone |
| `finance_administrator` | `organizational_administrator` | The adopted owner decision of canon 19f.14, in one relevant scope     |

The last pair is canon 19f.14's own owner decision and it says what an
exception must look like: any operational exception for a small scope
has to be a governed, documented policy decision, never a silent
combination. Nothing in this service implements such an exception.

`incompatible_roles_for` derives each role's set from the matrix rather
than restating it, and `AUDITOR_INCOMPATIBLE_ROLES` is derived the same
way. A second, hand-maintained list would drift, and a drifted copy of a
separation-of-duties rule is the rule silently weakening.

`assert_roles_compatible` refuses any held set containing a full pair
and names both offending roles, since "incompatible" without the pair is
not actionable. It runs twice per act, deliberately: canon 19f.14
requires the matrix at assignment and again at the moment of the act.
PACK-08 does the first; `assert_authorized` does the second over
`port.held_roles(actor, scope)` plus the role being accepted, and
`application._guard` runs it a third time over the held set alone, so
the matrix stays enforced in the command frame even if a future
authorisation path stops doing it.

### The canon rows that are not role pairs

Canon 19f.14's table also lists `finance_auditor` against the report
preparer and against the report approver, the transaction creator
against the approver of the same object, and the claimant against the
reviewer, approver, authoriser or executor of their own claim. None of
these is in `INCOMPATIBLE_ROLE_PAIRS`, and their absence is the design
rather than a gap: they compare two actors on one object, not two
grants. Both acts in each row can sit inside one perfectly compatible
role set, so a role check cannot see them. They are enforced per act by
`assert_not_self_approval`, `assert_auditor_independent` and
`records.assert_not_self_acting` — section 5.

## 4. Which roles may perform which action

`ACTION_REQUIREMENTS` is a closed mapping of 40 governed actions to the
roles permitted to perform them. `assert_authorized` consults it, and an
action absent from it has no permitted role and therefore denies — so
adding a command without deciding who may run it fails closed rather
than defaulting open (`ФИН-04`, `ФИН-45`).

| Action                          | Permitted roles                                         |
| ------------------------------- | ------------------------------------------------------- |
| `open_period`                   | `finance_administrator`                                 |
| `close_period`                  | `finance_administrator`                                 |
| `request_period_reopening`      | `finance_administrator`                                 |
| `approve_period_reopening`      | `finance_administrator`, `organizational_administrator` |
| `manage_chart_of_accounts`      | `finance_administrator`                                 |
| `post_transaction`              | `finance_administrator`                                 |
| `correct_transaction`           | `finance_administrator`                                 |
| `reverse_transaction`           | `finance_administrator`                                 |
| `register_import_batch`         | `finance_administrator`                                 |
| `reclassify_transaction`        | `finance_administrator`                                 |
| `record_contribution`           | `finance_administrator`                                 |
| `assess_contribution`           | `finance_administrator`                                 |
| `accept_contribution`           | `finance_administrator`                                 |
| `return_contribution`           | `payment_executor`                                      |
| `record_sponsorship`            | `finance_administrator`                                 |
| `approve_sponsorship`           | `finance_administrator`                                 |
| `record_external_benefit`       | `finance_administrator`                                 |
| `record_expense`                | `finance_administrator`                                 |
| `approve_expense`               | `finance_administrator`                                 |
| `authorize_payment`             | `payment_authorizer`                                    |
| `execute_payment`               | `payment_executor`                                      |
| `record_obligation`             | `finance_administrator`                                 |
| `settle_obligation`             | `payment_executor`                                      |
| `record_transfer`               | `finance_administrator`                                 |
| `write_off_position`            | `finance_administrator`, `organizational_administrator` |
| `create_snapshot`               | `finance_administrator`                                 |
| `prepare_report`                | `finance_administrator`                                 |
| `submit_for_review`             | `finance_administrator`                                 |
| `record_review`                 | `finance_administrator`, `report_signatory`             |
| `approve_report`                | `report_signatory`, `organizational_administrator`      |
| `sign_report`                   | `report_signatory`                                      |
| `request_audit`                 | `finance_administrator`, `organizational_administrator` |
| `record_audit_opinion`          | `finance_auditor`                                       |
| `record_auditor_review`         | `finance_administrator`, `report_signatory`             |
| `create_report_version`         | `finance_administrator`                                 |
| `supersede_report`              | `finance_administrator`                                 |
| `record_external_submission`    | `report_signatory`                                      |
| `record_external_acceptance`    | `finance_administrator`, `report_signatory`             |
| `create_publication_projection` | `report_signatory`, `organizational_administrator`      |
| `mint_party_handle`             | `finance_administrator`                                 |

Four separations are visible in the values and are the point of the
table.

`authorize_payment` and `execute_payment` never share a role (canon
19f.10). `record_audit_opinion` is the only action a `finance_auditor`
may perform at all, because the audit contour writes into nothing it
audits (canon 19f.18 rule 3) — and `record_auditor_review`, which writes
the conclusion's reference onto the report version, is deliberately a
report-side action that excludes `finance_auditor` for exactly that
reason. Preparing, approving, signing, submitting and publishing a
report are five separate entries, so no single role walks a report from
draft to publication (`ФИН-33`). And `organizational_administrator`
appears only where a second, non-finance authority is the governance
point — approving a period reopening, approving a report, requesting an
audit, authorising a publication, approving a write-off — never on an
ordinary posting path; being hard-incompatible with
`finance_administrator` in the same scope, those entries cannot collapse
into one actor.

Two entries carry judgements worth naming. `return_contribution`
requires `payment_executor` rather than `finance_administrator`:
returning an already-received contribution moves money outward, so it is
an execution act, while the return obligation itself is decided by the
finance administrator. `register_import_batch` is listed separately from
`post_transaction` even though both currently resolve to
`finance_administrator`, so that a future policy can grant posting
without granting ingestion; collapsing them into one key would make that
future separation invisible.

Four of the forty actions have no command this round —
`submit_for_review`, `settle_obligation`, `record_transfer` and
`supersede_report`. They carry their role set and are unreachable.

### The order of refusals in `assert_authorized`

Fixed, and each step has its own code:

1. an action absent from `ACTION_REQUIREMENTS` raises
   `FINANCE_AUTHORITY_MISSING` — a command nobody assigned a role to is
   not thereby open to everyone;
2. an undeterminable scope raises `ORGANIZATION_SCOPE_UNDETERMINED`
   before anything else is read (`ФИН-04`);
3. authorities presented only for other scopes raise
   `ORGANIZATION_SCOPE_MISMATCH` — the caller holds something, just not
   here, and conflating that with "holds nothing" would lose a
   distinction the reason-code registry draws;
4. no presented authority carrying a required role, or none resolving to
   an active assignment, raises `FINANCE_AUTHORITY_MISSING`. Which of
   the two failed is deliberately not distinguished: telling a caller
   that its role was right but its assignment inactive discloses the
   assignment state of a scope it has no authority in;
5. the roles the actor really holds are re-checked against the matrix,
   raising `AUTHORITY_ROLE_INCOMPATIBLE`.

An authority carrying no `actor_reference` skips only step 5, and
skipping it clears nothing — it means finance had no actor to ask about.

## 5. What a role table cannot express

Four per-object checks carry the canon rows that compare actors rather
than grants. All of them compare opaque actor references, the only
actor-level value this service holds, and all of them are blind to role.

Creator against approver. `authorization.assert_not_self_approval`
raises `CONFLICT_REVIEW_SELF_APPROVAL_PROHIBITED` when the acting actor
is the actor whose earlier act is being reviewed, approved, authorised
or executed. `FinanceReportVersion.approve` runs it against every actor
that appears in the version's own history under `prepared`; `sign` runs
it against the recorded approver, because signing one's own approval
collapses two of the six distinguishable acts into one. Either reference
being blank is neither a pass nor a failure: it is the absence of the
fact the function decides on, so the check abstains and the caller's
other rules still apply.

Claimant against reviewer, approver, authoriser and executor.
`records.assert_not_self_acting` compares the claimant's purpose-scoped
handle reference with the acting authority's `actor_reference`. Where
both are present and equal, the act is refused whichever role the
authority names: holding `payment_authorizer` does not make self-payment
lawful.

Authorizer against executor of the same payment.
`PaymentAuthorization.execute` refuses execution by the authorising
actor — the role pair in section 3 handles the case of one person
holding both grants, and this handles the case of one person executing
the specific authorisation they issued.

Auditor against preparer and approver.
`assert_auditor_independent` takes the operational actor references and
raises `FINANCE_AUDITOR_INDEPENDENCE_VIOLATION` when the auditor is
among them. `FinanceReportVersion.operational_actor_references` derives
that set from the version's own append-only history — the actors that
prepared, reviewed, approved, signed, submitted and published it —
rather than from role grants, because these canon rows are action-level
and invisible to any role check. The function also checks scope first
(a foreign auditor keeps the scope refusal rather than the independence
one), checks that the role code is `finance_auditor`, and, where a port
is given, checks the roles the auditor actually holds against
`AUDITOR_INCOMPATIBLE_ROLES`. Called without a port it runs three of
four checks; that is finance answering with what it can see, and it is
never a clearance.

Canon 19f.18 requires independence at opening, at every finding and at
conclusion, not once at opening. `AuditEngagement.open`,
`record_finding` and `conclude` each call the function, which is why it
is a free function taking everything it needs rather than a property
latched onto the engagement. `conclude` additionally refuses a
concluding authority other than the engagement's own auditor, refuses a
second conclusion (a changed opinion is a new engagement), and refuses
fewer findings than the policy-supplied `minimum_findings`.

Period reopening. `ledger.assert_reopening_dual_control` compares both
`authority_id` and `actor_reference`, because two distinct assignments
held by one person is not dual control.

Write-off. `records.assert_write_off_authorized` refuses a bare state
change: a write-off names an authority and a recorded reason, and where
an open PACK-09 case still concerns the position it must cite that case
too, so a write-off cannot quietly close something a case is still about
(`ФИН-22`). On top of that, `write_off_financial_obligation` requires a
second `approving_authority` that is neither the same assignment nor the
same actor as the one acting, refusing with
`FINANCE_WRITE_OFF_NOT_AUTHORIZED` in both cases. Canon 19f.11 makes
that dual control a policy threshold; the command applies it
unconditionally, which is stricter and never softer. The command
deliberately passes no `prior_actor_references` to `_guard`, because the
frame's generic self-approval check would answer with
`CONFLICT_REVIEW_SELF_APPROVAL_PROHIBITED` and mask the more specific
code. A table of role sets cannot express "two different actors", which
is why this lives in the command.

## 6. Conflict declaration fails closed

`assert_conflict_declared` produces two refusals, and the first is the
important one. `None` and `undeclared` are the same answer — unknown —
and both raise `CONFLICT_OF_INTEREST_UNDECLARED`, because silence is not
"no conflict"; treating it as one is precisely how an undeclared
conflict becomes an approved act (`ФИН-32`). A declared blocking
conflict raises `CONFLICT_OF_INTEREST_BLOCKING`, a different fact with a
different code: the state was declared, and it refuses.
`declared_non_blocking` and `none` both pass and both stay recorded on
the act, so a later reviewer sees which of the two it was.

`application._guard` applies this to every command in the module, which
is stricter than canon 19f.13's "protected actions" and never softer:
there is no finance command a caller can run without declaring a
conflict state.

## 7. Party-handle resolution is not a `FinanceRole`

Resolving a `FinancePartyHandle` back to a party is the one act that
joins finance records to a legal identity, and canon 19f.15 requires a
separate, explicitly granted authority for it.

`PARTY_HANDLE_RESOLUTION_ROLE_CODE` is the bare string
`finance_party_handle_resolver`. It is deliberately not a `FinanceRole`
member, so `resolve_finance_role` returns `None` for it and no
role-based path can satisfy it by accident, and it is deliberately
absent from `ACTION_REQUIREMENTS`, so it cannot be granted by holding a
finance role.

`application._resolve_party_handle_authority` checks three things — the
exact role code, this exact scope, and an active assignment behind the
presented object — and answers every failure with the single code canon
19f.15 assigns, `FINANCE_PARTY_HANDLE_RESOLUTION_DENIED`, without
distinguishing which condition failed. The bar is narrower than
`assert_authorized`'s, not wider. `_guard` accepts a pre-resolved
authority only from the command named `resolve_party_handle` and refuses
it from every other, so the parameter cannot become a general way past
the action table.

The resolution itself emits `finance_party_handle.resolved` — who, what,
under which authority, for which purpose — and never the resolved value.
The audit `before_hash` and `after_hash` are the same access snapshot,
because a resolution changes no state, and neither carries the resolved
value.

## 8. A role name is never proof, and no flag switches this off

`AuthorityReference.role_code` is a caller-supplied string. On its own it
proves nothing (`ФИН-45`). `assert_authorized` takes `port` as a
required keyword-only argument and there is deliberately no overload
that decides on the presented object alone: every accepted authority has
been resolved through `AuthorizationPort.resolve_active_authority` to an
active, effective-dated assignment in this exact scope. A revoked,
expired, not-yet-effective, differently-scoped or entirely invented
authority answers `False`. The function returns the resolved authority
rather than `None`, so the caller records which authority acted instead
of re-deriving it.

`NO_BREAK_GLASS_NOTE` is a module constant rather than a comment, so
that the rule is quotable in a review, a test and an ADR, and so that
anyone reading the call sites finds it next to them. Nothing in
`authorization.py` is conditional: there is no `force=True`, no
`skip_checks`, no environment switch and no privileged-caller shortcut,
and none may be added, because separation of duties that a flag can
disable is separation of duties that was never in force (`ФИН-42`).

PACK-12 owns privileged and emergency access, and a PACK-12 grant is
explicitly not an accepted path through these checks: it can make a
caller able to reach a finance command, never able to pass one. An
adapter that returned `True` from `resolve_active_authority` because the
caller held an emergency grant, a support session or an operational
override would be implementing exactly the bypass `ФИН-42` forbids. The
governed way to act without an ordinary authority is a governed,
reason-coded, dual-controlled decision that leaves its own record — a
period reopening, a policy exception, a superseding report version —
never a silent bypass.
