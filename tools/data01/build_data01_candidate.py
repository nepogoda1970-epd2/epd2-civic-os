#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, os, shutil, tarfile, zipfile
from pathlib import Path

C3_NAME='EPD2_PILOT03_ASSEMBLIES_MOTIONS_AND_COMMUNICATIONS_CANDIDATE_0.1_C3.zip'
C3_SHA='52b5bbfe312d90d65f500f0b6085d33ffe3235ce4bd90562110a26a8fae208d1'
C6_NAME='EPD2_VCRYPTO-PB01-I10_FINAL_CRYPTOGRAPHIC_PROFILE_FREEZE_AND_RELEASE_READINESS_DECISION_CANDIDATE_0.1_C6.zip'
C6_SHA='442b83d9639a7398b3da767beb95976d379190229610d9b5ccb550d53d277d25'
TARGET_ROOT='EPD2_DATA-01_CANONICAL_DATA_OWNERSHIP_PERSISTENCE_BOUNDARIES_AND_AUDIT_EVIDENCE_FOUNDATION_CANDIDATE_0.1'
TARGET_ZIP=TARGET_ROOT+'.zip'
PB01_FILES=('PB01_ACCEPTED_LINEAGE.json','PB01_PROFILE_FREEZE_MANIFEST.json','PB01_RELEASE_ARTIFACT_MANIFEST.json','PB01_RELEASE_PROVENANCE.json')
FIXED_TS=1787184000

def sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for c in iter(lambda:f.read(1024*1024),b''): h.update(c)
    return h.hexdigest()

def one_root(parent:Path)->Path:
    roots=[p for p in parent.iterdir() if p.is_dir()]; files=[p for p in parent.iterdir() if p.is_file()]
    if len(roots)!=1 or files: raise SystemExit(f'exactly one root required in {parent}: roots={roots} files={files}')
    return roots[0]

def safe_extract_zip(z:Path,d:Path):
    with zipfile.ZipFile(z) as f:
        for i in f.infolist():
            pp=Path(i.filename)
            if pp.is_absolute() or '..' in pp.parts: raise SystemExit(f'unsafe zip path {i.filename}')
            if ((i.external_attr>>16)&0o170000)==0o120000: raise SystemExit(f'symlink forbidden {i.filename}')
        f.extractall(d)

def safe_extract_tar(t:Path,d:Path):
    with tarfile.open(t,'r:gz') as f:
        for m in f.getmembers():
            pp=Path(m.name)
            if pp.is_absolute() or '..' in pp.parts or m.issym() or m.islnk(): raise SystemExit(f'unsafe patch path {m.name}')
        f.extractall(d,filter='data')

def fmap(r:Path, exclude:set[str]=set()):
    return {p.relative_to(r).as_posix():sha(p) for p in r.rglob('*') if p.is_file() and p.relative_to(r).as_posix() not in exclude and '__pycache__/' not in p.relative_to(r).as_posix() and not p.name.endswith('.pyc')}

def write_generated(root:Path, base:Path):
    protected={}
    for p in sorted((x for x in base.rglob('*') if x.is_file()), key=lambda x:x.relative_to(base).as_posix()):
        rel=p.relative_to(base).as_posix()
        if rel in {'package.json','SHA256SUMS.txt'}: continue
        protected[rel]=sha(p)
    pm={'schema':'epd2.data01.predecessor-protection/1','predecessor_filename':C3_NAME,'predecessor_sha256':C3_SHA,'declared_modified_predecessor_files':['package.json','SHA256SUMS.txt'],'declared_modified_predecessor_sha256':{n:sha(base/n) for n in ('package.json','SHA256SUMS.txt')},'protected_files':protected}
    (root/'data').mkdir(exist_ok=True); (root/'data/predecessor-protected-sha256.json').write_text(json.dumps(pm,indent=2,sort_keys=True)+'\n')
    val={'schema':'epd2.data01.final-validation/1','status':'PENDING_LIVE_VALIDATION','candidate_filename':TARGET_ZIP,'candidate_sha256':None,'predecessor_filename':C3_NAME,'predecessor_sha256':C3_SHA,'pb01_frozen_baseline_filename':C6_NAME,'pb01_frozen_baseline_sha256':C6_SHA,'live_execution':False,'failure_or_pending_reason':'sealed candidate requires independent exact-ZIP PostgreSQL 16 validation','non_binding_pilot':True,'pilot04_predecessor':False}
    (root/'DATA01_FINAL_VALIDATION.json').write_text(json.dumps(val,indent=2,sort_keys=True)+'\n')
    report=f'''# EPD² DATA-01 Developer Validation Report\n\n## A. Candidate\n\n- Candidate: `{TARGET_ZIP}`\n- Candidate SHA-256: `EXTERNAL_AFTER_SEALING`\n- Application predecessor: `{C3_NAME}`\n- Application predecessor SHA-256: `{C3_SHA}`\n- Frozen PB01 baseline: `{C6_NAME}`\n- Frozen PB01 SHA-256: `{C6_SHA}`\n\n## B. Exact diff\n\nThe exact machine-readable predecessor delta is `DATA01_CHANGED_FILE_INVENTORY.json`. No predecessor deletion is permitted. Accepted PILOT-03 files are byte-protected except the explicitly declared `package.json` command addition and regenerated `SHA256SUMS.txt`.\n\n## C. Architecture\n\nCanonical bounded contexts are physically separated into PostgreSQL schemas `identity`, `governance`, `assembly`, `voting_boundary`, `verification`, `audit`, and `operations`, plus migration-only `data01_meta`. Runtime authority is split across dedicated service roles. `voting_boundary` is placeholder-only and contains no identity/credential/ballot linkage.\n\n## D. Migrations\n\nTwo transactional DATA-01 migrations are registered with immutable IDs and SHA-256 checksums. The validator exercises fresh bootstrap, idempotent re-application, predecessor-state preservation, migration tamper rejection and schema/privilege drift detection.\n\n## E. Tests\n\n`npm run validate:data01` is the fail-closed acceptance orchestrator. It requires the exact candidate ZIP binding, Node 24.19.0, PostgreSQL 16, DATA-01 static/code-quality tests, real database authority/adversarial tests, accepted PILOT-03 targeted/full regression and the 8-test browser regression. Unknown or skipped acceptance gates cannot authorize PASS.\n\nRequired adversarial coverage includes DATA01-NEG-01 through DATA01-NEG-10, voting-to-identity denial, audit-reader mutation denial, unknown verifier denial, migration-owner runtime denial, undeclared grant drift and dangerous cross-domain view detection.\n\n## F. Regression\n\nAccepted PILOT-03 C3 is the cumulative application predecessor and is protected by `data/predecessor-protected-sha256.json`. Frozen PB01 C6 governance manifests are copied only as read-only integrity bindings under `data/baselines/pb01/`; no PB01 crypto source/vector/runtime code is introduced or modified. PILOT-04 is not a predecessor.\n\n## G. Current-run evidence\n\nThe sealed candidate intentionally contains `DATA01_FINAL_VALIDATION.json` in `PENDING_LIVE_VALIDATION` state. A full exact-ZIP run overwrites this in the extracted validation workspace and writes `evidence/data01/current-run.json` with nonce, candidate SHA, PostgreSQL version, schema/migration/authority digests, test counts and verification result digest. The packaged placeholder MUST NOT be interpreted as acceptance evidence.\n\n## H. Known limitations / deferred gates\n\nConcrete PILOT-04 voting persistence semantics, API integration, infrastructure/deployment automation, OPS console, CTRL control plane, FRONT UI and SEC penetration testing remain explicitly deferred. DATA-01 establishes storage authority foundations only.\n'''
    (root/'DATA01_DEVELOPER_VALIDATION_REPORT.md').write_text(report)
    bm=fmap(base); cm=fmap(root,{'SHA256SUMS.txt','DATA01_CHANGED_FILE_INVENTORY.json'}); changes=[]
    for rel in sorted(set(bm)|set(cm)|{'DATA01_CHANGED_FILE_INVENTORY.json','SHA256SUMS.txt'}):
        if rel=='DATA01_CHANGED_FILE_INVENTORY.json': ch='added'
        elif rel=='SHA256SUMS.txt': ch='modified'
        elif rel not in bm: ch='added'
        elif rel not in cm: ch='deleted'
        elif bm[rel]!=cm[rel]: ch='modified'
        else: continue
        changes.append({'path':rel,'change':ch})
    counts={k:sum(x['change']==k for x in changes) for k in ('added','modified','deleted')}
    if counts['deleted']!=0: raise SystemExit(f'predecessor deletion forbidden: {counts}')
    inv={'schema':'epd2.data01.changed-file-inventory/1','predecessor_filename':C3_NAME,'predecessor_sha256':C3_SHA,'counts':counts,'changes':changes}
    (root/'DATA01_CHANGED_FILE_INVENTORY.json').write_text(json.dumps(inv,indent=2,sort_keys=True)+'\n')
    lines=[]
    for p in sorted((x for x in root.rglob('*') if x.is_file() and x.relative_to(root).as_posix()!='SHA256SUMS.txt'), key=lambda x:x.relative_to(root).as_posix()):
        rel=p.relative_to(root).as_posix()
        if '__pycache__/' in rel or p.name.endswith('.pyc'): raise SystemExit(f'cache forbidden: {rel}')
        lines.append(f'{sha(p)}  {rel}')
    (root/'SHA256SUMS.txt').write_text('\n'.join(lines)+'\n'); return counts,len(lines)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--c3',required=True); ap.add_argument('--c6',required=True); ap.add_argument('--patch',required=True); ap.add_argument('--output',required=True); ap.add_argument('--work',required=True); a=ap.parse_args()
    c3=Path(a.c3).resolve(); c6=Path(a.c6).resolve(); patch=Path(a.patch).resolve(); output=Path(a.output).resolve(); work=Path(a.work).resolve()
    if c3.name!=C3_NAME or sha(c3)!=C3_SHA: raise SystemExit('C3 exact artifact mismatch')
    if c6.name!=C6_NAME or sha(c6)!=C6_SHA: raise SystemExit('C6 exact artifact mismatch')
    shutil.rmtree(work,ignore_errors=True); (work/'c3').mkdir(parents=True); (work/'c6').mkdir(); safe_extract_zip(c3,work/'c3'); safe_extract_zip(c6,work/'c6')
    base=one_root(work/'c3'); c6root=one_root(work/'c6'); root=work/TARGET_ROOT; shutil.copytree(base,root,copy_function=shutil.copy2)
    for d in list(root.rglob('__pycache__')): shutil.rmtree(d,ignore_errors=True)
    for n in ('.pytest_cache','.ruff_cache','.mypy_cache','node_modules','target','.git'):
        for d in list(root.rglob(n)):
            if d.is_dir(): shutil.rmtree(d,ignore_errors=True)
    safe_extract_tar(patch,root); pbdir=root/'data/baselines/pb01'; pbdir.mkdir(parents=True,exist_ok=True)
    for n in PB01_FILES: shutil.copy2(c6root/n,pbdir/n)
    counts,entries=write_generated(root,base)
    for p in sorted(root.rglob('*'),reverse=True):
        try: os.utime(p,(FIXED_TS,FIXED_TS),follow_symlinks=False)
        except OSError: pass
    os.utime(root,(FIXED_TS,FIXED_TS))
    if any(p.is_symlink() for p in root.rglob('*')): raise SystemExit('symlink forbidden')
    if output.exists(): output.unlink()
    with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6,strict_timestamps=True) as z:
        for p in [root,*sorted(root.rglob('*'),key=lambda x:x.relative_to(work).as_posix())]:
            rel=p.relative_to(work).as_posix()
            if p.is_dir():
                zi=zipfile.ZipInfo(rel.rstrip('/')+'/',(2026,8,20,0,0,0)); zi.create_system=3; zi.external_attr=((p.stat().st_mode&0xFFFF)<<16)|0x10; zi.extra=b''; z.writestr(zi,b'',compress_type=zipfile.ZIP_STORED)
            else:
                zi=zipfile.ZipInfo(rel,(2026,8,20,0,0,0)); zi.create_system=3; zi.external_attr=(p.stat().st_mode&0xFFFF)<<16; zi.compress_type=zipfile.ZIP_DEFLATED; zi.extra=b''; z.writestr(zi,p.read_bytes(),compress_type=zipfile.ZIP_DEFLATED,compresslevel=6)
    print(json.dumps({'candidate':output.name,'sha256':sha(output),'diff_counts':counts,'sha256sum_entries':entries},indent=2))
if __name__=='__main__': main()
