# PACK-08 — Organization & Regional Scope Glossary

Companion terminology reference for canon `0.7.0` section 19e
("Организация и региональная авторизация — расширение / Organization &
Regional Scope Context"). This file is documentation only: it defines
no field, event, or reason code that is not already fixed by canon
section 19e; where the two disagree, canon section 19e is authoritative
and this glossary should be corrected to match it, not the reverse.

## The four non-interchangeable concepts (canon 19e.2)

- **Organization** — a governed, real-world organizational node owned
  exclusively by `organization-service` (canon 8.1, extended 19e.3),
  identified by `organization_id`.
- **Jurisdiction** — a geographic or legal fact external to this
  platform's own organizational structure (e.g. "DE", "Berlin"), never
  itself an `Organization` node.
- **CivicSpace** — a process-local area of participation nested under
  an `Organization` (canon 8.2, unchanged), identified by `space_id`.
- **Scope, process-local** — an opaque `scope_type`/`scope_id` pair
  meaning "the specific object instance a capability check or policy
  applies to," today not an organizational reference in most services
  that carry it.

These four may reference one another but are never substitutable for
one another, and none of `organization_id`, `jurisdiction`,
`region_code`, `scope_id`, `civic_space_id` may be silently
reinterpreted across domains (canon 19e.2).

## New canonical entities (canon 19e, owner: `organization-service` unless noted)

- **`OrganizationalUnit`** — a lighter-weight node for subordinate
  structures not themselves a full `Organization` in the legal/statutory
  sense (19e.5).
- **`OrganizationalRelation`** — the typed, versioned, effective-dated
  edge connecting two `Organization`/`OrganizationalUnit` nodes; three
  relation categories (hierarchy, continuity, cooperation) form
  multiple typed directed graphs, not a single tree (19e.7).
- **`OrganizationalHierarchyOverlapPolicy`** — governs when more than
  one concurrent hierarchy-category parent edge may exist for one node
  (19e.8).
- **`OrganizationalInheritancePolicy`** — governs ancestor/descendant
  regional-scope access; owned by the Organization & Regional Scope
  domain; consuming domains may restrict, never broaden (19e.13).
- **`OrganizationalAuthority`** — an institutional, organizationally-
  scoped authority assignment (DPO, election board member, election
  officer, independent auditor, finance auditor, party arbitrator,
  organizational administrator); distinct from, and never merged with,
  the Governance Context's `RoleAssignment` (canon 8.4, unchanged)
  (19e.15).
- **`OrganizationalScope`** — a reusable, opaque scope-reference value
  shape naming exactly which of the four concepts above it references;
  not a separately owned entity (19e.11).

## Key rules, by name

- **Default-deny regional scope authorization** — every scope-access
  decision is denied unless one of six explicit modes grants it (exact,
  ancestor, descendant, delegated, temporary supervision, institutional
  oversight without data access) (19e.12).
- **No automatic rights transfer** — merger, split, and successor
  declaration never automatically move authority, roles, or access
  rights; every transfer requires its own explicit governed decision
  (19e.10).
- **`parent_reference` is not authoritative** — it is a derived
  projection of the current active `OrganizationalRelation` set, never
  independently mutated, and may be omitted entirely (19e.4).
- **Migration-blocked** — a `RoleAssignment.scope_id` `role_code`
  classified as category 6 (invalid/legacy ambiguous) may not be wired
  into scope-authorization logic until reclassified (19e.19).
- **Minimum baseline, subject to legal refinement** — the eight-bullet
  non-combinable-role matrix (19e.16) is a floor, not a ceiling; future
  legal review may make it stricter, never looser.

## Related documents

- Canon: `docs/canonical/TZ-00-domain-event-canon.md` section 19e.
- ADRs: `docs/adr/ADR-032` through `docs/adr/ADR-037`.
- Specification: `docs/packs/PACK-08-SPECIFICATION.md`.
- Migration matrix: `docs/packs/PACK-08-MIGRATION-MATRIX.md`.
- Open decisions: `docs/packs/PACK-08-OPEN-DECISIONS.md`.
- Canon amendment report: `docs/handover/PACK-08-CANON-AMENDMENT-REPORT.md`.
