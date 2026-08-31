from __future__ import annotations
import argparse, hashlib, json, os, pathlib, re, shutil, stat, subprocess, sys, zipfile

C8_SHA='7836135f2e656c998b224c56698ad337c9474238cc241d250add710ba79ecaef'
C8_SIZE=34641029
API01_SHA='cea2fb0e23ee174e802ec1899cf62e570e5c8659a0f31c7e6c3c3955bffa3d27'
DATA06_SHA='8cba01997e4943f6d3c2b3fc1fe11e2c3527cd6c39123171a827fb8e3669cbf1'
C8_NAME='EPD2_API02_AUTHENTICATION_AND_AUTHORIZATION_RUNTIME_CANDIDATE_0.1_C8.zip'
C9_ROOT='EPD2_API02_AUTHENTICATION_AND_AUTHORIZATION_RUNTIME_CANDIDATE_0.1_C9'
C9_NAME=C9_ROOT+'.zip'

def sha(p:pathlib.Path)->str:
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''): h.update(b)
 return h.hexdigest()

def run(root:pathlib.Path,*args:str)->None:
 print('+',*args,flush=True)
 subprocess.run([sys.executable,*args],cwd=root,check=True,env=os.environ.copy())

def patch_workflow(p:pathlib.Path)->None:
 t=p.read_text()
 t=t.replace('authoritative acceptance workflow (C8)', 'authoritative acceptance workflow (C9)')
 t=t.replace('CANDIDATE_0.1_C8.zip','CANDIDATE_0.1_C9.zip')
 t=t.replace('CANDIDATE_ROLE: C8','CANDIDATE_ROLE: C9')
 t=t.replace('CANDIDATE_NAME: EPD2_API02_AUTHENTICATION_AND_AUTHORIZATION_RUNTIME_CANDIDATE_0.1_C8','CANDIDATE_NAME: EPD2_API02_AUTHENTICATION_AND_AUTHORIZATION_RUNTIME_CANDIDATE_0.1_C9')
 t=t.replace('ENTERING_CANDIDATE_NAME: EPD2_API02_AUTHENTICATION_AND_AUTHORIZATION_RUNTIME_CANDIDATE_0.1_C7.zip','ENTERING_CANDIDATE_NAME: EPD2_API02_AUTHENTICATION_AND_AUTHORIZATION_RUNTIME_CANDIDATE_0.1_C8.zip')
 t=t.replace('ENTERING_CANDIDATE_SHA256: 87e1a36da39b5427e94b619f075a117af8a996b44d601d18714b22f40f55a8fd','ENTERING_CANDIDATE_SHA256: '+C8_SHA)
 t=t.replace('…API02…CANDIDATE_0.1_C7.zip  87e1a36d…','…API02…CANDIDATE_0.1_C8.zip  7836135f…')
 t=t.replace('api02-c8-acceptance-evidence','api02-c9-acceptance-evidence')
 needle='on:\n  workflow_dispatch:\n'
 repl="on:\n  push:\n    branches:\n      - tmp/api02-c9-canonical-accept\n    paths:\n      - 'handoff/API-02/C9_ACCEPTANCE_INPUTS.env'\n  workflow_dispatch:\n"
 if needle not in t: raise RuntimeError('workflow on: block not found')
 t=t.replace(needle,repl,1)
 checkout='''      - name: "01 Check out repository (provenance only — GITHUB_SHA is recorded, nothing is read from it)"\n        uses: actions/checkout@v4\n        with:\n          persist-credentials: false\n'''
 control=checkout+'''\n      - name: "01a Resolve externally pinned exact-byte acceptance inputs"\n        id: control\n        shell: bash\n        run: |\n          set -euo pipefail\n          if [ "${GITHUB_EVENT_NAME}" = "workflow_dispatch" ]; then\n            CANDIDATE_SHA='${{ inputs.candidate_sha256 }}'\n            CANDIDATE_RUN='${{ inputs.candidate_run_id }}'\n            ANCHORS_RUN='${{ inputs.anchors_run_id }}'\n          else\n            CONTROL='handoff/API-02/C9_ACCEPTANCE_INPUTS.env'\n            test -f "$CONTROL" || { echo "::error::missing $CONTROL"; exit 1; }\n            CANDIDATE_SHA="$(grep '^candidate_sha256=' "$CONTROL" | cut -d= -f2-)"\n            CANDIDATE_RUN="$(grep '^candidate_run_id=' "$CONTROL" | cut -d= -f2-)"\n            ANCHORS_RUN="$(grep '^anchors_run_id=' "$CONTROL" | cut -d= -f2-)"\n          fi\n          [[ "$CANDIDATE_SHA" =~ ^[0-9a-f]{64}$ ]] || { echo "::error::invalid candidate_sha256"; exit 1; }\n          [[ "$CANDIDATE_RUN" =~ ^[0-9]+$ ]] || { echo "::error::invalid candidate_run_id"; exit 1; }\n          [[ "$ANCHORS_RUN" =~ ^[0-9]+$ ]] || { echo "::error::invalid anchors_run_id"; exit 1; }\n          echo "candidate_sha256=$CANDIDATE_SHA" >> "$GITHUB_OUTPUT"\n          echo "candidate_run_id=$CANDIDATE_RUN" >> "$GITHUB_OUTPUT"\n          echo "anchors_run_id=$ANCHORS_RUN" >> "$GITHUB_OUTPUT"\n'''
 if checkout not in t: raise RuntimeError('checkout step not found')
 t=t.replace(checkout,control,1)
 t=t.replace("${{ inputs.candidate_run_id != '' }}","${{ steps.control.outputs.candidate_run_id != '' }}")
 t=t.replace("${{ inputs.anchors_run_id != '' }}","${{ steps.control.outputs.anchors_run_id != '' }}")
 t=t.replace('${{ inputs.candidate_run_id }}','${{ steps.control.outputs.candidate_run_id }}')
 t=t.replace('${{ inputs.anchors_run_id }}','${{ steps.control.outputs.anchors_run_id }}')
 t=t.replace('${{ inputs.candidate_sha256 }}','${{ steps.control.outputs.candidate_sha256 }}')
 p.write_text(t)

def patch_tree(root:pathlib.Path)->None:
 lg=root/'scripts/api02/lineage_gates.py'; s=lg.read_text()
 s=s.replace('CANDIDATE_ROLE = "C8"','CANDIDATE_ROLE = "C9"')
 s=s.replace('CANDIDATE_CLASSIFICATION = "ACCEPTANCE_PATH_IDENTITY_AND_LINEAGE_INTEGRITY_CORRECTION_CANDIDATE"','CANDIDATE_CLASSIFICATION = "ACCEPTANCE_PATH_RECOVERABILITY_CORRECTION_CANDIDATE"')
 s=s.replace('ENTERING_ROLE = "C7"','ENTERING_ROLE = "C8"')
 s=s.replace('"sha256": "87e1a36da39b5427e94b619f075a117af8a996b44d601d18714b22f40f55a8fd",\n    "size": 34569523,\n    "files": 3940,','"sha256": "'+C8_SHA+'",\n    "size": 34641029,\n    "files": 3948,')
 s=s.replace('"internal_review_findings": ("IR-C7-01", "IR-C7-02", "IR-C7-03", "IR-C7-04"),','"internal_review_findings": ("IR-C8-01",),')
 lg.write_text(s)
 patch_workflow(root/'.github/workflows/api02-accept.yml')
 p=root/'docs/api/API-02/API02_LINEAGE.json'; d=json.loads(p.read_text())
 d['candidate'].update({'role':'C9','version':'0.1_C9','filename':C9_NAME,'root':C9_ROOT,'classification':'ACCEPTANCE_PATH_RECOVERABILITY_CORRECTION_CANDIDATE'})
 d['entering_baseline'].update({'role':'C8','version':'0.1_C8','filename':C8_NAME,'root':C8_NAME[:-4],'sha256':C8_SHA,'size':C8_SIZE,'files':3948,'status':'CORRECTED_BY_THIS_CANDIDATE / NOT ACCEPTED','internal_review_findings':['IR-C8-01'],'measurement_note':'`size` and `files` are measured from the exact C8 entering archive by `lineage_gates.anchor_file_problems`: `files` is the number of rows the entering archive own SHA256SUMS.txt lists.'})
 sa=d['sealed_accounting']; sa['layer_a']='docs/api/API-02/API02_API01C5_TO_C9_EXACT_INVENTORY.json'; sa['correction_record']='docs/api/API-02/API02_C8_TO_C9_CORRECTION_INVENTORY.json'
 raw=json.dumps(d,ensure_ascii=False)
 raw=raw.replace('docs/api/API-02/API02_API01C5_TO_C8_EXACT_INVENTORY.json','docs/api/API-02/API02_API01C5_TO_C9_EXACT_INVENTORY.json').replace('docs/api/API-02/API02_C7_TO_C8_CORRECTION_INVENTORY.json','docs/api/API-02/API02_C8_TO_C9_CORRECTION_INVENTORY.json').replace('"delta": "C7 → C8"','"delta": "C8 → C9"')
 d=json.loads(raw); p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
 for rel in ['docs/api/API-02/01_EXECUTIVE_RESULT.md','docs/api/API-02/03_ENTERING_BASELINE.md','docs/api/API-02/11_VOTING_IDENTITY_ISOLATION.md','docs/api/API-02/15_TEST_EVIDENCE.md','docs/api/API-02/16_OPEN_GAPS.md','docs/api/API-02/17_HANDOVER_TO_API03.md']:
  q=root/rel
  if not q.exists(): continue
  x=q.read_text().replace('API02_C7_TO_C8_CORRECTION_INVENTORY.json','API02_C8_TO_C9_CORRECTION_INVENTORY.json').replace('API02_API01C5_TO_C8_EXACT_INVENTORY.json','API02_API01C5_TO_C9_EXACT_INVENTORY.json').replace('EPD2_API02_AUTHENTICATION_AND_AUTHORIZATION_RUNTIME_CANDIDATE_0.1_C7.zip',C8_NAME).replace('87e1a36da39b5427e94b619f075a117af8a996b44d601d18714b22f40f55a8fd',C8_SHA).replace('C7 → C8','C8 → C9').replace('C7 -> C8','C8 -> C9').replace('API-02 C8 (this candidate)','API-02 C9 (this candidate)').replace('API-02 C8 candidate','API-02 C9 candidate').replace('(root `…_CANDIDATE_0.1_C8`)', '(DATA-06 root `…_CANDIDATE_0.1_C8`)')
  q.write_text(x)
 (root/'docs/api/API-02/API02_C8_TO_C9_CORRECTION_REPORT.md').write_text(f'''# API-02 C8 → C9 correction report\n\n**Candidate:** C9 — `ACCEPTANCE_PATH_RECOVERABILITY_CORRECTION_CANDIDATE`  \n**Entering baseline:** exact C8 archive, SHA-256 `{C8_SHA}`, 34,641,029 bytes.  \n**Acceptance predecessor:** API-01 C5 remains the sole accepted predecessor. C8 is not and has never been an accepted API-02 predecessor.\n\n## IR-C8-01 — unrecoverable rejected-candidate anchor in authoritative acceptance path\n\nC8 correctly repaired candidate identity and lineage integrity, but its authoritative workflow still required the exact rejected C7 archive as a mandatory correction-round anchor. Independent recovery established that the C7 archive is not retained in Git history or available canonical transport, while the C8 lineage itself correctly states that C7 was never accepted and is not an acceptance predecessor. That made authoritative review of otherwise exact C8 bytes operationally impossible.\n\nC9 changes no authentication, authorization, identity, voting-boundary, persistence, route, cryptographic or frontend runtime semantics. It corrects only the acceptance path: the exact C8 archive becomes the entering baseline for this correction round, while accepted API-01 C5 remains the sole acceptance predecessor and DATA-06 remains the inherited data anchor. The C8 → C9 inventory must therefore prove that every changed path is governance, validation, evidence, checksum, packaging or acceptance-path material. Any runtime delta is a sealing blocker.\n\n## Acceptance condition\n\nC9 remains `CANDIDATE_NOT_ACCEPTED` until an independent authoritative workflow run on the exact sealed C9 ZIP succeeds and its run/evidence identity is recorded in canonical project governance.\n\nNOT PRODUCTION READY. NOT LEGALLY ACTIVATED. NOT SECURITY CERTIFIED.\n''')
 for rel in ['SHA256SUMS.txt','docs/api/API-02/API02_API01C5_TO_C8_EXACT_INVENTORY.json','docs/api/API-02/API02_C7_TO_C8_CORRECTION_INVENTORY.json','docs/api/API-02/API02_SEALED_FILE_MANIFEST.json','docs/api/API-02/API02_STALE_STATE_AUDIT.json','validation/api02/evidence_consistency_result.json']:
  q=root/rel
  if q.exists(): q.unlink()
 fixes={
 'scripts/api02/acceptance_path_identity.py':[('form `…_0.1_C8`','form `…_0.1_C9`')],
 'scripts/api02/build_exact_inventories.py':[('# --- C8 ','# --- C9 ')],
 'scripts/api02/validator_selftest.py':[('a current C8 document calling itself an older round','a current candidate document calling itself an older round')],
 }
 for rel,rs in fixes.items():
  q=root/rel; x=q.read_text()
  for a,b in rs:x=x.replace(a,b)
  q.write_text(x)
 for q in (root/'validation/api02').glob('*.json'):
  try: x=q.read_text()
  except: continue
  x=x.replace('API02-C8 transition inventory and the C7 -> C8 correction record','API02-C9 transition inventory and the C8 -> C9 correction record').replace('EPD2_API02_AUTHENTICATION_AND_AUTHORIZATION_RUNTIME_CANDIDATE_0.1_C8.zip',C9_NAME).replace('EPD2_API02_AUTHENTICATION_AND_AUTHORIZATION_RUNTIME_CANDIDATE_0.1_C8',C9_ROOT).replace('"candidate_role": "C8"','"candidate_role": "C9"').replace('"role": "C8"','"role": "C9"').replace('"version": "0.1_C8"','"version": "0.1_C9"')
  q.write_text(x)
 q=root/'validation/api02/acceptance_path_identity_result.json'
 if q.exists():
  d=json.loads(q.read_text())
  for row in d.get('bindings',{}).get('candidate_identity',[]):
   if row.get('declaration')=='CANDIDATE_ROLE': row['declared']=row['expected']='C9'
  d['candidate_role']='C9'; q.write_text(json.dumps(d,indent=2,sort_keys=True,ensure_ascii=False)+'\n')
 for rel in ['validation/api02/candidate_identity_registry_result.json','validation/api02/candidate_identity_result.json']:
  q=root/rel
  if not q.exists(): continue
  d=json.loads(q.read_text())
  d['candidate']='C9'; d['candidate_classification']='ACCEPTANCE_PATH_RECOVERABILITY_CORRECTION_CANDIDATE'; d['entering_role']='C8'
  if isinstance(d.get('declarations'),list):
   d['declarations']=[str(x).replace('API02_API01C5_TO_C8_EXACT_INVENTORY.json','API02_API01C5_TO_C9_EXACT_INVENTORY.json').replace('API02_C7_TO_C8_CORRECTION_INVENTORY.json','API02_C8_TO_C9_CORRECTION_INVENTORY.json') for x in d['declarations']]
  for c in d.get('checks',[]):
   if isinstance(c,dict) and isinstance(c.get('check'),str):
    c['check']=c['check'].replace('declares C8','declares C9').replace('ACCEPTANCE_PATH_IDENTITY_AND_LINEAGE_INTEGRITY_CORRECTION_CANDIDATE','ACCEPTANCE_PATH_RECOVERABILITY_CORRECTION_CANDIDATE').replace('entering baseline is C7','entering baseline is C8')
  q.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')

def main()->int:
 ap=argparse.ArgumentParser(); ap.add_argument('--root',required=True); ap.add_argument('--api01',required=True); ap.add_argument('--data06',required=True); ap.add_argument('--entering',required=True); ap.add_argument('--out',required=True); ap.add_argument('--patch-only',action='store_true'); ap.add_argument('--package-only',action='store_true'); a=ap.parse_args()
 root=pathlib.Path(a.root).resolve(); api01=pathlib.Path(a.api01).resolve(); data06=pathlib.Path(a.data06).resolve(); entering=pathlib.Path(a.entering).resolve(); out=pathlib.Path(a.out).resolve(); out.mkdir(parents=True,exist_ok=True)
 assert root.name==C9_ROOT,root
 for p,h,size in [(entering,C8_SHA,C8_SIZE),(api01,API01_SHA,None),(data06,DATA06_SHA,None)]:
  assert p.is_file(),p
  assert sha(p)==h,(p,sha(p),h)
  if size is not None: assert p.stat().st_size==size
 os.environ['API02_ACCEPTED_API01_C5_ZIP']=str(api01); os.environ['API02_ACCEPTED_API01_ZIP']=str(api01); os.environ['API02_ACCEPTED_DATA06_ZIP']=str(data06); os.environ['API02_ENTERING_CANDIDATE_ZIP']=str(entering); os.environ['PYTHONDONTWRITEBYTECODE']='1'
 if not a.package_only:
  patch_tree(root)
 if a.patch_only:
  print('C9_PATCH:PASS',flush=True); return 0
 if a.package_only:
  zpath=out/C9_NAME
  files=[(p.relative_to(root).as_posix(),p) for p in root.rglob('*') if p.is_file() and not p.is_symlink()]
  files.sort(key=lambda x:x[0])
  with zipfile.ZipFile(zpath,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6,strict_timestamps=True) as z:
   for rel,p in files:
    zi=zipfile.ZipInfo(C9_ROOT+'/'+rel,(2026,8,31,0,0,0)); zi.compress_type=zipfile.ZIP_DEFLATED; zi.create_system=3; zi.external_attr=(stat.S_IMODE(p.stat().st_mode)<<16)
    z.writestr(zi,p.read_bytes(),compress_type=zipfile.ZIP_DEFLATED,compresslevel=6)
  h=sha(zpath); size=zpath.stat().st_size; (out/'candidate_sha256.txt').write_text(h+'  '+C9_NAME+'\n'); (out/'candidate_meta.json').write_text(json.dumps({'filename':C9_NAME,'sha256':h,'size':size,'root':C9_ROOT,'entering_sha256':C8_SHA,'acceptance_predecessor_sha256':API01_SHA,'data_anchor_sha256':DATA06_SHA},indent=2)+'\n')
  with zipfile.ZipFile(zpath) as z: assert z.testzip() is None
  print('C9_BUILD:PASS',size,h,flush=True); return 0
 for script in ['scripts/api02/build_authorization_registers.py','scripts/api02/build_mandatory_tests.py','scripts/api02/build_v23_reconciliation.py','scripts/api02/build_exact_inventories.py','scripts/api02/build_correction_inventory.py']:
  run(root,script)
 run(root,'scripts/api02/build_evidence_state.py')
 subprocess.run([sys.executable,'-c','import sys;sys.path.insert(0,"scripts/api02");import finalize_candidate as f;f.write_validation_txt()'],cwd=root,check=True,env=os.environ.copy())
 run(root,'scripts/api02/build_stale_audit.py'); run(root,'scripts/api02/build_consistency_result.py'); run(root,'scripts/api02/build_correction_inventory.py'); run(root,'scripts/api02/build_bsi_classification.py'); run(root,'scripts/api02/build_correction_inventory.py'); run(root,'scripts/api02/build_bsi_classification.py','--check'); run(root,'scripts/api02/build_sealed_accounting.py','--layer-a-only')
 subprocess.run([sys.executable,'-c','import sys;sys.path.insert(0,"scripts/api02");import finalize_candidate as f;print("CHECKSUM_ROWS",f.write_checksums())'],cwd=root,check=True,env=os.environ.copy())
 run(root,'scripts/api02/build_sealed_accounting.py','--layer-b-only'); run(root,'scripts/api02/finalize_candidate.py','--check'); run(root,'scripts/api02/acceptance_path_identity.py','--root','.')
 zpath=out/C9_NAME
 files=[(p.relative_to(root).as_posix(),p) for p in root.rglob('*') if p.is_file() and not p.is_symlink()]
 files.sort(key=lambda x:x[0])
 with zipfile.ZipFile(zpath,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6,strict_timestamps=True) as z:
  for rel,p in files:
   zi=zipfile.ZipInfo(C9_ROOT+'/'+rel,(2026,8,31,0,0,0)); zi.compress_type=zipfile.ZIP_DEFLATED; zi.create_system=3; zi.external_attr=(stat.S_IMODE(p.stat().st_mode)<<16)
   z.writestr(zi,p.read_bytes(),compress_type=zipfile.ZIP_DEFLATED,compresslevel=6)
 h=sha(zpath); size=zpath.stat().st_size
 (out/'candidate_sha256.txt').write_text(h+'  '+C9_NAME+'\n'); (out/'candidate_meta.json').write_text(json.dumps({'filename':C9_NAME,'sha256':h,'size':size,'root':C9_ROOT,'entering_sha256':C8_SHA,'acceptance_predecessor_sha256':API01_SHA,'data_anchor_sha256':DATA06_SHA},indent=2)+'\n')
 with zipfile.ZipFile(zpath) as z: assert z.testzip() is None
 print('C9_BUILD:PASS',size,h,flush=True)
 return 0
if __name__=='__main__': raise SystemExit(main())
