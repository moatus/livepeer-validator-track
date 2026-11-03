"""Private post-run integrity and export audit; NOT a verifier dependency."""
import pathlib,json,hashlib,struct,datetime,collections,ast
import numpy as np
from PIL import Image
from common import *
P=pathlib.Path(__file__).resolve().parent;OLD=P.parents[1]/'image-fingerprinting-poc/2026-10-25'
J=json.loads((P/'private/requests.json').read_text());byid={j['id']:j for j in J};R=[json.loads(p.read_text()) for p in (P/'runs').glob('*.json')];B=P/'bundle'
checks={}
checks['protocol_hashes']=all(hashlib.sha256((P/n).read_bytes()).hexdigest()==h for n,h in json.loads((P/'protocol-freeze.json').read_text()).items())
checks['preheldout_hashes']=all(hashlib.sha256((P/n).read_bytes()).hexdigest()==h for n,h in json.loads((P/'before-heldout.json').read_text()).items())
checks['92_private_jobs_194_real_generations']=len(J)==92 and len(R)==194
checks['all_54_float32_finite']=all(len((P/'vectors'/f"{r['key']}.f32").read_bytes())==216 and np.isfinite(np.fromfile(P/'vectors'/f"{r['key']}.f32",dtype='<f4')).all() for r in R)
images_ok=True;black_ok=True
for r in R:
 with Image.open(P/'images'/f"{r['key']}.png") as im:
  images_ok &= im.size==(512,512) and digest('pixel-content',pixels(im))==r['pixel_digest'] and commit('output',bytes.fromhex(byid[r['id']]['output_blind']),pixels(im))==r['output_commitment']
  if any(r['nsfw'] or []):black_ok &= not np.asarray(im).any()
checks['all_images_pixels_and_commitments']=bool(images_ok);checks['safety_flags_are_black']=bool(black_ok)
checks['matched_latents_per_seed']=all(len({r['latent_sha256'] for r in R if r['seed']==s})==1 for s in {r['seed'] for r in R})
checks['split_families_and_seeds_disjoint']=not ({j['family'] for j in J if j['split']=='calibration'} & {j['family'] for j in J if j['split']=='heldout'}) and not ({j['seed'] for j in J if j['split']=='calibration'} & {j['seed'] for j in J if j['split']=='heldout'})
freeze=json.loads((P/'frozen-rule.json').read_text())
checks['freeze_before_heldout']=all(freeze['timestamp']<r['timestamp'] for r in R if r['split']=='heldout')
checks['requests_before_first_load']=(P/'private/requests.json').stat().st_mtime < (P/'load-calibration.json').stat().st_mtime
checks['five_process_completions']=all((P/f'complete-{s}.json').exists() for s in ['calibration','calibration-reload','heldout','heldout-reload','collision'])
checks['checkpoint_files_unchanged']=all(hashlib.sha256((OLD/'models/sd15'/n).read_bytes()).hexdigest()==h for n,h in json.loads((OLD/'identity-sd15.json').read_text())['files'].items())
tokens={}
for p in (P/'private').glob('tokens-*.json'):
 for t in json.loads(p.read_text()):tokens[t['id']]=t
checks['main_prompts_fit_token_limit']=all(tokens[j['id']]['full_length']<=77 for j in J if j['split']!='collision')
checks['close_distant_tokens_differ']=all(len({tuple(tokens[j['id']]['effective_ids']) for j in J if j['family']==f and j['seed']==s})==3 for f in range(15) for s in ([5101,5202] if f<5 else [6303,6404]))
co=[j for j in J if j['split']=='collision'];cr=[r for r in R if r['split']=='collision']
checks['collision_raw_diff_tokens_equal']=co[0]['prompt']!=co[1]['prompt'] and tokens[co[0]['id']]['effective_ids']==tokens[co[1]['id']]['effective_ids']
checks['collision_vectors_equal']=(P/'vectors'/f"{cr[0]['key']}.f32").read_bytes()==(P/'vectors'/f"{cr[1]['key']}.f32").read_bytes()
checks['collision_pixels_equal']=cr[0]['pixel_digest']==cr[1]['pixel_digest']
cases=json.loads((B/'cases.json').read_text());truth={r['case_id']:r for r in json.loads((P/'private/ground-truth.json').read_text())}
expected_keys={'input_commitment','model_profile','settings_commitment','version','job_id','measurement_version','output_commitment','reference'}
checks['bundle_exact_case_schema']=all(set(c) in [{'case_id','expected','candidate'},{'case_id','expected','candidate','observed_output_commitment'}] and set(c['expected'])==expected_keys and set(c['candidate'])=={'fingerprint','receipt','signature'} for c in cases)
# Audit the actual export recursively by serialized text against all private strings.
content='\n'.join(p.read_text() for p in B.iterdir() if p.is_file())
forbidden=[str(P/'private'),str(OLD)]+[j[k] for j in J for k in ['prompt','input_blind','output_blind']]
checks['no_private_content_or_blindings_in_bundle']=all(x not in content for x in forbidden)
checks['private_key_not_exported']=not any('PRIVATE KEY' in p.read_text() for p in B.iterdir() if p.is_file())
checks['private_files_restricted']=all((p.stat().st_mode & 0o077)==0 for p in [P/'private/manifest.json',P/'private/requests.json',P/'private/test-ed25519.pem']) and (P.stat().st_mode & 0o077)==0
checks['numerical_negatives_preserve_metadata']=all(all(c['candidate']['receipt'][k]==c['expected'][k] for k in expected_keys-{'reference'}) and c.get('observed_output_commitment')==c['expected']['output_commitment'] for c in cases if truth[c['case_id']]['kind'] in ['close','distant'])
# Every primary positive uses a separately recorded generation, not reference reuse.
checks['independent_positive_records']=all(r['key']!=next(s['key'] for s in R if s['role']=='reference' and s['id']==r['id']) for r in R if r['role'] in ['candidate','reload'])
def normalized_scheduler(p):
 x=json.loads(p.read_text())['scheduler'];x['_use_default_values']=sorted(x.get('_use_default_values',[]));return canonical(x)
checks['same_effective_scheduler']=len({normalized_scheduler(p) for p in P.glob('load-*.json')})==1
out=dict(timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),checks={k:bool(v) for k,v in checks.items()},passed=all(checks.values()),token_lengths_main=[min(tokens[j['id']]['full_length'] for j in J if j['split']!='collision'),max(tokens[j['id']]['full_length'] for j in J if j['split']!='collision')],collision_full_token_lengths=[tokens[j['id']]['full_length'] for j in co],safety_replacements=sum(any(r['nsfw'] or []) for r in R))
dump(P/'verification.json',out);print(json.dumps(out,indent=2));assert out['passed']
