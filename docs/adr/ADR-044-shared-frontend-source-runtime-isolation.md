# ADR-044: Shared frontend source with runtime workspace isolation

- Status: Proposed
- Date: 2026-07-27

Share presentational source components while retaining ten independent origin,
session, navigation and storage contexts. Shared source must never become a
shared runtime identity/session layer.
