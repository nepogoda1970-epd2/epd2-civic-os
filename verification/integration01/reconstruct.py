#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, shutil, tarfile, zipfile
from pathlib import Path

def sha(p: Path) -> str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024), b''):
            h.update(b)
    return h.hexdigest()

def write_manifest(root: Path, manifest: Path) -> None:
    lines=[]
    for p in sorted(root.rglob('*')):
        if p.is_file() and p != manifest:
            lines.append(f"{sha(p)}  {p.relative_to(root).as_posix()}")
    manifest.write_text('\n'.join(lines)+'\n', encoding='utf-8')

def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument('--old-candidate', type=Path, required=True)
    ap.add_argument('--bundle', type=Path, required=True)
    ap.add_argument('--work', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a=ap.parse_args()
    shutil.rmtree(a.work, ignore_errors=True)
    a.work.mkdir(parents=True)
    bdir=a.work/'bundle'; bdir.mkdir()
    with tarfile.open(a.bundle,'r:*') as t: t.extractall(bdir, filter='data')
    exp=json.loads((bdir/'EXPECTED.json').read_text())
    assert sha(a.old_candidate)==exp['old_consolidation'], (sha(a.old_candidate),exp['old_consolidation'])
    olddir=a.work/'old'; olddir.mkdir()
    with zipfile.ZipFile(a.old_candidate) as z: z.extractall(olddir)
    oldroot=next(p for p in olddir.iterdir() if p.is_dir())
    package=a.work/'package'/exp['root_name']; repo=package/'repo'
    shutil.copytree(oldroot/'repo', repo)
    for p in (bdir/'repo_overlay').rglob('*'):
        if p.is_file():
            out=repo/p.relative_to(bdir/'repo_overlay'); out.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(p,out)
    write_manifest(repo, repo/'SHA256SUMS.txt')
    for p in (bdir/'package_overlay').rglob('*'):
        if p.is_file():
            out=package/p.relative_to(bdir/'package_overlay'); out.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(p,out)
            if (p.stat().st_mode & 0o100): out.chmod(out.stat().st_mode | 0o111)
    write_manifest(package, package/'SHA256SUMS.txt')
    fixed=tuple(exp['fixed_datetime']); a.out.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(a.out,'w',compression=zipfile.ZIP_STORED,allowZip64=True) as z:
        for p in sorted(package.rglob('*')):
            if not p.is_file(): continue
            arc=(Path(exp['root_name'])/p.relative_to(package)).as_posix()
            zi=zipfile.ZipInfo(arc,date_time=fixed); zi.compress_type=zipfile.ZIP_STORED; zi.create_system=3; zi.flag_bits|=0x800
            mode=0o755 if (p.stat().st_mode & 0o100) else 0o644; zi.external_attr=(0o100000|mode)<<16
            z.writestr(zi,p.read_bytes())
    got=sha(a.out); assert got==exp['candidate'],(got,exp['candidate'])
    print('INTEGRATION01_RECONSTRUCT_SHA_PASS',got,flush=True)
if __name__=='__main__': main()
