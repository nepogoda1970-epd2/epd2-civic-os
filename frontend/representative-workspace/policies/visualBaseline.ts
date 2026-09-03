/**
 * The immutable FRONT-00/FRONT-01 design baseline, restated for the isolated
 * WS-04 build.
 *
 * WS-04 may not import the Member Workspace runtime, so it cannot import the
 * shared stylesheet either without creating the coupling the isolation rule
 * forbids. The tokens are carried here as literal values and asserted
 * byte-for-byte against `frontend/web-shell/app/globals.css` by a test and by a
 * validator gate. Changing a token in either place fails both, which is the
 * mechanical form of "a Design Change Decision is required".
 *
 * `FRONT-00-DESIGN-PRESERVATION.md` additionally fixes four deviations that
 * bind this workspace: fixture/disabled marking where leaving a control
 * active-looking would misrepresent backend state; a 3px focus ring and 44px
 * targets; status by text and marker rather than colour; and legal/authority
 * notices that state non-activation.
 */

export const INHERITED_DESIGN_TOKENS = Object.freeze({
  "--accent": "#5c3d3d",
  "--text": "#1f1f1f",
  "--muted": "#666",
  "--light-bg": "#f4f5f7",
  "--card-border": "#e2e0d8",
  "--soft": "#f0ede6",
  "--white": "#fff",
  "--green": "#0b8b4f",
  "--danger": "#9d2424",
  "--warning": "#775700",
  "--space-1": "0.25rem",
  "--space-2": "0.5rem",
  "--space-3": "0.75rem",
  "--space-4": "1rem",
  "--space-6": "1.5rem",
  "--space-8": "2rem",
  "--space-10": "2.5rem",
  "--radius-sm": "8px",
  "--radius-lg": "14px",
  "--shadow-raised": "0 12px 24px -8px rgb(0 0 0 / 7%)",
  "--content-wide": "1280px",
  "--content-reading": "760px",
  "--z-sticky": "50",
  "--z-overlay": "100",
  "--focus": "#175cd3",
} as const);

/** The four permitted deviations that constrain this workspace. */
export const PRESERVATION_RULES = Object.freeze({
  fixtureOrDisabledWhereBackendAbsent: true,
  focusRingPx: 3,
  minimumInteractiveTargetPx: 44,
  statusCarriesTextNotColourAlone: true,
  authorityNoticesStateNonActivation: true,
} as const);

export const DESIGN_CHANGE_DECISION_REQUIRED = true as const;

/** No Design Change Decision was raised for FRONT-05. */
export const FRONT05_DESIGN_CHANGE_DECISIONS = Object.freeze([] as const);

/** The shell class this workspace uses, from the accepted workspace policy. */
export const WS04_SHELL = "institutional" as const;
export const WS04_NAVIGATION_SOURCE = "mandate-navigation" as const;
