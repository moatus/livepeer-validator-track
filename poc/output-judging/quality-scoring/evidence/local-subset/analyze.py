"""Offline deterministic analysis. --verify reproduces results without overwriting frozen decisions."""
import pathlib,json,hashlib,argparse,csv
import numpy as np
from sklearn.linear_model import RidgeClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import confusion_matrix
P=pathlib.Path(__file__).resolve().parent
MODELS=['sd14','sd15','sdxl'];ALPHAS=[100,10,1,.1]
def dump(name,x): (P/name).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def interval(correct,families):
 unique=np.unique(families);rng=np.random.default_rng(904);by=np.array([correct[families==f].mean() for f in unique]);s=by[rng.integers(len(by),size=(2000,len(by)))].mean(1);return np.quantile(s,[.025,.975]).tolist()
def main(verify=False):
 records={r['key']:r for r in [json.loads(f.read_text()) for f in sorted((P/'records').glob('*.json'))]};data=np.load(P/'local-scores.npz');base=data['variants']=='base';keys=data['keys'][base]
 good=np.array([not records[k]['black'] and not any(records[k].get('nsfw') or []) for k in keys]);keys=keys[good];idxbase=np.flatnonzero(base)[good]
 labels=np.array([records[k]['label'] for k in keys]);splits=np.array([records[k]['split'] for k in keys]);families=np.array([records[k]['family'] for k in keys]);prompts=np.array([records[k]['prompt_id'] for k in keys]);
 # No metadata is passed to these explicit feature selectors.
 def features(name,idx):
  if name=='pickscore':return data['pickscore'][idx,None]
  if name=='visual':return data['visual'][idx]
  if name=='visual+pickscore':return np.c_[data['visual'][idx],data['pickscore'][idx]]
  if name=='pickscore_image_embedding':return data['image_embedding'][idx]
 names=['pickscore','visual','visual+pickscore','pickscore_image_embedding'];decisions={};results={};predictions=[]
 # Fit all feature normalization and models using train; choose alpha using calibration only.
 fits={}
 for task,classes in [('sd1x',MODELS[:2]),('threeway',MODELS)]:
  sub=np.isin(labels,classes);tr=sub&(splits=='train');cal=sub&(splits=='calibration');test=sub&(splits=='heldout');decisions[task]={};fits[task]={}
  for name in names:
   X=features(name,idxbase);scaler=StandardScaler().fit(X[tr]);best=None
   for alpha in ALPHAS:
    clf=RidgeClassifier(alpha=alpha).fit(scaler.transform(X[tr]),labels[tr]);acc=float(np.mean(clf.predict(scaler.transform(X[cal]))==labels[cal]))
    if best is None or acc>best[0]:best=(acc,alpha,clf)
   acc,alpha,clf=best;fits[task][name]=(scaler,clf);decisions[task][name]=dict(alpha=alpha,calibration_accuracy=acc,scaler_mean=scaler.mean_.tolist(),scaler_scale=scaler.scale_.tolist(),coef=clf.coef_.tolist(),intercept=clf.intercept_.tolist(),classes=clf.classes_.tolist())
  q=data['pickscore'][idxbase];lo,hi=np.quantile(q[tr],[1/3,2/3]);commonlo=max(float(q[cal&(labels==c)].min()) for c in classes);commonhi=min(float(q[cal&(labels==c)].max()) for c in classes);decisions[task]['quality_band']=[float(max(lo,commonlo)),float(min(hi,commonhi))]
 decisions.update(protocol_sha256=sha(P/'PROTOCOL.json'),prompts_sha256=sha(P/'prompts.json'),scores_sha256=sha(P/'local-scores.npz'))
 if verify:
  assert decisions==json.loads((P/'frozen-analysis.json').read_text()),'fitted decisions changed'
 else:
  assert not (P/'frozen-analysis.json').exists(),'heldout already opened; use --verify'
  dump('frozen-analysis.json',decisions)
 # Heldout is opened only after all model decisions are saved.
 for task,classes in [('sd1x',MODELS[:2]),('threeway',MODELS)]:
  sub=np.isin(labels,classes);tr=sub&(splits=='train');test=sub&(splits=='heldout');cal=sub&(splits=='calibration');results[task]={}
  majority=sorted(classes,key=lambda c:(-np.sum(labels[tr]==c),c))[0]
  for name in ['majority']+names:
   taskres={}
   for variant in ['base','jpeg75','resize256']:
    if name=='majority' and variant!='base':continue
    ix=np.array([np.flatnonzero((data['keys']==k)&(data['variants']==variant))[0] for k in keys]);y=labels[test]
    if name=='majority':pred=np.full(len(y),majority)
    else:
     scaler,clf=fits[task][name];pred=clf.predict(scaler.transform(features(name,ix)[test]))
    correct=pred==y;q=data['pickscore'][idxbase][test];lo,hi=decisions[task]['quality_band'];band=(q>=lo)&(q<=hi)
    taskres[variant]=dict(n=len(y),correct=int(correct.sum()),accuracy=float(correct.mean()),prompt_cluster_ci95=interval(correct,families[test]),classes=classes,confusion=confusion_matrix(y,pred,labels=classes).tolist(),quality_band=dict(bounds=[lo,hi],n=int(band.sum()),counts={c:int(np.sum(band&(y==c))) for c in classes},accuracy=float(correct[band].mean()) if band.any() else None))
    for k,truth,guess in zip(keys[test],y,pred):predictions.append(dict(task=task,feature=name,variant=variant,key=k,true=truth,predicted=guess,correct=bool(truth==guess)))
   results[task][name]=taskres
  # Paired bootstrap improvement against simple visual+PickScore baseline (same prompt clusters).
  baseline=results[task]['visual+pickscore']['base']['accuracy'];results[task]['chance']=1/len(classes)
  results[task]['embedding_minus_simple']=results[task]['pickscore_image_embedding']['base']['accuracy']-baseline
  # Relative model/prompt residual variation, descriptive all splits; does not fit classifier.
  variation={}
  for name in names[:3]:
   X=features(name,idxbase);scaler=fits[task][name][0];z=scaler.transform(X[sub]);lab=labels[sub];pr=prompts[sub];
   # Remove matched-prompt mean to describe generator/draw differences independent of prompt average.
   residual=z.copy()
   for p in np.unique(pr):residual[pr==p]-=z[pr==p].mean(0)
   cent=np.stack([residual[lab==c].mean(0) for c in classes]);within=float(np.mean([np.mean((residual[lab==c]-cent[j])**2) for j,c in enumerate(classes)]));between=float(np.mean((cent-cent.mean(0))**2));variation[name]=dict(within_generator_residual_mean_square=within,between_generator_centroid_mean_square=between,ratio=between/within if within else None)
  results[task]['variation_descriptive_all_splits']=variation
 coverage={c:dict(scheduled=72,records=sum(r['label']==c for r in records.values()),successful=sum(r['label']==c and r['status']=='ok' for r in records.values()),black=sum(r['label']==c and r.get('black',False) for r in records.values()),usable=int(np.sum(labels==c)),nemotron=0) for c in MODELS}
 out=dict(results=results,coverage=coverage,nemotron=dict(status='blocked',calls=0,stability_images=0,quality_scalar=None,vector=None,incremental_value=None),pickscore_quality_band_limitation='range overlap/central band is not distribution matching; small subsets exploratory',selected_feature_columns={'pickscore':1,'visual':12,'visual+pickscore':13,'pickscore_image_embedding':int(data['image_embedding'].shape[1])})
 if verify:assert out==json.loads((P/'results.json').read_text()),'results differ'
 else:
  dump('results.json',out);dump('predictions.json',predictions)
  with (P/'local-scores.csv').open('w') as f:
   w=csv.writer(f);w.writerow(['key','variant','pickscore']+[f'visual_{i}' for i in range(12)])
   for i,k in enumerate(data['keys']):w.writerow([k,data['variants'][i],data['pickscore'][i]]+data['visual'][i].tolist())
 print(json.dumps({t:{n:round(v['base']['accuracy'],3) for n,v in results[t].items() if isinstance(v,dict) and 'base' in v} for t in ['sd1x','threeway']},indent=2))
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--verify',action='store_true');main(a.parse_args().verify)
