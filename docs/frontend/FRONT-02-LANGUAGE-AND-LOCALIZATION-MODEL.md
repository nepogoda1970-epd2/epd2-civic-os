# EPD² FRONT-02 Language and Localization Model

**Status:** GOVERNED FRONT-02 REFINEMENT / IMPLEMENTATION NOT STARTED  
**Date:** 2026-08-26  
**Parent specification:** `docs/frontend/FRONT-02-SPECIFICATION.md`  
**Execution state impact:** none — `API = NEXT`; `FRONT-02 = SPECIFICATION ESTABLISHED / IMPLEMENTATION NOT STARTED`

## 1. Purpose

This refinement fixes the DE/EN language model for EPD² frontend work. It implements the already-established architecture requirement that the baseline is DE/EN-ready while preserving German as the authoritative language for legally, procedurally and institutionally material content.

The model is:

```text
one governed route model
→ German canonical route paths
→ DE default / authoritative rendition where authority matters
→ EN supported translation rendition
→ one shared language selector
→ no second independent English route authority
```

This is a localization layer over the existing ten-workspace architecture. It does not create another workspace, another session system, another public site, or a second set of authoritative domain records.

## 2. Language roles

### 2.1 German

German (`de`) is:

- the default frontend language;
- the authoritative language for official German party rules, legal/procedural notices, governed forms and other content whose legal or procedural meaning depends on exact wording, unless a later governed decision explicitly states otherwise;
- the authoritative reference when an English translation and the German source diverge.

Where authority matters, the UI must make the authoritative German source identifiable and accessible.

### 2.2 English

English (`en`) is a fully supported frontend translation language for public and authenticated user-facing surfaces, subject to governed translation availability and approval for the relevant content version.

An English rendition:

- must not silently acquire independent legal or procedural effect;
- must remain linked to the exact German source/version it translates;
- must expose translation status when the content is legally, procedurally or institutionally material;
- must never silently continue to present a superseded translation after the German authoritative source has materially changed.

## 3. Route model

German public-route continuity remains canonical under `FRONT-02-SPECIFICATION.md` and `FRONT-02-PUBLIC-PAGE-ROUTE-DECISIONS.csv`.

Examples:

- `/programm` remains the canonical program route;
- `/programmwerkstatt` remains the canonical workshop route;
- `/regionen` remains the canonical region route;
- `/transparenz` remains the canonical transparency route;
- `/aktuelles` remains the canonical news route.

English target-blueprint paths such as `/home`, `/principles`, `/news`, `/elections`, `/donate` and `/roadmap` remain compatibility aliases/redirect inputs. They do not become a parallel authoritative English information architecture.

Language is a rendition state of the same governed route. A shareable language selection may be represented by an allowlisted locale parameter such as `?lang=en` / `?lang=de`, or an equivalent later governed localization mechanism, provided that:

- the canonical route identity remains unchanged;
- the locale parameter never changes authorization, eligibility, organization scope, workflow state or legal effect;
- unknown/unsupported locale values fail safely to German with an explicit fallback where material;
- language selection is not used as a cross-workspace tracking identifier.

## 4. Shared language selector

Every normal frontend shell that offers both languages must provide a visible `DE | EN` language selector.

The selector:

- uses the existing canonical visual language and nearest existing link/button pattern;
- does not redesign the FRONT-00/FRONT-01 header or shell;
- clearly indicates the active language;
- is keyboard operable and has an accessible name;
- updates the document language (`<html lang="de">` or `<html lang="en">`);
- preserves the current governed route and safe non-authority query state where possible;
- must not trigger or imply authentication, authorization, submission, voting or other consequential actions.

For WS-01 the selector belongs in the shared public header. For authenticated workspaces it belongs in the shared workspace shell/header and remains visually subordinate to primary navigation and authority/scope indicators.

## 5. Preference storage and privacy

Language preference is non-authoritative display state.

It may be stored only as a minimal language preference, for example `de` or `en`, using the storage/cookie rules of the owning origin.

It must not contain or encode:

- user identity;
- member status;
- political-interest categories;
- organization scope;
- voting eligibility or voting-event identity;
- case identifiers;
- cross-workspace correlation identifiers.

There is no shared authentication cookie, shared local storage or storage bridge between workspaces merely to synchronize language preference.

An explicit workspace handoff may carry `lang=de|en` as a non-identifying display hint. The target workspace remains responsible for its own authorization and may persist its own local language preference independently.

## 6. Governed translation content

Translation is governed content, not ad-hoc frontend copy.

For material translated content, the system must be able to associate at least:

- source content/version ID;
- language;
- translation version ID;
- translation status (`draft`, `under_review`, `approved`, `superseded` or equivalent governed state);
- effective/publication date where applicable;
- approval evidence;
- source/translation digest or equivalent immutable identity;
- supersession relationship;
- authoritative-language reference.

This refines and applies `FIR-FORM-004` to the frontend language layer.

## 7. Fallback and divergence

A missing, stale or unapproved English translation must never be silently presented as current authoritative content.

The governed fallback is:

1. preserve access to the current German authoritative rendition;
2. show a concise English notice that the English translation is unavailable, under review or out of date;
3. identify German as authoritative where the wording has legal or procedural significance;
4. preserve the user’s ability to return to English navigation/help without disguising untranslated material as translated.

For non-material editorial content, controlled temporary fallback may be simpler, but the interface must not produce a misleading mixed-language state that suggests a complete approved translation where none exists.

If DE and EN versions materially diverge, German governs unless a later explicit legal/governance decision establishes another authority rule for that exact content class.

## 8. Forms, notices and consequential actions

For governed forms and consequential journeys:

- button/action semantics remain identical across languages;
- English labels must map to the same action state as their German equivalents;
- confirmation, warning, receipt and error text must be versioned when material;
- the authoritative German wording must remain referenceable;
- translation may not change consent scope, eligibility conditions, deadlines, legal consequences or decision meaning.

The DE action vocabulary governed by `FIR-UX-005`/`FIR-UX-007` remains the semantic reference. English is a translation of those semantics, not a second action taxonomy.

## 9. Voting-client language

WS-03 may offer DE and EN presentation without weakening voting isolation.

Language selection:

- must not alter credential scope, eligibility, ballot identity, tally rules or receipt semantics;
- must not introduce a member identifier into WS-03;
- must not create a cross-origin storage bridge to WS-02;
- may be carried only as a non-identifying locale hint or selected locally in WS-03.

Where ballot titles, candidate names, options or binding instructions are translated, the translation must be tied to the exact governed ballot definition and its authoritative source. Translation changes are not ballot-definition changes unless the authoritative ballot content itself changes.

## 10. Search, publication and metadata

Public search must respect language without expanding authorization.

Search/index/rendition metadata should support language and source-version linkage. A translated search result may only point to an approved/openable rendition.

Public pages must provide correct document language metadata. Where technically supported, alternate-language metadata (`hreflang` or equivalent) may point to the same canonical route with an explicit language rendition state; it must not create competing route authority.

## 11. Regional/local pages

The regional operating model remains unchanged.

`/regionen` and `/regionen/[slug]` use the same DE/EN translation layer as the rest of WS-01. Regional bodies do not receive independent translation systems or local English mini-sites.

Regional content remains centrally governed and organization-scoped; language selection changes only the rendition language, never organization scope or authority.

## 12. Accessibility

The DE/EN layer is part of the accessibility definition of done.

At minimum:

- `<html lang>` matches the active language;
- language changes inside a page are programmatically marked where needed;
- the language selector is keyboard and screen-reader operable;
- translated labels preserve accessible names and relationships;
- error summaries and validation messages are available in the active supported language or use an explicit governed fallback;
- no critical action disappears because a translation is missing.

## 13. Acceptance requirements

FRONT-02 derived artefacts and later implementation evidence must cover DE/EN explicitly.

At minimum:

- Page Catalogue: language availability/status per page family;
- Navigation Map: `DE | EN` selector and route-preserving behavior;
- Content Map: authoritative DE source and EN translation relationships;
- Action Map: equivalent action semantics across languages;
- Screen-State Matrix: missing/stale/unapproved translation and language fallback;
- Permission & Assurance Matrix: language never changes authorization;
- Accessibility Flow: selector, document language and fallback behavior;
- Acceptance Screenshot Inventory: representative DE and EN screenshots for public, member, voting and scoped administrative shells.

A candidate fails this refinement when it:

- creates a second independent English route authority;
- allows translation state to alter authorization or workflow authority;
- silently presents stale/unapproved material English text as current authoritative content;
- lacks an accessible language selector where both languages are offered;
- uses shared cross-origin identity/session storage to synchronize language preference;
- changes the canonical FRONT-00/FRONT-01 visual baseline merely to add localization.

## 14. FIR disposition

This refinement creates **no new FIR ID** and changes no FIR status.

It refines/applies existing obligations under:

- `FIR-FORM-004 — Governed Form Content and Language Catalogue`;
- `FIR-UX-004 — Information Architecture and Navigation Governance`;
- `FIR-UX-007 — Content Design and Terminology Governance`;
- `FIR-UX-008 — Responsive and Multi-Device Experience`;
- `FIR-UX-011 — Frontend Pre-Implementation Specification Gate`;
- the existing accessibility/language architecture gap `AGR-27`;
- existing workspace/session/privacy invariants.

No current execution state changes. `API = NEXT`; FRONT-02 remains specification established and implementation not started.