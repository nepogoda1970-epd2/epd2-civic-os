# EPD2 GitHub Handoff Map

Purpose: pre-created transport locations for future governed blocks. These branches are **transport-only** and are never, by themselves, acceptance branches or acceptance evidence.

Created from main baseline `d2595263fdc95d193dca9d45fed170d5058051f1` on 2026-08-27. Their age relative to later accepted baselines is irrelevant because authoritative acceptance must use a separately constructed exact lineage.

| Block | Transport branch | Upload folder |
|---|---|---|
| API-02 | `handoff/api-02` | `handoff/API-02/incoming/` |
| API-03 | `handoff/api-03` | `handoff/API-03/incoming/` |
| API-04 | `handoff/api-04` | `handoff/API-04/incoming/` |
| API-05 | `handoff/api-05` | `handoff/API-05/incoming/` |
| API-06 | `handoff/api-06` | `handoff/API-06/incoming/` |
| INFRA | `handoff/infra` | `handoff/INFRA/incoming/` |
| OPS | `handoff/ops` | `handoff/OPS/incoming/` |
| SYSTEM TRIAL PREVIEW | `handoff/system-trial-preview` | `handoff/SYSTEM_TRIAL_PREVIEW/incoming/` |
| CTRL | `handoff/ctrl` | `handoff/CTRL/incoming/` |
| FRONT | `handoff/front` | `handoff/FRONT/incoming/` |
| FINAL INTEGRATION | `handoff/final-integration` | `handoff/FINAL_INTEGRATION/incoming/` |
| SEC | `handoff/sec` | `handoff/SEC/incoming/` |

## User upload rule

When a block is ready, upload the exact sealed candidate ZIP into that block's `incoming/` folder. Upload the developer report, inventory/manifest, and SHA-256 text alongside it when available.

Do not unpack, rename, regenerate, or re-pack a sealed candidate merely for GitHub transport. If GitHub receives bytes different from the locally reported artifact, treat that as a transport/packaging defect and stop.

## Intake rule

The registered workflow `.github/workflows/epd2-handoff-intake.yml` is transport verification only. It checks out the chosen transport branch, verifies exact SHA-256 and size when provided, and uploads the candidate plus generated intake metadata as a GitHub Actions artifact.

A successful intake run means only `EXACT_BYTES_TRANSPORTED`. It does **not** mean `PASS`, `ACCEPTED`, `CLOSED`, `FROZEN`, or `READY`.

## Authoritative acceptance rule

For every governed stage, authoritative acceptance must be constructed separately from the exact accepted predecessor baseline and exact transported candidate bytes, with the stage-specific authoritative workflow/validator registered before the acceptance run.

Never reuse an unrelated workflow as a transport hack. Never infer acceptance from a transport branch or intake artifact.

API-03 special rule: PRE-SEAL working drops are not authoritative candidates. The final API-03 C1 may be transported only after reconciliation onto exact independently accepted API-02 bytes.

SYSTEM TRIAL PREVIEW and FINAL INTEGRATION are checkpoints, not architecture layers. SEC must consume the exact accepted final integrated baseline.
