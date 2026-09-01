# PACK-11 — threat model

> What a governed document register is attacked for, what this round
> defends against, and what it explicitly does not.

## Assets

1. The **authoritative version history** of every governed document.
2. The **content** of documents, at four sensitivity classifications.
3. The **attribution** of every governed act (who recorded, reviewed,
   approved, published).
4. The **determinations** (signature, admissibility) other packs rely on.
5. The **evidence chain of custody**.

## Threats and controls

### T1 — Rewrite history

_An actor edits an approved version to say something else._

Controls: the version hash covers every substantive field; the store
refuses to replace a stored version at all; `record_state_change` compares
`hashable_fields` so a covered field cannot change without resealing; every
command re-verifies the chain before acting.

**Residual:** an actor with write access to the whole store can rewrite
every version and recompute every hash. See "Not defended" below.

### T2 — Remove an inconvenient version

Controls: gap-free numbering is part of chain verification, so a removed
version is detected by the _sequence_ rule even though every remaining
hash is individually correct. An empty version list is explicitly **not**
a valid chain — reporting "valid, length zero" would mean deleting
everything passes the check that exists to detect exactly that.

### T3 — Swap the bytes behind an unchanged record

Controls: `verify_version_content` compares the stored digest against the
actual bytes; `verify_document_integrity` runs it for every version;
`read_document_content` re-verifies before returning, so a caller never
receives content this service cannot show is the content that was
recorded.

### T4 — Graft a forged tail onto a real history

Controls: `previous_version_hash` linkage; the store refuses an append that
would re-parent. Rewriting a version _and_ resealing it does not escape —
the next version still links to the old hash, so the break moves one step
later.

### T5 — Approve or publish one's own document

Controls: the incompatibility matrix (role level) plus
`assert_not_self_approval` (act level). Two layers because the matrix
cannot express "the person who wrote this may not approve it" for role
pairs that are legitimately combinable. An **unrecorded** prior actor is
refused, not passed.

### T6 — Escalate through a stale or newly-conflicting role grant

Control: the matrix is re-checked at the moment of the act over the roles
the actor _actually_ holds now, via `AuthorizationPort.held_roles`. PACK-08's
assignment-time check cannot see a role granted afterwards.

### T7 — Bypass the workflow with a flag or an emergency path

Control: nothing in `authorization` is conditional. `NO_BREAK_GLASS_NOTE`
states the rule; the AST-level test in `test_privacy_boundary.py` enforces
it. A PACK-12 privileged grant can make a caller able to _reach_ a command,
never able to _pass_ one.

### T8 — Exfiltrate content through an event, an audit field or a projection

Controls: one emission chokepoint (`assert_emission_safe`) run by every
event builder and every projection builder over its own output _before_
returning; forbidden content-key names plus a value-level refusal of any
raw byte string whatever its key; `title_reference` instead of `title`;
review _counts_ instead of finding text; a public projection that is a
separate type rather than a filtered variant.

### T9 — Confirm the existence of another organization's documents

Controls: identical not-found error and message shape for "foreign scope"
and "does not exist"; `resolve_document_reference` returns
`exists=False, kind=None` for both; the specific scope-mismatch refusal is
reachable only by a caller that already claimed authority in that scope.

### T10 — Read an unverified pointer as a governed fact

Controls: no reference type carries a status; determinations are recorded
with an authority, a version hash and a reason code; absence is an explicit
`not_determined`; a stale determination is reported as absent rather than
as an answer.

### T11 — Destroy material under legal hold

Controls: `assert_no_destruction_under_hold` refuses under an active hold
and fails closed under an indeterminate one, with distinct codes; there is
no delete method on any port; disposition requires a current PACK-09
authorization; the hold state is re-read rather than cached across acts.

### T12 — Silently retract a publication

Control: a revoked publication becomes a tombstone stating that a
revocation occurred, when, and under which reason code — with no rendition
and no citation.

## Not defended against, and named as such

- **A fully-privileged store operator.** Tamper evidence, not tamper
  resistance (ADR-057). Countersigning and external anchoring of the head
  hash are the controls that would close this, and neither is in this
  round.
- **Content that is malicious as a file** (a weaponised PDF). This service
  stores and hashes bytes; it does not scan them. `FIR-INIT-004`'s
  technical filter is a different component's job.
- **A false determination.** If a legal reviewer records
  `ADMITTED` wrongly, this service records it faithfully. The control is
  the authority model and the audit trail, not a second opinion this
  service is not competent to form.
- **Traffic analysis of the event stream.** Event _types_ and organizational
  scope are visible to any consumer of the stream. A consumer able to read
  it learns that a legal opinion exists in an organization, though not what
  it says or whom it concerns.
- **Anything PACK-12, PACK-13 and PACK-14 own**: privileged access, the
  production data plane, and identity/key management.
