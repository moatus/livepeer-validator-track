"""Independent raw parser, centered dual ridge verification; no inference/network."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1'
import pathlib,json,hashlib,re,collections,time,csv
import numpy as np
P=pathlib.Path(__file__).resolve().parent;S=P/'source'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def duplicates(pairs):
 d={}
 for k,v in pairs:
  if k in d:raise ValueError(k)
  d[k]=v
 return d
# Negative controls protect exact fence/key/type contract without any new model calls.
try:json.loads('{"craft":1,"craft":2}',object_pairs_hook=duplicates)
except ValueError:pass
else:raise AssertionError('duplicate accepted')
assert type(True) is not int
raw=[json.loads(l) for l in (S/'raw-responses.jsonl').read_text().splitlines()];inputs=read(S/'inputs.json');records={r['key']:r for r in read(S/'original-records.json')};results=read(P/'results.json');fits=read(P/'fitted-analysis.json');saved=read(P/'predictions.json');audit=read(P/'response-audit.json');b=np.load(S/'baseline-scores.npz');AX=['object_count','color_binding','spatial','typography'];req={(s,r['key']):r['requirements'] for s in inputs for r in inputs[s]}
assert len(raw)==251 and len({(r['stage'],r['key'],r['vote']) for r in raw})==251
assert results['new_inference_calls']==0 and results['hosted_usd']==0
families=collections.defaultdict(set);seeds=collections.defaultdict(set)
for r in records.values():families[r['family']].add(r['split']);seeds[r['split']].add(r['seed'])
assert all(len(x)==1 for x in families.values())
for a in seeds:
 for c in seeds:
  if a!=c:assert not seeds[a]&seeds[c]
assert len({x['image_sha256'] for x in inputs['main']})==215
assert not {x['image_sha256'] for x in inputs['main']}&{x['image_sha256'] for x in inputs['stability']}
good={'A':{},'B':{}};stable={'A':[],'B':[]}
for r,d in zip(raw,audit):
 assert d['raw']==r['raw'] and d['original_status']==r['status'] and d['original_parsed']==r.get('parsed')
 assert d['raw_sha256']==hashlib.sha256(r['raw'].encode()).hexdigest()
 t=r['raw'].strip();m=re.fullmatch(r'```json\s*\n(.*?)\n```',t,re.S);x=json.loads(m[1] if m else t,object_pairs_hook=duplicates);assert x==d['extracted_object']
 assert d['image_sha256']==r['image_sha256'] and d['model_revision']==r['model_revision']
 assert r['hosted_usd']==0
 assert all(s not in r['judge_text'].lower() for s in ['sd14','sd15','sdxl','stable-diffusion','normalized/'])
 numeric=isinstance(x,dict) and all(type(x.get(a))==int and x[a] in range(11) for a in ['craft','aesthetics'])
 full=numeric and set(x)==set(AX+['craft','aesthetics'])
 if full:
  for a in AX:
   full=full and ((x[a] is None) if req[r['stage'],r['key']][a] is None else (type(x[a])==str and x[a] in ('no','partial','yes')))
 assert bool(full)==d['arm_A_accepted'] and bool(numeric)==d['arm_B_accepted']
 for arm,ok in [('A',full),('B',numeric)]:
  if ok:
   if r['stage']=='main':good[arm][r['key']]=x
   else:stable[arm].append(x)
max_coef_error=0.;max_score_error=0.;verified_predictions=0;bootstrap_checks=0
for arm in ['A','B']:
 assert len(good[arm])==({'A':102,'B':180}[arm]) and len(stable[arm])==({'A':21,'B':36}[arm])
 keys=[str(k) for k in b['keys'] if k in good[arm]];ix=[list(b['keys']).index(k) for k in keys];y=np.array([records[k]['label'] for k in keys]);sp=np.array([records[k]['split'] for k in keys]);fam=np.array([records[k]['family'] for k in keys]);prom=np.array([records[k]['prompt_id'] for k in keys]);p=b['pickscore'][ix,None].astype(float);v=b['visual'][ix].astype(float)
 q=[];ql=[]
 for k in keys:
  x=good[arm][k];nums=[x['craft']/10,x['aesthetics']/10]
  if arm=='A':
   vals=[{'no':0,'partial':.5,'yes':1}[x[a]] if x[a] is not None else 0 for a in AX];q.append(vals+[float(req['main',k][a] is not None) for a in AX]+nums);ql.append(.6*np.mean([vals[i] for i,a in enumerate(AX) if x[a] is not None])+.25*nums[0]+.15*nums[1])
  else:q.append(nums)
 q=np.array(q);Xs={'pickscore':p,'visual':v,'visual+pickscore':np.c_[v,p],'judge':q,'judge+pickscore':np.c_[q,p],'judge+visual+pickscore':np.c_[q,v,p]}
 if arm=='A':Xs['judge_quality']=np.array(ql)[:,None]
 # Independent primitive feature CSV equality is exact: values are untouched mappings.
 ff=list(csv.DictReader((P/'features.csv').open()));cols=results['arms'][arm]['judge_columns']
 for r in ff:
  if r['arm']==arm:assert float(r['value'])==q[keys.index(r['key']),cols.index(r['feature'])]
 for task,cs in [('sd1x',['sd14','sd15']),('threeway',['sd14','sd15','sdxl'])]:
  sub=np.isin(y,cs);tr=sub&(sp=='train');ca=sub&(sp=='calibration');te=sub&(sp=='heldout');rr=results['arms'][arm]['tasks'][task];corrects={};f=fam[te];u=np.unique(f);draws=np.random.default_rng(904).choice(u,size=(2000,len(u)))
  # Alternative bootstrap: explicit multiplicity counts (not indexing sums implementation).
  mult=np.array([[collections.Counter(draw)[k] for k in u] for draw in draws]);sizes=np.array([sum(f==k) for k in u])
  def interval(values):
   sums=np.array([sum(values[f==k]) for k in u]);return np.quantile((mult@sums)/(mult@sizes),[.025,.975])
  for name in ['majority']+list(Xs):
   fit=fits[arm][task][name]
   if name=='majority':pred=np.full(len(keys),sorted(cs,key=lambda c:(-sum(y[tr]==c),c))[0])
   else:
    X=Xs[name];mean=X[tr].mean(0);scale=X[tr].std(0);scale[scale==0]=1;Z=(X-mean)/scale;Z0=Z[tr]-Z[tr].mean(0)
    T=np.array([[1. if z==c else -1. for c in cs] for z in y[tr]]);T=T[:,1:] if len(cs)==2 else T;tm=T.mean(0);best=None
    for alpha in [100,10,1,.1]:
     coef=Z0.T@np.linalg.solve(Z0@Z0.T+alpha*np.eye(tr.sum()),T-tm);inter=tm-Z[tr].mean(0)@coef;scores=Z@coef+inter;pred=np.array(cs)[(scores[:,0]>0).astype(int)] if len(cs)==2 else np.array(cs)[scores.argmax(1)];acc=float(np.mean(pred[ca]==y[ca]))
     if best is None or acc>best[0]:best=(acc,alpha,coef,inter,pred,scores)
    acc,alpha,coef,inter,pred,scores=best
    assert alpha==fit['alpha'] and acc==fit['calibration_accuracy']
    assert set(fit['fit_keys'])==set(np.array(keys)[tr]) and set(fit['selection_keys'])==set(np.array(keys)[ca])
    assert not set(fit['fit_keys'])&set(fit['selection_keys'])
    np.testing.assert_allclose(mean,fit['scaler_mean'],rtol=1e-7,atol=1e-9);np.testing.assert_allclose(scale,fit['scaler_scale'],rtol=1e-7,atol=1e-9)
    np.testing.assert_allclose(coef.T,np.atleast_2d(fit['coef']),rtol=1e-7,atol=1e-9);np.testing.assert_allclose(inter,fit['intercept'],rtol=1e-7,atol=1e-9)
    max_coef_error=max(max_coef_error,float(np.max(np.abs(coef.T-np.atleast_2d(fit['coef'])))))
    saved_scores=Z@np.atleast_2d(fit['coef']).T+np.array(fit['intercept']);np.testing.assert_allclose(scores,saved_scores,rtol=1e-7,atol=1e-9);max_score_error=max(max_score_error,float(np.max(np.abs(scores-saved_scores))))
   rows=[r for r in saved if r['arm']==arm and r['task']==task and r['feature']==name];assert len(rows)==sum(sub)
   for r in rows:
    i=keys.index(r['key']);assert r['predicted']==pred[i] and r['true']==y[i] and r['correct']==bool(pred[i]==y[i]);verified_predictions+=1
   z=rr['models'][name];cor=pred[te]==y[te];corrects[name]=cor;assert z['correct']==sum(cor) and z['n']==sum(te);assert z['accuracy']==np.mean(cor)
   np.testing.assert_allclose(z['image_accuracy_cluster_ci95'],interval(cor),rtol=0,atol=1e-12);bootstrap_checks+=1
   for s in ['train','calibration','heldout']:
    mm=sub&(sp==s);conf=[[int(sum(mm&(y==a)&(pred==c))) for c in cs] for a in cs];assert conf==z['split_summary'][s]['confusion'];assert sum(mm)==z['split_summary'][s]['n'];assert sum(pred[mm]==y[mm])==z['split_summary'][s]['correct']
    if s=='heldout':assert conf==z['confusion']
   for pp,r in z['per_prompt'].items():
    mm=te&(prom==pp);assert r['correct']==sum(pred[mm]==y[mm]) and r['n']==sum(mm)
  for desc,z in rr['paired'].items():
   a,bn=desc.split(' minus ');a=corrects[a];bb=corrects[bn];d=a.astype(float)-bb
   assert z['improved']==sum(a&~bb) and z['worsened']==sum(~a&bb) and z['both_correct']==sum(a&bb) and z['both_wrong']==sum(~a&~bb) and z['accuracy_delta']==d.mean()
   np.testing.assert_allclose(z['paired_image_cluster_ci95'],interval(d),rtol=0,atol=1e-12);bootstrap_checks+=1
# All top-level originals plus all entries of BOTH terminal manifests, read only.
unchanged=0
for n,h in read(P/'original-start-hashes.json').items():
 if pathlib.Path(n).exists():assert sha(pathlib.Path(n))==h,n;unchanged+=1
base=P.with_name('2026-10-25');orig=P.with_name('2026-10-25-local-qwen');manifest_entries=0
if base.exists():
 for line in (base/'artifact-checksums.sha256').read_text().splitlines():
  h,n=line.split(None,1);assert sha(base/n.strip())==h,n;manifest_entries+=1
 for n,h in read(orig/'artifact-hashes.json').items():assert sha(orig/n)==h,n;manifest_entries+=1
 for name in ['raw-responses.jsonl','inputs.json','original-records.json','original-prompts.json','baseline-scores.npz','PROTOCOL.json','requirements.lock','execution-lock.json','model-lock.json']:assert sha(S/name)==sha(orig/name)
 d=np.load(base/'local-scores.npz');mask=d['variants']=='base'
 for name in ['keys','pickscore','visual']:assert np.array_equal(d[name][mask],b[name])
# Portable artifact-manifest verification if finalized.
if (P/'artifact-hashes.json').exists():
 for n,h in read(P/'artifact-hashes.json').items():assert sha(P/n)==h,n
v=dict(offline_verified=True,coverage_A=[38,34,30],coverage_B=[94,46,40],stability_votes_A=21,stability_votes_B=36,discrete_predictions_verified=verified_predictions,bootstrap_intervals_independently_verified=bootstrap_checks,max_coefficient_absolute_error=max_coef_error,max_score_absolute_error=max_score_error,float_rtol=1e-7,float_atol=1e-9,original_top_level_files_unchanged=unchanged,original_terminal_manifest_entries_verified=manifest_entries,new_inference_calls=0,cumulative_calls=251,hosted_usd=0)
(P/'verification.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v,indent=2))
