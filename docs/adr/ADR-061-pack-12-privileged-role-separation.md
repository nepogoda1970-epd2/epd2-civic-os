# ADR-061: Privileged role separation — two institutional roles, nine operational assignments

## Status

`proposed`

## Date

2026-07-29

## Context

`FIR-ROADMAP-002` schedules PACK-12 at repository version `0.12.0`, and
the register already carries the invariants this pack must make concrete:
`FIR-INV-008` (Security Admin / System Admin separation), `FIR-INV-009`
(JIT and break-glass governance), `FIR-INV-014` (no universal
administration) and `FIR-INV-007` (DLP and controlled export). The
architecture gap is `AGR-23`.

PACK-08 already owns the organizational authority model: canon 19e.15
keeps `role_code` an open string extensible "by configuration + ADR
review", canon 19e.16 fixes a minimum pairwise incompatibility baseline
and states it may be made stricter and never relaxed, and
`organization-service` implements both. PACK-10 and PACK-11 each defined
their own context roles on top of that model — seven finance roles, eight
document roles — without adding a canonically-named institutional role.

PACK-12 needs privileged administrative roles that no existing pack
defines, and it needs them not to become the very thing the register
forbids.

## Problem

1. Without an explicit decision, "administrator" is one word covering at
   least five incompatible jobs: running the infrastructure, setting
   security policy, managing identities, keeping the audit chain, and
   administering a domain. Conflating any two of them produces a role
   that can both make a rule and escape it.
2. Without a decision on where these roles live, PACK-12 could plausibly
   add them to canon 19e.16's seven-role institutional list — which would
   make an operational access-control concern into a constitutional one,
   and would require a canon amendment for every future adjustment.
3. Without an explicit extension of the incompatibility baseline, the
   pairs that matter for privileged administration would exist only as
   prose, and prose does not deny anything at runtime.

## Considered options

- **Option A — one `platform_administrator` role with capability flags.**
  Simple to implement and simple to misconfigure. A flag set is exactly
  the "unrestricted universal admin" `FIR-INV-014` forbids, wearing a
  configuration file. Rejected.
- **Option B — add the privileged roles to canon 19e.16's institutional
  list.** Would give them constitutional weight, but institutional roles
  in this repository are _offices_ (DPO, election officer, auditor,
  arbitrator), not operational access grades. It would also force a canon
  amendment for each future role, which the canon's own amendment
  discipline discourages. Rejected.
- **Option C — treat every one of the eleven as a new operational
  `role_code`.** This was the first draft's choice and it was wrong:
  System Administrator and Security Administrator are already
  institutional roles in the Architecture Framework, with established
  semantics and established incompatibilities. Registering them as new
  operational codes would have created a second, divergent definition of
  each — exactly the failure ADR-012 and ADR-027 guard against at every
  other boundary. Rejected on reconciliation.
- **Option D — consume the two institutional roles as they exist, and
  register only the nine genuinely new functions as operational
  assignments through canon 19e.15's open-list mechanism, plus fourteen
  additions to the 19e.16 pairwise baseline and one preserved pair.**
  **Chosen.**

## Decision

PACK-12 works with two kinds of authority and never conflates them.

**Existing institutional roles, consumed unchanged:** System
Administrator and Security Administrator. PACK-12 does not create,
rename, narrow or widen them (`P12-ROLE-014`), and the existing
institutional incompatibility between them is preserved rather than
invented (`P12-ROLE-015`).

**PACK-12 privileged operational assignments, introduced here:**
`iam_administrator`, `audit_custodian`, `domain_administrator`,
`data_owner`, `export_approver`, `dlp_security_officer`,
`independent_privileged_access_reviewer`, `break_glass_approver`,
`disclosure_control_reviewer` — nine `role_code` values registered
through canon 19e.15's open-list extension point.

Six rules bound the assignments (`P12-ROLE-016` through `P12-ROLE-021`):
an assignment never replaces an institutional role; it is conferred only
through governed authority; it is always scope-bound, purpose-bound and
effective-dated; it never extends canonical institutional authority;
existing institutional incompatibilities are preserved in full; and no
composition of assignments may yield an institutional authority the
subject does not hold.

PACK-12 adds **no** new canonically-named institutional role to canon
19e.16's seven-role list.

PACK-12 adds fourteen pairwise incompatibility entries to the baseline
and preserves one existing institutional pair, listed in
`PACK-12-ROLE-SEPARATION-MATRIX.md` section 4. It removes none.

The separations in `P12-ROLE-001` through `P12-ROLE-013` are normative.
Three are structural rather than merely prohibitive, and are the ones a
reviewer should check first: no role reaches ballot content, no role
mutates an audit record, and no combination spans all domains and scopes.

## Consequences

Easier: a reviewer can answer "what can this administrator do?" from one
matrix; new operational assignments can be added by ADR without a canon
amendment; the incompatibility baseline stays one mechanism rather than
two; and the framework's institutional definitions remain the single
source for the two roles it already owns.

Harder: eleven distinct authorities is more assignment work than one, and an
organization with few staff will find some pairs genuinely inconvenient.
That inconvenience is the control functioning, not a defect — but it does
mean the implementation must make delegation and time-bounded assignment
easy enough that operators do not route around it.

## Security impact

Directly and substantially. This ADR is the foundation for threats
T-P12-01 (universal-admin escalation), T-P12-02 (self-approval), T-P12-03
(role accumulation) and T-P12-08 (infrastructure admin reading domain
data). It does not by itself address T-P12-05 (credential sharing) or
T-P12-06 (session hijacking), which depend on PACK-14.

## Data impact

No canonical entity is changed. `role_code` remains an open string on
PACK-08's `OrganizationalAuthority` and `RoleAssignment`; the nine new
values are data within that existing field, not a schema change. The two
institutional roles are unchanged framework definitions and gain no new
representation here.

## Migration impact

None in this round — no code exists. At implementation time, the nine
values and fourteen added pairs are additive; no existing assignment becomes
invalid, though an existing subject holding a newly-incompatible pair
would surface at the next act-time check and require operator action.
That surfacing is intended.

## Reversibility

Reversible with cost. Removing a role code after grants exist would
orphan them; removing an incompatibility pair is forbidden by canon
19e.16's own closing rule.

## Related canon version

Authored against canon `0.8.0`. **Proposes no canon version bump** — see
`PACK-12-CANON-ASSESSMENT.md`.
