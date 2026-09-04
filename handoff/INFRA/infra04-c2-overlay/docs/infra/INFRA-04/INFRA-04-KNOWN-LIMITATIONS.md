# INFRA-04 — Known Limitations and Open Observations

Everything below is a limitation of *this* stage or an observation about
the inherited baseline. Nothing here is resolved by assertion, and nothing
here is hidden behind a passing gate.

## 1. Scope limitations of the stage itself

**Single-host preview runtime.** Every measured bound in
`infra/runtime/resilience_policy.json` was observed on one host, with one
PostgreSQL cluster and five shells. They are evidence bounds for that
environment. They say nothing about a multi-host deployment, and they are
not availability targets for any production system.

**The failure domains are the ones a single host can produce.** Process
exit, service unreachability, database outage, dependency outage,
unresolvable address, trust-material loss, storage pressure and a second
writer are all exercised for real. Rack, region, network-partition-with-
both-halves-alive and hardware-fault domains are *not* — they cannot be
produced honestly here, so no claim is made about them.

**Recovery is exercised, not certified.** The drills prove that a specific
recovery path behaved correctly on a specific run. They are not a
statement about every possible failure sequence.

**No application semantics.** INFRA-04 owns infrastructure behaviour. It
does not own session revocation, workflow authority, scope enforcement or
browser state, and the System Trial replay records those scenarios as
`ENVIRONMENT_BLOCKED` with their owning layer named rather than converting
any of them into an infrastructure PASS.

## 2. Observations about the inherited baseline

**C2 canonical rebase.** Canonical main advanced after C1 was assembled: CTRL-05 C1 was independently accepted and installed first; subsequent OPS-03 workflow-only commits moved the live head to `81c2d0db987536718b30242eeb168aecc21877ca` without changing the PCR or the INFRA-04 implementation surface. The CTRL-05 file delta has no path overlap with the INFRA-04 C1 install delta, so C2 preserves that accepted state. The old C1 changed-file manifest nevertheless cannot be reused: it listed 16 nonexistent `*.pyc` paths and carried four stale file digests. C2 regenerates the manifest only after runtime evidence is final and rejects any missing path or digest mismatch.

These were found while making the candidate packageable. They are recorded
here because they are real, and because the reviewer should know that the
INFRA-04 tree differs from canonical main in these respects.

**Canonical main did not pass its own canonical acceptance harness.**
Originally measured for C1 on `main@2ceb77b`; C2 is rebased on `main@81c2d0db` and must reproduce the quality gates on the GitHub runner:

| Mandatory harness check | State on pristine main |
| --- | --- |
| `backend.ruff-lint` | 88 errors |
| `backend.ruff-format` | 12 files would be reformatted |
| `backend.mypy` (`make typecheck`) | 81 errors, target fails |
| `frontend.prettier` | 245 files with style issues |

No candidate can be packaged from that baseline, so the gates were repaired
in a separate, clearly-scoped commit. Every change there is
behaviour-neutral: type annotations, formatting, and configuration that
tells the tools where to look. No control flow, emitted text, JSON field
name or ordering was altered.

**The acceptance harness and the INFRA-02 stage were never installed in
main.** They were restored byte-for-byte from the INFRA-03 pre-seal lineage
commit whose digest is the recorded `source_preseal_sha256` of the accepted
INFRA-03 C1. Nothing was authored.

**`pilot-roadmap-guard.yml` lost its least-privilege permissions block.**
The accepted INFRA-02 candidate carries `permissions: contents: read` on
that workflow; canonical main does not. Its absence is what makes INFRA-02's
own least-privilege gate fail. The accepted content was restored.

**Two API governance-closure workflows request `contents: write`.**
`api04-governance-close.yml` and `api05-governance-close.yml` are one-shot,
already-executed register transitions. They are classified as
`historical-stage` in the supply-chain policy and their elevation is
recorded there as an observation. **Owner: the API line.** INFRA-04 does
not repair them.

**`scripts/build_front05_identity.py` imports a module that is not in the
tree.** `front04_digest` is referenced but the FRONT-04-owned helper was
never installed. The reference is recorded in the mypy configuration as a
named limitation rather than papered over with a fabricated stub.
**Owner: the FRONT line.**

**The Playwright suite fails identically on pristine canonical main.**
28 browser tests fail in this sandbox: the ten FRONT-01 visual baselines
(pinned to the rendering of the host that produced them) and eighteen
FRONT-03 C1/production-profile tests whose expected elements are not
present here. For C1, the same 28 tests, as a byte-identical list, failed on a clean worktree of `main@2ceb77b` in the same container — 28 failed / 284 passed on both sides. C2 does not treat that historical parity as a pass; the complete browser gate must run again on its exact bytes.

`browser.playwright` is a mandatory harness check, and the harness is
fail-closed with no environment-limitation verdict, so **no candidate
archive can be produced in this environment**. That is reported, not worked
around: G53 is `BLOCKED`, no `INFRA04_PRESEAL_RESULT` marker is emitted,
and `INFRA04_PRESEAL_BLOCKED.json` records the harness checks that stopped
it. The seal is expected to succeed on the CI runner whose rendering the
baselines were reviewed against. **Owner: the FRONT line** for the visual
baselines and the C1/production browser profile.

**A frozen vector was rewritten by the test suite on every run.**
`test_target_conformance.py` wrote host-measured timings back over
`vectors/PACK-16D-TARGET-PROFILE-TIMINGS.json`, which is a byte-pinned
frozen artifact. The packaged tree therefore differed from the tested one
on every machine — the post-test byte mutation the harness exists to
refuse. The benchmark is now emitted to a run-evidence path (or a temporary
file) and the pinned record is left alone and asserted present.
**Owner: the voting line**, which may want the pinned record refreshed
deliberately rather than incidentally.

**Two negative-test fixtures tripped the private-key detector.**
`scripts/ctrl01_validator.py` and
`services/control-plane-service/tests/test_audit_evidence.py` each contain
a bare `BEGIN PRIVATE KEY` header as the *input* to a test that proves such
input is refused. There is no key body and no key material. They entered
canonical main after INFRA-02 was accepted, which is why INFRA-02's own
scanner flags them now. They are recorded in the existing governed
allowlist as `synthetic-test-material`, pinned to the SHA-256 of the exact
line in the exact file for the exact detector — no pattern exemption, no
path exemption, no detector weakening, and no history rewrite. Editing
either line invalidates its entry and re-arms the gate. **Owner: the CTRL
line**, if it prefers to restructure the fixtures instead.

**A voting-service property test asserted that a dependency was missing.**
`test_property_limitation_is_recorded` required `hypothesis` to raise
`ImportError`, recording an environment in which PyPI was unreachable.
Where the declared dev dependencies do install — as they do here — that
assertion fails for a reason unrelated to the code under test. The test now
asserts the limitation text (deterministic randomised loops, no shrinking)
and records the availability of `hypothesis` rather than demanding its
absence. Converting those tests to real strategies is unchanged as a
PACK-17 item. **Owner: the voting line.**

**Register regions disagree about what is already accepted.** The Program
Control Register's *primary position* records `INFRA-03 = ACCEPTED /
CLOSED`; the program-layer table still lists only INFRA-01 and INFRA-02,
and section 9 does not restate several accepted stages. The reconciliation
records this per region as a **lagging region**, and takes acceptance only
where a recorded governance decision exists. INFRA-04 does not edit the
registers and does not resolve the lag in its own favour.
**Owner: governance.**

## 3. Deliberately not done

**The registers are not updated by this stage.** No PCR or Master edit is
included. Recording an INFRA-04 transition is a governance act, and a
candidate that writes its own transition has accepted itself.

**No production, hosting-provider or certification claim.** The candidate emits only
the developer pre-seal marker `INFRA04_PRESEAL_RESULT`; the independent-review
terminal marker belongs exclusively to the external GitHub review job.

**INFRA layer closure is not proposed.** The register records
`INFRA = OPEN / NOT CLOSED`, and INFRA-05…INFRA-07 remain separately
governed.
