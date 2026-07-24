# PACK-05 — Decisions requiring explicit owner approval

**Status: all decisions resolved and canon updated — no open items
remain.** The project owner acted on ADR-016, ADR-017, ADR-018, ADR-019,
and ADR-020 on 2026-07-23; ADR-018's (and, for its repository-side
content, ADR-020's) canon-edit task was then carried out, as its own
separate step, later the same day. **No PACK-05 service code, schema,
OpenAPI file, or reason-code registry exists yet** — implementation of
`governance-service` itself remains separate and has not begun.

```text
sha256(docs/canonical/TZ-00-domain-event-canon.md) =
  61232dc8488f1dd96ea030fa3c41bd397c1c5cf1c7c8cee484bda0568d02c202
CANON_VERSION = 0.4.0
```

Canon has been updated for ADR-018's (amended) content: new section 19b
(Governance Context — `GovernancePolicy`, `GovernanceDecision`,
`TechnicalChallenge`, and the full integration of the already-canon-
defined `RoleAssignment`), new section 20.15 (twelve Governance events),
three new section 22 ownership-matrix rows, and section 23's reworded
`AdministratorRole` entry plus new forbidden-link entries. This was a
canon-only change — see section 3 below and
`docs/adr/ADR-018-canon-0.4.0-governance-context-additions.md`'s own
"Canon implementation" section for full detail.

## 1. Governance service decomposition (ADR-016) — accepted

One service, `services/governance-service`, owning `RoleAssignment`
(implementing existing canon 8.4), `GovernancePolicy`,
`GovernanceDecision`, `TechnicalChallenge`, is accepted exactly as
proposed. No amendment. Emergency/Crisis Override stays outside PACK-05;
the future physical-service relationship with any later Emergency/Crisis
pack remains explicitly unresolved, as proposed.

## 2. Cross-pack boundary and the ballot/result write question (ADR-017) — accepted

Accepted exactly as proposed, no amendment. Ballot invalidation: Option
B — `voting-service` remains the sole writer of `Ballot`, gains one new
command, `invalidate_ballot`, validating an approved `GovernanceDecision`
via a new read into `governance-service`. Result finality: no new
`tally-service` command, no new `ResultPublication` field — finality is
represented and queried entirely through `governance-service`'s own
`GovernanceDecision`/`get_finality_status`. Read edges
(`voting-service.get_ballot`, `tally-service.get_result_publication`,
`epd2_audit_core.list_by_target_types`, all already-existing functions)
and the one new reverse read edge
(`voting-service` → `governance-service.get_governance_decision`) are
accepted exactly as proposed.

## 3. Canon 0.4.0 Governance Context additions (ADR-018) — accepted with amendments

The three entities, twelve-event catalog, three ownership-matrix
additions, and the `AdministratorRole` resolution are accepted in
principle. Three amendments were required and are now incorporated
directly into ADR-018's own text (not tracked only here):

| #   | Amendment                                                | Resolution                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| --- | -------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | `TechnicalChallenge` submitter authorization             | The single, mandatory `submitted_by_role_id` field (which contradicted ADR-020's own rule that an eligible participant without a governance role may submit) is replaced with `submitter_authorization_type` (`participation_credential` \| `role_assignment`) and an opaque `submitter_authorization_reference`. No `Account`/`IdentityRecord`/person identifier/credential secret/`actor_id`/`RoleAssignment` UUID may appear in public output; the raw reference stays restricted; adjudicators gain no reverse path from a participation credential to the participant's identity. |
| 2   | Persisted finality outcome separated from derived status | `GovernanceDecision.finality_outcome` now stores only `final`/`invalidated`. A separate `FinalityStatus` read-model (`provisional`/`finality_blocked`/`final`/`invalidated`) is defined for `get_finality_status`'s return value; the two derived values are never stored on any `GovernanceDecision` row.                                                                                                                                                                                                                                                                             |
| 3   | `GovernanceDecision` immutability                        | `superseded` is removed from the _stored_ status enum. Stored statuses are exactly `proposed`, `approved`, `rejected`. A correction/reversal is always a new decision with `supersedes_decision_id`; whether a decision has been superseded is derived at query time, never a stored value.                                                                                                                                                                                                                                                                                            |

Every sub-item of Decision (D1–D6), the event catalog, and the
ownership-matrix additions are accepted as amended above — no sub-item
was rejected.

**Canon edit status:** performed, 2026-07-23, as its own separate,
dedicated task following this acceptance. The (amended) content described
in ADR-018 above is now part of
`docs/canonical/TZ-00-domain-event-canon.md` (section 19b, section
20.15, section 22's three new rows, section 23's reworded
`AdministratorRole` entry and new forbidden-link entries).
`canon_version` moved `0.3.0 → 0.4.0` — see the checksum block at the
top of this document.

## 4. Reason-code additions (ADR-019) — accepted

`contracts/reason-codes/pack-05.yml` with the specification's original
nine codes plus the four this ADR added
(`RESULT_FINALITY_BLOCKED_BY_OPEN_CHALLENGE`,
`RESULT_FINALITY_DETERMINATION_DUPLICATE`,
`GOVERNANCE_DECISION_SUPERSEDED`,
`TECHNICAL_CHALLENGE_SUBMITTER_INELIGIBLE`), plus reused generics, is
accepted exactly as proposed. No amendment. The exact final code list
remains subject to confirmation once `governance-service`'s real source
exists (ADR-019's own standing caveat, unchanged by acceptance).

## 5. Authority, roles, and challenge lifecycle (ADR-020) — accepted with amendments

| #   | Item                                       | Resolution                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | Amended? |
| --- | ------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------- |
| 1   | Two-actor approval scope                   | Accepted as proposed — required for `GovernancePolicy` activation, every `GovernanceDecision` approval, ballot invalidation, and result-finality determination.                                                                                                                                                                                                                                                                                                                                  | No       |
| 2   | Technical-challenge submission eligibility | Aligned with amended ADR-018: eligible participants use a valid, ballot-scoped `ParticipationCredential`; observers/reviewers use an active, in-scope `RoleAssignment`; submission still does not require a governance role; adjudication/approval still require one.                                                                                                                                                                                                                            | **Yes**  |
| 3   | Multiple-challenges rule                   | Accepted as proposed, verbatim, unchanged — each challenge gets its own adjudication; exactly one non-superseded aggregate finality determination per result; no finality while any challenge is unresolved; corrections use a new superseding decision, never mutation.                                                                                                                                                                                                                         | No       |
| 4   | No-challenge path                          | Accepted as proposed, unchanged — deadline expiry alone is never sufficient; an explicit two-actor decision is still required.                                                                                                                                                                                                                                                                                                                                                                   | No       |
| 5   | Role taxonomy and bootstrap                | The eight-`role_code` taxonomy is accepted exactly as proposed. The bootstrap mechanism — the one item flagged as open after the drafting round — is now fully specified: a dedicated deployment-time seed command (never the normal API), exactly two distinct initial actors, an immutable seed manifest/checksum/`AuditEvent`, permanent self-disabling after first successful run, no seeded actor may seed or approve its own assignment, every later grant uses the normal two-actor flow. | **Yes**  |

No sub-item of ADR-020 was rejected.

## 6. Not requiring a decision right now

Unchanged from the prior version of this document:

- Exact API shapes, JSON Schemas, and OpenAPI paths — implementation
  detail once `governance-service` implementation begins, not an owner
  decision.
- Frontend/UI work — out of scope per `docs/handover/PACK-05-SPEC.md`.
- The future Emergency/Crisis physical-service relationship (ADR-016) —
  explicitly deferred, not decided now.
- `docs/review/OPEN_QUESTIONS.md` item 10 (additive reason codes never
  folded back into canon) — flagged again by ADR-019, still not required
  for this pack's own Definition of Done.

## 7. What this acceptance round (and the follow-on canon update) does not authorize

Per this task's explicit instructions: no PACK-05 service directory,
implementation schema, OpenAPI file, or reason-code registry file was
created as part of the acceptance round or the later, dedicated
canon-update task. `services/governance-service` does not exist; no
PACK-02/03/04 source code was touched. Implementation of
`governance-service` remains a separate, later task, gated on the five
accepted ADRs and on the now-implemented canon 19b content, but not
authorized by either alone.
