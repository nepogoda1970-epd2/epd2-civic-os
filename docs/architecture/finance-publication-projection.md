# Finance publication and projection

Status: implemented for CLAUDE-PACK-10. This document describes
`services/finance-service/src/epd2_finance_service/projections.py` and
the group rule in `events.PUBLIC_PROJECTION_ALLOWED`: the six projection
groups canon 20.17 defines, why every projection is derived, versioned
and never authoritative, which report state may reach the public,
statistical disclosure control and what it does not catch, and the
identity-key rejection every payload passes.

Nothing in this module is a source of truth, nothing here is written
back into an aggregate, and no aggregate reads a projection. Canon
`ФИН-34` is the whole premise: public finance representations are
derived, versioned and never authoritative.

## 1. The six groups, and what each admits

Canon 20.17's own subsection on public projection splits the
seventy-two finance events into six groups and gives each a different
rule. `events.py` implements the group rule at event level;
`projections.py` implements it at object level.

| Group | Canon sections | What may be publicly projected                                                                                         |
| ----- | -------------- | ---------------------------------------------------------------------------------------------------------------------- |
| 1     | 19f.4–19f.6    | No individual event at all; only aggregated derived figures inside a published report version                          |
| 2     | 19f.7–19f.9    | Only to the extent an effective disclosure obligation prescribes                                                       |
| 3     | 19f.10–19f.12  | Only the aggregated level of an approved budget version and a published report version; no individual claim or payment |
| 4     | 19f.16–19f.17  | Only a version in state `published`; not `snapshot_frozen`, `validation_finding_recorded` or `correction_requested`    |
| 5     | 19f.18, 19f.20 | Only the fact of an audit, the `AuditConclusion` class, and the identifier and version of the policy in force          |
| 6     | 19f.15         | Never, in any extent and in no derived form                                                                            |

`events.PUBLIC_PROJECTION_ALLOWED` is assembled from six named group
constants so each group's reasoning sits next to its members. Group 1
and group 6 contribute the empty set. Group 3 contributes only
`budget.approved` and `budget.amended`, because those two events are the
approved budget version, while individual asset and obligation events
reach the public only as aggregated figures inside a published report —
which is that report's projection, not theirs. Group 4 contributes only
`finance_report.published`. Group 5 contributes
`finance_audit.opened`, `finance_audit.concluded`,
`finance_policy.version_published` and `finance_policy.superseded`; the
superseding event is admitted alongside the publication event because
the projectable fact is which policy version is in force, and a
projection that only ever learns of publications would report a
superseded version as current forever. `finance_audit.finding_recorded`
is not admitted: finding content is projected nowhere.

Membership in that set is necessary and never sufficient — canon 19f.21
adds that a permitted projection exists only as a derived, versioned,
non-authoritative representation under a disclosure policy and the
statistical disclosure rules. Absence, by contrast, is final.

The seven projection classes map onto the groups as follows.
`AccountBalanceProjection` and `PeriodSummaryProjection` are group 1 and
carry `INTERNAL_PROJECTION_VERSION`; building one is not a publication
decision, and a public consumer never sees either object.
`ContributionDisclosureProjection` and `SponsorshipDisclosureProjection`
are group 2. `BudgetSummaryProjection` is group 3.
`PublishedReportProjection` is group 4. `AuditConclusionProjection` is
group 5. Group 6 has no class, and that is the enforcement.

## 2. Derived, versioned, and never authoritative

`FinanceProjection` is the shared base and carries the provenance canon
19f.21 makes mandatory: the projection version, the generation instant,
the scope, the source aggregate's own lifecycle state, a correction
status, and optional references to the source snapshot and the source
report version. The fields are keyword-only, because a base class with
six provenance fields and subclasses with their own would otherwise
force every subclass field to carry a default just to satisfy positional
ordering — and a default is exactly what a provenance field must not
have.

Two version strings exist. `PUBLIC_PROJECTION_VERSION` is
`finance_public/v1` and `INTERNAL_PROJECTION_VERSION` is
`finance_internal/v1`. Keeping them separate means a change forced by an
internal need cannot silently renumber the public contract.

`SourceCorrectionStatus` makes correction and displacement visible
rather than silent, which canon 19f.21 requires.
`correction_status_for_report_state` honours an explicitly supplied
`superseded_by_version_reference` even when the version's own state has
not been re-read, because a projection that knows a successor exists and
reports `current` anyway is the precise failure the canon forbids.

One canon term has no member in that enum, and the code names the gap.
Canon 19f.21 lists withdrawal alongside correction and supersession, but
`ReportState` models no withdrawal — canon 19f.17 fixes twelve states
and none of them is "withdrawn". A `WITHDRAWN` member would be a status
no aggregate could ever produce, an enum member that is only ever a lie.
Until a withdrawal state exists in the report lifecycle, a withdrawn
publication surfaces as `SUPERSEDED`, which understates it.

### `is_authoritative` is a property, not a field

`FinanceProjection.is_authoritative` returns `False` and is a read-only
property. The choice is load-bearing. A field can be set — by a
constructor argument, by `dataclasses.replace`, by a deserialiser
reading an attacker-supplied JSON object, or simply by a future builder
that passes `True` by accident — and the projection would then claim an
authority it does not have. A property has no such path: there is
nothing to assign, `frozen=True` refuses assignment to the name anyway,
and `slots=True` means no instance dictionary can shadow it. The value
is hard-coded rather than derived, because there is no input under which
it would be true: a derived representation never becomes the accounting
source of truth, however authoritative its source was. It appears in
every `to_payload()` through `_provenance_payload`, so a consumer reads
the disclaimer rather than having to know it.

## 3. Only a `published` report version projects

`PublishedReportProjection.from_report_version` refuses every state
except `published`, `externally_accepted` included. An authority's
acceptance decision is not a publication decision, and publication needs
its own authorisation (`ФИН-28`, `ФИН-34`). It makes two further
refusals that cannot occur through `FinanceReportVersion.publish` but
are checked because a version reconstructed from storage could arrive
that way: a published version carrying no publication record, and a
published version naming no snapshot.

The projection carries the snapshot id as provenance and nothing of the
`snapshot_frozen` event. Those are different objects. Canon 19f.21
requires every representation to carry a reference to its
`ReportSnapshot`; canon 20.17 group 4 forbids projecting the freezing
act, which would publish the included transaction and entry identifier
sets. A pointer that lets a reader ask which frozen source set produced
a figure is not the same as publishing the source set.

It carries no figures at all. The aggregated totals a published report
contains are the report's own content — prepared, reviewed, approved,
signed and audited as such — and re-deriving them in a read model would
create a second set that can disagree with the published one.

The other builders apply the same shape of rule to their own groups.
`ContributionDisclosureProjection` refuses any contribution that is not
`accepted`; the quarantined case is worth stating, since a quarantined
contribution is the recorded admission that its source or verification
is still open (`ФИН-16`), and publishing it would present an unresolved
question as a disclosed fact. `SponsorshipDisclosureProjection` accepts
only a `disclosure_classified` or `terminated` agreement — approval says
the agreement is permitted, and only classification says anything about
publishing it; a terminated agreement stays projectable because ending
an agreement does not retract the obligation to have disclosed it.
`AuditConclusionProjection` refuses an open or in-progress engagement,
because such an engagement has no conclusion class and projecting the
bare fact would publish a mid-audit state as a finished one to a reader
who did not check the lifecycle field. `BudgetSummaryProjection`
hard-codes `source_lifecycle_state` to `"approved"` rather than
accepting it as a parameter, so a draft budget cannot be projected by
passing the wrong string.

Both group-2 builders require a disclosure-obligation reference and
refuse without one, with `PUBLICATION_NOT_ALLOWED` rather than a
validation code: nothing is malformed, the act itself is not permitted.
This module does not decide what must be published — that is a legal
question — and it refuses to proceed until the caller names the
obligation that answers it.

Group 6 is absolute. The contributor and sponsor handle references live
on the group-2 projection objects, because that is what lets an internal
caller group contributions by party for the legally required
aggregation, and `to_payload()` omits them entirely, emitting only a
`contributor_is_recorded` or `sponsor_is_recorded` boolean. A projection
that carried the handle onto the wire would satisfy "opaque" and violate
"never". `references.FinancePartyHandleReference` deliberately has no
`to_payload()` override adding the purpose, on the grounds that the
inherited payload is already more than a public surface may see.
`_require_opaque_party_reference` additionally refuses any party value
that is not an `fph:` handle reference, so a resolved identity cannot
enter the object in the first place.

The exact receipt instant is also absent from the group-2 projections,
which carry the reporting period label instead. A timestamp is a far
stronger identifier than any disclosure obligation asks for, and the
aggregation those obligations prescribe happens at period level anyway.

## 4. Statistical disclosure control

`assert_no_small_cell_disclosure(cell_counts, context=..., minimum_cell_size=...)`
raises `FINANCE_STATISTICAL_DISCLOSURE_RISK` when any non-zero cell is
below the applicable minimum. It is an assertion a builder calls before
emission, not a review a publisher performs afterwards (`ФИН-35`). An
empty cell passes, because zero says "nobody" and discloses nobody; a
cell of one is the whole problem, since an aggregate of one person is
that person. A negative count fails too — that is a bug rather than a
disclosure, but a mapping the function cannot interpret is not one it
may pass (`ФИН-41`).

`MINIMUM_CELL_SIZE` is 5, and it is a floor rather than a legal
threshold. This module does not get to set the real one. The applicable
minimum is a `FinancePolicy(statistical_disclosure)` value bound to the
representation and effective-dated under canon 19f.21; it depends on the
jurisdiction, the obligation and the population, and no constant in a
pure module can know it. Five is the conventional starting point in
official statistics and is used here for exactly one purpose: so that a
caller with no policy value still cannot emit a cell of one or two by
omission. A policy value above five is honoured; a policy value below
five is refused, because a code-level floor any caller can lower is not
a floor. No `FinancePolicy` aggregate exists this round, so in practice
the only value in force is the constant.

### The residual risks this does not catch

The function sees one mapping at one moment, so it cannot see
differencing. Stated concretely: publish a report version with a cell of
7, publish a corrected version whose same cell is 6, and the difference
identifies one contributor exactly — and both releases passed this check
individually. The same holds across overlapping cells inside a single
release, where a total and its parts differ by one; across a public
projection and a separately published aggregate over the same
population; and across a finance figure and any other public dataset
about the same people.

Defending against differencing needs state this module deliberately does
not hold — the history of what has already been released, and a policy
about what may be released next. Until a suppression policy owns that
history, this function is a floor on the most obvious failure and
nothing more, and calling it does not mean a release is safe.

There is a second, narrower residual risk in group 3.
`_assert_aggregate_categories` refuses a budget category label that
parses as a UUID, because a category keyed by record identifier is
per-record projection wearing an aggregate's clothes — the individual
`expense_claim.*` and `payment.*` projection canon 20.17 group 3
forbids, arriving through the one field shaped to hold many values. It
catches that obvious form and not a caller who labels a single claim
`"office costs"`. Nothing in a pure module can distinguish a genuine
category of one from a disguised record, which is what the small-cell
assertion is for and why neither check is sufficient alone.

## 5. The identity-key rejection over every payload

Every builder calls `_assert_emittable` before returning, and
`_assert_emittable` runs `domain.reject_identity_payload_keys` over the
projection's own `to_payload()` output. A projection that would leak an
identity key therefore never comes into existence — not even to be
discarded later by a caller who might forget. The check runs on the
payload rather than on a declared field list, so it covers fields that
did not exist when the builder was written: the point is not that
today's fields are safe, but that a careless future field cannot ship
(`ФИН-02`). It walks nested structures, so a prohibited key one level
down fails the same way as one at the top.

Spec 9.7 makes this module the single surface anything leaves the
context through, so PACK-12 can attach export and data-loss controls at
one place rather than auditing every call site.
`test_every_projection_payload_passes_the_identity_key_rejection`
exercises the property across the builders, and
`test_every_audit_state_payload_passes_the_identity_key_rejection` does
the same for the hashed state payloads in `events.py`.

Two consequences are worth naming. `FinanceAccount.account_id`
serialises as `finance_account_id` in both `projections.py` and
`events.py`, because `account_id` is in `PROHIBITED_IDENTITY_KEYS` —
in every other context in this repository it means a user account, and a
projection that emitted it would fail its own emission check. The rename
is not cosmetic; it is what lets the check stay blunt.

And the check is a key-shape check and nothing more. A projection that
put a contributor's name in a field called `benefit_description` passes
it. The defence against that is not this function: it is that no builder
in the module accepts free text from outside the aggregate it derives
from, and that `AuditConclusionProjection` in particular carries neither
`AuditFinding.summary_reference`, nor `AuditConclusion.reason`, nor its
evidence references, nor a finding count, nor the auditor's own
authority. Those last two are omissions rather than oversights: a count
is neither the fact of an audit nor the conclusion class, and in a small
perimeter "three findings" is disclosive about a handful of people;
naming the auditor may well be required by some obligation, but that is
a separate disclosure decision with its own authority, and canon 20.17
group 5 does not grant it here.
