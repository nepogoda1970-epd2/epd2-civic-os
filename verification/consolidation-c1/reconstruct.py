#!/usr/bin/env python3
from __future__ import annotations
import argparse, base64, hashlib, json, shutil, tarfile, zipfile
from pathlib import Path

C9_NAME='EPD2_PILOT04_NON_BINDING_DIGITAL_VOTE_PILOT_CANDIDATE_0.1_C9_ACCEPTED.zip'
D3_NAME='EPD2_DATA-03_OUTBOX_EVENT_STORE_AND_PROJECTIONS_CANDIDATE_0.1_C3.zip'
PB_NAME='EPD2_VCRYPTO-PB01-I10_FINAL_CRYPTOGRAPHIC_PROFILE_FREEZE_AND_RELEASE_READINESS_DECISION_CANDIDATE_0.1_C6.zip'
ROOT_NAME='EPD2_CONSOLIDATED_PILOT04_DATA03_PB01_BASELINE_CANDIDATE_0.1_C1'

def sha(path:Path)->str:
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
 return h.hexdigest()

def zi_from(m):
 z=zipfile.ZipInfo(m['filename'], tuple(m['date_time']))
 z.compress_type=m['compress_type']; z.comment=base64.b64decode(m['comment_b64']); z.extra=base64.b64decode(m['extra_b64'])
 z.create_system=m['create_system']; z.create_version=m['create_version']; z.extract_version=m['extract_version']; z.flag_bits=m['flag_bits']; z.volume=m['volume']; z.internal_attr=m['internal_attr']; z.external_attr=m['external_attr']
 return z

def striproot(name):
 p=name.split('/')
 return '/'.join(p[1:]) if len(p)>1 else name

def find_by_sha(root:Path, expected:str)->Path:
 for p in root.rglob('*'):
  if p.is_file() and sha(p)==expected: return p
 raise SystemExit(f'missing exact source {expected}')

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--c9',type=Path,required=True); ap.add_argument('--pb01',type=Path,required=True); ap.add_argument('--bundle',type=Path,required=True); ap.add_argument('--work',type=Path,required=True); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
 shutil.rmtree(a.work,ignore_errors=True); a.work.mkdir(parents=True)
 bdir=a.work/'bundle'; bdir.mkdir()
 with tarfile.open(a.bundle,'r:*') as t: t.extractall(bdir,filter='data')
 exp=json.loads((bdir/'EXPECTED.json').read_text())
 assert sha(a.c9)==exp['c9'],(sha(a.c9),exp['c9']); assert sha(a.pb01)==exp['pb01']
 zc9=zipfile.ZipFile(a.c9); c9map={striproot(i.filename):i for i in zc9.infolist() if not i.is_dir()}
 d3=a.work/D3_NAME
 recipe=json.loads((bdir/'d3_recipe.json').read_text())
 with zipfile.ZipFile(d3,'w') as zout:
  for m in recipe:
   zi=zi_from(m)
   if zi.is_dir(): data=b''
   else:
    rel=striproot(zi.filename); ov=bdir/'d3_overlay'/rel
    if ov.is_file(): data=ov.read_bytes()
    else: data=zc9.read(c9map[rel].filename)
   zout.writestr(zi,data,compress_type=zi.compress_type,compresslevel=6)
 assert sha(d3)==exp['data03'],(sha(d3),exp['data03'])
 print('RECONSTRUCT_DATA03_SHA_PASS',sha(d3),flush=True)
 package=a.work/'package'/ROOT_NAME; repo=package/'repo'; repo.mkdir(parents=True)
 for i in zc9.infolist():
  if i.is_dir(): continue
  rel=striproot(i.filename); p=repo/rel; p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(zc9.read(i.filename))
 for p in (bdir/'repo_overlay').rglob('*'):
  if p.is_file(): out=repo/p.relative_to(bdir/'repo_overlay'); out.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(p,out)
 for p in (bdir/'package_overlay').rglob('*'):
  if p.is_file(): out=package/p.relative_to(bdir/'package_overlay'); out.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(p,out)
 anchors=package/'anchors'; anchors.mkdir(parents=True,exist_ok=True)
 shutil.copyfile(a.c9,anchors/C9_NAME); shutil.copyfile(d3,anchors/D3_NAME); shutil.copyfile(a.pb01,anchors/PB_NAME)
 frecipe=json.loads((bdir/'final_recipe.json').read_text())
 a.out.parent.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(a.out,'w') as zout:
  for m in frecipe:
   zi=zi_from(m)
   if zi.is_dir(): data=b''
   else:
    rel=striproot(zi.filename); data=(package/rel).read_bytes()
   zout.writestr(zi,data,compress_type=zi.compress_type,compresslevel=9)
 assert sha(a.out)==exp['candidate'],(sha(a.out),exp['candidate'])
 print('RECONSTRUCT_CANDIDATE_SHA_PASS',sha(a.out),flush=True)

if __name__=='__main__': main()
