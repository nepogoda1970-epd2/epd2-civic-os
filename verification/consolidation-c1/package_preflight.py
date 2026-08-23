from __future__ import annotations
import hashlib, pathlib, stat, sys, zipfile
p=pathlib.Path(sys.argv[1]); expected='f8cc21c1701593c57ae9c069a7d61b57dd53ae7c60cf2b697062b67dcfd2981d'
assert hashlib.sha256(p.read_bytes()).hexdigest()==expected
with zipfile.ZipFile(p) as z:
 names=z.namelist(); assert len(names)==len(set(names)); assert z.testzip() is None
 roots={n.split('/')[0] for n in names if n}; assert len(roots)==1
 for i in z.infolist():
  q=pathlib.PurePosixPath(i.filename)
  assert not q.is_absolute() and '..' not in q.parts
  mode=(i.external_attr>>16)&0xffff
  assert not stat.S_ISLNK(mode)
 root=next(iter(roots)); sums=z.read(root+'/SHA256SUMS.txt').decode().splitlines(); declared={}
 for line in sums:
  h,n=line.split('  ',1); assert n not in declared and len(h)==64; declared[n]=h
 actual={}
 for i in z.infolist():
  if i.is_dir(): continue
  rel='/'.join(i.filename.split('/')[1:])
  if rel=='SHA256SUMS.txt': continue
  actual[rel]=hashlib.sha256(z.read(i.filename)).hexdigest()
 assert declared==actual,(len(declared),len(actual),set(declared)^set(actual))
 print(f'PACKAGE_PREFLIGHT_PASS entries={len(names)} sha256sums={len(actual)}/{len(actual)}')
