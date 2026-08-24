# EPD² Program Control Register

**Status:** Living canonical execution-state register  
**Location:** `docs/roadmap/EPD2_PROGRAM_CONTROL_REGISTER.md`  
**Updated:** 2026-08-25  
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

**Repository reconciliation note:** the canonical Master Register already
exists at the path above, but the GitHub copy inspected when this control
register was introduced predates the V16 maintenance copy. It must be
reconciled to V16 before a repository-only task may rely on V16-specific FIR
content. Until that reconciliation is complete, the conflict rule in
`EPD2_PROJECT_ENTRYPOINT.md` applies: do not silently infer or downgrade the
Master state.

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
| PILOT | `PARALLEL_DEVELOPMENT_EXISTS` | PILOT is not a blank future phase. PILOT-01…05 have existing lineage/work. Exact stage state is governed by section 5. PILOT work must not be misdescribed as nonexistent, but unaccepted candidates must not be promoted to accepted baselines. |

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
preparatory or already-existing parallel work in later layers or in the PILOT
line when that work does not make unsupported runtime, production,
legal-activation or security claims.

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
  corpora and test-harness preparation;
- corrective/specification work on an already-existing PILOT stage, provided
  its stage lock, predecessor rule and acceptance discipline are preserved.

Parallel work must not claim the later layer or PILOT stage `CLOSED`, `PASS`,
`ACCEPTED`, `PRODUCTION_READY` or `LEGALLY_ACTIVATED` before its governed
acceptance gate.

---

## 5. PILOT execution state

The canonical PILOT stage meanings remain locked by:

`docs/roadmap/EPD2_PILOT_ROADMAP_LOCK.md`

### PILOT-01 — Internal Organization Pilot

**Control state:** `COMPLETED_IN_INHERITED_ACCEPTED_LINEAGE`

PILOT-01 functionality/history is inherited by the later accepted cumulative
PILOT baseline. This reconstruction does not re-issue a separate PILOT-01
acceptance identity. If a task depends specifically on the original PILOT-01
candidate SHA, that identity must be re-opened from its historical acceptance
evidence rather than guessed.

### PILOT-02 — Membership & Participation Pilot

**Control state:** `ACCEPTED_HISTORY / SUPERSEDED_AS_CURRENT_BASELINE`

The roadmap lock records the accepted immutable predecessor:

`EPD2_PILOT02_PUBLIC_SITE_INTEGRATION_AND_UNIFIED_PILOT_PRODUCT_CANDIDATE_0.51.2_C4.zip`

SHA-256:

`261ab0996659f453d3d6d3cf43e12ad105fa6dbacd5035de40ca949029cbfc3e`

Its stale historical next-gate guidance is explicitly superseded by the current
PILOT roadmap lock and must not redefine later stage numbering.

### PILOT-03 — Assemblies / Motions / Communications Pilot

**Control state:** `ACCEPTED / ESTABLISHED`

Accepted cumulative application baseline:

`EPD2_PILOT03_ASSEMBLIES_MOTIONS_AND_COMMUNICATIONS_CANDIDATE_0.1_C3.zip`

SHA-256:

`52b5bbfe312d90d65f500f0b6085d33ffe3235ce4bd90562110a26a8fae208d1`

This is the accepted application predecessor repeatedly used as an external
trust anchor by the later DATA line.

### PILOT-04 — Non-binding Digital Vote Pilot

**Control state:** `DEVELOPED / NOT ACCEPTED_FROZEN`

The preserved PILOT-04 corrective line reaches at least C9 internally.
The C9 acceptance-state document records:

```text
LOCAL_PASS                              reached
READY_FOR_INDEPENDENT_GITHUB_ACCEPTANCE reached
GITHUB_AUTHORITATIVE_PASS              NOT REACHED
ACCEPTED_FROZEN                         NOT REACHED
```

Therefore PILOT-04 must not be called accepted or frozen on the basis of the
preserved candidate alone.

Important historical point for PILOT-05: its governed stage scope was opened
against exact PILOT-04 C7:

`EPD2_PILOT04_NON_BINDING_DIGITAL_VOTE_PILOT_CANDIDATE_0.1_C7.zip`

SHA-256:

`812652950e996bd7c781512e4bbc03488c58eb74ca0c652c2b830056d76c1f1d`

PILOT-05 explicitly treated that C7 hash as an exact-byte predecessor pin,
**not** as proof that PILOT-04 had been independently accepted.

### PILOT-05 — Representative Desk / Transparency Pilot

**Control state:** `SUBSTANTIAL C2 CORRECTIVE IMPLEMENTATION EXISTS / NOT ACCEPTED`

On 2026-08-25 the preserved two-part PILOT-05 artifact was reassembled as one
valid ZIP with one cumulative root:

`EPD2_PILOT05_REPRESENTATIVE_DESK_AND_TRANSPARENCY_PILOT_CANDIDATE_0.1_C2`

Reassembled artifact SHA-256:

`eb1fc9be21b479a07fd76c082d9964343049f6ba2b0f319677f8d4b9b74515c9`

Archive member count:

`3728`

This is substantial implemented product work, not a future idea. The preserved
PILOT-05 dossier contains, among other things:

- executive result;
- predecessor/scope record;
- route map;
- API exposure register;
- authorization matrix;
- architecture/domain description;
- threat model;
- user journey;
- test evidence;
- changed-file inventory;
- explicit open-gaps record;
- runtime migrations and tests;
- member/public frontend integration.

The C1 slice built a bounded representative constituency desk plus a separate
transparency/publication authority. The central invariant is that the desk is
not the publisher: desk authorities and publication authorities are separated,
private constituent material does not directly become public material, and
publication is a separate governed chain.

The preserved C2 tree contains at least two explicit C2 corrections:

1. `F-01 — true two-principal publication approval`
   - C1 allowed one authenticated caller to supply the identity of a supposed
     countersigner.
   - C2 changes this to two separate authenticated acts/transactions and binds
     both approvals to the same approval-subject digest.
   - migration: `0015_pilot05_two_principal_approval.sql`.

2. `F-02 — constituent correlation boundary`
   - C1 kept all inputs needed to recompute a constituent reference in the same
     database and therefore overstated unlinkability against a DB-dump attacker.
   - C2 moves the pseudonym derivation secret outside the database and uses a
     keyed HMAC construction with an explicit key version.
   - migration: `0016_pilot05_constituent_correlation_boundary.sql`.

However the reassembled C2 artifact is **not accepted** and must not be treated
as an acceptance-ready governed C2 baseline yet, because its package identity
and its internal acceptance governance are inconsistent:

- archive/root name says `...C2`;
- PILOT-05 executive/scope dossier still identifies `PILOT-05 C1`;
- lineage file is still `PILOT05_C1_LINEAGE.json` and names candidate `C1`;
- validator is still `scripts/validate_pilot05_c1.py`;
- the C1 changed-file inventory remains named as the governed stage inventory;
- no independently verified C2 acceptance record was found in this
  reconstruction.

Therefore the current governing interpretation is:

```text
PILOT-05 product work exists through C2 corrective code
PILOT-05 C2 acceptance package = NOT RECONCILED
PILOT-05 = NOT ACCEPTED
```

This work must be preserved. A future PILOT-05 continuation should start from
this C2 material only after a governed C2 lineage/inventory/validator package is
reconstructed and independently verified; it must not restart PILOT-05 from
scratch or silently discard the C2 corrections.

The C1 dossier also records open gaps that remain relevant unless a later
verified C2 artifact explicitly closes them, including: erasure/deletion
governance, approval staleness interval, text redaction, live office-mandate
authority integration, coordinated abuse controls, delegation, and a browser
end-to-end journey for PILOT-05 pages.

### PILOT-06 — Pilot Findings & Corrections

**Control state:** `NOT_STARTED_AS_GOVERNED_STAGE`

Do not open PILOT-06 merely because corrections have occurred inside PILOT-04
or PILOT-05. PILOT-06 has its own locked stage meaning.

### PILOT-07 — Production Readiness Decision

**Control state:** `NOT_STARTED`

No production-readiness decision is implied by the existing PILOT work.

---

## 6. Current frontend governance notes

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

## 7. Status-change discipline

A layer or PILOT stage may move to `CLOSED`, `ACCEPTED` or `ESTABLISHED` only
when the governed evidence for that exact layer/stage supports the transition.

Every change to one of the status rows or stage states above must state:

- previous state;
- new state;
- governing candidate/final artifact or repository commit;
- SHA-256 or equivalent immutable identity where applicable;
- acceptance/verification evidence;
- blockers left open;
- next permitted primary stage.

No status may be changed merely because a conversation says it is convenient.

---

## 8. Branch and reconciliation discipline

There is exactly one canonical Program Control Register.

A branch:

1. reads the target/current register as its entering state;
2. changes only facts supported by its own governed work/evidence;
3. never silently resets a newer state to an older one;
4. never creates a second competing control register.

At merge, reconcile against the target branch's current copy rather than
blindly replacing it with the branch copy.

---

## 9. Required repository gate

Governed cumulative candidates should fail when:

- `EPD2_PROJECT_ENTRYPOINT.md` is absent;
- `EPD2_PROGRAM_CONTROL_REGISTER.md` is absent;
- `EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md` is absent;
- more than one competing control/master register exists;
- the Program Control Register contradicts the governed stage represented by
  the candidate;
- the Program Control Register is stale after a layer/status transition.

---

## 10. Immediate execution decision

**Next primary development series: API.**

PILOT-05 substantial work is explicitly preserved as a parallel existing line.
It should not be restarted from zero. Its next legitimate step is a governed C2
acceptance-package reconciliation / independent verification, which may be
performed in parallel when prioritized, without changing `API = NEXT` as the
primary implementation sequence.
