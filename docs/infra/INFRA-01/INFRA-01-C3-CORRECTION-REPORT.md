# INFRA-01 — C3 Correction Report

**Stage:** INFRA-01 — CI Acceptance Harness & Release-Integrity Foundation  
**Correction:** C3 — current-authority reconciliation and package-identity repair  
**Candidate self-state:** `CANDIDATE_NOT_ACCEPTED` / `PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED`  
**Date:** 2026-09-01

## 1. Reason for C3

C2's implementation and governed mutation coverage passed independent inspection, but its sealed governance reconciliation was correctly rejected after the canonical target advanced from `main@556821e0e5d550a4db601bbe92e4f4673a1bc3ff` to `main@3d0b2fec5f86c491f36de1041caa66d983727480`.

The current target records API-03 C5 as `ACCEPTED / CLOSED` and API-04 as `ACTIVE / IN DEVELOPMENT / NOT ACCEPTED`. C2 still bound its reconciliation to the earlier API-03-active state. GitHub freshness proof run `33532645632` therefore failed closed with `TARGET_AUTHORITY_MISMATCH`, exactly as designed.

A second packaging-identity defect was discovered during independent preparation for canonical execution: the C2 harness generated `EPD2_INFRA01_CI_ACCEPTANCE_HARNESS_CANDIDATE_0.1_C2.zip`, while the packaged workflow attempted to upload `EPD2_INFRA01_CI_ACCEPTANCE_HARNESS_CANDIDATE_0.1.zip`. A successful harness would therefore have been followed by an artifact-upload failure. C3 repairs that filename binding without changing runtime or test semantics.

## 2. Exact current target authority

- repository: `nepogoda1970-epd2/epd2-civic-os`
- branch: `main`
- commit: `c333b9dd12e0c13dd402222cc958d95e779b8488`
- tree: `bc58993ff881a23c2193afdfe6b71e30e945f4f8`
- commit timestamp: `2026-09-01T17:13:28Z`
- commit message: `gov(front03): accept C1 and close bounded FRONT-03 stage`
- Program Control Register Git blob: `addcbc09d99c53bc8f0f39e4568949cac4dd2cf0`
- Program Control Register SHA-256: `c985cd17eb79ea4390a5c183581629a4d729e37f1485f1fba935cce2d5cc825d`
- Master Register Git blob: `7f5c6a9a88f8e653b43dc542a595ac37bf7a0692`
- Master Register SHA-256: `3cb40d8c46baa4126702a60cb3138b3776548eda4549fc4ec0dd6163c83c1a3d`

The API-03 C5 acceptance and API-04 activation remain preserved. During C3 pre-acceptance preparation, `main` advanced once more to `c333b9dd12e0c13dd402222cc958d95e779b8488` solely for bounded FRONT-03 C1 acceptance. Because no authoritative C3 PASS had yet occurred, C3 was refreshed in the same correction round rather than creating C4. The exact FRONT-03 acceptance record is carried and the candidate PCR preserves that new state while leaving the overall FRONT layer open.

## 3. C3 changes

C3 does not alter INFRA-01 execution semantics, fail-closed detector semantics, check registry meaning, M17–M22 mutation logic, service/runtime behavior, or security boundaries.

C3 only:

1. carries the exact current `docs/api/API-03/API03_C5_ACCEPTANCE_RECORD.json` and `docs/frontend/FRONT-03-C1-ACCEPTANCE-RECORD.json` bytes from main;
2. reconciles current PCR state to API-03 CLOSED / API-04 ACTIVE and bounded FRONT-03 C1 ACCEPTED/CLOSED while preserving the INFRA-01 pre-seal candidate state;
3. reseals `INFRA01_GOVERNANCE_RECONCILIATION.json` against current main;
4. updates the harness candidate package identity from C2 to C3;
5. fixes the packaged workflow upload path to that same C3 identity;
6. adds exact C0→C3 and C2→C3 archive-byte inventories with no exclusions, including generated package metadata;
7. reseals package checksums and freeze inventory.

## 4. Required result semantics

A local or GitHub canonical harness PASS is execution evidence only. The candidate does not self-accept. Independent post-run governance may move INFRA-01 to an accepted state only after the exact sealed C3 bytes have completed the authoritative external run with no failed or environment-blocked mandatory gate.
