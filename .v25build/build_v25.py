from __future__ import annotations
import hashlib, re, subprocess
PATH='docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md'
refs=subprocess.check_output(['git','for-each-ref','--format=%(refname)','refs/remotes/origin'],text=True).splitlines()
rows=[]
for ref in refs:
    try:
        b=subprocess.check_output(['git','show',f'{ref}:{PATH}'],stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        continue
    ids=re.findall(rb'^##\s+(FIR-[A-Z0-9_*.-]+)\b',b,flags=re.M)
    rows.append((len(set(ids)),hashlib.sha256(b).hexdigest(),ref))
for n,h,ref in sorted(rows,reverse=True)[:40]: print(f'{n}\t{h}\t{ref}')
