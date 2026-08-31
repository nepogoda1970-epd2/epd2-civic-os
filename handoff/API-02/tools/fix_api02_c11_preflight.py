from __future__ import annotations
import importlib
import json
import pathlib
import sys

root=pathlib.Path(sys.argv[1]).resolve()

# C11 carried-workflow entering-baseline comment.
p=root/'.github/workflows/api02-accept.yml'
t=p.read_text()
t=t.replace('API02_ENTERING_CANDIDATE_ZIP       …API02…CANDIDATE_0.1_C9.zip  42a1a59a…','API02_ENTERING_CANDIDATE_ZIP       …API02…CANDIDATE_0.1_C10.zip  479e1732…')
p.write_text(t)

# C11 exposes a latent C10+ bug in the stale-audit historical-cue regex.
p=root/'scripts/api02/build_stale_audit.py'
t=p.read_text()
old='_PAST_ROUND = f"C[1-{int(CANDIDATE_ROLE[1:]) - 1}]" if CANDIDATE_ROLE[1:].isdigit() else "C[12]"'
new='''def _past_round_cue_pattern() -> str:\n    rounds = past_rounds()\n    if not rounds:\n        return r"C(?!)"\n    return r"(?:" + "|".join(re.escape(round_name) for round_name in rounds) + r")"\n\n\n_PAST_ROUND = _past_round_cue_pattern()'''
if old not in t:
    raise SystemExit('expected legacy _PAST_ROUND expression not found')
t=t.replace(old,new,1)
p.write_text(t)

# C9 -> C10 is a whole-document predecessor record in C11. Enforce BOTH
# pieces required by historical_document_problems(): a HISTORICAL first-line
# heading and the exact **HISTORICAL.** banner in the opening block.
report=root/'docs/api/API-02/API02_C9_TO_C10_CORRECTION_REPORT.md'
lines=report.read_text().splitlines()
if not lines:
    raise SystemExit('C9->C10 correction report is empty')
if 'HISTORICAL' not in lines[0]:
    lines.insert(0,'# HISTORICAL — API-02 C9 → C10 correction record')
if '**HISTORICAL.**' not in '\n'.join(lines[:12]):
    lines.insert(1,'')
    lines.insert(2,'**HISTORICAL.** This document records the completed C9 → C10 correction and is retained as predecessor history.')
report.write_text('\n'.join(lines)+'\n')
head='\n'.join(report.read_text().splitlines()[:12])
assert 'HISTORICAL' in head.splitlines()[0]
assert '**HISTORICAL.**' in head

# Register the whole-document historical record explicitly.
p=root/'scripts/api02/lineage_gates.py'
t=p.read_text()
needle='    f"{DOSSIER}/PROGRAM_CONTROL_REGISTER_UPDATE_PROPOSAL.md",\n)'
replacement='    f"{DOSSIER}/PROGRAM_CONTROL_REGISTER_UPDATE_PROPOSAL.md",\n    f"{DOSSIER}/API02_C9_TO_C10_CORRECTION_REPORT.md",\n)'
if needle not in t:
    raise SystemExit('expected HISTORICAL_DOCUMENTS insertion point not found')
t=t.replace(needle,replacement,1)
p.write_text(t)

# Regenerate the carried current machine identity record from C11's own
# workflow + lineage instead of retaining C10 current-state evidence.
scripts=root/'scripts/api02'
sys.path.insert(0,str(scripts))
for name in ('lineage_gates','acceptance_path_identity'):
    sys.modules.pop(name,None)
apiid=importlib.import_module('acceptance_path_identity')
record=apiid.identity_record(root)
if record.get('candidate_role')!='C11' or record.get('entering_role')!='C10' or record.get('problems'):
    raise SystemExit(f'current acceptance identity record is not C11<-C10 clean: {record}')
out=root/'validation/api02/acceptance_path_identity_result.json'
out.write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')

print('API02_C11_PREFLIGHT_REFERENCE_FIX:PASS')
print('API02_C11_STALE_AUDIT_MULTIDIGIT_FIX:PASS')
print('API02_C11_HISTORICAL_RECORD_CLASSIFICATION:PASS')
print('API02_C11_HISTORICAL_BANNER_EXACT:PASS')
print('API02_C11_ACCEPTANCE_IDENTITY_RECORD:PASS')
