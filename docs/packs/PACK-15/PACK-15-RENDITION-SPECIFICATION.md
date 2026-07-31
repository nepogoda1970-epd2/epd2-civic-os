# PACK-15 — Rendition Specification

**Round:** PACK-15 — specification and ADR only. **No code. Not implemented. Not a candidate. Not a PASS.**
**Repository version:** unchanged at `0.14.0` · **Canon version:** unchanged at `0.8.0`
**Baseline:** `EPD2_PACK-14_IDENTITY_AUTHENTICATION_ACCOUNT_SECURITY_0.14.0_FINAL_PASS.zip`
**Authoritative register:** `EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER_UPDATED_V6.md`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**
**Architecture correction applied (2026-07-31).**

Required by `FIR-FORM-002` and `FIR-FORM-005`, and constrained by
`FIR-UX-003` … `FIR-UX-011`. This document performs the inventory and
classification those entries require **before** any new pattern is
proposed.

---

## 1. Existing visual baseline — inventory

Taken from the approved FRONT-00/FRONT-01 implementation, which
`FIR-UX-010` establishes as the authoritative visual baseline, and carried
unchanged from PACK-14's inventory of the same baseline.

### 1.1 Design tokens

From `frontend/web-shell/app/globals.css`, `:root`: `--accent` `#5c3d3d`;
`--text` `#1f1f1f`; `--muted` `#666`; `--light-bg` `#f4f5f7`;
`--card-border` `#e2e0d8`; `--soft` `#f0ede6`; `--white` `#fff`;
`--green` `#0b8b4f`; `--danger` `#9d2424`; `--warning` `#775700`;
`--space-1` … `--space-10`; `--radius-sm` `8px` / `--radius-lg` `14px`;
`--shadow-raised`; `--content-wide` `1280px` / `--content-reading` `760px`;
`--z-sticky` `50` / `--z-overlay` `100`; `--focus` `#175cd3`. Typography is
the system stack declared on `body`; `color-scheme: light`.

### 1.2 Existing shared components

From `frontend/web-shell/components/foundation.tsx`: `Button`,
`LinkButton`, `StatusBadge`, `Breadcrumb`, `PageHeader`, `Card`,
`MetricCard`, `Notice`, `StatePanel`, `FormField`, `SecondaryNavigation`,
`BackLink`, `MetadataList`, `StructuredList`, `AccessibleTableContainer`,
`SearchField`, `FilterGroup`, `RestrictedContentNotice`,
`StaleDataWarning`, `CandidateBanner`, `ProvenancePanel`, `Tabs`,
`Pagination`, `WorkspaceShell`.

---

## 2. Classification — reuse / extend / new

`FIR-UX-003`'s required classification, with a justification for every
entry that is not `reuse`.

| Pattern needed by PACK-15                          | Existing component                                  | Classification    | Justification                                                                                                                     |
| -------------------------------------------------- | --------------------------------------------------- | ----------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| Page frame and navigation (WS-02 side)             | `WorkspaceShell`, `Breadcrumb`, `PageHeader`        | **reuse**         | —                                                                                                                                 |
| Voting context presentation                        | `Card` + `MetadataList`                             | **reuse**         | —                                                                                                                                 |
| Eligibility state display                          | `StatePanel` + `Notice`                             | **extend**        | Needs reason-coded state semantics with a named next step; the panel exists, the semantics do not                                  |
| Form fields and validation                         | `FormField`                                         | **reuse**         | —                                                                                                                                 |
| Declarations                                       | `FormField` (checkbox variant)                      | **reuse**         | Never pre-checked                                                                                                                 |
| Eligibility decision notice                        | `ProvenancePanel` + `MetadataList`                  | **extend**        | Adds the rule-set version and the appeal path; keeps the existing visual weight                                                    |
| Handoff departure interstitial                     | —                                                   | **new, minimal**  | No equivalent exists. Built from `Card` + `Notice` + `Button` with existing tokens; introduces no new visual language              |
| Isolated voting-origin shell (WS-03)               | —                                                   | **new, minimal**  | Must share **no code path that carries identity state**; visually consistent, structurally separate. Owned by FRONT-PACK           |
| Credential availability and retrieval surface      | `Card` + `Button`                                   | **extend**        | Adds one-time-availability semantics                                                                                              |
| Dispute submission                                 | `FormField` + `StatePanel`                          | **reuse**         | —                                                                                                                                 |
| Assisted-action receipt                            | `ProvenancePanel`                                   | **extend**        | Adds helper attribution and the two mandatory declarations                                                                        |
| Status badges for eligibility and credential state | `StatusBadge`                                       | **extend**        | Needs the state set in §4; extension keeps the shape and adds meanings                                                            |
| Search over cases or credentials                   | `SearchField`                                       | **prohibited**    | **Deliberately not used.** No search surface over eligibility cases, credentials or participation exists, and none may be added   |
| Metric tiles for participation                     | `MetricCard`                                        | **prohibited**    | Would be an intermediate-tally surface                                                                                            |

**No pattern is classified `replace`, and no new design language is
introduced.** Two patterns are classified **prohibited**, which is a
classification this round adds deliberately: the component exists and is
appropriate-looking, and using it would violate an invariant.

---

## 3. Renditions per `FIR-FORM-005`

| Rendition                    | Requirement                                                                                                                                                     |
| ---------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Desktop web                  | `--content-reading` for forms and decisions; `--content-wide` only where a list is unavoidable                                                                    |
| Mobile web                   | Single column; touch targets ≥ 44px; no horizontal scroll; the whole handoff must be completable one-handed                                                       |
| Accessible representation    | Semantic landmarks; labelled fields; focus order matching visual order; visible `--focus` ring; live-region announcement of state changes; no reliance on colour  |
| Printable form               | Reading width; no interactive affordances; all declarations printed in full                                                                                      |
| Archival PDF                 | Same mandatory questions, declarations, warnings and confirmations as the digital form — **no divergence permitted**                                              |
| Immutable submission receipt | Form ID and version, submission ID, date and time, submitting party in the permitted identity form, organizational scope, attachment inventory, confirmed declarations, integrity reference, submission channel, next step and deadlines |
| Administrative review view   | Reviewers see **the case**, never a general search over cases or participants                                                                                    |
| Voting-origin rendition      | No shared navigation, no profile, no account menu, no analytics; visually consistent, structurally isolated                                                       |

**The receipt on the voting side carries no submitting party.** The
generic receipt structure names one; `F-P15-04`'s receipt omits it, and
that omission is specified rather than left to an implementer's judgement.

---

## 4. State semantics without colour

`FIR-UX-009` and `FIR-INV-012`. Every state is carried **simultaneously**
by textual status, page or card structure, badge shape, an accessible
marker, and the available actions. Colour is the fifth carrier, never the
first and never the only one.

| State                              | Text (DE)                             | Structure                | Marker         | Actions                       |
| ---------------------------------- | ------------------------------------- | ------------------------ | -------------- | ----------------------------- |
| Eligibility requested              | „Antrag eingegangen"                  | in the open list         | dot marker     | withdraw                      |
| Eligibility under review           | „In Prüfung"                          | in the open list         | clock marker   | submit evidence               |
| Eligibility approved               | „Teilnahmeberechtigt"                 | highlighted card         | check marker   | retrieve access               |
| Eligibility denied                 | „Nicht teilnahmeberechtigt"           | inline decision panel    | crossed marker | view reason, appeal           |
| Eligibility expired                | „Entscheidung abgelaufen"             | in the history list      | expired marker | request again, if in window   |
| Credential available               | „Zugang verfügbar"                    | prominent action card    | key marker     | retrieve                      |
| Credential retrieved               | „Zugang abgerufen"                    | confirmation card        | check marker   | enter the voting area         |
| Credential expired                 | „Zugang abgelaufen"                   | in the history list      | expired marker | report a problem              |
| Credential revoked                 | „Zugang widerrufen"                   | inline decision panel    | crossed marker | view reason, request review   |
| Context not open                   | „Abstimmung nicht geöffnet"           | disabled card with text  | lock marker    | view the window               |
| Dispute open                       | „Widerspruch in Bearbeitung"          | in the open list         | clock marker   | view, withdraw                |

**There is no state for "voted" and none may be added.** The participant's
own view ends at „Zugang abgerufen"; what happens in the voting area is
not reported back into the ordinary workspace.

---

## 5. Interaction requirements

| Requirement                              | Rule                                                                                                                     |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| The departure from WS-02 is explicit     | The participant is told they are leaving the member area and what changes                                                |
| No silent redirect into the voting origin| A navigation that carries a one-time artifact is never automatic                                                          |
| One-time availability is stated plainly  | Before retrieval, not after                                                                                              |
| No countdown pressure                    | Deadlines are stated; a ticking clock is a coercion aesthetic and is not used                                            |
| No progress indicator across the boundary| A cross-boundary progress bar would be a participation status                                                            |
| Errors state a reason and a next step    | `PACK-15-CONTENT-CATALOGUE-DE.md`                                                                                        |
| Nothing is prefilled from a prior context| Cross-context state is prohibited                                                                                        |

---

## 6. What this document does not define

**The page sequence.** PACK-15 supplies the domain side of
`FIR-UX-011`'s responsibility split — process, authoritative data,
permissions and assurance per action, forms, decisions, mandatory governed
content and state semantics. It produces **none** of `FIR-UX-011`'s ten
artefacts and defines no page order, navigation model or screen structure.

**The complete first-page-to-final-page structure is defined during the
relevant `FRONT-PACK Specification + UX/IA` stage, before frontend
implementation**, and nothing here may be read as pre-empting it.

---

## 7. Surfaces and states added by the architecture correction (2026-07-31)

### 7.1 New patterns, classified

| Pattern needed after the correction                | Existing component            | Classification    | Justification                                                                                     |
| -------------------------------------------------- | ----------------------------- | ----------------- | ------------------------------------------------------------------------------------------------- |
| Queued-access state on the identity side           | `StatePanel` + `Notice`       | **extend**        | Adds a "being prepared" state with no countdown and no position-in-queue                          |
| Access-available call to action                    | `Card` + `Button`             | **reuse**         | —                                                                                                 |
| Departure interstitial (leaving WS-02)             | `Card` + `Notice` + `Button`  | **new, minimal**  | Existing tokens only; states plainly what changes on crossing                                     |
| Minting waiting state inside WS-03                 | `StatePanel`                  | **extend**        | A determinate-looking but non-numeric progress state; no countdown, no position                   |
| Credential display                                 | —                             | **prohibited**    | **Credential material is never rendered.** There is no component for it and none may be added     |
| "Copy access code" affordance                      | —                             | **prohibited**    | Clipboard is a prohibited delivery channel                                                        |
| "Download / print access" affordance               | —                             | **prohibited**    | Prohibited delivery channels                                                                      |
| Queue-position or estimated-time indicator         | —                             | **prohibited**    | Leaks cohort structure (`T-P15-37`) and applies pressure                                          |

### 7.2 State semantics — additions

| State                          | Text (DE)                        | Structure               | Marker        | Actions                    |
| ------------------------------ | -------------------------------- | ----------------------- | ------------- | -------------------------- |
| Access queued                  | „Zugang wird vorbereitet"        | in the open list        | clock marker  | none; a notification follows |
| Access available               | „Zugang verfügbar"               | prominent action card   | key marker    | enter the voting area      |
| Leaving the member area        | „Sie verlassen den Mitgliederbereich" | full-width interstitial | boundary marker | continue, cancel        |
| Preparing access (inside WS-03)| „Zugang wird erstellt"           | centred waiting panel   | clock marker  | none                       |
| Entry complete                 | „Zugang eingelöst"               | confirmation panel      | check marker  | continue to the ballot     |

**There is still no state for "voted", and none may be added.** The
identity-side view ends at „Zugang verfügbar" / „Zugang abgerufen"; nothing
inside the voting area is reported back into the ordinary workspace.

### 7.3 Interaction requirements — additions

| Requirement                                   | Rule                                                                                                    |
| --------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| The waiting states are honest                 | They say that access is being prepared; they do not show a queue position, an estimate or a countdown   |
| No pressure aesthetics                        | No ticking clock, no "hurry", no scarcity framing — a coercion aesthetic in a voting flow is not neutral |
| Waiting is announced to assistive technology  | A polite live region announces state changes; the participant is never left with a silent spinner        |
| The waiting state is keyboard- and screen-reader-complete | The whole exchange must be completable without a pointer                                     |
| Nothing about the credential is announced     | Assistive technology announces the **step**, never a value                                              |
| Loss of the page is explained, not hidden     | If the visit is lost, the participant is told what that means and what to do (`F-P15-05`)               |
