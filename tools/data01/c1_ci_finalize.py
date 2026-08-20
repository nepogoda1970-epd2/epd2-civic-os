#!/usr/bin/env python3
import argparse, hashlib, json, os, shutil, stat, zipfile
from pathlib import Path

C1_ROOT = 'EPD2_DATA-01_CANONICAL_DATA_OWNERSHIP_PERSISTENCE_BOUNDARIES_AND_AUDIT_EVIDENCE_FOUNDATION_CANDIDATE_0.1_C1'
C3_NAME = 'EPD2_PILOT03_ASSEMBLIES_MOTIONS_AND_COMMUNICATIONS_CANDIDATE_0.1_C3.zip'
C3_SHA = '52b5bbfe312d90d65f500f0b6085d33ffe3235ce4bd90562110a26a8fae208d1'
SELFREF = {'DATA01_CHANGED_FILE_INVENTORY.json', 'SHA256SUMS.txt'}
CACHE_DIRS = {'.ruff_cache','.pytest_cache','.mypy_cache','__pycache__','node_modules','target'}

def sha(p: Path) -> str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024), b''): h.update(b)
    return h.hexdigest()

def filemap(root: Path):
    return {p.relative_to(root).as_posix():sha(p) for p in root.rglob('*') if p.is_file() and not p.is_symlink()}

def extract_one(zpath: Path, out: Path) -> Path:
    shutil.rmtree(out, ignore_errors=True); out.mkdir(parents=True)
    with zipfile.ZipFile(zpath) as z: z.extractall(out)
    roots=[p for p in out.iterdir() if p.is_dir()]
    if len(roots)!=1: raise SystemExit(f'expected one root in {zpath}, got {roots}')
    return roots[0]

def clean(root: Path):
    for p in sorted(root.rglob('*'), reverse=True):
        if p.is_dir() and p.name in CACHE_DIRS:
            shutil.rmtree(p, ignore_errors=True)
    for p in root.rglob('*.pyc'):
        p.unlink(missing_ok=True)

def inventory(root: Path, c3zip: Path, work: Path):
    if sha(c3zip)!=C3_SHA: raise SystemExit('wrong C3 SHA')
    c3root=extract_one(c3zip, work/'c3')
    pre=filemap(c3root); cur=filemap(root)
    changes=[]; counts={'added':0,'deleted':0,'modified':0}
    for rel in sorted(set(pre)|set(cur)):
        if rel not in pre: kind='added'
        elif rel not in cur: kind='deleted'
        elif pre[rel]!=cur[rel]: kind='modified'
        else: continue
        counts[kind]+=1
        changes.append({'change':kind,'current_sha256':None if rel in SELFREF else cur.get(rel),'path':rel,'predecessor_sha256':pre.get(rel)})
    doc={
      'changes':changes,'counts':counts,
      'derivation_rule':'exact SHA-256 file-map comparison of external accepted PILOT-03 C3 archive against sealed candidate root; self-referential inventory/SHA paths have null current hash and are bound by exact SHA256SUMS/preflight coverage',
      'derived_from_external_predecessor_zip':True,
      'predecessor_filename':C3_NAME,'predecessor_sha256':C3_SHA,
      'schema':'epd2.data01.changed-file-inventory/2'
    }
    (root/'DATA01_CHANGED_FILE_INVENTORY.json').write_text(json.dumps(doc,indent=2,sort_keys=False)+'\n')
    return counts

def sums(root: Path):
    rows=[]
    for p in sorted((p for p in root.rglob('*') if p.is_file() and not p.is_symlink()), key=lambda p:p.relative_to(root).as_posix()):
        rel=p.relative_to(root).as_posix()
        if rel=='SHA256SUMS.txt': continue
        rows.append(f'{sha(p)}  {rel}')
    (root/'SHA256SUMS.txt').write_text('\n'.join(rows)+'\n')
    return len(rows)

def modes_from_c0(c0zip: Path):
    out={}
    with zipfile.ZipFile(c0zip) as z:
        for i in z.infolist():
            parts=Path(i.filename.rstrip('/')).parts
            if len(parts)<2: continue
            rel=Path(*parts[1:]).as_posix()
            out[rel]=(i.external_attr>>16)&0xFFFF
    return out

def pack(root: Path, c0zip: Path, out: Path):
    modes=modes_from_c0(c0zip); work=root.parent
    if out.exists(): out.unlink()
    with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6,strict_timestamps=True) as z:
        paths=[root,*sorted(root.rglob('*'),key=lambda p:p.relative_to(work).as_posix())]
        for p in paths:
            relfull=p.relative_to(work).as_posix(); rel=p.relative_to(root).as_posix() if p!=root else ''
            key=relfull.rstrip('/')
            if p.is_dir():
                mode=modes.get(rel,0o40755)
                zi=zipfile.ZipInfo(key+'/',(2026,8,20,0,0,0)); zi.create_system=3; zi.external_attr=(mode<<16)|0x10; zi.extra=b''
                z.writestr(zi,b'',compress_type=zipfile.ZIP_STORED)
            else:
                mode=modes.get(rel,0o100755 if rel=='scripts/data01/validate_data01.py' else 0o100644)
                zi=zipfile.ZipInfo(relfull,(2026,8,20,0,0,0)); zi.create_system=3; zi.external_attr=mode<<16; zi.extra=b''
                z.writestr(zi,p.read_bytes(),compress_type=zipfile.ZIP_DEFLATED,compresslevel=6)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,required=True); ap.add_argument('--c0',type=Path,required=True); ap.add_argument('--c3',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); ap.add_argument('--work',type=Path,required=True); a=ap.parse_args()
    if a.root.name!=C1_ROOT: raise SystemExit('wrong C1 root name')
    clean(a.root)
    (a.root/'DATA01_CHANGED_FILE_INVENTORY.json').unlink(missing_ok=True)
    (a.root/'SHA256SUMS.txt').unlink(missing_ok=True)
    (a.root/'DATA01_CHANGED_FILE_INVENTORY.json').write_text('{}\n')
    (a.root/'SHA256SUMS.txt').write_text('')
    counts=inventory(a.root,a.c3,a.work)
    coverage=sums(a.root)
    clean(a.root)
    pack(a.root,a.c0,a.output)
    print(json.dumps({'candidate':a.output.name,'candidate_sha256':sha(a.output),'external_c3_to_c1_counts':counts,'sha256sums_coverage':coverage},sort_keys=True))
if __name__=='__main__': main()
