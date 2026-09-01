# INFRA-01 — FIR Coverage Matrix

**Stage:** `INFRA-01 — CI Acceptance Harness & Release-Integrity Foundation`
**Mode:** `PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED`

Status discipline: no FIR is marked `implemented` by this round. Status
changes require evidence satisfying each FIR's own acceptance criteria
(Master Register §30: a requirement "must not be marked implemented merely
because a reference interface or test seam exists"). "Materially advanced"
below means concrete governed mechanism/enforcement now exists in the
candidate; the FIR's register status remains `approved` unless the register
itself says otherwise.

## FIRs materially advanced

| FIR                                                                | What INFRA-01 adds                                                                                                                                                                                                                                                                                                                                                                                                                                 | What still gates the FIR's own closure                                                                                                                                                                                             |
| ------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `FIR-REL-001` — Release, Deployment & Environment Integrity        | Machine-readable deployment-manifest schema + fail-closed validator; `running combination == one approved manifest` enforced; mixed versions only via declared compatibility matrix; source→artifact provenance fields (artifact digest, source revision, lock digest, contract/config/migration identity); candidate archive provenance itself now proven byte-exact by the harness (freeze→package identity, `SHA256SUMS.txt`, sealed manifest). | Signed manifests, promotion (verified artifact, not rebuilt), environment separation enforcement, rollback/roll-forward testing, drift detection, emergency-release workflow — all need real deployment surface (later INFRA/OPS). |
| `FIR-READY-001` — Runtime Readiness & Stale-State Protection       | Canonical readiness contract schema + fail-closed evaluator: ten mandatory dimensions incl. deployment-manifest identity, schema/config compatibility, key/trust-anchor readiness, dependency readiness, projection freshness with watermark-vs-required-position stale detection, trusted time, migration and restore/reconciliation state; `UNKNOWN` fails closed; declared overall cannot contradict evaluation.                                | Wiring live services, launch-control gate integration, observability of readiness state in running environments, rolling-deployment mixture distinction in practice.                                                               |
| `FIR-EDGE-001` — Origin, Ingress & Routing Policy Governance       | Preserved and structurally defended: workflow definitions checked for domain-decision markers; infrastructure code checked for domain imports; CI/gateway surface cannot silently accrete domain authority (HI-11 mandatory stage).                                                                                                                                                                                                                | The versioned origin→route→policy artifact itself and its automated assurance list (unknown origins, route exposure, cookie-domain expansion, CSP/CORS relaxation…) — FRONT/INFRA work on a tree that has the edge surface.        |
| `FIR-SEC-SECRET-001` — Repository Secret Leakage Prevention        | INFRA/CI enforcement foundation: authoritative CI scanning of the current tree, staged/generated material and final archive bytes; persisted-evidence sanitation before bundling; central line-pinned governed allowlist with evidence-backed classifications; no inline bypass; hard fail on any unlisted match; mutation-proven (M10); design extends to Git-history scanning.                                                                   | Full publishable Git-history/ref scan, the public-repository release gate, confirmed-secret revocation/rotation runbook (OPS), scanner coverage decisions at public-release time.                                                  |
| `FIR-INFRA-SOV-001` — Sovereign Hosting & Data-Residency Assurance | Machine-readable sovereignty profile mandatory in every deployment manifest: region, jurisdiction, tenancy/isolation class, residency policy, operator-access model, key-custody model, provider role, backup location, explicit trust assumptions; `UNDECIDED` must be declared, unknown state fails closed; no provider selected; `provider != trust assumption` embedded.                                                                       | Actual hosting assurance profile approval, provider assessment, topology/key-custody design, backup/recovery/exit evidence — all pre-Public-Pilot gates owned later.                                                               |
| `FIR-TEST-001` — System-Level Failure & Adversarial Assurance      | The harness gives the future system-wide challenge its machine-readable substrate: registry-governed execution, verified/limited/failed/not-applicable result classes (`PASS/FAIL/BLOCKED/NOT_APPLICABLE_GOVERNED`), reproducible evidence bundles, independent validation of findings. Existing adversarial reference suites are now an explicitly executed mandatory check with executed-test evidence.                                          | The mandatory post-PACK-35 system-wide challenge itself, its 19-scenario corpus, corrective closure loop.                                                                                                                          |
| `FIR-TEST-002` — Incremental Cross-Service Failure Fixtures        | The 16-class mutation suite for the acceptance/verification boundary adds deterministic, isolated failure fixtures that become cumulative assurance (they run in every future pytest invocation); zero-test detection prevents fixture corpora from silently vanishing.                                                                                                                                                                            | Per-PACK cross-service failure fixtures for _business_ boundaries remain owned by the packs that introduce those boundaries.                                                                                                       |
| `FIR-API-001` — Gateway/BFF Non-Ownership                          | Structural non-ownership checks on infrastructure code and workflows (mechanically checked, negative mutations detected — the (b)/(c) conjuncts of its acceptance criterion for the infrastructure side).                                                                                                                                                                                                                                          | Gateway responsibility catalogue and gateway-package checker coverage on the API-line codebase that actually contains the gateway.                                                                                                 |
| `FIR-REG-001` / Master §1.4.1 freshness discipline                 | This round record carries the four mandatory FIR disposition categories; no second register introduced (and the harness now mechanically rejects competing registers — mutation M16).                                                                                                                                                                                                                                                              | The `check_register_freshness.py` mechanization exists only on the PACK-25 ZIP lineage, not on this baseline; porting it here is future work.                                                                                      |

## FIRs intentionally left unchanged

All requirements outside INFRA-01 scope — including every domain, voting,
identity, UX, AI, OPS, CTRL, SEC, legal-activation and BSI-readiness FIR.
INFRA-01 touches no voting trust boundary, no eligibility/credential
surface, no Voting Client, no ballot processing and no cryptographic
profile; the BSI V26 hard freeze gate (`no persistent member/person
identifier inside voting domain`) is untouched. `FIR-BASE-001` still
identifies the latest _accepted_ cumulative baseline — this candidate is not
accepted and therefore does not move it.

## FIR IDs implemented

None.

## FIR IDs deferred

None newly deferred; the closure work listed per-FIR above remains with its
existing owners.

## New FIR IDs created

None. Implementation discovery surfaced no future requirement not already
represented in the canonical register: the baseline defects found (red
lint/typecheck, frozen-artifact test writes, environment-inverted
limitation test) are corrected in this candidate, not deferred as new
requirements.
