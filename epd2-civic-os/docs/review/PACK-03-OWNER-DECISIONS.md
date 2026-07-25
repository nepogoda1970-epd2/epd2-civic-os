# PACK-03 — Decisions requiring explicit owner approval

**Status: all decisions resolved — no open items remain.** The project
owner acted on ADR-005, ADR-006, ADR-008, and ADR-009 on 2026-07-22, and
on the follow-on ADR-010 (the canon change ADR-009 item 13 required)
later the same day.

- `docs/adr/ADR-005-pack-03-service-decomposition.md` — **accepted**, as
  proposed.
- `docs/adr/ADR-006-pack-03-reason-code-additions.md` — **accepted**, as
  proposed.
- `docs/adr/ADR-008-pack-03-pack-02-integration-boundary.md` —
  **accepted**, as proposed.
- `docs/adr/ADR-009-voting-delegation-quorum-defaults.md` — **accepted
  with amendments** to items 13 and 14 (section 4 below); items 1–12 and
  15 accepted as proposed.
- `docs/adr/ADR-010-ballot-challenge-window-canon-addition.md` —
  **accepted with an amendment clarifying finality** (section 6 below).
  **Implemented**: the canon has been edited — `canon_version` is now
  `0.2.0`.

```text
sha256(docs/canonical/TZ-00-domain-event-canon.md) =
  5ed52c3a6a94e821323616ac369595fd364a71115cf5c1c6763d8edb51a6044a
CANON_VERSION = 0.2.0
```

Per canon section 26, PACK-03 service directories and implementation
code may now be created consistent with all five accepted ADRs above,
including the new canon fields. No PACK-03 service directory has been
created yet — implementation itself remains a separate, later task,
distinct from this governance round.

## 1. Service decomposition (ADR-005) — accepted

The six-service split (`initiative-service`, `deliberation-service`,
`moderation-service`, `voting-service`, `tally-service`,
`delegation-service`) is accepted exactly as proposed. No amendment.

## 2. Reason-code registry mechanism (ADR-006) — accepted

A new, separate `contracts/reason-codes/pack-03.yml` registry (mirroring
PACK-02's `pack-02.yml`) is accepted exactly as proposed. No amendment.
`docs/review/OPEN_QUESTIONS.md` item 10 remains open and unrelated to
this acceptance — still not required for PACK-03's own Definition of
Done, still available for the owner to revisit later.

## 3. Cross-pack integration boundary (ADR-008) — accepted

The enumerated PACK-03 → PACK-02 dependency edges, the one-way dependency
rule, and deferring a real message bus (Option C in ADR-008) are all
accepted exactly as proposed. No amendment.

## 4. Voting, delegation, quorum, tie, challenge, and finality defaults (ADR-009) — accepted with amendments

Items 1–12 and 15 accepted as proposed. Items 13 and 14 accepted only in
amended form — the amended text below is now the operative decision, not
the original proposal (both are kept in ADR-009 itself for the record).

| #   | Question                                                | Resolved decision                                                                                                   | Amended? |
| --- | ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- | -------- |
| 1   | Can a participant change their vote before close?       | Yes                                                                                                                 | No       |
| 2   | Which choice counts if the vote changed?                | Latest valid envelope before `closes_at`                                                                            | No       |
| 3   | Is abstention a distinct option?                        | Yes — explicit `BallotOption`                                                                                       | No       |
| 4   | Which voting methods are in the pilot?                  | Single-choice / yes-no only                                                                                         | No       |
| 5   | Is quorum required for every procedure?                 | No — per-ballot opt-in                                                                                              | No       |
| 6   | Who may create a ballot?                                | `RoleAssignment`-gated, scoped to the `CivicSpace`                                                                  | No       |
| 7   | Who approves final ballot parameters?                   | A second, distinct authorized actor (separation of authority)                                                       | No       |
| 8   | Is delegation enabled in the first pilot?               | Entity fully implemented; disabled by default per ballot                                                            | No       |
| 9   | Maximum delegation depth?                               | 1 (no re-delegation chains) for the pilot                                                                           | No       |
| 10  | Can a delegator override their delegate for one ballot? | Yes, if their own vote arrives before snapshot resolution closes                                                    | No       |
| 11  | How are ties handled?                                   | No silent tie-break — recorded as an explicit `tie_no_decision` outcome                                             | No       |
| 12  | When is a result final?                                 | After publication plus the challenge window (item 13) elapses unchallenged                                          | No       |
| 13  | Technical-challenge deadline?                           | 72 hours default, configurable per ballot; canon fields implemented now (ADR-010, canon 0.2.0), not deferred        | **Yes**  |
| 14  | Who may invalidate a ballot?                            | No PACK-03-reachable invalidation command; canonical `invalidated` status/validation only; Governance owns the rest | **Yes**  |
| 15  | What audit-package data is published openly?            | Aggregate counts + hash-only audit-chain proof, never vote contents                                                 | No       |

## 5. Note on items previously flagged as higher cost to change later

Item 3 (abstention modeling) and item 9 (delegation depth) are accepted
as proposed and remain flagged in ADR-009's own Reversibility section as
worth extra care once real ballots exist under them — no action needed
now, just awareness during implementation.

## 6. Canon change for item 13 (ADR-010) — accepted with amendment, implemented

`docs/adr/ADR-010-ballot-challenge-window-canon-addition.md` proposed the
canon minor-version addition item 13 required. The owner accepted the two
fields exactly as proposed and additionally required an explicit
finality clarification, now recorded in both ADR-010 and the canon text
itself (canon section 15.6):

- `Ballot.challenge_window_hours` (optional integer; repository default
  72 hours; configurable per ballot) and `ResultPublication.challenge_deadline_at`
  (`published_at` + the applicable challenge window) are now part of the
  canon, version `0.2.0`.
- **Finality clarification (the amendment)**: expiry of
  `challenge_deadline_at` is necessary but not sufficient for finality.
  PACK-03 must not automatically declare a `ResultPublication` final
  merely because the deadline elapsed. Until a canonical or explicitly
  approved technical-challenge registration/adjudication mechanism
  exists, `ResultPublication` remains provisional/finality-pending at the
  application level — no hidden, pack-local challenge process may be
  invented to fill that gap. The future challenge mechanism requires its
  own ADR before real production finality can be enabled. Tests may
  verify deadline calculation and provisional-window behavior only, never
  claim end-to-end challenge adjudication or automatic finality.
- **What remains deliberately unproposed**: a stored finality-status
  field, a canonical challenge-submission entity, and any new canonical
  event for finalization. These are explicitly out of scope for ADR-010
  and require their own, separate future ADR if ever needed.

This was the **first edit to `docs/canonical/TZ-00-domain-event-canon.md`'s
own text** in this project's history — every prior addition (PACK-02's 21
reason codes included) went through a pack-level registry file
specifically to avoid touching the canon document. `canon_version` moved
`0.1.0 → 0.2.0`, mirrored across `docs/canonical/canon-version.json`,
`packages/python/epd2-core/src/epd2_core/version.py`,
`packages/typescript/epd2-types/src/version.ts`, with both
version-consistency unit tests updated and `scripts/verify_versions.py`
passing.

No open item remains from this canon change — PACK-03 implementation of
the challenge-window/finality behavior (ADR-009 items 12–13) may now
proceed on the same footing as everything else accepted in sections 1–4
above, once implementation itself begins (still not started — section
"Status" above).

## 7. Not requiring a decision right now

Unchanged from the prior version of this document:

- Exact API shapes, JSON Schemas, and OpenAPI paths — implementation
  detail once the above are accepted, not an owner decision.
- Cryptographic vote-secrecy mechanism — `docs/handover/PACK-03-SPEC.md`
  section 10 already scopes PACK-03 to the _structural_ linkability
  guarantee (CT-00-09) only; a real cryptographic scheme is its own,
  later, separate proposal if ever required.
- Frontend/UI work for any PACK-03 service — unchanged, out of scope.
