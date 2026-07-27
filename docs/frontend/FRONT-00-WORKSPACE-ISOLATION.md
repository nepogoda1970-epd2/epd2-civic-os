# FRONT-00 Workspace Isolation

`foundation/workspaces.ts` declares WS-01 through WS-10 with unique placeholder
origins, route prefixes, shell variants, navigation sources, capabilities,
sensitivity, analytics, storage, session-sharing and activation metadata.
Placeholder domains are documentation only and are not deployment decisions.

Shared source components do not imply shared runtime state. Every entry sets
`sessionSharing: forbidden`. No common session provider or storage adapter exists.

## Voting Client

WS-03 is a separate origin and future separate build/deployable. Its policy is:
no shared or local cookies, localStorage, sessionStorage, IndexedDB, cache storage,
service worker, identity session, analytics, fingerprinting, telemetry, persistent
member identifier or reverse identity bridge. Only a future one-time,
purpose-scoped handoff artifact is allowed. No ballot or voting flow exists here.

## Mobile App channel

The Mobile App is not present in `WORKSPACES`; workspace and unique origin counts
remain ten. Its allowed catalogue scope is WS-02 plus explicitly user-facing
WS-05 request status. WS-04 and privileged WS-06 through WS-10 capabilities are
prohibited. For voting it may only open WS-03 in the system browser using the
declared one-time handoff. An embedded WebView, transferred member session,
persistent member identifier, and shared cookies/storage/analytics are
prohibited.
