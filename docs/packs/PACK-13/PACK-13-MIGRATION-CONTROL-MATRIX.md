# PACK-13 — Migration Control Matrix

Specification-only. No code. Not implemented.

Companion to `PACK-13-SPECIFICATION.md` §18–§20 and
`ADR-075-DATABASE-MIGRATION-DISCIPLINE.md`.

---

## 1. Migration classes and their controls

| Class                                       | Example                                   | Approval                      | SoD          | Dry-run             | Rollback                            | Evidence                                          |
| ------------------------------------------- | ----------------------------------------- | ----------------------------- | ------------ | ------------------- | ----------------------------------- | ------------------------------------------------- |
| **Expand** — additive, compatible           | add nullable column, add index, add table | owner                         | —            | required            | drop the addition                   | plan + execution record                           |
| **Backfill** — data only                    | populate the new column                   | owner                         | —            | required            | none; forward-fix                   | plan + checkpoints + reconciliation report        |
| **Switch** — consumer cutover               | begin reading the new column              | owner                         | —            | required            | revert read path                    | plan + observation record                         |
| **Contract** — destructive                  | drop the old column                       | owner **+ separate approver** | **required** | **required**        | **stated real or forward-fix-only** | plan + approval + execution + verification        |
| **Corrective** — fixes an applied migration | new migration correcting an error         | owner + approver              | required     | required            | as contract                         | plan + the defect record it corrects              |
| **Emergency**                               | incident remediation                      | break-glass (PACK-12)         | **required** | best effort, stated | stated                              | **privileged session evidence + post-hoc review** |

`P13-MIG-017` A migration is assigned exactly one class, and the class
determines its controls. A migration that would fit two classes is split.

---

## 2. Gate matrix — what must be true before a migration runs

| Gate                               | Expand   | Backfill | Switch | Contract | Corrective | Emergency        |
| ---------------------------------- | -------- | -------- | ------ | -------- | ---------- | ---------------- |
| Stable migration ID                | ✔        | ✔        | ✔      | ✔        | ✔          | ✔                |
| Checksum recorded and verified     | ✔        | ✔        | ✔      | ✔        | ✔          | ✔                |
| Deterministic ordering position    | ✔        | ✔        | ✔      | ✔        | ✔          | ✔                |
| No edit to any applied migration   | ✔        | ✔        | ✔      | ✔        | ✔          | ✔                |
| Owner identified                   | ✔        | ✔        | ✔      | ✔        | ✔          | ✔                |
| Separate approver                  | —        | —        | —      | ✔        | ✔          | ✔                |
| Scoped PACK-12 privileged grant    | ✔        | ✔        | ✔      | ✔        | ✔          | break-glass      |
| Dry-run evidence                   | ✔        | ✔        | ✔      | ✔        | ✔          | stated if absent |
| Batching / resume strategy         | if large | **✔**    | —      | if large | if large   | —                |
| Organization scope preserved       | ✔        | ✔        | ✔      | ✔        | ✔          | ✔                |
| Retention / hold records preserved | ✔        | ✔        | ✔      | **✔**    | ✔          | ✔                |
| Document / evidence linkage intact | ✔        | ✔        | ✔      | **✔**    | ✔          | ✔                |
| No global user ID created          | ✔        | ✔        | ✔      | ✔        | ✔          | ✔                |
| Voting unlinkability preserved     | ✔        | ✔        | ✔      | ✔        | ✔          | ✔                |
| Consumer readiness confirmed       | —        | —        | ✔      | **✔**    | ✔          | —                |
| Observation period elapsed         | —        | —        | —      | **✔**    | —          | —                |
| Post-hoc independent review        | —        | —        | —      | —        | —          | **✔**            |

`P13-MIG-018` Every ✔ in the last five rows is an **acceptance criterion
with a test**, not a checklist item a reviewer ticks. `no global user ID
created` in particular is a structural check over the migration's DDL, not
a judgement call.

---

## 3. Failure handling

| Failure                                                       | Immediate behaviour                            | Recovery                              | Never                                             |
| ------------------------------------------------------------- | ---------------------------------------------- | ------------------------------------- | ------------------------------------------------- |
| Checksum mismatch on an applied migration                     | **halt, escalate**                             | investigate provenance                | auto-repair; recompute and store the new checksum |
| Out-of-order migration detected                               | **halt**                                       | resolve ordering                      | apply anyway "because it works"                   |
| Migration already applied                                     | no-op, recorded                                | —                                     | re-apply                                          |
| Partial failure mid-migration                                 | **halt, preserve state, escalate**             | resume from checkpoint or forward-fix | auto-continue past an error                       |
| Backfill conflict (target already populated, different value) | route the record to review                     | human decision                        | overwrite; pick the "newer"                       |
| Rollback requested but untested                               | **refuse or execute with explicit acceptance** | forward-fix                           | present an untested script as a safety net        |
| Legal-hold state unknown during a destructive step            | **fail closed**                                | resolve hold state first              | proceed and reconcile later                       |
| Evidence write fails                                          | **halt**                                       | retry the evidence write              | proceed unevidenced                               |

---

## 4. Expand/contract sequence controls

| Step                                             | Required before proceeding                  | Evidence produced                   |
| ------------------------------------------------ | ------------------------------------------- | ----------------------------------- |
| 1. Add new structure                             | schema published; compatibility classified  | migration execution record          |
| 2. Dual-read / dual-write **(only if governed)** | **reconciliation strategy approved**        | reconciliation design reference     |
| 3. Backfill                                      | batching plan; rate limit; policy awareness | checkpoints; reconciliation report  |
| 4. Verify                                        | verification query defined in advance       | verification record                 |
| 5. Migrate consumers                             | consumer registry shows readiness           | consumer readiness record           |
| 6. Stop old writes                               | all producers migrated                      | execution record                    |
| 7. Observe                                       | **minimum duration elapsed** (OD-P13-04)    | observation record                  |
| 8. Remove old structure                          | contract-class gates in §2                  | destructive execution record        |
| 9. Archive evidence                              | all of the above                            | evidence bundle reference (PACK-11) |

`P13-XC-005` Steps 6 and 8 are never performed in the same change window.
The observation step exists precisely because divergence is discovered by
running, not by reviewing.

`P13-XC-006` Dual-write without an approved reconciliation strategy is
**forbidden** (`P13-XC-002`). Two writes that nobody compares are two
sources of truth.

---

## 5. Backfill control detail

| Property                  | Requirement                                  | How it is demonstrated                                     |
| ------------------------- | -------------------------------------------- | ---------------------------------------------------------- |
| Deterministic             | same input, same output                      | replay over a fixture set                                  |
| Restartable               | resumes from checkpoint                      | kill-and-resume test                                       |
| Idempotent                | re-running changes nothing                   | double-run test                                            |
| Checkpointed              | progress durable                             | checkpoint records                                         |
| Rate-limited              | bounded load                                 | configured limit + observed throughput                     |
| Organization-aware        | scope preserved and never crossed            | per-scope counts reconcile                                 |
| Policy-aware              | retention, hold and classification respected | held records untouched; report                             |
| Audited                   | who ran it, when, with what authority        | PACK-12 session evidence                                   |
| Verifiable                | counts reconcile                             | reconciliation report                                      |
| **Invents nothing**       | no defaulted or inferred facts               | unresolved records routed to review, counted in the report |
| No sensitive data in logs | structural                                   | log-content scan                                           |

`P13-BF-015` The reconciliation report is **mandatory output**, not an
optional artifact. A backfill that completed without one has not
demonstrably completed.
