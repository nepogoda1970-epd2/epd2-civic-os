#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OLD_MATRIX = ROOT / "docs/roadmap/EPD2_BSI_CC_PP_0121_CONFORMANCE_MATRIX.md"
NEW_DIR = ROOT / "docs/security/bsi"
NEW_MATRIX = NEW_DIR / "EPD2_BSI_CC_PP_0121_CERTIFICATION_READINESS_GAP_MATRIX_0.1.md"
QUESTIONNAIRE = NEW_DIR / "EPD2_BSI_CC_PP_0121_P0_PRE_EVALUATION_QUESTIONNAIRE_0.1.md"
BOOTSTRAP = ROOT / "docs/roadmap/EPD2_BSI_VOTING_BOOTSTRAP_RULE.md"
ENTRYPOINT = ROOT / "docs/roadmap/EPD2_PROJECT_ENTRYPOINT.md"
MASTER = ROOT / "docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md"
PCR = ROOT / "docs/roadmap/EPD2_PROGRAM_CONTROL_REGISTER.md"
EVIDENCE = ROOT / "docs/roadmap/EPD2_BSI_MASTER_UPDATE_EVIDENCE.json"

OLD_MATRIX_PATH = "docs/roadmap/EPD2_BSI_CC_PP_0121_CONFORMANCE_MATRIX.md"
NEW_MATRIX_PATH = "docs/security/bsi/EPD2_BSI_CC_PP_0121_CERTIFICATION_READINESS_GAP_MATRIX_0.1.md"
OLD_FIR = "FIR-BSI-001"
NEW_FIR = "FIR-VOTE-BSI-001"


def fail(message: str) -> None:
    raise SystemExit(message)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if text.count(old) != 1:
        fail(f"{label}: expected exactly one source occurrence, found {text.count(old)}")
    return text.replace(old, new, 1)


def main() -> int:
    NEW_DIR.mkdir(parents=True, exist_ok=True)

    before_master = subprocess.check_output(
        [
            "git",
            "show",
            "origin/main:docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md",
        ]
    )

    matrix = OLD_MATRIX.read_text(encoding="utf-8")
    matrix = replace_once(
        matrix,
        "# EPD² — BSI-CC-PP-0121 Certification-Readiness Matrix",
        "# EPD² — BSI-CC-PP-0121 Certification Readiness / Gap Matrix",
        "matrix title",
    )
    matrix = replace_once(
        matrix,
        "| M-31 | Product/legal scope | **ORANGE** | Define in-scope certification product/use case. PP-0121 certification must not be marketed as general approval for statutory political elections. |",
        "| M-31 | Product/legal scope | **ORANGE** | EPD² must not assume that internal party elections are either in-scope or out-of-scope without written BSI/ITSEF classification. PP-0121 certification must not be marketed as general approval for statutory political elections. |",
        "M-31",
    )
    freeze_anchor = (
        "Before changing that invariant for certification purposes, obtain a written "
        "pre-evaluation position from a recognised Common Criteria evaluation facility "
        "on this question:"
    )
    matrix = replace_once(
        matrix,
        freeze_anchor,
        "**Hard architectural freeze gate:** until that written ITSEF position is obtained, "
        "no implementation, certification-readiness change or governance update may introduce "
        "a persistent member/person identifier into the voting domain, or otherwise weaken the "
        "`no persistent member/person identifier inside voting domain` invariant merely to match "
        "PP terminology.\n\n"
        + freeze_anchor,
        "P0.1 freeze",
    )
    NEW_MATRIX.write_text(matrix, encoding="utf-8")
    OLD_MATRIX.unlink()

    bootstrap = BOOTSTRAP.read_text(encoding="utf-8")
    bootstrap = bootstrap.replace(OLD_MATRIX_PATH, NEW_MATRIX_PATH).replace(OLD_FIR, NEW_FIR)
    bootstrap = replace_once(
        bootstrap,
        "- no civil/member/account identity or persistent member identifier may be introduced into the voting domain without an explicit governed architecture decision;",
        "- no civil/member/account identity or persistent member/person identifier may be introduced into the voting domain; before a written ITSEF P0 position exists, this is a hard architectural freeze gate and cannot be relaxed merely for PP alignment;",
        "bootstrap identity freeze",
    )
    BOOTSTRAP.write_text(bootstrap, encoding="utf-8")

    entrypoint = ENTRYPOINT.read_text(encoding="utf-8")
    entrypoint = entrypoint.replace(OLD_MATRIX_PATH, NEW_MATRIX_PATH).replace(OLD_FIR, NEW_FIR)
    ENTRYPOINT.write_text(entrypoint, encoding="utf-8")

    master = MASTER.read_text(encoding="utf-8")
    master = master.replace(OLD_MATRIX_PATH, NEW_MATRIX_PATH).replace(OLD_FIR, NEW_FIR)
    maintenance_pattern = re.compile(r"^\*\*Maintenance copy:\*\* V25 —.*$", re.MULTILINE)
    maintenance_line = (
        "**Maintenance copy:** V26 — BSI CC PP-0121 certification-readiness governance refinement "
        "(2026-08-30), layered losslessly on the V25 canonical reconciliation. V25 lineage and all "
        "existing FIRs remain preserved; V26 adds/refines only `FIR-VOTE-BSI-001` and its governed "
        "certification-readiness references."
    )
    master, count = maintenance_pattern.subn(maintenance_line, master, count=1)
    if count != 1:
        fail(f"Master maintenance line replacement count={count}")

    fir_block = """## FIR-VOTE-BSI-001 — BSI CC PP-0121 Certification Readiness

- **Status:** `approved`
- **Priority:** `critical`
- **Domain:** voting security / Common Criteria / BSI certification readiness / assurance evidence
- **Target:** bounded EPD² Voting TOE and every future Voting-affecting API, INFRA, OPS, CTRL, FRONT and SEC change
- **Governed matrix:** `docs/security/bsi/EPD2_BSI_CC_PP_0121_CERTIFICATION_READINESS_GAP_MATRIX_0.1.md`
- **P0 questionnaire:** `docs/security/bsi/EPD2_BSI_CC_PP_0121_P0_PRE_EVALUATION_QUESTIONNAIRE_0.1.md`

### Normative requirement

EPD² Voting must preserve an architecture capable of becoming a bounded Common Criteria TOE conformant to the then-current applicable BSI online-voting Protection Profile, presently BSI-CC-PP-0121, without weakening existing voting privacy, unlinkability or WS-03 isolation invariants.

This FIR is a certification-readiness obligation, not a certification or conformance claim. It does not make EPD² Voting `BSI-certified`, `BSI compliant`, `CC compliant`, `EAL4`, production ready or legally activated.

### Hard P0 architectural freeze

Until a recognised Common Criteria evaluation facility provides a written P0 position on the PP-0121 identity model, EPD² must not weaken the invariant `no persistent member/person identifier inside voting domain` merely to match PP terminology. In particular, civil identity, member identity, account identity, persistent member/person identifiers and reverse-resolvable identity references remain prohibited inside the voting domain.

A negative evaluator answer does not itself authorize weakening that invariant. It triggers a governed TOE/certification-strategy decision.

EPD² must not assume that internal party elections are either in-scope or out-of-scope without written BSI/ITSEF classification.

### Mandatory certification-readiness gates

```text
ITSEF P0 feasibility
→ TOE boundary
→ Security Target
→ P1 closure
→ EAL4 + ALC_FLR.2 evidence
→ independent evaluation
→ BSI decision
```

The gates are ordered. Preparatory work may proceed in parallel where it does not pre-judge an unresolved earlier gate, but no later gate may be claimed complete on internal evidence alone where external evaluation is required.

### Required P0 questions

1. Can PP-0121 `User Identity`, `voters' register` and individual `voting record` be represented by a non-identifying, election-scoped, single-use eligibility representation that cannot be correlated to the ballot or to civil/member identity while preserving strict conformance?
2. For EPD², should the evaluation target be a central/single-component Voting TOE or a multi-component Voting TOE using the PP multi-component package?
3. How should internal party election use cases be classified against the stated `non-political elections` scope before any product-scope claim is made?

### Acceptance criteria

`FIR-VOTE-BSI-001` is not implemented merely because this FIR, the readiness matrix or the questionnaire exists. It may advance only on explicit evidence that:

- the written P0 evaluator position is recorded;
- the exact TOE boundary is frozen;
- a Security Target maps the applicable PP requirements under strict conformance;
- every claimed SFR/SAR has maintained design/implementation/test/evidence traceability;
- P1 production gaps are closed for the candidate TOE;
- the required EAL4 + ALC_FLR.2 assurance evidence exists;
- independent testing/vulnerability analysis findings are closed as required; and
- a BSI certification decision exists for a fixed product/version/configuration before any certification claim is made.

"""
    fir_pattern = re.compile(
        r"^## FIR-VOTE-BSI-001 — BSI CC PP-0121 Certification Readiness\n.*?(?=^## |\Z)",
        re.MULTILINE | re.DOTALL,
    )
    master, count = fir_pattern.subn(fir_block, master, count=1)
    if count != 1:
        fail(f"FIR block replacement count={count}")
    if master.count("## FIR-VOTE-BSI-001 —") != 1:
        fail("FIR-VOTE-BSI-001 heading must occur exactly once")
    if OLD_FIR in master:
        fail("legacy FIR-BSI-001 remains in Master")
    MASTER.write_text(master, encoding="utf-8")

    pcr = PCR.read_text(encoding="utf-8")
    pcr = replace_once(
        pcr,
        "Current Master maintenance level established by project governance work: **V25**,",
        "Current Master maintenance level established by project governance work: **V26**,",
        "PCR Master maintenance level",
    )
    marker = "**API-02 execution-state reconciliation (2026-08-27):**"
    v26_note = (
        "**Documentation-only V26 BSI certification-readiness governance update (2026-08-30):** "
        "`FIR-VOTE-BSI-001 — BSI CC PP-0121 Certification Readiness` is recorded as an approved "
        "critical future requirement. The BSI/Common Criteria workstream is permitted only as "
        "**`PREPARATORY PARALLEL WORK / NOT CERTIFIED`**. It changes no DATA/API/INFRA/OPS/CTRL/FRONT/SEC/PILOT "
        "stage status, does not open SEC, and is not a BSI/CC conformance or certification claim. "
        "The mandatory readiness sequence is `ITSEF P0 feasibility → TOE boundary → Security Target → P1 closure "
        "→ EAL4 + ALC_FLR.2 evidence → independent evaluation → BSI decision`. Until the written ITSEF P0 "
        "position exists, `no persistent member/person identifier inside voting domain` is a hard architectural "
        "freeze gate and may not be weakened merely for PP alignment. Internal party-election scope must not be "
        "assumed either in-scope or out-of-scope without written BSI/ITSEF classification. Governed matrix: "
        "`docs/security/bsi/EPD2_BSI_CC_PP_0121_CERTIFICATION_READINESS_GAP_MATRIX_0.1.md`.\n\n"
    )
    if "Documentation-only V26 BSI certification-readiness governance update" not in pcr:
        if marker not in pcr:
            fail("PCR V26 insertion marker not found")
        pcr = pcr.replace(marker, v26_note + marker, 1)

    pilot_row = (
        "| PILOT | `PARALLEL_DEVELOPMENT_EXISTS` | PILOT-01…05 have existing lineage/work. "
        "Exact stage state is governed below. |"
    )
    bsi_row = (
        "| BSI / CC readiness | `PREPARATORY PARALLEL WORK / NOT CERTIFIED` | P0 feasibility, TOE/ST "
        "preparation and assurance planning may proceed in parallel. This opens no SEC stage, changes no "
        "implementation-stage status and creates no certification claim. Hard P0 identity freeze applies. |"
    )
    if bsi_row not in pcr:
        if pilot_row not in pcr:
            fail("PCR program-layer insertion row not found")
        pcr = pcr.replace(pilot_row, bsi_row + "\n" + pilot_row, 1)
    PCR.write_text(pcr, encoding="utf-8")

    QUESTIONNAIRE.write_text(
        """# EPD² — BSI-CC-PP-0121 P0 Pre-Evaluation Questionnaire

**Version:** 0.1  
**Date:** 2026-08-30  
**Status:** PRE-EVALUATION QUESTION SET — NOT A CONFORMANCE OR CERTIFICATION CLAIM  
**Intended recipient:** recognised Common Criteria evaluation facility / ITSEF able to assess BSI-CC-PP-0121 feasibility

## 1. Purpose

EPD² is preparing a bounded certification-readiness workstream for its Voting subsystem against the then-current applicable BSI online-voting Protection Profile, presently BSI-CC-PP-0121. Before production architecture is changed for certification purposes, EPD² requests a written pre-evaluation position on two architecture-defining questions and one scope-classification question.

This questionnaire is intentionally limited to P0 feasibility. It is not a request for a formal Common Criteria evaluation, does not claim strict conformance, and does not ask the evaluator to accept unimplemented security functions.

## 2. Existing EPD² privacy boundary

The current EPD² voting boundary is intentionally identity-minimising:

```text
identity / membership
→ eligibility decision
→ minimal election-scoped single-use continuation capability
→ voting domain
→ encrypted ballot
```

The voting domain is designed not to receive civil identity, member identity, account identity, a persistent member/person identifier or a reverse-resolvable identity reference. The continuation capability is not intended to become a ballot identifier, credential identifier or reusable cross-domain identity session. Identity-side and ballot-side records must not become pairable through ordinary application or infrastructure metadata.

This privacy property is governed as a hard architectural invariant. EPD² does not want to weaken it merely to imitate a conventional voter-register implementation if PP-0121 can be satisfied while preserving the stronger separation.

## 3. Question A — PP identity model under strict conformance

BSI-CC-PP-0121 models voter identification/authentication, a voters' register, User Identity/security attributes and an individual voting record that changes after successful voting. EPD² requests a written position on the following.

**A1.** Under strict PP-0121 conformance, may the TOE represent the required voter-related concepts using a non-identifying, election-scoped, single-use eligibility representation, provided the representation supports the required eligibility/one-vote security functions but cannot be correlated to the ballot or reverse-resolved to civil/member identity inside the voting domain?

**A2.** If yes, what minimum semantics/evidence would the evaluator expect for `User Identity`, the voters' register and the voting record in the Security Target and TOE design? May the authoritative civil/member identity and membership register remain outside the Voting TOE while the TOE receives only the minimal election-scoped representation needed to establish eligibility and prevent a second effective vote?

**A3.** If no, which mandatory PP element prevents that representation, and would the evaluator recommend changing the TOE boundary rather than weakening ballot unlinkability? Please identify whether the issue is best addressed by including an identity/eligibility component inside a multi-component TOE, by another PP-conformant construction, or by choosing a different certification strategy.

**Requested output for Question A:** a short written feasibility position sufficient to decide whether EPD² may preserve the current `no persistent member/person identifier inside voting domain` architecture during Security Target drafting.

## 4. Question B — preferred TOE boundary

EPD² Civic OS is broader than the voting product intended for certification. The certification target should remain bounded to the Voting subsystem and the security-critical components necessary for that TOE.

Two candidate models are under consideration:

1. **Central / single-component Voting TOE:** identity, membership and general Civic OS functions remain outside the TOE; an eligibility boundary provides only the minimal election-scoped authorization needed by the Voting TOE.
2. **Multi-component Voting TOE:** selected voting and/or eligibility components form one evaluated TOE, with the PP multi-component trusted-channel package applied between relevant components.

**B1.** Which model appears more natural for PP-0121 strict conformance given the identity-minimising boundary above?

**B2.** If a multi-component TOE is preferable, which components would the evaluator expect to be inside the TOE at minimum, and which trust/channel interfaces should be treated as TSF interfaces or otherwise security-relevant?

**B3.** Which model is likely to minimize avoidable evaluation complexity without requiring EPD² to weaken unlinkability, independent verification or no-intermediate-tally invariants?

**Requested output for Question B:** a recommended candidate TOE topology to use as the starting point for `EPD2_BSI_TOE_BOUNDARY.md` and the first Security Target draft.

## 5. Scope-classification question — internal party elections

The Protection Profile is expressly framed for non-political elections. EPD² does not assume that an internal political-party election is automatically in-scope or automatically out-of-scope.

**C1.** Before EPD² selects a concrete certification product/use case, how should internal party elections be classified against the stated PP-0121 scope? If this classification requires a BSI position rather than an ITSEF-only interpretation, please identify the appropriate escalation path.

The requested answer is classification guidance only. EPD² will not market PP-0121 certification as general approval for statutory/public political elections.

## 6. Constraints not offered for relaxation during P0

The P0 discussion should assume that EPD² intends to preserve the following stronger project invariants unless a later explicit governance decision changes strategy:

- no persistent civil/member/person identity inside the voting domain;
- ballot secrecy and identity↔ballot unlinkability;
- no intermediate tally;
- independent/public verification of the election record;
- cryptographic truth/verifier semantics remain inside the Open Trust Core;
- certification-readiness evidence does not substitute for end-to-end verifiability.

A written answer that identifies a genuine strict-conformance conflict is welcome; such a conflict will be treated as a certification-strategy/TOE decision, not as automatic authorization to weaken these invariants.

## 7. Expected next step after the written P0 response

After the written P0 response, EPD² will choose and freeze a candidate TOE boundary, prepare a Security Target draft, map the applicable PP SFR/SAR set, and then close production/security/assurance gaps in the governed order:

```text
ITSEF P0 feasibility
→ TOE boundary
→ Security Target
→ P1 closure
→ EAL4 + ALC_FLR.2 evidence
→ independent evaluation
→ BSI decision
```

No formal certification claim will be made before the final BSI decision for a fixed product/version/configuration.
""",
        encoding="utf-8",
    )

    after_master = MASTER.read_bytes()
    evidence_payload = {
        "schema": "epd2.bsi.master-update-evidence.v2",
        "effective_date": "2026-08-30",
        "claim": "GOVERNANCE_REGISTRATION_ONLY_NOT_BSI_CC_CONFORMANCE",
        "master_path": "docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md",
        "before_sha256": hashlib.sha256(before_master).hexdigest(),
        "before_size": len(before_master),
        "after_sha256": hashlib.sha256(after_master).hexdigest(),
        "after_size": len(after_master),
        "fir_vote_bsi_001_heading_count": master.count("## FIR-VOTE-BSI-001 —"),
        "legacy_fir_bsi_001_present": OLD_FIR in master,
        "fir_oss_007_preserved": "FIR-OSS-007" in master,
        "program_control_modified": True,
        "matrix_path": NEW_MATRIX_PATH,
        "p0_questionnaire_path": "docs/security/bsi/EPD2_BSI_CC_PP_0121_P0_PRE_EVALUATION_QUESTIONNAIRE_0.1.md",
        "source_main_commit": subprocess.check_output(
            ["git", "rev-parse", "origin/main"], text=True
        ).strip(),
    }
    EVIDENCE.write_text(
        json.dumps(evidence_payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    if not NEW_MATRIX.is_file() or OLD_MATRIX.exists():
        fail("matrix move failed")
    if OLD_FIR in MASTER.read_text(encoding="utf-8"):
        fail("legacy FIR remains")
    if MASTER.read_text(encoding="utf-8").count("## FIR-VOTE-BSI-001 —") != 1:
        fail("unexpected FIR-VOTE-BSI-001 heading count")
    if "Hard architectural freeze gate" not in NEW_MATRIX.read_text(encoding="utf-8"):
        fail("hard freeze gate missing")
    if "internal party elections are either in-scope or out-of-scope" not in NEW_MATRIX.read_text(
        encoding="utf-8"
    ):
        fail("M-31 classification guard missing")
    if "PREPARATORY PARALLEL WORK / NOT CERTIFIED" not in PCR.read_text(encoding="utf-8"):
        fail("PCR preparatory line missing")
    json.loads(EVIDENCE.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
