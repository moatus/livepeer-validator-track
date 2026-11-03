import pathlib,json,hashlib,datetime,collections
P=pathlib.Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
schedule=json.loads((P/'schedule.json').read_text());records=[json.loads(p.read_text()) for p in sorted((P/'records').glob('*.json'))];s={r['key']:r for r in schedule};assert len(records)==len(s)==240
for r in records:
 assert all(r[k]==s[r['key']][k] for k in ['key','prompt_id','prompt','model','seed'])
 if r['status']=='ok':
  for kind in ['raw','normalized']:assert sha(P/r[kind])==r[kind+'_sha256']
freeze=json.loads((P/'freeze.json').read_text());assert all(sha(P/n)==h for n,h in freeze['files'].items());assert freeze['timestamp']<min(r['timestamp'] for r in records)
assert (P/'thresholds.json').stat().st_mtime_ns<=(P/'decisions-blind.json').stat().st_mtime_ns<=(P/'decisions.json').stat().st_mtime_ns
prompts=json.loads((P/'prompts.json').read_text());assert len(prompts)==len({p['family'] for p in prompts})==len({p['prompt'] for p in prompts})==40
prior=P.parent/'judge-score-fingerprinting-poc/2026-10-25/prompts.json';old=json.loads(prior.read_text());assert not ({p['prompt'] for p in prompts}&{p['prompt'] for p in old});assert not ({p['family'] for p in prompts}&{p['family'] for p in old})
r=dict(passed=True,image_hashes_verified=sum(r['status']=='ok' for r in records)*2,exact_schedule_record_matches=240,model_counts=dict(collections.Counter(r['model'] for r in records)),unique_seeds=len({r['seed'] for r in records}),prompt_families=40,prior_prompt_and_family_disjoint=True,freeze_before_first_generation=True,threshold_before_blind_before_evaluated_mtime=True,frozen_sources_unchanged=True)
(P/'delivery-verification.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
