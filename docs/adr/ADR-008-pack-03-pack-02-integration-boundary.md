# ADR-008: PACK-03 to PACK-02 integration boundary

## Status

`accepted`

## Date

2026-07-22

## Owner decision

Accepted as proposed, 2026-07-22. The project owner approved the
enumerated PACK-03 → PACK-02 dependency edges and the one-way dependency
rule (Decision, below) with no amendments, including deferring Option C
(a real message bus) rather than adopting it now. Actually writing the
cross-service call sites remains a later, separate implementation task,
not authorized by this acceptance alone.

## Context

PACK-02 shipped five services (`account-service`, `identity-service`,
`eligibility-service`, `credential-service`, `audit-core`) that today are
mutually independent except for each writing to `epd2_audit_core`
directly. PACK-03 (`docs/handover/PACK-03-SPEC.md`) is the first pack
where a service must _read_ another pack's already-shipped state to do
its own job:

- `initiative-service`'s `SupportRecord` needs a valid `initiative_support`
  `ParticipationCredential` (credential-service).
- `voting-service`'s `VoteEnvelope` needs a valid `ballot_access`
  `ParticipationCredential` (credential-service).
- `voting-service`'s `Ballot.eligibility_rule_version` needs to freeze
  against a real `EligibilityRule`/`EligibilitySnapshot`
  (eligibility-service), per canon section 9.1 ("after opening a vote,
  the rule version used is frozen").

INV-03 ("no direct access to another's database") forbids any PACK-03
service from importing a PACK-02 service's storage module or reaching
into its store directly — but it does not, by itself, say what a
_legitimate_ cross-service read looks like. This has never been decided
before because no PACK-02 service currently depends on another PACK-02
service at all.

## Problem

Without an explicit, enumerated boundary, "call the other service" could
be silently implemented as `from epd2_credential_service.storage import
InMemoryCredentialStore` inside `voting-service` — which is exactly the
INV-03 violation the existing `tests/repository/test_service_boundaries.py`
AST-based check was built to catch, except that check today has no rule
at all for a _cross-pack_ import (it only encodes PACK-02's own five
services' internal boundaries). Left unresolved, PACK-03 implementation
would either invent an ad hoc, unreviewed convention per service, or
accidentally violate INV-03 in a way the existing structural test cannot
even detect, because its forbidden-pair matrix has never been extended to
include a PACK-02↔PACK-03 edge at all.

Additionally, this repository has no real message bus
(`docs/review/KNOWN_LIMITATIONS.md`) — "communicate via canonical events"
today means "call a function that constructs/returns the same envelope a
real event bus would carry later," which must be stated explicitly here
rather than left to look like a genuine asynchronous integration.

## Considered options

- Option A — no boundary rule; each PACK-03 service developer decides
  case by case whether to import a PACK-02 storage module, an
  application-layer function, or something else, as the need arises.
- Option B — every PACK-03 service calls PACK-02 services' existing
  public `application`-layer functions only (e.g.
  `epd2_credential_service.application.validate_participation_credential`),
  never their `storage`/`domain` internals, with the exact allowed
  function set enumerated per PACK-03 service in this ADR and encoded as
  new rows in `tests/repository/test_service_boundaries.py`'s forbidden-
  pair matrix; the dependency direction is one-way (PACK-02 services may
  never import a PACK-03 service).
- Option C — introduce a real message queue / event bus now, so PACK-03
  services subscribe to PACK-02's canonical events asynchronously instead
  of calling functions in-process.

## Decision

Option B. Concretely:

1. **Allowed edges** (to be finalized per-service when each service's
   `pyproject.toml` is written, but the _shape_ is fixed now): each
   PACK-03 service's dependency list may include exactly the PACK-02
   service packages it legitimately needs, and only their `application`
   module's public functions —
   - `initiative-service` → `epd2_credential_service.application`
     (validate `initiative_support` credentials),
     `epd2_eligibility_service.application` (read eligibility decisions
     backing a support action).
   - `voting-service` → `epd2_credential_service.application` (validate
     `ballot_access` credentials), `epd2_eligibility_service.application`
     (freeze against `EligibilitySnapshot`).
   - `deliberation-service`, `moderation-service`, `tally-service`,
     `delegation-service` → no PACK-02 dependency identified yet in
     `docs/handover/PACK-03-SPEC.md`; if implementation reveals one, it
     must be added to this ADR (or a superseding ADR) before the import
     is written, not added silently.
2. **Forbidden direction**: no PACK-02 service package may ever import
   anything from a PACK-03 service package. PACK-02 already shipped and
   passed verification without knowledge of participation/decision
   concerns; this ADR keeps it that way.
3. **Forbidden regardless of direction**: any PACK-03↔PACK-03 import
   across the six new services (each communicates with its siblings only
   through the canonical events in `docs/handover/PACK-03-SPEC.md`
   section 5, or a specific, named, whitelisted read function — e.g.
   `tally-service` reading `voting-service`'s validated `VoteEnvelope` set
   requires its own named interface function, never free access to
   `voting-service`'s internals). This is a restatement of ADR-005's own
   service-boundary intent, made explicit here because it is the same
   kind of edge this ADR is otherwise enumerating exceptions to.
4. `tests/repository/test_service_boundaries.py` must be extended (not
   simply re-run) to encode every edge in item 1 as an explicit
   allow-list entry and to assert item 2 and item 3 as forbidden for
   every pair not on that list — the same AST-walk-based mechanism
   already used for PACK-02's own five-service matrix, extended in scope,
   not replaced.
5. Option C (a real message bus) is explicitly deferred, not rejected
   outright — it may become necessary once Transparency/Governance
   contexts (out of PACK-03's scope, `docs/handover/PACK-03-SPEC.md`
   section 1) need to consume these same events asynchronously. Adopting
   it now would be a significant, unscoped infrastructure change with no
   PACK-03 requirement driving it; Option B's in-process function calls
   are sufficient for everything PACK-03 itself needs and keep the change
   surface limited to what this pack actually requires.

## Consequences

PACK-03's `pyproject.toml` dependency lists gain explicit, narrow
dependencies on specific PACK-02 packages (not "the whole services/
directory") — the same shape PACK-02's own `epd2-core` dependency already
has. `tests/repository/test_service_boundaries.py` grows from a
same-pack-only check into a genuinely cross-pack one, which is a real
increase in what that test must express and maintain, but is the only way
INV-03 remains a _tested_ invariant rather than a documented convention
once a real cross-pack dependency exists for the first time. Every
PACK-03 service's own README must document which PACK-02
`application`-layer functions it calls and why, mirroring how PACK-02
services document their own dependency on `epd2_core`/`epd2_audit_core`.

## Security impact

This is the exact boundary CT-00-09 (Vote Linkability) and CT-00-08
(Identity Leakage) depend on holding structurally: `voting-service`
calling `credential-service.application.validate_participation_credential`
(which itself never returns or requires an `account_id`, per PACK-02's
own CT-00-08 guarantee) is safe; `voting-service` importing
`credential-service.storage` directly would risk exposing whatever
internal representation that store happens to use, bypassing the
validated, identity-free application-layer contract entirely. Enumerating
exactly which functions are callable (Decision item 1) is itself a
security control, not just an architectural tidiness preference.

## Data impact

No new canonical entity or field. This ADR does not change any PACK-02
entity, schema, or ownership — it only defines how PACK-03 code may read
PACK-02 state through PACK-02's own already-published interface.

## Migration impact

None — no PACK-03 service exists yet, and no PACK-02 service's public
`application`-layer interface needs to change to satisfy this ADR (the
functions enumerated in Decision item 1 already exist as of PACK-02's own
PASS state).

## Reversibility

Reversible with cost: once PACK-03 services depend on specific PACK-02
`application` functions, changing those functions' signatures becomes a
cross-pack breaking change requiring coordinated updates, the same
reversibility profile any public interface has once it has real callers.
Adopting Option C (a message bus) later remains possible without
reversing this ADR — it would sit underneath these same function calls,
not replace the boundary rule itself.

## Related canon version

Authored against canon version `0.1.0`. Proposes no canon change — INV-03
already requires exactly the boundary this ADR operationalizes; this ADR
only specifies which functions satisfy it for PACK-03's specific
cross-pack reads.
