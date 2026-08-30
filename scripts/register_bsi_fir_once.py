from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

MASTER = Path("docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md")
WORKFLOW = Path(".github/workflows/bsi-register-once.yml")
SCRIPT = Path("scripts/register_bsi_fir_once.py")
EVIDENCE = Path("docs/roadmap/EPD2_BSI_MASTER_UPDATE_EVIDENCE.json")
MARKER = "## FIR-BSI-001 — BSI CC PP-0121 Certification Readiness"

BLOCK = r'''

## Governance maintenance record — BSI voting certification readiness (2026-08-30)

**Round:** documentation/governance only. No API, INFRA, OPS, CTRL, FRONT,
SEC, PACK-15, PACK-16, PACK-17 or other implementation stage is accepted,
closed, reopened, certified or legally activated by this update.

**New FIR ID created:** `FIR-BSI-001 — BSI CC PP-0121 Certification Readiness`
— status `approved`, priority `critical`.

**Governed readiness artifacts:**

- `docs/roadmap/EPD2_BSI_CC_PP_0121_CONFORMANCE_MATRIX.md`;
- `docs/roadmap/EPD2_BSI_VOTING_BOOTSTRAP_RULE.md`.

**Core decision:** EPD² Voting is to be developed with future certification
against the applicable `BSI-CC-PP-0121` target in mind, presently targeting
`EAL4 + ALC_FLR.2`, while preserving stronger EPD² privacy,
no-intermediate-tally and independent-verification invariants. This is a
certification-readiness obligation, not a certification or conformance claim.

**Execution state:** unchanged. The Program Control Register remains the sole
authority for current stage state.

## FIR-BSI-001 — BSI CC PP-0121 Certification Readiness

- **Status:** `approved`
- **Priority:** `critical`
- **Domain:** voting security / Common Criteria / BSI certification readiness / assurance evidence
- **Target:** PACK-15/16/17 voting lineage + every future Voting-affecting API, INFRA, OPS, CTRL, FRONT and SEC change + final certification workstream
- **External target:** `BSI-CC-PP-0121`, Version 1.0, CC:2022 Revision 1; target assurance package `EAL4 + ALC_FLR.2`
- **Governed matrix:** `docs/roadmap/EPD2_BSI_CC_PP_0121_CONFORMANCE_MATRIX.md`
- **Bootstrap rule:** `docs/roadmap/EPD2_BSI_VOTING_BOOTSTRAP_RULE.md`

### Requirement

All future EPD² Voting implementation and material changes SHALL preserve a
traceable certification-readiness chain:

```text
BSI PP requirement / SAR
→ EPD² requirement
→ architecture / trust boundary
→ implementation
→ test
→ evidence
→ disposition
```

A Voting-affecting change SHALL identify the matrix rows it touches and SHALL
NOT silently introduce or hide a known blocker to future certification. A
known blocker may remain only when it is explicitly recorded as deferred with
a unique reference, technical rationale, responsible owner/workstream,
required closure stage/gate and required evidence.

### Stronger-invariant rule

Certification-readiness work SHALL NOT silently weaken a stronger established
EPD² invariant merely to imitate a conventional e-voting deployment. In
particular, identity↔ballot unlinkability, Voting Client isolation,
no-intermediate-tally and independent public verification remain hard project
properties. A suspected strict-conformance conflict is escalated to the
TOE/Security-Target decision and evaluator pre-assessment rather than resolved
by implementation convenience.

### P0 gates

Before freezing certification-oriented production architecture:

1. define the exact Target of Evaluation (TOE), including whether it is a
   single central voting-server TOE or a multi-component TOE;
2. obtain an evaluator/pre-assessment position on whether the PP voter identity,
   voters' register and voting-record concepts can be represented by EPD²'s
   non-identifying, election-scoped, single-use eligibility model while
   preserving strict conformance;
3. create a draft Security Target and exact PP/SFR/SAR traceability.

### Required production closures

The certifiable path must close, with evidence appropriate to the final TOE:
trusted endpoint and inter-component channels; production access control;
cryptographic secret handling and key custody; entropy/RNG policy; defensible
key destruction/zeroization; side-channel-resistant secret operations;
protected audit and reliable time without recreating identity↔ballot
correlation; self-tests, secure states and recovery; controlled import/export
and archival verification; production management controls; hardened deployment;
configuration/release integrity; flaw remediation; operational/preparative
guidance; SFR test coverage and vulnerability-analysis inputs.

### Acceptance criteria

`FIR-BSI-001` is not implemented merely because the matrix or documents exist.
It may advance only on explicit evidence that:

- the TOE and Security Target are defined for the intended certification target;
- every claimed PP SFR/SAR has a maintained trace to design, implementation,
  test and evidence;
- every known blocker is closed or remains explicitly governed as a
  pre-certification blocker with owner and closure gate;
- the certification evidence package is evaluation-ready for the fixed
  product/version/configuration.

Formal `BSI-certified`, `BSI compliant`, `CC compliant`, `EAL4 certified` or
successful-evaluation claims remain prohibited until supported by the actual
independent Common Criteria evaluation and BSI certification decision for the
specific product/version/configuration.

### Historical-status rule

This FIR is forward-looking. Its introduction does not by itself reopen or
invalidate historical PACK/stage acceptance. A historical implementation that
creates a gap for the future certifiable TOE becomes a governed future
remediation obligation and must be closed before the relevant certification
gate.
'''


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    raw = MASTER.read_bytes()
    text = raw.decode("utf-8")
    before_sha = sha256(raw)
    before_size = len(raw)

    if before_size < 700_000:
        raise SystemExit(f"REFUSE: canonical Master unexpectedly small: {before_size}")
    if "FIR-OSS-007" not in text:
        raise SystemExit("REFUSE: expected current V25 FIR-OSS-007 marker missing")
    if text.count(MARKER) > 1:
        raise SystemExit("REFUSE: duplicate FIR-BSI-001 already exists")

    if MARKER not in text:
        text = text.rstrip() + BLOCK.rstrip() + "\n"
        MASTER.write_text(text, encoding="utf-8", newline="\n")

    after = MASTER.read_bytes()
    after_text = after.decode("utf-8")
    if after_text.count(MARKER) != 1:
        raise SystemExit("REFUSE: FIR-BSI-001 uniqueness check failed")
    if "EPD2_BSI_CC_PP_0121_CONFORMANCE_MATRIX.md" not in after_text:
        raise SystemExit("REFUSE: governed BSI matrix linkage missing")

    payload = {
        "schema": "epd2.bsi.master-update-evidence.v1",
        "effective_date": "2026-08-30",
        "workflow_input_commit": os.environ.get("GITHUB_SHA"),
        "master_path": str(MASTER),
        "before_sha256": before_sha,
        "after_sha256": sha256(after),
        "before_size": before_size,
        "after_size": len(after),
        "fir_bsi_001_heading_count": after_text.count(MARKER),
        "fir_oss_007_preserved": "FIR-OSS-007" in after_text,
        "program_control_modified": False,
        "claim": "GOVERNANCE_REGISTRATION_ONLY_NOT_BSI_CC_CONFORMANCE",
    }
    EVIDENCE.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    WORKFLOW.unlink(missing_ok=True)
    SCRIPT.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
