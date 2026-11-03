import pathlib,json,hashlib,collections,datetime
import numpy as np
from PIL import Image
P=pathlib.Path(__file__).resolve().parent
R=[json.loads(f.read_text()) for f in (P/'runs').glob('*.json')]
def sha(b):return hashlib.sha256(b).hexdigest()
checks={}
for n,h in json.loads((P/'protocol-freeze.json').read_text()).items():checks['protocol_'+n]=sha((P/n).read_bytes())==h
checks['frozen_files']=all(sha((P/line.split('  ',1)[1]).read_bytes())==line.split('  ',1)[0] for line in (P/'before-heldout.sha256').read_text().splitlines())
checks['count_saved_202']=len(R)==202
checks['all_float32_54_finite']=all(pathlib.Path(r['fingerprint']).stat().st_size==216 and np.isfinite(np.fromfile(r['fingerprint'],dtype='<f4')).all() for r in R if r['instrumented'])
checks['all_images_512_actual_hash']=all(Image.open(r['image']).size==(512,512) and sha(np.array(Image.open(r['image'])).tobytes())==r['image_sha256'] for r in R)
latents=collections.defaultdict(set)
for r in R:latents[(r['prompt_id'],r['seed'])].add(r['latent_sha256'])
checks['matched_latents_across_models_repeats']=all(len(x)==1 for x in latents.values())
manifest=json.loads((P/'manifest.json').read_text());cal=[p for p in manifest if p['split']=='calibration'];ev=[p for p in manifest if p['split']=='evaluation']
checks['disjoint_prompt_groups']=not(set(p['group'] for p in cal)&set(p['group'] for p in ev))
checks['disjoint_split_seeds']=not(set(s for p in cal for s in p['seeds'])&set(s for p in ev for s in p['seeds']))
fit=json.loads((P/'frozen-classifier.json').read_text())
checks['fit_before_heldout']=fit['timestamp']<min(r['timestamp'] for r in R if r['split']=='evaluation')
checks['fit_only_calibration_20_each']=fit['count']==dict(sd14=20,sd15=20)
schedulers=[json.loads(f.read_text())['scheduler'] for f in P.glob('load-*.json')]
effective=lambda s:{k:v for k,v in s.items() if not k.startswith('_')}
checks['same_effective_scheduler_every_load']=all(effective(s)==effective(schedulers[0]) for s in schedulers)
checks['all_eight_phases_completed']=len(list(P.glob('complete-*.json')))==8
checks['safety_replacements_consistent']=all(not np.array(Image.open(r['image'])).any() for r in R if r['nsfw'] and any(r['nsfw']))
checks['heldout_images_not_safety_replaced']=not any(r['nsfw'] and any(r['nsfw']) for r in R if r['split']=='evaluation')
# Check pinned local checkpoint/config bytes against recorded identities.
checks['model_files_unchanged']=all(sha((P/'models'/l/n).read_bytes())==h for l in ['sd14','sd15'] for n,h in json.loads((P/f'identity-{l}.json').read_text())['files'].items())
summary=dict(timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),checks=checks,passed=all(checks.values()),counts=dict(saved_generations=len(R),numerical_fingerprints=sum(r['instrumented'] for r in R),baseline_generations=sum(not r['instrumented'] for r in R)),notes='Count excludes 8 warmups. No work is accepted based on accuracy threshold.')
(P/'verification.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2));assert summary['passed']
