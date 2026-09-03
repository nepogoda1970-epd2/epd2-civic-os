# CTRL-05 — Stage Contract

**Stage:** `CTRL-05 — Audit & Oversight Console`
**Mode:** `PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED`
**Self-state:** `CANDIDATE_NOT_ACCEPTED`
**Self-acceptance:** `false`

This contract claims no CTRL-05 acceptance, no CTRL-layer closure, no
production readiness, no legal activation, no final security acceptance and no
BSI or Common Criteria certification. The developer emits only a PRESEAL
marker; the governed decision belongs to the independent authoritative review.

## 1. What this stage is

A governed **read-and-review** control plane. It lets a competent oversight
actor inspect, correlate, independently verify, challenge, review and attest
the evidence that CTRL-02 (regional intervention and privileged operations),
CTRL-03 (credential, trust and key lifecycle) and CTRL-04 (operations console)
produced — **without acquiring any of their execution, secret or custody
powers**.

Oversight is not a higher privilege. It is a different one: strictly narrower
in what it may *do* and strictly explicit in what it may *see*.

## 2. Competence

There is no auditor role. There is a mandate.

| Element | Rule |
| --- | --- |
| `OversightMandate` | names the exact organization, the exact governed oversight unit, the evidence planes it covers, its rights, its governing rule version and the source decision that created it |
| authority | each right is backed by **its own** live CTRL-02 authority grant; a re-issued grant makes the mandate stale, not automatically wider |
| validity | bounded, at most 365 days; superseding is explicit and refuses the predecessor |
| scope containment | **equality**. A Bund mandate reaches no Land. One oversight unit reaches nothing of another, even inside the same organization |
| universal capability | a wildcard, `ADMIN`, `SUPER_ADMIN`, `ROOT` or `AUDITOR` capability grants **no** oversight competence and is refused before anything else is considered |
| operational capability | a mandate may not bind an audit right to an operational grant (`OPS.*`, `SECRET.*`, `KEY.CUSTODY`, `AUTHORITY.UNIVERSAL_ADMIN`) |
| no mandate | no visibility at all, whatever else the principal holds |

Rights are disjoint: `AUDIT.READ`, `AUDIT.CORRELATE`, `AUDIT.REVIEW`,
`AUDIT.ATTEST`, `AUDIT.EXPORT`. Reading does not carry correlating; reviewing
does not carry attesting; nothing carries exporting.

## 3. Hard boundaries

Each is enforced, each is refused with its own stable reason code, and each is
probed by an executable gate and a mutation fixture.

1. **No universal auditor.** `UNIVERSAL_AUDITOR_EXISTS = False`.
2. **Exact organizational and unit scope, no inheritance.** Evidence streams
   are assigned to an oversight scope by an explicit governed map
   (`PLANE:stream → region:org:unit`); an unmapped stream is invisible.
3. **No raw secrets anywhere** — console, API, browser, log, evidence or
   export. References are kept because they name a handle; material never is.
4. **Source evidence is immutable to CTRL-05.** It annotates only, through
   append-only superseding records. No source adapter exposes a write path and
   the console holds no public handle to a plane.
5. **No shell, SSH, SQL, exec, cluster or secret surface, and no CTRL-04
   execution path.** A reviewer never becomes an operator. Ten absent routes
   are refused explicitly so the absence is observable from outside.
6. **No voting-domain person identifier and no voting-isolation bypass.**
   Voting-domain evidence — declared as such by the plane that owns the fact —
   is never visible, openable or reviewable. The only permitted surface is a
   governed verification-interface reference.
7. **No cross-domain universal person index.** No correlation node is a
   person; no edge is derived from a personal attribute.
8. **Review history is append-only.** Nothing is removed, rewritten or
   reattributed; a dispute stands beside the finding it disputes.
9. **Commit-time reauthorization** on every disposition, attestation and
   export: `prepare` captures the mandate, the authority version, the case
   version and the content digest of every record under review; the act is
   re-authorized at commit against all four, and the ticket is single-use.
10. **Fail closed.** An unavailable plane, an unresolvable authority, an
    unverified integrity state or a missing dependency refuses. An unreadable
    plane is never reported as an absence of evidence.
11. **Certification non-claim.** Recorded in every evidence file.

## 4. Integrity

CTRL-05 does not ask a plane whether its evidence is intact. For every record
it re-derives that plane's own hash from the record's own fields, using that
plane's own algorithm, and re-walks the chain independently. The verdict is a
typed state — `VERIFIED`, `HASH_MISMATCH`, `CHAIN_BROKEN`, `SEQUENCE_BROKEN`,
`METADATA_MISSING`, `SOURCE_UNAVAILABLE`, `UNKNOWN_SCHEMA` — of which only
`VERIFIED` is trustworthy. A broken record is *reported*, never hidden and
never repaired, and it cannot carry a finding or an attestation.

## 5. Evidence

The oversight journal is itself hash-chained, keyed-sealed and append-only.
Every act and **every refusal** is a record. An idempotent retry is a governed
act and is journaled as `REPLAYED`. A clock rollback is journaled before it is
refused. A restored checkpoint is verified record by record against the
journal, including the content digest of every case, disposition, finding and
attestation, so a rewritten table cannot pass by keeping the counts right.

## 6. Export

Every export names an explicit purpose, and the purpose is a field allow-list
(`INTERNAL_REVIEW` ⊃ `GOVERNANCE_REPORT` ⊃ `EXTERNAL_AUDITOR` ⊃
`STATISTICAL`). Fields outside it are dropped and the drop becomes an
evidenced `RedactionDecision`. The payload is bound by digest. An export whose
unredacted bytes carry a secret shape is refused outright.

## 7. Bounds

No route searches everything. A query is anchored on an exact scope and capped
at 500 records; a correlation graph is anchored on an exact identifier, capped
at 200 nodes and depth 3; an export is capped at 200 records; a
reauthorization ticket lives ten minutes; a session lives at most eight hours.

## 8. Bound predecessors

| Stage | Accepted candidate SHA-256 |
| --- | --- |
| CTRL-01 | `07134db175587a9aa441fe87a811c7cfca6cc8dfbd30006279dd0edb598783b5` |
| CTRL-02 | `f58bafe758f19c0b40d3a525d85d0315052c01bc9ed14eae9973079a4dfb993e` |
| CTRL-03 | `89fca0f6c975a7c0e1eb70c2e3ad5229830e781c91d86637a81f99e39ac7b0ff` |
| CTRL-04 | `346acc12316ac4a8f2be45c889aa9002172710da61c67ec88e54a976bb5733a2` |

The installed CTRL-01/02/03/04 runtime files are left byte-identical (gate
G07). INFRA-01/02/03 and OPS-01/02 are bound by their accepted identities;
OPS-03 is recorded as not accepted.

## 9. Developer obligations

| Obligation | Target |
| --- | --- |
| executable gates | 56, every one an executed probe |
| mutation fixtures | 52, every one DETECTED |
| end-to-end journeys | 22, over real HTTP against the real installed planes |
| browser journeys | in a real Chromium, with screenshots |
| terminal marker | `CTRL05_PRESEAL_RESULT:PASS:<sha256>:<size>` |
| forbidden conclusions | `CANON PASS`, `ACCEPTED`, `CLOSED`, `CTRL LAYER CLOSED`, `PRODUCTION READY`, `BSI/CC CERTIFIED`, `SECURITY CERTIFIED` |
