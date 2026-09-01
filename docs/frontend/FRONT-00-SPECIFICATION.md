# FRONT-00 Specification

Status: **IMPLEMENTATION CANDIDATE**. FRONT-00 extracts a shared UI foundation from
`EPD_Front.zip` without activating business workflows. The confirmed repository
baseline is 0.9.0 and canon is 0.7.0; neither version is changed.

## Scope

- Shared tokens, shell, components, state patterns and non-production fixtures.
- Typed representative route metadata and a declarative ten-workspace catalogue.
- Fail-closed browser-storage and telemetry policy functions.
- Accessibility, responsive and architectural checks.
- Five representative migrations: public, cockpit, communication, form and table.

Excluded: real APIs, authentication/eID, voting, finance, legal case management,
messaging, assemblies, candidacy, administration and publication workflows.

## Invariants

Ten origins remain distinct. There is no global frontend session, global user
identifier or cross-workspace storage. WS-03 remains an independently deployable
target in future work and has no analytics, storage, persistent member identifier,
identity session, shared telemetry or reverse identity bridge.
