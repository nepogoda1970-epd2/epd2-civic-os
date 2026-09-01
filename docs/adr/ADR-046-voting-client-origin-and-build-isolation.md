# ADR-046: Voting Client origin and build isolation

- Status: Proposed
- Date: 2026-07-27

WS-03 requires a separate origin and future separately deployable artifact with
no shared identity session, storage, analytics, telemetry or persistent member
identifier. Handoff is one-time, purpose-scoped and has no reverse identity bridge.
