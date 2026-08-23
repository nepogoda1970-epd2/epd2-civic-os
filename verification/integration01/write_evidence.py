#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,os,platform,sys
from pathlib import Path

def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1048576),b''):
            h.update(b)
    return h.hexdigest()

zip_path=Path(sys.argv[1])
out=Path(sys.argv[2])
expected=os.environ['INT_EXPECTED_SHA']
assert sha(zip_path)==expected
obj={
    'schema':'epd2.integration01.github-acceptance.v1',
    'result':'PASS',
    'candidate_sha256':expected,
    'candidate_size':zip_path.stat().st_size,
    'github_run_id':os.environ.get('GITHUB_RUN_ID'),
    'github_run_attempt':os.environ.get('GITHUB_RUN_ATTEMPT'),
    'github_sha':os.environ.get('GITHUB_SHA'),
    'github_ref':os.environ.get('GITHUB_REF'),
    'runner_os':platform.platform(),
    'python':platform.python_version(),
    'inputs':{
        'pilot04_c9':'7fc4f3a5a982d11535006fcea8201ffb694546a01f5326eaed09fcf4ffc78664',
        'data04_c1':'e5502772cbb4abe961ca46059fa02a9610dd243e86c31ece7b7e5148aeb5c3d3',
        'pb01_c6':'442b83d9639a7398b3da767beb95976d379190229610d9b5ccb550d53d277d25'
    },
    'gates':['STATIC_PACKAGE','CANONICAL_ENV','FROZEN_DEPS','RUFF','RUFF_FORMAT','TYPECHECK','DATA04_LIVE','DATA04_TESTS','DATA03_REGRESSION','PILOT04_SECURITY_A_F','FULL_PYTEST','BROWSER','PB01_INTEGRITY','CROSS_BOUNDARY']
}
canon=json.dumps(obj,sort_keys=True,separators=(',',':')).encode()
obj['result_digest']=hashlib.sha256(canon).hexdigest()
out.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')
print('INTEGRATION01_EVIDENCE_DIGEST',obj['result_digest'])
