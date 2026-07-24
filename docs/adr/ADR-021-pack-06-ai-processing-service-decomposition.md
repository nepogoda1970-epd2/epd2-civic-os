# ADR-021: PACK-06 AI Processing service decomposition

## Status

`accepted`

## Date

2026-07-24

## Owner decision

Accepted as proposed, 2026-07-24. Exactly one new service,
`services/ai-processing-service`, owning `AIProcessingRecord`
exclusively; Emergency/Crisis Override stays outside PACK-06; no model
provider is ever a system of record and no provider gains Civic OS
mutation authority — all as drafted, with no amendment. Actually creating
the service directory, its `pyproject.toml`, `src/`, and `tests/` remains
a separate, later implementation task, not authorized by this acceptance
alone.

## Context

`docs/handover/PACK-06-SPEC.md` section 11 identifies AI Processing as
the smallest-surface pack proposed so far — its entire canon footprint
is one already-defined entity, `AIProcessingRecord` (17.1), plus that
entity's own event catalog (20.12), extended per ADR-023. Canon section
22 already names the future canonical owner, "AI Accountability
Service" — this ADR fixes the concrete `services/` directory and
package name that implements it, mirroring exactly how ADR-016 fixed
`services/governance-service` for canon's "Permission / Role Service"
label and how `audit-core` implements "Audit Core".

## Problem

Without a decomposition decision, `AIProcessingRecord` has a
canon-declared owner in prose but no concrete service boundary, package
name, or confirmation that no other in-flight or future concern
(Emergency/Crisis, in particular) is silently folded into the same
service.

## Considered options

- Option A — one new service, `services/ai-processing-service`, owning
  `AIProcessingRecord` exclusively, with Emergency/Crisis Override kept
  fully outside this pack's scope.
- Option B — fold AI Processing into `governance-service`, on the theory
  that both are "authority-adjacent" contexts.
- Option C — split AI Processing across multiple services by use class
  (e.g. one service for summarization/drafting, a separate one for
  anomaly indication), on the theory that anomaly indication is
  "voting-adjacent" and the rest is not.

## Decision

**Option A, accepted as proposed by the project owner, no amendment.**

- Exactly one new service: **`services/ai-processing-service`**
  (Python package `epd2_ai_processing_service`), owning
  `AIProcessingRecord` exclusively — the sole writer of every
  `AIProcessingRecord` row, matching canon section 22's already-existing
  owner label ("AI Accountability Service") under this project's
  established convention that a service's directory/package name need
  not repeat that prose label verbatim (the same convention already
  used for `governance-service` implementing "Permission / Role
  Service" and `audit-core` implementing "Audit Core").
- **Emergency/Crisis Override remains excluded from this pack.** No
  `EmergencyAction` field, event, or command is proposed anywhere in
  this ADR or the ADRs that follow it (ADR-022 through ADR-025); the
  future physical-service relationship between a later Emergency/Crisis
  pack and either `governance-service` or `ai-processing-service`
  remains unresolved, exactly as ADR-016 left it unresolved for
  Governance.
- **No model provider is ever a system of record, and no external
  provider ever receives Civic OS mutation authority.**
  `ai-processing-service`'s own storage (`AIProcessingRecord`) is the
  only system-of-record this pack introduces; a model provider — whether
  self-hosted or third-party — never holds write access to any Civic OS
  storage, never receives an `actor_id` or credential capable of calling
  any other service's command, and never becomes an implicit second
  source of truth for anything this project already treats as canonical.
  This principle governs ADR-025's provider-abstraction interface
  (section 6 there) and is restated here as this ADR's own foundational
  constraint on the service boundary itself, not only as an
  implementation detail of a later ADR.

Option B is rejected: `AIProcessingRecord` and `RoleAssignment`/
`GovernancePolicy`/`GovernanceDecision`/`TechnicalChallenge` have no
canon-declared ownership overlap, and folding them together would blur
the "AI is advisory only, never an authority" boundary this pack's
entire safety model depends on (`docs/handover/PACK-06-SPEC.md` section 8) by co-locating advisory output alongside the service that actually
holds decision-making authority. Option C is rejected: canon defines one
entity, not several, and splitting a single-entity owner across
multiple services would multiply the cross-pack boundary surface
(ADR-022) for no canon-grounded reason — anomaly indication (section 4.5
of the specification) produces the same `AIProcessingRecord` shape as
every other use class, distinguished only by its `purpose_code` value,
not by a different owning service.

## Consequences

`services/ai-processing-service` becomes this project's sixth
independent `uv` workspace member (after `account`/`identity`/
`eligibility`/`credential`/`audit-core` (PACK-02),
`initiative`/`deliberation`/`moderation`/`voting`/`tally`/`delegation`
(PACK-03), `transparency-service` (PACK-04), and `governance-service`
(PACK-05)) once implementation begins — a separate, later task, not
authorized by this ADR's acceptance alone. `tests/repository/
test_service_boundaries.py` will gain a new service identity to test
against once code exists; `scripts/check_repository.py`'s
`REQUIRED_PATHS` will gain the new service's required files at
implementation time.

## Security impact

Confirms, at the decomposition level, that this pack introduces no new
authority-bearing service — `ai-processing-service` will hold no
capability to approve, reject, invalidate, revoke, or publish anything
on any other entity. The "no model provider is a system of record, no
provider gains mutation authority" rule is this ADR's own security-load-
bearing decision, load-bearing for ADR-025's provider-abstraction
interface (section 6 there).

## Data impact

No canonical entity's fields, statuses, or owner change under this ADR.
`AIProcessingRecord`'s canon-declared owner (section 22, "AI
Accountability Service") is unchanged; this ADR only fixes the concrete
implementing service. Canon field/status/event extensions to
`AIProcessingRecord` itself are ADR-023's own, separate decision.

## Migration impact

None — no `services/ai-processing-service` exists yet; nothing is being
moved or renamed from an existing service.

## Reversibility

Reversible with low cost at this stage (no code exists). Once
`ai-processing-service` holds real `AIProcessingRecord` data, splitting
it into multiple services or merging it into another would become a
migration-bearing change, the same reversibility profile every prior
pack's own service-decomposition ADR has had once real data exists.

## Related canon version

Authored against canon version `0.4.0`. Proposes no canon change itself
— `AIProcessingRecord`'s canon-declared owner (section 22) is already
"AI Accountability Service" and is unchanged by this ADR.
