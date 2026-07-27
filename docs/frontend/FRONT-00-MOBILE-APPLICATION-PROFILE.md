# FRONT-00 Mobile Application Profile

Status: foundation requirement; inactive pending relevant PACK and activation
gates. This document does not claim a native app, PWA, production control, or
mobile accessibility certification.

## Client-channel model

`EPD² Mobile App` is an additional client channel, not a workspace, origin,
institutional role, or backend authority. The registry remains exactly WS-01
through WS-10 on ten origins. The app is primarily a future client for WS-02
Member Application capabilities. Its only optional WS-05 scope is limited
citizen-facing functionality such as citizen-office request status. It is not a
universal interface.

Citizen-office request submission, routing, status, and caseflow belong directly
to PACK-33, Citizen Office Routing & No-Wrong-Door Caseflow. Accordingly, the
only mobile-exposed capability in this foundation,
`citizen-office-request-status`, is scoped to WS-05 and activation-gated by
PACK-33. PACK-23 and PACK-29 remain upstream prerequisites through the PACK-33
dependency chain; neither replaces PACK-33 as the direct capability owner.
PACK-29 capabilities are not exposed through WS-05.

The typed source of truth is
`frontend/web-shell/foundation/mobile-application-profile.ts`. Every catalogue
entry records profile ID, client channel, workspace scope, capability decision,
session/storage/handoff/offline/notification policies, security gate, dependent
PACK, and inactive activation status.

Allowed future groups include member profile, initiatives, deliberation,
delegation, programme participation, neutral notifications, protected messages,
candidacy, assemblies, user-facing appeals, and explicitly gated WS-02 or
citizen-facing WS-05 functions. Full interfaces for WS-04 and WS-06 through
WS-10 are prohibited, as are privileged/universal administration,
certification, tally administration, legal decisions, and security
administration.

## Voting handoff

The fixed sequence is:

1. Mobile App requests a one-time, short-lived, purpose-scoped artifact bound to
   one voting event.
2. Mobile App opens the system browser.
3. The browser opens the separate WS-03 Voting Client origin and establishes a
   separate voting session.
4. Voting completes or is cancelled.
5. WS-03 clears its voting context and returns safely to the app with only
   `completed`, `cancelled`, `expired`, or `failed`.

Voting inside the app and embedded WebViews are prohibited. The member session
and persistent member identifier are never transferred. The app and WS-03 share
no cookies, localStorage, IndexedDB, analytics, fingerprinting, or identity
session. The handoff contains no user selection. The signed or one-time return
contains no ballot reference or vote content. Correlation metadata is minimized;
intermediate tally remains unavailable. FRONT-00 implements no handoff API,
deep link, credential, authentication, or voting action.

## Push and security

Push payloads are neutral minimal routing/status notices. They contain no
political preference, voting content, legal-case text, or sensitive membership
data. Full content requires authenticated server retrieval. A push provider is
not trusted storage, and FRONT-00 connects no provider.

Before activation, the app requires minimal secure session storage, no plaintext
high-assurance tokens, server authentication independent of biometric unlock,
remote logout, device/session inventory and revocation, and server-validated
deep links. Consequential offline actions and offline caches of voting,
privileged, or sensitive legal data are prohibited. Clipboard, screenshot, and
OS-sharing behavior require separate governance. Political-preference analytics
and PII, tokens, ballot data, or legal content in crash logs are prohibited.

## Delivery and source sharing

The required order is responsive WS-02 web, then a PWA only for non-critical
capabilities, then a native app only after API and security profiles stabilize.
FRONT-00 introduces no React Native, Flutter, Capacitor, service worker, or
native project.

Design tokens, schemas, generated API types, accessibility patterns, and
non-authoritative UI components may later be shared as source. Cookies, browser
storage, authority state, privileged sessions, and voting credentials must never
be shared as runtime state.

## Mobile accessibility foundation

Activation requires screen-reader support, scalable text/Dynamic Type,
sufficient touch targets, keyboard and switch navigation where applicable,
reduced motion, high contrast, understandable errors, accessible authentication
and handoff flows, and no critical gesture-only actions. FRONT-00 validates the
applicable responsive-web foundation only; native manual and certification gates
remain open.

## Traceability note

The supplied corrected Target Frontend Architecture archive does not contain the
referenced `EPD2_Mobile_Application_Profile_0.8.2.csv`. This profile implements
the approved Mobile Application Profile and the accompanying correction
requirements directly. A later source CSV comparison remains a documentation
traceability gate and cannot activate or broaden the app.
