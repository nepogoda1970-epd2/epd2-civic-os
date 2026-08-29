from __future__ import annotations
import hashlib, re, subprocess
from collections import Counter

CURRENT='007b5d71cf5a54e417cbd5647a35a57098ead186'
V23='5d427eba903999f15b6f6a0d9a3de915a30cf666'
ACCEPTED_BRANCH_HEAD='e79011a33d90cc44adeb0ce8619e39a6814a2ec1'
KNOWN_ACCEPTED_V16_SHA='0a6a97a3ed04e78b7d925e750c2b99954b7e2c04b143f48ed28be7572b809c14'
PATH='docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md'

def read(ref): return subprocess.check_output(['git','show',f'{ref}:{PATH}'])
def sha(b): return hashlib.sha256(b).hexdigest()
def ids(t): return re.findall(r'^##\s+(FIR-[A-Z0-9_*.-]+)\b',t,flags=re.M)
def sections(t):
    ms=list(re.finditer(r'^##\s+(FIR-[A-Z0-9_*.-]+)\b.*$',t,flags=re.M)); out={}
    for i,m in enumerate(ms):
        end=ms[i+1].start() if i+1<len(ms) else len(t)
        out[m.group(1)]=t[m.start():end].strip()
    return out
for ref,label in [(CURRENT,'CURRENT'),(V23,'V23'),(ACCEPTED_BRANCH_HEAD,'ACCEPTED_BRANCH')]:
    b=read(ref); t=b.decode(); ii=ids(t); print(label+'_SHA256='+sha(b)); print(label+'_FIRS='+str(len(set(ii))));
    d=sorted(k for k,n in Counter(ii).items() if n>1); print(label+'_DUP='+','.join(d))
cur=sections(read(CURRENT).decode()); v23=sections(read(V23).decode()); acc=sections(read(ACCEPTED_BRANCH_HEAD).decode())
print('ACCEPTED_MATCHES_KNOWN_V16='+str(sha(read(ACCEPTED_BRANCH_HEAD))==KNOWN_ACCEPTED_V16_SHA))
print('ACC_ONLY_V23='+','.join(sorted(set(acc)-set(v23))))
print('V23_ONLY_ACC='+','.join(sorted(set(v23)-set(acc))))
print('CURRENT_ONLY_ACC='+','.join(sorted(set(cur)-set(acc))))
print('ACC_ONLY_CURRENT='+','.join(sorted(set(acc)-set(cur))))
print('SHARED_ACC_V23_CONTENT_DIFF='+','.join(sorted(k for k in set(acc)&set(v23) if acc[k]!=v23[k])))
print('SHARED_ACC_CURRENT_CONTENT_DIFF='+','.join(sorted(k for k in set(acc)&set(cur) if acc[k]!=cur[k])))
