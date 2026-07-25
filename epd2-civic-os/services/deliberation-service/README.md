# Deliberation Service

Owns `Discussion` (canon section 13.1) and `Contribution` (canon section
13.2; ownership matrix section 22, "Discussion Service"). No other
service reads or writes this service's storage directly (INV-03).

## No PACK-02 dependency (ADR-008)

`docs/adr/ADR-008-pack-03-pack-02-integration-boundary.md` explicitly
lists `deliberation-service` (alongside `moderation-service`,
`tally-service`, `delegation-service`) as having **no PACK-02 dependency
identified** in `docs/handover/PACK-03-SPEC.md`. This package therefore
has zero import dependency on `epd2_credential_service`,
`epd2_eligibility_service`, or `epd2_identity_service` - `pyproject.toml`
depends on only `epd2-core` and `epd2-audit-core`. Per ADR-008, if a
future change reveals an actual need for one of those imports, it must be
added to that ADR (or a superseding ADR) before the import is written,
not added silently.

## Owned entities

- `Discussion` — `discussion_id, subject_type, subject_id, space_id,
status, moderation_policy_id`. Statuses: `open, limited, read_only,
closed, archived`. `archived` is terminal.
- `Contribution` — `contribution_id, discussion_id, author_actor_id,
parent_contribution_id, contribution_type, content, content_hash,
visibility_status, created_at, edited_version`. `contribution_type` is
  a fixed, separate enum (`comment, argument_for, argument_against,
question, answer, proposal, source_note, moderator_notice`) that never
  changes after creation. `visibility_status` values: `visible,
temporarily_hidden, restricted, removed_from_public_view, restored`.

## Canonical events (canon section 20.8, verbatim)

`discussion.opened`, `contribution.created`, `contribution.edited`,
`contribution.flagged`, `contribution.hidden`, `contribution.restored`,
`discussion.closed` — one command per event in `application.py`. No other
event types are defined by this service.

## No-domain-event `Discussion` transitions

Canon section 13.1's `Discussion` transition table has nine edges, but
section 20.8's event list only accounts for the two that create/end a
discussion outright (`open_discussion` → `discussion.opened`,
`close_discussion` → `discussion.closed`). The remaining four edges have
no canon event name at all:

- `open -> limited` (`application.limit_discussion`)
- `open|limited -> read_only` (`application.set_discussion_read_only`)
- `limited|read_only -> open` (`application.reopen_discussion`, reopening
  an existing discussion — distinct from `open_discussion`, which creates
  a brand-new one)
- `closed -> archived` (`application.archive_discussion`)

Each of these four commands still persists the transition and appends an
audit entry (`reason_code="DISCUSSION_STATUS_CHANGED"`, CT-00-07 /
INV-04) — they simply never build an `EventEnvelope`, the same "no event
for this step" shape
`epd2_voting_service.application.submit_ballot_for_configuration_review`
established. See `application.DiscussionTransitionResult` (no `event`
field) and `application._simple_discussion_transition_no_event`.

## No physical deletion (canon section 13.2)

Canon states: "Физическое удаление политически значимого Contribution
допускается только по отдельной retention policy, при сохранении audit
proof" (physical deletion of a politically significant `Contribution` is
allowed only under a separate retention policy, with audit proof
preserved). This service implements **no** physical deletion at all -
only `visibility_status` transitions such as `-> removed_from_public_view`,
which still preserve the row, its `content_hash`, and its full audit
trail via Audit Core. A separate, not-yet-specified retention-policy
process is canon's named mechanism for actual physical deletion; its
absence here is deliberate scope discipline, not an oversight.

## `restore_contribution` design choice

Canon section 13.2's transition table has two distinct edges back toward
public visibility:

```
temporarily_hidden -> restored
restricted -> restored
removed_from_public_view -> restored
restored -> visible
```

but canon section 20.8's event list defines only **one** event name for
this whole direction, `contribution.restored` — there is no second
canonical event for the `restored -> visible` leg specifically, and this
service must not invent one (step 3 of its build brief: emit only the
seven verbatim canon events).

Resolution: `application.restore_contribution` is a single command that
dispatches its actual target status off the contribution's _current_
status (see `_next_restore_target` in `application.py`):

- from `temporarily_hidden` / `restricted` / `removed_from_public_view` →
  transitions to `restored`.
- from `restored` → transitions to `visible`.

Both legs emit `contribution.restored` and both produce their own
distinct audit entry (`action="restore"`,
`reason_code="CONTRIBUTION_STATUS_CHANGED"`, with `before_hash`/
`after_hash` reflecting that specific leg's transition) — no hop is
silently skipped or merged into the other. A caller that wants a
`temporarily_hidden` contribution to end up fully `visible` again must
call `restore_contribution` twice: once to reach `restored`, once more to
reach `visible`. This keeps every state change individually audited
(CT-00-07) while staying within canon's exact, closed event vocabulary.

## Idempotency (CT-00-04)

Every command accepts an optional `event_id`, reused as the audit call's
`audit_event_id` — the same pattern `issue_participation_credential`
(credential-service) established. `open_discussion` and
`create_contribution` get this "for free" from their store's own
content-based dedup (mirroring `CredentialStore.issue`). The four
transition-mutating commands (`close_discussion`, `edit_contribution`,
`hide_contribution`, `restore_contribution`) instead check
`audit_store.get_by_event_id(event_id)` _before_ touching the store, and
short-circuit to the original result on a genuine replay — otherwise a
second identical call would see the _already-transitioned_ entity and
raise a spurious forbidden-transition error. `flag_contribution` needs no
special handling: it never mutates `Contribution` state, so a replayed
call naturally produces byte-identical audit content, and Audit Core's
own `append_audit_event` idempotency resolves it.

## `flag_contribution` and moderation-service

A flag is what typically triggers a `moderation-service` `ModerationCase`
(canon section 14.1) in the full system. Per ADR-005/ADR-008,
`deliberation-service` has no dependency edge to `moderation-service` (in
either direction) — `flag_contribution` only emits `contribution.flagged`
for some other process to react to; it never imports or calls
`moderation-service`.
