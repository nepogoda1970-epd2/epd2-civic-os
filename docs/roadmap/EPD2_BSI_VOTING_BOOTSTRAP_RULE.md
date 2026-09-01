# EPD² BSI Voting Certification-Readiness Bootstrap Rule

**Status:** Mandatory project bootstrap rule for Voting-affecting work  
**Effective date:** 2026-08-30  
**Certification status:** PRE-EVALUATION ONLY — NOT BSI/CC CERTIFIED OR CONFORMANT

## 1. Trigger

This rule applies whenever a task, stage, correction, handover, implementation, architecture change, infrastructure change, operational change, frontend change, security change or acceptance decision can affect:

- voting eligibility or the identity→voting trust boundary;
- voting credentials or continuation capabilities;
- the Voting Client;
- ballot construction, encryption, acceptance, storage or publication;
- ballot box / bulletin board / election record;
- guardians, key ceremony, decryption or tally;
- independent verification;
- voting audit, trusted time, trusted channels, recovery or secure states;
- voting production infrastructure, deployment, release or configuration management;
- evidence intended to support future BSI/Common Criteria evaluation.

## 2. Mandatory read order addition

After the normal project bootstrap documents and before changing a Voting-affecting artifact, read:

1. `docs/security/bsi/EPD2_BSI_CC_PP_0121_CERTIFICATION_READINESS_GAP_MATRIX_0.1.md`;
2. the current PACK-15/PACK-16/PACK-17 or successor voting contract/evidence relevant to the change;
3. the applicable `FIR-VOTE-BSI-001` entry in the Master Future Implementation Register.

## 3. Mandatory change classification

Every Voting-affecting handover or acceptance package must identify:

- BSI matrix rows touched;
- current and resulting readiness status for those rows;
- evidence path for the claim;
- newly introduced certification blockers, if any;
- owner and target closure stage for every blocker intentionally deferred.

`UNKNOWN` is permitted during development. Silent omission is not.

## 4. Closure rule

A Voting-affecting implementation or stage must not be described as having cleared the **BSI certification-readiness gate** when it introduces a known blocker that is neither fixed nor explicitly recorded as deferred with:

- unique blocker/reference ID;
- technical rationale;
- responsible owner/workstream;
- required closure stage/gate;
- evidence required to close it.

This rule does not independently prevent normal bounded implementation acceptance where project governance permits an explicit deferred gap. It prevents that deferred gap from disappearing from the future certification path.

## 5. Stronger EPD² invariants remain stronger

BSI-readiness work must not silently weaken established EPD² guarantees merely to imitate a conventional e-voting deployment. In particular:

- identity↔ballot unlinkability remains a hard project invariant;
- no civil/member/account identity or persistent member/person identifier may be introduced into the voting domain; before a written ITSEF P0 position exists, this is a hard architectural freeze gate and cannot be relaxed merely for PP alignment;
- no intermediate tally remains a hard EPD² invariant;
- independent verification and the Open Trust Core boundary remain mandatory;
- certification evidence is not a substitute for cryptographic/public verifiability.

If strict PP conformance appears to conflict with one of these properties, the issue is escalated to the TOE/Security-Target decision and external evaluator pre-assessment. The stronger project invariant is not weakened by implementation convenience.

## 6. Claim discipline

Until a recognised Common Criteria evaluation and BSI certification decision exists for a fixed product/version/configuration, project artifacts must not claim:

- `BSI-certified`;
- `BSI compliant`;
- `CC compliant`;
- `EAL4 certified`;
- successful BSI/Common Criteria evaluation.

Allowed wording is limited to factual statements such as `BSI certification-readiness`, `pre-evaluation`, `mapped against BSI-CC-PP-0121`, or the exact status recorded in the readiness matrix.

## 7. Historical-status rule

Introduction of `FIR-VOTE-BSI-001` is forward-looking governance. It does not by itself reopen or invalidate historical acceptance/closure records. If a historical implementation creates a gap for the future certifiable TOE, that gap is registered as future remediation and must be closed before the corresponding certification gate.
