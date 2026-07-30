# PACK-14 — Rendition Specification

**Round:** PACK-14 — specification and ADR only. **No code. Not implemented. Not a candidate. Not a PASS.**
**Repository version:** unchanged at `0.13.0` · **Canon version:** unchanged at `0.8.0`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**
**Architecture correction applied (2026-07-30).**

Required by `FIR-FORM-002` and `FIR-FORM-005`, and constrained by
`FIR-UX-003` … `FIR-UX-011`. This document performs the inventory and
token extraction those entries require **before** any new pattern is
proposed.

## 1. Existing visual baseline — inventory

Taken from the approved FRONT-00/FRONT-01 implementation, which
`FIR-UX-010` establishes as the authoritative visual baseline.

### 1.1 Actual design tokens

Extracted from `frontend/web-shell/app/globals.css`, `:root`:

| Token                                  | Value                                             | Role                   |
| -------------------------------------- | ------------------------------------------------- | ---------------------- |
| `--accent`                             | `#5c3d3d`                                         | Primary accent         |
| `--text`                               | `#1f1f1f`                                         | Body text              |
| `--muted`                              | `#666`                                            | Secondary text         |
| `--light-bg`                           | `#f4f5f7`                                         | Page background        |
| `--card-border`                        | `#e2e0d8`                                         | Card and panel borders |
| `--soft`                               | `#f0ede6`                                         | Soft fill              |
| `--white`                              | `#fff`                                            | Surface                |
| `--green`                              | `#0b8b4f`                                         | Positive status        |
| `--danger`                             | `#9d2424`                                         | Negative status        |
| `--warning`                            | `#775700`                                         | Caution status         |
| `--space-1` … `--space-10`             | `0.25`, `0.5`, `0.75`, `1`, `1.5`, `2`, `2.5` rem | Spacing rhythm         |
| `--radius-sm` / `--radius-lg`          | `8px` / `14px`                                    | Corner radii           |
| `--shadow-raised`                      | `0 12px 24px -8px rgb(0 0 0 / 7%)`                | Raised surface         |
| `--content-wide` / `--content-reading` | `1280px` / `760px`                                | Page widths            |
| `--z-sticky` / `--z-overlay`           | `50` / `100`                                      | Layering               |
| `--focus`                              | `#175cd3`                                         | Focus ring             |

Typography is the system stack declared on `body`; `color-scheme: light`.

### 1.2 Existing shared components

From `frontend/web-shell/components/foundation.tsx`:
`Button`, `LinkButton`, `StatusBadge`, `Breadcrumb`, `PageHeader`,
`Card`, `MetricCard`, `Notice`, `StatePanel`, `FormField`,
`SecondaryNavigation`, `BackLink`, `MetadataList`, `StructuredList`,
`AccessibleTableContainer`, `SearchField`, `FilterGroup`,
`RestrictedContentNotice`, `StaleDataWarning`, `CandidateBanner`,
`ProvenancePanel`, `Tabs`, `Pagination`, `WorkspaceShell`; plus
`DialogExample` and the migrated fixtures including `LoginFixture`.

## 2. Classification — reuse / extend / replace

`FIR-UX-003`'s required classification, with a justification for every
entry that is not `reuse`.

| Pattern needed by PACK-14                      | Existing component                                                  | Classification         | Justification                                                                                                                                               |
| ---------------------------------------------- | ------------------------------------------------------------------- | ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Page frame and navigation                      | `WorkspaceShell`, `SecondaryNavigation`, `Breadcrumb`, `PageHeader` | **reuse**              | —                                                                                                                                                           |
| Form fields and validation                     | `FormField`                                                         | **reuse**              | —                                                                                                                                                           |
| Primary and secondary actions                  | `Button`, `LinkButton`                                              | **reuse**              | —                                                                                                                                                           |
| Informational and warning notices              | `Notice`                                                            | **reuse**              | —                                                                                                                                                           |
| Empty, loading and error states                | `StatePanel`                                                        | **reuse**              | —                                                                                                                                                           |
| Credential and session lists                   | `StructuredList`, `AccessibleTableContainer`, `MetadataList`        | **reuse**              | —                                                                                                                                                           |
| Status of a credential, factor or session      | `StatusBadge`                                                       | **extend**             | Needs security-state semantics (active, revoked, expiring, compromised) that the existing badge does not carry. Extension keeps the shape and adds meanings |
| Confirmation dialog for a consequential action | `DialogExample`                                                     | **extend**             | Needs the object-version display and the step-up binding required by ADR-082. No new dialog language is introduced                                          |
| Step-up interruption panel                     | —                                                                   | **new, minimal**       | No equivalent exists. Built from `Card` + `FormField` + `Button` with existing tokens; introduces no new visual language                                    |
| Session and device inventory                   | `AccessibleTableContainer` + `MetadataList`                         | **reuse**              | —                                                                                                                                                           |
| Security alert surface                         | `Notice` (danger variant)                                           | **extend**             | Needs an action-required affordance distinct from an informational notice                                                                                   |
| Submission receipt                             | `ProvenancePanel` + `MetadataList`                                  | **extend**             | Receipt fields per `FIR-FORM-005`; the provenance pattern already carries the right visual weight                                                           |
| Login surface                                  | `LoginFixture`                                                      | **reuse as reference** | The migrated fixture is the visual precedent                                                                                                                |

**No pattern is classified `replace`, and no new design language is
introduced.** Every extension keeps the existing tokens, spacing rhythm,
radii, page widths, navigation character and restrained colour use.

## 3. Renditions per `FIR-FORM-005`

| Rendition                    | Requirement                                                                                                                                                                                                                              |
| ---------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Desktop web                  | `--content-reading` for forms, `--content-wide` for inventories                                                                                                                                                                          |
| Mobile web                   | Single column; touch targets ≥ 44px; no horizontal scroll; the step-up panel must be completable one-handed                                                                                                                              |
| Accessible representation    | Semantic landmarks, labelled fields, focus order matching visual order, `--focus` ring visible, live-region announcement of state changes, no reliance on colour alone                                                                   |
| Printable form               | Reading width, no interactive affordances, all declarations printed in full                                                                                                                                                              |
| Archival PDF                 | Same mandatory questions, declarations, warnings and confirmations as the digital form — **no divergence permitted**                                                                                                                     |
| Immutable submission receipt | Form ID and version, submission ID, date and time, submitting party in the permitted identity form, organizational scope, attachment inventory, confirmed declarations, integrity reference, submission channel, next step and deadlines |
| Administrative review view   | Reviewer surfaces show the case, never a general identity search                                                                                                                                                                         |

## 4. State semantics without colour

`FIR-UX-009` and `FIR-INV-012`. Every security state is carried
**simultaneously** by: textual status, page or card structure, badge shape,
an accessible icon or marker, and the available actions. Colour is the
fifth carrier, never the first and never the only one.

| State                  | Text                                | Structure               | Marker         | Actions             |
| ---------------------- | ----------------------------------- | ----------------------- | -------------- | ------------------- |
| Credential active      | „Aktiv"                             | in the active list      | check marker   | rename, remove      |
| Credential revoked     | „Widerrufen"                        | in the history list     | crossed marker | none                |
| Session current        | „Diese Sitzung"                     | first, highlighted card | dot marker     | none                |
| Session other          | „Aktiv"                             | in the list             | device marker  | end session         |
| Assurance insufficient | „Höheres Schutzniveau erforderlich" | inline blocking panel   | lock marker    | start step-up       |
| Account restricted     | „Eingeschränkt"                     | banner above content    | warning marker | view reason, appeal |

## 5. Interaction requirements

| Requirement                                                         | Rule                                                                         |
| ------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| Step-up interrupts and resumes                                      | The user's work is not lost; the pending action is shown by name and version |
| What is being confirmed is visible                                  | Including the object version (ADR-082)                                       |
| Every refusal shows the reason and the next step                    | The content catalogue's closing principle                                    |
| Codes are never pre-filled or auto-submitted                        | Prevents silent confirmation                                                 |
| Recovery codes are shown once, with an explicit acknowledgement     | `F-P14-08`                                                                   |
| Destructive actions state the consequence before the confirm button | `F-P14-05`, `F-P14-13`                                                       |
| No security state is announced by colour alone                      | §4                                                                           |

## 6. What this document does not do

It builds nothing. No component is written, no route is added, no snapshot
is taken. FRONT-PACK owns the implementation, and the classification above
is the inventory it must start from rather than repeat.

It also defines **no page sequence**. `FIR-UX-011` requires an approved
Page Specification Catalogue and Screen-State Matrix — page order, entry
screen, decision points, branch conditions, return and cancellation paths,
interrupted-process recovery, completion and receipt pages — and none of
its ten artefacts (`PAGE-CATALOGUE.md`, `PAGE-SEQUENCE-MAP.md`,
`NAVIGATION-MAP.md`, `CONTENT-MAP.md`, `ACTION-MAP.md`,
`SCREEN-STATE-MATRIX.md`, `PERMISSION-AND-ASSURANCE-MATRIX.md`,
`RESPONSIVE-LAYOUT-SPECIFICATION.md`, `ACCESSIBILITY-FLOW.md`,
`ACCEPTANCE-SCREENSHOT-INVENTORY.md`) is produced here.

**The complete first-page-to-final-page structure will be defined during
the relevant `FRONT-PACK Specification + UX/IA` stage, before frontend
implementation.** What this document supplies to that stage is the token
and component inventory, the reuse/extend/replace classification, the
rendition requirements and the colour-independent state semantics — the
domain-side inputs `FIR-UX-011`'s responsibility split assigns to the
domain PACK.
