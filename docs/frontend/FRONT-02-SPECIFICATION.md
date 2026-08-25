# EPD² FRONT-02 Specification — Design System, Application Shells & Page/Route Governance

**Status:** GOVERNED SPECIFICATION / IMPLEMENTATION NOT STARTED  
**Date:** 2026-08-25  
**Program position:** parallel FRONT specification while `API = NEXT`  
**Frontend closure state:** `NOT_STARTED_FINAL`  
**Canon:** unchanged  
**Production readiness:** NOT CLAIMED  
**Legal activation:** NOT CLAIMED

## 1. Purpose

FRONT-02 establishes the governed frontend foundation that later FRONT rounds must implement against. It is not a business-domain implementation round and it does not activate membership, voting, finance, casework, publication, representative, legal, administrative or other consequential capabilities.

FRONT-02 has four objectives:

1. convert the accepted FRONT-00 / FRONT-01 visual baseline into a governed design-system and application-shell specification;
2. reconcile the existing public-site routes, the Target Frontend Architecture 0.8.2 CORRECTED page catalogue and the legacy migration map into one explicit route-governance model;
3. define the missing public information-architecture families that are required for a complete public site without moving protected/product functionality into WS-01;
4. make failure, recovery, responsive, accessibility, help and search states first-class specification requirements before implementation begins.

## 2. Governing inputs

FRONT-02 is governed by, and must not silently supersede:

- `docs/roadmap/EPD2_PROJECT_ENTRYPOINT.md`;
- `docs/roadmap/EPD2_PROGRAM_CONTROL_REGISTER.md`;
- `docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md`;
- FRONT-00 accepted frontend foundation and visual regression baseline;
- FRONT-01 public website implementation and route catalogue;
- `EPD2_Target_Frontend_Architecture_0.8.2_CORRECTED` and its workspace, page, route, navigation, component, state and migration catalogues;
- `FIR-FRONT-001` and `FIR-FRONT-002`;
- `FIR-UX-003` through `FIR-UX-013`;
- `FIR-SEARCH-001` through `FIR-SEARCH-003`;
- `FIR-SUPPORT-001` through `FIR-SUPPORT-003`;
- `FIR-FORM-001` through `FIR-FORM-005` where forms are involved;
- `FIR-INV-003`, `FIR-INV-012` and `FIR-INV-015`;
- PACK-28 / WS-10 publication governance for public dynamic transparency and publication projections.

If these sources disagree on implementation state, the Program Control Register governs execution state and the Master Register governs future requirements. Route/name disagreements are resolved only through the explicit FRONT-02 route-governance rules below.

## 3. Non-negotiable architecture

FRONT-02 preserves the existing ten-workspace / ten-origin architecture:

- WS-01 Public Website;
- WS-02 Member Application;
- WS-03 Voting Client;
- WS-04 Representative Workspace;
- WS-05 Citizen Office Portal;
- WS-06 Institutional Administration;
- WS-07 Compliance & Legal Workspace;
- WS-08 Finance Workspace;
- WS-09 Independent Oversight & Verification;
- WS-10 Transparency Publication Portal.

No eleventh universal workspace, universal admin, universal session or universal frontend identity may be introduced.

The public site must not absorb authenticated or privileged product functionality merely because a public explanation page exists. In particular:

- membership application and member self-service belong to WS-02;
- ballot casting belongs only to isolated WS-03;
- representative operational work belongs to WS-04;
- citizen case intake and case status belong to WS-05;
- privileged administration belongs to WS-06;
- legal/compliance operations belong to WS-07;
- finance operations belong to WS-08;
- independent verification belongs to WS-09;
- governed public publication projections belong to WS-10.

WS-01 may explain these capabilities and provide safe handoffs, but it is never their source of truth or security boundary.

## 4. FRONT-02 implementation scope

FRONT-02 implementation, when started, is limited to shared frontend foundation work:

- design tokens derived from FRONT-00 / FRONT-01;
- shared typography, spacing, grid, borders, radius and layout primitives;
- header, footer, navigation, breadcrumbs and safe workspace handoff patterns;
- buttons, links, inputs, field groups, form sections and validation patterns;
- cards, lists, tables, filters, pagination and sorting patterns;
- tabs and local navigation;
- status badges and maturity/status presentation;
- alerts, notices and notifications;
- dialogs and confirmations;
- upload and document-reference patterns;
- timelines, history, provenance, version and evidence presentation;
- receipt and completion presentation;
- loading, empty, error, denied, stale, conflict, degraded and recovery states;
- page-shell variants for all ten workspaces while preserving origin/session boundaries;
- responsive behavior for mobile, tablet, desktop and wide layouts;
- accessibility behaviors including keyboard, screen reader, focus, zoom/reflow and reduced motion;
- visual regression fixtures and acceptance screenshot conventions;
- content-status and exact-label governance hooks;
- neutral support/help entry patterns;
- scoped search input/result primitives that do not create search authorization.

FRONT-02 does **not** implement domain authority, authoritative workflow state, legal effect, payment, member eligibility, ballot casting, tallying, publication approval, appeal decisions, case decisions, office/mandate authority, privileged IAM or production integrations.

## 5. Page and route authority model

### 5.1 One governed route model

FRONT-02 must end the current ambiguity between:

- the accepted FRONT-01 public route catalogue;
- the 81-page Target Frontend Architecture catalogue;
- the 61-entry current-to-target migration map;
- later PACK route registrations and V15/V16 frontend obligations.

The following authority order applies:

1. exact later governed route decision in the canonical repository;
2. accepted FRONT-01 route for an already implemented WS-01 public page;
3. later accepted domain/PACK route registration for its owning workspace;
4. Target Frontend Architecture 0.8.2 CORRECTED route for a not-yet-implemented workspace/page;
5. migration-map route only as a migration or alias input, never as an automatic canonical target.

A migration map may not silently replace an accepted FRONT-01 route.

### 5.2 German public-route continuity

The public site uses German public routes as the canonical public navigation surface. English target-blueprint routes are aliases/redirect candidates unless a later governed decision explicitly makes them canonical.

Mandatory route reconciliations are recorded in:

`docs/frontend/FRONT-02-PUBLIC-PAGE-ROUTE-DECISIONS.csv`

Examples include:

- `/home` → `/`;
- `/principles` → `/grundsaetze`;
- `/participate` → `/mitmachen`;
- `/structure` → `/struktur`;
- `/news` → `/aktuelles`;
- `/elections` and `/aktuelle-wahlen` → `/wahlen`;
- `/donate` → `/spenden`;
- `/technology` → `/technologie`;
- `/roadmap` → `/status`;
- `/faq` → `/hilfe`.

Redirect/alias support must preserve external links and must not create duplicate canonical content.

## 6. Required public information architecture additions

The following public families are required in the FRONT-02 page specification. Their presence in the catalogue does not activate backend functionality.

### 6.1 Presse

Canonical family:

- `/presse`;
- `/presse/[slug]`.

Required content model:

- press releases / official statements;
- publication date and issuer;
- correction/supersession state where applicable;
- press contact;
- media-kit / approved downloadable assets where governed;
- links only to approved public renditions.

### 6.2 Termine

Canonical family:

- `/termine`;
- `/termine/[slug]`.

Public event presentation may show approved public events. Internal assembly operations, attendance authority, quorum, voting or protected meeting functions remain in their owning workspaces.

### 6.3 Aktuelles

Canonical family:

- `/aktuelles`;
- `/aktuelles/[slug]`.

The detail page must support date, category, issuer/author role where appropriate, version/correction state and approved publication provenance. A flat list of topic placeholders is not the target information architecture.

### 6.4 Regionen

Canonical family:

- `/regionen`;
- `/regionen/[slug]`.

`/struktur` remains the organizational explanation page. `Meine Region finden` must resolve to the region directory/search flow rather than a dead route.

Only approved public organization projections may be displayed. Internal member directories must not be exposed.

### 6.5 Personen

Canonical family:

- `/personen`;
- `/personen/[slug]`.

This surface is limited to approved public personas such as governing-office holders, public candidates or public representatives. It must not become a membership directory or a cross-domain universal person profile.

### 6.6 Wahlen

Canonical family:

- `/wahlen`;
- `/wahlen/[slug]`.

This is a public information surface for approved election/campaign information. It must not embed WS-03 ballot casting or claim secret-electronic-voting readiness.

### 6.7 Hilfe and public search

Canonical public routes:

- `/hilfe`;
- `/suche`.

`/hilfe` is the public entry to the layered assistance model. It must support contextual help and versioned instructions and must not imply that a chatbot is the only support path.

`/suche` searches only approved public renditions. It must not create a global cross-domain search and must obey `findable subset of openable`.

## 7. Public pages preserved or explicitly governed

The following public content routes remain valid public surfaces or compatibility targets and must not disappear without a governed replacement/redirect:

- `/satzung` — governed public statute/document rendition;
- `/spenden` — public donation/contribution information and safe handoff only;
- `/verifizierung` — public explanation of verification, not the identity-proofing backend;
- `/nutzungsbedingungen` — public terms/usage information;
- `/impressum`;
- `/datenschutz`;
- `/barrierefreiheit`;
- `/kontakt`.

## 8. Mandatory system and recovery screens

FRONT-02 must provide governed patterns for system states. These are part of the product and are not optional polish.

Every relevant journey must map, as applicable:

- not found / 404;
- access denied / 403 without sensitive record disclosure;
- authentication required;
- session expired;
- loading;
- empty state;
- validation failure;
- stale data/version conflict;
- duplicate action;
- dependency unavailable;
- partial outage;
- maintenance;
- failed upload;
- interrupted submission;
- read-only/degraded mode;
- safe retry;
- alternative/offline channel where governed;
- completed state;
- immutable receipt/evidence state where applicable.

The UI must state whether the action was saved, submitted, rejected or left unchanged and what the user can do next.

## 9. Consequential-action pattern

Every consequential action pattern must distinguish at least:

- `Speichern`;
- `Einreichen`;
- `Bestätigen`;
- `Freigeben`;
- `Abstimmen`.

The shared pattern must support:

1. preview;
2. explicit consequence notice;
3. step-up authentication where required;
4. stale/version conflict check;
5. explicit confirmation;
6. authoritative backend commit;
7. receipt/evidence display only after commit succeeds.

Frontend state must never imply authoritative completion before backend success.

## 10. Shared public header

Every public page using the standard EPD² header must display directly beneath the upper-left `EPD²` logo:

`Erste Partei Direkte Demokratie`

The wording is exact. It is implemented through the shared public header/page shell, remains visually subordinate to the logo and does not authorize a redesign.

## 11. Transparency surface

`/transparenz` must be treated as a public verification hub under `FIR-UX-012`, not as a flat link list.

FRONT-02 must preserve the approved grouping:

1. Politik & Entscheidungen;
2. Finanzen & Dokumente;
3. Technologie & Civic OS.

Dynamic data must reach public rendering only through governed approved/publication projections. FRONT-02 must not introduce direct reads of raw internal operational tables.

Secret electronic voting status must remain equivalent to:

`IN ENTWICKLUNG / NICHT FREIGEGEBEN FÜR GEHEIME WAHLEN`

until the separately governed cryptographic, legal and activation gates pass.

## 12. Search governance

FRONT-02 may provide search components and WS-01 public search presentation, but authorization remains a backend/domain responsibility.

Rules:

- no unrestricted global search across EPD²;
- public search uses approved public renditions only;
- workspace search is scope/purpose aware;
- person search is purpose-specific;
- snippets, counts, facets, autocomplete and cache must not leak unauthorized data;
- the search index is not authoritative and cannot create legal effect;
- voting linkage data, protected-reporting identity, credentials/secrets and sealed evidence never enter general search.

## 13. Help and support governance

FRONT-02 must define reusable patterns for:

1. contextual help;
2. versioned Help Center;
3. case-specific secure question where applicable;
4. human support handoff;
5. technical support with minimum necessary access;
6. advisory AI assistance;
7. complaint/review/appeal path where applicable.

AI assistance must remain advisory and must never perform a consequential action without explicit confirmation or replace competent human authority.

## 14. Responsive and accessibility baseline

Every shared component and shell must be specified and later tested for:

- mobile;
- tablet;
- desktop;
- wide desktop;
- keyboard-only operation;
- screen reader semantics;
- 400% zoom/reflow;
- touch input;
- visible focus;
- reduced motion;
- adequate contrast;
- non-color-only status meaning.

No required action, evidence or status may disappear at a supported viewport.

## 15. Canonical visual baseline — immutable by default

FRONT-00 and FRONT-01 are the **canonical and immutable visual baseline** for all FRONT-02 work. The existing public pages, shared components, actual design tokens, typography, spacing, page widths, grid geometry, navigation, header/footer geometry, cards, borders, radii, colors, interaction states and accepted reference screenshots are not merely inspiration or a style reference: they are the implementation baseline that must be reused.

FRONT-02 **MUST NOT evolve, reinterpret, modernize, refresh, restyle or redesign** that baseline. In particular, no FRONT-02 implementation may change existing:

- typography family, scale, weight hierarchy or line-height system;
- spacing rhythm, container widths, gutters or grid logic;
- header, footer or navigation geometry and visual treatment;
- button, link, input, card, table, list, tab, badge, alert or dialog styling;
- color palette or color roles;
- border widths, radii, shadows or density;
- icon language or decorative treatment;
- hover, focus, disabled or active-state presentation;
- responsive breakpoints or existing component geometry;
- existing page composition solely for aesthetic reasons.

New FRONT-02 functionality must be composed from existing components and tokens. Where a genuinely new component is unavoidable, it must be derived from the canonical tokens and nearest existing component pattern, with no new visual language. Adding content may extend a page vertically or add governed blocks, but it must not restyle existing blocks.

The only permitted visual-baseline change is a **separate, explicit governed Design Change Decision** that identifies the exact affected token/component/page, states the reason, provides before/after screenshots, accessibility evidence and visual-regression impact, and is approved before implementation. A feature requirement, developer preference, "modernization", convenience or a new mockup is not such approval.

`FIR-UX-013` is a pre-existing governed content requirement for the exact identity line `Erste Partei Direkte Demokratie`; implementing that line through the shared header is permitted **only as that explicit requirement and without otherwise changing the header's visual design**.

Any FRONT-02 candidate that changes the canonical visual baseline without such a Design Change Decision is an automatic **FAIL**.

## 16. Mandatory pre-implementation artefacts

FRONT-02 implementation candidate must not start until these artefacts exist and are internally consistent for the FRONT-02 scope:

- `FRONT-02-PAGE-CATALOGUE.md`;
- `FRONT-02-PAGE-SEQUENCE-MAP.md`;
- `FRONT-02-NAVIGATION-MAP.md`;
- `FRONT-02-CONTENT-MAP.md`;
- `FRONT-02-ACTION-MAP.md`;
- `FRONT-02-SCREEN-STATE-MATRIX.md`;
- `FRONT-02-PERMISSION-AND-ASSURANCE-MATRIX.md`;
- `FRONT-02-RESPONSIVE-LAYOUT-SPECIFICATION.md`;
- `FRONT-02-ACCESSIBILITY-FLOW.md`;
- `FRONT-02-ACCEPTANCE-SCREENSHOT-INVENTORY.md`;
- route reconciliation consistent with `FRONT-02-PUBLIC-PAGE-ROUTE-DECISIONS.csv`.

For each page/screen the catalogue must include stable ID, route/pattern, workspace/origin, purpose, audience, source domain, source of truth, permissions/assurance, journey position, predecessors/successors, content order, actions, consequential actions, states, warnings, evidence/receipt handling, responsive structure, accessibility behavior, telemetry rule and acceptance evidence.

## 17. Acceptance gates for FRONT-02 implementation

A future FRONT-02 implementation candidate fails when any of the following is true:

- it creates an eleventh workspace/origin or collapses workspace isolation;
- it moves WS-03 voting into the member/public shell;
- it introduces a universal admin or universal person profile;
- it changes any canonical FRONT-00/FRONT-01 visual baseline element without a separate approved Design Change Decision;
- it implements only happy-path desktop states;
- failure/recovery states are missing;
- mobile or accessibility flow is incomplete;
- public dynamic content bypasses approved publication projections;
- public search can reveal protected/internal data;
- exact global identity wording is missing or inconsistent;
- `/transparenz` violates the approved IA or overstates readiness;
- legacy/current public routes break without explicit redirect/replacement;
- code invents consequential process logic or official wording not present in governed sources;
- browser, accessibility, screenshot and visual-regression evidence does not cover the approved sequence.

## 18. FIR disposition

This specification creates **no new FIR IDs**.

It takes up existing obligations without changing their status:

- `FIR-FRONT-001`, `FIR-FRONT-002`;
- `FIR-UX-003` through `FIR-UX-013`;
- `FIR-SEARCH-001` through `FIR-SEARCH-003`;
- `FIR-SUPPORT-001` through `FIR-SUPPORT-003`;
- `FIR-INV-003`, `FIR-INV-012`, `FIR-INV-015`.

`FIR-UX-011` is materially advanced at specification level for FRONT-02, but remains `approved`, not `implemented`: the mandatory derived catalogues, implementation and acceptance evidence still do not exist.

`FIR-UX-012` and `FIR-UX-013` remain `approved`, not `implemented`: this specification binds them into FRONT-02 but does not change the shared header or `/transparenz` code.

## 19. Execution status

After adoption of this document:

```text
FRONT-02 = SPECIFICATION ESTABLISHED
FRONT-02 IMPLEMENTATION = NOT STARTED
FRONT FINAL = NOT STARTED
API = NEXT
```

FRONT-02 implementation may proceed in parallel only within the boundaries of this specification and without changing the primary closure sequence:

`DATA → API → INFRA → OPS → CTRL → FRONT → SEC`.
