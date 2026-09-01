# FRONT-00 Browser Storage Policy

Storage is deny-by-default and purpose-specific. Sensitive data, ballots,
identity data, secrets and credentials may never be placed in browser storage or
client logs. Cross-workspace storage and `Domain` cookies are prohibited.

`storageAllowed()` rejects every storage kind for WS-03, every sensitive/ballot/
identity purpose for all workspaces, IndexedDB by default, and every unknown or
non-approved combination. Preferences are allowed only in explicitly
`preferences-only` workspaces. No custom cryptography wrapper is introduced.

URL parameters must not carry identity or secrets. Service workers and cache
storage require a later origin-specific approval; sensitive responses use
`Cache-Control: no-store`.

For the future Mobile App, secure storage is restricted to minimal session
artifacts and plaintext high-assurance tokens are prohibited. There is no offline
cache for voting, privileged, or sensitive legal data and no offline
consequential action. Cookies, browser storage, authority state, privileged
sessions, and voting credentials are never shared as runtime state.
