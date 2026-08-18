# EPD² PILOT Roadmap Lock

**Status:** LOCKED  
**Effective:** 2026-08-19  
**Machine-readable source:** `docs/roadmap/EPD2_PILOT_ROADMAP_LOCK.json`

This document is the canonical stage-number/scope lock for the EPD² PILOT line. A candidate, developer report, archived recommendation, handover note or implementation package may not redefine the meaning of a numbered PILOT stage.

## Locked roadmap

| Stage | Canonical scope |
|---|---|
| PILOT-01 | Internal Organization Pilot |
| PILOT-02 | Membership & Participation Pilot |
| PILOT-03 | Assemblies / Motions / Communications Pilot |
| PILOT-04 | Non-binding Digital Vote Pilot |
| PILOT-05 | Representative Desk / Transparency Pilot |
| PILOT-06 | Pilot Findings & Corrections |
| PILOT-07 | Production Readiness Decision |

`NON_BINDING_PILOT` remains in force until a separate governed activation decision changes it.

## Explicit supersession of stale PILOT-02 guidance

The accepted immutable predecessor remains:

`EPD2_PILOT02_PUBLIC_SITE_INTEGRATION_AND_UNIFIED_PILOT_PRODUCT_CANDIDATE_0.51.2_C4.zip`

SHA-256:

`261ab0996659f453d3d6d3cf43e12ad105fa6dbacd5035de40ca949029cbfc3e`

Inside that accepted archive, the historical file `docs/pilot/PILOT-02/25_NEXT_GATE_RECOMMENDATION.md` contains stale next-gate guidance describing PILOT-03 as **Pilot Operation Readiness** and instructing that assemblies/messaging not be added.

That guidance is **SUPERSEDED** by this roadmap lock. The accepted PILOT-02 archive MUST NOT be rewritten because doing so would invalidate its accepted SHA-256 and destroy the evidence chain.

## PILOT-03 rule

PILOT-03 MUST build on the accepted PILOT-02 C4 artifact and MUST include assemblies, motions, communications and member frontend integration. Deployment/operations readiness does not satisfy PILOT-03.

Deployment, environments, secrets, ingress/TLS, backup/restore, restart/crash recovery and operational lifecycle work is preserved separately as **PILOT-OPS — Deployment & Operations Readiness** and MUST NOT be renumbered as PILOT-03.

## Mandatory candidate scope manifest

Starting with PILOT-03, every candidate MUST contain `docs/roadmap/PILOT_STAGE_SCOPE.json` matching the machine-readable lock. Scope mismatch is a fatal candidate defect and is checked before functional testing.

## Verification order

1. exact ZIP/SHA and single-root integrity;
2. roadmap-lock and candidate-scope consistency;
3. predecessor identity and declared diff;
4. functional/security/runtime tests.

A candidate that fails step 2 is rejected immediately as wrong-scope.
