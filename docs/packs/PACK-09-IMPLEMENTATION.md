# PACK-09 — implementation notes

Companion to `PACK-09-SPECIFICATION.md`. What was built, how it follows
the conventions PACK-02 through PACK-08 established, and what is
deliberately absent.

## 1. Service layout

`services/compliance-service` follows the same five-module shape every
service in this repository uses:

| Module           | Contents                                                                                                                                                          |
| ---------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `domain.py`      | Frozen, slotted dataclasses and their structural invariants; pure functions (`evaluate_hold_applicability`, `assert_decision_maker_eligible`, `require_timezone`) |
| `events.py`      | Eight canonical event builders plus the `*_full_state_payload` snapshots fed to Audit Core's `before_hash`/`after_hash`                                           |
| `storage.py`     | One `Protocol` per aggregate plus an in-memory reference adapter; no delete method anywhere; create-once evidence; scoped lookups                                 |
| `application.py` | Commands with scope guards, `event_id` idempotency, Audit Core append and reason-coded refusals                                                                   |
| `exceptions.py`  | One class per registered reason code                                                                                                                              |

## 2. Conventions carried over from earlier packs

- **Dependency-injected `Clock`** — no command reads system time
  (`epd2_core.clock`). `test_a_fixed_clock_is_all_a_command_ever_reads`
  proves it.
- **Caller-supplied `event_id` idempotency (CT-00-04)** — replay
  detection goes through Audit Core's own `get_by_event_id`, exactly as
  `governance-service` and `organization-service` do. A retried command
  returns the recorded result rather than re-attempting the transition.
- **Audit Core append on every critical action (CT-00-07/INV-04)** — with
  canonical-JSON `before_hash`/`after_hash`. The hash chain stays
  verifiable across a full retention → authorize → destroy workflow
  (`test_the_audit_chain_stays_verifiable_across_a_full_workflow`).
- **Reason-coded refusal (canon section 24)** — every denial carries a
  code registered in `contracts/reason-codes/pack-09.yml`.
- **Optimistic concurrency** — `record_version`, `case_version`,
  `activity_version`, `request_version`, with optional
  `expected_*_version` parameters refusing on mismatch.
- **In-memory reference stores only** — production persistence is
  PACK-13 (ADR-038).

## 3. Design choices worth reading the code for

### Deadlines have no stored `status` or `due_at`

Both are `@property` values derived from an append-only `history` tuple.
That is why invariant 6 is structural: there is no field to overwrite. The
in-memory store adds a second, independent guard by refusing any write
whose history is not an extension of the stored prefix — so the guarantee
does not depend on every caller going through the domain methods.

### Due dates are computed on the local civil clock

`DeadlineDefinition.due_at` converts to the definition's named IANA zone,
adds days, and re-attaches the zone. A ten-day period spanning the March
DST change therefore lands on the same wall-clock time, and a deadline
started at 23:30 Berlin is due on the expected _local_ date rather than a
day later. Both cases are tested directly.

### Legal Hold has a third state

`indeterminate` is a real, storable state, not a placeholder.
`evaluate_hold_applicability` reports blocking and indeterminate holds
separately, because "the hold state could not be established" and "this
record is not yet eligible" are different facts. An indeterminate hold
_raises_ `LEGAL_HOLD_STATE_UNKNOWN` rather than returning an ineligible
verdict, so it can never be mistaken for an ordinary not-due answer.

### Only destructive dispositions are hold-blocked

`DESTRUCTIVE_DISPOSITION_ACTIONS` is `{delete, anonymize}`. `archive` and
`review` remain available under a hold, so a held record can still be
moved into managed storage or reviewed. Blocking those too would make
holds unworkable without protecting anything.

### Two-tier scope errors

Reads, and writes by a caller presenting no authority, report a foreign
organization's resource with the same `VALIDATION_RECORD_NOT_FOUND` as a
nonexistent one — same exception class, same message shape. The specific
`CROSS_ORGANIZATION_CASE_ACCESS_DENIED` / `CROSS_SCOPE_AUTHORITY_INVALID`
codes are reachable only by a caller who already asserted it holds
authority there. This is how invariant 14 (deterministic denial codes) and
the non-disclosure requirement are satisfied together rather than traded
off.

### Independence is one pure function

`domain.assert_decision_maker_eligible` takes the case, the candidate, the
appointer, the case's role assignments and its conflict declarations, and
raises. It has one call site
(`application.assign_independent_decision_maker`), so there is exactly one
implementation to review, and it is testable across every combination
without constructing a store.

### The authorization/record version binding

`authorize_destruction` transitions the record to `disposal_authorized`
_first_ and then binds the authorization to the version that transition
produced. Binding to the pre-transition version would have made every
authorization instantly stale, since `with_state` increments
`record_version` by design — a bug the test suite caught and which the
comment in `application.py` now records so it is not reintroduced.

## 4. Verification wiring added to the repository

PACK-09 is visible to the repository's own checks, not only to its own
tests:

| Check                                                     | PACK-09 wiring                                                                                                                                                                                                              |
| --------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `scripts/check_repository.py`                             | 44 new required paths (service files, ADRs, schemas, events, OpenAPI, reason codes, pack docs)                                                                                                                              |
| `tests/contract/_schema_helpers.py`                       | `PACK09_REASON_CODES_PATH`, `PACK09_OPENAPI_PATH`, `PACK09_SERVICE_DIRS`                                                                                                                                                    |
| `tests/contract/test_reason_codes_registry.py`            | pack-09 row (required fields, no duplicates, every literal registered, loads via `epd2_core`)                                                                                                                               |
| `tests/contract/test_openapi_contract.py`                 | ten PACK-09 assertions (tags, request bodies, reason-coded denials, no DELETE, three-step workflow present, no bulk/directory endpoint, no identity/voting property, explicit timestamp formats, component `$ref`s resolve) |
| `tests/contract/test_ct00_01_pack09_schema_validation.py` | new file: every entity schema and every event payload schema validated against real domain instances                                                                                                                        |
| `tests/contract/test_ct00_08_identity_leakage.py`         | PACK-09 section, exhaustive over every dataclass in the domain                                                                                                                                                              |
| `tests/contract/test_ct00_09_vote_linkability.py`         | PACK-09 section: import-boundary check, field check, schema-property check                                                                                                                                                  |
| `tests/repository/test_service_boundaries.py`             | `PACK09_SERVICE_PACKAGES` plus three PACK-09 tests, including the AST check that no store exposes a delete-shaped method                                                                                                    |
| `Makefile`                                                | `typecheck` now covers `services/compliance-service` — and `services/organization-service`, which had been missing since PACK-08                                                                                            |

CT-00-02 (unknown status), CT-00-03 (forbidden transition), CT-00-04
(idempotency), CT-00-06 (missing permission) and CT-00-07 (audit creation)
are covered for PACK-09 inside the service's own test suite rather than by
new sections in the shared CT-00 files — the same choice PACK-08 made for
`organization-service`, kept deliberately so the two rounds stay
consistent.

## 5. Deliberately absent

No production persistence, HTTP server, event-bus publication, document
storage, finance ledger, privileged administration, identity acquisition
or voting linkage. No panel/multi-decider arbitration model, no quorum
rule, no automatic conflict detection from organizational relationships —
conflicts must be _declared_; the system does not infer them (ADR-042
records this explicitly rather than implying coverage).

## 6. No claim of legal compliance

Repeated here because it belongs next to the code: this service provides a
governed workflow, evidence references and auditability. It does not
determine whether any retention schedule, legal basis, deadline
computation, data-subject response or arbitration decision satisfies the
GDPR, the BDSG, the Parteiengesetz or any other law.

## 7. Architecture & Domain Framework 0.8.1 additions

The Framework 0.8.1 Roadmap Amendment is authoritative for PACK-09 scope
for PACK-09. It extends the pack; nothing above is
withdrawn.

### 7.1 Module layout after the additions

| Module              | Owns                                                                                               |
| ------------------- | -------------------------------------------------------------------------------------------------- |
| `domain.py`         | records governance, Legal Hold (+ `RecordClass`, `HoldPropagationRecord`), registry, round-1 cases |
| `casework.py`       | the common legal-case substrate and its gates                                                      |
| `notices.py`        | the official-notice trust boundary and deadline triggers                                           |
| `dataprotection.py` | DPIA gate, activation decisions, transfers, consent withdrawal                                     |
| `references.py`     | the stable typed references PACK-09 publishes outward                                              |
| `events.py`         | 41 event builders and the audit-snapshot helpers                                                   |
| `application.py`    | 34 new commands alongside the round-1 set                                                          |
| `storage.py`        | 18 new Protocol/in-memory pairs alongside the round-1 set                                          |

### 7.2 The three-layer notice boundary, in one place

```
OfficialNotice          an authorized object exists      starts nothing
      |
ServiceAttempt          provider telemetry               starts nothing
      |                 (is_reconciled gates every rule)
NoticeEffectDecision    a governed determination         the ONLY deadline trigger
      |
DeadlineTrigger         recorded exactly once per deadline
```

`OfficialNotice` has no `served_at`, no `effective_at` and no
`establishes_legal_effect` — the concept is absent from the layer, not
merely false in it. `official_notice.issued` and
`service_attempt.recorded` each publish `establishes_legal_effect: false`
as a literal wire field, so a subscriber wiring the wrong event to a
deadline must override an explicit denial rather than merely omit a
check. See ADR-043.

### 7.3 What is structural rather than conventional

Each of these is enforced by a constructor or a derived property, so it
survives the next command somebody writes:

- `LegalCase.status`, `Hearing.status` and `ProceduralDecision`'s three
  statuses are derived from append-only histories. A status the history
  does not support is not expressible.
- `LegalCase.transition` refuses a substantive status without a bound
  jurisdiction. The gate is on the aggregate, not on a command.
- `ProceduralDecision.become_enforceable` refuses unless the decision is
  in effect; `suspend_effect` also stays enforceability.
- `InterimMeasure.__post_init__` refuses a granted measure without a
  human authority, without an end or review date, or without reasons.
- `DeadlineTrigger.__post_init__` refuses a telemetry source by name.
- `RecordClass.__post_init__` refuses an owner who is also the
  disposition authority.
- `FilingStore.update_intake` compares ten immutable fields; the notice
  effect and deadline trigger stores are create-once.
- No store in this service has a delete method, and no OpenAPI path is a
  DELETE.

### 7.4 Still deliberately absent

Everything in section 5 above, plus: no candidacy, nomination or ballot
admission entity (PACK-19); no assembly or motion entity (PACK-21); no
communication channel, template or message entity (PACK-22); no
complaints or investigation entity (PACK-23/24). For each, PACK-09
publishes only a typed reference in `references.py`. Propagation
completeness for Legal Holds is a deployment responsibility, not a
guarantee — see `docs/handover/PACK-09-KNOWN-LIMITATIONS.md` §2.
