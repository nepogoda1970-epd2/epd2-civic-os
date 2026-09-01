# FRONT-00 Candidate Report

Status: **FRONT-00 IMPLEMENTATION CANDIDATE** (not PASS).

Candidate revision: 0.1.3. Repository 0.9.0 and canon 0.7.0 are unchanged.

## Exact migrated source pages

| Source page                  | Migrated representative fixture      | Classification                    |
| ---------------------------- | ------------------------------------ | --------------------------------- |
| `index.html`                 | `/foundation/examples/public`        | migrated fixture                  |
| `intern/dashboard.html`      | `/foundation/examples/cockpit`       | migrated fixture                  |
| `intern/kommunikation.html`  | `/foundation/examples/communication` | migrated fixture                  |
| `buerger-login.html`         | `/foundation/examples/form`          | migrated fixture                  |
| `struktur/abstimmungen.html` | `/foundation/examples/table`         | migrated fixture                  |
| component catalogue          | `/foundation`                        | generic showcase, not a migration |

Each migration preserves the original composition and principal sections.
Candidate, backend-disconnection, and non-activation notices are explicit. Source
identity/status/messages/results remain static layout examples and no action is
connected.

## Deliberate visual differences

The complete nine-item list is in `FRONT-00-DESIGN-PRESERVATION.md`: candidate
banner; honest static-state wording; focus ring; 44 px targets; text-plus-marker
status; responsive overflow; table scroll semantics; disabled login/composer;
legal and authority notices. There is no intentional redesign.

## Tests and evidence

Rendered components:

- command: `npm run test:components --workspace=frontend/web-shell`
- result: 13 passed, 0 failed
- coverage: all button variants/disabled state, status text, breadcrumb/tabs
  current state, label/hint/error association, live region, shell landmarks and
  navigation, provenance, pagination, and dialog open/cancel/confirm/focus.

Existing frontend tests:

- command: `npm run test --workspace=frontend/web-shell`
- result: 25 node architecture tests + 13 rendered tests passed

Browser/visual/accessibility commands:

- `npm run test:browser --workspace=frontend/web-shell`: 51 passed
- `npm run test:visual --workspace=frontend/web-shell`: 15 passed against
  committed snapshots, without update mode
- `npm run test:a11y --workspace=frontend/web-shell`
- reviewed snapshot creation only:
  `npm run test:browser:update --workspace=frontend/web-shell`

Screenshot stems and routes are listed in `FRONT-00-VISUAL-REGRESSION.md`;
15 reviewed PNGs are included under
`frontend/web-shell/tests/browser/front00.browser.spec.ts-snapshots/` for mobile,
desktop, and wide projects.

All five originals and migrations were rendered at matching mobile, desktop, and
wide viewports and compared before approval. Differences are limited to the
documented candidate-status, accessibility, honest disabled-state, and
responsive corrections. The isolated test browser's font paths were corrected;
thresholds and the candidate-banner-only mask remain unchanged. CI does not
update snapshots.

Other exact local results:

- `npm run typecheck --workspace=frontend/web-shell`: success
- `npm run lint --workspace=frontend/web-shell`: success
- `npm run build --workspace=frontend/web-shell`: success; 16 static pages
- clean Python suite: 2659 passed, 4 skipped, 0 failed
- `ruff format --check .`: 217 files already formatted
- `ruff check .`: all checks passed
- `scripts/check_repository.py`: all 585 required paths present
- `scripts/check_forbidden_files.py`: no forbidden paths
- `scripts/verify_versions.py`: all version sources consistent
- `make typecheck`: success, including collision-safe mypy service-by-service
  checks and both TypeScript workspaces
- `uv run mypy .`: not the repository's valid command; it fails immediately on
  duplicate test-module basenames. CI now invokes `make typecheck`, matching the
  existing Makefile explanation and actual repository verification command.

## New test-only dependencies

- `@playwright/test`: real browser, keyboard, and screenshot checks
- `@axe-core/playwright`: automated accessibility scan
- `vitest`, `jsdom`, `@vitejs/plugin-react`: rendered DOM test runner
- Testing Library packages: accessible queries and user interactions
- `@sparticuz/chromium`: reproducible test-only browser fallback

No production dependency, framework, package manager, backend, contract, canon,
or business domain was added.

## Mobile Application Profile correction

The EPD² Mobile App is now represented as an inactive additional client channel,
not a workspace or eleventh origin. Workspace/origin count remains ten. Its
primary scope is future WS-02 capabilities; optional scope is restricted to
explicitly citizen-facing WS-05 request status. Privileged workspaces and
universal administration remain prohibited.

The WS-05 `citizen-office-request-status` declaration is activation-gated by
PACK-33, the direct owner of citizen-office request submission, routing, status,
and caseflow. PACK-23 and PACK-29 remain prerequisites only through the PACK-33
dependency chain. No PACK-29 capability is exposed through WS-05.

WS-03 may open only in the system browser through a future one-time,
short-lived, purpose- and voting-event-scoped handoff. Embedded WebView, member
session transfer, persistent member ID transfer, shared cookies/storage/
analytics/identity sessions, vote content in the return, and intermediate tally
are prohibited. Push, security, offline, crash-log, delivery-sequencing, source
sharing, and mobile accessibility gates are declared and architecture-tested.
No native app, PWA service worker, provider, device registration, deep link,
handoff API, authentication, or voting implementation was added. Production
mobile implementation is deferred.

Visual design, representative pages, routes, backend contracts, repository and
canon versions, accepted ADRs, and business scope are unchanged. The result
remains **FRONT-00 IMPLEMENTATION CANDIDATE**, never PASS.

## Scope and limitations

No membership workflow, authentication, communication backend, voting, finance,
legal workflow, API, persistence, production telemetry, or production origin is
implemented. WS-03 isolation declarations remain unchanged. Manual
assistive-technology, cross-browser, legal, security, and screenshot re-approval
after any visual change remain external gates.

This correction is only **FRONT-00 IMPLEMENTATION CANDIDATE**.
