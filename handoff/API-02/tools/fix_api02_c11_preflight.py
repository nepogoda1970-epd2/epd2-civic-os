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
# `C[1-9]` worked through C10, but the derived C11 value `C[1-10]` is a
# character class, not the sequence C1..C10. Build an explicit alternation
# from the already-governed `past_rounds()` source instead. This changes no
# token set and no CURRENT classification rule; it only makes the historical
# cue recognizer represent multi-digit prior rounds correctly.
p=root/'scripts/api02/build_stale_audit.py'
t=p.read_text()
old='_PAST_ROUND = f"C[1-{int(CANDIDATE_ROLE[1:]) - 1}]" if CANDIDATE_ROLE[1:].isdigit() else "C[12]"'
new='''def _past_round_cue_pattern() -> str:\n    rounds = past_rounds()\n    if not rounds:\n        return r"C(?!)"\n    return r"(?:" + "|".join(re.escape(round_name) for round_name in rounds) + r")"\n\n\n_PAST_ROUND = _past_round_cue_pattern()'''
if old not in t:
    raise SystemExit('expected legacy _PAST_ROUND expression not found')
t=t.replace(old,new,1)
p.write_text(t)

# The C9 -> C10 correction report is predecessor history once C11 is current.
# Keep its substantive bytes untouched and add only the governed whole-document
# historical declaration that makes that fact machine-checkable.
report=root/'docs/api/API-02/API02_C9_TO_C10_CORRECTION_REPORT.md'
rt=report.read_text()
if 'HISTORICAL' not in rt.splitlines()[0]:
    rt=(
        '# HISTORICAL — API-02 C9 → C10 correction record\n\n'
        '**HISTORICAL.** This document records the completed C9 → C10 correction and is retained as predecessor history.\n\n'
        + rt
    )
    report.write_text(rt)

# Register that whole-document history explicitly. The existing checker still
# requires the banner above, so this cannot become a blanket stale-state bypass.
p=root/'scripts/api02/lineage_gates.py'
t=p.read_text()
needle='    f"{DOSSIER}/PROGRAM_CONTROL_REGISTER_UPDATE_PROPOSAL.md",\n)'
replacement='    f"{DOSSIER}/PROGRAM_CONTROL_REGISTER_UPDATE_PROPOSAL.md",\n    f"{DOSSIER}/API02_C9_TO_C10_CORRECTION_REPORT.md",\n)'
if needle not in t:
    raise SystemExit('expected HISTORICAL_DOCUMENTS insertion point not found')
t=t.replace(needle,replacement,1)
p.write_text(t)

# C10 carried a machine identity record produced for C10. Regenerate that
# record from C11's own workflow + lineage before stale-state sealing, rather
# than preserving a stale current-state machine claim.
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
print('API02_C11_ACCEPTANCE_IDENTITY_RECORD:PASS')
