#!/usr/bin/env python3
import hashlib,json,os,sys
p=sys.argv[1]
o=json.load(open(p))
d=o.pop('result_digest')
calc=hashlib.sha256(json.dumps(o,sort_keys=True,separators=(',',':')).encode()).hexdigest()
assert d==calc
assert o['result']=='PASS'
assert o['candidate_sha256']==os.environ['INT_EXPECTED_SHA']
print('INTEGRATION01_EVIDENCE_PASS',d)
