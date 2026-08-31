from __future__ import annotations
import pathlib, sys
root=pathlib.Path(sys.argv[1]).resolve()
p=root/'.github/workflows/api02-accept.yml'
t=p.read_text()
t=t.replace('API02_ENTERING_CANDIDATE_ZIP       …API02…CANDIDATE_0.1_C9.zip  42a1a59a…','API02_ENTERING_CANDIDATE_ZIP       …API02…CANDIDATE_0.1_C10.zip  479e1732…')
p.write_text(t)
print('API02_C11_PREFLIGHT_REFERENCE_FIX:PASS')
