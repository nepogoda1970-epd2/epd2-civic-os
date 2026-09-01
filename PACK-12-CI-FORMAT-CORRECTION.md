# PACK-12 — CI FORMAT CORRECTION

**PACK-12 CI FORMAT CORRECTION — Prettier only.**
**Not a rebuilt candidate. Not a PASS.**

The PACK-12 candidate's status is unchanged:
**LOCAL VERIFICATION INCOMPLETE / EXTERNAL CI PENDING / NOT FINAL PASS.**

Applies on top of
`EPD2_PACK-12_PRIVILEGED_ADMIN_SEARCH_EXPORT_0.12.0_CANDIDATE_CORRECTED.zip`.
Overlay these 15 files at their repository paths; nothing else changes.

---

## What was done

`prettier --write` was run with the repository's own configuration
(no `.prettierrc` exists, so Prettier defaults apply, plus the existing
`.prettierignore`) on the files named in the correction request.

**Nothing else was touched.** No wording, semantics, code, test,
dependency, version, canon, CI configuration or scope change. No table
was reformatted by hand.

## The 15 changed files

| File                                                         | SHA-256                                                            |
| ------------------------------------------------------------ | ------------------------------------------------------------------ |
| `docs/adr/README.md`                                         | `75c1a9d2f1325667574cd0c4b06db70244d1d3d346a43d8bf7b6a3e96aab499c` |
| `docs/handover/PACK-12-IMPLEMENTATION-CANDIDATE-REPORT.md`   | `027b9bb61705f761fb880500caeb51bac7646c09b898ab47f14f2b071ce3d055` |
| `docs/handover/PACK-12-KNOWN-LIMITATIONS.md`                 | `39d07059370d32346c5368cc325a434d4211f0454c41ca803d6bc5a12e33707a` |
| `docs/handover/PACK-12-SPEC-ADR-REPORT.md`                   | `bb4f730ac00b99fc557e8c05f07acd2acbdd9d2f00f215119ca997bef39c4474` |
| `docs/packs/PACK-12/PACK-12-ACCEPTANCE-MATRIX.md`            | `b3ed4d16463bef018cdbc68cbe9c2afa501089bae40342c369d5f57b25edb4c1` |
| `docs/packs/PACK-12/PACK-12-CANON-ASSESSMENT.md`             | `b8f07bef812b593a69460224a57bd504288834cd173a195e2d0171948849aaf5` |
| `docs/packs/PACK-12/PACK-12-DATA-SEARCH-EXPORT-MATRIX.md`    | `fbac429c9d14dde3848f8aec1105396ce2b51141c5949fcb71b53163d7bba883` |
| `docs/packs/PACK-12/PACK-12-EVENT-CATALOG.md`                | `a439dd49468414551a69e8c66625d995b2d5ae37e8caaad2e3a0bc4e167c033a` |
| `docs/packs/PACK-12/PACK-12-FIR-COVERAGE-MATRIX.md`          | `f2d7a87cbe47712b9b1ac3f658c72d9f35f409a814a256bd549a9c7d3e966eae` |
| `docs/packs/PACK-12/PACK-12-REASON-CODE-CATALOG.md`          | `7a8c1ffa279bc180fc82e4a370c75a5e7a114b2765ae3e2e8a68304b85732a2a` |
| `docs/packs/PACK-12/PACK-12-ROLE-SEPARATION-MATRIX.md`       | `846171f1ca39b9c3625e1c42f3cb3f901fb275da173804688830145eeed8207a` |
| `docs/packs/PACK-12/PACK-12-SPECIFICATION.md`                | `f222a9cc36d0315a879d80ec04b72e12d8909cafb7a7f3b7c997843a3d4e9839` |
| `docs/packs/PACK-12/PACK-12-THREAT-MODEL.md`                 | `4b5c6dc7b9f7eea7070d703dbf20dda433cdab132221c9807f387e7b44acd62c` |
| `docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md` | `cf7094df0233d96e56af902847a4abbe090061531ec1879d3366a1eea5e76d31` |
| `services/privileged-access-service/README.md`               | `e2adeef8fc2819cb466da2c436d0ecfe292da30f112bc50e052841b393136330` |

Verified mechanically: with emphasis markers, table padding and line
wrapping normalised away, the word sequence of every one of the 15 files
is **identical** before and after. No wording changed.

---

## Three things the operator needs to know

### 1. One requested path does not exist

The request listed 16 files, including
`docs/handover/PACK-12-FIR-COVERAGE-MATRIX.md`. **That file does not
exist and was not created.** The FIR coverage matrix lives at
`docs/packs/PACK-12/PACK-12-FIR-COVERAGE-MATRIX.md`, which was also on
the list and _was_ formatted. The list therefore named 15 real files, one
of them twice under two directories.

### 2. Prettier version skew — the check was run with 3.8.1, CI pins 3.9.6

`package-lock.json` pins `prettier@3.9.6`. This environment cannot reach
the npm registry (`403 Forbidden` on both the public registry and the
internal mirror), so `npm ci` cannot run and 3.9.6 could not be
installed. The formatting was performed with **Prettier 3.8.1**, which
satisfies the declared `^3.3.0` range but is not the pinned build.

The two versions demonstrably disagree. Three files in the repository
fail `prettier --check` under 3.8.1 while being **byte-identical to the
PACK-11 FINAL PASS**, which passed CI under 3.9.6:

```text
docs/adr/ADR-051-rechenschaftsbericht-lifecycle-snapshot-and-authority-semantics.md
frontend/web-shell/foundation/storage-policy.ts
frontend/web-shell/foundation/types.ts
```

3.8.1 wants to escape `no*` as `no\*` inside a markdown table in the
ADR, and to break a TypeScript union across lines in `types.ts`. 3.9.6
does neither. **These three files were deliberately left untouched** —
they are correct under the version CI actually runs, and "fixing" them
here would have broken them in CI.

Consequently, `prettier --check .` repository-wide still reports those
three under 3.8.1. That is expected and is not a defect in this
correction.

**What this means for confidence:** the 15 corrected files contain no
changes of the classes where 3.8.1 and 3.9.6 were observed to differ (no
escape-sequence changes at all; the changes are emphasis-marker
normalisation `*x*` → `_x_`, table column padding, and blank-line
removal). The risk that 3.9.6 disagrees is low but **not zero**, and it
cannot be eliminated without the pinned binary.

### 3. One change was NOT pure formatting, and had to be prevented

In `docs/adr/README.md` the phrase _"extensible by configuration + ADR
review"_ was wrapped so that `+ ADR review` began a line. Prettier parses
a leading `+` as a **list bullet**: `--write` converted the sentence into
a bulleted list (`- ADR review", and canon 19e.16 ...`) and re-indented
the rest of the paragraph as list continuation. That is a semantic
corruption, not formatting, and it was not shipped.

The fix was to move the line break so the `+` is no longer at the start
of a line — the sentence now reads
`"by configuration + ADR review"` on one line. **No word was changed**,
and Prettier's own output was then taken as-is. This is the same failure
mode PACK-11 hit with a `+` at the start of a hash-formula line, handled
the same way.

---

## Verification performed

```text
prettier --check <the 15 files>   →  All matched files use Prettier code style!
prettier --check .                →  3 pre-existing files flagged (see item 2)
ruff check .                      →  All checks passed
pytest tests/repository tests/contract  →  1280 passed, 5 skipped
```

`make verify` still cannot run here for the reasons in section 5 of
`docs/handover/PACK-12-IMPLEMENTATION-CANDIDATE-REPORT.md`. This
correction does not change that, and claims no PASS.
