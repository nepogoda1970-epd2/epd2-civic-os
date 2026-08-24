# EPD² Program Control Register

**Status:** Living canonical execution-state register  
**Location:** `docs/roadmap/EPD2_PROGRAM_CONTROL_REGISTER.md`  
**Updated:** 2026-08-24  
**Purpose:** single authoritative source for the current execution state of the
EPD² development program.

This document answers only operational program-control questions:

- What is already closed?
- What is active or next?
- What may proceed in parallel?
- What must wait?
- Which canonical governance files must be read?
- Which stage owns the next execution decision?

It does not replace the Master Future Implementation Register.

---

## 1. Canonical bootstrap and governance sources

Mandatory first read:

`docs/roadmap/EPD2_PROJECT_ENTRYPOINT.md`

Current-state authority:

`docs/roadmap/EPD2_PROGRAM_CONTROL_REGISTER.md`

Future-requirement / governance authority:

`docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md`

Current Master maintenance level established by the project governance work:
**V16**, including `FIR-UX-012` and `FIR-UX-013`.

---

## 2. Program phase state

| Program layer | Current control state | Execution rule |
| --- | --- | --- |
| ARCH PACK-01…35 | `CLOSED` | Do not restart architectural PACK sequencing as current work. Corrections remain governed when evidence requires them. |
| DATA | `CLOSED` | Treat DATA as completed current program layer. Do not describe it as still being finished unless a new governed correction explicitly reopens it. |
| API | `NEXT` | Next primary runtime/development series. |
| INFRA | `NOT_STARTED` | Preparation/specification may proceed where it does not assume unproven API/runtime facts. Final implementation follows API dependencies. |
| OPS | `NOT_STARTED` | Procedures, state models and runbooks may be prepared; runtime operational closure follows INFRA. |
| CTRL | `NOT_STARTED` | Control-plane architecture, action inventory, roles, read models and screen specifications may be prepared. Integrated control-plane closure follows OPS/INFRA mechanisms. |
| FRONT | `NOT_STARTED_FINAL` | Shared/public frontend work, page specifications and governed static/read-only surfaces may proceed. Final integrated user journeys follow runtime/control-plane dependencies. |
| SEC | `NOT_STARTED_FINAL` | Threat models, adversarial fixtures and security tooling may proceed. Final penetration/adversarial/security baseline is performed against the integrated system. |
| PILOT | `FUTURE` | Begins only after the required integrated readiness/security decision. |

---

## 3. Governing execution sequence

The canonical closure sequence is:

```text
DATA → API → INFRA → OPS → CTRL → FRONT → SEC
```

Current position:

```text
DATA = CLOSED
API = NEXT
```

This sequence governs final dependency closure. It does **not** prohibit
preparatory work in later layers when that work does not make unsupported
runtime, production, legal-activation or security claims.

---

## 4. Parallel work currently permitted

While API is the next primary series, the following may proceed in parallel:

- INFRA specifications, environment/container topology, CI/CD and
  release/deployment-manifest design;
- OPS procedures, incident/recovery/change/election-operation runbooks and
  separation-of-duties models;
- CTRL control-plane specifications, action/authority inventories, read models
  and screen catalogues;
- FRONT shared design/application shells, public website work, page catalogues,
  accessibility/responsive baselines and non-misleading read-only/public
  surfaces;
- SEC threat-model consolidation, secret/supply-chain controls, adversarial
  corpora and test-harness preparation.

Parallel work must not claim the later layer `CLOSED`, `PASS`,
`PRODUCTION_READY` or `LEGALLY_ACTIVATED` before its governed acceptance gate.

---

## 5. Current frontend governance notes

The current Master Register includes:

- `FIR-UX-012 — Public Transparency Information Architecture & Verification Surface`;
- `FIR-UX-013 — Global EPD² Identity Line`.

The exact global public identity expansion fixed by `FIR-UX-013` is:

`Erste Partei Direkte Demokratie`

It is to appear directly beneath the standard upper-left `EPD²` logo on every
public page using the shared EPD² header, without redesigning the logo or public
visual baseline.

These are governance requirements and do not by themselves constitute frontend
implementation or acceptance.

---

## 6. Status-change discipline

A layer may move to `CLOSED` only when the governed evidence for that layer
supports closure.

Every change to one of the status rows above must state:

- previous state;
- new state;
- governing candidate/final artifact or repository commit;
- SHA-256 or equivalent immutable identity where applicable;
- acceptance/verification evidence;
- blockers left open;
- next permitted primary stage.

No status may be changed merely because a conversation says it is convenient.

---

## 7. Branch and reconciliation discipline

There is exactly one canonical Program Control Register.

A branch:

1. reads the target/current register as its entering state;
2. changes only facts supported by its own governed work/evidence;
3. never silently resets a newer state to an older one;
4. never creates a second competing control register.

At merge, reconcile against the target branch's current copy rather than
blindly replacing it with the branch copy.

---

## 8. Required repository gate

Governed cumulative candidates should fail when:

- `EPD2_PROJECT_ENTRYPOINT.md` is absent;
- `EPD2_PROGRAM_CONTROL_REGISTER.md` is absent;
- `EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md` is absent;
- more than one competing control/master register exists;
- the Program Control Register contradicts the governed stage represented by
  the candidate;
- the Program Control Register is stale after a layer/status transition.

---

## 9. Immediate execution decision

**Next primary development series: API.**

Later-layer preparatory work is permitted only under section 4 and does not
change the primary sequence or current control state.
