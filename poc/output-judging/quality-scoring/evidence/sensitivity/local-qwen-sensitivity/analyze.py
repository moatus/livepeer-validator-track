"""Offline-only sensitivity: imports numerical libraries, never inference libraries."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1'
import json,re,pathlib,hashlib,collections,csv,time
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import RidgeClassifier
from sklearn.metrics import confusion_matrix
P=pathlib.Path(__file__).resolve().parent;S=P/'source'
AX=['object_count','color_binding','spatial','typography'];NUM=['craft','aesthetics'];ALPHAS=[100,10,1,.1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(n,x):(P/n).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def load(n):return json.loads((S/n).read_text())
def table(n,rows):
 with (P/n).open('w') as f:
  if not rows:return
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def unique_pairs(pairs):
 d={}
 for k,v in pairs:
  if k in d:raise ValueError('duplicate:'+k)
  d[k]=v
 return d
def extract(raw):
 t=raw.strip();m=re.fullmatch(r'```json\s*\n(.*?)\n```',t,re.S)
 return (m.group(1) if m else t),bool(m)
def parse(raw,req):
 t,f=extract(raw);x=json.loads(t,object_pairs_hook=unique_pairs)
 assert isinstance(x,dict)
 numeric=all(type(x.get(a)) is int and 0<=x[a]<=10 for a in NUM)
 full=set(x)==set(AX+NUM) and numeric
 full=full and all((x.get(a) is None if req[a] is None else type(x.get(a)) is str and x[a] in ['no','partial','yes']) for a in AX)
 return x,f,full,numeric

def qvector(x,req):return [0 if x[a] is None else {'no':0,'partial':.5,'yes':1}[x[a]] for a in AX]+[int(req[a] is not None) for a in AX]+[x[a]/10 for a in NUM]
def quality(x):return .6*np.mean([{'no':0,'partial':.5,'yes':1}[x[a]] for a in AX if x[a] is not None])+.25*x['craft']/10+.15*x['aesthetics']/10

def boot(v,fam):
 u=np.unique(fam);n=np.array([sum(fam==f) for f in u]);s=np.array([np.sum(v[fam==f]) for f in u]);draw=np.random.default_rng(904).integers(len(u),size=(2000,len(u)))
 return np.quantile(s[draw].sum(1)/n[draw].sum(1),[.025,.975]).tolist()
def stats(X,cols,mask):
 out={}
 for j,c in enumerate(cols):
  z=X[mask,j];out[c]=dict(n=len(z),mean=float(z.mean()),variance=float(z.var()),minimum=float(z.min()),maximum=float(z.max()),values={str(float(k)):int(v) for k,v in zip(*np.unique(z,return_counts=True))})
 return out

def main():
 start=time.time();raw=[json.loads(l) for l in (S/'raw-responses.jsonl').read_text().splitlines()];inputs=load('inputs.json');records={r['key']:r for r in load('original-records.json')};req={(s,r['key']):r['requirements'] for s in inputs for r in inputs[s]}
 assert len(raw)==251 and sum(r['hosted_usd'] for r in raw)==0
 accepted={'A':{},'B':{}};aud=[];votes={'A':collections.defaultdict(list),'B':collections.defaultdict(list)}
 for r in raw:
  x,f,a,b=parse(r['raw'],req[r['stage'],r['key']]);assert (a if not f else False)==(r['status']=='ok')
  if r['status']=='ok':assert x==r['parsed']
  item=dict(stage=r['stage'],key=r['key'],vote=r['vote'],original_status=r['status'],original_parsed=r.get('parsed'),raw=r['raw'],raw_sha256=hashlib.sha256(r['raw'].encode()).hexdigest(),image_sha256=r['image_sha256'],model_revision=r['model_revision'],transformation='exact_json_fence' if f else 'identity',extracted_object=x,arm_A_accepted=a,arm_B_accepted=b)
  aud.append(item)
  for arm,ok in [('A',a),('B',b)]:
   if ok:
    z=qvector(x,req[r['stage'],r['key']]) if arm=='A' else [x[n]/10 for n in NUM]
    if r['stage']=='main':accepted[arm][r['key']]=(z,x)
    else:votes[arm][r['key']].append(z)
 dump('response-audit.json',aud)
 data=np.load(S/'baseline-scores.npz');allkeys=list(map(str,data['keys']));out={'status':'paired post hoc exploratory sensitivity; both prespecified arms reported','calls_cumulative':251,'new_inference_calls':0,'hosted_usd':0,'bootstrap':dict(replicates=2000,seed=904,estimand='image-weighted accuracy; whole-family resampling with multiplicity'),'arms':{}}
 fits={};predrows=[];metricrows=[];pairrows=[];coverrows=[];corrrows=[];distrows=[];perrows=[];featurerows=[]
 for arm in ['A','B']:
  good=accepted[arm];keys=np.array([k for k in allkeys if k in good]);idx=[allkeys.index(k) for k in keys];y=np.array([records[k]['label'] for k in keys]);sp=np.array([records[k]['split'] for k in keys]);fam=np.array([records[k]['family'] for k in keys]);prom=np.array([records[k]['prompt_id'] for k in keys]);q=np.array([good[k][0] for k in keys],dtype=np.float64);v=data['visual'][idx].astype(np.float64);p=data['pickscore'][idx,None].astype(np.float64)
  qcols=AX+[a+'_applicable' for a in AX]+[a+'/10' for a in NUM] if arm=='A' else [a+'/10' for a in NUM]
  Xs={'pickscore':p,'visual':v,'visual+pickscore':np.c_[v,p],'judge':q,'judge+pickscore':np.c_[q,p],'judge+visual+pickscore':np.c_[q,v,p]}
  if arm=='A':Xs['judge_quality']=np.array([quality(good[k][1]) for k in keys])[:,None]
  coverage={s:{c:int(sum((sp==s)&(y==c))) for c in ['sd14','sd15','sdxl']} for s in ['train','calibration','heldout']}
  expected=[38,34,30] if arm=='A' else [94,46,40];assert [sum(coverage[s].values()) for s in coverage]==expected
  assert sum(len(z) for z in votes[arm].values())==(21 if arm=='A' else 36)
  for inp in inputs['main']:
   r=records[inp['key']];coverrows.append(dict(arm=arm,key=r['key'],label=r['label'],split=r['split'],prompt_id=r['prompt_id'],family=r['family'],accepted=r['key'] in good))
  for i,k in enumerate(keys):
   for j,c in enumerate(qcols):featurerows.append(dict(arm=arm,key=k,label=y[i],split=sp[i],feature=c,value=float(q[i,j])))
  description={}
  for split in ['all','train','calibration','heldout']:
   for label in ['all','sd14','sd15','sdxl']:
    mask=(np.ones(len(keys),bool) if split=='all' else sp==split)&(np.ones(len(keys),bool) if label=='all' else y==label)
    if not mask.any():continue
    ds=stats(q,qcols,mask);description[split+'/'+label]=ds
    for c,d in ds.items():distrows.append(dict(arm=arm,split=split,label=label,feature=c,**{k:v for k,v in d.items() if k!='values'},value_counts=json.dumps(d['values'],sort_keys=True)))
   mask=np.ones(len(keys),bool) if split=='all' else sp==split
   for j,c in enumerate(qcols):
    for k,d in enumerate(['pickscore']+['visual_'+str(i) for i in range(v.shape[1])]):
     z=np.c_[p,v][mask,k];a=q[mask,j];cor=float(np.corrcoef(a,z)[0,1]) if a.std()>0 and z.std()>0 else None
     corrrows.append(dict(arm=arm,split=split,judge_feature=c,baseline_feature=d,n=int(mask.sum()),pearson=cor))
  stable={k:dict(valid_votes=len(vv),within_image_variance=np.var(vv,axis=0).tolist(),all_valid_votes_identical=all(z==vv[0] for z in vv)) for k,vv in votes[arm].items()}
  means=np.array([np.mean(z,axis=0) for z in votes[arm].values()]);res=dict(coverage=coverage,main_accepted=len(keys),stability=dict(valid_votes=sum(map(len,votes[arm].values())),valid_images=len(stable),per_image=stable,between_image_variance=means.var(0).tolist(),all_12_raw_triplicates_identical=all(len({r['raw'] for r in raw if r['stage']=='stability' and r['key']==k})==1 for k in [x['key'] for x in inputs['stability']])),judge_columns=qcols,feature_distributions=description,tasks={});fits[arm]={}
  for task,classes in [('sd1x',['sd14','sd15']),('threeway',['sd14','sd15','sdxl'])]:
   sub=np.isin(y,classes);tr=sub&(sp=='train');ca=sub&(sp=='calibration');te=sub&(sp=='heldout');assert all(np.any(tr&(y==c)) and np.any(ca&(y==c)) for c in classes)
   splitcounts={s:{c:int(sum(sub&(sp==s)&(y==c))) for c in classes} for s in ['train','calibration','heldout']};rr=dict(class_order=classes,split_class_counts=splitcounts,models={},paired={});fits[arm][task]={};corrects={}
   majority=sorted(classes,key=lambda c:(-sum(y[tr]==c),c))[0]
   for name in ['majority']+list(Xs):
    if name=='majority':pred=np.full(len(keys),majority);fit=dict(label=majority);alpha=None;calacc=float(np.mean(pred[ca]==y[ca]))
    else:
     X=Xs[name];sc=StandardScaler().fit(X[tr]);Z=sc.transform(X);best=None
     for alpha in ALPHAS:
      cl=RidgeClassifier(alpha=alpha).fit(Z[tr],y[tr]);calacc=float(np.mean(cl.predict(Z[ca])==y[ca]))
      if best is None or calacc>best[0]:best=(calacc,alpha,cl)
     calacc,alpha,cl=best;pred=cl.predict(Z);fit=dict(alpha=alpha,calibration_accuracy=calacc,scaler_mean=sc.mean_.tolist(),scaler_scale=sc.scale_.tolist(),coef=cl.coef_.tolist(),intercept=cl.intercept_.tolist(),classes=cl.classes_.tolist(),fit_keys=keys[tr].tolist(),selection_keys=keys[ca].tolist())
    fits[arm][task][name]=fit;correct=pred[te]==y[te];corrects[name]=correct;ci=boot(correct,fam[te]);m=dict(n=int(te.sum()),correct=int(correct.sum()),accuracy=float(correct.mean()),image_accuracy_cluster_ci95=ci,alpha=alpha,calibration_accuracy=calacc,confusion=confusion_matrix(y[te],pred[te],labels=classes).tolist(),split_summary={},per_prompt={})
    metricrows.append(dict(arm=arm,task=task,feature=name,train_n=int(tr.sum()),calibration_n=int(ca.sum()),heldout_n=int(te.sum()),correct=int(correct.sum()),accuracy=float(correct.mean()),ci_low=ci[0],ci_high=ci[1],alpha=alpha,calibration_accuracy=calacc))
    for s in ['train','calibration','heldout']:
     mm=sub&(sp==s);m['split_summary'][s]=dict(n=int(mm.sum()),correct=int(sum(pred[mm]==y[mm])),confusion=confusion_matrix(y[mm],pred[mm],labels=classes).tolist())
     for k,t,pr in zip(keys[mm],y[mm],pred[mm]):predrows.append(dict(arm=arm,task=task,feature=name,split=s,key=k,true=t,predicted=pr,correct=bool(t==pr)))
    for pp in np.unique(prom[te]):
     mm=prom[te]==pp;d=dict(n=int(sum(mm)),correct=int(correct[mm].sum()),accuracy=float(correct[mm].mean()));m['per_prompt'][pp]=d;perrows.append(dict(arm=arm,task=task,feature=name,prompt_id=pp,**d))
    rr['models'][name]=m
   for name in Xs:
    if not name.startswith('judge'):continue
    for base in ['majority','pickscore','visual','visual+pickscore']:
     a=corrects[name];b=corrects[base];d=a.astype(float)-b;ci=boot(d,fam[te]);z=dict(n=len(d),improved=int(sum(a&~b)),worsened=int(sum(~a&b)),both_correct=int(sum(a&b)),both_wrong=int(sum(~a&~b)),accuracy_delta=float(d.mean()),paired_image_cluster_ci95=ci)
     rr['paired'][name+' minus '+base]=z;pairrows.append(dict(arm=arm,task=task,feature=name,baseline=base,**{k:v for k,v in z.items() if k!='paired_image_cluster_ci95'},ci_low=ci[0],ci_high=ci[1]))
   res['tasks'][task]=rr
  out['arms'][arm]=res
 dump('results.json',out);dump('fitted-analysis.json',fits);dump('predictions.json',predrows)
 for n,r in [('metrics.csv',metricrows),('paired.csv',pairrows),('coverage.csv',coverrows),('per-prompt.csv',perrows),('features.csv',featurerows),('distributions.csv',distrows),('correlations.csv',corrrows),('predictions.csv',predrows)]:table(n,r)
 print(json.dumps({a:{t:{n:f"{z['correct']}/{z['n']}" for n,z in rr['models'].items()} for t,rr in r['tasks'].items()} for a,r in out['arms'].items()},indent=2))
if __name__=='__main__':main()
