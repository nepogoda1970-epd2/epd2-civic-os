# FRONT-00 Visual Regression

The visual baseline is derived page-by-page from the original `EPD_Front.zip`
sources:

| Source                       | Migrated route                       | Approved screenshot stem |
| ---------------------------- | ------------------------------------ | ------------------------ |
| `index.html`                 | `/foundation/examples/public`        | `index`                  |
| `intern/dashboard.html`      | `/foundation/examples/cockpit`       | `dashboard`              |
| `intern/kommunikation.html`  | `/foundation/examples/communication` | `kommunikation`          |
| `buerger-login.html`         | `/foundation/examples/form`          | `buerger-login`          |
| `struktur/abstimmungen.html` | `/foundation/examples/table`         | `abstimmungen`           |

Playwright records and compares full-page PNGs for mobile (Pixel 7), desktop
(1440x900), and wide desktop (1920x1080). Checked reference files belong under
`frontend/web-shell/tests/browser/front00.browser.spec.ts-snapshots/`; Playwright
adds the project/platform suffix. The candidate banner alone is narrowly masked
with its own background color. No page section is masked.

Comparison uses a per-pixel threshold of `0.2` and maximum differing pixel ratio
of `0.015`. This is intentionally strict: typography, header/navigation, spacing,
cards, buttons, forms, lists, major sections, and principal positions are in
scope.

To create a baseline, a reviewer must first open the corresponding original HTML
at the same viewport, compare source and migrated composition side-by-side, then
run:

`npm run test:browser:update --workspace=frontend/web-shell`

Snapshot updates are never run by CI and must be reviewed as image changes. CI
runs:

`npm run test:visual --workspace=frontend/web-shell`

Allowed differences are only the items in
`FRONT-00-DESIGN-PRESERVATION.md`: candidate banner, visible focus, minimum touch
targets, textual statuses, semantic corrections, and responsive overflow fixes.
An accessibility change must be reviewed, documented, and narrowly masked only
when it is nondeterministic; accessibility is not a reason to mask a full page.

## Approved candidate baseline

The candidate contains 15 reviewed PNG files: five fixture stems for each of the
`mobile`, `desktop`, and `wide` projects. Originals and migrations were opened
at corresponding viewports and reviewed for header, navigation, principal
sections, typography hierarchy, spacing, cards, buttons, forms, lists/tables,
and primary content positions. Only the documented candidate-status,
accessibility, and responsive corrections were accepted.

The browser runtime resolves its bundled fontconfig file and font/cache paths
inside the isolated temporary directory. This prevents textless screenshots and
does not alter application CSS or screenshot thresholds. The test configuration
may use `FRONT00_EXTERNAL_SERVER=1` only for a locally pre-started production
server; normal CI remains responsible for its own build/server and never updates
snapshots.
