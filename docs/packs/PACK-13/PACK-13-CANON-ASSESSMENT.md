# PACK-13 — Canon Assessment

Specification-only. **The canon is not modified by this round.**

---

## Verdict

```text
CANON AMENDMENT NOT REQUIRED
```

`CANON_VERSION` stays `0.8.0`. `docs/canonical/TZ-00-domain-event-canon.md`
is untouched by this round and must not be edited by the implementation
round either, unless a later assessment reverses this verdict with its own
evidence.

---

## 1. How the verdict was reached

The question is not "does PACK-13 introduce new concepts" — it plainly
does — but "does PACK-13 require the canon to say something it does not
already say, or to stop saying something it does".

Four tests were applied to every PACK-13 concept:

1. **Does it change the canonical domain model?** A new _entity_ in the
   canonical sense — one that domains reason about and events describe.
2. **Does it change the event envelope?** Canon §21.
3. **Does it change event naming or the event inventory?** Canon §20.
4. **Does it change a registered reason code's meaning, or the ownership
   matrix?** Canon §22, §24.

A concept that fails all four is infrastructure, and infrastructure does
not belong in a domain canon.

---

## 2. Concept-by-concept assessment

| Concept                                    | Changes domain model?                                                 | Changes envelope?                         | Changes naming/inventory?                       | Changes §22/§24 meaning?            | Verdict                     |
| ------------------------------------------ | --------------------------------------------------------------------- | ----------------------------------------- | ----------------------------------------------- | ----------------------------------- | --------------------------- |
| Transactional outbox                       | no — a persistence mechanism for events the canon already defines     | **no** — envelope used unchanged          | no — publishes existing events                  | no                                  | infrastructure              |
| At-least-once delivery                     | no — a transport property                                             | no                                        | no                                              | no                                  | infrastructure              |
| Consumer idempotency                       | no                                                                    | no                                        | no                                              | no                                  | infrastructure              |
| Aggregate version / optimistic concurrency | no — an existing implementation practice since PACK-02                | no                                        | no                                              | no                                  | infrastructure              |
| Schema registry                            | **no — and this is the important one** (see §3)                       | no                                        | no                                              | no                                  | infrastructure              |
| Compatibility modes                        | no                                                                    | no                                        | no                                              | no                                  | infrastructure              |
| API / event contract evolution             | no                                                                    | no — versions are already envelope fields | no — names are stable by requirement            | no                                  | infrastructure              |
| Migration discipline                       | no                                                                    | no                                        | no                                              | no                                  | infrastructure              |
| Projections and read models                | no — explicitly non-authoritative                                     | no                                        | no                                              | no                                  | infrastructure              |
| Data ownership matrix                      | **no** — it _restates_ canon §22's ownership at the persistence layer | no                                        | no                                              | **no — it must not contradict §22** | infrastructure, constrained |
| PACK-13's 37 events                        | no                                                                    | **no**                                    | **adds events, does not change the convention** | no                                  | see §4                      |
| PACK-13's reason codes                     | no                                                                    | no                                        | no                                              | **no — additive only**              | see §5                      |

---

## 3. Why the schema registry is not a canon change

This is the concept most likely to be mistaken for one, so the reasoning
is set out rather than asserted.

The registry records **artifacts** — JSON Schema files, OpenAPI documents,
migration metadata — and their lifecycle. The canon records **meaning** —
what a `Membership` is, what an event envelope contains, which context owns
which entity.

They are different objects, and `P13-REG-002` states the precedence
explicitly: **where the registry and the canon disagree, the canon
governs**, and the disagreement is a defect to be fixed rather than a
conflict to be arbitrated. A registry that could override the canon would
indeed be a canon amendment — by creating a second normative authority. The
specification forbids exactly that.

The consistency check in the handover report tests this: _"schema registry
does not become a new canon"_.

---

## 4. Why 37 new events are not a canon change

Canon §20 defines the **convention** (aggregate-prefixed names) and §21 the
**envelope**. PACK-13 adds events that obey both without altering either —
exactly as PACK-09 through PACK-12 each did. Canon §20's inventory has been
extended by every implementing pack without amendment, because extending an
inventory under an unchanged convention is what the convention is for.

Two properties make this safe, and both are requirements:

- `P13-EVT-001` — the envelope is used unchanged;
- `P13-EVT-002` — names carry the aggregate prefix, never a pack prefix.

Had PACK-13 needed a new envelope field — a delivery attempt count, a
broker reference, a schema digest — the verdict would be different. It does
not: those live in the outbox record and the delivery evidence, which are
persistence structures, not envelope fields. **Keeping transport metadata
out of the domain envelope is the specific decision that keeps this round
canon-neutral**, and ADR-071 records it.

---

## 5. Why the reason codes are not a canon change

Canon §24 registers reason codes and is refusal-only. PACK-13's codes are:

- **additive** — no existing code changes meaning (`P13-RSN-004`);
- **prefixed by family** — no collision with an existing code;
- **owned by PACK-13's contexts** — registered in a separate
  `contracts/reason-codes/pack-13.yml` at implementation time, following
  the ADR-006 Option B precedent that PACK-07 through PACK-12 all used.

This is the same treatment PACK-11 and PACK-12 received, neither of which
amended the canon.

---

## 6. What _would_ require an amendment

Recorded so that a future round recognises the trigger rather than
rediscovering the question:

| If a future round needed to…                               | Then                                                   |
| ---------------------------------------------------------- | ------------------------------------------------------ |
| add, remove or reinterpret an **envelope** field           | **amendment required** (canon §21)                     |
| change the **event naming convention**                     | amendment required (canon §20)                         |
| change **which context owns which entity**                 | amendment required (canon §22)                         |
| change the **meaning of a registered reason code**         | amendment required (canon §24)                         |
| make the schema registry **authoritative over the canon**  | amendment required — and should be refused             |
| introduce a **canonical identifier spanning domains**      | amendment required — and is forbidden by `FIR-INV-001` |
| record **delivery or transport state inside the envelope** | amendment required — and ADR-071 chooses not to        |

---

## 6a. Why the three corrections do not disturb the verdict

The corrected package narrows three claims and separates one conflated
pair. All four movements are **away** from canonical territory, not toward
it:

1. **Reserved future ownership boundaries.** PACK-13 previously read as
   though it assigned production ownership to services for identity,
   eligibility, credential, voting and tally. It now assigns none, and
   defers each to PACK-14 or PACK-15/16. Canon §22 rows for those contexts
   are untouched either way — but the corrected version is the one that is
   honest about who decides.
2. **Audit ingestion.** Resolving "only the owner writes" against "every
   domain appends to audit" **confirms** the canon §22 ownership assignment
   rather than qualifying it: `audit-core` owns persistence, and submission
   through a governed port is not an ownership exception. Had the
   contradiction been resolved the other way — by granting write access —
   _that_ would have required an amendment, because it would have changed
   what §22's ownership means.
3. **Voting topology.** PACK-13 no longer prescribes broker topics,
   deployment separation, connection or credential topology, or service
   names for the voting domain. It keeps only the general data-plane
   constraints, which restate existing invariants (`FIR-INV-002`,
   `FIR-INV-005`). Removing a prescription cannot create a canon
   requirement.
4. **Digest and version identity.** Both `content_digest` and
   `schema_version_id` are registry fields. Neither is a canonical entity,
   neither appears in the envelope, and separating them changes no event
   name and no registered code's meaning. It removes a claim the registry
   should never have made — a universal semantic-equivalence proof — which
   is a reduction in scope, not an extension.

The four tests in §1 therefore return the same answers they did before, and
for the same reasons.

---

## 7. Statement

PACK-13 concretises, at the level of specification and ADR, mechanisms the
Architecture Framework and the Master Future Implementation Register
already anticipate: a schema registry, contract evolution, idempotency,
migration discipline, and outbox and event semantics. Anticipated
mechanisms implemented within existing canonical conventions do not amend
the canon.

```text
CANON AMENDMENT NOT REQUIRED
```

The canon file itself is not modified by this round, and no PACK-13
document proposes an edit to it.
