# FRONT-00 Known Limitations

- Origin placeholders are not production domains.
- WS-03 remains an isolation-ready configuration, not a deployed artifact.
- No authentication, eID, API, persistence, analytics, messaging, voting,
  finance, legal workflow, or production telemetry exists.
- Fixture identity, status, dates, content, and counts are static layout content.
- Axe and rendered tests do not replace manual assistive-technology,
  cross-browser, zoom, contrast, or legal review.
- Playwright screenshot baselines require explicit human review against the
  original HTML before creation or update; CI never updates them.
- The bundled browser fallback is test-only. A standard CI runner may instead
  use its installed Playwright-compatible Chromium.
- Authority and organization/record scope are declarative, not runtime-enforced.
- The full CSV page/route catalogue remains normative; only five source pages are
  migrated in FRONT-00.
- No PWA or native Mobile App exists. Push, device registration, deep links,
  authentication, handoff, voting, remote logout/revocation, and native
  accessibility remain future gated implementations.
- The corrected Target Frontend Architecture ZIP supplied for this correction
  does not include the referenced
  `EPD2_Mobile_Application_Profile_0.8.2.csv`; the typed catalogue follows the
  approved profile text, and later CSV traceability remains open.
