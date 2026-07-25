"""Organization & Regional Scope Service (CLAUDE-PACK-08 implementation
round, canon-0.7.0, section 19e; ADR-032 through ADR-037).

Sole authoritative owner of `Organization`, `OrganizationalUnit`,
`CivicSpace`, `OrganizationalRelation`, `OrganizationalHierarchyOverlapPolicy`,
`OrganizationalInheritancePolicy`, and `OrganizationalAuthority`. Other
services may consume read models or capability-check results through this
package's `application` module; none may independently reconstruct or
broaden organizational authority (canon 19e.1, 19e.12).
"""
