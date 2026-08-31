from __future__ import annotations
import argparse, hashlib, json, os, pathlib, shutil, stat, subprocess, sys, zipfile, re
C9_SHA='42a1a59a5b4aaf769d38fac0c0426d5a436550b050d33b1cf7a0f4f1cd37a48b'
C9_SIZE=34638963
API01_SHA='cea2fb0e23ee174e802ec1899cf62e570e5c8659a0f31c7e6c3c3955bffa3d27'
DATA06_SHA='8cba01997e4943f6d3c2b3fc1fe11e2c3527cd6c39123171a827fb8e3669cbf1'
C9_NAME='EPD2_API02_AUTHENTICATION_AND_AUTHORIZATION_RUNTIME_CANDIDATE_0.1_C9.zip'
C10_ROOT='EPD2_API02_AUTHENTICATION_AND_AUTHORIZATION_RUNTIME_CANDIDATE_0.1_C10'
C10_NAME=C10_ROOT+'.zip'

def sha(p:pathlib.Path)->str:
 h=hashlib.sha256();
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''): h.update(b)
 return h.hexdigest()

def patch_workflow(p:pathlib.Path)->None:
 t=p.read_text()
 t=t.replace('authoritative acceptance workflow (C9)','authoritative acceptance workflow (C10)')
 t=t.replace('candidate                   EPD2_API02_AUTHENTICATION_AND_AUTHORIZATION_RUNTIME_CANDIDATE_0.1_C9.zip','candidate                   EPD2_API02_AUTHENTICATION_AND_AUTHORIZATION_RUNTIME_CANDIDATE_0.1_C10.zip')
 t=t.replace('API02_ENTERING_CANDIDATE_ZIP       …API02…CANDIDATE_0.1_C8.zip  7836135f…','API02_ENTERING_CANDIDATE_ZIP       …API02…CANDIDATE_0.1_C9.zip  42a1a59a…')
 t=t.replace('description: expected SHA-256 of EPD2_API02_AUTHENTICATION_AND_AUTHORIZATION_RUNTIME_CANDIDATE_0.1_C9.zip','description: expected SHA-256 of EPD2_API02_AUTHENTICATION_AND_AUTHORIZATION_RUNTIME_CANDIDATE_0.1_C10.zip')
 t=t.replace('CANDIDATE_ROLE: C9','CANDIDATE_ROLE: C10')
 t=t.replace('CANDIDATE_NAME: EPD2_API02_AUTHENTICATION_AND_AUTHORIZATION_RUNTIME_CANDIDATE_0.1_C9','CANDIDATE_NAME: EPD2_API02_AUTHENTICATION_AND_AUTHORIZATION_RUNTIME_CANDIDATE_0.1_C10')
 t=t.replace('ENTERING_CANDIDATE_NAME: EPD2_API02_AUTHENTICATION_AND_AUTHORIZATION_RUNTIME_CANDIDATE_0.1_C8.zip','ENTERING_CANDIDATE_NAME: '+C9_NAME)
 t=t.replace('ENTERING_CANDIDATE_SHA256: 7836135f2e656c998b224c56698ad337c9474238cc241d250add710ba79ecaef','ENTERING_CANDIDATE_SHA256: '+C9_SHA)
 t=t.replace('tmp/api02-c9-canonical-accept','tmp/api02-c10-canonical-accept')
 t=t.replace('handoff/API-02/C9_ACCEPTANCE_INPUTS.env','handoff/API-02/C10_ACCEPTANCE_INPUTS.env')
 t=t.replace('api02-c9-acceptance-evidence','api02-c10-acceptance-evidence')
 t=t.replace("uv --version | grep -qx 'uv 0.12.5'","uv --version | grep -q '^uv 0\\.12\\.5'")
 t=t.replace('uv --version | grep -qx "uv 0.12.5"','uv --version | grep -q \'^uv 0\\.12\\.5\'')
 t=t.replace("CANDIDATE_SHA='${{ steps.control.outputs.candidate_sha256 }}'\n            CANDIDATE_RUN='${{ steps.control.outputs.candidate_run_id }}'\n            ANCHORS_RUN='${{ steps.control.outputs.anchors_run_id }}'","CANDIDATE_SHA='${{ inputs.candidate_sha256 }}'\n            CANDIDATE_RUN='${{ inputs.candidate_run_id }}'\n            ANCHORS_RUN='${{ inputs.anchors_run_id }}'",1)
 pat=re.compile(r'\n\s*- name: "18 Install the frozen frontend contract \(npm ci\) so the browser journey can run".*?(?=\n\s*- name: "19 |\n\s*- name: "18 Run|\n\s*- name: "19 Run)',re.S)
 t,n=pat.subn('\n',t,count=1)
 if n==0:
  start=t.find('\n      - name: "18 Install the frozen frontend contract')
  if start!=-1:
   nxt=t.find('\n      - name:',start+10)
   if nxt==-1: raise RuntimeError('cannot bound frontend install step')
   t=t[:start]+t[nxt:]
 t=t.replace('- name: "19 Run the complete API-02 validator','- name: "18 Run the complete API-02 validator')
 t=t.replace('- name: "20 Assert complete 32-gate PASS','- name: "19 Assert complete 32-gate PASS')
 t=t.replace('- name: "21 Publish authoritative evidence','- name: "20 Publish authoritative evidence')
 t=t.replace('- name: "22 Authoritative result','- name: "21 Authoritative result')
 p.write_text(t)

def patch_json_current_candidate(path:pathlib.Path)->None:
 try:d=json.loads(path.read_text())
 except Exception:return
 def walk(v):
  if isinstance(v,dict):
   if str(v.get('filename','')).endswith('_C10.zip') or str(v.get('root','')).endswith('_C10'):
    if v.get('role')=='C9':v['role']='C10'
    if v.get('version')=='0.1_C9':v['version']='0.1_C10'
   for z in v.values():walk(z)
  elif isinstance(v,list):
   for z in v:walk(z)
 walk(d);path.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')

def patch_tree(root:pathlib.Path)->None:
 lg=root/'scripts/api02/lineage_gates.py'; s=lg.read_text()
 s=s.replace('CANDIDATE_ROLE = "C9"','CANDIDATE_ROLE = "C10"')
 s=s.replace('CANDIDATE_CLASSIFICATION = "ACCEPTANCE_PATH_RECOVERABILITY_CORRECTION_CANDIDATE"','CANDIDATE_CLASSIFICATION = "ACCEPTANCE_HARNESS_CLEAN_TREE_CORRECTION_CANDIDATE"')
 s=s.replace('ENTERING_ROLE = "C8"','ENTERING_ROLE = "C9"')
 s=s.replace('"sha256": "7836135f2e656c998b224c56698ad337c9474238cc241d250add710ba79ecaef",\n    "size": 34641029,\n    "files": 3948,','"sha256": "'+C9_SHA+'",\n    "size": '+str(C9_SIZE)+',\n    "files": 3949,')
 s=s.replace('"internal_review_findings": ("IR-C8-01",),','"internal_review_findings": ("IR-C9-01", "IR-C9-02"),')
 lg.write_text(s)
 patch_workflow(root/'.github/workflows/api02-accept.yml')
 p=root/'docs/api/API-02/API02_LINEAGE.json'; d=json.loads(p.read_text())
 d['candidate'].update({'role':'C10','version':'0.1_C10','filename':C10_NAME,'root':C10_ROOT,'classification':'ACCEPTANCE_HARNESS_CLEAN_TREE_CORRECTION_CANDIDATE'})
 d['entering_baseline'].update({'role':'C9','version':'0.1_C9','filename':C9_NAME,'root':C9_NAME[:-4],'sha256':C9_SHA,'size':C9_SIZE,'files':3949,'status':'CORRECTED_BY_THIS_CANDIDATE / NOT ACCEPTED','internal_review_findings':['IR-C9-01','IR-C9-02'],'measurement_note':'`size` and `files` are measured from the exact C9 entering archive by `lineage_gates.anchor_file_problems`: `files` is the number of rows the entering archive own SHA256SUMS.txt lists.'})
 d['sealed_accounting']['layer_a']='docs/api/API-02/API02_API01C5_TO_C10_EXACT_INVENTORY.json'; d['sealed_accounting']['correction_record']='docs/api/API-02/API02_C9_TO_C10_CORRECTION_INVENTORY.json'
 p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
 for rel in ['docs/api/API-02/01_EXECUTIVE_RESULT.md','docs/api/API-02/03_ENTERING_BASELINE.md','docs/api/API-02/11_VOTING_IDENTITY_ISOLATION.md']:
  q=root/rel; x=q.read_text()
  x=x.replace('API02_C8_TO_C9_CORRECTION_INVENTORY.json','API02_C9_TO_C10_CORRECTION_INVENTORY.json').replace('API02_API01C5_TO_C9_EXACT_INVENTORY.json','API02_API01C5_TO_C10_EXACT_INVENTORY.json')
  x=x.replace('API-02 C9 (this candidate)','API-02 C10 (this candidate)').replace('API-02 C9 candidate','API-02 C10 candidate')
  x=x.replace('EPD2_API02_AUTHENTICATION_AND_AUTHORIZATION_RUNTIME_CANDIDATE_0.1_C8.zip',C9_NAME).replace('7836135f2e656c998b224c56698ad337c9474238cc241d250add710ba79ecaef',C9_SHA)
  x=x.replace('C8 → C9','C9 → C10').replace('C8 -> C9','C9 -> C10')
  q.write_text(x)
 hist=root/'docs/api/API-02/API02_C8_TO_C9_CORRECTION_REPORT.md'; x=hist.read_text()
 x=x.replace('# API-02 C8 → C9 correction report','# API-02 C8 → C9 correction report — HISTORICAL',1)
 x=x.replace('## Acceptance condition','## HISTORICAL acceptance condition at C9 issuance',1)
 if 'HISTORICAL disposition recorded by C10' not in x:
  x += '\n## HISTORICAL disposition recorded by C10\n\nC9 was not accepted. Authoritative GitHub run `33382241821` reached the complete validator and returned `API02_RESULT:FAIL`; the failure exposed acceptance-harness contamination of the sealed candidate tree before gate 0. C10 supersedes C9 as the correction candidate and does not treat C9 as an accepted predecessor.\n'
 hist.write_text(x)
 (root/'docs/api/API-02/API02_C9_TO_C10_CORRECTION_REPORT.md').write_text(f'''# API-02 C9 → C10 correction report\n\n**Candidate:** C10 — `ACCEPTANCE_HARNESS_CLEAN_TREE_CORRECTION_CANDIDATE`  \n**Entering baseline:** exact C9 archive, SHA-256 `{C9_SHA}`, {C9_SIZE:,} bytes.  \n**Acceptance predecessor:** API-01 C5 remains the sole accepted predecessor. C9 was not accepted.\n\n## IR-C9-01 — authoritative acceptance contaminated the sealed candidate tree\n\nAuthoritative GitHub run `33382241821` verified the exact C9/API-01/DATA-06/C8 byte bindings, archive safety, sealed checksums, Layer A/B accounting, exact CPython/Node/npm/PostgreSQL toolchains, frozen dependencies and fail-closed Chromium. The complete validator then failed gate 0 because the C9 workflow had executed `npm ci` inside the freshly extracted sealed candidate before validation, creating `node_modules` and symlinks which gate 0 correctly forbids. This also invalidated the DATA-06 Phase-A regression measurement.\n\nC10 removes only that premature pre-validator frontend-install step. The full repository contract in gate 17 Phase A already owns `npm ci`; gate 18 runs after it and therefore receives the installed frontend dependencies without contaminating the candidate before gate 0.\n\n## IR-C9-02 — exact uv probe was syntactically over-strict\n\nAuthoritative run `33381997651` successfully installed uv 0.12.5 and exact CPython 3.12.12/3.13.7, then a harness line using an exact-line `grep` rejected `uv --version` because current uv includes a platform suffix. C10 changes that probe to require the exact `uv 0.12.5` version prefix while permitting the informational target suffix.\n\n## Runtime neutrality\n\nC10 changes no authentication, authorization, identity, voting-boundary, persistence, route, cryptographic, API or frontend runtime semantics. The C9 → C10 correction inventory and builder both fail closed if any runtime path changes.\n\n## Acceptance condition\n\nC10 remains `CANDIDATE_NOT_ACCEPTED` until an independent authoritative workflow run on the exact sealed C10 ZIP succeeds and its run/evidence identity is recorded in canonical project governance.\n\nNOT PRODUCTION READY. NOT LEGALLY ACTIVATED. NOT SECURITY CERTIFIED.\n''')
 q=root/'scripts/api02/acceptance_path_identity.py'; q.write_text(q.read_text().replace('form `…_0.1_C9`','form `…_0.1_C10`'))
 q=root/'scripts/api02/build_exact_inventories.py'; q.write_text(q.read_text().replace('# --- C9 ------------------------------------------------------------','# --- C10 -----------------------------------------------------------'))
 for rel in ['SHA256SUMS.txt','docs/api/API-02/API02_API01C5_TO_C9_EXACT_INVENTORY.json','docs/api/API-02/API02_C8_TO_C9_CORRECTION_INVENTORY.json','docs/api/API-02/API02_SEALED_FILE_MANIFEST.json','docs/api/API-02/API02_STALE_STATE_AUDIT.json','validation/api02/evidence_consistency_result.json']:
  q=root/rel
  if q.exists():q.unlink()
 for q in (root/'validation/api02').glob('*.json'): patch_json_current_candidate(q)
 for rel in ['validation/api02/candidate_identity_registry_result.json','validation/api02/candidate_identity_result.json']:
  q=root/rel
  if not q.exists():continue
  d=json.loads(q.read_text());d['candidate']='C10';d['candidate_classification']='ACCEPTANCE_HARNESS_CLEAN_TREE_CORRECTION_CANDIDATE';d['entering_role']='C9'
  if isinstance(d.get('declarations'),list):d['declarations']=[str(v).replace('API02_API01C5_TO_C9_EXACT_INVENTORY.json','API02_API01C5_TO_C10_EXACT_INVENTORY.json').replace('API02_C8_TO_C9_CORRECTION_INVENTORY.json','API02_C9_TO_C10_CORRECTION_INVENTORY.json') for v in d['declarations']]
  for c in d.get('checks',[]):
   if isinstance(c,dict) and isinstance(c.get('check'),str):c['check']=c['check'].replace('declares C9','declares C10').replace('ACCEPTANCE_PATH_RECOVERABILITY_CORRECTION_CANDIDATE','ACCEPTANCE_HARNESS_CLEAN_TREE_CORRECTION_CANDIDATE').replace('entering baseline is C8','entering baseline is C9')
  q.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
 sys.path.insert(0,str(root/'scripts/api02'));import acceptance_path_identity as api
 rec=api.identity_record(root); assert not rec['problems'],rec['problems']
 (root/'validation/api02/acceptance_path_identity_result.json').write_text(json.dumps(rec,indent=2,sort_keys=True)+'\n')
 for d in root.rglob('__pycache__'):shutil.rmtree(d,ignore_errors=True)

def package(root:pathlib.Path,out:pathlib.Path)->pathlib.Path:
 target=out/C10_NAME; files=[(p.relative_to(root).as_posix(),p) for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts];files.sort(key=lambda x:x[0])
 with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6,strict_timestamps=True) as z:
  for rel,p in files:
   zi=zipfile.ZipInfo(C10_ROOT+'/'+rel,(2026,8,31,0,0,0));zi.compress_type=zipfile.ZIP_DEFLATED;zi.create_system=3;zi.external_attr=(stat.S_IMODE(p.stat().st_mode)<<16);z.writestr(zi,p.read_bytes(),compress_type=zipfile.ZIP_DEFLATED,compresslevel=6)
 return target

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--out',required=True);ap.add_argument('--patch-only',action='store_true');ap.add_argument('--package-only',action='store_true');a=ap.parse_args();root=pathlib.Path(a.root).resolve();out=pathlib.Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True)
 if a.patch_only:patch_tree(root);print('API02_C10_PATCH:PASS');return
 if a.package_only:
  z=package(root,out);h=sha(z);(out/'candidate_sha256.txt').write_text(h+'  '+z.name+'\n');(out/'candidate_meta.json').write_text(json.dumps({'candidate':'C10','filename':z.name,'sha256':h,'size':z.stat().st_size,'root':C10_ROOT},indent=2)+'\n');print(z.stat().st_size,h);return
 patch_tree(root);z=package(root,out);print(z,sha(z))
if __name__=='__main__':main()
