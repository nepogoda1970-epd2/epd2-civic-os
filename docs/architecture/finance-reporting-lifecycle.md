# Finance reporting lifecycle

Status: implemented for CLAUDE-PACK-10. This document describes the
`Rechenschaftsbericht` lifecycle in
`services/finance-service/src/epd2_finance_service/reporting.py`: the
twelve canonical states, the operational vocabulary that maps onto them,
the transition graph and its three documented additions, the guarded
publication path, the three refusals that keep submission separate from
acknowledgement and acknowledgement separate from acceptance, the
snapshot binding, and the amendment and restatement routes. The
lifecycle decision is
`docs/adr/ADR-051-rechenschaftsbericht-lifecycle-snapshot-and-authority-semantics.md`.

## 1. The twelve states

Canon 19f.17 fixes twelve statuses. `reporting.ReportState` spells them
with the canon's own names, verbatim and in the canon's order:

```text
draft                    internally_reviewed
auditor_reviewed         approved
signed                   submitted
externally_acknowledged  externally_accepted
published                amended
restated                 superseded
```

There is no thirteenth. In particular there is no `correction_required`
and no `withdrawn`: neither is in the canon's list, and inventing one
would let a version sit in a status the canon does not define. What a
correction request actually produces is a `CorrectionRequest` appended
to the version, which changes the record and not the status.

## 2. The operational synonym map

The governing implementation brief's section 10 used a longer,
operational vocabulary, while also instructing that the exact canonical
state names be used where the canon defines them and that where canon
`0.8.0` is more specific the canon controls. Canon 19f.17 defines all
twelve, so the canon's names are authoritative in code and the brief's
vocabulary survives as `reporting.OPERATIONAL_STATE_SYNONYMS` — a
read-only documentation of an intended equivalence. Nothing dispatches
on it.

| Operational term                          | Canonical state       |
| ----------------------------------------- | --------------------- |
| `prepared`                                | `draft`               |
| `under_internal_review`                   | `draft`               |
| `internally_approved`                     | `internally_reviewed` |
| `audit_requested`                         | none                  |
| `audit_opinion_recorded`                  | `auditor_reviewed`    |
| `ready_for_external_submission`           | `signed`              |
| `externally_submitted_reference_recorded` | `submitted`           |
| `accepted_reference_recorded`             | `externally_accepted` |
| `correction_required`                     | none                  |

Three entries deserve their reasons.

`prepared` and `under_internal_review` both map to `draft` because canon
19f.17 has preparation produce the `draft` version from a frozen
snapshot and names no post-preparation status.
`FinanceReportVersion.prepare` is accordingly not a state transition: it
binds the snapshot and appends a `prepared` history entry, and the
version stays in `draft` (or in its correction entry state). Likewise
`record_review` appends a `ReviewRecord` without transitioning, because
a version may carry several review passes — a first with findings open,
a later one complete — and recording each as a transition would either
invent a self-edge or make every review look like progress it may not
represent.

`audit_requested` maps to no state at all. Requesting an audit opens an
`AuditEngagement`, which is a separate aggregate with its own
`opened -> in_progress -> concluded` lifecycle under canon 19f.18. The
report version does not move when an engagement opens; it moves when the
engagement's conclusion is recorded against it.

`correction_required` maps to no state either, for the reason in section
1: a recorded correction request is a `CorrectionRequest` on the
version, and the version leaves its state only when an actual `amended`
or `restated` successor is created.
`test_the_operational_synonym_map_invents_no_thirteenth_state` holds
this.

## 3. The transition graph

`ALLOWED_REPORT_TRANSITIONS` is derived from `_REPORT_PROGRESSION`, the
single ordered path, rather than typed out — so the canon's order is
stated once and the graph cannot drift from it. The result:

```text
draft                   -> internally_reviewed, superseded
internally_reviewed     -> auditor_reviewed, superseded
auditor_reviewed        -> approved, superseded
approved                -> signed, superseded
signed                  -> submitted, superseded
submitted               -> externally_acknowledged, externally_accepted,
                           superseded
externally_acknowledged -> externally_accepted, superseded
externally_accepted     -> published, superseded
published               -> superseded
amended                 -> internally_reviewed, superseded
restated                -> internally_reviewed, superseded
superseded              -> (nothing)
```

Three additions to the bare progression, each with its own reason:

- every state may reach `superseded`. Canon 19f.17: a version displaced
  by a later one becomes `superseded` and stays readable. It is terminal
  in the strict sense — `superseded` reaches nothing — and terminal is
  not the same as destroyed;
- `submitted` may go straight to `externally_accepted`. Canon 19f.17
  says acknowledgement is not implied by submission and acceptance is
  not implied by acknowledgement. If acceptance were reachable only
  through acknowledgement, an acceptance decision that arrived without
  any acknowledgement having been recorded would be unreachable, and the
  system would be forced either to refuse a real legal act or to
  fabricate an acknowledgement to get past a state machine.
  `test_an_acceptance_decision_arriving_without_an_acknowledgement_is_reachable`
  holds this;
- `amended` and `restated` are correction entry states whose only
  forward edge is `internally_reviewed` — they behave exactly like
  `draft`. A corrected version is reviewed, audited, approved and signed
  again, never resuming with decisions that were given for different
  figures.

`assert_report_transition_allowed` is a free function so the graph is
testable on its own and every method consults the same table.

## 4. The guarded publication path

`signed -> published` is deliberately absent from the table.
`PUBLICATION_GUARDED_SOURCE_STATE` names `signed` as the one state from
which `FinanceReportVersion.publish` may take a path the table does not
contain.

Canon 19f.17 permits a version to be published once it carries the
legally responsible signature and a separate publication authorisation
has been issued — the case of a report whose legal route does not run
through an external acceptance decision at all. A free table edge would
have made publication look like an ordinary next step and would have
dropped the authorisation requirement for anyone consulting the table
alone. `approved` is deliberately not the guarded source: an
approved-but-unsigned version has nobody legally answerable for it.

`publish` requires three independent facts and refuses on each with
`PUBLICATION_NOT_ALLOWED`:

- a `PublicationAuthorization` presented, scoped to this version's
  scope. Publication is not approval and approval is not publication
  (`ФИН-28`, `ФИН-34`);
- a recorded `ApprovalRecord` on the version;
- a `PublicationReference` naming that exact authorisation, so a
  publication record cannot cite one authorisation while being permitted
  by another.

From `externally_accepted` this is an ordinary tabled transition; from
`signed` it is the guarded path; from every other state it refuses
through the table.

The `PublicationAuthorization` itself has no creating command this
round. It has an aggregate, a create-once store and a required place in
`publish_report_version`, and the caller has to construct it.

## 5. Submission, acknowledgement, acceptance

Three distinct facts, three distinct records, and no implication between
them (`ФИН-26`, `ФИН-27`).

`ExternalSubmissionReference` is create-once and records that a version
was submitted: a submission reference, a recipient reference and a
timestamp. `record_submission` refuses without the legally responsible
`SignatureRecord`, re-asserting the ordering canon 19f.17 fixes even
though the table already enforces `approved -> signed -> submitted`.
Submission implies nothing further — not acknowledgement, not
acceptance, and not fulfilment of the reporting obligation, which is
recorded on the obligation itself.

`ExternalStatusKind` enumerates five kinds. Four of them —
`acknowledgement`, `receipt`, `delivery_telemetry`, `read_status` — are
telemetry: they say something arrived or was opened, and none is a legal
decision. The fifth, `authoritative_acceptance_decision`, is the only
kind `AUTHORITATIVE_ACCEPTANCE_KIND` admits.
`ExternalAcceptanceReference` is constructible for any of the five,
deliberately: telemetry is a real fact deserving a create-once record of
its own, and putting the check on the transition rather than in the
constructor is what lets a delivery record be stored honestly instead of
discarded or quietly promoted.

`record_external_acknowledgement` refuses an authoritative acceptance
decision offered as an acknowledgement, rather than silently downgrading
it. `record_external_acceptance` is the narrowest gate in the module and
raises two different codes:

- no reference at all raises `FINANCE_EXTERNAL_ACCEPTANCE_MISSING`;
- a reference of any telemetry kind raises
  `FINANCE_EXTERNAL_ACKNOWLEDGEMENT_NOT_AUTHORITATIVE`, naming what was
  offered.

The authoritative input is a PACK-09 `NoticeEffectRef` carried opaquely
as `notice_effect_reference`. Finance stores no verdict of its own about
it: `references.NoticeEffectReference` has no verdict field, because a
verdict stored here would be finance restating a PACK-09 determination
in its own words, and a restated determination is one that can disagree
with the original.

### No elapsed time ever produces acceptance

`assert_no_inferred_acceptance(version, now)` is the answer to the
question this system will be asked — "the authority has not replied in
six weeks, may we treat the report as accepted?" It validates `now` as
timezone-explicit and then never compares it to anything. That is not an
oversight; it is the point. The function raises
`FINANCE_EXTERNAL_ACCEPTANCE_MISSING` when no reference has been
recorded, and `FINANCE_EXTERNAL_ACKNOWLEDGEMENT_NOT_AUTHORITATIVE` when
a stored delivery receipt is read back as acceptance. Silence, elapsed
time, delivery and publication produce nothing.
`test_elapsed_time_never_produces_acceptance` and
`test_assert_no_inferred_acceptance_refuses_a_naive_now` hold both
halves.

## 6. The frozen snapshot binding

A version is bound to exactly one `ReportSnapshot` for its whole life.
`prepare` binds it, `assert_snapshot` refuses any other, and no method
rebinds it. `with_changes` — the only field-edit path — refuses a
different `snapshot_id` outright with
`FINANCE_REPORT_SNAPSHOT_MISMATCH`, and `__post_init__` refuses any
version outside `draft`, `amended` and `restated` that names no snapshot
at all.

The two refusals are distinct facts with distinct codes.
`FINANCE_REPORT_SNAPSHOT_MISSING` means there is no snapshot to work
from — no preparation, no validation, no submission (`ФИН-24`).
`FINANCE_REPORT_SNAPSHOT_MISMATCH` means a different one was presented,
which is an attempt to move a version onto figures it was not computed
from (`ФИН-25`). `prepare` additionally refuses a snapshot frozen for
another reporting period or another scope.

The snapshot is create-once and terminal. `ReportSnapshot.__post_init__`
re-derives `compute_snapshot_content_digest` from its own frozen
contents and refuses construction if the stored digest does not match,
so "recomputation that would change the digest" fails at the door. The
digest sorts identifiers as strings and serialises policy bindings field
by field, so it depends on what was frozen and never on the order the
application layer read it in. `ReportSnapshot.with_changes(**changes)`
exists only to raise: it closes the gap the digest check cannot, since a
caller changing only `snapshot_id` or `frozen_at` would otherwise slip
past `__post_init__`.

The perimeter is frozen alongside. `freeze_perimeter` accepts only an
`active` `ReportingPerimeterDefinition` — a draft has not been decided
and a superseded one has been replaced, so neither can be what a report
claims to cover — and produces a `PerimeterSnapshot` holding scope
references and a digest over the sorted scope ids, never a live pointer
that would be re-resolved at read time. This is the mechanism behind
canon 19f.16's requirement that a later reorganisation never changes the
perimeter of a closed or submitted period.

`ReportingPerimeterDefinition` has no creating command this round. The
aggregate, its `draft -> active -> superseded` lifecycle, its
`amend_draft` edit path and its store with `resolve_active` all exist,
and `freeze_report_snapshot` reads an active definition and freezes it;
creating and activating the definition is left to the caller.

## 7. Amendment, restatement, supersession

Canon 19f.17 gives two correction routes, and `CorrectionKind` names
both: `AMENDMENT` produces a successor in `amended`, `RESTATEMENT` a
successor in `restated`. `CorrectionKind.entry_state` derives the entry
state from the value, so the two cannot drift apart, and
`FinanceReportVersion.__post_init__` refuses a version in a correction
entry state that does not carry both the matching `correction_kind` and
the typed backward `restatement_of_version_reference`.

`create_successor_version` returns both halves of one act — the
predecessor marked `superseded` and the successor — so a caller cannot
record the successor while leaving its predecessor live, which is how
two versions of one report end up both current. The successor starts
with no snapshot, because changed figures need their own; it carries
`version = predecessor.version + 1`; and nothing about the predecessor
is rewritten. A submitted or published version that later turned out
wrong is part of the record of what was reported, and it stays readable
forever (`ФИН-05`, `ФИН-25`).

`_IMMUTABLE_REPORT_STATES` — `submitted`, `externally_acknowledged`,
`externally_accepted`, `published`, `superseded` — is where
`with_changes` and `record_correction_request` refuse. Governed
transitions out of those states still exist, because publishing an
accepted version is a decision and not an edit.

`delete_report_version` exists in the module and always raises
`GOVERNED_RECORD_DELETION_FORBIDDEN`. The honest API for an act the
domain forbids is a refusal with a reason code, not a missing function
that leaves the next reader unsure whether deletion is forbidden or
merely unimplemented.

The two correction events, `finance_report.amended` and
`finance_report.restated`, are emitted by
`create_corrected_report_version` through `_correction_event`: two
events rather than one "corrected", because the two routes are distinct
legal acts and a single event would erase which one happened. The
subject is the successor, and the typed backward link travels in the
payload. `finance_report.superseded` has a builder but no command emits
it — supersession travels as part of the correction event instead.
