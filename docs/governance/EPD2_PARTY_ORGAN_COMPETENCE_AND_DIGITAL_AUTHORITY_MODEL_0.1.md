# EPD² Party-Organ Competence & Digital Authority Model 0.1

**Status:** governed proposal supporting `FIR-GOV-005`; not itself an adopted party statute or legally activated authority map  
**Date:** 2026-08-28  
**Purpose:** bind the political and organizational competence of EPD² organs to the exact digital authorities represented in Civic OS.

## 1. Core constitutional rule

The EPD² authority model is federated and scope-bound.

```text
organizational hierarchy
!= political competence
!= organizational authority
!= data access
!= technical administration
!= security authority
!= voting authority
```

A higher organizational level does not automatically inherit the permissions, data access, offices, credentials or operational powers of a lower level. Every consequential digital authority must be traceable to an exact lawful/statutory competence, exact governing rule version, exact decision/election/appointment, exact organizational scope and current validity state.

## 2. Party structure represented by the model

The target structure is:

```text
Bundesverband
  -> Landesverband
      -> Kreisverband / Bezirksverband
          -> Ortsverband
              -> optional Ortsgruppe / local working group
```

An `Ortsgruppe` may be constituted as a non-Gebietsverband working structure. It does not receive independent statutory, financial, membership, disciplinary or data-administration authority merely because it exists in the portal.

Each formal Gebietsverband has its own organizational scope. Reorganization, merge, split, dissolution, successor status or territorial reassignment does not automatically migrate offices, authorities, data permissions, technical credentials or appointments.

## 3. Democratic organs and executive organs

### Bund

- `Bundesparteitag` — highest organ of the party.
- `Bundesvorstand` — executive board for the Bund scope and the powers assigned by law, Bundessatzung and Bundesparteitag.
- `Bundesschiedsgericht` — independent party court.
- `Bundesrechnungsprüfung` — independent financial review elected by the competent party assembly.

### Land

- `Landesparteitag` / lawful Landesmitgliederversammlung or Vertreterversammlung — highest organ of the Landesverband.
- `Landesvorstand` — executive board for the Land scope.
- `Landesschiedsgericht` — independent first or appellate instance as provided by Schiedsgerichtsordnung.
- `Landesrechnungsprüfung` — independent financial review.

### Kreis / Bezirk

- `Kreisparteitag` / Mitglieder- or Vertreterversammlung — highest organ of the Kreis-/Bezirksverband.
- `Kreis-/Bezirksvorstand` — executive board for its exact territorial scope.
- financial review according to the Finanzordnung.
- dispute jurisdiction according to the Schiedsgerichtsordnung; common Kreis-level courts may be used where lawfully constituted.

### Ortsverband

- `Hauptversammlung` — highest organ of the lowest formal Gebietsverband.
- `Ortsvorstand` — executive board for the Ortsverband.
- financial review where the Ortsverband owns a budget/accounting responsibility.

## 4. Competence matrix

| Subject                                        | Bund                                             | Land                                      | Kreis/Bezirk                              | Ort                                                  |
| ---------------------------------------------- | ------------------------------------------------ | ----------------------------------------- | ----------------------------------------- | ---------------------------------------------------- |
| Bundessatzung                                  | Bundesparteitag decides                          | may propose                               | may propose                               | may propose                                          |
| Grundsatzprogramm of EPD²                      | Bundesparteitag decides                          | may initiate/propose                      | may initiate/propose                      | may initiate/propose                                 |
| Landesprogramm / Landtagswahlprogramm          | federal law/Satzung limits only                  | Landesparteitag decides                   | may propose                               | may propose                                          |
| Kreis-/Kommunalprogramm                        | framework only                                   | framework/oversight only                  | competent Kreis assembly decides          | may propose or decide own local scope where assigned |
| Election of own Vorstand                       | Bundesparteitag                                  | Landesparteitag                           | Kreisparteitag                            | Hauptversammlung                                     |
| Removal of own elected Vorstand member         | competent own assembly under Satzung             | competent own assembly                    | competent own assembly                    | competent own assembly                               |
| Own budget                                     | Bund scope                                       | Land scope                                | Kreis scope                               | Orts scope if financially constituted                |
| Own financial execution                        | Bund roles                                       | Land roles                                | Kreis roles                               | Orts roles if assigned                               |
| Membership administration                      | only if competent/no lower body or reserved rule | exact Land competence                     | exact Kreis competence if assigned        | exact local competence if assigned                   |
| Candidate filing/signature                     | federal proposals where legally competent        | Land proposals where legally competent    | local proposals where legally competent   | local proposals where legally competent              |
| Political initiative intake                    | Bund scope                                       | Land scope                                | Kreis scope                               | Orts scope                                           |
| Citizen-office/casework                        | Bund cases                                       | Land cases                                | Kreis cases                               | local cases if service exists                        |
| Publication authority                          | own official scope only                          | own official scope only                   | own official scope only                   | own official scope only                              |
| Oversight of lower branch                      | only as Satzung/Ordnung explicitly grants        | only as Satzung/Ordnung explicitly grants | only as Satzung/Ordnung explicitly grants | none over higher scopes                              |
| Voting-domain authority                        | only voting-specific law/rules                   | only voting-specific law/rules            | only voting-specific law/rules            | only voting-specific law/rules                       |
| Technical identity/security/key administration | never by political hierarchy alone               | never by political hierarchy alone        | never by political hierarchy alone        | never by political hierarchy alone                   |

## 5. Bundesparteitag reserved competences

The target constitutional model reserves at least the following Bund-level matters to the Bundesparteitag, subject to mandatory law:

- adoption and amendment of Bundessatzung;
- adoption and amendment of the EPD² Grundsatzprogramm and other Bund-wide programme positions;
- adoption of Bund-level Nebenordnungen;
- election/removal of Bundesvorstand;
- election of Bundesschiedsgericht and Bundesrechnungsprüfung;
- acceptance and decision on required activity/accountability reports;
- dissolution/merger decisions assigned to the Bund level;
- confirmation of a consequential intervention against a Landesverband where the Bundessatzung assigns that competence;
- fundamental Bund-wide political decisions expressly reserved to it.

The Bundesparteitag does not technically operate Civic OS and does not receive root/platform/voting credentials from its political status.

## 6. Bundesvorstand

The Bundesvorstand executes Bund-level decisions, conducts ordinary Bund business, represents the party within its statutory representation rules, coordinates legally assigned party-wide obligations and manages only the authorities granted to it.

It is not a universal superior administrator. In particular, Bund hierarchy alone does not grant the Bundesvorstand unrestricted access to Land member data, correspondence, finance, casework, credentials, keys, voting materials or lower-level office assignments.

## 7. Landesparteitag and Landesvorstand

The Landesparteitag is the highest organ of the Landesverband and governs the Land scope within law and the Bundessatzung. It elects the Landesvorstand and the Land-level independent bodies required by the adopted governance model.

The Landesvorstand conducts ordinary Land business and executes lawful decisions for its Land scope. It does not become a Bund administrator or administrator of another Land.

A Land-level political office may be represented digitally only by an `OrganizationalAuthority` that points to the exact Land scope and source decision/election.

## 8. Kreis-/Bezirksverband and Ortsverband

Each lower formal Gebietsverband governs its own assigned local affairs. The higher-level association retains only the oversight, coordination, legal and emergency powers expressly created by law/Satzung/Ordnung.

A local working group that is not a formal Gebietsverband must not receive powers that legally belong to a formal party organ.

## 9. Membership and territorial assignment

EPD² membership is membership in one party, not a stack of independent memberships.

The system may maintain an effective-dated territorial assignment such as:

```text
EPD² member
  -> Land Berlin
      -> Kreis/Bezirk X
          -> Ortsverband Y
```

The assignment controls participation and procedural scope where law/Satzung so provides. It does not itself grant administrative authority.

A relocation creates a new effective-dated assignment. It must not rewrite historical participation, decisions, candidacies or audit evidence and must not create duplicate voting rights.

## 10. Political initiatives and programmes

Members and Gebietsverbände may submit initiatives according to the adopted procedural rules. The system may propose a scope classification, but no automated system may make the final political/legal competence decision on its own.

Regional programme authority remains regional. A Landesverband may adopt a lawful Landesprogramm within its competence, but it cannot unilaterally amend the EPD² Bund programme. A proposal to change the Bund programme proceeds into the Bund-level programme procedure.

## 11. Candidate and election authority

The model distinguishes:

```text
candidate selection / Aufstellung
!= filing/signature authority
```

A board that is legally authorized to sign or file a Wahlvorschlag does not thereby obtain power to appoint the candidate outside the legally required nomination procedure.

Digital authority must therefore distinguish nomination procedure roles, filing/signature roles, election-administration roles and voting/trustee roles.

## 12. Public mandate separation

```text
party office != public mandate
```

A Mandatsträger may receive representative/citizen-office workspace authority relevant to the public mandate, but no automatic Landesvorstand, finance, membership-administration, identity, security or voting authority.

Party participation results may create political accountability and explanation duties only within the adopted programme/Satzung model; they must not create an unlawful imperative public mandate.

## 13. Financial separation of duties

Each financially constituted scope may have its own budget and authorized finance actors under the common Beitrags- und Finanzordnung.

At minimum the system must be able to separate:

```text
prepare/payment request
approve
execute
book/reconcile
review/audit
```

A treasurer or finance administrator in one organizational scope receives no automatic finance authority in another scope.

The exact Bund/Land/Kreis/Ort allocation of contributions and budgets belongs in the Beitrags- und Finanzordnung, not in hard-coded software.

## 14. Party courts and independent review

The target model provides independent party-court review consistent with mandatory law. At minimum the party and the highest-level Gebietsverbände must have the required courts; the Schiedsgerichtsordnung may provide common courts for lower levels where lawful.

No Vorstand may obtain technical privileges that allow it to alter, suppress or delete the court record or audit evidence of proceedings concerning that Vorstand.

## 15. Regional intervention competence chain

`FIR-GOV-004` defines the technical intervention primitives. This proposal supplies the target political competence mapping, subject to adoption in Satzung/Ordnung.

### Level 1 — security containment

A compromised session/credential may be quarantined by a technically competent security authority under incident policy. This is not a political removal from office.

### Levels 2–4 — governance intervention

Consequential intervention requires a competent party-organ decision and the digital action must bind exactly to that decision.

Proposed default chain:

| Target                                   | Temporary initiating/acting organ                           | Required confirmation                                                  | Judicial/remedy route                                 |
| ---------------------------------------- | ----------------------------------------------------------- | ---------------------------------------------------------------------- | ----------------------------------------------------- |
| Landesverband / whole Landesorgan        | Bundesvorstand where Satzung permits                        | next Bundesparteitag / competent higher Bund organ required by Satzung | Bundesschiedsgericht                                  |
| Kreis-/Bezirksverband / whole Kreisorgan | Landesvorstand where Land/Bund rules permit                 | next Landesparteitag                                                   | Landesschiedsgericht, with further remedy as provided |
| Ortsverband / whole Ortsorgan            | Kreisvorstand; if no competent Kreis exists, Landesvorstand | next competent higher Parteitag                                        | competent Parteischiedsgericht                        |

A technical operator never decides the political merits of the intervention.

Intervention must be narrow, reason-coded, time-bounded where temporary, auditable and reviewable. It must not silently convert into a permanent higher-level takeover.

## 16. Digital authority binding

Every consequential `OrganizationalAuthority` must preserve at least:

- subject/person or governed office-holder reference;
- exact role/office code;
- exact organization and scope;
- competence/capability set;
- source rule/Satzung/Ordnung version;
- source election/appointment/decision reference;
- `valid_from` and, where applicable, `valid_until`;
- current lifecycle state;
- appointing/deciding authority;
- audit/evidence references.

The runtime must not grant authority solely because a profile says `Vorsitzender`, `Schatzmeister`, `Admin` or because the organization has a higher position in the hierarchy.

## 17. Mandatory separation from technical authority

Political/organizational roles and technical control roles are independent.

| Technical role               | May                                            | Must not derive                             |
| ---------------------------- | ---------------------------------------------- | ------------------------------------------- |
| Identity/Credential Operator | governed credential lifecycle                  | party office or political competence        |
| Recovery Approver            | approve governed recovery                      | restoration of suspended party office       |
| Security Operator            | contain sessions/credentials/incidents         | political/disciplinary decision authority   |
| Privileged Access Operator   | activate approved JIT/break-glass              | permanent universal admin                   |
| Service Owner                | request service identity/credential            | key custody or unrestricted platform access |
| Key Custodian                | execute approved KMS/HSM/certificate lifecycle | party-organ competence                      |
| Auditor/Reviewer             | inspect evidence                               | power to approve/execute own audited act    |
| Voting Trustee               | voting-specific trust authority                | general party/platform administration       |

## 18. Request / approval / execution / review split

For consequential administration the model must support separate authorities for:

- `REQUEST`;
- `APPROVE`;
- `EXECUTE` / `GENERATE_OR_ENROLL`;
- `ACTIVATE`;
- `SUSPEND_OR_QUARANTINE`;
- `REVOKE`;
- `RESTORE`;
- `ROTATE_OR_REPLACE`;
- `DESTROY` where applicable;
- `READ_METADATA`;
- `VIEW_OR_EXPORT_SECRET` only where separately necessary;
- `REVIEW_OR_AUDIT`.

No political title or generic technical admin role grants the complete set.

## 19. Voting trust-domain carve-out

The general organizational hierarchy must not create voting-key or ballot authority.

Bundesvorstand, Landesvorstand, regional admin, identity operator, security operator, ordinary platform key custodian and temporary supervisor do not receive authority to read ballots, reveal identity-vote linkage, mint voting credentials, operate trustee keys or alter tally evidence unless a separate voting-specific lawful role explicitly grants the exact act.

## 20. EPD Plattform e.V. boundary

EPD Plattform e.V. may provide technical services under the contract defined by the party. It is not a party organ and technical operation must not create political, membership, candidacy, financial, disciplinary, publication or voting competence.

## 21. Required portal/control-plane behavior

The control plane must show, for every authority decision:

```text
Who is acting?
Which office/role?
Which organizational scope?
Which exact capability?
Which rule version grants it?
Which election/appointment/decision created it?
Is it active now?
Is intervention/restriction active?
Is a second approval required?
Is required data access separately authorized?
What evidence will be produced?
What review/appeal route applies?
```

Any unresolved mandatory question fails closed.

## 22. Implementation placement

- **Satzung / Nebenordnung:** legal competence and organ structure.
- **Rules registry:** exact machine-readable RuleVersion and competence profile.
- **organization-service:** authoritative organization graph and `OrganizationalAuthority` lifecycle.
- **API/runtime:** action-time authorization; no stale-role inheritance.
- **CTRL:** proposal/approval/review queues, SoD, evidence and intervention controls.
- **FRONT:** user-visible office/scope/competence and remedies without misleading superadmin semantics.
- **OPS:** lawful operational procedures and emergency containment.
- **SEC:** adversarial tests for hierarchy escalation, cross-Land leakage, self-grant, stale authority, approval bypass and voting-domain escape.
- **FINAL INTEGRATION:** prove exact legal decision -> digital authority -> action -> evidence -> review chain.

## 23. Acceptance criteria

The target is not satisfied until an integrated baseline proves at least that:

1. Bund hierarchy alone cannot access a Land's protected data or administer it;
2. a valid Land office grants only its exact Land scope/capabilities;
3. a technical admin cannot create a political office or reactivate a suspended one;
4. a political office cannot self-mint technical credential/key authority;
5. every consequential authority traces to exact rule version + source decision + scope;
6. relocation/reorganization does not silently transfer authorities or create duplicate voting rights;
7. nomination and Wahlvorschlag filing are separately authorized;
8. finance preparation/approval/execution/review can be separated;
9. intervention follows the competent organ chain and does not disable unaffected member rights;
10. voting trust-domain authority cannot be acquired through ordinary party or technical hierarchy;
11. court/audit evidence remains immutable against the actors it reviews;
12. unsupported or stale authority fails closed.
