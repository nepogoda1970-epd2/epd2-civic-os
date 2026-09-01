# EPD² Resilient Trust, Delegated Regional Issuance, Recovery & Immutable Audit Model 0.1

**Status:** governed target model supporting `FIR-TRUST-002`; not implemented, not production activated  
**Date:** 2026-08-28  
**Purpose:** remove avoidable central trust single points of failure while preserving scope isolation, key custody, political/technical separation, voting isolation and durable independent evidence.

## 1. Core rule

EPD² must distinguish the authoritative source of organizational power from the credentials and cryptographic assertions used to exercise it.

```text
OrganizationalAuthority / governed decision
!= signed runtime assertion
!= human credential
!= session
!= service credential
!= cryptographic key
!= voting authority
```

No token, certificate, regional issuer, KMS role or possession of secret material creates political or organizational competence by itself.

## 2. Trust hierarchy without universal super-key administration

The target trust model is hierarchical but scope-bounded:

```text
CENTRAL ROOT OF TRUST
HSM/KMS; highly protected; class-specific m-of-n custody
        |
        | signs / delegates bounded trust
        v
PLATFORM / PURPOSE INTERMEDIATES
        |
        +------------------+------------------+
        v                  v                  v
     BUND TRUST       LAND BERLIN        LAND BAYERN
                       BOUNDED ISSUER      BOUNDED ISSUER
                           |
                    exact scope ceiling
                           |
                    +------+------+
                    v             v
                 KREIS A       KREIS B
                    |
                    v
                   ORT
```

The central root/master key is not handed to Bund, Land, Kreis, Ort, ordinary platform administration or political organs.

The central root must not be the online hot path for every ordinary regional action. Normal runtime validation should rely on bounded trust material and current authority state so a temporary central HSM/KMS or network outage does not automatically stop all permitted regional work.

## 3. Technology neutrality

This requirement does **not** mandate DID, Keycloak, Vault, a specific cloud KMS, a specific HSM vendor, blockchain or a specific certificate profile.

A later provider/technology decision must prove the properties in this model. A technology name is not evidence that the properties exist.

## 4. Delegated regional trust

A Land may receive a delegated issuer/trust capability only through a governed policy and technical trust chain.

Minimum delegation fields/properties:

- issuer identity and key/version reference;
- exact parent trust reference;
- exact organizational scope;
- permitted descendant scopes;
- permitted credential/assertion classes;
- permitted audiences/purposes;
- maximum lifetime/TTL;
- `valid_from` / `valid_until`;
- maximum delegation depth;
- whether sub-delegation is allowed and under what ceiling;
- policy/rule version;
- activation decision/approval reference;
- revocation/status reference;
- audit/evidence reference.

A regional issuer must never be able to:

- mint or replace the central root/master key;
- mint Bund authority from a Land scope;
- mint another Land's authority;
- expand its own scope or delegation ceiling;
- create political office or restore suspended `OrganizationalAuthority`;
- issue unrestricted platform-root privileges;
- issue voting credentials, ballot authority, tally authority or voting trustee keys;
- bypass current authority, session, intervention or separation-of-duties checks.

## 5. Regional disconnected/degraded operation

Regional continuity must use an explicit **bounded autonomy window**, not indefinite offline trust.

During temporary loss of central connectivity, the region may continue only operations whose policy expressly permits disconnected/degraded execution and whose existing local trust material remains valid.

At minimum the disconnected policy must distinguish:

```text
ALLOW_WHILE_DISCONNECTED
DENY_WHILE_DISCONNECTED
REQUIRE_FRESH_CENTRAL_CONFIRMATION
```

The following are denied by default while disconnected unless a later governed assurance profile proves an equivalent safe mechanism:

- scope expansion;
- creation of high-impact privileged roles;
- root/intermediate trust changes;
- recovery of suspended political/organizational authority;
- new break-glass activation outside an explicitly rehearsed offline recovery ceremony;
- voting-key or voting-trust operations;
- cross-Land administration;
- irreversible destructive evidence operations.

The autonomy duration, freshness threshold and maximum offline credential/assertion lifetime are configuration governed by accepted INFRA/OPS assurance. V22 deliberately does not invent a numeric RTO/RPO or autonomy period.

## 6. OrganizationalAuthority runtime projection

`OrganizationalAuthority` remains the authoritative governed record. Where a signed runtime assertion/capability projection is used, it is a short-lived representation of that record, not a replacement for it.

A projection must bind at least:

- authority ID;
- subject/principal reference appropriate to the domain;
- exact office/role code;
- organization/scope;
- capabilities/actions;
- source rule/policy version;
- source election/appointment/decision reference where required;
- issued-at and expiry;
- issuer and trust-chain reference;
- assurance level/context where required;
- purpose/audience;
- authority/state version or equivalent freshness binding.

At consequential action time the runtime must still re-evaluate current authoritative state or an accepted bounded-freshness equivalent. A still-cryptographically-valid assertion must fail when the underlying authority is suspended/revoked or when an active restriction invalidates the requested action.

## 7. Security containment plane and deadlock prevention

Security containment must not depend on ordinary Identity administration being able to approve the same emergency action it is trying to contain.

Security may have narrowly pre-authorized technical powers to:

- quarantine sessions;
- terminate active privileged access;
- revoke/disable compromised human credentials;
- revoke/disable compromised service credentials;
- isolate a workload/network path;
- mark a key/issuer compromised and stop new use;
- trigger mandatory incident evidence and notification.

Security must not thereby gain authority to:

- remove or appoint a party office;
- create or restore `OrganizationalAuthority`;
- decide a disciplinary/political outcome;
- take over a regional administration;
- mint replacement root/admin/voting authority for itself;
- erase or rewrite evidence of the containment action.

Identity/Credential operators must not be able to silently undo an active security containment flag. Restoration follows the governed recovery/review path appropriate to the object.

## 8. Key custody and threshold policy

No universal hard-coded `3-of-5` or other single quorum is imposed for every key class.

Each critical key class must have an approved threshold policy defining:

- `m-of-n` or equivalent approval/execution threshold;
- eligible custodian class;
- incompatible roles;
- rotation of custodians;
- geographic/organizational separation where required;
- lost-custodian handling;
- compromise handling;
- backup/recovery material rules;
- secret exportability/non-exportability;
- ceremony evidence and independent witness/review requirements.

Root/KEK and other high-impact material should use non-exportable HSM/KMS handling where the accepted technology supports it.

Custodian rotation is required on policy schedule and after relevant events such as compromise, role termination, recovery ceremony or material trust-policy change.

## 9. Quorum-loss and root recovery ceremony

Loss of ordinary custodian quorum must not be solved by promoting one superadmin.

The target recovery model separates:

```text
governance authorization
!= recovery custody
!= technical execution
!= independent review
```

A quorum-loss recovery ceremony must define:

1. declaration and evidence of quorum loss;
2. freeze/containment of affected high-impact changes;
3. competent governance authorization for recovery;
4. independent recovery-custodian quorum distinct from ordinary single-operator access;
5. controlled use of protected offline/escrowed recovery material where adopted;
6. generation/activation of new trust/key versions rather than silent resurrection of compromised material;
7. mandatory invalidation/retirement of superseded material;
8. consumer/trust-store convergence proof;
9. mandatory full rotation of affected custody after recovery;
10. immutable ceremony evidence and independent post-review.

A Parteischiedsgericht may authorize, constrain or review a recovery when the adopted Satzung/Ordnung gives it that legal competence, but it does **not** hold platform master keys, become a Key Custodian or technically execute HSM/KMS recovery merely because it is a court.

## 10. Mandatory failure and recovery scenarios

The integrated design and runbooks must explicitly cover at least:

1. central KMS/HSM unavailable;
2. central network path unavailable / DDoS isolation;
3. ordinary Key Custodian quorum lost;
4. root/KEK/master-class key compromised;
5. platform/intermediate signing key compromised;
6. regional delegated issuer compromised;
7. mass human credential compromise;
8. Security Operator credential/account compromised;
9. Identity/Credential service unavailable;
10. region isolated from central infrastructure;
11. audit ingestion temporarily unavailable;
12. audit storage unavailable;
13. trust-store corruption or malicious rollback attempt;
14. expired delegated regional trust with central path still unavailable;
15. inconsistent current authority state across runtime replicas.

For every scenario the runbook must identify:

```text
DETECTION
-> CONTAINMENT
-> PERMITTED DEGRADED OPERATIONS
-> PROHIBITED OPERATIONS
-> RECOVERY AUTHORITY
-> RECOVERY EXECUTION/CEREMONY
-> TRUST/STATE CONVERGENCE
-> REQUIRED ROTATION/INVALIDATION
-> EVIDENCE
-> INDEPENDENT POST-INCIDENT REVIEW
```

## 11. RTO, RPO and autonomy targets

V22 requires explicit service-class objectives but does not invent values.

Before production readiness, INFRA/OPS must adopt and test, for each relevant trust/service class:

- RTO;
- RPO where stateful recovery applies;
- maximum disconnected regional autonomy window;
- maximum trust/assertion staleness;
- maximum time to revoke compromised credentials/keys;
- maximum time to restore minimum critical administration;
- maximum acceptable audit-ingestion delay before fail-closed/degraded behavior changes.

The targets must be justified by threat/risk and operational requirements and demonstrated by rehearsal, not merely written in a configuration file.

## 12. Immutable audit as a first-class trust service

Existing append-only/tamper-evident evidence requirements are strengthened by a future external anchoring obligation for high-impact governance/security/key events.

Target chain:

```text
application/API/security/key events
        -> append-only audit intake
        -> canonical event/evidence digest
        -> hash-linked batch/chain
        -> WORM / immutable retention store
        -> independent external timestamp / anchor / countersignature
        -> authorized audit / court / oversight verification
```

No Identity, Security, Platform, regional or political administrator may obtain `UPDATE`/`DELETE` authority over historical audit evidence merely because they operate the source system.

Where audit ingestion is temporarily unavailable, consequential operations must follow a defined fail-closed or bounded local-spool policy; silent unlogged privileged operation is prohibited.

Blockchain is neither required nor prohibited. The acceptance property is independently verifiable immutability/tamper evidence plus an external trust anchor, not use of a particular ledger technology.

## 13. Audit access and evidence export

Authorized independent auditors, Parteischiedsgerichte and oversight bodies must be able to obtain the evidence necessary for their lawful scope without receiving the operational capability they are auditing.

Evidence export must preserve:

- exact event/record IDs;
- time ordering and trusted timestamp/anchor proof where available;
- actor/authority/scope references according to privacy rules;
- reason codes;
- request/approval/execution separation;
- relevant key/credential/issuer version IDs without plaintext secret material;
- integrity proofs;
- chain/anchor verification material;
- retention/legal-hold metadata where applicable.

## 14. Voting-domain carve-out

Nothing in delegated regional trust permits ordinary regional or platform trust issuers to mint voting credentials, ballot authority, trustee authority, tally authority or identity-vote linkage.

Voting-specific resilience remains governed by the voting trust boundary and its own ceremonies. `FIR-TRUST-002` may supply shared infrastructure properties only where the voting-specific design explicitly accepts them without weakening isolation.

## 15. Control-plane and frontend requirements

CTRL/FRONT must distinguish visually and semantically:

- political/governance decision;
- organizational authority creation/change;
- signed runtime authority projection;
- credential/session issuance;
- technical API/runtime action;
- security containment;
- political/organizational suspension/revocation;
- recovery authorization;
- technical recovery execution;
- audit/review.

Diagrams and consoles should not use one undifferentiated arrow for these relationships. Logical/governance influence, credential issuance and technical execution must be visually distinguishable.

Regional administration surfaces should also show scoped separation for finance, casework, publication, membership administration and other consequential domains rather than implying one generic regional admin role.

## 16. Implementation placement

| Layer / owner                   | Required responsibility                                                                                                                                                   |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Organization/governance         | authoritative `OrganizationalAuthority`, exact scope, status, source decision/rule, suspension/revocation/restoration semantics                                           |
| API                             | current-state authorization, bounded signed projections where adopted, stale/revoked assertion refusal; exact API-02…06 placement remains stage-contract governed         |
| Service identity/API-03 lineage | compatible trust generations/revocation/replay/audience semantics without allowing service identity to become human/organizational authority                              |
| INFRA                           | HSM/KMS/PKI/trust-store topology, regional trust substrate, redundancy, offline recovery material protection, immutable/WORM audit substrate, external anchor integration |
| OPS                             | key/custodian rotation, incident response, quorum-loss recovery, regional isolation operation, RTO/RPO/autonomy policy and rehearsals                                     |
| CTRL                            | separate request/approve/execute/review consoles, trust/key status, recovery ceremonies, degraded-mode visibility, audit verification                                     |
| FRONT                           | clear authority/session/restriction/degraded-state presentation and no misleading implication that a valid login equals active office                                     |
| SEC                             | adversarial testing of issuer escape, stale assertion use, rollback, quorum bypass, containment bypass, recovery abuse, audit deletion/tamper and voting-boundary escape  |
| FINAL INTEGRATION               | prove central outage/degraded regional operation, recovery, convergence, revocation and external audit verification on the exact integrated baseline                      |

## 17. Relationship to existing requirements

`FIR-TRUST-002` complements and does not supersede:

- `FIR-GOV-004` — regional intervention controls;
- `FIR-GOV-005` — statutory competence and digital authority binding;
- `FIR-SEC-004` — credential/key lifecycle and separation of duties;
- `FIR-TRUST-001` — signature/seal/trusted timestamp framework;
- `FIR-INV-010` / OD-20 — document-history tamper evidence and need for an external anchor;
- `FIR-ROADMAP-007` — independent verification, resilience and incident-readiness work, including voting-specific resilience.

It closes no existing FIR merely by being recorded.

## 18. Acceptance criteria

`FIR-TRUST-002` is not complete until the integrated accepted baseline proves at least that:

1. the central root/master key is not exposed to political or regional administrators;
2. ordinary permitted regional work does not require a central master-key operation for every request;
3. a regional issuer cannot escape its scope, audience, TTL, delegation depth or credential-class ceiling;
4. disconnected operation automatically respects an explicit autonomy/freshness limit and cannot become indefinite trust;
5. a cryptographically valid stale assertion cannot exercise suspended/revoked authority;
6. Security can contain a compromised session/credential without obtaining power to remove/appoint political office;
7. Identity cannot silently undo active security containment;
8. no single ordinary custodian can bypass the threshold policy of a protected key class;
9. quorum loss has a rehearsed recovery path without creating a permanent superadmin;
10. Schiedsgericht/governance authorization is technically separated from key custody/execution;
11. root/intermediate/issuer compromise paths create new versions and prove old material rejected after cutoff;
12. regional isolation behavior has tested RTO/RPO/autonomy/freshness targets rather than unspecified assumptions;
13. audit history is append-only/immutable and high-impact evidence can be independently verified against an external anchor/timestamp/countersignature;
14. Identity/Security/Platform/regional admins cannot rewrite/delete historical audit evidence;
15. privileged operation cannot silently continue when required audit evidence cannot be durably captured;
16. voting-specific keys/credentials remain unreachable through generic regional delegation;
17. recovery produces durable reason-coded evidence, convergence proof and mandatory post-review;
18. all relevant CTRL/FRONT surfaces distinguish governance authority, credentials, security containment and recovery rather than presenting them as one admin power.
