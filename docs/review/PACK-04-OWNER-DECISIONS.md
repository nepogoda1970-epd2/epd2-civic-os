# PACK-04 — Decisions requiring explicit owner approval

**Status: all decisions resolved and canon updated — no open items
remain.** The project owner acted on ADR-011, ADR-012, ADR-013, ADR-014,
and ADR-015 on 2026-07-23; ADR-013's canon-edit task was then carried
out, as its own separate step, later the same day. **No PACK-04 service
code, schema, OpenAPI file, or reason-code registry exists yet** —
implementation of `transparency-service` itself remains separate and has
not begun.

```text
sha256(docs/canonical/TZ-00-domain-event-canon.md) =
  9fc04b928ff043d25354039165eb7a9d0683396c6712210594eef232d6daf9ad
CANON_VERSION = 0.3.0
```

Canon has been updated for ADR-013's (amended) content: new section 19a
(`PublicLedgerEntry`, `AuditExportPackage`, `DisclosurePolicy`,
`LobbyLogEntry`), new section 20.14 (ten Transparency events), and four
new section 22 ownership-matrix rows. This was a canon-only change — see
section 3 below and `docs/adr/ADR-013-canon-0.3.0-transparency-context-additions.md`'s
own "Canon implementation" section for full detail.

## 1. Transparency service decomposition (ADR-011) — accepted

One service, `services/transparency-service`, owning `PublicLedgerEntry`,
`AuditExportPackage`, `DisclosurePolicy`, `LobbyLogEntry`, is accepted
exactly as proposed. No amendment.

## 2. Cross-pack read boundary and dependency matrix (ADR-012) — accepted

The enumerated read-only edges (`initiative-service`,
`moderation-service`, `voting-service`/`tally-service`,
`epd2_audit_core`), the explicit exclusions (`deliberation-service`,
`delegation-service`, and all four PACK-02 identity/credential-adjacent
services), and the one-way dependency direction are accepted exactly as
proposed. No amendment.

## 3. Canon 0.3.0 Transparency Context additions (ADR-013) — accepted with amendments

The four entities, ten-event catalog, and four ownership-matrix
additions are accepted in principle. Four amendments were required and
are now incorporated directly into ADR-013's own text (not tracked only
here):

| #   | Amendment                            | Resolution                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| --- | ------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | `AuditExportPackage` proof semantics | `chain_proof` is now a list of structured proof items (`event_hash`, `previous_event_hash`, public-safe metadata, `sequence_position`), plus new package-level `package_digest` and `integrity_proof` fields. A new "Verification semantics" subsection distinguishes public chain-continuity/ordering/non-modification verification (what the package proves) from full private `AuditEvent` hash recomputation (what it does not claim to prove). |
| 2   | `DisclosurePolicy` field model       | The single `disclosure_class` field plus loose `field_redaction_rules` list is replaced with a structured `field_rules` list (`field_path`, `disclosure_class`, `transformation`, optional `replacement_label`). Every candidate field must resolve to exactly one rule; missing or ambiguous resolution defaults to `prohibited`. Structurally forbidden fields remain outside the candidate set and cannot be reclassified by any policy.         |
| 3   | `PublicLedgerEntry` corrections      | A published entry's stored `status`, `content_snapshot`, and hashes are never rewritten after creation — there is no `corrected` stored status. A correction is exclusively a new row with `supersedes_entry_id` set; superseded-ness is a derived, query-time fact. The identical rule is extended to `LobbyLogEntry` for consistency (an ADR-level extension beyond what the owner's text named, flagged as such in ADR-013).                     |
| 4   | Role references                      | `published_by_role_id` and `submitted_by_role_id` must never appear verbatim in public content — only an approved, generalized role-scope `replacement_label`. Extended to `requested_by_role_id` and `approved_by_role_id` for consistency (same extension caveat as amendment 3).                                                                                                                                                                 |

Every sub-item of Decision (D3.1–D3.6), the event catalog, and the
ownership-matrix additions are accepted as amended above — no sub-item
was rejected.

**Canon edit status:** performed, 2026-07-23, as its own separate,
dedicated task following this acceptance. The (amended) content described
in ADR-013 above is now part of `docs/canonical/TZ-00-domain-event-canon.md`
(section 19a, section 20.14, section 22's four new rows, section 23's
new forbidden-link entries). `canon_version` moved `0.2.0 → 0.3.0` — see
the checksum block at the top of this document.

## 4. Reason-code additions (ADR-014) — accepted

`contracts/reason-codes/pack-04.yml` with `DISCLOSURE_POLICY_VIOLATION`,
`PUBLICATION_NOT_ALLOWED`, `REDACTION_REQUIRED`,
`LOBBY_LOG_ENTRY_INCOMPLETE`, `AUDIT_EXPORT_INTEGRITY_FAILED`,
`LEDGER_ENTRY_ALREADY_PUBLISHED`, plus reused generics, is accepted
exactly as proposed. No amendment. The exact final code list remains
subject to confirmation once `transparency-service`'s real source exists
(ADR-014's own standing caveat, unchanged by acceptance).

## 5. Disclosure, redaction, public audit export, and Lobby Log defaults (ADR-015) — accepted with amendments

| #   | Item                                                                                                  | Resolution                                                                                                                                                                                                                            | Amended?                                       |
| --- | ----------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| 1   | Four disclosure classes (`public`/`redacted`/`restricted`/`prohibited`), `prohibited` non-overridable | Accepted as proposed                                                                                                                                                                                                                  | No                                             |
| 2   | Separation-of-authority / versioned policy changes                                                    | Accepted as proposed                                                                                                                                                                                                                  | No                                             |
| 3   | Lobby Log mandatory fields                                                                            | Accepted as proposed                                                                                                                                                                                                                  | No                                             |
| 4   | Lobby Log publication timing                                                                          | 7 calendar days (amended from 14); no mandatory human review by default; **mandatory automated** completeness/prohibited-field/disclosure-policy validation before publication; corrections only via a new superseding entry          | **Yes**                                        |
| 5   | Moderator/appeal reviewer identity                                                                    | Publish only a generalized role-scope label; never a personal name, `actor_id`, `RoleAssignment` UUID, account, or identity reference; full information restricted to authorized audit/oversight                                      | **Yes** (previously open item 1, now resolved) |
| 6   | Small-cell threshold                                                                                  | `n = 10`; 1–9 shown banded as `"1–9"`; `0` shown exactly; the formally required official `ResultPublication` ledger entry is exempt and must disclose exact counts; distinction recorded explicitly in `DisclosurePolicy` field rules | **Yes** (previously open item 2, now resolved) |
| 7   | Public audit proof semantics                                                                          | Adopts ADR-013's amended D3.2 semantics; the original "external verifier can recompute and confirm the hash chain independently" claim is withdrawn                                                                                   | **Yes**                                        |

No sub-item of ADR-015 was rejected.

## 6. Not requiring a decision right now

Unchanged from the prior version of this document:

- Exact API shapes, JSON Schemas, and OpenAPI paths — implementation
  detail once the ADRs above are (now) accepted, not an owner decision.
- Frontend/UI work — out of scope per `docs/handover/PACK-04-SPEC.md`.
- `docs/review/OPEN_QUESTIONS.md` item 10 (additive reason codes never
  folded back into canon) — flagged again by ADR-014, still not required
  for this pack's own Definition of Done.

## 7. What this canon update does not authorize

Per that task's explicit instructions: no PACK-04 service directory,
implementation schema, OpenAPI file, or reason-code registry file was
created as part of the canon-edit task. `services/transparency-service`
does not exist; no PACK-02/03 source code was touched. Implementation of
`transparency-service` remains a separate, later task, gated on this
canon content but not authorized by it alone.
