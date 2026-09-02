#!/usr/bin/env python3
from pathlib import Path
import re,sys
r=Path(sys.argv[1]).resolve()

def rw(rel, pairs):
    p=r/rel; s=p.read_text()
    for a,b in pairs:
        if a not in s: raise SystemExit(f'missing anchor {rel}: {a[:80]!r}')
        s=s.replace(a,b)
    p.write_text(s)

# Generator: dynamic canonical baseline + accepted API-04/API-05.
p=r/'scripts/api06/build_api06_artifacts.py'; s=p.read_text().replace('STATE = "PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED"','STATE = "CANDIDATE_NOT_ACCEPTED"')
s=s.replace('''        "main_commit": "401b0de97786d0005f9258b15d0bf2200db5f708",
        "main_tree": "7aca2f328b3c5b17e0bebd744a8cfbfc3a3258ac",
        "program_control_register_sha256": (
            "9f38211b45c0abbb11039daf5a98996ea06554ebe813f10f36d015736efcd25d"
        ),
        "master_register_sha256": (
            "3cb40d8c46baa4126702a60cb3138b3776548eda4549fc4ec0dd6163c83c1a3d"
        ),''','''        "main_commit": __import__("os").environ["API06_CURRENT_MAIN_COMMIT"],
        "main_tree": __import__("os").environ["API06_CURRENT_MAIN_TREE"],
        "program_control_register_sha256": __import__("os").environ["API06_CURRENT_PCR_SHA256"],
        "master_register_sha256": __import__("os").environ["API06_CURRENT_MASTER_SHA256"],''')
a=s.index('            "API-04": {'); b=s.index('            "INFRA-01": {',a)
s=s[:a]+'''            "API-04": {
                "state": "ACCEPTED_CLOSED",
                "sha256": "8356ba6f1b0e254f9aa215b4873a1e38f44a47fdac2ac859ff62bd95db999337",
                "size_bytes": 43880523,
                "authoritative_run_id": 33569092401,
                "authoritative_job_id": 100058880258,
            },
            "API-05": {
                "state": "ACCEPTED_CLOSED",
                "sha256": "38bab7663b54f9f81538666315ee16195b0aa086e5b5c50c2b87acc3f4f03a70",
                "size_bytes": 43953160,
                "builder_run_id": 33574093099,
                "builder_job_id": 100074133148,
                "authoritative_run_id": 33574342011,
                "authoritative_job_id": 100074902089,
                "evidence_artifact_id": 9826088503,
            },
'''+s[b:]
a=s.index('    dump(\n        "docs/api/API-06/API06_API05_RECONCILIATION.json",'); b=s.index('\n\n    auth_rows = []',a)
s=s[:a]+'''    dump(
        "docs/api/API-06/API06_API05_RECONCILIATION.json",
        {
            "schema_version": "2",
            "state": "RECONCILED_AGAINST_EXACT_ACCEPTED_API05_C1",
            "accepted_api05_filename": "EPD2_API05_EXTERNAL_INTEGRATION_BOUNDARY_CANDIDATE_0.1_C1.zip",  # noqa: E501
            "accepted_api05_sha256": baseline["predecessors"]["API-05"]["sha256"],
            "accepted_api05_size_bytes": baseline["predecessors"]["API-05"]["size_bytes"],
            "authoritative_workflow": ".github/workflows/api05-accept.yml",
            "authoritative_run_id": baseline["predecessors"]["API-05"]["authoritative_run_id"],
            "authoritative_job_id": baseline["predecessors"]["API-05"]["authoritative_job_id"],
            "acceptance_result": "PASS",
            "interfaces_consumed": ["provider-profile","provider-claim","external-operation","signed-callback","API03IdentityPort","API04MessagePort"],
            "delta_from_development_state": "CLEAN_API06_DELTA_REBASED_ON_ACCEPTED_API05_C1",
            "required_api06_corrections": ["discard API-04/API-05 PRESEAL regressions","preserve accepted API-05 dependency versions","rerun all 40 API-06 gates on exact accepted API-05 C1 bytes"],
            "affected_gates_to_rerun": [f"G{i:02d}" for i in range(1,41)],
            "final_reconciliation_result": "RECONCILED_READY_FOR_INDEPENDENT_API06_ACCEPTANCE",
        },
    )'''+s[b:]
s=s.replace('"synthetic non-live API-05 provider profile",','"synthetic non-live provider profile using accepted API-05 contract",')
s=s.replace('''            "known_preview_limitations": [
                "API-04 and API-05 authoritative acceptance pending",
                "API layer not closed",
                "trial not open",
            ],''','''            "known_preview_limitations": [
                "API-06 independent acceptance pending",
                "API layer not closed",
                "trial not open",
            ],''')
a=s.index('    gaps = ['); b=s.index('    snapshot = {',a)
s=s[:a]+'''    gaps = [
        {"id":"API06-GAP-001","description":"API-06 has not undergone independent authoritative acceptance","severity":"BLOCKER","owning_stage":"API-06","API_closure_blocking":True,"workaround":None,"evidence":"CANDIDATE_NOT_ACCEPTED self-state","status":"OPEN"},
        {"id":"API06-GAP-002","description":"Production HSM/KMS/provider custody remains future work","severity":"DEFERRED","owning_stage":"INFRA/SEC","API_closure_blocking":False,"workaround":"synthetic preview trust only","evidence":"Master FIR","status":"DEFERRED"},
    ]
    dump("docs/api/API-06/API06_FINAL_API_GAP_REGISTER.json",{"schema":"epd2.api06.gaps/2","state":STATE,"api_closure_blocker_count":1,"preseal_implementation_blocker_count":0,"rows":gaps})

'''+s[b:]
s=s.replace('"api_closure_blockers": 3,','"api_closure_blockers": 1,'); p.write_text(s)

# Validator.
p=r/'scripts/validation/validate_api06.py'; s=p.read_text().replace('STATE = "PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED"','STATE = "CANDIDATE_NOT_ACCEPTED"')
s=s.replace('''        "predecessors": all(
            predecessor[name]["state"] == "ACCEPTED_CLOSED" and predecessor[name]["sha256"]
            for name in ("API-01", "API-02", "API-03", "INFRA-01", "OPS-01")
        )
        and predecessor["API-04"]["accepted_sha256"] is None
        and predecessor["API-05"]["accepted_sha256"] is None,
        "api05": api05["working_input"]["working_sha256"]
        == "958f850f7d5f2665bf90ea109ff40196dbc60e1a26c48d827554e482952bcb97"
        and api05["final_reconciliation_result"] == "BLOCKED_PENDING_API05_ACCEPTANCE"
        and len(api05["affected_gates_to_rerun"]) == 40,''','''        "predecessors": all(predecessor[name]["state"] == "ACCEPTED_CLOSED" and predecessor[name]["sha256"] for name in ("API-01","API-02","API-03","API-04","API-05"))
        and predecessor["API-04"]["sha256"] == "8356ba6f1b0e254f9aa215b4873a1e38f44a47fdac2ac859ff62bd95db999337"
        and predecessor["API-05"]["sha256"] == "38bab7663b54f9f81538666315ee16195b0aa086e5b5c50c2b87acc3f4f03a70",
        "api05": api05["accepted_api05_sha256"] == "38bab7663b54f9f81538666315ee16195b0aa086e5b5c50c2b87acc3f4f03a70"
        and api05["acceptance_result"] == "PASS"
        and api05["final_reconciliation_result"] == "RECONCILED_READY_FOR_INDEPENDENT_API06_ACCEPTANCE"
        and len(api05["affected_gates_to_rerun"]) == 40,''')
s=s.replace('and gaps["api_closure_blocker_count"] == 3,','and gaps["api_closure_blocker_count"] == 1,')
s=s.replace('"accepted exact identities + explicit API-04/API-05 null accepted identities"','"accepted exact API-01 through API-05 predecessor identities"').replace('gate(4, static["api05"], "exact API-05 working SHA; final seal blocked pending acceptance"),','gate(4, static["api05"], "exact accepted API-05 C1 reconciliation; all 40 gates rerun"),').replace('"FIR disposition + 3 truthful current closure blockers"','"FIR disposition + single truthful API-06 acceptance blocker"'); p.write_text(s)

for rel in ['services/api-closure-runtime/src/epd2_api_closure_runtime/verification.py','services/api-closure-runtime/src/epd2_api_closure_runtime/inventory.py','scripts/api06/run_api06_mutations.py','services/api-closure-runtime/tests/test_inventory.py']:
    p=r/rel; t=p.read_text().replace('PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED','CANDIDATE_NOT_ACCEPTED')
    if rel.endswith('verification.py'): t=t.replace('inv["api_closure_blockers"] >= 2','inv["api_closure_blockers"] >= 1')
    p.write_text(t)
p=r/'services/api-closure-runtime/tests/test_artifacts.py'; t=p.read_text().replace('PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED','CANDIDATE_NOT_ACCEPTED')
t=t.replace('assert baseline["predecessors"]["API-04"]["accepted_sha256"] is None','assert baseline["predecessors"]["API-04"]["sha256"] == "8356ba6f1b0e254f9aa215b4873a1e38f44a47fdac2ac859ff62bd95db999337"').replace('assert baseline["predecessors"]["API-05"]["accepted_sha256"] is None','assert baseline["predecessors"]["API-05"]["sha256"] == "38bab7663b54f9f81538666315ee16195b0aa086e5b5c50c2b87acc3f4f03a70"')
t=re.sub(r'    assert \(\n        row\["working_input"\]\["working_sha256"\]\n        == "958f850f7d5f2665bf90ea109ff40196dbc60e1a26c48d827554e482952bcb97"\n    \)\n    assert row\["final_reconciliation_result"\] == "BLOCKED_PENDING_API05_ACCEPTANCE"','    assert row["accepted_api05_sha256"] == "38bab7663b54f9f81538666315ee16195b0aa086e5b5c50c2b87acc3f4f03a70"\n    assert row["acceptance_result"] == "PASS"\n    assert row["final_reconciliation_result"] == "RECONCILED_READY_FOR_INDEPENDENT_API06_ACCEPTANCE"',t)
t=t.replace('assert gaps["api_closure_blocker_count"] == len(blockers) == 3','assert gaps["api_closure_blocker_count"] == len(blockers) == 1'); p.write_text(t)

(r/'docs/api/API-06/API06_STATUS.txt').write_text('API-06\nCANDIDATE_NOT_ACCEPTED\n')
(r/'docs/api/API-06/API06_STAGE_CONTRACT.md').write_text('''# API-06 — API Layer Completion, Contract Closure & Preview-Readiness Gate

## State

`CANDIDATE_NOT_ACCEPTED`

API-06 is the terminal bounded API implementation stage. The cumulative C1 is rebased on exact accepted API-05 C1 `38bab7663b54f9f81538666315ee16195b0aa086e5b5c50c2b87acc3f4f03a70` (43,953,160 bytes; authoritative run 33574342011, job 100074902089). API-04 is accepted at C1 `8356ba6f1b0e254f9aa215b4873a1e38f44a47fdac2ac859ff62bd95db999337`. No API-04/API-05 PRESEAL bytes may replace those accepted predecessors.

The stage closes the API implementation line by binding the runtime-derived surface to one machine inventory and exercising authentication, authorization, commit-time reauthorization, S2S trust, errors, idempotency, partial failure, privacy, voting isolation, resource bounds, PostgreSQL, migrations and preview handoff.

Candidate PASS requires all 40 governed gates PASS, 30/30 anti-cheat mutations detected, live PostgreSQL 16, preserved accepted API-05 bytes/dependency versions and freeze/package identity. The sealed candidate self-state remains `CANDIDATE_NOT_ACCEPTED`; independent authoritative acceptance and a separate post-run governance decision are mandatory before `API-06 = ACCEPTED / CLOSED` or `API = CLOSED`.

No production-readiness, legal-activation, final-security, BSI/CC or EAL4 claim follows.
''')
(r/'docs/api/API-06/API06_DEVELOPER_REPORT.md').write_text('''# API-06 C1 developer report

C1 is a clean cumulative delta over exact accepted API-05 C1, not the historical API-05 PRESEAL. The rebuild discards inherited API-04/API-05 regression from the development snapshot, preserves accepted dependency versions, and reruns the complete 40-gate API closure suite plus 30 governed mutations.

This is developer evidence only. The sealed candidate is `CANDIDATE_NOT_ACCEPTED`; independent authoritative acceptance and post-run governance closure are mandatory before the API layer can be closed.
''')
# Delete historical PRESEAL-only/generated additions from the sanitized C1 tree.
for rel in ['.github/workflows/api05-preseal.yml','.github/workflows/api06-preseal.yml','scripts/api06/build_api06_preseal.py','scripts/api06/verify_api06_package.py','validation/api05/validator_result.json']:
    (r/rel).unlink(missing_ok=True)
for rel in ['packages/python/epd2-s2s-crypto/build','packages/python/epd2-s2s-crypto/src/epd2_s2s_crypto.egg-info','validation/api06']:
    import shutil; shutil.rmtree(r/rel,ignore_errors=True)
print('API06_C1_CORRECTION:PASS')
