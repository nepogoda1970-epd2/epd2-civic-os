# ADR-056: Document authority separation, the incompatibility matrix and access profiles

## Status

`proposed`

## Date

2026-07-28

## Context

A governed document register concentrates two powers that are ordinarily
separate: the power to decide what a record says, and the power to decide
who sees it. `FIR-INV-006` forbids feature flags that disable separation
of duties, `FIR-INV-014` forbids a universal administration panel, and
`FIR-INV-013` requires organizational scope isolation from the beginning
of the data model. PACK-08 owns the authority assignments themselves and
enforces its incompatibility matrix at assignment time.

## Problem

1. PACK-08's assignment-time check is necessary and not sufficient. An
   actor whose two roles were compatible when granted can acquire a
   conflicting one afterwards, and the act happens later.
2. A role-level matrix alone cannot express "the person who wrote this may
   not approve it" in an organization where one person legitimately holds
   both a custodial and an approving role.
3. Without an explicit access model, "can read a document" would collapse
   into "has an authority", and a document classified `restricted` would
   be readable by anybody with any document role.

## Decision

**1. Eight institutional roles, not more**: `document_custodian`,
`document_author`, `document_reviewer`, `document_approver`,
`legal_reviewer`, `publication_officer`, `evidence_custodian`,
`independent_reader`. Every additional privileged role widens the
platform's privileged surface, and the twenty-one governed actions
decompose cleanly into these eight.

**2. A symmetric incompatibility matrix, derived rather than written
out per role.** `incompatible_roles_for` computes from an unordered set
of pairs, so the matrix cannot become asymmetric through an edit that
updates one direction and forgets the other - a bug that would otherwise
only appear when the roles were granted in the other order.

**3. The matrix is re-checked at the moment of the act**, over the roles
the acting actor *actually* holds in that scope, obtained through
`AuthorizationPort.held_roles`. This is the check PACK-08 structurally
cannot perform on PACK-11's behalf.

**4. Separation of duties is enforced per act, not per role set.**
`assert_not_self_approval` compares the opaque `actor_reference` on the
current act against every prior act the command names. An unrecorded
prior actor is **refused**, not passed: an act whose prior actor was not
recorded cannot be shown to involve a different person, and this check
exists precisely to stop "cannot be shown" from being read as "is".

**5. Two independent layers, and the order is deliberate.** The matrix
fires first and denies a whole class of act; separation fires second, for
role pairs that are legitimately combinable. `document_custodian` +
`document_approver` and `document_approver` + `publication_officer` are
both legal role sets, and both are still refused per act when one actor
performs both halves.

**6. Access is a ceiling, and a missing profile denies.** `AccessProfile`
names a `max_sensitivity`, a scope and a purpose. Holding one does not
grant a read - it bounds a read that also passes the authority check. Two
independent conditions, so neither alone suffices. `None` denies: the
caller who forgot to present a profile is indistinguishable from the
caller who has none.

**7. Independence is re-verified at read time.** An `independent_reader`
who has since acquired an operational role is no longer independent, and
the grant does not know that.

**8. There is no break-glass.** `NO_BREAK_GLASS_NOTE` states the rule as a
quotable module constant. No `force=`, no `skip_checks`, no environment
switch, no privileged-caller shortcut, and none may be added. PACK-12 will
own privileged access, and a PACK-12 grant can make a caller able to
*reach* a document command, never able to *pass* one.

## Consequences

Reaching the public takes three distinct actors: author, approver,
publication officer. A small organization can legally combine some roles
and still cannot short-circuit the workflow, because the per-act check
does not care how many hats one person wears.

`tests/test_privacy_boundary.py` enforces the no-break-glass rule over the
parsed AST rather than the raw text, so `NO_BREAK_GLASS_NOTE` - which
*names* those switches in order to forbid them - does not trip its own
test.

## Alternatives considered

**Role matrix only.** Rejected: cannot express per-act separation.

**Per-act separation only.** Rejected: would permit one actor to hold
author, reviewer and approver and simply use three sessions.

**Treat a missing access profile as ordinary internal access.** Rejected:
the most likely caller to omit it is the one who should not have it.

## Security impact

The act-time re-check is the control that survives a compromised or
mis-sequenced assignment process. The refusal of unverifiable separation
is the control that survives an incomplete audit trail.
