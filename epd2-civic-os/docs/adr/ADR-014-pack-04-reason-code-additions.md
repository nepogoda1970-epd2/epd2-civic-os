# ADR-014: PACK-04 reason-code registry and additive codes

## Status

`accepted`

## Date

2026-07-23

## Owner decision

Accepted as proposed, 2026-07-23. Creating a new, separate
`contracts/reason-codes/pack-04.yml` registry (Decision, below),
mirroring PACK-02/03's own `pack-02.yml`/`pack-03.yml` mechanism, is
approved with no amendments. The proposed additive code list
(`DISCLOSURE_POLICY_VIOLATION`, `PUBLICATION_NOT_ALLOWED`,
`REDACTION_REQUIRED`, `LOBBY_LOG_ENTRY_INCOMPLETE`,
`AUDIT_EXPORT_INTEGRITY_FAILED`, `LEDGER_ENTRY_ALREADY_PUBLISHED`)
remains subject to final confirmation once `transparency-service`'s real
`reason_code = "..."` call sites exist (this ADR's own caveat, unchanged
by acceptance) — that confirmation is a later, separate implementation
task, not authorized by this acceptance alone.

## Context

Canon section 24's fixed list of reason codes has none scoped to public
disclosure, redaction, or export integrity — unsurprising, since (per
ADR-013's own findings) canon never previously defined any Transparency-
context entity or action to have a reason code for. ADR-004 (PACK-02) and
ADR-006 (PACK-03) both established the same precedent for this situation:
a new, pack-specific, ADR-governed registry file
(`contracts/reason-codes/pack-0N.yml`) that copies canon's relevant codes
verbatim and adds new ones under a documented `source` tag, validated by
the existing `ReasonCodeRegistry` structural check and the
"every `reason_code` literal used in a service is registered" contract
test (`test_reason_codes_registry.py`), extended once more to scan
`transparency-service`.

## Problem

`docs/handover/PACK-04-SPEC.md` section 7 already anticipates specific
gaps ADR-013's four proposed entities would create refusal conditions
for: a `DisclosurePolicy` violation, an attempt to publish something a
policy forbids, a redaction that must occur but has not, an incomplete
`LobbyLogEntry` submission, and an `AuditExportPackage` whose hash chain
fails integrity verification. None of canon's 22 fixed codes name any of
these; reusing an unrelated existing code (e.g. `PERMISSION_DENIED` for
an incomplete lobby-log submission) would repeat the exact mislabeling
anti-pattern ADR-004 already found and fixed once for PACK-02
(`IDENTITY_NOT_VERIFIED` et al. misused for a plain not-found condition).

## Considered options

- Option A — restrict PACK-04 to only reused generic codes
  (`PERMISSION_DENIED`, `INTEGRITY_CHECK_FAILED`, `SERVICE_STATE_READ_ONLY`,
  `EVENT_VERSION_UNSUPPORTED`), forcing imprecise reuse for every gap in
  Context above.
- Option B — a new, separate `contracts/reason-codes/pack-04.yml`
  registry, following ADR-004/ADR-006's exact structure.
- Option C — append PACK-04's additive codes directly into
  `contracts/reason-codes/pack-03.yml`, on the theory that Transparency
  is "downstream" of Participation and Decision and could share that
  pack's registry file.

## Decision

Option B. `contracts/reason-codes/pack-04.yml` will be the single source
of truth for `transparency-service`, structured exactly like
`pack-02.yml`/`pack-03.yml`:

1. No canon section-24 codes are directly reused as-is by name for this
   pack's own refusal conditions (unlike PACK-03, which had nine
   directly-named canon codes to start from) — canon's Transparency
   silence (ADR-013 Context) means this pack's registry is almost
   entirely additive, plus reused generics.
2. Proposed additive codes, each `introduced_in_version: "pack-04-adr-014"`:
   `DISCLOSURE_POLICY_VIOLATION` (a publish action would violate the
   active `DisclosurePolicy` for its `subject_type`),
   `PUBLICATION_NOT_ALLOWED` (the underlying canonical event/status
   required for publication has not yet occurred — e.g. attempting to
   publish an `Initiative` that has not reached `published` status),
   `REDACTION_REQUIRED` (a field-redaction rule applies and was not
   satisfied before the publish attempt), `LOBBY_LOG_ENTRY_INCOMPLETE`
   (a mandatory field per ADR-013 D3.4 is missing at submission),
   `AUDIT_EXPORT_INTEGRITY_FAILED` (an `AuditExportPackage`'s `chain_proof`
   fails independent hash verification), `LEDGER_ENTRY_ALREADY_PUBLISHED`
   (an attempt to publish a duplicate `PublicLedgerEntry` for a
   `subject_event_id` that already has one — idempotency-adjacent, not a
   correction; corrections use `supersedes_entry_id` instead, per
   ADR-013 D3.1).
3. Reused generic codes (unchanged meaning): `PERMISSION_DENIED` (a
   `RoleAssignment`-gated action attempted by an unauthorized role),
   `INTEGRITY_CHECK_FAILED` (general hash-chain or schema integrity
   failures not specific to an audit export), `SERVICE_STATE_READ_ONLY`,
   `EVENT_VERSION_UNSUPPORTED`.
4. The same structural validation and contract test PACK-02/03 already
   have (`epd2_core.reason_codes.ReasonCodeRegistry`,
   `tests/contract/test_reason_codes_registry.py`), extended to scan
   `transparency-service`'s source in addition to the existing eleven
   services.

Option A is rejected for the same reason ADR-004/006 already gave: it
either produces imprecise refusals (violating INV-09) or eventually
reproduces the mislabeling bug ADR-004 fixed. Option C is rejected
because `pack-03.yml`'s header documents it as PACK-03's own registry
specifically; folding PACK-04's additions in would make provenance
(`introduced_in_version`) harder to audit across packs, and canon section
24 places no requirement that additive codes share a file across packs —
only that each pack maintain one centralized registry for itself, which
PACK-02 and PACK-03 both already satisfied with their own separate files.

The exact final code list remains subject to confirmation once
`transparency-service`'s real `reason_code = "..."` call sites exist (the
same caveat ADR-006 placed on its own list) — this ADR fixes the
mechanism and the concrete gaps identified in
`docs/handover/PACK-04-SPEC.md` section 7, not a guaranteed-final
enumeration.

## Consequences

`contracts/reason-codes/pack-04.yml` becomes the one file every
`transparency-service` `reason_code` literal must appear in.
`docs/review/OPEN_QUESTIONS.md` item 10 (PACK-02's additive codes never
folded back into canon section 24) is now three additive layers deep if
this pack proceeds (PACK-02, PACK-03, PACK-04) — flagged again for the
project owner's attention in `docs/review/PACK-04-OWNER-DECISIONS.md`,
not resolved by this ADR.

## Security impact

None of the additive codes weaken fail-closed behavior (INV-10) — each
addition makes a refusal more specific than an imprecise reuse would,
continuing the direction ADR-004/006 already established.
`AUDIT_EXPORT_INTEGRITY_FAILED` in particular strengthens, rather than
weakens, this pack's core public-verifiability promise by giving hash-
chain failures their own explicit, non-generic code.

## Data impact

None — reason codes are metadata on entities/events ADR-013 proposes;
this ADR adds no new canonical entity or field itself.

## Migration impact

None — no `transparency-service` has shipped; there is no prior
reason-code consumer to migrate.

## Reversibility

Reversible with cost: removing an additive code later requires confirming
no caller still emits it, the same reversibility profile ADR-004/006
already assigned to their own additive codes.

## Related canon version

Authored against canon version `0.2.0`. Proposes no canon edit — reason
codes remain a pack-level registry concern, exactly as ADR-004/006
already established; this ADR does not depend on ADR-013's acceptance to
be decided in principle, though several of its proposed codes reference
ADR-013's proposed entities/fields by name.
