# PACK-11 — cross-pack boundaries

> The mirror of ADR-053, written from PACK-11's side now that PACK-11
> exists. ADR-055 and ADR-060.

## Ownership

| Concern                                                                                                                              | Owner                                  |
| ------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------- |
| Document bytes, authoritative versions, version chains, evidence content, chain of custody                                           | **PACK-11**                            |
| Signature and admissibility _determinations_                                                                                         | **PACK-11** (recorded, never computed) |
| Publication renditions and their citations                                                                                           | **PACK-11**                            |
| Organizational scope, units, relations, authority assignment                                                                         | PACK-08                                |
| Legal cases, procedural deadlines, official notices, notice legal effect, legal hold, retention schedules, destruction authorization | PACK-09                                |
| Party finance, the accounting register, the Rechenschaftsbericht                                                                     | PACK-10                                |
| Privileged/JIT/break-glass access, controlled search, DLP, governed export                                                           | PACK-12                                |
| Production database, event bus, schema registry                                                                                      | PACK-13                                |
| Identity, authentication, keys, external trust providers                                                                             | PACK-14                                |
| Ballots, votes, tallies, delegation                                                                                                  | PACK-15/16                             |
| Minutes _content model_, assemblies                                                                                                  | future assemblies package              |
| Decision register workflow                                                                                                           | future decision-register package       |
| Candidacy, nomination, admission                                                                                                     | PACK-19                                |
| Communication channels and delivery                                                                                                  | PACK-22                                |

## What PACK-11 consumes, and how

Only typed references, declared in `references.py`. **No imports.**

| From    | Reference type                            | What PACK-11 does with it                                                                                                              |
| ------- | ----------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| PACK-08 | `OrganizationScopeReference`              | Carries it on every record. Never interprets the hierarchy, inheritance or the six access modes.                                       |
| PACK-09 | `RecordClassReference`                    | Stores the binding. Never computes a retention period.                                                                                 |
| PACK-09 | `LegalHoldReference` / `LegalHoldBinding` | Records PACK-09's answer with the moment observed. Re-read before every destruction-relevant act, deliberately not cached across acts. |
| PACK-09 | `DestructionAuthorizationReference`       | The only thing that can permit a disposition. Stale if issued against a smaller version count.                                         |
| PACK-09 | `LegalCaseReference`                      | Makes a document _about_ a case. Asserts no procedural fact.                                                                           |
| PACK-10 | `FinanceRecordReference`                  | The mirror of PACK-10's `EvidenceReference`. Both directions exist because different services ask the question from different sides.   |

## What PACK-11 exports

`DocumentRef`, `DocumentVersionRef`, `EvidenceRef`, `EvidenceBundleRef`,
`PublicationRenditionRef`, `SignatureDeterminationRef`,
`AdmissibilityDeterminationRef` — each an identifier plus scope, plus only
the metadata a citation genuinely needs (version number and hash; bundle
digest; citation reference).

**No exported reference carries a status.** A status on a reference would
be a cached answer that outlives the version — and, for admissibility, the
procedure — it was true of. A consumer that wants the answer resolves the
determination and gets the staleness check with it.

## What deliberately did _not_ change

PACK-09's `references.DocumentRef`, `EvidenceRef`, `MinutesRef` and
`NoticeProofPackageRef`, and PACK-10's `references.DocumentReference` and
`domain.EvidenceReference`, are **left exactly as they are**. They are not
rewritten to import PACK-11's real types.

That is the decision, not an omission. Those placeholders exist to hold a
boundary; converting them into imports would turn a documented boundary
into a runtime edge that a refactor could quietly widen, and would give
`compliance-service` and `finance-service` a dependency their manifests do
not declare. A future pack that needs a real document read adds that edge
under its own ADR — which is how every earlier cross-pack edge in this
repository was introduced.

## The four requirements ADR-053 fixed, now closed

ADR-053 recorded that "until all four exist, PACK-10 records the reference
and the absence of the assertion — it does not simulate any of the four
with a local heuristic". All four now exist:

1. `application.resolve_document_reference` → existence and kind in scope;
2. `application.determine_signature_status` / `get_signature_status`;
3. `application.determine_admissibility` / `get_admissibility_status`;
4. `documents.PublicationRendition.citation_reference`.

PACK-10 is not modified in this round to consume them. Consuming them is a
PACK-10 decision, made under a PACK-10 ADR, at a time PACK-10 chooses.

## Structural isolation from voting

No entity, reference, payload or projection in `document-service` has a
read or write edge to `VoteEnvelope`, `Tally`, `Ballot`, `Delegation`,
`DelegationSnapshot` or `ParticipationCredential`, directly or through
scope authorization. `PROHIBITED_VOTING_KEYS` makes the absence enforceable
at every emission boundary, and
`test_privacy_boundary.py::test_the_package_declares_no_voting_field_anywhere`
makes it enforceable at the declaration level.

A minutes document may _record_ that a vote happened. It may never carry a
reference that could join a ballot to a person.
