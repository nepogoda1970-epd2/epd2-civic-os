# EPD² System Trial Preview — Prerequisite Placement 0.1

**Status:** GOVERNANCE SCHEDULING DECISION — STAGED OFF-MAIN PENDING SAFE CANONICAL INSTALLATION  
**Decision date:** 2026-09-04  
**Authority baseline:** `main@7544f5dc3bf40304ae81b4d8ef476cc8ecb60ec5`  
**Purpose:** fix the implementation placement of the remaining System Trial Preview prerequisites without changing any existing stage acceptance state or prematurely opening System Trial Preview.

## 1. Why this record is staged off-main

INFRA-04 is currently performing exact canonical rebind/sealing against `main@7544f5dc3bf40304ae81b4d8ef476cc8ecb60ec5`. Moving `main` solely to record this scheduling decision would make that exact baseline stale and force another governance rebind. Therefore this placement decision is intentionally committed on a separate governance branch and MUST be installed/reconciled into canonical `main` only at a controlled point after the current INFRA-04 qualification/acceptance transaction or after an explicit rebind to the then-current main.

This staging status does **not** weaken the decision below; it only prevents an avoidable moving-baseline defect in the active INFRA-04 line.

## 2. Preview prerequisite placement

The remaining preview-readiness prerequisites are assigned as follows.

| Preview prerequisite | Governed implementation placement | Required outcome before preview checkpoint |
| --- | --- | --- |
| **PRQ-17 — deployed observability stack with its own access control and retention** | **INFRA-05 — Preview Observability Deployment & Evidence** | real deployed observability backend, access control, retention, permitted telemetry, alert/health evidence and deployment identity; hooks alone are insufficient |
| **PRQ-18 — real authenticated principals behind the operational role model** | **SEC-PREVIEW-01 — Real Authenticated Principals & Operational Role Binding** | real authenticated principals, accepted Identity/Auth runtime binding, governed operational-role binding and negative authorization evidence; mocks/fixtures alone are insufficient |
| **PRQ-19 — trusted external time source** | **INFRA-06 — Trusted Time Foundation & Preview Deployment** | real trusted external time source, provenance/skew/fail-closed behaviour and runtime evidence; local machine clock alone is insufficient |
| **PRQ-20 — recorded governance decision on the INFRA/OPS preview-readiness minimum** | **GOVERNANCE CHECKPOINT — not an implementation module** | separate post-evidence decision that the complete INFRA/OPS preview-readiness minimum is satisfied |

`INFRA-07` is **not required for the first System Trial Preview merely by stage number**. It becomes a preview blocker only if a later explicit governed decision assigns an unmet preview prerequisite to INFRA-07.

## 3. Relationship to INFRA-04

`INFRA-04 — Production Container Platform` remains a separately governed prerequisite platform stage. It provides the deployment/runtime substrate and integration hooks used by later preview work, but its acceptance does not by itself prove PRQ-17, PRQ-18 or PRQ-19.

No change to INFRA-04 scope, candidate identity, acceptance harness or current qualification state is made by this record.

## 4. Parallel-development rule

Development MAY begin in parallel before INFRA-04 is accepted, subject to the following fail-closed boundaries:

### INFRA-05

Permitted immediately as `PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED`.

It may develop:
- observability deployment manifests/configuration;
- privacy-safe metrics/logging/tracing policy enforcement;
- access-control and retention configuration;
- alerting/health evidence collectors;
- deterministic validation and mutation suites.

It MUST NOT seal or claim authoritative acceptance against an unaccepted INFRA-04 platform identity. Before seal it must reconcile/rebase to the exact independently accepted INFRA-04 bytes/state and prove deployment compatibility.

### INFRA-06

Permitted immediately as `PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED`.

It may develop:
- trusted-time provider abstraction and concrete preview deployment profile;
- time provenance/skew monitoring;
- rollback/jump detection;
- fail-closed/degraded behaviour;
- deterministic and mutation tests.

It MUST NOT seal or claim authoritative acceptance until it is reconciled with the exact accepted INFRA platform/runtime state on which its real preview deployment executes.

### SEC-PREVIEW-01

Permitted immediately as `PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED` because the API Identity/Auth foundation is already accepted/closed.

It may develop:
- real-principal integration against the accepted authentication/authorization runtime;
- operational-role binding;
- session/principal provenance evidence;
- negative authorization and stale/revoked-principal tests;
- preview-environment identity integration.

It MUST preserve all voting-domain identity freezes and trust-boundary invariants. It MUST NOT call itself final SEC, security certification, production readiness or accepted before independent governed review. Final seal must bind the exact accepted API identity/auth state and the exact preview deployment/runtime state needed by the integration.

## 5. Acceptance ordering versus development ordering

Development ordering and acceptance ordering are deliberately different.

Allowed development concurrency:

`INFRA-04 || INFRA-05 || INFRA-06 || SEC-PREVIEW-01`

with INFRA-05/06/SEC-PREVIEW-01 limited to preseal/not-accepted status until their exact predecessor/runtime bindings are available.

Required checkpoint logic:

1. INFRA-04 independently accepted/closed as its bounded stage.
2. PRQ-17 independently proven by INFRA-05 exact deployed evidence.
3. PRQ-19 independently proven by INFRA-06 exact trusted-time evidence.
4. PRQ-18 independently proven by SEC-PREVIEW-01 exact real-principal/role-binding evidence.
5. All existing OPS-owned preview-minimum prerequisites remain independently accepted/evidenced.
6. Governance records **PRQ-20 PASS** only after the complete current INFRA/OPS preview-readiness minimum is proven.
7. A separate explicit governance decision may then set **`SYSTEM TRIAL PREVIEW = OPEN`**.
8. Only after that decision may the **FIRST END-TO-END PROBNIK** be treated as opened/authorized.

No module may self-create steps 6 or 7.

## 6. Non-claims

This decision does NOT:
- accept or close INFRA-04, INFRA-05, INFRA-06, INFRA-07 or any SEC stage;
- close the INFRA layer;
- close the OPS layer;
- open System Trial Preview;
- claim production readiness;
- claim final security acceptance;
- alter BSI/Common Criteria status;
- weaken `no persistent member/person identifier inside voting domain` or any voting isolation invariant.

## 7. Canonical installation requirement

At the first safe governance point after the active INFRA-04 exact-baseline transaction, install/reconcile this placement decision into the canonical Program Control Register and current stage contracts. The installation must use the then-current exact `main` commit/tree/PCR identity and must not overwrite a newer accepted state.

Until that installation, this file is the recorded project-owner scheduling decision on branch `governance/preview-prereq-placement`, intentionally staged off-main to avoid destabilizing INFRA-04.