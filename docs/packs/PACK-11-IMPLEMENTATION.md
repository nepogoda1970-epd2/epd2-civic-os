# PACK-11 — implementation

> What was built, module by module, and the decision behind each shape
> that a reader would otherwise have to reconstruct.

## Files

```text
services/document-service/
  README.md
  pyproject.toml                     epd2-core, epd2-audit-core, nothing else
  src/epd2_document_service/
    __init__.py                      module map, status, implemented FIR entries
    exceptions.py                    one class per registered reason code
    domain.py                        value objects, taxonomies, the three emission boundaries
    versions.py                      immutable versions + the hash-linked chain
    authorization.py                 roles, actions, matrix, separation, access, independence
    documents.py                     the aggregate, review, approval, publication, supersession, revocation
    evidence.py                      evidence records, custody chains, sealed bundles
    determinations.py                signature + admissibility determinations, resolution
    references.py                    outward and inward typed references
    events.py                        25 event builders + the envelope
    storage.py                       ports, in-memory adapters, content-addressed content store
    projections.py                   restricted + public read models
    application.py                   commands and queries
  tests/                             13 modules, 358 tests
```

## Decisions a reader would otherwise have to reconstruct

**`content_descriptor`, not `content`, on the wire and in the hashed
fields.** `content` is in `FORBIDDEN_CONTENT_KEYS` because in every wire
payload in this repository that name means the bytes. The rename is what
lets the emission check stay blunt and key-name-based — and the guard
caught the original naming during development, which is the check working
as designed.

**`title_reference`, never `title`.** A document's title is content.
"Beschwerde gegen den Aufnahmebescheid von …" names a person as reliably as
a `full_name` field would.

**`is_authoritative` is a property, not a field.** A field could be
constructed `True`; a property cannot, and the distinction survives
`dataclasses.replace`, deserialisation and every future field.

**Review findings travel as counts.** `open_blocking_review_count` answers
"is this contested?" without answering "with what?" — the finding text is
the internal deliberation `FIR-MEM-001` says an applicant must not see.

**`_appended` takes explicit typed parameters, not `**changes`.** A bag
would type-check as `object` and let a misspelled field name become a
silent no-op, which on an aggregate whose job is not losing facts is the
worst available failure mode.

**`record_state_change` compares `hashable_fields`, not the stored hash.**
A caller that altered a covered field without resealing would leave
`version_hash` unchanged and slip past a hash-only comparison. This was a
real gap found by `test_a_state_change_may_not_alter_anything_the_hash_covers`
and closed by widening the check.

**`DOCUMENT_EVIDENCE_BUNDLE_ALREADY_SEALED` vs
`DOCUMENT_EVIDENCE_BUNDLE_SEALED`.** One string meaning both "this worked"
and "this was refused" would make every audit query over it ambiguous.

**The no-break-glass test parses the AST.** `NO_BREAK_GLASS_NOTE` *names*
`force`, `skip_checks` and `bypass` in order to forbid them; a
text-matching check cannot tell a prohibition from a bypass.

**Assembly and sealing of a bundle are one command**, unlike approval and
publication which are deliberately two. There, two acts by two roles is the
control. Here, an unsealed bundle is not a governed object at all, and a
window in which a bundle is citable but still mutable would be the defect.

## Test coverage

358 tests across thirteen modules. The version-integrity suite is written
against the *attacks* rather than the happy path: a rewritten field, a
removed version, a re-parented chain, a swapped content blob, a resealed
forgery. `test_privacy_boundary.py` sweeps the real source, the real
dataclass fields and the real payloads of a full lifecycle, so a field or
builder added later is covered without anybody remembering to add a test.

## Verification performed in this round

- Full test suite: 358 passed, 0 failed.
- `scripts/check_canon_0_8_0.py`: 18/18 checks pass.
- `scripts/verify_versions.py`: consistent.
- `scripts/check_repository.py`: all required paths present.
- Line length, trailing whitespace, EOF newline and unused-import sweeps:
  clean.
- Reason-code registry: 71 unique entries; every literal used in
  `services/document-service/src` is registered.

**Not performed in this sandbox**, and requiring the CI run described in
`LOCAL_VERIFICATION.md`: `uv lock` / `uv sync`, `ruff format --check`,
`ruff check`, `mypy`, `pytest` under the real runner, and the frontend
build. This sandbox has no package-index access, so the suite above was
executed with a local runner and the lint approximations named. That is
the same limitation every prior pack recorded, and CI is where it is
resolved.
