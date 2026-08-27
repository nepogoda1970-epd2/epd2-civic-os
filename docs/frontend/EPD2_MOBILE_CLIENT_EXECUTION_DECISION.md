# EPD² Mobile Client Execution Decision

**Status:** PLANNED / NOT IMPLEMENTED  
**Date:** 2026-08-27  
**Ownership:** FRONT  
**Architecture effect:** none — MOBILE is not a new architecture layer

## Decision

EPD² may provide native mobile applications for iOS and Android as official client channels of the existing FRONT layer. MOBILE is not a new architecture layer, does not create a second backend, and consumes the same governed accepted server-side contracts as other user-facing clients.

Canonical layer sequence remains:

```text
DATA → API → INFRA → OPS → CTRL → FRONT → SEC
```

## Timing

Architecture/specification preparation may begin before API closure. This MOBILE-READINESS work may define the mobile journey inventory, API-contract mapping, authentication/passkey and step-up UX requirements, secure storage, device/session lifecycle, push/deep-link boundaries, offline behaviour, accessibility, privacy/telemetry boundaries, release/signing requirements, and the web/mobile feature matrix. It must not invent unaccepted API behaviour or claim implementation.

Full mobile application runtime development should normally begin only after API-06 has authoritative acceptance, `API = CLOSED`, the minimum INFRA/OPS preview environment exists, and `SYSTEM TRIAL PREVIEW — FIRST END-TO-END PROBNIK` has exercised the accepted API runtime sufficiently to stabilize client-facing runtime assumptions. Preview findings that materially affect client contracts must first be routed to and reconciled by the owning layer. The browser-first System Trial Preview is not blocked by the absence of a native mobile app.

## Mandatory boundaries

- no direct database access from mobile;
- no separate mobile-owned AuthN/AuthZ domain;
- no bypass of accepted Gateway/BFF/API boundaries;
- human authentication/session/assurance/step-up/recovery remains owned by API-02;
- service-to-service identity remains owned by API-03;
- domain authorization remains server-side;
- no global `user_id` or mobile-generated cross-domain person identifier;
- no client-side authoritative procedural decision;
- no client-side authoritative voting logic;
- WS-03 Voting Client isolation and purpose-scoped handoff remain intact;
- analytics, notifications, caches and device identifiers must not create a voter↔ballot correlation bridge.

## FRONT mobile sub-line

These are governed labels under FRONT, not new architecture layers and not FIR IDs.

### FRONT-MOBILE-01 — Mobile Client Architecture & Security Boundaries

**Control state:** `PLANNED / SPECIFICATION MAY PROCEED`

Establish the mobile client contract, journey inventory, platform/security boundaries, feature matrix, technology decision and acceptance plan.

### FRONT-MOBILE-02 — Mobile Application Runtime

**Control state:** `NOT_STARTED`

Implement the actual iOS/Android client against accepted runtime contracts after the timing conditions above are met.

### FRONT-MOBILE-03 — Mobile E2E & Release Readiness

**Control state:** `NOT_STARTED`

Prove production-like mobile journeys and iOS/Android release readiness before FRONT can close if mobile is included in the target release baseline.

## Technology

No framework is canonically locked by this decision. Because the existing frontend line is TypeScript/React-oriented, React Native + Expo is the current preferred candidate, subject to FRONT-MOBILE-01 verification of build/release, native capability, security and maintainability requirements.

A likely repository shape may be:

```text
apps/web
apps/mobile
packages/api-client
packages/contracts
packages/ui-tokens
packages/i18n
```

Shared code should prioritize contracts, validation, design tokens, API clients and terminology. Web and native UI components need not be forced into one-to-one reuse.

## Feature parity

Mobile does not automatically require one-to-one parity with every web/admin surface. FRONT-MOBILE-01 must define required mobile journeys, optional journeys, web-only administrative surfaces, functions prohibited on mobile where necessary, and safe handoffs between clients/workspaces.

High-value mobile journeys are expected to include authentication, Bürgerbereich/Member Core, participation, Programme/Programmwerkstatt, notifications, delegation where activated, representative/transparency surfaces, and access to voting availability/handoff without moving authoritative voting logic into the general mobile client.

## Integration and SEC

If native mobile is part of the target production release, FRONT must not close merely because the web client is complete. The governed mobile scope must have required implementation and evidence before `FRONT CLOSED`. `FINAL INTEGRATION` must include the exact mobile baseline and its real API/runtime journeys. Final `SEC` challenges that same exact integrated baseline, including the mobile client.

## Master Register disposition

No new FIR is created now. Existing Master requirements already govern the substantive cross-cutting obligations, including `FIR-UX-003`, `FIR-UX-004` (which explicitly includes mobile navigation and deep links), `FIR-UX-005`, `FIR-UX-006`, `FIR-ID-001`, `FIR-ID-002`, `FIR-INCLUSION-001`, and the existing privacy/security/voting-isolation requirements.

Native iOS/Android delivery is therefore an execution/channel decision under FRONT rather than a duplicate future requirement. If FRONT-MOBILE-01 discovers a genuinely new normative invariant not covered by the current Master, it must receive a new FIR ID through normal Master change discipline before implementation relies on it.

## No status promotion

This decision does not change the current primary stage, does not start FRONT-MOBILE-02, does not close FRONT, and does not claim mobile, production or security readiness.
