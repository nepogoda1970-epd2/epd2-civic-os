#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, pathlib, shutil, sys, zipfile, subprocess

EXPECTED_MAIN = "616c944248e3afe109368aebc76c416ee75e60a3"
EXPECTED_PCR_SHA = "880cd61181ee01cc3d5ce7a63dab0d16de28e5a8dd2fa7efd77e62a14e9100b6"
CANDIDATE_NAME = "EPD2_API06_API_LAYER_COMPLETION_AND_PREVIEW_READINESS_CANDIDATE_0.1_C1.zip"
CANDIDATE_SHA = "3432b6615aa83c6f2860c015b7cafc2a18362aa371901616951a1bd5d263933c"
CANDIDATE_SIZE = 44012716
BUILDER_RUN = 33628261946
BUILDER_JOB = 100241096268
CANDIDATE_ARTIFACT_ID = 9845841293
CANDIDATE_ARTIFACT_DIGEST = "sha256:83b0dc1fb0f451dc26799156a0c12518a2e3146b1016ef7e719e9b2cda407a20"
BUILD_EVIDENCE_ARTIFACT_ID = 9845842104
BUILD_EVIDENCE_DIGEST = "sha256:683ec93b1a4caa5f15c158ae84fe087c671b4b5500c8a81f18676801a5def7eb"
AUTH_RUN = 33629147572
AUTH_JOB = 100243984921
AUTH_COMMIT = "2f3f951baa9d392ff7b0decc1137bcc0670c8fd2"
AUTH_ARTIFACT_ID = 9846196028
AUTH_ARTIFACT_DIGEST = "sha256:b1c4bb5072a8040b2eaa52a5f31bdfe353b6841228c18e9cd456122d6578bc8c"
SEALED_WORKFLOW_SHA256 = "0866787ae8715ec3a2808bce157c4352b5cf2f3ad5be82a0d79099b590fff4c5"
SEALED_WORKFLOW_GIT_BLOB = "37205e9fa76a8f4bebce77fb116e5995f6875347"

def sha256_file(p: pathlib.Path) -> str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

def safe_extract(zp: pathlib.Path, dest: pathlib.Path) -> pathlib.Path:
    with zipfile.ZipFile(zp) as z:
        names=z.namelist(); assert z.testzip() is None
        roots={n.split("/",1)[0] for n in names if n}; assert len(roots)==1, roots
        for n in names:
            pp=pathlib.PurePosixPath(n)
            assert not n.startswith("/") and ".." not in pp.parts, n
        z.extractall(dest)
    return dest/next(iter(roots))

def verify_internal_seal(root: pathlib.Path) -> int:
    count=0
    for line in (root/"SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        if not line.strip(): continue
        digest, rel=line.split("  ",1); p=root/rel
        assert p.is_file(), rel
        actual=sha256_file(p); assert actual==digest, (rel,digest,actual)
        count+=1
    return count

def is_payload(rel: str) -> bool:
    return (
        rel=="contracts/api/api06_api_surface.json"
        or rel.startswith("docs/api/API-06/")
        or rel.startswith("handoff/API-06/templates/C1/")
        or rel.startswith("scripts/api06/")
        or rel=="scripts/validation/validate_api06.py"
        or rel.startswith("services/api-closure-runtime/")
        or rel.startswith("validation/api06/")
    )

def require_replace(text: str, old: str, new: str) -> str:
    if old not in text:
        raise SystemExit(f"missing PCR anchor: {old[:160]!r}")
    return text.replace(old,new,1)

repo=pathlib.Path(sys.argv[1]).resolve(); cand_dir=pathlib.Path(sys.argv[2]).resolve(); evidence_dir=pathlib.Path(sys.argv[3]).resolve()
head=subprocess.check_output(["git","rev-parse","HEAD"],cwd=repo,text=True).strip(); assert head==EXPECTED_MAIN,(head,EXPECTED_MAIN)
pcr_path=repo/"docs/roadmap/EPD2_PROGRAM_CONTROL_REGISTER.md"; assert sha256_file(pcr_path)==EXPECTED_PCR_SHA

zip_candidates=list(cand_dir.rglob(CANDIDATE_NAME)); assert len(zip_candidates)==1,zip_candidates
candidate=zip_candidates[0]; assert candidate.stat().st_size==CANDIDATE_SIZE; assert sha256_file(candidate)==CANDIDATE_SHA
side=list(cand_dir.rglob(CANDIDATE_NAME+".sha256")); assert len(side)==1 and CANDIDATE_SHA in side[0].read_text(encoding="utf-8")

extract=repo.parent/"_api06_promote_extract"; shutil.rmtree(extract,ignore_errors=True); extract.mkdir(parents=True)
root=safe_extract(candidate,extract); seal_count=verify_internal_seal(root); assert seal_count==4339,seal_count
identity=json.loads((root/"docs/api/API-06/API06_CANDIDATE_IDENTITY.json").read_text()); seal=json.loads((root/"docs/api/API-06/API06_C1_SEAL_RECORD.json").read_text()); baseline=json.loads((root/"docs/api/API-06/API06_ENTERING_BASELINE_IDENTITY.json").read_text())
assert identity["state"]=="CANDIDATE_NOT_ACCEPTED" and identity["self_accepted"] is False and identity["builder_run_id"]==BUILDER_RUN
assert identity["sealed_acceptance_workflow_sha256"]==SEALED_WORKFLOW_SHA256
assert seal["candidate_self_state"]=="CANDIDATE_NOT_ACCEPTED" and seal["self_accepted"] is False and seal["governed_gates"]=="40/40 PASS" and seal["mutations"]=="30/30 detected"
assert baseline["main_commit"]==EXPECTED_MAIN and baseline["program_control_register_sha256"]==EXPECTED_PCR_SHA
assert sha256_file(root/"handoff/API-06/templates/C1/api06-accept.yml")==SEALED_WORKFLOW_SHA256
assert (root/"docs/api/API-05/API05_C1_ACCEPTANCE_RECORD.json").read_bytes()==(repo/"docs/api/API-05/API05_C1_ACCEPTANCE_RECORD.json").read_bytes()

external=list(evidence_dir.rglob("external_authoritative_result.json")); assert len(external)==1,external
auth=json.loads(external[0].read_text(encoding="utf-8"))
assert auth["stage"]=="API-06" and auth["result"]=="PASS" and auth["self_acceptance"] is False
assert auth["candidate_sha256"]==CANDIDATE_SHA and auth["candidate_size_bytes"]==CANDIDATE_SIZE and auth["builder_run_id"]==BUILDER_RUN and auth["authoritative_run_id"]==AUTH_RUN
assert auth["governed_gates_total"]==40 and auth["passed_gates"]==40 and auth["failed_gates"]==[] and auth["environment_blocked_gates"]==[] and auth["provenance_commit"]==AUTH_COMMIT

payload=[]
for p in sorted(root.rglob("*")):
    if p.is_file():
        rel=p.relative_to(root).as_posix()
        if is_payload(rel): payload.append((rel,p))
assert len(payload)==61,len(payload)
installed=[]
for rel,src in payload:
    dst=repo/rel; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(src,dst); assert dst.read_bytes()==src.read_bytes(); installed.append({"path":rel,"sha256":sha256_file(dst)})

api06_dir=repo/"docs/api/API-06"; api06_dir.mkdir(parents=True,exist_ok=True)
(api06_dir/"API06_C1_AUTHORITATIVE_ACCEPTANCE_RESULT.json").write_text(json.dumps(auth,indent=2)+"\n",encoding="utf-8")
manifest={"schema":"epd2.api06.c1.canonical-installation/1","stage":"API-06","candidate":{"filename":CANDIDATE_NAME,"sha256":CANDIDATE_SHA,"size_bytes":CANDIDATE_SIZE,"sealed_files":seal_count,"artifact_id":CANDIDATE_ARTIFACT_ID,"artifact_outer_digest":CANDIDATE_ARTIFACT_DIGEST},"authoritative":{"run_id":AUTH_RUN,"job_id":AUTH_JOB,"provenance_commit":AUTH_COMMIT,"result":"PASS"},"installed_file_count":len(installed),"verification":"EXACT_BYTES_MATCH_SEALED_C1","files":installed}
(api06_dir/"API06_C1_CANONICAL_INSTALLATION_MANIFEST.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
record={"schema":"epd2.api06.c1.acceptance-record/1","stage":"API-06","stage_title":"API Layer Completion, Contract Closure & Preview-Readiness Gate","decision":"ACCEPTED_CLOSED","decision_date":"2026-09-02","decision_authority":"Project Owner","previous_state":"NEXT / NOT ACCEPTED","new_state":"ACCEPTED / CLOSED","api_layer_state":"CLOSED","system_trial_preview_state":"NOT AUTOMATICALLY OPENED; PREVIEW-READINESS CHECKPOINT MAY NOW BE QUALIFIED","candidate":{"filename":CANDIDATE_NAME,"role":"C1","sha256":CANDIDATE_SHA,"size_bytes":CANDIDATE_SIZE,"sealed_files":seal_count,"artifact_id":CANDIDATE_ARTIFACT_ID,"artifact_outer_digest":CANDIDATE_ARTIFACT_DIGEST,"builder_run_id":BUILDER_RUN,"builder_job_id":BUILDER_JOB,"builder_provenance_commit":"40efd68d81cde67bf15453d095785d1971ec301b","self_state":"CANDIDATE_NOT_ACCEPTED","self_accepted":False},"accepted_predecessor":{"stage":"API-05","role":"C1","sha256":"38bab7663b54f9f81538666315ee16195b0aa086e5b5c50c2b87acc3f4f03a70","size_bytes":43953160,"authoritative_run_id":33574342011,"authoritative_job_id":100074902089,"state":"ACCEPTED / CLOSED"},"sealed_workflow":{"candidate_path":"handoff/API-06/templates/C1/api06-accept.yml","authoritative_path":".github/workflows/api06-accept.yml","git_blob":SEALED_WORKFLOW_GIT_BLOB,"sha256":SEALED_WORKFLOW_SHA256,"byte_equality":"PASS"},"authoritative":{"branch":"tmp/api06-c1-authoritative-accept","run_id":AUTH_RUN,"job_id":AUTH_JOB,"provenance_commit":AUTH_COMMIT,"conclusion":"SUCCESS","governed_gates_total":40,"passed_gates":40,"failed_gates":0,"environment_blocked_gates":0,"terminal_marker":"API06_RESULT:PASS:validation/api06/external_authoritative_result.json","sealed_source_unchanged":"PASS"},"authoritative_evidence_artifact":{"name":"api06-c1-authoritative-acceptance-33629147572","id":AUTH_ARTIFACT_ID,"digest":AUTH_ARTIFACT_DIGEST,"size_bytes":30852},"builder_evidence_artifact":{"name":"api06-c1-build-evidence-v3-33628261946","id":BUILD_EVIDENCE_ARTIFACT_ID,"digest":BUILD_EVIDENCE_DIGEST},"measured_evidence":{"governed_gates":"40/40 PASS (builder) + 40/40 PASS (independent authoritative replay)","mutations":"30/30 DETECTED","postgresql":"16.15 / server_version_num=160015","runtime_routes":91,"api06_service_tests":"49 passed / 0 failed","accepted_api05_behavioral_regression":"66 passed / 0 failed","accepted_api04_unit_regression":"PASS","locked_dependencies":"PASS","ruff":"PASS","complete_sha256_seal":"PASS","freeze_rehearsal":"PASS / source unchanged / archive byte equal","canonical_payload_installation":"61 exact sealed C1 payload files installed"},"candidate_self_state_resolution":"CANDIDATE_NOT_ACCEPTED remains the intentional no-self-acceptance safeguard inside the sealed candidate; the independent authoritative PASS and this post-run Project Owner governance decision establish canonical acceptance.","open_blockers":[],"next_permitted_primary_stage":"INFRA/OPS PREVIEW-READINESS MINIMUM","next_stage_state":"ELIGIBLE FOR GOVERNED QUALIFICATION","master_future_register_changed":False,"nonclaims":["automatic System Trial Preview opening","INFRA layer closure","OPS layer closure","production readiness","legal activation","final security readiness","BSI certification","Common Criteria / EAL4 certification"]}
(api06_dir/"API06_C1_ACCEPTANCE_RECORD.json").write_text(json.dumps(record,indent=2)+"\n",encoding="utf-8")

pcr=pcr_path.read_text(encoding="utf-8")
note=f"""**API-06 authoritative acceptance, terminal API-stage closure and API-layer closure (2026-09-02):** exact sealed candidate `{CANDIDATE_NAME}`, SHA-256 `{CANDIDATE_SHA}`, size `{CANDIDATE_SIZE:,}` bytes, passed independent exact-byte GitHub Actions authoritative review, run `{AUTH_RUN}`, job `{AUTH_JOB}`, provenance commit `{AUTH_COMMIT}`, conclusion `success`. The independent runner verified exact candidate identity and complete internal SHA-256 seal, byte-for-byte sealed acceptance-workflow equality, current canonical API-05 closure/API-06 entering governance, locked dependencies, accepted API-04 live regression environment, all `40/40` governed API-06 gates, `30/30` mutations detected, PostgreSQL `16.15`, and unchanged sealed source after execution. Terminal marker: `API06_RESULT:PASS:validation/api06/external_authoritative_result.json`. Authoritative evidence artifact `api06-c1-authoritative-acceptance-{AUTH_RUN}`, artifact ID `{AUTH_ARTIFACT_ID}`, digest `{AUTH_ARTIFACT_DIGEST}`. The governance decision is recorded in `docs/api/API-06/API06_C1_ACCEPTANCE_RECORD.json`, and the exact sealed API-06 payload is installed in canonical `main` with hashes in `docs/api/API-06/API06_C1_CANONICAL_INSTALLATION_MANIFEST.json`. **API-06 is therefore `ACCEPTED / CLOSED`, and the API layer is `CLOSED`.** The sealed candidate's `CANDIDATE_NOT_ACCEPTED` self-state remains the intentional no-self-acceptance safeguard and is superseded only by the independent run plus this post-run Project Owner decision. This releases the API dependency for INFRA/OPS preview-readiness qualification, but does **not** automatically open System Trial Preview, close INFRA/OPS, claim production readiness, legal activation, BSI/CC/EAL4 certification or final security acceptance.\n\n"""
anchor="## 2. Program phase state"; assert anchor in pcr; pcr=pcr.replace(anchor,note+anchor,1)
pcr=require_replace(pcr,"| API | `API-01 ACCEPTED / CLOSED; API-02 ACCEPTED / CLOSED; API-03 ACCEPTED / CLOSED; API-04 ACCEPTED / CLOSED; API-05 ACCEPTED / CLOSED; API-06 NEXT` | API-05 is closed at exact accepted C1. API-06 is the next permitted primary stage but is not active until its governed stage work is opened. API remains open through API-06. |","| API | `API-01 ACCEPTED / CLOSED; API-02 ACCEPTED / CLOSED; API-03 ACCEPTED / CLOSED; API-04 ACCEPTED / CLOSED; API-05 ACCEPTED / CLOSED; API-06 ACCEPTED / CLOSED; API LAYER CLOSED` | Exact API-06 C1 is independently accepted and its exact sealed payload is installed in canonical main. The API layer is CLOSED. This releases the API prerequisite for INFRA/OPS preview-readiness qualification; System Trial Preview still requires an explicit checkpoint-opening decision and does not close INFRA or OPS. |")
pcr=require_replace(pcr,"| OPS | `OPS-01 ACCEPTED / CLOSED; OPS-02 ACCEPTED / CLOSED; OPS LAYER OPEN` | Exact bounded OPS-01 Operational Readiness, Incident, Recovery & Change Control Foundation is accepted/closed at C2. Exact bounded OPS-02 Preview Operations, Deployment, Observability & Recovery Readiness is accepted/closed at C3. The overall OPS layer remains open; this transition does not open System Trial Preview and final OPS closure still follows API/INFRA dependencies and the governed system-trial path. |","| OPS | `OPS-01 ACCEPTED / CLOSED; OPS-02 ACCEPTED / CLOSED; OPS LAYER OPEN; OPS-03 QUALIFICATION ELIGIBLE` | Exact bounded OPS-01 C2 and OPS-02 C3 are accepted/closed. API-06/API-layer closure has released the final-API-runtime prerequisite for OPS-03 qualification. The overall OPS layer remains open; OPS-03 still requires its own exact candidate, governed PASS and independent acceptance, and System Trial Preview is not opened by this API transition. |")
pcr=require_replace(pcr,"| CTRL | `CTRL-01 ACCEPTED / CLOSED; CTRL LAYER OPEN` | Exact bounded CTRL-01 C1 Governed Control Plane is accepted/closed and its exact sealed payload is installed in canonical main. The overall CTRL layer remains open; API-06 remains NEXT / NOT ACCEPTED and System Trial Preview remains CHECKPOINT_NOT_OPEN. Later CTRL work and whole-layer closure remain separately governed. |","| CTRL | `CTRL-01 ACCEPTED / CLOSED; CTRL LAYER OPEN` | Exact bounded CTRL-01 C1 Governed Control Plane is accepted/closed and its exact sealed payload is installed in canonical main. The overall CTRL layer remains open. API-06/API are now closed, but System Trial Preview remains separately checkpoint-governed and later CTRL work/whole-layer closure remain separately governed. |")
old_primary="""Current primary position:\n\n```text\nDATA = CLOSED\nAPI-01 = ACCEPTED / CLOSED\nAPI-02 = ACCEPTED / CLOSED\nAPI-03 = ACCEPTED / CLOSED\nAPI-04 = ACCEPTED / CLOSED\nAPI-05 = ACCEPTED / CLOSED\nAPI-06 = NEXT\n```"""
new_primary="""Current primary position:\n\n```text\nDATA = CLOSED\nAPI-01 = ACCEPTED / CLOSED\nAPI-02 = ACCEPTED / CLOSED\nAPI-03 = ACCEPTED / CLOSED\nAPI-04 = ACCEPTED / CLOSED\nAPI-05 = ACCEPTED / CLOSED\nAPI-06 = ACCEPTED / CLOSED\nAPI = CLOSED\nNEXT CHECKPOINT = INFRA/OPS PREVIEW-READINESS MINIMUM\n```"""
pcr=require_replace(pcr,old_primary,new_primary)
pcr=require_replace(pcr,"  → API-06 NEXT\n  → API CLOSED","  → API-06 CLOSED\n  → API CLOSED")
pcr=require_replace(pcr,"While `API-06 = NEXT`, the following parallel work may proceed without treating API-06 as active or accepted. API-05 is accepted/closed at exact C1 and is the governed predecessor for API-06:","With `API = CLOSED`, parallel work may continue while the explicit INFRA/OPS preview-readiness minimum is qualified. API-06 is accepted/closed at exact C1; no parallel line may treat API closure as automatic INFRA/OPS/CTRL/FRONT closure or as System Trial Preview opening:")
old9="""**Primary implementation:** `API-06 = NEXT` (`API-01 = ACCEPTED / CLOSED`; `API-02 = ACCEPTED / CLOSED`; `API-03 = ACCEPTED / CLOSED`; `API-04 = ACCEPTED / CLOSED`; `API-05 = ACCEPTED / CLOSED`). API-06 is the next permitted primary API stage; it is not active or accepted until its governed stage work is opened and independently accepted.\n\n**Governed forward path:** open and complete API-06 from the exact accepted API-05 C1 predecessor, seal and independently verify API-06, and close API only after API-06 authoritative acceptance. Then establish the explicit INFRA/OPS preview-readiness minimum and open `SYSTEM TRIAL PREVIEW — FIRST END-TO-END PROBNIK`. The preview is an early usable-system checkpoint only and cannot close INFRA or OPS. After preview findings are handled through owning-layer lineage, complete INFRA → OPS → CTRL → FRONT, establish `FINAL INTEGRATION`, and run final SEC against that exact integrated baseline before the final readiness decision."""
new9="""**Primary implementation:** `API = CLOSED` through exact independently accepted `API-06 C1`. The current governed checkpoint is `INFRA/OPS PREVIEW-READINESS MINIMUM`; OPS-03 qualification may now bind the exact accepted API-06 runtime.\n\n**Governed forward path:** qualify the explicit INFRA/OPS preview-readiness minimum against the exact accepted API runtime and then, only by a separate checkpoint-opening decision, open `SYSTEM TRIAL PREVIEW — FIRST END-TO-END PROBNIK`. The preview is an early usable-system checkpoint only and cannot close INFRA or OPS. After preview findings are handled through owning-layer lineage, complete INFRA → OPS → CTRL → FRONT, establish `FINAL INTEGRATION`, and run final SEC against that exact integrated baseline before the final readiness decision."""
pcr=require_replace(pcr,old9,new9)
pcr=require_replace(pcr,"This accepted foundation may be reused by later preview/final OPS work, but it does not close the overall OPS layer, does not authorize production operation, and does not alter `API-06 = NEXT`.","This accepted foundation may be reused by later preview/final OPS work, but it does not close the overall OPS layer or authorize production operation. API is now closed; OPS-03 qualification must independently bind the exact accepted API-06 identity.")
pcr=require_replace(pcr,"This does not close the overall INFRA layer, open or accept INFRA-03…INFRA-07, select a hosting provider, or change `API-06 = NEXT`.","This does not close the overall INFRA layer, open or accept INFRA-03…INFRA-07, or select a hosting provider. API is now closed; INFRA remains separately governed.")
pcr=require_replace(pcr,"API-06 is now the next permitted primary API stage; this FRONT work does not constitute FRONT acceptance or final closure.","API is now closed; this FRONT work still does not constitute FRONT acceptance or final closure and remains downstream of the governed preview/integration path.")
pcr=require_replace(pcr,"Neither accepted PILOT stage changes `API-06 = NEXT`, claims production readiness/legal activation, or forces immediate INTEGRATION-01 advancement.","Neither accepted PILOT stage claims production readiness/legal activation or forces immediate INTEGRATION-01 advancement; API closure does not alter their own governed acceptance lineage.")
pcr_path.write_text(pcr,encoding="utf-8")
print(f"API06_CANONICAL_INSTALL:PASS:{len(installed)}:{CANDIDATE_SHA}:{CANDIDATE_SIZE}")
