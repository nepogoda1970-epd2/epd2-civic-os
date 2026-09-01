# Audit Kernel (Audit Core)

Status: implemented for CLAUDE-PACK-02. This document describes
`services/audit-core`, the single append-only, hash-chained store for
`AuditEvent` (canon section 18.1), and how the other four PACK-02 services
call into it. See `docs/adr/ADR-003-append-only-audit-hash-chain.md` for
the decision record behind the chaining design, and
`docs/review/PACK-02-THREAT-MODEL.md` ("event tampering") for what this
mechanism does and does not protect against.

## 1. Why Audit Core exists

Canon `INV-04` requires that every politically or legally significant
action leave a durable, verifiable trace; `INV-05` requires that a
politically significant object is never silently overwritten without
retaining the prior version. Within PACK-02's scope, the significant
actions are: account creation and status change, identity verification
(start, result, revocation), eligibility evaluation and snapshot creation,
and credential issuance/revocation. Audit Core is the one place all of
these land, independent of which of the other four services performed the
action.

## 2. Ownership and interface

Audit Core owns `AuditEvent` exclusively (canon section 22 ownership
matrix) and exposes only:

- `append(request) -> AuditEvent` — the sole write path.
- `get_by_event_id(audit_event_id) -> AuditEvent | None`
- `list_by_aggregate(target_type, target_id) -> list[AuditEvent]`
- `verify_chain() -> ChainVerificationResult`

There is no `update` or `delete` method on `InMemoryAuditEventStore` at
all — not merely an unused one. `tests/contract/test_audit.py::test_append_only_no_update_or_delete_method_exists`
checks this structurally (`hasattr(store, "update")` etc. must be
`False`), so "append-only" is a property of the interface's shape, not
just a documented convention a future change could quietly violate.

## 3. Every critical service action calls Audit Core

Per CT-00-07, a service's critical command is not considered done unless
it actually produces a durable `AuditEvent` — the pack (section 17)
explicitly forbids claiming an audit trail exists in documentation only.
Concretely, the following application functions take an `audit_store`
parameter and call `append_audit_event` before returning:

| Service             | Function                          | `AuditEvent.reason_code` on success                                                                                                                                 |
| ------------------- | --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| account-service     | `create_account`                  | `ACCOUNT_CREATED`                                                                                                                                                   |
| account-service     | `change_account_status`           | `ACCOUNT_STATUS_CHANGED` (only when the transition has a canonical event — see ADR-002)                                                                             |
| identity-service    | `start_identity_verification`     | `IDENTITY_VERIFICATION_STARTED`                                                                                                                                     |
| identity-service    | `record_verification_result`      | outcome-specific (`IDENTITY_VERIFIED`, `IDENTITY_NOT_VERIFIED`, `IDENTITY_VERIFICATION_EXPIRED`, `IDENTITY_DUPLICATE_SUSPECTED`, `IDENTITY_MANUAL_REVIEW_REQUIRED`) |
| identity-service    | `revoke_verification`             | `IDENTITY_VERIFICATION_REVOKED`                                                                                                                                     |
| eligibility-service | `evaluate_eligibility`            | outcome-specific (`ELIGIBILITY_MET`, `ELIGIBILITY_NOT_MET`, `ELIGIBILITY_PENDING`, or `INTEGRITY_CHECK_FAILED` fail-closed for an unreachable decision value)       |
| eligibility-service | `create_eligibility_snapshot`     | `ELIGIBILITY_SNAPSHOT_CREATED`                                                                                                                                      |
| credential-service  | `issue_participation_credential`  | `CREDENTIAL_ISSUED`                                                                                                                                                 |
| credential-service  | `revoke_participation_credential` | relevant `CREDENTIAL_*` code                                                                                                                                        |

Deliberately **not** audited, and documented as such in each function's
docstring rather than left silent: `eligibility-service`'s
`create_eligibility_rule` (emits no domain event and has no natural audit
key by design) and `credential-service`'s `validate_participation_credential`
(a read-only query with no state change to record).
`tests/contract/test_ct00_07_audit_creation.py` checks both the positive
case (a real, retrievable `AuditEvent` exists after each audited action)
and the negative case (a denied command — `actor_is_authorized=False` —
creates zero `AuditEvent`s, since `PERMISSION_DENIED` is refused before
any state change occurs).

Every domain service depends on `epd2-audit-core` as an ordinary package
dependency (see each service's `pyproject.toml`) — this is the one
intentional cross-service dependency in the whole system, and it is
one-directional: Audit Core depends on nothing domain-specific in return.

## 4. Hash chaining and tamper evidence

A single global, sequential hash chain (not one chain per aggregate — see
ADR-003 for why) links every `AuditEvent` ever appended:

```text
event_hash = sha256(canonical_dumps(record_without_event_hash) + previous_event_hash)
```

`canonical_dumps` (`epd2_core.canonical_json`) produces a deterministic,
key-order-independent serialization, so `event_hash` depends only on
logical content — checked directly by
`tests/contract/test_audit.py::test_event_hash_is_deterministic_for_identical_content`
and by a Hypothesis test
(`tests/contract/test_property_based.py::test_canonical_dumps_is_independent_of_input_key_order`).

`verify_chain()` recomputes every `event_hash` in order and confirms each
record's stored `previous_event_hash` matches the prior record's stored
`event_hash`; a mismatch reports the first broken link's
`audit_event_id`, not merely `False`. Both classes of tamper are tested
directly against the in-memory store (bypassing the public API, since the
public API has no way to tamper in the first place — see section 2):
mutating a stored record's payload field (`test_verify_chain_detects_a_tampered_payload`)
and mutating a stored record's `previous_event_hash` link
(`test_verify_chain_detects_a_broken_previous_hash_link`).

This is explicitly **not** presented as a production-grade blockchain or
qualified electronic evidence (pack section 9.2) — it is a minimal,
in-memory, single-process tamper-evidence mechanism sufficient for
contract tests. See `docs/review/PACK-02-THREAT-MODEL.md` for the
residual risk this leaves (an actor with write access to the underlying
store can rebuild an internally-consistent alternate chain from scratch;
this mechanism detects tampering with records left in place, it does not
prevent a full, self-consistent rewrite).

## 5. Idempotency and conflict (CT-00-04, pack section 9.3)

Appending an `audit_event_id` already present, with identical content, is
a no-op success — it returns the existing record rather than creating a
duplicate or raising. Appending the same `audit_event_id` with different
content is rejected fail-closed with a stable reason code
(`AUDIT_EVENT_CONFLICT`), and the existing record is never overwritten.
Both are checked directly (`test_idempotent_replay_of_identical_request_succeeds`,
`test_conflict_on_duplicate_event_id_with_different_body`) and via
Hypothesis over arbitrary action-text/id combinations
(`test_property_based.py`).

This is Audit Core's own guarantee at the `audit_event_id` layer, distinct
from — and narrower than — end-to-end command-level idempotency at the
call-site layer (a caller retrying "issue this same credential" and
getting exactly one audit entry, not two, requires the caller to supply
the same `audit_event_id` on retry). Only
`credential-service.issue_participation_credential` currently accepts an
explicit `event_id` parameter for this; the other three services'
analogous create-commands do not yet, which is recorded as a known,
non-blocking asymmetry in `docs/review/OPEN_QUESTIONS.md` (item 11).

## 6. Fields (canon 18.1, unchanged)

`AuditEvent` carries exactly the canon-mandated fields — `audit_event_id`,
`event_type`, `occurred_at`, `recorded_at`, `actor_id`, `actor_type`,
`target_type`, `target_id`, `action`, `reason_code`, `policy_version`,
`before_hash`, `after_hash`, `correlation_id`, `source_service`,
`previous_event_hash`, `event_hash` — with no PACK-02-specific additions.
`before_hash`/`after_hash` are computed from each service's full-state
payload function (e.g. `credential_full_state_payload`, distinct from the
minimal payload used for the service's own domain events — see
`docs/adr/ADR-002-identity-participation-separation.md` for why these two
payload shapes are kept separate).

## 7. Clock injection (pack section 13.3)

All audit timestamps (`occurred_at`, `recorded_at`) come from a
dependency-injected `Clock` (`epd2_core.clock.Clock`/`FixedClock`), never
from a direct system-time call inside domain logic — this is what makes
`tests/contract/test_audit.py`'s determinism assertions and the Hypothesis
property tests reproducible.
