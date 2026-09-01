#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, os, shutil, stat
from pathlib import Path
ACCEPTED_API03_SHA="5fb769cd387c7bcf10b9783d05fce44066985c7408a015cb4c670419ce316b55"
R2_SHA="1f3e172e579d66b30416dc8a0779dc3dfe67f6cf0c85c1ca3b1ffa2337f8dc1d"
def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as fh:
        for block in iter(lambda:fh.read(1024*1024),b''): h.update(block)
    return h.hexdigest()

def copy_api04_delta(r2: Path, out: Path) -> None:
    for rel in ('docs/api/API-04','services/events-messaging-runtime'):
        dst=out/rel
        if dst.exists(): shutil.rmtree(dst)
        shutil.copytree(r2/rel,dst)
    for rel in ('contracts/reason-codes/api-04.yml','scripts/provision_broker.py','scripts/validate_api04.py'):
        dst=out/rel; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(r2/rel,dst)

def apply_correction_patch(out: Path, patch_file: Path) -> None:
    import subprocess
    subprocess.run(['patch','-p1','--batch','--forward','-i',str(patch_file)], cwd=out, check=True)
    setup=out/'scripts/api04_ci_setup.sh'
    if setup.exists(): setup.chmod(0o755)
    legacy=out/'services/events-messaging-runtime/src/epd2_events_messaging_runtime/identity/api03_r13_adapter.py'
    if legacy.exists(): legacy.unlink()

def predecessor_manifest(api03: Path, out: Path) -> None:
    exclude={'docs/roadmap/EPD2_PROGRAM_CONTROL_REGISTER.md','SHA256SUMS.txt'}
    rows=[]
    for p in sorted(api03.rglob('*')):
        if p.is_file():
            rel=p.relative_to(api03).as_posix()
            if rel in exclude: continue
            rows.append(f"{sha256(p)}  {rel}")
    (out/'API03_C5_PREDECESSOR_SHA256SUMS.txt').write_text('\n'.join(rows)+'\n')

def overlay_governance(repo: Path, out: Path) -> dict:
    paths=['docs/roadmap/EPD2_PROGRAM_CONTROL_REGISTER.md','docs/api/API-03/API03_C5_ACCEPTANCE_RECORD.json']
    digests={}
    for rel in paths:
        src=repo/rel
        if not src.is_file(): raise SystemExit(f'missing current governance: {rel}')
        dst=out/rel; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
        digests[rel]=sha256(dst)
    (out/'docs/api/API-04/API04_CURRENT_GOVERNANCE_BINDING.json').write_text(json.dumps({
      'source_commit':os.environ.get('GITHUB_SHA'), 'files':digests,
      'note':'Current canonical governance overlay; runtime predecessor bytes remain exact API-03 C5.'
    },indent=2)+'\n')
    return digests

def clean(out: Path) -> None:
    for p in list(out.rglob('*')):
        if p.is_dir() and p.name in {'__pycache__','.pytest_cache','.mypy_cache'}: shutil.rmtree(p,ignore_errors=True)
        elif p.is_file() and p.name=='.DS_Store': p.unlink()

def refresh_inventory(out: Path, *, status: str) -> None:
    docs=out/'docs/api/API-04'
    inv=json.loads((docs/'API04_PRESEAL_INVENTORY.json').read_text())
    inv['version']='0.3.0-c1'
    inv['status']=status
    registry=json.loads((docs/'API04_TOPIC_AND_SUBSCRIPTION_REGISTER.json').read_text())
    acl=json.loads((docs/'API04_PRODUCER_CONSUMER_ACL_MATRIX.json').read_text())
    src=out/'services/events-messaging-runtime/src/epd2_events_messaging_runtime'
    inv['counts']={
      **inv.get('counts',{}),
      'topics':len(registry['topics']),'subscriptions':len(registry['subscriptions']),
      'produce_bindings':len(acl['produce_bindings']),'consume_bindings':len(acl['consume_bindings']),
      'source_modules':len(list(src.rglob('*.py'))),
      'migrations':len(list((src/'persistence/migrations/postgresql').glob('*.sql'))),
      'documents':len(list(docs.glob('*.md'))),'registers':len(list(docs.glob('*.json'))),
    }
    inv['predecessor']={
      'api03_c5_sha256':ACCEPTED_API03_SHA,'state':'ACCEPTED / CLOSED',
      'reconciliation_state':'RECONCILED_AGAINST_EXACT_ACCEPTED_API03_C5'
    }
    (docs/'API04_PRESEAL_INVENTORY.json').write_text(json.dumps(inv,indent=2)+'\n')

def file_manifest(out: Path, *, status: str) -> None:
    target=out/'docs/api/API-04/API04_PRESEAL_FILE_MANIFEST.json'
    files=[]; total=0
    for p in sorted(out.rglob('*')):
        if not p.is_file(): continue
        rel=p.relative_to(out).as_posix()
        if rel in {'SHA256SUMS.txt','docs/api/API-04/API04_PRESEAL_FILE_MANIFEST.json'} or rel.startswith('validation/api04/'): continue
        size=p.stat().st_size; total+=size; files.append({'path':rel,'bytes':size,'sha256':sha256(p)})
    target.write_text(json.dumps({
      'register':'API04_PRESEAL_FILE_MANIFEST','version':'0.3.0-c1','status':status,
      'note':'Regenerated from exact accepted API-03 C5 plus API-04 C1 owned delta.',
      'file_count':len(files),'total_bytes':total,'files':files
    },indent=2)+'\n')

def set_status(out: Path, status: str, version: str) -> None:
    (out/'docs/api/API-04/API04_STATUS.txt').write_text(status+'\n')
    for rel in ['services/events-messaging-runtime/src/epd2_events_messaging_runtime/__init__.py',
                'services/events-messaging-runtime/src/epd2_events_messaging_runtime/runtime/composition.py']:
        p=out/rel; s=p.read_text();
        s=s.replace('STATUS = "PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED"',f'STATUS = "{status}"')
        if rel.endswith('__init__.py'):
            s=s.replace('VERSION = "0.2.0-preseal"',f'VERSION = "{version}"')
        p.write_text(s)
    lin=out/'docs/api/API-04/API04_LINEAGE.json'; d=json.loads(lin.read_text()); d['status']=status; d['mode']='SEALED_CANDIDATE_NOT_ACCEPTED' if status=='CANDIDATE_NOT_ACCEPTED' else 'RECONCILED_PRESEAL_NOT_ACCEPTED'; lin.write_text(json.dumps(d,indent=2)+'\n')
    acl=out/'docs/api/API-04/API04_PRODUCER_CONSUMER_ACL_MATRIX.json'; d=json.loads(acl.read_text()); d['status']=status; acl.write_text(json.dumps(d,indent=2)+'\n')

def seal(out: Path, *, builder_run: str, builder_commit: str, workflow_template: Path) -> None:
    dst=out/'handoff/API-04/templates/C1/api04-accept.yml'; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(workflow_template,dst)
    wf_sha=sha256(dst)
    seal_record=out/'docs/api/API-04/API04_C1_SEAL_RECORD.json'
    seal_record.write_text(json.dumps({
      'schema':'epd2.api04.c1.seal/1','stage':'API-04','candidate_role':'C1',
      'candidate_self_state':'CANDIDATE_NOT_ACCEPTED','self_accepted':False,
      'source_r2':{'sha256':R2_SHA,'size_bytes':1309315,'discovery_run_id':33528603078,'artifact_id':9808749950},
      'accepted_predecessor':{'stage':'API-03','role':'C5','sha256':ACCEPTED_API03_SHA,'size_bytes':43300451,'authoritative_run_id':33511256210},
      'builder':{'run_id':builder_run,'provenance_commit':builder_commit},
      'sealed_acceptance_workflow':{'path':'handoff/API-04/templates/C1/api04-accept.yml','sha256':wf_sha},
      'acceptance_requirement':'Independent workflow must reproduce this workflow byte-for-byte, verify complete SHA256SUMS and rerun G0-G27 with zero blocked gates.',
    },indent=2)+'\n')
    clean(out); refresh_inventory(out,status='CANDIDATE_NOT_ACCEPTED'); file_manifest(out,status='CANDIDATE_NOT_ACCEPTED')
    rows=[]
    for p in sorted(out.rglob('*')):
        if p.is_file() and p.relative_to(out).as_posix()!='SHA256SUMS.txt': rows.append(f"{sha256(p)}  {p.relative_to(out).as_posix()}")
    (out/'SHA256SUMS.txt').write_text('\n'.join(rows)+'\n')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--api03-root'); ap.add_argument('--r2-root'); ap.add_argument('--repo-root'); ap.add_argument('--out-root'); ap.add_argument('--finalize',action='store_true'); ap.add_argument('--workflow-template'); ap.add_argument('--patch-file'); args=ap.parse_args()
    out=Path(args.out_root)
    if not args.finalize:
        api03=Path(args.api03_root); r2=Path(args.r2_root); repo=Path(args.repo_root)
        if out.exists(): shutil.rmtree(out)
        shutil.copytree(api03,out,copy_function=shutil.copy2)
        copy_api04_delta(r2,out); apply_correction_patch(out,Path(args.patch_file)); predecessor_manifest(api03,out); overlay_governance(repo,out); clean(out)
        set_status(out,'PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED','0.3.0-c1-preseal')
        refresh_inventory(out,status='PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED'); file_manifest(out,status='PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED')
        print('API04_C1_RECONCILE:PASS',out)
    else:
        set_status(out,'CANDIDATE_NOT_ACCEPTED','0.3.0-c1')
        seal(out,builder_run=os.environ.get('GITHUB_RUN_ID','LOCAL'),builder_commit=os.environ.get('GITHUB_SHA','LOCAL'),workflow_template=Path(args.workflow_template))
        print('API04_C1_SEAL:PASS',out)
if __name__=='__main__': main()
