# ADR-040: Data Catalog, Processing Registry, and legal basis as a managed field

## Status

`accepted`

## Date

2026-07-26

## Context

An organization that processes personal data has to be able to say, on
demand and per organizational unit, what it processes, for what purpose,
about which categories of people, who receives it, under what recorded
legal basis, with what technical and organizational measures, and for how
long. In practice that inventory is usually maintained as a spreadsheet
that drifts from reality, and its "legal basis" column is free text —
which means it can neither be queried nor reviewed, and quietly becomes a
place where someone writes a sentence that reads like a legal conclusion.

There is also a specific temptation here that this repository has to
resist explicitly. A processing registry is _about_ personal data, and the
easiest way to make one feel complete is to let it hold examples — a
sample record, a contact address, a subject list. Doing that turns the
compliance service into a second identity store, which is exactly what
ADR-002's identity/participation separation forbids.

## Problem

Three questions:

1. What is the minimum inventory PACK-09 must maintain to support
   retention, disposal and data-subject requests, without becoming a
   general-purpose data platform?
2. How should "legal basis" be represented so it is queryable and
   reviewable but makes no legal claim?
3. How is the registry prevented from accumulating identity data?

## Considered options

For question 2 specifically:

- **Option A — free-text `legal_basis: str`.** Maximum flexibility;
  unqueryable; invites prose that reads as legal advice.
- **Option B — closed enum drawn from a fixed vocabulary,** with an
  `other_documented` escape hatch and an explicit disclaimer that the value
  asserts nothing about sufficiency.
- **Option C — structured legal-basis object** with statute references,
  applicability conditions and a validity assessment.

## Decision

### 1. Two entity families, both organization-scoped

`DataAsset` is the Data Catalog entry: one governed store or dataset in
one organization (`name`, `asset_class`, `system_reference`,
`record_class`, `retention_policy_reference`, `status`, `valid_from`,
`owner_authority_reference`). It is the bridge between "a system exists"
and "a retention schedule governs it".

`ProcessingActivity` is the Processing Registry entry, and carries exactly
the fields the required scope names: `purpose`, `legal_basis`,
`data_subject_categories`, `personal_data_categories`,
`recipient_categories`, `controller_reference`,
`process_owner_authority_reference`, `retention_policy_reference`,
`technical_organizational_measures`, `system_references`,
`data_asset_references`, `organization_id`, `status`, `valid_from`,
`activity_version`, and an optional `dpo_review_reference`.

Everything is **categorical**. `data_subject_categories` is
`("members", "applicants")`, never a list of people. No field can hold an
individual, and `__post_init__` requires at least one entry in
`data_subject_categories`, `personal_data_categories`,
`technical_organizational_measures` and `system_references` — an entry
that names no subject category and no measure is
`PROCESSING_REGISTRY_INCOMPLETE`, not silently accepted.

### 2. `legal_basis` is Option B: a managed classification, not an assessment

`LegalBasis` is a closed `StrEnum`: `consent`, `contract`,
`legal_obligation`, `vital_interests`, `public_task`,
`legitimate_interests`, `party_statute`, `other_documented`.

Option A was rejected because a free-text field cannot be queried, cannot
be reviewed for consistency across an organization, and predictably
accumulates prose that looks like a legal determination the system is not
entitled to make. Option C was rejected as out of scope and actively
misleading: a structured "validity assessment" field would imply this
system evaluates legal sufficiency, which it does not and must not.

**What the enum does and does not mean** is recorded on the enum itself,
in the schema description, in the OpenAPI description and in the service
README: choosing a value records _which basis the organization has
documented for this activity_. It asserts nothing about whether that basis
is legally sufficient, correctly chosen, or complete, and recording it does
not make the organization compliant with the GDPR, the BDSG or the
Parteiengesetz. Every legal determination remains a human judgement made
outside this system. `other_documented` exists so an organization is never
forced to mis-classify in order to record something.

### 3. Retention reference is mandatory and resolved, not just typed

`register_processing_activity` and `register_data_asset` both resolve
`retention_policy_reference` against the retention-policy store and
additionally check the resolved policy belongs to the same organization. A
registry entry therefore cannot point at a nonexistent policy
(`VALIDATION_RECORD_NOT_FOUND`) or at another organization's policy
(`CROSS_ORGANIZATION_CASE_ACCESS_DENIED`). Type-checking a UUID field
would have caught neither.

### 4. Status lifecycle is a closed state machine

`RegistryEntryStatus` is `draft` → `active` ⇄ `suspended` → `deprecated`,
with `deprecated` terminal. Every transition increments
`activity_version` / `asset_version`, so "which version of this activity
description was in force" is answerable. Updating an activity's substance
means registering a new version with `supersedes_activity_version` set,
never editing the old one in place.

### 5. Identity data is refused at the boundary

`ProcessingActivity` accepts an `additional_metadata: dict[str, str]` for
genuinely open notes, and `domain.reject_identity_payload_keys` runs over
it at construction against `FORBIDDEN_IDENTITY_FIELD_NAMES` (28 names:
`email`, `user_id`, `member_id`, `national_id`, `date_of_birth`,
`kyc_payload`, `eid_token`, …). A write carrying any of them raises
`PROCESSING_REGISTRY_IDENTITY_PAYLOAD_REJECTED`. Every name on that list
is exercised by `tests/contract/test_ct00_08_identity_leakage.py`, so the
list and the behaviour cannot drift apart.

### 6. Cross-scope reads need the matching capability

`read_processing_activity` resolves in-scope entries normally. A caller
presenting a `CrossScopeAuthorityGrant` carrying
`read_processing_registry` may reach another organization's entry; a
caller presenting nothing gets the non-disclosing
`VALIDATION_RECORD_NOT_FOUND`, and a caller presenting a grant that
carries a _different_ capability gets the explicit
`CROSS_SCOPE_AUTHORITY_INVALID`.

## Consequences

Easier: the registry is queryable ("every activity in this Land under
`legitimate_interests` whose retention is under 30 days"), reviewable, and
structurally incapable of holding a data subject. Retention and disposal
can rely on `retention_policy_reference` actually resolving.

Harder: an organization whose documented basis does not fit the eight
enum values must use `other_documented` and keep the reasoning in a
document under PACK-11. Extending the enum is additive and cheap, but it
is a contract change, not a data entry.

## Security impact

The identity-rejection gate is a real control, not documentation: it runs
on construction, so it applies on every path into the entity including
future ones. The categorical-only design means a leak of the entire
processing registry discloses organizational structure and processing
purposes — sensitive, but not personal data about any individual.

The mandatory, resolved retention reference closes a subtler hole: an
activity pointing at a policy in another organization would have let a
retention schedule be governed from outside the scope that owns the data.

## Data impact

New schemas: `data-asset`, `processing-activity`. New event:
`processing_activity.status_changed` (carrying the managed
`legal_basis` value, the status, the version and the retention reference —
never a category list of subjects or any note text). No existing entity
changes.

## Migration impact

None. An organization importing an existing spreadsheet inventory must map
its free-text basis column onto the eight enum values, using
`other_documented` where no value fits; that mapping is a data-entry task,
not a schema migration.

## Reversibility

The enum is additive-extendable. Replacing it with free text would be a
breaking contract change and would reintroduce the problem it solves, so
in practice this is reversible only with cost. The identity-rejection gate
is trivially reversible in code and must not be.

## Related canon version

Canon `0.7.0`, no bump. `DataAsset` and `ProcessingActivity` are
compliance-side inventory owned by one service; canon does not name them,
and the one new event uses canon section 21's envelope unchanged.


## Amendment (Architecture & Domain Framework 0.8.1, same 0.9.0 round)

Framework section 13.1 requires a **DPIA gate** in front of processing
activation. This ADR's registry recorded what is processed and on what
basis; it did not decide whether an activity may run.

`dataprotection.assert_activation_permitted` is that gate, and its most
important property is what it does with *absence*:

1. an activity with **no recorded requirement determination at all** is
   refused with `DPIA_REQUIRED`, whatever its risk class;
2. a `high` or `special_category` activity with no assessment is refused;
3. an assessment not in an activating state is refused with
   `DPIA_NOT_APPROVED`;
4. an approved assessment past its `valid_until` is refused at step 3 as
   well — "expired" is the practical meaning of an approval past its
   validity date, before anybody transitions the record.

Step 1 is the load-bearing one. "Nobody ever asked" and "we asked and the
answer was no" are different states with different outcomes, and a gate
that treated a missing determination as a pass would let every
unassessed activity through. `DPIARequirementDetermination` is therefore
recorded even when `dpia_required` is false, and
`dpia.requirement_determined` is published either way.

`assert_dpo_independence` refuses an approval whose reviewer is the
controller or the process owner. An assessment signed off by the party
that wants the processing is not a review.

Activation itself is a recorded decision
(`ProcessingActivationDecision`), not a derived consequence of an
approved DPIA: an activity becomes active because somebody with authority
decided so and that decision carries a reason code. Blocked and revoked
activations travel through the same object, so a refusal is visible
rather than silent.

`ConsentWithdrawalRecord.retention_obligation_persists` records the
converse: withdrawal of consent is **not** automatic deletion where a
statutory retention duty or an active hold still applies. Conflating the
two would let a withdrawal destroy evidence.
