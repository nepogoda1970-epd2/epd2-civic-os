# FRONT-01 Implementation Report

Status: **FRONT-01 PUBLIC WEBSITE 0.2.0 CANDIDATE**

Baseline: `EPD2_FRONT-00_FOUNDATION_0.1.6_PASS.zip`

This report is finalized after verification and packaging. It records the
implementation scope without claiming production, legal, operational or
security activation.

## Implementation

- Added 31 WS-01 routes and a common public shell.
- Added typed maturity statuses and `CapabilityStatusBanner`.
- Added program skeleton, initiative lifecycle, voting isolation,
  publication-flow and public-board explanations.
- Migrated or dispositioned all 61 legacy HTML files.
- Reworded SYSTEM LIVE, binding voting, automatic legal effect, public
  reputation, imperative mandate, active finance/caseflow and direct-log
  claims.
- Applied audit conditions C1–C8 and WC/FEC corrections.

## Boundaries

WS-01 is the only implemented workspace. No authenticated or operational
business capability was added. Repository `0.9.0` and Canon `0.7.0` are
unchanged. PACK-10 runtime, PACK-19–35, Domains 51–58, WS-02, WS-03, WS-04,
WS-05, WS-07, WS-08, WS-09 and WS-10 remain dependencies as labelled.

## Routes and legacy migration

- 31 statically generated WS-01 routes are listed in
  `FRONT-01-ROUTE-CATALOG.csv`.
- All 61 legacy HTML files have one disposition in
  `FRONT-01-LEGACY-MIGRATION-MAP.csv`: migrate, merge, rewrite, public
  explanation, move to a future workspace, remove or redirect.
- Removed or qualified claims include `SYSTEM LIVE`, binding or
  cryptographically verified voting, automatic legal effects, public
  individual reputation, imperative mandate, active finance ledger, active
  citizen-office routing and direct public operational logs.

## Exact file inventory

Added:

- 9 FRONT-01 documentation files under `docs/frontend` and `docs/handover`;
- `frontend/web-shell/app/[...slug]/page.tsx`;
- `frontend/web-shell/components/public-site.tsx`;
- `frontend/web-shell/public/content.ts`;
- `frontend/web-shell/public/status.ts`;
- three FRONT-01 test source files;
- 30 PNG files under
  `frontend/web-shell/tests/browser/front01.browser.spec.ts-snapshots`.

Modified:

- `.prettierignore`;
- `frontend/web-shell/app/globals.css`;
- `frontend/web-shell/app/layout.tsx`;
- `frontend/web-shell/app/page.tsx`;
- `frontend/web-shell/tests/smoke.test.ts`.

Removed: none.

## Verification

Commands and results:

- `make format-check`: PASS; Ruff format 217 files and Prettier;
- `make lint`: PASS; Ruff and ESLint;
- `make typecheck`: PASS; all Python mypy groups and both TypeScript
  workspaces;
- `uv run pytest`: 2658 passed, 4 skipped, plus the three forbidden-path tests
  verified on the clean package tree;
- `npm run test --workspace=frontend/web-shell`: 34 architecture/source tests
  and 16 rendered component tests passed;
- `npm run build --workspace=frontend/web-shell`: PASS; 46 static pages;
- Playwright normal comparison mode: 108/108 passed, executed as 36/36 mobile,
  36/36 desktop and 36/36 wide;
- FRONT-01 visual regression: 30/30 PNG comparisons passed;
- axe serious/critical checks: PASS;
- keyboard, landmarks, reduced motion, internal links and no-mutation checks:
  PASS.

The snapshot set was created once for FRONT-01 and then verified without
snapshot-update mode. FRONT-00's 15 baselines and gates remain in place.

## Package

The candidate includes the complete standalone repository, `.github`,
`.gitignore` and required `.gitkeep` files. It excludes `.git`, dependencies,
build output, caches, reports, temporary data and nested ZIP files.

The final output SHA-256 is supplied as a detached checksum and in the handover
message: an archive cannot truthfully contain its own final hash without
changing that hash.
