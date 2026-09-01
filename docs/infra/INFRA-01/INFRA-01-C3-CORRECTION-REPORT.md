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
- commit: `3d0b2fec5f86c491f36de1041caa66d983727480`
- tree: `684a5777cee8ef608716d12514e9b7dc673048d5`
- commit timestamp: `2026-09-01T13:20:03Z`
- commit message: `gov(api03): close C5 and advance primary API-04`
- Program Control Register Git blob: `cee1163943023ddafe942c032309e7967fb7883c`
- Program Control Register SHA-256: `0a4acf40b5254405e6ff3abeaf6671c845d765225f422322b8b0b0f09d3083a0`
- Master Register Git blob: `7f5c6a9a88f8e653b43dc542a595ac37bf7a0692`
- Master Register SHA-256: `3cb40d8c46baa4126702a60cb3138b3776548eda4549fc4ec0dd6163c83c1a3d`

The two commits that advanced main after the C2 target are narrowly preserved: `f3f59563cf5397106c74034b26ab6f23534f3897` adds the exact API-03 C5 acceptance record, and `3d0b2fec5f86c491f36de1041caa66d983727480` advances the canonical PCR to API-03 CLOSED / API-04 ACTIVE.

## 3. C3 changes

C3 does not alter INFRA-01 execution semantics, fail-closed detector semantics, check registry meaning, M17–M22 mutation logic, service/runtime behavior, or security boundaries.

C3 only:

1. carries the exact current `docs/api/API-03/API03_C5_ACCEPTANCE_RECORD.json` bytes from main;
2. reconciles current PCR state to API-03 CLOSED / API-04 ACTIVE while preserving the INFRA-01 pre-seal candidate state;
3. reseals `INFRA01_GOVERNANCE_RECONCILIATION.json` against current main;
4. updates the harness candidate package identity from C2 to C3;
5. fixes the packaged workflow upload path to that same C3 identity;
6. adds exact C0→C3 and C2→C3 archive-byte inventories with no exclusions, including generated package metadata;
7. reseals package checksums and freeze inventory.

## 4. Required result semantics

A local or GitHub canonical harness PASS is execution evidence only. The candidate does not self-accept. Independent post-run governance may move INFRA-01 to an accepted state only after the exact sealed C3 bytes have completed the authoritative external run with no failed or environment-blocked mandatory gate.
