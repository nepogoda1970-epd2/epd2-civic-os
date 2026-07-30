# PACK-12 — Role Separation Matrix

Specification-only. No code. Not implemented.

> **Status note, updated by the PACK-12 FINAL PASS round
> (2026-07-29).** The "specification-only / not implemented" statement
> above describes the _specification round_ that produced this document
> and is preserved as the historical record. It is no longer the state of
> the repository: `services/privileged-access-service` now implements this
> specification; the implementation reached **FINAL PASS** at repository
> version `0.12.0`.
>
> **PACK-12 is now FINAL PASS** at repository version `0.12.0`, verified
> by an external GitHub Actions run. **NOT PRODUCTION READY. NOT LEGALLY
> ACTIVATED.** See `docs/handover/PACK-12-FINAL-PASS-REPORT.md`.

Companion to `PACK-12-SPECIFICATION.md` section 3 and
`ADR-061-pack-12-privileged-role-separation.md`.

---

## 1. Two distinct kinds of authority

**This distinction governs the whole document.** An earlier draft treated
all eleven PACK-12 roles as new, equivalent operational roles introduced
through canon 19e.15's open `role_code` list. That was wrong for two of
them, and the correction is normative.

| Kind                                           | What it is                                                                                  | Where it comes from                                                                              |
| ---------------------------------------------- | ------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| **Existing institutional roles**               | Standing institutional offices with established semantics and established incompatibilities | The Architecture Framework, which already defines them. PACK-12 does not create or redefine them |
| **PACK-12 privileged operational assignments** | Scope-bound, purpose-bound, effective-dated functions granted through governed authority    | Introduced by PACK-12 through canon 19e.15's open `role_code` extension point                    |

### 1.1 Existing institutional roles — consumed, not defined

| Role                       | PACK-12 position                                                                                                                                                                                                                |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **System Administrator**   | Already an institutional role in the Architecture Framework. PACK-12 keeps its institutional semantics and its existing incompatibilities unchanged, and adds only obligations about what it may **not** reach (`P12-ROLE-003`) |
| **Security Administrator** | Already an institutional role in the Architecture Framework. Same position: existing semantics and incompatibilities preserved; PACK-12 adds only the boundary that it is not a domain decision-maker (`P12-ROLE-004`)          |

`P12-ROLE-014` PACK-12 MUST NOT redefine, rename, narrow or widen the
institutional semantics of System Administrator or Security
Administrator. Any constraint this package states about either MUST be
read as a restatement of, or an addition consistent with, the framework's
existing definition — never as a replacement of it.

`P12-ROLE-015` The existing institutional incompatibility between System
Administrator and Security Administrator is preserved unchanged. PACK-12
does not create that separation; the framework and register `FIR-INV-008`
already establish it, and PACK-12 depends on it.

### 1.2 PACK-12 privileged operational assignments — nine

| Assignment                               | Function                                                              |
| ---------------------------------------- | --------------------------------------------------------------------- |
| `iam_administrator`                      | Identity lifecycle, credential binding, role assignment mechanics     |
| `audit_custodian`                        | Audit availability, retention, chain verification, evidence sealing   |
| `domain_administrator`                   | Administration of ONE named domain within ONE organizational scope    |
| `data_owner`                             | Authority over a record class in a scope; export authorization for it |
| `export_approver`                        | Approval or refusal of a specific export request                      |
| `dlp_security_officer`                   | DLP policy authorship, DLP assessment, forbidden-data findings        |
| `independent_privileged_access_reviewer` | Periodic and post-access review of grants and sessions                |
| `break_glass_approver`                   | The second control on a break-glass activation                        |
| `disclosure_control_reviewer`            | Small-cohort, cumulative-release and differencing review; exceptions  |

### 1.3 Rules governing operational assignments

`P12-ROLE-016` An operational assignment MUST NOT replace, substitute for
or stand in place of an institutional role. The two are different kinds
of authority and are never interchangeable.

`P12-ROLE-017` A subject MUST receive an operational assignment only
through governed authority — a PACK-08 `OrganizationalAuthority` or
`RoleAssignment` resolved through the authorization port. An assignment
asserted by a caller, a configuration file or a bare role-name string is
not an assignment.

`P12-ROLE-018` Every operational assignment MUST be scope-bound,
purpose-bound and effective-dated. An assignment lacking any of the three
MUST NOT be issuable.

`P12-ROLE-019` An operational assignment MUST NOT extend, widen or
supplement canonical institutional authority. Holding
`domain_administrator` grants no institutional standing; holding
`audit_custodian` makes no one an `independent_auditor`.

`P12-ROLE-020` Existing institutional incompatibilities MUST be preserved
in full. PACK-12's additions in section 4 are cumulative with them, never
substitutional.

`P12-ROLE-021` An operational assignment MUST NOT be used to obtain, by
composition or by sequence, an authority the Institutional Role Matrix
would refuse. Where the effect of a set of assignments would amount to an
institutional authority the subject does not hold, the act MUST be
refused with `PRIVILEGE_ROLE_COMBINATION_PROHIBITED` — not permitted on
the ground that no single assignment was individually forbidden.

---

## 2. Relationship to PACK-08 and the canon

Canon 19e.15 keeps `role_code` an open string, extensible "by
configuration + ADR review". Canon 19e.16 fixes a **minimum** pairwise
incompatibility baseline and states it may be made stricter and never
relaxed.

PACK-12 therefore:

- registers the **nine operational** `role_code` values in the open list,
  through `ADR-061-pack-12-privileged-role-separation.md`;
- consumes the **two institutional** roles as they already exist;
- adds pairwise incompatibility entries (section 4);
- removes nothing, relaxes nothing, renames nothing;
- adds **no** new canonically-named institutional role to canon 19e.16's
  seven-role list (`dpo`, `election_board_member`, `election_officer`,
  `independent_auditor`, `finance_auditor`, `party_arbitrator`,
  `organizational_administrator`).

---

## 3. Capability matrix

`Y` = within the authority. `N` = never, by specification. `G` = only
through a separate governed grant naming that capability.

Institutional roles are marked **[I]**, operational assignments **[O]**.

| Capability                                        | sec.adm [I] | sys.adm [I] | iam.adm [O] | audit.cust [O] | dom.adm [O] | data.owner [O] | exp.appr [O] | dlp.off [O] | ind.rev [O] | bg.appr [O] | disc.rev [O] |
| ------------------------------------------------- | ----------- | ----------- | ----------- | -------------- | ----------- | -------------- | ------------ | ----------- | ----------- | ----------- | ------------ |
| Configure privileged-access policy                | Y           | N           | N           | N              | N           | N              | N            | N           | N           | N           | N            |
| Configure DLP / index policy                      | Y           | N           | N           | N              | N           | N              | N            | Y           | N           | N           | N            |
| Administer infrastructure                         | N           | Y           | N           | N              | N           | N              | N            | N           | N           | N           | N            |
| Read domain content                               | N           | N           | N           | N              | G           | G              | N            | N           | N           | N           | N            |
| Take a domain decision                            | N           | N           | N           | N              | G           | N              | N            | N           | N           | N           | N            |
| Manage identities and bindings                    | N           | N           | Y           | N              | N           | N              | N            | N           | N           | N           | N            |
| Grant privileged domain access to self            | N           | N           | N           | N              | N           | N              | N            | N           | N           | N           | N            |
| Approve a privileged-access request               | G           | N           | N           | N              | N           | N              | N            | N           | N           | N           | N            |
| Modify or delete an audit record                  | N           | N           | N           | N              | N           | N              | N            | N           | N           | N           | N            |
| Verify and seal audit / evidence                  | N           | N           | N           | Y              | N           | N              | N            | N           | N           | N           | N            |
| Authorize export of a record class                | N           | N           | N           | N              | N           | Y              | N            | N           | N           | N           | N            |
| Approve a specific export                         | N           | N           | N           | N              | N           | N              | Y            | N           | N           | N           | N            |
| Perform DLP assessment                            | N           | N           | N           | N              | N           | N              | N            | Y           | N           | N           | N            |
| Review grants and sessions                        | N           | N           | N           | N              | N           | N              | N            | N           | Y           | N           | N            |
| Approve break-glass                               | N           | N           | N           | N              | N           | N              | N            | N           | N           | Y           | N            |
| Decide a disclosure exception                     | N           | N           | N           | N              | N           | N              | N            | N           | N           | N           | Y            |
| Reach ballot-level or intermediate-tally material | N           | N           | N           | N              | N           | N              | N            | N           | N           | N           | N            |

The two all-`N` rows are the load-bearing ones: no authority in this
matrix, in any combination, and under any emergency condition, mutates an
audit record or reaches ballot-level or intermediate-tally material.

Final **certified** results are a different category and are governed by
`PACK-12-DATA-SEARCH-EXPORT-MATRIX.md` section 4, not by that row. No
authority here publishes a certified result either; PACK-12 can only
audit that a governed publication occurred.

---

## 4. Pairwise incompatibility

Each pair MUST NOT be held, active, by the same subject, in the same
organizational scope, at the same time. These are **cumulative** with the
existing institutional incompatibilities and with PACK-08's
`PAIRWISE_INCOMPATIBLE_ROLES`; nothing existing is removed or relaxed
(`P12-ROLE-020`).

Pair 1 is marked **[preserved]** — an existing institutional
incompatibility restated for completeness, not a PACK-12 invention.

| #   | A                                        | B                                        | Kind      | Why                                                                   |
| --- | ---------------------------------------- | ---------------------------------------- | --------- | --------------------------------------------------------------------- |
| 1   | `security_administrator` [I]             | `system_administrator` [I]               | preserved | Existing institutional separation; register `FIR-INV-008`             |
| 2   | `security_administrator` [I]             | `iam_administrator` [O]                  | added     | Policy author must not also mint the identities the policy binds      |
| 3   | `security_administrator` [I]             | `independent_privileged_access_reviewer` | added     | Review of one's own policy is not review                              |
| 4   | `system_administrator` [I]               | `audit_custodian` [O]                    | added     | The operator of the store must not also be its custodian              |
| 5   | `system_administrator` [I]               | `domain_administrator` [O]               | added     | Infrastructure authority must not become content authority            |
| 6   | `iam_administrator`                      | `domain_administrator`                   | added     | Otherwise self-provisioning of domain access is one assignment away   |
| 7   | `iam_administrator`                      | `independent_privileged_access_reviewer` | added     | The reviewer must not be able to alter the bindings under review      |
| 8   | `audit_custodian`                        | `independent_privileged_access_reviewer` | added     | Independence of the evidence chain from its reviewer                  |
| 9   | `data_owner`                             | `export_approver`                        | added     | The owner proposes; a distinct approver decides                       |
| 10  | `dlp_security_officer`                   | `export_approver`                        | added     | Assessment must not decide the thing it assessed                      |
| 11  | `dlp_security_officer`                   | `disclosure_control_reviewer`            | added     | Two independent lenses on release risk, not one                       |
| 12  | `break_glass_approver`                   | `system_administrator` [I]               | added     | The most likely activator must not also be the approver               |
| 13  | `break_glass_approver`                   | `independent_privileged_access_reviewer` | added     | Post-hoc review must be independent of the approval                   |
| 14  | `disclosure_control_reviewer`            | `data_owner`                             | added     | The party wanting release must not clear its own risk                 |
| 15  | `independent_privileged_access_reviewer` | `domain_administrator`                   | added     | The reviewer must hold no operational privilege in the reviewed scope |

Fourteen additions, one preserved. `P12-ROLE-012` requires the whole
table to be enforced at assignment and re-checked at the act.

---

## 5. Per-request separation, beyond role pairs

Role incompatibility is not sufficient on its own: two compatible
authorities held by one person can still collapse a control if that
person occupies both ends of a single decision.

| Rule                                                                              | Requirement    |
| --------------------------------------------------------------------------------- | -------------- |
| The requester of a privileged grant MUST NOT be its approver                      | `P12-PAM-004`  |
| The activator of a break-glass MUST NOT be its approver                           | `P12-BG-003`   |
| The activator MUST NOT be the independent reviewer of that activation             | `P12-BG-014`   |
| The DLP officer who assessed an export MUST NOT approve it                        | `P12-DLP-003`  |
| The requester of an export MUST NOT approve it                                    | `P12-EXP-006`  |
| The requester of a release MUST NOT be its disclosure-control reviewer            | `P12-SDC-006`  |
| An IAM administrator MUST NOT be the subject of an assignment they alone effected | `P12-ROLE-005` |
| No composition of assignments may yield an institutional authority not held       | `P12-ROLE-021` |

---

## 6. What this matrix does not do

It does not grant anything. Every cell marked `Y` describes the outer
bound of an authority; an actual capability still requires a grant that
is purpose-, resource-, operation-, organization- and time-scoped
(`P12-PAM-002`). A role is a ceiling, never a key.

It also does not define System Administrator or Security Administrator.
Those belong to the Architecture Framework, and this document consumes
them unchanged.
