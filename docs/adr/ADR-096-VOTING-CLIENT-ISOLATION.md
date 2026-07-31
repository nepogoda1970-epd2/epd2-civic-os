# ADR-096 — WS-03 starts empty, leaves nothing behind, and shares nothing with any other origin

**Status:** proposed
**Round:** PACK-15 — Voting Trust Boundary, Eligibility & Credential Separation (specification and ADR only)
**Repository version:** unchanged at `0.14.0` · **Canon version:** unchanged at `0.8.0`

**NO CODE. NOT IMPLEMENTED. NOT A CANDIDATE. NOT A PASS. NOT PRODUCTION
READY. NOT LEGALLY ACTIVATED.**

> **Architecture correction (2026-07-31).** The decision below is unchanged
> and is not reversed. The open questions it left are now closed; the
> closures are recorded in `docs/packs/PACK-15/PACK-15-SPECIFICATION.md`
> §32 and summarised for this ADR in the note that follows. The
> authoritative register is now
> `EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER_UPDATED_V6.md`, carried at
> the canonical path, which preserves every prior entry and adds
> `FIR-OSS-001` … `FIR-OSS-006`.
>
> **The isolation now covers content as well as storage (`OD-P15-07`).**
> WS-03 already stored nothing; it now also **holds credential and assertion
> material in volatile page memory only**, never persisting, displaying,
> copying, downloading or printing it, with no programmatic clipboard write
> and `no-store` on every credential-, assertion- and status-bearing
> response. No APM agent, session-replay tool or error SDK may run inside
> WS-03, and error reporting is by reason code only.
>
> `pickup.redeem` is added as the single identity-side operation callable
> from inside WS-03; it is audience- and origin-bound and returns the
> assertion and nothing else. Everything ADR-088 and this ADR already
> prohibited remains prohibited, unchanged.

## Context

`FIR-INV-003` requires the Voting Client to have a separate origin, no
shared cookies, no shared localStorage, no shared IndexedDB, no shared
identity session, no analytics, no fingerprinting, no shared telemetry, a
one-time purpose-scoped handoff artifact and no persistent member
identifier. FRONT-00 declares `sessionSharing: forbidden` on every
workspace. PACK-14's cross-workspace matrix confirms WS-03 as the workspace
that receives no session at all, and ADR-088 defines the artifact that
carries a participant into it.

All of that is inherited and confirmed. What PACK-15 has to add is the
detail PACK-14 explicitly left to it — the browser-boundary controls,
because the server-side separation of ADR-089 and ADR-093 is worth nothing
if the browser reconstructs the correlation.

The failure modes here are ordinary and unglamorous: a shared error-
reporting SDK that attaches a user ID; a font loaded from a CDN that sees
the referrer; a service worker registered at the parent domain scope; a
`Referer` header carrying a context identifier back to the member area; a
cached credential-bearing response in a shared proxy; an analytics tag
added by someone who was told to instrument "all pages".

## Decision

**WS-03 is a separate origin that starts empty on every entry, shares
nothing with any other origin in either direction, and leaves nothing
behind on exit.**

Confirmed unchanged from PACK-14 and FRONT-00, and prohibited structurally
and completely: shared cookies; local identity cookies; localStorage;
sessionStorage; IndexedDB; cache storage used as identity or cross-context
state; shared service worker; shared identity session; parent-domain
session; analytics; fingerprinting; shared telemetry; shared
error-reporting identity; persistent member identifier; general account ID;
membership number; contact data; ordinary device identifier; reusable
cross-origin token; cross-workspace frontend state.

Added by this round:

| Control           | Requirement                                                                                                                                                        |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| CSP               | Own policy; `frame-ancestors 'none'`; **no third-party script origin at all**; no inline script without a nonce; no `connect-src` to any ordinary workspace origin |
| Allowed origins   | Explicit allow-list; the ordinary workspaces are not on it                                                                                                         |
| Redirects         | Targets from a fixed allow-list; never a caller-supplied raw URL; no open redirect                                                                                 |
| Referrer          | `no-referrer` on the entry navigation and on every navigation leaving WS-03                                                                                        |
| Cache             | `no-store` on every credential-bearing and status-bearing response; no shared cache entry keyed by anything participant-specific                                   |
| Service worker    | Not shared; none that persists participation state across contexts                                                                                                 |
| Error reporting   | Reason codes only — no identity, no credential value, no pseudonym, no stack containing either                                                                     |
| Return navigation | Carries no identity-bearing token **and no voting-side identifier**                                                                                                |

Two rules deserve emphasis:

1. **No third-party script origin at all.** Not a CDN, not a font service,
   not a tag manager, not a session-replay tool, not an APM agent, not an
   error SDK. Each is a party that observes a voting session, and the
   allow-list is empty rather than curated.

2. **Both directions matter.** A return navigation carrying a voting-side
   identifier back into the member area is as damaging as an outbound
   identity leak — it hands the identity side a voting-side handle, which
   is the same join from the other end.

## Consequences

**The Voting Client cannot be built like the rest of the frontend.** It
shares the visual baseline and shares no code path that carries identity
state. FRONT-PACK inherits this as a constraint on its architecture, not as
a styling note.

**Debugging WS-03 in production is deliberately hard.** No APM, no session
replay, no user-scoped error reports. Failures are diagnosed from reason
codes and aggregate signals. This is accepted.

**The Mobile App must open WS-03 in the system browser**, not a WebView —
PACK-14 already required this and ADR-088 already explained why; nothing
here relaxes it.

**Network-level correlation is not addressed** and is not claimed to be. A
participant reaching WS-03 from the same IP address they used in WS-02
minutes earlier is correlatable by anyone observing the network, and no
browser control changes that (`T-P15-10`, PACK-17).

## Alternatives rejected

**A subdomain with a scoped cookie.** Rejected: a parent-domain cookie is
one misconfiguration away, and "scoped" is a runtime property of a header.

**An iframe inside the member workspace.** Rejected: the embedding page
observes the frame's lifecycle and the participant's presence in it, and
`frame-ancestors 'none'` exists to make this refusal structural.

**A curated third-party allow-list for fonts and error reporting.**
Rejected: every entry is a party observing a voting session, and a
curated list is a list that grows.

**Reusing the member session for convenience during an outage.** Rejected:
isolation is not conditional on the weather.
