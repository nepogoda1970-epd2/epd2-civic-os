# organization-service

Sole authoritative owner of `Organization` (canon 8.1, extended by canon
section 19e), `OrganizationalUnit`, `CivicSpace` (canon 8.2, unchanged —
first real implementation), `OrganizationalRelation`,
`OrganizationalHierarchyOverlapPolicy`, `OrganizationalInheritancePolicy`,
and `OrganizationalAuthority` — PACK-08 implementation round (canon-0.7.0,
ADR-032 through ADR-037).

## Scope

This service implements exactly the canon-0.7.0/PACK-08-SPECIFICATION.md
model: multiple typed organizational relationship graphs, effective
dating, reorganization workflows with a hard no-automatic-rights-transfer
invariant, default-deny regional scope authorization across six explicit
access modes, institutional authority assignment/lifecycle/incompatibility,
and temporary supervision with a 90-day default maximum. See
`docs/packs/PACK-08-IMPLEMENTATION.md` for the full implementation report
and `docs/canonical/TZ-00-domain-event-canon.md` section 19e for the
canonical model itself.

## Explicitly out of scope (this round)

Production database, production event bus/transport, real IAM/eID,
voting cryptography, finance, Rechenschaftsbericht, document service,
search, DLP, arbitration workflow, legal hold, production deployment,
secrets management, HSM/KMS, mobile application, a full regional
administration portal, and a cross-regional member directory — all
explicitly out of scope per this round's own governing request.

## Storage

In-memory reference adapters only (`storage.py`), following the same
pattern every prior pack's own service already establishes — no
production database. Effective-dated queries are deterministic and never
mutate or overwrite a past record; every store keeps every version of
every record it has ever seen.

## Module layout

- `domain.py` — entities, statuses, allowed-transition tables, cycle and
  overlap detection, the minimum role-incompatibility baseline, and the
  effective-dating helpers.
- `application.py` — commands (create/activate/suspend/dissolve/merge/
  split/declare-successor, relation create/end/reassign, authority
  assign/activate/revoke) and the `check_regional_scope_access` default-
  deny authorization engine.
- `events.py` — the thirteen canonical events (canon section 20.5,
  19e.20).
- `exceptions.py` — reason-code-tied exceptions (canon section 24).
- `storage.py` — storage protocols and in-memory reference adapters.

## Cross-service boundary

This service imports only `epd2_core`/`epd2_audit_core` (the same
boundary every prior pack's own service observes,
`tests/repository/test_service_boundaries.py`). No other service is wired
to call into `organization-service` in this implementation round — a
future round may add that edge under its own ADR.
