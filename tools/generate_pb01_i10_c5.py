import os, json, hashlib, shutil, csv, zipfile, stat, re
from pathlib import Path

C4ZIP=Path(os.environ.get('I10_C4_ZIP','EPD2_VCRYPTO-PB01-I10_FINAL_CRYPTOGRAPHIC_PROFILE_FREEZE_AND_RELEASE_READINESS_DECISION_CANDIDATE_0.1_C4.zip')).resolve()
C4SHA='371262b0ff94c7cb51813168fcbe08cc1544e3661254855bf6b0b715d96c4fb2'
C5NAME='EPD2_VCRYPTO-PB01-I10_FINAL_CRYPTOGRAPHIC_PROFILE_FREEZE_AND_RELEASE_READINESS_DECISION_CANDIDATE_0.1_C5'
C5ZIP=Path(os.environ.get('I10_C5_ZIP',C5NAME+'.zip')).resolve()
WORK=Path(os.environ.get('I10_C5_WORK','/tmp/i10c5_build')).resolve()
if WORK.exists(): shutil.rmtree(WORK)
WORK.mkdir()

def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()
assert sha(C4ZIP)==C4SHA
with zipfile.ZipFile(C4ZIP) as z: z.extractall(WORK/'c4')
c4roots=[p for p in (WORK/'c4').iterdir() if p.is_dir()]; assert len(c4roots)==1
c4root=c4roots[0]; c5root=WORK/C5NAME; shutil.copytree(c4root,c5root)

def files_map(root): return {str(p.relative_to(root)).replace(os.sep,'/'):sha(p) for p in root.rglob('*') if p.is_file()}
before=files_map(c4root)

exec_paths=['evidence/build/belenios-tool-3.3.0-linux-x86_64','guardian-side/partial_decrypt.sh','guardian-side/reference_threshold_ceremony.sh','scripts/i09_generate_ballots_native.sh','scripts/run_i05_postgres_validation.sh','scripts/run_i06_postgres_validation.sh','scripts/run_i07_postgres_validation.sh','scripts/run_i09_c1_concurrency.sh','scripts/run_i09_postgres_class.sh','verifier/rust/bin/epd2-i08-verifier-c','verifier/rust/vendor/curve25519-dalek/tests/build_tests.sh','verifier/rust/vendor/libc/etc/libc-util.py']
for rel in exec_paths:
    assert (c5root/rel).is_file(), rel
    os.chmod(c5root/rel,0o755)
exec_paths=sorted(exec_paths)

p=c5root/'scripts/i10_validate_current_run.mjs'
s=p.read_text()
s=s.replace("import {resolve,join} from 'node:path';import {mkdtemp,copyFile,rm} from 'node:fs/promises';", "import {resolve,join} from 'node:path';import {mkdtemp,copyFile,rm,access} from 'node:fs/promises';import {constants as fsConstants} from 'node:fs';")
needle="const temp=await mkdtemp(join(tmpdir(),'epd2-i10-cleanroom-'));try{run('unzip',['-q',zipPath,'-d',temp],{label:'zip:extract',timeoutMs:I10_TIMEOUTS.quick});const work=join(temp,roots[0]);run('sha256sum',['-c','SHA256SUMS.txt'],{cwd:work,label:'preinstall:sha256sums',timeoutMs:I10_TIMEOUTS.quick});"
check="const temp=await mkdtemp(join(tmpdir(),'epd2-i10-cleanroom-'));try{run('unzip',['-q',zipPath,'-d',temp],{label:'zip:extract',timeoutMs:I10_TIMEOUTS.quick});const work=join(temp,roots[0]);for(const rel of "+json.dumps(exec_paths,separators=(',',':'))+"){try{await access(join(work,rel),fsConstants.X_OK);}catch{throw new Error(`ZIP_EXECUTABLE_MODE_REQUIRED:${rel}`);}}run('sha256sum',['-c','SHA256SUMS.txt'],{cwd:work,label:'preinstall:sha256sums',timeoutMs:I10_TIMEOUTS.quick});"
assert needle in s
p.write_text(s.replace(needle,check))

wp=c5root/'scripts/i10_validate_worker.mjs'; w=wp.read_text(); assert 'CANDIDATE_0.1_C4.zip' in w; wp.write_text(w.replace('CANDIDATE_0.1_C4.zip','CANDIDATE_0.1_C5.zip'))

tp=c5root/'tests/i10-freeze-release.test.mjs'; t=tp.read_text()
if "constants as fsConstants" not in t:
    t="import {constants as fsConstants} from 'node:fs';import {access} from 'node:fs/promises';"+t
reg="\ntest('sealed candidate preserves governed executable file modes',async()=>{for(const rel of "+json.dumps(exec_paths,separators=(',',':'))+"){await assert.doesNotReject(()=>access(rel,fsConstants.X_OK),`executable mode missing: ${rel}`);}});\n"
t += reg
tp.write_text(t)

report=f'''# EPD² PB01-I10 C5 Packaging Mode Preservation Corrective Report\n\n## Candidate\n\n- Target: `{C5NAME}.zip`\n- Exact corrective predecessor: `EPD2_VCRYPTO-PB01-I10_FINAL_CRYPTOGRAPHIC_PROFILE_FREEZE_AND_RELEASE_READINESS_DECISION_CANDIDATE_0.1_C4.zip`\n- Predecessor SHA-256: `{C4SHA}`\n- Accepted semantic predecessor remains I09 C4 SHA-256 `10e1f158a1ee621be45bf80b0f9dea21585a64ae728268affbbe41dbbc4e760a`.\n- System status remains `NON_BINDING_PILOT`.\n\n## Triggering external evidence\n\nExact C4 run `32373499122` reconstructed the sealed C4 SHA exactly and then failed `regression:i03-core`: valid ballots returned HTTP 422 and the class reached its fail-closed timeout. Independent artifact analysis established that the native Belenios verifier executable bytes were unchanged but its POSIX execute mode had been lost by the deterministic ZIP repack (`0755` in exact C1 -> `0644` in C2/C3/C4). The I03 boundary correctly mapped inability to execute the native verifier to `INVALID_ENCRYPTED_BALLOT` / HTTP 422.\n\nA diagnostic run on the exact C4 tree with **only the inherited executable bits restored** produced `npm test` **34/34 PASS** with no source/test semantic change. This proves the C4 failures were packaging-mode defects, not ballot/API/ledger/security defects.\n\n## C5 correction\n\nC5 restores execute permission `0755` for every inherited file that was executable in the exact original C1 package. File content bytes are unchanged for those paths. A new fail-closed clean-extraction gate requires all governed executable paths to satisfy `X_OK` before SHA, dependency installation, or regression execution. `test:i10` independently asserts the same invariant.\n\nNo crypto profile, ballot format, credential, revote, final-set, tally, guardian, decryption, verifier source, database schema, or application runtime semantic is changed.\n\n## Release authority\n\nC5 remains pending until a fresh untouched exact-ZIP run in Node 24.19.0 / Go 1.23.2 / Rust+Cargo 1.97.1 / PostgreSQL 16 returns nonce-bound `PASS` / `RELEASE_READY`.\n'''
(c5root/'EPD2_PB01_I10_DEVELOPER_REPORT.md').write_text(report)

fv=c5root/'I10_FINAL_VALIDATION.json'; j=json.load(open(fv)); j['candidate_filename']=C5NAME+'.zip'; j['candidate_sha256']=None; j['current_run_nonce']=None; j['verification_result_digest']=None; j['status']='PENDING_INDEPENDENT_EXACT_ZIP_VALIDATION'; j['live_execution']=False; j['release_readiness_decision']='NOT_RELEASE_READY'; j['authority_note']='Documentary C5 assembly record only. Exact ZIP execution must preserve governed POSIX executable modes and create a fresh nonce-bound result.'; fv.write_text(json.dumps(j,indent=2)+'\n')

lp=c5root/'PB01_ACCEPTED_LINEAGE.json'; l=json.load(open(lp)); i10=next(x for x in l['stages'] if x['stage_id']=='I10'); i10['accepted_candidate_filename']=C5NAME+'.zip'; i10['acceptance_status']='CANDIDATE — C5 packaging-mode corrective pending independent exact-ZIP acceptance'; lp.write_text(json.dumps(l,indent=2)+'\n')

pp=c5root/'PB01_RELEASE_PROVENANCE.json'; pr=json.load(open(pp)); pr['candidate_filename']=C5NAME+'.zip'; pr['c5_packaging_mode_corrective']={'predecessor_candidate':'EPD2_VCRYPTO-PB01-I10_FINAL_CRYPTOGRAPHIC_PROFILE_FREEZE_AND_RELEASE_READINESS_DECISION_CANDIDATE_0.1_C4.zip','predecessor_sha256':C4SHA,'triggering_external_run':32373499122,'classification':'ZIP_PACKAGING_MODE_PRESERVATION_DEFECT','diagnostic':'exact C4 bytes + executable bits only => npm test 34/34 PASS','governed_executable_paths':exec_paths,'semantic_drift':False}; pp.write_text(json.dumps(pr,indent=2)+'\n')

ev={'schema_version':'epd2.pb01.i10-c5-executable-mode-preservation/1','candidate':C5NAME+'.zip','predecessor_candidate':'EPD2_VCRYPTO-PB01-I10_FINAL_CRYPTOGRAPHIC_PROFILE_FREEZE_AND_RELEASE_READINESS_DECISION_CANDIDATE_0.1_C4.zip','predecessor_sha256':C4SHA,'triggering_external_run':32373499122,'classification':'ZIP_PACKAGING_MODE_PRESERVATION_DEFECT','root_cause':'deterministic re-pack preserved file bytes but normalized inherited executable files from 0755 to 0644','diagnostic_result':'restoring inherited executable bits only on exact C4 tree makes npm test PASS 34/34','governed_executable_paths':[{'path':x,'required_mode':'0755','content_sha256':sha(c5root/x)} for x in exec_paths],'semantic_drift':False,'system_status':'NON_BINDING_PILOT','historical_provenance_exception_count':1,'historical_provenance_exception_stage':'I05'}
evpath=c5root/'evidence/i10/I10_C5_EXECUTABLE_MODE_PRESERVATION.json'; evpath.write_text(json.dumps(ev,indent=2)+'\n')

after_pre=files_map(c5root)
new=set(after_pre)-set(before); mod={x for x in set(after_pre)&set(before) if after_pre[x]!=before[x]}; deleted=set(before)-set(after_pre); assert not deleted
inv_json='PB01_I10_C5_CHANGED_FILE_INVENTORY.json'; inv_csv='PB01_I10_C5_CHANGED_FILE_INVENTORY.csv'; new.update({inv_json,inv_csv}); mod.update({'PB01_RELEASE_ARTIFACT_MANIFEST.json','SHA256SUMS.txt'})
changes=[]
for path in sorted(new|mod):
    ct='ADDED' if path in new and path not in before else 'MODIFIED'; recursive=path in {inv_json,inv_csv,'PB01_RELEASE_ARTIFACT_MANIFEST.json','SHA256SUMS.txt'}
    changes.append({'path':path,'change_type':ct,'sha256_before':before.get(path),'sha256_after':None if recursive else after_pre.get(path),'reason':'recursive packaging metadata' if recursive else 'PB01-I10 C5 packaging-mode corrective','security_relevance':path.startswith(('scripts/','tests/','evidence/')) or path.endswith('.json')})
mode_changes=[{'path':x,'mode_before':'0644','mode_after':'0755','content_sha256_unchanged':sha(c5root/x)} for x in exec_paths]
counts={'added':sum(x['change_type']=='ADDED' for x in changes),'modified':sum(x['change_type']=='MODIFIED' for x in changes),'deleted':0,'archive_mode_modified':len(mode_changes)}
inv={'schema_version':'epd2.pb01.i10-c5-changed-file-inventory/1','predecessor_candidate':'EPD2_VCRYPTO-PB01-I10_FINAL_CRYPTOGRAPHIC_PROFILE_FREEZE_AND_RELEASE_READINESS_DECISION_CANDIDATE_0.1_C4.zip','predecessor_sha256':C4SHA,'counts':counts,'changes':changes,'archive_mode_changes':mode_changes,'semantic_scope':'ZIP mode preservation + validation harness assertion + current-candidate governance metadata only; no crypto/runtime/profile drift'}
(c5root/inv_json).write_text(json.dumps(inv,indent=2)+'\n')
with open(c5root/inv_csv,'w',newline='') as f:
    fields=['path','change_type','sha256_before','sha256_after','reason','security_relevance']; wr=csv.DictWriter(f,fieldnames=fields); wr.writeheader(); wr.writerows(changes)

rmp=c5root/'PB01_RELEASE_ARTIFACT_MANIFEST.json'; rmj=json.load(open(rmp)); arts={a['path']:a for a in rmj['artifacts']}
covered=[str(x.relative_to(c5root)).replace(os.sep,'/') for x in c5root.rglob('*') if x.is_file() and str(x.relative_to(c5root)).replace(os.sep,'/') not in {'PB01_RELEASE_ARTIFACT_MANIFEST.json','SHA256SUMS.txt'}]
for path in covered:
    h=sha(c5root/path)
    if path in arts: arts[path]['sha256']=h
    else: arts[path]={'path':path,'artifact_class':'validation-script' if path.startswith('scripts/') else ('test' if path.startswith('tests/') else 'release-metadata-or-documentation'),'sha256':h,'source_or_generated':'source','producer':'PB01 cumulative candidate / I10 C5 corrective assembler','profile':'epd2.belenios-homomorphic/1','version':'PB01-I10-C5','required':True,'security_relevance':True,'verification_relevance':True}
arts={k:v for k,v in arts.items() if k in covered}; rmj['artifacts']=[arts[k] for k in sorted(arts)]; rmj['artifact_count']=len(rmj['artifacts']); rmj['c5_packaging_mode_corrective']={'predecessor_sha256':C4SHA,'governed_executable_count':len(exec_paths),'semantic_drift':False}; rmp.write_text(json.dumps(rmj,indent=2)+'\n')

allfiles=sorted(str(x.relative_to(c5root)).replace(os.sep,'/') for x in c5root.rglob('*') if x.is_file() and x.name!='SHA256SUMS.txt')
with open(c5root/'SHA256SUMS.txt','w') as f:
    for path in allfiles: f.write(f"{sha(c5root/path)}  ./{path}\n")

if C5ZIP.exists(): C5ZIP.unlink()
with zipfile.ZipFile(C5ZIP,'w',compression=zipfile.ZIP_STORED) as z:
    for pth in sorted(c5root.rglob('*')):
        if not pth.is_file(): continue
        rel=C5NAME+'/'+str(pth.relative_to(c5root)).replace(os.sep,'/')
        zi=zipfile.ZipInfo(rel,date_time=(1980,1,1,0,0,0)); zi.compress_type=zipfile.ZIP_STORED; zi.create_system=3
        mode=0o755 if str(pth.relative_to(c5root)).replace(os.sep,'/') in exec_paths else 0o644
        zi.external_attr=((stat.S_IFREG|mode)<<16)
        with open(pth,'rb') as f: z.writestr(zi,f.read())
print(json.dumps({'candidate':str(C5ZIP),'sha256':sha(C5ZIP),'file_count':len(allfiles)+1,'byte_counts':counts,'governed_executables':len(exec_paths)},indent=2))
