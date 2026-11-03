import pathlib,json,hashlib,collections
import numpy as np
P=pathlib.Path(__file__).resolve().parent
manifest=json.load(open(P/'dataset.json'))['clips']
assert len(manifest)==30
splits={k:{r['speaker'] for r in manifest if r['split']==k} for k in ['calibration','evaluation']}
assert not splits['calibration'] & splits['evaluation']
for r in manifest:assert hashlib.sha256(pathlib.Path(r['path']).read_bytes()).hexdigest()==r['sha256']
rows=[json.load(open(f)) for f in (P/'runs').glob('*.json')]
assert len(rows)==240,len(rows)
for model in ['parakeet','whisper']:
 for clip in manifest:
  rr=[r for r in rows if r['model']==model and r['clip']==clip['id']]
  assert len(rr)==4
  assert sum(r['instrumented'] for r in rr)==3
  assert sum(r['round']==1 for r in rr)==2
  for r in rr:
   assert r['words'] and all(np.isfinite(w['start']) and np.isfinite(w['end']) and w['end']>=w['start'] for w in r['words'])
   if r['instrumented']:assert len(r['fingerprint'])==24 and np.isfinite(r['fingerprint']).all()
for f in (P/'runs').glob('*.f32'):
 r=json.load(open(f.with_suffix('.json')))
 assert f.stat().st_size==96
 assert np.array_equal(np.fromfile(f,dtype='float32'),np.array(r['fingerprint'],dtype='float32'))
frozen=json.load(open(P/'frozen-before-evaluation.json'))
assert hashlib.sha256((P/'config.json').read_bytes()).hexdigest()==frozen['config_sha256']
result=dict(status='pass',runs=len(rows),instrumented=sum(r['instrumented'] for r in rows),speakers={k:sorted(v) for k,v in splits.items()},audio_hashes_checked=30,binary_fingerprints_checked=180)
json.dump(result,open(P/'verification.json','w'),indent=2)
print(json.dumps(result,indent=2))
