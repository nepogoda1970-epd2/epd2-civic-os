# New Module Guide

This guide describes how a future business module (service) should be added
to EPD² Civic OS. It does not itself add any business module — no business
module exists yet in CLAUDE-PACK-01.

## Before adding a module

1. Confirm the module and its owned entities are already listed in
   `docs/canonical/TZ-00-domain-event-canon.md` (section 22, "Матрица
   владения сущностями") and in `docs/architecture/data-ownership.md`. If
   not, an ADR is required first.
2. Confirm which canonical events (section 20 of the canon) the module will
   produce and/or consume.
3. Confirm the module does not require direct database access to another
   module's tables (`INV-03` of the canon).

## Where a new module lives

- Its own directory under `services/`.
- A `README.md` describing its purpose, its owned entities, and the events
  it produces/consumes.
- Any shared contract it exposes (OpenAPI, event schema, JSON schema) lives
  under `contracts/`, versioned.
- It must not import internals of another service directly.
- It may depend on `packages/python/epd2-core` or
  `packages/typescript/epd2-types` for shared, non-business infrastructure
  code only.

## Required test coverage

Per `docs/canonical/TZ-00-domain-event-canon.md`, section 27 ("Минимальные
contract tests"), every module must eventually pass the common contract
test suite: schema validation, unknown status rejection, forbidden
transition rejection, event idempotency, unsupported event version
rejection, missing permission rejection, audit creation, identity leakage
prevention, vote linkability prevention, rule freeze, AI human control, and
emergency stop behavior — as applicable to that module.

## Out of scope for this guide

This guide does not authorize creating any business module in the current
package (CLAUDE-PACK-01). It exists so that a future package has a
documented starting point.
