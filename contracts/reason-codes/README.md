# Reason Codes

`pack-02.yml` in this directory is the executable, centralized reason-code
registry required by `CLAUDE-PACK-02` section 10. It is loaded at runtime
by `epd2_core.reason_codes.ReasonCodeRegistry.load_from_yaml`.

## Contents

- All 22 canon codes from `docs/canonical/TZ-00-domain-event-canon.md`,
  section 24 (`source: canon`), copied verbatim — their meaning is fixed
  by canon and can only change via a canon ADR and version bump.
- 16 additive codes introduced by this pack (`source: pack-02-adr-004`),
  documented and justified in
  `docs/adr/ADR-004-reason-code-registry.md` — generic validation-layer
  codes reused across services, audit-integrity codes, credential-specific
  validation failures, and `AuditEvent.reason_code` classifications for
  successfully-audited actions (canon's section-24 list is refusal-only
  and has no code that means "this succeeded").

## Rules

- No service may use a free-text string in place of a registered code
  (canon section 24). Every `reason_code`/`reason_codes` literal in
  `services/*/src` must appear in `pack-02.yml` — enforced by
  `tests/contract/test_reason_codes_registry.py`.
- New reason codes require an ADR (see ADR-004 for the precedent) and are
  additive only: no entry's `code` or `meaning` may be repurposed once
  merged.
- `introduced_in_version` is `"0.1.0"` for canon-defined codes and
  `"pack-02-0.1.0"` for pack-introduced codes.

## Status

Executable (previously documentary-only in PACK-01). Loaded and validated
by `epd2_core.reason_codes`. The PACK-02 services' `exceptions.py` /
`validation.py` modules reference these codes by string literal rather
than importing the registry at raise-time, since `epd2_core.reason_codes`
requires PyYAML, which the domain services' own `pyproject.toml` files do
not declare as a dependency (services intentionally have no direct
dependency on YAML parsing). Consistency between every literal actually
used and this registry is verified structurally by
`tests/contract/test_reason_codes_registry.py`.
