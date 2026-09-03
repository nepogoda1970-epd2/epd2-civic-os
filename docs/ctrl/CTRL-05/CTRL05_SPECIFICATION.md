# CTRL-05 — Specification

**Stage:** `CTRL-05 — Audit & Oversight Console`
**Mode:** `PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED`
**Self-state:** `CANDIDATE_NOT_ACCEPTED`

No CTRL-05 acceptance, no CTRL-layer closure, no production readiness, no
legal activation, no final security acceptance and no BSI or Common Criteria
certification is claimed anywhere in this document.

## 1. Shape

| File | Lines | What it is |
| --- | --- | --- |
| `oversight_sources.py` | 779 | read-only projections of the three evidence planes, and the independent integrity verification |
| `oversight_console.py` | 3904 | the governed runtime: competence, scope, review lifecycle, two-phase commit, export, journal, persistence |
| `oversight_api.py` | 764 | the HTTP JSON transport and the observably absent surfaces |
| `oversight_console.html` | — | the single-page console; renders, never decides |

## 2. Evidence sources

Each adapter wraps exactly one accepted plane and exposes only reading
methods. The console holds them privately and hands out no handle.

| Plane | Source | Reads |
| --- | --- | --- |
| CTRL-02 | `Ctrl02EvidenceSource` | `RegionalOperationsService.events` — intervention, privileged/JIT and break-glass acts |
| CTRL-03 | `Ctrl03EvidenceSource` | `CredentialLifecycleService.events` — credential, trust and key lifecycle acts |
| CTRL-04 | `Ctrl04EvidenceSource` | the Operations Console `EvidenceJournal` plus its composed `epd2.ctrl04.evidence.v1` record |

Every record becomes an `EvidenceEnvelope` carrying an `EvidenceReference`
(`PLANE:stream:event`, sequence, event hash, content digest), the domain, the
scope key, the governed fields of the act, the fields that were redacted, and
an `IntegrityVerification`.

**Integrity is re-derived, never read.** For CTRL-02 and CTRL-03 the payload
hash is rebuilt as `sha256(json.dumps(payload, sort_keys=True))` from the
record's own fields and the chain is re-walked; for CTRL-04 the accepted
CTRL-01 `ControlEvidenceEvent.compute_hash` is applied and the chain re-walked
independently. Only `VERIFIED` is trustworthy.

**Domain is declared, never guessed.** A record is voting-domain when it names
an object the owning plane declared voting-domain (CTRL-04's target registry)
or when its object class is voting-domain by construction (CTRL-03's
`VOTING_KEY_REFERENCE`). No name is sniffed.

**Unavailability is reported, never converted into absence.** `collect`
returns the envelopes it could read *and* a per-plane failure map.

## 3. Competence and scope

`OversightScope(region_id, org_id, unit_id)`; `contains` is equality.
`OversightMandate` binds each right to its own live CTRL-02 grant through
`authority_bindings`, and a right with no binding cannot be constructed.

`_resolve_mandate` refuses in a fixed order, because each failure is a
different governance fact:

1. a universal or wildcard capability → `AUD_UNIVERSAL_AUDITOR_FORBIDDEN`
2. no mandate at all → `AUD_NO_OVERSIGHT_MANDATE`
3. wrong organization → `AUD_WRONG_ORGANIZATION_SCOPE`
4. wrong oversight unit → `AUD_WRONG_UNIT_SCOPE`
5. plane not in the mandate → `AUD_PLANE_NOT_IN_MANDATE`
6. right not carried → `AUD_RIGHT_ABSENT`
7. not effective now → `AUD_MANDATE_EXPIRED` / `AUD_MANDATE_SUPERSEDED`
8. no governing rule → `AUD_COMPETENCE_SOURCE_MISSING`
9. the right bound to an operational capability → `AUD_OPERATIONAL_RIGHT_NOT_USABLE_HERE`
10. no live grant, or a different one → `AUD_AUTHORITY_UNRESOLVABLE` / `AUD_STALE_AUTHORITY`

Visibility is a separate, equally itemised decision
(`_visibility_refusal`): voting boundary, then plane, then unit, then
organization — each with its own code, so "not your unit" never looks like
"not your organization".

## 4. Review lifecycle

```
EVIDENCE.SEARCH → EVIDENCE.OPEN → EVIDENCE.VERIFY
                → CORRELATION.GRAPH / CHAIN.OPEN
CASE.OPEN → CASE.CLARIFY
          → [PREPARE → CASE.DISPOSE]
          → [PREPARE → FINDING.RAISE] → FINDING.DISPUTE
          → REMEDIATION.LINK
          → [PREPARE → CASE.ATTEST] → CASE.CLOSE
          → [PREPARE → EVIDENCE.EXPORT]
```

14 governed actions, 5 read and 9 mutating; 28 typed records; 28 policy
obligations, all enforced; 49 stable refusal reason codes.

**Two-phase commit.** `prepare` issues a server-held ticket capturing the
mandate id, the mandate reference, the authority grant id and version, the
case version, and the content digest of every evidence record in the case. At
commit `_reauthorize` re-checks the session, the CSRF token, the mandate, the
authority grant *and* version, the case version and every evidence digest, and
consumes the ticket. Divergence in any of them refuses with its own code:
`AUD_STALE_AUTHORITY`, `AUD_STALE_REVIEW_VERSION`,
`AUD_EVIDENCE_DIVERGED_SINCE_REVIEW`, `AUD_REPLAYED_REQUEST`.

**Idempotency is a governed act.** A retry with the same key returns the same
object, but only after the session, its CSRF token and the live mandate have
been re-checked, and the replay is journaled as `REPLAYED`.

**Append-only.** A second disposition supersedes the first and both stand. A
disputed finding is marked `DISPUTED` and kept beside its dispute. No method
removes anything.

## 5. Export

`INTERNAL_REVIEW` (12 fields) ⊃ `GOVERNANCE_REPORT` (9) ⊃ `EXTERNAL_AUDITOR`
(6) ⊃ `STATISTICAL` (4). Fields outside the purpose are dropped into an
evidenced `RedactionDecision`; the payload carries a SHA-256 digest; an export
reaching outside its case, past 200 records, or carrying a secret shape in its
unredacted bytes is refused.

## 6. Secret and identifier policy

Metadata is redacted key- and value-wise (`redact_metadata`), free text is
scrubbed at ingestion (`scrub_text`) for **every** governed field — title,
clarification text, rationale, summary, statement and remediation plane — and
structures are scrubbed **per value**, never as serialised bytes. Session CSRF
tokens are delivered as a response header, never in a read body, and are never
persisted. The journal refuses any attribute whose key is a person
identifier.

## 7. HTTP surface

11 scoped read routes and 12 act routes. Every case-shaped read names its
exact oversight scope in the query string and resolves the mandate for it;
there is no route that lists everything. 32 forbidden client fields are
refused on presence, not ignored. Ten absent surfaces — shell, exec, sql, ssh,
kubectl, secrets, keys, operations, action execution, evidence mutation — are
refused with `AUD_EXECUTION_SURFACE_ABSENT` so their absence is provable.

## 8. Persistence

`checkpoint()` writes the mandates (without session tokens), the review
tables, the tickets, the decisions, the journal, its anchor and a keyed seal.
`from_checkpoint` re-derives every journal record, compares the anchor,
verifies the seal, and then cross-checks the tables against the journal *per
record*: the case's title, scope and author; each disposition's state,
rationale, author and predecessor; each finding's severity, summary, author
and evidence; each attestation's outcome, statement, author and attested case
version. A restored session carries a fresh server-side token, so a restart
invalidates in-flight CSRF tokens rather than trusting old ones.

## 9. Validation

| Item | Result |
| --- | --- |
| gates | 56/56 PASS, every gate an executed probe |
| mutation fixtures | 52/52 DETECTED (28 policy flips, 24 direct code edits) |
| E2E journeys | J01–J22, 22/22 PASS over real HTTP against the real installed planes |
| browser journeys | B01–B05, 5/5 PASS in Chromium, screenshots in `validation/ctrl05/browser/` |
| tests | 213 CTRL-05 tests; cumulative control-plane suite 597 passed |
