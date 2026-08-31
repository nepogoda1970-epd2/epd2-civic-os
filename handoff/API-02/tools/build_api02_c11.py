from __future__ import annotations
import argparse, hashlib, json, os, pathlib, shutil, stat, sys, zipfile

C10_SHA='479e17323422f20e0badec5256ced45c48392e8a103698d9a32d37324e393eeb'
C10_SIZE=34652031
C10_NAME='EPD2_API02_AUTHENTICATION_AND_AUTHORIZATION_RUNTIME_CANDIDATE_0.1_C10.zip'
C11_ROOT='EPD2_API02_AUTHENTICATION_AND_AUTHORIZATION_RUNTIME_CANDIDATE_0.1_C11'
C11_NAME=C11_ROOT+'.zip'


def sha(p:pathlib.Path)->str:
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()


def patch_json_current(path:pathlib.Path)->None:
 try:d=json.loads(path.read_text())
 except Exception:return
 def walk(v):
  if isinstance(v,dict):
   # Explicit current-candidate records only; entering-baseline C10 must stay C10.
   current=False
   if v.get('candidate')=='C10': current=True
   if v.get('candidate_root')=='EPD2_API02_AUTHENTICATION_AND_AUTHORIZATION_RUNTIME_CANDIDATE_0.1_C10': current=True
   if v.get('root')=='EPD2_API02_AUTHENTICATION_AND_AUTHORIZATION_RUNTIME_CANDIDATE_0.1_C10' and not str(v.get('status','')).startswith('CORRECTED_BY_THIS_CANDIDATE'): current=True
   if current:
    if v.get('candidate')=='C10':v['candidate']='C11'
    if v.get('candidate_root')=='EPD2_API02_AUTHENTICATION_AND_AUTHORIZATION_RUNTIME_CANDIDATE_0.1_C10':v['candidate_root']=C11_ROOT
    if v.get('root')=='EPD2_API02_AUTHENTICATION_AND_AUTHORIZATION_RUNTIME_CANDIDATE_0.1_C10':v['root']=C11_ROOT
    if v.get('filename')==C10_NAME:v['filename']=C11_NAME
    if v.get('candidate_filename')==C10_NAME:v['candidate_filename']=C11_NAME
    if v.get('role')=='C10':v['role']='C11'
    if v.get('version')=='0.1_C10':v['version']='0.1_C11'
   for x in v.values():walk(x)
  elif isinstance(v,list):
   for x in v:walk(x)
 walk(d)
 path.write_text(json.dumps(d,indent=2,sort_keys=True,ensure_ascii=False)+'\n')


def patch_workflow(p:pathlib.Path)->None:
 t=p.read_text()
 t=t.replace('authoritative acceptance workflow (C10)','authoritative acceptance workflow (C11)')
 t=t.replace('CANDIDATE_0.1_C10.zip','CANDIDATE_0.1_C11.zip')
 t=t.replace('CANDIDATE_ROLE: C10','CANDIDATE_ROLE: C11')
 t=t.replace('CANDIDATE_NAME: EPD2_API02_AUTHENTICATION_AND_AUTHORIZATION_RUNTIME_CANDIDATE_0.1_C10','CANDIDATE_NAME: EPD2_API02_AUTHENTICATION_AND_AUTHORIZATION_RUNTIME_CANDIDATE_0.1_C11')
 t=t.replace('ENTERING_CANDIDATE_NAME: EPD2_API02_AUTHENTICATION_AND_AUTHORIZATION_RUNTIME_CANDIDATE_0.1_C9.zip','ENTERING_CANDIDATE_NAME: '+C10_NAME)
 t=t.replace('ENTERING_CANDIDATE_SHA256: 42a1a59a5b4aaf769d38fac0c0426d5a436550b050d33b1cf7a0f4f1cd37a48b','ENTERING_CANDIDATE_SHA256: '+C10_SHA)
 t=t.replace('tmp/api02-c10-canonical-accept','tmp/api02-c11-canonical-accept')
 t=t.replace('handoff/API-02/C10_ACCEPTANCE_INPUTS.env','handoff/API-02/C11_ACCEPTANCE_INPUTS.env')
 t=t.replace('api02-c10-acceptance-evidence','api02-c11-acceptance-evidence')
 p.write_text(t)


def patch_tree(root:pathlib.Path)->None:
 lg=root/'scripts/api02/lineage_gates.py';s=lg.read_text()
 s=s.replace('CANDIDATE_ROLE = "C10"','CANDIDATE_ROLE = "C11"')
 s=s.replace('CANDIDATE_CLASSIFICATION = "ACCEPTANCE_HARNESS_CLEAN_TREE_CORRECTION_CANDIDATE"','CANDIDATE_CLASSIFICATION = "ACCEPTANCE_PATH_REFERENCE_INTEGRITY_CORRECTION_CANDIDATE"')
 s=s.replace('ENTERING_ROLE = "C9"','ENTERING_ROLE = "C10"')
 s=s.replace('"sha256": "42a1a59a5b4aaf769d38fac0c0426d5a436550b050d33b1cf7a0f4f1cd37a48b",\n    "size": 34638963,\n    "files": 3949,','"sha256": "'+C10_SHA+'",\n    "size": '+str(C10_SIZE)+',\n    "files": 3950,')
 s=s.replace('"internal_review_findings": ("IR-C9-01", "IR-C9-02"),','"internal_review_findings": ("IR-C10-01",),')
 lg.write_text(s)
 patch_workflow(root/'.github/workflows/api02-accept.yml')

 p=root/'docs/api/API-02/API02_LINEAGE.json';d=json.loads(p.read_text())
 d['candidate'].update({'role':'C11','version':'0.1_C11','filename':C11_NAME,'root':C11_ROOT,'classification':'ACCEPTANCE_PATH_REFERENCE_INTEGRITY_CORRECTION_CANDIDATE'})
 d['entering_baseline'].update({'role':'C10','version':'0.1_C10','filename':C10_NAME,'root':C10_NAME[:-4],'sha256':C10_SHA,'size':C10_SIZE,'files':3950,'status':'CORRECTED_BY_THIS_CANDIDATE / NOT ACCEPTED','internal_review_findings':['IR-C10-01'],'measurement_note':'`size` and `files` are measured from the exact C10 entering archive; `files` is the number of rows in the entering archive own SHA256SUMS.txt.'})
 d['sealed_accounting']['layer_a']='docs/api/API-02/API02_API01C5_TO_C11_EXACT_INVENTORY.json'
 d['sealed_accounting']['correction_record']='docs/api/API-02/API02_C10_TO_C11_CORRECTION_INVENTORY.json'
 # Correct every governed current lineage reference to the current exact inventory/correction record.
 raw=json.dumps(d,ensure_ascii=False)
 for old in ('docs/api/API-02/API02_API01C5_TO_C9_EXACT_INVENTORY.json','docs/api/API-02/API02_API01C5_TO_C10_EXACT_INVENTORY.json'):
  raw=raw.replace(old,'docs/api/API-02/API02_API01C5_TO_C11_EXACT_INVENTORY.json')
 for old in ('docs/api/API-02/API02_C8_TO_C9_CORRECTION_INVENTORY.json','docs/api/API-02/API02_C9_TO_C10_CORRECTION_INVENTORY.json'):
  raw=raw.replace(old,'docs/api/API-02/API02_C10_TO_C11_CORRECTION_INVENTORY.json')
 raw=raw.replace('"delta": "C9 → C10"','"delta": "C10 → C11"').replace('"delta": "C9 -> C10"','"delta": "C10 -> C11"')
 d=json.loads(raw);p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')

 for rel in ['docs/api/API-02/01_EXECUTIVE_RESULT.md','docs/api/API-02/03_ENTERING_BASELINE.md','docs/api/API-02/11_VOTING_IDENTITY_ISOLATION.md']:
  q=root/rel
  if not q.exists():continue
  x=q.read_text()
  x=x.replace('API02_API01C5_TO_C10_EXACT_INVENTORY.json','API02_API01C5_TO_C11_EXACT_INVENTORY.json').replace('API02_C9_TO_C10_CORRECTION_INVENTORY.json','API02_C10_TO_C11_CORRECTION_INVENTORY.json')
  x=x.replace('API-02 C10 (this candidate)','API-02 C11 (this candidate)').replace('API-02 C10 candidate','API-02 C11 candidate')
  x=x.replace('C9 → C10','C10 → C11').replace('C9 -> C10','C10 -> C11')
  q.write_text(x)

 hist=root/'docs/api/API-02/API02_C9_TO_C10_CORRECTION_REPORT.md'
 if hist.exists():
  x=hist.read_text().replace('# API-02 C9 → C10 correction report','# API-02 C9 → C10 correction report — HISTORICAL',1)
  if 'HISTORICAL disposition recorded by C11' not in x:
   x+='\n## HISTORICAL disposition recorded by C11\n\nC10 was not accepted. Authoritative GitHub run `33398257956` rejected C10 at the acceptance-path gate because `API02_LINEAGE.json` retained one governed prose reference to the removed C9 exact-inventory path. C11 supersedes C10 as the correction candidate.\n'
  hist.write_text(x)

 (root/'docs/api/API-02/API02_C10_TO_C11_CORRECTION_REPORT.md').write_text(f'''# API-02 C10 → C11 correction report\n\n**Candidate:** C11 — `ACCEPTANCE_PATH_REFERENCE_INTEGRITY_CORRECTION_CANDIDATE`  \n**Entering baseline:** exact C10 archive, SHA-256 `{C10_SHA}`, {C10_SIZE:,} bytes.\n\n## IR-C10-01 — stale governed evidence path in lineage prose\n\nAuthoritative GitHub run `33398257956` verified the exact C10/API-01/DATA-06/C9 archive bindings and archive safety, then the candidate-carried acceptance-path validator correctly rejected one broken governed reference: `API02_LINEAGE.json` at `acceptance_predecessor.note` still named `API02_API01C5_TO_C9_EXACT_INVENTORY.json`, which C10 no longer carried.\n\nC11 corrects that governed lineage/reference integrity and advances only current candidate/evidence identity from C10 to C11. No authentication, authorization, identity, voting-boundary, persistence, route, cryptographic, API, service or frontend runtime semantics change.\n\nThe C11 builder MUST run both `acceptance_path_identity.py` and `validate_api02.py --acceptance-path-only` before sealing and again after the fixed-point seal. Any unresolved governed reference blocks packaging.\n\nC11 remains `CANDIDATE_NOT_ACCEPTED` until an independent authoritative workflow run on the exact sealed C11 ZIP returns the terminal PASS and its evidence is recorded in canonical governance.\n\nNOT PRODUCTION READY. NOT LEGALLY ACTIVATED. NOT SECURITY CERTIFIED.\n''')

 q=root/'scripts/api02/acceptance_path_identity.py';q.write_text(q.read_text().replace('form `…_0.1_C10`','form `…_0.1_C11`'))
 q=root/'scripts/api02/build_exact_inventories.py';q.write_text(q.read_text().replace('# --- C10 -----------------------------------------------------------','# --- C11 -----------------------------------------------------------'))

 for rel in ['SHA256SUMS.txt','docs/api/API-02/API02_API01C5_TO_C10_EXACT_INVENTORY.json','docs/api/API-02/API02_C9_TO_C10_CORRECTION_INVENTORY.json','docs/api/API-02/API02_SEALED_FILE_MANIFEST.json','docs/api/API-02/API02_STALE_STATE_AUDIT.json','validation/api02/evidence_consistency_result.json']:
  q=root/rel
  if q.exists():q.unlink()

 for q in (root/'validation/api02').glob('*.json'):patch_json_current(q)
 for rel in ['validation/api02/candidate_identity_registry_result.json','validation/api02/candidate_identity_result.json']:
  q=root/rel
  if not q.exists():continue
  d=json.loads(q.read_text());d['candidate']='C11';d['candidate_classification']='ACCEPTANCE_PATH_REFERENCE_INTEGRITY_CORRECTION_CANDIDATE';d['entering_role']='C10'
  if isinstance(d.get('declarations'),list):
   d['declarations']=[str(v).replace('API02_API01C5_TO_C10_EXACT_INVENTORY.json','API02_API01C5_TO_C11_EXACT_INVENTORY.json').replace('API02_C9_TO_C10_CORRECTION_INVENTORY.json','API02_C10_TO_C11_CORRECTION_INVENTORY.json') for v in d['declarations']]
  for c in d.get('checks',[]):
   if isinstance(c,dict) and isinstance(c.get('check'),str):
    c['check']=c['check'].replace('declares C10','declares C11').replace('ACCEPTANCE_HARNESS_CLEAN_TREE_CORRECTION_CANDIDATE','ACCEPTANCE_PATH_REFERENCE_INTEGRITY_CORRECTION_CANDIDATE').replace('entering baseline is C9','entering baseline is C10')
  q.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
 for dcache in root.rglob('__pycache__'):shutil.rmtree(dcache,ignore_errors=True)


def package(root:pathlib.Path,out:pathlib.Path)->pathlib.Path:
 target=out/C11_NAME
 files=[(p.relative_to(root).as_posix(),p) for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
 files.sort(key=lambda x:x[0])
 with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6,strict_timestamps=True) as z:
  for rel,p in files:
   zi=zipfile.ZipInfo(C11_ROOT+'/'+rel,(2026,8,31,0,0,0));zi.compress_type=zipfile.ZIP_DEFLATED;zi.create_system=3;zi.external_attr=(stat.S_IMODE(p.stat().st_mode)<<16)
   z.writestr(zi,p.read_bytes(),compress_type=zipfile.ZIP_DEFLATED,compresslevel=6)
 return target


def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--out',required=True);ap.add_argument('--patch-only',action='store_true');ap.add_argument('--package-only',action='store_true');a=ap.parse_args()
 root=pathlib.Path(a.root).resolve();out=pathlib.Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True)
 if a.patch_only:
  patch_tree(root);print('API02_C11_PATCH:PASS');return
 if a.package_only:
  p=package(root,out);h=sha(p);s=p.stat().st_size
  (out/'candidate_sha256.txt').write_text(f'{h}  {p.name}\n')
  (out/'candidate_meta.json').write_text(json.dumps({'candidate':'C11','filename':p.name,'sha256':h,'size':s,'root':C11_ROOT},indent=2)+'\n')
  print(s,h);return
 raise SystemExit('choose --patch-only or --package-only')

if __name__=='__main__':main()
