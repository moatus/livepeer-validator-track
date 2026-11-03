"""Offline analysis and verifier. Run with --verify to compare without writing results."""
import os
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1'
import json,pathlib,hashlib,sys,collections
import numpy as np
from sklearn.linear_model import RidgeClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import confusion_matrix
P=pathlib.Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(n,x):(P/n).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def vector(x,req):return [0 if x[a] is None else {'no':0,'partial':.5,'yes':1}[x[a]] for a in AXES]+[int(req[a] is not None) for a in AXES]+[x['craft']/10,x['aesthetics']/10]
def bootstrap(v,f):
 u=np.unique(f);means=np.array([np.mean(v[f==a]) for a in u]);rng=np.random.default_rng(904);return np.quantile(means[rng.integers(len(u),size=(2000,len(u)))].mean(1),[.025,.975]).tolist()
AXES=['object_count','color_binding','spatial','typography']
def main(verify=False):
 protocol=json.loads((P/'PROTOCOL.json').read_text());inputs=json.loads((P/'inputs.json').read_text());records={r['key']:r for r in json.loads((P/'original-records.json').read_text())};raw=list(map(json.loads,(P/'raw-responses.jsonl').read_text().splitlines()))
 assert len(raw)<=280 and len({(r['stage'],r['key'],r['vote']) for r in raw})==len(raw)
 # Strict independent reparse: no inference imports and no online access.
 reqs={(stage,r['key']):r['requirements'] for stage in ['stability','main'] for r in inputs[stage]}
 for r in raw:
  if r['status']=='runtime_error':continue
  try:
   x=json.loads(r['raw'].strip());assert set(x)==set(AXES+['craft','aesthetics'])
   for a in AXES:assert (x[a] is None if reqs[r['stage'],r['key']][a] is None else type(x[a]) is str and x[a] in ['yes','partial','no'])
   for a in ['craft','aesthetics']:assert type(x[a]) is int and 0<=x[a]<=10
  except Exception:assert r['status']=='parse_error'
  else:assert r['status']=='ok' and x==r['parsed']
 good={r['key']:r for r in raw if r['stage']=='main' and r['status']=='ok'}
 data=np.load(P/'baseline-scores.npz');keys=np.array([k for k in data['keys'] if k in good]);indices=np.array([list(data['keys']).index(k) for k in keys]);lab=np.array([records[k]['label'] for k in keys]);split=np.array([records[k]['split'] for k in keys]);fam=np.array([records[k]['family'] for k in keys]);prompt=np.array([records[k]['prompt_id'] for k in keys]);Q=np.array([vector(good[k]['parsed'],reqs['main',k]) for k in keys]);pick=data['pickscore'][indices,None];vis=data['visual'][indices]
 quality=np.array([.6*np.mean([{'no':0,'partial':.5,'yes':1}[v] for a,v in good[k]['parsed'].items() if a in AXES and v is not None])+.25*good[k]['parsed']['craft']/10+.15*good[k]['parsed']['aesthetics']/10 for k in keys])[:,None]
 Xs={'pickscore':pick,'visual':vis,'visual+pickscore':np.c_[vis,pick],'qwen':Q,'qwen+pickscore':np.c_[Q,pick],'qwen+visual+pickscore':np.c_[Q,vis,pick],'qwen_quality':quality}
 results={};fits={};predictions=[];paired={}
 for task,classes in [('sd1x',['sd14','sd15']),('threeway',['sd14','sd15','sdxl'])]:
  sub=np.isin(lab,classes);tr=sub&(split=='train');cal=sub&(split=='calibration');te=sub&(split=='heldout');results[task]={};fits[task]={};preds={}
  if not all(np.any(tr&(lab==c)) and np.any(cal&(lab==c)) for c in classes) or not te.any():continue
  for name,X in Xs.items():
   sc=StandardScaler().fit(X[tr]);best=None
   for a in [100,10,1,.1]:
    cl=RidgeClassifier(alpha=a).fit(sc.transform(X[tr]),lab[tr]);acc=float(np.mean(cl.predict(sc.transform(X[cal]))==lab[cal]))
    if best is None or acc>best[0]:best=(acc,a,cl)
   acc,a,cl=best;pred=cl.predict(sc.transform(X[te]));correct=pred==lab[te];preds[name]=correct
   fits[task][name]=dict(alpha=a,calibration_accuracy=acc,scaler_mean=sc.mean_.tolist(),scaler_scale=sc.scale_.tolist(),coef=cl.coef_.tolist(),intercept=cl.intercept_.tolist(),classes=cl.classes_.tolist())
   results[task][name]=dict(train_n=int(tr.sum()),calibration_n=int(cal.sum()),n=int(te.sum()),correct=int(correct.sum()),accuracy=float(correct.mean()),prompt_cluster_ci95=bootstrap(correct,fam[te]),classes=classes,confusion=confusion_matrix(lab[te],pred,labels=classes).tolist(),per_prompt={p:dict(n=int(np.sum(prompt[te]==p)),correct=int(correct[prompt[te]==p].sum())) for p in sorted(set(prompt[te]))})
   for part in ['train','calibration','heldout']:
    mm=sub&(split==part);pp=cl.predict(sc.transform(X[mm]));results[task][name][part+'_summary']=dict(n=int(mm.sum()),correct=int(np.sum(pp==lab[mm])),confusion=confusion_matrix(lab[mm],pp,labels=classes).tolist())
    for k,t,y in zip(keys[mm],lab[mm],pp):predictions.append(dict(task=task,feature=name,split=part,key=k,true=t,predicted=y,correct=bool(t==y)))
  paired[task]={}
  for name in ['qwen','qwen+pickscore','qwen+visual+pickscore']:
   for base in ['pickscore','visual+pickscore']:
    delta=preds[name].astype(float)-preds[base];paired[task][name+' minus '+base]=dict(n=len(delta),both_correct=int(np.sum(preds[name]&preds[base])),both_wrong=int(np.sum(~preds[name]&~preds[base])),improved=int(np.sum(delta==1)),worsened=int(np.sum(delta==-1)),accuracy_delta=float(delta.mean()),paired_prompt_cluster_ci95=bootstrap(delta,fam[te]))
 stability={};groups=collections.defaultdict(list)
 for r in raw:
  if r['stage']=='stability':groups[r['key']].append(r)
 for k,rr in groups.items():
  valid=[r for r in rr if r['status']=='ok'];arr=np.array([vector(r['parsed'],reqs['stability',k]) for r in valid]);stability[k]=dict(attempts=len(rr),parsed=len(valid),all_raw_identical=len({r.get('raw') for r in rr})==1,all_votes_identical=len({json.dumps(r.get('parsed'),sort_keys=True) for r in rr})==1,axis_variance=arr.var(0).tolist() if len(arr) else None)
 means=np.array([np.mean([vector(r['parsed'],reqs['stability',k]) for r in rr if r['status']=='ok'],axis=0) for k,rr in groups.items() if any(r['status']=='ok' for r in rr)])
 coverage={}
 for c in ['sd14','sd15','sdxl']:
  intended=[x for x in inputs['main'] if records[x['key']]['label']==c];attempted=[r for r in raw if r['stage']=='main' and records[r['key']]['label']==c];coverage[c]=dict(usable_original=len(intended),attempted=len(attempted),parsed=sum(r['status']=='ok' for r in attempted),parse_failures=sum(r['status']=='parse_error' for r in attempted),runtime_failures=sum(r['status']=='runtime_error' for r in attempted),splits={s:int(np.sum((lab==c)&(split==s))) for s in ['train','calibration','heldout']})
 out=dict(status='complete' if len(good)==215 else 'partial',coverage=coverage,calls=len(raw),hosted_usd=sum(r['hosted_usd'] for r in raw),results=results,paired=paired,stability=stability,stability_between_image_axis_variance=means.var(0).tolist() if len(means) else None,vector_columns=AXES+[a+'_applicable' for a in AXES]+['craft/10','aesthetics/10'])
 scores=[dict(key=k,vector=Q[i].tolist(),quality=float(quality[i,0]),parsed=good[k]['parsed']) for i,k in enumerate(keys)]
 outputs={'results.json':out,'fitted-analysis.json':fits,'predictions.json':predictions,'score-vectors.json':scores}
 for n,x in outputs.items():
  if verify:assert x==json.loads((P/n).read_text()),n+' differs'
  else:dump(n,x)
 for n,h in json.loads((P/'freeze-hashes.json').read_text()).items():assert sha(P/n)==h,n+' changed'
 print(json.dumps(dict(status=out['status'],calls=len(raw),results={t:{n:f"{v['correct']}/{v['n']}" for n,v in rr.items()} for t,rr in results.items()}),indent=2))
if __name__=='__main__':main('--verify' in sys.argv)
