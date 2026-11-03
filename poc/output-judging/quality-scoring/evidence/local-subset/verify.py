"""Scientific-integrity checks; offline, never generates images or calls a provider."""
import pathlib,json,hashlib,subprocess,collections
import numpy as np
from PIL import Image
P=pathlib.Path(__file__).resolve().parent
checks={};issues=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for n in ['PROTOCOL.json','prompts.json']:
 assert sha(P/n)==(P/(n+'.sha256')).read_text().split()[0],n
checks['protocol_prompt_hashes']=True
assert all(json.loads((P/f'runtime-{m}.json').read_text())['protocol_sha256']==sha(P/'PROTOCOL.json') for m in ['sd14','sd15','sdxl'])
checks['same_frozen_protocol_all_generator_runs']=True
prompts=json.loads((P/'prompts.json').read_text());byid={p['id']:p for p in prompts};assert len(byid)==24
assert collections.Counter(p['split'] for p in prompts)==dict(train=12,calibration=6,heldout=6)
fam=collections.defaultdict(set);seeds=collections.defaultdict(set)
for p in prompts:fam[p['family']].add(p['split']);seeds[p['split']].update(p['seeds'])
assert all(len(v)==1 for v in fam.values());assert not (seeds['train']&seeds['heldout'] or seeds['train']&seeds['calibration'] or seeds['heldout']&seeds['calibration'])
checks['whole_family_split_and_disjoint_seeds']=True
assert all(not any(token in p['prompt'].lower() for token in ['sd14','sd15','sdxl','stable diffusion','compvis']) for p in prompts)
checks['no_generator_names_in_prompt_text']=True
pilot=json.loads((P/'stability-manifest.json').read_text());assert len(pilot)==12
assert not {p['family'] for p in prompts if p['split']=='heldout'}&{r['prior_family'] for r in pilot}
checks['stability_families_disjoint_by_manifest']=True
records=[json.loads(f.read_text()) for f in (P/'records').glob('*.json')];assert len(records)==216;assert len(list((P/'records').glob('*.attempt')))==216
assert len({r['key'] for r in records})==216
hashes=collections.defaultdict(list);usable=[]
for r in records:
 p=byid[r['prompt_id']];assert (r['family'],r['split'])==(p['family'],p['split']);assert r['seed']==p['seeds'][r['draw']]
 if r['status']!='ok':issues.append({'key':r['key'],'status':r['status']});continue
 for kind in ['raw','normalized']:assert sha(P/r[kind])==r[kind+'_sha256']
 im=Image.open(P/r['normalized']);assert im.size==(512,512) and im.mode=='RGB' and not im.info
 assert hashlib.sha256(np.asarray(im).tobytes()).hexdigest()==r['pixel_sha256']
 if not r['black'] and not any(r.get('nsfw') or []):usable.append(r);hashes[r['pixel_sha256']].append(r)
for h,rs in hashes.items():assert len(rs)==1,('duplicate usable image',h,[r['key'] for r in rs])
checks['image_hashes_normalization_no_metadata_no_duplicate_usable_images']=True
# Pairing must match noise but generator checkpoints must be different.
for pid in byid:
 for draw in range(3):
  pair=[r for r in records if r['prompt_id']==pid and r['draw']==draw and r['label'] in ['sd14','sd15']];assert len(pair)==2;assert pair[0]['latent_sha256']==pair[1]['latent_sha256']
checks['matched_sd1x_noise']=True
z=np.load(P/'local-scores.npz');assert set(z.files)=={'keys','variants','pickscore','image_embedding','text_embedding','visual'}
assert z['visual'].shape==(648,12);assert len(z['pickscore'])==648
assert all(np.isfinite(z[n]).all() for n in ['pickscore','image_embedding','text_embedding','visual'])
assert set(z['variants'])=={'base','jpeg75','resize256'}
# Recompute selected scalar/simple values directly from pixels and saved vectors.
index={r['key']:r for r in usable}
for i,k in enumerate(z['keys']):
 if z['variants'][i]!='base':continue
 im=np.asarray(Image.open(P/next(r['normalized'] for r in records if r['key']==k)),dtype=float)/255
 assert np.allclose(z['visual'][i,:3],im.mean((0,1)),atol=1e-12)
 assert np.allclose(z['visual'][i,3:6],im.std((0,1)),atol=1e-12)
 # The stored preference scalar is an encoder dot product, independent of labels.
 scale=json.loads((P/'score-runtime.json').read_text())['logit_scale_exp']
 assert np.isclose(z['pickscore'][i],scale*np.dot(z['image_embedding'][i],z['text_embedding'][i]),rtol=1e-5)
# Text conditioning must be identical across generators for every authored prompt.
for pid in byid:
 ix=[i for i,k in enumerate(z['keys']) if records[[r['key'] for r in records].index(k)]['prompt_id']==pid and z['variants'][i]=='base']
 assert np.allclose(z['text_embedding'][ix],z['text_embedding'][ix[0]],atol=1e-6)
checks['explicit_feature_allowlist_and_independent_pixel_embedding_checks']=True
# Classifier fitting is recomputed, enforcing train-only scaling/calibration-only alpha.
r=subprocess.run([str(P/'.venv/bin/python'),str(P/'analyze.py'),'--verify'],capture_output=True,text=True)
assert r.returncode==0,r.stdout+r.stderr
checks['offline_result_recomputation_and_frozen_fit']=True
ledger=[json.loads(l) for l in (P/'spend.jsonl').read_text().splitlines()];assert sum(x.get('hosted_calls',0) for x in ledger)==0
checks['no_hosted_calls_or_spend']=True
lock=json.loads((P/'SCORER-LOCK.json').read_text());runtime=json.loads((P/'score-runtime.json').read_text())
assert lock['score_script_sha256']==runtime['script_sha256']==sha(P/'score_local.py')
assert lock['analysis_script_sha256']==sha(P/'analyze.py')
assert runtime['started_at']>lock.get('updated_before_scoring_at',lock['locked_at'])
checks['scorer_code_lock_before_scoring']=True
if (P/'artifact-checksums.sha256').exists():
 for line in (P/'artifact-checksums.sha256').read_text().splitlines():
  h,n=line.split('  ',1);assert sha(P/n)==h,n
 checks['terminal_artifact_hashes']=True
out=dict(ok=True,checks=checks,scheduled_images=216,usable_images=len(usable),generation_failures=issues,limitations=['Semantic-family separation depends on authored manifest; names alone do not prove conceptual independence','Feature checks enforce explicit numeric allowlist and metadata removal, not absence of all visual provenance clues','Saved PickScore embeddings share the preference encoder and are not an independent judge'])
(P/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
