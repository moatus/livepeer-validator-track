import pathlib,json,hashlib,itertools
import numpy as np
from peer import peer,tests
P=pathlib.Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
f=json.loads((P/'freeze.json').read_text());assert all(sha(P/n)==h for n,h in f['files'].items());tests()
a=np.load(P/'features.npz',allow_pickle=False);lookup={k:i for i,k in enumerate(a['keys'])};groups=json.loads((P/'groups.json').read_text());threshold=json.loads((P/'thresholds.json').read_text())['values'];blind=json.loads((P/'decisions-blind.json').read_text())
for rep in threshold:
 cal=[g for g in groups if g['split']=='calibration' and g['condition']=='honest'];assert len(cal)==20
 maxima=[max(peer(a[rep][[lookup[k] for k in g['members']]],float('inf'))['scores']) for g in cal];assert max(maxima)==threshold[rep]
 # Independently replay with only keys, vectors, membership and honest calibration selector.
 # This verification intentionally does not read labels.json, schedule.json or decisions.json.
 for g in groups:
  r=next(r for r in blind if r['method']==rep and r['group']==g['group'])
  valid=all(k in lookup for k in g['members']);assert r['valid']==valid
  if valid:assert peer(a[rep][[lookup[k] for k in g['members']]],threshold[rep])=={k:r[k] for k in ['distances','scores','candidate','decision']}
assert all(np.isfinite(a[rep]).all() for rep in threshold)
print('PASS: frozen sources, synthetic checks, honest-only threshold recomputation, label-free full decision replay, finite features')
