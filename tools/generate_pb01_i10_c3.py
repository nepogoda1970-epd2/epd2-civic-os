import os, json, hashlib, shutil, csv, re, zipfile
from pathlib import Path

C2ZIP=Path(os.environ.get('I10_C2_ZIP','EPD2_VCRYPTO-PB01-I10_FINAL_CRYPTOGRAPHIC_PROFILE_FREEZE_AND_RELEASE_READINESS_DECISION_CANDIDATE_0.1_C2.zip')).resolve()
C2SHA='edbb427cb8b7651ac1c351d9f3f8b8de46945152dcea82637a45d540cbbc49c6'
C3NAME='EPD2_VCRYPTO-PB01-I10_FINAL_CRYPTOGRAPHIC_PROFILE_FREEZE_AND_RELEASE_READINESS_DECISION_CANDIDATE_0.1_C3'
C3ZIP=Path(os.environ.get('I10_C3_ZIP',C3NAME+'.zip')).resolve()
WORK=Path(os.environ.get('I10_C3_WORK','/tmp/i10c3build')).resolve()
if WORK.exists(): shutil.rmtree(WORK)
WORK.mkdir()
with zipfile.ZipFile(C2ZIP) as z: z.extractall(WORK/'c2')
c2roots=[p for p in (WORK/'c2').iterdir() if p.is_dir()]
assert len(c2roots)==1
c2root=c2roots[0]
c3root=WORK/C3NAME
shutil.copytree(c2root,c3root)

def sha(p:Path):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
def files_map(root):
    return {str(p.relative_to(root)).replace(os.sep,'/'):sha(p) for p in root.rglob('*') if p.is_file()}
before=files_map(c2root)

cur=(c3root/'scripts/i10_validate_current_run.mjs').read_text()
needle="r=spawnSync(process.execPath,['scripts/i10_check_predecessor.mjs'],{cwd:work,stdio:'inherit',env:process.env});req(r.status===0,'I10_PREDECESSOR_PREINSTALL_FAILED');\nr=spawnSync('npm',['ci','--offline','--ignore-scripts'],{cwd:work,stdio:'inherit',env:process.env});req(r.status===0,'NPM_CI_OFFLINE_FAILED');"
repl="r=spawnSync(process.execPath,['scripts/i10_check_predecessor.mjs'],{cwd:work,stdio:'inherit',env:process.env});req(r.status===0,'I10_PREDECESSOR_PREINSTALL_FAILED');\nr=spawnSync(process.execPath,['scripts/i10_static_release_checks.mjs'],{cwd:work,stdio:'inherit',env:process.env});req(r.status===0,'I10_STATIC_RELEASE_PREINSTALL_FAILED');\nr=spawnSync('npm',['ci','--offline','--ignore-scripts'],{cwd:work,stdio:'inherit',env:process.env});req(r.status===0,'NPM_CI_OFFLINE_FAILED');"
assert needle in cur
(c3root/'scripts/i10_validate_current_run.mjs').write_text(cur.replace(needle,repl))

worker=(c3root/'scripts/i10_validate_worker.mjs').read_text()
old="run(process.execPath,['scripts/i10_check_freeze.mjs']);run(process.execPath,['scripts/i10_static_release_checks.mjs']);run('npm',['run','test:i10']);"
new="run(process.execPath,['scripts/i10_check_freeze.mjs']);run('npm',['run','test:i10']);"
assert old in worker
worker=worker.replace(old,new).replace('CANDIDATE_0.1_C2.zip','CANDIDATE_0.1_C3.zip')
(c3root/'scripts/i10_validate_worker.mjs').write_text(worker)

tp=c3root/'tests/i10-freeze-release.test.mjs'
t=tp.read_text()
oldtest="test('I10 predecessor scope check runs before dependency installation and is not repeated after node_modules exists',async()=>{const c=await readFile('scripts/i10_validate_current_run.mjs','utf8');const w=await readFile('scripts/i10_validate_worker.mjs','utf8');const pre=c.indexOf(\"scripts/i10_check_predecessor.mjs\");const install=c.indexOf(\"['ci','--offline','--ignore-scripts']\");assert.ok(pre>=0,'predecessor preinstall check missing');assert.ok(install>pre,'predecessor check must precede npm ci');assert.equal(w.includes(\"scripts/i10_check_predecessor.mjs\"),false,'worker must not re-scan transient node_modules as candidate delta');});"
newtest="test('I10 archive scope and static hygiene checks run before dependency installation and are not repeated after node_modules exists',async()=>{const c=await readFile('scripts/i10_validate_current_run.mjs','utf8');const w=await readFile('scripts/i10_validate_worker.mjs','utf8');const pre=c.indexOf(\"scripts/i10_check_predecessor.mjs\");const hygiene=c.indexOf(\"scripts/i10_static_release_checks.mjs\");const install=c.indexOf(\"['ci','--offline','--ignore-scripts']\");assert.ok(pre>=0,'predecessor preinstall check missing');assert.ok(hygiene>pre,'static release check must follow predecessor check on clean extraction');assert.ok(install>hygiene,'both archive checks must precede npm ci');assert.equal(w.includes(\"scripts/i10_check_predecessor.mjs\"),false,'worker must not re-scan transient node_modules as candidate delta');assert.equal(w.includes(\"scripts/i10_static_release_checks.mjs\"),false,'worker must not re-run archive hygiene after transient dependency installation');});"
assert oldtest in t
t=t.replace(oldtest,newtest).replace('full governed lineage validator passes current C1 metadata','full governed lineage validator passes current I10 metadata')
tp.write_text(t)

report=f'''# EPD² PB01-I10 C3 Validation Harness Corrective Report

## Candidate

- Target: `{C3NAME}.zip`
- Exact predecessor: `EPD2_VCRYPTO-PB01-I10_FINAL_CRYPTOGRAPHIC_PROFILE_FREEZE_AND_RELEASE_READINESS_DECISION_CANDIDATE_0.1_C2.zip`
- Predecessor SHA-256: `{C2SHA}`
- Corrective scope: validation harness ordering and governed candidate metadata only.
- System status remains `NON_BINDING_PILOT`.

## Triggering defect

External exact-ZIP run `32366109392` reached the C2 candidate's own `validate:i10` and confirmed freeze/lineage PASS, then failed with:

`HYGIENE:node_modules/.bin/playwright`

This is a validation-harness defect, not cryptographic/runtime/profile drift. C2 correctly moved the strict predecessor/scope check before `npm ci`, but `scripts/i10_validate_worker.mjs` still invoked `scripts/i10_static_release_checks.mjs` after `npm ci --offline --ignore-scripts` created transient `node_modules`. The unchanged strict hygiene checker then correctly rejected that generated workspace state.

## C3 correction

C3 does **not** weaken `scripts/i10_static_release_checks.mjs`. Instead it preserves the strict check unchanged and corrects ordering:

1. exact ZIP listing/path hygiene;
2. clean extraction;
3. `SHA256SUMS.txt` verification;
4. strict predecessor/scope check on the clean extracted tree;
5. strict static release/hygiene check on the same clean extracted tree;
6. only then `npm ci --offline --ignore-scripts`;
7. live worker, freeze, tests and mandatory regressions;
8. no archive-hygiene re-scan after transient `node_modules` exists.

A regression test fails closed if either archive check is moved after dependency installation or is reintroduced into the post-install worker.

## Frozen semantics

No changes are made to `src/`, `server/`, `client/`, `schemas/`, `migrations/`, cryptographic profile, ballot/revote/final-set/tally/guardian/decryption semantics, Rust verifier source, Cargo.lock, Go verifier semantics, PostgreSQL schema, or dependency lock material. Accepted I09 C4 remains the frozen semantic baseline.

The single governed I05 historical provenance exception remains unchanged and explicit; no I05 archive SHA is fabricated.

## Release authority

C3 does **not** self-declare `RELEASE_READY`. Packaged validation evidence remains non-authoritative/pending. Only a fresh untouched exact sealed C3 run in Node 24.19.0 / Go 1.23.2 / Rust+Cargo 1.97.1 / PostgreSQL 16 may produce the nonce-bound PASS and establish I10 Outcome A.
'''
(c3root/'EPD2_PB01_I10_DEVELOPER_REPORT.md').write_text(report)

fv=c3root/'I10_FINAL_VALIDATION.json'; j=json.load(open(fv)); j['candidate_filename']=C3NAME+'.zip'; j['authority_note']='Documentary C3 assembly record only. C3 preserves strict archive hygiene and executes predecessor/static release checks on the clean extracted candidate before transient dependency installation. No crypto/runtime/profile semantics change. validate:i10 clean-room execution must create a fresh nonce-bound record before RELEASE_READY.'; j['status']='PENDING_INDEPENDENT_EXACT_ZIP_VALIDATION'; j['release_readiness_decision']='NOT_RELEASE_READY'; j['live_execution']=False; j['candidate_sha256']=None; j['current_run_nonce']=None; j['verification_result_digest']=None
fv.write_text(json.dumps(j,indent=2)+'\n')

lp=c3root/'PB01_ACCEPTED_LINEAGE.json'; l=json.load(open(lp)); i10=next(x for x in l['stages'] if x['stage_id']=='I10'); i10['accepted_candidate_filename']=C3NAME+'.zip'; i10['acceptance_status']='CANDIDATE — C3 harness corrective pending independent exact-ZIP acceptance'; lp.write_text(json.dumps(l,indent=2)+'\n')

pp=c3root/'PB01_RELEASE_PROVENANCE.json'; p=json.load(open(pp)); p['candidate_filename']=C3NAME+'.zip'; p['c3_validation_harness_corrective']={'predecessor_candidate':'EPD2_VCRYPTO-PB01-I10_FINAL_CRYPTOGRAPHIC_PROFILE_FREEZE_AND_RELEASE_READINESS_DECISION_CANDIDATE_0.1_C2.zip','predecessor_sha256':C2SHA,'scope':'validation harness ordering only; no crypto/runtime/schema/migration/dependency semantic change','defect':'C2 moved predecessor check preinstall but still ran strict static archive hygiene after npm ci generated transient node_modules','correction':'run both strict predecessor and static release/hygiene checks on clean extraction before npm ci; do not weaken either checker'}; pp.write_text(json.dumps(p,indent=2)+'\n')

ev={'schema_version':'epd2.pb01.i10-c3-harness-correction-validation/1','candidate':C3NAME+'.zip','predecessor_candidate':'EPD2_VCRYPTO-PB01-I10_FINAL_CRYPTOGRAPHIC_PROFILE_FREEZE_AND_RELEASE_READINESS_DECISION_CANDIDATE_0.1_C2.zip','predecessor_sha256':C2SHA,'triggering_external_run':32366109392,'triggering_failure':'HYGIENE:node_modules/.bin/playwright','classification':'VALIDATION_HARNESS_DEFECT','correction':'strict predecessor and static release/hygiene checks execute on clean extracted tree before npm ci; post-install worker does not re-run archive-scope/hygiene checks','strict_static_checker_modified':False,'semantic_scope':'validation harness ordering only; no crypto/runtime/profile drift','system_status':'NON_BINDING_PILOT','historical_provenance_exception_count':1,'historical_provenance_exception_stage':'I05','corrected_sources':{}}
evpath=c3root/'evidence/i10/I10_C3_HARNESS_CORRECTION_VALIDATION.json'; evpath.parent.mkdir(parents=True,exist_ok=True); evpath.write_text(json.dumps(ev,indent=2)+'\n')
ev['corrected_sources']={'scripts/i10_validate_current_run.mjs':sha(c3root/'scripts/i10_validate_current_run.mjs'),'scripts/i10_validate_worker.mjs':sha(c3root/'scripts/i10_validate_worker.mjs'),'scripts/i10_static_release_checks.mjs':sha(c3root/'scripts/i10_static_release_checks.mjs'),'tests/i10-freeze-release.test.mjs':sha(c3root/'tests/i10-freeze-release.test.mjs')}; evpath.write_text(json.dumps(ev,indent=2)+'\n')

after_pre=files_map(c3root)
new_paths=set(after_pre)-set(before); mod_paths={x for x in set(after_pre)&set(before) if after_pre[x]!=before[x]}
inv_json='PB01_I10_C3_CHANGED_FILE_INVENTORY.json'; inv_csv='PB01_I10_C3_CHANGED_FILE_INVENTORY.csv'; new_paths.update({inv_json,inv_csv}); mod_paths.update({'PB01_RELEASE_ARTIFACT_MANIFEST.json','SHA256SUMS.txt'})
changes=[]
for path in sorted(new_paths|mod_paths):
    ct='ADDED' if path in new_paths and path not in before else 'MODIFIED'; recursive=path in {inv_json,inv_csv,'PB01_RELEASE_ARTIFACT_MANIFEST.json','SHA256SUMS.txt'}; sec=path.endswith('.json') or path.startswith('scripts/') or path.startswith('tests/') or path.startswith('evidence/'); reason=('recursive packaging metadata; exact final hash bound by release manifest/SHA256SUMS' if recursive else 'PB01-I10 C3 validation-harness corrective'); changes.append({'path':path,'change_type':ct,'sha256_before':before.get(path),'sha256_after':None if recursive else after_pre.get(path),'reason':reason,'security_relevance':bool(sec)})
counts={'added':sum(x['change_type']=='ADDED' for x in changes),'modified':sum(x['change_type']=='MODIFIED' for x in changes),'deleted':0}
inv={'schema_version':'epd2.pb01.i10-c3-changed-file-inventory/1','predecessor_candidate':'EPD2_VCRYPTO-PB01-I10_FINAL_CRYPTOGRAPHIC_PROFILE_FREEZE_AND_RELEASE_READINESS_DECISION_CANDIDATE_0.1_C2.zip','predecessor_sha256':C2SHA,'counts':counts,'changes':changes,'semantic_scope':'validation harness ordering + current-candidate governance metadata only; no crypto/runtime/profile drift'}
(c3root/inv_json).write_text(json.dumps(inv,indent=2)+'\n')
with open(c3root/inv_csv,'w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['path','change_type','sha256_before','sha256_after','reason','security_relevance']); w.writeheader(); w.writerows(changes)

rmp=c3root/'PB01_RELEASE_ARTIFACT_MANIFEST.json'; rmj=json.load(open(rmp)); arts={a['path']:a for a in rmj['artifacts']}; covered=[str(x.relative_to(c3root)).replace(os.sep,'/') for x in c3root.rglob('*') if x.is_file() and str(x.relative_to(c3root)).replace(os.sep,'/') not in {'PB01_RELEASE_ARTIFACT_MANIFEST.json','SHA256SUMS.txt'}]
for path in covered:
    h=sha(c3root/path)
    if path in arts: arts[path]['sha256']=h
    else: arts[path]={'path':path,'artifact_class':'release-metadata-or-documentation' if not (path.startswith('scripts/') or path.startswith('tests/')) else ('validation-script' if path.startswith('scripts/') else 'test'),'sha256':h,'source_or_generated':'source','producer':'PB01 cumulative candidate / I10 C3 corrective assembler','profile':'epd2.belenios-homomorphic/1','version':'PB01-I10-C3','required':True,'security_relevance':True,'verification_relevance':True}
arts={k:v for k,v in arts.items() if k in covered}; rmj['artifacts']=[arts[k] for k in sorted(arts)]; rmj['artifact_count']=len(rmj['artifacts']); rmj['c3_validation_harness_corrective']={'predecessor_candidate':'EPD2_VCRYPTO-PB01-I10_FINAL_CRYPTOGRAPHIC_PROFILE_FREEZE_AND_RELEASE_READINESS_DECISION_CANDIDATE_0.1_C2.zip','predecessor_sha256':C2SHA,'external_failure_run':32366109392,'failure':'HYGIENE:node_modules/.bin/playwright','correction':'strict archive checks run preinstall; worker does not repeat them postinstall','semantic_drift':False}; rmp.write_text(json.dumps(rmj,indent=2)+'\n')

allfiles=sorted(str(x.relative_to(c3root)).replace(os.sep,'/') for x in c3root.rglob('*') if x.is_file() and x.name!='SHA256SUMS.txt')
with open(c3root/'SHA256SUMS.txt','w') as f:
    for path in allfiles: f.write(f"{sha(c3root/path)}  ./{path}\n")
after=files_map(c3root); added=sorted(set(after)-set(before)); modified=sorted(x for x in set(after)&set(before) if after[x]!=before[x]); deleted=sorted(set(before)-set(after)); assert not deleted; assert sorted(x['path'] for x in changes)==sorted(added+modified); assert counts=={'added':len(added),'modified':len(modified),'deleted':0}

if C3ZIP.exists(): C3ZIP.unlink()
with zipfile.ZipFile(C3ZIP,'w',compression=zipfile.ZIP_STORED) as z:
    for p in sorted(c3root.rglob('*')):
        if not p.is_file(): continue
        rel=C3NAME+'/'+str(p.relative_to(c3root)).replace(os.sep,'/'); zi=zipfile.ZipInfo(rel,date_time=(1980,1,1,0,0,0)); zi.compress_type=zipfile.ZIP_STORED; zi.create_system=3; zi.external_attr=(0o100644 << 16); zi.flag_bits=0; z.writestr(zi,p.read_bytes())
print('ZIP',C3ZIP); print('SHA256',sha(C3ZIP)); print('COUNTS',counts); print('FILES',len(after)); print('ADDED',*added,sep='\n'); print('MODIFIED',*modified,sep='\n')
