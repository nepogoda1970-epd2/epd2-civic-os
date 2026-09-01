# FRONT-00 Accessibility

The baseline is WCAG 2.2 AA-oriented, not certified.

Automated coverage uses Testing Library rendered tests plus Playwright and axe
for the component showcase and all five migrated fixtures. It checks serious and
critical axe findings, keyboard skip-link behavior, single `h1`, header/main/footer
landmarks, labels and validation association, textual status, table semantics,
dialog semantics/focus lifecycle, and reduced-motion emulation.

Commands:

- `npm run test:components --workspace=frontend/web-shell`
- `npm run test:a11y --workspace=frontend/web-shell`
- `npm run test:browser --workspace=frontend/web-shell`

Implemented semantics include German document language, visible skip link,
heading hierarchy, native fields, explicit hints/errors, alert/live regions,
textual statuses, visible focus, 44 px targets, native dialog, captions and
header scopes, labelled scroll regions, and `prefers-reduced-motion`.

Automated scans cannot certify WCAG. Manual assistive-technology, 200%/400% zoom,
forced-colors, real content stress, and cross-browser review remain required.

The Mobile Application foundation additionally requires screen-reader support,
Dynamic Type or equivalent scalable text, sufficient touch targets, keyboard and
switch navigation where applicable, reduced motion, high contrast,
understandable error states, accessible authentication and voting-handoff flows,
and no critical gesture-only action. Current checks cover only the applicable
responsive-web baseline; no native accessibility certification is claimed.
