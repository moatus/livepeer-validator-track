import pathlib,json,hashlib,datetime
import numpy as np
P=pathlib.Path(__file__).resolve().parent
rows=[json.load(open(f)) for f in (P/'runs').glob('*.json')]
assert not any(r['split']=='evaluation' for r in rows),'Freeze before collecting evaluation'
cal={m:np.array([r['fingerprint'] for r in rows if r['model']==m and r['instrumented'] and r['round']==0]) for m in ['parakeet','whisper']}
assert all(v.shape==(12,24) for v in cal.values())
scale=np.maximum(np.sqrt(np.mean([v.var(0,ddof=1) for v in cal.values()],axis=0)),1e-6)
json.dump(dict(frozen_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),config_sha256=hashlib.sha256((P/'config.json').read_bytes()).hexdigest(),means={k:v.mean(0).tolist() for k,v in cal.items()},scale=scale.tolist()),open(P/'frozen-before-evaluation.json','w'),indent=2)
print('Classifier frozen from 24 calibration model/clip pairs')
