# EPD² FRONT-02 Regional Operating Model

**Status:** GOVERNED FRONT-02 REFINEMENT / IMPLEMENTATION NOT STARTED  
**Date:** 2026-08-25  
**Parent specification:** `docs/frontend/FRONT-02-SPECIFICATION.md`  
**Execution state impact:** none — `API = NEXT`; `FRONT-02 = SPECIFICATION ESTABLISHED / IMPLEMENTATION NOT STARTED`

## 1. Purpose

This refinement fixes the frontend operating model for Landes-, Kreis-, Orts- and other governed regional party bodies. It does not create separate local products, separate local websites, separate local identity systems or separate voting engines.

The model is:

```text
one EPD² platform
→ one governed public information architecture
→ one authenticated member application
→ one isolated voting client
→ organization-scoped regional views and authority
```

The same frontend architecture is reused across territorial levels. Regional differentiation is produced by governed `organization_scope`, not by cloning applications or duplicating authoritative datasets.

## 2. Public regional hub — WS-01

Canonical public routes remain:

- `/regionen` — region directory / public discovery;
- `/regionen/[slug]` — approved public regional hub.

`/regionen` must support discovery by governed public organization data, including Bundesland and, where approved and technically available, Ort / PLZ routing to the competent public organization projection.

A regional detail page is a hub inside the common EPD² public site, not a separately designed mini-site. Its governed information architecture is:

1. `Übersicht`;
2. `Aktuelles`;
3. `Termine`;
4. `Initiativen`;
5. `Personen`;
6. `Wahlen`;
7. `Dokumente & Transparenz`;
8. `Kontakt`.

The exact public name and territorial level must be visible, for example `Landesverband Berlin`, `Kreisverband …` or `Ortsverband …`, together with the approved public competence/territory description.

Only approved public organization projections, approved public personas and approved public renditions may appear. A regional hub must never expose an internal membership directory, protected case data, voting linkage, staff-only organization records or privileged administration data.

## 3. Shared central content, regional filtering

Regional pages must not create independent copies of common content domains.

The following remain governed central content families and are filtered/projected by organization scope where applicable:

- `Aktuelles`;
- `Termine`;
- `Initiativen`;
- approved public `Personen`;
- public `Wahlen` information;
- governed public documents and transparency renditions.

Examples:

```text
Aktuelles → organization_scope = Berlin
Termine → organization_scope = Berlin
Initiativen → organization_scope = Berlin
Wahlen → organization_scope = Berlin
```

A content item may belong to Bund, Land, Kreis, Ortsverband or another governed body only when the authoritative source carries that scope. Frontend filtering must not invent territorial ownership.

The public regional hub may aggregate links to these scoped renditions, but the authoritative source remains the owning domain / publication projection.

## 4. Authenticated regional work — WS-02

A member uses the same WS-02 account and session for member-facing work across all scopes they are authorized to access. There is no separate account or local member application for each regional organization.

The currently active organization scope must be visible whenever it materially changes the meaning, authority or dataset of the current screen.

A governed scope selector may expose only scopes the current user is authorized to use, for example:

```text
Bereich: Bund
Bereich: Landesverband Berlin
Bereich: Kreisverband …
Bereich: Ortsverband …
```

Changing scope must:

- re-evaluate authorization and purpose;
- load only data available in the selected scope;
- clear or invalidate stale context that is not valid in the new scope;
- prevent a deep link from silently preserving authority from the previous scope;
- make the selected scope visible on consequential actions and receipts where relevant.

Ordinary regional access must not create broad cross-regional visibility. Access to another regional body requires an explicit governed grant or role valid for that scope.

## 5. Regional voting

There is no regional voting engine.

Binding or otherwise governed votes that require the voting trust boundary use the same isolated WS-03 Voting Client regardless of territorial level.

Example:

```text
WS-02 / Bereich: Landesverband Berlin
→ eligible voting event: Vorstandswahl Berlin
→ one-time purpose-scoped voting handoff
→ WS-03
→ ballot / review / receipt
→ governed certification / result publication
```

The handoff must carry only the minimum purpose and organization scope required for the voting event. The WS-02 member session is not transferred into WS-03.

Eligibility for a Bund, Land, Kreis or Ortsverband vote must be decided by the authoritative eligibility/rules layer for that exact event and scope. Frontend scope selection is not itself voting authority.

A non-binding meeting poll may remain inside the governed assembly context when its profile explicitly allows this and must not be presented as a secret cryptographic election.

## 6. Regional administration — WS-06 and other owning workspaces

Regional administrative work uses the same governed administrative architecture with scoped authority.

Examples:

```text
Landesgeschäftsstelle Berlin → organization_scope = Landesverband Berlin
Kreis administration → organization_scope = exact Kreisverband
local office role → organization_scope = exact governed body
```

Workspace access or a federal-level technical account does not automatically confer authority over all regional data. Authorization remains a function of role, purpose, organization scope, record scope and the owning domain policy.

No universal regional administrator or universal party-wide admin may be introduced.

## 7. Organization hierarchy and lifecycle boundary

FRONT-02 specifies how an existing governed organization scope is presented and navigated. It does not itself create legal or organizational authority to:

- establish a new Landes-, Kreis- or Ortsverband;
- dissolve or merge an organization;
- alter territorial competence;
- change office-holder authority;
- move members between organizations;
- resolve hierarchy or affiliation disputes.

Those actions remain domain-governed organization lifecycle work and require their own authoritative rules, evidence and acceptance.

The frontend must therefore distinguish between:

- displaying an approved existing organization projection;
- selecting an authorized working scope;
- performing a governed organization lifecycle change.

Only the first two are part of this FRONT-02 refinement.

## 8. Required derived artefact coverage

The FRONT-02 derived artefacts required by `FIR-UX-011` must cover this model explicitly.

At minimum:

- Page Catalogue: `/regionen`, `/regionen/[slug]` and scoped WS-02/WS-06 shells;
- Navigation Map: public regional hub and authenticated scope switching;
- Content Map: central domain content projected by organization scope;
- Action Map: scope-sensitive actions and safe WS-03 handoff;
- Screen-State Matrix: unauthorized scope, stale scope, moved/deprecated organization, unavailable regional projection;
- Permission & Assurance Matrix: Bund/Land/Kreis/Orts/body scope;
- Accessibility Flow: scope selector and regional navigation;
- Acceptance Screenshot Inventory: public hub, scoped member view, scoped administration and voting handoff state.

## 9. FIR disposition

This refinement creates **no new FIR ID** and changes no FIR status.

It refines existing obligations under:

- `FIR-UX-004 — Information Architecture and Navigation Governance`;
- `FIR-FRONT-001`;
- `FIR-FRONT-002`;
- `FIR-UX-011`;
- existing organization-scope, authorization and voting-isolation invariants.

The canonical Master Register must carry the same regional operating rule so that this frontend refinement cannot drift from future cross-cutting requirements.
