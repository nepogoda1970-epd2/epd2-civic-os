# PACK-16A — Handover

```text
PACK-16A NARROW DOCUMENTATION CORRECTION
NO ARCHITECTURE CHANGE
NO PROTOCOL DECISION CHANGE
NO IMPLEMENTATION
REPOSITORY_VERSION 0.15.0
CANON_VERSION 0.8.0
ADR-099 STATUS: PROPOSED
EXTERNAL ARCHITECTURAL REVIEW REQUIRED
NOT FINAL PASS
NOT PRODUCTION READY
NOT LEGALLY ACTIVATED
PACK-16B MUST NOT START
```

Carried forward unchanged from the original candidate:

```text
PACK-16A SPECIFICATION CANDIDATE
PROTOCOL AND BALLOT MODEL SELECTION ONLY
NO PRODUCTION CODE
EXTERNAL CI PASS NOT CLAIMED FOR THIS TREE
PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT
PACK-16B MUST NOT START BEFORE ARCHITECTURAL ACCEPTANCE
```

---

## 0. What this round is

A **narrow documentation correction** following the PACK-16A architectural
audit. The audit returned:

```text
PROTOCOL RESEARCH ............................ PASS
BALLOT MODEL DECISION ........................ PASS FOR REVIEW
PACK-15 BOUNDARY PRESERVATION ................ PASS
ARCHIVE HYGIENE .............................. PASS
ACCEPTANCE MATRIX INTEGRITY .................. NARROW CORRECTION REQUIRED
EVIDENCE INTEGRITY ........................... NARROW CORRECTION REQUIRED
```

Two defects were corrected and nothing else. **PACK-16A was not
re-reviewed, the protocol research was not repeated, no architectural
direction was changed, and PACK-16B was not started.**

### 0.1 Explicit confirmations

```text
EPD2-HOM-1 .................................. UNCHANGED
ElectionGuard 2.1 protocol lineage .......... UNCHANGED
homomorphic exponential-ElGamal ballot model  UNCHANGED
threshold DKG and threshold decryption ...... UNCHANGED
NIZK proof model ............................ UNCHANGED
Benaloh cast-or-challenge model ............. UNCHANGED
no-revoting decision for EPD2-HOM-1 ......... UNCHANGED
EPD2-MIX-1 deferred status .................. UNCHANGED
PACK-15 trust boundary ...................... UNCHANGED
continuation-capability semantics ........... UNCHANGED
no-intermediate-tally invariant ............. UNCHANGED
coercion and receipt limitations ............ UNCHANGED
bulletin-board architectural conclusion ..... UNCHANGED
German legal boundary ....................... UNCHANGED
Canon assessment result ..................... UNCHANGED
FIR statuses ................................ UNCHANGED
REPOSITORY_VERSION 0.15.0 ................... UNCHANGED
CANON_VERSION 0.8.0 ......................... UNCHANGED
ADR-099 status: proposed .................... UNCHANGED
open-decision semantics ..................... UNCHANGED
Master Register ............................. BYTE-IDENTICAL
```

---

## 1. Archive

| Item                             | Value                                                                                                 |
| -------------------------------- | ------------------------------------------------------------------------------------------------------- |
| **New archive filename**         | `EPD2_PACK-16A_VERIFIABLE_VOTING_PROTOCOL_AND_BALLOT_MODEL_SPEC_ADR_CORRECTED_CANDIDATE.zip`          |
| **New archive SHA-256**          | Computed at packaging and published with the delivery message; recomputable by the recipient with `sha256sum` over the delivered file |
| **New archive file count**       | **1195** files in one repository root — **unchanged**                                                 |
| **Corrected from**               | `EPD2_PACK-16A_VERIFIABLE_VOTING_PROTOCOL_AND_BALLOT_MODEL_SPEC_ADR_CANDIDATE.zip`                    |
| **Source candidate SHA-256**     | `c31b7e326d795470cad55a9b17b9ff2f34d4e6dcd9bfc12b4f7542546201e76b` — **verified before use**           |
| **Baseline**                     | `EPD2_PACK-15_VOTING_TRUST_BOUNDARY_ELIGIBILITY_CREDENTIAL_SEPARATION_0.15.0_FINAL_PASS.zip`          |
| **Baseline SHA-256**             | `38697c0a0bca9d211bf9f44ec5c2f7b475d86bd38eb1ccc10bc9521c3f2f087a`                                    |
| **Baseline file count**          | 1172                                                                                                  |

The archive is the confirmed PACK-15 FINAL PASS tree plus twenty-three
added documentation files and one modified register — the same set as the
original candidate, with five of the added documents corrected in place.
Nothing was carried in from any other tree, and **the original candidate
ZIP is not included inside this archive**.

---

## 2. Exact diff against the original PACK-16A candidate

**Added — 0 files. Deleted — 0 files. Modified — 5 files.**

| File                                                    | What changed                                                                                                   |
| ------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| `PACK-16A-ACCEPTANCE-MATRIX.md`                         | §13 summary replaced with the recomputed counts; §13.1 arithmetic check added. **No row status changed**       |
| `PACK-16A-PROTOCOL-EVIDENCE-MATRIX.md`                  | Restructured as the **single canonical Evidence Registry**: eleven fields per entry; the nine legal entries consolidated in; `E-48` recorded as reserved; §2 and §13 counts added |
| `PACK-16A-GERMAN-LEGAL-BOUNDARY.md`                     | §9 converted from a definition table to a **pointer table** that defines nothing. **No legal content, mode, verdict or conclusion changed** |
| `ADR-099-VERIFIABLE-VOTING-PROTOCOL-AND-BALLOT-MODEL.md`| *Evidence standard* section: single-registry statement and corrected counts. **No decision, driver, consequence, residual risk or status changed** |
| `PACK-16A-SPECIFICATION-REPORT.md`                       | Two evidence-count claims corrected                                                                            |
| `PACK-16A-HANDOVER.md`                                  | This document: correction record, corrected archive facts, verification of both defects                        |

**No file outside the set permitted by the correction task was touched.**
`PACK-16A-HANDOVER.md` is listed in that set. **The Master Register is
byte-identical** to the original candidate: it required no correction, so
it received none.

Everything below §2.1 describes the archive's contents relative to the
**PACK-15 baseline**, and is carried forward from the original candidate
unchanged.

### 2.1 Contents relative to the PACK-15 baseline

**Added — 23 files.**

```text
docs/adr/ADR-099-VERIFIABLE-VOTING-PROTOCOL-AND-BALLOT-MODEL.md
docs/packs/PACK-16/PACK-16A-SCOPE-AND-BOUNDARY.md
docs/packs/PACK-16/PACK-16A-PROTOCOL-COMPARISON.md
docs/packs/PACK-16/PACK-16A-PROTOCOL-EVIDENCE-MATRIX.md
docs/packs/PACK-16/PACK-16A-THREAT-MODEL.md
docs/packs/PACK-16/PACK-16A-BALLOT-MODEL-SPECIFICATION.md
docs/packs/PACK-16/PACK-16A-ELECTION-PROFILE-MATRIX.md
docs/packs/PACK-16/PACK-16A-REVOTING-AND-BALLOT-LIFECYCLE.md
docs/packs/PACK-16/PACK-16A-COERCION-AND-RECEIPT-BOUNDARY.md
docs/packs/PACK-16/PACK-16A-BULLETIN-BOARD-REQUIREMENTS.md
docs/packs/PACK-16/PACK-16A-TRUSTEE-AND-CEREMONY-REQUIREMENTS.md
docs/packs/PACK-16/PACK-16A-ROLE-SEPARATION-MATRIX.md
docs/packs/PACK-16/PACK-16A-GERMAN-LEGAL-BOUNDARY.md
docs/packs/PACK-16/PACK-16A-PRIVACY-DATA-FLOW-MATRIX.md
docs/packs/PACK-16/PACK-16A-FAILURE-AND-ABORT-MODEL.md
docs/packs/PACK-16/PACK-16A-ACCESSIBILITY-REQUIREMENTS.md
docs/packs/PACK-16/PACK-16A-REASON-CODE-SPECIFICATION.md
docs/packs/PACK-16/PACK-16A-FIR-COVERAGE-MATRIX.md
docs/packs/PACK-16/PACK-16A-CANON-ASSESSMENT.md
docs/packs/PACK-16/PACK-16A-ACCEPTANCE-MATRIX.md
docs/packs/PACK-16/PACK-16A-OPEN-DECISIONS.md
docs/packs/PACK-16/PACK-16A-SPECIFICATION-REPORT.md
docs/packs/PACK-16/PACK-16A-HANDOVER.md
```

**Modified — 1 file.**

```text
docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md
```

Two changes, both additive:

1. **New section `1.20 Round record — PACK-16A specification and ADR
   (2026-08-01)`**, inserted immediately before `# 2. Current confirmed
   baseline` and after section 1.19. It records the baseline and its
   verified digest, what the round did, the selection, the documents
   added, the FIR treatment, the canon verdict and the prohibitions.
2. **A sequencing note appended inside `FIR-ROADMAP-006`**, after its
   existing scope list and before `FIR-ROADMAP-007`. It records the four
   PACK-16 stages, states that PACK-16A implements nothing in the entry's
   scope, and states that **the status stays `approved` and the target
   version stays `0.16.0`**.

**No prior register content was altered, reordered or removed. No status
value was changed. No identifier was reused. No second register exists.**

**Deleted — 0 files.**

**Source, test, migration, contract, CI and lock-file changes — 0.**

---

## 3. Protocol recommendation

```text
RECOMMENDED PROTOCOL FAMILY
  Homomorphic encrypted ballots with exponential ElGamal, distributed
  threshold key generation and decryption, non-interactive zero-knowledge
  well-formedness proofs, and Benaloh cast-or-challenge, in the lineage of
  the ElectionGuard Design Specification 2.1.0.

RECOMMENDED BOUNDED PROFILE
  EPD2-HOM-1 — cardinal ballots, homomorphic tally.

DEFINED, NOT SELECTED, PROHIBITED PENDING RESEARCH
  EPD2-MIX-1 — ordinal ballots, mixnet tally.

REVOTING
  None in EPD2-HOM-1. Explicitly decided, not deferred.
```

**A specification is selected, not a library.** There is no production-grade
implementation of the selected specification version; that is the largest
engineering risk in the selection and is `OD-P16A-04` and `RR-01`.

**Why this family.** Its declared limitation — it performs no eligibility
and no authentication, and requires them to be established outside it,
asking only that ballots cast not exceed voters entitled — is a description
of the interface PACK-15 already built. The boundary and the protocol were
designed independently and meet without either being bent.

---

## 4. Rejected alternatives

| Family                | Verdict                                 | Recorded reason                                                                                                   |
| --------------------- | --------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| Belenios 3.0/3.1      | **SUITABLE ONLY AS REFERENCE**          | Its credential list pairs voter identity with a voting-side reference — the row PACK-15 §3 forbids; mixnet mode publishes decrypted individual ballots; coercion resistance officially disclaimed |
| Helios v3             | **NOT SUITABLE**                        | Weak Fiat–Shamir still in shipping code; no ballot weeding; n-of-n trustees; voter names beside ciphertexts; authors disclaim high-stakes use |
| Estonian IVXV 1.8.0   | **NOT SUITABLE**                        | Identity↔ciphertext binding stored for the whole period and severed by a trusted offline procedure; no plaintext-knowledge proof; revoting defeats individual verifiability |
| Verificatum VMN 3.1.0 | **SUITABLE ONLY AS REFERENCE**          | Not a voting system; provides no ballot independence on its own; component candidate for the deferred mixnet profile |
| JCJ / Civitas         | **NOT SUITABLE**                        | Untappable-channel assumption; quadratic tallying; fake-credential usability; never deployed; the property itself contested |
| Selene                | **REQUIRES FURTHER RESEARCH**           | Coercion *mitigation* with a collision problem; but lay-comprehensible verifiability is the closest published answer to the German standard |
| BeleniosRF            | **REQUIRES FURTHER RESEARCH**           | Strong receipt-freeness with no voter strategy required; research prototype, not shipped                          |
| VoteAgain             | **NOT SUITABLE**                        | Broken by third-party analysis with no fix proposed; all authorities must be trusted for coercion resistance       |
| A bespoke protocol    | **REFUSED**                             | No cryptographic research capacity; the one risk process cannot mitigate                                          |

---

## 5. Local verification

Performed on the assembled candidate tree.

| Check                                                   | Result                                                                                  |
| ------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| Baseline archive SHA-256 matches the declared digest    | **PASS** — `38697c0a…f087a`                                                             |
| Baseline: one repository root                           | **PASS**                                                                                |
| Baseline: 1172 files, one `uv.lock`, one `package-lock.json`, one Master Register, 0 duplicate paths, 0 nested ZIPs | **PASS**                                     |
| All 22 required PACK-16A documents present              | **PASS**                                                                                |
| `docs/adr/ADR-099-VERIFIABLE-VOTING-PROTOCOL-AND-BALLOT-MODEL.md` path correct | **PASS**                                                          |
| ADR-099 status is `proposed`                            | **PASS**                                                                                |
| One canonical Master Register, at the canonical path    | **PASS**                                                                                |
| Master Register prior content preserved                 | **PASS** — additive only; verified by diff                                              |
| `FIR-UX-011` preserved                                  | **PASS**                                                                                |
| `FIR-OSS-001` … `FIR-OSS-006` preserved                 | **PASS**                                                                                |
| `REPOSITORY_VERSION` unchanged at `0.15.0`              | **PASS** — Python, TypeScript, CHANGELOG                                                |
| `CANON_VERSION` unchanged at `0.8.0`                    | **PASS** — Python, TypeScript, `canon-version.json`                                     |
| `scripts/verify_versions.py`                            | **PASS**                                                                                |
| `scripts/check_repository.py` required and forbidden paths | **PASS**                                                                             |
| No source changes (Python, TypeScript, frontend)        | **PASS** — 0 files                                                                      |
| No test changes                                         | **PASS** — 0 files                                                                      |
| No migration changes                                    | **PASS** — 0 files                                                                      |
| No contract or fixture changes                          | **PASS** — 0 files                                                                      |
| No CI workflow changes                                  | **PASS** — 0 files                                                                      |
| No lock-file changes (`uv.lock`, `package-lock.json`)   | **PASS** — byte-identical                                                               |
| No dependency-graph changes                             | **PASS** — `pyproject.toml`, `package.json` byte-identical                              |
| No duplicate archive paths                              | **PASS**                                                                                |
| No nested ZIP files                                     | **PASS**                                                                                |
| No nested repository                                    | **PASS**                                                                                |
| No forbidden generated directories                      | **PASS** — no `.git`, `.venv`, `node_modules`, `.next`, `__pycache__`, caches           |
| No false implementation claims                          | **PASS** — prohibited-phrase scan over the added documents                              |
| No false legal claims                                   | **PASS** — same scan                                                                    |
| External evidence references resolvable                 | **PASS** — every `[E-nn]` used resolves in the evidence matrix                          |
| Markdown formatting / link checks                       | **PARTIAL** — internal cross-references verified; no Markdown linter or link checker is provisioned in this repository |
| Application test suite                                  | **NOT RUN** — the application tree is unchanged, so it is not required for this round   |

```text
PARTIAL LOCAL VERIFICATION ONLY
EXTERNAL ARCHITECTURAL REVIEW REQUIRED
```

**No result above is fabricated.** Where a check could not be performed it
says so.

### 5.1 Defect 1 — Acceptance Matrix summary

**Method.** The status cell of every `AC-P16A-nnn` row was extracted
programmatically and counted. **The rows were treated as the source of
truth and the summary was recomputed from them**; no status was changed to
reconcile with the previously published summary.

**Verification command.**

```text
python3 - <<'PY'
import re, collections
VOCAB = ["SATISFIED BY SPECIFICATION","PARTIALLY SATISFIED","SELECTED FOR REVIEW",
         "DEFERRED","OPEN","BLOCKED","NOT APPLICABLE"]
rows = []
for line in open('docs/packs/PACK-16/PACK-16A-ACCEPTANCE-MATRIX.md'):
    m = re.match(r'^\|\s*`(AC-P16A-\d+)`\s*\|', line)
    if not m: continue
    cells = [c.strip() for c in line.strip().strip('|').split('|')]
    rows.append((m.group(1), cells[8].replace('*','').strip()))
ids = [r[0] for r in rows]
nums = sorted(int(i.split('-')[-1]) for i in ids)
c = collections.Counter(s for _, s in rows)
print("rows:", len(rows))
print("duplicate IDs:", [k for k,v in collections.Counter(ids).items() if v>1])
print("missing IDs:", [n for n in range(1, max(nums)+1) if n not in nums])
print("outside vocabulary:", [r for r in rows if r[1] not in VOCAB])
for v in VOCAB: print(f"{v}: {c.get(v,0)}")
print("sum:", sum(c.values()))
PY
```

**Output.**

```text
rows: 96
duplicate IDs: []
missing IDs: []
outside vocabulary: []
SATISFIED BY SPECIFICATION: 71
PARTIALLY SATISFIED: 14
SELECTED FOR REVIEW: 3
DEFERRED: 4
BLOCKED: 3
OPEN: 0
NOT APPLICABLE: 1
sum: 96
```

**Result — Variant A applied.**

| Check                                             | Result                                  |
| ------------------------------------------------- | ----------------------------------------- |
| Requirement rows                                  | **96** — unchanged                      |
| `sum(status counts) == requirement rows`          | **96 == 96 ✓**                          |
| Status values outside the permitted vocabulary    | **0**                                   |
| Duplicate Requirement IDs                         | **0**                                   |
| Missing Requirement IDs in `AC-P16A-001…096`      | **0**                                   |
| Summary matches row-level statuses exactly        | **yes**                                 |
| Previously published summary                      | 62/16/4/5/4/0/1, summing to **92 ≠ 96** |
| **Row statuses changed**                          | **none — 0 rows**                       |

**Rows whose status was corrected: none.** The row-level statuses were
independently recounted and found correct, so no `requirement ID / old
status / new status / reason` entries arise. The published summary had been
written as an estimate rather than derived from the rows; it has been
replaced by the count, and §13.1 of the matrix carries the arithmetic check
that prevents the two diverging again.

### 5.2 Defect 2 — single canonical Evidence Registry

**What was wrong.** Nine legal evidence entries — `E-41`, `E-49` … `E-56` —
were defined only in `PACK-16A-GERMAN-LEGAL-BOUNDARY.md` §9, while
documents asserted that all evidence appears in the Evidence Matrix. The
identifier `E-48` was absent from the sequence, and the published count of
"56 evidence entries" counted numeric slots, omitted the four sub-lettered
entries and counted the missing slot as a source.

**What was done.**

1. `PACK-16A-PROTOCOL-EVIDENCE-MATRIX.md` is now the **single canonical
   registry**, with eleven fields per entry: source title; author or
   issuing institution; version or publication date; source type; URL or
   stable reference; relevant section or page; property supported; scope of
   support; limitations; documents using the evidence; and the `P` / `I` /
   `L` / `INF` kind.
2. The nine legal entries were consolidated into it, **content, scope and
   conclusions unchanged**.
3. `PACK-16A-GERMAN-LEGAL-BOUNDARY.md` §9 is now a **pointer table** that
   defines nothing and explicitly directs to the canonical registry.
4. **`E-48` — Variant A applied.** No lost source was found; it is recorded
   as `RESERVED / INTENTIONALLY UNUSED`, with the note that no substantive
   claim relies on it and that it must not be reused without an explicit
   registry update. **`E-49` … `E-56` were not renumbered**, because they
   are cited across eight documents and renumbering would create reference
   churn and a risk of mis-pointing a legal citation.

**Verification command.** The extraction distinguishes a **definition** (an
entry heading in the canonical registry) from a **reference** (a `` `[E-nn]` ``
citation) from a bare **mention** in prose.

```text
python3 - <<'PY'
import re, os, collections
roots = ['docs/packs/PACK-16',
         'docs/adr/ADR-099-VERIFIABLE-VOTING-PROTOCOL-AND-BALLOT-MODEL.md']
files = []
for r in roots:
    files += [r] if os.path.isfile(r) else [os.path.join(r,f) for f in sorted(os.listdir(r))]
REF = re.compile(r'`\[(E-\d+[a-z]?)\]`')                 # a citation
DEF = re.compile(r'^#####\s+`(E-\d+[a-z]?)`')            # a definition
refs, defs = collections.defaultdict(set), collections.defaultdict(list)
for f in files:
    for line in open(f):
        for m in REF.findall(line): refs[m].add(os.path.basename(f))
        d = DEF.match(line)
        if d: defs[d.group(1)].append(os.path.basename(f))
print("definitions:", len(defs))
print("multi-defined:", {k:v for k,v in defs.items() if len(v)>1})
print("defined outside the registry:",
      [k for k,v in defs.items() if any(not b.startswith('PACK-16A-PROTOCOL-EVIDENCE') for b in v)])
print("references:", len(refs))
print("unresolved:", sorted(set(refs) - set(defs)))
print("defined, never referenced:", sorted(set(defs) - set(refs)))
PY
```

**Output.**

```text
definitions: 60
multi-defined: {}
defined outside the registry: []
references: 58
unresolved: []
defined, never referenced: ['E-47', 'E-48']
```

**Result.**

| Check                                          | Result                                                                 |
| ---------------------------------------------- | ------------------------------------------------------------------------ |
| Canonical evidence registries                  | **1**                                                                  |
| Duplicate Evidence definitions                 | **0**                                                                  |
| Conflicting Evidence definitions               | **0**                                                                  |
| Evidence IDs with two different sources        | **0**                                                                  |
| Evidence IDs defined outside the registry      | **0**                                                                  |
| Unresolved Evidence references                 | **0**                                                                  |
| Orphaned references                            | **0**                                                                  |
| `E-49` … `E-56` canonically defined            | **yes** — registry §9                                                  |
| `E-48` explicitly resolved                     | **yes** — `RESERVED / INTENTIONALLY UNUSED`, registry §10               |
| Reserved IDs explicitly marked                 | **yes**                                                                |
| Definitions not cited elsewhere                | **2** — `E-47` (deliberate context, registry §8) and `E-48` (reserved) |

**Counts, stated so that the arithmetic is checkable:**

```text
allocated Evidence IDs .................. 60
substantive evidence definitions ........ 59
reserved Evidence IDs ...................  1   (E-48)
highest Evidence ID ..................... E-56
unique references resolved .............. 58
unresolved Evidence references ..........  0
conflicting Evidence definitions ........  0

reconciliation:
  numeric slots E-01 … E-56 ............. 56
    reserved (E-48) ......................  1
    substantive numbered ................. 55
  sub-lettered (E-10a, E-16a, E-28a, E-28b)  4
  substantive definitions = 55 + 4 ...... 59
  allocated = 59 + 1 reserved ........... 60
```

The extractor reports **60 definitions** because it counts the reserved
entry's heading; **59 of them are substantive** and one is the reserved
slot. `58 = 59 − 1` because `E-47` is deliberately uncited.

### 5.3 Repository integrity after the correction

| Check                                                | Result                                                       |
| ---------------------------------------------------- | -------------------------------------------------------------- |
| `REPOSITORY_VERSION` unchanged at `0.15.0`           | **PASS**                                                     |
| `CANON_VERSION` unchanged at `0.8.0`                 | **PASS**                                                     |
| `ADR-099` remains `proposed`                         | **PASS**                                                     |
| Source changes                                       | **0**                                                        |
| Test changes                                         | **0**                                                        |
| Migration changes                                    | **0**                                                        |
| CI workflow changes                                  | **0**                                                        |
| `uv.lock` unchanged                                  | **PASS** — byte-identical                                    |
| `package-lock.json` unchanged                        | **PASS** — byte-identical                                    |
| Dependency graph unchanged                           | **PASS** — `pyproject.toml`, `package.json` byte-identical   |
| **Master Register preserved**                        | **PASS** — byte-identical; no correction was required        |
| Canon files unchanged                                | **PASS** — byte-identical                                    |
| Files changed outside the permitted set              | **0**                                                        |
| `scripts/verify_versions.py`                         | **PASS**                                                     |
| `scripts/check_repository.py`                        | **PASS** — 983 / 983 required paths                          |

---

## 6. Canon assessment

```text
CANON CLARIFICATION REQUIRED
CANON AMENDMENT NOT REQUIRED AND NOT PROPOSED
CANON_VERSION REMAINS 0.8.0 — canon files untouched
```

Six clarifications `CQ-01` … `CQ-06`. Three amendment **candidates**
recorded, not proposed: a bulletin-board publication aggregate (canon 19a.1
forbids `PublicLedgerEntry → VoteEnvelope`, and that prohibition stands and
is not challenged), a trustee/key-ceremony evidence aggregate, and a mirror
registry. Owning rounds: PACK-16B and PACK-16C.

---

## 7. FIR summary

| Measure                                            | Value                                          |
| -------------------------------------------------- | ---------------------------------------------- |
| Marked `implemented`                               | **0**                                          |
| Created                                            | **0**                                          |
| Removed, renamed or downgraded                     | **0**                                          |
| Specified                                          | 20                                             |
| Deferred with a named owner                        | 8                                              |
| Blocked pending legal assessment                   | 1 — `FIR-CAND-001`                             |
| `FIR-ROADMAP-006` status                           | **unchanged `approved`**, target `0.16.0`      |
| `FIR-INV-002`                                      | **not closed; cannot be closed by this round** |
| `FIR-UX-011`, `FIR-OSS-001` … `FIR-OSS-006`        | **preserved unchanged**                        |
| Master Register copies in the archive              | **1**                                          |

---

## 8. Open decisions

Twelve, each with an owner and a closing round: `OD-P16A-01` revoting for
future profiles · `OD-P16A-02` the mixnet profile · `OD-P16A-03` parameters
against BSI TR-02102-1 (2026-01) · `OD-P16A-04` implementation selection ·
`OD-P16A-05` specification stewardship · `OD-P16A-06` formal proof of the
composed profile · `OD-P16A-07` retention of the published record ·
`OD-P16A-08` licensing interaction · `OD-P16A-09` scope-level channel
reconciliation · `OD-P16A-10` lay-comprehensible verifiability ·
`OD-P16A-11` what *Stand der Technik* requires · `OD-P16A-12` the canon
repository-compatibility bound.

Inherited and still open: `OD-P15-05` (re-owned to PACK-16B),
`OD-P15-06`, `OD-P15-08`.

**None blocks architectural acceptance of PACK-16A.**

---

## 9. Known limitations

```text
No production-grade implementation of the selected specification exists.
Ranked, STV, Condorcet and Majority Judgment ballots are unsupported.
Cast-as-intended relies on challenge, which is probabilistic and
   depends on voluntary take-up.
Individual verifiability take-up is empirically low — 9.9 % at best in
   the most mature deployment in the world.
Voter-device compromise is out of scope for every candidate assessed.
Timing correlation between redemption and casting is reduced and
   bounded, not eliminated.
Small electorates weaken every unlinkability property, and no
   cryptography changes this.
Coercion during casting and forced abstention are UNMITIGATED.
Pre-closure public scrutiny of the ballot set is given up in order to
   satisfy NO INTERMEDIATE TALLY.
The bulletin board is not provided by the selected family and must be
   built entirely by EPD².
There is no symbolic or cryptographic proof of the profile as composed.
Eligibility verifiability is weaker than Council of Europe Standard 18.
```

---

## 10. Residual risks

`RR-01` … `RR-15`, listed in
`PACK-16A-BALLOT-MODEL-SPECIFICATION.md` §11 and
`PACK-16A-BULLETIN-BOARD-REQUIREMENTS.md` §7. The three graded **high**:
no production-grade implementation (`RR-01`); device compromise out of
scope (`RR-05`); small electorates weaken every unlinkability property
(`RR-07`); plus `RR-09` no formal proof of the composed profile and
`RR-10` the board is entirely EPD²'s to build.

---

## 11. Source and evidence list

Fifty-six entries in `PACK-16A-PROTOCOL-EVIDENCE-MATRIX.md`, plus the legal
sources in `PACK-16A-GERMAN-LEGAL-BOUNDARY.md` §9. Primary categories:

```text
Official protocol specifications — ElectionGuard 2.1.0; Belenios 3.0;
   Helios v3/v4; IVXV protocols and architecture 1.8.0; Verificatum
   VMN 3.1.0 user manual and standalone-verifier specification
Peer-reviewed papers — USENIX Security 2024, 2020, 2008; IEEE CSF 2018;
   IEEE S&P 2008; ASIACRYPT 2012; CCS 2016, 2014; FC 2016, 2022, 2023;
   E-Vote-ID 2016, 2017, 2023; AFRICACRYPT 2010; WPES 2005; SSTIC 2024
Official caveat and limitation documents — "Known caveats of Belenios
   3.1" (28 April 2025); Helios "Attacks and Defenses"; Verificatum
   FAQ and manual warnings
Third-party security disclosures — Lewis, Pereira, Teague (March 2019)
Binding regulation — Swiss OEV/VEleS SR 161.116
Constitutional law — BVerfG 2 BvC 3/07, 2 BvC 4/07, BVerfGE 123, 39
German technical guidance — BSI TR-02102-1 (2026-01); BSI-CC-PP-0121-2024;
   BSI TR-03169; BSI E2E-verifiability guidance (25 April 2025)
German party and electoral law — PartG §§ 9, 15, 17 (11. PartGÄndG,
   in force 05.03.2024); BWahlG §§ 21(3), 27(5); Bundeswahlleiterin
   Leitfaden Aufstellungsversammlung (September 2024); Bundestag WD
   opinions; Ausschussdrucksache 20(4)340-A
Intergovernmental standards — CoE CM/Rec(2017)5; OSCE/ODIHR
   ELE-EST/527/2025
```

**No marketing material is used as evidence. Items that could not be
verified are marked UNVERIFIED and support no conclusion. Where sources
contradict each other, the contradiction is shown rather than resolved by
assertion.**

---

## 12. Recommended PACK-16B scope

```text
PACK-16B — Cryptographic Parameters, Key Ceremony and Trustee Architecture

Choose the group, key size and hash; justify against BSI TR-02102-1
   (2026-01) and declare any divergence from the selected specification's
   fixed parameters — OD-P16A-03
Choose k and n within TP-01 … TP-07
Design the key ceremony to KC-01 … KC-20
Publish parameter provenance an outside party can reproduce — BM-33, KC-19
Specify the custody medium and the trustee appointment procedure
Specify test-key isolation, demonstrably — KC-20
Re-own and close OD-P15-05
Address OD-P16A-05 (specification stewardship)
Assess canon amendment candidate CA-02
NO key escrow, NO recovery guardian, NO administrative decryption path
Specification and ADR only; no implementation; no version bump
```

## 13. Recommended PACK-16C scope

```text
PACK-16C — Casting, Verification, Receipt and Bulletin-Board Specification

Specify the bulletin board to BB-01 … BB-37, including the checkpoint
   scheme, the mirror protocol and the batch/delay parameters of BB-11
Specify the casting protocol messages and the election-record format
Specify the Verification Client on a third origin — BB-14
Specify the receipt surface and its governed content
Write the verifier prose sufficient for an independent verifier — BB-34
Answer OD-P16A-10 (lay-comprehensible verifiability)
Pursue OD-P16A-06 (symbolic and cryptographic proof of the composed
   profile) with external cryptographic review
Register the reason-code namespaces
Specify the evidence-bundle extension for the ballot domain
Assess canon amendment candidates CA-01 and CA-03
Specification and ADR only; no implementation; no version bump
```

---

## 14. What the recipient is asked to do

1. Audit this archive against the completion criteria of the round
   definition.
2. Decide **architectural acceptance or rejection of `ADR-099`**. It is
   `proposed` and must not be recorded as `accepted` by packaging,
   verification or the passage of time.
3. If accepted, authorise **PACK-16B** and nothing further.
4. If rejected, state which of the six invalidating conditions in
   `PACK-16A-BALLOT-MODEL-SPECIFICATION.md` §12 applies, so that the
   re-opening is scoped.

`PACK-16A-SPECIFICATION-REPORT.md` §7 names the five points a reviewer
should attack first.

```text
NOT FINAL PASS · NOT PRODUCTION READY · NOT LEGALLY ACTIVATED
EXTERNAL CI PASS NOT CLAIMED FOR THIS TREE
PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT
PACK-16B MUST NOT START BEFORE ARCHITECTURAL ACCEPTANCE
```
