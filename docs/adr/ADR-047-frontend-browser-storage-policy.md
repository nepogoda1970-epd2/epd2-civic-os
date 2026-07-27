# ADR-047: Frontend browser-storage policy

- Status: Proposed
- Date: 2026-07-27

Browser storage is deny-by-default, origin-local and purpose-specific. Sensitive,
identity, credential and voting data are prohibited. Unknown use fails closed.
