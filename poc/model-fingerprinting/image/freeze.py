import json,pathlib,hashlib,datetime
import numpy as np
P=pathlib.Path(__file__).resolve().parent
records=[json.loads(f.read_text()) for f in sorted((P/'runs').glob('*.json'))]
assert not any(r['split']=='evaluation' for r in records)
x={label:np.stack([np.fromfile(r['fingerprint'],dtype='<f4') for r in records if r['label']==label and r['split']=='calibration' and r['tag']=='first']) for label in ['sd14','sd15']}
assert all(v.shape==(20,54) for v in x.values())
centers={k:v.mean(0).astype(float) for k,v in x.items()}
scale=np.sqrt(np.mean(np.concatenate([(v-centers[k])**2 for k,v in x.items()]),axis=0)).clip(1e-6)
fit=dict(timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),labels=list(x),centers={k:v.tolist() for k,v in centers.items()},scale=scale.tolist(),count={k:len(v) for k,v in x.items()},protocol_sha256=hashlib.sha256((P/'protocol-freeze.json').read_bytes()).hexdigest(),rule='argmin mean square standardized distance; float64 comparisons')
(P/'frozen-classifier.json').write_text(json.dumps(fit,indent=2)+'\n')
print('Frozen calibration-only classifier',fit['count'])
