# EPD² PILOT Roadmap Lock

**Status:** LOCKED  
**Effective:** 2026-08-19  
**Machine-readable source:** `docs/roadmap/EPD2_PILOT_ROADMAP_LOCK.json`

This document is the canonical stage-number/scope lock for the EPD² PILOT line. A candidate, developer report, archived recommendation, handover note or implementation package may not redefine the meaning of a numbered PILOT stage.

## Locked roadmap

| Stage    | Canonical scope                             |
| -------- | ------------------------------------------- |
| PILOT-01 | Internal Organization Pilot                 |
| PILOT-02 | Membership & Participation Pilot            |
| PILOT-03 | Assemblies / Motions / Communications Pilot |
| PILOT-04 | Non-binding Digital Vote Pilot              |
| PILOT-05 | Representative Desk / Transparency Pilot    |
| PILOT-06 | Pilot Findings & Corrections                |
| PILOT-07 | Production Readiness Decision               |

`NON_BINDING_PILOT` remains in force until a separate governed activation decision changes it.

## Explicit supersession of stale PILOT-02 guidance

The accepted immutable predecessor remains:

`EPD2_PILOT02_PUBLIC_SITE_INTEGRATION_AND_UNIFIED_PILOT_PRODUCT_CANDIDATE_0.51.2_C4.zip`

SHA-256:

`261ab0996659f453d3d6d3cf43e12ad105fa6dbacd5035de40ca949029cbfc3e`

Inside that accepted archive, the historical file:

`docs/pilot/PILOT-02/25_NEXT_GATE_RECOMMENDATION.md`

contains stale next-gate guidance describing PILOT-03 as **Pilot Operation Readiness** and instructing that assemblies/messaging not be added.

That guidance is **SUPERSEDED** by this roadmap lock.

The accepted PILOT-02 archive MUST NOT be rewritten because doing so would invalidate its accepted SHA-256 and destroy the evidence chain. Historical text may remain in the immutable predecessor, but it has no authority over the stage definitions above.

## PILOT-03 accepted predecessor and required scope

PILOT-03 MUST build on the accepted PILOT-02 C4 artifact identified above.

Its product scope MUST include, at minimum:

- assemblies;
- motions;
- communications;
- member frontend integration for those capabilities.

Deployment/operations readiness does not satisfy PILOT-03.

## Separate operations workstream

Deployment, environments, secrets, ingress/TLS, backup/restore, restart/crash recovery and operational lifecycle work is preserved as a separate workstream:

**PILOT-OPS — Deployment & Operations Readiness**

It MUST NOT be renumbered as PILOT-03. Useful PILOT-OPS evidence may later feed production-readiness work, including PILOT-07 where applicable.

## Mandatory candidate scope manifest

Starting with PILOT-03, every PILOT candidate MUST contain:

`docs/roadmap/PILOT_STAGE_SCOPE.json`

The manifest MUST state:

- `stage_id`;
- exact canonical `stage_title`;
- roadmap lock schema version;
- accepted predecessor filename/SHA where fixed;
- required capabilities;
- `non_binding_pilot` status.

A candidate may not self-define or rename its stage.

**Scope mismatch is a fatal candidate defect and is checked before functional testing.**

## Verification discipline

For every future PILOT candidate, independent verification begins in this order:

1. exact ZIP name/SHA and single-root integrity;
2. roadmap-lock and candidate-scope consistency;
3. predecessor identity and declared diff;
4. only then functional/security/runtime tests.

A candidate that fails step 2 is rejected immediately as wrong-scope; time is not spent running the full technical battery for the wrong stage.

## Governance rule

If any future document conflicts with this lock, the conflict MUST be surfaced explicitly. It may not be silently reconciled in favor of the newer package.

Changing this roadmap requires an explicit project-level roadmap decision and a deliberate update to both this Markdown lock and its machine-readable JSON counterpart.
