# PACK-12 — Canon Assessment

Specification-only. **The canon is not modified by this round.**
`docs/canonical/TZ-00-domain-event-canon.md` is untouched and
`CANON_VERSION` remains `0.8.0`.

> **Status note added by the PACK-12 implementation candidate round
> (2026-07-29).** The "specification-only / not implemented" statement
> above describes the *specification round* that produced this document
> and is preserved as the historical record. It is no longer the state of
> the repository: `services/privileged-access-service` now implements this
> specification as an **implementation candidate** at repository version
> `0.12.0`.
>
> **LOCAL VERIFICATION INCOMPLETE / EXTERNAL CI PENDING / NOT FINAL PASS.**
> Nothing here is claimed as verified, passed, or production-ready. See
> `docs/handover/PACK-12-IMPLEMENTATION-CANDIDATE-REPORT.md` section 5.


---

## Verdict

# CANON AMENDMENT NOT REQUIRED

---

## 0. Reconciliation basis

This assessment has been reconciled against `EPD2 Architecture Domain
Framework 0.8.2 CORRECTED`, `EPD2 Target Frontend Architecture 0.8.2
CORRECTED`, canon `0.8.0`, the Master Future Implementation Register and
the accepted ADRs of PACK-01 through PACK-11. `OD-P12-01` is closed.

The reconciliation changed three things and left the verdict standing.
Two of the changes strengthen the verdict rather than weakening it:

1. **System Administrator and Security Administrator are existing
   institutional roles in the framework.** The first draft treated them
   as new operational `role_code` values. Correcting that removes two
   roles from PACK-12's introductions — so PACK-12 now introduces nine
   operational assignments rather than eleven roles, and touches the
   institutional layer even less than the first draft claimed.
2. **The framework's canonical classification values are authoritative.**
   The first draft compressed them into four levels. The corrected
   package maps canonical classification to a _derived_ enforcement tier
   and states that the source classification governs — again, less
   assertion of authority by PACK-12, not more.
3. **The voting rule was too broad.** A blanket ban on "tallies" would
   have forbidden publication of a final certified result. The corrected
   rule keeps ballot-level and intermediate/non-certified tally material
   absolutely prohibited and leaves the certified result to the
   authoritative voting and result-certification domain. This restores a
   boundary the framework already draws; it does not create one.

None of the three introduces a system-wide rule absent from the canon.

## 1. What the question actually is

Canon section 25 makes a canon amendment a governed act with its own
version discipline, and canon section 26 requires an ADR for it. The
register's own change discipline adds that an amendment must be a genuinely
new system-wide rule, not a restatement of an existing one at a new level
of detail.

So the test is not "does PACK-12 introduce important rules?" — it plainly
does. The test is: **does PACK-12 introduce a system-wide rule that is
absent from the canon, and that binds every domain rather than PACK-12's
own?**

The answer is no, for the six reasons below.

## 2. The invariants PACK-12 enforces already exist

Every system-wide rule PACK-12 relies on is already in the master
register as an approved invariant. PACK-12 specifies _how_ they are met
in three domains; it does not create them.

| PACK-12 requirement                                                                    | Already-approved source                     |
| -------------------------------------------------------------------------------------- | ------------------------------------------- |
| No universal administration                                                            | `FIR-INV-014`                               |
| Security Admin / System Admin separation                                               | `FIR-INV-008`                               |
| Time-limited, purpose-bound, audited access; break-glass with out-of-band notification | `FIR-INV-009`                               |
| Scoped search and export, reason codes, DLP, rate limits, approval, audit evidence     | `FIR-INV-007`                               |
| Statistical disclosure control for small samples                                       | `FIR-INV-011`                               |
| Bund/Land/Kreis isolation                                                              | `FIR-INV-013`                               |
| Feature flags never disable invariants or separation of duties                         | `FIR-INV-006`                               |
| No global user ID; identity/ballot unlinkability; Voting Client isolation              | `FIR-INV-001`, `FIR-INV-002`, `FIR-INV-003` |
| No false production claims                                                             | `FIR-INV-015`                               |

`FIR-ROADMAP-002` schedules PACK-12 itself, with a scope list that
matches this specification's three domains. A pack implementing its own
scheduled roadmap entry is the ordinary case, and the register's
discipline is explicit that a new PACK does not by itself justify an
amendment.

## 3. The role model uses an extension point the canon already provides

Canon 19e.15 keeps `role_code` an open string, extensible "by
configuration + ADR review". Canon 19e.16 fixes a **minimum** pairwise
incompatibility baseline and states that it may be made stricter and
never relaxed.

PACK-12's eleven privileged role codes are that extension, introduced by
`ADR-061`. PACK-12's fifteen incompatibility pairs make the
baseline stricter, which 19e.16 explicitly permits.

PACK-12 adds **no** new canonically-named institutional role to 19e.16's
seven-role list (`dpo`, `election_board_member`, `election_officer`,
`independent_auditor`, `finance_auditor`, `party_arbitrator`,
`organizational_administrator`). The eleven are operational access roles,
not institutional offices — and this is the same choice PACK-10 made for
its seven finance roles and PACK-11 for its eight document roles, neither
of which triggered an amendment.

## 4. The reason codes follow the PACK-11 precedent exactly

Canon section 24 registers no `PRIVILEGE_*`, `SEARCH_*`, `EXPORT_*` or
`DISCLOSURE_*` code today, and this specification proposes 97 of them.

That looked like an amendment trigger when PACK-11 faced the same
situation, and it was not. `contracts/reason-codes/pack-11.yml` contains
**no** `source: canon-0.8.0` entry at all: canon section 24 registers no
document or evidence code either, and PACK-11 shipped its whole registry
as pack-introduced codes under ADR-004's registry rule. PACK-08, PACK-09
and PACK-07 did the same for their own domains.

Section 24 fixes the _standard_ for reason codes — the required fields,
the prohibition on free-text strings, the additive-only rule. It is not
an exhaustive enumeration of every code the platform may ever hold, and
treating it as one would require a canon amendment for every new
governed refusal in every future pack.

## 5. The events follow canon section 20's convention without changing it

The 44 event types in `PACK-12-EVENT-CATALOG.md` use canon section 21's
envelope unchanged, and canon section 20's aggregate-prefix naming
convention unchanged. `event_version` starts at `1.0`; no envelope field
is added, removed or reinterpreted.

Canon section 20 does enumerate event families per context, and PACK-12's
three contexts are not among them — exactly as PACK-11's document events
were not, and PACK-11 did not amend canon for them. The enumeration grows
when a canon-amendment round adds a context section (as 0.8.0 did for
finance's 19f/20.17); it does not have to grow ahead of the
implementation that will populate it.

## 6. Nothing in PACK-12 binds domains outside PACK-12

The decisive test. A canon amendment is warranted when a rule must be
obeyed by domains that have no other reason to know about it.

PACK-12's rules bind:

- the privileged-administration context it defines;
- the search context it defines;
- the export and disclosure-control context it defines.

Where PACK-12 constrains another domain, it does so by **restating that
domain's own existing rule** — ballot-level and intermediate-tally
material is unreachable because `FIR-INV-002`/`003`/`005` already say so;
the final certified result belongs to the authoritative voting and
result-certification domain because that domain already owns it; a legal
hold does not authorise export because PACK-09 already owns hold
semantics; document bytes stay with PACK-11 because canon 19f.22 already
assigns them there; and the source classification governs because the
framework already makes it authoritative (`P12-CLS-001`). Restating an
existing constraint at a new boundary is specification work, not
constitutional work.

## 7. What would change this verdict

Recorded so a later round can test the question rather than re-argue it.
An amendment **would** be required if the implementation round finds that:

1. a privileged-access or export rule must bind every existing domain's
   own aggregates directly, in a way those domains cannot express through
   their existing authorization ports; or
2. the canonical event envelope (section 21) needs a new field to carry
   purpose, grant reference or session reference — this specification
   assumes it does not, and that assumption is testable at implementation
   time; or
3. the entity-ownership matrix (section 22) must be amended because a
   PACK-12 aggregate turns out to own a concept an existing row already
   assigns elsewhere; or
4. statistical disclosure control requires a platform-wide rule about
   what may be published at all, as opposed to a per-release assessment —
   this is the most plausible future trigger, and it belongs to whichever
   round actually builds the analytics engine, with PACK-13; or
5. a framework rule is found in a later framework revision that is
   genuinely system-wide, genuinely absent from canon, and genuinely not
   covered by the `FIR-INV-*` register entries in section 2. The
   reconciliation performed for this corrected package found no such
   rule; a future framework revision could introduce one.

The reconciliation input for items 1–5 was the Architecture Framework
0.8.2 CORRECTED content supplied by the framework owner as part of the
correction instruction for this package, together with canon 0.8.0, the
Master Future Implementation Register and the accepted ADRs of PACK-01
through PACK-11. Where a later reader has the framework document itself
to hand, sections 3, 6 and 8.0 of the specification are the places to
check first, because they are where PACK-12 touches framework-owned
definitions most closely.

## 8. Consequence for this round

No canon file is touched. `CANON_VERSION` stays `0.8.0`.
`REPOSITORY_VERSION` stays `0.11.0`. No `docs/canonical/` file, no
`canon-version.json` field and no version constant is modified by the
PACK-12 specification round.
