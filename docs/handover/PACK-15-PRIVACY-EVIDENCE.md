# PACK-15 — Privacy evidence

```text
PACK-15 FINAL PASS
REPOSITORY_VERSION 0.15.0
CANON_VERSION 0.8.0
EXTERNAL CI PASS
HYGIENE CORRECTION VERIFIED
NOT PRODUCTION READY
NOT LEGALLY ACTIVATED
```

The privacy claim of this pack is narrow and should be stated exactly:

> **No component in this repository can answer the question "did this
> person vote".**

Not "no component is permitted to". Not "no component currently does".
The claim is that the data required to answer it is not co-located in any
store, log, event, response or export, and that no join path exists to
bring it together - so an operator with a SQL prompt, a backup tape and a
court order cannot answer it either.

This document records how that claim is made structural, and where it
stops.

---

## 1. The chain, and where each link is cut

The question decomposes into a four-link chain:

```
person -> eligibility assertion -> voting credential -> ballot
```

| Link                      | How it is cut                                                                                                                                                                                                                                                                                                                                              | Where                                                                                |
| ------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| `person -> assertion`     | The assertion carries twelve fields and none of them identifies anyone. The participation-unit ledger records **that** an assertion was minted for a unit, never **which** assertion - there is no `assertion_id` column in that table, and adding one would be the pairing ADR-093 forbids.                                                               | `voting_eligibility.ASSERTION_FIELD_NAMES`; `eligibility/0001_eligibility_cases.sql` |
| `assertion -> credential` | The spent-nonce record is a **set**: three columns, no value column, no room for a credential reference beside the nonce. The bounded idempotency window is the only place the two ever coexist, it lives in memory-equivalent storage for at most 900 seconds, and `CredentialIssuanceIdempotencyRecord.assert_not_durable` refuses to make it permanent. | `0002_spent_nonce_set.sql`; `voting_credentials.py`                                  |
| `credential -> ballot`    | Out of scope for this pack by construction: `credential-service` has no ballot store, no ballot column and no read edge to one. Redemption returns a continuation capability to the caller in the moment and stores it as `withheld`.                                                                                                                      | `voting_credential_sql_storage.SqlCredentialRedemptionStore`                         |
| the whole chain           | The four boundaries are **separate SQLite database files**, so a foreign key between them is not expressible and a JOIN has no syntax. This is not a discipline anyone has to keep.                                                                                                                                                                        | four migration sets                                                                  |

The most important sentence in this section is the last one. Every
guarantee above could have been implemented as a rule in application code.
Rules in application code survive exactly as long as the next person who
needs a number in a hurry.

---

## 2. Data minimization at the crossing

The only artefact that crosses the trust boundary is the eligibility
assertion. It has a **closed twelve-field list** (ADR-091), and the list
is enforced rather than documented: `EligibilityAssertion.wire_payload()`
constructs exactly those twelve keys, and `assert_no_forbidden_fields`
scans the result.

The Assertion Issuer's input is smaller still.
`MinimizedDecisionInput` has **five** fields, and there is no field on it
for a participant, a case, a criterion input, a reason history or an
evidence reference. The issuer cannot receive one, because the type has
nowhere to put it.

What the voting side therefore knows about a participation: the context,
an eligibility class, an organizational scope, whether the assurance
requirement was met, a coarsened issuance time, an expiry, an audience, a
purpose and a one-time nonce. What it does not know: everything else.

---

## 3. The timing channel

Structural unlinkability does not survive a timing correlation. If an
assertion is minted at 14:03:11 and a credential at 14:03:14, and the
electorate is small and the hour quiet, the two records are plausibly the
same participation regardless of what the schema permits.

`OD-P15-02` bounds that channel with nine governed controls, each with a
reference default, a permitted range and a **hard floor configuration
cannot go below**:

| Control                    |    Default | Hard floor |
| -------------------------- | ---------: | ---------: |
| Timestamp granularity      |      300 s |       60 s |
| Release delay (min / max)  | 30 / 300 s |  10 / 60 s |
| Batch interval             |      120 s |       60 s |
| Batch maximum size         |        250 |         50 |
| Minimum cohort             |          5 |          3 |
| Cohort wait maximum        |     3600 s |      600 s |
| Minting delay (min / max)  |   5 / 30 s |   2 / 10 s |
| Small-electorate threshold |         50 |         20 |
| Disclosure minimum cell    |          5 |          5 |

A value outside its range is refused with
`TIMING_PROFILE_OUT_OF_BOUNDS`, **never clamped silently**. A silently
clamped privacy control is a disabled privacy control that still reports
as enabled.

Two properties of this design are worth stating because they pull in
opposite directions and the resolution matters:

- **A cohort of one is never released early.** It waits for others.
- **Access is never denied for want of a cohort.** At the cohort-wait
  deadline the assertion is released anyway, and the exception is
  recorded with the cohort-size _class_.

Disenfranchising a participant in order to protect that participant's own
unlinkability is not a trade this system makes. The privacy loss is
recorded instead of being silently taken or silently avoided.

Cohort sizes are reported as classes (`single`, `below_minimum`,
`at_minimum`, `above_minimum`) and never as numbers, because an exact
cohort size in a small electorate is itself a participation statement.

---

## 4. What may never be said

Two reason codes are **deliberately absent from the registry and may
never be added**: `ALREADY_VOTED` and `PARTICIPATION_CONFIRMED`.

To emit either, some component would have to know that a particular
participant's credential was redeemed - which is precisely the linkage
this pack removes. A code that cannot be emitted truthfully is not a
missing feature; it is a claim the architecture is built to be unable to
make.

The nearest permissible codes are `CREDENTIAL_ALREADY_ISSUED` (identity
side, about issuance) and `CREDENTIAL_ALREADY_REDEEMED` (voting side,
about a credential the presenter is holding). Neither says a person voted.

The registry file records this prohibition in its own header, so a future
contributor reading it before adding a code encounters the reason rather
than the rule alone.

---

## 5. Person-level status is not offered anywhere

| Surface                 | What it will answer                                                     | What it will not                                                                                                                                                                     |
| ----------------------- | ----------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `credential.status`     | The status class of a credential reference **the caller already holds** | Anything keyed on a person; and an unknown reference returns the same shape as a withdrawn one, so it is not an existence oracle                                                     |
| `eligibility.case.read` | The case's own status and a decision count                              | Nothing about a credential or a ballot - this side holds no such value                                                                                                               |
| `evidence.stream.read`  | One stream, for one context                                             | Any request naming both an identity-side and a voting-side stream is refused by `assert_streams_separable`                                                                           |
| Evidence bundles        | Eight sections of aggregates                                            | Fifteen forbidden keys, scanned at every nesting depth; cells below the disclosure floor are suppressed **complementarily**, so a suppressed cell cannot be recovered by subtraction |

There is no search endpoint on the voting side. Not a restricted one - none.

---

## 6. Retention and deletion

| Class                     | Where                                                 | Note                                                                                                                                                          |
| ------------------------- | ----------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Eligibility case          | `eligibility_case.retention_class`, with `legal_hold` | Identity-side, identified, and governed by the existing PACK-11/PACK-12 retention machinery                                                                   |
| Assertion and queue entry | Assertion-issuer database                             | Carries no participant reference, so its retention is not a personal-data question at all                                                                     |
| Spent nonce               | Voting-side database                                  | Must outlive the voting window: deleting it would re-enable a second issuance for a nonce already used                                                        |
| Idempotency record        | Voting-side database                                  | Bounded to 900 seconds and purgeable; this is the only record that pairs an assertion nonce with a credential, and it is the one record designed to disappear |
| Audit records             | Three separate audit databases                        | Per-stream `retention_class` and `legal_hold` columns                                                                                                         |

The asymmetry in that table is deliberate and is the honest cost of the
design: the spent-nonce set must be kept, and the idempotency record must
not be. Getting those two backwards would either allow double issuance or
create a durable assertion-to-credential map.

---

## 7. What this pack does **not** protect against

Stated plainly, because a privacy document that lists only its successes
is a marketing document:

1. **Traffic analysis at the network layer.** If an observer can watch
   both origins and correlate TLS sessions, the timing controls above do
   not help. Mitigating that needs infrastructure this repository does
   not own.
2. **A compromised voting client.** Everything here assumes the isolated
   voting origin is not itself hostile. A malicious client sees the
   credential and the ballot together, by necessity.
3. **A participant who tells someone.** Coercion resistance is not
   claimed and is not implemented. This pack makes the _system_ unable to
   answer the question; it does not make the _participant_ unable to.
4. **Correlation from data outside this system.** If an external register
   records who requested eligibility and an external log records who
   opened the voting origin, the two together are a correlation this
   repository never sees and cannot prevent.
5. **Statistical inference on very small electorates.** The disclosure
   floor of five and the small-electorate hardening reduce this; they do
   not eliminate it. In an electorate of six, aggregate figures are close
   to individual ones no matter how they are suppressed.

---

## 8. Verification status of the claims in this document

Every structural claim above is asserted by an executed test - see
`PACK-15-TEST-EVIDENCE.md` section 5 for the property-to-module mapping
and section 3 for the counts (434 PACK-15 tests, all passing under real
`pytest`).

The claims that are **not** verified by execution in this round are the
frontend ones: the isolated voting origin, its content and its
accessibility behaviour exist as source and have never been rendered
here. Nothing in section 5 of this document depends on that code, but the
participant-facing half of the privacy story does, and it remains
unverified until external CI runs.

---

## External verification — the authoritative run

GitHub Actions has run against the cleaned tree and **passed every
stage**. This section records that run; the local results elsewhere in
this document are what preceded it and are not a substitute for it.

| Stage                            | Result                        |
| -------------------------------- | ----------------------------- |
| Required paths                   | PASS — 983 / 983              |
| Forbidden paths                  | PASS                          |
| Version consistency              | PASS — `0.15.0` / `0.8.0`     |
| Ruff format                      | PASS — **436 files**          |
| Prettier                         | PASS                          |
| Ruff lint                        | PASS                          |
| ESLint                           | PASS                          |
| mypy                             | PASS                          |
| Python tests                     | PASS — 5343 passed, 4 skipped |
| TypeScript package tests         | PASS — 3 passed               |
| Node tests                       | PASS — 41 passed              |
| Frontend tests                   | PASS — 23 passed              |
| Next.js production build         | PASS                          |
| Static pages                     | 48 / 48                       |
| Browser / visual / accessibility | PASS — 135 passed             |

**Verification artifact SHA-256**
`e8fd5b2a14e61be95be49afd461467a9ddbaab8f5dc70db68a9ab5f0bb9cd1b4`
**Internal verification ZIP SHA-256**
`7ea70c5b9ba3c7350e1d0831148c2be560512e17f78392031c1b0e5e7ea3df8c`

Both were recomputed from the supplied files and both matched.

**`Ruff format: 436 files` is the number that matters.** The previous
external run reported 609, because the tree it verified still contained
`epd2-civic-os/`, a stale nested copy of the repository at `0.6.0`. That
directory has been removed and the tree re-verified from scratch. **Every
verification artifact for a tree containing it is superseded and is not
FINAL PASS evidence.**

The verified tree was compared file by file against the archive shipped
here: 1171 source files, zero differences. The artifact additionally
contains 753 files that the run itself produced — `__pycache__`,
`.hypothesis`, tool caches, Playwright output, a `tsbuildinfo` and five
root scratch files — none of which are part of this archive.
