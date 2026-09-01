#!/usr/bin/env python3
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import stat
import sys

EXPECTED_ROLE='C5'
MANIFEST_REL='docs/api/API-03/API03_C5_SEALED_FILE_MANIFEST.json'
CHECKSUM_REL='SHA256SUMS.txt'
WORKFLOW_REL='.github/workflows/api03-accept.yml'
STATUS_REL='API03_C5_STATUS.txt'
SOURCE_C4_SHA='09531e9b64dd66c558e3c2478ea897e020adfd4814a7237cd8eab7f18b568a86'
ACCEPTED_C13_SHA='9363561271f0f92d2afc42ccbb0d792cb5461c97c19a5f46a6fa51408bdfc6a9'

def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):
            h.update(chunk)
    return h.hexdigest()

def relfiles(root: Path) -> list[str]:
    out=[]
    for p in root.rglob('*'):
        if p.is_symlink():
            raise AssertionError(f'symlink forbidden: {p.relative_to(root)}')
        if p.is_file():
            out.append(p.relative_to(root).as_posix())
    return sorted(out)

def parse_sums(path: Path) -> dict[str,str]:
    rows={}
    for line in path.read_text(encoding='utf-8').splitlines():
        if not line.strip(): continue
        assert len(line)>=67 and line[64:66]=='  ',f'invalid SHA256SUMS row: {line!r}'
        digest=line[:64]; rel=line[66:]
        assert len(digest)==64 and all(c in '0123456789abcdef' for c in digest),digest
        assert rel and rel not in rows,rel
        rows[rel]=digest
    return rows

def main() -> int:
    root=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
    assert root.is_dir(),root
    assert (root/STATUS_REL).read_text(encoding='utf-8').strip()=='CANDIDATE_NOT_ACCEPTED'
    assert not (root/'API03_C4_STATUS.txt').exists()
    all_files=relfiles(root)
    assert CHECKSUM_REL in all_files and MANIFEST_REL in all_files and WORKFLOW_REL in all_files
    sums=parse_sums(root/CHECKSUM_REL)
    expected_sums=set(all_files)-{CHECKSUM_REL}
    assert set(sums)==expected_sums,{'missing':sorted(expected_sums-set(sums)),'extra':sorted(set(sums)-expected_sums)}
    for rel,digest in sums.items():
        actual=sha256(root/rel)
        assert actual==digest,(rel,actual,digest)
    manifest=json.loads((root/MANIFEST_REL).read_text(encoding='utf-8'))
    assert manifest['schema']=='epd2.api03.sealed-file-manifest/1'
    assert manifest['stage']=='API-03' and manifest['candidate']['role']==EXPECTED_ROLE
    assert manifest['candidate']['root']==root.name
    assert manifest['source_c4_sha256']==SOURCE_C4_SHA
    assert manifest['accepted_api02_c13_sha256']==ACCEPTED_C13_SHA
    assert manifest['files_in_archive']==len(all_files)
    assert manifest['excluded_self_referential']==[MANIFEST_REL,CHECKSUM_REL]
    entries=manifest['entries']
    entry_map={e['path']:e for e in entries}
    assert len(entry_map)==len(entries),'duplicate manifest path'
    expected_entries=set(all_files)-{MANIFEST_REL,CHECKSUM_REL}
    assert set(entry_map)==expected_entries,{'missing':sorted(expected_entries-set(entry_map)),'extra':sorted(set(entry_map)-expected_entries)}
    for rel,e in entry_map.items():
        p=root/rel
        assert e['sha256']==sha256(p),(rel,'sha')
        assert e['size']==p.stat().st_size,(rel,'size')
        mode=f"{stat.S_IMODE(p.stat().st_mode):04o}"
        assert e['mode']==mode,(rel,e['mode'],mode)
    assert sums[MANIFEST_REL]==sha256(root/MANIFEST_REL)
    workflow=(root/WORKFLOW_REL).read_text(encoding='utf-8')
    assert 'API-03 C5 authoritative acceptance' in workflow
    assert 'CANDIDATE_NOT_ACCEPTED' in workflow
    assert 'API03_RESULT:PASS:validation/api03/authoritative_acceptance_result.json' in workflow
    assert '# DRAFT' not in workflow and 'This workflow is a draft' not in workflow
    seal=json.loads((root/'docs/api/API-03/API03_C5_SEAL_RECORD.json').read_text(encoding='utf-8'))
    assert seal['candidate_state']=='CANDIDATE_NOT_ACCEPTED'
    assert seal['source_c4']['sha256']==SOURCE_C4_SHA
    assert seal['accepted_predecessor']['sha256']==ACCEPTED_C13_SHA
    assert seal['sealed_workflow_sha256']==sha256(root/WORKFLOW_REL)
    assert seal['open_blockers']==['independent authoritative acceptance']
    print(json.dumps({'status':'PASS','files_in_archive':len(all_files),'sha256_rows':len(sums),'manifest_entries':len(entries),'workflow_sha256':sha256(root/WORKFLOW_REL)},sort_keys=True))
    print('API03_C5_SEAL:PASS')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
