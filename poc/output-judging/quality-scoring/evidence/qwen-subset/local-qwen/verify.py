"""Independent, offline artifact and scientific-integrity checks; no model needed."""
import pathlib,json,hashlib,subprocess,sys,collections
import numpy as np
P=pathlib.Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for n,h in json.loads((P/'freeze-hashes.json').read_text()).items():assert sha(P/n)==h,n
if (P/'artifact-hashes.json').exists():
 for n,h in json.loads((P/'artifact-hashes.json').read_text()).items():assert sha(P/n)==h,n
execution=json.loads((P/'execution-lock.json').read_text())
for n,h in execution['code_sha256'].items():assert sha(P/n)==h,n+' execution code changed'
assert sha(P/'PROTOCOL.json')==execution['protocol_sha256']
assert sha(P/'requirements.lock')==execution['dependencies_sha256']
records={r['key']:r for r in json.loads((P/'original-records.json').read_text())};inputs=json.loads((P/'inputs.json').read_text());families=collections.defaultdict(set);seeds=collections.defaultdict(set)
for r in records.values():families[r['family']].add(r['split']);seeds[r['split']].add(r['seed'])
assert all(len(s)==1 for s in families.values())
for a in seeds:
 for b in seeds:
  if a!=b:assert not seeds[a]&seeds[b]
assert len(inputs['main'])==215
assert len({r['image_sha256'] for r in inputs['main']})==215,'duplicate content'
assert not {r['image_sha256'] for r in inputs['main']}&{r['image_sha256'] for r in inputs['stability']}
assert len({r['key'] for r in inputs['main']})==215
raw=[json.loads(l) for l in (P/'raw-responses.jsonl').read_text().splitlines()]
for r in raw:
 if 'judge_text' in r:
  assert all(t not in r['judge_text'].lower() for t in ['sd14','sd15','sdxl','stable-diffusion','generator_label_private','normalized/'])
 assert r['hosted_usd']==0
assert len(raw)<=280
# Baseline copy provenance, if original remains available; review bundle works without it.
original=P.with_name('2026-10-25')
if original.exists():
 for n,h in json.loads((P/'PROTOCOL.json').read_text())['original_hashes'].items():assert sha(original/n)==h,n+' original changed'
 d=np.load(original/'local-scores.npz');b=np.load(P/'baseline-scores.npz');m=d['variants']=='base'
 for k in ['keys','pickscore','visual']:assert np.array_equal(d[k][m],b[k]),k
subprocess.run([sys.executable,str(P/'analyze.py'),'--verify'],check=True)
print(json.dumps(dict(offline_verified=True,calls=len(raw),families=len(families),no_split_overlap=True,no_duplicate_images=True,hosted_usd=0)))
