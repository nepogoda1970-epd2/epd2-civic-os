# EPD² FRONT-02 Programmwerkstatt Refinement

**Status:** GOVERNED FRONT-02 REFINEMENT / IMPLEMENTATION NOT STARTED  
**Date:** 2026-08-25  
**Parent specification:** `docs/frontend/FRONT-02-SPECIFICATION.md`

## Purpose

This refinement fixes the scalable public presentation of the Programmwerkstatt when the number of initiatives becomes large.

## Landing-page rule

The existing six process-stage cards may remain as the explanatory process overview.

Beneath them, the landing page shows a compact highlighted-initiative section with **3 to 6 initiatives maximum**. It must not become the full initiative catalogue.

Each highlighted initiative card should expose at least:

- title;
- concise problem/proposal summary;
- thematic area where assigned;
- current lifecycle stage;
- last meaningful update.

## Default ordering

The main initiative catalogue defaults to **Aktualität**.

During early/low-volume operation, actuality may be determined through governed recency and editorial/process relevance.

Once sufficient real participation data exists, the default ranking may automatically incorporate privacy-safe aggregate activity/attention signals. Participation in an associated consultation or vote may be one such signal, including the aggregate number of participants where publication of that aggregate is permitted.

This ranking is a discovery aid only. It is not a political decision, adoption gate or eligibility rule.

The ranking must never use or expose:

- ballot choice;
- voter identity;
- secret-vote linkage;
- protected participation data.

Public participation counts may be used only where the governing voting/publication rules permit publication of that aggregate.

Popularity must not silently suppress valid less-active initiatives. Alternative governed views must remain available, such as newest, lifecycle stage or thematic area.

## Large catalogues

The catalogue must use bounded pages rather than an endless feed. It must support stable pagination or an equivalent stable page model, plus search and filters. Filter and pagination state should be linkable/recoverable.

## Thematic sections

The information architecture must support thematic sections/categories without requiring them to be activated from day one.

Themes may later provide dedicated filtered views or landing sections while every initiative remains addressable through the common catalogue.

## Initiative detail

The detailed initiative page remains the place for the full problem statement, proposal/version, arguments and sources, review state, consultation/voting references, history and outcome.

WS-01 renders approved public information and safe handoffs only. Authenticated deliberation and voting remain in their owning workspaces.

## Governance disposition

This refinement introduces no new frontend execution state and does not change `API = NEXT` or `FRONT = FRONT-02_SPECIFIED / NOT_STARTED_FINAL`.

It refines the existing FRONT-02 obligations under `FIR-PROG-001`, `FIR-INIT-024`, `FIR-UX-004`, `FIR-UX-009`, `FIR-UX-010` and `FIR-UX-011`. No FIR status is promoted by this document.
