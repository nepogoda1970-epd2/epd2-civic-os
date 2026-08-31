from __future__ import annotations
import pathlib, sys

root=pathlib.Path(sys.argv[1]).resolve()

# C11 carried-workflow entering-baseline comment.
p=root/'.github/workflows/api02-accept.yml'
t=p.read_text()
t=t.replace('API02_ENTERING_CANDIDATE_ZIP       …API02…CANDIDATE_0.1_C9.zip  42a1a59a…','API02_ENTERING_CANDIDATE_ZIP       …API02…CANDIDATE_0.1_C10.zip  479e1732…')
p.write_text(t)

# C11 exposes a latent C10+ bug in the stale-audit historical-cue regex.
# `C[1-9]` worked through C10, but the derived C11 value `C[1-10]` is a
# character class, not the sequence C1..C10.  Build an explicit alternation
# from the already-governed `past_rounds()` source instead.  This changes no
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

print('API02_C11_PREFLIGHT_REFERENCE_FIX:PASS')
print('API02_C11_STALE_AUDIT_MULTIDIGIT_FIX:PASS')
