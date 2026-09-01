# ADR-082 — Authentication assurance and step-up are per-action, not per-login

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
> **Freshness and session-age values (OD-P14-04):** governed configuration
> with safe defaults, not constants and not canon —
> `low` 30 min idle / 7 d absolute, `substantial` 30 min / 24 h, `high`
> 15 min / 8 h; step-up freshness 15 min, ordinary official submission
> 60 min, security or contact change 15 min. Stricter is free; relaxing is
> a governed change; **no deadline can be configured away**, and no
> configuration may disable step-up, an audit obligation or a separation of
> duties.
>
> **Method ceilings:** a synced passkey and password-plus-MFA each cap at
> `substantial`, so neither satisfies a `high` action, and two capped paths
> do not add up to an uncapped one.

## Context

A single login is not a standing licence. Reading a personal dashboard and
approving a payment are not the same act, and a session that authorises
both equally has confused "who is this" with "may this happen now."

Canon 19d.8 already fixes the vocabulary, and PACK-14 is bound by it. It
names **five never-interchangeable concepts** — identity assurance,
authentication assurance, attribute freshness, session authentication time
and method, and provider reference — and fixes the assurance scale as
`none` / `low` / `substantial` / `high` for both
`IdentityRecord.identity_assurance_level` (19d.2) and
`AuthenticationContext.authentication_assurance_level` (19d.8). It also
places the _policy_ — `StepUpAuthenticationRequirement` — in
`eligibility-service`, evaluated **fail-closed** as a conjunction of every
applicable condition, with no "or" permitted.

## Decision

**PACK-14 reuses canon's existing four-value assurance scale and does not
invent a new one.** Where a NIST-style AAL vocabulary is convenient in
prose, it maps onto canon rather than replacing it:

| Informal name | Canon value   | Meaning                                                                   |
| ------------- | ------------- | ------------------------------------------------------------------------- |
| AAL-0         | `none`        | Unauthenticated                                                           |
| AAL-1         | `low`         | Authenticated by a single non-phishing-resistant factor                   |
| AAL-2         | `substantial` | Strengthened: multi-factor, or a single factor with compensating controls |
| AAL-3         | `high`        | Phishing-resistant, origin-bound, device-bound where required             |

Normative rules:

1. Every consequential action declares a **required assurance** and a
   **freshness window**. Both must hold at the moment of the act, not at
   the moment of login.
2. Step-up is **bound to a specific action and to a specific object
   version**. A confirmation obtained for version _n_ of an object is
   invalid for version _n+1_: if what the user approved changed, the
   approval did not survive it.
3. Step-up has an explicit timeout, an explicit cancellation path, a
   defined failed-step-up behaviour and an evidence record. A step-up that
   silently expires into a permitted action is a defect, not a convenience.
4. Evaluation is **fail-closed**, following canon 19d.8 exactly: a missing,
   expired or unresolvable authentication context is a refusal, never a
   default allow.
5. Assurance may be **downgraded** by events (credential removal, risk
   signal, elapsed time) without the session being destroyed; the session
   then simply cannot perform what it no longer satisfies.

## Consequences

The frontend must be able to interrupt any consequential flow with a
step-up and resume it without losing the user's work, and must show what
is being confirmed — including the object version. That requirement lands
in the frontend contract and in the forms layer, not as an afterthought.

Nothing here makes authentication into an electronic signature. That
boundary is ADR-085's neighbour and `FIR-TRUST-001`'s subject; PACK-14
defines authenticated confirmation and transaction-bound consent, and
explicitly does not claim either is a qualified signature.
