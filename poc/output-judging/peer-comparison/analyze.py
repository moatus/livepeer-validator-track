import pathlib,json,hashlib,itertools,math
import numpy as np
from peer import peer,tests
P=pathlib.Path(__file__).resolve().parent
def dump(n,x):(P/n).write_text(json.dumps(x,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def wilson(k,n):
 if not n:return None
 z=1.95996398454;p=k/n;den=1+z*z/n;mid=(p+z*z/(2*n))/den;half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den;return [max(0,mid-half),min(1,mid+half)]
frozen=json.loads((P/'freeze.json').read_text());assert all(sha(P/n)==h for n,h in frozen['files'].items());verification=tests();data=np.load(P/'features.npz',allow_pickle=False);keys=list(data['keys']);assert len(keys)==len(set(keys));groups=json.loads((P/'groups.json').read_text());lookup={k:i for i,k in enumerate(keys)}
def vectors(g,rep):return data[rep][[lookup[k] for k in g['members']]]
thresholds={};cal={}
for rep in ['rpa','pickscore']:
 gs=[g for g in groups if g['condition']=='honest' and g['split']=='calibration'];assert len(gs)==20 and all(all(k in lookup for k in g['members']) for g in gs),'incomplete calibration: stop evaluation'
 cal[rep]=[dict(group=g['group'],**peer(vectors(g,rep),float('inf'))) for g in gs];thresholds[rep]=max(max(r['scores']) for r in cal[rep])
assert not (P/'thresholds.json').exists();dump('thresholds.json',dict(values=thresholds,calibration=cal,source='only20 honest calibration numeric vectors per method',features_sha256=sha(P/'features.npz')));(P/'thresholds.sha256').write_text(sha(P/'thresholds.json')+'\n')
# Decision pass complete and persisted before labels are opened.
decisions=[]
for rep,t in thresholds.items():
 for g in groups:
  valid=all(k in lookup for k in g['members']);r=dict(method=rep,group=g['group'],valid=valid)
  if valid:
   r.update(peer(vectors(g,rep),t))
   base=r
   for perm in itertools.permutations(range(4)):
    q=peer(vectors(g,rep)[list(perm)],t);assert np.allclose(q['scores'],np.array(r['scores'])[list(perm)])
    assert q['decision']==('no clear outlier' if r['decision']=='no clear outlier' else perm.index(r['decision']))
  else:r.update(decision='no clear outlier',missing=[k for k in g['members'] if k not in lookup])
  decisions.append(r)
dump('decisions-blind.json',decisions);blind_hash=sha(P/'decisions-blind.json');labels=json.loads((P/'labels.json').read_text());gmap={g['group']:g for g in groups};summary={};enriched=[]
for r in decisions:
 g=gmap[r['group']];truth=labels[r['group']]['substitute_slot'];r=dict(r,**{k:g[k] for k in ['split','condition','prompt_id']},truth=truth)
 if r['valid']:
  r['outcome']='abstention' if r['decision']=='no clear outlier' else ('false_accusation' if truth is None else 'correct' if r['decision']==truth else 'wrong_honest_slot')
  r['rank_correct']=truth is not None and r['candidate']==truth
 else:r['outcome']='invalid'
 enriched.append(r)
for rep in thresholds:
 summary[rep]={}
 for cond in ['honest','close','broad','jpeg75']:
  rs=[r for r in enriched if r['method']==rep and r['split']=='heldout' and r['condition']==cond];valid=[r for r in rs if r['valid']];counts={k:sum(r['outcome']==k for r in rs) for k in ['correct','wrong_honest_slot','false_accusation','abstention','invalid']};counts.update(scheduled=len(rs),valid=len(valid),rank_correct=sum(r.get('rank_correct',False) for r in rs),rank_denominator=len(valid) if cond in ['close','broad'] else None)
  metric='correct' if cond in ['close','broad'] else 'false_accusation';counts['wilson95_valid_'+metric]=wilson(counts[metric],len(valid));summary[rep][cond]=counts
blocks=[]
for rep in thresholds:
 for cond in ['honest','close','broad']:
  for b in range(4):
   rs=[r for r in enriched if r['method']==rep and r['condition']==cond and r['prompt_id'] in [f'q{i:02d}' for i in range(20+5*b,25+5*b)]];entry=dict(method=rep,condition=cond,block=b,scheduled=5,valid=sum(r['valid'] for r in rs))
   if entry['valid']==5:
    role_scores=np.array([[r['scores'][gmap[r['group']]['roles'].index(role)] for role in range(4)] for r in rs]);means=role_scores.mean(0);wins=np.flatnonzero(means==max(means));candidate=int(wins[0]) if len(wins)==1 else None;entry.update(role_means=means.tolist(),rank_candidate=candidate,substitute_role=b if cond!='honest' else None,correct=candidate==b if cond!='honest' else None,honest_score_range=[float(role_scores.min()),float(role_scores.max())] if cond=='honest' else None)
   blocks.append(entry)
records=[json.loads(f.read_text()) for f in sorted((P/'records').glob('*.json'))];schedule=json.loads((P/'schedule.json').read_text());assert len(records)==len(schedule)==240 and len(list((P/'records').glob('*.attempt')))==240;assert {r['key'] for r in records}=={r['key'] for r in schedule};assert len({r['seed'] for r in schedule})==240
verification.update(generation_accounting=True,finite_features=all(np.isfinite(data[k]).all() for k in ['rpa','pickscore']),frozen_code_consistency=True,thresholds_unchanged=sha(P/'thresholds.json')==(P/'thresholds.sha256').read_text().strip(),blind_decisions_sha256=blind_hash,real_group_permutations=len([r for r in decisions if r['valid']])*24,threshold_dependency='only calibration honest groups; labels opened after decisions-blind.json persisted')
dump('verification.json',verification);dump('decisions.json',enriched);dump('results.json',dict(experiment='CONSENSUS-007',scientific_review='pending',thresholds=thresholds,heldout=summary,repeated_job_rank_only=blocks,accounting=dict(scheduled=240,terminal=len(records),ok=sum(r['status']=='ok' for r in records),black=sum(r.get('black',False) for r in records),safety=sum(any(r.get('nsfw') or []) for r in records),failed=sum(r['status']!='ok' for r in records),generation_seconds=sum(r['seconds'] for r in records)),random_choice_context=.25,verification=verification))
print(json.dumps(summary,indent=2))
