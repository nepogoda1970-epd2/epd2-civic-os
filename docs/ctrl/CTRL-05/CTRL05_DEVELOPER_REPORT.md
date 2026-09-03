# CTRL-05 — Developer Report

**Stage:** `CTRL-05 — Audit & Oversight Console`
**Mode:** `PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED`
**Self-state:** `CANDIDATE_NOT_ACCEPTED`
**Date:** 2026-09-03

This report claims no CTRL-05 acceptance, no CTRL-layer closure, no production
readiness, no legal activation, no final security acceptance and no BSI or
Common Criteria certification. The developer emits only a PRESEAL marker.

## 1. Bootstrap

Fresh clone of canonical `main`:

| Field | Value |
| --- | --- |
| repository | `nepogoda1970-epd2/epd2-civic-os` |
| commit | `2ceb77be91448462262b84f278a00cfe6dd4228e` |
| tree | `ec057046e235bbd438a4aaa1a23e9f40dff804a2` |

Read in order: `EPD2_PROJECT_ENTRYPOINT.md`,
`EPD2_PROGRAM_CONTROL_REGISTER.md` (state: `CTRL-01/02/03/04 ACCEPTED /
CLOSED; CTRL LAYER OPEN`), the relevant Master Register sections, the CTRL-01
specification, the CTRL-02/03 acceptance records, the CTRL-04 stage contract,
specification, acceptance record and canonical installation manifest, and the
INFRA-01/02/03 and OPS-01/02 acceptance records. The starter ZIP was treated
as the assignment, not as a baseline.

The pre-existing control-plane suite reproduced at `384 passed` before any
CTRL-05 file was added.

## 2. What was built

| Item | Count / fact |
| --- | --- |
| governed actions | 14 (5 read, 9 mutating) |
| typed records | 28 frozen dataclasses |
| rights | `AUDIT.READ / CORRELATE / REVIEW / ATTEST / EXPORT`, each backed by its own live CTRL-02 grant |
| policy obligations | 28 explicit switches, all enforced; `OversightPolicy.governed()` only |
| refusal reason codes | 49 |
| evidence planes | CTRL-02, CTRL-03, CTRL-04 — the real installed runtimes, read in process |
| HTTP routes | 11 read (incl. UI and catalogue), 12 acts; 10 explicitly absent surfaces |
| CTRL-05 tests | 213 (cumulative suite 597 passed, 0 failed, 0 skipped) |
| gates | 56/56 PASS, every gate an executed probe |
| mutation fixtures | 52/52 DETECTED |
| E2E journeys | J01–J22, 22/22 PASS over real HTTP |
| browser journeys | B01–B05, 5/5 PASS in Chromium (screenshots in `validation/ctrl05/browser/`) |

Detail is in `CTRL05_SPECIFICATION.md`; the contract is
`contracts/control/ctrl05_oversight_console.json`.

## 3. Design decisions worth flagging

**The evidence is real, in a way CTRL-04's could not be.** CTRL-04 had to bind
OPS/INFRA by accepted identity because their runtimes are not installed on
`main`. CTRL-05's dependencies *are* installed: the CTRL-02, CTRL-03 and
CTRL-04 runtimes live in this repository. So the journeys perform a real
CTRL-02 intervention (requested, approved twice, activated), a real CTRL-03
JWS signing-key revocation (security and trust-custodian approval, executed),
and real CTRL-04 service-restart actions through
request/approve/commit/resolve — and then read the hash-chained records those
operations actually produced. The evidence class is
`REAL_INSTALLED_CTRL02_CTRL03_CTRL04_PLANES`. Nothing about an evidence plane
is mocked.

**Competence is per-right, not per-role.** A mandate binds *each* right to its
own CTRL-02 grant (`authority_bindings`). This was a deliberate correction:
one grant per mandate could not express "may read and review here, but not
export", and it made "the authority behind this act" ambiguous. A right with
no binding cannot be constructed at all.

**Unit scope is a full scope key.** Evidence streams are assigned to
`region:org:unit`, not to a bare unit label. The first implementation used the
label, and two organizations that happen to name their oversight unit
identically could then see each other's unscoped evidence. That is fixed and
gate G27 proves it with two same-named units in different organizations.

**Every containment failure has its own code.** "Not your organization", "not
your unit", "not your plane" and "voting boundary" are four different
governance facts, and a reviewer who is refused must be able to tell which.

**The frontend renders; it never decides.** The page greys controls from the
mandate it was told about, but every act and every integrity verdict is
re-derived server-side, 32 client-supplied authoritative fields are refused on
presence, and every server value is HTML-escaped at ingestion.

**Voting evidence exists in the test world on purpose.** CTRL-04 refuses an
operation on a voting-domain target and journals the refusal. That real record
is in the plane CTRL-05 reads, so the voting boundary is exercised against an
actual envelope. Before this, the boundary was unreachable code.

## 4. Independent adversarial review, and what it found

The first candidate was put through an adversarial review whose brief was to
find places where the implementation is weaker than it appears. It found ten
real defects; an eleventh surfaced while writing the regression tests for
them. They are recorded here, with their resolution, because a reviewer should
know that a first pass produced them. Each fix carries a test in
`tests/test_ctrl05_hardening.py` that reproduces the defect.

| # | Finding | Why it mattered | Resolution |
| --- | --- | --- | --- |
| 1 | `/audit/v1/cases`, `/audit/v1/cases/<id>` and `/audit/v1/read-model` checked only that a session existed, then returned **every** case in every organization and unit — titles, dispositions, finding summaries, attestation statements, evidence hashes and the governed evidence-unit map. A principal with no mandate at all got full oversight visibility. | Hard boundaries 1 and 2 held for `search` only; the whole read-route family was unscoped and untested. | Governed read entry points (`governed_cases`, `governed_case`, `governed_read_model`, `governed_exports`) resolve the exact mandate from a scope named in the query string and filter every collection; a case outside the mandate is reported *unknown*, not *forbidden*. The projections that take no actor are now documented as in-process only. |
| 2 | `action_chain` filtered the chain by visibility but fetched the composed CTRL-04 action record by correlation id alone. A legitimately scoped Bavarian reviewer, naming a Berlin action id, got 0 visible steps *and* the full record — executor, target, authority decisions. Action ids are sequential, so this was enumerable. | Cross-organization dump of another region's operational history, and a voting-boundary bypass. | The composed record is gated by the same `_visibility_refusal` as the chain: no visible step, no record. |
| 3 | `_verify_state_against_journal` compared only record *counts*. A CRITICAL finding could be downgraded to INFORMATIONAL, its summary rewritten, its authorship changed and the case moved into another oversight unit — with a valid keyed seal. | Boundary 8, and the module's own claim that the tables must agree with the journal. | Every governed act now journals a `content_digest` over its substance, and restore matches each case, disposition, finding and attestation to its own record by id and re-derives that digest. Seven reproducing tests. |
| 4 | The idempotency short-circuit ran *before* session, CSRF, mandate and ticket checks, and appended nothing. A revoked session with a superseded mandate and no CSRF token still received the object its earlier self produced. A replayed dispute returned the same finding twice. | Boundary 9 and 10: a governed act returned data with no live authority and left no evidence. | `_replay` re-checks session, CSRF token and the live mandate carrying the right, journals the retry as `REPLAYED`, and for ticket acts still requires a real ticket. The dispute replay returns the original and its dispute. |
| 5 | `case = self._case(...)` sat outside the guarded block in four methods, and `_time` raised directly, so `AUD_UNKNOWN_CASE` and **every** clock rollback left no journal record. | "Every refusal is evidence-bearing" was false for the attempt one most wants recorded. | The lookups moved inside the guarded block, refusal handlers no longer depend on the unresolved case, and a rollback goes through `_refuse` before raising. |
| 6 | `correlation_graph` discarded the unavailability map and never consulted `fail_closed_on_source_unavailable`: with two planes down it returned an empty graph indistinguishable from "no correlated evidence". | Boundary 10. `search` and `action_chain` failed closed; the graph failed open. | It now refuses `AUD_SOURCE_UNAVAILABLE`. |
| 7 | `remediation_plane` was the one governed free-text field never scrubbed, and reached `case_view` — the API route and the UI's data source — verbatim, while the journal and read model were clean. The surfaces disagreeing was itself the proof. | Boundary 3. The secret sweeps in the tests and in J19 never injected a secret into a governed field, so they could not fail. | The field is scrubbed and `_require_id`-shaped; J19, G19 and a hardening test now **inject** a secret into every governed free-text field before sweeping. |
| 8 | `self.sources` was public and each adapter held `self._service`, so `service.sources["CTRL-04"]._service` was a live `OperationsConsoleService` with `approve`/`commit`/`resolve`, and `available` was publicly writable. The class docstring claimed the opposite. | Boundary 5 is asserted as *structural*; the claim was false even though no HTTP route reached it. | The mapping is private behind `plane_ids()`/`_source()`, and gate G21 now probes behaviourally: no attribute of the service (its own journal excepted) may expose an acting method. |
| 9 | `GET /audit/v1/me` returned the session CSRF token in the response body and `checkpoint()` persisted every session's token, contradicting the record's own docstring. The test that should have caught it compared against *another* session's token and had two identical branches. | Boundary 3 lists session credentials as forbidden on every surface; a checkpoint file became a token store. | The token is delivered as an `X-EPD2-CSRF` response header, is excluded from the checkpoint, and a restored session gets a fresh server-side token — a restart invalidates in-flight tokens. The test now asserts the *requesting* session's token is absent. |
| 10 | Gate G53 was three-quarters tautological: it asserted the substrings `esc(` and `innerHTML` (a page defining `esc` and never calling it would pass), searched for tokens no plausible page contains, and read a developer-set constant. | A gate that cannot fail measures nothing. | G53 now serves a script-shaped case title through the API, asserts it travels as data, and asserts every JSON ingestion in the page is the escaped one (`count("await r.json()") == count("esc(await r.json())")`). |
| 11 | Found while writing the fix for 7: `scrub_text` applied to a **serialised** JSON document can consume the closing quote of the string it matches, so `read_model` either failed to parse or silently lost its tail whenever a governed field ended with `key=<secret>`. | A redactor that corrupts the document it protects is worse than none. | `_scrub_structure` scrubs string *leaves*; the export secret sweep now runs over the unredacted bytes with a wider marker set, so it too can actually fail. |

Two further gaps were found by the mutation corpus rather than the review, and
are recorded for the same reason: `enforce_integrity_verification` and
`enforce_append_only_history` were declared obligations that no code path
consulted, and the voting boundary was unreachable because no source ever
marked an envelope voting-domain. All three are now wired, and the mutation
fixtures that flip them are detected.

Findings the review classified as incidental detection, kept and disclosed:
M06 (`enforce_competence_source`) and M15 (`enforce_query_bounds`) are defence
in depth — the dataclass constructors already refuse an empty rule version and
an out-of-range limit, so their fixtures are detected through a probe that
forces the invariant past the constructor. M20 is detected through a second
attestation on an already-attested case, which is the property the obligation
protects.

## 5. Observed conditions in the canonical baseline

Recorded, not resolved.

**`PCR-CTRL05-STATE-ABSENT`.** The Program Control Register records
`CTRL-01/02/03/04 ACCEPTED / CLOSED; CTRL LAYER OPEN` and its stage-state
block stops at CTRL-04. It records no CTRL-05 execution state. The starter
package supplies that state. Per the entrypoint's update rule, the governed
acceptance of this candidate should record the CTRL-05 transition.

**`PCR-INFRA03-PHASE-TABLE-STALE`.** §1 (line 63) and the stage-state block
(line 123) both record `INFRA-03 = ACCEPTED / CLOSED`, while the §2 phase-state
table's INFRA row (line 96) still reads `INFRA-01 ACCEPTED / CLOSED; INFRA-02
ACCEPTED / CLOSED; INFRA LAYER OPEN` and says INFRA-03…07 are "not promoted".
The two statements disagree. CTRL-05 binds INFRA-03 by its accepted identity
and does not rely on the phase table.

**Repository-wide `mypy scripts` fails on `main` before CTRL-05** (pre-existing
errors in unrelated files). CTRL-05's own runtime and scripts type-check clean
with the service source on the path; the whole-repository `make typecheck`
target is not a green gate on the baseline and is not claimed here.

**Pre-existing failing test** noted in the CTRL-01 report
(`voting-service/tests/reference/test_property.py`) is unchanged and outside
this stage's suite.

**Playwright is not a workspace dependency.** It was installed into the local
virtualenv to run the browser journeys against the environment's pre-provisioned
Chromium. The browser script exits 3 with an explicit `NOT_EXECUTED` result
rather than simulating a pass when Playwright is absent.

## 6. Known limitations

- Sessions are server-side records identified by an opaque header. The
  reference deployment has no session issuer, origin binding or step-up. This
  is a boundary, not a claim.
- Redaction is marker- and pattern-based. A secret stored under an innocuous
  key with an unrecognisable value is not caught; the journal additionally
  refuses known secret shapes and the export refuses them outright.
- The correlation graph's second-hop relation is `same object_ref`, which is a
  deliberately narrow governed relation. Richer correlation would need a
  governed relation vocabulary, which this stage does not invent.
- Checkpointing rewrites the whole state on every mutation; adequate for the
  reference world, not a production persistence design.
- The oversight unit map is supplied by the deployment. CTRL-05 refuses
  unmapped evidence, but it cannot verify that the map itself is correct —
  that is a governance input, and it is recorded in every read model.
- The `EvidenceSealer` key lives in the process that writes the checkpoint. Its
  separation value only materialises when the key is held elsewhere.
- The installed CTRL-01/02/03/04 files were deliberately left byte-identical
  (gate G07), so where CTRL-05 needed a fact those modules only hold privately
  — CTRL-04's voting-domain target registry — the test world reads it directly
  rather than adding an accessor to an accepted module.

## 7. Before any future seal

1. Re-fetch current `main` and re-run G01; a drifted baseline is a
   reconciliation obligation.
2. Reconcile OPS-03 if it is accepted by then; bind its exact identity or keep
   it recorded as not accepted.
3. Re-run the mutation corpus, the E2E journeys and the browser journeys after
   any runtime change; G54 refuses evidence whose runtime digest does not
   match the runtime bytes.
4. Re-record the freeze deliberately, then verify against it, then seal, then
   post-verify the sealed bytes.
