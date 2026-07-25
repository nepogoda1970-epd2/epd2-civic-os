# ADR-001: Use a modular monorepo for the initial development stage

## Status

Accepted for repository skeleton v0.1.0

## Date

2026-07-19

## Context

EPD² Civic OS will eventually consist of many independent bounded-context
services (Identity, Eligibility, Credential, Organization, Initiative,
Deliberation, Moderation, Voting, Tally, Delegation, Transparency,
Governance, Audit Core — see `docs/canonical/TZ-00-domain-event-canon.md`,
section 5). At the current stage (CLAUDE-PACK-01), none of these services
exist yet; only a repository skeleton is being created.

## Problem

Choose a repository strategy for the initial development stage that
supports strict module boundaries now, without prematurely committing to a
multi-repository or fully distributed deployment model before any business
logic exists.

## Considered options

- Option A — one repository per future service, from day one.
- Option B — a single modular monorepo with hard module boundaries and no
  cross-module imports, service extraction deferred to when a service
  actually needs independent deployment.
- Option C — a single unstructured repository with no enforced boundaries.

## Decision

Use a modular monorepo for the initial development stage (Option B):

- monorepo at the current stage;
- hard boundaries between modules;
- direct imports between future services are forbidden;
- future extraction of individual services into independent repositories
  remains possible without redesign;
- shared packages (`packages/python/epd2-core`, `packages/typescript/epd2-types`)
  contain only infrastructure types and utilities, never business logic.

## Consequences

Development stays coordinated (single source of truth for contracts, shared
CI, single version of the canon) while every future service is designed so
it can be extracted later without a rewrite. Enforcing "no direct imports
between future services" requires ongoing discipline and repository-level
checks (see `scripts/check_repository.py`), since a monorepo makes it
technically easy to violate boundaries by accident.

## Security impact

None at this stage — no business logic or credentials exist yet.

## Data impact

None at this stage — no canonical entities are persisted yet. This ADR only
establishes structural boundaries for their future implementation.

## Migration impact

None — this is the initial repository structure.

## Reversibility

Reversible. Individual modules can be extracted into separate repositories
later, since this ADR already requires that no future service directly
import another future service's internals.

## Related canon version

Authored against canon version `0.1.0`. Does not propose any canon version
bump.
