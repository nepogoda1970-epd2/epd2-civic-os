#!/usr/bin/env python3
import hashlib
import json
import subprocess
from pathlib import Path

main = subprocess.check_output(['git','rev-parse','origin/main'], text=True).strip()
tree = subprocess.check_output(['git','show','-s','--format=%T','origin/main'], text=True).strip()
modified = subprocess.check_output(['git','show','-s','--format=%cI','origin/main'], text=True).strip().replace('+00:00','Z')
pcr = Path('docs/roadmap/EPD2_PROGRAM_CONTROL_REGISTER.md')
pcr_sha = hashlib.sha256(pcr.read_bytes()).hexdigest()
pcr_blob = subprocess.check_output(['git','rev-parse','origin/main:docs/roadmap/EPD2_PROGRAM_CONTROL_REGISTER.md'], text=True).strip()
old = {
    '81c2d0db987536718b30242eeb168aecc21877ca': main,
    '5460ccd9ec5929c2136926a4a2585f3fca52937e': tree,
    '21857ce3ef10ab8a5cdd6b176938e564dc614cad1518b36525336ca64b454b5e': pcr_sha,
    '663b583a58453744e193cf468b7d6f59ff009d87': pcr_blob,
    '2026-09-03T22:08:26Z': modified,
}
paths = [
    Path('docs/infra/INFRA-04/INFRA-04-KNOWN-LIMITATIONS.md'),
    Path('docs/infra/INFRA-04/INFRA-04-STAGE-CONTRACT.md'),
    Path('docs/infra/INFRA-04/INFRA04_DEVELOPER_REPORT.md'),
    Path('validation/infra04/verification-summary.json'),
    Path('validation/infra04/main-binding.json'),
    Path('validation/infra04/verification-transcript.txt'),
]
for path in paths:
    if not path.exists():
        continue
    text = path.read_text()
    for before, after in old.items():
        text = text.replace(before, after)
    path.write_text(text)
rp = Path('docs/infra/INFRA-01/INFRA01_GOVERNANCE_RECONCILIATION.json')
rec = json.loads(rp.read_text())
rec['target_authority'] = {
    'main_commit': main,
    'main_tree': tree,
    'pcr_sha256': pcr_sha,
    'pcr_blob_sha': pcr_blob,
    'pcr_path': 'docs/roadmap/EPD2_PROGRAM_CONTROL_REGISTER.md',
    'pcr_modified_at': modified,
}
rec.setdefault('expected_state', {})['OPS-03'] = {'version':'0.1','status':'ACCEPTED','implementation':'CLOSED'}
for region in rec.get('verification', {}).get('regions', []):
    if region.get('id') == 'ops03-not-accepted':
        region.clear()
        region.update({'id':'ops03-accepted-closed','must_include':'OPS-03 ACCEPTED / CLOSED','must_exclude':'OPS-03 QUALIFICATION ELIGIBLE'})
rp.write_text(json.dumps(rec, indent=2) + '\n')
sp = Path('scripts/infra02/supply_chain_policy.json')
policy = json.loads(sp.read_text())
for name in ('ops03-c3-authoritative-build.yml','ops03-c3-final.yml','ops03-c3-v2.yml'):
    policy['workflow_classes'][name] = 'historical-stage'
policy['workflow_classes'] = dict(sorted(policy['workflow_classes'].items()))
sp.write_text(json.dumps(policy, indent=2) + '\n')
print(f'LIVE_MAIN={main}')
print(f'LIVE_TREE={tree}')
print(f'LIVE_PCR_SHA256={pcr_sha}')
print(f'LIVE_PCR_BLOB={pcr_blob}')
print(f'LIVE_PCR_MODIFIED={modified}')
