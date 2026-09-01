# ADR-052: Finance authority separation, incompatible roles and independent finance audit

## Status

`proposed`

## Date

2026-07-27

## Context

PACK-08 introduced `OrganizationalAuthority` (ADR-036) as the sole
vehicle for institutional, organizationally-scoped appointments, and
seeded one party-finance role early: `finance_auditor`. ADR-036's
"Non-combinable roles" section already states, as a reserved rule,
that `finance_auditor` is incompatible with "any future
finance-preparation/approval role" in the same scope — a placeholder
written before any such role existed. PACK-08 section 9.1
additionally fixed that institutional roles are added only "by
configuration plus ADR review, never silently."

PACK-10 specifies the governed party-finance domain (section 1): the
ledger, income and expenditure, donations and sponsorship, the
expense and reimbursement workflow, budgets, the Rechenschaftsbericht
lifecycle, and independent finance audit. Nine distinct functions
recur across that domain and must be kept separable so that no single
actor can create, review, authorize, execute, approve, sign or audit
the same financially consequential act unchecked: transaction
creator, transaction reviewer, finance administrator, payment
authorizer, payment executor, report preparer, report approver,
legally responsible signatory, and finance auditor (PACK-10 section
4.10, section 4.6, HI-30 through HI-34, HI-53).

`HARD-INVARIANTS-0.8.md` HI-11 (no universal administrator), HI-12
(separation of duties) and HI-13 (scoped institutional authority)
govern how far that separation may be pushed into
`OrganizationalAuthority` itself: every institutional role widens the
platform's standing privilege surface, whether or not it is ever
misused, because it becomes a role someone can hold, be appointed to
and be checked against indefinitely.

## Problem

Which of the nine functions must become new institutional `role_code`
values on `OrganizationalAuthority`, and which are sufficiently
separated by recording the acting authority on the action itself?
Getting this wrong in either direction is a concrete failure: too
many institutional roles silently expands the privilege surface HI-11
exists to bound; too few makes legally required standing appointments
— a party's treasurer, its legally responsible signatory —
unrepresentable as anything but an ad hoc claim on a single
transaction, which is not how German party law expects those offices
to work.

A second, narrower problem is closing ADR-036's own reservation: that
ADR fixed that `finance_auditor` is incompatible with "any future
finance-preparation/approval role" without naming one, because none
existed yet. PACK-10 is the round in which finance-preparation and
finance-approval roles are first specified, so this ADR must state,
by name, which roles fill that reservation.

A third problem is independence itself: an `AuditEngagement` that can
write into the very ledger, contribution or report aggregates it
audits, or whose independence is checked once at opening and never
again, produces a conclusion that cannot be trusted regardless of how
its incompatibility rules read on paper.

## Considered options

- **Option A — institutional.** All nine functions become `role_code`
  values on `OrganizationalAuthority`.
- **Option B — action-level.** None of the nine functions become
  institutional roles; every separation is enforced entirely by
  recording distinct authority references on the acts themselves.
- **Option C — mixed (chosen).** Exactly four of the nine functions
  become new institutional roles; the remaining five are action-level
  separations recorded on the action, and one of the nine
  (`finance_auditor`) is already institutional from PACK-08 and is
  left unchanged.

## Decision

**Option C.** Four new institutional roles are added to
`OrganizationalAuthority`'s `role_code` set: `finance_administrator`,
`payment_authorizer`, `payment_executor`, `report_signatory`.
`finance_auditor` remains the institutional role PACK-08 already
defines, unchanged by this ADR. The remaining four functions stay
action-level: transaction creator, transaction reviewer, report
preparer, report approver.

### Why four, not nine, not zero

Option A (all nine institutional) was rejected because most of these
functions are properties of a single act, not standing offices: a
"transaction creator" is whoever created this transaction, not a
person appointed in advance to create transactions in general; the
same is true of a reviewer, a preparer, and an approver of a given
report version. Turning every one of them into a standing,
effective-dated, revocable appointment would multiply
`OrganizationalAuthority` records for roles nobody is actually
"appointed" to in the institutional sense, and would silently expand
the platform's privilege surface for no separation benefit beyond
what recording the actor's authority reference on the act already
gives.

Option B (zero institutional) was rejected because two of the nine
functions genuinely are standing offices under German party law and
practice: a treasurer-equivalent finance administrator and a legally
responsible signatory are appointed for a period, hold their office
independently of any single transaction, and are the offices a
report, an auditor or a regulator needs to be able to name without
pointing at one act. Payment authorization and execution are added to
that set for the same reason payment separation is a named hard
invariant (HI-32, HI-48): a payment authority is exercised repeatedly
across many payables, not invented per payment, and its
incompatibility with execution only has force if both sides resolve
to a standing, checkable appointment rather than an unverifiable
claim recorded next to the payment itself.

The nine functions, and the institutional/action-level decision for
each:

| Function                      | Institutional `role_code` (this ADR)                | Basis                                                                                   |
| ----------------------------- | --------------------------------------------------- | --------------------------------------------------------------------------------------- |
| Transaction creator           | No — action-level                                   | Authority reference recorded on the `FinancialTransaction`/`JournalEntry` creation act  |
| Transaction reviewer          | No — action-level                                   | Authority reference recorded on the review act                                          |
| Finance administrator         | Yes — new `finance_administrator`                   | Standing office; account activation, period open/close, snapshot freeze                 |
| Payment authorizer            | Yes — new `payment_authorizer`                      | Standing office; authorizes `PaymentAuthorization` (HI-32, HI-48)                       |
| Payment executor              | Yes — new `payment_executor`                        | Standing office; executes an authorized payment, distinct from the authorizer           |
| Report preparer               | No — action-level                                   | Authority reference recorded on `finance_report.prepared`                               |
| Report approver               | No — action-level                                   | Authority reference recorded on `finance_report.approved`                               |
| Legally responsible signatory | Yes — new `report_signatory`                        | Standing office; sign-off is a legally consequential act distinct from approval (HI-34) |
| Finance auditor               | Already institutional (PACK-08, ADR-036); unchanged | Pre-existing role; incompatibility set extended by this ADR, not the role itself        |

### Every new institutional role's shape

Each of the four new roles is added under PACK-08 section 9.1's rule
that roles are added "by configuration plus ADR review, never
silently" — this ADR is that review. Every one of the four:

- is **justified** against a named function this section already
  states, not introduced speculatively;
- is **scoped to exactly one** `OrganizationalScope` — never "all
  scopes." A `finance_administrator` for one `OrganizationalUnit` is
  not automatically a `finance_administrator` for its parent, sibling
  or child scope; that would recreate the universal administrator
  HI-11 forbids under a finance-specific name;
- is **effective-dated** with `valid_from`/`valid_until`, per
  ADR-036's role lifecycle invariants;
- is **revocable only with a `revocation_reason_reference`** — a
  revocation without a reason reference cannot be constructed,
  mirroring the reason-coded-refusal convention (HI-43);
- **carries an explicit `incompatibilities` set**, evaluated at
  assignment and re-evaluated whenever the assignment is used to
  authorize an action, not only once at grant time.

No globally privileged role is introduced by this ADR: none of the
four carries a scope value of "all," none is assumed to also carry
`grants_data_access`, and none is treated as senior to, or a superset
of, any other institutional role in the platform.

### Filling ADR-036's reservation

ADR-036's "Non-combinable roles" section reserved, verbatim:
"`finance_auditor` × any future finance-preparation/approval role —
incompatible, in the same scope (rule reserved now; roles do not yet
exist)." This ADR is what fills that reservation. The
finance-preparation/approval roles named there are, specifically:
`finance_administrator`, `payment_authorizer`, `payment_executor`,
`report_signatory`, and the action-level report-preparer and
report-approver separations. All are made incompatible with
`finance_auditor` in the same scope below. PACK-08 section 9.3 rule 3
and canon 19e.16 ("a finance auditor may not simultaneously be
finance administrator in the same legally relevant scope") are
preserved verbatim, not narrowed, by this extension — restated as
HI-31.

### Proposed incompatibility matrix extension

| Pair                                                          | Scope of incompatibility         | Reason code                                | Status                                                       |
| ------------------------------------------------------------- | -------------------------------- | ------------------------------------------ | ------------------------------------------------------------ |
| `finance_auditor` × `finance_administrator`                   | same organization/legal scope    | `AUTHORITY_ROLE_INCOMPATIBLE`              | Preserved verbatim (PACK-08 9.3 rule 3, canon 19e.16, HI-31) |
| `finance_auditor` × `payment_authorizer`                      | same scope                       | `AUTHORITY_ROLE_INCOMPATIBLE`              | New — fills ADR-036 reservation                              |
| `finance_auditor` × `payment_executor`                        | same scope                       | `AUTHORITY_ROLE_INCOMPATIBLE`              | New — fills ADR-036 reservation                              |
| `finance_auditor` × `report_signatory`                        | same scope                       | `AUTHORITY_ROLE_INCOMPATIBLE`              | New — fills ADR-036 reservation                              |
| `finance_auditor` × report preparer (action-level)            | same scope/period                | `AUTHORITY_ROLE_INCOMPATIBLE`              | New — fills ADR-036 reservation                              |
| `finance_auditor` × report approver (action-level)            | same scope/period                | `AUTHORITY_ROLE_INCOMPATIBLE`              | New — fills ADR-036 reservation                              |
| `payment_authorizer` × `payment_executor`                     | same payment                     | `ORGANIZATION_DUAL_CONTROL_VIOLATION`      | New — HI-32, HI-48                                           |
| creator × approver of the same object                         | same object (transaction/report) | `CONFLICT_REVIEW_SELF_APPROVAL_PROHIBITED` | New — action-level, role-independent                         |
| claimant × reviewer/approver/authorizer/executor of own claim | that claim                       | `CONFLICT_REVIEW_SELF_APPROVAL_PROHIBITED` | New — HI-32                                                  |
| `finance_administrator` × `organizational_administrator`      | same scope                       | `AUTHORITY_ROLE_INCOMPATIBLE` (if adopted) | Open — OD-10, recommended default incompatible               |

`finance_administrator` × `organizational_administrator` is carried
forward as an **open question** rather than settled here (OD-10):
ADR-036 already lists `finance_auditor` ×
`organizational_administrator` as a retained instance of its
self-assignment and dual-control principles, but never addressed
whether the same reasoning extends to `finance_administrator`
specifically. The recommended default, pending the legal-review
closure OD-7 already tracks for the wider matrix, is **incompatible**:
an `organizational_administrator` who is also the scope's
`finance_administrator` could both configure the organizational
structure a finance approval depends on and hold the finance
authority the approval checks, which is the same operational-plus-
oversight collision HI-12 exists to prevent. This ADR does not close
OD-10; it records the default and the reasoning so a future
legal-review round is not starting from nothing.

### Authority is never a role-name string

Every check in this domain resolves an actually active,
scope-matching `OrganizationalAuthority` (or, where a system/
governance-policy role is what is checked, `RoleAssignment`) record
with a currently valid `valid_from`/`valid_until` window, through
`organization-service` — never a comparison against a `role_code`
string alone (HI-53, canon 19e.12). Holding a position in the
organizational hierarchy grants nothing by itself; a scope's
top-level unit head is not implicitly its `finance_administrator`.
Inheritance of an authority down or across scopes is opt-in per role
and per action, through PACK-08's `OrganizationalInheritancePolicy`,
never assumed.

The reason codes this resolution can raise: `FINANCE_AUTHORITY_MISSING`
(no active, scope-matching authority resolves at all);
`ORGANIZATIONAL_AUTHORITY_NOT_USABLE` (reused from PACK-08 — the
authority exists but is not currently usable, e.g. outside its
effective window); `AUTHORITY_ROLE_INCOMPATIBLE` (reused — the
resolved authority collides with an incompatible role already held in
the same scope); `AUTHORITY_ASSIGNMENT_INVALID` (reused — the
authority record itself fails a PACK-08 lifecycle rule);
`AUTHORITY_SCOPE_INVALID` (reused — the authority's scope is
structurally invalid for this action).

### Self-approval and dual control

`domain.assert_not_self_approval` compares the authority reference of
the act that created or benefits from a transaction, claim or
obligation with the authority reference of the act that approves,
authorizes or executes it. A match refuses with the reused
`CONFLICT_REVIEW_SELF_APPROVAL_PROHIBITED`. Where a dual-control
action is at stake — the proposer and the activator/approver must
always differ, restating ADR-036 bullet 8 for finance — a match
instead refuses with the reused `ORGANIZATION_DUAL_CONTROL_VIOLATION`.
Three actions are fixed as dual-control by this ADR: reopening a
closed accounting period (HI-11 of this pack); a write-off above a
policy-set threshold; and activating a critical finance policy
version.

### Conflict of interest reuses canon 19d.11, invents nothing

PACK-10 creates **no new global conflict entity**. Each protected
action records a `conflict_state` (the same closed vocabulary
ADR-042 already established for compliance-service:
`none_declared`/`declared`/`confirmed`/`waived`) and, where one
exists, a reference to an existing canon 19d.11 `ConflictAssessment`
— never a finance-local duplicate of that record. Reusing
`ConflictAssessment` is preferred over inventing a finance-specific
conflict entity for the same reason ADR-042 gave for reusing
`ProceduralCase`: a finance conflict declaration needs the same
positive-declaration, blocking-state and waiver-attribution rules
compliance-service already built and tested, and duplicating that
machinery would duplicate its bugs and let the two conflict models
drift apart. An `undeclared` state fails closed
(`CONFLICT_OF_INTEREST_UNDECLARED`, HI-33); a `declared` or
`confirmed` blocking state refuses (`CONFLICT_OF_INTEREST_BLOCKING`).

### Independent finance audit

`AuditEngagement` is the root aggregate, owned by
`audit_engagement.py` (specification section 7): append-only
`AuditFinding` children, and exactly one create-once
`AuditConclusion` per engagement. It is named "conclusion," never
"opinion," deliberately — nothing in the data model may be read as
issuing a statutory audit opinion, which this platform is not
authorized to certify (specification section 22).
`audit_engagement.py` may not write to any aggregate it audits: an
engagement reads the ledger, contributions, reports and positions it
examines, and records what it finds only in its own `AuditFinding`
children. A reconciliation the auditor performs is itself recorded as
a finding, never written as an authoritative `ReconciliationRecord`
— the auditor observes and reports; it does not correct the books it
is auditing.

Independence is one pure function,
`assert_auditor_independent(engagement, candidate_authority,
prepared_by_authority, conflict_declarations)`, mirroring ADR-042's
own "independence is one pure function, applied by one command"
pattern. It is re-checked at three points, not once: at engagement
opening, at each recorded finding, and at conclusion — because a
conflict, or an incompatible role assignment, can arise after an
engagement has already begun. Any failure raises
`FINANCE_AUDITOR_INDEPENDENCE_VIOLATION`.

### Feature flags

No feature flag may disable any check in this ADR — the authority
resolution, the incompatibility matrix, the self-approval and
dual-control checks, the conflict-of-interest gate, or auditor
independence (HI-45). A flag may gate an optional read surface or
import adapter; none may be read inside an invariant check.

## Consequences

Easier: a report, a regulator or a future audit can name the office
that authorized a payment, administered finance for a scope, or
signed a report, independently of any single transaction; the
incompatibility matrix is enforceable in one place
(`organization-service`'s authority resolution) rather than
scattered across every command that touches money; ADR-036's
finance-preparation/approval reservation is closed by name instead of
staying an indefinite placeholder.

Harder: standing up finance authority for a new organizational unit
now requires four separate, effective-dated, single-scope
appointments before any payment can be authorized and executed by
different people, where an ad hoc single-field model would have taken
one; an operator who expects a `finance_administrator` to also be
implicitly a `payment_authorizer` will be surprised by
`FINANCE_AUTHORITY_MISSING` until both are explicitly assigned; and
the five action-level separations mean the same review or approval
step must record a distinct authority reference every time, with no
shortcut for a small organization where the same few people fill
every role — because a small organization is exactly where role
collision is easiest to miss.

Not decided, honestly stated rather than glossed: `OD-10`
(`finance_administrator` × `organizational_administrator`) is
recorded with a recommended default, not settled; the complete,
legally-refined incompatibility matrix beyond this extension remains
OD-7's open legal-review matter, unchanged by this ADR.

## Security impact

This ADR implements HI-30 through HI-34 and HI-53 directly: no single
authority resolves to both sides of a payment, a report action, or an
audit of the scope it administers, and every resolution goes through
an actually active, scope-matching authority record rather than a
name comparison.

**Collusion is not made impossible by this ADR — it is made
evidenced.** Two people who each legitimately hold one incompatible
half of a separated pair (a `payment_authorizer` and a
`payment_executor`, say) and agree between themselves to defeat the
separation's intent cannot be stopped by any access-control rule,
here or anywhere else in the platform: the system can only enforce
that two _different_, currently active, correctly-scoped authorities
acted, not that those two people did not coordinate. What this ADR
guarantees instead is that such collusion leaves a verifiable trail:
an append-only history of who held which authority when, distinct
authority references on every act, and — for the audit domain
specifically — an `AuditEngagement` whose findings and conclusion are
themselves append-only and independence-checked at three separate
points, so a colluding pair's actions remain visible to a later,
independent audit even though the pair's initial action was not
itself blocked.

This ADR adds **no new data access**. `grants_data_access` and
`grants_procedural_authority` remain the two independent booleans
ADR-036 fixed on the PACK-08 `OrganizationalAuthority` record; none
of the four new roles is assumed to carry either flag by default, and
a future implementation round sets both explicitly per role/scope
combination exactly as ADR-036 already requires.

## Data impact

`OrganizationalAuthority.role_code` gains four new values:
`finance_administrator`, `payment_authorizer`, `payment_executor`,
`report_signatory`. No new field is added to `OrganizationalAuthority`
itself; `incompatibilities`, `valid_from`/`valid_until`,
`revocation_reason_reference`, `grants_data_access` and
`grants_procedural_authority` are the same fields ADR-036 already
defined. `AuditEngagement`, `AuditFinding` and `AuditConclusion` are
new aggregates owned by `finance-service` (specification section
8.2.19); no canon entity is added or amended by this ADR.
`conflict_state` is a field on each protected finance action, not a
new canon entity, and where a declaration exists it carries a
reference to an existing canon 19d.11 `ConflictAssessment`.

## Migration impact

The four new `role_code` values are additive configuration on an
already-extensible field (`OrganizationalAuthority.role_code` is not
a closed enum requiring a schema migration to extend); no existing
`OrganizationalAuthority` assignment is changed, revoked or
reinterpreted by this ADR. `finance_auditor`'s existing
incompatibility with `finance_administrator` (PACK-08 section 9.3
rule 3, canon 19e.16) is unchanged; this ADR only adds further
incompatible pairs alongside it. The canon amendment PACK-10 requires
overall (`PACK-10-CANON-AMENDMENT-PROPOSAL.md`, `0.7.0 → 0.8.0`) must
record this ADR's extended incompatibility baseline as part of that
amendment's own institutional-role account; this ADR does not itself
edit canon text and creates no obligation for existing deployments to
migrate any data before that amendment is accepted.

## Reversibility

Reversible with cost before any implementation exists. Once
`finance_administrator`, `payment_authorizer`, `payment_executor` or
`report_signatory` assignments exist in a real deployment, narrowing,
renaming or merging any of the four — or relaxing any pair in the
incompatibility matrix — becomes a change with real appointment data
to migrate, not a specification edit; expanding the matrix (e.g.
resolving OD-10) remains additive and low-cost at any time, matching
ADR-036's own precedent for its non-combinable-role baseline.

## Related canon version

Authored against canon version `0.7.0`. This ADR proposes no change
to canon text: `OrganizationalAuthority` and the institutional-role
mechanism it extends are governed by PACK-08's own canon-amendment
requirement (ADR-036 "Related canon version"), not by this ADR.
PACK-10 as a whole requires a canon amendment (`0.7.0 → 0.8.0`,
`proposed`) before any implementation of this pack begins, per
`PACK-10-CANON-AMENDMENT-PROPOSAL.md`; this ADR's four new
`role_code` values and its incompatibility-matrix extension are among
the content that amendment must record, but preparing and accepting
the amendment itself is out of this ADR's scope.
