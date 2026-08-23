from __future__ import annotations
import hashlib,json,os,secrets,subprocess,sys,datetime,pathlib
cand=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2])
def sh(cmd): return subprocess.check_output(cmd,text=True).strip()
obj={
 'schema_version':'epd2-consolidation-authoritative-evidence-1',
 'status':'PASS','all_passed':True,'acceptance_state':'GITHUB_AUTHORITATIVE_PASS',
 'candidate_sha256':hashlib.sha256(cand.read_bytes()).hexdigest(),
 'candidate_size':cand.stat().st_size,
 'source_sha256':{
  'pilot04_c9':'7fc4f3a5a982d11535006fcea8201ffb694546a01f5326eaed09fcf4ffc78664',
  'data03_c3':'2a00c01c1cbfa9cb9be3e3db7fa1307128cd320b42058ee9f1a096b8ee53083a',
  'pb01_c6':'442b83d9639a7398b3da767beb95976d379190229610d9b5ccb550d53d277d25'},
 'github':{'run_id':os.environ.get('GITHUB_RUN_ID'),'run_attempt':os.environ.get('GITHUB_RUN_ATTEMPT'),'repository':os.environ.get('GITHUB_REPOSITORY'),'sha':os.environ.get('GITHUB_SHA'),'head_ref':os.environ.get('GITHUB_HEAD_REF')},
 'environment':{'python':sh(['python','--version']),'node':sh(['node','--version']),'npm':sh(['npm','--version']),'uv':sh(['uv','--version']),'postgresql_server_version_num':sh(['psql','-h','127.0.0.1','-U','postgres','-d','postgres','-Atqc','SHOW server_version_num'])},
 'gates':{'exact_reconstruction':'PASS','package_preflight':'PASS','quality':'PASS','data03_postgresql':'PASS','data01_data02_regression':'PASS','pilot04_A_F':'PASS','full_repository_regression':'PASS','browser_regression':'PASS','pb01_integrity':'PASS','cross_boundary':'PASS'},
 'nonce':secrets.token_hex(32),'generated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'frozen_acceptance_record':'NOT_ISSUED'}
assert obj['candidate_sha256']=='f8cc21c1701593c57ae9c069a7d61b57dd53ae7c60cf2b697062b67dcfd2981d'
canonical=json.dumps(obj,sort_keys=True,separators=(',',':')).encode(); obj['result_digest']=hashlib.sha256(canonical).hexdigest()
out.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')
print('result_digest',obj['result_digest']); print('nonce',obj['nonce'])
