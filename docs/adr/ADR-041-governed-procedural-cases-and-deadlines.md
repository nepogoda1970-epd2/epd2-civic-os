# ADR-041: Governed procedural cases, deadlines, and organizational scope isolation

## Status

`accepted`

## Date

2026-07-26

## Context

Data-subject requests, compliance reviews, legal requests, arbitration and
internal disputes are all the same shape of thing: a case, opened inside
one organization, run by identifiable procedural roles, moving through a
constrained set of statuses, with required steps, referenced evidence, one
decision, and deadlines that can be suspended, resumed, extended,
escalated, met or missed.

Deadlines are where legal workflows most often go quietly wrong, and the
failure modes are specific:

- **History overwritten.** A deadline stored as a mutable `due_at` plus
  `status` loses its own past on every change. After a suspension and a
  resumption nobody can say what the original due date was, which is
  exactly what a dispute about timeliness turns on.
- **Silent reset.** Reopening a case, or a workflow change, creates a
  "new" deadline for the same obligation. The old one vanishes and the
  clock restarts, unnoticed.
- **Implicit timezone.** A deadline computed in UTC and reported to a
  German organization is off by one or two hours, which moves the due
  _date_ for anything falling near midnight — and DST makes the error
  inconsistent across the year.

Scope isolation is the other half of this ADR, and it is not separable
from it: a case, a deadline and a decision are all obligations, and an
organization that could create or alter another's obligations by knowing
an id would have an authority it never was granted.

## Problem

1. How should a governed case and its deadlines be modelled so that no
   transition can overwrite history and no replacement can happen
   silently?
2. How is timezone handling made explicit rather than assumed?
3. How is organizational scope isolated, given a Bund/Land/Kreis structure
   where hierarchy _looks_ like it should imply access?

## Considered options

For deadlines:

- **Option A — mutable `due_at` + `status` fields, separate audit log.**
  Conventional. History lives somewhere else and can diverge.
- **Option B — mutable fields plus an in-entity event list.** Better, but
  nothing stops a writer from setting `due_at` directly and appending
  nothing.
- **Option C — no stored `due_at`/`status` at all: both derived from an
  append-only `history` tuple.**

For scope:

- **Option D — hierarchical inheritance:** a parent organization inherits
  read/write over descendants.
- **Option E — flat isolation plus explicit, presented, capability-scoped
  grants.**

## Decision

### 1. Deadlines: Option C — history is the only state

`ProceduralDeadline` has **no** `status` field and **no** `due_at` field.
Both are `@property` values derived from an append-only
`history: tuple[DeadlineHistoryEntry, ...]`:

- `status` is `_STATUS_AFTER_EVENT[history[-1].event_type]`;
- `due_at` is the most recent entry's `due_at_after`.

Every transition (`suspend`, `resume`, `extend`, `satisfy`, `escalate`,
`expire`, `supersede`) appends exactly one entry recording `sequence`,
`event_type`, `occurred_at`, **`due_at_before`**, **`due_at_after`**,
`remaining_seconds`, `reason_code` and `actor_party_reference`. There is no
setter for either derived value, so PACK-09 required invariant 6
("deadline history is append-only") is structural rather than
conventional: a caller who wanted to overwrite the due date would have to
change the class.

`__post_init__` additionally requires that the first entry is `started`
and that sequences are contiguous from 1, and
`InMemoryProceduralDeadlineStore.save` refuses any write whose history is
not an extension of the stored prefix. Options A and B were rejected
because both leave a writable `due_at`; the guarantee has to be
unavailable, not merely discouraged.

Suspension preserves the _remaining_ period (`remaining_seconds`), and
resumption recomputes `due_at` as `now + remaining` — it does not restart
the full period.

### 2. No silent replacement

`start_deadline` refuses to create a second deadline for a
`(case, deadline_code)` pair that already has a live one (running,
suspended or escalated) unless the caller names it explicitly in
`supersedes_deadline_id`. When it does, the predecessor is _superseded_:
it keeps its entire history, gains a `superseded_by_deadline_id` link and a
final `superseded` entry, and the successor records
`supersedes_deadline_id`. The refusal is
`DEADLINE_SILENT_REPLACEMENT_REJECTED` (invariant 7). Reopening a case
therefore cannot quietly restart a clock.

### 3. Timezone is explicit or the operation is refused

`DeadlineDefinition.timezone` is a required IANA name, validated with
`zoneinfo` at construction; empty or unknown is
`DEADLINE_TIMEZONE_UNDETERMINED`, never a fallback to UTC. `due_at` is
computed on the _local civil clock_ — convert to the named zone, add days,
re-attach the zone — so a period spanning a DST change lands on the same
wall-clock time on the due date rather than drifting by an hour. Every
instance carries its own `timezone` so a due time can always be reported
in the zone it was computed in.

Separately, every `datetime` field on every PACK-09 entity is validated
timezone-aware at construction (`domain._require_aware`). A naive datetime
is a hard error, not a value silently read as UTC.

### 4. Cases: constrained transitions, distinguishable roles, referenced evidence

`ProceduralCase` statuses are `open` → `admissibility_review` →
(`active` ⇄ `stayed`) → `decided` → `closed`, with
`admissibility_review` → `closed` as the inadmissible path. Closing
requires an explicit `closure_reason_code`; moving to `decided` is refused
unless a decision has been recorded.

`procedural_authority_reference`, `case_handler_reference` and
`assigned_decision_maker_reference` are three distinct references, checked
in `__post_init__` — a case that violates the separation cannot be
constructed at all (see ADR-042 for the independence rules layered on
top). `required_steps` tracks what is outstanding; `evidence_references`
holds opaque pointers only, never content.

A closed case is not modifiable by any ordinary command
(`PROCEDURAL_CASE_CLOSED`); challenging its decision is `file_appeal`,
which opens a _separate_ case linked by an `AppealReference`.

### 5. Data-subject requests carry a verification status, never identity

`DataSubjectRequest` records `identity_verification_status`
(`not_verified` / `verification_pending` / `verified` /
`verification_failed`) plus an opaque
`identity_verification_reference` pointing at whatever service performed
the verification. There is no field, and no command parameter anywhere,
that could carry an attribute, document, eID assertion or KYC payload
(invariant 11). A request cannot be answered while the status is not
`verified` (`IDENTITY_VERIFICATION_INSUFFICIENT`). Search results and
completion evidence are references. Refusals and partial grants must carry
a `limitation_reason_code`.

### 6. Scope: Option E — flat isolation plus explicit presented grants

`RequestContext` carries the caller's own `organization_id` (or `None`,
which is `ORGANIZATION_SCOPE_UNDETERMINED` — fail closed, never
defaulted) and a set of `authority_reference_ids` the caller is
_presenting_ for this operation.

Option D was rejected outright. A Bund-level organization gets **nothing**
automatically over a Landesverband's cases, and a Kreisverband nothing
over its parent Land's. Crossing a boundary requires a
`CrossScopeAuthorityGrant` issued _by the organization being reached
into_, carrying the specific `ScopeCapability` the operation needs
(`read_case`, `manage_case`, `manage_deadline`,
`read_processing_registry`, `authorize_destruction` — no wildcard, no
"all"), still valid at `now`, **and** explicitly presented by the caller.
A standing broad grant that the caller does not present is never used, so
it cannot be exercised by accident.

Cases may never be opened into another organization at all, even with a
grant: creating obligations inside a scope one does not own is not a
capability this pack confers.

**Non-disclosure.** A read, or a write by a caller presenting no
authority, that targets another organization's resource raises the same
`ComplianceRecordNotFoundError` / `VALIDATION_RECORD_NOT_FOUND` as a
resource that does not exist — identical class, identical message shape.
The specific `CROSS_ORGANIZATION_CASE_ACCESS_DENIED` /
`CROSS_SCOPE_AUTHORITY_INVALID` codes are reachable only by a caller who
already asserted it holds authority there, so they disclose existence only
to someone who already claimed the right to know.

## Consequences

Easier: a deadline's whole life is one readable list; a timeliness dispute
is answerable from the entity itself; scope reasoning is two helpers, not
a hierarchy walk.

Harder: deadline mutation is more verbose, and a legitimate cross-scope
operation needs a grant to exist _and_ be passed in — two steps where an
inheritance model would need none. That friction is the point: it makes
cross-organization access an explicit, auditable act.

Also harder: because reads report foreign resources as absent, a
legitimate operator who mistypes an organization sees "not found" rather
than "wrong scope". Accepted deliberately — the alternative leaks
existence to anyone with an id.

## Security impact

The scope model is the pack's second primary control after ADR-038's
dependency rule. The two-tier error strategy (non-disclosing not-found for
unauthenticated-to-scope callers, specific codes for authority-claiming
callers) resolves the standing tension between PACK-09 required invariant
14 (deterministic reason codes for denials) and the requirement that a
foreign id disclose nothing.

Append-only deadline history is an integrity control: it removes the
ability to retroactively make a missed deadline look met.

## Data impact

New schemas: `procedural-case`, `case-decision`, `deadline-definition`,
`procedural-deadline`, `data-subject-request`,
`cross-scope-authority-grant`. New events:
`procedural_case.status_changed`,
`procedural_deadline.state_changed`,
`data_subject_request.status_changed`. `procedural-deadline.schema.json`
documents `status` and `due_at` as required _output_ fields alongside the
full `history` array, matching what the read model returns.

`case_version` and `request_version` are optimistic-concurrency fields;
the corresponding commands accept an optional expected version and refuse
on mismatch.

## Migration impact

None. No pre-existing case or deadline data exists.

## Reversibility

The derived-`status`/`due_at` design is effectively irreversible without
losing invariant 6. The scope model is extendable — new capabilities are
additive — but moving to hierarchical inheritance would be a security
regression requiring its own ADR and a threat-model review.

## Related canon version

Canon `0.7.0`, no bump. `ProceduralCase`, `ProceduralDeadline` and
`DataSubjectRequest` are compliance-side workflow state owned by one
service; the three new events use canon section 21's envelope unchanged.


## Amendment (Architecture & Domain Framework 0.8.1, same 0.9.0 round)

Framework section 13.1 requires a **common legal-case substrate** that
every governed proceeding shares, and section 13.2 requires deadlines to
carry their legal basis and trigger source. This ADR's `ProceduralCase`
and `ProceduralDeadline` are unchanged and keep their callers; the
substrate is added alongside them in `casework.py`.

Four properties of that substrate are worth recording as decisions:

**Status is derived everywhere.** `LegalCase.status`, `Hearing.status` and
`ProceduralDecision`'s three statuses are all computed from append-only
histories, extending this ADR's own decision for `ProceduralDeadline` to
every new aggregate. A status the history does not support is not
expressible, so no store, cache or read model can publish one.

**Jurisdiction gates substantive capability.** A case cannot enter
`substantive_review`, `hearing` or `decided` without a bound
`JurisdictionDetermination`, and the refusal lives in
`LegalCase.transition` rather than in a command — a guard that only exists
in a command can be bypassed by the next command somebody writes.
`SUBSTANTIVE_CASE_STATUSES` is public precisely so the application layer
gates on the same set rather than keeping a second copy.

**Effect, finality and enforceability are three separate facts.** A
decision may be in effect while still appealable, and final while not
enforceable. `ProceduralDecision` refuses to become enforceable unless it
is in effect, and suspending effect also stays enforceability — a
suspended decision that stayed enforceable is exactly the failure
Framework hard invariant 52 exists to prevent, so the coupling lives in
the aggregate.

**The docket is immutable.** `Filing.docket_sequence` is assigned by the
store, is strictly increasing per case and is never reused. A rejected
filing keeps its position with its reason code — "this was filed and
refused" is itself part of the record — and correction is supersession,
not mutation. `submitted_at` and `received_at` are separate fields so a
deadline running from receipt cannot silently use the submitter's clock.

**What starts a deadline** is decided separately, in **ADR-043**, because
it turned out to be a genuine architectural fork with two viable
alternatives rather than a consequence of this ADR's representation
choice.
