# FRONT-05 PACK / API DEPENDENCY RECONCILIATION

Derived from `frontend/representative-workspace/domain/capabilities.ts` by
`scripts/build_front05_records.py`. This document is not maintained by hand:
a hand-written dependency table drifts from the code it describes and then
reassures a reviewer about something that is no longer true.

## Summary

- Capabilities in the register: **29**
- `SUPPORTED_REAL_PATH`: **3** — all three are local, depending on nothing external
- `BLOCKED_BY_DEPENDENCY`: **25**
- `UNSUPPORTED`: **1** — a prohibition, not a missing dependency
- `SUPPORTED_WITH_DECLARED_LIMITATION`: **0**

No capability that reaches the network is supported. There is no accepted
executable HTTP runtime anywhere in the programme: every
`contracts/openapi/pack-*.yaml` states that no production HTTP server ships in
that pack, and the two services WS-04 would need — `representative-desk-service`
(PACK-29) and `office-mandate-service` (PACK-20) — exist only inside unaccepted
candidate archives. The representative-facing requirements FIR-REP-001..004 are
recorded as `captured`, which is the pre-specification state.

## The distinction this document exists to draw

A dependency that is missing and a dependency that is defective are different findings. A missing dependency becomes a real path when it is built. A defective one must be corrected before it may be relied on at all, and a route appearing over the top of it does not correct it.

**Rule.** A capability whose dependency is classified SECURITY_SENSITIVE_BOUNDARY may only carry status BLOCKED_BY_DEPENDENCY or UNSUPPORTED. It may never be SUPPORTED_REAL_PATH, and it may never be SUPPORTED_WITH_DECLARED_LIMITATION — a declared limitation states the bounds within which something is safe, and there are no bounds within which a self-asserted authorization is safe.

## Security-sensitive boundaries

These are not entries in a gap list. Each is a finding against the dependency
itself, and each is reported upward as such.

### SSD-01 — PACK-13 transparency-service

**Affects.** `publication_proposal_submission`, `publication_state_observation`

**Observed.** Publication has the single state PUBLISHED, and authorization is a caller-supplied actor_is_authorized boolean.

**Finding.** A caller-supplied authorization boolean is a self-asserted authorization: the caller declares its own permission and the service accepts the declaration. The field that looks like an authorization gate is an authorization claim, made by exactly the party the gate exists to constrain. Accepting it as sufficient would let a rendition reach publication carrying nothing but the proposer's own claim of being allowed to publish — which is the separation WS-04 exists to preserve.

**FRONT-05 position.** FRONT-05 does not treat this boolean as evidence that authorization occurred, does not set or send such a flag, and builds no privileged path on it. No port signature contains a field it could be carried in.

**Remedies that would not resolve it:**

- adding a proposal route while authorization stays caller-supplied
- having WS-04 set actor_is_authorized itself
- treating a successful call as evidence that authorization occurred
- recording the capability as SUPPORTED_WITH_DECLARED_LIMITATION

**Unblocking condition.** a server-authoritative proposal and authorization contract: a proposal state distinct from PUBLISHED, and an approval decided and recorded by an authority other than the proposer.

**Status until then.** BLOCKED_BY_DEPENDENCY, with publication approval itself remaining prohibited for WS-04 under every dependency state.

**Escalation.** Reported to the accepting authority as a security-relevant finding against PACK-13, not as a FRONT-05 gap.

## Prohibited capability

- `conflict_restriction_change` — A subject may never clear a restriction over themselves. This is a prohibition, so it would remain unsupported even if an accepted route existed.

## Absent dependencies

Missing, and unremarkable: each becomes a real path when the named thing is
built and accepted.

| Capability | Owner | Missing dependency |
| --- | --- | --- |
| `mandate_session_establishment` | API-02 / identity boundary | an accepted executable route issuing a mandate-scoped representative session |
| `mandate_scope_resolution` | PACK-20 office-mandate-service (unaccepted) | an accepted mandate register exposing the mandate, its level, and its active authority window |
| `authority_revalidation` | PACK-20 office-mandate-service (unaccepted) | an accepted server-side authority check evaluated at commit time |
| `step_up_authentication` | API-02 / identity boundary | an accepted executable step-up ceremony returning a raised assurance level |
| `case_intake_list` | PACK-29 representative-desk-service (unaccepted) | an accepted executable route listing mandate-scoped citizen cases |
| `case_detail_read` | PACK-29 representative-desk-service (unaccepted) | an accepted executable route returning a single case within mandate scope |
| `case_assignment` | PACK-29 representative-desk-service (unaccepted) | an accepted executable case assignment operation |
| `case_triage_transition` | PACK-29 representative-desk-service (unaccepted) | an accepted executable state-transition operation with optimistic-concurrency semantics |
| `case_response_record` | PACK-29 representative-desk-service (unaccepted) | an accepted executable route recording an outbound response against a case |
| `case_scoped_search` | PACK-29 representative-desk-service (unaccepted) | an accepted executable search operation that is server-side scope-bound |
| `position_draft_read` | PACK-29 representative-desk-service (unaccepted) | an accepted executable route returning stored position drafts |
| `position_draft_write` | PACK-29 representative-desk-service (unaccepted) | an accepted executable route persisting a draft |
| `position_internal_submission` | PACK-29 representative-desk-service (unaccepted) | an accepted executable route accepting an internal submission |
| `deviation_record_read` | PACK-29 / transparency-service | an accepted executable route returning deviation records with provenance |
| `deviation_record_write` | PACK-29 representative-desk-service (unaccepted) | an accepted executable route recording a deviation against a governed decision |
| `deviation_decision_reference` | PACK-16 / decision runtime | an accepted executable route resolving a governed decision identifier to its published record |
| `declaration_read` | PACK-09 compliance-service | an accepted executable route returning a representative's own declarations |
| `declaration_submission` | PACK-09 compliance-service | an accepted executable route accepting a declaration submission |
| `conflict_restriction_read` | PACK-09 compliance-service | an accepted executable route returning active conflict restrictions for a mandate |
| `registry_read_reference` | PACK-20 / PACK-09 registers (unaccepted or specification-level) | an accepted executable read route over a protected register |
| `eligibility_status_display` | Eligibility authority, outside WS-04 | an accepted executable route returning a decided eligibility status |
| `audit_trail_read` | CTRL / governed control plane (NOT_STARTED) | any control-plane implementation whatsoever |
| `telemetry_emission` | Platform telemetry (not connected) | a connected accepted telemetry platform |

## Machine assertions

| Assertion | Value |
| --- | --- |
| `no_security_sensitive_capability_is_supported` | `true` |
| `no_security_sensitive_capability_is_a_declared_limitation` | `true` |
| `every_security_sensitive_capability_states_a_finding` | `true` |
| `caller_asserted_authorization_treated_as_sufficient` | `false` |

Checked by gate `G46` in `scripts/validate_front05.py` and asserted at module
load in `domain/capabilities.ts`, which throws rather than letting the
workspace start with a security-sensitive capability marked supported.
