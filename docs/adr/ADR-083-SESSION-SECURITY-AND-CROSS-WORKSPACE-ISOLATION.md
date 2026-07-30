# ADR-083 — Session security and cross-workspace isolation

**Status:** proposed
**Round:** PACK-14 — Identity, Authentication & Account Security (specification and ADR only)
**Repository version:** unchanged at `0.13.0` · **Canon version:** unchanged at `0.8.0`

**NO CODE. NOT IMPLEMENTED. NOT A CANDIDATE. NOT A PASS. NOT PRODUCTION
READY. NOT LEGALLY ACTIVATED.**

> **Architecture correction (2026-07-30).** The decision below is unchanged.
> The open questions it left are now closed; the closures are recorded in
> `docs/packs/PACK-14/PACK-14-SPECIFICATION.md` §29 and summarised per ADR
> in the note that follows.
>
> **Session model status (OD-P14-05):** `SessionRecord` is a PACK-14
> **service-level aggregate**, not a canonical entity, following PACK-12's
> `PrivilegedSession`. Its events use PACK-13's canonical envelope
> unchanged.
>
> **Cross-origin bootstrap (OD-P14-06):** each protected workspace runs its
> **own** authentication ceremony; `identity-service` returns a single-use,
> short-lived, **audience-bound** authorization response; the workspace
> mints its **own origin-local session** from it. No parent-domain cookie,
> no cross-origin reusable token, no shared browser-storage identity, and
> crossing a higher-risk boundary requires new authentication or step-up.
> **This is not SSO and must not be described as a shared application
> session.**
>
> **Ownership (OD-P14-02):** `identity-service` owns Session Security as an
> internally separated module with its own storage boundary. No parallel
> authentication service exists.

## Context

FRONT-00 declares ten workspaces (WS-01 … WS-10) with distinct origins and
`sessionSharing: forbidden` on every entry. WS-03, the Voting Client, goes
further: no shared or local cookies, no localStorage, sessionStorage,
IndexedDB, cache storage or service worker; no shared identity session, no
analytics, no fingerprinting, no telemetry, no persistent member
identifier, no reverse identity bridge.

PACK-14 is the round that issues the sessions those declarations constrain.
A single "log in once, use everywhere" cookie scoped to a parent domain
would silently void all ten declarations in one line of configuration.

## Decision

**A session is scoped to a workspace and never spans a risk boundary.**

1. Sessions are issued per workspace scope. No cookie is issued at a
   parent domain that would be sent to sibling workspaces. No token is
   reusable across origins.
2. **Rotation is mandatory** after authentication, after step-up and after
   any privilege change. Session fixation is prevented structurally rather
   than detected.
3. Both an **idle timeout** and an **absolute timeout** exist. There is no
   infinite session and no silent indefinite refresh.
4. Revocation exists at two granularities — one session and all sessions —
   and a revoked session **cannot silently refresh**. Credential compromise
   invalidates the sessions that credential could have produced.
5. If refresh tokens are used, they rotate, and **reuse of a rotated token
   is treated as replay**: it revokes the family and raises a security
   event rather than issuing a new token.
6. No session identifier appears in a URL. Cookies carry `Secure`,
   `HttpOnly` and an appropriate `SameSite`; a CSRF strategy is required
   for every state-changing request; origin binding is applied where the
   flow allows it.
7. Crossing from a lower-sensitivity workspace to a higher-sensitivity one
   requires **reauthentication**, not token exchange.
8. **No browser storage is an identity bridge.** localStorage,
   sessionStorage, IndexedDB and shared analytics identifiers are
   prohibited as carriers of session or identity between origins.

## Consequences

Users will authenticate more than once across workspaces. That is the
intended cost, and the design must make it fast and comprehensible rather
than trying to avoid it — an SSO cookie that removes the friction removes
the isolation with it.

Operationally, a session inventory becomes a user-facing feature: people
need to see their active sessions and devices and end them. That surface
is specified in the frontend contract and in the forms layer.
