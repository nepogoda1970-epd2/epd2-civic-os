# INFRA-01 — C2 Correction Report

**Stage:** `INFRA-01 — CI Acceptance Harness & Release-Integrity Foundation`
**Correction:** `C2` — exact-inventory / reconciliation-provenance correction
**Business scope:** NONE
**Self-state:** `PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED / CANDIDATE_NOT_ACCEPTED`

```text
INFRA-01 C2 CORRECTION CANDIDATE
LOCAL CANONICAL HARNESS: see INFRA-01-ACCEPTANCE-MATRIX.md
EXTERNAL GOVERNED ACCEPTANCE: NOT YET PERFORMED
NOT PRODUCTION READY
NOT LEGALLY ACTIVATED
```

## 1. Lineage and target authority

| field                                  | value                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| -------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| exact entering (C1) candidate          | `EPD2_INFRA01_CI_ACCEPTANCE_HARNESS_CANDIDATE_0.1_C1.zip`, SHA-256 `085373b7a6ba623e9a3e661c7c0cedfca1506a2903505dbc7ace56de54f27452` (15,832,415 bytes, 1453 members)                                                                                                                                                                                                                                                                 |
| exact C0 predecessor                   | `EPD2_INFRA01_CI_ACCEPTANCE_HARNESS_CANDIDATE_0.1.zip`, SHA-256 `3bb42509a9db56d34db2bade38a3e73af1a202599392e257c91f3b3627743210`                                                                                                                                                                                                                                                                                                     |
| independent verdict on C1              | `REJECTED / CORRECTION REQUIRED` (INFRA01-C2-01, INFRA01-C2-02)                                                                                                                                                                                                                                                                                                                                                                        |
| target authority re-checked at C2 seal | `nepogoda1970-epd2/epd2-civic-os` `main` — re-fetched and unchanged: commit `556821e0e5d550a4db601bbe92e4f4673a1bc3ff`, tree `95fb9c911db229cf589330531b14f41b7049235e`, PCR blob `2269540db0d6955f5ec0999d0448b3af4ec196f1` / SHA `8f27b4687d8fc1ea84084d1ee95824eda9cd58edcd504407592923d64a34d240`, Master blob `7f5c6a9a88f8e653b43dc542a595ac37bf7a0692` / SHA `3cb40d8c46baa4126702a60cb3138b3776548eda4549fc4ec0dd6163c83c1a3d` |
| target commit timestamp                | `2026-09-01T12:10:51+01:00` (= `2026-09-01T11:10:51Z`)                                                                                                                                                                                                                                                                                                                                                                                 |
| actual `reconciled_at` (C2 reseal)     | recorded truthfully in `INFRA01_GOVERNANCE_RECONCILIATION.json` (schema `/2`); mechanically enforced `reconciled_at >= target_commit_timestamp`                                                                                                                                                                                                                                                                                        |
| source lineage                         | unchanged: Entering Baseline Identity v1.1 (`8ff32c3e…`, repository 0.16.0, canon 0.8.0); no runtime/domain import                                                                                                                                                                                                                                                                                                                     |
| C2 candidate archive                   | `EPD2_INFRA01_CI_ACCEPTANCE_HARNESS_CANDIDATE_0.1_C2.zip`; exact SHA-256 in the `.sha256` sidecar and the sealed execution manifest                                                                                                                                                                                                                                                                                                    |

## 2. Finding dispositions

**INFRA01-C2-01 (exact C0→C1 inventory objectively false) — CORRECTED.**
The C1 inventory omitted `SHA256SUMS.txt` and
`ACCEPTANCE/FREEZE-INVENTORY.json` and declared `modified = 12` where the
archive-byte truth is `modified = 14`; its "exclusion-free" claim was false.
C2 replaces it with `INFRA01_C0_TO_C2_EXACT_INVENTORY.json`, measured
against archive bytes with **no exclusions** — every delivered ZIP path
accounted, packaging metadata included (classified `generated_metadata`,
never omitted from counts), the inventory document itself listed. The
superseded C0→C1 error is preserved on record inside the new inventory's
`supersedes` block and as an erratum in the C1 correction report — history
is corrected with disclosure, not rewritten. A deterministic exact-delta
verifier ships as `scripts/acceptance/delta.py` with the CLI
`uv run python -m scripts.acceptance verify-delta --predecessor <zip>
--candidate <zip> --inventory <json>`, recomputing
added/modified/removed/unchanged from archive bytes and comparing both path
membership and declared counts; divergence fails closed with
`CORRECTION_INVENTORY_MISMATCH` (mutation M21). The exact measured counts
for the final sealed archives are stated in §4.

**INFRA01-C2-02 (temporally impossible reconciliation provenance) —
CORRECTED.** The C1 record claimed `reconciled_at =
2026-09-01T01:30:00+00:00`, 9 h 40 m 51 s before its own target commit
existed. At C2 seal the target `main` was re-fetched (unchanged at
`556821e0…`), the record now carries the truthful
`target_commit_timestamp` and a truthful `reconciled_at`, and was resealed
(schema `epd2.infra01.governance-reconciliation/2`). The validator now
mechanically enforces temporal provenance — missing/unparseable timestamps,
`reconciled_at < target_commit_timestamp`, or a future `reconciled_at`
fail closed with `RECONCILIATION_TIME_INVALID` (mutation M22); a record in
the old `/1` shape without temporal fields also fails closed. Timestamps
are never left to human inspection.

## 3. New detector codes and mutations

`CORRECTION_INVENTORY_MISMATCH` (M21: omitted packaging metadata; also
phantom paths and false counts) and `RECONCILIATION_TIME_INVALID` (M22:
reconciliation predating target; also future timestamps and missing
temporal fields). 21 negative mutation classes now map onto 21 distinct
detector codes; M20 remains the mandatory positive history fixture. M01–M20
preserved untouched; the 55-test regression floor is preserved and extended
(63 passing across the two harness test files); no §6 control weakened. BSI
V26 files remain byte-identical to their §7-pinned identities.

## 4. Exact inventories (measured from final sealed archive bytes)

`INFRA01_C0_TO_C2_EXACT_INVENTORY.json` — C0 (`3bb42509…`) → C2, all paths
including packaging metadata; supersedes the false C0→C1 inventory and
records its error. `INFRA01_C1_TO_C2_EXACT_INVENTORY.json` — C1
(`085373b7…`) → C2. Exact counts are inside the inventories and were
verified with `verify-delta` against the final sealed C2 archive (see the
delivery note); the developer precheck refuses handoff on any mismatch.

## 5. Developer verification

Targeted suites (63 passed ≥ 55 floor + M21/M22), `verify-reconciliation`
PASS with current-target comparison against re-fetched `main`,
`verify-delta` PASS for both inventories against the final sealed archive,
full canonical harness (43 governed checks) PASS — matrix in
`INFRA-01-ACCEPTANCE-MATRIX.md`, machine-readable proof in the sealed
`EXECUTION-MANIFEST.json`. Developer-local PASS is not authoritative
acceptance (C2 assignment §12).
