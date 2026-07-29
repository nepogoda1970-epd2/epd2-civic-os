# PACK-12 — Threat Model

Specification-only. No code. Not implemented.

> **Status note added by the PACK-12 implementation candidate round
> (2026-07-29).** The "specification-only / not implemented" statement
> above describes the _specification round_ that produced this document
> and is preserved as the historical record. It is no longer the state of
> the repository: `services/privileged-access-service` now implements this
> specification as an **implementation candidate** at repository version
> `0.12.0`.
>
> **LOCAL VERIFICATION INCOMPLETE / EXTERNAL CI PENDING / NOT FINAL PASS.**
> Nothing here is claimed as verified, passed, or production-ready. See
> `docs/handover/PACK-12-IMPLEMENTATION-CANDIDATE-REPORT.md` section 5.

Companion to `PACK-12-SPECIFICATION.md`.

---

## 0. Method and honesty rules

Each threat records: protected asset; attacker or failure mode; trust
boundary crossed; preventive control; detective control; evidence;
residual risk; dependency on a later pack.

Two rules govern the residual-risk column:

1. A control that is **specified** is not a control that **exists**.
   PACK-12 writes no code. Every "preventive control" below is a
   requirement on the future implementation, and the residual risk stated
   assumes the requirement is correctly implemented. Until then the
   residual risk is the full threat.
2. Where the honest answer is "this is not fully mitigable", it says so.
   A threat model whose every row ends in "mitigated" is a marketing
   document.

`T-P12-NN` identifiers are referenced by `PACK-12-ACCEPTANCE-MATRIX.md`.

---

## T-P12-01 — Universal-admin escalation

- **Asset:** every domain's content and decisions.
- **Attacker / failure:** an administrator accumulates or is granted a
  role set that in aggregate spans all domains and scopes; or a
  convenience "superadmin" is introduced during operations.
- **Boundary:** privileged administration → all domain contexts.
- **Preventive:** `P12-ROLE-001`, `P12-ROLE-002`, `P12-ROLE-011`,
  `P12-ROLE-019`, `P12-ROLE-021`, `P12-FE-004`; register `FIR-INV-014`.
- **Detective:** periodic review `P12-PAM-008`; role-set reports;
  `privileged_access.review_completed`.
- **Evidence:** grant records, role assignment history, review outcomes.
- **Residual:** an operator with control of both policy configuration and
  the deployment could in principle reconstruct wide access over time.
  Mitigated by pair 1 of the role matrix, not eliminated.
- **Dependency:** PACK-14 for identity assurance behind the actor
  reference.

## T-P12-02 — Self-approval

- **Asset:** the integrity of every approval gate.
- **Attacker / failure:** a subject approves their own request directly,
  or indirectly via a second role they also hold.
- **Boundary:** requester → approver.
- **Preventive:** `P12-PAM-004`, `P12-BG-003`, `P12-DLP-003`,
  `P12-EXP-006`, `P12-SDC-006`, role matrix section 5.
- **Detective:** `PRIVILEGE_SELF_APPROVAL_PROHIBITED` refusals;
  approval-pair analysis in review.
- **Evidence:** decision records naming requester and approver
  separately.
- **Residual:** collusion between two subjects is not addressed by
  separation of duties and is not claimed to be.
- **Dependency:** none.

## T-P12-03 — Role accumulation

- **Asset:** separation of duties as a whole.
- **Attacker / failure:** individually harmless roles accumulate on one
  subject until the combination breaks a control.
- **Boundary:** IAM → privileged administration.
- **Preventive:** `P12-ROLE-012`, `P12-ROLE-013`, `P12-ROLE-020`,
  `P12-ROLE-021`; the pair table, cumulative with the existing
  institutional incompatibilities.
- **Detective:** re-evaluation at the act, not only at assignment;
  dormancy and review reporting.
- **Evidence:** `SeparationOfDutiesEvaluation` records at approval and at
  activation.
- **Residual:** the pair table is a minimum baseline; a harmful
  combination not yet in it will not be caught. The table is explicitly
  extensible and never relaxable.
- **Dependency:** PACK-08 owns the baseline this extends.

## T-P12-04 — Dormant standing privilege

- **Asset:** the blast radius of a compromised account.
- **Attacker / failure:** a grant issued for a past need remains active
  indefinitely and is later used or stolen.
- **Boundary:** time.
- **Preventive:** `P12-PAM-002` (time-bound), `P12-PAM-003` (no standing
  superuser), `P12-PAM-006` (automatic expiry, no in-place extension).
- **Detective:** `P12-PAM-009` dormancy surfacing;
  `PRIVILEGE_GRANT_DORMANT`.
- **Evidence:** grant windows, last-use records, review outcomes.
- **Residual:** a grant used regularly but no longer necessary is not
  detected by dormancy alone; periodic review is the compensating
  control.
- **Dependency:** none.

## T-P12-05 — Credential sharing

- **Asset:** attribution of privileged acts.
- **Attacker / failure:** two people use one privileged credential, so
  session evidence attributes acts to the wrong subject.
- **Boundary:** human → actor reference.
- **Preventive:** out of PACK-12's reach; PACK-14 owns authentication and
  assurance. PACK-12 requires attributability (`P12-PAM-002`) and states
  the dependency rather than pretending to solve it.
- **Detective:** session evidence anomalies; concurrent-session patterns.
- **Evidence:** session records with actor reference and timing.
- **Residual:** **substantial and not mitigated by PACK-12.** Attribution
  is only as strong as the authentication behind the actor reference.
- **Dependency:** PACK-14, hard.

## T-P12-06 — Session hijacking

- **Asset:** an active privileged session.
- **Attacker / failure:** a session token or context is stolen and reused.
- **Preventive:** `P12-FE-007` (no ordinary shared end-user session for
  privileged UI); `P12-PAM-010` (re-check at every operation).
- **Detective:** session evidence; anomaly review.
- **Evidence:** `privileged_session.*` events.
- **Residual:** **not mitigated by PACK-12.** Session binding, token
  handling and re-authentication are PACK-14's.
- **Dependency:** PACK-14, hard.

## T-P12-07 — Audit suppression

- **Asset:** the audit chain and session evidence.
- **Attacker / failure:** a privileged actor disables, truncates, edits
  or deletes audit records to hide an act.
- **Boundary:** privileged administration → audit core.
- **Preventive:** `P12-ROLE-006`, `P12-BG-011`, `P12-SES-004`,
  `PRIVILEGE_AUDIT_MUTATION_PROHIBITED`; PACK-02's append-only hash
  chain.
- **Detective:** chain verification by the `audit_custodian`;
  `AUDIT_CHAIN_BROKEN`.
- **Evidence:** hash chain; sealed session evidence.
- **Residual:** tamper **evidence**, not tamper resistance. An actor with
  storage-level access can rewrite and recompute. There is no external
  anchor (`P12-SES-007`).
- **Dependency:** key management and external anchoring, later packs.

## T-P12-08 — Infrastructure admin reading domain data

- **Asset:** all domain content at rest.
- **Attacker / failure:** a `system_administrator` reads database or
  storage contents directly, bypassing every domain control.
- **Boundary:** infrastructure → domain content.
- **Preventive:** `P12-ROLE-003`, `P12-ROLE-014` (institutional semantics
  preserved), role matrix pair 5, `P12-EXP-007`.
- **Detective:** infrastructure-level access logging; export-path
  reconciliation (data leaving without a governed export object).
- **Evidence:** grant records; absence of a corresponding export object.
- **Residual:** **significant.** Storage-level read is largely outside
  application control. Encryption-at-rest with keys the system
  administrator does not hold is the real mitigation and is **not**
  specified here.
- **Dependency:** PACK-13 (data plane), key management, hard.

## T-P12-09 — Stale ACL in the search index

- **Asset:** records whose authorization has narrowed.
- **Attacker / failure:** a user retains findability through an index
  built under a previous, wider authorization.
- **Boundary:** source of truth → index projection.
- **Preventive:** `P12-SRCH-004`, `P12-SRCH-005`, `P12-SRCH-012`.
- **Detective:** `SEARCH_INDEX_AUTHORIZATION_STALE`; reconciliation runs.
- **Evidence:** `QueryAudit`; `search_index.*` events.
- **Residual:** a reconciliation window exists between a source change
  and index convergence; query-time re-resolution is what closes it, at a
  latency cost the implementation must accept rather than optimise away.
- **Dependency:** PACK-13 for the real index.

## T-P12-10 — Count, facet and snippet leakage

- **Asset:** the existence and shape of restricted records.
- **Attacker / failure:** a user infers restricted content from a result
  count, a facet value, an autocomplete suggestion or a snippet.
- **Preventive:** `P12-SRCH-006`, `P12-SRCH-007`, `P12-SRCH-008`.
- **Detective:** `SEARCH_RESULT_SUPPRESSED`, `SEARCH_FACET_SUPPRESSED`
  with count **bands**, not exact counts.
- **Evidence:** `QueryAudit`.
- **Residual:** timing and latency side channels are not addressed.
- **Dependency:** none.

## T-P12-11 — Cache cross-contamination

- **Asset:** any cached result set.
- **Attacker / failure:** a cache entry populated for one subject or
  scope is served to another.
- **Preventive:** `P12-SRCH-009` (authorization context in the cache key).
- **Detective:** `SEARCH_CACHE_CONTEXT_MISMATCH`.
- **Evidence:** `QueryAudit` with cache-hit marker.
- **Residual:** shared CDN or proxy layers outside the application are
  not covered.
- **Dependency:** PACK-13, PACK-14 (gateway).

## T-P12-12 — Unauthorized bulk extraction

- **Asset:** whole record classes.
- **Attacker / failure:** a legitimate read permission is exercised at
  scale until it amounts to a copy of the dataset.
- **Preventive:** `P12-EXP-005`, `P12-DLP-001` (size, frequency, volume
  limits), `P12-EXP-001` (export as a governed object).
- **Detective:** `EXPORT_DLP_FREQUENCY_LIMIT_EXCEEDED`,
  `EXPORT_DLP_UNUSUAL_VOLUME_REVIEW`, repeated-request risk.
- **Evidence:** export objects; access events; query audit.
- **Residual:** slow extraction under all thresholds remains possible;
  cumulative accounting (`P12-SDC-004`) is the compensating control.
- **Dependency:** PACK-13 for the telemetry to detect it at scale.

## T-P12-13 — Export of hidden fields

- **Asset:** fields denied by policy.
- **Attacker / failure:** denied fields ride along in the artifact —
  embedded in an identifier, a metadata block, a spreadsheet's hidden
  column, or a format's internal structure.
- **Preventive:** `P12-EXP-008` (exclusion before generation, not
  filtering at delivery), field-policy pipeline in the data matrix
  section 5.
- **Detective:** `EXPORT_MANIFEST_MISMATCH`; manifest-to-artifact
  reconciliation.
- **Evidence:** immutable manifest bound to the artifact.
- **Residual:** format-specific carriers (document metadata, revision
  history, embedded thumbnails) require format-aware sanitisation the
  implementation must supply.
- **Dependency:** none.

## T-P12-14 — Small-cohort re-identification

- **Asset:** individuals within an aggregate release.
- **Attacker / failure:** a cohort small enough to identify a person is
  published or exported.
- **Preventive:** `P12-SDC-001`, `P12-SDC-005`, `P12-SDC-007`.
- **Detective:** `DISCLOSURE_THRESHOLD_FAILED`,
  `DISCLOSURE_COMPLEMENT_RECOVERABLE`.
- **Evidence:** `DisclosureRiskAssessment`, `SuppressionDecision`.
- **Residual:** external auxiliary data can re-identify cohorts that pass
  every internal rule. Thresholds reduce, never eliminate, this.
- **Dependency:** PACK-13 for release-history storage at scale.

## T-P12-15 — Repeated-query differencing

- **Asset:** suppressed values.
- **Attacker / failure:** two nearly-identical queries differ by one
  individual, and the difference discloses that individual.
- **Preventive:** `P12-SDC-003`, `P12-SDC-007`.
- **Detective:** `DISCLOSURE_REPEATED_QUERY_RISK`;
  `disclosure_control.cumulative_risk_flagged`.
- **Evidence:** `ReleaseHistoryReference`; query audit.
- **Residual:** differencing across subjects, or across a subject and a
  colleague, is only caught if history is accounted per purpose rather
  than per actor. `OD-P12-08` is open on exactly this.
- **Dependency:** PACK-13.

## T-P12-16 — Cumulative export disclosure

- **Asset:** individuals across several permitted exports.
- **Attacker / failure:** each export passes its own assessment; jointly
  they re-identify.
- **Preventive:** `P12-SDC-004`.
- **Detective:** `DISCLOSURE_CUMULATIVE_RELEASE_RISK`.
- **Evidence:** release history; export objects.
- **Residual:** cumulative accounting must be bounded in time and storage
  to be implementable; any bound creates a window. Stated, not solved.
- **Dependency:** PACK-13; `OD-P12-08`.

## T-P12-17 — Malicious or compromised recipient

- **Asset:** the exported artifact after delivery.
- **Attacker / failure:** an authorised recipient misuses, re-shares or
  loses the data.
- **Preventive:** `P12-EXP-014`, `P12-EXP-015`, recipient-category
  profile, watermarking, transfer-channel restriction.
- **Detective:** access events; watermark attribution on a leaked copy.
- **Evidence:** obligations record; delivery and access events;
  destruction attestation.
- **Residual:** **not mitigable by the platform.** Once delivered, the
  data is outside the trust boundary. Controls are deterrent and
  attributive only (`P12-DLP-004`).
- **Dependency:** contractual and legal, not technical.

## T-P12-18 — Revoked export remaining externally available

- **Asset:** a revoked artifact's already-delivered copies.
- **Attacker / failure:** revocation is believed to have removed the
  data; it has not.
- **Preventive:** none possible. `P12-EXP-013` requires the system to say
  so plainly rather than imply deletion.
- **Detective:** access events cease at the platform boundary only.
- **Evidence:** revocation record; destruction attestation where obtained.
- **Residual:** **full.** This row exists so that no operator is misled
  by the word "revoke".
- **Dependency:** none; this is a truthfulness requirement, not a control.

## T-P12-19 — Insider use of break-glass

- **Asset:** everything break-glass can reach.
- **Attacker / failure:** an insider manufactures or exaggerates an
  emergency to obtain wide access quickly.
- **Preventive:** `P12-BG-001`..`P12-BG-005`, `P12-BG-010`, narrow scope,
  short hard expiry.
- **Detective:** `P12-BG-006` notification; `P12-BG-014` independent
  post-hoc review.
- **Evidence:** emergency condition reference; dual-control decision;
  session evidence; review outcome.
- **Residual:** a genuine-looking emergency with a colluding approver
  defeats dual control. Post-hoc independent review is the compensating
  control and is deliberately mandatory rather than discretionary.
- **Dependency:** PACK-17 for incident correlation.

## T-P12-20 — Break-glass without independent notification

- **Asset:** the visibility of emergency access.
- **Attacker / failure:** the activator suppresses, delays or redirects
  the out-of-band notification so nobody independent learns of it.
- **Preventive:** `P12-BG-007` (not suppressible by the activator or
  anyone they direct), `P12-BG-008` (undelivered ⇒ escalate, never
  silently complete).
- **Detective:** `break_glass.notification_dispatched` emitted on failure
  too; `PRIVILEGE_BREAK_GLASS_NOTIFICATION_UNDELIVERED`.
- **Evidence:** dispatch event with outcome; escalation reference.
- **Residual:** an actor controlling the notification transport itself
  remains a gap until the gateway pack governs it.
- **Dependency:** PACK-17 / gateway pack, hard.

## T-P12-21 — Privileged access to ballot-level or intermediate-tally material

- **Asset:** ballot content, individual vote selections, vote envelopes,
  voter-to-choice and credential-to-ballot linkage, cryptographic voting
  secrets, intermediate, partial and non-certified tally material,
  delegation records. **Not** the final certified result, which is a
  different category — see the note below.
- **Attacker / failure:** any privileged path — role, grant, break-glass,
  search or export — reaches voting material.
- **Preventive:** `P12-VOTE-001`, `P12-VOTE-002`, `P12-VOTE-003`,
  `P12-BG-010`, `P12-HCD-003`, `P12-EXP-003`; role matrix all-`N` row;
  `SEARCH_BALLOT_CONTENT_PROHIBITED`, `EXPORT_BALLOT_CONTENT_PROHIBITED`,
  `EXPORT_UNCERTIFIED_RESULT_PROHIBITED`.
- **Detective:** any occurrence of those reason codes is an incident, not
  a routine refusal.
- **Evidence:** refusal events; structural absence of a voting reference
  anywhere in the PACK-12 model.
- **Residual:** the strongest guarantee is structural — PACK-12 defines
  no reference type that can point at voting material, mirroring how
  PACK-10 and PACK-11 handle the same boundary. Storage-level access
  (T-P12-08) remains the residual path.
- **Dependency:** PACK-15/16 own the voting boundary itself, and the
  authoritative voting and result-certification domain owns publication
  of the final certified result (`P12-VOTE-004`). PACK-12 can audit that
  a governed publication occurred and nothing more (`P12-VOTE-005`);
  treating a certified, closed, rendition-bound result as if it were
  ballot-level material would be a different error, and this row does not
  make it.

## T-P12-22 — Export bypass through direct database access

- **Asset:** every record class.
- **Attacker / failure:** data is extracted directly from storage,
  producing no export object, no manifest, no DLP assessment and no
  audit.
- **Preventive:** `P12-EXP-007` declares this a control failure rather
  than an alternative path; `P12-ROLE-003` separates infrastructure from
  content authority.
- **Detective:** reconciliation of data egress against governed export
  objects; infrastructure access review.
- **Evidence:** absence of an export object for observed egress.
- **Residual:** **significant**, and the same residual as T-P12-08.
  Application-layer specification cannot close a storage-layer path.
- **Dependency:** PACK-13, key management, hard.

---

## 1. Residual-risk summary

| Class                                                   | Threats                                                |
| ------------------------------------------------------- | ------------------------------------------------------ |
| Addressed by PACK-12 specification, subject to build    | 01, 02, 03, 04, 09, 10, 11, 12, 13, 14, 15, 16, 19, 21 |
| Depends materially on PACK-13 (data plane)              | 08, 09, 12, 14, 15, 16, 22                             |
| Depends materially on PACK-14 (auth, session, gateway)  | 05, 06, 11                                             |
| Depends materially on PACK-17 / gateway (notification)  | 20                                                     |
| Not mitigable by the platform; truthfulness requirement | 17, 18                                                 |

No row in this model is closed by this round. PACK-12 has produced a
specification; the controls exist when they are built, tested and
verified, and not before.
