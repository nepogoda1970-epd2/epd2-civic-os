# PACK-14 — Canon Assessment

**Round:** PACK-14 — specification and ADR only. **No code. Not implemented. Not a candidate. Not a PASS.**
**Repository version:** unchanged at `0.13.0` · **Canon version:** unchanged at `0.8.0`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**
**Architecture correction applied (2026-07-30).**

## Verdict

```text
CANON AMENDMENT NOT REQUIRED
```

`CANON_VERSION` remains `0.8.0`. `docs/canonical/TZ-00-domain-event-canon.md`
is not modified by this round.

## Why — the reasoning, not the conclusion

A canon amendment is required when a round needs a concept the canon does
not have, or needs to change the meaning of one it does. PACK-14 needs
neither, and the reason is that canon 0.6.0–0.8.0 already did this work.

### 1. The assurance vocabulary already exists

Canon 19d.2 fixes `identity_assurance_level` and canon 19d.8 fixes
`authentication_assurance_level`, both on the same four values —
`none` / `low` / `substantial` / `high` — and both explicitly non-
interchangeable. The obvious temptation for an identity pack is to
introduce an AAL-0…AAL-3 scale of its own because that vocabulary is
familiar from external standards. **PACK-14 does not**: it maps the
informal names onto canon's existing values (specification §6) and adds no
enum. A second scale would have been a canon change disguised as a
convenience.

### 2. The five separations already exist

Canon 19d.8 names **five never-interchangeable concepts**: identity
assurance, authentication assurance, attribute freshness, session
authentication time and method, and provider reference. Every separation
PACK-14 needs is one of these or follows from them.

### 3. Step-up policy already has an owner and an evaluation rule

`StepUpAuthenticationRequirement` exists in canon 19d.8, is owned by
`eligibility-service`, and is already evaluated **fail-closed** as a
conjunction with no "or" permitted. PACK-14's action-binding and
object-version-binding rules are constraints on _how a requirement is
satisfied_, not new canonical entities.

### 4. `Account`, `IdentityRecord` and `AuthenticationContext` already exist

Canon 7.2 defines `Account` as a **technical** account with six statuses;
canon 7.3/19d.2 defines `IdentityRecord` with its ownership and its
prohibition on using verification as a proxy for citizenship; canon 19d.8
defines `AuthenticationContext`. PACK-14 extends operational detail around
them and redefines none of them.

### 5. The membership boundary already exists

Canon 19d.9's two-stage admission — formal eligibility evaluation, then an
authorized human decision — is exactly the boundary PACK-14 must not
cross, and PACK-14 adds no path around it.

## What would have required an amendment, and was avoided

| Tempting move                                                                          | Why it would have amended canon         | What PACK-14 does instead                                                                                 |
| -------------------------------------------------------------------------------------- | --------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| A new AAL-0…AAL-3 enum                                                                 | A second assurance scale beside canon's | Maps onto canon's four values                                                                             |
| Adding `locked`, `closure_pending`, `deleted_or_anonymized` to canon 7.2's status list | Changes a canonical enumeration         | Records them as specification-level operational states and defers the canonical question to **OD-P14-01** |
| A canonical `Session` entity                                                           | Adds a canonical aggregate              | Specifies the session model at pack level; whether it becomes canonical is **OD-P14-05**                  |
| Redefining `AuthenticationContext` to hold session state                               | Changes an existing entity's meaning    | Keeps 19d.8's entity as-is and models sessions beside it                                                  |
| A canonical global identity mapping table                                              | Directly contradicts `FIR-INV-001`      | Governed mapping boundaries with purpose, scope, owner, policy, retention and evidence                    |

## The three canonical questions are now closed — still without an amendment

| Question                                                                    | Decision                                                                                                                                                            | Canon effect                                            |
| --------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------- |
| **OD-P14-01** — do the three additional account states belong in canon 7.2? | **No.** They are not states at all: `AccountLock`, a security-class `AccountRestriction`, `AccountClosureRequest` state, and lifecycle outcomes with their events   | **None.** Canon 7.2's six values stand unchanged        |
| **OD-P14-05** — does the session model belong in canon?                     | **No.** `SessionRecord` is a service-level aggregate, following PACK-12's `PrivilegedSession`                                                                       | **None.** Its events use canon §21's envelope unchanged |
| **OD-P14-06** — should the voting handoff acquire a canonical form?         | **No, not from here.** PACK-14 defines the outbound boundary; the artifact's canonical treatment, if it ever needs one, belongs to PACK-15/16 with the threat model | **None**                                                |

The architecture correction closed nine of the ten open decisions and
**strengthened** this verdict rather than weakening it: each closure was
resolved in the direction that needs no canon change, and that was a
selection criterion rather than a coincidence. Extending
`AccountStatus`, canonising `SessionRecord` or fixing a canonical handoff
form would each have required an amendment; none was necessary to make the
architecture implementable.

**OD-P14-07 (retention periods) remains open** and is not a canonical
question — PACK-09 owns retention schedules, and a schedule is a legal
determination rather than a canonical structure.

**This round amends nothing.**
