from __future__ import annotations
import hashlib,json,os,sys,pathlib
p=pathlib.Path(sys.argv[1]); x=json.loads(p.read_text()); d=x.pop('result_digest'); calc=hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
assert d==calc; assert x['status']=='PASS' and x['all_passed'] is True and x['acceptance_state']=='GITHUB_AUTHORITATIVE_PASS'; assert x['candidate_sha256']=='f8cc21c1701593c57ae9c069a7d61b57dd53ae7c60cf2b697062b67dcfd2981d'; assert x['github']['run_id']==os.environ['GITHUB_RUN_ID']; assert all(v=='PASS' for v in x['gates'].values()); assert x['frozen_acceptance_record']=='NOT_ISSUED'; print('EVIDENCE_VERIFY_PASS',d)
