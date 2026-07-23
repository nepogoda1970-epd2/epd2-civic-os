# Transparency Service

Owns `PublicLedgerEntry`, `AuditExportPackage`, `DisclosurePolicy`,
`LobbyLogEntry` (canon `docs/canonical/TZ-00-domain-event-canon.md`
section 19a, added by canon 0.3.0 / ADR-013). ADR-011 consolidates all
four into this one physical package.

## Cross-pack read boundary (ADR-012)

This is the first time this project reads from another same-generation
pack (PACK-03) rather than an older one. `pyproject.toml` declares five
dependencies beyond `epd2-core`/`epd2-audit-core`:
`epd2-initiative-service`, `epd2-moderation-service`,
`epd2-voting-service`, `epd2-tally-service`. ADR-012 sanctions four
upstream read-only functions, each newly added (this pack) to the
*upstream* service's own `application.py` as a small, additive,
backward-compatible read wrapper around that service's existing `Store.
get`, as PACK-04's only permitted upstream `.application`-module
imports:

- `epd2_initiative_service.application.get_published_initiative` /
  `get_initiative_version`
- `epd2_moderation_service.application.get_moderation_decision`
- `epd2_voting_service.application.get_ballot`
- `epd2_tally_service.application.get_result_publication`

These four are import-legal and boundary-tested (`tests/repository/
test_service_boundaries.py`'s
`ALLOWED_PACK04_TO_UPSTREAM_APPLICATION_MODULES`), but no command body
in `epd2_transparency_service.application` currently calls them:
`publish_ledger_entry`, `correct_ledger_entry`, and
`submit_lobby_log_entry` all take caller-supplied content
(`raw_content`) rather than fetching it internally — sourcing the
correct upstream snapshot is the caller's responsibility, and this
service's own job is disclosure filtering plus immutable publication.
They remain available for a later verify-before-publish enhancement
(e.g. rejecting a ledger entry whose `subject_id` does not resolve to a
real published initiative).

This module also uses one new, additive, read-only Audit Core function,
`epd2_audit_core.application.list_by_target_types`, called directly
from `generate_audit_export_package`. No PACK-02 identity/credential
service, no `deliberation-service`, and no `delegation-service` is ever
imported here — see `tests/repository/test_service_boundaries.py`'s
`ALLOWED_PACK04_TO_UPSTREAM_APPLICATION_MODULES`.

## Entities and their state machines

### `PublicLedgerEntry` (canon 19a.1)

No status transition table — the only status is `published`, set at
creation, never changed. A correction is always a *new* row with
`supersedes_entry_id` set (`application.correct_ledger_entry`); the
original row is never rewritten (`storage.PublicLedgerEntryStore` has no
`save`). `previous_entry_hash` chains published entries in creation
order — a separate, lighter hash chain from Audit Core's own
(`domain.LEDGER_GENESIS_HASH`).

### `AuditExportPackage` (canon 19a.2)

`generated -> published -> superseded`
(`domain.AUDIT_EXPORT_PACKAGE_ALLOWED_TRANSITIONS`). `published ->
superseded` is never a standalone command — it only ever happens as a
side effect of `application.publish_audit_export_package` publishing a
*new* package whose own `supersedes_package_id` names the old one; the
old package's content is never rewritten, only its `status`.

`chain_proof` (ADR-013 amendment 1): an ordered list of `ChainProofItem`
— `event_hash`, `previous_event_hash` (of the *previous item in this
exported segment*, not Audit Core's own chain), public-safe metadata,
`sequence_position`. `package_digest` and `integrity_proof` are
package-level fields computed over the whole ordered list. See
`application.verify_audit_export_package`'s docstring, and canon section
19a.2's own "Семантика проверки", for exactly what this proves (chain
continuity, ordering/completeness, non-modification of the *exported
segment*) and what it explicitly does not (recomputing the original
private `AuditEvent.event_hash` values, which depend on fields this
package never discloses — `actor_id`, `actor_type`, `before_hash`,
`after_hash`).

### `DisclosurePolicy` (canon 19a.3)

`draft -> active -> superseded`
(`domain.DISCLOSURE_POLICY_ALLOWED_TRANSITIONS`). `draft -> active`
requires `approved_by_role_id` (INV-08). At most one `active` policy per
`applies_to_subject_type` at a time — activating a new version
automatically supersedes the previously-active one for the same subject
type (`application.activate_disclosure_policy`), never a standalone
command.

`field_rules` (ADR-013 amendment 2): each rule is `field_path`,
`disclosure_class` (`public`/`redacted`/`restricted`/`prohibited`),
`transformation` (`none`/`generalize_to_role_scope`/`band_small_cell`/
`suppress`/`hash`), optional `replacement_label`. A field with no
matching rule, or more than one, resolves to `prohibited` (fail-closed,
INV-10, `domain.resolve_field_rule`) — this is never overridable, and a
structurally forbidden field (`domain.FORBIDDEN_FIELD_NAMES`) can never
be reclassified to anything but `prohibited` (enforced in
`DisclosurePolicy.__post_init__`).

`small_cell_threshold` defaults to `10`
(`domain.DEFAULT_SMALL_CELL_THRESHOLD`): values `1..9` are banded as
`"1-9"`, `0` shown exactly, everything `>= 10` shown exactly
(`domain.band_small_cell_value`). `PublicLedgerEntry.subject_type =
result_publication` is exempt (`domain.
SMALL_CELL_EXEMPT_SUBJECT_TYPES`) — the formally required official
result always discloses exact counts.

### `LobbyLogEntry` (canon 19a.4)

`submitted -> published`, one-shot, no return
(`domain.LOBBY_LOG_ENTRY_ALLOWED_TRANSITIONS`). Publication requires
mandatory automated validation (completeness, no forbidden fields, an
`active` `DisclosurePolicy` for `"lobby_log_entry"`) and has **no**
mandatory human pre-publication review by default (ADR-015 item 4,
amended). Canon's 7-calendar-day publication window
(`domain.LOBBY_LOG_PUBLICATION_WINDOW`) is not hard-enforced as a
publish-blocking rule — see `domain.is_within_publication_deadline`'s
docstring and "Known gaps" below. A correction is always a new row with
`supersedes_entry_id` (`application.correct_lobby_log_entry`), only
allowed against an already-`published` original.

## Application commands -> canon events (section 20.14, verbatim list)

| Command                          | Transition                                          | Event                                       |
| --------------------------------- | ---------------------------------------------------- | --------------------------------------------- |
| `publish_ledger_entry`            | (create) `-> published`                             | `transparency.ledger_entry_published`       |
| `correct_ledger_entry`            | (create, new row) `-> published`                    | `transparency.ledger_entry_corrected`       |
| `generate_audit_export_package`   | (create) `-> generated`                             | `transparency.audit_export_generated`       |
| `publish_audit_export_package`    | `generated -> published` (+ old `-> superseded`)   | `transparency.audit_export_published`       |
| `define_disclosure_policy`        | (create) `-> draft`                                 | `transparency.disclosure_policy_defined`    |
| `activate_disclosure_policy`      | `draft -> active` (+ old `-> superseded`)          | `transparency.disclosure_policy_activated`  |
| _(side effect of the above)_      | `active -> superseded`                              | `transparency.disclosure_policy_superseded` |
| `submit_lobby_log_entry`          | (create) `-> submitted`                             | `transparency.lobby_log_entry_submitted`    |
| `publish_lobby_log_entry`         | `submitted -> published`                            | `transparency.lobby_log_entry_published`    |
| `correct_lobby_log_entry`         | (create, new row) `-> published`                    | `transparency.lobby_log_entry_corrected`    |

Every command follows the shared shape: `actor: ActorRef,
actor_is_authorized: bool, correlation_id: UUID, clock: Clock, event_id:
UUID | None = None`, and every state-changing command calls
`append_audit_event` (CT-00-07). `event_id` is the CT-00-04 idempotency
key.

## Never published verbatim (canon 19a.6)

`published_by_role_id`, `requested_by_role_id`, `approved_by_role_id`,
`submitted_by_role_id` are real, stored domain fields (internal
`RoleAssignment` references) but are omitted entirely from every
`*_public_payload` function in `events.py` — the only place any of these
four entities is serialized for a public event. `domain.
FORBIDDEN_FIELD_NAMES` additionally blocks
`account_id`/`person_id`/`identity_record_id`/
`participation_credential_id`/`vote_envelope_id`/
`encrypted_or_encoded_choice`/`credential_proof` from ever entering a
`content_snapshot` (`domain.assert_no_forbidden_fields`, called
unconditionally in `domain.apply_disclosure_policy`, before any
`DisclosurePolicy` rule is even consulted). `AuditExportPackage.
chain_proof` items (`domain.ChainProofItem`) structurally have no
`actor_id`/`actor_type`/`before_hash`/`after_hash` fields at all — they
cannot be included even by mistake.

## Known gaps (documented, not silently dropped)

- **7-day Lobby Log publication window is not publish-blocking.** Canon
  names no dedicated reason code for a *missed* deadline (unlike
  `LOBBY_LOG_ENTRY_INCOMPLETE` for missing mandatory fields), so
  `publish_lobby_log_entry` does not hard-reject a late publish on this
  basis alone; `domain.is_within_publication_deadline` is
  observability-only.
- **`integrity_proof` is not a cryptographic signature.** No signing key
  is implemented in this pack — `application._compute_integrity_proof`
  is a deterministic, publicly-recomputable hash over
  `package_digest`/`event_count`/`generated_at`, not a signature. Canon
  section 19a.2's own "Семантика проверки" never claims signature
  verification either, only chain-continuity/ordering/non-modification.
- **`applies_to_subject_type` is a free string**, not a closed enum —
  canon section 19a.3 gives this field no enumerated value list (unlike
  `PublicLedgerEntry.subject_type` or `AuditExportPackage.
  included_target_types`, which canon does enumerate).

## Reason codes

Canon codes reused verbatim: `VALIDATION_UNKNOWN_STATUS`,
`VALIDATION_FORBIDDEN_TRANSITION`, `VALIDATION_RECORD_NOT_FOUND`,
`PERMISSION_DENIED`.

Additive, ADR-014 (`exceptions.py`): `DISCLOSURE_POLICY_VIOLATION`,
`PUBLICATION_NOT_ALLOWED`, `REDACTION_REQUIRED`,
`LOBBY_LOG_ENTRY_INCOMPLETE`, `AUDIT_EXPORT_INTEGRITY_FAILED`,
`LEDGER_ENTRY_ALREADY_PUBLISHED`.

Additive, this service's own duplicate-conflict codes (`exceptions.py`):
`LEDGER_ENTRY_DUPLICATE_CONFLICT`,
`AUDIT_EXPORT_PACKAGE_DUPLICATE_CONFLICT`,
`DISCLOSURE_POLICY_DUPLICATE_CONFLICT`,
`LOBBY_LOG_ENTRY_DUPLICATE_CONFLICT`.

Additive, audit-success classifications (`application.py`, info
severity): `TRANSPARENCY_LEDGER_ENTRY_PUBLISHED`,
`TRANSPARENCY_AUDIT_EXPORT_STATUS_CHANGED`,
`TRANSPARENCY_DISCLOSURE_POLICY_STATUS_CHANGED`,
`TRANSPARENCY_LOBBY_LOG_ENTRY_STATUS_CHANGED`.
