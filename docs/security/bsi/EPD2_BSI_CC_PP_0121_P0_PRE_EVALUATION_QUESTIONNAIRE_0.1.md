# EPD² — BSI-CC-PP-0121 P0 Pre-Evaluation Questionnaire

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
