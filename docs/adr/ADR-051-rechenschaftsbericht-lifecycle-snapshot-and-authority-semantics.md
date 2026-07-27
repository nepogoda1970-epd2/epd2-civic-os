# ADR-051: Rechenschaftsbericht lifecycle, source snapshot and authority semantics

## Status

`proposed`

## Date

2026-07-27

## Context

PACK-10 specifies the Rechenschaftsbericht (statutory accountability
report) as a governed lifecycle, not a document with a status flag:
reporting obligation, reporting period, reporting perimeter,
organizational consolidation, preparation, source-data freeze,
validation, finance-auditor review, correction, management/board
approval, legally responsible sign-off, submission, receipt or
acknowledgement, publication, amendment and restatement, with prior
versions preserved (PACK-10-SPECIFICATION.md section 4.9).

ADR-043 already fixed the precedent this ADR extends: `OfficialNotice`,
`ServiceAttempt` and `NoticeEffectDecision` are three separate objects
because a channel's telemetry must never be able to write legal effect.
PACK-10's report lifecycle faces the identical shape of risk one layer
up — a filing's `submitted` status, a portal's delivery receipt and a
regulator's `accepted_by_authority` determination are three different
claims made by three different parties, and collapsing them into one
status field would let upload or telemetry manufacture legal
acceptance.

The lifecycle also has to survive an organizational fact PACK-08
already governs: perimeters change. A Land association can merge,
split or reorganize after a period closes. If the reporting perimeter
were derived from the organizational hierarchy at read time rather
than frozen at report time, a later reorganization would silently
rewrite what an already-submitted report was a report _of_.

Hard invariants #25–#29, #34, #39 and #54 (PACK-10-SPECIFICATION.md
section 6) and the aggregate shape in section 8.2.15–8.2.18 already
fix the constraints; this ADR is the record of why that shape was
chosen over the alternatives and what it does and does not assert.

## Problem

Four sub-questions, decided together because they interact:

- Is a report version one object with a status field, or several
  objects with asymmetric capabilities, mirroring ADR-043's choice at
  the notice layer?
- What must exist before a version can be prepared, validated or
  submitted, and what happens to that precondition once later versions
  exist?
- What evidence is sufficient to move a version from `submitted` to
  `accepted_by_authority`, and who decides sufficiency?
- How is a restatement represented without creating two competing
  version chains for the same obligation?

## Considered options

- **Option A — one `FinanceReportVersion` with a status field and a
  `source_data` reference that is re-resolved on read.** Simplest
  storage shape. The perimeter and ledger state a report reflects would
  be computed at read time from current data, so a later posting or
  reorganization could change what an already-submitted report
  "means" without touching its stored fields.
- **Option B — a status field plus a derived `acceptance_status`**
  computed from telemetry, acknowledgement and a configurable
  deemed-acceptance rule. Structurally identical to ADR-043's rejected
  Option B: it makes legal acceptance a function of signals nobody with
  legal standing produced.
- **Option C — snapshot-first aggregate with disjoint create-once and
  append-only children, and acceptance reachable only from an external
  authoritative reference.** `ReportSnapshot` is its own create-once
  aggregate; `FinanceReportVersion` is an append-only child of
  `FinanceReport`; `SubmissionRecord`, `ConsolidationRecord` and
  `PublicationRecord` are create-once children of a version;
  `ValidationFinding`s are append-only; a restatement is a new version
  carrying `restatement_of_version_reference`, not a second entity
  type.

## Decision

**Option C.**

### Lifecycle states and transitions

Ten states, each separately authorized, per report version:

| State                     | Meaning                                              |
| ------------------------- | ---------------------------------------------------- |
| `draft`                   | prepared from a frozen snapshot; not reviewed        |
| `internally_reviewed`     | internal review recorded                             |
| `auditor_reviewed`        | independent audit review recorded                    |
| `approved`                | management/board approval recorded                   |
| `signed`                  | legally responsible sign-off recorded                |
| `submitted`               | a `SubmissionRecord` was created                     |
| `externally_acknowledged` | an `ExternalAcknowledgement` was recorded (optional) |
| `accepted_by_authority`   | a `NoticeEffectRef` recorded acceptance (optional)   |
| `published`               | a `PublicationRecord` was created (optional)         |
| `amended_or_restated`     | superseded by a new version (terminal for this one)  |

Allowed and forbidden transitions:

| From                      | To                        | Allowed | Requires                                                                                           |
| ------------------------- | ------------------------- | ------- | -------------------------------------------------------------------------------------------------- |
| (none)                    | `draft`                   | yes     | frozen `ReportSnapshot`                                                                            |
| `draft`                   | `internally_reviewed`     | yes     | internal review authority                                                                          |
| `internally_reviewed`     | `auditor_reviewed`        | yes     | concluded `AuditEngagement`, same scope/period                                                     |
| `auditor_reviewed`        | `approved`                | yes     | management/board authority                                                                         |
| `approved`                | `signed`                  | yes     | legally responsible signatory                                                                      |
| `signed`                  | `submitted`               | yes     | `SubmissionRecord` created                                                                         |
| `submitted`               | `externally_acknowledged` | yes     | `ExternalAcknowledgement` recorded                                                                 |
| `submitted`               | `accepted_by_authority`   | yes     | `NoticeEffectRef` only                                                                             |
| `externally_acknowledged` | `accepted_by_authority`   | yes     | `NoticeEffectRef` only                                                                             |
| `approved`                | `published`               | yes     | approval **and** publication authorization                                                         |
| any post-submission state | `amended_or_restated`     | yes     | new version with `restatement_of_version_reference`                                                |
| `draft`                   | `submitted`               | no      | skips required intermediate states                                                                 |
| `submitted`               | `accepted_by_authority`   | no*     | telemetry/acknowledgement/read status alone (`FINANCE_EXTERNAL_ACKNOWLEDGEMENT_NOT_AUTHORITATIVE`) |
| `draft`                   | `published`               | no      | a draft is never publishable                                                                       |
| `signed`                  | `published`               | no      | publication requires `approved`, not merely `signed`                                               |
| (any submitted/published) | (edited in place)         | no      | `FINANCE_IMMUTABLE_RECORD_MODIFICATION_ATTEMPTED`                                                  |
| `internally_reviewed`     | `signed`                  | no      | skips `auditor_reviewed` and `approved`                                                            |

\* The `submitted → accepted_by_authority` row above the forbidden
table is the _only_ legitimate path, gated on a `NoticeEffectRef`; this
row records the same edge failing when that reference is absent.

### Aggregate shape

`FinanceReport` is the root: one per (scope, `ReportingObligation`),
holding an append-only chain of `FinanceReportVersion` children,
numbered monotonically. Each version has create-once
`ConsolidationRecord`, `SubmissionRecord` (with its own create-once
`ExternalAcknowledgement`) and `PublicationRecord` children, plus
append-only `ValidationFinding`s. `ReportSnapshot` is deliberately its
own create-once aggregate, not a version-owned value object, so a
snapshot survives independently of every version that ever referenced
it — including one later amended or restated.

A restatement is a version carrying
`restatement_of_version_reference`, not a separate `Restatement`
entity. A second entity type would create two competing chains for the
same obligation — a version chain and a restatement chain — with no
single ordering and no single answer to "what is the current version
of this report". One append-only chain, distinguished by a reference
field, keeps the ordering total and the history singular.

### Snapshot first

A version can only be prepared from a frozen `ReportSnapshot` that
binds the period locks, the policy versions and the ledger state it
was computed from, identified by a content digest. No snapshot means
no preparation, no validation, no submission
(`FINANCE_REPORT_SNAPSHOT_MISSING`). `frozen` is `ReportSnapshot`'s
only state, and it is terminal: no write path exists back into a
frozen snapshot, and a snapshot a version references can never be
replaced, only superseded by a new snapshot feeding a new version.

### Submission is not acceptance

`submitted → accepted_by_authority` is reachable **only** from an
explicit authoritative reference: a PACK-09 `NoticeEffectRef` produced
by a governed `NoticeEffectDecision` (ADR-043), or an equivalent
recorded governed decision. Upload, delivery telemetry, read status,
an acknowledgement, a receipt or publication never produce it
(`FINANCE_EXTERNAL_ACKNOWLEDGEMENT_NOT_AUTHORITATIVE`). Structurally,
no telemetry field is an input to any transition; telemetry is
recorded on its own create-once record
(`ExternalAcknowledgement`), read but never consulted by the state
machine. This is ADR-043's boundary, restated at the report layer
rather than reinvented: the same three-way split — object exists,
attempt was made, authority decided — applies here with
`FinanceReportVersion` standing in for `OfficialNotice`,
`ExternalAcknowledgement` for `ServiceAttempt`, and `NoticeEffectRef`
for `NoticeEffectDecision`.

### Publication is not approval

Publishing requires an existing approval **and** a separate
publication authorization (`PUBLICATION_NOT_ALLOWED` if either is
missing); publishing does not set approval, and approving does not
publish. Only the published version is publishable, and it is always
labelled with its version, its snapshot reference, its perimeter and
its status. A draft is never publishable, regardless of how far its
internal review has progressed.

### Four actions, four authorities

Prepare, approve (management/board), sign off (legally responsible
signatory) and independent audit review (`finance_auditor`) are four
distinguishable actions, each a separate command, each recording a
separate authority reference, each producing a separate event.
Auditor review additionally requires a concluded `AuditEngagement` for
the same scope and period (`FINANCE_AUDIT_INCOMPLETE`); auditor
independence is re-verified at the moment of review, not only at
engagement opening, because an incompatibility (for example, the
auditor becoming finance administrator in the same scope) can arise
between engagement opening and review.

| Action       | Authority                           | Record produced           |
| ------------ | ----------------------------------- | ------------------------- |
| prepare      | `finance_administrator`             | `draft` version           |
| audit review | `finance_auditor`, engagement-bound | `auditor_reviewed` marker |
| approve      | management/board authority          | `approved` marker         |
| sign off     | legally responsible signatory       | `signed` marker           |
| submit       | submission authority                | `SubmissionRecord`        |
| publish      | publication authority (separate)    | `PublicationRecord`       |

Whether the preparer may also be the signatory is an **open legal
question** (OD-9). The recommended conservative default, recorded here
and not resolved by this ADR: preparer ≠ auditor is mandatory
(PACK-08 section 9.3 rule 3, HI-31, structural), and preparer =
signatory is permitted only where the applicable law and the
organization's own statutes affirmatively allow it. Absent that
affirmative permission, the system's default posture must be to
require the preparer and signatory to be different authorities.

### Corrections

`finance_report.correction_requested` records a request carrying an
authority reference, a reason code and a PACK-09 `DeadlineRef`.
Amendment or restatement creates a **new** version; every submitted or
published version stays intact
(`FINANCE_IMMUTABLE_RECORD_MODIFICATION_ATTEMPTED`). Reopening the
underlying accounting period for a period that has already been
submitted additionally requires this explicit correction/restatement
decision — reopening the period alone (ADR-049) does not by itself
authorize touching a report version that already exists for it; the
two decisions are cross-referenced, not merged, because a period
reopening and a report correction can have different authorities and
different reason codes.

### Perimeter and consolidation

The reporting perimeter is an effective-dated
`ReportingPerimeterDefinition`, resolved **as of the reporting
period**, and frozen into the version as a `PerimeterSnapshot`. A
later reorganization can never rewrite it
(`FINANCE_REPORTING_PERIMETER_UNDETERMINED`, reused
`HISTORICAL_SCOPE_NOT_EFFECTIVE`). Consolidation is a descendant-mode
read (PACK-08 ADR-034) performed under an explicit consolidation
authority that writes exactly one thing, in its own scope: the
`ConsolidationRecord`, naming which perimeters were consolidated and
which internal transfers were eliminated. Consolidation never writes
into a lower scope (`FINANCE_CROSS_SCOPE_CONSOLIDATION_DENIED`).

### What the lifecycle does not assert

Reaching `signed` means a recorded signatory performed a recorded act
— not that the report is correct, complete or sufficient. Reaching
`accepted_by_authority` means an authoritative reference was recorded
— the legal effect of that acceptance is determined outside this
system, by the authority that produced the `NoticeEffectDecision`. No
`is_compliant` or `is_production_ready` field exists anywhere on
`FinanceReport`, `FinanceReportVersion` or any of their children
(HI-46).

Option A was rejected because a re-resolved `source_data` reference
lets both the ledger and the organizational hierarchy move underneath
an already-prepared report, which is exactly the class of defect
HI-25 and HI-54 exist to prevent — a report that silently means
something different tomorrow than it meant when it was signed. Option
B was rejected for the reason ADR-043 already gives for its own
Option B: a derived `acceptance_status` makes legal acceptance a
function of signals, and the next relaxation of the derivation rule
would look like a configuration change rather than an override of a
governance decision.

## Consequences

Easier: the boundary between "something happened" and "it was legally
accepted" is auditable by reading one state machine and one guard
(`submitted → accepted_by_authority` requires a `NoticeEffectRef`),
exactly as ADR-043 made the notice boundary auditable by reading one
module. A `ReportSnapshot` that outlives every version referencing it
means a restated report's snapshot provenance is never in question,
even years later.

Harder: five child aggregate types instead of one status field, and a
consolidation, submission or publication step that a deployment must
actually wire up — an environment that never records a
`NoticeEffectRef` will find that no version ever reaches
`accepted_by_authority`, which is the intended fail-closed direction
but is a real operational obligation. The preparer/signatory question
(OD-9) stays open by design; implementations must apply the
conservative default until a legal determination resolves it, which
means some organizations will need a `report_signatory` distinct from
every preparer even where local law might eventually permit overlap.

## Security impact

Positive and specific, mirroring ADR-043's stated failure: an actor
who controls or spoofs a delivery channel, a portal receipt, or a
regulator's read status can at most produce an
`ExternalAcknowledgement` that does not drive any transition. Under
this ADR, that actor cannot move a version past `submitted` without an
independently governed `NoticeEffectDecision`, which means an
availability-shaped or telemetry-shaped attack on legal acceptance
gets no purchase. The auditor-independence re-check at review time
closes a narrower but real window: an auditor whose independence was
valid at engagement opening but has since lapsed (for example, through
a new appointment as finance administrator in the same scope) is
refused at the point that matters, not only at the point that was
convenient to check.

No new identity surface: authority references resolve through PACK-08
`OrganizationalAuthority`/`RoleAssignment` records, never role-code
string comparison (HI-53); no report, version or child record carries
a `FinancePartyHandle` beyond what section 8 already specifies for
contributions.

## Data impact

Adds the `FinanceReport` aggregate root and its children
(`FinanceReportVersion`, `ConsolidationRecord`, `SubmissionRecord`,
`ExternalAcknowledgement`, `PublicationRecord`, `ValidationFinding`),
plus the `ReportSnapshot` and `ReportingPerimeterDefinition`
aggregates, all owned by `reporting.py` (PACK-10-SPECIFICATION.md
section 8.2.15–8.2.18). No existing PACK-08 or PACK-09 entity changes
shape. `FinanceReportVersion` references `ReportSnapshot` and
`PerimeterSnapshot` by identifier plus digest, never by embedding
mutable state.

## Migration impact

None for this round: no stored shape changes and no deployed data
exists. If a later round changes the ten-state enumeration, existing
`FinanceReportVersion` records keep their recorded state unchanged;
only new versions would observe an extended set.

## Reversibility

The state set can be extended additively — a future state inserted
between two existing ones, or a new terminal state, does not require
rewriting history, because history is append-only per version and
each transition is its own recorded event.

Collapsing `submitted` and `accepted_by_authority` back into one state
would be a hard regression of ADR-043's trust boundary at the report
layer and must be treated as **effectively irreversible**: once
consumers rely on `accepted_by_authority` meaning "an authoritative
reference was recorded", merging it with `submitted` would silently
convert every prior submission into a legally accepted one, which no
migration can undo without re-litigating each report's actual
acceptance status against external authorities.

## Related canon version

Authored against canon `0.7.0`. PACK-10 as a whole requires a canon
amendment (`CANON_VERSION` `0.7.0 → 0.8.0`, proposed — see
`docs/packs/PACK-10-CANON-AMENDMENT-PROPOSAL.md`), but this ADR does
not itself edit `docs/canonical/TZ-00-domain-event-canon.md` or any
other canon-owned file. `CANON_VERSION` stays `0.7.0` until that
separate, dedicated amendment round lands.
