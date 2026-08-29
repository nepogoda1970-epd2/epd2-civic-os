from __future__ import annotations
import hashlib, re, subprocess
PATH='docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md'
commits=subprocess.check_output(['git','log','--all','--format=%H','--',PATH],text=True).splitlines()
seen=set(); rows=[]
for c in commits:
    if c in seen: continue
    seen.add(c)
    try: b=subprocess.check_output(['git','show',f'{c}:{PATH}'],stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError: continue
    ids=re.findall(rb'^##\s+(FIR-[A-Z0-9_*.-]+)\b',b,flags=re.M)
    rows.append((len(set(ids)),hashlib.sha256(b).hexdigest(),c))
print('COMMITS_SCANNED='+str(len(rows)))
for n,h,c in sorted(rows,reverse=True)[:60]:
    msg=subprocess.check_output(['git','show','-s','--format=%s',c],text=True).strip()
    print(f'{n}\t{h}\t{c}\t{msg}')
