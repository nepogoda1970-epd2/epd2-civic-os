# ADR-038: PACK-09 compliance-service decomposition

## Status

`accepted`

## Date

2026-07-26

## Context

PACK-08 completed the organizational substrate: `Organization`,
`CivicSpace`, `OrganizationalUnit`, `OrganizationalRelation`,
`OrganizationalAuthority` and `OrganizationalScope`, with Bund /
Landesverband / Kreisverband modelled as effective-dated relations rather
than a fixed hierarchy. What that substrate does not yet carry is the
_legal_ layer a real party organization is obliged to operate: how long
each kind of record may be kept, who may destroy one and on what
evidence, what happens when litigation freezes a record, what personal
data the organization processes and under which recorded basis, how a
data-subject request is handled inside a deadline, and how an internal
dispute is arbitrated by somebody who is not a party to it.

Every one of those concerns shares three properties that pull them into
one bounded context:

1. they are all _control metadata about other services' records_, never
   the records themselves;
2. they are all scoped to exactly one organization, and crossing that
   boundary is the central security question;
3. they all produce evidence and audit trails rather than user-facing
   product surface.

They also share a hard constraint: none of them may become a correlation
point. A compliance context that could join a membership record to a
case, a case to a person, and a person to a ballot would undo the
identity/participation separation ADR-002 established and every
anti-correlation guarantee built on top of it.

## Problem

Where should the Compliance, Records Governance & Legal Workflows context
live, and what may it depend on?

Three sub-questions have to be answered together, because a wrong answer
to any one makes the others unsafe:

- One service or several? Retention, Legal Hold, the processing registry,
  governed cases, deadlines and arbitration could plausibly be two or
  three services.
- What may it read? Retention needs to know a record exists; a
  data-subject request needs to know a search happened; arbitration needs
  to know who holds which role.
- What must it never hold? The temptation in every compliance system is
  to accumulate "just enough" identity to make requests answerable.

## Considered options

- **Option A — extend existing services in place.** Put retention on
  `membership-service`, cases on `governance-service`, the processing
  registry on `transparency-service`. No new service directory.
- **Option B — three new services** (`records-service`,
  `legal-workflow-service`, `privacy-registry-service`), each with its
  own contracts and stores.
- **Option C — one new bounded service, `compliance-service`**, owning
  all six entity families, referencing organizational scopes by opaque
  UUID and importing only `epd2_core` and `epd2_audit_core`.

## Decision

**Option C.** PACK-09 introduces exactly one wholly new service,
`services/compliance-service`, owning:

| Family                             | Entities                                                                                                                             |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| Records governance                 | `RetentionPolicy`, `RetentionStartEvent`, `GovernedRecord`, `DisposalEligibility`, `DestructionAuthorization`, `DestructionEvidence` |
| Legal Hold                         | `LegalHold`, `LegalHoldScope`, `LegalHoldHistoryEntry`, `HoldApplicability`                                                          |
| Data catalog & processing registry | `DataAsset`, `ProcessingActivity`, `LegalBasis`                                                                                      |
| Governed cases                     | `ProceduralCase`, `CaseRoleAssignment`, `CaseDecision`, `AppealReference`, `ProceduralStep`                                          |
| Deadlines                          | `DeadlineDefinition`, `ProceduralDeadline`, `DeadlineHistoryEntry`                                                                   |
| Requests, disputes, cross-scope    | `DataSubjectRequest`, `DisputeParties`, `ConflictOfInterestDeclaration`, `CrossScopeAuthorityGrant`                                  |

Option A was rejected because it would scatter one security boundary
across four existing services: the "may this organization reach that
record" check would then exist in four places and drift. Option B was
rejected because the six families share one scope model, one authority
model and one audit pattern; splitting them would multiply the
cross-service edges ADR-008, ADR-012, ADR-017, ADR-022 and ADR-027 each
had to negotiate individually, for no ownership benefit — and the first
thing two of the three services would need is a synchronous read into the
third.

**Dependency rule.** `compliance-service` imports `epd2_core` and
`epd2_audit_core` and nothing else. It does _not_ import
`organization-service`: an organizational scope enters this service as an
opaque `organization_id: UUID` supplied by the caller, and the service's
job is to check equality and explicit grants, not to resolve hierarchy.
It does not import `identity-service`, `account-service` or
`credential-service` (PACK-09 required invariant 11), and it does not
import `voting-service`, `tally-service` or `delegation-service`
(invariant 12). Both absences are asserted structurally by
`tests/repository/test_service_boundaries.py` and, from the opposite
angle, by `tests/contract/test_ct00_09_vote_linkability.py`.

**No global person identifier.** A natural person appears in this service
only as a `CasePartyReference` — a random UUID minted per case by
`domain.mint_case_party_reference`, never reused across cases, never
derived from any identity, membership or account value, and with no
resolution path inside the service — or as an opaque authority reference
pointing at a role assignment, never at a person (invariant 1).

## Consequences

Easier: one place to audit the scope boundary; one reason-code registry
(`contracts/reason-codes/pack-09.yml`); one OpenAPI contract; one audit
pattern. A reviewer can read `application.py`'s guard helpers and know how
every boundary in the pack is enforced.

Harder: `compliance-service` is a comparatively large service, and future
packs that need part of it (PACK-10's finance retention, PACK-11's
document evidence) will have to add narrow, ADR-sanctioned read edges
rather than inheriting a smaller service wholesale. That is the cost this
ADR accepts, and it is the same shape of cost ADR-012 and ADR-027 already
accepted.

Explicitly assigned elsewhere and _not_ implemented here:

| Deferred to | What                                                                              |
| ----------- | --------------------------------------------------------------------------------- |
| PACK-10     | Party finance accounting, Rechenschaftsbericht, sponsorship and lobbying registry |
| PACK-11     | Document storage, evidence content, cryptographic document version chains         |
| PACK-12     | Privileged JIT/break-glass administration, DLP                                    |
| PACK-13     | Production database deployment, production event bus, schema registry service     |
| PACK-14     | Real IAM/eID, credential issuance                                                 |
| PACK-15/16  | Voting threat model, cryptographic voting                                         |
| PACK-17     | Production incident response                                                      |
| PACK-18     | User-facing applications                                                          |

Only typed references and interface boundaries necessary for PACK-09
itself exist for those: `evidence_references` and
`completion_evidence_reference` are opaque strings, and
`identity_verification_reference` is an opaque UUID.

## Security impact

Substantial and deliberate. This ADR's dependency rule is the pack's
primary security control: a service that cannot import identity cannot
accumulate it, and a service that cannot import voting cannot correlate
to it. The scope model (`RequestContext` plus `CrossScopeAuthorityGrant`)
is the second: there is no hierarchy-derived inheritance anywhere, so a
Bund-level actor is exactly as unprivileged against a Land's records as
any unrelated organization until that Land issues, and the caller
presents, a grant.

Reads of another organization's resource by id return the same
`VALIDATION_RECORD_NOT_FOUND` as a nonexistent resource, so a foreign id
cannot be used to probe for existence. The specific
`CROSS_ORGANIZATION_CASE_ACCESS_DENIED` / `CROSS_SCOPE_AUTHORITY_INVALID`
codes are reachable only by a caller who already asserted it holds
authority there.

## Data impact

Adds fifteen new entity schemas under `contracts/schemas/` and eight new
event payload schemas under `contracts/events/`, all owned by
`compliance-service`. No existing canonical entity's ownership, status set
or field list changes. `GovernedRecord.source_reference` is an opaque
pointer _into_ another service's data, never a foreign key that service
must honour, so no existing service gains an obligation.

## Migration impact

None. `compliance-service` starts empty; there is no existing compliance
data in the repository to migrate, and no other service's stored shape
changes. In-memory reference stores are used, matching every prior pack's
level (production persistence is PACK-13).

## Reversibility

Reversible with cost. The service is a leaf: nothing imports it, so it
could be removed or split without touching PACK-02 through PACK-08. The
contracts it publishes (`pack-09.yaml`, the schemas, the reason codes)
would need a compatibility ADR if a future round redistributed the
entities, exactly as ADR-006 Option B handled the analogous question for
reason codes.

## Related canon version

Authored against canon `0.7.0`. **No canon bump is proposed.** PACK-09
introduces no new canonical entity, status set or event that canon section
8, 19 or 20 must name: every entity here is compliance-side control
metadata owned by one service, and the eight events follow canon section
21's existing envelope contract unchanged. `CANON_VERSION` therefore stays
`0.7.0`, and no canon-owned file is touched by this round. Should a later
round need canon to name `GovernedRecord` or `LegalHold` as first-class
canonical entities, that requires its own canon amendment ADR in the shape
of ADR-013/ADR-018/ADR-023/ADR-028/ADR-037.

## Amendment (Architecture & Domain Framework 0.8.1, same 0.9.0 round)

The Framework 0.8.1 Roadmap Amendment supersedes this ADR's entity table
as the authoritative statement of PACK-09 scope. Nothing above is
withdrawn; four families are **added** to the same service, under the
same dependency rule:

| Family                         | Entities                                                                                                                                                                                  |
| ------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Legal-case substrate           | `LegalCase`, `JurisdictionDetermination`, `CaseParty`, `RepresentationMandate`, `Filing`, `Hearing`, `InterimMeasure`, `ProceduralDecision`, `Remedy`                                     |
| Recusal and conflict hooks     | `RecusalRecord`, `ReplacementAssignment`                                                                                                                                                  |
| Official notice trust boundary | `OfficialNotice`, `ServiceAttempt`, `NoticeEffectDecision`, `DeadlineTrigger` (see **ADR-043**)                                                                                           |
| Records and data protection    | `RecordClass`, `HoldPropagationRecord`, `DPIARequirementDetermination`, `DataProtectionImpactAssessment`, `ProcessingActivationDecision`, `TransferAssessment`, `ConsentWithdrawalRecord` |

The dependency rule is unchanged and now covers four more modules:
`casework.py`, `notices.py`, `dataprotection.py` and `references.py`
import `epd2_core` and nothing outside this service.
`tests/repository/test_service_boundaries.py` and
`tests/contract/test_ct00_08_identity_leakage.py` were both extended to
the new modules, because a forbidden field added to `casework.py` would
otherwise have escaped a check that only ever looked at `domain.py`.

**`references.py` is new and is the pack's outward interface.** Framework
section 13.1 requires PACK-09 to publish stable typed references for
PACK-10/11/19/21-24: `LegalCaseRef`, `DeadlineRef`, `NoticeEffectRef`,
`HoldRef`, `RecordClassRef` and their siblings. Every one carries an id
and the organizational scope it lives in, and nothing else — no name, no
status, no payload — so a downstream pack holding a reference can neither
infer state from it nor use it to reach into another organization. There
is no `PersonRef`, `UserRef` or `MemberRef` in that module and there must
never be one; `test_the_references_module_publishes_no_person_shaped_reference`
asserts their absence by name.

Two reason codes introduced earlier in this same unreleased 0.9.0 round
were **renamed in place** rather than duplicated:
`CROSS_ORGANIZATION_CASE_ACCESS_DENIED` → `CROSS_SCOPE_ACCESS_DENIED` and
`DECISION_AUTHORITY_MISSING` → `DECISION_AUTHORITY_DENIED`, both now
covering objects wider than a "case". The old exception class names remain
as aliases so no call site broke. Registering synonyms instead would have
left two codes meaning one thing, which is exactly what the pack's
"no duplicate codes under different names" constraint forbids.
