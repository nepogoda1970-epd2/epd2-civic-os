# EPD² Project Entrypoint

**Status:** Canonical project bootstrap document  
**Location:** `docs/roadmap/EPD2_PROJECT_ENTRYPOINT.md`

This file is the mandatory first read for every EPD² development, verification,
planning, status-assessment, correction, packaging, release, frontend, data,
API, infrastructure, operations, control-plane or security task.

## 1. Mandatory read order

Before making any statement about what is finished, active, next, blocked,
permitted or ready, read in this order:

1. `docs/roadmap/EPD2_PROGRAM_CONTROL_REGISTER.md`
2. `docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md`
3. the current stage contract / handover named by the Program Control Register.

Do not infer current execution state from conversation history, old PACK/DATA/API
reports, archive filenames, remembered status, or a roadmap alone when these
canonical repository sources are available.

## 2. Authority split

`EPD2_PROGRAM_CONTROL_REGISTER.md`
is the authoritative source for the **current execution state**:
what is closed, active, next, blocked, permitted in parallel, and which baseline
is currently governing.

`EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md`
is the authoritative source for **future requirements, governance obligations,
hard invariants, deferred work and implementation conditions**.

Neither file replaces the other.

## 3. Conflict rule

If the Program Control Register, Master Future Implementation Register, current
stage contract, candidate contents or verification evidence disagree materially:

- do not guess;
- do not silently choose the older statement;
- do not claim PASS/CLOSED/READY;
- record the conflict and reconcile it through a governed update.

## 4. Update rule

Every governed stage/correction that changes current execution state must update
`EPD2_PROGRAM_CONTROL_REGISTER.md` in the same governed change.

Every governed change that creates, changes, supersedes or closes future
requirements must update
`EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md` in the same governed change.

No branch may create a competing project-control register or competing master
future-implementation register.

## 5. Branch / merge rule

A working branch reads the current canonical files as its entering state.
It may change only the status facts and governance entries justified by that
branch's work and evidence.

At merge/reconciliation, the target branch's current canonical state is the
base. A branch must not silently overwrite newer status or register changes.

## 6. Repository gate

Cumulative candidates and governed releases must contain exactly one canonical
copy of each of these files at these paths:

- `docs/roadmap/EPD2_PROJECT_ENTRYPOINT.md`
- `docs/roadmap/EPD2_PROGRAM_CONTROL_REGISTER.md`
- `docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md`

Repository governance should fail closed when a required file is missing,
duplicated as a competing register, or stale relative to the governed
stage/baseline represented by the candidate.

## 7. Voting / BSI certification-readiness bootstrap

Any task or acceptance decision that can affect the EPD² Voting trust boundary,
eligibility, Voting Client, ballot processing, cryptography, guardians, tally,
independent verification, voting audit/time/channels/recovery, or the
security-critical production environment must additionally read and apply:

- `docs/roadmap/EPD2_BSI_VOTING_BOOTSTRAP_RULE.md`;
- `docs/security/bsi/EPD2_BSI_CC_PP_0121_CERTIFICATION_READINESS_GAP_MATRIX_0.1.md`;
- `FIR-VOTE-BSI-001` in the Master Future Implementation Register.

From 2026-08-30 forward, Voting-affecting work must identify the BSI readiness
rows it touches and must not silently introduce a blocker to the future
certification target. A known blocker must either be closed or explicitly
recorded as deferred with an owner, rationale, required closure stage and
required evidence.

This is a **certification-readiness gate**, not a certification claim. It does
not alter historical execution state by itself and it does not authorize the
terms `BSI-certified`, `BSI compliant`, `CC compliant` or `EAL4` for the
current product.
