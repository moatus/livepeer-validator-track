import pathlib,json,datetime,hashlib
import numpy as np
from common import dump
P=pathlib.Path(__file__).resolve().parent
assert not any(json.loads(p.read_text())['split']=='heldout' for p in (P/'runs').glob('*.json'))
R=[json.loads(p.read_text()) for p in (P/'runs').glob('*.json')];refs={r['id']:r for r in R if r['role']=='reference'}
def vec(r):return np.fromfile(P/'vectors'/f"{r['key']}.f32",dtype='<f4').astype(float)
assert len(refs)==30
scale=np.std(np.stack([vec(r) for r in refs.values()]),axis=0).clip(1e-6)
def dist(a,b):return float(np.sqrt(np.mean(((vec(a)-vec(b))/scale)**2)))
pos=[dist(r,refs[r['id']]) for r in R if r['role'] in ['candidate','reload']]
neg=[]
for r in refs.values():
 for s in refs.values():
  if r['family']==s['family'] and r['seed']==s['seed'] and (r['variant'],s['variant']) in [('A','B'),('B','A'),('A','C'),('C','A')]:neg.append(dist(r,s))
tol=max(1e-5,10*max(pos))
fit=dict(timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),measurement_version='IMG-002-54-v1',scale=scale.tolist(),tolerance=tol,score='RMS((candidate-reference)/scale), float64; accept <= tolerance',calibration_positive_n=len(pos),calibration_positive_max=max(pos),calibration_negative_n=len(neg),calibration_negative_min=min(neg),alternate_used=False)
assert min(neg)>tol,'54-feature calibration failed: stop before heldout; alternate decision required'
dump(P/'frozen-rule.json',fit)
dump(P/'before-heldout.json',{n:hashlib.sha256((P/n).read_bytes()).hexdigest() for n in ['run.py','freeze.py','verifier.py','build_bundle.py','analyze.py','common.py','protocol-freeze.json','frozen-rule.json','config.json','private/requests.json']})
print(json.dumps({k:v for k,v in fit.items() if k!='scale'}))
